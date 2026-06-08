"""Pure-unit tests for ``clawmetry.alert_evaluator`` (PRD #779 PR-D pt2).

No DuckDB, no network, no daemon globals — exercises the evaluator's three
condition types + dedup memo + degenerate inputs. Runs in <1s.
"""
from __future__ import annotations

import os
import sys

import pytest


_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)


from clawmetry import alert_evaluator  # noqa: E402


# ── Helpers ────────────────────────────────────────────────────────────────────


def _rule(rid, **cond):
    """Build a DuckDB-shape rule row. ``cond`` is the condition_json body."""
    return {
        "id":             rid,
        "name":           cond.pop("name", f"rule {rid}"),
        "enabled":        cond.pop("enabled", True),
        "condition_json": cond,
    }


def _events(et, ts_offsets, *, base_ts="2026-05-13T04:00:00+00:00"):
    """Build a chronological list of events of type ``et``. ``ts_offsets`` is
    a list of integer second offsets (event[i].ts = base_ts + offsets[i]).
    Each event gets a unique id so dedup works."""
    from datetime import datetime, timedelta, timezone
    base = datetime.fromisoformat(base_ts)
    if base.tzinfo is None:
        base = base.replace(tzinfo=timezone.utc)
    out = []
    for i, off in enumerate(ts_offsets):
        ts = (base + timedelta(seconds=off)).isoformat()
        out.append({
            "id":         f"{et}-{i}-{off}",
            "event_type": et,
            "ts":         ts,
            "data":       {"i": i},
        })
    return out


# ── 1. count_over_threshold ───────────────────────────────────────────────────


def test_count_over_threshold_fires_when_above_threshold():
    rule = _rule(
        "r-count",
        type="count_over_threshold",
        event_type="error",
        threshold=5,
        window_sec=60,
        cooldown_sec=0,
    )
    events = _events("error", [0, 5, 10, 15, 20])  # 5 events in 20s
    memo = {}
    matches = alert_evaluator.evaluate([rule], events, memo)
    assert len(matches) == 1
    m = matches[0]
    assert m["rule"]["id"] == "r-count"
    assert m["event"]["id"] == "error-4-20"  # the 5th event crosses the line
    assert m["metadata"]["count"] == 5
    assert m["metadata"]["threshold"] == 5
    assert "5 'error' events" in m["summary"]


def test_count_over_threshold_no_fire_under_threshold():
    rule = _rule(
        "r-count",
        type="count_over_threshold",
        event_type="error",
        threshold=5,
        window_sec=60,
        cooldown_sec=0,
    )
    events = _events("error", [0, 5, 10])  # only 3 events
    memo = {}
    matches = alert_evaluator.evaluate([rule], events, memo)
    assert matches == []


def test_count_over_threshold_window_excludes_old_events():
    """Events outside the rolling window should NOT contribute to the count."""
    rule = _rule(
        "r-count",
        type="count_over_threshold",
        event_type="error",
        threshold=3,
        window_sec=10,  # tight 10s window
        cooldown_sec=0,
    )
    # 4 events spread across 60s — only 2 will fall inside any 10s window.
    events = _events("error", [0, 20, 40, 60])
    memo = {}
    matches = alert_evaluator.evaluate([rule], events, memo)
    assert matches == []


def test_count_over_threshold_filters_by_event_type():
    """Events of OTHER types must not contribute to the count."""
    rule = _rule(
        "r-count",
        type="count_over_threshold",
        event_type="error",
        threshold=3,
        window_sec=60,
        cooldown_sec=0,
    )
    # 2 errors + 5 non-errors in the same window — should not fire.
    events = (
        _events("error", [0, 5])
        + _events("info", [10, 15, 20, 25, 30])
    )
    memo = {}
    matches = alert_evaluator.evaluate([rule], events, memo)
    assert matches == []


# ── 2. dedup memo / cooldown ─────────────────────────────────────────────────


def test_dedup_memo_prevents_re_firing_same_event():
    """Calling evaluate() twice with the same matching events should fire only
    once (the second call's match is suppressed by the dedup memo)."""
    rule = _rule(
        "r-dedup",
        type="count_over_threshold",
        event_type="error",
        threshold=3,
        window_sec=60,
        cooldown_sec=3600,  # 1h cooldown
    )
    events = _events("error", [0, 5, 10])
    memo = {}
    first = alert_evaluator.evaluate([rule], events, memo)
    second = alert_evaluator.evaluate([rule], events, memo)
    assert len(first) == 1
    assert second == []
    # Memo bookkeeping shape
    assert "r-dedup" in memo
    assert memo["r-dedup"].get("last_event_id") == first[0]["event"]["id"]
    assert memo["r-dedup"].get("last_fired_ts", 0) > 0


