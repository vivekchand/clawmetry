"""Brain error surfacing (Brain-visualizer adoption #3).

The store has carried per-tool-result error flags since ingest — family
adapters stamp ``data.extra.isError`` and the OpenClaw v3 mapper stamps
``data.is_error`` — but ``/api/brain-history`` dropped them, so the feed
showed a failed Bash call and a clean one identically (and the UI's ❌
ERROR icon was unreachable dead weight). These tests pin the mapper
contract: a real error becomes a first-class ``type: ERROR`` event with
``isError: true``; benign errors (downgraded at ingest) and clean results
stay ``TOOL_RESULT``.
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
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_BATCH", "5")
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_READ", "1")

    import clawmetry.local_store as ls
    importlib.reload(ls)
    import routes.brain as br
    importlib.reload(br)

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


def _ingest(store, i, data):
    store.ingest({
        "id": f"ev-err-{i}",
        "node_id": "agent+test",
        "agent_id": "main",
        "session_id": "claude_code:sess-err",
        "event_type": "tool_result",
        "ts": f"2026-05-11T12:00:0{i}Z",
        "data": data,
        "cost_usd": 0.0,
        "token_count": 0,
        "model": "",
    })


def test_error_flags_become_error_events(app):
    a, ls = app
    store = ls.get_store()
    # Family-adapter shape (Claude Code, Codex, …): flag under extra.isError.
    _ingest(store, 0, {"role": "toolResult", "content": "Exit code 1: boom",
                       "_runtime": "claude_code",
                       "extra": {"isError": True, "toolUseId": "t1"}})
    # OpenClaw v3 shape: flag at data.is_error (+ data.data mirror).
    _ingest(store, 1, {"output": "command not found", "is_error": True,
                       "data": {"output": "command not found", "is_error": True}})
    # Benign error, downgraded at ingest — must NOT resurface as ERROR.
    _ingest(store, 2, {"role": "toolResult", "content": "read guard tripped",
                       "_runtime": "claude_code", "benign_error": True,
                       "extra": {"isError": False, "toolUseId": "t3"}})
    # Clean result.
    _ingest(store, 3, {"role": "toolResult", "content": "21 passed, 0 failed",
                       "_runtime": "claude_code",
                       "extra": {"isError": False, "toolUseId": "t4"}})
    _wait_flush(store)

    c = a.test_client()
    r = c.get("/api/brain-history?limit=10")
    assert r.status_code == 200, r.get_data(as_text=True)[:300]
    body = r.get_json()
    assert body.get("_source") == "local_store"

    by_id = {ev["eventId"]: ev for ev in body["events"]}
    assert by_id["ev-err-0"]["type"] == "ERROR"
    assert by_id["ev-err-0"]["isError"] is True
    assert by_id["ev-err-1"]["type"] == "ERROR"
    assert by_id["ev-err-1"]["isError"] is True
    # "0 failed" in a clean result must not be flagged (text is never
    # inspected — only the stored structured flag counts).
    assert by_id["ev-err-3"]["type"] == "TOOL_RESULT"
    assert "isError" not in by_id["ev-err-3"]
    assert by_id["ev-err-2"]["type"] == "TOOL_RESULT"
    assert "isError" not in by_id["ev-err-2"]


def test_row_is_error_never_raises_on_junk(app):
    _a, _ls = app
    import routes.brain as br
    assert br._row_is_error({}) is False
    assert br._row_is_error({"data": None}) is False
    assert br._row_is_error({"data": "not a dict"}) is False
    assert br._row_is_error({"data": {"extra": "not a dict"}}) is False
    assert br._row_is_error({"data": {"extra": {"isError": True}}}) is True
    assert br._row_is_error({"data": {"is_error": True, "benign_error": True}}) is False
