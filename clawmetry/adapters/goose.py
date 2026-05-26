"""GooseAdapter — read Goose (Block / block/goose) sessions from its SQLite store.

Goose (https://github.com/block/goose) is Block's open-source agent (Rust
CLI + desktop). It does NOT share OpenClaw's session layout: as of Goose
1.35.0 every session lives in a SINGLE shared SQLite database, not in
per-session JSONL files. Older / desktop builds wrote JSONL under a
``sessions/`` dir; this adapter targets the current SQLite store, which is
what a fresh ``goose`` install writes.

On-disk layout
--------------
``$XDG_DATA_HOME/goose/sessions/sessions.db`` (default on macOS/Linux
``~/.local/share/goose/sessions/sessions.db``). VERIFIED against a real
Goose 1.35.0 install by running ``goose run`` against local Ollama and
reading the DB it wrote (``schema_version`` = 13). Two relevant tables:

``sessions`` (one row per conversation)::

    id                         TEXT PRIMARY KEY     -- e.g. "20260525_1"
    name                       TEXT                 -- model-generated title
    description                TEXT
    session_type               TEXT  ('user' | 'scheduled' | ...)
    working_dir                TEXT
    created_at / updated_at    TIMESTAMP  ("2026-05-25 19:51:12", local, no TZ)
    total_tokens               INTEGER              -- REAL usage, populated
    input_tokens               INTEGER
    output_tokens              INTEGER
    accumulated_total_tokens   INTEGER
    accumulated_cost           REAL                 -- NULL for local providers
    provider_name              TEXT  ('ollama', 'anthropic', ...)
    model_config_json          TEXT  -> {"model_name": "llama3.2", ...}
    goose_mode                 TEXT  ('auto' | ...)

``messages`` (one row per turn)::

    id                  INTEGER PRIMARY KEY AUTOINCREMENT
    message_id          TEXT                       -- "msg_..." / "chatcmpl-747"
    session_id          TEXT  REFERENCES sessions(id)
    role                TEXT  ('user' | 'assistant')
    content_json        TEXT  -- JSON array of content blocks (see below)
    created_timestamp   INTEGER  -- epoch SECONDS
    tokens              INTEGER  -- per-message, observed NULL (use session totals)

``content_json`` is a JSON ARRAY of content blocks. Observed block shapes::

    {"type": "text", "text": "..."}
    {"type": "toolRequest",  "id": "call_x", "toolCall":  {"status": "success",
        "value": {"name": "tree", "arguments": {...}}},
        "_meta": {"goose_extension": "developer"}}
    {"type": "toolResponse", "id": "call_x", "toolResult": {"status": "success",
        "value": {"content": [{"type": "text", "text": "..."}], "isError": false}}}

Tool RESPONSE blocks arrive on a ``role=user`` message (the runtime feeds
tool output back as a user turn) — we classify by block type, not row role,
so a tool result is emitted as a ``tool_result`` event regardless.

Tokens + cost
-------------
Unlike PicoClaw/NanoClaw, Goose DOES record real token usage on disk
(``sessions.total_tokens`` etc.), so we surface those AND advertise the COST
capability. ``accumulated_cost`` is populated only for paid providers; for
local Ollama it is NULL, so ``cost_usd`` is honestly ``None`` there (tokens
are real, USD simply was not computed). Per-message ``tokens`` was observed
NULL in real captures, so event-level ``tokens`` stay 0 and the session
totals carry the truth.

Read-only contract
------------------
The Goose runtime owns ``sessions.db`` (it runs in WAL mode — note the
``.db-wal`` / ``.db-shm`` sidecars). We ALWAYS open it read-only
(``file:<path>?mode=ro``, NOT ``immutable=1`` so we can still see committed
WAL data), always close the connection, and never raise out of any public
method — failures are logged and degrade to empty.
"""
from __future__ import annotations

import json
import logging
import os
import sqlite3
from datetime import datetime, timezone
from typing import Any

from .base import AgentAdapter, Capability, DetectResult, Event, Session

logger = logging.getLogger("clawmetry.adapters.goose")

