"""Regression test for issue #1718.

Embodied (transcripts) tab showed list count = 11 while detail page = 0
because ``/api/transcripts`` reported raw ``event_count`` from the events
table — counting plumbing rows like ``session.started`` / ``model.changed``
/ ``thinking_level_change`` / ``channel.*`` / ``custom`` — while
``/api/transcript/<sid>`` only renders ``prompt.submitted`` /
``model.completed`` / ``trace.artifacts`` / ``tool.*`` / role-bearing
Anthropic events.

This test asserts that for every session returned by ``/api/transcripts``
the ``messages`` count equals the ``messageCount`` returned by
``/api/transcript/<id>``. Fixture seeds a realistic OpenClaw v3 event mix
(``session.started`` + ``model.changed`` + ``prompt.submitted`` +
``model.completed`` + ``custom_message``) so the bug class — list path
counting plumbing types the detail path skips — is exercised end-to-end.
"""

from __future__ import annotations

import importlib
import json
import time

import pytest
from flask import Flask


@pytest.fixture
def app(tmp_path, monkeypatch):
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH",
                       str(tmp_path / "events.duckdb"))
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_SECS", "0.05")
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_READ", "1")

    import clawmetry.local_store as ls
    importlib.reload(ls)
    import routes.sessions as sessions_mod
    importlib.reload(sessions_mod)

    # Force the daemon-proxy lookup to miss so the routes fall back to
    # the in-process LocalStore singleton seeded by this test. Without
    # this the route would talk to whatever local-running sync daemon
    # the dev box has (it owns the real DuckDB) and the assertions would
    # read production data, not our fixture rows.
    import routes.local_query as lq
    monkeypatch.setattr(lq, "_DISCOVERY_PATH",
                        str(tmp_path / "no-such-discovery.json"))
    # Drop the in-memory cache too — it may already be populated from a
    # previous test inside the same pytest session.
    lq._DAEMON_CACHE["disc"] = None
    lq._DAEMON_CACHE["ts"] = 0.0

    a = Flask(__name__)
    a.register_blueprint(sessions_mod.bp_sessions)
    yield a, ls
    try:
        ls.get_store().stop(flush=True)
    except Exception:
        pass


def _ev(event_id, sid, event_type, data_obj, ts):
    """Build an events-table row with arbitrary event_type + data payload."""
    return {
        "id": event_id,
        "node_id": "node-test",
        "agent_id": "main",
        "session_id": sid,
        "event_type": event_type,
        "ts": ts,
        "data": json.dumps(data_obj),
    }


def _anthropic_msg(event_id, sid, role, content, ts, **extra):
    """Anthropic-shape message event — same helper shape used by
    ``test_transcript_local_store.py`` so the two suites stay aligned."""
    obj = {"role": role, "content": content, "timestamp": ts, **extra}
    return {
        "id": event_id,
        "node_id": "node-test",
        "agent_id": "main",
        "session_id": sid,
        "event_type": "message" if role in ("user", "assistant") else role,
        "ts": ts,
        "data": json.dumps(obj),
    }


def _drain(store):
    store._flush_now()
    for _ in range(10):
        if not store._ring:
            break
        time.sleep(0.05)


