"""Regression guards for the fast fresh-install ingest path (Stage 1).

Background: the original flush path wrote ~19 events/s end-to-end — a
1000-event flush took ~53s — because (a) DuckDB's Python binding retries a
FAILED ``import pandas`` for nearly every bound parameter (CPython does not
negative-cache failed imports, so each attempt re-scans sys.path), (b) the
integrity stamper re-UPDATEd every inserted row post-insert (delete+reinsert
against six secondary indexes), and (c) the disabled SIEM/OTLP hooks paid a
failed ``clawmetry_pro`` import per event. The fix: negative-cache the pandas
miss, compute the #2200 hash chain in Python BEFORE insert and fold it into
one chunked multi-row VALUES INSERT, and hoist hook enablement to once per
batch.

These tests are the ruthless-verify guard: the perf test FAILS on the
un-fixed code (measured >240s for the 5000-event batch pre-fix, <5s post-fix)
and the parity tests pin the integrity chain byte-for-byte to the legacy
stamping scheme so replay/verification sees identical hashes.
"""

from __future__ import annotations

import importlib
import time

import pytest


# ── fixtures ──────────────────────────────────────────────────────────────


def _fresh_store_module(tmp_path, monkeypatch, name="events.duckdb"):
    """Reload clawmetry.local_store against an isolated scratch DuckDB."""
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / name))
    # Background flusher effectively off — tests flush explicitly.
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_SECS", "999")
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_BATCH", "1000")
    monkeypatch.setenv("CLAWMETRY_INTEGRITY", "1")
    import clawmetry.local_store as ls
    importlib.reload(ls)
    return ls


@pytest.fixture
def ls_mod(tmp_path, monkeypatch):
    return _fresh_store_module(tmp_path, monkeypatch)


@pytest.fixture
def store(ls_mod):
    s = ls_mod.LocalStore()
    yield s
    s.stop(flush=True)


def _ev(i: int, node: str = "node-a", **overrides):
    base = {
        "id": f"ev-{i:06d}",
        "node_id": node,
        "agent_id": "main",
        "session_id": f"sess-{i % 20}",
        "event_type": "message",
        "ts": f"2026-08-0{1 + i % 8}T12:00:{i % 60:02d}Z",
        "data": {
            "role": "assistant",
            "content": "hello world " * 10,
            "extra": {"inputTokens": 10, "outputTokens": 5},
        },
        "token_count": 15,
        "model": "claude-opus-4-8",
    }
    base.update(overrides)
    return base


# ── perf regression guard ─────────────────────────────────────────────────


def test_bulk_ingest_flush_5000_events_under_10s(store):
    """The 100x guard. Pre-fix this batch took >240s (per-parameter failed
    pandas imports + the post-insert integrity UPDATE pass); post-fix it
    runs in a few seconds. 10s leaves generous margin for slow CI runners
    while still failing the un-fixed code by a factor of ~25."""
    events = [_ev(i, node="node-a" if i % 3 else "node-b") for i in range(5000)]
    t0 = time.monotonic()
    store.ingest_many(events)
    store.flush()
    elapsed = time.monotonic() - t0
    n, stamped = store._conn.execute(
        "SELECT COUNT(*), COUNT(chain_hash) FROM events"
    ).fetchone()
    assert n == 5000, f"expected 5000 rows, got {n}"
    assert stamped == 5000, "integrity chain must stamp every fresh row"
    assert elapsed < 10.0, (
        f"5000-event ingest+flush took {elapsed:.1f}s — the bulk-insert "
        "fast path has regressed (budget 10s; pre-fix code took >240s)"
    )


# ── integrity-chain parity with the legacy stamping scheme ────────────────


def _legacy_chain(events):
    """Replicate the retired ``_stamp_integrity`` algorithm exactly: group
    events by node_id (batch order), sort by id within the node, chain
    SHA-256 hashes from the 64-zero genesis via ``_integrity_hash``.
    Returns (per-id (prev, hash) map, per-node final head)."""
    import clawmetry.local_store as ls
    by_node: dict[str, list[dict]] = {}
    for e in events:
        by_node.setdefault(str(e.get("node_id") or "unknown"), []).append(e)
    expected: dict[str, tuple[str, str]] = {}
    heads: dict[str, str] = {}
    for node, evs in by_node.items():
        head = "0" * 64
        for e in sorted(evs, key=lambda e: str(e["id"])):
            h = ls._integrity_hash(head, e)
            expected[str(e["id"])] = (head, h)
            head = h
        heads[node] = head
    return expected, heads


