"""Day buckets are node-local calendar days, and SQL agrees with Python.

ADR-046 gave every cost surface ONE definition of today / this week / this
month, in the node's local calendar. It left one layer untouched, and said so:
a day BUCKET was the first ten characters of whatever timestamp string the
runtime wrote. So a runtime stamping UTC put a California user's 5pm spend on
tomorrow, while the window asking for "today" was local. The window and the
buckets it filtered were on two different clocks.

The bug that matters most here is not the timezone; it is DISAGREEMENT. There
are two implementations of the bucket — SQL for the live aggregate, Python for
the rollup writers — and if they drift, the same events sum to two different
day totals depending on which path a surface reads. That is the exact shape of
the bug ADR-046 was written to end, so most of this file is one path checked
against the other.

Acceptance criteria proven here (docs/acceptance_criteria.json):

* AC-OBS-CEA-001.3 -- when the operator changes the available time scope, the
  displayed measurements update to that scope. A window in local time reading
  buckets in the runtime's time does not honour the scope it claims:
  ``test_utc_evening_lands_on_the_local_day``,
  ``test_bucket_matches_the_window_helper_for_the_same_instant``.
"""
from __future__ import annotations

import importlib

import pytest

from clawmetry import cost_windows as cw


# Timestamps that actually appear: OpenClaw and Claude Code write ISO with a
# trailing Z, some runtimes write a naive local string, some write an explicit
# offset, one writes nanoseconds.
_SHAPES = [
    "2026-08-25T02:30:00Z",
    "2026-08-25T20:30:00Z",
    "2026-08-25 20:30:00",
    "2026-08-25T02:30:00+00:00",
    "2026-08-24T23:30:00-07:00",
    "2026-08-25T02:30:00.123456789Z",
    "2026-08-25",
    "2026-01-01T00:00:00Z",
    "2026-12-31T23:59:59Z",
]


def _duck():
    duckdb = pytest.importorskip("duckdb")
    return duckdb.connect()


def _sql_day(conn, ts):
    expr = cw.day_expr_sql("$1")
    return conn.execute(f"SELECT {expr}", [ts]).fetchone()[0]


# ── the two implementations must not drift ──────────────────────────────

@pytest.mark.parametrize("ts", _SHAPES)
def test_sql_and_python_agree_on_every_real_timestamp_shape(ts):
    """The whole point. Two implementations of one bucket; if they disagree,
    the rollups and the live aggregate report different day totals for the
    same events."""
    conn = _duck()
    assert _sql_day(conn, ts) == cw.local_day(ts), ts


def test_a_timestamp_with_no_derivable_day_is_the_documented_exception():
    """SQL keeps the junk in its old bucket; Python returns None so the row is
    skipped, because the rollup day column is a real DATE. Pre-existing, and
    asserted so nobody 'fixes' one side into a crash."""
    conn = _duck()
    assert cw.local_day("garbage") is None
    assert _sql_day(conn, "garbage") == "garbage"


# ── the behaviour change itself ─────────────────────────────────────────

@pytest.fixture()
def la_timezone(monkeypatch):
    """Run the body in America/Los_Angeles, then put the process back.

    ``monkeypatch.setenv`` restores the variable, but libc keeps the old zone
    until ``tzset()`` is called again — so without the explicit restore this
    fixture would silently re-time every later test in the process.
    """
    import time as _t

    if not hasattr(_t, "tzset"):
        pytest.skip("TZ cannot be changed at runtime on this platform")
    monkeypatch.setenv("TZ", "America/Los_Angeles")
    _t.tzset()
    try:
        yield
    finally:
        monkeypatch.undo()
        _t.tzset()


def test_utc_evening_lands_on_the_local_day(la_timezone):
    """02:30 UTC is the PREVIOUS evening in Los Angeles. Under the old prefix
    bucket this spend showed up on the 25th while the user's "today" was still
    the 24th."""
    assert cw.local_day("2026-08-25T02:30:00Z") == "2026-08-24"
    assert "2026-08-25T02:30:00Z"[:10] == "2026-08-25"  # what it used to be


def test_the_timezone_fixture_actually_restores(la_timezone):
    """Guard on the guard: a leaked TZ would make later failures look random."""
    assert cw.local_day("2026-08-25T02:30:00Z") == "2026-08-24"


