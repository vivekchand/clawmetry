"""Runtime-agnostic span reconstruction for family runtimes (Agent Graph WS-A).

The Agent Graph tab (``GET /api/local/agent-graph`` →
``LocalStore.query_agent_graph``) draws nodes from ``GROUP BY (agent_type,
agent_id)`` over the ``spans`` table and edges from ``agent.spawn`` spans
joined to their parent span. Until this module existed only two producers
wrote spans: the OTLP receiver and the OpenClaw JSONL builder — and the
latter stamped every span ``agent_type='openclaw'`` / ``agent_id='main'``,
so the graph rendered ONE self-node and ZERO edges, and the 14 pro family
runtimes (claude_code, codex, cursor, …) never appeared at all (their
ingest path — ``sync.sync_family_runtimes`` — wrote sessions/subagents/
events but never spans).

This module converts the ALREADY-NORMALIZED family data
(:class:`clawmetry.adapters.base.Session` / ``Event`` shaped objects — plain
attribute access, so tests can feed namespaces) into span row dicts
compatible with ``LocalStore.ingest_span``:

  * one ``session`` root span per session,
  * ``llm.call`` for message events that carry usage,
  * ``tool.<name>`` for tool_call events,
  * ``thinking`` / ``error`` for those event types,
  * ``agent.spawn`` for (a) ``Task`` tool_calls (Claude Code-style subagent
    dispatch) or explicit ``subagent_spawn``/``agent_spawn`` events, and
    (b) each subagent record (:func:`build_subagent_spawn_span`).

Identity stamping is the point of the feature: ``agent_type`` is the REAL
runtime id (``'claude_code'``, never ``'openclaw'``); ``agent_id`` is
``'main'`` for parent-session spans and a stable child label
(subagent_type / agent stem / ``'subagent'``) for spawn spans and for spans
of sessions with ``parent_id`` set. ``agent.spawn`` spans parent onto the
spawning session's root span so the edge query yields ``main → child``.

Span ids are deterministic (sha1 over runtime/session/kind/key) so
re-ingest is idempotent — ``ingest_span`` is an ``INSERT OR REPLACE``
upsert on the ``span_id`` PK (verified local_store.py), which also lets the
two ``agent.spawn`` sources dedupe: when the subagent meta carries a
``toolUseId`` both sources derive the SAME span_id and collapse into one
row.

Dedupe contract (spawn spans):
  * source (a) Task tool_call  → key = the tool_use block id when present,
    else the event id / index;
  * source (b) subagent record → key = ``extra.toolUseId`` when present
    (same key as (a) → same span_id → upsert dedupe), else the child
    session id (a second, differently-keyed spawn span may then coexist,
    but ``query_agent_graph`` SELECT-DISTINCTs edges so the graph stays
    correct).

Volume: commentary/progress/plumbing events are skipped and event spans are
capped (default ~300/session); truncation is counted on the session span's
``spans.truncated`` attribute. ``agent.spawn`` spans are never truncated —
they're the edges the feature exists for.
"""
from __future__ import annotations

import hashlib
import time
from typing import Any

__all__ = [
    "build_family_spans",
    "build_subagent_spawn_span",
    "session_span_id",
    "session_trace_id",
]

# Cap on non-spawn spans emitted per session. Spawn spans ride on top —
# a session that fanned out keeps ALL its edges even when its event
# timeline is truncated.
MAX_SPANS_PER_SESSION = 300

# Event types that spawn a subagent regardless of tool name.
_SPAWN_EVENT_TYPES = ("subagent_spawn", "agent_spawn")

# Tool names that mean "spawn a subagent" (Claude Code Task dispatch).
_SPAWN_TOOL_NAMES = ("task",)


def _sha1_hex(*parts: Any) -> str:
    joined = "|".join("" if p is None else str(p) for p in parts)
    return hashlib.sha1(joined.encode("utf-8", "replace")).hexdigest()


def _span_id(*parts: Any) -> str:
    return _sha1_hex(*parts)[:16]


def session_trace_id(runtime: str, session_id: str) -> str:
    """Deterministic 32-hex trace id for one (runtime, session)."""
    return _sha1_hex(runtime, session_id, "trace")[:32]


def session_span_id(runtime: str, session_id: str) -> str:
    """Deterministic root-span id for one (runtime, session).

    ``session_id`` here is the NAMESPACED id (``'<runtime>:<native id>'``)
    exactly as stored in the sessions/events tables, so callers on either
    side (writer in sync.py, joins in tests) derive the same id.
    """
    return _span_id(runtime, session_id, "session")


