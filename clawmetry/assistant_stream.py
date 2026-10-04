"""Bounded Assistant SSE lifecycle, cancellation and incremental redaction.

The producer never writes conversation history. Only the response consumer can
commit a completed result, immediately before sending the terminal done event.
"""
from __future__ import annotations

from contextlib import contextmanager, ExitStack
import http.client
import json
import queue
import re
import socket
import threading
import time
from urllib.parse import urlsplit
import urllib.request

from flask import Response

HEARTBEAT_SECONDS = 5.0
REQUEST_SECONDS = 180.0
QUEUE_SIZE = 32
MAX_TEXT = 131072
MAX_LINE = 262144


class Cancelled(Exception):
    """The consumer has closed the response."""


class BrokenStream(ValueError):
    """Provider transport ended without an authenticated successful completion."""


class StreamScrubber:
    """Withhold unfinished words and Bearer prefixes before applying the scrubber.

    A fixed character lookbehind is unsafe for arbitrarily long credentials.
    Pending text is bounded by the provider's total output limit instead. Word
    boundaries add a small delay, while still delivering actual provider deltas.
    """

    def __init__(self, scrub, secret=None):
        self.scrub = scrub
        self.secret = secret
        self.pending = ""
        self.size = 0
        self.emitted = 0

    def feed(self, text, *, final=False):
        if not isinstance(text, str):
            raise BrokenStream()
        self.size += len(text)
        if self.size > MAX_TEXT:
            raise BrokenStream()
        self.pending += text
        if final:
            cut = len(self.pending)
        else:
            boundaries = list(re.finditer(r"\s+", self.pending))
            cut = boundaries[-1].end() if boundaries else 0
            # Bearer may be separated from its credential by several chunks,
            # including chunks consisting entirely of spaces or newlines.
            bearer = re.search(r"(?i)\bBearer\s*$", self.pending[:cut])
            if bearer:
                cut = bearer.start()
        ready, self.pending = self.pending[:cut], self.pending[cut:]
        if self.secret:
            ready = ready.replace(self.secret, "[redacted]")
        ready = self.scrub(ready)[:max(0, 6000 - self.emitted)]
        self.emitted += len(ready)
        return ready


class StreamJob:
    """One admitted request; a slot remains owned until its producer exits."""

    def __init__(self, release):
        self.events = queue.Queue(maxsize=QUEUE_SIZE)
        self.cancelled = threading.Event()
        self.finished = threading.Event()
        self.deadline = time.monotonic() + REQUEST_SECONDS
        self._lock = threading.Lock()
        self._release = release
        self._resources = set()
        self._started = False
        self._closed = False
        self._released = False
        self._timed_out = False
        self._timer = None
        self.worker = None

    def check(self):
        if self._timed_out or time.monotonic() >= self.deadline:
            raise TimeoutError()
        if self.cancelled.is_set():
            raise Cancelled()

    def abort(self, *, timeout=False):
        with self._lock:
            self._timed_out = self._timed_out or timeout
            self.cancelled.set()
            resources = tuple(self._resources)
        for abort in resources:
            try:
                abort()
            except Exception:
                pass

    @contextmanager
    def resource(self, abort):
        with self._lock:
            self._resources.add(abort)
        try:
            self.check()
            yield
            self.check()
        finally:
            with self._lock:
                self._resources.discard(abort)

    def emit(self, event, payload):
        while True:
            self.check()
            try:
                self.events.put((event, payload), timeout=0.1)
                return
            except queue.Full:
                continue

    def status(self, message):
        self.emit("status", {"message": message})

    def _maybe_release(self):
        with self._lock:
            if self._released or not self._closed:
                return
            if self._started and not self.finished.is_set():
                return
            self._released = True
        self._release()

    def close(self):
        with self._lock:
            self._closed = True
        self.abort()
        if self._timer:
            self._timer.cancel()
        self._maybe_release()

    def start(self, work):
        def produce():
            try:
                self.check()
                self.emit("result", work(self))
            except Cancelled:
                pass
            except Exception as exc:
                # Keep errors internal. The consumer maps them to fixed copy.
                try:
                    self.emit("failure", exc)
                except (Cancelled, TimeoutError):
                    pass
            finally:
                self.finished.set()
                self._maybe_release()

        with self._lock:
            self.check()
            self._started = True
        self._timer = threading.Timer(
            max(0.001, self.deadline - time.monotonic()),
            lambda: self.abort(timeout=True),
        )
        self._timer.daemon = True
        self.worker = threading.Thread(target=produce, name="assistant-stream", daemon=True)
        try:
            self._timer.start()
            self.worker.start()
        except Exception:
            self.finished.set()
            raise


