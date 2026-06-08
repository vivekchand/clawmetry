"""Tests for issue #2875 — session fields absent after SQLite metadata migration.

Verifies that _get_sessions() passes the six SQLite-migrated session fields
(ended_at, end_reason, parent_id, message_count, title, cost_status) through
from the gateway response, and that list_sessions() maps them onto Session.

Fingerprint: hgap-5f334cfa6d
"""
from __future__ import annotations

import importlib

import pytest


_FAKE_BASE = {
    "key": "sess-abc123",
    "displayName": "My session",
    "updatedAtMs": 1_748_000_000_000,
    "model": "claude-opus-4-7",
    "channel": "main",
    "totalTokens": 1000,
    "inputTokens": 600,
    "outputTokens": 400,
    "cacheReadTokens": 0,
    "cacheWriteTokens": 0,
    "kind": "direct",
    "agentId": "main",
}


def _sessions(monkeypatch, extra_fields: dict):
    import dashboard as _d
    import clawmetry.adapters.openclaw as oc_mod

    fake = {**_FAKE_BASE, **extra_fields}
    monkeypatch.setattr(_d, "_get_sessions", lambda: [fake])
    importlib.reload(oc_mod)
    adapter = oc_mod.OpenClawAdapter()
    result = adapter.list_sessions()
    assert result, "expected at least one session"
    return result[0]


def test_ended_at_populated(monkeypatch):
    """_get_sessions() normalises endedAtMs → endedAt; list_sessions() maps it."""
    s = _sessions(monkeypatch, {"endedAt": 1_748_001_000_000})
    assert s.ended_at == pytest.approx(1_748_001_000_000 / 1000.0)


def test_ended_at_zero_treated_as_absent(monkeypatch):
    """endedAt=0 means no end time; Session.ended_at should be None."""
    s = _sessions(monkeypatch, {"endedAt": 0})
    assert s.ended_at is None


def test_ended_at_none_when_absent(monkeypatch):
    s = _sessions(monkeypatch, {})
    assert s.ended_at is None


def test_end_reason(monkeypatch):
    s = _sessions(monkeypatch, {"endReason": "user_stopped"})
    assert s.end_reason == "user_stopped"


def test_end_reason_empty_when_absent(monkeypatch):
    s = _sessions(monkeypatch, {})
    assert s.end_reason == ""


def test_parent_id_from_parentId(monkeypatch):
    s = _sessions(monkeypatch, {"parentId": "parent-sess-xyz"})
    assert s.parent_id == "parent-sess-xyz"


def test_parent_id_none_when_absent(monkeypatch):
    s = _sessions(monkeypatch, {})
    assert s.parent_id is None


def test_message_count(monkeypatch):
    s = _sessions(monkeypatch, {"messageCount": 42})
    assert s.message_count == 42


def test_message_count_zero_when_absent(monkeypatch):
    s = _sessions(monkeypatch, {})
    assert s.message_count == 0


def test_title(monkeypatch):
    s = _sessions(monkeypatch, {"title": "Refactor auth module"})
    assert s.title == "Refactor auth module"


def test_title_empty_when_absent(monkeypatch):
    s = _sessions(monkeypatch, {})
    assert s.title == ""


def test_cost_status(monkeypatch):
    s = _sessions(monkeypatch, {"costStatus": "estimated"})
    assert s.cost_status == "estimated"


def test_cost_status_empty_when_absent(monkeypatch):
    s = _sessions(monkeypatch, {})
    assert s.cost_status == ""


def test_all_fields_together(monkeypatch):
    """All six new fields populate correctly in a single session."""
    s = _sessions(
        monkeypatch,
        {
            "endedAt": 1_748_003_000_000,
            "endReason": "max_turns",
            "parentId": "parent-999",
            "messageCount": 17,
            "title": "Feature branch",
            "costStatus": "exact",
        },
    )
    assert s.ended_at == pytest.approx(1_748_003_000.0)
    assert s.end_reason == "max_turns"
    assert s.parent_id == "parent-999"
    assert s.message_count == 17
    assert s.title == "Feature branch"
    assert s.cost_status == "exact"


def test_existing_fields_unaffected(monkeypatch):
    """Existing token/cost/model fields still work after the change."""
    s = _sessions(monkeypatch, {"costUsd": 0.0055, "messageCount": 5})
    assert s.cost_usd == pytest.approx(0.0055)
    assert s.total_tokens == 1000
    assert s.model == "claude-opus-4-7"
    assert s.message_count == 5


# ── _get_sessions() gateway-normalization tests ──────────────────────────────
# These test the dashboard.py change: that _get_sessions() extracts the new
# fields from raw gateway responses and places them under normalized keys.

def test_get_sessions_normalises_endedAtMs(monkeypatch):
    """_get_sessions() maps gateway endedAtMs → dict key 'endedAt'."""
    import dashboard as _d

    fake_api = {
        "sessions": [
            {
                "key": "x1",
                "displayName": "test",
                "updatedAtMs": 1_748_000_000_000,
                "endedAtMs": 1_748_001_000_000,
                "endReason": "user_stopped",
                "parentId": "p-1",
                "messageCount": 5,
                "title": "My title",
                "costStatus": "estimated",
                "model": "claude-opus-4-7",
                "channel": "main",
                "totalTokens": 100,
                "kind": "direct",
                "agentId": "main",
            }
        ]
    }
    monkeypatch.setattr(_d, "_gw_ws_rpc", lambda *a, **k: fake_api)
    monkeypatch.setitem(_d._sessions_cache, "data", None)
    monkeypatch.setitem(_d._sessions_cache, "ts", 0)

    sessions = _d._get_sessions()
    assert sessions, "expected one session"
    s = sessions[0]
    assert s["endedAt"] == 1_748_001_000_000
    assert s["endReason"] == "user_stopped"
    assert s["parentId"] == "p-1"
    assert s["messageCount"] == 5
    assert s["title"] == "My title"
    assert s["costStatus"] == "estimated"


def test_get_sessions_normalises_parentSessionId_fallback(monkeypatch):
    """_get_sessions() maps parentSessionId as fallback for parentId."""
    import dashboard as _d

    fake_api = {
        "sessions": [
            {
                "key": "x2",
                "displayName": "test2",
                "updatedAtMs": 1_748_000_000_000,
                "parentSessionId": "fallback-parent",
                "model": "claude-opus-4-7",
                "channel": "main",
                "totalTokens": 0,
                "kind": "direct",
                "agentId": "main",
            }
        ]
    }
    monkeypatch.setattr(_d, "_gw_ws_rpc", lambda *a, **k: fake_api)
    monkeypatch.setitem(_d._sessions_cache, "data", None)
    monkeypatch.setitem(_d._sessions_cache, "ts", 0)

    sessions = _d._get_sessions()
    assert sessions
    assert sessions[0]["parentId"] == "fallback-parent"
