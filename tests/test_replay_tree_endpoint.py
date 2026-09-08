"""Tests for /api/replay-tree/<sid> + query_replay_events (#4813 part 2).

Foundation tests: query method reads rows correctly, endpoint returns
the empty shape when no rows exist, and _build_replay_tree correctly
folds turns / delegations / workflows / approvals / mode changes from
a flat canonical event stream.
"""

from __future__ import annotations

import json
import time

import pytest


# ── query_replay_events (store method) ───────────────────────────────────


@pytest.fixture
def store(tmp_path, monkeypatch):
    """Fresh writable LocalStore per test.

    Skips the get_store() singleton (which returns a ProxyStore forwarding
    through the real daemon on developer machines) — we want a direct
    LocalStore for isolated schema tests. DB_PATH is captured at import
    time, so we monkeypatch the module attribute rather than the env var.
    """
    from pathlib import Path
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


def test_query_replay_events_empty_for_unknown_session(store):
    """Fresh store with no rows → empty list, not an error."""
    assert store.query_replay_events(session_id="does-not-exist") == []


def test_query_replay_events_roundtrips_row_with_blobs(store):
    """Insert one row directly, read it back, verify blobs decode to dicts."""
    from clawmetry.replay_schema import KIND_AGENT_SPAWN

    with store._write_lock:
        store._conn.execute(
            """
            INSERT INTO replay_events
              (span_id, parent_span_id, session_id, runtime, kind, ts,
               payload, mode, approval, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                "span-A", None, "sess-1", "claude_code",
                KIND_AGENT_SPAWN, 100.0,
                json.dumps({"prompt": "hi"}).encode(),
                None, None,
                int(time.time() * 1000),
            ],
        )
    rows = store.query_replay_events(session_id="sess-1")
    assert len(rows) == 1
    r = rows[0]
    assert r["span_id"] == "span-A"
    assert r["kind"] == KIND_AGENT_SPAWN
    assert r["payload"] == {"prompt": "hi"}   # decoded to dict
    assert r["mode"] is None
    assert r["approval"] is None


# ── _build_replay_tree (pure grouping fn) ────────────────────────────────


def _e(**kw):
    """Compact event builder with sensible defaults."""
    return {
        "span_id": kw.get("span_id"),
        "parent_span_id": kw.get("parent_span_id"),
        "session_id": kw.get("session_id", "sess-1"),
        "runtime": kw.get("runtime", "claude_code"),
        "kind": kw["kind"],
        "ts": kw.get("ts", 0.0),
        "payload": kw.get("payload"),
        "mode": kw.get("mode"),
        "approval": kw.get("approval"),
    }


def test_build_tree_empty_rows_returns_honest_shape():
    from routes.sessions import _build_replay_tree

    out = _build_replay_tree("sess-x", [])
    assert out == {
        "session_id": "sess-x",
        "runtime": None,
        "mode": None,
        "turns": [],
        "workflows": [],
        "row_count": 0,
    }


def test_build_tree_groups_events_by_turn():
    from routes.sessions import _build_replay_tree

    rows = [
        _e(span_id="u1", kind="llm.call", ts=1.0),
        _e(span_id="a1", kind="llm.response", ts=2.0, parent_span_id="u1"),
        _e(span_id="t1", kind="tool.call", ts=3.0, parent_span_id="a1"),
        _e(span_id="tr1", kind="tool.result", ts=4.0, parent_span_id="t1"),
        _e(span_id="u2", kind="llm.call", ts=5.0),
        _e(span_id="a2", kind="llm.response", ts=6.0, parent_span_id="u2"),
    ]
    out = _build_replay_tree("s1", rows)
    assert len(out["turns"]) == 2
    assert out["turns"][0]["turn_id"] == "u1"
    assert len(out["turns"][0]["events"]) == 4
    assert out["turns"][1]["turn_id"] == "u2"
    assert len(out["turns"][1]["events"]) == 2
    assert out["runtime"] == "claude_code"


def test_build_tree_captures_latest_mode():
    from routes.sessions import _build_replay_tree

    rows = [
        _e(span_id="m1", kind="mode.changed", ts=0.0,
           mode={"permission": "default"}),
        _e(span_id="u1", kind="llm.call", ts=1.0),
        _e(span_id="m2", kind="mode.changed", ts=2.0,
           mode={"permission": "bypassPermissions"}),
    ]
    out = _build_replay_tree("s1", rows)
    assert out["mode"] == {"permission": "bypassPermissions"}


def test_build_tree_folds_delegations_under_spawn():
    from routes.sessions import _build_replay_tree

    rows = [
        _e(span_id="u1", kind="llm.call", ts=1.0),
        _e(span_id="a1", kind="llm.response", ts=2.0, parent_span_id="u1"),
        _e(span_id="spawn1", kind="agent.spawn", ts=3.0, parent_span_id="a1"),
        # child events attached under spawn1 via parent_span_id
        _e(span_id="child-u1", kind="llm.call", ts=4.0, parent_span_id="spawn1"),
        _e(span_id="child-a1", kind="llm.response", ts=5.0, parent_span_id="spawn1"),
    ]
    out = _build_replay_tree("s1", rows)
    assert len(out["turns"]) == 1
    turn = out["turns"][0]
    assert len(turn["delegations"]) == 1
    d = turn["delegations"][0]
    assert d["span_id"] == "spawn1"
    assert len(d["events"]) == 2
    assert [e["span_id"] for e in d["events"]] == ["child-u1", "child-a1"]


def test_build_tree_groups_workflow_events():
    from routes.sessions import _build_replay_tree

    rows = [
        _e(span_id="wf1", kind="workflow.start", ts=0.0),
        _e(span_id="s1", kind="workflow.stage", ts=1.0, parent_span_id="wf1"),
        _e(span_id="s2", kind="workflow.stage", ts=2.0, parent_span_id="wf1"),
        _e(span_id="wfe", kind="workflow.end", ts=3.0, parent_span_id="wf1"),
    ]
    out = _build_replay_tree("s1", rows)
    assert len(out["workflows"]) == 1
    wf = out["workflows"][0]
    assert len(wf["events"]) == 4


def test_build_tree_attaches_approvals_to_gated_event():
    from routes.sessions import _build_replay_tree

    rows = [
        _e(span_id="u1", kind="llm.call", ts=1.0),
        _e(span_id="a1", kind="llm.response", ts=2.0, parent_span_id="u1"),
        _e(span_id="t1", kind="tool.call", ts=3.0, parent_span_id="a1"),
        _e(span_id="ap1", kind="approval.requested", ts=3.1,
           parent_span_id="t1",
           approval={"status": "requested"}),
        _e(span_id="ap2", kind="approval.decided", ts=3.2,
           parent_span_id="t1",
           approval={"status": "approved", "resolver": "user"}),
        _e(span_id="tr1", kind="tool.result", ts=4.0, parent_span_id="t1"),
    ]
    out = _build_replay_tree("s1", rows)
    assert len(out["turns"]) == 1
    assert len(out["turns"][0]["approvals"]) == 2


def test_build_tree_synthetic_turn_zero_when_events_precede_first_call():
    from routes.sessions import _build_replay_tree

    rows = [
        _e(span_id="sys", kind="thinking", ts=0.0),
        _e(span_id="u1", kind="llm.call", ts=1.0),
    ]
    out = _build_replay_tree("s1", rows)
    assert len(out["turns"]) == 2
    assert out["turns"][0]["turn_id"] == "turn-0"


# ── endpoint honesty: empty session returns valid empty shape ────────────


def test_endpoint_returns_empty_shape_for_unknown_session(store, monkeypatch):
    """No replay_events for the session → honest empty shape, HTTP 200.
    Guards against the 'no dead UI' FLYWHEEL rule (§0a.4).

    Uses a minimal Flask app with just bp_sessions registered — importing
    dashboard.app doesn't register blueprints (they're registered inside
    main() at first-run), so we scaffold the smallest surface that hosts
    the /api/replay-tree route.
    """
    from flask import Flask
    from routes.sessions import bp_sessions
    from clawmetry import local_store as ls

    # Force _ls_call's daemon-proxy to miss so it falls back to the
    # direct-open path against our tmp store — otherwise it'd hit the
    # real ~/.clawmetry daemon on a developer machine.
    monkeypatch.setattr(
        "routes.local_query.local_store_via_daemon",
        lambda *a, **kw: None,
    )
    monkeypatch.setattr(ls, "get_store", lambda read_only=False: store)

    app = Flask(__name__)
    app.register_blueprint(bp_sessions)
    client = app.test_client()

    r = client.get("/api/replay-tree/sess-nope")
    assert r.status_code == 200
    body = r.get_json()
    assert body["session_id"] == "sess-nope"
    assert body["turns"] == []
    assert body["workflows"] == []
    assert body["row_count"] == 0
