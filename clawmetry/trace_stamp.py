"""Stamp agent-authored commits with the ClawMetry session that produced them.

Why this exists (PRD-pr-trace.md §2a): the vendor trailer Claude Code writes
(``Claude-Session: https://claude.ai/code/session_01…``) carries a **cloud**
session id that appears nowhere as structured metadata in the local transcript
— a scan of 200 transcripts found it only inside tool inputs and stdout. There
is no on-disk mapping from that id to a local session, so it cannot be joined
to anything ClawMetry stores.

So we write our own trailer, carrying the id we already own — the LocalStore
primary key::

    Clawmetry-Session: claude_code:36f12caf-56e7-4d1d-9db2-89808ad3d03a

That id is what ``/api/local/sessions``, ``/api/replay-tree/<sid>`` and
``/api/local/transcript/<sid>`` key on, so a commit stamped this way resolves
to a trace with **zero bridging**.

Coverage starts the day the hook is installed and cannot be backfilled
(PRD §3a): transcripts rotate, and the store keeps only the most recent
``CLAWMETRY_FAMILY_SESSION_LIMIT`` sessions per runtime. Every commit made
without the hook is a trace permanently lost.

Never raises. A stamping failure must never block a commit — the worst
outcome is an unstamped commit, and that is strictly better than a developer
unable to commit because an observability tool had an opinion.
"""

from __future__ import annotations

import logging
import os
import re
import subprocess

logger = logging.getLogger("clawmetry.trace_stamp")

TRAILER_KEY = "Clawmetry-Session"

#: ``env var`` -> runtime prefix used in LocalStore session ids. Order is
#: precedence: the first variable that is set wins. Values are matched against
#: ``sessions.session_id`` as ``f"{prefix}:{value}"``.
_ENV_LADDER: tuple[tuple[str, str], ...] = (
    ("CLAWMETRY_SESSION_ID", ""),          # explicit override, already prefixed
    ("CLAUDE_CODE_SESSION_ID", "claude_code"),
    ("OPENCLAW_SESSION_ID", "openclaw"),
    ("CODEX_SESSION_ID", "codex"),
    ("CURSOR_SESSION_ID", "cursor"),
    ("GOOSE_SESSION_ID", "goose"),
)

_TRAILER_RE = re.compile(
    rf"^{re.escape(TRAILER_KEY)}:\s*(\S+)\s*$", re.MULTILINE
)

#: A session id is opaque, but it lands in a commit message and later in a URL
#: path, so keep it to characters that survive both without quoting.
_SAFE_ID = re.compile(r"^[A-Za-z0-9_:.\-]{4,200}$")


def detect_session_id() -> str | None:
    """Return the LocalStore session id for the agent making this commit.

    Reads the runtime's own environment — deterministic, no daemon round-trip,
    and correct even when several agents run concurrently in the same repo
    (which is exactly the case the time-window heuristic gets wrong; see
    PRD §2b, where 94 of 96 PRs matched more than one session).

    Returns ``None`` when no agent runtime is detectable, which is the normal
    case for a human commit.
    """
    for var, prefix in _ENV_LADDER:
        raw = (os.environ.get(var) or "").strip()
        if not raw:
            continue
        sid = raw if not prefix else f"{prefix}:{raw}"
        if _SAFE_ID.match(sid):
            return sid
        logger.warning("ignoring malformed session id in %s", var)
    return None


def existing_trailer(message: str) -> str | None:
    """Return the session id already stamped on ``message``, if any."""
    m = _TRAILER_RE.search(message or "")
    return m.group(1) if m else None


