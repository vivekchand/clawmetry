"""Tests for ``clawmetry.entitlements.resolution_diagnostic()`` and the
companion ``GET /api/entitlement/diagnostic`` endpoint.

The diagnostic surfaces the *inputs* to entitlement resolution — license file
presence, cloud-plan cache presence, the raw ``CLAWMETRY_ENFORCE`` env value
+ the bool it resolves to, and the in-process cache liveness. This is the
operator triage surface for "why does this install think it's on tier X?".

Pins:
    * Default OSS shape (no files present, enforce off) reports the expected
      paths and booleans.
    * The ``license_path`` / ``cloud_plan_path`` reflect ``HOME`` — proving
      no real ``$HOME/.clawmetry`` leaks in.
    * ``license_present`` / ``cloud_plan_present`` + ``*_size_bytes`` flip on
      when the files exist.
    * File *contents* are never read or surfaced (only path + size + presence).
    * ``CLAWMETRY_ENFORCE`` is reflected accurately (raw env + ``is_enforced``).
    * Cache liveness flips with ``get_entitlement()`` calls + ``invalidate()``.
    * The route returns a 200 + the helper's shape; falls back gracefully
      when the helper raises (never 5xx).
"""
from __future__ import annotations

import importlib
import json
import os
import time

import pytest
from flask import Flask


# ── fixtures ─────────────────────────────────────────────────────────────────


@pytest.fixture
def ent(monkeypatch, tmp_path):
    """Fresh entitlements module with HOME pointed at an empty tmp dir so no
    real ``~/.clawmetry/license.key`` or ``cloud_plan.json`` leaks in."""
    monkeypatch.delenv("CLAWMETRY_ENFORCE", raising=False)
    monkeypatch.setenv("HOME", str(tmp_path))
    import clawmetry.entitlements as e

    importlib.reload(e)
    e.invalidate()
    yield e, tmp_path
    e.invalidate()


@pytest.fixture
def client(monkeypatch, tmp_path):
    """Flask test client with bp_entitlement wired and a clean HOME."""
    monkeypatch.delenv("CLAWMETRY_ENFORCE", raising=False)
    monkeypatch.setenv("HOME", str(tmp_path))
    import clawmetry.entitlements as e

    importlib.reload(e)
    e.invalidate()

    from routes.entitlement import bp_entitlement

    app = Flask(__name__)
    app.register_blueprint(bp_entitlement)
    return app.test_client(), tmp_path


# ── resolution_diagnostic() shape ────────────────────────────────────────────


def test_resolution_diagnostic_default_shape(ent):
    """Empty HOME, no enforce env: known keys present, sensible defaults."""
    e, tmp_path = ent
    d = e.resolution_diagnostic()
    for key in (
        "license_path",
        "license_present",
        "license_size_bytes",
        "cloud_plan_path",
        "cloud_plan_present",
        "cloud_plan_size_bytes",
        "enforce_env",
        "is_enforced",
        "cache_age_seconds",
        "cache_ttl_seconds",
        "cache_hit_next_call",
        "cache_cached_tier",
    ):
        assert key in d, key
    assert d["license_present"] is False
    assert d["license_size_bytes"] == 0
    assert d["cloud_plan_present"] is False
    assert d["cloud_plan_size_bytes"] == 0
    assert d["enforce_env"] is None
    assert d["is_enforced"] is False
    # Empty cache before any get_entitlement() call.
    assert d["cache_age_seconds"] is None
    assert d["cache_hit_next_call"] is False
    assert d["cache_cached_tier"] is None
    assert isinstance(d["cache_ttl_seconds"], (int, float))
    assert d["cache_ttl_seconds"] > 0


def test_resolution_diagnostic_paths_reflect_home(ent):
    """The paths must root under the test HOME — proves no real ~/.clawmetry
    leaks into the test."""
    e, tmp_path = ent
    d = e.resolution_diagnostic()
    # _LICENSE_PATH / _CLOUD_PLAN_CACHE are computed at module import via
    # os.path.expanduser; reload above re-evaluates them under our HOME.
    assert str(tmp_path) in d["license_path"]
    assert str(tmp_path) in d["cloud_plan_path"]
    assert d["license_path"].endswith("license.key")
    assert d["cloud_plan_path"].endswith("cloud_plan.json")


def test_resolution_diagnostic_is_json_serializable(ent):
    """Dashboard / CLI consume this via JSON — pin a clean round-trip so a
    stray frozenset/Path leak fails loudly here, not in /api/entitlement/diagnostic."""
    e, _ = ent
    d = e.resolution_diagnostic()
    assert json.loads(json.dumps(d)) == d


# ── license / cloud-plan presence ────────────────────────────────────────────


def test_license_present_flips_when_file_exists(ent):
    e, tmp_path = ent
    lic = tmp_path / ".clawmetry" / "license.key"
    lic.parent.mkdir(parents=True, exist_ok=True)
    lic.write_text("CLAW1.fake.fake")
    d = e.resolution_diagnostic()
    assert d["license_present"] is True
    assert d["license_size_bytes"] == len("CLAW1.fake.fake")


def test_cloud_plan_present_flips_when_file_exists(ent):
    e, tmp_path = ent
    cp = tmp_path / ".clawmetry" / "cloud_plan.json"
    cp.parent.mkdir(parents=True, exist_ok=True)
    cp.write_text(json.dumps({"plan": "cloud_starter"}))
    d = e.resolution_diagnostic()
    assert d["cloud_plan_present"] is True
    assert d["cloud_plan_size_bytes"] > 0


