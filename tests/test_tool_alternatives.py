"""Unit tests for ``clawmetry/token_confidence.py`` alternatives extraction (issue #1616).

Covers the three data sources called out in the issue:

* OpenAI logprobs → top-k alternative tool names extracted from the
  first identifying token of the chosen tool name.
* Claude / Gemini extended-thinking → "Chose X over Y" narration parsed
  for self-reported alternatives.
* Neither available → graceful empty list (no fabricated options).

The Brain integration test verifies ``annotate_tool_alternatives``
stamps the field in place so the frontend can render the panel.
"""

from __future__ import annotations

import math

from clawmetry.token_confidence import (
    annotate_tool_alternatives,
    extract_tool_alternatives,
)


def _logprob_entry(token, prob, top=()):
    """Build one OpenAI-shape logprob entry (token + optional alternatives)."""
    return {
        "token": token,
        "logprob": math.log(max(prob, 1e-12)),
        "top_logprobs": [
            {"token": t, "logprob": math.log(max(p, 1e-12))} for t, p in top
        ],
    }


# ── 1. OpenAI logprobs → alternatives extracted ────────────────────────


def test_extracts_alternatives_from_openai_logprobs():
    """The first token of the chosen tool name carries the rejected options."""
    events = [
        {
            "type": "AGENT",
            "logprobs": {
                "content": [
                    _logprob_entry(
                        "create_event",
                        0.89,
                        top=[("send_email", 0.05), ("ask_clarification", 0.06)],
                    ),
                ]
            },
        },
        {
            "event_type": "tool.call",
            "tool_name": "create_event",
        },
    ]
    out = extract_tool_alternatives(events)
    assert len(out) == 1
    row = out[0]
    assert row["chosen"] == "create_event"
    assert row["source"] == "logprobs"
    names = {a["name"] for a in row["alternatives"]}
    assert names == {"send_email", "ask_clarification"}
    # Sorted descending by score.
    assert row["alternatives"][0]["score"] >= row["alternatives"][-1]["score"]
    # The chosen score is stamped from the same token.
    assert row["chosen_score"] is not None
    assert 0.5 < row["chosen_score"] < 1.0


def test_logprobs_alternatives_skip_punctuation_and_whitespace_tokens():
    """Non-identifier alts (``" "``, ``"_"``, ``"\\n"``) must NOT be surfaced."""
    events = [
        {
            "type": "AGENT",
            "logprobs": {
                "content": [
                    _logprob_entry(
                        "send",
                        0.7,
                        top=[(" ", 0.1), ("_", 0.05), ("read", 0.15)],
                    ),
                ]
            },
        },
        {"event_type": "tool.call", "tool_name": "send_email"},
    ]
    out = extract_tool_alternatives(events)
    assert len(out) == 1
    names = {a["name"] for a in out[0]["alternatives"]}
    assert names == {"read"}  # whitespace + underscore dropped


def test_logprobs_caps_alternatives_at_four():
    """Defensive cap matches ``_TOOL_TOP_K`` so the panel stays scannable."""
    events = [
        {
            "type": "AGENT",
            "logprobs": {
                "content": [
                    _logprob_entry(
                        "create",
                        0.6,
                        top=[
                            ("alt_a", 0.1),
                            ("alt_b", 0.08),
                            ("alt_c", 0.06),
                            ("alt_d", 0.04),
                            ("alt_e", 0.02),
                            ("alt_f", 0.01),
                        ],
                    ),
                ]
            },
        },
        {"event_type": "tool.call", "tool_name": "create_event"},
    ]
    out = extract_tool_alternatives(events)
    assert len(out[0]["alternatives"]) == 4


# ── 2. Extended-thinking → alternatives extracted ──────────────────────


def test_extracts_alternatives_from_extended_thinking_chose_over():
    """Claude extended-thinking ``Chose X over Y, Z`` narration is parsed."""
    events = [
        {
            "type": "AGENT",
            "thinking": "I evaluated the options. Chose `create_event` over send_email, ask_clarification because the user wants a calendar item.",
        },
        {"event_type": "tool.call", "tool_name": "create_event"},
    ]
    out = extract_tool_alternatives(events)
    assert len(out) == 1
    row = out[0]
    assert row["source"] == "thinking"
    names = [a["name"] for a in row["alternatives"]]
    assert "send_email" in names
    assert "ask_clarification" in names
    # Thinking-source alts carry no fabricated score — explicit None.
    assert all(a["score"] is None for a in row["alternatives"])


