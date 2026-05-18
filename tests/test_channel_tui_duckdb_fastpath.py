"""Regression guard for the /api/channel/tui DuckDB fast path (issue #1656).

Until this fix landed, ``routes/channels.py:api_channel_tui`` was the last
Tier-1 channel route still walking session JSONLs on every poll — the
2026-05-18 MOAT coverage audit flagged it as the sole remaining BYPASS
violation across all 230 dashboard endpoints.

The fix wires ``_try_local_store_channel_tui`` BEFORE the legacy JSONL
walker. Unlike Telegram/Signal/BlueBubbles (which carry dedicated
``channel.in`` / ``channel.out`` events), TUI turns live in the unified
``events`` table as ``prompt.submitted`` (user role) + ``model.completed``
(assistant role), with the ``openclaw-tui`` Sender marker preserved
verbatim inside ``data.finalPromptText`` by the daemon's v3 mapper
(``clawmetry/sync.py:_parse_v3_event``).

These tests assert:

  1. DuckDB-seeded ``prompt.submitted`` (with the TUI marker) + the next
     ``model.completed`` in the same session pair into the legacy
     ``{messages, todayIn, todayOut, total, status}`` envelope.
  2. The Sender-block JSON preamble is stripped from the rendered user
     bubble (matches the legacy walker's ``_strip_sender_block`` shape).
  3. A ``prompt.submitted`` row WITHOUT the ``openclaw-tui`` marker
     (e.g. an inbound from Telegram via the same session JSONL) does
     NOT surface on the TUI route — guards the silent-zero bug class
     memory ``feedback_synthetic_tests_missed_real_event_shape.md``
     warns about.
  4. Empty DuckDB → helper returns ``None`` so the route falls through
     to the legacy JSONL walker (which on a test box with no sessions
     dir returns ``status='no sessions dir'`` — confirms the
     ``_source='local_store_v3'`` tag is reserved for the fast path).

The test fixture isolates DuckDB to a tmp_path (mirrors
``tests/test_channel_bluebubbles_local_store_v3.py``) and shorts out
the daemon-proxy discovery so a contributor's running daemon doesn't
serve stale rows out of its own production DuckDB.
"""

from __future__ import annotations

import importlib
import uuid
from datetime import datetime, timedelta, timezone

import pytest
from flask import Flask


def _now_iso() -> str:
    return datetime.now(tz=timezone.utc).isoformat()


def _iso_seconds_offset(seconds: int) -> str:
    return (datetime.now(tz=timezone.utc) + timedelta(seconds=seconds)).isoformat()


def _seed_tui_prompt(
    store,
    *,
    body: str,
    session_id: str,
    ts: str | None = None,
    with_marker: bool = True,
):
    """Seed one ``prompt.submitted`` event in the exact shape
    ``sync._parse_v3_event`` writes for a TUI user turn — Sender block
    preamble preserved in ``data.finalPromptText``.

    ``with_marker=False`` produces a non-TUI prompt (no ``openclaw-tui``
    marker) so we can prove the helper filters by marker, not by event
    type alone."""
    if with_marker:
        text = (
            '```json\n'
            '{"channel":"openclaw-tui","user":"vivek"}\n'
            '```\n'
            + body
        )
    else:
        text = body
    store.ingest({
        "id":         f"prompt-{uuid.uuid4().hex[:12]}",
        "node_id":    "node-test",
        "agent_type": "openclaw",
        "agent_id":   "main",
        "event_type": "prompt.submitted",
        "ts":         ts or _now_iso(),
        "session_id": session_id,
        "workspace_id": None,
        "data": {
            "finalPromptText": text,
            "timestamp":       ts or _now_iso(),
            "type":            "prompt.submitted",
            "data":            {"finalPromptText": text},
        },
        "cost_usd":    None,
        "token_count": None,
        "model":       None,
    })


def _seed_assistant_reply(
    store,
    *,
    completion_text: str,
    session_id: str,
    ts: str | None = None,
):
    """Seed one ``model.completed`` event in the same shape
    ``sync._parse_v3_event`` writes for an assistant turn."""
    store.ingest({
        "id":         f"completion-{uuid.uuid4().hex[:12]}",
        "node_id":    "node-test",
        "agent_type": "openclaw",
        "agent_id":   "main",
        "event_type": "model.completed",
        "ts":         ts or _now_iso(),
        "session_id": session_id,
        "workspace_id": None,
        "data": {
            "completionText": completion_text,
            "assistantTexts": [completion_text] if completion_text else [],
            "modelId":        "claude-opus-4-7",
            "timestamp":      ts or _now_iso(),
            "type":           "model.completed",
            "data":           {"completionText": completion_text},
        },
        "cost_usd":    0.001,
        "token_count": 50,
        "model":       "claude-opus-4-7",
    })


