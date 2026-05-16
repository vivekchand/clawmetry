"""
clawmetry/gateway_tap.py — live OpenClaw gateway WebSocket subscriber.

Why this exists
---------------

OpenClaw stores Telegram (and other ephemeral channels — Signal,
WhatsApp, Discord, Slack, IRC, iMessage, WebChat, …) chat traffic
**entirely in memory**. There is NO ``~/.openclaw/<channel>/*.jsonl``
written for inbound messages on those channels — the only on-disk
evidence is ``[telegram] sendMessage ok …`` ACK lines in
``~/.openclaw/logs/gateway.log`` (outbound only, no body).

That gap means:

  * The Brain tab silently misses every inbound user message on
    Telegram + sibling adapters.
  * ``channel_messages`` only ever contains outbound ACK rows (with
    ``body=None``) — half a conversation.

This module taps the gateway's live WebSocket JSON-RPC stream
(``ws://localhost:18789``), subscribes to per-session message events
that DO carry the body, and upserts each frame into the local DuckDB
``events`` and ``channel_messages`` tables. Real-time, in-process,
no extra dependencies beyond the optional ``websocket-client`` (already
the import path used by ``helpers/gateway.py``).

Where it lives
--------------

The tap runs as a single background thread inside the sync daemon
(``clawmetry/sync.py:run_daemon``). One thread, one persistent socket,
exponential-backoff reconnect on every disconnect. The thread is a
``daemon=True`` so a daemon shutdown doesn't hang on it.

Failure modes
-------------

1. ``websocket-client`` not installed → tap is a no-op. Logged once at
   startup; the gateway-log parser path keeps going (outbound ACKs only).
2. Gateway not reachable / token missing → tap retries with backoff.
3. Gateway accepts ``connect`` but our token gets ``scopes=[]`` —
   subscribing to ``sessions.messages.subscribe`` etc. then fails with
   ``missing scope: operator.read``. We log a single WARNING with the
   exact symptom so the user can update their OpenClaw config (or pin
   the upstream issue at openclaw/openclaw).

Disable
-------

Set ``CLAWMETRY_ENABLE_WS_TAP=1`` in the environment to opt in.
Default is OFF until the upstream OpenClaw server grants the
required ``operator.read`` scope.
"""

from __future__ import annotations

import json
import logging
import os
import threading
import uuid
from datetime import datetime, timezone
from typing import Any, Callable, Iterable

log = logging.getLogger("clawmetry-sync")  # share the daemon logger sink


# ── Defaults & config ────────────────────────────────────────────────────


# Channels we attempt to subscribe to. Mirrors ``_CHANNEL_DIRS`` in
# ``clawmetry/sync.py`` — every chat-channel adapter that exposes
# inbound messages over the gateway. The gateway protocol does not
# (yet) accept a per-channel filter on ``sessions.messages.subscribe``
# — the subscription is global — so this list is documentation only.
# We kept it as a list (rather than dropping to a single subscribe call)
# so a future per-channel subscribe API can plug in without touching
# the call sites in sync.py.
CHANNEL_NAMES: tuple[str, ...] = (
    "telegram",
    "signal",
    "whatsapp",
    "discord",
    "slack",
    "irc",
    "imessage",
    "webchat",
    "googlechat",
    "msteams",
    "bluebubbles",
    "matrix",
    "mattermost",
    "line",
    "nostr",
    "twitch",
    "feishu",
    "zalo",
    "tlon",
    "synologychat",
    "nextcloudtalk",
)


# Reconnect cadence — exponential backoff with jitter cap.
_BACKOFF_INITIAL_SEC = 2.0
_BACKOFF_MAX_SEC = 60.0


# Enable env var (feature is default-OFF until upstream grants scopes).
_ENABLE_ENV = "CLAWMETRY_ENABLE_WS_TAP"


# ── Frame normalization ─────────────────────────────────────────────────

