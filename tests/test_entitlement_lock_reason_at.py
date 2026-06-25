"""Tests for ``lock_reason_at(perspective_tier, item, kind=...)`` +
``GET /api/entitlement/lock-reason-at``.

What-if sibling of :func:`lock_reason` -- the lock-reason string for an
item computed as if the install were on ``perspective_tier``, not
against the live resolved entitlement. Lets a pricing-comparison
tooltip preview the exact lock sentence a downgrade-to-target would
surface in one round-trip, before the user commits.

Pins:

* the helper is independent of the live resolver -- grace mode,
  enforcement, license cache, and cloud_plan.json all have no effect
* every tier in ``_TIER_ORDER`` resolves; unknown / empty / ``None`` /
  non-string perspective ids return ``None``
* free features / free runtimes are always unlocked at every tier
* paid features / paid runtimes are locked on OSS / Cloud Free and
  unlocked at the tier ``min_tier_for_*`` reports (so the helper agrees
  with the affordability surface)
* capacity axes (``channels`` / ``retention_days`` / ``nodes``) use the
  per-tier caps (``_TIER_CHANNEL_LIMIT`` / ``_TIER_RETENTION_DAYS`` /
  ``_TIER_NODE_LIMIT``) rather than the single-node OSS default that
  ``_hypothetical_entitlement`` hands to ``feature_spec_at`` /
  ``runtime_spec_at`` -- so e.g. asking about 100 nodes from Enterprise
  is unlocked, not locked
* the helper never raises; a synthesis failure returns ``None``
* the endpoint 400s on missing ``tier=`` / no-axis / multi-axis input,
  404s on unknown tier (with ``which`` so the caller can render the
  right "unknown ..." message), and never 5xxs
* the endpoint response shape matches ``/api/entitlement/lock-reason``
  exactly (same keys, same ordering of semantics) so a paywall surface
  can swap the live endpoint for the what-if one with no reshape
"""
from __future__ import annotations

import importlib
import json

import pytest
from flask import Flask


_ROW_KEYS = {
    "key",
    "kind",
    "reason",
    "locked",
    "allowed",
    "required_tier",
    "required_tier_label",
    "required_tier_rank",
    "current_tier",
    "current_tier_rank",
    "upgrade_required",
}


@pytest.fixture
def ent(monkeypatch, tmp_path):
    """Fresh entitlements module with HOME pointed at an empty tmp dir
    so no real ~/.clawmetry/license.key or cloud_plan.json leaks in.
    Enforcement off by default (grace mode) -- ``lock_reason_at`` is
    independent of either knob, so the fixture only needs to make sure
    the live resolver does not surprise the test."""
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


# ── helper: round-trip & shape ────────────────────────────────────────────────


def test_helper_returns_string_or_none(ent):
    fid = next(iter(ent.FREE_FEATURES))
    out = ent.lock_reason_at(ent.TIER_CLOUD_PRO, fid, kind="feature")
    assert out is None or isinstance(out, str)


def test_every_tier_resolves(ent):
    """Every tier in ``_TIER_ORDER`` returns a string-or-None for some
    feature -- pins the per-tier round-trip contract."""
    paid_universe = (
        ent.STARTER_FEATURES | ent.PRO_ONLY_FEATURES | ent.ENTERPRISE_FEATURES
    )
    fid = next(iter(paid_universe))
    for tier in ent._TIER_ORDER:
        out = ent.lock_reason_at(tier, fid, kind="feature")
        assert out is None or isinstance(out, str), (tier, fid)


# ── invalid perspective tier ─────────────────────────────────────────────────


def test_unknown_tier_returns_none(ent):
    fid = next(iter(ent.FREE_FEATURES))
    assert ent.lock_reason_at("not_a_real_tier", fid, kind="feature") is None


def test_empty_tier_returns_none(ent):
    fid = next(iter(ent.FREE_FEATURES))
    assert ent.lock_reason_at("", fid, kind="feature") is None


def test_none_tier_returns_none(ent):
    fid = next(iter(ent.FREE_FEATURES))
    assert ent.lock_reason_at(None, fid, kind="feature") is None


def test_non_string_tier_returns_none(ent):
    fid = next(iter(ent.FREE_FEATURES))
    assert ent.lock_reason_at(123, fid, kind="feature") is None
    assert ent.lock_reason_at(object(), fid, kind="feature") is None


# ── normalisation ─────────────────────────────────────────────────────────────


