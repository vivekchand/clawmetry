"""CursorAdapter — read Cursor IDE AI chat from its SQLite key-value store.

Cursor (https://cursor.com) is a VS Code fork. Like VS Code it keeps app
state in SQLite "vscdb" files, but its AI chat / "Composer" history lives in
a Cursor-specific key-value table, ``cursorDiskKV`` (a sibling of the stock
VS Code ``ItemTable``). Two DBs matter:

    Global   ~/Library/Application Support/Cursor/User/globalStorage/state.vscdb
    Per-ws   ~/Library/Application Support/Cursor/User/workspaceStorage/<hash>/state.vscdb

The GLOBAL DB is the primary source on modern Cursor: every chat/composer
session is a ``cursorDiskKV`` row keyed ``composerData:<composerId>`` whose
value is a JSON blob. The list/index of sessions is a single ``ItemTable``
row, ``composer.composerHeaders`` -> ``{"allComposers": [ {composerId,
createdAt, name, unifiedMode, ...}, ... ]}``.

Inside a ``composerData:<id>`` blob the messages live in one of two shapes
(Cursor migrated formats across versions; we handle both):

  * INLINE (older):   ``conversationMap`` is a dict ``{bubbleId: bubble}``
                      and ``fullConversationHeadersOnly`` may order them.
  * HEADER+ROWS (newer): ``conversationMap`` is empty, the bubble ORDER is
                      ``fullConversationHeadersOnly`` (a list of
                      ``{"bubbleId": str, "type": int}``), and each bubble's
                      body is a SEPARATE ``cursorDiskKV`` row keyed
                      ``bubbleId:<composerId>:<bubbleId>``.

A "bubble" (one message) carries:
    ``type``          int   1 = user, 2 = assistant   (this is the role)
    ``text``          str   the message text
    ``richText``      str   optional rich-text fallback for ``text``
    ``createdAt`` / ``clientStartTime``   ms-epoch timestamp (optional)
    ``toolFormerData``                    a tool call/result, when present
    ``tokenCount``                        optional usage hint (NOT a billed total)

Some installs also keep the older per-workspace layout in the WORKSPACE DB:
``ItemTable`` rows ``aiService.prompts`` (list of user prompts) and
``aiService.generations`` (list of assistant generations), plus
``composer.composerData`` (the per-workspace composer index). We read the
global DB first and fall back to per-workspace DBs so historical data on
either layout shows up.

VERIFIED against a real Cursor install on macOS (Cursor app, globalStorage +
workspaceStorage state.vscdb). Real-world corrections baked in below:

  * WAL GOTCHA: Cursor is usually running and keeps recent writes in the
    ``state.vscdb-wal`` sidecar (not yet checkpointed into the main file).
    Opening with ``immutable=1`` IGNORES the WAL and returns the stale/empty
    main file -> sessions vanish. So unlike a quiescent DB we open
    ``mode=ro`` (read-only, WAL-visible) WITHOUT ``immutable=1``, and set
    ``PRAGMA query_only=ON`` as a belt-and-braces guard. We only ever run
    SELECTs, always close the connection, and never raise.
  * NO BILLED COST: Cursor does not store a per-session billed token total or
    dollar cost on disk (billing is server-side). A bubble may carry a
    ``tokenCount`` hint; we surface it in ``extra`` but DO NOT claim COST.

The IDE owns these files. We are a passive observer: read-only open, never a
writer lock, never a mutation, never an uncaught exception.
"""
from __future__ import annotations

import glob
import json
import logging
import os
import sqlite3
from typing import Any

from .base import AgentAdapter, Capability, DetectResult, Event, Session

logger = logging.getLogger("clawmetry.adapters.cursor")

_AGENT = "cursor"

# cursorDiskKV / ItemTable key prefixes + names.
_COMPOSER_DATA_PREFIX = "composerData:"
_BUBBLE_PREFIX = "bubbleId:"
_HEADERS_KEY = "composer.composerHeaders"  # global ItemTable: session index
_WS_COMPOSER_DATA_KEY = "composer.composerData"  # workspace ItemTable: index
_WS_PROMPTS_KEY = "aiService.prompts"  # workspace ItemTable: legacy user prompts
_WS_GENERATIONS_KEY = "aiService.generations"  # workspace: legacy assistant gens

# Bubble ``type`` -> unified role. 1 = user, 2 = assistant (Cursor's encoding).
_BUBBLE_TYPE_ROLE = {1: "user", 2: "assistant"}

