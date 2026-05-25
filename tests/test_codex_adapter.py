"""Tests for CodexAdapter (clawmetry/adapters/codex.py).

Validates against a real (redacted) Codex CLI rollout fixture, extended with
the documented line types a minimal capture lacked (assistant message,
reasoning, function_call, function_call_output, token_count). Wire shapes match
openai/codex codex-rs/protocol/src/{models,protocol}.rs. See the fixture's
REAL/PROVENANCE.md for capture + redaction details.

Covers:
  - detect() reports detected + the right session_count, never raises
  - list_sessions() returns the session newest-first, with model + provider
    from session_meta/turn_context, message_count, and timestamps > 0
  - token usage is read off the real token_count event_msg (COST is honest)
  - list_events() yields the expected ordered event types
  - the adapter never raises on a garbage / unparseable rollout file
"""
from __future__ import annotations

import os

import pytest

from clawmetry.adapters.base import Capability
from clawmetry.adapters.codex import CodexAdapter

_FIXTURE_SESSIONS_ROOT = os.path.join(
    os.path.dirname(__file__),
    "fixtures",
    "runtimes",
    "codex",
    "sessions",
)

_SESSION_UUID = "019e28c2-6d89-7f22-95a4-3c619a6a8046"


@pytest.fixture
def adapter() -> CodexAdapter:
    return CodexAdapter(sessions_root=_FIXTURE_SESSIONS_ROOT)


# -- detect ------------------------------------------------------------------


def test_detect_detected_and_counts(adapter):
    result = adapter.detect()
    assert result.detected is True
    assert result.running is False
    assert result.name == "codex"
    assert result.display_name == "Codex"
    # One rollout file in the fixture tree.
    assert result.session_count == 1
    assert result.meta["sessionsRoot"] == _FIXTURE_SESSIONS_ROOT


def test_detect_false_when_dir_absent(tmp_path, monkeypatch):
    """detect() must not raise and reports detected=False with no home."""
    monkeypatch.setenv("CODEX_HOME", str(tmp_path / "no-such-codex"))
    a = CodexAdapter(sessions_root=str(tmp_path / "no-such-sessions"))
    result = a.detect()
    assert result.detected is False
    assert result.session_count == 0


def test_detect_honors_codex_home(tmp_path, monkeypatch):
    """With no explicit sessions_root, CODEX_HOME/sessions is used."""
    home = tmp_path / "codex-home"
    (home / "sessions").mkdir(parents=True)
    monkeypatch.setenv("CODEX_HOME", str(home))
    a = CodexAdapter()
    assert a.sessions_root == str(home / "sessions")
    assert a.detect().detected is True


# -- list_sessions -----------------------------------------------------------


def test_list_sessions_basic_shape(adapter):
    sessions = adapter.list_sessions()
    assert len(sessions) == 1
    s = sessions[0]
    # id is the UUID parsed out of the rollout filename.
    assert s.id == _SESSION_UUID
    assert s.agent == "codex"
    # model from turn_context, provider from session_meta.
    assert s.model == "gpt-5.4"
    assert s.source == "openai"
    # cli_version surfaced in extra.
    assert s.extra["cliVersion"] == "0.125.0"


def test_list_sessions_message_count_and_timestamps(adapter):
    s = adapter.list_sessions()[0]
    # Four response_item `message` lines (2 user/dev real + 1 user real +
    # 1 appended assistant) in the fixture.
    assert s.message_count == 4
    # Timestamps parse to real epoch seconds, not 0.
    assert s.started_at > 0
    assert s.ended_at is not None and s.ended_at > 0
    assert s.ended_at >= s.started_at


def test_list_sessions_title_from_user_prompt(adapter):
    s = adapter.list_sessions()[0]
    # The human prompt (not the <environment_context> boilerplate) becomes title.
    assert s.title.startswith("Reply exactly with: hi")
    assert s.display_name.startswith("Reply exactly with: hi")


