"""Tests for ``clawmetry.entitlements.tiers_for_feature`` /
``tiers_for_runtime`` + ``GET /api/entitlement/tiers-for``.

Inverse of :func:`min_tier_for_feature` / :func:`min_tier_for_runtime`:
where the ``min_tier_for_*`` helpers return the *cheapest* tier that
grants an item (one id used by the upgrade-CTA), the ``tiers_for_*``
helpers return the **full** ladder of tiers that grant it. The
"Available in: Pro, Self-hosted Pro, Trial, Enterprise" availability
list a pricing-page row or feature tooltip needs.

These tests pin:

* every paid feature / runtime resolves to a non-empty tier list
* free features / runtimes appear in every tier (no holes)
* paid features only appear in tiers that grant them (no leakage
  into Starter for Pro-only features, etc.)
* min_tier matches the existing :func:`min_tier_for_feature` /
  :func:`min_tier_for_runtime` helpers (consistency invariant)
* the catalog rows surface the same ladder so a matrix UI does not
  need an N+1 round-trip
* the API endpoint round-trips both axes and rejects bad input cleanly
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


def test_feature_returns_full_shape(ent):
    body = ent.tiers_for_feature("self_evolve")
    assert body is not None
    assert set(body.keys()) == {
        "item",
        "kind",
        "label",
        "free",
        "min_tier",
        "min_tier_label",
        "min_tier_rank",
        "tiers",
    }
    assert body["kind"] == "feature"
    assert body["item"] == "self_evolve"


def test_runtime_returns_full_shape(ent):
    body = ent.tiers_for_runtime("claude_code")
    assert body is not None
    assert set(body.keys()) == {
        "item",
        "kind",
        "label",
        "free",
        "min_tier",
        "min_tier_label",
        "min_tier_rank",
        "tiers",
    }
    assert body["kind"] == "runtime"
    assert body["item"] == "claude_code"


def test_tier_rows_have_expected_keys(ent):
    body = ent.tiers_for_feature("self_evolve")
    assert body["tiers"], "paid feature must list at least one tier"
    for row in body["tiers"]:
        assert set(row.keys()) == {"id", "label", "rank", "purchasable"}
        assert isinstance(row["id"], str) and row["id"]
        assert isinstance(row["label"], str) and row["label"]
        assert isinstance(row["rank"], int)
        assert isinstance(row["purchasable"], bool)


def test_tier_rows_sorted_by_rank_then_id(ent):
    body = ent.tiers_for_feature("self_evolve")
    ranks = [(r["rank"], r["id"]) for r in body["tiers"]]
    assert ranks == sorted(ranks)


# ── min_tier consistency ──────────────────────────────────────────────────


def test_min_tier_matches_min_tier_for_feature(ent):
    for fid in ent.ALL_FEATURES:
        body = ent.tiers_for_feature(fid)
        assert body is not None, fid
        assert body["min_tier"] == ent.min_tier_for_feature(fid), fid


def test_min_tier_matches_min_tier_for_runtime(ent):
    for rt in ent.ALL_RUNTIMES:
        body = ent.tiers_for_runtime(rt)
        assert body is not None, rt
        assert body["min_tier"] == ent.min_tier_for_runtime(rt), rt


# ── free features / runtimes available everywhere ─────────────────────────


def test_free_feature_appears_in_every_tier(ent):
    body = ent.tiers_for_feature("sessions")
    assert body["free"] is True
    ids = {row["id"] for row in body["tiers"]}
    # Every known tier grants the free observability surface.
    assert ids == set(ent._TIER_ORDER)


def test_free_runtime_appears_in_every_tier(ent):
    body = ent.tiers_for_runtime("openclaw")
    assert body["free"] is True
    ids = {row["id"] for row in body["tiers"]}
    assert ids == set(ent._TIER_ORDER)


def test_nemoclaw_free_runtime_appears_in_every_tier(ent):
    body = ent.tiers_for_runtime("nemoclaw")
    assert body["free"] is True
    ids = {row["id"] for row in body["tiers"]}
    assert ids == set(ent._TIER_ORDER)


# ── paid feature/runtime carriage ─────────────────────────────────────────


def test_starter_feature_carried_by_all_paid_tiers(ent):
    # ``fleet`` is in STARTER_FEATURES -> trial + starter + pro + self-hosted
    # pro + enterprise all carry it; OSS / cloud_free do not.
    body = ent.tiers_for_feature("fleet")
    ids = {row["id"] for row in body["tiers"]}
    assert ent.TIER_OSS not in ids
    assert ent.TIER_CLOUD_FREE not in ids
    assert ent.TIER_TRIAL in ids
    assert ent.TIER_CLOUD_STARTER in ids
    assert ent.TIER_CLOUD_PRO in ids
    assert ent.TIER_PRO in ids
    assert ent.TIER_ENTERPRISE in ids


def test_pro_only_feature_skips_starter(ent):
    # ``self_evolve`` is PRO_ONLY -> NOT in starter, but in trial (full paid
    # grant) + pro tiers + enterprise.
    body = ent.tiers_for_feature("self_evolve")
    ids = {row["id"] for row in body["tiers"]}
    assert ent.TIER_CLOUD_STARTER not in ids
    assert ent.TIER_TRIAL in ids
    assert ent.TIER_CLOUD_PRO in ids
    assert ent.TIER_PRO in ids
    assert ent.TIER_ENTERPRISE in ids


def test_enterprise_feature_only_in_enterprise(ent):
    body = ent.tiers_for_feature("sso")
    ids = {row["id"] for row in body["tiers"]}
    assert ids == {ent.TIER_ENTERPRISE}


def test_paid_runtime_carriage(ent):
    # Every paid runtime is granted at every paid tier (trial, starter,
    # cloud pro, self-hosted pro, enterprise).
    expected = {
        ent.TIER_TRIAL,
        ent.TIER_CLOUD_STARTER,
        ent.TIER_CLOUD_PRO,
        ent.TIER_PRO,
        ent.TIER_ENTERPRISE,
    }
    for rt in ent.PAID_RUNTIMES:
        body = ent.tiers_for_runtime(rt)
        ids = {row["id"] for row in body["tiers"]}
        assert ids == expected, rt


# ── purchasable flag ──────────────────────────────────────────────────────


def test_trial_row_marked_non_purchasable(ent):
    body = ent.tiers_for_feature("fleet")
    by_id = {row["id"]: row for row in body["tiers"]}
    assert by_id[ent.TIER_TRIAL]["purchasable"] is False
    assert by_id[ent.TIER_CLOUD_STARTER]["purchasable"] is True
    assert by_id[ent.TIER_ENTERPRISE]["purchasable"] is True


def test_min_tier_is_purchasable_for_paid_feature(ent):
    body = ent.tiers_for_feature("fleet")
    # min_tier is cheapest purchasable -- trial is excluded (promo grant).
    assert body["min_tier"] == ent.TIER_CLOUD_STARTER
    by_id = {row["id"]: row for row in body["tiers"]}
    assert by_id[body["min_tier"]]["purchasable"] is True


# ── input handling / safety ───────────────────────────────────────────────


def test_unknown_feature_returns_none(ent):
    assert ent.tiers_for_feature("not_a_real_feature_xyz") is None


def test_unknown_runtime_returns_none(ent):
    assert ent.tiers_for_runtime("not_a_real_runtime_xyz") is None


def test_empty_returns_none(ent):
    assert ent.tiers_for_feature("") is None
    assert ent.tiers_for_feature(None) is None  # type: ignore[arg-type]
    assert ent.tiers_for_runtime("") is None
    assert ent.tiers_for_runtime(None) is None  # type: ignore[arg-type]


def test_runtime_alias_resolves(ent):
    # ``claude-code`` aliases ``claude_code`` -- the inverse helper must
    # canonicalise the same way the rest of the resolver does.
    body = ent.tiers_for_runtime("claude-code")
    assert body is not None
    assert body["item"] == "claude_code"


def test_lowercases_input(ent):
    body = ent.tiers_for_feature("FLEET")
    assert body is not None
    assert body["item"] == "fleet"


def test_never_raises(monkeypatch, ent):
    def boom(*_, **__):
        raise RuntimeError("synthetic")

    monkeypatch.setattr(ent, "tier_label", boom)
    assert ent.tiers_for_feature("fleet") is None
    assert ent.tiers_for_runtime("claude_code") is None


def test_does_not_mutate_live_entitlement(ent):
    live_before = ent.get_entitlement().to_dict()
    ent.tiers_for_feature("self_evolve")
    ent.tiers_for_runtime("claude_code")
    live_after = ent.get_entitlement().to_dict()
    assert live_before == live_after


# ── catalog row enrichment ────────────────────────────────────────────────


def test_feature_catalog_carries_tiers_ladder(ent):
    by_id = {row["id"]: row for row in ent.feature_catalog()}
    # Free features: every tier in the ladder.
    assert set(by_id["sessions"]["tiers"]) == set(ent._TIER_ORDER)
    # Pro-only features: starter is missing.
    assert ent.TIER_CLOUD_STARTER not in by_id["self_evolve"]["tiers"]
    assert ent.TIER_CLOUD_PRO in by_id["self_evolve"]["tiers"]
    # Enterprise-only features.
    assert by_id["sso"]["tiers"] == [ent.TIER_ENTERPRISE]


def test_runtime_catalog_carries_tiers_ladder(ent):
    by_id = {row["id"]: row for row in ent.runtime_catalog()}
    # Free runtimes -> every tier.
    assert set(by_id["openclaw"]["tiers"]) == set(ent._TIER_ORDER)
    assert set(by_id["nemoclaw"]["tiers"]) == set(ent._TIER_ORDER)
    # Paid runtime -> every paid tier, no oss / cloud_free.
    paid_tier_ids = set(by_id["claude_code"]["tiers"])
    assert ent.TIER_OSS not in paid_tier_ids
    assert ent.TIER_CLOUD_FREE not in paid_tier_ids
    assert ent.TIER_CLOUD_STARTER in paid_tier_ids
    assert ent.TIER_TRIAL in paid_tier_ids
    assert ent.TIER_ENTERPRISE in paid_tier_ids


def test_catalog_tiers_are_id_only_strings(ent):
    """The catalog inline-list uses ids only (compact). The full row-shape
    -- id / label / rank / purchasable -- lives on
    ``/api/entitlement/tiers-for``."""
    for row in ent.feature_catalog():
        assert isinstance(row["tiers"], list)
        for t in row["tiers"]:
            assert isinstance(t, str)
    for row in ent.runtime_catalog():
        assert isinstance(row["tiers"], list)
        for t in row["tiers"]:
            assert isinstance(t, str)


# ── API surface ───────────────────────────────────────────────────────────


def test_api_returns_feature_ladder(client, ent):
    rv = client.get("/api/entitlement/tiers-for?feature=fleet")
    assert rv.status_code == 200
    body = rv.get_json()
    assert body["kind"] == "feature"
    assert body["item"] == "fleet"
    ids = {row["id"] for row in body["tiers"]}
    assert ent.TIER_CLOUD_STARTER in ids
    assert ent.TIER_ENTERPRISE in ids
    assert ent.TIER_OSS not in ids


def test_api_returns_runtime_ladder(client, ent):
    rv = client.get("/api/entitlement/tiers-for?runtime=claude_code")
    assert rv.status_code == 200
    body = rv.get_json()
    assert body["kind"] == "runtime"
    assert body["item"] == "claude_code"
    ids = {row["id"] for row in body["tiers"]}
    assert ids == {
        ent.TIER_TRIAL,
        ent.TIER_CLOUD_STARTER,
        ent.TIER_CLOUD_PRO,
        ent.TIER_PRO,
        ent.TIER_ENTERPRISE,
    }


def test_api_missing_args_is_400(client):
    rv = client.get("/api/entitlement/tiers-for")
    assert rv.status_code == 400
    body = rv.get_json()
    assert "error" in body


def test_api_both_args_is_400(client):
    rv = client.get(
        "/api/entitlement/tiers-for?feature=fleet&runtime=claude_code"
    )
    assert rv.status_code == 400
    body = rv.get_json()
    assert "error" in body


def test_api_unknown_feature_is_404(client):
    rv = client.get("/api/entitlement/tiers-for?feature=nonsense_xyz")
    assert rv.status_code == 404
    body = rv.get_json()
    assert body["feature"] == "nonsense_xyz"


def test_api_unknown_runtime_is_404(client):
    rv = client.get("/api/entitlement/tiers-for?runtime=nonsense_xyz")
    assert rv.status_code == 404
    body = rv.get_json()
    assert body["runtime"] == "nonsense_xyz"


def test_api_runtime_alias_resolves(client, ent):
    rv = client.get("/api/entitlement/tiers-for?runtime=claude-code")
    assert rv.status_code == 200
    assert rv.get_json()["item"] == "claude_code"


def test_api_lowercases_query(client, ent):
    rv = client.get("/api/entitlement/tiers-for?feature=FLEET")
    assert rv.status_code == 200
    assert rv.get_json()["item"] == "fleet"


# ── invariant vs tier_catalog ─────────────────────────────────────────────


def test_feature_ladder_matches_tier_catalog_grants(ent):
    """Every (feature, tier) pair where tier carries feature in
    ``tiers_for_feature`` must also list that feature in
    ``tier_catalog``'s ``features`` set -- catches a desync between
    the inverse helper and the forward catalog."""
    tier_feats = {
        t["id"]: set(t["features"]) | set(ent.FREE_FEATURES)
        for t in ent.tier_catalog()
    }
    for fid in ent.ALL_FEATURES:
        body = ent.tiers_for_feature(fid)
        for row in body["tiers"]:
            tid = row["id"]
            assert fid in tier_feats[tid], (fid, tid)
