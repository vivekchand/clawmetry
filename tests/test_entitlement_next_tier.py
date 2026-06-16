"""Tests for ``Entitlement.next_purchasable_tier()`` + the module-level helper.

The dashboard's primary "Upgrade to ___" CTA button needs a single, canonical
"what's the next tier above this install?" lookup so the JS doesn't re-derive
the ladder. These tests pin the table per-tier so a future ladder shuffle
breaks loudly here instead of silently in the UI.
"""
from __future__ import annotations

import importlib
from dataclasses import replace

import pytest
from flask import Flask


@pytest.fixture
def ent(monkeypatch, tmp_path):
    # Grace mode by default -- next_purchasable_tier is grace-independent so
    # this matches every other entitlement test in the suite.
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


# ── per-tier table ──────────────────────────────────────────────────────────


def test_oss_upgrades_to_cloud_starter(ent):
    e = ent._build(ent.TIER_OSS, "oss")
    assert e.next_purchasable_tier() == ent.TIER_CLOUD_STARTER


def test_cloud_free_upgrades_to_cloud_starter(ent):
    e = ent._build(ent.TIER_CLOUD_FREE, "cloud")
    assert e.next_purchasable_tier() == ent.TIER_CLOUD_STARTER


def test_cloud_starter_upgrades_to_cloud_pro(ent):
    e = ent._build(ent.TIER_CLOUD_STARTER, "cloud")
    assert e.next_purchasable_tier() == ent.TIER_CLOUD_PRO


def test_cloud_pro_upgrades_to_enterprise(ent):
    e = ent._build(ent.TIER_CLOUD_PRO, "cloud")
    assert e.next_purchasable_tier() == ent.TIER_ENTERPRISE


def test_self_hosted_pro_upgrades_to_enterprise(ent):
    e = ent._build(ent.TIER_PRO, "license")
    assert e.next_purchasable_tier() == ent.TIER_ENTERPRISE


def test_trial_upgrades_to_enterprise(ent):
    # Trial shares rank 2 with cloud_pro/self-hosted pro, so the next strictly
    # higher purchasable tier is enterprise (rank 3).
    e = ent._build(ent.TIER_TRIAL, "cloud")
    assert e.next_purchasable_tier() == ent.TIER_ENTERPRISE


def test_enterprise_has_no_next_tier(ent):
    e = ent._build(ent.TIER_ENTERPRISE, "license")
    assert e.next_purchasable_tier() is None


# ── safety / fallback ───────────────────────────────────────────────────────


def test_unknown_tier_falls_through_to_cloud_starter(ent):
    # A misconfigured plan with an unknown tier id should still drive the
    # operator at the bottom rung of the upgrade ladder rather than render
    # no CTA at all.
    e = replace(ent._oss_free(), tier="nonsense_tier_xyz")
    assert e.next_purchasable_tier() == ent.TIER_CLOUD_STARTER


def test_returned_tier_is_always_purchasable(ent):
    # Trial is intentionally excluded from the purchasable ladder; assert that
    # no tier ever returns trial as its "next" target.
    for tier in (
        ent.TIER_OSS,
        ent.TIER_CLOUD_FREE,
        ent.TIER_TRIAL,
        ent.TIER_CLOUD_STARTER,
        ent.TIER_CLOUD_PRO,
        ent.TIER_PRO,
        ent.TIER_ENTERPRISE,
    ):
        e = ent._build(tier, "test")
        nxt = e.next_purchasable_tier()
        assert nxt != ent.TIER_TRIAL, f"{tier} should not advertise trial as next"


def test_next_tier_rank_is_strictly_higher(ent):
    # For every non-enterprise tier the returned next-tier must out-rank the
    # current one. Pins the strict-greater invariant against accidental
    # off-by-one regressions in _PURCHASABLE_TIERS ordering.
    for tier in (
        ent.TIER_OSS,
        ent.TIER_CLOUD_FREE,
        ent.TIER_CLOUD_STARTER,
        ent.TIER_CLOUD_PRO,
        ent.TIER_PRO,
    ):
        e = ent._build(tier, "test")
        nxt = e.next_purchasable_tier()
        assert nxt is not None
        assert ent.tier_rank(nxt) > ent.tier_rank(tier)


# ── module-level convenience function ───────────────────────────────────────


def test_module_level_helper_matches_method(ent):
    # The bare module-level helper resolves the current entitlement and
    # delegates, so it must agree with the bound method.
    assert ent.next_purchasable_tier() == ent.get_entitlement().next_purchasable_tier()


def test_module_level_helper_never_raises(monkeypatch, ent):
    # If get_entitlement somehow raises, the module-level helper must swallow
    # and return None rather than crash the dashboard CTA render.
    def boom(*_, **__):
        raise RuntimeError("synthetic")

    monkeypatch.setattr(ent, "get_entitlement", boom)
    assert ent.next_purchasable_tier() is None


# ── to_dict / API surface ───────────────────────────────────────────────────


def test_to_dict_includes_next_tier_and_label(ent):
    payload = ent._oss_free().to_dict()
    assert payload["next_tier"] == ent.TIER_CLOUD_STARTER
    assert payload["next_tier_label"] == ent.tier_label(ent.TIER_CLOUD_STARTER)


def test_to_dict_omits_next_for_enterprise(ent):
    payload = ent._build(ent.TIER_ENTERPRISE, "license").to_dict()
    assert payload["next_tier"] is None
    assert payload["next_tier_label"] is None


def test_api_entitlement_surfaces_next_tier(client, ent):
    rv = client.get("/api/entitlement")
    assert rv.status_code == 200
    body = rv.get_json()
    # An OSS-default install should advertise cloud_starter as the upgrade.
    assert body["next_tier"] == ent.TIER_CLOUD_STARTER
    assert body["next_tier_label"] == ent.tier_label(ent.TIER_CLOUD_STARTER)
