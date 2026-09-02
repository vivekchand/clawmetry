"""Harness Engineering bench: pure scoring math, no I/O.

Computes, per runtime ("harness"), the honest engineering scorecard the
Bench tab renders: dollars-per-finished-job ($/done), a plain-word verdict
stamp, five dimension marks, and the coverage state that keeps a blind
harness from ranking.

Contracts (Blueprint "Harness Benchmarks & Comparison"):
- $/done = window spend of MEASURABLE sessions (failed runs included) divided
  by measurable sessions that ended in success. Sessions whose quality signals
  are not measurable are excluded from BOTH sides and reported in coverage.
- Below BENCH_MIN_SESSIONS measurable sessions no dollar figure is produced.
- A harness with zero measurable sessions is `cant_see` and can never rank.
- Weighting happens only within a runtime; cross-runtime standings are never
  weighted by absolute spend.
- Every mark carries its coverage state (observed / supported_none_seen /
  unsupported) and the source that produced it; nothing is a fabricated zero.

Like clawmetry/quality.py and clawmetry/efficiency.py this module is pure so
tests can drive it with fixture rows; routes/bench.py owns all store access.
"""

from __future__ import annotations

import random
from typing import Any

# Minimum measurable sessions before a $/done figure is printed. Matches the
# quality-thresholds calibration floor so "enough data to judge" means the
# same thing across the product.
BENCH_MIN_SESSIONS = 12

# Failed-spend share at or above which a priced harness is stamped burning.
BURNING_FAILED_SPEND_SHARE = 0.35

# A priced harness costing at least this multiple of the cheapest priced
# harness is stamped burning even with a modest failed-spend share.
BURNING_COST_MULTIPLE = 2.0

_BOOTSTRAP_ROUNDS = 200
_BOOTSTRAP_SEED = 0xBE7C

STAMP_EARNING = "earning"
STAMP_BURNING = "burning"
STAMP_COASTING = "coasting"
STAMP_CANT_SEE = "cant_see"

STATE_OBSERVED = "observed"
STATE_NONE_SEEN = "supported_none_seen"
STATE_UNSUPPORTED = "unsupported"

MARK_STRONG = "strong"
MARK_WEAK = "weak"
MARK_UNSEEN = "unseen"

# The five dimensions, in display order. Keys are stable wire ids.
DIMENSIONS = ("context", "model_use", "subagents", "delegation", "completion")


def _num(v: Any, default: float = 0.0) -> float:
    try:
        f = float(v)
    except (TypeError, ValueError):
        return default
    if f != f or f in (float("inf"), float("-inf")):
        return default
    return f


def _session_features(row: dict) -> dict[str, Any]:
    """Extract the per-session facts the bench needs from a
    query_quality_sessions row. Never raises."""
    if not isinstance(row, dict):
        row = {}
    meta = row.get("metadata")
    if not isinstance(meta, dict):
        meta = {}
    quality = meta.get("quality")
    if not isinstance(quality, dict):
        quality = {}
    measurable = bool(quality.get("measurable"))
    verdicts = quality.get("verdicts")
    rough = False
    if isinstance(verdicts, list):
        rough = any(
            isinstance(v, dict) and v.get("severity") == "rough" for v in verdicts
        )
    outcome = row.get("outcome") or ""
    return {
        "session_id": row.get("session_id") or "",
        "cost_usd": max(0.0, _num(row.get("cost_usd"))),
        "tokens": max(0.0, _num(row.get("total_tokens"))),
        "outcome": outcome,
        "measurable": measurable,
        "rough": rough,
        "done": measurable and outcome == "success",
    }


def _bootstrap_band(costs: list[float], dones: list[bool]) -> tuple[float, float] | None:
    """10th..90th percentile band for $/done via a seeded bootstrap over
    sessions. Deterministic so the UI does not flicker between loads."""
    n = len(costs)
    if n == 0:
        return None
    rng = random.Random(_BOOTSTRAP_SEED + n)
    samples: list[float] = []
    for _ in range(_BOOTSTRAP_ROUNDS):
        spend = 0.0
        done = 0
        for _ in range(n):
            i = rng.randrange(n)
            spend += costs[i]
            if dones[i]:
                done += 1
        if done > 0:
            samples.append(spend / done)
    if len(samples) < _BOOTSTRAP_ROUNDS // 2:
        # Resamples too often contained zero successes; a band from the
        # remainder would understate the uncertainty.
        return None
    samples.sort()
    lo = samples[int(len(samples) * 0.10)]
    hi = samples[min(len(samples) - 1, int(len(samples) * 0.90))]
    return (round(lo, 2), round(hi, 2))


