"""New alert rule types: stuck_session / rate_limited / blocked_on_user /
agent_attention (loop_signals-fed) and cost_velocity (event cost-fed).

Pure evaluator tests plus the daemon-side slice helper and the free seed rule.
"""
from __future__ import annotations

import os
import sys
import time

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from clawmetry import alert_evaluator as ae  # noqa: E402


def _iso(offset_sec=0):
    return time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime(time.time() - offset_sec))


def _rule(rid, cond):
    return {"id": rid, "name": rid, "enabled": True, "condition_json": cond}


def _sig(kind, sid="claude_code:s1", sev="warning", age=60, signature=None):
    return {"session_id": sid, "signature": signature or f"daemon_detect_{kind}",
            "severity": sev, "last_seen": _iso(age), "details": {"kind": kind}}


def test_signal_types_are_registered_and_map_to_kinds():
    for t in ("stuck_session", "rate_limited", "blocked_on_user", "agent_attention"):
        assert t in ae.ATTENTION_RULE_TYPES
        assert t in ae._LEGACY_ALERT_TYPE_MAP
    assert "cost_velocity" in ae._LEGACY_ALERT_TYPE_MAP
    assert ae.ATTENTION_RULE_KINDS["rate_limited"] == {"rate_limited"}
    assert ae.ATTENTION_RULE_KINDS["blocked_on_user"] == {"blocked_on_user"}
    assert ae.STUCK_KINDS <= ae.ATTENTION_RULE_KINDS["agent_attention"]
    assert {"rate_limited", "blocked_on_user", "crashed"} <= ae.ATTENTION_RULE_KINDS["agent_attention"]


def test_stuck_session_fires_on_a_stuck_signal_only():
    rules = [_rule("stuck", {"type": "stuck_session"})]
    assert ae.evaluate(rules, [], {}, loop_signals=[_sig("rate_limited")]) == []
    m = ae.evaluate(rules, [], {}, loop_signals=[_sig("no_progress")])
    assert len(m) == 1 and m[0]["metadata"]["worst_kind"] == "no_progress"
    assert m[0]["event"]["session_id"] == "claude_code:s1"


def test_legacy_daemon_stuck_signature_counts_as_stuck():
    rules = [_rule("stuck", {"type": "stuck_session"})]
    sig = {"session_id": "s", "signature": "daemon_stuck", "severity": "warning",
           "last_seen": _iso(10), "details": None}
    assert len(ae.evaluate(rules, [], {}, loop_signals=[sig])) == 1


def test_rate_limited_and_blocked_on_user_types():
    m = ae.evaluate([_rule("rl", {"type": "rate_limited"})], [], {},
                    loop_signals=[_sig("rate_limited"), _sig("blocked_on_user", sid="x")])
    assert len(m) == 1 and m[0]["metadata"]["kinds"] == ["rate_limited"]
    m = ae.evaluate([_rule("bu", {"type": "blocked_on_user"})], [], {},
                    loop_signals=[_sig("blocked_on_user")])
    assert len(m) == 1 and m[0]["summary"].startswith("rule fired")


def test_agent_attention_is_the_union_and_counts_sessions():
    rules = [_rule("attn", {"type": "agent_attention", "threshold": 2})]
    one = ae.evaluate(rules, [], {}, loop_signals=[_sig("crashed")])
    assert one == []
    two = ae.evaluate(rules, [], {}, loop_signals=[_sig("crashed"), _sig("stuck_loop", sid="s2")])
    assert len(two) == 1 and two[0]["metadata"]["sessions"] == 2


def test_signal_rules_respect_severity_floor_and_window():
    rules = [_rule("attn", {"type": "agent_attention"})]
    assert ae.evaluate(rules, [], {}, loop_signals=[_sig("stuck_loop", sev="info")]) == []
    rules = [_rule("attn", {"type": "agent_attention", "min_severity": "info"})]
    assert len(ae.evaluate(rules, [], {}, loop_signals=[_sig("stuck_loop", sev="info")])) == 1
    rules = [_rule("attn", {"type": "agent_attention", "window_minutes": 5})]
    assert ae.evaluate(rules, [], {}, loop_signals=[_sig("stuck_loop", age=3600)]) == []


def test_signal_rules_no_fire_without_a_slice_and_scope_by_runtime():
    rules = [_rule("attn", {"type": "agent_attention"})]
    assert ae.evaluate(rules, [], {}, loop_signals=None) == []
    scoped = [_rule("attn", {"type": "agent_attention", "runtime": "codex"})]
    assert ae.evaluate(scoped, [], {}, loop_signals=[_sig("crashed", sid="claude_code:a")]) == []
    assert len(ae.evaluate(scoped, [], {}, loop_signals=[_sig("crashed", sid="codex:a")])) == 1


def test_signal_rule_cooldown_applies():
    rules = [_rule("attn", {"type": "agent_attention", "cooldown_sec": 3600})]
    state = {}
    assert len(ae.evaluate(rules, [], state, loop_signals=[_sig("crashed")])) == 1
    assert ae.evaluate(rules, [], state, loop_signals=[_sig("crashed")]) == []


def test_cost_velocity_from_event_costs():
    evs = [{"id": f"e{i}", "event_type": "tool_call", "ts": _iso(i * 10),
            "cost_usd": 0.5, "session_id": "codex:s"} for i in range(12)]
    fired = ae.evaluate([_rule("cv", {"type": "cost_velocity", "threshold": 1.0,
                                      "window_sec": 120})], evs, {})
    assert len(fired) == 1
    assert fired[0]["metadata"]["usd_per_min"] >= 1.0
    quiet = ae.evaluate([_rule("cv", {"type": "cost_velocity", "threshold": 100.0,
                                      "window_sec": 120})], evs, {})
    assert quiet == []


def test_cost_velocity_never_fabricates_without_costs():
    evs = [{"id": "e1", "event_type": "tool_call", "ts": _iso(1), "session_id": "s"}]
    assert ae.evaluate([_rule("cv", {"type": "cost_velocity", "threshold": 0.01})], evs, {}) == []


def test_daemon_slice_helper_fetches_only_when_a_signal_rule_exists():
    from clawmetry import sync as _sync

    class Store:
        calls = []

        def query_recent_loop_signals(self, limit=20, since_minutes=60):
            Store.calls.append(since_minutes)
            return [{"session_id": "s"}]

    st = Store()
    assert _sync._alerts_loop_signals_slice(st, [_rule("x", {"type": "error_rate"})], ae) is None
    assert Store.calls == []
    rows = _sync._alerts_loop_signals_slice(
        st, [_rule("a", {"type": "agent_attention", "window_minutes": 45}),
             _rule("b", {"type": "rate_limited"})], ae)
    assert rows == [{"session_id": "s"}] and Store.calls == [45]


def test_free_seed_rule_agent_needs_attention():
    from routes.alerts import DEFAULT_ALERT_RULES
    seed = next(r for r in DEFAULT_ALERT_RULES if r["id"] == "agent_attention_default")
    assert seed["type"] == "agent_attention"
    assert seed["pro_only"] is False and seed["enabled"] is True
    assert seed["label"] == "Agent needs attention"
    assert set(seed["channels"]) == {"banner", "telegram"}
    assert "—" not in seed["description"] and "--" not in seed["description"]
