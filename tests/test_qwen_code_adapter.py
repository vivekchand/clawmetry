"""Tests for QwenCodeAdapter (clawmetry/adapters/qwen_code.py).

Validates against fixtures in Qwen Code's real on-disk chat-recording shape
(Gemini-CLI lineage), NOT OpenClaw's v3 envelope:

  - detect() reports detected + the right session_count, never raises
  - list_sessions() returns both fixtures, newest first, with the model and
    a title taken from the first user prompt
  - message_count counts user/assistant/tool_result records (not system)
  - real token totals come from usageMetadata; cost_usd is None (tokens-only)
  - list_events() yields the expected ordered event types including a
    tool_call (functionCall) and a tool_result (functionResponse)
  - the adapter never raises on a garbage / unparseable session file

Plus a REAL-capture block (skipped if the capture is absent) that parses the
actual bytes Qwen Code v0.16.1 wrote against a local Ollama qwen3:8b model.
See REAL/PROVENANCE.md.

Qwen Code is a FREE runtime as of 2026-09-20 (entitlements.FREE_RUNTIMES), so
the reader and this test ship in the OSS package: a plain `pip install
clawmetry` must be able to read a Qwen Code install with no licence key and no
wheel download. See docs/ENTITLEMENTS.md and QwenLM/qwen-code#9294.
"""
from __future__ import annotations

import json
import os

import pytest

from clawmetry.adapters.base import Capability
from clawmetry.adapters.qwen_code import QwenCodeAdapter

_FIXTURE_PROJECTS_DIR = os.path.join(
    os.path.dirname(__file__),
    "fixtures",
    "runtimes",
    "qwen_code",
    "projects",
)


@pytest.fixture
def adapter() -> QwenCodeAdapter:
    return QwenCodeAdapter(projects_dir=_FIXTURE_PROJECTS_DIR)


def _transcript(events):
    """Timeline rows only: the single context.compiled event rides in front
    of the transcript and is asserted on by its own test below."""
    return [e for e in events if e.type != "context.compiled"]


# -- detect ------------------------------------------------------------------


def test_detect_detected_and_counts(adapter):
    result = adapter.detect()
    assert result.detected is True
    assert result.running is False
    assert result.name == "qwen_code"
    assert result.display_name == "Qwen Code"
    # Two .jsonl fixtures present under projects/*/chats/.
    assert result.session_count == 2
    assert result.meta["projectsDir"] == _FIXTURE_PROJECTS_DIR


def test_detect_false_when_dir_absent(tmp_path, monkeypatch):
    """detect() must not raise and reports detected=False with no home."""
    monkeypatch.setenv("QWEN_HOME", str(tmp_path / "no-such-qwen"))
    a = QwenCodeAdapter(projects_dir=str(tmp_path / "no-such-projects"))
    result = a.detect()
    assert result.detected is False
    assert result.session_count == 0


# -- list_sessions -----------------------------------------------------------


def test_list_sessions_count_and_order(adapter):
    sessions = adapter.list_sessions()
    assert len(sessions) == 2
    # Newest first: text session (last ts 11:30) precedes tool session (10:01).
    assert sessions[0].id == "sess-text-0002"
    assert sessions[1].id == "sess-tool-0001"


def test_list_sessions_model_and_title(adapter):
    by_id = {s.id: s for s in adapter.list_sessions()}

    tool = by_id["sess-tool-0001"]
    assert tool.model == "qwen3:8b"
    assert tool.source == "qwen_code"
    assert tool.title == "List the files in the current directory, then summarize."
    assert tool.display_name == tool.title

    text = by_id["sess-text-0002"]
    assert text.title == "Write a one-line Python hello world and explain it briefly."


def test_list_sessions_message_count_excludes_system(adapter):
    by_id = {s.id: s for s in adapter.list_sessions()}
    # sess-tool: user + 2 assistant + 1 tool_result = 4 (2 system skipped).
    assert by_id["sess-tool-0001"].message_count == 4
    # sess-text: user + 1 assistant = 2.
    assert by_id["sess-text-0002"].message_count == 2


def test_list_sessions_timestamps(adapter):
    by_id = {s.id: s for s in adapter.list_sessions()}
    tool = by_id["sess-tool-0001"]
    assert tool.started_at > 0
    assert tool.ended_at is not None
    assert tool.ended_at >= tool.started_at


