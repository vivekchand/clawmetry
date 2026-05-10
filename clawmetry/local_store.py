"""Local SQLite event store — Phase 1 of the local-first refactor (#958).

The node holds the durable record of every telemetry event. Cloud sync (sync.py)
remains the upstream path; this module is the *local* persistence layer that the
OSS dashboard and the future cloud→node relay (#960/#961) will read from.

Design choices:

* SQLite + WAL so the daemon (writer) and the dashboard (reader) can coexist
  in the same process without locking. SQLite is the only zero-dep persistence
  story that works on every platform `pip install` lands on.
* A small in-memory ring buffer flushed every ``FLUSH_INTERVAL`` seconds or
  ``FLUSH_BATCH`` events, whichever first. Worst-case data loss on a hard
  kill is one flush interval (~2 s) — never DB corruption (WAL guarantees).
* Idempotent ``ingest()``: every event carries a UUID; INSERT OR IGNORE makes
  re-delivery from the JSONL watcher a no-op. The cloud-sync daemon and the
  local writer can both call ingest() on the same event without dedup logic
  outside this module.
* Read API returns plain dicts (``query_events``, ``query_sessions``, ...) —
  no ORM, no abstractions. The shapes mirror the cloud ``events`` table and
  the cloud ``/api/cloud/*`` JSON responses so the dashboard can swap backends
  with minimal edits.
* Pure stdlib + sqlite3. No new pip deps for this phase.

NOT in this module (deliberately):

* Network — there is no HTTP server here. Adding endpoints is a follow-up
  blueprint (`clawmetry/blueprints/local_query.py`) so this module stays
  pure-storage and trivially unit-testable.
* Encryption — events are stored plaintext locally. The bytes never leave
  the device through this module; the cloud sync daemon does its own E2E
  encryption pass before POSTing.
* Cloud sync — independent. Adding the local store does not change what
  sync.py ships.
"""

from __future__ import annotations

import json
import logging
import os
import sqlite3
import threading
import time
from collections import deque
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterable, Iterator

log = logging.getLogger("clawmetry.local_store")


# Public knobs — tuned for the common case (one daemon, one dashboard, ≤1 K
# events/s sustained on a developer laptop). Adjust via env vars only.

DB_PATH = Path(
    os.environ.get(
        "CLAWMETRY_LOCAL_STORE_PATH",
        os.path.expanduser("~/.clawmetry/events.db"),
    )
)

# Background flusher: flush at least every FLUSH_INTERVAL seconds, OR when
# the in-memory queue reaches FLUSH_BATCH events. Whichever first.
FLUSH_INTERVAL_SECS = float(os.environ.get("CLAWMETRY_LOCAL_FLUSH_SECS", "2.0"))
FLUSH_BATCH = int(os.environ.get("CLAWMETRY_LOCAL_FLUSH_BATCH", "1000"))

# Cap the ring buffer so a runaway producer doesn't OOM the daemon. If we hit
# the cap we drop oldest events on the floor and log a warning — better than
# crashing the daemon.
RING_MAX = int(os.environ.get("CLAWMETRY_LOCAL_RING_MAX", "10000"))

# Default size cap. When the DB exceeds this, the next vacuum prunes oldest.
LOCAL_MAX_BYTES = int(
    float(os.environ.get("CLAWMETRY_LOCAL_MAX_GB", "5.0")) * 1024 * 1024 * 1024
)

SCHEMA_VERSION = 1

