"""
clawmetry/evaluators.py — the named evaluator CATALOGUE (single source of truth).

ClawMetry already COMPUTES most of the agent-quality signals that hosted eval
products (Traceloop, LangSmith, Langfuse, Phoenix) sell as their moat. We just
never presented them as a named, branded library. This module does exactly
that: it maps each shipped signal to a friendly, plain-language evaluator entry
so the dashboard can show "here are the named evaluators ClawMetry runs on your
agent" the same way the hosted tools do.

Design rules:
  * This is a CATALOGUE, not a compute path. It NEVER recomputes a signal.
    Each entry declares WHERE the value already comes from (a real DuckDB
    column or a real function), so the catalogue can't drift away from the
    code that actually produces the number. The guard test
    ``tests/test_evaluators_catalogue.py`` re-extracts every ``source`` and
    fails if it points at something that no longer exists.
  * Free entries map to OSS signals that ship today. Pro entries are declared
    here but their VALUE comes from the clawmetry-pro plugin when present
    (entitlement-gated); when the plugin is absent OSS shows them locked, with
    an honest upgrade state, never a silently-disabled blank.
  * Cloud-safe: the catalogue is static data. ``catalogue()`` works with no
    DuckDB store at all (the cloud container has none), so the Evaluators
    surface renders in the hosted dashboard without a blank.

Public API:
    catalogue() -> list[dict]                 # the named evaluators
    catalogue_with_coverage(store) -> dict     # catalogue + live coverage counts
    attach_session_values(entry_or_list, session) -> ...   # live value per session
    pro_hook(slug) -> callable | None          # the plugin-filled compute hook
    register_pro_evaluator(slug, fn)           # called by clawmetry-pro
"""

from __future__ import annotations

import logging
from typing import Any, Callable

log = logging.getLogger("clawmetry.evaluators")


# ── Categories + tiers (frozen strings; they land in the wire API) ──────────────

CATEGORY_QUALITY = "quality"
CATEGORY_RELIABILITY = "reliability"
CATEGORY_EFFICIENCY = "efficiency"
CATEGORY_SAFETY = "safety"
CATEGORY_AGENT = "agent"

TIER_FREE = "free"
TIER_PRO = "pro"

STATUS_LIVE = "live"            # shipped + computed today
STATUS_PARTIAL = "partial"     # computed, but heuristic / not yet content-grounded
STATUS_PRO = "pro"             # value comes from the Pro plugin; locked without it


# ── The catalogue — single source of truth ──────────────────────────────────────
#
# Each entry:
#   slug         stable id used by the API + the per-session value attach
#   name         friendly, plain-language display name (no jargon)
#   description  what it answers, in words a first-timer understands
#   category     one of the CATEGORY_* values (drives the UI chip)
#   tier         free | pro (drives the badge + the locked state)
#   status       live | partial | pro
#   computed_in  human-readable "where the number is produced" (for the UI)
#   source       MACHINE-CHECKABLE pointer the guard test re-extracts:
#                  "module:symbol"      a real importable function/constant, OR
#                  "column:sessions.x"  a real DuckDB sessions column, OR
#                  "pro:<slug>"         value filled by the clawmetry-pro plugin
#   value_field  for free/live entries: the session-row field that already
#                holds the per-session value (None = aggregate-only signal)

