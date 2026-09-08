"""Local alert-rule evaluator — pure logic, no I/O (PRD #779 PR-D part 2).

Used by the OSS daemon to walk DuckDB events against the cached alert rules
that the cloud relays via the heartbeat ``cache_pushes`` channel, fire matches
locally, and POST the result to the cloud's ``/api/cloud/alerts/dispatch``
endpoint for notification fan-out.

Why a separate module:
* Keeps the evaluator pure (rules + events in, matches + state mutation out)
  so the unit tests can exercise every condition shape without touching
  DuckDB, the network, or daemon globals.
* Lets ``clawmetry/sync.py`` stay focused on I/O (DuckDB read, HTTP POST,
  state persistence). Closes the architectural inversion called out in the
  2026-05-13 audit (P0 #1 + #2 — alerts were 100% cloud-evaluated and the
  local trigger had never fired in this daemon's lifetime).

Rule shape (mirrors what the cloud relays into ``alert_rules.condition_json``;
see ``clawmetry/local_store.py`` and ``clawmetry/sync.py:_apply_pending_write``):

    {
      "id": "<rule-id>",
      "name": "<human label>",
      "enabled": true,
      "condition_json": {
        # PRD #779 spec types (preferred — event-stream native):
        "type": "count_over_threshold" | "error_rate" | "tool_call_pattern",
        # Common fields:
        "event_type": "<event_type>",            # which events to count
        "threshold": <int|float>,                 # firing line
        "window_sec": <int>,                      # rolling window
        "cooldown_sec": <int>,                    # min seconds between fires
        # tool_call_pattern only:
        "tool_name": "<name substring or regex-lite>",
        "arg_pattern": "<substring matched against str(data)>",
        # legacy cloud aliases — best-effort mapping (see _normalise_rule):
        "alert_type": "daily_spend" | "session_cost" | "token_velocity"
                    | "error_rate" | "cron_failure" | "node_offline",
        "threshold_value": <int|float>,
      },
      ...other fields are passed through untouched
    }

The evaluator never raises on bad input — a malformed rule is logged once and
skipped. The daemon must keep ticking even if one cloud-authored rule is
broken.
"""
from __future__ import annotations

import logging
import re
import time
from datetime import datetime, timezone
from typing import Any

log = logging.getLogger("clawmetry.alert_evaluator")


# ── Defaults ──────────────────────────────────────────────────────────────────
# Sensible fallbacks when a rule omits these fields. Tuned for the common case
# (cost / error / velocity rules running on a single-developer node).
DEFAULT_WINDOW_SEC = 300        # 5-minute rolling window
DEFAULT_COOLDOWN_SEC = 3600     # 1-hour debounce (matches cloud `_debounce_ok`)


# Map cloud-side ``alert_type`` strings to PRD spec evaluator types.
# Anything not in this map is treated as ``count_over_threshold`` against the
# rule's ``event_type`` field, which is a safe under-fire default — it won't
# spam channels with bogus alerts, just under-cover a niche rule shape until
# we wire its evaluator below. TODO(PRD #779 part 3): add evaluators for
# ``daily_spend`` (sum cost over UTC day), ``session_cost`` (per-session
# rollup), ``cron_failure`` (consecutive cron exit_code != 0).
_LEGACY_ALERT_TYPE_MAP = {
    "error_rate":      "error_rate",
    "token_velocity":  "count_over_threshold",  # threshold tokens/min
    "node_offline":    "count_over_threshold",  # treat absence as count==0
    "daily_spend":     "count_over_threshold",  # TODO real cost-sum impl
    "session_cost":    "count_over_threshold",  # TODO real per-session impl
    "cron_failure":    "count_over_threshold",  # TODO real cron impl
    # Eval->monitor loop: the alert builder POSTs these as ``alert_type`` (no
    # explicit ``type``). They evaluate over the per-session quality slice
    # (sessions.eval_score / sessions.outcome) the daemon pre-fetches, NOT
    # the event stream, so they map to themselves and dispatch in
    # ``_evaluate_one`` below.
    "eval_score_below":     "eval_score_below",
    "outcome_failure_rate": "outcome_failure_rate",
    # Harness Engineering "Watch $/done": cost per finished job crossed a
    # dollar threshold. Quality-slice fed, maps to itself.
    "dollars_per_done_above": "dollars_per_done_above",
    # Behaviour Signals (WO-58): a named signal's rate over a window crossed
    # a threshold. Fed by the ``signal_turns`` / ``signal_matches`` tables the
    # daemon fills (clawmetry/behaviour_signals.py), never by matched text.
    "signal_rate_above": "signal_rate_above",
    # Silent-failure rule types (fed by the Guard detectors' loop_signals rows
    # and the event stream's cost column). Map to themselves.
    "stuck_session":    "stuck_session",
    "rate_limited":     "rate_limited",
    "blocked_on_user":  "blocked_on_user",
    "agent_attention":  "agent_attention",
    "cost_velocity":    "cost_velocity",
}

# Rule types that read the behaviour-signal rate slice. Like the quality
# types, the daemon only queries that slice when such a rule is enabled.
SIGNAL_RULE_TYPES = frozenset({"signal_rate_above"})
DEFAULT_SIGNAL_WINDOW_MINUTES = 24 * 60
DEFAULT_SIGNAL_MIN_TURNS = 20

