"""Time-window filter tests for the ``first_matching`` / ``last_matching``
scalar helpers in :mod:`clawmetry._paywall_events` and their HTTP
endpoints ``/api/paywall/events/{first,last}``.

Pairs with:

* ``test_paywall_events_first_last_matching.py`` -- store-level
  categorical filter contract, empty-ring / short-circuit invariants.
* ``test_paywall_events_first_last_api.py`` -- HTTP shape + never-5xx
  posture for the two scalar endpoints.
* ``test_paywall_events_time_window.py`` -- same time-window contract
  applied to ``recent`` / ``summary`` / ``count_matching``. The tests
  here extend that contract to the two scalar endpoints so a dashboard
  tile can rebind the same ``[since, until)`` window pair from
  ``/api/paywall/events/recent`` to ``/api/paywall/events/last``
  without translation.

Invariants pinned:

* ``since`` is inclusive, ``until`` is exclusive -- ``[since, until)``.
* Either bound may be ``None`` / blank -- meaning "unbounded on that side".
* Bad bounds (non-numeric, NaN, negative epoch, ``bool``) collapse to
  "not supplied" via :func:`_coerce_ts_bound`, so a stray query string
  cannot silently drop every row.
* The window ``AND``-combines with the categorical filters
  (``event`` / ``feature`` / ``harness`` / ``source`` / ``plan_chosen``).
* ``matched`` reflects the post-filter, post-window subset size and
  stays byte-equal to ``count_matching(**filters, **window)``.
* The response envelope ALWAYS carries ``time_window`` -- with or
  without bounds supplied, and on the neutral fallback envelope too --
  so a caller can trust the top-level key set.
* Endpoints never 5xx.
"""
from __future__ import annotations

import json

import pytest
from flask import Flask


# ── fixtures ────────────────────────────────────────────────────────────────


@pytest.fixture(autouse=True)
def _fresh_store():
    from clawmetry import _paywall_events as pe

    pe.reset()
    yield
    pe.reset()


@pytest.fixture
def clock(monkeypatch):
    """Deterministic clock for the store's ``time.time()`` calls.

    Yields a mutable ``{"now": <float>}`` box; the test bumps
    ``clock["now"]`` between ``record_event`` calls so recorded ``ts``
    values are predictable, and the window tests can pin exact
    inclusive / exclusive boundaries.
    """
    from clawmetry import _paywall_events as pe

    box = {"now": 1_000_000.0}
    monkeypatch.setattr(pe.time, "time", lambda: box["now"])
    return box


@pytest.fixture
def client():
    from routes.entitlement import bp_entitlement
    from clawmetry import _paywall_events as pe

    pe.reset()
    app = Flask(__name__)
    app.register_blueprint(bp_entitlement)
    app.config["TESTING"] = True
    try:
        yield app.test_client()
    finally:
        pe.reset()


def _record(pe, clock, ts, payload):
    clock["now"] = float(ts)
    pe.record_event(payload)


def _post_event(client, **fields):
    resp = client.post(
        "/api/paywall/event",
        data=json.dumps(fields),
        content_type="application/json",
    )
    assert resp.status_code == 204


# ── store-level: last_matching ──────────────────────────────────────────────


def test_last_matching_since_inclusive_boundary(clock):
    from clawmetry import _paywall_events as pe

    _record(pe, clock, 100.0, {"event": "e0"})
    _record(pe, clock, 200.0, {"event": "e1"})
    _record(pe, clock, 300.0, {"event": "e2"})

    # since=200 is inclusive -> e1 and e2 remain, newest is e2
    row = pe.last_matching(since=200.0)
    assert row is not None
    assert row["event"] == "e2"

    # since=201 excludes e1 -> newest becomes e2
    row = pe.last_matching(since=201.0)
    assert row is not None
    assert row["event"] == "e2"

    # since=301 excludes everything -> None
    assert pe.last_matching(since=301.0) is None


def test_last_matching_until_exclusive_boundary(clock):
    from clawmetry import _paywall_events as pe

    _record(pe, clock, 100.0, {"event": "e0"})
    _record(pe, clock, 200.0, {"event": "e1"})
    _record(pe, clock, 300.0, {"event": "e2"})

    # until=300 excludes e2 -> newest becomes e1
    row = pe.last_matching(until=300.0)
    assert row is not None
    assert row["event"] == "e1"

    # until=300.001 includes e2 -> newest is e2
    row = pe.last_matching(until=300.001)
    assert row is not None
    assert row["event"] == "e2"

    # until=100 excludes everything (e0 lands ON boundary, exclusive)
    assert pe.last_matching(until=100.0) is None


