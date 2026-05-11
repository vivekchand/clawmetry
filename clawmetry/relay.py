"""clawmetry/relay.py — node-side WebSocket relay client (epic #964 phase 3b).

Maintains a long-lived WebSocket to `wss://app.clawmetry.com/api/node/relay`,
waits for `{type:"query"}` frames from the cloud, dispatches each via
`routes.local_query.relay_dispatch()`, returns chunked responses.

Design notes
------------
- **Optional dependency.** `websocket-client` is in `extras_require["relay"]`,
  not the base install. If it's missing the relay simply doesn't start; the
  daemon keeps working in cloud-ingest-only mode.
- **Daemon thread.** One thread per process. Reconnects with exponential
  backoff (2s → 60s cap). The sync daemon's main loop is unaware.
- **Skipped on OSS-local mode.** If `config` has no `api_key` / `node_id`,
  the relay never starts — local-only OSS users pay no overhead.
- **Privacy boundary unchanged.** Encrypted blobs stay encrypted; plaintext
  columns (token counts, timestamps, event types) ride the WS in the clear
  (TLS-protected). Same trust model as today's heartbeat / ingest.

Tests live in `tests/test_relay.py` and mock the WebSocket layer.
"""

from __future__ import annotations

import json
import logging
import os
import threading
import time
from typing import Optional

log = logging.getLogger(__name__)

RELAY_URL_DEFAULT = "wss://app.clawmetry.com/api/node/relay"
CHUNK_ROWS = 100               # max rows per response frame
RECONNECT_INITIAL_SEC = 2
RECONNECT_MAX_SEC = 60
RECV_TIMEOUT_SEC = 30          # forces a heartbeat ping when idle

# Shapes the node advertises in its register frame. Mirrors the allowlist in
# `routes/local_query._SHAPES` — keep these in sync.
_CAPABILITIES = [
    "query.events",
    "query.sessions",
    "query.aggregates",
    "query.transcript",
    "query.health",
]


def start_relay_thread(config: dict, version: str = "unknown") -> Optional[threading.Thread]:
    """Spin up a daemon thread that maintains the WS to cloud.

    Returns the thread object on success, ``None`` when relay can't or
    shouldn't run (no cloud account, `websocket-client` missing). Callers
    don't need to do anything with the returned thread — it's daemon=True.
    """
    api_key = (config or {}).get("api_key")
    node_id = (config or {}).get("node_id")
    if not api_key or not node_id:
        log.debug("relay: no cloud account (api_key/node_id missing) — relay disabled")
        return None
    try:
        import websocket  # noqa: F401 — pull dep early to fail fast
    except ImportError:
        log.info(
            "relay: websocket-client not installed; cloud cold-data relay disabled. "
            "Install with `pip install clawmetry[relay]` to enable.")
        return None

    relay_url = os.environ.get("CLAWMETRY_RELAY_URL", RELAY_URL_DEFAULT)
    t = threading.Thread(
        target=_relay_supervisor,
        args=(relay_url, api_key, node_id, version),
        daemon=True,
        name="clawmetry-relay",
    )
    t.start()
    log.info("relay: thread started → %s", relay_url)
    return t


def _relay_supervisor(relay_url: str, api_key: str, node_id: str, version: str) -> None:
    """Reconnect loop. Each call to `_run_once` is one WS session; on any
    exception we backoff and retry. Backoff resets after a clean exit."""
    backoff = RECONNECT_INITIAL_SEC
    while True:
        try:
            _run_once(relay_url, api_key, node_id, version)
            # Clean exit (server closed gracefully) — reset backoff.
            backoff = RECONNECT_INITIAL_SEC
            log.info("relay: connection closed by server; reconnecting in %ds", backoff)
            time.sleep(backoff)
        except Exception as e:  # noqa: BLE001 — any failure → retry
            log.warning("relay: error: %s — reconnecting in %ds", str(e)[:200], backoff)
            time.sleep(backoff)
            backoff = min(backoff * 2, RECONNECT_MAX_SEC)


