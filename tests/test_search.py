"""Tests for LocalStore.query_search() — issue #2860.

Covers: title match, eval_reason match, case-insensitive match, miss,
model filter, status filter, and empty-query guard.
"""
from __future__ import annotations

import importlib
import time
import uuid

import pytest


@pytest.fixture
def store(tmp_path, monkeypatch):
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "events.duckdb"))
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_SECS", "0.05")
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_BATCH", "5")
    import clawmetry.local_store as ls
    importlib.reload(ls)
    s = ls.LocalStore()
    s.start()
    yield s
    s.stop(flush=True)


def _session(*, title, status="ended", agent_type="openclaw", session_id=None,
             last_active_at="2026-06-09T10:05:00Z"):
    return {
        "session_id":     session_id or str(uuid.uuid4()),
        "agent_type":     agent_type,
        "title":          title,
        "status":         status,
        "started_at":     "2026-06-09T10:00:00Z",
        "last_active_at": last_active_at,
    }


def _event(session_id, model="claude-opus-4-8"):
    return {
        "id":          str(uuid.uuid4()),
        "node_id":     "test-node",
        "agent_id":    "main",
        "session_id":  session_id,
        "event_type":  "assistant",
        "ts":          "2026-06-09T10:01:00Z",
        "model":       model,
        "cost_usd":    0.001,
        "token_count": 10,
    }


def _wait_flush(s, timeout=2.0):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if s.health()["ring_depth"] == 0:
            return
        time.sleep(0.02)


def test_title_match(store):
    sess = _session(title="debug file read loop issue")
    store.ingest_session(sess)
    rows = store.query_search(q="file read loop")
    assert len(rows) == 1
    assert rows[0]["session_id"] == sess["session_id"]


def test_eval_reason_match(store):
    sess = _session(title="unrelated title")
    store.ingest_session(sess)
    store.persist_eval_score(
        session_id=sess["session_id"],
        score=0.4,
        reason="agent stuck on permissions error",
        judge_model="test",
        scored_at=int(time.time() * 1000),
    )
    rows = store.query_search(q="permissions error")
    assert len(rows) == 1
    assert rows[0]["session_id"] == sess["session_id"]


def test_case_insensitive(store):
    sess = _session(title="Python Import Error")
    store.ingest_session(sess)
    assert store.query_search(q="python import") != []
    assert store.query_search(q="PYTHON IMPORT") != []


def test_no_match_returns_empty(store):
    sess = _session(title="write unit test")
    store.ingest_session(sess)
    rows = store.query_search(q="xyzzy_nonexistent_token_42")
    assert rows == []


def test_empty_query_returns_empty(store):
    store.ingest_session(_session(title="some session"))
    assert store.query_search(q="") == []
    assert store.query_search(q="   ") == []


def test_model_filter(store):
    sid_opus = str(uuid.uuid4())
    sid_haiku = str(uuid.uuid4())
    store.ingest_session(_session(title="deploy script", session_id=sid_opus))
    store.ingest_session(_session(title="deploy again", session_id=sid_haiku))
    store.ingest(_event(sid_opus, model="claude-opus-4-8"))
    store.ingest(_event(sid_haiku, model="claude-haiku-4-5"))
    _wait_flush(store)
    rows = store.query_search(q="deploy", model="opus")
    sids = {r["session_id"] for r in rows}
    assert sid_opus in sids
    assert sid_haiku not in sids


def test_status_filter(store):
    sid_ended = str(uuid.uuid4())
    sid_active = str(uuid.uuid4())
    store.ingest_session(_session(title="same title task", session_id=sid_ended,
                                  status="ended"))
    store.ingest_session(_session(title="same title task", session_id=sid_active,
                                  status="active"))
    rows = store.query_search(q="same title task", status="ended")
    sids = {r["session_id"] for r in rows}
    assert sid_ended in sids
    assert sid_active not in sids


def test_result_fields(store):
    sess = _session(title="check result shape")
    store.ingest_session(sess)
    store.persist_eval_score(
        session_id=sess["session_id"],
        score=0.9,
        reason="all good",
        judge_model="test",
        scored_at=int(time.time() * 1000),
    )
    rows = store.query_search(q="result shape")
    assert len(rows) == 1
    row = rows[0]
    for key in ("session_id", "agent_type", "title", "started_at",
                "last_active_at", "status", "cost_usd", "total_tokens",
                "outcome", "eval_score", "eval_reason"):
        assert key in row, f"missing key: {key}"
    assert row["title"] == "check result shape"
    assert row["eval_reason"] == "all good"
