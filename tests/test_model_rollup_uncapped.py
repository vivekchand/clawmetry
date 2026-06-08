"""Regression guard for the uncapped per-runtime / per-model rollup.

The cloud Models tab + runtimeSummary snapshot builders
(``sync._build_runtime_summary`` / ``_build_model_attribution``) used to scan
``store.query_events(limit=20000)`` — the 20k MOST-RECENT events GLOBALLY. Once
a high-volume runtime (claude_code at 100k+ events) passed that budget it
consumed the whole window, so smaller runtimes (goose/hermes/opencode/qwen_code)
DROPPED OUT of the snapshot entirely and the big runtime itself was undercounted
~5× (the $15.97-vs-$19.86 / 22M-vs-134M-token screenshot, 2026-06-08).

``query_model_rollup`` replaces that with two SQL ``GROUP BY`` aggregates over
the FULL events table, so every event counts and no runtime is starved. These
tests pin:
  - every seeded runtime appears (no starvation), with EXACT token/cost/turn
    sums (no cap, no loss);
  - a bare-UUID session buckets to ``openclaw`` and reconciles to ground truth;
  - mid-session model switches are detected;
  - model-less events count toward tokens but not turns.
"""

from __future__ import annotations

import importlib
import time
from datetime import datetime, timezone

import pytest


def _iso(s: float) -> str:
    return datetime.fromtimestamp(s, tz=timezone.utc).isoformat()


def _wait_flush(store, t: float = 2.0) -> None:
    deadline = time.monotonic() + t
    while time.monotonic() < deadline:
        if store.health()["ring_depth"] == 0:
            return
        time.sleep(0.02)


@pytest.fixture
def store(tmp_path, monkeypatch):
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "events.duckdb"))
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_SECS", "0.05")
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_BATCH", "1")
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_READ", "1")
    import clawmetry.local_store as ls
    importlib.reload(ls)
    ls.mark_writer_owner()
    s = ls.get_store()
    yield s
    try:
        s.stop(flush=True)
    except Exception:
        pass


def _seed(store, sid, model, ts, *, tokens=100, cost=0.01, eid=None):
    store.ingest({
        "id": eid or (sid + "-" + str(int(ts * 1000))),
        "node_id": "agent+test",
        "agent_id": "main",
        "session_id": sid,
        "event_type": "tool_call",
        "ts": _iso(ts),
        "data": {"tool_name": "X"},
        "cost_usd": cost,
        "token_count": tokens,
        "model": model,
    })


def _seed_session(store, sid, *, tokens=0, cost=0.0):
    """Write the sessions-table row that the per-runtime TOTALS read from.

    In production every session is written here (sync_session_metadata / family
    adapters); family adapters stash the token total on the row while
    events.token_count stays 0, which is exactly why the rollup totals must come
    from this table, not the events sum."""
    store.ingest_session({
        "session_id": sid, "agent_type": "openclaw", "agent_id": "main",
        "status": "completed", "total_tokens": tokens, "cost_usd": cost,
        "last_active_at": _iso(1000.0),
    })


def test_rollup_includes_every_runtime_with_exact_totals(store):
    """No runtime starves; per-runtime token/cost/turn sums are exact."""
    now = time.time()
    # A high-volume runtime (claude_code) plus several small ones. Even a modest
    # count proves the contract: the rollup is a GROUP BY, not a recent-N slice.
    seeds = []
    for i in range(40):
        seeds.append(("claude_code:c1", "claude-opus-4-8", now - 5000 + i, 1000, 0.10))
    seeds += [
        ("goose:g1", "llama3.2", now - 100, 26487, 0.0),
        ("hermes:h1", "hermes-fast", now - 90, 8832, 0.0),
        ("opencode:o1", "opencode-1", now - 80, 22505, 0.0),
        ("qwen_code:q1", "qwen3:8b", now - 70, 50643, 0.0),
        # Bare-UUID OpenClaw session (the live one from the screenshot).
        ("682c73e4-aaa", "claude-opus-4-8", now - 60, 32760, 19.86),
    ]
    for j, (sid, m, ts, tok, cost) in enumerate(seeds):
        _seed(store, sid, m, ts, tokens=tok, cost=cost, eid=f"e{j}")
    # Per-runtime totals come from the sessions table (family adapters keep
    # the token total there, not on events). Mirror production by writing each
    # session row with its bridged total. Family runtimes (goose/hermes/…) keep
    # tokens ONLY on the session row — events.token_count is irrelevant for them.
    _seed_session(store, "claude_code:c1", tokens=40000, cost=4.00)
    _seed_session(store, "goose:g1", tokens=26487, cost=0.0)
    _seed_session(store, "hermes:h1", tokens=8832, cost=0.0)
    _seed_session(store, "opencode:o1", tokens=22505, cost=0.0)
    _seed_session(store, "qwen_code:q1", tokens=50643, cost=0.0)
    _seed_session(store, "682c73e4-aaa", tokens=32760, cost=19.86)
    _wait_flush(store)

    roll = store.query_model_rollup()
    by_rt = roll["by_runtime"]

    # Every seeded runtime is present — the bug DROPPED these entirely.
    for rt in ("claude_code", "goose", "hermes", "opencode", "qwen_code", "openclaw"):
        assert rt in by_rt, f"runtime {rt} starved out of the rollup: {list(by_rt)}"

    # Exact sums sourced from the bridged sessions table (no cap → no loss; and
    # family token totals are NOT lost just because events.token_count is 0).
    assert by_rt["goose"]["tokens"] == 26487
    assert by_rt["hermes"]["tokens"] == 8832
    assert by_rt["opencode"]["tokens"] == 22505
    assert by_rt["qwen_code"]["tokens"] == 50643
    # OpenClaw bare-UUID reconciles to ground truth.
    assert by_rt["openclaw"]["tokens"] == 32760
    assert round(by_rt["openclaw"]["cost_usd"], 2) == 19.86
    assert by_rt["openclaw"]["sessions"] == 1
    # claude_code: one session, totals from its bridged session row.
    assert by_rt["claude_code"]["tokens"] == 40000
    assert by_rt["claude_code"]["sessions"] == 1
    assert round(by_rt["claude_code"]["cost_usd"], 2) == 4.00