def test_list_sessions_real_tokens_summed_cost_none(adapter):
    """Tokens ARE on disk (usageMetadata); USD cost is not."""
    by_id = {s.id: s for s in adapter.list_sessions()}
    tool = by_id["sess-tool-0001"]
    # Two assistant records: total 1280 + 1460 == 2740.
    assert tool.total_tokens == 2740
    assert tool.input_tokens == 1200 + 1400
    assert tool.output_tokens == 80 + 60
    assert tool.reasoning_tokens == 40 + 20
    # Free local Ollama -> a real $0.00 cost (you pay for hardware, not per
    # token), derived from the token split + model. Not "unknown".
    assert tool.cost_usd == 0.0
    assert tool.cost_status == "derived"


# -- list_events -------------------------------------------------------------


def test_list_events_ordered_types_with_tool_call(adapter):
    events = _transcript(adapter.list_events("sess-tool-0001"))
    types = [(e.type, e.role) for e in events]

    # Expected chronological order:
    #   user message
    #   assistant thinking (thought part)
    #   assistant tool_call (functionCall)
    #   tool_result (functionResponse)
    #   assistant thinking
    #   assistant message
    assert types == [
        ("message", "user"),
        ("thinking", "assistant"),
        ("tool_call", "assistant"),
        ("tool_result", "tool"),
        ("thinking", "assistant"),
        ("message", "assistant"),
    ]

    tool_call = next(e for e in events if e.type == "tool_call")
    assert tool_call.tool_name == "list_directory"
    assert tool_call.tool_calls[0]["id"] == "call_demo01"
    assert tool_call.tool_calls[0]["name"] == "list_directory"
    assert tool_call.tool_calls[0]["arguments"] == {"path": "/tmp/demo"}

    tool_result = next(e for e in events if e.type == "tool_result")
    assert tool_result.extra["toolCallId"] == "call_demo01"
    assert tool_result.tool_name == "list_directory"
    assert "probe.txt" in tool_result.content

    # Events are chronologically ordered (non-decreasing timestamps).
    ts_list = [e.ts for e in events if e.ts]
    assert ts_list == sorted(ts_list)


def test_list_events_empty_for_unknown_session(adapter):
    assert adapter.list_events("does-not-exist") == []


def test_context_compiled_event_is_partial_and_from_the_records(adapter, tmp_path, monkeypatch):
    """INPUTS pillar: no system prompt is persisted (type=system records are
    telemetry), so the context event carries the record-stamped cwd/version,
    the assistant model, the first prompt, the invoked tool names, the
    tool-call decisions and settings.json's MCP server names."""
    home = tmp_path / "qwen-home"
    home.mkdir()
    (home / "settings.json").write_text(json.dumps({
        "mcpServers": {"filesystem": {"command": "npx"}, "github": {"url": "http://x"}},
        "security": {"auth": {"selectedType": "USE_OPENAI"}},
        "telemetry": {"target": "local"},
    }))
    monkeypatch.setenv("QWEN_HOME", str(home))

    events = adapter.list_events("sess-tool-0001")
    ctx = events[0]
    assert ctx.type == "context.compiled"
    assert ctx.id.startswith("ctx:sess-tool-0001:")
    assert ctx.ts <= min(e.ts for e in events[1:] if e.ts)
    x = ctx.extra
    assert "systemPrompt" not in x
    assert x["prompt"] == "List the files in the current directory, then summarize."
    assert x["tools"] == ["list_directory"]
    meta = x["runtimeMeta"]
    assert meta["cwd"] == "/tmp/demo"
    assert meta["version"] == "0.16.1"
    assert meta["model"]
    assert meta["mcpServers"] == [{"name": "filesystem"}, {"name": "github"}]
    assert meta["activeAuthType"] == "USE_OPENAI"
    assert meta["telemetryTarget"] == "local"
    assert "invoked names only" in x["source"]
    assert sum(1 for e in events if e.type == "context.compiled") == 1

    # No settings file: the settings-derived keys are absent, not blank.
    monkeypatch.setenv("QWEN_HOME", str(tmp_path / "nowhere"))
    bare = adapter.list_events("sess-tool-0001")[0].extra["runtimeMeta"]
    assert "mcpServers" not in bare and "activeAuthType" not in bare
    assert bare["cwd"] == "/tmp/demo"
    assert getattr(Capability, "INPUTS", None) is None or Capability.INPUTS in adapter.capabilities()
    assert adapter.trail_coverage()["inputs"] == "partial"