def test_last_matching_since_and_until_and_combine(clock):
    from clawmetry import _paywall_events as pe

    for ts in (100.0, 200.0, 300.0, 400.0):
        _record(pe, clock, ts, {"event": f"e{int(ts)}"})

    # [200, 400) -> e200, e300; newest is e300
    row = pe.last_matching(since=200.0, until=400.0)
    assert row is not None
    assert row["event"] == "e300"


def test_last_matching_window_and_categorical_filters_and_combine(clock):
    from clawmetry import _paywall_events as pe

    _record(pe, clock, 100.0, {"event": "paywall_view", "feature": "fleet"})
    _record(pe, clock, 200.0, {"event": "paywall_cta_click", "feature": "fleet"})
    _record(pe, clock, 300.0, {"event": "paywall_view", "feature": "self_evolve"})
    _record(pe, clock, 400.0, {"event": "paywall_view", "feature": "fleet"})

    # event=paywall_view + [150, 350) -> only ts=300 (self_evolve)
    row = pe.last_matching(event="paywall_view", since=150.0, until=350.0)
    assert row is not None
    assert row["feature"] == "self_evolve"

    # event=paywall_view + feature=fleet + [150, 500) -> ts=400
    row = pe.last_matching(
        event="paywall_view", feature="fleet", since=150.0, until=500.0,
    )
    assert row is not None
    assert row["ts"] == 400.0


def test_last_matching_bad_bounds_collapse_to_unbounded(clock):
    from clawmetry import _paywall_events as pe

    _record(pe, clock, 100.0, {"event": "e0"})
    _record(pe, clock, 200.0, {"event": "e1"})

    # Every "bad" bound collapses; last_matching returns the newest row.
    for since_bad in (None, "", "   ", "junk", -1, -0.5, "nan", True, False):
        for until_bad in (None, "", "   ", "junk", "nan", True, False):
            row = pe.last_matching(since=since_bad, until=until_bad)
            assert row is not None
            assert row["event"] == "e1", (since_bad, until_bad)


def test_last_matching_empty_window_returns_none(clock):
    from clawmetry import _paywall_events as pe

    _record(pe, clock, 100.0, {"event": "e0"})
    # since >= until -> empty window by construction.
    assert pe.last_matching(since=200.0, until=200.0) is None
    assert pe.last_matching(since=500.0, until=100.0) is None


def test_last_matching_numeric_string_bounds_accepted(clock):
    from clawmetry import _paywall_events as pe

    _record(pe, clock, 100.0, {"event": "e0"})
    _record(pe, clock, 200.0, {"event": "e1"})

    row = pe.last_matching(since="150", until="500")
    assert row is not None
    assert row["event"] == "e1"


# ── store-level: first_matching ─────────────────────────────────────────────


def test_first_matching_since_inclusive_boundary(clock):
    from clawmetry import _paywall_events as pe

    _record(pe, clock, 100.0, {"event": "e0"})
    _record(pe, clock, 200.0, {"event": "e1"})
    _record(pe, clock, 300.0, {"event": "e2"})

    # since=200 -> e1, e2; oldest is e1
    row = pe.first_matching(since=200.0)
    assert row is not None
    assert row["event"] == "e1"

    # since=201 -> e2 only; oldest is e2
    row = pe.first_matching(since=201.0)
    assert row is not None
    assert row["event"] == "e2"


def test_first_matching_until_exclusive_boundary(clock):
    from clawmetry import _paywall_events as pe

    _record(pe, clock, 100.0, {"event": "e0"})
    _record(pe, clock, 200.0, {"event": "e1"})
    _record(pe, clock, 300.0, {"event": "e2"})

    # until=200 excludes e1 -> oldest is e0
    row = pe.first_matching(until=200.0)
    assert row is not None
    assert row["event"] == "e0"

    # until=100.5 includes e0 -> oldest is e0
    row = pe.first_matching(until=100.5)
    assert row is not None
    assert row["event"] == "e0"

    # until=100 excludes e0 (boundary is exclusive) -> None
    assert pe.first_matching(until=100.0) is None


