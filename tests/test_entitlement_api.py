"""Tests for the ``/api/entitlement`` endpoint (``routes/entitlement.py``).

Validates the JSON shape, grace/enforced flag round-trip, per-tier runtime
list, and the ``is_paid`` flag under each representative paid tier — so the
dashboard's entitlement consumer never receives a surprise null or stale shape.

Complements ``tests/test_routes_runtimes.py`` which covers ``/api/runtimes``.
"""
from __future__ import annotations

import importlib
import json

import pytest
from flask import Flask


@pytest.fixture
def client(monkeypatch, tmp_path):
    """Flask test client wired with bp_entitlement and a clean HOME."""
    monkeypatch.delenv("CLAWMETRY_ENFORCE", raising=False)
    monkeypatch.setenv("HOME", str(tmp_path))
    import clawmetry.entitlements as e

    importlib.reload(e)
    e.invalidate()

    from routes.entitlement import bp_entitlement

    app = Flask(__name__)
    app.register_blueprint(bp_entitlement)
    return app.test_client(), tmp_path


# ── shape invariants ──────────────────────────────────────────────────────────


def test_api_entitlement_shape_grace(client):
    c, _ = client
    resp = c.get("/api/entitlement")
    assert resp.status_code == 200
    d = resp.get_json()
    for key in ("tier", "source", "grace", "enforced", "is_paid",
                "retention_days", "runtimes", "features", "all_runtimes"):
        assert key in d, key
    assert isinstance(d["runtimes"], list)
    assert isinstance(d["features"], list)
    assert isinstance(d["all_runtimes"], list)


@pytest.mark.parametrize(
    "plan,expected",
    [
        ("cloud_starter", 30),
        ("cloud_pro", 90),
        ("enterprise", None),
    ],
)
def test_api_entitlement_retention_days_matches_tier(monkeypatch, tmp_path, plan, expected):
    """``/api/entitlement`` carries the per-tier retention cap so the
    dashboard can render "we are keeping N days" without re-deriving the
    table client-side. Enterprise comes back as JSON ``null`` (= unlimited /
    custom). Pinned alongside the in-process ``to_dict`` test so an accidental
    desync between the method, the dict, and the HTTP shape fails loudly."""
    monkeypatch.delenv("CLAWMETRY_ENFORCE", raising=False)
    monkeypatch.setenv("HOME", str(tmp_path))
    import clawmetry.entitlements as e
    importlib.reload(e)
    e.invalidate()

    cache = tmp_path / ".clawmetry" / "cloud_plan.json"
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(json.dumps({"plan": plan, "node_limit": 1, "expiry": None}))

    from routes.entitlement import bp_entitlement
    app = Flask(__name__)
    app.register_blueprint(bp_entitlement)
    d = app.test_client().get("/api/entitlement").get_json()

    assert d["tier"] == plan
    assert d["retention_days"] == expected


def test_api_entitlement_retention_days_oss_default(client):
    """OSS-free surfaces ``retention_days == 7`` — the same value the
    never-raise fallback hard-codes, so a resolver failure can't silently
    flip the surfaced cap."""
    c, _ = client
    d = c.get("/api/entitlement").get_json()
    assert d["retention_days"] == 7


def test_api_entitlement_grace_defaults(client):
    c, _ = client
    d = c.get("/api/entitlement").get_json()
    assert d["grace"] is True
    assert d["enforced"] is False
    assert d["is_paid"] is False
    assert d["tier"] == "oss"
    # OSS tier: runtimes lists the entitled set (FREE_RUNTIMES); all_runtimes
    # is the full catalog.  In grace mode every runtime is *allowed* (via
    # allows_runtime), but the runtimes field reflects the tier's grant.
    import clawmetry.entitlements as e
    assert set(d["runtimes"]) == set(e.FREE_RUNTIMES)
    assert set(d["all_runtimes"]) == set(e.ALL_RUNTIMES)


def test_api_entitlement_grace_enforced_are_inverse(client):
    """grace and enforced must always be exact inverses — the frontend uses
    both and breaking this causes half the UI to show the wrong lock state."""
    c, _ = client
    d = c.get("/api/entitlement").get_json()
    assert d["grace"] == (not d["enforced"])


# ── enforce mode ─────────────────────────────────────────────────────────────


