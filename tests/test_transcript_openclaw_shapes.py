"""Regression tests for `_try_local_store_transcript` (#1129 bug 3).

Before the fix, the helper assumed every event row in DuckDB looked like an
Anthropic message (``{role, content, usage, tool_calls}``) — but OpenClaw
writes a very different shape (``{type: "<ns>.<action>", data: {...}}``).
Result: every OpenClaw event rendered with ``role="trace.artifacts"``,
``content=""``, and ``tokens=0``.

This file pins the post-fix behaviour by feeding synthesized OpenClaw events
through the helper and asserting that:

* ``prompt.submitted`` produces a single user turn.
* ``trace.artifacts`` may emit user / assistant / tool turns depending on
  which fields its ``data`` block carries.
* ``model.completed`` produces an assistant turn.
* ``tool.call`` / ``tool.result`` produce tool turns.
* Plumbing events (``session.ended``, ``context.compiled``,
  ``agent.heartbeat``) emit NOTHING — no debug-typed roles, no empty
  bodies.
* Tokens are summed from ``data.promptCache.lastCallUsage`` and the model
  is taken from ``modelId``.
* The legacy Anthropic shape still works (mixed-shape sessions, too).
"""

from __future__ import annotations

import importlib
import uuid

import pytest


@pytest.fixture
def env(tmp_path, monkeypatch):
    """Per-test isolated DuckDB store + freshly imported routes module."""
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "events.duckdb"))
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_SECS", "0.02")
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_BATCH", "1")
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_READ", "1")

    import clawmetry.local_store as ls
    importlib.reload(ls)
    import routes.sessions as sessions_mod
    importlib.reload(sessions_mod)

    store = ls.get_store()
    yield store, sessions_mod
    try:
        store.stop(flush=True)
    except Exception:
        pass


def _wait(store, timeout=2.0):
    import time
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if store.health()["ring_depth"] == 0:
            return
        time.sleep(0.01)
    raise AssertionError("flusher did not drain")


def _ingest(store, sid, data, *, ts="2026-05-13T10:00:00Z", event_type="brain"):
    store.ingest({
        "id": str(uuid.uuid4()),
        "node_id": "agent+test",
        "agent_id": "main",
        "session_id": sid,
        "event_type": event_type,
        "ts": ts,
        "data": data,
    })


# ── unit-level tests on the pure helpers ──────────────────────────────────


def test_is_openclaw_event_discriminator():
    from routes.sessions import _is_openclaw_event
    assert _is_openclaw_event({"type": "trace.artifacts", "data": {}})
    assert _is_openclaw_event({"type": "prompt.submitted"})
    # Anthropic shape — has role.
    assert not _is_openclaw_event({"role": "user", "content": "hi"})
    # No type at all.
    assert not _is_openclaw_event({"content": "hi"})
    # Non-dotted type (legacy "tool_result" etc.) — keep on Anthropic path.
    assert not _is_openclaw_event({"type": "tool_result"})


def test_openclaw_event_tokens_prefers_per_call_usage():
    from routes.sessions import _openclaw_event_tokens
    data = {"promptCache": {"lastCallUsage": {"input": 100, "output": 50, "total": 150}}}
    assert _openclaw_event_tokens(data) == 150
    # Fallback to input+output when total missing.
    data = {"promptCache": {"lastCallUsage": {"input": 100, "output": 50}}}
    assert _openclaw_event_tokens(data) == 150
    # Fallback further to data.usage when no promptCache.
    data = {"usage": {"input_tokens": 7, "output_tokens": 3}}
    assert _openclaw_event_tokens(data) == 10
    assert _openclaw_event_tokens({}) == 0


# ── end-to-end tests through the helper ───────────────────────────────────


def test_prompt_submitted_produces_user_turn(env):
    store, sessions_mod = env
    sid = "sess-prompt"
    _ingest(store, sid, {
        "type": "prompt.submitted",
        "data": {"finalPromptText": "What is 2+2?"},
    })
    _wait(store)
    result = sessions_mod._try_local_store_transcript(sid)
    assert result is not None
    msgs = result["messages"]
    assert len(msgs) == 1
    assert msgs[0]["role"] == "user"
    assert msgs[0]["content"] == "What is 2+2?"


def test_trace_artifacts_emits_user_assistant_and_tool(env):
    store, sessions_mod = env
    sid = "sess-trace"
    _ingest(store, sid, {
        "type": "trace.artifacts",
        "modelApi": "anthropic-messages",
        "modelId": "claude-opus-4-7",
        "provider": "anthropic",
        "data": {
            "finalPromptText": "Read README and summarise.",
            "finalStatus": "success",
            "promptCache": {"lastCallUsage": {"input": 1234, "output": 567, "total": 1801}},
            "assistantTexts": ["Sure — here is the summary."],
            "toolMetas": [
                {"name": "Read", "input": {"path": "/tmp/README.md"}, "output": "# Title"},
            ],
        },
    })
    _wait(store)
    result = sessions_mod._try_local_store_transcript(sid)
    msgs = result["messages"]
    roles = [m["role"] for m in msgs]
    assert "user" in roles
    assert "assistant" in roles
    assert "tool" in roles
    # Model picked up from modelId (NOT from a missing 'model' field).
    assert result["model"] == "claude-opus-4-7"
    # Tokens summed from promptCache.lastCallUsage.total.
    assert result["totalTokens"] == 1801
    # No turn carries the debug type "trace.artifacts" as a role.
    assert "trace.artifacts" not in roles
    # Tool turn body shows the tool name.
    tool_msg = next(m for m in msgs if m["role"] == "tool")
    assert "Read" in tool_msg["content"]


