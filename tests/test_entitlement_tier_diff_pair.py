"""Tests for ``clawmetry.entitlements.tier_diff(from, to)`` + the
``GET /api/entitlement/tier-diff`` endpoint.

Generalises :func:`upgrade_diff` / :func:`downgrade_diff` (which pin one
endpoint to the resolved entitlement) to ANY pair of known tiers so a
"Compare A vs B" pricing-page widget can render any transition without
first switching the resolver.

Pins:

* full payload shape (from/to, direction tag, added/lost lists,
  capacity_changes dict for all three axes)
* direction tag covers upgrade / downgrade / lateral / identity
* swap-the-endpoints invariant -- ``added_features`` mirrors the swapped
  ``lost_features`` byte-for-byte (and same for runtimes)
* trial accepted as a hypothetical endpoint even though it is not
  purchasable
* identity-tier diff returns empty deltas
* enterprise vs free unlocks the enterprise-only feature set
* unknown tier id returns ``None`` (and ``404`` on the endpoint)
* never raises
* API surface: 400 on missing args, 404 on unknown ids, 200 on a happy
  path with the expected shape
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


_EXPECTED_KEYS = {
    "from",
    "from_label",
    "from_rank",
    "to",
    "to_label",
    "to_rank",
    "direction",
    "added_features",
    "lost_features",
    "added_runtimes",
    "lost_runtimes",
    "capacity_changes",
}


# ── shape ────────────────────────────────────────────────────────────────────


def test_tier_diff_shape(ent):
    body = ent.tier_diff(ent.TIER_OSS, ent.TIER_CLOUD_PRO)
    assert body is not None
    assert set(body.keys()) == _EXPECTED_KEYS
    assert body["from"] == ent.TIER_OSS
    assert body["to"] == ent.TIER_CLOUD_PRO
    assert body["from_label"] == ent.tier_label(ent.TIER_OSS)
    assert body["to_label"] == ent.tier_label(ent.TIER_CLOUD_PRO)
    assert body["from_rank"] == ent.tier_rank(ent.TIER_OSS)
    assert body["to_rank"] == ent.tier_rank(ent.TIER_CLOUD_PRO)
    for axis in ("channel_limit", "retention_days", "node_limit"):
        cap = body["capacity_changes"][axis]
        assert set(cap.keys()) == {"before", "after", "delta", "unlocked", "locked"}


def test_added_and_lost_lists_are_sorted(ent):
    body = ent.tier_diff(ent.TIER_OSS, ent.TIER_ENTERPRISE)
    assert body["added_features"] == sorted(body["added_features"])
    assert body["added_runtimes"] == sorted(body["added_runtimes"])
    # downgrade direction also sorts.
    body = ent.tier_diff(ent.TIER_ENTERPRISE, ent.TIER_OSS)
    assert body["lost_features"] == sorted(body["lost_features"])
    assert body["lost_runtimes"] == sorted(body["lost_runtimes"])


# ── direction tag ────────────────────────────────────────────────────────────


def test_direction_upgrade(ent):
    body = ent.tier_diff(ent.TIER_OSS, ent.TIER_CLOUD_PRO)
    assert body["direction"] == "upgrade"


def test_direction_downgrade(ent):
    body = ent.tier_diff(ent.TIER_ENTERPRISE, ent.TIER_CLOUD_STARTER)
    assert body["direction"] == "downgrade"


def test_direction_identity(ent):
    body = ent.tier_diff(ent.TIER_CLOUD_PRO, ent.TIER_CLOUD_PRO)
    assert body["direction"] == "identity"
    # identity collapses to empty deltas on every axis.
    assert body["added_features"] == []
    assert body["lost_features"] == []
    assert body["added_runtimes"] == []
    assert body["lost_runtimes"] == []


def test_direction_lateral_same_rank(ent):
    # cloud_pro and pro both sit at rank 2; the diff is a lateral move.
    body = ent.tier_diff(ent.TIER_CLOUD_PRO, ent.TIER_PRO)
    assert body["direction"] == "lateral"
    # the feature/runtime grants happen to match across the rank-2 cluster,
    # so a lateral leaves the deltas empty.
    assert body["added_features"] == []
    assert body["lost_features"] == []


def test_direction_lateral_oss_to_cloud_free(ent):
    # OSS and cloud_free are both rank 0 -- lateral with empty deltas.
    body = ent.tier_diff(ent.TIER_OSS, ent.TIER_CLOUD_FREE)
    assert body["direction"] == "lateral"
    assert body["added_features"] == []
    assert body["lost_features"] == []
    assert body["added_runtimes"] == []
    assert body["lost_runtimes"] == []


# ── content sanity ───────────────────────────────────────────────────────────


def test_oss_to_starter_unlocks_starter_features(ent):
    body = ent.tier_diff(ent.TIER_OSS, ent.TIER_CLOUD_STARTER)
    added = set(body["added_features"])
    assert ent.STARTER_FEATURES <= added
    # Starter does not grant Pro-only features.
    assert ent.PRO_ONLY_FEATURES.isdisjoint(added)


def test_cloud_pro_to_starter_loses_pro_only_features(ent):
    body = ent.tier_diff(ent.TIER_CLOUD_PRO, ent.TIER_CLOUD_STARTER)
    assert body["direction"] == "downgrade"
    lost = set(body["lost_features"])
    assert ent.PRO_ONLY_FEATURES <= lost


def test_oss_to_enterprise_unlocks_enterprise_features(ent):
    body = ent.tier_diff(ent.TIER_OSS, ent.TIER_ENTERPRISE)
    added = set(body["added_features"])
    # Enterprise grants everything Pro grants AND the enterprise-only set.
    assert ent.PAID_FEATURES <= added
    assert ent.ENTERPRISE_FEATURES <= added


def test_cloud_pro_to_enterprise_unlocks_only_enterprise_extras(ent):
    body = ent.tier_diff(ent.TIER_CLOUD_PRO, ent.TIER_ENTERPRISE)
    added = set(body["added_features"])
    # Cloud Pro already has every paid feature; only the enterprise set is new.
    assert added == set(ent.ENTERPRISE_FEATURES)
    assert body["lost_features"] == []


def test_oss_to_starter_does_not_unlock_paid_runtimes(ent):
    # Starter is a paid tier but the runtime grant is on/off across all paid
    # tiers, not graded -- so any move from rank-0 to a paid tier flips on the
    # full paid-runtime catalog.
    body = ent.tier_diff(ent.TIER_OSS, ent.TIER_CLOUD_STARTER)
    added = set(body["added_runtimes"])
    assert ent.PAID_RUNTIMES <= added
    # Free runtimes are already on at both endpoints, so they are NOT added.
    assert ent.FREE_RUNTIMES.isdisjoint(added)


def test_capacity_changes_channel_unlocked_oss_to_pro(ent):
    body = ent.tier_diff(ent.TIER_OSS, ent.TIER_CLOUD_PRO)
    cap = body["capacity_changes"]["channel_limit"]
    assert cap["before"] == 3
    assert cap["after"] is None
    assert cap["unlocked"] is True
    assert cap["locked"] is False


def test_capacity_changes_retention_finite_delta(ent):
    body = ent.tier_diff(ent.TIER_CLOUD_STARTER, ent.TIER_CLOUD_PRO)
    cap = body["capacity_changes"]["retention_days"]
    assert cap["before"] == 30
    assert cap["after"] == 90
    assert cap["delta"] == 60
    assert cap["unlocked"] is False
    assert cap["locked"] is False


def test_capacity_changes_retention_locked_pro_to_starter(ent):
    body = ent.tier_diff(ent.TIER_ENTERPRISE, ent.TIER_CLOUD_STARTER)
    cap = body["capacity_changes"]["retention_days"]
    # Enterprise has unlimited retention -> Starter has 30d. Locked flips.
    assert cap["before"] is None
    assert cap["after"] == 30
    assert cap["locked"] is True
    assert cap["unlocked"] is False


# ── trial as endpoint ────────────────────────────────────────────────────────


def test_trial_accepted_as_destination(ent):
    body = ent.tier_diff(ent.TIER_OSS, ent.TIER_TRIAL)
    assert body is not None
    # trial carries the full paid feature set, same as Pro.
    added = set(body["added_features"])
    assert ent.PAID_FEATURES <= added


def test_trial_accepted_as_source(ent):
    body = ent.tier_diff(ent.TIER_TRIAL, ent.TIER_OSS)
    assert body is not None
    lost = set(body["lost_features"])
    assert ent.PAID_FEATURES <= lost


# ── swap-the-endpoints invariant ────────────────────────────────────────────


def test_swap_endpoints_added_mirrors_lost_features(ent):
    forward = ent.tier_diff(ent.TIER_OSS, ent.TIER_CLOUD_PRO)
    reverse = ent.tier_diff(ent.TIER_CLOUD_PRO, ent.TIER_OSS)
    assert forward["added_features"] == reverse["lost_features"]
    assert forward["lost_features"] == reverse["added_features"]


def test_swap_endpoints_added_mirrors_lost_runtimes(ent):
    forward = ent.tier_diff(ent.TIER_OSS, ent.TIER_CLOUD_PRO)
    reverse = ent.tier_diff(ent.TIER_CLOUD_PRO, ent.TIER_OSS)
    assert forward["added_runtimes"] == reverse["lost_runtimes"]
    assert forward["lost_runtimes"] == reverse["added_runtimes"]


def test_swap_endpoints_flips_capacity_axes(ent):
    forward = ent.tier_diff(ent.TIER_OSS, ent.TIER_CLOUD_PRO)
    reverse = ent.tier_diff(ent.TIER_CLOUD_PRO, ent.TIER_OSS)
    for axis in ("channel_limit", "retention_days", "node_limit"):
        f = forward["capacity_changes"][axis]
        r = reverse["capacity_changes"][axis]
        assert f["before"] == r["after"]
        assert f["after"] == r["before"]
        assert f["unlocked"] == r["locked"]
        assert f["locked"] == r["unlocked"]


def test_swap_endpoints_flips_direction(ent):
    forward = ent.tier_diff(ent.TIER_OSS, ent.TIER_CLOUD_PRO)
    reverse = ent.tier_diff(ent.TIER_CLOUD_PRO, ent.TIER_OSS)
    assert forward["direction"] == "upgrade"
    assert reverse["direction"] == "downgrade"


# ── consistency vs current-relative helpers ──────────────────────────────────


def test_oss_upgrade_diff_matches_tier_diff_from_oss(ent):
    # When `from` == the resolved entitlement, tier_diff's added_* equals
    # the current-relative upgrade_diff's added_*.
    e = ent._build(ent.TIER_OSS, "oss")
    body = ent.tier_diff(ent.TIER_OSS, ent.TIER_CLOUD_PRO)
    legacy = e.upgrade_diff(ent.TIER_CLOUD_PRO)
    assert body["added_features"] == legacy["added_features"]
    assert body["added_runtimes"] == legacy["added_runtimes"]


def test_pro_downgrade_diff_matches_tier_diff_from_pro(ent):
    e = ent._build(ent.TIER_CLOUD_PRO, "cloud")
    body = ent.tier_diff(ent.TIER_CLOUD_PRO, ent.TIER_CLOUD_STARTER)
    legacy = e.downgrade_diff(ent.TIER_CLOUD_STARTER)
    assert body["lost_features"] == legacy["lost_features"]
    assert body["lost_runtimes"] == legacy["lost_runtimes"]


# ── unknown ids ──────────────────────────────────────────────────────────────


def test_unknown_from_returns_none(ent):
    assert ent.tier_diff("not_a_tier", ent.TIER_CLOUD_PRO) is None


def test_unknown_to_returns_none(ent):
    assert ent.tier_diff(ent.TIER_OSS, "not_a_tier") is None


def test_both_unknown_returns_none(ent):
    assert ent.tier_diff("a", "b") is None


def test_empty_args_return_none(ent):
    assert ent.tier_diff("", ent.TIER_OSS) is None
    assert ent.tier_diff(ent.TIER_OSS, "") is None
    assert ent.tier_diff("", "") is None
    assert ent.tier_diff(None, None) is None  # type: ignore[arg-type]


def test_whitespace_and_case_normalised(ent):
    # mixed-case + surrounding whitespace must still resolve.
    body = ent.tier_diff("  OSS  ", "Cloud_Pro")
    assert body is not None
    assert body["from"] == ent.TIER_OSS
    assert body["to"] == ent.TIER_CLOUD_PRO


# ── never-raise ──────────────────────────────────────────────────────────────


def test_never_raises_on_garbage(ent):
    # The helper must never raise on garbage input -- a paywall surface
    # short-circuits to None instead of 500-ing.
    assert ent.tier_diff(object(), object()) is None  # type: ignore[arg-type]
    assert ent.tier_diff(123, 456) is None  # type: ignore[arg-type]


# ── API surface ──────────────────────────────────────────────────────────────


def test_api_tier_diff_ok(client, ent):
    rv = client.get(
        f"/api/entitlement/tier-diff?from={ent.TIER_OSS}&to={ent.TIER_CLOUD_PRO}"
    )
    assert rv.status_code == 200
    body = rv.get_json()
    assert set(body.keys()) == _EXPECTED_KEYS
    assert body["direction"] == "upgrade"
    assert body["from"] == ent.TIER_OSS
    assert body["to"] == ent.TIER_CLOUD_PRO


def test_api_tier_diff_missing_from(client):
    rv = client.get("/api/entitlement/tier-diff?to=cloud_pro")
    assert rv.status_code == 400
    body = rv.get_json()
    assert body.get("error") == "missing from or to"


def test_api_tier_diff_missing_to(client):
    rv = client.get("/api/entitlement/tier-diff?from=oss")
    assert rv.status_code == 400


def test_api_tier_diff_missing_both(client):
    rv = client.get("/api/entitlement/tier-diff")
    assert rv.status_code == 400


def test_api_tier_diff_unknown_from(client):
    rv = client.get("/api/entitlement/tier-diff?from=not_a_tier&to=oss")
    assert rv.status_code == 404
    body = rv.get_json()
    assert body.get("error") == "unknown tier"
    assert body.get("from") == "not_a_tier"
    assert body.get("to") == "oss"


def test_api_tier_diff_unknown_to(client):
    rv = client.get("/api/entitlement/tier-diff?from=oss&to=not_a_tier")
    assert rv.status_code == 404


def test_api_tier_diff_identity_returns_empty_deltas(client, ent):
    rv = client.get(
        f"/api/entitlement/tier-diff?from={ent.TIER_CLOUD_PRO}&to={ent.TIER_CLOUD_PRO}"
    )
    assert rv.status_code == 200
    body = rv.get_json()
    assert body["direction"] == "identity"
    assert body["added_features"] == []
    assert body["lost_features"] == []


def test_api_tier_diff_trial_destination_ok(client, ent):
    rv = client.get(
        f"/api/entitlement/tier-diff?from={ent.TIER_OSS}&to={ent.TIER_TRIAL}"
    )
    assert rv.status_code == 200
    body = rv.get_json()
    assert body["to"] == ent.TIER_TRIAL
    assert body["direction"] == "upgrade"
