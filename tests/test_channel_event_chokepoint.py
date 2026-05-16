"""Issue #1220 — pin the ``LocalStore.ingest_channel_event`` chokepoint.

Two May 2026 P0 regressions (#1212 telegram→Brain blank channel; #1438
local-store opt-in default OFF) both shared the same root cause: a
writer projected to ONE of the two tables ``channel_messages`` /
``events`` but not the other, and downstream readers that joined them
silently returned empty. This file is the contract test that prevents
the next adapter from re-introducing the bug.

Contract under test:
  * Calling ``ingest_channel_event(channel_msg, node_id=...)`` writes
    BOTH the channel_messages row AND the events row in one shot.
  * The events row carries ``event_type='channel.<direction>'`` so the
    Brain reader's ``CHANNEL.`` prefix filter matches it.
  * The events row carries ``node_id`` + ``agent_type='openclaw'`` so
    multi-node fleet filters work.
  * The full inbound payload (text, sender, chat_id) is preserved in
    the events ``data`` blob so /api/brain-history renders without
    re-reading the channel_messages table.
"""

from __future__ import annotations

import importlib
import time

import pytest
from flask import Flask


@pytest.fixture
def store(tmp_path, monkeypatch):
    monkeypatch.setenv(
        "CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "events.duckdb")
    )
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_SECS", "0.05")
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_BATCH", "5")
    import clawmetry.local_store as ls
    importlib.reload(ls)
    s = ls.get_store()
    yield s
    try:
        s.stop(flush=True)
    except Exception:
        pass


def _wait(store, t: float = 2.0) -> None:
    deadline = time.monotonic() + t
    while time.monotonic() < deadline:
        try:
            if store.health()["ring_depth"] == 0:
                return
        except Exception:
            return
        time.sleep(0.02)


def _telegram_inbound_channel_msg() -> dict:
    """Mirror the real OpenClaw-on-disk shape (post-#1212 reference fixture).

    This is the shape ``sync._parse_channel_event`` returns for a JSONL
    line and that ``gateway_tap._normalize_frame`` returns for a WS
    frame. Both writers funnel through ``ingest_channel_event``.
    """
    return {
        "id": "telegram:1532693273:9001",
        "agent_id": "main",
        "provider": "telegram",
        "channel_id": "1532693273",
        "sender_id": "42",
        "sender_name": "diya",
        "body": "hello from diya",
        "ts": "2026-05-14T09:00:00+00:00",
        "direction": "in",
        "session_key": None,
        "raw_blob": {
            "provider": "telegram",
            "chat_id": 1532693273,
            "message_id": 9001,
            "ts": "2026-05-14T09:00:00+00:00",
            "text": "hello from diya",
            "from": {"id": 42, "username": "diya", "first_name": "Diya"},
            "_clawmetry_source": "gateway.ws",
        },
    }


# ── 1. Both tables get populated by a single call ────────────────────────


def test_ingest_channel_event_writes_both_tables(store):
    """The single chokepoint MUST land rows in channel_messages AND
    events. This is the precise contract that #1212 added by hand and
    #1220 made structural."""
    store.ingest_channel_event(
        _telegram_inbound_channel_msg(), node_id="test-node",
    )
    _wait(store)
    store._flush_now()

    # channel_messages — the per-channel detail view reads this.
    chm = store._conn.execute(
        "SELECT id, provider, channel_id, direction, body, sender_name "
        "FROM channel_messages WHERE id = ?",
        ["telegram:1532693273:9001"],
    ).fetchall()
    assert chm == [(
        "telegram:1532693273:9001", "telegram", "1532693273",
        "in", "hello from diya", "diya",
    )]

    # events — the Brain feed reads this. event_type MUST start with
    # ``channel.`` (the Brain reader UPPER()s + prefix-matches).
    ev = store._conn.execute(
        "SELECT id, event_type, node_id, agent_type, agent_id, "
        "       session_id, cost_usd, token_count "
        "FROM events WHERE id = ?",
        ["telegram:1532693273:9001"],
    ).fetchall()
    assert ev == [(
        "telegram:1532693273:9001", "channel.in", "test-node",
        "openclaw", "main", None, None, None,
    )]


