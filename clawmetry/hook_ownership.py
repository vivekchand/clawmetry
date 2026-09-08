"""Ownership-aware editing of a shared hooks array.

ClawMetry is not the only thing that writes ``~/.claude/settings.json``.
GitKraken's ``gk ai hook install claude-code --force`` ships on a very large
install base, ``numbat`` is already co-resident on developer machines, and a
user may hand-write entries of their own.  Every one of those writers owns
part of the same array.

Two shapes of coexistence exist, and only one of them was ever handled:

* **Separate entry** — the foreign writer appends its own ``{matcher, hooks}``
  entry.  This is what ``numbat`` does today, and it is why co-installation
  appears to work.
* **Merged entry** — the foreign writer appends its command into the *hooks
  list of an entry that already exists*, typically the one whose matcher it
  wants.  This is the documented risk of a ``--force`` install, and it is
  invisible to any check that asks "is this entry ours?".

Removing at *entry* granularity is wrong the moment the second shape occurs:
an entry holding our command and a foreign one is not ours to delete.  Every
helper here works at *hook* granularity — it removes the commands carrying our
markers and leaves every sibling in place, dropping the entry itself only once
nothing is left in it.

The rule this module enforces, in one line: **never delete a hook you did not
write.**
"""
from __future__ import annotations

import os
from typing import Callable, Iterable, List, Optional, Sequence, Tuple

_QUOTE_CHARS = ("'", '"')


def normalize_command(cmd: str) -> str:
    """The form of a hook command line that marker tests must run against.

    Ownership is decided by looking for a marker substring — say
    ``clawmetry hook claude-code`` — inside the installed command.  The
    command we write quotes its launcher, because ``sys.executable`` and the
    console script routinely sit under a path containing a space, so the raw
    text reads::

        '/…/Application Support/ClawMetry/…/bin/clawmetry' hook claude-code …

    and the marker does **not** match: there is a closing quote where the
    marker expects a space.  Two things then break at once, and both were
    live:

    * the installer no longer recognises its OWN previous entry, so instead
      of replacing it, it appends another — once per install pass, forever;
    * the uninstaller no longer recognises it either, so it survives the
      uninstall pointing at a binary that has been deleted, and the runtime
      errors on every tool call.

    That is not an exotic path.  It is every macOS desktop-app install
    (``~/Library/Application Support/ClawMetry``), every Windows install
    under ``C:\\Program Files``, and every user whose home directory
    contains a space.

    Stripping the shell quoting (and the Windows ``.exe`` suffix, which sits
    between the launcher name and the subcommand for the same reason) makes
    ownership independent of *where* the launcher lives.
    """
    if not isinstance(cmd, str):
        return ""
    out = cmd
    for q in _QUOTE_CHARS:
        out = out.replace(q, "")
    return out.replace(".exe", "")


def command_binary(cmd: str) -> str:
    """The launcher path from a hook command line, shell-quoting honoured.

    ``cmd.split()[0]`` returns ``'/Users/me/Application`` for a quoted path
    with a space in it, so every "does this binary still exist?" test built
    on it answered the wrong question for exactly the installs that needed
    it most.
    """
    if not isinstance(cmd, str) or not cmd.strip():
        return ""
    try:
        import shlex
        parts = shlex.split(cmd, posix=(os.name != "nt"))
    except ValueError:          # unbalanced quotes — fall back to raw split
        parts = cmd.split()
    return parts[0] if parts else ""


def command_binary_exists(cmd: str) -> bool:
    """True when the command's launcher is runnable.

    Only absolute paths are checked; a bare name resolves through ``PATH`` at
    execution time and cannot be pre-judged here, so it is treated as live.
    """
    first = command_binary(cmd)
    if not first:
        return False
    if not os.path.isabs(first):
        return True
    return os.path.exists(first) if os.name == "nt" else os.access(first, os.X_OK)


def hook_is_ours(hook: dict, markers: Sequence[str]) -> bool:
    """True if *hook*'s command carries one of our command markers."""
    if not isinstance(hook, dict):
        return False
    cmd = hook.get("command") or ""
    if not isinstance(cmd, str):
        return False
    norm = normalize_command(cmd)
    return any(m in norm for m in markers)


