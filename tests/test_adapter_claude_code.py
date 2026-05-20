"""Tests for ClaudeCodeAdapter span ingestion (issue #1011).

Validates:
  - llm.call + tool child spans are written for a basic assistant turn
  - thinking blocks produce a ``thinking`` span with kind=INTERNAL
  - Task tool_use becomes ``agent.spawn`` rather than ``tool.Task``
  - detect() returns False when the projects directory is absent
  - tool-result-only user turns don't create a new llm.call span
"""
from __future__ import annotations

import importlib
import json
import uuid

import pytest


# ── fixtures ────────────────────────────────────────────────────────────────────────────


@pytest.fixture
def store(tmp_path, monkeypatch):
    """Fresh isolated DuckDB store per test."""
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "events.duckdb"))
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_SECS", "0.05")
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_BATCH", "5")
    import clawmetry.local_store as ls

    importlib.reload(ls)
    ls._reset_singleton_for_tests()
    s = ls.get_store()
    yield s
    try:
        s.stop(flush=True)
    except Exception:
        pass
    ls._reset_singleton_for_tests()


def _write_jsonl(path, lines):
    path.write_text("\n".join(json.dumps(o) for o in lines) + "\n")


def _session_id():
    return "test-sess-" + uuid.uuid4().hex[:8]


# ── tests ────────────────────────────────────────────────────────────────────────────────


def test_ingest_spans_basic_llm_and_tool(store, tmp_path):
    """Assistant turn with a tool_use block → llm.call + tool.<name> spans."""
    from clawmetry.adapters.claude_code import ClaudeCodeAdapter

    session_id = _session_id()
    tool_uid = "tu_" + uuid.uuid4().hex[:8]
    lines = [
        {
            "type": "user",
            "uuid": uuid.uuid4().hex,
            "timestamp": "2026-05-11T10:00:00.000Z",
            "message": {"role": "user", "content": "Write a file"},
        },
        {
            "type": "assistant",
            "uuid": uuid.uuid4().hex,
            "timestamp": "2026-05-11T10:00:05.000Z",
            "message": {
                "role": "assistant",
                "model": "claude-opus-4-7",
                "content": [
                    {"type": "text", "text": "Sure!"},
                    {"type": "tool_use", "id": tool_uid, "name": "Write", "input": {}},
                ],
                "usage": {"input_tokens": 100, "output_tokens": 40},
            },
        },
    ]
    path = tmp_path / f"{session_id}.jsonl"
    _write_jsonl(path, lines)

    adapter = ClaudeCodeAdapter()
    n = adapter.ingest_spans(str(path), session_id, store)

    assert n == 2
    spans = store.query_spans(session_id=session_id)
    names = {s["name"] for s in spans}
    assert "llm.call" in names
    assert "tool.Write" in names

    llm = next(s for s in spans if s["name"] == "llm.call")
    assert llm["model"] == "claude-opus-4-7"
    assert llm["tokens_input"] == 100
    assert llm["tokens_output"] == 40

    tool_span = next(s for s in spans if s["name"] == "tool.Write")
    assert tool_span["parent_span_id"] == llm["span_id"]


def test_ingest_spans_thinking_block(store, tmp_path):
    """thinking content block → thinking span with kind=INTERNAL."""
    from clawmetry.adapters.claude_code import ClaudeCodeAdapter

    session_id = _session_id()
    lines = [
        {
            "type": "user",
            "uuid": "u1",
            "timestamp": "2026-05-11T10:00:00Z",
            "message": {"role": "user", "content": "Think hard"},
        },
        {
            "type": "assistant",
            "uuid": "a1",
            "timestamp": "2026-05-11T10:00:04Z",
            "message": {
                "role": "assistant",
                "model": "claude-opus-4-7",
                "content": [
                    {"type": "thinking", "id": "th1", "thinking": "Hmm..."},
                    {"type": "text", "text": "Done."},
                ],
                "usage": {"input_tokens": 50, "output_tokens": 20},
            },
        },
    ]
    path = tmp_path / f"{session_id}.jsonl"
    _write_jsonl(path, lines)

    adapter = ClaudeCodeAdapter()
    n = adapter.ingest_spans(str(path), session_id, store)

    assert n == 2  # llm.call + thinking
    spans = store.query_spans(session_id=session_id)
    names = {s["name"] for s in spans}
    assert "thinking" in names

    thinking_span = next(s for s in spans if s["name"] == "thinking")
    assert thinking_span["kind"] == "INTERNAL"
    llm_span = next(s for s in spans if s["name"] == "llm.call")
    assert thinking_span["parent_span_id"] == llm_span["span_id"]


