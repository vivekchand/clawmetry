"""Connector liveness — turn the daemon's ``connector.health`` signal
stream into a per-channel ok/degraded/down verdict.

Incident 2026-05-24: a Telegram inbound long-poll wedged (network stall →
aborted shutdown that timed out) and never restarted. The agent kept
SENDING (scheduled crons fired) but silently stopped RECEIVING for ~37h,
and ClawMetry showed green the whole time.

The daemon (``sync.sync_connector_health_from_logs``) tails gateway.log +
gateway.err.log into ``connector.health`` events. This module is the SINGLE
classifier shared by:
  * the dashboard ``/api/system-health`` (``routes/health.py``), and
  * the cloud snapshot builder (``sync.sync_system_snapshot``),
so the local UI and the cloud dashboard never disagree on whether a channel
is down.

Pure + dependency-free (stdlib only) so the daemon can import it without
pulling Flask.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone

# An inbound poll that has been unhealthy this long with no recovery is DOWN.
CONNECTOR_DOWN_MIN = 15
# Window for counting repeated disconnects (flapping).
CONNECTOR_FLAP_WINDOW_MIN = 60
CONNECTOR_FLAP_COUNT = 3

CONNECTOR_HEALTHY = {"started", "recovered"}
CONNECTOR_UNHEALTHY = {"stall", "disconnect", "wedged"}


def enabled_channels_from_config(openclaw_dir: str | None = None) -> list[str]:
    """Channel providers explicitly enabled in openclaw.json
    (``channels.<provider>.enabled == true``).

    ``openclaw_dir`` overrides discovery (the daemon passes its resolved
    workspace). Falls back to ``$CLAWMETRY_OPENCLAW_DIR`` / ``$OPENCLAW_HOME``
    / ``~/.openclaw``. Empty on cloud / no config — the cloud reads liveness
    from the snapshot built daemon-side. Never raises.
    """
    candidates = []
    if openclaw_dir:
        candidates.append(os.path.join(openclaw_dir, "openclaw.json"))
    env = os.environ.get("CLAWMETRY_OPENCLAW_DIR") or os.environ.get("OPENCLAW_HOME")
    if env:
        candidates.append(os.path.join(env, "openclaw.json"))
    candidates.append(os.path.join(os.path.expanduser("~"), ".openclaw", "openclaw.json"))
    for p in candidates:
        try:
            if not os.path.exists(p):
                continue
            with open(p, errors="ignore") as f:
                cfg = json.load(f)
            chans = (cfg or {}).get("channels") or {}
            return [
                str(name).lower()
                for name, c in chans.items()
                if isinstance(c, dict) and c.get("enabled")
            ]
        except Exception:
            continue
    return []


def _mins_since(ts, now: datetime) -> int | None:
    try:
        t = datetime.fromisoformat(str(ts).replace("Z", "+00:00"))
        return max(0, int((now - t).total_seconds() / 60))
    except Exception:
        return None


def classify_connector_liveness(
    enabled: list[str],
    rows: list[dict],
    now: datetime | None = None,
) -> list[dict]:
    """Classify each enabled channel from the connector.health stream.

    ``rows`` is the output of ``LocalStore.query_connector_health`` —
    ``[{provider, kind, ts, raw}, ...]`` newest-first. Returns
    ``[{provider, state, reason, mins_ago, last_kind}, ...]``, worst-first,
    where ``state`` ∈ ``down`` | ``degraded`` | ``unknown`` | ``ok``.

    ``down`` is the verdict that catches a deaf channel: most-recent signal
    is unhealthy, no recovery since, and older than the grace window.
    """
    if not enabled:
        return []
    if now is None:
        now = datetime.now(timezone.utc)

    by_prov: dict[str, list] = {}
    for r in (rows or []):
        if isinstance(r, dict) and r.get("provider"):
            by_prov.setdefault(str(r["provider"]).lower(), []).append(r)

    out = []
    for prov in enabled:
        sigs = by_prov.get(prov, [])
        if not sigs:
            out.append({
                "provider": prov, "state": "unknown",
                "reason": "no inbound-poll signals seen in the last 24h",
                "mins_ago": None, "last_kind": None,
            })
            continue
        latest = sigs[0]
        latest_kind = latest.get("kind")
        mins_ago = _mins_since(latest.get("ts"), now)
        recent_bad = sum(
            1 for s in sigs
            if s.get("kind") in CONNECTOR_UNHEALTHY
            and (_mins_since(s.get("ts"), now) or 1e9) <= CONNECTOR_FLAP_WINDOW_MIN
        )
        if latest_kind in CONNECTOR_UNHEALTHY and (
            mins_ago is None or mins_ago >= CONNECTOR_DOWN_MIN
        ):
            state = "down"
            reason = (
                f"inbound poll {latest_kind} {mins_ago}m ago with no recovery "
                f"since — this channel can no longer receive messages"
            )
        elif latest_kind in CONNECTOR_UNHEALTHY:
            state = "degraded"
            reason = f"inbound poll {latest_kind} {mins_ago}m ago (watching for recovery)"
        elif recent_bad >= CONNECTOR_FLAP_COUNT:
            state = "degraded"
            reason = f"inbound poll flapping ({recent_bad} disconnects in the last hour)"
        else:
            state = "ok"
            reason = f"inbound poll healthy (last signal: {latest_kind} {mins_ago}m ago)"
        out.append({
            "provider": prov, "state": state, "reason": reason,
            "mins_ago": mins_ago, "last_kind": latest_kind,
        })
    order = {"down": 0, "degraded": 1, "unknown": 2, "ok": 3}
    out.sort(key=lambda r: order.get(r["state"], 9))
    return out
