"""Tests for issue #3883 — openclaw: channel-plugin ingress monitor lifecycle phases.

Verifies that _gateway_plugin_health() forwards per-plugin lifecycle phase
fields (phase, admission, claim_identity, adoption_handoff, pruning) introduced
by the shared plugin-SDK monitor so a plugin stuck mid-admission is
distinguishable from a healthy loaded one.

Fingerprint: hgap-5065cc5026 (used to dedupe — keep it in the body).
"""
from __future__ import annotations

import importlib
import sys
import types

import pytest


@pytest.fixture(autouse=True)
def _restore_sys_modules():
    """Restore sys.modules entries clobbered by _make_mock_dashboard/_reload_adapter."""
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


def test_phase_field_forwarded_when_present():
    """Plugin entries with a 'phase' field surface it in gatewayPluginHealth."""
    _make_mock_dashboard({
        "plugins": [
            {"name": "irc", "state": "loaded", "type": "channel", "phase": "admission"},
            {"name": "synology-chat", "state": "loaded", "type": "channel", "phase": "running"},
        ]
    })
    oc = _reload_adapter()
    result = oc._gateway_plugin_health()
    assert result != {}
    entries = {e["name"]: e for e in result["gatewayPluginHealth"]}
    assert entries["irc"]["phase"] == "admission"
    assert entries["synology-chat"]["phase"] == "running"


def test_phase_summary_tallied():
    """gatewayPluginPhaseSummary counts plugins per phase when phases are present."""
    _make_mock_dashboard({
        "plugins": [
            {"name": "irc", "state": "loaded", "phase": "admission"},
            {"name": "google-chat", "state": "loaded", "phase": "admission"},
            {"name": "slack", "state": "loaded", "phase": "running"},
        ]
    })
    oc = _reload_adapter()
    result = oc._gateway_plugin_health()
    ps = result.get("gatewayPluginPhaseSummary", {})
    assert ps.get("admission") == 2
    assert ps.get("running") == 1


def test_phase_summary_absent_when_no_phases():
    """gatewayPluginPhaseSummary is omitted when no plugin carries a phase field."""
    _make_mock_dashboard({
        "plugins": [
            {"name": "telegram", "state": "loaded", "type": "channel"},
        ]
    })
    oc = _reload_adapter()
    result = oc._gateway_plugin_health()
    assert "gatewayPluginPhaseSummary" not in result


def test_admission_detail_flag_forwarded():
    """Per-step 'admission' detail flag is forwarded when present."""
    _make_mock_dashboard({
        "plugins": [
            {"name": "irc", "state": "loaded", "phase": "admission", "admission": "pending"},
        ]
    })
    oc = _reload_adapter()
    result = oc._gateway_plugin_health()
    entry = result["gatewayPluginHealth"][0]
    assert entry.get("admission") == "pending"


def test_claim_identity_detail_flag_forwarded():
    """Per-step 'claim_identity' detail flag is forwarded when present."""
    _make_mock_dashboard({
        "plugins": [
            {"name": "synology-chat", "state": "errored", "phase": "claim-identity",
             "claim_identity": "failed"},
        ]
    })
    oc = _reload_adapter()
    result = oc._gateway_plugin_health()
    entry = result["gatewayPluginHealth"][0]
    assert entry.get("claim_identity") == "failed"


def test_adoption_handoff_detail_flag_forwarded():
    """Per-step 'adoption_handoff' detail flag is forwarded when present."""
    _make_mock_dashboard({
        "plugins": [
            {"name": "google-chat", "state": "loaded", "phase": "adoption-handoff",
             "adoption_handoff": "complete"},
        ]
    })
    oc = _reload_adapter()
    result = oc._gateway_plugin_health()
    entry = result["gatewayPluginHealth"][0]
    assert entry.get("adoption_handoff") == "complete"


def test_pruning_flag_forwarded():
    """Per-step 'pruning' flag is forwarded when present."""
    _make_mock_dashboard({
        "plugins": [
            {"name": "legacy-sms", "state": "disabled", "pruning": True},
        ]
    })
    oc = _reload_adapter()
    result = oc._gateway_plugin_health()
    entry = result["gatewayPluginHealth"][0]
    assert entry.get("pruning") is True


def test_absent_lifecycle_fields_not_included():
    """Lifecycle fields absent in the gateway payload are not added to entries."""
    _make_mock_dashboard({
        "plugins": [
            {"name": "telegram", "state": "loaded", "type": "channel"},
        ]
    })
    oc = _reload_adapter()
    result = oc._gateway_plugin_health()
    entry = result["gatewayPluginHealth"][0]
    for key in ("phase", "admission", "claim_identity", "adoption_handoff", "pruning"):
        assert key not in entry, f"Unexpected key '{key}' in entry: {entry}"


def test_existing_state_summary_unaffected():
    """Adding lifecycle phase support does not break the existing state tally."""
    _make_mock_dashboard({
        "plugins": [
            {"name": "irc", "state": "loaded", "phase": "admission"},
            {"name": "slack", "state": "errored", "phase": "claim-identity",
             "claim_identity": "failed"},
        ]
    })
    oc = _reload_adapter()
    result = oc._gateway_plugin_health()
    assert result["gatewayPluginHealthSummary"] == {"loaded": 1, "errored": 1}
