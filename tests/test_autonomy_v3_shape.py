"""Silent-zero regression test for /api/autonomy on real OpenClaw v3 installs.

Bug class (6th instance — 2026-05-18): the fast path in
``routes/autonomy.py`` queried only ``event_type="message"``. Real v3 writes
user turns as ``prompt.submitted``; Claude Code writes ``user``. Result:
0 rows on real installs → Overview widget blank. See
``feedback_synthetic_tests_missed_real_event_shape.md``.
"""

from __future__ import annotations

import importlib
import time
from datetime import datetime, timezone

import pytest
from flask import Flask


def _iso(s: float) -> str:
    return datetime.fromtimestamp(s, tz=timezone.utc).isoformat()


def _wait_flush(store, t=2.0):
    deadline = time.monotonic() + t
    while time.monotonic() < deadline:
        if store.health()["ring_depth"] == 0:
            return
        time.sleep(0.02)


@pytest.fixture
def autonomy_app(tmp_path, monkeypatch):
    """Flask app + tmp DuckDB with daemon proxy short-circuited."""
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "events.duckdb"))
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_SECS", "0.05")
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_BATCH", "1")
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_READ", "1")
    import clawmetry.local_store as ls
    importlib.reload(ls)
    import routes.local_query as lq
    importlib.reload(lq)
    monkeypatch.setattr(lq, "local_store_via_daemon", lambda *a, **k: None)
    monkeypatch.setattr(lq, "_read_discovery", lambda: None)
    monkeypatch.setattr(lq, "_cached_discovery", lambda: None)
    import routes.autonomy as aut
    importlib.reload(aut)
    aut._AUTONOMY_CACHE["data"] = None
    aut._AUTONOMY_CACHE["ts"] = 0.0
    a = Flask(__name__)
    a.register_blueprint(aut.bp_autonomy)
    yield a, ls
    try:
        ls.get_store().stop(flush=True)
    except Exception:
        pass


def _ingest(store, *, eid, sid, et, ts, data):
    store.ingest({
        "id": eid, "node_id": "agent+test", "agent_id": "main",
        "session_id": sid, "event_type": et, "ts": _iso(ts),
        "data": data, "cost_usd": None, "token_count": None, "model": None,
    })


def test_autonomy_reads_v3_prompt_submitted_events(autonomy_app):
    """Pre-fix: 0 rows → empty response. Post-fix: 4 samples + ratio 0.5."""
    a, ls = autonomy_app
    store = ls.get_store()
    now = time.time()
    for i, gap in enumerate([0, 60, 180]):
        _ingest(store, eid=f"a-{i}", sid="sess-a", et="prompt.submitted",
                ts=now - 3600 + gap, data={"finalPromptText": f"t{i}"})
    _ingest(store, eid="b-0", sid="sess-b", et="prompt.submitted",
            ts=now - 7200, data={"finalPromptText": "one-shot"})
    _wait_flush(store)
    body = a.test_client().get("/api/autonomy").get_json() or {}
    assert body.get("_source") == "local_store", body
    assert body["samples_7d"] == 4, body
    assert body["score"] is not None
    assert body["autonomy_ratio_7d"] == 0.5
    assert len([d for d in body["series_daily"] if d.get("sessions")]) >= 1


def test_autonomy_reads_claude_code_user_events(autonomy_app):
    """Claude Code shape: event_type='user'. Pre-fix: never queried."""
    a, ls = autonomy_app
    store = ls.get_store()
    now = time.time()
    for i in range(2):
        _ingest(store, eid=f"cc-{i}", sid=f"sess-cc-{i}", et="user",
                ts=now - 1800 - i * 60,
                data={"message": {"role": "user", "content": f"hi {i}"}})
    _wait_flush(store)
    body = a.test_client().get("/api/autonomy").get_json() or {}
    assert body.get("_source") == "local_store", body
    assert body["samples_7d"] == 2
    assert body["autonomy_ratio_7d"] == 1.0


def test_autonomy_unions_all_three_event_shapes(autonomy_app):
    """Mixed store — one of each shape. All three counted."""
    a, ls = autonomy_app
    store = ls.get_store()
    now = time.time()
    _ingest(store, eid="m", sid="s1", et="message", ts=now - 600,
            data={"message": {"role": "user", "content": "legacy"}})
    _ingest(store, eid="u", sid="s2", et="user", ts=now - 700,
            data={"message": {"role": "user", "content": "cc"}})
    _ingest(store, eid="p", sid="s3", et="prompt.submitted", ts=now - 800,
            data={"finalPromptText": "v3"})
    _wait_flush(store)
    body = a.test_client().get("/api/autonomy").get_json() or {}
    assert body.get("_source") == "local_store", body
    assert body["samples_7d"] == 3, body
    assert body["autonomy_ratio_7d"] == 1.0


def test_autonomy_ignores_assistant_events_in_mixed_store(autonomy_app):
    """Assistant events on message/assistant/model.completed must NOT count."""
    a, ls = autonomy_app
    store = ls.get_store()
    now = time.time()
    _ingest(store, eid="real", sid="sess-mix", et="prompt.submitted",
            ts=now - 600, data={"finalPromptText": "real"})
    _ingest(store, eid="ac", sid="sess-mix", et="model.completed",
            ts=now - 500, data={"completionText": "asst"})
    _ingest(store, eid="aa", sid="sess-mix", et="assistant", ts=now - 400,
            data={"message": {"role": "assistant",
                              "content": [{"type": "text", "text": "ok"}]}})
    _ingest(store, eid="am", sid="sess-mix", et="message", ts=now - 300,
            data={"message": {"role": "assistant",
                              "content": [{"type": "text", "text": "ok2"}]}})
    _wait_flush(store)
    body = a.test_client().get("/api/autonomy").get_json() or {}
    assert body.get("_source") == "local_store", body
    assert body["samples_7d"] == 1, body
