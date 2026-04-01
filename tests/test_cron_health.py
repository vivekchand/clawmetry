"""
Tests for Cron Health Monitor (GH #302) and Anomaly Detection Engine (GH #301).

Covers:
- GET /api/cron/health-summary — per-job health stats, success rate, anomaly flags
- GET /api/cron/<job_id>/runs — run history with p50/p95 stats
- POST /api/cron/<job_id>/kill — individual kill switch
- POST /api/cron/kill-all — emergency stop all crons
- GET /api/anomalies — rolling-baseline anomaly detection
- POST /api/anomalies/<id>/ack — acknowledge an anomaly
- Unit tests for anomaly detection logic (no server needed)
"""
import os
import sys
import json
import time
import tempfile
import sqlite3
import pytest
import requests

# ---------------------------------------------------------------------------
# Helpers (same as test_api.py)
# ---------------------------------------------------------------------------

def get(api, base_url, path, **kwargs):
    return api.get(f"{base_url}{path}", timeout=10, **kwargs)


def post(api, base_url, path, **kwargs):
    return api.post(f"{base_url}{path}", timeout=10, **kwargs)


def assert_ok(resp):
    assert resp.status_code == 200, (
        f"Expected 200 for {resp.url}, got {resp.status_code}: {resp.text[:300]}"
    )
    return resp.json()


def assert_keys(data, *keys):
    for k in keys:
        assert k in data, f"Missing key '{k}' in response: {list(data.keys())}"


# ---------------------------------------------------------------------------
# Cron Health Monitor — integration tests
# ---------------------------------------------------------------------------

class TestCronHealthSummary:
    """Tests for GET /api/cron/health-summary (GH #302)."""

    def test_returns_200(self, api, base_url):
        r = get(api, base_url, "/api/cron/health-summary")
        assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text[:200]}"

    def test_response_structure(self, api, base_url):
        d = assert_ok(get(api, base_url, "/api/cron/health-summary"))
        assert_keys(d, "jobs", "totals", "hasAnomalies", "hasErrors", "hasSilent")

    def test_jobs_is_list(self, api, base_url):
        d = assert_ok(get(api, base_url, "/api/cron/health-summary"))
        assert isinstance(d["jobs"], list)

    def test_totals_keys(self, api, base_url):
        d = assert_ok(get(api, base_url, "/api/cron/health-summary"))
        totals = d["totals"]
        assert_keys(totals, "total", "ok", "error", "silent", "disabled", "warning")
        assert totals["total"] >= 0

    def test_totals_sum_consistency(self, api, base_url):
        d = assert_ok(get(api, base_url, "/api/cron/health-summary"))
        totals = d["totals"]
        computed = totals["ok"] + totals["error"] + totals["silent"] + totals["disabled"] + totals["warning"]
        assert computed == totals["total"], (
            f"Total {totals['total']} != sum of statuses {computed}"
        )

    def test_job_fields_if_present(self, api, base_url):
        d = assert_ok(get(api, base_url, "/api/cron/health-summary"))
        for job in d["jobs"][:5]:
            assert_keys(job, "id", "name", "enabled", "health", "lastStatus",
                        "costUsd", "costSpike", "durationSpike")
            assert job["health"] in ("ok", "error", "warning", "silent", "disabled"), (
                f"Unexpected health value: {job['health']}"
            )

    def test_booleans_are_booleans(self, api, base_url):
        d = assert_ok(get(api, base_url, "/api/cron/health-summary"))
        for key in ("hasAnomalies", "hasErrors", "hasSilent"):
            assert isinstance(d[key], bool), f"'{key}' should be bool, got {type(d[key])}"

    def test_cost_usd_is_numeric(self, api, base_url):
        d = assert_ok(get(api, base_url, "/api/cron/health-summary"))
        for job in d["jobs"][:5]:
            assert isinstance(job["costUsd"], (int, float)), (
                f"costUsd should be numeric, got {type(job['costUsd'])}"
            )
            assert job["costUsd"] >= 0


