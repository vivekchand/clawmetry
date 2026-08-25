"""The daemon recovers from an invalidated DuckDB instead of running bricked.

DuckDB says it plainly: "database has been invalidated because of a previous
fatal error. The database must be restarted prior to being used again." Until
this change nothing acted on that. The daemon kept running with a dead handle,
every write failed the same way, every read answered empty, and the process
never exited -- so launchd never restarted it and the dashboard just went
quiet. On 2026-08-25 a dev machine sat in that state long enough to write
70 MB of identical tracebacks while ``launchctl list`` reported exit status 0.

Restarting alone does not fix it either: the cause is usually a corrupt index,
so a fresh daemon re-ingests the same rows and invalidates again in seconds.
The recovery is the one the code already documented for a human to run by
hand -- reopen, CHECKPOINT, drop every index, CHECKPOINT, migrate -- and
``_migrate`` recreates every index from ``_DDL``, which is what makes it safe
to automate.

These tests pin the properties that matter: rows survive, indexes come back,
it runs at most once, and a bricked store becomes VISIBLE in health().
"""
from __future__ import annotations

import pytest

duckdb = pytest.importorskip("duckdb")


@pytest.fixture
def store(tmp_path, monkeypatch):
    """A real LocalStore on a scratch DuckDB file.

    Never the developer's own store: a full-suite run that wrote into the real
    ``~/.clawmetry`` is what corrupted the index this test exists for
    (memory ``feedback_tests_mutate_real_clawmetry_home``).
    """
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("CLAWMETRY_HOME", str(tmp_path / ".clawmetry"))
    import importlib

    import clawmetry.local_store as ls

    importlib.reload(ls)
    ls.DB_PATH = tmp_path / "test.duckdb"
    ls._fatal_db_state.update({"invalidated": False, "recovered": 0,
                               "last_error": None})
    ls._fatal_db_reported = False
    st = ls.LocalStore(read_only=False)
    yield ls, st
    try:
        st.stop(flush=False)
    except Exception:
        pass


def _index_names(st):
    return {r[0] for r in st._conn.execute(
        "SELECT index_name FROM duckdb_indexes()").fetchall() if r and r[0]}


# ── the recovery ────────────────────────────────────────────────────────────


def test_recovery_keeps_every_row(store):
    """Dropping indexes must not drop data. This is the whole reason the
    rebuild is safe to run automatically."""
    ls, st = store
    # Through the real ingest path, not hand-written SQL: the point is that
    # rows the daemon actually wrote survive the rebuild.
    st.ingest_many([
        {"id": "e1", "node_id": "n1", "agent_type": "claude_code",
         "session_id": "s1", "event_type": "tool_call", "ts": 1.0},
        {"id": "e2", "node_id": "n1", "agent_type": "claude_code",
         "session_id": "s1", "event_type": "tool_result", "ts": 2.0},
    ])
    st.flush()
    before = st._conn.execute("SELECT COUNT(*) FROM events").fetchone()[0]
    assert before == 2

    assert st.recover_invalidated_db() is True

    after = st._conn.execute("SELECT COUNT(*) FROM events").fetchone()[0]
    assert after == before


def test_recovery_puts_the_indexes_back(store):
    """``_migrate`` recreates them from _DDL, so the schema ends where it
    started. If it did not, the next query would table-scan forever."""
    ls, st = store
    before = _index_names(st)
    assert before, "expected the schema to define indexes"

    assert st.recover_invalidated_db() is True

    assert _index_names(st) == before


def test_the_store_is_writable_after_recovery(store):
    ls, st = store
    st.recover_invalidated_db()
    st.ingest({"id": "after", "node_id": "n1", "agent_type": "claude_code",
               "session_id": "s2", "event_type": "tool_call", "ts": 3.0})
    st.flush()
    assert st._conn.execute(
        "SELECT COUNT(*) FROM events WHERE id='after'").fetchone()[0] == 1


def test_recovery_runs_at_most_once_per_process(store):
    """A rebuilt index that invalidates again is not a stale index, and a
    loop would only hide the real cause."""
    ls, st = store
    assert st.recover_invalidated_db() is True
    assert st.recover_invalidated_db() is False


def test_a_read_only_store_never_rebuilds(store, tmp_path):
    """Only the writer owns the schema. A dashboard process attempting this
    would fight the daemon for the lock."""
    ls, st = store
    st._read_only = True
    st._recovery_attempted = False
    assert st.recover_invalidated_db() is False