# A normalized turn we project from any provider's WS frame. Mirrors the
# shape that ``clawmetry/sync.py:_parse_channel_event`` produces for
# JSONL lines, so the downstream brain-history reader doesn't need to
# care which transport the row arrived on.
#
# Required: provider, ts. Everything else is best-effort with a sane
# default. Returning ``None`` skips the frame entirely.
def _normalize_frame(frame: dict) -> dict | None:
    """Project a gateway WS event frame into a ``channel_messages`` row
    dict, or ``None`` if the frame is not a chat message.

    The gateway's own per-channel event names vary
    (``sessions.message``, ``telegram.inbound``, ``channel.message``,
    …). We accept any frame whose ``payload`` carries enough fields to
    pin a channel + a timestamp. Heartbeats / health / status frames
    fall through to ``None`` and the caller drops them.

    The returned dict is passed straight to
    ``LocalStore.ingest_channel_event`` (issue #1220) which fans it
    onto BOTH the ``channel_messages`` and ``events`` tables in a
    single chokepoint — earlier versions of this module hand-rolled
    a parallel ``events`` row here, which drifted out of contract
    every time the projection logic was touched.
    """
    if not isinstance(frame, dict):
        return None
    if frame.get("type") != "event":
        return None

    event_name = str(frame.get("event") or "")
    payload = frame.get("payload") or {}
    if not isinstance(payload, dict):
        return None

    # ── provider ────────────────────────────────────────────────────────
    # Try the provider-tagged shapes first, then fall back to inferring
    # from the event name (e.g. ``telegram.inbound`` → ``telegram``).
    provider = (
        payload.get("provider")
        or payload.get("channel")
        or payload.get("adapter")
    )
    if not provider and "." in event_name:
        head = event_name.split(".", 1)[0].lower()
        if head in CHANNEL_NAMES:
            provider = head
    if not provider:
        # Not a channel event we know how to project. (Health, presence,
        # state-version, etc. all land here.)
        return None
    provider = str(provider).lower().strip()

    # ── ts ──────────────────────────────────────────────────────────────
    raw_ts = (
        payload.get("ts")
        or payload.get("timestamp")
        or payload.get("date")
        or frame.get("ts")
    )
    if raw_ts is None:
        return None
    if isinstance(raw_ts, (int, float)):
        try:
            # Telegram-style epoch seconds (or millis if > 1e12).
            secs = float(raw_ts)
            if secs > 1e12:
                secs = secs / 1000.0
            raw_ts = datetime.fromtimestamp(
                secs, tz=timezone.utc
            ).isoformat()
        except (ValueError, OSError, OverflowError):
            return None
    ts = str(raw_ts)

    # ── direction ───────────────────────────────────────────────────────
    direction = payload.get("direction")
    if direction not in ("in", "out"):
        # Heuristic: explicit role + bot signal → outbound.
        if (
            payload.get("from_bot") is True
            or payload.get("role") == "assistant"
            or "outbound" in event_name.lower()
            or "send" in event_name.lower()
        ):
            direction = "out"
        elif (
            "inbound" in event_name.lower()
            or payload.get("from")
            or payload.get("sender")
            or payload.get("user")
        ):
            direction = "in"
        else:
            direction = "in"  # default to inbound (the gap we're closing)

    # ── chat / channel id ───────────────────────────────────────────────
    chat_id = (
        payload.get("chat_id")
        or payload.get("chatId")
        or payload.get("channel_id")
        or payload.get("channelId")
        or payload.get("conversation_id")
        or payload.get("session_id")
    )
    chat = payload.get("chat") if isinstance(payload.get("chat"), dict) else None
    if not chat_id and chat:
        chat_id = chat.get("id")
    if not chat_id:
        chat_id = "unknown"
    chat_id = str(chat_id)

    # ── message id (dedup key) ──────────────────────────────────────────
    raw_id = (
        payload.get("message_id")
        or payload.get("messageId")
        or payload.get("id")
        or payload.get("update_id")
        or payload.get("updateId")
    )
    if raw_id is None:
        # Synthesize from ts + chat so re-deliveries collapse on PK.
        raw_id = f"{ts}"
    eid = f"{provider}:{chat_id}:{raw_id}"

    # ── body ────────────────────────────────────────────────────────────
    body = payload.get("text") or payload.get("body") or payload.get("message")
    if body is None:
        content = payload.get("content")
        if isinstance(content, str):
            body = content
        elif isinstance(content, list):
            for c in content:
                if isinstance(c, dict) and c.get("type") == "text":
                    body = c.get("text")
                    if body:
                        break
    if body is not None:
        body = str(body)

    # ── sender ──────────────────────────────────────────────────────────
    sender_block = (
        payload.get("from")
        or payload.get("sender")
        or payload.get("user")
        or {}
    )
    if not isinstance(sender_block, dict):
        sender_block = {}
    sender_id = (
        payload.get("sender_id")
        or sender_block.get("id")
        or payload.get("user_id")
        or chat_id
    )
    sender_name = (
        payload.get("sender_name")
        or sender_block.get("username")
        or sender_block.get("first_name")
        or sender_block.get("name")
    )

    return {
        "id": eid,
        "agent_id": "main",
        "provider": provider,
        "channel_id": str(chat_id),
        "sender_id": str(sender_id) if sender_id is not None else None,
        "sender_name": sender_name,
        "body": (body[:4000] if body else None),
        "ts": ts,
        "direction": direction,
        "session_key": payload.get("session_id") or payload.get("session_key"),
        # raw_blob preserves the full payload + WS-tap source
        # breadcrumbs. ``ingest_channel_event`` flattens it into the
        # events-table ``data`` blob so brain filters can split WS-tap
        # rows from log-parser rows when debugging without us having
        # to maintain two parallel projections.
        "raw_blob": {
            **payload,
            "_clawmetry_source": "gateway.ws",
            "_clawmetry_event": event_name,
        },
    }


