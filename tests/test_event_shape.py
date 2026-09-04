"""clawmetry.event_shape: one normaliser for every stored event shape.

One case per runtime shape the store actually holds, driven from the checked-in
fixtures where one exists (OpenClaw v3, OpenClaw trajectory, Claude Code) and
from the family-adapter row shape ``sync.py`` writes for every pro runtime
(Codex, Cursor, Gemini CLI, ...). Each case asserts the four typed columns:
role / block_kind / tool_name / is_error.
"""
from __future__ import annotations

import json
import os

import pytest

from clawmetry import event_shape as es
from clawmetry import replay_schema

HERE = os.path.dirname(os.path.abspath(__file__))
FIX = os.path.join(HERE, "fixtures")


def _lines(path):
    with open(path, encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]


def _cols(shape):
    return (shape["role"], shape["block_kind"], shape["tool_name"], shape["is_error"])


# ── vocabulary contract ───────────────────────────────────────────────────

def test_block_kinds_align_with_replay_schema():
    """block_kind uses the replay vocabulary: thinking, tool_use (tool.call),
    tool_result (tool.result)."""
    assert "thinking" in es.BLOCK_KINDS and replay_schema.KIND_THINKING == "thinking"
    assert "tool_use" in es.BLOCK_KINDS and replay_schema.KIND_TOOL_CALL == "tool.call"
    assert "tool_result" in es.BLOCK_KINDS and replay_schema.KIND_TOOL_RESULT == "tool.result"
    assert set(es.BLOCK_KINDS) == {"text", "thinking", "tool_use", "tool_result", "system", "other"}


def test_classify_never_raises_on_garbage():
    for et, data in [(None, None), ("", ""), ("message", "not json"),
                     ("message", b"\xff\xfe"), ("tool_call", 42),
                     ("model.completed", {"data": "nope"}), (object(), [1, 2])]:
        shape = es.classify(et, data)
        assert shape["block_kind"] in es.BLOCK_KINDS
        assert shape["role"] in es.ROLES
        assert isinstance(shape["is_error"], bool)


# ── OpenClaw v3 (normalised by sync._parse_v3_event) ─────────────────────

@pytest.fixture(scope="module")
def v3_rows():
    from clawmetry import sync
    rows = []
    for obj in _lines(os.path.join(FIX, "openclaw", "v3-session.jsonl")):
        if sync._is_v3_event(obj):
            row = sync._parse_v3_event(obj, "sid-v3", "node-test")
            if row is not None:
                rows.append(row)
    assert rows, "fixture produced no v3 rows"
    return rows


def test_openclaw_v3_prompt_submitted(v3_rows):
    row = next(r for r in v3_rows if r["event_type"] == "prompt.submitted")
    shape = es.classify(row["event_type"], row["data"])
    assert _cols(shape) == ("user", "text", "", False)
    assert shape["text"] == "hello world from MOAT verification"


def test_openclaw_v3_model_completed_with_tool_use(v3_rows):
    row = next(r for r in v3_rows if r["event_type"] == "model.completed")
    shape = es.classify(row["event_type"], row["data"])
    assert shape["role"] == "assistant"
    assert shape["block_kind"] == "text"          # text + a tool call: text wins
    assert shape["tool_name"] == "bash"           # from toolMetas
    assert shape["tool_uses"] and shape["tool_uses"][0]["name"] == "bash"
    assert shape["is_error"] is False
    assert "I will run a tool" in shape["text"]


def test_openclaw_v3_tool_result(v3_rows):
    row = next(r for r in v3_rows if r["event_type"] == "tool.result")
    shape = es.classify(row["event_type"], row["data"])
    assert shape["role"] == "tool"
    assert shape["block_kind"] == "tool_result"
    assert shape["is_error"] is False
    assert shape["text"].strip() == "moat"
    assert shape["tool_results"][0]["tool_use_id"] == "toolu_01moat"


def test_openclaw_v3_plumbing_is_other(v3_rows):
    for et in ("session.started", "model.changed"):
        row = next(r for r in v3_rows if r["event_type"] == et)
        assert _cols(es.classify(row["event_type"], row["data"])) == ("", "other", "", False)


def test_openclaw_v3_tool_result_error_flag():
    from clawmetry import sync
    obj = {"type": "tool_use_result", "id": "x1", "timestamp": "2026-05-12T22:35:31Z",
           "tool_use_id": "toolu_9", "content": [{"type": "text", "text": "Permission denied"}],
           "is_error": True}
    row = sync._parse_v3_event(obj, "sid", "node")
    shape = es.classify(row["event_type"], row["data"])
    assert shape["block_kind"] == "tool_result" and shape["is_error"] is True