def test_tier_is_lowercased_and_trimmed(ent):
    paid = next(iter(ent.STARTER_FEATURES))
    a = ent.lock_reason_at(ent.TIER_OSS, paid, kind="feature")
    b = ent.lock_reason_at(ent.TIER_OSS.upper(), paid, kind="feature")
    c = ent.lock_reason_at(f"  {ent.TIER_OSS}  ", paid, kind="feature")
    assert a == b == c
    assert a is not None  # paid feature is locked on OSS


# ── feature axis: free / paid / per-tier ──────────────────────────────────────


def test_free_feature_unlocked_at_every_tier(ent):
    """Free features are part of the OSS grant; the helper must return
    ``None`` at every tier in the ladder. Mirrors the same invariant on
    :func:`feature_spec_at`."""
    fid = next(iter(ent.FREE_FEATURES))
    for tier in ent._TIER_ORDER:
        assert ent.lock_reason_at(tier, fid, kind="feature") is None, (tier, fid)


def test_paid_feature_locked_at_oss(ent):
    paid_universe = (
        ent.STARTER_FEATURES | ent.PRO_ONLY_FEATURES | ent.ENTERPRISE_FEATURES
    )
    fid = next(iter(paid_universe))
    out = ent.lock_reason_at(ent.TIER_OSS, fid, kind="feature")
    assert isinstance(out, str) and out  # non-empty sentence


def test_paid_feature_unlocked_at_enterprise(ent):
    paid_universe = (
        ent.STARTER_FEATURES | ent.PRO_ONLY_FEATURES | ent.ENTERPRISE_FEATURES
    )
    for fid in paid_universe:
        out = ent.lock_reason_at(ent.TIER_ENTERPRISE, fid, kind="feature")
        assert out is None, fid


def test_starter_feature_unlocked_at_starter_locked_at_oss(ent):
    """A Starter feature is unlocked at Starter but locked at OSS.
    Cross-checks the per-tier resolution end-to-end -- if the
    perspective tier is wired in correctly, the lock state flips
    EXACTLY at the boundary :func:`min_tier_for_feature` reports."""
    for fid in ent.STARTER_FEATURES:
        unlocked = ent.lock_reason_at(
            ent.TIER_CLOUD_STARTER, fid, kind="feature"
        )
        assert unlocked is None, fid
        locked = ent.lock_reason_at(ent.TIER_OSS, fid, kind="feature")
        assert isinstance(locked, str), fid


def test_pro_only_feature_locked_at_starter(ent):
    for fid in ent.PRO_ONLY_FEATURES:
        locked = ent.lock_reason_at(
            ent.TIER_CLOUD_STARTER, fid, kind="feature"
        )
        assert isinstance(locked, str), fid
        unlocked = ent.lock_reason_at(ent.TIER_CLOUD_PRO, fid, kind="feature")
        assert unlocked is None, fid


def test_enterprise_feature_only_unlocked_at_enterprise(ent):
    for fid in ent.ENTERPRISE_FEATURES:
        for tier in ent._TIER_ORDER:
            out = ent.lock_reason_at(tier, fid, kind="feature")
            if tier == ent.TIER_ENTERPRISE:
                assert out is None, (tier, fid)
            else:
                assert isinstance(out, str), (tier, fid)


def test_kind_can_be_inferred_for_feature(ent):
    """``kind=None`` lets the inner method infer ``feature`` vs
    ``runtime`` from the id."""
    paid = next(iter(ent.STARTER_FEATURES))
    inferred = ent.lock_reason_at(ent.TIER_OSS, paid)
    explicit = ent.lock_reason_at(ent.TIER_OSS, paid, kind="feature")
    assert inferred == explicit
    assert isinstance(inferred, str)


# ── runtime axis ──────────────────────────────────────────────────────────────


def test_free_runtime_unlocked_at_every_tier(ent):
    for rt in ent.FREE_RUNTIMES:
        for tier in ent._TIER_ORDER:
            out = ent.lock_reason_at(tier, rt, kind="runtime")
            assert out is None, (tier, rt)


def test_paid_runtime_locked_on_oss_unlocked_on_starter(ent):
    for rt in ent.PAID_RUNTIMES:
        locked = ent.lock_reason_at(ent.TIER_OSS, rt, kind="runtime")
        assert isinstance(locked, str), rt
        unlocked = ent.lock_reason_at(
            ent.TIER_CLOUD_STARTER, rt, kind="runtime"
        )
        assert unlocked is None, rt


