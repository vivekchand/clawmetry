"""What each runtime actually records — so a surface can say "not recorded"
instead of rendering a zero.

The Observe pillar's real gap was never breadth, it was consistency. Coverage
is honest *per adapter*, but the surfaces above the adapters (the Cost tab, the
Efficiency grade, model attribution) are call-event driven: they sum per-call
token/cost rows. A runtime that never writes per-call cost to disk therefore
renders as a $0.00 / grade-less / empty panel, which reads as **ClawMetry is
broken** rather than **this runtime does not record that**.

Those are opposite messages to a buyer. "Cursor spent $0.00 this month" is a
false statement about their spend; "Cursor does not record cost where ClawMetry
can read it" is a true statement about Cursor. This module is the difference:
one declared table of what each runtime persists, so every surface can tell an
idle runtime apart from a token-blind one and say *which* and *why*.

Ground truth is ``docs/compatibility.md`` — the per-runtime table we maintain
from real installs and real captures. Each entry below carries the exact
sentence from that runtime's row that justifies its verdict, and
``tests/test_runtime_records.py`` fails if the sentence is no longer in the doc.
So the table cannot quietly drift away from the documented reality, and a new
runtime cannot be added to the catalogue without someone deciding what it
records.

Deliberately NOT in here: how ClawMetry reads any of it. No store paths, no
filenames, no table or column names, no env vars. This module answers "what
will the operator see", which is the half we publish.
"""
from __future__ import annotations

# ── signal states ────────────────────────────────────────────────────────
# The runtime writes it; ClawMetry reads it straight off the runtime's own
# record. Numbers are the runtime's, not ours.
ON_DISK = "on_disk"
# The runtime does not write it, but ClawMetry can compute it from something
# the runtime DOES write (cost from token counts x published model prices).
# Real, and labelled as derived so nobody mistakes it for a vendor invoice.
DERIVED = "derived"
# The runtime keeps no record ClawMetry can read. There is no number to show
# and no way to compute one. This is the state that must never render as 0.
UNAVAILABLE = "unavailable"
# Not yet verified against a real capture of this runtime. Honest ignorance —
# rendered as "not verified", never as a zero and never as a claim.
UNKNOWN = "unknown"
# The runtime records it for SOME of its work and not the rest, and nothing on
# disk marks which is which. A total is therefore a floor, not a bill. This
# state exists because collapsing it into ON_DISK reintroduces exactly the bug
# this module was written to remove: a number presented as complete when it is
# not. Surfaces must show the number AND say it is a floor.
PARTIAL = "partial"

_STATES = frozenset({ON_DISK, DERIVED, UNAVAILABLE, UNKNOWN, PARTIAL})

# Signals a surface can ask about. Deliberately short: these are the three the
# broken-looking panels actually depend on. Adding a fourth means being able to
# answer it for all 28 runtimes, which is the bar that keeps this table true.
SIGNALS = ("tokens", "cost", "model")


def _e(tokens, cost, model, evidence, *, note="", doc_label=None, doc_file="docs/compatibility.md"):
    return {
        "tokens": tokens,
        "cost": cost,
        "model": model,
        "evidence": evidence,
        "note": note,
        "doc_label": doc_label,
        "doc_file": doc_file,
    }


