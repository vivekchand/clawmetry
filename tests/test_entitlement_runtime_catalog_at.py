"""Tests for ``runtime_catalog_at(tier)`` + ``GET
/api/entitlement/runtime-catalog-at``.

What-if sibling of :func:`runtime_catalog`. Same shape as the live catalog
row, ``allowed`` / ``locked`` / ``entitled`` recomputed against a
hypothetical Entitlement at the requested tier.

Pins:

* the row shape (keys + ordering) matches :func:`runtime_catalog` exactly
* every tier in ``_TIER_ORDER`` resolves
* FREE_RUNTIMES (``openclaw``, ``nemoclaw``) are always unlocked
  regardless of the requested tier
* PAID_RUNTIMES are locked at tiers below the paid floor and unlocked at
  ``trial`` / ``cloud_starter`` and above
* the helper is independent of the live resolver (grace toggle / cached
  cloud plan do not affect the what-if rows)
* unknown / empty / ``None`` / non-string tier ids return ``None``
* the endpoint 400s on missing input, 404s on unknown ids
"""
from __future__ import annotations

import importlib
import json

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


_ROW_KEYS = {
    "id",
    "label",
    "free",
    "tier",
    "tiers",
    "allowed",
    "locked",
    "entitled",
}


# ── shape ─────────────────────────────────────────────────────────────────────


def test_row_shape_matches_runtime_catalog(ent):
    cat_keys = set(ent.runtime_catalog()[0].keys())
    rows = ent.runtime_catalog_at(ent.TIER_CLOUD_PRO)
    assert rows is not None and len(rows) > 0
    assert set(rows[0].keys()) == cat_keys == _ROW_KEYS


def test_row_ordering_matches_runtime_catalog(ent):
    cat_ids = [row["id"] for row in ent.runtime_catalog()]
    at_ids = [row["id"] for row in ent.runtime_catalog_at(ent.TIER_OSS)]
    assert cat_ids == at_ids


def test_catalogue_derived_fields_are_invariant_across_tiers(ent):
    """Only ``allowed`` / ``locked`` / ``entitled`` may shift between
    tiers; ``id``, ``label``, ``free``, ``tier``, ``tiers`` are
    catalogue-derived and must stay identical."""
    base = {row["id"]: row for row in ent.runtime_catalog_at(ent.TIER_OSS)}
    for tier in ent._TIER_ORDER:
        rows = ent.runtime_catalog_at(tier)
        assert rows is not None
        for row in rows:
            ref = base[row["id"]]
            for key in ("id", "label", "free", "tier", "tiers"):
                assert row[key] == ref[key], (tier, row["id"], key)


# ── round-trip ────────────────────────────────────────────────────────────────


def test_every_tier_in_order_resolves(ent):
    for tier in ent._TIER_ORDER:
        rows = ent.runtime_catalog_at(tier)
        assert rows is not None, tier
        assert len(rows) == len(ent.ALL_RUNTIMES)


def test_unknown_tier_returns_none(ent):
    assert ent.runtime_catalog_at("not_a_real_tier") is None


def test_empty_returns_none(ent):
    assert ent.runtime_catalog_at("") is None


def test_none_returns_none(ent):
    assert ent.runtime_catalog_at(None) is None


def test_non_string_returns_none(ent):
    assert ent.runtime_catalog_at(123) is None
    assert ent.runtime_catalog_at(object()) is None


def test_input_is_lowercased_and_trimmed(ent):
    a = ent.runtime_catalog_at(ent.TIER_CLOUD_PRO)
    b = ent.runtime_catalog_at(ent.TIER_CLOUD_PRO.upper())
    c = ent.runtime_catalog_at(f"  {ent.TIER_CLOUD_PRO}  ")
    assert a == b == c


# ── per-tier lock state ───────────────────────────────────────────────────────


def test_free_runtimes_unlocked_at_every_tier(ent):
    for tier in ent._TIER_ORDER:
        rows = ent.runtime_catalog_at(tier)
        free_rows = [r for r in rows if r["free"]]
        for r in free_rows:
            assert r["allowed"] is True, (tier, r["id"])
            assert r["locked"] is False, (tier, r["id"])
            assert r["entitled"] is True, (tier, r["id"])


def test_oss_tier_locks_every_paid_runtime(ent):
    rows = {r["id"]: r for r in ent.runtime_catalog_at(ent.TIER_OSS)}
    for rt in ent.PAID_RUNTIMES:
        assert rows[rt]["allowed"] is False, rt
        assert rows[rt]["locked"] is True, rt
        assert rows[rt]["entitled"] is False, rt


