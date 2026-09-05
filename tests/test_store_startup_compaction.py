"""#5498 — startup compaction of a mostly-dead DuckDB file.

DuckDB never shrinks its file and only merges row groups that are about
25% deleted, so the dead row versions left by rewrites accumulate for the
life of the file (a real node: 1,634 MB on disk, 575 MB after a rewrite).
The writer now measures dead space once at startup, before it opens the
connection it keeps, and rewrites the file with ``COPY FROM DATABASE`` when
the file is mostly dead, keeping the previous file beside it for a week.
"""
from __future__ import annotations

import importlib
import os
import time

import duckdb
import pytest


def _fresh(tmp_path, monkeypatch, name="compact.duckdb", **env):
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / name))
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_SECS", "999")
    for k in ("CLAWMETRY_AUTO_COMPACT", "CLAWMETRY_AUTO_COMPACT_MIN_BYTES",
              "CLAWMETRY_AUTO_COMPACT_MIN_DEAD_PCT"):
        monkeypatch.delenv(k, raising=False)
    for k, v in env.items():
        monkeypatch.setenv(k, v)
    import clawmetry.local_store as ls
    importlib.reload(ls)
    return ls


def _span(i: int, rev: int = 0):
    return {
        "span_id": f"sp-{i:05d}", "trace_id": "t", "name": "tool.call",
        "start_ts": 1000.0 + i, "end_ts": 1001.0 + i, "agent_type": "claude_code",
        "session_id": "s1", "attributes": {"rev": rev, "pad": "x" * 200},
    }


def _bloat(ls, n_spans=1000, rewrites=10):
    """Rewrite the same spans many times: each pass is DELETE+INSERT."""
    s = ls.LocalStore()
    try:
        for rev in range(rewrites):
            s.ingest_spans_batch([_span(i, rev) for i in range(n_spans)])
        with s._write_lock:
            s._conn.execute("CHECKPOINT")
            m = ls.measure_dead_space(s._conn)
    finally:
        s.stop(flush=True)
    return m


def test_measure_dead_space_sees_rewrite_versions(tmp_path, monkeypatch):
    ls = _fresh(tmp_path, monkeypatch, CLAWMETRY_AUTO_COMPACT="0")
    m = _bloat(ls)
    assert m["live_rows"] >= 1000
    assert m["dead_rows"] > m["live_rows"], m
    assert m["dead_pct"] >= 0.40, m


def test_startup_compacts_a_mostly_dead_file(tmp_path, monkeypatch):
    ls = _fresh(tmp_path, monkeypatch, CLAWMETRY_AUTO_COMPACT="0")
    _bloat(ls)
    db = tmp_path / "compact.duckdb"
    before = db.stat().st_size
    ls2 = _fresh(tmp_path, monkeypatch, CLAWMETRY_AUTO_COMPACT_MIN_BYTES="0")
    s = ls2.LocalStore()
    try:
        last = s.health()["last_compaction"]
        assert last["ran"] is True, last
        assert last["after_bytes"] <= before
        assert s._conn.execute("SELECT COUNT(*) FROM spans").fetchone()[0] == 1000
        assert s._conn.execute(
            "SELECT attributes FROM spans WHERE span_id = 'sp-00007'"
        ).fetchone()[0] is not None
        with s._write_lock:
            m = ls2.measure_dead_space(s._conn)
        assert m["dead_rows"] == 0, m
        assert (tmp_path / "compact.duckdb.pre-compact").stat().st_size == pytest.approx(before, rel=0.05)
        assert not (tmp_path / "compact.duckdb.compacting").exists()
        # The store keeps working as a writer after the swap.
        assert s.ingest_spans_batch([_span(99999)]) == 1
    finally:
        s.stop(flush=True)


def test_healthy_or_small_files_are_left_alone(tmp_path, monkeypatch):
    ls = _fresh(tmp_path, monkeypatch)
    s = ls.LocalStore()
    try:
        s.ingest_spans_batch([_span(i) for i in range(50)])
    finally:
        s.stop(flush=True)
    db = tmp_path / "compact.duckdb"
    ls2 = _fresh(tmp_path, monkeypatch)  # default 64 MB floor
    s = ls2.LocalStore()
    try:
        last = s.health()["last_compaction"]
        assert last["ran"] is False and last["reason"] == "small"
    finally:
        s.stop(flush=True)
    ls3 = _fresh(tmp_path, monkeypatch, CLAWMETRY_AUTO_COMPACT_MIN_BYTES="0")
    s = ls3.LocalStore()
    try:
        last = s.health()["last_compaction"]
        assert last["ran"] is False and last["reason"] == "healthy", last
        assert not (tmp_path / "compact.duckdb.pre-compact").exists()
    finally:
        s.stop(flush=True)
    assert db.exists()


def test_kill_switch_skips_the_check(tmp_path, monkeypatch):
    ls = _fresh(tmp_path, monkeypatch, CLAWMETRY_AUTO_COMPACT="0")
    _bloat(ls, n_spans=300, rewrites=6)
    ls2 = _fresh(tmp_path, monkeypatch, CLAWMETRY_AUTO_COMPACT="0",
                 CLAWMETRY_AUTO_COMPACT_MIN_BYTES="0")
    s = ls2.LocalStore()
    try:
        assert s.health()["last_compaction"] == {}
    finally:
        s.stop(flush=True)