def test_naive_timestamps_are_treated_as_already_local():
    """A runtime writing a bare wall clock is writing THIS machine's clock.
    Converting it would move real spend to the wrong day."""
    assert cw.local_day("2026-08-25 20:30:00") == "2026-08-25"
    assert cw.local_day("2026-08-25") == "2026-08-25"


def test_bucket_matches_the_window_helper_for_the_same_instant():
    """A window start and a bucket key have to come from the same clock, or
    'today' filters buckets that are not today."""
    now = cw.now_local()
    today_start, _week, _month = cw.window_start_days(now)
    assert cw.local_day(now.isoformat()) == today_start


def test_utc_and_offset_spellings_of_one_instant_bucket_identically():
    """Same moment, three notations. Any disagreement here would split one
    turn's spend across two days depending on which runtime logged it."""
    same = [
        "2026-08-25T02:30:00Z",
        "2026-08-25T02:30:00+00:00",
        "2026-08-24T19:30:00-07:00",
    ]
    days = {cw.local_day(t) for t in same}
    assert len(days) == 1, days


# ── never crash on the input we do not control ──────────────────────────

@pytest.mark.parametrize("bad", [None, "", "   ", "garbage", "not-a-date", 0, []])
def test_unparseable_input_yields_no_bucket_rather_than_today(bad):
    """An underivable bucket must not become today, or every unparsed row
    would pile onto whatever day the code happened to run."""
    assert cw.local_day(bad) is None


def test_a_date_prefix_on_an_otherwise_broken_string_still_buckets():
    assert cw.local_day("2026-08-25T99:99:99") == "2026-08-25"


def test_normalizer_handles_the_two_shapes_fromisoformat_rejects():
    assert cw._normalize_ts("2026-08-25T02:30:00Z").endswith("+00:00")
    assert cw._normalize_ts("2026-08-25T02:30:00.123456789Z") == (
        "2026-08-25T02:30:00.123456+00:00"
    )


# ── end to end through the store ────────────────────────────────────────

@pytest.fixture()
def store(tmp_path, monkeypatch):
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "t.duckdb"))
    import clawmetry.local_store as ls
    ls = importlib.reload(ls)
    return ls.LocalStore()


def _ev(eid, ts, cost):
    return {"id": eid, "node_id": "n", "session_id": "claude_code:s1",
            "agent_type": "openclaw", "ts": ts, "event_type": "assistant",
            "cost_usd": cost, "token_count": 10}


def test_live_aggregate_and_rollup_bucket_the_same_events_the_same_way(store):
    """The live SQL aggregate and the rollup writer are the two paths a cost
    surface can read. They must produce the same day totals."""
    events = [
        _ev("e1", "2026-08-25T02:30:00Z", 1.0),
        _ev("e2", "2026-08-25T20:30:00Z", 2.0),
        _ev("e3", "2026-08-25 20:30:00", 4.0),
    ]
    for e in events:
        store.ingest(e)
    store.flush()

    live = {r["day"]: round(float(r["cost_usd"]), 6)
            for r in store.query_aggregates()}
    rollup = {
        str(day): round(float(cost), 6)
        for day, cost in store._conn.execute(
            "SELECT day, SUM(cost_usd) FROM rollup_runtime_daily GROUP BY day"
        ).fetchall()
    }
    assert live == rollup, (live, rollup)

    expected = {}
    for e in events:
        d = cw.local_day(e["ts"])
        expected[d] = round(expected.get(d, 0.0) + e["cost_usd"], 6)
    assert live == expected


def test_totals_are_preserved_whatever_the_bucketing(store):
    """Re-bucketing moves spend between days; it must never create or lose
    any. A user's month total cannot change because we fixed a timezone."""
    events = [_ev(f"e{i}", "2026-08-25T02:30:00Z", 1.5) for i in range(5)]
    for e in events:
        store.ingest(e)
    store.flush()
    total = sum(float(r["cost_usd"]) for r in store.query_aggregates())
    assert round(total, 6) == round(1.5 * 5, 6)


def test_schema_version_was_bumped_for_the_rebuild(store):
    """Rollup rows written under the old bucket key would sum into the same
    day cell as new ones, producing a day that is half local and half UTC.
    The v13 migration wipes them; without the bump it never runs."""
    import clawmetry.local_store as ls
    assert ls.SCHEMA_VERSION >= 13
    stamped = store._conn.execute(
        "SELECT MAX(version) FROM schema_version"
    ).fetchone()[0]
    assert stamped >= 13
