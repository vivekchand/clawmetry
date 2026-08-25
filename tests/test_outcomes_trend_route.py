"""``GET /api/outcomes/trend`` — the "is my agent improving?" endpoint.

Free tier on purpose: it answers the one Evaluate question a fleet tool is
positioned to win, using outcome + cost data every install already has, with
no judge key and no API spend.

Pins the parts that would silently mislead if they drifted:

- the two periods are split by timestamp, not by fetch order;
- rows with no usable timestamp are dropped rather than charged to the
  current window, which would manufacture a trend out of undated backfill;
- an unreachable store degrades to ``store_available: false`` and a 200, never a
  500 (the issue #1127 lesson the sibling /api/outcomes route already learnt).
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from flask import Flask


def _app():
    from routes.sessions import bp_sessions

    app = Flask(__name__)
    app.register_blueprint(bp_sessions)
    return app


def _iso(days_ago: float) -> str:
    dt = datetime.now(timezone.utc) - timedelta(days=days_ago)
    return dt.isoformat().replace("+00:00", "Z")


def _row(outcome, days_ago, cost=1.0, sid=None):
    return {
        "session_id": sid or f"{outcome}-{days_ago}",
        "outcome": outcome,
        "cost_usd": cost,
        "total_tokens": 500,
        "last_active_at": _iso(days_ago),
    }


@pytest.fixture
def store_rows(monkeypatch):
    """Swap the DuckDB hop for a list the test controls."""
    holder = {"rows": []}

    def _fake(method_name, **kwargs):
        assert method_name == "query_outcomes"
        holder["kwargs"] = kwargs
        return holder["rows"]

    monkeypatch.setattr("routes.sessions._ls_call", _fake)
    return holder


# ── period split ────────────────────────────────────────────────────────────


def test_rows_land_in_the_period_their_timestamp_belongs_to(store_rows):
    """3 days ago is this week; 10 days ago is the week before it."""
    store_rows["rows"] = [
        _row("success", 1), _row("success", 2), _row("success", 3),
        _row("failed", 3),
        _row("failed", 9), _row("failed", 10), _row("failed", 11),
        _row("success", 12),
    ]
    with _app().test_client() as c:
        body = c.get("/api/outcomes/trend?window=7d").get_json()
    assert body["store_available"] is True
    assert body["current"]["finished"] == 4
    assert body["previous"]["finished"] == 4
    assert body["current"]["success_rate"] == 0.75
    assert body["previous"]["success_rate"] == 0.25
    assert body["direction"] == "improving"


def test_one_read_covers_both_windows(store_rows):
    """Two round-trips would double the daemon-proxy cost of a non-headline
    card, so the handler fetches 2x the window once and splits in Python."""
    store_rows["rows"] = []
    with _app().test_client() as c:
        c.get("/api/outcomes/trend?window=7d")
    since = store_rows["kwargs"]["since"]
    age_days = (
        datetime.now(timezone.utc)
        - datetime.fromisoformat(since.replace("Z", "+00:00"))
    ).days
    assert 13 <= age_days <= 14, f"expected a 14d read for a 7d window, got {since}"


def test_undated_rows_are_dropped_not_counted_as_current(store_rows):
    """An undated backfill row charged to "this week" would invent a trend."""
    store_rows["rows"] = [
        {"session_id": "ghost", "outcome": "failed", "last_active_at": None},
        {"session_id": "ghost2", "outcome": "failed", "last_active_at": ""},
    ]
    with _app().test_client() as c:
        body = c.get("/api/outcomes/trend?window=7d").get_json()
    assert body["current"]["total"] == 0
    assert body["previous"]["total"] == 0
    assert body["direction"] == "unknown"


def test_ended_at_is_used_when_last_active_is_missing(store_rows):
    store_rows["rows"] = [
        {"session_id": "s1", "outcome": "success", "ended_at": _iso(1)},
    ]
    with _app().test_client() as c:
        body = c.get("/api/outcomes/trend?window=7d").get_json()
    assert body["current"]["total"] == 1


# ── window + runtime handling ───────────────────────────────────────────────


def test_unknown_window_falls_back_to_7d(store_rows):
    store_rows["rows"] = []
    with _app().test_client() as c:
        body = c.get("/api/outcomes/trend?window=bananas").get_json()
    assert body["window"] == "7d"


def test_runtime_is_passed_through_and_echoed(store_rows):
    """Per-runtime honesty: a number shown under the runtime switcher must
    scope to that runtime, and the payload has to say which one it is."""
    store_rows["rows"] = []
    with _app().test_client() as c:
        body = c.get("/api/outcomes/trend?runtime=claude_code").get_json()
    assert store_rows["kwargs"]["runtime"] == "claude_code"
    assert body["runtime"] == "claude_code"


def test_node_wide_is_labelled_all(store_rows):
    store_rows["rows"] = []
    with _app().test_client() as c:
        body = c.get("/api/outcomes/trend").get_json()
    assert body["runtime"] == "all"


# ── degradation ─────────────────────────────────────────────────────────────


def test_unreachable_store_is_a_200_with_available_false(monkeypatch):
    """``_ls_call`` returns None when the daemon proxy AND the direct open
    both miss. The card must render an honest empty state, not a 500."""
    monkeypatch.setattr("routes.sessions._ls_call", lambda *a, **k: None)
    with _app().test_client() as c:
        r = c.get("/api/outcomes/trend")
        assert r.status_code == 200
        body = r.get_json()
    assert body["store_available"] is False
    assert body["direction"] == "unknown"
    assert body["current"]["total"] == 0
