"""Tests for clawmetry/adapters/hermes.py.

Builds a fixture SQLite DB matching Hermes's real schema (captured from
a live ``~/.hermes/state.db``) and exercises HermesAdapter against it
— detection, session list mapping (tokens/cost/parent link), event
decoding, and stream_events catching newly-inserted rows.
"""
from __future__ import annotations

import os
import sqlite3
import threading
import time

import pytest

from clawmetry.adapters.base import Capability, Session, Event
from clawmetry.adapters.hermes import HermesAdapter


HERMES_SCHEMA = """
CREATE TABLE sessions (
    id TEXT PRIMARY KEY,
    source TEXT NOT NULL,
    user_id TEXT,
    model TEXT,
    model_config TEXT,
    system_prompt TEXT,
    parent_session_id TEXT,
    started_at REAL NOT NULL,
    ended_at REAL,
    end_reason TEXT,
    message_count INTEGER DEFAULT 0,
    tool_call_count INTEGER DEFAULT 0,
    input_tokens INTEGER DEFAULT 0,
    output_tokens INTEGER DEFAULT 0,
    cache_read_tokens INTEGER DEFAULT 0,
    cache_write_tokens INTEGER DEFAULT 0,
    reasoning_tokens INTEGER DEFAULT 0,
    billing_provider TEXT,
    billing_base_url TEXT,
    billing_mode TEXT,
    estimated_cost_usd REAL,
    actual_cost_usd REAL,
    cost_status TEXT,
    cost_source TEXT,
    pricing_version TEXT,
    title TEXT
);
CREATE TABLE messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL REFERENCES sessions(id),
    role TEXT NOT NULL,
    content TEXT,
    tool_call_id TEXT,
    tool_calls TEXT,
    tool_name TEXT,
    timestamp REAL NOT NULL,
    token_count INTEGER,
    finish_reason TEXT,
    reasoning TEXT,
    reasoning_details TEXT,
    codex_reasoning_items TEXT
);
"""


@pytest.fixture
def hermes_home(tmp_path, monkeypatch):
    home = tmp_path / "hermes"
    home.mkdir()
    db_path = home / "state.db"
    conn = sqlite3.connect(str(db_path))
    conn.executescript(HERMES_SCHEMA)
    conn.commit()
    conn.close()
    monkeypatch.setenv("HERMES_HOME", str(home))
    yield home


@pytest.fixture
def hermes_db(hermes_home):
    return sqlite3.connect(str(hermes_home / "state.db"))


def _insert_session(conn, **overrides):
    defaults = {
        "id": "s1",
        "source": "cli",
        "user_id": "vivek",
        "model": "claude-sonnet-4-6",
        "parent_session_id": None,
        "started_at": 1_776_459_097.24,
        "ended_at": None,
        "end_reason": "",
        "message_count": 4,
        "input_tokens": 1234,
        "output_tokens": 567,
        "cache_read_tokens": 890,
        "cache_write_tokens": 12,
        "reasoning_tokens": 0,
        "estimated_cost_usd": 0.034,
        "actual_cost_usd": None,
        "cost_status": "estimated",
        "cost_source": "model_registry",
        "title": "test session",
    }
    defaults.update(overrides)
    conn.execute(
        "INSERT INTO sessions (id, source, user_id, model, parent_session_id, "
        "started_at, ended_at, end_reason, message_count, input_tokens, "
        "output_tokens, cache_read_tokens, cache_write_tokens, "
        "reasoning_tokens, estimated_cost_usd, actual_cost_usd, "
        "cost_status, cost_source, title) "
        "VALUES (:id, :source, :user_id, :model, :parent_session_id, "
        ":started_at, :ended_at, :end_reason, :message_count, :input_tokens, "
        ":output_tokens, :cache_read_tokens, :cache_write_tokens, "
        ":reasoning_tokens, :estimated_cost_usd, :actual_cost_usd, "
        ":cost_status, :cost_source, :title)",
        defaults,
    )


