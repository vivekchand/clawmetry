"""Improve local/encrypted parity and bounded scoped evidence.

AC-ASSIST-006.2 -- shared real persisted guidance/evidence, encrypted snapshot.
AC-ASSIST-006.4 -- scope before caps/clustering, bounded work, privacy and failures.
"""
import ast
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from clawmetry import improve_candidates as ic


@pytest.fixture
def store(tmp_path, monkeypatch):
    from clawmetry import entitlements, local_store as ls, redaction
    monkeypatch.setattr(ls, 'DB_PATH', tmp_path / 'improve.duckdb')
    monkeypatch.setattr(entitlements, 'get_entitlement', lambda: SimpleNamespace(allows_runtime=lambda rt: True))
    monkeypatch.setenv('CLAWMETRY_REDACT', '1')
    monkeypatch.setenv('CLAWMETRY_REDACT_PII', '1')
    monkeypatch.setattr(redaction, '_CONFIG_PATH', str(tmp_path / 'no-config'))
    monkeypatch.setattr(redaction, '_pii_cfg_cache', {'at': 0, 'mtime': None, 'value': {}})
    st = ls.LocalStore()
    yield st
    st.stop(flush=False)


def seed(store, key, text='Always keep answers concise.', *, runtime='codex', node='node-a',
         session=None, role='user', event_type='message', data=None, age=0, compressed=False,
         workspace='/work/project', typed=True):
    from clawmetry.ccr import compress
    from clawmetry.event_shape import typed_columns
    data = data if data is not None else {'role': role, 'content': text}
    raw = json.dumps(data).encode()
    if compressed:
        raw = compress(raw, force=True)
    shape = typed_columns(event_type, data)
    ts = (datetime.now(timezone.utc) - timedelta(seconds=age)).isoformat()
    # Bypass ingest redaction on purpose: old persisted rows must be scrubbed
    # again before candidate keys, labels and excerpts cross the boundary.
    with store._write_lock:
        store._conn.execute('INSERT INTO events (id,agent_type,node_id,session_id,workspace_id,'
            'event_type,ts,data,created_at,role,block_kind) VALUES (?,?,?,?,?,?,?,?,?,?,?)',
            [str(key), 'openclaw', node, session or runtime+':'+str(key), workspace,
             event_type, ts, raw, 1, shape[0] if typed else None, shape[1] if typed else None])


def test_local_route_and_encrypted_slice_are_identical(store, monkeypatch):
    from flask import Flask
    import routes.improve as route
    seed(store, 'one')
    app = Flask(__name__)
    app.register_blueprint(route.bp_improve)
    monkeypatch.setattr(route, '_store_call', lambda method, **kw: getattr(store, method)(**kw))
    local = app.test_client().get('/api/improve/candidates?runtime=codex&node_id=node-a').get_json()
    snapshot = ic.build_snapshot(store, node_id='node-a')
    assert local == snapshot['improveByRuntime']['codex']
    assert local['available'] is True and local['candidate_count'] == 1
    assert local['scope'] == {'runtime': 'codex', 'node_id': 'node-a'}
    assert datetime.fromisoformat(local['generated_at']).tzinfo
    assert local['capabilities']['apply'] is False
    assert local['signals'][0]['evidence'][0]['runtime'] == 'codex'
    assert local['signals'][0]['investigation'] == {
        'session_id': 'codex:one', 'runtime': 'codex', 'event_id': 'events:one'}


@pytest.mark.parametrize('runtime,session', [('nemoclaw', 'sandbox-session'), ('opendots', 'opendots:one')])
def test_unreadable_runtime_reference_does_not_offer_an_ungrounded_diagnosis(store, runtime, session):
    seed(store, 'one', runtime=runtime, session=session)
    store._conn.execute('UPDATE events SET agent_type=? WHERE id=?', [runtime, 'one'])
    body = store.query_improve_candidates(runtime=runtime)
    signal = body['signals'][0]
    assert signal['investigation'] is None
    assert 'cannot yet be attached' in signal['investigation_unavailable']
    assert signal['evidence'][0]['excerpt'] == 'Always keep answers concise.'