_DDL = [
    """
    CREATE TABLE IF NOT EXISTS events (
        id            TEXT PRIMARY KEY,
        node_id       TEXT NOT NULL,
        agent_id      TEXT NOT NULL DEFAULT 'main',
        session_id    TEXT,
        workspace_id  TEXT,
        event_type    TEXT NOT NULL,
        ts            TEXT NOT NULL,
        data          BLOB,
        cost_usd      REAL,
        token_count   INTEGER,
        model         TEXT,
        created_at    INTEGER NOT NULL
    )
    """,
    "CREATE INDEX IF NOT EXISTS idx_events_ts          ON events(ts DESC)",
    "CREATE INDEX IF NOT EXISTS idx_events_session     ON events(session_id, ts)",
    "CREATE INDEX IF NOT EXISTS idx_events_agent_ts    ON events(agent_id, ts DESC)",
    "CREATE INDEX IF NOT EXISTS idx_events_type_ts     ON events(event_type, ts DESC)",
    """
    CREATE TABLE IF NOT EXISTS daily_aggregates (
        agent_id      TEXT NOT NULL,
        workspace_id  TEXT,
        day           TEXT NOT NULL,
        cost_usd      REAL DEFAULT 0,
        token_count   INTEGER DEFAULT 0,
        event_count   INTEGER DEFAULT 0,
        error_count   INTEGER DEFAULT 0,
        PRIMARY KEY (agent_id, workspace_id, day)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS schema_version (
        version    INTEGER PRIMARY KEY,
        applied_at INTEGER NOT NULL
    )
    """,
]


# ── Connection management ────────────────────────────────────────────────────

# One connection per thread. SQLite forbids sharing a connection across threads
# unless check_same_thread=False, but even then concurrent writes serialize.
# Per-thread connections + WAL mode is the standard pattern.
_thread_local = threading.local()


def _connect() -> sqlite3.Connection:
    """Return the current thread's connection, creating it on first call."""
    conn = getattr(_thread_local, "conn", None)
    if conn is not None:
        return conn
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH), timeout=30, isolation_level=None)
    conn.row_factory = sqlite3.Row
    # WAL: concurrent reader + writer. NORMAL: trade strict fsync for ~10×
    # write throughput; we accept ≤ one flush of loss on power-cut, the same
    # bound the in-memory ring already imposes.
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute("PRAGMA temp_store=MEMORY")
    _thread_local.conn = conn
    return conn


def _migrate(conn: sqlite3.Connection) -> None:
    """Apply DDL idempotently and stamp the schema version."""
    for stmt in _DDL:
        conn.execute(stmt)
    cur = conn.execute("SELECT MAX(version) AS v FROM schema_version")
    row = cur.fetchone()
    current = row["v"] if row and row["v"] is not None else 0
    if current < SCHEMA_VERSION:
        conn.execute(
            "INSERT OR IGNORE INTO schema_version (version, applied_at) VALUES (?, ?)",
            (SCHEMA_VERSION, int(time.time() * 1000)),
        )


# ── Singleton store ─────────────────────────────────────────────────────────

_store: "LocalStore | None" = None
_store_lock = threading.Lock()


def get_store() -> "LocalStore":
    """Lazy-init the process-wide singleton. Cheap to call repeatedly."""
    global _store
    if _store is not None:
        return _store
    with _store_lock:
        if _store is None:
            _store = LocalStore()
            _store.start()
    return _store


