"""Reply-recovery event scanner for the OpenClaw adapter.

OpenClaw 2026.9.2+ ('Replies survive restarts') recovers active, queued,
and delegated replies after Gateway restarts.  This module surfaces the
gateway-level restart-recovery signal so the dashboard meta view can report it.

Kept in its own module so Drift Bot can find it at the head of a short file
rather than buried deep inside the main adapter.
"""
from __future__ import annotations

_RECOVERY_KEYWORDS = (
    "reply recovery",
    "recovery marker",
    "reply restored",
    "reply resumed",
    "recover reply",
    "restart recover",
    "reply requeued",
    "reply recovered",
)


def reply_recovery_events(events: list) -> dict:
    """Return reply-recovery metadata when gateway logs show restart-triggered
    reply recovery (issue #5620).

    Scans the already-fetched gateway log events (no extra I/O). Returns a
    dict with:
    - ``replyRecoveryDetected`` (bool True) — at least one recovery event found
    - ``replyRecoveryCount`` (int) — number of matching events in the log window
    - ``lastReplyRecoveryTs`` (str, optional) — timestamp of the most recent event

    Returns ``{}`` when no recovery events are found. Never raises.
    """
    try:
        if not events:
            return {}
        recovery_events = []
        for evt in events:
            if not isinstance(evt, dict):
                continue
            msg = str(evt.get("msg", "")).lower()
            if not msg:
                continue
            if any(kw in msg for kw in _RECOVERY_KEYWORDS):
                recovery_events.append(evt)
        if not recovery_events:
            return {}
        result: dict = {
            "replyRecoveryDetected": True,
            "replyRecoveryCount": len(recovery_events),
        }
        last_ts = recovery_events[-1].get("ts")
        if last_ts is not None:
            result["lastReplyRecoveryTs"] = last_ts
        return result
    except Exception:
        return {}


# Legacy private alias kept for any callers that imported the old name directly.
_reply_recovery_events = reply_recovery_events
