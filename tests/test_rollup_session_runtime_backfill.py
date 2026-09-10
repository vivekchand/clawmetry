"""`rollup_session.runtime` heals rows written before the #5743 write fix (#5781).

#5743 fixed the WRITE path: a new rollup derives its runtime from the session
id prefix rather than `agent_type`, which the family ingest never sets, so
every paid runtime had been landing as `openclaw`. It repaired nothing already
in the table.

And these rows do not heal on their own. `_mirror_session_rollups_locked`
rewrites a row only when its session is re-ingested, and ended sessions are
skipped by the family high-water mark by design, because re-reading thousands
of finished transcripts every cycle is exactly the cost that mark exists to
avoid. A session that finished before the upgrade keeps its wrong runtime
forever.

Measured on a node running 0.12.849 (which carries the write fix), 76 minutes
after restart: 2279 rows, 179 correct, **2100 stale**, 2070 of them ended
claude_code sessions. Reproduced independently on a second node: 2305 rows,
205 correct, 2100 stale, same breakdown. **Zero rows were genuinely OpenClaw**
on either.

The damage is not cosmetic: `query_rollup_sessions(runtime="claude_code")`
returns 92% fewer rows than it should, and `query_usage_by_team` joins
`tm.key_value = rs.runtime`, so historical per-team spend collapses under
`openclaw`.
"""
from __future__ import annotations

import importlib
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture
def store(tmp_path, monkeypatch):
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "cm.duckdb"))
    import clawmetry.local_store as ls
    importlib.reload(ls)
    monkeypatch.setattr(ls, "_daemon_registered", lambda *a, **k: False)
    s = ls.get_store()
    yield s, ls
    try:
        s.stop(flush=True)
    except Exception:
        pass


def _seed(store, rows):
    for sid, runtime in rows:
        store._conn.execute(
            "INSERT INTO rollup_session (session_id, runtime) VALUES (?, ?) "
            "ON CONFLICT (session_id) DO UPDATE SET runtime = excluded.runtime",
            [sid, runtime])


def _runtime_of(store, sid):
    r = store._conn.execute(
        "SELECT runtime FROM rollup_session WHERE session_id = ?", [sid]).fetchone()
    return r[0] if r else None


def test_a_stale_row_lands_under_its_real_runtime(store):
    """The 2070-row case: an ended claude_code session mislabelled openclaw."""
    s, ls = store
    _seed(s, [("claude_code:abc-123", "openclaw")])
    ls._migrate_rollup_session_runtime(s._conn)
    assert _runtime_of(s, "claude_code:abc-123") == "claude_code"


@pytest.mark.parametrize("runtime", [
    "claude_code", "codex", "opencode", "goose", "cursor",
])
def test_every_runtime_seen_stale_in_the_field_heals(store, runtime):
    """The exact prefixes measured stale on a real node."""
    s, ls = store
    sid = f"{runtime}:sess-1"
    _seed(s, [(sid, "openclaw")])
    ls._migrate_rollup_session_runtime(s._conn)
    assert _runtime_of(s, sid) == runtime


def test_a_genuine_openclaw_row_is_untouched(store):
    """OpenClaw ids carry no runtime prefix, so they cannot match."""
    s, ls = store
    _seed(s, [("bare-uuid-no-prefix", "openclaw")])
    ls._migrate_rollup_session_runtime(s._conn)
    assert _runtime_of(s, "bare-uuid-no-prefix") == "openclaw"


def test_a_colon_that_is_not_a_runtime_is_untouched(store):
    """The reason the migration checks a KNOWN prefix list rather than just
    splitting on ':'. An OpenClaw id that happens to contain a colon must
    never be read as a runtime."""
    s, ls = store
    _seed(s, [("weird:id-with-colon", "openclaw")])
    ls._migrate_rollup_session_runtime(s._conn)
    assert _runtime_of(s, "weird:id-with-colon") == "openclaw"


def test_an_already_correct_row_is_left_alone(store):
    s, ls = store
    _seed(s, [("codex:sess-9", "codex")])
    ls._migrate_rollup_session_runtime(s._conn)
    assert _runtime_of(s, "codex:sess-9") == "codex"


def test_the_migration_is_idempotent(store):
    s, ls = store
    _seed(s, [("cursor:sess-2", "openclaw")])
    for _ in range(3):
        ls._migrate_rollup_session_runtime(s._conn)
    assert _runtime_of(s, "cursor:sess-2") == "cursor"


def test_a_null_runtime_is_healed_too(store):
    """`IS DISTINCT FROM` rather than `<>`: a NULL runtime is as wrong as a
    mislabelled one, and `NULL <> 'x'` is NULL, so a plain inequality would
    silently skip it."""
    s, ls = store
    s._conn.execute(
        "INSERT INTO rollup_session (session_id, runtime) VALUES (?, NULL)",
        ["goose:sess-null"])
    ls._migrate_rollup_session_runtime(s._conn)
    assert _runtime_of(s, "goose:sess-null") == "goose"


def test_the_predicate_is_shared_with_the_write_path(store):
    """The migration and `_runtime_of_session_id` must not drift: both read
    `_NON_OPENCLAW_RUNTIME_PREFIXES`."""
    import inspect
    s, ls = store
    src = inspect.getsource(ls._migrate_rollup_session_runtime)
    assert "_NON_OPENCLAW_RUNTIME_PREFIXES" in src
    # And the two agree, runtime by runtime, on the whole catalogue.
    for prefix in list(ls._NON_OPENCLAW_RUNTIME_PREFIXES)[:12]:
        sid = f"{prefix}:x"
        _seed(s, [(sid, "openclaw")])
    ls._migrate_rollup_session_runtime(s._conn)
    for prefix in list(ls._NON_OPENCLAW_RUNTIME_PREFIXES)[:12]:
        sid = f"{prefix}:x"
        assert _runtime_of(s, sid) == ls._runtime_of_session_id(sid), sid


def test_the_migration_actually_runs_on_open(tmp_path, monkeypatch):
    """A migration nothing calls repairs nothing. Opens a store, seeds a stale
    row, closes, re-opens, and asserts the row healed without anyone calling
    the function by hand."""
    db = tmp_path / "healed.duckdb"
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(db))
    import clawmetry.local_store as ls
    importlib.reload(ls)
    monkeypatch.setattr(ls, "_daemon_registered", lambda *a, **k: False)

    s = ls.get_store()
    _seed(s, [("claude_code:on-open", "openclaw")])
    # Force the stale state a pre-#5743 store would have on disk.
    s._conn.execute("UPDATE schema_version SET version = 15")
    s.stop(flush=True)
    ls._store_rw = None

    importlib.reload(ls)
    monkeypatch.setattr(ls, "_daemon_registered", lambda *a, **k: False)
    s2 = ls.get_store()
    try:
        assert _runtime_of(s2, "claude_code:on-open") == "claude_code", (
            "the migration must run from _apply_migrations on open, not only "
            "when a test calls it directly"
        )
    finally:
        s2.stop(flush=True)