_AGENT = "goose"


# -- discovery ---------------------------------------------------------------


def _default_db_path() -> str:
    """Resolve Goose's sessions.db, honouring XDG_DATA_HOME like Goose does.

    Goose uses the platform data dir: ``$XDG_DATA_HOME/goose`` (falling back
    to ``~/.local/share/goose``) on macOS/Linux. The sessions store lives at
    ``<data>/sessions/sessions.db``.
    """
    xdg = os.environ.get("XDG_DATA_HOME")
    base = xdg if xdg else os.path.expanduser("~/.local/share")
    return os.path.join(base, "goose", "sessions", "sessions.db")


# -- helpers -----------------------------------------------------------------


def _parse_ts(ts: Any) -> float:
    """Parse a Goose timestamp to float epoch seconds. Never raises.

    Goose stores two flavours:
      * ``messages.created_timestamp`` — an INTEGER epoch in SECONDS.
      * ``sessions.created_at`` / ``updated_at`` — a TEXT timestamp like
        ``"2026-05-25 19:51:12"`` (SQLite ``CURRENT_TIMESTAMP``: UTC,
        space-separated, no timezone).
    Returns 0.0 for anything unparseable so callers never have to guard.
    """
    if ts is None:
        return 0.0
    if isinstance(ts, (int, float)):
        return float(ts)
    try:
        s = str(ts).strip()
        if not s:
            return 0.0
        # Numeric-looking string -> epoch seconds.
        try:
            return float(s)
        except ValueError:
            pass
        # SQLite "YYYY-MM-DD HH:MM:SS" -> ISO; treat naive as UTC.
        iso = s.replace(" ", "T", 1)
        if iso.endswith("Z"):
            iso = iso[:-1] + "+00:00"
        dt = datetime.fromisoformat(iso)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.timestamp()
    except (ValueError, AttributeError, TypeError):
        return 0.0


def _open_ro(db_path: str) -> sqlite3.Connection | None:
    """Open Goose's sessions.db read-only. Returns None on failure.

    We use ``mode=ro`` (NOT ``immutable=1``) because the live runtime writes
    in WAL mode; immutable would hide committed-but-not-checkpointed data.
    read-only takes no writer lock, so we never perturb the runtime's files.
    """
    if not os.path.isfile(db_path):
        return None
    try:
        conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True, timeout=2.0)
        conn.row_factory = sqlite3.Row
        return conn
    except sqlite3.Error as exc:
        logger.debug("Goose: cannot open %s read-only: %s", db_path, exc)
        return None


def _model_from_config(model_config_json: Any, provider_name: Any) -> str:
    """Pull the display model name out of ``sessions.model_config_json``.

    The column is a JSON string like ``{"model_name":"llama3.2",...}``.
    Falls back to the provider name, then "". Never raises.
    """
    if isinstance(model_config_json, str) and model_config_json.strip():
        try:
            cfg = json.loads(model_config_json)
            if isinstance(cfg, dict):
                mn = cfg.get("model_name") or cfg.get("model")
                if isinstance(mn, str) and mn:
                    return mn
        except (json.JSONDecodeError, TypeError, ValueError):
            pass
    return provider_name if isinstance(provider_name, str) else ""


def _int_or_zero(val: Any) -> int:
    """Coerce a possibly-NULL numeric column to a non-negative int."""
    if isinstance(val, bool):
        return int(val)
    if isinstance(val, (int, float)):
        try:
            return max(0, int(val))
        except (ValueError, OverflowError):
            return 0
    return 0


def _decode_blocks(content_json: Any) -> list[dict[str, Any]]:
    """Decode a ``messages.content_json`` value into a list of block dicts.

    Defensive: returns [] for NULL / non-JSON / non-list payloads. A bare
    string payload is wrapped as a single text block so older shapes still
    surface text.
    """
    if content_json is None:
        return []
    raw = content_json if isinstance(content_json, str) else str(content_json)
    try:
        obj = json.loads(raw)
    except (json.JSONDecodeError, TypeError, ValueError):
        return [{"type": "text", "text": raw}] if raw else []
    if isinstance(obj, list):
        return [b for b in obj if isinstance(b, dict)]
    if isinstance(obj, dict):
        return [obj]
    if isinstance(obj, str):
        return [{"type": "text", "text": obj}] if obj else []
    return []


