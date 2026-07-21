"""Tests for issue #3884 — openclaw: who's-online presence roster.

Verifies that _gateway_presence_roster() extracts connected-user entries from
the gateway.status RPC response and surfaces them on DetectResult.meta.

Fingerprint: hgap-5d37b03e2e (used to dedupe — keep it in the body).
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
    """Return a minimal mock dashboard module with _gw_ws_rpc wired up."""
    mod = types.ModuleType("dashboard")
    mod._gw_ws_rpc = lambda method, params=None: rpc_return
    sys.modules["dashboard"] = mod
    return mod


def _reload_adapter():
    import clawmetry.adapters.openclaw as oc_mod
    importlib.reload(oc_mod)
    return oc_mod


def test_full_roster_returned():
    """All user fields are extracted when the RPC returns a connectedUsers list."""
    _make_mock_dashboard({
        "connectedUsers": [
            {
                "email": "alice@example.com",
                "displayName": "Alice",
                "avatar": "https://example.com/alice.png",
            },
            {
                "email": "bob@example.com",
                "displayName": "Bob",
                "avatarUrl": "https://example.com/bob.png",
            },
        ],
    })
    oc = _reload_adapter()
    result = oc._gateway_presence_roster()
    assert result["gatewayPresenceCount"] == 2
    roster = result["gatewayPresenceRoster"]
    assert len(roster) == 2
    assert roster[0]["email"] == "alice@example.com"
    assert roster[0]["displayName"] == "Alice"
    assert roster[0]["avatar"] == "https://example.com/alice.png"
    assert roster[1]["email"] == "bob@example.com"
    assert roster[1]["displayName"] == "Bob"
    assert roster[1]["avatar"] == "https://example.com/bob.png"


def test_fallback_key_variants_resolved():
    """Alternate key spellings (onlineUsers, email_address, display_name) are tried."""
    _make_mock_dashboard({
        "onlineUsers": [
            {
                "email_address": "carol@example.com",
                "display_name": "Carol",
                "photo_url": "https://example.com/carol.png",
            },
        ],
    })
    oc = _reload_adapter()
    result = oc._gateway_presence_roster()
    assert result["gatewayPresenceCount"] == 1
    user = result["gatewayPresenceRoster"][0]
    assert user["email"] == "carol@example.com"
    assert user["displayName"] == "Carol"
    assert user["avatar"] == "https://example.com/carol.png"


def test_entry_without_email_skipped():
    """User entries missing an email are silently dropped; valid entries kept."""
    _make_mock_dashboard({
        "connectedUsers": [
            {"displayName": "Ghost"},
            {"email": "real@example.com", "displayName": "Real"},
        ],
    })
    oc = _reload_adapter()
    result = oc._gateway_presence_roster()
    assert result["gatewayPresenceCount"] == 1
    assert result["gatewayPresenceRoster"][0]["email"] == "real@example.com"


def test_empty_user_list_gives_empty_dict():
    """A gateway.status response with an empty connectedUsers list returns {}."""
    _make_mock_dashboard({"connectedUsers": []})
    oc = _reload_adapter()
    assert oc._gateway_presence_roster() == {}


def test_no_presence_key_gives_empty_dict():
    """A gateway.status response with only plugins and no user roster returns {}."""
    _make_mock_dashboard({
        "plugins": [{"name": "telegram", "state": "loaded"}],
        "hostName": "mybox",
    })
    oc = _reload_adapter()
    assert oc._gateway_presence_roster() == {}


def test_rpc_returns_none_gives_empty_dict():
    """When the RPC returns None (gateway down), return {}."""
    _make_mock_dashboard(None)
    oc = _reload_adapter()
    assert oc._gateway_presence_roster() == {}


def test_optional_fields_absent_when_not_in_entry():
    """displayName and avatar are omitted from the user dict when not provided."""
    _make_mock_dashboard({
        "presence": [{"email": "minimal@example.com"}],
    })
    oc = _reload_adapter()
    result = oc._gateway_presence_roster()
    user = result["gatewayPresenceRoster"][0]
    assert user["email"] == "minimal@example.com"
    assert "displayName" not in user
    assert "avatar" not in user
