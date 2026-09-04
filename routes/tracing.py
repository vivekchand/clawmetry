"""
routes/tracing.py — Phoenix/Arize-style tracing endpoints.

A *trace* is one OpenClaw session; each event in that session becomes a
*span*. Spans form a semantic tree (main-agent turns are roots; a sub-agent
burst nests under the turn that ran it) and are laid out on a wall-clock
timeline (waterfall) by their ``ts``. Sub-agent events
(``subagent:*``) form the agent graph.

Events-first by design: this reads the OpenClaw events ClawMetry already
ingests, so it works without any OTLP exporter. OTel spans (the /v1/traces
``spans`` table) are a SECOND source, not a merge: a trace id that has no
events is served from the spans table (``_span_traces`` /
``_build_spans_from_store``), and a trace that has events is built from the
events alone. Spans an OTLP exporter pushed for the SAME session are not
folded into the events-derived tree.

Reasoning is first-class: every thinking block / ``thinking`` event becomes a
``reasoning`` span ("think"), and the ``execute_tool`` spans it drove nest
under it (see ``_build_spans``). When the raw events carry no thinking, the
``replay_events`` table (kind ``thinking``, written by adapters'
``iter_replay_events``) is read as a fallback.

Endpoints (bp_tracing):
  GET /api/traces            — list of traces (sessions) with summary
  GET /api/trace/<id>        — one trace: span tree + waterfall + agent graph

DuckDB-first: reads go through the daemon proxy (``local_store_via_daemon``)
with a single-process read-only fallback, mirroring routes.sessions.
"""

import json
from datetime import datetime

from flask import Blueprint, jsonify, request
from clawmetry import event_shape as _event_shape

from clawmetry.config import is_local_store_read_enabled, hide_clawmetry_session

bp_tracing = Blueprint('tracing', __name__)


# Event types that are pure plumbing — never their own span in the trace view.
_TRACE_PLUMBING_TYPES = frozenset({
    "session.started", "session.ended", "session.created",
    "model.changed", "thinking_level_change", "context.compiled",
    "agent.heartbeat", "queue-operation", "custom", "custom_message",
})

