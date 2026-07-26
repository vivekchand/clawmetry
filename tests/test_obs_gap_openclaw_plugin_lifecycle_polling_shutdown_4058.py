"""Tests for issue #4058 — openclaw: channel plugin lifecycle 'polling' and 'shutdown'
detail flags not forwarded by _gateway_plugin_health().

Verifies that the per-step detail-flag loop covers all six SDK lifecycle steps,
including 'polling' and 'shutdown' which were previously silently dropped.

Fingerprint: hgap-57d9fbd884 (used to dedupe — keep it in the body).
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


def test_polling_detail_flag_forwarded():
    """Per-step 'polling' detail flag is forwarded when present."""
    _make_mock_dashboard({
        "plugins": [
            {"name": "irc", "state": "loaded", "phase": "polling", "polling": "active"},
        ]
    })
    oc = _reload_adapter()
    result = oc._gateway_plugin_health()
    entry = result["gatewayPluginHealth"][0]
    assert entry.get("polling") == "active"


def test_shutdown_detail_flag_forwarded():
    """Per-step 'shutdown' detail flag is forwarded when present."""
    _make_mock_dashboard({
        "plugins": [
            {"name": "google-chat", "state": "loaded", "phase": "shutdown", "shutdown": "graceful"},
        ]
    })
    oc = _reload_adapter()
    result = oc._gateway_plugin_health()
    entry = result["gatewayPluginHealth"][0]
    assert entry.get("shutdown") == "graceful"


def test_polling_and_shutdown_in_phase_summary():
    """Phase summary includes 'polling' and 'shutdown' counts when present."""
    _make_mock_dashboard({
        "plugins": [
            {"name": "irc", "state": "loaded", "phase": "polling", "polling": "active"},
            {"name": "synology-chat", "state": "loaded", "phase": "polling"},
            {"name": "google-chat", "state": "loaded", "phase": "shutdown", "shutdown": "graceful"},
        ]
    })
    oc = _reload_adapter()
    result = oc._gateway_plugin_health()
    ps = result.get("gatewayPluginPhaseSummary", {})
    assert ps.get("polling") == 2
    assert ps.get("shutdown") == 1


def test_absent_polling_shutdown_flags_not_injected():
    """Absent polling/shutdown fields are not added to plugin entries."""
    _make_mock_dashboard({
        "plugins": [
            {"name": "telegram", "state": "loaded", "type": "channel"},
        ]
    })
    oc = _reload_adapter()
    result = oc._gateway_plugin_health()
    entry = result["gatewayPluginHealth"][0]
    assert "polling" not in entry
    assert "shutdown" not in entry


def test_all_six_detail_flags_forwarded_together():
    """All six lifecycle detail flags are forwarded when a plugin carries all of them."""
    _make_mock_dashboard({
        "plugins": [
            {
                "name": "irc", "state": "loaded", "phase": "polling",
                "admission": "ok", "claim_identity": "ok",
                "adoption_handoff": "ok", "pruning": False,
                "polling": "active", "shutdown": None,
            },
        ]
    })
    oc = _reload_adapter()
    result = oc._gateway_plugin_health()
    entry = result["gatewayPluginHealth"][0]
    assert entry.get("admission") == "ok"
    assert entry.get("claim_identity") == "ok"
    assert entry.get("adoption_handoff") == "ok"
    assert entry.get("pruning") is False
    assert entry.get("polling") == "active"
    # shutdown is None — entry.get(detail_key) is not None check excludes it
    assert "shutdown" not in entry
