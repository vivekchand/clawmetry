"""Time-window filter tests for :mod:`clawmetry._paywall_events` and
the ``/api/paywall/events/summary`` + ``/api/paywall/events/recent``
HTTP endpoints.

Pairs with ``test_paywall_events_summary_filters.py`` and
``test_paywall_events_recent_filters.py`` -- the store's ``since`` /
``until`` kwargs are the natural third dimension after the categorical
filters, and both endpoints must accept them via the same query-string
names so a dashboard tile can bind one window pair to both surfaces
without translation.

Invariants pinned:

* ``since`` is inclusive, ``until`` is exclusive -- half-open
  ``[since, until)``. Back-to-back windows do NOT double-count events
  landing on the boundary.
* Either bound may be ``None`` / blank -- meaning "unbounded on that side".
* Bad bounds (non-numeric, NaN, negative epoch, ``bool``) collapse to
  "not supplied" so a stray query string cannot silently drop every row.
* The window AND-combines with the categorical filters
  (``event`` / ``feature`` / ``harness`` / ``source`` / ``plan_chosen``).
* Process-lifetime counters (``total``, ``dropped``, ``first_ts``,
  ``last_ts``, ``capacity``) and unfiltered ``in_window`` are NEVER
  sliced by the window -- they describe the ring itself.
* ``matched`` reflects the post-filter, post-window subset size and stays
  in lock-step across summary / recent for the same query.
* Both endpoints always emit ``time_window: {"since": ..., "until": ...}``
  so a caller can rely on the top-level key set being stable.
* Endpoints never 5xx -- the neutral fallback envelope must also carry
  ``time_window``.
"""
from __future__ import annotations

import math

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


def _record(pe, clock, ts, payload):
    clock["now"] = float(ts)
    pe.record_event(payload)


# ── _coerce_ts_bound / _normalise_time_bounds ────────────────────────────────


def test_coerce_ts_bound_accepts_float_int_and_numeric_string():
    from clawmetry._paywall_events import _coerce_ts_bound

    assert _coerce_ts_bound(1000.5) == 1000.5
    assert _coerce_ts_bound(1000) == 1000.0
    assert _coerce_ts_bound("1234.5") == 1234.5
    assert _coerce_ts_bound("  1234.5  ") == 1234.5   # stripped


def test_coerce_ts_bound_rejects_bogus_values():
    from clawmetry._paywall_events import _coerce_ts_bound

    assert _coerce_ts_bound(None) is None
    assert _coerce_ts_bound("") is None
    assert _coerce_ts_bound("   ") is None
    assert _coerce_ts_bound("notanumber") is None
    assert _coerce_ts_bound(float("nan")) is None
    assert _coerce_ts_bound("nan") is None
    assert _coerce_ts_bound(-1) is None
    assert _coerce_ts_bound(-0.001) is None
    assert _coerce_ts_bound("-5") is None
    # ``bool`` collapses -- a stray True should not become 1.0.
    assert _coerce_ts_bound(True) is None
    assert _coerce_ts_bound(False) is None


def test_normalise_time_bounds_returns_pair():
    from clawmetry._paywall_events import _normalise_time_bounds

    assert _normalise_time_bounds(None, None) == (None, None)
    assert _normalise_time_bounds("10", "20") == (10.0, 20.0)
    assert _normalise_time_bounds("junk", 42) == (None, 42.0)
    # Empty window (since >= until) is passed through unchanged; the store
    # simply filters every row out.
    assert _normalise_time_bounds(100, 100) == (100.0, 100.0)


# ── _row_matches_time_window ────────────────────────────────────────────────


def test_row_matches_time_window_half_open_interval():
    from clawmetry._paywall_events import _row_matches_time_window

    row = {"ts": 100.0}
    # No bounds -> match.
    assert _row_matches_time_window(row, None, None)
    # since inclusive.
    assert _row_matches_time_window(row, 100.0, None)
    assert not _row_matches_time_window(row, 100.0001, None)
    # until exclusive.
    assert not _row_matches_time_window(row, None, 100.0)
    assert _row_matches_time_window(row, None, 100.0001)
    # Both bounds.
    assert _row_matches_time_window(row, 99.0, 101.0)
    assert not _row_matches_time_window(row, 101.0, 200.0)


