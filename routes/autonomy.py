"""
routes/autonomy.py — Autonomy Score endpoint.

North-star metric for how autonomous the user's agent is becoming.
Based on Alexander Krentsel's Berkeley talk *Principles for Autonomous System
Design*:  "Success will be when human nudges space out exponentially."

Blueprint: bp_autonomy
Endpoint:  GET /api/autonomy
"""

from __future__ import annotations

import json
import math
import os
import statistics
from collections import defaultdict
from datetime import datetime, timezone

from flask import Blueprint, jsonify
from clawmetry.config import is_local_store_read_enabled

bp_autonomy = Blueprint("autonomy", __name__)

_AUTONOMY_CACHE = {"ts": 0.0, "data": None}
_AUTONOMY_CACHE_TTL_SECONDS = 60


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _parse_ts(msg: dict, file_mtime: float) -> float:
    """Return a unix timestamp (float seconds) for *msg*.

    Checks keys in order: timestamp, ts, created_at, time.  Handles both
    unix-epoch numbers and ISO-8601 strings.  Falls back to *file_mtime*.
    """
    for key in ("timestamp", "ts", "created_at", "time"):
        val = msg.get(key)
        if val is None:
            continue
        if isinstance(val, (int, float)):
            v = float(val)
            # Distinguish milliseconds from seconds: epoch > 1e12 → ms
            return v / 1000.0 if v > 1e12 else v
        if isinstance(val, str) and val:
            try:
                return datetime.fromisoformat(
                    val.replace("Z", "+00:00")
                ).timestamp()
            except ValueError:
                pass
    return file_mtime


def _median_safe(values: list):
    """Return median of *values*, or None if list is empty."""
    if not values:
        return None
    return statistics.median(values)


def _linear_slope(xs: list, ys: list) -> float:
    """Return the slope of a simple linear regression of xs → ys."""
    n = len(xs)
    if n < 2:
        return 0.0
    x_mean = sum(xs) / n
    y_mean = sum(ys) / n
    denom = sum((x - x_mean) ** 2 for x in xs)
    if denom == 0:
        return 0.0
    numer = sum((xs[i] - x_mean) * (ys[i] - y_mean) for i in range(n))
    return numer / denom


