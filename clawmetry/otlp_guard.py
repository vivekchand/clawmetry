"""OTLP intake, before it is stored or judged (REQ-OBS-OTG-001).

Two gaps closed here, both specific to what arrives over OpenTelemetry:

1. **Tool spans become tool events.** The detectors behind Guard read the
   ``events`` table. A span describing a tool call used to be written only to
   ``spans``, so a trace showing an agent run a recursive delete at a home
   directory raised nothing. :func:`tool_events_from_span` normalises one tool
   span into the same ``tool_call`` / ``tool_result`` event contract the
   daemon and the OTLP log path already write, so the existing detectors,
   thresholds, incident rows and policies apply unchanged. There is no second
   detector pipeline.

2. **Received payloads are scrubbed before they rest.** Span rows are
   scrubbed in ``LocalStore.ingest_spans_batch`` (``redaction.redact_span``).
   The log-record ledger's attributes are scrubbed here, minus the identity
   keys it already keeps in typed columns (:func:`scrub_ledger_attributes`).

What this is NOT: prevention. A span is exported after the tool ran, so an
incident raised from one is an observation. :func:`observation_label` marks
such incidents so no surface says the action was stopped.

Where each piece is wired (the call sites live deep in large files):

* ``dashboard._process_otlp_traces`` calls :func:`tool_events_from_span` for
  every received span that is not a wait span, and writes the resulting
  ``tool_call`` / ``tool_result`` events in one ``LocalStore.put_otlp_batch``
  hop together with the ``waiting_on_user`` events (AC-OBS-OTG-001.1, .2).
* ``LocalStore.put_otlp_batch`` applies the daemon-ownership rule and uses
  :data:`TRACE_EVENT_ID_PREFIX` so the first OTLP signal (logs or traces) to
  report a session owns its tool stream (AC-OBS-OTG-001.3), and passes the
  log-record ledger's attributes through :func:`scrub_ledger_attributes`.
* ``LocalStore.ingest_spans_batch``, the single span write path, scrubs every
  span with ``redaction.redact_span`` and withholds a value it cannot scan
  (AC-OBS-OTG-001.4, .5).
* ``sync._emit_detector_incidents`` calls :func:`observation_label` on the
  session's events and :func:`label_incident` on each incident, then copies
  ``incident["observation"]`` (``{"source": "received_telemetry", "signals",
  "after_the_fact": True, "prevented": False}``) into the ``loop_signals``
  row's details next to ``frameworks`` (AC-OBS-OTG-001.6).

The six criteria are mirrored in ``docs/acceptance_criteria.json`` and covered
by ``tests/test_otlp_trace_guard_redaction.py``.

Normalisation rules, each one a guard against a false reading:

* Only a span that says it is a tool execution counts: a ``gen_ai.tool.name``
  or ``tool.name`` attribute, ``gen_ai.operation.name == "execute_tool"``, or
  a registered runtime profile's tool-name alias. A generic ``code.function``
  span is a function, not a tool call.
* No session, no event: every detector keys on ``session_id``. OpenClaw spans
  keep a null session by design (their sessions come from transcripts).
* Arguments the span did not carry are UNKNOWN, not empty. Hashing "no args"
  to one constant would make ten different reads look like a loop, so each
  unknown gets a distinct placeholder (the rule the log path already uses).
* Event ids are ``otlp:span:<span_id>:call`` / ``:result``. The ``otlp:``
  head keeps the daemon-ownership rule in ``put_otlp_batch`` working, and the
  ``span:`` segment lets it tell a trace-derived tool stream from a
  log-derived one, so a runtime exporting both is not counted twice.
"""
from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from typing import Any, Iterable, Optional

TRACE_EVENT_ID_PREFIX = "otlp:span:"
TOOL_EVENT_TYPES = ("tool_call", "tool_result")
TOOL_OPERATION = "execute_tool"

# How the event was captured. A received span describes something that has
# already happened; nothing in this path held it.
CAPTURE_AFTER_THE_FACT = "post_action_telemetry"

OBSERVATION_NOTE = (
    "Seen in telemetry the agent exported after the action ran. "
    "ClawMetry did not hold or block it."
)

