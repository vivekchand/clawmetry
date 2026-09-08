"""Agent Graph spans for family runtimes (WS-A, clawmetry/span_reconstruct.py).

Feeds synthetic claude_code-shaped normalized Session/Event/subagent data
through the generic span builder into a real DuckDB store and asserts the
whole feature contract:

  * agent_type stamping — spans carry the REAL runtime id, never 'openclaw';
  * agent_id — 'main' for parent-session spans, a stable child label for
    agent.spawn spans and subagent-session spans;
  * the main → child edge appears in ``query_agent_graph`` (the spawn span
    parents onto the session root span, so the src != dst filter keeps it);
  * the two agent.spawn sources (parent-side Task tool_call, child-side
    subagent record) dedupe into ONE span via the shared toolUseId key;
  * ``runtime`` filter on ``query_agent_graph`` scopes nodes + edges (and
    'openclaw' matches legacy NULL agent_type rows via COALESCE);
  * re-ingest is idempotent (deterministic ids + INSERT OR REPLACE);
  * volume cap: event spans truncate at max_spans, spawn spans never do;
  * OpenClaw's own builder accepts an agent_type override (nemoclaw
    batches) and stamps spawn spans with a child agent_id so openclaw gets
    real edges too.
"""
from __future__ import annotations

import importlib

import pytest

from clawmetry.adapters.base import Event, Session
from clawmetry.span_reconstruct import (
    build_family_spans,
    build_subagent_spawn_span,
    session_span_id,
)

T0 = 1_750_000_000.0
RT = "claude_code"
PARENT_ID = "3f6a2b1c-parent"
CHILD_ID = f"{PARENT_ID}::agent-a1b2c3"
TOOL_USE_ID = "toolu_spawn_01"


# ── fixtures ────────────────────────────────────────────────────────────────


@pytest.fixture
def store(tmp_path, monkeypatch):
    """Fresh isolated DuckDB store per test (same pattern as test_spans_ingest)."""
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "events.duckdb"))
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_SECS", "0.05")
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_BATCH", "5")
    import clawmetry.local_store as ls
    importlib.reload(ls)
    ls._reset_singleton_for_tests()
    # Construct directly (not get_store()): on a dev box with a live daemon
    # get_store() returns the HTTP _ProxyStore, which can't serve a hermetic
    # tmp-path DB. Same pattern as test_byruntime_slices and friends.
    s = ls.LocalStore(read_only=False)
    s.start()
    yield s
    try:
        s.stop(flush=True)
    except Exception:
        pass
    ls._reset_singleton_for_tests()


def _parent_session() -> Session:
    return Session(
        agent=RT, id=PARENT_ID, model="claude-opus-4",
        started_at=T0, ended_at=T0 + 120,
        message_count=4, total_tokens=1500, input_tokens=900,
        output_tokens=600, cost_usd=0.42,
    )


def _parent_events() -> list[Event]:
    return [
        Event(agent=RT, session_id=PARENT_ID, id="e1", type="message",
              ts=T0 + 1, role="assistant", content="working on it",
              tokens=500,
              extra={"inputTokens": 300, "outputTokens": 200,
                     "model": "claude-opus-4"}),
        Event(agent=RT, session_id=PARENT_ID, id="e2", type="tool_call",
              ts=T0 + 2, role="assistant", tool_name="Read",
              tool_calls=[{"id": "toolu_read_01", "name": "Read",
                           "input": {"file_path": "/tmp/x"}}]),
        # Claude Code subagent dispatch: Task tool_call → agent.spawn.
        Event(agent=RT, session_id=PARENT_ID, id="e3", type="tool_call",
              ts=T0 + 3, role="assistant", tool_name="Task",
              tool_calls=[{"id": TOOL_USE_ID, "name": "Task",
                           "input": {"subagent_type": "researcher",
                                     "description": "dig through the docs"}}]),
        Event(agent=RT, session_id=PARENT_ID, id="e4", type="thinking",
              ts=T0 + 4, role="assistant", content="hmm"),
        Event(agent=RT, session_id=PARENT_ID, id="e5", type="error",
              ts=T0 + 5, content="tool exploded"),
        # Renderable but graph-irrelevant types must be skipped.
        Event(agent=RT, session_id=PARENT_ID, id="e6", type="tool_result",
              ts=T0 + 6, content="ok"),
        Event(agent=RT, session_id=PARENT_ID, id="e7", type="compaction",
              ts=T0 + 7),
        # Message WITHOUT usage: skipped for volume.
        Event(agent=RT, session_id=PARENT_ID, id="e8", type="message",
              ts=T0 + 8, role="user", content="thanks"),
    ]


