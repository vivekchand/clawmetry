"""Tests for the /api/sessions local-store fast path (epic #964 PR 3 of 3).

Same opt-in pattern as test_brain_local_fastpath.py:
- CLAWMETRY_LOCAL_STORE_READ=1 + populated store → returns from DuckDB
- Flag unset → falls through to legacy gateway/JSONL path
- Empty store → falls through (so fresh installs see normal data)
"""

from __future__ import annotations

import importlib

import pytest
from flask import Flask


@pytest.fixture
def app(tmp_path, monkeypatch):
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "events.duckdb"))
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_SECS", "0.05")
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_READ", "1")

    import clawmetry.local_store as ls
    importlib.reload(ls)
    import routes.sessions as sessions_mod
    importlib.reload(sessions_mod)

    a = Flask(__name__)
    a.register_blueprint(sessions_mod.bp_sessions)
    yield a, ls
    try:
        ls.get_store().stop(flush=True)
    except Exception:
        pass


def test_sessions_fast_path_returns_local_rows(app):
    a, ls = app
    store = ls.get_store()
    store.ingest_session({
        "session_id": "sess-fast-A",
        "agent_type": "openclaw",
        "title": "Refactoring routes/sessions.py",
        "started_at": "2026-05-11T10:00:00Z",
        "last_active_at": "2026-05-11T10:30:00Z",
        "status": "active",
        "total_tokens": 12500,
        "cost_usd": 0.42,
        "message_count": 17,
        "metadata": {"channel": "telegram"},
    })
    store.ingest_session({
        "session_id": "sess-fast-B",
        "agent_type": "claude_code",
        "title": "Adding multi-agent schema",
        "started_at": "2026-05-11T09:00:00Z",
        "last_active_at": "2026-05-11T11:00:00Z",
        "status": "active",
        "total_tokens": 50000,
        "cost_usd": 1.7,
    })

    c = a.test_client()
    r = c.get("/api/sessions")
    assert r.status_code == 200
    body = r.get_json()
    assert body.get("_source") == "local_store"
    assert len(body["sessions"]) == 2
    by_id = {s["session_id"]: s for s in body["sessions"]}
    # Most-recent-first: B (11:00) before A (10:30)
    assert body["sessions"][0]["session_id"] == "sess-fast-B"
    assert by_id["sess-fast-A"]["agent_type"] == "openclaw"
    assert by_id["sess-fast-B"]["agent_type"] == "claude_code"
    assert by_id["sess-fast-A"]["channel"] == "telegram"
    assert by_id["sess-fast-A"]["total_cost"] == 0.42


def test_sessions_fast_path_falls_back_when_store_empty(app):
    """Empty store → fast path returns None → legacy path runs (which we
    can't easily exercise here, so we just verify no _source tag)."""
    a, _ls = app
    c = a.test_client()
    r = c.get("/api/sessions")
    # Falls through to gateway path (returns 500 in unit-test context with
    # no gateway, OR returns sessions if there's a workspace; either way
    # it's NOT tagged _source: local_store).
    body = r.get_json() or {}
    assert body.get("_source") != "local_store"


def test_sessions_fast_path_disabled_without_flag(tmp_path, monkeypatch):
    """No CLAWMETRY_LOCAL_STORE_READ → fast path never runs even with
    a populated store. Default = zero behavior change for existing deploys."""
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "events.duckdb"))
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_SECS", "0.05")
    monkeypatch.delenv("CLAWMETRY_LOCAL_STORE_READ", raising=False)

    import clawmetry.local_store as ls
    importlib.reload(ls)
    import routes.sessions as sessions_mod
    importlib.reload(sessions_mod)

    store = ls.get_store()
    store.ingest_session({
        "session_id": "sess-noflag",
        "agent_type": "openclaw",
        "title": "Should not appear",
        "started_at": "2026-05-11T10:00:00Z",
    })

    a = Flask(__name__)
    a.register_blueprint(sessions_mod.bp_sessions)
    r = a.test_client().get("/api/sessions")
    body = r.get_json() or {}
    assert body.get("_source") != "local_store"
    try:
        store.stop(flush=True)
    except Exception:
        pass