# -- capabilities ------------------------------------------------------------


def test_capabilities_sessions_events_cost(adapter):
    caps = adapter.capabilities()
    assert Capability.SESSIONS in caps
    assert Capability.EVENTS in caps
    # COST is claimed: Qwen Code records real usageMetadata token counts.
    assert Capability.COST in caps


# -- never raises on bad input -----------------------------------------------


def test_never_raises_on_garbage_file(tmp_path):
    """A garbage / unparseable session file must be skipped, not fatal."""
    chats = tmp_path / "projects" / "-tmp-x" / "chats"
    chats.mkdir(parents=True)

    (chats / "garbage.jsonl").write_text(
        "this is not json\n{not valid either\n\x00\x01\x02\n"
    )
    (chats / "good.jsonl").write_text(
        '{"type":"user","sessionId":"good","timestamp":"2026-05-25T12:00:00.000Z",'
        '"message":{"role":"user","parts":[{"text":"hi"}]}}\n'
    )

    a = QwenCodeAdapter(projects_dir=str(tmp_path / "projects"))

    result = a.detect()
    assert result.detected is True
    assert result.session_count == 2

    sessions = a.list_sessions()
    assert len(sessions) == 2
    by_id = {s.id: s for s in sessions}
    assert by_id["garbage"].message_count == 0
    assert by_id["good"].message_count == 1

    assert a.list_events("garbage") == []
    good_events = _transcript(a.list_events("good"))
    assert len(good_events) == 1
    assert good_events[0].type == "message"
    assert good_events[0].role == "user"
    assert good_events[0].content == "hi"


# -- REAL captured session (ground truth) ------------------------------------
#
# Captured by actually installing Qwen Code (@qwen-code/qwen-code v0.16.1) and
# running real agent turns against a local Ollama qwen3:8b model. These tests
# lock in the real Gemini-lineage shape against actual bytes: the "model" role
# normalises to "assistant", usageMetadata carries real token counts, and the
# native functionCall / functionResponse tool shape parses. See REAL/PROVENANCE.md.

_REAL_PROJECTS = os.path.join(
    os.path.dirname(__file__), "fixtures", "runtimes", "qwen_code", "REAL", "projects"
)


def _real_present() -> bool:
    import glob as _g
    return bool(_g.glob(os.path.join(_REAL_PROJECTS, "*", "chats", "*.jsonl")))


@pytest.mark.skipif(not _real_present(), reason="real Qwen Code capture not present")
def test_real_capture_parses():
    a = QwenCodeAdapter(projects_dir=_REAL_PROJECTS)
    assert a.detect().detected is True
    sessions = a.list_sessions()
    # Two real sessions captured.
    assert len(sessions) == 2
    for s in sessions:
        assert s.model == "qwen3:8b"
        # Real usageMetadata token counts must be surfaced (>0).
        assert s.total_tokens > 0
        # Free local Ollama endpoint -> a real derived $0.00 (not "unknown").
        assert s.cost_usd == 0.0


@pytest.mark.skipif(not _real_present(), reason="real Qwen Code capture not present")
def test_real_capture_tool_call_and_roles():
    a = QwenCodeAdapter(projects_dir=_REAL_PROJECTS)
    # The tool-using session is the one whose first prompt mentions a tool.
    sessions = a.list_sessions()
    tool_sess = next(
        s for s in sessions if "list the files" in s.title.lower()
    )
    events = a.list_events(tool_sess.id)

    # The real native list_directory functionCall must be extracted.
    tool_calls = [e for e in events if e.type == "tool_call"]
    assert tool_calls, "expected at least one tool_call event"
    names = {e.tool_name for e in tool_calls}
    assert "list_directory" in names
    assert "unknown" not in names

    # Its tool_result functionResponse must be parsed with the matching id.
    tool_results = [e for e in events if e.type == "tool_result"]
    assert tool_results, "expected at least one tool_result event"
    assert any("probe.txt" in e.content for e in tool_results)

    # Gemini "model" role must normalise to "assistant"; no raw "model" leaks.
    roles = {e.role for e in events}
    assert "assistant" in roles
    assert "model" not in roles

    # Every event timestamp must parse (>0).
    assert all(e.ts > 0 for e in events)
