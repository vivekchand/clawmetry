"""
routes/heartbeat.py — Heartbeat liveness panel API endpoint (#686).

Owns the single route registered on bp_heartbeat:

  GET  /api/heartbeat  — liveness summary with cadence, ok/action ratio,
                         and last 10 beat outcomes, computed from session
                         transcripts in SESSIONS_DIR.

Session transcripts are scanned for "heartbeat" sessions (name contains
"heartbeat") and their assistant replies classified:
  - "ok"     : assistant replied exactly "HEARTBEAT_OK"
  - "action" : any other assistant reply in a heartbeat session

All shared helpers (``SESSIONS_DIR``) stay in ``dashboard.py`` and are
reached via late ``import dashboard as _d`` to avoid circular imports.
"""

import json
import os
import time
from datetime import datetime, timezone

from flask import Blueprint, jsonify

bp_heartbeat = Blueprint("heartbeat", __name__)


def _parse_iso_ts(ts_str):
    """Parse an ISO-8601 timestamp string to a Unix float; return 0 on error."""
    if not ts_str or not isinstance(ts_str, str):
        return 0.0
    try:
        return datetime.fromisoformat(ts_str.replace("Z", "+00:00")).timestamp()
    except Exception:
        return 0.0


def _compute_heartbeat_data(sessions_dir):
    """
    Scan *sessions_dir* for heartbeat sessions and return a dict with:
      last_heartbeat_ts, cadence_24h, ok_vs_action_24h, recent_beats
    Returns sensible zero-state if the directory is missing or unreadable.
    """
    now = time.time()
    cutoff_24h = now - 86400  # 24 hours ago

    # Collect all .jsonl files, skip deleted/reset artefacts
    try:
        all_files = [
            f
            for f in os.listdir(sessions_dir)
            if f.endswith(".jsonl")
            and ".deleted." not in f
            and ".reset." not in f
        ]
    except OSError:
        all_files = []

    beats = []  # list of {"ts": float, "outcome": "ok"|"action"}

    for fname in all_files:
        # Quick name-level filter — only open files whose name hints "heartbeat"
        sid_lower = fname.lower()
        fpath = os.path.join(sessions_dir, fname)
        name_is_heartbeat = "heartbeat" in sid_lower

        # We also need to scan content for sessions that aren't named that way
        # but may still contain HEARTBEAT_OK replies.  For performance we skip
        # content scanning unless the name already indicates it; the spec says
        # "check name first".
        if not name_is_heartbeat:
            continue

        session_ts = None  # timestamp of the session's first assistant turn
        outcomes_in_file = []  # all assistant-reply outcomes in this file

        try:
            with open(fpath, "r", errors="replace") as fh:
                for raw in fh:
                    raw = raw.strip()
                    if not raw:
                        continue
                    try:
                        ev = json.loads(raw)
                    except Exception:
                        continue

                    if ev.get("type") != "message":
                        continue

                    msg = ev.get("message") or {}
                    role = msg.get("role", "")
                    if role != "assistant":
                        continue

                    ev_ts = _parse_iso_ts(ev.get("timestamp", ""))
                    if ev_ts <= 0:
                        continue

                    if session_ts is None:
                        session_ts = ev_ts

                    # Collect assistant text content
                    content = msg.get("content") or []
                    if not isinstance(content, list):
                        continue

                    reply_text = ""
                    for blk in content:
                        if isinstance(blk, dict) and blk.get("type") == "text":
                            reply_text += (blk.get("text") or "")
                        elif isinstance(blk, str):
                            reply_text += blk

                    reply_text = reply_text.strip()
                    outcome = "ok" if reply_text == "HEARTBEAT_OK" else "action"
                    outcomes_in_file.append({"ts": ev_ts, "outcome": outcome})

        except Exception:
            continue

        # Use the last (most recent) assistant turn as the beat timestamp,
        # falling back to the first if we only have one.
        if outcomes_in_file:
            beat_ts = outcomes_in_file[-1]["ts"]
            # Determine overall outcome for this session: if any turn is
            # "action", the session is "action"; otherwise "ok".
            final_outcome = (
                "action"
                if any(o["outcome"] == "action" for o in outcomes_in_file)
                else "ok"
            )
            beats.append({"ts": beat_ts, "outcome": final_outcome})

    # Sort by timestamp descending
    beats.sort(key=lambda b: b["ts"], reverse=True)

    last_heartbeat_ts = beats[0]["ts"] if beats else 0.0

    # 24h window
    beats_24h = [b for b in beats if b["ts"] >= cutoff_24h]
    ok_count = sum(1 for b in beats_24h if b["outcome"] == "ok")
    action_count = sum(1 for b in beats_24h if b["outcome"] == "action")
    total_24h = ok_count + action_count

    ok_ratio = round(ok_count / total_24h, 3) if total_24h > 0 else 1.0

    # 10 most recent beats (already sorted desc, reverse to show oldest first)
    recent_beats = list(reversed(beats[:10]))

    return {
        "last_heartbeat_ts": last_heartbeat_ts,
        "beats_24h": beats_24h,
        "ok_count": ok_count,
        "action_count": action_count,
        "ok_ratio": ok_ratio,
        "recent_beats": recent_beats,
    }


