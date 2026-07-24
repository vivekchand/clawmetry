"""API tests for the two new paywall-event read endpoints:

  GET /api/paywall/events/summary
  GET /api/paywall/events/recent

Both are thin JSON wrappers around :mod:`clawmetry._paywall_events`.
Store-level invariants live in ``test_paywall_events_store.py`` -- these
tests pin the HTTP contract:

* Both endpoints must never 5xx (a broken store falls back to the neutral
  empty shape).
* Both must never gate on the entitlement -- they surface OSS-free beacon
  activity that a paywall dashboard tile needs to render even on OSS.
* ``summary`` returns the exact set of keys the pricing dashboard tile
  binds to (drift here would silently blank tiles).
* ``recent`` clamps ``limit`` into ``[0, 200]`` -- no unbounded response.
"""
from __future__ import annotations

import json

import pytest
from flask import Flask


@pytest.fixture
def client():
    """Minimal Flask app with ``bp_entitlement`` registered and the paywall
    store reset per test so writes don't bleed across tests."""
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


# ── summary happy path ─────────────────────────────────────────────────────


def test_summary_empty_shape(client):
    resp = client.get("/api/paywall/events/summary")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["total"] == 0
    assert body["in_window"] == 0
    assert body["dropped"] == 0
    assert body["capacity"] >= 1
    assert body["first_ts"] is None
    assert body["last_ts"] is None
    for k in ("by_event", "by_feature", "by_harness", "by_source", "by_plan_chosen"):
        assert body[k] == {}


def test_summary_reflects_prior_paywall_event_posts(client):
    """The `/api/paywall/event` beacon must feed into the store so a
    subsequent `/summary` GET reflects it."""
    for _ in range(3):
        resp = client.post(
            "/api/paywall/event",
            data=json.dumps(
                {"event": "paywall_view", "feature": "fleet", "harness": "claude_code"}
            ),
            content_type="application/json",
        )
        assert resp.status_code == 204
    client.post(
        "/api/paywall/event",
        data=json.dumps({"event": "paywall_cta_click", "plan_chosen": "pro"}),
        content_type="application/json",
    )

    body = client.get("/api/paywall/events/summary").get_json()
    assert body["total"] == 4
    assert body["in_window"] == 4
    assert body["by_event"] == {"paywall_view": 3, "paywall_cta_click": 1}
    assert body["by_feature"] == {"fleet": 3}
    assert body["by_harness"] == {"claude_code": 3}
    assert body["by_plan_chosen"] == {"pro": 1}
    assert body["first_ts"] is not None
    assert body["last_ts"] is not None
    assert body["first_ts"] <= body["last_ts"]


def test_summary_shape_is_stable(client):
    """A pricing dashboard tile binds to a fixed set of keys. If the
    endpoint ever drops one, tiles blank silently -- pin the full key
    set. ``filters`` and ``matched`` are the always-present mirror of
    ``/api/paywall/events/recent`` so a tile binding one filter set to
    both endpoints reads the same shape from each."""
    body = client.get("/api/paywall/events/summary").get_json()
    expected = {
        "total", "in_window", "dropped", "capacity",
        "first_ts", "last_ts",
        "by_event", "by_feature", "by_harness", "by_source", "by_plan_chosen",
        "filters", "matched",
    }
    assert set(body.keys()) == expected


def test_summary_never_5xxs_on_store_failure(client, monkeypatch):
    """The neutral empty shape must render even when the store raises."""
    from clawmetry import _paywall_events as pe

    def _boom():
        raise RuntimeError("simulated store failure")

    monkeypatch.setattr(pe, "summary", _boom)
    resp = client.get("/api/paywall/events/summary")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["total"] == 0
    assert body["in_window"] == 0
    assert body["by_event"] == {}


def test_summary_does_not_consult_entitlement(client, monkeypatch):
    """Store reads must not depend on the resolved entitlement -- gating
    would silently blank the tile on OSS-free (which is exactly where
    the beacon signal is most useful)."""
    import clawmetry.entitlements as ent

    monkeypatch.setattr(
        ent, "get_entitlement",
        lambda *a, **kw: (_ for _ in ()).throw(RuntimeError("nope"))
    )
    resp = client.get("/api/paywall/events/summary")
    assert resp.status_code == 200


# ── recent happy path ──────────────────────────────────────────────────────


def test_recent_empty_shape(client):
    resp = client.get("/api/paywall/events/recent")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["events"] == []
    assert body["count"] == 0
    assert body["in_window"] == 0
    # No `?limit=` -> resolves to the module's default (50).
    assert body["limit"] == 50


def test_recent_returns_newest_first(client):
    for i in range(4):
        client.post(
            "/api/paywall/event",
            data=json.dumps({"event": f"e{i}"}),
            content_type="application/json",
        )
    body = client.get("/api/paywall/events/recent").get_json()
    assert body["count"] == 4
    assert [e["event"] for e in body["events"]] == ["e3", "e2", "e1", "e0"]


