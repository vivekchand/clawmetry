"""#5500 — the range indexes on events and spans are gone, and a store that
still carries them sheds them at the next boot.

DuckDB's guidance is to index only for point lookups returning under 0.1%
of rows; zone maps already prune range scans on time columns because rows
arrive in time order. The nine range indexes never appeared in a profiled
plan for the dashboard's hottest queries, cost about 115 MB on a real
store, and made every UPDATE on the table a DELETE plus INSERT.
"""
from __future__ import annotations

import importlib

import duckdb

DROPPED = {
    "events": {"idx_events_ts", "idx_events_agent_ts", "idx_events_type_ts",
               "idx_events_atype_ts", "idx_events_session_ts_type",
               "idx_events_created_at"},
    "spans": {"idx_spans_ts", "idx_spans_agent_ts", "idx_spans_trace_start"},
}
KEPT = {
    "events": {"idx_events_session"},
    "spans": {"idx_spans_trace_id", "idx_spans_parent", "idx_spans_session"},
}


def _names(conn, table):
    return {r[0] for r in conn.execute(
        "SELECT index_name FROM duckdb_indexes() WHERE table_name = ?", [table]
    ).fetchall()}


def _fresh(tmp_path, monkeypatch, name="idx.duckdb"):
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / name))
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_SECS", "999")
    import clawmetry.local_store as ls
    importlib.reload(ls)
    return ls


def test_fresh_store_has_only_point_lookup_indexes(tmp_path, monkeypatch):
    ls = _fresh(tmp_path, monkeypatch)
    s = ls.LocalStore()
    try:
        for table in ("events", "spans"):
            names = _names(s._conn, table)
            assert KEPT[table] <= names, (table, names)
            assert not (DROPPED[table] & names), (table, DROPPED[table] & names)
    finally:
        s.stop(flush=True)


def test_existing_store_sheds_the_range_indexes_on_boot(tmp_path, monkeypatch):
    ls = _fresh(tmp_path, monkeypatch, name="old.duckdb")
    s = ls.LocalStore()
    try:
        s.ingest_spans_batch([{"span_id": f"s{i}", "trace_id": "t", "name": "n",
                               "start_ts": 1.0 + i} for i in range(20)])
    finally:
        s.stop(flush=True)
    # Recreate the pre-#5500 indexes the way an older wheel left them.
    conn = duckdb.connect(str(tmp_path / "old.duckdb"))
    conn.execute("CREATE INDEX IF NOT EXISTS idx_events_ts ON events(ts)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_events_type_ts ON events(event_type, ts)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_events_session_ts_type ON events(session_id, ts, event_type)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_spans_ts ON spans(ts)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_spans_agent_ts ON spans(agent_type, start_ts)")
    conn.execute("CHECKPOINT")
    assert "idx_spans_ts" in _names(conn, "spans")
    conn.close()
    ls2 = _fresh(tmp_path, monkeypatch, name="old.duckdb")
    s = ls2.LocalStore()
    try:
        for table in ("events", "spans"):
            names = _names(s._conn, table)
            assert not (DROPPED[table] & names), (table, DROPPED[table] & names)
            assert KEPT[table] <= names
        assert s._conn.execute("SELECT COUNT(*) FROM spans").fetchone()[0] == 20
        # Point lookups still work and writes still land.
        assert len(s.query_spans(trace_id="t", limit=100)) == 20
        assert s.ingest_spans_batch([{"span_id": "s99", "trace_id": "t", "name": "n", "start_ts": 99.0}]) == 1
    finally:
        s.stop(flush=True)