def _insert_message(conn, **overrides):
    defaults = {
        "session_id": "s1",
        "role": "user",
        "content": "hello",
        "tool_call_id": None,
        "tool_calls": None,
        "tool_name": None,
        "timestamp": 1_776_459_098.4,
        "token_count": 0,
        "finish_reason": None,
    }
    defaults.update(overrides)
    conn.execute(
        "INSERT INTO messages (session_id, role, content, tool_call_id, "
        "tool_calls, tool_name, timestamp, token_count, finish_reason) "
        "VALUES (:session_id, :role, :content, :tool_call_id, :tool_calls, "
        ":tool_name, :timestamp, :token_count, :finish_reason)",
        defaults,
    )


def test_detect_reports_not_detected_when_db_missing(tmp_path, monkeypatch):
    empty = tmp_path / "no-hermes"
    empty.mkdir()
    monkeypatch.setenv("HERMES_HOME", str(empty))
    r = HermesAdapter().detect()
    assert r.detected is False
    assert r.session_count == 0
    assert r.name == "hermes"
    assert Capability.SESSIONS.value in r.capabilities


def test_detect_counts_sessions(hermes_home, hermes_db):
    _insert_session(hermes_db, id="s1")
    _insert_session(hermes_db, id="s2")
    hermes_db.commit()
    hermes_db.close()
    r = HermesAdapter().detect()
    assert r.detected is True
    assert r.session_count == 2
    assert r.workspace == str(hermes_home)


def test_detect_running_false_without_gateway_pid(hermes_home, hermes_db):
    _insert_session(hermes_db)
    hermes_db.commit()
    hermes_db.close()
    assert HermesAdapter().running() is False


def test_detect_running_true_with_live_pid(hermes_home, hermes_db, monkeypatch):
    _insert_session(hermes_db)
    hermes_db.commit()
    hermes_db.close()
    (hermes_home / "gateway.pid").write_text(f"{os.getpid()}\n")
    assert HermesAdapter().running() is True


def test_detect_running_false_with_dead_pid(hermes_home):
    # PID 2**20 is effectively never in use.
    (hermes_home / "gateway.pid").write_text("1048576\n")
    assert HermesAdapter().running() is False


def test_list_sessions_maps_schema(hermes_home, hermes_db):
    _insert_session(
        hermes_db,
        id="abc",
        model="gpt-5.4",
        source="telegram",
        started_at=1000.0,
        input_tokens=100,
        output_tokens=50,
        cache_read_tokens=25,
        cache_write_tokens=5,
        estimated_cost_usd=0.05,
        actual_cost_usd=0.04,
        cost_status="actual",
        title="greetings",
    )
    hermes_db.commit()
    hermes_db.close()
    [s] = HermesAdapter().list_sessions()
    assert isinstance(s, Session)
    assert s.agent == "hermes"
    assert s.id == "abc"
    assert s.model == "gpt-5.4"
    assert s.source == "telegram"
    assert s.started_at == 1000.0
    assert s.input_tokens == 100
    assert s.output_tokens == 50
    assert s.total_tokens == 150
    assert s.cache_read_tokens == 25
    assert s.cache_write_tokens == 5
    # actual preferred over estimated
    assert s.cost_usd == 0.04
    assert s.cost_status == "actual"
    assert s.title == "greetings"
    assert s.display_name == "greetings"


def test_list_sessions_falls_back_to_estimated_cost(hermes_home, hermes_db):
    _insert_session(
        hermes_db, estimated_cost_usd=0.10, actual_cost_usd=None, cost_status="estimated"
    )
    hermes_db.commit()
    hermes_db.close()
    [s] = HermesAdapter().list_sessions()
    assert s.cost_usd == 0.10


def test_list_sessions_ordered_newest_first(hermes_home, hermes_db):
    _insert_session(hermes_db, id="old", started_at=100.0)
    _insert_session(hermes_db, id="new", started_at=200.0)
    _insert_session(hermes_db, id="mid", started_at=150.0)
    hermes_db.commit()
    hermes_db.close()
    ids = [s.id for s in HermesAdapter().list_sessions()]
    assert ids == ["new", "mid", "old"]


