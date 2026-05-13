"""Tests for :mod:`clawmetry.adapters.nemo` — issue #234.

Exercises the NeMo Agent Toolkit telemetry adapter by feeding it
synthesized event dicts (no real NeMo install required) and asserting:

  * Each NeMo event_type maps to the expected dot.separated ClawMetry
    event_type.
  * The mapped rows pass `LocalStore.ingest` validation and are
    queryable via `query_events`.
  * Token counts, model, and cost land on the right top-level columns.
  * The session_id grouping uses the NeMo ``trace_id`` so all events
    from one workflow run end up in the same ClawMetry session.
  * Object-style events (NeMo's native ``IntermediateStep`` shape) work
    via duck-typing, not just dicts.
  * Unknown event types are dropped (not crash, not stored).
  * Errors in the upstream store don't bubble out of ``on_event``.

We use an isolated tmp DuckDB so the user's real ``~/.clawmetry/`` is
untouched — same fixture pattern as ``tests/test_brain_local_store.py``.
"""

from __future__ import annotations

import importlib
import time
import types
import uuid

import pytest


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _wait_flush(store, t: float = 2.0) -> None:
    """Block until the in-memory ring buffer has drained to DuckDB."""
    deadline = time.monotonic() + t
    while time.monotonic() < deadline:
        if store.health()["ring_depth"] == 0:
            return
        time.sleep(0.02)


@pytest.fixture
def isolated_store(tmp_path, monkeypatch):
    """Fresh DuckDB at ``tmp_path/events.duckdb`` — no cross-test bleed.

    Reloads ``clawmetry.local_store`` so module-level env-var-derived
    constants (DB path, flush knobs) pick up the monkeypatched values.
    """
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "events.duckdb"))
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_SECS", "0.05")
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_BATCH", "1")  # flush on every write

    import clawmetry.local_store as ls
    importlib.reload(ls)
    # Reset the process-wide singleton so the next get_store() opens our tmp.
    ls._reset_singleton_for_tests()
    store = ls.get_store()
    yield store
    # Clean shutdown — stop the background flusher so pytest doesn't see
    # a "dangling thread" warning from another test that reloads the module.
    try:
        store.stop(flush=True)
    finally:
        ls._reset_singleton_for_tests()


@pytest.fixture
def adapter(isolated_store):
    """Fresh ``NeMoAdapter`` bound to the isolated store."""
    # Late import — module-level import would bind to whichever local_store
    # singleton existed before our fixture reloaded it.
    from clawmetry.adapters.nemo import NeMoAdapter

    return NeMoAdapter(
        isolated_store,
        node_id="test-node",
        agent_id="test-agent",
        default_session_id="default-sess",
        default_model="nemo-test-model",
    )


# ---------------------------------------------------------------------------
# Mapping unit tests (no I/O)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "raw_type,expected",
    [
        ("WORKFLOW_START", "session.started"),
        ("workflow_start", "session.started"),
        ("TASK_START",     "session.started"),
        ("WORKFLOW_END",   "session.ended"),
        ("task_end",       "session.ended"),
        ("LLM_START",      "prompt.submitted"),
        ("llm_call",       "prompt.submitted"),
        ("LLM_END",        "model.completed"),
        ("llm_response",   "model.completed"),
        ("TOOL_START",     "tool.call"),
        ("tool_call",      "tool.call"),
        ("TOOL_END",       "tool.result"),
        ("tool_result",    "tool.result"),
    ],
)
def test_event_type_mapping(adapter, raw_type, expected):
    row = adapter.map_event({
        "event_type": raw_type,
        "trace_id":   "trace-x",
        "span_id":    "span-x",
        "start_time": "2026-05-13T10:00:00Z",
        "end_time":   "2026-05-13T10:00:01Z",
        "attributes": {},
    })
    assert row is not None
    assert row["event_type"] == expected
    assert row["agent_type"] == "nemo"
    assert row["session_id"] == "trace-x"


def test_unknown_event_type_dropped(adapter, caplog):
    caplog.set_level("WARNING", logger="clawmetry.adapters.nemo")
    row = adapter.map_event({"event_type": "NOT_A_REAL_NEMO_EVENT"})
    assert row is None
    # Logged at WARNING, not raised.
    assert any("unknown event_type" in r.message for r in caplog.records)


def test_missing_event_type_dropped(adapter):
    assert adapter.map_event({"attributes": {"x": 1}}) is None
    assert adapter.map_event({}) is None


def test_enum_event_type_accepted(adapter):
    """NeMo's IntermediateStepType is an enum; we read .value or .name."""
    fake_enum = types.SimpleNamespace(value="LLM_END", name="LLM_END")
    row = adapter.map_event({
        "event_type": fake_enum,
        "trace_id":   "t",
        "attributes": {"model": "m", "completion": "hi", "input_tokens": 1, "output_tokens": 2},
    })
    assert row is not None
    assert row["event_type"] == "model.completed"


