"""Replay-event mapper for OpenClaw (#4816, schema in #4813).

Maps one OpenClaw session onto the canonical ``clawmetry.replay_schema``
events the transcript viewer renders through ``/api/replay-tree``. The
daemon calls ``OpenClawAdapter.iter_replay_events`` after every transcript
batch (``sync._local_ingest_session_batch``) and upserts the result into
``replay_events``.

Sources, in the order they are read:

1. The session transcript ``<sid>.jsonl`` in the directory
   ``sync._openclaw_sessions_dir()`` resolves: the legacy
   ``~/.openclaw/agents/main/sessions`` or, on OpenClaw 2026.9.x, the JSONL
   mirror ``clawmetry/openclaw_sqlite.py`` maintains. This is the v3
   envelope ``{"type": ..., "id", "parentId", "timestamp", ...}``.
   ``parentId`` is a chain, not a tree, so no event carries it as
   ``parent_span_id`` (``reference_openclaw_v3_parentid_is_chain``). The
   only ``parent_span_id`` written is an approval's gate: the ``tool.call``
   span it decided, which is how ``/api/replay-tree`` attaches it to a turn.
2. ``sessions.json`` next to the transcript: the session key
   (``agent:main:main``, ``agent:main:cron:<job>``) for a session id. The
   key is what the state database stores on approvals and sub-agent runs.
3. ``~/.openclaw/state/openclaw.sqlite``, opened read-only, never locked
   for writing: ``exec_approvals_config`` (the one leading ``mode.changed``),
   ``operator_approvals`` (``approval.requested`` / ``approval.decided``) and
   ``subagent_runs`` (``agent.spawn``).

What is deliberately not read yet, and why:

* ``acp_replay_events`` / ``acp_replay_sessions``: the purpose-built ACP
  replay stream the issue names as the primary source. On a live OpenClaw
  2026.9.3 node both tables exist and hold zero rows; its ``update_json``
  shapes are only knowable from rows, so a reader would be written against
  guessed field names. The transcript path above is what every session has
  today. When rows appear, this module is where the ACP reader goes.
* ``flow_runs`` / ``task_runs`` (``workflow.*``): ``flow_runs`` is empty on
  the same node and ``task_runs`` rows there are cron automation runs with
  no requester session, so there is nothing to attach to a session yet.
* ``plugin_binding_approvals``: keyed per plugin and channel, not per
  session; it cannot be placed on a session timeline.
* ``command_log_entries``: does not exist in the 2026.9.3 schema.

Nothing here raises to the caller: an unknown session yields nothing, a bad
line is skipped, an unreadable database only removes its enrichment.
"""
from __future__ import annotations

import json
import logging
import os
import re
import sqlite3
from datetime import datetime, timezone
from typing import Any, Iterator, Optional

from clawmetry import replay_schema as _rs

logger = logging.getLogger("clawmetry.adapters.openclaw_replay")

RUNTIME = "openclaw"

# Free text kept per payload field. The store redacts secrets; this bound
# keeps one long tool result from inflating a row.
_MAX_TEXT = 4000
# Cap on sessions.json entries scanned for the session key.
_MAX_INDEX_ENTRIES = 5000
# Cap on state-database rows joined per session.
_MAX_DB_ROWS = 500
_DB_TIMEOUT_S = 0.5
_UUID_SUFFIX = re.compile(
    r"-?[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$")


# ── small helpers ────────────────────────────────────────────────────────────


def _ts(raw: Any, fallback: float = 0.0) -> float:
    """Unix seconds from an OpenClaw timestamp.

    OpenClaw writes millisecond integers on live records and ISO-8601
    strings on older transcripts and fixtures. Anything else falls back.
    """
    if isinstance(raw, bool):
        return fallback
    if isinstance(raw, (int, float)):
        v = float(raw)
        if v <= 0:
            return fallback
        return v / 1000.0 if v > 1e11 else v
    if isinstance(raw, str) and raw.strip():
        s = raw.strip()
        try:
            v = float(s)
            return v / 1000.0 if v > 1e11 else v
        except ValueError:
            pass
        try:
            if s.endswith("Z"):
                s = s[:-1] + "+00:00"
            dt = datetime.fromisoformat(s)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.timestamp()
        except ValueError:
            return fallback
    return fallback


