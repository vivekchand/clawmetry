"""Adaptive grounded debugging.

AC-ASSIST-008.1: discover recorded command/output evidence.
AC-ASSIST-008.2: preserve recorded call relationships.
AC-ASSIST-008.3: bounded pages, continuations and follow-up context.
AC-ASSIST-008.4: retain metric definitions and observation time.
AC-ASSIST-008.5: actual service sources render with truthful coverage.
AC-ASSIST-008.6: bounded context, cancellation and read-only scope.
"""
import json
import copy
from tests.test_assistant_evidence_frontend import SOURCE, _render
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

from clawmetry import assistant_context as context, assistant_service as service
from clawmetry.assistant_phase import PhaseControl, PhaseExpired
from clawmetry.assistant_stream import StreamJob, Cancelled
from clawmetry.assistant_stream import http_response


def evidence(rows, **kwargs):
    return dict(label='Evidence', rows=rows, sql='SELECT id FROM events LIMIT 100',
                error=None, visual=False, truncated=False, **kwargs)


def test_context_includes_more_than_twenty_rows_and_complete_long_cells():
    rows = [{'id': n, 'title': 'x' * 600} for n in range(53)]
    packet = json.loads(context.prompt_context({'question': 'Explain'}, [evidence(rows)], 'system', 'anthropic'))
    source = packet['evidence'][0]
    assert source['rows'] == rows
    assert source['included_rows'] == 53
    assert not source['preview_truncated']


def test_answer_uses_all_53_retrieved_rows_when_they_fit(monkeypatch):
    """Regression: the original answer silently saw only the first 20 rows."""
    monkeypatch.setattr(service, '_planner_system', lambda store: service._PLAN)
    rows = [{'event_id': str(i), 'title': 'recorded detail ' * 40} for i in range(53)]
    def generate(system, prompt):
        if system == service._SYNTHESIS:
            # Accept both prompt encodings so this guard fails on the original
            # behavior, not merely because the JSON envelope changed.
            sources = (json.loads(prompt.split('\nEvidence:\n', 1)[1])
                       if '\nEvidence:\n' in prompt else json.loads(prompt)['evidence'])
            assert sources[0]['rows'] == rows
            return 'Checked all 53 retrieved records [1].'
        return json.dumps({'queries': [{'sql': 'SELECT id, title FROM sessions LIMIT 100'}]})
    response, _ = service._answer_chat('anthropic', 'Read the evidence', 'c', [], generate,
                                      lambda *args, **kwargs: {'rows': rows})
    assert response['sources'][0]['rows'] == 53


def test_fresh_error_evidence_takes_priority_over_old_history_in_managed_window():
    row = {'event_id': 'codex:s:1', 'fields': {'output': 'failure details ' * 1500}}
    history = [{'role': 'assistant', 'content': 'x' * 3000} for _ in range(6)]
    prompt = context.prompt_context({'question': 'Explain this error', 'conversation': history},
                                    [evidence([row])], 'system', 'managed')
    packet = json.loads(prompt)
    assert packet['evidence'][0]['rows'] == [row]
    assert len(packet['conversation']) < len(history)
    assert len(prompt) <= context.MANAGED_PROMPT_CHARS


@pytest.mark.parametrize('mode', ['anthropic', 'managed'])
def test_assembled_context_budget_includes_unicode_system_history_and_evidence(mode):
    records = [evidence([{'output': '界' * 5000}] * 20) for _ in range(8)]
    system = 'schema' * 2000
    prompt = context.prompt_context({'question': 'debug', 'conversation': [
        {'content': '界' * 5000} for _ in range(6)]}, records, system, mode)
    assert len((system + prompt).encode()) <= context.MAX_CONTEXT_BYTES
    if mode == 'managed':
        assert len(prompt) <= context.MANAGED_PROMPT_CHARS
    packet = json.loads(prompt)
    assert all(e['returned_rows'] == 20 for e in packet['evidence'])
    assert all(e['preview_truncated'] for e in packet['evidence'])
    for entry in packet['evidence']:
        assert all(r['output'] == '界' * 5000 for r in entry['rows'])


