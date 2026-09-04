"""Cohort compare and similar runs: pure math, no I/O (WO-60).

"Did the change help?" asked about a fleet, not about two sessions. An
operator changes a model, a runtime version, an instructions file or a
policy; the question is whether the population of sessions after the
change is doing better than the population before it. Everything here is
computed from rows the store already records. Nothing re-runs, nothing
calls a model, nothing assigns sessions to arms (cohorts are observational).

Contracts (requirement "Cohort compare and similar runs", REQ-COH-001..004):

* A cohort is the set of sessions matching a **filter** over runtime, model,
  runtime version, repository, developer, branch and a date range. Unknown
  filter keys are dropped, never errors.
* Per side the stats carry session count, cost, tokens, steps, tool error
  rate, outcome mix, cache hit and cost per finished job; every numeric
  metric gets a signed delta with a ``favorable`` direction. The delta math
  is the same function ``/api/run-compare`` uses (:func:`signed_deltas`).
* The verdict is one of ``Better`` / ``Worse`` / ``Same`` /
  ``Not enough data`` and rests on a small documented metric set
  (:data:`VERDICT_METRICS`). It never hides a metric that moved the other
  way: ``mixed`` is true and ``against`` lists them.
* Comparability follows the harness-bench rule: cohorts that differ
  materially on repository or developer mix are flagged, not silently
  compared.
* Shape similarity is n-gram based (2-grams and 3-grams of the ordered tool
  names, weighted Jaccard). A learned encoder may replace it without
  changing the response contract.

Like ``clawmetry/harness_bench.py`` this module is pure so tests can drive it
with fixture rows; ``clawmetry/cohort_queries.py`` owns store access and
``routes/cohort.py`` owns HTTP.
"""

from __future__ import annotations

import json
import os
from collections import Counter
from datetime import datetime, timedelta, timezone
from typing import Any

# ── Filters ────────────────────────────────────────────────────────────────

FILTER_KEYS = (
    "runtime", "model", "runtime_version", "repo", "developer", "branch",
    "since", "until",
)

# Minimum sessions per side before a verdict is printed. Small fleets are
# the norm for a solo developer, so "Not enough data" is a first-class
# answer, never an error.
DEFAULT_MIN_SESSIONS = 5
MIN_SESSIONS_ENV = "CLAWMETRY_COHORT_MIN_SESSIONS"

# A metric has "moved" when its relative change is at least this much.
# Below it the two sides are reported as the same on that metric.
MATERIAL_REL_CHANGE = 0.10
# Rates (0..1) additionally need an absolute move of this size, so a
# failure rate going 1% -> 1.2% is not a 20% regression.
MATERIAL_ABS_RATE = 0.02

# Comparability: total-variation distance between the two sides' repo /
# developer distributions above which the deltas are flagged as not
# like-for-like (harness bench compares same-workspace cohorts only; this is
# the softer, warn-not-refuse version of that rule).
COMPARABILITY_MAX_DISTANCE = 0.5

# Outcome labels, mirroring clawmetry/outcome_classifier.py. "abandoned" is
# derived here (ended with no finishing signal), the rest are stored labels.
OUTCOME_KEYS = (
    "success", "failed", "cognitive_loop", "tool_call_stuck", "escalated",
    "ongoing", "abandoned", "unknown",
)
FAILURE_OUTCOMES = frozenset({"failed", "cognitive_loop", "tool_call_stuck"})

LOWER_BETTER = (
    "cost_usd", "cost_per_session", "tokens", "tokens_per_session", "steps",
    "steps_per_session", "tool_error_rate", "failure_rate", "cost_per_done",
    "frustration_rate", "abandoned_rate",
)
HIGHER_BETTER = ("cache_hit", "done_rate")

