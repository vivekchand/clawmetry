"""Local DuckDB event store — Phase 1 of the local-first refactor (#964).

Switched from SQLite to DuckDB (decision: 2026-05-11). Same public API; the
durability + concurrency model differs (DuckDB MVCC instead of SQLite WAL),
but the surface — ``ingest()``, ``query_events()``, ``query_sessions()``,
``query_aggregates()``, ``health()``, ``vacuum()`` — is unchanged.

Why DuckDB:
* Columnar storage → analytical queries (GROUP BY, time-window aggregates,
  per-tool/per-session/per-day rollups) run an order of magnitude faster than
  on SQLite. The dashboard's Brain/Tokens/Sessions tabs are exactly that
  shape of workload.
* Native Parquet and CSV I/O — future cheap archival + ad-hoc export are a
  one-liner, not a library swap.
* Time-series-friendly query patterns become first-class.
* Trade-off: a real wheel dependency (~14 MB) instead of stdlib sqlite3.
  Considered acceptable: the analytical advantages compound as the local
  store accrues months of data.

NOT in this module (deliberately):
* Network — there is no HTTP server here. Adding endpoints is a follow-up
  blueprint.
* Encryption — events are stored plaintext locally. Cloud sync continues
  to do its own E2E encryption pass before POSTing.
* Cloud sync — independent. Adding the local store does not change what
  ``sync.py`` ships.

Concurrency model:
* DuckDB connections are heavyweight; we keep a process-wide singleton
  connection guarded by a ``threading.Lock`` for writes. Reads are issued
  via ``.cursor()`` instances which are thread-safe.
* DuckDB allows only one *writer* process per file; multiple *readers* are
  allowed. The daemon process owns the writer; future external readers
  (e.g. a separate dashboard process per #960) will open with
  ``read_only=True``.
"""

from __future__ import annotations

import json
import logging
import os
import threading
import time
from collections import deque
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterable, Iterator

import duckdb

log = logging.getLogger("clawmetry.local_store")


# Public knobs — tuned for the common case (one daemon, one dashboard, ≤1 K
# events/s sustained on a developer laptop). Adjust via env vars only.

# Note: changed from events.db (SQLite, in 0.12.164) → events.duckdb. The
# old file is left in place if present; the new file is created fresh.
# The 0.12.164 SQLite file was live for hours at most; treating its data
# as disposable is fine.
DB_PATH = Path(
    os.environ.get(
        "CLAWMETRY_LOCAL_STORE_PATH",
        os.path.expanduser("~/.clawmetry/events.duckdb"),
    )
)

FLUSH_INTERVAL_SECS = float(os.environ.get("CLAWMETRY_LOCAL_FLUSH_SECS", "2.0"))
FLUSH_BATCH = int(os.environ.get("CLAWMETRY_LOCAL_FLUSH_BATCH", "1000"))
RING_MAX = int(os.environ.get("CLAWMETRY_LOCAL_RING_MAX", "10000"))
LOCAL_MAX_BYTES = int(
    float(os.environ.get("CLAWMETRY_LOCAL_MAX_GB", "5.0")) * 1024 * 1024 * 1024
)

SCHEMA_VERSION = 1

_DDL = [
    """
    CREATE TABLE IF NOT EXISTS events (
        id            VARCHAR PRIMARY KEY,
        node_id       VARCHAR NOT NULL,
        agent_id      VARCHAR NOT NULL DEFAULT 'main',
        session_id    VARCHAR,
        workspace_id  VARCHAR,
        event_type    VARCHAR NOT NULL,
        ts            VARCHAR NOT NULL,
        data          BLOB,
        cost_usd      DOUBLE,
        token_count   INTEGER,
        model         VARCHAR,
        created_at    BIGINT NOT NULL
    )
    """,
    "CREATE INDEX IF NOT EXISTS idx_events_ts          ON events(ts)",
    "CREATE INDEX IF NOT EXISTS idx_events_session     ON events(session_id, ts)",
    "CREATE INDEX IF NOT EXISTS idx_events_agent_ts    ON events(agent_id, ts)",
    "CREATE INDEX IF NOT EXISTS idx_events_type_ts     ON events(event_type, ts)",
    """
    CREATE TABLE IF NOT EXISTS daily_aggregates (
        agent_id      VARCHAR NOT NULL,
        workspace_id  VARCHAR,
        day           VARCHAR NOT NULL,
        cost_usd      DOUBLE DEFAULT 0,
        token_count   INTEGER DEFAULT 0,
        event_count   INTEGER DEFAULT 0,
        error_count   INTEGER DEFAULT 0,
        PRIMARY KEY (agent_id, workspace_id, day)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS schema_version (
        version    INTEGER PRIMARY KEY,
        applied_at BIGINT NOT NULL
    )
    """,
]


