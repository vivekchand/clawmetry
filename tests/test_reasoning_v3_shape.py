"""Silent-zero regression test for /api/reasoning on real OpenClaw v3 installs.

Bug class (7th instance — 2026-05-18): the fast path in
``routes/reasoning.py`` queried only ``event_type="message"``. Real v3
writes assistant turns as ``model.completed`` with thinking in
``data.assistantTexts`` and answer in ``data.completionText`` — no
``data.message.content`` block to walk. Claude Code writes ``assistant``.
See ``feedback_synthetic_tests_missed_real_event_shape.md`` +
``reference_openclaw_v3_event_types.md``.
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
def reasoning_app(tmp_path, monkeypatch):
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
    import routes.reasoning as rea
    importlib.reload(rea)
    a = Flask(__name__)
    a.register_blueprint(rea.bp_reasoning)
    yield a, ls
    try:
        ls.get_store().stop(flush=True)
    except Exception:
        pass


def _ingest(store, *, eid, sid, et, ts, data, model="claude-opus-4-7"):
    store.ingest({
        "id": eid, "node_id": "agent+test", "agent_id": "main",
        "session_id": sid, "event_type": et, "ts": _iso(ts),
        "data": data, "cost_usd": 0.01, "token_count": 100, "model": model,
    })


def test_reasoning_extracts_chain_from_model_completed(reasoning_app):
    """v3 shape: data.assistantTexts + data.completionText, NO data.message."""
    a, ls = reasoning_app
    store = ls.get_store()
    thinking = (
        "The user wants to refactor this function. Let me try a cleaner "
        "approach. If I extract the helper, the test stays small. So I'll do that."
    )
    answer = "Here's the refactored function with the helper extracted."
    _ingest(store, eid="v1", sid="sess-v", et="model.completed",
            ts=time.time() - 120,
            data={"modelId": "claude-opus-4-7",
                  "completionText": answer, "assistantTexts": [thinking]})
    _wait_flush(store)
    r = a.test_client().get("/api/reasoning?session=sess-v")
    assert r.status_code == 200, r.get_data(as_text=True)[:300]
    body = r.get_json() or {}
    assert body.get("_source") == "local_store", body
    assert body["summary"]["chain_count"] == 1, body
    c = body["chains"][0]
    assert c["thinking_tokens"] > 0
    assert c["answer_tokens"] > 0
    assert c["steps"]
    assert thinking in c["raw_thinking"]


def test_reasoning_extracts_chain_from_claude_code_assistant(reasoning_app):
    """Claude Code shape: event_type='assistant' + legacy content block list."""
    a, ls = reasoning_app
    store = ls.get_store()
    _ingest(store, eid="c1", sid="sess-c", et="assistant",
            ts=time.time() - 60,
            data={"message": {"role": "assistant", "content": [
                {"type": "thinking", "thinking":
                    "The user wants the file. Let me look at the imports. "
                    "If I check the package, the answer will be obvious. "
                    "So I'll grep for it."},
                {"type": "text", "text": "Found it. The import is on line 12."},
            ]}})
    _wait_flush(store)
    body = a.test_client().get("/api/reasoning?session=sess-c").get_json() or {}
    assert body.get("_source") == "local_store", body
    assert body["summary"]["chain_count"] == 1, body
    c = body["chains"][0]
    assert c["thinking_tokens"] > 0
    assert c["answer_tokens"] > 0


def test_reasoning_unions_legacy_and_v3_shapes(reasoning_app):
    """One legacy 'message' + one v3 'model.completed' → 2 chains, ts-sorted."""
    a, ls = reasoning_app
    store = ls.get_store()
    now = time.time()
    _ingest(store, eid="m1", sid="sess-mix", et="message", ts=now - 600,
            data={"message": {"role": "assistant", "content": [
                {"type": "thinking", "thinking": "The user wants a small change."},
                {"type": "text", "text": "Done — see the patch."},
            ]}})
    _ingest(store, eid="v1", sid="sess-mix", et="model.completed", ts=now - 60,
            data={"modelId": "claude-opus-4-7",
                  "completionText": "And here's the follow-up.",
                  "assistantTexts": [
                      "The user wants a follow-up. Let me look at the test. "
                      "If it still passes, I can proceed. So I'll add the feature."
                  ]})
    _wait_flush(store)
    body = a.test_client().get("/api/reasoning?session=sess-mix").get_json() or {}
    assert body.get("_source") == "local_store", body
    assert body["summary"]["chain_count"] == 2, body
    ts_seq = [c["timestamp"] for c in body["chains"]]
    assert ts_seq == sorted(ts_seq), ts_seq


def test_reasoning_empty_when_no_thinking_present(reasoning_app):
    """model.completed with no assistantTexts must not fabricate chains."""
    a, ls = reasoning_app
    store = ls.get_store()
    _ingest(store, eid="nt", sid="sess-nt", et="model.completed",
            ts=time.time() - 60,
            data={"modelId": "claude-opus-4-7",
                  "completionText": "Answer with no thinking."})
    _wait_flush(store)
    body = a.test_client().get("/api/reasoning?session=sess-nt").get_json() or {}
    assert body.get("summary", {}).get("chain_count", 0) == 0, body
