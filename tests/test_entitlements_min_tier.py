"""Tests for the ``min_tier_for_*`` helpers and ``/api/entitlement/required-tier``.

The lock affordance copy ("Available in Starter" / "Available in Pro") needs a
single, canonical reverse lookup from a feature or runtime to the cheapest
purchasable tier that grants it. The helpers under test are the source of
truth; this file pins the table so a future tier shuffle breaks loudly here
instead of silently in the UI.
"""
from __future__ import annotations

import importlib

import pytest
from flask import Flask


@pytest.fixture
def ent(monkeypatch, tmp_path):
    monkeypatch.delenv("CLAWMETRY_ENFORCE", raising=False)
    monkeypatch.setenv("HOME", str(tmp_path))
    import clawmetry.entitlements as e

    importlib.reload(e)
    e.invalidate()
    yield e
    e.invalidate()


@pytest.fixture
def client(ent):
    from routes.entitlement import bp_entitlement

    app = Flask(__name__)
    app.register_blueprint(bp_entitlement)
    return app.test_client()


# ── tier_rank ────────────────────────────────────────────────────────────────


def test_tier_rank_orders_purchasable_tiers(ent):
    assert ent.tier_rank(ent.TIER_OSS) == 0
    assert ent.tier_rank(ent.TIER_CLOUD_FREE) == 0
    assert ent.tier_rank(ent.TIER_CLOUD_STARTER) > ent.tier_rank(ent.TIER_OSS)
    assert ent.tier_rank(ent.TIER_PRO) == ent.tier_rank(ent.TIER_CLOUD_PRO)
    assert ent.tier_rank(ent.TIER_CLOUD_PRO) > ent.tier_rank(ent.TIER_CLOUD_STARTER)
    assert ent.tier_rank(ent.TIER_ENTERPRISE) > ent.tier_rank(ent.TIER_CLOUD_PRO)


def test_tier_rank_unknown_returns_minus_one(ent):
    assert ent.tier_rank("nope") == -1
    assert ent.tier_rank("") == -1
    assert ent.tier_rank(None) == -1


def test_tier_rank_case_insensitive(ent):
    assert ent.tier_rank("CLOUD_PRO") == ent.tier_rank(ent.TIER_CLOUD_PRO)


# ── min_tier_for_feature ─────────────────────────────────────────────────────


def test_free_feature_minimum_is_oss(ent):
    for f in sorted(ent.FREE_FEATURES):
        assert ent.min_tier_for_feature(f) == ent.TIER_OSS, f


def test_starter_features_minimum_is_starter(ent):
    for f in sorted(ent.STARTER_FEATURES):
        assert ent.min_tier_for_feature(f) == ent.TIER_CLOUD_STARTER, f


def test_pro_only_features_minimum_is_cloud_pro(ent):
    for f in sorted(ent.PRO_ONLY_FEATURES):
        assert ent.min_tier_for_feature(f) == ent.TIER_CLOUD_PRO, f


def test_enterprise_features_minimum_is_enterprise(ent):
    for f in sorted(ent.ENTERPRISE_FEATURES):
        assert ent.min_tier_for_feature(f) == ent.TIER_ENTERPRISE, f


def test_min_tier_for_feature_unknown_returns_none(ent):
    assert ent.min_tier_for_feature("not_a_real_feature") is None
    assert ent.min_tier_for_feature("") is None
    assert ent.min_tier_for_feature(None) is None


def test_min_tier_for_feature_excludes_trial(ent):
    for f in ent.PAID_FEATURES | ent.ENTERPRISE_FEATURES:
        assert ent.min_tier_for_feature(f) != ent.TIER_TRIAL, f


def test_min_tier_for_feature_is_case_insensitive(ent):
    assert ent.min_tier_for_feature("OTEL_EXPORT") == ent.TIER_CLOUD_PRO


# ── min_tier_for_runtime ─────────────────────────────────────────────────────


def test_free_runtime_minimum_is_oss(ent):
    for rt in sorted(ent.FREE_RUNTIMES):
        assert ent.min_tier_for_runtime(rt) == ent.TIER_OSS, rt


def test_paid_runtime_minimum_is_starter(ent):
    for rt in sorted(ent.PAID_RUNTIMES):
        assert ent.min_tier_for_runtime(rt) == ent.TIER_CLOUD_STARTER, rt


def test_min_tier_for_runtime_unknown_returns_none(ent):
    assert ent.min_tier_for_runtime("not_a_runtime") is None
    assert ent.min_tier_for_runtime("") is None
    assert ent.min_tier_for_runtime(None) is None


# ── Entitlement.min_tier_for ─────────────────────────────────────────────────


def test_entitlement_min_tier_for_dispatches_to_feature_and_runtime(ent):
    en = ent.get_entitlement(force=True)
    assert en.min_tier_for("sessions") == ent.TIER_OSS
    assert en.min_tier_for("otel_export") == ent.TIER_CLOUD_PRO
    assert en.min_tier_for("claude_code") == ent.TIER_CLOUD_STARTER
    assert en.min_tier_for("openclaw") == ent.TIER_OSS


def test_entitlement_min_tier_for_unknown_returns_none(ent):
    en = ent.get_entitlement(force=True)
    assert en.min_tier_for("not_a_key") is None
    assert en.min_tier_for("") is None
    assert en.min_tier_for(None) is None


# ── /api/entitlement/required-tier ───────────────────────────────────────────


def test_required_tier_for_feature(client, ent):
    resp = client.get("/api/entitlement/required-tier?feature=otel_export")
    assert resp.status_code == 200
    d = resp.get_json()
    assert d["key"] == "otel_export"
    assert d["kind"] == "feature"
    assert d["required_tier"] == ent.TIER_CLOUD_PRO
    assert d["current_tier"] == ent.TIER_OSS
    assert d["upgrade_required"] is True
    assert d["allowed"] is True  # grace mode


def test_required_tier_for_free_feature(client, ent):
    d = client.get("/api/entitlement/required-tier?feature=sessions").get_json()
    assert d["required_tier"] == ent.TIER_OSS
    assert d["upgrade_required"] is False
    assert d["allowed"] is True


def test_required_tier_for_runtime(client, ent):
    d = client.get("/api/entitlement/required-tier?runtime=claude_code").get_json()
    assert d["key"] == "claude_code"
    assert d["kind"] == "runtime"
    assert d["required_tier"] == ent.TIER_CLOUD_STARTER
    assert d["upgrade_required"] is True


def test_required_tier_unknown_key_is_null_not_error(client):
    resp = client.get("/api/entitlement/required-tier?feature=nope_does_not_exist")
    assert resp.status_code == 200
    d = resp.get_json()
    assert d["required_tier"] is None
    assert d["upgrade_required"] is False


def test_required_tier_requires_one_query_param(client):
    assert client.get("/api/entitlement/required-tier").status_code == 400
    assert client.get(
        "/api/entitlement/required-tier?feature=sessions&runtime=openclaw"
    ).status_code == 400
