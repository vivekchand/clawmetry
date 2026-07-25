"""Tests for issue #4023 — openclaw: external supervisor mode env-var fallback.

Verifies that _gateway_supervisor_mode_env() surfaces OPENCLAW_SUPERVISOR_MODE
and OPENCLAW_SUPERVISOR_MODE_VERSION from the local environment so the
supervisor context appears even when the gateway is down (RPC unavailable).

Fingerprint: hgap-fada9f0f13 (used to dedupe — keep it in the body).
"""
from __future__ import annotations

import importlib
import os
import sys
import types

import pytest


@pytest.fixture(autouse=True)
def _restore_env_and_modules(monkeypatch):
    saved_dashboard = sys.modules.get("dashboard")
    saved_adapter = sys.modules.get("clawmetry.adapters.openclaw")
    monkeypatch.delenv("OPENCLAW_SUPERVISOR_MODE", raising=False)
    monkeypatch.delenv("OPENCLAW_SUPERVISOR_MODE_VERSION", raising=False)
    yield
    if saved_dashboard is None:
        sys.modules.pop("dashboard", None)
    else:
        sys.modules["dashboard"] = saved_dashboard
    if saved_adapter is None:
        sys.modules.pop("clawmetry.adapters.openclaw", None)
    else:
        sys.modules["clawmetry.adapters.openclaw"] = saved_adapter


def _stub_dashboard():
    mod = types.ModuleType("dashboard")
    sys.modules["dashboard"] = mod
    return mod


def _reload_adapter():
    _stub_dashboard()
    import clawmetry.adapters.openclaw as oc_mod
    importlib.reload(oc_mod)
    return oc_mod


def test_supervisor_mode_env_external(monkeypatch):
    """OPENCLAW_SUPERVISOR_MODE=external is surfaced as gatewaySupervisorMode."""
    monkeypatch.setenv("OPENCLAW_SUPERVISOR_MODE", "external")
    oc = _reload_adapter()
    result = oc._gateway_supervisor_mode_env()
    assert result["gatewaySupervisorMode"] == "external"
    assert "gatewaySupervisorModeVersion" not in result


def test_supervisor_mode_env_with_version(monkeypatch):
    """Both mode and version env vars are surfaced when set."""
    monkeypatch.setenv("OPENCLAW_SUPERVISOR_MODE", "external")
    monkeypatch.setenv("OPENCLAW_SUPERVISOR_MODE_VERSION", "2")
    oc = _reload_adapter()
    result = oc._gateway_supervisor_mode_env()
    assert result["gatewaySupervisorMode"] == "external"
    assert result["gatewaySupervisorModeVersion"] == "2"


def test_supervisor_mode_env_absent():
    """When env var is not set, helper returns empty dict."""
    oc = _reload_adapter()
    result = oc._gateway_supervisor_mode_env()
    assert result == {}


def test_supervisor_mode_env_empty_string(monkeypatch):
    """Empty string is treated as absent (falsy) and returns empty dict."""
    monkeypatch.setenv("OPENCLAW_SUPERVISOR_MODE", "")
    oc = _reload_adapter()
    result = oc._gateway_supervisor_mode_env()
    assert result == {}
