"""Device snapshot — a compact, screen-sized JSON for hardware companions.

ClawMetry already ingests every supported runtime (OpenClaw, NVIDIA NemoClaw,
and the 10 Pro adapters) into DuckDB. A small desk device (e.g. an ESP32 with a
tiny display) can't render the full dashboard, so this Blueprint exposes one
tiny, all-runtime payload it can poll over the local network and a ``/device-
preview`` page that renders that payload like the physical gauge would, so the
whole data path can be proven with zero hardware.

The endpoint is read-only and DuckDB-first like the rest of ClawMetry: it reads
through the daemon proxy (``_ls_call``) and reuses the same aggregate helpers
the dashboard uses, so it stays correct in cloud (no raw filesystem reads). A
short TTL cache keeps a chatty device from storming the daemon.
"""

import time

from flask import Blueprint, jsonify

bp_device = Blueprint("device", __name__)

# How long a built snapshot is reused before recomputing. A device that polls
# every second must not trigger a fresh DuckDB sweep every second — share one
# build across all pollers within the window (the performance-is-a-cost rule).
_SNAPSHOT_TTL_SECONDS = 5.0
_snapshot_cache = {"ts": 0.0, "payload": None}

SCHEMA_VERSION = 1


def _ls_call(method_name, **kwargs):
    """Cross-process LocalStore call with single-process fallback (issue #1088).

    Mirrors the per-module helper used across ``routes/`` — prefer the daemon
    HTTP proxy (so we never grab the writer lock), fall back to a read-only
    open for tests/dev where no daemon is running.
    """
    try:
        from routes.local_query import local_store_via_daemon

        result = local_store_via_daemon(method_name, **kwargs)
        if result is not None:
            return result
    except Exception:
        pass
    try:
        from clawmetry import local_store

        store = local_store.get_store(read_only=True)
        return getattr(store, method_name)(**kwargs)
    except Exception:
        return None


def _coerce_rows(rows):
    """Normalise the proxy envelope (``{"result": [...]}`` / ``{"rows": [...]}``)
    or a bare list into a plain list."""
    if isinstance(rows, dict):
        rows = rows.get("result") or rows.get("rows") or []
    return rows if isinstance(rows, list) else []


def _runtime_for(session_id):
    """Map a session id to its runtime label. OSS-Free always resolves to
    ``openclaw``; the clawmetry-pro plugin resolves the real runtime."""
    try:
        from clawmetry import waste_flags as _wf

        return _wf.runtime_from_session_id(session_id) or "openclaw"
    except Exception:
        return "openclaw"


def _usage_today():
    """(cost_today_usd, tokens_today) across ALL runtimes, or (0.0, 0)."""
    try:
        from routes.usage import _try_local_store_usage

        usage = _try_local_store_usage() or {}
        return (
            round(float(usage.get("todayCost", 0.0)), 4),
            int(usage.get("today", 0)),
        )
    except Exception:
        return (0.0, 0)


def _active_sessions():
    """(active_count, sorted distinct runtimes among active sessions).

    Derived from the typed ``sessions`` table — the same source the Overview
    helper counts from (status == "active"). Runtime is the session-id prefix
    (``agent_type`` is always "openclaw"), so distinct runtimes light up across
    all 12 once clawmetry-pro is installed.
    """
    rows = _coerce_rows(_ls_call("query_sessions_table", limit=300))
    active = [s for s in rows if isinstance(s, dict) and s.get("status") == "active"]
    runtimes = sorted({_runtime_for(s.get("session_id") or "") for s in active})
    return len(active), runtimes


def _top_alert():
    """The single most important currently-firing alert (newest unack'd in the
    last 24h), or None."""
    try:
        import dashboard as _d

        alerts = _d._get_active_alerts() or []
        if not alerts:
            return None
        a = alerts[0]  # _get_active_alerts is ORDER BY fired_at DESC
        return {
            "message": a.get("message") or a.get("rule_id") or "Alert firing",
            "fired_at": a.get("fired_at"),
        }
    except Exception:
        return None


