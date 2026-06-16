"""Tests for ``Entitlement.upgrade_diff`` + the module-level helper +
``GET /api/entitlement/upgrade-diff``.

The dashboard's upgrade CTA ("Upgrade to Pro - unlocks N features + M
runtimes") reads this single primitive instead of re-deriving per-tier feature
membership in JavaScript. These tests pin the per-tier delta so a future
reshuffle of the tier -> feature/runtime tables breaks loudly here instead of
silently in the UI.
"""
from __future__ import annotations

import importlib

import pytest
from flask import Flask


@pytest.fixture
def ent(monkeypatch, tmp_path):
    # Grace mode by default -- upgrade_diff is a pure-data primitive that does
    # not depend on grace; matching every other entitlement test fixture in the
    # suite keeps the test env identical.
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


# ── per-tier delta from OSS ────────────────────────────────────────────────


def test_oss_to_cloud_starter_adds_starter_features(ent):
    e = ent._oss_free()
    diff = e.upgrade_diff(ent.TIER_CLOUD_STARTER)
    assert diff["target"] == ent.TIER_CLOUD_STARTER
    assert set(diff["added_features"]) == set(ent.STARTER_FEATURES)
    # Cloud Starter is a paid tier -> unlocks every paid runtime in one shot.
    assert set(diff["added_runtimes"]) == set(ent.PAID_RUNTIMES)


def test_oss_to_cloud_pro_adds_all_paid_features(ent):
    e = ent._oss_free()
    diff = e.upgrade_diff(ent.TIER_CLOUD_PRO)
    assert diff["target"] == ent.TIER_CLOUD_PRO
    assert set(diff["added_features"]) == set(ent.PAID_FEATURES)
    assert set(diff["added_runtimes"]) == set(ent.PAID_RUNTIMES)


def test_oss_to_enterprise_adds_paid_and_enterprise_features(ent):
    e = ent._oss_free()
    diff = e.upgrade_diff(ent.TIER_ENTERPRISE)
    assert diff["target"] == ent.TIER_ENTERPRISE
    assert set(diff["added_features"]) == set(ent.PAID_FEATURES) | set(
        ent.ENTERPRISE_FEATURES
    )
    assert set(diff["added_runtimes"]) == set(ent.PAID_RUNTIMES)


# ── per-tier delta from a non-OSS starting tier ────────────────────────────


def test_starter_to_cloud_pro_adds_only_pro_only_features(ent):
    e = ent._build(ent.TIER_CLOUD_STARTER, "cloud")
    diff = e.upgrade_diff(ent.TIER_CLOUD_PRO)
    # Starter already grants STARTER_FEATURES -- only the pro-only delta
    # should appear as "added".
    assert set(diff["added_features"]) == set(ent.PRO_ONLY_FEATURES)
    # Starter is paid -> already has every paid runtime; nothing to add.
    assert diff["added_runtimes"] == []


def test_cloud_pro_to_enterprise_adds_only_enterprise_features(ent):
    e = ent._build(ent.TIER_CLOUD_PRO, "cloud")
    diff = e.upgrade_diff(ent.TIER_ENTERPRISE)
    assert set(diff["added_features"]) == set(ent.ENTERPRISE_FEATURES)
    assert diff["added_runtimes"] == []


def test_enterprise_to_enterprise_is_empty(ent):
    e = ent._build(ent.TIER_ENTERPRISE, "license")
    diff = e.upgrade_diff(ent.TIER_ENTERPRISE)
    assert diff["target"] == ent.TIER_ENTERPRISE
    assert diff["added_features"] == []
    assert diff["added_runtimes"] == []


def test_diff_to_same_or_lower_tier_is_empty(ent):
    # "Upgrading" from Pro back down to Starter is a no-op for the CTA: the
    # delta surface is a strict ADD list, so nothing should appear.
    e = ent._build(ent.TIER_CLOUD_PRO, "cloud")
    diff = e.upgrade_diff(ent.TIER_CLOUD_STARTER)
    assert diff["added_features"] == []
    assert diff["added_runtimes"] == []


