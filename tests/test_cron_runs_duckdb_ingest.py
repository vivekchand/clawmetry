"""Tests for the cron-run JSONL → DuckDB ingest path (issue #605 follow-up).

PR #1147 had the dashboard route parse ``~/.openclaw/cron/runs/*.jsonl``
on every request — a violation of the DuckDB-first rule. The follow-up
moves the parse into the sync daemon and exposes a ``query_cron_runs``
read path. These tests cover:

  1. ``sync_cron_runs`` parses a JSONL file into DuckDB rows.
  2. Re-running ``sync_cron_runs`` does not duplicate (offset tracking).
  3. ``LocalStore.query_cron_runs`` filters + sorts correctly.
  4. ``/api/crons/<jobId>/runs`` reads from DuckDB when the store is
     populated, and falls back to the JSONL reader otherwise.

Tests are hermetic: each one rebuilds the LocalStore singleton against a
tmp DuckDB and pins ``OPENCLAW_HOME`` so the resolver picks up the test
fixture rather than the dev box's real ``~/.openclaw``.
"""

from __future__ import annotations

import importlib
import json
import os

import pytest


# ── fixtures ───────────────────────────────────────────────────────────────


@pytest.fixture
def isolated(tmp_path, monkeypatch):
    """Reload ``local_store`` + ``sync`` + ``routes.crons`` against an
    isolated tmp DuckDB and a tmp OpenClaw home. Yields a bundle with
    the freshly-loaded modules + the runs dir for fixture writes."""
    db_path = tmp_path / "clawmetry.duckdb"
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(db_path))
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_SECS", "0.05")
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_BATCH", "5")
    # Pin OPENCLAW_HOME so _cron_run_dirs (in sync.py) + _resolve_cron_runs_jsonl
    # (in routes.crons) discover OUR fake tree, not the developer laptop's
    # real ~/.openclaw.
    fake_home = tmp_path / "openclaw_home"
    runs_dir = fake_home / "cron" / "runs"
    runs_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("OPENCLAW_HOME", str(fake_home))
    monkeypatch.setenv("CLAWMETRY_OPENCLAW_DIR", str(fake_home))
    # The legacy CLAWMETRY_LOCAL_STORE_READ gate doesn't apply to the new
    # endpoint (it always reads from DuckDB first), but the unrelated
    # ``_try_local_store_cron_runs`` fast path consults it — set 0 so we
    # don't accidentally serve old data from the events table.
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_READ", "0")

    import clawmetry.local_store as ls
    importlib.reload(ls)
    import clawmetry.sync as sync
    importlib.reload(sync)
    import routes.crons as cr
    importlib.reload(cr)

    yield {
        "ls": ls,
        "sync": sync,
        "cr": cr,
        "runs_dir": runs_dir,
        "fake_home": fake_home,
    }
    try:
        ls.get_store().stop(flush=True)
    except Exception:
        pass


def _write_jsonl(runs_dir, job_id, records):
    fpath = runs_dir / f"{job_id}.jsonl"
    with open(fpath, "w") as f:
        for r in records:
            f.write(json.dumps(r) + "\n")
    return fpath


def _build_app(cr):
    from flask import Flask
    app = Flask(__name__)
    app.register_blueprint(cr.bp_crons)
    return app


# ── ingest tests ───────────────────────────────────────────────────────────


