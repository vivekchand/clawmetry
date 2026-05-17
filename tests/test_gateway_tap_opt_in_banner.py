"""Tests for issue #1233 — gateway-tap opt-in banner on /api/overview.

PR #1228 flipped the live WS gateway tap to default-OFF. Users who
previously relied on it (Telegram, Signal, Discord, ...) silently lost
inbound message capture. This test suite covers the comms surface we
piggyback on /api/overview to nudge those users back to opt-in.

The helper under test is ``routes.overview._compute_gateway_tap_comms``,
which inspects the local DuckDB ``channel_messages`` table to decide
whether to show the banner.
"""

from __future__ import annotations

import importlib
from datetime import datetime, timedelta, timezone

import pytest
from flask import Flask


@pytest.fixture
def comms_app(tmp_path, monkeypatch):
    """Flask app with the overview blueprint + a fresh local DuckDB store.

    The fast path is enabled so /api/overview reads from DuckDB; the tap
    env var is cleared so the default-OFF cohort is exercised.
    """
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "events.duckdb"))
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_SECS", "0.05")
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_BATCH", "5")
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_READ", "1")
    monkeypatch.delenv("CLAWMETRY_ENABLE_WS_TAP", raising=False)

    import clawmetry.local_store as ls
    importlib.reload(ls)
    import routes.local_query as lq
    importlib.reload(lq)
    # Short-circuit the daemon HTTP proxy so the test never accidentally
    # talks to a running developer daemon and reads the real DuckDB.
    monkeypatch.setattr(lq, "local_store_via_daemon", lambda *a, **k: None)
    monkeypatch.setattr(lq, "_read_discovery", lambda: None)
    monkeypatch.setattr(lq, "_cached_discovery", lambda: None)
    import routes.overview as ov
    importlib.reload(ov)
    # Defeat the 5min cache between cases.
    ov._GATEWAY_TAP_COMMS_CACHE.update(ts=0.0, value=None)

    a = Flask(__name__)
    a.register_blueprint(ov.bp_overview)
    yield a, ls, ov
    try:
        ls.get_store().stop(flush=True)
    except Exception:
        pass


def _ingest_channel_msg(store, *, mid: str, days_ago: float) -> None:
    """Write a single channel_messages row dated ``days_ago`` days back."""
    ts = datetime.now(tz=timezone.utc) - timedelta(days=days_ago)
    store.ingest_channel_message({
        "id": mid,
        "agent_id": "main",
        "provider": "telegram",
        "channel_id": "chat-1",
        "sender_id": "user-1",
        "sender_name": "Tester",
        "body": "hello",
        "ts": ts.isoformat(),
        "direction": "in",
    })


def test_banner_fires_when_prior_activity_but_no_recent(comms_app):
    """1+ rows in prior 7d, 0 rows in last 24h, tap env unset → banner ON."""
    _, ls, ov = comms_app
    store = ls.get_store()
    # Three messages from 3 days ago — proves the user was previously
    # capturing inbound channel traffic. Nothing in the last 24h → gap is
    # active right now.
    _ingest_channel_msg(store, mid="m-3d-a", days_ago=3.0)
    _ingest_channel_msg(store, mid="m-3d-b", days_ago=3.0)
    _ingest_channel_msg(store, mid="m-5d-a", days_ago=5.0)

    out = ov._compute_gateway_tap_comms()
    assert out["show_gateway_tap_banner"] is True
    # show_pro_cta is True for non-Pro users (the default in tests).
    assert out["show_pro_cta"] is True


def test_banner_suppressed_when_recent_activity_present(comms_app):
    """Row in last 24h → tap isn't the gap → banner OFF."""
    _, ls, ov = comms_app
    store = ls.get_store()
    _ingest_channel_msg(store, mid="m-3d", days_ago=3.0)
    _ingest_channel_msg(store, mid="m-now", days_ago=0.1)  # within 24h

    out = ov._compute_gateway_tap_comms()
    assert out["show_gateway_tap_banner"] is False


def test_banner_suppressed_for_fresh_install(comms_app):
    """Empty channel_messages → fresh install, no prior activity → banner OFF."""
    _, _ls, ov = comms_app
    out = ov._compute_gateway_tap_comms()
    assert out["show_gateway_tap_banner"] is False


def test_banner_suppressed_when_tap_env_enabled(comms_app, monkeypatch):
    """User already opted back in via CLAWMETRY_ENABLE_WS_TAP=1 → banner OFF."""
    _, ls, ov = comms_app
    monkeypatch.setenv("CLAWMETRY_ENABLE_WS_TAP", "1")
    # Reset cache because the env state changed.
    ov._GATEWAY_TAP_COMMS_CACHE.update(ts=0.0, value=None)
    store = ls.get_store()
    _ingest_channel_msg(store, mid="m-3d", days_ago=3.0)

    out = ov._compute_gateway_tap_comms()
    assert out["show_gateway_tap_banner"] is False


def test_overview_response_carries_comms_envelope(comms_app):
    """/api/overview surfaces ``_comms`` so the dashboard JS can render."""
    a, ls, _ov = comms_app
    store = ls.get_store()
    store.ingest_session({
        "session_id": "sess-A", "agent_type": "openclaw", "title": "any",
        "started_at": "2026-05-11T10:00:00+00:00",
        "last_active_at": "2026-05-11T11:00:00+00:00",
        "status": "active", "total_tokens": 100,
        "metadata": {"model": "claude-opus-4-7"},
    })
    _ingest_channel_msg(store, mid="m-3d", days_ago=3.0)

    body = a.test_client().get("/api/overview").get_json() or {}
    assert body.get("_source") == "local_store"
    assert (body.get("_comms") or {}).get("show_gateway_tap_banner") is True