def test_kind_can_be_inferred_for_runtime(ent):
    rt = next(iter(ent.PAID_RUNTIMES))
    inferred = ent.lock_reason_at(ent.TIER_OSS, rt)
    explicit = ent.lock_reason_at(ent.TIER_OSS, rt, kind="runtime")
    assert inferred == explicit
    assert isinstance(inferred, str)


# ── capacity axes: channels / retention_days / nodes ─────────────────────────


def test_channels_within_oss_cap_unlocked(ent):
    """OSS gives :data:`_FREE_CHANNEL_LIMIT` channels; asking for one
    within the cap is unlocked."""
    assert ent.lock_reason_at(ent.TIER_OSS, "1", kind="channels") is None


def test_channels_over_oss_cap_locked(ent):
    """Asking for many more channels than OSS allows is locked, and the
    sentence names a paid tier."""
    over = ent._FREE_CHANNEL_LIMIT + 100
    out = ent.lock_reason_at(ent.TIER_OSS, str(over), kind="channels")
    assert isinstance(out, str), out


def test_channels_unlimited_at_starter(ent):
    """Starter and above are channel-unlimited (``_TIER_CHANNEL_LIMIT``
    maps them to ``None``) -- asking about any positive count is
    unlocked."""
    assert (
        ent.lock_reason_at(ent.TIER_CLOUD_STARTER, "10000", kind="channels")
        is None
    )


def test_retention_within_oss_window_unlocked(ent):
    """7-day retention is the OSS default cap."""
    assert ent.lock_reason_at(ent.TIER_OSS, "7", kind="retention_days") is None


def test_retention_over_oss_window_locked(ent):
    out = ent.lock_reason_at(ent.TIER_OSS, "365", kind="retention_days")
    assert isinstance(out, str), out


def test_nodes_within_oss_cap_unlocked(ent):
    """OSS / Cloud Free are a single-node grant; one node is allowed."""
    assert ent.lock_reason_at(ent.TIER_OSS, "1", kind="nodes") is None


def test_nodes_over_oss_cap_locked(ent):
    out = ent.lock_reason_at(ent.TIER_OSS, "5", kind="nodes")
    assert isinstance(out, str), out


def test_nodes_unlimited_at_enterprise(ent):
    """Enterprise (and every other paid tier) has ``node_limit=None``
    (unlimited) in :data:`_TIER_NODE_LIMIT`. The naive
    ``_hypothetical_entitlement`` builder hardcodes ``node_limit=1`` --
    ``lock_reason_at`` must use the per-tier cap instead. This pins
    that branch."""
    for n in (5, 50, 5000):
        out = ent.lock_reason_at(ent.TIER_ENTERPRISE, str(n), kind="nodes")
        assert out is None, (n, out)


def test_nodes_unlimited_at_cloud_pro(ent):
    for n in (5, 50, 5000):
        out = ent.lock_reason_at(ent.TIER_CLOUD_PRO, str(n), kind="nodes")
        assert out is None, (n, out)


# ── independent of live resolver ──────────────────────────────────────────────


def test_helper_ignores_grace_mode(ent, monkeypatch):
    """Grace short-circuits the live ``lock_reason`` to ``None`` for
    everything. ``lock_reason_at`` builds its own hypothetical
    Entitlement with ``grace=False``, so a paid feature at OSS still
    surfaces a lock string regardless of grace state."""
    monkeypatch.delenv("CLAWMETRY_ENFORCE", raising=False)
    ent.invalidate()
    paid = next(iter(ent.STARTER_FEATURES))
    out = ent.lock_reason_at(ent.TIER_OSS, paid, kind="feature")
    assert isinstance(out, str), out


def test_helper_ignores_enforce_flag(ent, monkeypatch):
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    ent.invalidate()
    fid = next(iter(ent.FREE_FEATURES))
    # Free feature still unlocked at every tier regardless of enforce.
    for tier in ent._TIER_ORDER:
        assert ent.lock_reason_at(tier, fid, kind="feature") is None, tier


def test_helper_ignores_cloud_plan_cache(ent, monkeypatch, tmp_path):
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    cache = tmp_path / ".clawmetry" / "cloud_plan.json"
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(json.dumps({"plan": "cloud_pro"}))
    ent.invalidate()
    # Even with a Pro cache in HOME, asking from the OSS perspective
    # still locks a Pro-only feature.
    pro_only_fid = next(iter(ent.PRO_ONLY_FEATURES))
    out = ent.lock_reason_at(ent.TIER_OSS, pro_only_fid, kind="feature")
    assert isinstance(out, str), out


# ── never-raise ───────────────────────────────────────────────────────────────