def test_history_retains_source_scope_ids_and_metric_definition_not_raw_outputs():
    """AC-ASSIST-008.3 Follow-ups retain definitions and retrievable references."""
    history = [{'role': 'assistant', 'content': 'Past answer', 'sources': [{
        'kind': 'session_evidence', 'read': {'session_id': 'codex:s', 'runtime': 'codex'},
        'coverage': {'scope': {'node_id': 'this-node'}}, 'next_cursor': 'page2',
        'metric_contract': {'denominator': 'tool results', 'time_range': '2026-10-04'},
        'preview': [{'event_id': 'codex:s:1', 'fields': {'output': 'VERY LARGE OLD OUTPUT'}}],
    }]}]
    compact = context.history_context(history, lambda value: value)
    source = compact[0]['sources'][0]
    assert source['read']['session_id'] == 'codex:s'
    assert source['metric_contract']['denominator'] == 'tool results'
    assert source['next_cursor'] == 'page2'
    assert source['references'] == [{'event_id': 'codex:s:1'}]
    assert 'VERY LARGE OLD OUTPUT' not in json.dumps(compact)


def test_discovery_then_paired_error_read_then_field_continuation(monkeypatch):
    """AC-ASSIST-008.2 Exact call identity survives intervening observations."""
    monkeypatch.setattr(service, '_planner_system', lambda store: service._PLAN)
    prompts, calls = [], []
    plans = [
        {'queries': [{'sql': 'SELECT session_id FROM sessions LIMIT 1'}], 'investigate': True},
        {'session_reads': [{'session_id': 'codex:s', 'runtime': 'codex', 'mode': 'errors'}], 'investigate': True},
        {'session_reads': [{'session_id': 'codex:s', 'runtime': 'codex', 'mode': 'event',
                            'event_id': 'events:codex:s:2', 'field': 'output', 'offset': 4000}]},
    ]

    def generate(system, prompt):
        packet = json.loads(prompt)
        prompts.append(packet)
        if system == service._SYNTHESIS:
            assert packet['evidence'][1]['rows'][0]['pairing']['status'] == 'paired'
            assert packet['evidence'][2]['rows'][0]['fields']['output'] == 'Actual failure detail'
            return 'The command failed with the recorded error [2][3].'
        return json.dumps(plans.pop(0))

    def store(method, **kwargs):
        calls.append((method, kwargs))
        if method == 'query_assistant_sql':
            return {'rows': [{'session_id': 'codex:s'}]}
        assert kwargs['node_id'] == 'trusted-node'
        if kwargs.get('offset'):
            rows = [{'event_id': 'events:codex:s:2', 'fields': {'output': 'Actual failure detail'}}]
        else:
            rows = [{'event_id': 'events:codex:s:2', 'call_id': 'call1',
                     'fields': {'command': 'pytest', 'output': 'First excerpt'},
                     'field_status': {'output': {'status': 'truncated', 'next_offset': 4000}},
                     'pairing': {'status': 'paired', 'call_event_id': 'events:codex:s:1'}}]
        return {'items': rows, 'scope': {'session_id': 'codex:s'}, 'coverage': {'returned': 1}}

    response, history = service._answer_chat('anthropic', 'Why did the command fail?', 'c', [],
                                             generate, store, node_id='trusted-node')
    assert len(calls) == 3
    assert calls[-1][1]['offset'] == 4000
    assert response['sources'][1]['kind'] == 'session_evidence'
    assert response['sources'][1]['coverage']['coverage']['returned'] == 1
    assert response['sources'][1]['coverage']['scope']['session_id'] == 'codex:s'
    assert response['sources'][1]['preview'][0]['fields']['command'] == 'pytest'
    assert history[-1]['sources'] == response['sources']
    assert prompts[1]['evidence'][0]['rows'][0]['session_id'] == 'codex:s'


def test_metric_definition_survives_saving_and_next_turn_with_observation_time():
    """AC-ASSIST-008.4 Preserve population and basis instead of just old prose."""
    definition = {'population': 'tool result rows', 'runtime': 'codex',
                  'time_range': '2026-10-04 00:00 through 2026-10-05 00:00',
                  'timezone': 'UTC', 'numerator': '299 recorded error results',
                  'denominator': '6357 recorded tool results', 'token_basis': 'unknown'}
    metric = context.metric_contract({'metric_contract': definition}, '2026-10-05T07:00:00Z')
    sources = context.saved_sources([evidence([{'errors': 299, 'results': 6357}], metric_contract=metric)])
    prior = context.history_context([{'role': 'assistant', 'sources': sources}], lambda value: value)
    retained = prior[0]['sources'][0]['metric_contract']
    assert all(retained[key] == value for key, value in definition.items())
    assert retained['observed_at'] == '2026-10-05T07:00:00Z'


