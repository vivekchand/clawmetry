"""Tests for the Crons-tab local-store fast paths (epic #964 phase 4).

Mirrors the opt-in pattern used by ``test_sessions_local_fastpath.py`` and
``test_heartbeat_local_store.py``:

  CLAWMETRY_LOCAL_STORE_READ=1 + populated ``crons`` table → response is
  served from DuckDB and tagged ``_source: local_store``. Flag unset OR
  empty store → fast path returns None and the legacy gateway/file path
  runs (we patch the gateway out so we can assert on the response shape
  without standing up a real OpenClaw).

Routes covered:
  /api/crons
  /api/cron/<job_id>/runs
  /api/cron/health-summary
  /api/cron-health
"""

from __future__ import annotations

import importlib

import pytest
from flask import Flask


# ── fixtures ───────────────────────────────────────────────────────────────


def _build_app(tmp_path, monkeypatch, *, enable_fast_path: bool):
    """Build an isolated Flask app with bp_crons + a tmp DuckDB.

    Reload order matters: ``local_store`` first (so its module-level path
    constants pick up the env var), then ``routes.crons`` so its lazy
    imports resolve against the freshly-loaded store.
    """
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "events.duckdb"))
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_SECS", "0.05")
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_BATCH", "5")
    if enable_fast_path:
        monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_READ", "1")
    else:
        monkeypatch.delenv("CLAWMETRY_LOCAL_STORE_READ", raising=False)

    import clawmetry.local_store as ls
    importlib.reload(ls)
    import routes.crons as cr
    importlib.reload(cr)

    app = Flask(__name__)
    # cron-health calls api_cron_health_summary() under
    # _d.app.test_request_context() — it doesn't need OUR app to be the one,
    # just Flask's app context. Register the blueprint and we're set.
    app.register_blueprint(cr.bp_crons)
    return app, ls, cr


@pytest.fixture
def fast_path_app(tmp_path, monkeypatch):
    app, ls, cr = _build_app(tmp_path, monkeypatch, enable_fast_path=True)
    yield app, ls, cr
    try:
        ls.get_store().stop(flush=True)
    except Exception:
        pass


@pytest.fixture
def no_flag_app(tmp_path, monkeypatch):
    """Same shape as fast_path_app but with CLAWMETRY_LOCAL_STORE_READ unset.
    Used by the negative test that asserts the env gate is honoured."""
    app, ls, cr = _build_app(tmp_path, monkeypatch, enable_fast_path=False)
    yield app, ls, cr
    try:
        ls.get_store().stop(flush=True)
    except Exception:
        pass


def _seed_two_crons(store):
    """Insert two cron jobs typical of an OpenClaw install. Timestamps are
    pinned to ~now so the silent-job detector (>2.5x interval) doesn't fire
    and shadow the per-status health classification we want to assert on."""
    import time
    from datetime import datetime, timezone, timedelta
    now = datetime.now(timezone.utc)
    recent_iso = (now - timedelta(seconds=30)).isoformat()
    next_iso = (now + timedelta(minutes=5)).isoformat()
    store.ingest_cron({
        "cron_id": "daily-backup",
        "name": "Daily Backup",
        "schedule": '{"kind":"cron","expr":"0 3 * * *"}',
        "enabled": True,
        "last_run_at": recent_iso,
        "last_status": "success",
        "next_run_at": next_iso,
        "createdAtMs": int(time.time() * 1000) - 86400000,
        "lastDurationMs": 4500,
        "consecutiveFailures": 0,
    })
    store.ingest_cron({
        "cron_id": "metrics-poll",
        "name": "Metrics Poll",
        # Long enough interval that the recent_iso last_run_at stays inside
        # the 2.5x silent-job window.
        "schedule": '{"kind":"every","everyMs":3600000}',
        "enabled": True,
        "last_run_at": recent_iso,
        "last_status": "error",
        "next_run_at": next_iso,
        "createdAtMs": int(time.time() * 1000) - 86400000,
        "lastDurationMs": 1200,
        "consecutiveFailures": 4,
        "lastError": "connection refused",
    })


