"""How much content received telemetry keeps (REQ-OBS-OTG-001, AC-OBS-OTG-001.9).

``CLAWMETRY_OTLP_CONTENT`` chooses one of three profiles for what the OTLP
receivers store: span rows, the tool and typed events derived from spans and
log records, and the log-record ledger's attributes.

* ``redacted`` (the default, and the answer for any unrecognised value):
  today's behaviour. Content is kept; the secret tier and the personal-data
  tier each apply per their own switches.
* ``full``: content is kept and the personal-data tier is NOT applied to
  received telemetry. Secrets are still masked, because secret masking follows
  only ``CLAWMETRY_REDACT``; no content profile relaxes it.
* ``metadata``: prompts, responses, tool arguments and results, status
  messages and every attribute outside :data:`METADATA_ATTR_KEYS` are replaced
  by :data:`WITHHELD` before storage. The row says so: a span's attributes
  carry ``clawmetry.content`` and ``clawmetry.content.withheld`` (the withheld
  keys), an event's data carries ``content_withheld``. Tool arguments become a
  per-call unknown placeholder, so trajectory detectors still count calls, but
  behavioural detectors cannot read arguments that were never stored.

Two switches stay separate from this profile on purpose: secret masking
(``CLAWMETRY_REDACT``) and personal-data filtering (``CLAWMETRY_REDACT_PII`` and
the per-category config in ``clawmetry/redaction.py``).

Where it is applied: ``dashboard._otel_to_row`` calls :func:`minimise_span_row`
on every received span (and strips any ``clawmetry.content`` or
``clawmetry.redaction`` attribute an exporter sent, so a sender cannot claim a
profile); ``clawmetry/otlp_sources.py`` calls :func:`minimise_event` on every
OTLP event before it is stored; ``clawmetry/otlp_guard.py`` applies
:func:`minimise_ledger_value` to the ledger. :func:`posture_check` is the line
the security posture shows.
"""
from __future__ import annotations

import os
from typing import Any

PROFILE_ENV = "CLAWMETRY_OTLP_CONTENT"
PROFILES = ("full", "redacted", "metadata")
DEFAULT_PROFILE = "redacted"

MARKER_KEY = "clawmetry.content"
WITHHELD_KEYS_KEY = "clawmetry.content.withheld"
# Attributes an exporter may not set on our behalf.
RESERVED_ATTR_KEYS = frozenset({MARKER_KEY, WITHHELD_KEYS_KEY, "clawmetry.redaction"})
WITHHELD = "[WITHHELD:content-profile]"
_WITHHELD_KEYS_CAP = 64

# What the personal-data tier does not detect, stated wherever the profile is.
PII_NOT_DETECTED = ("names", "street addresses", "dates of birth", "record numbers")

# Metadata an operator can keep under ``metadata``: identity, model, counts,
# timing, operation and tool names, status. Nothing here is free text a user
# or an agent wrote.
METADATA_ATTR_KEYS = frozenset({
    "gen_ai.operation.name", "gen_ai.system", "gen_ai.provider.name",
    "gen_ai.request.model", "gen_ai.response.model", "gen_ai.response.id",
    "gen_ai.response.finish_reasons", "gen_ai.request.max_tokens",
    "gen_ai.request.temperature", "gen_ai.request.top_p",
    "gen_ai.tool.name", "gen_ai.tool.call.id", "gen_ai.tool.type",
    "gen_ai.conversation.id", "gen_ai.agent.id", "gen_ai.agent.name",
    "gen_ai.usage.cost_usd",
    "session.id", "session_id", "agent.type", "agent.id", "agent_type",
    "openclaw.session_id", "openclaw.agent_id", "openclaw.agent_type",
    "tool.name", "tool_name", "tool.call.id", "tool_call_id", "call_id",
    "tool_use_id", "tool.source", "tool_source", "decision", "tool.decision",
    "success", "tool.success", "source",
    "llm.model", "model", "cost_usd", "cost.usd", "cost", "llm.usage.cost",
    "input_tokens", "output_tokens", "total_tokens", "prompt_tokens",
    "completion_tokens", "tokens.input", "tokens.output",
    "duration_ms", "duration.ms",
    "error.type", "exception.type", "otel.status_code",
    "http.request.method", "http.response.status_code", "server.port",
    "service.name", "service.version", "service.namespace",
    "deployment.environment", "deployment.environment.name",
    "host.name", "host.id", "node.id", "telemetry.sdk.name",
    "telemetry.sdk.language", "telemetry.sdk.version",
    "event.name", "code.function",
})
METADATA_ATTR_PREFIXES = ("gen_ai.usage.", "llm.usage.")

