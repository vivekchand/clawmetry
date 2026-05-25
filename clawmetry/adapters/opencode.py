"""OpencodeAdapter — read opencode (sst/opencode) session data from its SQLite store.

opencode (https://github.com/sst/opencode) is an open-source terminal AI
coding agent. Recent versions (verified against opencode 1.15.x) persist all
session state in a single SQLite database, NOT the older JSON ``storage/``
tree. This adapter reads that database read-only and never modifies it.

On-disk layout
--------------
``$XDG_DATA_HOME/opencode/opencode.db`` (default
``~/.local/share/opencode/opencode.db``). The ``CLAWMETRY_OPENCODE_DB`` env
var or the constructor ``db_path`` argument override the path (used in
tests). opencode also keeps a ``-wal`` / ``-shm`` sidecar; we open with the
WAL visible so freshly written sessions are not missed.

Schema (the three tables we read)::

    session(id, project_id, parent_id, slug, directory, title, version,
            time_created, time_updated, agent, model, cost,
            tokens_input, tokens_output, tokens_reasoning,
            tokens_cache_read, tokens_cache_write, ...)
    message(id, session_id, time_created, time_updated, data)   -- data = JSON
    part(id, message_id, session_id, time_created, time_updated, data)  -- JSON

``session.model`` is a JSON object, e.g.::

    {"id":"llama3.2:latest","providerID":"ollama","variant":"default"}

``session.time_created`` / ``time_updated`` are epoch MILLISECONDS.

Each ``message.data`` JSON is shaped like::

    {"role":"user"|"assistant",
     "model":{"providerID":"ollama","modelID":"llama3.2:latest"},
     "tokens":{"total":6713,"input":6684,"output":29,"reasoning":0,
               "cache":{"write":0,"read":0}},
     "time":{"created":1779741644158,"completed":1779741665586},
     "finish":"tool-calls", "parentID":"msg_..."}

Each ``part.data`` JSON has a ``type`` field — observed values:
``text``, ``reasoning``, ``tool``, ``step-start``, ``step-finish``::

    {"type":"text","text":"pong","time":{"start":...,"end":...}}
    {"type":"reasoning","text":"Okay, the user wants ..."}
    {"type":"tool","tool":"glob","callID":"call_r7p7f2c9",
     "state":{"status":"completed","input":{"pattern":"**/*.py"},
              "output":"No files found","time":{"start":...,"end":...}}}
    {"type":"step-start"}
    {"type":"step-finish","reason":"tool-calls","tokens":{...},"cost":0}

Tokens and cost ARE on disk (per session and per assistant message), so this
adapter advertises the COST capability and surfaces real token totals. For a
local Ollama provider opencode records ``cost=0`` honestly (zero-cost local
model), which we pass through unchanged.

The adapter is read-only and never modifies the opencode database.
"""
from __future__ import annotations

import glob
import json
import logging
import os
import sqlite3
from typing import Any

from .base import AgentAdapter, Capability, DetectResult, Event, Session

logger = logging.getLogger("clawmetry.adapters.opencode")

_AGENT = "opencode"

# Part types that carry no human-meaningful content; we keep them out of the
# unified event stream (they are step framing, not messages or tool activity).
_FRAMING_PART_TYPES = {"step-start", "step-finish"}


# -- helpers -----------------------------------------------------------------


def _opencode_data_dir() -> str:
    """Resolve opencode's data directory, honouring XDG_DATA_HOME."""
    xdg = os.environ.get("XDG_DATA_HOME")
    if xdg:
        return os.path.join(xdg, "opencode")
    return os.path.expanduser("~/.local/share/opencode")


def _default_db_path() -> str:
    return os.path.join(_opencode_data_dir(), "opencode.db")


def _ms_to_s(ms: Any) -> float:
    """Convert an epoch-milliseconds value to float seconds.

    opencode stores timestamps as epoch ms (integers). A value that already
    looks like seconds (< ~10^11) is passed through, so the adapter still
    behaves if a future opencode version switches units. Returns 0.0 for
    anything unparseable so callers never crash.
    """
    if ms is None:
        return 0.0
    try:
        v = float(ms)
    except (TypeError, ValueError):
        return 0.0
    if v <= 0:
        return 0.0
    # Heuristic: epoch seconds for "now" is ~1.7e9; epoch ms is ~1.7e12.
    # Anything >= 1e11 is treated as milliseconds.
    if v >= 1e11:
        return v / 1000.0
    return v


