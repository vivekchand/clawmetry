"""HermesAdapter — read Hermes Agent data from ``~/.hermes/state.db``.

Hermes (https://github.com/NousResearch/hermes-agent) is an OpenClaw-
descendant agent; the author even ships a ``hermes claw migrate`` CLI.
Its architecture mirrors OpenClaw's (gateway + cron + skills + sessions
+ subagents + 20+ messaging platforms), but its session store is a
normalized SQLite database — ``sessions`` + ``messages`` tables — rather
than OpenClaw's append-only per-session JSONL files.

The SQLite schema pre-computes tokens + cost per session, so this
adapter is actually *shorter* than OpenClawAdapter. The trade-off is
live-tail strategy: Hermes exposes no local gateway port, so we poll
SQLite on ``stream_events()`` (3-second cadence — good enough for a
dashboard, cheap on a WAL-mode db).

Concurrency: Hermes actively writes ``state.db`` while this adapter
reads. We always open read-only via ``sqlite3.connect(..., uri=True)``
with ``mode=ro`` and ``immutable=0``; on a lock we retry once after
100 ms. Never use ``immutable=1`` — it caches the file and the adapter
would stop seeing new writes.
"""
from __future__ import annotations

import json
import logging
import os
import sqlite3
import threading
import time
from typing import Iterator, List, Optional, Set

from .base import AgentAdapter, Capability, DetectResult, Event, Session

logger = logging.getLogger("clawmetry.adapters.hermes")


def _hermes_home() -> str:
    return os.environ.get("HERMES_HOME") or os.path.expanduser("~/.hermes")


def _state_db_path(home: Optional[str] = None) -> str:
    return os.path.join(home or _hermes_home(), "state.db")


def _open_ro(db_path: str) -> sqlite3.Connection:
    """Open the Hermes SQLite in read-only mode, retrying once on a lock."""
    uri = f"file:{db_path}?mode=ro"
    for attempt in range(2):
        try:
            conn = sqlite3.connect(uri, uri=True, timeout=2.0)
            conn.row_factory = sqlite3.Row
            return conn
        except sqlite3.OperationalError as exc:
            if "locked" in str(exc).lower() and attempt == 0:
                time.sleep(0.1)
                continue
            raise


_SESSION_COLS = (
    "id, source, user_id, model, parent_session_id, started_at, ended_at, "
    "end_reason, message_count, input_tokens, output_tokens, "
    "cache_read_tokens, cache_write_tokens, reasoning_tokens, "
    "estimated_cost_usd, actual_cost_usd, cost_status, cost_source, title"
)


def _row_to_session(row: sqlite3.Row) -> Session:
    input_tokens = int(row["input_tokens"] or 0)
    output_tokens = int(row["output_tokens"] or 0)
    cache_read = int(row["cache_read_tokens"] or 0)
    cache_write = int(row["cache_write_tokens"] or 0)
    reasoning = int(row["reasoning_tokens"] or 0)
    # Prefer actual over estimated, matching Hermes's own cost_status semantics.
    actual = row["actual_cost_usd"]
    estimated = row["estimated_cost_usd"]
    cost_usd = actual if actual is not None else estimated
    return Session(
        agent="hermes",
        id=row["id"],
        title=row["title"] or "",
        display_name=row["title"] or row["id"],
        model=row["model"] or "",
        source=row["source"] or "",
        started_at=float(row["started_at"] or 0.0),
        ended_at=float(row["ended_at"]) if row["ended_at"] is not None else None,
        parent_id=row["parent_session_id"],
        message_count=int(row["message_count"] or 0),
        total_tokens=input_tokens + output_tokens,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        cache_read_tokens=cache_read,
        cache_write_tokens=cache_write,
        reasoning_tokens=reasoning,
        cost_usd=float(cost_usd) if cost_usd is not None else None,
        cost_status=row["cost_status"] or "",
        end_reason=row["end_reason"] or "",
        extra={
            "userId": row["user_id"] or "",
            "costSource": row["cost_source"] or "",
        },
    )


def _row_to_event(row: sqlite3.Row) -> Event:
    tool_calls_raw = row["tool_calls"]
    tool_calls: list = []
    if tool_calls_raw:
        try:
            parsed = json.loads(tool_calls_raw)
            if isinstance(parsed, list):
                tool_calls = parsed
        except (json.JSONDecodeError, TypeError):
            logger.debug(f"Hermes event {row['id']}: tool_calls not JSON")
    event_type = "tool_call" if tool_calls or row["tool_name"] else "message"
    return Event(
        agent="hermes",
        session_id=row["session_id"],
        id=str(row["id"]),
        type=event_type,
        ts=float(row["timestamp"] or 0.0),
        role=row["role"] or "",
        content=row["content"] or "",
        tool_name=row["tool_name"] or "",
        tool_calls=tool_calls,
        tokens=int(row["token_count"] or 0),
        extra={
            "finishReason": row["finish_reason"] or "",
            "toolCallId": row["tool_call_id"] or "",
        },
    )


