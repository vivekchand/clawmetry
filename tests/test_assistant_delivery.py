"""Collection-independent encrypted delivery, wake budgets and lifecycle.

AC-ASSIST-007.2
AC-ASSIST-007.4
AC-ASSIST-007.6
AC-ASSIST-007.8
"""
import copy
import io
import json
import queue
import threading
import time
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from types import SimpleNamespace
from urllib.parse import parse_qs, urlsplit

import pytest

from clawmetry import assistant_executor as execution, assistant_relay as relay, sync
from tests.test_assistant_executor import stack, generator
from tests.test_assistant_relay import remote, request, decrypt, finish_relay


@pytest.fixture
def delivery(remote, monkeypatch):
    monkeypatch.setattr(relay, '_delivery_worker', None)
    monkeypatch.setattr(relay, '_wake_hint', threading.Event())
    monkeypatch.setattr(sync, '_WAKE_POLL_MUTED_UNTIL', 0)
    monkeypatch.delenv('CLAWMETRY_WAKE_POLL', raising=False)
    yield remote
    relay.stop_delivery()
    if relay._delivery_worker:
        relay._delivery_worker.thread.join(3)
        assert not relay._delivery_worker.thread.is_alive()


def eventually(predicate, seconds=3):
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        if predicate():
            return
        time.sleep(.01)
    assert predicate()


def test_sealed_requests_complete_while_collector_is_blocked_beyond_start_validity(delivery, monkeypatch):
    """An actual 31s collector stall cannot expire new requests or stall deltas.

    Real AES envelopes, executor, writer and encrypted cumulative journals;
    the provider and cloud transport are controlled unit-test dependencies.
    """
    executor, config, store = delivery
    calls = generator(monkeypatch)
    collecting, release = threading.Event(), threading.Event()
    collector = threading.Thread(target=lambda: (collecting.set(), release.wait(40)))
    mailbox = queue.Queue()
    uploads = []
    poll_starts = []

    def poll(cfg, wait_secs, **kwargs):
        poll_starts.append(time.monotonic())
        assert kwargs['assistant_epoch'] == executor.epoch
        while not kwargs['control'].cancelled.wait(.01):
            try:
                return {'assistant_actions': [mailbox.get_nowait()]}
            except queue.Empty:
                pass
        return None

    monkeypatch.setattr(sync, '_wake_wait', poll)
    monkeypatch.setattr(sync, 'send_heartbeat', lambda *a: pytest.fail('worker sent a heartbeat'))
    monkeypatch.setattr(sync, '_dispatch_pending_queries', lambda *a: pytest.fail('worker ran generic queries'))
    monkeypatch.setattr(relay, '_post', lambda cfg, payload: uploads.append(payload) or {'controls': []})
    collector.start()
    assert collecting.wait(1)
    started = time.monotonic()
    try:
        body, sealed = request(executor, config)
        mailbox.put(sealed)
        assert relay.start_delivery()
        eventually(lambda: any(p.get('terminal') for p in uploads))
        final = decrypt(config, next(p for p in uploads if p.get('terminal')))
        assert any(e['event'] == 'delta' for e in final['events'])
        assert final['events'][-1]['event'] == 'done'
        assert time.time()*1000 < body['expires_at_ms']
        assert store.query_assistant_conversation(conversation_id=body['request_id'])
        # Same-ID redelivery through wake cannot repeat provider work.
        mailbox.put(sealed)
        eventually(lambda: len([p for p in uploads if p.get('terminal')]) == 2)
        assert len(calls) == 2
        # Keep collection unavailable for longer than the entire start TTL.
        assert not release.wait(max(0, 31-(time.monotonic()-started)))
        assert collector.is_alive() and time.monotonic()-started >= 31
        read, sealed_read = request(executor, config, 'panels_list', {})
        mailbox.put(sealed_read)
        eventually(lambda: any(p.get('request_id') == read['request_id'] and p.get('terminal') for p in uploads))
        assert time.time()*1000 < read['expires_at_ms']
        assert len(calls) == 2
        assert all(b-a >= .98 for a, b in zip(poll_starts, poll_starts[1:]))
    finally:
        release.set()
        collector.join(2)


