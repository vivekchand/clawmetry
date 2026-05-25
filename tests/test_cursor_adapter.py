"""Tests for clawmetry/adapters/cursor.py.

Exercises CursorAdapter against a generated Cursor ``state.vscdb`` fixture
(tests/fixtures/runtimes/cursor/...) built by _make_fixture.py, which mirrors
the REAL Cursor key/value structure captured on macOS:

  * global ItemTable index   composer.composerHeaders -> allComposers
  * global cursorDiskKV       composerData:<id>  +  bubbleId:<id>:<bid> rows
  * BOTH message shapes       fullConversationHeadersOnly+rows (newer) AND
                              inline conversationMap (older)
  * per-workspace legacy      aiService.prompts / aiService.generations

Covers: detection (session count across global + workspace DBs), session
summaries (titles from name / first user message, model from modelConfig,
ms->s timestamps), event roles/order/tool-calls for both storage shapes,
the unknown-on-disk reality (no billed tokens / cost), read-only (the DB file
is never mutated by reads), and the never-raises contract on corrupt/missing
DBs.
"""
from __future__ import annotations

import importlib.util
import os
import sqlite3

import pytest

from clawmetry.adapters.base import Capability, Event, Session
from clawmetry.adapters.cursor import CursorAdapter

_FIX_DIR = os.path.join(os.path.dirname(__file__), "fixtures", "runtimes", "cursor")
_GEN_PATH = os.path.join(_FIX_DIR, "_make_fixture.py")

# Composer ids the fixture seeds (must match _make_fixture.py).
_AGENT_ID = "2bfaf51e-b8da-4800-933b-1e217d08d5ba"  # newer header+rows format
_CHAT_ID = "3f582f7c-801d-4f75-9bff-3be4b2368251"   # inline conversationMap


