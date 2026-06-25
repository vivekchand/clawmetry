"""Tests for ``feature_spec_at(tier, feature)`` + ``GET
/api/entitlement/feature-spec-at``.

Scalar what-if sibling of :func:`feature_catalog_at`: one catalogue row
for ``feature`` with ``allowed`` / ``locked`` / ``entitled`` computed as
if the install were on ``tier``. Lets a pricing-comparison tooltip
hydrate against ONE feature at a hypothetical tier in one round-trip
without fetching the full ``feature_catalog_at`` payload.

Pins:

* the row shape matches a row from ``feature_catalog_at(tier)``
  EXACTLY (so the scalar and bulk what-if accessors cannot drift) -- a
  parity test enumerates every (tier, feature) pair
* every (tier, feature) pair in ``_TIER_ORDER`` x ``ALL_FEATURES``
  round-trips
* unknown / empty / ``None`` / non-string tier ids return ``None``
* unknown / empty / ``None`` / non-string feature ids return ``None``
* both args are trimmed + lowercased before resolution
* free features are always ``allowed=True`` / ``locked=False``
  regardless of the requested tier
* the helper is independent of the live resolver: switching
  enforcement or pointing HOME at a license cache does not change the
  rows the what-if surface returns
* the endpoint 400s on missing input, 404s on unknown ids (with
  ``which`` so the caller can render the right "unknown ..." message),
  and never 5xxs
"""
from __future__ import annotations

import importlib
import json

import pytest
from flask import Flask


_ROW_KEYS = {
    "id",
    "label",
    "tier",
    "tiers",
    "free",
    "allowed",
    "locked",
    "entitled",
    "alias",
}


