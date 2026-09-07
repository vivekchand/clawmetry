"""Tests for #5578 — openclaw response_steered events produce spans in the Tracing tab.

The harness emits a ``"response_steered"`` JSONL event (openclaw CHANGELOG 2026.9.2,
#138046/#138434) when a running response is steered mid-flight over a cached WebSocket
during async direct function-tool execution. Before this fix ``_build_spans_from_events``
had no branch for the ``response_steered`` type, so every steering event fell through
the loop silently, leaving the activity invisible in the Timeline and Brain stream tabs.
"""
from __future__ import annotations

from clawmetry.adapters.openclaw import OpenClawAdapter


def test_response_steered_produces_span_with_count_and_tool_id():
    events = [
        {"type": "session", "version": "1.0", "timestamp": "2026-09-06T00:00:00Z"},
        {
            "type": "response_steered",
            "timestamp": "2026-09-06T00:00:01Z",
            "steeringCount": 2,
            "asyncToolId": "t_abc123",
        },
    ]
    spans = OpenClawAdapter._build_spans_from_events(events, "s1")
    by_name = {s["name"]: s for s in spans}
    assert "response.steered" in by_name, "response_steered event must produce a span"
    span = by_name["response.steered"]
    assert span["kind"] == "INTERNAL"
    assert span["parent_span_id"] == by_name["session"]["span_id"]
    attrs = span["attributes"]
    assert attrs["event.kind"] == "response_steered"
    assert attrs["steering.count"] == 2
    assert attrs["steering.async_tool_id"] == "t_abc123"


def test_response_steered_accepts_snake_case_fields():
    events = [
        {
            "type": "response_steered",
            "timestamp": "2026-09-06T00:00:02Z",
            "steering_count": 3,
            "async_tool_id": "t_xyz",
            "continuation_id": "cont_001",
        },
    ]
    spans = OpenClawAdapter._build_spans_from_events(events, "s2")
    assert len(spans) == 1
    attrs = spans[0]["attributes"]
    assert attrs["steering.count"] == 3
    assert attrs["steering.async_tool_id"] == "t_xyz"
    assert attrs["steering.continuation_id"] == "cont_001"


def test_response_steered_accepts_camelcase_continuation():
    events = [
        {
            "type": "response_steered",
            "timestamp": "2026-09-06T00:00:03Z",
            "steeringCount": 1,
            "toolCallId": "tc_99",
            "continuationId": "c_42",
        },
    ]
    spans = OpenClawAdapter._build_spans_from_events(events, "s3")
    assert len(spans) == 1
    attrs = spans[0]["attributes"]
    assert attrs["steering.count"] == 1
    assert attrs["steering.async_tool_id"] == "tc_99"
    assert attrs["steering.continuation_id"] == "c_42"


def test_response_steered_minimal_payload_still_emits_span():
    events = [{"type": "response_steered", "timestamp": "2026-09-06T00:00:04Z"}]
    spans = OpenClawAdapter._build_spans_from_events(events, "s4")
    assert len(spans) == 1
    assert spans[0]["name"] == "response.steered"
    assert spans[0]["attributes"] == {"event.kind": "response_steered"}


def test_response_steered_span_ids_are_deterministic():
    events = [{"type": "response_steered", "timestamp": "2026-09-06T00:00:05Z", "steeringCount": 1}]
    a = OpenClawAdapter._build_spans_from_events(events, "s5")
    b = OpenClawAdapter._build_spans_from_events(events, "s5")
    assert a[0]["span_id"] == b[0]["span_id"]
