"""Context-economics snapshot slice must split compactions per-runtime.

Founder report 2026-06-03: selecting opencode/codex showed Claude Code's
compactions (the all-runtimes aggregate). `_context_econ_by_runtime` groups
compactions + overflow sessions by each compaction's session_id prefix so the
cloud interceptor can serve the selected runtime's view (empty for a runtime
that never compacted).
"""
import clawmetry.sync as sync


def _comp(sid, trigger="proactive", reclaimed=100):
    return {"session_id": sid, "trigger": trigger, "reclaimed": reclaimed}


def test_compactions_split_by_runtime(monkeypatch):
    monkeypatch.setattr(sync, "_runtime_of_session", lambda s: (
        s.split(":")[0] if ":" in s else "openclaw"))
    comps = [
        _comp("claude_code:a", "overflow", 500),
        _comp("claude_code:b", "proactive", 200),
        _comp("goose:c", "proactive", 50),
        _comp("bare-uuid", "proactive", 10),  # -> openclaw
    ]
    ovf = [{"session_id": "claude_code:a"}, {"session_id": "goose:c"}]
    base = {"peak_pct": 87.5, "utilization_points": 400}

    out = sync._context_econ_by_runtime(comps, ovf, base)

    assert set(out.keys()) == {"claude_code", "goose", "openclaw"}
    assert "opencode" not in out and "codex" not in out

    cc = out["claude_code"]
    assert cc["summary"]["compaction_count"] == 2
    assert cc["summary"]["overflow_count"] == 1
    assert cc["summary"]["proactive_count"] == 1
    assert cc["summary"]["total_reclaimed"] == 700
    assert cc["summary"]["peak_pct"] == 87.5            # inherits node-wide
    assert [s["session_id"] for s in cc["overflow_sessions"]] == ["claude_code:a"]

    # reconciliation: per-runtime compaction counts sum to the total
    assert sum(d["summary"]["compaction_count"] for d in out.values()) == 4


def test_empty_input_yields_empty(monkeypatch):
    monkeypatch.setattr(sync, "_runtime_of_session", lambda s: "openclaw")
    assert sync._context_econ_by_runtime([], [], {}) == {}
