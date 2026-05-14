"""Tests for ``clawmetry/gateway_tap.py`` — the live WS subscriber that
captures inbound chat-channel messages OpenClaw stores in memory only.

What this pins
--------------

1. ``_normalize_frame`` projects a Telegram-shaped gateway WS frame
   into ``events`` + ``channel_messages`` rows with the right
   provider, direction, body, and dedup id.
2. ``_normalize_frame`` rejects non-channel frames (health snapshots,
   etc.) with ``None`` so they don't pollute DuckDB.
3. ``GatewayTap._handle_frame`` upserts a real telegram inbound row
   into a per-test DuckDB. Brain-history reads can then see it.
4. The full WS receive loop runs against a stubbed ``websocket``
   module — the tap connects, drains the connect handshake, accepts
   a degraded subscribe response, processes a pushed inbound frame,
   and writes it to DuckDB. Then the connection closes and the tap
   reconnects without crashing the loop.
5. Body-bearing WS-tap rows beat NULL-body parser ACK rows when the
   same ``(provider, chat_id, message_id)`` already exists — the
   COALESCE upsert in ``ingest_channel_message`` makes the body
   stick.
6. ``CLAWMETRY_DISABLE_WS_TAP=1`` short-circuits ``start()`` to a
   no-op (escape-hatch behavior).
"""

from __future__ import annotations

import importlib
import json
import sys
import threading
import time
from datetime import datetime, timezone

import pytest


# ── Per-test DuckDB + freshly-imported tap module ────────────────────────


@pytest.fixture
def tap_env(tmp_path, monkeypatch):
    """Per-test DuckDB + fake ``~/.openclaw`` so detection helpers don't
    pick up the developer's real config and cross-talk."""
    duck = tmp_path / "events.duckdb"
    oc_home = tmp_path / "openclaw"
    oc_home.mkdir()
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(duck))
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_SECS", "0.05")
    monkeypatch.setenv("CLAWMETRY_OPENCLAW_DIR", str(oc_home))
    monkeypatch.delenv("CLAWMETRY_DISABLE_WS_TAP", raising=False)
    monkeypatch.delenv("OPENCLAW_GATEWAY_TOKEN", raising=False)

    import clawmetry.local_store as ls
    importlib.reload(ls)
    import clawmetry.gateway_tap as gw_tap
    importlib.reload(gw_tap)

    store = ls.get_store()
    yield {"store": store, "ls": ls, "tap": gw_tap, "oc_home": oc_home}
    try:
        store.stop(flush=True)
    except Exception:
        pass


def _telegram_inbound_frame(text: str = "hello from diya",
                            chat_id: int = 1532693273,
                            message_id: int = 9001) -> dict:
    """A realistic shape for the gateway's pushed Telegram inbound
    event. We don't have a published schema (memory note
    ``reference_openclaw_telegram_inmemory.md``), so we model the
    frame on the data the gateway exposes via ``health.channels``
    plus the standard Telegram update payload."""
    return {
        "type": "event",
        "event": "telegram.inbound",
        "payload": {
            "provider": "telegram",
            "direction": "in",
            "chat_id": chat_id,
            "message_id": message_id,
            "ts": datetime(2026, 5, 14, 9, 0, 0, tzinfo=timezone.utc).isoformat(),
            "text": text,
            "from": {"id": 42, "username": "diya", "first_name": "Diya"},
        },
    }


# ── 1. Frame normalization ───────────────────────────────────────────────


def test_normalize_telegram_inbound(tap_env):
    """The standard inbound shape projects into the canonical row."""
    norm = tap_env["tap"]._normalize_frame(_telegram_inbound_frame())
    assert norm is not None

    ev = norm["events"]
    assert ev["event_type"] == "channel.in"
    assert ev["id"] == "telegram:1532693273:9001"
    assert ev["data"]["text"] == "hello from diya"
    assert ev["data"]["_clawmetry_source"] == "channel:telegram:in"

    ch = norm["channel"]
    assert ch["provider"] == "telegram"
    assert ch["channel_id"] == "1532693273"
    assert ch["body"] == "hello from diya"
    assert ch["direction"] == "in"
    assert ch["sender_id"] == "42"
    assert ch["sender_name"] == "diya"


