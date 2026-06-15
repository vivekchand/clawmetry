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
                "runtimes", "features", "all_runtimes"):
        assert key in d, key
    assert isinstance(d["runtimes"], list)
    assert isinstance(d["features"], list)
    assert isinstance(d["all_runtimes"], list)


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


# ── tier_label on /api/entitlement ──────────────────────────────────────────


def test_api_entitlement_carries_tier_label(client):
    """The payload includes a human-readable label alongside the tier id so
    the dashboard's tier badge can render without a duplicate JS map."""
    c, _ = client
    d = c.get("/api/entitlement").get_json()
    assert d["tier"] == "oss"
    assert d["tier_label"] == "OSS"


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

    # GET still returns the cached OSS result -- TTL hasn't elapsed.
    stale = client_.get("/api/entitlement").get_json()
    assert stale["tier"] == "oss"

    refreshed = client_.post("/api/entitlement/refresh").get_json()
    assert refreshed["tier"] == "cloud_pro"
    assert refreshed["source"] == "cloud"
    assert refreshed["is_paid"] is True


def test_api_entitlement_refresh_idempotent(client):
    """Repeated refresh calls return identical shapes -- refresh must be safe
    to spam from a dashboard timer / connect-flow retry loop."""
    c, _ = client
    a = c.post("/api/entitlement/refresh").get_json()
    b = c.post("/api/entitlement/refresh").get_json()
    assert a == b


# ── upgrade-diff endpoint ────────────────────────────────────────────────────


def test_api_upgrade_diff_oss_to_cloud_pro(client):
    c, _ = client
    resp = c.get("/api/entitlement/upgrade-diff?target=cloud_pro")
    assert resp.status_code == 200
    d = resp.get_json()
    assert d["target"] == "cloud_pro"
    import clawmetry.entitlements as e
    assert set(d["added_features"]) == set(e.PAID_FEATURES)
    assert set(d["added_runtimes"]) == set(e.PAID_RUNTIMES)
    assert d["added_features"] == sorted(d["added_features"])
    assert d["added_runtimes"] == sorted(d["added_runtimes"])


def test_api_upgrade_diff_unknown_target_is_empty_not_500(client):
    c, _ = client
    resp = c.get("/api/entitlement/upgrade-diff?target=nope")
    assert resp.status_code == 200
    d = resp.get_json()
    assert d["target"] == "nope"
    assert d["added_features"] == []
    assert d["added_runtimes"] == []


def test_api_upgrade_diff_missing_target_is_empty(client):
    c, _ = client
    resp = c.get("/api/entitlement/upgrade-diff")
    assert resp.status_code == 200
    d = resp.get_json()
    assert d["added_features"] == []
    assert d["added_runtimes"] == []


def test_api_upgrade_diff_case_insensitive(client):
    c, _ = client
    a = c.get("/api/entitlement/upgrade-diff?target=cloud_pro").get_json()
    b = c.get("/api/entitlement/upgrade-diff?target=CLOUD_PRO").get_json()
    assert a["added_features"] == b["added_features"]
    assert a["added_runtimes"] == b["added_runtimes"]


@pytest.mark.parametrize("tier,expected_runtime_diff", [
    ("cloud_starter", "paid"),
    ("cloud_pro", "paid"),
    ("enterprise", "paid"),
])
def test_api_upgrade_diff_paid_tiers_all_unlock_paid_runtimes(client, tier,
                                                               expected_runtime_diff):
    c, _ = client
    d = c.get(f"/api/entitlement/upgrade-diff?target={tier}").get_json()
    import clawmetry.entitlements as e
    assert set(d["added_runtimes"]) == set(e.PAID_RUNTIMES)


def test_api_upgrade_diff_starter_subscriber_to_pro(monkeypatch, tmp_path):
    """A Starter subscriber asking for Pro should only see PRO_ONLY features."""
    monkeypatch.delenv("CLAWMETRY_ENFORCE", raising=False)
    monkeypatch.setenv("HOME", str(tmp_path))
    import clawmetry.entitlements as e
    importlib.reload(e)
    e.invalidate()

    cache = tmp_path / ".clawmetry" / "cloud_plan.json"
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(json.dumps({"plan": "cloud_starter", "node_limit": 1,
                                 "expiry": None}))

    from routes.entitlement import bp_entitlement
    app = Flask(__name__)
    app.register_blueprint(bp_entitlement)
    d = app.test_client().get("/api/entitlement/upgrade-diff?target=cloud_pro").get_json()

    assert set(d["added_features"]) == set(e.PRO_ONLY_FEATURES)
    assert d["added_runtimes"] == []


# ── grace countdown ───────────────────────────────────────────────────────────


def test_api_entitlement_enforce_at_keys_unset(client):
    """Always present on /api/entitlement so frontend can read them without
    a feature-detect; unset means all three are null."""
    c, _ = client
    d = c.get("/api/entitlement").get_json()
    for key in ("enforce_at", "enforce_at_iso", "days_until_enforce"):
        assert key in d, key
        assert d[key] is None


def test_api_entitlement_enforce_at_surfaced(monkeypatch, tmp_path):
    monkeypatch.delenv("CLAWMETRY_ENFORCE", raising=False)
    monkeypatch.setenv("CLAWMETRY_ENFORCE_AT", "2099-01-01T00:00:00Z")
    monkeypatch.setenv("HOME", str(tmp_path))
    import clawmetry.entitlements as e
    importlib.reload(e)
    e.invalidate()

    from routes.entitlement import bp_entitlement
    app = Flask(__name__)
    app.register_blueprint(bp_entitlement)
    d = app.test_client().get("/api/entitlement").get_json()
    assert d["enforce_at"] is not None
    assert d["enforce_at_iso"] == "2099-01-01T00:00:00Z"
    assert isinstance(d["days_until_enforce"], int)
    assert d["days_until_enforce"] > 0
    assert d["grace"] is True
    assert d["enforced"] is False
