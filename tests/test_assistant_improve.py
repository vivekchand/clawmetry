"""Improve hands the Assistant an exact incident, not an ambiguous excerpt.

AC-IMPROVE-CHAT-001.2: seed recorded before/after context, including corrections.
AC-IMPROVE-CHAT-001.3: fail explicitly before inference on missing/wrong scope.
AC-IMPROVE-CHAT-001.5: request a grounded explanation and a verifiable proposal.
AC-IMPROVE-CHAT-001.6: retain exact evidence sources for saved follow-ups.
"""
import json
import time
from types import SimpleNamespace

import pytest

from clawmetry import assistant_improve as improve
from clawmetry import assistant_service as service
from clawmetry.assistant_stream import Cancelled
from clawmetry.local_store import _NON_OPENCLAW_RUNTIME_PREFIXES
from tests.test_assistant_evidence import NODE, SID, call, event, result
from tests.test_assistant_evidence import store as evidence_store

REF = {'session_id': SID, 'runtime': 'codex', 'event_id': 'events:anchor'}


@pytest.fixture
def store(tmp_path):
    yield from evidence_store.__wrapped__(tmp_path)


@pytest.fixture(autouse=True)
def entitled(monkeypatch):
    from clawmetry import entitlements
    monkeypatch.setattr(entitlements, 'get_entitlement', lambda: SimpleNamespace(allows_runtime=lambda _: True))


def test_runtime_access_is_checked_before_any_read(monkeypatch):
    from clawmetry import entitlements
    monkeypatch.setattr(entitlements, 'get_entitlement', lambda: SimpleNamespace(allows_runtime=lambda _: False))
    with pytest.raises(ValueError, match='current plan'):
        improve.seed_review(lambda *_args, **_kw: pytest.fail('not entitled'), REF, NODE)


@pytest.mark.parametrize('runtime', sorted({'openclaw', *_NON_OPENCLAW_RUNTIME_PREFIXES}))
def test_handoff_preserves_each_declared_runtime_with_legacy_storage_labels(store, runtime):
    sid = 'selected-openclaw' if runtime == 'openclaw' else runtime + ':selected'
    store._conn.execute('INSERT INTO sessions(agent_type,session_id,node_id,updated_at) '
                        "VALUES ('openclaw',?,?,1)", [sid, NODE])
    event(store, 'selected', sid=sid)
    reference = {'session_id': sid, 'runtime': runtime, 'event_id': 'events:selected'}
    _, reads = improve.seed_review(lambda method, **kw: getattr(store, method)(**kw), reference, NODE)
    assert reads[0][1]['items'][0]['event_id'] == 'events:selected'
    assert all(args['session_id'] == sid and args['runtime'] == runtime for args, _ in reads)


def incident(store):
    event(store, 'before', data={'role': 'user', 'content': 'stop now'}, ts='2026-10-04T01:58:00Z')
    event(store, 'anchor', data={'role': 'user', 'content': 'can you start server again ??'})
    call(store, command='python voice_server.py', ts='2026-10-04T02:24:00Z')
    result(store, output='Starting voice service; arm controller remains stopped', ts='2026-10-04T02:24:01Z')
    event(store, 'correction', data={'role': 'user', 'content': 'I meant teleoperation, not the voice service'}, ts='2026-10-04T02:25:00Z')
    event(store, 'foreign', sid='codex:other', data={'role': 'user', 'content': 'FOREIGN PRIVATE'}, ts='2026-10-04T02:25:00Z')


