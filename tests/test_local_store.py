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
    # Re-assert the version comes out of health() rather than hardcoding it.
    # Hardcoded values silently drift each time someone bumps SCHEMA_VERSION
    # (was 6 at #1007, drifted to 9 by #1626; #1627). Reading the constant
    # lets the assertion auto-track future bumps while still catching the
    # "schema_version reported wrong" class of bug.
    from clawmetry.local_store import SCHEMA_VERSION
    assert h["schema_version"] == SCHEMA_VERSION
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


# ── read-only mode (cross-process dashboard read while daemon writes) ──────


def test_read_only_mode_skips_migration_and_flusher(tmp_path, monkeypatch):
    """RO LocalStore opens the DB without writing (no migration, no flusher).
    Required so the dashboard process can attach to a daemon-owned file."""
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "events.duckdb"))
    import clawmetry.local_store as ls
    importlib.reload(ls)
    # First open RW to materialise the schema
    rw = ls.LocalStore(read_only=False)
    rw.start()
    rw.ingest({"id": "e1", "node_id": "n1", "event_type": "x",
               "ts": int(time.time() * 1000)})
    time.sleep(0.2)
    rw.stop(flush=True)
    # Now reopen RO — should NOT raise + ingest must refuse
    ro = ls.LocalStore(read_only=True)
    assert ro._read_only is True
    assert ro._flusher_thread is None
    ro.start()  # no-op in RO
    assert ro._flusher_thread is None
    rows = ro.query_events(limit=10)
    assert len(rows) == 1
    with pytest.raises(RuntimeError, match="read-only"):
        ro.ingest({"id": "e2", "node_id": "n1", "event_type": "x",
                   "ts": int(time.time() * 1000)})
    ro.stop(flush=False)


def test_get_store_ro_after_rw_returns_writer(tmp_path, monkeypatch):
    """Same-process: get_store(read_only=True) shares the writer's connection
    when one already exists (DuckDB rejects an RO handle next to an RW one
    in the same process)."""
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "events.duckdb"))
    import clawmetry.local_store as ls
    importlib.reload(ls)
    ls._reset_singleton_for_tests()
    writer = ls.get_store(read_only=False)
    assert writer._read_only is False
    reader = ls.get_store(read_only=True)
    assert reader is writer  # shared connection


def test_get_store_ro_first_isolated(tmp_path, monkeypatch):
    """When a process only ever reads (typical dashboard-only-mode), the RO
    singleton stands alone."""
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "events.duckdb"))
    # Bootstrap the file by writing then closing (mimics daemon having run earlier)
    import clawmetry.local_store as ls
    importlib.reload(ls)
    seed = ls.LocalStore(read_only=False)
    seed.start()
    seed.ingest({"id": "x", "node_id": "n", "event_type": "x",
                 "ts": int(time.time() * 1000)})
    time.sleep(0.2)
    seed.stop(flush=True)
    importlib.reload(ls)  # fresh process boundary
    ls._reset_singleton_for_tests()
    reader = ls.get_store(read_only=True)
    assert reader._read_only is True
    rows = reader.query_events(limit=5)
    assert len(rows) == 1


# ── phase-3 query helpers (issue #1088 follow-up, 2026-05-13) ─────────────