@pytest.mark.parametrize('change', ['node_id', 'api_key', 'encryption_key', 'epoch', 'executor', 'paused'])
def test_inflight_identity_change_discards_actions_and_hints(delivery, monkeypatch, change):
    executor, config, store = delivery
    entered, finish = threading.Event(), threading.Event()
    original_epoch = executor.epoch
    old_config = dict(config)
    _, sealed = request(executor, config, 'panels_list', {})
    dispatched = []

    def poll(*a, **kw):
        entered.set()
        assert finish.wait(2)
        return {'assistant_actions': [sealed], 'work': True, 'viewer_active': True}

    monkeypatch.setattr(sync, '_wake_wait', poll)
    monkeypatch.setattr(relay, 'dispatch', lambda *a: dispatched.append(a))
    relay.start_delivery()
    assert entered.wait(1)
    if change in config:
        config[change] = 'new-identity'
    elif change == 'epoch':
        executor.epoch = uuid.uuid4().hex
    elif change == 'executor':
        monkeypatch.setattr(execution, '_executor', execution.Executor(store, config['node_id']))
    else:
        monkeypatch.setattr(relay, '_allowed', lambda: False)
    finish.set()
    eventually(lambda: relay._delivery_worker.transport is None)
    relay.stop_delivery()
    assert not dispatched and not relay._wake_hint.is_set()
    if change in config:
        new_epoch = executor.epoch
        assert new_epoch != original_epoch
        # A concurrent heartbeat carrying the old configuration cannot rotate
        # the newly bound executor back to the old account/key/node.
        assert not relay.capability(old_config)['enabled']
        assert executor.epoch == new_epoch


def test_each_action_rechecks_identity_and_never_dispatches_generic_actions(delivery, monkeypatch):
    executor, config, _ = delivery
    _, sealed = request(executor, config, 'panels_list', {})
    dispatched = []
    def dispatch(cfg, action):
        dispatched.append(action)
        config['api_key'] = 'rotated-owner'
    monkeypatch.setattr(relay, 'dispatch', dispatch)
    monkeypatch.setattr(sync, '_wake_wait', lambda *a, **kw: {'assistant_actions': [
        {'type': 'approval_decision'}, sealed, sealed]})
    relay.start_delivery()
    eventually(lambda: len(dispatched) == 1)
    relay.stop_delivery()
    assert dispatched == [sealed]


def test_wake_keeps_old_envelope_epoch_for_receipt_only_recovery(delivery, monkeypatch):
    executor, config, store = delivery
    calls = generator(monkeypatch)
    body, sealed = request(executor, config)
    uploads = []
    monkeypatch.setattr(relay, '_post', lambda cfg, payload: uploads.append(payload) or {'controls': []})
    assert relay.dispatch(config, sealed)
    finish_relay()
    final = decrypt(config, uploads[-1])
    replacement = execution.Executor(store, config['node_id'])
    monkeypatch.setattr(execution, '_executor', replacement)
    monkeypatch.setattr(replacement, 'start', lambda **kw: pytest.fail('recovery started work'))
    assert replacement.epoch != body['epoch']
    uploads.clear()
    def poll(cfg, wait_secs, **kw):
        assert kw['assistant_epoch'] == replacement.epoch
        return {'assistant_actions': [sealed]}
    monkeypatch.setattr(sync, '_wake_wait', poll)
    relay.start_delivery()
    eventually(lambda: any(p.get('terminal') for p in uploads))
    relay.stop_delivery()
    assert decrypt(config, uploads[-1]) == final
    assert len(calls) == 2


@pytest.mark.parametrize('response', [None, {}, {'work': True, 'viewer_active': True},
    {'assistant_actions': [], 'viewer_active': True}, {'assistant_actions': 'invalid'},
    {'assistant_actions': [{'type': 'assistant_request'}]*9},
    {'assistant_actions': [{'type': 'assistant_request'}]}])
def test_idle_legacy_error_and_active_poll_budgets(delivery, monkeypatch, response):
    """Run 120 virtual seconds and count requests, not just delay constants."""
    now = [100.0]
    starts = []
    seen = []
    worker = relay._DeliveryWorker()
    class Stop:
        stopped = False
        def is_set(self): return self.stopped
        def wait(self, seconds):
            assert seconds >= 1
            now[0] += seconds
            self.stopped = now[0] >= 220
    worker.stop = Stop()
    monkeypatch.setattr(relay.time, 'monotonic', lambda: now[0])
    monkeypatch.setattr(worker, 'poll', lambda *a: starts.append(now[0]) or copy.deepcopy(response))
    monkeypatch.setattr(relay, 'dispatch', lambda cfg, action: seen.append(action))
    worker.run()
    assert all(b-a >= 1 for a, b in zip(starts, starts[1:]))
    if response and response.get('assistant_actions') == [{'type': 'assistant_request'}]:
        assert len(starts) == len(seen) == 120
    else:
        assert len(starts) <= 12 and not seen
    assert relay._wake_hint.is_set() is bool(response and (response.get('work') or response.get('viewer_active')))