def _load_generator():
    spec = importlib.util.spec_from_file_location("_cursor_fixture_gen", _GEN_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture
def global_db(tmp_path):
    """Freshly materialised Cursor profile; returns the GLOBAL state.vscdb path."""
    gen = _load_generator()
    return gen.make_fixture(str(tmp_path / "cursor"))


@pytest.fixture
def global_db_no_ws(tmp_path):
    """Profile with ONLY the global DB (no per-workspace legacy bucket)."""
    gen = _load_generator()
    return gen.make_fixture(str(tmp_path / "cursor"), with_workspace=False)


# ── committed fixtures sanity ────────────────────────────────────────────


def test_committed_fixtures_exist():
    db = os.path.join(_FIX_DIR, "data", "User", "globalStorage", "state.vscdb")
    assert os.path.isfile(db)
    assert CursorAdapter(db_path=db).detect().detected is True


# ── detect ───────────────────────────────────────────────────────────────


def test_detect_when_present(global_db):
    r = CursorAdapter(db_path=global_db).detect()
    assert r.detected is True
    assert r.name == "cursor"
    assert r.display_name == "Cursor"
    assert r.running is False
    # 2 composer sessions (global) + 1 legacy aiService bucket (workspace)
    assert r.session_count == 3
    assert Capability.SESSIONS.value in r.capabilities
    assert Capability.EVENTS.value in r.capabilities
    assert r.meta["dbPath"] == global_db


def test_detect_global_only(global_db_no_ws):
    r = CursorAdapter(db_path=global_db_no_ws).detect()
    assert r.detected is True
    # only the 2 composer sessions, no workspace legacy bucket
    assert r.session_count == 2


def test_detect_missing_db():
    r = CursorAdapter(db_path="/no/such/Cursor/User/globalStorage/state.vscdb").detect()
    assert r.detected is False
    assert r.session_count == 0
    # capabilities still advertised so the chip bar can show a grey dot
    assert Capability.SESSIONS.value in r.capabilities


def test_detect_empty_db(tmp_path):
    # A real vscdb with the tables but zero chat rows -> not detected.
    db = tmp_path / "state.vscdb"
    conn = sqlite3.connect(str(db))
    gen = _load_generator()
    conn.executescript(gen.SCHEMA)
    conn.commit()
    conn.close()
    r = CursorAdapter(db_path=str(db)).detect()
    assert r.detected is False
    assert r.session_count == 0


# ── list_sessions ──────────────────────────────────────────────────────────


def test_list_sessions_count_and_ids(global_db):
    sessions = CursorAdapter(db_path=global_db).list_sessions()
    ids = {s.id for s in sessions}
    assert _AGENT_ID in ids
    assert _CHAT_ID in ids
    assert any(s.id.startswith("aiservice:") for s in sessions)
    assert all(isinstance(s, Session) for s in sessions)
    assert all(s.agent == "cursor" for s in sessions)


def test_list_sessions_titles(global_db):
    by_id = {s.id: s for s in CursorAdapter(db_path=global_db).list_sessions()}
    # AGENT session has an explicit name in composerData.
    assert by_id[_AGENT_ID].title == "Ship the cursor adapter"
    assert by_id[_AGENT_ID].display_name == "Ship the cursor adapter"
    # CHAT session has NO name -> title falls back to first user message.
    assert by_id[_CHAT_ID].title == "how do I read Cursor chats?"


def test_list_sessions_model_from_modelconfig(global_db):
    by_id = {s.id: s for s in CursorAdapter(db_path=global_db).list_sessions()}
    # Cursor records the chosen model in composerData.modelConfig.
    assert by_id[_AGENT_ID].model == "claude-4.6-sonnet"
    # CHAT session set no model -> honestly empty.
    assert by_id[_CHAT_ID].model == ""


def test_list_sessions_message_counts(global_db):
    by_id = {s.id: s for s in CursorAdapter(db_path=global_db).list_sessions()}
    assert by_id[_AGENT_ID].message_count == 3  # 3 bubbles (header+rows)
    assert by_id[_CHAT_ID].message_count == 2   # 2 bubbles (inline map)


def test_list_sessions_timestamps_ms_to_seconds(global_db):
    by_id = {s.id: s for s in CursorAdapter(db_path=global_db).list_sessions()}
    s = by_id[_AGENT_ID]
    # createdAt 1779182203579 ms -> ~1779182203.579 s
    assert s.started_at == pytest.approx(1779182203.579, abs=0.01)
    assert s.ended_at is not None
    assert s.ended_at >= s.started_at
    assert s.started_at < 1e12  # in SECONDS, not milliseconds


def test_list_sessions_no_cost_or_tokens(global_db):
    """Cursor stores no billed token total / dollar cost on disk."""
    for s in CursorAdapter(db_path=global_db).list_sessions():
        assert s.total_tokens == 0
        assert s.input_tokens == 0
        assert s.output_tokens == 0
        assert s.cost_usd is None


def test_list_sessions_newest_first(global_db):
    sessions = CursorAdapter(db_path=global_db).list_sessions()
    # CHAT session (createdAt 1779182300000) is newer than AGENT (1779182203579).
    ordered = [s.id for s in sessions if s.id in (_AGENT_ID, _CHAT_ID)]
    assert ordered == [_CHAT_ID, _AGENT_ID]


# ── list_events: newer header+rows format ──────────────────────────────────


def test_list_events_header_rows_roles_and_order(global_db):
    events = CursorAdapter(db_path=global_db).list_events(_AGENT_ID)
    assert all(isinstance(e, Event) for e in events)
    assert [e.role for e in events] == ["user", "assistant", "assistant"]
    # chronological by bubble ts
    ts = [e.ts for e in events]
    assert ts == sorted(ts)
    # type 1 -> user, type 2 -> assistant surfaced in extra
    assert [e.extra.get("bubbleType") for e in events] == [1, 2, 2]


def test_list_events_header_rows_content_and_bubble_ids(global_db):
    events = CursorAdapter(db_path=global_db).list_events(_AGENT_ID)
    assert events[0].id == "b1"
    assert events[0].content == "write the Cursor adapter"
    assert events[1].content == "on it - reading the vscdb schema now"


def test_list_events_tool_call_extracted(global_db):
    events = CursorAdapter(db_path=global_db).list_events(_AGENT_ID)
    tool_ev = events[2]
    assert tool_ev.type == "tool_call"
    assert tool_ev.tool_name == "read_file"
    assert tool_ev.tool_calls and tool_ev.tool_calls[0]["name"] == "read_file"
    assert tool_ev.tool_calls[0]["status"] == "completed"


def test_list_events_token_count_is_hint_not_billed(global_db):
    events = CursorAdapter(db_path=global_db).list_events(_AGENT_ID)
    # The assistant bubble carried tokenCount=128 -> surfaced as a HINT only,
    # never promoted to Event.tokens (billed total is unknown on disk).
    assert events[1].extra.get("tokenCountHint") == 128
    assert all(e.tokens == 0 for e in events)


# ── list_events: older inline conversationMap format ───────────────────────


def test_list_events_inline_map_roles_and_richtext(global_db):
    events = CursorAdapter(db_path=global_db).list_events(_CHAT_ID)
    assert [e.role for e in events] == ["user", "assistant"]
    assert events[0].content == "how do I read Cursor chats?"
    # assistant bubble had empty text but a richText doc -> flattened to text
    assert events[1].content == "open state.vscdb read-only"


# ── list_events: legacy aiService bucket ───────────────────────────────────


def test_list_events_legacy_aiservice(global_db):
    a = CursorAdapter(db_path=global_db)
    legacy = next(s for s in a.list_sessions() if s.id.startswith("aiservice:"))
    events = a.list_events(legacy.id)
    roles = [e.role for e in events]
    assert roles.count("user") == 2
    assert roles.count("assistant") == 1
    assert events[0].content == "legacy: refactor the parser"


def test_list_events_unknown_session(global_db):
    assert CursorAdapter(db_path=global_db).list_events("nope-not-a-real-id") == []


# ── capabilities (honesty) ─────────────────────────────────────────────────


def test_capabilities_only_sessions_and_events():
    caps = CursorAdapter().capabilities()
    assert caps == {Capability.SESSIONS, Capability.EVENTS}
    assert Capability.COST not in caps
    assert Capability.SUBAGENTS not in caps
    assert Capability.CRONS not in caps
    assert Capability.GATEWAY_RPC not in caps


# ── read-only contract ─────────────────────────────────────────────────────


def test_read_only_does_not_modify_db(global_db):
    """Reads must not change the DB file mtime/size."""
    before = os.stat(global_db)
    a = CursorAdapter(db_path=global_db)
    a.detect()
    a.list_sessions()
    a.list_events(_AGENT_ID)
    a.list_events(_CHAT_ID)
    after = os.stat(global_db)
    assert before.st_size == after.st_size
    assert before.st_mtime == after.st_mtime


# ── never-raises contract ───────────────────────────────────────────────────


def test_never_raises_on_corrupt_db(tmp_path):
    db = tmp_path / "User" / "globalStorage" / "state.vscdb"
    db.parent.mkdir(parents=True)
    db.write_bytes(b"this is definitely not a sqlite database")
    a = CursorAdapter(db_path=str(db))
    # None of these may raise.
    r = a.detect()
    assert isinstance(r.detected, bool)
    assert a.list_sessions() == []
    assert a.list_events("anything") == []


def test_never_raises_on_missing_db():
    a = CursorAdapter(db_path="/definitely/not/here/state.vscdb")
    assert a.detect().detected is False
    assert a.list_sessions() == []
    assert a.list_events("x") == []


def test_never_raises_on_malformed_composer_blob(tmp_path):
    """A composerData row whose value is not valid JSON must be skipped."""
    db = tmp_path / "state.vscdb"
    conn = sqlite3.connect(str(db))
    gen = _load_generator()
    conn.executescript(gen.SCHEMA)
    conn.execute(
        "INSERT INTO cursorDiskKV (key, value) VALUES (?, ?)",
        ("composerData:broken", "{not valid json"),
    )
    conn.commit()
    conn.close()
    a = CursorAdapter(db_path=str(db))
    assert a.detect().detected is False  # the only row was unparseable
    assert a.list_sessions() == []
    assert a.list_events("broken") == []