def test_cloud_free_tier_locks_every_paid_runtime(ent):
    rows = {r["id"]: r for r in ent.runtime_catalog_at(ent.TIER_CLOUD_FREE)}
    for rt in ent.PAID_RUNTIMES:
        assert rows[rt]["allowed"] is False, rt
        assert rows[rt]["locked"] is True, rt
        assert rows[rt]["entitled"] is False, rt


def test_cloud_starter_unlocks_every_paid_runtime(ent):
    rows = {r["id"]: r for r in ent.runtime_catalog_at(ent.TIER_CLOUD_STARTER)}
    for rt in ent.PAID_RUNTIMES:
        assert rows[rt]["allowed"] is True, rt
        assert rows[rt]["locked"] is False, rt
        assert rows[rt]["entitled"] is True, rt


def test_trial_unlocks_every_paid_runtime(ent):
    rows = {r["id"]: r for r in ent.runtime_catalog_at(ent.TIER_TRIAL)}
    for rt in ent.PAID_RUNTIMES:
        assert rows[rt]["allowed"] is True, rt
        assert rows[rt]["locked"] is False, rt


def test_enterprise_unlocks_everything(ent):
    rows = ent.runtime_catalog_at(ent.TIER_ENTERPRISE)
    for r in rows:
        assert r["allowed"] is True, r["id"]
        assert r["locked"] is False, r["id"]
        assert r["entitled"] is True, r["id"]


# ── independent of live resolver ──────────────────────────────────────────────


def test_helper_ignores_grace_mode(ent, monkeypatch):
    monkeypatch.delenv("CLAWMETRY_ENFORCE", raising=False)
    ent.invalidate()
    rows = {r["id"]: r for r in ent.runtime_catalog_at(ent.TIER_OSS)}
    paid_rt = next(iter(ent.PAID_RUNTIMES))
    assert rows[paid_rt]["locked"] is True
    assert rows[paid_rt]["allowed"] is False


def test_helper_ignores_cloud_plan_cache(ent, monkeypatch, tmp_path):
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    cache = tmp_path / ".clawmetry" / "cloud_plan.json"
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(json.dumps({"plan": "cloud_pro"}))
    ent.invalidate()
    rows = {r["id"]: r for r in ent.runtime_catalog_at(ent.TIER_OSS)}
    paid_rt = next(iter(ent.PAID_RUNTIMES))
    assert rows[paid_rt]["locked"] is True
    assert rows[paid_rt]["allowed"] is False


# ── never-raise ───────────────────────────────────────────────────────────────


def test_never_raises_when_get_entitlement_crashes(ent, monkeypatch):
    def boom(*_a, **_kw):
        raise RuntimeError("simulated resolver failure")

    monkeypatch.setattr(ent, "get_entitlement", boom)
    rows = ent.runtime_catalog_at(ent.TIER_CLOUD_PRO)
    assert rows is not None
    assert len(rows) == len(ent.ALL_RUNTIMES)


# ── HTTP endpoint ─────────────────────────────────────────────────────────────


def test_endpoint_known_tier_returns_rows(client, ent):
    resp = client.get(
        f"/api/entitlement/runtime-catalog-at?tier={ent.TIER_CLOUD_PRO}"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["tier"] == ent.TIER_CLOUD_PRO
    assert body["runtimes"] == ent.runtime_catalog_at(ent.TIER_CLOUD_PRO)


def test_endpoint_lowercases_and_trims(client, ent):
    resp = client.get(
        f"/api/entitlement/runtime-catalog-at?tier=%20%20{ent.TIER_CLOUD_PRO.upper()}%20%20"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["tier"] == ent.TIER_CLOUD_PRO


def test_endpoint_missing_arg_returns_400(client):
    resp = client.get("/api/entitlement/runtime-catalog-at")
    assert resp.status_code == 400
    assert "error" in resp.get_json()


def test_endpoint_blank_arg_returns_400(client):
    resp = client.get("/api/entitlement/runtime-catalog-at?tier=%20%20")
    assert resp.status_code == 400


def test_endpoint_unknown_tier_returns_404(client):
    resp = client.get("/api/entitlement/runtime-catalog-at?tier=nonsense_xyz")
    assert resp.status_code == 404
    body = resp.get_json()
    assert body["tier"] == "nonsense_xyz"
    assert "error" in body


def test_endpoint_every_tier_in_order_round_trips(client, ent):
    for tier in ent._TIER_ORDER:
        resp = client.get(f"/api/entitlement/runtime-catalog-at?tier={tier}")
        assert resp.status_code == 200, tier
        body = resp.get_json()
        assert body["tier"] == tier, tier
        assert len(body["runtimes"]) == len(ent.ALL_RUNTIMES), tier