class TestSyncCronRunsIngest:
    """``sync_cron_runs`` parses JSONL into DuckDB rows."""

    def test_ingests_five_lines_into_cron_runs(self, isolated):
        sync = isolated["sync"]
        ls = isolated["ls"]
        runs_dir = isolated["runs_dir"]
        records = [
            {
                "id": f"run-{i}",
                "started_at": f"2026-05-13T10:00:0{i}Z",
                "duration_ms": 1000 + i * 50,
                "status": "ok" if i % 2 == 0 else "error",
                "error": "boom" if i % 2 else "",
                "usage": {"total_tokens": 100 + i,
                          "input_tokens": 50 + i,
                          "output_tokens": 50},
                "delivered_at": f"2026-05-13T10:00:0{i}.500Z" if i % 2 == 0 else None,
                "next_run_at": f"2026-05-13T10:01:0{i}Z",
            }
            for i in range(5)
        ]
        _write_jsonl(runs_dir, "daily-backup", records)

        state = {"cron_run_offsets": {}}
        config = {"node_id": "test-node", "api_key": "cm_test"}
        n = sync.sync_cron_runs(config, state, paths={})
        assert n == 5, f"expected 5 rows ingested, got {n}"

        # Verify rows in DuckDB.
        store = ls.get_store()
        rows = store.query_cron_runs(job_id="daily-backup", limit=20)
        assert len(rows) == 5
        # Most-recent-first ordering.
        assert rows[0]["id"] == "run-4"
        assert rows[-1]["id"] == "run-0"
        # First-class columns round-trip.
        assert rows[0]["status"] == "ok"
        assert rows[0]["duration_ms"] == 1200
        # Freeform usage payload preserved via the data BLOB.
        assert isinstance(rows[0]["data"], dict)
        assert rows[0]["data"].get("usage", {}).get("total_tokens") == 104

    def test_rerun_does_not_duplicate(self, isolated):
        """The offset cursor + INSERT OR IGNORE combine to keep re-runs
        idempotent. Re-scanning the same file must not add new rows."""
        sync = isolated["sync"]
        ls = isolated["ls"]
        runs_dir = isolated["runs_dir"]
        records = [
            {
                "id": f"run-{i}",
                "started_at": f"2026-05-13T11:00:0{i}Z",
                "duration_ms": 1000 + i * 100,
                "status": "ok",
            }
            for i in range(3)
        ]
        _write_jsonl(runs_dir, "deploy-bot", records)

        state = {"cron_run_offsets": {}}
        config = {"node_id": "test-node"}
        first = sync.sync_cron_runs(config, state, paths={})
        assert first == 3
        # Offset must have advanced past the file.
        offsets = state["cron_run_offsets"]
        assert any(k.endswith("deploy-bot.jsonl") for k in offsets), \
            f"offsets did not record file: {offsets!r}"
        offset_after_first = list(offsets.values())[0]
        assert offset_after_first > 0

        # Second pass: file unchanged, offset == size, zero new rows.
        second = sync.sync_cron_runs(config, state, paths={})
        assert second == 0, "second sync re-ingested rows"

        store = ls.get_store()
        rows = store.query_cron_runs(job_id="deploy-bot", limit=20)
        assert len(rows) == 3

    def test_append_after_first_sync_ingests_only_new(self, isolated):
        """Append a fourth line after the first sync. Only the new line
        is parsed (offset moved) but DuckDB rows from before still exist."""
        sync = isolated["sync"]
        ls = isolated["ls"]
        runs_dir = isolated["runs_dir"]
        fpath = _write_jsonl(runs_dir, "weekly-report", [
            {"id": "r-0", "started_at": "2026-05-13T12:00:00Z",
             "duration_ms": 500, "status": "ok"},
            {"id": "r-1", "started_at": "2026-05-13T12:00:01Z",
             "duration_ms": 600, "status": "ok"},
        ])
        state = {"cron_run_offsets": {}}
        config = {"node_id": "test"}
        assert sync.sync_cron_runs(config, state, paths={}) == 2

        # Append one more line.
        with open(fpath, "a") as f:
            f.write(json.dumps({"id": "r-2", "started_at": "2026-05-13T12:00:02Z",
                                "duration_ms": 700, "status": "ok"}) + "\n")
        assert sync.sync_cron_runs(config, state, paths={}) == 1

        store = ls.get_store()
        rows = store.query_cron_runs(job_id="weekly-report", limit=20)
        assert len(rows) == 3

    def test_malformed_lines_skipped_not_raised(self, isolated):
        """A garbled line in the middle of a file mustn't abort the sync —
        the rest of the file's valid lines must still ingest."""
        sync = isolated["sync"]
        ls = isolated["ls"]
        runs_dir = isolated["runs_dir"]
        fpath = runs_dir / "noisy-job.jsonl"
        with open(fpath, "w") as f:
            f.write(json.dumps({"id": "ok-1", "started_at": "2026-05-13T13:00:00Z",
                                "status": "ok", "duration_ms": 100}) + "\n")
            f.write("{not valid json\n")
            f.write(json.dumps({"id": "ok-2", "started_at": "2026-05-13T13:00:01Z",
                                "status": "ok", "duration_ms": 200}) + "\n")
            f.write("\n")  # blank line
            f.write("42\n")  # non-dict
            f.write(json.dumps({"id": "ok-3", "started_at": "2026-05-13T13:00:02Z",
                                "status": "ok", "duration_ms": 300}) + "\n")

        n = sync.sync_cron_runs({"node_id": "x"}, {"cron_run_offsets": {}},
                                 paths={})
        assert n == 3

        store = ls.get_store()
        rows = store.query_cron_runs(job_id="noisy-job", limit=20)
        assert sorted(r["id"] for r in rows) == ["ok-1", "ok-2", "ok-3"]

    def test_missing_runs_dir_returns_zero(self, tmp_path, monkeypatch):
        """No JSONLs → zero rows, no exception. ClawMetry must work on
        a fresh install where the OpenClaw cron writer hasn't run yet."""
        monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH",
                           str(tmp_path / "clawmetry.duckdb"))
        monkeypatch.setenv("OPENCLAW_HOME", str(tmp_path / "nothing-here"))
        monkeypatch.setenv("CLAWMETRY_OPENCLAW_DIR", str(tmp_path / "nothing-here"))
        import clawmetry.local_store as ls
        import clawmetry.sync as sync
        importlib.reload(ls)
        importlib.reload(sync)
        try:
            n = sync.sync_cron_runs({"node_id": "x"},
                                     {"cron_run_offsets": {}},
                                     paths={})
            assert n == 0
        finally:
            try:
                ls.get_store().stop(flush=True)
            except Exception:
                pass


# ── query tests ────────────────────────────────────────────────────────────


