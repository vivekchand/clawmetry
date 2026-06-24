"""Tests for ``feature_catalog_at(tier)`` + ``GET
/api/entitlement/feature-catalog-at``.

What-if sibling of :func:`feature_catalog`: returns the same row shape but
with ``allowed`` / ``locked`` / ``entitled`` computed as if the install
were on ``tier`` instead of the resolved tier. Lets a pricing-comparison
UI render the catalogue at any hypothetical tier without first switching
the live resolver.

Pins:

* the row shape (keys + ordering) matches :func:`feature_catalog` exactly,
  so a UI swapping between "current" and "hypothetical" never has to
  reshape client-side
* every tier in ``_TIER_ORDER`` (including ``trial``) resolves to a non-
  None catalogue
* OSS-floor catalog at the lowest tier locks every paid feature; the top
  tier unlocks every paid feature; intermediate tiers unlock the right
  subset
* the helper is independent of the live resolver: switching enforcement
  or pointing HOME at a license file does not change the rows the
  what-if surface returns
* free features are always ``allowed=True`` / ``locked=False`` regardless
  of the requested tier
* unknown / empty / ``None`` / non-string tier ids return ``None``
* the endpoint 400s on missing input, 404s on unknown ids, and falls
  back gracefully if the helper short-circuits
"""
from __future__ import annotations

import importlib
import json

import pytest
from flask import Flask


@pytest.fixture
def ent(monkeypatch, tmp_path):
    """Fresh entitlements module with HOME pointed at an empty tmp dir so no
    real ~/.clawmetry/license.key or cloud_plan.json leaks in. Enforcement off
    by default (grace mode) -- ``feature_catalog_at`` is independent of either
    knob, so the fixture only needs to make sure the live resolver does not
    surprise the test."""
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


# ── shape ─────────────────────────────────────────────────────────────────────


def test_row_shape_matches_feature_catalog(ent):
    """A row from ``feature_catalog_at`` carries the same keys as a
    ``feature_catalog()`` row -- defends against a rename on one side
    silently shipping a half-renamed payload to a comparison UI."""
    cat_keys = set(ent.feature_catalog()[0].keys())
    rows = ent.feature_catalog_at(ent.TIER_CLOUD_PRO)
    assert rows is not None and len(rows) > 0
    assert set(rows[0].keys()) == cat_keys == _ROW_KEYS


def test_row_ordering_matches_feature_catalog(ent):
    """Row order is identical to ``feature_catalog()`` -- a UI rendering
    both surfaces side-by-side must line up rung-for-rung."""
    cat_ids = [row["id"] for row in ent.feature_catalog()]
    at_ids = [row["id"] for row in ent.feature_catalog_at(ent.TIER_OSS)]
    assert cat_ids == at_ids


def test_catalogue_derived_fields_are_invariant_across_tiers(ent):
    """``id``, ``label``, ``tier``, ``tiers``, ``free``, ``alias`` are
    catalogue-derived and must not depend on the hypothetical tier.
    Only ``allowed`` / ``locked`` / ``entitled`` may shift."""
    base = {row["id"]: row for row in ent.feature_catalog_at(ent.TIER_OSS)}
    for tier in ent._TIER_ORDER:
        rows = ent.feature_catalog_at(tier)
        assert rows is not None
        for row in rows:
            ref = base[row["id"]]
            for key in ("id", "label", "tier", "tiers", "free", "alias"):
                assert row[key] == ref[key], (tier, row["id"], key)


# ── round-trip ────────────────────────────────────────────────────────────────


def test_every_tier_in_order_resolves(ent):
    for tier in ent._TIER_ORDER:
        rows = ent.feature_catalog_at(tier)
        assert rows is not None, tier
        assert len(rows) == len(ent.ALL_FEATURES)


def test_unknown_tier_returns_none(ent):
    assert ent.feature_catalog_at("not_a_real_tier") is None


def test_empty_returns_none(ent):
    assert ent.feature_catalog_at("") is None


def test_none_returns_none(ent):
    assert ent.feature_catalog_at(None) is None


