"""Tests for PicoClawAdapter (clawmetry/adapters/picoclaw.py).

Validates against correct-shape fixtures of flat ``providers.Message``
JSONL (the real PicoClaw on-disk format, NOT OpenClaw's v3 envelope):

  - detect() reports detected + the right session_count, never raises
  - list_sessions() returns both fixtures, newest first, with the model
    provider-stripped for display but the full model kept in extra
  - message_count comes from the .meta.json sidecar
  - total_tokens == 0 and cost_usd is None (PicoClaw carries no on-disk
    token / cost data — this test documents that reality)
  - list_events() yields the expected ordered event types, including the
    tool_call derived from an assistant message's tool_calls array
  - the adapter never raises on a garbage / unparseable session file
"""
from __future__ import annotations

import os

import pytest

from clawmetry.adapters.base import Capability
from clawmetry.adapters.picoclaw import PicoClawAdapter

_FIXTURE_SESSIONS_DIR = os.path.join(
    os.path.dirname(__file__),
    "fixtures",
    "runtimes",
    "picoclaw",
    "workspace",
    "sessions",
)


@pytest.fixture
def adapter() -> PicoClawAdapter:
    return PicoClawAdapter(sessions_dir=_FIXTURE_SESSIONS_DIR)


# -- detect ------------------------------------------------------------------


def test_detect_detected_and_counts(adapter):
    result = adapter.detect()
    assert result.detected is True
    assert result.running is False
    assert result.name == "picoclaw"
    assert result.display_name == "PicoClaw"
    # Two .jsonl fixtures present.
    assert result.session_count == 2
    assert result.meta["sessionsDir"] == _FIXTURE_SESSIONS_DIR


def test_detect_false_when_dir_absent(tmp_path, monkeypatch):
    """detect() must not raise and reports detected=False with no home."""
    monkeypatch.setenv("PICOCLAW_HOME", str(tmp_path / "no-such-picoclaw"))
    a = PicoClawAdapter(sessions_dir=str(tmp_path / "no-such-sessions"))
    result = a.detect()
    assert result.detected is False
    assert result.session_count == 0


# -- list_sessions -----------------------------------------------------------


def test_list_sessions_count_and_order(adapter):
    sessions = adapter.list_sessions()
    assert len(sessions) == 2
    # Newest first: hosted session (11:30) precedes ollama session (10:00).
    assert sessions[0].id == "sess-hosted-def456"
    assert sessions[1].id == "sess-ollama-abc123"


def test_list_sessions_model_provider_stripped_and_full_kept(adapter):
    by_id = {s.id: s for s in adapter.list_sessions()}

    ollama = by_id["sess-ollama-abc123"]
    # Display model strips the provider prefix.
    assert ollama.model == "llama3.2:3b"
    # Full provider-qualified model is preserved in extra.
    assert ollama.extra["modelFull"] == "ollama/llama3.2:3b"
    # Source is the provider prefix.
    assert ollama.source == "ollama"

    hosted = by_id["sess-hosted-def456"]
    # Hosted model has no provider prefix — unchanged.
    assert hosted.model == "gpt-5.4"
    assert hosted.extra["modelFull"] == "gpt-5.4"
    assert hosted.source == ""


def test_list_sessions_message_count_from_meta(adapter):
    by_id = {s.id: s for s in adapter.list_sessions()}
    assert by_id["sess-ollama-abc123"].message_count == 4
    assert by_id["sess-hosted-def456"].message_count == 2


def test_list_sessions_title_and_started_ended(adapter):
    by_id = {s.id: s for s in adapter.list_sessions()}
    ollama = by_id["sess-ollama-abc123"]
    assert ollama.title == "List directory contents"
    assert ollama.display_name == "List directory contents"
    assert ollama.started_at > 0
    assert ollama.ended_at is not None
    assert ollama.ended_at >= ollama.started_at


