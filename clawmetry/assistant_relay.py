"""Authenticated encrypted Assistant adapter over the existing node relay.

Cloud relays opaque requests and cumulative journals. Only this node decrypts
instructions, and only the shared daemon executor can query or perform inference.
"""
from __future__ import annotations

import base64
import hashlib
import json
import logging
import re
import threading
import time
import urllib.request
import uuid
import zlib

from clawmetry import assistant_executor as execution

_log = logging.getLogger(__name__)
_lock = threading.Lock()
_active = set()
_slots = threading.BoundedSemaphore(8)
_identity = None
_config_reader = None


def _identity_of(config):
    return hashlib.sha256(execution.encode([config.get(k) for k in ('node_id', 'api_key', 'encryption_key')])).digest()


def configure(config_reader):
    global _config_reader
    _config_reader = config_reader


def _allowed():
    from clawmetry.config import is_cloud_disabled
    from clawmetry.sync import _sync_allowed
    return not is_cloud_disabled() and _sync_allowed()


def capability(config):
    global _identity
    try:
        executor = execution.current()
    except Exception:
        return {'v': 1, 'epoch': '', 'enabled': False, 'paused': False}
    identity = _identity_of(config)
    with _lock:
        if _identity is not None and identity != _identity:
            executor.epoch = uuid.uuid4().hex
            executor.node_id = config.get('node_id') or 'local'
        _identity = identity
    enabled = bool(config.get('node_id') and config.get('api_key') and config.get('encryption_key'))
    return {'v': 1, 'epoch': executor.epoch, 'enabled': enabled, 'paused': not _allowed()}


def _open(sealed, key, limit):
    """Apply ciphertext AND decoded bounds before JSON, including gzip bombs."""
    from clawmetry.sync import _get_aesgcm
    if not isinstance(sealed, str) or len(sealed) > (limit+64)*2 or not re.fullmatch(r'[A-Za-z0-9_=-]+', sealed):
        raise ValueError('invalid sealed envelope')
    raw = base64.urlsafe_b64decode(sealed+'==')
    if len(raw) < 28 or len(raw) > limit+64:
        raise ValueError('invalid envelope size')
    plain = _get_aesgcm(key).decrypt(raw[:12], raw[12:], None)
    if plain.startswith(b'\x1f\x8b'):
        decoder = zlib.decompressobj(31)
        plain = decoder.decompress(plain, limit+1)
        if not decoder.eof or decoder.unused_data or decoder.unconsumed_tail:
            raise ValueError('invalid compressed envelope')
    if len(plain) > limit:
        raise ValueError('decoded envelope too large')
    def reject_constant(value):
        raise ValueError('invalid JSON number')
    value = json.loads(plain.decode('utf-8'), parse_constant=reject_constant)
    if not isinstance(value, dict):
        raise ValueError('invalid envelope')
    return value


def _milliseconds(value):
    if type(value) is not int or value < 0:
        raise ValueError('invalid timestamp')
    return value


def _validate_binding(body, node_id, epoch, request_id):
    if body.get('v') != 1 or body.get('node_id') != node_id or body.get('epoch') != epoch or body.get('request_id') != request_id:
        raise ValueError('wrong request binding')


def _post(config, payload):
    # One bounded exchange, no generic ingest retry loop: the next active tick
    # retries identical ciphertext/acks. Provider watchdog runs independently.
    from clawmetry.sync import INGEST_URL
    req = urllib.request.Request(INGEST_URL.rstrip('/')+'/ingest/assistant/exchange',
        data=execution.encode(payload), method='POST', headers={
            'Content-Type': 'application/json', 'X-Api-Key': config['api_key'], 'X-Node-Id': config['node_id']})
    with urllib.request.urlopen(req, timeout=3) as response:
        raw = response.read(256*1024+1)
    if len(raw) > 256*1024:
        raise ValueError('exchange response too large')
    result = json.loads(raw) if raw else {}
    if not isinstance(result, dict):
        raise ValueError('invalid exchange response')
    return result


