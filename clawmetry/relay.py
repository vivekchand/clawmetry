"""clawmetry/relay.py — DEPRECATED stub.

The node-side WebSocket relay client was retired 2026-05-13. The cloud
endpoint ``wss://app.clawmetry.com/api/node/relay`` was killed 2026-05-12
(returns 404 in prod) after the simple-websocket handshake-400 dead end
documented in ``reference_ws_handshake_400_unsolved.md``. Per
``project_relay_transport_decision``, the replacement is heartbeat
piggyback: the cloud attaches ``pending_queries`` to the heartbeat
response, the daemon answers via ``/ingest/cache``. No new long-lived
connections.

This module is kept as a no-op stub so:
  * old daemon installs that still ``from clawmetry import relay`` don't
    crash on import, and
  * the existing unit tests in ``tests/test_relay.py`` can still import
    the dispatch / chunking helpers (which are unrelated to the dead WS
    supervisor and continue to drive the heartbeat-piggyback query path
    via ``routes.local_query.relay_dispatch``).

The reconnect supervisor (``_relay_supervisor``) is intentionally NOT
exported anymore — calling ``start_relay_thread`` is a no-op that
returns ``None``.
"""

from __future__ import annotations

import json
import logging
import threading

log = logging.getLogger(__name__)

# Historical constants — preserved so any external code that imported them
# (or any test that asserts on the module surface) keeps working.
RELAY_URL_DEFAULT = "wss://app.clawmetry.com/api/node/relay"
CHUNK_ROWS = 100               # max rows per response frame
RECONNECT_INITIAL_SEC = 2
RECONNECT_MAX_SEC = 60
RECV_TIMEOUT_SEC = 30

# Shapes the node advertises in its register frame. Mirrors the allowlist in
# ``routes/local_query._SHAPES`` — keep these in sync (the heartbeat-piggyback
# replacement uses the same dispatch table, so the drift test stays useful).
_CAPABILITIES = [
    "query.events",
    "query.sessions",
    "query.aggregates",
    "query.transcript",
    "query.health",
]


def start_relay_thread(config: dict, version: str = "unknown") -> threading.Thread | None:
    """No-op since 2026-05-13. See module docstring.

    Returns ``None`` unconditionally so callers' ``if t:`` guards stay
    valid. Logged at DEBUG (not INFO/WARNING) so users don't see a
    misleading "relay disabled" line on every daemon start.
    """
    log.debug(
        "relay: start_relay_thread is a no-op (WS retired 2026-05-13, "
        "replaced by heartbeat-piggyback per project_relay_transport_decision)"
    )
    return None


def _handle_frame(ws, frame: dict) -> None:
    """Single-frame dispatcher. Retained for unit tests; the live WS path
    is dead, but the dispatch shape is reused by the heartbeat-piggyback
    handler in ``sync._dispatch_pending_queries``."""
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
    """Dispatch a ``query`` frame through the same path the HTTP API
    uses, chunk-stream the response back. Retained for back-compat
    tests; the live network path is dead."""
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
            out["_shape"] = body.get("_shape")
            out["_elapsed_ms"] = body.get("_elapsed_ms")
            out["count"] = body.get("count", total)
        ws.send(json.dumps(out))


def _send_error(ws, qid, code: str, msg: str) -> None:
    try:
        ws.send(json.dumps({"type": "error", "id": qid, "code": code, "msg": msg}))
    except Exception:
        log.debug("relay: failed to send error frame for qid=%s", qid)
