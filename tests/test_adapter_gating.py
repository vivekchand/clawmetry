"""Tests for adapter / runtime-ingest gating under enforced OSS (issue #2293).

Closes the gap between ``test_entitlements.py`` (which proves the *gate*
returns the right answer) and the actual *enforcement surfaces* that consume
it. Two surfaces enforce paid-runtime gating in the OSS package:

1. ``routes/runtime_ingest.py`` — the custom-runtime HTTP ingest API. The OSS
   stub returns ``HTTP 402 upgrade_required`` on every write endpoint
   (``POST /api/v1/runs``, ``POST /api/v1/runs/<id>/events``,
   ``POST /api/v1/runs/<id>/end``, ``GET /api/v1/runs/<id>``). The read-only
   ``GET /api/v1/runtimes`` listing stays free.
2. ``clawmetry/adapters/registry.py`` — adapter registration is intentionally
   *not* gated (closed-source ``clawmetry-pro`` packages register their own
   adapters at import time). The gate fires when the runtime catalog is read
   for the UI: every paid runtime is reported ``locked=True`` under enforced
   OSS so it cannot be silently activated through the switcher.

These tests pin both surfaces so a regression in either is loud.
"""
from __future__ import annotations

import importlib
import sys
from pathlib import Path

import pytest
from flask import Flask

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


# ── fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture
def ent(monkeypatch, tmp_path):
    """Fresh entitlements module with HOME pointed at an empty tmp dir."""
    monkeypatch.delenv("CLAWMETRY_ENFORCE", raising=False)
    monkeypatch.setenv("HOME", str(tmp_path))
    import clawmetry.entitlements as e
    importlib.reload(e)
    e.invalidate()
    yield e
    e.invalidate()


@pytest.fixture
def ingest_client():
    """Flask test client wired with the OSS runtime-ingest stub blueprint."""
    from routes.runtime_ingest import bp_runtime_ingest
    app = Flask(__name__)
    app.register_blueprint(bp_runtime_ingest)
    return app.test_client()


# ── runtime-ingest stub: write endpoints return 402 ──────────────────────────


@pytest.mark.parametrize(
    "method,path",
    [
        ("POST", "/api/v1/runs"),
        ("POST", "/api/v1/runs/abc-123/events"),
        ("POST", "/api/v1/runs/abc-123/end"),
        ("GET", "/api/v1/runs/abc-123"),
    ],
)
def test_runtime_ingest_paid_endpoints_return_402(ingest_client, method, path):
    """Every paid runtime-ingest write endpoint returns 402 upgrade_required
    on the OSS stub (no clawmetry-pro installed). This is the wire-level
    contract paid SDK clients depend on so they know to surface the upgrade
    affordance instead of silently failing."""
    resp = ingest_client.open(path, method=method, json={})
    assert resp.status_code == 402, f"{method} {path}"
    body = resp.get_json()
    assert body["error"] == "upgrade_required"
    assert body["feature"] == "custom_runtime_ingest"
    assert "clawmetry-pro" in body["hint"]


def test_runtime_ingest_listing_stays_free(ingest_client):
    """``GET /api/v1/runtimes`` is the catalogue — SDK clients call it before
    they hit the paid write routes to know what they can push to. It must
    NEVER return 402, even on the OSS stub."""
    resp = ingest_client.get("/api/v1/runtimes")
    assert resp.status_code == 200
    body = resp.get_json()
    assert "runtimes" in body
    assert isinstance(body["runtimes"], list)


def test_runtime_ingest_stub_402_independent_of_enforce(ingest_client, monkeypatch):
    """The 402 on paid endpoints is structural (clawmetry-pro not installed),
    not gated on ``CLAWMETRY_ENFORCE``. Flipping enforce does not unlock a
    free user — they still need clawmetry-pro or Cloud Pro."""
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "0")
    resp = ingest_client.post("/api/v1/runs", json={})
    assert resp.status_code == 402
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    resp = ingest_client.post("/api/v1/runs", json={})
    assert resp.status_code == 402


# ── adapter registry: catalog enforces, register() does not ──────────────────


def test_registry_register_does_not_gate(ent):
    """``registry.register()`` is intentionally not gated — clawmetry-pro
    plugins register their own adapters at import time and OSS must let them
    through. The gate fires later, when the runtime catalog is read for the
    UI. This test pins that contract so a well-meaning refactor doesn't add
    an entitlement check inside ``register()`` and break the override path
    proven by ``test_adapter_registry_override.py``."""
    from clawmetry.adapters import base, registry

    class _FakeAdapter(base.AgentAdapter):
        name = "fake_paid_runtime"
        display_name = "Fake Paid Runtime"
        def detect(self): return base.DetectResult(name=self.name, display_name=self.display_name, detected=False)
        def list_sessions(self, limit=100): return []
        def capabilities(self): return set()

    try:
        registry.register(_FakeAdapter())
        # Even when the registry is willing to register a paid-runtime
        # adapter, the entitlement layer is the source of truth — the
        # catalog must still report the (real) paid runtimes as locked.
        assert registry.get("fake_paid_runtime") is not None
    finally:
        registry.unregister("fake_paid_runtime")


def test_runtime_catalog_locks_all_paid_under_oss_enforced(ent, monkeypatch):
    """Under ``TIER_OSS`` enforced, the runtime catalog ``locked`` flag is
    True for every entry in ``PAID_RUNTIMES`` — this is the signal the
    runtime switcher uses to render 🔒 + intercept clicks. If this ever
    flips False, paid runtimes activate silently."""
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    ent.invalidate()
    cat = {r["id"]: r for r in ent.runtime_catalog()}
    for rt in ent.PAID_RUNTIMES:
        assert cat[rt]["locked"] is True, f"{rt} not locked under enforced OSS"
        assert cat[rt]["allowed"] is False, f"{rt} allowed under enforced OSS"
        assert cat[rt]["free"] is False, rt
    for rt in ent.FREE_RUNTIMES:
        assert cat[rt]["locked"] is False, rt
        assert cat[rt]["allowed"] is True, rt