def _clip(text: Any) -> Optional[str]:
    if not isinstance(text, str):
        return None
    if len(text) > _MAX_TEXT:
        return text[:_MAX_TEXT]
    return text


def _text(content: Any) -> str:
    """Flatten a v3 ``content`` value (string or block list) to text."""
    if isinstance(content, str):
        return content
    parts: list[str] = []
    if isinstance(content, list):
        for block in content:
            if isinstance(block, str):
                parts.append(block)
            elif isinstance(block, dict) and block.get("type") == "text":
                val = block.get("text")
                if isinstance(val, str):
                    parts.append(val)
    return "".join(parts)


def _int(v: Any) -> int:
    try:
        return int(v or 0)
    except (TypeError, ValueError):
        return 0


def _usage(u: Any) -> dict[str, Any]:
    """Normalise the v3 ``usage`` dict (``input``/``output``/``cacheRead``/
    ``cacheWrite``/``totalTokens``/``cost``) and its older aliases."""
    if not isinstance(u, dict):
        return {}
    out: dict[str, Any] = {
        "input": _int(u.get("input", u.get("inputTokens", u.get("input_tokens")))),
        "output": _int(u.get("output", u.get("outputTokens", u.get("output_tokens")))),
        "cache_read": _int(u.get("cacheRead", u.get("cache_read_input_tokens"))),
        "cache_write": _int(u.get("cacheWrite", u.get("cache_creation_input_tokens"))),
        "total": _int(u.get("totalTokens", u.get("total_tokens"))),
    }
    cost = u.get("cost")
    if isinstance(cost, (int, float)) and not isinstance(cost, bool):
        out["cost_usd"] = float(cost)
    elif isinstance(cost, dict):
        total = cost.get("total")
        if isinstance(total, (int, float)) and not isinstance(total, bool):
            out["cost_usd"] = float(total)
    return out


def _collaboration(session_key: Optional[str]) -> Optional[str]:
    """``cron`` / ``direct`` / the third key segment, from a session key
    such as ``agent:main:cron:<job>`` or ``agent:main:main``."""
    if not isinstance(session_key, str) or not session_key:
        return None
    parts = session_key.split(":")
    if len(parts) < 3:
        return None
    seg = parts[2]
    if seg == "main":
        return "direct"
    # A per-session key segment such as ``cm-investigation-<uuid>`` keeps
    # its label and drops the id, so the chip stays a short, repeatable word.
    seg = _UUID_SUFFIX.sub("", seg)
    return seg or None


def permission_from_exec(row: Optional[dict[str, Any]]) -> str:
    """Permission chip from an ``exec_approvals_config`` row.

    ``security`` is ``deny`` / ``allowlist`` / ``full`` and ``ask`` is
    ``always`` / ``on-miss`` / ``never`` (OpenClaw 2026.9.3 ``dist``). Only
    the combination that never asks and never refuses is ``yolo``; anything
    that can ask or refuse is ``default``; no row is ``unknown``.
    """
    if not row:
        return "unknown"
    security = str(row.get("default_security") or "").lower()
    ask = str(row.get("default_ask") or "").lower()
    if security == "full" and ask == "never":
        return "yolo"
    if security or ask:
        return "default"
    return "unknown"


# ── read-only sources ────────────────────────────────────────────────────────


