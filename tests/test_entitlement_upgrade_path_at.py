"""Tests for ``clawmetry.entitlements.upgrade_path_at`` +
``GET /api/entitlement/upgrade-path-at``.

Source-anchored what-if sibling of :mod:`test_entitlement_upgrade_path`:
where the live variant pins the walk's start to the resolver, this one
walks strictly above a caller-supplied hypothetical ``tier``. Pins the
per-source ladder + per-row shape + parity contract with the live
:func:`upgrade_path` so a pricing-wizard "compare from tier X" surface
keeps rendering when ``_PURCHASABLE_TIERS`` / ``_TIER_RANK`` shift
underneath it.
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
    synthetic = ent._build(tier, source="test")

    def _stub(force: bool = False):  # noqa: ARG001
        return synthetic

    monkeypatch.setattr(ent, "get_entitlement", _stub)


# -- shape -----------------------------------------------------------------


def test_returns_list_for_known_source(ent):
    path = ent.upgrade_path_at(ent.TIER_OSS)
    assert isinstance(path, list)


def test_each_row_matches_tier_unlocks_shape(ent):
    path = ent.upgrade_path_at(ent.TIER_OSS)
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
    # Row equality with the singular endpoint -- the _at helper is a pure
    # source-anchored plural sibling, not a divergent path.
    path = ent.upgrade_path_at(ent.TIER_OSS)
    for row in path:
        assert row == ent.tier_unlocks(row["tier"])


# -- per-source ladder -----------------------------------------------------


def test_oss_source_full_upper_ladder(ent):
    tiers = [row["tier"] for row in ent.upgrade_path_at(ent.TIER_OSS)]
    assert tiers == [
        ent.TIER_CLOUD_STARTER,
        ent.TIER_CLOUD_PRO,
        ent.TIER_PRO,
        ent.TIER_ENTERPRISE,
    ]


def test_cloud_free_source_matches_oss_source(ent):
    # Both are rank 0, so ladder above is identical.
    a = [r["tier"] for r in ent.upgrade_path_at(ent.TIER_CLOUD_FREE)]
    b = [r["tier"] for r in ent.upgrade_path_at(ent.TIER_OSS)]
    assert a == b


def test_starter_source_drops_starter_and_below(ent):
    tiers = [row["tier"] for row in ent.upgrade_path_at(ent.TIER_CLOUD_STARTER)]
    assert tiers == [
        ent.TIER_CLOUD_PRO,
        ent.TIER_PRO,
        ent.TIER_ENTERPRISE,
    ]


def test_cloud_pro_source_is_enterprise_only(ent):
    # Same-rank siblings (rank 2 pro / cloud_pro) excluded, only strictly
    # above (enterprise) remains.
    assert [r["tier"] for r in ent.upgrade_path_at(ent.TIER_CLOUD_PRO)] == [
        ent.TIER_ENTERPRISE,
    ]


def test_self_hosted_pro_source_mirrors_cloud_pro(ent):
    assert [r["tier"] for r in ent.upgrade_path_at(ent.TIER_PRO)] == [
        ent.TIER_ENTERPRISE,
    ]


def test_enterprise_source_is_empty(ent):
    assert ent.upgrade_path_at(ent.TIER_ENTERPRISE) == []


def test_trial_source_walks_past_same_rank(ent):
    # Trial is rank 2, same as pro / cloud_pro. Strictly-above walk should
    # skip same-rank siblings and only land on enterprise.
    assert [r["tier"] for r in ent.upgrade_path_at(ent.TIER_TRIAL)] == [
        ent.TIER_ENTERPRISE,
    ]


# -- parity with live upgrade_path -----------------------------------------


def test_at_source_matches_live_when_source_equals_current(ent):
    # Byte-parity: for any resolved current tier, upgrade_path_at(current)
    # returns the same rows as the live upgrade_path().
    live = ent.upgrade_path()
    at = ent.upgrade_path_at(ent.TIER_OSS)  # fixture resolves to OSS
    assert at == live


def test_at_source_parity_across_forced_tiers(monkeypatch, ent):
    for tier in (
        ent.TIER_OSS,
        ent.TIER_CLOUD_FREE,
        ent.TIER_CLOUD_STARTER,
        ent.TIER_CLOUD_PRO,
        ent.TIER_PRO,
        ent.TIER_ENTERPRISE,
    ):
        _force_tier(monkeypatch, ent, tier)
        assert ent.upgrade_path_at(tier) == ent.upgrade_path(), tier


# -- ordering / stability --------------------------------------------------


def test_ordered_by_rank_then_tier_id(ent):
    path = ent.upgrade_path_at(ent.TIER_OSS)
    ranks = [row["tier_rank"] for row in path]
    assert ranks == sorted(ranks)
    rank2 = [row["tier"] for row in path if row["tier_rank"] == 2]
    assert rank2 == sorted(rank2)


def test_stable_across_calls(ent):
    a = ent.upgrade_path_at(ent.TIER_OSS)
    b = ent.upgrade_path_at(ent.TIER_OSS)
    c = ent.upgrade_path_at(ent.TIER_OSS)
    assert a == b == c


def test_trial_never_in_path(ent):
    for src in (ent.TIER_OSS, ent.TIER_CLOUD_STARTER, ent.TIER_PRO):
        ids = {row["tier"] for row in ent.upgrade_path_at(src)}
        assert ent.TIER_TRIAL not in ids


# -- lenient _at posture ---------------------------------------------------


def test_unknown_tier_returns_none(ent):
    assert ent.upgrade_path_at("nope") is None
    assert ent.upgrade_path_at("") is None
    assert ent.upgrade_path_at(None) is None  # type: ignore[arg-type]


def test_whitespace_and_casing_normalised(ent):
    assert ent.upgrade_path_at("  OSS  ") == ent.upgrade_path_at(ent.TIER_OSS)


# -- safety ----------------------------------------------------------------


def test_never_raises_on_builder_failure(monkeypatch, ent):
    def boom(*_, **__):
        raise RuntimeError("synthetic")

    monkeypatch.setattr(ent, "tier_unlocks", boom)
    assert ent.upgrade_path_at(ent.TIER_OSS) == []


def test_does_not_mutate_live_entitlement(ent):
    before = ent.get_entitlement().to_dict()
    ent.upgrade_path_at(ent.TIER_PRO)
    after = ent.get_entitlement().to_dict()
    assert before == after


# -- API surface -----------------------------------------------------------


def test_api_envelope_shape(client, ent):
    rv = client.get(f"/api/entitlement/upgrade-path-at?tier={ent.TIER_OSS}")
    assert rv.status_code == 200
    body = rv.get_json()
    assert set(body.keys()) == {
        "tier",
        "tier_label",
        "tier_rank",
        "path",
        "current_tier",
        "current_tier_rank",
        "grace",
        "enforced",
    }


def test_api_oss_source_full_ladder(client, ent):
    rv = client.get(f"/api/entitlement/upgrade-path-at?tier={ent.TIER_OSS}")
    body = rv.get_json()
    assert body["tier"] == ent.TIER_OSS
    assert body["tier_rank"] == 0
    tiers = [row["tier"] for row in body["path"]]
    assert tiers == [
        ent.TIER_CLOUD_STARTER,
        ent.TIER_CLOUD_PRO,
        ent.TIER_PRO,
        ent.TIER_ENTERPRISE,
    ]


def test_api_row_parity_with_singular_endpoint(client, ent):
    rv = client.get(f"/api/entitlement/upgrade-path-at?tier={ent.TIER_OSS}")
    body = rv.get_json()
    for row in body["path"]:
        single = client.get(
            f"/api/entitlement/tier-unlocks?tier={row['tier']}",
        ).get_json()
        assert row == single


def test_api_body_parity_with_live_upgrade_path(client, ent):
    # Envelopes differ (extra tier / tier_label / tier_rank echo), but the
    # `path` array is byte-identical when source == current.
    at = client.get(
        f"/api/entitlement/upgrade-path-at?tier={ent.TIER_OSS}",
    ).get_json()
    live = client.get("/api/entitlement/upgrade-path").get_json()
    assert at["path"] == live["path"]


def test_api_enterprise_source_is_empty(client, ent):
    rv = client.get(f"/api/entitlement/upgrade-path-at?tier={ent.TIER_ENTERPRISE}")
    body = rv.get_json()
    assert body["tier"] == ent.TIER_ENTERPRISE
    assert body["path"] == []


def test_api_missing_tier_400(client):
    rv = client.get("/api/entitlement/upgrade-path-at")
    assert rv.status_code == 400
    body = rv.get_json()
    assert "error" in body


def test_api_empty_tier_400(client):
    rv = client.get("/api/entitlement/upgrade-path-at?tier=")
    assert rv.status_code == 400


def test_api_unknown_tier_404(client):
    rv = client.get("/api/entitlement/upgrade-path-at?tier=nope")
    assert rv.status_code == 404
    body = rv.get_json()
    assert body["error"] == "unknown tier"
    assert body["tier"] == "nope"


def test_api_never_5xxs_on_resolver_failure(client, ent, monkeypatch):
    def boom(*_, **__):
        raise RuntimeError("synthetic")

    monkeypatch.setattr(ent, "get_entitlement", boom)
    rv = client.get(f"/api/entitlement/upgrade-path-at?tier={ent.TIER_OSS}")
    assert rv.status_code == 200
    body = rv.get_json()
    assert body["path"] == []
    assert body["grace"] is True
    assert body["enforced"] is False
