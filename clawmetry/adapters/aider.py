"""AiderAdapter — read Aider session data from its on-disk chat history.

Aider (https://github.com/Aider-AI/aider, ``pip install aider-chat``) is an
AI pair-programming CLI. It does NOT share OpenClaw's session layout, so this
subclasses :class:`AgentAdapter` directly rather than reusing
:class:`OpenClawAdapter`. The native format is a human-readable MARKDOWN
transcript, not JSONL.

On-disk layout (PER-PROJECT, not central)
-----------------------------------------
Aider writes its history files into the WORKING DIRECTORY of each project
(the git repo root it was launched in), NOT a single central home dir:

    <project>/.aider.chat.history.md   markdown transcript (this is what we read)
    <project>/.aider.input.history     raw user-input log (one block per prompt)
    <project>/.aider.llm.history       raw LLM API calls (only if --llm-history set)

There is NO ``~/.aider`` sessions directory and NO env var pointing at a
central store, so a generic "scan one home dir" discovery does not work.
We instead scan a small, BOUNDED set of likely locations (the current
working dir, plus an optional ``AIDER_HISTORY_DIRS`` colon-separated env
override, plus the constructor ``roots`` arg for tests). We deliberately do
NOT walk all of ``$HOME`` — that would be slow and is the wrong tradeoff for
a per-page-load detect(). This per-project discovery limitation is the same
class of constraint NanoClaw has (CWD-relative data dir, no home env var):
ClawMetry can only surface Aider projects whose dir it is pointed at.

Real ``.aider.chat.history.md`` format (captured from a real Ollama run)
------------------------------------------------------------------------
Each session is delimited by a top-level header line::

    # aider chat started at 2026-05-25 21:51:40

(local time, ``YYYY-MM-DD HH:MM:SS``, no timezone). Within a session block:

  * ``> ...``   metadata / tool-output lines written by aider itself. These
    include the model line (``> Model: ollama_chat/llama3.2 with whole edit
    format``), the version, the token line (``> Tokens: 796 sent, 34
    received.``), interactive prompt echoes, and ``> Applied edit to X``.
  * ``#### <text>``   a USER prompt.
  * any other non-blank line   ASSISTANT prose (including fenced ``` code
    blocks the model emitted). We fold the assistant's prose + code for one
    reply into a single assistant ``message`` event.

TOKENS / COST: aider's ``.md`` logs a per-reply ``> Tokens: N sent, M
received.`` line. We parse it when present and surface input/output/total
tokens honestly. Aider does NOT write a dollar cost into the ``.md`` for
local (Ollama) models, and the sent/received split is per-reply not a full
session usage object, so we report ``cost_usd=None`` (unknown) and only
advertise COST when at least one Tokens line was actually parsed.

The adapter is read-only and never modifies any Aider history file.
"""
from __future__ import annotations

import glob
import hashlib
import logging
import os
import re
from datetime import datetime, timezone
from typing import Any

from .base import AgentAdapter, Capability, DetectResult, Event, Session

logger = logging.getLogger("clawmetry.adapters.aider")

_AGENT = "aider"

_HISTORY_FILENAME = ".aider.chat.history.md"

# "# aider chat started at 2026-05-25 21:51:40"
_SESSION_HEADER_RE = re.compile(
    r"^#\s+aider chat started at\s+(.+?)\s*$"
)
# "> Model: ollama_chat/llama3.2 with whole edit format"
_MODEL_RE = re.compile(r"^>\s*Model:\s*(\S+)")
# "> Tokens: 796 sent, 34 received." (commas/k-suffixes tolerated)
_TOKENS_RE = re.compile(
    r"^>\s*Tokens:\s*([0-9][0-9,\.kKmM]*)\s*sent,\s*([0-9][0-9,\.kKmM]*)\s*received",
)
# "#### user prompt text"
_USER_PROMPT_RE = re.compile(r"^####\s?(.*)$")
# Header timestamp format aider writes (local, no tz).
_TS_FORMAT = "%Y-%m-%d %H:%M:%S"


# -- helpers -----------------------------------------------------------------


