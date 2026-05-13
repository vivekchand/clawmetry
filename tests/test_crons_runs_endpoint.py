"""Tests for the per-job run timeline endpoint (issue #605).

Covers ``GET /api/crons/<jobId>/runs`` which reads
``~/.openclaw/cron/runs/{jobId}.jsonl`` and returns the last N runs
most-recent-first. Endpoint must NEVER 500 — missing file / malformed
lines must still return 200 with an empty or partial list.

Builds an isolated Flask app with just ``bp_crons`` so we don't have to
stand up the full dashboard (mirrors ``test_crons_local_store.py``).
"""

from __future__ import annotations

import importlib
import json
import os

import pytest
from flask import Flask


# ── helpers ────────────────────────────────────────────────────────────────


def _build_app(tmp_path, monkeypatch):
    """Build an isolated Flask app with bp_crons rooted at tmp_path/.openclaw."""
    fake_home = tmp_path / "openclaw_home"
    runs_dir = fake_home / "cron" / "runs"
    runs_dir.mkdir(parents=True, exist_ok=True)
    # Pin OPENCLAW_HOME so _resolve_cron_runs_jsonl picks our fixture
    # over the real ~/.openclaw on the dev box.
    monkeypatch.setenv("OPENCLAW_HOME", str(fake_home))
    # Force-disable the local-store fast path — irrelevant here, but
    # keeps the test hermetic if the dev env has CLAWMETRY_LOCAL_STORE_READ=1.
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_READ", "0")

    import routes.crons as cr
    importlib.reload(cr)

    app = Flask(__name__)
    app.register_blueprint(cr.bp_crons)
    return app, runs_dir


def _write_jsonl(runs_dir, job_id, records):
    fpath = runs_dir / f"{job_id}.jsonl"
    with open(fpath, "w") as f:
        for r in records:
            f.write(json.dumps(r) + "\n")
    return fpath


# ── fixtures ───────────────────────────────────────────────────────────────


@pytest.fixture
def app_and_runs(tmp_path, monkeypatch):
    yield _build_app(tmp_path, monkeypatch)


# ── tests ──────────────────────────────────────────────────────────────────


class TestCronRunsEndpoint:
    """Spec from issue #605."""

    def test_missing_file_returns_200_empty(self, app_and_runs):
        app, _runs_dir = app_and_runs
        client = app.test_client()
        resp = client.get("/api/crons/does-not-exist/runs")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["jobId"] == "does-not-exist"
        assert data["runs"] == []
        assert data["count"] == 0
        assert data["file"] is None

    def test_reads_jsonl_and_returns_records(self, app_and_runs):
        app, runs_dir = app_and_runs
        records = [
            {
                "ts": 1_700_000_000_000 + i * 60_000,
                "duration_ms": 1000 + i * 50,
                "status": "ok" if i % 2 == 0 else "error",
                "error": "something failed" if i % 2 else "",
                "usage": {"total_tokens": 100 + i},
                "delivered_at": 1_700_000_000_000 + i * 60_000 + 500 if i % 2 == 0 else None,
                "next_run_at": 1_700_000_000_000 + (i + 1) * 60_000,
            }
            for i in range(5)
        ]
        _write_jsonl(runs_dir, "test-job", records)

        resp = app.test_client().get("/api/crons/test-job/runs")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["jobId"] == "test-job"
        assert data["count"] == 5
        assert len(data["runs"]) == 5
        # Most-recent first → timestamps must be descending.
        ts_list = [r["ts"] for r in data["runs"]]
        assert ts_list == sorted(ts_list, reverse=True)
        # Sanity: top run carries the expected shape keys.
        top = data["runs"][0]
        for k in ("ts", "duration_ms", "status", "error", "usage",
                  "delivered_at", "next_run_at"):
            assert k in top, f"missing key {k} in {top}"

    def test_limit_default_30_and_cap_100(self, app_and_runs):
        app, runs_dir = app_and_runs
        # 150 records — more than the cap.
        records = [
            {"ts": 1_700_000_000_000 + i * 1000, "duration_ms": 10, "status": "ok"}
            for i in range(150)
        ]
        _write_jsonl(runs_dir, "big-job", records)

        client = app.test_client()
        d1 = client.get("/api/crons/big-job/runs").get_json()
        assert d1["count"] == 30  # default
        d2 = client.get("/api/crons/big-job/runs?limit=10").get_json()
        assert d2["count"] == 10
        d3 = client.get("/api/crons/big-job/runs?limit=999").get_json()
        assert d3["count"] == 100  # capped
        d4 = client.get("/api/crons/big-job/runs?limit=garbage").get_json()
        assert d4["count"] == 30  # falls back to default

    def test_malformed_lines_are_skipped(self, app_and_runs):
        app, runs_dir = app_and_runs
        fpath = runs_dir / "messy.jsonl"
        with open(fpath, "w") as f:
            f.write('{"ts": 1700000000000, "status": "ok", "duration_ms": 100}\n')
            f.write("this is not json\n")
            f.write("\n")  # blank
            f.write('{"ts": 1700000060000, "status": "error", "error": "boom"}\n')
            f.write("{broken json\n")
        resp = app.test_client().get("/api/crons/messy/runs")
        assert resp.status_code == 200
        data = resp.get_json()
        # Two parseable lines, two malformed/blank skipped.
        assert data["count"] == 2
        # Status values survived.
        statuses = [r["status"] for r in data["runs"]]
        assert "ok" in statuses
        assert "error" in statuses

    def test_error_truncated_to_200_chars(self, app_and_runs):
        app, runs_dir = app_and_runs
        long_err = "x" * 500
        _write_jsonl(runs_dir, "err-job", [
            {"ts": 1, "status": "error", "duration_ms": 0, "error": long_err},
        ])
        data = app.test_client().get("/api/crons/err-job/runs").get_json()
        assert len(data["runs"][0]["error"]) == 200

    def test_path_traversal_rejected(self, app_and_runs):
        app, _ = app_and_runs
        client = app.test_client()
        # Flask's URL routing rejects ".." in <job_id> as a 404 redirect,
        # so we test the helper directly for the slash + `..` cases that
        # could otherwise sneak through manual URL-encoding.
        import routes.crons as cr
        assert cr._resolve_cron_runs_jsonl("../../etc/passwd") is None
        assert cr._resolve_cron_runs_jsonl("a/b") is None
        assert cr._resolve_cron_runs_jsonl("") is None

    def test_camelcase_field_names_also_accepted(self, app_and_runs):
        """OpenClaw writers have historically alternated camelCase /
        snake_case. We accept both and normalise to the spec contract."""
        app, runs_dir = app_and_runs
        _write_jsonl(runs_dir, "camel", [
            {
                "timestamp": "2026-05-13T12:00:00Z",
                "durationMs": 2500,
                "status": "ok",
                "deliveryStatus": {"deliveredAt": "2026-05-13T12:00:03Z"},
                "nextRunAtMs": 1_800_000_000_000,
            }
        ])
        data = app.test_client().get("/api/crons/camel/runs").get_json()
        assert data["count"] == 1
        r = data["runs"][0]
        assert r["duration_ms"] == 2500
        assert r["status"] == "ok"
        assert r["delivered_at"] is not None
        assert r["next_run_at"] == 1_800_000_000_000
        assert r["ts"] > 0  # ISO timestamp parsed to ms