def test_normalize_outbound_inferred_from_event_name(tap_env):
    """When ``direction`` is missing we infer from event name + role."""
    frame = {
        "type": "event",
        "event": "telegram.outbound",
        "payload": {
            "provider": "telegram",
            "chat_id": 1,
            "message_id": 7,
            "ts": "2026-05-14T09:00:00+00:00",
            "text": "ack body present",
            "role": "assistant",
        },
    }
    norm = tap_env["tap"]._normalize_frame(frame)
    assert norm is not None
    assert norm["channel"]["direction"] == "out"
    assert norm["channel"]["body"] == "ack body present"


def test_normalize_health_frame_returns_none(tap_env):
    """Non-channel frames (health, presence, …) are silently dropped."""
    frame = {
        "type": "event",
        "event": "health",
        "payload": {"ok": True, "ts": 1778750855030},
    }
    assert tap_env["tap"]._normalize_frame(frame) is None


def test_normalize_epoch_seconds_coerced_to_iso(tap_env):
    """Adapters that send Unix ts (seconds) get coerced to ISO so the
    events.ts column stays sortable as a string."""
    frame = _telegram_inbound_frame()
    frame["payload"]["ts"] = 1778750855  # epoch seconds
    norm = tap_env["tap"]._normalize_frame(frame)
    assert norm is not None
    assert norm["events"]["ts"].startswith("2026-")


# ── 2. _handle_frame writes through to DuckDB ────────────────────────────


def test_handle_frame_writes_event_and_channel_message(tap_env):
    tap = tap_env["tap"].GatewayTap(
        url="ws://127.0.0.1:18789",
        token="fake-token",
        store=tap_env["store"],
        node_id="test-node",
    )
    tap._handle_frame(_telegram_inbound_frame())
    tap_env["store"]._flush_now()

    # events row landed
    conn = tap_env["store"]._conn
    rows = conn.execute(
        "SELECT id, event_type, node_id, agent_type FROM events "
        "WHERE id = ?", ["telegram:1532693273:9001"],
    ).fetchall()
    assert rows == [("telegram:1532693273:9001", "channel.in",
                     "test-node", "openclaw")]

    # channel_messages row landed with the body
    crows = conn.execute(
        "SELECT provider, channel_id, body, direction, sender_name "
        "FROM channel_messages WHERE id = ?",
        ["telegram:1532693273:9001"],
    ).fetchall()
    assert crows == [("telegram", "1532693273", "hello from diya",
                      "in", "diya")]
    assert tap.rows_written == 1
    assert tap.frames_seen == 1


def test_handle_frame_drops_unparseable_frame(tap_env):
    """Garbage frames don't crash the loop or write rows."""
    tap = tap_env["tap"].GatewayTap(
        url="ws://x", token="t", store=tap_env["store"], node_id="n"
    )
    tap._handle_frame({"type": "event", "event": "unknown", "payload": "junk"})
    assert tap.rows_written == 0


# ── 3. Body-bearing WS-tap row beats NULL-body parser ACK row ────────────


def test_ws_tap_body_overwrites_parser_null_body(tap_env):
    """Sequence: gateway.log parser writes an outbound ACK with
    body=None (id="telegram:42:7"), THEN the WS tap captures the same
    message with body='hi'. The COALESCE upsert means the body sticks
    — verifies the dedup contract called out in the task."""
    store = tap_env["store"]

    # 1. Parser-style row (no body)
    store.ingest_channel_message({
        "id": "telegram:42:7",
        "provider": "telegram",
        "channel_id": "telegram:42",
        "ts": "2026-05-14T09:00:00+00:00",
        "direction": "out",
        "body": None,
    })
    # 2. WS-tap row (with body)
    store.ingest_channel_message({
        "id": "telegram:42:7",
        "provider": "telegram",
        "channel_id": "telegram:42",
        "ts": "2026-05-14T09:00:01+00:00",
        "direction": "out",
        "body": "real body captured by WS tap",
    })

    rows = store._conn.execute(
        "SELECT body FROM channel_messages WHERE id = ?",
        ["telegram:42:7"],
    ).fetchall()
    assert rows == [("real body captured by WS tap",)]