def _parse_header_ts(raw: str) -> float:
    """Parse aider's ``# aider chat started at <ts>`` timestamp to epoch secs.

    Aider writes local time without a timezone (``2026-05-25 21:51:40``).
    We interpret it as local time and return epoch seconds. Returns 0.0 on
    anything unparseable so callers never crash on a malformed header.
    """
    if not raw:
        return 0.0
    s = str(raw).strip()
    try:
        dt = datetime.strptime(s, _TS_FORMAT)
        # Naive timestamp -> treat as local time (aider writes local time).
        return dt.timestamp()
    except (ValueError, TypeError):
        pass
    # Fallback: tolerate an ISO-8601 variant if a future aider changes format.
    try:
        if s.endswith("Z"):
            s = s[:-1] + "+00:00"
        dt = datetime.fromisoformat(s)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.timestamp()
    except (ValueError, TypeError):
        return 0.0


def _parse_token_count(raw: str) -> int:
    """Parse a token count token like ``796``, ``1,024``, or ``2.5k``.

    Aider usually writes plain integers, but tolerate thousands separators
    and ``k``/``m`` suffixes defensively. Returns 0 on anything unparseable.
    """
    if not raw:
        return 0
    s = raw.strip().replace(",", "")
    mult = 1
    if s[-1:] in ("k", "K"):
        mult, s = 1000, s[:-1]
    elif s[-1:] in ("m", "M"):
        mult, s = 1_000_000, s[:-1]
    try:
        return int(round(float(s) * mult))
    except ValueError:
        return 0


def _expand_roots(roots: list[str] | None) -> list[str]:
    """Build the bounded, ordered list of dirs to scan for history files.

    Order: explicit constructor ``roots`` (tests / non-default installs) ->
    ``AIDER_HISTORY_DIRS`` colon-separated env override -> the current
    working dir. De-duplicated, expanded, never raises. We do NOT walk
    ``$HOME`` (per-project discovery limitation, documented at module top).
    """
    out: list[str] = []

    def _add(path: str) -> None:
        if not path:
            return
        try:
            expanded = os.path.abspath(os.path.expanduser(path))
        except Exception:
            return
        if expanded not in out:
            out.append(expanded)

    if roots:
        for r in roots:
            _add(r)
    env = os.environ.get("AIDER_HISTORY_DIRS")
    if env:
        for part in env.split(os.pathsep):
            _add(part)
    try:
        _add(os.getcwd())
    except OSError:
        pass
    return out


def _find_history_files(roots: list[str]) -> list[str]:
    """Return existing ``.aider.chat.history.md`` paths under the given roots.

    A root may be either a directory that contains the history file, or the
    history file's path directly. Cheap (one stat / glob per root), bounded,
    never raises.
    """
    found: list[str] = []
    for root in roots:
        try:
            if os.path.isfile(root) and os.path.basename(root) == _HISTORY_FILENAME:
                cand = root
            else:
                cand = os.path.join(root, _HISTORY_FILENAME)
            if os.path.isfile(cand):
                real = os.path.abspath(cand)
                if real not in found:
                    found.append(real)
        except OSError as exc:
            logger.debug("AiderAdapter: cannot stat under %s: %s", root, exc)
            continue
    return found


def _session_id(path: str, index: int, started_ts: float) -> str:
    """Stable id for one session block: hash(path) + block index + start ts.

    Path is hashed so the id is stable but does not leak the full filesystem
    path; the block index + start ts disambiguate multiple sessions in one
    file. Stable across re-reads of the same file (no mtime / randomness).
    """
    h = hashlib.sha1(path.encode("utf-8", "replace")).hexdigest()[:12]
    return f"{h}-{index}-{int(started_ts)}"


class _Block:
    """A parsed session block from a ``.aider.chat.history.md`` file."""

    __slots__ = (
        "started_at",
        "model",
        "input_tokens",
        "output_tokens",
        "events_raw",
        "first_user",
    )

    def __init__(self, started_at: float) -> None:
        self.started_at = started_at
        self.model = ""
        self.input_tokens = 0
        self.output_tokens = 0
        # list of (kind, text) where kind in {"user", "assistant", "meta"}
        self.events_raw: list[tuple[str, str]] = []
        self.first_user = ""