def test_list_sessions_tokens_from_token_count_event(adapter):
    s = adapter.list_sessions()[0]
    # Read off the real token_count event_msg in the fixture.
    assert s.total_tokens == 1235
    assert s.input_tokens == 1200
    assert s.output_tokens == 35
    assert s.cache_read_tokens == 800
    assert s.reasoning_tokens == 12
    # Codex writes tokens but not USD, so cost stays unknown.
    assert s.cost_usd is None
    assert s.cost_status == "tokens_only"
    assert s.extra["tokensOnDisk"] is True


# -- list_events -------------------------------------------------------------


def test_list_events_ordered_types(adapter):
    events = adapter.list_events(_SESSION_UUID)
    types = [e.type for e in events]
    # response_item lines, in file order:
    #   developer message, user message, user message (3 real),
    #   reasoning, function_call, function_call_output, assistant message.
    assert types == [
        "message",
        "message",
        "message",
        "thinking",
        "tool_call",
        "tool_result",
        "message",
    ]
    # Every event carries the native session id and a real timestamp.
    for e in events:
        assert e.session_id == _SESSION_UUID
        assert e.agent == "codex"
        assert e.ts > 0


def test_list_events_tool_call_details(adapter):
    events = adapter.list_events(_SESSION_UUID)
    tool_call = next(e for e in events if e.type == "tool_call")
    assert tool_call.tool_name == "shell"
    assert tool_call.role == "assistant"
    assert tool_call.tool_calls[0]["id"] == "call_abc123"
    assert "echo" in tool_call.tool_calls[0]["arguments"]

    tool_result = next(e for e in events if e.type == "tool_result")
    # function_call_output payload uses the {content: "..."} variant.
    assert tool_result.content.strip() == "hi"
    assert tool_result.extra["callId"] == "call_abc123"


def test_list_events_assistant_message_text(adapter):
    events = adapter.list_events(_SESSION_UUID)
    assistant = next(
        e for e in events if e.type == "message" and e.role == "assistant"
    )
    # output_text content flattened to plain text.
    assert assistant.content == "hi"


def test_list_events_unknown_session_is_empty(adapter):
    assert adapter.list_events("no-such-session") == []


# -- capabilities ------------------------------------------------------------


def test_capabilities(adapter):
    caps = adapter.capabilities()
    assert Capability.SESSIONS in caps
    assert Capability.EVENTS in caps
    # COST is advertised because token usage is genuinely on disk.
    assert Capability.COST in caps


# -- robustness --------------------------------------------------------------


def test_never_raises_on_garbage_file(tmp_path):
    """A non-JSON / truncated rollout must not crash detect/list/events."""
    root = tmp_path / "sessions" / "2026" / "05" / "15"
    root.mkdir(parents=True)
    bad = root / "rollout-2026-05-15T00-00-00-deadbeef-0000-0000-0000-000000000000.jsonl"
    bad.write_text("not json at all\n{broken: ]\n\x00\x01garbage\n")

    a = CodexAdapter(sessions_root=str(tmp_path / "sessions"))
    # detect counts the file but does not parse it.
    assert a.detect().detected is True
    # list_sessions tolerates the garbage and still returns a Session.
    sessions = a.list_sessions()
    assert len(sessions) == 1
    # list_events on the garbage rollout yields nothing, no exception.
    assert a.list_events("deadbeef-0000-0000-0000-000000000000") == []


def test_empty_rollout_reports_zero_tokens(tmp_path):
    """A session with no token_count line honestly reports zero tokens."""
    root = tmp_path / "sessions" / "2026" / "05" / "15"
    root.mkdir(parents=True)
    f = root / "rollout-2026-05-15T00-00-00-aaaaaaaa-0000-0000-0000-000000000000.jsonl"
    f.write_text(
        '{"timestamp":"2026-05-15T00:00:00.000Z","type":"session_meta",'
        '"payload":{"id":"aaaaaaaa-0000-0000-0000-000000000000",'
        '"model_provider":"openai","cli_version":"0.125.0"}}\n'
    )
    a = CodexAdapter(sessions_root=str(tmp_path / "sessions"))
    s = a.list_sessions()[0]
    assert s.total_tokens == 0
    assert s.cost_status == "unavailable"
    assert s.extra["tokensOnDisk"] is False
