"""Accuracy gates for the materialized rollup tables (issue #2988,
Query Spine P2).

Three gates, all on a varied fixture corpus (multiple models, runtimes,
days, cache-token splits, derived-cost events, duplicate event ids):

1. PARITY — rollup totals exactly equal an independent full-scan
   aggregate over the events table (stored cost_usd / token_count /
   model columns + splits re-read from the data payloads), and
   rollup_session rows match query_sessions_table for the shared fields.
2. INCREMENTAL == BATCH — ingesting the corpus in several flushed
   batches produces byte-identical rollups to a single-batch ingest.
3. BACKFILL == INCREMENTAL — wiping the rollups and running the chunked
   backfill reproduces the incrementally-built tables exactly.

Plus regression guards: duplicate-id re-ingest must not double-count
(INSERT OR IGNORE drops the row, so the rollup must too), and the
startup backfill must be a no-op when the rollups already hold rows
(no full-table recompute on the steady-state hot path).
"""

from __future__ import annotations

import importlib

import pytest

# Costs are stored per-event rounded to 8 decimals; sums are compared at
# the same precision so float association order (batching) cannot flake
# the exact-equality gates.
_R = 8


@pytest.fixture
def fresh_store(tmp_path, monkeypatch):
    """Isolated LocalStore factory on a tmp DuckDB path."""
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_SECS", "3600")  # manual flush only
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_BATCH", "100000")

    made = []

    def _make(name: str):
        monkeypatch.setenv(
            "CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / f"{name}.duckdb")
        )
        import clawmetry.local_store as ls
        ls = importlib.reload(ls)
        store = ls.LocalStore()
        made.append(store)
        return ls, store

    yield _make
    for s in made:
        try:
            s.stop(flush=False)
        except Exception:
            pass