def test_object_event_duck_typed(adapter):
    """NeMo IntermediateStep objects (attrs, not keys) work too."""
    ev = types.SimpleNamespace(
        event_type="TOOL_START",
        trace_id="trace-obj",
        span_id="span-obj",
        start_time=1715000000.0,
        attributes={"tool_name": "Bash", "tool_input": {"cmd": "ls"}},
    )
    row = adapter.map_event(ev)
    assert row is not None
    assert row["event_type"] == "tool.call"
    assert row["session_id"] == "trace-obj"
    assert row["data"]["name"] == "Bash"
    assert row["data"]["input"] == {"cmd": "ls"}


def test_attributes_alternate_keys(adapter):
    """``metadata`` / ``payload`` / ``data`` are accepted as attribute holders."""
    for key in ("attributes", "metadata", "payload", "data"):
        row = adapter.map_event({
            "event_type": "LLM_END",
            "trace_id":   "t",
            key: {"model": "claude", "completion": "x", "input_tokens": 5, "output_tokens": 7},
        })
        assert row is not None, f"key={key} should resolve attrs"
        assert row["model"] == "claude"
        assert row["token_count"] == 12


def test_llm_end_token_and_cost_extraction(adapter):
    row = adapter.map_event({
        "event_type": "LLM_END",
        "trace_id":   "trace-llm",
        "span_id":    "span-llm",
        "attributes": {
            "model":          "claude-3.5-sonnet",
            "completion":     "Hello world",
            "input_tokens":   512,
            "output_tokens":  128,
            "cost_usd":       0.0032,
        },
    })
    assert row["model"] == "claude-3.5-sonnet"
    assert row["token_count"] == 512 + 128
    assert row["cost_usd"] == pytest.approx(0.0032)
    assert row["data"]["completionText"] == "Hello world"
    assert row["data"]["promptCache"]["lastCallUsage"] == {
        "input": 512, "output": 128, "total": 640,
    }
    # The v3-compatible nested ``data.data`` payload should mirror it.
    assert row["data"]["data"]["completionText"] == "Hello world"
    # Discriminator stamped for the dashboard's read path.
    assert row["data"]["type"] == "model.completed"


def test_llm_end_cost_dict_flattened(adapter):
    """Cost can arrive as {"total": …} — must be flattened to a float."""
    row = adapter.map_event({
        "event_type": "LLM_END",
        "trace_id":   "t",
        "attributes": {"cost_usd": {"total": 1.23}, "input_tokens": 1, "output_tokens": 2},
    })
    assert row["cost_usd"] == pytest.approx(1.23)


def test_llm_end_bad_tokens_default_zero(adapter):
    """Bad token values must not crash — fall back to 0."""
    row = adapter.map_event({
        "event_type": "LLM_END",
        "trace_id":   "t",
        "attributes": {"input_tokens": "lol", "output_tokens": None},
    })
    assert row["token_count"] == 0


def test_tool_call_and_result(adapter):
    call = adapter.map_event({
        "event_type": "TOOL_START",
        "trace_id":   "sess",
        "span_id":    "tool-span-1",
        "attributes": {"tool_name": "tavily_search", "tool_input": {"q": "claude"}},
    })
    assert call["data"]["name"] == "tavily_search"
    assert call["data"]["input"] == {"q": "claude"}
    assert call["data"]["id"] == "tool-span-1"

    result = adapter.map_event({
        "event_type": "TOOL_END",
        "trace_id":   "sess",
        "span_id":    "tool-span-1",
        "attributes": {"tool_name": "tavily_search", "tool_output": "result-text"},
    })
    assert result["data"]["tool_use_id"] == "tool-span-1"
    assert result["data"]["output"] == "result-text"
    assert result["data"]["is_error"] is False


def test_tool_result_with_error(adapter):
    row = adapter.map_event({
        "event_type": "TOOL_END",
        "trace_id":   "t",
        "attributes": {"tool_name": "x", "error": "boom"},
    })
    assert row["data"]["is_error"] is True
    assert row["data"]["error"] == "boom"


def test_session_id_fallback_chain(adapter):
    # No trace_id, no session_id → adapter default.
    row = adapter.map_event({"event_type": "WORKFLOW_START"})
    assert row["session_id"] == "default-sess"
    # Explicit session_id at top level — used when trace_id absent.
    row = adapter.map_event({"event_type": "WORKFLOW_START", "session_id": "explicit"})
    assert row["session_id"] == "explicit"
    # trace_id wins over both.
    row = adapter.map_event({
        "event_type": "WORKFLOW_START",
        "trace_id":   "trace-wins",
        "session_id": "loser",
    })
    assert row["session_id"] == "trace-wins"


