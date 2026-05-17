"""
clawmetry/eval_regression_replay.py — Phase 3 evals: regression-replay.

Closes the eval loop. Phase 1 (#1623) scored real sessions with an
LLM-as-judge. Phase 2 (#1626) added golden test suites for release gating.
Phase 3 answers the question the first two leave open: *is my agent
getting BETTER over time?*

The recipe: pull yesterday's failed sessions out of DuckDB, re-run each
one's ORIGINAL user input through the current agent + prompt config, and
compare the new outcome against the original. If a session that failed
last week passes this week, that's a real, measurable improvement — and
it goes straight onto the overview tile so the user can see their work
moving the needle.

Design constraints (composes with Phase 1 + Phase 2):
  * Reuse Phase 1's judge call (``eval_runner._call_judge``), Phase 2's
    agent shell-out (``eval_suite_runner._default_agent_call``), Phase 1
    rate limiter pattern. No new HTTP code paths.
  * Pull replay inputs from the local DuckDB ``events`` table, NOT from
    JSONL re-reads. Honours feedback_duckdb_first_rule + the bug-class
    gate in feedback_synthetic_tests_missed_real_event_shape (use real
    event shapes — same canonical type-union as eval_runner._PROMPT_*).
  * Cost guard. Replay COSTS API tokens (agent re-run + judge call) —
    every safety belt from Phase 1 applies double here. Default to
    ``manual`` invocation, no cron. Replays per-run are hard-capped.
  * Persistence in a new ``eval_regression_runs`` table; the schema
    migration bumps SCHEMA_VERSION to 10. Idempotent on
    (session_id, replayed_at).
  * Never crashes the daemon — every external call (agent, judge,
    store) is wrapped; failures degrade to a status row, not an
    exception.

Public API:
    find_failed_sessions(*, window_days=7, limit=50) -> list[dict]
    replay_session(session_id, *, agent_call=None) -> ReplayResult
    compare_outcomes(old_session, new_run) -> str   # improved/regressed/same
    run_regression(*, window_days=7, limit=10) -> RegressionRun
    regression_summary(*, window_days=7) -> dict    # for /api/evals/regression-summary
"""

from __future__ import annotations

import json
import logging
import os
import time
from dataclasses import dataclass, field, asdict
from typing import Any, Callable

log = logging.getLogger("clawmetry.eval_regression_replay")


# ── Config ─────────────────────────────────────────────────────────────────────

# Master kill switch. Default ON so the CLI is usable out of the box, but
# the scheduler will NEVER call us unless the user explicitly types
# ``clawmetry eval --regression`` (see feedback note in module docstring).
def is_enabled() -> bool:
    return os.environ.get("CLAWMETRY_EVALS_REGRESSION_ENABLED", "1") not in (
        "0", "false", "False", "",
    )


# Hard ceiling on a single regression run — every replay = 1 agent call +
# 1 judge call ≈ a few cents. 10 by default keeps a manual ``--regression``
# under a quarter even on Sonnet, and the user can raise it explicitly.
DEFAULT_REPLAY_BUDGET = int(os.environ.get("CLAWMETRY_EVALS_REGRESSION_MAX", "10"))

# How far back to look for failed sessions. 7 days mirrors the PRD ("last
# week's failures"). Bounded to 90 days because anything older almost
# certainly involves a config + version drift the replay can't reason about.
DEFAULT_WINDOW_DAYS = int(os.environ.get("CLAWMETRY_EVALS_REGRESSION_WINDOW_DAYS", "7"))

# "Failed" rubric. A session is replay-worthy if EITHER:
#   * outcome label says it broke (failed/escalated), OR
#   * the eval score is below this threshold.
# The two signals are deliberately additive — outcome is binary and noisy;
# eval score is graded and noisy in a different direction. Both together
# catch more real failures with fewer false positives.
LOW_SCORE_THRESHOLD = float(
    os.environ.get("CLAWMETRY_EVALS_REGRESSION_LOW_SCORE", "3.0")
)


# Same canonical event-type union as eval_runner. Centralising it would be
# nice; for now keep a copy + the comment that they must stay in sync. Both
# get bumped together when a new agent shape lands.
_PROMPT_EVENT_TYPES = (
    "prompt.submitted",
    "message",
    "user",
    "subagent:user",
)


