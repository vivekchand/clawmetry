"""Tests for the ``/api/features`` endpoint (``routes/entitlement.py``).

The endpoint feeds the locked-but-visible feature affordance on the settings
and paywall surfaces — every paid feature appears in the catalog even on a
free install, with ``locked`` set from the resolved entitlement. Feature-side
sibling of ``/api/runtimes`` (covered by ``tests/test_routes_runtimes.py``).

The headline invariant: in GRACE mode (the default), every catalog row reports
``locked=False`` so the UI behaves exactly as it did before this endpoint
existed. ``CLAWMETRY_ENFORCE=1`` flips the paid rows to ``locked=True`` for an
OSS install.
"""
from __future__ import annotations

import importlib

import pytest
from flask import Flask


@pytest.fixture
def client(monkeypatch, tmp_path):
    """Flask test client wired with bp_entitlement against a clean HOME."""
    monkeypatch.delenv("CLAWMETRY_ENFORCE", raising=False)
    monkeypatch.setenv("HOME", str(tmp_path))
    import clawmetry.entitlements as e

    importlib.reload(e)
    e.invalidate()

    from routes.entitlement import bp_entitlement

    app = Flask(__name__)
    app.register_blueprint(bp_entitlement)
    return app.test_client()


def test_features_grace_locks_nothing(client):
    resp = client.get("/api/features")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["grace"] is True
    assert data["enforced"] is False
    by_id = {r["id"]: r for r in data["features"]}
    # Sessions is always free.
    assert by_id["sessions"]["free"] is True
    assert by_id["sessions"]["locked"] is False
    # Every published paid feature is present and not locked in grace mode.
    for fid in (
        "multi_runtime",
        "fleet",
        "self_evolve",
        "otel_export",
        "sso",
        "audit_logs",
        "rbac",
    ):
        assert fid in by_id, fid
        assert by_id[fid]["free"] is False, fid
        assert by_id[fid]["locked"] is False, fid
        assert by_id[fid]["label"], fid  # never blank


def test_features_enforced_oss_locks_paid(monkeypatch, tmp_path):
    """When CLAWMETRY_ENFORCE=1 and no license/cloud plan is present every paid
    feature is reported locked — the UI uses this to render the 🔒 affordance
    on settings + paywall surfaces."""
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    monkeypatch.setenv("HOME", str(tmp_path))
    import clawmetry.entitlements as e

    importlib.reload(e)
    e.invalidate()

    from routes.entitlement import bp_entitlement

    app = Flask(__name__)
    app.register_blueprint(bp_entitlement)
    c = app.test_client()
    data = c.get("/api/features").get_json()
    assert data["enforced"] is True
    assert data["grace"] is False
    by_id = {r["id"]: r for r in data["features"]}
    assert by_id["sessions"]["locked"] is False  # free stays free
    assert by_id["multi_runtime"]["locked"] is True  # starter
    assert by_id["self_evolve"]["locked"] is True  # pro
    assert by_id["sso"]["locked"] is True  # enterprise


def test_features_shape_is_stable(client):
    """Each row carries the keys the frontend reads — defends against an
    accidental rename breaking settings/paywall surfaces."""
    data = client.get("/api/features").get_json()
    assert isinstance(data["features"], list)
    for row in data["features"]:
        for key in ("id", "label", "tier", "free", "allowed", "locked"):
            assert key in row, row
        assert isinstance(row["id"], str)
        assert isinstance(row["label"], str)
        assert isinstance(row["tier"], str)
        assert isinstance(row["free"], bool)
        assert isinstance(row["allowed"], bool)
        assert isinstance(row["locked"], bool)
        if row["free"]:
            assert row["locked"] is False, row


def test_features_tier_field_matches_bucket(client):
    """Each row's ``tier`` reflects the tier bucket the feature first appears
    in — drives the "STARTER+" / "PRO+" badges in the UI."""
    import clawmetry.entitlements as e

    data = client.get("/api/features").get_json()
    by_id = {r["id"]: r for r in data["features"]}
    for fid in e.FREE_FEATURES:
        assert by_id[fid]["tier"] == e.TIER_OSS, fid
    for fid in e.STARTER_FEATURES:
        assert by_id[fid]["tier"] == e.TIER_CLOUD_STARTER, fid
    for fid in e.PRO_ONLY_FEATURES:
        assert by_id[fid]["tier"] == e.TIER_CLOUD_PRO, fid
    for fid in e.ENTERPRISE_FEATURES:
        assert by_id[fid]["tier"] == e.TIER_ENTERPRISE, fid


def test_features_endpoint_never_5xxs_when_resolver_crashes(monkeypatch, tmp_path):
    """A blown resolver still returns 200 with the OSS-free fallback shape so
    the dashboard never sees a 5xx over a gate read."""
    monkeypatch.setenv("HOME", str(tmp_path))
    import clawmetry.entitlements as e

    importlib.reload(e)
    e.invalidate()

    def boom(*_a, **_kw):
        raise RuntimeError("simulated resolver failure")

    monkeypatch.setattr(e, "get_entitlement", boom)

    from routes.entitlement import bp_entitlement

    app = Flask(__name__)
    app.register_blueprint(bp_entitlement)
    c = app.test_client()
    resp = c.get("/api/features")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["grace"] is True
    assert data["enforced"] is False
    assert isinstance(data["features"], list)
    # Fallback lists at least the free features.
    ids = {r["id"] for r in data["features"]}
    for fid in ("sessions", "transcripts", "usage", "overview"):
        assert fid in ids, fid