# Keyed by the runtime ids in ``clawmetry.entitlements.ALL_RUNTIMES``.
RUNTIME_RECORDS: dict[str, dict] = {
    # ── OpenClaw family ──────────────────────────────────────────────────
    "openclaw": _e(
        ON_DISK, ON_DISK, ON_DISK,
        "Tokens and pre-computed cost",
        doc_file="docs/RUNTIME_FAMILY.md",
        note="OpenClaw writes both token counts and its own cost figure, so "
             "every cost surface reads the runtime's own numbers.",
    ),
    "nemoclaw": _e(
        ON_DISK, ON_DISK, ON_DISK,
        "OpenClaw v3 JSONL",
        doc_label="NVIDIA NemoClaw",
        note="NemoClaw records in the OpenClaw shape, so it carries the same "
             "tokens and cost OpenClaw does.",
    ),
    "picoclaw": _e(
        UNAVAILABLE, UNAVAILABLE, ON_DISK,
        "Tokens/cost not on disk",
        note="PicoClaw records the conversation and which model answered, but "
             "no token counts and no cost. Transcripts, tool calls and model "
             "attribution are complete; spend is not something PicoClaw keeps.",
    ),
    "nanoclaw": _e(
        UNAVAILABLE, UNAVAILABLE, UNAVAILABLE,
        "Model/tokens/cost not on disk",
        note="NanoClaw records the conversation only. Transcripts and message "
             "counts are complete; model, tokens and cost are not written "
             "anywhere ClawMetry can read.",
    ),
    "hermes": _e(
        ON_DISK, ON_DISK, ON_DISK,
        "pre-computed tokens/cost",
        note="Hermes computes and stores its own tokens and cost, so cost "
             "surfaces read the runtime's numbers rather than ours.",
    ),
    # ── coding agents that record usage but not money ────────────────────
    "claude_code": _e(
        ON_DISK, DERIVED, ON_DISK,
        "token usage",
        note="Claude Code records token usage per turn but not a dollar "
             "figure. ClawMetry prices those tokens at published rates, so "
             "cost here is an API-equivalent estimate, not a vendor invoice — "
             "on a Claude subscription the incremental cost is $0.",
    ),
    "codex": _e(
        ON_DISK, DERIVED, ON_DISK,
        "token usage",
        note="Codex records token usage but no dollar figure. ClawMetry "
             "prices those tokens at published rates, so cost is an "
             "API-equivalent estimate rather than a vendor invoice.",
    ),
    "aider": _e(
        ON_DISK, DERIVED, ON_DISK,
        "token counts",
        note="Aider records token counts per exchange but no cost. ClawMetry "
             "prices them at published rates.",
    ),
    "goose": _e(
        ON_DISK, DERIVED, ON_DISK,
        "real token totals",
        note="Goose records real token totals but no cost figure. ClawMetry "
             "prices them at published rates.",
    ),
    "qwen_code": _e(
        ON_DISK, DERIVED, ON_DISK,
        "real token usage",
        note="Qwen Code records real token usage but no cost figure. "
             "ClawMetry prices it at published rates.",
    ),
    "grok": _e(
        ON_DISK, DERIVED, ON_DISK,
        "per-turn token split",
        note="Grok records a per-turn token split and which model served it, "
             "but no cost. ClawMetry prices the tokens at published rates.",
    ),
    "gemini_cli": _e(
        ON_DISK, DERIVED, ON_DISK,
        "Per-turn token split",
        note="Gemini CLI records a per-turn token split and the model id, but "
             "no cost. ClawMetry prices the tokens at published rates.",
    ),
    # ── runtimes that record money themselves ────────────────────────────
    "opencode": _e(
        ON_DISK, ON_DISK, ON_DISK,
        "real tokens + cost",
        note="opencode stores both tokens and cost, so the numbers shown are "
             "the runtime's own.",
    ),
    "pi": _e(
        ON_DISK, ON_DISK, ON_DISK,
        "real tokens + cost",
        note="Pi stores both tokens and cost, so the numbers shown are the "
             "runtime's own.",
    ),
    "deepagents": _e(
        ON_DISK, ON_DISK, ON_DISK,
        "real tokens + cost",
        doc_label="Deep Agents",
        note="Deep Agents stores both tokens and cost, so the numbers shown "
             "are the runtime's own.",
    ),
    "antigravity": _e(
        ON_DISK, ON_DISK, ON_DISK,
        "token split (prompt/thinking/response) and cost",
        note="Antigravity records a per-generation token split and cost, "
             "including background generations that burn tokens with no "
             "visible turn.",
    ),
    "copilot": _e(
        ON_DISK, ON_DISK, ON_DISK,
        "vendor-billed AI-credit cost",
        doc_label="GitHub Copilot",
        note="Copilot records a cache-aware token split and the AI-credit "
             "cost the vendor actually bills, so this is a real charge rather "
             "than an estimate.",
    ),
    "exo": _e(
        ON_DISK, ON_DISK, ON_DISK,
        "Per-call usage + cost persisted by Exo itself",
        note="Exo persists per-call usage and cost itself, so the numbers "
             "shown are the runtime's own.",
    ),
    "cline": _e(
        ON_DISK, ON_DISK, ON_DISK,
        "Cost in USD is on disk",
        note="Cline records cost in USD directly, which is rare — the figure "
             "shown is the runtime's own, not a price-list estimate.",
    ),
    "openhands": _e(
        ON_DISK, ON_DISK, ON_DISK,
        "Tokens and per-call cost live in the sidecar",
        note="OpenHands records tokens and per-call cost. Its cost reads 0.00 "
             "both for a free local model and for a pricing lookup it could "
             "not resolve, so a genuine zero and a missing price look alike.",
    ),
    "grok_bot": _e(
        UNAVAILABLE, UNAVAILABLE, UNAVAILABLE,
        "No tokens, model or cost",
        note="Grok Bot runs inference on its own cloud VM. The desktop client "
             "stores the full transcript -- both sides -- but an exhaustive walk "
             "of its store finds no token counts, no model id and no cost: the "
             "fields do not exist rather than being empty. Transcripts and local "
             "tool-permission asks are complete; spend is not observable here at "
             "all, so no figure is derived.",
    ),
    "openworker": _e(
        ON_DISK, DERIVED, ON_DISK,
        "The token split rides a per-message sidecar tagged with the model "
        "that produced that turn",
        note="OpenWorker persists the token split (input/output/cache read and "
             "write) on every assistant message, tagged with the model that "
             "produced it, so a session that switches models is priced per "
             "model. It writes no dollars anywhere, so cost is always derived "
             "from the pricing table, never reported. Its audit log also "
             "carries token columns; those meter the Auto-Approve reviewer, "
             "not the agent, and are deliberately excluded from session cost.",
    ),
    # ── partial / conditional ────────────────────────────────────────────
    "n8n": _e(
        PARTIAL, PARTIAL, ON_DISK,
        "tokens + cost where the model sub-node records usage",
        note="n8n records tokens and cost only for workflow steps whose model "
             "node reports usage. Steps that do not report leave real spend "
             "uncounted, so an n8n total is a floor, not a full bill.",
    ),
    # ── token-blind runtimes ─────────────────────────────────────────────
    "cursor": _e(
        UNAVAILABLE, UNAVAILABLE, ON_DISK,
        "No billed cost on disk (server-side)",
        note="Cursor bills server-side and keeps no token or cost record on "
             "the machine. Transcripts and model attribution are complete; "
             "spend has to come from Cursor's own billing page.",
    ),
    "deepseek_harness": _e(
        UNAVAILABLE, UNAVAILABLE, ON_DISK,
        "Transcripts, model, tool calls",
        doc_label="DeepSeek Harness",
        note="DeepSeek Harness records the conversation, the model and tool "
             "calls, but no token counts and no cost.",
    ),
    "kimi": _e(
        UNKNOWN, UNKNOWN, UNAVAILABLE,
        "Model id is not written to disk",
        doc_label="Kimi CLI",
        note="Kimi CLI does not write the model id, so model attribution is "
             "blank by design. Whether it records usage has not been verified "
             "against a real capture yet.",
    ),
    "qm": _e(
        UNAVAILABLE, UNAVAILABLE, UNAVAILABLE,
        "delegates to Pi / opencode / Codex / Claude Code, which show up as "
        "their own runtimes",
        note="QM orchestrates other runtimes rather than calling models "
             "itself. Its spend appears under the runtime that did the work, "
             "so a QM total of zero is correct, not missing data.",
    ),
    "devin": _e(
        UNKNOWN, UNKNOWN, UNKNOWN,
        "Sessions and tool calls",
        note="Not yet verified against a real capture. Sessions and tool "
             "calls are read; whether usage and cost are recorded has not "
             "been confirmed, so no number is claimed either way.",
    ),
}


