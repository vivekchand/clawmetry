"""Tests for ``clawmetry/proxy.py`` plugin host wiring.

The enforcement proxy runs as a separate process (``python -m clawmetry.proxy``)
and was the only ClawMetry process besides the sync daemon where paid plugins
were silently skipped. ``create_proxy_app`` now calls
:func:`clawmetry.extensions.load_plugins(app)` right after the Flask app is
constructed so a clawmetry-pro plugin can register policy / routing blueprints
on the proxy. Errors must never take the proxy down — the proxy is the LLM
egress chokepoint.

These tests are hermetic — they monkey-patch ``load_plugins`` so no real entry
points are touched, and they avoid spawning a server.
"""

from __future__ import annotations

import pytest


@pytest.fixture
def reset_extensions_state():
    """Reset the once-guard so each test exercises ``load_plugins`` fresh."""
    import clawmetry.extensions as ext

    saved = ext._loaded
    ext._loaded = False
    yield ext
    ext._loaded = saved


def _build_app(monkeypatch, fake_load):
    """Patch ``load_plugins`` on the extensions module and build the proxy app.

    The proxy imports the symbol at call time inside ``create_proxy_app`` —
    we patch the source module so the late import resolves to ``fake_load``.
    """
    import clawmetry.extensions as ext

    monkeypatch.setattr(ext, "load_plugins", fake_load)

    from clawmetry.proxy import create_proxy_app, ProxyConfig

    return create_proxy_app(ProxyConfig())


def test_create_proxy_app_calls_load_plugins_once(monkeypatch, reset_extensions_state):
    """The proxy invokes ``load_plugins(app)`` exactly once at construction
    so paid plugins can register Blueprints on the enforcement Flask app."""
    calls = []

    def fake_load(app=None):
        calls.append(app)

    app = _build_app(monkeypatch, fake_load)

    assert len(calls) == 1, "load_plugins must be called exactly once"
    assert calls[0] is app, "the proxy Flask app must be handed to the plugin"


def test_create_proxy_app_swallows_load_plugins_errors(
    monkeypatch, reset_extensions_state
):
    """A broken plugin must never take the proxy down — the proxy is the LLM
    egress chokepoint, so we log and continue rather than propagate."""

    def fake_load(app=None):
        raise RuntimeError("simulated plugin crash")

    # Must not raise.
    app = _build_app(monkeypatch, fake_load)

    # Sanity check: app is still a usable Flask app.
    from flask import Flask

    assert isinstance(app, Flask)


def test_create_proxy_app_logs_warning_on_plugin_error(
    monkeypatch, reset_extensions_state, caplog
):
    """When a plugin raises, the proxy logs a warning so the operator can see
    the failure without the process dying."""
    import logging

    def fake_load(app=None):
        raise RuntimeError("simulated plugin crash")

    with caplog.at_level(logging.WARNING, logger="clawmetry.proxy"):
        _build_app(monkeypatch, fake_load)

    assert any(
        "load_plugins" in rec.message and "simulated plugin crash" in rec.message
        for rec in caplog.records
    ), "expected a warning mentioning the failed load_plugins call"


def test_create_proxy_app_does_not_call_dashboard_load(
    monkeypatch, reset_extensions_state
):
    """The proxy must call its own ``load_plugins(app)`` — not rely on the
    dashboard process having loaded plugins, because the proxy runs in a
    separate process under ``python -m clawmetry.proxy``."""
    calls = []

    def fake_load(app=None):
        calls.append(("called", app is not None))

    _build_app(monkeypatch, fake_load)

    assert calls == [("called", True)]
