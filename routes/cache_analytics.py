"""
routes/cache_analytics.py — Prompt Cache Hit Rate Analytics.

Shows how effectively prompt caching is being used across sessions,
including hit ratios, token breakdowns, estimated cost savings, and
per-model / per-session drill-downs.

Blueprint: bp_cache_analytics
Endpoint:  GET /api/cache-analytics
"""

import json
import os
import time
from collections import defaultdict
from datetime import datetime, timezone, timedelta

from flask import Blueprint, jsonify

bp_cache_analytics = Blueprint("cache_analytics", __name__)

# ---------------------------------------------------------------------------
# Cost constants (Anthropic pricing)
# ---------------------------------------------------------------------------

_NORMAL_INPUT_PER_TOKEN = 3.00 / 1_000_000   # $3.00 per 1M tokens
_CACHED_INPUT_PER_TOKEN = 0.30 / 1_000_000   # $0.30 per 1M tokens
_SAVINGS_PER_CACHED_TOKEN = _NORMAL_INPUT_PER_TOKEN - _CACHED_INPUT_PER_TOKEN  # $2.70 per 1M

# ---------------------------------------------------------------------------
# Cache
# ---------------------------------------------------------------------------

_CACHE_TTL = 30  # seconds
_cache_result = None
_cache_ts = 0.0


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _parse_ts(msg, file_mtime):
    """Return a unix timestamp for *msg*."""
    for key in ("timestamp", "ts", "created_at", "time"):
        val = msg.get(key)
        if val is None:
            continue
        if isinstance(val, (int, float)):
            v = float(val)
            return v / 1000.0 if v > 1e12 else v
        if isinstance(val, str) and val:
            try:
                return datetime.fromisoformat(
                    val.replace("Z", "+00:00")
                ).timestamp()
            except ValueError:
                pass
    return file_mtime