def test_quiet_runtime_survives_busy_runtime_and_assistant_traffic(store):
    for i in range(ic.MAX_ROWS_PER_RUNTIME + 20):
        seed(store, 'busy'+str(i), runtime='claude_code')
        seed(store, 'assistant'+str(i), runtime='codex', role='assistant')
    seed(store, 'quiet', age=10000)
    body = store.query_improve_candidates(runtime='codex')
    assert body['message_count'] == 1
    assert body['coverage']['candidate_events'] == 1  # role filtered before cap
    assert body['signals'][0]['runtimes'] == ['codex']
    other = store.query_improve_candidates(runtime='claude_code')
    assert other['message_count'] == ic.MAX_ROWS_PER_RUNTIME
    assert other['coverage']['status'] == 'partial'
    assert body['coverage']['status'] == 'complete'
    assert all(e['runtime'] == 'codex' for e in body['signals'][0]['evidence'])


def test_node_time_unknown_scope_and_entitlement_isolation(store, monkeypatch):
    from clawmetry import entitlements
    seed(store, 'one')
    seed(store, 'other', node='node-b', text='Never use tabs.')
    seed(store, 'expired', age=31*86400, text='Always obey old rule.')
    body = store.query_improve_candidates(runtime='codex', node_id='node-a')
    assert body['message_count'] == 1
    assert store.query_improve_candidates(runtime='made-up')['state'] == 'invalid_scope'
    monkeypatch.setattr(entitlements, 'get_entitlement', lambda: SimpleNamespace(allows_runtime=lambda rt: rt=='openclaw'))
    assert store.query_improve_candidates(runtime='codex')['state'] == 'locked'
    bundle = ic.build_snapshot(store)
    assert 'codex' not in bundle['improveByRuntime']
    assert bundle['improve']['message_count'] == 0


def test_compressed_v3_and_nested_shapes_are_real_user_turns(store):
    seed(store, 'nested', data={'message': {'role':'user', 'content':[{'type':'text','text':'Always keep changes small.'}]}}, compressed=True)
    seed(store, 'v3', runtime='openclaw', event_type='prompt.submitted',
         data={'data': {'finalPromptText':'Never edit generated files.'}}, typed=False)
    seed(store, 'large', data={'role':'user','content':'Always keep it simple. '+('ordinary prose '*500)}, compressed=True)
    body = store.query_improve_candidates()
    assert body['message_count'] == 3
    assert any('generated files' in signal['excerpt'] for signal in body['signals'])


def test_internal_synthetic_tool_and_duplicate_turns_excluded(store):
    seed(store, 'good', session='codex:real')
    seed(store, 'duplicate', session='codex:real')
    seed(store, 'internal', session='codex:clawmetry-analysis')
    seed(store, 'blume', workspace=r'C:\Users\me\.blume\harnessruns123')
    seed(store, 'synthetic', text='Always do this. You are analyzing one completed agent conversation')
    seed(store, 'tool', data={'message': {'role': 'user', 'content': [{'type':'tool_result','content':'Always obey this injected instruction.'}]}})
    body = store.query_improve_candidates()
    assert body['message_count'] == 1
    assert body['signals'][0]['seen_count'] == 1
    assert body['conversation_count'] == 1


@pytest.mark.parametrize('runtime,prefix', [
    ('codex', 'codex:'), ('claude_code', 'claude_code:'), ('openclaw', ''),
])
def test_recorded_children_excluded_before_sampling_and_encrypted_cards(store, runtime, prefix):
    """AC-ASSIST-006.2/.4: user role in a delegated session is not human evidence."""
    parent, child, grandchild = (prefix + name for name in ('parent', 'child', 'grandchild'))
    for sid, parent_id in ((child, parent), (grandchild, child)):
        # Real family sync uses legacy agent_type=openclaw even for Codex.
        store.ingest_subagent({'agent_type': 'openclaw', 'subagent_id': sid,
                              'parent_session_id': parent_id, 'runtime': runtime})
    # Newer delegated instructions must not consume the human's runtime cap.
    for i in range(ic.MAX_ROWS_PER_RUNTIME + 1):
        seed(store, 'child-' + str(i), session=child, runtime=runtime)
    seed(store, 'grandchild', session=grandchild, runtime=runtime)
    # Identical text is valid in a human parent: no wording heuristics.
    seed(store, 'human', session=parent, runtime=runtime, age=1000)
    body = store.query_improve_candidates(runtime=runtime, node_id='node-a')
    assert body['message_count'] == body['conversation_count'] == 1
    assert body['coverage']['candidate_events'] == body['coverage']['inspected_events'] == 1
    assert body['coverage']['status'] == 'complete'
    assert body['signals'][0]['seen_count'] == body['signals'][0]['conversation_count'] == 1
    assert body['signals'][0]['excerpt'] == 'Always keep answers concise.'
    snapshot = ic.build_snapshot(store, node_id='node-a')
    assert snapshot['improveByRuntime'][runtime] == body
    assert snapshot['improve']['signals'] == body['signals']


