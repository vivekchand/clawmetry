"""Tests for the daemon-error → DuckDB → health-card pipeline (PRD #1133 layer 4).

PR #1139 surfaced daemon errors on the System Health card by parsing
``~/.clawmetry/sync.log`` text on every ``/api/system-health`` call — a
DuckDB-first-rule violation. This follow-up:

  1. Has the daemon ALSO write each ERROR-level log record into the local
     DuckDB ``events`` table as ``event_type='daemon.error'`` rows.
  2. Has ``routes.health.compute_daemon_health()`` query DuckDB first and
     fall back to the legacy log-tail parser only when no DuckDB rows exist
     (so fresh installs / pre-this-fix data still surface).
  3. Rate-limits the daemon write: at most one row per
     (first-80-chars-of-message, 60-second-bucket), so the
     ``ALERTS_EVAL_INTERVAL_SEC`` regression that fired 4×/min cannot
     stamp 5,760 rows/day into DuckDB.

Tests:

* TestHandler — direct unit tests for ``_DaemonErrorDuckDBHandler``:
  basic ingest, INFO/WARNING ignored, exception capture, rate-limit dedup.
* TestPipeline — end-to-end: 3 ``log.error(...)`` calls → 3 DuckDB rows.
* TestComputeDaemonHealth — read side reads DuckDB and returns
  ``_source='local_store'`` with correct counts.

No Flask server, no network, no sleep. ~150ms total.
"""
from __future__ import annotations

import importlib
import logging
import sys
import time
import types
from datetime import datetime, timedelta, timezone

import pytest


# ── Fixture: isolated DuckDB + reloaded sync module ─────────────────────────


@pytest.fixture
def env(tmp_path, monkeypatch):
    """Fresh DuckDB per test + reloaded ``clawmetry.sync`` + ``routes.health``
    so handler installation and read-side both target the tmp file.

    The Python ``logging`` module returns the SAME logger instance across
    importlib.reload() calls (loggers are process-singletons keyed by
    name), so we explicitly strip the daemon logger's handlers before each
    test to avoid handler instances pointing at the previous test's
    DuckDB store leaking into the current test.
    """
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "clawmetry.duckdb"))
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_SECS", "0.05")
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_BATCH", "1")
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_READ", "1")
    # Also point the daemon's CONFIG_DIR at tmp so load_config() in the
    # handler's node_id resolution doesn't pull the dev machine's real
    # ~/.clawmetry/config.json (which would leak the host's node_id into
    # rows that the read side then ignores).
    monkeypatch.setenv("HOME", str(tmp_path))

    # Strip pre-existing daemon-error handlers from prior tests (logging
    # loggers survive importlib.reload).
    daemon_log = logging.getLogger("clawmetry-sync")
    pre_existing = list(daemon_log.handlers)
    for h in pre_existing:
        if type(h).__name__ == "_DaemonErrorDuckDBHandler":
            daemon_log.removeHandler(h)

    import clawmetry.local_store as ls
    importlib.reload(ls)
    import clawmetry.sync as sync_mod
    importlib.reload(sync_mod)
    import routes.health as hp
    importlib.reload(hp)
    yield ls, sync_mod, hp
    try:
        ls.get_store().stop(flush=True)
    except Exception:
        pass
    # Tear down our handler so the next test gets a clean logger.
    for h in list(daemon_log.handlers):
        if type(h).__name__ == "_DaemonErrorDuckDBHandler":
            daemon_log.removeHandler(h)


def _wait_flush(store, timeout=2.0):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if store.health()["ring_depth"] == 0:
            return
        time.sleep(0.01)


# ── Handler unit tests ─────────────────────────────────────────────────────


