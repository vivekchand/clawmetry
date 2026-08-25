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

from typing import Callable, Iterable, List, Optional, Sequence, Tuple


def hook_is_ours(hook: dict, markers: Sequence[str]) -> bool:
    """True if *hook*'s command carries one of our command markers."""
    if not isinstance(hook, dict):
        return False
    cmd = hook.get("command") or ""
    if not isinstance(cmd, str):
        return False
    return any(m in cmd for m in markers)


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