class LocalStore:
    """Thread-safe local event store with a background batched flusher."""

    def __init__(self) -> None:
        self._ring: deque[dict[str, Any]] = deque(maxlen=RING_MAX)
        self._ring_lock = threading.Lock()
        # Cumulative counter of events dropped because the ring filled up.
        # Surfaced via ``health()`` so the dashboard can warn the user.
        self._dropped = 0
        self._flusher_stop = threading.Event()
        self._flusher_thread: threading.Thread | None = None
        self._last_flush_ts = time.monotonic()
        # Ensure schema exists from the main thread before any worker hits it.
        _migrate(_connect())

    # ── lifecycle ────────────────────────────────────────────────────────

    def start(self) -> None:
        """Start the background flusher. Safe to call multiple times."""
        if self._flusher_thread and self._flusher_thread.is_alive():
            return
        self._flusher_stop.clear()
        t = threading.Thread(
            target=self._flusher_loop,
            name="clawmetry-local-store-flusher",
            daemon=True,
        )
        self._flusher_thread = t
        t.start()
        log.info("local store: started, db=%s", DB_PATH)

    def stop(self, *, flush: bool = True) -> None:
        """Stop the flusher. Optionally drain the ring first."""
        self._flusher_stop.set()
        if self._flusher_thread:
            self._flusher_thread.join(timeout=10)
        if flush:
            self._flush_now()

    # ── ingest ──────────────────────────────────────────────────────────

    def ingest(self, event: dict[str, Any]) -> None:
        """Queue one event. Returns immediately; the flusher persists in the
        background. Required keys: ``id``, ``node_id``, ``event_type``, ``ts``.
        Other columns optional. Re-ingesting the same id is a no-op (INSERT OR
        IGNORE) so callers don't need their own dedup."""
        if not event.get("id"):
            raise ValueError("event must include 'id'")
        if not event.get("node_id"):
            raise ValueError("event must include 'node_id'")
        if not event.get("event_type"):
            raise ValueError("event must include 'event_type'")
        if not event.get("ts"):
            raise ValueError("event must include 'ts'")
        with self._ring_lock:
            if len(self._ring) >= RING_MAX:
                # deque(maxlen=) silently drops; track for visibility.
                self._dropped += 1
            self._ring.append(event)
        # Trigger an immediate flush if we just hit the batch boundary,
        # so a burst doesn't wait the full FLUSH_INTERVAL.
        if len(self._ring) >= FLUSH_BATCH:
            self._flush_now()

    def ingest_many(self, events: Iterable[dict[str, Any]]) -> None:
        for e in events:
            self.ingest(e)

    # ── flush ───────────────────────────────────────────────────────────

    def _flusher_loop(self) -> None:
        while not self._flusher_stop.is_set():
            self._flusher_stop.wait(FLUSH_INTERVAL_SECS)
            try:
                self._flush_now()
            except Exception:
                log.exception("local store: flush failed (will retry)")

    def _flush_now(self) -> int:
        """Drain the ring into SQLite in one transaction. Returns rows written.
        We hold a snapshot of the events while writing and only clear them from
        the ring after a successful COMMIT — so a write failure leaves the data
        queued for the next flush attempt instead of vanishing."""
        with self._ring_lock:
            if not self._ring:
                return 0
            batch = list(self._ring)
        rows = [_event_to_row(e) for e in batch]
        conn = _connect()
        # One transaction → one fsync (under synchronous=NORMAL) for the whole
        # batch. INSERT OR IGNORE so re-delivery is harmless.
        with _txn(conn):
            conn.executemany(
                """
                INSERT OR IGNORE INTO events
                  (id, node_id, agent_id, session_id, workspace_id,
                   event_type, ts, data, cost_usd, token_count, model, created_at)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
                """,
                rows,
            )
        # Commit succeeded — safe to remove the snapshot from the ring.
        # New events appended *during* the write stay in the ring for the next
        # cycle. We pop precisely len(batch) entries from the left.
        with self._ring_lock:
            for _ in range(len(batch)):
                if self._ring:
                    self._ring.popleft()
        self._last_flush_ts = time.monotonic()
        return len(rows)

    # ── queries ─────────────────────────────────────────────────────────

    def query_events(
        self,
        *,
        session_id: str | None = None,
        agent_id: str | None = None,
        event_type: str | None = None,
        since: str | None = None,
        until: str | None = None,
        limit: int = 500,
    ) -> list[dict[str, Any]]:
        """Read events. Defaults to most recent first. Empty kwargs = global
        recent stream."""
        conn = _connect()
        clauses: list[str] = []
        params: list[Any] = []
        if session_id:
            clauses.append("session_id = ?")
            params.append(session_id)
        if agent_id:
            clauses.append("agent_id = ?")
            params.append(agent_id)
        if event_type:
            clauses.append("event_type = ?")
            params.append(event_type)
        if since:
            clauses.append("ts >= ?")
            params.append(since)
        if until:
            clauses.append("ts <= ?")
            params.append(until)
        where = ("WHERE " + " AND ".join(clauses)) if clauses else ""
        sql = f"""
            SELECT id, node_id, agent_id, session_id, workspace_id,
                   event_type, ts, data, cost_usd, token_count, model
            FROM events
            {where}
            ORDER BY ts DESC, id DESC
            LIMIT ?
        """
        params.append(int(limit))
        return [_row_to_event(r) for r in conn.execute(sql, params).fetchall()]

    def query_sessions(
        self,
        *,
        agent_id: str | None = None,
        since: str | None = None,
        until: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """One row per distinct session_id seen, with start/end timestamps,
        event count, and total cost."""
        conn = _connect()
        clauses: list[str] = ["session_id IS NOT NULL"]
        params: list[Any] = []
        if agent_id:
            clauses.append("agent_id = ?")
            params.append(agent_id)
        if since:
            clauses.append("ts >= ?")
            params.append(since)
        if until:
            clauses.append("ts <= ?")
            params.append(until)
        where = "WHERE " + " AND ".join(clauses)
        sql = f"""
            SELECT
              session_id,
              MIN(agent_id)               AS agent_id,
              MIN(ts)                     AS started_at,
              MAX(ts)                     AS updated_at,
              COUNT(*)                    AS event_count,
              COALESCE(SUM(cost_usd), 0)  AS cost_usd,
              COALESCE(SUM(token_count),0) AS token_count
            FROM events
            {where}
            GROUP BY session_id
            ORDER BY updated_at DESC
            LIMIT ?
        """
        params.append(int(limit))
        return [dict(r) for r in conn.execute(sql, params).fetchall()]

    def query_aggregates(
        self,
        *,
        agent_id: str | None = None,
        since: str | None = None,
        until: str | None = None,
    ) -> list[dict[str, Any]]:
        """Per-day rollup. Computed on the fly from events; the materialized
        ``daily_aggregates`` table is reserved for the nightly job in #959.
        On-the-fly is fine at the scale of one node × one year × ~1 K events/day
        (~365 K rows; sub-100ms with the ts index)."""
        conn = _connect()
        clauses: list[str] = []
        params: list[Any] = []
        if agent_id:
            clauses.append("agent_id = ?")
            params.append(agent_id)
        if since:
            clauses.append("ts >= ?")
            params.append(since)
        if until:
            clauses.append("ts <= ?")
            params.append(until)
        where = ("WHERE " + " AND ".join(clauses)) if clauses else ""
        sql = f"""
            SELECT
              substr(ts, 1, 10)            AS day,
              agent_id,
              COUNT(*)                     AS event_count,
              COALESCE(SUM(cost_usd), 0)   AS cost_usd,
              COALESCE(SUM(token_count),0) AS token_count
            FROM events
            {where}
            GROUP BY day, agent_id
            ORDER BY day DESC
        """
        return [dict(r) for r in conn.execute(sql, params).fetchall()]

    # ── ops / maintenance ──────────────────────────────────────────────

    def health(self) -> dict[str, Any]:
        """Snapshot of store state — for the /local/health endpoint and the
        dashboard footer."""
        conn = _connect()
        size_bytes = DB_PATH.stat().st_size if DB_PATH.exists() else 0
        row = conn.execute(
            "SELECT COUNT(*) AS n, MIN(ts) AS oldest, MAX(ts) AS newest FROM events"
        ).fetchone()
        with self._ring_lock:
            ring_depth = len(self._ring)
            dropped = self._dropped
        return {
            "db_path": str(DB_PATH),
            "size_bytes": size_bytes,
            "size_mb": round(size_bytes / 1024 / 1024, 2),
            "size_cap_bytes": LOCAL_MAX_BYTES,
            "event_count": int(row["n"] or 0),
            "oldest_ts": row["oldest"],
            "newest_ts": row["newest"],
            "ring_depth": ring_depth,
            "ring_max": RING_MAX,
            "ring_dropped_total": dropped,
            "schema_version": SCHEMA_VERSION,
            "last_flush_ago_s": round(time.monotonic() - self._last_flush_ts, 2),
        }

    def vacuum(self, *, prune_to_bytes: int | None = None) -> dict[str, Any]:
        """Reclaim space. If ``prune_to_bytes`` is set (or the DB has exceeded
        ``LOCAL_MAX_BYTES``), delete oldest events first until the projected
        size fits, then VACUUM. Returns a summary."""
        # Drain pending writes first so size reflects reality.
        self._flush_now()
        conn = _connect()
        before_size = DB_PATH.stat().st_size if DB_PATH.exists() else 0
        cap = prune_to_bytes if prune_to_bytes is not None else LOCAL_MAX_BYTES
        deleted = 0
        if before_size > cap:
            # Estimate rows-per-byte from the current table to translate the
            # excess size into a rough delete-count. Conservative: prune 20%
            # extra so we don't spam vacuum on every flush.
            row = conn.execute("SELECT COUNT(*) AS n FROM events").fetchone()
            n = int(row["n"] or 0)
            if n > 0 and before_size > 0:
                bytes_per_row = before_size / n
                excess_bytes = (before_size - cap) * 1.2
                rows_to_drop = int(excess_bytes / bytes_per_row) if bytes_per_row else 0
                if rows_to_drop > 0:
                    cur = conn.execute(
                        """
                        DELETE FROM events WHERE id IN (
                          SELECT id FROM events ORDER BY ts ASC LIMIT ?
                        )
                        """,
                        (rows_to_drop,),
                    )
                    deleted = cur.rowcount
        # VACUUM cannot run inside a transaction; isolation_level=None lets us
        # call it directly.
        conn.execute("VACUUM")
        after_size = DB_PATH.stat().st_size if DB_PATH.exists() else 0
        return {
            "deleted_rows": deleted,
            "before_bytes": before_size,
            "after_bytes": after_size,
            "cap_bytes": cap,
            "reclaimed_bytes": max(0, before_size - after_size),
        }


# ── helpers ────────────────────────────────────────────────────────────────


def _event_to_row(e: dict[str, Any]) -> tuple:
    """Coerce an event dict into the column tuple for the events table.
    Unknown keys are tolerated and dropped — events come from many sources
    (jsonl parser, gateway, claude-cli adapter) with slightly different shapes,
    and the store should not be the strict-schema choke point."""
    data = e.get("data")
    if data is not None and not isinstance(data, (bytes, bytearray)):
        # Serialise dicts/lists to JSON bytes; leave strings alone (they're
        # already in their final form).
        if isinstance(data, str):
            data = data.encode("utf-8")
        else:
            data = json.dumps(data, separators=(",", ":")).encode("utf-8")
    return (
        str(e["id"]),
        str(e["node_id"]),
        str(e.get("agent_id") or "main"),
        e.get("session_id"),
        e.get("workspace_id"),
        str(e["event_type"]),
        str(e["ts"]),
        data,
        float(e["cost_usd"]) if e.get("cost_usd") is not None else None,
        int(e["token_count"]) if e.get("token_count") is not None else None,
        e.get("model"),
        int(time.time() * 1000),
    )


def _row_to_event(r: sqlite3.Row) -> dict[str, Any]:
    """Inverse of _event_to_row: rehydrate a row into a JSON-friendly dict.
    The ``data`` column is decoded back to JSON if it's valid, else returned
    as a UTF-8 string. Bytes-in-bytes-out callers can re-encode."""
    out = dict(r)
    raw = out.get("data")
    if raw is not None:
        try:
            text = raw.decode("utf-8") if isinstance(raw, (bytes, bytearray)) else raw
            try:
                out["data"] = json.loads(text)
            except (ValueError, TypeError):
                out["data"] = text
        except UnicodeDecodeError:
            out["data"] = None
    return out


@contextmanager
def _txn(conn: sqlite3.Connection) -> Iterator[None]:
    """Explicit BEGIN/COMMIT around a block. We use isolation_level=None
    (autocommit) so transactions are explicit; this contextmanager makes that
    safe."""
    conn.execute("BEGIN")
    try:
        yield
    except Exception:
        conn.execute("ROLLBACK")
        raise
    else:
        conn.execute("COMMIT")
