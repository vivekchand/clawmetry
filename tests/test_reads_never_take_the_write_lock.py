"""Store reads must not queue behind the write lock or behind each other.

On 2026-09-02 every read held ``_write_lock`` for its whole execute-and-fetch.
One open dashboard tab issues ~85 requests per 25 s and the overview endpoint
alone makes 17-23 store calls, so queries costing 0.05-0.2 s in isolation took
1-3 s live, overview took 4-18 s, and the page's 3-5 s client timeouts fired on
every tab while the daemon idled. Reads now use one DuckDB cursor per thread
and never touch the lock.
"""
from __future__ import annotations

import threading
import time

import pytest

duckdb = pytest.importorskip("duckdb")


@pytest.fixture
def store(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("CLAWMETRY_HOME", str(tmp_path / ".clawmetry"))
    import importlib

    import clawmetry.local_store as ls

    importlib.reload(ls)
    ls.DB_PATH = tmp_path / "test.duckdb"
    ls._oom_bumps = 0
    st = ls.LocalStore(read_only=False)
    st.ingest_many([
        {"id": f"e{i}", "node_id": "n1", "agent_type": "claude_code",
         "session_id": "s1", "event_type": "tool_call", "ts": float(i + 1)}
        for i in range(20)
    ])
    st.flush()
    yield ls, st
    try:
        st.stop(flush=False)
    except Exception:
        pass


def test_a_read_completes_while_the_write_lock_is_held(store):
    """The property that matters: a flush in progress must not stall the
    dashboard. Hold the lock the way the flusher does and read through it."""
    ls, st = store
    released = threading.Event()

    def hold():
        with st._write_lock:
            released.wait(5)

    t = threading.Thread(target=hold)
    t.start()
    time.sleep(0.05)
    try:
        started = time.monotonic()
        rows = st._fetch("SELECT COUNT(*) FROM events", [])
        elapsed = time.monotonic() - started
    finally:
        released.set()
        t.join()
    assert rows[0][0] == 20
    assert elapsed < 1.0, f"read waited {elapsed:.2f}s behind the write lock"


def test_each_thread_gets_its_own_cursor(store):
    ls, st = store
    seen = {}

    def worker(name):
        st._fetch("SELECT 1", [])
        # Hold the object, not its id: a cursor freed when its thread ends
        # can be reallocated at the same address for the next thread.
        seen[name] = st._read_local.cur

    ts = [threading.Thread(target=worker, args=(f"t{i}",)) for i in range(3)]
    [t.start() for t in ts]
    [t.join() for t in ts]
    assert len({id(c) for c in seen.values()}) == 3


def test_concurrent_reads_see_committed_writes(store):
    """Cursors are separate connections: they must see what the writer has
    flushed, because that is what every dashboard read is for."""
    ls, st = store
    st.ingest({"id": "late", "node_id": "n1", "agent_type": "claude_code",
               "session_id": "s1", "event_type": "tool_call", "ts": 99.0})
    st.flush()
    out = {}

    def reader():
        out["n"] = st._fetch("SELECT COUNT(*) FROM events WHERE id='late'", [])[0][0]

    t = threading.Thread(target=reader)
    t.start()
    t.join()
    assert out["n"] == 1


def test_cursor_follows_the_connection_after_a_recovery(store):
    """A reopen bumps the generation; the next read on this thread must not
    run on the closed parent."""
    ls, st = store
    st._fetch("SELECT 1", [])
    old = st._read_local.cur
    assert st.recover_invalidated_db(RuntimeError(
        "FATAL Error: database has been invalidated because of a previous fatal "
        "error.\nOriginal Error: Out of Memory Error: failed to pin block")) is True
    assert st._fetch("SELECT COUNT(*) FROM events", [])[0][0] == 20
    assert st._read_local.cur is not old


def test_eight_readers_and_a_writer_do_not_queue(store):
    """Throughput guard: with the lock, eight readers serialised to roughly
    one read at a time. Cursors must run them concurrently."""
    ls, st = store
    stop = threading.Event()
    lat = []
    lock = threading.Lock()

    def writer():
        i = 0
        while not stop.is_set():
            st.ingest({"id": f"w{i}", "node_id": "n1", "agent_type": "claude_code",
                       "session_id": "s2", "event_type": "tool_call", "ts": 1000.0 + i})
            st.flush()
            i += 1
            time.sleep(0.02)

    def reader():
        while not stop.is_set():
            t = time.monotonic()
            st._fetch("SELECT COUNT(*) FROM events", [])
            with lock:
                lat.append(time.monotonic() - t)

    ts = [threading.Thread(target=writer)] + [threading.Thread(target=reader) for _ in range(8)]
    [t.start() for t in ts]
    time.sleep(1.5)
    stop.set()
    [t.join() for t in ts]
    lat.sort()
    assert len(lat) > 50
    assert lat[int(len(lat) * 0.95)] < 0.5, f"p95 read latency {lat[int(len(lat)*0.95)]:.3f}s"
