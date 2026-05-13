"""Tests for the DuckDB coverage Phase-4 channel-message foundation
landed 2026-05-13 (issue #1088 follow-up).

Each test verifies the new ``_try_local_store_*`` fast path on
``routes/channels.py`` returns ``_source: "local_store"`` when the new
DuckDB ``channel_messages`` table has the relevant rows. The remaining
18 per-provider channel routes (Telegram, Signal, WhatsApp, Discord,
Slack, IRC, iMessage, WebChat, …) land in follow-up PRs once the schema
is proven by these three.

Surfaces under test:
  - /api/channels/<provider>/messages   routes/channels.py
  - /api/channels/<provider>/threads    routes/channels.py
  - /api/channels/summary               routes/channels.py
"""

from __future__ import annotations

import importlib

import pytest
from flask import Flask


@pytest.fixture
def fresh_store(tmp_path, monkeypatch):
    """Reload local_store against a fresh DuckDB file with the read flag on."""
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


def _seed_telegram(store):
    """Seed a small mixed inbound + outbound Telegram conversation across
    two channel_ids so the threads + summary endpoints have something
    interesting to aggregate."""
    msgs = [
        ("m-1", "1234", "Alice", "hi there",  "in",  "2026-05-13T10:00:00Z"),
        ("m-2", "1234", "Bot",   "(reply)",   "out", "2026-05-13T10:00:01Z"),
        ("m-3", "1234", "Alice", "thanks",    "in",  "2026-05-13T10:00:02Z"),
        ("m-4", "9999", "Bob",   "hey",       "in",  "2026-05-13T09:00:00Z"),
    ]
    for mid, chan, sender, body, dirn, ts in msgs:
        store.ingest_channel_message({
            "id":          mid,
            "provider":    "telegram",
            "channel_id":  chan,
            "sender_name": sender,
            "sender_id":   sender.lower(),
            "body":        body,
            "ts":          ts,
            "direction":   dirn,
            "session_key": f"sess-{chan}",
        })


# ── /api/channels/<provider>/messages ──────────────────────────────────────


def test_channel_messages_fast_path(fresh_store):
    store = fresh_store.get_store()
    _seed_telegram(store)
    c = _client()
    r = c.get("/api/channels/telegram/messages")
    assert r.status_code == 200
    body = r.get_json()
    assert body.get("_source") == "local_store"
    assert body["provider"] == "telegram"
    assert body["total"] == 4
    # Most-recent first; first message in the response is m-3 (10:00:02Z).
    first = body["messages"][0]
    assert first["id"] == "m-3"
    assert first["direction"] == "in"
    assert first["sender"] == "Alice"
    assert first["channelId"] == "1234"


def test_channel_messages_empty_returns_local_store_empty_tag(fresh_store):
    """No rows ingested → endpoint still serves a tagged empty response so
    the cloud UI distinguishes "schema live, no rows yet" from a 404."""
    fresh_store.get_store()  # ensure schema exists
    c = _client()
    r = c.get("/api/channels/telegram/messages")
    assert r.status_code == 200
    body = r.get_json()
    assert body["_source"] == "local_store_empty"
    assert body["messages"] == []


# ── /api/channels/<provider>/threads ───────────────────────────────────────


def test_channel_threads_fast_path(fresh_store):
    store = fresh_store.get_store()
    _seed_telegram(store)
    c = _client()
    r = c.get("/api/channels/telegram/threads")
    assert r.status_code == 200
    body = r.get_json()
    assert body.get("_source") == "local_store"
    assert body["provider"] == "telegram"
    assert body["total"] == 2
    by_chan = {t["channelId"]: t for t in body["threads"]}
    assert set(by_chan) == {"1234", "9999"}
    main = by_chan["1234"]
    assert main["msgIn"] == 2
    assert main["msgOut"] == 1
    assert main["total"] == 3
    assert main["lastSnippet"] == "thanks"
    # Most-recent thread sorted first in the response.
    assert body["threads"][0]["channelId"] == "1234"


# ── /api/channels/summary ──────────────────────────────────────────────────


def test_channels_summary_fast_path(fresh_store):
    store = fresh_store.get_store()
    _seed_telegram(store)
    # Toss in one Slack inbound so the summary spans more than one provider.
    store.ingest_channel_message({
        "id":         "s-1",
        "provider":   "slack",
        "channel_id": "C42",
        "body":       "ping",
        "ts":         "2026-05-13T11:00:00Z",
        "direction":  "in",
    })
    c = _client()
    r = c.get("/api/channels/summary")
    assert r.status_code == 200
    body = r.get_json()
    assert body.get("_source") == "local_store"
    by_prov = {p["provider"]: p for p in body["providers"]}
    assert set(by_prov) == {"telegram", "slack"}
    tg = by_prov["telegram"]
    assert tg["msgIn"] == 3
    assert tg["msgOut"] == 1
    assert tg["distinctChannels"] == 2
    assert by_prov["slack"]["msgIn"] == 1
    # Cross-provider totals.
    assert body["totals"]["msgIn"] == 4
    assert body["totals"]["msgOut"] == 1
    assert body["totals"]["total"] == 5
