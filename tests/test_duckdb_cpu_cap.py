"""DuckDB must not fan out across every core — ClawMetry is a light sidecar.

Regression guard for the CPU-budget principle (FLYWHEEL.md): _open_connection
caps DuckDB threads + memory_limit so a single aggregate query can't peg the
whole machine (observed: a 12-core box at ~200% CPU re-running query_aggregates).
"""
import os
import importlib


def _reload_store():
    import clawmetry.local_store as ls
    return importlib.reload(ls)


def test_default_caps_threads_and_memory(monkeypatch):
    monkeypatch.delenv("CLAWMETRY_DUCKDB_THREADS", raising=False)
    monkeypatch.delenv("CLAWMETRY_DUCKDB_MEMORY_LIMIT", raising=False)
    ls = _reload_store()
    cfg = ls._duckdb_runtime_config()
    assert cfg["threads"] == 2, cfg
    assert cfg["memory_limit"] == "2GB", cfg


def test_env_override_threads(monkeypatch):
    monkeypatch.setenv("CLAWMETRY_DUCKDB_THREADS", "1")
    ls = _reload_store()
    assert ls._duckdb_runtime_config()["threads"] == 1


def test_zero_threads_means_duckdb_default(monkeypatch):
    monkeypatch.setenv("CLAWMETRY_DUCKDB_THREADS", "0")
    ls = _reload_store()
    assert "threads" not in ls._duckdb_runtime_config()


def test_applied_to_real_connection(tmp_path, monkeypatch):
    monkeypatch.delenv("CLAWMETRY_DUCKDB_THREADS", raising=False)
    import duckdb
    ls = _reload_store()
    con = duckdb.connect(str(tmp_path / "t.duckdb"), config=ls._duckdb_runtime_config())
    assert con.execute("SELECT current_setting('threads')").fetchone()[0] == 2
