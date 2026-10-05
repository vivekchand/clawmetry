"""A cancellable planning phase that leaves time to explain retrieved evidence."""
from __future__ import annotations

from contextlib import contextmanager
import threading
import time


class PhaseExpired(TimeoutError):
    """The investigation budget ended; the request can still synthesize."""


class PhaseControl:
    def __init__(self, parent, deadline):
        self.parent = parent
        self.cancelled = parent.cancelled
        self.deadline = min(parent.deadline, deadline)
        self._expired = False
        self._lock = threading.Lock()
        self._resources = set()
        self._timer = threading.Timer(max(0, self.deadline - time.monotonic()),
                                      lambda: self.abort(timeout=True))
        self._timer.daemon = True

    def check(self):
        # Lease expiry, node identity and user Stop always take precedence.
        self.parent.check()
        if self._expired or time.monotonic() >= self.deadline:
            raise PhaseExpired()

    @property
    def worker(self):
        return self.parent.worker

    def abort(self, *, timeout=False):
        with self._lock:
            self._expired = True
            resources = tuple(self._resources)
        for callback in resources:
            try:
                callback()
            except Exception:
                pass

    @contextmanager
    def resource(self, callback):
        # Parent cancellation must wake the same blocking socket/child process.
        with self.parent.resource(callback):
            with self._lock:
                self._resources.add(callback)
            try:
                self.check()
                yield
            finally:
                with self._lock:
                    self._resources.discard(callback)
                self.check()

    def emit(self, event, payload):
        self.check()
        self.parent.emit(event, payload)

    def status(self, message):
        self.emit('status', {'message': message})

    def __enter__(self):
        self.check()
        self._timer.start()
        return self

    def __exit__(self, *exc):
        self._timer.cancel()
        # Translate a broken pipe caused by our timer into a phase expiry, but
        # never suppress parent cancellation or an actual provider failure.
        self.check()