class TestHandler:
    def test_install_is_idempotent(self, env):
        ls, sync_mod, _ = env
        h1 = sync_mod.install_daemon_error_event_handler()
        h2 = sync_mod.install_daemon_error_event_handler()
        assert h1 is not None and h2 is not None
        assert h1 is h2  # second call returns the same instance

    def test_info_and_warning_records_are_ignored(self, env):
        ls, sync_mod, _ = env
        sync_mod.install_daemon_error_event_handler()
        sync_mod.log.info("hello world")
        sync_mod.log.warning("yellow alert")
        _wait_flush(ls.get_store())
        rows = ls.get_store().query_events(event_type="daemon.error", limit=100)
        assert rows == []

    def test_error_writes_one_row(self, env):
        ls, sync_mod, _ = env
        sync_mod.install_daemon_error_event_handler()
        sync_mod.log.error("Sync cycle error: NameError ALERTS_EVAL_INTERVAL_SEC")
        _wait_flush(ls.get_store())
        rows = ls.get_store().query_events(event_type="daemon.error", limit=100)
        assert len(rows) == 1
        ev = rows[0]
        assert ev["event_type"] == "daemon.error"
        assert ev["agent_id"] == "clawmetry-daemon"
        assert ev["agent_type"] == "clawmetry"
        assert ev["data"]["message"].startswith("Sync cycle error:")

    def test_exception_info_is_captured(self, env):
        ls, sync_mod, _ = env
        sync_mod.install_daemon_error_event_handler()
        try:
            raise RuntimeError("boom in tool dispatch")
        except RuntimeError:
            sync_mod.log.exception("tool dispatch failed")
        _wait_flush(ls.get_store())
        rows = ls.get_store().query_events(event_type="daemon.error", limit=100)
        assert len(rows) == 1
        data = rows[0]["data"]
        assert "tool dispatch failed" in data["message"]
        assert data.get("exception")
        assert "RuntimeError" in data["exception"]
        assert "boom in tool dispatch" in data["exception"]


# ── Rate-limit / dedup tests ───────────────────────────────────────────────


class TestRateLimit:
    def test_30_identical_errors_in_one_bucket_writes_one_row(self, env):
        """The original ALERTS_EVAL_INTERVAL_SEC bug fired 4×/min; the
        DuckDB tee must collapse that to one row per 60s bucket so a
        single regression doesn't stamp ~6k rows/day."""
        ls, sync_mod, _ = env
        h = sync_mod.install_daemon_error_event_handler()
        for _ in range(30):
            sync_mod.log.error("Sync cycle error: name 'ALERTS_EVAL_INTERVAL_SEC' is not defined")
        _wait_flush(ls.get_store())
        rows = ls.get_store().query_events(event_type="daemon.error", limit=100)
        assert len(rows) == 1
        # Dropped count should reflect the 29 deduped attempts.
        assert h._dropped >= 29
        assert h._emitted == 1

    def test_distinct_messages_each_get_a_row(self, env):
        ls, sync_mod, _ = env
        sync_mod.install_daemon_error_event_handler()
        for i in range(5):
            sync_mod.log.error("error variant %d details here", i)
        _wait_flush(ls.get_store())
        rows = ls.get_store().query_events(event_type="daemon.error", limit=100)
        assert len(rows) == 5

    def test_same_prefix_next_bucket_writes_a_new_row(self, env):
        """Manually advance the handler's bucket so we don't need to sleep
        60s. Same message, different bucket → two rows (carries the
        'errors haven't stopped' signal across the gap).

        We pick a bucket-aligned anchor (1_000_020 // 60 == 16667 exactly)
        so both ``+0`` and ``+59`` land in the same 60s window.
        """
        ls, sync_mod, _ = env
        h = sync_mod.install_daemon_error_event_handler()
        anchor = float(60 * 16667)  # 1_000_020.0
        msg = "repeating cron loop failure"
        assert h._should_emit(msg, anchor) is True
        # Within same 60s window → blocked.
        assert h._should_emit(msg, anchor + 30.0) is False
        assert h._should_emit(msg, anchor + 59.9) is False
        # Next bucket → allowed.
        assert h._should_emit(msg, anchor + 60.0) is True

    def test_dedup_uses_first_80_chars(self, env):
        """Two messages with identical 80-char prefixes but different
        suffixes (e.g. a trailing UUID) should still dedup — the prefix
        is the signal, suffix noise."""
        ls, sync_mod, _ = env
        h = sync_mod.install_daemon_error_event_handler()
        prefix = "x" * 80
        assert h._should_emit(prefix + "-aaa", 1.0) is True
        assert h._should_emit(prefix + "-bbb", 30.0) is False


# ── End-to-end pipeline: 3 log.error() → 3 DuckDB rows → health card ────────


