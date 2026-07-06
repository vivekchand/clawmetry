"""Tests for issue #3551 — openclaw: gateway host/system status fields.

Verifies that _gateway_host_status() extracts host/system fields from the
gateway.status RPC response and surfaces them on DetectResult.meta.

Fingerprint: hgap-dd7ff7ab07 (used to dedupe — keep it in the body).
"""
from __future__ import annotations

import importlib
import sys
import types


def _make_mock_dashboard(rpc_return):
    """Return a minimal mock dashboard module with _gw_ws_rpc wired up."""
    mod = types.ModuleType("dashboard")
    mod._gw_ws_rpc = lambda method, params=None: rpc_return
    sys.modules["dashboard"] = mod
    return mod


def _reload_adapter():
    import clawmetry.adapters.openclaw as oc_mod
    importlib.reload(oc_mod)
    return oc_mod


def test_all_host_fields_present():
    """All eight host/system fields are extracted when the RPC returns them."""
    _make_mock_dashboard({
        "plugins": [],
        "hostName": "gateway-host.local",
        "networkAddress": "192.168.1.50",
        "os": "linux",
        "runtime": "node/20.11.0",
        "uptime": 7200,
        "cpu": 8.5,
        "memory": {"total": 16777216000, "used": 4294967296},
        "disk": {"total": 107374182400, "used": 21474836480},
    })
    oc = _reload_adapter()
    result = oc._gateway_host_status()
    assert result["gatewayHostName"] == "gateway-host.local"
    assert result["gatewayNetworkAddress"] == "192.168.1.50"
    assert result["gatewayHostOS"] == "linux"
    assert result["gatewayHostRuntime"] == "node/20.11.0"
    assert result["gatewayHostUptime"] == 7200
    assert result["gatewayHostCPU"] == 8.5
    assert result["gatewayHostMemory"] == {"total": 16777216000, "used": 4294967296}
    assert result["gatewayHostDisk"] == {"total": 107374182400, "used": 21474836480}


def test_partial_fields_only_present_keys_returned():
    """Only fields that are non-None/non-empty are included in the result."""
    _make_mock_dashboard({
        "hostname": "partial-host",
        "os": "darwin",
    })
    oc = _reload_adapter()
    result = oc._gateway_host_status()
    assert result.get("gatewayHostName") == "partial-host"
    assert result.get("gatewayHostOS") == "darwin"
    assert "gatewayNetworkAddress" not in result
    assert "gatewayHostRuntime" not in result
    assert "gatewayHostUptime" not in result
    assert "gatewayHostCPU" not in result
    assert "gatewayHostMemory" not in result
    assert "gatewayHostDisk" not in result


def test_rpc_returns_none_gives_empty_dict():
    """When the gateway RPC returns None (gateway down), return {}."""
    _make_mock_dashboard(None)
    oc = _reload_adapter()
    result = oc._gateway_host_status()
    assert result == {}


def test_no_host_fields_in_response_gives_empty_dict():
    """A gateway.status response with only plugins and no host fields → {}."""
    _make_mock_dashboard({
        "plugins": [
            {"name": "telegram", "state": "loaded", "type": "channel"},
        ]
    })
    oc = _reload_adapter()
    result = oc._gateway_host_status()
    assert result == {}


def test_fallback_key_variants_resolved():
    """Fallback key names (host_name, network_address, node_version) are tried."""
    _make_mock_dashboard({
        "host_name": "fallback-host",
        "network_address": "10.0.0.1",
        "node_version": "v18.20.0",
        "uptime_seconds": 3600,
        "cpu_usage": 15.2,
        "memory_usage": {"total": 8589934592, "used": 2147483648},
        "disk_usage": {"total": 53687091200, "used": 10737418240},
    })
    oc = _reload_adapter()
    result = oc._gateway_host_status()
    assert result.get("gatewayHostName") == "fallback-host"
    assert result.get("gatewayNetworkAddress") == "10.0.0.1"
    assert result.get("gatewayHostRuntime") == "v18.20.0"
    assert result.get("gatewayHostUptime") == 3600
    assert result.get("gatewayHostCPU") == 15.2
    assert result.get("gatewayHostMemory") == {"total": 8589934592, "used": 2147483648}
    assert result.get("gatewayHostDisk") == {"total": 53687091200, "used": 10737418240}
