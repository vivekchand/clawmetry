"""NanoClawAdapter — read NanoClaw sessions from per-session SQLite DBs.

NanoClaw (https://github.com/nanocoai/nanoclaw, TypeScript) does NOT share
OpenClaw's session layout. Each session lives in its own pair of SQLite
files under a per-group / per-session directory:

    <data_dir>/<agent_group_id>/<session_id>/
        inbound.db    (host writes, container reads)
        outbound.db   (container writes, host reads)

``inbound.db`` holds table ``messages_in`` (host-originated messages —
user/channel input, scheduled wakes), ``outbound.db`` holds
``messages_out`` (container-originated replies + system messages) plus a
``session_state`` key/value table.

Global ordering: ``seq`` is unique within a session ACROSS both tables —
the host writes even seqs, the container writes odd ones. To reconstruct
a transcript we read both tables and merge-sort by ``seq`` (falling back
to ``timestamp`` when a seq is missing).

``content`` is a JSON string whose shape depends on ``kind``; we parse it
defensively and pull out a text/body field, falling back to the raw
string when it is not JSON or has no recognisable text field.

Both of the following were VERIFIED against a real NanoClaw install
(github.com/nanocoai/nanoclaw @ 2.0.69) by running its own runtime code and
capturing the session SQLite (see tests/fixtures/runtimes/nanoclaw/REAL/):

  * Model / tokens / cost: the message tables have NO model, token, or cost
    columns. The Agent SDK transcript that DOES carry usage lives INSIDE the
    container (``$HOME/.claude/projects/.../<sessionId>.jsonl``) and is
    archived-to-markdown then rotated/deleted; it never lands on the
    host-visible session dir, and ``claude.ts translateEvents()`` keeps only
    the result text + session id. So model/tokens/cost are genuinely
    unrecoverable host-side. We honestly surface model="", total_tokens=0,
    cost_usd=None and omit the COST capability.
  * Data dir: NanoClaw resolves its data dir as
    ``path.resolve(process.cwd(), 'data')`` (install-CWD-relative). There is
    NO ``NANOCLAW_HOME`` and NO ``DATA_DIR`` env override in NanoClaw, and it
    does NOT use ``~/.nanoclaw``. The README flow clones to a checkout dir
    (e.g. ``~/nanoclaw-v2``) and runs from there, so the real path is
    ``<checkout>/data/v2-sessions``. We therefore discover the dir from a
    bounded set of common checkout locations (plus a ClawMetry-side
    ``CLAWMETRY_NANOCLAW_DIR`` override and the constructor arg) instead of
    guessing a single home path.

Read-only contract: the NanoClaw runtime actively owns these DB files.
We ALWAYS open them read-only + immutable
(``file:<path>?mode=ro&immutable=1``) so we never take a writer lock or
mutate the runtime's data, always close the connection, and never raise
out of any public method — failures are logged and degrade to empty.
"""
from __future__ import annotations

import glob
import json
import logging
import os
import sqlite3
from datetime import datetime, timezone
from typing import Any

from .base import AgentAdapter, Capability, DetectResult, Event, Session

logger = logging.getLogger("clawmetry.adapters.nanoclaw")

_AGENT = "nanoclaw"

# Inbound ``kind`` values that represent user/channel-originated chat.
_INBOUND_CHAT_KINDS = {"chat", "message", "user", "channel", "wake"}
# Outbound ``kind`` values that represent the agent's chat replies.
_OUTBOUND_CHAT_KINDS = {"chat", "chat-sdk", "assistant", "reply"}


# Common locations a NanoClaw checkout lands in. NanoClaw's data dir is
# CWD-relative (<checkout>/data/v2-sessions) with no env var, so we scan a
# bounded, explicit set of likely checkout roots rather than walking $HOME.
_CHECKOUT_GLOBS = (
    "~/nanoclaw*/data/v2-sessions",
    "~/projects/nanoclaw*/data/v2-sessions",
    "~/src/nanoclaw*/data/v2-sessions",
    "~/code/nanoclaw*/data/v2-sessions",
    "~/dev/nanoclaw*/data/v2-sessions",
    "~/.nanoclaw/data/v2-sessions",  # last-ditch fallback (not used by NanoClaw)
)


def _has_session_dbs(v2_sessions_dir: str) -> bool:
    """True if a v2-sessions dir actually holds a <group>/<session>/inbound.db."""
    try:
        return bool(glob.glob(os.path.join(v2_sessions_dir, "*", "*", "inbound.db")))
    except OSError:
        return False


