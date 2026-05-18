"""Regression guard for the /api/channel/whatsapp DuckDB v3 events fast path
(Tier-2 #1565, 2026-05-18 coverage audit).

Sister of ``test_channel_signal_local_store_v3.py`` —
``api_channel_whatsapp`` now shares the same dual-tier contract
(``_try_local_store_provider_messages`` first, then
``_try_local_store_channel_events`` for the v3 events-table fallback)
that Telegram / Signal / BlueBubbles already enforce. The silent-zero
hazard memory ``feedback_synthetic_tests_missed_real_event_shape.md``
warns about applies equally to WhatsApp.

Tests cover:

  1. Populated path — whatsapp + telegram rows seeded; whatsapp route
     returns ONLY the whatsapp rows tagged ``_source='local_store_v3'``.
  2. Empty events table → helper returns None so route defers to legacy
     log/JSONL walker (no ``_source='local_store_v3'`` tag).
  3. ``event_type`` discipline — only ``channel.in`` and ``channel.out``
     project; a stray ``message`` row with ``data.provider='whatsapp'``
     MUST NOT show up.
  4. Time-range / sort — newest-first ordering across the union of
     channel.in + channel.out reads.
"""

from __future__ import annotations

import importlib
import uuid
from datetime import datetime, timedelta, timezone

import pytest
from flask import Flask


def _now_iso():
    return datetime.now(tz=timezone.utc).isoformat()


def _iso_minutes_ago(minutes: int) -> str:
    return (datetime.now(tz=timezone.utc) - timedelta(minutes=minutes)).isoformat()


def _ingest_channel_event(
    store,
    *,
    provider: str,
    direction: str,
    body: str = "hello",
    sender_name: str = "alice",
    channel_id: str = "whatsapp-chat-1",
    ts: str | None = None,
):
    store.ingest({
        "id":         f"ch-{uuid.uuid4().hex[:12]}",
        "node_id":    "node-test",
        "agent_type": "openclaw",
        "agent_id":   "main",
        "event_type": f"channel.{direction}",
        "ts":         ts or _now_iso(),
        "session_id": None,
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

    monkeypatch.setattr(lq, "_read_discovery", lambda: None)

    import dashboard  # noqa: F401

    a = Flask(__name__)
    a.register_blueprint(channels_mod.bp_channels)
    yield a, ls, channels_mod
    try:
        ls.get_store().stop(flush=True)
    except Exception:
        pass


def test_whatsapp_v3_events_path_serves_when_channel_messages_empty(app):
    """Populated v3 events but empty ``channel_messages`` → fast path
    must return ``_source='local_store_v3'`` with only whatsapp rows."""
    a, ls, _c = app
    store = ls.get_store()
    _ingest_channel_event(
        store,
        provider="whatsapp",
        direction="in",
        body="hey from whatsapp",
        sender_name="bob",
        channel_id="whatsapp-chat-1",
    )
    _ingest_channel_event(
        store,
        provider="whatsapp",
        direction="out",
        body="ack",
        channel_id="whatsapp-chat-1",
    )
    # Cross-provider row must NOT pollute the whatsapp response.
    _ingest_channel_event(
        store,
        provider="telegram",
        direction="in",
        body="tg cross-channel",
        sender_name="alice",
    )
    store.flush()
    assert store.query_channel_messages(provider="whatsapp", limit=5) == []

    r = a.test_client().get("/api/channel/whatsapp?limit=10")
    assert r.status_code == 200, r.get_data(as_text=True)
    body = r.get_json()
    assert body.get("_source") == "local_store_v3", (
        f"_source must be local_store_v3 (v3 events fallback); got "
        f"{body.get('_source')!r}"
    )
    msgs = body.get("messages") or []
    assert len(msgs) == 2, f"expected 2 whatsapp rows, got {len(msgs)}: {msgs}"
    inbound = next(m for m in msgs if m["direction"] == "in")
    assert inbound["sender"] == "bob"
    assert inbound["text"] == "hey from whatsapp"
    assert inbound["chatId"] == "whatsapp-chat-1"


def test_whatsapp_v3_events_empty_returns_legacy_fallback(app):
    """Empty events → helper returns None, route falls through to legacy
    walker. The legacy walker on a test box with no log files MUST NOT
    carry the ``_source='local_store_v3'`` audit tag."""
    a, ls, _c = app
    assert ls.get_store().query_events(event_type="channel.in", limit=5) == []
    r = a.test_client().get("/api/channel/whatsapp")
    assert r.status_code == 200
    body = r.get_json()
    assert body.get("_source") != "local_store_v3"


def test_whatsapp_v3_events_ignores_non_channel_event_types(app):
    """Only ``channel.in`` / ``channel.out`` rows project. A v3
    ``message`` row that happens to carry ``data.provider='whatsapp'``
    MUST NOT show up — that would inflate the whatsapp counters with LLM
    turns and re-create the bug class
    ``feedback_synthetic_tests_missed_real_event_shape.md`` warns
    about."""
    a, ls, _c = app
    store = ls.get_store()
    _ingest_channel_event(
        store,
        provider="whatsapp",
        direction="in",
        body="real whatsapp turn",
    )
    # Stray non-channel event with provider tag — should be ignored.
    store.ingest({
        "id":         f"msg-{uuid.uuid4().hex[:12]}",
        "node_id":    "node-test",
        "agent_type": "openclaw",
        "agent_id":   "main",
        "event_type": "message",
        "ts":         _now_iso(),
        "session_id": "sess-llm",
        "workspace_id": None,
        "data": {
            "provider": "whatsapp",
            "body":     "this is an LLM turn that mentions whatsapp",
        },
        "cost_usd": 0.001, "token_count": 100, "model": "claude-3-5-sonnet",
    })
    store.flush()

    r = a.test_client().get("/api/channel/whatsapp?limit=10")
    body = r.get_json()
    assert body.get("_source") == "local_store_v3"
    msgs = body.get("messages") or []
    assert len(msgs) == 1, (
        f"only the channel.in row should surface; got {len(msgs)} rows: "
        f"{[m['text'] for m in msgs]}"
    )
    assert msgs[0]["text"] == "real whatsapp turn"


def test_whatsapp_v3_events_newest_first_across_in_and_out(app):
    """Helper merges separate channel.in + channel.out pulls and MUST
    return newest-first. Guards against the union being returned in
    in-then-out (or out-then-in) chunk order, which would put a fresh
    outbound under a stale inbound on the WhatsApp tab."""
    a, ls, _c = app
    store = ls.get_store()
    # Older inbound — 30 min ago.
    _ingest_channel_event(
        store,
        provider="whatsapp",
        direction="in",
        body="older inbound",
        ts=_iso_minutes_ago(30),
    )
    # Fresher outbound — now.
    _ingest_channel_event(
        store,
        provider="whatsapp",
        direction="out",
        body="fresh outbound",
    )
    store.flush()

    r = a.test_client().get("/api/channel/whatsapp?limit=10")
    body = r.get_json()
    assert body["_source"] == "local_store_v3"
    msgs = body.get("messages") or []
    assert len(msgs) == 2
    # The fresh outbound must come first.
    assert msgs[0]["text"] == "fresh outbound"
    assert msgs[1]["text"] == "older inbound"
