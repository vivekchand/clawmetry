"""
routes/otel_export.py — Pro+ OTel/OTLP export.

Streams recent ClawMetry events as OTLP-JSON ``logRecords`` so a customer's
Datadog / Grafana / Honeycomb / OTel collector can poll us and pipe agent
activity into their existing observability stack. Pro-tier feature on
clawmetry.com/pricing (entitlement gate ``otel_export``, moved from
Enterprise to Pro in the 2026-05-29 catalogue rewrite to match the published
pricing). While the open-core rollout is in GRACE mode the gate is
permissive, so the endpoint is reachable today for evaluation.

  GET /api/otel/export[?limit=N]                    — one record per EVENT
    -> {"resourceLogs": [{"resource": ..., "scopeLogs": [...]}]}
  GET /api/otel/export?shape=sessions[&window=7d&runtime=claude_code]
    -> the same envelope, one record per SESSION, carrying the evaluation
       facts: outcome, outcome confidence, cost, tokens, duration, runtime.

Two shapes because they answer different questions. The event shape says
what happened; the session shape says how it went and what it cost, which
is what an eval stack scores on. Exporting that is deliberately worth more
to a buyer already running Braintrust / Langfuse / Arize than a competing
evaluation view inside ClawMetry would be — we do not out-build the eval
vendors, we hand them better-labelled data.

Trace-tree export (events as Spans) is the next refinement.

Gating: the route uses the shared :func:`clawmetry._gate.gate` decorator
so the 402 body carries the same ``feature`` / ``tier`` / ``required_tier``
envelope every other paid-feature route returns. Callers who used to read
``feature`` and ``required_tier`` off other 402 responses now get the same
shape here.
"""

from __future__ import annotations

import logging

from flask import Blueprint, jsonify, request

from clawmetry._gate import gate

logger = logging.getLogger("clawmetry.routes.otel_export")

bp_otel_export = Blueprint("otel_export", __name__)

# Windows the session shape accepts. Mirrors ``_OUTCOME_WINDOW_TO_SECS``
# in routes/sessions.py so "7d" means the same thing on both surfaces.
_WINDOW_SECS = {"1h": 3600, "1d": 86400, "24h": 86400,
                "7d": 7 * 86400, "30d": 30 * 86400}


def _event_to_log_record(ev: dict) -> dict:
    """Map a ClawMetry event row to an OTLP LogRecord (JSON)."""
    ts = ev.get("ts") or ev.get("timestamp") or 0
    try:
        ts_ns = str(int(float(ts) * 1_000_000_000))
    except Exception:
        ts_ns = "0"
    event_type = str(ev.get("event_type") or ev.get("type") or "event")
    body = event_type
    role = ev.get("role") or ev.get("data", {}).get("role") if isinstance(ev.get("data"), dict) else ev.get("role")

    attrs: list[dict] = []
    def _add(k: str, v):
        if v is None or v == "":
            return
        if isinstance(v, bool):
            attrs.append({"key": k, "value": {"boolValue": v}})
        elif isinstance(v, (int,)):
            attrs.append({"key": k, "value": {"intValue": str(v)}})
        elif isinstance(v, float):
            attrs.append({"key": k, "value": {"doubleValue": v}})
        else:
            attrs.append({"key": k, "value": {"stringValue": str(v)[:512]}})

    _add("session_id", ev.get("session_id"))
    _add("event_type", event_type)
    _add("role", role)
    _add("tool_name", ev.get("tool_name") or ev.get("toolName"))
    _add("model", ev.get("model"))
    _add("agent_type", _runtime_of(ev.get("agent_type"), ev.get("session_id")))
    _add("runtime", _runtime_of(ev.get("agent_type"), ev.get("session_id")))

    return {
        "timeUnixNano": ts_ns,
        "severityNumber": 9,           # INFO
        "severityText": "INFO",
        "body": {"stringValue": body},
        "attributes": attrs,
    }


def _runtime_of(agent_type, session_id) -> str:
    """The runtime a row belongs to, session-id prefix first.

    ``sessions.agent_type`` is a legacy column ``upsert_sessions`` hardcodes
    to ``"openclaw"`` for every row, so trusting it labelled every Claude
    Code / Codex / Cursor record as OpenClaw in the exported stream — the
    same prefix-parse bug the hosted Activity feed had. The session-id
    prefix (``claude_code:abc`` -> ``claude_code``) is the canonical answer,
    and matches the frontend's ``_cmRuntimeOf``.
    """
    sid = str(session_id or "")
    if ":" in sid:
        prefix = sid.split(":", 1)[0].strip()
        if prefix:
            return prefix
    at = str(agent_type or "").strip()
    return at or "openclaw"