def test_row_without_numeric_ts_only_matches_unbounded_window():
    from clawmetry._paywall_events import _row_matches_time_window

    assert _row_matches_time_window({}, None, None)
    assert not _row_matches_time_window({}, 100.0, None)
    assert not _row_matches_time_window({"ts": "notanumber"}, 100.0, None)
    assert not _row_matches_time_window({"ts": True}, 100.0, None)


# ── store-level summary ──────────────────────────────────────────────────────


def test_summary_unfiltered_call_emits_time_window_field():
    from clawmetry import _paywall_events as pe

    pe.record_event({"event": "paywall_view", "feature": "fleet"})
    s = pe.summary()
    assert s["time_window"] == {"since": None, "until": None}
    # Unfiltered: matched == in_window, matching the categorical contract.
    assert s["matched"] == s["in_window"] == 1


def test_summary_since_is_inclusive(clock):
    from clawmetry import _paywall_events as pe

    _record(pe, clock, 100.0, {"event": "paywall_view", "feature": "a"})
    _record(pe, clock, 101.0, {"event": "paywall_view", "feature": "b"})

    s = pe.summary(since=100.0)
    assert s["time_window"] == {"since": 100.0, "until": None}
    assert s["matched"] == 2

    s = pe.summary(since=100.5)
    assert s["matched"] == 1
    assert s["by_feature"] == {"b": 1}


def test_summary_until_is_exclusive(clock):
    from clawmetry import _paywall_events as pe

    _record(pe, clock, 100.0, {"event": "paywall_view", "feature": "a"})
    _record(pe, clock, 101.0, {"event": "paywall_view", "feature": "b"})

    # until=101.0 excludes the ts=101.0 row (half-open).
    s = pe.summary(until=101.0)
    assert s["time_window"] == {"since": None, "until": 101.0}
    assert s["matched"] == 1
    assert s["by_feature"] == {"a": 1}


def test_summary_back_to_back_windows_do_not_double_count(clock):
    """Half-open ``[since, until)`` guarantees adjacent windows partition
    the ring cleanly. A dashboard rendering minute-bucket tiles depends
    on this."""
    from clawmetry import _paywall_events as pe

    for ts in (100.0, 100.5, 101.0, 101.5, 102.0):
        _record(pe, clock, ts, {"event": "paywall_view", "feature": "f"})

    left = pe.summary(since=100.0, until=101.0)["matched"]
    right = pe.summary(since=101.0, until=102.0)["matched"]
    tail = pe.summary(since=102.0)["matched"]
    assert left + right + tail == pe.summary()["in_window"] == 5
    # Explicit boundary check: ts=101.0 must land in `right`, not `left`.
    assert left == 2 and right == 2 and tail == 1


def test_summary_ring_stats_not_sliced_by_window(clock):
    from clawmetry import _paywall_events as pe

    for ts in (100.0, 200.0, 300.0):
        _record(pe, clock, ts, {"event": "paywall_view", "feature": "f"})

    s = pe.summary(since=250.0)
    assert s["matched"] == 1              # only ts=300 lands in the window
    assert s["in_window"] == 3            # ring size unaffected
    assert s["total"] == 3                # lifetime counter unaffected
    assert s["first_ts"] == 100.0         # never sliced
    assert s["last_ts"] == 300.0


def test_summary_window_and_categorical_filter_combine(clock):
    from clawmetry import _paywall_events as pe

    _record(pe, clock, 100.0, {"event": "paywall_view",      "feature": "fleet"})
    _record(pe, clock, 200.0, {"event": "paywall_cta_click", "feature": "fleet"})
    _record(pe, clock, 300.0, {"event": "paywall_cta_click", "feature": "anomaly"})

    s = pe.summary(event="paywall_cta_click", since=150.0, until=250.0)
    assert s["matched"] == 1
    assert s["by_feature"] == {"fleet": 1}
    assert s["filters"] == {"event": "paywall_cta_click"}
    assert s["time_window"] == {"since": 150.0, "until": 250.0}


