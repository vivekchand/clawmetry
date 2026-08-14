"""
clawmetry/quality.py — pure helpers for the Quality tab.

The Quality tab (formerly "Evals") answers ONE question in three seconds:
"Is my agent doing good work?". This module holds the plain-Python logic
that converts the numeric signals ClawMetry already computes (outcome,
reliability_score, eval_score, cost, duration) into the human-facing
grade + narrated patterns + plain-English "story" per rough run.

Design rules:
  * Zero jargon in the strings we return — this text lands in the UI.
  * Deterministic first. LLM-judge scores enrich the grade when a key is
    set, but the grade never blanks without one (see Elon-mode note in the
    2026-08-14 redesign: the deterministic signals are the product).
  * Never raise; return a well-shaped empty on any bad input so the
    endpoint stays quiet on a fresh install.

Public surface:
    grade_for(score: float) -> str        # 0.0..1.0 -> "A" | "B" | ... | "F"
    compute_report_card(rows) -> dict     # sessions rows -> full tab payload
    story_for(session_row) -> str         # plain-English one-liner
"""

from __future__ import annotations

from typing import Any

# Outcome enum → the per-session score contribution.
# success  = full credit; escalated (human took over) = partial;
# every failure mode is zero — the operator's job is to fix the top-N.
# Unknown / NULL outcomes are excluded from the average (bootstrapping
# empty tabs return a grade based on scored rows only).
_OUTCOME_SCORE: dict[str, float] = {
    "success":         1.0,
    "escalated":       0.6,
    "failed":          0.0,
    "tool_call_stuck": 0.0,
    "cognitive_loop":  0.0,
    "stuck":           0.0,
    "looping":         0.0,
    "budget_exceeded": 0.0,
}

# Outcome enum → the pattern label users see in "What went wrong".
# Plain English, present-tense verb, no ML jargon.
_PATTERN_LABEL: dict[str, str] = {
    "tool_call_stuck": "Agent got stuck retrying the same tool",
    "stuck":           "Agent got stuck retrying the same tool",
    "cognitive_loop":  "Looped in place, editing the same file over and over",
    "looping":         "Looped in place, editing the same file over and over",
    "failed":          "Gave up mid-task",
    "budget_exceeded": "Ran past the token budget and truncated",
    "escalated":       "Handed the task back for a human to finish",
}

