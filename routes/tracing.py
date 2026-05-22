"""
routes/tracing.py — Phoenix/Arize-style tracing endpoints.

A *trace* is one OpenClaw session; each event in that session becomes a
*span*. Spans are linked into a tree via ``data.parentId`` and laid out on a
wall-clock timeline (waterfall) by their ``ts``. Sub-agent events
(``subagent:*``) form the agent graph.

Events-first by design: this reads the OpenClaw events ClawMetry already
ingests, so it works without any OTLP exporter. OTel spans (the /v1/traces
``spans`` table) are merged in when present.

Endpoints (bp_tracing):
  GET /api/traces            — list of traces (sessions) with summary
  GET /api/trace/<id>        — one trace: span tree + waterfall + agent graph

DuckDB-first: reads go through the daemon proxy (``local_store_via_daemon``)
with a single-process read-only fallback, mirroring routes.sessions.
"""

import json
from datetime import datetime

from flask import Blueprint, jsonify, request

from clawmetry.config import is_local_store_read_enabled, hide_clawmetry_session

bp_tracing = Blueprint('tracing', __name__)


# Event types that are pure plumbing — never their own span in the trace view.
_TRACE_PLUMBING_TYPES = frozenset({
    "session.started", "session.ended", "session.created",
    "model.changed", "thinking_level_change", "context.compiled",
    "agent.heartbeat", "queue-operation", "custom", "custom_message",
})


def _events_for(session_id=None, limit=12000):
    """Read events via the daemon proxy, RO-fallback for single-process boots."""
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
    if rows is None and is_local_store_read_enabled():
        try:
            from clawmetry import local_store
            store = local_store.get_store(read_only=True)
            rows = (store.query_events(session_id=session_id, limit=limit)
                    if session_id else store.query_events(limit=limit))
        except Exception:
            rows = None
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


def _span_kind(event_type, is_subagent):
    et = (event_type or "").lower()
    if "prompt.submitted" in et or et.endswith("user") or et == "user":
        return "prompt"
    if "model.completed" in et or "assistant" in et:
        return "llm"
    if "tool" in et:
        return "tool"
    if "attachment" in et:
        return "attachment"
    return "event"


def _walk_tool_uses(node):
    """Yield tool_use dicts nested anywhere in ``node`` (depth-first)."""
    if isinstance(node, dict):
        if node.get("type") == "tool_use" and node.get("name"):
            yield node
        for v in node.values():
            yield from _walk_tool_uses(v)
    elif isinstance(node, list):
        for item in node:
            yield from _walk_tool_uses(item)


def _short_name(event_type, data, is_subagent):
    """Human-readable span name."""
    kind = _span_kind(event_type, is_subagent)
    prefix = "subagent " if is_subagent else ""
    if kind == "prompt":
        return prefix + "prompt"
    if kind == "llm":
        # surface the first tool call name if this assistant turn made one
        tus = list(_walk_tool_uses(data))
        if tus:
            names = [t.get("name", "").replace("mcp__openclaw__", "")
                     for t in tus if t.get("name")]
            if names:
                return prefix + "llm → " + ", ".join(names[:3])
        return prefix + "llm"
    if kind == "tool":
        return prefix + "tool result"
    return prefix + (event_type or "event")


def _summarize_trace(session_id, rows):
    """Roll up one session's events into a trace summary row."""
    starts, total_tokens, total_cost, errors, model = [], 0, 0.0, 0, None
    span_count = 0
    has_subagents = False
    for e in rows:
        et = (e.get("event_type") or "")
        if et in _TRACE_PLUMBING_TYPES:
            continue
        span_count += 1
        if et.startswith("subagent:"):
            has_subagents = True
        ms = _ts_ms(e.get("ts"))
        if ms:
            starts.append(ms)
        total_tokens += int(e.get("token_count") or 0)
        try:
            total_cost += float(e.get("cost_usd") or 0.0)
        except (TypeError, ValueError):
            pass
        if not model and e.get("model"):
            model = e.get("model")
        d = e.get("data") if isinstance(e.get("data"), dict) else {}
        if d.get("isError") or d.get("is_error") or (et or "").endswith("error"):
            errors += 1
    start_ms = min(starts) if starts else None
    end_ms = max(starts) if starts else None
    duration_ms = (end_ms - start_ms) if (start_ms and end_ms) else 0
    return {
        "trace_id": session_id,
        "name": session_id[:40],
        "start_ms": start_ms,
        "duration_ms": duration_ms,
        "span_count": span_count,
        "model": model,
        "total_tokens": total_tokens,
        "total_cost_usd": round(total_cost, 6),
        "error_count": errors,
        "has_subagents": has_subagents,
        "status": "error" if errors else "ok",
    }


