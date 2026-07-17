"""Tests for issue #3783 — openclaw: external supervisor mode not surfaced.

Verifies that _gateway_host_status() extracts supervisorMode /
supervisorModeVersion from the gateway.status RPC payload and surfaces
them on DetectResult.meta.

Fingerprint: hgap-21ddd6b36b (used to dedupe — keep it in the body).
"""
from __future__ import annotations

import importlib
import sys
import types

import pytest


@pytest.fixture(autouse=True)
def _restore_sys_modules():
    saved_dashboard = sys.modules.get("dashboard")
    saved_adapter = sys.modules.get("clawmetry.adapters.openclaw")
    yield
    if saved_dashboard is None:
        sys.modules.pop("dashboard", None)
    else:
        sys.modules["dashboard"] = saved_dashboard
    if saved_adapter is None:
        sys.modules.pop("clawmetry.adapters.openclaw", None)
    else:
        sys.modules["clawmetry.adapters.openclaw"] = saved_adapter


def _make_mock_dashboard(rpc_return):
    mod = types.ModuleType("dashboard")
    mod._gw_ws_rpc = lambda method, params=None: rpc_return
    sys.modules["dashboard"] = mod
    return mod


def _reload_adapter():
    import clawmetry.adapters.openclaw as oc_mod
    importlib.reload(oc_mod)
    return oc_mod


def test_supervisor_mode_external_extracted():
    """supervisorMode='external' is surfaced as gatewaySupervisorMode."""
    _make_mock_dashboard({
        "hostName": "gw.local",
        "supervisorMode": "external",
        "supervisorModeVersion": "1",
    })
    oc = _reload_adapter()
    result = oc._gateway_host_status()
    assert result["gatewaySupervisorMode"] == "external"
    assert result["gatewaySupervisorModeVersion"] == "1"


def test_supervisor_mode_snake_case_fallback():
    """supervisor_mode / supervisor_mode_version keys are also accepted."""
    _make_mock_dashboard({
        "hostname": "gw.local",
        "supervisor_mode": "external",
        "supervisor_mode_version": "2",
    })
    oc = _reload_adapter()
    result = oc._gateway_host_status()
    assert result["gatewaySupervisorMode"] == "external"
    assert result["gatewaySupervisorModeVersion"] == "2"


def test_absent_supervisor_fields_not_in_result():
    """When gateway.status carries no supervisor fields, keys are absent."""
    _make_mock_dashboard({
        "hostName": "gw.local",
        "os": "linux",
    })
    oc = _reload_adapter()
    result = oc._gateway_host_status()
    assert "gatewaySupervisorMode" not in result
    assert "gatewaySupervisorModeVersion" not in result


def test_supervisor_mode_without_version():
    """supervisorMode present without a version → only mode key emitted."""
    _make_mock_dashboard({
        "supervisorMode": "external",
    })
    oc = _reload_adapter()
    result = oc._gateway_host_status()
    assert result["gatewaySupervisorMode"] == "external"
    assert "gatewaySupervisorModeVersion" not in result