@bp_heartbeat.route("/api/heartbeat")
def api_heartbeat():
    """
    Return a comprehensive heartbeat liveness summary.

    Response shape:
    {
      "last_heartbeat_ts": <unix float>,
      "last_heartbeat_age_seconds": <int|null>,
      "expected_interval_seconds": <int>,
      "status": "healthy"|"drifting"|"missed"|"never",
      "cadence_24h": {
        "expected_beats": <int>,
        "actual_beats": <int>,
        "on_time_ratio": <float>
      },
      "ok_vs_action_24h": {
        "heartbeat_ok_count": <int>,
        "action_taken_count": <int>,
        "ok_ratio": <float>
      },
      "recent_beats": [{"ts": <float>, "outcome": "ok"|"action"}, ...]
    }
    """
    import dashboard as _d

    now = time.time()
    interval = int(_d._heartbeat_interval_sec)
    sessions_dir = _d.SESSIONS_DIR or os.path.expanduser(
        "~/.openclaw/agents/main/sessions"
    )

    data = {
        "last_heartbeat_ts": 0.0,
        "beats_24h": [],
        "ok_count": 0,
        "action_count": 0,
        "ok_ratio": 1.0,
        "recent_beats": [],
    }

    if os.path.isdir(sessions_dir):
        try:
            data = _compute_heartbeat_data(sessions_dir)
        except Exception:
            pass  # keep zero-state defaults

    last_ts = data["last_heartbeat_ts"]

    # Also incorporate the in-memory global (which may be more recent than
    # what's persisted to disk if the session JSONL hasn't been flushed yet).
    gw_last_ts = float(_d._last_heartbeat_ts or 0)
    if gw_last_ts > last_ts:
        last_ts = gw_last_ts

    # Compute age
    if last_ts > 0:
        age_seconds = int(now - last_ts)
    else:
        age_seconds = None

    # Determine status
    if last_ts == 0:
        status = "never"
    else:
        gap = now - last_ts
        if gap <= interval:
            status = "healthy"
        elif gap <= interval * 1.5:
            status = "drifting"
        else:
            status = "missed"

    # Expected beats in 24h window
    window_seconds = 86400
    expected_beats = max(1, window_seconds // interval) if interval > 0 else 48
    actual_beats = len(data["beats_24h"])
    on_time_ratio = round(actual_beats / expected_beats, 3) if expected_beats > 0 else 0.0
    on_time_ratio = min(on_time_ratio, 1.0)  # cap at 1.0

    return jsonify({
        "last_heartbeat_ts": last_ts,
        "last_heartbeat_age_seconds": age_seconds,
        "expected_interval_seconds": interval,
        "status": status,
        "cadence_24h": {
            "expected_beats": expected_beats,
            "actual_beats": actual_beats,
            "on_time_ratio": on_time_ratio,
        },
        "ok_vs_action_24h": {
            "heartbeat_ok_count": data["ok_count"],
            "action_taken_count": data["action_count"],
            "ok_ratio": data["ok_ratio"],
        },
        "recent_beats": data["recent_beats"],
    })
