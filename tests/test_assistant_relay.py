"""Real encryption, cancellation and receipt-only recovery.

Covers AC-ASSIST-007.2, AC-ASSIST-007.4, AC-ASSIST-007.6 and AC-ASSIST-007.8.
"""
import hashlib
import threading
import time
import uuid

import pytest

from clawmetry import assistant_executor as execution, assistant_relay as relay
from clawmetry import assistant_service as service
from clawmetry.sync import encrypt_payload, generate_encryption_key
from tests.test_assistant_executor import stack, generator, wait


@pytest.fixture
def remote(stack, monkeypatch):
    executor, client, store = stack
    config = {'node_id': executor.node_id, 'api_key': 'cm-test-owner', 'encryption_key': generate_encryption_key()}
    monkeypatch.setattr(relay, '_identity', None)
    monkeypatch.setattr(relay, '_allowed', lambda: True)
    monkeypatch.setattr(relay, '_config_reader', lambda: dict(config))
    monkeypatch.setattr(relay, '_active', set())
    monkeypatch.setattr(relay, '_slots', threading.BoundedSemaphore(8))
    relay.capability(config)
    yield executor, config, store
    deadline = time.monotonic()+4
    while relay._active and time.monotonic() < deadline:
        time.sleep(.01)
    assert not relay._active


def request(executor, config, operation='chat', payload=None, **overrides):
    now = int(time.time()*1000)
    body = {'v': 1, 'node_id': config['node_id'], 'epoch': executor.epoch,
            'request_id': uuid.uuid4().hex, 'operation': operation,
            'payload': payload if payload is not None else {'message': 'Count', 'stream': True},
            'issued_at_ms': now, 'expires_at_ms': now+30000, **overrides}
    return body, action(config, body)


def action(config, body):
    rid = body['request_id']
    return {'type': 'assistant_request', 'id': rid, 'epoch': body['epoch'],
            'cache_key': f"assistant:{hashlib.sha256(config['api_key'].encode()).hexdigest()}:{config['node_id']}:{rid}",
            'sealed': encrypt_payload(body, config['encryption_key'])}


def control(config, body, action='cancel', seq=1, **overrides):
    now = int(time.time()*1000)
    value = {**{k: body[k] for k in ('v', 'node_id', 'epoch', 'request_id')},
             'operation': 'control', 'control_seq': seq, 'action': action,
             'issued_at_ms': now, 'lease_until_ms': now+29000, **overrides}
    sealed = encrypt_payload(value, config['encryption_key'])
    return {'id': hashlib.sha256(sealed.encode()).hexdigest(), 'sealed': sealed}


def finish_relay():
    deadline = time.monotonic()+4
    while relay._active and time.monotonic() < deadline:
        time.sleep(.01)
    assert not relay._active


def decrypt(config, payload):
    return relay._open(payload['blob'], config['encryption_key'], execution.MAX_JOURNAL_BYTES)


def test_encrypted_real_deltas_and_exact_completed_journal_restart_recovery(remote, monkeypatch):
    executor, config, store = remote
    calls = generator(monkeypatch)
    body, delivery = request(executor, config)
    uploads = []
    monkeypatch.setattr(relay, '_post', lambda cfg, payload: uploads.append(payload) or {'controls': [], 'terminal': False})
    assert relay.dispatch(config, delivery)
    finish_relay()
    final = decrypt(config, uploads[-1])
    assert final['terminal'] and final['http_status'] == 200
    assert any(e['event'] == 'delta' for e in final['events'])
    assert [e['seq'] for e in final['events']] == list(range(1, len(final['events'])+1))
    assert len(calls) == 2
    executor2 = execution.Executor(store, config['node_id'])
    monkeypatch.setattr(execution, '_executor', executor2)
    monkeypatch.setattr(executor2, 'start', lambda **kw: pytest.fail('recovery started new work'))
    assert relay.dispatch(config, delivery)
    finish_relay()
    assert decrypt(config, uploads[-1]) == final
    assert len(calls) == 2 and len(store.query_assistant_conversations()) == 1


def test_queued_cancel_with_full_inference_slots_tombstones_before_ack_and_redelivery(remote, monkeypatch):
    executor, config, store = remote
    monkeypatch.setattr(service.assistant_providers, 'generate', lambda *a, **kw: pytest.fail('cancelled request inferred'))
    assert executor.slots.acquire(False) and executor.slots.acquire(False)
    body, delivery = request(executor, config)
    cancel = control(config, body)
    uploads = []
    def exchange(cfg, payload):
        uploads.append(payload)
        if cancel['id'] in payload.get('control_ack', []):
            with store._write_lock:
                assert store._conn.execute('SELECT state FROM assistant_requests WHERE request_id=?', [body['request_id']]).fetchone()[0] == 'failed'
        return {'controls': [cancel] if len(uploads) == 1 else [], 'terminal': False}
    monkeypatch.setattr(relay, '_post', exchange)
    try:
        assert relay.dispatch(config, delivery)
        finish_relay()
        assert decrypt(config, uploads[-1])['http_status'] == 499
    finally:
        executor.slots.release(); executor.slots.release()
    # Even without a cloud terminal hint, the durable tombstone wins.
    assert relay.dispatch(config, delivery)
    finish_relay()
    assert decrypt(config, uploads[-1])['http_status'] == 499
    assert not store.query_assistant_conversations()


