"""Tests for ``clawmetry.entitlements.downgrade_path_at`` +
``GET /api/entitlement/downgrade-path-at``.

Source-anchored what-if sibling of :mod:`test_entitlement_downgrade_path`:
walks strictly below a caller-supplied hypothetical ``tier`` and returns
the cumulative-loss row for each rung. Pins the per-source ladder + row
shape + parity contract with the live :func:`downgrade_path` so a
"compare from tier X" downgrade-warning surface keeps rendering when
``_PURCHASABLE_TIERS`` / ``_TIER_RANK`` / ``_TIER_FEATURES`` shift
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
    assert isinstance(ent.downgrade_path_at(ent.TIER_ENTERPRISE), list)


def test_each_row_shape(ent):
    path = ent.downgrade_path_at(ent.TIER_ENTERPRISE)
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


def test_source_echo_matches_caller_supplied(ent):
    # current_tier / current_tier_label / current_tier_rank echo the
    # caller-supplied `_at` source (not the resolver) so a per-row consumer
    # can label the "from" side of the transition.
    path = ent.downgrade_path_at(ent.TIER_PRO)
    for row in path:
        assert row["current_tier"] == ent.TIER_PRO
        assert row["current_tier_label"] == ent.tier_label(ent.TIER_PRO)
        assert row["current_tier_rank"] == ent.tier_rank(ent.TIER_PRO)


# -- per-source ladder -----------------------------------------------------


def test_floor_source_is_empty(ent):
    assert ent.downgrade_path_at(ent.TIER_OSS) == []
    assert ent.downgrade_path_at(ent.TIER_CLOUD_FREE) == []


def test_starter_source_has_only_floor_pair(ent):
    tiers = [r["target"] for r in ent.downgrade_path_at(ent.TIER_CLOUD_STARTER)]
    # rank 0 siblings, sorted by id ascending after the -rank sort.
    assert set(tiers) == {ent.TIER_OSS, ent.TIER_CLOUD_FREE}


def test_pro_source_walks_all_rungs_below(ent):
    tiers = [r["target"] for r in ent.downgrade_path_at(ent.TIER_PRO)]
    # Descending: rank 1 (starter) first, then rank 0 pair.
    # `pro` is rank 2 -- same-rank siblings (cloud_pro) are excluded.
    assert tiers[0] == ent.TIER_CLOUD_STARTER
    assert set(tiers[1:]) == {ent.TIER_OSS, ent.TIER_CLOUD_FREE}


def test_enterprise_source_full_lower_ladder(ent):
    tiers = [r["target"] for r in ent.downgrade_path_at(ent.TIER_ENTERPRISE)]
    # Descending: rank 2 pair (cloud_pro then pro), rank 1, rank 0 pair.
    assert tiers[0] == ent.TIER_CLOUD_PRO
    assert tiers[1] == ent.TIER_PRO
    assert tiers[2] == ent.TIER_CLOUD_STARTER
    assert set(tiers[3:]) == {ent.TIER_OSS, ent.TIER_CLOUD_FREE}


def test_trial_source_walks_below(ent):
    # Trial (rank 2) -- strictly-below walk lands on rank 1 (starter) then
    # rank 0 pair. Same-rank siblings (pro / cloud_pro) excluded.
    tiers = [r["target"] for r in ent.downgrade_path_at(ent.TIER_TRIAL)]
    assert tiers[0] == ent.TIER_CLOUD_STARTER
    assert set(tiers[1:]) == {ent.TIER_OSS, ent.TIER_CLOUD_FREE}


# -- cumulative shape ------------------------------------------------------


def test_lost_lists_monotonically_grow(ent):
    # Cumulative: each further-down rung's loss list is a superset of the
    # closer rung's.
    path = ent.downgrade_path_at(ent.TIER_ENTERPRISE)
    for a, b in zip(path, path[1:]):
        assert set(a["lost_features"]) <= set(b["lost_features"])
        assert set(a["lost_runtimes"]) <= set(b["lost_runtimes"])


def test_lost_lists_sorted(ent):
    path = ent.downgrade_path_at(ent.TIER_ENTERPRISE)
    for row in path:
        assert row["lost_features"] == sorted(row["lost_features"])
        assert row["lost_runtimes"] == sorted(row["lost_runtimes"])


def test_lost_lists_match_tier_diff(ent):
    # Each row's cumulative loss list matches tier_diff(source, target)
    # -- the _at variant uses tier_diff to stay catalogue-anchored.
    src = ent.TIER_ENTERPRISE
    for row in ent.downgrade_path_at(src):
        diff = ent.tier_diff(src, row["target"])
        assert diff is not None
        assert row["lost_features"] == list(diff["lost_features"])
        assert row["lost_runtimes"] == list(diff["lost_runtimes"])


# -- parity with live downgrade_path ---------------------------------------


def test_at_source_matches_live_when_source_equals_current(monkeypatch, ent):
    # For a plain-catalogue current tier (no runtime overrides), the
    # `_at` variant is byte-identical to the live path.
    for tier in (
        ent.TIER_CLOUD_STARTER,
        ent.TIER_PRO,
        ent.TIER_CLOUD_PRO,
        ent.TIER_ENTERPRISE,
    ):
        _force_tier(monkeypatch, ent, tier)
        assert ent.downgrade_path_at(tier) == ent.downgrade_path(), tier


# -- ordering / stability --------------------------------------------------


def test_ordered_by_neg_rank_then_tier_id(ent):
    path = ent.downgrade_path_at(ent.TIER_ENTERPRISE)
    ranks = [row["target_rank"] for row in path]
    assert ranks == sorted(ranks, reverse=True)
    # Same-rank cluster (rank 0): cloud_free < oss lexicographically.
    rank0 = [row["target"] for row in path if row["target_rank"] == 0]
    assert rank0 == sorted(rank0)


def test_stable_across_calls(ent):
    a = ent.downgrade_path_at(ent.TIER_ENTERPRISE)
    b = ent.downgrade_path_at(ent.TIER_ENTERPRISE)
    c = ent.downgrade_path_at(ent.TIER_ENTERPRISE)
    assert a == b == c


def test_trial_never_in_path(ent):
    # Trial is a promotional grant, not purchasable. Downgrade CTA must
    # never route to it.
    for src in (ent.TIER_ENTERPRISE, ent.TIER_PRO, ent.TIER_CLOUD_STARTER):
        ids = {r["target"] for r in ent.downgrade_path_at(src)}
        assert ent.TIER_TRIAL not in ids


# -- lenient _at posture ---------------------------------------------------


def test_unknown_tier_returns_none(ent):
    assert ent.downgrade_path_at("nope") is None
    assert ent.downgrade_path_at("") is None
    assert ent.downgrade_path_at(None) is None  # type: ignore[arg-type]


def test_whitespace_and_casing_normalised(ent):
    a = ent.downgrade_path_at("  ENTERPRISE  ")
    b = ent.downgrade_path_at(ent.TIER_ENTERPRISE)
    assert a == b


# -- safety ----------------------------------------------------------------


def test_never_raises_on_builder_failure(monkeypatch, ent):
    def boom(*_, **__):
        raise RuntimeError("synthetic")

    monkeypatch.setattr(ent, "tier_diff", boom)
    assert ent.downgrade_path_at(ent.TIER_ENTERPRISE) == []


def test_does_not_mutate_live_entitlement(ent):
    before = ent.get_entitlement().to_dict()
    ent.downgrade_path_at(ent.TIER_ENTERPRISE)
    after = ent.get_entitlement().to_dict()
    assert before == after


# -- API surface -----------------------------------------------------------


def test_api_envelope_shape(client, ent):
    rv = client.get(
        f"/api/entitlement/downgrade-path-at?tier={ent.TIER_ENTERPRISE}",
    )
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


def test_api_enterprise_source_full_lower_ladder(client, ent):
    rv = client.get(
        f"/api/entitlement/downgrade-path-at?tier={ent.TIER_ENTERPRISE}",
    )
    body = rv.get_json()
    assert body["tier"] == ent.TIER_ENTERPRISE
    tiers = [row["target"] for row in body["path"]]
    assert tiers[0] == ent.TIER_CLOUD_PRO


def test_api_floor_source_empty(client, ent):
    rv = client.get(f"/api/entitlement/downgrade-path-at?tier={ent.TIER_OSS}")
    body = rv.get_json()
    assert body["tier"] == ent.TIER_OSS
    assert body["path"] == []


def test_api_body_parity_with_live_downgrade_path(client, ent, monkeypatch):
    # For a plain-catalogue current tier, the `path` array is
    # byte-identical to the live endpoint's `path`.
    _force_tier(monkeypatch, ent, ent.TIER_ENTERPRISE)
    at = client.get(
        f"/api/entitlement/downgrade-path-at?tier={ent.TIER_ENTERPRISE}",
    ).get_json()
    live = client.get("/api/entitlement/downgrade-path").get_json()
    assert at["path"] == live["path"]


def test_api_missing_tier_400(client):
    rv = client.get("/api/entitlement/downgrade-path-at")
    assert rv.status_code == 400
    assert "error" in rv.get_json()


def test_api_empty_tier_400(client):
    rv = client.get("/api/entitlement/downgrade-path-at?tier=")
    assert rv.status_code == 400


def test_api_unknown_tier_404(client):
    rv = client.get("/api/entitlement/downgrade-path-at?tier=nope")
    assert rv.status_code == 404
    body = rv.get_json()
    assert body["error"] == "unknown tier"
    assert body["tier"] == "nope"


def test_api_never_5xxs_on_resolver_failure(client, ent, monkeypatch):
    def boom(*_, **__):
        raise RuntimeError("synthetic")

    monkeypatch.setattr(ent, "get_entitlement", boom)
    rv = client.get(
        f"/api/entitlement/downgrade-path-at?tier={ent.TIER_ENTERPRISE}",
    )
    assert rv.status_code == 200
    body = rv.get_json()
    assert body["path"] == []
    assert body["grace"] is True
    assert body["enforced"] is False
