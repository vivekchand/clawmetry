"""Unit tests for ``clawmetry/token_confidence.py`` (issue #563)."""

from __future__ import annotations

import math

import pytest

from clawmetry.token_confidence import (
    annotate_events,
    extract_token_confidence,
)


def _entry(token, logprob, top=()):
    """Build one OpenAI-shape logprob entry (token + optional alternatives)."""
    return {
        "token": token,
        "logprob": logprob,
        "top_logprobs": [{"token": t, "logprob": lp} for t, lp in top],
    }


def test_extract_returns_none_when_no_logprobs():
    """Anthropic-shaped events lack logprobs; we must return ``None``."""
    for ev in (
        {},
        {"type": "AGENT"},
        {"type": "AGENT", "data": {"message": {"content": "hi"}}},
        None,
        42,
    ):
        assert extract_token_confidence(ev) is None


def test_extract_openai_shape_logprobs_top_level():
    """Reads ``logprobs.content`` at the event root (legacy adapter shape)."""
    ev = {
        "type": "AGENT",
        "logprobs": {
            "content": [
                _entry("Hello", math.log(0.95), top=[("Hi", math.log(0.03))]),
                _entry(" world", math.log(0.40), top=[("there", math.log(0.55))]),
            ]
        },
    }
    out = extract_token_confidence(ev)
    assert out is not None
    assert out["summary"]["token_count"] == 2
    assert out["summary"]["total_tokens"] == 2
    assert not out["truncated"]
    # Bands: 0.95 → h, 0.40 → l
    assert out["tokens"][0]["band"] == "h"
    assert out["tokens"][1]["band"] == "l"
    # The first token's chosen rank should be 1 (it WAS top).
    assert out["tokens"][0]["rank"] == 1
    # The second token had a higher-probability alternative → rank 2.
    assert out["tokens"][1]["rank"] == 2
    # Top-k alternatives present + sorted descending by prob.
    assert out["tokens"][1]["top_k"][0]["token"] == "there"


def test_extract_openai_shape_logprobs_nested_under_data_message():
    """Reads ``data.message.logprobs.content`` (v3 mapper shape)."""
    ev = {
        "type": "AGENT",
        "data": {
            "message": {
                "logprobs": {
                    "content": [_entry("Ok", math.log(0.99))]
                }
            }
        },
    }
    out = extract_token_confidence(ev)
    assert out is not None
    assert out["tokens"][0]["token"] == "Ok"
    assert out["tokens"][0]["band"] == "h"


def test_extract_caps_tokens_at_200_and_marks_truncated():
    """Multi-thousand-token completions must not blow up the Brain DOM."""
    content = [_entry("x", math.log(0.5)) for _ in range(500)]
    ev = {"type": "AGENT", "logprobs": {"content": content}}
    out = extract_token_confidence(ev)
    assert out is not None
    assert out["summary"]["token_count"] == 200
    assert out["summary"]["total_tokens"] == 500
    assert out["truncated"] is True


def test_summary_flags_high_variance_tokens():
    """Red-band (p < 0.2) tokens are counted in ``high_variance_count``."""
    ev = {
        "type": "AGENT",
        "logprobs": {
            "content": [
                _entry("safe", math.log(0.95)),
                _entry("risky", math.log(0.15)),
                _entry("risky2", math.log(0.10)),
            ]
        },
    }
    out = extract_token_confidence(ev)
    assert out["summary"]["high_variance_count"] == 2


def test_annotate_events_stamps_only_llm_events():
    """``annotate_events`` mutates LLM events in place; skips non-LLM rows."""
    events = [
        {"type": "USER", "detail": "hi"},  # never stamped
        {
            "type": "AGENT",
            "logprobs": {"content": [_entry("ok", math.log(0.99))]},
        },
        {"type": "EXEC", "detail": "ls"},  # never stamped
    ]
    annotate_events(events)
    assert "token_confidence" not in events[0]
    assert "token_confidence" in events[1]
    assert events[1]["token_confidence"]["summary"]["token_count"] == 1
    assert "token_confidence" not in events[2]


def test_annotate_events_does_not_raise_on_garbage():
    """One malformed row must not poison the whole feed (graceful fallback)."""
    events = [
        {"type": "AGENT", "logprobs": "not-a-dict"},
        None,
        {"type": "AGENT", "logprobs": {"content": [{"bad": "shape"}]}},
        42,
    ]
    annotate_events(events)  # must not raise
    # None of these should have been stamped — all are unusable.
    assert not any(isinstance(ev, dict) and "token_confidence" in ev for ev in events if isinstance(ev, dict))


def test_brain_history_stamps_token_confidence_when_logprobs_present(monkeypatch):
    """Integration: ``_annotate_token_confidence`` wires into the Brain pipeline."""
    import routes.brain as br
    events = [
        {
            "type": "AGENT",
            "logprobs": {"content": [_entry("Hello", math.log(0.95))]},
        },
        {"type": "USER", "detail": "hi"},
    ]
    # Use the same indirection ``brain.py`` uses — annotate_events on
    # _annotate_token_confidence ensures the import contract is stable.
    br._annotate_token_confidence(events)
    assert events[0].get("token_confidence", {}).get("summary", {}).get("token_count") == 1
    assert "token_confidence" not in events[1]