# ── Data classes ──────────────────────────────────────────────────────────────


@dataclass
class FailedSession:
    """One row from ``find_failed_sessions``. Used as the input envelope
    for ``replay_session`` so callers don't re-query the store."""
    session_id: str
    title: str
    original_input: str
    original_outcome: str
    original_score: float | None
    last_active_at: str


@dataclass
class ReplayResult:
    """One executed replay. ``status`` is one of ``improved`` / ``regressed``
    / ``same`` / ``error``. ``error`` = the harness itself broke (agent
    crash, judge unavailable, missing original input)."""
    session_id: str
    status: str
    original_outcome: str
    new_outcome: str
    original_score: float | None
    new_score: float | None
    reason: str
    replayed_at: int  # epoch millis

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class RegressionRun:
    """Aggregate of one ``run_regression`` invocation."""
    ran_at: int
    window_days: int
    results: list[ReplayResult] = field(default_factory=list)

    @property
    def tested(self) -> int:
        return len(self.results)

    @property
    def improved(self) -> int:
        return sum(1 for r in self.results if r.status == "improved")

    @property
    def regressed(self) -> int:
        return sum(1 for r in self.results if r.status == "regressed")

    @property
    def same(self) -> int:
        return sum(1 for r in self.results if r.status == "same")

    @property
    def errored(self) -> int:
        return sum(1 for r in self.results if r.status == "error")


# ── Failed-session probe ──────────────────────────────────────────────────────


def _get_store(store: Any = None) -> Any:
    """Return the injected store or fall back to the daemon's singleton.
    Read-only — replay doesn't need write access until ``run_regression``
    persists results."""
    if store is not None:
        return store
    from clawmetry import local_store
    return local_store.get_store()


def _extract_first_prompt(events: list[dict[str, Any]]) -> str:
    """Pull the user's first prompt text from a session's event list.

    Honours the bug-class gate from feedback_synthetic_tests_missed_real_
    event_shape: probes all four real event shapes the v3 daemon emits,
    not just ``message``. Returns the first non-empty match in chronological
    order; falls back to "" so the caller can mark the replay as errored
    rather than re-running garbage.
    """
    # Events arrive newest-first from ``query_events``; we want chronological.
    for ev in reversed(events):
        et = ev.get("event_type") or ev.get("type") or ""
        if et not in _PROMPT_EVENT_TYPES:
            continue
        data = ev.get("data") or {}
        if isinstance(data, (bytes, bytearray)):
            try:
                data = json.loads(data.decode("utf-8"))
            except (ValueError, UnicodeDecodeError):
                continue
        if not isinstance(data, dict):
            continue
        for key in ("finalPromptText", "promptText", "text", "input", "content"):
            v = data.get(key)
            if isinstance(v, str) and v.strip():
                return v
        msg = data.get("message") if isinstance(data.get("message"), dict) else None
        if msg:
            c = msg.get("content")
            if isinstance(c, str) and c.strip():
                return c
            if isinstance(c, list):
                parts = [b.get("text", "") for b in c if isinstance(b, dict)]
                joined = "\n".join(p for p in parts if p)
                if joined.strip():
                    return joined
    return ""


