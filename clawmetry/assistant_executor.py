"""Single daemon-owned Assistant execution and persistence boundary.

Both HTTP/SSE and encrypted relay clients use typed jobs on this executor.
The inference budget and conversation locks therefore cannot multiply with web
processes. No writer or executor is created by a dashboard fallback.
"""
from __future__ import annotations

import hashlib
import json
import queue
import re
import threading
import time
import uuid

from clawmetry.assistant_receipts import Receipts
from clawmetry.assistant_service import AssistantService, Outcome, OPERATIONS, _ChatFailure, _chat_error, validate_chat
from clawmetry.assistant_stream import StreamJob, Cancelled, BrokenStream

MAX_REQUEST_BYTES = 32 * 1024
MAX_JOURNAL_BYTES = 512 * 1024
MAX_EVENTS = 512
LEASE_SECONDS = 30
TERMINAL_SECONDS = 600
DURABLE_OPERATIONS = frozenset({'chat', 'panel_create', 'panel_delete', 'credits_checkout'})


def encode(value):
    return json.dumps(value, ensure_ascii=False, separators=(',', ':'), allow_nan=False).encode('utf-8')


class Job(StreamJob):
    def __init__(self, executor, request_id, operation, lease_seconds, release, identity):
        super().__init__(release)
        self.executor = executor
        self.request_id = request_id
        self.operation = operation
        self.epoch = executor.epoch
        self.node_id = executor.node_id
        self.lock = threading.RLock()
        self.lease_until = time.monotonic() + min(LEASE_SECONDS, lease_seconds)
        self.control_seq = 0
        self.identity = identity
        self.journal_events = []
        self.terminal = False
        self.http_status = None
        self.completed_at = None
        self.pending_text = ''
        self.last_text_at = 0.0

    def check(self, *, force_identity=False):
        super().check()
        if self.epoch != self.executor.epoch:
            raise Cancelled('execution epoch changed')
        if time.monotonic() >= self.lease_until:
            raise Cancelled('lease expired')
        if self.identity is not None and not self.identity(force=force_identity):
            raise Cancelled('execution identity changed')

    def snapshot(self):
        return {'v': 1, 'node_id': self.node_id, 'epoch': self.epoch,
                'request_id': self.request_id, 'operation': self.operation,
                'events': list(self.journal_events), 'terminal': self.terminal,
                **({'http_status': self.http_status} if self.terminal else {})}

    def append(self, event, data):
        item = {'seq': len(self.journal_events)+1, 'event': event, 'data': data}
        # Reserve room for a fixed terminal error so overflow is explicit.
        if len(self.journal_events) >= MAX_EVENTS-1 or len(encode({**self.snapshot(), 'events': self.journal_events+[item]})) > MAX_JOURNAL_BYTES-1024:
            raise _ChatFailure('This response is too large. Try a narrower question or conversation.', 413)
        self.journal_events.append(item)

    def flush_text(self):
        if self.pending_text:
            self.append('delta', {'text': self.pending_text})
            self.pending_text = ''
            self.last_text_at = time.monotonic()

    def renew(self):
        with self.lock:
            self.check()
            self.lease_until = time.monotonic()+LEASE_SECONDS

    def control(self, sequence, action, lease_until_ms):
        if action == 'cancel' and not self.terminal:
            self.abort()
            return
        with self.lock:
            if self.terminal or self.cancelled.is_set():
                return
            self.check()
            if action == 'renew':
                if sequence <= self.control_seq:
                    return
                self.control_seq = sequence
                seconds = (lease_until_ms-time.time()*1000)/1000
                if not 0 < seconds <= LEASE_SECONDS+1:
                    raise ValueError('invalid lease')
                self.lease_until = time.monotonic()+min(LEASE_SECONDS, seconds)