def _normalize_data_dir(path: str) -> str:
    """Accept either a v2-sessions dir or a checkout root and return the former.

    Lets ``CLAWMETRY_NANOCLAW_DIR`` (and the constructor arg) point at the
    NanoClaw checkout root, its ``data`` dir, or the ``v2-sessions`` dir
    directly. A path that already holds ``<group>/<session>/inbound.db`` is
    treated as the sessions root as-is (whatever its name); an unresolvable
    path is returned unchanged so detect() reports detected=False gracefully.
    """
    path = os.path.expanduser(path.rstrip(os.sep))
    if _has_session_dbs(path) or os.path.basename(path) == "v2-sessions":
        return path
    for sub in ("v2-sessions", os.path.join("data", "v2-sessions")):
        cand = os.path.join(path, sub)
        if os.path.isdir(cand):
            return cand
    return path


def _discover_data_dir() -> str:
    """Discover a real NanoClaw v2-sessions dir with zero config.

    Order: explicit ClawMetry override -> the current working dir's data/ ->
    common checkout locations. Returns the first that actually contains
    session DBs; if none do, returns the first plausible path so detect()
    reports detected=False gracefully. Never raises.
    """
    # 1. Explicit ClawMetry-side override (NanoClaw has no env var of its own).
    override = os.environ.get("CLAWMETRY_NANOCLAW_DIR")
    if override:
        return _normalize_data_dir(override)

    candidates: list[str] = []
    # 2. Running from inside the checkout (NanoClaw's own CWD-relative path).
    candidates.append(os.path.join(os.getcwd(), "data", "v2-sessions"))
    # 3. Common checkout locations (bounded globs, newest match first).
    for pattern in _CHECKOUT_GLOBS:
        try:
            for hit in sorted(glob.glob(os.path.expanduser(pattern)), reverse=True):
                candidates.append(hit)
        except OSError:
            continue

    for cand in candidates:
        if _has_session_dbs(cand):
            return cand
    return candidates[0] if candidates else os.path.expanduser(_CHECKOUT_GLOBS[-1])


def _parse_ts(ts: Any) -> float:
    """Parse an RFC3339 / ISO-8601 string (or numeric epoch) to float seconds.

    NanoClaw stores timestamps as TEXT (RFC3339). Returns 0.0 on anything
    unparseable so callers never have to guard.
    """
    if ts is None:
        return 0.0
    if isinstance(ts, (int, float)):
        return float(ts)
    try:
        s = str(ts).strip()
        if not s:
            return 0.0
        if s.endswith("Z"):
            s = s[:-1] + "+00:00"
        dt = datetime.fromisoformat(s)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.timestamp()
    except (ValueError, AttributeError, TypeError):
        return 0.0


def _open_ro(db_path: str) -> sqlite3.Connection | None:
    """Open a NanoClaw SQLite DB read-only + immutable.

    ``immutable=1`` is safe here: we are a passive observer and never need
    to see in-flight writes mid-transcript. It guarantees we take no lock
    and cannot perturb the runtime's files. Returns None on failure.
    """
    if not os.path.isfile(db_path):
        return None
    try:
        conn = sqlite3.connect(
            f"file:{db_path}?mode=ro&immutable=1", uri=True, timeout=2.0
        )
        conn.row_factory = sqlite3.Row
        return conn
    except sqlite3.Error as exc:
        logger.debug("NanoClaw: cannot open %s read-only: %s", db_path, exc)
        return None


def _extract_text(content: Any) -> str:
    """Pull a human-readable text body out of a NanoClaw ``content`` value.

    ``content`` is a JSON string whose shape varies by ``kind``. Try to
    decode it and look for a text-ish field; fall back to the raw string.
    """
    if content is None:
        return ""
    raw = content if isinstance(content, str) else str(content)
    try:
        obj = json.loads(raw)
    except (json.JSONDecodeError, TypeError, ValueError):
        return raw
    if isinstance(obj, str):
        return obj
    if isinstance(obj, dict):
        for key in ("text", "body", "message", "content", "prompt", "value"):
            val = obj.get(key)
            if isinstance(val, str) and val:
                return val
        # NanoClaw control messages have no text field, e.g.
        # {"operation":"reaction","emoji":"X"} or {"operation":"edit",...}.
        # Summarise them so they never leak raw JSON into a session title.
        op = obj.get("operation")
        if isinstance(op, str) and op:
            emoji = obj.get("emoji")
            if op == "reaction" and emoji:
                return f"[reaction {emoji}]"
            return f"[{op}]"
        # OpenAI/Anthropic-style content blocks: [{"type":"text","text":...}]
        blocks = obj.get("content")
        if isinstance(blocks, list):
            parts = [
                b.get("text")
                for b in blocks
                if isinstance(b, dict) and isinstance(b.get("text"), str)
            ]
            if parts:
                return "\n".join(parts)
        return raw
    if isinstance(obj, list):
        parts = [
            b.get("text")
            for b in obj
            if isinstance(b, dict) and isinstance(b.get("text"), str)
        ]
        if parts:
            return "\n".join(parts)
        return raw
    return raw


