"""Tests for ``clawmetry.entitlements.upgrade_path`` +
``GET /api/entitlement/upgrade-path``.

Where :func:`tier_unlocks` answers "what does tier X unlock vs the tier
below it" for one named tier, ``upgrade_path`` answers the
current-user-relative question: "which purchasable tiers are still
*above* me, in order, and what does each one first unlock as I climb".
These tests pin the per-current-tier ladder + per-row marginal shape so
a future reshuffle of ``_PURCHASABLE_TIERS`` / ``_TIER_RANK`` /
``_TIER_FEATURES`` breaks loudly here instead of silently in an
upgrade-CTA wizard.
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

    Each test asserts the ladder *above* a specific current tier, so we
    bypass the live resolver and hand back a deterministic Entitlement.
    """
    synthetic = ent._build(tier, source="test")

    def _stub(force: bool = False):  # noqa: ARG001
        return synthetic

    monkeypatch.setattr(ent, "get_entitlement", _stub)


# -- shape -----------------------------------------------------------------


def test_returns_list(ent):
    path = ent.upgrade_path()
    assert isinstance(path, list)


def test_each_row_matches_tier_unlocks_shape(ent):
    path = ent.upgrade_path()
    expected_keys = {
        "tier",
        "tier_label",
        "tier_rank",
        "previous_tier",
        "previous_tier_label",
        "previous_tier_rank",
        "features",
        "runtimes",
    }
    for row in path:
        assert set(row.keys()) == expected_keys


def test_rows_byte_equal_to_singular_tier_unlocks(ent):
    # Row equality with the singular endpoint -- the batch is a pure
    # plural sibling, not a divergent path. If a future patch tries to
    # compute "marginal vs previous step in the path" this trips.
    path = ent.upgrade_path()
    for row in path:
        assert row == ent.tier_unlocks(row["tier"])


# -- per-current-tier ladder -----------------------------------------------


def test_oss_default_path_is_full_upper_ladder(ent):
    # Fresh fixture resolves to OSS (rank 0) -- path covers everything above.
    path = ent.upgrade_path()
    tiers = [row["tier"] for row in path]
    assert tiers == [
        ent.TIER_CLOUD_STARTER,  # rank 1
        ent.TIER_CLOUD_PRO,       # rank 2 (sorted by id, cloud_pro < pro)
        ent.TIER_PRO,             # rank 2
        ent.TIER_ENTERPRISE,      # rank 3
    ]


def test_floor_includes_both_rank0_siblings_excluded(ent):
    # OSS and CLOUD_FREE are both rank 0 -- neither should appear in the
    # path when current is OSS (or CLOUD_FREE), since rank must be
    # *strictly greater* than current_rank.
    path = ent.upgrade_path()
    ids = {row["tier"] for row in path}
    assert ent.TIER_OSS not in ids
    assert ent.TIER_CLOUD_FREE not in ids


def test_starter_path_drops_starter_and_below(monkeypatch, ent):
    _force_tier(monkeypatch, ent, ent.TIER_CLOUD_STARTER)
    path = ent.upgrade_path()
    tiers = [row["tier"] for row in path]
    assert tiers == [
        ent.TIER_CLOUD_PRO,
        ent.TIER_PRO,
        ent.TIER_ENTERPRISE,
    ]


def test_cloud_pro_path_is_enterprise_only(monkeypatch, ent):
    # Cloud Pro is rank 2 -- only Enterprise (rank 3) sits above.
    # Self-hosted Pro (rank 2) is the same rank, so it's excluded.
    _force_tier(monkeypatch, ent, ent.TIER_CLOUD_PRO)
    path = ent.upgrade_path()
    assert [row["tier"] for row in path] == [ent.TIER_ENTERPRISE]


def test_self_hosted_pro_path_mirrors_cloud_pro(monkeypatch, ent):
    _force_tier(monkeypatch, ent, ent.TIER_PRO)
    path = ent.upgrade_path()
    assert [row["tier"] for row in path] == [ent.TIER_ENTERPRISE]