# The verdict rests on these, in priority order. cost_per_done falls back to
# cost_per_session when no side has a finished job; frustration_rate only
# takes part when a behaviour-signal table exists in the store.
VERDICT_METRICS = (
    "cost_per_done", "failure_rate", "tool_error_rate", "frustration_rate",
)


def min_sessions() -> int:
    """Per-side sample floor, env-overridable. Never below 1."""
    raw = os.environ.get(MIN_SESSIONS_ENV, "").strip()
    try:
        n = int(raw) if raw else DEFAULT_MIN_SESSIONS
    except ValueError:
        n = DEFAULT_MIN_SESSIONS
    return max(1, n)


def parse_filter(raw: Any) -> dict:
    """Normalise a filter given as a JSON string, a dict, or None.

    Unknown keys are dropped, values are stripped strings, empty values are
    omitted. Malformed JSON yields ``{}`` rather than an error so a bad link
    degrades to "everything" with the filter echoed back for the reader.
    """
    if raw is None:
        return {}
    if isinstance(raw, (bytes, bytearray)):
        raw = raw.decode("utf-8", "replace")
    if isinstance(raw, str):
        raw = raw.strip()
        if not raw:
            return {}
        try:
            raw = json.loads(raw)
        except ValueError:
            return {}
    if not isinstance(raw, dict):
        return {}
    out: dict = {}
    for k in FILTER_KEYS:
        v = raw.get(k)
        if v is None:
            continue
        s = str(v).strip()
        if s:
            out[k] = s
    return out


def filter_from_params(args: Any, side: str) -> dict:
    """Read side ``a`` / ``b`` from query params.

    Accepts ``a=<json>`` or repeated params ``a.runtime=`` / ``a_runtime=``;
    the repeated form overrides keys of the JSON form.
    """
    getter = getattr(args, "get", None)
    if getter is None:
        return {}
    out = parse_filter(getter(side))
    for k in FILTER_KEYS:
        for sep in (".", "_"):
            v = getter(f"{side}{sep}{k}")
            if v is not None and str(v).strip():
                out[k] = str(v).strip()
                break
    return out


def describe_filter(f: dict) -> str:
    """Plain-words label for a filter, for titles and empty states."""
    bits = []
    for k in ("runtime", "model", "runtime_version", "repo", "developer", "branch"):
        if f.get(k):
            bits.append(f"{k.replace('_', ' ')} {f[k]}")
    if f.get("since") and f.get("until"):
        bits.append(f"{f['since'][:10]} to {f['until'][:10]}")
    elif f.get("since"):
        bits.append(f"since {f['since'][:10]}")
    elif f.get("until"):
        bits.append(f"until {f['until'][:10]}")
    return ", ".join(bits) or "all sessions"


# ── Session rows ───────────────────────────────────────────────────────────

def _num(v: Any, default: float = 0.0) -> float:
    try:
        if v is None:
            return default
        return float(v)
    except (TypeError, ValueError):
        return default


def _repo_of(cwd: Any) -> str:
    s = str(cwd or "").strip().rstrip("/")
    if not s:
        return ""
    return s.rsplit("/", 1)[-1] or s


def _runtime_of(row: dict) -> str:
    meta = row.get("metadata") if isinstance(row.get("metadata"), dict) else {}
    rt = str(meta.get("runtime") or row.get("runtime") or "").strip()
    if rt:
        return rt
    sid = str(row.get("session_id") or "")
    return sid.split(":", 1)[0] if ":" in sid else "openclaw"


def _model_of(row: dict) -> str:
    meta = row.get("metadata") if isinstance(row.get("metadata"), dict) else {}
    for k in ("model", "recent_model"):
        v = meta.get(k) or row.get(k)
        if isinstance(v, str) and v.strip():
            return v.strip()
    return ""


def _runtime_version_of(row: dict) -> str:
    meta = row.get("metadata") if isinstance(row.get("metadata"), dict) else {}
    for k in ("runtime_version", "runtimeVersion", "cliVersion", "version"):
        v = meta.get(k) or row.get(k)
        if isinstance(v, str) and v.strip():
            return v.strip()
    return ""


