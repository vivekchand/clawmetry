"""PicoClawAdapter — read PicoClaw session data from its workspace JSONL.

PicoClaw (https://github.com/sipeed/picoclaw) is a Go agent that does NOT
share OpenClaw's session layout, so this subclasses :class:`AgentAdapter`
directly rather than reusing :class:`OpenClawAdapter`. The native format is
its own flat ``providers.Message`` JSONL, closer in spirit to the Claude
Code adapter (a non-OpenClaw filesystem reader) than to OpenClaw's v3
envelope format.

On-disk layout
--------------
``$PICOCLAW_HOME/workspace/sessions/<key>.jsonl`` (default
``~/.picoclaw/workspace/sessions/``, respects the ``PICOCLAW_HOME`` env
var). Each session also has a ``<key>.meta.json`` sidecar holding a
``SessionMeta`` ``{key, summary, skip, count, created_at, updated_at,
scope, aliases}``.

Each ``.jsonl`` line is a FLAT ``providers.Message`` (NOT an OpenClaw v3
``{"type":"message","message":{...}}`` envelope)::

    {
      "role": "assistant",
      "content": "...",              # content is a STRING, not a block array
      "model_name": "llama3",        # bare config alias, OR "ollama/llama3.1:8b"
      "created_at": "2026-05-25T10:11:39.37008+02:00",   # RFC3339, Go-trimmed fraction
      "tool_calls": [{"id": ..., "type": "function",
                      "function": {"name": ..., "arguments": "..."}}],  # OpenAI-nested
      "tool_call_id": "...",          # omitempty, on tool-result lines
      "reasoning_content": "...",     # omitempty
      "media": [], "attachments": []
    }

The ``model_name`` may be a bare config alias (e.g. ``llama3``) or a
``provider/model`` string (e.g. ``ollama/llama3.1:8b``) depending on the
user's PicoClaw config; both are handled (provider prefix kept in extra).

IMPORTANT — tokens and cost are NOT on disk. The ``providers.Message``
struct carries no usage / token / cost field, so PicoClaw JSONL gives us
zero token data. We surface ``total_tokens=0`` and ``cost_usd=None`` and
deliberately do NOT advertise the COST capability. This is honest: the
data simply is not there to read.

The adapter is read-only and never modifies the PicoClaw data directory.
"""
from __future__ import annotations

import glob
import json
import logging
import os
import re
from datetime import datetime, timezone
from typing import Any

# Normalises the fractional-seconds part of an ISO-8601 timestamp. PicoClaw is
# written in Go, whose time.Time JSON marshaling TRIMS trailing zeros, so it
# emits e.g. "2026-05-25T10:11:39.37008+02:00" (5 fractional digits).
# datetime.fromisoformat() on Python 3.9/3.10 only accepts exactly 0, 3, or 6
# fractional digits, so an odd count raises ValueError and the timestamp would
# silently parse as 0.0. We pad/truncate the fractional run to 6 digits.
# (Caught against a real captured PicoClaw session; ClawMetry CI runs Py3.9.)
_FRAC_RE = re.compile(r"\.(\d+)")

from .base import AgentAdapter, Capability, DetectResult, Event, Session

logger = logging.getLogger("clawmetry.adapters.picoclaw")

_AGENT = "picoclaw"


# -- helpers -----------------------------------------------------------------


def _picoclaw_home() -> str:
    return os.environ.get("PICOCLAW_HOME") or os.path.expanduser("~/.picoclaw")


def _default_sessions_dir() -> str:
    return os.path.join(_picoclaw_home(), "workspace", "sessions")


def _parse_ts(ts: Any) -> float:
    """Parse an RFC3339 / ISO-8601 string or numeric epoch to float seconds.

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
        # Pad/truncate fractional seconds to 6 digits so Go's trailing-zero
        # trimming (e.g. ".37008") still parses on Python 3.9/3.10.
        s = _FRAC_RE.sub(lambda m: "." + (m.group(1) + "000000")[:6], s, count=1)
        dt = datetime.fromisoformat(s)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.timestamp()
    except (ValueError, AttributeError):
        return 0.0


def _strip_provider(model_name: str) -> str:
    """Return the display model name, dropping any ``provider/`` prefix.

    ``ollama/llama3.2:3b`` -> ``llama3.2:3b``; a hosted bare ``gpt-5.4``
    is returned unchanged.
    """
    if not model_name:
        return ""
    return model_name.split("/", 1)[1] if "/" in model_name else model_name


def _provider_of(model_name: str) -> str:
    """Return the provider prefix of a model name, or "" if none.

    ``ollama/llama3.2:3b`` -> ``ollama``; bare ``gpt-5.4`` -> ``""``.
    """
    if model_name and "/" in model_name:
        return model_name.split("/", 1)[0]
    return ""


def _iter_messages(path: str):
    """Yield parsed flat ``providers.Message`` dicts from a JSONL file.

    Defensive by design: skips blank lines, lines that do not parse as
    JSON, and any line that is not a dict with a ``role`` (e.g. a
    ``session``-style header some versions write as the first line).
    Never raises on a single bad line.
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
                if not obj.get("role"):
                    # Header line or malformed record — skip.
                    continue
                yield obj
    except OSError as exc:
        logger.warning("PicoClawAdapter: cannot read %s: %s", path, exc)
        return