def test_task_tool_becomes_agent_spawn(store, tmp_path):
    """tool_use with name=Task maps to agent.spawn, not tool.Task."""
    from clawmetry.adapters.claude_code import ClaudeCodeAdapter

    session_id = _session_id()
    lines = [
        {
            "type": "user",
            "uuid": "u2",
            "timestamp": "2026-05-11T10:00:00Z",
            "message": {"role": "user", "content": "Spawn a subagent"},
        },
        {
            "type": "assistant",
            "uuid": "a2",
            "timestamp": "2026-05-11T10:00:05Z",
            "message": {
                "role": "assistant",
                "model": "claude-opus-4-7",
                "content": [
                    {"type": "tool_use", "id": "task1", "name": "Task", "input": {}},
                ],
                "usage": {"input_tokens": 80, "output_tokens": 10},
            },
        },
    ]
    path = tmp_path / f"{session_id}.jsonl"
    _write_jsonl(path, lines)

    adapter = ClaudeCodeAdapter()
    adapter.ingest_spans(str(path), session_id, store)

    spans = store.query_spans(session_id=session_id)
    names = {s["name"] for s in spans}
    assert "agent.spawn" in names
    assert "tool.Task" not in names


def test_detect_false_when_no_projects_dir(tmp_path, monkeypatch):
    """detect() returns detected=False when the projects directory is absent."""
    from clawmetry.adapters.claude_code import ClaudeCodeAdapter

    monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(tmp_path / "no-such-dir"))
    adapter = ClaudeCodeAdapter()
    result = adapter.detect()
    assert result.detected is False


def test_tool_result_user_turn_does_not_advance_llm_span(store, tmp_path):
    """A tool-result-only user turn should not start a new llm.call span."""
    from clawmetry.adapters.claude_code import ClaudeCodeAdapter

    session_id = _session_id()
    lines = [
        {
            "type": "user",
            "uuid": "u3",
            "timestamp": "2026-05-11T10:00:00Z",
            "message": {"role": "user", "content": "Do the thing"},
        },
        {
            "type": "assistant",
            "uuid": "a3",
            "timestamp": "2026-05-11T10:00:03Z",
            "message": {
                "role": "assistant",
                "model": "claude-opus-4-7",
                "content": [{"type": "tool_use", "id": "t3", "name": "bash", "input": {}}],
                "usage": {"input_tokens": 60, "output_tokens": 15},
            },
        },
        # tool-result plumbing — should NOT produce a new llm.call
        {
            "type": "user",
            "uuid": "u4",
            "timestamp": "2026-05-11T10:00:04Z",
            "message": {
                "role": "user",
                "content": [{"type": "tool_result", "tool_use_id": "t3", "content": "ok"}],
            },
        },
    ]
    path = tmp_path / f"{session_id}.jsonl"
    _write_jsonl(path, lines)

    adapter = ClaudeCodeAdapter()
    n = adapter.ingest_spans(str(path), session_id, store)

    spans = store.query_spans(session_id=session_id)
    llm_spans = [s for s in spans if s["name"] == "llm.call"]
    assert len(llm_spans) == 1, f"Expected 1 llm.call span, got {len(llm_spans)}"