def _controls(job, controls, config):
    if not isinstance(controls, list) or len(controls) > 32:
        raise ValueError('invalid controls')
    acknowledged = []
    for item in controls:
        if not isinstance(item, dict):
            continue
        sealed = item.get('sealed')
        control_id = item.get('id')
        if not isinstance(sealed, str) or not isinstance(control_id, str) or hashlib.sha256(sealed.encode()).hexdigest() != control_id:
            continue
        try:
            value = _open(sealed, config['encryption_key'], 4096)
            _validate_binding(value, job.node_id, job.epoch, job.request_id)
            if value.get('operation') != 'control' or value.get('action') not in ('renew', 'cancel'):
                raise ValueError('invalid control')
            sequence = value.get('control_seq')
            if type(sequence) is not int or not 0 < sequence <= 1000000:
                raise ValueError('invalid control sequence')
            issued = _milliseconds(value.get('issued_at_ms'))
            lease = _milliseconds(value.get('lease_until_ms'))
            now = time.time()*1000
            if issued > now+5000 or lease > issued+30000 or lease < issued:
                raise ValueError('invalid control time')
            # A late authenticated cancellation still takes effect. A stale
            # renewal is safely deduplicated; it never revives a dead lease.
            if value['action'] == 'cancel' or lease > now:
                job.control(sequence, value['action'], lease)
            acknowledged.append(control_id)
        except execution.Cancelled:
            # Already expired/cancelled work cannot be resurrected.
            acknowledged.append(control_id)
        except Exception:
            _log.warning('Assistant rejected an invalid encrypted control')
    return acknowledged


def dispatch(config, action):
    """Validate a narrow action before starting a bounded relay consumer."""
    try:
        executor = execution.current()
        cap = capability(config)
        if not cap['enabled'] or cap['paused']:
            return False
        rid = action.get('id')
        if not isinstance(rid, str) or not re.fullmatch(r'[a-f0-9]{32}', rid):
            return False
        owner = hashlib.sha256(config['api_key'].encode()).hexdigest()
        expected = f"assistant:{owner}:{config['node_id']}:{rid}"
        epoch = action.get('epoch')
        if action.get('cache_key') != expected or not isinstance(epoch, str) or not re.fullmatch(r'[a-f0-9]{32}', epoch):
            return False
        body = _open(action.get('sealed'), config['encryption_key'], execution.MAX_REQUEST_BYTES)
        _validate_binding(body, config['node_id'], epoch, rid)
        if body.get('operation') not in execution.OPERATIONS or not isinstance(body.get('payload'), dict):
            return False
        issued = _milliseconds(body.get('issued_at_ms'))
        expires = _milliseconds(body.get('expires_at_ms'))
        now = time.time()*1000
        if not issued <= expires <= issued+30000 or issued > now+5000:
            return False
        # Same-ID receipts can be read after the start expiry, but an expired
        # unclaimed envelope never launches new work.
        digest = hashlib.sha256(execution.encode({'operation': body['operation'], 'payload': body['payload']})).hexdigest()
        receipt = executor.receipts.lookup(rid, epoch, body['operation'], digest)
        if (epoch != executor.epoch or expires < now) and receipt is None:
            return False
        with _lock:
            if rid in _active:
                return True
            if not _slots.acquire(blocking=False):
                return False
            _active.add(rid)
        try:
            threading.Thread(target=_run, args=(executor, dict(config), body, receipt),
                             name='assistant-relay', daemon=True).start()
        except Exception:
            with _lock:
                _active.discard(rid)
                _slots.release()
            raise
        return True
    except Exception:
        _log.warning('Assistant rejected an invalid encrypted request')
        return False


