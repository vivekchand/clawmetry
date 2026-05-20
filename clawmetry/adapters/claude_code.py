"""ClaudeCodeAdapter — session listing and span ingestion from Claude Code JSONL.

Reads ``~/.claude/projects/<project-slug>/<session-id>.jsonl`` and maps
each conversation turn into OTel-shaped spans stored in the local DuckDB
``spans`` table. Phase 5 of the tracing epic (#1006).

Span mapping (per issue #1011):
  * assistant turn           → ``llm.call`` span
  * ``tool_use`` block       → ``tool.<name>`` child span
  * ``tool_use`` name=Task   → ``agent.spawn`` child span
  * ``thinking`` block       → ``thinking`` child span (kind=INTERNAL)

The adapter is read-only and never modifies the Claude Code data directory.
"""
from __future__ import annotations

import json
import logging
import os
import uuid
from datetime import datetime, timezone
from typing import Any

from .base import AgentAdapter, Capability, DetectResult, Event, Session

logger = logging.getLogger("clawmetry.adapters.claude_code")

_AGENT_TYPE = "claude_code"
_AGENT_ID = "claude-code"


# ── helpers ───────────────────────────────────────────────────────────────────────────────


def _projects_root() -> str:
    cfg = os.environ.get("CLAUDE_CONFIG_DIR")
    base = cfg if cfg else os.path.expanduser("~/.claude")
    return os.path.join(base, "projects")


def _parse_ts(ts: Any) -> float:
    """Parse ISO-8601 string or numeric epoch (seconds) to float seconds."""
    if ts is None:
        return 0.0
    if isinstance(ts, (int, float)):
        return float(ts)
    try:
        s = str(ts)
        if s.endswith("Z"):
            s = s[:-1] + "+00:00"
        dt = datetime.fromisoformat(s)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.timestamp()
    except (ValueError, AttributeError):
        return 0.0


def _span_id(prefix: str, uid: str) -> str:
    return f"cc-{prefix}:{uid}"


def _is_tool_result_only(content: Any) -> bool:
    """Return True when a user message contains only tool-result blocks."""
    if isinstance(content, list) and content:
        return all(
            isinstance(c, dict) and c.get("type") == "tool_result"
            for c in content
        )
    return False


# ── adapter ────────────────────────────────────────────────────────────────────────────────


