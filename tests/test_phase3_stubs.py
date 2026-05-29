"""Tests for the OSS delegating shims after Phase 3 moved Pro libs to clawmetry-pro.

* clawmetry/siem.py         (was Enterprise impl)
* clawmetry/waste_flags.py  (was Pro impl)
* clawmetry/error_signal.py (was Pro impl)

Each shim must:
* Return safe defaults when clawmetry-pro is unavailable.
* Re-export the real impl when clawmetry-pro is importable (lightly
  covered here; thorough tests live in clawmetry-pro).
"""
from __future__ import annotations

import importlib
import sys

import pytest


def _hide_pro(monkeypatch):
    """Force ``from clawmetry_pro.lib import <name>`` to raise ImportError."""
    monkeypatch.setitem(sys.modules, "clawmetry_pro", None)
    monkeypatch.setitem(sys.modules, "clawmetry_pro.lib", None)
    monkeypatch.setitem(sys.modules, "clawmetry_pro.lib.siem", None)
    monkeypatch.setitem(sys.modules, "clawmetry_pro.lib.waste_flags", None)
    monkeypatch.setitem(sys.modules, "clawmetry_pro.lib.error_signal", None)


# ── siem shim ────────────────────────────────────────────────────────────────


def test_siem_forward_event_noop_when_pro_absent(monkeypatch):
    _hide_pro(monkeypatch)
    import clawmetry.siem as _s
    importlib.reload(_s)
    _s.forward_event({"id": "e1", "event_type": "x"})  # no raise


def test_siem_get_default_exporter_returns_none(monkeypatch):
    _hide_pro(monkeypatch)
    import clawmetry.siem as _s
    importlib.reload(_s)
    assert _s.get_default_exporter() is None


def test_siem_format_helpers_return_empty(monkeypatch):
    _hide_pro(monkeypatch)
    import clawmetry.siem as _s
    importlib.reload(_s)
    assert _s.format_cef({}) == ""
    assert _s.format_json({}) == ""
    assert _s.format_syslog_line({}) == ""


def test_siem_class_access_raises_with_hint(monkeypatch):
    _hide_pro(monkeypatch)
    import clawmetry.siem as _s
    importlib.reload(_s)
    with pytest.raises(AttributeError, match="clawmetry-pro"):
        _ = _s.SIEMExporter


# ── waste_flags shim ─────────────────────────────────────────────────────────


def test_waste_flags_compute_returns_empty_list(monkeypatch):
    _hide_pro(monkeypatch)
    import clawmetry.waste_flags as _w
    importlib.reload(_w)
    assert _w.compute_flags({}) == []


def test_waste_flags_signals_returns_empty_dict(monkeypatch):
    _hide_pro(monkeypatch)
    import clawmetry.waste_flags as _w
    importlib.reload(_w)
    assert _w.compute_signals_from_events([]) == {}


def test_runtime_from_session_id_defaults_to_openclaw(monkeypatch):
    _hide_pro(monkeypatch)
    import clawmetry.waste_flags as _w
    importlib.reload(_w)
    # Free-default: assume OpenClaw (the only Free runtime).
    assert _w.runtime_from_session_id("anything") == "openclaw"


def test_severity_from_counts_defaults_to_info(monkeypatch):
    _hide_pro(monkeypatch)
    import clawmetry.waste_flags as _w
    importlib.reload(_w)
    assert _w.severity_from_counts(10, 5) == "info"


def test_event_is_real_error_defaults_to_false(monkeypatch):
    _hide_pro(monkeypatch)
    import clawmetry.waste_flags as _w
    importlib.reload(_w)
    assert _w.event_is_real_error({"is_error": True}) is False


# ── error_signal shim ────────────────────────────────────────────────────────


def test_error_signal_is_benign_defaults_to_false(monkeypatch):
    _hide_pro(monkeypatch)
    import clawmetry.error_signal as _e
    importlib.reload(_e)
    assert _e.is_benign_tool_error("anything") is False


def test_error_signal_extract_text_returns_empty(monkeypatch):
    _hide_pro(monkeypatch)
    import clawmetry.error_signal as _e
    importlib.reload(_e)
    assert _e.extract_tool_result_text({"foo": "bar"}) == ""


def test_error_signal_corrected_passes_through_raw(monkeypatch):
    _hide_pro(monkeypatch)
    import clawmetry.error_signal as _e
    importlib.reload(_e)
    # No correction available: returns the raw value as bool.
    assert _e.corrected_is_error(True, "any text") is True
    assert _e.corrected_is_error(False, "any text") is False
    assert _e.corrected_is_error(None, "any text") is False