def _connect_ro(path: Optional[str]) -> Optional[sqlite3.Connection]:
    """Read-only SQLite connection, or None. The gateway writes this file
    continuously; ``mode=ro`` never takes a writer lock."""
    if not path or not os.path.isfile(path):
        return None
    try:
        conn = sqlite3.connect(
            "file:%s?mode=ro" % path, uri=True, timeout=_DB_TIMEOUT_S,
            check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn
    except sqlite3.Error as exc:
        logger.debug("openclaw replay: state db unavailable (%s): %s", path, exc)
        return None


def _table_exists(conn: sqlite3.Connection, name: str) -> bool:
    try:
        row = conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (name,)
        ).fetchone()
        return row is not None
    except sqlite3.Error:
        return False


def _columns(conn: sqlite3.Connection, table: str) -> set[str]:
    try:
        return {r[1] for r in conn.execute("PRAGMA table_info(%s)" % table)}
    except sqlite3.Error:
        return set()


class _Sources:
    """Everything besides the transcript, read lazily and never raising."""

    def __init__(self, sessions_dir: Optional[str], state_db: Optional[str]):
        self.sessions_dir = sessions_dir
        self.state_db = state_db
        self._index: Optional[dict[str, str]] = None   # session id -> key
        self._key_to_id: dict[str, str] = {}
        self._conn: Optional[sqlite3.Connection] = None
        self._conn_tried = False

    # sessions.json ------------------------------------------------------

    def _load_index(self) -> None:
        self._index = {}
        if not self.sessions_dir:
            return
        path = os.path.join(self.sessions_dir, "sessions.json")
        try:
            with open(path, encoding="utf-8") as fh:
                raw = json.load(fh)
        except (OSError, ValueError):
            return
        if not isinstance(raw, dict):
            return
        for n, (key, entry) in enumerate(raw.items()):
            if n >= _MAX_INDEX_ENTRIES:
                break
            if not isinstance(entry, dict):
                continue
            sid = entry.get("sessionId")
            if isinstance(sid, str) and sid and isinstance(key, str):
                self._index.setdefault(sid, key)
                self._key_to_id.setdefault(key, sid)

    def session_key(self, session_id: str) -> Optional[str]:
        if self._index is None:
            self._load_index()
        return (self._index or {}).get(session_id)

    def session_id_for_key(self, key: Any) -> Optional[str]:
        if self._index is None:
            self._load_index()
        if isinstance(key, str):
            return self._key_to_id.get(key)
        return None

    # state database -----------------------------------------------------

    def _db(self) -> Optional[sqlite3.Connection]:
        if not self._conn_tried:
            self._conn_tried = True
            self._conn = _connect_ro(self.state_db)
        return self._conn

    def close(self) -> None:
        if self._conn is not None:
            try:
                self._conn.close()
            except sqlite3.Error:
                pass
            self._conn = None

    def exec_mode(self) -> Optional[dict[str, Any]]:
        conn = self._db()
        if conn is None or not _table_exists(conn, "exec_approvals_config"):
            return None
        try:
            row = conn.execute(
                "SELECT default_security, default_ask, default_ask_fallback, "
                "auto_allow_skills, agent_count, allowlist_count, updated_at_ms "
                "FROM exec_approvals_config ORDER BY updated_at_ms DESC LIMIT 1"
            ).fetchone()
        except sqlite3.Error as exc:
            logger.debug("openclaw replay: exec_approvals_config unreadable: %s", exc)
            return None
        return dict(row) if row is not None else None

    def approvals(self, session_id: str, session_key: Optional[str]) -> list[dict[str, Any]]:
        conn = self._db()
        if conn is None or not _table_exists(conn, "operator_approvals"):
            return []
        cols = _columns(conn, "operator_approvals")
        wanted = [
            "approval_id", "kind", "status", "decision", "terminal_reason",
            "resolver_kind", "source_tool_name", "source_tool_call_id",
            "source_session_id", "source_session_key", "created_at_ms",
            "resolved_at_ms", "updated_at_ms",
        ]
        have = [c for c in wanted if c in cols]
        if "approval_id" not in have or "created_at_ms" not in have:
            return []
        clauses: list[str] = []
        params: list[Any] = []
        if "source_session_id" in have:
            clauses.append("source_session_id = ?")
            params.append(session_id)
        if session_key and "source_session_key" in have:
            clauses.append("source_session_key = ?")
            params.append(session_key)
        if not clauses:
            return []
        try:
            rows = conn.execute(
                "SELECT %s FROM operator_approvals WHERE %s "
                "ORDER BY created_at_ms ASC LIMIT %d"
                % (", ".join(have), " OR ".join(clauses), _MAX_DB_ROWS),
                params,
            ).fetchall()
        except sqlite3.Error as exc:
            logger.debug("openclaw replay: operator_approvals unreadable: %s", exc)
            return []
        return [dict(r) for r in rows]

    def subagent_runs(self, session_key: Optional[str]) -> list[dict[str, Any]]:
        if not session_key:
            return []
        conn = self._db()
        if conn is None or not _table_exists(conn, "subagent_runs"):
            return []
        cols = _columns(conn, "subagent_runs")
        need = {"run_id", "child_session_key", "requester_session_key", "created_at"}
        if not need.issubset(cols):
            return []
        has_ctrl = "controller_session_key" in cols
        has_payload = "payload_json" in cols
        select = ["run_id", "child_session_key", "requester_session_key", "created_at"]
        if has_ctrl:
            select.append("controller_session_key")
        if has_payload:
            select.append("payload_json")
        where = "requester_session_key = ?"
        params: list[Any] = [session_key]
        if has_ctrl:
            where += " OR controller_session_key = ?"
            params.append(session_key)
        try:
            rows = conn.execute(
                "SELECT %s FROM subagent_runs WHERE %s "
                "ORDER BY created_at ASC LIMIT %d"
                % (", ".join(select), where, _MAX_DB_ROWS),
                params,
            ).fetchall()
        except sqlite3.Error as exc:
            logger.debug("openclaw replay: subagent_runs unreadable: %s", exc)
            return []
        return [dict(r) for r in rows]


