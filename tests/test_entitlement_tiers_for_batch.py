"""Tests for ``clawmetry.entitlements.tiers_for_batch`` +
``GET /api/entitlement/tiers-for-batch``.

Plural sibling of :func:`tiers_for_feature` / :func:`tiers_for_runtime`.
Where the singular helpers answer "which tiers grant *this* feature or
runtime" one id at a time, the batch returns the same row shape for
every entry in ``ALL_FEATURES`` and ``ALL_RUNTIMES`` so a pricing-table
/ feature-comparison matrix UI can render the full "Available in X"
grid off **one** round-trip. These tests pin the contract:

  - returns one row per known feature and one row per known runtime
  - each row matches the singular helper output byte-for-byte
  - free items appear in every tier (no holes), paid items only in
    their granting tiers (no leakage)
  - never raises -- a resolver failure short-circuits to empty lists
  - the wrapper endpoint always returns a 200 with the grace envelope
    so the pricing page keeps rendering even when the resolver is sick
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


def test_returns_two_buckets(ent):
    body = ent.tiers_for_batch()
    assert isinstance(body, dict)
    assert set(body.keys()) == {"features", "runtimes"}
    assert isinstance(body["features"], list)
    assert isinstance(body["runtimes"], list)
    assert body["features"], "feature ladder must be non-empty"
    assert body["runtimes"], "runtime ladder must be non-empty"


def test_each_feature_row_has_singular_shape(ent):
    expected = {
        "item",
        "kind",
        "label",
        "free",
        "min_tier",
        "min_tier_label",
        "min_tier_rank",
        "tiers",
    }
    for row in ent.tiers_for_batch()["features"]:
        assert set(row.keys()) == expected
        assert row["kind"] == "feature"


def test_each_runtime_row_has_singular_shape(ent):
    expected = {
        "item",
        "kind",
        "label",
        "free",
        "min_tier",
        "min_tier_label",
        "min_tier_rank",
        "tiers",
    }
    for row in ent.tiers_for_batch()["runtimes"]:
        assert set(row.keys()) == expected
        assert row["kind"] == "runtime"


def test_tier_rows_have_expected_keys(ent):
    body = ent.tiers_for_batch()
    for row in body["features"] + body["runtimes"]:
        for tier_row in row["tiers"]:
            assert set(tier_row.keys()) == {
                "id",
                "label",
                "rank",
                "purchasable",
            }


# ── coverage ──────────────────────────────────────────────────────────────


def test_covers_every_known_feature(ent):
    items = {row["item"] for row in ent.tiers_for_batch()["features"]}
    assert items == set(ent.ALL_FEATURES)


def test_covers_every_known_runtime(ent):
    items = {row["item"] for row in ent.tiers_for_batch()["runtimes"]}
    assert items == set(ent.ALL_RUNTIMES)


# ── ordering ──────────────────────────────────────────────────────────────


def test_features_sorted_by_feature_tier_rank_then_id(ent):
    rows = ent.tiers_for_batch()["features"]
    keys = [
        (ent._FEATURE_TIER_RANK.get(ent.feature_tier(r["item"]), 9), r["item"])
        for r in rows
    ]
    assert keys == sorted(keys)


def test_runtimes_free_first_then_paid_alpha(ent):
    rows = ent.tiers_for_batch()["runtimes"]
    items = [r["item"] for r in rows]
    expected = sorted(ent.FREE_RUNTIMES) + sorted(ent.PAID_RUNTIMES)
    assert items == expected


def test_stable_across_calls(ent):
    assert ent.tiers_for_batch() == ent.tiers_for_batch()


# ── parity with singular helpers ──────────────────────────────────────────


def test_feature_rows_equal_singular_calls(ent):
    for row in ent.tiers_for_batch()["features"]:
        assert row == ent.tiers_for_feature(row["item"])


def test_runtime_rows_equal_singular_calls(ent):
    for row in ent.tiers_for_batch()["runtimes"]:
        assert row == ent.tiers_for_runtime(row["item"])


# ── free vs paid invariants ───────────────────────────────────────────────


def test_free_features_appear_in_every_tier(ent):
    rows = {r["item"]: r for r in ent.tiers_for_batch()["features"]}
    for fid in ent.FREE_FEATURES:
        ids = {t["id"] for t in rows[fid]["tiers"]}
        assert ids == set(ent._TIER_ORDER), fid
        assert rows[fid]["free"] is True


def test_free_runtimes_appear_in_every_tier(ent):
    rows = {r["item"]: r for r in ent.tiers_for_batch()["runtimes"]}
    for rt in ent.FREE_RUNTIMES:
        ids = {t["id"] for t in rows[rt]["tiers"]}
        assert ids == set(ent._TIER_ORDER), rt
        assert rows[rt]["free"] is True


def test_paid_runtimes_skip_floor_tiers(ent):
    rows = {r["item"]: r for r in ent.tiers_for_batch()["runtimes"]}
    for rt in ent.PAID_RUNTIMES:
        ids = {t["id"] for t in rows[rt]["tiers"]}
        assert ent.TIER_OSS not in ids
        assert ent.TIER_CLOUD_FREE not in ids
        assert rows[rt]["free"] is False


def test_enterprise_feature_only_in_enterprise(ent):
    rows = {r["item"]: r for r in ent.tiers_for_batch()["features"]}
    ids = {t["id"] for t in rows["sso"]["tiers"]}
    assert ids == {ent.TIER_ENTERPRISE}


# ── safety ────────────────────────────────────────────────────────────────


def test_does_not_mutate_live_entitlement(ent):
    before = ent.get_entitlement().to_dict()
    ent.tiers_for_batch()
    after = ent.get_entitlement().to_dict()
    assert before == after


def test_never_raises(monkeypatch, ent):
    def boom(*_, **__):
        raise RuntimeError("synthetic resolver failure")

    monkeypatch.setattr(ent, "tiers_for_feature", boom)
    monkeypatch.setattr(ent, "tiers_for_runtime", boom)
    # Helper swallows per-row failures and returns empty lists -- never
    # propagates. The outer try/except guards against catastrophic
    # failure in the iteration setup itself.
    body = ent.tiers_for_batch()
    assert body == {"features": [], "runtimes": []}


# ── API surface ───────────────────────────────────────────────────────────


def test_api_returns_envelope_shape(client):
    rv = client.get("/api/entitlement/tiers-for-batch")
    assert rv.status_code == 200
    body = rv.get_json()
    assert set(body.keys()) == {
        "features",
        "runtimes",
        "current_tier",
        "current_tier_rank",
        "grace",
        "enforced",
    }


def test_api_covers_every_feature_and_runtime(client, ent):
    rv = client.get("/api/entitlement/tiers-for-batch")
    body = rv.get_json()
    feat_ids = {row["item"] for row in body["features"]}
    rt_ids = {row["item"] for row in body["runtimes"]}
    assert feat_ids == set(ent.ALL_FEATURES)
    assert rt_ids == set(ent.ALL_RUNTIMES)


def test_api_rows_match_singular_endpoint(client, ent):
    rv = client.get("/api/entitlement/tiers-for-batch")
    body = rv.get_json()
    for row in body["features"]:
        single = client.get(
            f"/api/entitlement/tiers-for?feature={row['item']}"
        )
        assert single.status_code == 200
        assert single.get_json() == row
    for row in body["runtimes"]:
        single = client.get(
            f"/api/entitlement/tiers-for?runtime={row['item']}"
        )
        assert single.status_code == 200
        assert single.get_json() == row


def test_api_envelope_reports_grace_in_oss_default(client):
    body = client.get("/api/entitlement/tiers-for-batch").get_json()
    # OSS-free default is grace=True, enforced=False, tier="oss" -- the
    # envelope mirrors tier-unlocks-batch / tier-locks-batch.
    assert body["grace"] is True
    assert body["enforced"] is False
    assert body["current_tier"] == "oss"
    assert body["current_tier_rank"] == 0


def test_api_resolver_failure_returns_grace_envelope(monkeypatch, client):
    import clawmetry.entitlements as e

    def boom(*_, **__):
        raise RuntimeError("synthetic resolver failure")

    monkeypatch.setattr(e, "tiers_for_batch", boom)
    rv = client.get("/api/entitlement/tiers-for-batch")
    assert rv.status_code == 200
    body = rv.get_json()
    assert body == {
        "features": [],
        "runtimes": [],
        "current_tier": "oss",
        "current_tier_rank": 0,
        "grace": True,
        "enforced": False,
    }
