"""CodexAdapter — read OpenAI Codex CLI session data from its rollout files.

Codex (https://github.com/openai/codex) is OpenAI's coding agent CLI. It
does NOT share OpenClaw's session layout, so this subclasses
:class:`AgentAdapter` directly (like the Claude Code + PicoClaw adapters,
which are non-OpenClaw filesystem readers).

On-disk layout
--------------
``$CODEX_HOME/sessions/YYYY/MM/DD/rollout-<ISO-ts>-<uuid>.jsonl`` (default
``~/.codex/sessions/``, respects the ``CODEX_HOME`` env var). Sessions are
date-partitioned "rollout" transcripts; the filename carries the session
start timestamp and the session UUID, e.g.::

    rollout-2026-05-15T01-11-31-019e28c2-6d89-7f22-95a4-3c619a6a8046.jsonl

Wire format (one JSON object per line)
--------------------------------------
Every line is a ``RolloutLine`` wrapping a ``RolloutItem``::

    {"timestamp": "2026-05-14T23:11:32.007Z", "type": <kind>, "payload": {...}}

``type`` is one of ``session_meta``, ``response_item``, ``event_msg``,
``turn_context``, ``compacted``. The interesting payloads (serde tags from
``openai/codex`` ``codex-rs/protocol/src/{models,protocol}.rs``):

- ``session_meta``  -> payload ``{id, timestamp, cwd, originator,
  cli_version, source, model_provider, base_instructions}``. The session
  UUID and provider live here.
- ``turn_context``  -> payload ``{turn_id, cwd, model, approval_policy,
  sandbox_policy, effort, reasoning_effort, ...}``. The ``model`` field
  (e.g. ``gpt-5.4``) is the authoritative model for the turn.
- ``response_item`` -> payload is a tagged ``ResponseItem`` whose own
  ``type`` is one of:
    - ``message``       ``{role, content: [{type: input_text|output_text,
      text}]}`` (role developer/user/assistant)
    - ``reasoning``     ``{summary: [{type: summary_text, text}],
      content: [{type: reasoning_text|text, text}]}``
    - ``function_call`` ``{name, arguments (JSON string), call_id}``
    - ``function_call_output`` ``{call_id, output: {content | content_items}}``
    - ``local_shell_call`` / ``custom_tool_call`` / ``custom_tool_call_output``
- ``event_msg``     -> protocol-level events, tagged ``EventMsg``:
    - ``user_message``  ``{message, images, ...}``
    - ``agent_message`` ``{message, phase, ...}``
    - ``token_count``   ``{info: {total_token_usage: {input_tokens,
      cached_input_tokens, output_tokens, reasoning_output_tokens,
      total_tokens}, last_token_usage, model_context_window}, rate_limits}``
    - ``task_started`` / ``task_complete`` lifecycle markers

Tokens + cost
-------------
Codex DOES write real token usage on disk, but only via the ``token_count``
``event_msg`` once the model has responded. ``info.total_token_usage`` is a
running cumulative; we take the LAST ``total_token_usage`` seen (the final
running total) for the session-level breakdown. A session that was cut off
before any model response (no ``token_count`` line) honestly reports zero
tokens. Codex does not write a per-session USD cost, so ``cost_usd`` stays
``None`` and we surface COST only because the token breakdown is genuinely
on disk.

The adapter is read-only and never modifies the Codex data directory.
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

logger = logging.getLogger("clawmetry.adapters.codex")

_AGENT = "codex"

# Normalises the fractional-seconds part of an ISO-8601 timestamp. Codex emits
# millisecond precision with a trailing "Z" (e.g. "2026-05-14T23:11:32.007Z"),
# but datetime.fromisoformat() on Python 3.9/3.10 only accepts exactly 0, 3, or
# 6 fractional digits AND does not accept the literal "Z" suffix. We pad the
# fractional run to 6 digits and swap "Z" for "+00:00" so it parses everywhere.
# (ClawMetry CI runs Py3.9; see picoclaw.py for the same defence.)
_FRAC_RE = re.compile(r"\.(\d+)")

# rollout-<ISO-ts>-<uuid>.jsonl. The uuid is the trailing five hex groups; the
# ISO timestamp uses '-' as both date and time separators (T stays). We pull the
# uuid as the last 5 dash-joined groups so a dashed timestamp never confuses it.
_UUID_RE = re.compile(
    r"([0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12})"
)


# -- helpers -----------------------------------------------------------------


def _codex_home() -> str:
    return os.environ.get("CODEX_HOME") or os.path.expanduser("~/.codex")


def _default_sessions_root() -> str:
    return os.path.join(_codex_home(), "sessions")


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
        # Pad/truncate fractional seconds to 6 digits so Codex's millisecond
        # precision (".007") still parses on Python 3.9/3.10.
        s = _FRAC_RE.sub(lambda m: "." + (m.group(1) + "000000")[:6], s, count=1)
        dt = datetime.fromisoformat(s)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.timestamp()
    except (ValueError, AttributeError):
        return 0.0


def _ts_from_filename(basename: str) -> float:
    """Parse the start timestamp encoded in a rollout filename.

    ``rollout-2026-05-15T01-11-31-<uuid>.jsonl`` -> epoch seconds. The time
    component uses '-' as the separator (filesystem-safe), so we rebuild a
    parseable ISO string before handing it to :func:`_parse_ts`. Returns 0.0
    if the filename does not match the expected shape.
    """
    m = re.match(r"rollout-(\d{4}-\d{2}-\d{2})T(\d{2})-(\d{2})-(\d{2})-", basename)
    if not m:
        return 0.0
    date, hh, mm, ss = m.groups()
    return _parse_ts(f"{date}T{hh}:{mm}:{ss}+00:00")


def _uuid_from_filename(basename: str) -> str:
    """Extract the session UUID from a rollout filename, or "" if absent."""
    m = _UUID_RE.search(basename)
    return m.group(1) if m else ""


def _iter_lines(path: str):
    """Yield parsed ``RolloutLine`` dicts from a rollout JSONL file.

    Defensive by design: skips blank lines, lines that do not parse as JSON,
    and any line that is not a dict. Never raises on a single bad line.
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
                if isinstance(obj, dict):
                    yield obj
    except OSError as exc:
        logger.warning("CodexAdapter: cannot read %s: %s", path, exc)
        return


