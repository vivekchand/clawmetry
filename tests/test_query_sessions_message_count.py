"""Regression test for `LocalStore.query_sessions_table` (#1129 bug 4).

The ``sessions`` table has a ``message_count`` column, but the OpenClaw
session ingest path never populates it — so every OpenClaw session showed
``message_count: 0`` in ``/api/sessions``.

The fix computes the count from the ``events`` table via a correlated
subquery. These tests pin that behaviour.
"""

from __future__ import annotations

import importlib
import uuid

import pytest


@pytest.fixture
def store(tmp_path, monkeypatch):
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "events.duckdb"))
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_SECS", "0.02")
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_BATCH", "1")
    import clawmetry.local_store as ls
    importlib.reload(ls)
    s = ls.LocalStore()
    s.start()
    yield s
    s.stop(flush=True)


def _wait(s, timeout=2.0):
    import time
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if s.health()["ring_depth"] == 0:
            return
        time.sleep(0.01)
    raise AssertionError("flusher did not drain")


def _ingest_event(s, sid, *, ts="2026-05-13T10:00:00Z", agent_type="openclaw"):
    # Issue #1718: message_count is now restricted to renderable event_types
    # (the ones ``_try_local_store_transcript`` actually emits as turns).
    # ``brain`` is NOT renderable — use ``model.completed`` so the count
    # reflects something the user would actually see in the modal.
    s.ingest({
        "id": str(uuid.uuid4()),
        "node_id": "agent+test",
        "agent_id": "main",
        "agent_type": agent_type,
        "session_id": sid,
        "event_type": "model.completed",
        "ts": ts,
        "data": {"type": "model.completed", "data": {"text": "x"}},
    })


def test_message_count_computed_from_events_table(store):
    """ingest_session never sets message_count; query_sessions_table should
    still report the actual number of events for that session."""
    sid = "sess-count-1"
    store.ingest_session({
        "session_id": sid,
        "agent_type": "openclaw",
        "title": "OpenClaw session",
        "started_at":     "2026-05-13T10:00:00Z",
        "last_active_at": "2026-05-13T10:05:00Z",
        "status": "active",
        # Note: NO message_count passed — this is the bug.
    })
    for i in range(7):
        _ingest_event(store, sid, ts=f"2026-05-13T10:00:{i:02d}Z")
    _wait(store)

    rows = store.query_sessions_table(agent_type="openclaw")
    assert len(rows) == 1
    assert rows[0]["session_id"] == sid
    assert rows[0]["message_count"] == 7


def test_message_count_falls_back_to_stored_value_when_no_events(store):
    """sync.py's ingest path DOES set message_count but never writes the
    events. query_sessions_table must honour the stored value in that case
    (GREATEST of the two)."""
    sid = "sess-stored-only"
    store.ingest_session({
        "session_id": sid,
        "agent_type": "claude_code",
        "title": "Claude Code session (sync.py path)",
        "started_at":     "2026-05-13T10:00:00Z",
        "last_active_at": "2026-05-13T10:00:00Z",
        "message_count": 42,
    })
    _wait(store)

    rows = store.query_sessions_table(agent_type="claude_code")
    assert len(rows) == 1
    assert rows[0]["message_count"] == 42


def test_message_count_uses_max_when_both_set(store):
    """If both the stored column AND the events table have data, the larger
    of the two wins — so we never UNDER-count when the stored value is
    stale (events kept arriving after ingest_session)."""
    sid = "sess-both"
    store.ingest_session({
        "session_id": sid,
        "agent_type": "openclaw",
        "title": "both",
        "started_at":     "2026-05-13T10:00:00Z",
        "last_active_at": "2026-05-13T10:01:00Z",
        "message_count": 2,  # stale
    })
    for i in range(5):
        _ingest_event(store, sid, ts=f"2026-05-13T10:00:{i:02d}Z")
    _wait(store)

    rows = store.query_sessions_table(agent_type="openclaw")
    assert len(rows) == 1
    assert rows[0]["message_count"] == 5  # events count wins over stale 2


def test_message_count_isolated_per_session(store):
    """Correlated subquery must filter by session_id — events for OTHER
    sessions must not inflate the count."""
    store.ingest_session({
        "session_id": "sess-A",
        "agent_type": "openclaw",
        "started_at":     "2026-05-13T10:00:00Z",
        "last_active_at": "2026-05-13T10:00:00Z",
    })
    store.ingest_session({
        "session_id": "sess-B",
        "agent_type": "openclaw",
        "started_at":     "2026-05-13T10:00:00Z",
        "last_active_at": "2026-05-13T10:00:01Z",
    })
    for i in range(3):
        _ingest_event(store, "sess-A", ts=f"2026-05-13T10:00:{i:02d}Z")
    for i in range(10):
        _ingest_event(store, "sess-B", ts=f"2026-05-13T10:01:{i:02d}Z")
    _wait(store)

    rows = {r["session_id"]: r for r in store.query_sessions_table(agent_type="openclaw")}
    assert rows["sess-A"]["message_count"] == 3
    assert rows["sess-B"]["message_count"] == 10