class TestQueryCronRuns:
    """``LocalStore.query_cron_runs`` filters + sorts as documented."""

    def test_filter_by_job_id_and_desc_sort(self, isolated):
        ls = isolated["ls"]
        store = ls.get_store()
        # Seed two jobs interleaved by timestamp.
        for i, job in enumerate(["job-a", "job-b", "job-a", "job-b"]):
            store.ingest_cron_run({
                "id": f"{job}:{i}",
                "job_id": job,
                "started_at": f"2026-05-13T14:00:0{i}Z",
                "duration_ms": 100 * (i + 1),
                "status": "ok",
            })
        rows_a = store.query_cron_runs(job_id="job-a", limit=10)
        assert len(rows_a) == 2
        # Most-recent-first.
        assert rows_a[0]["id"] == "job-a:2"
        assert rows_a[1]["id"] == "job-a:0"

        rows_b = store.query_cron_runs(job_id="job-b", limit=10)
        assert [r["id"] for r in rows_b] == ["job-b:3", "job-b:1"]

    def test_limit_clamps(self, isolated):
        ls = isolated["ls"]
        store = ls.get_store()
        for i in range(6):
            store.ingest_cron_run({
                "id": f"r-{i}",
                "job_id": "lots-of-runs",
                "started_at": f"2026-05-13T15:00:0{i}Z",
                "duration_ms": 10,
                "status": "ok",
            })
        # limit < total → trimmed
        rows = store.query_cron_runs(job_id="lots-of-runs", limit=2)
        assert len(rows) == 2
        # limit=0 clamped to 1
        rows = store.query_cron_runs(job_id="lots-of-runs", limit=0)
        assert len(rows) == 1
        # negative also clamped
        rows = store.query_cron_runs(job_id="lots-of-runs", limit=-5)
        assert len(rows) == 1


# ── API tests ──────────────────────────────────────────────────────────────


class TestApiReadsFromDuckDB:
    """``GET /api/crons/<jobId>/runs`` prefers DuckDB, falls back to JSONL."""

    def test_endpoint_reads_from_duckdb_when_populated(self, isolated):
        sync = isolated["sync"]
        cr = isolated["cr"]
        runs_dir = isolated["runs_dir"]
        # Populate DuckDB via the ingest helper (no JSONL needed for this
        # assertion — the route mustn't depend on the file when the store
        # has rows).
        records = [
            {"id": f"d-{i}",
             "started_at": f"2026-05-13T16:00:0{i}Z",
             "duration_ms": 500 + i,
             "status": "ok"}
            for i in range(3)
        ]
        _write_jsonl(runs_dir, "duckdb-job", records)
        n = sync.sync_cron_runs({"node_id": "test"},
                                 {"cron_run_offsets": {}}, paths={})
        assert n == 3

        app = _build_app(cr)
        client = app.test_client()
        resp = client.get("/api/crons/duckdb-job/runs?limit=10")
        assert resp.status_code == 200
        body = resp.get_json()
        assert body["jobId"] == "duckdb-job"
        assert body["source"] == "duckdb"
        assert body["count"] == 3
        assert len(body["runs"]) == 3
        # Most-recent first.
        assert body["runs"][0]["duration_ms"] == 502

    def test_endpoint_falls_back_to_jsonl_when_duckdb_empty(self, isolated):
        """If the daemon hasn't ingested yet, the JSONL parser keeps the
        UI working. This is the graceful-migration path called out in the
        task spec."""
        cr = isolated["cr"]
        runs_dir = isolated["runs_dir"]
        _write_jsonl(runs_dir, "fresh-job", [
            {"id": "fresh-0", "started_at": "2026-05-13T17:00:00Z",
             "duration_ms": 999, "status": "ok"}
        ])
        # Don't run sync_cron_runs — DuckDB is empty for this job.

        app = _build_app(cr)
        client = app.test_client()
        resp = client.get("/api/crons/fresh-job/runs")
        assert resp.status_code == 200
        body = resp.get_json()
        assert body["source"] == "jsonl"
        assert body["count"] == 1
        assert body["runs"][0]["duration_ms"] == 999

    def test_endpoint_returns_empty_when_both_paths_empty(self, isolated):
        cr = isolated["cr"]
        app = _build_app(cr)
        client = app.test_client()
        resp = client.get("/api/crons/nonexistent/runs")
        assert resp.status_code == 200
        body = resp.get_json()
        assert body["runs"] == []
        assert body["count"] == 0

    def test_endpoint_rejects_path_traversal(self, isolated):
        cr = isolated["cr"]
        app = _build_app(cr)
        client = app.test_client()
        # Flask's URL router blocks bare ``/`` and percent-encoded ``/``
        # before our handler runs (they hit a 404). The traversal we DO
        # have to defend against is a literal ``..`` segment inside the
        # job_id capture, e.g. a request to ``/api/crons/..evil/runs``.
        # The handler must refuse it and return an empty payload — never
        # 500, never touch the filesystem.
        resp = client.get("/api/crons/..evil/runs")
        assert resp.status_code == 200
        body = resp.get_json()
        assert body["runs"] == []
        assert body["file"] is None