def test_list_count_matches_detail_count_openclaw_v3(app):
    """Issue #1718 regression — OpenClaw v3 event mix.

    Six raw events per session, but only 2 are renderable
    (``prompt.submitted`` + ``model.completed``). Before the fix the list
    returned 6 and the detail returned 2; after the fix both return 2.
    """
    a, ls = app
    store = ls.get_store()
    sid = "sess-openclaw-v3-mix"

    # Renderable: prompt.submitted, model.completed (= 2 turns in the
    # detail modal). Real OpenClaw v3 events carry the payload at BOTH
    # the top level AND under a nested ``data`` block — the
    # ``_expand_openclaw_event`` helper reads from ``data.*``, so the
    # fixture must include the nested block to render.
    store.ingest(_ev("e1", sid, "session.started",
                     {"type": "session.started",
                      "data": {},
                      "timestamp": "2026-05-19T10:00:00Z"},
                     "2026-05-19T10:00:00Z"))
    store.ingest(_ev("e2", sid, "model.changed",
                     {"type": "model.changed", "modelId": "claude-opus-4-7",
                      "data": {"modelId": "claude-opus-4-7"},
                      "timestamp": "2026-05-19T10:00:01Z"},
                     "2026-05-19T10:00:01Z"))
    store.ingest(_ev("e3", sid, "prompt.submitted",
                     {"type": "prompt.submitted",
                      "finalPromptText": "hello agent",
                      "data": {"finalPromptText": "hello agent"},
                      "timestamp": "2026-05-19T10:00:02Z"},
                     "2026-05-19T10:00:02Z"))
    store.ingest(_ev("e4", sid, "model.completed",
                     {"type": "model.completed",
                      "completionText": "hi there",
                      "data": {"completionText": "hi there"},
                      "timestamp": "2026-05-19T10:00:03Z"},
                     "2026-05-19T10:00:03Z"))
    # Non-renderable plumbing types the OpenClaw daemon emits — these
    # used to be counted by ``/api/transcripts`` (raw event_count) but
    # never appeared in the detail modal, producing the issue #1718
    # mismatch (list=6, detail=2).
    store.ingest(_ev("e5", sid, "custom_message",
                     {"type": "custom_message", "content": "debug",
                      "data": {"content": "debug"},
                      "timestamp": "2026-05-19T10:00:04Z"},
                     "2026-05-19T10:00:04Z"))
    store.ingest(_ev("e6", sid, "custom",
                     {"type": "custom",
                      "data": {},
                      "timestamp": "2026-05-19T10:00:05Z"},
                     "2026-05-19T10:00:05Z"))
    _drain(store)

    c = a.test_client()

    list_resp = c.get("/api/transcripts")
    assert list_resp.status_code == 200
    list_body = list_resp.get_json()
    assert list_body.get("_source") == "local_store"
    row = next(
        (t for t in list_body["transcripts"] if t["id"] == sid), None
    )
    assert row is not None, "transcript list missing the seeded session"

    detail_resp = c.get(f"/api/transcript/{sid}")
    assert detail_resp.status_code == 200
    detail_body = detail_resp.get_json()
    assert detail_body.get("_source") == "local_store"

    # The actual rendered messages count from the detail modal.
    detail_count = detail_body["messageCount"]
    assert detail_count == 2, (
        f"Detail should render exactly 2 messages "
        f"(prompt.submitted + model.completed); got {detail_count}"
    )

    # The list's reported count MUST match what the detail will render.
    assert row["messages"] == detail_count, (
        f"List/detail count mismatch (issue #1718): "
        f"list={row['messages']}, detail={detail_count}"
    )


def test_list_count_matches_detail_count_anthropic_shape(app):
    """Anthropic-style events: 4 message events, all renderable.

    Sanity check that the renderable filter doesn't under-count classic
    role-bearing payloads.
    """
    a, ls = app
    store = ls.get_store()
    sid = "sess-anthropic-mix"

    store.ingest(_anthropic_msg("a1", sid, "user", "hi",   "2026-05-19T11:00:00Z"))
    store.ingest(_anthropic_msg("a2", sid, "assistant", "hello",
                                "2026-05-19T11:00:01Z",
                                usage={"input_tokens": 5, "output_tokens": 3}))
    store.ingest(_anthropic_msg("a3", sid, "user", "again",
                                "2026-05-19T11:00:02Z"))
    store.ingest(_anthropic_msg("a4", sid, "assistant", "yo",
                                "2026-05-19T11:00:03Z",
                                usage={"input_tokens": 4, "output_tokens": 2}))
    _drain(store)

    c = a.test_client()

    list_body = c.get("/api/transcripts").get_json()
    row = next(
        (t for t in list_body["transcripts"] if t["id"] == sid), None
    )
    assert row is not None
    detail_body = c.get(f"/api/transcript/{sid}").get_json()

    assert detail_body["messageCount"] == 4
    assert row["messages"] == detail_body["messageCount"], (
        f"Anthropic-shape list/detail count mismatch: "
        f"list={row['messages']}, detail={detail_body['messageCount']}"
    )


