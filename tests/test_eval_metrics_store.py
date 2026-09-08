"""``eval_metrics`` table round-trip + scheduler-query tests (#2862).

One row per (session, metric), latest-only upsert; ``engine`` labels who
computed the verdict. ``query_sessions_missing_eval_metrics`` drives the
daemon's deterministic-checks tick.
"""
from __future__ import annotations

import importlib
import os
import sys
from datetime import datetime, timezone

import pytest

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)


@pytest.fixture
def fresh_store(tmp_path, monkeypatch):
    monkeypatch.setenv(
        "CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "events.duckdb")
    )
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_SECS", "0.05")
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_BATCH", "1")

    sys.modules.pop("clawmetry.local_store", None)
    import clawmetry.local_store as ls
    importlib.reload(ls)

    # A live daemon on the dev box would otherwise make get_store() return
    # the HTTP proxy (whose old daemon lacks the new methods). Tests own
    # their tmp DB, so claim the writer like the daemon does.
    ls.mark_writer_owner()
    store = ls.get_store()
    yield ls, store

    try:
        store.stop(flush=False)
    except Exception:
        pass


def _now_iso():
    return datetime.now(timezone.utc).isoformat()


def _seed_session(store, sid, **kw):
    row = {
        "session_id": sid,
        "agent_type": "claude_code",
        "status": "completed",
        "total_tokens": 1200,
        "last_active_at": _now_iso(),
        "started_at": _now_iso(),
    }
    row.update(kw)
    store.ingest_session(row)


def test_persist_and_query_round_trip(fresh_store):
    _, store = fresh_store
    store.persist_eval_metric(
        session_id="s1", metric_slug="no-tool-errors", score=1.0,
        passed=True, reason="No tool/turn errors recorded.",
        detail='{"n": 3}', engine="builtin", scored_at=1754000000000,
    )
    rows = store.query_eval_metrics(session_id="s1")
    assert len(rows) == 1
    r = rows[0]
    assert r["metric_slug"] == "no-tool-errors"
    assert r["score"] == 1.0
    assert r["passed"] is True
    assert r["engine"] == "builtin"
    assert r["detail"] == '{"n": 3}'
    assert r["scored_at"] == 1754000000000


def test_upsert_is_latest_only(fresh_store):
    _, store = fresh_store
    for score, passed in [(1.0, True), (0.0, False)]:
        store.persist_eval_metric(
            session_id="s1", metric_slug="no-tool-errors", score=score,
            passed=passed, reason="r", engine="builtin",
        )
    rows = store.query_eval_metrics(session_id="s1")
    assert len(rows) == 1
    assert rows[0]["score"] == 0.0 and rows[0]["passed"] is False


def test_query_filters(fresh_store):
    _, store = fresh_store
    store.persist_eval_metric(session_id="s1", metric_slug="a", score=1.0,
                              passed=True, reason="", engine="builtin")
    store.persist_eval_metric(session_id="s1", metric_slug="b", score=0.0,
                              passed=False, reason="", engine="deepeval")
    store.persist_eval_metric(session_id="s2", metric_slug="a", score=0.5,
                              passed=None, reason="", engine="builtin")
    assert len(store.query_eval_metrics(session_id="s1")) == 2
    assert len(store.query_eval_metrics(metric_slug="a")) == 2
    only = store.query_eval_metrics(session_id="s1", metric_slug="b")
    assert len(only) == 1 and only[0]["engine"] == "deepeval"


def test_missing_metrics_query_and_engine_isolation(fresh_store):
    _, store = fresh_store
    _seed_session(store, "done-unchecked")
    _seed_session(store, "done-checked")
    _seed_session(store, "inflight", status="active", ended_at=None)
    _seed_session(store, "empty", total_tokens=0)
    store.persist_eval_metric(session_id="done-checked", metric_slug="no-tool-errors",
                              score=1.0, passed=True, reason="", engine="builtin")
    # A different engine's verdict must NOT satisfy the builtin pass.
    store.persist_eval_metric(session_id="done-unchecked", metric_slug="answer-quality-geval",
                              score=0.9, passed=True, reason="", engine="deepeval")

    pending = store.query_sessions_missing_eval_metrics(engine="builtin", limit=10)
    sids = {r["session_id"] for r in pending}
    assert "done-unchecked" in sids
    assert "done-checked" not in sids       # already has a builtin row
    assert "inflight" not in sids           # still mutating
    assert "empty" not in sids              # trivial


def test_persist_never_raises_on_bad_input(fresh_store):
    _, store = fresh_store
    store.persist_eval_metric(session_id="", metric_slug="x", score=None,
                              passed=None, reason="", engine="builtin")
    store.persist_eval_metric(session_id="s", metric_slug="", score=None,
                              passed=None, reason="", engine="builtin")
    assert store.query_eval_metrics() == []


def test_deterministic_tick_scores_pending_sessions(fresh_store, monkeypatch):
    """End-to-end scheduler pass on real stored shapes: seed a completed
    session + its events, run the daemon tick, assert a builtin verdict
    landed and the session left the pending set."""
    ls, store = fresh_store
    _seed_session(store, "tick-sess")
    store.ingest({
        "id": "ev-1",
        "node_id": "n1",
        "session_id": "tick-sess",
        "event_type": "tool_call",
        "ts": _now_iso(),
        "data": {
            "_runtime": "claude_code",
            "content": "",
            "tool_calls": "[{'id': 't1', 'input': {'command': 'ls'}, 'name': 'Bash'}]",
            "tool_name": "Bash",
        },
    })
    store.ingest({
        "id": "ev-2",
        "node_id": "n1",
        "session_id": "tick-sess",
        "event_type": "tool_result",
        "ts": _now_iso(),
        "data": {"_runtime": "claude_code", "content": "ok",
                 "extra": "{'isError': False, 'toolUseId': 't1'}"},
    })
    store._flush_now()

    from clawmetry import sync
    monkeypatch.setattr(sync, "DETERMINISTIC_CHECKS", ["no-tool-errors"])
    touched = sync._run_deterministic_checks_tick()
    assert touched == 1

    rows = store.query_eval_metrics(session_id="tick-sess")
    assert len(rows) == 1
    assert rows[0]["metric_slug"] == "no-tool-errors"
    assert rows[0]["passed"] is True and rows[0]["engine"] == "builtin"
    # Second tick: nothing pending anymore.
    assert sync._run_deterministic_checks_tick() == 0


def test_daemon_proxy_allowlist_carries_metric_methods():
    """The dashboard reaches the store only through the daemon proxy;
    a method missing from the allowlist silently returns None there."""
    from routes import local_query
    allowed = local_query._DAEMON_METHODS
    for m in ("persist_eval_metric", "query_eval_metrics",
              "query_sessions_missing_eval_metrics"):
        assert m in allowed, f"{m} missing from daemon-proxy allowlist"
