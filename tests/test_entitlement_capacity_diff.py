"""Tests for ``Entitlement.capacity_diff`` + the module-level helper +
``GET /api/entitlement/capacity-diff`` + the ``next_tier_capacity_diff`` /
``prev_tier_capacity_diff`` surfacing on ``to_dict``.

``upgrade_diff`` / ``downgrade_diff`` enumerate added / lost features and
runtimes. ``capacity_diff`` is their direction-agnostic companion for the
three capacity axes: channel cap, retention window, node cap. The dashboard
CTA card reads off this single primitive instead of re-deriving per-tier
caps in JavaScript.

Pins:
  * the ``{before, after, delta, unlocked, locked}`` triple shape per axis
  * the unlimited (``None``) sentinel semantics
  * the never-raise contract on bad input
  * symmetry with the existing upgrade-diff / preview wiring
"""
from __future__ import annotations

import importlib

import pytest
from flask import Flask


@pytest.fixture
def ent(monkeypatch, tmp_path):
    # Grace mode by default -- matches every other entitlement test fixture
    # in the suite. ``capacity_diff`` is a pure-data primitive; ``before``
    # comes off the entitlement, so grace mode does affect the input.
    monkeypatch.delenv("CLAWMETRY_ENFORCE", raising=False)
    monkeypatch.setenv("HOME", str(tmp_path))
    import clawmetry.entitlements as e

    importlib.reload(e)
    e.invalidate()
    yield e
    e.invalidate()


@pytest.fixture
def enforced(monkeypatch, tmp_path):
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
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


# -- axis-triple shape ------------------------------------------------------


def test_axis_triple_shape(enforced):
    diff = enforced._oss_free().capacity_diff(enforced.TIER_CLOUD_STARTER)
    for axis in ("channel_limit", "retention_days", "node_limit"):
        assert axis in diff, axis
        triple = diff[axis]
        assert set(triple) == {"before", "after", "delta", "unlocked", "locked"}


def test_capacity_diff_returns_target(enforced):
    diff = enforced._oss_free().capacity_diff(enforced.TIER_CLOUD_PRO)
    assert diff["target"] == enforced.TIER_CLOUD_PRO


# -- oss -> starter under enforce ------------------------------------------


def test_oss_to_starter_unlocks_channel_cap(enforced):
    diff = enforced._oss_free().capacity_diff(enforced.TIER_CLOUD_STARTER)
    triple = diff["channel_limit"]
    # OSS sits at the free channel ceiling; starter removes it.
    assert triple["before"] == enforced._FREE_CHANNEL_LIMIT
    assert triple["after"] is None
    assert triple["delta"] is None  # unlimited side -> no finite delta
    assert triple["unlocked"] is True
    assert triple["locked"] is False


def test_oss_to_starter_grows_retention(enforced):
    diff = enforced._oss_free().capacity_diff(enforced.TIER_CLOUD_STARTER)
    triple = diff["retention_days"]
    # 7d -> 30d is a finite delta on both sides; nothing unlocked.
    assert triple["before"] == 7
    assert triple["after"] == 30
    assert triple["delta"] == 23
    assert triple["unlocked"] is False
    assert triple["locked"] is False


def test_oss_to_starter_unlocks_node_cap(enforced):
    diff = enforced._oss_free().capacity_diff(enforced.TIER_CLOUD_STARTER)
    triple = diff["node_limit"]
    assert triple["before"] == enforced._FREE_NODE_LIMIT
    assert triple["after"] is None
    assert triple["delta"] is None
    assert triple["unlocked"] is True
    assert triple["locked"] is False


# -- starter -> pro: only retention moves; channel / node already unlimited


