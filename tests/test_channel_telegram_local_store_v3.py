"""Regression guard for the /api/channel/telegram DuckDB v3 events fast path
(Tier-1 #1565, refs #1583's coverage audit).

``routes/channels.py:_try_local_store_channel_events`` is a second-tier fast
path layered AFTER ``_try_local_store_provider_messages`` (which reads the
specialised ``channel_messages`` table). When the dedicated table is empty
but the unified ``events`` table has ``channel.in`` / ``channel.out`` rows
the sync daemon already wrote, this helper still serves DuckDB-first
instead of falling through to the legacy gateway.log grep + JSONL walker.

Why a separate v3 path:

  * On real OpenClaw v3 installs the daemon's chokepoint
    (``LocalStore.ingest_channel_event``) writes to BOTH ``channel_messages``
    AND ``events``, but only the ``events`` write is guaranteed — see
    ``feedback_synthetic_tests_missed_real_event_shape.md`` for the
    silent-zero bug class on this kind of dual-write contract.
  * Without this fallback, a daemon that restarted between writes (or a
    legacy ingest path that took the bare ``ingest()`` side-door) would
    leave the route silently log-scraping on every poll.

Tests cover:

  1. Populated v3 events → fast path returns ``_source='local_store_v3'``
     with telegram-only rows and the legacy ``{messages,total,todayIn,
     todayOut}`` envelope.
  2. Empty events table → helper returns ``None`` so the route falls
     through to the legacy walker.
  3. Provider filter — events for OTHER providers (signal/slack) must
     NOT bleed into the telegram response.
  4. Time-range / today counters honour the daemon's ISO ts strings
     (the 2026-05-17 audit found a class of routes that returned all
     events under "todayIn" because the ts substring match was loose).
"""

from __future__ import annotations

import importlib
import uuid
from datetime import datetime, timezone

import pytest
from flask import Flask


def _now_iso():
    return datetime.now(tz=timezone.utc).isoformat()


def _ingest_channel_event(
    store,
    *,
    provider: str,
    direction: str,
    body: str = "hello",
    sender_name: str = "alice",
    channel_id: str = "1532693273",
    ts: str | None = None,
    session_id: str | None = None,
):
    """Seed one channel event row in the exact shape
    ``LocalStore.ingest_channel_event`` would write (see
    clawmetry/local_store.py:1250-1264).

    We bypass the chokepoint here and call ``ingest`` directly so the test
    actually exercises the silent-zero contract: events-table populated,
    channel_messages table EMPTY — the very case the v3 fallback exists
    for."""
    store.ingest({
        "id":         f"ch-{uuid.uuid4().hex[:12]}",
        "node_id":    "node-test",
        "agent_type": "openclaw",
        "agent_id":   "main",
        "event_type": f"channel.{direction}",
        "ts":         ts or _now_iso(),
        "session_id": session_id,
        "workspace_id": None,
        "data": {
            "provider":    provider,
            "channel_id":  channel_id,
            "direction":   direction,
            "sender_name": sender_name,
            "body":        body,
        },
        "cost_usd":    None,
        "token_count": None,
        "model":       None,
    })


@pytest.fixture
def app(tmp_path, monkeypatch):
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "events.duckdb"))
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_SECS", "0.05")
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_READ", "1")

    import clawmetry.local_store as ls
    importlib.reload(ls)
    import routes.local_query as lq
    importlib.reload(lq)
    import routes.channels as channels_mod
    importlib.reload(channels_mod)

    # Isolate from a contributor's running daemon: without this, ``_ls_call``
    # proxies through ``~/.clawmetry/local_query.json`` and the daemon
    # queries its OWN production DuckDB instead of our tmp_path fixture.
    monkeypatch.setattr(lq, "_read_discovery", lambda: None)

    import dashboard  # noqa: F401

    a = Flask(__name__)
    a.register_blueprint(channels_mod.bp_channels)
    yield a, ls, channels_mod
    try:
        ls.get_store().stop(flush=True)
    except Exception:
        pass