# Default Cursor application-support root on each platform. The constructor
# arg / CLAWMETRY_CURSOR_DB override wins; this is just zero-config discovery.
_APP_SUPPORT_BY_PLATFORM = {
    "darwin": "~/Library/Application Support/Cursor",
    "linux": "~/.config/Cursor",
    "win32": "~/AppData/Roaming/Cursor",
}


def _default_cursor_root() -> str:
    import sys

    base = _APP_SUPPORT_BY_PLATFORM.get(sys.platform, "~/.config/Cursor")
    return os.path.expanduser(base)


def _default_global_db() -> str:
    return os.path.join(
        _default_cursor_root(), "User", "globalStorage", "state.vscdb"
    )


def _open_ro(db_path: str) -> sqlite3.Connection | None:
    """Open a Cursor vscdb read-only with the WAL VISIBLE.

    We deliberately do NOT pass ``immutable=1``: Cursor is typically running
    and recent chats sit in the ``-wal`` sidecar; ``immutable=1`` would skip
    the WAL and read a stale/empty main file. ``mode=ro`` keeps us from ever
    taking a writer lock, and ``PRAGMA query_only=ON`` blocks accidental
    writes. Returns None on any failure (never raises).
    """
    if not os.path.isfile(db_path):
        return None
    try:
        conn = sqlite3.connect(
            f"file:{db_path}?mode=ro", uri=True, timeout=2.0
        )
        conn.row_factory = sqlite3.Row
        try:
            conn.execute("PRAGMA query_only=ON")
        except sqlite3.Error:
            pass
        return conn
    except sqlite3.Error as exc:
        logger.debug("Cursor: cannot open %s read-only: %s", db_path, exc)
        return None


def _has_table(conn: sqlite3.Connection, table: str) -> bool:
    try:
        row = conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
            (table,),
        ).fetchone()
        return row is not None
    except sqlite3.Error:
        return False


def _kv_get(conn: sqlite3.Connection, table: str, key: str) -> Any:
    """Fetch + JSON-decode a single key's value from ItemTable/cursorDiskKV."""
    if not _has_table(conn, table):
        return None
    try:
        row = conn.execute(
            f"SELECT value FROM {table} WHERE key=?", (key,)  # noqa: S608 (table is a fixed literal)
        ).fetchone()
    except sqlite3.Error as exc:
        logger.debug("Cursor: read %s[%s] failed: %s", table, key, exc)
        return None
    if row is None:
        return None
    return _loads(row["value"])


def _loads(raw: Any) -> Any:
    """JSON-decode a stored value (may be bytes or str); None on failure."""
    if raw is None:
        return None
    if isinstance(raw, (bytes, bytearray)):
        try:
            raw = raw.decode("utf-8", "replace")
        except (UnicodeDecodeError, AttributeError):
            return None
    try:
        return json.loads(raw)
    except (json.JSONDecodeError, TypeError, ValueError):
        return None


def _ms_to_s(ms: Any) -> float:
    """Cursor stores ms-epoch timestamps. Convert to float seconds; 0.0 if absent."""
    if ms is None:
        return 0.0
    try:
        v = float(ms)
    except (TypeError, ValueError):
        return 0.0
    if v <= 0:
        return 0.0
    # Heuristic: values > ~10^11 are milliseconds; smaller are already seconds.
    return v / 1000.0 if v > 1e11 else v


def _bubble_role(bubble: dict[str, Any]) -> str:
    """Map a bubble's ``type`` (1=user, 2=assistant) to a unified role."""
    t = bubble.get("type")
    try:
        return _BUBBLE_TYPE_ROLE.get(int(t), "")
    except (TypeError, ValueError):
        return ""


def _bubble_text(bubble: dict[str, Any]) -> str:
    """Pull human-readable text out of a bubble.

    Prefer ``text``; fall back to ``richText`` (which can be a JSON ProseMirror
    doc or a plain string). Tool-only bubbles legitimately have no text.
    """
    text = bubble.get("text")
    if isinstance(text, str) and text.strip():
        return text
    rich = bubble.get("richText")
    if isinstance(rich, str) and rich.strip():
        parsed = _loads(rich)
        if parsed is None:
            return rich
        flat = _flatten_richtext(parsed)
        if flat:
            return flat
    return ""