def test_locked_file_is_not_touched(tmp_path, monkeypatch):
    ls = _fresh(tmp_path, monkeypatch, CLAWMETRY_AUTO_COMPACT="0")
    _bloat(ls, n_spans=300, rewrites=6)
    db = tmp_path / "compact.duckdb"
    holder = duckdb.connect(str(db))
    try:
        out = ls.compact_store_file(db, force=True)
    finally:
        holder.close()
    assert out["ran"] is False and out["reason"].startswith("locked"), out
    assert not (tmp_path / "compact.duckdb.pre-compact").exists()


def test_old_backup_is_pruned_on_startup(tmp_path, monkeypatch):
    ls = _fresh(tmp_path, monkeypatch)
    bak = tmp_path / "compact.duckdb.pre-compact"
    bak.write_bytes(b"old")
    old = time.time() - 8 * 86400
    os.utime(bak, (old, old))
    fresh = tmp_path / "compact.duckdb.pre-compact"
    s = ls.LocalStore()
    try:
        assert not fresh.exists()
    finally:
        s.stop(flush=True)
    # A young backup survives.
    bak.write_bytes(b"new")
    ls2 = _fresh(tmp_path, monkeypatch)
    s = ls2.LocalStore()
    try:
        assert bak.exists()
    finally:
        s.stop(flush=True)


def test_row_count_mismatch_aborts_and_keeps_original(tmp_path, monkeypatch):
    ls = _fresh(tmp_path, monkeypatch, CLAWMETRY_AUTO_COMPACT="0")
    _bloat(ls, n_spans=300, rewrites=6)
    db = tmp_path / "compact.duckdb"
    real_execute = duckdb.DuckDBPyConnection.execute

    def sabotage(self, sql, *a, **k):
        if isinstance(sql, str) and sql.startswith('SELECT COUNT(*) FROM _compact_target."spans"'):
            return real_execute(self, "SELECT 0", *a, **k)
        return real_execute(self, sql, *a, **k)

    monkeypatch.setattr(duckdb.DuckDBPyConnection, "execute", sabotage)
    out = ls.compact_store_file(db, force=True)
    monkeypatch.undo()
    assert out["ran"] is False and "mismatch" in out["reason"], out
    assert db.exists() and not (tmp_path / "compact.duckdb.pre-compact").exists()
    assert not (tmp_path / "compact.duckdb.compacting").exists()


# ── the rewrite runs in a helper process; a crash there cannot brick the daemon ──

def test_startup_compaction_runs_in_a_child_and_reports(tmp_path, monkeypatch):
    ls = _fresh(tmp_path, monkeypatch, CLAWMETRY_AUTO_COMPACT="0")
    _bloat(ls, n_spans=600, rewrites=8)
    ls2 = _fresh(tmp_path, monkeypatch, CLAWMETRY_AUTO_COMPACT_MIN_BYTES="0")
    seen = {}
    real_run = ls2.subprocess.run

    def spy(cmd, **kw):
        seen["cmd"] = cmd
        return real_run(cmd, **kw)

    monkeypatch.setattr(ls2.subprocess, "run", spy)
    s = ls2.LocalStore()
    try:
        last = s.health()["last_compaction"]
        assert last["ran"] is True, last
        assert seen["cmd"][0] == ls2.sys.executable and "-c" in seen["cmd"]
        assert s._conn.execute("SELECT COUNT(*) FROM spans").fetchone()[0] == 600
    finally:
        s.stop(flush=True)


def test_helper_crash_mid_swap_restores_the_store(tmp_path, monkeypatch):
    ls = _fresh(tmp_path, monkeypatch, CLAWMETRY_AUTO_COMPACT="0")
    _bloat(ls, n_spans=300, rewrites=4)
    db = tmp_path / "compact.duckdb"
    size = db.stat().st_size
    ls2 = _fresh(tmp_path, monkeypatch, CLAWMETRY_AUTO_COMPACT_MIN_BYTES="0")

    def crash(cmd, **kw):
        # Simulate a native crash after the first rename of the swap.
        os.replace(db, tmp_path / "compact.duckdb.pre-compact")
        (tmp_path / "compact.duckdb.compacting").write_bytes(b"partial")
        return ls2.subprocess.CompletedProcess(cmd, -11, stdout="", stderr="Segmentation fault")

    monkeypatch.setattr(ls2.subprocess, "run", crash)
    s = ls2.LocalStore()
    try:
        last = s.health()["last_compaction"]
        assert last["ran"] is False and "exited -11" in last["reason"], last
        assert db.exists() and db.stat().st_size == size
        assert not (tmp_path / "compact.duckdb.compacting").exists()
        assert s._conn.execute("SELECT COUNT(*) FROM spans").fetchone()[0] == 300
    finally:
        s.stop(flush=True)


def test_helper_timeout_is_reported_and_store_kept(tmp_path, monkeypatch):
    ls = _fresh(tmp_path, monkeypatch, CLAWMETRY_AUTO_COMPACT="0")
    _bloat(ls, n_spans=200, rewrites=3)
    db = tmp_path / "compact.duckdb"
    ls2 = _fresh(tmp_path, monkeypatch, CLAWMETRY_AUTO_COMPACT_MIN_BYTES="0")

    def hang(cmd, **kw):
        raise ls2.subprocess.TimeoutExpired(cmd, kw.get("timeout", 0))

    monkeypatch.setattr(ls2.subprocess, "run", hang)
    s = ls2.LocalStore()
    try:
        last = s.health()["last_compaction"]
        assert last["ran"] is False and "timed out" in last["reason"], last
        assert db.exists()
    finally:
        s.stop(flush=True)
