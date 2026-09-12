"""AgentOps window metrics: latency, handoffs, guardrails, review, ground truth.

IBM Technology's AgentOps explainer ("Are Your AI Agents Flying Blind?")
names the numbers an operator should watch. ClawMetry already recorded most
of the raw material and turned very little of it into a figure anything could
alert on. This module closes that gap for the ones an observer can measure:

* p50 / p95 **session duration** (end-to-end completion time),
* p50 / p95 **tool latency**, overall and per tool, plus tool error counts,
* **handoff** failure rate and p50 / p95 handoff round trip (sub-agent spawn
  to its result),
* **guardrail violation rate**: the share of active sessions that tripped a
  Guard policy, had an approval denied, or hit a blocking guardrail verdict,
* **reviewer accuracy** from the human review queue,
* **ground-truth accuracy** and **first-pass rate** from outcomes the
  operator's own system posts to ``POST /api/ground-truth``.

Everything reads rows the store already keeps (``sessions``, ``events``,
``subagents``, ``policy_actions``, ``approvals``, ``guardrail_events``,
``review_queue``, ``session_ground_truth``) over one window. The result is
merged into ``LocalStore.query_session_quality_window``, so each figure
reaches the alert evaluator on the cloud-dispatch and the self-hosted path
alike, runtime-scoped, without new plumbing.

House rules:

* A figure with no sample is ``None`` and its count is ``0``; a rate is
  never reported as 0% because nothing was measured.
* Blocks are independent. One failing query (an older store without a table)
  blanks its own keys and logs, never the rest.
* The whole result is cached per ``(store, window, runtime)`` for
  :data:`CACHE_TTL_SEC`, so an alert tick every 15 seconds does not rescan
  the event table (FLYWHEEL.md 1e, the CPU budget).
"""

from __future__ import annotations

import logging
import re
import threading
import time
from datetime import datetime, timezone
from typing import Any

log = logging.getLogger("clawmetry.agentops_metrics")

CACHE_TTL_SEC = 60.0
# Upper bound on rows any one block reads. Enough for a busy node's hour and
# a quiet node's week; the tool block reports ``tool_scan_truncated`` when it
# hits the ceiling so a reader knows the percentile is over the newest calls.
ROW_LIMIT = 5000
TOOL_EVENT_SCAN_LIMIT = 5000
PER_TOOL_TOP = 25

FAILURE_OUTCOMES = frozenset({"failed", "tool_call_stuck", "cognitive_loop"})
# Sub-agent statuses that mean the delegated task did not come back.
HANDOFF_FAILED_STATUSES = frozenset({
    "failed", "error", "errored", "timeout", "timed_out", "killed",
    "cancelled", "canceled", "aborted", "crashed",
})
# Guardrail verdicts that stopped something. ``no_override`` / ``allow`` are
# the allowed side and deliberately absent.
GUARDRAIL_BLOCK_VERDICTS = frozenset({
    "deny", "denied", "block", "blocked", "reject", "rejected", "violation",
})
APPROVAL_DENIED = frozenset({"deny", "denied", "reject", "rejected"})

_cache: dict = {}
_cache_lock = threading.Lock()


# ── Small pure helpers ─────────────────────────────────────────────────────

def percentile(values, p: float) -> float | None:
    """Linear-interpolated percentile (``p`` in 0..100). ``None`` when empty."""
    vals = sorted(float(v) for v in values if v is not None)
    if not vals:
        return None
    if len(vals) == 1:
        return vals[0]
    k = (len(vals) - 1) * (p / 100.0)
    f = int(k)
    if f + 1 < len(vals):
        return vals[f] + (vals[f + 1] - vals[f]) * (k - f)
    return vals[f]


def parse_ts(value: Any) -> float | None:
    """Epoch seconds from an ISO string or an epoch number (s or ms).

    Tolerates a trailing ``Z`` and millisecond fractions on Python < 3.11
    (``fromisoformat`` there rejects both). A naive timestamp is read as UTC,
    which is what every writer in the store emits.
    """
    if value is None:
        return None
    if isinstance(value, (int, float)):
        v = float(value)
        return v / 1000.0 if v > 1e11 else v
    txt = str(value).strip()
    if not txt:
        return None
    if txt.endswith("Z"):
        txt = txt[:-1] + "+00:00"
    dt = None
    try:
        dt = datetime.fromisoformat(txt)
    except ValueError:
        try:
            dt = datetime.fromisoformat(txt[:19])
        except ValueError:
            return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.timestamp()