def _frame(event, payload):
    return "event: " + event + "\ndata: " + json.dumps(payload, ensure_ascii=True) + "\n\n"


def response(work, persist, release, error_message):
    job = StreamJob(release)

    def generate():
        try:
            # Yield before starting provider work, including a blocking plan.
            yield _frame("status", {"message": "Preparing your analysis."})
            job.start(work)
            heartbeat = time.monotonic() + HEARTBEAT_SECONDS
            while True:
                job.check()
                try:
                    event, payload = job.events.get(timeout=min(0.1, HEARTBEAT_SECONDS))
                except queue.Empty:
                    if job.finished.is_set() and job.events.empty():
                        raise BrokenStream()
                    if time.monotonic() >= heartbeat:
                        yield ": keepalive\n\n"
                        heartbeat = time.monotonic() + HEARTBEAT_SECONDS
                    continue
                job.check()
                if event == "failure":
                    raise payload
                if event == "result":
                    # Cancellation before this commit leaves history unchanged.
                    # A disconnect after commit cannot undo a completed turn.
                    result = persist(payload)
                    yield _frame("done", result)
                    return
                yield _frame(event, payload)
                heartbeat = time.monotonic() + HEARTBEAT_SECONDS
        except Cancelled:
            return
        except Exception as exc:
            job.abort()
            yield _frame("error", {"error": error_message(exc)[0]})
        finally:
            job.close()

    result = Response(generate(), mimetype="text/event-stream", headers={
        "Cache-Control": "no-cache, no-store, no-transform",
        "X-Accel-Buffering": "no",
    })
    # Also releases a response closed before its generator is ever entered.
    result.call_on_close(job.close)
    return result


@contextmanager
def http_response(url, *, payload, headers, control, timeout=65, method="POST"):
    """Use a retained public socket handle to interrupt a blocked HTTP read.

    Closing a buffered HTTPResponse from another thread can block on its reader
    lock. Socket shutdown wakes the producer, which then closes its own buffers.
    Connect itself is bounded separately and the request-wide timer remains live.
    """
    control.check()
    target = urlsplit(url)
    if target.scheme not in ("http", "https") or not target.hostname:
        raise ValueError("Invalid provider address")
    with ExitStack() as resources:
        def connected(sock):
            def abort():
                try:
                    sock.shutdown(socket.SHUT_RDWR)
                except OSError:
                    pass

            try:
                resources.enter_context(control.resource(abort))
                sock.settimeout(min(timeout, max(0.001, control.deadline - time.monotonic())))
            except BaseException:
                sock.close()
                raise

        def retain_tcp(connection):
            # Keep http.client's proxy CONNECT handling, but register the TCP
            # socket before CONNECT can block waiting for proxy headers.
            create = connection._create_connection

            def create_retained(*args, **kwargs):
                control.check()
                sock = create(*args, **kwargs)
                connected(sock)
                return sock

            connection._create_connection = create_retained

        class HTTPConnection(http.client.HTTPConnection):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                retain_tcp(self)

        class HTTPSConnection(http.client.HTTPSConnection):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                retain_tcp(self)

            def connect(self):
                http.client.HTTPConnection.connect(self)
                # TLS replaces (detaches) the raw socket. Retain the SSL
                # handle before its handshake so cancellation covers TLS too.
                # The original context still enforces certificates/hostnames.
                self.sock = self._context.wrap_socket(
                    self.sock, server_hostname=self._tunnel_host or self.host,
                    do_handshake_on_connect=False)
                connected(self.sock)
                self.sock.do_handshake()
                control.check()

        class HTTPHandler(urllib.request.HTTPHandler):
            def http_open(self, req):
                return self.do_open(HTTPConnection, req)

        class HTTPSHandler(urllib.request.HTTPSHandler):
            def https_open(self, req):
                return self.do_open(HTTPSConnection, req, context=self._context)

        # Keep urllib's default proxy discovery, HTTPS CONNECT support, no_proxy,
        # redirects and certificate validation, as in the existing JSON path.
        opener = urllib.request.build_opener(HTTPHandler(), HTTPSHandler())
        req = urllib.request.Request(url, data=payload, headers=headers, method=method)
        with opener.open(req, timeout=10) as result:
            control.check()
            yield result