def test_extracts_alternatives_from_extended_thinking_considered_but_chose():
    """The inverse "Considered X but chose Y" pattern is also supported."""
    events = [
        {
            "type": "AGENT",
            "data": {
                "message": {
                    "content": [
                        {
                            "type": "thinking",
                            "thinking": "Considered send_email and ask_user but chose create_event.",
                        }
                    ]
                }
            },
        },
        {"event_type": "tool.call", "tool_name": "create_event"},
    ]
    out = extract_tool_alternatives(events)
    assert len(out) == 1
    names = {a["name"] for a in out[0]["alternatives"]}
    assert names == {"send_email", "ask_user"}


def test_thinking_narration_mismatched_with_actual_tool_is_ignored():
    """If the narration's chosen tool != actual tool, do NOT show alts."""
    events = [
        {
            "type": "AGENT",
            "thinking": "Chose send_email over delete_event.",
        },
        # Actual tool call is something else entirely.
        {"event_type": "tool.call", "tool_name": "create_event"},
    ]
    out = extract_tool_alternatives(events)
    assert out[0]["alternatives"] == []
    assert out[0]["source"] == "none"


# ── 3. No alternatives available → graceful empty state ────────────────


def test_anthropic_call_without_logprobs_or_thinking_returns_empty():
    """The honest empty-state path — no fabricated alternatives."""
    events = [
        {"type": "AGENT", "detail": "Sure, I'll do that."},  # plain Claude
        {"event_type": "tool.call", "tool_name": "create_event"},
    ]
    out = extract_tool_alternatives(events)
    assert len(out) == 1
    assert out[0]["chosen"] == "create_event"
    assert out[0]["alternatives"] == []
    assert out[0]["source"] == "none"
    assert out[0]["chosen_score"] is None


def test_no_preceding_llm_event_returns_empty():
    """A bare tool.call with no nearby model event yields no alternatives."""
    events = [
        {"type": "USER", "detail": "hi"},
        {"event_type": "tool.call", "tool_name": "create_event"},
    ]
    out = extract_tool_alternatives(events)
    assert out[0]["alternatives"] == []
    assert out[0]["source"] == "none"


def test_extract_does_not_raise_on_garbage_input():
    """One bad row never poisons the whole Brain feed."""
    assert extract_tool_alternatives([]) == []
    assert extract_tool_alternatives(None) == []  # type: ignore[arg-type]
    assert extract_tool_alternatives([None, 42, {"event_type": "tool.call"}]) == []


def test_no_tool_call_events_returns_empty():
    """Non-tool events should not show up in the output."""
    events = [{"type": "USER"}, {"type": "AGENT"}, {"event_type": "model.completed"}]
    assert extract_tool_alternatives(events) == []


# ── 4. Brain integration → annotate stamps the field ───────────────────


def test_annotate_stamps_tool_alternatives_on_tool_call_event():
    """``annotate_tool_alternatives`` mutates events in place for the frontend."""
    events = [
        {
            "type": "AGENT",
            "logprobs": {
                "content": [
                    _logprob_entry(
                        "create",
                        0.8,
                        top=[("send_email", 0.1), ("read_file", 0.05)],
                    ),
                ]
            },
        },
        {"event_type": "tool.call", "tool_name": "create_event"},
    ]
    annotate_tool_alternatives(events)
    payload = events[1].get("tool_alternatives")
    assert payload is not None
    assert payload["chosen"] == "create_event"
    assert payload["source"] == "logprobs"
    names = {a["name"] for a in payload["alternatives"]}
    assert "send_email" in names


def test_annotate_empty_or_garbage_is_noop():
    """No throw on empty / wrong-shape input."""
    annotate_tool_alternatives([])          # no-op, no raise
    annotate_tool_alternatives(None)        # type: ignore[arg-type]
    events = [{"event_type": "tool.call", "tool_name": "x"}]
    annotate_tool_alternatives(events)
    # tool_alternatives is stamped even with empty alternatives (so the
    # frontend renders the honest "not available" hint).
    assert events[0]["tool_alternatives"]["alternatives"] == []
    assert events[0]["tool_alternatives"]["source"] == "none"


def test_brain_history_pipeline_wires_in_alternatives(monkeypatch):
    """Integration: the Brain handler stamps ``tool_alternatives``."""
    import routes.brain as br
    events = [
        {
            "type": "AGENT",
            "logprobs": {
                "content": [
                    _logprob_entry(
                        "create",
                        0.8,
                        top=[("send_email", 0.1)],
                    ),
                ]
            },
        },
        {"event_type": "tool.call", "tool_name": "create_event"},
    ]
    # Same indirection brain.py uses — proves the import contract is stable.
    br._annotate_tool_alternatives(events)
    assert events[1].get("tool_alternatives", {}).get("chosen") == "create_event"