def test_epoch_timestamp_coerced(adapter):
    """Epoch seconds (float) must be coerced to ISO before ingest — the
    local_store ts column is a string ISO timestamp; passing a float
    crashes downstream queries on dates."""
    row = adapter.map_event({
        "event_type": "LLM_END",
        "trace_id":   "t",
        "end_time":   1715000000.0,
        "attributes": {},
    })
    assert isinstance(row["ts"], str)
    assert row["ts"].startswith("20")  # ISO year prefix


# ---------------------------------------------------------------------------
# End-to-end ingest + query tests
# ---------------------------------------------------------------------------


def _synth_workflow(trace_id: str = None) -> list[dict]:
    """A realistic NeMo event stream — workflow with one LLM call and one tool call."""
    trace_id = trace_id or str(uuid.uuid4())
    return [
        {
            "event_type": "WORKFLOW_START",
            "trace_id":   trace_id,
            "span_id":    "wf-span",
            "start_time": "2026-05-13T10:00:00Z",
            "attributes": {"workflow_name": "research_demo"},
        },
        {
            "event_type": "LLM_START",
            "trace_id":   trace_id,
            "span_id":    "llm-span",
            "start_time": "2026-05-13T10:00:01Z",
            "attributes": {"model": "claude-3.5-sonnet", "prompt": "What is ClawMetry?"},
        },
        {
            "event_type": "LLM_END",
            "trace_id":   trace_id,
            "span_id":    "llm-span",
            "end_time":   "2026-05-13T10:00:02Z",
            "attributes": {
                "model": "claude-3.5-sonnet",
                "completion": "ClawMetry is an OSS observability dashboard.",
                "input_tokens": 100,
                "output_tokens": 50,
                "cost_usd": 0.0015,
            },
        },
        {
            "event_type": "TOOL_START",
            "trace_id":   trace_id,
            "span_id":    "tool-span",
            "start_time": "2026-05-13T10:00:03Z",
            "attributes": {"tool_name": "web_search", "tool_input": {"q": "clawmetry"}},
        },
        {
            "event_type": "TOOL_END",
            "trace_id":   trace_id,
            "span_id":    "tool-span",
            "end_time":   "2026-05-13T10:00:04Z",
            "attributes": {"tool_name": "web_search", "tool_output": "OSS dashboard."},
        },
        {
            "event_type": "WORKFLOW_END",
            "trace_id":   trace_id,
            "span_id":    "wf-span",
            "end_time":   "2026-05-13T10:00:05Z",
            "attributes": {"workflow_name": "research_demo", "status": "completed"},
        },
    ]


def test_end_to_end_ingest_and_query(adapter, isolated_store):
    trace_id = "trace-e2e"
    events = _synth_workflow(trace_id)
    rows = [adapter.on_event(e) for e in events]
    assert all(r is not None for r in rows), "every event should map + ingest"

    _wait_flush(isolated_store)

    stored = isolated_store.query_events(session_id=trace_id, limit=100)
    assert len(stored) == 6, f"expected 6 stored rows, got {len(stored)}"

    types_in_store = {r["event_type"] for r in stored}
    assert types_in_store == {
        "session.started",
        "session.ended",
        "prompt.submitted",
        "model.completed",
        "tool.call",
        "tool.result",
    }

    # Spot-check the LLM_END row — token / cost / model on top-level cols.
    llm_end = next(r for r in stored if r["event_type"] == "model.completed")
    assert llm_end["model"] == "claude-3.5-sonnet"
    assert llm_end["token_count"] == 150
    assert llm_end["cost_usd"] == pytest.approx(0.0015)
    assert llm_end["agent_type"] == "nemo"
    assert llm_end["node_id"] == "test-node"
    assert llm_end["agent_id"] == "test-agent"


def test_on_event_swallows_ingest_errors(adapter, monkeypatch, caplog):
    """A failing store must not propagate out of on_event — losing one
    telemetry event should never crash the host NeMo agent."""

    def _boom(_row):
        raise RuntimeError("disk full")

    monkeypatch.setattr(adapter._store, "ingest", _boom)
    caplog.set_level("WARNING", logger="clawmetry.adapters.nemo")
    result = adapter.on_event({
        "event_type": "LLM_END",
        "trace_id":   "t",
        "attributes": {},
    })
    assert result is None
    assert any("local_store.ingest raised" in r.message for r in caplog.records)


def test_mapped_event_types_constant():
    """The public ``MAPPED_EVENT_TYPES`` tuple matches what the mapper produces."""
    from clawmetry.adapters.nemo import MAPPED_EVENT_TYPES, _EVENT_TYPE_MAP

    assert set(MAPPED_EVENT_TYPES) == set(_EVENT_TYPE_MAP.values())
    # Stable order — pin so future changes are intentional.
    assert MAPPED_EVENT_TYPES == (
        "session.started",
        "session.ended",
        "prompt.submitted",
        "model.completed",
        "tool.call",
        "tool.result",
    )
