"""Regression tests for the v3 underscore-schema OpenClaw parser (#1135).

Real OpenClaw bare ``<sid>.jsonl`` files use a "v3 underscore" schema —
``{"type": "session", "version": 3, ...}`` on line 1, then ``message`` /
``model_change`` / ``tool_use_result`` (underscore-separated) on subsequent
lines, with the LLM payload nested under ``message.{role,content,usage}``.

The trajectory parser (which the daemon used unconditionally before #1135)
doesn't understand this shape — every event landed in DuckDB with the wrong
event_type and an un-translated data blob, so the read side surfaced
nothing. These tests pin the new behaviour:

* ``_is_v3_event`` correctly classifies the two shapes.
* ``_parse_v3_event`` maps each underscore type to the dot.separated
  event_type the trajectory parser produces, with content placed under the
  same nested key paths PR #1132's expander reads.
* Plumbing types (``thinking_level_change``, ``cwd_change``) are skipped.
* Unknown v3 types are skipped, not raised.
* ``_local_ingest_session_batch`` writes v3 batches to DuckDB end-to-end.
* The trajectory schema still works — no regression.
* The exact 7-line fixture from issue #1135 lands as exactly 6 events
  (skipping the one ``thinking_level_change`` plumbing line).
"""

from __future__ import annotations

import importlib
import json
import os
import time
from pathlib import Path

import pytest


FIXTURES = Path(__file__).parent / "fixtures" / "openclaw"


# ── Pure-function tests for the parser (no DuckDB needed) ──────────────────

def _import_sync():
    import clawmetry.sync as sync
    return sync


def test_is_v3_event_recognises_v3_session_line():
    sync = _import_sync()
    assert sync._is_v3_event({"type": "session", "version": 3, "id": "x"}) is True


def test_is_v3_event_recognises_v3_message_line():
    sync = _import_sync()
    assert sync._is_v3_event({"type": "message", "message": {"role": "user"}}) is True
    assert sync._is_v3_event({"type": "model_change"}) is True
    assert sync._is_v3_event({"type": "tool_use_result"}) is True


def test_is_v3_event_rejects_trajectory_dot_types():
    sync = _import_sync()
    # Trajectory schema uses dot.separated types — never confused for v3.
    for t in (
        "trace.artifacts", "session.started", "session.ended",
        "model.completed", "prompt.submitted", "context.compiled",
    ):
        assert sync._is_v3_event({"type": t, "data": {}}) is False, t


def test_is_v3_event_rejects_garbage():
    sync = _import_sync()
    assert sync._is_v3_event(None) is False
    assert sync._is_v3_event({}) is False
    assert sync._is_v3_event({"type": None}) is False
    assert sync._is_v3_event({"type": 42}) is False
    assert sync._is_v3_event("not a dict") is False


def test_v3_session_line_becomes_session_started():
    sync = _import_sync()
    obj = {
        "type": "session", "version": 3, "id": "sess-1",
        "timestamp": "2026-05-12T22:35:31.119296Z",
        "cwd": "/tmp/x",
    }
    row = sync._parse_v3_event(obj, session_id="sess-1", node_id="agent+test")
    assert row is not None
    assert row["event_type"] == "session.started"
    assert row["session_id"] == "sess-1"
    assert row["agent_type"] == "openclaw"
    assert row["agent_id"] == "main"
    assert row["data"]["cwd"] == "/tmp/x"
    assert row["data"]["version"] == 3


def test_v3_model_change_becomes_model_changed():
    sync = _import_sync()
    obj = {
        "type": "model_change", "id": "m1",
        "timestamp": "2026-05-12T22:35:31.129296Z",
        "provider": "anthropic", "modelId": "claude-opus-4-7",
    }
    row = sync._parse_v3_event(obj, session_id="sess-1", node_id="agent+test")
    assert row is not None
    assert row["event_type"] == "model.changed"
    assert row["model"] == "claude-opus-4-7"
    assert row["data"]["provider"] == "anthropic"
    assert row["data"]["modelId"] == "claude-opus-4-7"


def test_v3_message_user_becomes_prompt_submitted():
    """A role=user `message` event must map to prompt.submitted with the
    text content placed at the dot-schema path PR #1132's expander reads
    (data.finalPromptText)."""
    sync = _import_sync()
    obj = {
        "type": "message", "id": "u1",
        "timestamp": "2026-05-12T22:35:31.149296Z",
        "message": {
            "role": "user",
            "content": [{"type": "text", "text": "hello world"}],
        },
    }
    row = sync._parse_v3_event(obj, session_id="sess-1", node_id="agent+test")
    assert row is not None
    assert row["event_type"] == "prompt.submitted"
    assert row["data"]["finalPromptText"] == "hello world"


def test_v3_message_user_with_string_content_works():
    sync = _import_sync()
    obj = {
        "type": "message", "id": "u2",
        "timestamp": "2026-05-12T22:35:31.149296Z",
        "message": {"role": "user", "content": "a plain string"},
    }
    row = sync._parse_v3_event(obj, session_id="sess-1", node_id="n")
    assert row is not None
    assert row["event_type"] == "prompt.submitted"
    assert row["data"]["finalPromptText"] == "a plain string"