def test_lifecycle_never_replaces_a_still_blocked_poll(delivery, monkeypatch):
    entered, finish = threading.Event(), threading.Event()
    polls = []
    def poll(*a, **kw):
        polls.append(1)
        entered.set()
        assert finish.wait(2)
        return {'assistant_actions': [], 'work': True}
    monkeypatch.setattr(sync, '_wake_wait', poll)
    assert relay.start_delivery()
    first = relay._delivery_worker
    assert entered.wait(1)
    assert relay.start_delivery() and relay._delivery_worker is first
    relay.stop_delivery()
    assert not relay.start_delivery() and relay._delivery_worker is first
    finish.set()
    first.thread.join(2)
    assert not first.thread.is_alive() and not relay._wake_hint.is_set()
    assert len(polls) == 1
    assert relay.start_delivery() and relay._delivery_worker is not first


@pytest.mark.parametrize('part', ['headers', 'body', 'proxy_headers', 'proxy_tls'])
@pytest.mark.parametrize('stop', [False, True])
def test_delivery_transport_interrupts_real_drip_socket(monkeypatch, part, stop):
    # This transport test also runs on all three native API-test runners,
    # without requiring a DuckDB or cryptography installation there.
    config = {'node_id': 'node-test', 'api_key': 'owner', 'encryption_key': 'key'}
    executor = SimpleNamespace(epoch=uuid.uuid4().hex, node_id=config['node_id'])
    monkeypatch.setattr(execution, 'current', lambda: executor)
    monkeypatch.setattr(relay, '_identity', None)
    monkeypatch.setattr(relay, '_config_reader', lambda: dict(config))
    monkeypatch.setattr(relay, '_allowed', lambda: True)
    monkeypatch.setattr(relay, '_delivery_worker', None)
    monkeypatch.setattr(relay, '_wake_hint', threading.Event())
    monkeypatch.setattr(sync, '_WAKE_POLL_MUTED_UNTIL', 0)
    monkeypatch.delenv('CLAWMETRY_WAKE_POLL', raising=False)
    reached, finish = threading.Event(), threading.Event()
    paths = []
    class Handler(BaseHTTPRequestHandler):
        def do_CONNECT(self):
            paths.append(self.path)
            if part == 'proxy_tls':
                self.wfile.write(b'HTTP/1.1 200 Connection established\r\n\r\n')
                self.wfile.flush()
                self.connection.settimeout(2)
                assert self.connection.recv(4096)  # real TLS ClientHello
                reached.set()
                finish.wait(3)  # never finish the TLS handshake
            else:
                self.wfile.write(b'HTTP/1.1 200 OK\r\nX-Drip: ')
                self.wfile.flush()
                reached.set()
                self.drip()

        def drip(self):
            while not finish.wait(.02):
                try:
                    self.wfile.write(b' ')
                    self.wfile.flush()
                except OSError:
                    break

        def do_GET(self):
            paths.append(parse_qs(urlsplit(self.path).query))
            if part == 'body':
                self.send_response(200)
                self.end_headers()
            else:
                self.wfile.write(b'HTTP/1.1 200 OK\r\nX-Drip: ')
                self.wfile.flush()
            reached.set()
            self.drip()
        def log_message(self, *a): pass
    server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    monkeypatch.setattr(sync, 'INGEST_URL', f'http://127.0.0.1:{server.server_port}')
    monkeypatch.setattr(relay, '_WAKE_SECONDS', .3)
    monkeypatch.setenv('no_proxy', '127.0.0.1')
    if part.startswith('proxy_'):
        monkeypatch.setenv('https_proxy', f'http://127.0.0.1:{server.server_port}')
        monkeypatch.setenv('no_proxy', '')
        monkeypatch.delenv('NO_PROXY', raising=False)
        monkeypatch.setattr(sync, 'INGEST_URL', 'https://assistant.invalid')
    server_thread.start()
    try:
        started = time.monotonic()
        relay.start_delivery()
        worker = relay._delivery_worker
        assert reached.wait(2)
        if stop:
            relay.stop_delivery()
            worker.thread.join(1)
            assert not worker.thread.is_alive()
        else:
            eventually(lambda: worker.transport is None, seconds=1)
        assert time.monotonic()-started < 1.5
        assert len(paths) == 1
        if part.startswith('proxy_'):
            assert paths == ['assistant.invalid:443']
        else:
            assert paths[0]['assistant_epoch'] == [executor.epoch]
            assert int(paths[0]['wait'][0]) <= 20
    finally:
        relay.stop_delivery()
        relay._delivery_worker.thread.join(2)
        assert not relay._delivery_worker.thread.is_alive()
        finish.set()
        server.shutdown()
        server.server_close()
        server_thread.join(2)


