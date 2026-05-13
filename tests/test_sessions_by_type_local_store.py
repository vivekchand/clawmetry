"""Tests for the /api/sessions/by-type local-store fast path
(epic #964 — engineer-3 follow-up to test_sessions_local_fastpath.py).

Same opt-in pattern as the /api/sessions fast path:
- CLAWMETRY_LOCAL_STORE_READ=1 + populated store → returns from DuckDB
- ?type=<filter> narrows the sessions list (counts always cover all rows)
- Flag unset → falls through to legacy gateway/JSONL path
- Empty store → falls through (so fresh installs see normal data)
"""

from __future__ import annotations

import importlib

import pytest
from flask import Flask


# All four buckets the legacy by-type handler reports.
_TYPES = ("main", "heartbeat", "user", "sub-agent")


def _seed_one_of_each(store):
    """Insert one session of each session_type via metadata.session_type."""
    base_ts = "2026-05-11T10:"
    rows = [
        # session_type set explicitly via metadata so we don't depend on
        # _infer_session_type() to classify the seed data.
        ("sess-main",      "Working on routes refactor",
         {"session_type": "main"}),
        ("sess-heartbeat", "heartbeat ping",
         {"session_type": "heartbeat"}),
        ("sess-user",      "Telegram chat with vivek",
         {"session_type": "user", "channel": "telegram"}),
        ("sess-subagent",  "Sub-agent: code-review",
         {"session_type": "sub-agent", "kind": "subagent"}),
    ]
    for i, (sid, title, meta) in enumerate(rows):
        store.ingest_session({
            "session_id": sid,
            "agent_type": "openclaw",
            "title": title,
            # Stagger last_active_at so most-recent-first ordering is stable.
            "started_at":     f"{base_ts}{10 + i:02d}:00Z",
            "last_active_at": f"{base_ts}{30 + i:02d}:00Z",
            "status": "active",
            "total_tokens": 1000 * (i + 1),
            "cost_usd": 0.10 * (i + 1),
            "message_count": i + 1,
            "metadata": meta,
        })


@pytest.fixture
def app(tmp_path, monkeypatch):
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "events.duckdb"))
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_SECS", "0.05")
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_READ", "1")

    import clawmetry.local_store as ls
    importlib.reload(ls)
    import routes.sessions as sessions_mod
    importlib.reload(sessions_mod)

    a = Flask(__name__)
    a.register_blueprint(sessions_mod.bp_sessions)
    yield a, ls
    try:
        ls.get_store().stop(flush=True)
    except Exception:
        pass


def test_by_type_no_filter_returns_all_with_counts(app):
    """No ?type → all 4 sessions returned, counts dict balances."""
    a, ls = app
    _seed_one_of_each(ls.get_store())

    r = a.test_client().get("/api/sessions/by-type")
    assert r.status_code == 200
    body = r.get_json()
    assert body.get("_source") == "local_store"
    assert len(body["sessions"]) == 4

    counts = body["counts"]
    assert counts["main"] == 1
    assert counts["heartbeat"] == 1
    assert counts["user"] == 1
    assert counts["sub-agent"] == 1
    assert counts["total"] == 4
    # Counts must always sum to total (legacy contract — counts cover every row).
    assert sum(counts[t] for t in _TYPES) == counts["total"]


@pytest.mark.parametrize("type_filter,expected_sid", [
    ("main",      "sess-main"),
    ("heartbeat", "sess-heartbeat"),
    ("user",      "sess-user"),
    ("sub-agent", "sess-subagent"),
])
def test_by_type_filter_narrows_sessions_but_counts_unchanged(
    app, type_filter, expected_sid
):
    """?type=X → sessions narrows to that bucket, counts still cover all 4."""
    a, ls = app
    _seed_one_of_each(ls.get_store())

    r = a.test_client().get(f"/api/sessions/by-type?type={type_filter}")
    assert r.status_code == 200
    body = r.get_json()
    assert body.get("_source") == "local_store"

    sessions = body["sessions"]
    assert len(sessions) == 1
    assert sessions[0]["session_id"] == expected_sid
    assert sessions[0]["session_type"] == type_filter

    # counts dict must still report the full population, not the filtered view.
    counts = body["counts"]
    assert counts["total"] == 4
    assert all(counts[t] == 1 for t in _TYPES)


def test_by_type_unknown_filter_returns_empty_sessions(app):
    """?type=<bogus> → empty sessions list, counts still complete."""
    a, ls = app
    _seed_one_of_each(ls.get_store())

    r = a.test_client().get("/api/sessions/by-type?type=does-not-exist")
    assert r.status_code == 200
    body = r.get_json()
    assert body["sessions"] == []
    assert body["counts"]["total"] == 4


def test_by_type_falls_back_when_store_empty(app):
    """Empty store → fast path returns None → legacy path runs.

    We can't easily exercise the legacy path in a unit-test (no gateway,
    no workspace), so we just verify the response is NOT tagged as
    served from local_store.
    """
    a, _ls = app
    body = a.test_client().get("/api/sessions/by-type").get_json() or {}
    assert body.get("_source") != "local_store"


def test_by_type_disabled_without_flag(tmp_path, monkeypatch):
    """No CLAWMETRY_LOCAL_STORE_READ → fast path never runs even with a
    populated store. Default = zero behaviour change for existing deploys."""
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "events.duckdb"))
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_SECS", "0.05")
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_READ", "0")  # force legacy path

    import clawmetry.local_store as ls
    importlib.reload(ls)
    import routes.sessions as sessions_mod
    importlib.reload(sessions_mod)

    store = ls.get_store()
    store.ingest_session({
        "session_id": "sess-noflag",
        "agent_type": "openclaw",
        "title": "Should not appear via fast path",
        "started_at":     "2026-05-11T10:00:00Z",
        "last_active_at": "2026-05-11T10:00:00Z",
        "metadata": {"session_type": "main"},
    })

    a = Flask(__name__)
    a.register_blueprint(sessions_mod.bp_sessions)
    body = a.test_client().get("/api/sessions/by-type").get_json() or {}
    assert body.get("_source") != "local_store"
    try:
        store.stop(flush=True)
    except Exception:
        pass