# Rule types that read the Guard detectors' ``loop_signals`` slice (the
# daemon pre-fetches it only when one of these rules is enabled). Each maps to
# the detector kinds it fires on; ``condition.kinds`` may narrow or widen it.
STUCK_KINDS = frozenset({"stuck_loop", "no_progress", "repeated_tool_failure",
                         "action_discrepancy"})
ATTENTION_RULE_KINDS: dict[str, frozenset] = {
    "stuck_session":   STUCK_KINDS,
    "rate_limited":    frozenset({"rate_limited"}),
    "blocked_on_user": frozenset({"blocked_on_user"}),
    # The seed rule: anything a person needs to step in for.
    "agent_attention": STUCK_KINDS | {"rate_limited", "blocked_on_user", "crashed"},
}
ATTENTION_RULE_TYPES = frozenset(ATTENTION_RULE_KINDS)
DEFAULT_ATTENTION_WINDOW_MINUTES = 30
_ATTENTION_SEVERITY_RANK = {"info": 0, "warning": 1, "critical": 2}

# Rule types that read the per-session quality slice (eval scores + outcome
# labels) instead of the raw event stream. The daemon only bothers to query
# that slice when at least one such rule is enabled (it is otherwise wasted
# DuckDB work — see ``sync.py:evaluate_alerts``).
QUALITY_RULE_TYPES = frozenset({"eval_score_below", "outcome_failure_rate",
                                "dollars_per_done_above"})

# Default window + min-sample floors for the quality rules, used when the
# rule body omits them. Tuned so a single low-scoring session can't trip an
# alert (``min_sessions``) and the window is long enough to gather a few
# scored/classified sessions on a normal node.
DEFAULT_QUALITY_WINDOW_MINUTES = 60
DEFAULT_QUALITY_MIN_SESSIONS = 3


# ── Public API ────────────────────────────────────────────────────────────────


# Session-id prefix -> runtime scoping (founder 2026-08-03: rules are
# runtime-scoped by default). Pure helper: a namespaced session id like
# "copilot:<uuid>" belongs to that runtime; anything without a known family
# prefix is OpenClaw. The known-prefix set comes from
# ``clawmetry.entitlements.ALL_RUNTIMES`` (a constants frozenset, no I/O);
# if that import ever fails the helper degrades to "prefix as-is".
def _session_runtime(sid: Any) -> str:
    sid = str(sid or "")
    if ":" not in sid:
        return "openclaw"
    head = sid.split(":", 1)[0]
    try:
        from clawmetry.entitlements import ALL_RUNTIMES
        return head if head in ALL_RUNTIMES else "openclaw"
    except ImportError:
        return head or "openclaw"


def _rule_runtime(raw_rule: dict[str, Any]) -> str:
    """A rule's runtime scope: the row's ``runtime`` column (local SQLite
    bridge) or ``condition_json.runtime`` (cloud-authored), else 'all'."""
    rt = raw_rule.get("runtime")
    if not rt:
        cond = raw_rule.get("condition_json")
        if isinstance(cond, dict):
            rt = cond.get("runtime")
    rt = str(rt or "all").strip().lower()
    return rt or "all"