def _compute_autonomy(sessions_dir: str) -> dict:
    """Scan session JSONL files and return autonomy metrics."""

    now_utc = datetime.now(tz=timezone.utc)
    cutoff_ts = now_utc.timestamp() - 7 * 86400  # 7 days ago

    # Buckets: day-string → {gaps: [...], sessions_with_no_extra_nudge: int, sessions: int, user_msgs: int}
    daily: dict = defaultdict(lambda: {"gaps": [], "no_nudge_sessions": 0, "sessions": 0, "user_msgs": 0})

    all_gaps: list = []
    total_sessions_7d = 0
    no_nudge_sessions_7d = 0
    total_user_msgs_7d = 0

    if not sessions_dir or not os.path.isdir(sessions_dir):
        return _empty_response()

    try:
        files = [
            f for f in os.listdir(sessions_dir)
            if f.endswith(".jsonl")
            and ".deleted." not in f
            and ".reset." not in f
            and ".trajectory." not in f
            and ".checkpoint." not in f
        ]
    except OSError:
        return _empty_response()

    for fname in files:
        fpath = os.path.join(sessions_dir, fname)
        try:
            file_mtime = os.path.getmtime(fpath)
        except OSError:
            file_mtime = now_utc.timestamp()

        # Quick reject: if file is older than 7 days and not recently modified
        if file_mtime < cutoff_ts:
            continue

        user_timestamps: list = []
        any_msg_in_window = False

        try:
            with open(fpath, "r", errors="replace") as fh:
                for raw in fh:
                    raw = raw.strip()
                    if not raw:
                        continue
                    try:
                        ev = json.loads(raw)
                    except (json.JSONDecodeError, ValueError):
                        continue

                    # Support both bare messages and wrapped {"type":"message","message":{}}
                    if isinstance(ev, dict):
                        if ev.get("type") == "message":  # v3-shape-gate: allow (reason: JSONL on-disk walker; transcript files keep pre-v3 shape)
                            msg = ev.get("message") or {}
                        else:
                            msg = ev
                    else:
                        continue

                    role = msg.get("role", "")
                    if role != "user":
                        continue

                    ts = _parse_ts(msg, file_mtime)
                    # Also check outer event for timestamp
                    if ts == file_mtime and isinstance(ev, dict) and ev.get("type") == "message":  # v3-shape-gate: allow (reason: JSONL on-disk walker; transcript files keep pre-v3 shape)
                        ts = _parse_ts(ev, file_mtime)

                    if ts < cutoff_ts:
                        continue

                    any_msg_in_window = True
                    user_timestamps.append(ts)
        except OSError:
            continue

        if not any_msg_in_window or not user_timestamps:
            continue

        user_timestamps.sort()
        total_sessions_7d += 1

        # Gaps between consecutive user messages (seconds)
        session_gaps = [
            user_timestamps[i + 1] - user_timestamps[i]
            for i in range(len(user_timestamps) - 1)
            if user_timestamps[i + 1] - user_timestamps[i] > 0  # ignore sub-second noise
        ]

        # "No nudge after first" = only 1 user message in the session
        is_no_nudge = len(user_timestamps) <= 1
        if is_no_nudge:
            no_nudge_sessions_7d += 1

        total_user_msgs_7d += len(user_timestamps)
        all_gaps.extend(session_gaps)

        # Per-day bucketing (use timestamp of first user msg in session)
        day_key = datetime.fromtimestamp(user_timestamps[0], tz=timezone.utc).strftime("%Y-%m-%d")
        daily[day_key]["gaps"].extend(session_gaps)
        daily[day_key]["sessions"] += 1
        daily[day_key]["user_msgs"] += len(user_timestamps)
        if is_no_nudge:
            daily[day_key]["no_nudge_sessions"] += 1

    if total_sessions_7d == 0:
        return _empty_response()

    # Aggregate metrics
    median_gap = _median_safe(all_gaps)
    autonomy_ratio = no_nudge_sessions_7d / total_sessions_7d if total_sessions_7d else None

    # Build 7-day series (fill missing days with None)
    series_daily = []
    for offset in range(6, -1, -1):
        import datetime as _dt_mod
        day_dt = now_utc - _dt_mod.timedelta(days=offset)
        day_str = day_dt.strftime("%Y-%m-%d")
        bucket = daily.get(day_str)
        if bucket and bucket["sessions"] > 0:
            day_median = _median_safe(bucket["gaps"])
            day_ratio = (
                bucket["no_nudge_sessions"] / bucket["sessions"]
                if bucket["sessions"] else None
            )
            series_daily.append({
                "day": day_str,
                "median_gap_sec": day_median,
                "autonomy_ratio": day_ratio,
                "sessions": bucket["sessions"],
            })
        else:
            series_daily.append({
                "day": day_str,
                "median_gap_sec": None,
                "autonomy_ratio": None,
                "sessions": 0,
            })

    # Trend: linear regression of daily median_gap over the 7 days
    xs = []
    ys = []
    for i, entry in enumerate(series_daily):
        if entry["median_gap_sec"] is not None:
            xs.append(float(i))
            ys.append(entry["median_gap_sec"])

    trend_slope_7d = 0.0
    if len(xs) >= 2:
        raw_slope = _linear_slope(xs, ys)
        # Normalise by median so it's scale-free
        if median_gap and median_gap > 0:
            trend_slope_7d = raw_slope / median_gap
        else:
            trend_slope_7d = 0.0

    if trend_slope_7d > 0.02:
        trend_direction = "improving"
    elif trend_slope_7d < -0.02:
        trend_direction = "declining"
    else:
        trend_direction = "flat"

    # Composite score clamped to [0, 1]
    try:
        ar = autonomy_ratio if autonomy_ratio is not None else 0.0
        tanh_part = math.tanh(trend_slope_7d * 10) * 0.5
        raw_score = 0.5 * ar + tanh_part + 0.5
        score = max(0.0, min(1.0, raw_score))
    except Exception:
        score = 0.0

    return {
        "score": round(score, 4),
        "median_gap_seconds_7d": median_gap,
        "autonomy_ratio_7d": autonomy_ratio,
        "trend_slope_7d": round(trend_slope_7d, 6),
        "trend_direction": trend_direction,
        "samples_7d": total_user_msgs_7d,
        "series_daily": series_daily,
    }


