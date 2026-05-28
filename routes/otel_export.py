"""
routes/otel_export.py — Enterprise OTel/OTLP export.

Streams recent ClawMetry events as OTLP-JSON ``logRecords`` so a customer's
Datadog / Grafana / Honeycomb / OTel collector can poll us and pipe agent
activity into their existing observability stack. This is the first
Enterprise-only feature (entitlement gate ``otel_export``); while the
open-core rollout is in GRACE mode the gate is permissive, so the endpoint is
reachable today for evaluation.

  GET /api/otel/export[?limit=N]
    -> {"resourceLogs": [{"resource": ..., "scopeLogs": [...]}]}

The mapping is intentionally simple: one ``LogRecord`` per event, body = a
short label, attributes = session_id / event_type / role / tool_name / model.
Trace-tree export (events as Spans) is the next refinement.
"""

from __future__ import annotations

import logging

from flask import Blueprint, jsonify, request

logger = logging.getLogger("clawmetry.routes.otel_export")

bp_otel_export = Blueprint("otel_export", __name__)


def _entitlement_allows() -> tuple[bool, dict]:
    """Whether this install may use OTel export. Grace lets everyone through;
    after enforce, only Enterprise-tier installs do. Never raises."""
    try:
        from clawmetry import entitlements as _ent

        en = _ent.get_entitlement()
        return en.allows_feature("otel_export"), en.to_dict()
    except Exception as exc:  # pragma: no cover
        logger.warning("otel_export: entitlement read failed, defaulting open: %s", exc)
        return True, {"tier": "oss", "grace": True}


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
    _add("agent_type", ev.get("agent_type") or "openclaw")

    return {
        "timeUnixNano": ts_ns,
        "severityNumber": 9,           # INFO
        "severityText": "INFO",
        "body": {"stringValue": body},
        "attributes": attrs,
    }


def _build_otlp_envelope(events: list[dict]) -> dict:
    """Wrap LogRecords in the OTLP/JSON resourceLogs/scopeLogs envelope."""
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
                        "scope": {"name": "clawmetry.events", "version": "1"},
                        "logRecords": [_event_to_log_record(e) for e in events],
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


@bp_otel_export.route("/api/otel/export", methods=["GET"])
def api_otel_export():
    """OTLP/JSON export of recent events. Enterprise-gated; permissive during
    the open-core grace period. Never raises."""
    allowed, ent = _entitlement_allows()
    if not allowed:
        return jsonify({
            "error": "upgrade_required",
            "feature": "otel_export",
            "tier": ent.get("tier"),
            "hint": "OTel export is an Enterprise feature. Contact sales at https://clawmetry.com/pricing",
        }), 402

    try:
        limit = max(1, min(int(request.args.get("limit", 200) or 200), 5000))
    except Exception:
        limit = 200
    events = _fetch_events(limit)
    return jsonify(_build_otlp_envelope(events))