def _corpus() -> tuple[list[dict], list[dict]]:
    """(events, sessions): multiple models / runtimes / days, cache splits,
    a derived-cost event, a no-model event, and a duplicate event id."""
    events = [
        # day 1, openclaw, explicit cost + lumped tokens (no split)
        {"id": "ev-001", "node_id": "n1", "agent_type": "openclaw",
         "session_id": "s-oc-1", "event_type": "message",
         "ts": "2026-01-01T08:00:00Z", "model": "claude-opus-4-7",
         "cost_usd": 0.012, "token_count": 1200,
         "data": {"text": "hello"}},
        # day 1, openclaw, second model
        {"id": "ev-002", "node_id": "n1", "agent_type": "openclaw",
         "session_id": "s-oc-1", "event_type": "message",
         "ts": "2026-01-01T09:00:00Z", "model": "gpt-4o",
         "cost_usd": 0.005, "token_count": 800, "data": {"text": "hi"}},
        # day 1, claude_code adapter shape: lumped token_count preset,
        # in/out/cache splits stashed under data.extra, cost derived once
        # at ingest via providers_pricing (longest-prefix rates).
        {"id": "ev-003", "node_id": "n1", "agent_type": "claude_code",
         "session_id": "s-cc-1", "event_type": "assistant",
         "ts": "2026-01-01T10:00:00Z", "model": "claude-opus-4-7",
         "token_count": 5000,
         "data": {"extra": {"inputTokens": 1000, "outputTokens": 500,
                            "cacheReadInputTokens": 3000,
                            "cacheCreationInputTokens": 500}}},
        # day 2, claude_code, same model (rolls into a new day row)
        {"id": "ev-004", "node_id": "n1", "agent_type": "claude_code",
         "session_id": "s-cc-1", "event_type": "assistant",
         "ts": "2026-01-02T11:00:00Z", "model": "claude-opus-4-7",
         "token_count": 2000,
         "data": {"extra": {"inputTokens": 700, "outputTokens": 300,
                            "cacheReadInputTokens": 1000}}},
        # day 2, openclaw, usage-dict shape (data.usage splits)
        {"id": "ev-005", "node_id": "n1", "agent_type": "openclaw",
         "session_id": "s-oc-2", "event_type": "model.completed",
         "ts": "2026-01-02T12:00:00Z",
         "data": {"modelId": "claude-haiku-4-5",
                  "usage": {"input_tokens": 400, "output_tokens": 100}}},
        # day 2, no model / no tokens: counts toward runtime activity only
        {"id": "ev-006", "node_id": "n1", "agent_type": "openclaw",
         "session_id": "s-oc-2", "event_type": "tool_call",
         "ts": "2026-01-02T12:01:00Z", "data": {"tool": "Bash"}},
        # DUPLICATE id of ev-001 (different payload): INSERT OR IGNORE
        # drops it from the events table, so the rollup must drop it too.
        {"id": "ev-001", "node_id": "n1", "agent_type": "openclaw",
         "session_id": "s-oc-1", "event_type": "message",
         "ts": "2026-01-01T08:00:00Z", "model": "claude-opus-4-7",
         "cost_usd": 99.0, "token_count": 999999, "data": {"text": "dupe"}},
    ]
    sessions = [
        {"session_id": "s-oc-1", "agent_type": "openclaw", "node_id": "n1",
         "title": "alpha", "started_at": "2026-01-01T08:00:00Z",
         "last_active_at": "2026-01-01T09:30:00Z", "status": "ended",
         "total_tokens": 2000, "cost_usd": 0.017, "message_count": 2},
        {"session_id": "s-cc-1", "agent_type": "claude_code", "node_id": "n1",
         "title": "code session", "started_at": "2026-01-01T10:00:00Z",
         "last_active_at": "2026-01-02T11:00:00Z", "status": "active",
         "total_tokens": 7000, "cost_usd": 0.04, "message_count": 2},
        {"session_id": "s-oc-2", "agent_type": "openclaw", "node_id": "n1",
         "title": "beta", "started_at": "2026-01-02T12:00:00Z",
         "last_active_at": "2026-01-02T12:01:00Z", "status": "active",
         "total_tokens": 500, "cost_usd": 0.001, "message_count": 1},
    ]
    return events, sessions