def _empty_response() -> dict:
    return {
        "score": None,
        "median_gap_seconds_7d": None,
        "autonomy_ratio_7d": None,
        "trend_slope_7d": None,
        "trend_direction": "no_data",
        "samples_7d": 0,
        "series_daily": [],
    }


def _try_local_store_autonomy() -> dict | None:
    """Tier-1 DuckDB fast path for /api/autonomy.

    Reads ``message`` events from the local store, filters to user-role
    messages within the last 7 days, and runs the same per-session gap
    aggregation the JSONL parser does. Returns the canonical autonomy
    payload (score / median_gap / autonomy_ratio / trend / series_daily)
    plus ``"_source": "local_store"``.

    Returns ``None`` to defer to the legacy fallback if:
      - the ``local_store`` module isn't importable
      - the events table has no qualifying user messages
      - any unexpected error happens (we'd rather degrade than 500)
    """
    try:
        from clawmetry import local_store
    except Exception:
        return None
    # Issue #1256: route through daemon HTTP proxy. Direct get_store()
    # raises IOException on multi-process installs (DuckDB's file lock is
    # exclusive across processes; read_only=True doesn't bypass it).
    try:
        from routes.local_query import local_store_via_daemon
        rows = local_store_via_daemon("query_events", event_type="message", limit=5000)
        if rows is None:
            # Daemon unreachable → single-process fallback (tests/dev mode).
            store = local_store.get_store(read_only=True)
            rows = store.query_events(event_type="message", limit=5000)
    except Exception:
        return None
    if not rows:
        return None

    now_utc = datetime.now(tz=timezone.utc)
    cutoff_ts = now_utc.timestamp() - 7 * 86400

    # session_id → sorted list of user-msg unix timestamps (within the window)
    per_session: dict[str, list[float]] = defaultdict(list)
    for r in rows:
        ts_str = r.get("ts") or ""
        if not ts_str:
            continue
        try:
            ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00")).timestamp()
        except Exception:
            continue
        if ts < cutoff_ts:
            continue
        data = r.get("data") if isinstance(r, dict) else None
        if not isinstance(data, dict):
            continue
        msg = data.get("message") if isinstance(data.get("message"), dict) else data
        role = msg.get("role") if isinstance(msg, dict) else None
        if role != "user":
            continue
        sid = r.get("session_id") or ""
        per_session[sid].append(ts)

    if not per_session:
        return None

    daily: dict = defaultdict(lambda: {
        "gaps": [], "no_nudge_sessions": 0, "sessions": 0, "user_msgs": 0,
    })
    all_gaps: list = []
    total_sessions_7d = 0
    no_nudge_sessions_7d = 0
    total_user_msgs_7d = 0

    for sid, stamps in per_session.items():
        stamps.sort()
        total_sessions_7d += 1
        session_gaps = [
            stamps[i + 1] - stamps[i]
            for i in range(len(stamps) - 1)
            if stamps[i + 1] - stamps[i] > 0
        ]
        is_no_nudge = len(stamps) <= 1
        if is_no_nudge:
            no_nudge_sessions_7d += 1
        total_user_msgs_7d += len(stamps)
        all_gaps.extend(session_gaps)
        day_key = datetime.fromtimestamp(stamps[0], tz=timezone.utc).strftime("%Y-%m-%d")
        daily[day_key]["gaps"].extend(session_gaps)
        daily[day_key]["sessions"] += 1
        daily[day_key]["user_msgs"] += len(stamps)
        if is_no_nudge:
            daily[day_key]["no_nudge_sessions"] += 1

    if total_sessions_7d == 0:
        return None

    median_gap = _median_safe(all_gaps)
    autonomy_ratio = (no_nudge_sessions_7d / total_sessions_7d) if total_sessions_7d else None

    series_daily = []
    import datetime as _dt_mod
    for offset in range(6, -1, -1):
        day_dt = now_utc - _dt_mod.timedelta(days=offset)
        day_str = day_dt.strftime("%Y-%m-%d")
        bucket = daily.get(day_str)
        if bucket and bucket["sessions"] > 0:
            day_median = _median_safe(bucket["gaps"])
            day_ratio = (bucket["no_nudge_sessions"] / bucket["sessions"]
                         if bucket["sessions"] else None)
            series_daily.append({
                "day": day_str,
                "median_gap_sec": day_median,
                "autonomy_ratio": day_ratio,
                "sessions": bucket["sessions"],
            })
        else:
            series_daily.append({
                "day": day_str,
                "median_gap_sec": None,
                "autonomy_ratio": None,
                "sessions": 0,
            })

    xs, ys = [], []
    for i, entry in enumerate(series_daily):
        if entry["median_gap_sec"] is not None:
            xs.append(float(i))
            ys.append(entry["median_gap_sec"])

    trend_slope_7d = 0.0
    if len(xs) >= 2:
        raw_slope = _linear_slope(xs, ys)
        if median_gap and median_gap > 0:
            trend_slope_7d = raw_slope / median_gap
    if trend_slope_7d > 0.02:
        trend_direction = "improving"
    elif trend_slope_7d < -0.02:
        trend_direction = "declining"
    else:
        trend_direction = "flat"

    try:
        ar = autonomy_ratio if autonomy_ratio is not None else 0.0
        tanh_part = math.tanh(trend_slope_7d * 10) * 0.5
        raw_score = 0.5 * ar + tanh_part + 0.5
        score = max(0.0, min(1.0, raw_score))
    except Exception:
        score = 0.0

    return {
        "score": round(score, 4),
        "median_gap_seconds_7d": median_gap,
        "autonomy_ratio_7d": autonomy_ratio,
        "trend_slope_7d": round(trend_slope_7d, 6),
        "trend_direction": trend_direction,
        "samples_7d": total_user_msgs_7d,
        "series_daily": series_daily,
        "_source": "local_store",
    }