class TestCronRunHistory:
    """Tests for GET /api/cron/<job_id>/runs (GH #302)."""

    def test_returns_200_or_502(self, api, base_url):
        """Endpoint always returns 200 (with enriched data) or 502 (gateway down)."""
        # Use a fake job_id — should return empty runs, not a 500
        r = get(api, base_url, "/api/cron/__test_nonexistent_job__/runs")
        assert r.status_code in (200, 502), f"Unexpected status {r.status_code}"

    def test_response_structure(self, api, base_url):
        r = get(api, base_url, "/api/cron/__test_job__/runs")
        if r.status_code == 502:
            pytest.skip("Gateway unavailable")
        d = r.json()
        assert_keys(d, "jobId", "runs", "stats")

    def test_stats_keys(self, api, base_url):
        r = get(api, base_url, "/api/cron/__test_job__/runs")
        if r.status_code == 502:
            pytest.skip("Gateway unavailable")
        d = r.json()
        stats = d["stats"]
        # stats is {} when there are no runs — that's valid; check keys only when populated
        if stats:
            assert_keys(stats, "totalRuns", "successCount", "errorCount",
                        "successRate", "avgDurationMs", "p50DurationMs", "p95DurationMs",
                        "avgCostUsd", "totalCostUsd")

    def test_runs_is_list(self, api, base_url):
        r = get(api, base_url, "/api/cron/__test_job__/runs")
        if r.status_code == 502:
            pytest.skip("Gateway unavailable")
        d = r.json()
        assert isinstance(d["runs"], list)

    def test_success_rate_range(self, api, base_url):
        r = get(api, base_url, "/api/cron/__test_job__/runs")
        if r.status_code == 502:
            pytest.skip("Gateway unavailable")
        d = r.json()
        stats = d["stats"]
        if not stats:
            pytest.skip("No run history for test job (no crons configured)")
        sr = stats["successRate"]
        assert 0 <= sr <= 100, f"successRate {sr} out of range [0, 100]"

    def test_p95_gte_p50(self, api, base_url):
        r = get(api, base_url, "/api/cron/__test_job__/runs")
        if r.status_code == 502:
            pytest.skip("Gateway unavailable")
        d = r.json()
        stats = d["stats"]
        if not stats:
            pytest.skip("No run history for test job (no crons configured)")
        assert stats["p95DurationMs"] >= stats["p50DurationMs"], (
            "p95 should be >= p50"
        )


class TestCronKillSwitch:
    """Tests for POST /api/cron/<job_id>/kill (GH #302)."""

    def test_kill_nonexistent_returns_200_or_502(self, api, base_url):
        """Kill a nonexistent job — should return 200 (ok=False) or 502 (gateway down)."""
        r = post(api, base_url, "/api/cron/__nonexistent_test_kill__/kill",
                 json={})
        assert r.status_code in (200, 502), f"Unexpected status {r.status_code}"

    def test_kill_response_structure(self, api, base_url):
        r = post(api, base_url, "/api/cron/__test_kill_job__/kill", json={})
        if r.status_code == 502:
            pytest.skip("Gateway unavailable")
        d = r.json()
        assert "ok" in d or "error" in d, f"Response should have 'ok' or 'error': {d}"

    def test_kill_all_returns_200(self, api, base_url):
        r = post(api, base_url, "/api/cron/kill-all", json={})
        assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text[:200]}"

    def test_kill_all_response_structure(self, api, base_url):
        d = assert_ok(post(api, base_url, "/api/cron/kill-all", json={}))
        assert_keys(d, "ok", "disabled", "errors")
        assert isinstance(d["disabled"], int)
        assert isinstance(d["errors"], list)


# ---------------------------------------------------------------------------
# Anomaly Detection Engine — integration tests (GH #301)
# ---------------------------------------------------------------------------

