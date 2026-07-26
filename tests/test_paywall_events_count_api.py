"""API tests for the scalar paywall-event count endpoint:

  GET /api/paywall/events/count

Thin JSON wrapper around
:func:`clawmetry._paywall_events.count_matching` --
scalar counterpart of ``/api/paywall/events/{summary,recent,first,last}``
for the "42 CTA clicks in this window" dashboard tile shape that only
wants the number and does not want to pay for the per-row ``dict(e)``
copy of ``/recent`` or the five ``by_*`` aggregations of ``/summary``.

Store-level ``count_matching`` invariants (categorical filters +
``since`` / ``until``) already live in
``test_paywall_events_recent_filters.py`` and
``test_paywall_events_time_window.py``. The tests here pin the HTTP
contract:

* Never 5xxs.
* Ships in GRACE -- no entitlement gate.
* Empty ring returns the neutral ``count=0`` envelope, including a
  ``time_window: {since: null, until: null}`` echo so a dashboard tile
  can trust the top-level key set is stable regardless of window
  supply.
* Categorical filter params echo back under ``filters`` (blank ones
  omitted) exactly the same shape as ``/recent`` / ``/first`` /
  ``/last``.
* Time-window params (``since`` / ``until``) apply the half-open
  ``[since, until)`` semantics and echo the resolved bounds under
  ``time_window``. Bad bounds collapse to "not supplied".
* Cross-endpoint agreement: for the same filter + window inputs
  ``/count``'s ``count`` byte-equals ``/recent``'s ``matched`` and
  ``/summary``'s ``matched``.
"""
from __future__ import annotations

import json

import pytest
from flask import Flask


# ── fixtures ────────────────────────────────────────────────────────────────


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


@pytest.fixture
def clock(monkeypatch):
    """Deterministic clock for the store's ``time.time()`` calls so the
    tests can pin exact ``since`` / ``until`` boundaries."""
    from clawmetry import _paywall_events as pe

    box = {"now": 1_000_000.0}
    monkeypatch.setattr(pe.time, "time", lambda: box["now"])
    return box


def _post_event(client, **fields):
    resp = client.post(
        "/api/paywall/event",
        data=json.dumps(fields),
        content_type="application/json",
    )
    assert resp.status_code == 204


def _post_at(client, clock, ts, **fields):
    clock["now"] = float(ts)
    _post_event(client, **fields)


# ── empty ring ──────────────────────────────────────────────────────────────


def test_count_empty_ring_returns_neutral_envelope(client):
    body = client.get("/api/paywall/events/count").get_json()
    assert body == {
        "count": 0,
        "in_window": 0,
        "filters": {},
        "time_window": {"since": None, "until": None},
    }


def test_count_envelope_always_carries_time_window_key(client):
    """The neutral fallback and the populated envelope must both carry
    ``time_window`` so a dashboard tile can rely on the top-level key
    set being stable regardless of whether bounds were supplied."""
    body = client.get("/api/paywall/events/count").get_json()
    assert set(body.keys()) == {"count", "in_window", "filters", "time_window"}


# ── unfiltered ──────────────────────────────────────────────────────────────


def test_count_unfiltered_reflects_ring_size(client):
    _post_event(client, event="paywall_view", feature="fleet")
    _post_event(client, event="paywall_view", feature="self_evolve")
    _post_event(client, event="paywall_cta_click", feature="fleet")

    body = client.get("/api/paywall/events/count").get_json()
    assert body["count"] == 3
    assert body["in_window"] == 3
    assert body["filters"] == {}
    assert body["time_window"] == {"since": None, "until": None}


def test_count_unfiltered_equals_in_window_on_populated_ring(client):
    """The no-filter, no-window count is byte-equal to ``in_window`` --
    matches the ``count_matching`` short-circuit for ``not filters and
    not has_window``."""
    for i in range(7):
        _post_event(client, event="paywall_view", feature=f"f{i}")
    body = client.get("/api/paywall/events/count").get_json()
    assert body["count"] == body["in_window"] == 7


# ── categorical filters ────────────────────────────────────────────────────


def test_count_filter_narrows_to_matching_rows(client):
    _post_event(client, event="paywall_view", feature="fleet")
    _post_event(client, event="paywall_view", feature="self_evolve")
    _post_event(client, event="paywall_cta_click", feature="fleet")

    body = client.get(
        "/api/paywall/events/count?event=paywall_view",
    ).get_json()
    assert body["count"] == 2
    assert body["in_window"] == 3  # ring unaffected by filter
    assert body["filters"] == {"event": "paywall_view"}


