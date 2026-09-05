"""Tests for #5548 — OOM-victim preference for local model servers not tracked.

OpenClaw 2026.9.1+ ("A Gateway that stays up") lowers the gateway's own OOM
score so the kernel preferentially kills local model servers (e.g. Ollama)
under memory pressure.  Without this fix the kill shows up only as an
unexplained sandbox/model outage.

Fix: ``_gateway_oom_victim(events)`` scans the already-read gateway log events
for entries whose ``msg`` contains "oom" / "out of memory", or "killed"
alongside a model-server keyword.  ``detect()`` merges the result dict
(``oomVictimDetected``, ``oomVictimMsg``, optionally ``oomVictimTs``) into
``meta`` when a match is found.
"""
from __future__ import annotations

import pytest


def _fn():
    from clawmetry.adapters.openclaw import _gateway_oom_victim
    return _gateway_oom_victim


# ---------------------------------------------------------------------------
# Empty / no-match cases
# ---------------------------------------------------------------------------

def test_empty_events_returns_empty_dict():
    """No events → {} (no OOM state)."""
    assert _fn()([]) == {}


def test_none_input_returns_empty_dict():
    """Passing None instead of a list doesn't raise."""
    assert _fn()(None) == {}  # type: ignore[arg-type]


def test_unrelated_warn_returns_empty_dict():
    """A warn about disk I/O is not an OOM event."""
    events = [{"level": "warn", "msg": "slow disk I/O detected"}]
    assert _fn()(events) == {}


def test_killed_without_model_context_returns_empty_dict():
    """'killed' alone (no model/ollama/sandbox/server context) is not matched."""
    events = [{"level": "warn", "msg": "process killed by user"}]
    assert _fn()(events) == {}


def test_error_without_oom_returns_empty_dict():
    """An error entry unrelated to OOM is not matched."""
    events = [{"level": "error", "msg": "connection refused"}]
    assert _fn()(events) == {}


# ---------------------------------------------------------------------------
# Positive: "oom" keyword
# ---------------------------------------------------------------------------

def test_oom_in_msg_detected():
    """msg containing 'oom' is detected as an OOM victim event."""
    events = [{"msg": "oom kill: ollama process terminated", "ts": "2026-09-05T10:00:00Z"}]
    result = _fn()(events)
    assert result["oomVictimDetected"] is True
    assert "oom" in result["oomVictimMsg"].lower()
    assert result["oomVictimTs"] == "2026-09-05T10:00:00Z"


def test_oom_case_insensitive():
    """'OOM' (uppercase) is matched case-insensitively."""
    events = [{"msg": "OOM-kill: local model server stopped"}]
    result = _fn()(events)
    assert result["oomVictimDetected"] is True


def test_out_of_memory_phrase_detected():
    """'out of memory' phrase triggers the match."""
    events = [{"msg": "out of memory: ollama sandbox evicted"}]
    result = _fn()(events)
    assert result["oomVictimDetected"] is True


# ---------------------------------------------------------------------------
# Positive: "killed" + model-server keyword
# ---------------------------------------------------------------------------

def test_killed_with_model_keyword():
    """'killed' + 'model' in msg is detected."""
    events = [{"msg": "local model server killed by kernel"}]
    result = _fn()(events)
    assert result["oomVictimDetected"] is True


def test_killed_with_ollama_keyword():
    """'killed' + 'ollama' in msg is detected."""
    events = [{"msg": "ollama process killed unexpectedly"}]
    result = _fn()(events)
    assert result["oomVictimDetected"] is True


def test_killed_with_sandbox_keyword():
    """'killed' + 'sandbox' in msg is detected."""
    events = [{"msg": "sandbox inference server killed by OS"}]
    result = _fn()(events)
    assert result["oomVictimDetected"] is True


def test_killed_with_server_keyword():
    """'killed' + 'server' in msg is detected."""
    events = [{"msg": "inference server killed, gateway survived"}]
    result = _fn()(events)
    assert result["oomVictimDetected"] is True


# ---------------------------------------------------------------------------
# First-match semantics
# ---------------------------------------------------------------------------

def test_returns_first_matching_event():
    """When multiple OOM events exist, the first (newest-first list) is returned."""
    msg_first = "oom kill: ollama evicted (first)"
    msg_second = "oom kill: sandbox evicted (second)"
    events = [{"msg": msg_first}, {"msg": msg_second}]
    result = _fn()(events)
    assert result["oomVictimMsg"] == msg_first


def test_skips_non_matching_before_match():
    """Non-matching entries before an OOM entry don't block the result."""
    msg = "oom kill: model server sacrificed to keep gateway alive"
    events = [
        {"msg": "disk space low"},
        {"msg": "slow query on db"},
        {"msg": msg},
    ]
    result = _fn()(events)
    assert result["oomVictimDetected"] is True
    assert result["oomVictimMsg"] == msg


# ---------------------------------------------------------------------------
# Timestamp handling
# ---------------------------------------------------------------------------

def test_ts_included_when_present():
    """oomVictimTs is set when the event carries a 'ts' field."""
    events = [{"msg": "oom kill: ollama stopped", "ts": "2026-09-05T12:34:56Z"}]
    result = _fn()(events)
    assert result["oomVictimTs"] == "2026-09-05T12:34:56Z"


def test_ts_absent_when_not_in_event():
    """oomVictimTs is not present when the event has no 'ts' field."""
    events = [{"msg": "oom kill: model server evicted"}]
    result = _fn()(events)
    assert "oomVictimTs" not in result


# ---------------------------------------------------------------------------
# Robustness
# ---------------------------------------------------------------------------

def test_malformed_non_dict_entries_skipped():
    """Non-dict entries are silently skipped; the real entry is still found."""
    events = [None, "bad", 42, {"msg": "oom kill: ollama died"}]
    result = _fn()(events)
    assert result["oomVictimDetected"] is True


def test_missing_msg_key_does_not_raise():
    """Entries missing 'msg' are treated as non-matching; never raises."""
    events = [{"level": "warn", "ts": "2026-09-05"}, {"msg": "oom kill: server gone"}]
    result = _fn()(events)
    assert result["oomVictimDetected"] is True


def test_exception_in_events_returns_empty_dict():
    """An object whose iteration raises is handled gracefully."""
    class _Bad:
        def __iter__(self):
            raise RuntimeError("boom")

    assert _fn()(_Bad()) == {}  # type: ignore[arg-type]