def _round(v: float | None, nd: int = 3) -> float | None:
    return None if v is None else round(float(v), nd)


def _rate(num: int, den: int) -> float | None:
    return round(num / den, 4) if den else None


def _retarget(clause: str | None, column: str) -> str | None:
    """``_runtime_session_id_clause`` is written against a bare
    ``session_id`` column. Point it at another column (``s.session_id``,
    ``parent_session_id``) so every block scopes by the same rule."""
    if not clause:
        return clause
    return re.sub(r"\bsession_id\b", column, clause)


def _session_runtime(sid: Any) -> str:
    from clawmetry.alert_evaluator import _session_runtime as _sr
    return _sr(sid)


def _in_runtime(sid: Any, runtime: str | None) -> bool:
    if not runtime or runtime == "all":
        return True
    return _session_runtime(sid) == str(runtime).lower()


# ── Public API ─────────────────────────────────────────────────────────────

def clear_cache() -> None:
    with _cache_lock:
        _cache.clear()


def window_extras(store: Any, window_minutes: int, runtime: str | None = None,
                  *, now: float | None = None) -> dict:
    """Cached :func:`compute_window_extras`. ``now`` bypasses the cache (tests)."""
    if now is not None:
        return compute_window_extras(store, window_minutes, runtime, now=now)
    key = (id(store), int(window_minutes), str(runtime or "all").lower())
    t = time.time()
    with _cache_lock:
        hit = _cache.get(key)
        if hit and (t - hit[0]) < CACHE_TTL_SEC:
            return dict(hit[1])
    out = compute_window_extras(store, window_minutes, runtime)
    with _cache_lock:
        if len(_cache) > 64:
            _cache.clear()
        _cache[key] = (t, out)
    return dict(out)


def compute_window_extras(store: Any, window_minutes: int,
                          runtime: str | None = None, *,
                          now: float | None = None) -> dict:
    """Every AgentOps figure over ``now - window_minutes``. Never raises."""
    try:
        from clawmetry.local_store import _runtime_session_id_clause
        clause, params = _runtime_session_id_clause(runtime)
    except Exception:
        clause, params = None, []
    now = time.time() if now is None else float(now)
    try:
        window_minutes = max(1, int(window_minutes))
    except (TypeError, ValueError):
        window_minutes = 60
    cutoff_s = now - window_minutes * 60
    ctx = {
        "cutoff_s": cutoff_s,
        "cutoff_ms": int(cutoff_s * 1000),
        "cutoff_iso": datetime.fromtimestamp(cutoff_s, tz=timezone.utc).isoformat(),
        "clause": clause,
        "params": list(params),
        "runtime": runtime,
    }
    out: dict = {}
    for block in (_latency_block, _tool_block, _handoff_block,
                  _guardrail_block, _review_block, _ground_truth_block):
        try:
            out.update(block(store, ctx))
        except Exception as e:  # one missing table must not blank the rest
            log.warning("agentops metrics: %s failed: %s", block.__name__, e)
    return out


# ── Blocks ─────────────────────────────────────────────────────────────────

def _fetch(store: Any, sql: str, params: list) -> list:
    return list(store._fetch(sql, params) or [])


def _latency_block(store: Any, ctx: dict) -> dict:
    """End-to-end duration of top-level sessions classified in the window
    (the same cohort ``outcome_failure_rate`` counts). Sub-agent sessions are
    excluded: they are handoffs, measured by :func:`_handoff_block`."""
    scoped = _retarget(ctx["clause"], "s.session_id")
    rows = _fetch(store, f"""
        SELECT s.started_at, s.ended_at
          FROM sessions s
         WHERE s.started_at IS NOT NULL
           AND s.ended_at IS NOT NULL
           AND s.outcome IS NOT NULL AND s.outcome <> 'ongoing'
           AND s.outcome_classified_at IS NOT NULL
           AND s.outcome_classified_at >= ?
           AND s.session_id NOT IN (
               SELECT subagent_id FROM subagents
                WHERE parent_session_id IS NOT NULL AND parent_session_id <> '')
           {('AND ' + scoped) if scoped else ''}
         LIMIT {ROW_LIMIT}
    """, [ctx["cutoff_ms"], *ctx["params"]])
    durs = []
    for started, ended in rows:
        a, b = parse_ts(started), parse_ts(ended)
        if a is not None and b is not None and b > a:
            durs.append(b - a)
    return {
        "timed_sessions": len(durs),
        "session_duration_p50_sec": _round(percentile(durs, 50), 1),
        "session_duration_p95_sec": _round(percentile(durs, 95), 1),
    }


