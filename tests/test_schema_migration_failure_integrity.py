"""Regression tests for schema-migration failure-mode integrity (#1602).

Bug class: the migration runner stamped ``schema_version`` even when the
gated migration body itself raised. On the next boot the version gate
("current < 7") was False, the migration was skipped, and the store
quietly ran on a half-migrated schema.

These tests assert the opposite contract:

  1. If a gated migration raises, the version row is NOT stamped.
  2. The first ``LocalStore()`` constructor that hits the failure raises
     (loudly — daemons see it in logs and CI catches it).
  3. The DuckDB file is left in a clean state — a subsequent boot, with
     the failure mode removed, completes the migration and stamps the
     version exactly as if the failure had never occurred.

We simulate the failure by monkey-patching ``_run_dedup_migration_v7``
to raise. That's the only currently-gated migration; if future bumps
add more we extend the same pattern.
"""

from __future__ import annotations

import importlib
import os

import pytest


@pytest.fixture
def fresh_store_env(tmp_path, monkeypatch):
    """Isolated DuckDB path + tight flusher, but DON'T construct the
    store — these tests instantiate it themselves so they can observe
    the migration phase."""
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "events.duckdb"))
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_SECS", "0.05")
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_BATCH", "5")
    import clawmetry.local_store as ls
    importlib.reload(ls)
    return ls


def _read_schema_version(ls_mod) -> int:
    """Open a throwaway connection straight to the file and read the
    stamped version. Bypasses LocalStore so we can inspect even when
    construction failed."""
    conn = ls_mod._open_connection(read_only=True)
    try:
        row = conn.execute("SELECT MAX(version) FROM schema_version").fetchone()
        return row[0] if row and row[0] is not None else 0
    finally:
        conn.close()


def test_migration_failure_does_not_stamp_version(fresh_store_env, monkeypatch):
    """If the v7 migration body raises, the version row must NOT be
    stamped — otherwise the next boot would skip the retry and leave
    the schema in a permanent half-state (#1602)."""
    ls = fresh_store_env

    # Pre-create the events table at "v6" (no schema_version stamped) so
    # the migration gate ``current < 7`` actually fires.  We do this by
    # opening a writer connection, creating just the events table, then
    # closing it before LocalStore() opens its own connection.
    conn = ls._open_connection(read_only=False)
    try:
        for stmt in ls._DDL:
            conn.execute(stmt)
        # Wipe any version rows the DDL itself might have left behind so
        # we genuinely look like a v6-or-older store.
        conn.execute("DELETE FROM schema_version")
    finally:
        conn.close()

    # Inject the failure.
    boom = RuntimeError("simulated v7 dedup failure")
    def _failing(_conn):
        raise boom
    monkeypatch.setattr(ls, "_run_dedup_migration_v7", _failing)

    # Construct → must raise. (The fix re-raises after rolling back.)
    with pytest.raises(Exception):
        ls.LocalStore()

    # Critical: schema_version stayed at the pre-migration value.
    assert _read_schema_version(ls) < 7, (
        "version was stamped despite migration failure — #1602 has regressed"
    )


def test_migration_recovers_on_next_boot_after_failure(fresh_store_env, monkeypatch):
    """The whole point of NOT stamping is so the next boot retries.
    Verify the recovery path end-to-end: fail once, un-break the
    migration, boot again, observe the version stamp + working store."""
    ls = fresh_store_env

    # Same v6-shaped store prep as above.
    conn = ls._open_connection(read_only=False)
    try:
        for stmt in ls._DDL:
            conn.execute(stmt)
        conn.execute("DELETE FROM schema_version")
    finally:
        conn.close()

    # Boot 1: failure path.
    real_migration = ls._run_dedup_migration_v7
    call_count = {"n": 0}
    def _flaky(c):
        call_count["n"] += 1
        if call_count["n"] == 1:
            raise RuntimeError("simulated transient v7 failure")
        return real_migration(c)
    monkeypatch.setattr(ls, "_run_dedup_migration_v7", _flaky)

    with pytest.raises(Exception):
        ls.LocalStore()
    assert _read_schema_version(ls) < 7

    # Boot 2: the un-patched migration is wrapped by ``_flaky`` and
    # succeeds on attempt #2 — exactly the "transient failure cleared
    # itself" recovery scenario.
    store = ls.LocalStore()
    try:
        store.start()
        assert call_count["n"] == 2, (
            "second boot did NOT retry the migration — recovery contract "
            "broken; #1602 fix is incomplete"
        )
        # Version stamped at current SCHEMA_VERSION now that the gated
        # migration finally succeeded.
        h = store.health()
        assert h["schema_version"] == ls.SCHEMA_VERSION
    finally:
        store.stop(flush=False)


def test_fresh_store_stamps_version_normally(fresh_store_env):
    """Sanity check: the fix didn't break the happy path. A brand-new
    store with no failures should construct cleanly and stamp the
    current SCHEMA_VERSION."""
    ls = fresh_store_env
    store = ls.LocalStore()
    try:
        store.start()
        assert store.health()["schema_version"] == ls.SCHEMA_VERSION
    finally:
        store.stop(flush=False)