def session_view(row: dict) -> dict:
    """Reduce a store row to the fields the cohort math reads.

    Missing figures stay missing (``None``) rather than becoming zeros, so a
    cohort of sessions with no tool stream reports ``tool_error_rate: None``
    instead of a fabricated 0%.
    """
    meta = row.get("metadata") if isinstance(row.get("metadata"), dict) else {}
    split = meta.get("tokenSplit") if isinstance(meta.get("tokenSplit"), dict) else {}
    tool_results = row.get("tool_results", meta.get("toolResults"))
    tool_errors = row.get("tool_errors", meta.get("toolErrors"))
    steps = row.get("steps")
    if steps is None:
        steps = row.get("tool_calls")
    if steps is None and tool_results is not None:
        steps = tool_results
    outcome = str(row.get("outcome") or "").strip() or "unknown"
    status = str(row.get("status") or "").lower()
    if outcome == "unknown" and row.get("ended_at") and status in ("ended", "completed", "closed", "done"):
        outcome = "abandoned"
    git_links = row.get("git_commits_linked")
    done = bool(git_links) if git_links is not None else (outcome == "success")
    signals = row.get("signals")
    return {
        "session_id": str(row.get("session_id") or ""),
        "title": row.get("title") or "",
        "runtime": _runtime_of(row),
        "model": _model_of(row),
        "runtime_version": _runtime_version_of(row) or None,
        "repo": _repo_of(row.get("cwd")),
        "developer": str(row.get("node_id") or "").strip(),
        "branch": str(row.get("git_branch") or "").strip(),
        "started_at": str(row.get("started_at") or row.get("last_active_at") or ""),
        "cost_usd": _num(row.get("cost_usd")),
        "tokens": int(_num(row.get("total_tokens"))),
        "steps": int(_num(steps)) if steps is not None else None,
        "tool_results": int(_num(tool_results)) if tool_results is not None else None,
        "tool_errors": int(_num(tool_errors)) if tool_errors is not None else None,
        "cache_read": int(_num(split.get("cacheRead"))) if split else None,
        "input_tokens": int(_num(split.get("input"))) if split else None,
        "outcome": outcome,
        "done": done,
        "done_basis": "git_commit" if git_links is not None else "outcome",
        "signals": sorted(signals) if isinstance(signals, (list, set, tuple)) else None,
        "instructions_hash": str(row.get("instructions_hash") or "") or None,
    }


def _ts_key(s: str) -> str:
    return (s or "")[:19].replace(" ", "T")


def session_matches(view: dict, f: dict) -> bool:
    for k in ("runtime", "model", "runtime_version", "repo", "developer", "branch"):
        want = f.get(k)
        if want and str(view.get(k) or "").lower() != want.lower():
            return False
    st = _ts_key(view.get("started_at") or "")
    if f.get("since") and st and st < _ts_key(f["since"]):
        return False
    if f.get("until") and st and st > _ts_key(f["until"]):
        return False
    return True


def select_cohort(views: list[dict], f: dict) -> list[dict]:
    return [v for v in views if session_matches(v, f)]


# ── Per-side stats ─────────────────────────────────────────────────────────

