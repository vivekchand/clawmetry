"""#5496 / #5497 — upsert dedupe and the forward-progress window.

Background: on a real store the family adapters re-emitted every span and
session after each daemon restart, and ``ingest_spans_batch`` /
``ingest_sessions_batch`` re-ran each as DELETE+INSERT. DuckDB never
compacts the dead versions away, so 91,590 live spans carried 4,278,615
row versions and the file was 1.6 GB for 575 MB of data. The store now
keeps a content hash of the last row it wrote (in the table, so it survives
a restart, and in memory, so there is no lookup per row) and skips rows
whose content did not change.

These tests are the ruthless-verify guard: on the un-fixed code every
"writes nothing" assertion below fails with a non-zero write count.
"""
from __future__ import annotations

import importlib
from datetime import datetime, timedelta, timezone

import pytest


def _fresh_store_module(tmp_path, monkeypatch, name="dedupe.duckdb", **env):
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / name))
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_SECS", "999")
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_BATCH", "1000")
    for k, v in env.items():
        monkeypatch.setenv(k, v)
    import clawmetry.local_store as ls
    importlib.reload(ls)
    return ls


@pytest.fixture
def ls_mod(tmp_path, monkeypatch):
    return _fresh_store_module(tmp_path, monkeypatch)


@pytest.fixture
def store(ls_mod):
    s = ls_mod.LocalStore()
    try:
        yield s
    finally:
        s.stop(flush=True)


def _span(i: int, **overrides):
    base = {
        "span_id": f"sp-{i:04d}",
        "trace_id": "trace-1",
        "name": "tool.call",
        "start_ts": 1000.0 + i,
        "end_ts": 1001.0 + i,
        "agent_type": "claude_code",
        "session_id": "sess-1",
        "attributes": {"tool": "Bash", "i": i},
    }
    base.update(overrides)
    return base


def _sess(i: int, **overrides):
    base = {
        "agent_type": "openclaw",
        "session_id": f"sess-{i:04d}",
        "title": f"session {i}",
        "started_at": "2026-09-01T09:00:00Z",
        "last_active_at": "2026-09-01T10:00:00Z",
        "status": "active",
        "total_tokens": 100 + i,
        "cost_usd": 0.01 * i,
        "message_count": 3,
        "metadata": {"channel": "telegram"},
    }
    base.update(overrides)
    return base


def _versions(store, table):
    return store._conn.execute(
        "SELECT estimated_size FROM duckdb_tables() WHERE table_name = ?", [table]
    ).fetchone()[0]


# ── spans ─────────────────────────────────────────────────────────────────

def test_spans_identical_redelivery_writes_nothing(store):
    spans = [_span(i) for i in range(30)]
    assert store.ingest_spans_batch(spans) == 30
    assert store.ingest_spans_batch(spans) == 0
    assert store.ingest_spans_batch([_span(i) for i in range(30)]) == 0
    assert store._conn.execute("SELECT COUNT(*) FROM spans").fetchone()[0] == 30
    assert store._conn.execute(
        "SELECT COUNT(*) FROM spans WHERE content_hash IS NULL"
    ).fetchone()[0] == 0


def test_spans_changed_content_still_overwrites(store):
    store.ingest_spans_batch([_span(i) for i in range(5)])
    # A late-arriving end_ts is exactly the retry OTel exporters make.
    assert store.ingest_spans_batch([_span(0, end_ts=1500.0, name="tool.retry")]) == 1
    name, end_ts = store._conn.execute(
        "SELECT name, end_ts FROM spans WHERE span_id = 'sp-0000'"
    ).fetchone()
    assert (name, end_ts) == ("tool.retry", 1500.0)
    # Cost / status changes count as content too.
    assert store.ingest_spans_batch([_span(1, cost_usd=0.5)]) == 1
    assert store.ingest_spans_batch([_span(1, cost_usd=0.5)]) == 0


def test_spans_dedupe_survives_restart(tmp_path, monkeypatch):
    ls1 = _fresh_store_module(tmp_path, monkeypatch, name="restart.duckdb")
    s1 = ls1.LocalStore()
    try:
        assert s1.ingest_spans_batch([_span(i) for i in range(40)]) == 40
    finally:
        s1.stop(flush=True)
    ls2 = _fresh_store_module(tmp_path, monkeypatch, name="restart.duckdb")
    s2 = ls2.LocalStore()
    try:
        assert s2._span_hashes is None  # cold: seeded from the table on first use
        assert s2.ingest_spans_batch([_span(i) for i in range(40)]) == 0
        assert s2.ingest_spans_batch([_span(3, status="error")]) == 1
    finally:
        s2.stop(flush=True)


def test_spans_legacy_rows_without_hash_are_written_once(tmp_path, monkeypatch):
    ls1 = _fresh_store_module(tmp_path, monkeypatch, name="legacy.duckdb")
    s1 = ls1.LocalStore()
    try:
        s1.ingest_spans_batch([_span(i) for i in range(10)])
        # Simulate rows written by a pre-#5496 wheel: hash unknown.
        with s1._write_lock:
            s1._conn.execute("UPDATE spans SET content_hash = NULL")
    finally:
        s1.stop(flush=True)
    ls2 = _fresh_store_module(tmp_path, monkeypatch, name="legacy.duckdb")
    s2 = ls2.LocalStore()
    try:
        assert s2.ingest_spans_batch([_span(i) for i in range(10)]) == 10  # stamp once
        assert s2.ingest_spans_batch([_span(i) for i in range(10)]) == 0   # then never
    finally:
        s2.stop(flush=True)


