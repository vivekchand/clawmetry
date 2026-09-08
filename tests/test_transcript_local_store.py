"""Tests for the /api/transcript/<sid> local-store fast path.

Closes the explicit MOAT gap surfaced in the real-OpenClaw E2E pipeline:
the transcript endpoint used to read JSONL directly, bypassing DuckDB.

Pattern matches test_sessions_local_fastpath.py:
- CLAWMETRY_LOCAL_STORE_READ=1 + populated events → returns from DuckDB
- Flag unset → falls through to legacy JSONL path
- No events for the session → falls through (so the JSONL path can still serve)
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
    import routes.sessions as sessions_mod
    importlib.reload(sessions_mod)

    a = Flask(__name__)
    a.register_blueprint(sessions_mod.bp_sessions)
    yield a, ls
    try:
        ls.get_store().stop(flush=True)
    except Exception:
        pass


def _ev(event_id, sid, role, content, ts, **extra):
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
    """Force the ring buffer to flush so the events table is populated."""
    store._flush_now()
    # Allow the background flusher one tick.
    for _ in range(10):
        if not store._ring:
            break
        time.sleep(0.05)


def test_transcript_fast_path_returns_local_rows(app):
    a, ls = app
    store = ls.get_store()
    sid = "sess-transcript-A"
    store.ingest(_ev("e1", sid, "user", "hello", "2026-05-12T10:00:00Z"))
    store.ingest(_ev("e2", sid, "assistant", "hi there",
                     "2026-05-12T10:00:05Z", model="claude-opus-4-7",
                     usage={"input_tokens": 12, "output_tokens": 5}))
    store.ingest(_ev("e3", sid, "user", "what is 2+2?", "2026-05-12T10:00:10Z"))
    store.ingest(_ev("e4", sid, "assistant", "4",
                     "2026-05-12T10:00:15Z",
                     usage={"input_tokens": 8, "output_tokens": 1}))
    _drain(store)

    c = a.test_client()
    r = c.get(f"/api/transcript/{sid}")
    assert r.status_code == 200
    body = r.get_json()
    assert body.get("_source") == "local_store"
    assert body["messageCount"] == 4
    assert body["model"] == "claude-opus-4-7"
    assert body["totalTokens"] == 26
    # Ascending timeline preserved.
    roles = [m["role"] for m in body["messages"]]
    assert roles == ["user", "assistant", "user", "assistant"]
    contents = [m["content"] for m in body["messages"]]
    assert contents == ["hello", "hi there", "what is 2+2?", "4"]
    # Duration: 15s between first and last.
    assert body["duration"] == "15s"


def test_transcript_fast_path_emits_tool_call_messages(app):
    a, ls = app
    store = ls.get_store()
    sid = "sess-transcript-tool"
    store.ingest(_ev("t1", sid, "assistant", "let me check",
                     "2026-05-12T10:00:00Z",
                     tool_calls=[{"name": "Bash", "input": {"cmd": "ls"}}]))
    _drain(store)

    c = a.test_client()
    r = c.get(f"/api/transcript/{sid}")
    body = r.get_json()
    assert body.get("_source") == "local_store"
    # tool message inserted before the assistant message
    tool_msgs = [m for m in body["messages"] if m["role"] == "tool"]
    assert len(tool_msgs) == 1
    assert "[Tool Call: Bash]" in tool_msgs[0]["content"]
    assert "ls" in tool_msgs[0]["content"]


def test_transcript_fast_path_falls_back_when_session_empty(app, tmp_path, monkeypatch):
    """Unknown session → fast path returns None → legacy path runs and 404s
    because no JSONL exists."""
    a, _ = app
    # Point dashboard.SESSIONS_DIR at an empty directory so the legacy
    # path's existence check fails and we get a 404 (not a crash).
    import dashboard as _d
    monkeypatch.setattr(_d, "SESSIONS_DIR", str(tmp_path / "no-such-dir"), raising=False)
    c = a.test_client()
    r = c.get("/api/transcript/sess-doesnt-exist")
    assert r.status_code == 404


def test_transcript_fast_path_off_when_flag_unset(app, monkeypatch):
    a, ls = app
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_READ", "0")  # force legacy path
    store = ls.get_store()
    sid = "sess-off"
    store.ingest(_ev("o1", sid, "user", "should not be served from duckdb",
                     "2026-05-12T11:00:00Z"))
    _drain(store)

    # Without the flag, the route falls through to the JSONL path which
    # 404s because no file exists. Verify the response is NOT tagged with
    # _source=local_store.
    import dashboard as _d
    monkeypatch.setattr(_d, "SESSIONS_DIR", "/tmp/no-such-dir-here", raising=False)
    c = a.test_client()
    r = c.get(f"/api/transcript/{sid}")
    assert r.status_code == 404
    body = r.get_json() or {}
    assert body.get("_source") != "local_store"


def test_transcript_includes_external_api_calls(app):
    """External HTTP calls recorded by the interceptor appear in the transcript response."""
    a, ls = app
    store = ls.get_store()
    sid = "sess-ext-api-calls"
    # Seed a session row so query_external_calls(session_id=…) JOIN resolves.
    # updated_at is a far-future epoch-ms value so any call ts within the
    # session window satisfies (e.ts <= epoch_ms(updated_at * 1000)::VARCHAR).
    store.ingest_session({
        "session_id": sid,
        "started_at": "2026-05-12T10:00:00Z",
        "updated_at": 9_999_999_999_999,
    })
    # Seed one event so the fast-path returns a non-empty session.
    store.ingest(_ev("extapi-e1", sid, "user", "call github api", "2026-05-12T10:00:01Z"))
    # Seed one external API call within the session time window.
    store.ingest_external_call({
        "ts": "2026-05-12T10:00:05Z",
        "host": "api.github.com",
        "url": "https://api.github.com/repos/owner/repo",
        "method": "GET",
        "status_code": 200,
        "latency_ms": 42.0,
        "library": "requests",
    }, node_id="node-test")
    _drain(store)

    c = a.test_client()
    r = c.get(f"/api/transcript/{sid}")
    assert r.status_code == 200
    body = r.get_json()
    assert body.get("_source") == "local_store"
    calls = body.get("external_api_calls", [])
    assert len(calls) == 1
    assert calls[0]["host"] == "api.github.com"
    assert calls[0]["method"] == "GET"
    assert calls[0]["status_code"] == 200


def test_transcript_thinking_rows_are_typed_and_usage_stamped(app):
    """Extended-thinking events keep ``type: "thinking"`` so the UI can style
    the model's internal reasoning apart from the actual reply, and the
    daemon-stamped per-event token/cost lands on the message (once per row)."""
    a, ls = app
    store = ls.get_store()
    sid = "sess-thinking-typed"
    store.ingest(_ev("t1", sid, "user", "how is life", "2026-05-12T10:00:00Z"))
    think = _ev("t2", sid, "assistant", "casual small talk — reply warmly",
                "2026-05-12T10:00:03Z")
    think["event_type"] = "thinking"
    think["data"] = json.dumps({"type": "thinking", "role": "assistant",
                                "content": "casual small talk — reply warmly",
                                "timestamp": "2026-05-12T10:00:03Z"})
    think["token_count"] = 1276
    think["cost_usd"] = 0.0886
    store.ingest(think)
    store.ingest(_ev("t3", sid, "assistant", "life is good!",
                     "2026-05-12T10:00:05Z"))
    _drain(store)

    c = a.test_client()
    r = c.get(f"/api/transcript/{sid}")
    assert r.status_code == 200
    msgs = r.get_json()["messages"]
    assert [m["role"] for m in msgs] == ["user", "assistant", "assistant"]
    # The thinking turn is typed; the actual reply is not.
    assert msgs[1].get("type") == "thinking"
    assert msgs[2].get("type") != "thinking"
    # Usage stamped from the event row for the per-turn spend badge.
    assert msgs[1].get("tokens") == 1276
    assert abs(msgs[1].get("cost_usd", 0) - 0.0886) < 1e-9
    assert "tokens" not in msgs[2]


def test_transcript_nested_message_thinking_block_emitted(app):
    """Claude-Code shape: a ``thinking`` content block nested under
    ``data.message`` becomes its own ``type: "thinking"`` turn instead of
    being silently dropped, and the row's usage lands once on the first
    message emitted for the row."""
    a, ls = app
    store = ls.get_store()
    sid = "sess-thinking-nested"
    row = {
        "id": "n1",
        "node_id": "node-test",
        "agent_id": "main",
        "session_id": sid,
        "event_type": "assistant",
        "ts": "2026-05-12T10:00:00Z",
        "token_count": 500,
        "cost_usd": 0.05,
        "data": json.dumps({
            "message": {
                "role": "assistant",
                "content": [
                    {"type": "thinking", "thinking": "let me reason about it"},
                    {"type": "text", "text": "the actual answer"},
                ],
            },
            "timestamp": "2026-05-12T10:00:00Z",
        }),
    }
    store.ingest(row)
    _drain(store)

    c = a.test_client()
    r = c.get(f"/api/transcript/{sid}")
    assert r.status_code == 200
    msgs = r.get_json()["messages"]
    assert len(msgs) == 2
    assert msgs[0]["type"] == "thinking"
    assert msgs[0]["content"] == "let me reason about it"
    assert msgs[1]["content"] == "the actual answer"
    # Row usage stamped exactly once (first message of the row).
    assert msgs[0].get("tokens") == 500
    assert "tokens" not in msgs[1]


# ── Snapshot message cap keeps the opening user prompt ──────────────────────
# The cloud replay renders the SNAPSHOT transcript (sync._build_transcripts),
# which caps long sessions to the last N messages. The old tail-only cap
# dropped the first user message, so the hosted replay opened mid-session on
# a bare tool chip and its turn TOC lost the anchor turn (user report
# 2026-08-29). _cap_transcript_messages must keep the opening prompt plus an
# honest omission marker.


def _msgs(n, first_user_at=0):
    out = []
    for i in range(n):
        if i == first_user_at:
            out.append({"role": "user", "content": f"the opening prompt {i}",
                        "timestamp": 1000 + i})
        else:
            out.append({"role": "assistant", "content": f"reply {i}",
                        "timestamp": 1000 + i})
    return out


def test_cap_keeps_short_transcripts_untouched():
    from clawmetry.sync import _cap_transcript_messages
    msgs = _msgs(10)
    capped, truncated, oldest_ts = _cap_transcript_messages(msgs, 80)
    assert capped is msgs
    assert truncated is False
    assert oldest_ts is None


def test_cap_preserves_first_user_prompt_and_marks_omission():
    from clawmetry.sync import _cap_transcript_messages
    msgs = _msgs(83)  # the exact shape of the field report: 83 msgs, cap 80
    capped, truncated, oldest_ts = _cap_transcript_messages(msgs, 80)
    assert truncated is True
    assert len(capped) <= 80
    # Paging cursor = the first message of the contiguous tail (capped[2]:
    # opening prompt, marker, then the tail).
    assert oldest_ts == capped[2]["timestamp"]
    # Opening user prompt survives, first in the list.
    assert capped[0]["role"] == "user"
    assert capped[0]["content"] == "the opening prompt 0"
    # Honest omission marker sits between the prompt and the tail, timestamped
    # so the viewer's ts-sorted merge keeps it in place.
    marker = capped[1]
    assert marker["role"] == "system"
    # Structured paging affordance: the replay renders type=history_gap as an
    # inline "load earlier" row with a live count, not as a system message.
    assert marker["type"] == "history_gap"
    assert marker["omitted"] == 83 - 1 - len(capped[2:])
    assert "not loaded yet" in marker["content"]
    assert "cloud" not in marker["content"].lower()
    assert capped[0]["timestamp"] < marker["timestamp"] < capped[2]["timestamp"]
    # Tail is the most recent messages, ending on the true last message.
    assert capped[-1]["content"] == "reply 82"


def test_cap_without_user_prompt_still_marks_omission():
    from clawmetry.sync import _cap_transcript_messages
    msgs = [{"role": "assistant", "content": f"reply {i}", "timestamp": 1000 + i}
            for i in range(100)]
    capped, truncated, _oldest = _cap_transcript_messages(msgs, 80)
    assert truncated is True
    assert capped[0]["role"] == "system"
    assert capped[0]["type"] == "history_gap"
    assert capped[0]["omitted"] == 100 - len(capped[1:])
    assert capped[-1]["content"] == "reply 99"


def test_cap_first_user_prompt_already_in_tail_not_duplicated():
    from clawmetry.sync import _cap_transcript_messages
    msgs = _msgs(100, first_user_at=95)
    capped, truncated, _oldest = _cap_transcript_messages(msgs, 80)
    assert truncated is True
    user_turns = [m for m in capped if m.get("role") == "user"]
    assert len(user_turns) == 1


# ── Transcript history paging (transcript_page shape + endpoint) ───────────
# The replay serves the newest window instantly (snapshot on cloud, capped
# fast path locally) and pages older history on demand: before_ts is an
# exclusive ms cursor, so walking next_before_ts backward covers the whole
# session with no duplicates and no gaps.


def _seed_paged_session(ls, sid, n=10):
    store = ls.get_store()
    for i in range(n):
        ts = f"2026-05-12T10:00:{i:02d}Z"
        role = "user" if i % 4 == 0 else "assistant"
        store.ingest(_ev(f"pg{i}", sid, role, f"msg {i}", ts))
    _drain(store)
    return store


def test_query_transcript_page_walks_backward_without_dupes_or_gaps(app):
    a, ls = app
    sid = "sess-paging"
    store = _seed_paged_session(ls, sid, n=10)

    seen = []
    cursor = None
    for _ in range(20):  # bounded walk
        page = store.query_transcript_page(
            session_id=sid, before_ts=cursor, limit=3)
        if not page["rows"]:
            assert page["has_more"] is False
            break
        seen.extend(r["id"] for r in page["rows"])
        cursor = page["next_before_ts"]
        if not page["has_more"]:
            break
    # Every event exactly once, newest-first.
    assert seen == [f"pg{i}" for i in range(9, -1, -1)]


def test_query_transcript_page_cursor_is_exclusive(app):
    a, ls = app
    sid = "sess-paging-excl"
    store = _seed_paged_session(ls, sid, n=5)
    first = store.query_transcript_page(session_id=sid, limit=2)
    assert [r["id"] for r in first["rows"]] == ["pg4", "pg3"]
    assert first["has_more"] is True
    second = store.query_transcript_page(
        session_id=sid, before_ts=first["next_before_ts"], limit=2)
    assert [r["id"] for r in second["rows"]] == ["pg2", "pg1"]


def test_transcript_page_endpoint_renders_messages(app):
    a, ls = app
    sid = "sess-paging-http"
    _seed_paged_session(ls, sid, n=8)
    c = a.test_client()
    r = c.get(f"/api/transcript-page/{sid}?limit=3")
    assert r.status_code == 200
    body = r.get_json()
    assert body["has_more"] is True
    assert body["next_before_ts"]
    # Rendered messages come oldest-first within the page and carry content.
    contents = [m["content"] for m in body["messages"]]
    assert contents == ["msg 5", "msg 6", "msg 7"]
    # Walk one page older through the cursor.
    r2 = c.get(
        f"/api/transcript-page/{sid}?limit=3&before_ts={body['next_before_ts']}")
    body2 = r2.get_json()
    assert [m["content"] for m in body2["messages"]] == ["msg 2", "msg 3", "msg 4"]


def test_transcript_fast_path_caps_to_newest_window(app, monkeypatch):
    """A session past the message cap serves the NEWEST window (opening
    prompt + omission marker + tail) and stamps paging metadata — the old
    head-keep bound hid the live end of long sessions."""
    a, ls = app
    import routes.sessions as sessions_mod
    store = ls.get_store()
    sid = "sess-longcap"
    for i in range(30):
        ts = f"2026-05-12T11:{i // 60:02d}:{i % 60:02d}Z"
        role = "user" if i == 0 else "assistant"
        store.ingest(_ev(f"lc{i}", sid, role, f"turn {i}", ts))
    _drain(store)
    t = sessions_mod._try_local_store_transcript(sid, _msg_cap=10)
    assert t["_truncated"] is True
    assert t["messageCount"] == 30
    msgs = t["messages"]
    assert len(msgs) <= 10
    assert msgs[0]["content"] == "turn 0"          # opening prompt kept
    assert msgs[1]["role"] == "system"             # omission marker
    assert msgs[-1]["content"] == "turn 29"        # newest end visible
    assert t["_oldest_contiguous_ts"] == msgs[2]["timestamp"]


def test_render_transcript_page_renders_and_strips_for_relay(app, monkeypatch):
    """Daemon-side relay answer: raw page rows become rendered messages via
    the shared builder, with paging metadata carried through and raw payloads
    stripped (snapshot size discipline)."""
    a, ls = app
    from clawmetry import sync as sync_mod
    rows = [
        _ev("r2", "sess-relay", "assistant", "the reply", "2026-05-12T10:00:02Z"),
        _ev("r1", "sess-relay", "user", "the ask", "2026-05-12T10:00:01Z"),
    ]
    # _ev returns ingest-shaped rows (data is a JSON string); query rows carry
    # decoded dicts — decode to match what query_transcript_page hands over.
    for r in rows:
        r["data"] = json.loads(r["data"])
    page = {"rows": rows, "has_more": True, "next_before_ts": 1234}
    out = sync_mod._render_transcript_page(page, {"session_id": "sess-relay"})
    assert out["has_more"] is True
    assert out["next_before_ts"] == 1234
    contents = [m["content"] for m in out["messages"]]
    assert contents == ["the ask", "the reply"]
    assert all("raw" not in m for m in out["messages"])


def test_render_transcript_page_never_raises_on_garbage():
    from clawmetry import sync as sync_mod
    out = sync_mod._render_transcript_page(None, None)
    assert out["messages"] == [] and out["has_more"] is False
    out2 = sync_mod._render_transcript_page({"rows": [{"broken": True}]}, {})
    assert isinstance(out2["messages"], list)