def test_v3_message_assistant_extracts_tokens_and_model():
    """A role=assistant `message` event must map to model.completed with
    tokens summed from message.usage and the model name on the row."""
    sync = _import_sync()
    obj = {
        "type": "message", "id": "a1",
        "timestamp": "2026-05-12T22:35:31.159296Z",
        "message": {
            "role": "assistant",
            "content": [{"type": "text", "text": "I will run a tool"}],
            "model": "claude-opus-4-7",
            "provider": "anthropic",
            "usage": {
                "input": 120, "output": 42, "totalTokens": 162,
                "cost": {"input": 0.0018, "output": 0.00315, "total": 0.00495},
            },
            "stopReason": "tool_use",
        },
    }
    row = sync._parse_v3_event(obj, session_id="sess-1", node_id="n")
    assert row is not None
    assert row["event_type"] == "model.completed"
    assert row["model"] == "claude-opus-4-7"
    assert row["token_count"] == 162
    assert row["cost_usd"] == pytest.approx(0.00495)
    assert row["data"]["completionText"] == "I will run a tool"
    # PR #1132's _openclaw_event_tokens reads from this exact path:
    assert row["data"]["promptCache"]["lastCallUsage"]["total"] == 162
    assert row["data"]["promptCache"]["lastCallUsage"]["input"] == 120
    assert row["data"]["promptCache"]["lastCallUsage"]["output"] == 42


def test_v3_message_assistant_extracts_tool_metas():
    """An assistant message containing tool_use blocks must surface them
    on data.toolMetas so PR #1132's expander can render the tool calls."""
    sync = _import_sync()
    obj = {
        "type": "message", "id": "a1",
        "timestamp": "2026-05-12T22:35:31.159296Z",
        "message": {
            "role": "assistant",
            "content": [
                {"type": "text", "text": "I will run a tool"},
                {"type": "tool_use", "id": "toolu_01moat", "name": "bash",
                 "input": {"command": "echo moat"}},
            ],
            "model": "claude-opus-4-7",
            "usage": {"input": 1, "output": 1, "totalTokens": 2},
        },
    }
    row = sync._parse_v3_event(obj, session_id="sess-1", node_id="n")
    assert row is not None
    metas = row["data"].get("toolMetas")
    assert isinstance(metas, list) and len(metas) == 1
    assert metas[0]["name"] == "bash"
    assert metas[0]["input"] == {"command": "echo moat"}


def test_v3_thinking_level_change_is_skipped():
    """Plumbing types must NOT emit DuckDB rows — they pollute analytics."""
    sync = _import_sync()
    obj = {
        "type": "thinking_level_change", "id": "x",
        "timestamp": "2026-05-12T22:35:31.139296Z",
        "thinkingLevel": "off",
    }
    assert sync._parse_v3_event(obj, session_id="s", node_id="n") is None


def test_v3_cwd_change_is_skipped():
    sync = _import_sync()
    obj = {
        "type": "cwd_change", "id": "x",
        "timestamp": "2026-05-12T22:35:31.139296Z",
        "cwd": "/new/path",
    }
    assert sync._parse_v3_event(obj, session_id="s", node_id="n") is None


def test_v3_unknown_event_type_is_skipped_not_raised():
    """Future-proofing: a brand-new v3 underscore type we've never seen
    must be silently dropped (with a debug log) rather than crashing the
    ingest loop or landing as event_type='unknown' rows."""
    sync = _import_sync()
    obj = {
        "type": "future_underscore_type",
        "timestamp": "2026-05-12T22:35:31.139296Z",
        "payload": {},
    }
    # _parse_v3_event drops everything outside _V3_KNOWN_TYPES — but the
    # caller only reaches it via _is_v3_event, which gates on the same set.
    # Either way, no exception.
    assert sync._parse_v3_event(obj, session_id="s", node_id="n") is None


def test_v3_event_without_timestamp_is_skipped():
    """The local store indexes on ts; events without one must drop, not
    fabricate."""
    sync = _import_sync()
    obj = {
        "type": "message",
        "message": {"role": "user", "content": "x"},
    }
    assert sync._parse_v3_event(obj, session_id="s", node_id="n") is None


def test_v3_tool_use_result_becomes_tool_result():
    sync = _import_sync()
    obj = {
        "type": "tool_use_result", "id": "tr1",
        "timestamp": "2026-05-12T22:35:31.169296Z",
        "tool_use_id": "toolu_01moat",
        "content": [{"type": "text", "text": "moat\n"}],
        "is_error": False,
    }
    row = sync._parse_v3_event(obj, session_id="sess-1", node_id="n")
    assert row is not None
    assert row["event_type"] == "tool.result"
    assert row["data"]["output"] == "moat\n"
    assert row["data"]["tool_use_id"] == "toolu_01moat"


# ── Integration: full v3 fixture → DuckDB via _local_ingest_session_batch ──