def _mark(verdict: str, state: str, source: str, note: str = "") -> dict[str, Any]:
    out = {"verdict": verdict, "state": state, "source": source}
    if note:
        out["note"] = note
    return out


def _completion_mark(feats: list[dict]) -> dict[str, Any]:
    measurable = [f for f in feats if f["measurable"]]
    if not measurable:
        return _mark(MARK_UNSEEN, STATE_UNSUPPORTED, "quality_signals",
                     "completion signals are not measurable for this harness")
    finished = [f for f in measurable if f["outcome"] not in ("ongoing", "")]
    if not finished:
        return _mark(MARK_UNSEEN, STATE_NONE_SEEN, "outcome_classifier",
                     "no finished sessions in the window yet")
    done = sum(1 for f in finished if f["done"])
    rate = done / len(finished)
    return _mark(MARK_STRONG if rate >= 0.8 else MARK_WEAK,
                 STATE_OBSERVED, "outcome_classifier")


def _context_mark(eff_scope: dict | None) -> dict[str, Any]:
    if not isinstance(eff_scope, dict) or eff_scope.get("insufficient_data"):
        return _mark(MARK_UNSEEN, STATE_NONE_SEEN, "efficiency_rollup",
                     "not enough model calls recorded to judge context use")
    score = eff_scope.get("score")
    if score is None:
        return _mark(MARK_UNSEEN, STATE_NONE_SEEN, "efficiency_rollup")
    return _mark(MARK_STRONG if _num(score) >= 70 else MARK_WEAK,
                 STATE_OBSERVED, "efficiency_rollup")


def _model_use_mark(eff_scope: dict | None) -> dict[str, Any]:
    if not isinstance(eff_scope, dict) or eff_scope.get("insufficient_data"):
        return _mark(MARK_UNSEEN, STATE_NONE_SEEN, "efficiency_rollup",
                     "not enough model calls recorded to judge model choice")
    actions = eff_scope.get("actions")
    downgrade = None
    if isinstance(actions, list):
        for a in actions:
            if isinstance(a, dict) and a.get("id") == "model_downgrade":
                downgrade = a
                break
    if downgrade is not None and _num(downgrade.get("savings_monthly_usd")) > 0:
        return _mark(MARK_WEAK, STATE_OBSERVED, "efficiency_rollup",
                     "an expensive model is doing work a cheaper one could")
    return _mark(MARK_STRONG, STATE_OBSERVED, "efficiency_rollup")


def _subagent_mark(stats: dict | None) -> dict[str, Any]:
    if not isinstance(stats, dict):
        return _mark(MARK_UNSEEN, STATE_UNSUPPORTED, "subagents",
                     "this harness does not record sub-agent spawns")
    spawned = int(_num(stats.get("spawned")))
    if spawned <= 0:
        return _mark(MARK_UNSEEN, STATE_NONE_SEEN, "subagents",
                     "no sub-agent spawns observed in the window")
    completed = int(_num(stats.get("completed")))
    orphaned = int(_num(stats.get("orphaned")))
    finished = completed + int(_num(stats.get("failed")))
    if finished <= 0:
        return _mark(MARK_UNSEEN, STATE_NONE_SEEN, "subagents",
                     "sub-agents observed but none finished yet")
    rate = completed / finished
    verdict = MARK_STRONG if rate >= 0.8 and orphaned == 0 else MARK_WEAK
    return _mark(verdict, STATE_OBSERVED, "subagents")


def _delegation_mark(stats: dict | None) -> dict[str, Any]:
    # Deferred/scheduled hand-offs are recorded per harness only where the
    # subagent stream carries workflow/cron kinds today. Everything else is
    # honestly unseen rather than guessed.
    if not isinstance(stats, dict):
        return _mark(MARK_UNSEEN, STATE_UNSUPPORTED, "run_ledger",
                     "this harness does not record deferred or scheduled work")
    deferred = int(_num(stats.get("deferred")))
    if deferred <= 0:
        return _mark(MARK_UNSEEN, STATE_NONE_SEEN, "run_ledger",
                     "no deferred or scheduled hand-offs observed in the window")
    return _mark(MARK_STRONG, STATE_OBSERVED, "run_ledger")


