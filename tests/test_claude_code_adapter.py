"""Tests for ClaudeCodeAdapter list_sessions + list_events.

Validates the unified Session / Event mapping against a representative
Claude Code transcript fixture (real on-disk JSONL shape, REDACTED content).
The fixture lives at::

    tests/fixtures/runtimes/claude_code/projects/<enc-cwd>/<uuid>.jsonl

and is pointed at via the ``CLAUDE_CONFIG_DIR`` env var that the adapter
honours (the fixture base contains a ``projects/`` subdirectory).

Coverage:
  - list_sessions() reads model, message_count, token totals, timestamps
  - list_events() maps user / assistant text -> message, thinking -> thinking,
    tool_use -> tool_call (name + input), tool_result -> tool_result
  - events come back in chronological order
  - usage tokens ride the first event of each assistant turn
  - unknown session id -> [] (never raises)
"""
from __future__ import annotations

import os

import pytest

_FIXTURE_BASE = os.path.join(
    os.path.dirname(__file__),
    "fixtures",
    "runtimes",
    "claude_code",
)
_SESSION_ID = "11111111-2222-3333-4444-555555555555"


@pytest.fixture
def adapter(monkeypatch):
    # The adapter resolves ~/.claude (or CLAUDE_CONFIG_DIR) then appends
    # "projects/". Point it at the fixture base so it finds the fixture dir.
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", _FIXTURE_BASE)
    from clawmetry.adapters.claude_code import ClaudeCodeAdapter

    return ClaudeCodeAdapter()


# ── detect / list_sessions ───────────────────────────────────────────────────


def test_detect_finds_fixture(adapter):
    result = adapter.detect()
    assert result.detected is True
    assert result.session_count == 1


def test_list_sessions_summary(adapter):
    sessions = adapter.list_sessions(limit=10)
    assert len(sessions) == 1
    s = sessions[0]
    assert s.agent == "claude_code"
    assert s.id == _SESSION_ID
    assert s.model == "claude-opus-4-7"
    # 1 user prompt + 2 assistant turns (tool-result-only user turn excluded)
    assert s.message_count == 3
    assert s.input_tokens == 1200 + 1400
    assert s.output_tokens == 90 + 45
    assert s.total_tokens == s.input_tokens + s.output_tokens
    assert s.cache_read_tokens == 8000 + 8300
    assert s.started_at > 0
    assert s.ended_at is not None and s.ended_at >= s.started_at


# ── list_events ──────────────────────────────────────────────────────────────


def test_list_events_types_and_order(adapter):
    events = adapter.list_events(_SESSION_ID, limit=500)
    types = [e.type for e in events]
    # user msg -> thinking -> tool_call -> tool_result -> assistant msg
    assert types == ["message", "thinking", "tool_call", "tool_result", "message"]

    # chronological by timestamp
    ts = [e.ts for e in events if e.ts]
    assert ts == sorted(ts)

    # every event is tagged for this agent + session, with a non-empty id
    for e in events:
        assert e.agent == "claude_code"
        assert e.session_id == _SESSION_ID
        assert e.id


def test_list_events_user_message(adapter):
    events = adapter.list_events(_SESSION_ID)
    user_msg = events[0]
    assert user_msg.type == "message"
    assert user_msg.role == "user"
    assert "REDACTED" in user_msg.content


def test_list_events_thinking(adapter):
    events = adapter.list_events(_SESSION_ID)
    thinking = next(e for e in events if e.type == "thinking")
    assert thinking.role == "assistant"
    assert "REDACTED" in thinking.content


def test_list_events_tool_call_carries_name_and_input(adapter):
    events = adapter.list_events(_SESSION_ID)
    call = next(e for e in events if e.type == "tool_call")
    assert call.tool_name == "Bash"
    assert call.id == "toolu_aaa111"
    assert call.tool_calls and call.tool_calls[0]["name"] == "Bash"
    assert call.tool_calls[0]["input"] is not None


def test_list_events_tool_result(adapter):
    events = adapter.list_events(_SESSION_ID)
    result = next(e for e in events if e.type == "tool_result")
    assert result.role == "tool"
    assert "REDACTED" in result.content
    assert result.extra.get("toolUseId") == "toolu_aaa111"
    assert result.extra.get("isError") is False


def test_list_events_usage_tokens_on_first_turn_event(adapter):
    events = adapter.list_events(_SESSION_ID)
    # First assistant turn's first event (thinking) carries that turn's usage.
    thinking = next(e for e in events if e.type == "thinking")
    assert thinking.tokens == 1200 + 90
    assert thinking.extra.get("inputTokens") == 1200
    assert thinking.extra.get("outputTokens") == 90
    # The tool_call in the SAME turn must not double-count tokens.
    call = next(e for e in events if e.type == "tool_call")
    assert call.tokens == 0
    # Final assistant message turn carries its own usage.
    final = events[-1]
    assert final.type == "message" and final.role == "assistant"
    assert final.tokens == 1400 + 45


def test_list_events_respects_limit(adapter):
    events = adapter.list_events(_SESSION_ID, limit=2)
    assert len(events) == 2


def test_list_events_unknown_session_returns_empty(adapter):
    assert adapter.list_events("no-such-session-id") == []


def test_list_events_missing_projects_dir_returns_empty(tmp_path, monkeypatch):
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(tmp_path / "nope"))
    from clawmetry.adapters.claude_code import ClaudeCodeAdapter

    assert ClaudeCodeAdapter().list_events(_SESSION_ID) == []
