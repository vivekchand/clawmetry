"""routes/turn_anatomy.py — per-turn anatomy waterfall (PRD P0-3).

A *turn* is one round of agent work: the events between two consecutive
``prompt.submitted`` boundaries within a session (the human/scheduler prompt,
the model call(s) it triggered, every tool the model invoked with its
start→end duration, any context compaction, and the final reply).

This decomposes a session into those turns and emits, per turn, an ordered
list of *spans* laid out on the wall-clock timeline so the UI can draw a
horizontal waterfall (bar width ∝ duration). It also exposes a *stalled*
detector: sessions whose most recent turn has been running with no new event
for longer than a threshold (a long-running / stuck agent indicator).

Events-first by design: reads the OpenClaw events ClawMetry already ingests
into DuckDB (no OTLP exporter needed), via the daemon read proxy
(``local_store_via_daemon``) with a single-process read-only fallback — the
same DuckDB-first pattern as ``routes/tracing.py`` / ``routes/scheduler.py``.
Never 500s on empty data.

Endpoints (bp_turn_anatomy):
  GET /api/turn-anatomy?session_id=...  — ordered spans grouped per turn
  GET /api/turn-anatomy/stalled         — sessions whose latest turn is stalled
"""
from __future__ import annotations

from datetime import datetime, timezone

from flask import Blueprint, jsonify, request

bp_turn_anatomy = Blueprint("turn_anatomy", __name__)

# Pure-plumbing event types that never become a span of their own.
_PLUMBING_TYPES = frozenset({
    "session.started", "session.ended", "session.created",
    "model.changed", "thinking_level_change", "context.compiled",
    "agent.heartbeat", "queue-operation",
})

# How long (minutes) a session's latest turn may sit with no new event before
# we flag it as stalled / long-running.
_DEFAULT_STALL_MIN = 5


def _events_for(session_id=None, limit=14000):
    """Read events via the daemon proxy with a single-process RO fallback."""
    rows = None
    try:
        from routes.local_query import local_store_via_daemon
        if session_id:
            rows = local_store_via_daemon(
                "query_events", session_id=session_id, limit=limit)
        else:
            rows = local_store_via_daemon("query_events", limit=limit)
    except Exception:
        rows = None
    if rows is None:
        try:
            from clawmetry.config import is_local_store_read_enabled
            if not is_local_store_read_enabled():
                return None
            from clawmetry import local_store
            store = local_store.get_store(read_only=True)
            rows = (store.query_events(session_id=session_id, limit=limit)
                    if session_id else store.query_events(limit=limit))
        except Exception:
            rows = None
    # The proxy may wrap the list in an envelope depending on transport.
    if isinstance(rows, dict):
        rows = rows.get("result") or rows.get("rows") or []
    return rows


def _ts_ms(ts):
    """Coerce an event ts (ISO-8601 string or epoch s/ms) to ms-since-epoch."""
    if ts is None:
        return None
    if isinstance(ts, (int, float)):
        return int(ts * 1000) if ts < 1e12 else int(ts)
    try:
        return int(datetime.fromisoformat(
            str(ts).replace("Z", "+00:00")).timestamp() * 1000)
    except Exception:
        return None


def _now_ms():
    return int(datetime.now(timezone.utc).timestamp() * 1000)


def _data(e):
    d = e.get("data")
    return d if isinstance(d, dict) else {}