# ── transcript stream ────────────────────────────────────────────────────────


def _read_records(path: str) -> Iterator[tuple[int, dict[str, Any]]]:
    """(line number, record) for every well-formed JSON object line."""
    try:
        with open(path, encoding="utf-8", errors="replace") as fh:
            for n, line in enumerate(fh, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except ValueError:
                    continue
                if isinstance(obj, dict):
                    yield n, obj
    except OSError as exc:
        logger.debug("openclaw replay: cannot read %s: %s", path, exc)


def _tool_result_event(prefix: str, session_id: str, ts: float,
                       tool_use_id: Any, content: Any, is_error: Any,
                       fallback_id: str) -> dict[str, Any]:
    tu = tool_use_id if isinstance(tool_use_id, str) and tool_use_id else ""
    span = "%s:result:%s" % (prefix, tu or fallback_id)
    types: list[str] = []
    if isinstance(content, list):
        seen: set[str] = set()
        for block in content:
            if isinstance(block, dict):
                bt = block.get("type")
                if isinstance(bt, str) and bt and bt not in seen:
                    seen.add(bt)
                    types.append(bt)
    payload: dict[str, Any] = {
        "tool_use_id": tu or None,
        "is_error": bool(is_error),
        "output": _clip(_text(content)),
    }
    if types:
        payload["content_types"] = sorted(types)
    return {
        "ts": ts, "kind": _rs.KIND_TOOL_RESULT, "span_id": span,
        "parent_span_id": None, "session_id": session_id, "runtime": RUNTIME,
        "payload": payload,
    }


def _transcript_events(path: str, session_id: str, prefix: str,
                       header: dict[str, Any]) -> Iterator[dict[str, Any]]:
    """Canonical events for one v3 transcript, in file order.

    ``header`` is filled from the leading ``session`` record (``cwd``,
    ``version``, ``ts``) so the caller can stamp the ``mode.changed`` event.
    """
    last_ts = 0.0
    turn = 0
    for n, obj in _read_records(path):
        t = obj.get("type")
        rid = obj.get("id")
        rid = rid if isinstance(rid, str) and rid else "ln%d" % n
        ts = _ts(obj.get("timestamp"), last_ts)
        if ts:
            last_ts = ts

        if t == "session":
            if not header:
                header["ts"] = ts
                cwd = obj.get("cwd")
                if isinstance(cwd, str) and cwd:
                    header["cwd"] = cwd
                version = obj.get("version")
                if version is not None:
                    header["version"] = str(version)
            continue

        if t == "message":
            msg = obj.get("message")
            if not isinstance(msg, dict):
                continue
            role = msg.get("role")
            content = msg.get("content")
            # The envelope timestamp orders the file; the inner message
            # timestamp is coarser and only used when the envelope has none.
            if obj.get("timestamp") is not None:
                mts = ts
            else:
                mts = _ts(msg.get("timestamp"), ts) or ts
            if role == "user":
                blocks = content if isinstance(content, list) else []
                results = [b for b in blocks
                           if isinstance(b, dict) and b.get("type") == "tool_result"]
                for i, block in enumerate(results):
                    yield _tool_result_event(
                        prefix, session_id, mts, block.get("tool_use_id")
                        or block.get("toolUseId"), block.get("content"),
                        block.get("is_error"), "%s:%d" % (rid, i))
                text = _text(content)
                if text or not results:
                    turn += 1
                    yield {
                        "ts": mts, "kind": _rs.KIND_LLM_CALL,
                        "span_id": "%s:call:%s" % (prefix, rid),
                        "parent_span_id": None, "session_id": session_id,
                        "runtime": RUNTIME,
                        "payload": {"turn": turn, "text": _clip(text)},
                    }
            elif role == "assistant":
                blocks = content if isinstance(content, list) else []
                thinking_n = 0
                tool_n = 0
                texts: list[str] = []
                tool_calls: list[dict[str, Any]] = []
                for block in blocks:
                    if not isinstance(block, dict):
                        continue
                    bt = block.get("type")
                    if bt == "thinking":
                        thinking_n += 1
                        yield {
                            "ts": mts, "kind": _rs.KIND_THINKING,
                            "span_id": "%s:think:%s:%d" % (prefix, rid, thinking_n),
                            "parent_span_id": None, "session_id": session_id,
                            "runtime": RUNTIME,
                            "payload": {"text": _clip(block.get("thinking")
                                                      if isinstance(block.get("thinking"), str)
                                                      else block.get("text"))},
                        }
                    elif bt == "text":
                        val = block.get("text")
                        if isinstance(val, str):
                            texts.append(val)
                    elif bt == "tool_use":
                        tool_n += 1
                        tid = block.get("id")
                        tid = tid if isinstance(tid, str) and tid else "%s:%d" % (rid, tool_n)
                        tool_calls.append({
                            "ts": mts, "kind": _rs.KIND_TOOL_CALL,
                            "span_id": "%s:tool:%s" % (prefix, tid),
                            "parent_span_id": None, "session_id": session_id,
                            "runtime": RUNTIME,
                            "payload": {
                                "tool_use_id": tid,
                                "name": block.get("name") or "tool",
                                "input": block.get("input")
                                if isinstance(block.get("input"), dict) else {},
                            },
                        })
                if isinstance(content, str):
                    texts.append(content)
                payload: dict[str, Any] = {
                    "text": _clip("".join(texts)),
                    "model": msg.get("model"),
                    "provider": msg.get("provider"),
                    "stop_reason": msg.get("stopReason"),
                    "usage": _usage(msg.get("usage")),
                    "tool_calls": len(tool_calls),
                }
                api = msg.get("api")
                if isinstance(api, str) and api:
                    payload["api"] = api
                yield {
                    "ts": mts, "kind": _rs.KIND_LLM_RESPONSE,
                    "span_id": "%s:resp:%s" % (prefix, rid),
                    "parent_span_id": None, "session_id": session_id,
                    "runtime": RUNTIME, "payload": payload,
                }
                for ev in tool_calls:
                    yield ev
            continue

        if t == "tool_use":
            tid = obj.get("id")
            tid = tid if isinstance(tid, str) and tid else rid
            yield {
                "ts": ts, "kind": _rs.KIND_TOOL_CALL,
                "span_id": "%s:tool:%s" % (prefix, tid),
                "parent_span_id": None, "session_id": session_id,
                "runtime": RUNTIME,
                "payload": {
                    "tool_use_id": tid,
                    "name": obj.get("name") or "tool",
                    "input": obj.get("input") if isinstance(obj.get("input"), dict) else {},
                },
            }
            continue

        if t == "tool_use_result":
            yield _tool_result_event(
                prefix, session_id, ts, obj.get("tool_use_id") or obj.get("toolUseId"),
                obj.get("content"), obj.get("is_error"), rid)
            continue

        if t == "compaction":
            yield {
                "ts": ts, "kind": _rs.KIND_COMPACTION,
                "span_id": "%s:compaction:%s" % (prefix, rid),
                "parent_span_id": None, "session_id": session_id,
                "runtime": RUNTIME,
                "payload": {
                    "tokens_before": _int(obj.get("tokensBefore") or obj.get("tokens_before")),
                    "tokens_after": _int(obj.get("tokensAfter") or obj.get("tokens_after")),
                },
            }
            continue
        # model_change, thinking_level_change, cwd_change and anything else
        # have no canonical kind; the event ingest already records them.


# ── state-database events ────────────────────────────────────────────────────


_APPROVED = {"approve", "approved", "allow", "allowed", "accept", "accepted"}
_DENIED = {"deny", "denied", "reject", "rejected", "refuse", "refused"}
_TIMEOUT = {"expired", "expire", "timeout", "timed_out", "timed-out"}


def _approval_status(row: dict[str, Any]) -> Optional[str]:
    decision = str(row.get("decision") or "").lower()
    status = str(row.get("status") or "").lower()
    reason = str(row.get("terminal_reason") or "").lower()
    if decision in _APPROVED or status in _APPROVED:
        return "approved"
    if decision in _DENIED or status in _DENIED:
        return "denied"
    if decision in _TIMEOUT or status in _TIMEOUT or reason in _TIMEOUT:
        return "timeout"
    return None


def _resolver(kind: Any) -> str:
    k = str(kind or "").lower()
    if not k:
        return "unknown"
    if k in ("system", "policy", "auto", "rule"):
        return "policy"
    if k in ("hook",):
        return "hook"
    if k in ("model",):
        return "model"
    if k in ("operator", "user", "device", "reviewer", "human", "client"):
        return "user"
    return "unknown"


def _approval_events(rows: list[dict[str, Any]], session_id: str,
                     prefix: str, tool_spans: dict[str, str],
                     ) -> Iterator[dict[str, Any]]:
    """``approval.requested`` / ``approval.decided`` per ``operator_approvals``
    row. When the row names a tool call the transcript emitted, both events
    point at that ``tool.call`` span through ``parent_span_id``: that is the
    gate the replay tree hangs an approval on. A row for a call the
    transcript does not show stays unattached and still counts."""
    for row in rows:
        aid = row.get("approval_id")
        if not isinstance(aid, str) or not aid:
            continue
        requested_ts = _ts(row.get("created_at_ms"))
        if not requested_ts:
            continue
        call_id = row.get("source_tool_call_id")
        gate = tool_spans.get(call_id) if isinstance(call_id, str) else None
        payload = {
            "approval_id": aid,
            "kind": row.get("kind"),
            "tool_name": row.get("source_tool_name"),
            "tool_call_id": row.get("source_tool_call_id"),
            "source": "operator_approvals",
        }
        yield {
            "ts": requested_ts, "kind": _rs.KIND_APPROVAL_REQUESTED,
            "span_id": "%s:approval:%s:requested" % (prefix, aid),
            "parent_span_id": gate, "session_id": session_id, "runtime": RUNTIME,
            "payload": dict(payload),
            "approval": {"status": "requested", "decision_reason": None,
                         "resolver": None, "edit_diff": None},
        }
        status = _approval_status(row)
        if status is None:
            continue
        decided_ts = (_ts(row.get("resolved_at_ms"))
                      or _ts(row.get("updated_at_ms")) or requested_ts)
        reason = row.get("terminal_reason")
        yield {
            "ts": decided_ts, "kind": _rs.KIND_APPROVAL_DECIDED,
            "span_id": "%s:approval:%s:decided" % (prefix, aid),
            "parent_span_id": gate, "session_id": session_id, "runtime": RUNTIME,
            "payload": dict(payload),
            "approval": {
                "status": status,
                "decision_reason": str(reason) if reason not in (None, "") else None,
                "resolver": _resolver(row.get("resolver_kind")),
                "edit_diff": None,
            },
        }


_SPAWN_PAYLOAD_KEYS = (
    ("task", "task"), ("task_name", "task_name"), ("taskName", "task_name"),
    ("model", "model"), ("spawn_mode", "spawn_mode"), ("spawnMode", "spawn_mode"),
    ("workspace_dir", "workspace_dir"), ("workspaceDir", "workspace_dir"),
    ("agent_id", "agent_id"), ("agentId", "agent_id"),
)


def _spawn_events(rows: list[dict[str, Any]], session_id: str, prefix: str,
                  sources: _Sources) -> Iterator[dict[str, Any]]:
    for row in rows:
        run_id = row.get("run_id")
        if not isinstance(run_id, str) or not run_id:
            continue
        ts = _ts(row.get("created_at"))
        if not ts:
            continue
        child_key = row.get("child_session_key")
        payload: dict[str, Any] = {
            "run_id": run_id,
            "child_session_key": child_key,
            "child_session_id": sources.session_id_for_key(child_key),
            "controller_session_key": row.get("controller_session_key"),
            "requester_session_key": row.get("requester_session_key"),
            "source": "subagent_runs",
        }
        raw = row.get("payload_json")
        extra: Any = None
        if isinstance(raw, str) and raw:
            try:
                extra = json.loads(raw)
            except ValueError:
                extra = None
        if isinstance(extra, dict):
            for src, dst in _SPAWN_PAYLOAD_KEYS:
                val = extra.get(src)
                if dst not in payload and isinstance(val, str) and val:
                    payload[dst] = _clip(val)
        yield {
            "ts": ts, "kind": _rs.KIND_AGENT_SPAWN,
            "span_id": "%s:spawn:%s" % (prefix, run_id),
            "parent_span_id": None, "session_id": session_id, "runtime": RUNTIME,
            "payload": payload,
        }


# ── entry point ──────────────────────────────────────────────────────────────


def default_state_db() -> str:
    try:
        from clawmetry import sync as _sync
        home = _sync._get_openclaw_dir()
    except Exception:
        home = os.path.expanduser("~/.openclaw")
    return os.path.join(home, "state", "openclaw.sqlite")


def default_sessions_dir() -> Optional[str]:
    """The directory the daemon reads transcripts from (legacy or mirror)."""
    try:
        from clawmetry import sync as _sync
        return _sync._openclaw_sessions_dir()
    except Exception as exc:
        logger.debug("openclaw replay: sessions dir unresolved: %s", exc)
        return None


def transcript_path(session_id: str, sessions_dir: Optional[str]) -> Optional[str]:
    if not session_id or not sessions_dir:
        return None
    if "/" in session_id or os.sep in session_id or session_id in (".", ".."):
        return None
    candidate = os.path.join(sessions_dir, session_id + ".jsonl")
    return candidate if os.path.isfile(candidate) else None


def iter_replay_events(session_id: str, limit: int = 5000, *,
                       sessions_dir: Optional[str] = None,
                       state_db: Optional[str] = None,
                       ) -> Iterator[dict[str, Any]]:
    """Canonical replay events for one OpenClaw session, oldest first.

    The transcript is read in file order; approvals and sub-agent spawns
    from the state database are merged in by timestamp (stable, so a tie
    keeps transcript order). One ``mode.changed`` leads. Never raises.
    """
    try:
        budget = max(0, int(limit))
    except (TypeError, ValueError):
        budget = 5000
    if budget <= 0:
        return
    sid = session_id if isinstance(session_id, str) else ""
    if not sid:
        return
    sdir = sessions_dir if sessions_dir else default_sessions_dir()
    path = transcript_path(sid, sdir)
    if not path:
        return
    prefix = "%s:%s" % (RUNTIME, sid)
    sources = _Sources(sdir, state_db if state_db is not None else default_state_db())
    try:
        header: dict[str, Any] = {}
        transcript = list(_transcript_events(path, sid, prefix, header))
        session_key = sources.session_key(sid)
        exec_row = sources.exec_mode()
        tool_spans = {
            e["payload"]["tool_use_id"]: e["span_id"] for e in transcript
            if e["kind"] == _rs.KIND_TOOL_CALL
            and isinstance(e["payload"].get("tool_use_id"), str)
        }
        extra: list[dict[str, Any]] = []
        extra.extend(_approval_events(
            sources.approvals(sid, session_key), sid, prefix, tool_spans))
        extra.extend(_spawn_events(sources.subagent_runs(session_key), sid, prefix, sources))

        first_ts = header.get("ts") or (transcript[0]["ts"] if transcript else 0.0)
        if not first_ts and extra:
            first_ts = min(e["ts"] for e in extra)
        mode: dict[str, Any] = {"permission": permission_from_exec(exec_row)}
        collab = _collaboration(session_key)
        if collab:
            mode["collaboration"] = collab
        mode_payload: dict[str, Any] = {
            "source": "exec_approvals_config" if exec_row else None,
            "session_key": session_key,
        }
        if exec_row:
            mode_payload.update({
                "security": exec_row.get("default_security"),
                "ask": exec_row.get("default_ask"),
                "ask_fallback": exec_row.get("default_ask_fallback"),
                "auto_allow_skills": (bool(exec_row.get("auto_allow_skills"))
                                      if exec_row.get("auto_allow_skills") is not None
                                      else None),
                "agent_overrides": _int(exec_row.get("agent_count")),
                "allowlist_entries": _int(exec_row.get("allowlist_count")),
            })
        for k in ("cwd", "version"):
            if header.get(k):
                mode_payload[k] = header[k]
        events: list[dict[str, Any]] = [{
            "ts": float(first_ts or 0.0), "kind": _rs.KIND_MODE_CHANGED,
            "span_id": "%s:mode" % prefix, "parent_span_id": None,
            "session_id": sid, "runtime": RUNTIME, "payload": mode_payload,
            "mode": mode,
        }]
        # Stable merge: transcript order is kept for equal timestamps and
        # the mode marker always leads.
        merged = sorted(transcript + extra, key=lambda e: e["ts"])
        events.extend(merged)
        for ev in events:
            if budget <= 0:
                return
            budget -= 1
            yield ev
    except Exception as exc:  # a bad record never sinks the replay
        logger.warning("openclaw replay of %s stopped: %s", sid, exc)
    finally:
        sources.close()