def _oldest_pending_approval():
    """The oldest pending approval (so the device surfaces what's been waiting
    longest), with its tool action + runtime, or None.

    ``query_approvals`` returns newest-first, so we take the min by
    ``created_at`` to get the oldest.
    """
    try:
        rows = _coerce_rows(_ls_call("query_approvals", status="pending", limit=200))
        rows = [r for r in rows if isinstance(r, dict)]
        if not rows:
            return None
        oldest = min(rows, key=lambda r: (r.get("created_at") or ""))
        sid = oldest.get("requestor_session_id") or ""
        created = oldest.get("created_at") or ""
        waiting = None
        # created_at is an ISO-ish string; best-effort age in seconds.
        try:
            from datetime import datetime

            ts = datetime.fromisoformat(str(created).replace("Z", "")[:19])
            waiting = max(0, int(time.time() - ts.timestamp()))
        except Exception:
            waiting = None
        return {
            "id": oldest.get("id"),
            "action": oldest.get("action") or "tool call",
            "runtime": _runtime_for(sid),
            "session_id": sid,
            "waiting_seconds": waiting,
        }
    except Exception:
        return None


def _overall_health(has_alert, has_approval):
    """Coarse green/amber/red the size of one LED.

    red   — daemon is broken.
    amber — daemon degraded, an alert is firing, or an approval is waiting.
    green — nothing needs a human.
    """
    daemon_status = None
    try:
        from routes.health import compute_daemon_health

        daemon_status = (compute_daemon_health() or {}).get("status")
    except Exception:
        daemon_status = None

    if daemon_status == "broken":
        return "red"
    if daemon_status == "degraded" or has_alert or has_approval:
        return "amber"
    return "green"


def _build_device_snapshot():
    """Assemble the compact, all-runtime device payload."""
    cost_today, tokens_today = _usage_today()
    active_count, runtimes = _active_sessions()
    alert = _top_alert()
    approval = _oldest_pending_approval()
    health = _overall_health(alert is not None, approval is not None)
    return {
        "schema": SCHEMA_VERSION,
        "generated_at": int(time.time()),
        "cost_today_usd": cost_today,
        "tokens_today": tokens_today,
        "active_sessions": active_count,
        "runtimes_active": runtimes,
        "health": health,
        "alert": alert,
        "approval": approval,
    }


def _device_snapshot_cached():
    """Build at most once per TTL window; share across all pollers."""
    now = time.time()
    cached = _snapshot_cache.get("payload")
    if cached is not None and (now - _snapshot_cache["ts"]) < _SNAPSHOT_TTL_SECONDS:
        return cached
    payload = _build_device_snapshot()
    _snapshot_cache["payload"] = payload
    _snapshot_cache["ts"] = now
    return payload


@bp_device.route("/api/device/snapshot")
def api_device_snapshot():
    """Compact, all-runtime snapshot a hardware companion can poll.

    Never raises: every contributing read degrades to a safe default, so the
    device always gets a well-formed payload (the never-crash-on-bad-input
    convention). Shape::

        {
          "schema": 1,
          "generated_at": 1733356800,
          "cost_today_usd": 4.12,
          "tokens_today": 1840000,
          "active_sessions": 3,
          "runtimes_active": ["claude_code", "openclaw"],
          "health": "green" | "amber" | "red",
          "alert":   {"message": "...", "fired_at": ...} | null,
          "approval": {"id": ..., "action": "Bash", "runtime": "claude_code",
                        "session_id": "...", "waiting_seconds": 42} | null
        }
    """
    try:
        return jsonify(_device_snapshot_cached())
    except Exception:
        # Absolute last resort — still hand the device a valid shape.
        return jsonify({
            "schema": SCHEMA_VERSION,
            "generated_at": int(time.time()),
            "cost_today_usd": 0.0,
            "tokens_today": 0,
            "active_sessions": 0,
            "runtimes_active": [],
            "health": "green",
            "alert": None,
            "approval": None,
        })