class TestAnomaliesEndpoint:
    """Tests for GET /api/anomalies."""

    def test_returns_200(self, api, base_url):
        r = get(api, base_url, "/api/anomalies")
        assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text[:200]}"

    def test_response_structure(self, api, base_url):
        d = assert_ok(get(api, base_url, "/api/anomalies"))
        assert_keys(d, "anomalies", "active_count", "has_active", "baselines",
                    "threshold_cost_multiplier", "threshold_token_multiplier",
                    "threshold_error_multiplier")

    def test_anomalies_is_list(self, api, base_url):
        d = assert_ok(get(api, base_url, "/api/anomalies"))
        assert isinstance(d["anomalies"], list)

    def test_active_count_is_integer(self, api, base_url):
        d = assert_ok(get(api, base_url, "/api/anomalies"))
        assert isinstance(d["active_count"], int)
        assert d["active_count"] >= 0

    def test_has_active_is_bool(self, api, base_url):
        d = assert_ok(get(api, base_url, "/api/anomalies"))
        assert isinstance(d["has_active"], bool)

    def test_has_active_matches_count(self, api, base_url):
        d = assert_ok(get(api, base_url, "/api/anomalies"))
        # has_active should be True iff active_count > 0
        assert d["has_active"] == (d["active_count"] > 0), (
            f"has_active={d['has_active']} but active_count={d['active_count']}"
        )

    def test_baselines_keys(self, api, base_url):
        d = assert_ok(get(api, base_url, "/api/anomalies"))
        baselines = d["baselines"]
        assert_keys(baselines, "baseline_cost_7d", "baseline_tokens_7d",
                    "baseline_error_rate_7d", "session_count_7d")

    def test_thresholds_are_positive(self, api, base_url):
        d = assert_ok(get(api, base_url, "/api/anomalies"))
        assert d["threshold_cost_multiplier"] > 0
        assert d["threshold_token_multiplier"] > 0
        assert d["threshold_error_multiplier"] > 0

    def test_anomaly_fields_if_present(self, api, base_url):
        d = assert_ok(get(api, base_url, "/api/anomalies"))
        for a in d["anomalies"][:5]:
            assert_keys(a, "id", "session_key", "metric", "value", "baseline",
                        "ratio", "severity", "detected_at")
            assert a["metric"] in ("cost_spike", "token_spike", "error_rate_spike"), (
                f"Unexpected metric: {a['metric']}"
            )
            assert a["severity"] in ("critical", "high", "medium"), (
                f"Unexpected severity: {a['severity']}"
            )
            assert a["ratio"] > 0
            assert a["value"] > 0
            assert a["baseline"] > 0

    def test_anomaly_ratio_consistent(self, api, base_url):
        d = assert_ok(get(api, base_url, "/api/anomalies"))
        for a in d["anomalies"][:5]:
            if a["baseline"] > 0:
                expected_ratio = a["value"] / a["baseline"]
                assert abs(a["ratio"] - expected_ratio) < 0.1, (
                    f"ratio {a['ratio']} doesn't match value/baseline {expected_ratio:.3f}"
                )


class TestAnomalyAck:
    """Tests for POST /api/anomalies/<id>/ack."""

    def test_ack_nonexistent_returns_200_or_500(self, api, base_url):
        """ACK on nonexistent ID should be graceful."""
        r = post(api, base_url, "/api/anomalies/99999999/ack", json={})
        assert r.status_code in (200, 500), f"Unexpected status {r.status_code}"

    def test_ack_response_has_ok(self, api, base_url):
        r = post(api, base_url, "/api/anomalies/99999999/ack", json={})
        if r.status_code == 200:
            d = r.json()
            assert "ok" in d


# ---------------------------------------------------------------------------
# Unit tests — anomaly logic (no server needed)
# ---------------------------------------------------------------------------