@pytest.fixture
def app(tmp_path, monkeypatch):
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "events.duckdb"))
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_SECS", "0.05")
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_READ", "1")
    # Point SESSIONS_DIR at an empty tmp dir so the legacy JSONL walker
    # path (used for the empty-DuckDB fallback test) returns the
    # well-known "no sessions dir" envelope instead of leaking events
    # from a contributor's real ~/.openclaw.
    empty_sessions = tmp_path / "empty_sessions"
    empty_sessions.mkdir()

    import clawmetry.local_store as ls
    importlib.reload(ls)
    import routes.local_query as lq
    importlib.reload(lq)
    import routes.channels as channels_mod
    importlib.reload(channels_mod)

    monkeypatch.setattr(lq, "_read_discovery", lambda: None)

    import dashboard  # noqa: F401

    # Override the dashboard's SESSIONS_DIR so the legacy walker has
    # nothing to read — this isolates the fallback assertion from any
    # ambient OpenClaw install on the test machine.
    monkeypatch.setattr(dashboard, "SESSIONS_DIR", str(tmp_path / "missing_sessions"))

    a = Flask(__name__)
    a.register_blueprint(channels_mod.bp_channels)
    yield a, ls, channels_mod
    try:
        ls.get_store().stop(flush=True)
    except Exception:
        pass


def test_tui_v3_fast_path_serves_when_duckdb_has_tui_prompts(app):
    """Seeded TUI ``prompt.submitted`` + next ``model.completed`` pair
    into the legacy envelope and the response is tagged
    ``_source='local_store_v3'`` (audit canary for the fast path)."""
    a, ls, _c = app
    store = ls.get_store()
    sid = "sess-tui-1"
    prompt_ts = _iso_seconds_offset(-60)
    reply_ts = _iso_seconds_offset(-30)
    _seed_tui_prompt(store, body="hello clawd", session_id=sid, ts=prompt_ts)
    _seed_assistant_reply(
        store, completion_text="hi from clawd", session_id=sid, ts=reply_ts,
    )
    store.flush()

    # Contract check: DuckDB has the rows the fast path needs.
    assert len(store.query_events(event_type="prompt.submitted", limit=5)) >= 1
    assert len(store.query_events(event_type="model.completed", limit=5)) >= 1

    r = a.test_client().get("/api/channel/tui?limit=10")
    assert r.status_code == 200, r.get_data(as_text=True)
    body = r.get_json()
    assert body.get("_source") == "local_store_v3", (
        f"_source must be local_store_v3 (DuckDB fast path); got "
        f"{body.get('_source')!r}"
    )
    msgs = body.get("messages") or []
    assert len(msgs) == 2, f"expected 1 in + 1 out, got {len(msgs)}"
    # Newest-first: assistant reply (ts=-30s) precedes user prompt (ts=-60s).
    assert msgs[0]["direction"] == "out"
    assert msgs[0]["text"] == "hi from clawd"
    assert msgs[0]["sender"] == "Clawd"
    assert msgs[1]["direction"] == "in"
    assert msgs[1]["text"] == "hello clawd", (
        f"Sender block must be stripped from the rendered bubble; got "
        f"{msgs[1]['text']!r}"
    )
    assert msgs[1]["sender"] == "User"


def test_tui_v3_fast_path_strips_sender_block_preamble(app):
    """The ```json {...}``` Sender-block preamble that the OpenClaw TUI
    writes into ``finalPromptText`` MUST be stripped before the body is
    handed to the UI — matches the legacy walker's
    ``_strip_sender_block`` shape so the dashboard render path stays
    identical between the fast path and the fallback."""
    a, ls, _c = app
    store = ls.get_store()
    _seed_tui_prompt(
        store,
        body="real user message",
        session_id="sess-tui-strip",
        ts=_now_iso(),
    )
    store.flush()

    r = a.test_client().get("/api/channel/tui?limit=10")
    body = r.get_json()
    assert body.get("_source") == "local_store_v3"
    msgs = body.get("messages") or []
    assert len(msgs) == 1
    rendered = msgs[0]["text"]
    assert "```json" not in rendered, (
        f"Sender-block fence must be stripped; got {rendered!r}"
    )
    assert "openclaw-tui" not in rendered, (
        f"Sender-block marker must be stripped; got {rendered!r}"
    )
    assert rendered == "real user message"