def test_list_sessions_exposes_parent_link(hermes_home, hermes_db):
    _insert_session(hermes_db, id="root")
    _insert_session(hermes_db, id="child", parent_session_id="root", started_at=200.0)
    hermes_db.commit()
    hermes_db.close()
    sessions = {s.id: s for s in HermesAdapter().list_sessions()}
    assert sessions["child"].parent_id == "root"
    assert sessions["root"].parent_id is None


def test_read_session_returns_none_for_unknown(hermes_home, hermes_db):
    _insert_session(hermes_db)
    hermes_db.commit()
    hermes_db.close()
    assert HermesAdapter().read_session("nope") is None


def test_list_events_maps_message_rows(hermes_home, hermes_db):
    _insert_session(hermes_db)
    _insert_message(hermes_db, role="user", content="hello", timestamp=1.0)
    _insert_message(
        hermes_db,
        role="assistant",
        content="hi",
        timestamp=2.0,
        token_count=12,
        finish_reason="stop",
    )
    hermes_db.commit()
    hermes_db.close()
    events = HermesAdapter().list_events("s1")
    assert len(events) == 2
    assert all(isinstance(e, Event) for e in events)
    assert events[0].role == "user"
    assert events[0].content == "hello"
    assert events[0].type == "message"
    assert events[1].role == "assistant"
    assert events[1].tokens == 12
    assert events[1].extra["finishReason"] == "stop"


def test_list_events_decodes_tool_calls(hermes_home, hermes_db):
    import json as _json

    _insert_session(hermes_db)
    tool_calls_json = _json.dumps(
        [{"id": "call_1", "function": {"name": "grep", "arguments": "{}"}}]
    )
    _insert_message(
        hermes_db,
        role="assistant",
        content="",
        tool_calls=tool_calls_json,
        tool_name="grep",
    )
    hermes_db.commit()
    hermes_db.close()
    [e] = HermesAdapter().list_events("s1")
    assert e.type == "tool_call"
    assert e.tool_name == "grep"
    assert len(e.tool_calls) == 1
    assert e.tool_calls[0]["id"] == "call_1"


def test_list_events_skips_unknown_session(hermes_home, hermes_db):
    _insert_session(hermes_db)
    hermes_db.commit()
    hermes_db.close()
    assert HermesAdapter().list_events("unknown") == []


def test_capabilities_subset_for_v1():
    caps = HermesAdapter().capabilities()
    # V1 deliberately narrow — widens in later PRs when each panel is
    # wired end-to-end. Assert the ones we DO ship, and confirm we
    # don't accidentally advertise BRAIN/CRONS (which aren't implemented).
    assert Capability.SESSIONS in caps
    assert Capability.EVENTS in caps
    assert Capability.COST in caps
    assert Capability.SUBAGENTS in caps
    assert Capability.BRAIN not in caps
    assert Capability.CRONS not in caps
    assert Capability.GATEWAY_RPC not in caps


def test_stream_events_yields_new_rows(hermes_home, hermes_db):
    _insert_session(hermes_db)
    _insert_message(hermes_db, content="existing", timestamp=1.0)
    hermes_db.commit()
    hermes_db.close()

    adapter = HermesAdapter()
    # Poll faster in tests so the loop iterates quickly.
    adapter._poll_interval = 0.05

    seen: list[Event] = []
    stop_err: list[BaseException] = []

    def consume():
        try:
            for ev in adapter.stream_events():
                seen.append(ev)
                if len(seen) >= 2:
                    adapter.stop_stream()
                    break
        except BaseException as exc:  # pragma: no cover — surfaced to main thread
            stop_err.append(exc)

    t = threading.Thread(target=consume, daemon=True)
    t.start()

    # Give the stream a poll cycle to initialise last_id past the
    # pre-existing row, then insert two new rows.
    time.sleep(0.15)
    conn = sqlite3.connect(str(hermes_home / "state.db"))
    _insert_message(conn, content="new-1", timestamp=10.0)
    _insert_message(conn, content="new-2", timestamp=11.0)
    conn.commit()
    conn.close()

    t.join(timeout=3.0)
    adapter.stop_stream()
    assert not stop_err, stop_err
    contents = sorted(e.content for e in seen)
    assert contents == ["new-1", "new-2"]