def _get(obj: Any, name: str, default: Any = None) -> Any:
    """Tolerant attribute-or-key access (dataclass, namespace, or dict)."""
    if isinstance(obj, dict):
        return obj.get(name, default)
    return getattr(obj, name, default)


def _extra_of(obj: Any) -> dict:
    extra = _get(obj, "extra") or {}
    return extra if isinstance(extra, dict) else {}


def _f(v: Any) -> float | None:
    try:
        f = float(v)
    except (TypeError, ValueError):
        return None
    return f if f > 0 else None


def _i(v: Any) -> int | None:
    try:
        n = int(v)
    except (TypeError, ValueError):
        return None
    return n if n > 0 else None


def _first(d: dict, *keys: str) -> Any:
    for k in keys:
        v = d.get(k)
        if v:
            return v
    return None


def child_agent_label(session: Any) -> str:
    """Stable child label for a subagent session.

    Preference order: an explicit subagent/agent type from the adapter's
    ``extra`` (Claude Code stamps ``agentType`` from the meta.json), then
    the agent file stem, then the ``::<stem>`` suffix of the namespaced
    child id, then the literal ``'subagent'``.
    """
    extra = _extra_of(session)
    label = _first(
        extra, "agentType", "agent_type", "subagentType", "subagent_type",
        "agentFile", "agent_file",
    )
    if label:
        return str(label)
    sid = str(_get(session, "id") or "")
    if "::" in sid:
        stem = sid.rsplit("::", 1)[1].strip()
        if stem:
            return stem
    return "subagent"


def _spawn_label_from_tool_call(event: Any) -> tuple[str, str, dict]:
    """(child_label, tool_use_id, input_dict) for a spawn-shaped tool_call."""
    calls = _get(event, "tool_calls") or []
    call = calls[0] if calls and isinstance(calls[0], dict) else {}
    inp = call.get("input") if isinstance(call.get("input"), dict) else {}
    label = _first(inp, "subagent_type", "subagentType", "agent_type",
                   "agentType", "agent", "name") or ""
    if not label:
        extra = _extra_of(event)
        label = _first(extra, "subagent_type", "subagentType", "agentType",
                       "agent_type", "label") or ""
    tool_use_id = str(call.get("id") or "")
    return (str(label) or "subagent", tool_use_id, inp)


def _is_spawn_event(event: Any) -> bool:
    etype = str(_get(event, "type") or "").lower()
    if etype in _SPAWN_EVENT_TYPES:
        return True
    if etype == "tool_call":
        return str(_get(event, "tool_name") or "").lower() in _SPAWN_TOOL_NAMES
    return False


def _event_has_usage(event: Any) -> bool:
    if _i(_get(event, "tokens")):
        return True
    extra = _extra_of(event)
    return bool(
        _first(extra, "inputTokens", "input_tokens", "outputTokens",
               "output_tokens", "usage")
    )