# ── visibility ──────────────────────────────────────────────────────────────


def test_health_reports_a_bricked_store(store):
    """The gap that let one sit unnoticed: from the outside a bricked daemon
    is indistinguishable from an idle one."""
    ls, st = store
    assert st.health()["db_invalidated"] is False

    ls._report_fatal_db_once(RuntimeError("database has been invalidated"))
    assert st.health()["db_invalidated"] is True
    assert "invalidated" in str(st.health()["db_last_error"])


def test_health_clears_and_counts_after_a_successful_rebuild(store):
    ls, st = store
    ls._report_fatal_db_once(RuntimeError("database has been invalidated"))
    assert st.health()["db_invalidated"] is True

    assert st.recover_invalidated_db() is True

    h = st.health()
    assert h["db_invalidated"] is False
    assert h["db_recoveries"] == 1


def test_the_fatal_detector_matches_duckdbs_wording(store):
    """Pinned against DuckDB's real message, not a paraphrase."""
    ls, _st = store
    real = (
        'FATAL Error: Failed: database has been invalidated because of a '
        'previous fatal error. The database must be restarted prior to being '
        'used again.\nOriginal error: "Invalid Input Error: Failed to delete '
        'all rows from index. Only deleted 0 out of 301 rows.'
    )
    assert ls._is_fatal_db_state(RuntimeError(real)) is True
    assert ls._is_fatal_db_state(RuntimeError("Could not set lock")) is False


# ── the wiring ──────────────────────────────────────────────────────────────


class _PoisonedConn:
    """Wraps the real connection and raises on the Nth matching statement.

    A DuckDB connection's methods are read-only, so the failure has to be
    injected by substituting the connection object rather than patching a
    method on it. Everything except ``execute`` delegates untouched.
    """

    def __init__(self, real, error, match="INSERT", times=1):
        self._real = real
        self._error = error
        self._match = match
        self._left = times
        self.raised = 0

    def execute(self, sql, *a, **kw):
        if self._left > 0 and self._match in str(sql).upper():
            self._left -= 1
            self.raised += 1
            raise RuntimeError(self._error)
        return self._real.execute(sql, *a, **kw)

    def __getattr__(self, name):
        return getattr(self._real, name)


def test_the_flush_path_attempts_recovery_and_retries_the_batch(store, monkeypatch):
    """The integration point. Detecting the fatal is worth nothing unless the
    flusher acts on it: before this change it logged once and gave up, and
    the queued events sat in the ring forever while the daemon stayed alive.
    """
    ls, st = store
    calls = {"recover": 0}
    real_recover = st.recover_invalidated_db

    def _recover():
        calls["recover"] += 1
        return real_recover()

    monkeypatch.setattr(st, "recover_invalidated_db", _recover)

    # Poison exactly the first flush, the way a corrupt index does.
    st._conn = _PoisonedConn(
        st._conn,
        "FATAL Error: Failed: database has been invalidated because of a "
        "previous fatal error.",
    )

    st.ingest({"id": "queued", "node_id": "n1", "agent_type": "claude_code",
               "session_id": "s1", "event_type": "tool_call", "ts": 1.0})
    st.flush()

    assert calls["recover"] == 1, "the flusher never tried to recover"
    # The ring holds the batch across the failure (snapshot-then-pop), so a
    # successful rebuild must land the event rather than lose it.
    assert st._conn.execute(
        "SELECT COUNT(*) FROM events WHERE id='queued'").fetchone()[0] == 1


def test_a_non_fatal_error_does_not_trigger_a_rebuild(store, monkeypatch):
    """Dropping every index is cheap but not free. An ordinary contended
    write must keep using the existing retry/backoff instead."""
    ls, st = store
    calls = {"recover": 0}
    monkeypatch.setattr(
        st, "recover_invalidated_db",
        lambda: calls.__setitem__("recover", calls["recover"] + 1) or False,
    )
    poisoned = _PoisonedConn(st._conn, "Could not set lock on file")
    st._conn = poisoned
    st.ingest({"id": "contended", "node_id": "n1", "agent_type": "claude_code",
               "session_id": "s1", "event_type": "tool_call", "ts": 1.0})
    st.flush()
    assert calls["recover"] == 0