def find_failed_sessions(
    *,
    window_days: int = DEFAULT_WINDOW_DAYS,
    limit: int = 50,
    store: Any = None,
) -> list[FailedSession]:
    """Return sessions worth replaying: outcome in (failed/escalated) OR
    eval_score below ``LOW_SCORE_THRESHOLD``, within the last
    ``window_days``. Newest first so the replay budget gets spent on the
    most relevant signals if it runs out.

    The original input is extracted in the same pass — saves the caller
    a follow-up ``query_events`` round trip per session.
    """
    store = _get_store(store)
    try:
        from datetime import datetime, timedelta, timezone
        cutoff = (datetime.now(timezone.utc) - timedelta(days=int(window_days))).isoformat()
    except Exception:
        cutoff = ""

    sql = """
        SELECT session_id, COALESCE(title, ''), COALESCE(outcome, ''),
               eval_score, COALESCE(last_active_at, started_at, '')
          FROM sessions
         WHERE (
                  outcome IN ('failed', 'escalated')
               OR (eval_score IS NOT NULL AND eval_score < ?)
              )
           AND (? = '' OR COALESCE(last_active_at, started_at, '') >= ?)
         ORDER BY COALESCE(last_active_at, started_at) DESC NULLS LAST
         LIMIT ?
    """
    try:
        rows = store._fetch(sql, [LOW_SCORE_THRESHOLD, cutoff, cutoff, int(limit)])
    except Exception as e:
        log.warning("regression: find_failed_sessions query failed: %s", e)
        return []

    out: list[FailedSession] = []
    for sid, title, outcome, score, last_active in rows:
        try:
            events = store.query_events(session_id=sid, limit=200)
        except Exception:
            events = []
        original_input = _extract_first_prompt(events)
        out.append(FailedSession(
            session_id=str(sid),
            title=str(title or ""),
            original_input=original_input,
            original_outcome=str(outcome or "unknown"),
            original_score=float(score) if score is not None else None,
            last_active_at=str(last_active or ""),
        ))
    return out


# ── Replay one session ────────────────────────────────────────────────────────


def _default_agent_call(test_input: str):
    """Lazy-import the Phase 2 agent shell-out so importing this module
    in environments without OpenClaw works for testing + summary reads."""
    from clawmetry.eval_suite_runner import _default_agent_call as inner
    return inner(test_input)


def _default_judge_call(model: str, prompt: str, *, timeout: float = 30.0) -> str:
    """Lazy import of Phase 1 judge call. Keeps httpx out of import-time
    requirements for the summary endpoint."""
    from clawmetry.eval_runner import _call_judge
    return _call_judge(model, prompt, timeout=timeout)


def replay_session(
    session_id: str,
    *,
    failed_session: FailedSession | None = None,
    agent_call: Callable[[str], Any] | None = None,
    judge_call: Callable[..., str] | None = None,
    judge_model: str = "claude-haiku-4-5",
    store: Any = None,
) -> ReplayResult:
    """Re-run one failed session's original input through the current
    agent + prompt config, score the new output, and return a comparison.

    All external callables are injectable so tests can drive deterministic
    paths without subprocesses or HTTP. The ``failed_session`` envelope
    can be passed in to skip the (already-done) original-input lookup.
    """
    replayed_at = int(time.time() * 1000)
    agent_call = agent_call or _default_agent_call
    judge_call = judge_call or _default_judge_call

    # Reload the failed session envelope if the caller didn't pass one.
    if failed_session is None:
        store_obj = _get_store(store)
        try:
            events = store_obj.query_events(session_id=session_id, limit=200)
        except Exception:
            events = []
        original_input = _extract_first_prompt(events)
        # Look up outcome + score off the sessions row.
        try:
            row = store_obj._fetch(
                "SELECT COALESCE(outcome, ''), eval_score FROM sessions WHERE session_id = ?",
                [session_id],
            )
            if row:
                orig_outcome = str(row[0][0] or "unknown")
                orig_score = float(row[0][1]) if row[0][1] is not None else None
            else:
                orig_outcome, orig_score = "unknown", None
        except Exception:
            orig_outcome, orig_score = "unknown", None
        failed_session = FailedSession(
            session_id=session_id,
            title="",
            original_input=original_input,
            original_outcome=orig_outcome,
            original_score=orig_score,
            last_active_at="",
        )

    if not failed_session.original_input.strip():
        return ReplayResult(
            session_id=session_id,
            status="error",
            original_outcome=failed_session.original_outcome,
            new_outcome="unknown",
            original_score=failed_session.original_score,
            new_score=None,
            reason="no original input extractable from session events",
            replayed_at=replayed_at,
        )

    # Re-run through the current agent. Defensive: ANY failure becomes an
    # error row rather than a daemon-crashing exception.
    try:
        response = agent_call(failed_session.original_input)
    except Exception as e:
        return ReplayResult(
            session_id=session_id,
            status="error",
            original_outcome=failed_session.original_outcome,
            new_outcome="failed",
            original_score=failed_session.original_score,
            new_score=None,
            reason=f"agent crashed: {type(e).__name__}: {e}",
            replayed_at=replayed_at,
        )

    if getattr(response, "error", None):
        return ReplayResult(
            session_id=session_id,
            status="error",
            original_outcome=failed_session.original_outcome,
            new_outcome=getattr(response, "outcome", "failed") or "failed",
            original_score=failed_session.original_score,
            new_score=None,
            reason=str(response.error),
            replayed_at=replayed_at,
        )

    # Score the new output with the Phase 1 judge.
    new_score: float | None = None
    judge_reason = ""
    try:
        from clawmetry.eval_runner import DEFAULT_RUBRIC, parse_score
        prompt = (
            str(DEFAULT_RUBRIC["prompt"])
            + "\n\n---\nTRANSCRIPT:\nUSER: "
            + failed_session.original_input.strip()
            + "\n\nASSISTANT: "
            + (getattr(response, "text", "") or "").strip()
            + "\n---"
        )
        reply = judge_call(judge_model, prompt, timeout=30.0)
        new_score, parsed_reason = parse_score(reply)
        if parsed_reason:
            judge_reason = parsed_reason
    except Exception as e:
        return ReplayResult(
            session_id=session_id,
            status="error",
            original_outcome=failed_session.original_outcome,
            new_outcome=getattr(response, "outcome", "success") or "success",
            original_score=failed_session.original_score,
            new_score=None,
            reason=f"judge unavailable: {type(e).__name__}: {e}",
            replayed_at=replayed_at,
        )

    new_outcome = str(getattr(response, "outcome", "success") or "success")
    status = compare_outcomes(
        old_outcome=failed_session.original_outcome,
        old_score=failed_session.original_score,
        new_outcome=new_outcome,
        new_score=new_score,
    )
    return ReplayResult(
        session_id=session_id,
        status=status,
        original_outcome=failed_session.original_outcome,
        new_outcome=new_outcome,
        original_score=failed_session.original_score,
        new_score=new_score,
        reason=judge_reason or f"{failed_session.original_outcome} -> {new_outcome}",
        replayed_at=replayed_at,
    )