def split_entry(entry: dict, markers: Sequence[str],
                ours_pred: "Optional[Callable[[dict], bool]]" = None,
                ) -> "Tuple[List[dict], List[dict]]":
    """Split *entry*'s hooks into ``(ours, foreign)``.

    *ours_pred* overrides the marker test for callers that own a narrower
    slice of the array (the mirror hook, for instance, is owned by a
    different installer than the gate even though both are ClawMetry).
    """
    pred = ours_pred or (lambda h: hook_is_ours(h, markers))
    ours: List[dict] = []
    foreign: List[dict] = []
    for h in (entry or {}).get("hooks") or []:
        (ours if pred(h) else foreign).append(h)
    return ours, foreign


def prune_our_hooks(entries: "Optional[Iterable]", markers: Sequence[str],
                    ours_pred: "Optional[Callable[[dict], bool]]" = None,
                    ) -> "Tuple[List[dict], int]":
    """Return ``(kept_entries, removed_hook_count)``.

    Removes only the hooks that are ours.  An entry that also holds foreign
    hooks survives carrying exactly those; an entry left empty is dropped.
    Non-dict entries are passed through untouched — a foreign writer's
    malformed row is still not ours to repair.
    """
    kept: List[dict] = []
    removed = 0
    for entry in list(entries or []):
        if not isinstance(entry, dict):
            kept.append(entry)          # not ours, not our problem
            continue
        ours, foreign = split_entry(entry, markers, ours_pred)
        if not ours:
            kept.append(entry)
            continue
        removed += len(ours)
        if foreign:
            entry["hooks"] = foreign    # preserve the co-resident writer
            kept.append(entry)
        # else: entry held only our hooks -> drop it
    return kept, removed


def foreign_hook_count(entries: "Optional[Iterable]", markers: Sequence[str],
                       ours_pred: "Optional[Callable[[dict], bool]]" = None,
                       ) -> int:
    """Number of hooks in *entries* that belong to somebody else.

    Used by the collision harness and the regression tests to assert the
    invariant directly: this number must never go down because of us.
    """
    pred = ours_pred or (lambda h: hook_is_ours(h, markers))
    n = 0
    for entry in entries or []:
        if not isinstance(entry, dict):
            continue
        for h in entry.get("hooks") or []:
            if isinstance(h, dict) and not pred(h):
                n += 1
    return n


# ── bounded hook timeouts ──────────────────────────────────────────────────
#
# The second way a co-installed gate hurts the user is time, not ownership.
# A hook timeout is how long the *runtime* will sit on a tool call waiting
# for us, and on a fail-closed runtime (Copilot CLI) a hook that never
# answers denies the call.  Deriving it from the longest policy window gave
# an installed timeout of 604860s — seven days — so anything that wedged our
# client wedged the user's agent for a week.
#
# The client itself is already bounded when ClawMetry is simply not running:
# ~2s, exit 0, empty stdout (no opinion).  The ceiling here covers the case
# the client cannot cover — a hook process that is alive but stuck.

DEFAULT_HOOK_TIMEOUT_CEILING_S = 28800   # 8 hours

_CEILING_ENV = "CLAWMETRY_HOOK_TIMEOUT_MAX_S"


def hook_timeout_ceiling_s(environ=None) -> int:
    """The configured ceiling, or 0 meaning "no ceiling".

    ``CLAWMETRY_HOOK_TIMEOUT_MAX_S=0`` restores the old unbounded behaviour
    for an operator who really does run week-long approval windows and
    accepts that a wedged hook blocks for that long.
    """
    import os as _os
    env = _os.environ if environ is None else environ
    raw = (env.get(_CEILING_ENV) or "").strip()
    if not raw:
        return DEFAULT_HOOK_TIMEOUT_CEILING_S
    try:
        val = int(raw)
    except (TypeError, ValueError):
        return DEFAULT_HOOK_TIMEOUT_CEILING_S
    return max(0, val)


def clamp_hook_timeout(seconds: int, environ=None) -> int:
    """Clamp an installed hook timeout to the ceiling.

    When a policy window is longer than the ceiling the runtime's own
    timeout now fires first, which means that one call is blocked by the
    runtime instead of resolving through the policy's ``on_timeout``.  That
    is the deliberate trade: a bounded block beats an unbounded one.
    """
    ceiling = hook_timeout_ceiling_s(environ)
    if ceiling <= 0:
        return int(seconds)
    return min(int(seconds), ceiling)