# ── OpenClaw trajectory envelope (raw dotted events, nested data.data) ───

def test_openclaw_trajectory_shapes():
    rows = _lines(os.path.join(FIX, "openclaw", "trajectory.jsonl"))
    by = {r["type"]: r for r in rows}
    p = es.classify("prompt.submitted", by["prompt.submitted"])
    assert _cols(p) == ("user", "text", "", False)
    assert p["text"] == "trajectory schema sanity check"
    t = es.classify("trace.artifacts", by["trace.artifacts"])
    assert t["role"] == "assistant" and t["block_kind"] == "text"
    assert t["text"] == "trajectory reply"
    m = es.classify("model.completed", by["model.completed"])
    assert m["role"] == "assistant" and m["text"] == "done"
    assert es.classify("session.ended", by["session.ended"])["block_kind"] == "other"


def test_openclaw_tool_call_and_context_compiled():
    call = es.classify("tool.call", {"type": "tool.call",
                                     "data": {"name": "mcp__openclaw__read", "input": {"path": "x"}}})
    assert _cols(call) == ("assistant", "tool_use", "read", False)
    assert call["tool_uses"][0]["input"] == {"path": "x"}
    ctx = es.classify("context.compiled", {"type": "context.compiled",
                                           "data": {"systemPrompt": "you are", "tools": []}})
    assert ctx["role"] == "system" and ctx["block_kind"] == "system"
    comp = es.classify("compaction", {"summary": "condensed"})
    assert comp["block_kind"] == "system" and comp["text"] == "condensed"


# ── Claude Code raw transcript rows (data.message.content blocks) ────────

@pytest.fixture(scope="module")
def cc_rows():
    path = os.path.join(FIX, "runtimes", "claude_code", "projects",
                        "-Users-dev-projects-demo",
                        "11111111-2222-3333-4444-555555555555.jsonl")
    return _lines(path)


def test_claude_code_user_prompt(cc_rows):
    row = next(r for r in cc_rows if r.get("type") == "user"
               and isinstance(r["message"].get("content"), str))
    shape = es.classify(row["type"], row)
    assert _cols(shape) == ("user", "text", "", False)
    assert shape["text"].startswith("REDACTED user request")


def test_claude_code_thinking_plus_tool_use(cc_rows):
    row = next(r for r in cc_rows if r.get("type") == "assistant"
               and any(b.get("type") == "tool_use" for b in r["message"]["content"]))
    shape = es.classify(row["type"], row)
    assert shape["role"] == "assistant"
    assert shape["block_kind"] == "tool_use"   # no text block: the call is the action
    assert shape["tool_name"] == "Bash"
    assert shape["thinking_blocks"] and "reasoning" in shape["thinking"]
    assert shape["tool_uses"][0]["id"] == "toolu_aaa111"


def test_claude_code_tool_result_block(cc_rows):
    row = next(r for r in cc_rows if r.get("type") == "user"
               and isinstance(r["message"].get("content"), list))
    shape = es.classify(row["type"], row)
    assert shape["role"] == "tool"
    assert shape["block_kind"] == "tool_result"
    assert shape["tool_results"][0]["tool_use_id"] == "toolu_aaa111"
    assert shape["is_error"] is False


def test_claude_code_final_text(cc_rows):
    row = [r for r in cc_rows if r.get("type") == "assistant"][-1]
    shape = es.classify(row["type"], row)
    assert shape["role"] == "assistant" and shape["block_kind"] == "text"
    assert shape["text"]


def test_claude_code_tool_result_error_block():
    row = {"type": "user", "message": {"role": "user", "content": [
        {"type": "tool_result", "tool_use_id": "t1", "is_error": True,
         "content": "command not found"}]}}
    shape = es.classify("user", row)
    assert _cols(shape) == ("tool", "tool_result", "", True)
    assert shape["text"] == "command not found"


# ── Family-adapter rows (what sync.py stores for Codex / Cursor / Gemini) ─

@pytest.mark.parametrize("runtime", ["codex", "cursor", "gemini_cli", "copilot", "goose"])
def test_family_message_rows(runtime):
    u = es.classify("message", {"role": "user", "content": "fix the flaky test", "_runtime": runtime})
    assert _cols(u) == ("user", "text", "", False)
    a = es.classify("message", {"role": "assistant", "content": "On it.", "_runtime": runtime})
    assert _cols(a) == ("assistant", "text", "", False)


def test_family_tool_call_row_codex():
    shape = es.classify("tool_call", {
        "role": "assistant", "content": "", "_runtime": "codex",
        "tool_name": "shell", "tool_calls": [{"id": "call_1", "input": {"cmd": "pytest"}}],
    })
    assert _cols(shape) == ("assistant", "tool_use", "shell", False)
    assert shape["tool_uses"][0]["id"] == "call_1"