def build_runtime_scope(
    rows: list[dict] | None,
    *,
    runtime: str,
    eff_scope: dict | None = None,
    subagent_stats: dict | None = None,
    min_sessions: int = BENCH_MIN_SESSIONS,
) -> dict[str, Any]:
    """Score one runtime from its query_quality_sessions rows."""
    feats = [_session_features(r) for r in (rows or [])]
    total_spend = round(sum(f["cost_usd"] for f in feats), 2)
    measurable = [f for f in feats if f["measurable"]]
    m_spend = sum(f["cost_usd"] for f in measurable)
    done_n = sum(1 for f in measurable if f["done"])
    failed_spend = sum(f["cost_usd"] for f in measurable if not f["done"]
                       and f["outcome"] not in ("ongoing", ""))

    # An install whose daemon predates outcome reporting returns rows with
    # no outcome at all; that is "outcomes unavailable", not "nothing ever
    # finished", and the two must not share a message (no fabricated zeros).
    has_outcomes = any(f["outcome"] for f in measurable)
    dollars_per_done: dict[str, Any] = {
        "value": None,
        "band": None,
        "n_measurable": len(measurable),
        "n_done": done_n,
        "basis": "measurable_sessions",
    }
    if len(measurable) >= min_sessions and done_n > 0:
        dollars_per_done["value"] = round(m_spend / done_n, 2)
        dollars_per_done["band"] = _bootstrap_band(
            [f["cost_usd"] for f in measurable],
            [f["done"] for f in measurable],
        )
    elif len(measurable) >= min_sessions:
        dollars_per_done["basis"] = (
            "no_success_outcomes" if has_outcomes else "outcomes_unavailable")
    failed_spend_share = round(failed_spend / m_spend, 3) if m_spend > 0 else None

    marks = {
        "context": _context_mark(eff_scope),
        "model_use": _model_use_mark(eff_scope),
        "subagents": _subagent_mark(subagent_stats),
        "delegation": _delegation_mark(subagent_stats),
        "completion": _completion_mark(feats),
    }

    return {
        "runtime": runtime,
        "sessions": len(feats),
        "measurable_sessions": len(measurable),
        "spend_usd": total_spend,
        "dollars_per_done": dollars_per_done,
        "failed_spend_share": failed_spend_share,
        "marks": marks,
        "coverage": {
            "state": (STATE_OBSERVED if measurable
                      else (STATE_NONE_SEEN if feats else STATE_UNSUPPORTED)),
            "unmeasured_sessions": len(feats) - len(measurable),
        },
        # Stamp is assigned in build_bench, where cohort context exists.
        "stamp": None,
        "rankable": dollars_per_done["value"] is not None,
    }


def _assign_stamps(scopes: dict[str, dict]) -> None:
    priced = [s["dollars_per_done"]["value"] for s in scopes.values()
              if s["dollars_per_done"]["value"] is not None]
    cheapest = min(priced) if priced else None
    for s in scopes.values():
        if s["measurable_sessions"] == 0:
            s["stamp"] = STAMP_CANT_SEE
            s["stamp_reason"] = "completion is not verifiable from what this harness records"
            continue
        value = s["dollars_per_done"]["value"]
        if value is None:
            basis = s["dollars_per_done"].get("basis")
            s["stamp"] = STAMP_COASTING
            if basis == "outcomes_unavailable":
                s["stamp_reason"] = ("outcome records are not flowing yet; "
                                     "they arrive with the daemon's next update")
            elif basis == "no_success_outcomes":
                s["stamp_reason"] = "no completed jobs recorded in the window"
            else:
                s["stamp_reason"] = (
                    "only %d measurable runs; needs %d to price a job"
                    % (s["measurable_sessions"], BENCH_MIN_SESSIONS)
                )
            continue
        share = s["failed_spend_share"] or 0.0
        expensive = (
            cheapest is not None and cheapest > 0 and len(priced) >= 2
            and value >= BURNING_COST_MULTIPLE * cheapest
        )
        if share >= BURNING_FAILED_SPEND_SHARE or expensive:
            s["stamp"] = STAMP_BURNING
            s["stamp_reason"] = (
                "%d%% of its spend went into runs that produced nothing"
                % round(share * 100)
                if share >= BURNING_FAILED_SPEND_SHARE
                else "costs %.1fx the cheapest harness on the bench"
                % (value / cheapest)
            )
        else:
            s["stamp"] = STAMP_EARNING
            s["stamp_reason"] = "finishing jobs at a healthy price"