def test_enterprise_path_is_empty(monkeypatch, ent):
    _force_tier(monkeypatch, ent, ent.TIER_ENTERPRISE)
    assert ent.upgrade_path() == []


def test_cloud_free_path_matches_oss_path(monkeypatch, ent):
    # CLOUD_FREE shares rank 0 with OSS -- same ladder above.
    _force_tier(monkeypatch, ent, ent.TIER_CLOUD_FREE)
    cloud_free_tiers = [row["tier"] for row in ent.upgrade_path()]
    # Reset and check OSS default.
    ent.invalidate()
    oss_tiers = [row["tier"] for row in ent.upgrade_path()]
    assert cloud_free_tiers == oss_tiers


# -- ordering / stability --------------------------------------------------


def test_ordered_by_rank_then_tier_id(ent):
    path = ent.upgrade_path()
    ranks = [row["tier_rank"] for row in path]
    assert ranks == sorted(ranks)
    # Same-rank cluster (rank 2): cloud_pro < pro lexicographically.
    rank2 = [row["tier"] for row in path if row["tier_rank"] == 2]
    assert rank2 == sorted(rank2)


def test_stable_across_calls(ent):
    a = ent.upgrade_path()
    b = ent.upgrade_path()
    c = ent.upgrade_path()
    assert a == b == c


def test_trial_never_in_path(monkeypatch, ent):
    # Trial is a promotional grant, not purchasable. The upgrade-CTA must
    # never route to it -- mirrors tier_unlocks()'s posture.
    _force_tier(monkeypatch, ent, ent.TIER_OSS)
    ids = {row["tier"] for row in ent.upgrade_path()}
    assert ent.TIER_TRIAL not in ids


# -- safety ----------------------------------------------------------------


def test_never_raises(monkeypatch, ent):
    def boom(*_, **__):
        raise RuntimeError("synthetic")

    monkeypatch.setattr(ent, "get_entitlement", boom)
    assert ent.upgrade_path() == []


def test_does_not_mutate_live_entitlement(ent):
    live_before = ent.get_entitlement().to_dict()
    ent.upgrade_path()
    live_after = ent.get_entitlement().to_dict()
    assert live_before == live_after


# -- API surface -----------------------------------------------------------


def test_api_envelope_shape(client):
    rv = client.get("/api/entitlement/upgrade-path")
    assert rv.status_code == 200
    body = rv.get_json()
    assert set(body.keys()) == {
        "path",
        "current_tier",
        "current_tier_rank",
        "grace",
        "enforced",
    }


def test_api_oss_default_path(client, ent):
    rv = client.get("/api/entitlement/upgrade-path")
    body = rv.get_json()
    assert body["current_tier"] == ent.TIER_OSS
    assert body["current_tier_rank"] == 0
    tiers = [row["tier"] for row in body["path"]]
    assert tiers == [
        ent.TIER_CLOUD_STARTER,
        ent.TIER_CLOUD_PRO,
        ent.TIER_PRO,
        ent.TIER_ENTERPRISE,
    ]


def test_api_row_parity_with_singular_endpoint(client, ent):
    rv = client.get("/api/entitlement/upgrade-path")
    body = rv.get_json()
    for row in body["path"]:
        single = client.get(
            f"/api/entitlement/tier-unlocks?tier={row['tier']}",
        ).get_json()
        assert row == single


def test_api_enterprise_path_is_empty(client, ent, monkeypatch):
    _force_tier(monkeypatch, ent, ent.TIER_ENTERPRISE)
    rv = client.get("/api/entitlement/upgrade-path")
    body = rv.get_json()
    assert body["current_tier"] == ent.TIER_ENTERPRISE
    assert body["path"] == []


def test_api_never_5xxs_on_resolver_failure(client, ent, monkeypatch):
    def boom(*_, **__):
        raise RuntimeError("synthetic")

    monkeypatch.setattr(ent, "get_entitlement", boom)
    rv = client.get("/api/entitlement/upgrade-path")
    assert rv.status_code == 200
    body = rv.get_json()
    assert body["path"] == []
    assert body["current_tier"] == ent.TIER_OSS
    assert body["grace"] is True
    assert body["enforced"] is False