def test_non_string_returns_none(ent):
    assert ent.feature_catalog_at(123) is None
    assert ent.feature_catalog_at(object()) is None


def test_input_is_lowercased_and_trimmed(ent):
    a = ent.feature_catalog_at(ent.TIER_CLOUD_PRO)
    b = ent.feature_catalog_at(ent.TIER_CLOUD_PRO.upper())
    c = ent.feature_catalog_at(f"  {ent.TIER_CLOUD_PRO}  ")
    assert a == b == c


# ── per-tier lock state ───────────────────────────────────────────────────────


def test_free_features_unlocked_at_every_tier(ent):
    """Free features are part of the OSS grant and must be ``allowed=True``
    / ``locked=False`` at every tier (the open-core floor)."""
    for tier in ent._TIER_ORDER:
        rows = ent.feature_catalog_at(tier)
        free_rows = [r for r in rows if r["free"]]
        for r in free_rows:
            assert r["allowed"] is True, (tier, r["id"])
            assert r["locked"] is False, (tier, r["id"])
            assert r["entitled"] is True, (tier, r["id"])


def test_oss_tier_locks_every_paid_feature(ent):
    rows = ent.feature_catalog_at(ent.TIER_OSS)
    paid_universe = (
        ent.STARTER_FEATURES | ent.PRO_ONLY_FEATURES | ent.ENTERPRISE_FEATURES
    )
    locked = {r["id"] for r in rows if r["locked"]}
    # Aliases map to the same canonical lock state as their target, so
    # the paid_universe is a subset of the locked set.
    assert paid_universe.issubset(locked)


def test_cloud_free_tier_locks_every_paid_feature(ent):
    rows = ent.feature_catalog_at(ent.TIER_CLOUD_FREE)
    paid_universe = (
        ent.STARTER_FEATURES | ent.PRO_ONLY_FEATURES | ent.ENTERPRISE_FEATURES
    )
    locked = {r["id"] for r in rows if r["locked"]}
    assert paid_universe.issubset(locked)


def test_cloud_starter_unlocks_starter_locks_pro(ent):
    rows = {r["id"]: r for r in ent.feature_catalog_at(ent.TIER_CLOUD_STARTER)}
    for fid in ent.STARTER_FEATURES:
        assert rows[fid]["allowed"] is True, fid
        assert rows[fid]["locked"] is False, fid
        assert rows[fid]["entitled"] is True, fid
    for fid in ent.PRO_ONLY_FEATURES | ent.ENTERPRISE_FEATURES:
        assert rows[fid]["allowed"] is False, fid
        assert rows[fid]["locked"] is True, fid
        assert rows[fid]["entitled"] is False, fid


def test_cloud_pro_unlocks_starter_and_pro_locks_enterprise(ent):
    rows = {r["id"]: r for r in ent.feature_catalog_at(ent.TIER_CLOUD_PRO)}
    for fid in ent.STARTER_FEATURES | ent.PRO_ONLY_FEATURES:
        assert rows[fid]["allowed"] is True, fid
        assert rows[fid]["locked"] is False, fid
        assert rows[fid]["entitled"] is True, fid
    for fid in ent.ENTERPRISE_FEATURES:
        assert rows[fid]["allowed"] is False, fid
        assert rows[fid]["locked"] is True, fid
        assert rows[fid]["entitled"] is False, fid


def test_enterprise_unlocks_everything(ent):
    rows = ent.feature_catalog_at(ent.TIER_ENTERPRISE)
    for r in rows:
        assert r["allowed"] is True, r["id"]
        assert r["locked"] is False, r["id"]
        assert r["entitled"] is True, r["id"]


def test_trial_unlocks_paid_features_not_enterprise(ent):
    """``_TIER_FEATURES[trial] = PAID_FEATURES`` -- the trial tier grants
    the same paid surface as Pro but does NOT include
    ``ENTERPRISE_FEATURES``."""
    rows = {r["id"]: r for r in ent.feature_catalog_at(ent.TIER_TRIAL)}
    for fid in ent.STARTER_FEATURES | ent.PRO_ONLY_FEATURES:
        assert rows[fid]["entitled"] is True, fid
    for fid in ent.ENTERPRISE_FEATURES:
        assert rows[fid]["entitled"] is False, fid