def test_starter_to_pro_only_channel_already_unlimited(enforced):
    # Build the Starter with an explicit unlimited node cap so the channel
    # axis is the only one that's "both sides unlimited" -- the node axis
    # is license-bound so a default ``_build`` carries node_limit=1.
    e = enforced._build(enforced.TIER_CLOUD_STARTER, "cloud", node_limit=None)
    diff = e.capacity_diff(enforced.TIER_CLOUD_PRO)
    # channel: both sides unlimited at Starter and Pro.
    triple = diff["channel_limit"]
    assert triple["before"] is None and triple["after"] is None
    assert triple["delta"] is None
    assert triple["unlocked"] is False and triple["locked"] is False
    # node: both sides unlimited too (explicit node_limit=None above).
    triple = diff["node_limit"]
    assert triple["before"] is None and triple["after"] is None
    assert triple["delta"] is None
    assert triple["unlocked"] is False and triple["locked"] is False
    # Retention grows 30 -> 90.
    r = diff["retention_days"]
    assert r["before"] == 30 and r["after"] == 90
    assert r["delta"] == 60
    assert not r["unlocked"] and not r["locked"]


def test_starter_default_node_cap_unlocks_on_upgrade_to_pro(enforced):
    # Default ``_build`` carries node_limit=1 (the license-bound default).
    # Upgrading to Pro removes the static cap.
    e = enforced._build(enforced.TIER_CLOUD_STARTER, "cloud")
    n = e.capacity_diff(enforced.TIER_CLOUD_PRO)["node_limit"]
    assert n["before"] == 1
    assert n["after"] is None
    assert n["delta"] is None
    assert n["unlocked"] is True and n["locked"] is False


# -- enterprise removes the retention cap too ------------------------------


def test_cloud_pro_to_enterprise_unlocks_retention(enforced):
    e = enforced._build(enforced.TIER_CLOUD_PRO, "cloud")
    diff = e.capacity_diff(enforced.TIER_ENTERPRISE)
    r = diff["retention_days"]
    assert r["before"] == 90 and r["after"] is None
    assert r["delta"] is None
    assert r["unlocked"] is True and r["locked"] is False


# -- downgrade direction ---------------------------------------------------


def test_starter_to_oss_locks_channel_cap(enforced):
    e = enforced._build(enforced.TIER_CLOUD_STARTER, "cloud")
    diff = e.capacity_diff(enforced.TIER_OSS)
    triple = diff["channel_limit"]
    assert triple["before"] is None  # was unlimited at Starter
    assert triple["after"] == enforced._FREE_CHANNEL_LIMIT
    assert triple["delta"] is None
    assert triple["unlocked"] is False
    assert triple["locked"] is True


def test_cloud_pro_to_starter_loses_retention(enforced):
    e = enforced._build(enforced.TIER_CLOUD_PRO, "cloud")
    diff = e.capacity_diff(enforced.TIER_CLOUD_STARTER)
    r = diff["retention_days"]
    assert r["before"] == 90 and r["after"] == 30
    assert r["delta"] == -60
    assert not r["unlocked"] and not r["locked"]


def test_enterprise_to_pro_locks_retention(enforced):
    e = enforced._build(enforced.TIER_ENTERPRISE, "license")
    diff = e.capacity_diff(enforced.TIER_CLOUD_PRO)
    r = diff["retention_days"]
    assert r["before"] is None and r["after"] == 90
    assert r["delta"] is None
    assert r["unlocked"] is False and r["locked"] is True


# -- license-bound node_limit honoured as the "before" side ---------------


def test_starter_with_license_node_cap_carries_through(enforced):
    e = enforced._build(enforced.TIER_CLOUD_STARTER, "cloud", node_limit=10)
    diff = e.capacity_diff(enforced.TIER_CLOUD_PRO)
    n = diff["node_limit"]
    # license-bound cap survives on the "before" side; Pro static cap is
    # the unlimited sentinel.
    assert n["before"] == 10
    assert n["after"] is None
    assert n["unlocked"] is True


# -- self-diff is a no-op on every axis -----------------------------------