def cohort_stats(views: list[dict], *, signals_available: bool = False) -> dict:
    """Aggregate one side. Rates are ``None`` when their denominator is
    empty; ``signals`` is the literal string ``"not available"`` when the
    store has no behaviour-signal table."""
    n = len(views)
    cost = sum(v["cost_usd"] for v in views)
    tokens = sum(v["tokens"] for v in views)
    step_views = [v for v in views if v.get("steps") is not None]
    steps = sum(v["steps"] for v in step_views)
    tr = sum(v["tool_results"] for v in views if v.get("tool_results") is not None)
    te = sum(v["tool_errors"] for v in views if v.get("tool_errors") is not None)
    cr = sum(v["cache_read"] for v in views if v.get("cache_read") is not None)
    inp = sum(v["input_tokens"] for v in views if v.get("input_tokens") is not None)
    mix = Counter(v["outcome"] for v in views)
    outcome_mix = {k: int(mix.get(k, 0)) for k in OUTCOME_KEYS if mix.get(k, 0)}
    finished = [v for v in views if v["outcome"] not in ("ongoing", "unknown")]
    failures = sum(1 for v in views if v["outcome"] in FAILURE_OUTCOMES)
    done = sum(1 for v in views if v["done"])
    done_basis = "git_commit" if any(v["done_basis"] == "git_commit" for v in views) else "outcome"

    out: dict = {
        "session_count": n,
        "cost_usd": round(cost, 4),
        "cost_per_session": round(cost / n, 4) if n else None,
        "tokens": int(tokens),
        "tokens_per_session": int(tokens / n) if n else None,
        "steps": int(steps) if step_views else None,
        "steps_per_session": round(steps / len(step_views), 1) if step_views else None,
        "tool_error_rate": round(te / tr, 4) if tr else None,
        "outcome_mix": outcome_mix,
        "failure_rate": round(failures / len(finished), 4) if finished else None,
        "abandoned_rate": (round(mix.get("abandoned", 0) / len(finished), 4)
                           if finished else None),
        "cache_hit": round(cr / (cr + inp), 4) if (cr + inp) > 0 else None,
        "done": done,
        "done_rate": round(done / len(finished), 4) if finished else None,
        "cost_per_done": round(cost / done, 4) if done else None,
        "done_basis": done_basis,
        "coverage": {
            "steps": len(step_views),
            "tool_health": sum(1 for v in views if v.get("tool_results") is not None),
            "cache": sum(1 for v in views if v.get("cache_read") is not None),
            "finished": len(finished),
        },
    }
    if signals_available:
        sig = Counter()
        for v in views:
            for s in v.get("signals") or []:
                sig[s] += 1
        out["signals"] = {k: round(c / n, 4) for k, c in sorted(sig.items())} if n else {}
        frustration = sum(1 for v in views if "frustration" in (v.get("signals") or []))
        out["frustration_rate"] = round(frustration / n, 4) if n else None
    else:
        out["signals"] = "not available"
    return out


# ── Deltas (shared with /api/run-compare) ─────────────────────────────────

def signed_deltas(a: dict, b: dict, lower_better: tuple, higher_better: tuple) -> dict:
    """Signed delta per numeric metric present on both sides.

    ``abs`` is b minus a, ``pct`` is relative to a (``None`` when a is zero,
    never a division by zero), ``favorable`` says whether the move is an
    improvement given the metric's direction. This is the one delta rule in
    the product: ``/api/run-compare`` and ``/api/cohort-compare`` both call
    it, so a green cell means the same thing on both surfaces.
    """
    out: dict = {}
    for key in tuple(lower_better) + tuple(higher_better):
        va = a.get(key)
        vb = b.get(key)
        if va is None or vb is None:
            continue
        if isinstance(va, bool) or isinstance(vb, bool):
            continue
        try:
            absd = vb - va
        except TypeError:
            continue
        pct = (absd / va * 100.0) if va not in (0, 0.0) else None
        lower = key in lower_better
        favorable = (absd < 0) if lower else (absd > 0)
        out[key] = {
            "a": va, "b": vb, "abs": absd, "pct": pct,
            "favorable": favorable, "favorable_lower": lower,
        }
    return out


def cohort_deltas(a: dict, b: dict) -> dict:
    return signed_deltas(a, b, LOWER_BETTER, HIGHER_BETTER)


# ── Verdict ────────────────────────────────────────────────────────────────