def build_bench(
    sessions_by_runtime: dict[str, list[dict]] | None,
    *,
    efficiency_by_runtime: dict[str, dict] | None = None,
    subagent_stats_by_runtime: dict[str, dict] | None = None,
    days: int = 30,
    min_sessions: int = BENCH_MIN_SESSIONS,
) -> dict[str, Any]:
    """The one cross-runtime fan-out payload behind GET /api/bench."""
    eff = efficiency_by_runtime or {}
    sub = subagent_stats_by_runtime or {}
    scopes: dict[str, dict] = {}
    try:
        for rt, rows in (sessions_by_runtime or {}).items():
            scopes[rt] = build_runtime_scope(
                rows, runtime=rt, eff_scope=eff.get(rt),
                subagent_stats=sub.get(rt), min_sessions=min_sessions,
            )
        _assign_stamps(scopes)
    except Exception:
        scopes = {}
    ranked = sorted(
        (s["runtime"] for s in scopes.values() if s["rankable"]),
        key=lambda rt: scopes[rt]["dollars_per_done"]["value"],
    )
    unranked = sorted(rt for rt in scopes if not scopes[rt]["rankable"])
    return {
        "schema": 1,
        "window_days": days,
        "min_sessions": min_sessions,
        "byRuntime": scopes,
        "ranked": ranked,
        "unranked": unranked,
    }


# ---------------------------------------------------------------------------
# Context curves (REQ-HB-007): shape query_context_economics output into
# per-session curves and per-runtime typical curves.
# ---------------------------------------------------------------------------

def build_context_curves(econ: dict | None, *, max_sessions: int = 6) -> dict[str, Any]:
    """Group utilization points into per-session curves with compaction and
    overflow markers attached. Input is query_context_economics output."""
    econ = econ if isinstance(econ, dict) else {}
    points = econ.get("utilization") or []
    compactions = econ.get("compactions") or []
    overflow = set(econ.get("overflow_sessions") or [])

    by_sid: dict[str, list[dict]] = {}
    for p in points:
        if not isinstance(p, dict):
            continue
        sid = p.get("session_id") or ""
        if not sid:
            continue
        by_sid.setdefault(sid, []).append(p)

    comp_by_sid: dict[str, list[dict]] = {}
    for c in compactions:
        if not isinstance(c, dict):
            continue
        sid = c.get("session_id") or ""
        comp_by_sid.setdefault(sid, []).append({
            "ts": c.get("ts"),
            "trigger": c.get("trigger") or "unknown",
            "reclaimed": c.get("reclaimed"),
        })

    curves = []
    for sid, pts in by_sid.items():
        pts.sort(key=lambda p: p.get("ts") or 0)
        curves.append({
            "session_id": sid,
            "points": [{"ts": p.get("ts"), "pct": _num(p.get("pct"))} for p in pts],
            "peak_pct": max((_num(p.get("pct")) for p in pts), default=0.0),
            "compactions": comp_by_sid.get(sid, []),
            "overflowed": sid in overflow,
            "model": next((p.get("model") for p in pts if p.get("model")), None),
        })
    # Longest, most recent sessions first; cap for the wire.
    curves.sort(key=lambda c: (len(c["points"]), c["points"][-1]["ts"] or 0
                               if c["points"] else 0), reverse=True)
    return {"curves": curves[:max_sessions], "session_count": len(by_sid)}


# ---------------------------------------------------------------------------
# Head-to-head (REQ-HB-005): like-for-like cohort comparison. Two harnesses
# compare only when they did the same kind of work (same workload profile)
# with enough measurable sessions each; anything less is declined rather
# than compared (AC-HB-005.2).
# ---------------------------------------------------------------------------