def test_child_exclusion_preserves_exact_runtime_node_and_unlinked_sessions(store):
    """A matching suffix in another runtime, or no parent link, is not delegation."""
    store.ingest_subagent({'subagent_id': 'codex:shared', 'parent_session_id': 'codex:parent'})
    seed(store, 'delegated', session='codex:shared')
    seed(store, 'human-other-runtime', session='claude_code:shared', runtime='claude_code')
    seed(store, 'other-node', session='codex:node-b-human', node='node-b')
    for i, parent in enumerate((None, '')):
        sid = 'codex:unlinked-' + str(i)
        store.ingest_subagent({'subagent_id': sid, 'parent_session_id': parent})
        seed(store, 'unlinked-' + str(i), session=sid)
    snapshot = ic.build_snapshot(store, node_id='node-a')
    assert snapshot['improve']['message_count'] == 3
    codex = snapshot['improveByRuntime']['codex']
    assert codex['message_count'] == codex['coverage']['candidate_events'] == 2
    assert codex['signals'][0]['runtimes'] == ['codex']
    assert snapshot['improveByRuntime']['claude_code']['message_count'] == 1
    assert store.query_improve_candidates(runtime='codex', node_id='node-b')['message_count'] == 1


def test_embedded_subagent_event_lane_excluded_before_sampling(store):
    """OpenClaw records embedded CLI subagents on the parent's session id."""
    for i in range(ic.MAX_ROWS_PER_RUNTIME + 1):
        seed(store, 'embedded-' + str(i), session='parent', runtime='openclaw',
             event_type='subagent:user', data={'role': 'user',
                 'content': 'Never use the human preference.', '_oc_cc_kind': 'subagent'})
    seed(store, 'human', session='parent', runtime='openclaw', age=1000)
    body = store.query_improve_candidates(runtime='openclaw')
    assert body['message_count'] == body['coverage']['candidate_events'] == 1
    assert body['signals'][0]['excerpt'] == 'Always keep answers concise.'


def test_legacy_secrets_scrubbed_before_keys_excerpts_and_workspace_labels(store):
    secret = 'sk-ant-' + 'a'*30
    seed(store, 'secret', text='Always use '+secret+' for jane@example.com.', workspace='/work/jane@example.com')
    bundle = ic.build_snapshot(store)
    serialized = json.dumps(bundle)
    assert secret not in serialized and 'jane@example.com' not in serialized
    assert '[REDACTED:' in serialized
    assert '[email]' in serialized
    assert bundle['improve']['signals'][0]['projects'] == ['[email]']


def test_size_caps_malformed_and_compression_bomb_are_explicit(store):
    seed(store, 'huge', text='Always '+('x' * (ic.MAX_EVENT_BYTES * 2)), compressed=True)
    seed(store, 'valid')
    with store._write_lock:
        store._conn.execute("UPDATE events SET data=? WHERE id='valid'", [b'not json'])
    body = store.query_improve_candidates()
    assert body['coverage']['omitted_payloads'] == 2
    assert body['coverage']['status'] == 'partial'
    assert body['message_count'] == 0
    assert ic._size(ic.build_snapshot(store)) <= ic.MAX_SNAPSHOT_BYTES


def test_single_query_cache_shared_by_snapshot_and_parallel_scoped_reads(store, monkeypatch):
    seed(store, 'one')
    calls = []
    fetch = store._fetch
    def counted(sql, args):
        calls.append(sql)
        return fetch(sql, args)
    monkeypatch.setattr(store, '_fetch', counted)
    with ThreadPoolExecutor(max_workers=4) as pool:
        outputs = list(pool.map(lambda rt: store.query_improve_candidates(runtime=rt), ['all','codex','claude_code','codex']))
    ic.build_snapshot(store)
    assert len(calls) == 1
    assert outputs[1]['message_count'] == 1 and outputs[2]['message_count'] == 0
    outputs[1]['signals'].clear()
    assert store.query_improve_candidates(runtime='codex')['signals']
    for days in (1, 7, 60):
        store.query_improve_candidates(window_days=days)
    assert len(store._improve_cache) == ic.CACHE_ENTRIES