def test_telegram_v3_events_path_serves_when_channel_messages_empty(app):
    """Populated v3 events but empty ``channel_messages`` → fast path
    must return ``_source='local_store_v3'`` with the seeded rows."""
    a, ls, _c = app
    store = ls.get_store()
    _ingest_channel_event(
        store,
        provider="telegram",
        direction="in",
        body="hello clawd",
        sender_name="vivek",
        channel_id="1532693273",
    )
    _ingest_channel_event(
        store,
        provider="telegram",
        direction="out",
        body="hi back",
        channel_id="1532693273",
    )
    store.flush()
    # Contract check: events table populated, channel_messages NOT
    # (the v3 events helper is the only thing that can serve this).
    assert len(store.query_events(event_type="channel.in", limit=5)) >= 1
    assert len(store.query_events(event_type="channel.out", limit=5)) >= 1
    assert store.query_channel_messages(provider="telegram", limit=5) == []

    r = a.test_client().get("/api/channel/telegram?limit=10")
    assert r.status_code == 200, r.get_data(as_text=True)
    body = r.get_json()
    assert body.get("_source") == "local_store_v3", (
        f"_source must be local_store_v3 (v3 events fallback); got "
        f"{body.get('_source')!r}"
    )
    msgs = body.get("messages") or []
    assert len(msgs) == 2, f"expected 2 telegram messages, got {len(msgs)}"
    directions = sorted(m["direction"] for m in msgs)
    assert directions == ["in", "out"]
    # sender_name surfaced from the data blob (not "User" fallback).
    inbound = next(m for m in msgs if m["direction"] == "in")
    assert inbound["sender"] == "vivek"
    assert inbound["text"] == "hello clawd"
    assert inbound["chatId"] == "1532693273"


def test_telegram_v3_events_empty_returns_legacy_fallback(app):
    """Empty events table → helper returns ``None`` so the route falls
    through to the legacy gateway.log + JSONL walker. The walker on a
    test box with no log files yields an empty payload but MUST NOT carry
    ``_source='local_store_v3'`` (that tag is reserved for the fast
    path)."""
    a, ls, _c = app
    # Sanity: nothing seeded.
    assert ls.get_store().query_events(event_type="channel.in", limit=5) == []
    assert ls.get_store().query_events(event_type="channel.out", limit=5) == []

    r = a.test_client().get("/api/channel/telegram")
    assert r.status_code == 200
    body = r.get_json()
    assert body.get("_source") != "local_store_v3", (
        "empty events → fast path must defer to legacy walker; got "
        f"_source={body.get('_source')!r}"
    )


def test_telegram_v3_events_filters_by_provider(app):
    """A signal/slack event MUST NOT bleed into the telegram response.
    The provider tag lives on ``data.provider`` and the helper filters in
    Python — guard against the helper accidentally serving the whole
    channel.in / channel.out cross-section."""
    a, ls, _c = app
    store = ls.get_store()
    _ingest_channel_event(
        store,
        provider="telegram",
        direction="in",
        body="tg msg",
        sender_name="alice",
    )
    _ingest_channel_event(
        store,
        provider="signal",
        direction="in",
        body="signal msg",
        sender_name="bob",
    )
    _ingest_channel_event(
        store,
        provider="slack",
        direction="in",
        body="slack msg",
        sender_name="carol",
    )
    store.flush()

    r = a.test_client().get("/api/channel/telegram?limit=10")
    body = r.get_json()
    assert body.get("_source") == "local_store_v3"
    msgs = body.get("messages") or []
    assert len(msgs) == 1, (
        f"telegram route must filter to provider=telegram only; got {len(msgs)} "
        f"rows: {[m['text'] for m in msgs]}"
    )
    assert msgs[0]["text"] == "tg msg"
    assert msgs[0]["sender"] == "alice"


def test_telegram_v3_events_today_counters_match_iso_prefix(app):
    """Today-in/today-out counters use the ``YYYY-MM-DD`` prefix on the
    ISO ts. Seed a fresh-today row + an old-2024 row and confirm only the
    fresh-today row counts. Guards against the loose substring match the
    2026-05-17 audit flagged in a peer route."""
    a, ls, _c = app
    store = ls.get_store()
    _ingest_channel_event(
        store,
        provider="telegram",
        direction="in",
        body="today inbound",
    )
    _ingest_channel_event(
        store,
        provider="telegram",
        direction="out",
        body="today outbound",
    )
    _ingest_channel_event(
        store,
        provider="telegram",
        direction="in",
        body="old inbound",
        ts="2024-01-01T08:30:00+00:00",
    )
    store.flush()

    r = a.test_client().get("/api/channel/telegram?limit=10")
    body = r.get_json()
    assert body["_source"] == "local_store_v3"
    # 3 telegram rows total — old one still surfaces in ``messages``, just
    # not in today counters.
    assert body["total"] == 3
    assert body["todayIn"] == 1, (
        f"only 1 inbound row carries today's date prefix; got todayIn="
        f"{body['todayIn']}"
    )
    assert body["todayOut"] == 1