def test_independent_state_per_rule():
    """Two rules firing on the same events should have independent memos."""
    rule_a = _rule(
        "r-a",
        type="count_over_threshold",
        event_type="error",
        threshold=3,
        window_sec=60,
        cooldown_sec=3600,
    )
    rule_b = _rule(
        "r-b",
        type="count_over_threshold",
        event_type="error",
        threshold=2,
        window_sec=60,
        cooldown_sec=3600,
    )
    events = _events("error", [0, 5, 10])
    memo = {}
    matches = alert_evaluator.evaluate([rule_a, rule_b], events, memo)
    rids = sorted(m["rule"]["id"] for m in matches)
    assert rids == ["r-a", "r-b"]
    # Each got its own memo entry.
    assert "r-a" in memo and "r-b" in memo
    # Second pass: both deduped.
    assert alert_evaluator.evaluate([rule_a, rule_b], events, memo) == []


def test_disabled_rule_never_fires():
    rule = _rule(
        "r-off",
        enabled=False,
        type="count_over_threshold",
        event_type="error",
        threshold=1,
        window_sec=60,
        cooldown_sec=0,
    )
    events = _events("error", [0, 5, 10])
    assert alert_evaluator.evaluate([rule], events, {}) == []


# ── 3. degenerate inputs ─────────────────────────────────────────────────────


def test_empty_rules_returns_empty():
    assert alert_evaluator.evaluate([], _events("x", [0, 1, 2]), {}) == []
    assert alert_evaluator.evaluate(None, _events("x", [0, 1, 2]), {}) == []


def test_empty_events_returns_empty():
    rule = _rule(
        "r1", type="count_over_threshold", event_type="x", threshold=1,
        window_sec=60, cooldown_sec=0,
    )
    assert alert_evaluator.evaluate([rule], [], {}) == []
    assert alert_evaluator.evaluate([rule], None, {}) == []


def test_malformed_rule_does_not_raise():
    """No id, no condition — evaluator should skip, not crash."""
    bad = [
        {},                                # no id
        {"id": "bad", "condition_json": "not-a-dict"},
        {"id": "u", "condition_json": {"type": "no_such_type"}},
    ]
    events = _events("x", [0, 5, 10])
    assert alert_evaluator.evaluate(bad, events, {}) == []


def test_none_state_raises_typeerror():
    """Pass an empty dict — None is a programmer error."""
    rule = _rule(
        "r1", type="count_over_threshold", event_type="x", threshold=1,
        window_sec=60, cooldown_sec=0,
    )
    with pytest.raises(TypeError):
        alert_evaluator.evaluate([rule], _events("x", [0]), None)


# ── 4. error_rate ────────────────────────────────────────────────────────────


def test_error_rate_fires_above_threshold():
    rule = _rule(
        "r-err",
        type="error_rate",
        threshold=0.4,           # 40% errors
        window_sec=60,
        cooldown_sec=0,
    )
    # 5 events in window: 3 errors, 2 ok → 60% error rate.
    events = (
        _events("error", [0, 5, 10])
        + _events("ok", [12, 14])
    )
    matches = alert_evaluator.evaluate([rule], events, {})
    assert len(matches) == 1
    md = matches[0]["metadata"]
    assert md["errors"] == 3
    assert md["total"] == 5
    assert md["rate"] >= 0.6


def test_error_rate_under_min_sample_does_not_fire():
    """With <5 events in window, error_rate suppresses to avoid false positives
    on trivially small samples."""
    rule = _rule(
        "r-err", type="error_rate", threshold=0.4,
        window_sec=60, cooldown_sec=0,
    )
    # 3 events, all errors — would be 100% but sample too small.
    events = _events("error", [0, 5, 10])
    assert alert_evaluator.evaluate([rule], events, {}) == []


def test_error_rate_percentage_threshold_is_normalised():
    """Threshold > 1 should be treated as a percentage (cloud-form input)."""
    rule = _rule(
        "r-err", type="error_rate",
        threshold=50,  # i.e. 50% — should be normalised to 0.5
        window_sec=60, cooldown_sec=0,
    )
    events = (
        _events("error", [0, 5, 10, 15])
        + _events("ok", [12, 14, 16, 18])
    )
    # 4 errors / 8 total = 50%, equals threshold → fires.
    matches = alert_evaluator.evaluate([rule], events, {})
    assert len(matches) == 1