EVALUATOR_CATALOGUE: list[dict[str, Any]] = [
    {
        "slug": "agent-goal-accuracy",
        "name": "Did the agent finish the job?",
        "description": (
            "Labels every run as success, failed, escalated, stuck on a tool, "
            "or looping, so you can see at a glance whether your agent actually "
            "got the task done."
        ),
        "category": CATEGORY_AGENT,
        "tier": TIER_FREE,
        "status": STATUS_LIVE,
        "computed_in": "Outcome classifier, on every session",
        "source": "clawmetry.outcome_classifier:classify_session",
        "value_field": "outcome",
    },
    {
        "slug": "agent-flow-quality",
        "name": "Did the agent work cleanly?",
        "description": (
            "Trace-level checks that the agent acted, read before it wrote, its "
            "tools succeeded, it recovered from errors, and it did not loop. A "
            "clean run passes all of them."
        ),
        "category": CATEGORY_RELIABILITY,
        "tier": TIER_FREE,
        "status": STATUS_LIVE,
        "computed_in": "Reliability scorer (ClawBench-style trace checks)",
        "source": "clawmetry.sync:_reliability_score_session",
        "value_field": "reliability_score",
    },
    {
        "slug": "answer-quality",
        "name": "How good was the answer?",
        "description": (
            "An LLM judge scores each finished session from 0 to 5 against a "
            "rubric you control. The judge runs on your own API key and your "
            "transcripts never leave your machine for our cloud."
        ),
        "category": CATEGORY_QUALITY,
        "tier": TIER_FREE,
        "status": STATUS_LIVE,
        "computed_in": "Local LLM-as-judge on your own key",
        "source": "column:sessions.eval_score",
        "value_field": "eval_score",
    },
    {
        "slug": "agent-efficiency",
        "name": "Did the agent waste effort or money?",
        "description": (
            "Flags runs that ran away on steps, kept missing the prompt cache, "
            "pulled back oversized tool results, or bloated their own context. "
            "Each flag is a place you are paying for work that did not help."
        ),
        "category": CATEGORY_EFFICIENCY,
        "tier": TIER_PRO,
        "status": STATUS_PRO,
        "computed_in": "Waste-flag analyzer (Pro)",
        "source": "pro:agent-efficiency",
        "value_field": None,
    },
    {
        "slug": "agent-tool-error-detector",
        "name": "Were tool errors real or harmless?",
        "description": (
            "Separates genuine tool failures from benign noise (an empty grep, a "
            "missing optional file) so the error count reflects problems worth "
            "your attention, not background chatter."
        ),
        "category": CATEGORY_RELIABILITY,
        "tier": TIER_PRO,
        "status": STATUS_PRO,
        "computed_in": "Benign-error filter (Pro)",
        "source": "pro:agent-tool-error-detector",
        "value_field": None,
    },
    {
        "slug": "pii-detector",
        "name": "Did anything personal leak?",
        "description": (
            "Scans run content for personal data such as emails so you can catch "
            "sensitive information moving through your agent."
        ),
        "category": CATEGORY_SAFETY,
        "tier": TIER_FREE,
        "status": STATUS_LIVE,
        "computed_in": "Policy-event scan over agent content",
        "source": "dashboard:_scan_content_for_policy_events",
        "value_field": None,
    },
    {
        "slug": "secrets-detector",
        "name": "Were credentials exposed?",
        "description": (
            "Looks for API keys, tokens, and other secrets in run content so a "
            "leaked credential shows up before it becomes an incident."
        ),
        "category": CATEGORY_SAFETY,
        "tier": TIER_FREE,
        "status": STATUS_LIVE,
        "computed_in": "Policy-event scan over agent content",
        "source": "dashboard:_scan_content_for_policy_events",
        "value_field": None,
    },
    {
        "slug": "prompt-injection-detector",
        "name": "Was the agent being manipulated?",
        "description": (
            "Watches for prompt-injection patterns in run content, the attempts "
            "to hijack your agent with instructions hidden inside data it reads."
        ),
        "category": CATEGORY_SAFETY,
        "tier": TIER_FREE,
        "status": STATUS_LIVE,
        "computed_in": "Policy-event scan over agent content",
        "source": "dashboard:_scan_content_for_policy_events",
        "value_field": None,
    },
    {
        "slug": "hallucination-risk",
        "name": "How risky was this answer?",
        "description": (
            "A quick per-call risk read based on signals like sampling "
            "temperature. It is an early-warning heuristic, not a fact check. "
            "For a claim-by-claim check see Faithfulness."
        ),
        "category": CATEGORY_QUALITY,
        "tier": TIER_FREE,
        "status": STATUS_PARTIAL,
        "computed_in": "Per-call risk heuristic",
        "source": "clawmetry.risk:compute_hallucination_risk",
        "value_field": None,
    },
    {
        "slug": "faithfulness",
        "name": "Was every claim backed by the evidence?",
        "description": (
            "Breaks the agent's final reply into individual claims and checks "
            "each one against the tool results and context it actually saw, then "
            "scores how grounded the answer is and lists any claim nothing "
            "supports. Runs on your own key; your data stays on your machine."
        ),
        "category": CATEGORY_QUALITY,
        "tier": TIER_PRO,
        "status": STATUS_PRO,
        "computed_in": "Content-grounded claim verification (Pro)",
        "source": "pro:faithfulness",
        "value_field": "faithfulness_score",
    },
]


# ── Pro hook registry — clawmetry-pro fills these when present ───────────────────
#
# OSS declares the pro entries above. The clawmetry-pro plugin calls
# ``register_pro_evaluator(slug, fn)`` at load time so OSS can DEFER to the real
# compute when the plugin is installed (and the install is entitled), and show
# the locked/upgrade state otherwise. The compute itself never lives in OSS.

_PRO_HOOKS: dict[str, Callable[..., Any]] = {}


def register_pro_evaluator(slug: str, fn: Callable[..., Any]) -> None:
    """Register a Pro evaluator's compute callable for ``slug``.

    Called by clawmetry-pro at plugin load. Idempotent (later wins). Never
    raises so a bad registration can't taint the extension load.
    """
    try:
        if not slug or not callable(fn):
            return
        _PRO_HOOKS[str(slug)] = fn
        log.info("evaluators: pro hook registered for %r", slug)
    except Exception:  # pragma: no cover - defensive
        log.warning("evaluators: register_pro_evaluator(%r) failed", slug, exc_info=True)


