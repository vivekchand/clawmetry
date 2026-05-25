"""
Outbound OTLP trace exporter for ClawMetry.

Exports completed sessions as OpenTelemetry GenAI spans to a configurable
remote endpoint (Datadog / Grafana / Honeycomb / any OTLP HTTP collector).

Activated when CLAWMETRY_OTEL_EXPORT_ENDPOINT is set. Off by default.
No new dependencies — uses urllib.request (stdlib) and the DuckDB proxy
that is already wired for the dashboard process.

GenAI semantic conventions: https://opentelemetry.io/docs/specs/semconv/gen-ai/
"""
from __future__ import annotations

import json
import os
import secrets
import threading
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from typing import Any

_EXPORT_ENDPOINT_ENV = "CLAWMETRY_OTEL_EXPORT_ENDPOINT"
_EXPORT_HEADERS_ENV = "CLAWMETRY_OTEL_EXPORT_HEADERS"
_EXPORT_INTERVAL_ENV = "CLAWMETRY_OTEL_EXPORT_INTERVAL"
_DEFAULT_INTERVAL_S = 60

_stats: dict[str, Any] = {
    "endpoint": "",
    "last_flush_at": None,
    "spans_sent": 0,
    "last_error": None,
}
_stats_lock = threading.Lock()
# ISO-8601 watermark — only sessions updated after this are exported on each flush.
_last_watermark: str | None = None
_watermark_lock = threading.Lock()


# ── OTLP attribute helpers ──────────────────────────────────────────────────

def _str_attr(key: str, value: str) -> dict:
    return {"key": key, "value": {"stringValue": str(value)}}


def _int_attr(key: str, value: int) -> dict:
    return {"key": key, "value": {"intValue": str(int(value))}}


def _dbl_attr(key: str, value: float) -> dict:
    return {"key": key, "value": {"doubleValue": float(value)}}


# ── Timestamp helpers ───────────────────────────────────────────────────────

def _iso_to_nano(ts: str | None) -> int:
    """Convert ISO-8601 string to Unix nanoseconds; 0 on failure."""
    if not ts:
        return 0
    try:
        dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        return int(dt.timestamp() * 1_000_000_000)
    except Exception:
        return 0


# ── Span builder ───────────────────────────────────────────────────────────

def _session_to_span(session: dict[str, Any]) -> dict | None:
    """Build one OTLP span dict from a DuckDB session row."""
    sid = session.get("session_id") or ""
    if not sid:
        return None

    attrs = [
        _str_attr("gen_ai.system", "openclaw"),
        _str_attr("gen_ai.operation.name", "session"),
        _str_attr("session.id", sid),
    ]
    if session.get("agent_id"):
        attrs.append(_str_attr("agent.id", str(session["agent_id"])))
    token_count = int(session.get("token_count") or 0)
    if token_count:
        attrs.append(_int_attr("gen_ai.usage.input_tokens", token_count))
    cost = session.get("cost_usd")
    if cost:
        attrs.append(_dbl_attr("clawmetry.cost_usd", float(cost)))
    event_count = int(session.get("event_count") or 0)
    if event_count:
        attrs.append(_int_attr("clawmetry.event_count", event_count))

    start_ns = _iso_to_nano(session.get("started_at"))
    end_ns = _iso_to_nano(session.get("updated_at"))
    now_ns = int(time.time() * 1_000_000_000)
    if not start_ns:
        start_ns = end_ns or now_ns
    if not end_ns:
        end_ns = now_ns

    return {
        "traceId": secrets.token_hex(16),
        "spanId": secrets.token_hex(8),
        "name": "openclaw.session",
        "kind": 2,  # SERVER
        "startTimeUnixNano": str(start_ns),
        "endTimeUnixNano": str(end_ns),
        "attributes": attrs,
        "status": {"code": 1},  # OK
    }


