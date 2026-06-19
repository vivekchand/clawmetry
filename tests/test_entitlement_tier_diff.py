"""Tests for ``Entitlement.next_tier_diff()`` + ``previous_tier_diff()``.

These methods bundle ``next_purchasable_tier`` + ``upgrade_diff`` (and the
mirror for downgrade) into a single payload so the paywall "Upgrade to ___" /
"Cancelling drops you to ___" CTAs render off a single ``/api/entitlement``
read instead of chaining two HTTP calls.

Pins:
  * the shape returned by the methods
  * the ceiling / floor short-circuit (None at Enterprise / OSS-free)
  * agreement with the lower-level ``upgrade_diff`` / ``downgrade_diff`` paths
  * surfacing on ``to_dict()`` + ``/api/entitlement`` so the dashboard's
    one-call CTA contract stays wired
  * the never-raise contract under a flaky resolver
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


# ── shape ────────────────────────────────────────────────────────────────────


def test_next_tier_diff_shape_matches_upgrade_diff(ent):
    e = ent._build(ent.TIER_OSS, "oss")
    diff = e.next_tier_diff()
    assert diff is not None
    assert set(diff) == {"target", "added_features", "added_runtimes"}
    assert diff["target"] == e.next_purchasable_tier()
    # exactly what upgrade_diff(next_tier) would have returned
    assert diff == e.upgrade_diff(e.next_purchasable_tier())


def test_previous_tier_diff_shape_matches_downgrade_diff(ent):
    e = ent._build(ent.TIER_CLOUD_PRO, "cloud")
    diff = e.previous_tier_diff()
    assert diff is not None
    assert set(diff) == {"target", "lost_features", "lost_runtimes"}
    assert diff["target"] == e.previous_purchasable_tier()
    assert diff == e.downgrade_diff(e.previous_purchasable_tier())


# ── ceiling / floor short-circuit ────────────────────────────────────────────


def test_enterprise_has_no_next_tier_diff(ent):
    e = ent._build(ent.TIER_ENTERPRISE, "license")
    assert e.next_tier_diff() is None


def test_oss_has_no_previous_tier_diff(ent):
    # OSS is already the floor; there's no purchasable tier below it.
    e = ent._build(ent.TIER_OSS, "oss")
    assert e.previous_tier_diff() is None


def test_cloud_free_has_no_previous_tier_diff(ent):
    # cloud_free sits at the same rank-0 floor as oss; the cancellation CTA
    # has nothing to advertise.
    e = ent._build(ent.TIER_CLOUD_FREE, "cloud")
    assert e.previous_tier_diff() is None


# ── content sanity ───────────────────────────────────────────────────────────


def test_oss_next_tier_diff_unlocks_starter_features(ent):
    diff = ent._build(ent.TIER_OSS, "oss").next_tier_diff()
    assert diff is not None
    assert diff["target"] == ent.TIER_CLOUD_STARTER
    # an OSS install has zero paid features; everything in STARTER_FEATURES
    # should appear in the added set.
    added = set(diff["added_features"])
    assert ent.STARTER_FEATURES <= added


def test_cloud_pro_previous_tier_diff_loses_pro_only_features(ent):
    # Downgrading cloud_pro -> cloud_starter strips PRO_ONLY_FEATURES.
    diff = ent._build(ent.TIER_CLOUD_PRO, "cloud").previous_tier_diff()
    assert diff is not None
    assert diff["target"] == ent.TIER_CLOUD_STARTER
    lost = set(diff["lost_features"])
    assert ent.PRO_ONLY_FEATURES <= lost


def test_cloud_starter_previous_tier_diff_targets_cloud_free(ent):
    # A cloud-sourced starter install cancels to cloud_free, not oss.
    e = ent._build(ent.TIER_CLOUD_STARTER, "cloud")
    diff = e.previous_tier_diff()
    assert diff is not None
    assert diff["target"] == ent.TIER_CLOUD_FREE


def test_self_hosted_pro_previous_tier_diff_targets_self_hosted_floor(ent):
    # A license-sourced pro install downgrades within the self-hosted cluster.
    e = ent._build(ent.TIER_PRO, "license")
    diff = e.previous_tier_diff()
    assert diff is not None
    # rank-1 cluster only has cloud_starter, so source-aware fallback returns
    # that as the next purchasable target.
    assert diff["target"] == e.previous_purchasable_tier()


# ── to_dict / API surface ────────────────────────────────────────────────────


def test_to_dict_carries_next_tier_diff_for_oss(ent):
    payload = ent._oss_free().to_dict()
    assert "next_tier_diff" in payload
    diff = payload["next_tier_diff"]
    assert diff is not None
    assert diff["target"] == payload["next_tier"]
    assert "added_features" in diff
    assert "added_runtimes" in diff


def test_to_dict_carries_prev_tier_diff_None_at_floor(ent):
    payload = ent._oss_free().to_dict()
    assert "prev_tier_diff" in payload
    assert payload["prev_tier_diff"] is None


def test_to_dict_carries_prev_tier_diff_for_paid(ent):
    payload = ent._build(ent.TIER_CLOUD_PRO, "cloud").to_dict()
    diff = payload["prev_tier_diff"]
    assert diff is not None
    assert diff["target"] == payload["prev_tier"]
    assert "lost_features" in diff
    assert "lost_runtimes" in diff


def test_to_dict_omits_next_tier_diff_at_enterprise(ent):
    payload = ent._build(ent.TIER_ENTERPRISE, "license").to_dict()
    assert payload["next_tier_diff"] is None


def test_api_entitlement_surfaces_next_tier_diff(client, ent):
    rv = client.get("/api/entitlement")
    assert rv.status_code == 200
    body = rv.get_json()
    assert "next_tier_diff" in body
    assert "prev_tier_diff" in body
    # OSS-default fixture: starter is the next purchasable tier.
    assert body["next_tier_diff"] is not None
    assert body["next_tier_diff"]["target"] == ent.TIER_CLOUD_STARTER
    # OSS is at the floor; no downgrade CTA to render.
    assert body["prev_tier_diff"] is None


# ── module-level helpers ─────────────────────────────────────────────────────


def test_module_level_next_tier_diff_matches_method(ent):
    assert ent.next_tier_diff() == ent.get_entitlement().next_tier_diff()


def test_module_level_previous_tier_diff_matches_method(ent):
    assert ent.previous_tier_diff() == ent.get_entitlement().previous_tier_diff()


# ── never-raise ──────────────────────────────────────────────────────────────


def test_next_tier_diff_swallows_resolver_failure(monkeypatch, ent):
    def boom(*_, **__):
        raise RuntimeError("synthetic")

    # Force the per-instance resolver to blow up; the method must return None.
    e = ent._build(ent.TIER_OSS, "oss")
    monkeypatch.setattr(type(e), "next_purchasable_tier", lambda self: (_ for _ in ()).throw(RuntimeError("synthetic")))
    assert e.next_tier_diff() is None


def test_previous_tier_diff_swallows_resolver_failure(monkeypatch, ent):
    e = ent._build(ent.TIER_CLOUD_PRO, "cloud")
    monkeypatch.setattr(
        type(e),
        "previous_purchasable_tier",
        lambda self: (_ for _ in ()).throw(RuntimeError("synthetic")),
    )
    assert e.previous_tier_diff() is None


def test_module_level_next_tier_diff_never_raises(monkeypatch, ent):
    def boom(*_, **__):
        raise RuntimeError("synthetic")

    monkeypatch.setattr(ent, "get_entitlement", boom)
    assert ent.next_tier_diff() is None


def test_module_level_previous_tier_diff_never_raises(monkeypatch, ent):
    def boom(*_, **__):
        raise RuntimeError("synthetic")

    monkeypatch.setattr(ent, "get_entitlement", boom)
    assert ent.previous_tier_diff() is None