def _open_ro(db_path: str) -> sqlite3.Connection | None:
    """Open the opencode DB read-only with the WAL visible. Never raises.

    ``mode=ro`` guarantees we never take a writer lock on a database opencode
    may be actively using; ``PRAGMA query_only=ON`` is a second guard. We do
    NOT pass ``immutable=1`` because recent sessions live in the ``-wal``
    sidecar and immutable would read a stale main file. Returns None on any
    failure.
    """
    if not os.path.isfile(db_path):
        return None
    try:
        conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True, timeout=2.0)
        conn.row_factory = sqlite3.Row
        try:
            conn.execute("PRAGMA query_only=ON")
        except sqlite3.Error:
            pass
        return conn
    except sqlite3.Error as exc:
        logger.debug("Opencode: cannot open %s read-only: %s", db_path, exc)
        return None


def _has_table(conn: sqlite3.Connection, table: str) -> bool:
    try:
        row = conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name=? LIMIT 1",
            (table,),
        ).fetchone()
        return row is not None
    except sqlite3.Error:
        return False


def _loads(raw: Any) -> Any:
    """Parse a JSON column value defensively. Returns None on failure."""
    if raw is None:
        return None
    if isinstance(raw, (dict, list)):
        return raw
    try:
        return json.loads(raw)
    except (TypeError, ValueError):
        return None


def _model_display(model_field: Any) -> tuple[str, str]:
    """Return ``(model_id, provider_id)`` from a session.model JSON value.

    ``session.model`` is JSON like ``{"id":"llama3.2:latest",
    "providerID":"ollama","variant":"default"}``. Some rows may store a bare
    string. Returns ``("", "")`` when nothing usable is present.
    """
    obj = _loads(model_field)
    if isinstance(obj, dict):
        model_id = obj.get("id") or obj.get("modelID") or ""
        provider = obj.get("providerID") or obj.get("provider") or ""
        return str(model_id), str(provider)
    if isinstance(model_field, str) and model_field:
        # Bare string, possibly "provider/model".
        if "/" in model_field:
            prov, mod = model_field.split("/", 1)
            return mod, prov
        return model_field, ""
    return "", ""


def _int(val: Any) -> int:
    try:
        return int(val)
    except (TypeError, ValueError):
        return 0


# -- adapter -----------------------------------------------------------------