def test_summary_bogus_bound_collapses_to_not_supplied(clock):
    from clawmetry import _paywall_events as pe

    _record(pe, clock, 100.0, {"event": "paywall_view", "feature": "f"})
    for bad in ("junk", float("nan"), -1, True):
        s = pe.summary(since=bad)
        assert s["matched"] == 1, f"since={bad!r} silently sliced the ring"
        assert s["time_window"]["since"] is None
    for bad in ("junk", -0.5, False):
        s = pe.summary(until=bad)
        assert s["matched"] == 1, f"until={bad!r} silently sliced the ring"
        assert s["time_window"]["until"] is None


def test_summary_empty_window_matches_nothing(clock):
    """``since >= until`` is an empty half-open interval by construction --
    a caller supplying identical bounds asks for zero rows and gets them,
    but the ring stats survive."""
    from clawmetry import _paywall_events as pe

    _record(pe, clock, 100.0, {"event": "paywall_view", "feature": "f"})
    s = pe.summary(since=200.0, until=200.0)
    assert s["matched"] == 0
    assert s["by_feature"] == {}
    assert s["in_window"] == 1
    assert s["time_window"] == {"since": 200.0, "until": 200.0}


# ── store-level recent + count_matching ─────────────────────────────────────


def test_recent_respects_time_window(clock):
    from clawmetry import _paywall_events as pe

    _record(pe, clock, 100.0, {"event": "paywall_view", "feature": "old"})
    _record(pe, clock, 200.0, {"event": "paywall_view", "feature": "new"})

    rows = pe.recent(50, since=150.0)
    assert len(rows) == 1
    assert rows[0]["feature"] == "new"


def test_recent_window_and_filter_and_limit_compose(clock):
    from clawmetry import _paywall_events as pe

    for ts, feature in ((100.0, "fleet"), (110.0, "fleet"), (120.0, "fleet"),
                        (200.0, "anomaly")):
        _record(pe, clock, ts, {"event": "paywall_cta_click", "feature": feature})

    rows = pe.recent(2, feature="fleet", since=100.0, until=200.0)
    # Newest-first within the window; limit clamps AFTER filtering.
    assert len(rows) == 2
    assert [r["ts"] for r in rows] == [120.0, 110.0]


def test_count_matching_agrees_with_recent_within_ceiling(clock):
    from clawmetry import _paywall_events as pe

    for ts in (100.0, 110.0, 120.0, 200.0):
        _record(pe, clock, ts, {"event": "paywall_view", "feature": "f"})

    matched = pe.count_matching(since=100.0, until=150.0)
    rows = pe.recent(pe.RECENT_MAX_LIMIT, since=100.0, until=150.0)
    assert matched == len(rows) == 3


def test_count_matching_unbounded_returns_full_ring(clock):
    from clawmetry import _paywall_events as pe

    for ts in (100.0, 110.0):
        _record(pe, clock, ts, {"event": "paywall_view", "feature": "f"})
    assert pe.count_matching() == 2


# ── HTTP endpoints ───────────────────────────────────────────────────────────


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


def _post(client, payload):
    return client.post("/api/paywall/event", json=payload)


def test_http_summary_unfiltered_carries_time_window(client):
    _post(client, {"event": "paywall_view", "feature": "fleet"})
    body = client.get("/api/paywall/events/summary").get_json()
    assert body["time_window"] == {"since": None, "until": None}


def test_http_summary_since_until_query_params(client, clock):
    from clawmetry import _paywall_events as pe

    # `_post` triggers `record_event` which reads `time.time()`; the
    # `clock` fixture makes those reads deterministic.
    clock["now"] = 100.0
    _post(client, {"event": "paywall_view", "feature": "old"})
    clock["now"] = 200.0
    _post(client, {"event": "paywall_view", "feature": "new"})

    body = client.get(
        "/api/paywall/events/summary?since=150&until=300"
    ).get_json()
    assert body["time_window"] == {"since": 150.0, "until": 300.0}
    assert body["matched"] == 1
    assert body["by_feature"] == {"new": 1}
    # Ring stats survive.
    assert body["in_window"] == 2
    assert body["total"] == 2

    # `_pe` unused-import guard so an accidental removal of the fixture
    # dependency doesn't break the test silently.
    assert pe.RECENT_MAX_LIMIT >= 1


