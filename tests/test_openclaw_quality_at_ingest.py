"""OpenClaw sessions are quality-graded at ingest, like family runtimes.

Before 2026-09-11 only ``sync_family_runtimes`` wrote ``metadata.quality``.
OpenClaw sessions arrive through ``_local_ingest_sessions_batch`` and never
got a grade, so the Harness Engineering bench counted zero measurable OpenClaw
sessions and stamped the flagship runtime "Can't see".
"""

from __future__ import annotations

import clawmetry.sync as sync


def _events(sid, n=6):
    rows = []
    for i in range(n):
        rows.append({"event_type": "tool.use", "ts": 1000 + 2 * i, "session_id": sid,
                     "data": {"name": "read_file", "input": {"path": f"/f{i}.py"}}})
        rows.append({"event_type": "tool.result", "ts": 1001 + 2 * i, "session_id": sid,
                     "data": {"is_error": False, "content": "ok"}})
    return rows


class _Store:
    def __init__(self, events):
        self.events = events
        self.reads = 0
        self.written = []

    def query_events(self, session_id=None, limit=None, **_):
        self.reads += 1
        return [e for e in self.events if e["session_id"] == session_id]

    def ingest_sessions_batch(self, rows):
        self.written.extend(rows)
        return len(rows)


def _run(monkeypatch, store, rows):
    from clawmetry import local_store
    monkeypatch.setattr(local_store, "get_store", lambda: store)
    sync._local_ingest_sessions_batch(rows, "node")
    return store.written


def test_openclaw_session_gets_a_quality_block(monkeypatch):
    sync._OPENCLAW_QUALITY_CACHE.clear()
    store = _Store(_events("oc-1"))
    rows = _run(monkeypatch, store, [{"session_id": "oc-1", "updated_at": "t1",
                                      "channel": "telegram"}])
    meta = rows[0]["metadata"]
    assert meta["channel"] == "telegram", "existing metadata must survive"
    assert meta["quality"]["measurable"] is True
    assert meta["quality"]["runtime"] == "openclaw"


def test_unchanged_session_reuses_its_grade_without_rereading(monkeypatch):
    sync._OPENCLAW_QUALITY_CACHE.clear()
    store = _Store(_events("oc-2"))
    row = {"session_id": "oc-2", "updated_at": "t1"}
    _run(monkeypatch, store, [dict(row)])
    _run(monkeypatch, store, [dict(row)])
    assert store.reads == 1
    # The re-sent row still carries the grade: the metadata upsert replaces
    # the whole blob, so dropping it here would erase the stored verdict.
    assert store.written[-1]["metadata"]["quality"]["measurable"] is True


def test_changed_session_is_regraded(monkeypatch):
    sync._OPENCLAW_QUALITY_CACHE.clear()
    store = _Store(_events("oc-3"))
    _run(monkeypatch, store, [{"session_id": "oc-3", "updated_at": "t1"}])
    _run(monkeypatch, store, [{"session_id": "oc-3", "updated_at": "t2"}])
    assert store.reads == 2


def test_family_prefixed_ids_are_left_to_the_family_path(monkeypatch):
    sync._OPENCLAW_QUALITY_CACHE.clear()
    store = _Store([])
    rows = _run(monkeypatch, store, [{"session_id": "codex:abc", "updated_at": "t"}])
    assert store.reads == 0
    assert rows[0]["metadata"] is None


def test_unreadable_events_never_block_the_write(monkeypatch):
    sync._OPENCLAW_QUALITY_CACHE.clear()

    class _Broken(_Store):
        def query_events(self, **_):
            raise RuntimeError("store busy")

    store = _Broken([])
    rows = _run(monkeypatch, store, [{"session_id": "oc-4", "updated_at": "t"}])
    assert len(rows) == 1
    assert rows[0]["metadata"] is None