# Terminal outcomes an eval stack should be able to alert on, mapped to OTel
# severity so a Datadog / Grafana / Honeycomb monitor works without the
# operator writing an attribute filter first.
_OUTCOME_SEVERITY: dict[str, tuple[int, str]] = {
    "success": (9, "INFO"),
    "escalated": (13, "WARN"),
    "failed": (17, "ERROR"),
    "cognitive_loop": (17, "ERROR"),
    "tool_call_stuck": (17, "ERROR"),
    "ongoing": (5, "DEBUG"),
}


def _duration_sec(row: dict):
    """Wall-clock seconds between started_at and the last activity, or None."""
    from datetime import datetime

    def _parse(v):
        t = str(v or "").strip().replace("Z", "+00:00")
        if not t:
            return None
        try:
            return datetime.fromisoformat(t)
        except ValueError:
            return None

    start = _parse(row.get("started_at"))
    end = _parse(row.get("ended_at") or row.get("last_active_at"))
    if start is None or end is None:
        return None
    delta = (end - start).total_seconds()
    return round(delta, 3) if delta >= 0 else None


def _session_to_log_record(row: dict) -> dict:
    """Map one session row to an OTLP LogRecord carrying the EVALUATION facts.

    The event-shaped export answers "what happened"; an eval stack needs
    "how did it go and what did it cost". These are the fields Braintrust /
    Langfuse / Arize actually score on, so exporting them is worth more to a
    buyer who already runs one of those than a competing view inside
    ClawMetry would be.
    """
    ts = row.get("last_active_at") or row.get("ended_at") or row.get("started_at")
    ts_ns = "0"
    if ts:
        from datetime import datetime

        try:
            t = str(ts).strip().replace("Z", "+00:00")
            ts_ns = str(int(datetime.fromisoformat(t).timestamp() * 1_000_000_000))
        except (ValueError, OverflowError, OSError):
            ts_ns = "0"

    outcome = str(row.get("outcome") or "") or "unknown"
    sev_num, sev_text = _OUTCOME_SEVERITY.get(outcome, (9, "INFO"))

    attrs: list[dict] = []

    def _add(k: str, v):
        if v is None or v == "":
            return
        if isinstance(v, bool):
            attrs.append({"key": k, "value": {"boolValue": v}})
        elif isinstance(v, int):
            attrs.append({"key": k, "value": {"intValue": str(v)}})
        elif isinstance(v, float):
            attrs.append({"key": k, "value": {"doubleValue": v}})
        else:
            attrs.append({"key": k, "value": {"stringValue": str(v)[:512]}})

    runtime = _runtime_of(row.get("agent_type"), row.get("session_id"))
    _add("session_id", row.get("session_id"))
    _add("runtime", runtime)
    _add("agent_type", runtime)
    _add("session_title", row.get("title"))
    _add("outcome", outcome)
    _add("status", row.get("status"))
    conf = row.get("outcome_confidence")
    if conf is not None:
        try:
            _add("outcome_confidence", float(conf))
        except (TypeError, ValueError):
            pass
    cost = row.get("cost_usd")
    if cost is not None:
        try:
            _add("cost_usd", float(cost))
        except (TypeError, ValueError):
            pass
    tokens = row.get("total_tokens")
    if tokens is not None:
        try:
            _add("total_tokens", int(tokens))
        except (TypeError, ValueError):
            pass
    dur = _duration_sec(row)
    if dur is not None:
        _add("duration_sec", dur)
    _add("started_at", row.get("started_at"))
    _add("ended_at", row.get("ended_at") or row.get("last_active_at"))

    return {
        "timeUnixNano": ts_ns,
        "severityNumber": sev_num,
        "severityText": sev_text,
        "body": {"stringValue": "session." + outcome},
        "attributes": attrs,
    }