def _text_of_blocks(blocks: list[dict[str, Any]]) -> str:
    """Join the text of all ``text`` blocks in a content array."""
    parts = [
        b.get("text")
        for b in blocks
        if b.get("type") == "text" and isinstance(b.get("text"), str)
    ]
    return "\n".join(p for p in parts if p)


def _tool_result_text(tool_result: Any) -> str:
    """Extract human-readable text from a ``toolResponse.toolResult`` value.

    Real shape: ``{"status":"success","value":{"content":[{"type":"text",
    "text":...}],"isError":false}}``. Falls back to a JSON dump so nothing is
    silently lost.
    """
    if not isinstance(tool_result, dict):
        return ""
    value = tool_result.get("value")
    if isinstance(value, dict):
        content = value.get("content")
        if isinstance(content, list):
            parts = [
                c.get("text")
                for c in content
                if isinstance(c, dict) and isinstance(c.get("text"), str)
            ]
            if parts:
                return "\n".join(p for p in parts if p)
    try:
        return json.dumps(tool_result)
    except (TypeError, ValueError):
        return ""


# -- adapter -----------------------------------------------------------------


class GooseAdapter(AgentAdapter):
    """Adapter for Goose sessions stored in its shared SQLite database.

    ``db_path`` defaults to Goose's real store (XDG-aware) but is a
    constructor arg so tests and non-default installs can point it anywhere.
    """

    name = "goose"
    display_name = "Goose"

    def __init__(self, db_path: str | None = None) -> None:
        self._db_path = db_path or _default_db_path()

    @property
    def db_path(self) -> str:
        return self._db_path

    # -- AgentAdapter contract -----------------------------------------------

    def detect(self) -> DetectResult:
        """Cheap detection. Never raises.

        ``detected`` is True when the sessions DB exists with >= 1 session
        row. ``running`` is always False — Goose has no gateway we tap.
        """
        db_path = self._db_path
        workspace = os.path.dirname(os.path.dirname(db_path))  # .../goose
        try:
            if not os.path.isfile(db_path):
                return DetectResult(
                    name=self.name,
                    display_name=self.display_name,
                    detected=False,
                    workspace=workspace,
                    capabilities=[c.value for c in self.capabilities()],
                    meta={"dbPath": db_path},
                )
            session_count = self._count_sessions()
            return DetectResult(
                name=self.name,
                display_name=self.display_name,
                detected=session_count > 0,
                running=False,
                workspace=workspace,
                session_count=session_count,
                capabilities=[c.value for c in self.capabilities()],
                meta={"dbPath": db_path},
            )
        except Exception as exc:  # detect() must never raise
            logger.debug("Goose detect() failed: %s", exc)
            return DetectResult(
                name=self.name,
                display_name=self.display_name,
                detected=False,
                workspace=workspace,
                capabilities=[c.value for c in self.capabilities()],
                meta={"error": str(exc)},
            )

    def _count_sessions(self) -> int:
        conn = _open_ro(self._db_path)
        if conn is None:
            return 0
        try:
            cur = conn.execute("SELECT count(*) FROM sessions")
            row = cur.fetchone()
            return int(row[0]) if row and row[0] is not None else 0
        except sqlite3.Error as exc:
            logger.debug("Goose: count sessions failed: %s", exc)
            return 0
        finally:
            conn.close()

    def list_sessions(self, limit: int = 100) -> list[Session]:
        """Return recent sessions, newest first. Never raises on a bad row."""
        conn = _open_ro(self._db_path)
        if conn is None:
            return []
        sessions: list[Session] = []
        try:
            cur = conn.execute(
                "SELECT id, name, description, session_type, working_dir, "
                "created_at, updated_at, total_tokens, input_tokens, "
                "output_tokens, accumulated_total_tokens, accumulated_cost, "
                "provider_name, model_config_json, goose_mode "
                "FROM sessions ORDER BY updated_at DESC LIMIT ?",
                (max(1, int(limit)),),
            )
            for row in cur.fetchall():
                try:
                    sess = self._session_from_row(row)
                except Exception as exc:
                    logger.warning("Goose: skipping bad session row: %s", exc)
                    continue
                if sess is not None:
                    sessions.append(sess)
        except sqlite3.Error as exc:
            logger.warning("Goose list_sessions query failed: %s", exc)
            return []
        finally:
            conn.close()

        # Sort by logical activity time, newest first. We re-sort on the
        # parsed timestamp (not the raw SQL order) so a session whose
        # updated_at parsed oddly still orders sensibly.
        sessions.sort(key=lambda s: s.ended_at or s.started_at or 0.0, reverse=True)
        return sessions[:limit]

    def _session_from_row(self, row: sqlite3.Row) -> Session | None:
        keys = row.keys()
        sid = row["id"]
        if sid is None:
            return None
        sid = str(sid)

        name = row["name"] if "name" in keys else ""
        description = row["description"] if "description" in keys else ""
        title = (name or description or "").strip()

        provider = row["provider_name"] if "provider_name" in keys else ""
        model = _model_from_config(
            row["model_config_json"] if "model_config_json" in keys else None,
            provider,
        )

        started_at = _parse_ts(row["created_at"] if "created_at" in keys else None)
        ended_raw = row["updated_at"] if "updated_at" in keys else None
        ended_at: float | None = _parse_ts(ended_raw) or None

        total_tokens = _int_or_zero(
            row["total_tokens"] if "total_tokens" in keys else 0
        )
        accumulated = _int_or_zero(
            row["accumulated_total_tokens"] if "accumulated_total_tokens" in keys else 0
        )
        # Prefer the accumulated total (sums across model switches) when larger.
        total_tokens = max(total_tokens, accumulated)

        cost_raw = row["accumulated_cost"] if "accumulated_cost" in keys else None
        cost_usd: float | None
        cost_status: str
        if isinstance(cost_raw, (int, float)):
            cost_usd = float(cost_raw)
            cost_status = "exact"
        else:
            # Local providers (e.g. Ollama) record no USD; tokens are real
            # but cost simply was not computed. Honest about it.
            cost_usd = None
            cost_status = "unavailable"

        message_count = self._message_count(sid)

        return Session(
            agent=_AGENT,
            id=sid,
            title=title,
            display_name=title or sid,
            model=model,
            source=provider if isinstance(provider, str) else "",
            started_at=started_at,
            ended_at=ended_at,
            message_count=message_count,
            total_tokens=total_tokens,
            input_tokens=_int_or_zero(
                row["input_tokens"] if "input_tokens" in keys else 0
            ),
            output_tokens=_int_or_zero(
                row["output_tokens"] if "output_tokens" in keys else 0
            ),
            cost_usd=cost_usd,
            cost_status=cost_status,
            extra={
                "provider": provider if isinstance(provider, str) else "",
                "sessionType": row["session_type"] if "session_type" in keys else "",
                "workingDir": row["working_dir"] if "working_dir" in keys else "",
                "gooseMode": row["goose_mode"] if "goose_mode" in keys else "",
            },
        )

    def _message_count(self, session_id: str) -> int:
        conn = _open_ro(self._db_path)
        if conn is None:
            return 0
        try:
            cur = conn.execute(
                "SELECT count(*) FROM messages WHERE session_id = ?", (session_id,)
            )
            r = cur.fetchone()
            return int(r[0]) if r and r[0] is not None else 0
        except sqlite3.Error:
            return 0
        finally:
            conn.close()

    def list_events(self, session_id: str, limit: int = 500) -> list[Event]:
        """Parse one session's messages into unified events, chronological."""
        conn = _open_ro(self._db_path)
        if conn is None:
            return []
        events: list[Event] = []
        seq = 0
        try:
            cur = conn.execute(
                "SELECT id, message_id, role, content_json, created_timestamp, "
                "tokens FROM messages WHERE session_id = ? "
                "ORDER BY created_timestamp ASC, id ASC",
                (session_id,),
            )
            rows = cur.fetchall()
        except sqlite3.Error as exc:
            logger.warning("Goose list_events query failed: %s", exc)
            return []
        finally:
            conn.close()

        for row in rows:
            if len(events) >= limit:
                break
            role = (row["role"] or "") if "role" in row.keys() else ""
            ts = _parse_ts(
                row["created_timestamp"] if "created_timestamp" in row.keys() else None
            )
            tokens = _int_or_zero(row["tokens"] if "tokens" in row.keys() else 0)
            blocks = _decode_blocks(
                row["content_json"] if "content_json" in row.keys() else None
            )

            text_emitted = False
            for block in blocks:
                if len(events) >= limit:
                    break
                btype = block.get("type")

                if btype == "toolRequest":
                    seq += 1
                    call = block.get("toolCall") or {}
                    value = call.get("value") if isinstance(call, dict) else {}
                    value = value if isinstance(value, dict) else {}
                    tool_name = value.get("name") or "unknown"
                    arguments = value.get("arguments")
                    meta = block.get("_meta") if isinstance(block.get("_meta"), dict) else {}
                    events.append(Event(
                        agent=_AGENT,
                        session_id=session_id,
                        id=f"{session_id}:{seq}",
                        type="tool_call",
                        ts=ts,
                        role=role or "assistant",
                        tool_name=str(tool_name),
                        tool_calls=[{
                            "id": block.get("id") or "",
                            "name": str(tool_name),
                            "arguments": arguments,
                        }],
                        extra={
                            "extension": meta.get("goose_extension") or "",
                            "status": call.get("status") if isinstance(call, dict) else "",
                        },
                    ))

                elif btype == "toolResponse":
                    seq += 1
                    result = block.get("toolResult") or {}
                    result = result if isinstance(result, dict) else {}
                    value = result.get("value") if isinstance(result.get("value"), dict) else {}
                    is_error = bool(value.get("isError")) if isinstance(value, dict) else False
                    events.append(Event(
                        agent=_AGENT,
                        session_id=session_id,
                        id=f"{session_id}:{seq}",
                        type="tool_result",
                        ts=ts,
                        # Tool results are stored on a role=user row; surface
                        # them as tool output, not a user message.
                        role="tool",
                        content=_tool_result_text(result),
                        extra={
                            "toolCallId": block.get("id") or "",
                            "status": result.get("status") or "",
                            "isError": is_error,
                        },
                    ))

                elif btype == "text":
                    txt = block.get("text")
                    if isinstance(txt, str) and txt:
                        seq += 1
                        events.append(Event(
                            agent=_AGENT,
                            session_id=session_id,
                            id=f"{session_id}:{seq}",
                            type="message",
                            ts=ts,
                            role=role,
                            content=txt,
                            tokens=tokens,
                        ))
                        text_emitted = True

            # If the row had blocks we did not recognise but does carry text,
            # fall back to a single message so nothing is silently dropped.
            if not text_emitted and not any(
                b.get("type") in ("toolRequest", "toolResponse") for b in blocks
            ):
                fallback = _text_of_blocks(blocks)
                if fallback:
                    seq += 1
                    events.append(Event(
                        agent=_AGENT,
                        session_id=session_id,
                        id=f"{session_id}:{seq}",
                        type="message",
                        ts=ts,
                        role=role,
                        content=fallback,
                        tokens=tokens,
                    ))

        return events

    def capabilities(self) -> set[Capability]:
        # SESSIONS + EVENTS + COST. Goose records REAL token usage on disk
        # (sessions.total_tokens / input_tokens / output_tokens), so COST is
        # honest here — unlike PicoClaw/NanoClaw which carry no usage columns.
        # accumulated_cost (USD) is present for paid providers and NULL for
        # local Ollama; we surface tokens always and USD when on disk.
        return {Capability.SESSIONS, Capability.EVENTS, Capability.COST}
