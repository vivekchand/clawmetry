"""
routes/tracing.py — Phoenix/Arize-style tracing endpoints.

A *trace* is one OpenClaw session; each event in that session becomes a
*span*. Spans form a semantic tree (main-agent turns are roots; a sub-agent
burst nests under the turn that ran it) and are laid out on a wall-clock
timeline (waterfall) by their ``ts``. Sub-agent events
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


def _event_cost(e):
    """Best-effort USD cost for one event, derived when the stored value is 0/None.

    Multi-runtime adapters (Claude Code, Codex, …) pre-set ``token_count`` (the
    lumped total) and stash the input/output/cache split under ``data.extra`` —
    a shape the #2049 ingest derivation skipped, so these events land with
    ``cost_usd`` NULL and the Cost column reads ``$0`` for sessions that clearly
    cost money. Derive it here (read-side) from the split × model pricing,
    cache-aware, with the provider inferred from the model. Honour an explicit
    stored cost first so OpenClaw's already-priced events are never re-derived.
    """
    try:
        c = e.get("cost_usd")
        if c:
            return float(c)
    except (TypeError, ValueError):
        pass
    d = e.get("data") if isinstance(e.get("data"), dict) else {}
    model = e.get("model") or d.get("model") or ""
    if not model:
        return 0.0
    ex = d.get("extra") if isinstance(d.get("extra"), dict) else {}
    u = d.get("usage") if isinstance(d.get("usage"), dict) else {}

    def _pick(*keys):
        for src in (ex, u):
            if not isinstance(src, dict):
                continue
            for k in keys:
                v = src.get(k)
                if v:
                    try:
                        return int(v)
                    except (TypeError, ValueError):
                        return 0
        return 0

    ti = _pick("inputTokens", "input_tokens")
    to = _pick("outputTokens", "output_tokens")
    cr = _pick("cacheReadInputTokens", "cache_read_input_tokens")
    cw = _pick("cacheCreationInputTokens", "cache_creation_input_tokens")
    if not (ti or to or cr or cw):
        return 0.0
    try:
        from clawmetry.providers_pricing import estimate_event_cost_usd
        return float(estimate_event_cost_usd(
            str(model), input_tokens=ti, output_tokens=to,
            cache_read_tokens=cr, cache_write_tokens=cw) or 0.0)
    except Exception:
        return 0.0


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
    # Classify span kind from BOTH v3 (prompt.submitted/model.completed) and
    # legacy (user/assistant) event-type names. This is a both-shapes display
    # classifier, not a row-dropping filter, so it never silent-zeros on v3.
    if "prompt.submitted" in et or et.endswith("user") or et == "user":  # v3-shape-gate: allow (reason: span-kind classifier matches both v3 prompt.submitted and legacy user)
        return "prompt"
    if "model.completed" in et or "assistant" in et:  # v3-shape-gate: allow (reason: span-kind classifier matches both v3 model.completed and legacy assistant)
        return "llm"
    if "tool" in et:
        return "tool"
    if "attachment" in et:
        return "attachment"
    return "event"


def _walk_tool_uses(node, _parent_name=None):
    """Yield tool_use-like dicts nested anywhere in ``node`` (depth-first).

    Recognises two shapes:
      * **OpenClaw / Anthropic** — ``{type: 'tool_use', name, id, input}``
      * **Claude Code** — top-level ``data.tool_calls = [{id, input}]`` with
        the tool name on the parent at ``data.tool_name``. The yielded dict
        is normalised to ``{type:'tool_use', name, id, input}`` so callers
        don't need to know which shape produced it.
    """
    if isinstance(node, dict):
        if node.get("type") == "tool_use" and node.get("name"):
            yield node
        # Claude Code shape: data.tool_calls = [...] with name at data.tool_name
        tn = node.get("tool_name")
        tcs = node.get("tool_calls")
        if isinstance(tcs, list) and tn:
            for tc in tcs:
                if isinstance(tc, dict):
                    yield {
                        "type": "tool_use",
                        "name": tn,
                        "id": tc.get("id") or tc.get("tool_call_id") or "",
                        "input": tc.get("input") or tc.get("arguments") or {},
                    }
        for k, v in node.items():
            if k == "tool_calls":
                continue  # already handled above
            yield from _walk_tool_uses(v, _parent_name=node.get("tool_name") or _parent_name)
    elif isinstance(node, list):
        for item in node:
            yield from _walk_tool_uses(item, _parent_name=_parent_name)


def _walk_tool_results(node):
    """Yield (tool_use_id, is_error) for tool_result blocks anywhere in ``node``.

    Recognises:
      * **OpenClaw / Anthropic** — ``{type: 'tool_result', tool_use_id, is_error}``
      * **Claude Code** — the link lives in ``data.extra`` (a JSON-encoded
        string) as ``{toolUseId, isError}``.

    The join key for span reconstruction: an assistant tool_use.id is closed by
    the later user event whose tool_result.tool_use_id matches it.
    """
    if isinstance(node, dict):
        if node.get("type") == "tool_result" and node.get("tool_use_id"):
            yield node.get("tool_use_id"), bool(node.get("is_error"))
        # Claude Code shape: tool_result event with linkage in data.extra.
        extra = node.get("extra")
        if isinstance(extra, str) and extra:
            try:
                ex = json.loads(extra)
            except (ValueError, TypeError):
                ex = None
            if isinstance(ex, dict):
                tuid = ex.get("toolUseId") or ex.get("tool_use_id") or ex.get("tool_call_id")
                if tuid:
                    yield tuid, bool(ex.get("isError") or ex.get("is_error"))
        elif isinstance(extra, dict):
            tuid = extra.get("toolUseId") or extra.get("tool_use_id") or extra.get("tool_call_id")
            if tuid:
                yield tuid, bool(extra.get("isError") or extra.get("is_error"))
        for v in node.values():
            yield from _walk_tool_results(v)
    elif isinstance(node, list):
        for item in node:
            yield from _walk_tool_results(item)


def _tool_label(name):
    return (name or "tool").replace("mcp__openclaw__", "")


def _short_input(inp):
    """One-line summary of a tool_use input dict for the span detail/name."""
    if not isinstance(inp, dict):
        return ""
    for k in ("file_path", "path", "command", "query", "url", "pattern", "name"):
        v = inp.get(k)
        if isinstance(v, str) and v:
            return f"{k}={v[:140]}"
    try:
        return json.dumps(inp)[:160]
    except Exception:
        return ""


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


def _derive_trace_title(rows):
    """Best-effort first-user-prompt → trace title (MLflow-style header).

    Reuses the bug-class-gated probe from clawmetry.eval_regression_replay so
    we honour the same v3 event-shape coverage. Returns "" on no match; the
    frontend falls back to the trace id when title is empty. Cheap: walks
    ``rows`` once, stops at the first non-empty prompt text.
    """
    try:
        from clawmetry.eval_regression_replay import _extract_first_prompt
        txt = _extract_first_prompt(rows or []) or ""
    except Exception:
        txt = ""
    # Collapse whitespace + cap at 120 chars so it renders on one line.
    txt = " ".join((txt or "").split())
    return txt[:120] + ("…" if len(txt) > 120 else "")


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
        total_cost += _event_cost(e)
        if not model and e.get("model"):
            model = e.get("model")
        d = e.get("data") if isinstance(e.get("data"), dict) else {}
        if d.get("isError") or d.get("is_error") or (et or "").endswith("error"):
            errors += 1
    start_ms = min(starts) if starts else None
    end_ms = max(starts) if starts else None
    duration_ms = (end_ms - start_ms) if (start_ms and end_ms) else 0
    title = _derive_trace_title(rows)
    return {
        "trace_id": session_id,
        "name": session_id[:40],
        # First-user-prompt title for the MLflow-style trace header.
        # Empty string when no prompt is recoverable; the UI falls back
        # to the trace id in that case.
        "title": title,
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

    # Scan a bounded window of recent events to group into the trace list.
    # 14000 was needlessly heavy on the shared DuckDB connection (it's the
    # main contributor to proxy-timeout empties); 6000 still covers far more
    # than the ``limit`` traces we return, most-recent first.
    rows = _events_for(limit=6000)
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
    """Reconstruct a semantic OTel-style span tree from session events.

    Produces ``invoke_agent → chat → execute_tool`` nesting (PRD-tracing.md §5)
    using the tool_use.id ↔ tool_result.tool_use_id join, NOT the data.parentId
    conversation chain (which staircases 1399-deep). Sub-agent activity nests
    under its own ``invoke_agent`` span. Cost/tokens/duration roll up
    child→parent (``rolled_*`` fields on parents).

    Each span: {span_id, parent_span_id, name, kind, event_type, start_ms,
    duration_ms, model, tokens, cost, status, is_subagent, detail, tool,
    rolled_tokens?, rolled_cost?}. Returns (spans_list, root_ids).
    """
    evs = sorted(
        (e for e in rows if (e.get("event_type") or "") not in _TRACE_PLUMBING_TYPES),
        key=lambda e: _ts_ms(e.get("ts")) or 0,
    )
    if not evs:
        return [], []
    order_ms = [(_ts_ms(e.get("ts")) or 0) for e in evs]
    t0, t1 = order_ms[0], order_ms[-1]
    spans = []
    by_id = {}
    seen = set()

    def _mk(span_id, parent, name, kind, start, end, *, is_sub=False, model="",
            tokens=0, cost=0.0, status="ok", detail="", tool="", event_type=""):
        sid = str(span_id)
        while sid in seen:
            sid += "_"
        seen.add(sid)
        s = {
            "span_id": sid, "parent_span_id": (str(parent) if parent else None),
            "name": name, "kind": kind, "event_type": event_type,
            "start_ms": start, "duration_ms": max(0, (end or start) - start),
            "model": model, "tokens": int(tokens or 0),
            "cost": round(float(cost or 0.0), 6), "status": status,
            # `detail` carries the primary text for the MLflow-style Chat
            # tab. Bumped from 240 → 8000 because the old cap reduced
            # multi-paragraph assistant turns and tool inputs to single
            # truncated sentences in the UI. `output` is filled in when
            # the matching tool_result closes the span (below) so the
            # Outputs tab has content without a second round-trip.
            "is_subagent": is_sub, "detail": (detail or "")[:8000], "tool": tool,
            "output": "",
        }
        spans.append(s)
        by_id[sid] = s
        return s

    # Agent root spans: main always; sub-agent created lazily on first subagent event.
    main_root = _mk("agent-main", None, "invoke_agent main", "agent", t0, t1)
    sub_root = None
    tool_spans = {}  # tool_use_id -> execute_tool span (closed on its result)

    for i, e in enumerate(evs):
        d = e.get("data") if isinstance(e.get("data"), dict) else {}
        et = e.get("event_type") or ""
        low = et.lower()
        is_sub = low.startswith("subagent:")
        start = order_ms[i]
        nxt = order_ms[i + 1] if i + 1 < len(order_ms) else t1
        eid = str(d.get("id") or e.get("id") or f"ev-{i}")
        # Extract the human-readable text for this event across every shape
        # we see in the wild. The old code only checked `data.message.content`
        # (OpenClaw v3 assistant) + `data.finalPromptText` (OpenClaw prompt) —
        # which meant Claude Code events (`data.content` directly, no
        # `message` wrapper) ended up with empty `detail` and the MLflow-
        # style Chat tab had nothing to render.
        text = ""
        msg = d.get("message")
        if isinstance(msg, dict) and isinstance(msg.get("content"), str):
            text = msg["content"]
        elif isinstance(msg, dict) and isinstance(msg.get("content"), list):
            # Anthropic SDK content list: [{type:'text',text:'…'}, …]
            parts = [b.get("text", "") for b in msg["content"] if isinstance(b, dict)]
            text = "\n".join(p for p in parts if p)
        elif isinstance(d.get("finalPromptText"), str):
            text = d["finalPromptText"]
        elif isinstance(d.get("promptText"), str):
            text = d["promptText"]
        elif isinstance(d.get("content"), str):
            # Claude Code shape: `data.content` is the message body directly
            # (no `message` wrapper). Without this the user prompt is empty
            # and falls through to a generic `message` span instead of a
            # `prompt` span.
            text = d["content"]
        elif isinstance(d.get("content"), list):
            parts = [b.get("text", "") for b in d["content"] if isinstance(b, dict)]
            text = "\n".join(p for p in parts if p)
        elif isinstance(d.get("text"), str):
            text = d["text"]

        if is_sub and sub_root is None:
            sub_root = _mk("agent-sub", main_root["span_id"],
                           "invoke_agent sub-agent", "agent", start, t1, is_sub=True)
        agent_parent = (sub_root or main_root)["span_id"] if is_sub else main_root["span_id"]

        # Multi-runtime adapters (Claude Code, Codex, …) emit event_type
        # `message` for BOTH turns and carry the speaker in `data.role` — so
        # classify on the role too. Gated to text turns so a `tool_call` row
        # (also role=assistant) takes the explicit `tool_call → assistant`
        # branch below instead of being misclassified by the role-only check.
        d_role = (d.get("role") or "").lower()
        is_assistant = ("assistant" in low) or ("model.completed" in low) \
            or (d_role == "assistant" and low in ("message", "text"))
        is_user = (low.endswith("user") or low == "user" or "prompt" in low
                   or (d_role == "user" and low == "message"))
        # tool_call is an assistant turn (the assistant invokes the tool):
        # route it through the chat+execute_tool branch so _walk_tool_uses
        # discovers its tool_calls and emits the matching tool spans.
        if low == "tool_call":
            is_assistant = True

        # Close execute_tool spans whose result just arrived (the join). When
        # we have a tool_result event, also attach its text to the tool span
        # as `output` so the Outputs tab in the MLflow-style detail pane has
        # content without a second BLOB round-trip.
        results = list(_walk_tool_results(d))
        if results or low == "tool_result":
            tool_result_text = ""
            if isinstance(d.get("content"), str):
                tool_result_text = d["content"]
            elif text:
                tool_result_text = text
            for tuid, is_err in results:
                ts = tool_spans.get(tuid)
                if ts is not None:
                    ts["duration_ms"] = max(0, start - ts["start_ms"])
                    if is_err:
                        ts["status"] = "error"
                    if tool_result_text and not ts.get("output"):
                        ts["output"] = tool_result_text[:8000]
            if is_user and not text.strip():
                continue  # pure tool-result turn → no span of its own
            if low == "tool_result":
                # Claude Code tool_result with no embedded tool_use_id link:
                # we already updated the most-recent tool span above when the
                # results walker yielded ids; if none did, skip emitting a
                # generic event-span for this row (its content is on the tool).
                continue

        if is_assistant:
            chat = _mk(eid, agent_parent,
                       ("chat " + (e.get("model") or "")).strip() or "chat",
                       "llm", start, nxt, is_sub=is_sub, model=e.get("model") or "",
                       tokens=e.get("token_count"), cost=_event_cost(e),
                       status="error" if (d.get("isError") or d.get("is_error")) else "ok",
                       detail=text, event_type=et)
            for j, tu in enumerate(_walk_tool_uses(d)):
                tuid = tu.get("id") or f"{eid}-tu-{j}"
                tname = _tool_label(tu.get("name"))
                ts = _mk(tuid, chat["span_id"], "execute_tool " + tname, "tool",
                         start, nxt, is_sub=is_sub, tool=tname,
                         detail=_short_input(tu.get("input")), event_type=et)
                tool_spans[tu.get("id") or tuid] = ts
            continue

        if is_user and text.strip():
            _mk(eid, agent_parent, "prompt", "prompt", start, nxt, is_sub=is_sub,
                detail=text, event_type=et)
            continue

        # Fallback: any other renderable event as a child of its agent root.
        _mk(eid, agent_parent, (et or "event"), _span_kind(et, is_sub), start, nxt,
            is_sub=is_sub, model=e.get("model") or "", tokens=e.get("token_count"),
            cost=_event_cost(e), detail=text, event_type=et)

    # Roll cost/tokens/duration child→parent; propagate error to agent parents.
    children = {}
    for s in spans:
        if s["parent_span_id"]:
            children.setdefault(s["parent_span_id"], []).append(s["span_id"])

    def _rollup(sid):
        s = by_id[sid]
        tok, cost = s["tokens"], s["cost"]
        end = s["start_ms"] + s["duration_ms"]
        err = s["status"] == "error"
        for c in children.get(sid, []):
            ct, cc, ce, cerr = _rollup(c)
            tok += ct; cost += cc; end = max(end, ce); err = err or cerr
        if children.get(sid):
            s["rolled_tokens"] = tok
            s["rolled_cost"] = round(cost, 6)
            if end > s["start_ms"] + s["duration_ms"]:
                s["duration_ms"] = end - s["start_ms"]
            if err and s["kind"] == "agent":
                s["status"] = "error"
        return tok, cost, end, err

    roots = [s["span_id"] for s in spans if not s["parent_span_id"]]
    for r in roots:
        _rollup(r)
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
