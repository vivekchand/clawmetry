"""Reasoning as first-class spans in the tracing waterfall + turn anatomy.

The decision trail needs the thinking that drove each action, and the link
between the two. These tests pin:

* a ``thinking`` event (family-adapter shape) becomes a ``reasoning`` span
  named ``think`` whose ``detail`` is the thinking text;
* the ``execute_tool`` span that follows nests UNDER that reasoning span
  (the reasoning-to-tool causal link), not under the chat span;
* an OpenClaw / Anthropic assistant message with an inline thinking block
  gets a reasoning span under its chat span, tools under the reasoning;
* a new user prompt closes the reasoning scope;
* when the raw events carry no thinking, ``replay_events`` kind=thinking rows
  are merged in by ``/api/trace/<id>``;
* turn anatomy emits a distinct ``thinking`` span kind (never folded into
  ``model``) and both endpoints report ``reasoning.coverage``.
"""
from __future__ import annotations

import pytest

from routes import tracing as T
from routes import turn_anatomy as TA


def _ts(i):
    return f"2026-09-03T10:00:{i:02d}.000Z"


def _family_rows():
    """Claude Code / Codex shape: thinking, tool_call and tool_result are
    separate rows; tool linkage via data.tool_calls[].id + extra.toolUseId."""
    return [
        {"id": "e1", "event_type": "message", "ts": _ts(0),
         "data": {"role": "user", "content": "list the files", "_runtime": "claude_code"}},
        {"id": "e2", "event_type": "thinking", "ts": _ts(1),
         "data": {"role": "assistant", "content": "I should run ls first.", "_runtime": "claude_code"}},
        {"id": "e3", "event_type": "tool_call", "ts": _ts(2),
         "data": {"role": "assistant", "content": "", "tool_name": "Bash",
                  "tool_calls": [{"id": "toolu_1", "input": {"command": "ls"}}]}},
        {"id": "e4", "event_type": "tool_result", "ts": _ts(3),
         "data": {"role": "user", "content": "a.py b.py",
                  "extra": '{"toolUseId": "toolu_1", "isError": false}'}},
        {"id": "e5", "event_type": "message", "ts": _ts(4),
         "data": {"role": "assistant", "content": "Two files."}},
    ]


def _by_kind(spans, kind):
    return [s for s in spans if s["kind"] == kind]


def test_thinking_event_becomes_reasoning_span_and_parents_the_tool():
    spans, roots = T._build_spans(_family_rows())
    reasoning = _by_kind(spans, "reasoning")
    assert len(reasoning) == 1
    r = reasoning[0]
    assert r["name"] == "think"
    assert r["detail"] == "I should run ls first."
    tools = _by_kind(spans, "tool")
    assert len(tools) == 1
    assert tools[0]["parent_span_id"] == r["span_id"], \
        "execute_tool must nest under the reasoning that caused it"
    # The tool_result still closes the span (duration measured to its result).
    assert tools[0]["duration_ms"] == 1000
    assert tools[0]["output"] == "a.py b.py"
    # The reasoning span rolls up its tool child.
    assert "rolled_cost" in r


def test_tool_without_preceding_reasoning_nests_under_chat():
    rows = [r for r in _family_rows() if r["event_type"] != "thinking"]
    spans, _ = T._build_spans(rows)
    assert not _by_kind(spans, "reasoning")
    tool = _by_kind(spans, "tool")[0]
    chat_ids = {s["span_id"] for s in _by_kind(spans, "llm")}
    assert tool["parent_span_id"] in chat_ids