# What we say per-session in the "rough runs" list. Deliberately narrative,
# with a "then <thing that happened>" clause so the row reads as a mini
# incident report rather than a status pill.
_STORY_BY_OUTCOME: dict[str, str] = {
    "tool_call_stuck": "Stuck retrying the same tool, then gave up.",
    "stuck":           "Stuck retrying the same tool, then gave up.",
    "cognitive_loop":  "Looped in place — kept editing the same file with no forward progress.",
    "looping":         "Looped in place — kept editing the same file with no forward progress.",
    "failed":          "Gave up mid-task.",
    "budget_exceeded": "Ran past the token budget and truncated the answer.",
    "escalated":       "Couldn't finish and asked a human to take over.",
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


def _session_score(row: dict[str, Any]) -> float | None:
    """Blend outcome (deterministic, always present after classification)
    with judge score (0..5, only when the user set a key).

    The blend is intentional: on a fresh install with no judge key the
    grade still reflects real work (from outcome alone). Adding a judge
    key later shifts the grade smoothly without a blank-then-populate flash.
    """
    outcome = (row.get("outcome") or "").strip()
    o_score = _OUTCOME_SCORE.get(outcome)
    judge = row.get("eval_score")
    j_score = None
    if judge is not None:
        try:
            j_score = max(0.0, min(1.0, float(judge) / 5.0))
        except (TypeError, ValueError):
            j_score = None
    if o_score is None and j_score is None:
        return None
    if o_score is None:
        return j_score
    if j_score is None:
        return o_score
    # 60/40 in favor of outcome. The outcome signal is more objective
    # ("did the task finish?"); the judge is a subjective quality read
    # that shouldn't dominate the operational answer.
    return 0.6 * o_score + 0.4 * j_score


def story_for(row: dict[str, Any]) -> str:
    """Plain-English one-liner for a rough run. Never blank — falls back
    to the judge's reason, then a generic 'ended without a clean answer'."""
    outcome = (row.get("outcome") or "").strip()
    if outcome in _STORY_BY_OUTCOME:
        return _STORY_BY_OUTCOME[outcome]
    reason = (row.get("eval_reason") or "").strip()
    if reason:
        # Truncate to a sentence-length preview so the row stays scannable.
        r = reason.split(". ")[0].rstrip(".") + "."
        return r if len(r) <= 140 else r[:137] + "…"
    return "Ended without a clean answer."


def _title_or_id(row: dict[str, Any]) -> str:
    """The user-facing name of a session: the title if we have one, else a
    truncated session_id. Never a bare hash — that was the vaporbox smell."""
    title = (row.get("title") or "").strip()
    if title:
        return title if len(title) <= 60 else title[:57] + "…"
    sid = str(row.get("session_id") or "")
    return sid if len(sid) <= 24 else sid[:21] + "…"


def _fmt_cost(cost: float | None) -> str:
    if cost is None:
        return "$0.00"
    c = float(cost)
    if c >= 0.01:
        return f"${c:.2f}"
    if c > 0:
        return "<$0.01"
    return "$0.00"


def _fmt_minutes(seconds: float | None) -> str:
    if seconds is None or seconds <= 0:
        return "—"
    s = int(seconds)
    if s < 60:
        return f"{s} sec"
    m = s // 60
    if m < 60:
        return f"{m} min"
    h = m // 60
    return f"{h}h {m % 60}m"


def compute_report_card(
    rows: list[dict[str, Any]] | None,
    *,
    max_patterns: int = 6,
    max_rough_runs: int = 5,
    prior_grade_score: float | None = None,
) -> dict[str, Any]:
    """Turn a window of session rows into the wire payload the Quality tab
    renders. Never raises. Empty rows → an honest "nothing to grade yet"
    empty payload the UI knows how to display.

    ``prior_grade_score`` (0..1) is optional; when passed the payload
    includes a ``vs_prior`` field (``"up"|"down"|"same"``) so the UI can
    render "Down from a C+ last week."
    """
    rows = rows or []

    scored = [(r, _session_score(r)) for r in rows]
    scored = [(r, s) for (r, s) in scored if s is not None]

    total = len(rows)
    graded = len(scored)

    if graded == 0:
        return {
            "grade":           "—",
            "grade_score":     None,
            "total_runs":      total,
            "graded_runs":     0,
            "success_runs":    0,
            "rough_runs_n":    0,
            "rough_cost":      "$0.00",
            "rough_seconds":   0,
            "patterns":        [],
            "rough_runs":      [],
            "week":            [],
            "vs_prior":        None,
            "headline":        "Nothing to grade yet.",
            "subline":         (
                "Your agents haven't finished a task in this window. "
                "Send Claude Code or OpenClaw a task and come back — "
                "the first grade lands the moment a session ends."
            ),
        }

    avg_score = sum(s for _, s in scored) / graded
    grade = grade_for(avg_score)

    good = [r for (r, s) in scored if s >= 0.75]
    rough = [r for (r, s) in scored if s < 0.60]

    # Sort rough runs by (lowest score, highest cost) so the most-expensive
    # failures surface first — cost is the second sort key so a "cheap"
    # failure doesn't beat an "expensive" one at the same score.
    rough_sorted = sorted(
        [(r, s) for (r, s) in scored if s < 0.60],
        key=lambda pair: (pair[1], -float(pair[0].get("cost_usd") or 0)),
    )

    # Patterns: group rough runs by outcome, sum cost + avg duration.
    # Only shows named patterns (unknown outcomes drop into a rollup).
    by_pattern: dict[str, dict[str, Any]] = {}
    for r in rough:
        outcome = (r.get("outcome") or "").strip()
        label = _PATTERN_LABEL.get(outcome, "Ended without a clean answer")
        p = by_pattern.setdefault(label, {
            "label":   label,
            "count":   0,
            "cost":    0.0,
            "seconds": 0.0,
        })
        p["count"] += 1
        p["cost"] += float(r.get("cost_usd") or 0)
        # Session duration heuristic: (ended_at - started_at) if both, else 0.
        dur = 0.0
        try:
            from datetime import datetime
            for fmt in ("%Y-%m-%dT%H:%M:%S.%f", "%Y-%m-%dT%H:%M:%S"):
                try:
                    s = datetime.fromisoformat((r.get("started_at") or "").replace("Z", "+00:00"))
                    e = datetime.fromisoformat((r.get("ended_at") or r.get("last_active_at") or "").replace("Z", "+00:00"))
                    dur = max(0.0, (e - s).total_seconds())
                    break
                except (ValueError, TypeError, AttributeError):
                    pass
        except Exception:
            dur = 0.0
        p["seconds"] += dur

    patterns = sorted(by_pattern.values(), key=lambda p: -p["cost"])[:max_patterns]
    for p in patterns:
        n = max(1, p["count"])
        p["avg_minutes"] = _fmt_minutes(p["seconds"] / n)
        p["cost_display"] = _fmt_cost(p["cost"])
        # Drop internal accumulators the UI doesn't need.
        p.pop("seconds", None)
        p.pop("cost",    None)

    rough_total_cost = sum(float(r.get("cost_usd") or 0) for r in rough)
    rough_total_seconds = sum(p_seconds for p_seconds in
                              (by_pattern[k].get("_raw_seconds", 0) for k in by_pattern)) or 0

    # Recompute rough_total_seconds cleanly from the rough list (the loop
    # above popped the accumulator into avg_minutes already).
    rough_total_seconds = 0.0
    try:
        from datetime import datetime
        for r in rough:
            try:
                s = datetime.fromisoformat((r.get("started_at") or "").replace("Z", "+00:00"))
                e = datetime.fromisoformat((r.get("ended_at") or r.get("last_active_at") or "").replace("Z", "+00:00"))
                rough_total_seconds += max(0.0, (e - s).total_seconds())
            except (ValueError, TypeError, AttributeError):
                pass
    except Exception:
        pass

    rough_runs_out: list[dict[str, Any]] = []
    for r, s in rough_sorted[:max_rough_runs]:
        rough_runs_out.append({
            "session_id":     r.get("session_id"),
            "agent_type":     r.get("agent_type") or "",
            "title":          _title_or_id(r),
            "when":           r.get("last_active_at") or r.get("ended_at") or r.get("started_at"),
            "story":          story_for(r),
            "cost_display":   _fmt_cost(r.get("cost_usd")),
            "score":          round(s, 2),
        })

    vs_prior = None
    if prior_grade_score is not None:
        try:
            p = float(prior_grade_score)
            delta = avg_score - p
            if delta > 0.03:
                vs_prior = "up"
            elif delta < -0.03:
                vs_prior = "down"
            else:
                vs_prior = "same"
        except (TypeError, ValueError):
            vs_prior = None

    # Headline / subline: one plain sentence + a supporting one.
    if len(good) == total:
        headline = "Your agents did clean work this window."
    elif len(rough) == 0:
        headline = "Your agents did solid work this window."
    elif grade == "F":
        headline = "Your agents struggled this window."
    else:
        headline = "Your agents did good work this window."
    n_good = len(good)
    n_rough = len(rough)
    cost_str = _fmt_cost(rough_total_cost)
    time_str = _fmt_minutes(rough_total_seconds)
    if n_rough == 0:
        subline = f"{n_good} tasks done well. No rough ones."
    else:
        subline = (
            f"{n_good} tasks done well. {n_rough} rough "
            f"{'one' if n_rough == 1 else 'ones'} cost you {cost_str}"
            + (f" and about {time_str}." if time_str != "—" else ".")
        )

    return {
        "grade":         grade,
        "grade_score":   round(avg_score, 4),
        "total_runs":    total,
        "graded_runs":   graded,
        "success_runs":  n_good,
        "rough_runs_n":  n_rough,
        "rough_cost":    cost_str,
        "rough_seconds": int(rough_total_seconds),
        "patterns":      patterns,
        "rough_runs":    rough_runs_out,
        "week":           [],  # populated by the endpoint (per-day buckets)
        "vs_prior":       vs_prior,
        "headline":       headline,
        "subline":        subline,
    }