# ── The tap loop ────────────────────────────────────────────────────────


class GatewayTap:
    """Background WS subscriber. One instance per daemon.

    The tap is fail-quiet by design: any error during connect, auth, or
    receive triggers a backoff-and-reconnect rather than crashing the
    daemon. The DuckDB write path is the only thing we trust to raise
    (and we wrap each row in its own try so a malformed frame can't
    poison the batch).
    """

    def __init__(
        self,
        url: str,
        token: str,
        store: Any,
        node_id: str,
        *,
        on_connect: Callable[[], None] | None = None,
        on_disconnect: Callable[[Exception | None], None] | None = None,
        on_event: Callable[[dict], None] | None = None,
        channels: Iterable[str] = CHANNEL_NAMES,
    ) -> None:
        self.url = url
        self.token = token
        self.store = store
        self.node_id = node_id
        self.channels = tuple(channels)
        self._on_connect = on_connect
        self._on_disconnect = on_disconnect
        self._on_event = on_event
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        # Stats so health checks / tests can introspect activity.
        self.connected = False
        self.frames_seen = 0
        self.rows_written = 0
        self.last_error: str | None = None

    # ── lifecycle ──────────────────────────────────────────────────────

    def start(self) -> threading.Thread:
        if self._thread is not None and self._thread.is_alive():
            return self._thread
        t = threading.Thread(
            target=self._run, daemon=True, name="gateway-ws-tap"
        )
        self._thread = t
        t.start()
        return t

    def stop(self, timeout: float = 2.0) -> None:
        self._stop.set()
        t = self._thread
        if t is not None:
            t.join(timeout=timeout)

    # ── main loop ──────────────────────────────────────────────────────

    def _run(self) -> None:
        backoff = _BACKOFF_INITIAL_SEC
        while not self._stop.is_set():
            try:
                self._run_once()
                # Clean disconnect: reset backoff so the next reconnect
                # is immediate (gateway restart, network blip).
                backoff = _BACKOFF_INITIAL_SEC
            except Exception as e:  # noqa: BLE001 — log and retry
                self.last_error = repr(e)
                log.warning(
                    "gateway WS tap disconnected, reconnecting in %.0fs (%s)",
                    backoff, e,
                )
                if self._on_disconnect:
                    try:
                        self._on_disconnect(e)
                    except Exception:
                        pass
            # Wait for backoff with shutdown polling (so stop() is responsive).
            self._stop.wait(timeout=backoff)
            backoff = min(_BACKOFF_MAX_SEC, backoff * 2.0)

    def _run_once(self) -> None:
        try:
            import websocket  # type: ignore
        except ImportError:
            log.warning(
                "gateway WS tap: websocket-client not installed — "
                "inbound channel messages will NOT reach DuckDB. "
                "Install `pip install websocket-client` to enable."
            )
            # Long sleep before re-checking; the import won't appear at
            # runtime, this is essentially a one-shot warning.
            self._stop.wait(timeout=300)
            return

        ws_url = (
            self.url.replace("http://", "ws://").replace("https://", "wss://")
        ).rstrip("/")
        if not ws_url:
            raise RuntimeError("empty gateway URL")
        if not self.token:
            raise RuntimeError("missing gateway token")

        ws = websocket.create_connection(f"{ws_url}/", timeout=10)
        ws.settimeout(30)

        # Drain initial challenge frame (if any). Best-effort — some
        # gateway builds push it, some don't.
        try:
            ws.settimeout(2)
            ws.recv()
        except Exception:
            pass
        ws.settimeout(30)

        # Connect handshake.
        cid = f"clawmetry-tap-{uuid.uuid4().hex[:8]}"
        connect_msg = {
            "type": "req",
            "id": cid,
            "method": "connect",
            "params": {
                "minProtocol": 3,
                "maxProtocol": 3,
                "client": {
                    "id": "cli",
                    "version": "clawmetry-ws-tap",
                    "platform": "python",
                    "mode": "cli",
                    "instanceId": cid,
                },
                "role": "operator",
                "scopes": ["operator.admin", "operator.read"],
                "auth": {"token": self.token},
            },
        }
        ws.send(json.dumps(connect_msg))

        granted: list[str] = []
        for _ in range(10):
            r = json.loads(ws.recv())
            if r.get("type") == "res" and r.get("id") == cid:
                if not r.get("ok"):
                    raise RuntimeError(
                        f"gateway connect rejected: "
                        f"{r.get('error', {}).get('message', 'unknown')}"
                    )
                granted = (
                    r.get("payload", {}).get("auth", {}).get("scopes") or []
                )
                break
        else:
            raise RuntimeError("gateway never replied to connect")

        # Best-effort subscribe. The gateway pushes some events
        # (`health`) without subscription, but per-channel message
        # bodies require explicit subscribe — and require
        # `operator.read` scope. We log loudly but DON'T abort if the
        # subscribe is rejected: the tap still sees `health` channel
        # snapshots and any future-protocol push events.
        sub_methods = (
            ("sessions.messages.subscribe", {}),
            ("sessions.subscribe", {}),
        )
        sub_ok = False
        for method, params in sub_methods:
            sid = f"sub-{uuid.uuid4().hex[:6]}"
            try:
                ws.send(json.dumps({
                    "type": "req",
                    "id": sid,
                    "method": method,
                    "params": params,
                }))
                # Drain up to a few frames waiting for our response.
                for _ in range(20):
                    r = json.loads(ws.recv())
                    if r.get("type") == "event":
                        # An event arrived mid-handshake; route it.
                        self._handle_frame(r)
                        continue
                    if r.get("id") == sid:
                        if r.get("ok"):
                            sub_ok = True
                        else:
                            err = r.get("error", {}).get("message", "?")
                            log.warning(
                                "gateway WS tap: %s rejected (%s) — "
                                "inbound channel bodies will not arrive "
                                "until OpenClaw grants `operator.read` "
                                "scope to the gateway token. See "
                                "openclaw/openclaw issue tracker.",
                                method, err,
                            )
                        break
            except Exception as e:  # noqa: BLE001
                log.debug("gateway WS tap: %s subscribe error: %s", method, e)

        self.connected = True
        if sub_ok:
            log.info(
                "gateway WS tap connected — capturing live channel events"
            )
        else:
            log.info(
                "gateway WS tap connected (degraded — no message subscribe; "
                "granted scopes=%s)", granted,
            )
        if self._on_connect:
            try:
                self._on_connect()
            except Exception:
                pass

        # Receive loop — blocks on recv(). Any exception bubbles to
        # _run() which logs + reconnects.
        try:
            ws.settimeout(60)
            while not self._stop.is_set():
                raw = ws.recv()
                if not raw:
                    raise RuntimeError("gateway closed connection")
                try:
                    frame = json.loads(raw)
                except Exception:
                    continue
                self._handle_frame(frame)
        finally:
            self.connected = False
            try:
                ws.close()
            except Exception:
                pass

    # ── per-frame ingest ──────────────────────────────────────────────

    def _handle_frame(self, frame: dict) -> None:
        self.frames_seen += 1
        if self._on_event:
            try:
                self._on_event(frame)
            except Exception:
                pass

        channel_msg = _normalize_frame(frame)
        if channel_msg is None:
            return

        # Issue #1220: single chokepoint writes channel_messages +
        # events atomically. The previous version of this method
        # called ingest_many() for the events projection and
        # ingest_channel_message() for the per-channel row — the two
        # writers drifted out of contract every time the projection
        # logic was touched on one side and not the other (the
        # original P0 #1212 bug).
        try:
            self.store.ingest_channel_event(
                channel_msg, node_id=self.node_id,
            )
            self.rows_written += 1
        except Exception as e:  # noqa: BLE001
            log.debug("gateway WS tap: channel_event ingest skipped (%s)", e)


