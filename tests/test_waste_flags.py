"""Per-run waste-flag heuristics (#2196 item #3)."""
from __future__ import annotations

import importlib
import json

import pytest

from clawmetry import waste_flags as wf


# ── compute_flags ──────────────────────────────────────────────────────────

def test_empty_or_partial_signals_emit_nothing():
    assert wf.compute_flags({}) == []
    assert wf.compute_flags(None) == []
    assert wf.compute_flags("not a dict") == []
    # Partial: step_count only, no waste
    assert wf.compute_flags({"step_count": 3}) == []


def test_runaway_flag():
    out = wf.compute_flags({"step_count": 99})
    assert any(f["type"] == "runaway" for f in out)
    assert "99 steps" in next(f for f in out if f["type"] == "runaway")["msg"]


def test_cold_cache_requires_min_steps_and_low_ratio():
    # 2 steps -> below COLD_CACHE_MIN_STEPS, no flag
    assert not any(f["type"] == "cold_cache" for f in wf.compute_flags({
        "step_count": 2, "cache_read_tokens": 0, "input_tokens": 1000,
    }))
    # Enough steps + low hit ratio -> flagged
    out = wf.compute_flags({
        "step_count": 20, "cache_read_tokens": 1000, "input_tokens": 9000,
    })
    cold = [f for f in out if f["type"] == "cold_cache"]
    assert cold and "10%" in cold[0]["msg"]
    # Healthy cache + plenty of steps -> no flag
    assert not any(f["type"] == "cold_cache" for f in wf.compute_flags({
        "step_count": 20, "cache_read_tokens": 9500, "input_tokens": 500,
    }))


def test_unscoped_result_and_bloated_context():
    out = wf.compute_flags({
        "max_tool_result_bytes": 50_000,
        "max_event_token_count": 120_000,
    })
    types = {f["type"] for f in out}
    assert "unscoped_result" in types
    assert "bloated_context" in types


def test_threshold_env_overrides(monkeypatch):
    monkeypatch.setenv("CLAWMETRY_WASTE_RUNAWAY_STEPS", "3")
    importlib.reload(wf)
    assert any(f["type"] == "runaway" for f in wf.compute_flags({"step_count": 4}))


# ── compute_signals_from_events ────────────────────────────────────────────

def test_signals_aggregate_tool_calls_and_results():
    # Reload module so any env-tweaks from above don't leak into this test
    importlib.reload(wf)
    rows = [
        # Two tool calls -> step_count=2
        {"event_type": "tool_call", "data": {}, "token_count": 0},
        {"event_type": "tool.call", "data": None, "token_count": 0},
        # Tool result with a big body -> max_tool_result_bytes
        {"event_type": "tool_result", "token_count": 0,
         "data": {"content": "x" * 20_000, "role": "tool"}},
        # Assistant turn carrying token split via data.usage
        {"event_type": "assistant", "token_count": 80_000,
         "data": {"role": "assistant",
                  "usage": {"input": 1000, "cacheRead": 9000}}},
        # Same shape but via data.extra (claude_code family)
        {"event_type": "assistant", "token_count": 4000,
         "data": {"_runtime": "claude_code",
                  "extra": {"inputTokens": 500, "cacheReadInputTokens": 4500}}},
        # Bytes-encoded data must be parsed back
        {"event_type": "tool_call", "token_count": 0,
         "data": json.dumps({"foo": "bar"}).encode("utf-8")},
    ]
    s = wf.compute_signals_from_events(rows)
    assert s["step_count"] == 3  # 2 tool_call + 1 byte-encoded tool_call
    assert s["max_tool_result_bytes"] > 20_000
    assert s["max_event_token_count"] == 80_000
    assert s["cache_read_tokens"] == 13_500  # 9000 + 4500
    assert s["input_tokens"] == 1_500       # 1000 + 500


def test_signals_then_flags_end_to_end():
    importlib.reload(wf)
    # Build a synthetic runaway run: 31 tool calls + a bloated step.
    rows = []
    for _ in range(31):
        rows.append({"event_type": "tool_call", "data": {}, "token_count": 0})
    rows.append({"event_type": "assistant", "token_count": 60_000,
                 "data": {"usage": {"input": 60_000}}})
    flags = wf.compute_flags(wf.compute_signals_from_events(rows))
    types = {f["type"] for f in flags}
    assert {"runaway", "bloated_context"}.issubset(types)