def test_query_compactions_round_trip(store):
    """compaction events round-trip back as projected rows with summary,
    tokens_before, first_kept_entry_id, and from_hook fields."""
    store.ingest(_ev(
        id="cmp-1",
        session_id="sess-cmp",
        event_type="compaction",
        ts="2026-05-12T10:00:00Z",
        data={
            "type": "compaction",
            "timestamp": "2026-05-12T10:00:00Z",
            "summary": "Compacted 12 messages → 2K-token summary",
            "tokensBefore": 8500,
            "firstKeptEntryId": "ent-42",
            "fromHook": True,
        },
    ))
    store.ingest(_ev(
        id="cmp-2",
        session_id="sess-other",
        event_type="compaction",
        ts="2026-05-12T11:00:00Z",
        data={"type": "compaction", "summary": "later one",
              "tokensBefore": 100, "firstKeptEntryId": "", "fromHook": False},
    ))
    _wait_for_flush(store)

    rows = store.query_compactions()
    assert len(rows) == 2
    # Most-recent first.
    assert rows[0]["session_id"] == "sess-other"
    assert rows[1]["session_id"] == "sess-cmp"
    assert rows[1]["summary"].startswith("Compacted")
    assert rows[1]["tokens_before"] == 8500
    assert rows[1]["first_kept_entry_id"] == "ent-42"
    assert rows[1]["from_hook"] is True

    # session_id filter narrows.
    only_one = store.query_compactions(session_id="sess-cmp")
    assert [r["session_id"] for r in only_one] == ["sess-cmp"]


def test_query_cost_split_aggregates_per_session(store):
    """Two assistant turns in the same session aggregate into one cost-split
    row with summed tokens + costs and a primary_model derived from the
    most-used model."""
    for i in range(2):
        store.ingest(_ev(
            id=f"cs-{i}",
            session_id="sess-cs",
            event_type="message",
            ts=f"2026-05-12T10:0{i}:00Z",
            model="claude-opus-4-7",
            data={
                "type": "message",
                "message": {
                    "role": "assistant",
                    "model": "claude-opus-4-7",
                    "content": [{"type": "text", "text": "ok"}],
                    "usage": {
                        "input": 1000, "output": 500,
                        "cacheRead": 2000, "cacheWrite": 100,
                        "totalTokens": 3600,
                        "cost": {"input": 0.01, "output": 0.02,
                                 "cacheRead": 0.001, "cacheWrite": 0.0005,
                                 "total": 0.0315},
                    },
                },
            },
        ))
    # A different session that should appear as a second row.
    store.ingest(_ev(
        id="cs-other",
        session_id="sess-cs-other",
        event_type="message",
        ts="2026-05-12T10:05:00Z",
        model="claude-haiku-4",
        data={
            "type": "message",
            "message": {
                "role": "assistant", "model": "claude-haiku-4",
                "content": [{"type": "text", "text": "x"}],
                "usage": {"input": 100, "output": 50, "totalTokens": 150,
                          "cost": {"total": 0.001, "input": 0.0007, "output": 0.0003}},
            },
        },
    ))
    _wait_for_flush(store)

    rows = store.query_cost_split()
    assert len(rows) == 2
    by_sid = {r["session_id"]: r for r in rows}
    aggregated = by_sid["sess-cs"]
    assert aggregated["primary_model"] == "claude-opus-4-7"
    assert aggregated["input_tokens"] == 2000
    assert aggregated["output_tokens"] == 1000
    assert aggregated["cache_read_tokens"] == 4000
    assert aggregated["cache_write_tokens"] == 200
    assert aggregated["total_tokens"] == 7200
    assert aggregated["total_cost_usd"] == pytest.approx(0.063, abs=1e-6)
    # Cache hit ratio = cache_read / (input + cache_read) = 4000 / 6000 = 66.7%
    assert aggregated["cache_hit_ratio_pct"] == pytest.approx(66.7, abs=0.1)
    # Single-session lookup ignores aggregations from other sessions.
    only = store.query_cost_split(session_id="sess-cs")
    assert len(only) == 1
    assert only[0]["session_id"] == "sess-cs"


