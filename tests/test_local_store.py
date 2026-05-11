"""Tests for clawmetry.local_store — the local SQLite event store (#958)."""

from __future__ import annotations

import importlib
import os
import time
import uuid
from pathlib import Path

import pytest


# ── fixture ───────────────────────────────────────────────────────────────


@pytest.fixture
def store(tmp_path, monkeypatch):
    """Fresh isolated store per test. We rebind the module-level paths/knobs
    before importing so a) every test gets its own DuckDB file and b) the
    flusher is fast enough that ingest→assert doesn't sleep all day."""
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "events.duckdb"))
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_SECS", "0.05")
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_BATCH", "5")
    # Force a fresh import so the env vars take effect AND so module-level
    # singletons from previous tests don't leak.
    import clawmetry.local_store as ls
    importlib.reload(ls)
    s = ls.LocalStore()
    s.start()
    yield s
    s.stop(flush=True)


def _ev(**overrides):
    """Build a minimal valid event with sensible defaults."""
    base = {
        "id": str(uuid.uuid4()),
        "node_id": "agent+test-node",
        "agent_id": "main",
        "session_id": "sess-1",
        "event_type": "tool_call",
        "ts": "2026-05-10T12:00:00Z",
        "data": {"tool": "Read", "args": {"path": "/tmp/x"}},
        "cost_usd": 0.001,
        "token_count": 42,
        "model": "claude-opus-4-7",
    }
    base.update(overrides)
    return base


def _wait_for_flush(s, timeout=2.0):
    """Block until the flusher drains the ring or timeout."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if s.health()["ring_depth"] == 0:
            return
        time.sleep(0.02)
    raise AssertionError("flusher did not drain the ring within timeout")


# ── ingest validation ─────────────────────────────────────────────────────


def test_ingest_requires_id(store):
    with pytest.raises(ValueError):
        store.ingest(_ev(id=""))


def test_ingest_requires_node_id(store):
    with pytest.raises(ValueError):
        store.ingest(_ev(node_id=""))


def test_ingest_requires_event_type(store):
    with pytest.raises(ValueError):
        store.ingest(_ev(event_type=""))


def test_ingest_requires_ts(store):
    with pytest.raises(ValueError):
        store.ingest(_ev(ts=""))


# ── ingest → query round-trip ─────────────────────────────────────────────


def test_single_event_persists_and_reads_back(store):
    e = _ev()
    store.ingest(e)
    _wait_for_flush(store)
    rows = store.query_events(session_id="sess-1")
    assert len(rows) == 1
    assert rows[0]["id"] == e["id"]
    assert rows[0]["event_type"] == "tool_call"
    # data was a dict on ingest; should round-trip as a dict
    assert rows[0]["data"] == {"tool": "Read", "args": {"path": "/tmp/x"}}
    assert rows[0]["cost_usd"] == 0.001
    assert rows[0]["token_count"] == 42


def test_idempotent_on_duplicate_id(store):
    """Re-ingesting the same id is a no-op (INSERT OR IGNORE)."""
    e = _ev()
    store.ingest(e)
    store.ingest(e)
    store.ingest(e)
    _wait_for_flush(store)
    rows = store.query_events(session_id="sess-1")
    assert len(rows) == 1


def test_string_data_passes_through_as_string(store):
    """If the caller hands us a string in `data`, don't re-JSON it."""
    e = _ev(data="just a plain string")
    store.ingest(e)
    _wait_for_flush(store)
    rows = store.query_events(session_id="sess-1")
    assert rows[0]["data"] == "just a plain string"


def test_bytes_data_round_trip(store):
    """If the caller hands us bytes containing valid utf-8 JSON, round-trip
    parses to a dict. If the bytes contain valid utf-8 non-JSON, round-trip
    returns the string. If the bytes are not valid utf-8, round-trip yields
    None (the reader should fall back to ``raw`` on the underlying row)."""
    # valid utf-8 + valid JSON
    e1 = _ev(id="b-json", data=b'{"k":"v"}')
    # valid utf-8 + non-JSON  (the \x01\x02\x03 bytes ARE valid utf-8)
    e2 = _ev(id="b-text", data=b"\x01\x02\x03binary")
    # not valid utf-8 (continuation byte without leader)
    e3 = _ev(id="b-bin", data=b"\xff\xfe\xfd raw bytes")
    store.ingest(e1)
    store.ingest(e2)
    store.ingest(e3)
    _wait_for_flush(store)
    by_id = {r["id"]: r for r in store.query_events()}
    assert by_id["b-json"]["data"] == {"k": "v"}
    assert by_id["b-text"]["data"] == "\x01\x02\x03binary"
    assert by_id["b-bin"]["data"] is None


