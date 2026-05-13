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