def test_query_session_model_journey_orders_segments(store):
    """model_change + assistant message events emerge in timestamp order with
    kind tags so the route can fold them into segments."""
    store.ingest(_ev(
        id="mj-mc-1",
        session_id="sess-mj",
        event_type="model_change",
        ts="2026-05-12T10:00:00Z",
        data={"modelId": "claude-sonnet-4-5", "provider": "anthropic"},
    ))
    store.ingest(_ev(
        id="mj-msg-1",
        session_id="sess-mj",
        event_type="message",
        ts="2026-05-12T10:01:00Z",
        model="claude-sonnet-4-5",
        data={
            "type": "message",
            "message": {
                "role": "assistant", "model": "claude-sonnet-4-5",
                "content": [{"type": "text", "text": "hi"}],
                "usage": {"totalTokens": 200, "cost": {"total": 0.003}},
            },
        },
    ))
    store.ingest(_ev(
        id="mj-think-1",
        session_id="sess-mj",
        event_type="thinking_level_change",
        ts="2026-05-12T10:02:00Z",
        data={"thinkingLevel": "high"},
    ))
    store.ingest(_ev(
        id="mj-mc-2",
        session_id="sess-mj",
        event_type="model_change",
        ts="2026-05-12T10:03:00Z",
        data={"modelId": "claude-opus-4-7", "provider": "anthropic"},
    ))
    # Different session — should not appear in the result.
    store.ingest(_ev(
        id="mj-other",
        session_id="sess-other",
        event_type="model_change",
        ts="2026-05-12T10:04:00Z",
        data={"modelId": "x", "provider": "y"},
    ))
    _wait_for_flush(store)

    rows = store.query_session_model_journey(session_id="sess-mj")
    assert [r["kind"] for r in rows] == [
        "model_change", "message", "thinking_level_change", "model_change"
    ]
    assert rows[0]["model"] == "claude-sonnet-4-5"
    assert rows[1]["total_tokens"] == 200
    assert rows[1]["total_cost"] == pytest.approx(0.003, abs=1e-6)
    assert rows[2]["level"] == "high"
    assert rows[3]["model"] == "claude-opus-4-7"
    # Empty session_id returns nothing rather than scanning the table.
    assert store.query_session_model_journey(session_id="") == []


# ── channel_messages (issue #1088 Phase 4) ───────────────────────────────


def test_channel_message_ingest_round_trip(store):
    """One inbound + one outbound message round-trips through DuckDB."""
    store.ingest_channel_message({
        "id":          "msg-tg-1",
        "agent_id":    "main",
        "provider":    "telegram",
        "channel_id":  "1234",
        "sender_id":   "user-7",
        "sender_name": "Alice",
        "body":        "hello world",
        "ts":          "2026-05-13T10:00:00Z",
        "direction":   "in",
        "session_key": "sess-A",
        "raw_blob":    {"message_id": 42},
    })
    store.ingest_channel_message({
        "id":         "msg-tg-2",
        "provider":   "Telegram",  # mixed case → lowercased
        "channel_id": "1234",
        "body":       "(reply)",
        "ts":         "2026-05-13T10:00:01Z",
        "direction":  "out",
    })
    rows = store.query_channel_messages(provider="telegram")
    assert len(rows) == 2
    # Most-recent first.
    assert rows[0]["id"] == "msg-tg-2"
    assert rows[1]["id"] == "msg-tg-1"
    # Provider lowercased on ingest.
    assert rows[0]["provider"] == "telegram"
    # raw_blob round-trips as a dict.
    assert rows[1]["raw_blob"] == {"message_id": 42}


def test_channel_message_validates_required_fields(store):
    """Missing id / provider / ts / bad direction all raise ValueError."""
    with pytest.raises(ValueError):
        store.ingest_channel_message({"provider": "tg", "ts": "x", "direction": "in"})
    with pytest.raises(ValueError):
        store.ingest_channel_message({"id": "1", "ts": "x", "direction": "in"})
    with pytest.raises(ValueError):
        store.ingest_channel_message({"id": "1", "provider": "tg", "direction": "in"})
    with pytest.raises(ValueError):
        store.ingest_channel_message({"id": "1", "provider": "tg", "ts": "x", "direction": "sideways"})