@pytest.fixture
def ent(monkeypatch, tmp_path):
    """Fresh entitlements module with HOME pointed at an empty tmp dir
    so no real ~/.clawmetry/license.key or cloud_plan.json leaks in.
    Enforcement off by default (grace mode) -- ``feature_spec_at`` is
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


# ── shape ─────────────────────────────────────────────────────────────────────


def test_row_shape_matches_catalog_at_row(ent):
    fid = next(iter(ent.FREE_FEATURES))
    spec = ent.feature_spec_at(ent.TIER_CLOUD_PRO, fid)
    assert spec is not None
    assert set(spec.keys()) == _ROW_KEYS


def test_parity_with_every_catalog_at_row(ent):
    """For every (tier, feature) pair, the scalar what-if accessor
    returns the same dict as the bulk what-if accessor. Pins the
    scalar/bulk no-drift contract -- this is THE invariant the helper
    exists to make hydratable in one round-trip."""
    for tier in ent._TIER_ORDER:
        bulk_by_id = {row["id"]: row for row in ent.feature_catalog_at(tier)}
        for fid, row in bulk_by_id.items():
            assert ent.feature_spec_at(tier, fid) == row, (tier, fid)


# ── round-trip ────────────────────────────────────────────────────────────────


def test_every_pair_in_order_resolves(ent):
    for tier in ent._TIER_ORDER:
        for fid in ent.ALL_FEATURES:
            spec = ent.feature_spec_at(tier, fid)
            assert spec is not None, (tier, fid)
            assert spec["id"] == fid


# ── invalid tier ──────────────────────────────────────────────────────────────


def test_unknown_tier_returns_none(ent):
    fid = next(iter(ent.FREE_FEATURES))
    assert ent.feature_spec_at("not_a_real_tier", fid) is None


def test_empty_tier_returns_none(ent):
    fid = next(iter(ent.FREE_FEATURES))
    assert ent.feature_spec_at("", fid) is None


def test_none_tier_returns_none(ent):
    fid = next(iter(ent.FREE_FEATURES))
    assert ent.feature_spec_at(None, fid) is None


def test_non_string_tier_returns_none(ent):
    fid = next(iter(ent.FREE_FEATURES))
    assert ent.feature_spec_at(123, fid) is None
    assert ent.feature_spec_at(object(), fid) is None


# ── invalid feature ───────────────────────────────────────────────────────────


def test_unknown_feature_returns_none(ent):
    assert ent.feature_spec_at(ent.TIER_CLOUD_PRO, "not_a_real_feature") is None


def test_empty_feature_returns_none(ent):
    assert ent.feature_spec_at(ent.TIER_CLOUD_PRO, "") is None


def test_none_feature_returns_none(ent):
    assert ent.feature_spec_at(ent.TIER_CLOUD_PRO, None) is None


def test_non_string_feature_returns_none(ent):
    assert ent.feature_spec_at(ent.TIER_CLOUD_PRO, 123) is None
    assert ent.feature_spec_at(ent.TIER_CLOUD_PRO, object()) is None


# ── normalisation ─────────────────────────────────────────────────────────────


def test_inputs_are_lowercased_and_trimmed(ent):
    fid = next(iter(ent.FREE_FEATURES))
    a = ent.feature_spec_at(ent.TIER_CLOUD_PRO, fid)
    b = ent.feature_spec_at(ent.TIER_CLOUD_PRO.upper(), fid.upper())
    c = ent.feature_spec_at(f"  {ent.TIER_CLOUD_PRO}  ", f"  {fid}  ")
    assert a == b == c


# ── per-tier lock state ───────────────────────────────────────────────────────


def test_free_feature_unlocked_at_every_tier(ent):
    """Free features are part of the OSS grant and must be
    ``allowed=True`` / ``locked=False`` at every tier (the open-core
    floor) -- mirrors the same invariant on the bulk catalog_at."""
    fid = next(iter(ent.FREE_FEATURES))
    for tier in ent._TIER_ORDER:
        row = ent.feature_spec_at(tier, fid)
        assert row["allowed"] is True, (tier, fid)
        assert row["locked"] is False, (tier, fid)
        assert row["entitled"] is True, (tier, fid)


def test_oss_tier_locks_a_paid_feature(ent):
    paid_universe = (
        ent.STARTER_FEATURES | ent.PRO_ONLY_FEATURES | ent.ENTERPRISE_FEATURES
    )
    fid = next(iter(paid_universe))
    row = ent.feature_spec_at(ent.TIER_OSS, fid)
    assert row["locked"] is True
    assert row["allowed"] is False


def test_cloud_starter_unlocks_starter_locks_pro(ent):
    for fid in ent.STARTER_FEATURES:
        row = ent.feature_spec_at(ent.TIER_CLOUD_STARTER, fid)
        assert row["allowed"] is True, fid
        assert row["locked"] is False, fid
    for fid in ent.PRO_ONLY_FEATURES | ent.ENTERPRISE_FEATURES:
        row = ent.feature_spec_at(ent.TIER_CLOUD_STARTER, fid)
        assert row["allowed"] is False, fid
        assert row["locked"] is True, fid


def test_enterprise_unlocks_everything(ent):
    for fid in ent.ALL_FEATURES:
        row = ent.feature_spec_at(ent.TIER_ENTERPRISE, fid)
        assert row["allowed"] is True, fid
        assert row["locked"] is False, fid


# ── independent of live resolver ──────────────────────────────────────────────


def test_helper_ignores_grace_mode(ent, monkeypatch):
    monkeypatch.delenv("CLAWMETRY_ENFORCE", raising=False)
    ent.invalidate()
    enterprise_fid = next(iter(ent.ENTERPRISE_FEATURES))
    row = ent.feature_spec_at(ent.TIER_OSS, enterprise_fid)
    assert row["locked"] is True
    assert row["allowed"] is False


def test_helper_ignores_cloud_plan_cache(ent, monkeypatch, tmp_path):
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    cache = tmp_path / ".clawmetry" / "cloud_plan.json"
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(json.dumps({"plan": "cloud_pro"}))
    ent.invalidate()
    enterprise_fid = next(iter(ent.ENTERPRISE_FEATURES))
    row = ent.feature_spec_at(ent.TIER_OSS, enterprise_fid)
    assert row["locked"] is True
    assert row["allowed"] is False


# ── never-raise ───────────────────────────────────────────────────────────────


def test_never_raises_when_get_entitlement_crashes(ent, monkeypatch):
    """The helper builds its own hypothetical Entitlement and does not
    consult :func:`get_entitlement`, so a blown resolver must not
    affect the result. Pins the never-raise contract anyway."""

    def boom(*_a, **_kw):
        raise RuntimeError("simulated resolver failure")

    monkeypatch.setattr(ent, "get_entitlement", boom)
    fid = next(iter(ent.FREE_FEATURES))
    row = ent.feature_spec_at(ent.TIER_CLOUD_PRO, fid)
    assert row is not None
    assert row["id"] == fid


# ── HTTP endpoint ─────────────────────────────────────────────────────────────


def test_endpoint_known_pair_returns_row(client, ent):
    fid = next(iter(ent.FREE_FEATURES))
    resp = client.get(
        f"/api/entitlement/feature-spec-at?tier={ent.TIER_CLOUD_PRO}&feature={fid}"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["tier"] == ent.TIER_CLOUD_PRO
    assert body["feature"] == fid
    assert body["spec"] == ent.feature_spec_at(ent.TIER_CLOUD_PRO, fid)


def test_endpoint_lowercases_and_trims(client, ent):
    fid = next(iter(ent.FREE_FEATURES))
    resp = client.get(
        f"/api/entitlement/feature-spec-at?tier=%20%20{ent.TIER_CLOUD_PRO.upper()}%20%20"
        f"&feature=%20%20{fid.upper()}%20%20"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["tier"] == ent.TIER_CLOUD_PRO
    assert body["feature"] == fid


def test_endpoint_missing_tier_returns_400(client, ent):
    fid = next(iter(ent.FREE_FEATURES))
    resp = client.get(f"/api/entitlement/feature-spec-at?feature={fid}")
    assert resp.status_code == 400
    assert "error" in resp.get_json()


def test_endpoint_blank_tier_returns_400(client, ent):
    fid = next(iter(ent.FREE_FEATURES))
    resp = client.get(
        f"/api/entitlement/feature-spec-at?tier=%20%20&feature={fid}"
    )
    assert resp.status_code == 400


def test_endpoint_missing_feature_returns_400(client, ent):
    resp = client.get(
        f"/api/entitlement/feature-spec-at?tier={ent.TIER_CLOUD_PRO}"
    )
    assert resp.status_code == 400
    assert "error" in resp.get_json()


def test_endpoint_blank_feature_returns_400(client, ent):
    resp = client.get(
        f"/api/entitlement/feature-spec-at?tier={ent.TIER_CLOUD_PRO}&feature=%20%20"
    )
    assert resp.status_code == 400


def test_endpoint_unknown_tier_returns_404(client, ent):
    fid = next(iter(ent.FREE_FEATURES))
    resp = client.get(
        f"/api/entitlement/feature-spec-at?tier=nonsense_xyz&feature={fid}"
    )
    assert resp.status_code == 404
    body = resp.get_json()
    assert body["tier"] == "nonsense_xyz"
    assert body["which"] == "tier"
    assert "error" in body


def test_endpoint_unknown_feature_returns_404(client, ent):
    resp = client.get(
        f"/api/entitlement/feature-spec-at?tier={ent.TIER_CLOUD_PRO}"
        "&feature=not_a_real_feature"
    )
    assert resp.status_code == 404
    body = resp.get_json()
    assert body["feature"] == "not_a_real_feature"
    assert body["which"] == "feature"
    assert "error" in body


def test_endpoint_every_pair_in_order_round_trips(client, ent):
    for tier in ent._TIER_ORDER:
        for fid in ent.ALL_FEATURES:
            resp = client.get(
                f"/api/entitlement/feature-spec-at?tier={tier}&feature={fid}"
            )
            assert resp.status_code == 200, (tier, fid)
            body = resp.get_json()
            assert body["tier"] == tier, (tier, fid)
            assert body["feature"] == fid, (tier, fid)
            assert body["spec"]["id"] == fid, (tier, fid)