def test_list_sessions_tokens_and_cost_unavailable(adapter):
    """PicoClaw carries NO token / cost data on disk — documented here."""
    for s in adapter.list_sessions():
        assert s.total_tokens == 0
        assert s.input_tokens == 0
        assert s.output_tokens == 0
        assert s.cost_usd is None
        assert s.cost_status == "unavailable"
        assert s.extra.get("tokensUnavailable") is True


# -- list_events -------------------------------------------------------------


def test_list_events_ordered_types_with_tool_call(adapter):
    events = adapter.list_events("sess-ollama-abc123")
    types = [(e.type, e.role) for e in events]

    # Expected chronological order:
    #   user message
    #   assistant thinking (reasoning_content)
    #   assistant message
    #   assistant tool_call (shell)
    #   tool_result
    #   final assistant message
    assert types == [
        ("message", "user"),
        ("thinking", "assistant"),
        ("message", "assistant"),
        ("tool_call", "assistant"),
        ("tool_result", "tool"),
        ("message", "assistant"),
    ]

    # The tool_call event surfaces the tool name + the {id,name,arguments}.
    tool_call = next(e for e in events if e.type == "tool_call")
    assert tool_call.tool_name == "shell"
    assert tool_call.tool_calls[0]["id"] == "call_001"
    assert tool_call.tool_calls[0]["name"] == "shell"
    assert "ls -la" in tool_call.tool_calls[0]["arguments"]

    # The tool_result carries the originating tool_call_id.
    tool_result = next(e for e in events if e.type == "tool_result")
    assert tool_result.extra["toolCallId"] == "call_001"

    # Events are chronologically ordered (non-decreasing timestamps).
    ts_list = [e.ts for e in events if e.ts]
    assert ts_list == sorted(ts_list)


def test_list_events_empty_for_unknown_session(adapter):
    assert adapter.list_events("does-not-exist") == []


# -- capabilities ------------------------------------------------------------


def test_capabilities_sessions_events_no_cost(adapter):
    caps = adapter.capabilities()
    assert Capability.SESSIONS in caps
    assert Capability.EVENTS in caps
    # COST is deliberately NOT claimed — no on-disk token / cost data.
    assert Capability.COST not in caps


# -- never raises on bad input -----------------------------------------------


def test_never_raises_on_garbage_file(tmp_path):
    """A garbage / unparseable session file must be skipped, not fatal."""
    sessions_dir = tmp_path / "sessions"
    sessions_dir.mkdir()

    # Pure garbage that is not valid JSON on any line.
    (sessions_dir / "garbage.jsonl").write_text(
        "this is not json\n{not valid either\n\x00\x01\x02\n"
    )
    # A line that parses but is not a Message (no role) — must be skipped.
    (sessions_dir / "noroles.jsonl").write_text(
        '{"type": "session", "key": "x"}\n{"foo": "bar"}\n'
    )
    # A valid minimal session so we confirm the good one still surfaces.
    (sessions_dir / "good.jsonl").write_text(
        '{"role": "user", "content": "hi", "created_at": "2026-05-25T12:00:00Z"}\n'
    )

    a = PicoClawAdapter(sessions_dir=str(sessions_dir))

    # detect must not raise and counts all three .jsonl files.
    result = a.detect()
    assert result.detected is True
    assert result.session_count == 3

    # list_sessions must not raise; garbage / no-role sessions produce
    # zero-message Session rows but never crash.
    sessions = a.list_sessions()
    assert len(sessions) == 3
    by_id = {s.id: s for s in sessions}
    assert by_id["garbage"].message_count == 0
    assert by_id["noroles"].message_count == 0
    assert by_id["good"].message_count == 1

    # list_events must not raise on the garbage / no-role files.
    assert a.list_events("garbage") == []
    assert a.list_events("noroles") == []
    good_events = a.list_events("good")
    assert len(good_events) == 1
    assert good_events[0].type == "message"
    assert good_events[0].role == "user"