def test_openclaw_inline_thinking_block_nests_under_chat_and_parents_tool():
    rows = [
        {"id": "p", "event_type": "prompt.submitted", "ts": _ts(0),
         "data": {"finalPromptText": "hi"}},
        {"id": "a", "event_type": "model.completed", "ts": _ts(1), "model": "claude-x",
         "data": {"message": {"role": "assistant", "content": [
             {"type": "thinking", "thinking": "Need to read the file."},
             {"type": "text", "text": "Reading."},
             {"type": "tool_use", "id": "tu1", "name": "read", "input": {"path": "x"}},
         ]}}},
        {"id": "u", "event_type": "prompt.submitted", "ts": _ts(2),
         "data": {"message": {"role": "user", "content": [
             {"type": "tool_result", "tool_use_id": "tu1", "content": "ok"}]}}},
    ]
    spans, _ = T._build_spans(rows)
    chat = _by_kind(spans, "llm")[0]
    reasoning = _by_kind(spans, "reasoning")
    assert len(reasoning) == 1
    assert reasoning[0]["parent_span_id"] == chat["span_id"]
    assert reasoning[0]["detail"] == "Need to read the file."
    # The chat detail carries only the visible text, never the thinking.
    assert chat["detail"] == "Reading."
    tool = _by_kind(spans, "tool")[0]
    assert tool["parent_span_id"] == reasoning[0]["span_id"]


def test_extra_thinking_on_assistant_message_is_a_reasoning_span():
    rows = [
        {"id": "a", "event_type": "message", "ts": _ts(1),
         "data": {"role": "assistant", "content": "done",
                  "extra": {"thinking": "carried on the message"}}},
    ]
    spans, _ = T._build_spans(rows)
    assert [s["detail"] for s in _by_kind(spans, "reasoning")] == ["carried on the message"]


def test_new_prompt_closes_reasoning_scope():
    rows = _family_rows() + [
        {"id": "e6", "event_type": "message", "ts": _ts(5),
         "data": {"role": "user", "content": "now delete them"}},
        {"id": "e7", "event_type": "tool_call", "ts": _ts(6),
         "data": {"role": "assistant", "content": "", "tool_name": "Bash",
                  "tool_calls": [{"id": "toolu_2", "input": {"command": "rm"}}]}},
    ]
    spans, _ = T._build_spans(rows)
    second_tool = [s for s in _by_kind(spans, "tool") if s["tool"] == "Bash"][-1]
    reasoning_ids = {s["span_id"] for s in _by_kind(spans, "reasoning")}
    assert second_tool["parent_span_id"] not in reasoning_ids, \
        "a tool after a new user prompt must not inherit the earlier reasoning"


def test_thinking_texts_covers_every_shape():
    assert T._thinking_texts({"message": {"content": [
        {"type": "thinking", "thinking": "a"},
        {"type": "reasoning", "text": "b"},
        {"type": "redacted_thinking", "data": "zzz"},
        {"type": "text", "text": "visible"}]}}) == ["a", "b"]
    assert T._thinking_texts({"content": "plain", "thinking": "c"}) == ["c"]
    assert T._thinking_texts({"extra": {"thinking": "d"}}) == ["d"]
    assert T._thinking_texts({}) == []
    assert T._thinking_texts(None) == []


def test_replay_thinking_rows_reshape():
    rows = [
        {"kind": "thinking", "span_id": "s1", "ts": 1.0, "payload": {"text": "from replay"}},
        {"kind": "tool.call", "span_id": "s2", "ts": 2.0, "payload": {"text": "nope"}},
        {"kind": "thinking", "span_id": "s3", "ts": 3.0, "payload": {"text": "   "}},
    ]
    import routes.local_query as LQ
    orig = LQ.local_store_via_daemon
    LQ.local_store_via_daemon = lambda method, **kw: rows if method == "query_replay_events" else None
    try:
        out = T._replay_thinking_rows("codex:abc")
    finally:
        LQ.local_store_via_daemon = orig
    assert len(out) == 1
    assert out[0]["event_type"] == "thinking"
    assert out[0]["data"]["content"] == "from replay"


