"""
clawmetry.trace — Dependency-free Python tracing SDK for AI applications.

Emits OTLP/JSON spans to a local ClawMetry receiver with no external
dependencies — stdlib only (urllib.request, threading, queue, json, os, time).

Usage::

    import clawmetry.trace as ct

    ct.init(app="support-agent")

    with ct.span("plan", model="claude-opus-5") as s:
        result = llm.complete(prompt)
        s.tokens(input=1200, output=340)

    @ct.trace
    def handle(request):
        ...

    ct.tool_call("read_file", input={"path": "/tmp/x"}, output="contents...")

The SDK self-identifies via the OTLP ``service.name`` resource attribute so
the application appears in the ClawMetry runtime switcher automatically.
Background flush drops spans silently when nothing is listening — it never
raises into the host application and never blocks it.
"""
from __future__ import annotations

import functools
import json
import os
import queue
import threading
import time
import urllib.request
from contextlib import contextmanager
from typing import Any, Generator, Optional

# ─────────────────────────────────────────────────────────────────────────────
# Defaults
# ─────────────────────────────────────────────────────────────────────────────

_DEFAULT_ENDPOINT = "http://localhost:4318/v1/traces"
_QUEUE_MAXSIZE = 512        # drop oldest when full — never block the host
_FLUSH_INTERVAL_S = 2.0     # background worker cadence
_FLUSH_BATCH = 64           # max spans per HTTP POST
_HTTP_TIMEOUT_S = 2.0       # connect + read timeout per flush

# ─────────────────────────────────────────────────────────────────────────────
# Module-level state
# ─────────────────────────────────────────────────────────────────────────────

_service_name: str = "clawmetry-app"
_endpoint: str = _DEFAULT_ENDPOINT
_span_queue: "queue.Queue[dict]" = queue.Queue(maxsize=_QUEUE_MAXSIZE)
_worker: Optional[threading.Thread] = None
_worker_lock = threading.Lock()
_span_stack: threading.local = threading.local()  # per-thread span stack

# ─────────────────────────────────────────────────────────────────────────────
# Internal helpers
# ─────────────────────────────────────────────────────────────────────────────

def _now_ns() -> int:
    return int(time.time() * 1e9)


def _rand_hex(n_bytes: int) -> str:
    return os.urandom(n_bytes).hex()


def _otlp_attr(key: str, value: Any) -> dict:
    if isinstance(value, bool):
        return {"key": key, "value": {"boolValue": value}}
    if isinstance(value, int):
        return {"key": key, "value": {"intValue": value}}
    if isinstance(value, float):
        return {"key": key, "value": {"doubleValue": value}}
    return {"key": key, "value": {"stringValue": str(value)}}


def _post_batch(spans: list) -> None:
    """POST a batch of OTLP span dicts; swallow every error — nothing is listening is fine."""
    if not spans:
        return
    payload = {
        "resourceSpans": [
            {
                "resource": {
                    "attributes": [_otlp_attr("service.name", _service_name)]
                },
                "scopeSpans": [
                    {
                        "scope": {"name": "clawmetry.trace", "version": "1.0"},
                        "spans": spans,
                    }
                ],
            }
        ]
    }
    try:
        body = json.dumps(payload).encode()
        req = urllib.request.Request(
            _endpoint,
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=_HTTP_TIMEOUT_S):
            pass
    except Exception:
        pass


def _worker_loop() -> None:
    """Drain the span queue in batches; runs as a daemon thread."""
    while True:
        time.sleep(_FLUSH_INTERVAL_S)
        batch: list = []
        try:
            while len(batch) < _FLUSH_BATCH:
                batch.append(_span_queue.get_nowait())
        except queue.Empty:
            pass
        if batch:
            _post_batch(batch)


def _ensure_worker() -> None:
    global _worker
    with _worker_lock:
        if _worker is None or not _worker.is_alive():
            t = threading.Thread(target=_worker_loop, daemon=True, name="clawmetry-trace")
            t.start()
            _worker = t


def _enqueue(span_dict: dict) -> None:
    try:
        _span_queue.put_nowait(span_dict)
    except queue.Full:
        pass  # bounded queue full — drop, never block


def _current_stack() -> list:
    if not hasattr(_span_stack, "stack"):
        _span_stack.stack = []
    return _span_stack.stack

# ─────────────────────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────────────────────

def init(
    app: str,
    *,
    endpoint: str = _DEFAULT_ENDPOINT,
) -> None:
    """Configure the tracer and start the background flush thread.

    Call once near process start before recording any spans.

    Args:
        app:      Service name shown in the ClawMetry runtime switcher.
        endpoint: OTLP/JSON traces endpoint (default ``http://localhost:4318/v1/traces``).
    """
    global _service_name, _endpoint
    _service_name = app
    _endpoint = endpoint
    _ensure_worker()