def _parse_history_file(path: str) -> list[_Block]:
    """Parse a ``.aider.chat.history.md`` file into a list of session blocks.

    Defensive: a file with no session header still yields one implicit block
    so its turns are not lost; an unreadable file yields an empty list and
    logs a warning. Never raises.
    """
    blocks: list[_Block] = []
    cur: _Block | None = None
    # Accumulator for the current assistant prose run.
    assistant_buf: list[str] = []

    def _flush_assistant() -> None:
        if cur is None:
            return
        text = "\n".join(assistant_buf).strip("\n")
        if text.strip():
            cur.events_raw.append(("assistant", text))
        assistant_buf.clear()

    try:
        with open(path, "r", errors="replace") as fh:
            for raw_line in fh:
                line = raw_line.rstrip("\n")

                header = _SESSION_HEADER_RE.match(line)
                if header:
                    _flush_assistant()
                    cur = _Block(_parse_header_ts(header.group(1)))
                    blocks.append(cur)
                    continue

                if cur is None:
                    # Content before any header -> implicit first block.
                    cur = _Block(0.0)
                    blocks.append(cur)

                user_m = _USER_PROMPT_RE.match(line)
                if user_m:
                    _flush_assistant()
                    text = user_m.group(1).strip()
                    cur.events_raw.append(("user", text))
                    if not cur.first_user and text:
                        cur.first_user = text
                    continue

                if line.startswith(">"):
                    # Metadata line: harvest model + tokens, then drop it.
                    model_m = _MODEL_RE.match(line)
                    if model_m and not cur.model:
                        cur.model = model_m.group(1).strip()
                    tok_m = _TOKENS_RE.match(line)
                    if tok_m:
                        cur.input_tokens += _parse_token_count(tok_m.group(1))
                        cur.output_tokens += _parse_token_count(tok_m.group(2))
                    # We do not surface aider's own ``>`` chrome as events.
                    continue

                # Anything else is assistant prose (incl. fenced code blocks).
                assistant_buf.append(line)
            _flush_assistant()
    except OSError as exc:
        logger.warning("AiderAdapter: cannot read %s: %s", path, exc)
        return []
    return blocks


def _title_from(first_user: str, fallback: str) -> str:
    """Build a one-line session title from the first user prompt."""
    title = (first_user or "").strip().replace("\n", " ")
    if not title:
        return fallback
    if len(title) > 80:
        title = title[:77] + "..."
    return title


# -- adapter -----------------------------------------------------------------


