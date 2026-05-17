"""Regression guard for the /api/channel/bluebubbles DuckDB v3 events fast
path (Tier-1 #1565, refs #1583's coverage audit + PR #1585's
telegram/signal precedent).

``routes/channels.py:_try_local_store_channel_events`` is layered AFTER
``_try_local_store_provider_messages`` (which reads the specialised
``channel_messages`` table). When the dedicated table is empty but the
unified ``events`` table has ``channel.in`` / ``channel.out`` rows the
sync daemon already wrote, this helper still serves DuckDB-first instead
of falling through to the legacy BlueBubbles REST probe + log-grep.

Why this matters for BlueBubbles specifically:

  * BlueBubbles is in ``sync._CHANNEL_DIRS`` so the daemon ingests
    ``~/.openclaw/bluebubbles/*.jsonl`` into both tables via the
    ``LocalStore.ingest_channel_event`` chokepoint (clawmetry/
    local_store.py:1177-1265).
  * The legacy route hits a third-party BlueBubbles REST API with a 3s
    timeout — on a misconfigured / unreachable BB server every dashboard
    poll silently paid that 3s tax. The fast path skips it entirely
    when DuckDB has rows.
  * Same silent-zero bug class as memory
    ``feedback_synthetic_tests_missed_real_event_shape.md``: a synthetic
    test against the specialised table passes while real OpenClaw v3
    data lives only in ``events``.

Tests cover:

  1. Populated v3 events → fast path returns
     ``_source='local_store_v3'`` with only bluebubbles rows and the
     legacy ``{messages,total,todayIn,todayOut,chatCount,status}``
     envelope.
  2. Empty events table → helper returns ``None`` so the route falls
     through to the BB REST + log-grep walker (which on a test box with
     no config still returns 200 but MUST NOT carry the
     ``_source='local_store_v3'`` audit tag).
  3. ``event_type`` discipline — only ``channel.in`` / ``channel.out``
     project. A stray ``message`` row with ``data.provider='bluebubbles'``
     MUST NOT show up (that bug class would inflate counters with LLM
     turns that happen to mention the provider in their data blob).
  4. Time-range / today counters honour the daemon's ISO ts strings —
     guards against the loose substring match the 2026-05-17 audit
     flagged in a peer route.
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
    channel_id: str = "iMessage;-;+15551234567",
    ts: str | None = None,
    session_id: str | None = None,
):
    """Seed one channel event row in the exact shape
    ``LocalStore.ingest_channel_event`` would write (see
    clawmetry/local_store.py:1250-1264).

    We bypass the chokepoint here and call ``ingest`` directly so the
    test actually exercises the silent-zero contract: events-table
    populated, channel_messages table EMPTY — the very case the v3
    fallback exists for."""
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

    # Isolate from a contributor's running daemon: without this,
    # ``_ls_call`` proxies through ``~/.clawmetry/local_query.json`` and
    # the daemon queries its OWN production DuckDB instead of our
    # tmp_path fixture.
    monkeypatch.setattr(lq, "_read_discovery", lambda: None)

    import dashboard  # noqa: F401

    a = Flask(__name__)
    a.register_blueprint(channels_mod.bp_channels)
    yield a, ls, channels_mod
    try:
        ls.get_store().stop(flush=True)
    except Exception:
        pass


def test_bluebubbles_v3_events_path_serves_when_channel_messages_empty(app):
    """Populated v3 events but empty ``channel_messages`` → fast path
    must return ``_source='local_store_v3'`` with only bluebubbles rows
    and the legacy envelope keys (chatCount/status) defaulted for UI
    compatibility."""
    a, ls, _c = app
    store = ls.get_store()
    _ingest_channel_event(
        store,
        provider="bluebubbles",
        direction="in",
        body="hey from imessage",
        sender_name="bob",
        channel_id="iMessage;-;+15551234567",
    )
    _ingest_channel_event(
        store,
        provider="bluebubbles",
        direction="out",
        body="ack from clawd",
        channel_id="iMessage;-;+15551234567",
    )
    # Cross-provider row must NOT pollute the bluebubbles response.
    _ingest_channel_event(
        store,
        provider="telegram",
        direction="in",
        body="tg cross-channel",
        sender_name="alice",
    )
    store.flush()
    # Contract check: events table populated, channel_messages NOT —
    # this is the silent-zero contract the v3 fallback exists for.
    assert len(store.query_events(event_type="channel.in", limit=5)) >= 1
    assert len(store.query_events(event_type="channel.out", limit=5)) >= 1
    assert store.query_channel_messages(provider="bluebubbles", limit=5) == []

    r = a.test_client().get("/api/channel/bluebubbles?limit=10")
    assert r.status_code == 200, r.get_data(as_text=True)
    body = r.get_json()
    assert body.get("_source") == "local_store_v3", (
        f"_source must be local_store_v3 (v3 events fallback); got "
        f"{body.get('_source')!r}"
    )
    msgs = body.get("messages") or []
    assert len(msgs) == 2, (
        f"expected 2 bluebubbles rows, got {len(msgs)}: "
        f"{[m['text'] for m in msgs]}"
    )
    directions = sorted(m["direction"] for m in msgs)
    assert directions == ["in", "out"]
    inbound = next(m for m in msgs if m["direction"] == "in")
    assert inbound["sender"] == "bob"
    assert inbound["text"] == "hey from imessage"
    assert inbound["chatId"] == "iMessage;-;+15551234567"
    # Legacy envelope keys preserved so the UI doesn't need a v3-aware
    # render path. ``chatCount`` is None because the v3 fast path can't
    # talk to the BB server; ``status`` records which DuckDB tier served.
    assert "chatCount" in body
    assert body["chatCount"] is None
    assert body.get("status") == "local_store_v3"


def test_bluebubbles_v3_events_empty_returns_legacy_fallback(app):
    """Empty events → helper returns ``None`` so the route falls through
    to the BB REST + log-grep walker. The walker on a test box with no
    BB config / no log files MUST NOT carry the
    ``_source='local_store_v3'`` audit tag — that would let the v3
    coverage canary report a false positive."""
    a, ls, _c = app
    assert ls.get_store().query_events(event_type="channel.in", limit=5) == []
    assert ls.get_store().query_events(event_type="channel.out", limit=5) == []

    r = a.test_client().get("/api/channel/bluebubbles")
    assert r.status_code == 200
    body = r.get_json()
    assert body.get("_source") != "local_store_v3", (
        "empty events → fast path must defer to legacy walker; got "
        f"_source={body.get('_source')!r}"
    )


def test_bluebubbles_v3_events_ignores_non_channel_event_types(app):
    """Only ``channel.in`` / ``channel.out`` rows project. A v3
    ``message`` row that happens to carry ``data.provider='bluebubbles'``
    MUST NOT show up — that would inflate the bluebubbles counters with
    LLM turns and re-create the bug class
    ``feedback_synthetic_tests_missed_real_event_shape.md`` warns about.

    This guards against a future helper change that loosens the
    ``event_type`` filter (e.g. by switching to a ``provider``-keyed
    query and forgetting the ``channel.`` prefix)."""
    a, ls, _c = app
    store = ls.get_store()
    _ingest_channel_event(
        store,
        provider="bluebubbles",
        direction="in",
        body="real bluebubbles turn",
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
            "provider": "bluebubbles",
            "body":     "this is an LLM turn that mentions bluebubbles",
        },
        "cost_usd": 0.001, "token_count": 100, "model": "claude-3-5-sonnet",
    })
    # And the modern v3 ``model.completed`` name — same hazard.
    store.ingest({
        "id":         f"mc-{uuid.uuid4().hex[:12]}",
        "node_id":    "node-test",
        "agent_type": "openclaw",
        "agent_id":   "main",
        "event_type": "model.completed",
        "ts":         _now_iso(),
        "session_id": "sess-llm",
        "workspace_id": None,
        "data": {
            "provider": "bluebubbles",
            "body":     "another LLM turn",
        },
        "cost_usd": 0.002, "token_count": 200, "model": "claude-3-5-sonnet",
    })
    store.flush()

    r = a.test_client().get("/api/channel/bluebubbles?limit=10")
    body = r.get_json()
    assert body.get("_source") == "local_store_v3"
    msgs = body.get("messages") or []
    assert len(msgs) == 1, (
        f"only the channel.in row should surface; got {len(msgs)} rows: "
        f"{[m['text'] for m in msgs]}"
    )
    assert msgs[0]["text"] == "real bluebubbles turn"


def test_bluebubbles_v3_events_newest_first_across_in_and_out(app):
    """Helper merges separate ``channel.in`` + ``channel.out`` pulls and
    MUST return newest-first across the union. Guards against the union
    being returned in in-then-out (or out-then-in) chunk order, which
    would put a fresh outbound under a stale inbound on the BlueBubbles
    tab."""
    a, ls, _c = app
    store = ls.get_store()
    # Older inbound — 30 min ago.
    _ingest_channel_event(
        store,
        provider="bluebubbles",
        direction="in",
        body="older inbound",
        ts=_iso_minutes_ago(30),
    )
    # Fresher outbound — now.
    _ingest_channel_event(
        store,
        provider="bluebubbles",
        direction="out",
        body="fresh outbound",
    )
    # Also seed a stale-2024 row to confirm today-counters use the
    # YYYY-MM-DD ISO prefix and don't inflate.
    _ingest_channel_event(
        store,
        provider="bluebubbles",
        direction="in",
        body="ancient row",
        ts="2024-01-01T08:30:00+00:00",
    )
    store.flush()

    r = a.test_client().get("/api/channel/bluebubbles?limit=10")
    body = r.get_json()
    assert body["_source"] == "local_store_v3"
    msgs = body.get("messages") or []
    assert len(msgs) == 3
    # Fresh outbound must come first (newest-first across the union).
    assert msgs[0]["text"] == "fresh outbound"
    assert msgs[1]["text"] == "older inbound"
    assert msgs[2]["text"] == "ancient row"
    # Today counters: 1 inbound today, 1 outbound today, the 2024 row
    # MUST NOT count.
    assert body["todayIn"] == 1, (
        f"only 1 inbound row carries today's date prefix; got todayIn="
        f"{body['todayIn']}"
    )
    assert body["todayOut"] == 1