class TestAnomalyDetectionLogic:
    """Pure unit tests for the anomaly detection algorithms.

    These run without a running server by importing the logic directly.
    """

    def test_cost_spike_detection(self):
        """Sessions with cost > 2x average should be flagged."""
        # Import the function directly
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from dashboard import _compute_session_cost_anomalies

        now = time.time()
        sessions = [
            {'session_id': 'base1', 'cost_usd': 0.01, 'start_ts': now - 6 * 86400},
            {'session_id': 'base2', 'cost_usd': 0.01, 'start_ts': now - 5 * 86400},
            {'session_id': 'base3', 'cost_usd': 0.01, 'start_ts': now - 4 * 86400},
            {'session_id': 'spike', 'cost_usd': 0.10, 'start_ts': now - 3600},  # 10x avg
        ]
        anomalies = _compute_session_cost_anomalies(sessions)
        assert len(anomalies) == 1, f"Expected 1 anomaly, got {len(anomalies)}"
        assert anomalies[0]['session_id'] == 'spike'
        assert anomalies[0]['ratio'] > 2.0

    def test_no_anomaly_when_cost_normal(self):
        """Sessions within 2x average should not be flagged."""
        from dashboard import _compute_session_cost_anomalies

        now = time.time()
        sessions = [
            {'session_id': 'base1', 'cost_usd': 0.05, 'start_ts': now - 6 * 86400},
            {'session_id': 'base2', 'cost_usd': 0.05, 'start_ts': now - 5 * 86400},
            {'session_id': 'base3', 'cost_usd': 0.05, 'start_ts': now - 4 * 86400},
            {'session_id': 'normal', 'cost_usd': 0.09, 'start_ts': now - 3600},  # 1.8x avg
        ]
        anomalies = _compute_session_cost_anomalies(sessions)
        assert len(anomalies) == 0, f"Expected 0 anomalies (1.8x < 2x), got {len(anomalies)}"

    def test_anomalies_sorted_by_ratio_descending(self):
        """Anomalies should be returned most-severe first."""
        from dashboard import _compute_session_cost_anomalies

        now = time.time()
        sessions = [
            {'session_id': 'base1', 'cost_usd': 0.01, 'start_ts': now - 6 * 86400},
            {'session_id': 'base2', 'cost_usd': 0.01, 'start_ts': now - 5 * 86400},
            {'session_id': 'base3', 'cost_usd': 0.01, 'start_ts': now - 4 * 86400},
            {'session_id': 'mild_spike', 'cost_usd': 0.03, 'start_ts': now - 7200},  # 3x
            {'session_id': 'big_spike', 'cost_usd': 0.10, 'start_ts': now - 3600},   # 10x
        ]
        anomalies = _compute_session_cost_anomalies(sessions)
        assert len(anomalies) >= 1
        for i in range(len(anomalies) - 1):
            assert anomalies[i]['ratio'] >= anomalies[i + 1]['ratio'], (
                "Anomalies not sorted by ratio descending"
            )

    def test_enrich_cron_runs_p95(self):
        """p95 should be >= p50 in enriched cron run stats."""
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from dashboard import _enrich_cron_runs

        runs = [
            {'status': 'ok', 'durationMs': 1000, 'costUsd': 0.01},
            {'status': 'ok', 'durationMs': 1200, 'costUsd': 0.01},
            {'status': 'ok', 'durationMs': 1100, 'costUsd': 0.01},
            {'status': 'ok', 'durationMs': 1050, 'costUsd': 0.01},
            {'status': 'error', 'durationMs': 5000, 'costUsd': 0.0},  # outlier
        ]
        result = _enrich_cron_runs('test_job', runs)
        stats = result['stats']
        assert stats['p95DurationMs'] >= stats['p50DurationMs']
        assert stats['totalRuns'] == 5
        assert stats['successCount'] == 4
        assert stats['errorCount'] == 1
        assert abs(stats['successRate'] - 80.0) < 0.1

    def test_enrich_cron_runs_empty(self):
        """Empty run list should return zero stats."""
        from dashboard import _enrich_cron_runs
        result = _enrich_cron_runs('empty_job', [])
        assert result['runs'] == []
        assert result['stats'] == {}

    def test_anomaly_db_schema(self):
        """Anomaly DB should be creatable with correct schema."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        try:
            conn = sqlite3.connect(db_path)
            conn.executescript('''
                CREATE TABLE IF NOT EXISTS anomalies (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    detected_at REAL NOT NULL,
                    session_key TEXT NOT NULL,
                    metric TEXT NOT NULL,
                    value REAL NOT NULL,
                    baseline REAL NOT NULL,
                    ratio REAL NOT NULL,
                    severity TEXT NOT NULL,
                    acknowledged INTEGER DEFAULT 0
                );
            ''')
            conn.execute(
                'INSERT INTO anomalies (detected_at, session_key, metric, value, baseline, ratio, severity) VALUES (?, ?, ?, ?, ?, ?, ?)',
                (time.time(), 'test_session', 'cost_spike', 0.10, 0.01, 10.0, 'critical')
            )
            conn.commit()
            rows = conn.execute('SELECT * FROM anomalies').fetchall()
            assert len(rows) == 1
            row = dict(zip([d[0] for d in conn.execute('SELECT * FROM anomalies').description], rows[0]))
            assert row['metric'] == 'cost_spike'
            assert row['severity'] == 'critical'
            assert row['acknowledged'] == 0
            conn.close()
        finally:
            os.unlink(db_path)