def test_spans_kill_switch_restores_always_write(tmp_path, monkeypatch):
    ls = _fresh_store_module(tmp_path, monkeypatch, name="off.duckdb",
                             CLAWMETRY_UPSERT_DEDUPE="0")
    s = ls.LocalStore()
    try:
        assert s.ingest_spans_batch([_span(i) for i in range(5)]) == 5
        assert s.ingest_spans_batch([_span(i) for i in range(5)]) == 5
    finally:
        s.stop(flush=True)


def test_spans_in_batch_duplicates_keep_last(store):
    assert store.ingest_spans_batch([_span(0), _span(0, name="tool.last")]) == 1
    assert store._conn.execute(
        "SELECT name FROM spans WHERE span_id = 'sp-0000'"
    ).fetchone()[0] == "tool.last"


# ── sessions ──────────────────────────────────────────────────────────────

def test_sessions_identical_redelivery_writes_nothing(store):
    rows = [_sess(i) for i in range(20)]
    assert store.ingest_sessions_batch(rows) == 20
    assert store.ingest_sessions_batch([dict(r) for r in rows]) == 0
    for r in rows[:5]:
        store.ingest_session(dict(r))  # the per-row API delegates to the batch
    assert store._conn.execute("SELECT COUNT(*) FROM sessions").fetchone()[0] == 20
    assert store._conn.execute(
        "SELECT COUNT(*) FROM sessions WHERE content_hash IS NULL"
    ).fetchone()[0] == 0


def test_sessions_changed_content_still_upserts(store):
    store.ingest_sessions_batch([_sess(1)])
    assert store.ingest_sessions_batch([_sess(1, total_tokens=999,
                                              last_active_at="2026-09-01T11:00:00Z")]) == 1
    tokens, last = store._conn.execute(
        "SELECT total_tokens, last_active_at FROM sessions WHERE session_id = 'sess-0001'"
    ).fetchone()
    assert (tokens, last) == (999, "2026-09-01T11:00:00Z")
    # COALESCE semantics are unchanged: a re-ingest that lost the title keeps it.
    assert store.ingest_sessions_batch([_sess(1, total_tokens=999, title=None,
                                              last_active_at="2026-09-01T11:00:00Z")]) == 1
    assert store._conn.execute(
        "SELECT title FROM sessions WHERE session_id = 'sess-0001'"
    ).fetchone()[0] == "session 1"


def test_sessions_dedupe_survives_restart(tmp_path, monkeypatch):
    ls1 = _fresh_store_module(tmp_path, monkeypatch, name="srestart.duckdb")
    s1 = ls1.LocalStore()
    try:
        assert s1.ingest_sessions_batch([_sess(i) for i in range(15)]) == 15
    finally:
        s1.stop(flush=True)
    ls2 = _fresh_store_module(tmp_path, monkeypatch, name="srestart.duckdb")
    s2 = ls2.LocalStore()
    try:
        assert s2.ingest_sessions_batch([_sess(i) for i in range(15)]) == 0
        assert _versions(s2, "sessions") == 15
    finally:
        s2.stop(flush=True)


def test_sessions_rollups_only_touch_written_rows(store):
    store.ingest_sessions_batch([_sess(i) for i in range(5)])
    before = store._conn.execute(
        "SELECT day, runtime, sessions FROM rollup_runtime_daily ORDER BY day, runtime"
    ).fetchall()
    store.ingest_sessions_batch([_sess(i) for i in range(5)])  # skipped
    after = store._conn.execute(
        "SELECT day, runtime, sessions FROM rollup_runtime_daily ORDER BY day, runtime"
    ).fetchall()
    assert before == after


# ── forward progress window + cache (#5497) ───────────────────────────────

def _event(sid: str, ts: datetime, i: int, tokens: int = 50):
    return {
        "id": f"{sid}-ev-{i}",
        "agent_type": "openclaw",
        "node_id": "n1",
        "agent_id": "main",
        "session_id": sid,
        "event_type": "assistant",
        "ts": ts.strftime("%Y-%m-%dT%H:%M:%S.000000+00:00"),
        "data": {"role": "assistant", "content": "ok", "usage": {"input_tokens": tokens, "output_tokens": 0}},
        "cost_usd": 0.001,
        "token_count": tokens,
        "model": "m",
    }


def test_forward_progress_defaults_to_a_day_and_caches(store, ls_mod):
    now = datetime.now(timezone.utc)
    store.ingest_many([
        _event("old-sess", now - timedelta(days=3), 1),
        _event("old-sess", now - timedelta(days=3), 2),
        _event("new-sess", now - timedelta(hours=1), 1),
        _event("new-sess", now - timedelta(hours=1), 2),
    ])
    store._flush_now()
    ls_mod._READ_CACHE.clear()
    hits_before = ls_mod._READ_CACHE_HITS["hit"]
    rows = store.query_forward_progress()
    assert [r["session_id"] for r in rows] == ["new-sess"]
    assert store.query_forward_progress() is rows          # served from the cache
    assert ls_mod._READ_CACHE_HITS["hit"] == hits_before + 1
    wide = (now - timedelta(days=5)).strftime("%Y-%m-%dT%H:%M:%SZ")
    assert {r["session_id"] for r in store.query_forward_progress(since=wide)} == {"old-sess", "new-sess"}
    # An explicit session_id is never windowed away.
    assert [r["session_id"] for r in store.query_forward_progress(session_id="old-sess")] == ["old-sess"]