def test_signals_never_raises_on_garbage():
    importlib.reload(wf)
    rows = [
        {"event_type": None, "data": object()},
        {"event_type": 12345, "data": "not json"},
        {},
        {"event_type": "tool_call", "token_count": "not-a-number", "data": b"not-json"},
    ]
    s = wf.compute_signals_from_events(rows)
    # Only the last row's event_type matches tool_call -> step_count=1
    assert s["step_count"] == 1
    # Everything else stays at zero rather than crashing
    assert s["max_tool_result_bytes"] == 0
    assert s["max_event_token_count"] == 0


# ── snapshot integration ───────────────────────────────────────────────────


def test_build_waste_flags_in_snapshot(tmp_path, monkeypatch):
    """Integrate-test the daemon's _build_waste_flags(): ingest synthetic
    sessions and assert flagged ones land in the map and clean ones don't."""
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "ev.duckdb"))
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_SECS", "0.05")
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_BATCH", "2")
    monkeypatch.delenv("CLAWMETRY_ROLE", raising=False)
    import clawmetry.local_store as ls
    importlib.reload(ls)
    monkeypatch.setattr(ls, "_daemon_registered", lambda: False)
    store = ls.get_store()
    # Patch the sync module's get_store() lookup to return ours.
    from clawmetry import sync as syncmod
    monkeypatch.setattr(syncmod, "_resolve_openclaw_bin", lambda: None, raising=False)

    # Runaway session: 35 tool_call events.
    for i in range(35):
        store.ingest({
            "id": f"runaway:ev-{i}",
            "node_id": "n", "agent_id": "main", "session_id": "sess-runaway",
            "event_type": "tool_call",
            "ts": f"2026-05-28T12:00:{i:02d}Z",
            "data": {"name": "Bash"},
            "cost_usd": None, "token_count": 0, "model": None,
        })
    # Clean session: 3 tool_call events, nothing unusual.
    for i in range(3):
        store.ingest({
            "id": f"clean:ev-{i}",
            "node_id": "n", "agent_id": "main", "session_id": "sess-clean",
            "event_type": "tool_call",
            "ts": f"2026-05-28T13:00:{i:02d}Z",
            "data": {"name": "Read"},
            "cost_usd": None, "token_count": 0, "model": None,
        })
    # Flush ring -> events table.
    deadline_helper = lambda: store.health()["ring_depth"] == 0
    import time as _t
    end = _t.monotonic() + 3
    while _t.monotonic() < end and not deadline_helper():
        _t.sleep(0.02)

    try:
        out = syncmod._build_waste_flags()
        assert "sess-runaway" in out, f"runaway should be flagged: keys={list(out)}"
        assert any(f["type"] == "runaway" for f in out["sess-runaway"])
        assert "sess-clean" not in out, "clean sessions must be omitted (empty == clean)"
    finally:
        store.stop(flush=True)


# ── Health-timeline helpers + snapshot builder (#2196 item #4) ──────────────


def test_runtime_from_session_id():
    importlib.reload(wf)
    assert wf.runtime_from_session_id("claude_code:abc-def") == "claude_code"
    assert wf.runtime_from_session_id("Cursor:xyz") == "cursor"  # lower-cased
    # OpenClaw sessions are bare UUIDs -> default bucket
    assert wf.runtime_from_session_id("12345678-1234-1234-1234-1234567890ab") == "openclaw"
    # garbage in -> default bucket, never raises
    assert wf.runtime_from_session_id(None) == "openclaw"
    assert wf.runtime_from_session_id("") == "openclaw"
    assert wf.runtime_from_session_id(":no-head") == "openclaw"


def test_severity_from_counts():
    importlib.reload(wf)
    assert wf.severity_from_counts(0, 0) == "green"
    assert wf.severity_from_counts(0, 3) == "yellow"
    assert wf.severity_from_counts(1, 0) == "red"
    assert wf.severity_from_counts(2, 5) == "red"  # error wins
    # garbage-safe
    assert wf.severity_from_counts(None, "bad") == "green"


