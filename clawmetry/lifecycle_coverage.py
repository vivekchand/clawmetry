"""Which lifecycle facts each runtime can put on a session's trail.

The problem this solves
-----------------------
Claude Code fires a hook for every lifecycle fact ClawMetry records: a tool
that failed, a subagent that started or stopped, a tool call the runtime
itself refused, a context compaction, the session start, and the
instructions file that was loaded. Most other runtimes offer no hook at
all, and their transcripts carry only some of those facts after the event.

An empty "Permission denials" row on a Cursor session is therefore two
different statements wearing the same clothes: nothing was refused, or
Cursor never tells anyone what it refused. Rendering them identically is
how a trail tells a confident lie, so this module is the declared, single
source both the local and the hosted dashboard read to say which one it is.

Vocabulary (the same three verdicts ``context_coverage`` uses, in the
declared form the trail work chose):

  ``full``     the runtime reports the fact as it happens (a hook or a
               structured runtime event), and ClawMetry records it.
  ``partial``  the fact is recoverable after the event, from the transcript
               or the session row, with a stated limitation.
  ``none``     the runtime does not expose the fact, or ClawMetry has not
               verified a source for it. The note says which.

Every runtime in ``entitlements.FREE_RUNTIMES | PAID_RUNTIMES`` has an
entry; ``tests/test_hook_lifecycle.py`` asserts that. Where nothing has
been verified against the runtime's real store the honest default is
``none`` with a note that says so, never an invented ``partial``.
"""
from __future__ import annotations

from typing import Any

from clawmetry import context_coverage as _cc

# The seven facts, in the order the trail presents them.
FACTS: tuple[str, ...] = (
    "tool_failed",
    "subagent_started",
    "subagent_stopped",
    "permission_denied",
    "context_compacted",
    "session_started",
    "instructions_loaded",
)

# Event types the daemon writes for each fact (the hook intake and any
# transcript adapter that emits the same fact use these names).
EVENT_TYPES: dict[str, str] = {
    "tool_failed": "tool.failed",
    "subagent_started": "subagent.started",
    "subagent_stopped": "subagent.stopped",
    "permission_denied": "permission.denied",
    "context_compacted": "context.compacted",
    "session_started": "session.started",
    "instructions_loaded": "instructions.loaded",
}

FACT_LABELS: dict[str, str] = {
    "tool_failed": "Tool failures",
    "subagent_started": "Subagent starts",
    "subagent_stopped": "Subagent stops",
    "permission_denied": "Permission denials",
    "context_compacted": "Context compactions",
    "session_started": "Session start",
    "instructions_loaded": "Instructions loaded",
}

VERDICTS: tuple[str, ...] = ("full", "partial", "none")

_NOT_VERIFIED = "not verified against this runtime's session store yet"
_NO_HOOK = "no hook system exposes this fact; the transcript does not record it"


def _entry(**facts: "tuple[str, str]") -> dict[str, dict[str, str]]:
    return {k: {"verdict": v, "note": n} for k, (v, n) in facts.items()}


def _default_entry(runtime: str) -> dict[str, dict[str, str]]:
    """The honest floor for a runtime nothing has been verified for.

    Compaction is the one fact with an already-verified source: the
    ``context_coverage`` denylist is maintained by reading each adapter for
    a compaction emission, so a runtime *not* on that list is ``partial``
    (recovered from the transcript, not reported as it happens).
    """
    out = {f: {"verdict": "none", "note": _NOT_VERIFIED} for f in FACTS}
    if _cc.declared_support(runtime, "compaction"):
        out["context_compacted"] = {
            "verdict": "partial",
            "note": "recovered from compaction events in the transcript, "
                    "not reported as it happens",
        }
    return out