def _seed(store, events, sessions, *, batches: int = 1):
    n = max(1, len(events) // batches)
    for off in range(0, len(events), n):
        for e in events[off:off + n]:
            store.ingest(dict(e))
        assert store.flush() >= 0
    for s in sessions:
        store.ingest_session(dict(s))
    store.flush()


def _model_rollup_map(store):
    return {
        (r["day"], r["model"], r["runtime"]): (
            r["tokens_in"], r["tokens_out"], r["cache_read"],
            r["cache_write"], round(float(r["cost_usd"]), _R), r["calls"],
        )
        for r in store.query_rollup_model_daily(limit=10000)
    }


def _runtime_rollup_map(store):
    return {
        (r["day"], r["runtime"]): (
            r["tokens"], round(float(r["cost_usd"]), _R),
            r["sessions"], r["active_sessions"],
        )
        for r in store.query_rollup_runtime_daily(limit=10000)
    }


def _split_from_payload(data) -> tuple[int, int, int, int]:
    """Independent (test-local) split reader: in/out/cache tokens from the
    adapter/data payload shapes the corpus uses."""
    ti = to = cr = cw = 0
    if isinstance(data, dict):
        for src in (data.get("extra"), data.get("usage")):
            if not isinstance(src, dict):
                continue
            ti = ti or int(src.get("inputTokens") or src.get("input_tokens") or 0)
            to = to or int(src.get("outputTokens") or src.get("output_tokens") or 0)
            cr = cr or int(src.get("cacheReadInputTokens")
                           or src.get("cache_read_input_tokens") or 0)
            cw = cw or int(src.get("cacheCreationInputTokens")
                           or src.get("cache_creation_input_tokens") or 0)
    return ti, to, cr, cw


def test_rollups_match_full_scan_aggregate(fresh_store):
    """Gate 1 (parity): rollup totals == independent full-scan aggregate of
    the events table; rollup_session == query_sessions_table shared fields."""
    _, store = fresh_store("parity")
    events, sessions = _corpus()
    _seed(store, events, sessions)

    rows = store.query_events(limit=10000)
    assert len(rows) == 6, "duplicate id must be deduped in the events table"

    # Full-scan aggregates (independent reimplementation).
    want_model: dict = {}
    want_runtime: dict = {}
    for r in rows:
        day = str(r["ts"])[:10]
        runtime = r["agent_type"]
        tokens = int(r["token_count"] or 0)
        cost = float(r["cost_usd"] or 0.0)
        wr = want_runtime.setdefault((day, runtime), [0, 0.0, None, None])
        wr[0] += tokens
        wr[1] += cost
        if r["model"]:
            ti, to, cr, cw = _split_from_payload(r.get("data"))
            wm = want_model.setdefault((day, r["model"], runtime),
                                       [0, 0, 0, 0, 0.0, 0])
            wm[0] += ti
            wm[1] += to
            wm[2] += cr
            wm[3] += cw
            wm[4] += cost
            wm[5] += 1

    got_model = _model_rollup_map(store)
    assert set(got_model) == set(want_model)
    for k, w in want_model.items():
        assert got_model[k] == (w[0], w[1], w[2], w[3], round(w[4], _R), w[5]), k

    # Derived pricing sanity: the adapter-shape event (ev-003) has no
    # explicit cost; the rollup cost must equal the events-table stored
    # cost (priced once, longest-prefix rates), and be non-zero.
    cc_key = ("2026-01-01", "claude-opus-4-7", "claude_code")
    assert got_model[cc_key][4] > 0

    # Session-count refreshes may create day/runtime cells with zero event
    # tokens; the corpus aligns sessions with event days, so the key sets
    # match exactly here.
    got_runtime = _runtime_rollup_map(store)
    assert set(got_runtime) == set(want_runtime)
    for k, w in want_runtime.items():
        assert got_runtime[k][0] == w[0], k
        assert got_runtime[k][1] == round(w[1], _R), k

    # Session counts vs a sessions-table scan.
    sess_rows = store.query_sessions_table(limit=1000)
    for (day, runtime), got in got_runtime.items():
        started = sum(
            1 for s in sess_rows
            if s["agent_type"] == runtime
            and str(s["started_at"] or s["last_active_at"])[:10] == day
        )
        active = sum(
            1 for s in sess_rows
            if s["agent_type"] == runtime
            and str(s["last_active_at"] or "")[:10] == day
        )
        assert got[2] == started, (day, runtime)
        assert got[3] == active, (day, runtime)

    # rollup_session vs query_sessions_table shared fields. ``turns`` is
    # compared against the seeded typed-session row: query_sessions_table
    # GREATEST-bridges message_count with a renderable-events count, while
    # rollup_session mirrors the typed sessions row (the ingest contract).
    seeded = {s["session_id"]: s for s in sessions}
    got_sessions = {r["session_id"]: r for r in store.query_rollup_sessions(limit=1000)}
    assert set(got_sessions) == set(seeded)
    for s in sess_rows:
        g = got_sessions[s["session_id"]]
        assert g["runtime"] == s["agent_type"]
        assert g["title"] == s["title"]
        assert g["status"] == s["status"]
        assert g["started_at"] == s["started_at"]
        assert g["last_activity"] == s["last_active_at"]
        assert g["tokens"] == s["total_tokens"]
        assert round(float(g["cost_usd"]), _R) == round(float(s["cost_usd"]), _R)
        assert g["turns"] == seeded[s["session_id"]]["message_count"]
        assert g["stuck_flag"] is False


def test_duplicate_id_reingest_does_not_double_count(fresh_store):
    """Re-flushing an already-stored id is a rollup no-op (mirrors the
    events table's INSERT OR IGNORE)."""
    _, store = fresh_store("dedup")
    events, sessions = _corpus()
    _seed(store, events, sessions)
    before_m = _model_rollup_map(store)
    before_r = _runtime_rollup_map(store)
    for e in events:
        store.ingest(dict(e))
    store.flush()
    assert _model_rollup_map(store) == before_m
    assert _runtime_rollup_map(store) == before_r


def test_incremental_equals_single_batch(fresh_store):
    """Gate 2: N flushed batches == one batch, byte-identical rollups."""
    events, sessions = _corpus()
    _, inc = fresh_store("incremental")
    _seed(inc, events, sessions, batches=3)
    _, one = fresh_store("singlebatch")
    _seed(one, events, sessions, batches=1)
    assert _model_rollup_map(inc) == _model_rollup_map(one)
    assert _runtime_rollup_map(inc) == _runtime_rollup_map(one)
    assert inc.query_rollup_sessions(limit=100) == one.query_rollup_sessions(limit=100)


def test_backfill_equals_incremental(fresh_store):
    """Gate 3: wipe the rollups, run the chunked backfill, get identical
    tables back."""
    _, store = fresh_store("backfill")
    events, sessions = _corpus()
    _seed(store, events, sessions)
    want_m = _model_rollup_map(store)
    want_r = _runtime_rollup_map(store)
    want_s = store.query_rollup_sessions(limit=1000)
    res = store.backfill_rollups(force=True)
    assert res["skipped"] is False
    assert _model_rollup_map(store) == want_m
    assert _runtime_rollup_map(store) == want_r
    assert store.query_rollup_sessions(limit=1000) == want_s


def test_backfill_is_chunked(fresh_store, monkeypatch):
    """The backfill paginates by rowid: with a chunk smaller than the corpus
    it still reproduces the exact totals (no chunk-boundary drift)."""
    ls, store = fresh_store("chunked")
    events, sessions = _corpus()
    _seed(store, events, sessions)
    want_m = _model_rollup_map(store)
    monkeypatch.setattr(ls, "ROLLUP_BACKFILL_CHUNK", 2)
    res = store.backfill_rollups(force=True)
    assert res["skipped"] is False
    assert _model_rollup_map(store) == want_m


def test_backfill_skips_when_populated(fresh_store):
    """Steady-state guard: a writer (re)open never re-runs the backfill once
    the rollups hold rows — no full-table recompute on the hot path."""
    _, store = fresh_store("skipguard")
    events, sessions = _corpus()
    _seed(store, events, sessions)
    res = store.backfill_rollups()
    assert res == {"skipped": True, "reason": "rollups_populated"}


def test_backfill_runs_on_upgrade_open(fresh_store, tmp_path, monkeypatch):
    """Upgrade path: a store whose events exist but whose rollups are empty
    (simulating a pre-rollup wheel) backfills once at writer open."""
    ls, store = fresh_store("upgrade")
    events, sessions = _corpus()
    _seed(store, events, sessions)
    want_m = _model_rollup_map(store)
    want_r = _runtime_rollup_map(store)
    # Simulate the pre-upgrade store: drop the rollup contents, close.
    with store._write_lock:
        store._conn.execute("DELETE FROM rollup_model_daily")
        store._conn.execute("DELETE FROM rollup_runtime_daily")
        store._conn.execute("DELETE FROM rollup_session")
    store.stop(flush=False)
    # Re-open the SAME db path: __init__ must detect empty-rollups +
    # populated events and rebuild.
    reopened = ls.LocalStore()
    try:
        assert _model_rollup_map(reopened) == want_m
        assert _runtime_rollup_map(reopened) == want_r
        assert len(reopened.query_rollup_sessions(limit=100)) == len(sessions)
    finally:
        reopened.stop(flush=False)