class HermesAdapter(AgentAdapter):
    name = "hermes"
    display_name = "Hermes Agent"

    # Polling cadence for stream_events(). 3s keeps WAL-check cheap while
    # feeling live enough for a dashboard.
    _poll_interval = 3.0

    def __init__(self) -> None:
        self._stream_stop = threading.Event()

    def _db(self) -> Optional[sqlite3.Connection]:
        path = _state_db_path()
        if not os.path.isfile(path):
            return None
        try:
            return _open_ro(path)
        except sqlite3.Error as exc:
            logger.debug(f"Hermes DB open failed: {exc}")
            return None

    def detect(self) -> DetectResult:
        home = _hermes_home()
        db_path = _state_db_path(home)
        if not os.path.isfile(db_path):
            return DetectResult(
                name=self.name,
                display_name=self.display_name,
                detected=False,
                workspace=home,
                capabilities=[c.value for c in self.capabilities()],
            )
        session_count = 0
        try:
            with _open_ro(db_path) as conn:
                cur = conn.execute("SELECT COUNT(*) AS n FROM sessions")
                session_count = int(cur.fetchone()["n"])
        except sqlite3.Error as exc:
            logger.debug(f"Hermes detect count failed: {exc}")
        return DetectResult(
            name=self.name,
            display_name=self.display_name,
            detected=True,
            running=self._gateway_running(home),
            workspace=home,
            session_count=session_count,
            capabilities=[c.value for c in self.capabilities()],
            meta={"dbPath": db_path},
        )

    @staticmethod
    def _gateway_running(home: str) -> bool:
        """Best-effort liveness check — gateway.pid file + /proc check.

        Hermes writes ``gateway.pid`` when its gateway process starts and
        removes it on shutdown. If the PID is valid and the process is
        alive, we call it running.
        """
        pid_file = os.path.join(home, "gateway.pid")
        if not os.path.isfile(pid_file):
            return False
        try:
            with open(pid_file) as f:
                raw = f.read().strip().split()[0]
            pid = int(raw)
        except (OSError, ValueError):
            return False
        try:
            os.kill(pid, 0)
            return True
        except (OSError, ProcessLookupError):
            return False

    def list_sessions(self, limit: int = 100) -> List[Session]:
        conn = self._db()
        if conn is None:
            return []
        try:
            cur = conn.execute(
                f"SELECT {_SESSION_COLS} FROM sessions "
                "ORDER BY started_at DESC LIMIT ?",
                (limit,),
            )
            return [_row_to_session(row) for row in cur.fetchall()]
        except sqlite3.Error as exc:
            logger.warning(f"Hermes list_sessions failed: {exc}")
            return []
        finally:
            conn.close()

    def read_session(self, session_id: str) -> Optional[Session]:
        conn = self._db()
        if conn is None:
            return None
        try:
            cur = conn.execute(
                f"SELECT {_SESSION_COLS} FROM sessions WHERE id = ?",
                (session_id,),
            )
            row = cur.fetchone()
            return _row_to_session(row) if row else None
        except sqlite3.Error as exc:
            logger.warning(f"Hermes read_session failed: {exc}")
            return None
        finally:
            conn.close()

    def list_events(self, session_id: str, limit: int = 500) -> List[Event]:
        conn = self._db()
        if conn is None:
            return []
        try:
            cur = conn.execute(
                "SELECT id, session_id, role, content, tool_call_id, "
                "tool_calls, tool_name, timestamp, token_count, "
                "finish_reason FROM messages WHERE session_id = ? "
                "ORDER BY timestamp ASC LIMIT ?",
                (session_id, limit),
            )
            return [_row_to_event(row) for row in cur.fetchall()]
        except sqlite3.Error as exc:
            logger.warning(f"Hermes list_events failed: {exc}")
            return []
        finally:
            conn.close()

    def stream_events(self) -> Iterator[Event]:
        """Yield new Hermes messages as they are written.

        Polls ``max(id) FROM messages`` every ``_poll_interval`` seconds.
        Stops when ``_stream_stop`` is set by ``stop_stream()`` so the
        dashboard can cleanly terminate SSE sessions.
        """
        last_id = 0
        # Initialise last_id so we don't replay the entire history on first poll.
        conn = self._db()
        if conn is None:
            return
        try:
            cur = conn.execute("SELECT COALESCE(MAX(id), 0) AS m FROM messages")
            last_id = int(cur.fetchone()["m"])
        except sqlite3.Error:
            pass
        finally:
            conn.close()

        while not self._stream_stop.is_set():
            conn = self._db()
            if conn is None:
                time.sleep(self._poll_interval)
                continue
            try:
                cur = conn.execute(
                    "SELECT id, session_id, role, content, tool_call_id, "
                    "tool_calls, tool_name, timestamp, token_count, "
                    "finish_reason FROM messages WHERE id > ? "
                    "ORDER BY id ASC",
                    (last_id,),
                )
                for row in cur.fetchall():
                    last_id = max(last_id, int(row["id"]))
                    yield _row_to_event(row)
            except sqlite3.Error as exc:
                logger.warning(f"Hermes stream poll failed: {exc}")
            finally:
                conn.close()
            if self._stream_stop.wait(self._poll_interval):
                break

    def stop_stream(self) -> None:
        self._stream_stop.set()

    def capabilities(self) -> Set[Capability]:
        # Deliberately narrow for v1: Hermes exposes more data (skills
        # dir, cron tick files, memory markdown) but hooking each one
        # into ClawMetry's tabs needs per-feature engineering. Ship the
        # core flow first, widen once the UI layer lands in PR 3.
        return {
            Capability.SESSIONS,
            Capability.EVENTS,
            Capability.COST,
            Capability.SUBAGENTS,
        }

    def running(self) -> bool:
        return self._gateway_running(_hermes_home())