def _run(executor, config, body, receipt=None):
    from clawmetry.sync import encrypt_payload
    rid, epoch = body['request_id'], body['epoch']
    recovering = epoch != executor.epoch
    bound = _identity_of(config)
    checked_at = [0.0]
    identity_ok = [True]

    def identity(*, force=False):
        # Check cheap identity between token chunks; re-read configuration once
        # per second. The terminal barrier below always forces a fresh read.
        now = time.monotonic()
        if force or now-checked_at[0] >= 1:
            current = _config_reader() if _config_reader else config
            identity_ok[0] = _identity_of(current) == bound and _allowed()
            checked_at[0] = now
        return identity_ok[0] and (recovering or executor.epoch == epoch)

    ack = []
    try:
        if not identity(force=True):
            return
        # An old epoch can only read an exact durable receipt. It never enters
        # start(), acquires inference admission or performs another mutation.
        if recovering:
            if receipt is None:
                return
            status = receipt['status'] or 503
            data = receipt['data'] or {'error': 'The assistant restarted before this request completed. Start a new request.'}
            journal = {'v': 1, 'node_id': config['node_id'], 'epoch': epoch, 'request_id': rid,
                       'operation': body['operation'], 'events': [{'seq': 1,
                       'event': 'done' if status < 400 else 'error', 'data': data}],
                       'terminal': True, 'http_status': status}
            journal = receipt.get('journal') or journal
            if len(execution.encode(journal)) > execution.MAX_JOURNAL_BYTES:
                return
            if identity(force=True):
                _post(config, {'node_id': config['node_id'], 'epoch': epoch, 'request_id': rid,
                              'blob': encrypt_payload(journal, config['encryption_key']), 'terminal': True})
            return
        # Fetch already queued controls before admission. Sharing the event
        # with the real job makes authenticated cancellation irreversible.
        gate = execution.Job(executor, rid, body['operation'],
            max(0, (body['issued_at_ms']+30000-time.time()*1000)/1000), lambda: None, identity)
        reply = _post(config, {'node_id': config['node_id'], 'epoch': epoch, 'request_id': rid,
                               'control_ack': []})
        if reply.get('terminal') is True:
            return  # A delayed action cannot restart a cloud-terminal request.
        ack = _controls(gate, reply.get('controls', []), config)
        result = executor.start(request_id=rid, operation=body['operation'], payload=body['payload'],
            lease_seconds=gate.lease_until-time.monotonic(), identity=identity, cancelled=gate.cancelled)
        if result.get('error'):
            if gate.cancelled.is_set():
                # Capacity/conflict failures did not durably apply cancellation.
                # Leave controls queued so a later delivery cannot resurrect it.
                ack = []
            journal = {'v': 1, 'node_id': config['node_id'], 'epoch': epoch, 'request_id': rid,
                       'operation': body['operation'], 'events': [{'seq': 1, 'event': 'error',
                       'data': {'error': result['error']}}], 'terminal': True, 'http_status': result['http_status']}
            if identity(force=True):
                _post(config, {'node_id': config['node_id'], 'epoch': epoch, 'request_id': rid,
                              'blob': encrypt_payload(journal, config['encryption_key']), 'terminal': True,
                              'control_ack': ack})
            return
        job = executor.jobs[rid]
        ack = _controls(job, reply.get('controls', []), config)
        last_blob = None
        sealed_raw = None
        sealed_blob = None
        last_send = 0.0
        terminal_attempts = 0
        while True:
            if not identity() or executor.epoch != epoch:
                executor.cancel(request_id=rid)
                return  # Never upload under a removed/changed node credential.
            data = executor.read(request_id=rid)
            terminal = data.get('terminal', False)
            now = time.monotonic()
            if now-last_send < 1 and not terminal:
                time.sleep(0.05)
                continue
            raw = execution.encode(data)
            if len(raw) > execution.MAX_JOURNAL_BYTES:
                executor.cancel(request_id=rid)
                return
            payload = {'node_id': config['node_id'], 'epoch': epoch, 'request_id': rid,
                       'terminal': terminal, 'control_ack': ack}
            if raw != last_blob or terminal:
                if raw != sealed_raw:
                    sealed_blob = encrypt_payload(data, config['encryption_key'])
                    sealed_raw = raw
                payload['blob'] = sealed_blob
            last_send = time.monotonic()
            try:
                reply = _post(config, payload)
                last_blob = raw
                ack = _controls(job, reply.get('controls', []), config)
                if terminal:
                    return
            except Exception:
                if terminal:
                    terminal_attempts += 1
                    if terminal_attempts >= 3:
                        return
                # No renewed authenticated control means lease expiry, even if
                # a proxy keeps accepting uploads while the browser is gone.
                time.sleep(1)
    except Exception:
        # Never include decrypted requests or provider/HTTP diagnostics here.
        _log.warning('Assistant relay exchange interrupted')
    finally:
        with _lock:
            _active.discard(rid)
            _slots.release()
