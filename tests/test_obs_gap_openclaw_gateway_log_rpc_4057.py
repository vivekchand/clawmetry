"""Tests for #4057 — openclaw: RPC-based log fallback for remote/non-local gateways.

Verifies that _gateway_log_events() falls back to _gateway_log_events_rpc() when
no local log files are found, and that _gateway_log_events_rpc() correctly parses
the gateway.logs RPC response into normalised event dicts.

Fingerprint: hgap-5034733724 (used to dedupe — keep it in the body).
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


# ---------------------------------------------------------------------------
# _gateway_log_events_rpc tests
# ---------------------------------------------------------------------------

def test_rpc_events_key_returned():
    """gateway.logs response with 'events' key is parsed correctly."""
    _make_mock_dashboard({
        "events": [
            {"time": 1000, "level": "info", "msg": "started", "subsystem": "core"},
            {"time": 1001, "level": "warn", "msg": "slow",    "subsystem": "llm"},
        ]
    })
    oc = _reload_adapter()
    result = oc._gateway_log_events_rpc()
    assert len(result) == 2
    assert result[0]["msg"] == "started"
    assert result[0]["ts"] == 1000
    assert result[1]["subsystem"] == "llm"


def test_rpc_alternate_payload_keys():
    """'lines', 'entries', and 'logs' are all accepted payload keys."""
    for key in ("lines", "entries", "logs"):
        _make_mock_dashboard({
            key: [{"level": "info", "msg": f"via {key}"}]
        })
        oc = _reload_adapter()
        result = oc._gateway_log_events_rpc()
        assert len(result) == 1, f"failed for payload key '{key}'"
        assert result[0]["msg"] == f"via {key}"


def test_rpc_none_returns_empty():
    """When gateway RPC returns None (gateway down), return []."""
    _make_mock_dashboard(None)
    oc = _reload_adapter()
    assert oc._gateway_log_events_rpc() == []


def test_rpc_empty_events_list_returns_empty():
    """Empty events list in payload → []."""
    _make_mock_dashboard({"events": []})
    oc = _reload_adapter()
    assert oc._gateway_log_events_rpc() == []


def test_rpc_message_field_normalised_to_msg():
    """'message' key in RPC response is normalised to 'msg'."""
    _make_mock_dashboard({
        "events": [{"ts": 42, "level": "info", "message": "normalised"}]
    })
    oc = _reload_adapter()
    result = oc._gateway_log_events_rpc()
    assert len(result) == 1
    assert result[0]["msg"] == "normalised"
    assert "message" not in result[0]


def test_rpc_count_limits_results():
    """count parameter caps the number of events returned."""
    _make_mock_dashboard({
        "events": [{"level": "info", "msg": f"e{i}"} for i in range(20)]
    })
    oc = _reload_adapter()
    result = oc._gateway_log_events_rpc(count=5)
    assert len(result) == 5


def test_rpc_no_ws_rpc_attr_returns_empty():
    """When dashboard has no _gw_ws_rpc (not yet connected), return []."""
    mod = types.ModuleType("dashboard")
    sys.modules["dashboard"] = mod
    oc = _reload_adapter()
    assert oc._gateway_log_events_rpc() == []


# ---------------------------------------------------------------------------
# _gateway_log_events fallback integration tests
# ---------------------------------------------------------------------------

def test_disk_empty_falls_back_to_rpc(monkeypatch):
    """When _gateway_log_files() returns [], _gateway_log_events uses RPC."""
    _make_mock_dashboard({
        "events": [{"level": "info", "msg": "from rpc", "subsystem": "net"}]
    })
    oc = _reload_adapter()
    monkeypatch.setattr("clawmetry.adapters.openclaw._gateway_log_files", lambda: [])
    result = oc._gateway_log_events()
    assert len(result) == 1
    assert result[0]["msg"] == "from rpc"


def test_disk_wins_over_rpc(monkeypatch, tmp_path):
    """When local disk has events, RPC is not needed and disk data is returned."""
    import json as _json
    log = tmp_path / "openclaw-2026-07-26.log"
    log.write_text(_json.dumps({"level": "info", "msg": "from disk"}) + "\n", encoding="utf-8")

    _make_mock_dashboard({
        "events": [{"level": "warn", "msg": "from rpc"}]
    })
    oc = _reload_adapter()
    monkeypatch.setattr("clawmetry.adapters.openclaw._gateway_log_files", lambda: [str(log)])
    result = oc._gateway_log_events()
    assert len(result) == 1
    assert result[0]["msg"] == "from disk"


def test_oserror_falls_back_to_rpc(monkeypatch, tmp_path):
    """OSError opening the log file triggers RPC fallback."""
    _make_mock_dashboard({
        "events": [{"level": "error", "msg": "rpc fallback after oserror"}]
    })
    oc = _reload_adapter()
    monkeypatch.setattr(
        "clawmetry.adapters.openclaw._gateway_log_files",
        lambda: ["/nonexistent/path/openclaw-2026-07-26.log"],
    )
    result = oc._gateway_log_events()
    assert len(result) == 1
    assert result[0]["msg"] == "rpc fallback after oserror"