def _read_meta(jsonl_path: str) -> dict[str, Any]:
    """Read the ``<key>.meta.json`` sidecar for a session JSONL, if present.

    Returns an empty dict when the sidecar is absent or unreadable —
    never raises.
    """
    meta_path = jsonl_path[:-6] + ".meta.json" if jsonl_path.endswith(".jsonl") else jsonl_path + ".meta.json"
    if not os.path.isfile(meta_path):
        return {}
    try:
        with open(meta_path, "r", errors="replace") as fh:
            data = json.load(fh)
        return data if isinstance(data, dict) else {}
    except (OSError, json.JSONDecodeError) as exc:
        logger.debug("PicoClawAdapter: bad meta sidecar %s: %s", meta_path, exc)
        return {}


def _session_from_files(jsonl_path: str, key: str) -> Session | None:
    """Build a unified :class:`Session` from a session JSONL + meta sidecar.

    Returns ``None`` only if the file cannot be stat'd at all. A parse
    error on individual lines is skipped, never fatal.
    """
    meta = _read_meta(jsonl_path)

    model_full = ""
    msg_count = 0
    first_ts = 0.0
    last_ts = 0.0
    for obj in _iter_messages(jsonl_path):
        msg_count += 1
        mn = obj.get("model_name")
        if mn:
            # Last non-empty model_name wins (latest model used).
            model_full = mn
        ts = _parse_ts(obj.get("created_at"))
        if ts:
            if not first_ts:
                first_ts = ts
            last_ts = ts

    # Prefer meta count when present; fall back to the parsed message count.
    meta_count = meta.get("count")
    message_count = int(meta_count) if isinstance(meta_count, (int, float)) else msg_count

    started_at = _parse_ts(meta.get("created_at")) or first_ts
    ended_at: float | None = _parse_ts(meta.get("updated_at")) or last_ts or None
    if ended_at is None:
        # Fall back to file mtime so the UI can still order the session.
        try:
            ended_at = os.path.getmtime(jsonl_path)
        except OSError:
            ended_at = None
        if not started_at and ended_at:
            started_at = ended_at

    summary = meta.get("summary") or ""

    return Session(
        agent=_AGENT,
        id=key,
        title=summary,
        display_name=summary or key,
        model=_strip_provider(model_full),
        source=_provider_of(model_full),
        started_at=started_at,
        ended_at=ended_at,
        message_count=message_count,
        # Tokens + cost are NOT present in PicoClaw's on-disk Message
        # struct, so we honestly report zero / unknown rather than guess.
        total_tokens=0,
        cost_usd=None,
        cost_status="unavailable",
        extra={
            # Keep the full provider-qualified model name for callers that
            # need to route / price it; `model` above is the display name.
            "modelFull": model_full,
            "scope": meta.get("scope") or "",
            "skip": bool(meta.get("skip", False)),
            "aliases": meta.get("aliases") or [],
            "tokensUnavailable": True,
        },
    )


# -- adapter -----------------------------------------------------------------


