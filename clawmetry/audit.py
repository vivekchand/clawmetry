"""
clawmetry/audit.py — append-only audit log.

A bounded, sqlite-backed audit log for Enterprise installs. Callers record
significant events (license activation, config changes, approval decisions,
admin overrides, …) via :func:`record_audit`; the
:mod:`routes.audit` endpoint exposes them, gated on the ``audit_logs``
entitlement.

Design choices
--------------
* **Append-only**. No update / delete API — once written, an entry stays.
* **SQLite**, not DuckDB. The audit log is small and write-cheap; using
  SQLite avoids contending with the daemon's DuckDB writer lock and keeps the
  audit store independent of the main observability path (so a corrupt
  ``events.duckdb`` never takes the audit log down with it).
* **Never raises**. ``record_audit`` always returns silently — audit
  recording must never block or break the caller's primary action.
* **Path is overridable** via ``CLAWMETRY_AUDIT_DB`` for tests / multi-tenant
  scenarios.
"""

from __future__ import annotations

import json
import logging
import os
import sqlite3
import threading
import time
from typing import Any, Iterable

logger = logging.getLogger("clawmetry.audit")

_DEFAULT_PATH = os.path.expanduser("~/.clawmetry/audit.db")
_lock = threading.Lock()
_initialised: set[str] = set()


def _path() -> str:
    return os.environ.get("CLAWMETRY_AUDIT_DB", "").strip() or _DEFAULT_PATH


def _connect() -> sqlite3.Connection:
    p = _path()
    os.makedirs(os.path.dirname(p), exist_ok=True)
    conn = sqlite3.connect(p, timeout=5.0)
    conn.row_factory = sqlite3.Row
    return conn


def _ensure_schema(conn: sqlite3.Connection) -> None:
    p = _path()
    if p in _initialised:
        return
    with _lock:
        if p in _initialised:
            return
        conn.execute(
            """CREATE TABLE IF NOT EXISTS audit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ts REAL NOT NULL,
                event_type TEXT NOT NULL,
                actor TEXT NOT NULL DEFAULT '',
                target TEXT NOT NULL DEFAULT '',
                details TEXT NOT NULL DEFAULT '{}'
            )"""
        )
        conn.execute("CREATE INDEX IF NOT EXISTS idx_audit_ts ON audit_log(ts DESC)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_audit_type ON audit_log(event_type, ts DESC)")
        conn.commit()
        _initialised.add(p)


def record_audit(
    event_type: str,
    actor: str = "",
    target: str = "",
    details: dict | None = None,
) -> None:
    """Append a single audit entry. Never raises — a failed audit write must
    never block the caller's main action."""
    if not event_type:
        return
    try:
        conn = _connect()
        try:
            _ensure_schema(conn)
            conn.execute(
                "INSERT INTO audit_log (ts, event_type, actor, target, details) "
                "VALUES (?, ?, ?, ?, ?)",
                (
                    time.time(),
                    event_type[:128],
                    (actor or "")[:128],
                    (target or "")[:256],
                    json.dumps(details or {}, separators=(",", ":"))[:4096],
                ),
            )
            conn.commit()
        finally:
            conn.close()
    except Exception as exc:  # pragma: no cover - defensive
        logger.warning("audit: record failed (%s): %s", event_type, exc)


def read_audit_log(
    limit: int = 200,
    event_type: str | None = None,
    since: float | None = None,
) -> list[dict]:
    """Return recent audit entries, newest first. Never raises."""
    limit = max(1, min(int(limit or 200), 5000))
    try:
        conn = _connect()
        try:
            _ensure_schema(conn)
            sql = "SELECT id, ts, event_type, actor, target, details FROM audit_log"
            args: list[Any] = []
            where: list[str] = []
            if event_type:
                where.append("event_type = ?")
                args.append(event_type)
            if since is not None:
                where.append("ts >= ?")
                args.append(float(since))
            if where:
                sql += " WHERE " + " AND ".join(where)
            sql += " ORDER BY id DESC LIMIT ?"
            args.append(limit)
            rows = list(conn.execute(sql, args))
        finally:
            conn.close()
        out: list[dict] = []
        for r in rows:
            try:
                details = json.loads(r["details"]) if r["details"] else {}
            except Exception:
                details = {"_raw": str(r["details"])[:512]}
            out.append({
                "id": r["id"],
                "ts": r["ts"],
                "event_type": r["event_type"],
                "actor": r["actor"],
                "target": r["target"],
                "details": details,
            })
        return out
    except Exception as exc:  # pragma: no cover - defensive
        logger.warning("audit: read failed: %s", exc)
        return []


def event_types() -> list[str]:
    """Distinct event types recorded so far — useful for UI filters."""
    try:
        conn = _connect()
        try:
            _ensure_schema(conn)
            rows = list(conn.execute(
                "SELECT event_type, COUNT(*) AS n FROM audit_log GROUP BY event_type ORDER BY n DESC"
            ))
        finally:
            conn.close()
        return [{"event_type": r["event_type"], "count": int(r["n"])} for r in rows]
    except Exception:
        return []
