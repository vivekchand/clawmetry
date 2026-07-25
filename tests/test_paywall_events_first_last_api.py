"""API tests for the two new scalar paywall-event read endpoints:

  GET /api/paywall/events/last
  GET /api/paywall/events/first

Both are thin JSON wrappers around
:func:`clawmetry._paywall_events.last_matching` /
:func:`clawmetry._paywall_events.first_matching`. Store-level
invariants live in ``test_paywall_events_first_last_matching.py``; the
tests here pin the HTTP contract:

* Both endpoints must never 5xx.
* Both must never gate on the entitlement -- they surface OSS-free
  beacon activity that a paywall dashboard tile needs even on OSS.
* Empty ring returns the neutral ``event=null`` envelope.
* Filter params echo back under ``filters`` (blank ones omitted).
* ``matched`` mirrors the underlying ``count_matching`` count.
"""
from __future__ import annotations

import json

import pytest
from flask import Flask


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


def _post_event(client, **fields):
    resp = client.post(
        "/api/paywall/event",
        data=json.dumps(fields),
        content_type="application/json",
    )
    assert resp.status_code == 204


# ── /api/paywall/events/last ────────────────────────────────────────────────


def test_last_empty_ring_returns_null_envelope(client):
    body = client.get("/api/paywall/events/last").get_json()
    assert body == {
        "event": None,
        "matched": 0,
        "in_window": 0,
        "filters": {},
    }


def test_last_reflects_most_recent_beacon(client):
    _post_event(client, event="paywall_view", feature="fleet")
    _post_event(client, event="paywall_view", feature="self_evolve")
    _post_event(client, event="paywall_cta_click", feature="fleet")

    body = client.get("/api/paywall/events/last").get_json()
    assert body["event"] is not None
    assert body["event"]["event"] == "paywall_cta_click"
    assert body["event"]["feature"] == "fleet"
    assert body["matched"] == 3
    assert body["in_window"] == 3
    assert body["filters"] == {}


def test_last_filter_narrows_to_newest_match(client):
    _post_event(client, event="paywall_view", feature="fleet")
    _post_event(client, event="paywall_view", feature="self_evolve")
    _post_event(client, event="paywall_cta_click", feature="fleet")

    body = client.get(
        "/api/paywall/events/last?event=paywall_view",
    ).get_json()
    assert body["event"] is not None
    assert body["event"]["event"] == "paywall_view"
    assert body["event"]["feature"] == "self_evolve"
    assert body["matched"] == 2
    assert body["filters"] == {"event": "paywall_view"}


def test_last_no_match_returns_null_but_non_zero_in_window(client):
    _post_event(client, event="paywall_view", feature="fleet")

    body = client.get(
        "/api/paywall/events/last?event=not_a_real_event",
    ).get_json()
    assert body["event"] is None
    assert body["matched"] == 0
    assert body["in_window"] == 1
    assert body["filters"] == {"event": "not_a_real_event"}


def test_last_blank_filter_is_not_supplied(client):
    _post_event(client, event="paywall_view", feature="fleet")

    body = client.get(
        "/api/paywall/events/last?event=&feature=",
    ).get_json()
    assert body["event"] is not None
    # Blank filters are "not supplied" -- not echoed under `filters`.
    assert body["filters"] == {}
    assert body["matched"] == 1


def test_last_combines_filters_with_and(client):
    _post_event(client, event="paywall_view", feature="fleet")
    _post_event(client, event="paywall_view", feature="self_evolve")
    _post_event(client, event="paywall_cta_click", feature="fleet")

    body = client.get(
        "/api/paywall/events/last"
        "?event=paywall_view&feature=fleet",
    ).get_json()
    assert body["event"] is not None
    assert body["event"]["event"] == "paywall_view"
    assert body["event"]["feature"] == "fleet"
    assert body["matched"] == 1
    assert body["filters"] == {"event": "paywall_view", "feature": "fleet"}