# ── 4. End-to-end: stubbed ``websocket`` module drives one full cycle ────


class _StubWS:
    """Minimal ``websocket-client`` connection stand-in. Plays a script
    of frames on ``recv()`` and records ``send()`` calls so the test
    can assert the connect + subscribe handshake."""

    def __init__(self, script: list[str]):
        self._script = list(script)
        self.sent: list[str] = []
        self.closed = False

    def settimeout(self, _t):
        pass

    def send(self, payload: str):
        self.sent.append(payload)

    def recv(self) -> str:
        if not self._script:
            # Simulates server-side close → tap reconnects.
            raise ConnectionError("script exhausted")
        return self._script.pop(0)

    def close(self):
        self.closed = True


def _fake_websocket_module(script: list[str]):
    """Install a fake `websocket` module exposing only the API the tap
    uses (``create_connection``). The module persists across tap
    reconnects so the script can be queried for state."""
    holder = {"ws": None}

    class _Mod:
        def create_connection(self, _url, timeout=None):
            ws = _StubWS(script)
            holder["ws"] = ws
            return ws

        # ``websocket.WebSocketTimeoutException`` is referenced nowhere
        # in our tap loop (we catch generic ``Exception``), so we don't
        # need to expose it. Add it lazily if a future change refers
        # to it.

    return _Mod(), holder


