"""Enforce-mode contract tests for the ``bp_assets`` JSON API.

``asset_registry`` is a Pro-only feature (see ``PRO_ONLY_FEATURES`` in
``clawmetry/entitlements.py``). All four JSON endpoints on ``bp_assets``
(list, get one, create, review) implement it, so they all wear the
``@gate("asset_registry")`` decorator.

These tests pin two things so a future edit can't silently break the
tier story:

  1. Enforce mode: each endpoint returns a 402 ``upgrade_required``
     body with ``feature="asset_registry"`` and
     ``required_tier=TIER_CLOUD_PRO``. The gate check fires before any
     handler code runs, so the 402 short-circuits before the daemon /
     DuckDB path is even touched — no ``_try_store_call`` monkeypatch
     needed.
  2. Grace mode: the gate is transparent. The endpoint doesn't
     short-circuit with 402; whatever the downstream handler returns
     (200 empty list, 4xx bad request, 5xx if the daemon is off) wins.

Companion to ``tests/test_route_gates.py`` (which pins the same contract
for one representative endpoint) and follows the same pattern used for
``bp_alerts`` and ``bp_policy`` gates.
"""
from __future__ import annotations

import importlib
import json

import pytest
from flask import Flask


@pytest.fixture
def enforce(monkeypatch, tmp_path):
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    monkeypatch.setenv("HOME", str(tmp_path))
    import clawmetry.entitlements as e

    importlib.reload(e)
    e.invalidate()
    yield e
    e.invalidate()


@pytest.fixture
def grace(monkeypatch, tmp_path):
    monkeypatch.delenv("CLAWMETRY_ENFORCE", raising=False)
    monkeypatch.setenv("HOME", str(tmp_path))
    import clawmetry.entitlements as e

    importlib.reload(e)
    e.invalidate()
    yield e
    e.invalidate()


def _app_with_assets_bp():
    from routes.assets import bp_assets

    app = Flask(__name__)
    app.register_blueprint(bp_assets)
    return app


# ── enforce mode: 402 on every JSON endpoint ─────────────────────────────────


_ENFORCE_MATRIX = [
    ("GET", "/api/assets", None),
    ("GET", "/api/assets/asset-abc", None),
    ("POST", "/api/assets", {"asset_type": "skill", "name": "hello"}),
    ("POST", "/api/assets/asset-abc/review", {"action": "approve"}),
]


@pytest.mark.parametrize("method,path,body", _ENFORCE_MATRIX)
def test_assets_endpoint_returns_402_when_enforced(enforce, method, path, body):
    app = _app_with_assets_bp()
    with app.test_client() as c:
        r = c.open(
            path,
            method=method,
            data=json.dumps(body) if body is not None else None,
            content_type="application/json" if body is not None else None,
        )
        assert r.status_code == 402, (
            f"{method} {path} returned {r.status_code}, expected 402 "
            "(gate should short-circuit before handler runs)"
        )
        payload = r.get_json()
        assert payload["error"] == "upgrade_required"
        assert payload["feature"] == "asset_registry"
        assert payload["required_tier"] == enforce.TIER_CLOUD_PRO
        # ``tier`` reflects the caller's current tier so the UI can render
        # the delta ("you have X, upgrade to Y"). On an OSS install with no
        # license, this is TIER_OSS.
        assert payload["tier"] == enforce.TIER_OSS


# ── grace mode: gate is transparent on every JSON endpoint ───────────────────


@pytest.mark.parametrize("method,path,body", _ENFORCE_MATRIX)
def test_assets_endpoint_is_transparent_in_grace_mode(
    monkeypatch, grace, method, path, body
):
    # Stub the DuckDB path so the handler returns deterministically in-process
    # without needing the sync daemon or a real store. The gate should be a
    # no-op in grace mode; the stub just proves the handler ran through.
    def _stub_try_store_call(method_name, **kwargs):
        if method_name == "get_asset":
            return {"id": kwargs.get("asset_id"), "asset_type": "skill"}
        if method_name == "query_assets":
            return []
        if method_name == "ingest_asset":
            return True
        if method_name == "update_asset_status":
            return True
        return None

    import routes.assets as _assets_mod
    monkeypatch.setattr(_assets_mod, "_try_store_call", _stub_try_store_call)

    app = _app_with_assets_bp()
    with app.test_client() as c:
        r = c.open(
            path,
            method=method,
            data=json.dumps(body) if body is not None else None,
            content_type="application/json" if body is not None else None,
        )
        assert r.status_code != 402, (
            f"{method} {path} 402'd in grace mode; gate is not transparent"
        )


# ── enforce mode: 402 wins over routing errors on the JSON endpoints ─────────


def test_enforce_mode_402_precedes_json_validation(enforce):
    """Gate must fire before body validation. A POST with a missing required
    field would normally 400; in enforce mode it should still 402 so the UI
    renders the upgrade CTA, not a validation error."""
    app = _app_with_assets_bp()
    with app.test_client() as c:
        r = c.post("/api/assets", json={})  # missing asset_type + name
        assert r.status_code == 402
        assert r.get_json()["feature"] == "asset_registry"


# ── defensive: an entitlement-lookup crash falls through, does NOT 402 ──────


def test_entitlement_lookup_crash_falls_through(monkeypatch, enforce):
    """Mirrors the contract in tests/test_route_gates.py: if the entitlement
    read itself raises, the request path stays defensive and the handler
    runs — the worst that happens is a paid feature briefly runs on a Free
    tier. A flaky entitlement check must never fail closed."""
    def _explode():
        raise RuntimeError("boom")

    monkeypatch.setattr("clawmetry.entitlements.get_entitlement", _explode)

    def _stub_try_store_call(method_name, **kwargs):
        return [] if method_name == "query_assets" else None

    import routes.assets as _assets_mod
    monkeypatch.setattr(_assets_mod, "_try_store_call", _stub_try_store_call)

    app = _app_with_assets_bp()
    with app.test_client() as c:
        r = c.get("/api/assets")
        assert r.status_code != 402