def _build_payload(spans: list[dict]) -> bytes:
    """Wrap spans in an OTLP resourceSpans envelope (JSON encoding)."""
    payload = {
        "resourceSpans": [
            {
                "resource": {
                    "attributes": [
                        _str_attr("service.name", "clawmetry"),
                        _str_attr("telemetry.sdk.name", "clawmetry.otel_exporter"),
                    ]
                },
                "scopeSpans": [
                    {
                        "scope": {"name": "clawmetry.otel_exporter"},
                        "spans": spans,
                    }
                ],
            }
        ]
    }
    return json.dumps(payload).encode()


# ── Flush logic ─────────────────────────────────────────────────────────────

def _flush_once(endpoint: str, headers: dict) -> int:
    """Query DuckDB, build spans for new sessions, POST to endpoint.

    Returns number of spans sent; raises on HTTP / connection errors.
    """
    global _last_watermark

    with _watermark_lock:
        since = _last_watermark

    # Use get_store() — in the dashboard process this returns _ProxyStore which
    # forwards query_sessions() to the daemon's local_server via HTTP, so we
    # never hold a DuckDB writer lock here.
    from clawmetry.local_store import get_store
    store = get_store(read_only=True)
    sessions: list[dict] = store.query_sessions(since=since, limit=200) or []

    spans = [s for s in (_session_to_span(r) for r in sessions) if s is not None]
    if not spans:
        return 0

    body = _build_payload(spans)
    req = urllib.request.Request(
        endpoint,
        data=body,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "User-Agent": "clawmetry-otel-exporter/1.0",
            **headers,
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            resp.read()
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"OTLP HTTP {exc.code}: {exc.reason}") from exc

    # Advance watermark to the most-recent updated_at we just exported.
    newest = max(
        (r.get("updated_at") or r.get("started_at") or "" for r in sessions),
        default="",
    )
    if newest:
        with _watermark_lock:
            _last_watermark = newest

    return len(spans)


# ── Background loop ─────────────────────────────────────────────────────────

def _export_loop(endpoint: str, headers: dict, interval_s: int) -> None:
    while True:
        try:
            count = _flush_once(endpoint, headers)
            with _stats_lock:
                _stats["last_flush_at"] = datetime.now(timezone.utc).isoformat()
                _stats["spans_sent"] += count
                _stats["last_error"] = None
        except Exception as exc:
            with _stats_lock:
                _stats["last_error"] = str(exc)
        time.sleep(interval_s)


# ── Public API ──────────────────────────────────────────────────────────────

def start_exporter() -> bool:
    """Start the OTLP export daemon thread. Returns True if started.

    Reads configuration from environment variables:
      CLAWMETRY_OTEL_EXPORT_ENDPOINT  — required; OTLP HTTP/JSON traces URL
                                         e.g. http://localhost:4318/v1/traces
      CLAWMETRY_OTEL_EXPORT_HEADERS   — optional JSON dict of extra HTTP headers
                                         e.g. {"X-API-Key": "tok_xxx"}
      CLAWMETRY_OTEL_EXPORT_INTERVAL  — optional poll interval in seconds (default 60)
    """
    endpoint = os.environ.get(_EXPORT_ENDPOINT_ENV, "").strip()
    if not endpoint:
        return False

    raw_headers = os.environ.get(_EXPORT_HEADERS_ENV, "").strip()
    try:
        headers: dict = json.loads(raw_headers) if raw_headers else {}
        if not isinstance(headers, dict):
            headers = {}
    except Exception:
        headers = {}

    try:
        interval_s = max(5, int(os.environ.get(_EXPORT_INTERVAL_ENV, _DEFAULT_INTERVAL_S)))
    except (ValueError, TypeError):
        interval_s = _DEFAULT_INTERVAL_S

    with _stats_lock:
        _stats["endpoint"] = endpoint

    t = threading.Thread(
        target=_export_loop,
        args=(endpoint, headers, interval_s),
        daemon=True,
        name="otel-exporter",
    )
    t.start()
    return True


def get_stats() -> dict:
    """Return export health stats for /api/otel-status."""
    with _stats_lock:
        return dict(_stats)
