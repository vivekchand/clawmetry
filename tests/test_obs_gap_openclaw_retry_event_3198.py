"""Tests for #3198 — openclaw retry events produce spans in the Tracing tab.

The harness emits a ``"retry"`` JSONL event (openclaw 2026.6.9, #92191/#93073)
when the agent retries a thinking-only or empty post-tool turn. Before this fix
``_build_spans_from_events`` had no branch for the ``retry`` type, so every
retry event fell through the loop and produced no span — leaving a silent gap
in the trace wherever a retry occurred.
"""
from __future__ import annotations

from clawmetry.adapters.openclaw import OpenClawAdapter


def test_retry_event_produces_span_with_reason_and_turn_kind():
    events = [
        {"type": "session", "version": "1.0", "timestamp": "2026-06-19T00:00:00Z"},
        {
            "type": "retry",
            "timestamp": "2026-06-19T00:00:01Z",
            "reason": "thinking_only",
            "turn_kind": "post_tool",
        },
    ]
    spans = OpenClawAdapter._build_spans_from_events(events, "s1")
    by_name = {s["name"]: s for s in spans}
    assert "retry" in by_name, "retry event must produce a span"
    span = by_name["retry"]
    assert span["kind"] == "INTERNAL"
    assert span["parent_span_id"] == by_name["session"]["span_id"]
    attrs = span["attributes"]
    assert attrs["event.kind"] == "retry"
    assert attrs["retry.reason"] == "thinking_only"
    assert attrs["retry.turn_kind"] == "post_tool"


def test_retry_event_with_count():
    events = [
        {
            "type": "retry",
            "timestamp": "2026-06-19T00:00:02Z",
            "reason": "empty_post_tool",
            "turn_kind": "thinking_only",
            "count": 2,
        },
    ]
    spans = OpenClawAdapter._build_spans_from_events(events, "s2")
    assert len(spans) == 1
    attrs = spans[0]["attributes"]
    assert attrs["retry.reason"] == "empty_post_tool"
    assert attrs["retry.turn_kind"] == "thinking_only"
    assert attrs["retry.count"] == 2


def test_retry_event_accepts_camelcase_fields():
    events = [
        {
            "type": "retry",
            "timestamp": "2026-06-19T00:00:03Z",
            "retryReason": "thinking_only",
            "turnKind": "post_tool",
            "retryCount": 3,
        },
    ]
    spans = OpenClawAdapter._build_spans_from_events(events, "s3")
    assert len(spans) == 1
    attrs = spans[0]["attributes"]
    assert attrs["retry.reason"] == "thinking_only"
    assert attrs["retry.turn_kind"] == "post_tool"
    assert attrs["retry.count"] == 3


def test_retry_event_minimal_payload_still_emits_span():
    events = [{"type": "retry", "timestamp": "2026-06-19T00:00:04Z"}]
    spans = OpenClawAdapter._build_spans_from_events(events, "s4")
    assert len(spans) == 1
    assert spans[0]["name"] == "retry"
    assert spans[0]["attributes"] == {"event.kind": "retry"}


def test_retry_span_ids_are_deterministic():
    events = [{"type": "retry", "timestamp": "2026-06-19T00:00:05Z", "reason": "thinking_only"}]
    a = OpenClawAdapter._build_spans_from_events(events, "s5")
    b = OpenClawAdapter._build_spans_from_events(events, "s5")
    assert a[0]["span_id"] == b[0]["span_id"]
