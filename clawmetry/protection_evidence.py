"""Protection evidence for Guard, with no inference from agent self-reports.

The builder is pure. Request handlers read only stored observations. The
explicit capture helper is called by the daemon, outside the event writer lock.
Configuration and approval records never prove arbitrary execution isolation.
"""
from __future__ import annotations

import json
import logging
import math
import time
from datetime import datetime, timezone

log = logging.getLogger("clawmetry.protection_evidence")
HOOK_SETTING = "guard.protection.hooks"
FRESH_MS = 180_000
SECURITY_STATUS_SETTING = "guard.security.status"


def _number(value):
    try:
        number = float(value)
        return number if math.isfinite(number) and number > 0 else None
    except (TypeError, ValueError, OverflowError):
        return None


def _time_ms(value):
    if isinstance(value, bool):
        return None
    number = _number(value)
    if number:
        return int(number if number >= 100_000_000_000 else number * 1000)
    if not isinstance(value, str):
        return None
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return int(dt.timestamp() * 1000)
    except (ValueError, OverflowError, OSError):
        return None


def _recent(stamp, now_ms):
    return stamp is not None and 0 <= now_ms - stamp <= FRESH_MS


def _strings(values, limit=12):
    return [v[:80] for v in values[:limit] if isinstance(v, str)] \
        if isinstance(values, list) else []


def _configuration(runtime, hooks, now_ms):
    result = {"state": "unknown", "source": "runtime_hook_configuration",
              "checked_at": None, "events": [], "matchers": [], "supported": None}
    if not isinstance(hooks, dict):
        return result
    checked = _number(hooks.get("checked_at"))
    checked = int(checked) if checked else None
    runtimes = hooks.get("runtimes")
    item = runtimes.get(runtime) if isinstance(runtimes, dict) else None
    if not isinstance(item, dict) or checked is None or checked > now_ms:
        return result
    result["checked_at"] = checked
    result["supported"] = item.get("supported") is True
    state = item.get("state")
    result["state"] = state if state in ("configured", "not_configured", "unknown", "broken") else "unknown"
    if not _recent(checked, now_ms):
        result["state"] = "stale"
    result["events"] = _strings(item.get("events"))
    result["matchers"] = _strings(item.get("matchers"))
    return result


def _decision(session_id, runtime, approvals, now_ms):
    selected = None
    for row in approvals[:500] if isinstance(approvals, list) else ():
        if not isinstance(row, dict) or row.get("requestor_session_id") != session_id:
            continue
        meta = row.get("args")
        if not isinstance(meta, dict) or meta.get("runtime") != runtime \
                or meta.get("source") != "pretooluse-hook" \
                or meta.get("kind") in ("question_set", "permission_prompt"):
            continue
        status = row.get("status")
        if status not in ("pending", "approved", "auto_approved", "denied", "expired", "timeout"):
            continue
        stamp = _time_ms(row.get("resolved_at")) or _time_ms(row.get("created_at"))
        if not stamp or stamp > now_ms:
            continue
        if selected and selected["observed_at"] >= stamp:
            continue
        # Only record references and fixed tokens. Raw inputs may contain secrets.
        selected = {"record_id": str(row.get("id") or "")[:128],
                    "source": "local_pre_tool_approval", "result": status,
                    "observed_at": stamp, "recent": _recent(stamp, now_ms)}
    return selected


def _isolation(row, policies, now_ms):
    result = {"state": "unknown", "source": None, "observed_at": None,
              "execution_verified": False,
              "detail": "Subprocess file and network isolation has not been verified."}
    # tool_policy is an OpenClaw-native source. Similar agent IDs in another
    # runtime must not inherit its sandbox claim.
    if row.get("runtime") not in ("openclaw", "nemoclaw") or not row.get("agent_id"):
        return result
    for policy in policies[:100] if isinstance(policies, list) else ():
        if not isinstance(policy, dict) or policy.get("agent_id") != row["agent_id"]:
            continue
        mode = policy.get("sandbox_mode")
        if mode not in ("off", "all", "non-main", "nonmain"):
            continue
        stamp = _number(policy.get("observed_at"))
        stamp = int(stamp) if stamp else None
        if not stamp or stamp > now_ms:
            continue
        result.update(state=("configured" if mode != "off" else "not_configured")
                      if _recent(stamp, now_ms) else "stale",
                      source="native_sandbox_configuration", observed_at=stamp,
                      mode=mode,
                      detail="The native sandbox setting was recorded. Its isolation has not been verified for this session.")
        break
    return result


