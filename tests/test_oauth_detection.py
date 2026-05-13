"""Tests for issue #556 — Anthropic OAuth detection on /api/overview.

Some users authenticate against Anthropic via Claude.ai OAuth (``sk-ant-oat...``)
rather than an API key (``sk-ant-api...``). OAuth tokens have lower rate
limits and different pricing, so we surface a dashboard banner prompting
migration. The backend detector scans the most recent ~50 events for two
signals:

  1. ``data.api_key_prefix`` field — explicit hint emitted by some
     interceptors.
  2. A raw ``Authorization: Bearer sk-ant-oat...`` substring anywhere in
     the event payload (covers captured HTTP request dumps).

This test seeds the DuckDB local store with events that trigger each path
and asserts the ``/api/overview`` response carries ``client_health``.
"""

from __future__ import annotations

import importlib
import time
from datetime import datetime, timezone

import pytest
from flask import Flask


# ─────────────────────────────────────────────────────────────────────────────
# fixtures
# ─────────────────────────────────────────────────────────────────────────────


@pytest.fixture
def overview_app(tmp_path, monkeypatch):
    """Flask app + freshly-reloaded local_store + routes.overview blueprint."""
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "events.duckdb"))
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_SECS", "0.05")
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_BATCH", "5")
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_READ", "1")

    import clawmetry.local_store as ls
    importlib.reload(ls)
    import routes.overview as ov
    importlib.reload(ov)

    a = Flask(__name__)
    a.register_blueprint(ov.bp_overview)
    yield a, ls, ov
    try:
        ls.get_store().stop(flush=True)
    except Exception:
        pass


def _iso(epoch_seconds: float) -> str:
    return datetime.fromtimestamp(epoch_seconds, tz=timezone.utc).isoformat()


def _wait_flush(store, t: float = 2.0) -> None:
    deadline = time.monotonic() + t
    while time.monotonic() < deadline:
        if store.health()["ring_depth"] == 0:
            return
        time.sleep(0.02)


# ─────────────────────────────────────────────────────────────────────────────
# unit tests on the helper directly
# ─────────────────────────────────────────────────────────────────────────────


def test_detect_returns_false_when_store_empty(overview_app):
    """No events stored → using_oauth=False, last_seen_ts=None."""
    _a, _ls, ov = overview_app
    result = ov._detect_anthropic_oauth()
    assert result == {"using_oauth": False, "last_seen_ts": None}


def test_detect_flags_oauth_bearer_in_event_payload(overview_app):
    """Event with ``Authorization: Bearer sk-ant-oat-...`` in data → True."""
    _a, ls, ov = overview_app
    store = ls.get_store()
    store.ingest({
        "id": "ev-oat-1",
        "node_id": "agent+test",
        "agent_id": "main",
        "session_id": "sess-oat",
        "event_type": "http_request",
        "ts": _iso(time.time()),
        "data": {
            "method": "POST",
            "url": "https://api.anthropic.com/v1/messages",
            "headers": {
                "Authorization": "Bearer sk-ant-oat-01-abc123def456",
                "anthropic-version": "2023-06-01",
            },
        },
        "model": "claude-opus-4-7",
    })
    _wait_flush(store)

    result = ov._detect_anthropic_oauth()
    assert result["using_oauth"] is True
    assert result["last_seen_ts"]  # non-empty ISO timestamp


def test_detect_flags_api_key_prefix_field(overview_app):
    """Event with explicit ``data.api_key_prefix`` starting ``sk-ant-oat`` → True."""
    _a, ls, ov = overview_app
    store = ls.get_store()
    store.ingest({
        "id": "ev-prefix-1",
        "node_id": "agent+test",
        "agent_id": "main",
        "session_id": "sess-prefix",
        "event_type": "llm_call",
        "ts": _iso(time.time()),
        "data": {"api_key_prefix": "sk-ant-oat-01-xxxx"},
        "model": "claude-sonnet-4-7",
    })
    _wait_flush(store)

    result = ov._detect_anthropic_oauth()
    assert result["using_oauth"] is True


def test_detect_returns_false_for_api_key_events(overview_app):
    """Events with API-key prefix (sk-ant-api) and no OAuth markers → False."""
    _a, ls, ov = overview_app
    store = ls.get_store()
    store.ingest({
        "id": "ev-api-1",
        "node_id": "agent+test",
        "agent_id": "main",
        "session_id": "sess-api",
        "event_type": "http_request",
        "ts": _iso(time.time()),
        "data": {
            "headers": {"Authorization": "Bearer sk-ant-api03-abc123def456"},
            "api_key_prefix": "sk-ant-api03",
        },
        "model": "claude-opus-4-7",
    })
    _wait_flush(store)

    result = ov._detect_anthropic_oauth()
    assert result["using_oauth"] is False
    assert result["last_seen_ts"] is None


# ─────────────────────────────────────────────────────────────────────────────
# integration: /api/overview wires client_health into its response body
# ─────────────────────────────────────────────────────────────────────────────


def test_overview_response_includes_client_health_block(overview_app):
    """/api/overview must always include the client_health block, even when
    the store is empty (using_oauth=False is the right default)."""
    a, _ls, _ov = overview_app
    # Seed a session so the fast path actually runs.
    store = _ls.get_store()
    store.ingest_session({
        "session_id": "sess-shape",
        "agent_type": "openclaw",
        "title": "shape check",
        "started_at": "2026-05-11T10:00:00+00:00",
        "last_active_at": "2026-05-11T11:00:00+00:00",
        "status": "active",
        "total_tokens": 100,
        "metadata": {"model": "claude-opus-4-7"},
    })

    r = a.test_client().get("/api/overview")
    assert r.status_code == 200
    body = r.get_json() or {}
    assert "client_health" in body, body
    ch = body["client_health"]
    assert isinstance(ch, dict)
    assert "using_oauth" in ch
    assert "last_seen_ts" in ch
    # No OAuth event seeded → flag stays off.
    assert ch["using_oauth"] is False


def test_overview_response_flags_oauth_when_event_present(overview_app):
    """End-to-end: an OAuth event in the local store flows through the
    overview fast path as client_health.using_oauth=True."""
    a, ls, _ov = overview_app
    store = ls.get_store()
    # Seed a session so the fast path runs (it returns None on empty sessions).
    store.ingest_session({
        "session_id": "sess-oauth-int",
        "agent_type": "openclaw",
        "title": "oauth detection check",
        "started_at": "2026-05-11T10:00:00+00:00",
        "last_active_at": "2026-05-11T11:00:00+00:00",
        "status": "active",
        "total_tokens": 100,
        "metadata": {"model": "claude-opus-4-7"},
    })
    store.ingest({
        "id": "ev-oat-int",
        "node_id": "agent+test",
        "agent_id": "main",
        "session_id": "sess-oauth-int",
        "event_type": "http_request",
        "ts": _iso(time.time()),
        "data": {"headers": {"Authorization": "Bearer sk-ant-oat-01-xyz"}},
        "model": "claude-opus-4-7",
    })
    _wait_flush(store)

    r = a.test_client().get("/api/overview")
    body = r.get_json() or {}
    ch = body.get("client_health") or {}
    assert ch.get("using_oauth") is True
    assert ch.get("last_seen_ts")
