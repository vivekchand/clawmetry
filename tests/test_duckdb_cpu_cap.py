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


def test_default_caps_threads_and_memory(monkeypatch, tmp_path):
    monkeypatch.delenv("CLAWMETRY_DUCKDB_THREADS", raising=False)
    monkeypatch.delenv("CLAWMETRY_DUCKDB_MEMORY_LIMIT", raising=False)
    ls = _reload_store()
    # A small (or absent) store sits on the 2GB floor, the value the cap
    # was tuned against for years.
    ls.DB_PATH = tmp_path / "small.duckdb"
    ls._oom_bumps = 0
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


# ── the ceiling follows the store (2026-09-02) ──────────────────────────────
#
# A flat 2GB ceiling overflowed on a 4.2 GB store (query_aggregates full-table
# dedupe), the rollback ran out too, and DuckDB invalidated the handle: two
# hours of 500s from a daemon that looked healthy. The ceiling is now derived:
# 1.5x the file, floored at 2GB, capped at half of RAM, one notch up per OOM.

GB = 1024 ** 3


def test_small_store_sits_on_the_floor():
    ls = _reload_store()
    assert ls._duckdb_memory_limit_bytes(100 * 1024 ** 2, 32 * GB, 0) == 2 * GB


def test_big_store_gets_one_and_a_half_times_its_size():
    ls = _reload_store()
    assert ls._duckdb_memory_limit_bytes(4 * GB, 32 * GB, 0) == 6 * GB


def test_the_ceiling_never_exceeds_half_of_ram():
    ls = _reload_store()
    assert ls._duckdb_memory_limit_bytes(40 * GB, 16 * GB, 0) == 8 * GB


def test_a_small_box_still_gets_the_floor():
    """Below 4 GB of RAM half-of-RAM would undercut the floor the store was
    tuned against; the floor wins (it is a ceiling, not a reservation)."""
    ls = _reload_store()
    assert ls._duckdb_memory_limit_bytes(1 * GB, 3 * GB, 0) == 2 * GB


def test_each_oom_raises_the_ceiling_one_notch():
    ls = _reload_store()
    assert ls._duckdb_memory_limit_bytes(4 * GB, 64 * GB, 1) == 9 * GB
    assert ls._duckdb_memory_limit_bytes(4 * GB, 64 * GB, 2) == int(13.5 * GB)


def test_unknown_ram_means_no_cap():
    ls = _reload_store()
    assert ls._duckdb_memory_limit_bytes(4 * GB, None, 0) == 6 * GB


def test_env_override_wins_over_the_derived_ceiling(monkeypatch, tmp_path):
    monkeypatch.setenv("CLAWMETRY_DUCKDB_MEMORY_LIMIT", "512MB")
    ls = _reload_store()
    assert ls._duckdb_runtime_config()["memory_limit"] == "512MB"


def test_blank_env_means_duckdb_default(monkeypatch):
    monkeypatch.setenv("CLAWMETRY_DUCKDB_MEMORY_LIMIT", "")
    ls = _reload_store()
    assert "memory_limit" not in ls._duckdb_runtime_config()


def test_the_setting_is_rendered_in_duckdb_units():
    ls = _reload_store()
    assert ls._format_duckdb_bytes(2 * GB) == "2GB"
    assert ls._format_duckdb_bytes(6 * GB) == "6GB"
    assert ls._format_duckdb_bytes(int(13.5 * GB)) == "13824MB"


def test_the_derived_ceiling_reads_the_real_file(monkeypatch, tmp_path):
    """End to end: a store file of a known size produces the matching
    connection config, and DuckDB accepts it."""
    monkeypatch.delenv("CLAWMETRY_DUCKDB_MEMORY_LIMIT", raising=False)
    import duckdb
    ls = _reload_store()
    ls._oom_bumps = 0
    ls.DB_PATH = tmp_path / "grown.duckdb"
    ls.DB_PATH.write_bytes(b"\0" * (3 * GB // 1024))   # 3 MB: on the floor
    monkeypatch.setattr(ls, "_physical_ram_bytes", lambda: 64 * GB)
    assert ls._duckdb_runtime_config()["memory_limit"] == "2GB"
    monkeypatch.setattr(ls, "_on_disk_bytes", lambda: 4 * GB)
    cfg = ls._duckdb_runtime_config()
    assert cfg["memory_limit"] == "6GB"
    con = duckdb.connect(str(tmp_path / "t.duckdb"), config=cfg)
    assert con.execute("SELECT current_setting('memory_limit')").fetchone()[0] == "5.5 GiB"


def test_physical_ram_is_known_on_this_platform():
    ls = _reload_store()
    ram = ls._physical_ram_bytes()
    assert ram is None or ram > 256 * 1024 ** 2
