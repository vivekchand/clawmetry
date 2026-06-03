"""The Tool-catalog snapshot slice must split tools per-runtime.

Founder report 2026-06-03: selecting opencode/codex on the node page showed
Claude Code's tools (Bash/Read/Edit/chrome-devtools) — the all-runtimes
aggregate. Fix: `_build_tool_catalog_slice` emits a `byRuntime` map (runtime ->
{tools, groups, totals}) derived from each tool_call event's session_id prefix,
so the cloud interceptor can serve the selected runtime's catalog (and an
empty one for a runtime that never invoked a tool).
"""
import clawmetry.sync as sync


class _FakeStore:
    def __init__(self, events):
        self._events = events

    def query_events(self, limit=5000):
        return self._events

    def query_tool_policy(self, limit=25):
        return []


def _call(session_id, tool, tuid):
    return {
        "event_type": "tool_call",
        "ts": 1000,
        "session_id": session_id,
        "data": {"tool_name": tool, "tool_calls": [{"id": tuid, "name": tool}]},
    }


def test_by_runtime_splits_tools(monkeypatch):
    events = [
        _call("claude_code:s1", "Bash", "a"),
        _call("claude_code:s1", "Bash", "b"),
        _call("claude_code:s1", "Read", "c"),
        _call("goose:s2", "extensionmanager__list", "d"),
        _call("625c0ad9-bare-uuid", "openclaw_tool", "e"),  # bare uuid -> openclaw
    ]
    monkeypatch.setattr(sync, "_runtime_of_session", lambda sid: (
        sid.split(":")[0] if ":" in sid else "openclaw"))

    import clawmetry.local_store as ls
    monkeypatch.setattr(ls, "get_store", lambda *a, **k: _FakeStore(events))

    slice_ = sync._build_tool_catalog_slice()
    br = slice_.get("byRuntime", {})

    # claude_code, goose, openclaw each get their own catalog; codex/opencode absent
    assert set(br.keys()) == {"claude_code", "goose", "openclaw"}
    assert "codex" not in br and "opencode" not in br

    cc = {t["name"]: t["calls"] for t in br["claude_code"]["tools"]}
    assert cc == {"Bash": 2, "Read": 1}
    assert br["goose"]["totals"]["total_calls"] == 1
    assert br["openclaw"]["totals"]["total_calls"] == 1

    # reconciliation: per-runtime call counts sum to the aggregate
    agg_calls = sum(t["calls"] for t in slice_["tools"])
    rt_calls = sum(d["totals"]["total_calls"] for d in br.values())
    assert agg_calls == rt_calls == 5
