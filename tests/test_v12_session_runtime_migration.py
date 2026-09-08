"""v11 -> v12 migration: re-attribute mislabeled session runtimes.

v11 fixed the EVENT side of the same bug class (rollup tokens/cost attributed
to openclaw for every family runtime). It left the ``sessions`` table alone,
so nodes that had already ingested Claude Code / Codex / Cursor sessions kept
a table full of rows stamped 'openclaw'. Those rows are what
``_refresh_runtime_day_session_counts_locked`` counts, so the Fleet card stayed
on "detected here / syncing to cloud" even after the ingest path was fixed.

Fixing ingest forward-only is not enough — the existing rows have to be
re-stamped, or an established node never recovers.
"""

from __future__ import annotations

import importlib

import duckdb
import pytest


@pytest.fixture()
def store(tmp_path, monkeypatch):
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "events.duckdb"))
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_READ", "1")
    import clawmetry.local_store as ls
    importlib.reload(ls)
    s = ls.get_store()
    yield s
    try:
        s.stop(flush=True)
    except Exception:
        pass


def test_migration_restamps_family_sessions(tmp_path, monkeypatch):
    db = tmp_path / "events.duckdb"
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(db))
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_READ", "1")

    import clawmetry.local_store as ls
    importlib.reload(ls)

    # Build the schema, then rewind to v11 and plant the pre-fix rows exactly
    # as the old ingest path wrote them: correct session_id, wrong agent_type.
    s = ls.get_store()
    s.ingest_sessions_batch([
        {
            "agent_type": "openclaw",
            "session_id": "claude_code:66bfb3ac",
            "node_id": "n1",
            "started_at": "2026-08-23T10:00:00+00:00",
            "last_active_at": "2026-08-23T11:00:00+00:00",
        },
        {
            "agent_type": "openclaw",
            "session_id": "codex:deadbeef",
            "node_id": "n1",
            "started_at": "2026-08-23T10:00:00+00:00",
            "last_active_at": "2026-08-23T11:00:00+00:00",
        },
        {
            "agent_type": "openclaw",
            "session_id": "a-real-openclaw-session",
            "node_id": "n1",
            "started_at": "2026-08-23T10:00:00+00:00",
            "last_active_at": "2026-08-23T11:00:00+00:00",
        },
    ])
    s.stop(flush=True)

    con = duckdb.connect(str(db))
    con.execute("DELETE FROM schema_version WHERE version >= 12")
    con.execute(
        "UPDATE sessions SET agent_type = 'openclaw'"
    )  # simulate the pre-fix state for every row
    assert con.execute(
        "SELECT COUNT(*) FROM sessions WHERE agent_type <> 'openclaw'"
    ).fetchone()[0] == 0
    con.close()

    # Reopening runs _migrate, which should apply v12.
    importlib.reload(ls)
    s2 = ls.get_store()
    rows = dict(
        s2._fetch("SELECT session_id, agent_type FROM sessions", [])
    )
    s2.stop(flush=True)

    assert rows["claude_code:66bfb3ac"] == "claude_code"
    assert rows["codex:deadbeef"] == "codex"
    # A session with no runtime prefix must stay put.
    assert rows["a-real-openclaw-session"] == "openclaw"


def test_v12_wipes_all_three_rollup_tables():
    """v12 must clear rollup_model_daily too, not just the two tables it dirties.

    Caught against a copy of a real node's DuckDB, not by unit test:
    ``backfill_rollups`` decides whether to run with

        COUNT(rollup_model_daily) + COUNT(rollup_runtime_daily)
                                  + COUNT(rollup_session)

    and returns ``{'skipped': True, 'reason': 'rollups_populated'}`` when that
    sum is non-zero. A v12 that wiped only runtime+session left model_daily
    populated, so the startup backfill never ran and the runtime/session
    rollups stayed EMPTY — strictly worse than the bug being fixed. v11 wipes
    all three for exactly this reason.
    """
    import inspect
    import clawmetry.local_store as ls

    src = inspect.getsource(ls.LocalStore._migrate)
    v12 = src.split("current < 12", 1)[1].split("Step 4", 1)[0]
    for table in ("rollup_model_daily", "rollup_runtime_daily", "rollup_session"):
        assert f'DELETE FROM {table}' in v12, (
            f"v12 must wipe {table} or backfill_rollups skips as "
            f"'rollups_populated' and the rollups never rebuild"
        )


def test_session_counts_roll_up_per_runtime(store):
    """The payoff: once agent_type is right, the per-runtime session count the
    Fleet reads is non-zero instead of 0."""
    store.ingest_sessions_batch([
        {
            "agent_type": "claude_code",
            "session_id": "claude_code:s1",
            "node_id": "n1",
            "started_at": "2026-08-23T10:00:00+00:00",
            "last_active_at": "2026-08-23T10:30:00+00:00",
        },
        {
            "agent_type": "claude_code",
            "session_id": "claude_code:s2",
            "node_id": "n1",
            "started_at": "2026-08-23T12:00:00+00:00",
            "last_active_at": "2026-08-23T12:30:00+00:00",
        },
    ])

    rows = store.query_rollup_runtime_daily()
    cc = [r for r in rows if r["runtime"] == "claude_code"]
    assert cc, f"claude_code missing from the runtime rollup: {rows}"
    assert sum(r["sessions"] for r in cc) == 2