def _child_session() -> Session:
    """Shaped like clawmetry_pro claude_code _subagent_session output."""
    return Session(
        agent=RT, id=CHILD_ID, parent_id=PARENT_ID,
        title="dig through the docs", display_name="dig through the docs",
        model="claude-opus-4", started_at=T0 + 4, ended_at=T0 + 90,
        total_tokens=700, cost_usd=0.11,
        extra={"depth": 1, "isSubagent": True, "agentType": "researcher",
               "agentFile": "agent-a1b2c3", "toolUseId": TOOL_USE_ID},
    )


def _ingest_all(store) -> None:
    for sp in build_family_spans(RT, _parent_session(), _parent_events()):
        store.ingest_span(sp)
    for sp in build_family_spans(RT, _child_session(), []):
        store.ingest_span(sp)
    spawn = build_subagent_spawn_span(RT, _child_session())
    assert spawn is not None
    store.ingest_span(spawn)
    store.flush()


# ── builder shape ───────────────────────────────────────────────────────────


def test_agent_type_is_real_runtime_never_openclaw():
    spans = build_family_spans(RT, _parent_session(), _parent_events())
    assert spans, "builder returned no spans"
    assert all(sp["agent_type"] == RT for sp in spans)
    names = sorted(sp["name"] for sp in spans)
    assert "session" in names
    assert "agent.spawn" in names
    assert "tool.Read" in names
    assert "thinking" in names
    assert "error" in names
    assert any(n.startswith("llm.call") for n in names)
    # Skipped types must not leak through.
    assert not any("tool_result" in n or "compaction" in n for n in names)


def test_parent_spans_are_main_and_spawn_carries_child_label():
    spans = build_family_spans(RT, _parent_session(), _parent_events())
    by_name = {sp["name"]: sp for sp in spans}
    root = by_name["session"]
    assert root["agent_id"] == "main"
    assert root["span_id"] == session_span_id(RT, f"{RT}:{PARENT_ID}")
    spawn = by_name["agent.spawn"]
    assert spawn["agent_id"] == "researcher"
    # The edge contract: spawn parents onto the session root span.
    assert spawn["parent_span_id"] == root["span_id"]
    # Non-spawn event spans stay attributed to the parent agent.
    assert by_name["tool.Read"]["agent_id"] == "main"


def test_llm_call_carries_usage_and_model():
    spans = build_family_spans(RT, _parent_session(), _parent_events())
    llm = [sp for sp in spans if sp["name"].startswith("llm.call")]
    assert len(llm) == 1
    assert llm[0]["model"] == "claude-opus-4"
    assert llm[0]["tokens_input"] == 300
    assert llm[0]["tokens_output"] == 200
    assert llm[0]["token_count"] == 500


def test_child_session_spans_use_child_label():
    spans = build_family_spans(RT, _child_session(), [])
    assert len(spans) == 1  # session root only (children skip event re-ingest)
    root = spans[0]
    assert root["agent_type"] == RT
    assert root["agent_id"] == "researcher"
    # The child root parents onto the deterministic spawn span id.
    spawn = build_subagent_spawn_span(RT, _child_session())
    assert root["parent_span_id"] == spawn["span_id"]