@bp_tracing.route("/api/traces")
def api_traces():
    """List traces (one per session), most-recent first.

    DuckDB-first; ClawMetry's own helper sessions are hidden (plumbing).
    Returns ``available:false`` (HTTP 200) when the store can't be read.
    """
    try:
        limit = min(int(request.args.get("limit", 100)), 500)
    except (ValueError, TypeError):
        limit = 100

    rows = _events_for(limit=14000)
    if rows is None:
        return jsonify({"available": False, "traces": [], "total": 0})

    by_sid = {}
    for e in rows:
        sid = (e.get("session_id") or "").strip()
        if not sid or hide_clawmetry_session(sid):
            continue
        by_sid.setdefault(sid, []).append(e)

    traces = [_summarize_trace(sid, evs) for sid, evs in by_sid.items()]
    traces = [t for t in traces if t["span_count"] > 0]
    traces.sort(key=lambda t: (t.get("start_ms") or 0), reverse=True)
    return jsonify({
        "available": True,
        "traces": traces[:limit],
        "total": len(traces),
    })


def _build_spans(rows):
    """Turn a session's events into span dicts + a parent→child tree.

    Returns (spans_list, root_ids). Each span:
      {span_id, parent_span_id, name, kind, start_ms, duration_ms,
       model, tokens, cost, status, is_subagent, detail}
    Durations are wall-clock gaps to the next event (event-based tracing),
    which gives a usable waterfall without explicit span end markers.
    """
    # Sort ascending by ts so gap-based durations are forward-looking.
    evs = sorted(
        (e for e in rows if (e.get("event_type") or "") not in _TRACE_PLUMBING_TYPES),
        key=lambda e: _ts_ms(e.get("ts")) or 0,
    )
    spans = []
    order_ms = [(_ts_ms(e.get("ts")) or 0) for e in evs]
    trace_end = max(order_ms) if order_ms else 0
    for i, e in enumerate(evs):
        d = e.get("data") if isinstance(e.get("data"), dict) else {}
        et = e.get("event_type") or ""
        is_sub = et.startswith("subagent:")
        sid = d.get("id") or e.get("id") or f"span-{i}"
        parent = d.get("parentId") or d.get("parentUuid")
        start = order_ms[i]
        # gap to next event = nominal duration; floor for visibility, cap at trace end
        nxt = order_ms[i + 1] if i + 1 < len(order_ms) else trace_end
        dur = max(0, (nxt - start)) if nxt and start else 0
        detail = ""
        msg = d.get("message")
        if isinstance(msg, dict):
            c = msg.get("content")
            if isinstance(c, str):
                detail = c[:240]
        spans.append({
            "span_id": str(sid),
            "parent_span_id": str(parent) if parent else None,
            "name": _short_name(et, d, is_sub),
            "kind": _span_kind(et, is_sub),
            "event_type": et,
            "start_ms": start,
            "duration_ms": dur,
            "model": e.get("model") or "",
            "tokens": int(e.get("token_count") or 0),
            "cost": round(float(e.get("cost_usd") or 0.0), 6),
            "status": "error" if (d.get("isError") or d.get("is_error")) else "ok",
            "is_subagent": is_sub,
            "detail": detail,
        })
    # Only keep parent links that resolve to a span in this trace.
    ids = {s["span_id"] for s in spans}
    roots = []
    for s in spans:
        if not s["parent_span_id"] or s["parent_span_id"] not in ids:
            s["parent_span_id"] = None
            roots.append(s["span_id"])
    return spans, roots


def _build_agent_graph(spans):
    """Nodes = main agent + each sub-agent; edges = main → sub-agent.

    Sub-agent spans are grouped into a single 'sub-agents' lane node when we
    can't tell them apart, otherwise per distinct sub-agent run.
    """
    main_spans = [s for s in spans if not s["is_subagent"]]
    sub_spans = [s for s in spans if s["is_subagent"]]
    nodes = [{
        "id": "main",
        "label": "main agent",
        "span_count": len(main_spans),
        "tokens": sum(s["tokens"] for s in main_spans),
        "cost": round(sum(s["cost"] for s in main_spans), 6),
        "kind": "main",
    }]
    edges = []
    if sub_spans:
        nodes.append({
            "id": "subagents",
            "label": "sub-agents",
            "span_count": len(sub_spans),
            "tokens": sum(s["tokens"] for s in sub_spans),
            "cost": round(sum(s["cost"] for s in sub_spans), 6),
            "kind": "subagent",
        })
        edges.append({"from": "main", "to": "subagents"})
    return {"nodes": nodes, "edges": edges}


@bp_tracing.route("/api/trace/<session_id>")
def api_trace(session_id):
    """One trace: ordered spans (for the waterfall + tree) + agent graph.

    DuckDB-first. Returns ``available:false`` (HTTP 200) when unreadable, and
    404 when the session has no events.
    """
    if hide_clawmetry_session(session_id) and \
            request.args.get("include_internal") != "1":
        return jsonify({"available": True, "trace_id": session_id,
                        "spans": [], "agent_graph": {"nodes": [], "edges": []},
                        "internal": True})

    rows = _events_for(session_id=session_id, limit=14000)
    if rows is None:
        return jsonify({"available": False, "spans": []})
    if not rows:
        return jsonify({"error": "Trace not found", "spans": []}), 404

    spans, roots = _build_spans(rows)
    summary = _summarize_trace(session_id, rows)
    agent_graph = _build_agent_graph(spans)
    return jsonify({
        "available": True,
        "trace_id": session_id,
        "summary": summary,
        "spans": spans,
        "root_span_ids": roots,
        "agent_graph": agent_graph,
    })
