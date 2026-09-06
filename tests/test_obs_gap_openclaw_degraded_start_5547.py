"""Tests for #5547 — degraded-start (migration warning) Gateway state not captured.

OpenClaw 2026.9.1+ keeps the gateway process running when it encounters a
migration warning on boot, but enters a degraded state distinct from fully
healthy.  ``_gateway_live()`` only checks PID/port and returns True for both,
so the degraded state was previously invisible to ClawMetry.

Fix: ``_gateway_migration_warning(events)`` scans the already-read gateway log
events for warn/warning-level entries whose message contains "migration" and
returns the first match.  ``detect()`` surfaces ``gatewayDegraded=True`` and
``gatewayMigrationWarning=<msg>`` when a match is found.
"""
from __future__ import annotations

import pytest


def _fn():
    from clawmetry.adapters.openclaw import _gateway_migration_warning
    return _gateway_migration_warning


# ---------------------------------------------------------------------------
# Empty / no-warning cases
# ---------------------------------------------------------------------------

def test_empty_events_returns_none():
    """No events → None (no degraded state)."""
    assert _fn()([]) is None


def test_no_warning_level_returns_none():
    """Info-level migration entry is not a warning — should not trigger."""
    events = [{"level": "info", "msg": "migration check passed"}]
    assert _fn()(events) is None


def test_warn_unrelated_msg_returns_none():
    """warn-level entry whose msg doesn't mention migration → None."""
    events = [{"level": "warn", "msg": "slow disk I/O detected"}]
    assert _fn()(events) is None


def test_error_level_migration_returns_none():
    """error-level migration entry is not a warn → None."""
    events = [{"level": "error", "msg": "migration failed"}]
    assert _fn()(events) is None


# ---------------------------------------------------------------------------
# Positive cases
# ---------------------------------------------------------------------------

def test_warn_migration_returns_msg():
    """warn level + 'migration' in msg → returns the message string."""
    msg = "migration warning: schema v3 not yet applied, running in degraded mode"
    events = [{"level": "warn", "msg": msg, "ts": "2026-09-05T06:00:00Z"}]
    result = _fn()(events)
    assert result == msg


def test_warning_level_variant_accepted():
    """'warning' (spelled out) is also accepted as a warn level."""
    msg = "migration warning detected, gateway degraded"
    events = [{"level": "warning", "msg": msg}]
    assert _fn()(events) == msg


def test_returns_first_migration_warning():
    """When multiple migration warnings exist, the first (newest) is returned."""
    msg_first = "migration warning: pending migration foo"
    msg_second = "migration warning: pending migration bar"
    events = [
        {"level": "warn", "msg": msg_first},
        {"level": "warn", "msg": msg_second},
    ]
    assert _fn()(events) == msg_first


def test_skips_non_migration_warns_before_match():
    """Non-migration warns before the migration warn don't block the result."""
    msg = "migration warning: legacy column present"
    events = [
        {"level": "warn", "msg": "disk space low"},
        {"level": "warn", "msg": msg},
    ]
    assert _fn()(events) == msg


def test_case_insensitive_migration():
    """'Migration' (capitalised) is still matched."""
    msg = "Migration warning: table rename pending"
    events = [{"level": "warn", "msg": msg}]
    assert _fn()(events) == msg


# ---------------------------------------------------------------------------
# Robustness
# ---------------------------------------------------------------------------

def test_malformed_non_dict_entries_skipped():
    """Non-dict entries in the list are silently skipped; never raises."""
    events = [None, "bad", 42, {"level": "warn", "msg": "migration warning: ok"}]
    result = _fn()(events)
    assert result == "migration warning: ok"


def test_missing_keys_do_not_raise():
    """Entries missing 'level' or 'msg' are treated as non-matching; never raises."""
    events = [{"ts": "2026-09-05"}, {"level": "warn"}, {"msg": "migration warning"}]
    assert _fn()(events) is None


def test_none_input_returns_none():
    """Passing None instead of a list doesn't raise."""
    assert _fn()(None) is None  # type: ignore[arg-type]