def _tool_block(store: Any, ctx: dict) -> dict:
    """Tool-call latency, paired call -> result by tool-use id with the same
    helpers the Tool Catalog uses, so both surfaces agree on every number."""
    from routes import tool_catalog as tc

    raw = store.query_events(since=ctx["cutoff_iso"], runtime=ctx["runtime"],
                             limit=TOOL_EVENT_SCAN_LIMIT)
    rows = tc._coerce_rows(raw)
    idx = tc._result_index(rows)
    per: dict = {}
    all_durs: list = []
    calls = errors = 0
    for name, _start, dur, err, _sid in tc._iter_tool_calls(rows, idx):
        a = per.setdefault(name, {"calls": 0, "durs": [], "errors": 0})
        a["calls"] += 1
        calls += 1
        if dur is not None:
            a["durs"].append(dur)
            all_durs.append(dur)
        if err:
            a["errors"] += 1
            errors += 1
    by_tool = sorted(
        ({"name": n, "calls": a["calls"], "timed_calls": len(a["durs"]),
          "errors": a["errors"],
          "p50_ms": _round(percentile(a["durs"], 50), 0),
          "p95_ms": _round(percentile(a["durs"], 95), 0)}
         for n, a in per.items()),
        key=lambda t: (-t["calls"], t["name"]),
    )[:PER_TOOL_TOP]
    return {
        "tool_calls": calls,
        "tool_errors": errors,
        "tool_error_rate": _rate(errors, calls),
        "timed_tool_calls": len(all_durs),
        "tool_latency_p50_ms": _round(percentile(all_durs, 50), 0),
        "tool_latency_p95_ms": _round(percentile(all_durs, 95), 0),
        "tool_latency_by_tool": by_tool,
        "tool_scan_truncated": len(rows) >= TOOL_EVENT_SCAN_LIMIT,
    }


def _handoff_block(store: Any, ctx: dict) -> dict:
    """Sub-agent handoffs spawned in the window, scoped by the PARENT's
    runtime. A handoff has failed when its status says so or the child
    session's outcome is a failure label; running ones are left out of the
    rate. Latency is the round trip, spawn to the child's end: the recorded
    spawn time equals the child's start time, so a pickup delay is not
    something the store can measure and is not claimed."""
    scoped = _retarget(ctx["clause"], "a.parent_session_id")
    rows = _fetch(store, f"""
        SELECT a.spawned_at, a.ended_at, a.status, s.outcome
          FROM subagents a
          LEFT JOIN sessions s ON s.session_id = a.subagent_id
         WHERE a.parent_session_id IS NOT NULL AND a.parent_session_id <> ''
           AND a.spawned_at IS NOT NULL AND a.spawned_at >= ?
           {('AND ' + scoped) if scoped else ''}
         ORDER BY a.spawned_at DESC
         LIMIT {ROW_LIMIT}
    """, [ctx["cutoff_iso"], *ctx["params"]])
    total = finished = failed = 0
    durs = []
    for spawned, ended, status, outcome in rows:
        total += 1
        st = str(status or "").strip().lower()
        oc = str(outcome or "").strip().lower()
        is_failed = st in HANDOFF_FAILED_STATUSES or oc in FAILURE_OUTCOMES
        if ended or is_failed:
            finished += 1
        if is_failed:
            failed += 1
        a, b = parse_ts(spawned), parse_ts(ended)
        if a is not None and b is not None and b >= a:
            durs.append(b - a)
    return {
        "handoffs": total,
        "handoffs_finished": finished,
        "handoff_failed": failed,
        "handoff_failure_rate": _rate(failed, finished),
        "handoff_timed": len(durs),
        "handoff_p50_sec": _round(percentile(durs, 50), 1),
        "handoff_p95_sec": _round(percentile(durs, 95), 1),
    }