def test_pro_to_pro_is_noop(enforced):
    # Match the per-tier static caps exactly (node unlimited at Pro) so the
    # self-diff lands as a true no-op on every axis.
    e = enforced._build(enforced.TIER_CLOUD_PRO, "cloud", node_limit=None)
    diff = e.capacity_diff(enforced.TIER_CLOUD_PRO)
    for axis in ("channel_limit", "retention_days", "node_limit"):
        triple = diff[axis]
        assert triple["before"] == triple["after"]
        assert triple["unlocked"] is False
        assert triple["locked"] is False
        if triple["before"] is None:
            assert triple["delta"] is None
        else:
            assert triple["delta"] == 0


# -- fallback on unknown / blank target ------------------------------------


def test_unknown_target_returns_axes_none(enforced):
    diff = enforced._oss_free().capacity_diff("nonsense_tier_xyz")
    assert diff["target"] == "nonsense_tier_xyz"
    assert diff["channel_limit"] is None
    assert diff["retention_days"] is None
    assert diff["node_limit"] is None


def test_empty_target_returns_axes_none(enforced):
    diff = enforced._oss_free().capacity_diff("")
    assert diff["target"] == ""
    assert diff["channel_limit"] is None
    assert diff["retention_days"] is None
    assert diff["node_limit"] is None


def test_target_is_lowercased(enforced):
    # The /api/tiers route emits canonical ids, but a hand-rolled query
    # parameter must still resolve.
    diff = enforced._oss_free().capacity_diff("CLOUD_STARTER")
    assert diff["target"] == enforced.TIER_CLOUD_STARTER
    assert diff["channel_limit"]["unlocked"] is True


# -- grace mode collapses the "before" side to unlimited -----------------


def test_grace_mode_oss_to_starter_unlocked_is_false_under_grace(ent):
    # Under grace the resolved entitlement reports ``channel_limit() is None``
    # because there's no live cap. So the upgrade-CTA shape says "both sides
    # unlimited; no transition" -- the right answer pre-enforce.
    diff = ent._oss_free().capacity_diff(ent.TIER_CLOUD_STARTER)
    assert diff["channel_limit"]["before"] is None
    assert diff["channel_limit"]["after"] is None
    assert diff["channel_limit"]["unlocked"] is False
    assert diff["channel_limit"]["locked"] is False


# -- next_tier_capacity_diff / previous_tier_capacity_diff ---------------


def test_next_tier_capacity_diff_targets_next_purchasable(enforced):
    e = enforced._oss_free()
    diff = e.next_tier_capacity_diff()
    assert diff is not None
    assert diff["target"] == e.next_purchasable_tier()
    assert diff == e.capacity_diff(e.next_purchasable_tier())


def test_previous_tier_capacity_diff_targets_previous_purchasable(enforced):
    e = enforced._build(enforced.TIER_CLOUD_PRO, "cloud")
    diff = e.previous_tier_capacity_diff()
    assert diff is not None
    assert diff["target"] == e.previous_purchasable_tier()
    assert diff == e.capacity_diff(e.previous_purchasable_tier())


def test_enterprise_has_no_next_tier_capacity_diff(enforced):
    e = enforced._build(enforced.TIER_ENTERPRISE, "license")
    assert e.next_tier_capacity_diff() is None


def test_oss_has_no_prev_tier_capacity_diff(enforced):
    e = enforced._oss_free()
    assert e.previous_tier_capacity_diff() is None


# -- to_dict surfacing ----------------------------------------------------


def test_to_dict_carries_next_tier_capacity_diff(ent):
    payload = ent._oss_free().to_dict()
    assert "next_tier_capacity_diff" in payload
    assert "prev_tier_capacity_diff" in payload
    # OSS-default fixture: starter is the next purchasable tier.
    diff = payload["next_tier_capacity_diff"]
    assert diff is not None
    assert diff["target"] == payload["next_tier"]
    assert "channel_limit" in diff


def test_to_dict_prev_tier_capacity_diff_None_at_floor(ent):
    payload = ent._oss_free().to_dict()
    assert payload["prev_tier_capacity_diff"] is None


def test_to_dict_next_tier_capacity_diff_None_at_enterprise(ent):
    payload = ent._build(ent.TIER_ENTERPRISE, "license").to_dict()
    assert payload["next_tier_capacity_diff"] is None