# ── Daemon entry point ──────────────────────────────────────────────────


def start(config: dict) -> GatewayTap | None:
    """Spawn the gateway tap thread. Returns the ``GatewayTap`` instance
    (so the caller can introspect ``.connected`` / ``.frames_seen``) or
    ``None`` if disabled or unconfigured.

    Config dict required keys: ``node_id``. URL+token are detected
    from the live OpenClaw config (mirroring dashboard's
    ``_detect_gateway_token`` / ``_detect_gateway_port``).
    """
    if os.environ.get(_ENABLE_ENV, "").strip() not in ("1", "true", "yes"):
        log.debug("gateway WS tap disabled (set CLAWMETRY_ENABLE_WS_TAP=1 to enable)")
        return None

    url, token = _detect_gateway_endpoint()
    if not url or not token:
        log.warning(
            "gateway WS tap: cannot detect gateway URL or token — "
            "skipped. Set OPENCLAW_GATEWAY_TOKEN or check "
            "~/.openclaw/openclaw.json."
        )
        return None

    try:
        from clawmetry import local_store
        store = local_store.get_store()
    except Exception as e:  # noqa: BLE001
        log.warning("gateway WS tap: local_store unavailable (%s)", e)
        return None

    tap = GatewayTap(url=url, token=token, store=store,
                     node_id=config.get("node_id") or "unknown")
    tap.start()
    return tap