def compare_outcomes(
    *,
    old_outcome: str,
    old_score: float | None,
    new_outcome: str,
    new_score: float | None,
) -> str:
    """Classify a replay as improved / regressed / same.

    Rules, in order of precedence:
      1. Outcome transition wins. failed/escalated -> success/any is an
         improvement; the reverse is a regression. (Outcome is the
         human-meaningful signal; the eval score is supporting evidence.)
      2. If outcome is unchanged, fall back to score delta with a 0.5
         dead band so judge noise (Haiku is not bit-exact) doesn't get
         counted as a real swing.
      3. Anything ambiguous (one side missing, no score change) → ``same``.
    """
    _failed = ("failed", "escalated")
    old_failed = old_outcome in _failed
    new_failed = new_outcome in _failed
    if old_failed and not new_failed:
        return "improved"
    if not old_failed and new_failed:
        return "regressed"
    # Outcome unchanged — try score delta.
    if old_score is not None and new_score is not None:
        delta = new_score - old_score
        if delta >= 0.5:
            return "improved"
        if delta <= -0.5:
            return "regressed"
    return "same"


# ── Persistence ───────────────────────────────────────────────────────────────


def _persist_result(result: ReplayResult, *, store: Any = None) -> None:
    """Write one ``ReplayResult`` row to ``eval_regression_runs``. Best-
    effort — a missing daemon or RO connection logs a warning and returns
    without crashing the CLI."""
    if store is None:
        try:
            from clawmetry import local_store
            store = local_store.get_store()
        except Exception as e:
            log.warning("regression: local_store unavailable: %s", e)
            return
    persister = getattr(store, "persist_eval_regression_run", None)
    if persister is None:
        log.warning(
            "regression: store has no persist_eval_regression_run "
            "(older schema? expected v10)"
        )
        return
    try:
        persister(
            session_id=result.session_id,
            status=result.status,
            original_outcome=result.original_outcome,
            new_outcome=result.new_outcome,
            original_score=result.original_score,
            new_score=result.new_score,
            reason=result.reason,
            replayed_at=result.replayed_at,
        )
    except Exception as e:
        log.warning("regression: persist row %s failed: %s", result.session_id, e)