def build_family_spans(
    runtime: str,
    session: Any,
    events: list | None,
    *,
    node_id: str | None = None,
    max_spans: int = MAX_SPANS_PER_SESSION,
) -> list[dict]:
    """Convert one normalized family session (+ its events) into span rows.

    ``session`` / ``events`` are :class:`clawmetry.adapters.base.Session` /
    ``Event`` shaped (attribute access; plain namespaces work too, which is
    what the tests feed). Returns a list of dicts ready for
    ``LocalStore.ingest_span``; never raises on malformed events (they are
    skipped).

    For a session with ``parent_id`` set (a subagent child) every span is
    stamped ``agent_id=<child label>`` and the root session span parents
    onto the deterministic spawn-span id, keeping the whole child subtree
    attached under the parent's trace. Callers typically pass ``events=[]``
    for children (sync skips per-event re-ingest for them) — the session
    span alone is enough to give the child node its stats.
    """
    runtime = str(runtime or "").strip() or "unknown"
    native_id = str(_get(session, "id") or "")
    ns_id = native_id if native_id.startswith(f"{runtime}:") else f"{runtime}:{native_id}"
    trace_id = session_trace_id(runtime, ns_id)
    root_id = session_span_id(runtime, ns_id)
    parent_native = _get(session, "parent_id")
    is_child = bool(parent_native)
    agent_id = child_agent_label(session) if is_child else "main"
    model = str(_get(session, "model") or "") or None

    now = time.time()
    started = _f(_get(session, "started_at")) or now
    ended = _f(_get(session, "ended_at"))

    root_attrs: dict = {
        "session.id": ns_id,
        "session.runtime": runtime,
        "reconstructed": True,
    }
    if is_child:
        root_attrs["subagent.parent_session_id"] = f"{runtime}:{parent_native}"
        root_attrs["subagent.label"] = agent_id

    root_span: dict = {
        "span_id": root_id,
        "trace_id": trace_id,
        # A child session's root parents onto its spawn span so the trace
        # tree stays connected. build_subagent_spawn_span derives the same
        # deterministic id from the child session record.
        "parent_span_id": (
            _spawn_span_id_for_child(runtime, session) if is_child else None
        ),
        "name": "session",
        "kind": "INTERNAL",
        "start_ts": started,
        "end_ts": ended,
        "session_id": ns_id,
        "node_id": node_id,
        "agent_type": runtime,
        "agent_id": agent_id,
        "model": model,
        "cost_usd": _f(_get(session, "cost_usd")),
        "tokens_input": _i(_get(session, "input_tokens")),
        "tokens_output": _i(_get(session, "output_tokens")),
        "token_count": _i(_get(session, "total_tokens")),
        "attributes": root_attrs,
    }
    spans: list[dict] = [root_span]

    truncated = 0
    emitted = 0
    last_llm_span_id: str | None = None

    for idx, ev in enumerate(events or []):
        etype = str(_get(ev, "type") or "").lower()
        ts = _f(_get(ev, "ts")) or started
        ev_key = str(_get(ev, "id") or "") or f"idx:{idx}"

        # ── agent.spawn (source (a)) — never truncated ─────────────────
        if _is_spawn_event(ev):
            label, tool_use_id, inp = _spawn_label_from_tool_call(ev)
            spawn_key = tool_use_id or ev_key
            attrs: dict = {"reconstructed": True, "subagent.label": label}
            if tool_use_id:
                attrs["tool_use_id"] = tool_use_id
            desc = inp.get("description") if isinstance(inp, dict) else None
            if isinstance(desc, str) and desc.strip():
                attrs["spawn.description"] = desc.strip()[:200]
            spans.append({
                "span_id": _span_id(runtime, ns_id, "spawn", spawn_key),
                "trace_id": trace_id,
                # Root-span parent — this is what makes the graph edge:
                # ps = session span (agent_id 'main'), cs = this span
                # (agent_id = child label), src != dst → edge survives.
                "parent_span_id": root_id,
                "name": "agent.spawn",
                "kind": "INTERNAL",
                "start_ts": ts,
                "session_id": ns_id,
                "node_id": node_id,
                "agent_type": runtime,
                "agent_id": label,
                "attributes": attrs,
            })
            continue

        # ── capped event timeline ──────────────────────────────────────
        if emitted >= max_spans:
            truncated += 1
            continue

        if etype == "message":
            if not _event_has_usage(ev):
                continue  # commentary-grade message; skip for volume
            extra = _extra_of(ev)
            ev_model = str(extra.get("model") or "") or model
            spans.append({
                "span_id": _span_id(runtime, ns_id, "llm", ev_key),
                "trace_id": trace_id,
                "parent_span_id": root_id,
                "name": f"llm.call {ev_model}".strip() if ev_model else "llm.call",
                "kind": "CLIENT",
                "start_ts": ts,
                "session_id": ns_id,
                "node_id": node_id,
                "agent_type": runtime,
                "agent_id": agent_id,
                "model": ev_model,
                "tokens_input": _i(_first(extra, "inputTokens", "input_tokens")),
                "tokens_output": _i(_first(extra, "outputTokens", "output_tokens")),
                "token_count": _i(_get(ev, "tokens")),
                "cost_usd": _f(_first(extra, "costUsd", "cost_usd")),
                "attributes": {"reconstructed": True},
            })
            last_llm_span_id = spans[-1]["span_id"]
            emitted += 1

        elif etype == "tool_call":
            tool_name = str(_get(ev, "tool_name") or "").strip() or "tool"
            spans.append({
                "span_id": _span_id(runtime, ns_id, "tool", ev_key),
                "trace_id": trace_id,
                # Nest under the turn's llm.call when we have one — mirrors
                # the OpenClaw builder's hierarchy for the Tracing tab.
                "parent_span_id": last_llm_span_id or root_id,
                "name": f"tool.{tool_name}",
                "kind": "CLIENT",
                "start_ts": ts,
                "session_id": ns_id,
                "node_id": node_id,
                "agent_type": runtime,
                "agent_id": agent_id,
                "tool_name": tool_name,
                "attributes": {"reconstructed": True},
            })
            emitted += 1

        elif etype == "thinking":
            spans.append({
                "span_id": _span_id(runtime, ns_id, "thinking", ev_key),
                "trace_id": trace_id,
                "parent_span_id": last_llm_span_id or root_id,
                "name": "thinking",
                "kind": "INTERNAL",
                "start_ts": ts,
                "session_id": ns_id,
                "node_id": node_id,
                "agent_type": runtime,
                "agent_id": agent_id,
                "attributes": {"reconstructed": True},
            })
            emitted += 1

        elif etype == "error":
            content = _get(ev, "content")
            attrs = {"reconstructed": True}
            if isinstance(content, str) and content.strip():
                attrs["error.message"] = content.strip()[:500]
            spans.append({
                "span_id": _span_id(runtime, ns_id, "error", ev_key),
                "trace_id": trace_id,
                "parent_span_id": root_id,
                "name": "error",
                "kind": "INTERNAL",
                "status": "ERROR",
                "status_code": "ERROR",
                "start_ts": ts,
                "session_id": ns_id,
                "node_id": node_id,
                "agent_type": runtime,
                "agent_id": agent_id,
                "attributes": attrs,
            })
            emitted += 1

        # everything else (tool_result, compaction, model_change,
        # commentary, progress, custom) is skipped: it carries no graph
        # signal and this path must stay cheap.

    if truncated:
        root_attrs["spans.truncated"] = truncated

    return spans