def _classify(kind: str, inbound: bool) -> tuple[str, str]:
    """Map a NanoClaw message ``kind`` to a unified (role, type).

    Inbound chat -> user; outbound chat/chat-sdk -> assistant; anything
    that looks like a system message -> role=system. Always type=message
    (the message tables carry no tool-call structure).
    """
    k = (kind or "").lower()
    if k in ("system", "system-prompt", "wake-system"):
        return "system", "message"
    if inbound:
        if k in _INBOUND_CHAT_KINDS:
            return "user", "message"
        # Unknown inbound kind: treat as user-side input, surface kind in extra.
        return "user", "message"
    # outbound
    if k in _OUTBOUND_CHAT_KINDS:
        return "assistant", "message"
    return "assistant", "message"


class NanoClawAdapter(AgentAdapter):
    """Adapter for NanoClaw per-session SQLite stores.

    ``data_dir`` defaults to ``~/.nanoclaw/data/v2-sessions`` but is a
    constructor arg so tests (and non-default installs) can point it
    anywhere.
    """

    name = "nanoclaw"
    display_name = "NanoClaw"

    def __init__(self, data_dir: str | None = None) -> None:
        # Explicit arg wins; otherwise discover a real install (CWD-relative,
        # common checkout locations, or CLAWMETRY_NANOCLAW_DIR override).
        self.data_dir = (
            _normalize_data_dir(data_dir) if data_dir else _discover_data_dir()
        )

    # ── helpers ──────────────────────────────────────────────────────────

    def _session_dirs(self) -> list[str]:
        """Return paths of every ``<group>/<session>`` dir holding inbound.db.

        Cheap glob, never raises. Bounded by the filesystem layout (two
        levels deep), and we only stat for the inbound.db marker.
        """
        if not os.path.isdir(self.data_dir):
            return []
        try:
            inbound_dbs = glob.glob(
                os.path.join(self.data_dir, "*", "*", "inbound.db")
            )
        except OSError as exc:
            logger.debug("NanoClaw: glob failed under %s: %s", self.data_dir, exc)
            return []
        return [os.path.dirname(p) for p in inbound_dbs]

    def _read_session(self, session_dir: str) -> Session | None:
        """Build one unified Session from a session dir, or None if unreadable."""
        session_id = os.path.basename(session_dir.rstrip(os.sep))
        group_id = os.path.basename(os.path.dirname(session_dir.rstrip(os.sep)))
        inbound = os.path.join(session_dir, "inbound.db")
        outbound = os.path.join(session_dir, "outbound.db")

        message_count = 0
        min_ts: float | None = None
        max_ts: float | None = None
        latest_text = ""
        latest_seq = -1
        readable = False

        for db_path, table in (
            (inbound, "messages_in"),
            (outbound, "messages_out"),
        ):
            conn = _open_ro(db_path)
            if conn is None:
                continue
            readable = True
            try:
                cur = conn.execute(
                    f"SELECT seq, timestamp, content FROM {table}"  # noqa: S608 (table is a fixed literal)
                )
                for row in cur.fetchall():
                    message_count += 1
                    ts = _parse_ts(row["timestamp"])
                    if ts:
                        min_ts = ts if min_ts is None else min(min_ts, ts)
                        max_ts = ts if max_ts is None else max(max_ts, ts)
                    seq = row["seq"]
                    seq_val = int(seq) if seq is not None else -1
                    if seq_val >= latest_seq:
                        text = _extract_text(row["content"])
                        if text:
                            latest_seq = seq_val
                            latest_text = text
            except sqlite3.Error as exc:
                logger.warning(
                    "NanoClaw: read %s in %s failed: %s", table, session_dir, exc
                )
            finally:
                conn.close()

        if not readable:
            return None

        display = (latest_text or session_id).strip().replace("\n", " ")
        if len(display) > 80:
            display = display[:77] + "..."

        return Session(
            agent=_AGENT,
            id=session_id,
            display_name=display or session_id,
            # Model is UNKNOWN on disk — NanoClaw's message tables carry no
            # model column. Usage likely lives in the Agent SDK event log.
            model="",
            source="nanoclaw",
            started_at=min_ts or 0.0,
            ended_at=max_ts,
            message_count=message_count,
            # Tokens/cost UNKNOWN on disk (no columns). Surfaced as 0 / None.
            total_tokens=0,
            cost_usd=None,
            extra={"agentGroupId": group_id},
        )

    # ── AgentAdapter contract ────────────────────────────────────────────

    def detect(self) -> DetectResult:
        try:
            home = os.path.dirname(os.path.dirname(self.data_dir))
            if not os.path.isdir(self.data_dir):
                return DetectResult(
                    name=self.name,
                    display_name=self.display_name,
                    detected=False,
                    workspace=home,
                    capabilities=[c.value for c in self.capabilities()],
                    meta={"dataDir": self.data_dir},
                )
            session_dirs = self._session_dirs()
            return DetectResult(
                name=self.name,
                display_name=self.display_name,
                detected=len(session_dirs) > 0,
                running=False,
                workspace=home,
                session_count=len(session_dirs),
                capabilities=[c.value for c in self.capabilities()],
                meta={"dataDir": self.data_dir},
            )
        except Exception as exc:  # never raise from detect()
            logger.debug("NanoClaw detect failed: %s", exc)
            return DetectResult(
                name=self.name,
                display_name=self.display_name,
                detected=False,
                capabilities=[c.value for c in self.capabilities()],
            )

    def list_sessions(self, limit: int = 100) -> list[Session]:
        try:
            sessions: list[Session] = []
            for session_dir in self._session_dirs():
                try:
                    sess = self._read_session(session_dir)
                except Exception as exc:
                    logger.warning(
                        "NanoClaw: skipping unreadable session %s: %s",
                        session_dir,
                        exc,
                    )
                    continue
                if sess is not None:
                    sessions.append(sess)
            # Newest first by ended_at (fall back to started_at).
            sessions.sort(
                key=lambda s: (s.ended_at if s.ended_at is not None else s.started_at),
                reverse=True,
            )
            return sessions[:limit]
        except Exception as exc:
            logger.warning("NanoClaw list_sessions failed: %s", exc)
            return []

    def list_events(self, session_id: str, limit: int = 500) -> list[Event]:
        try:
            session_dir = self._locate_session(session_id)
            if session_dir is None:
                return []
            rows: list[tuple[int, float, Event]] = []

            inbound = os.path.join(session_dir, "inbound.db")
            outbound = os.path.join(session_dir, "outbound.db")

            rows.extend(self._read_events(inbound, "messages_in", session_id, True))
            rows.extend(self._read_events(outbound, "messages_out", session_id, False))

            # Merge-sort by seq (global within a session); fall back to ts.
            rows.sort(key=lambda r: (r[0], r[1]))
            return [r[2] for r in rows[:limit]]
        except Exception as exc:
            logger.warning("NanoClaw list_events failed: %s", exc)
            return []

    def _locate_session(self, session_id: str) -> str | None:
        for session_dir in self._session_dirs():
            if os.path.basename(session_dir.rstrip(os.sep)) == session_id:
                return session_dir
        return None

    def _read_events(
        self, db_path: str, table: str, session_id: str, inbound: bool
    ) -> list[tuple[int, float, Event]]:
        """Read one message table -> list of (seq, ts, Event) sort keys."""
        conn = _open_ro(db_path)
        if conn is None:
            return []
        out: list[tuple[int, float, Event]] = []
        try:
            if inbound:
                cur = conn.execute(
                    "SELECT id, seq, kind, timestamp, content, "
                    "platform_id, channel_type, thread_id "
                    "FROM messages_in"
                )
            else:
                cur = conn.execute(
                    "SELECT id, seq, kind, timestamp, content, in_reply_to, "
                    "platform_id, channel_type, thread_id "
                    "FROM messages_out"
                )
            for row in cur.fetchall():
                kind = row["kind"] or ""
                role, etype = _classify(kind, inbound)
                ts = _parse_ts(row["timestamp"])
                seq = row["seq"]
                # Missing seq sorts last among its timestamp; keep stable.
                seq_val = int(seq) if seq is not None else 1_000_000_000
                keys = row.keys()
                parent = row["in_reply_to"] if (not inbound and "in_reply_to" in keys) else None
                ev = Event(
                    agent=_AGENT,
                    session_id=session_id,
                    id=str(row["id"]),
                    type=etype,
                    ts=ts,
                    role=role,
                    content=_extract_text(row["content"]),
                    parent_id=parent,
                    tokens=0,  # tokens UNKNOWN on disk
                    extra={
                        "kind": kind,
                        "seq": seq_val if seq is not None else None,
                        "direction": "inbound" if inbound else "outbound",
                        "platformId": row["platform_id"] or "",
                        "channelType": row["channel_type"] or "",
                        "threadId": row["thread_id"] or "",
                    },
                )
                out.append((seq_val, ts, ev))
        except sqlite3.Error as exc:
            logger.warning(
                "NanoClaw: read %s from %s failed: %s", table, db_path, exc
            )
        finally:
            conn.close()
        return out

    def capabilities(self) -> set[Capability]:
        # HONEST scope: we only read sessions + their message events. No
        # cost (no token/cost columns on disk), no subagents, no crons,
        # no live stream. Do not advertise what we don't implement.
        return {Capability.SESSIONS, Capability.EVENTS}