def test_spawn_sources_dedupe_on_tool_use_id():
    parent_spans = build_family_spans(RT, _parent_session(), _parent_events())
    task_spawn = [sp for sp in parent_spans if sp["name"] == "agent.spawn"][0]
    sub_spawn = build_subagent_spawn_span(RT, _child_session())
    # Same toolUseId on both sides → same deterministic span_id → the
    # INSERT OR REPLACE upsert collapses them into one row.
    assert task_spawn["span_id"] == sub_spawn["span_id"]
    assert sub_spawn["parent_span_id"] == session_span_id(RT, f"{RT}:{PARENT_ID}")
    assert sub_spawn["agent_id"] == "researcher"


def test_spawn_fallback_without_tool_use_id():
    child = _child_session()
    child.extra = {"depth": 1}  # no toolUseId, no agentType
    spawn = build_subagent_spawn_span(RT, child)
    assert spawn is not None
    # Label falls back to the ::stem of the namespaced child id.
    assert spawn["agent_id"] == "agent-a1b2c3"
    # Not a child → no spawn span.
    assert build_subagent_spawn_span(RT, _parent_session()) is None


def test_volume_cap_truncates_events_but_never_spawns():
    events = []
    for i in range(50):
        events.append(Event(agent=RT, session_id=PARENT_ID, id=f"t{i}",
                            type="tool_call", ts=T0 + i, tool_name="Bash",
                            tool_calls=[{"id": f"tu{i}", "name": "Bash",
                                         "input": {}}]))
    # Spawn arrives AFTER the cap is exhausted — must still be emitted.
    events.append(Event(agent=RT, session_id=PARENT_ID, id="late-spawn",
                        type="tool_call", ts=T0 + 99, tool_name="Task",
                        tool_calls=[{"id": "tu-late", "name": "Task",
                                     "input": {"subagent_type": "late"}}]))
    spans = build_family_spans(RT, _parent_session(), events, max_spans=10)
    names = [sp["name"] for sp in spans]
    assert names.count("agent.spawn") == 1
    assert sum(1 for n in names if n.startswith("tool.")) == 10
    root = [sp for sp in spans if sp["name"] == "session"][0]
    assert root["attributes"]["spans.truncated"] == 40


# ── store round-trip: graph nodes + edges ──────────────────────────────────


def test_main_to_child_edge_from_query_agent_graph(store):
    _ingest_all(store)
    graph = store.query_agent_graph()
    node_ids = {n["id"] for n in graph["nodes"]}
    assert f"{RT}:main" in node_ids
    assert f"{RT}:researcher" in node_ids
    assert "openclaw:main" not in node_ids  # nothing mislabeled
    assert {"from": f"{RT}:main", "to": f"{RT}:researcher"} in graph["edges"]


def test_spawn_dedupe_lands_one_row(store):
    _ingest_all(store)
    rows = store.query_spans(session_id=f"{RT}:{PARENT_ID}", limit=500)
    spawn_rows = [r for r in rows if r["name"] == "agent.spawn"]
    assert len(spawn_rows) == 1, (
        "Task-event spawn + subagent-record spawn must upsert into ONE row "
        f"(got {len(spawn_rows)})"
    )


def test_runtime_filter_scopes_nodes_and_edges(store):
    _ingest_all(store)
    # A foreign runtime's span must disappear under the filter.
    store.ingest_span({
        "span_id": "oc-span-1", "trace_id": "oc-trace-1", "name": "session",
        "start_ts": T0, "session_id": "bare-openclaw-uuid",
        "agent_type": "openclaw", "agent_id": "main",
    })
    store.flush()

    filtered = store.query_agent_graph(runtime=RT)
    ids = {n["id"] for n in filtered["nodes"]}
    assert ids == {f"{RT}:main", f"{RT}:researcher"}
    assert {"from": f"{RT}:main", "to": f"{RT}:researcher"} in filtered["edges"]

    oc = store.query_agent_graph(runtime="openclaw")
    assert {n["id"] for n in oc["nodes"]} == {"openclaw:main"}
    assert oc["edges"] == []

    # None / 'all' return the unfiltered union.
    everything = store.query_agent_graph(runtime="all")
    assert {n["id"] for n in everything["nodes"]} >= {
        f"{RT}:main", f"{RT}:researcher", "openclaw:main"}

    # Unknown runtime: empty, never a leak of the unfiltered graph.
    none = store.query_agent_graph(runtime="not-a-runtime")
    assert none["nodes"] == [] and none["edges"] == []