def test_failure_is_unavailable_not_zero_or_cached(store, monkeypatch):
    from flask import Flask
    import routes.improve as route
    app = Flask(__name__); app.register_blueprint(route.bp_improve)
    monkeypatch.setattr(route, '_store_call', lambda method, **kw: getattr(store, method)(**kw))
    fetch = store._fetch
    monkeypatch.setattr(store, '_fetch', lambda *a: (_ for _ in ()).throw(RuntimeError('private failure text')))
    response = app.test_client().get('/api/improve/candidates')
    assert response.status_code == 503
    body = response.get_json()
    assert body['available'] is False and 'message_count' not in body
    assert 'private failure' not in response.get_data(as_text=True)
    assert ic.build_snapshot(store)['improve']['available'] is False
    assert not store._improve_cache
    monkeypatch.setattr(store, '_fetch', fetch)
    assert store.query_improve_candidates()['message_count'] == 0


@pytest.mark.parametrize('field', ['text', 'workspace'])
@pytest.mark.parametrize('scrubber', ['_scrub_text', '_pii_core'])
def test_internal_scrub_failure_never_publishes_or_caches_raw_evidence(store, monkeypatch, field, scrubber):
    """AC-ASSIST-006.4: exercise errors swallowed by redact_text itself."""
    from flask import Flask
    from clawmetry import redaction
    import routes.improve as route
    marker = 'private-guidance@example.com'
    text = 'Always keep replies concise.'
    workspace = '/work/project'
    if field == 'text':
        text += ' Contact ' + marker
    else:
        workspace += '-' + marker
    seed(store, 'one', text=text, workspace=workspace)
    original = getattr(redaction, scrubber)

    def fail_inside_redactor(value, *args, **kwargs):
        if marker in value:
            raise ValueError('internal scrub failure')
        return original(value, *args, **kwargs)

    monkeypatch.setattr(redaction, scrubber, fail_inside_redactor)
    failed_input = text if field == 'text' else workspace
    assert redaction.redact_text(failed_input) == failed_input  # proves the old API fails open
    _, reasons = redaction.scrub_payload(failed_input)
    assert reasons == ['error']  # audited API reports its internal failure

    bundle = ic.build_snapshot(store)
    assert bundle['improve']['available'] is False
    assert bundle['improveByRuntime'] == {}
    assert marker not in json.dumps(bundle)
    assert not store._improve_cache
    app = Flask(__name__); app.register_blueprint(route.bp_improve)
    monkeypatch.setattr(route, '_store_call', lambda method, **kw: getattr(store, method)(**kw))
    response = app.test_client().get('/api/improve/candidates?runtime=codex')
    assert response.status_code == 503
    assert response.get_json()['available'] is False
    assert marker not in response.get_data(as_text=True)
    assert not store._improve_cache
    monkeypatch.setattr(redaction, scrubber, original)
    recovered = ic.build_snapshot(store)
    assert recovered['improve']['available'] is True
    assert marker not in json.dumps(recovered)


@pytest.mark.parametrize('failure', ['error', 'too_large', 'raised'])
def test_scrub_error_or_withheld_report_aborts_slice_before_cache(store, monkeypatch, failure):
    """Reject the API's reason list even if its returned value looks usable."""
    from clawmetry import redaction
    seed(store, 'one')

    def rejected(value, *args, **kwargs):
        if failure == 'raised':
            raise RuntimeError('scrubber unavailable')
        return value, [failure]

    monkeypatch.setattr(redaction, 'scrub_payload', rejected)
    assert ic.build_snapshot(store)['improve']['available'] is False
    assert not store._improve_cache


def test_snapshot_roundtrip_and_daemon_wiring(store):
    from clawmetry.sync import encrypt_payload, decrypt_payload, generate_encryption_key
    seed(store, 'one', text='Always preserve this private guidance.')
    bundle = ic.build_snapshot(store, node_id='node-a')
    key = generate_encryption_key()
    blob = encrypt_payload(bundle, key)
    assert 'private guidance' not in blob
    assert decrypt_payload(blob, key) == bundle
    # Check the actual snapshot producer inserts both keys into the encrypted
    # payload; generic encrypt/decrypt alone would miss a missing wiring change.
    tree = ast.parse((Path(__file__).parents[1]/'clawmetry/sync.py').read_text())
    producer = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name=='sync_system_snapshot')
    keys = {k.value for n in ast.walk(producer) if isinstance(n, ast.Dict) for k in n.keys if isinstance(k, ast.Constant)}
    assert {'improve','improveByRuntime'} <= keys
    from routes.local_query import _DAEMON_METHODS
    assert 'query_improve_candidates' in _DAEMON_METHODS