def stamp(message: str, session_id: str | None = None) -> str:
    """Return ``message`` with the session trailer appended.

    Idempotent: a message that already carries the trailer is returned
    unchanged, so amends and rebases do not accumulate duplicates. Comment
    lines (``#``) are left at the end of the buffer where git put them, so
    the trailer stays inside the message body.
    """
    try:
        if message is None:
            return ""
        if existing_trailer(message):
            return message
        sid = session_id or detect_session_id()
        if not sid:
            return message

        lines = message.split("\n")
        # git's prepare-commit-msg buffer ends with a block of '#' comments and
        # possibly a scissors line; the trailer belongs before them. Blank
        # lines adjacent to that block belong to it, but a buffer that is only
        # blank at the end (the ordinary trailing newline) has no comment tail
        # at all -- treating it as one is how the trailer ends up orphaned
        # after two blank lines.
        cut = len(lines)
        for i in range(len(lines) - 1, -1, -1):
            s = lines[i].strip()
            if s.startswith("#") or not s:
                cut = i
            else:
                break

        body = lines[:cut]
        tail = lines[cut:]
        if not any(ln.strip().startswith("#") for ln in tail):
            tail = []  # nothing but the trailing newline
        while tail and not tail[0].strip():
            tail.pop(0)  # we re-add exactly one separator blank line below

        while body and not body[-1].strip():
            body.pop()
        if body:
            # Trailers form one block, so join an existing one without a blank
            # line. The subject line is never part of that block even when it
            # looks like a trailer -- "fix: a thing" matches the same shape as
            # "Co-Authored-By: x", and treating it as one glues the trailer
            # straight onto the subject.
            in_trailer_block = len(body) > 1 and bool(
                re.match(r"^[A-Za-z][A-Za-z0-9-]*:\s", body[-1])
            )
            if not in_trailer_block:
                body.append("")
        body.append(f"{TRAILER_KEY}: {sid}")
        if tail:
            return "\n".join(body + [""] + tail)
        return "\n".join(body) + "\n"
    except Exception as exc:  # never block a commit
        logger.warning("commit stamping failed, leaving message untouched: %s", exc)
        return message


def stamp_file(path: str) -> bool:
    """Stamp the commit-message file at ``path`` in place.

    This is the entry point git's ``prepare-commit-msg`` hook calls. Returns
    ``True`` when the file was modified.
    """
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as fh:
            original = fh.read()
        stamped = stamp(original)
        if stamped == original:
            return False
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(stamped)
        return True
    except Exception as exc:
        logger.warning("could not stamp %s: %s", path, exc)
        return False


# ── git hook installation ──────────────────────────────────────────────────

_HOOK_MARKER = "# clawmetry trace stamp"
_HOOK_BODY = f"""#!/bin/sh
{_HOOK_MARKER} -- see PRD-pr-trace.md. Removing this line disables the hook.
# Stamps agent-authored commits with the ClawMetry session that produced them.
# Exits 0 unconditionally: a stamping failure must never block a commit.
clawmetry trace stamp "$1" 2>/dev/null || true
exit 0
"""


def hook_command_works(cmd: str = "clawmetry") -> bool:
    """Can the binary the hook will call actually run ``trace stamp``?

    Found by dogfooding: `trace init` happily wrote a hook calling `clawmetry
    trace stamp` on a machine whose PATH `clawmetry` was an older release with
    no `trace` command. The hook ends in `|| true` so a commit is never
    blocked, which is correct, and it meant the hook silently did nothing.
    Every commit looked fine and no trailer was written, which is the worst
    shape a failure can take here: coverage cannot be backfilled, so the
    traces lost while it went unnoticed are lost permanently.
    """
    try:
        out = subprocess.run(
            [cmd, "trace", "--help"],
            capture_output=True, text=True, timeout=20, check=False,
        )
        return "trace" in (out.stdout or "") and out.returncode == 0
    except Exception:
        return False


def _hooks_dir(repo: str) -> str:
    out = subprocess.run(
        ["git", "rev-parse", "--git-path", "hooks"],
        cwd=repo, capture_output=True, text=True, timeout=10, check=False,
    )
    rel = (out.stdout or "").strip() or "hooks"
    return rel if os.path.isabs(rel) else os.path.join(repo, rel)


