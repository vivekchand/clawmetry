"""Tests for the /api/sessions 24h retention cap (issue #1448 surface 1/4).

PR #1445 capped /api/flow/runs at 24h for OSS / Cloud-Free users. The
pre-merge product review (issue #1448) flagged that Sessions, Usage,
Brain-history and Local-events all leaked the same retention upsell. This
file covers the Sessions slice.

Mirrors the OSS-capped / Pro-bypass pattern from
tests/test_flow_runs_endpoint.py: a Pro user keeps full history, an OSS
(non-Pro) caller only sees sessions whose last activity falls inside the
24h window AND the response carries ``capped_at_24h: true`` so the UI
can render the upgrade CTA.
"""

from __future__ import annotations

import importlib
import time

import pytest
from flask import Flask


@pytest.fixture
def app(tmp_path, monkeypatch):
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "events.duckdb"))
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_SECS", "0.05")
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_READ", "1")
    # Isolate sessions dir so the unregistered-JSONL merge doesn't drag in
    # rows from the dev's local ~/.openclaw workspace.
    empty_sessions = tmp_path / "sessions_empty"
    empty_sessions.mkdir()
    monkeypatch.setenv("OPENCLAW_SESSIONS_DIR", str(empty_sessions))
    import dashboard as _d
    monkeypatch.setattr(_d, "SESSIONS_DIR", str(empty_sessions), raising=False)

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


def _seed_old_and_recent(store):
    """One ancient session (8 days back) + one fresh session (5 min back).

    The local-store fast path returns ISO-8601 last_active_at strings, so
    that's what we seed; the retention helper handles both ISO and
    epoch-millis variants.
    """
    import datetime as _dt
    now = _dt.datetime.now(_dt.timezone.utc)
    old_ts = (now - _dt.timedelta(days=8)).strftime("%Y-%m-%dT%H:%M:%SZ")
    new_ts = (now - _dt.timedelta(minutes=5)).strftime("%Y-%m-%dT%H:%M:%SZ")
    store.ingest_session({
        "session_id": "sess-old",
        "agent_type": "openclaw",
        "title": "Old session",
        "started_at": old_ts,
        "last_active_at": old_ts,
        "status": "ended",
        "total_tokens": 100,
        "cost_usd": 0.1,
    })
    store.ingest_session({
        "session_id": "sess-new",
        "agent_type": "openclaw",
        "title": "Fresh session",
        "started_at": new_ts,
        "last_active_at": new_ts,
        "status": "active",
        "total_tokens": 50,
        "cost_usd": 0.05,
    })
    # Give the background flusher a beat to land both rows on disk.
    time.sleep(0.2)


def test_api_sessions_caps_24h_for_free_users(app, monkeypatch):
    a, ls = app
    _seed_old_and_recent(ls.get_store())
    import dashboard as _d
    monkeypatch.setattr(_d, "_is_pro_user", lambda: False)

    r = a.test_client().get("/api/sessions")
    assert r.status_code == 200, r.get_data(as_text=True)[:300]
    body = r.get_json()
    assert body["capped_at_24h"] is True
    sids = {s["session_id"] for s in body["sessions"]}
    # 8-day-old session must be dropped; fresh session stays visible.
    assert sids == {"sess-new"}


def test_api_sessions_no_cap_for_pro_users(app, monkeypatch):
    a, ls = app
    _seed_old_and_recent(ls.get_store())
    import dashboard as _d
    monkeypatch.setattr(_d, "_is_pro_user", lambda: True)

    r = a.test_client().get("/api/sessions")
    assert r.status_code == 200, r.get_data(as_text=True)[:300]
    body = r.get_json()
    assert body["capped_at_24h"] is False
    sids = {s["session_id"] for s in body["sessions"]}
    # Pro users keep full history including the 8-day-old session.
    assert sids == {"sess-old", "sess-new"}
