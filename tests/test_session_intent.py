"""sessions.intent: the FULL first user prompt, per session, every runtime.

Covers the store contract (first wins, redacted, capped, lazily back-filled),
the two read surfaces (/api/sessions rows and the /api/transcript payload) and
the cloud rule: intent rides ONLY the E2E-encrypted companion field, never a
plaintext key. Temp DuckDB only.
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
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_READ", "1")
    import clawmetry.local_store as ls
    importlib.reload(ls)
    from pathlib import Path
    monkeypatch.setattr(ls, "DB_PATH", Path(str(tmp_path / "events.duckdb")))
    import routes.sessions as sessions_mod
    importlib.reload(sessions_mod)
    a = Flask(__name__)
    a.register_blueprint(sessions_mod.bp_sessions)
    yield a, ls
    try:
        ls.get_store().stop(flush=True)
    except Exception:
        pass


def _ev(eid, sid, role, content, ts, et="message", **data):
    d = {"role": role, "content": content, **data}
    return {"id": eid, "node_id": "node-test", "agent_id": "main", "session_id": sid,
            "event_type": et, "ts": ts, "data": json.dumps(d)}


def _drain(store):
    store._flush_now()
    for _ in range(20):
        if not store._ring:
            break
        time.sleep(0.05)


LONG_PROMPT = ("Please migrate the billing service off the legacy invoice table. "
               "Keep the rounding rules, add a feature flag, and write tests. ") * 8


def test_intent_is_full_prompt_not_title_and_first_wins(app):
    a, ls = app
    store = ls.get_store()
    sid = "codex:intent-a"
    store.ingest_session({"agent_type": "codex", "session_id": sid, "node_id": "n",
                          "title": LONG_PROMPT[:80], "intent": LONG_PROMPT,
                          "intent_source": "adapter",
                          "started_at": "2026-09-01T00:00:00Z",
                          "last_active_at": "2026-09-01T00:01:00Z"})
    row = store.get_session_intent(sid)
    assert row["intent"] == LONG_PROMPT.strip()
    assert len(row["intent"]) > 80
    assert row["intent_source"] == "adapter"
    # A re-ingest with a different prompt must NOT replace the opening one.
    store.ingest_session({"agent_type": "codex", "session_id": sid, "node_id": "n",
                          "intent": "a later prompt", "intent_source": "adapter",
                          "last_active_at": "2026-09-01T00:02:00Z"})
    assert store.get_session_intent(sid)["intent"] == LONG_PROMPT.strip()
    assert store.update_session_intent(sid, "another later prompt") is False


def test_intent_is_redacted_and_capped(app):
    a, ls = app
    store = ls.get_store()
    sid = "openclaw:intent-b"
    store.ingest_session({"agent_type": "openclaw", "session_id": sid, "node_id": "n",
                          "started_at": "2026-09-01T00:00:00Z",
                          "last_active_at": "2026-09-01T00:01:00Z"})
    secret = "sk-ant-api03-" + "a" * 40
    assert store.update_session_intent(
        sid, f"use key {secret} and then " + "y" * 5000) is True
    got = store.get_session_intent(sid)["intent"]
    assert secret not in got
    assert "REDACTED" in got or "[" in got
    from clawmetry.event_shape import INTENT_MAX_CHARS
    assert len(got) == INTENT_MAX_CHARS and got.endswith("...")


def test_intent_backfilled_from_events_for_every_runtime_shape(app):
    a, ls = app
    store = ls.get_store()
    cases = {
        # family adapter row
        "cursor:bf-1": [_ev("c1", "cursor:bf-1", "assistant", "hi", "2026-09-01T00:00:00Z"),
                        _ev("c2", "cursor:bf-1", "user", "Add dark mode to settings",
                            "2026-09-01T00:00:01Z")],
        # openclaw v3-normalised prompt
        "oc-bf-2": [{"id": "o1", "node_id": "n", "session_id": "oc-bf-2",
                     "event_type": "prompt.submitted", "ts": "2026-09-01T00:00:00Z",
                     "data": json.dumps({"type": "prompt.submitted",
                                         "finalPromptText": "Summarise yesterday's incidents",
                                         "data": {"finalPromptText": "Summarise yesterday's incidents"}})}],
        # raw Claude Code row with a system-reminder frame first
        "claude_code:bf-3": [
            {"id": "k1", "node_id": "n", "session_id": "claude_code:bf-3",
             "event_type": "user", "ts": "2026-09-01T00:00:00Z",
             "data": json.dumps({"type": "user", "message": {
                 "role": "user", "content": "<system-reminder>ctx</system-reminder>"}})},
            {"id": "k2", "node_id": "n", "session_id": "claude_code:bf-3",
             "event_type": "user", "ts": "2026-09-01T00:00:01Z",
             "data": json.dumps({"type": "user", "message": {
                 "role": "user", "content": [{"type": "text", "text": "Fix the failing CI job"}]}})},
        ],
    }
    for sid, evs in cases.items():
        store.ingest_session({"agent_type": sid.split(":")[0] if ":" in sid else "openclaw",
                              "session_id": sid, "node_id": "n",
                              "started_at": "2026-09-01T00:00:00Z",
                              "last_active_at": "2026-09-01T00:01:00Z"})
        for e in evs:
            store.ingest(e)
    # A session with events but no human prompt is stamped 'none', not rescanned.
    store.ingest_session({"agent_type": "openclaw", "session_id": "oc-noprompt", "node_id": "n",
                          "started_at": "2026-09-01T00:00:00Z",
                          "last_active_at": "2026-09-01T00:01:00Z"})
    store.ingest(_ev("z1", "oc-noprompt", "assistant", "cron output", "2026-09-01T00:00:00Z"))
    _drain(store)

    assert store.backfill_session_intents(limit=50) == 3
    assert store.get_session_intent("cursor:bf-1")["intent"] == "Add dark mode to settings"
    assert store.get_session_intent("oc-bf-2")["intent"] == "Summarise yesterday's incidents"
    assert store.get_session_intent("claude_code:bf-3")["intent"] == "Fix the failing CI job"
    none = store.get_session_intent("oc-noprompt")
    assert none["intent"] == "" and none["intent_source"] == "none"
    assert store.backfill_session_intents(limit=50) == 0


def test_api_sessions_rows_and_transcript_expose_intent(app):
    a, ls = app
    store = ls.get_store()
    sid = "gemini_cli:api-1"
    store.ingest_session({"agent_type": "gemini_cli", "session_id": sid, "node_id": "n",
                          "title": "Write release notes", "started_at": "2026-09-01T00:00:00Z",
                          "last_active_at": "2026-09-01T00:01:00Z"})
    store.ingest(_ev("g1", sid, "user", "Write release notes for 0.13 covering the guard changes",
                     "2026-09-01T00:00:00Z"))
    store.ingest(_ev("g2", sid, "assistant", "Here they are", "2026-09-01T00:00:05Z"))
    _drain(store)
    assert store.backfill_session_intents() == 1

    c = a.test_client()
    body = c.get("/api/sessions").get_json()
    row = next(r for r in body["sessions"] if r["session_id"] == sid)
    assert row["intent"] == "Write release notes for 0.13 covering the guard changes"
    assert row["intent_source"] == "events"
    assert "commits" in row and "prs" in row

    t = c.get(f"/api/transcript/{sid}").get_json()
    assert t["_source"] == "local_store"
    assert t["intent"] == "Write release notes for 0.13 covering the guard changes"
    assert t["intent_source"] == "events"


def test_openclaw_batch_ingest_sets_intent_from_first_prompt(app):
    """sync._local_ingest_session_batch stamps intent from the batch."""
    a, ls = app
    store = ls.get_store()
    from clawmetry import sync
    sid = "3fc28a8b-b0f5-47af-b234-fa2f96db8112"
    store.ingest_session({"agent_type": "openclaw", "session_id": sid, "node_id": "n",
                          "started_at": "2026-05-12T22:35:31Z",
                          "last_active_at": "2026-05-12T22:35:32Z"})
    import os
    fx = os.path.join(os.path.dirname(__file__), "fixtures", "openclaw", "v3-session.jsonl")
    with open(fx) as fh:
        batch = [json.loads(line) for line in fh if line.strip()]
    sync._local_ingest_session_batch(batch, f"{sid}.jsonl", "n", None)
    _drain(store)
    assert store.get_session_intent(sid)["intent"] == "hello world from MOAT verification"


def test_cloud_rows_carry_intent_only_sealed(app):
    a, ls = app
    store = ls.get_store()
    from clawmetry import sync
    sid = "codex:cloud-1"
    store.ingest_session({"agent_type": "codex", "session_id": sid, "node_id": "n",
                          "intent": "Rotate the staging DB password and update secrets",
                          "intent_source": "adapter",
                          "started_at": "2026-09-01T00:00:00Z",
                          "last_active_at": "2026-09-01T00:01:00Z"})
    key = sync.generate_key() if hasattr(sync, "generate_key") else None
    if key is None:
        import base64
        import os as _os
        key = base64.urlsafe_b64encode(_os.urandom(32)).decode()
    rows = [{"session_id": sid, "title": sid, "intent": "must be dropped"}]
    sync._trail_decorate_cloud_session_rows(rows, key)
    r = rows[0]
    assert "intent" not in r
    assert r.get("intent_blob")
    assert "Rotate the staging" not in json.dumps(r)
    assert sync.decrypt_payload(r["intent_blob"], key)["intent"] == \
        "Rotate the staging DB password and update secrets"
    # No key: nothing leaves, not even sealed.
    rows2 = [{"session_id": sid, "title": sid}]
    sync._trail_decorate_cloud_session_rows(rows2, None)
    assert "intent_blob" not in rows2[0] and "intent" not in rows2[0]
    assert sync.seal_session_intent("x", None) is None