def _text_from_content(content: Any) -> str:
    """Flatten a ResponseItem message ``content`` array into plain text.

    Each item is ``{type: input_text|output_text|..., text: "..."}``. We join
    the ``text`` of every item with newlines. Falls back to a JSON dump for any
    unexpected shape so content is never silently lost.
    """
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, dict) and isinstance(item.get("text"), str):
                parts.append(item["text"])
            elif isinstance(item, str):
                parts.append(item)
        if parts:
            return "\n".join(parts)
        # No recognised text parts but a non-empty list -> keep the structure.
        return json.dumps(content) if content else ""
    if content is None:
        return ""
    return json.dumps(content)


def _text_from_reasoning(payload: dict[str, Any]) -> str:
    """Flatten a Reasoning payload's summary + content into thinking text."""
    parts: list[str] = []
    for key in ("summary", "content"):
        seq = payload.get(key)
        if isinstance(seq, list):
            for item in seq:
                if isinstance(item, dict) and isinstance(item.get("text"), str):
                    parts.append(item["text"])
    return "\n".join(parts)


def _output_text(output: Any) -> str:
    """Flatten a function_call_output ``output`` (FunctionCallOutputPayload).

    The wire encoding is either a plain ``{content: "..."}`` string variant or
    an ``{content_items: [...]}`` structured-content variant. Older/raw shapes
    may put the string directly. We coerce all of these to display text.
    """
    if isinstance(output, str):
        return output
    if isinstance(output, dict):
        c = output.get("content")
        if isinstance(c, str):
            return c
        items = output.get("content_items")
        if isinstance(items, list):
            return _text_from_content(items)
        if c is not None:
            return _text_from_content(c)
        return json.dumps(output)
    if output is None:
        return ""
    return json.dumps(output)