# Event ``data`` keys that are metadata (the receivers write these names).
METADATA_DATA_KEYS = frozenset({
    "tool", "tool_name", "is_error", "duration_ms", "decision", "source",
    "tool_source", "model", "provider", "input_tokens", "output_tokens",
    "cache_read_tokens", "cache_creation_tokens", "cost_usd", "_otlp",
    "_otlp_signal", "_otlp_args_unknown", "trace_id", "span_id", "call_id",
    "capture", "success",
})


def configured() -> dict:
    """``{"profile", "raw", "recognised"}`` from the environment, read now."""
    raw = os.environ.get(PROFILE_ENV)
    value = (raw or "").strip().lower()
    if not value:
        return {"profile": DEFAULT_PROFILE, "raw": raw, "recognised": True}
    if value in PROFILES:
        return {"profile": value, "raw": raw, "recognised": True}
    return {"profile": DEFAULT_PROFILE, "raw": raw, "recognised": False}


def profile() -> str:
    return configured()["profile"]


def _metadata_attr(key: Any) -> bool:
    if not isinstance(key, str):
        return False
    return key in METADATA_ATTR_KEYS or key.startswith(METADATA_ATTR_PREFIXES)


def _minimise_attrs(attrs: Any, withheld: set) -> Any:
    if not isinstance(attrs, dict):
        return attrs
    out: dict = {}
    for key, value in attrs.items():
        if key in RESERVED_ATTR_KEYS:
            continue
        if _metadata_attr(key) or value in (None, ""):
            out[key] = value
        else:
            out[key] = WITHHELD
            withheld.add(str(key))
    return out


def _strip_reserved(attrs: Any) -> Any:
    if not isinstance(attrs, dict):
        return attrs
    return {k: v for k, v in attrs.items() if k not in RESERVED_ATTR_KEYS}


def minimise_span_row(row: dict) -> dict:
    """Apply the profile to one received span row. Never raises."""
    try:
        if not isinstance(row, dict):
            return row
        out = dict(row)
        attrs = _strip_reserved(out.get("attributes"))
        prof = profile()
        if prof == "redacted":
            out["attributes"] = attrs
            return out
        if prof == "full":
            attrs = dict(attrs) if isinstance(attrs, dict) else {}
            attrs[MARKER_KEY] = "full"
            out["attributes"] = attrs
            return out
        withheld: set = set()
        for col in ("input", "output"):
            if out.get(col) not in (None, ""):
                out[col] = WITHHELD
                withheld.add(col)
        if out.get("status_message"):
            out["status_message"] = WITHHELD
            withheld.add("status_message")
        attrs = _minimise_attrs(attrs if isinstance(attrs, dict) else {}, withheld)
        events = []
        for ev in out.get("events") or []:
            if isinstance(ev, dict):
                ev = dict(ev)
                ev["attributes"] = _minimise_attrs(ev.get("attributes") or {}, withheld)
            events.append(ev)
        out["events"] = events
        links = []
        for ln in out.get("links") or []:
            if isinstance(ln, dict):
                ln = dict(ln)
                ln["attributes"] = _minimise_attrs(ln.get("attributes") or {}, withheld)
            links.append(ln)
        out["links"] = links
        attrs[MARKER_KEY] = "metadata"
        if withheld:
            attrs[WITHHELD_KEYS_KEY] = sorted(withheld)[:_WITHHELD_KEYS_CAP]
        out["attributes"] = attrs
        return out
    except Exception:
        # Could not apply the profile: withhold the content columns rather
        # than store content the operator asked not to keep.
        if profile() == "metadata" and isinstance(row, dict):
            safe = dict(row)
            for col in ("input", "output", "status_message", "attributes", "events", "links"):
                safe[col] = None
            safe["attributes"] = {MARKER_KEY: "metadata", "clawmetry.redaction": "withheld:error"}
            return safe
        return row


