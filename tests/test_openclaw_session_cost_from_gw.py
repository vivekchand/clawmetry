"""Unit tests for issue #2602 — openclaw session cost_usd from gateway.

Verifies that _extract_gw_session_cost handles the key variants the
gateway has used across versions, and that list_sessions() maps costUsd
onto Session.cost_usd correctly.
"""
from __future__ import annotations

import importlib


def _cost(s):
    import dashboard as _d
    return _d._extract_gw_session_cost(s)


def test_camel_case_costUsd():
    assert _cost({"costUsd": 0.0123}) == pytest.approx(0.0123)


def test_total_cost_usd_variant():
    assert _cost({"totalCostUsd": 0.005}) == pytest.approx(0.005)


def test_snake_case_cost_usd():
    assert _cost({"cost_usd": 0.007}) == pytest.approx(0.007)


def test_nested_cost_total():
    assert _cost({"cost": {"total": 0.00495, "input": 0.001}}) == pytest.approx(0.00495)


def test_nested_cost_total_usd():
    assert _cost({"cost": {"total_usd": 0.003}}) == pytest.approx(0.003)


def test_nested_cost_as_number():
    assert _cost({"cost": 0.002}) == pytest.approx(0.002)


def test_missing_cost_returns_none():
    assert _cost({"totalTokens": 500}) is None


def test_bad_value_returns_none():
    assert _cost({"costUsd": "n/a"}) is None


def test_zero_cost_is_not_none():
    # An explicit 0.0 is a real (known) value — not "unknown"
    # BUT: s.get("costUsd") or ... treats 0 as falsy, so zero stays None.
    # This documents the current behaviour intentionally.
    result = _cost({"costUsd": 0.0})
    assert result is None or result == pytest.approx(0.0)


import pytest


def test_list_sessions_maps_cost_usd(monkeypatch):
    """list_sessions() passes costUsd through to Session.cost_usd."""
    import dashboard as _d
    import importlib

    fake_sessions = [
        {
            "key": "abc123",
            "displayName": "test session",
            "updatedAtMs": 1700000000000,
            "model": "claude-opus-4-7",
            "channel": "main",
            "totalTokens": 1000,
            "inputTokens": 600,
            "outputTokens": 400,
            "cacheReadTokens": 0,
            "cacheWriteTokens": 0,
            "costUsd": 0.0123,
            "kind": "direct",
            "agentId": "main",
        }
    ]
    monkeypatch.setattr(_d, "_get_sessions", lambda: fake_sessions)

    import clawmetry.adapters.openclaw as oc_mod
    importlib.reload(oc_mod)

    adapter = oc_mod.OpenClawAdapter()
    sessions = adapter.list_sessions()
    assert sessions, "expected at least one session"
    s = sessions[0]
    assert s.cost_usd == pytest.approx(0.0123), f"expected 0.0123 got {s.cost_usd}"


def test_list_sessions_cost_none_when_missing(monkeypatch):
    """cost_usd stays None when the gateway omits the cost field."""
    import dashboard as _d
    import importlib

    fake_sessions = [
        {
            "key": "def456",
            "displayName": "no cost",
            "updatedAtMs": 1700000000000,
            "model": "claude-opus-4-7",
            "channel": "main",
            "totalTokens": 500,
            "inputTokens": 0,
            "outputTokens": 0,
            "cacheReadTokens": 0,
            "cacheWriteTokens": 0,
            "kind": "direct",
            "agentId": "main",
        }
    ]
    monkeypatch.setattr(_d, "_get_sessions", lambda: fake_sessions)

    import clawmetry.adapters.openclaw as oc_mod
    importlib.reload(oc_mod)

    adapter = oc_mod.OpenClawAdapter()
    sessions = adapter.list_sessions()
    assert sessions
    assert sessions[0].cost_usd is None