def test_query_channel_messages_filters_and_limit(store):
    """provider/channel_id/since/limit all gate the result set."""
    base = "2026-05-13T10:00:0"
    for i in range(5):
        store.ingest_channel_message({
            "id":         f"m-tg-{i}",
            "provider":   "telegram",
            "channel_id": "1111" if i < 3 else "2222",
            "body":       f"tg-{i}",
            "ts":         f"{base}{i}Z",
            "direction":  "in",
        })
    for i in range(2):
        store.ingest_channel_message({
            "id":         f"m-sl-{i}",
            "provider":   "slack",
            "channel_id": "C42",
            "body":       f"sl-{i}",
            "ts":         f"{base}{i}Z",
            "direction":  "in",
        })
    # Provider filter.
    assert {r["id"] for r in store.query_channel_messages(provider="slack")} == {
        "m-sl-0", "m-sl-1"
    }
    # channel_id filter scopes to one chat.
    assert {r["id"] for r in store.query_channel_messages(
        provider="telegram", channel_id="1111"
    )} == {"m-tg-0", "m-tg-1", "m-tg-2"}
    # since cuts off old rows.
    rows = store.query_channel_messages(
        provider="telegram", since="2026-05-13T10:00:03Z"
    )
    assert {r["id"] for r in rows} == {"m-tg-3", "m-tg-4"}
    # limit caps the page.
    assert len(store.query_channel_messages(provider="telegram", limit=2)) == 2


def test_query_channel_threads_groups_by_channel(store):
    """One row per channel_id, with in/out counts and last-* fields."""
    base = "2026-05-13T10:00:0"
    for i, body, dirn in [
        (0, "hi",        "in"),
        (1, "yo",        "in"),
        (2, "(reply)",   "out"),
        (3, "thx",       "in"),
    ]:
        store.ingest_channel_message({
            "id":          f"t-{i}",
            "provider":    "telegram",
            "channel_id":  "1234",
            "sender_name": "Alice" if dirn == "in" else "Bot",
            "body":        body,
            "ts":          f"{base}{i}Z",
            "direction":   dirn,
        })
    # Different channel_id — its own thread row.
    store.ingest_channel_message({
        "id":          "t-other",
        "provider":    "telegram",
        "channel_id":  "9999",
        "sender_name": "Bob",
        "body":        "stranger danger",
        "ts":          "2026-05-13T09:00:00Z",
        "direction":   "in",
    })
    threads = store.query_channel_threads(provider="telegram")
    by_chan = {t["channel_id"]: t for t in threads}
    assert set(by_chan) == {"1234", "9999"}
    main = by_chan["1234"]
    assert main["msg_in"] == 3
    assert main["msg_out"] == 1
    assert main["total"] == 4
    assert main["last_body"] == "thx"
    assert main["last_direction"] == "in"
    # Most-recent thread sorted first.
    assert threads[0]["channel_id"] == "1234"
    # Empty provider returns empty list (cheap guard).
    assert store.query_channel_threads(provider="") == []


def test_query_channel_summary_groups_across_providers(store):
    """One row per provider; in/out counts; distinct_channels honoured."""
    for i in range(3):
        store.ingest_channel_message({
            "id":         f"s-tg-{i}",
            "provider":   "telegram",
            "channel_id": "1" if i < 2 else "2",
            "body":       "x",
            "ts":         f"2026-05-13T10:00:0{i}Z",
            "direction":  "in" if i < 2 else "out",
        })
    store.ingest_channel_message({
        "id":         "s-sl-1",
        "provider":   "slack",
        "channel_id": "C42",
        "body":       "x",
        "ts":         "2026-05-13T11:00:00Z",
        "direction":  "in",
    })
    summary = store.query_channel_summary()
    by_prov = {r["provider"]: r for r in summary}
    assert set(by_prov) == {"telegram", "slack"}
    tg = by_prov["telegram"]
    assert tg["msg_in"] == 2
    assert tg["msg_out"] == 1
    assert tg["total"] == 3
    assert tg["distinct_channels"] == 2
    sl = by_prov["slack"]
    assert sl["msg_in"] == 1
    assert sl["distinct_channels"] == 1
