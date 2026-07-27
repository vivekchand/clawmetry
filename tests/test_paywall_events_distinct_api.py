"""API tests for the paywall-event distinct-values endpoint:

  GET /api/paywall/events/distinct

Thin JSON wrapper around :func:`clawmetry._paywall_events.distinct_values`
-- populates filter-dropdown options for the paywall-events dashboard so
a UI never lists dead filter values. Store-level distinct_values
invariants (sorting, dedup, filter-before-distinct, empty-string
exclusion, ``summary`` parity) live in ``test_paywall_events_distinct.py``;
these tests pin the HTTP contract:

* Never 5xxs.
* Ships in GRACE -- no entitlement gate.
* Empty ring returns the neutral all-empty envelope, including a
  ``time_window: {since: null, until: null}`` echo so a dashboard tile
  can trust the top-level key set is stable regardless of window
  supply.
* Categorical filter params (``event`` / ``feature`` / ``harness`` /
  ``source`` / ``plan_chosen``) narrow the ring BEFORE the distinct
  set is computed and echo back under ``filters`` (blank ones
  omitted).
* Time-window params (``since`` / ``until``) apply the half-open
  ``[since, until)`` semantics and echo the resolved bounds under
  ``time_window``. Bad bounds collapse to "not supplied".
* Cross-endpoint agreement: for the same inputs the per-dimension
  ``distinct`` list byte-equals the sorted keys of
  ``/api/paywall/events/summary``'s corresponding ``by_*`` dict.
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


_EMPTY_DISTINCT = {
    "event": [],
    "feature": [],
    "harness": [],
    "source": [],
    "plan_chosen": [],
}


# ── empty ring ──────────────────────────────────────────────────────────────


def test_distinct_empty_ring_returns_neutral_envelope(client):
    body = client.get("/api/paywall/events/distinct").get_json()
    assert body == {
        "distinct": _EMPTY_DISTINCT,
        "in_window": 0,
        "matched": 0,
        "filters": {},
        "time_window": {"since": None, "until": None},
    }


def test_distinct_envelope_always_carries_top_level_keys(client):
    body = client.get("/api/paywall/events/distinct").get_json()
    assert set(body.keys()) == {
        "distinct", "in_window", "matched", "filters", "time_window",
    }
    assert set(body["distinct"].keys()) == set(_EMPTY_DISTINCT.keys())


# ── unfiltered ──────────────────────────────────────────────────────────────


def test_distinct_unfiltered_returns_sorted_uniques(client):
    _post_event(client, event="paywall_view", feature="fleet")
    _post_event(client, event="paywall_cta_click", feature="anomaly")
    _post_event(client, event="paywall_view", feature="fleet")  # dup

    body = client.get("/api/paywall/events/distinct").get_json()
    assert body["distinct"]["event"] == ["paywall_cta_click", "paywall_view"]
    assert body["distinct"]["feature"] == ["anomaly", "fleet"]
    assert body["in_window"] == 3
    assert body["matched"] == 3


def test_distinct_unfiltered_matched_equals_in_window(client):
    for i in range(4):
        _post_event(client, event="paywall_view", feature=f"f{i}")
    body = client.get("/api/paywall/events/distinct").get_json()
    assert body["matched"] == body["in_window"] == 4


# ── categorical filters ────────────────────────────────────────────────────


def test_distinct_filter_narrows_before_distinct_set(client):
    _post_event(client, event="paywall_view", feature="fleet")
    _post_event(client, event="paywall_view", feature="anomaly")
    _post_event(client, event="paywall_cta_click", feature="self_evolve")

    body = client.get(
        "/api/paywall/events/distinct?event=paywall_view",
    ).get_json()
    # self_evolve co-occurs only with paywall_cta_click -- must not appear.
    assert body["distinct"]["feature"] == ["anomaly", "fleet"]
    assert body["distinct"]["event"] == ["paywall_view"]
    assert body["matched"] == 2
    assert body["in_window"] == 3
    assert body["filters"] == {"event": "paywall_view"}


def test_distinct_blank_filter_is_not_supplied(client):
    _post_event(client, event="paywall_view", feature="fleet")
    body = client.get(
        "/api/paywall/events/distinct?event=&feature=",
    ).get_json()
    assert body["filters"] == {}
    assert body["distinct"]["feature"] == ["fleet"]
    assert body["matched"] == 1


def test_distinct_combines_filters_with_and(client):
    _post_event(client, event="paywall_view", feature="fleet", harness="claude_code")
    _post_event(client, event="paywall_view", feature="fleet", harness="codex")
    _post_event(client, event="paywall_cta_click", feature="fleet", harness="claude_code")

    body = client.get(
        "/api/paywall/events/distinct"
        "?event=paywall_view&feature=fleet",
    ).get_json()
    assert body["distinct"]["harness"] == ["claude_code", "codex"]
    assert body["matched"] == 2
    assert body["filters"] == {"event": "paywall_view", "feature": "fleet"}


def test_distinct_all_five_filter_axes_echo(client):
    _post_event(
        client,
        event="paywall_cta_click",
        feature="fleet",
        harness="claude_code",
        source="banner",
        plan_chosen="cloud_pro",
    )
    body = client.get(
        "/api/paywall/events/distinct"
        "?event=paywall_cta_click"
        "&feature=fleet"
        "&harness=claude_code"
        "&source=banner"
        "&plan_chosen=cloud_pro",
    ).get_json()
    assert body["filters"] == {
        "event": "paywall_cta_click",
        "feature": "fleet",
        "harness": "claude_code",
        "source": "banner",
        "plan_chosen": "cloud_pro",
    }
    assert body["matched"] == 1


def test_distinct_filter_no_match_yields_empty_lists(client):
    _post_event(client, event="paywall_view", feature="fleet")
    body = client.get(
        "/api/paywall/events/distinct?event=not_a_real_event",
    ).get_json()
    assert body["distinct"] == _EMPTY_DISTINCT
    assert body["matched"] == 0
    assert body["in_window"] == 1


# ── time-window semantics ──────────────────────────────────────────────────


def test_distinct_time_window_echoes_resolved_bounds(client, clock):
    _post_at(client, clock, 100.0, event="paywall_view", feature="a")
    _post_at(client, clock, 200.0, event="paywall_view", feature="b")

    body = client.get(
        "/api/paywall/events/distinct?since=150&until=250",
    ).get_json()
    assert body["distinct"]["feature"] == ["b"]
    assert body["time_window"] == {"since": 150.0, "until": 250.0}


def test_distinct_since_is_inclusive_until_is_exclusive(client, clock):
    _post_at(client, clock, 100.0, event="paywall_view", feature="a")
    _post_at(client, clock, 101.0, event="paywall_view", feature="b")

    body = client.get(
        "/api/paywall/events/distinct?since=100",
    ).get_json()
    assert body["distinct"]["feature"] == ["a", "b"]
    assert body["time_window"] == {"since": 100.0, "until": None}

    body = client.get(
        "/api/paywall/events/distinct?until=101",
    ).get_json()
    assert body["distinct"]["feature"] == ["a"]
    assert body["time_window"] == {"since": None, "until": 101.0}


def test_distinct_bad_bounds_collapse_to_unbounded(client, clock):
    _post_at(client, clock, 100.0, event="paywall_view", feature="a")
    _post_at(client, clock, 200.0, event="paywall_view", feature="b")

    body = client.get(
        "/api/paywall/events/distinct?since=junk&until=nan",
    ).get_json()
    assert body["distinct"]["feature"] == ["a", "b"]
    assert body["time_window"] == {"since": None, "until": None}


def test_distinct_empty_window_matches_nothing(client, clock):
    _post_at(client, clock, 100.0, event="paywall_view", feature="f")
    body = client.get(
        "/api/paywall/events/distinct?since=200&until=200",
    ).get_json()
    assert body["distinct"] == _EMPTY_DISTINCT
    assert body["matched"] == 0
    assert body["in_window"] == 1
    assert body["time_window"] == {"since": 200.0, "until": 200.0}


def test_distinct_window_and_categorical_filter_combine(client, clock):
    _post_at(client, clock, 100.0, event="paywall_view",      feature="fleet")
    _post_at(client, clock, 200.0, event="paywall_cta_click", feature="fleet")
    _post_at(client, clock, 300.0, event="paywall_cta_click", feature="anomaly")

    body = client.get(
        "/api/paywall/events/distinct"
        "?event=paywall_cta_click&since=150&until=250",
    ).get_json()
    assert body["distinct"]["feature"] == ["fleet"]
    assert body["matched"] == 1
    assert body["filters"] == {"event": "paywall_cta_click"}
    assert body["time_window"] == {"since": 150.0, "until": 250.0}


# ── cross-endpoint agreement with /summary ─────────────────────────────────


def test_distinct_agrees_with_summary_by_star_keys(client):
    """For the same filter + window inputs the per-dimension distinct
    list byte-equals the sorted keys of ``/summary``'s corresponding
    ``by_*`` dict -- pinned so the two dashboard views cannot silently
    drift."""
    _post_event(client, event="paywall_view", feature="fleet", harness="claude_code")
    _post_event(client, event="paywall_cta_click", feature="anomaly", harness="codex")
    _post_event(client, event="paywall_view", feature="fleet", harness="claude_code")

    distinct_body = client.get("/api/paywall/events/distinct").get_json()
    summary_body = client.get("/api/paywall/events/summary").get_json()
    for dim, by_key in (
        ("event", "by_event"),
        ("feature", "by_feature"),
        ("harness", "by_harness"),
        ("source", "by_source"),
        ("plan_chosen", "by_plan_chosen"),
    ):
        assert distinct_body["distinct"][dim] == sorted(
            summary_body[by_key].keys(),
        ), dim


def test_distinct_agrees_with_summary_matched(client, clock):
    for ts, feature in ((100.0, "fleet"), (200.0, "fleet"),
                        (300.0, "anomaly")):
        _post_at(client, clock, ts, event="paywall_view", feature=feature)

    query = "?event=paywall_view&since=150"
    distinct = client.get(f"/api/paywall/events/distinct{query}").get_json()
    summary = client.get(f"/api/paywall/events/summary{query}").get_json()
    assert distinct["matched"] == summary["matched"]
    assert distinct["time_window"] == summary["time_window"]
    assert distinct["filters"] == summary["filters"]


# ── never-5xx / grace ──────────────────────────────────────────────────────


def test_distinct_never_5xxs_on_broken_store(client, monkeypatch):
    from clawmetry import _paywall_events as pe

    def _boom(**kwargs):
        raise RuntimeError("simulated store outage")

    monkeypatch.setattr(pe, "distinct_values", _boom)
    resp = client.get("/api/paywall/events/distinct")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body == {
        "distinct": _EMPTY_DISTINCT,
        "in_window": 0,
        "matched": 0,
        "filters": {},
        "time_window": {"since": None, "until": None},
    }


def test_distinct_ships_in_grace_no_entitlement_gate(client):
    """No auth header, no license key, no tier check."""
    resp = client.get("/api/paywall/events/distinct")
    assert resp.status_code == 200
    resp = client.get("/api/paywall/events/distinct?feature=fleet")
    assert resp.status_code == 200


def test_distinct_response_is_json(client):
    resp = client.get("/api/paywall/events/distinct")
    assert resp.headers["Content-Type"].startswith("application/json")