def test_wake_response_byte_bound_and_exact_node_encoding(monkeypatch):
    node = 'workspace/a +?雪'
    class Response(io.BytesIO):
        def __enter__(self): return self
        def __exit__(self, *a): self.close()
    def open_response(req, timeout):
        assert parse_qs(urlsplit(req.full_url).query) == {
            'node_id': [node], 'wait': ['15'], 'assistant_epoch': ['e'*32]}
        assert timeout <= 25
        return Response(b' '*(1024*1024+1))
    monkeypatch.setattr(sync.urllib.request, 'urlopen', open_response)
    monkeypatch.setattr(sync, '_WAKE_POLL_MUTED_UNTIL', 0)
    assert sync._wake_wait({'node_id': node, 'api_key': 'owner'}, 20, assistant_epoch='e'*32) is None


@pytest.mark.parametrize('node', ['node + /%?', '工作站/é +?'])
def test_delivery_transport_exact_unicode_node_wake_and_exchange(monkeypatch, node):
    seen = []
    class Handler(BaseHTTPRequestHandler):
        def reply(self):
            self.send_response(200)
            self.send_header('Content-Length', '2')
            self.end_headers()
            self.wfile.write(b'{}')
        def do_GET(self):
            seen.append((parse_qs(urlsplit(self.path).query)['node_id'][0], self.headers.get('X-Node-Id')))
            assert self.headers['X-Api-Key'] == 'owner'
            self.reply()
        def do_POST(self):
            payload = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
            seen.append((payload['node_id'], self.headers.get('X-Node-Id')))
            assert self.headers['X-Api-Key'] == 'owner'
            self.reply()
        def log_message(self, *a): pass
    server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    monkeypatch.setattr(sync, 'INGEST_URL', f'http://127.0.0.1:{server.server_port}')
    monkeypatch.setattr(sync, '_WAKE_POLL_MUTED_UNTIL', 0)
    monkeypatch.setenv('no_proxy', '127.0.0.1')
    server_thread.start()
    try:
        config = {'node_id': node, 'api_key': 'owner'}
        assert relay._DeliveryWorker().poll(config, 'e'*32) == {}
        assert relay._post(config, {'node_id': node}) == {}
        assert seen == [(node, node if node.isascii() else None)] * 2
    finally:
        server.shutdown()
        server.server_close()
        server_thread.join(2)


def test_shutdown_revokes_delivery_before_writer_flush(delivery, monkeypatch):
    monkeypatch.setattr(sync, '_shutdown_flushed', threading.Event())
    monkeypatch.setattr(sync, '_ocsf_tail_shutdown', lambda: None)
    entered = threading.Event()
    def poll(*a, **kw):
        entered.set()
        assert kw['control'].cancelled.wait(2)
        return {'assistant_actions': [], 'work': True}
    def flush():
        assert relay._delivery_worker.stop.is_set()
        return 0, 0
    monkeypatch.setattr(sync, '_wake_wait', poll)
    monkeypatch.setattr(sync, '_drain_local_store_now', flush)
    relay.start_delivery()
    assert entered.wait(1)
    sync._graceful_shutdown('test', force_exit=False)
    relay._delivery_worker.thread.join(1)
    assert not relay._delivery_worker.thread.is_alive()
    assert not relay._wake_hint.is_set()


def test_legacy_heartbeat_dispatches_assistant_before_slow_generic_query(monkeypatch):
    from routes import local_query
    order = []
    def generic(*a, **kw):
        assert order == ['a', 'b']
        order.append('query')
        return {'rows': []}
    monkeypatch.setattr(local_query, '_dispatch', generic)
    monkeypatch.setattr(sync, '_dispatch_pending_action', lambda cfg, action: order.append(action['id']))
    monkeypatch.setattr(sync, 'encrypt_payload', lambda *a: 'sealed')
    monkeypatch.setattr(sync, '_post', lambda *a, **kw: {})
    sync._dispatch_pending_queries({'node_id': 'n', 'api_key': 'k', 'encryption_key': 'k'}, [
        {'shape': 'sessions', 'id': 'query', 'cache_key': 'query', 'args': {}},
        {'type': 'assistant_request', 'id': 'a'}, None,
        {'type': 'assistant_request', 'id': 'b'}, {'type': 'other', 'id': 'other'}])
    assert order == ['a', 'b', 'query', 'other']