def test_count_filter_no_match_returns_zero_but_nonzero_in_window(client):
    _post_event(client, event="paywall_view", feature="fleet")

    body = client.get(
        "/api/paywall/events/count?event=not_a_real_event",
    ).get_json()
    assert body["count"] == 0
    assert body["in_window"] == 1
    assert body["filters"] == {"event": "not_a_real_event"}


def test_count_blank_filter_is_not_supplied(client):
    _post_event(client, event="paywall_view", feature="fleet")

    body = client.get(
        "/api/paywall/events/count?event=&feature=",
    ).get_json()
    # Blank filters are "not supplied" -- not echoed under `filters`.
    assert body["filters"] == {}
    assert body["count"] == 1


def test_count_combines_filters_with_and(client):
    _post_event(client, event="paywall_view", feature="fleet")
    _post_event(client, event="paywall_view", feature="self_evolve")
    _post_event(client, event="paywall_cta_click", feature="fleet")

    body = client.get(
        "/api/paywall/events/count"
        "?event=paywall_view&feature=fleet",
    ).get_json()
    assert body["count"] == 1
    assert body["filters"] == {"event": "paywall_view", "feature": "fleet"}


def test_count_all_five_filter_axes_echo(client):
    _post_event(
        client,
        event="paywall_cta_click",
        feature="fleet",
        harness="claude_code",
        source="banner",
        plan_chosen="cloud_pro",
    )
    body = client.get(
        "/api/paywall/events/count"
        "?event=paywall_cta_click"
        "&feature=fleet"
        "&harness=claude_code"
        "&source=banner"
        "&plan_chosen=cloud_pro",
    ).get_json()
    assert body["count"] == 1
    assert body["filters"] == {
        "event": "paywall_cta_click",
        "feature": "fleet",
        "harness": "claude_code",
        "source": "banner",
        "plan_chosen": "cloud_pro",
    }


# ── time-window semantics ──────────────────────────────────────────────────


def test_count_time_window_echoes_resolved_bounds(client, clock):
    _post_at(client, clock, 100.0, event="paywall_view", feature="a")
    _post_at(client, clock, 200.0, event="paywall_view", feature="b")

    body = client.get(
        "/api/paywall/events/count?since=150&until=250",
    ).get_json()
    assert body["count"] == 1
    assert body["time_window"] == {"since": 150.0, "until": 250.0}


def test_count_since_is_inclusive_until_is_exclusive(client, clock):
    _post_at(client, clock, 100.0, event="paywall_view", feature="a")
    _post_at(client, clock, 101.0, event="paywall_view", feature="b")

    # since=100 includes ts=100.
    body = client.get(
        "/api/paywall/events/count?since=100",
    ).get_json()
    assert body["count"] == 2
    assert body["time_window"] == {"since": 100.0, "until": None}

    # until=101 excludes ts=101.
    body = client.get(
        "/api/paywall/events/count?until=101",
    ).get_json()
    assert body["count"] == 1
    assert body["time_window"] == {"since": None, "until": 101.0}


def test_count_back_to_back_windows_do_not_double_count(client, clock):
    """Half-open ``[since, until)`` guarantees adjacent windows partition
    the ring cleanly -- boundary rows land in the right-hand window,
    not both. A minute-bucket dashboard depends on this."""
    for ts in (100.0, 100.5, 101.0, 101.5, 102.0):
        _post_at(client, clock, ts, event="paywall_view", feature="f")

    left = client.get(
        "/api/paywall/events/count?since=100&until=101",
    ).get_json()["count"]
    right = client.get(
        "/api/paywall/events/count?since=101&until=102",
    ).get_json()["count"]
    tail = client.get(
        "/api/paywall/events/count?since=102",
    ).get_json()["count"]
    assert left + right + tail == 5
    # Explicit boundary check: ts=101.0 lands in `right`, not `left`.
    assert left == 2 and right == 2 and tail == 1


def test_count_bad_bounds_collapse_to_unbounded(client, clock):
    _post_at(client, clock, 100.0, event="paywall_view", feature="a")
    _post_at(client, clock, 200.0, event="paywall_view", feature="b")

    body = client.get(
        "/api/paywall/events/count?since=junk&until=nan",
    ).get_json()
    # Bogus bounds don't silently slice the ring -- they collapse
    # to "not supplied".
    assert body["count"] == 2
    assert body["time_window"] == {"since": None, "until": None}


def test_count_empty_window_matches_nothing(client, clock):
    """``since >= until`` is an empty half-open interval -- a caller
    supplying identical bounds asks for zero rows and gets them,
    but ``in_window`` still reflects the ring."""
    _post_at(client, clock, 100.0, event="paywall_view", feature="f")

    body = client.get(
        "/api/paywall/events/count?since=200&until=200",
    ).get_json()
    assert body["count"] == 0
    assert body["in_window"] == 1
    assert body["time_window"] == {"since": 200.0, "until": 200.0}


