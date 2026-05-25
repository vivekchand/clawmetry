"""QwenCodeAdapter — read Qwen Code chat-recording history from disk.

Qwen Code (https://github.com/QwenLM/qwen-code) is Alibaba's open-source
coding CLI, a fork of Google's Gemini CLI. It supports any OpenAI-compatible
provider (Qwen API, OpenRouter, a local Ollama ``/v1`` endpoint, ...) via the
``OPENAI_API_KEY`` / ``OPENAI_BASE_URL`` / ``OPENAI_MODEL`` env vars.

Like the Claude Code and PicoClaw adapters, this is a non-OpenClaw filesystem
reader that subclasses :class:`AgentAdapter` directly. The native format is
Qwen Code's own Gemini-CLI-lineage chat recording, NOT OpenClaw's v3 envelope.

On-disk layout
--------------
Chat recording is written (when enabled with ``--chat-recording`` or the
``general.chatRecording`` setting) under the per-project directory::

    ~/.qwen/projects/<project-hash>/chats/<sessionId>.jsonl

``<project-hash>`` is the working-directory path with ``/`` replaced by ``-``
(e.g. ``-private-tmp-qwen-real-run``). One ``.jsonl`` file per session; one
JSON record per line.

Each line is a record with a flat envelope plus a nested ``message``::

    {
      "uuid": "...",                 # this record's id
      "parentUuid": "..." | null,    # previous record (a chain, not a tree)
      "sessionId": "...",            # == the file's basename
      "timestamp": "2026-05-25T20:41:03.715Z",   # ISO-8601, UTC "Z"
      "type": "user" | "assistant" | "tool_result" | "system",
      "cwd": "...",
      "version": "0.16.1",
      "model": "qwen3:8b",           # present on assistant records
      "message": { "role": ..., "parts": [ ... ] },
      "usageMetadata": { ... }       # present on assistant records
    }

The ``message.parts`` array is the Gemini ``Content.parts`` shape:
  - user text:        ``{"text": "..."}``                (role ``user``)
  - assistant text:   ``{"text": "..."}``                (role ``model``)
  - assistant reasoning: ``{"text": "...", "thought": true}``
  - tool call:        ``{"functionCall": {"id", "name", "args"}}``
  - tool result:      ``{"functionResponse": {"id", "name", "response": {...}}}``
    (carried on a ``type:"tool_result"`` record whose ``message.role`` is ``user``)

Note the assistant role on disk is the Gemini ``"model"`` string, which we
normalise to ``"assistant"`` for the unified Event schema.

Tokens ARE on disk. Assistant records carry ``usageMetadata`` with
``promptTokenCount`` / ``candidatesTokenCount`` / ``thoughtsTokenCount`` /
``totalTokenCount`` / ``cachedContentTokenCount``. We surface real token
counts and advertise the COST capability. Cost in USD is NOT recorded (the
endpoint may be a free local Ollama), so ``cost_usd`` stays ``None`` and is
left for downstream pricing — we never fabricate a dollar figure.

``type:"system"`` records (``attribution_snapshot`` / ``ui_telemetry``) are
control/telemetry, not conversation, and are skipped for events.

The adapter is read-only and never modifies the Qwen Code data directory.
"""
from __future__ import annotations

import glob
import json
import logging
import os
import re
from datetime import datetime, timezone
from typing import Any

from .base import AgentAdapter, Capability, DetectResult, Event, Session

logger = logging.getLogger("clawmetry.adapters.qwen_code")

_AGENT = "qwen_code"

# Normalises the fractional-seconds run of an ISO-8601 timestamp to exactly 6
# digits. datetime.fromisoformat() on Python 3.9/3.10 only accepts 0, 3, or 6
# fractional digits; Qwen Code emits millisecond precision (3 digits, e.g.
# ".715Z") which is fine, but we pad/truncate defensively so any odd-length
# fraction from a future version still parses instead of silently becoming 0.0.
# (ClawMetry CI runs Py3.9.)
_FRAC_RE = re.compile(r"\.(\d+)")


# -- helpers -----------------------------------------------------------------


def _qwen_home() -> str:
    return os.environ.get("QWEN_HOME") or os.path.expanduser("~/.qwen")


def _projects_dir() -> str:
    return os.path.join(_qwen_home(), "projects")


