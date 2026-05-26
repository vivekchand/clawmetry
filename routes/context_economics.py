"""routes/context_economics.py — context-window economics (PRD P1-2).

Surfaces the cost of the context window itself: how full each agent turn's
prompt got, when OpenClaw compacted (proactively vs forced by an overflow
error), how many tokens each compaction reclaimed, and which sessions keep
slamming into the wall (overflow-then-retry).

  GET /api/context-economics?session_id=...

Returns ``{utilization, compactions, overflow_sessions, summary, _source}``.
Reads go through the daemon proxy (the daemon owns the DuckDB writer lock)
with a single-process direct-read fallback — the same pattern as
``routes/scheduler.py`` / ``routes/agents.py``. NEVER 500s on empty data: a
fresh sync (no compactions yet, or OpenClaw running under its context limit)
returns empty lists so the tab renders an honest "no compactions yet" state.
"""
from __future__ import annotations

from flask import Blueprint, jsonify, request

bp_context_economics = Blueprint("context_economics", __name__)


def _ls_call(method_name: str, **kwargs):
    """Cross-process LocalStore call with single-process fallback (issue #1088)."""
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


def _coerce(payload):
    """``local_store_via_daemon`` returns the raw method result (a dict) or a
    ``{"result": {...}}`` envelope depending on transport — normalise both."""
    if isinstance(payload, dict) and "result" in payload and isinstance(payload["result"], dict):
        return payload["result"]
    return payload if isinstance(payload, dict) else {}


@bp_context_economics.route("/api/context-economics")
def api_context_economics():
    """Context-window economics bundle.

    Query params:
      * ``session_id`` — scope the utilization gauge to one conversation
        (the UI session picker / clickable chips). Compactions + overflow
        flags are computed workspace-wide; the route filters them to the
        picked session here so the chips/list stay coherent with the gauge.
      * ``limit`` — max utilization points (<=2000, default 400).

    The ``summary`` block is a small derived rollup the tab paints as chips:
    compaction count, overflow count, total tokens reclaimed, peak window %.
    """
    session_id = (request.args.get("session_id") or "").strip() or None
    try:
        limit = max(1, min(2000, int(request.args.get("limit", 400))))
    except (TypeError, ValueError):
        limit = 400

    data = _coerce(_ls_call(
        "query_context_economics",
        session_id=session_id,
        util_limit=limit,
    ))
    utilization = data.get("utilization") or []
    compactions = data.get("compactions") or []
    overflow_sessions = data.get("overflow_sessions") or []

    # When a session is picked, scope compactions to it so the list matches
    # the gauge. (query_context_economics returns compactions workspace-wide
    # so the cross-session overflow flag stays meaningful.)
    if session_id:
        compactions = [
            c for c in compactions if str(c.get("session_id")) == session_id
        ]

    # Session chips for the picker: distinct sessions seen in the gauge,
    # most-recent first, with their peak utilization %.
    chips: dict[str, dict] = {}
    for u in utilization:
        sid = str(u.get("session_id") or "")
        if not sid:
            continue
        entry = chips.setdefault(sid, {"session_id": sid, "peak_pct": 0.0, "ts": ""})
        try:
            entry["peak_pct"] = max(entry["peak_pct"], float(u.get("pct") or 0))
        except (TypeError, ValueError):
            pass
        ts = str(u.get("ts") or "")
        if ts > entry["ts"]:
            entry["ts"] = ts
    session_chips = sorted(chips.values(), key=lambda c: c["ts"], reverse=True)

    total_reclaimed = sum(int(c.get("reclaimed") or 0) for c in compactions)
    overflow_count = sum(1 for c in compactions if c.get("trigger") == "overflow")
    peak_pct = max((float(u.get("pct") or 0) for u in utilization), default=0.0)
    summary = {
        "compaction_count":     len(compactions),
        "overflow_count":       overflow_count,
        "proactive_count":      len(compactions) - overflow_count,
        "total_reclaimed":      total_reclaimed,
        "peak_pct":             round(peak_pct, 2),
        "overflow_sessions":    len(overflow_sessions),
        "utilization_points":   len(utilization),
    }

    return jsonify({
        "utilization":       utilization,
        "compactions":       compactions,
        "overflow_sessions": overflow_sessions,
        "session_chips":     session_chips,
        "summary":           summary,
        "_source":           "local_store",
    })