_RATE_METRICS = frozenset({
    "tool_error_rate", "failure_rate", "frustration_rate", "abandoned_rate",
    "cache_hit", "done_rate",
})


def _material(key: str, d: dict) -> bool:
    absd = d.get("abs")
    if absd in (None, 0, 0.0):
        return False
    if key in _RATE_METRICS:
        return abs(absd) >= MATERIAL_ABS_RATE
    pct = d.get("pct")
    if pct is None:
        return True  # from zero to something is always a move
    return abs(pct) >= MATERIAL_REL_CHANGE * 100.0


def verdict(stats_a: dict, stats_b: dict, deltas: dict, *, floor: int | None = None) -> dict:
    """One word plus the metrics behind it.

    Returns ``{verdict, mixed, drivers, against, min_sessions, sample}``.
    ``drivers`` are the metrics that moved in the verdict's direction,
    ``against`` the ones that moved the other way (present whenever
    ``mixed`` is true). A tie is reported as ``Same`` with ``mixed: true``.
    """
    floor = min_sessions() if floor is None else max(1, int(floor))
    na = int(stats_a.get("session_count") or 0)
    nb = int(stats_b.get("session_count") or 0)
    sample = {"a": na, "b": nb}
    if na < floor or nb < floor:
        return {
            "verdict": "Not enough data", "mixed": False, "drivers": [],
            "against": [], "min_sessions": floor, "sample": sample,
            "reason": (f"Each side needs at least {floor} sessions; "
                       f"got {na} and {nb}."),
        }
    metrics = list(VERDICT_METRICS)
    # cost per finished job falls back to cost per session when neither side
    # has a finished job to price.
    if "cost_per_done" not in deltas and "cost_per_session" in deltas:
        metrics[metrics.index("cost_per_done")] = "cost_per_session"
    good, bad = [], []
    for key in metrics:
        d = deltas.get(key)
        if not d or not _material(key, d):
            continue
        (good if d["favorable"] else bad).append(key)
    if not good and not bad:
        word = "Same"
    elif len(good) > len(bad):
        word = "Better"
    elif len(bad) > len(good):
        word = "Worse"
    else:
        word = "Same"
    mixed = bool(good and bad)
    drivers, against = (good, bad) if word != "Worse" else (bad, good)
    return {
        "verdict": word, "mixed": mixed, "drivers": drivers,
        "against": against, "min_sessions": floor, "sample": sample,
        "metrics_considered": metrics,
    }


# ── Comparability ──────────────────────────────────────────────────────────

def _distribution(views: list[dict], key: str) -> dict:
    c = Counter(str(v.get(key) or "") for v in views)
    n = sum(c.values())
    return {k: v / n for k, v in c.items()} if n else {}


def mix_distance(views_a: list[dict], views_b: list[dict], key: str) -> float | None:
    """Total-variation distance (0 identical, 1 disjoint) between the two
    sides' distributions over ``key``. ``None`` when a side is empty."""
    pa = _distribution(views_a, key)
    pb = _distribution(views_b, key)
    if not pa or not pb:
        return None
    keys = set(pa) | set(pb)
    return round(0.5 * sum(abs(pa.get(k, 0.0) - pb.get(k, 0.0)) for k in keys), 4)


def comparability(views_a: list[dict], views_b: list[dict]) -> dict:
    """Warn when the two cohorts differ materially on repository or
    developer mix (the harness-bench rule: unlike work is never compared).
    The comparison still runs; the warning travels with the numbers."""
    warnings = []
    for key, label in (("repo", "repository"), ("developer", "developer")):
        # A dimension nobody recorded on either side is not a mismatch.
        if not any(v.get(key) for v in views_a + views_b):
            continue
        dist = mix_distance(views_a, views_b, key)
        if dist is not None and dist > COMPARABILITY_MAX_DISTANCE:
            warnings.append({
                "dimension": key,
                "distance": dist,
                "note": (f"The two sides mostly ran on different {label}s "
                         f"({int(dist * 100)}% of the mix differs). "
                         f"Deltas may reflect the work, not the change."),
            })
    return {"comparable": not warnings, "warnings": warnings}


