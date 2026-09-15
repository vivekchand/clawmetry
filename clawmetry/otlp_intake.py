"""clawmetry/otlp_intake.py -- what the OTLP receiver kept, and how it answers.

REQ-OBS-OIA-001. An OpenTelemetry exporter discards a batch the moment it sees
a success status. The receiver used to answer success to every export it could
decode, whether or not the write to the local store went through: when the
daemon that owns the store was busy, restarting or unreachable the write was
dropped with a warning and the exporter was told the batch arrived. Nothing on
either side showed the gap.

This module holds the three pieces that close it, kept out of the 20k-line
``dashboard.py`` so a reader finds them in one place:

* **The outcome of one export** (``new_result`` / ``apply_batch_outcome``):
  how many items arrived, how many are in the store, how many were refused as
  malformed, recognised as already stored, held only in the live tiles, or
  skipped because another source already reports them, and whether the store
  confirmed the write at all.
* **The answer** (``build_response``), following the OTLP/HTTP specification:
  ``200`` only when the store confirmed the write, with a ``partialSuccess``
  count when some items were refused as malformed (retrying cannot change
  those); ``503`` with ``Retry-After`` when the store could not confirm, so
  the exporter keeps the batch and sends it again. Every stored item is keyed
  by its own identity, so the retry replaces rather than adds.
* **The receiver's own counters** (``record_result`` / ``snapshot``), read by
  ``/api/otel-status``. Counts, timestamps and a failure category only: never
  a record's content, an attribute value or a credential.

There is deliberately no intake queue. The receiver acknowledges after the
store write, and the exporter's own retry buffer holds a batch the store could
not take. ``snapshot()`` says so rather than reporting a queue depth of zero
that a reader would take to mean "a queue exists and is empty".
"""
from __future__ import annotations

import json
import threading
import time
from typing import Any

from clawmetry.ingest_contract import OTLP_RETRY_AFTER_SECONDS

SIGNALS = ("logs", "traces", "metrics")

# What one item is called on each signal, in the OTLP/JSON partial-success
# field and in the sentence the sender reads.
_REJECTED_FIELD = {
    "logs": ("rejectedLogRecords", "rejected_log_records", "log records"),
    "traces": ("rejectedSpans", "rejected_spans", "spans"),
    "metrics": ("rejectedDataPoints", "rejected_data_points", "data points"),
}

ITEM_COUNTERS = (
    "received",
    "stored",
    "rejected",
    "already_stored",
    "live_view_only",
    "not_read",
    "skipped_other_source",
    "retry_requested",
)

REQUEST_COUNTERS = (
    "acknowledged",
    "partially_acknowledged",
    "retry_requested",
    "malformed",
    "protobuf_unavailable",
    "unauthorized",
    "during_budget_pause",
)

# Failure categories. A fixed vocabulary, so nothing a sender put in a body
# can reach the status endpoint through an exception message.
FAILURE_STORE_UNAVAILABLE = "store_unavailable"
FAILURE_STORE_WRITE_FAILED = "store_write_failed"
FAILURE_NO_OUTCOME = "no_outcome"
FAILURE_MALFORMED = "malformed"
FAILURE_PROTOBUF_UNAVAILABLE = "protobuf_unavailable"
FAILURE_UNAUTHORIZED = "unauthorized"


def signal_for_path(path_or_signal: str) -> str | None:
    """``/v1/logs`` -> ``logs``; a bare signal name passes through."""
    s = str(path_or_signal or "").strip().rstrip("/")
    if s in SIGNALS:
        return s
    tail = s.rsplit("/", 1)[-1]
    return tail if tail in SIGNALS else None


# ── The outcome of one export ───────────────────────────────────────────────

def new_result(signal: str) -> dict[str, Any]:
    out: dict[str, Any] = {k: 0 for k in ITEM_COUNTERS if k != "retry_requested"}
    out.update({"signal": signal, "durable": True, "failure": None})
    return out


def mark_unstored(result: dict[str, Any], failure: str) -> None:
    """The store did not confirm this export. The first cause wins: it is the
    one an operator needs, and later ones are usually its consequence."""
    result["durable"] = False
    if not result.get("failure"):
        result["failure"] = failure


def apply_batch_outcome(result: dict[str, Any], outcome: Any) -> None:
    """Fold what ``LocalStore.put_otlp_batch`` returned into ``result``.

    ``None`` is what the daemon proxy returns when the daemon could not be
    reached or refused the call, and it is indistinguishable from a write that
    never happened, so it is treated as one. A daemon on an older build
    returns the dict without the newer keys; those default to zero.
    """
    if not isinstance(outcome, dict):
        mark_unstored(result, FAILURE_STORE_UNAVAILABLE)
        return

    def _n(key: str) -> int:
        try:
            return max(0, int(outcome.get(key) or 0))
        except (TypeError, ValueError):
            return 0

    result["stored"] += _n("records")
    result["rejected"] += _n("records_rejected")
    result["already_stored"] += (
        _n("records_already_stored") + _n("records_duplicate_in_batch")
    )
    result["skipped_other_source"] += sum(
        _n(k) for k in outcome if str(k).startswith("events_skipped_")
    )
    if (_n("records_failed") or _n("events_failed")
            or bool(outcome.get("events_flush_failed"))):
        mark_unstored(result, FAILURE_STORE_WRITE_FAILED)


# ── The answer ──────────────────────────────────────────────────────────────

def _is_json(content_type: str | None) -> bool:
    ct = str(content_type or "").lower()
    return "application/json" in ct or "application/x-ndjson" in ct


