"""Tests for the entry-point plugin loader's introspection surface.

Pins the diagnostic API operators read to confirm ``clawmetry-pro`` (or any
other ``clawmetry.extensions`` entry point) has actually loaded on a node:

- ``clawmetry.extensions.loaded_plugins()`` — names of plugins that loaded
  successfully in this process.
- ``GET /api/extensions`` — wire shape carrying those names plus the
  registered-event hooks, never-raising on any introspection failure.
"""
from __future__ import annotations

import json

import pytest
from flask import Flask

import clawmetry.extensions as ext


class _FakeEntryPoint:
    """Stub mimicking importlib.metadata.EntryPoint."""

    def __init__(self, fn, name="fake"):
        self._fn = fn
        self.name = name

    def load(self):
        return self._fn


def _fake_eps(*pairs):
    return [_FakeEntryPoint(fn, name=n) for fn, n in pairs]


@pytest.fixture(autouse=True)
def _reset_loader():
    """Drop the once-guard + the loaded-name mirror before every test so
    monkeypatched entry points actually run. Also snapshot/restore the event
    registry so handlers registered here can't leak into adjacent suites and
    handlers from adjacent suites can't leak in here."""
    ext._loaded = False
    with ext._lock:
        ext._loaded_plugins.clear()
        prior_registry = {k: list(v) for k, v in ext._registry.items()}
        ext._registry.clear()
    yield
    ext._loaded = False
    with ext._lock:
        ext._loaded_plugins.clear()
        ext._registry.clear()
        ext._registry.update(prior_registry)


# ── loaded_plugins() ─────────────────────────────────────────────────────────


def test_loaded_plugins_empty_before_load():
    assert ext.loaded_plugins() == []


def test_loaded_plugins_returns_a_copy():
    """Caller mutation must not corrupt the registry."""
    ext.loaded_plugins().append("ghost")
    assert ext.loaded_plugins() == []


def test_loaded_plugins_records_successful_loads(monkeypatch):
    monkeypatch.setattr(
        ext, "_select_entry_points",
        lambda group: _fake_eps((lambda: None, "alpha"), (lambda: None, "beta")),
    )
    ext.load_plugins()
    assert ext.loaded_plugins() == ["alpha", "beta"]


def test_loaded_plugins_excludes_failed_plugins(monkeypatch):
    """A plugin that raised during load must NOT appear — operators rely on
    this list to confirm successful wiring, not attempted wiring."""
    def boom():
        raise RuntimeError("boom")

    def good():
        return None

    monkeypatch.setattr(
        ext, "_select_entry_points",
        lambda group: _fake_eps((boom, "broken"), (good, "ok")),
    )
    ext.load_plugins()
    assert ext.loaded_plugins() == ["ok"]


def test_loaded_plugins_resets_on_reentry(monkeypatch):
    """If a test flips ``_loaded`` back to False, the next load_plugins()
    call must start the list fresh (no duplicates from the prior pass)."""
    monkeypatch.setattr(
        ext, "_select_entry_points",
        lambda group: _fake_eps((lambda: None, "alpha")),
    )
    ext.load_plugins()
    assert ext.loaded_plugins() == ["alpha"]
    # Simulate a process where ``_loaded`` was reset (test fixture, reload, …).
    ext._loaded = False
    ext.load_plugins()
    assert ext.loaded_plugins() == ["alpha"]  # not ["alpha", "alpha"]


def test_loaded_plugins_records_app_style_plugins(monkeypatch):
    """A plugin with ``register_all(app)`` is also recorded once invoked."""
    received = []
    monkeypatch.setattr(
        ext, "_select_entry_points",
        lambda group: _fake_eps((lambda app: received.append(app), "needs-app")),
    )
    sentinel = object()
    ext.load_plugins(app=sentinel)
    assert received == [sentinel]
    assert ext.loaded_plugins() == ["needs-app"]


# ── GET /api/extensions ──────────────────────────────────────────────────────


@pytest.fixture
def client():
    from routes.extensions import bp_extensions

    app = Flask(__name__)
    app.register_blueprint(bp_extensions)
    return app.test_client()


def test_api_extensions_shape_empty(client):
    resp = client.get("/api/extensions")
    assert resp.status_code == 200
    body = json.loads(resp.data)
    assert body == {
        "plugins": [],
        "plugin_count": 0,
        "events": [],
        "handler_counts": {},
    }


def test_api_extensions_reports_loaded_plugins(client, monkeypatch):
    monkeypatch.setattr(
        ext, "_select_entry_points",
        lambda group: _fake_eps((lambda: None, "clawmetry-pro")),
    )
    ext.load_plugins()

    body = json.loads(client.get("/api/extensions").data)
    assert body["plugins"] == ["clawmetry-pro"]
    assert body["plugin_count"] == 1


def test_api_extensions_reports_registered_events(client):
    ext.register("test.evt.api.a", lambda p: None)
    ext.register("test.evt.api.a", lambda p: None)  # 2 handlers for one event
    ext.register("test.evt.api.b", lambda p: None)

    body = json.loads(client.get("/api/extensions").data)
    assert "test.evt.api.a" in body["events"]
    assert "test.evt.api.b" in body["events"]
    assert body["handler_counts"]["test.evt.api.a"] >= 2
    assert body["handler_counts"]["test.evt.api.b"] >= 1


def test_api_extensions_never_raises(client, monkeypatch):
    """If introspection itself blows up, the endpoint still returns 200 with
    a safe empty shape — the dashboard always has something to render."""
    def explode():
        raise RuntimeError("introspection broken")

    monkeypatch.setattr(ext, "loaded_plugins", explode)

    resp = client.get("/api/extensions")
    assert resp.status_code == 200
    body = json.loads(resp.data)
    assert body == {
        "plugins": [],
        "plugin_count": 0,
        "events": [],
        "handler_counts": {},
    }
