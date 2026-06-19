"""Tests for #3199 — openclaw:compaction-event usage fields.

Compaction events preserve fresh token-usage data after harness fix #93084.
Two gaps:
1. _build_spans_from_events now emits a span for compaction events so the
   Tracing tab shows the compaction boundary (previously silently dropped).
2. _extract_cost_tokens_model now reads token_count/cost from top-level usage
   on non-message events so the DB column is populated correctly.
"""
from __future__ import annotations

from clawmetry.adapters.openclaw import OpenClawAdapter
from clawmetry.sync import _extract_cost_tokens_model


def test_compaction_event_produces_span():
    events = [
        {"type": "session", "version": 3, "timestamp": "2026-06-19T10:00:00Z"},
        {
            "type": "compaction",
            "timestamp": "2026-06-19T10:05:00Z",
            "summary": "Summarised 47 turns to free context.",
            "tokensBefore": 180000,
            "fromHook": False,
            "usage": {"totalTokens": 8200, "input_tokens": 6800, "output_tokens": 1400},
        },
    ]
    spans = OpenClawAdapter._build_spans_from_events(events, "sess1")
    by_name = {s["name"]: s for s in spans}
    assert "compaction" in by_name, "compaction event must produce a span"
    sp = by_name["compaction"]
    assert sp["kind"] == "INTERNAL"
    assert sp["parent_span_id"] == by_name["session"]["span_id"]
    attrs = sp["attributes"]
    assert attrs["event.kind"] == "compaction"
    assert attrs["compaction.tokens_before"] == 180000
    assert attrs["compaction.usage.total_tokens"] == 8200
    assert attrs["compaction.from_hook"] is False
    assert attrs["compaction.summary"] == "Summarised 47 turns to free context."


def test_compaction_span_without_usage():
    events = [
        {"type": "compaction", "timestamp": "2026-06-19T10:06:00Z",
         "summary": "Proactive compaction.", "tokensBefore": 90000},
    ]
    spans = OpenClawAdapter._build_spans_from_events(events, "sess1")
    assert len(spans) == 1
    sp = spans[0]
    assert sp["name"] == "compaction"
    attrs = sp["attributes"]
    assert attrs["event.kind"] == "compaction"
    assert attrs["compaction.tokens_before"] == 90000
    assert "compaction.usage.total_tokens" not in attrs


def test_compaction_span_id_is_deterministic():
    events = [
        {"type": "compaction", "timestamp": "2026-06-19T10:07:00Z"},
    ]
    a = OpenClawAdapter._build_spans_from_events(events, "s2")
    b = OpenClawAdapter._build_spans_from_events(events, "s2")
    assert a[0]["span_id"] == b[0]["span_id"]


def test_compaction_usage_inout_fallback():
    """When totalTokens is absent, input+output sum is used."""
    events = [
        {
            "type": "compaction",
            "timestamp": "2026-06-19T10:08:00Z",
            "usage": {"input_tokens": 5000, "output_tokens": 1200},
        },
    ]
    spans = OpenClawAdapter._build_spans_from_events(events, "sess1")
    assert spans[0]["attributes"]["compaction.usage.total_tokens"] == 6200


def test_extract_cost_tokens_compaction_top_level_usage():
    """_extract_cost_tokens_model reads totalTokens + cost from compaction's top-level usage."""
    obj = {
        "type": "compaction",
        "timestamp": "2026-06-19T10:05:00Z",
        "summary": "Context summarised.",
        "tokensBefore": 200000,
        "usage": {
            "totalTokens": 9500,
            "input_tokens": 8000,
            "output_tokens": 1500,
            "cost": {"total": 0.025},
        },
    }
    cost_usd, token_count, model = _extract_cost_tokens_model(obj)
    assert token_count == 9500, f"expected 9500 got {token_count}"
    assert cost_usd == 0.025


def test_extract_cost_tokens_no_regression_for_message_events():
    """Existing message events continue to read usage from message.usage."""
    obj = {
        "type": "message",
        "message": {
            "role": "assistant",
            "model": "claude-opus-4-7",
            "usage": {
                "totalTokens": 500,
                "cost": {"total": 0.01},
            },
        },
    }
    cost_usd, token_count, model = _extract_cost_tokens_model(obj)
    assert token_count == 500
    assert cost_usd == 0.01
    assert model == "claude-opus-4-7"


def test_extract_cost_tokens_compaction_cost_only():
    """cost_usd extracted even when totalTokens absent."""
    obj = {
        "type": "compaction",
        "usage": {"cost": {"total": 0.005}},
    }
    cost_usd, token_count, _model = _extract_cost_tokens_model(obj)
    assert cost_usd == 0.005
    assert token_count is None
