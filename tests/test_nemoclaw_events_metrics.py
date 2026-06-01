"""Tests for /api/nemoclaw/events and /api/nemoclaw/metrics (GH #876)."""
import json
import os
import sys
import unittest
from unittest.mock import MagicMock, patch

os.environ["CLAWMETRY_NO_INTERCEPT"] = "1"
os.environ["CLAWMETRY_DASHBOARD"] = "1"

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


def _make_app():
    """Build a minimal Flask app with only the NemoClaw blueprint registered."""
    from flask import Flask
    app = Flask(__name__)
    app.config["TESTING"] = True

    # Stub out dashboard helpers used by the routes
    import types
    dashboard_stub = types.ModuleType("dashboard")
    dashboard_stub._detect_nemoclaw = lambda: None  # NemoClaw not installed
    sys.modules.setdefault("dashboard", dashboard_stub)

    from routes.nemoclaw import bp_nemoclaw
    app.register_blueprint(bp_nemoclaw)
    return app


# The /api/nemoclaw/events + /metrics endpoints moved to clawmetry-pro;
# vanilla OSS now serves the 402 upgrade stub on both. The real impl
# (DuckDB-backed events + aggregate metrics) is covered by clawmetry-pro's
# own suite. The LocalStore guardrail helpers below stay in OSS and keep
# their direct unit coverage.


def _assert_upgrade_required(test, resp):
    test.assertEqual(resp.status_code, 402)
    data = json.loads(resp.data)
    test.assertEqual(data.get("error"), "upgrade_required")
    test.assertEqual(data.get("feature"), "nemo_governance")
    test.assertIn("hint", data)


class TestNemoClawEventsEndpointStub(unittest.TestCase):

    def setUp(self):
        self.app = _make_app()
        self.client = self.app.test_client()

    def test_events_returns_402(self):
        _assert_upgrade_required(self, self.client.get("/api/nemoclaw/events"))


class TestNemoClawMetricsEndpointStub(unittest.TestCase):

    def setUp(self):
        self.app = _make_app()
        self.client = self.app.test_client()

    def test_metrics_returns_402(self):
        _assert_upgrade_required(self, self.client.get("/api/nemoclaw/metrics"))


class TestLocalStoreGuardrailMethods(unittest.TestCase):
    """Unit tests for ingest_guardrail_event and query_guardrail_events."""

    def _make_store(self):
        from clawmetry.local_store import LocalStore
        import tempfile, pathlib
        tmp = pathlib.Path(tempfile.mkdtemp()) / "test.duckdb"
        store = LocalStore.__new__(LocalStore)
        import duckdb, threading
        store._conn = duckdb.connect(str(tmp))
        store._write_lock = threading.Lock()
        store._path = tmp
        # Run only the DDL we need
        store._conn.execute("""
            CREATE TABLE IF NOT EXISTS guardrail_events (
                id VARCHAR PRIMARY KEY,
                owner_hash VARCHAR,
                ts VARCHAR NOT NULL,
                rule_name VARCHAR,
                verdict VARCHAR,
                session_id VARCHAR,
                action VARCHAR,
                latency_ms DOUBLE
            )
        """)
        store._conn.execute("""
            CREATE TABLE IF NOT EXISTS approvals (
                id VARCHAR PRIMARY KEY,
                owner_hash VARCHAR,
                requestor_session_id VARCHAR,
                action VARCHAR,
                args BLOB,
                status VARCHAR NOT NULL DEFAULT 'pending',
                created_at VARCHAR,
                resolved_at VARCHAR,
                resolver VARCHAR,
                decision VARCHAR,
                decision_reason VARCHAR
            )
        """)
        return store

    def _fetch(self, store, sql, params=None):
        cur = store._conn.cursor()
        if params:
            cur.execute(sql, params)
        else:
            cur.execute(sql)
        return cur.fetchall()

    # Monkey-patch _fetch on the store instance
    def _attach_fetch(self, store):
        store._fetch = lambda sql, params=None: self._fetch(store, sql, params)

    def test_ingest_and_query_guardrail_event(self):
        store = self._make_store()
        self._attach_fetch(store)
        store.ingest_guardrail_event({
            "id": "evt-1",
            "ts": "2026-05-27T10:00:00",
            "rule_name": "no-exfil",
            "verdict": "triggered",
            "session_id": "sess-abc",
            "action": "write_file",
            "latency_ms": 12.5,
        })
        rows = store.query_guardrail_events()
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["id"], "evt-1")
        self.assertEqual(rows[0]["verdict"], "triggered")
        self.assertAlmostEqual(rows[0]["latency_ms"], 12.5)

    def test_ingest_guardrail_event_requires_id(self):
        store = self._make_store()
        self._attach_fetch(store)
        with self.assertRaises(ValueError):
            store.ingest_guardrail_event({"ts": "2026-05-27T10:00:00"})

    def test_query_guardrail_events_empty(self):
        store = self._make_store()
        self._attach_fetch(store)
        self.assertEqual(store.query_guardrail_events(), [])

    def test_query_nemoclaw_metrics_empty_store(self):
        store = self._make_store()
        self._attach_fetch(store)
        m = store.query_nemoclaw_metrics()
        self.assertEqual(m["total_approvals"], 0)
        self.assertEqual(m["triggers_24h"], 0)
        self.assertIsNone(m["approval_rate_pct"])
        self.assertIsNone(m["avg_latency_secs"])


if __name__ == "__main__":
    unittest.main()
