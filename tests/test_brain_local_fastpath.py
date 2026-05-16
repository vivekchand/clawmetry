"""Tests for epic #964 phase 1b — local-store fast path on /api/brain-history.

The fast path is opt-in via CLAWMETRY_LOCAL_STORE_READ=1 so the legacy
JSONL parser stays the default until ≥80% adoption (epic's gate).
"""

from __future__ import annotations

import importlib
import json
import time

import pytest
from flask import Flask


@pytest.fixture
def app(tmp_path, monkeypatch):
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "events.duckdb"))
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_SECS", "0.05")
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_BATCH", "5")
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_READ", "1")

    import clawmetry.local_store as ls
    importlib.reload(ls)
    import routes.brain as br
    importlib.reload(br)

    # Pre-#1448 fixtures seed historical timestamps that fall outside the
    # OSS 24h retention cap. Default to a Pro user so existing assertions
    # still pass; the cap tests monkeypatch ``_is_pro_user`` explicitly.
    import dashboard as _d
    monkeypatch.setattr(_d, "_is_pro_user", lambda: True)

    a = Flask(__name__)
    a.register_blueprint(br.bp_brain)
    yield a, ls
    try:
        ls.get_store().stop(flush=True)
    except Exception:
        pass


def _wait_flush(store, t=2.0):
    deadline = time.monotonic() + t
    while time.monotonic() < deadline:
        if store.health()["ring_depth"] == 0:
            return
        time.sleep(0.02)


def test_brain_fast_path_returns_local_store_events(app):
    a, ls = app
    store = ls.get_store()
    for i in range(5):
        store.ingest({
            "id": f"ev-fast-{i}",
            "node_id": "agent+test",
            "agent_id": "main",
            "session_id": "sess-fast",
            "event_type": "tool_call",
            "ts": f"2026-05-11T12:00:0{i}Z",
            "data": {"tool": "Bash", "input": f"echo hello-{i}"},
            "cost_usd": 0.001,
            "token_count": 10,
            "model": "claude-opus-4-7",
        })
    _wait_flush(store)

    c = a.test_client()
    r = c.get("/api/brain-history?limit=10")
    assert r.status_code == 200, r.get_data(as_text=True)[:300]
    body = r.get_json()
    # The fast path tags responses so we can verify no JSONL fallback ran.
    assert body.get("_source") == "local_store"
    assert body["count"] == 5
    types = {ev["type"] for ev in body["events"]}
    assert "TOOL_CALL" in types
    # session_id maps to both src and sessionId
    assert all(ev["sessionId"] == "sess-fast" for ev in body["events"])


def test_brain_fast_path_falls_back_when_store_empty(app):
    """Empty store → fast path returns None so JSONL parser runs.
    We can't easily exercise the full JSONL parser in unit tests
    (needs ~/.openclaw fixture), so we just verify the fast path
    *defers* by returning the JSONL endpoint's typical shape (no
    `_source: local_store` tag)."""
    a, _ls = app
    c = a.test_client()
    r = c.get("/api/brain-history?limit=10")
    assert r.status_code == 200
    body = r.get_json()
    # Fast path returned None → fell through to legacy parser, which
    # does NOT add the _source tag.
    assert body.get("_source") != "local_store"


def test_brain_fast_path_disabled_without_env_flag(tmp_path, monkeypatch):
    """No CLAWMETRY_LOCAL_STORE_READ → fast path never runs, even with
    populated store. Defaults to legacy JSONL behavior so existing
    deploys see zero change without explicit opt-in."""
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "events.duckdb"))
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_SECS", "0.05")
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_READ", "0")  # force legacy path

    import clawmetry.local_store as ls
    importlib.reload(ls)
    import routes.brain as br
    importlib.reload(br)

    store = ls.get_store()
    store.ingest({
        "id": "ev-noflag",
        "node_id": "agent+test", "agent_id": "main", "session_id": "sess-x",
        "event_type": "tool_call", "ts": "2026-05-11T12:00:00Z",
        "data": {"tool": "Bash"}, "cost_usd": 0.001, "token_count": 5,
        "model": "claude-opus-4-7",
    })
    _wait_flush(store)

    a = Flask(__name__)
    a.register_blueprint(br.bp_brain)
    r = a.test_client().get("/api/brain-history?limit=10")
    body = r.get_json()
    assert body.get("_source") != "local_store"
    try:
        store.stop(flush=True)
    except Exception:
        pass


# ── Retention cap (issue #1448 surface 3) ───────────────────────────────────
#
# OSS / Cloud-Free users get capped to the last 24h of events on
# /api/brain-history. Cloud-Pro users (gated by ``dashboard._is_pro_user``)
# bypass the cap. The response always carries ``capped_at_24h`` so the UI
# can render the upgrade CTA above the brain stream.


def _seed_old_and_recent_events(store):
    """One ancient event (8 days old) + one fresh event (now)."""
    import datetime as _dt
    now = _dt.datetime.now(_dt.timezone.utc)
    old_ts = (now - _dt.timedelta(days=8)).strftime("%Y-%m-%dT%H:%M:%SZ")
    new_ts = (now - _dt.timedelta(minutes=5)).strftime("%Y-%m-%dT%H:%M:%SZ")
    store.ingest({
        "id": "ev-old", "node_id": "n1", "agent_id": "main",
        "session_id": "sess-old", "event_type": "tool_call",
        "ts": old_ts, "data": {"tool": "Bash", "input": "echo ancient"},
        "cost_usd": 0.01, "token_count": 10, "model": "claude-opus-4-7",
    })
    store.ingest({
        "id": "ev-new", "node_id": "n1", "agent_id": "main",
        "session_id": "sess-new", "event_type": "tool_call",
        "ts": new_ts, "data": {"tool": "Bash", "input": "echo fresh"},
        "cost_usd": 0.01, "token_count": 10, "model": "claude-opus-4-7",
    })
    _wait_flush(store)


def test_api_brain_history_caps_24h_for_free(app, monkeypatch):
    a, ls = app
    _seed_old_and_recent_events(ls.get_store())
    import dashboard as _d
    monkeypatch.setattr(_d, "_is_pro_user", lambda: False)

    r = a.test_client().get("/api/brain-history?limit=10")
    assert r.status_code == 200, r.get_data(as_text=True)[:300]
    body = r.get_json()
    assert body.get("capped_at_24h") is True
    sids = {ev["sessionId"] for ev in body["events"]}
    # 8-day-old event must be excluded; only the fresh one survives.
    assert sids == {"sess-new"}


def test_api_brain_history_no_cap_for_pro(app, monkeypatch):
    a, ls = app
    _seed_old_and_recent_events(ls.get_store())
    import dashboard as _d
    monkeypatch.setattr(_d, "_is_pro_user", lambda: True)

    r = a.test_client().get("/api/brain-history?limit=10")
    body = r.get_json()
    assert body.get("capped_at_24h") is False
    sids = {ev["sessionId"] for ev in body["events"]}
    # Pro users see the full history including the 8-day-old event.
    assert sids == {"sess-old", "sess-new"}