# ── 5. tool_call_pattern ─────────────────────────────────────────────────────


def test_tool_call_pattern_matches_explicit_name():
    rule = _rule(
        "r-tool",
        type="tool_call_pattern",
        tool_name="exec",
        cooldown_sec=0,
    )
    events = [
        {"id": "e1", "event_type": "tool", "ts": "2026-05-13T04:00:00+00:00",
         "data": {"tool_name": "exec", "args": {"cmd": "ls"}}},
        {"id": "e2", "event_type": "tool", "ts": "2026-05-13T04:00:01+00:00",
         "data": {"tool_name": "browser", "args": {}}},
    ]
    matches = alert_evaluator.evaluate([rule], events, {})
    assert len(matches) == 1
    assert matches[0]["event"]["id"] == "e1"


def test_tool_call_pattern_with_arg_regex():
    rule = _rule(
        "r-tool",
        type="tool_call_pattern",
        tool_name="exec",
        arg_pattern=r"rm\s+-rf",
        cooldown_sec=0,
    )
    events = [
        {"id": "e1", "event_type": "tool", "ts": "2026-05-13T04:00:00+00:00",
         "data": {"tool_name": "exec", "args": {"cmd": "ls"}}},
        {"id": "e2", "event_type": "tool", "ts": "2026-05-13T04:00:01+00:00",
         "data": {"tool_name": "exec", "args": {"cmd": "rm -rf /"}}},
    ]
    matches = alert_evaluator.evaluate([rule], events, {})
    assert len(matches) == 1
    assert matches[0]["event"]["id"] == "e2"


def test_tool_call_pattern_no_match():
    rule = _rule(
        "r-tool", type="tool_call_pattern",
        tool_name="never_called", cooldown_sec=0,
    )
    events = [
        {"id": "e1", "event_type": "tool", "ts": "2026-05-13T04:00:00+00:00",
         "data": {"tool_name": "exec", "args": {"cmd": "ls"}}},
    ]
    assert alert_evaluator.evaluate([rule], events, {}) == []


# ── 6. legacy alert_type aliasing ────────────────────────────────────────────


def test_legacy_alert_type_maps_to_count_evaluator():
    """A cloud rule with alert_type='token_velocity' (no explicit `type`) is
    treated as count_over_threshold so we at least get coverage instead of
    silently ignoring the rule."""
    rule = _rule(
        "r-legacy",
        alert_type="token_velocity",     # legacy field
        event_type="assistant",
        threshold_value=2,                # legacy field
        window_sec=60,
        cooldown_sec=0,
    )
    events = _events("assistant", [0, 5, 10])
    matches = alert_evaluator.evaluate([rule], events, {})
    assert len(matches) == 1


# ── 7. eval_score_below (eval->monitor loop) ─────────────────────────────────


def _quality(*, eval_count=0, eval_avg=None, eval_scores=None,
             classified_total=0, failed_count=0, outcome_counts=None,
             window_minutes=60):
    """Build a query_session_quality_window()-shaped dict."""
    failure_rate = (failed_count / classified_total) if classified_total else None
    return {
        "window_minutes":   window_minutes,
        "eval_count":       eval_count,
        "eval_avg":         eval_avg,
        "eval_scores":      eval_scores or [],
        "outcome_counts":   outcome_counts or {},
        "classified_total": classified_total,
        "failed_count":     failed_count,
        "failure_rate":     failure_rate,
    }


def test_eval_score_below_fires_when_avg_below_threshold():
    rule = _rule(
        "r-eval",
        alert_type="eval_score_below",
        threshold_value=3,         # fire when avg < 3
        cooldown_sec=0,
    )
    q = _quality(eval_count=4, eval_avg=2.1, eval_scores=[1, 2, 2, 3.4])
    matches = alert_evaluator.evaluate([rule], [], {}, q)
    assert len(matches) == 1
    md = matches[0]["metadata"]
    assert md["avg_score"] == 2.1
    assert md["threshold"] == 3.0
    assert md["session_count"] == 4
    assert "avg eval score 2.10" in matches[0]["summary"]


def test_eval_score_below_no_fire_when_avg_at_or_above_threshold():
    rule = _rule("r-eval", alert_type="eval_score_below",
                 threshold_value=3, cooldown_sec=0)
    q = _quality(eval_count=5, eval_avg=3.0)  # exactly at threshold -> no fire
    assert alert_evaluator.evaluate([rule], [], {}, q) == []
    q2 = _quality(eval_count=5, eval_avg=4.2)
    assert alert_evaluator.evaluate([rule], [], {}, q2) == []