def _inspection(status, now_ms):
    result = {"state": "unknown", "scope": "node", "source": "incremental_security_ingest",
              "last_pass_ms": None, "processed": None, "unscoped": None, "limitations": None,
              "page_full": None, "history_gap": None,
              "backfill_pending": None, "priority_processed": None}
    if not isinstance(status, dict):
        return result
    stamp = _number(status.get("last_pass_ms"))
    if stamp is None or stamp > now_ms:
        return result
    result["last_pass_ms"] = int(stamp)
    state = status.get("status")
    result["state"] = state if state in ("inspected", "partial", "unavailable", "disabled") else "unknown"
    if result["state"] == "inspected" and status.get("page_full") is True:
        result["state"] = "backlog"
    if result["state"] in ("inspected", "backlog") and status.get("backfill_pending") is True:
        result["state"] = "partial"
    if not _recent(stamp, now_ms):
        result["state"] = "stale"
    for name in ("processed", "unscoped", "limitations", "priority_processed"):
        val = status.get(name)
        if type(val) is int and 0 <= val <= 1_000_000:
            result[name] = val
    result["page_full"] = status.get("page_full") if type(status.get("page_full")) is bool else None
    result["history_gap"] = status.get("history_gap") if type(status.get("history_gap")) is bool else None
    result["backfill_pending"] = status.get("backfill_pending") if type(status.get("backfill_pending")) is bool else None
    return result


def build(row, *, approvals=None, hooks=None, tool_policies=None, inspection=None, now=None):
    """Build a bounded per-session report from node-owned records only.

    No metadata supplied by an observed agent is promoted to independent
    sandbox, scanner or execution evidence. An approval decision states a
    review result, never proof that the runtime applied it.
    """
    row = row if isinstance(row, dict) else {}
    now = time.time() if now is None else now
    now_ms = int((_number(now) or 0) * 1000)
    runtime = str(row.get("runtime") or "")
    session_id = str(row.get("session_id") or "")
    is_remote = isinstance(row.get("observation"), dict) and row["observation"].get("prevented") is False
    can_control = row.get("controllable")
    configuration = _configuration(runtime, None if is_remote else hooks, now_ms)
    return {
        "schema_version": 1, "generated_at": now_ms,
        "node_inspection": _inspection(inspection, now_ms),
        "observation": {
            "state": "pending" if row.get("pending_ingest") else "recorded",
            "source": "exported_telemetry" if is_remote else "local_store",
            "execution_verified": False,
            "detail": "Recorded activity does not establish that an action was prevented.",
        },
        "pre_tool": {
            "capability": "supported" if configuration.get("supported") is True else "not_verified",
            "configuration": configuration,
            "last_decision": None if is_remote else _decision(session_id, runtime, approvals, now_ms),
            "execution_verified": False,
            "initial_service_failure": "not_verified",
            "detail": "A hook setting or approval record does not verify every tool call. Initial service failure remains a coverage gap.",
        },
        "containment": {
            "state": "available" if can_control is True else "unavailable" if can_control is False else "unknown",
            "source": "session_control_capability" if can_control is not None else None,
            "actions": [a for a in row.get("control_actions", []) if a in ("pause", "resume", "stop", "kill")]
                       if isinstance(row.get("control_actions"), list) else [],
            "execution_verified": False,
            "detail": "Available controls do not establish that a process has been contained.",
        },
        "isolation": _isolation(row, None if is_remote else tool_policies, now_ms),
        "code_validation": {
            "state": "unknown", "source": None, "execution_verified": False,
            "detail": "This view has no independent code scan evidence. Check code results before release.",
        },
    }


def load_context(call):
    """Three bounded reads shared by every listed session, never per-row I/O."""
    context = {"approvals": [], "hooks": None, "tool_policies": [], "inspection": None}
    for method, target, kwargs in (
            ("query_approvals", "approvals", {"limit": 500}),
            ("query_tool_policy", "tool_policies", {"limit": 100}),
            ("list_node_settings", "hooks", {})):
        try:
            value = call(method, **kwargs)
            if target == "hooks":
                raw = value.get(HOOK_SETTING) if isinstance(value, dict) else None
                context[target] = json.loads(raw) if isinstance(raw, str) else raw
                raw_status = value.get(SECURITY_STATUS_SETTING) if isinstance(value, dict) else None
                context["inspection"] = json.loads(raw_status) if isinstance(raw_status, str) else raw_status
            elif isinstance(value, list):
                context[target] = value
        except Exception as exc:
            log.warning("Protection evidence unavailable from %s (%s)", method, type(exc).__name__)
    return context


def capture_and_store(store):
    """Daemon-only configuration observation, with no control side effect."""
    from clawmetry.protection_capture import capture_hook_configuration
    value = capture_hook_configuration()
    store.set_node_setting(HOOK_SETTING, json.dumps(value, separators=(",", ":")))
    return value
