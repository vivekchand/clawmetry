"""Per-runtime snapshot slices for the cloud Cost + Context-economics tabs
(issue #3004).

The cloud runtime-scope sweep (clawmetry-cloud #1618) made every hosted tab
honest, but three sub-panels fell back to empty / lifetime-stand-in because the
daemon snapshot carried no per-runtime slice for them. This test pins the three
new slices the daemon now emits, all sourced from the materialized
``rollup_runtime_daily`` table (#2988) so they cost a cheap read, not a full
event scan (FLYWHEEL 1e):

1. ``dailyUsage.byRuntime[rt]`` — a 14-day per-runtime {day, tokens, cost_usd}
   series for the Cost 14-day chart.
2. ``runtimeSummary[rt].tokens_7d / cost_7d_usd / tokens_30d / cost_30d_usd`` —
   real rolling week/month windows per runtime for the Cost cards.
3. ``contextEconomics.byRuntime[rt].utilization / session_chips`` — the
   per-turn utilization series + the session-picker chips, bucketed per
   runtime for the Context-economics gauge.

All three are additive: the node-wide ``dailyUsage`` / ``runtimeSummary`` /
``contextEconomics`` keys are untouched.
"""
from __future__ import annotations

import importlib
from datetime import datetime, timedelta

import pytest


@pytest.fixture
def fresh_store(tmp_path, monkeypatch):
    """Isolated LocalStore on a tmp DuckDB path (manual flush)."""
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_SECS", "3600")
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_BATCH", "100000")
    monkeypatch.setenv(
        "CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "byruntime.duckdb")
    )
    import clawmetry.local_store as ls
    ls = importlib.reload(ls)
    store = ls.LocalStore()
    try:
        yield ls, store
    finally:
        try:
            store.stop(flush=False)
        except Exception:
            pass


def _day(offset_days: int) -> str:
    return (datetime.now() - timedelta(days=offset_days)).strftime("%Y-%m-%d")


def _seed_runtime_daily(store, rows):
    """Insert (day, runtime, tokens, cost_usd, sessions, active_sessions)
    directly into the materialized rollup, bypassing ingest so the test owns
    the exact per-day/per-runtime corpus."""
    with store._write_lock:
        for day, rt, tok, cost, sess, act in rows:
            store._conn.execute(
                "INSERT INTO rollup_runtime_daily "
                "(day, runtime, tokens, cost_usd, sessions, active_sessions) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                [day, rt, tok, cost, sess, act],
            )


def _corpus_rows():
    """Two runtimes across several days inside the 14d/7d/30d windows.

    claude_code: days 0,1,8,20  (so 7d window catches days 0+1 only;
                 30d catches all four; 14d series catches days 0,1,8)
    openclaw:    days 0,2,40    (day 40 is OUTSIDE every window)
    """
    return [
        # claude_code
        (_day(0),  "claude_code", 1000, 1.0, 2, 1),
        (_day(1),  "claude_code", 2000, 2.0, 1, 0),
        (_day(8),  "claude_code", 4000, 4.0, 3, 1),
        (_day(20), "claude_code", 8000, 8.0, 1, 0),
        # openclaw
        (_day(0),  "openclaw",     500, 0.5, 1, 1),
        (_day(2),  "openclaw",     700, 0.7, 2, 0),
        (_day(40), "openclaw",    9999, 9.9, 1, 0),  # outside 30d window
    ]


# ── 1. dailyUsage.byRuntime ──────────────────────────────────────────────

def test_daily_usage_by_runtime_14d_series(fresh_store, monkeypatch):
    ls, store = fresh_store
    _seed_runtime_daily(store, _corpus_rows())
    import clawmetry.sync as sync
    monkeypatch.setattr(sync, "_backfill_event_costs_once", lambda s: None)
    monkeypatch.setattr(sync, "_backfill_benign_errors_once", lambda s: None)
    monkeypatch.setattr(ls, "get_store", lambda *a, **k: store)

    du = sync._build_daily_usage(days=14)

    # Node-wide keys still present + unchanged in shape (additive).
    assert "days" in du and "today" in du and "monthCost" in du
    assert len(du["days"]) == 14

    br = du.get("byRuntime") or {}
    assert set(br.keys()) == {"claude_code", "openclaw"}

    # Each runtime series is exactly 14 points, oldest first, zero-filled.
    cc = br["claude_code"]
    assert len(cc) == 14
    assert [p["day"] for p in cc] == [_day(i) for i in range(13, -1, -1)]

    by_day = {p["day"]: p for p in cc}
    assert by_day[_day(0)]["tokens"] == 1000
    assert by_day[_day(0)]["cost_usd"] == 1.0
    assert by_day[_day(1)]["tokens"] == 2000
    assert by_day[_day(8)]["tokens"] == 4000
    # day 20 is outside the 14-day window -> not present as a point
    assert _day(20) not in by_day
    # a day with no rollup row is a zero-filled point, not missing
    assert by_day[_day(5)]["tokens"] == 0
    assert by_day[_day(5)]["cost_usd"] == 0.0

    oc = {p["day"]: p for p in br["openclaw"]}
    assert oc[_day(0)]["tokens"] == 500
    assert oc[_day(2)]["tokens"] == 700
    # the 14d sum per runtime reconciles with the seeded in-window rows
    assert sum(p["tokens"] for p in cc) == 1000 + 2000 + 4000
    assert sum(p["tokens"] for p in br["openclaw"]) == 500 + 700


