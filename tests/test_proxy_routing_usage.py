"""Tests for issue #3438 — smart model routing savings attribution in /api/usage.

Verifies that:
1. query_routing_savings() aggregates auto_downgraded events correctly.
2. Per-(from_model, to_model) pair stats are accurate.
3. Empty workspace returns zero-valued result, not an exception.
4. _try_local_store_usage() includes routing_savings_usd and
   routing_substitutions in its return dict.
"""

from __future__ import annotations

import importlib
import uuid

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

# Use a timestamp that is always within a 30-day window from today
# (2026-06 is within 30 days of 2026-07-01, the current date).
_RECENT_TS = "2026-06-25T10:00:00"
_OLD_TS = "2020-01-01T00:00:00"


def _seed_routing_events(store, events):
    """Ingest a list of auto_downgraded event payloads into the store and flush."""
    for ev in events:
        store.ingest({
            "id": uuid.uuid4().hex,
            "node_id": "node-1",
            "agent_id": "clawmetry-proxy",
            "agent_type": "openclaw",
            "event_type": "auto_downgraded",
            "ts": ev.get("ts", _RECENT_TS),
            "session_id": ev.get("session_id", "sess-1"),
            "data": {
                "from_model": ev["from_model"],
                "to_model": ev["to_model"],
                "estimated_saved_usd": ev["estimated_saved_usd"],
                "reason": ev.get("reason", "short-no-tools"),
            },
        })
    # ingest() queues in the ring buffer; flush to DuckDB before querying.
    store._flush_now()


# ---------------------------------------------------------------------------
# Fixture
# ---------------------------------------------------------------------------

@pytest.fixture
def store(tmp_path, monkeypatch):
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "events.duckdb"))
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_READ", "1")
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_SECS", "0.05")
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_BATCH", "5")

    import clawmetry.local_store as ls
    importlib.reload(ls)

    s = ls.get_store()
    yield s
    try:
        s.stop(flush=True)
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Unit tests: query_routing_savings()
# ---------------------------------------------------------------------------

def test_empty_store_returns_zero(store):
    result = store.query_routing_savings(days=30)
    assert result["total_savings_usd"] == 0.0
    assert result["total_substitutions"] == 0
    assert result["by_pair"] == []


def test_single_substitution(store):
    _seed_routing_events(store, [
        {"from_model": "claude-opus-4-8", "to_model": "claude-haiku-4-5",
         "estimated_saved_usd": 0.005},
    ])
    result = store.query_routing_savings(days=30)
    assert result["total_substitutions"] == 1
    assert abs(result["total_savings_usd"] - 0.005) < 1e-9
    assert len(result["by_pair"]) == 1
    pair = result["by_pair"][0]
    assert pair["from_model"] == "claude-opus-4-8"
    assert pair["to_model"] == "claude-haiku-4-5"
    assert pair["count"] == 1
    assert abs(pair["saved_usd"] - 0.005) < 1e-9


def test_multiple_substitutions_same_pair(store):
    _seed_routing_events(store, [
        {"from_model": "claude-opus-4-8", "to_model": "claude-haiku-4-5",
         "estimated_saved_usd": 0.003},
        {"from_model": "claude-opus-4-8", "to_model": "claude-haiku-4-5",
         "estimated_saved_usd": 0.007},
    ])
    result = store.query_routing_savings(days=30)
    assert result["total_substitutions"] == 2
    assert abs(result["total_savings_usd"] - 0.01) < 1e-9
    assert len(result["by_pair"]) == 1
    assert result["by_pair"][0]["count"] == 2


def test_multiple_pairs_sorted_by_savings(store):
    _seed_routing_events(store, [
        {"from_model": "gpt-4o", "to_model": "gpt-4o-mini",
         "estimated_saved_usd": 0.001},
        {"from_model": "claude-opus-4-8", "to_model": "claude-haiku-4-5",
         "estimated_saved_usd": 0.010},
    ])
    result = store.query_routing_savings(days=30)
    assert result["total_substitutions"] == 2
    # Highest-savings pair must come first
    assert result["by_pair"][0]["from_model"] == "claude-opus-4-8"
    assert result["by_pair"][1]["from_model"] == "gpt-4o"


def test_days_window_excludes_old_events(store):
    _seed_routing_events(store, [
        {"from_model": "claude-opus-4-8", "to_model": "claude-haiku-4-5",
         "estimated_saved_usd": 0.005, "ts": _OLD_TS},
    ])
    result = store.query_routing_savings(days=30)
    assert result["total_substitutions"] == 0
    assert result["total_savings_usd"] == 0.0


# ---------------------------------------------------------------------------
# Integration test: _try_local_store_usage() exposes routing fields
# ---------------------------------------------------------------------------

def test_usage_fast_path_includes_routing_fields(tmp_path, monkeypatch):
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "u.duckdb"))
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_READ", "1")
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_SECS", "0.05")
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_BATCH", "5")

    import clawmetry.local_store as ls
    importlib.reload(ls)
    import routes.usage as ru
    importlib.reload(ru)

    s = ls.get_store()
    try:
        # Seed enough cost events to satisfy the fast-path (needs aggregates or events).
        for i in range(6):
            s.ingest({
                "id": uuid.uuid4().hex,
                "node_id": "node-1",
                "agent_id": "agent-1",
                "agent_type": "openclaw",
                "event_type": "model.completed",
                "ts": _RECENT_TS,
                "session_id": "sess-1",
                "cost_usd": 0.01,
                "token_count": 500,
            })
        # The 6th ingest triggers auto-flush (FLUSH_BATCH=5 -> flushes at 5).
        # Also seed one routing event.
        s.ingest({
            "id": uuid.uuid4().hex,
            "node_id": "node-1",
            "agent_id": "clawmetry-proxy",
            "agent_type": "openclaw",
            "event_type": "auto_downgraded",
            "ts": _RECENT_TS,
            "session_id": "sess-1",
            "data": {
                "from_model": "claude-opus-4-8",
                "to_model": "claude-haiku-4-5",
                "estimated_saved_usd": 0.008,
                "reason": "short-no-tools",
            },
        })
        s._flush_now()

        result = ru._try_local_store_usage()
        assert result is not None, "_try_local_store_usage() returned None with seeded data"
        assert "routing_savings_usd" in result, "routing_savings_usd missing from /api/usage response"
        assert "routing_substitutions" in result, "routing_substitutions missing from /api/usage response"
        assert isinstance(result["routing_savings_usd"], float)
        assert isinstance(result["routing_substitutions"], list)
    finally:
        try:
            s.stop(flush=True)
        except Exception:
            pass


if __name__ == "__main__":
    import pytest as _pytest
    _pytest.main([__file__, "-v"])