def test_http_summary_blank_time_bounds_treated_as_not_supplied(client):
    _post(client, {"event": "paywall_view", "feature": "f"})
    body = client.get("/api/paywall/events/summary?since=&until=").get_json()
    assert body["time_window"] == {"since": None, "until": None}
    assert body["matched"] == 1


def test_http_summary_bad_time_bounds_collapse(client):
    _post(client, {"event": "paywall_view", "feature": "f"})
    body = client.get(
        "/api/paywall/events/summary?since=notanumber&until=NaN"
    ).get_json()
    assert body["time_window"] == {"since": None, "until": None}
    assert body["matched"] == 1


def test_http_recent_since_until_query_params(client, clock):
    clock["now"] = 100.0
    _post(client, {"event": "paywall_view", "feature": "old"})
    clock["now"] = 200.0
    _post(client, {"event": "paywall_view", "feature": "new"})

    body = client.get(
        "/api/paywall/events/recent?since=150&until=300"
    ).get_json()
    assert body["time_window"] == {"since": 150.0, "until": 300.0}
    assert body["matched"] == 1
    assert body["count"] == 1
    assert body["events"][0]["feature"] == "new"


def test_http_recent_unfiltered_carries_time_window(client):
    _post(client, {"event": "paywall_view", "feature": "f"})
    body = client.get("/api/paywall/events/recent").get_json()
    assert body["time_window"] == {"since": None, "until": None}


def test_http_summary_matched_equals_recent_matched_across_window(client, clock):
    """Dashboard tile bound to both endpoints with the same query must see
    the same ``matched`` count regardless of the categorical filters +
    window combined."""
    for ts, event, feature in (
        (100.0, "paywall_view",      "fleet"),
        (110.0, "paywall_view",      "fleet"),
        (120.0, "paywall_cta_click", "fleet"),
        (200.0, "paywall_view",      "anomaly"),
    ):
        clock["now"] = ts
        _post(client, {"event": event, "feature": feature})

    q = "event=paywall_view&feature=fleet&since=100&until=150"
    s = client.get(f"/api/paywall/events/summary?{q}").get_json()
    r = client.get(f"/api/paywall/events/recent?limit=200&{q}").get_json()
    assert s["matched"] == r["matched"] == 2
    assert s["time_window"] == r["time_window"] == {
        "since": 100.0, "until": 150.0,
    }


def test_http_summary_fallback_shape_includes_time_window(client, monkeypatch):
    """Even the error-path neutral shape must carry ``time_window`` so a
    caller can trust the top-level key set is stable."""
    from clawmetry import _paywall_events as pe

    def _boom(**kwargs):
        raise RuntimeError("simulated store failure")

    monkeypatch.setattr(pe, "summary", _boom)
    body = client.get(
        "/api/paywall/events/summary?since=100&until=200"
    ).get_json()
    assert "time_window" in body
    assert body["time_window"] == {"since": None, "until": None}
    assert body["matched"] == 0


def test_http_recent_fallback_shape_includes_time_window(client, monkeypatch):
    from clawmetry import _paywall_events as pe

    def _boom(*args, **kwargs):
        raise RuntimeError("simulated store failure")

    monkeypatch.setattr(pe, "recent", _boom)
    body = client.get("/api/paywall/events/recent?since=100").get_json()
    assert "time_window" in body
    assert body["time_window"] == {"since": None, "until": None}
    assert body["events"] == []


def test_http_recent_time_window_echoed_even_when_filters_mismatch(client, clock):
    """A window that matches nothing must still echo the resolved bounds
    so the UI can render the window it asked for."""
    clock["now"] = 100.0
    _post(client, {"event": "paywall_view", "feature": "f"})
    body = client.get(
        "/api/paywall/events/recent?since=500&until=600"
    ).get_json()
    assert body["matched"] == 0
    assert body["events"] == []
    assert body["time_window"] == {"since": 500.0, "until": 600.0}


def test_math_is_used():
    """Sanity: ``math`` is imported at module top for the NaN test."""
    assert math.isnan(float("nan"))
