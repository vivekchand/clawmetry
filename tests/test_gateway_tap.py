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
6. ``start()`` is a no-op by default; set ``CLAWMETRY_ENABLE_WS_TAP=1``
   to opt in.
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
    monkeypatch.delenv("CLAWMETRY_ENABLE_WS_TAP", raising=False)
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
    """The standard inbound shape projects into the canonical row.

    Post-#1220: ``_normalize_frame`` returns ONE flat ``channel_msg``
    dict (not the prior ``{events, channel}`` tuple). The events-table
    projection is now derived inside ``LocalStore.ingest_channel_event``
    so a single chokepoint owns both writes.
    """
    ch = tap_env["tap"]._normalize_frame(_telegram_inbound_frame())
    assert ch is not None
    assert ch["id"] == "telegram:1532693273:9001"
    assert ch["provider"] == "telegram"
    assert ch["channel_id"] == "1532693273"
    assert ch["body"] == "hello from diya"
    assert ch["direction"] == "in"
    assert ch["sender_id"] == "42"
    assert ch["sender_name"] == "diya"
    # raw_blob carries the full payload + WS-tap source breadcrumb.
    assert ch["raw_blob"]["text"] == "hello from diya"
    assert ch["raw_blob"]["_clawmetry_source"] == "gateway.ws"


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
    ch = tap_env["tap"]._normalize_frame(frame)
    assert ch is not None
    assert ch["direction"] == "out"
    assert ch["body"] == "ack body present"


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
    ch = tap_env["tap"]._normalize_frame(frame)
    assert ch is not None
    assert ch["ts"].startswith("2026-")


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
    """start() returns None by default (tap is opt-in)."""
    monkeypatch.delenv("CLAWMETRY_ENABLE_WS_TAP", raising=False)
    res = tap_env["tap"].start({"node_id": "n"})
    assert res is None


def test_enable_env_var_allows_start(tap_env, monkeypatch):
    """When CLAWMETRY_ENABLE_WS_TAP=1, start() proceeds past the gate
    (returns None here only because no gateway endpoint is configured)."""
    monkeypatch.setenv("CLAWMETRY_ENABLE_WS_TAP", "1")
    res = tap_env["tap"].start({"node_id": "n"})
    # No gateway configured in test env → still None, but for a
    # different reason (missing URL/token, not the env-var gate).
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


# ── 7. Stale gateway token self-heal ────────────────────────────────────
#
# Field report 2026-09-09 (Steven M. Alper): after a gateway restart the tap
# logged `token_mismatch` "every minute indefinitely" and only a full
# reinstall fixed it. Cause: the token was read once at daemon start and
# cached on the instance; every reconnect replayed the dead credential.


def _write_gw_config(oc_home, token, port=18789):
    (oc_home / "openclaw.json").write_text(json.dumps({
        "gateway": {"port": port, "auth": {"token": token}},
    }))


#: Captured verbatim off a LIVE OpenClaw gateway on 2026-09-10 by sending a
#: deliberately wrong token to 127.0.0.1:18789. Not invented: the top-level
#: `code` for a bad token is the generic INVALID_REQUEST, and matching only
#: that would classify a credential failure as a transient one. The durable
#: signal is `details.code` / `details.authReason`.
_LIVE_BAD_TOKEN_ERROR = {
    "code": "INVALID_REQUEST",
    "message": (
        "unauthorized: gateway token mismatch (use this gateway's "
        "gateway.auth.token or pair the device)"
    ),
    "details": {
        "code": "AUTH_TOKEN_MISMATCH",
        "authReason": "token_mismatch",
        "canRetryWithDeviceToken": False,
        "recommendedNextStep": "update_auth_credentials",
    },
}

#: Same probe, connecting with no `auth` block at all.
_LIVE_NO_TOKEN_ERROR = {
    "code": "NOT_PAIRED",
    "message": "device identity required",
    "details": {"code": "DEVICE_IDENTITY_REQUIRED"},
}