def _guardrail_block(store: Any, ctx: dict) -> dict:
    """Share of sessions active in the window that tripped a guardrail: a
    Guard policy matched (monitor mode included, because the match is the
    violation; enforcement is a separate decision), an approval was denied,
    or a guardrail verdict blocked something."""
    scoped = ctx["clause"]
    row = _fetch(store, f"""
        SELECT COUNT(*) FROM sessions
         WHERE COALESCE(last_active_at, started_at, '') >= ?
           {('AND ' + scoped) if scoped else ''}
    """, [ctx["cutoff_iso"], *ctx["params"]])
    active = int(row[0][0] or 0) if row else 0

    hits: dict = {}
    by_source = {"policy": 0, "approval_denied": 0, "guardrail_block": 0}
    probes = (
        ("policy", "SELECT session_id FROM policy_actions WHERE created_at >= ?",
         [ctx["cutoff_ms"]]),
        ("approval_denied",
         "SELECT requestor_session_id FROM approvals "
         "WHERE COALESCE(resolved_at, created_at, '') >= ? "
         "AND lower(COALESCE(decision, status, '')) IN ("
         + ",".join("?" * len(APPROVAL_DENIED)) + ")",
         [ctx["cutoff_iso"], *sorted(APPROVAL_DENIED)]),
        ("guardrail_block",
         "SELECT session_id FROM guardrail_events WHERE ts >= ? "
         "AND lower(COALESCE(verdict, '')) IN ("
         + ",".join("?" * len(GUARDRAIL_BLOCK_VERDICTS)) + ")",
         [ctx["cutoff_iso"], *sorted(GUARDRAIL_BLOCK_VERDICTS)]),
    )
    for source, sql, params in probes:
        try:
            for (sid,) in _fetch(store, sql + f" LIMIT {ROW_LIMIT}", params):
                if not sid or not _in_runtime(sid, ctx["runtime"]):
                    continue
                by_source[source] += 1
                hits[str(sid)] = True
        except Exception as e:  # an older store may lack the table
            log.debug("agentops metrics: guardrail probe %s skipped: %s", source, e)
    violating = min(len(hits), active) if active else len(hits)
    return {
        "guardrail_sessions": active,
        "guardrail_violating_sessions": violating,
        "guardrail_violation_rate": _rate(violating, active),
        "guardrail_events_by_source": by_source,
    }


def _review_block(store: Any, ctx: dict) -> dict:
    """Reviewer verdicts recorded in the window. Borderline is excluded from
    the denominator, as ``query_review_accuracy`` does."""
    scoped = ctx["clause"]
    rows = _fetch(store, f"""
        SELECT status, COUNT(*) FROM review_queue
         WHERE reviewed_at IS NOT NULL AND reviewed_at >= ?
           {('AND ' + scoped) if scoped else ''}
         GROUP BY status
    """, [ctx["cutoff_iso"], *ctx["params"]])
    counts = {str(s or ""): int(n or 0) for s, n in rows}
    correct = counts.get("reviewed_correct", 0)
    wrong = counts.get("reviewed_wrong", 0)
    return {
        "reviews": correct + wrong,
        "review_correct": correct,
        "review_wrong": wrong,
        "review_borderline": counts.get("reviewed_borderline", 0),
        "review_accuracy": _rate(correct, correct + wrong),
    }


def _ground_truth_block(store: Any, ctx: dict) -> dict:
    """Outcomes the operator's system of record posted for sessions in the
    window (``POST /api/ground-truth``). Accuracy counts reports that carry a
    ``correct`` verdict; first-pass rate counts reports that carry
    ``first_pass``. Either may be absent on a report, so each has its own
    denominator."""
    scoped = ctx["clause"]
    rows = _fetch(store, f"""
        SELECT correct, first_pass FROM session_ground_truth
         WHERE reported_at >= ?
           {('AND ' + scoped) if scoped else ''}
         LIMIT {ROW_LIMIT}
    """, [ctx["cutoff_ms"], *ctx["params"]])
    verdicts = [bool(c) for c, _ in rows if c is not None]
    firsts = [bool(f) for _, f in rows if f is not None]
    return {
        "ground_truth_reported": len(rows),
        "ground_truth_judged": len(verdicts),
        "ground_truth_correct": sum(verdicts),
        "ground_truth_accuracy": _rate(sum(verdicts), len(verdicts)),
        "first_pass_known": len(firsts),
        "first_pass_count": sum(firsts),
        "first_pass_rate": _rate(sum(firsts), len(firsts)),
    }
