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
    ls._oom_bumps = 0
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

    def _recover(exc=None, **kw):
        calls["recover"] += 1
        return real_recover(exc, **kw)

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
        lambda *a, **k: calls.__setitem__("recover", calls["recover"] + 1) or False,
    )
    poisoned = _PoisonedConn(st._conn, "Could not set lock on file")
    st._conn = poisoned
    st.ingest({"id": "contended", "node_id": "n1", "agent_type": "claude_code",
               "session_id": "s1", "event_type": "tool_call", "ts": 1.0})
    st.flush()
    assert calls["recover"] == 0


# ── the read path (2026-09-02) ──────────────────────────────────────────────
#
# On 2026-09-02 a 4.2 GB store ran the daemon out of its 2 GB buffer pool on
# ``query_aggregates``; the rollback ran out too and DuckDB invalidated the
# handle. Nothing was queued to write that morning, so the flush-path recovery
# above never ran, and every dashboard query answered 500 for two hours while
# the daemon looked healthy. These pin the two halves of that fix: reads heal
# the handle as well, and an out-of-memory invalidation is answered with a
# bigger ceiling rather than an index rebuild.

_OOM_FATAL = (
    "FATAL Error: Failed: database has been invalidated because of a previous "
    "fatal error. The database must be restarted prior to being used again.\n"
    'Original error: "Failed to rollback transaction. Cannot continue '
    "operation.\nOriginal Error: Out of Memory Error: failed to pin block of "
    'size 8.3 MiB (1.8 GiB/1.8 GiB used)'
)
_INDEX_FATAL = (
    "FATAL Error: Failed: database has been invalidated because of a previous "
    'fatal error.\nOriginal error: "Invalid Input Error: Failed to delete all '
    'rows from index. Only deleted 0 out of 301 rows.'
)


def _poison_reads(st, error, match="SELECT", times=1):
    """Reads run on this thread's cursor (a second connection), not on
    ``st._conn``; poison the cursor so the fatal surfaces where reads look."""
    st._read_local.cur = _PoisonedConn(st._read_cursor(), error, match=match, times=times)
    st._read_local.gen = st._conn_generation


def _limit_gib(st) -> float:
    txt = st._conn.execute("SELECT current_setting('memory_limit')").fetchone()[0]
    num, unit = txt.split()
    return float(num) * {"GiB": 1.0, "MiB": 1 / 1024, "TiB": 1024.0}[unit]


def test_a_failed_read_heals_the_handle_and_answers(store, monkeypatch):
    """The integration point for reads. A dashboard query on a dead handle
    used to raise straight through to a 500; it now recovers once and
    returns the rows."""
    ls, st = store
    st.ingest({"id": "r1", "node_id": "n1", "agent_type": "claude_code",
               "session_id": "s1", "event_type": "tool_call", "ts": 1.0})
    st.flush()
    calls = {"recover": 0}
    real = st.recover_invalidated_db

    def _recover(exc=None, **kw):
        calls["recover"] += 1
        return real(exc, **kw)

    monkeypatch.setattr(st, "recover_invalidated_db", _recover)
    _poison_reads(st, _INDEX_FATAL)

    rows = st._fetch("SELECT COUNT(*) FROM events", [])

    assert calls["recover"] == 1
    assert rows[0][0] == 1
    assert ls._fatal_db_state["invalidated"] is False


def test_a_non_fatal_read_error_is_the_callers(store):
    """Only the invalidated-handle wording triggers a rebuild on read; an
    ordinary bad query still raises to whoever wrote it."""
    ls, st = store
    with pytest.raises(Exception):
        st._fetch("SELECT * FROM no_such_table", [])
    assert ls._fatal_db_state["invalidated"] is False
    assert st._recovery_attempted is False


def test_an_out_of_memory_invalidation_reopens_with_a_bigger_ceiling(store):
    """Nothing on disk is wrong after an OOM, so the indexes stay and the
    handle comes back under a larger memory_limit."""
    ls, st = store
    before_idx = _index_names(st)
    before_gib = _limit_gib(st)
    _poison_reads(st, _OOM_FATAL)

    rows = st._fetch("SELECT COUNT(*) FROM events", [])

    assert rows[0][0] == 0
    assert ls._oom_bumps == 1
    assert st._recovery_attempted is False, "an OOM must not spend the one index rebuild"
    assert _index_names(st) == before_idx
    assert _limit_gib(st) > before_gib
    assert ls._fatal_db_state["recovered"] == 1
    assert ls._fatal_db_state["invalidated"] is False


def test_an_oom_reopen_is_refused_inside_the_cooldown(store):
    """The ceiling moved once. A query that still does not fit five seconds
    later needs a human, not a second reopen every tick."""
    ls, st = store
    assert st.recover_invalidated_db(RuntimeError(_OOM_FATAL)) is True
    assert st.recover_invalidated_db(RuntimeError(_OOM_FATAL)) is False
    assert ls._oom_bumps == 1


def test_an_oom_reopen_does_not_consume_the_index_rebuild(store):
    ls, st = store
    assert st.recover_invalidated_db(RuntimeError(_OOM_FATAL)) is True
    # A later stale-index invalidation still gets its one rebuild.
    assert st.recover_invalidated_db(RuntimeError(_INDEX_FATAL)) is True
    assert st._recovery_attempted is True


def test_a_caller_behind_the_latest_reopen_is_already_healed(store):
    """Several request threads fail on the same dead handle at once. The
    first reopens; the others, carrying the generation they saw before
    failing, must not each reopen again."""
    ls, st = store
    gen = st._conn_generation
    assert st.recover_invalidated_db(RuntimeError(_OOM_FATAL),
                                     seen_generation=gen) is True
    assert st._conn_generation == gen + 1
    # Same stale generation, reported by a slower thread: no second reopen.
    assert st.recover_invalidated_db(RuntimeError(_OOM_FATAL),
                                     seen_generation=gen) is True
    assert ls._oom_bumps == 1


def test_health_still_answers_on_a_dead_handle(store, monkeypatch):
    """``db_invalidated`` is only useful if health() can be read while the
    store is bricked. When recovery declines, the row still comes back."""
    ls, st = store
    monkeypatch.setattr(st, "recover_invalidated_db", lambda *a, **k: False)
    _poison_reads(st, _INDEX_FATAL, match="SELECT COUNT(*) AS N", times=10)
    h = st.health()
    assert h["db_invalidated"] is True
    assert "invalidated" in (h["db_last_error"] or "")
    assert h["event_count"] == 0


def test_the_oom_classifier_reads_duckdbs_wording(store):
    ls, _st = store
    assert ls._is_oom_error(RuntimeError(_OOM_FATAL)) is True
    assert ls._is_oom_error(RuntimeError(_INDEX_FATAL)) is False
    assert ls._is_oom_error(None) is False


def test_health_reports_the_ceiling_it_runs_under(store):
    ls, st = store
    h = st.health()
    assert h["duckdb_memory_limit"].endswith("GiB")
    assert h["duckdb_oom_reopens"] == 0
    assert st.recover_invalidated_db(RuntimeError(_OOM_FATAL)) is True
    h2 = st.health()
    assert h2["duckdb_oom_reopens"] == 1
    assert _limit_gib(st) > 1.9