def _classify(e):
    """Classify an event into a turn-anatomy kind.

    Handles BOTH OpenClaw v3 normalized types (prompt.submitted /
    model.completed / tool_call / tool_result) AND the multi-runtime adapter
    shapes (Claude Code, Codex, …) that emit ``message`` rows carrying the
    speaker in ``data.role``. This is a display classifier, not a row-dropping
    filter, so it never silent-zeros on either shape.

    Returns one of: 'prompt', 'model', 'tool_call', 'tool_result',
    'compaction', or '' (skip / plumbing).
    """
    et = (e.get("event_type") or "").lower()
    if et in _PLUMBING_TYPES:
        return ""
    if "compact" in et:
        return "compaction"
    d = _data(e)
    role = (d.get("role") or "").lower()

    # Tool plumbing first (a tool_call row may also have role=assistant).
    if "tool_result" in et or "tool_use_result" in et or role == "tool":
        return "tool_result"
    if "tool_call" in et or "tool.call" in et or d.get("tool_name") or d.get("tool_calls"):
        return "tool_call"

    # Prompt / user boundary. (``et.endswith("user")`` already covers an
    # exact ``"user"`` as well as v3-adjacent ``*user`` spellings; the v3
    # name ``prompt.submitted`` is matched first, so this never silent-zeros.)
    if "prompt.submitted" in et or et.endswith("user") \
            or (role == "user" and et in ("message", "text")):
        return "prompt"

    # Model call / assistant reply.
    if "model.completed" in et or "assistant" in et \
            or (role == "assistant" and et in ("message", "text")):
        return "model"

    if et == "thinking":
        return "model"
    return ""


def _tool_name(e):
    d = _data(e)
    name = d.get("tool_name")
    if name:
        return str(name).replace("mcp__openclaw__", "")
    tcs = d.get("tool_calls")
    if isinstance(tcs, list) and tcs and isinstance(tcs[0], dict):
        n = tcs[0].get("name") or (tcs[0].get("function") or {}).get("name")
        if n:
            return str(n).replace("mcp__openclaw__", "")
    return "tool"


def _tool_use_ids(e):
    """tool_use ids this event opens (a tool_call) — for start→end matching."""
    d = _data(e)
    ids = []
    tcs = d.get("tool_calls")
    if isinstance(tcs, list):
        for tc in tcs:
            if isinstance(tc, dict) and tc.get("id"):
                ids.append(str(tc["id"]))
    return ids


def _tool_result_id(e):
    """tool_use id this tool_result closes (the join key)."""
    d = _data(e)
    ex = d.get("extra") if isinstance(d.get("extra"), dict) else {}
    return ex.get("toolUseId") or ex.get("tool_use_id") or d.get("tool_use_id")


def _is_error(e):
    d = _data(e)
    ex = d.get("extra") if isinstance(d.get("extra"), dict) else {}
    return bool(ex.get("isError") or d.get("isError") or d.get("is_error")
                or (e.get("event_type") or "").endswith("error"))


def _prompt_text(e):
    d = _data(e)
    for k in ("finalPromptText", "content"):
        v = d.get(k)
        if isinstance(v, str) and v.strip():
            return v
    msg = d.get("message")
    if isinstance(msg, dict) and isinstance(msg.get("content"), str):
        return msg["content"]
    return ""