HEADTOHEAD_MIN_COHORT = 5


def build_headtohead(
    sessions_by_runtime: dict[str, list[dict]] | None,
    *,
    min_cohort: int = HEADTOHEAD_MIN_COHORT,
    max_profiles: int = 4,
) -> dict[str, Any]:
    """Cohort comparison per workload profile.

    Returns {"matchups": [...], "declined_reason": str|None}. A matchup
    exists only for a profile where at least two harnesses each have
    ``min_cohort`` measurable sessions; cohort stats cover only measurable
    sessions so a blind harness cannot look cheap by having invisible
    failures (same rule as $/done).
    """
    from clawmetry.workload_profiles import classify_session

    # Two cohort bases (AC-HB-005.1): same workload profile, and same
    # workspace (cwd) where sessions carry one. A workspace matchup is the
    # cleaner like-for-like signal; the profile matchup is the fallback.
    cohorts: dict[str, dict[str, list[dict]]] = {}
    ws_cohorts: dict[str, dict[str, list[dict]]] = {}
    try:
        for rt, rows in (sessions_by_runtime or {}).items():
            for row in rows or []:
                feats = _session_features(row)
                if not feats["measurable"]:
                    continue
                if isinstance(row, dict):
                    rough_meta = row.get("metadata")
                    cwd = str(row.get("cwd") or "").rstrip("/")
                else:
                    cwd = ""
                profile = classify_session(row)
                cohorts.setdefault(profile, {}).setdefault(rt, []).append(feats)
                if cwd:
                    ws_cohorts.setdefault(cwd, {}).setdefault(rt, []).append(feats)
    except Exception:
        return {"matchups": [], "declined_reason": "cohorts_unavailable"}

    def _sides_for(by_rt: dict[str, list[dict]]) -> list[dict]:
        eligible = {rt: fl for rt, fl in by_rt.items() if len(fl) >= min_cohort}
        if len(eligible) < 2:
            return []
        sides = []
        for rt, fl in eligible.items():
            finished = [f for f in fl if f["outcome"] not in ("ongoing", "")]
            done = sum(1 for f in finished if f["done"])
            spend = sum(f["cost_usd"] for f in fl)
            rough = sum(1 for f in fl if f["rough"])
            sides.append({
                "runtime": rt,
                "sessions": len(fl),
                "done_rate": (round(done / len(finished), 3)
                              if finished else None),
                "avg_cost_usd": round(spend / len(fl), 2),
                "avg_tokens": int(sum(f["tokens"] for f in fl) / len(fl)),
                "spend_usd": round(spend, 2),
                "dollars_per_done": (round(spend / done, 2) if done else None),
                # Trajectory roughness (loop/recovery proxy): share of
                # measurable sessions with a rough quality verdict.
                "rough_rate": round(rough / len(fl), 3),
            })
        # Cheapest verified completion first; unpriceable sides last.
        sides.sort(key=lambda s: (s["dollars_per_done"] is None,
                                  s["dollars_per_done"] or 0))
        return sides[:4]

    matchups = []
    seen_ws_runtimes: set = set()
    for cwd, by_rt in ws_cohorts.items():
        sides = _sides_for(by_rt)
        if not sides:
            continue
        seen_ws_runtimes.update(s["runtime"] for s in sides)
        matchups.append({
            "basis": "workspace",
            "workspace": cwd.rsplit("/", 1)[-1] or cwd,
            "min_cohort": min_cohort,
            "sides": sides,
        })
    for profile, by_rt in cohorts.items():
        sides = _sides_for(by_rt)
        if not sides:
            continue
        # A workspace matchup over the same runtimes already tells this
        # story more precisely; skip the coarser duplicate.
        if {s["runtime"] for s in sides} <= seen_ws_runtimes and matchups:
            continue
        matchups.append({
            "basis": "workload_profile",
            "profile": profile,
            "min_cohort": min_cohort,
            "sides": sides,
        })
    matchups.sort(key=lambda m: -sum(s["spend_usd"] for s in m["sides"]))
    declined = None
    if not matchups:
        declined = "no_comparable_cohorts"
    return {"matchups": matchups[:max_profiles], "declined_reason": declined}