def test_list_count_matches_detail_count_all_sessions(app):
    """Cross-session sweep: seed three distinct sessions with different
    event mixes and assert list-vs-detail parity for every one.
    """
    a, ls = app
    store = ls.get_store()

    # Session A: 1 prompt + 1 completion (2 renderable, 3 raw).
    store.ingest(_ev("A1", "sess-A", "session.started",
                     {"type": "session.started", "data": {},
                      "timestamp": "2026-05-19T12:00:00Z"},
                     "2026-05-19T12:00:00Z"))
    store.ingest(_ev("A2", "sess-A", "prompt.submitted",
                     {"type": "prompt.submitted",
                      "finalPromptText": "q",
                      "data": {"finalPromptText": "q"},
                      "timestamp": "2026-05-19T12:00:01Z"},
                     "2026-05-19T12:00:01Z"))
    store.ingest(_ev("A3", "sess-A", "model.completed",
                     {"type": "model.completed",
                      "completionText": "a",
                      "data": {"completionText": "a"},
                      "timestamp": "2026-05-19T12:00:02Z"},
                     "2026-05-19T12:00:02Z"))

    # Session B: ONLY non-renderable plumbing (0 renderable, 3 raw).
    # Pre-fix this would show 3 in the list and 0 in the detail.
    store.ingest(_ev("B1", "sess-B", "session.started",
                     {"type": "session.started", "data": {},
                      "timestamp": "2026-05-19T13:00:00Z"},
                     "2026-05-19T13:00:00Z"))
    store.ingest(_ev("B2", "sess-B", "model.changed",
                     {"type": "model.changed", "modelId": "x",
                      "data": {"modelId": "x"},
                      "timestamp": "2026-05-19T13:00:01Z"},
                     "2026-05-19T13:00:01Z"))
    store.ingest(_ev("B3", "sess-B", "custom",
                     {"type": "custom", "data": {},
                      "timestamp": "2026-05-19T13:00:02Z"},
                     "2026-05-19T13:00:02Z"))

    # Session C: tool + message mix (3 renderable, 4 raw).
    store.ingest(_ev("C1", "sess-C", "session.started",
                     {"type": "session.started", "data": {},
                      "timestamp": "2026-05-19T14:00:00Z"},
                     "2026-05-19T14:00:00Z"))
    store.ingest(_ev("C2", "sess-C", "prompt.submitted",
                     {"type": "prompt.submitted",
                      "finalPromptText": "do a thing",
                      "data": {"finalPromptText": "do a thing"},
                      "timestamp": "2026-05-19T14:00:01Z"},
                     "2026-05-19T14:00:01Z"))
    store.ingest(_ev("C3", "sess-C", "tool.result",
                     {"type": "tool.result",
                      "name": "Bash", "output": "ok",
                      "data": {"name": "Bash", "output": "ok"},
                      "timestamp": "2026-05-19T14:00:02Z"},
                     "2026-05-19T14:00:02Z"))
    store.ingest(_ev("C4", "sess-C", "model.completed",
                     {"type": "model.completed",
                      "completionText": "done",
                      "data": {"completionText": "done"},
                      "timestamp": "2026-05-19T14:00:03Z"},
                     "2026-05-19T14:00:03Z"))

    _drain(store)

    c = a.test_client()
    list_body = c.get("/api/transcripts").get_json()
    transcripts_by_id = {t["id"]: t for t in list_body["transcripts"]}
    for sid in ("sess-A", "sess-B", "sess-C"):
        assert sid in transcripts_by_id, f"missing session {sid} in list"
        list_row = transcripts_by_id[sid]
        detail_body = c.get(f"/api/transcript/{sid}").get_json()
        assert list_row["messages"] == detail_body["messageCount"], (
            f"Session {sid}: list/detail count mismatch "
            f"(list={list_row['messages']}, detail={detail_body['messageCount']})"
        )