class Executor:
    def __init__(self, store, node_id='local', *, epoch=None):
        self.store = store
        self.node_id = node_id or 'local'
        self.epoch = epoch or uuid.uuid4().hex
        self.receipts = Receipts(store)
        self.service = AssistantService(store)
        self.lock = threading.RLock()
        self.slots = threading.BoundedSemaphore(2)
        self.light_slots = threading.BoundedSemaphore(4)
        self.conversations = set()
        self.jobs = {}

    def start(self, *, request_id, operation, payload, lease_seconds=LEASE_SECONDS, identity=None, cancelled=None):
        lease_deadline = time.monotonic() + min(LEASE_SECONDS, lease_seconds)
        if not isinstance(request_id, str) or not re.fullmatch(r'[a-f0-9]{32}', request_id):
            return {'error': 'Invalid request identity.', 'http_status': 400}
        if operation not in OPERATIONS or not isinstance(payload, dict):
            return {'error': 'Invalid Assistant operation.', 'http_status': 400}
        try:
            raw = encode({'operation': operation, 'payload': payload})
            if len(raw) > MAX_REQUEST_BYTES:
                raise ValueError()
            if operation == 'chat':
                validate_chat(payload)
        except _ChatFailure as exc:
            return {'error': exc.message, 'http_status': exc.status}
        except (ValueError, TypeError, RecursionError):
            return {'error': 'The Assistant request is too large or invalid.', 'http_status': 400}
        digest = hashlib.sha256(raw).hexdigest()
        payload = json.loads(raw)['payload']
        with self.lock:
            self._prune()
            existing = self.jobs.get(request_id)
            if existing:
                if existing.digest != digest:
                    return {'error': 'This request identity was already used.', 'http_status': 409}
                if cancelled is not None and cancelled.is_set() and not existing.terminal:
                    existing.abort()
                return {'request_id': request_id, 'http_status': 202}
            if cancelled is not None and cancelled.is_set():
                # Record cancellation before acknowledging it, even when both
                # inference slots are occupied. A queued duplicate must not
                # resurrect paid work after the cloud removes the control.
                data = {'error': 'The request was cancelled before it started.'}
                status = 499
                receipt = None
                try:
                    if operation in DURABLE_OPERATIONS:
                        receipt = self.receipts.claim(request_id, self.epoch, operation, digest)
                        if receipt and receipt['state'] != 'running':
                            data, status = receipt['data'], receipt['status'] or 500
                        else:
                            self.receipts.fail(request_id, data['error'], status)
                except OverflowError:
                    return {'error': 'Assistant request storage is busy. Retry shortly.', 'http_status': 429}
                except ValueError:
                    return {'error': 'This request identity was already used.', 'http_status': 409}
                replay = Job(self, request_id, operation, LEASE_SECONDS, lambda: None, None)
                replay.digest = digest
                replay.append('done' if status < 400 else 'error', data)
                replay.terminal, replay.http_status, replay.completed_at = True, status, time.monotonic()
                if receipt and receipt.get('journal'):
                    replay = self._receipt_job(request_id, operation, digest, receipt)
                replay.finished.set()
                self.jobs[request_id] = replay
                return {'request_id': request_id, 'http_status': 202}
            admission = self.slots if operation == 'chat' else self.light_slots
            if not admission.acquire(blocking=False):
                return {'error': 'The assistant is answering other questions. Please retry shortly.', 'http_status': 429}
            prepared = None
            cid = None
            claimed = False
            locked_conversation = False
            try:
                durable = operation in DURABLE_OPERATIONS
                receipt = self.receipts.claim(request_id, self.epoch, operation, digest) if durable else None
                if receipt:
                    if receipt['state'] == 'running':
                        raise _ChatFailure('This request was interrupted. Start a new request.', 503)
                    self.jobs[request_id] = self._receipt_job(request_id, operation, digest, receipt)
                    admission.release()
                    return {'request_id': request_id, 'http_status': 202}
                claimed = durable
                if cancelled is not None and cancelled.is_set():
                    raise _ChatFailure('The request was cancelled before it started.', 499)
                if lease_seconds <= 0 or (identity is not None and not identity(force=True)):
                    raise _ChatFailure('This Assistant request expired. Please retry.', 499)
                if operation == 'chat':
                    cid = payload.get('conversation_id') or request_id
                    if cid in self.conversations:
                        raise _ChatFailure('Wait for the current answer before sending a follow-up.', 409)
                    prepared = self.service.prepare_chat(payload, request_id)
                    self.conversations.add(cid)
                    locked_conversation = True

                def release():
                    with self.lock:
                        if cid:
                            self.conversations.discard(cid)
                        admission.release()

                remaining = lease_deadline-time.monotonic()
                if remaining <= 0 or (identity is not None and not identity(force=True)):
                    raise _ChatFailure('This Assistant request expired. Please retry.', 499)
                job = Job(self, request_id, operation, remaining, release, identity)
                job.digest = digest
                if cancelled is not None:
                    job.cancelled = cancelled
                if operation == 'chat':
                    job.append('status', {'message': 'Preparing your analysis.'})
                self.jobs[request_id] = job
                worker = threading.Thread(target=self._consume, args=(job, payload, prepared),
                                          name='assistant-consumer', daemon=True)
                try:
                    worker.start()
                except Exception:
                    self.jobs.pop(request_id, None)
                    self.conversations.discard(cid)
                    raise
                return {'request_id': request_id, 'http_status': 202}
            except Exception as exc:
                if locked_conversation:
                    self.conversations.discard(cid)
                admission.release()
                message, status = _chat_error(exc)
                if isinstance(exc, OverflowError):
                    message, status = 'Assistant request storage is busy. Retry shortly.', 429
                if isinstance(exc, ValueError) and not isinstance(exc, _ChatFailure):
                    message, status = 'This request identity was already used.', 409
                if claimed:
                    self.receipts.fail(request_id, message, status)
                return {'error': message, 'http_status': status}

    def _receipt_job(self, request_id, operation, digest, receipt):
        replay = Job(self, request_id, operation, LEASE_SECONDS, lambda: None, None)
        replay.digest = digest
        journal = receipt.get('journal')
        if journal:
            replay.journal_events = journal['events']
            replay.epoch, replay.node_id = journal['epoch'], journal['node_id']
        else:
            replay.append('done' if (receipt['status'] or 500) < 400 else 'error', receipt['data'])
        replay.terminal = True
        replay.http_status = receipt['status'] or 500
        replay.completed_at = time.monotonic()
        replay.finished.set()
        return replay

    def _consume(self, job, payload, prepared):
        try:
            job.start(lambda control: self.service.execute(job.operation, payload, job.request_id, control, prepared))
            while True:
                job.check()
                try:
                    event, value = job.events.get(timeout=0.1)
                except queue.Empty:
                    job.check()
                    with job.lock:
                        if time.monotonic()-job.last_text_at >= 0.5:
                            job.flush_text()
                    if job.finished.is_set() and job.events.empty():
                        raise BrokenStream()
                    continue
                with job.lock:
                    job.check()
                    if event == 'failure':
                        raise value
                    if event == 'result':
                        job.flush_text()
                        terminal = {'seq': len(job.journal_events)+1, 'event': 'done', 'data': value.data}
                        prospective = {**job.snapshot(), 'events': job.journal_events+[terminal],
                                       'terminal': True, 'http_status': value.status}
                        if len(prospective['events']) > MAX_EVENTS or len(encode(prospective)) > MAX_JOURNAL_BYTES:
                            raise _ChatFailure('This response is too large. Try a narrower question or conversation.', 413)
                        # Controls, identity, lease, durable response and history
                        # share this barrier. Disconnect after commit is final.
                        if job.operation in DURABLE_OPERATIONS:
                            self.receipts.finish(job.request_id, value, lambda: job.check(force_identity=True), journal=prospective)
                        else:
                            job.check(force_identity=True)
                        job.journal_events.append(terminal)
                        job.http_status = value.status
                        job.terminal = True
                        job.completed_at = time.monotonic()
                        return
                    if event == 'delta':
                        job.pending_text += value['text']
                        if time.monotonic()-job.last_text_at >= 0.5:
                            job.flush_text()
                    else:
                        job.flush_text()
                        job.append(event, value)
        except Exception as exc:
            job.abort()
            message, status = _chat_error(exc)
            if isinstance(exc, Cancelled):
                message, status = 'The answer was interrupted before it could be saved. Please retry.', 499
            try:
                if job.operation in DURABLE_OPERATIONS:
                    self.receipts.fail(job.request_id, message, status)
            except Exception:
                message, status = 'The answer could not be saved. Please retry.', 503
            with job.lock:
                job.pending_text = ''
                job.journal_events.append({'seq': len(job.journal_events)+1, 'event': 'error', 'data': {'error': message}})
                job.http_status = status
                job.terminal = True
                job.completed_at = time.monotonic()
        finally:
            # The producer owns admission until it exits, even if cancellation
            # cannot immediately interrupt a blocking OS/provider operation.
            payload.clear()
            job.close()

    def read(self, *, request_id, renew=False):
        with self.lock:
            job = self.jobs.get(request_id)
        if job is None:
            return {'error': 'This Assistant request expired. Please retry.', 'http_status': 404}
        with job.lock:
            if renew and not job.terminal:
                try:
                    job.renew()
                except Cancelled:
                    job.abort()
            return job.snapshot()

    def cancel(self, *, request_id):
        with self.lock:
            job = self.jobs.get(request_id)
        if job:
            if not job.terminal:
                job.abort()
        return {'cancelled': bool(job)}

    def _prune(self):
        now = time.monotonic()
        self.jobs = {rid: job for rid, job in self.jobs.items()
                     if job.completed_at is None or now-job.completed_at < (TERMINAL_SECONDS if job.operation in DURABLE_OPERATIONS else 60) or
                     (job._started and not job.finished.is_set())}
        reads = sorted((job.completed_at, rid) for rid, job in self.jobs.items()
                       if job.operation not in DURABLE_OPERATIONS and job.completed_at is not None and job.finished.is_set())
        for _, rid in reads[:-64]:
            self.jobs.pop(rid, None)


_executor = None
_initialization_lock = threading.Lock()


def initialize(store, node_id='local'):
    global _executor
    with _initialization_lock:
        if _executor is None:
            _executor = Executor(store, node_id)
        elif _executor.store is not store:
            raise RuntimeError('Assistant writer identity changed')
        return _executor


def current(store=None):
    value = _executor
    if value is None or (store is not None and value.store is not store):
        raise _ChatFailure('Start the local sync service to use Assistant.', 503)
    return value