def test_integrity_chain_matches_legacy_stamping_byte_for_byte(store):
    """The bulk path computes chain hashes in Python pre-insert; they must
    be IDENTICAL to what the old post-insert UPDATE pass produced, or every
    existing store's replay/verification breaks on upgrade."""
    events = [_ev(i, node="node-a" if i % 2 else "node-b") for i in range(50)]
    store.ingest_many(events)
    store.flush()
    expected, heads = _legacy_chain(events)
    rows = store._conn.execute(
        "SELECT id, chain_prev_hash, chain_hash FROM events"
    ).fetchall()
    assert len(rows) == 50
    for rid, prev_h, h in rows:
        exp_prev, exp_h = expected[str(rid)]
        assert prev_h == exp_prev, f"chain_prev_hash mismatch at {rid}"
        assert h == exp_h, f"chain_hash mismatch at {rid}"
    for node, exp_head in heads.items():
        got = store._conn.execute(
            "SELECT chain_hash FROM chain_heads WHERE node_id = ?", [node]
        ).fetchone()
        assert got and got[0] == exp_head, f"chain head mismatch for {node}"
    # And the replay/verification code agrees end-to-end.
    assert store.verify_integrity()["status"] == "valid"


def test_redelivered_events_do_not_restamp_or_fork_the_chain(store):
    events = [_ev(i) for i in range(20)]
    store.ingest_many(events)
    store.flush()
    before = dict(store._conn.execute(
        "SELECT id, chain_hash FROM events"
    ).fetchall())
    head_before = store._conn.execute(
        "SELECT chain_hash FROM chain_heads WHERE node_id = 'node-a'"
    ).fetchone()[0]
    # Re-deliver the same batch (idempotent replay after a crash).
    store.ingest_many(events)
    store.flush()
    after = dict(store._conn.execute(
        "SELECT id, chain_hash FROM events"
    ).fetchall())
    assert after == before, "re-delivery must not rewrite chain hashes"
    head_after = store._conn.execute(
        "SELECT chain_hash FROM chain_heads WHERE node_id = 'node-a'"
    ).fetchone()[0]
    assert head_after == head_before
    assert store.verify_integrity()["status"] == "valid"


def test_chain_continues_across_flushes_and_restarts(ls_mod):
    s = ls_mod.LocalStore()
    try:
        s.ingest_many([_ev(i) for i in range(10)])
        s.flush()
        s.ingest_many([_ev(i) for i in range(10, 20)])
        s.flush()
    finally:
        s.stop(flush=True)
    # New process (fresh LocalStore) resumes the chain from chain_heads.
    s2 = ls_mod.LocalStore()
    try:
        s2.ingest_many([_ev(i) for i in range(20, 30)])
        s2.flush()
        result = s2.verify_integrity()
        assert result["status"] == "valid"
        assert result["checked"] == 30
    finally:
        s2.stop(flush=True)


def test_pre_chain_redelivery_gets_stamped_in_place(store):
    """A row inserted before integrity was enabled (chain_hash NULL) that is
    re-delivered gets stamped via the UPDATE side-path, matching the legacy
    behavior."""
    e = _ev(0)
    import clawmetry.local_store as ls
    row = ls._event_to_row(e)
    with store._write_lock:
        store._conn.execute(
            f"INSERT INTO events ({store._EVENT_INSERT_COLS}) VALUES "
            "(" + ",".join("?" * 16) + ")",
            list(row) + [None, None],
        )
    store.ingest(e)
    store.flush()
    prev_h, h = store._conn.execute(
        "SELECT chain_prev_hash, chain_hash FROM events WHERE id = ?",
        [e["id"]],
    ).fetchone()
    assert prev_h == "0" * 64
    assert h == ls._integrity_hash("0" * 64, e)
    assert store.verify_integrity()["status"] == "valid"


