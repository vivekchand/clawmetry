"""``sync._seconds_since`` must honour a UTC ``Z`` suffix.

Burned 2026-09-11: hook-parked AskUserQuestion approvals are stamped
``created_at=...Z`` (UTC). ``_seconds_since`` stripped the ``Z`` and compared
the result against local wall-clock, so on a CEST machine the cloud strip said
"waiting 2h 2m" for a question asked four minutes earlier. Naive strings are
still local wall-clock, which is what most store rows carry.
"""

from __future__ import annotations

import os
import time
from datetime import datetime, timedelta, timezone

import pytest

from clawmetry.sync import _seconds_since

pytestmark = pytest.mark.skipif(not hasattr(time, "tzset"),
                                reason="needs time.tzset (POSIX)")


@pytest.fixture(autouse=True)
def _cest():
    old = os.environ.get("TZ")
    os.environ["TZ"] = "Europe/Amsterdam"
    time.tzset()
    yield
    if old is None:
        os.environ.pop("TZ", None)
    else:
        os.environ["TZ"] = old
    time.tzset()


def _utc_ago(secs):
    return datetime.now(timezone.utc) - timedelta(seconds=secs)


def test_z_suffix_is_utc_not_local():
    ts = _utc_ago(240).strftime("%Y-%m-%dT%H:%M:%SZ")
    assert 235 <= _seconds_since(ts) <= 250


def test_offset_with_microseconds():
    ts = _utc_ago(30).isoformat()
    assert 25 <= _seconds_since(ts) <= 40


def test_short_fraction_with_z_falls_back_but_stays_utc():
    # Python 3.9's fromisoformat rejects a 3-digit fraction; the fallback must
    # still treat the value as UTC.
    ts = _utc_ago(60).strftime("%Y-%m-%dT%H:%M:%S") + ".123Z"
    assert 55 <= _seconds_since(ts) <= 70


def test_naive_is_local_wall_clock():
    ts = (datetime.now() - timedelta(seconds=90)).strftime("%Y-%m-%dT%H:%M:%S")
    assert 85 <= _seconds_since(ts) <= 100


@pytest.mark.parametrize("bad", [None, "", "not a time", 42])
def test_garbage_is_zero(bad):
    assert _seconds_since(bad) == 0