class _Span:
    """A single recorded span.  Obtained via the :func:`span` context manager."""

    def __init__(
        self,
        name: str,
        *,
        model: Optional[str] = None,
        trace_id: str,
        parent_span_id: Optional[str] = None,
    ) -> None:
        self._name = name
        self._trace_id = trace_id
        self._span_id = _rand_hex(8)
        self._parent_span_id = parent_span_id
        self._start_ns = _now_ns()
        self._attrs: list = []
        if model:
            self._attrs.append(_otlp_attr("gen_ai.operation.name", "chat"))
            self._attrs.append(_otlp_attr("gen_ai.request.model", model))

    # ── Attribute helpers ─────────────────────────────────────────────────

    def tokens(
        self,
        *,
        input: Optional[int] = None,
        output: Optional[int] = None,
    ) -> "_Span":
        """Record token counts.  Returns *self* for chaining."""
        if input is not None:
            self._attrs.append(_otlp_attr("gen_ai.usage.input_tokens", input))
        if output is not None:
            self._attrs.append(_otlp_attr("gen_ai.usage.output_tokens", output))
        return self

    def set(self, key: str, value: Any) -> "_Span":
        """Attach a custom span attribute.  Returns *self* for chaining."""
        self._attrs.append(_otlp_attr(key, value))
        return self

    # ── OTLP serialisation ────────────────────────────────────────────────

    def _to_otlp(self) -> dict:
        d: dict = {
            "traceId": self._trace_id,
            "spanId": self._span_id,
            "name": self._name,
            "kind": 1,  # SPAN_KIND_INTERNAL
            "startTimeUnixNano": str(self._start_ns),
            "endTimeUnixNano": str(_now_ns()),
            "attributes": self._attrs,
            "status": {"code": 1},  # STATUS_CODE_OK
        }
        if self._parent_span_id:
            d["parentSpanId"] = self._parent_span_id
        return d

    # ── Context manager protocol ──────────────────────────────────────────

    def __enter__(self) -> "_Span":
        return self

    def __exit__(self, *_: Any) -> None:
        _enqueue(self._to_otlp())


@contextmanager
def span(
    name: str,
    *,
    model: Optional[str] = None,
) -> Generator[_Span, None, None]:
    """Context manager that records a named span.

    Spans nested inside other ``span()`` blocks are automatically linked as
    children via ``parentSpanId`` and share the same ``traceId``.

    Example::

        with ct.span("plan", model="claude-opus-5") as s:
            result = llm.complete(prompt)
            s.tokens(input=1200, output=340)
    """
    _ensure_worker()
    stack = _current_stack()
    parent_span_id = stack[-1]._span_id if stack else None
    trace_id = stack[0]._trace_id if stack else _rand_hex(16)

    sp = _Span(name, model=model, trace_id=trace_id, parent_span_id=parent_span_id)
    stack.append(sp)
    try:
        yield sp
    finally:
        stack.pop()
        _enqueue(sp._to_otlp())


def tool_call(
    name: str,
    *,
    input: Optional[dict] = None,
    output: Optional[Any] = None,
    error: Optional[str] = None,
) -> None:
    """Record a tool invocation as a fire-and-forget span (no context manager needed).

    If called inside a :func:`span` block, the tool span is automatically
    linked as a child of the enclosing span.

    Example::

        ct.tool_call("read_file", input={"path": "/tmp/x"}, output="contents...")
    """
    _ensure_worker()
    stack = _current_stack()
    parent_span_id = stack[-1]._span_id if stack else None
    trace_id = stack[0]._trace_id if stack else _rand_hex(16)

    sp = _Span(name, trace_id=trace_id, parent_span_id=parent_span_id)
    sp._attrs.append(_otlp_attr("gen_ai.operation.name", "execute_tool"))
    if input is not None:
        try:
            sp._attrs.append(_otlp_attr("gen_ai.tool.input", json.dumps(input)[:4096]))
        except Exception:
            pass
    if output is not None:
        try:
            sp._attrs.append(_otlp_attr("gen_ai.tool.output", str(output)[:4096]))
        except Exception:
            pass
    if error is not None:
        sp._attrs.append(_otlp_attr("error.message", error))
        sp._attrs.append(_otlp_attr("error", True))
    _enqueue(sp._to_otlp())


def trace(func: Any) -> Any:
    """Decorator: wraps a callable in a :func:`span` automatically.

    The span name is the function's qualified name.

    Example::

        @ct.trace
        def handle(request):
            ...
    """
    @functools.wraps(func)
    def _wrapper(*args: Any, **kwargs: Any) -> Any:
        with span(func.__qualname__):
            return func(*args, **kwargs)
    return _wrapper


__all__ = ["init", "span", "tool_call", "trace"]
