"""ChatGPT-style session titles from the first real user prompt.

Family runtimes (Claude Code, Codex, …) expose no display name, so their
session rows surfaced as raw UUIDs and the Conversations tab showed
"Untitled session" for every one (founder report 2026-07-30). The first
real user message is an excellent title ("bump clawmetry cloud to use the
latest version of clawmetry oss"), so both the ingest path
(``clawmetry/sync.py::sync_family_runtimes``) and the ``/api/transcripts``
fast path (``routes/sessions.py``) derive one here.

Derivation rule (pinned by ``tests/test_family_session_titles.py``):
take the FIRST user text that is not harness plumbing — skip texts starting
with ``<`` (``<system-reminder>``, ``<command-name>``,
``<local-command-stdout>``) and with ``Caveat:`` (the resumed-session
preamble) and empty/whitespace-only texts — collapse whitespace, truncate to
80 chars (ellipsis when truncated).

Everything here is best-effort and must never raise into an ingest loop or
a request handler (the never-crash rule): the public entry points swallow
all exceptions and return ``""``.
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path

TITLE_MAX_CHARS = 80

# Texts that can never be a human prompt: harness-injected wrappers
# (<system-reminder>, <command-name>, <local-command-stdout>, …) and the
# "Caveat: the messages below were generated…" resumed-session preamble.
_SKIP_PREFIXES = ("<", "Caveat:")

_UUID_RE = re.compile(
    r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-"
    r"[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"
)

# Derived titles are deterministic (first qualifying user text of a
# transcript never changes once written), so a small in-process cache makes
# re-deriving for an active session free — an already-titled session never
# re-reads the file head. Only NON-EMPTY results are cached: a session that
# has no qualifying prompt yet must be re-tried once it grows one.
_TITLE_CACHE: dict = {}
_TITLE_CACHE_MAX = 512


def clean_prompt_text(text) -> str:
    """Collapse whitespace; return "" when the text can't be a human title."""
    if not isinstance(text, str):
        return ""
    text = " ".join(text.split())
    if not text or text.startswith(_SKIP_PREFIXES):
        return ""
    return text


def truncate_title(text: str) -> str:
    """Cap to TITLE_MAX_CHARS total, ellipsised (matches the cloud
    ``_derive_transcript_title`` cap so list rows render consistently)."""
    if len(text) > TITLE_MAX_CHARS:
        return text[: TITLE_MAX_CHARS - 1].rstrip() + "…"
    return text


def derive_title_from_texts(texts) -> str:
    """First qualifying text from an iterable of candidates, title-shaped."""
    for t in texts:
        t = clean_prompt_text(t)
        if t:
            return truncate_title(t)
    return ""


def looks_like_session_id(title, session_id: str = "") -> bool:
    """True when a stored "title" is really just the id (empty, a UUID, the
    session id itself, or a truncated prefix of it) — i.e. not a real title
    worth preserving, so a derived one may replace it (the no-clobber rule
    only protects human-meaningful titles)."""
    t = (title or "").strip()
    if not t:
        return True
    if _UUID_RE.match(t):
        return True
    sid = (session_id or "").strip()
    if sid:
        bare = sid.split(":", 1)[-1]
        if t in (sid, bare):
            return True
        # Truncated-id titles (the list path stores sid[:40]); require a
        # real prefix length so a short genuine title can't false-positive.
        if len(t) >= 8 and (sid.startswith(t) or bare.startswith(t)):
            return True
    return False


def _texts_from_content(content):
    """Yield candidate strings from a message ``content`` (str or blocks)."""
    if isinstance(content, str):
        yield content
    elif isinstance(content, list):
        for block in content:
            if isinstance(block, str):
                yield block
            elif isinstance(block, dict) and block.get("type") == "text":
                t = block.get("text")
                if isinstance(t, str):
                    yield t