def _usage_from_token_count(payload: dict[str, Any]) -> dict[str, int]:
    """Pull a TokenUsage breakdown out of a ``token_count`` event payload.

    The running cumulative lives at ``info.total_token_usage``. Returns a flat
    dict of int fields (missing fields default to 0). Empty dict if absent.
    """
    info = payload.get("info")
    if not isinstance(info, dict):
        return {}
    usage = info.get("total_token_usage")
    if not isinstance(usage, dict):
        return {}

    def _i(key: str) -> int:
        v = usage.get(key)
        return int(v) if isinstance(v, (int, float)) else 0

    return {
        "input_tokens": _i("input_tokens"),
        "cached_input_tokens": _i("cached_input_tokens"),
        "output_tokens": _i("output_tokens"),
        "reasoning_output_tokens": _i("reasoning_output_tokens"),
        "total_tokens": _i("total_tokens"),
    }


def _first_user_text(content: Any) -> str:
    """Return a short title from a user message's content, skipping the noisy
    ``<environment_context>`` / ``<permissions instructions>`` boilerplate Codex
    injects as the first developer/user turns."""
    text = _text_from_content(content).strip()
    if not text:
        return ""
    if text.startswith("<"):
        # Boilerplate context block, not the human's prompt.
        return ""
    return text


def _session_from_file(path: str) -> Session | None:
    """Build a unified :class:`Session` from one rollout file.

    Returns ``None`` only if the file cannot be read at all. Per-line parse
    errors are skipped, never fatal.
    """
    basename = os.path.basename(path)
    session_id = _uuid_from_filename(basename)

    model = ""
    provider = ""
    cli_version = ""
    title = ""
    msg_count = 0
    first_ts = 0.0
    last_ts = 0.0
    usage: dict[str, int] = {}

    for obj in _iter_lines(path):
        kind = obj.get("type")
        payload = obj.get("payload")
        if not isinstance(payload, dict):
            payload = {}
        ts = _parse_ts(obj.get("timestamp"))
        if ts:
            if not first_ts:
                first_ts = ts
            last_ts = ts

        if kind == "session_meta":
            # The session UUID + provider authoritatively live here.
            if not session_id and isinstance(payload.get("id"), str):
                session_id = payload["id"]
            if isinstance(payload.get("model_provider"), str):
                provider = payload["model_provider"]
            if isinstance(payload.get("cli_version"), str):
                cli_version = payload["cli_version"]
        elif kind == "turn_context":
            # The model can change per turn; keep the latest.
            if isinstance(payload.get("model"), str) and payload["model"]:
                model = payload["model"]
        elif kind == "response_item":
            if payload.get("type") == "message":
                msg_count += 1
                if not title:
                    role = payload.get("role")
                    if role == "user":
                        title = _first_user_text(payload.get("content"))
        elif kind == "event_msg":
            ev = payload.get("type")
            if ev == "token_count":
                u = _usage_from_token_count(payload)
                if u:
                    # Running cumulative; the last one seen is the session total.
                    usage = u
            elif ev == "user_message" and not title:
                m = payload.get("message")
                if isinstance(m, str) and m.strip() and not m.lstrip().startswith("<"):
                    title = m.strip()

    # Prefer the first line's UTC timestamp for started_at. The filename time
    # is filesystem-safe LOCAL time (e.g. Europe/Berlin), so treating it as UTC
    # can run AHEAD of the UTC line timestamps; only fall back to it when the
    # file has no parseable line timestamps at all.
    started_at = first_ts or _ts_from_filename(basename)
    ended_at: float | None = last_ts or None
    if ended_at is None:
        try:
            ended_at = os.path.getmtime(path)
        except OSError:
            ended_at = None
    if not started_at and ended_at:
        started_at = ended_at

    total_tokens = usage.get("total_tokens", 0)

    return Session(
        agent=_AGENT,
        id=session_id or basename,
        title=title,
        display_name=title or (session_id[:24] if session_id else basename),
        model=model,
        source=provider,
        started_at=started_at,
        ended_at=ended_at,
        message_count=msg_count,
        total_tokens=total_tokens,
        input_tokens=usage.get("input_tokens", 0),
        output_tokens=usage.get("output_tokens", 0),
        cache_read_tokens=usage.get("cached_input_tokens", 0),
        reasoning_tokens=usage.get("reasoning_output_tokens", 0),
        # Codex writes token usage but NOT a per-session USD cost, so we leave
        # cost unknown rather than fabricate it.
        cost_usd=None,
        cost_status="tokens_only" if usage else "unavailable",
        extra={
            "cliVersion": cli_version,
            "rolloutFile": basename,
            "tokensOnDisk": bool(usage),
        },
    )