def test_last_never_5xxs_on_broken_store(client, monkeypatch):
    from clawmetry import _paywall_events as pe

    def _boom(**kwargs):
        raise RuntimeError("simulated store outage")

    monkeypatch.setattr(pe, "last_matching", _boom)
    resp = client.get("/api/paywall/events/last")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body == {
        "event": None,
        "matched": 0,
        "in_window": 0,
        "filters": {},
    }


# ── /api/paywall/events/first ───────────────────────────────────────────────


def test_first_empty_ring_returns_null_envelope(client):
    body = client.get("/api/paywall/events/first").get_json()
    assert body == {
        "event": None,
        "matched": 0,
        "in_window": 0,
        "filters": {},
    }


def test_first_reflects_oldest_beacon(client):
    _post_event(client, event="paywall_view", feature="fleet")
    _post_event(client, event="paywall_view", feature="self_evolve")
    _post_event(client, event="paywall_cta_click", feature="fleet")

    body = client.get("/api/paywall/events/first").get_json()
    assert body["event"] is not None
    assert body["event"]["event"] == "paywall_view"
    assert body["event"]["feature"] == "fleet"
    assert body["matched"] == 3
    assert body["in_window"] == 3
    assert body["filters"] == {}


def test_first_filter_narrows_to_oldest_match(client):
    _post_event(client, event="paywall_view", feature="fleet")
    _post_event(client, event="paywall_cta_click", feature="fleet")
    _post_event(client, event="paywall_view", feature="self_evolve")

    body = client.get(
        "/api/paywall/events/first?event=paywall_view",
    ).get_json()
    assert body["event"] is not None
    assert body["event"]["event"] == "paywall_view"
    assert body["event"]["feature"] == "fleet"  # oldest paywall_view
    assert body["matched"] == 2
    assert body["filters"] == {"event": "paywall_view"}


def test_first_no_match_returns_null_but_non_zero_in_window(client):
    _post_event(client, event="paywall_view", feature="fleet")

    body = client.get(
        "/api/paywall/events/first?feature=nonexistent",
    ).get_json()
    assert body["event"] is None
    assert body["matched"] == 0
    assert body["in_window"] == 1
    assert body["filters"] == {"feature": "nonexistent"}


def test_first_never_5xxs_on_broken_store(client, monkeypatch):
    from clawmetry import _paywall_events as pe

    def _boom(**kwargs):
        raise RuntimeError("simulated store outage")

    monkeypatch.setattr(pe, "first_matching", _boom)
    resp = client.get("/api/paywall/events/first")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body == {
        "event": None,
        "matched": 0,
        "in_window": 0,
        "filters": {},
    }


# ── cross-checks ────────────────────────────────────────────────────────────


def test_first_and_last_return_same_row_when_ring_has_one(client):
    _post_event(client, event="paywall_view", feature="fleet")
    first = client.get("/api/paywall/events/first").get_json()
    last = client.get("/api/paywall/events/last").get_json()
    assert first["event"] == last["event"]
    assert first["matched"] == last["matched"] == 1


def test_last_agrees_with_recent_limit_one(client):
    """``/api/paywall/events/last`` is the scalar unwrap of
    ``/api/paywall/events/recent?limit=1`` -- same row, same fields.
    """
    for i in range(5):
        _post_event(client, event=f"e{i}", feature="fleet")
    last = client.get("/api/paywall/events/last").get_json()
    recent = client.get("/api/paywall/events/recent?limit=1").get_json()
    assert last["event"] == recent["events"][0]


def test_no_entitlement_gate_ships_in_grace(client):
    """Both endpoints ship in GRACE -- no auth header, no license key
    required, no tier check. If someone wires a paid gate accidentally
    the paywall dashboard tile goes blank on OSS."""
    for path in (
        "/api/paywall/events/first",
        "/api/paywall/events/last",
    ):
        resp = client.get(path)
        assert resp.status_code == 200
