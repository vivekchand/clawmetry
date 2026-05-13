"""Tests for helpers/system.py — portable uptime replacement for `uptime -p`.

Covers the GNU/macOS portability fix from issue #1127.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Ensure the repo root (where helpers/ lives) is importable when pytest is
# invoked from anywhere.
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from helpers import system as sys_helpers  # noqa: E402


def test_format_uptime_none():
    assert sys_helpers.format_uptime(None) == "unknown"


def test_format_uptime_less_than_minute():
    assert sys_helpers.format_uptime(0) == "up less than a minute"
    assert sys_helpers.format_uptime(45) == "up less than a minute"


def test_format_uptime_singular_plural():
    # Plural form must match GNU `uptime -p` so the dashboard JS keeps
    # working (it strips the leading "up ").
    assert sys_helpers.format_uptime(60) == "up 1 minute"
    assert sys_helpers.format_uptime(120) == "up 2 minutes"
    assert sys_helpers.format_uptime(3600) == "up 1 hour"
    assert sys_helpers.format_uptime(7200) == "up 2 hours"
    assert sys_helpers.format_uptime(86400) == "up 1 day"
    assert sys_helpers.format_uptime(2 * 86400) == "up 2 days"


def test_format_uptime_compound():
    # 1 day + 1 hour + 1 minute
    assert sys_helpers.format_uptime(86400 + 3600 + 60) == "up 1 day, 1 hour, 1 minute"
    # 3 days + 4 hours + 12 minutes
    secs = 3 * 86400 + 4 * 3600 + 12 * 60
    assert sys_helpers.format_uptime(secs) == "up 3 days, 4 hours, 12 minutes"


def test_format_uptime_starts_with_up():
    # Dashboard JS does .replace("up ", "") — every non-unknown response
    # must start with "up " for that to work.
    for s in [60, 120, 3700, 90061, 86400]:
        out = sys_helpers.format_uptime(s)
        assert out.startswith("up "), f"format_uptime({s}) = {out!r}"


def test_boot_time_is_plausible_on_this_host():
    """boot_time() should return a sane POSIX timestamp on the test host."""
    import time

    bt = sys_helpers.boot_time()
    # Test runner has to be running on some OS we support — if it returns
    # None we've regressed portability.
    assert bt is not None, "boot_time() returned None on this host"
    # Boot must be in the past and within the last decade.
    assert bt < time.time()
    assert bt > time.time() - (10 * 365 * 86400)


def test_uptime_seconds_matches_boot_time():
    import time

    bt = sys_helpers.boot_time()
    if bt is None:
        pytest.skip("boot_time unavailable on this host")
    expected = int(time.time() - bt)
    actual = sys_helpers.uptime_seconds()
    # Allow up to 2s drift between the two clock reads.
    assert abs(actual - expected) <= 2


def test_uptime_pretty_round_trip():
    """End-to-end: real host -> pretty string starting with 'up '."""
    out = sys_helpers.uptime_pretty()
    assert isinstance(out, str)
    # We don't expect "unknown" on a real test host (Linux/macOS/Win all
    # have a supported path), but if a future runner lacks all 4 backends
    # we should still degrade gracefully rather than crash.
    assert out == "unknown" or out.startswith("up ")