def test_tui_v3_fast_path_ignores_non_tui_prompts(app):
    """A ``prompt.submitted`` row WITHOUT the ``openclaw-tui`` marker
    (e.g. an inbound from Telegram routed through the same session
    JSONL) MUST NOT surface on the TUI route. Guards the silent-zero
    bug class memory ``feedback_synthetic_tests_missed_real_event_shape.md``
    warns about — easy to write a helper that grabs ALL prompts and
    inflate the TUI counters with cross-channel turns."""
    a, ls, _c = app
    store = ls.get_store()
    _seed_tui_prompt(
        store, body="real tui prompt", session_id="sess-1", ts=_now_iso(),
    )
    _seed_tui_prompt(
        store,
        body="this is from telegram, not TUI",
        session_id="sess-1",
        ts=_now_iso(),
        with_marker=False,
    )
    store.flush()

    r = a.test_client().get("/api/channel/tui?limit=10")
    body = r.get_json()
    assert body.get("_source") == "local_store_v3"
    msgs = body.get("messages") or []
    inbound = [m for m in msgs if m["direction"] == "in"]
    assert len(inbound) == 1, (
        f"only the TUI-tagged prompt should surface; got {len(inbound)} "
        f"rows: {[m['text'] for m in inbound]}"
    )
    assert inbound[0]["text"] == "real tui prompt"


def test_tui_v3_fast_path_empty_falls_back_to_legacy_walker(app):
    """Empty DuckDB → helper returns ``None`` so the route falls through
    to the legacy JSONL walker. The walker on a test box with no
    sessions dir returns the well-known ``status='no sessions dir'``
    envelope; the ``_source='local_store_v3'`` tag MUST NOT be present
    (it is reserved for the fast path)."""
    a, ls, _c = app
    assert ls.get_store().query_events(
        event_type="prompt.submitted", limit=5,
    ) == []

    r = a.test_client().get("/api/channel/tui?limit=10")
    assert r.status_code == 200
    body = r.get_json()
    assert body.get("_source") != "local_store_v3", (
        "empty DuckDB → must defer to legacy walker; got "
        f"_source={body.get('_source')!r}"
    )
    # Legacy walker's well-known shape — confirms the fallback executed.
    assert body.get("status") == "no sessions dir"
    assert body.get("messages") == []


def test_tui_v3_fast_path_today_counters_use_iso_prefix(app):
    """``todayIn`` / ``todayOut`` use the ``YYYY-MM-DD`` ISO prefix on
    the daemon's ts strings. Seed a fresh-today TUI pair + an ancient
    2024 pair and confirm only today's rows are counted (guards against
    the loose substring match the 2026-05-17 audit flagged in a peer
    route)."""
    a, ls, _c = app
    store = ls.get_store()
    # Today's pair.
    _seed_tui_prompt(
        store, body="today msg", session_id="sess-today", ts=_now_iso(),
    )
    _seed_assistant_reply(
        store,
        completion_text="today reply",
        session_id="sess-today",
        ts=_iso_seconds_offset(5),
    )
    # Ancient 2024 pair.
    _seed_tui_prompt(
        store,
        body="ancient msg",
        session_id="sess-ancient",
        ts="2024-01-01T08:30:00+00:00",
    )
    _seed_assistant_reply(
        store,
        completion_text="ancient reply",
        session_id="sess-ancient",
        ts="2024-01-01T08:30:05+00:00",
    )
    store.flush()

    r = a.test_client().get("/api/channel/tui?limit=20")
    body = r.get_json()
    assert body.get("_source") == "local_store_v3"
    assert body.get("todayIn") == 1, (
        f"only the today prompt counts; got todayIn={body.get('todayIn')}"
    )
    assert body.get("todayOut") == 1, (
        f"only the today reply counts; got todayOut={body.get('todayOut')}"
    )
    assert body.get("total") == 4