def _open_connection(*, read_only: bool = False) -> duckdb.DuckDBPyConnection:
    """Open a DuckDB connection at DB_PATH, creating the directory if needed."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    return duckdb.connect(str(DB_PATH), read_only=read_only)


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


def _reset_singleton_for_tests() -> None:
    """Test-only helper. Drops the cached store so the next get_store() picks
    up new env vars (DB path, flush knobs)."""
    global _store
    with _store_lock:
        if _store is not None:
            try:
                _store.stop(flush=False)
            except Exception:
                pass
        _store = None


class LocalStore:
    """Thread-safe local event store with a background batched flusher."""

    def __init__(self) -> None:
        self._ring: deque[dict[str, Any]] = deque(maxlen=RING_MAX)
        self._ring_lock = threading.Lock()
        # DuckDB connection state isn't safe across concurrent transactions.
        # All writes go through ``_write_lock``; reads issue cursors which
        # DuckDB makes thread-safe internally.
        self._write_lock = threading.Lock()
        self._dropped = 0
        self._flusher_stop = threading.Event()
        self._flusher_thread: threading.Thread | None = None
        self._last_flush_ts = time.monotonic()
        self._conn = _open_connection(read_only=False)
        self._migrate()

    def _migrate(self) -> None:
        """Apply DDL idempotently and stamp the schema version."""
        with self._write_lock:
            for stmt in _DDL:
                self._conn.execute(stmt)
            cur = self._conn.execute("SELECT MAX(version) AS v FROM schema_version")
            row = cur.fetchone()
            current = row[0] if row and row[0] is not None else 0
            if current < SCHEMA_VERSION:
                self._conn.execute(
                    "INSERT OR IGNORE INTO schema_version (version, applied_at) VALUES (?, ?)",
                    [SCHEMA_VERSION, int(time.time() * 1000)],
                )

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
            try:
                self._flush_now()
            except Exception:
                log.exception("local store: final flush on stop failed")
        # Close the underlying connection so a subsequent process can open it.
        try:
            with self._write_lock:
                self._conn.close()
        except Exception:
            pass

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
                self._dropped += 1
            self._ring.append(event)
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
        """Drain the ring into DuckDB in one transaction. Returns rows written.
        Snapshot-then-pop pattern: events stay in the ring until the COMMIT
        succeeds, so a write failure leaves them queued for the next attempt
        instead of vanishing."""
        with self._ring_lock:
            if not self._ring:
                return 0
            batch = list(self._ring)
        rows = [_event_to_row(e) for e in batch]
        with self._write_lock:
            with _txn(self._conn):
                self._conn.executemany(
                    """
                    INSERT OR IGNORE INTO events
                      (id, node_id, agent_id, session_id, workspace_id,
                       event_type, ts, data, cost_usd, token_count, model, created_at)
                    VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
                    """,
                    rows,
                )
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
        """Read events. Defaults to most recent first."""
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
        return [_row_to_event(r, _EVENT_COLS) for r in self._fetch(sql, params)]

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
              COALESCE(SUM(token_count), 0) AS token_count
            FROM events
            {where}
            GROUP BY session_id
            ORDER BY updated_at DESC
            LIMIT ?
        """
        params.append(int(limit))
        return [_row_to_dict(r, ["session_id","agent_id","started_at","updated_at",
                                  "event_count","cost_usd","token_count"])
                for r in self._fetch(sql, params)]

    def query_aggregates(
        self,
        *,
        agent_id: str | None = None,
        since: str | None = None,
        until: str | None = None,
    ) -> list[dict[str, Any]]:
        """Per-day rollup. Computed on the fly from events; columnar storage
        means this is cheap even at hundreds-of-thousands of rows."""
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
              COALESCE(SUM(token_count), 0) AS token_count
            FROM events
            {where}
            GROUP BY day, agent_id
            ORDER BY day DESC
        """
        return [_row_to_dict(r, ["day","agent_id","event_count","cost_usd","token_count"])
                for r in self._fetch(sql, params)]

    # ── ops / maintenance ──────────────────────────────────────────────

    def health(self) -> dict[str, Any]:
        """Snapshot of store state — for the /local/health endpoint and the
        dashboard footer."""
        size_bytes = DB_PATH.stat().st_size if DB_PATH.exists() else 0
        rows = self._fetch(
            "SELECT COUNT(*) AS n, MIN(ts) AS oldest, MAX(ts) AS newest FROM events",
            []
        )
        n, oldest, newest = (rows[0] if rows else (0, None, None))
        with self._ring_lock:
            ring_depth = len(self._ring)
            dropped = self._dropped
        return {
            "db_path": str(DB_PATH),
            "engine": "duckdb",
            "size_bytes": int(size_bytes),
            "size_mb": round(size_bytes / 1024 / 1024, 2),
            "size_cap_bytes": LOCAL_MAX_BYTES,
            "event_count": int(n or 0),
            "oldest_ts": oldest,
            "newest_ts": newest,
            "ring_depth": ring_depth,
            "ring_max": RING_MAX,
            "ring_dropped_total": dropped,
            "schema_version": SCHEMA_VERSION,
            "last_flush_ago_s": round(time.monotonic() - self._last_flush_ts, 2),
        }

    def vacuum(self, *, prune_to_bytes: int | None = None) -> dict[str, Any]:
        """Reclaim space. If ``prune_to_bytes`` is set (or the DB has exceeded
        ``LOCAL_MAX_BYTES``), delete oldest events first until the projected
        size fits, then run a CHECKPOINT to reclaim file size."""
        self._flush_now()
        before_size = DB_PATH.stat().st_size if DB_PATH.exists() else 0
        cap = prune_to_bytes if prune_to_bytes is not None else LOCAL_MAX_BYTES
        deleted = 0
        if before_size > cap:
            n_rows = (self._fetch("SELECT COUNT(*) FROM events", []) or [(0,)])[0][0]
            if n_rows > 0 and before_size > 0:
                bytes_per_row = before_size / n_rows
                excess_bytes = (before_size - cap) * 1.2
                rows_to_drop = int(excess_bytes / bytes_per_row) if bytes_per_row else 0
                if rows_to_drop > 0:
                    with self._write_lock:
                        with _txn(self._conn):
                            cur = self._conn.execute(
                                """
                                DELETE FROM events WHERE id IN (
                                  SELECT id FROM events ORDER BY ts ASC LIMIT ?
                                )
                                """,
                                [rows_to_drop],
                            )
                            # DuckDB returns rowcount=-1 for DELETE in some
                            # versions; if so, trust our planned count.
                            try:
                                rc = cur.rowcount
                            except Exception:
                                rc = -1
                            deleted = rc if rc is not None and rc >= 0 else rows_to_drop
        # CHECKPOINT forces DuckDB to merge WAL → main file, reclaiming space
        # similarly to SQLite VACUUM. Cheaper than full VACUUM on large DBs.
        with self._write_lock:
            try:
                self._conn.execute("CHECKPOINT")
            except Exception:
                log.exception("local store: CHECKPOINT failed")
        after_size = DB_PATH.stat().st_size if DB_PATH.exists() else 0
        return {
            "deleted_rows": int(deleted),
            "before_bytes": before_size,
            "after_bytes": after_size,
            "cap_bytes": cap,
            "reclaimed_bytes": max(0, before_size - after_size),
        }

    # ── internals ───────────────────────────────────────────────────────

    def _fetch(self, sql: str, params: list[Any]) -> list[tuple]:
        """Issue a read, returning raw row tuples. DuckDB's ``.cursor()`` is
        thread-safe; we don't take the write lock for reads. We do however
        serialise with the writer through the lock to dodge transaction-state
        edge cases — DuckDB's reader-vs-writer story within one connection is
        better with light serialisation. At our scale (hundreds of qps max)
        this costs nothing."""
        with self._write_lock:
            cur = self._conn.execute(sql, params)
            return cur.fetchall()


# ── helpers ────────────────────────────────────────────────────────────────

_EVENT_COLS = [
    "id", "node_id", "agent_id", "session_id", "workspace_id",
    "event_type", "ts", "data", "cost_usd", "token_count", "model",
]


def _event_to_row(e: dict[str, Any]) -> tuple:
    """Coerce an event dict into the column tuple for the events table.
    Unknown keys are tolerated and dropped — events come from many sources
    (jsonl parser, gateway, claude-cli adapter) with slightly different
    shapes, and the store should not be the strict-schema choke point."""
    data = e.get("data")
    if data is not None and not isinstance(data, (bytes, bytearray)):
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


def _row_to_event(row: tuple, cols: list[str]) -> dict[str, Any]:
    """Inverse of _event_to_row. Decodes ``data`` BLOB back to JSON if valid,
    else to a UTF-8 string, else leaves as None."""
    out = dict(zip(cols, row))
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


def _row_to_dict(row: tuple, cols: list[str]) -> dict[str, Any]:
    """Generic tuple-to-dict for non-event rows (sessions, aggregates)."""
    return dict(zip(cols, row))


@contextmanager
def _txn(conn: duckdb.DuckDBPyConnection) -> Iterator[None]:
    """Explicit BEGIN/COMMIT around a write block. DuckDB autocommits by
    default; this contextmanager makes batch atomicity explicit."""
    conn.execute("BEGIN")
    try:
        yield
    except Exception:
        conn.execute("ROLLBACK")
        raise
    else:
        conn.execute("COMMIT")