# ── Top-level driver ──────────────────────────────────────────────────────────


def run_regression(
    *,
    window_days: int = DEFAULT_WINDOW_DAYS,
    limit: int = DEFAULT_REPLAY_BUDGET,
    agent_call: Callable[[str], Any] | None = None,
    judge_call: Callable[..., str] | None = None,
    judge_model: str = "claude-haiku-4-5",
    store: Any = None,
    persist: bool = True,
) -> RegressionRun:
    """End-to-end: find failed sessions, replay each, persist results.

    ``limit`` is a HARD ceiling on replays per invocation — this is the
    cost guard. Default 10 keeps a single ``--regression`` invocation
    under a few cents even on Sonnet. The user can override with
    ``CLAWMETRY_EVALS_REGRESSION_MAX`` if they're confident in their bill.
    """
    ran_at = int(time.time() * 1000)
    run = RegressionRun(ran_at=ran_at, window_days=int(window_days))

    if not is_enabled():
        log.info("regression: CLAWMETRY_EVALS_REGRESSION_ENABLED=0, skipping")
        return run

    failed = find_failed_sessions(
        window_days=window_days,
        limit=max(int(limit), 1),
        store=store,
    )
    if not failed:
        return run

    for fs in failed[: int(limit)]:
        try:
            result = replay_session(
                fs.session_id,
                failed_session=fs,
                agent_call=agent_call,
                judge_call=judge_call,
                judge_model=judge_model,
                store=store,
            )
        except Exception as e:
            log.warning("regression: replay_session(%s) crashed: %s", fs.session_id, e)
            result = ReplayResult(
                session_id=fs.session_id,
                status="error",
                original_outcome=fs.original_outcome,
                new_outcome="unknown",
                original_score=fs.original_score,
                new_score=None,
                reason=f"replay crashed: {type(e).__name__}: {e}",
                replayed_at=int(time.time() * 1000),
            )
        run.results.append(result)
        if persist:
            _persist_result(result, store=store)
    return run


# ── Summary surface (drives /api/evals/regression-summary + UI tile) ──────────


def regression_summary(
    *,
    window_days: int = DEFAULT_WINDOW_DAYS,
    store: Any = None,
) -> dict[str, Any]:
    """Aggregate persisted replay rows over the recent window. Drives
    the ``/api/evals/regression-summary`` endpoint and the overview tile's
    "Regression: X fixed" mini-line.

    Returns ``{tested, improved, regressed, same, errored, window_days,
    last_run_at}``. Empty payload (all zeros + ``last_run_at: None``) on
    a fresh install where no regression has run yet.
    """
    payload: dict[str, Any] = {
        "tested":       0,
        "improved":     0,
        "regressed":    0,
        "same":         0,
        "errored":      0,
        "window_days":  int(window_days),
        "last_run_at":  None,
    }
    try:
        store_obj = _get_store(store)
    except Exception as e:
        log.warning("regression: summary store unavailable: %s", e)
        return payload
    try:
        from datetime import datetime, timedelta, timezone
        cutoff_ms = int(
            (datetime.now(timezone.utc) - timedelta(days=int(window_days))).timestamp() * 1000
        )
    except Exception:
        cutoff_ms = 0
    try:
        rows = store_obj._fetch(
            """
            SELECT status, COUNT(*) AS n, MAX(replayed_at) AS last_ms
              FROM eval_regression_runs
             WHERE replayed_at >= ?
             GROUP BY status
            """,
            [cutoff_ms],
        )
    except Exception as e:
        log.warning("regression: summary query failed: %s", e)
        return payload
    last_ms = 0
    for status, n, lm in rows:
        n = int(n or 0)
        payload["tested"] += n
        if status in ("improved", "regressed", "same", "errored"):
            payload[status] += n
        try:
            lm_int = int(lm or 0)
            if lm_int > last_ms:
                last_ms = lm_int
        except (TypeError, ValueError):
            pass
    payload["last_run_at"] = last_ms or None
    return payload
