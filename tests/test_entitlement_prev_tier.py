"""Tests for ``Entitlement.previous_purchasable_tier()`` + the module-level
helper.

The dashboard's cancellation / "Downgrade to ___" CTA needs a single,
canonical "what's the next tier *below* this install?" lookup so the JS
doesn't re-derive the ladder. This is the symmetric counterpart of
``next_purchasable_tier`` and these tests pin the table per-tier so a future
ladder shuffle breaks loudly here instead of silently in the UI.
"""
from __future__ import annotations

import importlib
from dataclasses import replace

import pytest
from flask import Flask


@pytest.fixture
def ent(monkeypatch, tmp_path):
    # Grace mode by default -- previous_purchasable_tier is grace-independent
    # so this matches every other entitlement test in the suite.
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


def test_oss_has_no_previous_tier(ent):
    e = ent._build(ent.TIER_OSS, "oss")
    assert e.previous_purchasable_tier() is None


def test_cloud_free_has_no_previous_tier(ent):
    e = ent._build(ent.TIER_CLOUD_FREE, "cloud")
    assert e.previous_purchasable_tier() is None


def test_cloud_starter_downgrades_to_cloud_free(ent):
    # Cloud-sourced Starter cancels into cloud_free -- the account is
    # preserved, only the paid features are removed.
    e = ent._build(ent.TIER_CLOUD_STARTER, "cloud")
    assert e.previous_purchasable_tier() == ent.TIER_CLOUD_FREE


def test_license_starter_downgrades_to_oss(ent):
    # A license/self-hosted entitlement at rank 1 collapses to the OSS floor,
    # not cloud_free -- there is no cloud account to preserve.
    e = ent._build(ent.TIER_CLOUD_STARTER, "license")
    assert e.previous_purchasable_tier() == ent.TIER_OSS


def test_cloud_pro_downgrades_to_cloud_starter(ent):
    e = ent._build(ent.TIER_CLOUD_PRO, "cloud")
    assert e.previous_purchasable_tier() == ent.TIER_CLOUD_STARTER


def test_self_hosted_pro_downgrades_to_cloud_starter(ent):
    e = ent._build(ent.TIER_PRO, "license")
    assert e.previous_purchasable_tier() == ent.TIER_CLOUD_STARTER


def test_trial_downgrades_to_cloud_starter(ent):
    # Trial shares rank 2 with cloud_pro/self-hosted pro; the next strictly
    # lower purchasable tier is cloud_starter (rank 1).
    e = ent._build(ent.TIER_TRIAL, "cloud")
    assert e.previous_purchasable_tier() == ent.TIER_CLOUD_STARTER


def test_cloud_enterprise_downgrades_to_cloud_pro(ent):
    # Cloud-sourced Enterprise steps into cloud_pro -- the cloud-sibling at
    # rank 2.
    e = ent._build(ent.TIER_ENTERPRISE, "cloud")
    assert e.previous_purchasable_tier() == ent.TIER_CLOUD_PRO


def test_license_enterprise_downgrades_to_self_hosted_pro(ent):
    # License-sourced Enterprise (self-hosted) steps into self-hosted pro,
    # not cloud_pro -- the customer is not in the cloud world.
    e = ent._build(ent.TIER_ENTERPRISE, "license")
    assert e.previous_purchasable_tier() == ent.TIER_PRO


# ── safety / fallback ───────────────────────────────────────────────────────


def test_unknown_tier_clamps_to_floor(ent):
    # A misconfigured plan with an unknown tier id should report "already at
    # the floor" (None) -- unknown tier clamps to rank 0, so there is no lower
    # purchasable rung to advertise.
    e = replace(ent._oss_free(), tier="nonsense_tier_xyz")
    assert e.previous_purchasable_tier() is None


def test_returned_tier_is_always_purchasable(ent):
    # Trial is intentionally excluded from the purchasable ladder; assert that
    # no tier ever returns trial as its "previous" target.
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
        prev = e.previous_purchasable_tier()
        assert prev != ent.TIER_TRIAL, f"{tier} should not advertise trial as previous"


def test_prev_tier_rank_is_strictly_lower(ent):
    # For every non-floor tier the returned prev-tier must be strictly lower
    # than the current one. Pins the strict-less invariant against accidental
    # off-by-one regressions in _PURCHASABLE_TIERS ordering.
    for tier in (
        ent.TIER_CLOUD_STARTER,
        ent.TIER_TRIAL,
        ent.TIER_CLOUD_PRO,
        ent.TIER_PRO,
        ent.TIER_ENTERPRISE,
    ):
        e = ent._build(tier, "test")
        prev = e.previous_purchasable_tier()
        assert prev is not None
        assert ent.tier_rank(prev) < ent.tier_rank(tier)


def test_prev_is_inverse_of_next_in_round_trip(ent):
    # Symmetry sanity: stepping up via next_purchasable_tier and then back
    # down via previous_purchasable_tier should never advance the rank --
    # i.e. the down-step must reach the original rank or a rank below it,
    # never above it. (Strict equality would over-pin since starter/pro have
    # the cluster of rank-2 tiers sharing one slot in the diff matrix.)
    for tier in (
        ent.TIER_OSS,
        ent.TIER_CLOUD_STARTER,
        ent.TIER_CLOUD_PRO,
    ):
        e = ent._build(tier, "test")
        nxt = e.next_purchasable_tier()
        if nxt is None:
            continue
        stepped_up = ent._build(nxt, "test")
        back = stepped_up.previous_purchasable_tier()
        assert back is not None
        assert ent.tier_rank(back) <= ent.tier_rank(tier)


# ── module-level convenience function ───────────────────────────────────────


def test_module_level_helper_matches_method(ent):
    assert (
        ent.previous_purchasable_tier()
        == ent.get_entitlement().previous_purchasable_tier()
    )


def test_module_level_helper_never_raises(monkeypatch, ent):
    def boom(*_, **__):
        raise RuntimeError("synthetic")

    monkeypatch.setattr(ent, "get_entitlement", boom)
    assert ent.previous_purchasable_tier() is None


# ── to_dict / API surface ───────────────────────────────────────────────────


def test_to_dict_omits_prev_for_oss_floor(ent):
    payload = ent._oss_free().to_dict()
    assert payload["prev_tier"] is None
    assert payload["prev_tier_label"] is None


def test_to_dict_includes_prev_for_cloud_starter(ent):
    # Cloud-sourced Starter advertises cloud_free as its cancellation floor.
    payload = ent._build(ent.TIER_CLOUD_STARTER, "cloud").to_dict()
    assert payload["prev_tier"] == ent.TIER_CLOUD_FREE
    assert payload["prev_tier_label"] == ent.tier_label(ent.TIER_CLOUD_FREE)


def test_to_dict_includes_prev_for_license_enterprise(ent):
    # License-sourced Enterprise advertises self-hosted pro as its
    # cancellation step-down.
    payload = ent._build(ent.TIER_ENTERPRISE, "license").to_dict()
    assert payload["prev_tier"] == ent.TIER_PRO
    assert payload["prev_tier_label"] == ent.tier_label(ent.TIER_PRO)


def test_api_entitlement_surfaces_prev_tier(client, ent):
    # An OSS-default install is already at the floor, so prev_tier is None.
    rv = client.get("/api/entitlement")
    assert rv.status_code == 200
    body = rv.get_json()
    assert "prev_tier" in body
    assert "prev_tier_label" in body
    assert body["prev_tier"] is None
    assert body["prev_tier_label"] is None