def test_first_matching_window_and_categorical_filters_and_combine(clock):
    from clawmetry import _paywall_events as pe

    _record(pe, clock, 100.0, {"event": "paywall_view", "feature": "fleet"})
    _record(pe, clock, 200.0, {"event": "paywall_cta_click", "feature": "fleet"})
    _record(pe, clock, 300.0, {"event": "paywall_view", "feature": "self_evolve"})
    _record(pe, clock, 400.0, {"event": "paywall_view", "feature": "fleet"})

    # event=paywall_view + [150, 500) -> ts=300, 400; oldest is 300 (self_evolve)
    row = pe.first_matching(event="paywall_view", since=150.0, until=500.0)
    assert row is not None
    assert row["ts"] == 300.0
    assert row["feature"] == "self_evolve"

    # event=paywall_view + feature=fleet + [150, 500) -> ts=400 only
    row = pe.first_matching(
        event="paywall_view", feature="fleet", since=150.0, until=500.0,
    )
    assert row is not None
    assert row["ts"] == 400.0


def test_first_matching_bad_bounds_collapse_to_unbounded(clock):
    from clawmetry import _paywall_events as pe

    _record(pe, clock, 100.0, {"event": "e0"})
    _record(pe, clock, 200.0, {"event": "e1"})

    for since_bad in (None, "", "   ", "junk", -1, "nan", True, False):
        for until_bad in (None, "", "   ", "junk", "nan", True, False):
            row = pe.first_matching(since=since_bad, until=until_bad)
            assert row is not None
            assert row["event"] == "e0", (since_bad, until_bad)


def test_first_matching_empty_window_returns_none(clock):
    from clawmetry import _paywall_events as pe

    _record(pe, clock, 100.0, {"event": "e0"})
    assert pe.first_matching(since=200.0, until=200.0) is None
    assert pe.first_matching(since=500.0, until=100.0) is None


# ── store-level: agreement with recent / count_matching ─────────────────────


def test_last_matching_with_window_agrees_with_recent_limit_one(clock):
    from clawmetry import _paywall_events as pe

    for ts in (100.0, 200.0, 300.0, 400.0):
        _record(pe, clock, ts, {"event": f"e{int(ts)}", "feature": "fleet"})

    # Both should look at the same [200, 400) window and pick the newest.
    row = pe.last_matching(since=200.0, until=400.0)
    recent = pe.recent(1, since=200.0, until=400.0)
    assert recent and row == recent[0]


def test_first_matching_with_window_agrees_with_recent_tail(clock):
    from clawmetry import _paywall_events as pe

    for ts in (100.0, 200.0, 300.0, 400.0):
        _record(pe, clock, ts, {"event": f"e{int(ts)}", "feature": "fleet"})

    # recent is newest-first; the tail is the oldest.
    recent = pe.recent(200, since=200.0, until=400.0)
    row = pe.first_matching(since=200.0, until=400.0)
    assert recent
    assert row == recent[-1]


def test_scalar_matched_equals_count_matching_with_window(clock):
    """A dashboard tile computing ``matched`` off ``count_matching`` must
    stay in lock-step with what ``first_matching`` / ``last_matching``
    walk over."""
    from clawmetry import _paywall_events as pe

    _record(pe, clock, 100.0, {"event": "paywall_view", "feature": "fleet"})
    _record(pe, clock, 200.0, {"event": "paywall_cta_click", "feature": "fleet"})
    _record(pe, clock, 300.0, {"event": "paywall_view", "feature": "self_evolve"})
    _record(pe, clock, 400.0, {"event": "paywall_view", "feature": "fleet"})

    kwargs = dict(event="paywall_view", since=150.0, until=500.0)
    count = pe.count_matching(**kwargs)
    row = pe.last_matching(**kwargs)
    assert count == 2
    assert row is not None
    # If count > 0, both scalar helpers must find a row.
    assert pe.first_matching(**kwargs) is not None


# ── HTTP contract: /api/paywall/events/last ─────────────────────────────────


def test_last_endpoint_always_carries_time_window(client):
    """Even with no bounds and an empty ring, ``time_window`` is present."""
    body = client.get("/api/paywall/events/last").get_json()
    assert body["time_window"] == {"since": None, "until": None}


