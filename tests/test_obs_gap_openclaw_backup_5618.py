"""Regression tests for the backup-outcome gateway event scanner.

Closes: vivekchand/clawmetry#5618
"""
import pytest
from clawmetry.adapters.openclaw import _backup_outcome_events


# ---------------------------------------------------------------------------
# corrupt-archive rejection
# ---------------------------------------------------------------------------

def test_corrupt_archive_rejection_detected():
    events = [
        {"msg": "backup rejected: corrupt archive header detected", "ts": "2026-09-07T01:00:00Z"},
    ]
    result = _backup_outcome_events(events)
    assert result["backupOutcomeDetected"] is True
    assert result["backupCorruptArchiveRejected"] is True
    assert result["backupOutcomeTs"] == "2026-09-07T01:00:00Z"
    assert "corrupt archive header" in result["backupOutcomeMsg"]


def test_backup_integrity_failure_detected():
    events = [
        {"msg": "backup integrity check failed — archive is incomplete", "ts": "2026-09-07T02:00:00Z"},
    ]
    result = _backup_outcome_events(events)
    assert result["backupOutcomeDetected"] is True
    assert result["backupCorruptArchiveRejected"] is True


# ---------------------------------------------------------------------------
# plain backup failure (no corrupt keyword)
# ---------------------------------------------------------------------------

def test_plain_backup_failure_no_corrupt_flag():
    events = [
        {"msg": "backup failed: disk write error"},
    ]
    result = _backup_outcome_events(events)
    assert result["backupOutcomeDetected"] is True
    assert result.get("backupCorruptArchiveRejected") is None


# ---------------------------------------------------------------------------
# backup success
# ---------------------------------------------------------------------------

def test_backup_success_detected():
    events = [
        {"msg": "backup completed successfully", "ts": "2026-09-07T03:00:00Z"},
    ]
    result = _backup_outcome_events(events)
    assert result["backupOutcomeDetected"] is True
    assert result.get("backupCorruptArchiveRejected") is None


# ---------------------------------------------------------------------------
# no backup events → empty dict
# ---------------------------------------------------------------------------

def test_no_backup_events_returns_empty():
    events = [
        {"msg": "gateway started", "ts": "2026-09-07T00:00:00Z"},
        {"msg": "oom: model server killed", "ts": "2026-09-07T00:01:00Z"},
    ]
    assert _backup_outcome_events(events) == {}


def test_empty_events_list():
    assert _backup_outcome_events([]) == {}


def test_none_msg_skipped():
    events = [{"msg": None}, {"msg": "backup done"}]
    result = _backup_outcome_events(events)
    assert result["backupOutcomeDetected"] is True


# ---------------------------------------------------------------------------
# exception safety
# ---------------------------------------------------------------------------

def test_exception_safety_returns_empty():
    assert _backup_outcome_events(None) == {}  # type: ignore[arg-type]
    assert _backup_outcome_events("not-a-list") == {}  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# first matching event wins
# ---------------------------------------------------------------------------

def test_first_backup_event_wins():
    events = [
        {"msg": "backup rejected: corrupt archive", "ts": "2026-09-07T01:00:00Z"},
        {"msg": "backup completed", "ts": "2026-09-07T02:00:00Z"},
    ]
    result = _backup_outcome_events(events)
    assert result["backupOutcomeTs"] == "2026-09-07T01:00:00Z"
    assert result["backupCorruptArchiveRejected"] is True