def test_family_tool_result_row_error_in_extra_cursor():
    shape = es.classify("tool_result", {
        "role": "user", "content": "Traceback ...", "_runtime": "cursor",
        "tool_name": "run_terminal_cmd", "extra": {"toolUseId": "call_1", "isError": True},
    })
    assert _cols(shape) == ("tool", "tool_result", "run_terminal_cmd", True)
    assert shape["tool_results"][0]["tool_use_id"] == "call_1"


def test_family_tool_result_extra_as_json_string_gemini():
    shape = es.classify("tool_result", {
        "role": "tool", "content": "ok", "_runtime": "gemini_cli",
        "tool_name": "read_file", "extra": json.dumps({"toolUseId": "g9", "isError": False}),
    })
    assert _cols(shape) == ("tool", "tool_result", "read_file", False)
    assert shape["tool_results"][0]["tool_use_id"] == "g9"


def test_family_benign_error_is_not_an_error():
    shape = es.classify("tool_result", {"role": "user", "content": "EISDIR",
                                        "tool_name": "Read", "benign_error": True,
                                        "extra": {"isError": False}})
    assert shape["is_error"] is False


def test_family_thinking_row():
    shape = es.classify("thinking", {"role": "assistant", "content": "let me check the diff"})
    assert _cols(shape) == ("assistant", "thinking", "", False)
    assert shape["thinking"] == "let me check the diff" and shape["text"] == ""


# ── Claude Code native OTel intake rows ───────────────────────────────────

def test_otel_intake_rows():
    assert _cols(es.classify("user_prompt", {"prompt": "hi"})) == ("user", "text", "", False)
    llm = es.classify("llm_call", {"model": "claude-x"})
    assert llm["role"] == "assistant"
    err = es.classify("api_error", {"message": "429 rate limited"})
    assert err["role"] == "system" and err["block_kind"] == "system" and err["is_error"] is True
    wait = es.classify("waiting_on_user", {"tool_name": "Bash"})
    assert wait["block_kind"] == "system" and wait["tool_name"] == "Bash"


# ── flat Anthropic-style row (legacy ingest / tests) ─────────────────────

def test_flat_anthropic_message_with_tool_calls():
    shape = es.classify("message", {"role": "assistant", "content": "",
                                    "tool_calls": [{"name": "grep", "input": {"q": "x"}}]})
    assert _cols(shape) == ("assistant", "tool_use", "grep", False)
    tr = es.classify("tool_result", {"role": "tool_result", "content": "3 matches"})
    assert tr["role"] == "tool" and tr["block_kind"] == "tool_result"


def test_json_string_payload_is_decoded():
    shape = es.classify("message", json.dumps({"role": "user", "content": "hello"}))
    assert _cols(shape) == ("user", "text", "", False)


# ── first_user_prompt (sessions.intent source) ───────────────────────────

def test_first_user_prompt_skips_harness_frames_and_takes_earliest():
    rows = [
        {"event_type": "message", "ts": "2026-09-01T00:00:03Z",
         "data": {"role": "user", "content": "second real prompt"}},
        {"event_type": "message", "ts": "2026-09-01T00:00:01Z",
         "data": {"role": "user", "content": "<system-reminder>injected</system-reminder>"}},
        {"event_type": "message", "ts": "2026-09-01T00:00:02Z",
         "data": {"role": "user", "content": "  the   REAL first  prompt \n\nwith detail "}},
        {"event_type": "message", "ts": "2026-09-01T00:00:00Z",
         "data": {"role": "assistant", "content": "not a user"}},
    ]
    assert es.first_user_prompt(rows) == "the REAL first prompt\n\nwith detail"


def test_first_user_prompt_is_full_text_and_capped():
    long = "x" * 6000
    rows = [{"event_type": "prompt.submitted", "ts": "t",
             "data": {"type": "prompt.submitted", "data": {"finalPromptText": long}}}]
    out = es.first_user_prompt(rows)
    assert len(out) == es.INTENT_MAX_CHARS and out.endswith("...")
    assert len(out) > 80  # not the title truncation


def test_first_user_prompt_accepts_adapter_events():
    class Ev:
        def __init__(self, type_, role, content, ts):
            self.type, self.role, self.content, self.ts = type_, role, content, ts
            self.tool_name = ""
    evs = [Ev("message", "assistant", "hello", 2.0), Ev("message", "user", "do the thing", 3.0)]
    assert es.first_user_prompt(evs) == "do the thing"
    assert es.first_user_prompt([]) == ""