def test_runtime_filter_uses_coalesce_for_legacy_null():
    """The runtime clause must be COALESCE(agent_type,'openclaw') = ?.

    The CURRENT schema declares agent_type NOT NULL DEFAULT 'openclaw', so a
    NULL row is unrepresentable here — but pre-migration stores in the wild
    still carry NULLs, and a bare ``agent_type = 'openclaw'`` would silently
    hide their legacy spans. Guard at the source level since the condition
    can't be materialized in a fresh DB.
    """
    import inspect

    import clawmetry.local_store as ls

    src = inspect.getsource(ls.LocalStore.query_agent_graph)
    assert "COALESCE(agent_type,'openclaw') = ?" in src
    assert "COALESCE(cs.agent_type,'openclaw') = ?" in src
    assert "COALESCE(ps.agent_type,'openclaw') = ?" in src


def test_reingest_is_idempotent(store):
    _ingest_all(store)
    first = store.query_agent_graph()
    counts1 = {n["id"]: n["span_count"] for n in first["nodes"]}
    _ingest_all(store)  # deterministic ids → pure upsert, no dupes, no raise
    second = store.query_agent_graph()
    counts2 = {n["id"]: n["span_count"] for n in second["nodes"]}
    assert counts1 == counts2
    assert first["edges"] == second["edges"]


# ── OpenClaw builder: agent_type override + spawn child label ──────────────


def _openclaw_batch():
    return [
        {"type": "session", "version": "1.2.3", "timestamp": T0},
        {"type": "message", "timestamp": T0 + 1,
         "message": {"role": "assistant", "model": "claude-opus-4",
                     "usage": {"input_tokens": 10, "output_tokens": 5},
                     "content": [{"type": "text", "text": "hi"}]}},
        {"type": "subagent_spawn", "timestamp": T0 + 2,
         "subagent_id": "child-uuid-1", "label": "coder"},
        {"type": "subagent_spawn", "timestamp": T0 + 3,
         "subagent_id": "child-uuid-2"},  # no label → fallback
    ]


def test_openclaw_builder_agent_type_passthrough():
    from clawmetry.adapters.openclaw import OpenClawAdapter
    spans = OpenClawAdapter._build_spans_from_events(
        _openclaw_batch(), "sess-1", agent_type="nemoclaw")
    assert spans and all(sp["agent_type"] == "nemoclaw" for sp in spans)
    # Default preserved for the existing OpenClaw path.
    spans_oc = OpenClawAdapter._build_spans_from_events(_openclaw_batch(), "sess-1")
    assert all(sp["agent_type"] == "openclaw" for sp in spans_oc)


def test_openclaw_spawn_gets_child_agent_id_and_real_edge(store):
    from clawmetry.adapters.openclaw import OpenClawAdapter
    spans = OpenClawAdapter._build_spans_from_events(_openclaw_batch(), "sess-1")
    spawns = [sp for sp in spans if sp["name"] == "agent.spawn"]
    assert {sp["agent_id"] for sp in spawns} == {"coder", "subagent"}
    for sp in spans:
        store.ingest_span(sp)
    store.flush()
    graph = store.query_agent_graph(runtime="openclaw")
    ids = {n["id"] for n in graph["nodes"]}
    assert {"openclaw:main", "openclaw:coder", "openclaw:subagent"} <= ids
    assert {"from": "openclaw:main", "to": "openclaw:coder"} in graph["edges"]
    assert {"from": "openclaw:main", "to": "openclaw:subagent"} in graph["edges"]
