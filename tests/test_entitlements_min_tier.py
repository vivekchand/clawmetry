"""Tests for the tier-ordering primitives on :mod:`clawmetry.entitlements`.

Pins the contracts for:

* :func:`tier_label` -- human-readable label, with a graceful fallback for
  unknown ids so the UI never shows a blank pill.
* :func:`tier_rank` -- comparable rank used by the paywall to decide whether a
  click on a locked feature must route the operator through an upgrade.
* :func:`min_tier_for_feature` / :func:`min_tier_for_runtime` -- the "Available
  in ___" copy backing the lock affordance: free items resolve to ``oss``,
  paid items to their cheapest *purchasable* tier (Trial is excluded -- it is
  a promotional grant, not a price-page row).
* ``GET /api/entitlement/required-tier`` -- the matching HTTP surface, plus
  the never-raise contract on top of a flaky resolver.
* ``tier_label`` / ``tier_rank`` carried on ``/api/entitlement`` itself, so the
  dashboard's existing entitlement read keeps a single source of truth for
  copy + ordering.
"""
from __future__ import annotations

import importlib

import pytest
from flask import Flask


@pytest.fixture
def ent(monkeypatch, tmp_path):
    """Fresh entitlements module rooted at an empty tmp HOME, enforcement off."""
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


# ── tier_label ───────────────────────────────────────────────────────────────


def test_tier_label_known_ids(ent):
    assert ent.tier_label(ent.TIER_OSS) == "OSS"
    assert ent.tier_label(ent.TIER_CLOUD_FREE) == "Free"
    assert ent.tier_label(ent.TIER_CLOUD_STARTER) == "Starter"
    assert ent.tier_label(ent.TIER_CLOUD_PRO) == "Pro"
    assert ent.tier_label(ent.TIER_PRO) == "Self-hosted Pro"
    assert ent.tier_label(ent.TIER_TRIAL) == "Trial"
    assert ent.tier_label(ent.TIER_ENTERPRISE) == "Enterprise"


def test_tier_label_is_case_insensitive(ent):
    assert ent.tier_label("OSS") == "OSS"
    assert ent.tier_label("Cloud_Pro") == "Pro"


def test_tier_label_unknown_falls_back_to_title_case(ent):
    # Unknown ids still render *something* sensible so the UI never shows a
    # blank pill if a future tier slips in before the label map is updated.
    assert ent.tier_label("custom_plan") == "Custom Plan"


def test_tier_label_empty_falls_back_to_oss(ent):
    # A blank tier reads like "no info" and should match the OSS-free fallback
    # everywhere else in the resolver.
    assert ent.tier_label("") == "OSS"
    assert ent.tier_label(None) == "OSS"  # type: ignore[arg-type]


def test_every_known_tier_has_a_label(ent):
    """The label catalog must cover every TIER_* constant -- the catalogue
    conformance check the UI relies on so adding a tier without a label trips
    here, not in production."""
    canonical = {
        ent.TIER_OSS, ent.TIER_CLOUD_FREE, ent.TIER_TRIAL,
        ent.TIER_CLOUD_STARTER, ent.TIER_CLOUD_PRO, ent.TIER_PRO,
        ent.TIER_ENTERPRISE,
    }
    assert canonical <= set(ent.TIER_LABELS)


# ── tier_rank ────────────────────────────────────────────────────────────────


def test_tier_rank_orders_ladder(ent):
    assert ent.tier_rank(ent.TIER_OSS) == 0
    assert ent.tier_rank(ent.TIER_CLOUD_FREE) == 0
    assert ent.tier_rank(ent.TIER_CLOUD_STARTER) == 1
    # cloud_pro and self-hosted pro share rank 2 -- they unlock the same set.
    assert ent.tier_rank(ent.TIER_CLOUD_PRO) == 2
    assert ent.tier_rank(ent.TIER_PRO) == 2
    assert ent.tier_rank(ent.TIER_TRIAL) == 2
    assert ent.tier_rank(ent.TIER_ENTERPRISE) == 3


def test_tier_rank_unknown_is_negative(ent):
    assert ent.tier_rank("unknown_plan") == -1
    assert ent.tier_rank("") == -1


def test_tier_rank_is_strictly_increasing_along_purchasable_ladder(ent):
    # The "Upgrade required" boolean on /api/entitlement/required-tier compares
    # ranks; if the ladder regressed (e.g. starter > pro) the upgrade CTA
    # would point operators at the *wrong* tier.
    ranks = [
        ent.tier_rank(ent.TIER_OSS),
        ent.tier_rank(ent.TIER_CLOUD_STARTER),
        ent.tier_rank(ent.TIER_CLOUD_PRO),
        ent.tier_rank(ent.TIER_ENTERPRISE),
    ]
    assert ranks == sorted(ranks)
    assert len(set(ranks)) == len(ranks)  # strictly increasing


# ── min_tier_for_feature ─────────────────────────────────────────────────────


def test_min_tier_for_feature_free(ent):
    for f in ("sessions", "overview", "nemo_governance"):
        assert ent.min_tier_for_feature(f) == ent.TIER_OSS


def test_min_tier_for_feature_starter(ent):
    # STARTER_FEATURES all resolve to cloud_starter -- the cheapest tier that
    # grants the multi_runtime/fleet/all_channels bucket.
    for f in ent.STARTER_FEATURES:
        assert ent.min_tier_for_feature(f) == ent.TIER_CLOUD_STARTER


def test_min_tier_for_feature_pro_only(ent):
    # PRO_ONLY_FEATURES require cloud_pro -- starter does not grant them.
    for f in ent.PRO_ONLY_FEATURES:
        assert ent.min_tier_for_feature(f) == ent.TIER_CLOUD_PRO