def test_last_endpoint_echoes_resolved_bounds(client):
    _post_event(client, event="paywall_view", feature="fleet")
    body = client.get(
        "/api/paywall/events/last?since=100&until=99999999999",
    ).get_json()
    assert body["time_window"] == {"since": 100.0, "until": 99999999999.0}


def test_last_endpoint_bad_bounds_collapse_and_reflect(client):
    _post_event(client, event="paywall_view", feature="fleet")
    body = client.get(
        "/api/paywall/events/last?since=junk&until=nan",
    ).get_json()
    # Bad bounds collapse; both echo as null.
    assert body["time_window"] == {"since": None, "until": None}
    # Event is still returned (window collapsed to unbounded).
    assert body["event"] is not None
    assert body["matched"] == 1


def test_last_endpoint_window_narrows_matched(client, clock):
    """Bounds must actually filter -- exercising both the store and the
    HTTP glue in one shot."""
    from clawmetry import _paywall_events as pe

    _record(pe, clock, 100.0, {"event": "paywall_view", "feature": "fleet"})
    _record(pe, clock, 200.0, {"event": "paywall_view", "feature": "fleet"})
    _record(pe, clock, 300.0, {"event": "paywall_view", "feature": "fleet"})

    body = client.get(
        "/api/paywall/events/last?since=150&until=250",
    ).get_json()
    assert body["matched"] == 1
    assert body["event"] is not None
    assert body["event"]["ts"] == 200.0
    # in_window is process-lifetime ring size, NOT window-filtered.
    assert body["in_window"] == 3


def test_last_endpoint_window_and_categorical_filter_and_combine(client, clock):
    from clawmetry import _paywall_events as pe

    _record(pe, clock, 100.0, {"event": "paywall_view", "feature": "fleet"})
    _record(pe, clock, 200.0, {"event": "paywall_cta_click", "feature": "fleet"})
    _record(pe, clock, 300.0, {"event": "paywall_view", "feature": "self_evolve"})
    _record(pe, clock, 400.0, {"event": "paywall_view", "feature": "fleet"})

    body = client.get(
        "/api/paywall/events/last"
        "?event=paywall_view&feature=fleet&since=150&until=500",
    ).get_json()
    assert body["event"] is not None
    assert body["event"]["ts"] == 400.0
    assert body["matched"] == 1
    assert body["filters"] == {"event": "paywall_view", "feature": "fleet"}
    assert body["time_window"] == {"since": 150.0, "until": 500.0}


def test_last_endpoint_empty_window_returns_null(client, clock):
    from clawmetry import _paywall_events as pe

    _record(pe, clock, 100.0, {"event": "paywall_view", "feature": "fleet"})

    body = client.get(
        "/api/paywall/events/last?since=200&until=200",
    ).get_json()
    assert body["event"] is None
    assert body["matched"] == 0
    assert body["in_window"] == 1
    assert body["time_window"] == {"since": 200.0, "until": 200.0}


def test_last_endpoint_blank_bounds_are_not_supplied(client):
    _post_event(client, event="paywall_view", feature="fleet")
    body = client.get(
        "/api/paywall/events/last?since=&until=",
    ).get_json()
    assert body["event"] is not None
    assert body["time_window"] == {"since": None, "until": None}


def test_last_endpoint_never_5xxs_with_window(client, monkeypatch):
    from clawmetry import _paywall_events as pe

    def _boom(**kwargs):
        raise RuntimeError("simulated store outage")

    monkeypatch.setattr(pe, "last_matching", _boom)
    resp = client.get("/api/paywall/events/last?since=100&until=200")
    assert resp.status_code == 200
    body = resp.get_json()
    # Neutral fallback envelope still carries time_window.
    assert body == {
        "event": None,
        "matched": 0,
        "in_window": 0,
        "filters": {},
        "time_window": {"since": None, "until": None},
    }


# ── HTTP contract: /api/paywall/events/first ────────────────────────────────


def test_first_endpoint_always_carries_time_window(client):
    body = client.get("/api/paywall/events/first").get_json()
    assert body["time_window"] == {"since": None, "until": None}


def test_first_endpoint_echoes_resolved_bounds(client):
    _post_event(client, event="paywall_view", feature="fleet")
    body = client.get(
        "/api/paywall/events/first?since=100&until=99999999999",
    ).get_json()
    assert body["time_window"] == {"since": 100.0, "until": 99999999999.0}