def _flatten_richtext(node: Any) -> str:
    """Best-effort flatten of a ProseMirror-ish richText doc to plain text."""
    out: list[str] = []

    def walk(n: Any) -> None:
        if isinstance(n, dict):
            t = n.get("text")
            if isinstance(t, str):
                out.append(t)
            # ProseMirror uses ``content``; Lexical (what Cursor uses) wraps
            # everything under ``root`` and nests via ``children``.
            for child_key in ("root", "content", "children"):
                walk(n.get(child_key))
        elif isinstance(n, list):
            for item in n:
                walk(item)

    walk(node)
    return "".join(out).strip()


def _tool_from_bubble(bubble: dict[str, Any]) -> tuple[str, list[dict[str, Any]]]:
    """Extract (tool_name, tool_calls) from a bubble's ``toolFormerData``.

    Cursor records tool use inside ``toolFormerData`` on the bubble. Shapes
    vary across versions; we pull a name and a compact params/result echo and
    never raise on an unexpected shape.
    """
    tfd = bubble.get("toolFormerData")
    if not isinstance(tfd, dict):
        return "", []
    name = ""
    for key in ("name", "tool", "toolName"):
        val = tfd.get(key)
        if isinstance(val, str) and val:
            name = val
            break
    call: dict[str, Any] = {"name": name}
    for key in ("params", "rawArgs", "args", "input"):
        if key in tfd:
            call[key] = tfd[key]
            break
    for key in ("result", "rawResult", "output"):
        if key in tfd:
            call[key] = tfd[key]
            break
    if tfd.get("status"):
        call["status"] = tfd.get("status")
    return name, [call]


def _shorten(text: str, limit: int = 80) -> str:
    s = (text or "").strip().replace("\n", " ")
    return s if len(s) <= limit else s[: limit - 3] + "..."