# NeMo Guardrails compact tool-catalog meta-tools. When NEMOCLAW_TOOL_CATALOG
# is active these names appear as tool_use blocks in the JSONL transcript; they
# are guardrail dispatches, not real agent actions. Spans for these names get
# nemoclaw_meta=True so the frontend can filter/style them separately.
_NEMOCLAW_CATALOG_TOOLS: frozenset = frozenset({
    "tool_search",
    "tool_describe",
    "tool_call",
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


def _thinking_texts(d):
    """Reasoning text carried on one event's data, across every shape we ingest.

    * OpenClaw / Anthropic content lists: ``message.content[]`` (or
      ``content[]``) blocks of ``type: "thinking"`` (text under ``thinking``)
      or ``type: "reasoning"`` (text under ``text``). ``redacted_thinking``
      carries ciphertext only and is skipped.
    * Family adapters that ride reasoning on the assistant message instead of
      a separate event: ``extra.thinking`` / ``thinking`` string.
    Returns a list of non-empty strings in on-disk order.
    """
    out = []
    if not isinstance(d, dict):
        return out
    msg = d.get("message")
    content = msg.get("content") if isinstance(msg, dict) else None
    if content is None:
        content = d.get("content")
    if isinstance(content, list):
        for b in content:
            if not isinstance(b, dict):
                continue
            bt = b.get("type")
            if bt == "thinking":
                txt = b.get("thinking") if isinstance(b.get("thinking"), str) else b.get("text")
            elif bt == "reasoning":
                txt = b.get("text") if isinstance(b.get("text"), str) else b.get("reasoning")
            else:
                continue
            if isinstance(txt, str) and txt.strip():
                out.append(txt)
    extra = d.get("extra") if isinstance(d.get("extra"), dict) else {}
    for src in (extra, d):
        t = src.get("thinking")
        if isinstance(t, str) and t.strip() and t not in out:
            out.append(t)
    return out


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


# ── spans-backed traces (#4782) ─────────────────────────────────────────────
#
# Everything above reconstructs traces from the EVENTS table, which is right for
# OpenClaw and the runtimes that ship session transcripts: tracing then works
# with no exporter at all. But an app that speaks OTLP produces spans and no
# events, so it appeared in the runtime switcher, the Agent Inventory, and the
# cost tiles while having nothing to click into in the one view built to show
# traces. This module's own docstring claimed spans were "merged in when
# present"; they were not read here at all.
#
# So the spans table is a SECOND source, unioned in. Event reconstruction still
# wins whenever a trace has both, because it carries prompts, tool pairing, and
# sub-agent nesting that raw spans do not.


def _span_traces(limit=200, runtime=None):
    """Trace rollups straight from the ``spans`` table. Daemon proxy first,
    read-only fallback for single-process boots (mirrors ``_events_for``)."""
    kw = {"limit": limit}
    if runtime:
        kw["agent_type"] = runtime
    rows = None
    try:
        from routes.local_query import local_store_via_daemon
        rows = local_store_via_daemon("query_traces", **kw)
    except Exception:
        rows = None
    if rows is None and is_local_store_read_enabled():
        try:
            from clawmetry import local_store
            rows = local_store.get_store(read_only=True).query_traces(**kw)
        except Exception:
            rows = None
    return rows or []


def _spans_for_trace(trace_id, limit=5000):
    """Raw span rows for one OTel trace id."""
    rows = None
    try:
        from routes.local_query import local_store_via_daemon
        rows = local_store_via_daemon("query_spans", trace_id=trace_id, limit=limit)
    except Exception:
        rows = None
    if rows is None and is_local_store_read_enabled():
        try:
            from clawmetry import local_store
            rows = local_store.get_store(read_only=True).query_spans(
                trace_id=trace_id, limit=limit)
        except Exception:
            rows = None
    return rows or []


def _summarize_span_trace(row):
    """One ``query_traces`` row -> the trace-list contract.

    Same keys the event path returns so the frontend renders both without
    branching, plus ``source`` so it can label provenance.
    """
    start_ts = row.get("start_ts") or 0
    tokens = int(row.get("tokens_input") or 0) + int(row.get("tokens_output") or 0)
    service = (row.get("service_name") or "").strip()
    root = (row.get("root_name") or "").strip()
    trace_id = row.get("trace_id") or ""
    # Title reads as "my-langchain-app openai.chat", never a bare hex id. A
    # first-time user should not have to recognise a trace by its checksum.
    # ``root_name`` / ``service_name`` are new columns, so a dashboard talking
    # to a not-yet-upgraded daemon gets neither; fall back to the app's own
    # agent_type before giving up and showing the id.
    title = (" ".join(p for p in (service, root) if p)
             or (row.get("agent_type") or "").strip()
             or trace_id[:16])
    has_error = bool(row.get("has_error"))
    return {
        "trace_id": trace_id,
        "name": (root or service or row.get("agent_type") or trace_id)[:40],
        "title": title,
        "start_ms": int(start_ts * 1000) if start_ts else None,
        "duration_ms": row.get("duration_ms") or 0,
        "span_count": int(row.get("span_count") or 0),
        "model": row.get("model") or "",
        "total_tokens": tokens,
        "total_cost_usd": round(float(row.get("cost_usd") or 0.0), 6),
        "error_count": 1 if has_error else 0,
        "has_subagents": False,
        "status": "error" if has_error else "ok",
        "source": "spans",
        "service_name": service,
        "agent_type": row.get("agent_type") or "",
        "session_id": row.get("session_id") or "",
    }


def _span_ui_kind(row):
    """Map an OTel span onto the kinds the waterfall colours by.

    OTel's own ``kind`` (INTERNAL / CLIENT / SERVER) says how a span relates to
    its peer, not what it did, so it is useless for colouring an agent trace.
    Read the semantics instead: a tool name means a tool, a model or a GenAI
    operation means an LLM call.
    """
    name = (row.get("name") or "").lower()
    attrs = row.get("attributes") if isinstance(row.get("attributes"), dict) else {}
    if row.get("tool_name") or name.startswith("tool.") or "execute_tool" in name:
        return "tool"
    op = str(attrs.get("gen_ai.operation.name") or "").lower()
    if (row.get("model") or op in ("chat", "text_completion", "generate_content")
            or name.endswith(".chat") or name.endswith(".completion")
            or "llm" in name):
        return "llm"
    if "agent" in name or "workflow" in name:
        return "agent"
    if "retriev" in name or "embed" in name or "vector" in name:
        return "retrieval"
    return "event"


def _build_spans_from_store(rows):
    """Span rows -> (spans, root_ids) in the same shape ``_build_spans``
    returns, so the waterfall, the tree, and the detail drawer are one
    renderer rather than two."""
    rows = sorted(rows, key=lambda r: (r.get("start_ts") or 0))
    known = {r.get("span_id") for r in rows if r.get("span_id")}
    spans, roots = [], []
    for r in rows:
        sid = r.get("span_id")
        if not sid:
            continue
        parent = r.get("parent_span_id") or None
        # A parent we never received (dropped batch, sampling) would orphan the
        # span out of the tree entirely, so promote it to a root instead.
        if parent not in known:
            parent = None
        start_ts = r.get("start_ts") or 0
        tokens = int(r.get("tokens_input") or 0) + int(r.get("tokens_output") or 0)
        if not tokens:
            tokens = int(r.get("token_count") or 0)
        status = "error" if (r.get("status") or "").upper() == "ERROR" else "ok"
        detail = r.get("input") or r.get("output") or ""
        if not isinstance(detail, str):
            detail = json.dumps(detail, default=str)
        out = r.get("output") or ""
        if not isinstance(out, str):
            out = json.dumps(out, default=str)
        span = {
            "span_id": sid,
            "parent_span_id": parent,
            "name": r.get("name") or "span",
            "kind": _span_ui_kind(r),
            "event_type": "otel.span",
            "start_ms": int(start_ts * 1000) if start_ts else 0,
            "duration_ms": float(r.get("duration_ms") or 0),
            "model": r.get("model") or "",
            "tokens": tokens,
            "cost": round(float(r.get("cost_usd") or 0.0), 6),
            "status": status,
            "is_subagent": False,
            "detail": detail[:8000],
            "output": out[:8000],
            "tool": r.get("tool_name") or "",
        }
        spans.append(span)
        if parent is None:
            roots.append(sid)
    return spans, roots


def _summarize_spans(trace_id, spans):
    """Trace summary computed from the span list we already hold."""
    if not spans:
        return {"trace_id": trace_id, "span_count": 0}
    start = min(s["start_ms"] for s in spans)
    end = max(s["start_ms"] + int(s["duration_ms"]) for s in spans)
    errors = sum(1 for s in spans if s["status"] == "error")
    model = next((s["model"] for s in spans if s["model"]), "")
    return {
        "trace_id": trace_id,
        "name": trace_id[:40],
        "title": next((s["name"] for s in spans), "") or trace_id[:16],
        "start_ms": start,
        "duration_ms": max(0, end - start),
        "span_count": len(spans),
        "model": model,
        "total_tokens": sum(s["tokens"] for s in spans),
        "total_cost_usd": round(sum(s["cost"] for s in spans), 6),
        "error_count": errors,
        "has_subagents": False,
        "status": "error" if errors else "ok",
        "source": "spans",
    }


def _session_runtime(session_id):
    """Runtime that owns a session id, from its prefix. Mirrors the frontend's
    ``_cmRuntimeOf``: ``claude_code:abc`` -> ``claude_code``, bare -> openclaw."""
    sid = (session_id or "").strip()
    return sid.split(":", 1)[0].lower() if ":" in sid else "openclaw"


@bp_tracing.route("/api/traces")
def api_traces():
    """List traces, most-recent first, from BOTH sources.

    Event-derived traces (one per session) and span-derived traces (one per
    OTel ``trace_id``) are unioned. A session carrying both resolves to a single
    entry: the event reconstruction, which is richer.

    ``runtime=<id>`` scopes the list server-side. Span traces filter on
    ``agent_type``; event traces filter on the session-id prefix. A foreign OTLP
    app has no session prefix, so selecting one correctly yields only its own
    spans rather than leaking the node's OpenClaw sessions into its view.

    DuckDB-first; ClawMetry's own helper sessions are hidden (plumbing).
    Returns ``available:false`` (HTTP 200) when neither source can be read.
    """
    try:
        limit = min(int(request.args.get("limit", 100)), 500)
    except (ValueError, TypeError):
        limit = 100
    runtime = (request.args.get("runtime") or "").strip().lower()
    runtime = None if runtime in ("", "all") else runtime

    # Scan a bounded window of recent events to group into the trace list.
    # 14000 was needlessly heavy on the shared DuckDB connection (it's the
    # main contributor to proxy-timeout empties); 6000 still covers far more
    # than the ``limit`` traces we return, most-recent first.
    rows = _events_for(limit=6000)
    span_rows = _span_traces(limit=max(limit, 200), runtime=runtime)

    if rows is None and not span_rows:
        return jsonify({"available": False, "traces": [], "total": 0})

    by_sid = {}
    for e in (rows or []):
        sid = (e.get("session_id") or "").strip()
        if not sid or hide_clawmetry_session(sid):
            continue
        if runtime and _session_runtime(sid) != runtime:
            continue
        by_sid.setdefault(sid, []).append(e)

    traces = [_summarize_trace(sid, evs) for sid, evs in by_sid.items()]
    traces = [t for t in traces if t["span_count"] > 0]
    for t in traces:
        t["source"] = "events"

    # Union in the span-only traces. A trace whose session already produced an
    # event-derived entry is dropped here, not merged: two rows for one run is
    # the bug this guards against.
    seen_sessions = set(by_sid)
    seen_ids = {t["trace_id"] for t in traces}
    for row in span_rows:
        sid = (row.get("session_id") or "").strip()
        if sid and (sid in seen_sessions or hide_clawmetry_session(sid)):
            continue
        summary = _summarize_span_trace(row)
        if not summary["trace_id"] or summary["trace_id"] in seen_ids:
            continue
        seen_ids.add(summary["trace_id"])
        traces.append(summary)

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

    Reasoning is its own span kind (``reasoning``, name ``think``, detail =
    the thinking text). A thinking block inside an assistant message nests
    under that message's ``chat`` span; a standalone ``thinking`` event (the
    family adapters emit one before the message/tool_call it produced) sits
    beside the chat span under the agent root. Either way the reasoning span
    becomes the parent of every ``execute_tool`` span that follows it within
    the same assistant turn (the reasoning-to-tool causal link); a turn with
    no reasoning nests its tools under the chat span as before. The scope of
    "same turn" ends at the next user prompt or the next reasoning span.

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
    # Most recent reasoning span per lane (main / sub-agent); tools nest under
    # it until the next user prompt or the next reasoning span replaces it.
    last_reasoning = {False: None, True: None}

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
        # ONE normaliser for every shape (clawmetry.event_shape): the
        # OpenClaw v3 ``finalPromptText`` / ``completionText`` keys, the
        # Anthropic ``message.content`` block list, and the family-adapter
        # ``data.content`` body all resolve to the same ``text``.
        shape = _event_shape.classify(et, d)
        text = shape["text"]
        if not text and isinstance(d.get("text"), str):
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

        if low == "thinking":
            # Standalone reasoning event (family adapters: claude_code, codex,
            # kimi, ...; replay_events kind=thinking via the fallback below).
            # event_shape keeps reasoning in ``thinking`` (never ``text``),
            # so read that first; ``text`` covers the bare ``data.text`` shape.
            think_text = shape["thinking"] or text or ""
            if not think_text.strip():
                continue
            rs = _mk(eid, agent_parent, "think", "reasoning", start, nxt,
                     is_sub=is_sub, detail=think_text, event_type=et)
            last_reasoning[is_sub] = rs
            continue

        if is_assistant:
            chat = _mk(eid, agent_parent,
                       ("chat " + (e.get("model") or "")).strip() or "chat",
                       "llm", start, nxt, is_sub=is_sub, model=e.get("model") or "",
                       tokens=e.get("token_count"), cost=_event_cost(e),
                       status="error" if (d.get("isError") or d.get("is_error")
                                          or shape["is_error"]) else "ok",
                       detail=text, event_type=et)
            # Thinking blocks carried INSIDE the assistant message (OpenClaw,
            # Anthropic-shaped transcripts, extra.thinking) nest under it.
            for k, think_text in enumerate(_thinking_texts(d)):
                rs = _mk(f"{eid}-think-{k}", chat["span_id"], "think", "reasoning",
                         start, nxt, is_sub=is_sub, detail=think_text, event_type=et)
                last_reasoning[is_sub] = rs
            tool_parent = (last_reasoning[is_sub] or chat)["span_id"]
            for j, tu in enumerate(_walk_tool_uses(d)):
                tuid = tu.get("id") or f"{eid}-tu-{j}"
                tname = _tool_label(tu.get("name"))
                ts = _mk(tuid, tool_parent, "execute_tool " + tname, "tool",
                         start, nxt, is_sub=is_sub, tool=tname,
                         detail=_short_input(tu.get("input")), event_type=et)
                if (tu.get("name") or "") in _NEMOCLAW_CATALOG_TOOLS:
                    ts["nemoclaw_meta"] = True
                    dispatched = (tu.get("input") or {}).get("name")
                    if dispatched:
                        ts["dispatched_tool"] = dispatched
                tool_spans[tu.get("id") or tuid] = ts
            continue

        if is_user and text.strip():
            last_reasoning[is_sub] = None  # a new prompt closes the reasoning scope
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


def _replay_thinking_rows(session_id, limit=4000):
    """``replay_events`` rows of kind ``thinking`` for a session, reshaped as
    event-like dicts ``_build_spans`` understands (``event_type: thinking``,
    ``data.content`` = the text). Adapters that implement
    ``iter_replay_events`` may write reasoning there without emitting a
    ``thinking`` event, so this is the fallback when the raw events carry
    none. Empty list on any failure or when the store is unreadable."""
    try:
        from routes.local_query import local_store_via_daemon
        rows = local_store_via_daemon(
            "query_replay_events", session_id=session_id, limit=limit) or []
    except Exception:
        rows = []
    out = []
    for r in rows:
        if not isinstance(r, dict) or (r.get("kind") or "") != "thinking":
            continue
        payload = r.get("payload") if isinstance(r.get("payload"), dict) else {}
        text = ""
        for key in ("text", "thinking", "content", "summary"):
            v = payload.get(key)
            if isinstance(v, str) and v.strip():
                text = v
                break
        if not text and isinstance(r.get("payload"), str):
            text = r["payload"]
        if not text.strip():
            continue
        out.append({
            "id": f"replay-{r.get('span_id') or len(out)}",
            "event_type": "thinking",
            "ts": r.get("ts"),
            "data": {"role": "assistant", "content": text, "_replay": True},
        })
    return out


def _reasoning_summary(session_id, spans):
    """What the UI needs to render the reasoning lane honestly: how many
    reasoning spans exist, and (when there are none) whether the runtime's
    adapter says reasoning is exposed at all. ``coverage`` is one of
    full / partial / none / unknown, ``note`` is the adapter's own sentence."""
    runtime = _session_runtime(session_id)
    try:
        from routes.trail import coverage_for_runtime
        cov = coverage_for_runtime(runtime)
    except Exception:
        cov = {"inputs": "unknown", "reasoning": "unknown", "note": ""}
    return {
        "runtime": runtime,
        "span_count": sum(1 for s in spans if s.get("kind") == "reasoning"),
        "coverage": cov.get("reasoning", "unknown"),
        "note": cov.get("note", ""),
    }


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
    if rows:
        spans, roots = _build_spans(rows)
        if not any(s.get("kind") == "reasoning" for s in spans):
            # No thinking in the raw events: an adapter may have written its
            # reasoning to replay_events instead. Rebuild with those merged in
            # so the causal link still forms.
            replay = _replay_thinking_rows(session_id)
            if replay:
                spans, roots = _build_spans(list(rows) + replay)
        summary = _summarize_trace(session_id, rows)
        return jsonify({
            "available": True,
            "trace_id": session_id,
            "summary": summary,
            "spans": spans,
            "root_span_ids": roots,
            "agent_graph": _build_agent_graph(spans),
            "reasoning": _reasoning_summary(session_id, spans),
            "source": "events",
        })

    # No events. The id may be an OTel trace_id from an app that only speaks
    # OTLP (#4782) -- before this, those traces were listed nowhere and opened
    # to a 404, which reads as "ClawMetry lost my data".
    span_rows = _spans_for_trace(session_id)
    if span_rows:
        spans, roots = _build_spans_from_store(span_rows)
        return jsonify({
            "available": True,
            "trace_id": session_id,
            "summary": _summarize_spans(session_id, spans),
            "spans": spans,
            "root_span_ids": roots,
            "agent_graph": _build_agent_graph(spans),
            "source": "spans",
        })

    if rows is None:
        return jsonify({"available": False, "spans": []})
    return jsonify({"error": "Trace not found", "spans": []}), 404