def _seed_runs_for(store, cron_id, n=5, status="ok"):
    """Insert n cron_run events for cron_id via the events table."""
    import time
    for i in range(n):
        store.ingest({
            "id":          f"run-{cron_id}-{i}",
            "node_id":     "agent+test",
            "agent_id":    cron_id,
            "session_id":  f"sess-{cron_id}-{i}",
            "event_type":  "cron_run",
            "ts":          f"2026-05-1{i+1}T07:00:00Z",
            "data":        {"cron_id": cron_id, "status": status, "durationMs": 1000 + i * 100},
            "cost_usd":    0.012,
            "token_count": 200 + i,
        })
    # Block until ring buffer drains.
    deadline = time.monotonic() + 2.0
    while time.monotonic() < deadline:
        if store.health()["ring_depth"] == 0:
            return
        time.sleep(0.02)


# ── /api/crons ─────────────────────────────────────────────────────────────


def test_crons_fast_path_returns_local_store_data(fast_path_app):
    """Populated crons table → fast path serves from DuckDB and the response
    keeps the documented {jobs: [...]} contract."""
    app, ls, _cr = fast_path_app
    _seed_two_crons(ls.get_store())

    body = app.test_client().get("/api/crons").get_json()
    assert body.get("_source") == "local_store"
    assert "jobs" in body
    jobs = body["jobs"]
    assert len(jobs) == 2

    by_id = {j["id"]: j for j in jobs}
    assert "daily-backup" in by_id
    assert "metrics-poll" in by_id

    daily = by_id["daily-backup"]
    # Keys the dashboard JS reads.
    for k in ("id", "name", "schedule", "enabled", "state",
              "cost_usd", "cost_session_count", "cost_session_ids"):
        assert k in daily, f"job missing key {k}: {daily}"
    assert daily["enabled"] is True
    assert isinstance(daily["state"], dict)
    # JSON-encoded schedule string in the column should decode to a dict.
    assert isinstance(daily["schedule"], dict)
    assert daily["schedule"].get("kind") == "cron"
    # ISO timestamps must be reshaped into ms ints for the JS layer.
    assert isinstance(daily["state"]["lastRunAtMs"], int)
    assert daily["state"]["lastRunAtMs"] > 0
    assert isinstance(daily["state"]["nextRunAtMs"], int)
    assert daily["state"]["nextRunAtMs"] > 0
    # State extras stashed in the data blob round-trip.
    assert daily["state"]["lastStatus"] == "success"
    assert daily["state"]["lastDurationMs"] == 4500


def test_crons_fast_path_falls_through_when_store_empty(fast_path_app):
    """Empty crons table → fast path returns None and the legacy path runs.
    With no gateway in this test env the legacy path returns {jobs: []}."""
    app, _ls, _cr = fast_path_app
    body = app.test_client().get("/api/crons").get_json()
    # Fell through → no _source tag.
    assert body.get("_source") != "local_store"
    assert "jobs" in body


def test_crons_fast_path_disabled_without_env_flag(no_flag_app):
    """Negative test: CLAWMETRY_LOCAL_STORE_READ unset → DuckDB is never
    queried even with a populated store. The handler defers to the legacy
    gateway/file path."""
    app, ls, _cr = no_flag_app
    _seed_two_crons(ls.get_store())

    body = app.test_client().get("/api/crons").get_json()
    assert body.get("_source") != "local_store"
    assert "jobs" in body


# ── /api/cron/<job_id>/runs ────────────────────────────────────────────────


def test_cron_runs_fast_path_returns_runs(fast_path_app):
    """Populated events table with cron_run rows → fast path returns the
    enriched runs payload tagged with ``_source``."""
    app, ls, _cr = fast_path_app
    _seed_runs_for(ls.get_store(), "daily-backup", n=5)

    body = app.test_client().get("/api/cron/daily-backup/runs").get_json()
    assert body.get("_source") == "local_store"
    assert body.get("jobId") == "daily-backup"
    assert isinstance(body.get("runs"), list)
    assert len(body["runs"]) == 5

    # Most-recent first.
    timestamps = [r["timestamp"] for r in body["runs"]]
    assert timestamps == sorted(timestamps, reverse=True)

    # Every run must carry the contract keys.
    for r in body["runs"]:
        for k in ("sessionId", "timestamp", "status", "durationMs", "costUsd", "tokens"):
            assert k in r, f"run missing key {k}: {r}"

    # Stats block from _enrich_cron_runs.
    stats = body.get("stats", {})
    assert stats.get("totalRuns") == 5
    assert stats.get("successCount") == 5  # default status='ok' from seed