def install(repo: str | None = None, *, verify_binary: bool = True) -> dict:
    """Install the ``prepare-commit-msg`` hook in ``repo``.

    Refuses to clobber an unrelated existing hook — chaining someone else's
    hook script is their call, not ours — and refuses to install a hook that
    cannot run, which is a quieter and worse failure (see
    :func:`hook_command_works`).
    """
    repo = repo or os.getcwd()
    if verify_binary and not hook_command_works():
        return {
            "ok": False,
            "status": "stale-binary",
            "hint": ("the `clawmetry` on your PATH has no `trace` command, so the "
                     "hook would silently do nothing. Upgrade with "
                     "`pip install -U clawmetry` and re-run."),
        }
    try:
        hooks = _hooks_dir(repo)
        os.makedirs(hooks, exist_ok=True)
        path = os.path.join(hooks, "prepare-commit-msg")
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8", errors="replace") as fh:
                current = fh.read()
            if _HOOK_MARKER in current:
                return {"ok": True, "status": "already-installed", "path": path}
            return {
                "ok": False,
                "status": "foreign-hook",
                "path": path,
                "hint": f"add `clawmetry trace stamp \"$1\"` to {path} yourself",
            }
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(_HOOK_BODY)
        os.chmod(path, 0o755)
        return {"ok": True, "status": "installed", "path": path}
    except Exception as exc:
        return {"ok": False, "status": "error", "error": str(exc)[:200]}


def uninstall(repo: str | None = None) -> dict:
    repo = repo or os.getcwd()
    try:
        path = os.path.join(_hooks_dir(repo), "prepare-commit-msg")
        if not os.path.exists(path):
            return {"ok": True, "status": "not-installed"}
        with open(path, "r", encoding="utf-8", errors="replace") as fh:
            if _HOOK_MARKER not in fh.read():
                return {"ok": False, "status": "foreign-hook", "path": path}
        os.remove(path)
        return {"ok": True, "status": "removed", "path": path}
    except Exception as exc:
        return {"ok": False, "status": "error", "error": str(exc)[:200]}


def status(repo: str | None = None) -> dict:
    """Report whether stamping is active and what it would stamp right now."""
    repo = repo or os.getcwd()
    installed = False
    path = None
    try:
        path = os.path.join(_hooks_dir(repo), "prepare-commit-msg")
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8", errors="replace") as fh:
                installed = _HOOK_MARKER in fh.read()
    except Exception:
        pass
    return {
        "hook_installed": installed,
        "hook_path": path,
        "session_id": detect_session_id(),
        "runtime_detected": detect_session_id() is not None,
    }

# ── pre-push hook: the trigger for automatic tracing ───────────────────────

_PREPUSH_MARKER = "# clawmetry trace autopublish"
_PREPUSH_BODY = f"""#!/bin/sh
{_PREPUSH_MARKER} -- see PRD-pr-trace.md. Removing this line disables it.
# Captures a trace for the pushed branch and, where this repository opted in,
# publishes it and comments on the pull request.
# Exits 0 unconditionally: an observability tool must never block a push.
clawmetry trace autopublish >/dev/null 2>&1 || true
exit 0
"""


def install_prepush(repo: str | None = None) -> dict:
    """Install the ``pre-push`` hook that drives automatic tracing."""
    repo = repo or os.getcwd()
    try:
        hooks = _hooks_dir(repo)
        os.makedirs(hooks, exist_ok=True)
        path = os.path.join(hooks, "pre-push")
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8", errors="replace") as fh:
                current = fh.read()
            if _PREPUSH_MARKER in current:
                return {"ok": True, "status": "already-installed", "path": path}
            return {"ok": False, "status": "foreign-hook", "path": path,
                    "hint": f"add `clawmetry trace autopublish` to {path} yourself"}
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(_PREPUSH_BODY)
        os.chmod(path, 0o755)
        return {"ok": True, "status": "installed", "path": path}
    except Exception as exc:
        return {"ok": False, "status": "error", "error": str(exc)[:200]}