def iter_user_prompt_texts(jsonl_path, max_lines: int = 500):
    """Yield user-prompt candidate texts from a transcript file head.

    Ground-truth Claude Code shape: one JSON object per line,
    ``{"type": "user", "message": {"content": "…" | [blocks]}}``. Top-level
    ``role: user`` rows (other family runtimes / older files) are accepted
    too. ``max_lines`` bounds the read — this is a head-read, never a full
    parse of a multi-MB transcript.
    """
    with open(jsonl_path, "r", errors="replace") as f:
        for i, line in enumerate(f):
            if i >= max_lines:
                return
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except (json.JSONDecodeError, ValueError):
                continue
            if not isinstance(obj, dict):
                continue
            if obj.get("type") != "user" and obj.get("role") != "user":
                continue
            msg = obj.get("message")
            if not isinstance(msg, dict):
                msg = obj
            if msg.get("role") not in (None, "user"):
                continue
            yield from _texts_from_content(msg.get("content"))


def derive_title_from_jsonl(jsonl_path, max_lines: int = 500) -> str:
    """Title from a transcript file head. Never raises; "" when unusable."""
    try:
        return derive_title_from_texts(
            iter_user_prompt_texts(jsonl_path, max_lines=max_lines)
        )
    except Exception:
        return ""


def derive_title_from_family_events(events) -> str:
    """Title from unified adapter Event objects (the ``sync_family_runtimes``
    in-memory event list — covers codex/cursor/… without touching their
    native stores).

    Pass 1 considers only ``role == "user"`` events; pass 2 falls back to any
    event text (some adapters don't stamp roles — this preserves the legacy
    behaviour that titled those runtimes before). Never raises.
    """
    try:
        events = list(events or [])

        def _texts(user_only):
            for e in events:
                role = str(getattr(e, "role", "") or "").lower()
                if user_only and role != "user":
                    continue
                yielded = False
                for c in _texts_from_content(getattr(e, "content", None)):
                    yielded = True
                    yield c
                if not yielded:
                    t = getattr(e, "text", "")
                    if isinstance(t, str):
                        yield t

        return (derive_title_from_texts(_texts(True))
                or derive_title_from_texts(_texts(False)))
    except Exception:
        return ""


def claude_projects_root() -> Path:
    """Claude Code's projects dir (mirrors ``sync._claude_projects_root``;
    duplicated here so routes/ can use it without importing the daemon)."""
    custom = os.environ.get("CLAUDE_CONFIG_DIR")
    if custom:
        return Path(os.path.expanduser(custom)) / "projects"
    return Path(os.path.expanduser("~/.claude/projects"))


def find_claude_transcript(session_uuid: str):
    """Locate ``~/.claude/projects/<slug>/<uuid>.jsonl``.

    The slug encodes the agent's CWD, which we don't know — scan project
    dirs (there are tens, not thousands). Returns a Path or None.
    """
    sid = (session_uuid or "").strip()
    if not sid or "/" in sid or os.sep in sid:
        return None
    try:
        root = claude_projects_root()
        if not root.is_dir():
            return None
        for proj_dir in root.iterdir():
            p = proj_dir / f"{sid}.jsonl"
            if p.is_file():
                return p
    except OSError:
        return None
    return None


def _cache_put(key: str, title: str) -> None:
    if len(_TITLE_CACHE) >= _TITLE_CACHE_MAX:
        # FIFO eviction — plenty for the most-recent-N sessions we re-touch.
        try:
            _TITLE_CACHE.pop(next(iter(_TITLE_CACHE)))
        except (StopIteration, KeyError):
            _TITLE_CACHE.clear()
    _TITLE_CACHE[key] = title


def title_for_family_session(runtime: str, session_id: str, events=None) -> str:
    """Derive (and cache) a title for a family-runtime session.

    claude_code: prefer the ground-truth ``~/.claude`` transcript head, then
    the in-memory adapter events. Other runtimes: events only (their native
    stores live behind pro adapters we don't re-open here). Never raises.
    """
    key = f"{runtime}:{session_id}"
    try:
        cached = _TITLE_CACHE.get(key)
        if cached:
            return cached
        title = ""
        if runtime == "claude_code":
            path = find_claude_transcript(session_id)
            if path is not None:
                title = derive_title_from_jsonl(path)
        if not title and events is not None:
            title = derive_title_from_family_events(events)
        if title:
            _cache_put(key, title)
        return title
    except Exception:
        return ""