def test_repeated_reads_deduplicate_and_eight_read_budget_is_shared(monkeypatch):
    monkeypatch.setattr(service, '_planner_system', lambda store: service._PLAN)
    reads, passes = [], []
    def generate(system, prompt):
        if system == service._SYNTHESIS:
            return 'Bounded answer'
        passes.append(1)
        return json.dumps({'queries': [{'sql': f'SELECT {n} AS n FROM sessions'}
                                      for n in range((len(passes)-1)*4, len(passes)*4)],
                           'investigate': True})
    def store(method, **kwargs):
        reads.append(kwargs)
        return {'rows': [{'n': 1}]}
    service._answer_chat('anthropic', 'Inspect', 'c', [], generate, store)
    assert len(reads) == 8 and len(passes) == 2
    reads.clear()
    def same(system, prompt):
        return 'Answer' if system == service._SYNTHESIS else json.dumps({
            'queries': [{'sql': 'SELECT 1 AS n FROM sessions'}] * 4, 'investigate': True})
    service._answer_chat('anthropic', 'Inspect', 'c', [], same, store)
    assert len(reads) == 1


def test_no_model_node_override_or_arbitrary_reader_kwargs():
    with pytest.raises(ValueError):
        service._read_arguments({'session_id': 'codex:s', 'runtime': 'codex', 'node_id': 'other'}, 'this')
    with pytest.raises(ValueError):
        service._read_arguments({'session_id': 'codex:s', 'runtime': 'codex', 'path': '/tmp/log'}, 'this')


def test_phase_timeout_interrupts_blocking_work_and_keeps_parent_usable():
    parent = StreamJob(lambda: None)
    released = threading.Event()
    start = time.monotonic()
    with pytest.raises(PhaseExpired):
        with PhaseControl(parent, start + .08) as phase:
            with phase.resource(released.set):
                assert released.wait(1), 'timer did not interrupt blocking resource'
    assert time.monotonic() - start < 1
    parent.check()
    assert not parent.cancelled.is_set()


def test_stop_during_later_phase_interrupts_resource_and_never_becomes_budget_expiry():
    parent = StreamJob(lambda: None)
    with PhaseControl(parent, time.monotonic() + 5):
        pass
    released = threading.Event()
    with pytest.raises(Cancelled):
        with PhaseControl(parent, time.monotonic() + 5) as phase:
            with phase.resource(released.set):
                parent.abort()
                assert released.wait(.1)


def test_phase_timer_wakes_real_blocking_http_read_without_cancelling_synthesis():
    release = threading.Event()
    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            self.send_response(200)
            self.send_header('Content-Length', '100')
            self.end_headers()
            self.wfile.flush()
            release.wait(3)

        def log_message(self, *args):
            pass

    server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    worker = threading.Thread(target=lambda: server.serve_forever(poll_interval=.02), daemon=True)
    worker.start()
    parent = StreamJob(lambda: None)
    start = time.monotonic()
    try:
        with pytest.raises(PhaseExpired):
            with PhaseControl(parent, start + .2) as phase:
                with http_response(f'http://127.0.0.1:{server.server_port}/', payload=b'',
                                   headers={}, control=phase) as response:
                    response.read(100)
        assert time.monotonic() - start < 1.5
        parent.check()
        assert not parent.cancelled.is_set()
    finally:
        release.set()
        server.shutdown()
        server.server_close()
        worker.join(1)


def test_connection_setup_timeout_is_clamped_to_phase_deadline(monkeypatch):
    import urllib.request
    parent = StreamJob(lambda: None)
    phase = PhaseControl(parent, time.monotonic() + .4)
    captured = []
    class Opened:
        def __enter__(self):
            return self
        def __exit__(self, *args):
            return False
    class Opener:
        def open(self, request, timeout):
            captured.append(timeout)
            return Opened()
    monkeypatch.setattr(urllib.request, 'build_opener', lambda *args: Opener())
    with phase, http_response('http://127.0.0.1:1234', payload=b'', headers={}, control=phase):
        pass
    assert 0 < captured[0] <= .4