class ClaudeCodeAdapter(AgentAdapter):
    """Adapter for Claude Code sessions stored in ~/.claude/projects."""

    name = "claude_code"
    display_name = "Claude Code"

    # ── AgentAdapter contract ─────────────────────────────────────────────────────

    def detect(self) -> DetectResult:
        root = _projects_root()
        if not os.path.isdir(root):
            return DetectResult(
                name=self.name,
                display_name=self.display_name,
                detected=False,
                workspace=root,
                capabilities=[c.value for c in self.capabilities()],
            )
        session_count = 0
        try:
            for entry in os.scandir(root):
                if entry.is_dir():
                    for f in os.scandir(entry.path):
                        if f.name.endswith(".jsonl"):
                            session_count += 1
        except OSError:
            pass
        return DetectResult(
            name=self.name,
            display_name=self.display_name,
            detected=True,
            running=False,
            workspace=root,
            session_count=session_count,
            capabilities=[c.value for c in self.capabilities()],
            meta={"projectsRoot": root},
        )

    def list_sessions(self, limit: int = 100) -> list[Session]:
        root = _projects_root()
        if not os.path.isdir(root):
            return []
        sessions: list[Session] = []
        try:
            proj_dirs = sorted(
                (e for e in os.scandir(root) if e.is_dir()),
                key=lambda e: e.stat().st_mtime,
                reverse=True,
            )
        except OSError:
            return []
        for proj in proj_dirs:
            try:
                jsonl_files = sorted(
                    (f for f in os.scandir(proj.path) if f.name.endswith(".jsonl")),
                    key=lambda f: f.stat().st_mtime,
                    reverse=True,
                )
            except OSError:
                continue
            for f in jsonl_files:
                sess = _session_from_jsonl(f.path, f.name[:-6])
                if sess is not None:
                    sessions.append(sess)
                if len(sessions) >= limit:
                    return sessions
        return sessions

    def capabilities(self) -> set[Capability]:
        return {Capability.SESSIONS, Capability.EVENTS, Capability.COST}

    # ── span ingestion ─────────────────────────────────────────────────────────────────

    def ingest_spans(
        self,
        jsonl_path: str,
        session_id: str,
        store: Any,
    ) -> int:
        """Parse *jsonl_path* and write OTel spans into *store*.

        Returns the count of spans written. Silently skips unparseable lines
        and logs warnings for span-write failures — never raises.
        """
        try:
            with open(jsonl_path, "r", errors="replace") as fh:
                lines = fh.readlines()
        except OSError as exc:
            logger.warning("ClaudeCodeAdapter: cannot open %s: %s", jsonl_path, exc)
            return 0

        spans_written = 0
        pending_user_ts: float = 0.0

        for raw in lines:
            raw = raw.strip()
            if not raw:
                continue
            try:
                obj = json.loads(raw)
            except json.JSONDecodeError:
                continue

            evt_type = obj.get("type")

            if evt_type == "user":
                msg = obj.get("message") or {}
                content = msg.get("content")
                if not _is_tool_result_only(content):
                    pending_user_ts = _parse_ts(obj.get("timestamp")) or 0.0

            elif evt_type == "assistant":
                msg = obj.get("message") or {}
                usage = msg.get("usage") or {}
                model = msg.get("model") or ""
                content_blocks = msg.get("content") or []
                asst_ts = _parse_ts(obj.get("timestamp"))
                start_ts = pending_user_ts or asst_ts

                uid = obj.get("uuid") or obj.get("id") or uuid.uuid4().hex
                llm_sid = _span_id("llm", uid)

                spans_written += _write_span(store, {
                    "span_id": llm_sid,
                    "trace_id": session_id,
                    "parent_span_id": None,
                    "name": "llm.call",
                    "kind": "CLIENT",
                    "start_ts": start_ts,
                    "end_ts": asst_ts,
                    "agent_type": _AGENT_TYPE,
                    "agent_id": _AGENT_ID,
                    "session_id": session_id,
                    "model": model,
                    "tokens_input": int(usage.get("input_tokens") or 0),
                    "tokens_output": int(usage.get("output_tokens") or 0),
                    "token_count": int(
                        (usage.get("input_tokens") or 0)
                        + (usage.get("output_tokens") or 0)
                    ),
                    "attributes": {"gen_ai.system": "anthropic"},
                })

                for block in content_blocks:
                    if not isinstance(block, dict):
                        continue
                    btype = block.get("type")
                    if btype == "thinking":
                        t_uid = block.get("id") or uuid.uuid4().hex
                        spans_written += _write_span(store, {
                            "span_id": _span_id("thinking", t_uid),
                            "trace_id": session_id,
                            "parent_span_id": llm_sid,
                            "name": "thinking",
                            "kind": "INTERNAL",
                            "start_ts": start_ts,
                            "end_ts": asst_ts,
                            "agent_type": _AGENT_TYPE,
                            "agent_id": _AGENT_ID,
                            "session_id": session_id,
                        })
                    elif btype == "tool_use":
                        tool_name = block.get("name") or "unknown"
                        tool_uid = block.get("id") or uuid.uuid4().hex
                        span_name = (
                            "agent.spawn" if tool_name == "Task" else f"tool.{tool_name}"
                        )
                        spans_written += _write_span(store, {
                            "span_id": _span_id("tool", tool_uid),
                            "trace_id": session_id,
                            "parent_span_id": llm_sid,
                            "name": span_name,
                            "kind": "CLIENT",
                            "start_ts": asst_ts,
                            "end_ts": asst_ts,
                            "agent_type": _AGENT_TYPE,
                            "agent_id": _AGENT_ID,
                            "session_id": session_id,
                            "tool_name": tool_name,
                        })

                pending_user_ts = 0.0

        return spans_written


# ── module-level helpers ────────────────────────────────────────────────────────────────────────


def _write_span(store: Any, span: dict) -> int:
    """Write one span; return 1 on success, 0 on failure."""
    try:
        store.ingest_span(span)
        return 1
    except Exception as exc:
        logger.warning("ClaudeCodeAdapter: failed to write span %r: %s", span.get("name"), exc)
        return 0


def _session_from_jsonl(path: str, session_id: str) -> Session | None:
    """Build a Session summary by scanning one JSONL file."""
    model = ""
    total_in = total_out = cache_read = message_count = 0
    started_at = 0.0
    ended_at: float | None = None
    try:
        with open(path, "r", errors="replace") as fh:
            for raw in fh:
                raw = raw.strip()
                if not raw:
                    continue
                try:
                    obj = json.loads(raw)
                except json.JSONDecodeError:
                    continue
                ts = _parse_ts(obj.get("timestamp"))
                if not started_at:
                    started_at = ts
                t = obj.get("type")
                if t == "assistant":
                    msg = obj.get("message") or {}
                    if not model:
                        model = msg.get("model") or ""
                    usage = msg.get("usage") or {}
                    total_in += int(usage.get("input_tokens") or 0)
                    total_out += int(usage.get("output_tokens") or 0)
                    cache_read += int(usage.get("cache_read_input_tokens") or 0)
                    message_count += 1
                    ended_at = ts
                elif t == "user":
                    content = (obj.get("message") or {}).get("content")
                    if not _is_tool_result_only(content):
                        message_count += 1
    except OSError:
        return None
    return Session(
        agent=_AGENT_TYPE,
        id=session_id,
        model=model,
        started_at=started_at,
        ended_at=ended_at,
        message_count=message_count,
        input_tokens=total_in,
        output_tokens=total_out,
        total_tokens=total_in + total_out,
        cache_read_tokens=cache_read,
    )