def _build_otlp_envelope(
    events: list[dict],
    *,
    scope: str = "clawmetry.events",
    records: list[dict] | None = None,
) -> dict:
    """Wrap LogRecords in the OTLP/JSON resourceLogs/scopeLogs envelope.

    ``events`` keeps the original positional contract (event rows, mapped
    here). ``records`` lets a caller pass already-built LogRecords — the
    session shape below builds its own — and ``scope`` names which stream
    the receiver is looking at, so a collector can route sessions and events
    to different destinations.
    """
    log_records = (
        records
        if records is not None
        else [_event_to_log_record(e) for e in events]
    )
    return {
        "resourceLogs": [
            {
                "resource": {
                    "attributes": [
                        {"key": "service.name", "value": {"stringValue": "clawmetry"}},
                        {"key": "telemetry.sdk.name", "value": {"stringValue": "clawmetry-otel-export"}},
                    ]
                },
                "scopeLogs": [
                    {
                        "scope": {"name": scope, "version": "1"},
                        "logRecords": log_records,
                    }
                ],
            }
        ]
    }


def _fetch_events(limit: int) -> list[dict]:
    """Pull recent events via the daemon-proxy local-query path. Falls back to
    an empty list on any failure (cloud / no-daemon environments)."""
    try:
        from routes.local_query import _dispatch

        body = _dispatch("events", {"limit": limit})
        evs = body.get("events") if isinstance(body, dict) else None
        return evs if isinstance(evs, list) else []
    except Exception as exc:
        logger.warning("otel_export: event fetch failed: %s", exc)
        return []


def _fetch_sessions(limit: int, window: str, runtime: str | None) -> list[dict]:
    """Recent session rows with their outcome label, via the daemon proxy.

    ``query_outcomes`` is the read that carries the outcome enum alongside
    cost and tokens, and it inline-classifies rows the classifier has not
    reached yet — so a fresh install exports labelled sessions rather than
    a column of nulls. Falls back to an empty list on any failure (cloud /
    no-daemon environments), same as :func:`_fetch_events`.
    """
    since = None
    secs = _WINDOW_SECS.get((window or "").lower())
    if secs:
        from datetime import datetime, timedelta, timezone

        since = (
            datetime.now(timezone.utc) - timedelta(seconds=secs)
        ).isoformat().replace("+00:00", "Z")
    kwargs = {
        "agent_type": "openclaw",
        "since": since,
        "runtime": runtime,
        "limit": limit,
    }
    # Daemon proxy first: on a normal install the daemon holds the DuckDB
    # writer lock, so a direct open here raises. ``query_outcomes`` is on the
    # proxy allowlist in routes/local_query.py.
    try:
        from routes.local_query import local_store_via_daemon

        rows = local_store_via_daemon("query_outcomes", **kwargs)
        if isinstance(rows, list):
            return rows
    except Exception as exc:
        logger.debug("otel_export: daemon proxy miss: %s", exc)
    # Single-process boots (tests, dev mode) have no daemon to proxy through.
    try:
        from clawmetry import local_store

        rows = local_store.get_store(read_only=True).query_outcomes(**kwargs)
        return rows if isinstance(rows, list) else []
    except Exception as exc:
        logger.warning("otel_export: session fetch failed: %s", exc)
        return []


@bp_otel_export.route("/api/otel/export", methods=["GET"])
@gate("otel_export")
def api_otel_export():
    """OTLP/JSON export of recent events. Pro+ entitlement-gated via the
    shared :func:`clawmetry._gate.gate` decorator; permissive during the
    open-core grace period. Never raises."""
    try:
        limit = max(1, min(int(request.args.get("limit", 200) or 200), 5000))
    except Exception:
        limit = 200
    shape = (request.args.get("shape") or "events").strip().lower()
    if shape in ("sessions", "session"):
        window = (request.args.get("window") or "7d").strip().lower()
        runtime = (request.args.get("runtime") or "").strip() or None
        rows = _fetch_sessions(limit, window, runtime)
        return jsonify(
            _build_otlp_envelope(
                [],
                scope="clawmetry.sessions",
                records=[_session_to_log_record(r) for r in rows],
            )
        )
    events = _fetch_events(limit)
    return jsonify(_build_otlp_envelope(events))


# /api/otel/push/status and /api/otel/push/flush moved to the closed
# source clawmetry-pro package (clawmetry_pro/routes/otel_push.py) as
# part of the open-core split. The OSS dashboard registers the Pro
# blueprint when clawmetry-pro is installed and falls back to the OSS
# blueprint stubs otherwise; this file keeps only the always-free pull
# endpoint above.