# ── safety / fallback ──────────────────────────────────────────────────────


def test_unknown_target_returns_empty_lists(ent):
    diff = ent._oss_free().upgrade_diff("nonsense_tier_xyz")
    assert diff["target"] == "nonsense_tier_xyz"
    assert diff["added_features"] == []
    assert diff["added_runtimes"] == []


def test_empty_target_returns_empty_lists(ent):
    diff = ent._oss_free().upgrade_diff("")
    assert diff["added_features"] == []
    assert diff["added_runtimes"] == []


def test_target_is_lowercased(ent):
    # The dashboard renders tier ids verbatim from /api/tiers eventually; an
    # accidental upper-case query parameter must not produce a phantom miss.
    diff = ent._oss_free().upgrade_diff("CLOUD_STARTER")
    assert diff["target"] == ent.TIER_CLOUD_STARTER
    assert set(diff["added_features"]) == set(ent.STARTER_FEATURES)


def test_added_features_are_sorted(ent):
    diff = ent._oss_free().upgrade_diff(ent.TIER_CLOUD_PRO)
    assert diff["added_features"] == sorted(diff["added_features"])


def test_added_runtimes_are_sorted(ent):
    diff = ent._oss_free().upgrade_diff(ent.TIER_CLOUD_PRO)
    assert diff["added_runtimes"] == sorted(diff["added_runtimes"])


def test_added_features_never_includes_free(ent):
    # The delta is a strict ADD list; every entitlement already carries
    # FREE_FEATURES so they must never appear as "would unlock" copy.
    diff = ent._oss_free().upgrade_diff(ent.TIER_CLOUD_PRO)
    assert set(diff["added_features"]).isdisjoint(ent.FREE_FEATURES)


# ── module-level convenience function ──────────────────────────────────────


def test_module_level_helper_matches_method(ent):
    # The bare module-level helper resolves the current entitlement and
    # delegates, so it must agree with the bound method on the same target.
    target = ent.TIER_CLOUD_PRO
    assert ent.upgrade_diff(target) == ent.get_entitlement().upgrade_diff(target)


def test_module_level_helper_never_raises(monkeypatch, ent):
    # If get_entitlement somehow raises, the helper must swallow and return
    # the empty-list shape rather than crash a dashboard render.
    def boom(*_, **__):
        raise RuntimeError("synthetic")

    monkeypatch.setattr(ent, "get_entitlement", boom)
    out = ent.upgrade_diff(ent.TIER_CLOUD_PRO)
    assert out["target"] == ent.TIER_CLOUD_PRO
    assert out["added_features"] == []
    assert out["added_runtimes"] == []


# ── API surface ────────────────────────────────────────────────────────────


def test_api_returns_diff_for_starter(client, ent):
    rv = client.get(f"/api/entitlement/upgrade-diff?target={ent.TIER_CLOUD_STARTER}")
    assert rv.status_code == 200
    body = rv.get_json()
    assert body["target"] == ent.TIER_CLOUD_STARTER
    assert set(body["added_features"]) == set(ent.STARTER_FEATURES)
    assert set(body["added_runtimes"]) == set(ent.PAID_RUNTIMES)


def test_api_empty_target_returns_empty_lists_200(client):
    rv = client.get("/api/entitlement/upgrade-diff")
    assert rv.status_code == 200
    body = rv.get_json()
    assert body["target"] == ""
    assert body["added_features"] == []
    assert body["added_runtimes"] == []


def test_api_unknown_target_returns_empty_lists_200(client):
    rv = client.get("/api/entitlement/upgrade-diff?target=nonsense_tier_xyz")
    assert rv.status_code == 200
    body = rv.get_json()
    assert body["target"] == "nonsense_tier_xyz"
    assert body["added_features"] == []
    assert body["added_runtimes"] == []
