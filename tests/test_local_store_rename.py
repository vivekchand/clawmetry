"""Tests for the events.duckdb → clawmetry.duckdb rename + auto-migration.

These run against the real default path mechanism (no
CLAWMETRY_LOCAL_STORE_PATH env var) by monkeypatching the module-level
constants — the migration intentionally bails out when the env var is
set, so we can't isolate via tmp_path the way other tests do.
"""

from __future__ import annotations

import importlib
from pathlib import Path

import duckdb
import pytest


def _reload_local_store(monkeypatch, tmp_path, env_override=False):
    """Reload local_store with DB_PATH and LEGACY_DB_PATH pointed at tmp.
    By default removes CLAWMETRY_LOCAL_STORE_PATH so the migration runs."""
    if env_override:
        monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH",
                           str(tmp_path / "custom.duckdb"))
    else:
        monkeypatch.delenv("CLAWMETRY_LOCAL_STORE_PATH", raising=False)
    import clawmetry.local_store as ls
    importlib.reload(ls)
    # Override the module-level paths to live in tmp_path so we don't
    # touch the user's real ~/.clawmetry/.
    monkeypatch.setattr(ls, "DB_PATH", tmp_path / "clawmetry.duckdb")
    monkeypatch.setattr(ls, "LEGACY_DB_PATH", tmp_path / "events.duckdb")
    return ls


def _seed_legacy_file(path: Path):
    """Write a minimal valid DuckDB file at the legacy location with one row
    so the migration is observably moving real data, not just an empty file."""
    with duckdb.connect(str(path)) as c:
        c.execute("CREATE TABLE marker (token VARCHAR)")
        c.execute("INSERT INTO marker VALUES ('legacy-file-was-here')")


def test_migration_renames_legacy_file_when_new_absent(tmp_path, monkeypatch):
    legacy = tmp_path / "events.duckdb"
    new = tmp_path / "clawmetry.duckdb"
    _seed_legacy_file(legacy)
    assert legacy.exists()
    assert not new.exists()

    ls = _reload_local_store(monkeypatch, tmp_path)
    ls._migrate_legacy_db_path()

    # Legacy file moved to the new name.
    assert not legacy.exists(), "legacy events.duckdb should be gone"
    assert new.exists(), "clawmetry.duckdb should exist"

    # Data preserved.
    with duckdb.connect(str(new)) as c:
        rows = c.execute("SELECT token FROM marker").fetchall()
    assert rows == [("legacy-file-was-here",)]


def test_migration_skips_when_env_overrides_path(tmp_path, monkeypatch):
    """If CLAWMETRY_LOCAL_STORE_PATH is set, the user has chosen a custom
    path (e.g. test fixture). Don't surprise them by renaming files at
    the default location."""
    legacy = tmp_path / "events.duckdb"
    _seed_legacy_file(legacy)

    ls = _reload_local_store(monkeypatch, tmp_path, env_override=True)
    ls._migrate_legacy_db_path()

    # Legacy file untouched.
    assert legacy.exists()


def test_migration_keeps_new_when_both_exist(tmp_path, monkeypatch):
    """Both files present (e.g. user hand-copied). Keep the new one;
    don't clobber. Legacy stays for manual recovery."""
    legacy = tmp_path / "events.duckdb"
    new = tmp_path / "clawmetry.duckdb"
    _seed_legacy_file(legacy)
    # Seed new with different marker so we can tell them apart.
    with duckdb.connect(str(new)) as c:
        c.execute("CREATE TABLE marker (token VARCHAR)")
        c.execute("INSERT INTO marker VALUES ('new-file-already-existed')")

    ls = _reload_local_store(monkeypatch, tmp_path)
    ls._migrate_legacy_db_path()

    # Both still exist.
    assert legacy.exists()
    assert new.exists()
    # New file unchanged.
    with duckdb.connect(str(new)) as c:
        rows = c.execute("SELECT token FROM marker").fetchall()
    assert rows == [("new-file-already-existed",)]


def test_migration_noop_when_neither_exists(tmp_path, monkeypatch):
    """Fresh install — nothing to migrate. Must not crash."""
    ls = _reload_local_store(monkeypatch, tmp_path)
    ls._migrate_legacy_db_path()
    assert not (tmp_path / "events.duckdb").exists()
    assert not (tmp_path / "clawmetry.duckdb").exists()


def test_migration_moves_wal_alongside_db(tmp_path, monkeypatch):
    """DuckDB writes a sibling .wal file. Migration must move both
    so the next open recovers cleanly instead of seeing an orphaned WAL."""
    legacy = tmp_path / "events.duckdb"
    legacy_wal = tmp_path / "events.duckdb.wal"
    _seed_legacy_file(legacy)
    legacy_wal.write_bytes(b"fake wal content")

    ls = _reload_local_store(monkeypatch, tmp_path)
    ls._migrate_legacy_db_path()

    assert not legacy.exists()
    assert not legacy_wal.exists()
    assert (tmp_path / "clawmetry.duckdb").exists()
    assert (tmp_path / "clawmetry.duckdb.wal").exists()
    assert (tmp_path / "clawmetry.duckdb.wal").read_bytes() == b"fake wal content"


def test_default_db_path_is_clawmetry_duckdb(monkeypatch):
    """Smoke: with no env override, DB_PATH defaults to ~/.clawmetry/clawmetry.duckdb,
    not events.duckdb. Locks the rename in."""
    monkeypatch.delenv("CLAWMETRY_LOCAL_STORE_PATH", raising=False)
    import clawmetry.local_store as ls
    importlib.reload(ls)
    assert ls.DB_PATH.name == "clawmetry.duckdb"
    assert ls.LEGACY_DB_PATH.name == "events.duckdb"