def test_event_is_real_error_reads_corrected_flag():
    importlib.reload(wf)
    # Anthropic / v3 shape: top-level is_error
    assert wf.event_is_real_error({"data": {"is_error": True}})
    # Claude Code shape: nested in extra
    assert wf.event_is_real_error({"data": {"extra": {"isError": True}}})
    # Stored data may be encoded as JSON bytes
    assert wf.event_is_real_error({"data": json.dumps({"is_error": True}).encode("utf-8")})
    # Cleared (corrected) flag -> not an error
    assert not wf.event_is_real_error({"data": {"is_error": False, "benign_error": True}})
    # Garbage / no data -> not an error, no exception
    assert not wf.event_is_real_error({})
    assert not wf.event_is_real_error(None)
    assert not wf.event_is_real_error({"data": "not json"})


def test_build_health_timeline_bucketed_by_runtime(tmp_path, monkeypatch):
    """End-to-end snapshot builder: real + clean + flagged sessions across two
    runtimes; assert dots land in the right bucket with the right severity."""
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "ev.duckdb"))
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_SECS", "0.05")
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_BATCH", "2")
    monkeypatch.delenv("CLAWMETRY_ROLE", raising=False)
    import clawmetry.local_store as ls
    importlib.reload(ls)
    monkeypatch.setattr(ls, "_daemon_registered", lambda: False)
    store = ls.get_store()

    # Claude Code session — one tool_call (clean) + one real tool error
    store.ingest({
        "id": "cc:1", "node_id": "n", "agent_id": "main",
        "session_id": "claude_code:sess-red",
        "event_type": "tool_call", "ts": "2026-05-28T10:00:00Z",
        "data": {"name": "Bash"}, "cost_usd": None, "token_count": 0,
        "model": None,
    })
    store.ingest({
        "id": "cc:2", "node_id": "n", "agent_id": "main",
        "session_id": "claude_code:sess-red",
        "event_type": "tool_result", "ts": "2026-05-28T10:00:01Z",
        "data": {"role": "tool", "_runtime": "claude_code",
                 "content": "Exit code 1\nTraceback ...",
                 "extra": {"isError": True}},
        "cost_usd": None, "token_count": 0, "model": None,
    })
    # OpenClaw session — runaway (35 tool_call events), no errors
    for i in range(35):
        store.ingest({
            "id": f"oc:{i}", "node_id": "n", "agent_id": "main",
            "session_id": "11111111-2222-3333-4444-555555555555",
            "event_type": "tool_call", "ts": f"2026-05-28T11:00:{i:02d}Z",
            "data": {"name": "Bash"}, "cost_usd": None, "token_count": 0,
            "model": None,
        })
    # Goose session — clean
    store.ingest({
        "id": "g:1", "node_id": "n", "agent_id": "main",
        "session_id": "goose:happy", "event_type": "tool_call",
        "ts": "2026-05-28T12:00:00Z", "data": {"name": "Read"},
        "cost_usd": None, "token_count": 0, "model": None,
    })

    import time as _t
    end = _t.monotonic() + 3
    while _t.monotonic() < end and store.health()["ring_depth"] > 0:
        _t.sleep(0.02)

    try:
        from clawmetry import sync as syncmod
        out = syncmod._build_health_timeline()
        runtimes = {r["runtime"]: r["dots"] for r in out.get("runtimes", [])}
        # All three runtimes represented
        assert {"claude_code", "openclaw", "goose"}.issubset(set(runtimes.keys())), \
            f"runtimes={list(runtimes.keys())}"
        # Severity per session
        cc_dot = next(d for d in runtimes["claude_code"] if "sess-red" in d["session_id"])
        assert cc_dot["severity"] == "red", cc_dot
        oc_dot = next(d for d in runtimes["openclaw"]
                       if d["session_id"].startswith("11111111"))
        assert oc_dot["severity"] == "yellow", oc_dot
        assert oc_dot["flag_count"] >= 1 and "runaway" in oc_dot["flag_types"]
        g_dot = next(d for d in runtimes["goose"] if d["session_id"] == "goose:happy")
        assert g_dot["severity"] == "green", g_dot
    finally:
        store.stop(flush=True)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