def record_for(runtime: str | None) -> dict:
    """What ``runtime`` records. Unknown ids get the all-``UNKNOWN`` shape
    rather than an exception — a surface asking about a runtime we have never
    heard of must still render something honest."""
    key = (runtime or "").strip().lower()
    entry = RUNTIME_RECORDS.get(key)
    if entry is None:
        return {"tokens": UNKNOWN, "cost": UNKNOWN, "model": UNKNOWN,
                "evidence": "", "note": "", "doc_label": None,
                "doc_file": "docs/compatibility.md"}
    return entry


def state_of(runtime: str | None, signal: str) -> str:
    """State of one signal (``tokens`` / ``cost`` / ``model``) for a runtime."""
    return record_for(runtime).get(signal, UNKNOWN)


def is_recorded(runtime: str | None, signal: str) -> bool:
    """True when a real number can be shown for ``signal`` — the runtime wrote
    it, ClawMetry can derive it, or it covers part of the work. False means the
    panel must say so instead of rendering a zero.

    ``PARTIAL`` counts as recorded: there IS a number and suppressing it would
    hide real spend. It carries a caveat instead, via ``coverage_payload``."""
    return state_of(runtime, signal) in (ON_DISK, DERIVED, PARTIAL)


def unrecorded_signals(runtime: str | None) -> list[str]:
    """Signals this runtime does not record at all. Empty for a runtime that
    records everything, and empty for ``UNKNOWN`` — unverified is not the same
    claim as absent."""
    rec = record_for(runtime)
    return [s for s in SIGNALS if rec.get(s) == UNAVAILABLE]