def _build_turns(rows):
    """Decompose a session's events into ordered turns of waterfall spans.

    A turn starts at each ``prompt`` boundary (the first turn also absorbs any
    pre-prompt events). Within a turn we emit spans in wall-clock order:
    prompt → model call(s) → each tool (start at its tool_call, end at the
    matching tool_result) → compaction → reply. Each span's ``ended_ms`` is the
    next event's ts (so a bar's width is the wall-clock gap until the next
    activity); a tool span instead ends at its matched result.
    """
    evs = sorted(
        (e for e in rows if _classify(e)),
        key=lambda e: _ts_ms(e.get("ts")) or 0,
    )
    if not evs:
        return []
    start_ms = [(_ts_ms(e.get("ts")) or 0) for e in evs]

    # Partition into turns on each prompt boundary.
    turns = []
    cur = None
    for i, e in enumerate(evs):
        kind = _classify(e)
        if kind == "prompt" or cur is None:
            if kind == "prompt" or not turns:
                cur = {"events": [], "idx": []}
                turns.append(cur)
        cur["events"].append(e)
        cur["idx"].append(i)

    out = []
    for tn, turn in enumerate(turns):
        spans = []
        tool_open = {}  # tool_use_id -> span (awaiting its result)
        t_starts = [start_ms[i] for i in turn["idx"]]
        turn_start = min(t_starts) if t_starts else None
        turn_end = max(t_starts) if t_starts else None
        n = len(turn["events"])
        for j, e in enumerate(turn["events"]):
            gi = turn["idx"][j]
            kind = _classify(e)
            s_ms = start_ms[gi]
            # Default end = next event's start within the WHOLE session.
            nxt = start_ms[gi + 1] if gi + 1 < len(start_ms) else s_ms
            tokens = int(e.get("token_count") or 0)
            model = e.get("model") or _data(e).get("model") or ""

            if kind == "tool_result":
                # Close the matching open tool span; this row is not its own span.
                rid = _tool_result_id(e)
                sp = tool_open.pop(rid, None) if rid else None
                if sp is not None:
                    sp["ended_ms"] = s_ms
                    sp["duration_ms"] = max(0, s_ms - sp["started_ms"])
                    if _is_error(e):
                        sp["status"] = "error"
                else:
                    # Orphan result (no matching open tool_call captured) — show
                    # it as a zero-width tool span so nothing is silently lost.
                    spans.append({
                        "kind": "tool", "label": _tool_name(e) + " result",
                        "started_ms": s_ms, "ended_ms": s_ms, "duration_ms": 0,
                        "status": "error" if _is_error(e) else "ok",
                    })
                continue

            if kind == "tool_call":
                sp = {
                    "kind": "tool", "label": _tool_name(e),
                    "started_ms": s_ms, "ended_ms": nxt,
                    "duration_ms": max(0, nxt - s_ms),
                    "tokens": tokens or None,
                    "status": "error" if _is_error(e) else "ok",
                }
                spans.append(sp)
                # Register every tool_use id this call opened so its result closes it.
                for tuid in _tool_use_ids(e):
                    tool_open[tuid] = sp
                continue

            if kind == "compaction":
                spans.append({
                    "kind": "compaction", "label": "context compaction",
                    "started_ms": s_ms, "ended_ms": nxt,
                    "duration_ms": max(0, nxt - s_ms), "status": "ok",
                })
                continue

            if kind == "prompt":
                txt = _prompt_text(e)
                spans.append({
                    "kind": "prompt",
                    "label": (txt[:80] or "prompt").replace("\n", " "),
                    "started_ms": s_ms, "ended_ms": nxt,
                    "duration_ms": max(0, nxt - s_ms), "status": "ok",
                })
                continue

            # model: the last model event of the turn is the reply.
            is_last = (j == n - 1)
            spans.append({
                "kind": "reply" if is_last else "model",
                "label": ("reply" if is_last else "model call")
                         + (" " + model if model else ""),
                "started_ms": s_ms, "ended_ms": nxt,
                "duration_ms": max(0, nxt - s_ms),
                "tokens": tokens or None, "model": model or None,
                "status": "error" if _is_error(e) else "ok",
            })

        # Any tool still open at turn end never got a result → leave it ending
        # at the turn boundary (best-effort) so its bar is still drawn.
        for sp in tool_open.values():
            if sp.get("ended_ms") in (None, sp["started_ms"]) and turn_end:
                sp["ended_ms"] = turn_end
                sp["duration_ms"] = max(0, turn_end - sp["started_ms"])

        prompt_label = next(
            (s["label"] for s in spans if s["kind"] == "prompt"), "")
        tool_count = sum(1 for s in spans if s["kind"] == "tool")
        total_tokens = sum(int(s.get("tokens") or 0) for s in spans)
        has_error = any(s.get("status") == "error" for s in spans)
        out.append({
            "turn": tn + 1,
            "started_ms": turn_start,
            "ended_ms": turn_end,
            "duration_ms": (turn_end - turn_start) if (turn_start and turn_end) else 0,
            "prompt": prompt_label,
            "tool_count": tool_count,
            "total_tokens": total_tokens,
            "span_count": len(spans),
            "status": "error" if has_error else "ok",
            "spans": spans,
        })
    return out