def _run_once(relay_url: str, api_key: str, node_id: str, version: str) -> None:
    """One full WS session lifecycle: connect → register → dispatch
    incoming frames → return. Raises on any networking failure so the
    supervisor's backoff loop kicks in."""
    import websocket
    url = f"{relay_url}?token={api_key}&node_id={node_id}"
    ws = websocket.create_connection(
        url,
        header=[f"User-Agent: clawmetry-relay/{version}"],
        timeout=10,
    )
    try:
        # Register frame announces capabilities so the cloud knows which
        # shapes are safe to route to this node.
        ws.send(json.dumps({
            "type": "register",
            "node_id": node_id,
            "version": version,
            "capabilities": _CAPABILITIES,
        }))
        ws.settimeout(RECV_TIMEOUT_SEC)
        while True:
            try:
                raw = ws.recv()
            except websocket.WebSocketTimeoutException:
                # No traffic in RECV_TIMEOUT_SEC — send our own ping so the
                # cloud LB doesn't drop us as idle (Cloud Run idle = 5 min).
                try:
                    ws.ping()
                except Exception:
                    raise
                continue
            if not raw:
                # Empty payload = server requested close.
                return
            try:
                frame = json.loads(raw)
            except Exception:
                log.warning("relay: dropping non-JSON frame")
                continue
            _handle_frame(ws, frame)
    finally:
        try:
            ws.close()
        except Exception:
            pass


def _handle_frame(ws, frame: dict) -> None:
    """Single-frame dispatcher. `ws` is a live websocket.WebSocket."""
    ftype = frame.get("type")
    if ftype == "query":
        _handle_query(ws, frame)
    elif ftype == "ping":
        try:
            ws.send(json.dumps({"type": "pong"}))
        except Exception:
            raise
    else:
        log.debug("relay: ignoring frame type=%r", ftype)


def _handle_query(ws, frame: dict) -> None:
    """Dispatch a `query` frame through the same path the HTTP API uses,
    chunk-stream the response back. All errors → `{type:"error"}` frame
    so the cloud can surface them cleanly."""
    qid = frame.get("id")
    shape = frame.get("shape", "")
    args = frame.get("args") or {}

    try:
        from routes.local_query import relay_dispatch
        body = relay_dispatch(shape, args)
    except Exception as e:  # noqa: BLE001
        _send_error(ws, qid, "dispatch_exception", str(e)[:300])
        return

    if isinstance(body, dict) and "error" in body and "rows" not in body:
        _send_error(ws, qid, "dispatch_error", body["error"])
        return

    rows = body.get("rows") if isinstance(body, dict) else None

    if not rows:
        # Single-frame response (health shape, empty result, etc.)
        ws.send(json.dumps({
            "type": "response",
            "id": qid,
            "chunk": 1,
            "final": True,
            "body": body,
        }))
        return

    total = len(rows)
    chunk_count = (total + CHUNK_ROWS - 1) // CHUNK_ROWS
    for i in range(chunk_count):
        sl = rows[i * CHUNK_ROWS:(i + 1) * CHUNK_ROWS]
        is_final = (i == chunk_count - 1)
        out = {
            "type": "response",
            "id": qid,
            "chunk": i + 1,
            "final": is_final,
            "rows": sl,
        }
        if is_final:
            # Carry shape + count metadata on the final frame so the cloud
            # can validate completeness without re-iterating chunks.
            out["_shape"] = body.get("_shape")
            out["_elapsed_ms"] = body.get("_elapsed_ms")
            out["count"] = body.get("count", total)
        ws.send(json.dumps(out))


def _send_error(ws, qid, code: str, msg: str) -> None:
    try:
        ws.send(json.dumps({"type": "error", "id": qid, "code": code, "msg": msg}))
    except Exception:
        # If the WS itself is dead, the supervisor loop will catch it on
        # the next recv() and reconnect — nothing to do here.
        log.debug("relay: failed to send error frame for qid=%s", qid)