# ── Full comparison ────────────────────────────────────────────────────────

def compare(views: list[dict], filter_a: dict, filter_b: dict, *,
            signals_available: bool = False, floor: int | None = None,
            sample_sessions: int = 25) -> dict:
    """The whole response body for one comparison, from normalised views."""
    side_a = select_cohort(views, filter_a)
    side_b = select_cohort(views, filter_b)
    stats_a = cohort_stats(side_a, signals_available=signals_available)
    stats_b = cohort_stats(side_b, signals_available=signals_available)
    deltas = cohort_deltas(stats_a, stats_b)

    def _sample(rows: list[dict]) -> list[dict]:
        rows = sorted(rows, key=lambda v: v.get("started_at") or "", reverse=True)
        return [{
            "session_id": v["session_id"], "title": v.get("title") or "",
            "runtime": v["runtime"], "model": v["model"],
            "cost_usd": round(v["cost_usd"], 4), "outcome": v["outcome"],
            "started_at": v.get("started_at") or "",
        } for v in rows[:sample_sessions]]

    return {
        "a": {"filter": filter_a, "label": describe_filter(filter_a),
              "stats": stats_a, "sessions": _sample(side_a)},
        "b": {"filter": filter_b, "label": describe_filter(filter_b),
              "stats": stats_b, "sessions": _sample(side_b)},
        "deltas": deltas,
        "verdict": verdict(stats_a, stats_b, deltas, floor=floor),
        "comparability": comparability(side_a, side_b),
        "signals": ("available" if signals_available else "not available"),
        "runtimes": sorted({v["runtime"] for v in side_a + side_b}),
    }


# ── Suggested comparisons ──────────────────────────────────────────────────

