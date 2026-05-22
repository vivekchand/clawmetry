"""
clawmetry/sync.py — Cloud sync daemon for clawmetry connect.

Reads local OpenClaw sessions/logs, encrypts with AES-256-GCM (E2E),
and streams to ingest.clawmetry.com. The encryption key never leaves
the local machine — cloud stores ciphertext only.
"""

from __future__ import annotations
import json
import os
import random
import sys
import time
import glob
import base64
import secrets
import logging
import platform
import threading
import subprocess
import urllib.request
import urllib.error
import uuid
from pathlib import Path
from datetime import datetime, timezone
from itertools import islice


def _get_openclaw_dir():
    """Return the OpenClaw config directory, respecting CLAWMETRY_OPENCLAW_DIR env var."""
    return os.environ.get("CLAWMETRY_OPENCLAW_DIR", os.path.expanduser("~/.openclaw"))


# ── Single-instance PID lock ──────────────────────────────────────────────────
def _pid_file() -> Path:
    return Path(os.path.expanduser("~/.clawmetry/sync.pid"))


def _acquire_pid_lock() -> bool:
    """Atomically claim the PID file. Return False if another instance is
    already running. Uses ``O_CREAT|O_EXCL`` to win the create race when
    two daemons start simultaneously — the previous ``exists()`` then
    ``write_text()`` pattern had a TOCTOU window where both processes
    could pass the check and both write their PIDs.

    Identified by @dumko2001 in #512.
    """
    pid_path = _pid_file()
    pid_path.parent.mkdir(parents=True, exist_ok=True)
    pid_str = str(os.getpid()).encode()
    while True:
        try:
            fd = os.open(str(pid_path), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            try:
                os.write(fd, pid_str)
            finally:
                os.close(fd)
            return True
        except FileExistsError:
            try:
                existing_pid = int(pid_path.read_text().strip())
            except (ValueError, OSError):
                try:
                    pid_path.unlink()
                except OSError:
                    return False
                continue
            try:
                os.kill(existing_pid, 0)
                return False
            except ProcessLookupError:
                try:
                    pid_path.unlink()
                except OSError:
                    pass
                continue


def _release_pid_lock() -> None:
    try:
        _pid_file().unlink(missing_ok=True)
    except Exception:
        pass


# ── Graceful shutdown — drain ring buffer on SIGTERM/SIGINT/atexit (#1593) ──
#
# Without this, any events queued in the LocalStore ring buffer but not yet
# flushed by the 2s flusher tick are dropped on `kill -TERM`, launchctl
# bootout, systemctl restart, or any clean shutdown. Bounded data loss of
# ≤ FLUSH_INTERVAL_SECS × event-rate per shutdown — silent and frequent on
# macOS where every install.sh upgrade triggers a launchctl bootout/load.
#
# Three entry points cover the full exit surface:
#   1. SIGTERM   — what launchctl/systemctl/`kill` send by default
#   2. SIGINT    — Ctrl+C in foreground (`clawmetry sync --foreground`)
#   3. atexit    — belt-and-suspenders for `sys.exit(0)`, uncaught exceptions,
#                  normal interpreter teardown. atexit is NOT guaranteed to
#                  run on SIGTERM (Python's default SIGTERM handler bypasses
#                  it), which is why we need the explicit signal handler too.
#
# Re-entrancy guard: signal then atexit, or two signals in a row, both
# end up here. The flag ensures we drain exactly once.
#
# Timeout: a hung DuckDB lock (e.g. another process briefly holding the
# writer) must not block shutdown indefinitely. Spawn the flush on a
# background thread, join with a hard 5s budget, then os._exit(0) to
# force-exit if the flush is still in flight. The events stay in the
# ring file-of-record (PR #1608 + DuckDB INSERT OR IGNORE make the next
# start replay idempotent — see `_flush_now_locked` docstring).

_SHUTDOWN_FLUSH_TIMEOUT_SECS = 5.0
_shutdown_flushed = threading.Event()
_shutdown_lock = threading.Lock()


def _drain_local_store_now() -> tuple[int, float]:
    """Synchronously drain the LocalStore ring → DuckDB. Returns
    (rows_written, elapsed_seconds). Safe to call multiple times — the
    second call is a no-op (the ring is empty after the first commit).

    Pairs with PR #1608's ``_flush_lock`` (issue #1590): ``store.flush()``
    serialises against any concurrent flusher tick, so we never race the
    snapshot-then-pop window."""
    t0 = time.monotonic()
    try:
        from clawmetry import local_store as _ls
        store = _ls.get_store(read_only=False)
        rows = store.flush()
    except Exception:
        log.exception("graceful shutdown: local store flush raised")
        return (0, time.monotonic() - t0)
    return (rows, time.monotonic() - t0)


def _graceful_shutdown(reason: str, *, force_exit: bool) -> None:
    """Drain the ring buffer with a hard timeout, then optionally hard-exit.

    ``force_exit=True`` is used by the signal handlers — once we've
    drained (or timed out), we call ``os._exit(0)`` so the interpreter
    tears down without re-running other handlers (atexit already
    skipped, daemon threads die at process exit anyway).

    ``force_exit=False`` is used by the atexit path — the interpreter
    is already exiting; we just need to drain before it tears down.
    """
    # Re-entrancy guard. The first caller wins; subsequent callers
    # (e.g. atexit firing after a signal handler already drained) see
    # the flag set and skip.
    with _shutdown_lock:
        if _shutdown_flushed.is_set():
            if force_exit:
                os._exit(0)
            return
        _shutdown_flushed.set()

    log.info("graceful shutdown: %s — draining local store ring", reason)

    # Run the flush on a background thread so we can enforce a wall-clock
    # timeout. A blocked DuckDB write must not hang launchctl/systemctl
    # for >5s — the orchestrator will SIGKILL us anyway after its own
    # grace period (30s on launchd, 90s default on systemd).
    result: dict[str, object] = {}

    def _runner() -> None:
        try:
            result["rows"], result["elapsed"] = _drain_local_store_now()
        except Exception as e:
            result["error"] = e

    t = threading.Thread(target=_runner, name="clawmetry-shutdown-flush", daemon=True)
    t.start()
    t.join(timeout=_SHUTDOWN_FLUSH_TIMEOUT_SECS)

    if t.is_alive():
        log.warning(
            "graceful shutdown: local store flush exceeded %.1fs timeout — "
            "abandoning; events stay in ring for next start to replay "
            "(INSERT OR IGNORE makes it idempotent)",
            _SHUTDOWN_FLUSH_TIMEOUT_SECS,
        )
    elif "error" in result:
        log.warning("graceful shutdown: flush raised: %s", result["error"])
    else:
        rows = result.get("rows", 0)
        elapsed = result.get("elapsed", 0.0)
        log.info(
            "graceful shutdown: flushed %s row(s) in %.3fs", rows, elapsed
        )

    if force_exit:
        # sys.exit raises SystemExit which other threads can swallow;
        # os._exit terminates the process immediately. atexit has
        # already been bypassed (we set the guard above).
        os._exit(0)


def _signal_handler(signum, frame):  # noqa: ARG001 — signal handler signature
    try:
        import signal as _signal
        name = _signal.Signals(signum).name
    except Exception:
        name = f"signal {signum}"
    _graceful_shutdown(name, force_exit=True)


def _atexit_handler() -> None:
    _graceful_shutdown("atexit", force_exit=False)


def _install_shutdown_handlers() -> None:
    """Wire SIGTERM/SIGINT/atexit → graceful drain. Idempotent.

    Skipped when not running on the main thread (signal.signal() raises
    ValueError off-main) — tests that import sync.py from a worker
    thread get the atexit hook only, which is enough for `sys.exit()`
    paths.
    """
    import atexit
    import signal as _signal
    atexit.register(_atexit_handler)
    try:
        _signal.signal(_signal.SIGTERM, _signal_handler)
        _signal.signal(_signal.SIGINT, _signal_handler)
    except (ValueError, OSError) as e:
        # ValueError: not main thread. OSError: SIGTERM/SIGINT not
        # supported on this platform (some Windows configurations).
        log.warning(
            "graceful shutdown: signal handlers not installed (%s) — "
            "atexit-only fallback (SIGTERM may still drop ring events)",
            e,
        )


def _validate_log_offsets(state: dict, paths: dict) -> None:
    """Validate stored log offsets on startup.

    Prevents silent data gaps caused by log rotation or file truncation:
    after a restart the stored offset may be beyond the current file end, or
    the file may have shrunk and grown back past the offset (so offset < size
    but the bytes there are new content, not what was originally at that
    position).  We reset any offset >= current file size to 0 so the daemon
    re-reads from the start and catches up on missed events.
    """
    offsets = state.get("last_log_offsets", {})
    if not offsets:
        return
    log_dir = paths.get("log_dir", "")
    if not log_dir:
        return
    for fname in list(offsets.keys()):
        fpath = os.path.join(log_dir, fname)
        try:
            size = os.path.getsize(fpath)
            if offsets[fname] > size:
                log.warning(
                    f"Stale log offset for {fname}: stored={offsets[fname]}, "
                    f"file size={size}. Resetting to 0 to catch up on missed events."
                )
                offsets[fname] = 0
        except FileNotFoundError:
            log.warning(f"Log file {fname} gone — removing stale offset entry.")
            del offsets[fname]
        except Exception as e:
            log.warning(f"Could not validate offset for {fname}: {e}")


INGEST_URL = os.environ.get("CLAWMETRY_INGEST_URL", "https://ingest.clawmetry.com")
CONFIG_DIR = Path.home() / ".clawmetry"
CONFIG_FILE = CONFIG_DIR / "config.json"
STATE_FILE = CONFIG_DIR / "sync-state.json"
LOG_FILE = CONFIG_DIR / "sync.log"

POLL_INTERVAL = 15  # seconds between sync cycles
STREAM_INTERVAL = 2  # seconds between real-time stream pushes

# Adaptive heartbeat cadence (epic #775 — adaptive sync, PR 2/3).
# When a viewer has the cloud dashboard open, the cloud sets `viewer_active:
# true` on the heartbeat response and we tighten the loop so Telegram /
# tool / brain events appear in the cloud Brain tab in ~3s instead of up to
# 60s. When nobody is watching we drop back to the default 60s cadence to
# keep idle bandwidth + Cloud Run cost flat. Back-compat: a cloud that
# hasn't deployed PR 1 of the epic yet won't return the field, and the
# missing-field branch falls through to SLOW.
HEARTBEAT_INTERVAL_FAST = 3
HEARTBEAT_INTERVAL_SLOW = 60
BATCH_SIZE = (
    200  # events per encrypted POST (was 10; fewer HTTP requests = faster sync)
)
MAX_EVENTS_PER_CYCLE = (
    5000  # cap per sync cycle so initial sync doesn't block the main loop
)

CONFIG_DIR.mkdir(parents=True, exist_ok=True)
log = logging.getLogger("clawmetry-sync")
log.setLevel(logging.INFO)
if not log.handlers:
    _fmt = logging.Formatter("%(asctime)s [clawmetry-sync] %(levelname)s %(message)s")
    # Detect if stdout is already redirected to our log file (e.g. launchd).
    # In that case, only use StreamHandler to avoid duplicate lines.
    _stdout_is_log = False
    try:
        import os as _os

        if hasattr(sys.stdout, "fileno"):
            _stdout_is_log = (
                _os.path.samefile(
                    _os.fstat(sys.stdout.fileno()).st_ino
                    and f"/proc/self/fd/{sys.stdout.fileno()}"
                    or "",
                    str(LOG_FILE),
                )
                if _os.path.exists(str(LOG_FILE))
                else False
            )
    except Exception:
        try:
            _stdout_stat = _os.fstat(sys.stdout.fileno())
            _log_stat = _os.stat(str(LOG_FILE))
            _stdout_is_log = (
                _stdout_stat.st_dev == _log_stat.st_dev
                and _stdout_stat.st_ino == _log_stat.st_ino
            )
        except Exception:
            pass
    _sh = logging.StreamHandler(sys.stdout)
    _sh.setFormatter(_fmt)
    log.addHandler(_sh)
    if not _stdout_is_log:
        try:
            _fh = logging.FileHandler(str(LOG_FILE), encoding="utf-8")
            _fh.setFormatter(_fmt)
            log.addHandler(_fh)
        except Exception:
            pass
    log.propagate = False


# ── Daemon-error → DuckDB event handler (PRD #1133 layer 4, daemon side) ────
#
# Why: PR #1139 surfaced daemon errors on the System Health card by parsing
# ``~/.clawmetry/sync.log`` text on every /api/system-health call — a clear
# violation of the DuckDB-first rule (memory feedback_duckdb_first_rule.md).
# This handler tees every ERROR-level log line into a structured
# ``daemon.error`` event row in the local DuckDB so the read side can do a
# single indexed query instead of re-tailing the log on each request.
#
# Rate-limit: at most one row per (first-80-chars-of-message, 60s bucket).
# Important because the original ALERTS_EVAL_INTERVAL_SEC NameError fired
# 4×/min on every install, and we don't want that pattern to spam DuckDB
# 5,760 rows/day when one row/minute carries the same signal.
#
# Failure mode: any exception inside the handler is swallowed and counted —
# the daemon must never crash because telemetry plumbing broke.

import uuid as _uuid
import socket as _socket

_DAEMON_ERROR_AGENT_ID = "clawmetry-daemon"
_DAEMON_ERROR_AGENT_TYPE = "clawmetry"
_DAEMON_ERROR_EVENT_TYPE = "daemon.error"
_DAEMON_ERROR_DEDUP_PREFIX_LEN = 80
_DAEMON_ERROR_DEDUP_BUCKET_SEC = 60


class _DaemonErrorDuckDBHandler(logging.Handler):
    """Logging handler that mirrors ERROR records into DuckDB ``events``.

    One row per (message-prefix, 60-second-bucket) — repeated identical
    errors within the bucket are dropped so a 4×/min NameError doesn't
    flood the table. The cap is enforced in-memory; we don't query
    DuckDB to dedup (would defeat the point).
    """

    def __init__(self) -> None:
        super().__init__(level=logging.ERROR)
        # Map[prefix → last-emitted-bucket]. Single-process daemon, so a
        # plain dict guarded by a Lock is fine. Bounded eviction below
        # keeps memory flat under pathological churn.
        self._last_emit: dict[str, int] = {}
        self._lock = threading.Lock()
        self._dropped = 0
        self._emitted = 0
        self._node_id_cache: str | None = None

    def _node_id(self) -> str:
        if self._node_id_cache:
            return self._node_id_cache
        try:
            cfg = load_config()
            nid = cfg.get("node_id") or _socket.gethostname() or "unknown"
        except Exception:
            nid = _socket.gethostname() or "unknown"
        self._node_id_cache = str(nid)
        return self._node_id_cache

    def _should_emit(self, msg: str, now_ts: float) -> bool:
        """Return True iff this prefix hasn't been emitted in the current
        60-second bucket. Updates the bookkeeping atomically."""
        prefix = (msg or "")[:_DAEMON_ERROR_DEDUP_PREFIX_LEN]
        bucket = int(now_ts // _DAEMON_ERROR_DEDUP_BUCKET_SEC)
        with self._lock:
            last = self._last_emit.get(prefix)
            if last == bucket:
                self._dropped += 1
                return False
            self._last_emit[prefix] = bucket
            # Bounded eviction — keep the table from growing unbounded if
            # a misbehaving caller logs millions of unique error messages.
            if len(self._last_emit) > 1024:
                # Drop entries older than 2 buckets (~120s).
                stale_cutoff = bucket - 2
                for k in [k for k, v in self._last_emit.items() if v < stale_cutoff]:
                    del self._last_emit[k]
            return True

    def emit(self, record: logging.LogRecord) -> None:  # noqa: D401
        try:
            if record.levelno < logging.ERROR:
                return
            try:
                msg = record.getMessage()
            except Exception:
                msg = str(getattr(record, "msg", ""))
            now_ts = time.time()
            if not self._should_emit(msg, now_ts):
                return

            exc_str: str | None = None
            if record.exc_info:
                try:
                    exc_str = logging.Formatter().formatException(record.exc_info)
                except Exception:
                    exc_str = None

            from clawmetry import local_store as _ls
            store = _ls.get_store()
            event = {
                "id": _uuid.uuid4().hex,
                "agent_id": _DAEMON_ERROR_AGENT_ID,
                "agent_type": _DAEMON_ERROR_AGENT_TYPE,
                "node_id": self._node_id(),
                "event_type": _DAEMON_ERROR_EVENT_TYPE,
                "ts": datetime.now(timezone.utc).isoformat(),
                "data": {
                    "message": (msg or "")[:1000],
                    "exception": (exc_str or "")[:2000] if exc_str else None,
                    "logger": record.name,
                },
            }
            store.ingest(event)
            self._emitted += 1
        except Exception:
            # Never raise from a logging handler — would break the daemon's
            # own error logging.
            try:
                self._dropped += 1
            except Exception:
                pass


def install_daemon_error_event_handler(logger: logging.Logger | None = None) -> _DaemonErrorDuckDBHandler | None:
    """Attach the DuckDB-mirroring handler to the daemon logger.

    Idempotent: re-running won't add a second handler. Returns the handler
    instance (so tests can introspect ``_emitted`` / ``_dropped``) or None
    when installation fails — the daemon should keep running either way.
    """
    target = logger if logger is not None else log
    for h in target.handlers:
        if isinstance(h, _DaemonErrorDuckDBHandler):
            return h  # type: ignore[return-value]
    try:
        h = _DaemonErrorDuckDBHandler()
        target.addHandler(h)
        return h
    except Exception as e:  # pragma: no cover — defensive
        try:
            log.warning("install_daemon_error_event_handler failed: %s", e)
        except Exception:
            pass
        return None


# ── Encryption (AES-256-GCM) ─────────────────────────────────────────────────


def generate_encryption_key() -> str:
    """Generate a new 256-bit key. Returns base64url string."""
    return base64.urlsafe_b64encode(secrets.token_bytes(32)).decode()


def _normalize_encryption_key(key_str: str) -> str:
    """Ensure key is a valid base64url AES key. If not, derive one via SHA-256."""
    import hashlib as _hl_norm

    try:
        raw = base64.urlsafe_b64decode(key_str + "==")
        if len(raw) in (16, 24, 32):
            return key_str
    except Exception:
        pass
    derived = _hl_norm.sha256(key_str.encode()).digest()
    return base64.urlsafe_b64encode(derived).decode().rstrip("=")


def _get_aesgcm(key_b64: str):
    """Return an AESGCM cipher from a base64url key (auto-derives if passphrase)."""
    try:
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM

        key_b64 = _normalize_encryption_key(key_b64)
        raw = base64.urlsafe_b64decode(key_b64 + "==")
        return AESGCM(raw)
    except ImportError:
        raise RuntimeError(
            "E2E encryption requires the 'cryptography' package.\n"
            "  pip install cryptography"
        )


def encrypt_payload(data: dict, key_b64: str) -> str:
    """
    Encrypt a dict as AES-256-GCM.
    Returns base64url(nonce || ciphertext) — a single opaque string.
    Cloud stores this blob and never sees plaintext.
    """
    cipher = _get_aesgcm(key_b64)
    nonce = secrets.token_bytes(12)  # 96-bit nonce (GCM standard)
    plain = json.dumps(data).encode()
    ct = cipher.encrypt(nonce, plain, None)
    return base64.urlsafe_b64encode(nonce + ct).decode()


def decrypt_payload(blob: str, key_b64: str) -> dict:
    """Decrypt a blob produced by encrypt_payload. Used by clients."""
    cipher = _get_aesgcm(key_b64)
    raw = base64.urlsafe_b64decode(blob + "==")
    nonce, ct = raw[:12], raw[12:]
    return json.loads(cipher.decrypt(nonce, ct, None))


# ── Sync DLQ for AES-GCM encryption failures (#1601) ────────────────────────
# When ``encrypt_payload`` raises inside a write-path POST (rare: corrupt key,
# key rotation race, payload contains non-JSON-serialisable bytes), the
# affected batch is parked in the local DuckDB ``sync_dlq`` table instead of
# being silently dropped. The replay loop (``_dlq_replay``) drains the queue
# on each sync tick. Persistent across daemon restarts.
#
# Metric: ``sync_encryption_failures`` (process-local counter) exposed via
# ``get_encryption_failure_count`` for dashboards / health probes.

_ENCRYPTION_FAILURE_COUNT = 0
_DLQ_MAX_ATTEMPTS = int(os.environ.get("CLAWMETRY_SYNC_DLQ_MAX_ATTEMPTS", "10"))
_DLQ_REPLAY_BATCH = int(os.environ.get("CLAWMETRY_SYNC_DLQ_REPLAY_BATCH", "50"))


def get_encryption_failure_count() -> int:
    """Return the process-local count of AES-GCM encryption failures
    encountered during write-path sync. Reset on daemon restart; for a
    durable count consult ``sync_dlq`` row count via local_store.health()."""
    return _ENCRYPTION_FAILURE_COUNT


def _dlq_enqueue_encryption_failure(
    *,
    kind: str,
    endpoint: str,
    payload: dict,
    fname: str | None = None,
    node_id: str | None = None,
    subagent_id: str | None = None,
    error: str = "",
) -> None:
    """Persist a payload that failed AES-GCM encryption. Best-effort: if the
    local store itself is unavailable we re-raise so the caller can log."""
    global _ENCRYPTION_FAILURE_COUNT
    _ENCRYPTION_FAILURE_COUNT += 1
    # Stable id: node + fname + first/last event ids if available, else hash.
    # Makes enqueue idempotent if the same batch fails encryption twice
    # before the replayer drains the queue.
    try:
        body = json.dumps(payload, sort_keys=True, default=str)
    except Exception:
        # If even the json dump fails the payload is unrecoverable for cloud;
        # stash a stringified repr so the user has *something* to debug.
        body = repr(payload)
    dlq_id = (
        f"{kind}:{node_id or 'n'}:{fname or 'f'}:"
        f"{__import__('hashlib').sha256(body.encode('utf-8', 'replace')).hexdigest()[:16]}"
    )
    from clawmetry import local_store as _ls
    store = _ls.get_store()
    store.dlq_enqueue(
        dlq_id=dlq_id,
        kind=kind,
        endpoint=endpoint,
        payload_json=body,
        fname=fname,
        node_id=node_id,
        subagent_id=subagent_id,
        error=error,
    )


def _dlq_replay(api_key: str, enc_key: str | None) -> int:
    """Drain the sync DLQ. Returns the number of rows successfully replayed.
    Handles both encryption_failure rows (re-encrypt + POST, requires enc_key)
    and post_failure rows (retry the cloud POST, with or without encryption).
    Called from the sync loop on every tick; cheap no-op when queue is empty."""
    try:
        from clawmetry import local_store as _ls
        store = _ls.get_store()
    except Exception:
        return 0
    try:
        rows = store.dlq_list(limit=_DLQ_REPLAY_BATCH)
    except Exception as _e:
        log.debug("dlq_replay: dlq_list failed (continuing): %s", _e)
        return 0
    if not rows:
        return 0
    replayed = 0
    for row in rows:
        dlq_id = row["id"]
        is_post_failure = row.get("kind") == "post_failure"
        # Encryption-failure rows need enc_key to re-encrypt; defer them until
        # the user restores the key. post_failure rows can replay without it.
        if not enc_key and not is_post_failure:
            continue
        if row["attempts"] >= _DLQ_MAX_ATTEMPTS:
            # Abandon rather than spin forever on a permanently-poisoned row.
            log.error(
                "sync_dlq: abandoning %s after %d attempts (last err: see DLQ row)",
                dlq_id, row["attempts"],
            )
            try:
                store.dlq_delete(dlq_id)
            except Exception:
                pass
            continue
        try:
            payload = json.loads(row["payload_json"])
        except Exception as _e:
            log.warning("sync_dlq: payload not valid JSON for %s — dropping: %s",
                        dlq_id, _e)
            try:
                store.dlq_delete(dlq_id)
            except Exception:
                pass
            continue
        if enc_key:
            try:
                blob = encrypt_payload(payload, enc_key)
            except Exception as _enc_e:
                try:
                    store.dlq_mark_attempt(dlq_id, str(_enc_e))
                except Exception:
                    pass
                continue  # Still bad key — try next row, leave this one parked.
            try:
                _post(
                    row["endpoint"],
                    {"node_id": row["node_id"], "encrypted": True, "blob": blob},
                    api_key,
                )
            except Exception as _post_e:
                try:
                    store.dlq_mark_attempt(dlq_id, f"post: {_post_e}")
                except Exception:
                    pass
                continue
        else:
            # post_failure row with no encryption configured — replay as plain POST.
            try:
                _post(row["endpoint"], payload, api_key)
            except Exception as _post_e:
                try:
                    store.dlq_mark_attempt(dlq_id, f"post: {_post_e}")
                except Exception:
                    pass
                continue
        try:
            store.dlq_delete(dlq_id)
        except Exception:
            pass
        replayed += 1
    if replayed:
        log.info("sync_dlq: replayed %d parked batch(es) to cloud", replayed)
    return replayed


# ── Config ─────────────────────────────────────────────────────────────────────


def load_config() -> dict:
    if not CONFIG_FILE.exists():
        raise FileNotFoundError(f"No config at {CONFIG_FILE}. Run: clawmetry connect")
    return json.loads(CONFIG_FILE.read_text())


def save_config(data: dict) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(json.dumps(data, indent=2))
    CONFIG_FILE.chmod(0o600)


def load_state() -> dict:
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text())
        except Exception:
            pass
    return {"last_event_ids": {}, "last_log_offsets": {}, "last_sync": None}


def save_state(state: dict) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, indent=2))


# ── Initial-sync progress (vivekchand/clawmetry#748) ─────────────────────────
# Tracks per-phase progress to ~/.clawmetry/sync_progress.json so the local
# dashboard can show a "syncing…" banner on fresh installs instead of empty
# tabs. Written atomically (tmp + rename) because the dashboard reads this
# file on every banner poll.
SYNC_PROGRESS_FILE = CONFIG_DIR / "sync_progress.json"
_sync_progress_started_at: str | None = None


def _record_sync_progress(
    phase: str, done: int, total: int = 0, status: str = "running"
) -> None:
    global _sync_progress_started_at
    try:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        now = datetime.now(timezone.utc).isoformat()
        if _sync_progress_started_at is None:
            _sync_progress_started_at = now
        try:
            cfg = load_config()
            node_id = cfg.get("node_id", "")
        except Exception:
            node_id = ""
        payload = {
            "node_id": node_id,
            "phase": phase,
            "done": int(done),
            "total": int(total),
            "status": status,
            "started_at": _sync_progress_started_at,
            "updated_at": now,
        }
        tmp = SYNC_PROGRESS_FILE.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(payload, indent=2))
        os.replace(tmp, SYNC_PROGRESS_FILE)
    except Exception as e:
        log.debug(f"Could not record sync progress ({phase}): {e}")


# ── HTTP ──────────────────────────────────────────────────────────────────────


# ── HTTP retry policy (MOAT robustness, 2026-05-19) ──────────────────────────
# All retryable failures (network flap, Cloud Run cold start, PgBouncer
# restart returning 5xx, transient 429) are retried up to 4 times with
# exponential backoff + jitter. Total worst-case wait: ~12s. After that the
# caller's exception handler parks the payload in sync_dlq for the next tick.
#
# Retry budget (seconds, with ~25% jitter):
#   attempt 1 fail -> sleep ~1s
#   attempt 2 fail -> sleep ~2s
#   attempt 3 fail -> sleep ~4s
#   attempt 4 fail -> sleep ~8s
#   attempt 5 fail -> raise (caller parks in DLQ)
#
# Retryable status codes:
#   401 - cloud cold start (auth lookup races deploy)
#   408 - request timeout
#   425 - too early (very rare)
#   429 - rate limit (honors Retry-After header up to 60s cap)
#   500, 502, 503, 504 - cloud transient (PgBouncer restart, cold start)
#
# Non-retryable: 400, 403, 404, 409, 410, 413, 422 (client error, bad payload,
# unknown endpoint). Raising immediately surfaces the bug rather than burning
# the retry budget on a permanently-broken request.
#
# Network errors (URLError, socket.timeout, ConnectionResetError) are always
# retryable; they're indistinguishable from a transient cloud hiccup.

_HTTP_RETRYABLE_CODES = frozenset({401, 408, 425, 429, 500, 502, 503, 504})
_HTTP_MAX_ATTEMPTS = int(os.environ.get("CLAWMETRY_SYNC_HTTP_MAX_ATTEMPTS", "5"))
_HTTP_BASE_BACKOFF_S = float(os.environ.get("CLAWMETRY_SYNC_HTTP_BASE_BACKOFF_S", "1.0"))
_HTTP_MAX_BACKOFF_S = float(os.environ.get("CLAWMETRY_SYNC_HTTP_MAX_BACKOFF_S", "30.0"))
_HTTP_RETRY_AFTER_CAP_S = 60.0


def _compute_backoff(attempt: int, retry_after_hdr: str | None = None) -> float:
    """Exponential backoff with ~25% jitter; honors Retry-After header.

    ``attempt`` is 1-indexed (first failed attempt = 1). Returns the
    number of seconds to sleep before the next retry. Capped at
    ``_HTTP_MAX_BACKOFF_S`` so a server with a 24h Retry-After hint
    doesn't stall the daemon for a day.
    """
    if retry_after_hdr:
        try:
            # RFC 7231 lets Retry-After be either a delta in seconds or an
            # HTTP-date. We only honor the seconds form; daemons should not
            # block waiting for an absolute timestamp.
            ra = float(retry_after_hdr.strip())
            return min(max(0.0, ra), _HTTP_RETRY_AFTER_CAP_S)
        except (ValueError, TypeError):
            pass
    # 2^(attempt-1) * base, jittered by [-25%, +25%].
    base = _HTTP_BASE_BACKOFF_S * (2 ** max(0, attempt - 1))
    jitter = base * 0.25 * (2 * random.random() - 1)
    return max(0.1, min(_HTTP_MAX_BACKOFF_S, base + jitter))


def _post(path: str, payload: dict, api_key: str, timeout: int = 45) -> dict:
    """POST a payload to the cloud ingest endpoint.

    Hardening (MOAT 2026-05-19):
      * Up to ``_HTTP_MAX_ATTEMPTS`` retries on transient HTTP codes
        (401, 408, 425, 429, 5xx) and any network-level error
        (URLError, socket.timeout, ConnectionResetError, BrokenPipeError).
      * Exponential backoff with ~25% jitter; honors the server's
        ``Retry-After`` header (seconds form only, capped at 60s).
      * 429 still updates ``_TRIAL_STATE`` so subsequent calls short-
        circuit before paying the network round-trip, but we now retry
        the 429 itself so a transient throttle (e.g. a fleet-wide
        spike) doesn't immediately abandon the payload to the DLQ.
      * Client errors (400, 403, 404, 409, 410, 413, 422) raise
        immediately — burning retries on a permanently-broken request
        wastes the daemon's budget and delays the next legitimate call.
    """
    url = INGEST_URL.rstrip("/") + path
    body = json.dumps(payload).encode()
    headers = {"Content-Type": "application/json", "X-Api-Key": api_key}
    if payload.get("node_id"):
        headers["X-Node-Id"] = payload["node_id"]
    req = urllib.request.Request(
        url,
        data=body,
        headers=headers,
        method="POST",
    )
    last_err: Exception = RuntimeError(f"POST {url} never attempted")
    for attempt in range(1, _HTTP_MAX_ATTEMPTS + 1):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                resp_body = json.loads(resp.read())
            # Cloud heartbeat (and any other endpoint) may attach the user's
            # plan / sync_allowed / trial_days_left / upgrade_url. We mirror
            # those into _TRIAL_STATE so subsequent uploads can self-throttle
            # before paying the network round-trip. Best-effort: missing
            # fields leave the cache untouched.
            if isinstance(resp_body, dict) and "sync_allowed" in resp_body:
                _update_trial_state(resp_body)
            return resp_body
        except urllib.error.HTTPError as e:
            code = e.code
            try:
                msg = e.read().decode()[:200]
            except Exception:
                msg = ""
            retry_after_hdr = None
            try:
                retry_after_hdr = e.headers.get("Retry-After") if e.headers else None
            except Exception:
                retry_after_hdr = None
            last_err = RuntimeError(f"HTTP {code} from {url}: {msg}")
            # 429: cache the plan-paused signal so further calls short-circuit,
            # then fall through into the retryable branch below.
            if code == 429:
                try:
                    plan = json.loads(msg).get("plan", "") if msg else ""
                except Exception:
                    plan = ""
                _update_trial_state({
                    "sync_allowed": False,
                    "plan": plan or "trial_expired",
                    "upgrade_url": "https://app.clawmetry.com/cloud",
                })
            if code in _HTTP_RETRYABLE_CODES and attempt < _HTTP_MAX_ATTEMPTS:
                sleep_s = _compute_backoff(attempt, retry_after_hdr)
                log.debug(
                    "sync._post: %s returned %d (attempt %d/%d) — retrying in %.1fs",
                    path, code, attempt, _HTTP_MAX_ATTEMPTS, sleep_s,
                )
                time.sleep(sleep_s)
                continue
            raise last_err
        except (urllib.error.URLError, TimeoutError, ConnectionError,
                BrokenPipeError, OSError) as e:
            # Network-level error: DNS failure, connection reset, TLS error,
            # socket timeout, broken pipe (PgBouncer killed the connection
            # mid-write). All retryable; the daemon can't distinguish a
            # cloud cold start from a real outage.
            last_err = RuntimeError(f"network error POSTing {url}: {e}")
            if attempt < _HTTP_MAX_ATTEMPTS:
                sleep_s = _compute_backoff(attempt, None)
                log.debug(
                    "sync._post: %s network error (attempt %d/%d) — retrying in %.1fs: %s",
                    path, attempt, _HTTP_MAX_ATTEMPTS, sleep_s, e,
                )
                time.sleep(sleep_s)
                continue
            raise last_err
    raise last_err


# ── Client-side trial gating ────────────────────────────────────────────────
# Cloud /ingest/heartbeat returns {plan, sync_allowed, trial_days_left,
# upgrade_url} on every beat. We cache it here so:
#   - Large blob uploads (events / snapshots / memory / sessions / logs /
#     autonomy) skip themselves when sync_allowed=False, saving bandwidth.
#   - Heartbeats and approvals/alerts polls KEEP firing so the daemon
#     detects the moment the user upgrades (sync_allowed flips True →
#     uploads resume automatically, no daemon restart needed).
#   - A clear "upgrade to resume" log line prints once per UTC day so the
#     user knows why their dashboard stopped updating.

_TRIAL_STATE = {
    "sync_allowed": True,    # default: assume allowed until cloud says otherwise
    "plan": None,
    "trial_days_left": None,
    "upgrade_url": "https://app.clawmetry.com/cloud",
    "last_log_day": "",     # YYYY-MM-DD of the last "sync paused" log
}


def _update_trial_state(resp: dict) -> None:
    """Mirror plan info from a cloud response into the local cache + log
    a one-line "upgrade to resume" message once per UTC day on transition."""
    prev_allowed = _TRIAL_STATE["sync_allowed"]
    new_allowed = bool(resp.get("sync_allowed", True))
    _TRIAL_STATE["sync_allowed"] = new_allowed
    if "plan" in resp:
        _TRIAL_STATE["plan"] = resp.get("plan")
    if "trial_days_left" in resp:
        _TRIAL_STATE["trial_days_left"] = resp.get("trial_days_left")
    if resp.get("upgrade_url"):
        _TRIAL_STATE["upgrade_url"] = resp["upgrade_url"]
    reason = (resp.get("reason") or "").strip()
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    if not new_allowed and _TRIAL_STATE["last_log_day"] != today:
        _TRIAL_STATE["last_log_day"] = today
        if reason == "intent_pending":
            # KiloClaw / similar auto-provisioned flows. The user hasn't
            # asked to view their dashboard yet, so we heartbeat (so the
            # cloud knows we're alive) but upload nothing else. The moment
            # they click "View Observability", the heartbeat response
            # flips and uploads resume — no daemon restart needed.
            log.info(
                "Cloud sync deferred — waiting for the user to open their "
                "dashboard. Heartbeats continue; no sessions / events / "
                "logs / memory will leave this machine until then."
            )
        else:
            log.warning(
                "⚠ Trial expired (plan=%s). Cloud sync paused — heartbeats "
                "continue so we detect the moment you upgrade. Upgrade to Pro at "
                "%s to resume event/session/memory sync.",
                _TRIAL_STATE["plan"], _TRIAL_STATE["upgrade_url"],
            )
    elif new_allowed and not prev_allowed:
        if reason == "intent_started" or _TRIAL_STATE.get("plan") in (None, "free", "trial"):
            log.info("✓ Cloud sync activated — uploads resumed.")
        else:
            log.info(
                "✓ Pro plan detected (plan=%s). Cloud sync resumed.",
                _TRIAL_STATE["plan"],
            )


def _sync_allowed() -> bool:
    """Gate for large blob uploads. Heartbeats + approvals/alerts polls
    bypass this — they MUST keep firing so we detect the upgrade (or, for
    KiloClaw-provisioned accounts, the moment the user clicks "View
    Observability" and the cloud flips reason='intent_pending' off)."""
    return _TRIAL_STATE.get("sync_allowed", True)


def get_machine_id() -> str:
    """Generate a stable hardware fingerprint for this machine."""
    import hashlib, platform

    mid = ""
    # macOS: IOPlatformUUID (stable across reboots/reinstalls)
    if platform.system() == "Darwin":
        try:
            import subprocess

            out = subprocess.check_output(
                ["ioreg", "-rd1", "-c", "IOPlatformExpertDevice"],
                timeout=5,
                stderr=subprocess.DEVNULL,
            ).decode()
            for line in out.splitlines():
                if "IOPlatformUUID" in line:
                    mid = line.split('"')[-2]
                    break
        except Exception:
            pass
    # Linux: /etc/machine-id
    if not mid:
        # In Docker containers, /etc/machine-id is identical across clones
        # Use cgroup inode as container-specific fallback
        if _is_running_in_container():
            try:
                import stat

                st = os.stat("/proc/1")
                mid = f"container-{st.st_ino}"
            except Exception:
                pass
        if not mid:
            for path in ["/etc/machine-id", "/var/lib/dbus/machine-id"]:
                try:
                    with open(path) as f:
                        mid = f.read().strip()
                        if mid:
                            break
                except Exception:
                    pass
    # Windows: WMIC
    if not mid and platform.system() == "Windows":
        try:
            import subprocess

            out = subprocess.check_output(
                ["wmic", "csproduct", "get", "uuid"],
                timeout=5,
                stderr=subprocess.DEVNULL,
            ).decode()
            lines = [
                l.strip() for l in out.splitlines() if l.strip() and l.strip() != "UUID"
            ]
            if lines:
                mid = lines[0]
        except Exception:
            pass
    # Fallback: MAC address (less stable but better than nothing)
    if not mid:
        import uuid as _uuid_mod

        mid = str(_uuid_mod.getnode())
    return hashlib.sha256(mid.encode()).hexdigest()[:32]


def validate_key(
    api_key: str, hostname: str = "", existing_node_id: str = "", **kwargs
) -> dict:
    payload = {"api_key": api_key}
    if hostname:
        payload["hostname"] = hostname
    if existing_node_id:
        payload["existing_node_id"] = existing_node_id
    payload["machine_id"] = get_machine_id()
    return _post("/auth", payload, api_key)


# ── Path detection ─────────────────────────────────────────────────────────────


def _find_openclaw_dirs(root, max_depth=4):
    """Search a directory tree for OpenClaw sessions and workspace dirs."""
    sessions_dir = None
    workspace_dir = None
    try:
        for dirpath, dirnames, filenames in os.walk(root):
            depth = dirpath.replace(root, "").count(os.sep)
            if depth > max_depth:
                dirnames.clear()
                continue
            # Skip noisy dirs
            base = os.path.basename(dirpath)
            if base in ("node_modules", ".git", "__pycache__", "venv", ".venv"):
                dirnames.clear()
                continue
            if dirpath.endswith(
                os.sep + "agents" + os.sep + "main" + os.sep + "sessions"
            ) or dirpath.endswith("/agents/main/sessions"):
                if not sessions_dir:
                    sessions_dir = dirpath
                    log.info(f"  Found sessions: {dirpath}")
            if os.path.basename(dirpath) == "workspace" and os.path.isfile(
                os.path.join(dirpath, "AGENTS.md")
            ):
                if not workspace_dir:
                    workspace_dir = dirpath
                    log.info(f"  Found workspace: {dirpath}")
            if sessions_dir and workspace_dir:
                break
    except PermissionError:
        pass
    return sessions_dir, workspace_dir


def _is_running_in_container() -> bool:
    """Detect whether ClawMetry itself is running inside a Docker/OpenShell container."""
    # Check for /.dockerenv (present in Docker containers)
    if os.path.exists("/.dockerenv"):
        return True
    # Check cgroup for container indicators
    try:
        with open("/proc/1/cgroup", "r") as f:
            cgroup = f.read()
        if any(
            k in cgroup
            for k in ("docker", "kubepods", "containerd", "lxc", "opencontainer")
        ):
            return True
    except Exception:
        pass
    return False


def _detect_nemoclaw() -> dict:
    """Detect NemoClaw (NVIDIA's OpenClaw wrapper) presence on the host.

    Returns a dict with fields:
      detected (bool), binary (str), version (str),
      sandbox_name (str), sandbox_status (str), sandbox_type (str),
      inference_provider (str), inference_model (str),
      security_sandbox_enabled (bool), security_network_policy (bool)
    """
    import subprocess, shutil

    result: dict = {"detected": False}

    # 1. Check for the nemoclaw binary
    nemo_bin = shutil.which("nemoclaw")
    if not nemo_bin:
        for candidate in [
            "/usr/local/bin/nemoclaw",
            "/opt/nemoclaw/bin/nemoclaw",
            "/usr/bin/nemoclaw",
        ]:
            if os.path.isfile(candidate):
                nemo_bin = candidate
                break

    if not nemo_bin:
        # Also accept NEMOCLAW_SANDBOX env as a hint even without binary
        if not os.environ.get("NEMOCLAW_SANDBOX"):
            return result

    result["detected"] = True
    result["binary"] = nemo_bin or "(env-only)"

    # 2. Get version
    if nemo_bin:
        try:
            ver = (
                subprocess.check_output(
                    [nemo_bin, "--version"], stderr=subprocess.DEVNULL, timeout=5
                )
                .decode()
                .strip()
            )
            result["version"] = ver
        except Exception:
            result["version"] = "unknown"

    # 3. Collect sandbox status via `nemoclaw status`
    sandbox_name = os.environ.get("NEMOCLAW_SANDBOX", "")
    result["sandbox_name"] = sandbox_name
    result["sandbox_type"] = "nemoclaw"
    result["security_sandbox_enabled"] = True
    result["security_network_policy"] = True

    if nemo_bin:
        try:
            status_out = subprocess.check_output(
                [nemo_bin, "status", "--json"]
                + ([sandbox_name] if sandbox_name else []),
                stderr=subprocess.DEVNULL,
                timeout=10,
            ).decode()
            import json as _j

            status_data = _j.loads(status_out)
            result["sandbox_status"] = status_data.get("status", "unknown")
            result["inference_provider"] = status_data.get("inferenceProvider", "")
            result["inference_model"] = status_data.get("inferenceModel", "")
            if not sandbox_name:
                result["sandbox_name"] = status_data.get("name", "")
        except Exception:
            result["sandbox_status"] = "unknown"
            result["inference_provider"] = ""
            result["inference_model"] = ""
    else:
        result["sandbox_status"] = "unknown"
        result["inference_provider"] = ""
        result["inference_model"] = ""

    # 4. Try `openshell sandbox list` as alternative discovery
    openshell_bin = _find_openshell_bin()
    if openshell_bin and not result.get("sandbox_name"):
        try:
            import json as _j

            sb_out = subprocess.check_output(
                [openshell_bin, "sandbox", "list", "--json"],
                stderr=subprocess.DEVNULL,
                timeout=10,
            ).decode()
            sandboxes = _j.loads(sb_out)
            for sb in sandboxes if isinstance(sandboxes, list) else []:
                if any(
                    k in (sb.get("image", "") + sb.get("name", "")).lower()
                    for k in ("openclaw", "clawd", "nemoclaw")
                ):
                    result["sandbox_name"] = sb.get("name", "")
                    result["sandbox_status"] = sb.get("status", "unknown")
                    break
        except Exception:
            pass

    return result


def _find_openshell_bin() -> str | None:
    """Find the openshell CLI binary."""
    import shutil

    for name in ("openshell", "openshell-cli"):
        p = shutil.which(name)
        if p:
            return p
    for candidate in [
        "/usr/local/bin/openshell",
        "/opt/openshell/bin/openshell",
        "/usr/bin/openshell",
    ]:
        if os.path.isfile(candidate):
            return candidate
    return None


def _detect_docker_openclaw() -> dict:
    """Auto-detect OpenClaw running in Docker and find its data paths on the host.

    Detects both standard OpenClaw containers and NemoClaw/OpenShell sandboxes
    (ghcr.io/nvidia/openshell-community/* images).
    """
    import subprocess, json as _json

    result = {}
    try:
        # Find containers with openclaw/clawd/nemoclaw/openshell/nvidia in name or image
        out = subprocess.run(
            [
                "docker",
                "ps",
                "--format",
                "{{.ID}}\t{{.Names}}\t{{.Image}}\t{{.Mounts}}",
            ],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if out.returncode != 0:
            return {}
        for line in out.stdout.strip().splitlines():
            parts = line.split("\t")
            if len(parts) < 3:
                continue
            cid, name, image = parts[0], parts[1], parts[2]
            if not any(
                k in (name + image).lower()
                for k in [
                    "openclaw",
                    "clawd",
                    "claw",
                    "nemoclaw",
                    "openshell",
                    "nvidia",
                ]
            ):
                continue

            # Determine runtime: nemoclaw/openshell vs plain docker
            is_nemoclaw = any(
                k in (name + image).lower() for k in ("nemoclaw", "openshell", "nvidia")
            )
            runtime_tag = "nemoclaw" if is_nemoclaw else "docker"
            log.info(f"Found {runtime_tag} container: {name} ({image}) id={cid}")

            # NemoClaw sessions live at /sandbox/.openclaw/ inside the container
            # Plain OpenClaw containers use /root/.openclaw or /data
            nemoclaw_paths = ["/sandbox/.openclaw", "/sandbox/agents/main/sessions"]
            standard_paths = ["/root/.openclaw", "/data", "/app"]
            preferred_paths = (
                (nemoclaw_paths + standard_paths) if is_nemoclaw else standard_paths
            )

            # Get volume mounts via docker inspect
            try:
                insp = subprocess.run(
                    ["docker", "inspect", "--format", "{{json .Mounts}}", cid],
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                mounts = (
                    _json.loads(insp.stdout.strip()) if insp.returncode == 0 else []
                )
                for m in mounts:
                    src = m.get("Source", "")
                    dst = m.get("Destination", "")
                    # Look for data/workspace/sessions mounts
                    if (
                        "agents" in dst
                        or "sessions" in dst
                        or "/data" == dst
                        or "openclaw" in dst.lower()
                        or "/sandbox" in dst
                    ):
                        log.info(f"  Mount: {src} -> {dst}")
                        if "sessions" in dst:
                            result["sessions_dir"] = src
                        elif "agents" in dst:
                            result["sessions_dir"] = os.path.join(
                                src, "main", "sessions"
                            )
                        elif dst in (
                            "/data",
                            "/app",
                            "/home",
                            "/root",
                            "/opt",
                            "/sandbox",
                        ):
                            # Search mount point for sessions + workspace (up to 3 levels deep)
                            _found_s, _found_w = _find_openclaw_dirs(src)
                            if _found_s:
                                result["sessions_dir"] = _found_s
                            if _found_w:
                                result["workspace"] = _found_w
                    if "workspace" in dst:
                        result["workspace"] = src
                    if "logs" in dst or "tmp" in dst:
                        result["log_dir"] = src
            except Exception as e:
                log.debug(f"Docker inspect error: {e}")
            # If no volume mounts found, try docker exec to find paths
            if not result:
                try:
                    for check_path in preferred_paths:
                        sessions_path = (
                            f"{check_path}/agents/main/sessions"
                            if not check_path.endswith("sessions")
                            else check_path
                        )
                        chk = subprocess.run(
                            ["docker", "exec", cid, "ls", sessions_path],
                            capture_output=True,
                            text=True,
                            timeout=5,
                        )
                        if chk.returncode == 0 and chk.stdout.strip():
                            log.info(
                                f"  Found sessions inside container at {check_path}"
                            )
                            # Copy files out to host
                            mirror_subdir = (
                                "nemoclaw-mirror" if is_nemoclaw else "docker-mirror"
                            )
                            host_dir = Path.home() / ".clawmetry" / mirror_subdir
                            host_dir.mkdir(parents=True, exist_ok=True)
                            sessions_mirror = host_dir / "sessions"
                            workspace_mirror = host_dir / "workspace"
                            sessions_mirror.mkdir(exist_ok=True)
                            workspace_mirror.mkdir(exist_ok=True)
                            # rsync from container
                            subprocess.run(
                                [
                                    "docker",
                                    "cp",
                                    f"{cid}:{sessions_path}/.",
                                    str(sessions_mirror),
                                ],
                                capture_output=True,
                                timeout=30,
                            )
                            workspace_root = (
                                check_path
                                if check_path.endswith(".openclaw")
                                else os.path.dirname(check_path)
                            )
                            subprocess.run(
                                [
                                    "docker",
                                    "cp",
                                    f"{cid}:{workspace_root}/workspace/.",
                                    str(workspace_mirror),
                                ],
                                capture_output=True,
                                timeout=30,
                            )
                            # Copy logs
                            for log_path in ["/tmp/openclaw", f"{check_path}/logs"]:
                                subprocess.run(
                                    [
                                        "docker",
                                        "cp",
                                        f"{cid}:{log_path}/.",
                                        str(host_dir / "logs"),
                                    ],
                                    capture_output=True,
                                    timeout=15,
                                )
                            result["sessions_dir"] = str(sessions_mirror)
                            result["workspace"] = str(workspace_mirror)
                            result["log_dir"] = str(host_dir / "logs")
                            result["docker_container"] = cid
                            result["docker_path"] = check_path
                            result["container_id"] = cid
                            result["runtime"] = runtime_tag
                            log.info(f"  Mirrored {runtime_tag} data to {host_dir}")
                            break
                except Exception as e:
                    log.debug(f"Docker exec fallback error: {e}")
            if result:
                return result
    except FileNotFoundError:
        log.debug("Docker not installed or not in PATH")
    except Exception as e:
        log.debug(f"Docker detection error: {e}")
    return {}


def detect_paths() -> dict:
    Path.home()
    # Try Docker/NemoClaw container detection first
    docker_paths = _detect_docker_openclaw()
    if docker_paths.get("sessions_dir"):
        log.info(f"Using container-detected paths: {docker_paths}")

    sessions_candidates = [
        Path(_get_openclaw_dir()) / "agents" / "main" / "sessions",
        Path("/data/agents/main/sessions"),
        Path("/app/agents/main/sessions"),
        Path("/root/.openclaw/agents/main/sessions"),
        Path("/opt/openclaw/agents/main/sessions"),
        # NemoClaw/OpenShell sandbox paths (sessions live inside /sandbox)
        Path("/sandbox/.openclaw/agents/main/sessions"),
        Path("/sandbox/agents/main/sessions"),
    ]
    oc_home = os.environ.get("OPENCLAW_HOME", "")
    if oc_home:
        sessions_candidates.insert(0, Path(oc_home) / "agents" / "main" / "sessions")
    # Support explicit NemoClaw sandbox name via env var
    nemoclaw_sandbox = os.environ.get("NEMOCLAW_SANDBOX", "")
    if nemoclaw_sandbox:
        sessions_candidates.insert(
            0, Path(f"/sandbox/{nemoclaw_sandbox}/.openclaw/agents/main/sessions")
        )
        sessions_candidates.insert(
            1,
            Path(
                f"/var/lib/openshell/sandboxes/{nemoclaw_sandbox}/.openclaw/agents/main/sessions"
            ),
        )
    def _safe_exists(p):
        try:
            return p.exists()
        except (PermissionError, OSError):
            return False

    found_sessions = docker_paths.get("sessions_dir") or next(
        (str(p) for p in sessions_candidates if _safe_exists(p)), None
    )
    sessions_dir = found_sessions or str(sessions_candidates[0])

    if not found_sessions:
        log.warning("OpenClaw not detected — no session directories found.")
        log.warning("  Install: npm install -g openclaw  (https://openclaw.ai/docs)")
        log.warning("  Daemon will keep retrying every 60s.")
    else:
        # Warn if NemoClaw is detected and sync daemon appears to be inside the sandbox
        if _is_running_in_container():
            log.warning(
                "⚠️  NemoClaw/container detected: ClawMetry sync daemon appears to be running INSIDE the sandbox."
            )
            log.warning(
                "   Recommended: run the sync daemon on the HOST for unrestricted network access."
            )
            log.warning(
                "   If you must run inside the sandbox, add this to your NemoClaw network policy:"
            )
            log.warning("     network:")
            log.warning("       egress:")
            log.warning("         - host: ingest.clawmetry.com")
            log.warning("           port: 443")
            log.warning("           protocol: https")

    log_candidates = [
        Path("/tmp/openclaw"),
        Path(_get_openclaw_dir()) / "logs",
        Path("/data/logs"),
    ]
    log_dir = docker_paths.get("log_dir") or next(
        (str(p) for p in log_candidates if p.exists()), "/tmp/openclaw"
    )

    workspace_candidates = [
        Path(_get_openclaw_dir()) / "workspace",
        Path("/data/workspace"),
        Path("/app/workspace"),
    ]
    workspace = docker_paths.get("workspace") or next(
        (str(p) for p in workspace_candidates if p.exists()),
        str(workspace_candidates[0]),
    )

    log.info(f"Paths: sessions={sessions_dir} logs={log_dir} workspace={workspace}")
    return {"sessions_dir": sessions_dir, "log_dir": log_dir, "workspace": workspace}


def discover_workspaces(home: Path | None = None) -> list[dict]:
    """Discover all OpenClaw workspace profiles on this machine.

    Power users sometimes keep multiple OpenClaw workspaces (work / personal /
    experiments). Today ClawMetry auto-detects a single ``~/.openclaw`` dir;
    this helper scans for the common multi-profile patterns so the dashboard
    can offer a switcher.

    Discovery paths (all safe, no symlink-following, read-only):
      1. ``~/.openclaw`` — the canonical single-workspace location.
      2. ``~/.openclaw-*`` — suffix-style profiles (e.g. ``~/.openclaw-work``).
      3. ``~/.openclaw/profiles/<name>`` — explicit profiles convention.
      4. ``~/.clawmetry/workspaces.json`` — user-curated list (highest trust).

    A path is treated as a workspace when it contains an ``agents/`` or
    ``workspace/`` subdir or one of the conventional context files
    (``SOUL.md`` / ``AGENTS.md`` / ``MEMORY.md``). The check tolerates
    ``PermissionError`` and never crashes.

    Returns a list of ``{name, path, agent_count, last_active_ts}`` dicts,
    sorted by ``last_active_ts`` desc. The single-workspace zero-config
    case still works — it just returns a one-element list.
    """
    home = home or Path.home()
    discovered: dict[str, dict] = {}  # path -> entry (de-dup by abs path)

    def _is_workspace_like(p: Path) -> bool:
        try:
            if not p.is_dir() or p.is_symlink():
                return False
            # Strong signal: agents/ subdir (OpenClaw's standard layout)
            if (p / "agents").is_dir():
                return True
            if (p / "workspace").is_dir():
                return True
            for marker in ("SOUL.md", "AGENTS.md", "MEMORY.md"):
                if (p / marker).exists():
                    return True
        except (PermissionError, OSError):
            return False
        return False

    def _agent_count(p: Path) -> int:
        try:
            agents_dir = p / "agents"
            if not agents_dir.is_dir():
                return 0
            return sum(
                1
                for child in agents_dir.iterdir()
                if child.is_dir() and not child.is_symlink()
            )
        except (PermissionError, OSError):
            return 0

    def _last_active(p: Path) -> float:
        """Most-recent mtime across sessions/logs as a rough activity timestamp."""
        latest = 0.0
        try:
            sessions = p / "agents" / "main" / "sessions"
            if sessions.is_dir():
                for f in sessions.iterdir():
                    if f.is_symlink():
                        continue
                    try:
                        m = f.stat().st_mtime
                        if m > latest:
                            latest = m
                    except (PermissionError, OSError):
                        continue
            # Fallback: dir mtime
            if latest == 0.0:
                latest = p.stat().st_mtime
        except (PermissionError, OSError):
            pass
        return latest

    def _add(name: str, path: Path) -> None:
        try:
            abs_path = path.resolve(strict=False)
        except (OSError, RuntimeError):
            abs_path = path
        key = str(abs_path)
        if key in discovered:
            return
        if not _is_workspace_like(path):
            return
        discovered[key] = {
            "name": name,
            "path": key,
            "agent_count": _agent_count(path),
            "last_active_ts": _last_active(path),
        }

    # 1. Canonical ~/.openclaw
    default = home / ".openclaw"
    _add("default", default)

    # 2. Suffix-style profiles: ~/.openclaw-<name>
    try:
        for entry in home.iterdir():
            try:
                if entry.is_symlink() or not entry.is_dir():
                    continue
            except (PermissionError, OSError):
                continue
            name = entry.name
            if not name.startswith(".openclaw-"):
                continue
            profile = name[len(".openclaw-"):]
            if profile:
                _add(profile, entry)
    except (PermissionError, OSError, FileNotFoundError):
        pass

    # 3. ~/.openclaw/profiles/<name> convention
    profiles_dir = default / "profiles"
    try:
        if profiles_dir.is_dir() and not profiles_dir.is_symlink():
            for entry in profiles_dir.iterdir():
                try:
                    if entry.is_symlink() or not entry.is_dir():
                        continue
                except (PermissionError, OSError):
                    continue
                _add(entry.name, entry)
    except (PermissionError, OSError):
        pass

    # 4. User-curated ~/.clawmetry/workspaces.json
    cfg_path = home / ".clawmetry" / "workspaces.json"
    try:
        if cfg_path.is_file() and not cfg_path.is_symlink():
            with open(cfg_path) as f:
                cfg = json.load(f)
            entries = cfg.get("workspaces") if isinstance(cfg, dict) else cfg
            if isinstance(entries, list):
                for item in entries:
                    if not isinstance(item, dict):
                        continue
                    raw_path = item.get("path")
                    name = item.get("name") or ""
                    if not raw_path or not isinstance(raw_path, str):
                        continue
                    p = Path(os.path.expanduser(raw_path))
                    # Stay within the user's home dir as a safety boundary
                    # (don't follow paths outside ~ that the JSON might point at).
                    try:
                        rp = p.resolve(strict=False)
                    except (OSError, RuntimeError):
                        continue
                    try:
                        rp.relative_to(home.resolve(strict=False))
                    except ValueError:
                        # Allow explicit absolute paths outside home only when
                        # they exist & are not symlinks — power-user override.
                        if p.is_symlink():
                            continue
                    _add(name or p.name or "workspace", p)
    except (PermissionError, OSError, json.JSONDecodeError, ValueError):
        pass

    out = sorted(
        discovered.values(),
        key=lambda d: d.get("last_active_ts", 0.0),
        reverse=True,
    )
    return out


# ── Sync: session events (full content, encrypted) ────────────────────────────


def _list_session_jsonls(sessions_dir) -> list[str]:
    """Return all session transcript paths in sessions_dir.

    Includes both live `*.jsonl` and archived `*.jsonl.reset.<ts>` files.
    OpenClaw renames a session jsonl with a `.reset.<iso-ts>` suffix when
    the session is reset; the archive still holds real token usage and
    transcript content. Filtering by `endswith('.jsonl')` alone (the old
    behaviour) silently dropped every archived day's data from cloud,
    making the per-day Tokens chart pile every session onto today.
    """
    sessions_dir = str(sessions_dir)
    out: list[str] = []
    try:
        for fname in os.listdir(sessions_dir):
            if fname.endswith(".jsonl") or ".jsonl.reset." in fname:
                # Skip OpenClaw trace-artifact sidecars that live next to
                # real session files. Without this filter the daemon
                # ingests <sid>.trajectory.jsonl etc., and
                # _canonical_session_file() splits at the first `.jsonl`
                # producing phantom session_ids like '<uuid>.trajectory'
                # that pollute DuckDB and downstream APIs. The dashboard
                # read-path applies the same exclusion (dashboard.py,
                # routes/sessions.py, routes/brain.py, routes/usage.py).
                if (
                    ".trajectory." in fname
                    or ".checkpoint." in fname
                    or ".deleted." in fname
                ):
                    continue
                out.append(os.path.join(sessions_dir, fname))
    except OSError:
        pass
    return out


def _canonical_session_file(name: str) -> str:
    """Return the canonical `<session_id>.jsonl` form for a session path.

    `name` may be a basename (`<uuid>.jsonl` or `<uuid>.jsonl.reset.<ts>`)
    or a full path. Cloud keys session rows on this string -- for an
    archived reset, we want events to land under the same session_id as
    the original live session, not a per-archive ghost row.
    """
    base = os.path.basename(name)
    sid = base.split(".jsonl", 1)[0]
    return sid + ".jsonl"


def sync_sessions(config: dict, state: dict, paths: dict) -> int:
    # Skipped when sync is paused (expired trial). The state dict still
    # tracks last_event_ids so when the user upgrades, we resume from
    # exactly where we paused -- no event loss, no double-send.
    if not _sync_allowed():
        return 0
    _record_sync_progress("sessions", 0)
    sessions_dir = paths["sessions_dir"]
    api_key = config["api_key"]
    enc_key = config.get("encryption_key")
    node_id = config["node_id"]
    last_ids: dict = state.setdefault("last_event_ids", {})
    total = 0

    # Build file-basename → subagent_id map from sessions.json index.
    # Each sub-agent session has a *different* UUID as its key vs. its .jsonl filename.
    # Without this mapping the cloud UI cannot correlate blobs → sub-agent sessions.
    file_to_subagent_id: dict[str, str] = {}
    index_path = os.path.join(sessions_dir, "sessions.json")
    if os.path.isfile(index_path):
        try:
            with open(index_path) as _fi:
                _idx = json.load(_fi)
            for _k, _meta in _idx.items():
                if ":subagent:" in _k and isinstance(_meta, dict):
                    _sf = _meta.get("sessionFile", "")
                    if _sf:
                        _fn = os.path.basename(_sf)  # e.g. "00b5b41b-…jsonl"
                        file_to_subagent_id[_fn] = _k.split(":")[
                            -1
                        ]  # e.g. "317db68b-…"
        except Exception:
            pass

    jsonl_files = _list_session_jsonls(sessions_dir)
    # Sort newest-first so recent sessions sync before old ones
    jsonl_files.sort(key=lambda p: os.path.getmtime(p), reverse=True)

    for fpath in jsonl_files:
        if total >= MAX_EVENTS_PER_CYCLE:
            break  # continue next cycle; progress is saved per-file

        fname = os.path.basename(fpath)
        # Cloud keys session rows on the canonical `<uuid>.jsonl`. For an
        # archived `<uuid>.jsonl.reset.<ts>` we want events to land under
        # the same session row, not spawn a per-archive ghost.
        cloud_fname = _canonical_session_file(fname)
        last_line = last_ids.get(fname, 0)
        batch: list[dict] = []
        subagent_id = file_to_subagent_id.get(cloud_fname) or file_to_subagent_id.get(fname)

        try:
            with open(fpath, "r", errors="replace") as f:
                new_lines = list(islice(f, last_line, None))

            line_cursor = last_line
            for i, raw in enumerate(new_lines, start=last_line):
                raw = raw.strip()
                if not raw:
                    line_cursor = i + 1
                    continue
                try:
                    obj = json.loads(raw)
                except Exception:
                    line_cursor = i + 1
                    continue

                # Full content — encrypted before leaving machine
                batch.append(obj)
                line_cursor = i + 1

                if len(batch) >= BATCH_SIZE:
                    _flush_session_batch(
                        batch, cloud_fname, api_key, enc_key, node_id, subagent_id
                    )
                    total += len(batch)
                    batch = []
                    # Save progress after each batch so restarts don't re-upload
                    last_ids[fname] = line_cursor
                    if total >= MAX_EVENTS_PER_CYCLE:
                        break

            if batch:
                _flush_session_batch(
                    batch, cloud_fname, api_key, enc_key, node_id, subagent_id
                )
                total += len(batch)

            # line_cursor tracks our furthest position in the file (inclusive
            # of lines we skipped as blank/malformed), so it is always the
            # correct "next start offset". The previous `len(all_lines)` ref
            # was stale from a pre-islice implementation that read the whole
            # file — it raised NameError on every call, spamming warnings
            # and preventing the cursor from advancing past the last BATCH_SIZE
            # flush.
            last_ids[fname] = line_cursor

        except Exception as e:
            log.warning(f"Session sync error ({fname}): {e}")

    _record_sync_progress("sessions", total, total)
    return total


def _flush_session_batch(
    batch: list,
    fname: str,
    api_key: str,
    enc_key: str | None,
    node_id: str,
    subagent_id: str | None = None,
) -> None:
    # Write-through to local DuckDB FIRST (epic #964 / phase 1 / issue #958),
    # then synchronously flush so the rows are durable BEFORE the caller
    # advances its in-memory JSONL line cursor. Local is the durable store;
    # cloud is a hot cache. If the cloud POST fails below, the events are
    # still recorded locally.
    #
    # Write-then-ack ordering (audit fix, 2026-05-17):
    #   The caller (sync_sessions / sync_sessions_recent / …) advances
    #   ``state["last_event_ids"][fname]`` right after we return, and
    #   ``save_state(state)`` writes that cursor to disk at the end of the
    #   tick. ``_local_ingest_session_batch`` only ENQUEUES rows into the
    #   local-store ring buffer; the background flusher commits them ~2s
    #   later. If the daemon crashed between enqueue and the next flusher
    #   tick, the cursor would be durable on disk while the events were lost
    #   to volatile memory — silent ingest gap until the user manually
    #   rewound state.json. Calling ``flush()`` here makes the DuckDB COMMIT a
    #   precondition for the caller's offset advance, so a kill -9 anywhere
    #   in the path leaves the cursor pointing at lines that are either
    #   (a) already durable or (b) re-read on restart and idempotently
    #   collapsed by INSERT OR IGNORE on the canonical event id.
    #
    # Cloud-sync independence: local ingest+flush failures are logged but do
    # not block the cloud POST below. The MOAT mandate is local-first, but
    # cloud-first behaviour is preserved for users on read-only ~/.clawmetry/
    # or partial installs without DuckDB. The next flusher tick (or daemon
    # restart) will retry the local write; INSERT OR IGNORE makes it safe.
    try:
        _local_ingest_session_batch(batch, fname, node_id, subagent_id)
        from clawmetry import local_store as _ls
        _ls.get_store().flush()
    except Exception as _e:
        log.warning("local-store ingest/flush failed (cloud sync continues): %s", _e)

    payload = {"session_file": fname, "node_id": node_id, "events": batch}
    # Include subagent_id so the cloud can correlate blobs → sub-agent sessions.
    # The session key UUID (subagent_id) differs from the .jsonl filename UUID.
    if subagent_id:
        payload["subagent_id"] = subagent_id
    # Cloud-sync independence (audit fix, 2026-05-17):
    #   The local DuckDB row above is ALREADY committed at this point, so
    #   the cloud POST is best-effort relative to the local contract. We
    #   catch the exception here so:
    #     1. A cloud outage doesn't propagate out of _flush_session_batch and
    #        abort the per-file iteration in sync_sessions (which then
    #        skipped batches 2..N of the SAME file even though local could
    #        have ingested them just fine).
    #     2. The caller's cursor (``state["last_event_ids"][fname]``)
    #        advances based on LOCAL durability, not cloud reachability —
    #        matching the MOAT mandate that local is the source of truth and
    #        cloud is a hot cache.
    #   Cloud POST failures are now queued in sync_dlq (kind="post_failure")
    #   and replayed on the next tick by _dlq_replay, closing the silent-drop
    #   gap described in #1592. Local correctness is still the primary contract;
    #   cloud is a hot cache that self-heals via the DLQ retry loop.
    # Split encryption from POST so the diagnostic for each path is distinct
    # and an encryption failure no longer silently drops the batch (#1601).
    # Encryption can fail on: corrupted/rotated key, payload containing
    # non-JSON-serialisable bytes, missing cryptography wheel. POST can fail
    # on: network outage, cloud 5xx. Conflating them sends users on a
    # wild-goose chase for a network problem when the real issue is the key.
    blob: str | None = None
    if enc_key:
        try:
            blob = encrypt_payload(payload, enc_key)
        except Exception as _enc_e:
            # Persist to local DLQ so the next sync tick (or a daemon restart
            # after the user rotates the key back) can re-encrypt and POST.
            # The local DuckDB row is already durable above; this only protects
            # the cloud side of the pipeline from silent loss.
            try:
                _dlq_enqueue_encryption_failure(
                    kind="session_batch",
                    endpoint="/ingest/events",
                    payload=payload,
                    fname=fname,
                    node_id=node_id,
                    subagent_id=subagent_id,
                    error=str(_enc_e),
                )
            except Exception as _dlq_e:
                log.exception(
                    "E2E encryption AND DLQ persist both failed for %s "
                    "(events permanently dropped from cloud): enc=%s dlq=%s",
                    fname, _enc_e, _dlq_e,
                )
            else:
                log.error(
                    "E2E encryption failed for %s — batch parked in sync_dlq "
                    "for replay (key rotation? corrupt key?): %s",
                    fname, _enc_e,
                )
            return
    try:
        if blob is not None:
            _post(
                "/ingest/events",
                {"node_id": node_id, "encrypted": True, "blob": blob},
                api_key,
            )
        else:
            _post("/ingest/events", payload, api_key)
    except Exception as _cloud_e:
        try:
            _dlq_enqueue_encryption_failure(
                kind="post_failure",
                endpoint="/ingest/events",
                payload=payload,
                fname=fname,
                node_id=node_id,
                subagent_id=subagent_id,
                error=str(_cloud_e),
            )
        except Exception as _dlq_e:
            log.warning(
                "cloud /ingest/events POST failed AND DLQ park failed for %s "
                "(events permanently dropped from cloud): post=%s dlq=%s",
                fname, _cloud_e, _dlq_e,
            )
        else:
            log.warning(
                "cloud /ingest/events POST failed for %s — parked in sync_dlq "
                "for retry on next tick: %s",
                fname, _cloud_e,
            )


def _extract_cost_tokens_model(obj: dict) -> tuple:
    """Pull (cost_usd, token_count, model) out of a raw OpenClaw transcript event.

    Real OpenClaw events nest these under ``obj["message"]["usage"]``:

        {
          "type": "message",
          "message": {
            "model": "claude-opus-4-7",
            "usage": {
              "totalTokens": 162,
              "cost": {"total": 0.00495, ...}
            }
          }
        }

    Older / synthesised events sometimes carry top-level ``cost_usd`` /
    ``tokens`` / ``model``. We accept either shape so tests, sub-agent
    adapters, and the real OpenClaw harness all populate the columns
    (previously the nested shape silently became NULL — see MOAT_E2E_REPORT
    2026-05-13 root-cause #4)."""
    cost_usd = obj.get("cost_usd")
    if cost_usd is None:
        cost_usd = obj.get("costUsd")
    token_count = obj.get("token_count")
    if token_count is None:
        token_count = obj.get("tokens")
    model = obj.get("model")

    msg = obj.get("message")
    if isinstance(msg, dict):
        if model is None:
            model = msg.get("model")
        usage = msg.get("usage")
        if isinstance(usage, dict):
            if token_count is None:
                tt = usage.get("totalTokens")
                if tt is None:
                    tt = usage.get("total_tokens")
                if tt is not None:
                    try:
                        token_count = int(tt)
                    except (TypeError, ValueError):
                        token_count = None
            if cost_usd is None:
                cost = usage.get("cost")
                if isinstance(cost, dict):
                    cv = cost.get("total")
                    if cv is None:
                        cv = cost.get("total_usd")
                else:
                    cv = cost  # rare: cost itself is a number
                if cv is not None:
                    try:
                        cost_usd = float(cv)
                    except (TypeError, ValueError):
                        cost_usd = None
    return cost_usd, token_count, model


def _extract_channel_message(
    obj: dict,
    *,
    session_id: str,
) -> dict | None:
    """Best-effort projection of a transcript event into a
    ``channel_messages`` row.

    Issue #1088 Phase 4. Returns ``None`` when the event is not a chat
    message OR carries no recoverable channel signal — the daemon then
    just records the event in ``events`` and moves on.

    Two recognition paths:

    1. **Inbound** — a ``user``-role message whose text starts with one of
       the known adapter wrappers (e.g. ``[Telegram Alice id:123]…``,
       ``[iMessage +14155551234]…``). The Connector layer prefixes every
       inbound channel message with this bracket-tag so downstream
       routing / observability can attribute it without scanning the
       gateway log. We mirror that parser here so the local DuckDB has a
       single canonical row per inbound message — the same key the
       dashboard uses for dedupe.
    2. **Outbound** — an ``assistant``-role message in a session whose
       session_id was previously seen carrying an inbound channel
       message. The session_id is the join key so we don't have to
       re-parse the session metadata blob — the inbound path stamps
       the channel and chat-id on a sentinel row this code reads
       opportunistically (a future PR can plumb the session→channel
       index more directly).

    The shape is intentionally narrow: ``provider``, ``channel_id``,
    ``sender_*``, ``body``, ``ts``, ``direction``. Per-provider extras
    (attachments, reactions, message_id) ride along in ``raw_blob`` so
    we don't widen the schema for adapter-specific fields.
    """
    import re as _re
    if not isinstance(obj, dict):
        return None
    if obj.get("type") != "message":
        return None
    msg = obj.get("message")
    if not isinstance(msg, dict):
        return None
    role = msg.get("role")
    if role not in ("user", "assistant"):
        return None
    content = msg.get("content")
    text = ""
    if isinstance(content, str):
        text = content
    elif isinstance(content, list):
        for c in content:
            if isinstance(c, dict) and c.get("type") == "text":
                text = c.get("text", "") or ""
                if text:
                    break
    if not text:
        return None
    # Skip system/heartbeat noise — these aren't user-facing channel msgs.
    stripped = text.strip()
    if stripped.startswith("System:") or "HEARTBEAT" in stripped:
        return None
    ts = obj.get("timestamp") or obj.get("ts") or ""
    if not ts:
        return None
    eid = (
        obj.get("id")
        or obj.get("eventId")
        or obj.get("messageId")
        or f"{session_id}:{ts}:{role}"
    )
    if role == "user":
        # Recognised inbound formats — the Connector layer tags every
        # inbound message with one of these prefixes. We try Telegram /
        # iMessage / WhatsApp / Signal / Discord / Slack first because
        # those cover ~95% of installed adapters; the rest fall through
        # to the generic ``[Provider …]`` matcher.
        m = _re.match(
            r"\[(?P<prov>Telegram|iMessage|WhatsApp|Signal|Discord|Slack|"
            r"IRC|WebChat|GoogleChat|MSTeams|BlueBubbles|Matrix|Mattermost|"
            r"LINE|Nostr|Twitch|Feishu|Zalo|Tlon|SynologyChat|NextcloudTalk)"
            r"\s+(?P<sender>.+?)\s+id:(?P<sid>[^\]]+?)\]\s*(?P<body>.*)",
            stripped,
            flags=_re.IGNORECASE | _re.DOTALL,
        )
        if not m:
            return None
        provider = m.group("prov").lower()
        sender_name = m.group("sender").strip()
        chan_id = m.group("sid").strip()
        body = m.group("body").strip() or stripped
        return {
            "id":          str(eid),
            "agent_id":    "main",
            "provider":    provider,
            "channel_id":  chan_id,
            "sender_id":   chan_id,
            "sender_name": sender_name,
            "body":        body[:4000],
            "ts":          str(ts),
            "direction":   "in",
            "session_key": session_id,
            "raw_blob":    None,
        }
    # Assistant turn — outbound. We don't know the channel from the
    # event alone (the session-metadata blob carries it, processed in
    # _local_ingest_sessions_batch). Skip here; the per-session metadata
    # writer takes care of attribution via the ``openclaw_channels``
    # table. The summary endpoint joins on session_key so outbound
    # counts populate from a follow-up adapter PR. Returning None here
    # keeps this PR's footprint minimal and avoids stamping the wrong
    # provider on assistant turns from sessions we haven't classified.
    return None


# ── v3 underscore-schema parser (#1135) ───────────────────────────────────────
#
# OpenClaw writes TWO different jsonl shapes per session:
#
#   1. ``<sid>.trajectory.jsonl`` — runtime debug trace sidecar.
#      Dot.separated event types (``trace.artifacts``, ``model.completed``,
#      ``prompt.submitted``, ``session.ended``…) with content under
#      ``data.*``. The trajectory parser path (``_local_ingest_session_batch``
#      below) was originally written for this shape.
#
#   2. ``<sid>.jsonl`` — the canonical user-facing transcript ("v3" schema,
#      tagged by the leading ``{"type": "session", "version": 3, ...}`` line).
#      Underscore_separated event types (``message``, ``model_change``,
#      ``thinking_level_change``, ``tool_use_result``…) with the LLM payload
#      nested under ``message.{role,content,usage,model}``. Until #1135 the
#      ingest path stamped ``event_type="message"`` onto these rows AND left
#      the data shape un-translated, so the dashboard's transcript expander
#      (designed for the dot.separated shape from PR #1132) saw none of the
#      content.
#
# ``_parse_v3_event`` maps a v3 underscore event to the SAME row shape that
# the trajectory path produces — same dot-separated ``event_type`` values,
# same ``data.{finalPromptText,completionText,toolMetas,promptCache.…}``
# nested keys — so the read-side handlers in PR #1132 work unchanged. It
# returns ``None`` for plumbing types we deliberately drop
# (``thinking_level_change``, ``cwd_change``, …) and unknown types.

# Top-level v3 event types we recognise. Anything else falls through to the
# trajectory parser, which itself drops unknowns. Keep this set narrow to
# avoid mis-routing trajectory events that happen to have a synonym name.
_V3_KNOWN_TYPES = frozenset({
    "session",
    "model_change",
    "thinking_level_change",
    "cwd_change",
    "message",
    "tool_use",
    "tool_use_result",
})

# Plumbing event types that carry no transcript-visible content. Returning
# None here is intentional — the dashboard's brain feed and transcript view
# are noisier, not richer, when these are surfaced.
_V3_SKIP_TYPES = frozenset({
    "thinking_level_change",
    "cwd_change",
})


def _is_v3_event(obj: dict) -> bool:
    """Sniff a single parsed JSONL event for the v3 underscore schema.

    The first line of a v3 file is always ``{"type": "session", "version": N,
    ...}`` — that's the strongest signal. For subsequent lines we look for
    type-name + structural cues that only the v3 shape carries:

    * ``model_change``, ``thinking_level_change``, ``cwd_change``,
      ``tool_use``, ``tool_use_result`` — these names are NEW in v3 and
      never appear in trajectory or legacy synthesised events.
    * ``message`` is overloaded: legacy synthesised events use
      ``{"type":"message","role":"user","text":"…"}`` (top-level fields)
      while v3 nests under ``{"type":"message","message":{role,content,…}}``.
      We require the nested ``message`` dict to disambiguate; without it
      the line is treated as legacy and falls through to the trajectory
      parser (which preserves the existing event_type and data).
    """
    if not isinstance(obj, dict):
        return False
    t = obj.get("type")
    if not isinstance(t, str):
        return False
    if t == "session" and obj.get("version") is not None:
        return True
    if t == "message":
        # Disambiguate v3 (nested message dict) from legacy synthesised
        # events that ALSO use type=message but with top-level role/text.
        return isinstance(obj.get("message"), dict)
    return t in _V3_KNOWN_TYPES


def _v3_content_to_text(content) -> str:
    """Flatten a v3 ``message.content`` (string OR list of typed blocks)
    into a single plain-text string. Tool-use blocks and other non-text
    blocks are preserved separately by the caller — this helper deliberately
    drops them so the resulting text mirrors what the trajectory schema
    stored in ``finalPromptText``/``completionText`` (the printable bit)."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for block in content:
            if isinstance(block, dict) and block.get("type") == "text":
                txt = block.get("text") or ""
                if txt:
                    parts.append(txt)
        return "\n".join(parts)
    if content is None:
        return ""
    return str(content)


def _v3_extract_tool_metas(content) -> list[dict]:
    """Pull tool_use blocks out of an assistant ``message.content`` array
    and project them onto the ``toolMetas`` shape PR #1132's expander reads
    (``{name, input}``). Returns [] when there are no tool calls."""
    out: list[dict] = []
    if not isinstance(content, list):
        return out
    for block in content:
        if not isinstance(block, dict):
            continue
        if block.get("type") != "tool_use":
            continue
        out.append({
            "id": block.get("id"),
            "name": block.get("name") or "tool",
            "input": block.get("input") or {},
        })
    return out


def _parse_v3_event(
    obj: dict,
    session_id: str,
    node_id: str,
) -> dict | None:
    """Map ONE v3 underscore-schema event to a normalised local-store row.

    Returns ``None`` for plumbing events we deliberately skip
    (``thinking_level_change``, ``cwd_change``) and for anything unrecognised
    inside the v3 namespace — the caller treats ``None`` as "drop this row"
    rather than re-routing through the trajectory path (the v3 sniff already
    classified it).

    The output row carries the dot.separated ``event_type`` values and the
    nested ``data.*`` key paths the trajectory parser produces, so the read
    side (``_try_local_store_transcript`` / ``_try_local_store_transcript_events``
    in routes/sessions.py) works unchanged on both shapes.
    """
    t = obj.get("type")
    if not isinstance(t, str):
        return None
    if t in _V3_SKIP_TYPES:
        return None

    ts = obj.get("timestamp") or obj.get("ts") or ""
    if not ts:
        # The local store indexes on ts; without it we cannot place the
        # event on the timeline. Safer to drop than to fabricate.
        return None

    eid = obj.get("id") or obj.get("eventId") or f"{session_id}:{ts}:{t}"

    # Defaults; overridden per type below.
    event_type = "unknown"
    # ``data`` mirrors the TRAJECTORY shape that routes/sessions.py expects:
    # top-level ``type`` + ``timestamp`` + sometimes ``modelId`` for the
    # discriminator / model picker, and a NESTED ``data`` sub-dict carrying
    # the content fields (``finalPromptText``, ``completionText``,
    # ``promptCache``, ``toolMetas`` …) that ``_expand_openclaw_event`` and
    # ``_openclaw_event_tokens`` read. The legacy flat keys that #1135's
    # parser stored at the top level are kept alongside the nested copy so
    # existing brain-feed / debug consumers keep working.
    data: dict = {"_v3_type": t}  # preserve the original tag for debugging
    inner: dict = {}  # nested ``data.data`` payload — matches trajectory shape
    cost_usd: float | None = None
    token_count: int | None = None
    model: str | None = None

    if t == "session":
        # First line of every v3 file. Project onto session.started so the
        # brain feed and per-session sidebar see a session-creation marker.
        event_type = "session.started"
        data.update({
            "id": obj.get("id"),
            "version": obj.get("version"),
            "cwd": obj.get("cwd"),
            "timestamp": ts,
        })
        inner.update({
            "id": obj.get("id"),
            "version": obj.get("version"),
            "cwd": obj.get("cwd"),
        })

    elif t == "model_change":
        event_type = "model.changed"
        model = obj.get("modelId") or obj.get("model")
        data.update({
            "modelId": model,
            "provider": obj.get("provider"),
            "timestamp": ts,
        })
        inner.update({
            "modelId": model,
            "provider": obj.get("provider"),
        })

    elif t == "message":
        msg = obj.get("message") if isinstance(obj.get("message"), dict) else {}
        role = msg.get("role")
        content = msg.get("content")
        text = _v3_content_to_text(content)
        usage = msg.get("usage") if isinstance(msg.get("usage"), dict) else {}
        # v3 uses Anthropic-style camelCase keys: input / output / totalTokens.
        # PR #1132's _openclaw_event_tokens reads
        # data.promptCache.lastCallUsage.{total,input,output}, so we project
        # there. Cost lives under usage.cost.{total,input,output}.
        last_call_usage: dict = {}
        if usage:
            inp = usage.get("input") or usage.get("input_tokens")
            outp = usage.get("output") or usage.get("output_tokens")
            tot = (
                usage.get("totalTokens")
                or usage.get("total_tokens")
                or usage.get("total")
            )
            if inp is not None:
                last_call_usage["input"] = int(inp)
            if outp is not None:
                last_call_usage["output"] = int(outp)
            if tot is not None:
                try:
                    last_call_usage["total"] = int(tot)
                    token_count = int(tot)
                except (TypeError, ValueError):
                    pass
            elif inp is not None and outp is not None:
                token_count = int(inp) + int(outp)

            cost = usage.get("cost")
            if isinstance(cost, dict):
                cv = cost.get("total")
                if cv is None and cost.get("input") is not None and cost.get("output") is not None:
                    try:
                        cv = float(cost["input"]) + float(cost["output"])
                    except (TypeError, ValueError):
                        cv = None
                if cv is not None:
                    try:
                        cost_usd = float(cv)
                    except (TypeError, ValueError):
                        cost_usd = None

        if role == "user":
            event_type = "prompt.submitted"
            data.update({
                "finalPromptText": text,
                "timestamp": ts,
            })
            inner["finalPromptText"] = text
            if last_call_usage:
                data["promptCache"] = {"lastCallUsage": last_call_usage}
                inner["promptCache"] = {"lastCallUsage": last_call_usage}
        elif role == "assistant":
            event_type = "model.completed"
            model = msg.get("model") or model
            tool_metas = _v3_extract_tool_metas(content)
            data.update({
                "completionText": text,
                "assistantTexts": [text] if text else [],
                "modelId": model,
                "provider": msg.get("provider"),
                "timestamp": ts,
                "stopReason": msg.get("stopReason"),
            })
            inner.update({
                "completionText": text,
                "assistantTexts": [text] if text else [],
                "modelId": model,
                "provider": msg.get("provider"),
                "stopReason": msg.get("stopReason"),
            })
            if tool_metas:
                data["toolMetas"] = tool_metas
                inner["toolMetas"] = tool_metas
            if last_call_usage:
                data["promptCache"] = {"lastCallUsage": last_call_usage}
                inner["promptCache"] = {"lastCallUsage": last_call_usage}
        else:
            # Unknown role — be conservative, drop rather than mis-classify.
            return None

    elif t == "tool_use":
        # Top-level tool_use is rare in v3 (most tool calls live inside
        # assistant message.content), but if/when one does appear, project
        # it onto the dot.separated tool.call shape.
        event_type = "tool.call"
        data.update({
            "name": obj.get("name") or "tool",
            "input": obj.get("input") or {},
            "id": obj.get("id"),
            "timestamp": ts,
        })
        inner.update({
            "name": obj.get("name") or "tool",
            "input": obj.get("input") or {},
            "id": obj.get("id"),
        })

    elif t == "tool_use_result":
        event_type = "tool.result"
        # ``content`` is typically a list of {type:"text",text:"..."} blocks
        # or a plain string; flatten so PR #1132's expander finds it under
        # ``data.output`` / ``data.result``.
        result_text = _v3_content_to_text(obj.get("content"))
        data.update({
            "tool_use_id": obj.get("tool_use_id"),
            "output": result_text,
            "result": result_text,
            "is_error": obj.get("is_error"),
            "timestamp": ts,
        })
        inner.update({
            "tool_use_id": obj.get("tool_use_id"),
            "output": result_text,
            "result": result_text,
            "is_error": obj.get("is_error"),
        })

    else:
        # Unknown v3 event — log + drop so future schema additions don't
        # silently land as event_type="unknown" rows that pollute analytics.
        log.debug("unknown v3 event type %r — skipping (session=%s)", t, session_id)
        return None

    # MOAT fix: stamp the dot.separated event_type onto data.type so
    # routes/sessions.py::_is_openclaw_event (PR #1132) recognises this
    # row as an OpenClaw event. Without this the discriminator sees
    # data.type == None, falls back to the Anthropic shape, and
    # /api/transcript/<sid> renders 0 messages even though brain-history
    # (which reads the event_type column directly) works fine.
    data["type"] = event_type
    # MOAT fix part 2: attach the nested ``data`` payload that the
    # trajectory parser produces (``data: obj`` of the raw event line) so
    # ``_expand_openclaw_event`` / ``_openclaw_event_tokens`` find the
    # content + usage at the same key paths as for trajectory events.
    data["data"] = inner

    return {
        "id": str(eid),
        "agent_type": "openclaw",
        "node_id": node_id,
        "agent_id": "main",
        "session_id": session_id,
        "workspace_id": None,
        "event_type": event_type,
        "ts": str(ts),
        "data": data,
        "cost_usd": cost_usd,
        "token_count": token_count,
        "model": model,
    }


def _local_ingest_session_batch(
    batch: list,
    session_file: str,
    node_id: str,
    subagent_id: str | None,
) -> None:
    """Translate a batch of raw OpenClaw transcript events into the local
    store's normalised shape and queue them for write. Idempotent at the
    store level — INSERT OR IGNORE on event id.

    Schema-aware: events that carry the v3 underscore schema (see
    ``_is_v3_event`` / ``_parse_v3_event``) are routed through the v3 mapper,
    which projects them onto the SAME dot.separated event_types and nested
    data shape that the trajectory parser produces. Everything else falls
    through to the legacy trajectory path. This per-event sniff (vs. a
    per-batch one) keeps the code correct when a single batch happens to
    mix shapes — e.g. the streaming reader hands us tail-of-file v3 lines
    after a checkpoint switchover.
    """
    from clawmetry import local_store  # local import: keeps cli/sync importable on Pythons missing sqlite3

    store = local_store.get_store()
    rows: list[dict] = []
    # session_file is like '<uuid>.jsonl' — use the uuid as the canonical
    # session_id so the dashboard's per-session views can correlate.
    session_id = subagent_id or session_file.split(".jsonl", 1)[0]
    for obj in batch:
        if not isinstance(obj, dict):
            continue
        # Issue #1088 Phase 4: opportunistically project inbound channel
        # messages into the channel_messages table. Best-effort — never
        # blocks the events ingest below on a per-row failure. The channel
        # extractor reads ``message.{role,content}``, which is the v3 shape,
        # so it works regardless of which parser branch we take next.
        try:
            ch_row = _extract_channel_message(obj, session_id=session_id)
            if ch_row is not None:
                store.ingest_channel_message(ch_row)
        except Exception as _e:
            log.debug("channel_message extract failed (continuing): %s", _e)

        # v3 underscore schema (#1135) — translate onto the trajectory shape
        # so the read path works unchanged. ``_parse_v3_event`` returns None
        # for plumbing/unknown types; we drop those rather than fall back to
        # the trajectory parser (which would stamp event_type="message"
        # etc. and re-introduce the bug).
        if _is_v3_event(obj):
            row = _parse_v3_event(obj, session_id, node_id)
            if row is not None:
                rows.append(row)
            continue

        # Stable per-event id. For Claude Code-sourced events (legacy
        # ``sync_claude_cli_sessions`` path #1) we route through the unified
        # ``_canonical_event_id`` helper so the id is identical to whatever
        # paths #2 and #3 would compute for the same source line — that's
        # the dedup contract that lets ``INSERT OR IGNORE`` collapse the
        # 2x/3x duplicate writes the user reported (#1232). For non-CC
        # events we keep the legacy composition (eventId / messageId / fallback)
        # which was already stable per source.
        if obj.get("_cc_source"):
            eid = _canonical_event_id(obj, session_id=session_id)
        else:
            eid = (
                obj.get("id")
                or obj.get("eventId")
                or obj.get("messageId")
                or f"{session_id}:{obj.get('timestamp','?')}:{obj.get('type','?')}"
            )
        ts = obj.get("timestamp") or obj.get("ts") or ""
        if not ts:
            # Skip events with no timestamp — the local store's index assumes
            # ts is set, and filtering them out is safer than synthesising one.
            continue
        # Cost / token / model live UNDER ``message.usage`` in OpenClaw's real
        # transcript shape (verified 2026-05-13 against
        # ~/.openclaw/agents/main/sessions/*.jsonl). Top-level ``cost_usd`` /
        # ``tokens`` only appear in synthesised events (e.g. our own tests).
        # See MOAT_E2E_REPORT_2026-05-13 root-cause #4.
        cost_usd, token_count, model = _extract_cost_tokens_model(obj)
        # Strip the internal _cc_source marker so it never reaches the
        # stored ``data`` BLOB (it's a routing hint, not part of the event).
        if obj.get("_cc_source"):
            data_payload = {k: v for k, v in obj.items() if k != "_cc_source"}
        else:
            data_payload = obj
        rows.append({
            "id": str(eid),
            "node_id": node_id,
            "agent_id": "main",  # OpenClaw harness; Claude Code adapter will use 'claude-code'
            "session_id": session_id,
            "workspace_id": obj.get("workspace") or obj.get("workspace_id"),
            "event_type": str(obj.get("type") or obj.get("event_type") or "unknown"),
            "ts": str(ts),
            "data": data_payload,
            "cost_usd": cost_usd,
            "token_count": token_count,
            "model": model,
        })
    if rows:
        store.ingest_many(rows)


def _local_ingest_sessions_batch(rows: list, node_id: str) -> None:
    """Mirror a batch of session rows (the same dicts we push to /ingest/sessions)
    into the local DuckDB ``sessions`` table. One upsert per row; safe to call
    on a store that already has these sessions (ON CONFLICT DO UPDATE)."""
    if not rows:
        return
    from clawmetry import local_store

    store = local_store.get_store()
    for s in rows:
        sid = s.get("session_id") or s.get("session_key") or s.get("id")
        if not sid:
            continue
        # Cost field has been called several things in different code paths
        # (total_cost, cost_usd, totalCostUsd). Take the first non-None.
        cost = s.get("cost_usd")
        if cost is None:
            cost = s.get("total_cost") or s.get("totalCostUsd") or 0
        # Channel/chat_type/subject move into a separate metadata blob —
        # they're OpenClaw-specific and (per the multi-agent design) will get
        # promoted into the openclaw_channels extension table later.
        meta_extras = {
            k: v for k, v in s.items()
            if k in ("channel", "chat_type", "subject", "recent_model",
                     "session_key")
            and v
        }
        store.ingest_session({
            "agent_type": s.get("agent_type") or "openclaw",
            "session_id": sid,
            "node_id": node_id,
            "agent_id": s.get("agent_id") or "main",
            "title": s.get("subject") or s.get("title"),
            "started_at": s.get("started_at"),
            "last_active_at": s.get("updated_at") or s.get("last_active_at"),
            "ended_at": s.get("ended_at"),
            "status": s.get("status"),
            "total_tokens": s.get("total_tokens") or 0,
            "cost_usd": cost,
            "message_count": s.get("message_count") or 0,
            "metadata": meta_extras or None,
        })


def _local_ingest_memory_files(all_files: list, changed_paths: list) -> None:
    """Persist plaintext memory blobs to local DuckDB. ``all_files`` is the
    full list of (name, content) tuples; ``changed_paths`` is the subset
    that changed since last sync. We only write the changed ones — the
    store's sha256 dedup means it's a no-op anyway, but skipping the
    encode round-trip is cheaper."""
    if not changed_paths:
        return
    from clawmetry import local_store

    store = local_store.get_store()
    changed_set = set(changed_paths)
    now_iso = datetime.now(timezone.utc).isoformat()
    for name, content in all_files:
        if name not in changed_set:
            continue
        store.ingest_memory_blob({
            "agent_type": "openclaw",  # OpenClaw harness writes these files
            "agent_id": "main",
            "path": name,
            "ts": now_iso,
            "blob": content,
        })


_sessions_json_cache: dict = {"ts": 0.0, "data": None, "mtime": 0.0}


def sync_sessions_recent(
    config: dict, state: dict, paths: dict, minutes: int = 60
) -> int:
    """Sync only events from the last N minutes, reading files from the tail.

    This gives the dashboard immediate visibility into *current* activity.
    The normal ``sync_sessions`` loop then backfills older events in the
    background without blocking the Brain feed.

    Strategy:
      1. For each session file (newest-modified first), binary-search for the
         first line whose timestamp falls within the window.
      2. Sync from that line to EOF.
      3. Advance ``last_event_ids`` so the normal loop skips already-synced
         recent lines and continues backfilling from where it left off.
    """
    if not _sync_allowed():
        return 0
    _record_sync_progress("sessions_recent", 0)
    from datetime import timedelta

    sessions_dir = paths["sessions_dir"]
    api_key = config["api_key"]
    enc_key = config.get("encryption_key")
    node_id = config["node_id"]
    last_ids: dict = state.setdefault("last_event_ids", {})
    total = 0

    cutoff = datetime.now(timezone.utc) - timedelta(minutes=minutes)
    cutoff_iso = cutoff.isoformat()

    # Build subagent map (same logic as sync_sessions)
    # Cache sessions.json for 60 seconds to avoid re-parsing every call
    global _sessions_json_cache
    file_to_subagent_id: dict[str, str] = {}
    index_path = os.path.join(sessions_dir, "sessions.json")
    if os.path.isfile(index_path):
        try:
            current_mtime = os.path.getmtime(index_path)
            if _sessions_json_cache["data"] is not None and _sessions_json_cache["mtime"] == current_mtime:
                file_to_subagent_id = _sessions_json_cache["data"]
            else:
                with open(index_path) as _fi:
                    _idx = json.load(_fi)
                for _k, _meta in _idx.items():
                    if ":subagent:" in _k and isinstance(_meta, dict):
                        _sf = _meta.get("sessionFile", "")
                        if _sf:
                            file_to_subagent_id[os.path.basename(_sf)] = _k.split(":")[-1]
                _sessions_json_cache = {"ts": time.time(), "data": file_to_subagent_id.copy(), "mtime": current_mtime}
        except Exception:
            pass

    jsonl_files = _list_session_jsonls(sessions_dir)
    jsonl_files.sort(key=lambda p: os.path.getmtime(p), reverse=True)

    for fpath in jsonl_files:
        if total >= MAX_EVENTS_PER_CYCLE:
            break

        fname = os.path.basename(fpath)
        cloud_fname = _canonical_session_file(fname)
        subagent_id = file_to_subagent_id.get(cloud_fname) or file_to_subagent_id.get(fname)

        try:
            with open(fpath, "r", errors="replace") as f:
                all_lines = list(islice(f, None))  # read all for backwards scan

            n = len(all_lines)
            if n == 0:
                continue

            # Find the first line >= cutoff by scanning backwards.
            # Most lines have a "timestamp" field we can compare lexicographically.
            start_idx = n  # default: nothing recent
            for idx in range(n - 1, -1, -1):
                raw = all_lines[idx].strip()
                if not raw:
                    continue
                try:
                    obj = json.loads(raw)
                    ts = obj.get("timestamp", "")
                    if ts and ts < cutoff_iso:
                        start_idx = idx + 1
                        break
                except Exception:
                    continue
            else:
                # All lines are within the window (or no timestamps found)
                start_idx = 0

            if start_idx >= n:
                continue  # nothing recent in this file

            # Only sync lines that haven't been synced yet
            already_synced = last_ids.get(fname, 0)
            effective_start = max(start_idx, already_synced)
            if effective_start >= n:
                continue

            batch: list[dict] = []
            for i in range(effective_start, n):
                raw = all_lines[i].strip()
                if not raw:
                    continue
                try:
                    obj = json.loads(raw)
                except Exception:
                    continue
                batch.append(obj)
                if len(batch) >= BATCH_SIZE:
                    _flush_session_batch(
                        batch, cloud_fname, api_key, enc_key, node_id, subagent_id
                    )
                    total += len(batch)
                    batch = []
                    if total >= MAX_EVENTS_PER_CYCLE:
                        break

            if batch:
                _flush_session_batch(
                    batch, cloud_fname, api_key, enc_key, node_id, subagent_id
                )
                total += len(batch)

            # Advance cursor to EOF so backfill loop doesn't re-send these.
            # But DON'T advance past what the normal loop would have started at
            # — keep the old cursor so it backfills the gap between old cursor
            # and start_idx.
            last_ids[fname] = max(last_ids.get(fname, 0), n)

        except Exception as e:
            log.warning(f"Recent sync error ({fname}): {e}")

    _record_sync_progress("sessions_recent", total, total)
    return total


# ── Sync: claude-cli backend transcripts ──────────────────────────────────────
# OpenClaw routes most chat (TUI, Telegram, etc.) through the agent/cli-backend
# plugin, which delegates to the Claude Code CLI. Claude CLI writes the actual
# transcript to ~/.claude/projects/<cwd-slug>/<cli-session-id>.jsonl -- keyed on
# the agent process CWD, which is usually *not* the OpenClaw workspace. Without
# this adapter the cloud Brain feed stays frozen at the last bootstrap event
# and misses every real message.


def _claude_projects_root() -> Path:
    """Return Claude Code's projects directory."""
    custom = os.environ.get("CLAUDE_CONFIG_DIR")
    if custom:
        return Path(os.path.expanduser(custom)) / "projects"
    return Path(os.path.expanduser("~/.claude/projects"))


# ── Canonical Claude Code event id derivation (#1232) ────────────────────────
#
# Background: three independent ingest paths converge on the same logical
# Claude Code message but used to compute three different ``events.id`` values,
# defeating the ``INSERT OR IGNORE`` dedup at the local store boundary:
#
#   path #1  sync_claude_cli_sessions        →  bare uuid              (legacy)
#   path #2  sync_openclaw_claude_sessions   →  openclaw-cc:<cc>:top:<uuid>
#   path #3  sync_openclaw_claude_sessions_via_index
#                                            →  openclaw-cc:<oc>:top:<uuid> | line:N
#
# The user observed 2x and 3x duplicate rows in Brain. PR #1227's
# ``skip_claude_ids`` short-circuit only suppresses path #2 vs #3 collisions —
# path #1 (legacy) was always free to re-write the same logical event under a
# different id, and historical data already carries the dupes regardless.
#
# Fix: every Claude Code-derived event flows through ``_canonical_event_id`` so
# all three paths produce IDENTICAL ids for identical source lines. The store's
# existing PRIMARY KEY then dedups for free on subsequent re-reads. Subagent /
# tool-result rows keep their path-scoped id schemes — those aren't dupes
# (each file/uuid pair is genuinely unique).
def _canonical_event_id(
    obj: dict,
    *,
    session_id: str,
    line_no: int | None = None,
) -> str:
    """Stable, path-independent id for a Claude Code event.

    Deterministic — three different ingest paths reading the same source jsonl
    line MUST return the same id. The local store keys ``events`` by id, so
    matching ids → ``INSERT OR IGNORE`` collapses re-writes silently.

    Strategy:
      1. If the source line carries a ``uuid`` (or pre-translated ``id``) that
         looks like a UUID, use ``cc-msg:<uuid>``. Top-level Claude Code
         messages always have this; assistant / user / attachment / system
         events all qualify.
      2. Otherwise (queue-operation, summary, and other synthesised types
         that carry no per-event uuid), compose a content-stable hash from
         the few fields that survive across all three paths: session, ts,
         type, and an MD5 of the canonical body. ``line_no`` is intentionally
         NOT part of this — the same line read twice from two byte offsets
         (path #2 vs #3) would otherwise produce different ids.

    Returns a string suitable for use as ``events.id``. Never raises.
    """
    raw_uuid = obj.get("uuid") or obj.get("id")
    if isinstance(raw_uuid, str):
        s = raw_uuid.strip().lower()
        # 36-char canonical UUID form: 8-4-4-4-12 hex with dashes.
        if (
            len(s) == 36
            and s[8] == "-" and s[13] == "-" and s[18] == "-" and s[23] == "-"
            and all(c in "0123456789abcdef-" for c in s)
        ):
            return f"cc-msg:{s}"
    # Fallback: synthesise a deterministic id from the body. We compute the
    # hash over a normalised projection of the event so injected metadata
    # (added by _translate_claude_session_line: _claude_session_id,
    # _openclaw_session_id, _oc_cc_kind, _subagent_file, parentUuid renamed
    # to parentId, etc.) doesn't change the digest. The keys we keep are
    # everything except the small set of wrapper/cross-ref fields that
    # differ per-path.
    import hashlib
    skip_keys = {
        "_claude_session_id",
        "_openclaw_session_id",
        "_oc_cc_kind",
        "_subagent_file",
        "parentUuid",
        "parentId",
        "uuid",
        "id",
    }
    canonical = {
        k: v for k, v in obj.items()
        if k not in skip_keys
    }
    try:
        body = json.dumps(canonical, sort_keys=True, separators=(",", ":"), default=str)
    except Exception:
        body = repr(sorted(canonical.items()))
    digest = hashlib.md5(body.encode("utf-8", errors="replace")).hexdigest()[:16]
    ts = obj.get("timestamp") or obj.get("ts") or "?"
    evt_type = obj.get("type") or "unknown"
    return f"cc-derived:{session_id}:{ts}:{evt_type}:{digest}"


def _translate_claude_cli_event(obj: dict) -> dict:
    """Map claude-cli jsonl event keys onto OpenClaw event keys.

    The cloud Brain parser keys off 'id', 'parentId', 'type', 'timestamp',
    and 'message'. Claude CLI uses 'uuid' / 'parentUuid' for the first two;
    everything else lines up. We rename in-place and pass the rest through
    so cost/usage/tool fields survive without per-version translation.

    Tags the result with ``_cc_source: True`` so the downstream local-ingest
    helper knows to compute a canonical Claude Code event id (#1232) instead
    of falling back to its legacy session+ts+type composition.
    """
    out = dict(obj)
    if "uuid" in out and "id" not in out:
        out["id"] = out.pop("uuid")
    if "parentUuid" in out and "parentId" not in out:
        out["parentId"] = out.pop("parentUuid")
    out["_cc_source"] = True
    return out


def sync_claude_cli_sessions(config: dict, state: dict, paths: dict) -> int:
    """Tail claude-cli transcripts and push them under the OpenClaw session_file.

    For each entry in `agents/main/sessions/sessions.json` that carries a
    `claudeCliSessionId`, locate the matching jsonl under
    `~/.claude/projects/*/` (scanning all project dirs, since Claude Code
    derives the slug from the agent's CWD rather than the OpenClaw workspace),
    tail new lines, translate them, and push via `_flush_session_batch` using
    the OpenClaw session_file basename. The cloud correlates events to the
    existing session row by that basename, so no cloud-side change is required.
    """
    if not _sync_allowed():
        return 0
    sessions_dir = paths.get("sessions_dir") or ""
    if not sessions_dir:
        return 0

    api_key = config["api_key"]
    enc_key = config.get("encryption_key")
    node_id = config["node_id"]

    index_path = os.path.join(sessions_dir, "sessions.json")
    if not os.path.isfile(index_path):
        return 0
    try:
        with open(index_path) as fi:
            idx = json.load(fi)
    except Exception:
        return 0

    # Claude Code derives the project slug from the *agent process CWD*, not the
    # OpenClaw workspace — a Telegram session spawned from ~/clawd writes to
    # `-home-vivek-clawd/`, even though OpenClaw's workspace is
    # ~/.openclaw/workspace. Scan every project dir and index transcripts by
    # their session-id filename so we find the right file regardless of CWD.
    projects_root = _claude_projects_root()
    if not projects_root.is_dir():
        return 0
    cli_id_to_path: dict[str, Path] = {}
    try:
        for proj_dir in projects_root.iterdir():
            if not proj_dir.is_dir():
                continue
            for jp in proj_dir.glob("*.jsonl"):
                cli_id_to_path[jp.stem] = jp
    except OSError:
        return 0

    targets: list[tuple[str, str]] = []  # (claude_jsonl_path, openclaw_basename)
    for sess_key, meta in idx.items():
        if not isinstance(meta, dict):
            continue
        cli_id = meta.get("claudeCliSessionId") or (
            meta.get("cliSessionIds", {}) or {}
        ).get("claude-cli")
        if not cli_id:
            continue
        cli_path = cli_id_to_path.get(cli_id)
        if cli_path is None:
            continue
        oc_sf = meta.get("sessionFile", "")
        # Fall back to <openclaw_session_id>.jsonl when sessionFile is absent
        # (e.g. Telegram session metadata exists but the OpenClaw jsonl was
        # never written). Cloud will create the session row from these events.
        oc_basename = (
            os.path.basename(oc_sf)
            if oc_sf
            else f"{meta.get('sessionId', cli_id)}.jsonl"
        )
        targets.append((str(cli_path), oc_basename))

    if not targets:
        return 0

    # Separate offset namespace so it can't collide with OpenClaw jsonl offsets.
    cli_offsets: dict = state.setdefault("last_event_ids_cli", {})
    total = 0

    for cli_path, oc_basename in targets:
        if total >= MAX_EVENTS_PER_CYCLE:
            break

        offset_key = os.path.basename(cli_path)
        last_line = cli_offsets.get(offset_key, 0)
        batch: list[dict] = []

        try:
            with open(cli_path, "r", errors="replace") as f:
                new_lines = list(islice(f, last_line, None))

            line_cursor = last_line
            for i, raw in enumerate(new_lines, start=last_line):
                raw = raw.strip()
                if not raw:
                    line_cursor = i + 1
                    continue
                try:
                    obj = json.loads(raw)
                except Exception:
                    line_cursor = i + 1
                    continue
                batch.append(_translate_claude_cli_event(obj))
                line_cursor = i + 1
                if len(batch) >= BATCH_SIZE:
                    _flush_session_batch(
                        batch, oc_basename, api_key, enc_key, node_id
                    )
                    total += len(batch)
                    batch = []
                    cli_offsets[offset_key] = line_cursor
                    if total >= MAX_EVENTS_PER_CYCLE:
                        break

            if batch:
                _flush_session_batch(batch, oc_basename, api_key, enc_key, node_id)
                total += len(batch)

            cli_offsets[offset_key] = line_cursor

        except Exception as e:
            log.warning(f"claude-cli sync error ({offset_key}): {e}")

    return total


# ── Sync: OpenClaw → Claude Code session JSONL (process-discovered) ──────────
#
# OpenClaw delegates execution to a ``claude`` CLI subprocess. Claude Code
# writes its session transcript to:
#
#     ~/.claude/projects/<encoded-cwd>/<session-id>.jsonl
#
# where ``<encoded-cwd>`` is the agent's working directory with ``/`` and ``.``
# both replaced by ``-``. The user observed that Telegram conversations
# weren't appearing in Brain even though the file
# (``-Users-vivek--openclaw-workspace/49f1d9fc-….jsonl``) was being actively
# written. The legacy ``sync_claude_cli_sessions`` path covers most cases, but
# only when ``~/.openclaw/agents/main/sessions/sessions.json`` carries the
# ``claudeCliSessionId`` binding for that session — which is missing for any
# session that was started before OpenClaw wrote its binding, or where the
# binding was lost on a crash. This complementary, defense-in-depth path
# discovers the live session file by inspecting the running ``claude``
# subprocess directly, so capture is independent of OpenClaw's index file.
#
# Discovery works on macOS, Linux, and Windows because Claude Code uses the
# same ``~/.claude/projects/`` layout everywhere; the encoding is uniform.
#
# Default: ON. Escape hatch: ``CLAWMETRY_DISABLE_CLAUDE_SESSION_INGEST=1``.
# Per the DuckDB-first / never-default-off-a-MOAT-capability rule
# (feedback_local_store_default_off_killed_moat 2026-05-13).


def _encode_cwd_for_claude_projects(cwd: str) -> str:
    """Reproduce Claude Code's project-dir naming convention.

    Claude Code derives the ``~/.claude/projects/<dir>`` slug by replacing
    both ``/`` and ``.`` with ``-`` in the agent's CWD. So
    ``/Users/vivek/.openclaw/workspace`` → ``-Users-vivek--openclaw-workspace``
    (the leading ``-`` comes from the absolute path's leading ``/``; the
    consecutive ``--`` comes from ``/.`` collapsing).
    """
    return (cwd or "").replace("/", "-").replace(".", "-")


def _looks_like_openclaw_process(proc) -> bool:
    """True if a psutil.Process appears to be a claude-cli subprocess
    spawned by OpenClaw.

    Heuristics (any one is sufficient):
      * cmdline contains ``--mcp-config`` whose argument lives under
        ``~/.openclaw/`` (OpenClaw passes its own MCP config in)
      * cwd is under ``~/.openclaw/`` (the agent's working directory
        is the OpenClaw workspace)
      * any ancestor process name/exe matches ``openclaw`` or
        ``openclaw-gateway``

    All access is wrapped because psutil throws ``AccessDenied`` /
    ``NoSuchProcess`` freely on macOS sandbox-restricted processes.
    """
    oc_dir = os.path.realpath(_get_openclaw_dir())
    try:
        cmdline = proc.cmdline() or []
    except Exception:
        cmdline = []
    # --mcp-config <path-under-~/.openclaw/>
    for i, tok in enumerate(cmdline):
        if tok in ("--mcp-config", "--mcp_config") and i + 1 < len(cmdline):
            try:
                mcp_path = os.path.realpath(os.path.expanduser(cmdline[i + 1]))
                if mcp_path.startswith(oc_dir):
                    return True
            except Exception:
                pass
    # cwd under ~/.openclaw/
    try:
        cwd = os.path.realpath(proc.cwd())
        if cwd.startswith(oc_dir):
            return True
    except Exception:
        pass
    # ancestor named openclaw* — walk up at most 6 hops to bound cost
    try:
        cur = proc
        for _ in range(6):
            cur = cur.parent()
            if cur is None:
                break
            try:
                name = (cur.name() or "").lower()
            except Exception:
                name = ""
            if "openclaw" in name:
                return True
    except Exception:
        pass
    return False


def _discover_openclaw_claude_session_files() -> list[tuple[str, str]]:
    """Return ``[(session_id, jsonl_path), …]`` for live Claude Code
    sessions whose owning ``claude`` CLI process appears to belong to
    OpenClaw.

    Best-effort. Returns ``[]`` if psutil is unavailable, no claude
    processes are running, or all paths are unreadable. Never raises.

    Discovery flow (per running ``claude`` process):
      1. argv must contain ``--resume`` (Claude Code's session-resume flag).
         Sessions without ``--resume`` are one-shot scratch invocations
         we don't need to capture.
      2. Process must look like an OpenClaw subprocess
         (``_looks_like_openclaw_process``).
      3. Read the cwd via ``psutil.Process.cwd()`` and the session-id
         from the next argv token after ``--resume``.
      4. Construct ``~/.claude/projects/<encoded-cwd>/<session-id>.jsonl``
         and verify it exists and is readable.

    On macOS where ``psutil.cwd()`` may be blocked by SIP / sandboxing,
    fall back to scanning ``~/.claude/projects/*/<session-id>.jsonl`` for
    the discovered session-id (since the slug is derived from cwd, we
    can't reconstruct it without cwd, but a file named
    ``<session-id>.jsonl`` is unique across all project dirs).
    """
    try:
        import psutil  # type: ignore
    except Exception:
        return []
    projects_root = _claude_projects_root()
    if not projects_root.is_dir():
        return []
    discovered: dict[str, str] = {}  # session_id → jsonl path
    try:
        proc_iter = psutil.process_iter(["name", "cmdline"])
    except Exception:
        return []
    for proc in proc_iter:
        try:
            name = (proc.info.get("name") or "").lower()
            cmdline = proc.info.get("cmdline") or []
        except Exception:
            continue
        # The CLI binary is usually exactly "claude" or contains "claude"
        # in argv[0]; node-shim invocations can also surface as "node
        # /usr/local/bin/claude" so we sniff the full cmdline too.
        joined = " ".join(cmdline) if cmdline else ""
        if "claude" not in name and "claude" not in joined.lower():
            continue
        # Need --resume <id>
        sess_id: str | None = None
        for i, tok in enumerate(cmdline):
            if tok in ("--resume", "-r") and i + 1 < len(cmdline):
                cand = cmdline[i + 1]
                # session-id looks like a UUID; tolerate non-UUID for
                # non-OpenClaw forks but require dash-separated hex blob.
                if cand and "-" in cand and len(cand) >= 16:
                    sess_id = cand
                    break
        if not sess_id:
            continue
        if not _looks_like_openclaw_process(proc):
            continue
        # Try cwd-based path first
        jsonl_path: str | None = None
        try:
            cwd = proc.cwd()
            slug = _encode_cwd_for_claude_projects(cwd)
            cand_path = projects_root / slug / f"{sess_id}.jsonl"
            if cand_path.is_file() and os.access(cand_path, os.R_OK):
                jsonl_path = str(cand_path)
        except Exception:
            pass
        # Fallback: scan all project dirs for <session-id>.jsonl
        if jsonl_path is None:
            try:
                for proj_dir in projects_root.iterdir():
                    if not proj_dir.is_dir():
                        continue
                    cand_path = proj_dir / f"{sess_id}.jsonl"
                    if cand_path.is_file() and os.access(cand_path, os.R_OK):
                        jsonl_path = str(cand_path)
                        break
            except OSError:
                pass
        if jsonl_path:
            discovered[sess_id] = jsonl_path
    return [(sid, path) for sid, path in discovered.items()]


def _openclaw_claude_session_offset_key(jsonl_path: str) -> str:
    """Per-file offset key under ``state['claude_session_byte_offsets']``.

    Keying by absolute realpath so a workspace switch (different
    OpenClaw cwd → different encoded slug → different file) starts a
    fresh tail rather than reusing a stale offset.
    """
    return os.path.realpath(jsonl_path)


def _translate_claude_session_line(
    obj: dict,
    *,
    session_id: str,
    node_id: str,
    line_no: int,
    openclaw_session_id: str | None = None,
    kind: str = "top",
    subagent_file: str | None = None,
) -> dict | None:
    """Map a Claude Code session JSONL line onto an ``events`` row.

    Returns ``None`` for lines we can't map (missing timestamp,
    non-dict). Never raises.

    Field mapping:
      * ``id``         ← ``f"openclaw-cc:{join_id}:{kind}:{uuid_or_lineno}"``
                         where ``join_id`` is the OpenClaw session UUID
                         when provided (sessions.json walk path) or the
                         Claude Code session UUID (process-inspection
                         fallback path).
      * ``agent_type`` ← ``"openclaw"`` (so Brain's per-agent filters
                         still match — this transcript belongs to the
                         OpenClaw agent that spawned the claude CLI)
      * ``agent_id``   ← ``"main"``
      * ``session_id`` ← OpenClaw session UUID when ``openclaw_session_id``
                         is set (so the ``sessions`` table row written by
                         the sessions.json walk joins to these events).
                         Falls back to the Claude Code session UUID for
                         the process-inspection path which doesn't know
                         about the OpenClaw binding (closes #1226).
      * ``event_type`` ← Claude Code ``type`` field (user / assistant /
                         system / queue-operation / attachment / …) —
                         subagent rows are prefixed ``subagent:`` so
                         Brain can render them under a sub-agent lane.
      * ``ts``         ← Claude Code ``timestamp``
      * ``data``       ← the full JSON line (verbatim — Brain's
                         ``_extract_brain_detail`` walks several
                         alternative paths to find the rendered text).
                         The Claude Code session UUID is also embedded
                         here as ``_claude_session_id`` for cross-ref
                         and debugging without a schema bump (#1226).

    Cost / token / model fields ride along when the line carries them
    (assistant messages with ``message.usage.*``); legacy
    ``_extract_cost_tokens_model`` already handles that shape.
    """
    if not isinstance(obj, dict):
        return None
    ts = obj.get("timestamp") or obj.get("ts")
    if not ts:
        return None
    evt_type = str(obj.get("type") or "unknown")
    if kind == "subagent":
        evt_type = f"subagent:{evt_type}"
    join_id = openclaw_session_id or session_id
    # Stable id (#1232): top-level events use the canonical CC id derivation
    # so they collide with the legacy path #1 writes (sync_claude_cli_sessions)
    # and the process-inspection path #2. Subagent rows keep the
    # path-scoped scheme — different subagent files can legitimately reuse
    # the same uuid/line-number, so the file basename must scope the id.
    if kind == "subagent":
        eid_inner = obj.get("uuid") or obj.get("id") or f"line:{line_no}"
        if subagent_file:
            eid_inner = f"{subagent_file}:{eid_inner}"
        eid = f"openclaw-cc:{join_id}:{kind}:{eid_inner}"
    else:
        # ``kind="top"`` (and any future top-level-equivalent kind) flows
        # through the canonical CC id — see the comment block above
        # ``_canonical_event_id`` for the full design rationale.
        eid = _canonical_event_id(obj, session_id=join_id)
    cost_usd, token_count, model = _extract_cost_tokens_model(obj)
    # Embed cross-ref metadata in data so Brain / debugging can correlate
    # the OpenClaw side ↔ Claude CLI side without a schema change. We copy
    # the dict so we don't mutate the caller's parsed line.
    out_data = dict(obj)
    out_data["_claude_session_id"] = session_id
    if openclaw_session_id:
        out_data["_openclaw_session_id"] = openclaw_session_id
    if kind != "top":
        out_data["_oc_cc_kind"] = kind
    if subagent_file:
        out_data["_subagent_file"] = subagent_file
    return {
        "id": eid,
        "node_id": node_id,
        "agent_type": "openclaw",
        "agent_id": "main",
        "session_id": join_id,
        "workspace_id": obj.get("cwd") or obj.get("workspace_id"),
        "event_type": evt_type,
        "ts": str(ts),
        "data": out_data,
        "cost_usd": cost_usd,
        "token_count": token_count,
        "model": model,
    }


# Hard cap — never read more than this many *new* lines from a single
# file in one cycle, so a freshly discovered multi-MB file doesn't stall
# the cycle. The next cycle picks up where this one left off.
_OC_CC_MAX_LINES_PER_FILE_PER_CYCLE = 5000


def sync_openclaw_claude_sessions(
    config: dict | None,
    state: dict,
    paths: dict | None = None,
    skip_claude_ids: set[str] | None = None,
) -> int:
    """Discover OpenClaw-spawned ``claude`` CLI session files via process
    inspection and tail their newly-appended bytes into the local DuckDB
    ``events`` table.

    SECONDARY discovery path. The PRIMARY path is
    :func:`sync_openclaw_claude_sessions_via_index`, which walks
    ``sessions.json`` and follows the ``claudeCliSessionId`` binding.
    This function only fires for sessions whose binding hasn't been
    written to ``sessions.json`` yet (e.g. mid-session, or after a
    crash that lost the binding) — exactly the historical failure
    mode PR #1224 was designed to catch.

    ``skip_claude_ids`` lets the caller suppress sessions already
    handled by the index path so we don't double-write rows. The
    events PRIMARY KEY would dedup them anyway, but skipping saves
    the file IO.

    Returns the number of events ingested this call. Designed to be
    called once per daemon sync cycle. All failure modes are swallowed
    and logged at WARN — this is best-effort observability, not a
    correctness path for OpenClaw itself.

    Default: ON. Set ``CLAWMETRY_DISABLE_CLAUDE_SESSION_INGEST=1`` to
    disable (escape hatch only — every previous "off by default" rollout
    of a MOAT capability has bitten us in production).

    State layout (stored in ``state`` so it survives daemon restarts):

        state['claude_session_byte_offsets'] = {
            '/abs/path/to/session.jsonl': 12345,   # bytes consumed
            …
        }

    Idempotency: writes go through ``local_store.ingest_many`` which
    upserts on the events table's ``(agent_type, id)`` PRIMARY KEY,
    so re-reading a line is a no-op. Byte offsets are still tracked so
    the steady-state cycle reads only the tail.
    """
    if os.environ.get("CLAWMETRY_DISABLE_CLAUDE_SESSION_INGEST", "").strip() in (
        "1", "true", "yes", "on",
    ):
        return 0
    try:
        if not _sync_allowed():
            return 0
    except Exception:
        pass  # _sync_allowed only matters in the cloud-sync path

    node_id = (config or {}).get("node_id") or "local"

    try:
        targets = _discover_openclaw_claude_session_files()
    except Exception as e:
        log.debug("openclaw-cc discovery failed (non-fatal): %s", e)
        return 0
    if not targets:
        return 0
    if skip_claude_ids:
        targets = [
            (sid, p) for (sid, p) in targets
            if sid not in skip_claude_ids
        ]
        if not targets:
            return 0

    offsets: dict = state.setdefault("claude_session_byte_offsets", {})
    rows: list[dict] = []
    files_touched: list[str] = []

    for sess_id, jsonl_path in targets:
        key = _openclaw_claude_session_offset_key(jsonl_path)
        try:
            cur_size = os.path.getsize(jsonl_path)
        except OSError:
            continue
        last_off = int(offsets.get(key, 0) or 0)
        # File rotated / truncated — re-read from start. Cheap because
        # ingest_many is idempotent on the row id.
        if last_off > cur_size:
            last_off = 0
        if last_off >= cur_size:
            # No new bytes; nothing to do but record discovery for the
            # state file so a daemon restart doesn't re-read the world.
            offsets[key] = cur_size
            continue
        try:
            with open(jsonl_path, "rb") as f:
                f.seek(last_off)
                # Read up to a hard cap so a multi-MB cold file doesn't
                # stall this cycle. The remainder rolls into the next
                # cycle on the same offset key.
                lines_read = 0
                buf_lines: list[str] = []
                for raw in f:
                    lines_read += 1
                    if lines_read > _OC_CC_MAX_LINES_PER_FILE_PER_CYCLE:
                        break
                    buf_lines.append(raw.decode("utf-8", errors="replace"))
                # Track exact byte position of the last fully-read newline
                # so a partial trailing line on the next cycle resumes
                # from the correct offset. ``f.tell()`` after iteration
                # is the byte index AFTER the last line we consumed.
                new_off = f.tell()
        except OSError as e:
            log.debug("openclaw-cc read error %s (non-fatal): %s", jsonl_path, e)
            continue

        for i, raw_line in enumerate(buf_lines):
            stripped = raw_line.strip()
            if not stripped:
                continue
            try:
                obj = json.loads(stripped)
            except Exception:
                # Skip malformed JSON; advance offset so we don't re-try
                # forever on a known-bad line.
                continue
            row = _translate_claude_session_line(
                obj,
                session_id=sess_id,
                node_id=node_id,
                line_no=last_off + i,  # rough — only used for fallback id
            )
            if row is not None:
                rows.append(row)

        offsets[key] = new_off
        files_touched.append(jsonl_path)

    if rows:
        try:
            from clawmetry import local_store
            local_store.get_store().ingest_many(rows)
        except Exception as e:
            log.warning(
                "openclaw-cc local-store ingest failed (non-fatal): %s", e,
            )
            return 0

    if files_touched and rows:
        log.debug(
            "openclaw-cc: ingested %d events from %d file(s): %s",
            len(rows), len(files_touched),
            ", ".join(os.path.basename(p) for p in files_touched),
        )
    return len(rows)


# ── Sync: OpenClaw → Claude Code sessions via sessions.json (PR #1226) ───────
#
# PRIMARY discovery path. Reads ``~/.openclaw/agents/main/sessions/sessions.json``
# (the same index sync_claude_cli_sessions reads for the cloud-stream path)
# and follows ``cliSessionIds.claude-cli`` (or legacy ``claudeCliSessionId``)
# into ``~/.claude/projects/<encoded-cwd>/`` to capture three classes of files:
#
#   1. <claude-id>.jsonl                   — top-level transcript
#   2. <claude-id>/subagents/*.jsonl       — sub-agent transcripts
#   3. <claude-id>/tool-results/*          — tool-result dumps (opaque text)
#
# All three classes write into the local DuckDB ``events`` table keyed under
# the OpenClaw session UUID (NOT the Claude Code UUID). Plus we upsert one row
# into ``sessions`` per OpenClaw session so the typed-session view in
# ``query_sessions_table`` joins against these events.
#
# Why this exists: PR #1224 wired up process-inspection discovery and tagged
# events under the Claude UUID. Brain's join queries miss those rows, and
# sub-agent transcripts + tool-results were never captured at all. Diya
# (OpenClaw's bot) flagged these three gaps explicitly when verifying the
# install. This PR closes them.
#
# Diya's diagnosis (verbatim from the user):
#   "Sub-agent transcripts and large tool outputs live at
#    49f1d9fc-.../subagents/ and 49f1d9fc-.../tool-results/ — alongside the
#    top-level transcript."
#   "It needs to follow claudeCliSessionId into ~/.claude/projects/ to get
#    the real conversation."
#   "sessions.json lists a sessionFile at ~/.openclaw/agents/main/sessions/
#    625c0ad9-….jsonl, but I checked: that file does not exist. The generic
#    OpenClaw write path only runs when OpenClaw uses its built-in agent
#    loop. With the Claude CLI provider, that path is bypassed and the CLI
#    owns the transcript."

# Hard cap on tool-result body length stored in `data` (truncated). We
# don't want a 1 MB grep dump occupying a single row.
_OC_CC_TOOL_RESULT_MAX_BYTES = 64 * 1024

# Cap on number of tool-result files ingested per session per cycle, so a
# fresh discovery of a 100-file dir doesn't stall the cycle.
_OC_CC_MAX_TOOL_RESULTS_PER_CYCLE = 200

# Cap on number of subagent files inspected per session per cycle.
_OC_CC_MAX_SUBAGENT_FILES_PER_CYCLE = 50


def _walk_openclaw_session_bindings(sessions_dir: str) -> list[dict]:
    """Read ``~/.openclaw/agents/main/sessions/sessions.json`` and return one
    binding dict per session that has a Claude CLI binding. Each dict has:

      * ``key``                — sessions.json top-level key (e.g. ``agent:main:main``)
      * ``openclaw_session_id`` — the OpenClaw session UUID
      * ``claude_session_id``  — the Claude Code session UUID
      * ``workspace_dir``      — the agent CWD (from systemPromptReport)
      * ``title``              — origin.label / chatType / key (best-effort)
      * ``started_at``         — ISO ts (from sessionStartedAt or startedAt)
      * ``last_active_at``     — ISO ts (from lastInteractionAt or updatedAt)
      * ``status``             — sessions.json ``status`` field, default 'active'
      * ``origin``             — full origin dict (for metadata)

    Returns ``[]`` if the index doesn't exist or can't be parsed. Never
    raises — best-effort observability.
    """
    if not sessions_dir:
        return []
    index_path = os.path.join(sessions_dir, "sessions.json")
    if not os.path.isfile(index_path):
        return []
    try:
        with open(index_path) as fi:
            idx = json.load(fi)
    except Exception:
        return []
    if not isinstance(idx, dict):
        return []
    out: list[dict] = []
    for key, meta in idx.items():
        if not isinstance(meta, dict):
            continue
        cli_id = meta.get("claudeCliSessionId") or (
            meta.get("cliSessionIds", {}) or {}
        ).get("claude-cli")
        if not cli_id:
            continue
        oc_id = meta.get("sessionId")
        if not oc_id:
            continue
        # workspace_dir comes from systemPromptReport.workspaceDir (the CLI's
        # cwd). When that's missing — e.g. a pre-systemPromptReport session
        # written by an older OpenClaw — fall back to the OpenClaw default
        # workspace, which is the only CWD the user has anyway.
        sp = meta.get("systemPromptReport") or {}
        workspace = sp.get("workspaceDir") or os.path.join(
            _get_openclaw_dir(), "workspace",
        )
        # Title: origin.label > chatType > key — Brain renders this in the
        # session list so an empty string is jarring.
        origin = meta.get("origin") or {}
        title = (
            origin.get("label")
            or meta.get("chatType")
            or key
        )
        # Convert ms-epoch fields to ISO so downstream renderers don't have
        # to special-case sessions vs events. sessionStartedAt is the canonical
        # name; older OpenClaw used startedAt.
        def _iso(ms_or_iso):
            if not ms_or_iso:
                return None
            if isinstance(ms_or_iso, (int, float)):
                try:
                    return datetime.fromtimestamp(
                        ms_or_iso / 1000.0, tz=timezone.utc,
                    ).isoformat().replace("+00:00", "Z")
                except (ValueError, OSError):
                    return None
            return str(ms_or_iso)

        out.append({
            "key": key,
            "openclaw_session_id": str(oc_id),
            "claude_session_id": str(cli_id),
            "workspace_dir": workspace,
            "title": str(title)[:200] if title else key,
            "started_at": _iso(
                meta.get("sessionStartedAt") or meta.get("startedAt"),
            ),
            "last_active_at": _iso(
                meta.get("lastInteractionAt") or meta.get("updatedAt"),
            ),
            "status": meta.get("status") or "active",
            "origin": origin,
            "channel": (
                origin.get("provider")
                or meta.get("lastChannel")
                or (meta.get("deliveryContext") or {}).get("channel")
            ),
            "chat_type": meta.get("chatType"),
        })
    return out


# INVARIANT: ``claude_session_id`` MUST originate from sessions.json's
# ``claudeCliSessionId`` field — never from globbing/listing the parent dir.
# The encoded-cwd slug under ``~/.claude/projects/`` is shared by EVERY
# ``claude`` invocation the user ever ran from the OpenClaw workspace,
# including personal chats the user did not intend to observe. The
# ``allowed_claude_session_ids`` allowlist (built from sessions.json by the
# caller) is the only thing keeping us from sweeping those into the cloud-
# sync pipeline. Future refactors: keep this gate or replicate it; do NOT
# loosen it to "all sessions in this workspace". See issue #1231.
def _assert_claude_session_allowed(
    claude_session_id: str, allowed_claude_session_ids: set[str],
) -> None:
    """Privacy gate. Raise ``PermissionError`` if ``claude_session_id`` was
    not harvested from OpenClaw's sessions.json — i.e. it is not a Claude
    CLI session OpenClaw bound to one of its own OpenClaw sessions.

    A plain ``assert`` would be stripped by ``python -O``; this raises
    unconditionally because the boundary is privacy-critical.
    """
    if claude_session_id not in allowed_claude_session_ids:
        raise PermissionError(
            "refusing to walk ~/.claude/projects for session "
            f"{claude_session_id!r}: not in sessions.json allowlist "
            f"(size={len(allowed_claude_session_ids)})"
        )


def _claude_session_dir(
    workspace_dir: str,
    claude_session_id: str,
    allowed_claude_session_ids: set[str],
) -> Path:
    """Return ``~/.claude/projects/<encoded-cwd>/<claude-session-id>/`` —
    the directory that holds the subagents/ and tool-results/ subdirs.

    ``allowed_claude_session_ids`` MUST be the set of Claude CLI session
    UUIDs harvested from ``sessions.json``. See the invariant comment
    above ``_assert_claude_session_allowed``.
    """
    _assert_claude_session_allowed(claude_session_id, allowed_claude_session_ids)
    slug = _encode_cwd_for_claude_projects(workspace_dir)
    return _claude_projects_root() / slug / claude_session_id


def _claude_session_top_level_path(
    workspace_dir: str,
    claude_session_id: str,
    allowed_claude_session_ids: set[str],
) -> Path:
    """Return the top-level ``<claude-id>.jsonl`` path. Guarded by the
    sessions.json allowlist — see ``_assert_claude_session_allowed``."""
    _assert_claude_session_allowed(claude_session_id, allowed_claude_session_ids)
    slug = _encode_cwd_for_claude_projects(workspace_dir)
    return _claude_projects_root() / slug / f"{claude_session_id}.jsonl"


def _upsert_openclaw_session_row(binding: dict, node_id: str) -> None:
    """Upsert a row into the typed ``sessions`` table for an OpenClaw session,
    keyed by the OpenClaw session UUID. Best-effort — failures are logged
    and swallowed so observability doesn't block ingest.
    """
    try:
        from clawmetry import local_store
        store = local_store.get_store()
    except Exception as e:
        log.debug("openclaw-cc upsert_session: store unavailable: %s", e)
        return
    try:
        store.ingest_session({
            "agent_type": "openclaw",
            "session_id": binding["openclaw_session_id"],
            "node_id": node_id,
            "agent_id": "main",
            "workspace_id": binding.get("workspace_dir"),
            "title": binding.get("title"),
            "started_at": binding.get("started_at"),
            "last_active_at": binding.get("last_active_at"),
            "status": binding.get("status") or "active",
            "metadata": {
                "claude_session_id": binding.get("claude_session_id"),
                "key": binding.get("key"),
                "origin": binding.get("origin"),
                "channel": binding.get("channel"),
                "chat_type": binding.get("chat_type"),
            },
        })
    except Exception as e:
        log.debug("openclaw-cc upsert_session failed (non-fatal): %s", e)
    # Also write the openclaw_channels row so the channel pill renders.
    if binding.get("channel") or binding.get("origin"):
        try:
            origin = binding.get("origin") or {}
            store.ingest_channel({
                "session_id": binding["openclaw_session_id"],
                "channel": binding.get("channel"),
                "chat_type": binding.get("chat_type"),
                "subject": origin.get("label"),
                "origin_label": origin.get("label"),
            })
        except Exception as e:
            log.debug("openclaw-cc ingest_channel failed (non-fatal): %s", e)


def _ingest_jsonl_file_tail(
    jsonl_path: str,
    *,
    state: dict,
    node_id: str,
    claude_session_id: str,
    openclaw_session_id: str | None,
    kind: str,
    subagent_file: str | None,
) -> tuple[list[dict], int]:
    """Tail a JSONL file by byte offset and translate each new line into
    an events row. Returns ``(rows, lines_read)``. State is updated in-place.

    Shared between top-level and subagent file ingestion. Idempotent —
    re-reads emit identical row ids that hit the events PRIMARY KEY.
    """
    offsets: dict = state.setdefault("claude_session_byte_offsets", {})
    key = _openclaw_claude_session_offset_key(jsonl_path)
    rows: list[dict] = []
    try:
        cur_size = os.path.getsize(jsonl_path)
    except OSError:
        return rows, 0
    last_off = int(offsets.get(key, 0) or 0)
    if last_off > cur_size:
        last_off = 0
    if last_off >= cur_size:
        offsets[key] = cur_size
        return rows, 0
    try:
        with open(jsonl_path, "rb") as f:
            f.seek(last_off)
            lines_read = 0
            buf_lines: list[str] = []
            for raw in f:
                lines_read += 1
                if lines_read > _OC_CC_MAX_LINES_PER_FILE_PER_CYCLE:
                    break
                buf_lines.append(raw.decode("utf-8", errors="replace"))
            new_off = f.tell()
    except OSError as e:
        log.debug("openclaw-cc read error %s (non-fatal): %s", jsonl_path, e)
        return rows, 0
    for i, raw_line in enumerate(buf_lines):
        stripped = raw_line.strip()
        if not stripped:
            continue
        try:
            obj = json.loads(stripped)
        except Exception:
            continue
        row = _translate_claude_session_line(
            obj,
            session_id=claude_session_id,
            node_id=node_id,
            line_no=last_off + i,
            openclaw_session_id=openclaw_session_id,
            kind=kind,
            subagent_file=subagent_file,
        )
        if row is not None:
            rows.append(row)
    offsets[key] = new_off
    return rows, len(buf_lines)


def _ingest_tool_result_files(
    tool_results_dir: Path,
    *,
    state: dict,
    node_id: str,
    claude_session_id: str,
    openclaw_session_id: str,
) -> list[dict]:
    """Translate each tool-result file under ``<claude-id>/tool-results/`` into
    one events row. Tool-results are arbitrary text dumps (the on-disk shape
    Claude Code uses for large grep / WebFetch / Read outputs that don't fit
    inline in the transcript). Each file's basename is its stable id, so we
    dedup by (session, basename) regardless of size or content.

    State tracks per-file mtime; we re-read only on mtime bump (or on first
    discovery). The body is truncated to ``_OC_CC_TOOL_RESULT_MAX_BYTES``
    so the row stays small — full dumps live on disk anyway.
    """
    rows: list[dict] = []
    if not tool_results_dir.is_dir():
        return rows
    seen_mtimes: dict = state.setdefault("claude_tool_result_mtimes", {})
    try:
        entries = list(tool_results_dir.iterdir())
    except OSError:
        return rows
    # Cap so a freshly populated dir doesn't stall the cycle.
    entries.sort(key=lambda p: p.name)
    if len(entries) > _OC_CC_MAX_TOOL_RESULTS_PER_CYCLE:
        entries = entries[:_OC_CC_MAX_TOOL_RESULTS_PER_CYCLE]
    for entry in entries:
        try:
            if not entry.is_file():
                continue
            mtime = entry.stat().st_mtime
        except OSError:
            continue
        seen_key = f"{claude_session_id}:{entry.name}"
        if seen_mtimes.get(seen_key) == mtime:
            continue
        # Read up to the truncation cap so we never DoS ourselves on a
        # multi-MB grep result. Beyond the cap we record metadata only.
        try:
            with open(entry, "rb") as f:
                head_bytes = f.read(_OC_CC_TOOL_RESULT_MAX_BYTES + 1)
        except OSError:
            continue
        truncated = len(head_bytes) > _OC_CC_TOOL_RESULT_MAX_BYTES
        body = head_bytes[:_OC_CC_TOOL_RESULT_MAX_BYTES].decode(
            "utf-8", errors="replace",
        )
        try:
            size = entry.stat().st_size
        except OSError:
            size = len(head_bytes)
        ts_iso = datetime.fromtimestamp(
            mtime, tz=timezone.utc,
        ).isoformat().replace("+00:00", "Z")
        rows.append({
            "id": (
                f"openclaw-cc:{openclaw_session_id}:tool-result:{entry.name}"
            ),
            "node_id": node_id,
            "agent_type": "openclaw",
            "agent_id": "main",
            "session_id": openclaw_session_id,
            "workspace_id": None,
            "event_type": "tool-result",
            "ts": ts_iso,
            "data": {
                "_claude_session_id": claude_session_id,
                "_openclaw_session_id": openclaw_session_id,
                "_oc_cc_kind": "tool-result",
                "filename": entry.name,
                "size_bytes": size,
                "truncated": truncated,
                "body": body,
            },
            "cost_usd": None,
            "token_count": None,
            "model": None,
        })
        seen_mtimes[seen_key] = mtime
    return rows


def sync_openclaw_claude_sessions_via_index(
    config: dict | None,
    state: dict,
    paths: dict | None = None,
) -> tuple[int, set[str]]:
    """Primary discovery path: walk OpenClaw's sessions.json and tail the
    top-level + subagent + tool-result files Claude Code wrote for each
    bound session.

    Returns ``(events_ingested, claude_ids_handled)``. The second tuple
    element is consumed by the process-inspection fallback so it can skip
    sessions we've already covered here.

    Default: ON. Same escape hatch as the process-inspection path
    (``CLAWMETRY_DISABLE_CLAUDE_SESSION_INGEST=1``).
    """
    if os.environ.get("CLAWMETRY_DISABLE_CLAUDE_SESSION_INGEST", "").strip() in (
        "1", "true", "yes", "on",
    ):
        return 0, set()
    try:
        if not _sync_allowed():
            return 0, set()
    except Exception:
        pass

    node_id = (config or {}).get("node_id") or "local"
    paths = paths or {}
    sessions_dir = paths.get("sessions_dir") or os.path.join(
        _get_openclaw_dir(), "agents", "main", "sessions",
    )
    bindings = _walk_openclaw_session_bindings(sessions_dir)
    if not bindings:
        return 0, set()

    # PRIVACY GATE (issue #1231): build the allowlist of Claude CLI session
    # UUIDs once, from sessions.json, and pass it through to every helper
    # that constructs a ``~/.claude/projects/...`` path. This is the only
    # thing preventing a refactor from silently sweeping personal
    # (non-OpenClaw) Claude chats out of the encoded-cwd dir into cloud
    # sync. Never derive the path from a glob of the parent dir.
    allowed_claude_ids: set[str] = {
        b["claude_session_id"] for b in bindings if b.get("claude_session_id")
    }

    rows: list[dict] = []
    handled: set[str] = set()
    files_touched: list[str] = []
    sessions_upserted: list[str] = []

    for binding in bindings:
        claude_id = binding["claude_session_id"]
        oc_id = binding["openclaw_session_id"]
        workspace = binding["workspace_dir"]

        top_path = _claude_session_top_level_path(
            workspace, claude_id, allowed_claude_ids,
        )
        sess_dir = _claude_session_dir(
            workspace, claude_id, allowed_claude_ids,
        )
        # If neither the top-level file nor the subdir exists, this binding
        # points at a Claude session that hasn't started writing — skip it
        # this cycle, the daemon will re-check next cycle.
        if not top_path.is_file() and not sess_dir.is_dir():
            continue

        # Always upsert the sessions row first so even an empty / not-yet-
        # written top-level file produces a renderable session in the UI.
        # Idempotent (ON CONFLICT DO UPDATE).
        _upsert_openclaw_session_row(binding, node_id)
        sessions_upserted.append(oc_id)
        handled.add(claude_id)

        # 1. Top-level transcript
        if top_path.is_file():
            top_rows, _ = _ingest_jsonl_file_tail(
                str(top_path),
                state=state,
                node_id=node_id,
                claude_session_id=claude_id,
                openclaw_session_id=oc_id,
                kind="top",
                subagent_file=None,
            )
            if top_rows:
                rows.extend(top_rows)
                files_touched.append(str(top_path))

        # 2. Sub-agent transcripts — one JSONL per spawned sub-agent.
        subagents_dir = sess_dir / "subagents"
        if subagents_dir.is_dir():
            try:
                sub_files = sorted(subagents_dir.glob("*.jsonl"))
            except OSError:
                sub_files = []
            if len(sub_files) > _OC_CC_MAX_SUBAGENT_FILES_PER_CYCLE:
                sub_files = sub_files[:_OC_CC_MAX_SUBAGENT_FILES_PER_CYCLE]
            for sub_path in sub_files:
                sub_rows, _ = _ingest_jsonl_file_tail(
                    str(sub_path),
                    state=state,
                    node_id=node_id,
                    claude_session_id=claude_id,
                    openclaw_session_id=oc_id,
                    kind="subagent",
                    subagent_file=sub_path.stem,
                )
                if sub_rows:
                    rows.extend(sub_rows)
                    files_touched.append(str(sub_path))

        # 3. Tool-result dumps — one event per file, dedup by mtime.
        tool_dir = sess_dir / "tool-results"
        tr_rows = _ingest_tool_result_files(
            tool_dir,
            state=state,
            node_id=node_id,
            claude_session_id=claude_id,
            openclaw_session_id=oc_id,
        )
        if tr_rows:
            rows.extend(tr_rows)
            files_touched.append(str(tool_dir))

    if rows:
        try:
            from clawmetry import local_store
            local_store.get_store().ingest_many(rows)
        except Exception as e:
            log.warning(
                "openclaw-cc-index local-store ingest failed (non-fatal): %s", e,
            )
            return 0, handled

    if rows or sessions_upserted:
        log.debug(
            "openclaw-cc-index: %d events / %d sessions / %d files",
            len(rows), len(sessions_upserted), len(files_touched),
        )
    return len(rows), handled


# ── Sync: channel-adapter transcripts (Telegram, Signal, WhatsApp, …) ────────
#
# OpenClaw's chat-channel adapters persist inbound/outbound messages to a
# per-provider directory next to ``agents/``:
#
#   ~/.openclaw/telegram/<chat_id>.jsonl
#   ~/.openclaw/signal/<chat_id>.jsonl
#   ~/.openclaw/whatsapp/<chat_id>.jsonl
#   ~/.openclaw/discord/<channel_id>.jsonl
#   ~/.openclaw/slack/<channel_id>.jsonl
#   ~/.openclaw/imessage/<chat_id>.jsonl
#   ~/.openclaw/webchat/<session_id>.jsonl
#   …                    (one dir per adapter — see routes/channels.py)
#
# Until this PR, ``sync.py`` only watched ``agents/main/sessions/`` which made
# the Brain tab + ``channel_messages`` table miss every chat-channel turn —
# the user observed "I message Diya on Telegram and ClawMetry shows nothing".
#
# DuckDB-first HARD RULE: every event lands in the ``events`` table (so
# Brain/timeline reads see it) AND, when it parses as a chat turn, in
# ``channel_messages`` (so per-provider routes in ``routes/channels.py`` see
# it). No JSONL re-read at request time.
#
# The directory layout below is the canonical list maintained alongside the
# 21 adapter routes in ``routes/channels.py``. If a new adapter ships, add its
# directory name to ``_CHANNEL_DIRS`` and the daemon will pick it up on the
# next cycle — no further wiring required.
_CHANNEL_DIRS: tuple[str, ...] = (
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

# Filenames inside ``~/.openclaw/<channel>/`` that are NOT conversation
# transcripts — they're per-adapter bookkeeping (offset trackers, schema
# manifests, etc.). Skip them so we don't crash on JSON-object-per-file
# layouts and don't pollute ``events`` with daemon plumbing.
_CHANNEL_NON_TRANSCRIPT_BASENAMES: frozenset[str] = frozenset({
    "update-offset-default.json",
    "schema.json",
    "manifest.json",
})


def _list_channel_transcripts(channel_dir: str) -> list[str]:
    """Return paths to all *transcript* files under a single channel dir.

    A "transcript" is any ``*.jsonl`` (live or archived ``.jsonl.reset.<ts>``);
    we explicitly skip the per-adapter bookkeeping files listed in
    ``_CHANNEL_NON_TRANSCRIPT_BASENAMES``. The dashboard read path applies
    the same exclusion via ``routes/channels.py``.
    """
    out: list[str] = []
    try:
        for fname in os.listdir(channel_dir):
            if fname in _CHANNEL_NON_TRANSCRIPT_BASENAMES:
                continue
            # We accept .jsonl (live) and .jsonl.reset.<ts> (archived).
            if fname.endswith(".jsonl") or ".jsonl.reset." in fname:
                out.append(os.path.join(channel_dir, fname))
    except OSError:
        pass
    return out


def _parse_channel_event(
    obj: dict, *, provider: str, channel_id: str
) -> dict | None:
    """Project one channel-jsonl line into a ``channel_messages`` row dict
    (issue #1220: single chokepoint).

    The provider/channel-id are taken from the file path (cheap, robust),
    and the per-event fields are read from a deliberately permissive set
    of keys so we accept whatever shape the adapter writes:

    * direction   — ``direction`` | ``"in"`` if a ``from``/``sender`` block
                    is present | ``"out"`` if an ``assistant`` role / ``to``
                    block is present. Defaults to ``"in"`` (most adapter
                    jsonls record inbound first).
    * body        — first present of ``text`` | ``body`` | ``message`` |
                    ``content`` (string form) | content[0].text.
    * sender_id   — ``sender_id`` | ``from.id`` | ``user.id`` | ``user_id``.
    * sender_name — ``sender_name`` | ``from.username`` | ``from.first_name`` |
                    ``user.name``.
    * ts          — ``ts`` | ``timestamp`` | ``date`` (epoch-secs → ISO).
    * id          — ``id`` | ``message_id`` | ``update_id`` (uniqueness key).

    Returns ``None`` for lines we can't pin to a timestamp — those are
    usually heartbeat/keepalive plumbing the adapter writes between real
    messages. The caller passes the returned dict to
    ``LocalStore.ingest_channel_event`` which fans it out onto BOTH the
    ``channel_messages`` and ``events`` tables in one shot.
    """
    if not isinstance(obj, dict):
        return None

    # ── ts ───────────────────────────────────────────────────────────────
    raw_ts = obj.get("ts") or obj.get("timestamp") or obj.get("date")
    if not raw_ts:
        return None
    if isinstance(raw_ts, (int, float)):
        # Telegram/WhatsApp encode date as epoch seconds; coerce so all
        # downstream sorts work on ISO strings.
        try:
            raw_ts = datetime.fromtimestamp(
                float(raw_ts), tz=timezone.utc
            ).isoformat()
        except (ValueError, OSError, OverflowError):
            return None
    ts = str(raw_ts)

    # ── id (stable across re-ingest) ─────────────────────────────────────
    raw_id = (
        obj.get("id")
        or obj.get("message_id")
        or obj.get("messageId")
        or obj.get("update_id")
        or obj.get("updateId")
    )
    if raw_id is None:
        raw_id = f"{provider}:{channel_id}:{ts}"
    eid = f"{provider}:{channel_id}:{raw_id}"

    # ── direction ────────────────────────────────────────────────────────
    direction = obj.get("direction")
    if direction not in ("in", "out"):
        if obj.get("role") == "assistant" or obj.get("from_bot") is True:
            direction = "out"
        elif obj.get("from") or obj.get("sender") or obj.get("user"):
            direction = "in"
        else:
            direction = "in"

    # ── body ─────────────────────────────────────────────────────────────
    body = obj.get("text") or obj.get("body") or obj.get("message")
    if body is None:
        content = obj.get("content")
        if isinstance(content, str):
            body = content
        elif isinstance(content, list):
            for c in content:
                if isinstance(c, dict) and c.get("type") == "text":
                    body = c.get("text") or ""
                    if body:
                        break
    if body is not None:
        body = str(body)

    # ── sender ───────────────────────────────────────────────────────────
    sender_block = obj.get("from") or obj.get("sender") or obj.get("user") or {}
    if not isinstance(sender_block, dict):
        sender_block = {}
    sender_id = (
        obj.get("sender_id")
        or sender_block.get("id")
        or obj.get("user_id")
        or channel_id
    )
    sender_name = (
        obj.get("sender_name")
        or sender_block.get("username")
        or sender_block.get("first_name")
        or sender_block.get("name")
    )

    return {
        "id": eid,
        "agent_id": "main",
        "provider": provider,
        "channel_id": str(channel_id),
        "sender_id": str(sender_id) if sender_id is not None else None,
        "sender_name": sender_name,
        "body": (body[:4000] if body else None),
        "ts": ts,
        "direction": direction,
        "session_key": obj.get("session_id") or obj.get("session_key"),
        # raw_blob carries the full source line. ``ingest_channel_event``
        # flattens this dict into the events-table ``data`` blob so the
        # Brain feed renders the same fields the per-channel detail view
        # has — single source of truth, no drift.
        "raw_blob": obj,
    }


def sync_channel_messages(config: dict, state: dict, paths: dict) -> int:
    """Tail each ``~/.openclaw/<channel>/*.jsonl`` and ingest both events
    + channel_messages rows into local DuckDB.

    Returns the number of NEW rows ingested this cycle. Idempotent — the
    PRIMARY KEY on each table absorbs replays. Per-file offsets live in
    ``state["last_channel_offsets"]`` so we don't re-scan from byte zero
    on every cycle.
    """
    if not _sync_allowed():
        return 0
    _record_sync_progress("channel_messages", 0)
    from clawmetry import local_store

    openclaw_root = Path(_get_openclaw_dir())
    offsets: dict = state.setdefault("last_channel_offsets", {})
    store = local_store.get_store()
    node_id = config["node_id"]
    total = 0

    for provider in _CHANNEL_DIRS:
        if total >= MAX_EVENTS_PER_CYCLE:
            break
        channel_dir = openclaw_root / provider
        if not channel_dir.is_dir():
            continue
        for fpath in _list_channel_transcripts(str(channel_dir)):
            if total >= MAX_EVENTS_PER_CYCLE:
                break
            fname = os.path.basename(fpath)
            # Strip both .jsonl and any .reset.<ts> suffix to get the
            # canonical chat_id (== filename stem). Telegram writes
            # ``<chat_id>.jsonl``; archived resets share the same chat_id.
            channel_id = fname.split(".jsonl", 1)[0]
            offset_key = f"{provider}/{fname}"
            offset = int(offsets.get(offset_key, 0))
            channel_batch: list[dict] = []

            try:
                with open(fpath, "r", errors="replace") as f:
                    f.seek(0, 2)
                    size = f.tell()
                    if offset > size:
                        # File was rotated/truncated — restart from byte 0
                        # rather than skip silently. DuckDB PK dedupes
                        # any replayed messages on the upstream id.
                        offset = 0
                    f.seek(offset)
                    for raw in f:
                        raw = raw.strip()
                        if not raw:
                            continue
                        try:
                            obj = json.loads(raw)
                        except Exception:
                            continue
                        ch = _parse_channel_event(
                            obj, provider=provider, channel_id=channel_id
                        )
                        if ch is None:
                            continue
                        channel_batch.append(ch)
                        if len(channel_batch) >= BATCH_SIZE:
                            break
                    offsets[offset_key] = f.tell()
            except OSError as e:
                log.warning(
                    "channel sync error (%s/%s): %s", provider, fname, e
                )
                continue

            # Issue #1220: single chokepoint writes channel_messages +
            # events atomically per row. Replaces the prior split-write
            # that batched events through ingest_many() and then looped
            # ingest_channel_message() afterward — the two writers used
            # to drift any time the projection logic was touched on one
            # side and not the other (#1212 P0). Per-row try/except so
            # a single malformed row can't take down the whole batch.
            ingested = 0
            for ch in channel_batch:
                try:
                    store.ingest_channel_event(ch, node_id=node_id)
                    ingested += 1
                except Exception as e:
                    log.debug(
                        "channel_event ingest skipped (%s/%s): %s",
                        provider, fname, e,
                    )
            total += ingested

    _record_sync_progress("channel_messages", total, total)
    return total


# ── Sync: logs (full lines, encrypted) ────────────────────────────────────────


def sync_logs(config: dict, state: dict, paths: dict) -> int:
    # Skipped when sync is paused (expired trial). Offsets persist so
    # nothing is lost on resume.
    if not _sync_allowed():
        return 0
    log_dir = paths["log_dir"]
    api_key = config["api_key"]
    enc_key = config.get("encryption_key")
    node_id = config["node_id"]
    offsets: dict = state.setdefault("last_log_offsets", {})
    total = 0

    log_files = sorted(glob.glob(os.path.join(log_dir, "openclaw-*.log")))[-5:]
    for fpath in log_files:
        fname = os.path.basename(fpath)
        offset = offsets.get(fname, 0)
        entries: list[dict] = []

        try:
            with open(fpath, "r", errors="replace") as f:
                f.seek(0, 2)
                size = f.tell()
                if offset > size:
                    offset = 0
                f.seek(offset)
                for raw in f:
                    raw = raw.strip()
                    if not raw:
                        continue
                    try:
                        entries.append(json.loads(raw))
                    except Exception:
                        entries.append({"raw": raw})
                    if len(entries) >= BATCH_SIZE:
                        _flush_log_batch(entries, fname, api_key, enc_key, node_id)
                        total += len(entries)
                        entries = []
                offsets[fname] = f.tell()

            if entries:
                _flush_log_batch(entries, fname, api_key, enc_key, node_id)
                total += len(entries)

        except Exception as e:
            log.warning(f"Log sync error ({fname}): {e}")

    return total


def _flush_log_batch(
    entries: list, fname: str, api_key: str, enc_key: str | None, node_id: str
) -> None:
    payload = {"log_file": fname, "node_id": node_id, "lines": entries}
    if enc_key:
        _post(
            "/ingest/logs",
            {
                "node_id": node_id,
                "encrypted": True,
                "blob": encrypt_payload(payload, enc_key),
            },
            api_key,
        )
    else:
        _post("/ingest/logs", payload, api_key)


# ── Heartbeat ─────────────────────────────────────────────────────────────────


# Agent-install detection (cloud bug fix 2026-05-18). Cloud Run pods can't
# stat the user's home directory to decide whether OpenClaw / NemoClaw exists
# — they were hard-coding `no_agent=True` in a shim, which made the cloud
# "no agent detected" empty-state lie for every user. The daemon already
# knows (install.sh writes the same paths it checks), so we ride the answer
# up on the heartbeat envelope and the cloud aggregates across the user's
# fleet (ANY node with openclaw_detected → user has openclaw).
#
# Mirrors ``dashboard.detect_agent_install`` deliberately rather than
# importing dashboard.py: the daemon process must stay lean (importing
# dashboard pulls in Flask + 15k LOC) and these are cheap stat-only checks.
# Cached for ``_AGENT_INSTALL_TTL_SEC`` (60s) — heartbeats fire every 30s
# (FAST) or 60s (SLOW) so a 60s cache halves the syscalls without making
# the signal stale.
_AGENT_INSTALL_TTL_SEC = 60
_agent_install_cache: dict = {"ts": 0.0, "value": None}


def _detect_openclaw_install_for_heartbeat() -> bool:
    """Stat-only OpenClaw presence check (no subprocess, no DB)."""
    home = os.environ.get("OPENCLAW_HOME") or os.path.expanduser("~/.openclaw")
    if not home:
        return False
    if os.path.exists(os.path.join(home, "gateway", "gateway.pid")):
        return True
    sess_dir = os.path.join(home, "agents", "main", "sessions")
    if os.path.isdir(sess_dir):
        try:
            for name in os.listdir(sess_dir):
                if name.endswith(".jsonl"):
                    return True
        except OSError:
            pass
    ws = os.path.join(home, "workspace")
    for marker in ("SOUL.md", "AGENTS.md", "MEMORY.md"):
        if os.path.exists(os.path.join(ws, marker)):
            return True
    if os.path.isdir(home):
        try:
            if any(True for _ in os.scandir(home)):
                return True
        except OSError:
            pass
    return False


def _detect_nemoclaw_install_for_heartbeat() -> bool:
    """Stat-only NemoClaw presence check."""
    import shutil as _shutil
    if _shutil.which("nemoclaw"):
        return True
    cfg = os.path.expanduser("~/.nemoclaw")
    if os.path.isdir(cfg):
        try:
            if any(True for _ in os.scandir(cfg)):
                return True
        except OSError:
            pass
    return False


def _detect_any_local_data_for_heartbeat() -> bool:
    """Return True if local DuckDB store has any rows. Best-effort."""
    try:
        from clawmetry import local_store  # type: ignore
        store = local_store.get_store(read_only=True)
    except Exception:
        return False
    for method, kwargs in (
        ("query_events", {"limit": 1}),
        ("query_heartbeats", {"limit": 1}),
    ):
        try:
            fn = getattr(store, method, None)
            if fn is None:
                continue
            rows = fn(**kwargs)
            if rows:
                return True
        except Exception:
            continue
    return False


def _detect_agent_install_for_heartbeat() -> dict:
    """Return ``{openclaw_detected, nemoclaw_detected, any_data, signals,
    no_agent}`` — the same shape ``dashboard.detect_agent_install`` returns,
    cached for ``_AGENT_INSTALL_TTL_SEC`` seconds."""
    now = time.time()
    cached = _agent_install_cache.get("value")
    if cached and (now - _agent_install_cache["ts"]) < _AGENT_INSTALL_TTL_SEC:
        return cached
    openclaw = bool(_detect_openclaw_install_for_heartbeat())
    nemoclaw = bool(_detect_nemoclaw_install_for_heartbeat())
    any_data = bool(_detect_any_local_data_for_heartbeat())
    signals = []
    if openclaw:
        signals.append("openclaw")
    if nemoclaw:
        signals.append("nemoclaw")
    if any_data:
        signals.append("local_data")
    payload = {
        "openclaw_detected": openclaw,
        "nemoclaw_detected": nemoclaw,
        "any_data": any_data,
        "signals": signals,
        "no_agent": not (openclaw or nemoclaw or any_data),
    }
    _agent_install_cache["ts"] = now
    _agent_install_cache["value"] = payload
    return payload


def _detect_ollama_for_heartbeat():
    """Detect Ollama status for heartbeat reporting."""
    import shutil

    result = {"installed": False, "running": False, "models": []}

    # Check if binary exists
    ollama_bin = shutil.which("ollama")
    if not ollama_bin:
        common_paths = [
            "/opt/homebrew/bin/ollama",
            "/usr/local/bin/ollama",
            "/usr/bin/ollama",
            os.path.expanduser("~/.ollama/ollama"),
        ]
        if os.name == "nt":
            common_paths.extend(
                [
                    os.path.expandvars(r"%LOCALAPPDATA%\Programs\Ollama\ollama.exe"),
                    os.path.expandvars(r"%LOCALAPPDATA%\Ollama\ollama.exe"),
                ]
            )
        for p in common_paths:
            if os.path.isfile(p):
                ollama_bin = p
                break

    if ollama_bin:
        result["installed"] = True

    # Check if running + get models
    try:
        import json as _json

        req = urllib.request.Request("http://localhost:11434/api/tags", method="GET")
        with urllib.request.urlopen(req, timeout=3) as resp:
            if resp.status == 200:
                result["running"] = True
                data = _json.loads(resp.read())
                result["models"] = [
                    m.get("name", "") for m in data.get("models", [])[:10]
                ]
                result["installed"] = True  # If running, definitely installed
    except Exception:
        pass

    return result


# ── Gateway process-metric capture (#852 follow-up) ──────────────────────────
# PR #1146 added a *live* gateway-health snapshot (RSS/CPU/uptime). That's
# fine for "is it green right now?" but the gateway's slow memory-bloat-OOM
# pattern (~600 MB → ~945 MB) is only visible if you SEE THE TREND.
#
# Per the DuckDB-first rule, historical data lives in DuckDB. We capture
# gateway vitals every 30s in the daemon loop and write them as
# ``event_type="gateway.metric"`` events. The dashboard's
# ``/api/gateway-health/history`` then plots a 24h sparkline.
#
# Constraints:
#   * Every 30s max (rate-cap to keep DB writes cheap).
#   * Dedupe: if a fresh sample matches the previous one closely (within
#     5 min and small variance) we skip writing — the gateway is largely
#     idle between agent calls so otherwise we'd write ~2,880 near-identical
#     rows/day. With dedupe a typical day is ~50-300 rows.
#   * Skip writes when the gateway isn't running — no point flooding the
#     event log with "not_running" rows during dev or after a crash.
#   * Best-effort: any failure (compute_gateway_health, local_store import,
#     ingest) is swallowed; the daemon loop keeps ticking.

GATEWAY_METRIC_INTERVAL_SEC = 30
GATEWAY_METRIC_DEDUP_WINDOW_SEC = 300        # 5 min
GATEWAY_METRIC_DEDUP_RSS_TOLERANCE_MB = 5.0  # don't re-write within ±5 MB
GATEWAY_METRIC_DEDUP_CPU_TOLERANCE_PCT = 2.0  # don't re-write within ±2% CPU

# Module-level state for rate-capping + dedupe. (last_write_ts, last_payload).
# Reset on import; the daemon runs as one long-lived process, so this is fine.
# Sentinel ``None`` means "no sample written yet" — the rate-cap check skips
# the comparison so the very first call always falls through to capture.
_LAST_GATEWAY_METRIC_TS: float | None = None
_LAST_GATEWAY_METRIC: dict | None = None


def _should_dedupe_gateway_metric(prev: dict | None, curr: dict) -> bool:
    """Return True when *curr* is close enough to *prev* that we should skip
    the write. The five-minute time window is enforced by the caller — this
    helper just answers the value-similarity question.
    """
    if not isinstance(prev, dict):
        return False
    # PID changed → gateway restarted; always write.
    if prev.get("pid") != curr.get("pid"):
        return False
    prev_rss = prev.get("rss_mb")
    curr_rss = curr.get("rss_mb")
    if prev_rss is None or curr_rss is None:
        # Vitals went missing/recovered → write so the gap is visible.
        return prev_rss == curr_rss
    if abs(float(curr_rss) - float(prev_rss)) > GATEWAY_METRIC_DEDUP_RSS_TOLERANCE_MB:
        return False
    prev_cpu = prev.get("cpu_pct") or 0.0
    curr_cpu = curr.get("cpu_pct") or 0.0
    if abs(float(curr_cpu) - float(prev_cpu)) > GATEWAY_METRIC_DEDUP_CPU_TOLERANCE_PCT:
        return False
    return True


def capture_gateway_metric(config: dict) -> bool:
    """Capture one ``gateway.metric`` event into local DuckDB.

    Returns True when a row was written, False when skipped (rate-capped,
    deduped, gateway not running, or any failure).

    Imports ``routes.health.compute_gateway_health`` lazily so the daemon
    doesn't pull the dashboard module graph at import time (the daemon is
    optional; ``routes/`` is a peer of ``clawmetry/`` at the repo root).
    """
    global _LAST_GATEWAY_METRIC_TS, _LAST_GATEWAY_METRIC
    now_mono = time.monotonic()
    if (
        _LAST_GATEWAY_METRIC_TS is not None
        and (now_mono - _LAST_GATEWAY_METRIC_TS) < GATEWAY_METRIC_INTERVAL_SEC
    ):
        return False

    try:
        import routes.health as _rh  # late import — daemon is optional
    except Exception as _e:
        log.debug("gateway.metric: cannot import routes.health (%s)", _e)
        return False

    try:
        # Attribute lookup (NOT a bound reference) so tests + future
        # hot-reloads pick up monkeypatched implementations.
        snap = _rh.compute_gateway_health()
    except Exception as _e:
        log.debug("gateway.metric: compute_gateway_health failed (%s)", _e)
        return False

    if not snap or snap.get("status") == "not_running":
        # Skip noise when the gateway isn't found at all.
        _LAST_GATEWAY_METRIC_TS = now_mono
        return False

    curr = {
        "rss_mb":         snap.get("rss_mb"),
        "cpu_pct":        snap.get("cpu_pct"),
        "pid":            snap.get("pid"),
        "uptime_seconds": snap.get("uptime_seconds"),
    }

    # Dedupe within DEDUP_WINDOW: if this sample looks like the last one and
    # we wrote that one less than 5 min ago, skip the write.
    if _LAST_GATEWAY_METRIC is not None:
        elapsed = now_mono - _LAST_GATEWAY_METRIC_TS
        if elapsed < GATEWAY_METRIC_DEDUP_WINDOW_SEC and _should_dedupe_gateway_metric(
            _LAST_GATEWAY_METRIC, curr
        ):
            return False

    try:
        from clawmetry import local_store as _ls
        store = _ls.get_store()
        store.ingest({
            "id":         uuid.uuid4().hex,
            "node_id":    config.get("node_id") or "unknown",
            "agent_id":   "openclaw-gateway",
            "agent_type": "openclaw",
            "event_type": "gateway.metric",
            "ts":         datetime.now(timezone.utc).isoformat(),
            "data":       curr,
        })
    except Exception as _e:
        log.debug("gateway.metric: ingest failed (%s)", _e)
        return False

    _LAST_GATEWAY_METRIC_TS = now_mono
    _LAST_GATEWAY_METRIC = curr
    return True


# ── Daemon-collected snapshots ────────────────────────────────────────────────
# Cloud's tabs (Security, Models, Upgrades, Clusters, …) need data the OSS
# routes/* endpoints derive from local state — host filesystem checks,
# `openclaw --version` output, gateway WebSocket, etc. None of that exists
# on Cloud Run. The daemon collects locally and pushes on the heartbeat;
# cloud stores the latest blob per node and serves it via cloud-side
# `/api/<feature>` handlers that mirror the OSS shape.
#
# Each collector caches its result in `_snapshot_cache` so we don't
# recompute every heartbeat (most of these are ~100ms-1s and don't change
# minute-to-minute). Re-collected at the interval below or when missing.

_snapshot_cache: dict = {}            # name → (value, computed_at_unix_ts)
_SNAPSHOT_TTL_SEC = 300               # 5 min — security posture etc.


def _collect_security_posture() -> dict | None:
    """Run OSS `_scan_security_posture()` locally and return its result.

    Imports OSS dashboard.py via importlib so we don't pull the whole Flask
    app into the daemon process. Cached for 5 min — the underlying checks
    are filesystem reads (~50 ms total) but we don't need fresher data than
    that for a posture overview.
    """
    cached = _snapshot_cache.get("security_posture")
    if cached and (time.time() - cached[1]) < _SNAPSHOT_TTL_SEC:
        return cached[0]
    try:
        # Resolve OSS dashboard.py from the installed clawmetry package
        # (parent dir holds dashboard.py per setup.py's `py_modules`).
        import clawmetry as _cm_pkg
        import importlib.util as _ilu
        oss_dashboard_path = os.path.join(
            os.path.dirname(os.path.dirname(_cm_pkg.__file__)),
            "dashboard.py",
        )
        if not os.path.isfile(oss_dashboard_path):
            return None
        spec = _ilu.spec_from_file_location("_oss_dashboard_for_snapshot", oss_dashboard_path)
        mod = _ilu.module_from_spec(spec)
        # OSS dashboard.py uses sys.modules.setdefault("dashboard", ...) at
        # load — register first so it doesn't KeyError.
        import sys as _sys
        _sys.modules.setdefault("_oss_dashboard_for_snapshot", mod)
        spec.loader.exec_module(mod)
        scan = getattr(mod, "_scan_security_posture", None)
        if not scan:
            return None
        result = scan()
        _snapshot_cache["security_posture"] = (result, time.time())
        return result
    except Exception as e:
        log.warning(f"_collect_security_posture failed: {e}")
        return None


# Tool-name classifiers for `_collect_activity_counters_today` (issue #1652).
# Mirrors the lower-cased substring match used by `routes/brain.py::tool_to_type`
# so the heartbeat counters line up with the same buckets the OSS Brain page
# would show. Centralised here so the daemon doesn't have to import routes.
def _classify_tool_name(name: str) -> str:
    """Return the activity bucket for a tool ``name``. One of:
    ``exec``, ``browser``, ``other``. Lower-cased before matching."""
    tn = (name or "").lower()
    if not tn:
        return "other"
    if tn in ("exec", "process") or "shell" in tn or "bash" in tn:
        return "exec"
    if "browser" in tn:
        return "browser"
    return "other"


# Plaintext message-class events (issue #1652). These are the v3 + legacy
# event types that count as "the agent did one round-trip with the user or
# the model". Match the dedup set in `local_store.query_aggregates`.
_MESSAGE_EVENT_TYPES_TODAY = (
    "message", "prompt.submitted", "model.completed",
)


def _today_start_iso_utc() -> str:
    """Midnight-UTC of the current day as ISO-8601, suitable for the
    ``events.ts`` VARCHAR column's lexical ordering (UTC ISO sorts correctly
    as strings)."""
    now = datetime.now(timezone.utc)
    start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    return start.isoformat()


def _collect_activity_counters_today() -> dict | None:
    """Plaintext activity counters for the heartbeat envelope (issue #1652).

    Cloud has no plaintext source for real exec/tool-call activity counts —
    sessions + nodes.metadata carry version/health bits but no per-day
    counters, and the brain cache push is encrypted (cloud can't read it).
    This helper aggregates COUNTS (not session content) from the local
    DuckDB events table for today UTC, so cloud's Flow Exec modal (#953)
    and adjacent surfaces (#967 messages, #968 browser) can swap from the
    session-liveness proxy to real numbers in their next iteration.

    Returns a dict with five integer fields (all >= 0):

      * ``tool_calls_today`` — every tool invocation (exec + browser + other)
      * ``exec_calls_today`` — subset whose name classifies as shell/bash/exec
      * ``browser_actions_today`` — subset whose name contains ``browser``
      * ``unique_tools_today`` — count of distinct tool names invoked today
      * ``messages_today`` — count of ``message`` / ``prompt.submitted`` /
        ``model.completed`` events today

    Best-effort: returns ``None`` if local_store isn't importable or the
    underlying read raises — heartbeat MUST succeed even if counters fail.
    Why plaintext is OK: these are aggregates, not session content.
    No PII risk — same trust model as the existing `local_store_size_mb`.
    """
    try:
        from clawmetry import local_store
        store = local_store.get_store()
    except Exception:
        return None

    try:
        since = _today_start_iso_utc()

        # Tool calls: re-use the per-invocation reader so we count once
        # per ACTUAL tool call, not once per row (an assistant message
        # carrying 3 toolMetas yields 3 invocations, not 1).
        try:
            invs = store.query_tool_call_invocations(since=since, limit=200_000)
        except Exception:
            invs = []
        tool_calls = 0
        exec_calls = 0
        browser_actions = 0
        unique_names: set[str] = set()
        for row in invs:
            name = row.get("name") if isinstance(row, dict) else None
            if not isinstance(name, str) or not name:
                continue
            tool_calls += 1
            unique_names.add(name.lower())
            bucket = _classify_tool_name(name)
            if bucket == "exec":
                exec_calls += 1
            elif bucket == "browser":
                browser_actions += 1

        # Messages: count rows directly via query_events. We don't dedup the
        # assistant/model.completed twin here — message counts are a coarse
        # "did the agent talk today" signal and the dedupe would obscure
        # legitimately distinct prompt.submitted rows. Cloud uses this as a
        # heartbeat liveness proxy, not a billing aggregate.
        messages_today = 0
        for et in _MESSAGE_EVENT_TYPES_TODAY:
            try:
                rows = store.query_events(
                    event_type=et, since=since, limit=100_000,
                )
            except Exception:
                continue
            messages_today += len(rows)

        return {
            "tool_calls_today":      int(tool_calls),
            "exec_calls_today":      int(exec_calls),
            "browser_actions_today": int(browser_actions),
            "unique_tools_today":    int(len(unique_names)),
            "messages_today":        int(messages_today),
        }
    except Exception as e:
        log.debug("_collect_activity_counters_today failed: %s", e)
        return None


# Adaptive heartbeat: the most recent /ingest/heartbeat response body so the
# main loop (and tests) can derive the next sleep interval without changing
# `send_heartbeat`'s `bool` return type (callers in tests assert `is True`).
# `None` when no successful heartbeat has been received yet OR after a 5xx.
_LAST_HEARTBEAT_RESPONSE: dict | None = None


def _pick_heartbeat_interval(resp_json: dict | None) -> int:
    """Adaptive cadence (#775 PR 2/3): FAST when a viewer is watching the
    cloud dashboard, SLOW otherwise. Pure function so it can be unit-tested
    without booting the daemon loop.

    Back-compat: a cloud that hasn't deployed PR 1 yet won't return the
    `viewer_active` field, so missing → SLOW. Same for `None` (no successful
    heartbeat yet) and any non-dict input.
    """
    if not isinstance(resp_json, dict):
        return HEARTBEAT_INTERVAL_SLOW
    return (
        HEARTBEAT_INTERVAL_FAST
        if resp_json.get("viewer_active", False)
        else HEARTBEAT_INTERVAL_SLOW
    )


def send_heartbeat(config: dict) -> bool:
    """Send heartbeat to cloud. Returns True on success, False on failure.

    Side effect: on success, stashes the parsed response body in
    `_LAST_HEARTBEAT_RESPONSE` so the main loop can read `viewer_active`
    via `_pick_heartbeat_interval()` and adapt the next sleep interval.
    """
    global _LAST_HEARTBEAT_RESPONSE
    payload = {
        "node_id": config["node_id"],
        "ts": datetime.now(timezone.utc).isoformat(),
        "platform": platform.system(),
        "version": _get_version(),
        "e2e": bool(config.get("encryption_key")),
        "ollama": _detect_ollama_for_heartbeat(),
    }
    # Agent-install self-report (cloud bug fix 2026-05-18). Cloud Run pods
    # can't stat the user's home directory, so the daemon tells cloud what
    # agents exist locally and cloud aggregates across the user's fleet.
    # Best-effort — heartbeat MUST succeed even if detection raises.
    try:
        payload["agent_install"] = _detect_agent_install_for_heartbeat()
    except Exception as _ai_e:
        log.debug("agent_install detection failed (continuing): %s", _ai_e)
    # Daemon-collected snapshots (see _collect_security_posture docstring)
    sec = _collect_security_posture()
    if sec is not None:
        payload["security_posture"] = sec
    # Local-store health (epic #964 phase 1 → rollout gate for phase 2).
    # We need ≥80% of active nodes reporting healthy local stores before
    # slimming cloud retention to 24h. Best-effort; never blocks heartbeat.
    try:
        from clawmetry import local_store
        h = local_store.get_store().health()
        payload["local_store"] = {
            "engine":       h.get("engine"),
            "size_bytes":   h.get("size_bytes", 0),
            "events_total": h.get("events_total", 0),
            "ring_depth":   h.get("ring_depth", 0),
        }
        # Convenience field the cloud rollout playbook can group/aggregate on.
        size_mb = (h.get("size_bytes") or 0) / (1024 * 1024)
        payload["local_store_size_mb"] = round(size_mb, 3)
    except Exception:
        pass  # local store optional — never break heartbeat over it
    # Issue #1652: plaintext per-day activity counters so the cloud Flow Exec
    # modal (#953/#966), messages widget (#967) and browser widget (#968)
    # can show REAL numbers instead of inferring from session liveness.
    # Same trust model as `local_store_size_mb` — counts only, no content.
    try:
        counters = _collect_activity_counters_today()
        if counters:
            payload.update(counters)
    except Exception as _ce:
        log.debug("activity counters build failed (continuing): %s", _ce)
    # Phase 2 of relay-v2 (epic #1032): proactively push the top-50 brain
    # events to the cloud cache so the Brain page paints in <100ms on first
    # load instead of waiting for a relay round-trip. The blob is the same
    # E2E ciphertext we use for /ingest/cache, so the cloud never sees
    # plaintext. Best-effort — heartbeat MUST succeed even if this fails.
    try:
        pushes = _build_brain_cache_pushes(config)
        if pushes:
            payload["cache_pushes"] = pushes
    except Exception as _bp_e:
        log.debug("brain cache_push build failed (continuing): %s", _bp_e)
    # Phase 5 of relay-v2 (#1032): channel adapter status. Non-secret
    # status summary (provider, enabled, last_test_at/ok/error) pushed to
    # `channels:{owner_hash}:status` TTL 3600s so the cloud Channels tab
    # paints from Redis. Encrypted blob with config tokens NEVER traverses
    # this push — that ciphertext lives only in local DuckDB.
    try:
        ch_pushes = _build_channel_config_status_cache_pushes(config)
        if ch_pushes:
            payload.setdefault("cache_pushes", []).extend(ch_pushes)
    except Exception as _cp_e:
        log.debug("channel-config cache_push build failed (continuing): %s", _cp_e)
    # Phase 3 of relay-v2 (#1032): also push the user's alert-rule list so the
    # cloud Alerts tab paints from cache. Same envelope (`cache_pushes`) — the
    # cloud's _accept_cache_pushes handler iterates the array regardless of
    # which Phase contributed which entry.
    try:
        alert_pushes = _build_alert_rules_cache_pushes(config)
        if alert_pushes:
            payload.setdefault("cache_pushes", []).extend(alert_pushes)
    except Exception as _ap_e:
        log.debug("alert-rules cache_push build failed (continuing): %s", _ap_e)
    # Phase 4 of epic #1032: push the user's pending approvals queue so the
    # cloud Approvals inbox paints from cache. Same envelope (`cache_pushes`)
    # — cloud's _accept_cache_pushes iterates the array regardless of which
    # phase produced which entry. TTL is short (60s) by acceptance criterion:
    # "approval appears in cloud inbox within 2s", and a stale cache row
    # would block a fresh request from showing up; the next heartbeat
    # overwrites it anyway.
    try:
        ap_pushes = _build_approvals_cache_pushes(config)
        if ap_pushes:
            payload.setdefault("cache_pushes", []).extend(ap_pushes)
    except Exception as _ap_e2:
        log.debug("approvals cache_push build failed (continuing): %s", _ap_e2)
    # Memory tab (epic #1032): proactively push the user's memory-file
    # snapshot so the cloud Node Detail → Memory tab paints from cache.
    # Without this push the cloud handler returns `{blob: None}` and the
    # browser renders "No memory data synced". Best-effort.
    try:
        mem_pushes = _build_memory_cache_pushes(config)
        if mem_pushes:
            payload.setdefault("cache_pushes", []).extend(mem_pushes)
    except Exception as _mp_e:
        log.debug("memory cache_push build failed (continuing): %s", _mp_e)
    # Phase 6 of relay-v2 (#1640): cron-run history per job so the cloud Cron
    # modal paints run timelines from cache instead of showing cache_pending.
    try:
        cr_pushes = _build_cron_runs_cache_pushes(config)
        if cr_pushes:
            payload.setdefault("cache_pushes", []).extend(cr_pushes)
    except Exception as _cr_e:
        log.debug("cron-runs cache_push build failed (continuing): %s", _cr_e)
    # Crons list (cloud#948): push the user's cron job list so the cloud
    # Crons tab paints from cache. Without this push the cloud handler
    # returns {data: []} and the browser shows "no cron data" even when
    # the user has crons scheduled. Always include the entry on every
    # heartbeat (sync_crons already deduped the JSONL parse upstream, so
    # this is cheap); the cloud overwrites on each push.
    try:
        cron_pushes = _build_crons_cache_pushes(config)
        if cron_pushes:
            payload.setdefault("cache_pushes", []).extend(cron_pushes)
    except Exception as _cl_e:
        log.debug("crons cache_push build failed (continuing): %s", _cl_e)
    # Local-first: persist this heartbeat to local DuckDB so the dashboard
    # has a per-node liveness history even when offline. Best-effort.
    try:
        from clawmetry import local_store
        local_store.get_store().ingest_heartbeat(payload)
    except Exception as _le:
        log.debug("local-store heartbeat ingest failed (continuing): %s", _le)
    last_err = None
    for attempt in range(3):
        try:
            resp_json = _post("/ingest/heartbeat", payload, config["api_key"])
            if attempt > 0:
                log.info(f"Heartbeat succeeded after {attempt + 1} attempts")
            # Stash for adaptive-cadence pick (#775 PR 2/3). Normalise to dict
            # so `_pick_heartbeat_interval` always sees a sensible shape even
            # if `_post` ever decides to return None on a 204.
            _LAST_HEARTBEAT_RESPONSE = resp_json if isinstance(resp_json, dict) else {}
            # Phase 1 of relay-v2 (#1053): the cloud may piggyback a small
            # batch of `pending_queries` on the heartbeat response. Each is
            # a shape-allowlisted read against the local DuckDB; we run them,
            # encrypt the result, and POST back to /ingest/cache so the
            # cloud-side dashboard can serve subsequent requests from the
            # warm cache without ever touching the local node.
            pending = (resp_json or {}).get("pending_queries") or []
            if pending:
                _dispatch_pending_queries(config, pending)
            return True
        except Exception as e:
            last_err = e
            if attempt < 2:
                time.sleep(2**attempt)  # 1s, 2s backoff
    # Heartbeat failed: clear the stashed response so the next interval pick
    # falls back to SLOW (don't burn tighter cadence on a stale viewer flag).
    _LAST_HEARTBEAT_RESPONSE = None
    log.warning(f"Heartbeat failed after 3 attempts: {last_err}")
    return False


# ── Heartbeat-piggyback query dispatch (relay-v2 phase 1, #1053) ─────────────
# Allowlist mirrors routes.local_query._SHAPES. Duplicated here so the
# daemon stays safe when `routes/` isn't on sys.path (some installs run the
# sync daemon without the dashboard module loaded).
_PENDING_SHAPES = {"events", "sessions", "aggregates", "health", "transcript"}


def _canonical_args_hash(args: dict) -> str:
    """Stable sha256 of the args dict — sorted keys, no whitespace. Used as
    the cache_key fingerprint so the cloud can detect arg drift even if the
    same `cache_key` label is reused."""
    import hashlib
    canonical = json.dumps(args or {}, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _local_dispatch_fallback(shape: str, args: dict) -> dict:
    """Fallback dispatcher used when `routes.local_query` isn't importable
    (daemon-only installs). Mirrors the minimal shape→method bridge.

    Cloud-side pending_queries may carry kwargs the local store doesn't
    recognise (e.g. ``node_id`` — the cloud uses it to route between
    nodes, but the local DuckDB IS a single-node store). Filter to a
    per-shape allowlist so those extras don't surface as TypeErrors.
    """
    from clawmetry import local_store
    store = local_store.get_store(read_only=True)
    if shape == "health":
        return store.health()
    method_map = {
        "events":     "query_events",
        "sessions":   "query_sessions",
        "aggregates": "query_aggregates",
        "transcript": "query_events",
    }
    method = method_map.get(shape)
    if not method:
        raise ValueError(f"unknown shape: {shape}")
    rows = getattr(store, method)(**_filter_store_kwargs(shape, args or {}))
    return {"rows": rows, "count": len(rows), "_shape": shape, "_via": "fallback"}


# Per-shape allowlist of kwargs accepted by the underlying ``LocalStore``
# methods. Kept in sync with ``LocalStore.query_*`` signatures in
# ``clawmetry/local_store.py``. Mirrors ``routes.local_query._coerce_args``
# but defined here so the daemon-only fallback path doesn't need the
# routes package on sys.path.
_SHAPE_ALLOWED_KWARGS = {
    "events":     {"session_id", "agent_id", "event_type", "since", "until", "limit"},
    "sessions":   {"agent_id", "since", "until", "limit"},
    "aggregates": {"agent_id", "since", "until"},
    "transcript": {"session_id", "limit"},
}


def _filter_store_kwargs(shape: str, args: dict) -> dict:
    allowed = _SHAPE_ALLOWED_KWARGS.get(shape)
    if allowed is None:
        return dict(args)
    return {k: v for k, v in args.items() if k in allowed}


def _channel_enrichment_from_row(r: dict) -> dict:
    """Pull (provider, chat_id, sender_id, sender, direction) out of a
    channel.* events row so the cloud Brain renderer can display
    "Telegram: Vivek Chand: hello" instead of generic agent activity.

    The ingest path in ``sync_channel_messages`` (PR #1191) writes channel
    transcripts with:
      * ``event_type`` = ``"channel.in"`` or ``"channel.out"``
      * ``id`` = ``f"{provider}:{channel_id}:{raw_id}"`` — the only place
        ``provider`` lives on the events row, since the events table has
        no provider column.
      * ``data`` = the original adapter line (``from``/``sender``/``user``
        block, ``text``/``body``, etc.).

    Returns ``{}`` for non-channel rows so callers can spread it
    unconditionally. Never raises.
    """
    et = r.get("event_type") or ""
    if not isinstance(et, str) or not et.startswith("channel."):
        return {}
    direction = et.split(".", 1)[1] if "." in et else ""
    eid = r.get("id") or ""
    provider = ""
    chat_id = ""
    if isinstance(eid, str) and eid.count(":") >= 2:
        # ``{provider}:{channel_id}:{raw_id}`` — raw_id may itself contain
        # colons (rare, but defensible: split only the first two segments).
        parts = eid.split(":", 2)
        provider, chat_id = parts[0], parts[1]
    data = r.get("data") if isinstance(r.get("data"), dict) else {}
    sender_block = (
        data.get("from") or data.get("sender") or data.get("user") or {}
    )
    if not isinstance(sender_block, dict):
        sender_block = {}
    sender_id = (
        data.get("sender_id")
        or sender_block.get("id")
        or data.get("user_id")
        or chat_id
    )
    sender = (
        data.get("sender_name")
        or sender_block.get("username")
        or sender_block.get("first_name")
        or sender_block.get("name")
        or ""
    )
    out = {
        "provider":  provider,
        "chat_id":   str(chat_id) if chat_id != "" else "",
        "sender_id": str(sender_id) if sender_id is not None else "",
        "sender":    str(sender),
        "direction": direction,
    }
    return out


def _rows_to_brain_events(rows: list) -> list:
    """Return raw OpenClaw event payloads ready for the cloud browser's
    ``transformEvents`` to unwrap.

    The cloud Brain ``_cm_decryptBrain`` decrypts the blob, reads
    ``dec.events``, then runs ``transformEvents(rawEvs, ...)`` over each
    item — which expects the ORIGINAL JSONL shape:
    ``{type, message:{role, content}, timestamp}``. It walks
    ``message.content[].type === 'text'/'tool_use'/'thinking'`` to extract
    the human-readable detail.

    Earlier we pre-flattened to ``{type:'ASSISTANT', detail:'', src, ...}``
    (the OSS-local shape). That made ``transformEvents`` fall through to its
    empty-detail fallback and DROP every event — cloud Brain showed "No
    brain activity events found" even with hundreds of rows in DuckDB.
    Bug confirmed live 2026-05-13 (Diya/Telegram messages).

    For each row we forward ``row['data']`` as-is. We backfill
    ``timestamp`` from the column-level ``ts`` only when the inner JSONL
    didn't already carry one (transformEvents needs ``obj.timestamp ||
    obj.time``).

    Channel events (``event_type`` starts with ``channel.``) get extra
    top-level keys — ``provider`` / ``chat_id`` / ``sender_id`` /
    ``sender`` / ``direction`` — so the cloud Brain renderer can show
    "Telegram: Vivek Chand: hello, how are you doing?" instead of generic
    agent activity. ``transformEvents`` ignores keys it doesn't know about,
    so this is a forward-compatible enrichment.

    The OSS-local Brain tab uses ``routes/brain.py:_try_local_store_brain``
    which builds the display shape directly — that path is unchanged.
    """
    out = []
    for r in rows or []:
        if not isinstance(r, dict):
            continue
        data = r.get("data")
        enrich = _channel_enrichment_from_row(r)
        if isinstance(data, dict):
            if not data.get("timestamp") and not data.get("time") and r.get("ts"):
                data = {**data, "timestamp": r.get("ts")}
            if enrich:
                # Enrichment wins — the JSONL payload often carries the
                # raw ``sender``/``from`` BLOCK under the same key name
                # (Signal: ``data.sender = {"id":..,"name":..}``); we want
                # the renderer to read the FLAT string we computed, not
                # the nested dict. Same for ``provider`` / ``chat_id``
                # which never appear in adapter payloads.
                data = {**data, **enrich}
                # Stamp the channel event type back on so the cloud
                # renderer's fallback branch (line ~10038 of cloud
                # dashboard.py) can show "CHANNEL.IN" / "CHANNEL.OUT"
                # rather than guessing from a missing role.
                data.setdefault("type", r.get("event_type"))
            out.append(data)
        elif isinstance(data, str):
            out.append({
                **enrich,
                "type":      r.get("event_type") or "raw",
                "timestamp": r.get("ts", ""),
                "detail":    data[:2000],
            })
    return out


# ── Phase 2: proactive brain cache_push (epic #1032) ─────────────────────────
# The Brain page is the first thing most users hit on the cloud dashboard. In
# Phase 1 the cloud only had data for it after a browser /api/cloud/subscribe
# round-trip (one full heartbeat cycle, up to 60s). Phase 2 pushes the top-50
# brain events on EVERY heartbeat so the page paints from cache in <100ms.
#
# Key shape: `brain:{owner_hash}:{node_id}:recent`. The cloud derives
# owner_hash from the cm_ token (sha256 hex) — we compute the same value here
# so both sides agree on the key without needing the daemon to know the
# cloud's internal user id.
#
# TTL: 6h. Each heartbeat overwrites the entry, so TTL only matters when the
# daemon goes offline — after 6h the cloud treats the cache as cold and
# re-subscribes. Long enough to cover a typical work-day pause; short enough
# that stale data doesn't linger after a node is decommissioned.
BRAIN_CACHE_TTL_SEC = 21600
BRAIN_CACHE_LIMIT = 50


def _owner_hash_for_token(api_key: str) -> str:
    """Mirror of cloud's `_owner_hash_for(token)` — sha256 hex of the cm_
    token. The daemon computes it locally so the cache key it sends matches
    exactly what the cloud derives from the same token on read."""
    import hashlib
    return hashlib.sha256((api_key or "").encode("utf-8")).hexdigest()


def _build_brain_cache_pushes(config: dict) -> list:
    """Return the heartbeat `cache_pushes` array — currently a single entry
    holding the encrypted top-50 brain events for this node.

    Returns an empty list when:
      - The local store has no events yet (fresh install) — nothing to push.
      - Encryption key is unset — we never push plaintext.
      - The local store import fails — degrade silently.

    The blob shape mirrors `routes.brain._try_local_store_brain` so the cloud
    read path can hand the decrypted dict straight to the existing dashboard
    JS without translation.
    """
    enc_key = config.get("encryption_key")
    if not enc_key:
        return []
    api_key = config.get("api_key", "")
    node_id = config.get("node_id", "")
    if not (api_key and node_id):
        return []
    try:
        from clawmetry import local_store
    except Exception:
        return []
    try:
        store = local_store.get_store(read_only=True)
        rows = store.query_events(limit=BRAIN_CACHE_LIMIT)
    except Exception:
        return []
    if not rows:
        return []
    # Same translation as routes/brain.py:_try_local_store_brain so the
    # browser sees an identical event shape regardless of which path served
    # the data (cache hit vs. relay subscribe vs. JSONL fallback).
    events = _rows_to_brain_events(rows)
    payload = {
        "events":  events,
        "count":   len(events),
        "_source": "local_store",
        "_shape":  "brain_history",
    }
    try:
        blob = encrypt_payload(payload, enc_key)
    except Exception:
        return []
    owner_hash = _owner_hash_for_token(api_key)
    return [{
        "key":    f"brain:{owner_hash}:{node_id}:recent",
        "ttl_s":  BRAIN_CACHE_TTL_SEC,
        "blob":   blob,
    }]


# ── Memory files cache push (epic #1032 — Memory tab fix) ───────────────────
# The cloud Memory tab in Node Detail reads from a cache key populated here.
# Same heartbeat-piggyback envelope as the Brain cache push: encrypted blob
# under ``memory:{owner_hash}:{node_id}:files`` with the user's E2E key.
# Cloud read path: ``routes/cloud.py:cloud_memory_files``.

MEMORY_CACHE_TTL_SEC = 21600       # 6h — matches Brain TTL; files change slowly
MEMORY_CACHE_LIMIT = 200            # plenty for SOUL.md/USER.md/AGENTS.md/etc.
MEMORY_CONTENT_TRUNCATE = 500_000   # mirrors routes/infra.py truncation


def _build_memory_cache_pushes(config: dict) -> list:
    """Heartbeat cache_push entry holding the encrypted memory-file snapshot.

    Returns ``[]`` when:
      - No encryption key (we never push plaintext).
      - Local store unimportable / empty memory_blobs table.

    Decrypted payload shape mirrors what the cloud dashboard JS reads in
    ``_renderIDE`` / ``_selectFile`` (see clawmetry-cloud/dashboard.py
    ``_cloudLoadMemory``):

        {
          "memory_state":   {"files": [{"name": <path>, "size": <bytes>}, ...]},
          "memory_content": [{"path": <path>, "content": <utf8 str>}, ...]
        }

    The browser holds the key; cloud only ever stores ciphertext.
    """
    enc_key = config.get("encryption_key")
    if not enc_key:
        return []
    api_key = config.get("api_key", "")
    node_id = config.get("node_id", "")
    if not (api_key and node_id):
        return []
    try:
        from clawmetry import local_store
    except Exception:
        return []
    try:
        store = local_store.get_store(read_only=True)
        rows = store.query_memory_blobs(limit=MEMORY_CACHE_LIMIT)
    except Exception:
        return []
    if not rows:
        return []
    files: list[dict] = []
    contents: list[dict] = []
    seen: set = set()
    for r in rows:
        path = r.get("path") or ""
        if not path or path in seen:
            continue
        seen.add(path)
        blob_raw = r.get("blob")
        if isinstance(blob_raw, (bytes, bytearray)):
            try:
                content = bytes(blob_raw).decode("utf-8", errors="replace")
            except Exception:
                content = ""
        elif isinstance(blob_raw, str):
            content = blob_raw
        else:
            content = ""
        size = r.get("size_bytes")
        if size is None:
            size = len(content.encode("utf-8", errors="replace"))
        files.append({"name": path, "path": path, "size": int(size or 0)})
        # Truncate per-file content to bound the encrypted blob size — the
        # cloud Memory IDE shows a viewer pane (no diffing), so >500KB per
        # file is wasted heartbeat bandwidth.
        contents.append({"path": path, "content": content[:MEMORY_CONTENT_TRUNCATE]})
    if not files:
        return []
    payload = {
        "memory_state":   {"files": files},
        "memory_content": contents,
        "_source":        "local_store",
        "_shape":         "memory_files",
    }
    try:
        blob = encrypt_payload(payload, enc_key)
    except Exception:
        return []
    owner_hash = _owner_hash_for_token(api_key)
    return [{
        "key":    f"memory:{owner_hash}:{node_id}:files",
        "ttl_s":  MEMORY_CACHE_TTL_SEC,
        "blob":   blob,
    }]


# ── Crons list cache push (cloud#948 — Crons tab fix) ───────────────────────
# Mirrors the cron_runs cache contract documented in clawmetry-cloud
# routes/cloud.py:cloud_cron_runs, but for the JOB LIST itself. Epic #1032
# removed the cloud's events-table read for the Crons tab; the comment in
# /api/cloud/crons promised "data now flows via heartbeat-piggyback /
# DuckDB relay" but that flow was never wired. This is the OSS push half.
#
# Cache key:  crons:{owner_hash}:{node_id}
# Payload:    {"jobs": [<job dict shaped like /api/crons returns>, ...]}
# TTL:        6h  (same as Brain / Memory — long enough for a workday pause,
#                  short enough that decommissioned nodes don't linger).

CRONS_CACHE_TTL_SEC = 21600
CRONS_CACHE_LIMIT = 500


def _build_crons_cache_pushes(config: dict) -> list:
    """Heartbeat cache_push entry with the encrypted cron job list.

    Returns ``[]`` when:
      - No encryption key (we never push plaintext).
      - Local store unimportable / no crons rows yet (fresh install with
        zero crons — cloud read returns ``cache_pending`` and the JS
        renders the "no crons scheduled yet" empty state).

    Payload shape mirrors what ``routes/crons.py:_try_local_store_crons``
    returns (modulo cost attribution, which lives in the gateway-fetch
    path only), so the cloud-side decrypt can hand the dict straight to
    the dashboard JS that already renders ``snap.cronJobs``:

        {"jobs": [{id, name, schedule, enabled, createdAtMs,
                   state: {lastRunAtMs, lastStatus, nextRunAtMs, ...}},
                  ...],
         "_source": "local_store",
         "_shape":  "crons_list"}
    """
    enc_key = config.get("encryption_key")
    if not enc_key:
        return []
    api_key = config.get("api_key", "")
    node_id = config.get("node_id", "")
    if not (api_key and node_id):
        return []
    try:
        from clawmetry import local_store
    except Exception:
        return []
    try:
        store = local_store.get_store(read_only=True)
        rows = store.query_crons(limit=CRONS_CACHE_LIMIT)
    except Exception:
        return []
    # Note: rows == [] is still pushed so the cloud can distinguish "user
    # has zero crons" (cache hit with empty jobs) from "node never synced
    # yet" (cache miss / pending). Same UX contract as cron_runs.
    jobs: list[dict] = []
    for r in rows or []:
        try:
            # Inline the same shaping as routes/crons.py:_row_to_cron_job
            # so we don't have to import dashboard helpers from the daemon
            # (circular). Keep the field set narrow — just what the JS
            # renderer reads (id, name, schedule, enabled, state).
            extras = r.get("data") if isinstance(r.get("data"), dict) else {}
            state_extras = {
                k: extras[k]
                for k in ("lastDurationMs", "consecutiveFailures",
                          "lastError", "runHistory", "lastCostUsd")
                if k in extras
            }
            schedule = r.get("schedule")
            if isinstance(schedule, str):
                try:
                    decoded = json.loads(schedule)
                    if isinstance(decoded, dict):
                        schedule = decoded
                except Exception:
                    pass
            if schedule is None and isinstance(extras.get("schedule"),
                                               (dict, str)):
                schedule = extras["schedule"]

            def _to_ms(v):
                if v is None or v == "":
                    return 0
                try:
                    return int(v)
                except (TypeError, ValueError):
                    try:
                        from datetime import datetime as _dt
                        return int(_dt.fromisoformat(
                            str(v).replace("Z", "+00:00")
                        ).timestamp() * 1000)
                    except Exception:
                        return 0

            job = {
                "id":          r.get("cron_id", ""),
                "name":        r.get("name") or r.get("cron_id", ""),
                "schedule":    schedule or {},
                "enabled":     bool(r.get("enabled", True)),
                "createdAtMs": int(extras.get("createdAtMs") or 0),
                "state": {
                    "lastRunAtMs": _to_ms(r.get("last_run_at")),
                    "lastStatus":  r.get("last_status") or "pending",
                    "nextRunAtMs": _to_ms(r.get("next_run_at")),
                    **state_extras,
                },
            }
            # Carry through extras the renderer may use (task, channel,
            # model, prompt, ...). Skip keys we already projected.
            for k, v in extras.items():
                if k not in {"createdAtMs", "schedule", "lastDurationMs",
                             "consecutiveFailures", "lastError",
                             "runHistory", "lastCostUsd"}:
                    job.setdefault(k, v)
            jobs.append(job)
        except Exception:
            continue
    payload = {
        "jobs":    jobs,
        "count":   len(jobs),
        "_source": "local_store",
        "_shape":  "crons_list",
    }
    try:
        blob = encrypt_payload(payload, enc_key)
    except Exception:
        return []
    owner_hash = _owner_hash_for_token(api_key)
    return [{
        "key":    f"crons:{owner_hash}:{node_id}",
        "ttl_s":  CRONS_CACHE_TTL_SEC,
        "blob":   blob,
    }]


# ── Phase 5: channel adapter config (epic #1032) ────────────────────────────
# Channel adapter configs (Telegram bot tokens, Slack OAuth, Signal phone
# numbers, etc.) live in local DuckDB only. Cloud UI authors them via
# pending_queries actions; the daemon persists the E2E-encrypted blob in
# `channel_config`. Per-provider non-secret status (enabled, last_test_at,
# last_test_ok) gets pushed back to `channels:{owner_hash}:status` on every
# heartbeat so the cloud Channels tab paints from Redis.
#
# Invariant: cloud NEVER sees plaintext tokens. The encrypted blob only ever
# rests in local DuckDB; the cache_push carries STATUS ONLY (per provider).

CHANNEL_STATUS_CACHE_TTL_SEC = 3600

# Action-style pending entries the daemon handles in-process (no /ingest/cache
# POST). Phase 5 added the channel-config actions; Phase 3 of #1032 (alert
# rules) and Phase 4 of #1032 (approvals) extend the set so cloud-authored
# rules and Approve/Deny clicks land in local DuckDB on the next heartbeat
# cycle. Mirrors the cloud-side allowlists used by
# clawmetry-cloud/routes/alerts.py:_enqueue_alert_rule_change and the
# approvals enqueue path.
_PENDING_ACTIONS = frozenset({
    "channel_config_upsert",
    "channel_test",
    "alert_rule_upsert",
    "alert_rule_delete",
    "approval_decision",
    "selfevolve_fix",
    "selfevolve_analyze",
})


def _build_channel_config_status_cache_pushes(config: dict) -> list:
    """Build the heartbeat cache_push entries for channel adapter status.

    Returns ``[]`` when:
      - No encryption key configured (status fields are non-secret BUT we
        encrypt by convention so the cloud cache contract is uniform —
        every cache_push blob is ciphertext).
      - The local store has no channel_config rows yet.
      - The local_store import fails.

    Single entry shape:
        {
          key:   "channels:{owner_hash}:status",
          ttl_s: 3600,
          blob:  encrypt_payload({channels: [...], _source: "local_store",
                                   _shape: "channel_config_status"}, key),
        }

    The ``channels`` payload is a list of per-provider status dicts —
    NEVER the encrypted config blob. Plaintext tokens NEVER traverse the
    wire, even encrypted, on this key.
    """
    enc_key = config.get("encryption_key")
    if not enc_key:
        return []
    api_key = config.get("api_key", "")
    node_id = config.get("node_id", "")
    if not (api_key and node_id):
        return []
    try:
        from clawmetry import local_store
    except Exception:
        return []
    try:
        store = local_store.get_store(read_only=True)
        rows = store.query_channel_config_status()
    except Exception:
        return []
    if not rows:
        return []
    channels = []
    for r in rows:
        channels.append({
            "provider":        r.get("provider"),
            "enabled":         bool(r.get("enabled")) if r.get("enabled") is not None else False,
            "last_test_at":    r.get("last_test_at"),
            "last_test_ok":    r.get("last_test_ok"),
            "last_test_error": r.get("last_test_error"),
            "updated_at":      r.get("updated_at"),
        })
    payload = {
        "channels": channels,
        "count":    len(channels),
        "_source":  "local_store",
        "_shape":   "channel_config_status",
    }
    try:
        blob = encrypt_payload(payload, enc_key)
    except Exception:
        return []
    owner_hash = _owner_hash_for_token(api_key)
    return [{
        "key":   f"channels:{owner_hash}:status",
        "ttl_s": CHANNEL_STATUS_CACHE_TTL_SEC,
        "blob":  blob,
    }]


# ── Phase 3: proactive alert-rules cache_push (epic #1032) ───────────────────
# Alert rules live in local DuckDB after Phase 3 — the cloud UI authors them,
# the relay's pending_queries channel pipes them into the local store, and the
# evaluator (in-process daemon) reads from DuckDB. To keep the cloud Alerts
# tab paint-fast, we also push the current rule list to the cloud cache on
# every heartbeat under `alerts:{owner_hash}:rules`.
#
# Why a flat (no node) key: alert rules are owner-scoped, not node-scoped — a
# user with three nodes sees one rules list across all of them. Cloud-side
# read path uses the same key shape (see clawmetry-cloud routes/alerts.py).
#
# TTL: 3600s. Each heartbeat overwrites the entry, so TTL only matters when
# the daemon goes offline.
ALERT_RULES_CACHE_TTL_SEC = 3600
ALERT_RULES_CACHE_LIMIT = 500


def _build_alert_rules_cache_pushes(config: dict) -> list:
    """Return the heartbeat `cache_pushes` array for alert rules — currently
    a single entry holding the full enabled+disabled rule list owned by this
    cm_ token.

    Returns an empty list when:
      - The local store has no alert rules yet (no cloud has authored any).
      - Encryption key is unset — we never push plaintext.
      - The local store import fails — degrade silently.

    The blob shape mirrors `/api/alerts/rules` so the cloud read path can
    hand the decrypted dict straight to the existing dashboard JS.
    """
    enc_key = config.get("encryption_key")
    if not enc_key:
        return []
    api_key = config.get("api_key", "")
    if not api_key:
        return []
    try:
        from clawmetry import local_store
    except Exception:
        return []
    owner_hash = _owner_hash_for_token(api_key)
    try:
        store = local_store.get_store(read_only=True)
        # Filter by owner_hash so a multi-tenant local store (rare today, but
        # cheap to be correct about) only pushes the calling token's rules.
        rows = store.query_alert_rules(
            owner_hash=owner_hash, limit=ALERT_RULES_CACHE_LIMIT
        )
    except Exception:
        return []
    if not rows:
        return []
    # Same shape `/api/alerts/rules` returns when the local-store fast path
    # is enabled — cloud Alerts tab + integration tests can compare against
    # this without translation.
    payload = {
        "rules":   rows,
        "count":   len(rows),
        "_source": "local_store",
        "_shape":  "alert_rules",
    }
    try:
        blob = encrypt_payload(payload, enc_key)
    except Exception:
        return []
    return [{
        "key":    f"alerts:{owner_hash}:rules",
        "ttl_s":  ALERT_RULES_CACHE_TTL_SEC,
        "blob":   blob,
    }]


def _dispatch_pending_action(config: dict, action: dict) -> None:
    """Handle a single action-style pending entry. Routes by ``type``.

    Supported types (union across phases of epic #1032):

      * ``channel_config_upsert`` (Phase 5) — cloud-submitted channel
        adapter config → local DuckDB ``channel_config`` table.
      * ``channel_test`` (Phase 5) — run upstream-adapter test + stamp
        the result back into ``channel_config``.
      * ``alert_rule_upsert`` (Phase 3) — cloud-authored alert rule →
        ``alert_rules`` table via ``ingest_alert_rule``.
      * ``alert_rule_delete`` (Phase 3) — delete one alert rule by id.
      * ``approval_decision`` (Phase 4) — flip a row in ``approvals``
        from ``pending`` to approved/denied based on a cloud-relayed
        click. Idempotent — the approvals watcher polls for the new
        status and unblocks the agent.

    Unknown / malformed types are silently dropped (defensive — cloud
    should already have filtered). Per-action errors are logged but never
    raise — one bad action must not block the heartbeat batch."""
    atype = action.get("type")
    if atype not in _PENDING_ACTIONS:
        return
    if atype == "channel_config_upsert":
        _action_channel_config_upsert(config, action)
        return
    if atype == "channel_test":
        _action_channel_test(config, action)
        return
    if atype in ("alert_rule_upsert", "alert_rule_delete"):
        # Stamp THIS node's owner_hash: the cloud relay body carries no
        # owner_hash, so without this the rule lands with owner_hash=NULL and
        # _build_alert_rules_cache_pushes' owner_hash filter silently drops it
        # (the cloud Alerts tab then never shows the rule the user just saved).
        _apply_pending_write(
            atype, action,
            owner_hash=_owner_hash_for_token(config.get("api_key", "")),
        )
        return
    if atype == "approval_decision":
        _apply_approval_decision(action)
        return
    if atype == "selfevolve_fix":
        _action_selfevolve_fix(config, action)
        return
    if atype == "selfevolve_analyze":
        _action_selfevolve_analyze(config, action)
        return


def _selfevolve_fix_summary(stdout: str) -> str:
    """Pull a human summary from the `openclaw agent --json` envelope."""
    import re as _re

    try:
        out = json.loads(stdout)
    except Exception:
        return ((stdout or "").strip()[:600]) or "Done."
    result = out.get("result") or {}
    txt = ""
    for p in result.get("payloads") or []:
        if isinstance(p, dict) and p.get("text"):
            txt = p["text"]
    txt = txt or result.get("text") or out.get("text") or ""
    m = _re.search(r"DONE:.*", txt or "")
    return (m.group(0).strip()[:600] if m else (txt or "Done.").strip()[:600]) or "Done."


def _action_selfevolve_fix(config: dict, action: dict) -> None:
    """Cloud-relayed Self-Evolve "Fix with AI": run a finding's suggestion via
    ``openclaw agent`` (OpenClaw's own creds — the gateway token is read-only)
    and post the E2E-encrypted result to ``/ingest/cache`` under the action's
    ``cache_key`` so the cloud dashboard can poll + decrypt it. Runs in a
    background thread so a ~15s agent turn never blocks the heartbeat loop.

    Wire shape (queued cloud-side by /api/cloud/selfevolve-fix):
        {type:"selfevolve_fix", id, cache_key, suggestion, title, category, evidence}
    """
    cache_key = action.get("cache_key")
    suggestion = (action.get("suggestion") or "").strip()
    enc_key = config.get("encryption_key")
    api_key = config.get("api_key", "")
    node_id = config.get("node_id", "")
    if not (cache_key and suggestion and enc_key and api_key):
        return
    title = (action.get("title") or "").strip()
    category = (action.get("category") or "").strip()
    evidence = (action.get("evidence") or "").strip()
    aid = action.get("id")

    def _run():
        status, summary = "error", ""
        try:
            binp = _resolve_openclaw_bin()
            if not binp:
                summary = "openclaw CLI not found on this machine"
            else:
                message = (
                    "You are ClawMetry Self-Evolve in FIX mode. Apply the "
                    "recommended change to your OpenClaw setup now, using your "
                    "tools (edit config, adjust model routing, set values).\n\n"
                    "Finding (" + (category or "general") + "): " + title + "\n"
                    "Evidence: " + (evidence or "(none)") + "\n"
                    "Recommended action: " + suggestion + "\n\n"
                    "Make the concrete change. If a step needs a human decision "
                    "you cannot safely make on your own, do what you safely can "
                    "and state what remains. End with a one-line summary that "
                    "starts with 'DONE:' describing exactly what you changed."
                )
                env = dict(os.environ)
                node_dirs = [
                    os.path.dirname(binp),
                    "/opt/homebrew/bin",
                    "/usr/local/bin",
                    os.path.expanduser("~/.local/bin"),
                ]
                env["PATH"] = os.pathsep.join(
                    node_dirs + [env.get("PATH", "/usr/bin:/bin")]
                )
                proc = subprocess.run(
                    [
                        binp, "agent", "--session-id", "clawmetry-fix",
                        "--message", message, "--json", "--timeout", "300",
                    ],
                    capture_output=True, text=True, timeout=330, env=env,
                )
                if proc.returncode != 0:
                    summary = (
                        proc.stderr or ("agent exited %d" % proc.returncode)
                    )[:400]
                else:
                    status = "done"
                    summary = _selfevolve_fix_summary(proc.stdout)
        except Exception as e:  # never raise from the worker thread
            summary = str(e)[:400]
        try:
            blob = encrypt_payload(
                {"status": status, "summary": summary, "_shape": "selfevolve_fix"},
                enc_key,
            )
            _post(
                "/ingest/cache",
                {
                    "node_id": node_id,
                    "id": aid,
                    "cache_key": cache_key,
                    "blob": blob,
                    "shape": "selfevolve_fix",
                    "ttl": 3600,
                },
                api_key,
            )
        except Exception as e:
            log.warning("selfevolve_fix cache post failed: %s", e)

    threading.Thread(target=_run, daemon=True).start()


def _action_selfevolve_analyze(config: dict, action: dict) -> None:
    """Cloud-relayed on-demand Self-Evolve re-analyze (the Re-analyze button).

    Self-Evolve no longer runs on a timer (see _build_selfevolve) — this is the
    only thing that triggers a fresh review on cloud. Context is built on THIS
    (heartbeat) thread because DuckDB isn't thread-safe; the agent runs in a
    background thread (so a ~15s turn never blocks heartbeats), updates _SE_STATE
    so the next snapshot carries the fresh findings, and posts the E2E-encrypted
    findings to the action's cache_key for immediate cloud feedback.
    """
    cache_key = action.get("cache_key")
    enc_key = config.get("encryption_key")
    api_key = config.get("api_key", "")
    node_id = config.get("node_id", "")
    if not (cache_key and enc_key and api_key):
        return
    try:
        ctx = _selfevolve_build_context()
    except Exception:
        ctx = {}
    aid = action.get("id")

    def _run():
        payload = None
        try:
            payload = _selfevolve_compute_via_openclaw(ctx)
        except Exception as e:
            log.warning("selfevolve_analyze compute failed: %s", e)
        if payload:
            with _SE_LOCK:
                _SE_STATE["payload"] = payload
                _SE_STATE["computed_at"] = time.time()
        out = payload or {"findings": [], "insufficient": True,
                          "reason": "analysis failed — check the agent / gateway"}
        try:
            blob = encrypt_payload(out, enc_key)
            _post(
                "/ingest/cache",
                {
                    "node_id": node_id,
                    "id": aid,
                    "cache_key": cache_key,
                    "blob": blob,
                    "shape": "selfevolve_analyze",
                    "ttl": 3600,
                },
                api_key,
            )
        except Exception as e:
            log.warning("selfevolve_analyze cache post failed: %s", e)

    threading.Thread(target=_run, daemon=True).start()


def _action_channel_config_upsert(config: dict, action: dict) -> None:
    """Persist a cloud-submitted channel adapter config to local DuckDB.

    Wire shape (mirrors the cloud-side relay POST):
        {type: "channel_config_upsert", provider, encrypted_blob, enabled}

    ``encrypted_blob`` is the user-key-encrypted config (bot token, OAuth
    secret, etc.) — base64url-encoded over the wire, decoded to bytes
    before storage. The cloud relay strips any plaintext fields before
    queueing; the daemon does NOT decrypt either, just stores. The local
    adapter binary picks the ciphertext up out-of-band when it actually
    needs to dial the upstream provider."""
    provider = (action.get("provider") or "").strip().lower()
    if not provider:
        log.warning("channel_config_upsert: missing provider")
        return
    blob_raw = action.get("encrypted_blob")
    enabled = action.get("enabled")
    blob_bytes = None
    if blob_raw is not None:
        if isinstance(blob_raw, (bytes, bytearray)):
            blob_bytes = bytes(blob_raw)
        elif isinstance(blob_raw, str):
            # Cloud sends base64url (matches encrypt_payload output). Accept
            # std base64 too; raw plaintext-only string falls back to utf-8.
            import base64 as _b64
            try:
                blob_bytes = _b64.urlsafe_b64decode(blob_raw + "==")
            except Exception:
                try:
                    blob_bytes = _b64.b64decode(blob_raw + "==")
                except Exception:
                    blob_bytes = blob_raw.encode("utf-8")
        else:
            log.warning("channel_config_upsert: bad blob type %s", type(blob_raw))
            return
    try:
        from clawmetry import local_store
    except Exception as e:
        log.warning("channel_config_upsert: local_store import failed: %s", e)
        return
    try:
        local_store.get_store().ingest_channel_config(
            provider=provider,
            encrypted_blob=blob_bytes,
            enabled=bool(enabled) if enabled is not None else None,
            status_meta=None,
        )
        log.info("channel_config_upsert provider=%s enabled=%s blob_bytes=%s",
                 provider, enabled, len(blob_bytes) if blob_bytes else 0)
    except Exception as e:
        log.warning("channel_config_upsert ingest failed (provider=%s): %s",
                    provider, e)


def _action_channel_test(config: dict, action: dict) -> None:
    """Run a local test of the channel adapter and stamp the result.

    Wire shape: ``{type: "channel_test", provider}``.

    The actual upstream ping (Telegram getMe, Slack auth.test, ...) is
    delegated to ``_run_channel_test_local``. We persist the result via
    ``ingest_channel_config`` with status_meta only — the blob remains
    untouched. Status flows back to cloud on the next heartbeat
    cache_push."""
    provider = (action.get("provider") or "").strip().lower()
    if not provider:
        log.warning("channel_test: missing provider")
        return
    try:
        from clawmetry import local_store
    except Exception as e:
        log.warning("channel_test: local_store import failed: %s", e)
        return
    ok, err = _run_channel_test_local(config, provider)
    try:
        local_store.get_store().ingest_channel_config(
            provider=provider,
            encrypted_blob=None,
            enabled=None,
            status_meta={
                "last_test_at": time.strftime(
                    "%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "last_test_ok": bool(ok),
                "last_test_error": (err or "")[:240] if not ok else "",
            },
        )
        log.info("channel_test provider=%s ok=%s", provider, ok)
    except Exception as e:
        log.warning("channel_test status persist failed (provider=%s): %s",
                    provider, e)


def _run_channel_test_local(config: dict, provider: str):
    """Run the upstream ping for ``provider``. Returns (ok, error_msg|None).

    For Phase 5 this is a minimal stub: it confirms an encrypted blob
    exists in the local store (proof the user has actually configured
    the provider) and returns success. Actual provider-specific upstream
    pings (Telegram getMe, Slack auth.test, …) are owned by the OpenClaw
    adapter binary — bridging them here would duplicate decryption surface
    unnecessarily and weaken the "cloud never sees plaintext, daemon
    never decrypts" invariant. The adapter binary writes its own real
    test results back via the gateway in a follow-up phase."""
    try:
        from clawmetry import local_store
    except Exception as e:
        return False, f"local_store unavailable: {e}"
    try:
        # Daemon owns the writer; using the same RW handle for the read
        # avoids the "cannot open RO when file doesn't exist yet" edge case
        # on first-channel-test-before-any-config.
        rows = local_store.get_store().query_channel_configs(
            provider=provider, limit=1)
    except Exception as e:
        return False, f"local-store read failed: {e}"
    if not rows:
        return False, "not configured"
    blob = rows[0].get("config_json_encrypted")
    if blob is None or (isinstance(blob, (bytes, bytearray)) and len(blob) == 0):
        return False, "config blob empty"
    return True, None


# ── Phase 4: proactive approvals cache_push (epic #1032) ─────────────────────
# Approvals are now authoritative in local DuckDB — the policy watcher writes
# the row, the daemon pushes the pending-queue snapshot to the cloud cache on
# every heartbeat under `approvals:{owner_hash}:queue`, and the cloud Approvals
# inbox paints from cache (no Cloud SQL row).
#
# TTL is short (60s) so the inbox stays close to real time even between
# heartbeats — acceptance criterion is "appears in cloud inbox within 2s",
# which the cache_push interval (60s default) bounds at the upper end and the
# next heartbeat overwrites at the lower end. A request that arrives BETWEEN
# heartbeats is still visible at next-heartbeat-cache-write; the 60s TTL just
# protects against a daemon that goes silent.
APPROVALS_CACHE_TTL_SEC = 60
APPROVALS_CACHE_LIMIT = 200


def _build_approvals_cache_pushes(config: dict) -> list:
    """Return the heartbeat `cache_pushes` array for pending approvals —
    a single entry holding the current pending queue owned by this cm_ token.

    Returns an empty list when:
      - The local store has no pending approvals (the cloud inbox correctly
        renders empty in that case — no push needed).
      - Encryption key is unset — we never push plaintext.
      - The local store import fails — degrade silently.

    The blob shape mirrors `/api/cloud/approvals` (cloud-side list endpoint)
    so the cloud read path can return the decrypted dict straight to the
    dashboard JS without translation."""
    enc_key = config.get("encryption_key")
    if not enc_key:
        return []
    api_key = config.get("api_key", "")
    if not api_key:
        return []
    try:
        from clawmetry import local_store
    except Exception:
        return []
    owner_hash = _owner_hash_for_token(api_key)
    try:
        store = local_store.get_store(read_only=True)
        rows = store.query_approvals(
            owner_hash=owner_hash,
            status="pending",
            limit=APPROVALS_CACHE_LIMIT,
        )
    except Exception:
        return []
    if not rows:
        return []
    payload = {
        "approvals": rows,
        "count":     len(rows),
        "_source":   "local_store",
        "_shape":    "approvals_queue",
    }
    try:
        blob = encrypt_payload(payload, enc_key)
    except Exception:
        return []
    return [{
        "key":    f"approvals:{owner_hash}:queue",
        "ttl_s":  APPROVALS_CACHE_TTL_SEC,
        "blob":   blob,
    }]


# ── Phase 6: proactive cron-runs cache_push (issue #1640) ────────────────────
# Cloud READ path (routes/cloud.py:cloud_cron_runs) reads from
# ``cron_runs:{owner_hash}:{node_id}:{job_id}``.  Without this push the
# cloud Cron modal shows perpetual ``cache_pending`` for every job's run
# history.  One encrypted blob per distinct job_id; capped at
# CRON_RUNS_JOB_LIMIT jobs so heartbeat payload size stays bounded.
CRON_RUNS_CACHE_TTL_SEC = 300   # 5 min — runs change frequently
CRON_RUNS_JOB_LIMIT = 20        # max distinct jobs per heartbeat
CRON_RUNS_LIMIT_PER_JOB = 20    # most-recent runs included per job


def _build_cron_runs_cache_pushes(config: dict) -> list:
    """Return heartbeat ``cache_pushes`` entries for cron-run history.

    One entry per distinct ``job_id`` found in the local store, keyed as
    ``cron_runs:{owner_hash}:{node_id}:{job_id}``.  Returns an empty list
    when encryption key is absent, the local store is unavailable, or no
    cron runs have been ingested yet.
    """
    enc_key = config.get("encryption_key")
    if not enc_key:
        return []
    api_key = config.get("api_key", "")
    if not api_key:
        return []
    node_id = config.get("node_id", "")
    try:
        from clawmetry import local_store
    except Exception:
        return []
    owner_hash = _owner_hash_for_token(api_key)
    try:
        store = local_store.get_store(read_only=True)
        all_runs = store.query_cron_runs(
            limit=CRON_RUNS_JOB_LIMIT * CRON_RUNS_LIMIT_PER_JOB
        )
    except Exception:
        return []
    if not all_runs:
        return []
    # Group by job_id (query already returns rows ORDER BY started_at DESC).
    by_job: dict[str, list] = {}
    for run in all_runs:
        jid = run.get("job_id") or ""
        if not jid:
            continue
        if jid not in by_job:
            if len(by_job) >= CRON_RUNS_JOB_LIMIT:
                continue
            by_job[jid] = []
        if len(by_job[jid]) < CRON_RUNS_LIMIT_PER_JOB:
            by_job[jid].append(run)
    pushes = []
    for jid, runs in by_job.items():
        payload = {
            "runs":    runs,
            "count":   len(runs),
            "_source": "local_store",
            "_shape":  "cron_runs",
        }
        try:
            blob = encrypt_payload(payload, enc_key)
        except Exception:
            continue
        pushes.append({
            "key":   f"cron_runs:{owner_hash}:{node_id}:{jid}",
            "ttl_s": CRON_RUNS_CACHE_TTL_SEC,
            "blob":  blob,
        })
    return pushes


def _dispatch_pending_queries(config: dict, pending: list) -> None:
    """Run each cloud-requested query against the local store, encrypt the
    result, and POST back to /ingest/cache. Failures on individual queries
    are swallowed (logged) so one bad query never blocks the rest.

    Two flavors of pending entry are recognized:

    1. ``{shape, id, cache_key, args}`` — read query. Dispatched via
       routes.local_query (or fallback) and the result is encrypted +
       POSTed to /ingest/cache.
    2. ``{type, …}`` — local action (write or side-effect). Routed
       through ``_dispatch_pending_action``. The unified ``_PENDING_ACTIONS``
       allowlist covers Phase 5 channel-config actions
       (``channel_config_upsert``, ``channel_test``), Phase 3 alert-rule
       writes (``alert_rule_upsert``, ``alert_rule_delete``), and Phase 4
       approval decisions (``approval_decision``). Writes are
       fire-and-forget — no /ingest/cache POST; the next heartbeat's
       cache_push surfaces the new state to the cloud.
    """
    try:
        from routes.local_query import _dispatch as _local_dispatch  # type: ignore
    except Exception:
        _local_dispatch = _local_dispatch_fallback
    api_key = config.get("api_key", "")
    enc_key = config.get("encryption_key")
    node_id = config.get("node_id", "")
    for q in pending or []:
        try:
            if not isinstance(q, dict):
                continue
            # Action-style entry (epic #1032 Phase 5 onwards): no shape,
            # has a `type`. Dispatched locally; no /ingest/cache POST —
            # the next heartbeat's cache_push carries the new state.
            qtype = q.get("type")
            if qtype:
                try:
                    _dispatch_pending_action(config, q)
                except Exception as e:
                    log.warning("pending_action dispatch failed (type=%s): %s",
                                qtype, e)
                continue
            shape = q.get("shape")
            if shape not in _PENDING_SHAPES:
                continue  # defensive — cloud should have already filtered
            qid = q.get("id")
            cache_key = q.get("cache_key")
            args = q.get("args") or {}
            result = _local_dispatch(shape, args)
            if not enc_key:
                log.debug("pending_query %s: no encryption key; skipping", qid)
                continue
            # Bug 2026-05-13 (real MOAT fix): when this pending_query targets
            # the Brain cache key (`brain:*:recent`), the cloud's browser-side
            # `_cm_decryptBrain` reads `dec.events` from the decrypted blob.
            # `_local_dispatch('events', ...)` returns the raw shape
            # `{rows: [...], count, _shape, _via}` though — so the browser
            # sees `dec.events || []` = empty and shows "No brain activity
            # events found" even with hundreds of events in DuckDB. Translate
            # to the dashboard-display shape via `_rows_to_brain_events` so
            # both this writer and `_build_brain_cache_pushes` produce
            # identical blobs (one shouldn't silently overwrite the other
            # with a wrong-shape payload).
            payload = result
            if shape == "events" and isinstance(cache_key, str) \
                    and cache_key.startswith("brain:"):
                rows = (result or {}).get("rows") if isinstance(result, dict) else None
                events = _rows_to_brain_events(rows or [])
                payload = {
                    "events":  events,
                    "count":   len(events),
                    "_source": "local_store",
                    "_shape":  "brain_history",
                }
            blob = encrypt_payload(payload, enc_key)
            _post("/ingest/cache", {
                "node_id": node_id,
                "id": qid,
                "cache_key": cache_key,
                "blob": blob,
                "shape": shape,
                "args_hash": _canonical_args_hash(args),
                "ttl": 3600,
            }, api_key)
        except Exception as e:
            log.warning("pending_query dispatch failed (id=%s shape=%s): %s",
                        (q or {}).get("id") if isinstance(q, dict) else None,
                        (q or {}).get("shape") if isinstance(q, dict) else None,
                        e)


# ── Write-through helper (Phase 3 of #1032) ─────────────────────────────────
# Applies alert-rule writes from the cloud-relayed pending_queries channel to
# the local DuckDB. Dispatched from ``_dispatch_pending_action`` via the
# unified ``_PENDING_ACTIONS`` allowlist. Mirrors the cloud-side enqueue path
# (clawmetry-cloud/routes/alerts.py:_enqueue_alert_rule_change).


def _apply_pending_write(qtype: str, q: dict, owner_hash: str | None = None) -> None:
    """Apply one cloud-authored write to the local DuckDB.

    Routed by ``type``:

      ``alert_rule_upsert`` → ``ingest_alert_rule(body)``
      ``alert_rule_delete`` → ``delete_alert_rule(id)``

    Raises on bad input so the caller's per-item logger flags it. Cloud is
    already responsible for shape validation, so this is defense-in-depth.
    """
    from clawmetry import local_store
    store = local_store.get_store()
    if qtype == "alert_rule_upsert":
        body = q.get("body") or {}
        if not isinstance(body, dict):
            raise ValueError("alert_rule_upsert: body must be a dict")
        # The cloud uses `alert_type` (its own column) — translate into the
        # OSS local-store shape: condition_json holds the whole cloud body so
        # the evaluator + dashboard get everything without a follow-up fetch.
        rule = {
            "id":            body.get("id") or q.get("id"),
            "owner_hash":    body.get("owner_hash") or owner_hash,
            "name":          body.get("name"),
            "condition_json": body,
            "enabled":       body.get("enabled", True),
            "created_at":    body.get("created_at"),
            "updated_at":    body.get("updated_at"),
            "last_fired_at": body.get("last_triggered_at"),
            "fire_count":    body.get("trigger_count") or 0,
        }
        if not rule["id"]:
            raise ValueError("alert_rule_upsert: id required")
        store.ingest_alert_rule(rule)
        log.info("local store: applied alert_rule_upsert id=%s", rule["id"])
        return
    if qtype == "alert_rule_delete":
        rid = q.get("id")
        if not rid:
            raise ValueError("alert_rule_delete: id required")
        n = store.delete_alert_rule(rid)
        log.info("local store: applied alert_rule_delete id=%s (rows=%d)", rid, n)
        return
    # Unknown write — caller already gated via _PENDING_ACTIONS; reaching
    # here means the allowlist was changed without wiring this dispatcher.
    raise ValueError(f"unhandled write type: {qtype}")


def _apply_approval_decision(q: dict) -> None:
    """Flip an approvals row in local DuckDB based on a cloud-relayed
    decision. Used by `_dispatch_pending_queries`.

    Expected shape: ``{type: "approval_decision", id, decision, resolver,
    reason}``. ``id`` and ``decision`` are required; ``resolver`` defaults
    to a cloud-attribution string when unset; ``reason`` is optional.

    Idempotent: ``update_approval_decision`` only flips rows still in
    ``pending`` state, so a duplicate relay delivery is a no-op."""
    approval_id = (q.get("id") or "").strip()
    decision = (q.get("decision") or "").strip()
    if not approval_id or not decision:
        log.warning("approval_decision pending_query missing id/decision: %r", q)
        return
    resolver = (q.get("resolver") or "cloud-relay").strip()
    reason = q.get("reason")
    try:
        from clawmetry import local_store
        store = local_store.get_store()
    except Exception as e:
        log.warning("approval_decision %s: local_store unavailable: %s",
                    approval_id, e)
        return
    try:
        n = store.update_approval_decision(approval_id, decision, resolver,
                                            reason)
    except Exception as e:
        log.warning("approval_decision %s: update failed: %s", approval_id, e)
        return
    if n:
        log.info("[approval] %s relayed decision=%s by %s (status flipped)",
                 approval_id, decision, resolver)
    else:
        # Either unknown id or already decided — both safe to ignore.
        log.debug("[approval] %s relayed decision=%s — no-op (row missing or "
                  "already decided)", approval_id, decision)


def _get_version() -> str:
    try:
        import re

        src = (Path(__file__).parent.parent / "dashboard.py").read_text(
            errors="replace"
        )
        m = re.search(r'^__version__\s*=\s*["\'](.+?)["\']', src, re.M)
        return m.group(1) if m else "unknown"
    except Exception:
        return "unknown"


# ── Daemon loop ────────────────────────────────────────────────────────────────


# Heartbeat interval: re-emit an unchanged cron_state after this many seconds
# so the server's "last seen" TTL doesn't expire the job. See issue #599.
CRON_STATE_HEARTBEAT_SEC = 300  # 5 minutes


def sync_crons(config: dict, state: dict, paths: dict) -> int:
    """Sync cron job definitions to cloud.

    Skipped when the cloud has flagged this account's sync as paused (e.g.
    expired trial). Heartbeats keep firing so we detect upgrade.

    Dedup strategy (issue #599): emit a cron_state event per job only when the
    per-job state hash differs from the last emission, OR when the heartbeat
    interval (CRON_STATE_HEARTBEAT_SEC) has elapsed since the last emission
    for that job. Dedup tracking is persisted in the sync state dict so it
    survives daemon restarts.
    """
    if not _sync_allowed():
        return 0
    _record_sync_progress("crons", 0)
    api_key = config["api_key"]
    node_id = config["node_id"]
    last_hash = state.get("cron_hash", "")
    # Per-job dedup tracking: job_id -> [sha1_hash, last_emit_unix_ts]
    # Stored as list (not tuple) because JSON round-trip turns tuples into lists.
    job_dedup: dict = state.setdefault("cron_state_dedup", {})

    # Find cron jobs.json
    Path.home()
    cron_candidates = [
        Path(_get_openclaw_dir()) / "cron" / "jobs.json",
        Path(_get_openclaw_dir()) / "agents" / "main" / "cron" / "jobs.json",
    ]
    cron_file = next((str(p) for p in cron_candidates if p.exists()), None)
    if not cron_file:
        return 0

    try:
        import hashlib

        raw = open(cron_file, "rb").read()
        h = hashlib.md5(raw).hexdigest()
        file_unchanged = h == last_hash
        data = json.loads(raw)
        jobs = data.get("jobs", []) if isinstance(data, dict) else data

        now_ts = time.time()
        events = []
        emitted_job_ids: list = []
        for j in jobs:
            sched = j.get("schedule", {})
            kind = sched.get("kind", "")
            expr = (
                sched.get("interval", "")
                if kind == "interval"
                else (
                    f"at {sched.get('at', '')}"
                    if kind == "at"
                    else sched.get("cron", "")
                    if kind == "cron"
                    else ""
                )
            )
            job_state = j.get("state", {})
            job_id = j.get("id", "")
            event_data = {
                "job_id": job_id,
                "name": j.get("name", ""),
                "enabled": j.get("enabled", True),
                "expr": expr,
                "schedule": sched,
                "task": (j.get("task") or "")[:200],
                "state": {
                    "lastStatus": job_state.get("lastStatus"),
                    "lastRunAtMs": job_state.get("lastRunAtMs"),
                    "nextRunAtMs": job_state.get("nextRunAtMs"),
                    "lastDurationMs": job_state.get("lastDurationMs"),
                    "lastError": job_state.get("lastError"),
                    "consecutiveFailures": job_state.get("consecutiveFailures"),
                },
            }

            # Dedup: sha1 over the full event payload with sorted keys so the
            # hash is stable across poll iterations when nothing changed.
            job_hash = hashlib.sha1(
                json.dumps(event_data, sort_keys=True).encode("utf-8")
            ).hexdigest()
            prev = job_dedup.get(job_id) or [None, 0.0]
            prev_hash = prev[0] if len(prev) >= 1 else None
            prev_ts = prev[1] if len(prev) >= 2 else 0.0
            changed = job_hash != prev_hash
            stale = (now_ts - float(prev_ts or 0.0)) >= CRON_STATE_HEARTBEAT_SEC
            if not changed and not stale:
                continue

            events.append(
                {
                    "type": "cron_state",
                    "session_id": "",
                    "data": event_data,
                }
            )
            emitted_job_ids.append((job_id, job_hash))

            # Local-store write-through (epic #964 / DuckDB MOAT). Mirrors
            # what we just emitted to cloud — the dashboard's
            # /api/local/* path reads from `crons` table directly so this
            # has to land BEFORE cloud sync acks. Failures are logged
            # but non-fatal: legacy gateway-fetch path still works.
            try:
                from clawmetry import local_store as _ls
                _ls.get_store().ingest_cron({
                    "cron_id":     job_id,
                    "agent_type":  "openclaw",
                    "name":        j.get("name", ""),
                    "schedule":    expr,
                    "enabled":     bool(j.get("enabled", True)),
                    "last_run_at": str(job_state.get("lastRunAtMs") or ""),
                    "last_status": str(job_state.get("lastStatus") or ""),
                    "next_run_at": str(job_state.get("nextRunAtMs") or ""),
                    # All other freeform fields go into the BLOB
                    "task":        (j.get("task") or "")[:500],
                    "lastDurationMs":      job_state.get("lastDurationMs"),
                    "lastError":           job_state.get("lastError"),
                    "consecutiveFailures": job_state.get("consecutiveFailures"),
                })
            except Exception as _e:
                log.debug("local_store: ingest_cron failed for %s: %s",
                          job_id, _e)

        if events:
            _post("/api/ingest", {"events": events, "node_id": node_id}, api_key)
            # Only record new hashes/timestamps after the POST succeeds so a
            # transient ingest failure re-emits next cycle.
            for job_id, job_hash in emitted_job_ids:
                job_dedup[job_id] = [job_hash, now_ts]
            state["cron_hash"] = h
            _record_sync_progress("crons", len(events), len(events))
            return len(events)
        elif not file_unchanged:
            # File mtime/content changed but every job was deduped — still
            # record the new file hash so we don't re-parse it next tick.
            state["cron_hash"] = h
    except Exception as e:
        log.warning(f"Cron sync error: {e}")
    _record_sync_progress("crons", 0, 0)
    return 0


# ── Cron-run JSONL → DuckDB ingest (issue #605 DuckDB follow-up) ─────────
#
# OpenClaw's cron writer appends one JSON record per run to
# ``~/.openclaw/cron/runs/<jobId>.jsonl``. PR #1147 had the dashboard route
# parse those files on every request; this helper moves the parse into the
# sync daemon so the API can read from columnar DuckDB instead.
#
# Per-file offset tracking lives under ``state["cron_run_offsets"]`` so the
# daemon only re-reads new bytes each cycle. Offsets that point past the
# current file size (post-rotation, truncation) reset to 0 — the
# ``INSERT OR IGNORE`` on the cron_runs table makes the catch-up scan a
# no-op for already-stored rows.
#
# The function is deliberately resilient: any per-file or per-line failure
# is logged at debug level and skipped, never raised. ClawMetry is
# read-only-by-default; a malformed cron jsonl line must not break the
# rest of the sync cycle.


def _cron_run_dirs() -> list[Path]:
    """Candidate ``cron/runs`` directories, in resolution order. Mirrors
    ``routes/crons.py:_resolve_cron_runs_jsonl`` so the daemon picks up the
    same files the API would have read.
    """
    roots: list[str] = []
    data_dir = os.environ.get("OPENCLAW_DATA_DIR", "").strip()
    if data_dir:
        roots.append(os.path.expanduser(data_dir))
    home = os.environ.get("OPENCLAW_HOME", "").strip()
    if home:
        roots.append(os.path.expanduser(home))
    roots.append(_get_openclaw_dir())
    roots.append(os.path.expanduser("~/.clawdbot"))
    out: list[Path] = []
    seen: set[str] = set()
    for r in roots:
        p = Path(r) / "cron" / "runs"
        rp = str(p)
        if rp in seen:
            continue
        seen.add(rp)
        if p.exists() and p.is_dir():
            out.append(p)
    return out


def _parse_cron_run_line(line: str, job_id: str, node_id: str) -> dict | None:
    """Parse one JSONL line into the ``LocalStore.ingest_cron_run`` shape.

    Returns ``None`` on malformed JSON or non-dict payloads. The local
    store dedups by ``id``; when the writer didn't supply one we
    synthesise it from ``job_id`` + ``started_at`` so re-reads remain
    idempotent.
    """
    line = line.strip()
    if not line:
        return None
    try:
        obj = json.loads(line)
    except Exception:
        return None
    if not isinstance(obj, dict):
        return None
    # Field-name normalisation matches the older
    # ``routes/crons.py:_read_cron_run_lines`` so OpenClaw writers shipped
    # by every gateway version round-trip cleanly.
    started_at = (
        obj.get("started_at")
        or obj.get("startedAt")
        or obj.get("ts")
        or obj.get("timestamp")
    )
    ended_at = obj.get("ended_at") or obj.get("endedAt")
    duration_ms = obj.get("duration_ms") or obj.get("durationMs") or obj.get("duration")
    status = obj.get("status") or obj.get("result") or "unknown"
    err = obj.get("error") or obj.get("err") or obj.get("error_message") or ""
    if err and not isinstance(err, str):
        err = str(err)
    usage = obj.get("usage") if isinstance(obj.get("usage"), dict) else {}
    token_count = (
        obj.get("token_count")
        or obj.get("tokens")
        or (usage.get("total_tokens") if isinstance(usage, dict) else None)
        or (usage.get("totalTokens") if isinstance(usage, dict) else None)
    )
    cost_usd = obj.get("cost_usd") or obj.get("costUsd")
    delivered_at = obj.get("delivered_at") or obj.get("deliveredAt")
    if not delivered_at and isinstance(obj.get("deliveryStatus"), dict):
        delivered_at = obj["deliveryStatus"].get("deliveredAt")
    next_run_at = (
        obj.get("next_run_at")
        or obj.get("nextRunAt")
        or obj.get("nextRunAtMs")
    )
    # Coerce timestamps to ISO strings — the DuckDB column is VARCHAR
    # because the gateway writer hasn't been consistent about epoch-ms
    # vs ISO-8601 (issue #605 has examples of both). Keeping the column
    # opaque lets us re-parse on read without a schema change.
    def _norm_ts(v: Any) -> str | None:
        if v is None:
            return None
        if isinstance(v, (int, float)):
            return str(int(v))
        return str(v)
    rid = obj.get("id") or obj.get("run_id") or obj.get("runId")
    if not rid:
        rid = f"{job_id}:{_norm_ts(started_at) or ''}"
    run = {
        "id": str(rid),
        "node_id": node_id,
        "job_id": job_id,
        "agent_type": "openclaw",
        "started_at": _norm_ts(started_at),
        "ended_at": _norm_ts(ended_at),
        "duration_ms": duration_ms,
        "status": str(status) if status is not None else None,
        "error_message": err,
        "token_count": token_count,
        "cost_usd": cost_usd,
        "delivered_at": _norm_ts(delivered_at),
        "next_run_at": _norm_ts(next_run_at),
        "raw_jsonl_line": line[:8000],
        # Preserve the freeform payload (usage dict, gateway extras) so
        # ``query_cron_runs`` callers can introspect input/output token
        # splits without losing fidelity.
        "usage": usage,
    }
    return run


def sync_cron_runs(config: dict, state: dict, paths: dict) -> int:
    """Ingest new lines from ``~/.openclaw/cron/runs/*.jsonl`` into
    ``cron_runs`` in the local DuckDB store.

    Returns the number of rows newly ingested. Idempotent: lines already
    in the table (matched on the synthesised ``id``) are skipped by the
    ``ON CONFLICT DO NOTHING`` clause in ``LocalStore.ingest_cron_run``.
    Per-file byte offsets are persisted in ``state["cron_run_offsets"]``
    so subsequent cycles only read appended bytes.

    Failure modes (all degrade silently):
      * ``local_store`` not importable → return 0, no state mutation.
      * ``~/.openclaw/cron/runs`` missing → return 0.
      * Single file unreadable / line malformed → skip that file/line,
        keep going.
    """
    try:
        from clawmetry import local_store as _ls
    except Exception as e:
        log.debug("sync_cron_runs: local_store unavailable: %s", e)
        return 0

    node_id = config.get("node_id", "") if isinstance(config, dict) else ""
    offsets: dict = state.setdefault("cron_run_offsets", {})
    runs_dirs = _cron_run_dirs()
    if not runs_dirs:
        return 0

    try:
        store = _ls.get_store()
    except Exception as e:
        log.debug("sync_cron_runs: get_store failed: %s", e)
        return 0

    n_ingested = 0
    for runs_dir in runs_dirs:
        try:
            jsonl_files = sorted(runs_dir.glob("*.jsonl"))
        except OSError:
            continue
        for fpath in jsonl_files:
            try:
                job_id = fpath.stem  # filename without ``.jsonl``
                if not job_id:
                    continue
                # Per-file offset key includes the parent dir so two
                # candidate roots don't collide on the same jobId.
                key = f"{runs_dir}/{fpath.name}"
                last_offset = int(offsets.get(key, 0))
                try:
                    size = fpath.stat().st_size
                except OSError:
                    continue
                # Truncation / rotation guard: an offset past EOF means
                # the file was rewritten — reset to 0 and rely on
                # INSERT OR IGNORE for dedup.
                if last_offset > size:
                    last_offset = 0
                if last_offset == size:
                    continue
                with open(fpath, "r", errors="replace") as fh:
                    fh.seek(last_offset)
                    for line in fh:
                        run = _parse_cron_run_line(line, job_id, node_id)
                        if run is None:
                            continue
                        try:
                            store.ingest_cron_run(run)
                            n_ingested += 1
                        except Exception as e_in:
                            log.debug(
                                "sync_cron_runs: ingest failed for %s: %s",
                                job_id, e_in,
                            )
                    new_offset = fh.tell()
                offsets[key] = new_offset
            except Exception as e_f:
                log.debug("sync_cron_runs: file %s failed: %s", fpath, e_f)
                continue
    if n_ingested:
        log.debug("sync_cron_runs: ingested %d new rows", n_ingested)
    return n_ingested


def sync_session_metadata(config: dict, state: dict = None) -> int:
    """Sync OpenClaw session metadata rows to cloud sessions table.

    Skipped when the cloud has flagged sync as paused (expired trial).
    Heartbeats continue so the daemon detects the moment the user upgrades.

    Uses mtime tracking to only re-parse files that changed since last sync.
    Reads JSONL session files directly (HTTP API returns HTML, not JSON).
    Extracts session_id, model, timestamps from the event stream.
    """
    if not _sync_allowed():
        return 0
    _record_sync_progress("session_metadata", 0)
    api_key = config["api_key"]
    node_id = config["node_id"]
    if state is None:
        state = {}
    last_mtimes: dict = state.setdefault("session_mtimes", {})
    try:
        Path.home()
        sessions_candidates = [
            Path(_get_openclaw_dir()) / "agents" / "main" / "sessions",
            Path("/data/agents/main/sessions"),
        ]
        sessions_dir = next((p for p in sessions_candidates if p.exists()), None)
        if not sessions_dir:
            return 0

        # Sort by mtime descending so the newest files are processed and
        # uploaded first — the user sees today's sessions in the cloud
        # dashboard within seconds, and older history backfills over the
        # rest of the cycle. Previously a lexical sort + [-100:] slice
        # gave a non-deterministic sample of files and silently dropped
        # the rest. mtime-skip below keeps subsequent syncs cheap.
        jsonl_files = []
        for fpath_str in _list_session_jsonls(sessions_dir):
            fpath = Path(fpath_str)
            try:
                jsonl_files.append((fpath, fpath.stat().st_mtime))
            except OSError:
                continue
        jsonl_files.sort(key=lambda pair: pair[1], reverse=True)

        # Resolve a default model up front from sessions.json (the
        # canonical source). If absent we fall back to a running mode of
        # models actually seen during the parse — the count is updated
        # as batches flush, so later batches benefit from a stronger
        # signal at the cost of slightly less consistent fallback.
        _default_model = ""
        _sid_to_key: dict[str, str] = {}  # sessionId → session key (for channel info)
        _sid_to_meta: dict[str, dict] = {}  # sessionId → {provider, chatType, subject}
        _idx_path = sessions_dir / "sessions.json"
        if _idx_path.exists():
            try:
                with open(_idx_path) as _fi:
                    _idx = json.load(_fi)
                for _k, _meta in _idx.items():
                    if isinstance(_meta, dict):
                        _sid = _meta.get("sessionId", "")
                        if _sid:
                            _sid_to_key[_sid] = _k
                            _sid_to_meta[_sid] = {
                                "provider": _meta.get("provider", ""),
                                "chatType": _meta.get("chatType", ""),
                                "subject": _meta.get("subject") or _meta.get("displayName") or "",
                            }
                        if "subagent" not in _k:
                            _m = (_meta.get("model") or "").strip()
                            if _m and not _default_model:
                                _default_model = _m
            except Exception:
                pass
        model_counts: dict = {}

        def _flush(rows):
            if not rows:
                return 0
            fallback = _default_model
            if not fallback and model_counts:
                fallback = max(model_counts.items(), key=lambda kv: kv[1])[0]
            if fallback:
                for s in rows:
                    if not s.get("model"):
                        s["model"] = fallback
            # Local-first: write through to ~/.clawmetry/events.duckdb FIRST.
            # Best-effort — never blocks cloud sync on a local-store failure.
            try:
                _local_ingest_sessions_batch(rows, node_id)
            except Exception as _e:
                log.warning("local-store sessions ingest failed (cloud sync continues): %s", _e)
            _post("/ingest/sessions", {"node_id": node_id, "sessions": rows}, api_key)
            return len(rows)

        batch: list = []
        total_uploaded = 0
        BATCH_SIZE = 50
        for fpath, current_mtime in jsonl_files:
            if last_mtimes.get(fpath.name) == current_mtime:
                continue
            try:
                # `<uuid>.jsonl` -> stem is `<uuid>`. For an archived
                # `<uuid>.jsonl.reset.<ts>` Path.stem only strips the last
                # extension (.<ts>), leaving `<uuid>.jsonl.reset`. Split on
                # the first `.jsonl` instead so live and reset archives
                # both map to the same canonical session_id.
                sid = fpath.name.split(".jsonl", 1)[0]
                started_at = ""
                updated_at = ""
                total_tokens = 0
                total_cost = 0.0
                label = ""
                # Aggregate model usage across the session — a single session
                # can span several models (model_change mid-conversation, or
                # an orchestrator that routes to different backends). Previously
                # we stored "last model seen," which was arbitrary for multi-
                # model sessions. Now we keep the per-model token count and
                # pick the dominant one as the primary.
                model_tokens: dict = {}
                last_seen_model = ""
                # event_count (= JSONL line count) is the "messages" badge
                # the Embodied tab renders. The cloud Postgres copy of the
                # sessions table was previously plaintext-blank for this
                # column because the daemon never uploaded it, so every
                # cloud row showed "0 messages" even on actively chatting
                # sessions (cloud fix/embodied-tab-zeros). Counting bytes
                # too lets the cloud render "8.4 KB" rather than "0 B".
                event_count = 0
                size_bytes = 0
                try:
                    size_bytes = int(fpath.stat().st_size)
                except Exception:
                    pass

                # Scan session file for metadata, tokens, cost, model
                # Read head for start info, scan all for usage, tail for end
                with open(fpath, "r", errors="replace") as f:
                    for raw in f:
                        raw = raw.strip()
                        if not raw:
                            continue
                        event_count += 1
                        try:
                            ev = json.loads(raw)
                        except Exception:
                            continue
                        ts = ev.get("timestamp", "")
                        if not started_at and ts:
                            started_at = ts
                        if ts:
                            updated_at = ts
                        etype = ev.get("type", "")
                        if etype == "model_change" and ev.get("modelId"):
                            last_seen_model = ev["modelId"]
                        elif etype == "session" and ev.get("label"):
                            label = ev["label"]
                        elif etype == "message":
                            msg = ev.get("message", {})
                            msg_model = msg.get("model", "") or last_seen_model
                            usage = msg.get("usage", {})
                            if usage:
                                tks = int(usage.get("totalTokens", 0))
                                total_tokens += tks
                                if msg_model and tks:
                                    model_tokens[msg_model] = model_tokens.get(msg_model, 0) + tks
                                cost_obj = usage.get("cost", {})
                                if isinstance(cost_obj, dict):
                                    total_cost += float(cost_obj.get("total", 0))
                                elif isinstance(cost_obj, (int, float)):
                                    total_cost += float(cost_obj)
                            if msg_model:
                                last_seen_model = msg_model

                # Primary = model that consumed the most tokens in this session,
                # with last_seen_model as a tiebreaker for sessions that had a
                # model_change but no message-level usage yet.
                if model_tokens:
                    model = max(model_tokens.items(), key=lambda kv: kv[1])[0]
                else:
                    model = last_seen_model

                if model:
                    model_counts[model] = model_counts.get(model, 0) + 1
                # Resolve display name from session key when available
                _sk = _sid_to_key.get(sid, "")
                _sm = _sid_to_meta.get(sid, {})
                _dn = label or _sm.get("subject") or _sk or sid[:8]
                batch.append(
                    {
                        "session_id": sid,
                        "display_name": _dn,
                        "session_key": _sk,
                        "channel": _sm.get("provider", ""),
                        "chat_type": _sm.get("chatType", ""),
                        "status": "completed",
                        "model": model,
                        "recent_model": last_seen_model or model,
                        "total_tokens": total_tokens,
                        "total_cost": total_cost,
                        "started_at": started_at,
                        "updated_at": updated_at,
                        # Plaintext aggregates so the cloud Embodied tab can
                        # render real "55 messages, 8.4 KB" rows instead of
                        # zeros. Older cloud servers ignore unknown keys.
                        "event_count": event_count,
                        "size_bytes": size_bytes,
                    }
                )
                last_mtimes[fpath.name] = current_mtime
                if len(batch) >= BATCH_SIZE:
                    total_uploaded += _flush(batch)
                    batch = []
            except Exception as e:
                log.debug(f"Session parse error ({fpath.name}): {e}")

        total_uploaded += _flush(batch)
        _record_sync_progress("session_metadata", total_uploaded, total_uploaded)
        return total_uploaded
    except Exception as e:
        log.warning(f"Session metadata sync failed: {e}")
        _record_sync_progress("session_metadata", 0, 0)
        return 0


def sync_memory(config: dict, state: dict, paths: dict) -> int:
    """Sync memory files (MEMORY.md + memory/*.md) to cloud.

    Skipped when sync is paused (expired trial)."""
    if not _sync_allowed():
        return 0
    _record_sync_progress("memory", 0)
    workspace = paths.get("workspace", "")
    api_key = config["api_key"]
    enc_key = config.get("encryption_key")
    node_id = config["node_id"]
    last_hashes: dict = state.setdefault("memory_hashes", {})
    synced = 0

    # Collect all workspace memory files (same list as OSS dashboard)
    memory_files = []
    for name in [
        "MEMORY.md",
        "SOUL.md",
        "IDENTITY.md",
        "USER.md",
        "AGENTS.md",
        "TOOLS.md",
        "HEARTBEAT.md",
    ]:
        fpath = os.path.join(workspace, name)
        if os.path.isfile(fpath):
            memory_files.append((name, fpath))
    mem_dir = os.path.join(workspace, "memory")
    if os.path.isdir(mem_dir):
        for f in sorted(os.listdir(mem_dir)):
            if f.endswith(".md"):
                memory_files.append((f"memory/{f}", os.path.join(mem_dir, f)))

    if not memory_files:
        _record_sync_progress("memory", 0, 0)
        return 0

    # Check for changes via content hash; always send all file contents so the
    # Memory tab can display any file, not just files changed in the last cycle.
    import hashlib

    changed_files = []
    all_file_contents = []
    file_list = []
    for name, path in memory_files:
        try:
            content_bytes = open(path, "rb").read()
            h = hashlib.md5(content_bytes).hexdigest()
            text = content_bytes.decode("utf-8", errors="replace")
            file_list.append(
                {
                    "name": name,
                    "size": len(content_bytes),
                    "modified": os.path.getmtime(path),
                }
            )
            all_file_contents.append((name, text))
            if h != last_hashes.get(name):
                changed_files.append(name)
                last_hashes[name] = h
        except Exception as e:
            log.debug(f"Memory file read error ({name}): {e}")

    if not changed_files:
        _record_sync_progress("memory", len(memory_files), len(memory_files))
        return 0

    # Push memory files as encrypted blob (like session events).
    # Always include ALL file contents so the Memory tab can render any file.
    payload = {
        "node_id": node_id,
        "memory_state": {"files": file_list},
        "memory_content": [
            {"path": name, "content": content[:100000]}
            for name, content in all_file_contents
        ],
    }
    try:
        # Local-first: write changed memory files to local DuckDB BEFORE cloud.
        # The local store gets PLAINTEXT (it's the user's own machine); cloud
        # gets ciphertext when E2E is on. Best-effort.
        try:
            _local_ingest_memory_files(all_file_contents, changed_files)
        except Exception as _le:
            log.warning("local-store memory ingest failed (cloud sync continues): %s", _le)

        if enc_key:
            from clawmetry.sync import encrypt_payload

            _post(
                "/ingest/memory",
                {
                    "node_id": node_id,
                    "encrypted": True,
                    "blob": encrypt_payload(payload, enc_key),
                },
                api_key,
            )
        else:
            _post("/ingest/memory", payload, api_key)
        synced = len(changed_files)
    except Exception as e:
        log.warning(f"Memory sync error: {e}")

    _record_sync_progress("memory", synced, len(memory_files))
    return synced

    # ── Real-time log streaming ────────────────────────────────────────────────────

    """Build memory file list for the Memory popup."""


# ── BOOTSTRAP.md "First Contact" capture (issue #690) ─────────────────────────
#
# OpenClaw's BOOTSTRAP.md runs once at first startup to negotiate agent identity
# and then SELF-DELETES. We watch for it on every daemon tick and snapshot the
# file (plus the session id active when we saw it) into the local DuckDB
# `bootstrap_archive` table BEFORE OpenClaw removes it. The store is the
# authority — once captured, the artifact is read-only and survives any
# subsequent re-init / workspace move.
#
# Idempotent: `local_store.ingest_bootstrap_archive` dedups on
# (node_id, agent_id, content_sha256), so re-running the capture on an
# unchanged file is a no-op. If OpenClaw rewrites BOOTSTRAP.md with new content
# (re-negotiated identity), a fresh row is inserted, preserving the full
# first-contact history.

_BOOTSTRAP_CANDIDATE_PATHS = (
    # Documented spec location.
    ("agents", "main", "memory", "BOOTSTRAP.md"),
    # Some OpenClaw builds keep the file at the workspace root.
    ("agents", "main", "BOOTSTRAP.md"),
    ("BOOTSTRAP.md",),
)


def _find_bootstrap_file(workspace: str | None = None) -> Path | None:
    """Return the path to a present BOOTSTRAP.md, or None when absent.

    Checks the documented location first, then a couple of fallbacks that
    have been observed in the wild. Returns the first hit — bootstrap files
    don't coexist."""
    bases: list[Path] = [Path(_get_openclaw_dir())]
    if workspace:
        try:
            bases.append(Path(workspace))
        except Exception:
            pass
    for base in bases:
        for parts in _BOOTSTRAP_CANDIDATE_PATHS:
            candidate = base.joinpath(*parts)
            try:
                if candidate.is_file():
                    return candidate
            except OSError:
                continue
    return None


def _latest_session_id(workspace: str | None = None) -> str | None:
    """Best-effort: return the session id of the most-recently-modified
    JSONL transcript when the bootstrap was captured. We link the artifact
    to it so the dashboard can show "First Contact ⇄ first session" together.
    None when no session transcripts exist (bootstrap captured before any
    session, which is the normal first-boot case)."""
    candidates: list[Path] = [
        Path(_get_openclaw_dir()) / "agents" / "main" / "sessions",
    ]
    if workspace:
        try:
            candidates.append(Path(workspace) / "agents" / "main" / "sessions")
        except Exception:
            pass
    for sessions_dir in candidates:
        try:
            if not sessions_dir.is_dir():
                continue
        except OSError:
            continue
        newest_mtime = -1.0
        newest: Path | None = None
        try:
            for p in sessions_dir.iterdir():
                if p.suffix != ".jsonl":
                    continue
                try:
                    mt = p.stat().st_mtime
                except OSError:
                    continue
                if mt > newest_mtime:
                    newest_mtime = mt
                    newest = p
        except OSError:
            continue
        if newest is not None:
            # File name is the session id; strip the suffix.
            return newest.stem
    return None


def capture_bootstrap_if_present(
    config: dict | None = None,
    paths: dict | None = None,
    *,
    store=None,
) -> bool:
    """Daemon tick hook: snapshot BOOTSTRAP.md to the local store when
    present. Returns True when a NEW row was written, False otherwise
    (file absent, unchanged, or write failure — failure is logged but
    never raised, the daemon must keep ticking).

    ``store`` is overridable for tests; defaults to the process-wide
    LocalStore singleton."""
    try:
        config = config or {}
        node_id = config.get("node_id") or ""
        if not node_id:
            # Defensive — run_daemon backfills this on startup. Without it
            # we can't dedup, so skip silently.
            return False
        workspace = ""
        if paths:
            workspace = paths.get("workspace") or ""
        bootstrap_path = _find_bootstrap_file(workspace=workspace)
        if bootstrap_path is None:
            return False
        try:
            content_bytes = bootstrap_path.read_bytes()
        except OSError as e:
            log.warning("bootstrap capture: read failed for %s: %s",
                        bootstrap_path, e)
            return False
        try:
            content = content_bytes.decode("utf-8", errors="replace")
        except Exception:
            content = content_bytes.decode("latin-1", errors="replace")
        if not content.strip():
            # Empty BOOTSTRAP.md is meaningless — wait until OpenClaw fills it.
            return False
        import hashlib
        from datetime import datetime, timezone

        sha = hashlib.sha256(content.encode("utf-8")).hexdigest()
        try:
            mtime_iso = datetime.fromtimestamp(
                bootstrap_path.stat().st_mtime, tz=timezone.utc
            ).isoformat()
        except OSError:
            mtime_iso = None

        # Defer the import so a missing duckdb dep (older installs) doesn't
        # take the daemon down — bootstrap capture is best-effort.
        if store is None:
            try:
                from clawmetry import local_store as _ls
                store = _ls.get_store()
            except Exception as e:
                log.warning("bootstrap capture: local_store unavailable: %s", e)
                return False

        first_session = _latest_session_id(workspace=workspace)
        try:
            wrote = store.ingest_bootstrap_archive({
                "node_id": node_id,
                "agent_id": "main",
                "captured_at": datetime.now(timezone.utc).isoformat(),
                "file_mtime": mtime_iso,
                "content": content,
                "content_sha256": sha,
                "first_session_id": first_session,
                "size_bytes": len(content_bytes),
                "source_path": str(bootstrap_path),
            })
        except Exception as e:
            log.warning("bootstrap capture: ingest failed: %s", e)
            return False
        if wrote:
            log.info(
                "bootstrap capture: archived %s (sha=%s, session=%s)",
                bootstrap_path, sha[:12], first_session or "n/a",
            )
        return wrote
    except Exception as e:
        # Catch-all so a bug in this helper never crashes the daemon loop.
        log.warning("bootstrap capture: unexpected error: %s", e)
        return False


def _build_machine_info():
    """Build machine hardware info for the Machine popup."""
    try:
        import platform, subprocess, socket

        items = []
        items.append(
            {"label": "Hostname", "value": socket.gethostname(), "status": "ok"}
        )
        # IP
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            items.append({"label": "IP", "value": ip, "status": "ok"})
        except Exception:
            items.append({"label": "IP", "value": "unknown", "status": "warning"})
        # CPU
        items.append({"label": "CPU", "value": platform.machine(), "status": "ok"})
        # CPU Cores
        try:
            import multiprocessing

            items.append(
                {
                    "label": "CPU Cores",
                    "value": str(multiprocessing.cpu_count()),
                    "status": "ok",
                }
            )
        except Exception:
            pass
        # Load average
        try:
            load = os.getloadavg()
            items.append(
                {
                    "label": "Load (1/5/15m)",
                    "value": f"{load[0]:.2f} / {load[1]:.2f} / {load[2]:.2f}",
                    "status": "ok",
                }
            )
        except Exception:
            pass
        # GPU
        try:
            gpu = (
                subprocess.check_output(
                    ["nvidia-smi", "--query-gpu=name", "--format=csv,noheader"],
                    timeout=5,
                )
                .decode()
                .strip()
            )
            items.append({"label": "GPU", "value": gpu, "status": "ok"})
        except Exception:
            items.append(
                {"label": "GPU", "value": "N/A (no nvidia-smi)", "status": "ok"}
            )
        # Kernel
        items.append({"label": "Kernel", "value": platform.release(), "status": "ok"})
        return {"items": items}
    except Exception as e:
        log.warning(f"Machine info error: {e}")
        return {"items": []}


def _build_runtime_info():
    """Build runtime environment info for the Runtime popup."""
    try:
        import platform, subprocess

        items = []
        items.append(
            {"label": "Python", "value": platform.python_version(), "status": "ok"}
        )
        items.append(
            {
                "label": "OS",
                "value": f"{platform.system()} {platform.release()}",
                "status": "ok",
            }
        )
        items.append(
            {"label": "Architecture", "value": platform.machine(), "status": "ok"}
        )
        # OpenClaw version
        try:
            oc_ver = (
                subprocess.check_output(
                    ["openclaw", "--version"], stderr=subprocess.STDOUT, timeout=5
                )
                .decode()
                .strip()
            )
            items.append({"label": "OpenClaw", "value": oc_ver, "status": "ok"})
        except Exception:
            items.append({"label": "OpenClaw", "value": "unknown", "status": "warning"})
        # Disk /
        try:
            df = (
                subprocess.check_output(["df", "-h", "/"], timeout=5)
                .decode()
                .strip()
                .split("\n")
            )
            if len(df) >= 2:
                parts = df[1].split()
                pct = int(parts[4].replace("%", ""))
                st = "critical" if pct > 90 else "warning" if pct > 80 else "ok"
                items.append(
                    {
                        "label": "Disk /",
                        "value": f"{parts[2]} / {parts[1]} ({parts[4]} used)",
                        "status": st,
                    }
                )
        except Exception:
            pass
        # Node.js
        try:
            nv = (
                subprocess.check_output(["node", "--version"], timeout=5)
                .decode()
                .strip()
            )
            items.append({"label": "Node.js", "value": nv, "status": "ok"})
        except Exception:
            pass
        return {"items": items}
    except Exception as e:
        log.warning(f"Runtime info error: {e}")
        return {"items": []}


def _build_diagnostics(workspace=None):
    """Build the Diagnostics snapshot (detected config) for the cloud panel.

    Mirrors the OSS ``/api/diagnostics`` endpoint (routes/health.py) so cloud
    users see the same detected-config view the host shows, instead of the old
    "Diagnostics are local-only" dead-end. The auth-token VALUE is never
    included — only whether one is present. Best-effort: any failure yields an
    empty dict and the cloud falls back to its hint copy. Late-imports
    ``dashboard`` (the daemon can already import it for capture_gateway_metric).
    """
    try:
        import dashboard as _d

        gw_port = _d._detect_gateway_port()
        gw_url = _d.GATEWAY_URL or f"http://localhost:{gw_port}"
        auto_detected = []
        if not _d.GATEWAY_URL:
            auto_detected.append("gateway_port")
        ws = _d.WORKSPACE or workspace or os.getcwd()
        if _d.WORKSPACE or workspace:
            auto_detected.append("workspace")
        token = _d.GATEWAY_TOKEN or os.environ.get("OPENCLAW_GATEWAY_TOKEN", "").strip()
        # The daemon process never runs the dashboard's startup token detection,
        # so _d.GATEWAY_TOKEN is None here and (under launchd) the env var is
        # unset — auth_token_status was wrongly "missing" in the snapshot even
        # when openclaw.json has a gateway token. Fall back to the same detector
        # the dashboard and security posture use (reads gateway.auth.token).
        if not token:
            try:
                token = _d._detect_gateway_token() or ""
            except Exception:
                token = ""
        auth_token_status = "present" if token else "missing"
        openclaw_flags = {}
        flag_map = {
            "OPENCLAW_MODEL": "model",
            "OPENCLAW_REASONING": "reasoning",
            "OPENCLAW_THINKING": "thinking",
            "OPENCLAW_MAX_TOKENS": "max_tokens",
        }
        for env_key, flag_name in flag_map.items():
            val = os.environ.get(env_key, "").strip()
            if val:
                openclaw_flags[flag_name] = val
        try:
            warnings_list, _tips = _d.validate_configuration()
        except Exception:
            warnings_list = []
        return {
            "gateway_url": gw_url,
            "gateway_port": gw_port,
            "workspace_path": ws,
            "auth_token_status": auth_token_status,
            "openclaw_flags": openclaw_flags,
            "warnings": warnings_list,
            "auto_detected": auto_detected,
        }
    except Exception as _e:
        log.debug("diagnostics snapshot build failed: %s", _e)
        return {}


def _build_model_attribution():
    """Per-turn model attribution for the cloud Models tab.

    Mirrors the OSS ``/api/model-attribution`` shape (``{models:[{model,turns,
    sessions,share_pct}], switches, total_turns, primary_model}``) so cloud
    renders the exact data OSS shows. The Models tab needs PER-TURN
    attribution, which only lives in the local DuckDB (the cloud sessions
    table only has per-session primary model).

    Computed on the daemon's OWN store handle (the DuckDB writer connection),
    NOT routes.usage._try_local_store_model_attribution() — that does a
    read-only re-open which conflicts with the daemon's write lock (DuckDB
    locks at the process level) and silently returns empty inside the daemon.
    Best-effort: any failure yields {} (cloud falls back to its empty state).
    """
    try:
        from collections import defaultdict
        from clawmetry import local_store as _ls

        store = _ls.get_store()
        if store is None:
            return {}
        evs = store.query_events(limit=20000)
        if not evs:
            return {}
        model_turns: dict = {}
        sess_models = defaultdict(list)
        saw_any = False
        for ev in sorted(evs, key=lambda e: (e.get("session_id") or "", e.get("ts") or "")):
            m = (ev.get("model") or "").strip()
            if not m:
                continue
            saw_any = True
            model_turns[m] = model_turns.get(m, 0) + 1
            sid = ev.get("session_id") or ""
            if sid and (not sess_models[sid] or sess_models[sid][-1] != m):
                sess_models[sid].append(m)
        if not saw_any:
            return {}
        model_sessions: dict = {}
        switches = []
        for sid, mlist in sess_models.items():
            model_sessions[mlist[0]] = model_sessions.get(mlist[0], 0) + 1
            for prev, nxt in zip(mlist, mlist[1:]):
                switches.append({"session": sid, "from_model": prev, "to_model": nxt})
        total_turns = sum(model_turns.values())
        sorted_models = sorted(model_turns.items(), key=lambda x: -x[1])
        primary_model = sorted_models[0][0] if sorted_models else ""
        models_out = [{
            "model": m, "turns": t, "sessions": model_sessions.get(m, 0),
            "share_pct": round(t / total_turns * 100, 2) if total_turns else 0,
        } for m, t in sorted_models]
        return {"models": models_out, "switches": switches,
                "total_turns": total_turns, "primary_model": primary_model}
    except Exception as _e:
        log.debug("model attribution snapshot build failed: %s", _e)
        return {}


def _build_transcripts(limit_sessions=8, msg_cap=80, extra_sids=None):
    """Recent per-session transcripts for the cloud Embodied tab.

    Built on the daemon's OWN store handle (a read-only re-open deadlocks the
    write lock — same trap as model attribution). Returns ``{session_id:
    <transcript dict>}`` for the most-recent sessions, message-capped to bound
    the encrypted snapshot size. The transcript dict matches what
    ``/api/transcript/<id>`` returns, so the cloud just hands it to the
    existing Embodied renderer.

    ``extra_sids`` are session ids that MUST be included even if they fall
    outside the most-recent-N window — e.g. ACTIVE sub-agents, so the cloud
    Active Tasks click-through ("see what this sub-agent is doing") has a
    transcript to render. Best-effort -> {}.
    """
    try:
        from clawmetry import local_store as _ls
        import routes.sessions as _s

        store = _ls.get_store()
        if store is None:
            return {}
        from clawmetry.config import hide_clawmetry_session
        evs = store.query_events(limit=5000)  # DESC by ts (most recent first)
        recent_sids = []
        for e in (evs or []):
            sid = (e.get("session_id") or "").strip()
            # Hide ClawMetry's own helper sessions (clawmetry-*) from the cloud
            # snapshot too — they're plumbing, not the user's agent activity.
            if sid and not hide_clawmetry_session(sid) and sid not in recent_sids:
                recent_sids.append(sid)
            if len(recent_sids) >= limit_sessions:
                break
        # Always include explicitly-requested sessions (active sub-agents).
        for sid in (extra_sids or []):
            sid = (sid or "").strip()
            if sid and sid not in recent_sids:
                recent_sids.append(sid)
        if not recent_sids:
            return {}
        out = {}
        for sid in recent_sids:
            try:
                rows = store.query_events(session_id=sid, limit=10000)
                t = _s._try_local_store_transcript(sid, _events=rows)
            except Exception:
                t = None
            if t and t.get("messages"):
                msgs = t["messages"]
                if len(msgs) > msg_cap:
                    t = dict(t)
                    msgs = msgs[-msg_cap:]
                    t["messages"] = msgs
                    t["_truncated"] = True
                # Perf: the per-message `raw` payload (#1895) can be ~12 KB each.
                # Shipping it for 8 sessions × 80 msgs would bloat the shared
                # snapshot from ~170 KB to multiple MB. The raw toggle is a
                # local-dashboard feature; strip raw from the cloud snapshot and
                # let the cloud toggle degrade gracefully.
                t["messages"] = [
                    {k: v for k, v in m.items() if k != "raw"} if isinstance(m, dict) else m
                    for m in msgs
                ]
                out[sid] = t
        return out
    except Exception as _e:
        log.debug("transcripts snapshot build failed: %s", _e)
        return {}


def _build_memory_access(limit=200):
    """Memory access log for the cloud Memory tab (issue #1896).

    Built on the daemon's OWN store handle. Mirrors the OSS /api/memory-access
    endpoint by reusing routes.infra._extract_memory_accesses, so the cloud
    cm-cloud-memory-access interceptor can serve the same shape. Best-effort -> [].
    """
    try:
        from clawmetry import local_store as _ls
        import routes.infra as _inf
        store = _ls.get_store()
        if store is None:
            return []
        rows = store.query_events(limit=12000)
        return _inf._extract_memory_accesses(rows, limit=limit)
    except Exception as _e:
        log.debug("memory-access snapshot build failed: %s", _e)
        return []


def _build_traces(limit_traces=5, span_cap=100):
    """Trace list + capped per-trace details for the cloud Tracing tab (#1903).

    Built on the daemon's OWN store handle. Reuses routes.tracing helpers so the
    cloud cm-cloud-tracing interceptor serves the same shape as /api/traces and
    /api/trace/<id>. Per-trace spans are capped to bound the encrypted snapshot.
    Returns {"list": [...], "detail": {trace_id: {...}}}. Best-effort -> empty.
    """
    try:
        from clawmetry import local_store as _ls
        from clawmetry.config import hide_clawmetry_session
        import routes.tracing as _tr
        store = _ls.get_store()
        if store is None:
            return {"list": [], "detail": {}}
        rows = store.query_events(limit=14000)
        by_sid = {}
        for e in (rows or []):
            sid = (e.get("session_id") or "").strip()
            if not sid or hide_clawmetry_session(sid):
                continue
            by_sid.setdefault(sid, []).append(e)
        summaries = [_tr._summarize_trace(s, ev) for s, ev in by_sid.items()]
        summaries = [t for t in summaries if t["span_count"] > 0]
        summaries.sort(key=lambda t: (t.get("start_ms") or 0), reverse=True)
        summaries = summaries[:limit_traces]
        detail = {}
        for t in summaries:
            sid = t["trace_id"]
            spans, roots = _tr._build_spans(by_sid.get(sid, []))
            truncated = len(spans) > span_cap
            if truncated:
                spans = spans[:span_cap]
                ids = {s["span_id"] for s in spans}
                for s in spans:
                    if s["parent_span_id"] and s["parent_span_id"] not in ids:
                        s["parent_span_id"] = None
                roots = [s["span_id"] for s in spans if not s["parent_span_id"]]
            # Perf: drop the per-span free-text payload from the snapshot — it's
            # the bulk of the size. Cloud renders the waterfall/tree/graph from
            # the metadata; the full text is a local-dashboard detail.
            for s in spans:
                s.pop("detail", None)
            detail[sid] = {
                "trace_id": sid,
                "summary": t,
                "spans": spans,
                "root_span_ids": roots,
                "agent_graph": _tr._build_agent_graph(spans),
                "_truncated": truncated,
            }
        return {"list": summaries, "detail": detail}
    except Exception as _e:
        log.debug("traces snapshot build failed: %s", _e)
        return {"list": [], "detail": {}}


# ── Self-Evolve: delegate the review to OpenClaw itself ──────────────────────
# The cloud server has no model credential, and ClawMetry's gateway token is
# read-only (operator.read) — so neither can run the Self-Evolve LLM review.
# OpenClaw can: the daemon shells out to ``openclaw agent`` (a real, isolated
# session on OpenClaw's OWN credentials), parses the findings, and ships them
# in the snapshot. The session transcript also lands on disk -> DuckDB, so the
# whole thing flows local -> Redis -> cloud while ClawMetry stays read-only on
# the gateway (it only invokes OpenClaw's own owner-access CLI, never opens a
# write connection). Refresh is gated + backgrounded so we never re-bill on
# every heartbeat or block the snapshot loop.

_SE_SESSION_ID = "clawmetry-selfevolve"
_SE_REFRESH_SEC = 6 * 3600
_SE_LOCK = threading.Lock()
_SE_STATE = {"payload": None, "computed_at": 0.0, "running": False}


def _resolve_openclaw_bin():
    """Find the ``openclaw`` binary. The daemon runs under launchd with a
    minimal PATH, so ``shutil.which`` alone often misses Homebrew installs."""
    import shutil

    found = shutil.which("openclaw")
    if found:
        return found
    for cand in (
        "/opt/homebrew/bin/openclaw",
        "/usr/local/bin/openclaw",
        os.path.expanduser("~/.local/bin/openclaw"),
        "/usr/bin/openclaw",
    ):
        if os.path.isfile(cand) and os.access(cand, os.X_OK):
            return cand
    return None


def _selfevolve_build_context(workspace=None):
    """Compact telemetry context for the review, built on the daemon's OWN
    store handle (never a read-only re-open — that deadlocks the write lock).
    Best-effort -> {}."""
    ctx = {}
    try:
        ctx["models"] = _build_model_attribution()
    except Exception:
        pass
    try:
        ctx["diagnostics"] = _build_diagnostics(workspace)
    except Exception:
        pass
    try:
        from collections import Counter
        from clawmetry import local_store as _ls

        store = _ls.get_store()
        if store is not None:
            evs = store.query_events(limit=400)
            errs = [
                e
                for e in evs
                if str(e.get("status", "")).lower() in ("error", "failed")
                or e.get("is_error")
            ]
            type_counts = Counter(
                (e.get("event_type") or e.get("_v3_type") or "other") for e in evs
            )
            ctx["events_summary"] = {
                "recent_events": len(evs),
                "errors": len(errs),
                "by_type": dict(type_counts.most_common(12)),
            }
    except Exception:
        pass
    return ctx


def _selfevolve_compute_via_openclaw(ctx, timeout=200):
    """Run the Self-Evolve review by asking OpenClaw itself via ``openclaw
    agent``. ``ctx`` is the telemetry context built in the MAIN snapshot thread
    (DuckDB connections aren't thread-safe — building it here in the background
    thread races the snapshot thread and yields empty context -> the agent
    rightly returns ``insufficient``). Returns a payload matching
    ``/api/selfevolve/analyze`` or None."""
    try:
        import subprocess

        binp = _resolve_openclaw_bin()
        if not binp:
            return None
        import routes.selfevolve as _se

        ctx = ctx or {}
        # ``openclaw agent`` takes a single --message, so fold the JSON-shape
        # system instructions into the prompt body.
        message = (
            _se.SYSTEM_PROMPT
            + "\n\n=== Aggregated telemetry for this agent ===\n"
            + json.dumps(ctx, default=str, indent=2)[:6000]
            + "\n\nReturn ONLY the JSON described above. No preamble, no "
            "markdown fences."
        )
        # ``openclaw`` is a Node script; under the daemon's minimal launchd
        # PATH ``node`` isn't found (rc 127). Prepend the openclaw bin dir
        # (Homebrew puts ``node`` there too) plus the usual Node locations.
        env = dict(os.environ)
        node_dirs = [
            os.path.dirname(binp),
            "/opt/homebrew/bin",
            "/usr/local/bin",
            os.path.expanduser("~/.local/bin"),
        ]
        env["PATH"] = os.pathsep.join(
            node_dirs + [env.get("PATH", "/usr/bin:/bin")]
        )
        proc = subprocess.run(
            [
                binp,
                "agent",
                "--session-id",
                _SE_SESSION_ID,
                "--message",
                message,
                "--json",
                "--timeout",
                str(timeout),
            ],
            capture_output=True,
            text=True,
            timeout=timeout + 30,
            env=env,
        )
        if proc.returncode != 0:
            log.debug(
                "openclaw agent selfevolve rc=%s err=%s",
                proc.returncode,
                (proc.stderr or "")[:200],
            )
            return None
        out = json.loads(proc.stdout)
        result = out.get("result") or {}
        meta = result.get("meta") or {}
        raw = ""
        payloads = result.get("payloads") or []
        if payloads:
            raw = payloads[0].get("text") or ""
        if not raw:
            raw = meta.get("finalAssistantVisibleText") or ""
        findings, fmeta = _se._extract_findings(raw)
        return {
            "findings": findings,
            "insufficient": fmeta.get("insufficient", False),
            "reason": fmeta.get("reason", ""),
            "generated_at": int(time.time()),
            "model": (meta.get("systemPromptReport") or {}).get(
                "model", "openclaw-agent"
            ),
            "events_considered": (ctx.get("events_summary") or {}).get(
                "recent_events", 0
            ),
            "source": "openclaw-agent",
            "run_id": out.get("runId", ""),
            "session_id": _SE_SESSION_ID,
        }
    except Exception as _e:
        log.debug("selfevolve openclaw compute failed: %s", _e)
        return None


def _selfevolve_refresh_async(ctx):
    """Kick a background Self-Evolve run (at most one in flight). ``ctx`` is the
    telemetry context, pre-built in the caller's (main snapshot) thread."""

    def _run():
        payload = _selfevolve_compute_via_openclaw(ctx)
        with _SE_LOCK:
            _SE_STATE["running"] = False
            _SE_STATE["computed_at"] = time.time()
            # Only replace the cache with a result that actually has findings.
            # A transient empty/insufficient run (e.g. sparse context) must not
            # blow away a good prior payload.
            if payload and payload.get("findings"):
                _SE_STATE["payload"] = payload

    with _SE_LOCK:
        if _SE_STATE["running"]:
            return
        _SE_STATE["running"] = True
    threading.Thread(target=_run, daemon=True, name="selfevolve-refresh").start()


def _build_selfevolve(workspace=None):
    """Self-Evolve findings for the cloud Self-Evolve tab — computed by asking
    OpenClaw itself (see module note above). Best-effort -> {}."""
    try:
        with _SE_LOCK:
            payload = _SE_STATE["payload"]
            computed_at = _SE_STATE["computed_at"]
        # Cold start: fall back to whatever the local dashboard cached on disk
        # so the cloud renders immediately while the first fresh run is queued.
        if payload is None:
            try:
                import routes.selfevolve as _se

                payload = _se._load_cached()
            except Exception:
                payload = None
        can_run = bool(_resolve_openclaw_bin())
        # Self-Evolve no longer auto-runs on a timer. It spends Opus turns on a
        # schedule (the job repeatedly flagged itself for exactly that), and the
        # in-memory _SE_STATE meant every daemon restart reset the clock and
        # triggered an immediate run. It now runs ONLY on demand — the
        # Analyze/Re-analyze button (local: /api/selfevolve/analyze; cloud: the
        # `selfevolve_analyze` relay action). Opt back into the periodic refresh
        # with CLAWMETRY_SELFEVOLVE_AUTO=1 (interval CLAWMETRY_SELFEVOLVE_INTERVAL_SEC).
        _auto = os.environ.get("CLAWMETRY_SELFEVOLVE_AUTO", "").strip().lower() in ("1", "true", "yes", "on")
        if can_run and _auto and (time.time() - computed_at > _SE_REFRESH_SEC):
            # Build the context HERE, in the snapshot thread, before handing it
            # to the background runner — DuckDB connections aren't thread-safe,
            # so querying the store from the worker thread races this thread and
            # returns empty context (the agent then reports "insufficient").
            ctx = _selfevolve_build_context(workspace)
            _selfevolve_refresh_async(ctx)
        latest = payload or {"findings": [], "cached": False}
        status = {
            "available": bool(can_run or (payload and payload.get("findings"))),
            "auth_mode": "openclaw-agent",
            "has_cached": bool(payload and payload.get("findings")),
            "cached_at": (payload or {}).get("generated_at"),
            "setup_hint": None,
        }
        return {"status": status, "latest": latest}
    except Exception as _e:
        log.debug("selfevolve snapshot build failed: %s", _e)
        return {}


def _build_daily_usage(days=14):
    """14-day token/cost history for the cloud Cost tab.

    Sourced from DuckDB ``query_aggregates`` (events bucketed by their OWN ts =
    the correct historical truth). The cloud Cost tab previously rendered a
    today-collapsed approximation (all tokens looked like they happened today);
    shipping the real per-day rollup here -> snapshot -> Redis -> cloud fixes
    that. Shape matches ``/api/usage`` so the cloud just hands it to the
    existing renderer. Built on the daemon's OWN store handle. Best-effort
    -> {}."""
    try:
        from datetime import datetime, timedelta

        from clawmetry import local_store as _ls

        store = _ls.get_store()
        if store is None:
            return {}
        daily_tok: dict = {}
        daily_cost: dict = {}
        for r in (store.query_aggregates() or []):
            d = r.get("day") or ""
            if not d:
                continue
            daily_tok[d] = daily_tok.get(d, 0) + int(r.get("token_count") or 0)
            daily_cost[d] = daily_cost.get(d, 0.0) + float(r.get("cost_usd") or 0.0)
        di: dict = {}
        do: dict = {}
        dcr: dict = {}
        dcw: dict = {}
        try:
            for s in (store.query_daily_usage_splits() or []):
                d = s.get("day")
                if not d:
                    continue
                di[d] = int(s.get("input_tokens") or 0)
                do[d] = int(s.get("output_tokens") or 0)
                dcr[d] = int(s.get("cache_read_tokens") or 0)
                dcw[d] = int(s.get("cache_write_tokens") or 0)
                if daily_cost.get(d, 0.0) <= 0 and float(s.get("cost_usd") or 0) > 0:
                    daily_cost[d] = float(s.get("cost_usd"))
        except Exception:
            pass
        now = datetime.now()
        out_days = []
        for i in range(days - 1, -1, -1):
            ds = (now - timedelta(days=i)).strftime("%Y-%m-%d")
            out_days.append({
                "date": ds,
                "tokens": int(daily_tok.get(ds, 0)),
                "cost": round(float(daily_cost.get(ds, 0.0)), 6),
                "inputTokens": di.get(ds, 0),
                "outputTokens": do.get(ds, 0),
                "cacheReadTokens": dcr.get(ds, 0),
                "cacheWriteTokens": dcw.get(ds, 0),
            })
        tstr = now.strftime("%Y-%m-%d")
        wk = (now - timedelta(days=now.weekday())).strftime("%Y-%m-%d")
        mo = now.strftime("%Y-%m-01")
        return {
            "days": out_days,
            "today": int(daily_tok.get(tstr, 0)),
            "week": int(sum(v for k, v in daily_tok.items() if k >= wk)),
            "month": int(sum(v for k, v in daily_tok.items() if k >= mo)),
            "todayCost": round(float(daily_cost.get(tstr, 0.0)), 6),
            "weekCost": round(sum(v for k, v in daily_cost.items() if k >= wk), 6),
            "monthCost": round(sum(v for k, v in daily_cost.items() if k >= mo), 6),
        }
    except Exception as _e:
        log.debug("daily usage snapshot build failed: %s", _e)
        return {}


def _reliability_score_session(events):
    """ClawBench-style deterministic trace checks for ONE session.

    Returns (checks, signals). ``checks`` maps a check name to True/False/None
    (None = not applicable to this session). Walks the Claude-format message
    blocks (``data.message.content``) for tool_use / tool_result, plus
    ``model.completed.stopReason``. See PRD-cloud-pro-agent-reliability.md.
    """
    from collections import Counter

    tool_uses = []      # (name, input_signature)
    tool_results = 0
    tool_errors = 0
    bad_stop = 0
    completed = False
    for e in events:
        d = e.get("data") or {}
        et = (e.get("event_type") or "").lower()
        if et == "model.completed":
            completed = True
            sr = str(d.get("stopReason") or "").lower()
            if sr in ("error", "max_tokens", "content_filter", "refusal"):
                bad_stop += 1
        msg = d.get("message")
        if isinstance(msg, dict):
            content = msg.get("content")
            if isinstance(content, list):
                for b in content:
                    if not isinstance(b, dict):
                        continue
                    bt = b.get("type")
                    if bt == "tool_use":
                        nm = str(b.get("name") or "").lower()
                        try:
                            sig = json.dumps(b.get("input") or {}, sort_keys=True)[:160]
                        except Exception:
                            sig = ""
                        tool_uses.append((nm, sig))
                    elif bt == "tool_result":
                        tool_results += 1
                        if b.get("is_error"):
                            tool_errors += 1

    READ = {"read", "grep", "glob", "ls", "cat", "search", "web_search",
            "web_fetch", "memory_search"}
    WRITE = {"write", "edit", "multiedit", "str_replace", "str_replace_editor",
             "apply_patch"}
    names = [n for n, _ in tool_uses]
    errored = tool_errors > 0 or bad_stop > 0
    looped = any(c >= 4 for c in Counter(tool_uses).values())

    checks = {}
    # acted: the agent actually did work, not just talk.
    checks["acted"] = len(tool_uses) > 0
    # read_before_write: never wrote/edited before reading first.
    wrote = any(n in WRITE for n in names)
    if wrote:
        seen_read = False
        ok = True
        for n in names:
            if n in READ:
                seen_read = True
            if n in WRITE and not seen_read:
                ok = False
                break
        checks["read_before_write"] = ok
    else:
        checks["read_before_write"] = None
    # tool_success: tool calls returned without error.
    checks["tool_success"] = (tool_errors == 0) if tool_results > 0 else None
    # recovered: hit an error but still finished cleanly.
    checks["recovered"] = (completed and bad_stop == 0) if errored else None
    # no_loop: didn't repeat the same tool call 4+ times.
    checks["no_loop"] = (not looped)

    signals = {
        "tool_uses": len(tool_uses),
        "tool_results": tool_results,
        "tool_errors": tool_errors,
        "errored": errored,
        "looped": looped,
        "completed": completed,
    }
    return checks, signals


# Display weights for the aggregate Reliability Score (0-100).
_RELIABILITY_WEIGHTS = {
    "tool_success": 0.30,
    "recovered": 0.20,
    "read_before_write": 0.20,
    "no_loop": 0.20,
    "acted": 0.10,
}
# Human-readable failure-mode labels (the ClawBench-style taxonomy, P1 subset).
_RELIABILITY_FAILURE_LABELS = {
    "tool_success": "Tool calls errored",
    "recovered": "Errored without recovering",
    "read_before_write": "Wrote before reading",
    "no_loop": "Repeated the same action (loop)",
    "acted": "All talk, no action",
}


def _build_reliability(limit_sessions=25, min_sessions=4):
    """Agent Reliability score for the cloud Pro Reliability tab (P1).

    Deterministic, trace-based score over recent sessions — no LLM, cheap
    enough to run every snapshot. Built on the daemon's OWN store handle.
    Returns {score, grade, confidence, sessions_scored, checks[], taxonomy[]}.
    Best-effort -> {}.  See PRD-cloud-pro-agent-reliability.md (P1).
    """
    try:
        from clawmetry import local_store as _ls

        store = _ls.get_store()
        if store is None:
            return {}
        evs = store.query_events(limit=8000)  # DESC by ts
        if not evs:
            return {}
        # Group most-recent sessions (skip the ClawMetry helper sessions so we
        # score the user's real agent, not our own selfevolve/probe runs).
        order = []
        by_sid = {}
        for e in evs:
            sid = (e.get("session_id") or "").strip()
            if not sid or sid.startswith("clawmetry-"):
                continue
            if sid not in by_sid:
                by_sid[sid] = []
                order.append(sid)
            by_sid[sid].append(e)
            if len(order) > limit_sessions and sid not in order[:limit_sessions]:
                pass
        sids = order[:limit_sessions]

        # pass/applicable tallies per check + per-check failing-session count.
        passes = {k: 0 for k in _RELIABILITY_WEIGHTS}
        applic = {k: 0 for k in _RELIABILITY_WEIGHTS}
        fails = {k: 0 for k in _RELIABILITY_WEIGHTS}
        scored = 0
        for sid in sids:
            sess = list(reversed(by_sid[sid]))  # chronological
            checks, _sig = _reliability_score_session(sess)
            # Only count a session that did SOMETHING (has tool activity or a
            # completion) so empty/queue-only sessions don't dilute the score.
            if not (checks.get("acted") or _sig.get("completed")):
                continue
            scored += 1
            for k in _RELIABILITY_WEIGHTS:
                v = checks.get(k)
                if v is None:
                    continue
                applic[k] += 1
                if v:
                    passes[k] += 1
                else:
                    fails[k] += 1

        if scored == 0:
            return {
                "score": None,
                "grade": "—",
                "confidence": "no_data",
                "sessions_scored": 0,
                "checks": [],
                "taxonomy": [],
            }

        # Weighted score across checks that were applicable at least once.
        num = 0.0
        den = 0.0
        checks_out = []
        for k, w in _RELIABILITY_WEIGHTS.items():
            if applic[k] == 0:
                continue
            rate = passes[k] / applic[k]
            num += w * rate
            den += w
            checks_out.append({
                "key": k,
                "label": _RELIABILITY_FAILURE_LABELS.get(k, k),
                "pass_pct": round(rate * 100, 1),
                "applicable": applic[k],
            })
        score = round((num / den) * 100) if den > 0 else None

        def _grade(s):
            if s is None:
                return "—"
            return ("A" if s >= 90 else "B" if s >= 80 else "C" if s >= 70
                    else "D" if s >= 60 else "F")

        taxonomy = sorted(
            [
                {"key": k, "label": _RELIABILITY_FAILURE_LABELS[k], "count": c}
                for k, c in fails.items() if c > 0
            ],
            key=lambda x: -x["count"],
        )
        return {
            "score": score,
            "grade": _grade(score),
            # Honest about seed noise: a handful of sessions can't be trusted.
            "confidence": "low" if scored < min_sessions else "ok",
            "sessions_scored": scored,
            "checks": checks_out,
            "taxonomy": taxonomy,
        }
    except Exception as _e:
        log.debug("reliability snapshot build failed: %s", _e)
        return {}


def _build_memory_files(workspace):
    """Build memory file list for the Memory popup."""
    if not workspace or not os.path.isdir(workspace):
        return []
    files = []
    for name in [
        "MEMORY.md",
        "SOUL.md",
        "IDENTITY.md",
        "USER.md",
        "AGENTS.md",
        "TOOLS.md",
        "HEARTBEAT.md",
    ]:
        fpath = os.path.join(workspace, name)
        if os.path.isfile(fpath):
            try:
                st = os.stat(fpath)
                files.append(
                    {"name": name, "size": st.st_size, "modified": st.st_mtime}
                )
            except Exception:
                pass
    mem_dir = os.path.join(workspace, "memory")
    if os.path.isdir(mem_dir):
        for f in sorted(os.listdir(mem_dir)):
            if f.endswith(".md"):
                fpath = os.path.join(mem_dir, f)
                try:
                    st = os.stat(fpath)
                    files.append(
                        {
                            "name": f"memory/{f}",
                            "size": st.st_size,
                            "modified": st.st_mtime,
                        }
                    )
                except Exception:
                    pass
    return files


def _build_brain_data():
    """Build LLM call data for the Brain/AI Model popup."""
    try:
        import collections

        home = str(Path.home())
        session_dir = os.path.join(_get_openclaw_dir(), "agents", "main", "sessions")
        if not os.path.isdir(session_dir):
            return {"stats": {}, "calls": []}

        calls = []
        total_cost = 0.0
        total_tokens_in = 0
        total_tokens_out = 0
        total_cache_read = 0
        total_cache_write = 0
        total_duration = 0
        thinking_calls = 0
        cache_hit_calls = 0
        model_name = "unknown"

        today = datetime.now().strftime("%Y-%m-%d")

        files = sorted(
            glob.glob(os.path.join(session_dir, "*.jsonl")),
            key=os.path.getmtime,
            reverse=True,
        )[:20]

        for fp in files:
            try:
                session_name = os.path.basename(fp).split(".")[0][:12]
                prev_user_ts = None  # for duration calculation
                for line_raw in open(fp, errors="ignore"):
                    try:
                        ev = json.loads(line_raw)

                        # Track user message timestamps for duration calc
                        if ev.get("type") == "message":
                            msg_role = (ev.get("message") or {}).get("role", "")
                            if msg_role == "user":
                                prev_user_ts = ev.get("timestamp")

                        if ev.get("type") != "message":
                            continue
                        msg = ev.get("message", {})
                        role = msg.get("role", "")
                        if role != "assistant":
                            continue

                        usage = msg.get("usage") or ev.get("usage") or {}
                        if not usage:
                            continue

                        ts = ev.get("timestamp", "")
                        if not ts or today not in ts[:10]:
                            continue

                        # OpenClaw JSONL format uses: input/output/cacheRead/cacheWrite/cost.total
                        tok_in = (
                            usage.get("input")
                            or usage.get("inputTokens")
                            or usage.get("input_tokens")
                            or 0
                        )
                        tok_out = (
                            usage.get("output")
                            or usage.get("outputTokens")
                            or usage.get("output_tokens")
                            or 0
                        )
                        cr = (
                            usage.get("cacheRead")
                            or usage.get("cacheReadInputTokens")
                            or usage.get("cache_read_input_tokens")
                            or 0
                        )
                        cw = (
                            usage.get("cacheWrite")
                            or usage.get("cacheCreationInputTokens")
                            or usage.get("cache_creation_input_tokens")
                            or 0
                        )

                        # Use actual cost from usage.cost.total if available, else estimate
                        cost_obj = usage.get("cost", {})
                        if isinstance(cost_obj, dict) and cost_obj.get("total"):
                            cost = float(cost_obj["total"])
                        else:
                            cost = (
                                tok_in * 3 + tok_out * 15 + cr * 0.3 + cw * 3.75
                            ) / 1_000_000

                        # Duration: compute from prev user msg timestamp (durationMs rarely stored)
                        dur_ms = int(
                            ev.get("durationMs", 0) or ev.get("duration_ms", 0) or 0
                        )
                        if not dur_ms and prev_user_ts and ts:
                            try:
                                from datetime import timezone

                                t1 = datetime.fromisoformat(
                                    prev_user_ts.replace("Z", "+00:00")
                                )
                                t2 = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                                d = int((t2 - t1).total_seconds() * 1000)
                                if 0 < d < 300000:
                                    dur_ms = d
                            except Exception:
                                pass

                        has_thinking = False
                        tools_used = []
                        if isinstance(msg.get("content"), list):
                            for c in msg["content"]:
                                if c.get("type") == "thinking":
                                    has_thinking = True
                                elif c.get("type") == "toolCall":
                                    tn = c.get("name", "")
                                    if tn and tn not in tools_used:
                                        tools_used.append(tn)

                        m = msg.get("model") or ev.get("model") or ""
                        if m and m != "unknown":
                            model_name = m.split("/")[-1] if "/" in m else m

                        total_tokens_in += tok_in
                        total_tokens_out += tok_out
                        total_cache_read += cr
                        total_cache_write += cw
                        total_cost += cost
                        total_duration += dur_ms
                        if has_thinking:
                            thinking_calls += 1
                        if cr > 0:
                            cache_hit_calls += 1

                        calls.append(
                            {
                                "timestamp": ts,
                                "session": session_name,
                                "tokens_in": tok_in,
                                "tokens_out": tok_out,
                                "cost": "$" + format(cost, ".4f"),
                                "duration_ms": dur_ms,
                                "thinking": has_thinking,
                                "cache_read": cr,
                                "tools_used": tools_used[:5],
                            }
                        )
                    except Exception:
                        continue
            except Exception:
                continue

        calls.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        calls = calls[:100]

        n = len(calls)
        avg_ms = int(total_duration / n) if n > 0 else 0

        stats = {
            "model": model_name,
            "today_calls": n,
            "today_cost": "$" + format(total_cost, ".2f"),
            "avg_response_ms": avg_ms,
            "thinking_calls": thinking_calls,
            "cache_hits": cache_hit_calls,
            "today_tokens": {
                "input": total_tokens_in,
                "output": total_tokens_out,
                "cache_read": total_cache_read,
                "cache_write": total_cache_write,
            },
        }

        return {"stats": stats, "calls": calls, "total": n}
    except Exception as e:
        log.warning(f"Brain data error: {e}")
        return {"stats": {}, "calls": [], "total": 0}


def _build_tool_stats():
    """Build tool usage stats from recent session logs."""
    try:
        import collections, glob

        home = str(Path.home())
        session_dir = os.path.join(_get_openclaw_dir(), "agents", "main", "sessions")
        if not os.path.isdir(session_dir):
            return {}

        tool_counts = collections.Counter()
        tool_recent = {}  # tool_name -> last few entries
        channel_msgs = collections.defaultdict(
            lambda: {"in": 0, "out": 0, "messages": []}
        )

        today = datetime.now().strftime("%Y-%m-%d")

        # Read last 20 active sessions
        files = sorted(
            glob.glob(os.path.join(session_dir, "*.jsonl")),
            key=os.path.getmtime,
            reverse=True,
        )[:20]

        # Pre-load session-level channel info from sessions.json
        _session_channels = {}
        _sessions_json = os.path.join(session_dir, "sessions.json")
        try:
            with open(_sessions_json) as _sjf:
                _sj = json.load(_sjf)
            for _sk, _sv in _sj.items():
                _sf = os.path.basename(_sv.get("sessionFile", ""))
                _dc = _sv.get("deliveryContext", {}) or {}
                _ori = _sv.get("origin", {}) or {}
                _ch = (
                    _dc.get("channel", "")
                    or _ori.get("provider", "")
                    or _ori.get("surface", "")
                )
                if _sf and _ch:
                    _session_channels[_sf] = _ch
        except Exception:
            pass

        for fp in files:
            _file_channel = _session_channels.get(os.path.basename(fp), "")
            try:
                for line in open(fp, errors="ignore"):
                    try:
                        ev = json.loads(line)
                        if ev.get("type") != "message":
                            continue
                        msg = ev.get("message", {})
                        ts = ev.get("timestamp", "")
                        role = msg.get("role", "")

                        if isinstance(msg.get("content"), list):
                            for c in msg["content"]:
                                if c.get("type") == "toolCall":
                                    name = c.get("name", "?")
                                    tool_counts[name] += 1
                                    args = (
                                        c.get("arguments", {})
                                        or c.get("input", {})
                                        or c.get("args", {})
                                        or {}
                                    )
                                    if isinstance(args, str):
                                        try:
                                            args = json.loads(args)
                                        except:
                                            args = {}

                                    # Track recent entries for specific tools
                                    if name == "web_search":
                                        q = args.get("query", "")
                                        if q and name not in tool_recent:
                                            tool_recent[name] = []
                                        if q:
                                            tool_recent.setdefault(name, []).append(
                                                {"query": q[:200], "ts": ts}
                                            )
                                    elif name == "web_fetch":
                                        url = args.get("url", "")
                                        if url:
                                            tool_recent.setdefault(name, []).append(
                                                {"url": url[:200], "ts": ts}
                                            )
                                    elif name == "browser":
                                        action = args.get("action", "")
                                        url = args.get("url", "")
                                        tool_recent.setdefault(name, []).append(
                                            {
                                                "action": action,
                                                "url": url[:200] if url else "",
                                                "ts": ts,
                                            }
                                        )
                                    elif name == "exec":
                                        cmd = args.get("command", "")
                                        if cmd:
                                            tool_recent.setdefault(name, []).append(
                                                {"command": cmd[:300], "ts": ts}
                                            )
                                    elif name == "message":
                                        target = args.get("target", "") or args.get(
                                            "channel", ""
                                        )
                                        tool_recent.setdefault(name, []).append(
                                            {"target": target, "ts": ts}
                                        )

                        # Track channel messages (inbound + outbound)
                        if role in ("user", "assistant"):
                            text = ""
                            if isinstance(msg.get("content"), str):
                                text = msg["content"][:300]
                            elif isinstance(msg.get("content"), list):
                                for c in msg["content"]:
                                    if c.get("type") == "text":
                                        text = c.get("text", "")[:300]
                                        break

                            # Try to detect channel from metadata, fall back to session-level channel
                            meta = ev.get("metadata", {}) or {}
                            channel = (
                                meta.get("channel", "")
                                or meta.get("surface", "")
                                or _file_channel
                            )
                            if channel and text:
                                direction = "in" if role == "user" else "out"
                                channel_msgs[channel][direction] += 1
                                channel_msgs[channel]["messages"].append(
                                    {
                                        "direction": direction,
                                        "content": text[:200],
                                        "timestamp": ts,
                                        "sender": meta.get("sender", "User")
                                        if role == "user"
                                        else "Agent",
                                    }
                                )
                    except Exception:
                        continue
            except Exception:
                continue

        # Cap recent entries
        for name in tool_recent:
            tool_recent[name] = tool_recent[name][-30:]
            tool_recent[name].reverse()

        for ch in channel_msgs:
            channel_msgs[ch]["messages"] = channel_msgs[ch]["messages"][-30:]
            channel_msgs[ch]["messages"].reverse()

        return {
            "counts": dict(tool_counts.most_common(30)),
            "recent": {k: v for k, v in tool_recent.items()},
            "channelMsgs": dict(channel_msgs),
        }
    except Exception as e:
        log.warning(f"Tool stats error: {e}")
        return {}


def _build_channel_list(config):
    """Build list of configured channels."""
    try:
        str(Path.home())
        oc_config = os.path.join(_get_openclaw_dir(), "openclaw.json")
        if not os.path.isfile(oc_config):
            return []
        data = json.load(open(oc_config))
        channels = []
        ch_section = data.get("channels", {})
        if isinstance(ch_section, dict):
            for key in ch_section:
                channels.append({"name": key, "enabled": True})
        # Also check top-level channel keys
        for key in (
            "telegram",
            "discord",
            "slack",
            "whatsapp",
            "signal",
            "irc",
            "webchat",
            "imessage",
        ):
            if key in data and key not in [c["name"] for c in channels]:
                cfg = data[key]
                if isinstance(cfg, dict):
                    channels.append({"name": key, "enabled": cfg.get("enabled", True)})
        return channels
    except Exception:
        return []


def _build_channel_data(config):
    """Build channel message data from gateway.log (outgoing) + session files (incoming)."""
    import re as _re

    try:
        str(Path.home())
        today = datetime.now().strftime("%Y-%m-%d")
        gw_log = os.path.join(_get_openclaw_dir(), "logs", "gateway.log")
        session_dir = os.path.join(_get_openclaw_dir(), "agents", "main", "sessions")
        channels = {}

        known_channels = {
            "telegram",
            "imessage",
            "whatsapp",
            "signal",
            "discord",
            "slack",
            "webchat",
            "irc",
            "googlechat",
            "msteams",
        }

        # ── Outgoing: parse gateway.log ──────────────────────────────────────
        if os.path.exists(gw_log):
            with open(gw_log, errors="ignore") as f:
                for raw in f:
                    raw = raw.strip()
                    if not raw:
                        continue
                    ts_match = _re.match(r"(\d{4}-\d{2}-\d{2}T[\d:.]+Z)", raw)
                    if not ts_match or today not in ts_match.group(1):
                        continue
                    ts = ts_match.group(1)
                    ch_match = _re.search(r"\[(\w+)\]", raw)
                    if not ch_match:
                        continue
                    ch_name = ch_match.group(1).lower()
                    if ch_name not in known_channels:
                        continue
                    if ch_name not in channels:
                        channels[ch_name] = {
                            "messages": [],
                            "todayIn": 0,
                            "todayOut": 0,
                            "total": 0,
                        }
                    rest = raw[ts_match.end() :].strip()
                    if any(
                        x in rest
                        for x in (
                            "sendMessage ok",
                            "send ok",
                            "delivered",
                            "sendPhoto ok",
                            "sendAudio ok",
                            "sendDocument ok",
                        )
                    ):
                        channels[ch_name]["todayOut"] += 1
                        channels[ch_name]["total"] += 1
                        channels[ch_name]["messages"].append(
                            {
                                "direction": "out",
                                "content": "",
                                "timestamp": ts,
                                "sender": "Diya",
                            }
                        )

        # ── Incoming: parse session JSONL files ──────────────────────────────
        # Telegram sessions contain "message_id" in first user message
        # iMessage sessions contain media paths or iMessage-specific metadata
        if os.path.isdir(session_dir):
            for fname in sorted(os.listdir(session_dir)):
                if not fname.endswith(".jsonl"):
                    continue
                fpath = os.path.join(session_dir, fname)
                try:
                    mtime = datetime.fromtimestamp(os.path.getmtime(fpath)).strftime(
                        "%Y-%m-%d"
                    )
                    if mtime != today:
                        continue
                    detected_ch = None
                    first_user_ts = None
                    first_user_text = ""
                    with open(fpath, errors="ignore") as f2:
                        for line in f2:
                            try:
                                obj = json.loads(line)
                                if (
                                    obj.get("type") == "message"
                                    and obj.get("message", {}).get("role") == "user"
                                ):
                                    content = obj["message"].get("content", "")
                                    text = (
                                        content
                                        if isinstance(content, str)
                                        else " ".join(
                                            c.get("text", "")
                                            for c in content
                                            if isinstance(c, dict)
                                        )
                                    )
                                    if "message_id" in text and "sender_id" in text:
                                        if "imessage" in text.lower() or "+" in text:
                                            detected_ch = "imessage"
                                        else:
                                            detected_ch = "telegram"
                                        first_user_ts = obj.get("timestamp", "")
                                        first_user_text = text[:100]
                                    break
                            except Exception:
                                continue
                    if detected_ch and first_user_ts:
                        if detected_ch not in channels:
                            channels[detected_ch] = {
                                "messages": [],
                                "todayIn": 0,
                                "todayOut": 0,
                                "total": 0,
                            }
                        channels[detected_ch]["todayIn"] += 1
                        channels[detected_ch]["total"] += 1
                        channels[detected_ch]["messages"].append(
                            {
                                "direction": "in",
                                "content": first_user_text,
                                "timestamp": first_user_ts,
                                "sender": "User",
                            }
                        )
                except Exception:
                    continue

        # Cap and reverse (newest first)
        for ch in channels.values():
            ch["messages"] = ch["messages"][-50:]
            ch["messages"].sort(key=lambda x: x.get("timestamp", ""), reverse=True)

        return channels
    except Exception as e:
        log.warning(f"Channel data error: {e}")
        return {}


def _build_cron_jobs(paths):
    """Build cron jobs list for snapshot."""
    import json as _j2

    home = str(Path.home())
    cron_candidates = [
        os.path.join(_get_openclaw_dir(), "cron", "jobs.json"),
        os.path.join(_get_openclaw_dir(), "agents", "main", "cron", "jobs.json"),
    ]
    cron_file = next((p for p in cron_candidates if os.path.isfile(p)), None)
    if not cron_file:
        return []
    try:
        data = _j2.load(open(cron_file))
        jobs = data.get("jobs", []) if isinstance(data, dict) else data
        result = []
        for j in jobs:
            sched = j.get("schedule", {})
            kind = sched.get("kind", "")
            expr = (
                sched.get("interval", "")
                if kind == "interval"
                else (
                    f"at {sched.get('at', '')}"
                    if kind == "at"
                    else sched.get("cron", "")
                    if kind == "cron"
                    else ""
                )
            )
            sched_obj = j.get("schedule", {})
            result.append(
                {
                    "id": j.get("id", ""),
                    "name": j.get("name", ""),
                    "enabled": j.get("enabled", True),
                    "schedule": sched_obj,
                    "task": j.get("task", "")[:200],
                    "state": j.get("state", {}),
                    "lastRun": None,
                    "lastStatus": None,
                }
            )
        return result
    except Exception:
        return []


def sync_system_snapshot(config: dict, state: dict, paths: dict) -> int:
    """Push system info + subagent data as encrypted snapshot.

    Skipped when sync is paused (expired trial)."""
    if not _sync_allowed():
        return 0
    import subprocess, platform, json as _json

    api_key = config["api_key"]
    enc_key = config.get("encryption_key")
    node_id = config["node_id"]
    if not enc_key:
        return 0

    # System info
    system = []
    try:
        disk = (
            subprocess.run(["df", "-h", "/"], capture_output=True, text=True, timeout=5)
            .stdout.strip()
            .split("\n")[-1]
            .split()
        )
        disk_pct = int(disk[4].replace("%", "")) if len(disk) > 4 else 0
        disk_color = (
            "green" if disk_pct < 80 else ("yellow" if disk_pct < 90 else "red")
        )
        system.append(["Disk /", f"{disk[2]} / {disk[1]} ({disk[4]})", disk_color])
    except Exception:
        system.append(["Disk /", "--", ""])
    # Check for additional data drives
    for extra_mount in ["/mnt/data-drive", "/data", "/mnt/data", "/home"]:
        try:
            ed = (
                subprocess.run(
                    ["df", "-h", extra_mount], capture_output=True, text=True, timeout=3
                )
                .stdout.strip()
                .split("\n")[-1]
                .split()
            )
            if len(ed) > 4 and ed[5] != "/":
                ep = int(ed[4].replace("%", ""))
                ec = "green" if ep < 80 else ("yellow" if ep < 90 else "red")
                system.append([f"Disk {ed[5]}", f"{ed[2]} / {ed[1]} ({ed[4]})", ec])
        except Exception:
            pass

    try:
        if sys.platform == "darwin":
            import re as _re

            vm = subprocess.run(
                ["vm_stat"], capture_output=True, text=True, timeout=5
            ).stdout
            pages = {
                m.group(1): int(m.group(2))
                for m in _re.finditer(r'"(.+?)"\s*:\s*(\d+)', vm)
            }
            page_size = 16384
            used = (
                pages.get("Pages active", 0) + pages.get("Pages wired down", 0)
            ) * page_size
            total_raw = subprocess.run(
                ["sysctl", "-n", "hw.memsize"],
                capture_output=True,
                text=True,
                timeout=5,
            ).stdout.strip()
            total = int(total_raw) if total_raw else 0
            system.append(["RAM", f"{used // (1024**3)}G / {total // (1024**3)}G", ""])
        else:
            mem = (
                subprocess.run(
                    ["free", "-h"], capture_output=True, text=True, timeout=5
                )
                .stdout.strip()
                .split("\n")[1]
                .split()
            )
            system.append(["RAM", f"{mem[2]} / {mem[1]}", ""])
    except Exception:
        system.append(["RAM", "--", ""])

    # Portable uptime: stdlib-only (no `uptime -p` — missing on macOS/BSD).
    try:
        boot_ts = None
        try:
            import psutil  # type: ignore

            boot_ts = float(psutil.boot_time())
        except Exception:
            if sys.platform.startswith("linux"):
                try:
                    with open("/proc/uptime") as _uf:
                        boot_ts = time.time() - float(_uf.read().split()[0])
                except Exception:
                    pass
            elif sys.platform == "darwin" or "bsd" in sys.platform:
                try:
                    import re as _re

                    _out = subprocess.run(
                        ["sysctl", "-n", "kern.boottime"],
                        capture_output=True,
                        text=True,
                        timeout=2,
                    ).stdout
                    _m = _re.search(r"sec\s*=\s*(\d+)", _out)
                    if _m:
                        boot_ts = float(_m.group(1))
                except Exception:
                    pass
        if boot_ts is not None:
            secs = max(0, int(time.time() - boot_ts))
            days, rem = divmod(secs, 86400)
            hours, rem = divmod(rem, 3600)
            minutes = rem // 60
            parts = []
            if days:
                parts.append(f"{days}d")
            if hours:
                parts.append(f"{hours}h")
            if minutes or not parts:
                parts.append(f"{minutes}m")
            system.append(["Uptime", " ".join(parts), ""])
        else:
            system.append(["Uptime", "--", ""])
    except Exception:
        system.append(["Uptime", "--", ""])

    # Gateway status
    try:
        gw = subprocess.run(
            ["pgrep", "-f", "openclaw"], capture_output=True, text=True, timeout=5
        )
        gw_running = gw.returncode == 0
        system.append(
            [
                "Gateway",
                "Running" if gw_running else "Stopped",
                "green" if gw_running else "red",
            ]
        )
    except Exception:
        system.append(["Gateway", "--", ""])

    # Infra
    uname = platform.uname()
    infra = {
        "machine": uname.node,
        "runtime": f"Node.js - {uname.system} {uname.release.split('-')[0]}",
        "storage": system[0][1] if system else "--",
    }

    # Session info
    sessions_dir = paths.get("sessions_dir", "")
    session_count = 0
    model_name = ""
    main_tokens = 0
    subagents_list = []
    active_count = 0

    index_path = os.path.join(sessions_dir, "sessions.json") if sessions_dir else ""
    if index_path and os.path.isfile(index_path):
        try:
            with open(index_path) as f:
                index = _json.load(f)
            now_ms = time.time() * 1000
            from clawmetry.config import hide_clawmetry_session
            for key, meta in index.items():
                if not isinstance(meta, dict):
                    continue
                # Skip ClawMetry's own helper sessions (clawmetry-*) so they
                # don't inflate counts/tokens or surface as activity in cloud.
                if hide_clawmetry_session(key.split(":")[-1]) or "clawmetry-" in key:
                    continue
                session_count += 1
                if ":subagent:" in key:
                    age_ms = now_ms - meta.get("updatedAt", 0)
                    status = (
                        "active"
                        if age_ms < 120000
                        else ("idle" if age_ms < 3600000 else "stale")
                    )
                    if status == "active":
                        active_count += 1
                    subagents_list.append(
                        {
                            "label": meta.get("label", key.split(":")[-1][:12]),
                            "status": status,
                            "model": meta.get("model", ""),
                            "task": meta.get("task", "")[:100],
                            "tokens": meta.get("totalTokens", 0),
                            "sessionId": key.split(":")[-1],
                            "key": key,
                            # sessionFile basename lets the cloud map file-UUID → subagent-UUID
                            # for brain blobs that were synced before subagent_id was added.
                            "sessionFile": os.path.basename(
                                meta.get("sessionFile", "")
                            ),
                            "displayName": meta.get(
                                "label", meta.get("task", key.split(":")[-1][:12])
                            )[:80],
                            "updatedAt": meta.get("updatedAt", 0),
                            "runtimeMs": int(
                                now_ms
                                - meta.get("createdAt", meta.get("updatedAt", now_ms))
                            ),
                        }
                    )
                elif "subagent" not in key:
                    if not model_name:
                        model_name = meta.get("model", "")
                    main_tokens = max(main_tokens, meta.get("totalTokens", 0))
        except Exception as e:
            log.debug(f"Session index read error: {e}")

    # jsonl -> DuckDB -> snapshot. Write each sub-agent into the local store,
    # then read them BACK from DuckDB so the cloud snapshot and the OSS
    # /api/subagents fast path share ONE source (query_subagents). Previously
    # the snapshot shipped the filesystem-built list directly, bypassing
    # DuckDB — the data path is now jsonl -> duckdb -> redis -> cloud,
    # identical in OSS and cloud.
    try:
        from clawmetry import local_store as _ls_sa

        _sa_store = _ls_sa.get_store()
        for _sa in subagents_list:
            _sid = _sa.get("sessionId") or _sa.get("key")
            if not _sid:
                continue
            _sa_store.ingest_subagent(
                {
                    "subagent_id": _sid,
                    "agent_type": "openclaw",
                    "task": _sa.get("task", ""),
                    "status": _sa.get("status", ""),
                    "token_count": _sa.get("tokens", 0),
                    "model": _sa.get("model", ""),
                    "label": _sa.get("label", ""),
                    "displayName": _sa.get("displayName", ""),
                    "session_file": _sa.get("sessionFile", ""),
                    "updated_at_ms": _sa.get("updatedAt", 0),
                    "runtime_ms": _sa.get("runtimeMs", 0),
                }
            )
    except Exception as _e:
        log.debug("local_store: subagent ingest failed: %s", _e)
    try:
        import routes.sessions as _sa_routes
        from clawmetry import local_store as _ls_rb

        # Pass rows from the daemon's OWN store handle — the cross-process
        # _ls_call proxy is unreliable when called from inside the daemon.
        _duck_rows = _ls_rb.get_store().query_subagents(limit=500)
        _duck = _sa_routes._try_local_store_subagents(_rows=_duck_rows)
        if _duck and isinstance(_duck.get("subagents"), list):
            # Keep the filesystem list only if the DuckDB read came back empty
            # while the FS had rows (defensive — never blank a live workforce).
            if _duck["subagents"] or not subagents_list:
                subagents_list = _duck["subagents"]
                _dc = _duck.get("counts") or {}
                active_count = _dc.get("active", active_count)
    except Exception as _e:
        log.debug("subagents read-back from DuckDB failed: %s", _e)

    # Crons
    cron_enabled = 0
    cron_disabled = 0
    try:
        os.path.expanduser("~")
        cron_candidates = [
            os.path.join(_get_openclaw_dir(), "cron", "jobs.json"),
            os.path.join(_get_openclaw_dir(), "agents", "main", "cron", "jobs.json"),
            os.path.join(paths.get("workspace", ""), "..", "crons.json"),
        ]
        cron_path = next((p for p in cron_candidates if os.path.isfile(p)), None)
        if cron_path:
            cron_data = _json.load(open(cron_path))
            crons = (
                cron_data.get("jobs", cron_data)
                if isinstance(cron_data, dict)
                else cron_data
            )
            if isinstance(crons, list):
                for c in crons:
                    if c.get("enabled", True):
                        cron_enabled += 1
                    else:
                        cron_disabled += 1
    except Exception:
        pass

    # Memory files
    _mem_files = _build_memory_files(paths.get("workspace", ""))

    # Spending (from state if available)
    spending = state.get("spending", {"today": 0, "week": 0, "month": 0})

    payload = {
        "system": system,
        "infra": infra,
        "model": model_name or "unknown",
        "provider": "",
        "sessionCount": session_count,
        "mainTokens": main_tokens,
        "contextWindow": 200000,
        "cronCount": cron_enabled + cron_disabled,
        "cronEnabled": cron_enabled,
        "cronDisabled": cron_disabled,
        "memoryCount": len(_mem_files),
        "memorySize": sum(f.get("size", 0) for f in _mem_files),
        "memoryFiles": _mem_files,
        "subagents": subagents_list,
        "subagentCounts": {
            "active": active_count,
            "idle": len([s for s in subagents_list if s["status"] == "idle"]),
            "stale": len([s for s in subagents_list if s["status"] == "stale"]),
            "total": len(subagents_list),
        },
        "totalActive": active_count,
        "spending": spending,
        "cronJobs": _build_cron_jobs(paths),
        "channels": _build_channel_data(config),
        "toolStats": _build_tool_stats(),
        "brainData": _build_brain_data(),
        "gateway": {},
        "runtimeInfo": _build_runtime_info(),
        "machineInfo": _build_machine_info(),
        "channelList": _build_channel_list(config),
        "ollamaInfo": _detect_ollama_for_heartbeat(),
        "diagnostics": _build_diagnostics(paths.get("workspace")),
        "modelAttribution": _build_model_attribution(),
        "transcripts": _build_transcripts(
            extra_sids=[
                s["sessionId"]
                for s in subagents_list
                if s.get("status") in ("active", "idle") and s.get("sessionId")
            ]
        ),
        "selfEvolve": _build_selfevolve(paths.get("workspace")),
        "dailyUsage": _build_daily_usage(),
        "reliability": _build_reliability(),
        "memoryAccess": _build_memory_access(),
        "traces": _build_traces(),
    }

    # ── NemoClaw / sandbox enrichment ────────────────────────────────────────
    # Detect NemoClaw and add optional sandbox metadata to the snapshot.
    # The cloud stores this as generic key-value metadata — no NemoClaw-
    # specific UI logic lives in the dashboard.
    nemo = _detect_nemoclaw()
    if nemo.get("detected"):
        sandbox_meta = {
            "sandbox.name": nemo.get("sandbox_name", ""),
            "sandbox.status": nemo.get("sandbox_status", "unknown"),
            "sandbox.type": nemo.get("sandbox_type", "nemoclaw"),
            "inference.provider": nemo.get("inference_provider", ""),
            "inference.model": nemo.get("inference_model", ""),
            "security.sandbox_enabled": nemo.get("security_sandbox_enabled", True),
            "security.network_policy": nemo.get("security_network_policy", True),
        }
        payload["sandbox"] = sandbox_meta
        log.info(
            f"NemoClaw detected: sandbox={nemo.get('sandbox_name')} status={nemo.get('sandbox_status')}"
        )
    elif _is_running_in_container():
        # Generic container (Docker without NemoClaw) — still tag it
        payload["sandbox"] = {
            "sandbox.name": "",
            "sandbox.status": "running",
            "sandbox.type": "docker",
            "security.sandbox_enabled": True,
            "security.network_policy": False,
        }

    # Propagate container_id + runtime tag from path detection (set by _detect_docker_openclaw)
    docker_meta = _detect_docker_openclaw() if not nemo.get("detected") else {}
    if docker_meta.get("container_id") or docker_meta.get("runtime"):
        payload.setdefault("sandbox", {})
        if docker_meta.get("container_id"):
            payload["sandbox"]["container_id"] = docker_meta["container_id"]
        if docker_meta.get("runtime"):
            payload["sandbox"]["runtime"] = docker_meta["runtime"]
    elif nemo.get("detected"):
        payload.setdefault("sandbox", {})
        payload["sandbox"]["runtime"] = "nemoclaw"

    log.info(
        f"System snapshot: {len(subagents_list)} subagents ({active_count} active)"
    )

    # Local-store write-through (epic #964 / DuckDB MOAT). The dashboard
    # reads system + subagent state from these tables — without this
    # write, /api/local/system-snapshot + /api/local/subagents return
    # empty even though the cloud has the data. Failures non-fatal:
    # cloud sync still proceeds.
    try:
        from clawmetry import local_store as _ls
        _store = _ls.get_store()
        ts_iso = datetime.now(timezone.utc).isoformat()

        # One snapshot row per "kind" so the dashboard can query just the
        # part it needs (cpu / mem / disk / system) without loading the
        # full payload every time.
        _store.ingest_system_snapshot({
            "node_id":    node_id,
            "ts":         ts_iso,
            "kind":       "system",
            "rows":       payload.get("system", []),
            "infra":      payload.get("infra", {}),
            "session_count":     payload.get("sessionCount", 0),
            "model":             payload.get("model", ""),
            "main_tokens":       payload.get("mainTokens", 0),
            "subagent_count":    len(subagents_list),
            "active_subagents":  active_count,
        })

        # Sub-agent ingest moved EARLIER (right after the session-index read)
        # so the snapshot reads sub-agents back from DuckDB. Re-ingesting here
        # would corrupt the rows — subagents_list now carries the DuckDB shape
        # (displayName/totalTokens), not the filesystem shape (label/tokens).
    except Exception as _e:
        log.debug("local_store: snapshot/subagent write-through failed: %s", _e)

    # Split encryption from POST so the two failure modes have distinct
    # diagnostics + dispositions (sibling of #1601 / PR #1624).
    #   - Encryption failure → park in sync_dlq (corrupt/rotated key, payload
    #     containing non-JSON-serialisable bytes, missing cryptography wheel).
    #     The next sync tick's _dlq_replay picks it up automatically — the
    #     drainer is kind-agnostic and uses each row's stored endpoint.
    #   - POST failure → existing log.warning + drop. Lower severity than the
    #     session-batch path because the snapshot is re-emitted every cycle
    #     (no cumulative loss); cloud catches up on the next heartbeat.
    blob: str | None = None
    try:
        blob = encrypt_payload(payload, enc_key)
    except Exception as _enc_e:
        try:
            _dlq_enqueue_encryption_failure(
                kind="system_snapshot",
                endpoint="/ingest/system-snapshot",
                payload=payload,
                node_id=node_id,
                error=str(_enc_e),
            )
        except Exception as _dlq_e:
            log.exception(
                "E2E encryption AND DLQ persist both failed for "
                "system_snapshot (snapshot dropped from cloud; next cycle "
                "will re-emit): enc=%s dlq=%s",
                _enc_e, _dlq_e,
            )
        else:
            log.error(
                "E2E encryption failed for system_snapshot — parked in "
                "sync_dlq for replay (key rotation? corrupt key?): %s",
                _enc_e,
            )
        return 0
    try:
        _post(
            "/ingest/system-snapshot",
            {"node_id": node_id, "encrypted": True, "blob": blob},
            api_key,
        )
        return 1
    except Exception as e:
        log.warning(f"System snapshot sync error: {e}")
        return 0


# ── Real-time log streaming ────────────────────────────────────────────────────


def start_log_streamer(config: dict, paths: dict) -> threading.Thread:
    """Start a background thread that tails the local log file and POSTs lines to cloud in real-time."""


def start_log_streamer(config: dict, paths: dict) -> threading.Thread:
    """Start a background thread that tails the local log file and POSTs lines to cloud in real-time."""
    api_key = config["api_key"]
    node_id = config["node_id"]
    log_dir = paths.get("log_dir", "")

    def _find_latest_log():
        if not log_dir or not os.path.isdir(log_dir):
            return None
        today = datetime.now().strftime("%Y-%m-%d")
        candidates = sorted(
            glob.glob(os.path.join(log_dir, f"*{today}*")), reverse=True
        )
        if candidates:
            return candidates[0]
        # Fallback: most recent log file
        all_logs = sorted(
            glob.glob(os.path.join(log_dir, "*.log")),
            key=os.path.getmtime,
            reverse=True,
        )
        return all_logs[0] if all_logs else None

    def _stream_worker():
        log.info(f"Log streamer started — watching {log_dir}")
        current_file = None
        proc = None
        batch = []
        last_push = time.time()

        while True:
            try:
                # Find/rotate to latest log file
                latest = _find_latest_log()
                if latest != current_file:
                    if proc:
                        try:
                            proc.kill()
                        except Exception:
                            pass
                    current_file = latest
                    if not current_file:
                        time.sleep(5)
                        continue
                    proc = subprocess.Popen(
                        ["tail", "-f", "-n", "0", current_file],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True,
                    )
                    log.info(f"Tailing {current_file}")

                if not proc or not proc.stdout:
                    time.sleep(2)
                    continue

                # Non-blocking read with select
                import select

                ready, _, _ = select.select([proc.stdout], [], [], STREAM_INTERVAL)
                if ready:
                    line = proc.stdout.readline()
                    if line:
                        batch.append(line.rstrip())

                # Push batch every STREAM_INTERVAL seconds
                now = time.time()
                if batch and (now - last_push >= STREAM_INTERVAL or len(batch) >= 50):
                    try:
                        _post(
                            "/ingest/stream",
                            {"node_id": node_id, "lines": batch},
                            api_key,
                        )
                    except Exception as e:
                        log.debug(f"Stream push error: {e}")
                    batch = []
                    last_push = now

            except Exception as e:
                log.debug(f"Stream worker error: {e}")
                time.sleep(5)
                if proc:
                    try:
                        proc.kill()
                    except Exception:
                        pass
                    proc = None
                    current_file = None

    t = threading.Thread(target=_stream_worker, daemon=True, name="log-streamer")
    t.start()
    return t


def start_event_streamer(config: dict, state: dict, paths: dict) -> threading.Thread:
    """Real-time session event streamer — watches JSONL files for changes
    and pushes new events immediately (like Dropbox file sync).

    Only makes API calls when new data appears. Tracks file sizes locally
    to detect changes without polling the server.
    """
    api_key = config["api_key"]
    enc_key = config.get("encryption_key")
    node_id = config["node_id"]
    sessions_dir = paths["sessions_dir"]

    # Track file sizes to detect changes
    _file_sizes: dict[str, int] = {}
    _file_offsets: dict[str, int] = {}  # line offsets per file

    def _scan_and_push():
        """Check all JSONL files for new content. Push immediately if found."""
        if not os.path.isdir(sessions_dir):
            return 0
        total_pushed = 0
        jsonl_files = _list_session_jsonls(sessions_dir)
        # Only check recently modified files (last 2 hours) to avoid scanning stale ones
        cutoff = time.time() - 7200
        active = [f for f in jsonl_files if os.path.getmtime(f) > cutoff]

        # Build subagent map (reuse sync_sessions logic)
        file_to_subagent: dict[str, str] = {}
        idx_path = os.path.join(sessions_dir, "sessions.json")
        if os.path.isfile(idx_path):
            try:
                with open(idx_path) as _fi:
                    _idx = json.load(_fi)
                for _k, _meta in _idx.items():
                    if ":subagent:" in _k and isinstance(_meta, dict):
                        _sf = _meta.get("sessionFile", "")
                        if _sf:
                            file_to_subagent[os.path.basename(_sf)] = _k.split(":")[-1]
            except Exception:
                pass

        for fpath in active:
            fname = os.path.basename(fpath)
            try:
                cur_size = os.path.getsize(fpath)
            except OSError:
                continue
            prev_size = _file_sizes.get(fname, 0)
            if cur_size <= prev_size:
                # No change — skip (no API call)
                _file_sizes[fname] = cur_size
                continue

            # File grew — read only the new lines
            _file_sizes[fname] = cur_size
            offset = _file_offsets.get(fname, state.get("last_event_ids", {}).get(fname, 0))
            batch: list[dict] = []
            new_offset = offset
            try:
                with open(fpath, "r", errors="replace") as f:
                    for i, raw in enumerate(f):
                        if i < offset:
                            continue
                        raw = raw.strip()
                        new_offset = i + 1
                        if not raw:
                            continue
                        try:
                            batch.append(json.loads(raw))
                        except Exception:
                            continue
            except Exception as e:
                log.debug(f"Event streamer read error ({fname}): {e}")
                continue

            if batch:
                cloud_fname = _canonical_session_file(fname)
                subagent_id = file_to_subagent.get(cloud_fname) or file_to_subagent.get(fname)
                try:
                    _flush_session_batch(batch, cloud_fname, api_key, enc_key, node_id, subagent_id)
                    total_pushed += len(batch)
                    _file_offsets[fname] = new_offset
                    # Update shared state so main loop doesn't re-push
                    state.setdefault("last_event_ids", {})[fname] = new_offset
                except Exception as e:
                    log.debug(f"Event streamer push error ({fname}): {e}")
            else:
                _file_offsets[fname] = new_offset

        return total_pushed

    def _streamer_loop():
        log.info(f"Event streamer started — watching {sessions_dir}")
        # Initialize sizes so we don't re-push old data
        if os.path.isdir(sessions_dir):
            for f in _list_session_jsonls(sessions_dir):
                fname = os.path.basename(f)
                _file_sizes[fname] = os.path.getsize(f)
                _file_offsets[fname] = state.get("last_event_ids", {}).get(fname, 0)

        while True:
            try:
                pushed = _scan_and_push()
                if pushed:
                    log.debug(f"Event streamer pushed {pushed} events")
                    # Save state after each push so main loop stays in sync
                    save_state(state)
            except Exception as e:
                log.debug(f"Event streamer error: {e}")
            # Fast check — only sleeps 1s between scans (stat() is cheap)
            time.sleep(1)

    t = threading.Thread(target=_streamer_loop, daemon=True, name="event-streamer")
    t.start()
    return t


def run_daemon() -> None:
    if not _acquire_pid_lock():
        print(
            "[clawmetry-sync] Another instance is already running. Exiting.", flush=True
        )
        sys.exit(0)
    import atexit

    atexit.register(_release_pid_lock)
    # Issue #1593 — wire SIGTERM/SIGINT/atexit to drain the LocalStore ring
    # before exit. Without this, `launchctl bootout`, `systemctl stop`,
    # `kill <pid>`, and Ctrl+C all drop any events buffered in the 2s
    # flusher window. Register AFTER the PID-lock atexit so the LIFO
    # ordering drains events first, then releases the lock — that way a
    # racing supervisor restart sees the lock held until the flush is
    # done, instead of starting a second daemon mid-drain.
    _install_shutdown_handlers()
    config = load_config()
    # If node_id looks like email prefix (contains + or @), use hostname instead
    nid = config.get("node_id", "")
    if not nid:
        import socket

        config["node_id"] = socket.gethostname() or platform.node() or "unknown"
        save_config(config)
        log.info(f"Auto-set node_id:  → {config['node_id']!r}")
    paths = detect_paths()
    enc = "🔒 E2E encrypted" if config.get("encryption_key") else "⚠️  unencrypted"
    log.info(f"Starting sync daemon — node={config['node_id']} → {INGEST_URL} ({enc})")

    # ── Install daemon-error → DuckDB tee (PRD #1133 layer 4, daemon side) ──
    # Must happen AFTER the start-banner so we don't tee that line as an
    # event. Failure here is non-fatal — the read side keeps its sync.log
    # fallback.
    try:
        install_daemon_error_event_handler()
    except Exception as _e:
        log.warning("daemon-error event handler: failed to install: %s", _e)

    # ── Eagerly take the DuckDB writer lock BEFORE any read-only opener ──
    # DuckDB enforces a PROCESS-level lock on the file. Two failure modes
    # this warm-up addresses:
    #
    # 1. INTRA-process (the original bug): once a RO handle exists in THIS
    #    process, no RW handle can be opened (the singleton in
    #    ``local_store.get_store`` raises "cannot open writer — read-only
    #    handle already exists in this process"). Several startup paths
    #    request a RO store (heartbeat agent-install detection, cache push
    #    builders), and the main loop later tries to flush via the writer.
    #    Opening the writer FIRST means ``get_store(read_only=True)`` callers
    #    in this process transparently share the writer connection (see
    #    ``local_store.get_store`` lines 960-963) and no path is blocked.
    #
    # 2. INTER-process: a stray dashboard / second daemon / orphaned worktree
    #    can still own the writer lock. DuckDB then raises ``IO Error: Could
    #    not set lock on file ... Conflicting lock is held in <path> (PID
    #    <pid>) ...``. We surface that as an ERROR (not WARNING) with
    #    triage breadcrumbs because EVERY downstream writer call will fail
    #    until the offender exits, and the cascade of generic warnings
    #    elsewhere ("channel sync error", "telegram-gw-log unavailable",
    #    "pre-checkpoint flush failed") doesn't name the offending PID.
    try:
        from clawmetry import local_store as _ls_warmup
        _ls_warmup.get_store(read_only=False)
        log.info("local_store writer warm-up: owned (intra-process RO upgrades will share this handle)")
    except Exception as _ws_e:
        _msg = str(_ws_e)
        if "Conflicting lock" in _msg or "Could not set lock" in _msg:
            log.error(
                "local_store writer warm-up: ANOTHER PROCESS HOLDS THE "
                "DUCKDB WRITER LOCK. ALL writes will fail until it exits. "
                "Check the offending PID in: %s",
                _msg,
            )
        else:
            log.warning("local_store writer warm-up failed (continuing): %s", _ws_e)

    # ── Local query HTTP server (cross-process DuckDB read fix) ────────
    # Daemon owns the DuckDB writer lock; the dashboard process can't
    # open the same file (DuckDB exclusive lock blocks RO too). We host
    # the same routes/local_query.py shapes on a localhost port; the
    # dashboard's /api/local/* proxies through. Discovery+auth via
    # ~/.clawmetry/local_query.json. Failure here is non-fatal — the
    # dashboard falls back to direct DuckDB access (works in
    # single-process mode).
    #
    # MUST run BEFORE send_heartbeat(). The initial heartbeat is a
    # synchronous HTTP POST with `timeout=45` and up to 3 retries
    # (1s + 2s backoff) — i.e. ~135s worst-case when the ingest URL
    # is unreachable (offline laptop, CI smoke gate pointing at
    # 127.0.0.1:9, cloud cold start, PgBouncer flap). API Latency
    # Smoke gates on `~/.clawmetry/local_query.json` appearing
    # within 30s, and the cross-process dashboard's /api/local/*
    # proxy needs the discovery file too. Bringing the local query
    # server up FIRST decouples local-dashboard usability from any
    # cloud-side hiccup. Same class of "publish discovery before
    # blocking I/O" bug as PR #1762, just on the sister code path.
    try:
        from clawmetry import local_server as _local_server
        _ls_port = _local_server.start()
        if _ls_port:
            log.info("local query server: listening on 127.0.0.1:%d", _ls_port)
    except Exception as _e:
        log.warning("local query server: failed to start: %s", _e)

    # ── Startup sync: recent-first so Brain feed shows current activity ──
    send_heartbeat(config)
    log.info("Initial heartbeat sent")

    # WS relay deleted 2026-05-13: replaced by heartbeat-piggyback
    # (see project_relay_transport_decision). The cloud endpoint
    # /api/node/relay was killed 2026-05-12 (returns 404 in prod) after
    # the simple-websocket handshake-400 dead end documented in
    # reference_ws_handshake_400_unsolved.md. The reconnect loop was
    # spamming `relay: error: Handshake status 404 Not Found ...
    # reconnecting in 60s` forever — wasting bandwidth and burying real
    # errors. Cold-data reads now ride `pending_queries` piggybacked on
    # the heartbeat response and answered via /ingest/cache (issue #1053).
    # `clawmetry/relay.py` is retained as a stub so any third-party
    # importers don't crash, but `start_relay_thread` is no longer called.

    # ── Live gateway WS tap (capture in-memory channel messages) ────────
    # OpenClaw stores Telegram + sibling-channel chats entirely in
    # memory; gateway.log only carries outbound ACKs (no body), and no
    # JSONL is written for inbound. Without this tap, ClawMetry can
    # NEVER show real Telegram conversations on the Brain tab.
    # Default-ON; opt out via CLAWMETRY_ENABLE_WS_TAP=0.
    try:
        from clawmetry import gateway_tap as _gw_tap
        _gw_tap.start(config)
    except Exception as _e:
        log.warning("gateway WS tap: failed to start: %s", _e)

    state = load_state()

    # Always sync recent events first (last hour) — makes the dashboard
    # immediately useful even when there's a large backlog of old events.
    log.info("Syncing recent activity (last 60 min) first...")
    # Snapshot BOOTSTRAP.md immediately at startup — it may self-delete before
    # the first poll cycle on a fast-init OpenClaw. Idempotent; no-op when
    # the file isn't present (issue #690).
    try:
        if capture_bootstrap_if_present(config, paths):
            log.info("  Bootstrap: archived first-contact snapshot")
    except Exception as e:
        log.warning(f"  Bootstrap capture error: {e}")
    try:
        mem = sync_memory(config, state, paths)
        if mem:
            log.info(f"  Memory: {mem} files synced")
    except Exception as e:
        log.warning(f"  Memory sync error: {e}")
    try:
        recent_ev = sync_sessions_recent(config, state, paths, minutes=60)
        save_state(state)
        log.info(f"  Recent sessions: {recent_ev} events synced")
    except Exception as e:
        log.warning(f"  Recent session sync error: {e}")
    try:
        sm = sync_session_metadata(config, state)
        if sm:
            log.info(f"  Session metadata: {sm} rows synced")
    except Exception as e:
        log.warning(f"  Session metadata error: {e}")
    try:
        cr = sync_crons(config, state, paths)
        if cr:
            log.info(f"  Crons: {cr} synced")
    except Exception as e:
        log.warning(f"  Cron sync error: {e}")
    # Issue #605 DuckDB follow-up: ingest cron-run JSONL files so the
    # ``/api/crons/<jobId>/runs`` endpoint can read from DuckDB instead of
    # re-parsing JSONL on every request.
    try:
        crr = sync_cron_runs(config, state, paths)
        if crr:
            log.info(f"  Cron runs: {crr} rows ingested")
    except Exception as e:
        log.warning(f"  Cron-run ingest error: {e}")
    # Sync today's log lines immediately so Brain tab shows the most recent
    # activity right away — older log history is backfilled later
    try:
        lg = sync_logs(config, state, paths)
        if lg:
            log.info(f"  Recent logs: {lg} lines synced")
    except Exception as e:
        log.warning(f"  Recent log sync error: {e}")

    state["last_sync"] = datetime.now(timezone.utc).isoformat()
    # Force a sync local-store flush before persisting the startup cursor.
    # Same rationale as the per-tick checkpoint inside the main loop: never
    # commit an offset to disk while the events it represents are still in
    # volatile ring memory. INSERT OR IGNORE makes any replay a no-op.
    try:
        from clawmetry import local_store as _ls
        _ls.get_store().flush()
    except Exception as _flush_e:
        log.warning(
            "startup pre-checkpoint local-store flush failed (continuing): %s",
            _flush_e,
        )
    save_state(state)
    send_heartbeat(config)
    _record_sync_progress("complete", 0, 0, status="complete")
    log.info("Recent sync complete — Brain feed should show current activity")

    # Validate stored log offsets on startup — prevents silent gaps
    # after log rotation, file truncation, or daemon restarts
    _validate_log_offsets(state, paths)
    save_state(state)

    # Start real-time streamers in background
    start_log_streamer(config, paths)
    start_event_streamer(config, state, paths)

    # Backfill older sessions in a background thread so the main loop
    # (and Brain tab) shows current activity immediately. The backfill
    # thread waits for the first main-loop cycle to complete before
    # sending historical data — recent events always reach the cloud first.
    first_run = not state.get("initial_backfill_done")
    _backfill_done = threading.Event()
    if first_run:

        def _backfill_worker():
            # Give the main loop one full cycle (≈15s) to post recent events
            time.sleep(20)
            log.info("Background backfill starting — syncing older sessions...")
            try:
                bf_state = load_state()
                ev = sync_sessions(config, bf_state, paths)
                bf_state["initial_backfill_done"] = True
                bf_state["last_sync"] = datetime.now(timezone.utc).isoformat()
                save_state(bf_state)
                log.info(f"Background backfill: {ev} older events synced")
            except Exception as e:
                log.warning(f"Background backfill error: {e}")
            try:
                bf_state = load_state()
                lg = sync_logs(config, bf_state, paths)
                save_state(bf_state)
                log.info(f"Background backfill: {lg} log lines synced")
            except Exception as e:
                log.warning(f"Background backfill log error: {e}")
            _backfill_done.set()
            log.info("Background backfill complete")

        t = threading.Thread(target=_backfill_worker, daemon=True, name="backfill")
        t.start()

    # ── Cloud-mediated approvals watcher (vivekchand/clawmetry#667) ──
    # Background thread that tails session JSONLs for risky toolCalls and
    # blocks the agent (via gateway sessions_kill) when a human denies in
    # the cloud. No-op when ~/.clawmetry/policies.yml is empty/missing,
    # so this is a non-breaking default-off feature for OSS users.
    try:
        from clawmetry import approvals as _approvals
        _approvals_stop = threading.Event()
        # Route the approvals logger through the same handlers as our sync
        # logger so watcher activity (policy fires, decisions, kills) shows
        # up in ~/.clawmetry/sync.log alongside the sync line items.
        try:
            _ap_log = logging.getLogger("clawmetry-approvals")
            _ap_log.setLevel(logging.INFO)
            _ap_log.propagate = False
            for _h in list(log.handlers):
                if _h not in _ap_log.handlers:
                    _ap_log.addHandler(_h)
        except Exception:
            pass

        def _approvals_worker():
            try:
                _approvals.watcher_loop(
                    api_key=config["api_key"],
                    node_id=config["node_id"],
                    interval_sec=2.0,
                    stop_event=_approvals_stop,
                )
            except Exception as _ape:
                log.warning(f"approvals watcher exited: {_ape}")

        t_app = threading.Thread(
            target=_approvals_worker, daemon=True, name="approvals-watcher"
        )
        t_app.start()
        log.info("approvals watcher thread started "
                 f"(policies: {_approvals.POLICIES_PATH})")
    except Exception as _e:
        log.warning(f"approvals watcher failed to start: {_e}")

    # ── Decision-sampling cron (issue #1615) ──────────────────────────
    # Daily-at-midnight thread that picks N random sessions from yesterday
    # per agent_id and inserts them into the review_queue. Idempotent —
    # ingest_review_sample short-circuits on duplicate session_id, so a
    # restart mid-day re-runs without churning the queue. Default N=10
    # (CLAWMETRY_REVIEW_SAMPLE_SIZE env override).
    try:
        _review_stop = threading.Event()

        def _review_sampler_worker():
            from routes.review import sample_yesterday_for_review
            from datetime import datetime as _r_dt, timedelta as _r_td
            # Initial delay: let backfill finish so query_sessions_table
            # returns the full yesterday set, not an empty one.
            time.sleep(45)
            while not _review_stop.is_set():
                try:
                    result = sample_yesterday_for_review()
                    log.info(
                        "review sampler: %d sampled, %d skipped, %d agents",
                        result.get("sampled", 0),
                        result.get("skipped", 0),
                        result.get("agents", 0),
                    )
                except Exception as _re:
                    log.warning(f"review sampler tick failed: {_re}")
                # Sleep until next local midnight. 24h is the natural cadence;
                # we use a coarse compute (seconds-until-tomorrow-midnight)
                # rather than scheduling 1AM cron-style so the math stays in
                # one place. Daemon restart between ticks is harmless thanks
                # to ingest idempotency.
                now_local = _r_dt.now()
                tomorrow = now_local.date() + _r_td(days=1)
                next_midnight = _r_dt.combine(tomorrow, _r_dt.min.time())
                sleep_s = max(60.0, (next_midnight - now_local).total_seconds())
                _review_stop.wait(timeout=sleep_s)

        t_review = threading.Thread(
            target=_review_sampler_worker, daemon=True, name="review-sampler"
        )
        t_review.start()
        log.info("review sampler thread started (issue #1615)")
    except Exception as _e:
        log.warning(f"review sampler failed to start: {_e}")

    # Default to SLOW; flips to FAST after a heartbeat response with
    # `viewer_active: true` (epic #775 PR 2/3, adaptive sync cadence).
    # Seed from the startup heartbeat so the very first cycle picks up
    # FAST cadence when the user already has the cloud Brain tab open
    # at daemon start — otherwise the first 60s after startup is stuck
    # on SLOW even with an active viewer (2026-05-13 real-time MOAT fix).
    heartbeat_interval = _pick_heartbeat_interval(_LAST_HEARTBEAT_RESPONSE)
    snapshot_interval = 60  # system snapshot (subagents, flow metrics) every 60s
    log_sync_interval = 60  # log lines are low-priority; streamer covers real-time
    last_heartbeat = time.time()
    last_snapshot = 0  # force first snapshot immediately
    last_log_sync = (
        time.time()
    )  # already synced at startup; next run after log_sync_interval
    consecutive_hb_failures = 0
    # Alerts evaluator (PRD #779 PR-D pt2). 0 = fire on first cycle so we
    # exercise the dispatch path immediately if rules + matching events are
    # already present from startup backfill.
    last_alerts_eval = 0.0
    # Issue #1619 Phase 1 — LLM-as-judge scheduler. Sister cadence to the
    # alerts evaluator; 5-minute tick picks up to EVAL_BATCH unscored
    # completed sessions and persists scores in-process via the user's
    # existing API key (no cloud roundtrip). Default-on; CLAWMETRY_EVALS_
    # ENABLED=0 disables cleanly. 0 = fire on first cycle so a daemon
    # restart scores the backlog without waiting 5 min.
    last_evals_run = 0.0

    while True:
        try:
            state = load_state()

            # ── BOOTSTRAP.md "First Contact" capture (issue #690) ─────────
            # Best-effort; runs early in the tick so we snapshot the file
            # BEFORE any other helper notices OpenClaw has self-deleted it.
            # Idempotent — duplicate captures dedup at the local-store layer.
            try:
                capture_bootstrap_if_present(config, paths)
            except Exception as _be:
                log.warning("bootstrap capture failed: %s", _be)

            # ── High-priority: memory, flow metrics, subagents, recent sessions ──
            mem = sync_memory(config, state, paths)
            snap = 0
            now_snap = time.time()
            if now_snap - last_snapshot > snapshot_interval:
                snap = sync_system_snapshot(config, state, paths)  # subagents + flow
                last_snapshot = now_snap

            # ── Gateway process metric capture (#852 follow-up) ──
            # Persists RSS/CPU into DuckDB every 30s (rate-capped + deduped
            # inside the helper) so the dashboard can render a 24h sparkline
            # of memory pressure, not just a live snapshot. Best-effort.
            try:
                capture_gateway_metric(config)
            except Exception as _gm_e:
                log.debug("gateway.metric capture failed (continuing): %s", _gm_e)

            # ── Drain sync DLQ (#1601) ──
            # Replay any batches that previously failed AES-GCM encryption
            # (e.g. a key rotation race). Cheap no-op when the queue is
            # empty (single COUNT(*) on a tiny table). Failure here is
            # non-fatal — bad rows stay parked and we try again next tick.
            try:
                _dlq_replay(config.get("api_key"), config.get("encryption_key"))
            except Exception as _dlq_e:
                log.debug("sync_dlq replay failed (continuing): %s", _dlq_e)

            ev = sync_sessions(config, state, paths)
            ev += sync_claude_cli_sessions(config, state, paths)
            # PRIMARY: walk OpenClaw's sessions.json → ``cliSessionIds.claude-cli``
            # → ``~/.claude/projects/<encoded-cwd>/<id>.jsonl`` plus subagents/
            # and tool-results/. Tags events under the OpenClaw session UUID
            # and upserts a ``sessions`` row so the typed-session view joins.
            # Closes #1226 — the P0 follow-up to PR #1224. Failure is
            # non-fatal: the next cycle will retry from the saved offset.
            handled_claude_ids: set[str] = set()
            try:
                oc_cc_idx, handled_claude_ids = (
                    sync_openclaw_claude_sessions_via_index(
                        config, state, paths,
                    )
                )
                ev += oc_cc_idx
            except Exception as _occ_idx_e:
                log.debug(
                    "openclaw-cc-index sync error (non-fatal): %s",
                    _occ_idx_e,
                )
                oc_cc_idx = 0
            # SECONDARY: process-discovered Claude Code session JSONLs (PR
            # #1224, 2026-05-14). Catches sessions whose binding hasn't been
            # written to sessions.json yet — e.g. a brand-new session
            # mid-spawn, or one whose binding was lost on a crash. Skip
            # sessions already handled by the index path above so we don't
            # double-process. Failure is non-fatal.
            try:
                oc_cc = sync_openclaw_claude_sessions(
                    config, state, paths,
                    skip_claude_ids=handled_claude_ids,
                )
                ev += oc_cc
            except Exception as _occ_e:
                log.debug(
                    "openclaw-cc sync error (non-fatal): %s", _occ_e,
                )
                oc_cc = 0
            # Tail ~/.openclaw/<channel>/*.jsonl (Telegram, Signal, WhatsApp,
            # Discord, Slack, …). Until 2026-05-13 this watch path was missing
            # entirely — the user observed "I message Diya on Telegram and
            # ClawMetry shows nothing in Brain." Failure is non-fatal: the
            # next cycle will retry from the saved offset.
            try:
                ev += sync_channel_messages(config, state, paths)
            except Exception as _ce:
                log.warning(f"channel sync error (non-fatal): {_ce}")
            sm = sync_session_metadata(config, state)
            crons = sync_crons(config, state, paths)
            # Issue #605 DuckDB follow-up: tail cron-run JSONL files into
            # DuckDB so the dashboard's per-job timeline reads from the
            # columnar store. Failure is non-fatal — the legacy JSONL-read
            # fallback in routes/crons.py still works.
            try:
                cron_runs = sync_cron_runs(config, state, paths)
            except Exception as _e_cr:
                log.debug("sync_cron_runs error (non-fatal): %s", _e_cr)
                cron_runs = 0

            # ── Low-priority: log lines (real-time covered by streamer) ──
            lg = 0
            now_log = time.time()
            if now_log - last_log_sync > log_sync_interval:
                lg = sync_logs(config, state, paths)
                last_log_sync = now_log

            # ── Telegram outbound from gateway.log (#1192 follow-up) ──
            # OpenClaw stores Telegram chats in memory only — no JSONL is
            # written for them. The only on-disk evidence is the
            # ``[telegram] sendMessage ok ...`` ACKs in gateway.log. This
            # parser tails those into ``channel_messages`` so the Brain
            # / Channels tabs render at least the outbound side. Cheap
            # (byte-tail), idempotent (PRIMARY KEY on id), best-effort.
            try:
                tg = sync_telegram_from_gateway_log(config, state, paths)
            except Exception as _e_tg:
                log.debug(
                    "telegram-gw-log tick error (non-fatal): %s", _e_tg,
                )
                tg = 0

            state["last_sync"] = datetime.now(timezone.utc).isoformat()
            # Audit fix (2026-05-17): force a synchronous local-store flush
            # BEFORE persisting the cursor state. Belt-and-suspenders to
            # ``_flush_session_batch``'s own per-batch flush — covers any
            # ingest path (channels, logs, telegram, …) that mutated state
            # but routed its DuckDB writes through the ring buffer. If this
            # fails the cursor still advances (preserves legacy non-fatal
            # contract), but the next flusher tick + INSERT OR IGNORE keep
            # the events from being silently dropped.
            try:
                from clawmetry import local_store as _ls
                _ls.get_store().flush()
            except Exception as _flush_e:
                log.warning(
                    "pre-checkpoint local-store flush failed (continuing): %s",
                    _flush_e,
                )
            save_state(state)
            if ev or lg or mem or crons or sm or snap or cron_runs or tg or oc_cc:
                log.info(
                    f"Synced {ev} events ({oc_cc} from claude-cc), {lg} log lines, {mem} memory files, {crons} crons, {cron_runs} cron-runs, {sm} session rows, {tg} telegram-out ({enc})"
                )

            # ── Alerts evaluator (PRD #779 PR-D pt2, audit P0 #1 + #2) ──
            # Reads cached rules + recent events from the local DuckDB and
            # POSTs each match to the cloud's /api/cloud/alerts/dispatch
            # endpoint for notification fan-out. Throttled to
            # ALERTS_EVAL_INTERVAL_SEC. Failure is logged but never raises
            # into the sync cycle — alerts are best-effort relative to the
            # ingest path.
            now_alerts = time.time()
            if (now_alerts - last_alerts_eval) >= ALERTS_EVAL_INTERVAL_SEC:
                try:
                    n_alerts = evaluate_alerts(config, state)
                    if n_alerts:
                        log.info(
                            f"alerts: dispatched {n_alerts} match(es)"
                        )
                except Exception as _ae:
                    log.warning(f"alerts: evaluator tick errored: {_ae}")
                last_alerts_eval = now_alerts
                # Persist the eval state (last_eval_ts, cooldown memo) so
                # cooldown survives a daemon restart.
                try:
                    save_state(state)
                except Exception:
                    pass

            # ── Eval scheduler (issue #1619 Phase 1) ──
            # Sister of the alerts evaluator. Picks unscored completed
            # sessions from DuckDB and runs them through the LLM-as-
            # judge runner. Failure swallowed so a judge outage can't
            # take down the sync cycle.
            now_evals = time.time()
            if (now_evals - last_evals_run) >= EVAL_INTERVAL_SEC:
                try:
                    from clawmetry import eval_runner as _eval_runner
                    if _eval_runner.is_enabled():
                        n_scored = _eval_runner.score_pending_sessions(
                            batch_size=EVAL_BATCH,
                        )
                        if n_scored:
                            log.info(
                                "evals: scored %d session(s)", n_scored
                            )
                except Exception as _ee:
                    log.warning("evals: scheduler tick errored: %s", _ee)
                last_evals_run = now_evals

            # Re-mirror Docker data if running in Docker mode
            if hasattr(detect_paths, "_docker_cid") or any(
                "docker-mirror" in str(v) for v in paths.values()
            ):
                try:
                    fresh = _detect_docker_openclaw()
                    if fresh.get("sessions_dir"):
                        paths.update({k: v for k, v in fresh.items() if k in paths})
                except Exception:
                    pass

            now = time.time()
            if now - last_heartbeat > heartbeat_interval:
                if send_heartbeat(config):
                    if consecutive_hb_failures > 0:
                        log.info(
                            f"Heartbeat recovered after {consecutive_hb_failures} consecutive failures"
                        )
                    consecutive_hb_failures = 0
                    last_heartbeat = now
                    # Adaptive cadence (#775 PR 2/3): if the cloud signalled a
                    # live viewer, drop to FAST so Telegram / brain events
                    # appear in the dashboard within seconds. Otherwise stay
                    # at SLOW. Missing field → SLOW (back-compat with a cloud
                    # that hasn't deployed PR 1 of the epic yet).
                    heartbeat_interval = _pick_heartbeat_interval(
                        _LAST_HEARTBEAT_RESPONSE
                    )
                else:
                    consecutive_hb_failures += 1
                    if consecutive_hb_failures >= 5:
                        log.error(
                            f"CRITICAL: {consecutive_hb_failures} consecutive heartbeat failures — node appears offline in cloud"
                        )
                    # On failure stay on SLOW so we don't hammer a flapping
                    # cloud. The existing 1s/2s in-call backoff inside
                    # `send_heartbeat` already covers retry, and the next
                    # cycle inherits whatever interval we set here.
                    heartbeat_interval = HEARTBEAT_INTERVAL_SLOW

        except Exception as e:
            log.error(f"Sync cycle error: {e}")

        # Adaptive cycle sleep (P0 real-time MOAT, 2026-05-13). The
        # original `time.sleep(POLL_INTERVAL=15)` floored the heartbeat
        # latency at 15s even when `heartbeat_interval` had dropped to
        # FAST (3s) on viewer_active. That hard-capped Brain-tab
        # freshness at ~15s instead of the target 1-2s. We now sleep at
        # most `heartbeat_interval` so the next cycle (and its
        # heartbeat-piggyback brain push) fires on the FAST cadence
        # whenever a viewer is active. When idle (SLOW=60s),
        # POLL_INTERVAL still rules, so bandwidth + Cloud Run cost stay
        # flat.
        time.sleep(max(1, min(POLL_INTERVAL, heartbeat_interval)))


# ── Telegram gateway-log ingest (#1192 follow-up) ──────────────────────────
# DEPRECATED WHEN OPENCLAW PERSISTS: Remove this entire block (down through
# sync_telegram_from_gateway_log and its helpers) once OpenClaw writes Telegram
# sessions to disk like every other channel. The ``_CHANNEL_DIRS`` directory
# watcher in sync.py already covers that future path — on the day OpenClaw
# persists, this log parser becomes redundant and should be deleted.
#
# Why this exists
# ---------------
# OpenClaw runs Telegram direct-chat sessions ENTIRELY IN MEMORY. No per-
# session JSONL is ever written under ``~/.openclaw/agents/main/sessions/``
# or ``~/.openclaw/telegram/`` for inbound or outbound Telegram traffic
# (see memory ``reference_openclaw_telegram_inmemory.md``). PR #1192 wired
# up watching ``~/.openclaw/telegram/`` defensively for the day OpenClaw
# starts persisting, but until that upstream change lands the only on-disk
# evidence of Telegram activity is regex-recoverable from
# ``~/.openclaw/logs/gateway.log``.
#
# What gets captured
# ------------------
# Outbound ACK lines, e.g.
#
#   2026-05-13T22:54:19.865+02:00 [telegram] sendMessage ok chat=1532693273 message=8491
#   2026-05-13T06:00:56.332+02:00 [telegram] sendPhoto ok chat=1532693273 message=8480
#
# We synthesize a ``channel_messages`` row with ``direction="out"`` and
# ``body=None`` (the log only carries the ACK, never the message body).
# A breadcrumb is left in ``raw_blob`` so the dashboard can flag this row
# as "ack-only — body not captured" if it wants to.
#
# What is NOT captured
# --------------------
# * Outbound message bodies — the log never logs the text payload, only
#   the API ACK. The body lives only in OpenClaw's in-memory session
#   state.
# * Inbound messages — the production log emits ONLY long-poll
#   diagnostics for inbound (``[telegram] Polling stall detected``,
#   ``[diag] polling cycle finished``). Message bodies are not logged at
#   any verbosity setting we observed (2026-05-13). If a future OpenClaw
#   release adds an inbound trace line we can extend the parser, but
#   today there is nothing to parse.
#
# Long-term fix path
# ------------------
# 1. OpenClaw upstream change: persist inbound Telegram updates to a
#    session JSONL like every other channel does. Right thing, out of
#    ClawMetry's direct control.
# 2. Live gateway WebSocket tap on ``ws://localhost:18789`` — real-time,
#    no log parsing, but only catches messages received while the
#    ClawMetry daemon is running (no historical backfill).
# This log parser is the only path that works today without an OpenClaw
# upstream change AND backfills history on first install.

# Outbound API methods we currently parse. ``sendMessage`` covers the
# common case; the others appear in real production logs and trivially
# fit the same pattern.
_TELEGRAM_OUTBOUND_METHODS = (
    "sendMessage",
    "sendPhoto",
    "sendAudio",
    "sendDocument",
    "sendVideo",
    "sendVoice",
    "sendSticker",
    "sendAnimation",
    "sendLocation",
)

_TELEGRAM_PROVIDER = "telegram"
_TELEGRAM_OUTBOUND_PATTERN = None  # lazy compile; see helper below


def _telegram_outbound_pattern():
    """Lazily-compiled regex for one outbound telegram ACK line.

    Capture groups:
      1. ISO-8601 timestamp (with optional Z or +HH:MM offset, optional
         fractional seconds)
      2. API method (``sendMessage`` / ``sendPhoto`` / etc.)
      3. chat id (digits, may be negative for group chats)
      4. message id (digits)
    """
    import re as _re_local
    global _TELEGRAM_OUTBOUND_PATTERN
    if _TELEGRAM_OUTBOUND_PATTERN is None:
        methods = "|".join(_TELEGRAM_OUTBOUND_METHODS)
        _TELEGRAM_OUTBOUND_PATTERN = _re_local.compile(
            r"^(\d{4}-\d{2}-\d{2}T[\d:.]+(?:Z|[+-]\d{2}:?\d{2}))\s+"
            r"\[telegram\]\s+"
            r"(" + methods + r")\s+ok\s+"
            r"chat=(-?\d+)\s+"
            r"message=(\d+)"
        )
    return _TELEGRAM_OUTBOUND_PATTERN


def parse_telegram_outbound_line(line: str) -> dict | None:
    """Parse one gateway.log line into a ``channel_messages`` row dict.

    Returns ``None`` if the line is not an outbound Telegram ACK we
    recognise (the daemon will then leave the line alone — other parsers
    may still match it).

    The returned dict is shaped for ``LocalStore.ingest_channel_message()``.
    Importantly the ``id`` is ``"telegram:<chat>:<message>"`` so re-ingest
    is a primary-key no-op (idempotent if the byte-offset state is lost).
    """
    pat = _telegram_outbound_pattern()
    m = pat.match(line.strip())
    if not m:
        return None
    ts_iso, method, chat_id, message_id = (
        m.group(1), m.group(2), m.group(3), m.group(4),
    )
    return {
        "id": f"telegram:{chat_id}:{message_id}",
        "provider": _TELEGRAM_PROVIDER,
        "channel_id": f"telegram:{chat_id}",
        "ts": ts_iso,
        "direction": "out",
        # The log carries an ACK, not the message body. We deliberately
        # set body=None (rather than a placeholder string) so the read
        # side can render an "(no body captured)" affordance and isn't
        # tricked into showing literal placeholder text as content.
        "body": None,
        "raw_blob": {
            "source": "gateway.log",
            "method": method,
            "message_id": message_id,
            "chat_id": chat_id,
            # Breadcrumb for the dashboard / debug:
            "body_capture": "ack_only",
            "note": (
                "OpenClaw stores Telegram chats in memory; "
                "gateway.log only records the API ACK, not the body."
            ),
        },
    }


def _telegram_log_offset_key(log_path: str) -> str:
    """Per-log-path key under ``state['last_log_offsets']``.

    Keying by absolute path means a workspace switch (different
    ``CLAWMETRY_OPENCLAW_DIR``) starts a fresh tail rather than skipping
    forward in the new file.
    """
    return f"telegram_gw_log::{os.path.abspath(log_path)}"


def sync_telegram_from_gateway_log(
    config: dict | None,
    state: dict,
    paths: dict | None = None,
) -> int:
    """Tail the OpenClaw gateway.log for new Telegram outbound ACKs and
    ingest them into BOTH the local DuckDB ``channel_messages`` table
    (channel detail view) AND the ``events`` table (Brain feed).

    Returns the number of messages ingested this call. Designed to be
    called once per daemon sync cycle. All failure modes are swallowed
    (the daemon must never crash because telemetry plumbing broke); a
    warning is logged and ``0`` is returned.

    Why two writes
    --------------
    The Brain tab reads from ``LocalStore.query_events`` (the ``events``
    table) and renders any row whose ``event_type`` starts with
    ``CHANNEL.``. Until this dual-write was added, telegram outbound
    rows landed ONLY in ``channel_messages`` and Brain showed an empty
    Telegram channel — exactly the P0 user-visible bug this helper was
    meant to prevent. ``sync_channel_messages`` already dual-writes for
    JSONL-backed channels (see L2771-L2789); this brings the gateway-log
    parser into the same contract.

    Tail-and-resume contract
    ------------------------
    The last successfully-read byte offset is persisted in
    ``state['last_log_offsets'][_telegram_log_offset_key(log_path)]``.
    The caller is responsible for calling ``save_state(state)`` (the
    main loop already does this every cycle).

    Log rotation / truncation handling: if the file is shorter than the
    stored offset we reset to ``0`` and re-scan from the top. The
    ``ingest_channel_message`` PRIMARY KEY (and ``events`` ``INSERT OR
    IGNORE``) makes the re-scan idempotent.
    """
    try:
        if paths and isinstance(paths, dict) and paths.get("logs_dir"):
            log_path = os.path.join(str(paths["logs_dir"]), "gateway.log")
        else:
            log_path = os.path.join(_get_openclaw_dir(), "logs", "gateway.log")
        if not os.path.exists(log_path):
            return 0

        offsets = state.setdefault("last_log_offsets", {})
        key = _telegram_log_offset_key(log_path)
        prev_offset = int(offsets.get(key, 0) or 0)

        try:
            size = os.path.getsize(log_path)
        except OSError:
            return 0
        if size < prev_offset:
            # Log was rotated or truncated. Re-scan from the top; the
            # PRIMARY KEY on channel_messages.id keeps re-ingest a no-op.
            log.info(
                "telegram-gw-log: file shrank (size=%d < offset=%d); "
                "restarting tail from byte 0",
                size, prev_offset,
            )
            prev_offset = 0
        if size == prev_offset:
            return 0

        try:
            from clawmetry import local_store as _ls
            store = _ls.get_store()
        except Exception as e:
            log.warning("telegram-gw-log: local_store unavailable: %s", e)
            return 0

        try:
            with open(log_path, "rb") as fh:
                fh.seek(prev_offset)
                # Read in binary so the byte offset we persist is correct
                # for the next call regardless of multibyte characters in
                # the log (Telegram bodies aren't logged today, but other
                # entries do contain unicode).
                buf = fh.read()
        except OSError as e:
            log.warning("telegram-gw-log: read failed: %s", e)
            return 0

        try:
            text = buf.decode("utf-8", errors="ignore")
        except Exception:
            text = ""

        # Ensure we only consume complete lines this cycle. Anything
        # after the last newline is a partial line still being written;
        # leave the offset alone for that fragment so we re-read it next
        # cycle.
        last_nl = text.rfind("\n")
        if last_nl < 0:
            return 0
        complete = text[: last_nl + 1]
        new_offset = prev_offset + len(complete.encode("utf-8", errors="ignore"))

        # Resolve node_id ONCE per cycle (cheap dict lookup; the daemon
        # caches it for the life of the process). The events table needs
        # it on every row.
        node_id = (
            (config or {}).get("node_id")
            or os.environ.get("CLAWMETRY_NODE_ID")
            or "local"
        )

        ingested = 0
        for raw_line in complete.splitlines():
            if "[telegram]" not in raw_line:
                # Cheap pre-filter — only ~0.005% of gateway.log lines
                # are Telegram, and the regex match is non-trivial.
                continue
            row = parse_telegram_outbound_line(raw_line)
            if not row:
                continue
            try:
                # Issue #1220: single chokepoint writes channel_messages +
                # events atomically. Replaces the prior dual-write that
                # hand-rolled an events projection here (the original
                # P0 #1212 bug was forgetting to add that projection at
                # all; the chokepoint makes it structurally impossible).
                store.ingest_channel_event(row, node_id=node_id)
            except Exception as e:
                # One malformed row must not poison the rest of the tail.
                log.debug(
                    "telegram-gw-log: ingest_channel_event failed for "
                    "%s: %s", row.get("id"), e,
                )
                continue
            ingested += 1

        offsets[key] = new_offset
        if ingested:
            log.info(
                "telegram-gw-log: ingested %d outbound message(s) "
                "(offset %d → %d)",
                ingested, prev_offset, new_offset,
            )
        return ingested
    except Exception as e:
        log.warning("telegram-gw-log: cycle failed: %s", e)
        return 0


def _build_gateway_data(paths: dict = None) -> dict:
    """Parse gateway.log (plain text) for routing events."""
    import re

    try:
        from datetime import datetime as _dt

        today = _dt.now().strftime("%Y-%m-%d")
        gw_log = os.path.join(_get_openclaw_dir(), "logs", "gateway.log")

        routes = []
        stats = {
            "today_messages": 0,
            "today_heartbeats": 0,
            "today_crons": 0,
            "today_errors": 0,
            "active_sessions": 0,
        }

        _KNOWN_CHANNELS = {
            "telegram",
            "imessage",
            "whatsapp",
            "signal",
            "discord",
            "slack",
            "irc",
            "webchat",
            "googlechat",
            "msteams",
        }

        if os.path.exists(gw_log):
            with open(gw_log, errors="ignore") as f:
                for line in f:
                    line = line.strip()
                    if not line or not line.startswith(today):
                        continue
                    # Format: 2026-03-10T10:00:59.952Z [channel] rest...
                    m = re.match(r"(\S+Z)\s+\[(\w+)\]\s+(.*)", line)
                    if not m:
                        continue
                    ts, tag, rest = m.group(1), m.group(2), m.group(3)
                    route = {
                        "timestamp": ts,
                        "from": tag,
                        "to": "brain",
                        "session": "",
                        "type": "message",
                        "status": "ok",
                    }
                    if tag == "heartbeat":
                        route["type"] = "heartbeat"
                        stats["today_heartbeats"] += 1
                        routes.append(route)
                    elif tag == "cron":
                        route["type"] = "cron"
                        stats["today_crons"] += 1
                        routes.append(route)
                    elif tag in _KNOWN_CHANNELS:
                        if (
                            "sendMessage ok" in rest
                            or "send ok" in rest
                            or "delivered" in rest.lower()
                        ):
                            # Extract message_id for display
                            m_id = re.search(r"message=(\d+)", rest)
                            if m_id:
                                route["session"] = m_id.group(1)
                            route["to"] = "user"
                            stats["today_messages"] += 1
                            routes.append(route)
                    elif tag in ("warn", "error") or "error" in rest.lower()[:30]:
                        stats["today_errors"] += 1

        routes.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        return {
            "stats": stats,
            "routes": routes[:100],
            "total": len(routes),
            "status": "running",
            "port": 18789,
        }
    except Exception as e:
        return {
            "stats": {
                "today_messages": 0,
                "today_heartbeats": 0,
                "today_crons": 0,
                "today_errors": 0,
                "active_sessions": 0,
            },
            "routes": [],
            "total": 0,
            "status": "running",
            "port": 18789,
        }


def _compute_autonomy_daily_series(sessions_dir, days=90):
    """
    Compute per-day autonomy aggregates from local session transcripts.

    Returns a list of ``{day, median_gap_sec, autonomy_ratio, sample_count}``
    covering the last ``days`` days (UTC). Days with no user activity are
    skipped — we don't send empty days to cloud.

    The heavy lifting happens **here, on the user's machine**. Only the tiny
    aggregate leaves the box. See memory note ``local_compute_cloud_display``.
    """
    from collections import defaultdict
    from datetime import datetime as _dt_ad, timedelta as _td_ad, timezone as _tz_ad

    if not sessions_dir or not os.path.isdir(sessions_dir):
        return []

    now_utc = _dt_ad.now(tz=_tz_ad.utc)
    cutoff_ts = now_utc.timestamp() - days * 86400

    try:
        files = [
            f for f in os.listdir(sessions_dir)
            if f.endswith(".jsonl") and ".deleted." not in f and ".reset." not in f
        ]
    except OSError:
        return []

    daily = defaultdict(lambda: {"gaps": [], "no_nudge_sessions": 0, "sessions": 0, "user_msgs": 0})

    def _ts_of(msg_or_ev, fallback):
        for key in ("timestamp", "ts", "created_at", "time"):
            val = msg_or_ev.get(key)
            if val is None:
                continue
            if isinstance(val, (int, float)):
                return float(val) / (1000.0 if val > 10**12 else 1.0)
            if isinstance(val, str):
                try:
                    if val.endswith("Z"):
                        val = val[:-1] + "+00:00"
                    return _dt_ad.fromisoformat(val).timestamp()
                except (ValueError, TypeError):
                    continue
        return fallback

    for fname in files:
        fpath = os.path.join(sessions_dir, fname)
        try:
            file_mtime = os.path.getmtime(fpath)
        except OSError:
            file_mtime = now_utc.timestamp()
        if file_mtime < cutoff_ts:
            continue

        user_timestamps = []
        try:
            with open(fpath, "r", errors="replace") as fh:
                for raw in fh:
                    raw = raw.strip()
                    if not raw:
                        continue
                    try:
                        ev = json.loads(raw)
                    except (json.JSONDecodeError, ValueError):
                        continue
                    if not isinstance(ev, dict):
                        continue
                    msg = ev.get("message") if ev.get("type") == "message" else ev
                    if not isinstance(msg, dict):
                        continue
                    if msg.get("role") != "user":
                        continue
                    ts = _ts_of(msg, file_mtime)
                    if ts == file_mtime and ev.get("type") == "message":
                        ts = _ts_of(ev, file_mtime)
                    if ts < cutoff_ts:
                        continue
                    user_timestamps.append(ts)
        except OSError:
            continue

        if not user_timestamps:
            continue
        user_timestamps.sort()

        # Gaps between consecutive user messages in this session.
        session_gaps = [
            user_timestamps[i + 1] - user_timestamps[i]
            for i in range(len(user_timestamps) - 1)
            if user_timestamps[i + 1] - user_timestamps[i] > 0
        ]
        is_no_nudge = len(user_timestamps) <= 1

        day_key = _dt_ad.fromtimestamp(user_timestamps[0], tz=_tz_ad.utc).strftime("%Y-%m-%d")
        daily[day_key]["gaps"].extend(session_gaps)
        daily[day_key]["sessions"] += 1
        daily[day_key]["user_msgs"] += len(user_timestamps)
        if is_no_nudge:
            daily[day_key]["no_nudge_sessions"] += 1

    def _median(xs):
        xs = [x for x in xs if x is not None]
        if not xs:
            return None
        xs.sort()
        n = len(xs)
        m = n // 2
        return float(xs[m]) if n % 2 else (xs[m - 1] + xs[m]) / 2.0

    series = []
    # Build trailing 7-day slopes so cloud can see "improving/declining" hint.
    day_keys_sorted = sorted(daily.keys())
    for day_key in day_keys_sorted:
        bucket = daily[day_key]
        if bucket["sessions"] <= 0:
            continue
        series.append({
            "day": day_key,
            "median_gap_sec": _median(bucket["gaps"]),
            "autonomy_ratio": bucket["no_nudge_sessions"] / bucket["sessions"],
            "sample_count": bucket["user_msgs"],
            "trend_slope": None,  # filled in below if we can
        })

    # Rolling 7-day slope (normalized by running median).
    for i, entry in enumerate(series):
        window = series[max(0, i - 6): i + 1]
        if len(window) < 2:
            continue
        gaps = [w["median_gap_sec"] for w in window if w["median_gap_sec"] is not None]
        if len(gaps) < 2:
            continue
        xs = list(range(len(gaps)))
        n = len(xs)
        mean_x = sum(xs) / n
        mean_y = sum(gaps) / n
        num = sum((xs[k] - mean_x) * (gaps[k] - mean_y) for k in range(n))
        den = sum((xs[k] - mean_x) ** 2 for k in range(n))
        raw = num / den if den else 0.0
        med = _median(gaps)
        entry["trend_slope"] = round(raw / med, 6) if med else 0.0

    return series


def sync_autonomy(config, state, paths):
    """
    Push a daily autonomy aggregate to cloud (if opted in).

    Runs at most once per local-day: we record the last pushed UTC day in
    ``state['autonomy_last_day']`` and skip until that rolls over. On first
    run, pushes up to 90 days of history. Each subsequent run pushes
    whatever has changed.

    Skipped when sync is paused (expired trial).
    """
    if not _sync_allowed():
        return 0
    api_key = config.get("api_key") or ""
    if not api_key:
        return 0
    # User can opt out of sending analytics even if cloud sync is on.
    if config.get("cloud_autonomy_sync") is False:
        return 0

    from datetime import datetime as _dt_as, timezone as _tz_as
    today = _dt_as.now(tz=_tz_as.utc).strftime("%Y-%m-%d")
    last_pushed = state.get("autonomy_last_day", "")
    # Skip if we already pushed today, unless we've never pushed anything.
    if last_pushed == today and state.get("autonomy_pushed_any"):
        return 0

    sessions_dir = paths.get("sessions_dir") or paths.get("sessions")
    series = _compute_autonomy_daily_series(sessions_dir, days=90)
    if not series:
        return 0

    # Only send days we haven't pushed yet — or all of them on first run.
    if state.get("autonomy_pushed_any"):
        series = [s for s in series if s["day"] >= last_pushed]
    if not series:
        state["autonomy_last_day"] = today
        return 0

    node_id = config.get("node_id") or get_machine_id()
    payload = {"node_id": node_id, "snapshots": series}
    try:
        _post("/ingest/autonomy", payload, api_key, timeout=30)
        state["autonomy_last_day"] = today
        state["autonomy_pushed_any"] = True
        return len(series)
    except Exception as e:
        log.warning(f"sync_autonomy failed: {e}")
        return 0


ALERTS_EVAL_INTERVAL_SEC = 60  # Re-evaluate alerts every 60s (PRD #779)

# Issue #1619 Phase 1 — LLM-as-judge eval scheduler cadence. 300s (5 min)
# matches the PRD: every 5 min, pick up to EVAL_BATCH unscored completed
# sessions and persist their scores. Lower bound is the rate limiter
# (100/hour cap in clawmetry/eval_runner.py), so a chatty workspace
# self-throttles regardless of interval.
EVAL_INTERVAL_SEC = int(os.environ.get("CLAWMETRY_EVALS_INTERVAL_SEC", "300"))
EVAL_BATCH = int(os.environ.get("CLAWMETRY_EVALS_BATCH", "10"))
# Window for the events read from DuckDB on each tick. Wider than the
# evaluation interval so a slow tick doesn't drop events on the floor.
_ALERTS_EVENT_LOOKBACK_SEC = 600
# Cap rows fetched per tick. Generous for a single-node alert evaluator;
# rolling-window math is O(N²) in the worst case but N is small.
_ALERTS_EVENT_LIMIT = 2000


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _iso_now_minus(seconds: int) -> str:
    from datetime import timedelta as _td
    return (datetime.now(timezone.utc) - _td(seconds=seconds)).isoformat()


def evaluate_alerts(config: dict, state: dict) -> int:
    """Local DuckDB evaluation -> cloud dispatch on match (PRD #779 PR-D pt2).

    Closes the architectural inversion called out in the 2026-05-13 audit
    (P0 #1 + P0 #2): the daemon now reads the events it just wrote to
    DuckDB, walks the cloud-cached alert rules locally via
    ``clawmetry.alert_evaluator``, and POSTs each match to the cloud's
    ``/api/cloud/alerts/dispatch`` endpoint (which fans out to Slack/email/
    PagerDuty). Cloud no longer evaluates rules — it just dispatches
    notifications for matches the local node certifies.

    Returns the count of dispatched matches. Persists ``alerts_last_eval_ts``
    + ``alerts_eval_memo`` into ``state`` so cooldown survives daemon
    restart. Skipped silently when:
      * the user is OSS-only (no ``cm_`` api key) — alerts is Cloud-Pro only,
      * no rules are cached locally (cloud hasn't authored or pushed any),
      * the local store is unreachable (the function never raises into the
        daemon loop — at most logs a WARNING and returns 0).

    See PRD ``clawmetry-cloud#779`` and the cloud endpoint shipped in
    ``clawmetry-cloud#785`` for the dispatch payload contract.
    """
    api_key = config.get("api_key", "")
    node_id = config.get("node_id", "")
    if not api_key or not api_key.startswith("cm_") or not node_id:
        return 0  # OSS / unconfigured node: nothing to dispatch.

    try:
        from clawmetry import local_store, alert_evaluator
    except Exception as e:
        log.warning("alerts: local_store/alert_evaluator import failed: %s", e)
        return 0

    try:
        store = local_store.get_store()
    except Exception as e:
        log.warning("alerts: local store unavailable: %s", e)
        return 0

    # Scope to rules owned by this token. Same hash the cloud uses, so a
    # multi-tenant local store (rare today) only fires this token's rules.
    try:
        owner_hash = _owner_hash_for_token(api_key)
    except Exception:
        owner_hash = None
    try:
        rules = store.query_alert_rules(
            owner_hash=owner_hash,
            enabled_only=True,
            limit=200,
        )
    except Exception as e:
        log.warning("alerts: query_alert_rules failed: %s", e)
        return 0
    if not rules:
        return 0

    # Read the recent slice of events. ``since`` is whichever is more recent
    # of (last successful eval ts) or (now - lookback) — bounds the window
    # so a daemon restart doesn't replay the entire DuckDB history.
    last_eval_ts = state.get("alerts_last_eval_ts")
    since = last_eval_ts or _iso_now_minus(_ALERTS_EVENT_LOOKBACK_SEC)
    try:
        events = store.query_events(since=since, limit=_ALERTS_EVENT_LIMIT)
    except Exception as e:
        log.warning("alerts: query_events failed: %s", e)
        return 0

    last_eval_state = state.setdefault("alerts_eval_memo", {})
    if not isinstance(last_eval_state, dict):
        last_eval_state = {}
        state["alerts_eval_memo"] = last_eval_state

    try:
        matches = alert_evaluator.evaluate(rules, events, last_eval_state)
    except Exception as e:
        log.warning("alerts: evaluator errored: %s", e)
        state["alerts_last_eval_ts"] = _iso_now()
        return 0

    dispatched = 0
    for m in matches:
        rule = m.get("rule") or {}
        evt = m.get("event") or {}
        try:
            resp = _post(
                "/api/cloud/alerts/dispatch",
                {
                    "rule_id":       rule.get("id"),
                    "rule_name":     rule.get("name") or "",
                    "node_id":       node_id,
                    "event_id":      evt.get("id"),
                    "event_summary": (m.get("summary") or "")[:500],
                    "evaluated_at":  _iso_now(),
                    "metadata":      m.get("metadata") or {},
                },
                api_key,
                timeout=10,
            )
        except Exception as e:
            log.warning("alerts: dispatch failed (rule=%s): %s",
                        rule.get("id"), e)
            continue
        if isinstance(resp, dict) and resp.get("ok"):
            dispatched += 1
            if resp.get("deduped"):
                log.debug("alerts: rule=%s dispatched (cloud deduped)",
                          rule.get("id"))
            else:
                log.info("alerts: rule=%s dispatched -> %s",
                         rule.get("id"), resp.get("dispatched") or [])

    state["alerts_last_eval_ts"] = _iso_now()
    return dispatched


if __name__ == "__main__":
    while True:
        try:
            run_daemon()
            break  # clean exit
        except KeyboardInterrupt:
            break
        except Exception as e:
            import traceback

            log.error(f"Daemon crashed: {e}")
            log.error(traceback.format_exc())
            log.info("Restarting in 15 seconds...")
            time.sleep(15)