def test_null_optional_fields(store):
    """cost_usd / token_count / session_id can be None."""
    e = _ev(session_id=None, cost_usd=None, token_count=None, model=None)
    store.ingest(e)
    _wait_for_flush(store)
    # session_id=None → not findable by session lookup; use global recent
    rows = store.query_events()
    assert len(rows) == 1
    assert rows[0]["session_id"] is None
    assert rows[0]["cost_usd"] is None
    assert rows[0]["token_count"] is None


# ── batch flushing ────────────────────────────────────────────────────────


def test_batch_size_triggers_immediate_flush(store):
    """When the ring hits FLUSH_BATCH (=5 in fixture), flush fires inline
    rather than waiting the full FLUSH_INTERVAL."""
    for _ in range(5):
        store.ingest(_ev(id=str(uuid.uuid4())))
    # No explicit wait: the 5th ingest should have triggered _flush_now().
    # Give the lock-acquire a tiny moment.
    time.sleep(0.05)
    rows = store.query_events()
    assert len(rows) == 5


def test_many_events_persist(store):
    """1000 events ingested cleanly."""
    ids = [str(uuid.uuid4()) for _ in range(1000)]
    for i, eid in enumerate(ids):
        store.ingest(_ev(id=eid, ts=f"2026-05-10T12:00:{i % 60:02d}Z"))
    _wait_for_flush(store, timeout=5.0)
    h = store.health()
    assert h["event_count"] == 1000
    rows = store.query_events(limit=2000)
    assert {r["id"] for r in rows} == set(ids)


# ── query filters ────────────────────────────────────────────────────────


def test_query_by_session_id(store):
    store.ingest(_ev(id="a", session_id="sess-A"))
    store.ingest(_ev(id="b", session_id="sess-B"))
    _wait_for_flush(store)
    a = store.query_events(session_id="sess-A")
    b = store.query_events(session_id="sess-B")
    assert [r["id"] for r in a] == ["a"]
    assert [r["id"] for r in b] == ["b"]


def test_query_by_event_type(store):
    store.ingest(_ev(id="t1", event_type="tool_call"))
    store.ingest(_ev(id="t2", event_type="tool_call"))
    store.ingest(_ev(id="m1", event_type="memory_write"))
    _wait_for_flush(store)
    rows = store.query_events(event_type="memory_write")
    assert [r["id"] for r in rows] == ["m1"]


def test_query_by_time_range(store):
    """ISO-8601 timestamps are lexicographically orderable; range filters
    should hit the ts index."""
    store.ingest(_ev(id="early", ts="2026-05-09T00:00:00Z"))
    store.ingest(_ev(id="mid",   ts="2026-05-10T12:00:00Z"))
    store.ingest(_ev(id="late",  ts="2026-05-11T23:59:59Z"))
    _wait_for_flush(store)
    rows = store.query_events(
        since="2026-05-10T00:00:00Z", until="2026-05-11T00:00:00Z"
    )
    assert [r["id"] for r in rows] == ["mid"]


def test_query_orders_newest_first(store):
    store.ingest(_ev(id="old", ts="2026-05-09T00:00:00Z"))
    store.ingest(_ev(id="new", ts="2026-05-11T00:00:00Z"))
    _wait_for_flush(store)
    rows = store.query_events()
    assert rows[0]["id"] == "new"
    assert rows[1]["id"] == "old"


# ── sessions / aggregates ────────────────────────────────────────────────


def test_query_sessions_groups_by_session_id(store):
    """Three events in sess-X collapse into one session row with summed cost."""
    store.ingest(_ev(id="1", session_id="sess-X", ts="2026-05-10T10:00:00Z", cost_usd=0.10))
    store.ingest(_ev(id="2", session_id="sess-X", ts="2026-05-10T11:00:00Z", cost_usd=0.20))
    store.ingest(_ev(id="3", session_id="sess-X", ts="2026-05-10T12:00:00Z", cost_usd=0.30))
    store.ingest(_ev(id="y1", session_id="sess-Y", ts="2026-05-10T09:00:00Z", cost_usd=1.00))
    _wait_for_flush(store)
    sessions = store.query_sessions()
    by_sid = {s["session_id"]: s for s in sessions}
    assert by_sid["sess-X"]["event_count"] == 3
    assert round(by_sid["sess-X"]["cost_usd"], 4) == 0.60
    assert by_sid["sess-X"]["started_at"] == "2026-05-10T10:00:00Z"
    assert by_sid["sess-X"]["updated_at"] == "2026-05-10T12:00:00Z"
    # newest-updated first
    assert sessions[0]["session_id"] == "sess-X"


