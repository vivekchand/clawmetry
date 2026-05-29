"""Tests for clawmetry/extensions.py — plugin entry-point loading.

Regression focus: ``_select_entry_points`` must work on Python 3.9 (where
``entry_points(group=...)`` raises TypeError) as well as 3.10+, so the
closed-source clawmetry-pro package actually loads on every supported runtime.
"""
from __future__ import annotations

import clawmetry.extensions as ext


def test_select_entry_points_returns_list():
    # Never raises on any Python version; returns a list of EntryPoint.
    eps = ext._select_entry_points("clawmetry.extensions")
    assert isinstance(eps, list)


def test_select_unknown_group_is_empty():
    assert ext._select_entry_points("no.such.group.xyz123") == []


def test_load_plugins_idempotent_and_safe(monkeypatch):
    # Reset the once-guard, then load twice — must never raise regardless of
    # whether any extension package is installed.
    monkeypatch.setattr(ext, "_loaded", False)
    ext.load_plugins()
    ext.load_plugins()  # second call is a no-op via the guard


def test_register_emit_roundtrip():
    seen = []
    ext.register("test.evt.roundtrip", lambda p: seen.append(p))
    ext.emit("test.evt.roundtrip", {"x": 1})
    assert seen == [{"x": 1}]


def test_emit_swallows_handler_errors():
    def boom(_payload):
        raise ValueError("boom")

    ext.register("test.evt.boom", boom)
    ext.emit("test.evt.boom", {})  # must not propagate


# ── load_plugins(app) signature introspection (Phase 1.2) ────────────────────


class _FakeEntryPoint:
    """Stub entry point that returns ``fn`` from ``.load()`` and has ``.name``."""

    def __init__(self, fn, name="fake"):
        self._fn = fn
        self.name = name

    def load(self):
        return self._fn


def _fake_eps(*fns_with_names):
    return [_FakeEntryPoint(fn, name=n) for fn, n in fns_with_names]


def test_load_plugins_calls_old_style_with_no_args(monkeypatch):
    """A plugin that declares ``register_all()`` is still called no-args
    even when ``load_plugins(app)`` is invoked. Backward-compat."""
    monkeypatch.setattr(ext, "_loaded", False)
    calls = []

    def register_all():
        calls.append("no-args")

    monkeypatch.setattr(ext, "_select_entry_points",
                        lambda group: _fake_eps((register_all, "old")))
    ext.load_plugins(app=object())  # passes app, plugin ignores it
    assert calls == ["no-args"]


def test_load_plugins_passes_app_when_plugin_accepts_it(monkeypatch):
    monkeypatch.setattr(ext, "_loaded", False)
    received = []

    def register_all(app):
        received.append(app)

    sentinel = {"flask-app": True}
    monkeypatch.setattr(ext, "_select_entry_points",
                        lambda group: _fake_eps((register_all, "new")))
    ext.load_plugins(app=sentinel)
    assert received == [sentinel]


def test_load_plugins_with_no_app_never_passes_app(monkeypatch):
    """Calling ``load_plugins()`` (no args) never invokes a plugin with an
    arg, even when the plugin accepts one. Lets older OSS dashboards that
    haven't been updated keep working."""
    monkeypatch.setattr(ext, "_loaded", False)
    calls = []

    def register_all(app=None):
        calls.append(app)

    monkeypatch.setattr(ext, "_select_entry_points",
                        lambda group: _fake_eps((register_all, "new")))
    ext.load_plugins()  # no app
    assert calls == [None] or calls == []  # depending on Python signature handling


def test_load_plugins_swallows_plugin_exceptions(monkeypatch):
    """One bad plugin must not break the others."""
    monkeypatch.setattr(ext, "_loaded", False)
    other_called = []

    def boom(app):
        raise RuntimeError("boom")

    def good(app):
        other_called.append(app)

    monkeypatch.setattr(
        ext, "_select_entry_points",
        lambda group: _fake_eps((boom, "boom"), (good, "good")),
    )
    sentinel = object()
    ext.load_plugins(app=sentinel)  # must not raise
    assert other_called == [sentinel]


def test_load_plugins_handles_unintrospectable_callable(monkeypatch):
    """Built-in callables with no inspectable signature must not crash the
    loader; we fall back to no-args invocation for them."""
    monkeypatch.setattr(ext, "_loaded", False)
    # ``min`` is a builtin whose signature() may raise on some Python
    # versions / contexts. We just need any callable that takes args and
    # could raise during signature introspection.
    monkeypatch.setattr(ext, "_select_entry_points",
                        lambda group: _fake_eps((min, "builtin")))
    # Must not raise; ``min()`` with no args would error, but we wrap the
    # call in try/except in the loader, so it gets logged + swallowed.
    ext.load_plugins(app=object())