def pro_hook(slug: str) -> Callable[..., Any] | None:
    """Return the Pro compute callable for ``slug`` if the plugin registered
    one, else ``None`` (OSS then shows the locked state)."""
    return _PRO_HOOKS.get(str(slug))


def has_pro_hook(slug: str) -> bool:
    """True when a Pro evaluator is wired up for ``slug``."""
    return str(slug) in _PRO_HOOKS


# ── Catalogue accessors ──────────────────────────────────────────────────────────


def _entry_view(entry: dict[str, Any]) -> dict[str, Any]:
    """Return the wire-safe view of one catalogue entry.

    Resolves the live ``status`` for Pro entries: if the plugin registered a
    hook (and so the value can be produced) we report ``live``; otherwise the
    entry stays ``pro`` (locked). The static catalogue never mutates.
    """
    view = {
        "slug": entry["slug"],
        "name": entry["name"],
        "description": entry["description"],
        "category": entry["category"],
        "tier": entry["tier"],
        "status": entry["status"],
        "computed_in": entry["computed_in"],
    }
    if entry["tier"] == TIER_PRO:
        view["locked"] = not has_pro_hook(entry["slug"])
        if has_pro_hook(entry["slug"]):
            view["status"] = STATUS_LIVE
    else:
        view["locked"] = False
    return view


def catalogue() -> list[dict[str, Any]]:
    """Return the named evaluator catalogue as a list of wire-safe dicts.

    Pure + cloud-safe — needs no DuckDB store, so the Evaluators surface
    renders in the hosted dashboard without a blank.
    """
    return [_entry_view(e) for e in EVALUATOR_CATALOGUE]


def category_counts(entries: list[dict[str, Any]] | None = None) -> dict[str, int]:
    """Count evaluators per category for the UI summary chips."""
    rows = entries if entries is not None else catalogue()
    out: dict[str, int] = {}
    for e in rows:
        out[e["category"]] = out.get(e["category"], 0) + 1
    return out


def catalogue_with_coverage(store: Any = None) -> dict[str, Any]:
    """Return the catalogue plus live coverage counts.

    ``coverage`` is best-effort: when a DuckDB store is reachable we attach how
    many sessions carry an outcome label and an eval score over the recent
    window. With no store (the cloud container) coverage is omitted and the
    catalogue is still returned — never a blank, never a raise.
    """
    cat = catalogue()
    payload: dict[str, Any] = {
        "evaluators": cat,
        "total": len(cat),
        "free": sum(1 for e in cat if e["tier"] == TIER_FREE),
        "pro": sum(1 for e in cat if e["tier"] == TIER_PRO),
        "live": sum(1 for e in cat if e["status"] == STATUS_LIVE),
        "categories": category_counts(cat),
        "coverage": None,
    }
    if store is None:
        return payload
    coverage: dict[str, Any] = {}
    try:
        summary = store.query_eval_summary(window_hours=24)
        if isinstance(summary, dict):
            coverage["sessions_in_window"] = int(summary.get("total") or 0)
            coverage["answer_quality_scored"] = int(summary.get("scored") or 0)
    except Exception:
        pass
    try:
        rows = store.query_outcomes(limit=2000)
        labelled = sum(1 for r in (rows or []) if r.get("outcome"))
        coverage["goal_accuracy_labelled"] = labelled
    except Exception:
        pass
    payload["coverage"] = coverage or None
    return payload


# ── Per-session live value attach (reuse existing fields; never recompute) ──────


def attach_session_values(
    target: dict[str, Any] | list[dict[str, Any]],
    session: dict[str, Any] | None,
) -> Any:
    """Attach the live per-session value to catalogue entries where one exists.

    Reuses fields ALREADY present on the session row (``outcome``,
    ``eval_score``, ``reliability_score``, ``faithfulness_score``) — it does NOT
    recompute any signal. Entries with no per-session field, or whose field is
    absent on this session, get ``value=None``. Pro entries stay locked unless
    the session row already carries the plugin-written value.

    Accepts a single entry or a list (returns the same shape) so callers can
    decorate one evaluator or the whole catalogue.
    """
    sess = session or {}

    def _one(entry: dict[str, Any]) -> dict[str, Any]:
        out = dict(entry)
        field = None
        # Find the catalogue spec for this slug to read its value_field.
        for spec in EVALUATOR_CATALOGUE:
            if spec["slug"] == entry.get("slug"):
                field = spec.get("value_field")
                break
        value = None
        if field and field in sess and sess.get(field) is not None:
            value = sess.get(field)
        out["value"] = value
        return out

    if isinstance(target, list):
        return [_one(e) for e in target]
    return _one(target)