def test_min_tier_for_feature_enterprise(ent):
    for f in ent.ENTERPRISE_FEATURES:
        assert ent.min_tier_for_feature(f) == ent.TIER_ENTERPRISE


def test_min_tier_for_feature_unknown_returns_none(ent):
    # Unknown id is distinguishable from "free"; the route renders no CTA
    # rather than misleading the operator about a non-existent tier.
    assert ent.min_tier_for_feature("not_a_real_feature") is None


def test_min_tier_for_feature_empty_returns_none(ent):
    assert ent.min_tier_for_feature("") is None
    assert ent.min_tier_for_feature(None) is None  # type: ignore[arg-type]


def test_min_tier_for_feature_does_not_return_trial(ent):
    """Trial unlocks the full Pro set but is a promotional grant, not a price-
    page row. The required-tier CTA should never advertise it as the upgrade
    target."""
    for f in ent.PAID_FEATURES | ent.ENTERPRISE_FEATURES:
        assert ent.min_tier_for_feature(f) != ent.TIER_TRIAL


# ── min_tier_for_runtime ─────────────────────────────────────────────────────


def test_min_tier_for_runtime_free(ent):
    for rt in ent.FREE_RUNTIMES:
        assert ent.min_tier_for_runtime(rt) == ent.TIER_OSS


def test_min_tier_for_runtime_paid_is_starter(ent):
    # All paid runtimes unlock together via Starter's multi_runtime grant.
    for rt in ent.PAID_RUNTIMES:
        assert ent.min_tier_for_runtime(rt) == ent.TIER_CLOUD_STARTER


def test_min_tier_for_runtime_unknown_returns_none(ent):
    assert ent.min_tier_for_runtime("not_a_runtime") is None
    assert ent.min_tier_for_runtime("") is None


# ── /api/entitlement surfacing ───────────────────────────────────────────────


def test_api_entitlement_surfaces_tier_label_and_rank(client, ent):
    rv = client.get("/api/entitlement")
    assert rv.status_code == 200
    body = rv.get_json()
    assert body["tier"] == ent.TIER_OSS
    assert body["tier_label"] == "OSS"
    assert body["tier_rank"] == 0


# ── /api/entitlement/required-tier ───────────────────────────────────────────


def test_required_tier_feature_starter(client, ent):
    rv = client.get("/api/entitlement/required-tier?feature=multi_runtime")
    assert rv.status_code == 200
    body = rv.get_json()
    assert body["kind"] == "feature"
    assert body["key"] == "multi_runtime"
    assert body["required_tier"] == ent.TIER_CLOUD_STARTER
    assert body["required_tier_label"] == "Starter"
    assert body["required_tier_rank"] == 1
    assert body["current_tier"] == ent.TIER_OSS
    assert body["current_tier_rank"] == 0
    assert body["upgrade_required"] is True
    # Grace mode still flips allowed=True regardless of upgrade_required --
    # both flags carry independent information for the UI.
    assert body["allowed"] is True


def test_required_tier_feature_pro(client, ent):
    rv = client.get("/api/entitlement/required-tier?feature=self_evolve")
    body = rv.get_json()
    assert body["required_tier"] == ent.TIER_CLOUD_PRO
    assert body["required_tier_rank"] == 2
    assert body["upgrade_required"] is True


def test_required_tier_feature_enterprise(client, ent):
    rv = client.get("/api/entitlement/required-tier?feature=sso")
    body = rv.get_json()
    assert body["required_tier"] == ent.TIER_ENTERPRISE
    assert body["upgrade_required"] is True


def test_required_tier_feature_free(client, ent):
    rv = client.get("/api/entitlement/required-tier?feature=sessions")
    body = rv.get_json()
    assert body["required_tier"] == ent.TIER_OSS
    assert body["upgrade_required"] is False
    assert body["allowed"] is True


def test_required_tier_runtime_paid(client, ent):
    rv = client.get("/api/entitlement/required-tier?runtime=claude_code")
    body = rv.get_json()
    assert body["kind"] == "runtime"
    assert body["key"] == "claude_code"
    assert body["required_tier"] == ent.TIER_CLOUD_STARTER
    assert body["upgrade_required"] is True


def test_required_tier_runtime_free(client, ent):
    rv = client.get("/api/entitlement/required-tier?runtime=openclaw")
    body = rv.get_json()
    assert body["required_tier"] == ent.TIER_OSS
    assert body["upgrade_required"] is False


def test_required_tier_unknown_feature_returns_null(client, ent):
    rv = client.get("/api/entitlement/required-tier?feature=not_real")
    body = rv.get_json()
    # Unknown ids carry through as null so the UI shows no CTA at all rather
    # than advertising a tier that doesn't actually grant the missing key.
    assert body["required_tier"] is None
    assert body["required_tier_label"] is None
    assert body["upgrade_required"] is False


def test_required_tier_no_query_400(client):
    rv = client.get("/api/entitlement/required-tier")
    assert rv.status_code == 400


def test_required_tier_both_query_400(client):
    rv = client.get("/api/entitlement/required-tier?feature=sessions&runtime=openclaw")
    assert rv.status_code == 400


# ── never-raise on resolver failure ──────────────────────────────────────────


def test_required_tier_swallows_resolver_failure(monkeypatch, client, ent):
    """A flaky entitlement read must never break the paywall tooltip render --
    the route falls back to the OSS-free shape instead of 5xx."""
    def boom(*_, **__):
        raise RuntimeError("synthetic")

    monkeypatch.setattr(ent, "get_entitlement", boom)
    rv = client.get("/api/entitlement/required-tier?feature=multi_runtime")
    assert rv.status_code == 200
    body = rv.get_json()
    assert body["allowed"] is True
    assert body["current_tier"] == "oss"
    assert body["upgrade_required"] is False