def test_cron_runs_fast_path_filters_by_job_id(fast_path_app):
    """Events for OTHER cron jobs must not leak into a single-job runs query."""
    app, ls, _cr = fast_path_app
    _seed_runs_for(ls.get_store(), "daily-backup", n=3)
    _seed_runs_for(ls.get_store(), "metrics-poll", n=2)

    body = app.test_client().get("/api/cron/daily-backup/runs").get_json()
    assert body.get("_source") == "local_store"
    assert len(body["runs"]) == 3
    # All session ids should reference the daily-backup job.
    assert all("daily-backup" in r["sessionId"] for r in body["runs"])


def test_cron_runs_fast_path_falls_through_when_no_events(fast_path_app):
    """No matching events → fast path returns None → legacy path runs."""
    app, _ls, _cr = fast_path_app
    body = app.test_client().get("/api/cron/daily-backup/runs").get_json()
    # Legacy path enriches an empty list — payload must NOT carry _source tag.
    assert body.get("_source") != "local_store"


# ── /api/cron/health-summary ───────────────────────────────────────────────


def test_health_summary_fast_path_returns_summary(fast_path_app):
    """Populated crons table → health-summary fast path runs and the response
    matches the documented contract."""
    app, ls, _cr = fast_path_app
    _seed_two_crons(ls.get_store())

    body = app.test_client().get("/api/cron/health-summary").get_json()
    assert body.get("_source") == "local_store"
    for k in ("jobs", "totals", "hasAnomalies", "hasErrors", "hasSilent"):
        assert k in body, f"health-summary missing key {k}"

    jobs = body["jobs"]
    assert len(jobs) == 2
    by_id = {j["id"]: j for j in jobs}

    # daily-backup: enabled, success, no consecutive failures → ok
    daily = by_id["daily-backup"]
    assert daily["enabled"] is True
    assert daily["health"] == "ok"
    assert daily["lastStatus"] == "success"
    assert daily["lastDurationMs"] == 4500

    # metrics-poll: enabled, error, 4 consecutive failures → error
    metrics = by_id["metrics-poll"]
    assert metrics["enabled"] is True
    assert metrics["health"] == "error"
    assert metrics["consecutiveFailures"] == 4
    assert metrics["lastError"] == "connection refused"

    totals = body["totals"]
    assert totals["total"] == 2
    assert totals["error"] >= 1
    assert body["hasErrors"] is True


def test_health_summary_fast_path_falls_through_when_empty(fast_path_app):
    """Empty crons table → fast path defers to the legacy gateway path
    (which itself has no gateway in test env, so returns an empty summary)."""
    app, _ls, _cr = fast_path_app
    body = app.test_client().get("/api/cron/health-summary").get_json()
    assert body.get("_source") != "local_store"
    assert "jobs" in body


def test_health_summary_disabled_without_env_flag(no_flag_app):
    """Env gate honoured: populated store + flag unset → legacy path."""
    app, ls, _cr = no_flag_app
    _seed_two_crons(ls.get_store())
    body = app.test_client().get("/api/cron/health-summary").get_json()
    assert body.get("_source") != "local_store"


# ── /api/cron-health (alias on top of health-summary) ──────────────────────


def test_cron_health_alias_inherits_fast_path(fast_path_app):
    """Since /api/cron-health delegates to /api/cron/health-summary, the
    fast-path tag should propagate up to the alias's response."""
    app, ls, _cr = fast_path_app
    _seed_two_crons(ls.get_store())

    body = app.test_client().get("/api/cron-health").get_json()
    assert body.get("_source") == "local_store"
    # Documented alias shape.
    for k in ("crons", "totals", "has_anomalies"):
        assert k in body, f"cron-health missing key {k}"
    crons = body["crons"]
    assert len(crons) == 2
    for c in crons:
        for k in ("id", "name", "enabled", "health", "stats", "recent_runs", "last_error"):
            assert k in c, f"cron-health row missing key {k}: {c}"
        for sk in ("success_rate", "total_runs", "avg_duration_ms", "total_cost_usd"):
            assert sk in c["stats"]


def test_cron_health_disabled_without_env_flag(no_flag_app):
    """Env gate also honoured by the alias: no flag → no fast path."""
    app, ls, _cr = no_flag_app
    _seed_two_crons(ls.get_store())
    body = app.test_client().get("/api/cron-health").get_json()
    assert body.get("_source") != "local_store"