# ── 2. runtimeSummary[rt] 7d / 30d windows ───────────────────────────────

def test_runtime_summary_7d_30d_windows(fresh_store, monkeypatch):
    ls, store = fresh_store
    _seed_runtime_daily(store, _corpus_rows())
    import clawmetry.sync as sync
    monkeypatch.setattr(ls, "get_store", lambda *a, **k: store)

    rs = sync._build_runtime_summary()

    assert "claude_code" in rs and "openclaw" in rs
    cc = rs["claude_code"]
    # existing fields are still present (additive change)
    assert "cost_24h_usd" in cc and "tokens_24h" in cc and "tokens" in cc

    # 7d window: days 0 + 1 only (day 8/20 are older than 6 days back)
    assert cc["tokens_7d"] == 1000 + 2000
    assert cc["cost_7d_usd"] == 3.0
    # 30d window: days 0 + 1 + 8 + 20
    assert cc["tokens_30d"] == 1000 + 2000 + 4000 + 8000
    assert cc["cost_30d_usd"] == 15.0

    oc = rs["openclaw"]
    assert oc["tokens_7d"] == 500 + 700
    assert oc["cost_7d_usd"] == 1.2
    # day 40 is outside the 30d window -> excluded
    assert oc["tokens_30d"] == 500 + 700
    assert oc["cost_30d_usd"] == 1.2


# ── 3. contextEconomics.byRuntime utilization + chips ────────────────────

def _util(sid, ts, pct):
    return {"session_id": sid, "ts": ts, "pct": pct, "tokens": 1, "window": 2}


def test_context_econ_by_runtime_buckets_util_and_chips(monkeypatch):
    import clawmetry.sync as sync
    monkeypatch.setattr(sync, "_runtime_of_session", lambda s: (
        s.split(":")[0] if ":" in s else "openclaw"))

    comps = [
        {"session_id": "claude_code:a", "trigger": "overflow", "reclaimed": 500},
        {"session_id": "goose:c", "trigger": "proactive", "reclaimed": 50},
    ]
    ovf = [{"session_id": "claude_code:a"}]
    base = {"peak_pct": 99.0, "utilization_points": 7}
    util = [
        _util("claude_code:a", "2026-06-10T10:00:00Z", 40.0),
        _util("claude_code:a", "2026-06-10T11:00:00Z", 80.0),
        _util("claude_code:b", "2026-06-10T12:00:00Z", 30.0),
        _util("goose:c", "2026-06-10T09:00:00Z", 55.0),
        # a runtime (codex) with readings but NO compactions still gets a slice
        _util("codex:z", "2026-06-10T08:00:00Z", 12.0),
    ]

    out = sync._context_econ_by_runtime(comps, ovf, base, utilization=util)

    # codex has utilization but no compaction -> still surfaces
    assert set(out.keys()) == {"claude_code", "goose", "codex"}

    cc = out["claude_code"]
    # utilization bucketed to claude_code's two sessions (3 points)
    assert len(cc["utilization"]) == 3
    assert {u["session_id"] for u in cc["utilization"]} == {
        "claude_code:a", "claude_code:b"}
    # session chips: one per distinct session, peak = max pct, most-recent first
    chips = {c["session_id"]: c for c in cc["session_chips"]}
    assert set(chips) == {"claude_code:a", "claude_code:b"}
    assert chips["claude_code:a"]["peak_pct"] == 80.0
    assert chips["claude_code:b"]["peak_pct"] == 30.0
    # peak recomputed from THIS runtime's points (80), not the node-wide 99
    assert cc["summary"]["peak_pct"] == 80.0
    assert cc["summary"]["utilization_points"] == 3
    # compactions/overflow still bucketed correctly
    assert cc["summary"]["compaction_count"] == 1
    assert [s["session_id"] for s in cc["overflow_sessions"]] == ["claude_code:a"]

    # codex: readings only, no compactions
    codex = out["codex"]
    assert codex["summary"]["compaction_count"] == 0
    assert codex["summary"]["utilization_points"] == 1
    assert codex["summary"]["peak_pct"] == 12.0
    assert [c["session_id"] for c in codex["session_chips"]] == ["codex:z"]


def test_context_econ_by_runtime_no_util_back_compat(monkeypatch):
    """Old call shape (no utilization) still works: empty util/chips per
    runtime, peak inherits the node-wide value."""
    import clawmetry.sync as sync
    monkeypatch.setattr(sync, "_runtime_of_session", lambda s: (
        s.split(":")[0] if ":" in s else "openclaw"))
    comps = [{"session_id": "goose:c", "trigger": "proactive", "reclaimed": 10}]
    out = sync._context_econ_by_runtime(comps, [], {"peak_pct": 42.0})
    assert out["goose"]["utilization"] == []
    assert out["goose"]["session_chips"] == []
    assert out["goose"]["summary"]["peak_pct"] == 42.0