def test_api_entitlement_enforced_oss_grace_false(monkeypatch, tmp_path):
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    monkeypatch.setenv("HOME", str(tmp_path))
    import clawmetry.entitlements as e
    importlib.reload(e)
    e.invalidate()

    from routes.entitlement import bp_entitlement
    app = Flask(__name__)
    app.register_blueprint(bp_entitlement)
    d = app.test_client().get("/api/entitlement").get_json()

    assert d["grace"] is False
    assert d["enforced"] is True
    assert d["is_paid"] is False
    # In enforced OSS, only free runtimes are available.
    assert set(d["runtimes"]) == set(e.FREE_RUNTIMES)
    assert d["grace"] == (not d["enforced"])




# ── refresh endpoint ──────────────────────────────────────────────────────────


def test_api_entitlement_refresh_grace_shape(client):
    """POST /api/entitlement/refresh returns the same shape as GET when no
    license/cloud plan is present, and never raises on a clean HOME."""
    c, _ = client
    resp = c.post("/api/entitlement/refresh")
    assert resp.status_code == 200
    d = resp.get_json()
    for key in ("tier", "source", "grace", "enforced", "is_paid",
                "runtimes", "features"):
        assert key in d, key
    assert d["tier"] == "oss"
    assert d["grace"] is True
    assert d["enforced"] is False
    assert d["grace"] == (not d["enforced"])


def test_api_entitlement_refresh_busts_cache(monkeypatch, tmp_path):
    """Refresh must pick up a cloud_plan.json that was written *after* the
    first GET populated the cache, without waiting for the 60 s TTL."""
    monkeypatch.delenv("CLAWMETRY_ENFORCE", raising=False)
    monkeypatch.setenv("HOME", str(tmp_path))
    import clawmetry.entitlements as e
    importlib.reload(e)
    e.invalidate()

    from routes.entitlement import bp_entitlement
    app = Flask(__name__)
    app.register_blueprint(bp_entitlement)
    client_ = app.test_client()

    first = client_.get("/api/entitlement").get_json()
    assert first["tier"] == "oss"
    assert first["source"] == "oss"

    cache = tmp_path / ".clawmetry" / "cloud_plan.json"
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(json.dumps({"plan": "cloud_pro", "node_limit": 5,
                                 "expiry": None}))

    # GET still returns the cached OSS result — TTL hasn't elapsed.
    stale = client_.get("/api/entitlement").get_json()
    assert stale["tier"] == "oss"

    refreshed = client_.post("/api/entitlement/refresh").get_json()
    assert refreshed["tier"] == "cloud_pro"
    assert refreshed["source"] == "cloud"
    assert refreshed["is_paid"] is True


def test_api_entitlement_refresh_idempotent(client):
    """Repeated refresh calls return identical shapes — refresh must be safe
    to spam from a dashboard timer / connect-flow retry loop."""
    c, _ = client
    a = c.post("/api/entitlement/refresh").get_json()
    b = c.post("/api/entitlement/refresh").get_json()
    assert a == b


# ── paid tiers ────────────────────────────────────────────────────────────────


@pytest.mark.parametrize("tier", ["trial", "pro", "cloud_pro"])
def test_api_entitlement_paid_tier_grants_all_runtimes(monkeypatch, tmp_path, tier):
    """Subscribers on trial / pro / cloud_pro get is_paid=True and all runtimes
    in the runtimes list even with enforcement on."""
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    monkeypatch.setenv("HOME", str(tmp_path))
    import clawmetry.entitlements as e
    importlib.reload(e)
    e.invalidate()

    cache = tmp_path / ".clawmetry" / "cloud_plan.json"
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(json.dumps({"plan": tier, "node_limit": 1, "expiry": None}))

    from routes.entitlement import bp_entitlement
    app = Flask(__name__)
    app.register_blueprint(bp_entitlement)
    d = app.test_client().get("/api/entitlement").get_json()

    assert d["tier"] == tier
    assert d["is_paid"] is True
    assert d["grace"] is False
    assert d["grace"] == (not d["enforced"])
    # All paid runtimes must be present.
    for rt in e.PAID_RUNTIMES:
        assert rt in d["runtimes"], f"{tier}: {rt} missing from runtimes"
