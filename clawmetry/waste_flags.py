"""clawmetry/waste_flags.py: OSS delegating shim after the impl moved to clawmetry-pro.

The real per-run waste heuristics (runaway loops, cold cache, bloated
context, repeated-error chains) ship in the closed-source ``clawmetry-pro``
package as ``clawmetry_pro/lib/waste_flags.py``. Per-run waste flags
are a Pro feature (entitlement key ``per_run_waste_flags``).

When clawmetry-pro is installed, this shim delegates to the real
implementation so OSS callers (``routes/sessions.py``, ``routes/overview.py``,
``clawmetry/sync.py``) keep computing flags unchanged.

When clawmetry-pro is NOT installed, every flag computation returns an
empty list / safe default. OSS-only users do not see waste flags in their
dashboard; the Free tier degrades gracefully. The one exception is
``event_is_real_error``: its OSS default is a real structured check (see the
function) because an error counter that is always zero is not a safe default,
it is a wrong one.
"""
from __future__ import annotations

import logging
from typing import Any, Iterable

logger = logging.getLogger("clawmetry.waste_flags")


def _pro():
    """Return ``clawmetry_pro.lib.waste_flags`` when importable, else ``None``."""
    try:
        from clawmetry_pro.lib import waste_flags as _w
        return _w
    except Exception:
        return None


# ── public surface ─────────────────────────────────────────────────────────────


def compute_flags(signals: Any) -> list[dict]:
    """Compute per-run waste flags. Returns ``[]`` when clawmetry-pro is
    not installed (Free tier sees no waste-flag overlay)."""
    pro = _pro()
    if pro is None:
        return []
    try:
        return pro.compute_flags(signals)
    except Exception as exc:
        logger.warning("waste_flags.compute_flags delegation failed: %s", exc)
        return []


def compute_signals_from_events(events: Iterable[dict]) -> dict:
    """Reduce events into the signal dict ``compute_flags`` consumes.
    Returns ``{}`` when clawmetry-pro is not installed."""
    pro = _pro()
    if pro is None:
        return {}
    try:
        return pro.compute_signals_from_events(events)
    except Exception as exc:
        logger.warning("waste_flags.compute_signals delegation failed: %s", exc)
        return {}


def runtime_from_session_id(session_id: Any) -> str:
    """Map a session id prefix to a runtime label. OSS Free always
    returns ``"openclaw"`` (the only Free runtime); when clawmetry-pro
    is installed the real lookup runs."""
    pro = _pro()
    if pro is not None:
        try:
            return pro.runtime_from_session_id(session_id)
        except Exception:
            pass
    # Free-default: assume OpenClaw (the only Free runtime).
    return "openclaw"


def severity_from_counts(error_count: Any, flag_count: Any) -> str:
    """Map error + flag counts to a severity label. Free-default is
    ``"info"`` (no flagging happens on OSS-only)."""
    pro = _pro()
    if pro is not None:
        try:
            return pro.severity_from_counts(error_count, flag_count)
        except Exception:
            pass
    return "info"


# Event types that are an error by declaration, not by inference. Text
# heuristics ("looks like a traceback", "was it corrected later") stay in Pro;
# this list is the structured floor every install gets.
_ERROR_EVENT_TYPES = frozenset({
    "error", "tool.error", "tool_error", "api.error", "api_error",
    "model.error", "model_error", "llm.error", "llm_error", "agent.error",
    "agent_error", "session.error", "request.error", "request_failed",
    "exception", "guardrail.blocked", "budget_blocked",
})
_STATUS_KEYS = ("status", "status_code", "statusCode", "http_status")


def _free_event_is_real_error(event: Any) -> bool:
    """Structured-only error check (the OSS default).

    True when the event says so in a field a machine set: a tool result's
    ``is_error``/``isError`` flag, a non-empty ``error`` object, a non-zero
    exit code, an HTTP 4xx/5xx status, or an explicit error event type.
    Never reads free text, so a reply that merely mentions the word "error"
    is not one. Never raises."""
    try:
        if not isinstance(event, dict):
            return False
        et = str(event.get("event_type") or event.get("type") or "").strip().lower()
        if et in _ERROR_EVENT_TYPES or et.endswith(".error") or et.endswith("_error"):
            return True
        data = event.get("data")
        if isinstance(data, (bytes, bytearray)):
            try:
                import json as _json
                data = _json.loads(bytes(data).decode("utf-8", "replace"))
            except Exception:
                data = None
        if isinstance(data, str):
            try:
                import json as _json
                data = _json.loads(data)
            except Exception:
                data = None
        if not isinstance(data, dict):
            return False
        holders = [data]
        msg = data.get("message")
        if isinstance(msg, dict):
            holders.append(msg)
        for h in holders:
            for k in ("is_error", "isError"):
                if k in h:
                    return bool(h.get(k))
        err = data.get("error")
        if isinstance(err, dict):
            return bool(err)
        if isinstance(err, str) and err.strip():
            return True
        if err is True:
            return True
        for k in ("exit_code", "exitCode", "returncode", "exit_status"):
            if k in data:
                try:
                    return int(data.get(k)) != 0
                except (TypeError, ValueError):
                    continue
        for h in holders:
            for k in _STATUS_KEYS:
                v = h.get(k)
                if isinstance(v, bool):
                    continue
                try:
                    n = int(v)
                except (TypeError, ValueError):
                    continue
                if 400 <= n <= 599:
                    return True
        return False
    except Exception:
        return False


def event_is_real_error(event: Any) -> bool:
    """True when an event is a real error (not benign / not corrected).

    With clawmetry-pro installed the richer filter runs (text heuristics,
    corrected-later suppression). Without it the OSS default is a REAL
    structured check (``is_error`` flags, HTTP 4xx/5xx, non-zero exit codes,
    explicit error event types) rather than the old constant ``False`` that
    made every OSS error counter read zero."""
    pro = _pro()
    if pro is not None:
        try:
            return pro.event_is_real_error(event)
        except Exception:
            pass
    return _free_event_is_real_error(event)
