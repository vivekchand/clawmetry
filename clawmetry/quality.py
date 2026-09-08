"""
clawmetry/quality.py — the Quality tab's plain-English layer.

Turns evidence-bearing verdicts (``clawmetry.quality_signals``) into the
report card the tab renders: a grade, a headline, ranked failure patterns, and
per-session stories.

Rewritten 2026-08-15. The previous version scored sessions from a single
``outcome`` enum whose failure branch was a text-similarity heuristic blind to
most runtimes' tool calls, and whose success branch was a fallthrough default
("when uncertain we say success"). That produced a confident letter grade over
what was effectively one unreliable bit.

Three rules now hold, and each one is load-bearing:

  1. **Only measurable sessions are graded.** A session with too little signal
     is excluded and COUNTED OUT LOUD, never silently passed. In the audit
     window 18 of 62 sessions were pure research chats with no tool calls;
     every one had been collecting a free "success".
  2. **Rough means evidence exists.** A session is rough because a verdict
     carrying exhibits says so — not because nothing matched a success test.
  3. **No jargon reaches the user.** Verdict names are internal; the strings
     here are what a person reads.
"""

from __future__ import annotations

from typing import Any

# Verdict → the "what went wrong" pattern label, and the per-session story.
# Plain English, present tense, no ML vocabulary.
_VERDICT_COPY: dict[str, dict[str, str]] = {
    "tool_failures": {
        "label": "Tools kept failing",
        "story": "Its tools failed far more than usual for this runtime.",
    },
    "tool_thrash": {
        "label": "Ran the same command over and over",
        "story": "Retried the identical call again and again, and it kept failing.",
    },
    "no_forward_progress": {
        "label": "Edited the same file without ever checking it",
        "story": "Kept editing one file and never ran anything to see if it worked.",
    },
    "hard_failure": {
        "label": "Ended on an error",
        "story": "Stopped on an error it never recovered from.",
    },
}

# How much each verdict costs a session's score. A session lands at
# 1.0 minus the worst verdict's weight, scaled by that verdict's confidence —
# so a low-confidence finding dents the grade instead of tanking it.
_VERDICT_WEIGHT: dict[str, float] = {
    "hard_failure":        1.0,
    "tool_thrash":         0.8,
    "tool_failures":       0.7,
    "no_forward_progress": 0.6,
}


def grade_for(score: float | None) -> str:
    """0.0..1.0 → A / B / C / D / F. None or invalid → '—' (no grade yet)."""
    if score is None:
        return "—"
    try:
        s = float(score)
    except (TypeError, ValueError):
        return "—"
    if s >= 0.90:
        return "A"
    if s >= 0.75:
        return "B"
    if s >= 0.60:
        return "C"
    if s >= 0.40:
        return "D"
    return "F"


def session_score(assessment: dict[str, Any] | None) -> float | None:
    """One session's 0..1 score, or None when it is not gradeable.

    None is a real answer, not a failure. It means "we could not measure this
    one" and the caller must exclude it from the average rather than treat it
    as a pass — the exact substitution that made the old grade meaningless.
    """
    if not assessment or not assessment.get("measurable"):
        return None
    verdicts = assessment.get("verdicts") or []
    if not verdicts:
        return 1.0
    worst = 0.0
    for v in verdicts:
        w = _VERDICT_WEIGHT.get(v.get("verdict") or "", 0.5)
        conf = float(v.get("confidence") or 0.5)
        worst = max(worst, w * conf)
    return max(0.0, min(1.0, 1.0 - worst))


def story_for(assessment: dict[str, Any] | None) -> str:
    """Plain-English one-liner for a rough run, taken from its top verdict."""
    verdicts = (assessment or {}).get("verdicts") or []
    if not verdicts:
        return "Nothing went obviously wrong."
    name = verdicts[0].get("verdict") or ""
    return _VERDICT_COPY.get(name, {}).get(
        "story", "Ended without a clean result.")


