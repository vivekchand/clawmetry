"""Tests for the DuckDB coverage Phase-5 channel migration landed
2026-05-13 (issue #1088 follow-up to PR #1100).

Each test verifies the new ``_try_local_store_provider_messages``
fast-path on ``routes/channels.py`` returns ``_source: "local_store"``
when the DuckDB ``channel_messages`` table has the relevant rows. There
is one test per per-provider route migrated this PR (19 routes); three
adapters (iMessage, BlueBubbles, TUI) are intentionally NOT migrated
because their data isn't in ``channel_messages`` — see the section
header at the top of ``routes/channels.py`` for the reasoning.

Surfaces under test (one assertion each):
  /api/channel/telegram        routes/channels.py
  /api/channel/whatsapp        routes/channels.py
  /api/channel/signal          routes/channels.py
  /api/channel/discord         routes/channels.py
  /api/channel/slack           routes/channels.py
  /api/channel/irc             routes/channels.py
  /api/channel/webchat         routes/channels.py
  /api/channel/googlechat      routes/channels.py
  /api/channel/msteams         routes/channels.py
  /api/channel/matrix          routes/channels.py
  /api/channel/mattermost      routes/channels.py
  /api/channel/line            routes/channels.py
  /api/channel/nostr           routes/channels.py
  /api/channel/twitch          routes/channels.py
  /api/channel/feishu          routes/channels.py
  /api/channel/zalo            routes/channels.py
  /api/channel/tlon            routes/channels.py
  /api/channel/synology-chat   routes/channels.py
  /api/channel/nextcloud-talk  routes/channels.py
"""

from __future__ import annotations

import importlib

import pytest
from flask import Flask


@pytest.fixture
def fresh_store(tmp_path, monkeypatch):
    """Reload local_store against a fresh DuckDB file with the read flag on.

    Mirrors the Phase-4 fixture so the two test files compose: each runs in
    its own tmp DB and reloads the route module so the late-bound store
    handle picks up the freshly-reloaded local_store."""
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "events.duckdb"))
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_SECS", "0.05")
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_BATCH", "1")
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_READ", "1")

    import clawmetry.local_store as ls
    importlib.reload(ls)
    yield ls
    try:
        ls.get_store().stop(flush=True)
    except Exception:
        pass


def _client():
    """Reload routes/channels.py so its late-bound store handle picks up
    the freshly-reloaded local_store, then return a Flask test client."""
    import routes.channels as ch
    importlib.reload(ch)
    a = Flask(__name__)
    a.register_blueprint(ch.bp_channels)
    return a.test_client()


def _seed(store, provider: str, body: str = "hello", channel_id: str = "ch-1") -> None:
    """Seed one inbound message for ``provider`` so the per-provider route
    has at least one DuckDB row to serve. Tests assert ``_source`` only —
    the legacy-shape envelope is exercised by the Phase-4 messages test."""
    store.ingest_channel_message({
        "id":          f"{provider}-1",
        "provider":    provider,
        "channel_id":  channel_id,
        "sender_name": "Alice",
        "sender_id":   "alice",
        "body":        body,
        "ts":          "2026-05-13T10:00:00Z",
        "direction":   "in",
        "session_key": f"sess-{provider}",
    })


# ── Per-provider fast-path assertions ──────────────────────────────────────


def test_telegram_fast_path(fresh_store):
    _seed(fresh_store.get_store(), "telegram")
    r = _client().get("/api/channel/telegram")
    assert r.status_code == 200
    assert r.get_json().get("_source") == "local_store"


def test_whatsapp_fast_path(fresh_store):
    _seed(fresh_store.get_store(), "whatsapp")
    r = _client().get("/api/channel/whatsapp")
    assert r.status_code == 200
    assert r.get_json().get("_source") == "local_store"


def test_signal_fast_path(fresh_store):
    _seed(fresh_store.get_store(), "signal")
    r = _client().get("/api/channel/signal")
    assert r.status_code == 200
    assert r.get_json().get("_source") == "local_store"


def test_discord_fast_path(fresh_store):
    _seed(fresh_store.get_store(), "discord", body="[Discord MyGuild #general] hello")
    r = _client().get("/api/channel/discord")
    assert r.status_code == 200
    body = r.get_json()
    assert body.get("_source") == "local_store"
    # Extras extractor should have parsed guild + channel out of the body.
    assert "MyGuild" in body.get("guilds", [])
    assert "general" in body.get("channels", [])