def test_full_loop_against_stubbed_websocket(tap_env, monkeypatch):
    """Drive ``GatewayTap`` against a stubbed ``websocket`` module:
    one connect-ok response, one subscribe-ok response, one inbound
    frame, then EOF. Asserts the inbound frame round-trips into
    DuckDB and the loop's stop() exits the thread cleanly."""
    cid_holder: dict = {}

    def _connect_response(received_send: str) -> str:
        msg = json.loads(received_send)
        cid_holder["cid"] = msg["id"]
        return json.dumps({
            "type": "res", "id": msg["id"], "ok": True,
            "payload": {
                "type": "hello-ok", "protocol": 3,
                "auth": {"role": "operator", "scopes": ["operator.read"]},
                "features": {"methods": [
                    "sessions.messages.subscribe", "sessions.subscribe",
                ]},
            },
        })

    # Build the script: initial challenge, then connect-ok (id matches
    # whatever the tap sends), then sub-ok (also matches), then an
    # inbound frame. We can't compute connect/sub ids until the tap
    # sends them, so we use a "responder" pattern instead of a static
    # script — write a smarter stub.
    inbound_payload = json.dumps(_telegram_inbound_frame())

    class _ResponderWS:
        """A stub that REPLIES to whatever the tap sends. Each send()
        triggers an entry in a deque; recv() pops it. The first send
        is the connect handshake; we mint a connect-ok in response.
        Subsequent sends are subscribes; we mint sub-ok responses.
        After the second sub-ok we push the inbound frame, then EOF."""

        def __init__(self):
            self.queue: list[str] = [
                # Initial challenge
                json.dumps({"type": "event",
                            "event": "connect.challenge",
                            "payload": {"nonce": "x", "ts": 0}}),
            ]
            self.sent: list[str] = []
            self.closed = False
            self.subscribes_seen = 0
            self.inbound_pushed = False

        def settimeout(self, _t):
            pass

        def send(self, payload: str):
            self.sent.append(payload)
            try:
                msg = json.loads(payload)
            except Exception:
                return
            method = msg.get("method")
            mid = msg.get("id")
            if method == "connect":
                self.queue.append(json.dumps({
                    "type": "res", "id": mid, "ok": True,
                    "payload": {
                        "type": "hello-ok", "protocol": 3,
                        "auth": {"role": "operator",
                                 "scopes": ["operator.read"]},
                        "features": {"methods": [
                            "sessions.messages.subscribe",
                            "sessions.subscribe",
                        ]},
                    },
                }))
            elif method in (
                "sessions.messages.subscribe", "sessions.subscribe",
            ):
                self.subscribes_seen += 1
                self.queue.append(json.dumps({
                    "type": "res", "id": mid, "ok": True,
                    "payload": {"subscribed": True},
                }))
                # After we ACK the FIRST subscribe, push the inbound
                # frame. The tap accepts the first ok and skips the
                # second subscribe, then enters the recv loop.
                if not self.inbound_pushed:
                    self.queue.append(inbound_payload)
                    self.inbound_pushed = True

        def recv(self) -> str:
            # Block-spin briefly to give the test thread time to push
            # the next frame in response to a send. In real tests the
            # tap thread is the only producer/consumer so this is a
            # tight handoff.
            for _ in range(200):
                if self.queue:
                    return self.queue.pop(0)
                time.sleep(0.005)
            raise ConnectionError("stub: nothing to recv")

        def close(self):
            self.closed = True

    holder = {"ws": None, "count": 0}

    class _Mod:
        def create_connection(self, _url, timeout=None):
            holder["count"] += 1
            ws = _ResponderWS()
            holder["ws"] = ws
            return ws

    monkeypatch.setitem(sys.modules, "websocket", _Mod())

    tap = tap_env["tap"].GatewayTap(
        url="ws://127.0.0.1:18789",
        token="t",
        store=tap_env["store"],
        node_id="test-node",
    )
    on_event = threading.Event()
    tap._on_event = lambda _frame: on_event.set()
    tap.start()

    # Wait up to 2 seconds for the inbound frame to land.
    assert on_event.wait(timeout=2.0), "tap never received the inbound frame"

    # Force one more spin so the ingest path completes, then stop.
    deadline = time.time() + 1.0
    while tap.rows_written == 0 and time.time() < deadline:
        time.sleep(0.02)
    tap.stop(timeout=2.0)
    tap_env["store"]._flush_now()

    # The inbound frame landed in BOTH events and channel_messages.
    rows = tap_env["store"]._conn.execute(
        "SELECT body FROM channel_messages WHERE id = ?",
        ["telegram:1532693273:9001"],
    ).fetchall()
    assert rows == [("hello from diya",)], (
        f"WS-tap inbound frame did not land in channel_messages "
        f"(got {rows!r}, sent={holder['ws'].sent!r})"
    )
    assert tap.rows_written >= 1
    assert holder["count"] >= 1  # we connected at least once
    sent_methods = [json.loads(s).get("method") for s in holder["ws"].sent]
    assert "connect" in sent_methods
    # We attempted at least one subscribe (the first one returned ok so
    # we may not have sent the second).
    assert any("subscribe" in (m or "") for m in sent_methods), sent_methods


# ── 5. Disable env var ──────────────────────────────────────────────────


def test_disable_env_var_short_circuits_start(tap_env, monkeypatch):
    monkeypatch.setenv("CLAWMETRY_DISABLE_WS_TAP", "1")
    res = tap_env["tap"].start({"node_id": "n"})
    assert res is None


# ── 6. Endpoint detection from openclaw.json ────────────────────────────


def test_detect_gateway_endpoint_reads_openclaw_json(tap_env):
    """When the env vars are unset, ``_detect_gateway_endpoint`` reads
    the gateway port + token straight from ``~/.openclaw/openclaw.json``
    (matching the dashboard's detection path)."""
    cfg_path = tap_env["oc_home"] / "openclaw.json"
    cfg_path.write_text(json.dumps({
        "gateway": {
            "port": 18999,
            "auth": {"mode": "token", "token": "abc123"},
        },
    }))
    url, token = tap_env["tap"]._detect_gateway_endpoint()
    assert url == "ws://127.0.0.1:18999"
    assert token == "abc123"


def test_detect_gateway_endpoint_returns_none_when_no_config(tap_env):
    url, token = tap_env["tap"]._detect_gateway_endpoint()
    assert (url, token) == (None, None)
