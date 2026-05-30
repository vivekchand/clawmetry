"""Tests for the ``load_plugins(app)`` wire-up in
``dashboard_claudecode.create_app``.

The Claude Code dashboard variant is a *standalone* Flask app — its
``main()`` builds the app via ``create_app()`` and never imports the main
``dashboard`` module. dashboard.py's import-time ``load_plugins()`` call
therefore never fires for this process. Without an explicit wire-up here,
``clawmetry-pro`` plugins that ship Blueprints scoped to the Claude Code
surface would silently be skipped when a user runs

    python3 dashboard_claudecode.py --port 8901

even though they register correctly on the main dashboard process. These
tests pin down the wire-up so it can't regress.
"""
from __future__ import annotations

import logging

import pytest

import dashboard_claudecode
from clawmetry import extensions as _ext


@pytest.fixture(autouse=True)
def _reset_extensions_guard():
    """Each test gets a clean ``_loaded`` guard so ``load_plugins`` actually
    runs; otherwise the first test that imports anything plugin-adjacent
    would short-circuit later tests."""
    prev = _ext._loaded
    _ext._loaded = False
    try:
        yield
    finally:
        _ext._loaded = prev


def test_create_app_invokes_load_plugins(monkeypatch):
    """``create_app()`` must call ``extensions.load_plugins`` exactly once and
    hand it the Flask app — that is the contract paid plugins rely on to
    register Blueprints scoped to the Claude Code dashboard."""
    calls: list[object] = []

    def _fake_load(app=None):
        calls.append(app)

    monkeypatch.setattr(_ext, "load_plugins", _fake_load)

    app = dashboard_claudecode.create_app()

    assert len(calls) == 1, "load_plugins must be invoked exactly once"
    assert calls[0] is app, "load_plugins must receive the Flask app"


def test_create_app_swallows_plugin_load_errors(monkeypatch, caplog):
    """A raising ``load_plugins`` must not propagate — the standalone
    claudecode dashboard must come up even when a paid plugin is broken."""

    def _boom(app=None):
        raise RuntimeError("plugin install corrupt")

    monkeypatch.setattr(_ext, "load_plugins", _boom)

    with caplog.at_level(logging.WARNING, logger="clawmetry.claudecode"):
        app = dashboard_claudecode.create_app()

    assert app is not None, "create_app must still return a Flask app"
    assert any(
        "extension plugin load failed" in rec.getMessage().lower()
        for rec in caplog.records
    ), "broken plugin path must be logged at WARNING"


def test_create_app_returns_flask_app_with_blueprint(monkeypatch):
    """The plugin hook must not regress the existing app shape: the
    ``claudecode`` Blueprint still has to register on ``/``."""
    monkeypatch.setattr(_ext, "load_plugins", lambda app=None: None)

    app = dashboard_claudecode.create_app()

    # Flask app + blueprint still registered after the wire-up.
    assert hasattr(app, "register_blueprint")
    assert "claudecode" in app.blueprints, (
        "the bp_claudecode blueprint must still be registered after the "
        "load_plugins() call is added"
    )