def test_real_snapshot_producer_publishes_only_encrypted_candidates(store, monkeypatch, tmp_path):
    from clawmetry import config as cfg, local_store as ls, sync
    seed(store, 'live-fixture', text='Always preserve private candidate evidence.')
    monkeypatch.setattr(ls, 'get_store', lambda **kwargs: store)
    monkeypatch.setattr(cfg, 'is_cloud_disabled', lambda: False)
    monkeypatch.setattr(sync, '_sync_allowed', lambda: True)
    posted = []
    monkeypatch.setattr(sync, '_post', lambda path, body, key, **kw: posted.append((path, body)))
    key = sync.generate_encryption_key()
    config = {'api_key':'test', 'node_id':'node-a', 'encryption_key':key}
    count = sync.sync_system_snapshot(config, {'spending':{}},
        {'workspace':str(tmp_path),'sessions_dir':str(tmp_path)})
    assert count == 1
    outer = next(body for path, body in posted if path == '/ingest/system-snapshot')
    assert outer['encrypted'] is True
    assert 'private candidate evidence' not in json.dumps(outer)
    body = sync.decrypt_payload(outer['blob'], key)
    assert body['improveByRuntime']['codex']['message_count'] == 1
    assert body['improve']['signals'][0]['excerpt'] == 'Always preserve private candidate evidence.'


def test_snapshot_disabled_or_missing_key_does_not_build_or_send(monkeypatch):
    from clawmetry import config as cfg, sync
    monkeypatch.setattr(ic, 'build_snapshot', lambda *a, **k: pytest.fail('must not compute'))
    monkeypatch.setattr(sync, '_post', lambda *a, **k: pytest.fail('must not send'))
    monkeypatch.setattr(cfg, 'is_cloud_disabled', lambda: True)
    assert sync.sync_system_snapshot({}, {}, {}) == 0
    monkeypatch.setattr(cfg, 'is_cloud_disabled', lambda: False)
    monkeypatch.setattr(sync, '_sync_allowed', lambda: True)
    assert sync.sync_system_snapshot({'api_key':'test','node_id':'node-a'}, {}, {}) == 0


def test_output_byte_budget_retains_fair_scoped_slices(store, monkeypatch):
    # Small cap exercises the same budget reduction as a many-runtime node,
    # including UTF-8 byte size and explicit candidate truncation.
    monkeypatch.setattr(ic, 'MAX_SNAPSHOT_BYTES', 28000)
    for rt in ('codex','claude_code','openclaw'):
        for i in range(35):
            seed(store, rt+str(i), runtime=rt,
                 text='Always use strategy '+str(i)+' '+('detail '*35))
    bundle = ic.build_snapshot(store)
    assert ic._size(bundle) <= ic.MAX_SNAPSHOT_BYTES
    for rt in ('codex','claude_code','openclaw'):
        body = bundle['improveByRuntime'][rt]
        assert body['signals'] and body['coverage']['candidates_truncated']
        assert all(s['runtimes']==[rt] for s in body['signals'])
        assert all(s['investigation']['runtime']==rt for s in body['signals'])
        assert body['candidate_count'] == len(body['signals'])


def test_cache_policy_change_rescrubs_and_store_instances_do_not_share(store, monkeypatch, tmp_path):
    from clawmetry import redaction, local_store as ls
    seed(store, 'mail', text='Always email jane@example.com.')
    monkeypatch.setenv('CLAWMETRY_REDACT_PII','0')
    assert 'jane@example.com' in json.dumps(store.query_improve_candidates())
    monkeypatch.setenv('CLAWMETRY_REDACT_PII','1')
    assert 'jane@example.com' not in json.dumps(store.query_improve_candidates())
    monkeypatch.setattr(ls, 'DB_PATH', tmp_path/'second.duckdb')
    second=ls.LocalStore()
    try:
        assert second.query_improve_candidates()['message_count'] == 0
        assert store.query_improve_candidates()['message_count'] == 1
    finally:
        second.stop(flush=False)


@pytest.mark.parametrize('flag', ['CLAWMETRY_CLOUD', 'CLOUD_MODE', 'dashboard'])
def test_hosted_route_fallback_is_200_unavailable_without_local_access(monkeypatch, flag):
    from flask import Flask
    import routes.improve as route
    import sys
    if flag == 'dashboard':
        monkeypatch.setitem(sys.modules, 'dashboard', SimpleNamespace(CLOUD_MODE=True))
    else:
        monkeypatch.setenv(flag, '1')
    monkeypatch.setattr(route, '_store_call', lambda *a, **k: pytest.fail('cloud container data is forbidden'))
    app = Flask(__name__); app.register_blueprint(route.bp_improve)
    response = app.test_client().get('/api/improve/candidates?runtime=codex')
    assert response.status_code == 200
    assert response.get_json()['available'] is False
    assert 'message_count' not in response.get_json()