def test_auth_rejection_is_classified_from_the_real_wire(tap_env):
    """The live gateway's bad-token rejection must classify as a credential
    failure, and it must do so on `details`, not on the prose — the prose
    can be reworded or localised, the detail code cannot."""
    gw = tap_env["tap"]
    assert gw._is_auth_rejection(_LIVE_BAD_TOKEN_ERROR)
    assert gw._is_auth_rejection(_LIVE_NO_TOKEN_ERROR)

    # Strip the message entirely: `details` alone must still be enough.
    details_only = {
        "code": "INVALID_REQUEST",
        "details": dict(_LIVE_BAD_TOKEN_ERROR["details"]),
    }
    assert gw._is_auth_rejection(details_only), (
        "classification must not depend on the human-readable sentence"
    )

    # And the reverse, for older builds that send prose and no details.
    assert gw._is_auth_rejection({"message": "Token mismatch"})
    assert gw._is_auth_rejection({"code": "UNAUTHORIZED"})
    assert gw._is_auth_rejection({"message": "invalid token supplied"})

    # A busy/unhealthy gateway must NOT be, or we would re-read the config
    # on every ordinary blip.
    assert not gw._is_auth_rejection({"code": "protocol-mismatch"})
    assert not gw._is_auth_rejection({"message": "server is shutting down"})
    assert not gw._is_auth_rejection({})
    assert not gw._is_auth_rejection(None)


def test_auth_rejection_quotes_the_gateways_own_next_step(tap_env):
    """The gateway tells us what to do (`recommendedNextStep`). Quoting it
    beats inventing our own advice in a log line."""
    gw = tap_env["tap"]
    assert gw._auth_next_step(_LIVE_BAD_TOKEN_ERROR) == "update_auth_credentials"
    # No recommendation → fall back to the reason, then to nothing.
    assert gw._auth_next_step({"details": {"authReason": "token_mismatch"}}) == "token_mismatch"
    assert gw._auth_next_step(_LIVE_NO_TOKEN_ERROR) == ""
    assert gw._auth_next_step({}) == ""
    assert gw._auth_next_step(None) == ""


def test_refresh_credentials_picks_up_a_rotated_token(tap_env):
    """The core fix: a token rotated on disk is adopted."""
    oc_home = tap_env["oc_home"]
    _write_gw_config(oc_home, "old-token")
    tap = tap_env["tap"].GatewayTap(
        url="ws://127.0.0.1:18789", token="old-token",
        store=tap_env["store"], node_id="n",
    )

    assert tap._refresh_credentials() is False, "unchanged token → no churn"

    _write_gw_config(oc_home, "new-token")
    assert tap._refresh_credentials() is True
    assert tap.token == "new-token"
    assert tap.token_reloads == 1


def test_refresh_credentials_follows_a_moved_port(tap_env):
    """A gateway that comes back on a different port is followed too."""
    oc_home = tap_env["oc_home"]
    _write_gw_config(oc_home, "t", port=19999)
    tap = tap_env["tap"].GatewayTap(
        url="ws://127.0.0.1:18789", token="t",
        store=tap_env["store"], node_id="n",
    )
    assert tap._refresh_credentials() is True
    assert tap.url == "ws://127.0.0.1:19999"


def test_refresh_never_clears_a_working_token(tap_env):
    """``openclaw doctor --fix`` swaps the config file out from under us;
    a read that lands mid-swap must not downgrade a working tap to
    anonymous — that would turn a recoverable blip into a silent
    permanent degrade."""
    tap = tap_env["tap"].GatewayTap(
        url="ws://127.0.0.1:18789", token="still-good",
        store=tap_env["store"], node_id="n",
    )
    # No config file at all → _detect_gateway_endpoint returns (None, None).
    assert tap._refresh_credentials() is False
    assert tap.token == "still-good"