def test_never_raises_when_get_entitlement_crashes(ent, monkeypatch):
    """The helper synthesises its own Entitlement and never calls
    :func:`get_entitlement`, so a blown live resolver must not affect
    the result."""

    def boom(*_a, **_kw):
        raise RuntimeError("simulated resolver failure")

    monkeypatch.setattr(ent, "get_entitlement", boom)
    paid = next(iter(ent.STARTER_FEATURES))
    out = ent.lock_reason_at(ent.TIER_OSS, paid, kind="feature")
    assert isinstance(out, str), out


def test_unknown_feature_returns_none(ent):
    assert (
        ent.lock_reason_at(ent.TIER_OSS, "not_a_real_feature", kind="feature")
        is None
    )


def test_empty_item_returns_none(ent):
    assert ent.lock_reason_at(ent.TIER_OSS, "", kind="feature") is None


def test_unparseable_capacity_returns_none(ent):
    assert ent.lock_reason_at(ent.TIER_OSS, "abc", kind="channels") is None
    assert (
        ent.lock_reason_at(ent.TIER_OSS, "abc", kind="retention_days") is None
    )
    assert ent.lock_reason_at(ent.TIER_OSS, "abc", kind="nodes") is None


# ── HTTP endpoint: positive paths ─────────────────────────────────────────────