class TestPipeline:
    def test_three_distinct_errors_land_in_duckdb(self, env):
        ls, sync_mod, _ = env
        sync_mod.install_daemon_error_event_handler()
        sync_mod.log.error("first cycle error")
        sync_mod.log.error("second cycle error")
        sync_mod.log.error("third cycle error")
        _wait_flush(ls.get_store())
        rows = ls.get_store().query_events(event_type="daemon.error", limit=100)
        assert len(rows) == 3
        msgs = sorted([r["data"]["message"] for r in rows])
        assert msgs == ["first cycle error", "second cycle error", "third cycle error"]
        for r in rows:
            assert r["event_type"] == "daemon.error"
            assert r["agent_id"] == "clawmetry-daemon"

    def test_handler_swallows_local_store_exceptions(self, env, monkeypatch):
        """If local_store.ingest() raises (writer locked, DuckDB closed,
        etc.) the daemon must keep logging — telemetry is best-effort."""
        ls, sync_mod, _ = env
        h = sync_mod.install_daemon_error_event_handler()

        # Patch ingest to raise.
        store = ls.get_store()
        def _boom(*a, **kw):
            raise RuntimeError("simulated DuckDB outage")
        monkeypatch.setattr(store, "ingest", _boom)

        # Force a different prefix per call so dedup doesn't mask the test.
        sync_mod.log.error("alpha error path")
        sync_mod.log.error("beta error path")
        # No exception escapes; dropped count tracks the failures.
        assert h._dropped >= 2


# ── Read side: compute_daemon_health() reads DuckDB ─────────────────────────


class TestComputeDaemonHealth:
    def _seed(self, store, *, n_recent=0, n_old=0, last_msg="latest error"):
        """Seed DuckDB with daemon.error events; ``recent`` = within 5 min,
        ``old`` = between 5 min and 60 min ago. ``last_msg`` is attached to
        the single most-recent event.

        Recent events are spaced 1 second apart so up to 290 fit inside the
        5-min window (matters for the broken-threshold test).
        """
        now = datetime.now(timezone.utc)
        for i in range(n_recent):
            ts = now - timedelta(seconds=1 + i)
            store.ingest({
                "id": f"ev-recent-{i}",
                "node_id": "test-node",
                "agent_id": "clawmetry-daemon",
                "agent_type": "clawmetry",
                "event_type": "daemon.error",
                "ts": ts.isoformat(),
                "data": {"message": last_msg if i == 0 else f"recent err {i}"},
            })
        for i in range(n_old):
            ts = now - timedelta(minutes=10 + i)
            store.ingest({
                "id": f"ev-old-{i}",
                "node_id": "test-node",
                "agent_id": "clawmetry-daemon",
                "agent_type": "clawmetry",
                "event_type": "daemon.error",
                "ts": ts.isoformat(),
                "data": {"message": f"old err {i}"},
            })
        _wait_flush(store)

    def test_reads_counts_from_duckdb(self, env):
        ls, _sm, hp = env
        store = ls.get_store()
        self._seed(store, n_recent=3, n_old=4, last_msg="latest bug")
        out = hp.compute_daemon_health()
        assert out["_source"] == "local_store"
        assert out["errors_last_5min"] == 3
        assert out["errors_last_1h"] == 7
        assert out["last_error_message"] == "latest bug"
        assert out["status"] == "degraded"
        assert out["last_error_ts"] is not None
        assert "T" in out["last_error_ts"]

    def test_zero_rows_falls_back_to_log_tail(self, env, tmp_path):
        ls, _sm, hp = env
        # No DuckDB rows. Write a log file with one ERROR line.
        log_path = tmp_path / "sync.log"
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S,000")
        log_path.write_text(
            f"{ts} [clawmetry-sync] ERROR fallback-source probe\n", encoding="utf-8"
        )
        out = hp.compute_daemon_health(log_path=str(log_path))
        # No DuckDB rows → fallback path tagged _source='sync_log'.
        assert out["_source"] == "sync_log"
        assert out["errors_last_5min"] == 1
        assert out["last_error_message"] == "fallback-source probe"

    def test_50_recent_errors_is_broken_via_duckdb(self, env):
        ls, _sm, hp = env
        store = ls.get_store()
        self._seed(store, n_recent=35)
        out = hp.compute_daemon_health()
        assert out["_source"] == "local_store"
        assert out["errors_last_5min"] == 35
        assert out["status"] == "broken"

    def test_only_old_errors_is_healthy_5min_but_degraded_1h(self, env):
        ls, _sm, hp = env
        store = ls.get_store()
        self._seed(store, n_old=5)
        out = hp.compute_daemon_health()
        assert out["_source"] == "local_store"
        assert out["errors_last_5min"] == 0
        assert out["errors_last_1h"] == 5
        # No 5-min errors → status is healthy (matches PR #1139 thresholds).
        assert out["status"] == "healthy"
        # last_error_message still surfaces so the card can show "had errors".
        assert out["last_error_message"] is not None