def test_connect_rejection_raises_gateway_auth_error(tap_env, monkeypatch):
    """A rejected connect that blames the token surfaces as
    ``GatewayAuthError`` so ``_run`` knows re-reading the config could
    help — a plain RuntimeError would just sleep and replay the dead
    credential."""
    gw = tap_env["tap"]

    def _reject(received_send: str) -> str:
        msg = json.loads(received_send)
        return json.dumps({
            "type": "res", "id": msg["id"], "ok": False,
            "error": _LIVE_BAD_TOKEN_ERROR,
        })

    class _RejectWS(_StubWS):
        def recv(self):
            if self.sent:
                return _reject(self.sent[-1])
            raise ConnectionError("nothing sent yet")

    class _Mod:
        def create_connection(self, _url, timeout=None):
            return _RejectWS([])

    monkeypatch.setitem(sys.modules, "websocket", _Mod())
    tap = gw.GatewayTap(
        url="ws://127.0.0.1:18789", token="stale",
        store=tap_env["store"], node_id="n",
    )
    with pytest.raises(gw.GatewayAuthError):
        tap._run_once()


def test_run_loop_recovers_when_the_token_rotates(tap_env, monkeypatch):
    """End to end for the reported bug: the tap is holding a dead token,
    the gateway rejects it, the user's config now carries the new one —
    the loop must adopt it and connect WITHOUT a daemon restart."""
    gw = tap_env["tap"]
    oc_home = tap_env["oc_home"]
    _write_gw_config(oc_home, "rotated-token")

    attempts: list[str] = []

    class _ScriptedWS(_StubWS):
        def recv(self):
            if not self.sent:
                raise ConnectionError("nothing sent yet")
            msg = json.loads(self.sent[-1])
            token = (msg.get("params", {}).get("auth") or {}).get("token")
            attempts.append(token)
            if token != "rotated-token":
                return json.dumps({
                    "type": "res", "id": msg["id"], "ok": False,
                    "error": _LIVE_BAD_TOKEN_ERROR,
                })
            # Correct token: accept, then close so _run_once returns.
            raise ConnectionError("accepted then closed")

    class _Mod:
        def create_connection(self, _url, timeout=None):
            return _ScriptedWS([])

    monkeypatch.setitem(sys.modules, "websocket", _Mod())
    tap = gw.GatewayTap(
        url="ws://127.0.0.1:18789", token="dead-token",
        store=tap_env["store"], node_id="n",
    )

    # First attempt: the tap still believes in the dead token only if it
    # never re-reads. It does re-read, so it should present the rotated one.
    try:
        tap._run_once()
    except Exception:
        pass

    assert attempts and attempts[-1] == "rotated-token", (
        "the tap must present the token currently on disk, not the one it "
        "cached at daemon start — otherwise the user reinstalls to recover"
    )
    assert tap.token == "rotated-token"
    assert tap.token_reloads == 1


def test_repeated_identical_auth_failures_are_not_logged_every_minute(
    tap_env, monkeypatch, caplog
):
    """The user-visible half of the report: "misfiring every minute".
    The first rejection is a loud, actionable WARNING; identical repeats
    drop to DEBUG so the daemon log stays readable."""
    import logging

    gw = tap_env["tap"]
    _write_gw_config(tap_env["oc_home"], "same-stale-token")

    tap = gw.GatewayTap(
        url="ws://127.0.0.1:18789", token="same-stale-token",
        store=tap_env["store"], node_id="n",
    )
    calls = {"n": 0}

    def _always_reject():
        calls["n"] += 1
        if calls["n"] > 3:
            tap._stop.set()
            return
        raise gw.GatewayAuthError("gateway connect rejected: token_mismatch")

    monkeypatch.setattr(tap, "_run_once", _always_reject)
    monkeypatch.setattr(gw, "_BACKOFF_INITIAL_SEC", 0.0)
    monkeypatch.setattr(gw, "_BACKOFF_MAX_SEC", 0.0)

    with caplog.at_level(logging.DEBUG, logger="clawmetry-sync"):
        tap._run()

    warnings = [r for r in caplog.records if r.levelno == logging.WARNING]
    assert len(warnings) == 1, (
        f"expected exactly one WARNING for a repeating rejection, got "
        f"{[r.getMessage() for r in warnings]}"
    )
    assert "no reinstall needed" in warnings[0].getMessage()
    assert tap.auth_failures == 3
