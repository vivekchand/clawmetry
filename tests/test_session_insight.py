"""Unit tests for the context-graph per-session decision insight helper."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from routes.sessions import _derive_session_insight


def test_true_cost_includes_fanout_and_all_flags():
    sess = {"cost_usd": 1.00, "reasoning_cost_usd": 0.40, "cache_hit_pct": 11.0,
            "tool_error_pct": 40.0, "compaction_count": 3, "model_mix": True}
    lineage = [{"depth": 0, "cost_usd": 1.00}, {"depth": 1, "cost_usd": 0.50}, {"depth": 2, "cost_usd": 0.20}]
    ins = _derive_session_insight(sess, lineage)
    assert ins["true_cost_usd"] == 1.70        # own 1.00 + downstream 0.70
    assert ins["downstream_cost_usd"] == 0.70
    assert ins["subagent_count"] == 2
    assert set(ins["waste_flags"]) == {
        "reasoning_heavy", "cache_poor", "tools_failing",
        "compaction_thrash", "model_fallback", "fanned_out",
    }


def test_clean_session_has_no_flags():
    ins = _derive_session_insight(
        {"cost_usd": 0.10, "cache_hit_pct": 85.0, "tool_error_pct": 0, "compaction_count": 0},
        [{"depth": 0, "cost_usd": 0.10}],
    )
    assert ins["waste_flags"] == []
    assert ins["true_cost_usd"] == 0.10
    assert ins["subagent_count"] == 0


def test_empty_is_safe():
    ins = _derive_session_insight({}, [])
    assert ins["true_cost_usd"] == 0.0 and ins["waste_flags"] == []


from routes.sessions import _derive_waste_summary


def test_waste_summary_aggregates_recoverable_spend():
    sessions = [
        {"session_id": "a", "cost_usd": 1.00, "reasoning_cost_usd": 0.40, "cache_hit_pct": 11.0,
         "tool_error_pct": 40.0, "compaction_count": 3, "model_mix": True},
        {"session_id": "b", "cost_usd": 0.50, "cache_hit_pct": 85.0, "tool_error_pct": 0, "compaction_count": 0},
        {"session_id": "c", "cost_usd": 0.30, "cache_hit_pct": 20.0},
    ]
    w = _derive_waste_summary(sessions)
    assert w["total_cost_usd"] == 1.80
    assert w["reasoning_cost_usd"] == 0.40
    assert w["low_cache_sessions"] == 2          # a + c
    assert w["tool_failing_sessions"] == 1       # a
    assert w["compaction_heavy_sessions"] == 1   # a
    assert w["model_fallback_sessions"] == 1     # a
    assert w["flagged_session_count"] == 2       # a + c (b is clean)


def test_waste_summary_empty_is_safe():
    w = _derive_waste_summary([])
    assert w["total_cost_usd"] == 0.0 and w["flagged_session_count"] == 0


from routes.sessions import _session_governance


def test_session_governance_joins_approvals_and_guardrails():
    approvals = [
        {"requestor_session_id": "s1", "action": "bash", "decision": "approve", "status": "resolved"},
        {"requestor_session_id": "s1", "action": "write", "decision": "deny", "decision_reason": "outside scope", "status": "resolved"},
        {"requestor_session_id": "s2", "action": "bash", "decision": "approve"},
    ]
    guardrails = [
        {"session_id": "s1", "action": "curl", "rule_name": "egress", "verdict": "block"},
        {"session_id": "s1", "action": "read", "rule_name": "fs", "verdict": "allow"},
        {"session_id": "s2", "action": "x", "verdict": "allow"},
    ]
    g = _session_governance(approvals, guardrails, "s1")
    assert len(g["approvals"]) == 2 and len(g["guardrails"]) == 2
    assert g["decision_count"] == 4
    assert g["denied_count"] == 2          # 1 deny + 1 block


def test_session_governance_empty_is_safe():
    assert _session_governance([], [], "x")["decision_count"] == 0


from routes.sessions import _WASTE_RECOMMENDATIONS


def test_every_waste_flag_has_a_recommendation():
    # Every flag _derive_session_insight can emit (+ policy_denied from the route)
    # must have actionable advice, or the insight card shows a flag with no "what to do".
    sess = {"cost_usd": 1.0, "reasoning_cost_usd": 0.4, "cache_hit_pct": 11.0,
            "tool_error_pct": 40.0, "compaction_count": 3, "model_mix": True}
    flags = set(_derive_session_insight(sess, [{"depth": 0, "cost_usd": 1.0}, {"depth": 1, "cost_usd": 0.5}])["waste_flags"])
    flags.add("policy_denied")
    for f in flags:
        assert f in _WASTE_RECOMMENDATIONS and _WASTE_RECOMMENDATIONS[f]