def _iso(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%dT%H:%M:%S")


def _pretty_runtime(rt: str) -> str:
    return {
        "claude_code": "Claude Code", "openclaw": "OpenClaw",
        "nemoclaw": "NemoClaw", "gemini_cli": "Gemini CLI",
    }.get(rt, rt.replace("_", " ").title() if rt else "all runtimes")


def build_suggestions(views: list[dict], *, now: datetime | None = None,
                      recent_days: int = 14, context_available: bool = False,
                      runtime: str | None = None, cap: int = 8) -> list[dict]:
    """Derive ready-made a/b filters from what changed recently in the store.

    * a model first seen in the last ``recent_days`` on a runtime that had
      another model before it: before vs after;
    * a runtime version first seen in the window (only when versions are
      recorded at all);
    * an instructions-file hash first seen (only when the store has a
      ``session_context`` table; ``context_available`` says so);
    * "this week vs last week" per runtime.

    Every suggestion carries ``a`` / ``b`` filters and a plain-words title.
    """
    now = now or datetime.now(timezone.utc).replace(tzinfo=None)
    recent = _iso(now - timedelta(days=recent_days))
    # The "before" side reaches back one more window so the previous model /
    # version / instructions file has sessions to stand on.
    before = _iso(now - timedelta(days=recent_days * 2))
    if runtime and runtime != "all":
        views = [v for v in views if v["runtime"] == runtime]
    out: list[dict] = []

    def _first_seen(key: str) -> dict:
        seen: dict = {}
        for v in views:
            val = v.get(key)
            if not val:
                continue
            k = (v["runtime"], val)
            st = _ts_key(v.get("started_at") or "")
            if not st:
                continue
            if k not in seen or st < seen[k]:
                seen[k] = st
        return seen

    for key, kind, noun in (("model", "new_model", "model"),
                            ("runtime_version", "new_runtime_version", "runtime version")):
        seen = _first_seen(key)
        by_rt: dict = {}
        for (rt, val), first in seen.items():
            by_rt.setdefault(rt, []).append((first, val))
        for rt, items in by_rt.items():
            items.sort()
            if len(items) < 2:
                continue
            for i in range(1, len(items)):
                first, val = items[i]
                if first < recent:
                    continue
                prev_val = items[i - 1][1]
                title = (f"{val} vs {prev_val} on {_pretty_runtime(rt)}, "
                         f"last {recent_days} days")
                out.append({
                    "id": f"{kind}:{rt}:{val}",
                    "kind": kind,
                    "title": title,
                    "why": f"A new {noun} was first seen on {first[:10]}.",
                    "a": {"runtime": rt, key: prev_val, "since": before, "until": first},
                    "b": {"runtime": rt, key: val, "since": first},
                })
    if context_available:
        seen = _first_seen("instructions_hash")
        by_rt = {}
        for (rt, val), first in seen.items():
            by_rt.setdefault(rt, []).append((first, val))
        for rt, items in by_rt.items():
            items.sort()
            for i in range(1, len(items)):
                first, val = items[i]
                if first < recent:
                    continue
                out.append({
                    "id": f"new_instructions:{rt}:{val[:12]}",
                    "kind": "new_instructions",
                    "title": (f"Instructions changed on {_pretty_runtime(rt)}: "
                              f"before vs after {first[:10]}"),
                    "why": "The instructions file the agent reads changed.",
                    "a": {"runtime": rt, "since": before, "until": first},
                    "b": {"runtime": rt, "since": first},
                })
    week_ago = _iso(now - timedelta(days=7))
    two_weeks = _iso(now - timedelta(days=14))
    for rt in sorted({v["runtime"] for v in views}):
        out.append({
            "id": f"week_over_week:{rt}",
            "kind": "week_over_week",
            "title": f"This week vs last week on {_pretty_runtime(rt)}",
            "why": "The same runtime, seven days apart.",
            "a": {"runtime": rt, "since": two_weeks, "until": week_ago},
            "b": {"runtime": rt, "since": week_ago},
        })
    return out[:cap]


# ── Similar runs by tool-call shape ────────────────────────────────────────

def tool_shape(seq: list[str]) -> Counter:
    """2-gram and 3-gram multiset of an ordered tool-name sequence. Tool
    names are lower-cased; a one-tool session still yields its unigram so
    two single-call sessions can match."""
    names = [str(n).strip().lower() for n in seq if str(n or "").strip()]
    shape: Counter = Counter()
    if not names:
        return shape
    if len(names) == 1:
        shape[("1", names[0])] += 1
        return shape
    for i in range(len(names) - 1):
        shape[("2", names[i], names[i + 1])] += 1
    for i in range(len(names) - 2):
        shape[("3", names[i], names[i + 1], names[i + 2])] += 1
    return shape


def weighted_jaccard(a: Counter, b: Counter) -> float:
    if not a or not b:
        return 0.0
    keys = set(a) | set(b)
    num = sum(min(a.get(k, 0), b.get(k, 0)) for k in keys)
    den = sum(max(a.get(k, 0), b.get(k, 0)) for k in keys)
    return round(num / den, 4) if den else 0.0


def similar_by_shape(target_seq: list[str], candidates: dict[str, list[str]],
                     *, limit: int = 10) -> list[dict]:
    """Rank ``candidates`` ({session_id: tool sequence}) by shape similarity
    to ``target_seq``. Sessions with no tools never appear."""
    target = tool_shape(target_seq)
    if not target:
        return []
    scored = []
    for sid, seq in candidates.items():
        shape = tool_shape(seq)
        if not shape:
            continue
        score = weighted_jaccard(target, shape)
        if score <= 0:
            continue
        scored.append({"session_id": sid, "score": score, "tool_calls": len(seq)})
    scored.sort(key=lambda r: (-r["score"], r["session_id"]))
    return scored[:max(1, int(limit))]