@bp_turn_anatomy.route("/api/turn-anatomy")
def api_turn_anatomy():
    """Per-turn anatomy for one session.

    Query: ``session_id`` (required). Returns ``{session_id, turns, _source}``
    where each turn carries ordered ``spans``. Never 500s — a missing session
    or unreadable store returns an empty ``turns`` list (HTTP 200).
    """
    session_id = (request.args.get("session_id") or "").strip()
    if not session_id:
        return jsonify({"error": "session_id required", "turns": []}), 400
    try:
        limit = max(1, min(20000, int(request.args.get("limit", 14000))))
    except (TypeError, ValueError):
        limit = 14000

    rows = _events_for(session_id=session_id, limit=limit)
    if rows is None:
        return jsonify({"available": False, "session_id": session_id, "turns": []})

    turns = _build_turns(rows)
    return jsonify({
        "available": True,
        "session_id": session_id,
        "turns": turns,
        "turn_count": len(turns),
        "_source": "local_store",
    })


@bp_turn_anatomy.route("/api/turn-anatomy/stalled")
def api_turn_anatomy_stalled():
    """Sessions whose most recent turn is stalled / long-running.

    A session is stalled when its latest event is older than ``min`` minutes
    (default 5) but the latest turn never reached a terminal reply — i.e. the
    agent appears stuck mid-turn. Scans a bounded recent window of events.
    Returns ``{stalled:[...], threshold_min, _source}``; never 500s.
    """
    try:
        stall_min = max(1, min(1440, int(request.args.get("min", _DEFAULT_STALL_MIN))))
    except (TypeError, ValueError):
        stall_min = _DEFAULT_STALL_MIN
    threshold_ms = stall_min * 60 * 1000
    now = _now_ms()

    rows = _events_for(limit=6000)
    if rows is None:
        return jsonify({"available": False, "stalled": [], "threshold_min": stall_min})

    by_sid = {}
    for e in rows:
        sid = (e.get("session_id") or "").strip()
        if not sid:
            continue
        by_sid.setdefault(sid, []).append(e)

    stalled = []
    for sid, evs in by_sid.items():
        kinds = [(k, _ts_ms(e.get("ts"))) for e in evs for k in (_classify(e),) if k]
        if not kinds:
            continue
        last_ms = max((ms for _, ms in kinds if ms), default=None)
        if last_ms is None:
            continue
        idle_ms = now - last_ms
        if idle_ms < threshold_ms:
            continue
        # Terminal if the latest classified event is a reply/model with no
        # tool still pending. We approximate "running" as: the last event in
        # the turn is a prompt or an unresolved tool_call (waiting).
        kinds_only = [k for k, _ in sorted(
            ((k, ms or 0) for k, ms in kinds), key=lambda x: x[1])]
        last_kind = kinds_only[-1] if kinds_only else ""
        # Count tool_call vs tool_result to detect an unresolved tool.
        opened = sum(1 for k in kinds_only if k == "tool_call")
        closed = sum(1 for k in kinds_only if k == "tool_result")
        pending_tool = opened > closed
        running = last_kind in ("prompt", "tool_call", "model") or pending_tool
        if not running:
            continue
        stalled.append({
            "session_id": sid,
            "last_event_ms": last_ms,
            "idle_ms": idle_ms,
            "idle_min": round(idle_ms / 60000, 1),
            "last_kind": last_kind,
            "pending_tool": pending_tool,
            "event_count": len(evs),
        })

    stalled.sort(key=lambda s: s["idle_ms"], reverse=True)
    return jsonify({
        "available": True,
        "stalled": stalled,
        "threshold_min": stall_min,
        "_source": "local_store",
    })
