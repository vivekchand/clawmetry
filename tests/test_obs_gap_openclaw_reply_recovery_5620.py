"""Tests for #5620 — reply-recovery markers and retry attempts across Gateway
restarts not tracked.

OpenClaw 2026.9.2+ ('Replies survive restarts') recovers active, queued, and
delegated replies after Gateway restarts, guards against one completed reply
discarding another's recovery marker, and preserves continuation instructions
through compaction and retry attempts.  Per-turn ``recoveryMarker`` and
``retryAttempt`` fields are already read from session transcripts (landed in
the earlier #5577 fix); this covers the *gateway-level* restart recovery signal.

Fix: ``_reply_recovery_events(events)`` scans the already-read gateway log
events for recovery-related phrases and returns
``{"replyRecoveryDetected": True, "replyRecoveryCount": N, ...}`` or ``{}``.
``detect()`` merges the result into ``meta`` when a match is found.
"""
from __future__ import annotations

import pytest


def _fn():
    from clawmetry.adapters.openclaw import _reply_recovery_events
    return _reply_recovery_events


# ---------------------------------------------------------------------------
# Empty / no-match cases
# ---------------------------------------------------------------------------

def test_empty_events_returns_empty_dict():
    """No events → {} (no recovery state)."""
    assert _fn()([]) == {}


def test_none_input_returns_empty_dict():
    """Passing None instead of a list doesn't raise."""
    assert _fn()(None) == {}  # type: ignore[arg-type]


def test_unrelated_warn_returns_empty_dict():
    """A generic warn about disk I/O is not a recovery event."""
    events = [{"level": "warn", "msg": "slow disk I/O detected"}]
    assert _fn()(events) == {}


def test_error_without_recovery_keyword_returns_empty_dict():
    """An error entry unrelated to reply recovery is not matched."""
    events = [{"level": "error", "msg": "connection refused"}]
    assert _fn()(events) == {}


def test_restart_without_reply_context_returns_empty_dict():
    """'restart' alone (no reply/recovery context) is not matched."""
    events = [{"msg": "gateway restart initiated by user"}]
    assert _fn()(events) == {}


# ---------------------------------------------------------------------------
# Positive: "reply recovery" phrase
# ---------------------------------------------------------------------------

def test_reply_recovery_phrase_detected():
    """msg containing 'reply recovery' is detected."""
    events = [{"msg": "reply recovery: 3 active replies requeued", "ts": "2026-09-07T10:00:00Z"}]
    result = _fn()(events)
    assert result["replyRecoveryDetected"] is True
    assert result["replyRecoveryCount"] == 1
    assert result["lastReplyRecoveryTs"] == "2026-09-07T10:00:00Z"


def test_recovery_marker_phrase_detected():
    """msg containing 'recovery marker' is detected."""
    events = [{"msg": "recovery marker preserved for session abc123"}]
    result = _fn()(events)
    assert result["replyRecoveryDetected"] is True


def test_reply_restored_phrase_detected():
    """msg containing 'reply restored' is detected."""
    events = [{"msg": "reply restored after gateway restart"}]
    result = _fn()(events)
    assert result["replyRecoveryDetected"] is True


def test_reply_resumed_phrase_detected():
    """msg containing 'reply resumed' is detected."""
    events = [{"msg": "reply resumed: continuation instructions intact"}]
    result = _fn()(events)
    assert result["replyRecoveryDetected"] is True


def test_recover_reply_phrase_detected():
    """msg containing 'recover reply' is detected."""
    events = [{"msg": "attempting to recover reply from compacted state"}]
    result = _fn()(events)
    assert result["replyRecoveryDetected"] is True


def test_restart_recover_phrase_detected():
    """msg containing 'restart recover' is detected."""
    events = [{"msg": "restart recover: 2 delegated replies requeued"}]
    result = _fn()(events)
    assert result["replyRecoveryDetected"] is True


def test_reply_requeued_phrase_detected():
    """msg containing 'reply requeued' is detected."""
    events = [{"msg": "reply requeued after gateway restart"}]
    result = _fn()(events)
    assert result["replyRecoveryDetected"] is True


def test_reply_recovered_phrase_detected():
    """msg containing 'reply recovered' is detected."""
    events = [{"msg": "reply recovered: marker guard applied"}]
    result = _fn()(events)
    assert result["replyRecoveryDetected"] is True


# ---------------------------------------------------------------------------
# Case-insensitivity
# ---------------------------------------------------------------------------

def test_matching_is_case_insensitive():
    """'Reply Recovery' (capitalised) is still matched."""
    events = [{"msg": "Reply Recovery: session abc resumed"}]
    result = _fn()(events)
    assert result["replyRecoveryDetected"] is True


# ---------------------------------------------------------------------------
# Count semantics
# ---------------------------------------------------------------------------

def test_count_reflects_number_of_matching_events():
    """replyRecoveryCount equals the number of matching log entries."""
    events = [
        {"msg": "reply recovery: queued reply 1 restored"},
        {"msg": "unrelated log line"},
        {"msg": "reply recovery: queued reply 2 restored"},
        {"msg": "reply recovery: delegated reply 3 requeued"},
    ]
    result = _fn()(events)
    assert result["replyRecoveryCount"] == 3


def test_last_ts_is_from_last_matching_event():
    """lastReplyRecoveryTs comes from the last matching entry, not the first."""
    events = [
        {"msg": "reply recovery: reply 1", "ts": "2026-09-07T10:00:00Z"},
        {"msg": "unrelated"},
        {"msg": "reply recovery: reply 2", "ts": "2026-09-07T10:01:00Z"},
    ]
    result = _fn()(events)
    assert result["lastReplyRecoveryTs"] == "2026-09-07T10:01:00Z"


# ---------------------------------------------------------------------------
# Timestamp handling
# ---------------------------------------------------------------------------

def test_ts_included_when_present():
    """lastReplyRecoveryTs is set when the last matching event carries 'ts'."""
    events = [{"msg": "reply recovery: 1 reply restored", "ts": "2026-09-07T12:34:56Z"}]
    result = _fn()(events)
    assert result["lastReplyRecoveryTs"] == "2026-09-07T12:34:56Z"


def test_ts_absent_when_not_in_event():
    """lastReplyRecoveryTs is not present when the matching event has no 'ts'."""
    events = [{"msg": "reply recovery: marker guard ok"}]
    result = _fn()(events)
    assert "lastReplyRecoveryTs" not in result


# ---------------------------------------------------------------------------
# Robustness
# ---------------------------------------------------------------------------

def test_malformed_non_dict_entries_skipped():
    """Non-dict entries are silently skipped; the real entry is still found."""
    events = [None, "bad", 42, {"msg": "reply recovery: 1 active reply restored"}]
    result = _fn()(events)
    assert result["replyRecoveryDetected"] is True


def test_missing_msg_key_does_not_raise():
    """Entries missing 'msg' are treated as non-matching; never raises."""
    events = [{"level": "warn", "ts": "2026-09-07"}, {"msg": "reply recovery: ok"}]
    result = _fn()(events)
    assert result["replyRecoveryDetected"] is True


def test_exception_in_events_returns_empty_dict():
    """An object whose iteration raises is handled gracefully."""
    class _Bad:
        def __iter__(self):
            raise RuntimeError("boom")

    assert _fn()(_Bad()) == {}  # type: ignore[arg-type]