def _parse_ts(ts: Any) -> float:
    """Parse an ISO-8601 string or numeric epoch to float seconds.

    Returns 0.0 for anything unparseable so callers never crash on a bad
    or missing timestamp.
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
        # Pad/truncate fractional seconds to 6 digits for Python 3.9/3.10.
        s = _FRAC_RE.sub(lambda m: "." + (m.group(1) + "000000")[:6], s, count=1)
        dt = datetime.fromisoformat(s)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.timestamp()
    except (ValueError, AttributeError):
        return 0.0


def _norm_role(record_type: str, message: dict[str, Any]) -> str:
    """Normalise the on-disk role to the unified schema.

    Qwen Code (Gemini lineage) uses ``model`` for the assistant role and
    carries tool results on a ``user``-role record tagged ``type:tool_result``.
    We map: model -> assistant, tool_result record -> tool, else the raw role.
    """
    if record_type == "tool_result":
        return "tool"
    role = (message or {}).get("role") or ""
    if role == "model":
        return "assistant"
    return role


def _iter_records(path: str):
    """Yield parsed record dicts from a chat-recording JSONL file.

    Defensive: skips blank lines, lines that do not parse as JSON, and any
    line that is not a dict. Never raises on a single bad line.
    """
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
                if not isinstance(obj, dict):
                    continue
                yield obj
    except OSError as exc:
        logger.warning("QwenCodeAdapter: cannot read %s: %s", path, exc)
        return


def _parts_text(parts: Any) -> tuple[str, str]:
    """Split a ``message.parts`` array into (final_text, reasoning_text).

    Reasoning parts are ``{"text": ..., "thought": true}``; everything else
    with a ``text`` is treated as visible content. Returns joined strings
    (empty when absent). Non-list / malformed parts yield ("", "").
    """
    if not isinstance(parts, list):
        return "", ""
    visible: list[str] = []
    thoughts: list[str] = []
    for p in parts:
        if not isinstance(p, dict):
            continue
        txt = p.get("text")
        if not isinstance(txt, str) or not txt:
            continue
        if p.get("thought"):
            thoughts.append(txt)
        else:
            visible.append(txt)
    return "\n".join(visible), "\n".join(thoughts)


def _first_user_text(path: str) -> str:
    """Return the first user-message text in a session, for use as a title."""
    for obj in _iter_records(path):
        if obj.get("type") != "user":
            continue
        msg = obj.get("message")
        if not isinstance(msg, dict):
            continue
        visible, _ = _parts_text(msg.get("parts"))
        if visible:
            # Single-line, trimmed title.
            return " ".join(visible.split())[:200]
    return ""


def _session_from_file(path: str, session_id: str) -> Session | None:
    """Build a unified :class:`Session` from one chat-recording JSONL file.

    Walks every record once to count conversational messages, find the
    first/last timestamps, the model, and sum the latest usage metadata.
    Returns ``None`` only if the file cannot be stat'd at all.
    """
    model = ""
    msg_count = 0
    first_ts = 0.0
    last_ts = 0.0
    total_tokens = 0
    input_tokens = 0
    output_tokens = 0
    cache_read_tokens = 0
    reasoning_tokens = 0
    title = ""

    for obj in _iter_records(path):
        rtype = obj.get("type") or ""
        # Skip control/telemetry records for counting and titling.
        if rtype == "system":
            continue

        ts = _parse_ts(obj.get("timestamp"))
        if ts:
            if not first_ts:
                first_ts = ts
            last_ts = ts

        if rtype in ("user", "assistant", "tool_result"):
            msg_count += 1

        if rtype == "user" and not title:
            msg = obj.get("message")
            if isinstance(msg, dict):
                visible, _ = _parts_text(msg.get("parts"))
                if visible:
                    title = " ".join(visible.split())[:200]

        if rtype == "assistant":
            mdl = obj.get("model")
            if isinstance(mdl, str) and mdl:
                model = mdl  # last non-empty model wins
            usage = obj.get("usageMetadata")
            if isinstance(usage, dict):
                # usageMetadata is cumulative-per-call; sum across calls so the
                # session total reflects every model round-trip honestly.
                total_tokens += _int(usage.get("totalTokenCount"))
                input_tokens += _int(usage.get("promptTokenCount"))
                output_tokens += _int(usage.get("candidatesTokenCount"))
                cache_read_tokens += _int(usage.get("cachedContentTokenCount"))
                reasoning_tokens += _int(usage.get("thoughtsTokenCount"))

    ended_at: float | None = last_ts or None
    if ended_at is None:
        try:
            ended_at = os.path.getmtime(path)
        except OSError:
            ended_at = None
    if not first_ts and ended_at:
        first_ts = ended_at

    return Session(
        agent=_AGENT,
        id=session_id,
        title=title,
        display_name=title or session_id,
        model=model,
        source="qwen_code",
        started_at=first_ts,
        ended_at=ended_at,
        message_count=msg_count,
        total_tokens=total_tokens,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        cache_read_tokens=cache_read_tokens,
        reasoning_tokens=reasoning_tokens,
        # Cost in USD is not recorded on disk (the endpoint may be a free local
        # Ollama). We surface real tokens but leave the dollar figure unknown
        # rather than fabricate one.
        cost_usd=None,
        cost_status="tokens_only",
        extra={"costUsdUnavailable": True},
    )


def _int(v: Any) -> int:
    """Best-effort int coercion; 0 for anything non-numeric."""
    if isinstance(v, bool):
        return 0
    if isinstance(v, (int, float)):
        return int(v)
    return 0


# -- adapter -----------------------------------------------------------------


class QwenCodeAdapter(AgentAdapter):
    """Adapter for Qwen Code chat-recording sessions under ``~/.qwen``."""

    name = "qwen_code"
    display_name = "Qwen Code"

    def __init__(self, projects_dir: str | None = None) -> None:
        # Overridable for testing; defaults to QWEN_HOME/projects.
        self._projects_dir = projects_dir or _projects_dir()

    @property
    def projects_dir(self) -> str:
        return self._projects_dir

    # -- discovery (bounded) -------------------------------------------------

    def _session_files(self) -> list[str]:
        """Return chat-recording .jsonl files across all project dirs.

        Bounded discovery: only globs ``<projects>/*/chats/*.jsonl`` — one
        level of project dirs, never a recursive walk of ``$HOME``.
        """
        root = self._projects_dir
        if not os.path.isdir(root):
            return []
        try:
            return glob.glob(os.path.join(root, "*", "chats", "*.jsonl"))
        except OSError as exc:
            logger.warning("QwenCodeAdapter session glob failed: %s", exc)
            return []

    # -- AgentAdapter contract -----------------------------------------------

    def detect(self) -> DetectResult:
        """Cheap detection. Never raises.

        ``detected`` is True when the projects dir exists with >=1 session
        log, or when the Qwen home exists (installed but no recordings yet).
        ``running`` is always False — there is no live gateway for Qwen Code.
        """
        home = _qwen_home()
        try:
            files = self._session_files()
            session_count = len(files)
            has_home = os.path.isdir(home)
            detected = session_count > 0 or has_home
            return DetectResult(
                name=self.name,
                display_name=self.display_name,
                detected=detected,
                running=False,
                workspace=home,
                session_count=session_count,
                capabilities=[c.value for c in self.capabilities()],
                meta={"projectsDir": self._projects_dir},
            )
        except Exception as exc:  # belt-and-suspenders: detect() must never raise
            logger.debug("QwenCodeAdapter detect() failed: %s", exc)
            return DetectResult(
                name=self.name,
                display_name=self.display_name,
                detected=False,
                running=False,
                workspace=home,
                capabilities=[c.value for c in self.capabilities()],
                meta={"error": str(exc)},
            )

    def list_sessions(self, limit: int = 100) -> list[Session]:
        """Return recent sessions, newest first. Never raises on a bad file."""
        files = self._session_files()
        if not files:
            return []

        sessions: list[Session] = []
        for path in files:
            session_id = os.path.basename(path)[:-6]  # strip ".jsonl"
            try:
                sess = _session_from_file(path, session_id)
            except Exception as exc:
                # Never let one bad session sink the whole list.
                logger.warning("QwenCodeAdapter: skipping bad session %s: %s", path, exc)
                continue
            if sess is not None:
                sessions.append(sess)

        # Sort by logical activity time, newest first. We sort on the parsed
        # timestamp (last record / mtime fallback), NOT raw file mtime, so the
        # ordering is deterministic across a git checkout or file copy in CI.
        sessions.sort(key=lambda s: s.ended_at or s.started_at or 0.0, reverse=True)
        return sessions[:limit]

    def list_events(self, session_id: str, limit: int = 500) -> list[Event]:
        """Parse one session's chat recording into unified events.

        Records are already chronological on disk (one append per turn). We
        emit, per record: a ``thinking`` event for any reasoning part, a
        ``message`` event for visible text, a ``tool_call`` event per
        functionCall, and a ``tool_result`` event for a tool-result record.
        """
        path = self._find_session_path(session_id)
        if not path:
            return []

        events: list[Event] = []
        seq = 0
        for obj in _iter_records(path):
            if len(events) >= limit:
                break
            rtype = obj.get("type") or ""
            if rtype == "system":
                # attribution_snapshot / ui_telemetry — not conversation.
                continue

            ts = _parse_ts(obj.get("timestamp"))
            msg = obj.get("message") if isinstance(obj.get("message"), dict) else {}
            role = _norm_role(rtype, msg)
            parts = msg.get("parts")
            model = obj.get("model") if isinstance(obj.get("model"), str) else ""

            if rtype == "tool_result":
                # parts hold one or more functionResponse objects.
                if isinstance(parts, list):
                    for p in parts:
                        if not isinstance(p, dict):
                            continue
                        if len(events) >= limit:
                            break
                        fr = p.get("functionResponse")
                        if not isinstance(fr, dict):
                            continue
                        resp = fr.get("response")
                        content = ""
                        if isinstance(resp, dict):
                            out = resp.get("output")
                            content = out if isinstance(out, str) else json.dumps(resp)
                        elif resp is not None:
                            content = json.dumps(resp)
                        seq += 1
                        events.append(Event(
                            agent=_AGENT,
                            session_id=session_id,
                            id=f"{session_id}:{seq}",
                            type="tool_result",
                            ts=ts,
                            role="tool",
                            content=content,
                            tool_name=fr.get("name") or "",
                            extra={"toolCallId": fr.get("id") or ""},
                        ))
                continue

            # user / assistant records: split parts into thinking, text, calls.
            visible, reasoning = _parts_text(parts)

            if reasoning:
                seq += 1
                events.append(Event(
                    agent=_AGENT,
                    session_id=session_id,
                    id=f"{session_id}:{seq}",
                    type="thinking",
                    ts=ts,
                    role=role or "assistant",
                    content=reasoning,
                    tokens=0,
                    extra={"model": model} if model else {},
                ))

            if visible:
                seq += 1
                events.append(Event(
                    agent=_AGENT,
                    session_id=session_id,
                    id=f"{session_id}:{seq}",
                    type="message",
                    ts=ts,
                    role=role,
                    content=visible,
                    tokens=self._record_output_tokens(obj),
                    extra={"model": model} if model else {},
                ))

            # Each functionCall part becomes its own tool_call event.
            if isinstance(parts, list):
                for p in parts:
                    if not isinstance(p, dict):
                        continue
                    if len(events) >= limit:
                        break
                    fc = p.get("functionCall")
                    if not isinstance(fc, dict):
                        continue
                    name = fc.get("name") or "unknown"
                    seq += 1
                    events.append(Event(
                        agent=_AGENT,
                        session_id=session_id,
                        id=f"{session_id}:{seq}",
                        type="tool_call",
                        ts=ts,
                        role=role or "assistant",
                        tool_name=name,
                        tool_calls=[{
                            "id": fc.get("id") or "",
                            "name": name,
                            "arguments": fc.get("args"),
                        }],
                        extra={"model": model} if model else {},
                    ))
        return events

    def _find_session_path(self, session_id: str) -> str | None:
        """Locate the .jsonl for a session id across project dirs.

        The same session id is the file basename, so a bounded glob across
        the one-level project dirs finds it without walking ``$HOME``.
        """
        if not session_id:
            return None
        for path in self._session_files():
            if os.path.basename(path)[:-6] == session_id:
                return path
        return None

    @staticmethod
    def _record_output_tokens(obj: dict[str, Any]) -> int:
        """Output (candidate) token count for an assistant record, else 0."""
        usage = obj.get("usageMetadata")
        if isinstance(usage, dict):
            return _int(usage.get("candidatesTokenCount"))
        return 0

    def capabilities(self) -> set[Capability]:
        # SESSIONS + EVENTS + COST. Unlike PicoClaw, Qwen Code records real
        # usageMetadata token counts on every assistant record, so COST is
        # honestly claimed (the UI may price tokens). The USD figure itself is
        # not on disk and is left as None.
        return {Capability.SESSIONS, Capability.EVENTS, Capability.COST}
