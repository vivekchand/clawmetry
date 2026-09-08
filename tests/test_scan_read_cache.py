"""The three scans the dashboard polls hardest are served from a bounded
cache that clears on every flush.

2026-09-02, founder Mac, two dashboard tabs open: ``query_events`` 145 calls a
minute, ``query_outcomes`` 41, ``query_tool_call_invocations`` 40 -- the last a
32,600-row scan costing 1.5 s live, so that one shape kept a core busy on its
own. None had a cache. Now duplicate polls between writes collapse into one
query, a flush drops the cache so nothing answers from before new rows, and
callers that recompute "now minus 30 days" per request still hit because the
window bounds are bucketed to the TTL for the key only.
"""
from __future__ import annotations

import pytest

duckdb = pytest.importorskip("duckdb")


@pytest.fixture
def store(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("CLAWMETRY_HOME", str(tmp_path / ".clawmetry"))
    monkeypatch.setenv("CLAWMETRY_AGG_CACHE_TTL", "20")
    import importlib

    import clawmetry.local_store as ls

    importlib.reload(ls)
    ls.DB_PATH = tmp_path / "test.duckdb"
    ls._oom_bumps = 0
    st = ls.LocalStore(read_only=False)
    st.ingest_many([
        {"id": f"e{i}", "node_id": "n1", "agent_type": "claude_code", "session_id": "s1",
         "event_type": "tool_call", "ts": f"2026-09-02T10:00:{i:02d}+00:00",
         "data": {"tool": "Bash"}}
        for i in range(5)
    ])
    st.flush()
    ls.invalidate_read_cache()
    ls._READ_CACHE_HITS.update({"hit": 0, "miss": 0})
    yield ls, st
    try:
        st.stop(flush=False)
    except Exception:
        pass


def test_a_repeated_scan_is_served_from_cache(store):
    ls, st = store
    a = st.query_tool_call_invocations(since="2026-09-01T00:00:00Z")
    b = st.query_tool_call_invocations(since="2026-09-01T00:00:00Z")
    assert a == b and len(a) == 5
    assert ls._READ_CACHE_HITS == {"hit": 1, "miss": 1}


def test_window_bounds_recomputed_per_request_still_hit(store):
    """Callers pass "now minus N days" and the string differs by milliseconds
    each poll; the key buckets it to the TTL so the second poll hits."""
    ls, st = store
    st.query_tool_call_invocations(since="2026-09-01T00:00:00.000Z")
    st.query_tool_call_invocations(since="2026-09-01T00:00:03.417Z")
    assert ls._READ_CACHE_HITS["hit"] == 1


def test_a_flush_clears_the_cache(store):
    """Freshness is bounded by the flush cadence, not the TTL."""
    ls, st = store
    assert len(st.query_events(limit=50)) == 5
    st.ingest({"id": "new", "node_id": "n1", "agent_type": "claude_code", "session_id": "s1",
               "event_type": "tool_call", "ts": "2026-09-02T10:01:00+00:00"})
    st.flush()
    assert len(st.query_events(limit=50)) == 6


def test_different_filters_do_not_share_an_entry(store):
    ls, st = store
    assert len(st.query_events(limit=2)) == 2
    assert len(st.query_events(limit=5)) == 5
    assert len(st.query_events(limit=5, event_type="tool_result")) == 0


def test_the_cache_is_bounded(store):
    ls, st = store
    for i in range(ls._READ_CACHE_MAX + 10):
        st.query_events(limit=i + 1)
    assert len(ls._READ_CACHE) <= ls._READ_CACHE_MAX


def test_ttl_zero_disables_it(store, monkeypatch):
    ls, st = store
    monkeypatch.setattr(ls, "_AGG_CACHE_TTL", 0.0)
    st.query_outcomes()
    st.query_outcomes()
    assert ls._READ_CACHE_HITS["hit"] == 0


def test_health_reports_cache_activity(store):
    ls, st = store
    st.query_events(limit=3)
    st.query_events(limit=3)
    h = st.health()
    assert h["read_cache_hits"] == 1 and h["read_cache_misses"] == 1
    assert h["read_cache_entries"] >= 1