class CursorAdapter(AgentAdapter):
    """Adapter for Cursor IDE AI chat / Composer history.

    ``db_path`` defaults to the global ``state.vscdb`` but is a constructor
    arg so tests (and non-default installs) can point it anywhere. If the
    given/discovered global DB is present we ALSO scan sibling per-workspace
    DBs (bounded glob) so older per-workspace chat history surfaces too.
    """

    name = "cursor"
    display_name = "Cursor"

    def __init__(self, db_path: str | None = None) -> None:
        # Explicit arg / env override wins; else default global state.vscdb.
        self.db_path = os.path.expanduser(
            db_path
            or os.environ.get("CLAWMETRY_CURSOR_DB")
            or _default_global_db()
        )

    # ── DB discovery ─────────────────────────────────────────────────────

    def _workspace_dbs(self) -> list[str]:
        """Bounded glob of per-workspace ``state.vscdb`` siblings of db_path.

        Derives the Cursor User dir from db_path so a test fixture's
        workspaceStorage is also picked up. Never raises.
        """
        try:
            # db_path = <root>/User/globalStorage/state.vscdb
            #   dirname -> .../User/globalStorage
            #   dirname -> .../User   (the shared parent of workspaceStorage)
            user_dir = os.path.dirname(os.path.dirname(self.db_path))
            pattern = os.path.join(
                user_dir, "workspaceStorage", "*", "state.vscdb"
            )
            return sorted(glob.glob(pattern))
        except OSError as exc:
            logger.debug("Cursor: workspace glob failed: %s", exc)
            return []

    def _all_dbs(self) -> list[str]:
        """Global DB first, then any per-workspace DBs (deduped)."""
        dbs: list[str] = []
        if os.path.isfile(self.db_path):
            dbs.append(self.db_path)
        for w in self._workspace_dbs():
            if w not in dbs and os.path.isfile(w):
                dbs.append(w)
        return dbs

    # ── session reading ──────────────────────────────────────────────────

    def _read_db_sessions(self, db_path: str) -> list[Session]:
        """Read every chat/composer session out of one vscdb. Never raises."""
        conn = _open_ro(db_path)
        if conn is None:
            return []
        try:
            return self._sessions_from_conn(conn, db_path)
        except sqlite3.Error as exc:
            logger.warning("Cursor: read sessions from %s failed: %s", db_path, exc)
            return []
        finally:
            conn.close()

    def _sessions_from_conn(
        self, conn: sqlite3.Connection, db_path: str
    ) -> list[Session]:
        # Index of composer ids -> header metadata (name/createdAt/mode).
        headers = self._load_headers(conn)
        sessions: list[Session] = []
        seen: set[str] = set()

        # Primary: every composerData:<id> row in cursorDiskKV.
        if _has_table(conn, "cursorDiskKV"):
            try:
                rows = conn.execute(
                    "SELECT key, value FROM cursorDiskKV WHERE key LIKE ?",
                    (_COMPOSER_DATA_PREFIX + "%",),
                ).fetchall()
            except sqlite3.Error as exc:
                logger.debug("Cursor: composerData scan failed: %s", exc)
                rows = []
            for row in rows:
                cid = row["key"][len(_COMPOSER_DATA_PREFIX):]
                blob = _loads(row["value"])
                if not isinstance(blob, dict):
                    continue
                sess = self._session_from_blob(conn, cid, blob, headers.get(cid), db_path)
                if sess is not None:
                    sessions.append(sess)
                    seen.add(cid)

        # Fallback: legacy per-workspace aiService prompt/generation lists.
        legacy = self._legacy_workspace_session(conn, db_path)
        if legacy is not None and legacy.id not in seen:
            sessions.append(legacy)
        return sessions

    def _load_headers(self, conn: sqlite3.Connection) -> dict[str, dict[str, Any]]:
        """composerId -> header dict, from global or per-workspace index."""
        out: dict[str, dict[str, Any]] = {}
        for key in (_HEADERS_KEY, _WS_COMPOSER_DATA_KEY):
            idx = _kv_get(conn, "ItemTable", key)
            if isinstance(idx, dict):
                for h in idx.get("allComposers") or []:
                    if isinstance(h, dict) and h.get("composerId"):
                        out[h["composerId"]] = h
        return out

    def _session_from_blob(
        self,
        conn: sqlite3.Connection,
        cid: str,
        blob: dict[str, Any],
        header: dict[str, Any] | None,
        db_path: str,
    ) -> Session | None:
        bubbles = self._ordered_bubbles(conn, cid, blob)

        # Timestamps: prefer explicit createdAt; bound by bubble timestamps.
        created = _ms_to_s(
            blob.get("createdAt")
            or (header or {}).get("createdAt")
        )
        bubble_ts = [t for t in (b.get("_ts", 0.0) for b in bubbles) if t]
        started = created or (min(bubble_ts) if bubble_ts else 0.0)
        ended = max(bubble_ts) if bubble_ts else (created or None)
        if ended is not None and started and ended < started:
            ended = started

        # Title: explicit name -> latestConversationSummary -> first user text.
        title = ""
        name = blob.get("name") or (header or {}).get("name")
        if isinstance(name, str) and name.strip():
            title = name.strip()
        if not title:
            summ = blob.get("latestConversationSummary")
            if isinstance(summ, dict):
                txt = summ.get("summary") or summ.get("text")
                if isinstance(txt, str) and txt.strip():
                    title = txt.strip()
        if not title:
            for b in bubbles:
                if b.get("_role") == "user" and b.get("_text"):
                    title = b["_text"]
                    break

        mode = blob.get("unifiedMode") or (header or {}).get("unifiedMode") or ""
        # Cursor records the picked model in modelConfig when one was set.
        model = ""
        mc = blob.get("modelConfig")
        if isinstance(mc, dict):
            for key in ("modelName", "model", "name"):
                val = mc.get(key)
                if isinstance(val, str) and val:
                    model = val
                    break

        display = _shorten(title) if title else cid[:24]

        return Session(
            agent=_AGENT,
            id=cid,
            display_name=display,
            title=title,
            model=model,
            source="cursor",
            started_at=started,
            ended_at=ended,
            message_count=len(bubbles),
            # Cursor does not store a billed token total or dollar cost on
            # disk (billing is server-side). Honestly surface 0 / None.
            total_tokens=0,
            cost_usd=None,
            extra={
                "mode": mode,
                "dbPath": db_path,
                "workspaceId": ((blob.get("workspaceIdentifier") or {}) or {}).get("id")
                if isinstance(blob.get("workspaceIdentifier"), dict)
                else None,
            },
        )

    def _ordered_bubbles(
        self, conn: sqlite3.Connection, cid: str, blob: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """Return this composer's bubbles in chronological order.

        Handles both storage shapes:
          * header+rows: ``fullConversationHeadersOnly`` orders bubbleIds,
            each body is a ``bubbleId:<cid>:<bubbleId>`` cursorDiskKV row.
          * inline: ``conversationMap`` holds ``{bubbleId: bubble}`` directly.
        Each returned dict is annotated with ``_role``/``_text``/``_ts``/``_id``.
        """
        out: list[dict[str, Any]] = []
        conv_map = blob.get("conversationMap")
        conv_map = conv_map if isinstance(conv_map, dict) else {}
        headers = blob.get("fullConversationHeadersOnly")
        headers = headers if isinstance(headers, list) else []

        if headers:
            for h in headers:
                if not isinstance(h, dict):
                    continue
                bid = h.get("bubbleId")
                if not bid:
                    continue
                bubble = conv_map.get(bid)
                if not isinstance(bubble, dict):
                    bubble = self._read_bubble_row(conn, cid, bid)
                if not isinstance(bubble, dict):
                    # Header carries a type even when the body row is missing;
                    # represent it as an empty placeholder so ordering holds.
                    bubble = {"type": h.get("type"), "bubbleId": bid}
                out.append(self._annotate(bubble, bid))
        elif conv_map:
            # Inline-only: order by bubble timestamp, stable on insertion.
            items = [
                self._annotate(b, bid)
                for bid, b in conv_map.items()
                if isinstance(b, dict)
            ]
            items.sort(key=lambda b: b["_ts"])
            out.extend(items)
        return out

    def _read_bubble_row(
        self, conn: sqlite3.Connection, cid: str, bid: str
    ) -> dict[str, Any] | None:
        val = _kv_get(conn, "cursorDiskKV", f"{_BUBBLE_PREFIX}{cid}:{bid}")
        return val if isinstance(val, dict) else None

    def _annotate(self, bubble: dict[str, Any], bid: str) -> dict[str, Any]:
        b = dict(bubble)
        b["_id"] = bubble.get("bubbleId") or bid
        b["_role"] = _bubble_role(bubble)
        b["_text"] = _bubble_text(bubble)
        b["_ts"] = _ms_to_s(bubble.get("createdAt") or bubble.get("clientStartTime"))
        return b

    def _legacy_workspace_session(
        self, conn: sqlite3.Connection, db_path: str
    ) -> Session | None:
        """Synthesize one Session from legacy aiService.prompts/generations.

        Older Cursor kept the workspace chat as two flat ItemTable lists. We
        only emit this when there is actual content and no composerData rows
        already covered it, so it never doubles a modern session.
        """
        prompts = _kv_get(conn, "ItemTable", _WS_PROMPTS_KEY)
        gens = _kv_get(conn, "ItemTable", _WS_GENERATIONS_KEY)
        prompts = prompts if isinstance(prompts, list) else []
        gens = gens if isinstance(gens, list) else []
        if not prompts and not gens:
            return None
        # Use the workspace hash as a stable id for this legacy bucket.
        try:
            ws_hash = os.path.basename(os.path.dirname(db_path))
        except (OSError, TypeError):
            ws_hash = "workspace"
        sid = f"aiservice:{ws_hash}"
        title = ""
        for p in prompts:
            if isinstance(p, dict) and isinstance(p.get("text"), str) and p["text"].strip():
                title = p["text"]
                break
        return Session(
            agent=_AGENT,
            id=sid,
            display_name=_shorten(title) if title else sid,
            title=title,
            model="",
            source="cursor",
            started_at=0.0,
            ended_at=None,
            message_count=len(prompts) + len(gens),
            total_tokens=0,
            cost_usd=None,
            extra={"legacy": "aiService", "dbPath": db_path},
        )

    # ── AgentAdapter contract ────────────────────────────────────────────

    def detect(self) -> DetectResult:
        try:
            workspace = os.path.dirname(os.path.dirname(os.path.dirname(self.db_path)))
            if not os.path.isfile(self.db_path):
                return DetectResult(
                    name=self.name,
                    display_name=self.display_name,
                    detected=False,
                    workspace=workspace,
                    capabilities=[c.value for c in self.capabilities()],
                    meta={"dbPath": self.db_path},
                )
            # Cheap-ish: count sessions across all DBs. The composerData scan
            # is bounded by the row count; this runs on page load so we cap it.
            count = 0
            for db in self._all_dbs():
                count += len(self._read_db_sessions(db))
            return DetectResult(
                name=self.name,
                display_name=self.display_name,
                detected=count > 0,
                running=False,  # we cannot reliably tell if the IDE is open
                workspace=workspace,
                session_count=count,
                capabilities=[c.value for c in self.capabilities()],
                meta={"dbPath": self.db_path},
            )
        except Exception as exc:  # never raise from detect()
            logger.debug("Cursor detect failed: %s", exc)
            return DetectResult(
                name=self.name,
                display_name=self.display_name,
                detected=False,
                capabilities=[c.value for c in self.capabilities()],
            )

    def list_sessions(self, limit: int = 100) -> list[Session]:
        try:
            sessions: list[Session] = []
            seen: set[str] = set()
            for db in self._all_dbs():
                for s in self._read_db_sessions(db):
                    if s.id in seen:
                        continue
                    seen.add(s.id)
                    sessions.append(s)
            sessions.sort(
                key=lambda s: (
                    s.ended_at if s.ended_at is not None else s.started_at
                ),
                reverse=True,
            )
            return sessions[:limit]
        except Exception as exc:
            logger.warning("Cursor list_sessions failed: %s", exc)
            return []

    def list_events(self, session_id: str, limit: int = 500) -> list[Event]:
        try:
            for db in self._all_dbs():
                events = self._events_from_db(db, session_id, limit)
                if events:
                    return events
            return []
        except Exception as exc:
            logger.warning("Cursor list_events failed: %s", exc)
            return []

    def _events_from_db(
        self, db_path: str, session_id: str, limit: int
    ) -> list[Event]:
        conn = _open_ro(db_path)
        if conn is None:
            return []
        try:
            # Legacy aiService bucket.
            if session_id.startswith("aiservice:"):
                return self._legacy_events(conn, session_id, db_path, limit)
            blob = _kv_get(conn, "cursorDiskKV", f"{_COMPOSER_DATA_PREFIX}{session_id}")
            if not isinstance(blob, dict):
                return []
            bubbles = self._ordered_bubbles(conn, session_id, blob)
            events: list[Event] = []
            for i, b in enumerate(bubbles):
                role = b.get("_role") or ""
                text = b.get("_text") or ""
                tool_name, tool_calls = _tool_from_bubble(b)
                etype = "tool_call" if (tool_name and not text) else "message"
                extra: dict[str, Any] = {}
                tk = b.get("tokenCount")
                if tk is not None:
                    # A usage HINT only; not a billed total. Keep it visible
                    # but do not promote it to Session.total_tokens / COST.
                    extra["tokenCountHint"] = tk
                if b.get("type") is not None:
                    extra["bubbleType"] = b.get("type")
                events.append(
                    Event(
                        agent=_AGENT,
                        session_id=session_id,
                        id=str(b.get("_id") or f"{session_id}:{i}"),
                        type=etype,
                        ts=b.get("_ts", 0.0),
                        role=role,
                        content=text,
                        tool_name=tool_name,
                        tool_calls=tool_calls,
                        tokens=0,  # billed tokens UNKNOWN on disk
                        extra=extra,
                    )
                )
            return events[:limit]
        except sqlite3.Error as exc:
            logger.warning("Cursor: read events from %s failed: %s", db_path, exc)
            return []
        finally:
            conn.close()

    def _legacy_events(
        self, conn: sqlite3.Connection, session_id: str, db_path: str, limit: int
    ) -> list[Event]:
        prompts = _kv_get(conn, "ItemTable", _WS_PROMPTS_KEY)
        gens = _kv_get(conn, "ItemTable", _WS_GENERATIONS_KEY)
        prompts = prompts if isinstance(prompts, list) else []
        gens = gens if isinstance(gens, list) else []
        events: list[Event] = []
        for i, p in enumerate(prompts):
            text = p.get("text") if isinstance(p, dict) else (p if isinstance(p, str) else "")
            events.append(
                Event(
                    agent=_AGENT,
                    session_id=session_id,
                    id=f"prompt:{i}",
                    type="message",
                    role="user",
                    content=text or "",
                )
            )
        for i, g in enumerate(gens):
            text = ""
            if isinstance(g, dict):
                text = g.get("textDescription") or g.get("description") or g.get("text") or ""
            elif isinstance(g, str):
                text = g
            events.append(
                Event(
                    agent=_AGENT,
                    session_id=session_id,
                    id=f"generation:{i}",
                    type="message",
                    role="assistant",
                    content=text,
                    ts=_ms_to_s(g.get("unixMs")) if isinstance(g, dict) else 0.0,
                )
            )
        return events[:limit]

    def capabilities(self) -> set[Capability]:
        # HONEST scope: we read chat/composer sessions + their message events
        # (incl. tool calls when Cursor records them). Cursor stores no billed
        # token total / dollar cost on disk, so NO COST. No subagents, crons,
        # or live stream from this store.
        return {Capability.SESSIONS, Capability.EVENTS}
