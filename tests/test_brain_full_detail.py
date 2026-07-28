"""Brain feed serves the FULL event body — no serve-time truncation.

Founder live-hit (2026-07-28): MESSAGE rows in the Activity/Brain feed were
cut at exactly 200 characters mid-word ("the full log should be visible
without stripping anything") and THINKING rows rendered as blank lines.

Two guarantees, revert-proof against the old ``str(detail)[:200]`` cap in the
local-store fast path:

* a message event whose content is far longer than 200 chars is served
  in full;
* a thinking event with NO text (Claude Code persists extended thinking as
  an encrypted signature block, so the text is genuinely absent from the
  transcript) is served with an honest placeholder, not an empty string.
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

    # Hermetic even on a dev machine with a LIVE daemon: force the daemon RPC
    # to miss AND stop get_store() from returning a proxy to the live daemon,
    # so the fast path direct-opens the tmp_path store (the CI shape).
    import routes.local_query as lq
    monkeypatch.setattr(lq, "local_store_via_daemon", lambda *a, **k: None)
    monkeypatch.setattr(ls, "_daemon_registered", lambda: False, raising=False)

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


def test_message_detail_served_in_full(app):
    a, ls = app
    store = ls.get_store()
    # 2,400 chars of distinct words: a [:200] (or any other silent cap) is
    # guaranteed to drop the tail sentinel.
    long_text = " ".join(f"word{i}" for i in range(300)) + " TAIL-SENTINEL"
    assert len(long_text) > 2000
    store.ingest({
        "id": "ev-full-msg",
        "node_id": "agent+test",
        "agent_id": "main",
        "session_id": "claude_code:sess-full",
        "event_type": "message",
        "ts": "2026-05-11T12:00:00Z",
        "data": {"role": "assistant", "content": long_text,
                 "_runtime": "claude_code"},
        "cost_usd": 0.0,
        "token_count": 10,
        "model": "claude-opus-5",
    })
    _wait_flush(store)

    c = a.test_client()
    r = c.get("/api/brain-history?limit=10")
    assert r.status_code == 200, r.get_data(as_text=True)[:300]
    body = r.get_json()
    assert body.get("_source") == "local_store"
    rows = [ev for ev in body["events"] if ev["type"] == "MESSAGE"]
    assert rows, body["events"]
    detail = rows[0]["detail"]
    # The old code served str(detail)[:200] — this is the revert trap.
    assert len(detail) == len(long_text)
    assert detail.endswith("TAIL-SENTINEL")


def test_encrypted_thinking_gets_honest_placeholder(app):
    a, ls = app
    store = ls.get_store()
    # Claude Code writes {"type":"thinking","thinking":"","signature":"…"} —
    # the adapter's Event.content is "" and there is no text anywhere.
    store.ingest({
        "id": "ev-enc-think",
        "node_id": "agent+test",
        "agent_id": "main",
        "session_id": "claude_code:sess-think",
        "event_type": "thinking",
        "ts": "2026-05-11T12:00:01Z",
        "data": {"role": "assistant", "content": "",
                 "_runtime": "claude_code"},
        "cost_usd": 0.0,
        "token_count": 0,
        "model": "claude-opus-5",
    })
    _wait_flush(store)

    c = a.test_client()
    r = c.get("/api/brain-history?limit=10")
    assert r.status_code == 200
    body = r.get_json()
    assert body.get("_source") == "local_store"
    rows = [ev for ev in body["events"] if ev["type"] == "THINKING"]
    assert rows, body["events"]
    assert rows[0]["detail"] == (
        "(thinking encrypted by the runtime; no text stored)"
    )


def test_thinking_with_real_text_served_in_full(app):
    """A runtime that DOES store thinking text gets it through untouched."""
    a, ls = app
    store = ls.get_store()
    think = "let me reason about this " * 40  # 1,000 chars
    store.ingest({
        "id": "ev-real-think",
        "node_id": "agent+test",
        "agent_id": "main",
        "session_id": "claude_code:sess-think2",
        "event_type": "thinking",
        "ts": "2026-05-11T12:00:02Z",
        "data": {"role": "assistant", "content": think,
                 "_runtime": "claude_code"},
        "cost_usd": 0.0,
        "token_count": 0,
        "model": "claude-opus-5",
    })
    _wait_flush(store)

    c = a.test_client()
    r = c.get("/api/brain-history?limit=10")
    body = r.get_json()
    rows = [ev for ev in body["events"] if ev["type"] == "THINKING"]
    assert rows
    assert rows[0]["detail"] == think
