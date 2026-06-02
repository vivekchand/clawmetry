"""Unit tests for the `clawmetry status --live` line builder (pure part)."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from clawmetry.cli import _status_live_line


def test_aggregates_sessions_tokens_cost_and_recent_model():
    rows = [
        {"session_id": "a", "total_tokens": 1000, "cost_usd": 0.50, "model": "claude-opus", "updated_at": "2026-06-02T10:00:00"},
        {"session_id": "b", "total_tokens": 500, "cost_usd": 0.20, "model": "gpt-5", "updated_at": "2026-06-02T11:00:00"},
    ]
    line, prev = _status_live_line(rows, None, 100.0)
    assert "2 sessions" in line and "1,500 tokens" in line and "$0.7000" in line
    assert "gpt-5" in line          # most-recently-updated session's model
    assert "0 tok/s" in line        # first sample has no rate
    assert prev == (1500, 100.0)


def test_tps_from_token_delta_over_time():
    prev = (1500, 100.0)
    rows = [
        {"session_id": "a", "total_tokens": 1000, "cost_usd": 0.5, "model": "gpt-5", "updated_at": "2026-06-02T10:00:00"},
        {"session_id": "b", "total_tokens": 700, "cost_usd": 0.3, "model": "gpt-5", "updated_at": "2026-06-02T11:00:05"},
    ]
    line, _ = _status_live_line(rows, prev, 110.0)   # +200 tokens in 10s
    assert "20 tok/s" in line


def test_empty_is_safe():
    line, prev = _status_live_line([], None, 1.0)
    assert "0 sessions" in line and prev == (0, 1.0)
