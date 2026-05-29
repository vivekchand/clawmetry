"""Tests for routes/runtime_ingest.py — /api/v1/runs/* and /api/v1/engines/*.

All tests are hermetic (no live server, no gateway, no DuckDB on disk).
"""
from __future__ import annotations

import importlib

import pytest
from flask import Flask, jsonify


@pytest.fixture
def client(monkeypatch, tmp_path):
    """Minimal Flask test client with only bp_runtime_ingest registered."""
    monkeypatch.setenv("HOME", str(tmp_path))
    # Reload entitlements so no stale license cache is carried over.
    import clawmetry.entitlements as _ent
    importlib.reload(_ent)
    _ent.invalidate()

    # Clear the extensions registry so no leftover handlers bleed between tests.
    import clawmetry.extensions as _ext
    importlib.reload(_ext)

    from routes.runtime_ingest import bp_runtime_ingest

    app = Flask(__name__)
    app.register_blueprint(bp_runtime_ingest)
    app.config["TESTING"] = True
    return app.test_client()


# ── 402 stub behaviour ────────────────────────────────────────────────────────

def test_post_runs_returns_402(client):
    r = client.post("/api/v1/runs/my-run", json={"data": 1})
    assert r.status_code == 402
    body = r.get_json()
    assert body["error"] == "upgrade_required"
    assert body["feature"] == "custom_runtime_ingest"
    assert "hint" in body


def test_get_runs_returns_402(client):
    r = client.get("/api/v1/runs/some/nested/path")
    assert r.status_code == 402


def test_post_engines_returns_402(client):
    r = client.post("/api/v1/engines/my-engine")
    assert r.status_code == 402
    assert r.get_json()["feature"] == "custom_runtime_ingest"


def test_get_engines_root_returns_402(client):
    r = client.get("/api/v1/engines/")
    assert r.status_code == 402


# ── Plugin delegation ─────────────────────────────────────────────────────────

def test_runs_delegates_to_registered_plugin(client, monkeypatch, tmp_path):
    """A registered 'runtime_ingest.request' handler gets the call and its
    response is forwarded to the HTTP client."""
    import clawmetry.extensions as ext

    captured = {}

    def my_handler(payload):
        captured.update(payload)
        return jsonify({"accepted": True, "path": payload["path"]}), 201

    ext.register("runtime_ingest.request", my_handler)

    r = client.post("/api/v1/runs/run-xyz", json={"foo": "bar"})
    assert r.status_code == 201
    body = r.get_json()
    assert body["accepted"] is True
    assert body["path"] == "runs/run-xyz"
    assert captured["method"] == "POST"
    assert captured["body"] == {"foo": "bar"}


def test_engines_delegates_to_registered_plugin(client, monkeypatch, tmp_path):
    import clawmetry.extensions as ext

    def engine_handler(payload):
        return jsonify({"engine": payload["path"]}), 200

    ext.register("runtime_ingest.request", engine_handler)

    r = client.get("/api/v1/engines/my-engine")
    assert r.status_code == 200
    assert r.get_json()["engine"] == "engines/my-engine"


def test_none_returning_plugin_falls_through_to_402(client, monkeypatch, tmp_path):
    """A handler that returns None should not block the 402 fallback."""
    import clawmetry.extensions as ext

    def passive_handler(payload):
        return None  # explicitly declines

    ext.register("runtime_ingest.request", passive_handler)

    r = client.post("/api/v1/runs/declined")
    assert r.status_code == 402


# ── Entitlement key present ───────────────────────────────────────────────────

def test_custom_runtime_ingest_in_paid_features():
    """The feature key must exist in PAID_FEATURES so allows_feature() is
    consistent and the entitlement system has a stable string to gate on."""
    from clawmetry.entitlements import PAID_FEATURES
    assert "custom_runtime_ingest" in PAID_FEATURES


# ── extensions.dispatch present ───────────────────────────────────────────────

def test_dispatch_returns_first_non_none():
    from clawmetry.extensions import register, dispatch, _registry

    _registry.pop("test_dispatch_event", None)
    try:
        calls = []

        def h1(p):
            calls.append("h1")
            return None

        def h2(p):
            calls.append("h2")
            return "result-from-h2"

        def h3(p):
            calls.append("h3")
            return "should-not-reach"

        register("test_dispatch_event", h1)
        register("test_dispatch_event", h2)
        register("test_dispatch_event", h3)

        result = dispatch("test_dispatch_event", {})
        assert result == "result-from-h2"
        assert calls == ["h1", "h2"]  # h3 never called
    finally:
        _registry.pop("test_dispatch_event", None)


def test_dispatch_returns_none_when_no_handlers():
    from clawmetry.extensions import dispatch, _registry

    _registry.pop("unregistered_event_xyz", None)
    assert dispatch("unregistered_event_xyz") is None
