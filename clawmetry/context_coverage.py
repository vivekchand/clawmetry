"""Which context-blowout signals we can actually see, per runtime.

The problem this solves
-----------------------
A "Context blowouts: 0" tile is two completely different statements wearing
the same clothes:

  * this runtime ran clean, nothing overflowed; or
  * we have no way to observe overflow on this runtime at all.

Rendering those identically is worse than not shipping the tile. A user
comparing runtimes reads the second as the first and concludes their Codex
sessions never blow out, when the truth is that our Codex adapter emits no
compaction event and we were never going to see one.

ClawMetry sees context pressure through three independent signals, and
runtimes support different subsets:

  ``utilization``  Per-turn prompt-side token counts. Present whenever the
                   runtime records a usage envelope on its assistant turns.
                   This is the signal behind the "how full is the window"
                   gauge, and the one most runtimes do support.
  ``compaction``   An explicit event saying the harness summarised and
                   dropped history. Only some adapters surface one, because
                   only some runtimes write one down.
  ``overflow``     The provider rejected the prompt as too long — read out of
                   error text (see ``LocalStore._OVERFLOW_MARKERS``). Not
                   runtime-specific: wherever we ingest errors, we can spot
                   one.

The verdicts
------------
Coverage is reported **per runtime per signal**, and is measured from the
user's own store first — a declaration that disagrees with observed data
loses. Verdicts:

  ``observed``             we have this signal in the window. Counts are real.
  ``supported_none_seen``  the runtime can produce it; none occurred here.
                           A zero is a real zero.
  ``unsupported``          the adapter emits no such signal. A zero means
                           "blind", and the UI must say so rather than
                           render a reassuring 0.

``UNSUPPORTED_COMPACTION`` below is the only hand-maintained part, and it is
deliberately a *denylist of known-blind runtimes* rather than an allowlist of
capable ones. Getting the denylist wrong degrades a runtime to
``supported_none_seen`` — an honest "nothing seen" — whereas an allowlist
that goes stale would claim blindness for a runtime that just started
reporting. Failure should land on the cautious side.
"""

from __future__ import annotations

from typing import Any

# Signals, in the order the UI should present them (cheapest/most universal
# first).
SIGNALS = ("utilization", "compaction", "overflow")

# Runtimes whose adapter emits no compaction event, verified by reading the
# adapters rather than assumed: a runtime is listed here only when its module
# contains no ``type="compaction"`` emission. Re-check with
#
#     grep -c 'type="compaction"' clawmetry_pro/adapters/<runtime>.py
#
# A runtime that starts emitting one should be deleted from this set in the
# same PR, and ``tests/test_context_coverage.py`` pins the pairing so the two
# cannot drift apart silently.
#
# PENDING: ``codex`` comes off this list once a clawmetry-pro wheel carrying
# clawmetry-pro#174 (merged 2026-08-25, which maps Codex's
# ``RolloutItem::Compacted`` rollout line) is actually released. The trigger is
# the released wheel, NOT the merge: a user still on the previous wheel is
# genuinely blind, and delisting early would tell them "0, ran clean" while we
# cannot see. Deliberately not removed ahead of that wheel, because the two
# mistakes are not symmetric.
# Leaving it listed tells a user with no compactions that we are blind when we
# are not (conservative, and anyone who does have compactions is unaffected,
# since observation overrides this set). Removing it early tells a user
# "0, ran clean" while we are genuinely blind, which is the failure this
# module exists to prevent.
UNSUPPORTED_COMPACTION = frozenset({
    "aider",
    "claude_code",
    "cline",
    "codex",
    "cursor",
    "deepagents",
    "deepseek_harness",
    "devin",
    "exo",
    "gemini_cli",
    "goose",
    "grok",
    "hermes",
    "n8n",
    "nanoclaw",
    "opencode",
    "openhands",
    # OpenWorker DOES record compaction, but as a single current boundary on
    # the session row rather than as events, and the count above is derived
    # from events whose type contains "compact". So we would report "0
    # compactions, ran clean" for a session that has compacted, which is the
    # exact failure this module exists to prevent. Delist once the adapter
    # emits a compaction event, and only once the WHEEL carrying that ships.
    "openworker",
    # Grok Bot compacts (if at all) on its cloud VM; the desktop client
    # store has no compaction entry kind, so absence proves nothing.
    "grok_bot",
    # Lovable's agent runs (and manages its own context) in the vendor
    # cloud; the local surface is a git clone of the synced repo, which
    # records commits, not context events. Absence proves nothing.
    "lovable",
    # Replit Agent manages context on Replit's servers (checkpoints, scoped
    # chats); the in-workspace journal has no compaction entry kind, so
    # absence proves nothing.
    "replit",
    "picoclaw",
    "qm",
    "qwen_code",
})

# Runtimes whose own session store carries no token counts, so per-turn
# utilization cannot be computed from the transcript alone. Both are known
# and documented in ``sync.sync_vm_usage_log``: picoclaw writes a flat
# providers.Message JSONL with no usage envelope, and cursor's tokens live
# behind a proprietary backend. For these, cost/usage arrives via the hosted
# VM usage log instead, which has no per-turn context size in it.
UNSUPPORTED_UTILIZATION = frozenset({"picoclaw", "cursor"})


def declared_support(runtime: str, signal: str) -> bool:
    """Can ``runtime`` produce ``signal`` at all?

    Unknown runtimes are assumed capable — see the module docstring on why
    the conservative default is "we should have seen it" rather than
    "we're blind".
    """
    rt = (runtime or "").lower()
    if signal == "compaction":
        return rt not in UNSUPPORTED_COMPACTION
    if signal == "utilization":
        return rt not in UNSUPPORTED_UTILIZATION
    # Overflow is read out of error text, which is not adapter-specific.
    return True


def verdict(runtime: str, signal: str, observed_count: int) -> str:
    """One of ``observed`` / ``supported_none_seen`` / ``unsupported``.

    Observation wins over declaration: if we actually have the signal in the
    store, the runtime plainly supports it, whatever this module believes.
    That ordering is what stops a stale denylist from hiding real data.
    """
    if observed_count > 0:
        return "observed"
    return "supported_none_seen" if declared_support(runtime, signal) else "unsupported"


def explain(runtime: str, signal: str, v: str) -> str:
    """One line a UI can put next to the number. Empty when nothing needs
    saying (the count speaks for itself)."""
    if v != "unsupported":
        return ""
    if signal == "compaction":
        return (
            f"{runtime} does not record compaction events. A zero here means "
            "ClawMetry cannot see them, not that none happened. Window "
            "utilization below is still measured."
        )
    if signal == "utilization":
        return (
            f"{runtime} does not record per-turn token counts in its session "
            "store, so window utilization cannot be computed from the "
            "transcript."
        )
    return ""


def summarise(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Roll per-runtime coverage rows into headline counts for a tab header.

    ``rows`` is what ``LocalStore.query_context_coverage`` returns.
    """
    total = len(rows)
    full = sum(
        1 for r in rows
        if all(r.get(s, {}).get("verdict") != "unsupported" for s in SIGNALS)
    )
    return {
        "runtimes": total,
        "fully_observable": full,
        "partially_observable": total - full,
        "signals": list(SIGNALS),
    }
