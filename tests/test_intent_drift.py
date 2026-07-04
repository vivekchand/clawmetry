"""Unit tests for _detect_intent_drift_from_events (issue #3442).

Verifies the DuckDB-events path of the intent-drift helper introduced in
/api/sessions/<id>/intent-drift.  Tests use synthetic event dicts that
mirror the shape the sync daemon writes (event_type / ts / data fields)
without requiring DuckDB, a running daemon, or a Flask app.
"""

from __future__ import annotations

from routes.sessions import _detect_intent_drift_from_events


def test_intent_drift_fires_on_read_claim_then_write():
    """INT-001: assistant claims to read but the next tool call is a write."""
    events = [
        {
            "event_type": "message",
            "ts": "2026-07-02T01:00:00",
            "id": 1,
            "data": {
                "role": "assistant",
                "content": "I'll just read the file to check it",
            },
        },
        {
            "event_type": "message",
            "ts": "2026-07-02T01:00:01",
            "id": 2,
            "data": {"tool_calls": [{"name": "write_file"}]},
        },
    ]
    result = _detect_intent_drift_from_events(events)
    assert result["has_drift"] is True
    assert result["drift_count"] >= 1
    assert result["flags"][0]["check_id"] == "INT-001"


def test_intent_drift_clean_session_returns_zero():
    """Clean session with matching intent and tool returns drift_count=0."""
    events = [
        {
            "event_type": "message",
            "ts": "2026-07-02T01:00:00",
            "id": 1,
            "data": {
                "role": "assistant",
                "content": "I will read the file",
            },
        },
        {
            "event_type": "message",
            "ts": "2026-07-02T01:00:01",
            "id": 2,
            "data": {"tool_calls": [{"name": "read_file"}]},
        },
    ]
    result = _detect_intent_drift_from_events(events)
    assert result["has_drift"] is False
    assert result["drift_count"] == 0
    assert result["flags"] == []