def unverified_signals(runtime: str | None) -> list[str]:
    """Signals we have not verified for this runtime."""
    rec = record_for(runtime)
    return [s for s in SIGNALS if rec.get(s, UNKNOWN) == UNKNOWN]


def _label(runtime: str | None) -> str:
    try:
        from clawmetry.entitlements import RUNTIME_LABELS
        return RUNTIME_LABELS.get((runtime or "").strip().lower()) or (runtime or "this runtime")
    except Exception:
        return runtime or "this runtime"


def coverage_payload(runtime: str | None, *, has_data: bool = False) -> dict:
    """The block every cost/usage/efficiency surface attaches when it is
    scoped to one runtime.

    ``has_data`` is whether the surface actually found rows. It is what
    separates the two empty states that look identical today:

      * ``status="not_recorded"`` — the runtime keeps no such record. Show the
        reason. A zero here would be a false statement about the user's spend.
      * ``status="unverified"``  — we have not confirmed what this runtime
        records. Say that; claim nothing.
      * ``status="no_activity"`` — the runtime records it fine and there was
        simply nothing in the window. A zero here is true.
      * ``status="ok"``          — real data.

    Always returns a dict; never raises.
    """
    try:
        rt = (runtime or "").strip().lower()
        rec = record_for(rt)
        label = _label(rt)
        missing = unrecorded_signals(rt)
        unverified = unverified_signals(rt)
        cost_state = rec.get("cost", UNKNOWN)

        if has_data:
            status = "ok"
        elif cost_state == UNAVAILABLE:
            status = "not_recorded"
        elif cost_state == UNKNOWN:
            status = "unverified"
        else:
            status = "no_activity"

        if status == "not_recorded":
            headline = f"Not recorded by {label}"
        elif status == "unverified":
            headline = f"Not verified for {label}"
        elif status == "no_activity":
            headline = f"No activity for {label} in this window"
        else:
            headline = ""

        return {
            "runtime": rt,
            "runtime_label": label,
            "status": status,
            "headline": headline,
            "detail": rec.get("note") or "",
            "records": {s: rec.get(s, UNKNOWN) for s in SIGNALS},
            "unrecorded": missing,
            "unverified": unverified,
            # True only when the surface must suppress its number entirely.
            # A UI reading one boolean gets the safe behaviour by default.
            "suppress_zero": status in ("not_recorded", "unverified"),
            "cost_is_estimate": cost_state == DERIVED,
            # The number is real but covers only part of the work, so it is a
            # floor. Shown, never suppressed, and never presented as a total.
            "cost_is_partial": cost_state == PARTIAL,
            "partial_note": (rec.get("note") or "") if cost_state == PARTIAL else "",
        }
    except Exception:
        return {
            "runtime": (runtime or ""), "runtime_label": (runtime or ""),
            "status": "unverified", "headline": "", "detail": "",
            "records": {s: UNKNOWN for s in SIGNALS},
            "unrecorded": [], "unverified": list(SIGNALS),
            "suppress_zero": False, "cost_is_estimate": False,
            "cost_is_partial": False, "partial_note": "",
        }
