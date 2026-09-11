"""``query_quality_sessions(per_runtime_limit=...)`` against a real DuckDB.

The Harness Engineering bench read one cost-ordered, globally capped list. On a
live node claude_code (2007 sessions) took 1484 of the 1500 rows, codex took
the other 16, and copilot, cursor, pi, opencode, goose, hermes and four more
runtimes never reached the bench at all (2026-09-11).
"""

from __future__ import annotations

import collections
import importlib

import pytest


@pytest.fixture
def store(tmp_path, monkeypatch):
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_SECS", "3600")
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_BATCH", "100000")
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "q.duckdb"))
    import clawmetry.local_store as ls
    ls = importlib.reload(ls)
    s = ls.LocalStore()
    rows = []
    for i in range(30):  # the loud, expensive runtime
        rows.append({"session_id": f"claude_code:s{i}", "cost_usd": 100 + i})
    for i in range(3):
        rows.append({"session_id": f"pi:s{i}", "cost_usd": 0.01})
    rows.append({"session_id": "oc-1", "cost_usd": 0.02})  # bare id = openclaw
    for r in rows:
        r.update(agent_type="openclaw", node_id="n", agent_id="main",
                 last_active_at="2026-09-10T00:00:00", message_count=1,
                 total_tokens=10)
    s.ingest_sessions_batch(rows)
    try:
        yield s
    finally:
        try:
            s.stop(flush=False)
        except Exception:
            pass


def _by_runtime(rows):
    return collections.Counter(r["runtime"] for r in rows)


def test_global_cap_starves_quiet_runtimes(store):
    """The failure mode, pinned: an overall cap hands every row to the loud one."""
    got = _by_runtime(store.query_quality_sessions(limit=10))
    assert got == {"claude_code": 10}


def test_per_runtime_cap_keeps_every_runtime(store):
    got = _by_runtime(store.query_quality_sessions(limit=100, per_runtime_limit=10))
    assert got == {"claude_code": 10, "pi": 3, "openclaw": 1}


def test_per_runtime_cap_keeps_the_most_expensive_of_each(store):
    rows = store.query_quality_sessions(limit=100, per_runtime_limit=2)
    cc = sorted(r["cost_usd"] for r in rows if r["runtime"] == "claude_code")
    assert cc == [128, 129]


def test_runtime_filter_still_applies(store):
    got = _by_runtime(store.query_quality_sessions(
        runtime="pi", limit=100, per_runtime_limit=10))
    assert got == {"pi": 3}