def _title_or_id(row: dict[str, Any]) -> str:
    """The user-facing name of a session. Never a bare hash."""
    title = (row.get("title") or "").strip()
    if title:
        return title if len(title) <= 60 else title[:57] + "…"
    sid = str(row.get("session_id") or "")
    if ":" in sid:
        sid = sid.split(":", 1)[1]
    return sid if len(sid) <= 24 else sid[:21] + "…"


def _fmt_cost(cost: float | None) -> str:
    if cost is None:
        return "$0.00"
    try:
        c = float(cost)
    except (TypeError, ValueError):
        return "$0.00"
    if c >= 0.01:
        return f"${c:.2f}"
    return "<$0.01" if c > 0 else "$0.00"


def compute_report_card(
    rows: list[dict[str, Any]] | None,
    assessments: dict[str, dict[str, Any]] | None,
    *,
    prior_rows: list[dict[str, Any]] | None = None,
    prior_assessments: dict[str, dict[str, Any]] | None = None,
    max_patterns: int = 6,
    max_rough_runs: int = 5,
) -> dict[str, Any]:
    """Session rows + their assessments → the wire payload the tab renders.

    Never raises. Empty input yields an honest "nothing to grade yet".
    """
    rows = rows or []
    assessments = assessments or {}

    scored: list[tuple[dict, dict, float]] = []
    unmeasured: list[tuple[dict, dict]] = []
    for r in rows:
        a = assessments.get(str(r.get("session_id") or "")) or {}
        s = session_score(a)
        if s is None:
            unmeasured.append((r, a))
        else:
            scored.append((r, a, s))

    total = len(rows)
    graded = len(scored)

    if graded == 0:
        return {
            "grade": "—", "grade_score": None,
            "total_runs": total, "graded_runs": 0, "success_runs": 0,
            "unmeasured_runs": len(unmeasured),
            "rough_runs_n": 0, "rough_cost": "$0.00",
            "patterns": [], "rough_runs": [], "week": [], "vs_prior": None,
            "headline": "Nothing to grade yet.",
            "subline": (
                "No session in this window produced enough signal to judge. "
                "Run a task that uses tools and come back — the first grade "
                "lands when one finishes."
            ),
        }

    # Cost-weighted, not session-counted. A plain mean lets thirty cheap
    # one-shot chats outvote the $82 run that spun on one file for twelve
    # edits, which is exactly backwards from what the operator cares about —
    # and it is how a window with $171 of rough runs was scoring an A.
    # The floor keeps zero-cost sessions counting for something so a free
    # runtime is not silently ungraded.
    _FLOOR = 0.05
    weighted, weights = 0.0, 0.0
    for r, _a, s in scored:
        try:
            w = max(_FLOOR, float(r.get("cost_usd") or 0))
        except (TypeError, ValueError):
            w = _FLOOR
        weighted += s * w
        weights += w
    avg_score = (weighted / weights) if weights else (
        sum(s for _, _, s in scored) / graded)
    grade = grade_for(avg_score)

    clean = [(r, a) for (r, a, s) in scored if not (a.get("verdicts") or [])]
    rough = [(r, a, s) for (r, a, s) in scored if (a.get("verdicts") or [])]

    # Rank rough runs by cost — the operator's real priority is what the
    # failure cost them, not how confident we are about it.
    rough_sorted = sorted(
        rough, key=lambda t: -float(t[0].get("cost_usd") or 0))

    by_pattern: dict[str, dict[str, Any]] = {}
    for r, a, _s in rough:
        top = (a.get("verdicts") or [{}])[0]
        name = top.get("verdict") or ""
        label = _VERDICT_COPY.get(name, {}).get(
            "label", "Ended without a clean result")
        p = by_pattern.setdefault(label, {
            "label": label, "verdict": name, "count": 0, "cost": 0.0,
        })
        p["count"] += 1
        try:
            p["cost"] += float(r.get("cost_usd") or 0)
        except (TypeError, ValueError):
            pass

    patterns = sorted(by_pattern.values(), key=lambda p: -p["cost"])[:max_patterns]
    for p in patterns:
        p["cost_display"] = _fmt_cost(p["cost"])
        p.pop("cost", None)

    rough_total_cost = 0.0
    for r, _a, _s in rough:
        try:
            rough_total_cost += float(r.get("cost_usd") or 0)
        except (TypeError, ValueError):
            pass

    rough_runs_out: list[dict[str, Any]] = []
    for r, a, s in rough_sorted[:max_rough_runs]:
        verdicts = a.get("verdicts") or []
        rough_runs_out.append({
            "session_id":   r.get("session_id"),
            "runtime":      a.get("runtime") or r.get("runtime") or "",
            "title":        _title_or_id(r),
            "when":         (r.get("last_active_at") or r.get("ended_at")
                             or r.get("started_at")),
            "story":        story_for(a),
            "cost_display": _fmt_cost(r.get("cost_usd")),
            "score":        round(s, 2),
            # The whole point: the claim ships with its evidence attached.
            "verdicts":     verdicts,
        })

    vs_prior = None
    prior_avg = _avg_score(prior_rows, prior_assessments)
    if prior_avg is not None:
        delta = avg_score - prior_avg
        vs_prior = "up" if delta > 0.03 else ("down" if delta < -0.03 else "same")

    n_clean, n_rough = len(clean), len(rough)
    total_cost = 0.0
    for r, _a, _s in scored:
        try:
            total_cost += float(r.get("cost_usd") or 0)
        except (TypeError, ValueError):
            pass
    rough_share = (rough_total_cost / total_cost) if total_cost > 0 else 0.0

    # The headline reads the money, not just the letter. "Did good work" over
    # a window where a fifth of the spend went into rough runs is the kind of
    # reassurance that makes a user stop believing the whole tab.
    if n_rough == 0:
        headline = "Your agents did clean work this window."
    elif grade in ("D", "F"):
        headline = "Your agents struggled this window."
    elif rough_share >= 0.15:
        headline = "Good work overall, with some expensive exceptions."
    else:
        headline = "Your agents did good work this window."

    cost_str = _fmt_cost(rough_total_cost)
    if n_rough == 0:
        subline = f"{n_clean} tasks came back clean. Nothing rough."
    else:
        subline = (
            f"{n_clean} tasks came back clean. {n_rough} rough "
            f"{'one' if n_rough == 1 else 'ones'} cost you {cost_str}."
        )
    # Two different reasons a session is excluded, and they are not
    # interchangeable. "Too little activity to judge" is a fact about the
    # session; "not graded yet" is a fact about us. Reporting the second as
    # the first tells the user their work was too thin when the truth is the
    # collector hasn't caught up — the same species of wrong-but-reassuring
    # copy this rebuild exists to remove.
    thin = [1 for (_r, a) in unmeasured
            if "too little activity" in str(a.get("reason") or "").lower()]
    pending = len(unmeasured) - len(thin)
    if thin:
        subline += (
            f" {len(thin)} more had too little activity to judge, "
            "so they are left out of the grade."
        )
    if pending:
        subline += (
            f" {pending} {'is' if pending == 1 else 'are'} still being "
            "graded and will appear shortly."
        )

    return {
        "grade":            grade,
        "grade_score":      round(avg_score, 4),
        "total_runs":       total,
        "graded_runs":      graded,
        "success_runs":     n_clean,
        "unmeasured_runs":  len(unmeasured),
        "rough_runs_n":     n_rough,
        "rough_cost":       cost_str,
        "patterns":         patterns,
        "rough_runs":       rough_runs_out,
        "week":             [],
        "vs_prior":         vs_prior,
        "headline":         headline,
        "subline":          subline,
    }


def _avg_score(rows, assessments) -> float | None:
    """Mean score over gradeable sessions only. None when none are."""
    if not rows:
        return None
    assessments = assessments or {}
    vals = []
    for r in rows:
        s = session_score(assessments.get(str(r.get("session_id") or "")) or {})
        if s is not None:
            vals.append(s)
    return sum(vals) / len(vals) if vals else None