def minimise_event(ev: dict) -> dict:
    """Apply the profile to one OTLP event (``data._otlp``). Never raises."""
    try:
        if profile() != "metadata" or not isinstance(ev, dict):
            return ev
        data = ev.get("data")
        if not isinstance(data, dict) or not data.get("_otlp"):
            return ev
        out = dict(ev)
        slim: dict = {}
        for key, value in data.items():
            if key in METADATA_DATA_KEYS:
                slim[key] = value
            elif key == "args":
                # Distinct per call, so unknown arguments never read as a loop.
                slim["args"] = {"_otlp_args_unknown": True, "event_id": str(ev.get("id") or "")}
            elif value not in (None, ""):
                slim[key] = WITHHELD
        slim["content_withheld"] = "metadata"
        out["data"] = slim
        return out
    except Exception:
        return ev


def minimise_ledger_value(key: Any, value: Any) -> Any:
    """One non-identity ledger attribute under ``metadata``; else unchanged."""
    if profile() != "metadata":
        return value
    if _metadata_attr(key) or value in (None, ""):
        return value
    return WITHHELD


def personal_data_applies_to_span(span: Any) -> bool:
    """False only for a received span stored under ``full``.

    Both the stamp the receiver wrote and the current profile must say
    ``full``: the stamp alone could have been written by anything that calls
    the store directly.
    """
    try:
        attrs = span.get("attributes") if isinstance(span, dict) else None
        stamped = isinstance(attrs, dict) and attrs.get(MARKER_KEY) == "full"
        return not (stamped and profile() == "full")
    except Exception:
        return True


def personal_data_applies_to_event(event: Any) -> bool:
    """False only for an OTLP event while the profile is ``full``."""
    try:
        data = event.get("data") if isinstance(event, dict) else None
        return not (isinstance(data, dict) and data.get("_otlp") and profile() == "full")
    except Exception:
        return True


def posture_check() -> dict:
    """The security posture line for received telemetry. No em dashes: users read it."""
    cfg = configured()
    prof = cfg["profile"]
    gaps = ("Personal data not detected in any profile: " + ", ".join(PII_NOT_DETECTED) + ".")
    base = {"id": "otlp_content", "label": "Received telemetry content",
            "severity": "medium", "weight": 0, "profile": prof}
    if not cfg["recognised"]:
        return dict(base, status="warn",
                    detail="CLAWMETRY_OTLP_CONTENT is set to a value ClawMetry does not "
                           "recognise, so the default applies: content is kept, secrets "
                           "and personal data are masked. " + gaps,
                    remediation="Set CLAWMETRY_OTLP_CONTENT to full, redacted or metadata.")
    if prof == "full":
        return dict(base, status="warn",
                    detail="Full: prompts, responses and tool arguments from received "
                           "telemetry are stored with personal data as sent. Secrets are "
                           "still masked. " + gaps,
                    remediation="Unset CLAWMETRY_OTLP_CONTENT, or set it to redacted or metadata.")
    if prof == "metadata":
        return dict(base, status="pass",
                    detail="Metadata only: no prompt, response, tool argument or free text "
                           "from received telemetry is stored, and each withheld field is "
                           "labelled. Guard cannot read arguments that were not stored.",
                    remediation=None)
    return dict(base, status="pass",
                detail="Redacted: content from received telemetry is kept with secrets and "
                       "personal data masked before storage. " + gaps,
                remediation=None)