def test_eval_score_below_respects_min_sessions():
    """Below threshold but too few scored sessions -> no fire (single-sample
    noise guard). Default min_sessions is 3."""
    rule = _rule("r-eval", alert_type="eval_score_below",
                 threshold_value=3, cooldown_sec=0)
    q = _quality(eval_count=2, eval_avg=1.0)  # avg low, but only 2 sessions
    assert alert_evaluator.evaluate([rule], [], {}, q) == []
    # Custom min_sessions honoured.
    rule2 = _rule("r-eval2", alert_type="eval_score_below",
                  threshold_value=3, min_sessions=2, cooldown_sec=0)
    assert len(alert_evaluator.evaluate([rule2], [], {}, q)) == 1


def test_eval_score_below_no_fire_on_empty_quality():
    rule = _rule("r-eval", alert_type="eval_score_below",
                 threshold_value=3, cooldown_sec=0)
    # No quality slice fetched at all.
    assert alert_evaluator.evaluate([rule], [], {}, None) == []
    # Empty store (no scored sessions in window).
    assert alert_evaluator.evaluate([rule], [], {}, _quality()) == []


# ── 8. outcome_failure_rate (eval->monitor loop) ─────────────────────────────


def test_outcome_failure_rate_fires_above_threshold():
    rule = _rule(
        "r-out",
        alert_type="outcome_failure_rate",
        threshold_value=20,        # 20%
        cooldown_sec=0,
    )
    # 10 classified, 3 failed-ish -> 30% > 20% -> fires.
    q = _quality(classified_total=10, failed_count=3,
                 outcome_counts={"success": 7, "failed": 2, "cognitive_loop": 1})
    matches = alert_evaluator.evaluate([rule], [], {}, q)
    assert len(matches) == 1
    md = matches[0]["metadata"]
    assert md["failed_count"] == 3
    assert md["classified_total"] == 10
    assert md["failure_rate"] == 0.3
    assert md["threshold_pct"] == 20.0


def test_outcome_failure_rate_no_fire_at_or_below_threshold():
    rule = _rule("r-out", alert_type="outcome_failure_rate",
                 threshold_value=30, cooldown_sec=0)
    # 30% failure exactly equals 30% threshold -> no fire (strict exceed).
    q = _quality(classified_total=10, failed_count=3)
    assert alert_evaluator.evaluate([rule], [], {}, q) == []


def test_outcome_failure_rate_respects_min_sessions():
    rule = _rule("r-out", alert_type="outcome_failure_rate",
                 threshold_value=20, cooldown_sec=0)
    # 2 classified, both failed = 100% but below the 3-session floor.
    q = _quality(classified_total=2, failed_count=2)
    assert alert_evaluator.evaluate([rule], [], {}, q) == []


def test_outcome_failure_rate_accepts_fraction_threshold():
    """A threshold <= 1 is read as a fraction (0.2 == 20%)."""
    rule = _rule("r-out", alert_type="outcome_failure_rate",
                 threshold_value=0.2, cooldown_sec=0)
    q = _quality(classified_total=10, failed_count=3)  # 30% > 20%
    assert len(alert_evaluator.evaluate([rule], [], {}, q)) == 1


def test_outcome_failure_rate_no_fire_on_empty_quality():
    rule = _rule("r-out", alert_type="outcome_failure_rate",
                 threshold_value=20, cooldown_sec=0)
    assert alert_evaluator.evaluate([rule], [], {}, None) == []
    assert alert_evaluator.evaluate([rule], [], {}, _quality()) == []


def test_quality_rules_coexist_with_event_rules():
    """A quality rule and a count rule evaluated together both work — the
    quality rule reads ``quality``, the event rule reads ``events``."""
    qrule = _rule("r-eval", alert_type="eval_score_below",
                  threshold_value=3, cooldown_sec=0)
    erule = _rule("r-count", type="count_over_threshold", event_type="error",
                  threshold=3, window_sec=60, cooldown_sec=0)
    events = _events("error", [0, 5, 10])
    q = _quality(eval_count=4, eval_avg=2.0)
    matches = alert_evaluator.evaluate([qrule, erule], events, {}, q)
    rids = sorted(m["rule"]["id"] for m in matches)
    assert rids == ["r-count", "r-eval"]
