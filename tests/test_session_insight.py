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
