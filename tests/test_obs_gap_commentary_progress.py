"""Tests for #3015 — Claude CLI commentary/progress JSONL events become spans.

The harness emits inter-tool ``commentary`` and long-running ``progress``
events as distinct JSONL ``type`` values. Before #3015 the span builder only
matched ``session``/``message``/``subagent_spawn``/``agent_spawn`` and let these
fall through every branch, dropping the span and discarding the payload.
"""
from __future__ import annotations

from clawmetry.adapters.openclaw import OpenClawAdapter


def test_commentary_event_produces_span_with_text():
    events = [
        {"type": "session", "version": "1.0", "timestamp": "2026-06-05T00:00:00Z"},
        {"type": "commentary", "timestamp": "2026-06-05T00:00:01Z",
         "text": "Let me check the config first.", "subtype": "thinking"},
    ]
    spans = OpenClawAdapter._build_spans_from_events(events, "s1")
    by_name = {s["name"]: s for s in spans}
    assert "commentary" in by_name, "commentary event must produce a span"
    span = by_name["commentary"]
    assert span["kind"] == "INTERNAL"
    # parented to the session root span
    assert span["parent_span_id"] == by_name["session"]["span_id"]
    assert span["attributes"]["event.kind"] == "commentary"
    assert span["attributes"]["commentary.text"] == "Let me check the config first."
    assert span["attributes"]["commentary.subtype"] == "thinking"


def test_progress_event_reads_nested_data_blob():
    events = [
        {"type": "progress", "timestamp": "2026-06-05T00:00:02Z",
         "data": {"content": "Step 3/10 complete", "label": "tool_progress"}},
    ]
    spans = OpenClawAdapter._build_spans_from_events(events, "s1")
    assert len(spans) == 1
    attrs = spans[0]["attributes"]
    assert spans[0]["name"] == "progress"
    assert attrs["event.kind"] == "progress"
    assert attrs["commentary.text"] == "Step 3/10 complete"
    assert attrs["commentary.subtype"] == "tool_progress"


def test_commentary_without_text_still_emits_span():
    """Payload-less commentary still yields a span so the timeline is complete;
    it just carries no quick-read text attribute."""
    events = [{"type": "commentary", "timestamp": "2026-06-05T00:00:03Z"}]
    spans = OpenClawAdapter._build_spans_from_events(events, "s1")
    assert len(spans) == 1
    attrs = spans[0]["attributes"]
    assert attrs == {"event.kind": "commentary"}


def test_span_ids_are_deterministic_for_idempotent_reingest():
    events = [{"type": "commentary", "timestamp": "2026-06-05T00:00:04Z", "text": "hi"}]
    a = OpenClawAdapter._build_spans_from_events(events, "s1")
    b = OpenClawAdapter._build_spans_from_events(events, "s1")
    assert a[0]["span_id"] == b[0]["span_id"]
