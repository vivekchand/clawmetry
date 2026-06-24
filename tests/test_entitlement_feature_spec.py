"""Tests for ``feature_spec(feature)`` and ``GET
/api/entitlement/feature-spec``.

``feature_spec`` is the scalar sibling of ``feature_catalog()`` -- the row
shape a feature-detail page or upgrade tooltip hydrates against in one
round-trip instead of fetching the full catalogue and filtering
client-side.

Pins:

* the row shape matches a row from ``feature_catalog()`` exactly (so the
  scalar and bulk accessors cannot drift)
* every id in ``ALL_FEATURES`` round-trips through ``feature_spec``
* unknown / empty / ``None`` ids return ``None``
* the input is trimmed + lowercased before resolution
* grace mode reports zero locked rows (zero behaviour change)
* enforce-mode lock state on an OSS install matches the catalogue
* the endpoint 400s on a missing arg, 404s on an unknown id, and never
  5xxs (a resolver crash still returns a catalogue row built against the
  OSS-free fallback)
"""
from __future__ import annotations

import importlib
import json

import pytest


_SPEC_KEYS = {
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
    """Fresh entitlements module with HOME pointed at an empty tmp dir so no
    real ~/.clawmetry/license.key or cloud_plan.json leaks in. Enforcement off
    by default (grace mode)."""
    monkeypatch.delenv("CLAWMETRY_ENFORCE", raising=False)
    monkeypatch.setenv("HOME", str(tmp_path))
    import clawmetry.entitlements as e

    importlib.reload(e)
    e.invalidate()
    yield e
    e.invalidate()


@pytest.fixture
def client(ent):
    from flask import Flask
    from routes.entitlement import bp_entitlement

    app = Flask(__name__)
    app.register_blueprint(bp_entitlement)
    return app.test_client()


# ── shape ─────────────────────────────────────────────────────────────────────────────


def test_spec_row_keys_match_catalog_row(ent):
    """A row from ``feature_spec`` carries the same keys as a
    ``feature_catalog()`` row -- defends against a rename on one side
    silently shipping a half-renamed payload to the UI."""
    cat_keys = set(ent.feature_catalog()[0].keys())
    assert cat_keys == _SPEC_KEYS
    fid = next(iter(ent.FREE_FEATURES))
    spec = ent.feature_spec(fid)
    assert spec is not None
    assert set(spec.keys()) == _SPEC_KEYS


def test_spec_parity_with_every_catalog_row(ent):
    """For every row in the catalogue, the scalar accessor returns the
    same dict. Pins the scalar/bulk no-drift contract."""
    cat_by_id = {row["id"]: row for row in ent.feature_catalog()}
    for fid, row in cat_by_id.items():
        assert ent.feature_spec(fid) == row, fid


# ── round-trip ───────────────────────────────────────────────────────────────────────────


def test_every_known_feature_round_trips(ent):
    for fid in ent.ALL_FEATURES:
        spec = ent.feature_spec(fid)
        assert spec is not None, fid
        assert spec["id"] == fid


def test_unknown_feature_returns_none(ent):
    assert ent.feature_spec("not_a_real_feature") is None


def test_empty_returns_none(ent):
    assert ent.feature_spec("") is None


def test_none_returns_none(ent):
    assert ent.feature_spec(None) is None


def test_non_string_returns_none(ent):
    # Defensive: a stray int / object from a malformed caller must not crash.
    assert ent.feature_spec(123) is None
    assert ent.feature_spec(object()) is None


def test_input_is_lowercased_and_trimmed(ent):
    fid = next(iter(ent.FREE_FEATURES))
    assert ent.feature_spec(fid.upper()) == ent.feature_spec(fid)
    assert ent.feature_spec(f"  {fid}  ") == ent.feature_spec(fid)


# ── per-bucket tier carriage ─────────────────────────────────────────────────────────────


def test_free_features_carry_oss_tier_and_unlocked(ent):
    for fid in ent.FREE_FEATURES:
        row = ent.feature_spec(fid)
        assert row["tier"] == ent.TIER_OSS, fid
        assert row["free"] is True, fid
        assert row["locked"] is False, fid
        assert row["entitled"] is True, fid


def test_starter_features_carry_starter_tier(ent):
    for fid in ent.STARTER_FEATURES:
        row = ent.feature_spec(fid)
        assert row["tier"] == ent.TIER_CLOUD_STARTER, fid
        assert row["free"] is False, fid


def test_pro_features_carry_pro_tier(ent):
    for fid in ent.PRO_ONLY_FEATURES:
        row = ent.feature_spec(fid)
        assert row["tier"] == ent.TIER_CLOUD_PRO, fid
        assert row["free"] is False, fid


def test_enterprise_features_carry_enterprise_tier(ent):
    for fid in ent.ENTERPRISE_FEATURES:
        row = ent.feature_spec(fid)
        assert row["tier"] == ent.TIER_ENTERPRISE, fid
        assert row["free"] is False, fid


# ── alias flag ────────────────────────────────────────────────────────────────────────────


def test_alias_flag_marks_backcompat_pro_keys(ent):
    for fid in ("custom_alerts", "alert_webhooks", "anomaly_detection", "cost_optimizer"):
        row = ent.feature_spec(fid)
        assert row is not None and row["alias"] is True, fid


def test_alias_flag_false_for_canonical_keys(ent):
    for fid in ent.FREE_FEATURES | ent.STARTER_FEATURES | ent.ENTERPRISE_FEATURES:
        row = ent.feature_spec(fid)
        assert row is not None and row["alias"] is False, fid


# ── tiers ladder ──────────────────────────────────────────────────────────────────────────


def test_tiers_field_matches_feature_tier_ids(ent):
    for fid in ent.ALL_FEATURES:
        row = ent.feature_spec(fid)
        assert row["tiers"] == ent._feature_tier_ids(fid), fid


# ── grace vs enforce ────────────────────────────────────────────────────────────────────────


def test_grace_locks_nothing(ent):
    for fid in ent.ALL_FEATURES:
        row = ent.feature_spec(fid)
        assert row["allowed"] is True, fid
        assert row["locked"] is False, fid


def test_enforce_oss_locks_every_paid_feature(ent, monkeypatch):
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    ent.invalidate()
    for fid in ent.FREE_FEATURES:
        row = ent.feature_spec(fid)
        assert row["locked"] is False, fid
        assert row["allowed"] is True, fid
    for fid in ent.STARTER_FEATURES | ent.PRO_ONLY_FEATURES | ent.ENTERPRISE_FEATURES:
        row = ent.feature_spec(fid)
        assert row["locked"] is True, fid
        assert row["allowed"] is False, fid
        assert row["entitled"] is False, fid


def test_enforce_cloud_pro_unlocks_paid_but_not_enterprise(ent, monkeypatch, tmp_path):
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    cache = tmp_path / ".clawmetry" / "cloud_plan.json"
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(json.dumps({"plan": "cloud_pro"}))
    ent.invalidate()
    for fid in ent.STARTER_FEATURES | ent.PRO_ONLY_FEATURES:
        row = ent.feature_spec(fid)
        assert row["allowed"] is True, fid
        assert row["locked"] is False, fid
        assert row["entitled"] is True, fid
    for fid in ent.ENTERPRISE_FEATURES:
        row = ent.feature_spec(fid)
        assert row["allowed"] is False, fid
        assert row["locked"] is True, fid
        assert row["entitled"] is False, fid


# ── never-raise ─────────────────────────────────────────────────────────────────────────────


def test_never_raises_when_resolver_crashes(ent, monkeypatch):
    """A blown resolver still returns the catalogue row built against
    the OSS-free fallback -- matches the never-crash contract on
    ``feature_catalog()``."""

    def boom(*_a, **_kw):
        raise RuntimeError("simulated resolver failure")

    monkeypatch.setattr(ent, "get_entitlement", boom)
    fid = next(iter(ent.FREE_FEATURES))
    row = ent.feature_spec(fid)
    assert row is not None
    assert row["id"] == fid
    assert row["free"] is True


# ── HTTP endpoint ───────────────────────────────────────────────────────────────────────────


def test_endpoint_known_feature_returns_row(client, ent):
    fid = next(iter(ent.FREE_FEATURES))
    resp = client.get(f"/api/entitlement/feature-spec?feature={fid}")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body == ent.feature_spec(fid)


def test_endpoint_lowercases_and_trims(client, ent):
    fid = next(iter(ent.FREE_FEATURES))
    resp = client.get(
        f"/api/entitlement/feature-spec?feature=%20%20{fid.upper()}%20%20"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["id"] == fid


def test_endpoint_missing_arg_returns_400(client):
    resp = client.get("/api/entitlement/feature-spec")
    assert resp.status_code == 400
    assert "error" in resp.get_json()


def test_endpoint_blank_arg_returns_400(client):
    resp = client.get("/api/entitlement/feature-spec?feature=%20%20")
    assert resp.status_code == 400


def test_endpoint_unknown_feature_returns_404(client):
    resp = client.get("/api/entitlement/feature-spec?feature=nonsense_xyz")
    assert resp.status_code == 404
    body = resp.get_json()
    assert body["feature"] == "nonsense_xyz"
    assert "error" in body


def test_endpoint_every_known_feature_round_trips(client, ent):
    for fid in ent.ALL_FEATURES:
        resp = client.get(f"/api/entitlement/feature-spec?feature={fid}")
        assert resp.status_code == 200, fid
        body = resp.get_json()
        assert body["id"] == fid, fid


def test_endpoint_returns_grace_row_even_when_resolver_crashes(client, ent, monkeypatch):
    """``feature_spec`` catches resolver failures internally and falls
    back to the OSS-free row, so the endpoint must return 200 + a
    valid catalogue row even when ``get_entitlement`` explodes."""

    def boom(*_a, **_kw):
        raise RuntimeError("simulated resolver failure")

    monkeypatch.setattr(ent, "get_entitlement", boom)
    fid = next(iter(ent.FREE_FEATURES))
    resp = client.get(f"/api/entitlement/feature-spec?feature={fid}")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["id"] == fid
    assert body["free"] is True