class AiderAdapter(AgentAdapter):
    """Adapter for Aider chat-history markdown transcripts.

    Aider history is PER-PROJECT: each git repo Aider runs in gets its own
    ``.aider.chat.history.md`` in the repo root, and there is no central
    home dir or env var pointing at a session store. Discovery therefore
    scans a bounded set of roots (constructor ``roots`` arg, the
    ``AIDER_HISTORY_DIRS`` colon-separated env override, and the current
    working dir) rather than walking ``$HOME``. ClawMetry can only surface
    Aider projects whose directory it is explicitly pointed at.
    """

    name = "aider"
    display_name = "Aider"

    def __init__(self, roots: list[str] | None = None) -> None:
        # Overridable for testing; otherwise CWD + AIDER_HISTORY_DIRS env.
        self._roots = _expand_roots(roots)

    @property
    def roots(self) -> list[str]:
        return list(self._roots)

    # -- internal ------------------------------------------------------------

    def _collect(self) -> list[tuple[str, int, _Block]]:
        """Parse every discovered history file into (path, index, block).

        Never raises — a bad file is skipped with a warning.
        """
        out: list[tuple[str, int, _Block]] = []
        for path in _find_history_files(self._roots):
            try:
                blocks = _parse_history_file(path)
            except Exception as exc:  # belt-and-suspenders
                logger.warning("AiderAdapter: skipping bad history %s: %s", path, exc)
                continue
            for i, block in enumerate(blocks):
                out.append((path, i, block))
        return out

    def _session_from_block(self, path: str, index: int, block: _Block) -> Session:
        """Build a unified :class:`Session` from one parsed history block."""
        msg_events = [e for e in block.events_raw if e[0] in ("user", "assistant")]
        message_count = len(msg_events)

        started = block.started_at
        # Aider does not write a per-session end timestamp into the .md. Use
        # the file mtime as a best-effort ended_at so the UI can order it.
        ended: float | None
        try:
            ended = os.path.getmtime(path)
        except OSError:
            ended = None
        if ended is not None and started and ended < started:
            ended = started
        if not started and ended:
            started = ended

        input_tokens = block.input_tokens
        output_tokens = block.output_tokens
        total_tokens = input_tokens + output_tokens
        tokens_present = total_tokens > 0

        title = _title_from(block.first_user, fallback=f"aider session {index + 1}")

        return Session(
            agent=_AGENT,
            id=_session_id(path, index, started),
            title=title,
            display_name=title,
            model=block.model,
            source="aider",
            started_at=started,
            ended_at=ended,
            message_count=message_count,
            total_tokens=total_tokens,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            # Aider's .md logs a sent/received token split per reply but no
            # dollar cost (esp. for local Ollama models), so cost is unknown.
            cost_usd=None,
            cost_status="" if tokens_present else "unavailable",
            extra={
                "historyFile": path,
                "blockIndex": index,
                "tokensPresent": tokens_present,
            },
        )

    # -- AgentAdapter contract -----------------------------------------------

    def detect(self) -> DetectResult:
        """Cheap detection. Never raises.

        ``detected`` is True when any ``.aider.chat.history.md`` is found in
        the configured roots. ``running`` is always False — aider is a
        one-shot CLI with no gateway/daemon for ClawMetry to poll.
        """
        try:
            files = _find_history_files(self._roots)
            session_count = 0
            if files:
                # Count session-start headers across all files (cheap scan).
                for path in files:
                    try:
                        with open(path, "r", errors="replace") as fh:
                            for line in fh:
                                if _SESSION_HEADER_RE.match(line.rstrip("\n")):
                                    session_count += 1
                    except OSError:
                        continue
            workspace = os.path.dirname(files[0]) if files else (
                self._roots[0] if self._roots else ""
            )
            return DetectResult(
                name=self.name,
                display_name=self.display_name,
                detected=bool(files),
                running=False,
                workspace=workspace,
                session_count=session_count,
                capabilities=[c.value for c in self.capabilities()],
                meta={"roots": self._roots, "historyFiles": files},
            )
        except Exception as exc:  # detect() must never raise
            logger.debug("AiderAdapter detect() failed: %s", exc)
            return DetectResult(
                name=self.name,
                display_name=self.display_name,
                detected=False,
                running=False,
                capabilities=[c.value for c in self.capabilities()],
                meta={"error": str(exc)},
            )

    def list_sessions(self, limit: int = 100) -> list[Session]:
        """Return recent sessions, newest first. Never raises on a bad file."""
        try:
            sessions: list[Session] = []
            for path, index, block in self._collect():
                # Skip empty blocks (e.g. the aborted "version available"
                # block that has no user/assistant turns at all).
                if not any(e[0] in ("user", "assistant") for e in block.events_raw):
                    continue
                try:
                    sessions.append(self._session_from_block(path, index, block))
                except Exception as exc:
                    logger.warning(
                        "AiderAdapter: skipping bad block %s#%d: %s", path, index, exc
                    )
                    continue
            # Newest first by started_at (fall back to ended_at).
            sessions.sort(
                key=lambda s: (s.started_at or (s.ended_at or 0.0)), reverse=True
            )
            return sessions[:limit]
        except Exception as exc:
            logger.warning("AiderAdapter list_sessions failed: %s", exc)
            return []

    def list_events(self, session_id: str, limit: int = 500) -> list[Event]:
        """Parse one session block into unified events, chronological order."""
        try:
            for path, index, block in self._collect():
                sid = _session_id(path, index, block.started_at)
                if sid != session_id:
                    continue
                return self._events_from_block(session_id, block, limit)
            return []
        except Exception as exc:
            logger.warning("AiderAdapter list_events failed: %s", exc)
            return []

    def _events_from_block(
        self, session_id: str, block: _Block, limit: int
    ) -> list[Event]:
        events: list[Event] = []
        seq = 0
        # Aider's .md has no per-turn timestamps; all turns share the block's
        # start time. Order is preserved by file order (already chronological).
        ts = block.started_at
        for kind, text in block.events_raw:
            if len(events) >= limit:
                break
            if kind not in ("user", "assistant"):
                continue
            seq += 1
            role = "user" if kind == "user" else "assistant"
            extra: dict[str, Any] = {}
            if kind == "assistant" and block.model:
                extra["modelFull"] = block.model
            events.append(
                Event(
                    agent=_AGENT,
                    session_id=session_id,
                    id=f"{session_id}:{seq}",
                    type="message",
                    ts=ts,
                    role=role,
                    content=text,
                    extra=extra,
                )
            )
        return events

    def capabilities(self) -> set[Capability]:
        # SESSIONS + EVENTS always. COST is added dynamically when at least
        # one ``> Tokens:`` line was parsed across the discovered history,
        # so we never advertise fabricated zeros.
        caps = {Capability.SESSIONS, Capability.EVENTS}
        try:
            for _, _, block in self._collect():
                if (block.input_tokens + block.output_tokens) > 0:
                    caps.add(Capability.COST)
                    break
        except Exception:
            pass
        return caps