def _compute_cache_analytics(sessions_dir):
    """Scan session JSONL files and compute cache analytics for the last 7 days."""
    now_utc = datetime.now(timezone.utc)
    cutoff_ts = (now_utc - timedelta(days=7)).timestamp()

    # Accumulators
    total_calls = 0
    calls_with_cache = 0
    total_cache_read = 0
    total_cache_write = 0
    total_input_tokens = 0

    daily = defaultdict(lambda: {
        "calls": 0, "cache_hits": 0,
        "cache_read": 0, "cache_write": 0,
    })
    per_model = defaultdict(lambda: {
        "calls": 0, "cache_hits": 0, "cache_read": 0,
    })
    per_session = {}  # session_id -> {calls, cache_hits, cache_read}

    if not sessions_dir or not os.path.isdir(sessions_dir):
        return _empty_response()

    try:
        files = [
            f for f in os.listdir(sessions_dir)
            if f.endswith(".jsonl") and ".deleted." not in f and ".reset." not in f
        ]
    except OSError:
        return _empty_response()

    for fname in files:
        fpath = os.path.join(sessions_dir, fname)
        try:
            file_mtime = os.path.getmtime(fpath)
        except OSError:
            file_mtime = now_utc.timestamp()

        if file_mtime < cutoff_ts:
            continue

        session_id = fname.replace(".jsonl", "")
        sess_calls = 0
        sess_cache_hits = 0
        sess_cache_read = 0

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

                    if not isinstance(ev, dict):
                        continue

                    # Support both bare messages and wrapped
                    if ev.get("type") == "message":
                        msg = ev.get("message") or {}
                    else:
                        msg = ev

                    # Only count assistant messages with usage (LLM calls)
                    if msg.get("role") != "assistant":
                        continue
                    usage = msg.get("usage")
                    if not isinstance(usage, dict):
                        continue

                    ts = _parse_ts(msg, file_mtime)
                    if ts == file_mtime and isinstance(ev, dict) and ev.get("type") == "message":
                        ts = _parse_ts(ev, file_mtime)
                    if ts < cutoff_ts:
                        continue

                    cache_read = usage.get("cacheRead", 0) or 0
                    cache_write = usage.get("cacheWrite", 0) or 0
                    input_tokens = usage.get("input", 0) or 0
                    model = msg.get("model", "unknown") or "unknown"

                    total_calls += 1
                    sess_calls += 1
                    total_input_tokens += input_tokens
                    total_cache_read += cache_read
                    total_cache_write += cache_write

                    has_cache = cache_read > 0
                    if has_cache:
                        calls_with_cache += 1
                        sess_cache_hits += 1
                    sess_cache_read += cache_read

                    # Daily bucket
                    day_key = datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%d")
                    daily[day_key]["calls"] += 1
                    daily[day_key]["cache_read"] += cache_read
                    daily[day_key]["cache_write"] += cache_write
                    if has_cache:
                        daily[day_key]["cache_hits"] += 1

                    # Per-model
                    per_model[model]["calls"] += 1
                    per_model[model]["cache_read"] += cache_read
                    if has_cache:
                        per_model[model]["cache_hits"] += 1

        except OSError:
            continue

        if sess_calls > 0:
            per_session[session_id] = {
                "calls": sess_calls,
                "cache_hits": sess_cache_hits,
                "cache_read": sess_cache_read,
            }

    if total_calls == 0:
        return _empty_response()

    cache_hit_ratio = calls_with_cache / total_calls
    estimated_savings = total_cache_read * _SAVINGS_PER_CACHED_TOKEN

    # Build 7-day series
    series_daily = []
    for offset in range(6, -1, -1):
        day_dt = now_utc - timedelta(days=offset)
        day_str = day_dt.strftime("%Y-%m-%d")
        bucket = daily.get(day_str)
        if bucket and bucket["calls"] > 0:
            series_daily.append({
                "day": day_str,
                "hit_ratio": round(bucket["cache_hits"] / bucket["calls"], 4),
                "cache_read": bucket["cache_read"],
                "cache_write": bucket["cache_write"],
                "total_calls": bucket["calls"],
                "savings_usd": round(bucket["cache_read"] * _SAVINGS_PER_CACHED_TOKEN, 4),
            })
        else:
            series_daily.append({
                "day": day_str,
                "hit_ratio": None,
                "cache_read": 0,
                "cache_write": 0,
                "total_calls": 0,
                "savings_usd": 0.0,
            })

    # Per-model list
    per_model_list = sorted(
        [
            {
                "model": m,
                "hit_ratio": round(d["cache_hits"] / d["calls"], 4) if d["calls"] else 0,
                "cache_read": d["cache_read"],
                "total_calls": d["calls"],
            }
            for m, d in per_model.items()
        ],
        key=lambda x: x["cache_read"],
        reverse=True,
    )

    # Per-session top 10 by cache_read
    per_session_list = sorted(
        [
            {
                "session_id": sid,
                "hit_ratio": round(d["cache_hits"] / d["calls"], 4) if d["calls"] else 0,
                "cache_read": d["cache_read"],
                "total_calls": d["calls"],
            }
            for sid, d in per_session.items()
        ],
        key=lambda x: x["cache_read"],
        reverse=True,
    )[:10]

    return {
        "cache_hit_ratio": round(cache_hit_ratio, 4),
        "total_cache_read_tokens": total_cache_read,
        "total_cache_write_tokens": total_cache_write,
        "total_input_tokens": total_input_tokens,
        "estimated_savings_usd": round(estimated_savings, 4),
        "series_daily": series_daily,
        "per_model": per_model_list,
        "per_session": per_session_list,
    }


def _empty_response():
    return {
        "cache_hit_ratio": None,
        "total_cache_read_tokens": 0,
        "total_cache_write_tokens": 0,
        "total_input_tokens": 0,
        "estimated_savings_usd": 0.0,
        "series_daily": [],
        "per_model": [],
        "per_session": [],
    }


# ---------------------------------------------------------------------------
# Route
# ---------------------------------------------------------------------------

@bp_cache_analytics.route("/api/cache-analytics")
def api_cache_analytics():
    global _cache_result, _cache_ts

    now = time.time()
    if _cache_result is not None and (now - _cache_ts) < _CACHE_TTL:
        return jsonify(_cache_result)

    import dashboard as _d
    sessions_dir = _d.SESSIONS_DIR or os.path.expanduser(
        "~/.openclaw/agents/main/sessions"
    )
    try:
        result = _compute_cache_analytics(sessions_dir)
    except Exception:
        result = _empty_response()

    _cache_result = result
    _cache_ts = now
    return jsonify(result)
