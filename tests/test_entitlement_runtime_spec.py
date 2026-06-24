"""Tests for ``runtime_spec(runtime)`` and ``GET
/api/entitlement/runtime-spec``.

``runtime_spec`` is the scalar sibling of ``runtime_catalog()`` -- the row
shape a runtime-detail page or upgrade tooltip hydrates against in one
round-trip instead of fetching the full catalogue and filtering
client-side.

Pins:

* the row shape matches a row from ``runtime_catalog()`` exactly (so the
  scalar and bulk accessors cannot drift)
* every id in ``ALL_RUNTIMES`` round-trips through ``runtime_spec``
* unknown / empty / ``None`` ids return ``None``
* aliases (``claude-code``) canonicalise to ``claude_code``
* the input is trimmed + lowercased before resolution
* grace mode reports zero locked rows (zero behaviour change)
* enforce-mode lock state on an OSS install matches the catalogue
* the endpoint 400s on a missing arg, 404s on an unknown id, and falls
  back gracefully if the resolver crashes
"""
from __future__ import annotations

import importlib
import json

import pytest


_SPEC_KEYS = {
    "id",
    "label",
    "free",
    "tier",
    "tiers",
    "allowed",
    "locked",
    "entitled",
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


# ── shape ─────────────────────────────────────────────────────────────────────


def test_spec_row_keys_match_catalog_row(ent):
    """A row from ``runtime_spec`` carries the same keys as a
    ``runtime_catalog()`` row -- defends against a rename on one side
    silently shipping a half-renamed payload to the UI."""
    cat_keys = set(ent.runtime_catalog()[0].keys())
    assert cat_keys == _SPEC_KEYS
    rt = next(iter(ent.FREE_RUNTIMES))
    spec = ent.runtime_spec(rt)
    assert spec is not None
    assert set(spec.keys()) == _SPEC_KEYS


def test_spec_parity_with_every_catalog_row(ent):
    """For every row in the catalogue, the scalar accessor returns the
    same dict. Pins the scalar/bulk no-drift contract."""
    cat_by_id = {row["id"]: row for row in ent.runtime_catalog()}
    for rt, row in cat_by_id.items():
        assert ent.runtime_spec(rt) == row, rt


# ── round-trip ────────────────────────────────────────────────────────────────


def test_every_known_runtime_round_trips(ent):
    for rt in ent.ALL_RUNTIMES:
        spec = ent.runtime_spec(rt)
        assert spec is not None, rt
        assert spec["id"] == rt


def test_unknown_runtime_returns_none(ent):
    assert ent.runtime_spec("not_a_real_runtime") is None


def test_empty_returns_none(ent):
    assert ent.runtime_spec("") is None


def test_none_returns_none(ent):
    assert ent.runtime_spec(None) is None


def test_non_string_returns_none(ent):
    assert ent.runtime_spec(123) is None
    assert ent.runtime_spec(object()) is None


def test_input_is_lowercased_and_trimmed(ent):
    rt = next(iter(ent.FREE_RUNTIMES))
    assert ent.runtime_spec(rt.upper()) == ent.runtime_spec(rt)
    assert ent.runtime_spec(f"  {rt}  ") == ent.runtime_spec(rt)


def test_alias_canonicalises_to_canonical_id(ent):
    """``RUNTIME_ALIASES`` carries ``claude-code`` -> ``claude_code`` so
    a frontend that still uses the dash-form can hit the spec endpoint
    without translating client-side. The returned row always echoes the
    canonical id."""
    if "claude-code" in ent.RUNTIME_ALIASES:
        spec = ent.runtime_spec("claude-code")
        assert spec is not None
        assert spec["id"] == "claude_code"


# ── free vs paid carriage ─────────────────────────────────────────────────────


def test_free_runtimes_carry_free_tier_and_unlocked(ent):
    for rt in ent.FREE_RUNTIMES:
        row = ent.runtime_spec(rt)
        assert row["free"] is True, rt
        assert row["tier"] == "free", rt
        assert row["locked"] is False, rt
        assert row["allowed"] is True, rt
        assert row["entitled"] is True, rt


def test_paid_runtimes_carry_starter_tier(ent):
    for rt in ent.PAID_RUNTIMES:
        row = ent.runtime_spec(rt)
        assert row["free"] is False, rt
        assert row["tier"] == "starter", rt


def test_tiers_field_matches_runtime_tier_ids(ent):
    for rt in ent.ALL_RUNTIMES:
        row = ent.runtime_spec(rt)
        assert row["tiers"] == ent._runtime_tier_ids(rt), rt


# ── grace vs enforce ──────────────────────────────────────────────────────────


def test_grace_locks_nothing(ent):
    for rt in ent.ALL_RUNTIMES:
        row = ent.runtime_spec(rt)
        assert row["allowed"] is True, rt
        assert row["locked"] is False, rt


def test_enforce_oss_locks_every_paid_runtime(ent, monkeypatch):
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    ent.invalidate()
    for rt in ent.FREE_RUNTIMES:
        row = ent.runtime_spec(rt)
        assert row["locked"] is False, rt
        assert row["allowed"] is True, rt
        assert row["entitled"] is True, rt
    for rt in ent.PAID_RUNTIMES:
        row = ent.runtime_spec(rt)
        assert row["locked"] is True, rt
        assert row["allowed"] is False, rt
        assert row["entitled"] is False, rt


def test_enforce_cloud_pro_unlocks_paid_runtimes(ent, monkeypatch, tmp_path):
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    cache = tmp_path / ".clawmetry" / "cloud_plan.json"
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(json.dumps({"plan": "cloud_pro"}))
    ent.invalidate()
    for rt in ent.PAID_RUNTIMES:
        row = ent.runtime_spec(rt)
        assert row["allowed"] is True, rt
        assert row["locked"] is False, rt
        assert row["entitled"] is True, rt


# ── never-raise ───────────────────────────────────────────────────────────────


def test_never_raises_when_resolver_crashes(ent, monkeypatch):
    """A blown resolver still returns the catalogue row built against
    the OSS-free fallback -- matches the never-crash contract on
    ``runtime_catalog()``."""

    def boom(*_a, **_kw):
        raise RuntimeError("simulated resolver failure")

    monkeypatch.setattr(ent, "get_entitlement", boom)
    rt = next(iter(ent.FREE_RUNTIMES))
    row = ent.runtime_spec(rt)
    assert row is not None
    assert row["id"] == rt
    assert row["free"] is True


# ── HTTP endpoint ─────────────────────────────────────────────────────────────


def test_endpoint_known_runtime_returns_row(client, ent):
    rt = next(iter(ent.FREE_RUNTIMES))
    resp = client.get(f"/api/entitlement/runtime-spec?runtime={rt}")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body == ent.runtime_spec(rt)


def test_endpoint_lowercases_and_trims(client, ent):
    rt = next(iter(ent.FREE_RUNTIMES))
    resp = client.get(
        f"/api/entitlement/runtime-spec?runtime=%20%20{rt.upper()}%20%20"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["id"] == rt


def test_endpoint_resolves_alias_to_canonical_id(client, ent):
    if "claude-code" not in ent.RUNTIME_ALIASES:
        pytest.skip("claude-code alias not registered")
    resp = client.get("/api/entitlement/runtime-spec?runtime=claude-code")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["id"] == "claude_code"


def test_endpoint_missing_arg_returns_400(client):
    resp = client.get("/api/entitlement/runtime-spec")
    assert resp.status_code == 400
    assert "error" in resp.get_json()


def test_endpoint_blank_arg_returns_400(client):
    resp = client.get("/api/entitlement/runtime-spec?runtime=%20%20")
    assert resp.status_code == 400


def test_endpoint_unknown_runtime_returns_404(client):
    resp = client.get("/api/entitlement/runtime-spec?runtime=nonsense_xyz")
    assert resp.status_code == 404
    body = resp.get_json()
    assert body["runtime"] == "nonsense_xyz"
    assert "error" in body


def test_endpoint_every_known_runtime_round_trips(client, ent):
    for rt in ent.ALL_RUNTIMES:
        resp = client.get(f"/api/entitlement/runtime-spec?runtime={rt}")
        assert resp.status_code == 200, rt
        body = resp.get_json()
        assert body["id"] == rt, rt


def test_endpoint_returns_grace_row_even_when_resolver_crashes(client, ent, monkeypatch):
    """``runtime_spec`` catches resolver failures internally and falls
    back to the OSS-free row, so the endpoint must return 200 + a
    valid catalogue row even when ``get_entitlement`` explodes."""

    def boom(*_a, **_kw):
        raise RuntimeError("simulated resolver failure")

    monkeypatch.setattr(ent, "get_entitlement", boom)
    rt = next(iter(ent.FREE_RUNTIMES))
    resp = client.get(f"/api/entitlement/runtime-spec?runtime={rt}")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["id"] == rt
    assert body["free"] is True