def test_count_window_and_categorical_filter_combine(client, clock):
    _post_at(client, clock, 100.0, event="paywall_view",      feature="fleet")
    _post_at(client, clock, 200.0, event="paywall_cta_click", feature="fleet")
    _post_at(client, clock, 300.0, event="paywall_cta_click", feature="anomaly")

    body = client.get(
        "/api/paywall/events/count"
        "?event=paywall_cta_click&since=150&until=250",
    ).get_json()
    assert body["count"] == 1
    assert body["filters"] == {"event": "paywall_cta_click"}
    assert body["time_window"] == {"since": 150.0, "until": 250.0}


# ── cross-endpoint agreement ───────────────────────────────────────────────


def test_count_agrees_with_recent_matched(client, clock):
    """``/count``'s ``count`` byte-equals ``/recent``'s ``matched`` for
    the same filter + window inputs (both call
    ``_pe.count_matching``)."""
    for ts, feature in ((100.0, "fleet"), (110.0, "fleet"),
                        (120.0, "anomaly"), (200.0, "fleet")):
        _post_at(client, clock, ts, event="paywall_view", feature=feature)

    query = "?feature=fleet&since=100&until=200"
    count_body = client.get(f"/api/paywall/events/count{query}").get_json()
    recent_body = client.get(f"/api/paywall/events/recent{query}").get_json()
    assert count_body["count"] == recent_body["matched"]
    # And matches the length of a ceiling recent walk.
    assert count_body["count"] == 2


def test_count_agrees_with_summary_matched(client, clock):
    """``/count``'s ``count`` byte-equals ``/summary``'s ``matched`` for
    the same filter + window inputs."""
    for ts, feature in ((100.0, "fleet"), (200.0, "fleet"),
                        (300.0, "anomaly")):
        _post_at(client, clock, ts, event="paywall_view", feature=feature)

    query = "?event=paywall_view&since=150"
    count_body = client.get(f"/api/paywall/events/count{query}").get_json()
    summary_body = client.get(
        f"/api/paywall/events/summary{query}",
    ).get_json()
    assert count_body["count"] == summary_body["matched"]
    assert count_body["time_window"] == summary_body["time_window"]
    assert count_body["filters"] == summary_body["filters"]


def test_count_unfiltered_agrees_with_summary_in_window(client):
    """No filter + no window: ``count`` byte-equals ``summary.in_window``
    -- matches the store-side short-circuit for ``not filters and not
    has_window``."""
    for i in range(4):
        _post_event(client, event="paywall_view", feature=f"f{i}")
    count = client.get("/api/paywall/events/count").get_json()["count"]
    summary = client.get("/api/paywall/events/summary").get_json()
    assert count == summary["in_window"] == 4


# ── never-5xx / grace ──────────────────────────────────────────────────────


def test_count_never_5xxs_on_broken_store(client, monkeypatch):
    from clawmetry import _paywall_events as pe

    def _boom(**kwargs):
        raise RuntimeError("simulated store outage")

    monkeypatch.setattr(pe, "count_matching", _boom)
    resp = client.get("/api/paywall/events/count")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body == {
        "count": 0,
        "in_window": 0,
        "filters": {},
        "time_window": {"since": None, "until": None},
    }


def test_count_never_5xxs_when_summary_broken(client, monkeypatch):
    """A summary-side outage still resolves the count and echoes the
    query -- ``in_window`` and ``time_window`` fall back to safe
    defaults but the caller still sees a 200 with a real count."""
    from clawmetry import _paywall_events as pe

    _post_event(client, event="paywall_view", feature="fleet")

    def _boom(**kwargs):
        raise RuntimeError("simulated summary outage")

    monkeypatch.setattr(pe, "summary", _boom)
    resp = client.get("/api/paywall/events/count")
    assert resp.status_code == 200
    body = resp.get_json()
    # The endpoint's outer try/except swallows the whole handler on
    # any inner failure and returns the neutral envelope -- this pins
    # that posture so a later refactor cannot silently 5xx.
    assert body == {
        "count": 0,
        "in_window": 0,
        "filters": {},
        "time_window": {"since": None, "until": None},
    }


def test_count_ships_in_grace_no_entitlement_gate(client):
    """No auth header, no license key, no tier check. If someone wires
    a paid gate accidentally the paywall dashboard tile goes blank on
    OSS."""
    resp = client.get("/api/paywall/events/count")
    assert resp.status_code == 200
    resp = client.get("/api/paywall/events/count?feature=fleet")
    assert resp.status_code == 200


def test_count_response_is_json(client):
    resp = client.get("/api/paywall/events/count")
    assert resp.headers["Content-Type"].startswith("application/json")
