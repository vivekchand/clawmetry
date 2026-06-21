"""Tests for ``clawmetry.entitlements.tier_unlocks`` +
``GET /api/entitlement/tier-unlocks``.

Where :func:`preview` answers "what would the resulting Entitlement *look
like*" at a target tier (cumulative grant), :func:`tier_unlocks` answers
"what does this tier *first* unlock vs the tier below it" (marginal
grant) -- the "what's new in Pro vs Starter" view a pricing-page row or
upgrade-CTA card uses. These tests pin the marginal sets per tier so a
future reshuffle of ``_TIER_FEATURES`` / ``_TIER_PAID_RUNTIMES`` /
``_PURCHASABLE_TIERS`` / ``_TIER_RANK`` breaks loudly here instead of
silently in the upgrade-CTA copy.
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


# ── shape ─────────────────────────────────────────────────────────────────


def test_returns_full_shape(ent):
    body = ent.tier_unlocks(ent.TIER_CLOUD_PRO)
    assert set(body.keys()) == {
        "tier",
        "tier_label",
        "tier_rank",
        "previous_tier",
        "previous_tier_label",
        "previous_tier_rank",
        "features",
        "runtimes",
    }


def test_tier_metadata_matches_target(ent):
    body = ent.tier_unlocks(ent.TIER_CLOUD_PRO)
    assert body["tier"] == ent.TIER_CLOUD_PRO
    assert body["tier_label"] == ent.tier_label(ent.TIER_CLOUD_PRO)
    assert body["tier_rank"] == ent.tier_rank(ent.TIER_CLOUD_PRO)


def test_lists_are_sorted(ent):
    body = ent.tier_unlocks(ent.TIER_CLOUD_STARTER)
    assert body["features"] == sorted(body["features"])
    assert body["runtimes"] == sorted(body["runtimes"])


# ── per-tier marginals ────────────────────────────────────────────────────


def test_oss_has_no_previous_tier(ent):
    # OSS sits at rank 0 -- no purchasable tier is "below" it, so the
    # marginal collapses to the full free grant.
    body = ent.tier_unlocks(ent.TIER_OSS)
    assert body["previous_tier"] is None
    assert body["previous_tier_label"] is None
    assert body["previous_tier_rank"] is None
    assert set(body["features"]) == set(ent.FREE_FEATURES)
    assert set(body["runtimes"]) == set(ent.FREE_RUNTIMES)


def test_cloud_free_floor_collapses_to_free_grant(ent):
    # Cloud Free is also rank 0 -- same floor as OSS, so previous=None and
    # the marginal is the full free grant. This is the trip-wire if the
    # rank table ever drifts.
    body = ent.tier_unlocks(ent.TIER_CLOUD_FREE)
    assert body["previous_tier"] is None
    assert set(body["features"]) == set(ent.FREE_FEATURES)
    assert set(body["runtimes"]) == set(ent.FREE_RUNTIMES)


def test_starter_unlocks_paid_runtimes_and_starter_features(ent):
    body = ent.tier_unlocks(ent.TIER_CLOUD_STARTER)
    # Previous purchasable below Starter (rank 1) is OSS (rank 0).
    assert body["previous_tier"] == ent.TIER_OSS
    assert set(body["features"]) == set(ent.STARTER_FEATURES)
    # Every paid runtime first becomes available at Starter.
    assert set(body["runtimes"]) == set(ent.PAID_RUNTIMES)


def test_pro_unlocks_pro_only_features_no_new_runtimes(ent):
    body = ent.tier_unlocks(ent.TIER_CLOUD_PRO)
    # Previous purchasable below Pro (rank 2) is Starter (rank 1).
    assert body["previous_tier"] == ent.TIER_CLOUD_STARTER
    assert set(body["features"]) == set(ent.PRO_ONLY_FEATURES)
    # All paid runtimes already unlocked at Starter -- no marginal here.
    assert body["runtimes"] == []


def test_self_hosted_pro_mirrors_cloud_pro(ent):
    # TIER_PRO and TIER_CLOUD_PRO share rank 2 and grant set -- same
    # marginal vs the tier below.
    body = ent.tier_unlocks(ent.TIER_PRO)
    assert body["previous_tier"] == ent.TIER_CLOUD_STARTER
    assert set(body["features"]) == set(ent.PRO_ONLY_FEATURES)
    assert body["runtimes"] == []


def test_enterprise_unlocks_enterprise_features(ent):
    body = ent.tier_unlocks(ent.TIER_ENTERPRISE)
    # Previous purchasable below Enterprise (rank 3) is Cloud Pro (rank 2)
    # -- the first rank-2 entry in _PURCHASABLE_TIERS.
    assert body["previous_tier"] == ent.TIER_CLOUD_PRO
    assert set(body["features"]) == set(ent.ENTERPRISE_FEATURES)
    assert body["runtimes"] == []


# ── trial / unknown / safety ──────────────────────────────────────────────


def test_trial_returns_none(ent):
    # Trial is a promotional grant, not a purchasable plan -- callers must
    # not route an upgrade-CTA to it. Mirrors preview()'s posture (which
    # also rejects non-purchasable tiers).
    assert ent.tier_unlocks(ent.TIER_TRIAL) is None


def test_unknown_tier_returns_none(ent):
    assert ent.tier_unlocks("nonsense_tier_xyz") is None


def test_empty_returns_none(ent):
    assert ent.tier_unlocks("") is None
    assert ent.tier_unlocks(None) is None  # type: ignore[arg-type]


def test_lowercases_input(ent):
    body = ent.tier_unlocks("CLOUD_PRO")
    assert body is not None
    assert body["tier"] == ent.TIER_CLOUD_PRO


def test_never_raises(monkeypatch, ent):
    def boom(*_, **__):
        raise RuntimeError("synthetic")

    monkeypatch.setattr(ent, "tier_label", boom)
    assert ent.tier_unlocks(ent.TIER_CLOUD_PRO) is None


def test_does_not_mutate_live_entitlement(ent):
    live_before = ent.get_entitlement().to_dict()
    ent.tier_unlocks(ent.TIER_ENTERPRISE)
    live_after = ent.get_entitlement().to_dict()
    assert live_before == live_after


# ── round-trip vs catalogue ───────────────────────────────────────────────


def test_marginals_union_covers_paid_features(ent):
    # Every paid + enterprise feature must first-unlock at exactly one
    # purchasable tier so the pricing page can list them with no gaps.
    seen: set = set()
    for tier_id in (
        ent.TIER_CLOUD_STARTER,
        ent.TIER_CLOUD_PRO,
        ent.TIER_ENTERPRISE,
    ):
        seen |= set(ent.tier_unlocks(tier_id)["features"])
    assert seen == set(ent.PAID_FEATURES) | set(ent.ENTERPRISE_FEATURES)


def test_marginals_union_covers_paid_runtimes(ent):
    # Every paid runtime must first-unlock at exactly one purchasable
    # tier (Starter, today) -- same no-gap invariant.
    seen: set = set()
    for tier_id in (
        ent.TIER_CLOUD_STARTER,
        ent.TIER_CLOUD_PRO,
        ent.TIER_ENTERPRISE,
    ):
        seen |= set(ent.tier_unlocks(tier_id)["runtimes"])
    assert seen == set(ent.PAID_RUNTIMES)


def test_marginal_features_disjoint_across_tiers(ent):
    # A feature must first-unlock at exactly *one* tier -- if it shows up
    # in two marginal sets the pricing page double-lists it.
    starter = set(ent.tier_unlocks(ent.TIER_CLOUD_STARTER)["features"])
    pro = set(ent.tier_unlocks(ent.TIER_CLOUD_PRO)["features"])
    enterprise = set(ent.tier_unlocks(ent.TIER_ENTERPRISE)["features"])
    assert starter.isdisjoint(pro)
    assert starter.isdisjoint(enterprise)
    assert pro.isdisjoint(enterprise)


# ── API surface ───────────────────────────────────────────────────────────


def test_api_returns_marginal_for_pro(client, ent):
    rv = client.get(f"/api/entitlement/tier-unlocks?tier={ent.TIER_CLOUD_PRO}")
    assert rv.status_code == 200
    body = rv.get_json()
    assert body["tier"] == ent.TIER_CLOUD_PRO
    assert body["previous_tier"] == ent.TIER_CLOUD_STARTER
    assert set(body["features"]) == set(ent.PRO_ONLY_FEATURES)
    assert body["runtimes"] == []


def test_api_returns_marginal_for_starter(client, ent):
    rv = client.get(f"/api/entitlement/tier-unlocks?tier={ent.TIER_CLOUD_STARTER}")
    assert rv.status_code == 200
    body = rv.get_json()
    assert body["previous_tier"] == ent.TIER_OSS
    assert set(body["runtimes"]) == set(ent.PAID_RUNTIMES)


def test_api_missing_tier_is_400(client):
    rv = client.get("/api/entitlement/tier-unlocks")
    assert rv.status_code == 400
    assert "error" in rv.get_json()


def test_api_unknown_tier_is_404(client):
    rv = client.get("/api/entitlement/tier-unlocks?tier=nonsense_tier_xyz")
    assert rv.status_code == 404
    body = rv.get_json()
    assert body["tier"] == "nonsense_tier_xyz"


def test_api_trial_is_404(client, ent):
    # Trial is not purchasable -- the upgrade-CTA must never route to it.
    rv = client.get(f"/api/entitlement/tier-unlocks?tier={ent.TIER_TRIAL}")
    assert rv.status_code == 404


def test_api_lowercases_query(client, ent):
    rv = client.get("/api/entitlement/tier-unlocks?tier=CLOUD_STARTER")
    assert rv.status_code == 200
    assert rv.get_json()["tier"] == ent.TIER_CLOUD_STARTER