class PicoClawAdapter(AgentAdapter):
    """Adapter for PicoClaw sessions stored under its workspace directory."""

    name = "picoclaw"
    display_name = "PicoClaw"

    def __init__(self, sessions_dir: str | None = None) -> None:
        # Overridable for testing; defaults to PICOCLAW_HOME/workspace/sessions.
        self._sessions_dir = sessions_dir or _default_sessions_dir()

    @property
    def sessions_dir(self) -> str:
        return self._sessions_dir

    # -- AgentAdapter contract -----------------------------------------------

    def detect(self) -> DetectResult:
        """Cheap detection. Never raises.

        ``detected`` is True when the sessions dir exists, or when the
        PicoClaw home exists (installed but no sessions yet). ``running``
        is always False — there is no gateway wired for PicoClaw.
        """
        home = _picoclaw_home()
        sessions_dir = self._sessions_dir
        try:
            has_sessions_dir = os.path.isdir(sessions_dir)
            has_home = os.path.isdir(home)
            detected = has_sessions_dir or has_home
            session_count = 0
            if has_sessions_dir:
                try:
                    session_count = len(glob.glob(os.path.join(sessions_dir, "*.jsonl")))
                except OSError:
                    session_count = 0
            return DetectResult(
                name=self.name,
                display_name=self.display_name,
                detected=detected,
                running=False,
                workspace=home,
                session_count=session_count,
                capabilities=[c.value for c in self.capabilities()],
                meta={"sessionsDir": sessions_dir},
            )
        except Exception as exc:  # belt-and-suspenders: detect() must never raise
            logger.debug("PicoClawAdapter detect() failed: %s", exc)
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
        sessions_dir = self._sessions_dir
        if not os.path.isdir(sessions_dir):
            return []
        try:
            files = glob.glob(os.path.join(sessions_dir, "*.jsonl"))
        except OSError as exc:
            logger.warning("PicoClawAdapter list_sessions glob failed: %s", exc)
            return []

        sessions: list[Session] = []
        for path in files:
            key = os.path.basename(path)[:-6]  # strip ".jsonl"
            try:
                sess = _session_from_files(path, key)
            except Exception as exc:
                # Never let one bad session sink the whole list.
                logger.warning("PicoClawAdapter: skipping bad session %s: %s", path, exc)
                continue
            if sess is not None:
                sessions.append(sess)

        # Sort by the session's logical activity time, newest first. We sort
        # on the parsed timestamp (meta updated_at / last message / mtime
        # fallback), NOT raw file mtime — mtime is non-deterministic across a
        # git checkout or file copy and would make ordering flaky in CI.
        sessions.sort(key=lambda s: s.ended_at or s.started_at or 0.0, reverse=True)
        return sessions[:limit]

    def list_events(self, session_id: str, limit: int = 500) -> list[Event]:
        """Parse one session's JSONL into unified events, chronological order."""
        path = os.path.join(self._sessions_dir, f"{session_id}.jsonl")
        if not os.path.isfile(path):
            return []

        events: list[Event] = []
        seq = 0
        for obj in _iter_messages(path):
            if len(events) >= limit:
                break
            role = obj.get("role") or ""
            content = obj.get("content") or ""
            if not isinstance(content, str):
                # PicoClaw content is a string; coerce defensively.
                content = json.dumps(content)
            ts = _parse_ts(obj.get("created_at"))
            model_full = obj.get("model_name") or ""

            # A reasoning_content payload becomes its own thinking event,
            # emitted before the message it belongs to.
            reasoning = obj.get("reasoning_content")
            if reasoning:
                seq += 1
                events.append(Event(
                    agent=_AGENT,
                    session_id=session_id,
                    id=f"{session_id}:{seq}",
                    type="thinking",
                    ts=ts,
                    role=role,
                    content=str(reasoning),
                    extra={"modelFull": model_full} if model_full else {},
                ))

            tool_call_id = obj.get("tool_call_id")
            if tool_call_id:
                # This Message is a tool result feeding back into the model.
                seq += 1
                events.append(Event(
                    agent=_AGENT,
                    session_id=session_id,
                    id=f"{session_id}:{seq}",
                    type="tool_result",
                    ts=ts,
                    role=role or "tool",
                    content=content,
                    extra={"toolCallId": tool_call_id},
                ))
            else:
                # A regular user / assistant / system message.
                seq += 1
                events.append(Event(
                    agent=_AGENT,
                    session_id=session_id,
                    id=f"{session_id}:{seq}",
                    type="message",
                    ts=ts,
                    role=role,
                    content=content,
                    extra={"modelFull": model_full} if model_full else {},
                ))

            # Each ToolCall on an assistant message becomes its own event.
            tool_calls = obj.get("tool_calls")
            if isinstance(tool_calls, list):
                for tc in tool_calls:
                    if not isinstance(tc, dict):
                        continue
                    if len(events) >= limit:
                        break
                    # Real PicoClaw tool calls are OpenAI-nested:
                    # {"id", "type":"function", "function":{"name","arguments"}}.
                    # Read the nested function object first, falling back to a
                    # flat shape for forward/backward compatibility. (The flat
                    # read dropped tool name + args on real captured data.)
                    fn = tc.get("function") if isinstance(tc.get("function"), dict) else {}
                    name = fn.get("name") or tc.get("name") or "unknown"
                    arguments = (
                        fn.get("arguments")
                        if fn.get("arguments") is not None
                        else tc.get("arguments")
                    )
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
                            "id": tc.get("id") or "",
                            "name": name,
                            "arguments": arguments,
                        }],
                    ))
        return events

    def capabilities(self) -> set[Capability]:
        # SESSIONS + EVENTS only. We deliberately omit COST: PicoClaw's
        # on-disk Message struct carries no token / cost data, so claiming
        # COST would surface fabricated zeros in the UI.
        return {Capability.SESSIONS, Capability.EVENTS}
