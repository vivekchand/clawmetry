"""Tests for the /api/sessions local-store fast path (epic #964 PR 3 of 3).

Same opt-in pattern as test_brain_local_fastpath.py:
- CLAWMETRY_LOCAL_STORE_READ=1 + populated store → returns from DuckDB
- Flag unset → falls through to legacy gateway/JSONL path
- Empty store → falls through (so fresh installs see normal data)
"""

from __future__ import annotations

import importlib

import pytest
from flask import Flask


@pytest.fixture
def app(tmp_path, monkeypatch):
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "events.duckdb"))
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_SECS", "0.05")
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_READ", "1")
    # Isolate the on-disk sessions dir so the unregistered-JSONL merge
    # (added 2026-05-13) doesn't surface random files from the dev's
    # ~/.openclaw workspace into these unit tests.
    empty_sessions = tmp_path / "sessions_empty"
    empty_sessions.mkdir()
    monkeypatch.setenv("OPENCLAW_SESSIONS_DIR", str(empty_sessions))
    import dashboard as _d
    monkeypatch.setattr(_d, "SESSIONS_DIR", str(empty_sessions), raising=False)

    import clawmetry.local_store as ls
    importlib.reload(ls)
    import routes.sessions as sessions_mod
    importlib.reload(sessions_mod)

    # Issue #1448: the historical 2026-05-11 timestamps these tests seed
    # fall outside the OSS 24h retention cap. Default this fixture to a Pro
    # user so the pre-cap aggregation/fastpath assertions still pass; the
    # cap-specific tests live in test_sessions_retention_cap.py and
    # monkeypatch ``_is_pro_user`` explicitly.
    monkeypatch.setattr(_d, "_is_pro_user", lambda: True)

    a = Flask(__name__)
    a.register_blueprint(sessions_mod.bp_sessions)
    yield a, ls
    try:
        ls.get_store().stop(flush=True)
    except Exception:
        pass


def test_sessions_fast_path_returns_local_rows(app):
    a, ls = app
    store = ls.get_store()
    store.ingest_session({
        "session_id": "sess-fast-A",
        "agent_type": "openclaw",
        "title": "Refactoring routes/sessions.py",
        "started_at": "2026-05-11T10:00:00Z",
        "last_active_at": "2026-05-11T10:30:00Z",
        "status": "active",
        "total_tokens": 12500,
        "cost_usd": 0.42,
        "message_count": 17,
        "metadata": {"channel": "telegram"},
    })
    store.ingest_session({
        "session_id": "sess-fast-B",
        "agent_type": "claude_code",
        "title": "Adding multi-agent schema",
        "started_at": "2026-05-11T09:00:00Z",
        "last_active_at": "2026-05-11T11:00:00Z",
        "status": "active",
        "total_tokens": 50000,
        "cost_usd": 1.7,
    })

    c = a.test_client()
    r = c.get("/api/sessions")
    assert r.status_code == 200
    body = r.get_json()
    assert body.get("_source") == "local_store"
    assert len(body["sessions"]) == 2
    by_id = {s["session_id"]: s for s in body["sessions"]}
    # Most-recent-first: B (11:00) before A (10:30)
    assert body["sessions"][0]["session_id"] == "sess-fast-B"
    assert by_id["sess-fast-A"]["agent_type"] == "openclaw"
    assert by_id["sess-fast-B"]["agent_type"] == "claude_code"
    assert by_id["sess-fast-A"]["channel"] == "telegram"
    assert by_id["sess-fast-A"]["total_cost"] == 0.42


def test_sessions_fast_path_falls_back_when_store_empty(app):
    """Empty store → fast path returns None → legacy path runs (which we
    can't easily exercise here, so we just verify no _source tag)."""
    a, _ls = app
    c = a.test_client()
    r = c.get("/api/sessions")
    # Falls through to gateway path (returns 500 in unit-test context with
    # no gateway, OR returns sessions if there's a workspace; either way
    # it's NOT tagged _source: local_store).
    body = r.get_json() or {}
    assert body.get("_source") != "local_store"


def test_sessions_fast_path_disabled_without_flag(tmp_path, monkeypatch):
    """No CLAWMETRY_LOCAL_STORE_READ → fast path never runs even with
    a populated store. Default = zero behavior change for existing deploys."""
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
        "title": "Should not appear",
        "started_at": "2026-05-11T10:00:00Z",
    })

    a = Flask(__name__)
    a.register_blueprint(sessions_mod.bp_sessions)
    r = a.test_client().get("/api/sessions")
    body = r.get_json() or {}
    assert body.get("_source") != "local_store"
    try:
        store.stop(flush=True)
    except Exception:
        pass