@pytest.fixture()
def client():
    # A private Flask app: registering on the shared ``dashboard.app`` after
    # another test has sent it a request is refused by Flask, and these
    # handlers reach nothing on the app object itself.
    from flask import Flask
    app = Flask("test_tracing_reasoning_spans")
    app.register_blueprint(T.bp_tracing)
    app.register_blueprint(TA.bp_turn_anatomy)
    app.config["TESTING"] = True
    return app.test_client()


def test_api_trace_merges_replay_thinking_when_events_have_none(client, monkeypatch):
    rows = [r for r in _family_rows() if r["event_type"] != "thinking"]
    monkeypatch.setattr(T, "_events_for", lambda session_id=None, limit=0: rows)
    monkeypatch.setattr(T, "_replay_thinking_rows", lambda sid, limit=4000: [
        {"id": "replay-1", "event_type": "thinking", "ts": _ts(1),
         "data": {"role": "assistant", "content": "replayed thought", "_replay": True}}])
    monkeypatch.setattr(T, "hide_clawmetry_session", lambda sid: False)
    res = client.get("/api/trace/codex:abc")
    assert res.status_code == 200
    data = res.get_json()
    reasoning = [s for s in data["spans"] if s["kind"] == "reasoning"]
    assert [s["detail"] for s in reasoning] == ["replayed thought"]
    tool = [s for s in data["spans"] if s["kind"] == "tool"][0]
    assert tool["parent_span_id"] == reasoning[0]["span_id"]
    assert data["reasoning"]["span_count"] == 1
    assert data["reasoning"]["runtime"] == "codex"
    assert data["reasoning"]["coverage"] in ("full", "partial", "none", "unknown")


def test_api_trace_reports_coverage_for_empty_reasoning(client, monkeypatch):
    rows = [r for r in _family_rows() if r["event_type"] != "thinking"]
    monkeypatch.setattr(T, "_events_for", lambda session_id=None, limit=0: rows)
    monkeypatch.setattr(T, "_replay_thinking_rows", lambda sid, limit=4000: [])
    monkeypatch.setattr(T, "hide_clawmetry_session", lambda sid: False)
    import routes.trail as TR
    monkeypatch.setattr(TR, "coverage_for_runtime", lambda rt: {
        "inputs": "none", "reasoning": "none", "note": "git commits only"})
    data = client.get("/api/trace/lovable:xyz").get_json()
    assert data["reasoning"] == {"runtime": "lovable", "span_count": 0,
                                 "coverage": "none", "note": "git commits only"}


def test_turn_anatomy_emits_distinct_thinking_kind():
    assert TA._classify({"event_type": "thinking", "data": {}}) == "thinking"
    turns = TA._build_turns(_family_rows())
    kinds = [s["kind"] for t in turns for s in t["spans"]]
    assert "thinking" in kinds
    think = [s for t in turns for s in t["spans"] if s["kind"] == "thinking"][0]
    assert think["text"] == "I should run ls first."
    assert think["label"] == "thinking"


def test_turn_anatomy_inline_thinking_block_gets_own_span():
    rows = [
        {"id": "p", "event_type": "prompt.submitted", "ts": _ts(0), "data": {"finalPromptText": "hi"}},
        {"id": "a", "event_type": "model.completed", "ts": _ts(1),
         "data": {"message": {"role": "assistant", "content": [
             {"type": "thinking", "thinking": "hmm"}, {"type": "text", "text": "ok"}]}}},
    ]
    turns = TA._build_turns(rows)
    kinds = [s["kind"] for s in turns[0]["spans"]]
    assert kinds.index("thinking") < kinds.index("reply")


def test_api_turn_anatomy_reports_reasoning_block(client, monkeypatch):
    monkeypatch.setattr(TA, "_events_for", lambda session_id=None, limit=0: _family_rows())
    data = client.get("/api/turn-anatomy?session_id=claude_code:abc").get_json()
    assert data["reasoning"]["span_count"] == 1
    assert data["reasoning"]["runtime"] == "claude_code"