def test_in_batch_duplicate_ids_insert_once_and_verify(store):
    e = _ev(0)
    store.ingest_many([e, dict(e), dict(e)])
    store.flush()
    n = store._conn.execute("SELECT COUNT(*) FROM events").fetchone()[0]
    assert n == 1
    assert store.verify_integrity()["status"] == "valid"


# ── rollups keep counting each event exactly once ─────────────────────────


def test_rollups_match_full_scan_after_bulk_flush(store):
    events = [_ev(i) for i in range(100)]
    store.ingest_many(events)
    store.flush()
    # Re-deliver half — must not double-count.
    store.ingest_many(events[:50])
    store.flush()
    rollup = store._conn.execute(
        "SELECT SUM(tokens) FROM rollup_runtime_daily"
    ).fetchone()[0]
    scan = store._conn.execute(
        "SELECT SUM(token_count) FROM events"
    ).fetchone()[0]
    assert rollup == scan == 1500  # 100 events x 15 tokens


# ── batch session / span APIs ─────────────────────────────────────────────


def _sess(i: int, **overrides):
    base = {
        "session_id": f"sess-{i:04d}",
        "agent_type": "openclaw",
        "node_id": "node-a",
        "title": f"session {i}",
        "started_at": "2026-08-01T10:00:00Z",
        "last_active_at": "2026-08-01T11:00:00Z",
        "status": "ended",
        "total_tokens": 100 + i,
        "cost_usd": 0.01 * i,
        "message_count": i,
        "metadata": {"runtime": "claude_code"},
    }
    base.update(overrides)
    return base


def test_sessions_batch_matches_sequential_ingest(tmp_path, monkeypatch):
    rows = [_sess(i) for i in range(40)]

    def _dump(s):
        sessions = s._conn.execute(
            "SELECT agent_type, session_id, node_id, title, started_at, "
            "last_active_at, status, total_tokens, cost_usd, message_count "
            "FROM sessions ORDER BY session_id"
        ).fetchall()
        rollup = s._conn.execute(
            "SELECT session_id, runtime, tokens, cost_usd, turns "
            "FROM rollup_session ORDER BY session_id"
        ).fetchall()
        days = s._conn.execute(
            "SELECT day, runtime, sessions, active_sessions "
            "FROM rollup_runtime_daily ORDER BY day, runtime"
        ).fetchall()
        return sessions, rollup, days

    ls1 = _fresh_store_module(tmp_path, monkeypatch, name="seq.duckdb")
    s1 = ls1.LocalStore()
    try:
        for r in rows:
            s1.ingest_session(dict(r))
        seq = _dump(s1)
    finally:
        s1.stop(flush=True)

    ls2 = _fresh_store_module(tmp_path, monkeypatch, name="batch.duckdb")
    s2 = ls2.LocalStore()
    try:
        assert s2.ingest_sessions_batch([dict(r) for r in rows]) == 40
        batch = _dump(s2)
    finally:
        s2.stop(flush=True)

    assert batch == seq


def test_sessions_batch_upsert_keeps_earliest_started_at(store):
    store.ingest_sessions_batch([_sess(1, started_at="2026-08-01T09:00:00Z")])
    store.ingest_sessions_batch([
        _sess(1, started_at="2026-08-02T09:00:00Z", title=None,
              last_active_at="2026-08-02T10:00:00Z"),
    ])
    started, title = store._conn.execute(
        "SELECT started_at, title FROM sessions WHERE session_id = ?",
        ["sess-0001"],
    ).fetchone()
    assert started == "2026-08-01T09:00:00Z"  # COALESCE keeps first
    assert title == "session 1"               # COALESCE keeps non-NULL title


def test_sessions_batch_requires_session_id(store):
    with pytest.raises(ValueError):
        store.ingest_sessions_batch([{"agent_type": "openclaw"}])


