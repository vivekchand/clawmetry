"""Tests for the OSS 402-stub behavior for Phase 2 (selfevolve + assets).

These pin the shape OSS-only installs see when clawmetry-pro is NOT
loaded. The full-impl tests for selfevolve + assets live in
clawmetry-pro (private).
"""
from __future__ import annotations

import importlib

import pytest
from flask import Flask


# ── selfevolve stub ──────────────────────────────────────────────────────────


@pytest.fixture
def app_selfevolve(monkeypatch, tmp_path):
    monkeypatch.delenv("CLAWMETRY_ENFORCE", raising=False)
    monkeypatch.setenv("HOME", str(tmp_path))
    import clawmetry.entitlements as _ent
    importlib.reload(_ent)
    _ent.invalidate()
    from routes import selfevolve as _se
    importlib.reload(_se)
    app = Flask(__name__)
    app.register_blueprint(_se.bp_selfevolve)
    return app


@pytest.mark.parametrize("path,method", [
    ("/api/selfevolve/status", "GET"),
    ("/api/selfevolve/latest", "GET"),
    ("/api/selfevolve/analyze", "POST"),
    ("/api/selfevolve/fix", "POST"),
    ("/api/selfevolve/fix/status", "GET"),
    ("/api/selfevolve/findings/abc/save-as-asset", "POST"),
])
def test_selfevolve_stubs_return_402(app_selfevolve, path, method):
    with app_selfevolve.test_client() as c:
        r = c.open(path, method=method)
        assert r.status_code == 402, f"{method} {path} returned {r.status_code}"
        body = r.get_json()
        assert body["error"] == "upgrade_required"
        assert body["feature"] == "self_evolve"
        assert "clawmetry-pro" in body["hint"]


# ── assets stub ──────────────────────────────────────────────────────────────


@pytest.fixture
def app_assets(monkeypatch, tmp_path):
    monkeypatch.delenv("CLAWMETRY_ENFORCE", raising=False)
    monkeypatch.setenv("HOME", str(tmp_path))
    import clawmetry.entitlements as _ent
    importlib.reload(_ent)
    _ent.invalidate()
    from routes import assets as _a
    importlib.reload(_a)
    app = Flask(__name__)
    app.register_blueprint(_a.bp_assets)
    return app


@pytest.mark.parametrize("path,method", [
    ("/api/assets", "GET"),
    ("/api/assets/abc", "GET"),
    ("/api/assets", "POST"),
    ("/api/assets/abc/review", "POST"),
])
def test_assets_stubs_return_402(app_assets, path, method):
    with app_assets.test_client() as c:
        r = c.open(path, method=method)
        assert r.status_code == 402, f"{method} {path} returned {r.status_code}"
        body = r.get_json()
        assert body["error"] == "upgrade_required"
        assert body["feature"] == "asset_registry"
        assert "clawmetry-pro" in body["hint"]
