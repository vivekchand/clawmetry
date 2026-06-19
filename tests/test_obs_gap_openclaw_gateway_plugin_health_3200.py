"""Tests for issue #3200 — openclaw: gateway plugin health.

Verifies that _gateway_plugin_health() extracts per-plugin state from the
gateway.status RPC response and surfaces it on DetectResult.meta.

Fingerprint: hgap-267c342338 (used to dedupe — keep it in the body).
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


def test_loaded_errored_disabled_summary():
    """Helper builds summary counts per state."""
    _make_mock_dashboard({
        "plugins": [
            {"name": "telegram", "state": "loaded", "type": "channel"},
            {"name": "slack", "state": "errored", "type": "channel"},
            {"name": "openai", "state": "loaded", "type": "provider"},
            {"name": "legacy-sms", "state": "disabled", "type": "channel"},
        ]
    })
    oc = _reload_adapter()
    result = oc._gateway_plugin_health()
    assert "gatewayPluginHealth" in result
    assert "gatewayPluginHealthSummary" in result
    summary = result["gatewayPluginHealthSummary"]
    assert summary.get("loaded") == 2
    assert summary.get("errored") == 1
    assert summary.get("disabled") == 1


def test_rpc_returns_none_gives_empty_dict():
    """When the gateway RPC returns None (gateway down), return {}."""
    _make_mock_dashboard(None)
    oc = _reload_adapter()
    result = oc._gateway_plugin_health()
    assert result == {}


def test_empty_plugins_list_gives_empty_dict():
    """An empty plugins list means no data to surface."""
    _make_mock_dashboard({"plugins": []})
    oc = _reload_adapter()
    result = oc._gateway_plugin_health()
    assert result == {}


def test_plugins_without_type_field_accepted():
    """Entries without a type field are included; type key omitted."""
    _make_mock_dashboard({
        "plugins": [
            {"name": "whatsapp", "state": "loaded"},
        ]
    })
    oc = _reload_adapter()
    result = oc._gateway_plugin_health()
    assert result["gatewayPluginHealthSummary"] == {"loaded": 1}
    entry = result["gatewayPluginHealth"][0]
    assert entry["name"] == "whatsapp"
    assert "type" not in entry


def test_entries_with_missing_name_or_state_skipped():
    """Malformed entries (no name or no state) are silently dropped."""
    _make_mock_dashboard({
        "plugins": [
            {"name": "good-plugin", "state": "loaded"},
            {"state": "errored"},          # missing name
            {"name": "no-state-plugin"},   # missing state
            {},                            # empty
        ]
    })
    oc = _reload_adapter()
    result = oc._gateway_plugin_health()
    assert len(result["gatewayPluginHealth"]) == 1
    assert result["gatewayPluginHealth"][0]["name"] == "good-plugin"