def test_resolution_diagnostic_never_surfaces_file_contents(ent):
    """Critical: the diagnostic exposes paths + presence + size, never the
    license body. A leaked license key in the diagnostic would defeat the
    whole point of the file-permission hardening."""
    e, tmp_path = ent
    lic = tmp_path / ".clawmetry" / "license.key"
    lic.parent.mkdir(parents=True, exist_ok=True)
    secret = "CLAW1.SECRET_BODY_SHOULD_NEVER_LEAK"
    lic.write_text(secret)
    cp = tmp_path / ".clawmetry" / "cloud_plan.json"
    cloud_secret_marker = "CLOUD_SECRET_SHOULD_NEVER_LEAK"
    cp.write_text(json.dumps({"plan": "cloud_pro", "note": cloud_secret_marker}))
    blob = json.dumps(e.resolution_diagnostic())
    assert "SECRET_BODY_SHOULD_NEVER_LEAK" not in blob
    assert cloud_secret_marker not in blob


# ── enforce env reflection ───────────────────────────────────────────────────


def test_resolution_diagnostic_reflects_enforce_env(monkeypatch, tmp_path):
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    monkeypatch.setenv("HOME", str(tmp_path))
    import clawmetry.entitlements as e

    importlib.reload(e)
    e.invalidate()
    d = e.resolution_diagnostic()
    assert d["enforce_env"] == "1"
    assert d["is_enforced"] is True


def test_resolution_diagnostic_reports_raw_env_even_when_invalid(monkeypatch, tmp_path):
    """Raw env is reported verbatim so operators see typos like
    'CLAWMETRY_ENFORCE=enabled' that *look* on but resolve to off."""
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "enabled")
    monkeypatch.setenv("HOME", str(tmp_path))
    import clawmetry.entitlements as e

    importlib.reload(e)
    e.invalidate()
    d = e.resolution_diagnostic()
    assert d["enforce_env"] == "enabled"
    assert d["is_enforced"] is False  # not in _ENFORCE_ENABLE_VALUES


# ── cache liveness ───────────────────────────────────────────────────────────


def test_cache_age_and_hit_after_get_entitlement(ent):
    e, _ = ent
    e.get_entitlement(force=True)
    d = e.resolution_diagnostic()
    assert d["cache_age_seconds"] is not None
    assert d["cache_age_seconds"] >= 0.0
    assert d["cache_hit_next_call"] is True
    assert d["cache_cached_tier"] == "oss"


def test_cache_invalidate_resets_diagnostic(ent):
    e, _ = ent
    e.get_entitlement(force=True)
    e.invalidate()
    d = e.resolution_diagnostic()
    assert d["cache_age_seconds"] is None
    assert d["cache_hit_next_call"] is False
    assert d["cache_cached_tier"] is None


def test_cache_age_grows_over_time(ent):
    e, _ = ent
    e.get_entitlement(force=True)
    first = e.resolution_diagnostic()["cache_age_seconds"]
    time.sleep(0.02)
    second = e.resolution_diagnostic()["cache_age_seconds"]
    assert second >= first


# ── /api/entitlement/diagnostic endpoint ─────────────────────────────────────


def test_api_entitlement_diagnostic_returns_helper_shape(client):
    c, _ = client
    resp = c.get("/api/entitlement/diagnostic")
    assert resp.status_code == 200
    d = resp.get_json()
    for key in (
        "license_path",
        "license_present",
        "cloud_plan_path",
        "cloud_plan_present",
        "enforce_env",
        "is_enforced",
        "cache_age_seconds",
        "cache_ttl_seconds",
        "cache_hit_next_call",
        "cache_cached_tier",
    ):
        assert key in d, key


def test_api_entitlement_diagnostic_reflects_enforce(monkeypatch, tmp_path):
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    monkeypatch.setenv("HOME", str(tmp_path))
    import clawmetry.entitlements as e

    importlib.reload(e)
    e.invalidate()

    from routes.entitlement import bp_entitlement

    app = Flask(__name__)
    app.register_blueprint(bp_entitlement)
    d = app.test_client().get("/api/entitlement/diagnostic").get_json()
    assert d["enforce_env"] == "1"
    assert d["is_enforced"] is True


def test_api_entitlement_diagnostic_never_raises(monkeypatch, client):
    """When the helper itself explodes the route must still return a 200 +
    a minimal safe shape — the dashboard polls this endpoint."""
    c, _ = client

    def _boom():
        raise RuntimeError("simulated diagnostic breakage")

    import clawmetry.entitlements as e

    monkeypatch.setattr(e, "resolution_diagnostic", _boom)
    resp = c.get("/api/entitlement/diagnostic")
    assert resp.status_code == 200
    d = resp.get_json()
    # The fallback still carries the structural keys callers depend on.
    for key in (
        "license_path",
        "license_present",
        "cloud_plan_path",
        "cloud_plan_present",
        "enforce_env",
        "is_enforced",
    ):
        assert key in d, key
    assert d["license_present"] is False
    assert d["cloud_plan_present"] is False
    assert d.get("error")


def test_api_entitlement_diagnostic_does_not_leak_file_contents(client, tmp_path):
    """End-to-end mirror of the helper-level secrecy test — pin that the route
    surface, not just the helper, refuses to surface license / cloud-plan body
    bytes."""
    c, _ = client
    lic = tmp_path / ".clawmetry" / "license.key"
    lic.parent.mkdir(parents=True, exist_ok=True)
    secret = "CLAW1.ROUTE_SECRET_NO_LEAK"
    lic.write_text(secret)
    cp = tmp_path / ".clawmetry" / "cloud_plan.json"
    cloud_secret = "ROUTE_CLOUD_SECRET_NO_LEAK"
    cp.write_text(json.dumps({"plan": "cloud_pro", "note": cloud_secret}))
    blob = c.get("/api/entitlement/diagnostic").get_data(as_text=True)
    assert "ROUTE_SECRET_NO_LEAK" not in blob
    assert cloud_secret not in blob