# Hand-declared entries: only what has been read off the runtime's own
# hook docs or ClawMetry's ingest code. Anything not listed here falls to
# ``_default_entry``.
_DECLARED: dict[str, dict[str, dict[str, str]]] = {
    # Claude Code: all seven facts arrive from lifecycle hooks
    # (clawmetry/hooks_claude_code.py, `clawmetry hooks install`).
    "claude_code": _entry(
        tool_failed=("full", "PostToolUseFailure hook"),
        subagent_started=("full", "SubagentStart hook"),
        subagent_stopped=("full", "SubagentStop hook"),
        permission_denied=("full", "PermissionDenied hook; fires only when "
                                   "Claude Code itself refuses a call, so a "
                                   "human pressing No is not a denial"),
        context_compacted=("full", "PostCompact hook"),
        session_started=("full", "SessionStart hook"),
        instructions_loaded=("full", "InstructionsLoaded hook; the file is "
                                     "read at load time, stored redacted and "
                                     "capped, and hashed"),
    ),
    # OpenClaw: the v3 transcript is structured, so several facts are
    # recoverable after the event (clawmetry/sync.py).
    "openclaw": _entry(
        tool_failed=("partial", "tool results carrying an error, read from "
                                "the transcript"),
        subagent_started=("partial", "subagent run records in the session "
                                     "store, read after the run starts"),
        subagent_stopped=("partial", "subagent run records in the session "
                                     "store, read after the run ends"),
        permission_denied=("none", "the gateway records exec approvals, but "
                                   "no denial event reaches the transcript"),
        context_compacted=("partial", "compaction events in the transcript"),
        session_started=("partial", "the session header line of the "
                                    "transcript"),
        instructions_loaded=("partial", "workspace instruction files are "
                                        "catalogued by the Memory tab; which "
                                        "were loaded for a given session is "
                                        "not recorded"),
    ),
    # Runtimes with a pre-tool hook that ClawMetry installs (runtime_gates):
    # the hook gates, it does not report a refusal.
    "cursor": _entry(
        tool_failed=("none", _NOT_VERIFIED),
        subagent_started=("none", _NOT_VERIFIED),
        subagent_stopped=("none", _NOT_VERIFIED),
        permission_denied=("none", "Cursor hooks expose a pre-tool gate "
                                   "only; there is no denial event"),
        context_compacted=("none", "Cursor does not record compaction "
                                   "events; see context coverage"),
        session_started=("none", _NOT_VERIFIED),
        instructions_loaded=("none", "Cursor rules are read by the editor; "
                                     "no load event is exposed"),
    ),
    "copilot": _entry(
        tool_failed=("none", _NOT_VERIFIED),
        subagent_started=("none", _NOT_VERIFIED),
        subagent_stopped=("none", _NOT_VERIFIED),
        permission_denied=("none", "Copilot CLI hooks expose a pre-tool gate "
                                   "only; there is no denial event"),
        context_compacted=("partial", "recovered from compaction events in "
                                      "the transcript, not reported as it "
                                      "happens"),
        session_started=("none", _NOT_VERIFIED),
        instructions_loaded=("none", "no load event is exposed"),
    ),
}


def coverage_for(runtime: str) -> dict[str, dict[str, str]]:
    """The seven-fact declaration for one runtime id."""
    rt = (runtime or "").strip().lower()
    declared = _DECLARED.get(rt)
    if declared is not None:
        return {f: dict(declared[f]) for f in FACTS}
    return _default_entry(rt)


def all_runtimes() -> list[str]:
    from clawmetry import entitlements as _ent
    return sorted(_ent.FREE_RUNTIMES | _ent.PAID_RUNTIMES)


def coverage_table() -> dict[str, dict[str, dict[str, str]]]:
    """Every runtime, every fact. Keyed by runtime id."""
    return {rt: coverage_for(rt) for rt in all_runtimes()}


def explain(runtime: str, fact: str) -> str:
    """One line a UI can put next to an empty row. Empty when the fact is
    fully covered (the row speaks for itself)."""
    row = coverage_for(runtime).get(fact) or {}
    v = row.get("verdict")
    label = FACT_LABELS.get(fact, fact)
    if v == "full":
        return ""
    if v == "partial":
        return f"{label}: {row.get('note') or 'recovered after the event'}"
    return f"{label}: not exposed by {runtime}"


def summarise(runtime: str) -> dict[str, Any]:
    """Headline for a session view: which facts are missing and why."""
    rows = coverage_for(runtime)
    missing = [f for f in FACTS if rows[f]["verdict"] == "none"]
    partial = [f for f in FACTS if rows[f]["verdict"] == "partial"]
    return {
        "runtime": runtime,
        "facts": rows,
        "full": [f for f in FACTS if rows[f]["verdict"] == "full"],
        "partial": partial,
        "none": missing,
        "lines": [explain(runtime, f) for f in FACTS if rows[f]["verdict"] != "full"],
    }