# -- module-level helpers -------------------------------------------------


def test_module_level_capacity_diff_matches_method(enforced):
    target = enforced.TIER_CLOUD_PRO
    assert enforced.capacity_diff(target) == enforced.get_entitlement().capacity_diff(target)


def test_module_level_next_tier_capacity_diff_matches_method(enforced):
    assert (
        enforced.next_tier_capacity_diff()
        == enforced.get_entitlement().next_tier_capacity_diff()
    )


def test_module_level_previous_tier_capacity_diff_matches_method(enforced):
    assert (
        enforced.previous_tier_capacity_diff()
        == enforced.get_entitlement().previous_tier_capacity_diff()
    )


# -- never-raise contract -------------------------------------------------


def test_capacity_diff_swallows_resolver_failure(monkeypatch, enforced):
    e = enforced._oss_free()
    monkeypatch.setattr(
        type(e),
        "channel_limit",
        lambda self: (_ for _ in ()).throw(RuntimeError("synthetic")),
    )
    out = e.capacity_diff(enforced.TIER_CLOUD_PRO)
    assert out["target"] == enforced.TIER_CLOUD_PRO
    assert out["channel_limit"] is None
    assert out["retention_days"] is None
    assert out["node_limit"] is None


def test_module_capacity_diff_never_raises(monkeypatch, enforced):
    def boom(*_, **__):
        raise RuntimeError("synthetic")

    monkeypatch.setattr(enforced, "get_entitlement", boom)
    out = enforced.capacity_diff(enforced.TIER_CLOUD_PRO)
    assert out["target"] == enforced.TIER_CLOUD_PRO
    assert out["channel_limit"] is None
    assert out["retention_days"] is None
    assert out["node_limit"] is None


def test_module_next_tier_capacity_diff_never_raises(monkeypatch, enforced):
    def boom(*_, **__):
        raise RuntimeError("synthetic")

    monkeypatch.setattr(enforced, "get_entitlement", boom)
    assert enforced.next_tier_capacity_diff() is None


def test_module_previous_tier_capacity_diff_never_raises(monkeypatch, enforced):
    def boom(*_, **__):
        raise RuntimeError("synthetic")

    monkeypatch.setattr(enforced, "get_entitlement", boom)
    assert enforced.previous_tier_capacity_diff() is None


# -- API surface ----------------------------------------------------------


def test_api_returns_diff_for_starter(client, ent):
    rv = client.get(f"/api/entitlement/capacity-diff?target={ent.TIER_CLOUD_STARTER}")
    assert rv.status_code == 200
    body = rv.get_json()
    assert body["target"] == ent.TIER_CLOUD_STARTER
    for axis in ("channel_limit", "retention_days", "node_limit"):
        assert axis in body


def test_api_empty_target_returns_axes_none_200(client):
    rv = client.get("/api/entitlement/capacity-diff")
    assert rv.status_code == 200
    body = rv.get_json()
    assert body["target"] == ""
    assert body["channel_limit"] is None
    assert body["retention_days"] is None
    assert body["node_limit"] is None


def test_api_unknown_target_returns_axes_none_200(client):
    rv = client.get("/api/entitlement/capacity-diff?target=nonsense_tier_xyz")
    assert rv.status_code == 200
    body = rv.get_json()
    assert body["target"] == "nonsense_tier_xyz"
    assert body["channel_limit"] is None
    assert body["retention_days"] is None
    assert body["node_limit"] is None


def test_api_entitlement_surfaces_capacity_diff_fields(client, ent):
    # /api/entitlement should carry the new fields so the dashboard reads
    # one payload instead of chaining two HTTP calls.
    rv = client.get("/api/entitlement")
    assert rv.status_code == 200
    body = rv.get_json()
    assert "next_tier_capacity_diff" in body
    assert "prev_tier_capacity_diff" in body
    assert body["next_tier_capacity_diff"] is not None
    assert body["prev_tier_capacity_diff"] is None
