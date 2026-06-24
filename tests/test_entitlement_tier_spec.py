"""Tests for ``clawmetry.entitlements.tier_spec`` + ``GET
/api/entitlement/tier-spec``.

Scalar sibling of :func:`tier_catalog`: returns the full per-tier
descriptor for one tier id in one shot. Lets a pricing-page column /
upsell tooltip hydrate against a single tier without walking the
ladder client-side.

These tests pin:

* the response shape is identical to a row from :func:`tier_catalog`
  (no drift between the scalar and bulk accessors)
* every tier in the catalogue has a non-None spec, and every spec id
  echoes the requested tier
* tier-derived metadata (rank, label, retention, channel/node limit,
  paid runtimes carried) matches the underlying constant tables
* free vs paid classification (``is_paid``, ``unlocks_paid_runtimes``)
  follows the documented open-core split exactly
* the API endpoint round-trips, 400s on missing input, 404s on unknown
  tier ids, lowercases / trims the query, and never 5xxs on a resolver
  failure (catalogue-derived rows are answered even if the resolver
  short-circuits to OSS-free).
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


_SPEC_KEYS = {
    "id",
    "label",
    "is_paid",
    "is_current",
    "rank",
    "unlocks_paid_runtimes",
    "retention_days",
    "channel_limit",
    "node_limit",
    "features",
    "runtimes",
}


# ── shape ────────────────────────────────────────────────────────────────


def test_returns_full_shape_for_known_tier(ent):
    body = ent.tier_spec(ent.TIER_CLOUD_STARTER)
    assert body is not None
    assert set(body.keys()) == _SPEC_KEYS
    assert body["id"] == ent.TIER_CLOUD_STARTER


def test_every_known_tier_resolves(ent):
    for tier in ent._TIER_ORDER:
        spec = ent.tier_spec(tier)
        assert spec is not None, tier
        assert spec["id"] == tier
        assert set(spec.keys()) == _SPEC_KEYS


def test_unknown_tier_returns_none(ent):
    assert ent.tier_spec("nonsense_tier") is None
    assert ent.tier_spec("") is None
    assert ent.tier_spec(None) is None


def test_lowercases_and_trims_input(ent):
    assert ent.tier_spec("  CLOUD_STARTER  ")["id"] == ent.TIER_CLOUD_STARTER
    assert ent.tier_spec("Enterprise")["id"] == ent.TIER_ENTERPRISE


# ── parity with tier_catalog ─────────────────────────────────────────────


def test_each_spec_matches_catalog_row(ent):
    by_id = {row["id"]: row for row in ent.tier_catalog()}
    for tier in ent._TIER_ORDER:
        spec = ent.tier_spec(tier)
        assert spec == by_id[tier], tier


# ── classification ───────────────────────────────────────────────────────


def test_is_paid_matches_paid_tiers_set(ent):
    for tier in ent._TIER_ORDER:
        spec = ent.tier_spec(tier)
        assert spec["is_paid"] is (tier in ent._PAID_TIERS), tier


def test_unlocks_paid_runtimes_matches_paid_tiers_set(ent):
    for tier in ent._TIER_ORDER:
        spec = ent.tier_spec(tier)
        assert spec["unlocks_paid_runtimes"] is (
            tier in ent._TIER_PAID_RUNTIMES
        ), tier


def test_oss_and_cloud_free_carry_no_paid_features_or_runtimes(ent):
    for tier in (ent.TIER_OSS, ent.TIER_CLOUD_FREE):
        spec = ent.tier_spec(tier)
        assert spec["features"] == []
        assert spec["runtimes"] == []
        assert spec["is_paid"] is False
        assert spec["unlocks_paid_runtimes"] is False


def test_paid_tier_carries_all_paid_runtimes(ent):
    for tier in (
        ent.TIER_CLOUD_STARTER,
        ent.TIER_TRIAL,
        ent.TIER_CLOUD_PRO,
        ent.TIER_PRO,
        ent.TIER_ENTERPRISE,
    ):
        spec = ent.tier_spec(tier)
        assert set(spec["runtimes"]) == set(ent.PAID_RUNTIMES), tier
        # alphabetised so the UI render order is deterministic
        assert spec["runtimes"] == sorted(spec["runtimes"]), tier


# ── per-tier feature carriage ────────────────────────────────────────────


def test_starter_carries_starter_features_only(ent):
    feats = set(ent.tier_spec(ent.TIER_CLOUD_STARTER)["features"])
    assert feats == set(ent.STARTER_FEATURES)
    assert feats.isdisjoint(ent.PRO_ONLY_FEATURES)
    assert feats.isdisjoint(ent.ENTERPRISE_FEATURES)


def test_cloud_pro_carries_starter_plus_pro_only(ent):
    feats = set(ent.tier_spec(ent.TIER_CLOUD_PRO)["features"])
    assert feats == set(ent.PAID_FEATURES)
    assert feats.isdisjoint(ent.ENTERPRISE_FEATURES)


def test_self_hosted_pro_carries_same_paid_set_as_cloud_pro(ent):
    assert set(ent.tier_spec(ent.TIER_PRO)["features"]) == set(ent.PAID_FEATURES)


def test_trial_carries_full_pro_feature_set(ent):
    # Trial is promotional but unlocks the full Pro feature set so callers
    # can pin the same UI as cloud_pro during the trial window.
    feats = set(ent.tier_spec(ent.TIER_TRIAL)["features"])
    assert feats == set(ent.PAID_FEATURES)


def test_enterprise_carries_paid_plus_enterprise_features(ent):
    feats = set(ent.tier_spec(ent.TIER_ENTERPRISE)["features"])
    assert feats == set(ent.PAID_FEATURES | ent.ENTERPRISE_FEATURES)


def test_features_list_is_sorted(ent):
    for tier in ent._TIER_ORDER:
        feats = ent.tier_spec(tier)["features"]
        assert feats == sorted(feats), tier


# ── per-tier metadata ────────────────────────────────────────────────────


def test_rank_matches_tier_order_index(ent):
    for tier in ent._TIER_ORDER:
        assert ent.tier_spec(tier)["rank"] == ent._TIER_ORDER.index(tier), tier


def test_label_matches_tier_label_helper(ent):
    for tier in ent._TIER_ORDER:
        assert ent.tier_spec(tier)["label"] == ent.tier_label(tier), tier


def test_retention_days_matches_constant_table(ent):
    for tier in ent._TIER_ORDER:
        spec = ent.tier_spec(tier)
        assert spec["retention_days"] == ent._TIER_RETENTION_DAYS.get(tier, 7), tier
    # Enterprise = unlimited
    assert ent.tier_spec(ent.TIER_ENTERPRISE)["retention_days"] is None


def test_channel_and_node_limits_match_constant_tables(ent):
    for tier in ent._TIER_ORDER:
        spec = ent.tier_spec(tier)
        assert spec["channel_limit"] == ent._TIER_CHANNEL_LIMIT.get(
            tier, ent._FREE_CHANNEL_LIMIT
        ), tier
        assert spec["node_limit"] == ent._TIER_NODE_LIMIT.get(
            tier, ent._FREE_NODE_LIMIT
        ), tier


# ── is_current vs the resolved entitlement ───────────────────────────────


def test_is_current_marks_oss_in_grace_default(ent):
    # No license file, no cloud cache -> OSS-free is the resolved tier.
    spec = ent.tier_spec(ent.TIER_OSS)
    assert spec["is_current"] is True
    for other in ent._TIER_ORDER:
        if other == ent.TIER_OSS:
            continue
        assert ent.tier_spec(other)["is_current"] is False, other


# ── grace / enforce identity ─────────────────────────────────────────────


def test_grace_and_enforce_return_identical_spec(ent, monkeypatch):
    grace = ent.tier_spec(ent.TIER_CLOUD_PRO)
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    ent.invalidate()
    enforce = ent.tier_spec(ent.TIER_CLOUD_PRO)
    # Catalogue-derived: same answer regardless of paywall state.
    # is_current may differ if the resolved tier differs, so compare the
    # catalogue fields only.
    for k in _SPEC_KEYS - {"is_current"}:
        assert grace[k] == enforce[k], k


# ── API endpoint ─────────────────────────────────────────────────────────


def test_api_returns_known_tier(client, ent):
    rv = client.get("/api/entitlement/tier-spec?tier=cloud_pro")
    assert rv.status_code == 200
    body = rv.get_json()
    assert set(body.keys()) == _SPEC_KEYS
    assert body["id"] == ent.TIER_CLOUD_PRO
    assert body["label"] == "Pro"
    assert body["is_paid"] is True
    assert body["unlocks_paid_runtimes"] is True


def test_api_lowercases_query(client, ent):
    rv = client.get("/api/entitlement/tier-spec?tier=ENTERPRISE")
    assert rv.status_code == 200
    assert rv.get_json()["id"] == ent.TIER_ENTERPRISE


def test_api_trims_query(client, ent):
    rv = client.get("/api/entitlement/tier-spec?tier=%20%20cloud_starter%20%20")
    assert rv.status_code == 200
    assert rv.get_json()["id"] == ent.TIER_CLOUD_STARTER


def test_api_missing_arg_is_400(client):
    rv = client.get("/api/entitlement/tier-spec")
    assert rv.status_code == 400
    assert "error" in rv.get_json()


def test_api_blank_arg_is_400(client):
    rv = client.get("/api/entitlement/tier-spec?tier=")
    assert rv.status_code == 400
    assert "error" in rv.get_json()


def test_api_unknown_tier_is_404_and_echoes_id(client):
    rv = client.get("/api/entitlement/tier-spec?tier=nonsense_xyz")
    assert rv.status_code == 404
    body = rv.get_json()
    assert body.get("tier") == "nonsense_xyz"
    assert "error" in body


def test_api_every_known_tier_round_trips(client, ent):
    for tier in ent._TIER_ORDER:
        rv = client.get(f"/api/entitlement/tier-spec?tier={tier}")
        assert rv.status_code == 200, tier
        assert rv.get_json()["id"] == tier, tier


def test_api_never_5xxs_when_resolver_fails(client, ent, monkeypatch):
    # If the resolver itself errors, the catalogue row should still answer
    # (is_current degrades to False for non-OSS tiers, but the row renders).
    def _boom(*a, **kw):
        raise RuntimeError("simulated resolver failure")

    monkeypatch.setattr(ent, "get_entitlement", _boom)
    rv = client.get("/api/entitlement/tier-spec?tier=cloud_pro")
    assert rv.status_code == 200
    body = rv.get_json()
    assert body["id"] == ent.TIER_CLOUD_PRO
    assert body["is_current"] is False
