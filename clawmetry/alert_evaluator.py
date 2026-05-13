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
}


# ── Public API ────────────────────────────────────────────────────────────────


def evaluate(
    rules: list[dict[str, Any]] | None,
    events: list[dict[str, Any]] | None,
    last_eval_state: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    """Pure evaluator. Walks ``events`` against ``rules``, returns matches.

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

        try:
            match = _evaluate_one(rule, events_chrono)
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
) -> dict[str, Any] | None:
    """Dispatch on ``rule['type']``. Returns the match dict (rule-agnostic
    shape) or ``None`` when the rule didn't fire."""
    rt = rule.get("type")
    if rt == "count_over_threshold":
        return _eval_count_over_threshold(rule, events_chrono)
    if rt == "error_rate":
        return _eval_error_rate(rule, events_chrono)
    if rt == "tool_call_pattern":
        return _eval_tool_call_pattern(rule, events_chrono)
    # Unknown type — log once and skip. (PRD says: leave a TODO. Here we
    # explicitly under-fire instead of mis-firing.)
    log.debug("alerts: unsupported rule type %r — skipped (rule_id=%s)",
              rt, rule.get("id"))
    return None


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


__all__ = ["evaluate", "DEFAULT_WINDOW_SEC", "DEFAULT_COOLDOWN_SEC"]