def test_rollup_carries_today_cost_split(store):
    """by_runtime carries a TODAY slice (events in the current UTC day) distinct
    from the LIFETIME cost_usd — the dual-column 'Your agents' view."""
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc).timestamp()
    old = now - 5 * 86400  # 5 days ago → counts toward lifetime, not today
    _seed(store, "claude_code:c1", "claude-opus-4-8", now - 60, cost=2.0, eid="t1")
    _seed(store, "claude_code:c1", "claude-opus-4-8", old, cost=8.0, eid="t2")
    _seed_session(store, "claude_code:c1", tokens=100, cost=10.0)
    _wait_flush(store)
    roll = store.query_model_rollup()
    cc = roll["by_runtime"]["claude_code"]
    assert round(cc["cost_today_usd"], 2) == 2.0, "today = only today's events"
    assert round(cc["cost_usd"], 2) == 10.0, "lifetime = the session total"


def test_rollup_detects_model_switches(store):
    now = time.time()
    _seed(store, "682c73e4-aaa", "claude-opus-4-8", now - 30, eid="s1")
    _seed(store, "682c73e4-aaa", "claude-sonnet-4-6", now - 20, eid="s2")
    _seed(store, "682c73e4-aaa", "claude-opus-4-8", now - 10, eid="s3")
    _wait_flush(store)
    roll = store.query_model_rollup()
    switches = roll["switches"]
    pairs = {(s["from_model"], s["to_model"]) for s in switches if s["runtime"] == "openclaw"}
    assert ("claude-opus-4-8", "claude-sonnet-4-6") in pairs
    assert ("claude-sonnet-4-6", "claude-opus-4-8") in pairs


def test_model_less_events_do_not_count_as_turns(store):
    now = time.time()
    _seed(store, "goose:g1", "llama3.2", now - 30, tokens=100, eid="m1")
    # A model-less event (e.g. a tool_result row).
    store.ingest({
        "id": "m2", "node_id": "agent+test", "agent_id": "main",
        "session_id": "goose:g1", "event_type": "tool_result",
        "ts": _iso(now - 20), "data": {}, "cost_usd": 0.0,
        "token_count": 50, "model": None,
    })
    # Session-level token total (the authoritative source for runtime totals).
    _seed_session(store, "goose:g1", tokens=150, cost=0.0)
    _wait_flush(store)
    roll = store.query_model_rollup()
    # Runtime total comes from the bridged session row, not the events sum.
    assert roll["by_runtime"]["goose"]["tokens"] == 150
    goose_models = [r for r in roll["by_runtime_model"] if r["runtime"] == "goose"]
    # Only the model-bearing event counts as a turn.
    assert sum(r["turns"] for r in goose_models) == 1


def test_event_totals_by_session_bridge(store):
    """query_event_totals_by_session sums the events table per session — the
    source the cloud-push bridge uses when OpenClaw JSONL has no usage."""
    now = time.time()
    _seed(store, "682c73e4-aaa", "claude-opus-4-8", now - 30, tokens=20000, cost=12.0, eid="b1")
    _seed(store, "682c73e4-aaa", "claude-opus-4-8", now - 20, tokens=12760, cost=7.86, eid="b2")
    _seed(store, "other-sid", "x", now - 10, tokens=5, cost=0.0, eid="b3")
    _wait_flush(store)
    totals = store.query_event_totals_by_session(["682c73e4-aaa", "missing-sid"])
    assert totals["682c73e4-aaa"]["tokens"] == 32760
    assert round(totals["682c73e4-aaa"]["cost_usd"], 2) == 19.86
    assert "missing-sid" not in totals
    assert "other-sid" not in totals  # not requested