def evaluate(
    rules: list[dict[str, Any]] | None,
    events: list[dict[str, Any]] | None,
    last_eval_state: dict[str, Any] | None,
    quality: dict[str, Any] | None = None,
    quality_by_runtime: dict[str, dict[str, Any]] | None = None,
    signals: dict[str, Any] | None = None,
    signals_by_runtime: dict[str, dict[str, Any]] | None = None,
    loop_signals: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    """Pure evaluator. Walks ``events`` against ``rules``, returns matches.

    ``signals`` / ``signals_by_runtime``: the behaviour-signal rate slice for
    the ``signal_rate_above`` rule type, keyed ``{rule_id: rate_window}``
    (each ``rate_window`` is ``LocalStore.query_signal_rate_window``'s dict).
    ``None`` means the daemon did not fetch it and those rules no-fire.

    ``loop_signals`` is the ``loop_signals`` slice (``query_recent_loop_signals``
    rows) the silent-failure rule types read (``stuck_session`` /
    ``rate_limited`` / ``blocked_on_user`` / ``agent_attention``). ``None``
    means the daemon did not fetch it, and those types no-fire.

    No I/O. ``last_eval_state`` is mutated in place to remember the most
    recent fire time per rule so a second call within the cooldown window
    won't re-fire the same rule. Used by the daemon loop and unit tests
    alike.

    Args:
        rules: rows from ``local_store.query_alert_rules()``. Each rule is the
            dict shape stored in DuckDB (``id``, ``name``, ``enabled``,
            ``condition_json`` decoded back to a dict, etc.). ``None`` and
            empty lists are tolerated.
        events: rows from ``local_store.query_events()`` ordered most-recent
            first. ``None`` and empty lists are tolerated.
        quality: the per-session quality slice from
            ``local_store.query_session_quality_window()`` — drives the
            ``eval_score_below`` + ``outcome_failure_rate`` rule types (the
            eval->monitor loop). ``None`` means the daemon didn't fetch it
            (no quality rule enabled, or empty store) — those rule types then
            no-fire instead of crashing.
        last_eval_state: per-rule cooldown bookkeeping. Schema:
            ``{rule_id: {"last_fired_ts": <epoch_seconds>, "last_event_id": <id>}}``.
            Mutated in place. ``None`` raises (callers should pass an empty
            dict instead — explicit > silent).

    Returns:
        List of match dicts ready for the dispatch POST. Each match has:
            ``rule``: the rule dict (so dispatcher can read id / name / channels)
            ``event``: the triggering event row (so dispatcher can attach
                event_id + ts to the cloud notification)
            ``summary``: short human string ("rule X fired: 7 events of …")
            ``metadata``: numeric / contextual fields the cloud may want
    """
    if last_eval_state is None:
        raise TypeError("last_eval_state must be a dict (got None)")
    if not rules:
        return []
    if not events:
        events = []

    # Sort events oldest-first so windowed counts are deterministic and the
    # "triggering" event is the one that crossed the threshold (not the most
    # recent of an already-firing window). Stable sort on the ``ts`` ISO
    # string is correct for our timestamp shape (zero-padded UTC isoformat).
    events_chrono = sorted(events, key=lambda e: (e.get("ts") or "", e.get("id") or ""))

    matches: list[dict[str, Any]] = []
    now = time.time()
    for raw_rule in rules:
        try:
            rule = _normalise_rule(raw_rule)
        except Exception as e:
            log.warning("alerts: skipping malformed rule %r: %s", raw_rule.get("id"), e)
            continue
        if not rule:
            continue
        if not rule.get("enabled", True):
            continue
        rid = rule["id"]
        memo = last_eval_state.setdefault(rid, {})
        cooldown = float(rule.get("cooldown_sec") or DEFAULT_COOLDOWN_SEC)
        last_fired = float(memo.get("last_fired_ts") or 0)
        if cooldown > 0 and (now - last_fired) < cooldown:
            # Within cooldown — skip even if matching events exist. Cooldown
            # protects channels from notification storms.
            continue

        rule_rt = _rule_runtime(raw_rule)
        rule_loop_signals = loop_signals
        if rule_rt != "all":
            rule_events = [e for e in events_chrono
                           if _session_runtime(e.get("session_id")) == rule_rt]
            if loop_signals is not None:
                rule_loop_signals = [
                    s for s in loop_signals
                    if _session_runtime(s.get("session_id")) == rule_rt]
            # Quality slices are AGGREGATES (no session ids), so a scoped
            # rule needs a per-runtime slice pre-fetched by the caller.
            # Missing slice -> None -> quality rule types no-fire for that
            # tick (honest under-fire; never a node-wide number under a
            # runtime label).
            rule_quality = (quality_by_runtime or {}).get(rule_rt)
            rule_signals = ((signals_by_runtime or {}).get(rule_rt) or {})
        else:
            rule_events = events_chrono
            rule_quality = quality
            rule_signals = signals or {}

        try:
            match = _evaluate_one(rule, rule_events, rule_quality,
                                  signal_window=(rule_signals or {}).get(rid),
                                  loop_signals=rule_loop_signals)
        except Exception as e:
            log.warning("alerts: rule %s evaluator errored: %s", rid, e)
            continue
        if not match:
            continue

        # Dedup: if we already fired on this exact event id, don't re-fire.
        # Cooldown above usually catches this; the event-id check is the
        # belt-and-braces case where cooldown was 0 or expired and the same
        # event window is still being walked.
        evt_id = (match.get("event") or {}).get("id")
        if evt_id and memo.get("last_event_id") == evt_id:
            continue

        memo["last_fired_ts"] = now
        if evt_id:
            memo["last_event_id"] = evt_id

        matches.append({
            "rule":     raw_rule,        # pass through the unmodified row
            "event":    match["event"],
            "summary":  match["summary"],
            "metadata": match.get("metadata", {}),
        })

    return matches


# ── Rule normalisation ────────────────────────────────────────────────────────


def _normalise_rule(raw_rule: dict[str, Any]) -> dict[str, Any] | None:
    """Project a raw DuckDB ``alert_rules`` row into the evaluator's expected
    shape. Reads ``condition_json`` (the cloud rule body) and surfaces the
    fields the evaluator branches on. Returns ``None`` for rules that are too
    malformed to even attempt (no id, no condition body)."""
    rid = raw_rule.get("id")
    if not rid:
        return None
    cond = raw_rule.get("condition_json")
    if isinstance(cond, str):
        # Defensive — query_alert_rules already json-decodes, but if a caller
        # passes a raw string we try once. A non-JSON string means the row
        # is corrupt; refuse it.
        import json as _json
        try:
            cond = _json.loads(cond)
        except Exception:
            return None
    if not isinstance(cond, dict):
        return None

    rule_type = cond.get("type")
    if not rule_type:
        # Legacy cloud rule — translate ``alert_type`` to evaluator type.
        legacy = (cond.get("alert_type") or "").strip()
        if not legacy:
            # Rule has neither a `type` nor a legacy `alert_type` — there's
            # no condition to evaluate. Treat as malformed and skip rather
            # than firing on every event.
            return None
        rule_type = _LEGACY_ALERT_TYPE_MAP.get(legacy, "count_over_threshold")

    # Threshold may be under either name. Accept either.
    threshold = cond.get("threshold")
    if threshold is None:
        threshold = cond.get("threshold_value")
    if threshold is None:
        threshold = 1  # Default — fire on the first matching event.

    # Convert threshold to a numeric (cloud may send strings from the form).
    try:
        threshold = float(threshold)
    except (TypeError, ValueError):
        threshold = 1.0

    return {
        "id":           str(rid),
        "name":         raw_rule.get("name") or cond.get("name") or "",
        "enabled":      bool(raw_rule.get("enabled", True)),
        "type":         rule_type,
        "event_type":   cond.get("event_type"),
        "threshold":    threshold,
        "window_sec":   _coerce_int(cond.get("window_sec"), DEFAULT_WINDOW_SEC),
        "cooldown_sec": _coerce_int(cond.get("cooldown_sec"), DEFAULT_COOLDOWN_SEC),
        "tool_name":    cond.get("tool_name"),
        "arg_pattern":  cond.get("arg_pattern"),
        # Pass condition through so evaluators that need niche fields (channel
        # ids, error-event-type list, …) can read them without a re-decode.
        "condition":    cond,
    }


def _coerce_int(value: Any, default: int) -> int:
    if value is None:
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


# ── Per-type evaluators ───────────────────────────────────────────────────────


def _evaluate_one(
    rule: dict[str, Any],
    events_chrono: list[dict[str, Any]],
    quality: dict[str, Any] | None = None,
    signal_window: dict[str, Any] | None = None,
    loop_signals: list[dict[str, Any]] | None = None,
) -> dict[str, Any] | None:
    """Dispatch on ``rule['type']``. Returns the match dict (rule-agnostic
    shape) or ``None`` when the rule didn't fire."""
    rt = rule.get("type")
    if rt == "signal_rate_above":
        return _eval_signal_rate_above(rule, signal_window)
    if rt in ATTENTION_RULE_TYPES:
        return _eval_signal_kinds(rule, loop_signals)
    if rt == "cost_velocity":
        return _eval_cost_velocity(rule, events_chrono)
    if rt == "count_over_threshold":
        return _eval_count_over_threshold(rule, events_chrono)
    if rt == "error_rate":
        return _eval_error_rate(rule, events_chrono)
    if rt == "tool_call_pattern":
        return _eval_tool_call_pattern(rule, events_chrono)
    if rt == "eval_score_below":
        return _eval_eval_score_below(rule, quality)
    if rt == "outcome_failure_rate":
        return _eval_outcome_failure_rate(rule, quality)
    if rt == "dollars_per_done_above":
        return _eval_dollars_per_done(rule, quality)
    # Unknown type — log once and skip. (PRD says: leave a TODO. Here we
    # explicitly under-fire instead of mis-firing.)
    log.debug("alerts: unsupported rule type %r — skipped (rule_id=%s)",
              rt, rule.get("id"))
    return None


def _quality_window_minutes(rule: dict[str, Any]) -> int:
    """Window for a quality rule in minutes. Prefer an explicit
    ``window_minutes`` in the condition body; otherwise derive from
    ``window_sec`` (the shared field other rule types use); else default."""
    cond = rule.get("condition") or {}
    wm = cond.get("window_minutes")
    if wm is not None:
        return _coerce_int(wm, DEFAULT_QUALITY_WINDOW_MINUTES)
    # ``window_sec`` is normalised onto the rule already; convert when the
    # author set it instead of window_minutes.
    if cond.get("window_sec") is not None:
        secs = _coerce_int(cond.get("window_sec"), DEFAULT_QUALITY_WINDOW_MINUTES * 60)
        return max(1, secs // 60)
    return DEFAULT_QUALITY_WINDOW_MINUTES


def _quality_min_sessions(rule: dict[str, Any]) -> int:
    cond = rule.get("condition") or {}
    return max(1, _coerce_int(cond.get("min_sessions"), DEFAULT_QUALITY_MIN_SESSIONS))


def _quality_pseudo_event(rule_type: str, window_minutes: int) -> dict[str, Any]:
    """Quality rules fire on a window aggregate, not a single event, but the
    dispatch payload + dedup memo read ``match['event']['id']``. Synthesise a
    deterministic id from (type, window, current minute) so the dispatcher
    has a stable handle and the cooldown / event-id dedup still work."""
    minute_bucket = int(time.time() // 60)
    return {
        "id": f"quality:{rule_type}:{window_minutes}m:{minute_bucket}",
        "event_type": rule_type,
        "ts": datetime.now(timezone.utc).isoformat(),
        "data": {},
    }


def _eval_eval_score_below(
    rule: dict[str, Any],
    quality: dict[str, Any] | None,
) -> dict[str, Any] | None:
    """Fire when the average ``sessions.eval_score`` over the recent window
    drops BELOW ``threshold`` (0-5 scale). Requires at least ``min_sessions``
    scored sessions in the window so a single bad sample can't trip it.

    ``quality`` is ``query_session_quality_window()``'s result. ``None`` or an
    empty/un-scored store -> no fire (degrade gracefully, never crash)."""
    if not isinstance(quality, dict):
        return None
    threshold = rule.get("threshold")
    if threshold is None:
        return None
    min_sessions = _quality_min_sessions(rule)
    window_minutes = _quality_window_minutes(rule)

    count = int(quality.get("eval_count") or 0)
    avg = quality.get("eval_avg")
    if count < min_sessions or avg is None:
        return None
    if avg >= threshold:
        return None

    return {
        "event": _quality_pseudo_event("eval_score_below", window_minutes),
        "summary": (f"rule fired: avg eval score {avg:.2f} over {count} "
                    f"session(s) in {window_minutes}m "
                    f"(threshold={threshold:g})"),
        "metadata": {
            "avg_score":      round(float(avg), 3),
            "threshold":      float(threshold),
            "session_count":  count,
            "min_sessions":   min_sessions,
            "window_minutes": window_minutes,
        },
    }


def _eval_outcome_failure_rate(
    rule: dict[str, Any],
    quality: dict[str, Any] | None,
) -> dict[str, Any] | None:
    """Fire when failure-ish outcomes (``failed`` / ``tool_call_stuck`` /
    ``cognitive_loop``) as a fraction of classified non-``ongoing`` sessions
    in the window EXCEED ``threshold`` percent. Requires at least
    ``min_sessions`` classified sessions so a single failure can't trip it.

    ``threshold`` here is a percent (0-100) — the alert builder's unit. We
    accept a fraction in [0,1] too (if the author sent 0.2 meaning 20%)."""
    if not isinstance(quality, dict):
        return None
    threshold = rule.get("threshold")
    if threshold is None:
        return None
    # The builder sends a percent (e.g. 20). A value <= 1 is read as a
    # fraction (0.2 == 20%); anything larger is a percent and divided by 100.
    threshold = float(threshold)
    threshold_frac = threshold if threshold <= 1.0 else threshold / 100.0
    if threshold_frac <= 0:
        return None
    min_sessions = _quality_min_sessions(rule)
    window_minutes = _quality_window_minutes(rule)

    total = int(quality.get("classified_total") or 0)
    failed = int(quality.get("failed_count") or 0)
    if total < min_sessions:
        return None
    rate = quality.get("failure_rate")
    if rate is None:
        rate = (failed / total) if total else 0.0
    if rate <= threshold_frac:
        return None

    return {
        "event": _quality_pseudo_event("outcome_failure_rate", window_minutes),
        "summary": (f"rule fired: outcome failure rate {rate:.1%} "
                    f"({failed}/{total}) in {window_minutes}m "
                    f"(threshold={threshold_frac:.1%})"),
        "metadata": {
            "failure_rate":     round(float(rate), 4),
            "failed_count":     failed,
            "classified_total": total,
            "threshold_pct":    round(threshold_frac * 100, 2),
            "outcome_counts":   quality.get("outcome_counts") or {},
            "min_sessions":     min_sessions,
            "window_minutes":   window_minutes,
        },
    }


def signal_rule_fields(rule: dict[str, Any]) -> dict[str, Any]:
    """``{signal, threshold, window_minutes, min_turns}`` for a
    ``signal_rate_above`` rule, reading the normalised rule and its raw
    condition body. ``threshold`` is a fraction in [0, 1]; a percent (> 1)
    is divided by 100 the way ``outcome_failure_rate`` does."""
    cond = rule.get("condition") or {}
    sig = str(cond.get("signal") or rule.get("signal") or "").strip()
    thr = rule.get("threshold")
    if thr is None:
        thr = cond.get("threshold", cond.get("threshold_value"))
    try:
        thr = float(thr) if thr is not None else None
    except (TypeError, ValueError):
        thr = None
    if thr is not None and thr > 1.0:
        thr = thr / 100.0
    wm = cond.get("window_minutes")
    if wm is None and cond.get("window_sec") is not None:
        wm = _coerce_int(cond.get("window_sec"), DEFAULT_SIGNAL_WINDOW_MINUTES * 60) // 60
    return {
        "signal": sig,
        "threshold": thr,
        "window_minutes": max(1, _coerce_int(wm, DEFAULT_SIGNAL_WINDOW_MINUTES)),
        "min_turns": max(1, _coerce_int(cond.get("min_turns"), DEFAULT_SIGNAL_MIN_TURNS)),
    }


def _eval_signal_rate_above(
    rule: dict[str, Any],
    window: dict[str, Any] | None,
) -> dict[str, Any] | None:
    """Fire when a behaviour signal's rate over the window EXCEEDS
    ``threshold`` (fraction 0..1) with at least ``min_turns`` eligible turns,
    so one session cannot trip it. ``window`` is
    ``LocalStore.query_signal_rate_window``'s dict for this rule; ``None`` or
    an empty store -> no fire. The payload names the signal, the rate, the
    window, the runtime and the model. It never carries matched text."""
    if not isinstance(window, dict) or not window:
        return None
    f = signal_rule_fields(rule)
    if not f["signal"] or f["threshold"] is None or f["threshold"] < 0:
        return None
    turns = int(window.get("turns") or 0)
    if turns < f["min_turns"]:
        return None
    rate = window.get("rate")
    if rate is None:
        return None
    rate = float(rate)
    if rate <= f["threshold"]:
        return None
    wm = int(window.get("window_minutes") or f["window_minutes"])
    runtime = str(window.get("runtime") or "all")
    model = window.get("top_model") or "unknown"
    return {
        "event": _quality_pseudo_event(f"signal_rate_above:{f['signal']}", wm),
        "summary": (f"rule fired: {f['signal']} rate {rate:.1%} "
                    f"({int(window.get('matches') or 0)}/{turns} turns) in {wm}m "
                    f"on {runtime} (threshold={f['threshold']:.1%})"),
        "metadata": {
            "signal":         f["signal"],
            "rate":           round(rate, 4),
            "matches":        int(window.get("matches") or 0),
            "turns":          turns,
            "threshold":      round(f["threshold"], 4),
            "window_minutes": wm,
            "window":         f"{wm}m",
            "runtime":        runtime,
            "model":          model,
            "min_turns":      f["min_turns"],
        },
    }


def _eval_dollars_per_done(
    rule: dict[str, Any],
    quality: dict[str, Any] | None,
) -> dict[str, Any] | None:
    """Fire when the window's cost per finished job EXCEEDS ``threshold``
    dollars: total spend of classified terminal sessions divided by the
    sessions that ended ``success``. Basis is the classified cohort (the
    Harness Engineering tab's headline uses the measurable cohort; the fired
    alert names its basis so the two are never conflated). With zero
    successes there is no price, so the rule under-fires rather than
    dividing by hope; ``min_sessions`` keeps one expensive run from
    tripping it."""
    if not isinstance(quality, dict):
        return None
    threshold = rule.get("threshold")
    if threshold is None:
        return None
    try:
        threshold = float(threshold)
    except (TypeError, ValueError):
        return None
    if threshold <= 0:
        return None
    min_sessions = _quality_min_sessions(rule)
    window_minutes = _quality_window_minutes(rule)

    total = int(quality.get("classified_total") or 0)
    if total < min_sessions:
        return None
    done = int((quality.get("outcome_counts") or {}).get("success") or 0)
    if done <= 0:
        return None
    try:
        spend = float(quality.get("window_spend_usd") or 0.0)
    except (TypeError, ValueError):
        return None
    dpd = spend / done
    if dpd <= threshold:
        return None

    return {
        "event": _quality_pseudo_event("dollars_per_done_above", window_minutes),
        "summary": (f"rule fired: cost per finished job ${dpd:.2f} "
                    f"(${spend:.2f} across {total} classified sessions, "
                    f"{done} finished) in {window_minutes}m "
                    f"(threshold=${threshold:.2f}; basis: classified sessions)"),
        "metadata": {
            "dollars_per_done":  round(dpd, 2),
            "window_spend_usd":  round(spend, 2),
            "done_count":        done,
            "classified_total":  total,
            "threshold_usd":     round(threshold, 2),
            "basis":             "classified_sessions",
            "min_sessions":      min_sessions,
            "window_minutes":    window_minutes,
        },
    }


def _signal_kind(sig: dict[str, Any]) -> str:
    """Detector kind of one ``loop_signals`` row: ``details.kind`` when set,
    else derived from the ``daemon_detect_<kind>`` signature, else the
    no-progress stuck detector's ``daemon_stuck`` -> ``stuck_loop``."""
    det = sig.get("details")
    if isinstance(det, (bytes, bytearray, str)):
        try:
            import json as _json
            det = _json.loads(det if isinstance(det, str) else bytes(det).decode("utf-8", "replace"))
        except Exception:
            det = None
    if isinstance(det, dict) and det.get("kind"):
        return str(det.get("kind"))
    sigt = str(sig.get("signature") or "")
    if sigt.startswith("daemon_detect_"):
        return sigt[len("daemon_detect_"):]
    if sigt == "daemon_stuck":
        return "stuck_loop"
    return ""


def _eval_signal_kinds(
    rule: dict[str, Any],
    signals: list[dict[str, Any]] | None,
) -> dict[str, Any] | None:
    """Fire when a Guard detector wrote a ``loop_signals`` row of one of the
    rule's kinds, at or above ``min_severity`` (default warning), inside
    ``window_minutes`` (default 30). ``threshold`` = how many distinct
    sessions must be affected (default 1). Reads the slice the daemon
    pre-fetched; ``None`` -> no fire, never a crash."""
    if not signals:
        return None
    cond = rule.get("condition") or {}
    kinds = ATTENTION_RULE_KINDS.get(str(rule.get("type") or ""), frozenset())
    extra = cond.get("kinds")
    if isinstance(extra, (list, tuple)) and extra:
        kinds = frozenset(str(k) for k in extra)
    min_sev = _ATTENTION_SEVERITY_RANK.get(str(cond.get("min_severity") or "warning").lower(), 1)
    window_min = _coerce_int(cond.get("window_minutes"), DEFAULT_ATTENTION_WINDOW_MINUTES)
    cutoff = time.time() - max(1, window_min) * 60
    need = max(1, int(rule.get("threshold") or 1))

    hits: dict[str, dict[str, Any]] = {}
    for sig in signals:
        if not isinstance(sig, dict):
            continue
        kind = _signal_kind(sig)
        if kind not in kinds:
            continue
        sev = str(sig.get("severity") or "warning").lower()
        if _ATTENTION_SEVERITY_RANK.get(sev, 1) < min_sev:
            continue
        seen = _parse_iso_ts(str(sig.get("last_seen") or "")) if sig.get("last_seen") else None
        if seen is not None and seen < cutoff:
            continue
        sid = str(sig.get("session_id") or "")
        prev = hits.get(sid)
        if prev is None or _ATTENTION_SEVERITY_RANK.get(sev, 1) > _ATTENTION_SEVERITY_RANK.get(prev["severity"], 1):
            hits[sid] = {"session_id": sid, "kind": kind, "severity": sev,
                         "last_seen": sig.get("last_seen")}
    if len(hits) < need:
        return None
    worst = sorted(hits.values(),
                   key=lambda h: -_ATTENTION_SEVERITY_RANK.get(h["severity"], 1))[0]
    n = len(hits)
    pseudo = {
        "id": f"signal:{worst['session_id']}:{worst['kind']}:{worst.get('last_seen')}",
        "event_type": f"signal.{worst['kind']}",
        "session_id": worst["session_id"],
        "ts": str(worst.get("last_seen") or ""),
        "data": {"kind": worst["kind"], "severity": worst["severity"]},
    }
    return {
        "event": pseudo,
        "summary": (f"rule fired: {n} session(s) need attention "
                    f"({worst['kind']}, {worst['severity']}) in {window_min}m"),
        "metadata": {
            "sessions": n, "threshold": need, "window_minutes": window_min,
            "kinds": sorted({h["kind"] for h in hits.values()}),
            "worst_session_id": worst["session_id"],
            "worst_kind": worst["kind"], "worst_severity": worst["severity"],
        },
    }


def _eval_cost_velocity(
    rule: dict[str, Any],
    events_chrono: list[dict[str, Any]],
) -> dict[str, Any] | None:
    """Fire when spend over the trailing ``window_sec`` averages >= ``threshold``
    dollars per minute. Sums ``cost_usd`` on the events themselves (derived
    at ingest), so an install with no OTLP still gets a real number. No
    events with cost -> no fire (never a fabricated rate)."""
    threshold = float(rule.get("threshold") or 0)
    if threshold <= 0:
        return None
    window_sec = max(60, int(rule.get("window_sec") or DEFAULT_WINDOW_SEC))
    priced = []
    for e in events_chrono:
        try:
            c = float(e.get("cost_usd") or 0)
        except (TypeError, ValueError):
            continue
        if c <= 0:
            continue
        ts = _parse_iso_ts(e.get("ts"))
        if ts is None:
            continue
        priced.append((ts, c, e))
    if not priced:
        return None
    end_ts = priced[-1][0]
    start = end_ts - window_sec
    spent = sum(c for ts, c, _ in priced if ts >= start)
    per_min = spent / (window_sec / 60.0)
    if per_min < threshold:
        return None
    return {
        "event": priced[-1][2],
        "summary": (f"rule fired: ${per_min:.2f}/min over the last "
                    f"{window_sec // 60}m (threshold ${threshold:.2f}/min)"),
        "metadata": {
            "usd_per_min": round(per_min, 4), "threshold": threshold,
            "window_sec": window_sec, "spent_usd": round(spent, 4),
        },
    }


def _eval_count_over_threshold(
    rule: dict[str, Any],
    events_chrono: list[dict[str, Any]],
) -> dict[str, Any] | None:
    """Fire when ``>= threshold`` events of ``event_type`` occur in
    ``window_sec``. Triggering event = the one whose ts pushes the rolling
    window count over the line."""
    et = rule.get("event_type")
    window_sec = rule["window_sec"]
    threshold = rule["threshold"]

    # Filter by event_type when set; otherwise count every event (which is
    # only useful for very loud rules — daemon will gate via the rule
    # config — but the evaluator stays generic).
    matching = [e for e in events_chrono
                if (et is None or e.get("event_type") == et)]
    if not matching:
        return None
    if threshold <= 0:
        return None

    # Rolling window: for each event, how many matching events fall within
    # ``window_sec`` ending at this event's ts? When that count first crosses
    # the threshold, we fire on that event and stop (cooldown handles repeat
    # suppression).
    for i, e in enumerate(matching):
        ts_end = _parse_iso_ts(e.get("ts"))
        if ts_end is None:
            continue
        ts_start = ts_end - window_sec
        # Count events within [ts_start, ts_end]. The list is chronological
        # so we walk backwards from i.
        count = 0
        for j in range(i, -1, -1):
            ts_j = _parse_iso_ts(matching[j].get("ts"))
            if ts_j is None:
                continue
            if ts_j < ts_start:
                break
            count += 1
        if count >= threshold:
            return {
                "event":   e,
                "summary": (f"rule fired: {count} '{et or 'any'}' events "
                            f"in {window_sec}s (threshold={int(threshold)})"),
                "metadata": {
                    "count":      count,
                    "threshold":  threshold,
                    "window_sec": window_sec,
                    "event_type": et,
                },
            }
    return None


def _eval_error_rate(
    rule: dict[str, Any],
    events_chrono: list[dict[str, Any]],
) -> dict[str, Any] | None:
    """Fire when error-event fraction over total events in ``window_sec``
    exceeds ``threshold`` (interpreted as a fraction in [0, 1]; values >1
    are treated as percentages and divided by 100). Min sample size of 5
    events to avoid firing on trivially small windows."""
    window_sec = rule["window_sec"]
    threshold = rule["threshold"]
    if threshold > 1.0:
        threshold = threshold / 100.0
    if threshold <= 0:
        return None

    # An event is considered an error when its event_type contains "error",
    # ``data.status`` indicates failure, ``data.error`` is truthy, or the
    # explicit ``rule['condition'].get('error_event_types')`` list matches.
    error_types = set(rule.get("condition", {}).get("error_event_types") or [])

    def _is_error(e: dict[str, Any]) -> bool:
        et = (e.get("event_type") or "").lower()
        if "error" in et or "fail" in et:
            return True
        if error_types and e.get("event_type") in error_types:
            return True
        data = e.get("data")
        if isinstance(data, dict):
            if data.get("error"):
                return True
            status = (data.get("status") or "").lower()
            if status in ("error", "failed", "failure"):
                return True
        return False

    if not events_chrono:
        return None

    # Walk forward; at each event's ts, look back over window_sec.
    for i, e in enumerate(events_chrono):
        ts_end = _parse_iso_ts(e.get("ts"))
        if ts_end is None:
            continue
        ts_start = ts_end - window_sec
        total = 0
        errors = 0
        for j in range(i, -1, -1):
            ts_j = _parse_iso_ts(events_chrono[j].get("ts"))
            if ts_j is None:
                continue
            if ts_j < ts_start:
                break
            total += 1
            if _is_error(events_chrono[j]):
                errors += 1
        if total < 5:
            continue  # Sample size too small to be statistically interesting.
        rate = errors / total
        if rate >= threshold:
            return {
                "event":   e,
                "summary": (f"rule fired: error rate {rate:.1%} "
                            f"({errors}/{total}) in {window_sec}s "
                            f"(threshold={threshold:.1%})"),
                "metadata": {
                    "errors":     errors,
                    "total":      total,
                    "rate":       round(rate, 4),
                    "threshold":  threshold,
                    "window_sec": window_sec,
                },
            }
    return None


def _eval_tool_call_pattern(
    rule: dict[str, Any],
    events_chrono: list[dict[str, Any]],
) -> dict[str, Any] | None:
    """Fire on the first event whose tool name matches ``tool_name`` AND
    whose ``str(data)`` matches ``arg_pattern`` (substring or simple regex).

    Tool name is matched either against the explicit ``data.tool_name`` /
    ``data.name`` fields, or against substrings in ``str(data)`` (defensive,
    since multiple agent frameworks store the tool name in different places).
    """
    tool_name = (rule.get("tool_name") or "").strip()
    arg_pattern = rule.get("arg_pattern")
    if not tool_name and not arg_pattern:
        return None

    pattern_re: re.Pattern[str] | None = None
    if arg_pattern:
        try:
            pattern_re = re.compile(arg_pattern, re.IGNORECASE)
        except re.error:
            # Fall back to substring match on a malformed regex.
            pattern_re = None

    for e in events_chrono:
        data = e.get("data")
        data_str = ""
        explicit_name = ""
        if isinstance(data, dict):
            explicit_name = (data.get("tool_name") or data.get("name") or "")
            try:
                import json as _json
                data_str = _json.dumps(data, default=str)
            except Exception:
                data_str = str(data)
        elif isinstance(data, str):
            data_str = data

        # Tool-name match: explicit field exact-eq OR substring in serialised
        # data. Case-insensitive.
        name_ok = True
        if tool_name:
            tn_lc = tool_name.lower()
            name_ok = (
                explicit_name.lower() == tn_lc
                or tn_lc in explicit_name.lower()
                or tn_lc in data_str.lower()
            )
        if not name_ok:
            continue

        # Arg pattern match.
        arg_ok = True
        if arg_pattern:
            if pattern_re is not None:
                arg_ok = bool(pattern_re.search(data_str))
            else:
                arg_ok = arg_pattern.lower() in data_str.lower()
        if not arg_ok:
            continue

        return {
            "event":   e,
            "summary": (f"rule fired: tool_call_pattern matched "
                        f"tool={tool_name!r} arg_pattern={arg_pattern!r}"),
            "metadata": {
                "tool_name":   tool_name,
                "arg_pattern": arg_pattern,
                "event_type":  e.get("event_type"),
            },
        }
    return None


# ── Helpers ───────────────────────────────────────────────────────────────────


def _parse_iso_ts(ts: str | None) -> float | None:
    """Parse an ISO 8601 timestamp into epoch seconds. Returns None on bad
    input (which causes the evaluator to skip that event — preferred over
    raising)."""
    if not ts or not isinstance(ts, str):
        return None
    try:
        # Python's fromisoformat handles "2026-05-13T04:28:43Z" only on
        # 3.11+. Strip a trailing Z and add an explicit offset for older
        # interpreters too.
        s = ts.rstrip()
        if s.endswith("Z"):
            s = s[:-1] + "+00:00"
        dt = datetime.fromisoformat(s)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.timestamp()
    except (ValueError, TypeError):
        return None


__all__ = [
    "evaluate",
    "DEFAULT_WINDOW_SEC",
    "DEFAULT_COOLDOWN_SEC",
    "QUALITY_RULE_TYPES",
    "DEFAULT_QUALITY_WINDOW_MINUTES",
    "DEFAULT_QUALITY_MIN_SESSIONS",
]