def _detect_gateway_endpoint() -> tuple[str | None, str | None]:
    """Detect (url, token) from env + ~/.openclaw config files.

    Mirrors the dashboard's ``_detect_gateway_token`` /
    ``_detect_gateway_port`` (kept local here so the daemon doesn't
    have to import dashboard.py — the daemon never starts Flask).
    """
    oc_dir = os.environ.get(
        "CLAWMETRY_OPENCLAW_DIR", os.path.expanduser("~/.openclaw")
    )

    # Token: env first, then config files.
    token = os.environ.get("OPENCLAW_GATEWAY_TOKEN", "").strip() or None
    port: int | None = None
    try:
        port_env = os.environ.get("OPENCLAW_GATEWAY_PORT", "").strip()
        if port_env:
            port = int(port_env)
    except ValueError:
        port = None

    if token is None or port is None:
        for fname in ("openclaw.json", "moltbot.json", "clawdbot.json"):
            try:
                with open(os.path.join(oc_dir, fname)) as f:
                    cfg = json.load(f)
            except (OSError, ValueError):
                continue
            gw = cfg.get("gateway") if isinstance(cfg, dict) else None
            if not isinstance(gw, dict):
                continue
            if token is None:
                auth = gw.get("auth") or {}
                if isinstance(auth, dict) and auth.get("token"):
                    token = str(auth["token"])
            if port is None and gw.get("port"):
                try:
                    port = int(gw["port"])
                except (TypeError, ValueError):
                    pass
            if token and port:
                break

    if not port:
        port = 18789  # OpenClaw default
    if not token:
        return None, None

    return f"ws://127.0.0.1:{port}", token