# ── independent of live resolver ──────────────────────────────────────────────


def test_helper_ignores_grace_mode(ent, monkeypatch):
    """Grace mode allows everything in the LIVE entitlement; the what-if
    surface must still report locked rows for tiers below the feature's
    minimum (otherwise the helper would be useless when the resolver is
    in grace -- which is the default state today)."""
    monkeypatch.delenv("CLAWMETRY_ENFORCE", raising=False)
    ent.invalidate()
    rows = {r["id"]: r for r in ent.feature_catalog_at(ent.TIER_OSS)}
    enterprise_fid = next(iter(ent.ENTERPRISE_FEATURES))
    assert rows[enterprise_fid]["locked"] is True
    assert rows[enterprise_fid]["allowed"] is False


def test_helper_ignores_cloud_plan_cache(ent, monkeypatch, tmp_path):
    """The what-if rows must not be coloured by a cached cloud plan: a
    Pro license in the cache must not flip the OSS catalogue's locked
    set."""
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    cache = tmp_path / ".clawmetry" / "cloud_plan.json"
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(json.dumps({"plan": "cloud_pro"}))
    ent.invalidate()
    rows = {r["id"]: r for r in ent.feature_catalog_at(ent.TIER_OSS)}
    enterprise_fid = next(iter(ent.ENTERPRISE_FEATURES))
    assert rows[enterprise_fid]["locked"] is True
    assert rows[enterprise_fid]["allowed"] is False


# ── never-raise ───────────────────────────────────────────────────────────────


def test_never_raises_when_get_entitlement_crashes(ent, monkeypatch):
    """The helper builds its own hypothetical Entitlement and does not
    consult :func:`get_entitlement`, so a blown resolver must not affect
    the result. Still verify the never-raise contract: even if
    ``get_entitlement`` is patched to raise, the catalogue still resolves."""

    def boom(*_a, **_kw):
        raise RuntimeError("simulated resolver failure")

    monkeypatch.setattr(ent, "get_entitlement", boom)
    rows = ent.feature_catalog_at(ent.TIER_CLOUD_PRO)
    assert rows is not None
    assert len(rows) == len(ent.ALL_FEATURES)


# ── HTTP endpoint ─────────────────────────────────────────────────────────────


def test_endpoint_known_tier_returns_rows(client, ent):
    resp = client.get(
        f"/api/entitlement/feature-catalog-at?tier={ent.TIER_CLOUD_PRO}"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["tier"] == ent.TIER_CLOUD_PRO
    assert body["features"] == ent.feature_catalog_at(ent.TIER_CLOUD_PRO)


def test_endpoint_lowercases_and_trims(client, ent):
    resp = client.get(
        f"/api/entitlement/feature-catalog-at?tier=%20%20{ent.TIER_CLOUD_PRO.upper()}%20%20"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["tier"] == ent.TIER_CLOUD_PRO


def test_endpoint_missing_arg_returns_400(client):
    resp = client.get("/api/entitlement/feature-catalog-at")
    assert resp.status_code == 400
    assert "error" in resp.get_json()


def test_endpoint_blank_arg_returns_400(client):
    resp = client.get("/api/entitlement/feature-catalog-at?tier=%20%20")
    assert resp.status_code == 400


def test_endpoint_unknown_tier_returns_404(client):
    resp = client.get("/api/entitlement/feature-catalog-at?tier=nonsense_xyz")
    assert resp.status_code == 404
    body = resp.get_json()
    assert body["tier"] == "nonsense_xyz"
    assert "error" in body


def test_endpoint_every_tier_in_order_round_trips(client, ent):
    for tier in ent._TIER_ORDER:
        resp = client.get(f"/api/entitlement/feature-catalog-at?tier={tier}")
        assert resp.status_code == 200, tier
        body = resp.get_json()
        assert body["tier"] == tier, tier
        assert len(body["features"]) == len(ent.ALL_FEATURES), tier