def test_recent_respects_limit_query(client):
    for i in range(5):
        client.post(
            "/api/paywall/event",
            data=json.dumps({"event": f"e{i}"}),
            content_type="application/json",
        )
    body = client.get("/api/paywall/events/recent?limit=2").get_json()
    assert body["count"] == 2
    assert body["limit"] == 2
    assert [e["event"] for e in body["events"]] == ["e4", "e3"]


def test_recent_clamps_negative_limit(client):
    for i in range(3):
        client.post(
            "/api/paywall/event",
            data=json.dumps({"event": f"e{i}"}),
            content_type="application/json",
        )
    body = client.get("/api/paywall/events/recent?limit=-1").get_json()
    # Negative -> falls back to default.
    assert body["count"] == 3
    assert body["limit"] == 50


def test_recent_clamps_oversized_limit(client):
    body = client.get("/api/paywall/events/recent?limit=1000000").get_json()
    # Oversized -> clamped to _RECENT_MAX.
    assert body["limit"] == 200


def test_recent_ignores_garbage_limit(client):
    body = client.get("/api/paywall/events/recent?limit=nope").get_json()
    assert body["limit"] == 50


def test_recent_zero_limit_returns_empty_but_reports_window(client):
    client.post(
        "/api/paywall/event",
        data=json.dumps({"event": "paywall_view"}),
        content_type="application/json",
    )
    body = client.get("/api/paywall/events/recent?limit=0").get_json()
    assert body["events"] == []
    assert body["count"] == 0
    assert body["limit"] == 0
    assert body["in_window"] == 1


def test_recent_event_rows_carry_all_fields(client):
    client.post(
        "/api/paywall/event",
        data=json.dumps(
            {
                "event": "paywall_cta_click",
                "feature": "fleet",
                "harness": "claude_code",
                "source": "runtime-switcher",
                "plan_chosen": "pro",
            }
        ),
        content_type="application/json",
    )
    body = client.get("/api/paywall/events/recent?limit=1").get_json()
    row = body["events"][0]
    for key in ("event", "feature", "harness", "source", "plan_chosen", "ts"):
        assert key in row
    assert row["event"] == "paywall_cta_click"
    assert row["plan_chosen"] == "pro"


def test_recent_never_5xxs_on_store_failure(client, monkeypatch):
    from clawmetry import _paywall_events as pe

    def _boom(*_a, **_kw):
        raise RuntimeError("simulated store failure")

    monkeypatch.setattr(pe, "recent", _boom)
    resp = client.get("/api/paywall/events/recent")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body == {
        "events": [],
        "count": 0,
        "matched": 0,
        "limit": 0,
        "in_window": 0,
        "filters": {},
    }


def test_recent_does_not_consult_entitlement(client, monkeypatch):
    import clawmetry.entitlements as ent

    monkeypatch.setattr(
        ent, "get_entitlement",
        lambda *a, **kw: (_ for _ in ()).throw(RuntimeError("nope"))
    )
    resp = client.get("/api/paywall/events/recent")
    assert resp.status_code == 200


# ── method enforcement ────────────────────────────────────────────────────


def test_summary_post_not_allowed(client):
    """The summary endpoint is read-only; POST must 405 to avoid clients
    accidentally writing through it."""
    resp = client.post("/api/paywall/events/summary", data=b"{}")
    assert resp.status_code == 405


def test_recent_post_not_allowed(client):
    resp = client.post("/api/paywall/events/recent", data=b"{}")
    assert resp.status_code == 405


# ── beacon <-> store integration edge cases ────────────────────────────────


def test_post_event_with_broken_store_still_returns_204(client, monkeypatch):
    """The beacon route must not regress: if the store raises, the beacon
    still 204s so a broken store never turns into a browser error."""
    from clawmetry import _paywall_events as pe

    def _boom(_):
        raise RuntimeError("simulated store failure")

    monkeypatch.setattr(pe, "record_event", _boom)
    resp = client.post(
        "/api/paywall/event",
        data=json.dumps({"event": "paywall_view"}),
        content_type="application/json",
    )
    assert resp.status_code == 204


def test_empty_body_beacon_still_bumps_total(client):
    """Matches the store's "non-dict payload still records a beat"
    invariant -- so an operator can see that beacons are firing at all,
    even if the client is misconfigured and sends nothing."""
    resp = client.post("/api/paywall/event")
    assert resp.status_code == 204
    body = client.get("/api/paywall/events/summary").get_json()
    assert body["total"] == 1
    assert body["in_window"] == 1
    # Everything else is empty because the payload had no fields.
    assert body["by_event"] == {}
    assert body["by_feature"] == {}