class OpencodeAdapter(AgentAdapter):
    """Adapter for opencode sessions stored in its SQLite database."""

    name = "opencode"
    display_name = "opencode"

    def __init__(self, db_path: str | None = None) -> None:
        # Explicit arg / env override wins; else the default XDG data DB.
        self.db_path = os.path.expanduser(
            db_path
            or os.environ.get("CLAWMETRY_OPENCODE_DB")
            or _default_db_path()
        )

    @property
    def data_dir(self) -> str:
        return os.path.dirname(self.db_path)

    # -- AgentAdapter contract -----------------------------------------------

    def detect(self) -> DetectResult:
        """Cheap detection via a single ``SELECT count(*)``. Never raises.

        ``detected`` is True when the opencode DB exists with >= 1 session, or
        when the data dir exists (installed but no sessions yet). ``running``
        is always False: opencode is a per-invocation CLI with no long-lived
        gateway we can probe cheaply.
        """
        data_dir = self.data_dir
        try:
            has_db = os.path.isfile(self.db_path)
            has_dir = os.path.isdir(data_dir)
            session_count = 0
            if has_db:
                conn = _open_ro(self.db_path)
                if conn is not None:
                    try:
                        if _has_table(conn, "session"):
                            row = conn.execute(
                                "SELECT count(*) AS n FROM session"
                            ).fetchone()
                            session_count = _int(row["n"]) if row else 0
                    except sqlite3.Error as exc:
                        logger.debug("Opencode: count(*) failed: %s", exc)
                    finally:
                        conn.close()
            detected = bool(session_count) or has_db or has_dir
            return DetectResult(
                name=self.name,
                display_name=self.display_name,
                detected=detected,
                running=False,
                workspace=data_dir,
                session_count=session_count,
                capabilities=[c.value for c in self.capabilities()],
                meta={"dbPath": self.db_path},
            )
        except Exception as exc:  # belt-and-suspenders: detect() must never raise
            logger.debug("OpencodeAdapter detect() failed: %s", exc)
            return DetectResult(
                name=self.name,
                display_name=self.display_name,
                detected=False,
                running=False,
                workspace=data_dir,
                capabilities=[c.value for c in self.capabilities()],
                meta={"error": str(exc)},
            )

    def list_sessions(self, limit: int = 100) -> list[Session]:
        """Return recent sessions, newest first. Never raises on bad data."""
        conn = _open_ro(self.db_path)
        if conn is None or not _has_table(conn, "session"):
            if conn is not None:
                conn.close()
            return []
        try:
            return self._sessions_from_conn(conn, limit)
        except sqlite3.Error as exc:
            logger.warning("Opencode: list_sessions failed: %s", exc)
            return []
        finally:
            conn.close()

    def _sessions_from_conn(
        self, conn: sqlite3.Connection, limit: int
    ) -> list[Session]:
        # Discover which optional columns exist so we degrade gracefully on an
        # older/newer schema (token/cost columns were added over time).
        cols = self._session_columns(conn)
        want = [
            "id", "slug", "title", "parent_id", "agent", "model", "directory",
            "time_created", "time_updated", "cost",
            "tokens_input", "tokens_output", "tokens_reasoning",
            "tokens_cache_read", "tokens_cache_write",
        ]
        select_cols = [c for c in want if c in cols]
        if "id" not in select_cols:
            return []
        sql = (
            "SELECT " + ", ".join(select_cols)
            + " FROM session ORDER BY time_updated DESC, time_created DESC LIMIT ?"
        )
        try:
            rows = conn.execute(sql, (max(1, limit),)).fetchall()
        except sqlite3.Error as exc:
            logger.debug("Opencode: session select failed: %s", exc)
            return []

        # Per-session message count in one grouped query (avoids N+1).
        counts = self._message_counts(conn)

        sessions: list[Session] = []
        for row in rows:
            try:
                sess = self._session_from_row(row, counts)
            except Exception as exc:
                logger.warning("Opencode: skipping bad session row: %s", exc)
                continue
            if sess is not None:
                sessions.append(sess)
        return sessions

    def _session_columns(self, conn: sqlite3.Connection) -> set[str]:
        try:
            info = conn.execute("PRAGMA table_info(session)").fetchall()
            return {r["name"] for r in info}
        except sqlite3.Error:
            return set()

    def _message_counts(self, conn: sqlite3.Connection) -> dict[str, int]:
        if not _has_table(conn, "message"):
            return {}
        try:
            rows = conn.execute(
                "SELECT session_id, count(*) AS n FROM message GROUP BY session_id"
            ).fetchall()
            return {r["session_id"]: _int(r["n"]) for r in rows}
        except sqlite3.Error:
            return {}

    def _session_from_row(
        self, row: sqlite3.Row, counts: dict[str, int]
    ) -> Session | None:
        keys = row.keys()

        def g(key: str, default: Any = None) -> Any:
            return row[key] if key in keys else default

        sid = g("id")
        if not sid:
            return None

        model_id, provider = _model_display(g("model"))
        started_at = _ms_to_s(g("time_created"))
        updated_at = _ms_to_s(g("time_updated"))

        input_tokens = _int(g("tokens_input"))
        output_tokens = _int(g("tokens_output"))
        reasoning_tokens = _int(g("tokens_reasoning"))
        cache_read = _int(g("tokens_cache_read"))
        cache_write = _int(g("tokens_cache_write"))
        total_tokens = (
            input_tokens + output_tokens + reasoning_tokens
            + cache_read + cache_write
        )

        # cost is a REAL column; opencode records 0.0 for local/free models.
        cost_raw = g("cost")
        cost_usd: float | None
        if cost_raw is None:
            cost_usd = None
        else:
            try:
                cost_usd = float(cost_raw)
            except (TypeError, ValueError):
                cost_usd = None

        title = (g("title") or "").strip()
        slug = (g("slug") or "").strip()

        return Session(
            agent=_AGENT,
            id=str(sid),
            title=title,
            display_name=title or slug or str(sid),
            model=model_id,
            source=provider,
            started_at=started_at,
            ended_at=updated_at or None,
            parent_id=(str(g("parent_id")) if g("parent_id") else None),
            message_count=counts.get(str(sid), 0),
            total_tokens=total_tokens,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cache_read_tokens=cache_read,
            cache_write_tokens=cache_write,
            reasoning_tokens=reasoning_tokens,
            cost_usd=cost_usd,
            cost_status="" if cost_usd is not None else "unavailable",
            extra={
                "slug": slug,
                "agentMode": g("agent") or "",
                "directory": g("directory") or "",
                "providerID": provider,
            },
        )

    def list_events(self, session_id: str, limit: int = 500) -> list[Event]:
        """Parse one session's messages + parts into unified events.

        Events are returned in chronological order. Each opencode ``part``
        becomes one Event:
          - ``text``      -> message (role from the parent message)
          - ``reasoning`` -> thinking
          - ``tool``      -> tool_call, plus a tool_result when the tool state
                             carries output / an error
        ``step-start`` / ``step-finish`` framing parts are dropped.
        """
        conn = _open_ro(self.db_path)
        if conn is None or not _has_table(conn, "part"):
            if conn is not None:
                conn.close()
            return []
        try:
            return self._events_from_conn(conn, session_id, limit)
        except sqlite3.Error as exc:
            logger.warning("Opencode: list_events failed: %s", exc)
            return []
        finally:
            conn.close()

    def _events_from_conn(
        self, conn: sqlite3.Connection, session_id: str, limit: int
    ) -> list[Event]:
        # Map message_id -> role so each part can inherit its message's role
        # without a join (one cheap lookup).
        roles: dict[str, str] = {}
        if _has_table(conn, "message"):
            try:
                mrows = conn.execute(
                    "SELECT id, data FROM message WHERE session_id=?",
                    (session_id,),
                ).fetchall()
            except sqlite3.Error:
                mrows = []
            for mrow in mrows:
                mdata = _loads(mrow["data"]) or {}
                if isinstance(mdata, dict):
                    roles[mrow["id"]] = str(mdata.get("role") or "")

        try:
            prows = conn.execute(
                "SELECT id, message_id, time_created, data FROM part "
                "WHERE session_id=? ORDER BY time_created ASC, id ASC",
                (session_id,),
            ).fetchall()
        except sqlite3.Error as exc:
            logger.debug("Opencode: part select failed: %s", exc)
            return []

        events: list[Event] = []
        seq = 0
        for prow in prows:
            if len(events) >= limit:
                break
            data = _loads(prow["data"])
            if not isinstance(data, dict):
                continue
            ptype = data.get("type") or ""
            if ptype in _FRAMING_PART_TYPES:
                continue
            role = roles.get(prow["message_id"], "")
            ts = _ms_to_s(prow["time_created"])

            if ptype == "text":
                text = data.get("text")
                if not isinstance(text, str):
                    text = "" if text is None else json.dumps(text)
                seq += 1
                events.append(Event(
                    agent=_AGENT,
                    session_id=session_id,
                    id=prow["id"] or f"{session_id}:{seq}",
                    type="message",
                    ts=ts,
                    role=role or "assistant",
                    content=text,
                ))
            elif ptype == "reasoning":
                text = data.get("text")
                if not isinstance(text, str):
                    text = "" if text is None else json.dumps(text)
                seq += 1
                events.append(Event(
                    agent=_AGENT,
                    session_id=session_id,
                    id=prow["id"] or f"{session_id}:{seq}",
                    type="thinking",
                    ts=ts,
                    role=role or "assistant",
                    content=text,
                ))
            elif ptype == "tool":
                self._append_tool_events(events, data, session_id, prow, ts, role)
            # Any other (future) part type is ignored defensively.
        return events

    def _append_tool_events(
        self,
        events: list[Event],
        data: dict[str, Any],
        session_id: str,
        prow: sqlite3.Row,
        ts: float,
        role: str,
    ) -> None:
        """Turn one ``tool`` part into a tool_call (+ tool_result if any)."""
        tool_name = data.get("tool") or "unknown"
        call_id = data.get("callID") or ""
        state = data.get("state") if isinstance(data.get("state"), dict) else {}
        status = state.get("status") or ""
        tool_input = state.get("input")
        base_id = prow["id"] or f"{session_id}:{call_id}"

        events.append(Event(
            agent=_AGENT,
            session_id=session_id,
            id=base_id,
            type="tool_call",
            ts=ts,
            role=role or "assistant",
            tool_name=str(tool_name),
            tool_calls=[{
                "id": call_id,
                "name": str(tool_name),
                "arguments": tool_input,
            }],
            extra={"status": status} if status else {},
        ))

        # A completed/errored tool carries its result inline; emit it as a
        # separate tool_result event so the timeline shows the response.
        output = state.get("output")
        error = state.get("error")
        if output is not None or error is not None:
            content = error if error is not None else output
            if not isinstance(content, str):
                content = json.dumps(content)
            events.append(Event(
                agent=_AGENT,
                session_id=session_id,
                id=base_id + ":result",
                type="tool_result",
                ts=ts,
                role="tool",
                content=content,
                tool_name=str(tool_name),
                extra={
                    "status": status,
                    "callId": call_id,
                    "isError": error is not None,
                },
            ))

    def capabilities(self) -> set[Capability]:
        # SESSIONS + EVENTS + COST: opencode records per-session and
        # per-message token totals and a cost column on disk, so COST is
        # honest (real numbers, including a real 0.0 for local Ollama models).
        return {Capability.SESSIONS, Capability.EVENTS, Capability.COST}