def test_sessions_api_discovers_unregistered(tmp_path, monkeypatch):
    """A `<uuid>.jsonl` dropped into the sessions dir but NOT yet registered
    in `sessions.json` (or any gateway / WS source) must still appear in
    `/api/sessions`. Regression for MOAT_E2E_REPORT_2026-05-13 root-cause #3:
    new sessions were invisible until OpenClaw's registrar caught up.
    """
    import json as _json

    # Isolate dashboard's SESSIONS_DIR onto a tmp path so we don't depend on
    # whatever the dev's machine has under ~/.openclaw.
    sessions_dir = tmp_path / "sessions"
    sessions_dir.mkdir()
    monkeypatch.setenv("OPENCLAW_SESSIONS_DIR", str(sessions_dir))

    # Disable both fast paths so the test exercises the JSONL-merge branch.
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_READ", "0")  # force legacy path

    # Import dashboard FIRST so module-level SESSIONS_DIR sees our env var.
    import dashboard as _d
    _d.SESSIONS_DIR = str(sessions_dir)

    # Stub gateway + WS-fallback to return nothing — forces the route into
    # the file-based path that the merge augments.
    monkeypatch.setattr(_d, "_gw_invoke", lambda *a, **kw: None)
    monkeypatch.setattr(_d, "_get_sessions", lambda: [])
    monkeypatch.setattr(_d, "_augment_sessions_with_burn", lambda s: s)

    # Drop a JSONL with no entry in sessions.json — simulates a brand-new
    # session whose registrar hasn't run yet.
    sid = "f00dface-1111-2222-3333-444455556666"
    jsonl = sessions_dir / f"{sid}.jsonl"
    jsonl.write_text(_json.dumps({
        "type": "session", "id": sid,
        "timestamp": "2026-05-13T10:00:00Z",
    }) + "\n")

    # Trajectory + deleted variants must NOT show up.
    (sessions_dir / f"{sid}.trajectory.jsonl").write_text("{}\n")
    (sessions_dir / "deadbeef-deleted.jsonl").write_text("{}\n")

    import routes.sessions as sessions_mod
    importlib.reload(sessions_mod)

    a = Flask(__name__)
    a.register_blueprint(sessions_mod.bp_sessions)
    r = a.test_client().get("/api/sessions")
    assert r.status_code == 200
    body = r.get_json() or {}
    sids = {s.get("sessionId") or s.get("session_id") for s in body.get("sessions", [])}
    assert sid in sids, f"unregistered JSONL not surfaced: got {sids}"

    # Find our row and assert the unregistered marker is set.
    row = next(
        s for s in body["sessions"]
        if (s.get("sessionId") or s.get("session_id")) == sid
    )
    assert row.get("displayName") == "(unregistered)"
    assert row.get("_source") == "filesystem_unregistered"

    # Trajectory / deleted variants stayed out.
    assert not any(".trajectory" in (sid_ or "") for sid_ in sids)
    assert not any("deleted" in (sid_ or "") for sid_ in sids)


def test_sessions_api_does_not_duplicate_registered(tmp_path, monkeypatch):
    """When a JSONL is registered AND on disk, the merge must NOT duplicate
    it — the registered row takes precedence (matches by sessionId / key).
    """
    sessions_dir = tmp_path / "sessions"
    sessions_dir.mkdir()
    monkeypatch.setenv("OPENCLAW_SESSIONS_DIR", str(sessions_dir))
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_READ", "0")  # force legacy path

    import dashboard as _d
    _d.SESSIONS_DIR = str(sessions_dir)

    sid = "deadbeef-aaaa-bbbb-cccc-dddddddddddd"
    (sessions_dir / f"{sid}.jsonl").write_text("{}\n")

    # Gateway returns the same session — merge must not add a second copy.
    monkeypatch.setattr(_d, "_gw_invoke", lambda *a, **kw: {
        "sessions": [{"sessionId": sid, "displayName": "Real Session", "key": sid}],
    })
    monkeypatch.setattr(_d, "_augment_sessions_with_burn", lambda s: s)

    import routes.sessions as sessions_mod
    importlib.reload(sessions_mod)

    a = Flask(__name__)
    a.register_blueprint(sessions_mod.bp_sessions)
    r = a.test_client().get("/api/sessions")
    body = r.get_json() or {}
    matches = [
        s for s in body["sessions"]
        if (s.get("sessionId") or s.get("session_id")) == sid
    ]
    assert len(matches) == 1, f"expected 1 row for {sid}, got {len(matches)}"
    assert matches[0]["displayName"] == "Real Session"
