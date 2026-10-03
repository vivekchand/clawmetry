"""Session mode columns (#4814, deliverable 1).

``mode.changed`` replay events are projected onto the session's row so the
sessions list can show how a session ran without loading its replay tree.
"""
from __future__ import annotations

from pathlib import Path

import pytest


@pytest.fixture
def store(tmp_path, monkeypatch):
    from clawmetry import local_store as ls

    monkeypatch.setattr(ls, "DB_PATH", Path(str(tmp_path / "t.duckdb")))
    ls._reset_singleton_for_tests()
    s = ls.LocalStore(read_only=False)
    s.start()
    try:
        yield s
    finally:
        try:
            s.stop(flush=True)
        except Exception:
            pass
        ls._reset_singleton_for_tests()


SID = "claude_code:abc"


def _session(store, sid=SID):
    store.ingest_session({
        "session_id": sid,
        "title": "t",
        "started_at": "2026-10-03T07:00:00Z",
        "last_active_at": "2026-10-03T07:05:00Z",
        "status": "active",
    })


def _mode(n, ts, permission, sandbox=None, collaboration=None, sid=SID):
    return {
        "span_id": f"{sid}:mode:{n}",
        "session_id": sid,
        "runtime": "claude_code",
        "kind": "mode.changed",
        "ts": float(ts),
        "payload": {},
        "mode": {"permission": permission, "sandbox": sandbox,
                 "collaboration": collaboration},
    }


def _row(store, sid=SID):
    rows = store._fetch(
        "SELECT mode_permission, mode_sandbox, mode_collaboration, "
        "mode_resolved_at FROM sessions WHERE session_id = ?", [sid])
    return rows[0] if rows else None


def test_mode_is_null_until_a_mapper_reports_one(store):
    _session(store)
    assert _row(store) == (None, None, None, None)
    listed = [r for r in store.query_sessions_table(limit=10)
              if r["session_id"] == SID][0]
    assert listed["mode_permission"] is None


def test_latest_mode_event_wins(store):
    _session(store)
    store.ingest_replay_events([
        _mode(1, 100, "default", "workspace-write"),
        _mode(2, 300, "bypassPermissions", "danger-full-access", "cron"),
        _mode(3, 200, "plan"),
    ])
    assert _row(store) == (
        "bypassPermissions", "danger-full-access", "cron", 300.0)
    listed = [r for r in store.query_sessions_table(limit=10)
              if r["session_id"] == SID][0]
    assert listed["mode_permission"] == "bypassPermissions"
    assert listed["mode_sandbox"] == "danger-full-access"
    assert listed["mode_collaboration"] == "cron"


def test_an_older_batch_never_moves_the_mode_back(store):
    _session(store)
    store.ingest_replay_events([_mode(2, 300, "plan")])
    store.ingest_replay_events([_mode(1, 100, "default")])
    assert _row(store)[0] == "plan"
    assert _row(store)[3] == 300.0


def test_later_batch_advances_and_same_ts_last_in_order_wins(store):
    _session(store)
    store.ingest_replay_events([_mode(1, 100, "default")])
    store.ingest_replay_events([
        _mode(2, 400, "plan"),
        _mode(3, 400, "acceptEdits"),
    ])
    assert _row(store)[0] == "acceptEdits"
    assert _row(store)[3] == 400.0


def test_mode_survives_a_session_upsert(store):
    _session(store)
    store.ingest_replay_events([_mode(1, 100, "yolo")])
    _session(store)  # the daemon re-ingests the session every cycle
    assert _row(store)[0] == "yolo"


def test_missing_session_row_and_other_sessions_are_untouched(store):
    _session(store, "claude_code:other")
    # No sessions row for SID yet: the replay rows are still written.
    assert store.ingest_replay_events([_mode(1, 100, "plan")]) == 1
    assert _row(store) is None
    assert _row(store, "claude_code:other") == (None, None, None, None)
    # Once the row exists, the mapper's next pass fills it.
    _session(store)
    store.ingest_replay_events([_mode(1, 100, "plan")])
    assert _row(store)[0] == "plan"


def test_non_mode_events_do_not_touch_the_columns(store):
    _session(store)
    store.ingest_replay_events([{
        "span_id": f"{SID}:llm:1", "session_id": SID,
        "runtime": "claude_code", "kind": "llm.call", "ts": 50.0,
        "payload": {"text": "hi"},
    }])
    assert _row(store) == (None, None, None, None)


def test_sessions_table_route_row_exposes_the_mode(store, monkeypatch):
    import routes.sessions as rs

    _session(store)
    store.ingest_replay_events(
        [_mode(1, 100, "bypassPermissions", "danger-full-access")])
    monkeypatch.setattr(
        rs, "_fetch_sessions_table_rows",
        lambda limit=200: store.query_sessions_table(limit=limit))
    monkeypatch.setattr(rs, "_decorate_with_channel_context", lambda out: None)
    monkeypatch.setattr(rs, "_decorate_with_authority_counts", lambda out: None)
    row = [r for r in rs._try_local_store_sessions()["sessions"] if r["session_id"] == SID][0]
    assert row["mode_permission"] == "bypassPermissions"
    assert row["mode_sandbox"] == "danger-full-access"
    assert row["mode_collaboration"] == ""