def test_trace_artifacts_empty_data_emits_nothing(env):
    """A trace with no prompt/assistant/tool content should yield zero turns
    rather than a phantom 'trace.artifacts' message."""
    store, sessions_mod = env
    sid = "sess-empty-trace"
    _ingest(store, sid, {
        "type": "trace.artifacts",
        "modelId": "claude-opus-4-7",
        "data": {"finalStatus": "success"},
    })
    _wait(store)
    result = sessions_mod._try_local_store_transcript(sid)
    assert result is not None
    assert result["messages"] == []


def test_model_completed_emits_assistant(env):
    store, sessions_mod = env
    sid = "sess-model"
    _ingest(store, sid, {
        "type": "model.completed",
        "modelId": "claude-opus-4-7",
        "data": {"completionText": "Final answer: 4"},
    })
    _wait(store)
    result = sessions_mod._try_local_store_transcript(sid)
    msgs = result["messages"]
    assert len(msgs) == 1
    assert msgs[0]["role"] == "assistant"
    assert "Final answer" in msgs[0]["content"]


def test_model_completed_with_assistant_texts_list(env):
    store, sessions_mod = env
    sid = "sess-model-list"
    _ingest(store, sid, {
        "type": "model.completed",
        "modelId": "claude-opus-4-7",
        "data": {"assistantTexts": ["part one ", "part two"]},
    })
    _wait(store)
    result = sessions_mod._try_local_store_transcript(sid)
    assert len(result["messages"]) == 1
    assert result["messages"][0]["role"] == "assistant"
    assert "part one" in result["messages"][0]["content"]
    assert "part two" in result["messages"][0]["content"]


def test_tool_call_and_result(env):
    store, sessions_mod = env
    sid = "sess-tools"
    _ingest(store, sid, {
        "type": "tool.call",
        "data": {"name": "Bash", "input": {"cmd": "ls"}},
    }, ts="2026-05-13T10:00:01Z")
    _ingest(store, sid, {
        "type": "tool.result",
        "data": {"name": "Bash", "output": "file1\nfile2"},
    }, ts="2026-05-13T10:00:02Z")
    _wait(store)
    result = sessions_mod._try_local_store_transcript(sid)
    msgs = result["messages"]
    assert len(msgs) == 2
    assert all(m["role"] == "tool" for m in msgs)
    assert any("Bash" in m["content"] and "ls" in m["content"] for m in msgs)
    assert any("file1" in m["content"] for m in msgs)


def test_plumbing_events_emit_nothing(env):
    """session.ended, session.started, context.compiled, agent.heartbeat —
    NONE of these should produce a transcript turn."""
    store, sessions_mod = env
    sid = "sess-plumb"
    for et in ("session.started", "session.ended", "context.compiled", "agent.heartbeat"):
        _ingest(store, sid, {"type": et, "data": {"status": "ok"}})
    _wait(store)
    result = sessions_mod._try_local_store_transcript(sid)
    assert result is not None
    assert result["messages"] == []
    # And no debug-typed role leaks through.
    for m in result["messages"]:
        assert "." not in m["role"]


def test_unknown_openclaw_event_does_not_emit_garbage(env):
    """Unknown <ns>.<action> types should be silently skipped — never emit
    a turn whose role is 'foo.bar'."""
    store, sessions_mod = env
    sid = "sess-unknown"
    _ingest(store, sid, {"type": "foo.bar", "data": {"content": "anything"}})
    _wait(store)
    result = sessions_mod._try_local_store_transcript(sid)
    assert result["messages"] == []


def test_anthropic_shape_still_works(env):
    """Mixed sessions: legacy Anthropic-style rows + OpenClaw rows must both
    surface their content."""
    store, sessions_mod = env
    sid = "sess-mixed"
    _ingest(store, sid, {
        "role": "user", "content": "hello", "usage": {"input_tokens": 5, "output_tokens": 0},
    }, ts="2026-05-13T10:00:00Z")
    _ingest(store, sid, {
        "role": "assistant", "content": "hi back!",
        "usage": {"input_tokens": 5, "output_tokens": 3, "total_tokens": 8},
        "model": "claude-sonnet-4-5",
    }, ts="2026-05-13T10:00:01Z")
    _ingest(store, sid, {
        "type": "trace.artifacts",
        "modelId": "claude-opus-4-7",
        "data": {
            "assistantTexts": ["second turn"],
            "promptCache": {"lastCallUsage": {"input": 10, "output": 5, "total": 15}},
        },
    }, ts="2026-05-13T10:00:02Z")
    _wait(store)
    result = sessions_mod._try_local_store_transcript(sid)
    msgs = result["messages"]
    contents = " ".join(m["content"] for m in msgs)
    assert "hello" in contents
    assert "hi back!" in contents
    assert "second turn" in contents
    # Tokens accumulate across both shapes (Anthropic 5 + Anthropic 8 + OpenClaw 15).
    assert result["totalTokens"] == 5 + 8 + 15


def test_empty_store_returns_none(env):
    """Returning None lets the JSONL fallback take over for fresh installs."""
    _store, sessions_mod = env
    assert sessions_mod._try_local_store_transcript("nonexistent-session") is None