def test_busy_terminal_redelivery_does_not_start_after_capacity_frees(remote, monkeypatch):
    executor, config, store = remote
    monkeypatch.setattr(service.assistant_providers, 'generate', lambda *a, **kw: pytest.fail('terminal request inferred'))
    executor.slots.acquire(); executor.slots.acquire()
    body, delivery = request(executor, config)
    terminal = [False]
    uploads = []
    def exchange(cfg, payload):
        uploads.append(payload)
        if payload.get('terminal'):
            terminal[0] = True
        return {'controls': [], 'terminal': terminal[0]}
    monkeypatch.setattr(relay, '_post', exchange)
    try:
        assert relay.dispatch(config, delivery)
        finish_relay()
        assert decrypt(config, uploads[-1])['http_status'] == 429
    finally:
        executor.slots.release(); executor.slots.release()
    assert relay.dispatch(config, delivery)
    finish_relay()
    assert 'blob' not in uploads[-1]
    assert not store.query_assistant_conversations()


@pytest.mark.parametrize('change', ['node', 'epoch', 'digest', 'owner', 'key', 'expiry'])
def test_bound_request_rejection_never_calls_provider(remote, monkeypatch, change):
    executor, config, store = remote
    monkeypatch.setattr(executor, 'start', lambda **kw: pytest.fail('invalid request started'))
    body, delivery = request(executor, config)
    if change == 'node': body['node_id'] = 'other'
    if change == 'epoch': body['epoch'] = uuid.uuid4().hex
    if change == 'digest':
        digest = hashlib.sha256(execution.encode({'operation': 'chat', 'payload': body['payload']})).hexdigest()
        executor.receipts.claim(body['request_id'], body['epoch'], 'chat', digest)
        body['epoch'] = uuid.uuid4().hex
        body['payload']['message'] = 'Different'
    if change == 'expiry': body['issued_at_ms'] -= 31000; body['expires_at_ms'] -= 31000
    delivery = action(config, body)
    if change == 'owner': delivery['cache_key'] = 'assistant:other:node:'+body['request_id']
    if change == 'key': delivery['sealed'] = encrypt_payload(body, generate_encryption_key())
    assert relay.dispatch(config, delivery) is False
    assert not store.query_assistant_conversations()


def test_old_epoch_interrupted_receipt_never_calls_start(remote, monkeypatch):
    executor, config, store = remote
    body, delivery = request(executor, config)
    digest = hashlib.sha256(execution.encode({'operation': body['operation'], 'payload': body['payload']})).hexdigest()
    executor.receipts.claim(body['request_id'], body['epoch'], body['operation'], digest)
    restarted = execution.Executor(store, config['node_id'])
    monkeypatch.setattr(execution, '_executor', restarted)
    monkeypatch.setattr(restarted, 'start', lambda **kw: pytest.fail('interrupted recovery inferred'))
    uploads = []
    monkeypatch.setattr(relay, '_post', lambda cfg, payload: uploads.append(payload) or {'controls': []})
    assert relay.dispatch(config, delivery)
    finish_relay()
    final = decrypt(config, uploads[-1])
    assert final['epoch'] == body['epoch'] and final['http_status'] == 503
    assert final['events'][-1]['event'] == 'error'


def test_authenticated_stale_cancel_wins_and_foreign_controls_not_acknowledged(remote):
    executor, config, store = remote
    body, _ = request(executor, config)
    job = execution.Job(executor, body['request_id'], 'chat', 30, lambda: None, None)
    renew = control(config, body, 'renew', 8)
    cancel = control(config, body, 'cancel', 7)
    foreign = control(config, body, 'cancel', 9, node_id='other')
    assert relay._controls(job, [renew, cancel, foreign, renew], config) == [renew['id'], cancel['id'], renew['id']]
    assert job.cancelled.is_set()


def test_compressed_decoded_bounds_and_key_authentication(remote):
    executor, config, store = remote
    sealed = encrypt_payload({'content': 'x'*100000}, config['encryption_key'], compress=True)
    with pytest.raises(ValueError): relay._open(sealed, config['encryption_key'], 4096)
    with pytest.raises(Exception): relay._open(sealed, generate_encryption_key(), 4096)


def test_identity_rotates_capability_and_rejects_previous_key(remote, monkeypatch):
    executor, config, store = remote
    previous = relay.capability(config)['epoch']
    _, delivery = request(executor, config)
    config['encryption_key'] = generate_encryption_key()
    assert relay.capability(config)['epoch'] != previous
    assert not relay.dispatch(config, delivery)
    monkeypatch.setattr(relay, '_allowed', lambda: False)
    assert relay.capability(config)['paused'] is True


def test_lost_terminal_reply_retries_identical_ciphertext(remote, monkeypatch):
    executor, config, store = remote
    generator(monkeypatch)
    _, delivery = request(executor, config)
    terminal_blobs = []
    def exchange(cfg, payload):
        if payload.get('terminal'):
            terminal_blobs.append(payload['blob'])
            if len(terminal_blobs) == 1:
                raise TimeoutError('lost response after accepted upload')
        return {'controls': [], 'terminal': False}
    monkeypatch.setattr(relay, '_post', exchange)
    assert relay.dispatch(config, delivery)
    finish_relay()
    assert len(terminal_blobs) == 2 and terminal_blobs[0] == terminal_blobs[1]
