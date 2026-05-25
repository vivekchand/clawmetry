"""Tests for clawmetry/adapters/goose.py.

Exercises GooseAdapter against the committed SQLite fixture
(tests/fixtures/runtimes/goose/sessions/sessions.db) built by
_make_fixture.py from a real Goose 1.35.0 capture, plus a regenerated
tmp-path copy so tests never depend on a stale committed DB.

Covers: detection (count = session rows), session summary (model from
model_config_json, real token totals, message_count, timestamps), event
parsing (text messages + tool_call/tool_result blocks, chronological,
isError surfaced), the COST capability (Goose records real tokens), the
read-only contract (DB mtime/size unchanged), and the never-raises contract
against missing / corrupt DBs.
"""
from __future__ import annotations

import importlib.util
import os
import sqlite3

import pytest

from clawmetry.adapters.base import Capability, Event, Session
from clawmetry.adapters.goose import GooseAdapter, _parse_ts

_FIX_DIR = os.path.join(os.path.dirname(__file__), "fixtures", "runtimes", "goose")
_GEN_PATH = os.path.join(_FIX_DIR, "_make_fixture.py")
_COMMITTED_DB = os.path.join(_FIX_DIR, "sessions", "sessions.db")


def _load_generator():
    spec = importlib.util.spec_from_file_location("_goose_fixture_gen", _GEN_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture
def db_path(tmp_path):
    """Freshly materialised sessions.db (independent of the committed DB)."""
    gen = _load_generator()
    return gen.make_fixture(str(tmp_path / "sessions" / "sessions.db"))


# ── committed fixture sanity ──────────────────────────────────────────────


def test_committed_fixture_exists():
    assert os.path.isfile(_COMMITTED_DB)
    assert GooseAdapter(db_path=_COMMITTED_DB).detect().detected is True


# ── detect ─────────────────────────────────────────────────────────────────


def test_detect_when_present(db_path):
    r = GooseAdapter(db_path=db_path).detect()
    assert r.detected is True
    assert r.name == "goose"
    assert r.display_name == "Goose"
    assert r.running is False
    assert r.session_count == 3
    assert Capability.SESSIONS.value in r.capabilities
    assert Capability.EVENTS.value in r.capabilities
    assert Capability.COST.value in r.capabilities
    assert r.meta["dbPath"] == db_path


def test_detect_missing_db():
    r = GooseAdapter(db_path="/no/such/goose/sessions.db").detect()
    assert r.detected is False
    assert r.session_count == 0
    # capabilities still advertised so the chip bar can show a grey dot
    assert Capability.SESSIONS.value in r.capabilities


def test_detect_empty_db(tmp_path):
    # A valid DB with the schema but zero session rows -> not detected.
    gen = _load_generator()
    db = str(tmp_path / "empty.db")
    os.makedirs(os.path.dirname(db) or ".", exist_ok=True)
    conn = sqlite3.connect(db)
    conn.executescript(gen.SCHEMA)
    conn.commit()
    conn.close()
    r = GooseAdapter(db_path=db).detect()
    assert r.detected is False
    assert r.session_count == 0


# ── list_sessions ────────────────────────────────────────────────────────────


def test_list_sessions_count_and_newest_first(db_path):
    sessions = GooseAdapter(db_path=db_path).list_sessions()
    assert len(sessions) == 3
    assert all(isinstance(s, Session) for s in sessions)
    # newest (highest updated_at) first
    assert [s.id for s in sessions] == ["20260525_3", "20260525_2", "20260525_1"]


def test_list_sessions_model_title_provider(db_path):
    by_id = {s.id: s for s in GooseAdapter(db_path=db_path).list_sessions()}
    s1 = by_id["20260525_1"]
    assert s1.agent == "goose"
    # model comes from model_config_json -> model_name
    assert s1.model == "llama3.2"
    # source/provider from provider_name
    assert s1.source == "ollama"
    assert s1.extra["provider"] == "ollama"
    # title from the session name
    assert s1.title == "Python HelloWorld Example"
    assert s1.display_name == "Python HelloWorld Example"


def test_list_sessions_real_tokens(db_path):
    """Goose DOES record real token usage on disk (unlike Pico/NanoClaw)."""
    by_id = {s.id: s for s in GooseAdapter(db_path=db_path).list_sessions()}
    s3 = by_id["20260525_3"]
    assert s3.total_tokens == 16389
    assert s3.input_tokens == 6552
    assert s3.output_tokens == 20
    # local Ollama records no USD -> honest None / unavailable
    assert s3.cost_usd is None
    assert s3.cost_status == "unavailable"


def test_list_sessions_message_count(db_path):
    by_id = {s.id: s for s in GooseAdapter(db_path=db_path).list_sessions()}
    assert by_id["20260525_1"].message_count == 2
    assert by_id["20260525_3"].message_count == 6


def test_list_sessions_timestamps(db_path):
    by_id = {s.id: s for s in GooseAdapter(db_path=db_path).list_sessions()}
    s1 = by_id["20260525_1"]
    # created_at "2026-05-25 19:51:12" / updated_at "...19:51:18" (UTC text)
    assert s1.started_at == pytest.approx(_parse_ts("2026-05-25 19:51:12"))
    assert s1.ended_at == pytest.approx(_parse_ts("2026-05-25 19:51:18"))
    assert s1.started_at < s1.ended_at


def test_list_sessions_limit(db_path):
    sessions = GooseAdapter(db_path=db_path).list_sessions(limit=1)
    assert len(sessions) == 1
    assert sessions[0].id == "20260525_3"


# ── list_events ──────────────────────────────────────────────────────────────


def test_list_events_text_messages(db_path):
    events = GooseAdapter(db_path=db_path).list_events("20260525_1")
    assert all(isinstance(e, Event) for e in events)
    assert [e.role for e in events] == ["user", "assistant"]
    assert all(e.type == "message" for e in events)
    assert events[0].content == "Write a one-line Python hello world and explain it."
    assert "print(" in events[1].content


def test_list_events_tool_call_and_result(db_path):
    events = GooseAdapter(db_path=db_path).list_events("20260525_3")
    types = [e.type for e in events]
    # user msg, tool_call, tool_result, tool_call, tool_result, assistant msg
    assert types == [
        "message", "tool_call", "tool_result",
        "tool_call", "tool_result", "message",
    ]
    # tool_call carries the tool name + extension
    tc = events[1]
    assert tc.tool_name == "shell"
    assert tc.role == "assistant"
    assert tc.extra["extension"] == "developer"
    assert tc.tool_calls[0]["name"] == "shell"
    # tool_result carries text + classified as role 'tool'
    tr = events[2]
    assert tr.role == "tool"
    assert tr.content == "hello-from-goose\n"
    assert tr.extra["isError"] is False
    assert tr.extra["toolCallId"] == "call_demo01"


def test_list_events_tool_error_surfaced(db_path):
    events = GooseAdapter(db_path=db_path).list_events("20260525_3")
    err = events[4]
    assert err.type == "tool_result"
    assert err.extra["isError"] is True
    assert "Error" in err.content


def test_list_events_chronological(db_path):
    events = GooseAdapter(db_path=db_path).list_events("20260525_3")
    ts = [e.ts for e in events]
    assert ts == sorted(ts)


def test_list_events_unknown_session(db_path):
    assert GooseAdapter(db_path=db_path).list_events("nope") == []


def test_list_events_limit(db_path):
    events = GooseAdapter(db_path=db_path).list_events("20260525_3", limit=2)
    assert len(events) == 2


# ── capabilities (honesty) ───────────────────────────────────────────────────


def test_capabilities_includes_cost():
    caps = GooseAdapter().capabilities()
    assert caps == {Capability.SESSIONS, Capability.EVENTS, Capability.COST}
    # honest scope: we do NOT advertise what we don't implement
    assert Capability.SUBAGENTS not in caps
    assert Capability.CRONS not in caps
    assert Capability.GATEWAY_RPC not in caps


# ── never-raises contract ────────────────────────────────────────────────────


def test_never_raises_on_corrupt_db(tmp_path):
    db = tmp_path / "sessions.db"
    db.write_bytes(b"this is not a sqlite database")
    adapter = GooseAdapter(db_path=str(db))
    # None of these may raise.
    r = adapter.detect()
    assert r.detected is False
    assert isinstance(adapter.list_sessions(), list)
    assert adapter.list_events("x") == []


def test_never_raises_on_missing_db():
    adapter = GooseAdapter(db_path="/definitely/not/here/sessions.db")
    assert adapter.detect().detected is False
    assert adapter.list_sessions() == []
    assert adapter.list_events("x") == []


def test_never_raises_on_garbage_content_json(tmp_path):
    """A row with non-JSON / unexpected content_json must not crash parsing."""
    gen = _load_generator()
    db = str(tmp_path / "garbage.db")
    os.makedirs(os.path.dirname(db) or ".", exist_ok=True)
    conn = sqlite3.connect(db)
    conn.executescript(gen.SCHEMA)
    conn.execute(
        "INSERT INTO sessions (id, working_dir, created_at, updated_at, "
        "total_tokens, provider_name, model_config_json) "
        "VALUES ('g1', '/tmp', '2026-05-25 10:00:00', '2026-05-25 10:00:01', "
        "5, 'ollama', 'not-json')"
    )
    # content_json that is not a JSON array, plus one that is bad JSON entirely
    conn.execute(
        "INSERT INTO messages (session_id, role, content_json, created_timestamp) "
        "VALUES ('g1', 'user', '{\"unexpected\":\"object\"}', 1779738672)"
    )
    conn.execute(
        "INSERT INTO messages (session_id, role, content_json, created_timestamp) "
        "VALUES ('g1', 'assistant', 'totally not json', 1779738673)"
    )
    conn.commit()
    conn.close()
    adapter = GooseAdapter(db_path=db)
    assert adapter.detect().detected is True
    sessions = adapter.list_sessions()
    assert len(sessions) == 1
    # bad model_config_json falls back to provider name
    assert sessions[0].model == "ollama"
    # parsing the garbage rows must not raise
    events = adapter.list_events("g1")
    assert isinstance(events, list)
    # the bare-string content surfaces as a text message
    assert any("totally not json" in e.content for e in events)


# ── read-only contract ───────────────────────────────────────────────────────


def test_read_only_does_not_modify_db(db_path):
    """Reading must not change the DB file mtime/size (read-only open)."""
    before = os.stat(db_path)
    a = GooseAdapter(db_path=db_path)
    a.detect()
    a.list_sessions()
    a.list_events("20260525_3")
    after = os.stat(db_path)
    assert before.st_size == after.st_size
    assert before.st_mtime == after.st_mtime
