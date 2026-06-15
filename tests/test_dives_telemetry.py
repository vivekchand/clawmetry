"""Tests for DIVES-6: ingest_dive_run stores dive_run events in DuckDB (issue #999)."""
import json
import threading
import tempfile
import pathlib
import unittest


def _make_store():
    """Create a minimal in-memory-ish LocalStore with only the events table."""
    from clawmetry.local_store import LocalStore
    import duckdb
    tmp = pathlib.Path(tempfile.mkdtemp()) / "test_dives.duckdb"
    store = LocalStore.__new__(LocalStore)
    store._conn = duckdb.connect(str(tmp))
    store._write_lock = threading.Lock()
    store._path = tmp
    store._conn.execute("""
        CREATE TABLE IF NOT EXISTS events (
            id              VARCHAR PRIMARY KEY,
            agent_type      VARCHAR NOT NULL DEFAULT 'openclaw',
            node_id         VARCHAR NOT NULL,
            agent_id        VARCHAR NOT NULL DEFAULT 'main',
            session_id      VARCHAR,
            workspace_id    VARCHAR,
            event_type      VARCHAR NOT NULL,
            ts              VARCHAR NOT NULL,
            data            BLOB,
            cost_usd        DOUBLE,
            token_count     INTEGER,
            model           VARCHAR,
            created_at      BIGINT NOT NULL,
            chain_prev_hash VARCHAR,
            chain_hash      VARCHAR
        )
    """)
    return store


def _fetch_dive_runs(store):
    rows = store._conn.execute(
        "SELECT event_type, agent_type, node_id, agent_id, data "
        "FROM events WHERE event_type = 'dive_run'"
    ).fetchall()
    return [
        {
            "event_type": r[0],
            "agent_type": r[1],
            "node_id":    r[2],
            "agent_id":   r[3],
            "data":       json.loads(r[4]),
        }
        for r in rows
    ]


class TestIngestDiveRun(unittest.TestCase):
    def test_basic_row_written(self):
        store = _make_store()
        store.ingest_dive_run(
            question="How much did sessions cost today?",
            sql="SELECT SUM(cost_usd) FROM sessions",
            chart_type="bar",
            row_count=3,
            latency_ms=412,
            had_error=False,
        )
        runs = _fetch_dive_runs(store)
        self.assertEqual(len(runs), 1)
        r = runs[0]
        self.assertEqual(r["event_type"], "dive_run")
        self.assertEqual(r["agent_type"], "clawmetry")
        self.assertEqual(r["node_id"], "local")
        self.assertEqual(r["agent_id"], "dives")
        self.assertEqual(r["data"]["question"], "How much did sessions cost today?")
        self.assertEqual(r["data"]["sql"], "SELECT SUM(cost_usd) FROM sessions")
        self.assertEqual(r["data"]["chart_type"], "bar")
        self.assertEqual(r["data"]["row_count"], 3)
        self.assertEqual(r["data"]["latency_ms"], 412)
        self.assertFalse(r["data"]["had_error"])

    def test_error_run_flagged(self):
        store = _make_store()
        store.ingest_dive_run(
            question="oops",
            sql="not valid sql",
            had_error=True,
        )
        runs = _fetch_dive_runs(store)
        self.assertEqual(len(runs), 1)
        self.assertTrue(runs[0]["data"]["had_error"])

    def test_long_inputs_truncated(self):
        store = _make_store()
        store.ingest_dive_run(
            question="q" * 300,
            sql="s" * 600,
        )
        runs = _fetch_dive_runs(store)
        self.assertEqual(len(runs), 1)
        data = runs[0]["data"]
        self.assertLessEqual(len(data["question"]), 200)
        self.assertLessEqual(len(data["sql"]), 500)

    def test_defaults_are_safe(self):
        store = _make_store()
        store.ingest_dive_run()
        runs = _fetch_dive_runs(store)
        self.assertEqual(len(runs), 1)
        data = runs[0]["data"]
        self.assertEqual(data["question"], "")
        self.assertEqual(data["sql"], "")
        self.assertEqual(data["row_count"], 0)
        self.assertFalse(data["had_error"])

    def test_multiple_runs_all_logged(self):
        store = _make_store()
        for i in range(3):
            store.ingest_dive_run(question=f"q{i}", latency_ms=i * 10)
        runs = _fetch_dive_runs(store)
        self.assertEqual(len(runs), 3)


if __name__ == "__main__":
    unittest.main()
