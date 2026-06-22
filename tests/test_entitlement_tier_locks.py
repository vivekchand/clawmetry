"""Tests for ``clawmetry.entitlements.tier_locks`` +
``GET /api/entitlement/tier-locks``.

Where :func:`tier_unlocks` answers "what does tier X *first* unlock vs
the tier below it" (the upgrade-step marginal grant), ``tier_locks``
answers "what does tier X *first* lose vs the tier above it" (the
downgrade-step marginal loss) -- the per-rung downgrade-warning row a
step-down CTA renders. These tests pin the marginal-loss sets per tier
+ the set-identity invariant with ``tier_unlocks`` so a future reshuffle
of ``_TIER_FEATURES`` / ``_TIER_PAID_RUNTIMES`` / ``_PURCHASABLE_TIERS``
/ ``_TIER_RANK`` breaks loudly here instead of silently in the
downgrade-warning copy.
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


# -- shape -----------------------------------------------------------------


def test_returns_full_shape(ent):
    body = ent.tier_locks(ent.TIER_CLOUD_STARTER)
    assert set(body.keys()) == {
        "tier",
        "tier_label",
        "tier_rank",
        "next_tier",
        "next_tier_label",
        "next_tier_rank",
        "lost_features",
        "lost_runtimes",
    }


def test_tier_metadata_matches_target(ent):
    body = ent.tier_locks(ent.TIER_CLOUD_STARTER)
    assert body["tier"] == ent.TIER_CLOUD_STARTER
    assert body["tier_label"] == ent.tier_label(ent.TIER_CLOUD_STARTER)
    assert body["tier_rank"] == ent.tier_rank(ent.TIER_CLOUD_STARTER)


def test_lists_are_sorted(ent):
    body = ent.tier_locks(ent.TIER_OSS)
    assert body["lost_features"] == sorted(body["lost_features"])
    assert body["lost_runtimes"] == sorted(body["lost_runtimes"])


# -- per-tier marginals ----------------------------------------------------


def test_enterprise_has_no_next_tier(ent):
    # Enterprise sits at the ceiling (rank 3) -- no purchasable tier
    # sits above, so the marginal-loss view collapses to empty lists.
    body = ent.tier_locks(ent.TIER_ENTERPRISE)
    assert body["next_tier"] is None
    assert body["next_tier_label"] is None
    assert body["next_tier_rank"] is None
    assert body["lost_features"] == []
    assert body["lost_runtimes"] == []


def test_cloud_pro_loses_enterprise_features(ent):
    # Stepping down to Cloud Pro (rank 2) from Enterprise (rank 3) drops
    # every enterprise-only feature; paid runtimes stay (Cloud Pro is
    # also a paid-runtime tier).
    body = ent.tier_locks(ent.TIER_CLOUD_PRO)
    assert body["next_tier"] == ent.TIER_ENTERPRISE
    assert set(body["lost_features"]) == set(ent.ENTERPRISE_FEATURES)
    assert body["lost_runtimes"] == []


def test_self_hosted_pro_mirrors_cloud_pro(ent):
    # TIER_PRO and TIER_CLOUD_PRO share rank 2 and grant set -- same
    # marginal-loss vs the tier above (Enterprise).
    body = ent.tier_locks(ent.TIER_PRO)
    assert body["next_tier"] == ent.TIER_ENTERPRISE
    assert set(body["lost_features"]) == set(ent.ENTERPRISE_FEATURES)
    assert body["lost_runtimes"] == []


def test_starter_loses_pro_only_features_no_paid_runtimes(ent):
    # Stepping down to Starter (rank 1) from Cloud Pro (the next rank-2
    # entry above by ``(rank, id)`` order) drops pro-only features; paid
    # runtimes stay since Starter is also a paid-runtime tier.
    body = ent.tier_locks(ent.TIER_CLOUD_STARTER)
    assert body["next_tier"] == ent.TIER_CLOUD_PRO
    assert set(body["lost_features"]) == set(ent.PRO_ONLY_FEATURES)
    assert body["lost_runtimes"] == []


def test_oss_floor_loses_starter_grant(ent):
    # Stepping down to OSS (rank 0) from Cloud Starter (rank 1) drops
    # every Starter-tier feature *and* every paid runtime.
    body = ent.tier_locks(ent.TIER_OSS)
    assert body["next_tier"] == ent.TIER_CLOUD_STARTER
    assert set(body["lost_features"]) == set(ent.STARTER_FEATURES)
    assert set(body["lost_runtimes"]) == set(ent.PAID_RUNTIMES)


def test_cloud_free_floor_mirrors_oss(ent):
    # CLOUD_FREE shares rank 0 with OSS -- same marginal-loss view vs
    # the tier above (Cloud Starter). Trip-wire for rank-table drift.
    body = ent.tier_locks(ent.TIER_CLOUD_FREE)
    assert body["next_tier"] == ent.TIER_CLOUD_STARTER
    assert set(body["lost_features"]) == set(ent.STARTER_FEATURES)
    assert set(body["lost_runtimes"]) == set(ent.PAID_RUNTIMES)


# -- set-identity vs tier_unlocks -----------------------------------------


def test_loss_at_X_equals_unlock_at_next_features(ent):
    # The marginal loss at X must byte-equal the marginal unlock at the
    # next-higher purchasable tier above X -- the two views attribute the
    # same set difference to opposite endpoints of the rung. If this
    # desyncs the downgrade-warning row will quietly disagree with the
    # upgrade-CTA row above it.
    for tid in (
        ent.TIER_OSS,
        ent.TIER_CLOUD_FREE,
        ent.TIER_CLOUD_STARTER,
        ent.TIER_CLOUD_PRO,
        ent.TIER_PRO,
    ):
        locks = ent.tier_locks(tid)
        unlocks = ent.tier_unlocks(locks["next_tier"])
        assert locks["lost_features"] == unlocks["features"]
        assert locks["lost_runtimes"] == unlocks["runtimes"]


def test_enterprise_has_no_set_identity_pair(ent):
    # Enterprise has no rung above -- the set-identity invariant is
    # vacuously empty, captured by both sides being [] / None.
    body = ent.tier_locks(ent.TIER_ENTERPRISE)
    assert body["next_tier"] is None
    assert body["lost_features"] == []
    assert body["lost_runtimes"] == []


# -- next-tier selection (same-rank siblings) -----------------------------


def test_starter_next_picks_cloud_pro_over_self_hosted_pro(ent):
    # cloud_pro and pro share rank 2. Among strictly-higher candidates,
    # selection sorts by ``(rank, id)`` and takes the first -- "cloud_pro"
    # sorts before "pro" lexicographically.
    body = ent.tier_locks(ent.TIER_CLOUD_STARTER)
    assert body["next_tier"] == ent.TIER_CLOUD_PRO


def test_trial_never_appears_as_next_tier(ent):
    # Trial is excluded from _PURCHASABLE_TIERS; it must never be picked
    # as the marginal-loss source even though its rank (2) ties with the
    # paid Pro tiers.
    seen = {ent.tier_locks(t)["next_tier"] for t in (
        ent.TIER_OSS,
        ent.TIER_CLOUD_FREE,
        ent.TIER_CLOUD_STARTER,
        ent.TIER_CLOUD_PRO,
        ent.TIER_PRO,
    )}
    assert ent.TIER_TRIAL not in seen


# -- trial / unknown / safety ---------------------------------------------


def test_trial_returns_none(ent):
    # Trial is a promotional grant, not a purchasable plan -- callers must
    # not route a downgrade-warning row to it. Mirrors ``tier_unlocks``'s
    # posture (which also rejects non-purchasable tiers).
    assert ent.tier_locks(ent.TIER_TRIAL) is None


def test_unknown_tier_returns_none(ent):
    assert ent.tier_locks("nonsense_tier_xyz") is None


def test_empty_returns_none(ent):
    assert ent.tier_locks("") is None
    assert ent.tier_locks(None) is None  # type: ignore[arg-type]


def test_lowercases_input(ent):
    body = ent.tier_locks("CLOUD_STARTER")
    assert body is not None
    assert body["tier"] == ent.TIER_CLOUD_STARTER


def test_never_raises(monkeypatch, ent):
    def boom(*_, **__):
        raise RuntimeError("synthetic")

    monkeypatch.setattr(ent, "tier_label", boom)
    assert ent.tier_locks(ent.TIER_CLOUD_STARTER) is None


def test_does_not_mutate_live_entitlement(ent):
    live_before = ent.get_entitlement().to_dict()
    ent.tier_locks(ent.TIER_OSS)
    live_after = ent.get_entitlement().to_dict()
    assert live_before == live_after


# -- round-trip vs catalogue ----------------------------------------------


def test_marginal_losses_union_covers_paid_features(ent):
    # Every paid + enterprise feature must first-lock at exactly one
    # purchasable tier so the downgrade-warning roll-up has no gaps.
    seen: set = set()
    for tid in (
        ent.TIER_OSS,
        ent.TIER_CLOUD_STARTER,
        ent.TIER_CLOUD_PRO,
    ):
        seen |= set(ent.tier_locks(tid)["lost_features"])
    assert seen == set(ent.PAID_FEATURES) | set(ent.ENTERPRISE_FEATURES)


def test_marginal_losses_union_covers_paid_runtimes(ent):
    # Every paid runtime must first-lock at exactly one purchasable tier
    # (OSS, today) -- same no-gap invariant on the downgrade direction.
    seen: set = set()
    for tid in (
        ent.TIER_OSS,
        ent.TIER_CLOUD_STARTER,
        ent.TIER_CLOUD_PRO,
    ):
        seen |= set(ent.tier_locks(tid)["lost_runtimes"])
    assert seen == set(ent.PAID_RUNTIMES)


def test_marginal_losses_disjoint_across_distinct_ranks(ent):
    # A feature must first-lock at exactly *one* rung so the
    # downgrade-warning roll-up doesn't double-list it. Same-rank
    # siblings legitimately share the same loss set (oss & cloud_free
    # at rank 0; cloud_pro & pro at rank 2), so the disjointness check
    # is across distinct ranks.
    oss = set(ent.tier_locks(ent.TIER_OSS)["lost_features"])
    starter = set(ent.tier_locks(ent.TIER_CLOUD_STARTER)["lost_features"])
    cloud_pro = set(ent.tier_locks(ent.TIER_CLOUD_PRO)["lost_features"])
    assert oss.isdisjoint(starter)
    assert oss.isdisjoint(cloud_pro)
    assert starter.isdisjoint(cloud_pro)


def test_same_rank_siblings_have_identical_loss(ent):
    # cloud_free / oss (rank 0) and cloud_pro / pro (rank 2) both produce
    # identical loss rows -- same next_tier, same lost_* lists.
    a = ent.tier_locks(ent.TIER_OSS)
    b = ent.tier_locks(ent.TIER_CLOUD_FREE)
    assert a["next_tier"] == b["next_tier"]
    assert a["lost_features"] == b["lost_features"]
    assert a["lost_runtimes"] == b["lost_runtimes"]
    c = ent.tier_locks(ent.TIER_CLOUD_PRO)
    d = ent.tier_locks(ent.TIER_PRO)
    assert c["next_tier"] == d["next_tier"]
    assert c["lost_features"] == d["lost_features"]
    assert c["lost_runtimes"] == d["lost_runtimes"]


# -- API surface ----------------------------------------------------------


def test_api_returns_marginal_for_starter(client, ent):
    rv = client.get(f"/api/entitlement/tier-locks?tier={ent.TIER_CLOUD_STARTER}")
    assert rv.status_code == 200
    body = rv.get_json()
    assert body["tier"] == ent.TIER_CLOUD_STARTER
    assert body["next_tier"] == ent.TIER_CLOUD_PRO
    assert set(body["lost_features"]) == set(ent.PRO_ONLY_FEATURES)
    assert body["lost_runtimes"] == []


def test_api_returns_marginal_for_oss(client, ent):
    rv = client.get(f"/api/entitlement/tier-locks?tier={ent.TIER_OSS}")
    assert rv.status_code == 200
    body = rv.get_json()
    assert body["next_tier"] == ent.TIER_CLOUD_STARTER
    assert set(body["lost_runtimes"]) == set(ent.PAID_RUNTIMES)


def test_api_enterprise_is_200_with_empty_loss(client, ent):
    # Enterprise is a valid purchasable tier -- the marginal collapses
    # to empty lists, not a 404.
    rv = client.get(f"/api/entitlement/tier-locks?tier={ent.TIER_ENTERPRISE}")
    assert rv.status_code == 200
    body = rv.get_json()
    assert body["next_tier"] is None
    assert body["lost_features"] == []
    assert body["lost_runtimes"] == []


def test_api_missing_tier_is_400(client):
    rv = client.get("/api/entitlement/tier-locks")
    assert rv.status_code == 400
    assert "error" in rv.get_json()


def test_api_unknown_tier_is_404(client):
    rv = client.get("/api/entitlement/tier-locks?tier=nonsense_tier_xyz")
    assert rv.status_code == 404
    body = rv.get_json()
    assert body["tier"] == "nonsense_tier_xyz"


def test_api_trial_is_404(client, ent):
    # Trial is not purchasable -- the downgrade-CTA must never route to it.
    rv = client.get(f"/api/entitlement/tier-locks?tier={ent.TIER_TRIAL}")
    assert rv.status_code == 404


def test_api_lowercases_query(client, ent):
    rv = client.get("/api/entitlement/tier-locks?tier=CLOUD_STARTER")
    assert rv.status_code == 200
    assert rv.get_json()["tier"] == ent.TIER_CLOUD_STARTER


def test_api_row_parity_with_tier_unlocks_at_next(client, ent):
    # The HTTP-level set-identity check: the locks payload at X carries
    # the same loss lists as the unlocks payload at next_tier(X) carries
    # for features/runtimes. Routes shouldn't diverge from the helper.
    rv = client.get(f"/api/entitlement/tier-locks?tier={ent.TIER_CLOUD_STARTER}")
    locks = rv.get_json()
    rv2 = client.get(
        f"/api/entitlement/tier-unlocks?tier={locks['next_tier']}",
    )
    unlocks = rv2.get_json()
    assert locks["lost_features"] == unlocks["features"]
    assert locks["lost_runtimes"] == unlocks["runtimes"]