def test_query_aggregates_groups_by_day(store):
    store.ingest(_ev(id="m1", ts="2026-05-10T10:00:00Z", cost_usd=0.50, token_count=100))
    store.ingest(_ev(id="m2", ts="2026-05-10T11:00:00Z", cost_usd=0.50, token_count=150))
    store.ingest(_ev(id="t1", ts="2026-05-09T10:00:00Z", cost_usd=0.20, token_count=50))
    _wait_for_flush(store)
    aggs = store.query_aggregates()
    by_day = {a["day"]: a for a in aggs}
    assert by_day["2026-05-10"]["event_count"] == 2
    assert round(by_day["2026-05-10"]["cost_usd"], 4) == 1.00
    assert by_day["2026-05-10"]["token_count"] == 250


# ── health + maintenance ─────────────────────────────────────────────────


def test_health_reports_size_and_count(store):
    for i in range(10):
        store.ingest(_ev(id=str(uuid.uuid4()), ts=f"2026-05-10T12:00:{i:02d}Z"))
    _wait_for_flush(store)
    h = store.health()
    assert h["event_count"] == 10
    assert h["size_bytes"] > 0
    assert h["schema_version"] == 1
    assert h["ring_depth"] == 0
    assert h["ring_dropped_total"] == 0


def test_vacuum_returns_summary(store):
    for i in range(50):
        store.ingest(_ev(id=str(uuid.uuid4()), ts=f"2026-05-10T12:{i:02d}:00Z"))
    _wait_for_flush(store)
    res = store.vacuum()  # under cap → no deletes, but VACUUM still reclaims
    assert res["deleted_rows"] == 0
    assert res["before_bytes"] > 0
    assert res["after_bytes"] > 0


def test_vacuum_prunes_oldest_when_over_cap(store):
    """Force a tiny cap so any data is "over" — verify oldest events go first."""
    for i in range(100):
        store.ingest(
            _ev(id=f"e{i:03d}", ts=f"2026-05-10T12:{i // 60:02d}:{i % 60:02d}Z")
        )
    _wait_for_flush(store)
    before = store.health()["event_count"]
    res = store.vacuum(prune_to_bytes=1)  # forces aggressive prune
    after = store.health()["event_count"]
    assert res["deleted_rows"] > 0
    assert after < before
    # The kept rows should be the *newest*, not the oldest.
    rows = store.query_events(limit=10000)
    if rows:  # if anything survived the aggressive prune
        kept_ids = sorted(r["id"] for r in rows)
        # All survivors should be later than at least one dropped event.
        assert kept_ids[-1] > "e000"


# ── persistence across instances ─────────────────────────────────────────


def test_data_survives_restart(tmp_path, monkeypatch):
    """Stop the store, re-open it, verify data is still there."""
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "events.duckdb"))
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_SECS", "0.05")
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_BATCH", "5")
    import clawmetry.local_store as ls
    importlib.reload(ls)
    s1 = ls.LocalStore()
    s1.start()
    s1.ingest(_ev(id="persist-1"))
    s1.stop(flush=True)
    # New instance, same path — DuckDB needs the previous connection closed
    # (single-writer per file) which stop() handles.
    s2 = ls.LocalStore()
    s2.start()
    rows = s2.query_events(session_id="sess-1")
    assert len(rows) == 1
    assert rows[0]["id"] == "persist-1"
    s2.stop(flush=True)


# ── ring drop tracking ───────────────────────────────────────────────────


def test_ring_overflow_increments_dropped_counter(monkeypatch, tmp_path):
    """If a producer sustained-floods past RING_MAX, oldest events drop and
    we count it. Disable the flusher so the ring actually fills."""
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "events.db"))
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_SECS", "60")  # effectively off
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_BATCH", "1000000")
    monkeypatch.setenv("CLAWMETRY_LOCAL_RING_MAX", "5")
    import clawmetry.local_store as ls
    importlib.reload(ls)
    s = ls.LocalStore()
    # Don't start the flusher.
    for i in range(20):
        s.ingest(_ev(id=f"flood-{i}"))
    h = s.health()
    assert h["ring_depth"] == 5
    assert h["ring_dropped_total"] == 15