def test_real_store_context_reaches_planner_synthesis_and_saved_sources(store, monkeypatch):
    incident(store)
    monkeypatch.setattr(service, '_planner_system', lambda _: service._PLAN)
    prompts, reads = [], []

    def read(method, **kwargs):
        reads.append(kwargs)
        return getattr(store, method)(**kwargs)

    def generate(system, prompt):
        packet = json.loads(prompt)
        prompts.append(packet)
        visible = json.dumps(packet['evidence'])
        assert 'stop now' in visible and 'I meant teleoperation' in visible
        assert 'voice_server.py' in visible
        assert 'FOREIGN PRIVATE' not in visible
        assert packet['improve_review']['event_id'] == 'events:anchor'
        assert 'future run' in system and 'not proof' in system
        assert 'permanent word-to-action rule' in system
        if system.startswith(service._PLAN):
            assert packet['investigation']['reads_remaining'] == 5
            return '{"queries":[],"session_reads":[]}'
        return 'The agent targeted the voice service. Recovery is unconfirmed [3].'

    response, history = service._answer_chat('anthropic', 'Explain this moment', 'chat', [],
                                             generate, read, node_id=NODE, improve=REF)
    assert len(reads) == 3 and len(prompts) == 2
    assert all(read['node_id'] == NODE and read['session_id'] == SID for read in reads)
    assert response['sources'] == history[-1]['sources']
    assert response['title'] == 'Explain: can you start server again ??'
    assert response['sources'][0]['read']['event_id'] == REF['event_id']
    assert response['sources'][2]['coverage']['scope']['since'].startswith('2026-10-04T02:00')
    assert history[-2]['improve'] == REF
    reads.clear()

    def followup(system, prompt):
        packet = json.loads(prompt)
        assert packet['improve_review']['event_id'] == REF['event_id']
        assert 'permanent word-to-action rule' in system
        if system.startswith(service._PLAN):
            assert packet['investigation']['reads_remaining'] == 8
            return json.dumps({'session_reads': [{**REF, 'mode': 'event'}]})
        return 'Here is a proposed check, not a verified improvement [1].'
    reply, _ = service._answer_chat('anthropic', 'How should we verify it?', 'chat', history,
                                    followup, read, node_id=NODE)
    assert len(reads) == 1
    assert reply['sources'][0]['read']['event_id'] == REF['event_id']


@pytest.mark.parametrize('change', [
    {'node_id': 'other-node'}, {'event_id': 'events:missing'}, {'session_id': 'codex:other'},
])
def test_unavailable_anchor_never_calls_provider(store, monkeypatch, change):
    incident(store)
    monkeypatch.setattr(service, '_planner_system', lambda _: service._PLAN)
    reference = {**REF, **{k: v for k, v in change.items() if k != 'node_id'}}
    with pytest.raises(service._ChatFailure, match='no longer available'):
        service._answer_chat('anthropic', 'Explain', 'chat', [],
            lambda *_: pytest.fail('must not infer without the selected occurrence'),
            lambda method, **kw: getattr(store, method)(**kw),
            node_id=change.get('node_id', NODE), improve=reference)


@pytest.mark.parametrize('reference', [None, {}, {**REF, 'node_id': 'other'},
    {**REF, 'runtime': 'openclaw'}, {**REF, 'event_id': 'replay:anchor'},
    {**REF, 'session_id': '\nprivate'}, {**REF, 'event_id': 'events:'},
    {**REF, 'event_id': 'events:'+'a'*600}])
def test_invalid_reference_rejected_at_chat_boundary(reference):
    with pytest.raises(service._ChatFailure):
        service.validate_chat({'message': 'Explain', 'improve': reference})


def test_context_pagination_is_explicit_and_does_not_expand_initial_budget(store):
    incident(store)
    for n in range(30):
        event(store, f'later-{n}', ts=f'2026-10-04T02:30:{n:02d}Z')
    review, reads = improve.seed_review(lambda method, **kw: getattr(store, method)(**kw), REF, NODE)
    assert len(reads) == 3
    assert len(reads[-1][1]['items']) == 20
    assert reads[-1][1]['next_cursor']
    assert 'up to 10' in review['coverage_note']


def test_stopped_investigation_never_reads_or_calls_provider():
    class Control:
        def check(self):
            raise Cancelled()
    with pytest.raises(Cancelled):
        improve.seed_review(lambda *_args, **_kw: pytest.fail('cancelled'), REF, NODE, control=Control())
    with pytest.raises(ValueError, match='timed out'):
        improve.seed_review(lambda *_args, **_kw: pytest.fail('expired'), REF, NODE, deadline=time.monotonic()-1)


def test_improve_answer_still_streams_real_provider_text(monkeypatch):
    emitted = []
    class Control:
        def check(self): pass
        def emit(self, kind, value): emitted.append((kind, value))
    def generate(*_args, **kwargs):
        assert callable(kwargs['on_text'])
        kwargs['on_text']('Grounded explanation')
        return 'Grounded explanation'
    monkeypatch.setattr(service.assistant_providers, 'generate', generate)
    answer = service._stream_generate(Control(), 'anthropic', 'test-key',
        service._SYNTHESIS + improve.GUIDANCE, 'recorded context')
    assert answer == 'Grounded explanation'
    assert ''.join(v['text'] for k, v in emitted if k == 'delta') == answer