@pytest.fixture
def isolated_store(tmp_path, monkeypatch):
    """Reload local_store + sync with an isolated DuckDB per test."""
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "events.duckdb"))
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_SECS", "0.05")
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_BATCH", "5")
    import clawmetry.local_store as ls
    import clawmetry.sync as sync
    importlib.reload(ls)
    importlib.reload(sync)
    yield sync, ls
    try:
        ls.get_store().stop(flush=True)
    except Exception:
        pass


def _wait_for_flush(store, timeout=2.0):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if store.health()["ring_depth"] == 0:
            return
        time.sleep(0.02)
    raise AssertionError("flusher did not drain in time")


def _read_jsonl(path: Path) -> list[dict]:
    out: list[dict] = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line:
                out.append(json.loads(line))
    return out


def test_v3_session_file_produces_events(isolated_store):
    """End-to-end: feed the issue-#1135 fixture (7 lines) through the
    daemon ingest path; assert exactly 6 events land in DuckDB (one per
    line, minus the single thinking_level_change plumbing line) with the
    expected dot.separated event_types."""
    sync, ls = isolated_store
    batch = _read_jsonl(FIXTURES / "v3-session.jsonl")
    assert len(batch) == 7, "fixture must mirror the 7-line shape from #1135"

    sync._local_ingest_session_batch(
        batch,
        session_file="3fc28a8b-b0f5-47af-b234-fa2f96db8112.jsonl",
        node_id="agent+test",
        subagent_id=None,
    )
    store = ls.get_store()
    _wait_for_flush(store)

    rows = store.query_events(
        session_id="3fc28a8b-b0f5-47af-b234-fa2f96db8112",
        limit=100,
    )
    # 7 lines − 1 thinking_level_change = 6 events.
    assert len(rows) == 6, f"expected 6 events, got {len(rows)}: {[r['event_type'] for r in rows]}"

    types = sorted(r["event_type"] for r in rows)
    assert types == sorted([
        "session.started",
        "model.changed",
        "prompt.submitted",
        "model.completed",
        "tool.result",
        "model.completed",
    ])


def test_v3_assistant_message_writes_tokens_and_model_to_columns(isolated_store):
    """The first assistant turn in the fixture has totalTokens=162 and
    model=claude-opus-4-7. Assert those land on the row's typed columns
    (not just buried in the JSON blob)."""
    sync, ls = isolated_store
    batch = _read_jsonl(FIXTURES / "v3-session.jsonl")
    sync._local_ingest_session_batch(
        batch, session_file="3fc28a8b-b0f5-47af-b234-fa2f96db8112.jsonl",
        node_id="agent+test", subagent_id=None,
    )
    store = ls.get_store()
    _wait_for_flush(store)

    rows = store.query_events(
        session_id="3fc28a8b-b0f5-47af-b234-fa2f96db8112",
        limit=100,
    )
    completions = [r for r in rows if r["event_type"] == "model.completed"]
    assert len(completions) == 2
    for r in completions:
        assert r["model"] == "claude-opus-4-7"
        assert r["token_count"] == 162


def test_trajectory_schema_still_works_unchanged(isolated_store):
    """Sanity check: feeding the trajectory fixture through the same ingest
    path must NOT regress — the dot.separated event types pass through
    untouched (event_type == obj.type, data == obj)."""
    sync, ls = isolated_store
    batch = _read_jsonl(FIXTURES / "trajectory.jsonl")
    sync._local_ingest_session_batch(
        batch, session_file="trajectory-fixture.jsonl",
        node_id="agent+test", subagent_id=None,
    )
    store = ls.get_store()
    _wait_for_flush(store)

    rows = store.query_events(session_id="trajectory-fixture", limit=100)
    assert len(rows) == 5
    types = sorted(r["event_type"] for r in rows)
    assert types == sorted([
        "session.started",
        "prompt.submitted",
        "trace.artifacts",
        "model.completed",
        "session.ended",
    ])


def test_mixed_batch_routes_per_event(isolated_store):
    """A single batch that mixes v3 underscore + trajectory dot lines
    (e.g. when a daemon tail crosses a checkpoint switchover) must route
    each event independently — no batch-wide "is this v3?" classifier."""
    sync, ls = isolated_store
    batch = [
        # v3 line
        {"type": "session", "version": 3, "id": "mixed",
         "timestamp": "2026-05-12T22:00:00Z", "cwd": "/tmp"},
        # trajectory line
        {"type": "trace.artifacts", "timestamp": "2026-05-12T22:00:01Z",
         "modelId": "claude-opus-4-7",
         "data": {"finalPromptText": "hi", "assistantTexts": ["yo"]}},
    ]
    sync._local_ingest_session_batch(
        batch, session_file="mixed.jsonl", node_id="agent+test",
        subagent_id=None,
    )
    store = ls.get_store()
    _wait_for_flush(store)

    rows = store.query_events(session_id="mixed", limit=100)
    types = sorted(r["event_type"] for r in rows)
    assert types == ["session.started", "trace.artifacts"]
