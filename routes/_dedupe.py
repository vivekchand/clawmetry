"""routes/_dedupe.py — sibling-dedupe helper for v3 event sums (issue #1451).

Real OpenClaw v3 + Claude Code emit two event rows per billable LLM turn:
a rich ``assistant``/``message`` envelope plus a slim ``model.completed``
sibling ~100 ms later. Any analytics surface that blindly sums
``token_count`` over the events table therefore double-counts every turn.

This module centralises the 2-pass dedupe so every surface picks the
**richest envelope** per ``(session_id, ts_sec ±1 s)`` bucket. ``±1 s``
covers the writer-race window between the two emitters.

Usage::

    from routes._dedupe import build_sibling_bucket_max, is_sibling_dup

    bucket_max = build_sibling_bucket_max(events)
    for ev in events:
        if is_sibling_dup(ev, bucket_max):
            continue
        tokens += int(ev.get("token_count") or 0)
"""

from __future__ import annotations

from datetime import datetime

# ``assistant``/``message`` outrank ``model.completed`` inside one bucket.
_RICHER = {"assistant": 2, "message": 2, "model.completed": 1}


def _ts_sec(ts_str) -> int:
    """ISO-8601 string → integer epoch second. Returns 0 on any failure."""
    if not ts_str or not isinstance(ts_str, str):
        return 0
    try:
        return int(datetime.fromisoformat(ts_str.replace("Z", "+00:00")).timestamp())
    except Exception:
        return 0


def build_sibling_bucket_max(rows) -> dict:
    """Pass 1: scan rows once, return ``{(sid, sec±1): max_rank}``."""
    bucket_max: dict = {}
    for r in rows:
        et = (r.get("event_type") or "").strip()
        if et not in _RICHER:
            continue
        sid = r.get("session_id") or ""
        sec = _ts_sec(r.get("ts") or "")
        rank = _RICHER[et]
        for key in ((sid, sec - 1), (sid, sec), (sid, sec + 1)):
            if bucket_max.get(key, 0) < rank:
                bucket_max[key] = rank
    return bucket_max


def is_sibling_dup(row, bucket_max: dict) -> bool:
    """Pass 2 predicate: True iff ``row`` is a slim sibling of a richer
    envelope already in its ``(sid, sec)`` bucket. Non-sibling event types
    always return False (they don't have a paired writer)."""
    et = (row.get("event_type") or "").strip()
    if et not in _RICHER:
        return False
    sid = row.get("session_id") or ""
    sec = _ts_sec(row.get("ts") or "")
    return bucket_max.get((sid, sec), 0) > _RICHER[et]