# ---------------------------------------------------------------------------
# Route
# ---------------------------------------------------------------------------

@bp_autonomy.route("/api/autonomy")
def api_autonomy():
    import dashboard as _d
    now = datetime.now(tz=timezone.utc).timestamp()
    cached = _AUTONOMY_CACHE.get("data")
    if cached is not None and (now - float(_AUTONOMY_CACHE.get("ts") or 0)) < _AUTONOMY_CACHE_TTL_SECONDS:
        return jsonify(cached)

    # Tier-1 DuckDB fast path — opt-in via CLAWMETRY_LOCAL_STORE_READ=1.
    # Falls through to legacy JSONL scan when the flag is unset, the store
    # is empty, or no qualifying user messages exist in the 7-day window.
    if is_local_store_read_enabled():
        fast = _try_local_store_autonomy()
        if fast is not None:
            _AUTONOMY_CACHE["data"] = fast
            _AUTONOMY_CACHE["ts"] = now
            return jsonify(fast)

    sessions_dir = _d.SESSIONS_DIR or os.path.expanduser(
        "~/.openclaw/agents/main/sessions"
    )
    try:
        result = _compute_autonomy(sessions_dir)
    except Exception:
        result = _empty_response()
    _AUTONOMY_CACHE["data"] = result
    _AUTONOMY_CACHE["ts"] = now
    return jsonify(result)
