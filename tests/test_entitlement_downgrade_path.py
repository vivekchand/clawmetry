"""Tests for ``clawmetry.entitlements.downgrade_path`` +
``GET /api/entitlement/downgrade-path``.

Direction-flipped sibling of :mod:`test_entitlement_upgrade_path`: pins
the per-current-tier *descending* ladder + the cumulative-loss row shape
(rather than upgrade's marginal-unlock rows) so a downgrade-warning CTA
keeps rendering when ``_PURCHASABLE_TIERS`` / ``_TIER_RANK`` /
``_TIER_FEATURES`` shift underneath it.
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


def _force_tier(monkeypatch, ent, tier: str):
    """Pin :func:`get_entitlement` to a synthetic entitlement at ``tier``.

    Each test asserts the ladder *below* a specific current tier, so we
    bypass the live resolver and hand back a deterministic Entitlement.
    """
    synthetic = ent._build(tier, source="test")

    def _stub(force: bool = False):  # noqa: ARG001
        return synthetic

    monkeypatch.setattr(ent, "get_entitlement", _stub)


# -- shape -----------------------------------------------------------------


def test_returns_list(ent):
    path = ent.downgrade_path()
    assert isinstance(path, list)


def test_each_row_has_expected_keys(monkeypatch, ent):
    _force_tier(monkeypatch, ent, ent.TIER_ENTERPRISE)
    path = ent.downgrade_path()
    assert path, "Enterprise should have rungs to descend to"
    expected_keys = {
        "target",
        "target_label",
        "target_rank",
        "current_tier",
        "current_tier_label",
        "current_tier_rank",
        "lost_features",
        "lost_runtimes",
    }
    for row in path:
        assert set(row.keys()) == expected_keys


def test_row_lost_lists_match_downgrade_diff(monkeypatch, ent):
    # Cumulative-loss rows: each row's lost_* must match the same
    # downgrade_diff(target) the caller could compute directly. If a
    # future patch quietly switches to "marginal vs previous step" this
    # trips.
    _force_tier(monkeypatch, ent, ent.TIER_ENTERPRISE)
    pinned = ent.get_entitlement()
    path = ent.downgrade_path()
    for row in path:
        diff = pinned.downgrade_diff(row["target"])
        assert row["lost_features"] == diff["lost_features"]
        assert row["lost_runtimes"] == diff["lost_runtimes"]


def test_current_tier_context_pinned_on_every_row(monkeypatch, ent):
    _force_tier(monkeypatch, ent, ent.TIER_CLOUD_PRO)
    path = ent.downgrade_path()
    for row in path:
        assert row["current_tier"] == ent.TIER_CLOUD_PRO
        assert row["current_tier_rank"] == 2
        assert row["current_tier_label"] == ent.tier_label(ent.TIER_CLOUD_PRO)


# -- per-current-tier ladder -----------------------------------------------


def test_oss_default_path_is_empty(ent):
    # Fresh fixture resolves to OSS (rank 0) -- nothing below to descend to.
    assert ent.downgrade_path() == []


def test_cloud_free_path_is_empty(monkeypatch, ent):
    # Cloud Free shares rank 0 with OSS -- also has no rung below.
    _force_tier(monkeypatch, ent, ent.TIER_CLOUD_FREE)
    assert ent.downgrade_path() == []


def test_starter_path_is_rank0_floor(monkeypatch, ent):
    _force_tier(monkeypatch, ent, ent.TIER_CLOUD_STARTER)
    tiers = [row["target"] for row in ent.downgrade_path()]
    assert tiers == [ent.TIER_CLOUD_FREE, ent.TIER_OSS]


def test_cloud_pro_path_drops_starter_then_floor(monkeypatch, ent):
    _force_tier(monkeypatch, ent, ent.TIER_CLOUD_PRO)
    tiers = [row["target"] for row in ent.downgrade_path()]
    assert tiers == [
        ent.TIER_CLOUD_STARTER,  # rank 1
        ent.TIER_CLOUD_FREE,      # rank 0 (sorted by id, cloud_free < oss)
        ent.TIER_OSS,             # rank 0
    ]


def test_self_hosted_pro_path_mirrors_cloud_pro(monkeypatch, ent):
    # Pro is rank 2, same as Cloud Pro -- same descending ladder. Cloud Pro
    # (the sibling at rank 2) is *not* included since rank must be
    # strictly less than current_rank.
    _force_tier(monkeypatch, ent, ent.TIER_PRO)
    tiers = [row["target"] for row in ent.downgrade_path()]
    assert tiers == [
        ent.TIER_CLOUD_STARTER,
        ent.TIER_CLOUD_FREE,
        ent.TIER_OSS,
    ]


def test_enterprise_path_is_full_lower_ladder(monkeypatch, ent):
    _force_tier(monkeypatch, ent, ent.TIER_ENTERPRISE)
    tiers = [row["target"] for row in ent.downgrade_path()]
    assert tiers == [
        ent.TIER_CLOUD_PRO,       # rank 2 (sorted by id, cloud_pro < pro)
        ent.TIER_PRO,             # rank 2
        ent.TIER_CLOUD_STARTER,   # rank 1
        ent.TIER_CLOUD_FREE,      # rank 0
        ent.TIER_OSS,             # rank 0
    ]


# -- cumulative-loss semantics ---------------------------------------------


def test_lost_lists_grow_as_path_descends(monkeypatch, ent):
    # Cumulative loss strictly grows (or stays equal across same-rank
    # siblings) as the destination drops further from current.
    _force_tier(monkeypatch, ent, ent.TIER_ENTERPRISE)
    path = ent.downgrade_path()
    prev_feats: set = set()
    prev_runtimes: set = set()
    for row in path:
        this_feats = set(row["lost_features"])
        this_runtimes = set(row["lost_runtimes"])
        assert prev_feats.issubset(this_feats)
        assert prev_runtimes.issubset(this_runtimes)
        prev_feats = this_feats
        prev_runtimes = this_runtimes


def test_floor_row_loses_every_paid_runtime(monkeypatch, ent):
    # The bottom rung (rank 0) sees every paid runtime in lost_runtimes
    # when current sits at a paid-runtime-bearing tier.
    _force_tier(monkeypatch, ent, ent.TIER_ENTERPRISE)
    path = ent.downgrade_path()
    floor = path[-1]
    assert floor["target_rank"] == 0
    assert set(floor["lost_runtimes"]) == set(ent.PAID_RUNTIMES)


def test_same_rank_siblings_have_identical_loss(monkeypatch, ent):
    # cloud_pro and pro both at rank 2 -- dropping from Enterprise to
    # either should lose the same cumulative set.
    _force_tier(monkeypatch, ent, ent.TIER_ENTERPRISE)
    path = ent.downgrade_path()
    by_target = {row["target"]: row for row in path}
    cp = by_target[ent.TIER_CLOUD_PRO]
    pro = by_target[ent.TIER_PRO]
    assert cp["lost_features"] == pro["lost_features"]
    assert cp["lost_runtimes"] == pro["lost_runtimes"]


# -- ordering / stability --------------------------------------------------


def test_ordered_by_rank_desc_then_tier_id(monkeypatch, ent):
    _force_tier(monkeypatch, ent, ent.TIER_ENTERPRISE)
    path = ent.downgrade_path()
    ranks = [row["target_rank"] for row in path]
    assert ranks == sorted(ranks, reverse=True)
    # Same-rank cluster (rank 2): cloud_pro < pro lexicographically.
    rank2 = [row["target"] for row in path if row["target_rank"] == 2]
    assert rank2 == sorted(rank2)
    # Same-rank cluster (rank 0): cloud_free < oss lexicographically.
    rank0 = [row["target"] for row in path if row["target_rank"] == 0]
    assert rank0 == sorted(rank0)


def test_stable_across_calls(monkeypatch, ent):
    _force_tier(monkeypatch, ent, ent.TIER_ENTERPRISE)
    a = ent.downgrade_path()
    b = ent.downgrade_path()
    c = ent.downgrade_path()
    assert a == b == c


def test_trial_never_in_path(monkeypatch, ent):
    # Trial is a promotional grant, not purchasable -- must never appear
    # as a downgrade destination. Mirrors upgrade_path's posture.
    _force_tier(monkeypatch, ent, ent.TIER_ENTERPRISE)
    ids = {row["target"] for row in ent.downgrade_path()}
    assert ent.TIER_TRIAL not in ids


# -- safety ----------------------------------------------------------------


def test_never_raises(monkeypatch, ent):
    def boom(*_, **__):
        raise RuntimeError("synthetic")

    monkeypatch.setattr(ent, "get_entitlement", boom)
    assert ent.downgrade_path() == []


def test_does_not_mutate_live_entitlement(monkeypatch, ent):
    _force_tier(monkeypatch, ent, ent.TIER_ENTERPRISE)
    live_before = ent.get_entitlement().to_dict()
    ent.downgrade_path()
    live_after = ent.get_entitlement().to_dict()
    assert live_before == live_after


# -- API surface -----------------------------------------------------------


def test_api_envelope_shape(client):
    rv = client.get("/api/entitlement/downgrade-path")
    assert rv.status_code == 200
    body = rv.get_json()
    assert set(body.keys()) == {
        "path",
        "current_tier",
        "current_tier_rank",
        "grace",
        "enforced",
    }


def test_api_oss_default_path_is_empty(client, ent):
    rv = client.get("/api/entitlement/downgrade-path")
    body = rv.get_json()
    assert body["current_tier"] == ent.TIER_OSS
    assert body["current_tier_rank"] == 0
    assert body["path"] == []


def test_api_enterprise_path_is_full_lower_ladder(client, ent, monkeypatch):
    _force_tier(monkeypatch, ent, ent.TIER_ENTERPRISE)
    rv = client.get("/api/entitlement/downgrade-path")
    body = rv.get_json()
    assert body["current_tier"] == ent.TIER_ENTERPRISE
    targets = [row["target"] for row in body["path"]]
    assert targets == [
        ent.TIER_CLOUD_PRO,
        ent.TIER_PRO,
        ent.TIER_CLOUD_STARTER,
        ent.TIER_CLOUD_FREE,
        ent.TIER_OSS,
    ]


def test_api_row_lost_lists_match_module_path(client, ent, monkeypatch):
    # API row equality with the module helper -- the route is a pure pass-
    # through, not a re-derivation. A future divergence (extra fields, sort
    # change) trips here before reaching the UI.
    _force_tier(monkeypatch, ent, ent.TIER_ENTERPRISE)
    rv = client.get("/api/entitlement/downgrade-path")
    body = rv.get_json()
    assert body["path"] == ent.downgrade_path()


def test_api_never_5xxs_on_resolver_failure(client, ent, monkeypatch):
    def boom(*_, **__):
        raise RuntimeError("synthetic")

    monkeypatch.setattr(ent, "get_entitlement", boom)
    rv = client.get("/api/entitlement/downgrade-path")
    assert rv.status_code == 200
    body = rv.get_json()
    assert body["path"] == []
    assert body["current_tier"] == ent.TIER_OSS
    assert body["grace"] is True
    assert body["enforced"] is False