def test_endpoint_returns_shape_matching_live_lock_reason(client, ent):
    """The ``-at`` endpoint's row shape matches ``/api/entitlement/lock-reason``
    exactly so a paywall surface can swap one for the other without
    reshaping."""
    fid = next(iter(ent.FREE_FEATURES))
    resp = client.get(
        f"/api/entitlement/lock-reason-at?tier={ent.TIER_OSS}&feature={fid}"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert set(body.keys()) == _ROW_KEYS


def test_endpoint_feature_locked_at_oss(client, ent):
    paid = next(iter(ent.STARTER_FEATURES))
    resp = client.get(
        f"/api/entitlement/lock-reason-at?tier={ent.TIER_OSS}&feature={paid}"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["key"] == paid
    assert body["kind"] == "feature"
    assert body["locked"] is True
    assert body["allowed"] is False
    assert isinstance(body["reason"], str) and body["reason"]
    assert body["current_tier"] == ent.TIER_OSS
    assert body["required_tier"] is not None
    assert body["upgrade_required"] is True


def test_endpoint_feature_unlocked_at_enterprise(client, ent):
    paid = next(iter(ent.STARTER_FEATURES))
    resp = client.get(
        f"/api/entitlement/lock-reason-at?tier={ent.TIER_ENTERPRISE}"
        f"&feature={paid}"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["locked"] is False
    assert body["allowed"] is True
    assert body["reason"] is None
    assert body["current_tier"] == ent.TIER_ENTERPRISE
    assert body["upgrade_required"] is False


def test_endpoint_runtime_axis(client, ent):
    rt = next(iter(ent.PAID_RUNTIMES))
    resp = client.get(
        f"/api/entitlement/lock-reason-at?tier={ent.TIER_OSS}&runtime={rt}"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["kind"] == "runtime"
    assert body["locked"] is True
    assert body["current_tier"] == ent.TIER_OSS


def test_endpoint_channels_axis(client, ent):
    """100 channels at OSS is locked; at Cloud Starter (channel-unlimited)
    it is not."""
    over = ent._FREE_CHANNEL_LIMIT + 100
    resp = client.get(
        f"/api/entitlement/lock-reason-at?tier={ent.TIER_OSS}&channels={over}"
    )
    assert resp.status_code == 200
    assert resp.get_json()["locked"] is True

    resp = client.get(
        f"/api/entitlement/lock-reason-at?tier={ent.TIER_CLOUD_STARTER}"
        f"&channels={over}"
    )
    assert resp.status_code == 200
    assert resp.get_json()["locked"] is False


def test_endpoint_retention_axis(client, ent):
    resp = client.get(
        f"/api/entitlement/lock-reason-at?tier={ent.TIER_OSS}"
        "&retention_days=365"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["kind"] == "retention_days"
    assert body["locked"] is True


def test_endpoint_nodes_axis(client, ent):
    """Many nodes at OSS is locked; at Enterprise it is unlocked.
    Pins that the endpoint flows the per-tier ``_TIER_NODE_LIMIT``
    cap through correctly rather than the single-node default."""
    resp = client.get(
        f"/api/entitlement/lock-reason-at?tier={ent.TIER_OSS}&nodes=10"
    )
    assert resp.status_code == 200
    assert resp.get_json()["locked"] is True

    resp = client.get(
        f"/api/entitlement/lock-reason-at?tier={ent.TIER_ENTERPRISE}"
        "&nodes=10"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["locked"] is False
    assert body["current_tier"] == ent.TIER_ENTERPRISE


def test_endpoint_runtime_alias_canonicalises(client, ent):
    """The endpoint canonicalises runtime aliases the same way
    :func:`canonical_runtime` does, so callers can pass the dashed
    form."""
    # Pick a paid runtime that has a dashed alias.
    rt = None
    for cand in ent.PAID_RUNTIMES:
        if "_" in cand:
            rt = cand
            break
    if rt is None:
        pytest.skip("no PAID_RUNTIMES with underscore for alias check")
    aliased = rt.replace("_", "-")
    resp = client.get(
        f"/api/entitlement/lock-reason-at?tier={ent.TIER_OSS}"
        f"&runtime={aliased}"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["key"] == rt
    assert body["kind"] == "runtime"
    assert body["locked"] is True


# ── HTTP endpoint: input validation ───────────────────────────────────────────


def test_endpoint_missing_tier_returns_400(client, ent):
    fid = next(iter(ent.FREE_FEATURES))
    resp = client.get(f"/api/entitlement/lock-reason-at?feature={fid}")
    assert resp.status_code == 400


def test_endpoint_blank_tier_returns_400(client, ent):
    fid = next(iter(ent.FREE_FEATURES))
    resp = client.get(
        f"/api/entitlement/lock-reason-at?tier=%20%20&feature={fid}"
    )
    assert resp.status_code == 400


def test_endpoint_unknown_tier_returns_404(client, ent):
    fid = next(iter(ent.FREE_FEATURES))
    resp = client.get(
        f"/api/entitlement/lock-reason-at?tier=nonsense_xyz&feature={fid}"
    )
    assert resp.status_code == 404
    body = resp.get_json()
    assert body["which"] == "tier"
    assert body["tier"] == "nonsense_xyz"


def test_endpoint_no_axis_returns_400(client, ent):
    resp = client.get(
        f"/api/entitlement/lock-reason-at?tier={ent.TIER_OSS}"
    )
    assert resp.status_code == 400
    assert "error" in resp.get_json()


def test_endpoint_multi_axis_returns_400(client, ent):
    fid = next(iter(ent.FREE_FEATURES))
    rt = next(iter(ent.FREE_RUNTIMES))
    resp = client.get(
        f"/api/entitlement/lock-reason-at?tier={ent.TIER_OSS}"
        f"&feature={fid}&runtime={rt}"
    )
    assert resp.status_code == 400
    assert "error" in resp.get_json()


def test_endpoint_lowercases_and_trims_tier(client, ent):
    fid = next(iter(ent.FREE_FEATURES))
    resp = client.get(
        f"/api/entitlement/lock-reason-at?tier=%20%20{ent.TIER_OSS.upper()}%20"
        f"&feature={fid}"
    )
    assert resp.status_code == 200
    assert resp.get_json()["current_tier"] == ent.TIER_OSS


# ── HTTP endpoint: never-5xx contract ─────────────────────────────────────────


def test_endpoint_never_5xxs_when_helper_crashes(client, ent, monkeypatch):
    """Even if :func:`lock_reason_at` blows up, the route returns the
    grace-shape row, not a 500. Pins the UI-safe contract."""

    def boom(*_a, **_kw):
        raise RuntimeError("simulated helper crash")

    monkeypatch.setattr(ent, "lock_reason_at", boom)
    fid = next(iter(ent.FREE_FEATURES))
    resp = client.get(
        f"/api/entitlement/lock-reason-at?tier={ent.TIER_OSS}&feature={fid}"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["reason"] is None
    assert body["locked"] is False
    assert body["allowed"] is True
    assert body["current_tier"] == ent.TIER_OSS


def test_endpoint_every_tier_round_trips_with_free_feature(client, ent):
    """Round-trip every tier perspective with a free feature -- should
    return 200 + unlocked at every tier."""
    fid = next(iter(ent.FREE_FEATURES))
    for tier in ent._TIER_ORDER:
        resp = client.get(
            f"/api/entitlement/lock-reason-at?tier={tier}&feature={fid}"
        )
        assert resp.status_code == 200, tier
        body = resp.get_json()
        assert body["current_tier"] == tier, tier
        assert body["locked"] is False, tier
        assert body["reason"] is None, tier