def test_first_endpoint_window_narrows_matched(client, clock):
    from clawmetry import _paywall_events as pe

    _record(pe, clock, 100.0, {"event": "paywall_view", "feature": "fleet"})
    _record(pe, clock, 200.0, {"event": "paywall_view", "feature": "fleet"})
    _record(pe, clock, 300.0, {"event": "paywall_view", "feature": "fleet"})

    body = client.get(
        "/api/paywall/events/first?since=150&until=350",
    ).get_json()
    # [150, 350) -> ts=200 and ts=300 remain; oldest is 200.
    assert body["event"] is not None
    assert body["event"]["ts"] == 200.0
    assert body["matched"] == 2
    assert body["in_window"] == 3


def test_first_endpoint_window_and_categorical_filter_and_combine(client, clock):
    from clawmetry import _paywall_events as pe

    _record(pe, clock, 100.0, {"event": "paywall_view", "feature": "fleet"})
    _record(pe, clock, 200.0, {"event": "paywall_cta_click", "feature": "fleet"})
    _record(pe, clock, 300.0, {"event": "paywall_view", "feature": "self_evolve"})
    _record(pe, clock, 400.0, {"event": "paywall_view", "feature": "fleet"})

    body = client.get(
        "/api/paywall/events/first"
        "?event=paywall_view&since=150&until=500",
    ).get_json()
    # event=paywall_view in [150, 500) -> ts=300 (self_evolve), 400 (fleet).
    # first = ts=300.
    assert body["event"] is not None
    assert body["event"]["ts"] == 300.0
    assert body["event"]["feature"] == "self_evolve"
    assert body["matched"] == 2
    assert body["filters"] == {"event": "paywall_view"}
    assert body["time_window"] == {"since": 150.0, "until": 500.0}


def test_first_endpoint_empty_window_returns_null(client, clock):
    from clawmetry import _paywall_events as pe

    _record(pe, clock, 100.0, {"event": "paywall_view", "feature": "fleet"})

    body = client.get(
        "/api/paywall/events/first?since=200&until=200",
    ).get_json()
    assert body["event"] is None
    assert body["matched"] == 0
    assert body["in_window"] == 1
    assert body["time_window"] == {"since": 200.0, "until": 200.0}


def test_first_endpoint_never_5xxs_with_window(client, monkeypatch):
    from clawmetry import _paywall_events as pe

    def _boom(**kwargs):
        raise RuntimeError("simulated store outage")

    monkeypatch.setattr(pe, "first_matching", _boom)
    resp = client.get("/api/paywall/events/first?since=100&until=200")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body == {
        "event": None,
        "matched": 0,
        "in_window": 0,
        "filters": {},
        "time_window": {"since": None, "until": None},
    }


# ── cross-endpoint agreement ────────────────────────────────────────────────


def test_last_endpoint_agrees_with_recent_limit_one_with_window(client, clock):
    """``/api/paywall/events/last`` is the scalar unwrap of
    ``/api/paywall/events/recent?limit=1`` -- for any given window pair
    the two must return the same top row."""
    from clawmetry import _paywall_events as pe

    for ts in (100.0, 200.0, 300.0, 400.0):
        _record(pe, clock, ts, {"event": f"e{int(ts)}", "feature": "fleet"})

    q = "since=150&until=350"
    last = client.get(f"/api/paywall/events/last?{q}").get_json()
    recent = client.get(f"/api/paywall/events/recent?limit=1&{q}").get_json()
    assert recent["events"], "expected at least one match in the window"
    assert last["event"] == recent["events"][0]
    # time_window echo must match byte-for-byte between the two endpoints.
    assert last["time_window"] == recent["time_window"]


def test_first_endpoint_agrees_with_recent_tail_with_window(client, clock):
    from clawmetry import _paywall_events as pe

    for ts in (100.0, 200.0, 300.0, 400.0):
        _record(pe, clock, ts, {"event": f"e{int(ts)}", "feature": "fleet"})

    q = "since=150&until=350"
    first = client.get(f"/api/paywall/events/first?{q}").get_json()
    recent = client.get(f"/api/paywall/events/recent?limit=200&{q}").get_json()
    assert recent["events"]
    assert first["event"] == recent["events"][-1]
    assert first["time_window"] == recent["time_window"]
