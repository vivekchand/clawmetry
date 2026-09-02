"""Heartbeat rows are liveness pings, not transport envelopes.

On 2026-09-02 a 4.2 GB store turned out to hold 97 MB of events and 2 GB of
heartbeats: the daemon's heartbeat POST carries ``cache_pushes`` (encrypted
cache blobs for the hosted dashboard, ~8.7 MB each) and the whole payload was
stored in ``heartbeats.data``. DuckDB reads the entire column vector for any
statement that names it, so the dashboard's heartbeat poll (500 rows) needed
more than 2 GB of buffer pool: that is the query that ran the store out of
memory and invalidated it, and after a restart it held the store lock for tens
of seconds per poll while every other request timed out.

Three guards: the writer never stores the envelope, the reader never touches
the column unless asked, and the v14 migration empties the column on existing
stores without reading it.
"""
from __future__ import annotations

import json

import pytest

duckdb = pytest.importorskip("duckdb")


@pytest.fixture
def store(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("CLAWMETRY_HOME", str(tmp_path / ".clawmetry"))
    import importlib

    import clawmetry.local_store as ls

    importlib.reload(ls)
    ls.DB_PATH = tmp_path / "test.duckdb"
    ls._oom_bumps = 0
    st = ls.LocalStore(read_only=False)
    yield ls, st
    try:
        st.stop(flush=False)
    except Exception:
        pass


def _hb(ts="2026-09-02T09:00:00+00:00", **extra):
    base = {"node_id": "n1", "ts": ts, "version": "0.12.798", "e2e": True,
            "platform": "Darwin", "billing": {"plan": "trial"}}
    base.update(extra)
    return base


# ── the writer ──────────────────────────────────────────────────────────────


def test_cache_pushes_are_never_stored(store):
    ls, st = store
    push = [{"key": "brain:recent", "ttl_s": 21600, "blob": "x" * 200_000}]
    st.ingest_heartbeat(_hb(cache_pushes=push))
    row = st.query_heartbeats(limit=1, include_data=True)[0]
    assert "cache_pushes" not in row["data"]
    assert row["data"]["platform"] == "Darwin"
    assert row["data"]["billing"] == {"plan": "trial"}
    # The omission is recorded, with the size that was refused.
    assert row["data"]["_dropped"]["cache_pushes"] > 200_000


def test_any_oversized_value_is_dropped_and_recorded(store):
    ls, st = store
    st.ingest_heartbeat(_hb(surprise={"blob": "y" * (ls._HEARTBEAT_DATA_MAX_VALUE_BYTES + 1)}))
    row = st.query_heartbeats(limit=1, include_data=True)[0]
    assert "surprise" not in row["data"]
    assert "surprise" in row["data"]["_dropped"]


def test_a_small_heartbeat_is_stored_whole(store):
    ls, st = store
    st.ingest_heartbeat(_hb())
    row = st.query_heartbeats(limit=1, include_data=True)[0]
    assert "_dropped" not in row["data"]
    assert row["data"]["platform"] == "Darwin"


def test_a_stored_row_stays_small_even_from_a_bloated_payload(store):
    ls, st = store
    st.ingest_heartbeat(_hb(cache_pushes=[{"blob": "z" * 9_000_000}]))
    n = st._conn.execute(
        "SELECT OCTET_LENGTH(data) FROM heartbeats").fetchone()[0]
    assert n < ls._HEARTBEAT_DATA_MAX_VALUE_BYTES


# ── the reader ──────────────────────────────────────────────────────────────


def test_reads_do_not_touch_the_blob_column_by_default(store):
    ls, st = store
    st.ingest_heartbeat(_hb())
    rows = st.query_heartbeats(limit=500)
    assert rows and rows[0]["ts"] == "2026-09-02T09:00:00+00:00"
    assert rows[0]["data"] is None
    assert rows[0]["version"] == "0.12.798"


def test_include_data_returns_the_decoded_payload(store):
    ls, st = store
    st.ingest_heartbeat(_hb())
    rows = st.query_heartbeats(limit=1, include_data=True)
    assert isinstance(rows[0]["data"], dict)


# ── the migration ───────────────────────────────────────────────────────────


def test_v14_empties_stored_payloads_without_reading_them(store):
    """Simulate a v13 store carrying bloated rows, re-run the migration, and
    check the rows survive with their keys, an empty payload, the primary
    key still enforced, and the index back."""
    ls, st = store
    st._conn.execute(
        "INSERT INTO heartbeats (agent_type, node_id, ts, version, e2e, "
        "size_mb, events_total, data) VALUES ('openclaw','n1','2026-09-01T00:00:00+00:00',"
        "'0.12.700', true, 4200.0, 90000, ?)",
        [b"{" + b'"cache_pushes":"' + b"x" * 500_000 + b'"}'],
    )
    st.ingest_heartbeat(_hb())
    st._conn.execute("DELETE FROM schema_version WHERE version >= 14")
    st._migrate()

    rows = st._conn.execute(
        "SELECT ts, version, size_mb, events_total, data FROM heartbeats ORDER BY ts"
    ).fetchall()
    assert [r[0] for r in rows] == ["2026-09-01T00:00:00+00:00",
                                    "2026-09-02T09:00:00+00:00"]
    assert rows[0][1:4] == ("0.12.700", 4200.0, 90000)
    assert all(r[4] is None for r in rows)
    pk = st._conn.execute(
        "SELECT constraint_text FROM duckdb_constraints() "
        "WHERE table_name='heartbeats' AND constraint_type='PRIMARY KEY'"
    ).fetchall()
    assert pk == [("PRIMARY KEY(agent_type, node_id, ts)",)]
    idx = {r[0] for r in st._conn.execute(
        "SELECT index_name FROM duckdb_indexes() WHERE table_name='heartbeats'"
    ).fetchall()}
    assert "idx_heartbeats_node_ts" in idx
    assert st._conn.execute(
        "SELECT MAX(version) FROM schema_version").fetchone()[0] == ls.SCHEMA_VERSION
    # The upsert the daemon runs every minute still works on the swapped table.
    st.ingest_heartbeat(_hb(ts="2026-09-02T09:01:00+00:00"))
    st.ingest_heartbeat(_hb(ts="2026-09-02T09:01:00+00:00"))
    assert st._conn.execute("SELECT COUNT(*) FROM heartbeats").fetchone()[0] == 3


def test_v14_runs_once(store):
    ls, st = store
    st.ingest_heartbeat(_hb())
    before = st._conn.execute("SELECT COUNT(*) FROM schema_version").fetchone()[0]
    st._migrate()
    assert st._conn.execute("SELECT COUNT(*) FROM schema_version").fetchone()[0] == before
    assert st.query_heartbeats(limit=1, include_data=True)[0]["data"]["platform"] == "Darwin"