def test_slack_fast_path(fresh_store):
    _seed(fresh_store.get_store(), "slack", body="[Slack acme #random] ping")
    r = _client().get("/api/channel/slack")
    assert r.status_code == 200
    body = r.get_json()
    assert body.get("_source") == "local_store"
    assert "acme" in body.get("workspaces", [])


def test_irc_fast_path(fresh_store):
    _seed(fresh_store.get_store(), "irc", body="[IRC #python alice] hey")
    r = _client().get("/api/channel/irc")
    assert r.status_code == 200
    body = r.get_json()
    assert body.get("_source") == "local_store"
    assert "#python" in body.get("channels", [])
    assert body.get("status") == "connected"


def test_webchat_fast_path(fresh_store):
    _seed(fresh_store.get_store(), "webchat")
    r = _client().get("/api/channel/webchat")
    assert r.status_code == 200
    body = r.get_json()
    assert body.get("_source") == "local_store"
    # session_key is set in _seed → activeSessions counts it.
    assert body.get("activeSessions") == 1
    assert body.get("lastActive") == "2026-05-13T10:00:00Z"


def test_googlechat_fast_path(fresh_store):
    _seed(fresh_store.get_store(), "googlechat")
    r = _client().get("/api/channel/googlechat")
    assert r.status_code == 200
    body = r.get_json()
    assert body.get("_source") == "local_store"
    assert body.get("spaces") == []


def test_msteams_fast_path(fresh_store):
    _seed(fresh_store.get_store(), "msteams")
    r = _client().get("/api/channel/msteams")
    assert r.status_code == 200
    body = r.get_json()
    assert body.get("_source") == "local_store"
    assert body.get("teams") == []


def test_matrix_fast_path(fresh_store):
    _seed(fresh_store.get_store(), "matrix")
    r = _client().get("/api/channel/matrix")
    assert r.status_code == 200
    assert r.get_json().get("_source") == "local_store"


def test_mattermost_fast_path(fresh_store):
    _seed(fresh_store.get_store(), "mattermost")
    r = _client().get("/api/channel/mattermost")
    assert r.status_code == 200
    body = r.get_json()
    assert body.get("_source") == "local_store"
    assert body.get("channels") == []


def test_line_fast_path(fresh_store):
    _seed(fresh_store.get_store(), "line")
    r = _client().get("/api/channel/line")
    assert r.status_code == 200
    assert r.get_json().get("_source") == "local_store"


def test_nostr_fast_path(fresh_store):
    _seed(fresh_store.get_store(), "nostr")
    r = _client().get("/api/channel/nostr")
    assert r.status_code == 200
    assert r.get_json().get("_source") == "local_store"


def test_twitch_fast_path(fresh_store):
    _seed(fresh_store.get_store(), "twitch")
    r = _client().get("/api/channel/twitch")
    assert r.status_code == 200
    assert r.get_json().get("_source") == "local_store"


def test_feishu_fast_path(fresh_store):
    _seed(fresh_store.get_store(), "feishu")
    r = _client().get("/api/channel/feishu")
    assert r.status_code == 200
    assert r.get_json().get("_source") == "local_store"


def test_zalo_fast_path(fresh_store):
    _seed(fresh_store.get_store(), "zalo")
    r = _client().get("/api/channel/zalo")
    assert r.status_code == 200
    assert r.get_json().get("_source") == "local_store"


def test_tlon_fast_path(fresh_store):
    _seed(fresh_store.get_store(), "tlon")
    r = _client().get("/api/channel/tlon")
    assert r.status_code == 200
    assert r.get_json().get("_source") == "local_store"


def test_synology_chat_fast_path(fresh_store):
    _seed(fresh_store.get_store(), "synology-chat")
    r = _client().get("/api/channel/synology-chat")
    assert r.status_code == 200
    assert r.get_json().get("_source") == "local_store"


def test_nextcloud_talk_fast_path(fresh_store):
    _seed(fresh_store.get_store(), "nextcloud-talk")
    r = _client().get("/api/channel/nextcloud-talk")
    assert r.status_code == 200
    assert r.get_json().get("_source") == "local_store"