# -- adapter -----------------------------------------------------------------


class CodexAdapter(AgentAdapter):
    """Adapter for OpenAI Codex CLI rollout transcripts under ~/.codex."""

    name = "codex"
    display_name = "Codex"

    def __init__(self, sessions_root: str | None = None) -> None:
        # Overridable for testing; defaults to CODEX_HOME/sessions.
        self._sessions_root = sessions_root or _default_sessions_root()

    @property
    def sessions_root(self) -> str:
        return self._sessions_root

    # -- internal ------------------------------------------------------------

    def _rollout_files(self, cap: int | None = None) -> list[str]:
        """Return rollout *.jsonl paths under the date-partitioned root.

        Bounded recursive glob. ``cap`` short-circuits the walk once enough
        files are gathered so ``detect()`` stays cheap on huge histories.
        """
        root = self._sessions_root
        if not os.path.isdir(root):
            return []
        files: list[str] = []
        try:
            for dirpath, _dirs, names in os.walk(root):
                for n in names:
                    if n.startswith("rollout-") and n.endswith(".jsonl"):
                        files.append(os.path.join(dirpath, n))
                        if cap is not None and len(files) >= cap:
                            return files
        except OSError as exc:
            logger.warning("CodexAdapter: walk failed under %s: %s", root, exc)
        return files

    # -- AgentAdapter contract -----------------------------------------------

    def detect(self) -> DetectResult:
        """Cheap detection. Never raises.

        ``detected`` is True when the sessions root exists, or when the Codex
        home exists (installed but no sessions yet). ``running`` is always
        False — Codex has no live gateway we tap.
        """
        home = _codex_home()
        root = self._sessions_root
        try:
            has_root = os.path.isdir(root)
            has_home = os.path.isdir(home)
            detected = has_root or has_home
            # Cap the walk so detect() stays O(1)-ish even with deep histories.
            session_count = len(self._rollout_files(cap=5000)) if has_root else 0
            return DetectResult(
                name=self.name,
                display_name=self.display_name,
                detected=detected,
                running=False,
                workspace=home,
                session_count=session_count,
                capabilities=[c.value for c in self.capabilities()],
                meta={"sessionsRoot": root},
            )
        except Exception as exc:  # belt-and-suspenders: detect() must never raise
            logger.debug("CodexAdapter detect() failed: %s", exc)
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
        files = self._rollout_files()
        if not files:
            return []

        sessions: list[Session] = []
        for path in files:
            try:
                sess = _session_from_file(path)
            except Exception as exc:
                # Never let one bad rollout sink the whole list.
                logger.warning("CodexAdapter: skipping bad session %s: %s", path, exc)
                continue
            if sess is not None:
                sessions.append(sess)

        # Sort by logical activity time, newest first. We use the parsed
        # timestamp (filename start / last line / mtime fallback), NOT raw file
        # mtime, so ordering is deterministic across a git checkout or copy.
        sessions.sort(key=lambda s: s.ended_at or s.started_at or 0.0, reverse=True)
        return sessions[:limit]

    def _find_rollout(self, session_id: str) -> str | None:
        """Locate the rollout file whose UUID matches ``session_id``."""
        for path in self._rollout_files():
            base = os.path.basename(path)
            if _uuid_from_filename(base) == session_id or base == session_id:
                return path
        return None

    def list_events(self, session_id: str, limit: int = 500) -> list[Event]:
        """Parse one rollout into unified events, chronological order.

        ``session_id`` is the NATIVE id (the rollout UUID) — the ingest layer
        namespaces it later. Maps Codex line types to unified event types:
        ``message`` -> message, ``reasoning`` -> thinking,
        ``function_call`` -> tool_call, ``function_call_output`` -> tool_result.
        ``event_msg`` user/agent messages and lifecycle markers are skipped to
        avoid duplicating the canonical ``response_item`` messages.
        """
        path = self._find_rollout(session_id)
        if not path or not os.path.isfile(path):
            return []

        events: list[Event] = []
        seq = 0
        for obj in _iter_lines(path):
            if len(events) >= limit:
                break
            kind = obj.get("type")
            payload = obj.get("payload")
            if not isinstance(payload, dict):
                continue
            ts = _parse_ts(obj.get("timestamp"))

            if kind != "response_item":
                # session_meta / turn_context / event_msg are metadata or
                # duplicates of response_item messages; not timeline events.
                continue

            ptype = payload.get("type")

            if ptype == "message":
                seq += 1
                events.append(Event(
                    agent=_AGENT,
                    session_id=session_id,
                    id=f"{session_id}:{seq}",
                    type="message",
                    ts=ts,
                    role=payload.get("role") or "",
                    content=_text_from_content(payload.get("content")),
                ))
            elif ptype == "reasoning":
                seq += 1
                events.append(Event(
                    agent=_AGENT,
                    session_id=session_id,
                    id=f"{session_id}:{seq}",
                    type="thinking",
                    ts=ts,
                    role="assistant",
                    content=_text_from_reasoning(payload),
                ))
            elif ptype in ("function_call", "local_shell_call", "custom_tool_call"):
                name = payload.get("name") or payload.get("type") or "unknown"
                arguments = payload.get("arguments")
                if arguments is None and isinstance(payload.get("action"), dict):
                    # local_shell_call carries an `action` object instead.
                    arguments = json.dumps(payload["action"])
                call_id = payload.get("call_id") or ""
                seq += 1
                events.append(Event(
                    agent=_AGENT,
                    session_id=session_id,
                    id=f"{session_id}:{seq}",
                    type="tool_call",
                    ts=ts,
                    role="assistant",
                    tool_name=name,
                    tool_calls=[{
                        "id": call_id,
                        "name": name,
                        "arguments": arguments,
                    }],
                    extra={"callId": call_id} if call_id else {},
                ))
            elif ptype in ("function_call_output", "custom_tool_call_output"):
                call_id = payload.get("call_id") or ""
                seq += 1
                events.append(Event(
                    agent=_AGENT,
                    session_id=session_id,
                    id=f"{session_id}:{seq}",
                    type="tool_result",
                    ts=ts,
                    role="tool",
                    content=_output_text(payload.get("output")),
                    extra={"callId": call_id} if call_id else {},
                ))
            # Unknown response_item subtypes are skipped, not fatal.
        return events

    def capabilities(self) -> set[Capability]:
        # SESSIONS + EVENTS always; COST because Codex writes a real token
        # breakdown (token_count event_msg) to disk. We do NOT claim a USD cost
        # capability beyond the token counts — Codex does not persist USD.
        return {Capability.SESSIONS, Capability.EVENTS, Capability.COST}