def test_ingest_channel_event_outbound_direction(store):
    """Outbound (gateway.log telegram path) maps to event_type=channel.out."""
    msg = _telegram_inbound_channel_msg()
    msg["id"] = "telegram:1532693273:8491"
    msg["direction"] = "out"
    msg["body"] = None  # gateway.log only has the ACK, no body
    msg["raw_blob"] = {
        "source": "gateway.log",
        "method": "sendMessage",
        "chat_id": "1532693273",
        "message_id": "8491",
        "body_capture": "ack_only",
    }
    store.ingest_channel_event(msg, node_id="local")
    _wait(store)
    store._flush_now()

    ev_type = store._conn.execute(
        "SELECT event_type FROM events WHERE id = ?",
        ["telegram:1532693273:8491"],
    ).fetchone()
    assert ev_type == ("channel.out",)


def test_ingest_channel_event_is_idempotent(store):
    """Re-ingesting the same upstream id is a no-op on both tables
    (PRIMARY KEY + INSERT OR IGNORE). The daemon scans logs every
    cycle so idempotency is essential to avoid duplicate Brain rows."""
    msg = _telegram_inbound_channel_msg()
    store.ingest_channel_event(msg, node_id="n1")
    store.ingest_channel_event(msg, node_id="n1")
    store.ingest_channel_event(msg, node_id="n1")
    _wait(store)
    store._flush_now()

    chm_count = store._conn.execute(
        "SELECT COUNT(*) FROM channel_messages WHERE id = ?",
        ["telegram:1532693273:9001"],
    ).fetchone()[0]
    ev_count = store._conn.execute(
        "SELECT COUNT(*) FROM events WHERE id = ?",
        ["telegram:1532693273:9001"],
    ).fetchone()[0]
    assert chm_count == 1
    assert ev_count == 1


# ── 2. End-to-end: chokepoint → /api/brain-history ───────────────────────


def test_brain_history_surfaces_chokepoint_row(tmp_path, monkeypatch):
    """The original P0 regression: telegram outbound landed in
    channel_messages but NOT events, so /api/brain-history was blank.
    This test pins the full chokepoint → Brain feed path."""
    monkeypatch.setenv(
        "CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "events.duckdb")
    )
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_SECS", "0.05")
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_BATCH", "5")
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_READ", "1")

    import clawmetry.local_store as ls
    importlib.reload(ls)
    s = ls.get_store()
    try:
        s.ingest_channel_event(
            _telegram_inbound_channel_msg(), node_id="brain-test",
        )
        _wait(s)
        s._flush_now()

        # Hit /api/brain-history through a real Flask test client.
        import routes.brain as brain
        importlib.reload(brain)
        # PR #1481 added a 24h retention cap for non-Pro users. The seeded
        # channel msg has a 2026-05-14 ts (older than 24h) which the cap
        # would correctly drop. This test is about the chokepoint write
        # path, not the cap — bypass via Pro stub. Mirrors the fixture
        # pattern PR #1481 added to test_brain_local_fastpath.py.
        import dashboard as _d
        monkeypatch.setattr(_d, "_is_pro_user", lambda: True)
        app = Flask(__name__)
        app.register_blueprint(brain.bp_brain)
        client = app.test_client()

        r = client.get("/api/brain-history?limit=20")
        assert r.status_code == 200
        body = r.get_json()
        # The events list contains our channel row, surfaced with the
        # ``CHANNEL.IN`` type the Brain JS filters on.
        kinds = [(ev.get("type"), ev.get("direction")) for ev in body["events"]]
        assert ("CHANNEL.IN", "in") in kinds
    finally:
        try:
            s.stop(flush=True)
        except Exception:
            pass