def _spawn_span_id_for_child(runtime: str, child_session: Any) -> str:
    """Deterministic spawn-span id derived from a CHILD session record.

    Keyed on ``extra.toolUseId`` when the adapter carried it (then it
    matches the id source (a) derives from the parent's Task tool_use
    block → the two sources upsert into ONE row), else on the child's
    namespaced session id.
    """
    parent_ns = f"{runtime}:{_get(child_session, 'parent_id')}"
    extra = _extra_of(child_session)
    tool_use_id = _first(extra, "toolUseId", "tool_use_id")
    key = str(tool_use_id) if tool_use_id else _ns_child_id(runtime, child_session)
    return _span_id(runtime, parent_ns, "spawn", key)


def _ns_child_id(runtime: str, child_session: Any) -> str:
    cid = str(_get(child_session, "id") or "")
    return cid if cid.startswith(f"{runtime}:") else f"{runtime}:{cid}"


def build_subagent_spawn_span(
    runtime: str,
    child_session: Any,
    *,
    node_id: str | None = None,
) -> dict | None:
    """``agent.spawn`` span from a subagent session record (source (b)).

    Emitted by ``sync_family_runtimes`` at the same point it ingests the
    ``subagents`` row (the child-session iteration). The span lives in the
    PARENT's trace and parents onto the parent's session span, stamped
    ``agent_id=<child label>`` — that's the ``main → child`` edge. Returns
    ``None`` when the record has no ``parent_id`` (not a child).
    """
    parent_native = _get(child_session, "parent_id")
    if not parent_native:
        return None
    runtime = str(runtime or "").strip() or "unknown"
    parent_ns = f"{runtime}:{parent_native}"
    label = child_agent_label(child_session)
    started = _f(_get(child_session, "started_at")) or time.time()
    child_ns = _ns_child_id(runtime, child_session)
    extra = _extra_of(child_session)
    attrs: dict = {
        "reconstructed": True,
        "subagent_id": child_ns,
        "subagent.label": label,
    }
    tool_use_id = _first(extra, "toolUseId", "tool_use_id")
    if tool_use_id:
        attrs["tool_use_id"] = str(tool_use_id)
    return {
        "span_id": _spawn_span_id_for_child(runtime, child_session),
        "trace_id": session_trace_id(runtime, parent_ns),
        "parent_span_id": session_span_id(runtime, parent_ns),
        "name": "agent.spawn",
        "kind": "INTERNAL",
        "start_ts": started,
        "end_ts": _f(_get(child_session, "ended_at")),
        "session_id": parent_ns,
        "node_id": node_id,
        "agent_type": runtime,
        "agent_id": label,
        "cost_usd": _f(_get(child_session, "cost_usd")),
        "token_count": _i(_get(child_session, "total_tokens")),
        # Link out to the child's own trace so the Tracing tab can hop.
        "links": [{"trace_id": session_trace_id(runtime, child_ns),
                   "span_id": session_span_id(runtime, child_ns)}],
        "attributes": attrs,
    }