_TOOL_NAME_KEYS = ("gen_ai.tool.name", "tool.name")
# The GenAI semconv name first, then the spellings instrumentations ship.
_ARG_KEYS = (
    "gen_ai.tool.call.arguments", "tool.call.arguments", "tool.arguments",
    "tool_parameters", "tool.parameters", "input.value",
)
_RESULT_KEYS = (
    "gen_ai.tool.call.result", "tool.call.result", "tool.result",
    "output.value",
)
_TEXT_CAP = 2000

# Attribute keys the OTLP log receiver lifts into typed identity and rollup
# columns of ``otlp_records``. They are retained as sent (AC-OBS-006.2), so
# scrubbing their copy inside the attributes blob would only make the ledger
# disagree with itself.
LEDGER_IDENTITY_KEYS = frozenset({
    "service.name", "host.name", "host.id", "node.id",
    "session.id", "session_id", "gen_ai.conversation.id", "conversation.id",
    "cursor.conversation.id",
    "user.id", "user.account_uuid", "enduser.id", "user_id",
    "user.email", "enduser.email", "user_email",
    "organization.id", "organization.uuid", "org.id", "organization_id",
    "tenant.id",
    "team.id", "team", "department", "cost_center", "cost.center", "squad",
    "group.id",
    "vcs.repository.url.full", "vcs.repository.url", "repository", "repo",
    "git.repository", "git.repo", "code.repository", "project.name",
    "workspace",
})


def _first(attrs: dict, keys: Iterable[str]) -> Any:
    for k in keys:
        v = attrs.get(k)
        if v not in (None, ""):
            return v
    return None


def _iso(seconds: float) -> str:
    return datetime.fromtimestamp(seconds, timezone.utc).isoformat()


def _parse_args(raw: Any) -> Any:
    if isinstance(raw, (bytes, bytearray)):
        raw = bytes(raw).decode("utf-8", "replace")
    if isinstance(raw, str):
        try:
            parsed = json.loads(raw)
        except (ValueError, TypeError):
            return raw
        if isinstance(parsed, (dict, list)):
            return parsed
    return raw


def tool_name_for_span(row: dict, attrs: dict, profiled: bool = False) -> Optional[str]:
    """The tool this span executed, or None when it is not a tool span."""
    name = _first(attrs, _TOOL_NAME_KEYS)
    if name is not None:
        return str(name)
    op = str(attrs.get("gen_ai.operation.name") or "").strip().lower()
    if (op == TOOL_OPERATION or profiled) and row.get("tool_name"):
        return str(row["tool_name"])
    return None


def tool_events_from_span(row: dict, attrs: dict, *, profiled: bool = False,
                          received_at: Optional[float] = None) -> list:
    """``tool_call`` + ``tool_result`` events for one tool span, else ``[]``.

    ``row`` is the span row the receiver stores (session, runtime, times,
    status already resolved); ``attrs`` the span's own attributes. Never
    raises: a malformed span yields no events rather than breaking the batch.
    """
    try:
        if not isinstance(row, dict) or not isinstance(attrs, dict):
            return []
        session_id = row.get("session_id")
        agent_type = str(row.get("agent_type") or "")
        span_id = str(row.get("span_id") or "")
        if not session_id or not span_id or not agent_type or agent_type == "openclaw":
            return []
        tool = tool_name_for_span(row, attrs, profiled)
        if not tool:
            return []

        now = float(received_at or time.time())
        try:
            start = float(row.get("start_ts") or 0.0)
        except (TypeError, ValueError):
            start = 0.0
        # A span with no time of its own is placed at receipt, the same rule
        # the log path follows (AC-OBS-006.1).
        if start <= 0:
            start = now
        try:
            end = float(row.get("end_ts") or 0.0)
        except (TypeError, ValueError):
            end = 0.0
        end = max(end, start)

        raw_args = _first(attrs, _ARG_KEYS)
        args = _parse_args(raw_args) if raw_args is not None else None
        if args in (None, ""):
            # Distinct per call. Keyed by ``span_id`` so redaction's id
            # pass-through keeps it distinct even when the id is all digits.
            args = {"_otlp_args_unknown": True, "span_id": span_id}

        common = {
            "node_id": row.get("node_id") or "otlp",
            "agent_type": agent_type,
            "agent_id": row.get("agent_id") or "main",
            "session_id": str(session_id),
            "runtime_kind": agent_type,
        }
        provenance = {
            "_otlp": True,
            "_otlp_signal": "trace",
            "trace_id": row.get("trace_id"),
            "span_id": span_id,
            "call_id": attrs.get("gen_ai.tool.call.id"),
            "capture": CAPTURE_AFTER_THE_FACT,
        }
        call = dict(common)
        call.update({
            "id": TRACE_EVENT_ID_PREFIX + span_id + ":call",
            "ts": _iso(start),
            "event_type": "tool_call",
            "data": dict(provenance, tool=tool, tool_name=tool, args=args),
        })

        status = str(row.get("status_code") or "").strip().upper()
        error_type = attrs.get("error.type")
        is_error = status in ("ERROR", "STATUS_CODE_ERROR") or error_type not in (None, "")
        error_text = ""
        if is_error:
            error_text = str(row.get("status_message") or error_type or "error")[:_TEXT_CAP]
        result = _first(attrs, _RESULT_KEYS)
        if result is not None and not isinstance(result, str):
            try:
                result = json.dumps(result, default=str)
            except Exception:
                result = str(result)
        res = dict(common)
        res.update({
            "id": TRACE_EVENT_ID_PREFIX + span_id + ":result",
            "ts": _iso(end),
            "event_type": "tool_result",
            "data": dict(
                provenance, tool=tool, tool_name=tool, is_error=is_error,
                error=error_text,
                output=(result[:_TEXT_CAP] if isinstance(result, str) else None),
                duration_ms=row.get("duration_ms"),
            ),
        })
        return [call, res]
    except Exception:
        return []


