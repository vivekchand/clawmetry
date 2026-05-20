"""HTTP query server hosted INSIDE the sync daemon process.

WHY THIS EXISTS
===============
The daemon owns the DuckDB writer lock on ``~/.clawmetry/clawmetry.duckdb``.
DuckDB's exclusive file lock blocks **every** other process from opening
the file — even read-only. So the separate dashboard process (started by
``clawmetry`` CLI on port 8900, while ``clawmetry sync`` runs as a
launchd/systemd daemon on PID X) literally cannot read the local store.

Fix: the daemon process exposes the same ``routes/local_query.py``
shapes over a localhost HTTP endpoint. The dashboard's ``/api/local/*``
routes proxy to this endpoint when the port-discovery file is present
and the daemon is reachable. When daemon is down, dashboard falls back
to opening the DuckDB directly (works in single-process mode).

DISCOVERY + AUTH
================
On start, daemon:
1. Generates a one-time 32-hex-char token.
2. Binds an HTTP server to ``127.0.0.1`` on an ephemeral port.
3. Writes ``{"port": N, "token": "...", "pid": M}`` to
   ``~/.clawmetry/local_query.json``.

Dashboard ``routes/local_query.py``:
1. Reads ``local_query.json``.
2. Sends each request as ``Authorization: Bearer <token>`` to
   ``http://127.0.0.1:<port>/local/query``.
3. On any failure (file missing, port refused, auth rejected), falls
   back to direct DuckDB.

Bound to ``127.0.0.1`` only — no other host can reach it. Combined with
the rotating token, no other user on the same box can either (they'd
need to read the port file, which is mode 0600).

LIFECYCLE
=========
``start()`` spawns a daemon thread running werkzeug's WSGI server.
``stop()`` is a no-op — the thread is daemon=True and dies with the
process. Port file is removed atexit (best-effort).
"""

from __future__ import annotations

import json
import logging
import os
import secrets
import socket
import threading
from pathlib import Path
from typing import Optional

log = logging.getLogger("clawmetry.local_server")

DISCOVERY_PATH = Path(os.path.expanduser("~/.clawmetry/local_query.json"))


# ── module state — single-process singleton ──────────────────────────────────
_started_lock = threading.Lock()
_server_thread: Optional[threading.Thread] = None
_token: Optional[str] = None
_port: Optional[int] = None


def get_token() -> Optional[str]:
    """Return the auth token, or None if the server hasn't been started."""
    return _token


def get_port() -> Optional[int]:
    """Return the bound port, or None if the server hasn't been started."""
    return _port


def _make_app():
    """Build the Flask app that hosts only the local_query blueprint.

    Lazy-imported so non-daemon contexts don't pay the Flask cost.
    """
    from flask import Flask, request, jsonify
    from routes.local_query import bp_local_query

    app = Flask("clawmetry-local-server")

    @app.before_request
    def _check_token():
        # Expected: Authorization: Bearer <token>
        provided = (request.headers.get("Authorization") or "").strip()
        if not provided.startswith("Bearer "):
            return jsonify({"error": "unauthorized"}), 401
        if provided[len("Bearer "):] != _token:
            return jsonify({"error": "unauthorized"}), 401
        return None

    app.register_blueprint(bp_local_query)
    return app


def _pick_free_port() -> int:
    """Bind-to-zero trick: ask the kernel for a free localhost port."""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


def _write_discovery_file(port: int, token: str) -> None:
    """Atomically write the port+token JSON. Mode 0600 so only the same
    user can read it."""
    DISCOVERY_PATH.parent.mkdir(parents=True, exist_ok=True)
    payload = {"port": port, "token": token, "pid": os.getpid()}
    tmp = DISCOVERY_PATH.with_suffix(DISCOVERY_PATH.suffix + ".tmp")
    tmp.write_text(json.dumps(payload))
    os.chmod(tmp, 0o600)
    os.replace(tmp, DISCOVERY_PATH)




def _serve_forever(app, port: int) -> None:
    """Run werkzeug in single-thread, daemon-attached mode. Threaded=True
    so concurrent dashboard requests don't serialize on the WSGI loop."""
    from werkzeug.serving import make_server
    server = make_server("127.0.0.1", port, app, threaded=True)
    log.info("local_server: listening on 127.0.0.1:%d", port)
    try:
        server.serve_forever()
    except Exception:
        log.exception("local_server: serve_forever crashed")


def start() -> Optional[int]:
    """Start the local query HTTP server.

    Returns the bound port, or None if startup failed (caller can ignore
    — daemon proceeds without the server, dashboard falls back to direct
    DuckDB access).
    """
    global _server_thread, _token, _port
    with _started_lock:
        if _server_thread is not None and _server_thread.is_alive():
            log.debug("local_server: already running on port %d", _port)
            return _port
        # Pre-warm the writer LocalStore. The process hosting local_server
        # IS the daemon (only it answers /__local_query__/<method>), so it
        # owns the DuckDB writer lock by definition. Without this, the
        # ``_store()`` call inside routes/local_query.py opens DuckDB
        # read-only — which raises ``IO Error: Cannot open database … in
        # read-only mode: database does not exist`` on first-boot setups
        # where no .duckdb file has been created yet (CI keystone job,
        # fresh user install before any sync). Result: every
        # /__local_query__/<method> request 500s and the dashboard +
        # keystone E2E verifier silently fail. Idempotent — when the sync
        # daemon already opened the writer earlier in boot this is a
        # no-op singleton fetch.
        try:
            from clawmetry import local_store as _ls
            # This process hosts local_server -> it IS the daemon and owns the
            # writer. Mark it so get_store() opens the writer here and refuses
            # to let other processes (the dashboard) steal it during a restart.
            _ls.mark_writer_owner()
            _ls.get_store(read_only=False)
        except Exception as e:
            log.warning(
                "local_server: failed to pre-warm writer store (%s) — "
                "request handlers will surface this as 500s",
                e,
            )
        try:
            app = _make_app()
        except Exception as e:
            log.warning("local_server: cannot build app (%s) — disabled", e)
            return None
        _token = secrets.token_hex(16)
        _port = _pick_free_port()
        _server_thread = threading.Thread(
            target=_serve_forever, args=(app, _port),
            name="clawmetry-local-server", daemon=True,
        )
        _server_thread.start()
        try:
            _write_discovery_file(_port, _token)
        except Exception as e:
            log.warning("local_server: failed to write discovery file: %s", e)
        # NOTE: intentionally do NOT delete the discovery file on exit. During
        # a daemon restart the brief gap between old-exit and new-write would
        # leave the file missing — and a missing file makes get_store()'s
        # writer guard think "no daemon present", letting the dashboard grab
        # the writer in that window (the recurring Models/Embodied breakage).
        # The next daemon overwrites the file on start; a stale entry is
        # harmless (proxy clients already fall back on a dead port).
        return _port


def is_running() -> bool:
    """True iff the server thread is alive."""
    return _server_thread is not None and _server_thread.is_alive()
