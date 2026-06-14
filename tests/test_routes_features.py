"""Tests for the ``/api/features`` endpoint (``routes/entitlement.py``).

The endpoint feeds the locked-but-visible upgrade affordance on paid features
in the dashboard — every paid feature appears in the catalog even when the
local install does not exercise it, with ``locked`` set from the resolved
entitlement and ``tier`` set to the minimum tier that unlocks it (so the CTA
can read "Requires Starter" / "Requires Pro" / "Requires Enterprise"
verbatim from the API).

Headline invariant: in GRACE mode (the default) every catalog row reports
``locked=False`` so the UI behaves exactly as it did before this endpoint
existed. ``CLAWMETRY_ENFORCE=1`` flips the paid rows to ``locked=True`` for an
OSS install.
"""
from __future__ import annotations

import importlib
import json

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


# ── shape ─────────────────────────────────────────────────────────────────────


def test_features_endpoint_returns_200(client):
    resp = client.get("/api/features")
    assert resp.status_code == 200
    data = resp.get_json()
    assert "features" in data
    assert "grace" in data
    assert "enforced" in data
    assert isinstance(data["features"], list)
    assert data["features"], "feature catalog should never be empty"


def test_features_row_shape_is_stable(client):
    data = client.get("/api/features").get_json()
    for row in data["features"]:
        for key in ("id", "label", "tier", "free", "allowed", "locked", "entitled"):
            assert key in row, row
        assert isinstance(row["id"], str)
        assert isinstance(row["label"], str)
        assert isinstance(row["free"], bool)
        assert isinstance(row["allowed"], bool)
        assert isinstance(row["locked"], bool)
        assert isinstance(row["entitled"], bool)
        assert row["tier"] in {"oss", "cloud_starter", "cloud_pro", "enterprise"}
        if row["free"]:
            assert row["locked"] is False, row
            assert row["tier"] == "oss", row


def test_features_grace_locks_nothing(client):
    data = client.get("/api/features").get_json()
    assert data["grace"] is True
    assert data["enforced"] is False
    for row in data["features"]:
        assert row["locked"] is False, row


def test_features_grace_enforced_are_inverse(client):
    data = client.get("/api/features").get_json()
    assert data["grace"] == (not data["enforced"])


# ── enforce mode ─────────────────────────────────────────────────────────────


def test_features_enforced_oss_locks_paid(monkeypatch, tmp_path):
    """When CLAWMETRY_ENFORCE=1 and no license/cloud plan is present every
    paid feature is reported locked — the UI uses this to render the 🔒
    affordance on features the OSS install cannot exercise."""
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    monkeypatch.setenv("HOME", str(tmp_path))
    import clawmetry.entitlements as e

    importlib.reload(e)
    e.invalidate()

    from routes.entitlement import bp_entitlement

    app = Flask(__name__)
    app.register_blueprint(bp_entitlement)
    data = app.test_client().get("/api/features").get_json()

    assert data["enforced"] is True
    assert data["grace"] is False
    by_id = {row["id"]: row for row in data["features"]}
    # Free stays free.
    assert by_id["sessions"]["locked"] is False
    assert by_id["sessions"]["tier"] == "oss"
    # Starter locked at OSS.
    assert by_id["multi_runtime"]["locked"] is True
    assert by_id["multi_runtime"]["tier"] == "cloud_starter"
    # Pro locked at OSS.
    assert by_id["self_evolve"]["locked"] is True
    assert by_id["self_evolve"]["tier"] == "cloud_pro"
    # Enterprise locked at OSS.
    assert by_id["sso"]["locked"] is True
    assert by_id["sso"]["tier"] == "enterprise"


def test_features_cloud_pro_unlocks_pro_keeps_enterprise_locked(monkeypatch, tmp_path):
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    monkeypatch.setenv("HOME", str(tmp_path))
    import clawmetry.entitlements as e

    importlib.reload(e)
    e.invalidate()

    cache = tmp_path / ".clawmetry" / "cloud_plan.json"
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(json.dumps({"plan": "cloud_pro"}))

    from routes.entitlement import bp_entitlement

    app = Flask(__name__)
    app.register_blueprint(bp_entitlement)
    data = app.test_client().get("/api/features").get_json()
    by_id = {row["id"]: row for row in data["features"]}
    assert by_id["multi_runtime"]["locked"] is False
    assert by_id["self_evolve"]["locked"] is False
    assert by_id["siem_export"]["locked"] is True


def test_features_ordering_deterministic(client):
    """Two consecutive reads return the same id ordering — the upgrade list
    must not reshuffle on refresh."""
    a = [row["id"] for row in client.get("/api/features").get_json()["features"]]
    b = [row["id"] for row in client.get("/api/features").get_json()["features"]]
    assert a == b