def observation_label(events: Iterable[dict]) -> Optional[dict]:
    """How a session's tool stream was observed, when ALL of it was received.

    Returns None as soon as one tool event came from anywhere else (the
    daemon's transcript read, a pre-tool hook), because then this module
    cannot say the incident was only ever seen after the fact.
    """
    signals: set = set()
    seen = 0
    for ev in events or ():
        if not isinstance(ev, dict):
            continue
        if str(ev.get("event_type") or "") not in TOOL_EVENT_TYPES:
            continue
        data = ev.get("data")
        if isinstance(data, (bytes, bytearray)):
            data = bytes(data).decode("utf-8", "replace")
        if isinstance(data, str):
            try:
                data = json.loads(data)
            except (ValueError, TypeError):
                data = {}
        if not isinstance(data, dict) or not data.get("_otlp"):
            return None
        signals.add("trace" if str(ev.get("id") or "").startswith(TRACE_EVENT_ID_PREFIX)
                    else "log")
        seen += 1
    if not seen:
        return None
    return {
        "source": "received_telemetry",
        "signals": sorted(signals),
        "after_the_fact": True,
        "prevented": False,
    }


def label_incident(incident: dict, label: dict) -> dict:
    """Stamp an incident as observed after the fact. Idempotent."""
    if not isinstance(incident, dict) or not label:
        return incident
    incident["observation"] = dict(label)
    detail = str(incident.get("detail") or "")
    if OBSERVATION_NOTE not in detail:
        incident["detail"] = (detail + " " + OBSERVATION_NOTE).strip()
    return incident


def scrub_ledger_attributes(attributes: Any) -> Any:
    """Scrub an ``otlp_records`` attributes value before it is stored.

    Shape is ``{"resource": {...}, "record": {...}, "repo_raw": ...}``. The
    identity keys the ledger keeps in typed columns pass through; every other
    value gets the span scrubber, which withholds rather than stores a value it
    could not scan. Never raises.
    """
    try:
        from clawmetry import redaction as _r
    except Exception:
        return attributes
    try:
        if not isinstance(attributes, dict):
            scrubbed, why = _r.scrub_payload(attributes)
            return _r.mark_withheld(scrubbed, why)
        reasons: set = set()
        out: dict = {}
        for key, value in attributes.items():
            if key == "repo_raw":
                out[key] = value
                continue
            if isinstance(value, dict):
                inner: dict = {}
                for ik, iv in value.items():
                    if ik in LEDGER_IDENTITY_KEYS:
                        inner[ik] = iv
                        continue
                    s, why = _r.scrub_payload(iv, ik if isinstance(ik, str) else "")
                    inner[ik] = s
                    reasons.update(why)
                out[key] = inner
            else:
                s, why = _r.scrub_payload(value, key if isinstance(key, str) else "")
                out[key] = s
                reasons.update(why)
        return _r.mark_withheld(out, sorted(reasons))
    except Exception:
        return {"clawmetry.redaction": "withheld:error"}
