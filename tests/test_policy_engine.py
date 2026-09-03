"""Unit tests for the pure Guard policy evaluator.

No daemon, no DuckDB, no live agent — ``policy_engine.evaluate`` is a pure
function, so every matching rule and every safety invariant is testable here.
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from clawmetry import policy_engine as pe  # noqa: E402


def _incident(kind="no_progress", session_id="s1", runtime="claude_code",
              severity="warning", count=25, title="agent not advancing"):
    return {
        "kind": kind,
        "session_id": session_id,
        "runtime": runtime,
        "severity": severity,
        "title": title,
        "detail": "",
        "evidence": {"total_tool_calls": count},
        "first_bad_step": 3,
    }


def _policy(policy_id="p1", action="pause", **kw):
    base = {
        "policy_id": policy_id,
        "enabled": True,
        "scope_runtime": "",
        "scope_agent_id": "",
        "trigger_kind": "",
        "min_severity": "info",
        "min_repeat": 0,
        "min_duration_s": 0,
        "min_spend_usd": 0.0,
        "action": action,
    }
    base.update(kw)
    return base


# ── basic matching ─────────────────────────────────────────────────────────

def test_no_policies_means_no_decisions():
    assert pe.evaluate([_incident()], []) == []


def test_bare_policy_matches_any_incident():
    out = pe.evaluate([_incident()], [_policy()])
    assert len(out) == 1
    assert out[0]["action"] == "pause"
    assert out[0]["session_id"] == "s1"
    assert out[0]["kind"] == "no_progress"


def test_disabled_policy_never_fires():
    assert pe.evaluate([_incident()], [_policy(enabled=False)]) == []


def test_trigger_kind_filters():
    pol = _policy(trigger_kind="stuck_loop")
    assert pe.evaluate([_incident(kind="no_progress")], [pol]) == []
    assert len(pe.evaluate([_incident(kind="stuck_loop")], [pol])) == 1


def test_runtime_scope_filters_and_is_case_insensitive():
    pol = _policy(scope_runtime="Claude_Code")
    assert len(pe.evaluate([_incident(runtime="claude_code")], [pol])) == 1
    assert pe.evaluate([_incident(runtime="codex")], [pol]) == []


def test_unknown_action_is_refused_not_guessed():
    assert pe.evaluate([_incident()], [_policy(action="delete_everything")]) == []


# ── thresholds ─────────────────────────────────────────────────────────────

def test_min_repeat_threshold():
    pol = _policy(min_repeat=30)
    assert pe.evaluate([_incident(count=25)], [pol]) == []
    assert len(pe.evaluate([_incident(count=30)], [pol])) == 1


def test_min_severity_threshold():
    pol = _policy(min_severity="warning")
    assert pe.evaluate([_incident(severity="info")], [pol]) == []
    assert len(pe.evaluate([_incident(severity="warning")], [pol])) == 1


def test_spend_and_duration_thresholds_are_anded():
    pol = _policy(min_duration_s=300, min_spend_usd=5.0)
    facts = {"s1": {"bad_for_seconds": 600, "cost_usd": 4.0}}
    assert pe.evaluate([_incident()], [pol], facts) == []   # spend too low
    facts = {"s1": {"bad_for_seconds": 60, "cost_usd": 9.0}}
    assert pe.evaluate([_incident()], [pol], facts) == []   # too soon
    facts = {"s1": {"bad_for_seconds": 600, "cost_usd": 9.0}}
    assert len(pe.evaluate([_incident()], [pol], facts)) == 1


def test_missing_facts_do_not_accidentally_satisfy_thresholds():
    """A session we have no facts for must NOT match a spend threshold."""
    pol = _policy(min_spend_usd=5.0)
    assert pe.evaluate([_incident()], [pol], {}) == []


def test_zeroed_thresholds_never_block():
    facts = {"s1": {"bad_for_seconds": 0, "cost_usd": 0}}
    assert len(pe.evaluate([_incident()], [_policy()], facts)) == 1


# ── safety invariants ──────────────────────────────────────────────────────

def test_at_most_one_decision_per_session_strongest_wins():
    policies = [_policy("p1", action="alert"), _policy("p2", action="kill"),
                _policy("p3", action="pause")]
    out = pe.evaluate([_incident()], policies)
    assert len(out) == 1, "must never emit two signals for one session"
    assert out[0]["action"] == "kill"
    assert out[0]["policy_id"] == "p2"


def test_tie_break_is_deterministic():
    policies = [_policy("zzz", action="pause"), _policy("aaa", action="pause")]
    first = pe.evaluate([_incident()], policies)
    second = pe.evaluate([_incident()], list(reversed(policies)))
    assert first[0]["policy_id"] == "aaa"
    assert first == second


def test_monitor_returns_a_decision_so_dry_run_is_visible():
    out = pe.evaluate([_incident()], [_policy(action="monitor")])
    assert len(out) == 1
    assert out[0]["action"] == "monitor"
    assert not pe.is_actuating("monitor")
    assert "would monitor" in out[0]["reason"]


def test_actuating_classification():
    assert pe.is_actuating("pause") and pe.is_actuating("stop")
    assert pe.is_actuating("kill")
    assert not pe.is_actuating("alert")
    assert not pe.is_actuating("")


def test_incident_without_session_id_is_skipped():
    bad = _incident()
    bad["session_id"] = ""
    assert pe.evaluate([bad], [_policy()]) == []


def test_malformed_rows_never_raise():
    assert pe.evaluate([None, "junk", {}], [None, "junk", _policy()]) == []


def test_multiple_sessions_each_get_a_decision():
    incidents = [_incident(session_id="s1"), _incident(session_id="s2")]
    out = pe.evaluate(incidents, [_policy()])
    assert {d["session_id"] for d in out} == {"s1", "s2"}


def test_output_is_sorted_strongest_first():
    incidents = [_incident(session_id="s1"), _incident(session_id="s2")]
    policies = [_policy("p1", action="alert", scope_runtime=""),
                _policy("p2", action="kill", trigger_kind="stuck_loop")]
    incidents.append(_incident(session_id="s3", kind="stuck_loop"))
    out = pe.evaluate(incidents, policies)
    assert out[0]["action"] == "kill"


def test_evidence_records_the_numbers_that_matched():
    pol = _policy(min_repeat=10, min_spend_usd=1.0)
    facts = {"s1": {"bad_for_seconds": 420, "cost_usd": 3.5}}
    out = pe.evaluate([_incident(count=38)], [pol], facts)
    ev = out[0]["evidence"]
    assert ev["count"] == 38
    assert ev["cost_usd"] == 3.5
    assert ev["thresholds"]["min_repeat"] == 10
    assert "38 events" in out[0]["reason"]
