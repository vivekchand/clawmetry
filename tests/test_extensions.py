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
