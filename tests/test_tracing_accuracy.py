"""Accuracy regression tests for the Tracing tab's span builder.

These pin two bugs surfaced by checking /api/trace against the raw Claude Code
session JSONL on a real machine:

  1. **$0 cost for real spend.** Multi-runtime adapters (Claude Code, Codex, …)
     emit ``event_type='message'`` with the input/output split under
     ``data.extra`` and no top-level ``cost_usd``. The trace builder read
     ``e['cost_usd']`` directly → every span cost was 0 → a 100k-token session
     showed ``$0``. ``_event_cost`` now derives it (cache-aware, provider
     inferred from the model), honouring an explicit stored cost first.

  2. **LLM turns mislabelled.** Those adapters carry the speaker in
     ``data.role`` (event_type is just ``message`` for both turns), so
     ``_build_spans`` rendered every assistant turn as a generic ``event``
     span instead of a ``chat`` (llm) span, and the user prompt never became a
     ``prompt`` span. Classification now also keys on ``data.role``.
"""

from __future__ import annotations

from clawmetry.providers_pricing import estimate_event_cost_usd
from routes.tracing import _build_spans, _event_cost, _summarize_trace


def _cc_event(eid, role, *, et="message", text="", tok=0, extra=None,
              ts="2026-05-25T18:37:00Z", model="claude-opus-4-7"):
    """A Claude Code-shaped event row as ``query_events`` returns it."""
    data = {"role": role, "content": text}
    if extra:
        data["extra"] = extra
    return {
        "id": eid, "session_id": "claude_code:s1", "event_type": et,
        "ts": ts, "model": model, "token_count": tok, "cost_usd": None,
        "data": data,
    }


# ── _event_cost ───────────────────────────────────────────────────────────


def test_event_cost_derives_from_extra_split():
    e = _cc_event("a", "assistant", text="hi", tok=3212,
                  extra={"inputTokens": 3166, "outputTokens": 46})
    expect = estimate_event_cost_usd("claude-opus-4-7", input_tokens=3166, output_tokens=46)
    assert expect > 0
    assert abs(_event_cost(e) - expect) < 1e-9


def test_event_cost_is_cache_aware():
    no_cache = _cc_event("a", "assistant", tok=3212,
                         extra={"inputTokens": 3166, "outputTokens": 46})
    with_cache = _cc_event("b", "assistant", tok=3212,
                           extra={"inputTokens": 3166, "outputTokens": 46,
                                  "cacheReadInputTokens": 10319,
                                  "cacheCreationInputTokens": 12078})
    assert _event_cost(with_cache) > _event_cost(no_cache) > 0


def test_event_cost_honours_explicit_stored_cost():
    e = _cc_event("a", "assistant", tok=100, extra={"inputTokens": 100, "outputTokens": 0})
    e["cost_usd"] = 0.42
    assert _event_cost(e) == 0.42  # never re-derive when the value is real


def test_event_cost_zero_without_model_or_tokens():
    assert _event_cost(_cc_event("a", "assistant", model="", tok=0)) == 0.0


# ── _build_spans classification ─────────────────────────────────────────────


def test_build_spans_labels_claude_code_roles_and_cost():
    rows = [
        _cc_event("u", "user", text="do a thing", ts="2026-05-25T18:37:00Z"),
        _cc_event("a", "assistant", text="done", tok=3212,
                  extra={"inputTokens": 3166, "outputTokens": 46},
                  ts="2026-05-25T18:37:02Z"),
    ]
    spans, roots = _build_spans(rows)
    kinds = {s["kind"] for s in spans}
    # assistant 'message' → chat/llm span (was generic 'event'); user → 'prompt'
    assert "llm" in kinds, f"assistant turn not classified as llm: {[(s['name'], s['kind']) for s in spans]}"
    assert "prompt" in kinds, f"user turn not classified as prompt: {[(s['name'], s['kind']) for s in spans]}"
    chat = next(s for s in spans if s["kind"] == "llm")
    assert chat["name"].startswith("chat")
    assert chat["cost"] > 0, "chat span cost not derived from the extra split"
    prompt = next(s for s in spans if s["kind"] == "prompt")
    assert "do a thing" in (prompt.get("detail") or "")


def test_summarize_trace_derives_total_cost():
    rows = [
        _cc_event("a", "assistant", tok=3212,
                  extra={"inputTokens": 3166, "outputTokens": 46}),
    ]
    summ = _summarize_trace("claude_code:s1", rows)
    assert summ["total_cost_usd"] > 0, "trace total cost still $0 for a priced turn"
    assert summ["total_tokens"] == 3212


# ── NeMo catalog meta-tool tagging (issue #2607) ────────────────────────────


def _oc_tool_event(eid, tool_names, *, ts="2026-06-03T10:00:00Z"):
    """An OpenClaw v3 assistant message event with tool_use blocks in content."""
    content = [{"type": "text", "text": "searching"}]
    for i, name in enumerate(tool_names):
        content.append({"type": "tool_use", "id": f"tu{i}", "name": name, "input": {}})
    return {
        "id": eid, "session_id": "oc:s1", "event_type": "model.completed",
        "ts": ts, "model": "claude-sonnet-4-6", "token_count": 50, "cost_usd": None,
        "data": {"role": "assistant", "message": {"role": "assistant", "content": content}},
    }


def test_nemoclaw_catalog_tools_tagged():
    rows = [_oc_tool_event("e1", ["tool_search", "Bash"])]
    spans, _ = _build_spans(rows)
    tool_spans = [s for s in spans if s["kind"] == "tool"]
    assert tool_spans, "expected tool spans"
    by_name = {s["tool"]: s for s in tool_spans}
    assert by_name.get("tool_search", {}).get("nemoclaw_meta") is True, \
        "tool_search span should have nemoclaw_meta=True"
    assert "nemoclaw_meta" not in by_name.get("Bash", {}), \
        "regular tool span should not have nemoclaw_meta"


def test_nemoclaw_all_three_meta_tools_tagged():
    rows = [_oc_tool_event("e2", ["tool_search", "tool_describe", "tool_call"])]
    spans, _ = _build_spans(rows)
    tool_spans = [s for s in spans if s["kind"] == "tool"]
    assert len(tool_spans) == 3
    for s in tool_spans:
        assert s.get("nemoclaw_meta") is True, f"{s['tool']} should be tagged as nemoclaw_meta"
