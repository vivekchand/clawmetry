"""
Outbound OTLP trace exporter for ClawMetry.

Exports completed sessions as OpenTelemetry GenAI spans to a configurable
remote endpoint (Datadog / Grafana / Honeycomb / any OTLP HTTP collector).

Activation (off by default):

* env ``CLAWMETRY_OTEL_EXPORT_ENDPOINT`` — dashboard process starts the
  exporter (``start_exporter()``, the historical path), OR
* config ``otlp_endpoint`` in ~/.clawmetry/config.json — the sync daemon
  starts it (``start_exporter(scope="config")``, the enterprise path for
  headless nodes).

The two scopes are disjoint on purpose: env activates only the dashboard's
exporter, the config key activates only the daemon's, so a machine running
both processes never double-exports. Headers/interval follow the same split
(env CLAWMETRY_OTEL_EXPORT_HEADERS / CLAWMETRY_OTEL_EXPORT_INTERVAL vs
config ``otlp_headers`` / ``otlp_export_interval``).

This export is IN ADDITION to ClawMetry's own ingest protocol — it mirrors
agent activity into a customer's Datadog/Grafana/Honeycomb without replacing
the ClawMetry dashboard.

No new dependencies — uses urllib.request (stdlib) and the DuckDB proxy
that is already wired for the dashboard process.

GenAI semantic conventions: https://opentelemetry.io/docs/specs/semconv/gen-ai/
"""
from __future__ import annotations

import hashlib
import json
import os
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

_CONFIG_PATH = os.path.expanduser("~/.clawmetry/config.json")


def _config_get(key: str, default=None):
    """Best-effort read of one key from ~/.clawmetry/config.json."""
    try:
        with open(_CONFIG_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            return data.get(key, default)
    except Exception:
        pass
    return default

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

def _trace_id(session_id: str) -> str:
    """Deterministic 16-byte trace id per session, so tool spans exported in
    later flushes still land in the same trace."""
    return hashlib.sha256(("cm-trace:" + session_id).encode()).hexdigest()[:32]


def _span_id(seed: str) -> str:
    return hashlib.sha256(("cm-span:" + seed).encode()).hexdigest()[:16]


def _session_to_span(session: dict[str, Any]) -> dict | None:
    """Build one OTLP span dict from a DuckDB session row."""
    sid = session.get("session_id") or ""
    if not sid:
        return None

    system = str(session.get("agent_type") or "openclaw")
    attrs = [
        _str_attr("gen_ai.system", system),
        _str_attr("gen_ai.operation.name", "invoke_agent"),
        _str_attr("session.id", sid),
    ]
    if session.get("agent_id"):
        attrs.append(_str_attr("gen_ai.agent.name", str(session["agent_id"])))
        attrs.append(_str_attr("agent.id", str(session["agent_id"])))
    if session.get("model"):
        attrs.append(_str_attr("gen_ai.request.model", str(session["model"])))
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
        "traceId": _trace_id(sid),
        "spanId": _span_id(sid),
        "name": f"{system}.session",
        "kind": 2,  # SERVER
        "startTimeUnixNano": str(start_ns),
        "endTimeUnixNano": str(end_ns),
        "attributes": attrs,
        "status": {"code": 1},  # OK
    }


def _tool_event_to_span(event: dict[str, Any]) -> list[dict]:
    """Build child ``execute_tool`` spans from one tool-call event row.

    Uses clawmetry.detectors' shape-tolerant extractor — the same code the
    approvals watcher trusts — so all four tool-call payload shapes in the
    wild (top-level, family data.tool_calls[], v3 toolMetas[], content
    blocks) map correctly.
    """
    sid = str(event.get("session_id") or "")
    if not sid:
        return []
    data = event.get("data")
    if isinstance(data, (bytes, str)):
        try:
            data = json.loads(data)
        except Exception:
            data = {}
    if not isinstance(data, dict):
        data = {}
    try:
        from clawmetry.detectors import _iter_tool_calls_from_data
        calls = list(_iter_tool_calls_from_data(str(event.get("event_type") or ""), data))
    except Exception:
        calls = []
    if not calls:
        return []

    ts_ns = _iso_to_nano(event.get("ts")) or int(time.time() * 1_000_000_000)
    system = str(event.get("agent_type") or "openclaw")
    spans = []
    for idx, call in enumerate(calls):
        name = ""
        if isinstance(call, dict):
            name = str(
                call.get("name") or call.get("tool") or call.get("tool_name") or ""
            )
        attrs = [
            _str_attr("gen_ai.system", system),
            _str_attr("gen_ai.operation.name", "execute_tool"),
            _str_attr("session.id", sid),
        ]
        if name:
            attrs.append(_str_attr("gen_ai.tool.name", name))
        spans.append(
            {
                "traceId": _trace_id(sid),
                "spanId": _span_id(f"{event.get('id')}:{idx}"),
                "parentSpanId": _span_id(sid),
                "name": f"execute_tool {name}".strip(),
                "kind": 1,  # INTERNAL
                "startTimeUnixNano": str(ts_ns),
                "endTimeUnixNano": str(ts_ns),
                "attributes": attrs,
                "status": {"code": 1},
            }
        )
    return spans


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

    # Child execute_tool spans for tool-call events in the same window.
    events: list[dict] = []
    try:
        events = store.query_events(since=since, limit=500) or []
    except Exception:
        events = []
    for ev in events:
        try:
            spans.extend(_tool_event_to_span(ev))
        except Exception:
            continue

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

    # Advance watermark to the most-recent timestamp we just exported.
    newest = max(
        (
            *(r.get("updated_at") or r.get("started_at") or "" for r in sessions),
            *(str(e.get("ts") or "") for e in events),
        ),
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

def start_exporter(scope: str = "env") -> bool:
    """Start the OTLP export daemon thread. Returns True if started.

    ``scope`` picks the activation source (see module docstring — the split
    keeps a machine running both the dashboard and the daemon from
    double-exporting):

    * ``"env"``    — dashboard: CLAWMETRY_OTEL_EXPORT_ENDPOINT /
                     CLAWMETRY_OTEL_EXPORT_HEADERS (JSON dict) /
                     CLAWMETRY_OTEL_EXPORT_INTERVAL
    * ``"config"`` — sync daemon: ``otlp_endpoint`` / ``otlp_headers`` /
                     ``otlp_export_interval`` keys in ~/.clawmetry/config.json
    """
    if scope == "config":
        endpoint = str(_config_get("otlp_endpoint") or "").strip()
        headers = _config_get("otlp_headers") or {}
        if not isinstance(headers, dict):
            headers = {}
        raw_interval = _config_get("otlp_export_interval", _DEFAULT_INTERVAL_S)
    else:
        endpoint = os.environ.get(_EXPORT_ENDPOINT_ENV, "").strip()
        raw_headers = os.environ.get(_EXPORT_HEADERS_ENV, "").strip()
        try:
            headers = json.loads(raw_headers) if raw_headers else {}
            if not isinstance(headers, dict):
                headers = {}
        except Exception:
            headers = {}
        raw_interval = os.environ.get(_EXPORT_INTERVAL_ENV, _DEFAULT_INTERVAL_S)

    if not endpoint:
        return False

    try:
        interval_s = max(5, int(raw_interval))
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