def _span(i: int, **overrides):
    base = {
        "span_id": f"sp-{i:04d}",
        "trace_id": "trace-1",
        "name": "tool.call",
        "start_ts": 1000.0 + i,
        "end_ts": 1001.0 + i,
        "agent_type": "openclaw",
        "session_id": "sess-1",
    }
    base.update(overrides)
    return base


def test_spans_batch_inserts_and_replaces(store):
    assert store.ingest_spans_batch([_span(i) for i in range(30)]) == 30
    assert store._conn.execute(
        "SELECT COUNT(*) FROM spans"
    ).fetchone()[0] == 30
    # Re-delivery with a late-arriving end_ts overwrites (REPLACE semantics).
    store.ingest_spans_batch([_span(0, end_ts=1500.0, name="tool.retry")])
    name, end_ts = store._conn.execute(
        "SELECT name, end_ts FROM spans WHERE span_id = 'sp-0000'"
    ).fetchone()
    assert (name, end_ts) == ("tool.retry", 1500.0)
    assert store._conn.execute(
        "SELECT COUNT(*) FROM spans"
    ).fetchone()[0] == 30


def test_spans_batch_in_batch_duplicate_last_wins(store):
    store.ingest_spans_batch([
        _span(7, name="first"),
        _span(7, name="second"),
    ])
    rows = store._conn.execute(
        "SELECT name FROM spans WHERE span_id = 'sp-0007'"
    ).fetchall()
    assert rows == [("second",)]


def test_spans_batch_validates_required_fields(store):
    with pytest.raises(ValueError):
        store.ingest_spans_batch([{"span_id": "x", "trace_id": "t"}])


# ── hook hoisting: disabled hooks cost zero per-event calls ───────────────


def test_disabled_hooks_are_not_called_per_event(store, monkeypatch):
    calls = {"siem": 0, "otel": 0}
    from clawmetry import siem, otel_push
    monkeypatch.setattr(siem, "enabled", lambda: False)
    monkeypatch.setattr(otel_push, "enabled", lambda: False)
    monkeypatch.setattr(
        siem, "forward_event",
        lambda e: calls.__setitem__("siem", calls["siem"] + 1),
    )
    monkeypatch.setattr(
        otel_push, "forward_event",
        lambda e: calls.__setitem__("otel", calls["otel"] + 1),
    )
    store.ingest_many([_ev(i) for i in range(10)])
    assert calls == {"siem": 0, "otel": 0}


def test_enabled_hooks_still_fire_per_event(store, monkeypatch):
    calls = {"siem": 0, "otel": 0}
    from clawmetry import siem, otel_push
    monkeypatch.setattr(siem, "enabled", lambda: True)
    monkeypatch.setattr(otel_push, "enabled", lambda: True)
    monkeypatch.setattr(
        siem, "forward_event",
        lambda e: calls.__setitem__("siem", calls["siem"] + 1),
    )
    monkeypatch.setattr(
        otel_push, "forward_event",
        lambda e: calls.__setitem__("otel", calls["otel"] + 1),
    )
    store.ingest_many([_ev(i) for i in range(10)])
    assert calls == {"siem": 10, "otel": 10}


def test_redaction_still_applies_on_the_batch_path(store):
    store.ingest_many([_ev(
        0,
        data={"content": "my key is sk-ant-abcdefghijklmnop1234"},
    )])
    store.flush()
    evs = store.query_events(limit=10)
    blob = str(evs[0].get("data"))
    assert "sk-ant-abcdefghijklmnop1234" not in blob
    assert "REDACTED" in blob


# ── the pandas negative-cache (the per-parameter import stampede) ─────────


def test_pandas_miss_is_negative_cached_when_absent(ls_mod):
    import sys
    try:
        import importlib.util as ilu
        pandas_missing = sys.modules.get("pandas", "sentinel") is None or (
            "pandas" not in sys.modules and ilu.find_spec("pandas") is None
        )
    except ValueError:
        pandas_missing = True  # find_spec on a None entry — cache is active
    if not pandas_missing:
        pytest.skip("pandas installed in this environment — nothing to cache")
    assert sys.modules.get("pandas", "sentinel") is None, (
        "local_store import must negative-cache the pandas miss so duckdb's "
        "per-parameter probe stays O(1)"
    )