def test_phase_timer_reaps_real_harness_child_and_keeps_parent_usable(tmp_path, monkeypatch):
    from pathlib import Path
    from tests.test_assistant_stream import cli_stub
    from clawmetry import assistant_providers

    seen = cli_stub(tmp_path, monkeypatch, sleep=True)
    parent = StreamJob(lambda: None)
    with pytest.raises(PhaseExpired):
        with PhaseControl(parent, time.monotonic() + .3) as phase:
            iterator = assistant_providers.cli_text('claude', 'system', 'prompt', phase)
            assert next(iterator) == 'Visible '
            list(iterator)
    assert seen['proc'].poll() is not None and seen['proc'].stdout.closed
    assert not Path(seen['cwd']).exists()
    parent.check()


def test_redirect_recomputes_tcp_timeout_from_remaining_phase_budget(monkeypatch):
    import socket
    parent = StreamJob(lambda: None)
    phase = PhaseControl(parent, time.monotonic() + 1)
    captured = []
    original = socket.create_connection
    def connect(address, timeout=socket._GLOBAL_DEFAULT_TIMEOUT, source_address=None):
        captured.append((timeout, phase.deadline - time.monotonic()))
        return original(address, timeout, source_address)
    monkeypatch.setattr(socket, 'create_connection', connect)
    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            time.sleep(.15)
            self.send_response(302)
            self.send_header('Location', '/answer')
            self.send_header('Content-Length', '0')
            self.end_headers()
        def do_GET(self):
            self.send_response(200)
            self.send_header('Content-Length', '2')
            self.end_headers()
            self.wfile.write(b'ok')
        def log_message(self, *args):
            pass
    server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    thread = threading.Thread(target=lambda: server.serve_forever(poll_interval=.02), daemon=True)
    thread.start()
    try:
        with phase, http_response(f'http://127.0.0.1:{server.server_port}/', payload=b'',
                                  headers={}, control=phase) as response:
            assert response.read() == b'ok'
        assert len(captured) == 2
        assert captured[1][0] < captured[0][0] - .1
        assert all(timeout <= remaining + .005 for timeout, remaining in captured)
    finally:
        server.shutdown()
        server.server_close()
        thread.join(1)


def test_reader_phase_expiry_synthesizes_existing_evidence(monkeypatch):
    monkeypatch.setattr(service, '_planner_system', lambda store: service._PLAN)
    calls = []
    def generate(system, prompt):
        calls.append(system)
        if system == service._SYNTHESIS:
            packet = json.loads(prompt)
            assert 'time limit' in packet['investigation_status']
            assert packet['evidence'][0]['rows'] == [{'errors': 17}]
            return 'I found 17 errors; the investigation time limit prevented reading details [1].'
        if len(calls) > 1:
            raise PhaseExpired()
        return json.dumps({'queries': [{'sql': 'SELECT COUNT(*) AS errors FROM events'}], 'investigate': True})
    response, _ = service._answer_chat('anthropic', 'Debug', 'c', [], generate,
                                      lambda *a, **kw: {'rows': [{'errors': 17}]})
    assert '17 errors' in response['answer']
    assert len(calls) == 3


def test_service_produced_source_preserves_read_coverage_in_the_browser(monkeypatch):
    monkeypatch.setattr(service, '_planner_system', lambda store: service._PLAN)
    reader_result = {**copy.deepcopy(SOURCE['coverage']), 'items': copy.deepcopy(SOURCE['preview'])}
    read = copy.deepcopy(SOURCE['read'])

    def generate(system, prompt):
        if system == service._SYNTHESIS:
            return 'The recorded command failed [1].'
        return json.dumps({'session_reads': [read]})

    def store(method, **kwargs):
        assert method == 'query_assistant_session_evidence'
        assert kwargs['session_id'] == read['session_id']
        assert kwargs['node_id'] == 'test-node'
        return reader_result

    response, messages = service._answer_chat('anthropic', 'Why did this fail?', 'saved', [],
                                               generate, store, node_id='test-node')
    source = response['sources'][0]
    assert source['coverage']['coverage']['scanned'] == 53
    assert source['coverage']['next_cursor'] == reader_result['next_cursor']
    assert source['coverage']['scope'] == reader_result['scope']
    assert messages[-1]['sources'] == response['sources']
    _render(source, r"""
assert.match(sources.textContent, /53 records checked/);
assert.match(sources.textContent, /Recorded through: 2026-10-05T07:00:00Z/);
assert.match(sources.textContent, /More records remain to be checked/);
assert.match(sources.textContent, /Characters 501 to 525 of 900/);
const button=byClass(sources,'cm-assistant-evidence-open')[0];
button.dispatch('click');assert.deepEqual(opened,[source.read.session_id]);
""", "const opened=[];context.openTrail=sid=>opened.push(sid);")