def _refused_message(signal: str, n: int) -> str:
    noun = _REJECTED_FIELD.get(signal, ("", "", "items"))[2]
    return (
        f"{n} {noun} could not be stored because they are malformed "
        "(missing an id, a name or a time, or carrying a value the store "
        "cannot hold, such as a token count beyond its range). Resending "
        "them will not change that."
    )


def _protobuf_body(signal: str, rejected: int, message: str) -> bytes:
    """An ``Export<Signal>ServiceResponse``. Protobuf is only ever decoded when
    ``opentelemetry-proto`` is installed, so it is available here too; if it is
    somehow not, an empty body is still a valid empty message."""
    try:
        if signal == "logs":
            from opentelemetry.proto.collector.logs.v1 import (
                logs_service_pb2 as _m,
            )
            resp = _m.ExportLogsServiceResponse()
        elif signal == "traces":
            from opentelemetry.proto.collector.trace.v1 import (
                trace_service_pb2 as _m,
            )
            resp = _m.ExportTraceServiceResponse()
        else:
            from opentelemetry.proto.collector.metrics.v1 import (
                metrics_service_pb2 as _m,
            )
            resp = _m.ExportMetricsServiceResponse()
        if rejected:
            field = _REJECTED_FIELD[signal][1]
            try:
                setattr(resp.partial_success, field, int(rejected))
                resp.partial_success.error_message = message
            except Exception:
                pass  # an opentelemetry-proto older than partial success
        return resp.SerializeToString()
    except Exception:
        return b""


def build_response(
    signal: str, result: dict[str, Any], content_type: str | None,
) -> tuple[bytes | str, int, dict[str, str]]:
    """``(body, status, headers)`` for one export, per OTLP/HTTP."""
    if not result.get("durable", False):
        body = json.dumps({
            # google.rpc.Code UNAVAILABLE: the retryable code the OTLP
            # specification pairs with HTTP 503.
            "code": 14,
            "error": "not_stored",
            "message": (
                "The local store did not confirm the write, so nothing in "
                "this export is acknowledged. Send it again after the "
                "Retry-After delay; items that did reach the store are "
                "recognised and not counted twice."
            ),
            "retryable": True,
        })
        return body, 503, {
            "Content-Type": "application/json",
            "Retry-After": str(OTLP_RETRY_AFTER_SECONDS),
        }
    rejected = int(result.get("rejected") or 0)
    message = _refused_message(signal, rejected) if rejected else ""
    if not _is_json(content_type):
        return (
            _protobuf_body(signal, rejected, message),
            200,
            {"Content-Type": "application/x-protobuf"},
        )
    payload: dict[str, Any] = {}
    if rejected:
        # proto3 JSON renders int64 as a decimal string.
        payload["partialSuccess"] = {
            _REJECTED_FIELD[signal][0]: str(rejected),
            "errorMessage": message,
        }
    return json.dumps(payload), 200, {"Content-Type": "application/json"}


# ── The receiver's own counters ─────────────────────────────────────────────

_lock = threading.Lock()


def _fresh_state() -> dict[str, Any]:
    return {
        sig: {
            "items": {k: 0 for k in ITEM_COUNTERS},
            "requests": {k: 0 for k in REQUEST_COUNTERS},
            "last_success_at": None,
            "last_failure_at": None,
            "last_failure": None,
        }
        for sig in SIGNALS
    }


_started_at = time.time()
_state = _fresh_state()


def record_result(
    signal: str, result: dict[str, Any], *, budget_paused: bool = False,
) -> None:
    sig = signal_for_path(signal)
    if sig is None or not isinstance(result, dict):
        return
    now = time.time()
    with _lock:
        st = _state[sig]
        items, reqs = st["items"], st["requests"]
        for k in ITEM_COUNTERS:
            if k == "retry_requested":
                continue
            try:
                items[k] += max(0, int(result.get(k) or 0))
            except (TypeError, ValueError):
                pass
        if budget_paused:
            reqs["during_budget_pause"] += 1
        if result.get("durable"):
            if int(result.get("rejected") or 0):
                reqs["partially_acknowledged"] += 1
            else:
                reqs["acknowledged"] += 1
            st["last_success_at"] = now
        else:
            reqs["retry_requested"] += 1
            try:
                items["retry_requested"] += max(0, int(result.get("received") or 0))
            except (TypeError, ValueError):
                pass
            st["last_failure_at"] = now
            st["last_failure"] = str(result.get("failure") or FAILURE_NO_OUTCOME)


def record_request_failure(signal_or_path: str, category: str) -> None:
    """A request refused before any item was read: malformed body, missing
    protobuf support, or no credentials from another machine."""
    sig = signal_for_path(signal_or_path)
    if sig is None:
        return
    with _lock:
        st = _state[sig]
        if category in st["requests"]:
            st["requests"][category] += 1
        st["last_failure_at"] = time.time()
        st["last_failure"] = category


def snapshot() -> dict[str, Any]:
    with _lock:
        signals = {
            sig: {
                "items": dict(st["items"]),
                "requests": dict(st["requests"]),
                "last_success_at": st["last_success_at"],
                "last_failure_at": st["last_failure_at"],
                "last_failure": st["last_failure"],
            }
            for sig, st in _state.items()
        }
    return {
        "since": _started_at,
        "acknowledgement": "after_store_write",
        "retry_after_seconds": OTLP_RETRY_AFTER_SECONDS,
        "queue": {
            "kept": False,
            "note": (
                "The receiver keeps no intake queue. It acknowledges an "
                "export only after the local store confirms the write, and "
                "answers 503 with Retry-After when it cannot, so the "
                "exporter's own retry buffer holds the batch."
            ),
        },
        "signals": signals,
    }


def reset_for_tests() -> None:
    global _state, _started_at
    with _lock:
        _state = _fresh_state()
        _started_at = time.time()
