"""Replay-event mapper for Goose (#4813, clawmetry-pro#134).

Covers ``GooseAdapter.iter_replay_events`` over the committed fixture
database and over purpose-built ones: a cron-started session that ran a
recipe (mode chip "cron", one workflow group with the recipe steps), an
interactive session without a recipe (flat replay, no workflow group),
recipe shapes from different Goose versions, an older database without
the mode and schedule columns, and the daemon hook writing the rows the
replay-tree endpoint reads. Goose has no sub-agents, so no event carries
``parent_span_id``.
"""
from __future__ import annotations

import json
import os
import sqlite3
from pathlib import Path

import pytest

from clawmetry.adapters.goose import GooseAdapter
from clawmetry.adapters.goose_replay import recipe_payload
from clawmetry.replay_schema import validate

_FIXTURE_DB = os.path.join(
    os.path.dirname(__file__), "fixtures", "runtimes", "goose", "sessions",
    "sessions.db",
)

_SESSION_COLS = (
    "id TEXT PRIMARY KEY, name TEXT, session_type TEXT, working_dir TEXT, "
    "created_at TEXT, provider_name TEXT, model_config_json TEXT"
)
_MODERN_COLS = _SESSION_COLS + (
    ", goose_mode TEXT, schedule_id TEXT, recipe_json TEXT, "
    "user_recipe_values_json TEXT"
)

_RECIPE = {
    "version": "1.0.0",
    "title": "Nightly dependency report",
    "description": "List outdated packages.",
    "instructions": "Check every lock file.",
    "prompt": "Report outdated dependencies.",
    "activities": ["Scan lock files", "Write the summary"],
    "extensions": [{"type": "builtin", "name": "developer"}],
    "parameters": [{"key": "repo", "input_type": "string"}],
    "sub_recipes": [{"name": "audit", "path": "./audit.yaml"}],
}


def _text(text):
    return json.dumps([{"type": "text", "text": text}])


def _make_db(tmp_path, cols, session, messages, jobs=None):
    """A Goose data dir with one session. Returns the sessions.db path."""
    sess_dir = tmp_path / "goose" / "sessions"
    sess_dir.mkdir(parents=True)
    db = str(sess_dir / "sessions.db")
    conn = sqlite3.connect(db)
    conn.execute(f"CREATE TABLE sessions ({cols})")
    conn.execute(
        "CREATE TABLE messages (id INTEGER PRIMARY KEY AUTOINCREMENT, "
        "message_id TEXT, session_id TEXT, role TEXT, content_json TEXT, "
        "created_timestamp INTEGER, tokens INTEGER)")
    names = [c.split()[0] for c in cols.split(", ")]
    conn.execute(
        f"INSERT INTO sessions ({','.join(names)}) "
        f"VALUES ({','.join('?' * len(names))})",
        [session.get(n) for n in names])
    for role, content, ts, tokens in messages:
        conn.execute(
            "INSERT INTO messages (session_id, role, content_json, "
            "created_timestamp, tokens) VALUES (?,?,?,?,?)",
            (session["id"], role, content, ts, tokens))
    conn.commit()
    conn.close()
    if jobs is not None:
        (tmp_path / "goose" / "schedule.json").write_text(json.dumps(jobs))
    return db


@pytest.fixture
def adapter() -> GooseAdapter:
    return GooseAdapter(db_path=_FIXTURE_DB)


@pytest.fixture
def cron_adapter(tmp_path) -> GooseAdapter:
    """A cron-started session that ran a recipe, with one tool round."""
    db = _make_db(
        tmp_path, _MODERN_COLS,
        {"id": "cron-1", "name": "Nightly", "session_type": "scheduled",
         "working_dir": "/tmp/demo", "created_at": "2026-05-25 19:51:40",
         "provider_name": "anthropic",
         "model_config_json": json.dumps({"model_name": "claude-haiku-4-5"}),
         "goose_mode": "approve", "schedule_id": "nightly-deps",
         "recipe_json": json.dumps(_RECIPE),
         "user_recipe_values_json": json.dumps({"repo": "secret-repo-name"})},
        [
            ("user", _text("Report outdated dependencies."), 1779738706, None),
            ("assistant", json.dumps([
                {"type": "thinking", "thinking": "Read the lock file first.",
                 "signature": "sig"},
                {"type": "text", "text": "Checking."},
                {"type": "toolRequest", "id": "call_1",
                 "toolCall": {"status": "success", "value": {
                     "name": "shell", "arguments": {"command": "pip list -o"}}},
                 "_meta": {"goose_extension": "developer"}},
            ]), 1779738706, 42),
            ("user", json.dumps([
                {"type": "toolResponse", "id": "call_1",
                 "toolResult": {"status": "success", "value": {
                     "content": [{"type": "text", "text": "flask 2.0 -> 3.0"}],
                     "isError": False}}},
            ]), 1779738706, None),
            ("assistant", _text("One package is outdated."), 1779738706, None),
        ],
        jobs=[{"id": "nightly-deps", "cron": "0 0 2 * * *",
               "source": "/recipes/deps.yaml"}],
    )
    return GooseAdapter(db_path=db)


@pytest.fixture
def store(tmp_path, monkeypatch):
    from clawmetry import local_store as ls

    monkeypatch.setattr(ls, "DB_PATH", Path(str(tmp_path / "t.duckdb")))
    ls._reset_singleton_for_tests()
    s = ls.LocalStore(read_only=False)
    s.start()
    try:
        yield s
    finally:
        try:
            s.stop(flush=True)
        except Exception:
            pass
        ls._reset_singleton_for_tests()


# -- committed fixture: interactive sessions, no recipe ----------------------


def test_every_fixture_event_is_valid_and_unique(adapter):
    sessions = adapter.list_sessions()
    assert sessions
    for sess in sessions:
        events = list(adapter.iter_replay_events(sess.id))
        assert events
        assert [validate(e) for e in events] == [[]] * len(events)
        spans = [e["span_id"] for e in events]
        assert len(spans) == len(set(spans))
        assert all(s.startswith(f"goose:{sess.id}:") for s in spans)
        assert all(e["runtime"] == "goose" for e in events)


def test_interactive_session_is_a_flat_replay(adapter):
    events = list(adapter.iter_replay_events("20260525_3"))
    assert [e["kind"] for e in events] == [
        "mode.changed", "llm.call", "tool.call", "tool.result",
        "tool.call", "tool.result", "llm.response",
    ]
    # No recipe: no workflow group. No sub-agents: no delegation edge.
    assert not [e for e in events if e["kind"].startswith("workflow.")]
    assert all(e["parent_span_id"] is None for e in events)
    assert events[0]["mode"] == {"permission": "yolo"}
    assert events[0]["payload"]["goose_mode"] == "auto"
    assert "trigger" not in events[0]["payload"]


def test_tool_payloads(adapter):
    events = list(adapter.iter_replay_events("20260525_3"))
    call, result, _, failed = events[2:6]
    assert call["payload"] == {
        "tool": "shell", "call_id": "call_demo01",
        "args": {"command": "echo hello-from-goose"},
        "extension": "developer"}
    assert result["payload"]["call_id"] == "call_demo01"
    assert result["payload"]["output"] == "hello-from-goose\n"
    assert result["payload"]["is_error"] is False
    assert failed["payload"]["is_error"] is True
    assert events[-1]["payload"]["model"] == "llama3.2"
    assert "usage" not in events[-1]["payload"]


def test_unknown_session_missing_db_and_limit(adapter, tmp_path):
    assert list(adapter.iter_replay_events("no-such-session")) == []
    missing = GooseAdapter(db_path=str(tmp_path / "absent" / "sessions.db"))
    assert list(missing.iter_replay_events("20260525_3")) == []
    assert len(list(adapter.iter_replay_events("20260525_3", limit=3))) == 3
    assert list(adapter.iter_replay_events("20260525_3", limit=0)) == []


# -- cron-started session with a recipe --------------------------------------


def test_cron_session_reports_cron_mode_and_the_recipe(cron_adapter):
    events = list(cron_adapter.iter_replay_events("cron-1"))
    assert [validate(e) for e in events] == [[]] * len(events)
    assert [e["kind"] for e in events] == [
        "mode.changed", "workflow.start", "llm.call", "llm.response",
        "thinking", "tool.call", "tool.result", "llm.response",
    ]
    mode = events[0]
    assert mode["mode"] == {"permission": "default", "collaboration": "cron"}
    assert mode["payload"]["schedule_id"] == "nightly-deps"
    assert mode["payload"]["cron"] == "0 0 2 * * *"
    recipe = events[1]["payload"]
    assert recipe["title"] == "Nightly dependency report"
    assert recipe["steps"] == [
        {"kind": "instructions", "text": "Check every lock file."},
        {"kind": "prompt", "text": "Report outdated dependencies."},
        {"kind": "activity", "text": "Scan lock files"},
        {"kind": "activity", "text": "Write the summary"},
        {"kind": "sub_recipe", "name": "audit"},
    ]
    assert recipe["extensions"] == ["developer"]
    assert recipe["parameters"] == ["repo"]
    # The values a user typed for recipe parameters are never read.
    assert "secret-repo-name" not in json.dumps(events)
    assert events[3]["payload"]["usage"] == {"total_tokens": 42}


def test_same_second_rows_keep_transcript_order_in_the_store(cron_adapter):
    """Goose timestamps are whole seconds and the store orders by
    ``(ts, span_id)``, so span ids must sort in transcript order."""
    events = list(cron_adapter.iter_replay_events("cron-1"))
    assert len({e["ts"] for e in events[2:]}) == 1
    resorted = sorted(events, key=lambda e: (e["ts"], e["span_id"]))
    assert [e["span_id"] for e in resorted] == [e["span_id"] for e in events]


def test_cron_session_tree_has_one_workflow_and_one_turn(cron_adapter):
    from routes.sessions import _build_replay_tree

    tree = _build_replay_tree(
        "cron-1", list(cron_adapter.iter_replay_events("cron-1")))
    assert tree["mode"] == {"permission": "default", "collaboration": "cron"}
    assert len(tree["workflows"]) == 1
    assert tree["workflows"][0]["events"][0]["payload"]["steps"]
    assert len(tree["turns"]) == 1
    assert tree["turns"][0]["delegations"] == []


def test_interactive_session_tree_has_no_workflow(adapter):
    from routes.sessions import _build_replay_tree

    tree = _build_replay_tree(
        "20260525_3", list(adapter.iter_replay_events("20260525_3")))
    assert tree["workflows"] == []
    assert len(tree["turns"]) == 1


# -- version differences -----------------------------------------------------


def test_recipe_shapes_from_different_versions():
    assert recipe_payload(None) is None
    assert recipe_payload("") is None
    assert recipe_payload("not json") is None
    assert recipe_payload("[1, 2]") is None
    assert recipe_payload("{}") is None
    older = recipe_payload(json.dumps({"recipe": {
        "name": "Legacy", "instructions": "Do it.",
        "extensions": ["developer", "memory"],
        "parameters": {"repo": "string"},
        "activities": [{"text": "First"}, 7, ""],
    }}))
    assert older["title"] == "Legacy"
    assert older["steps"] == [
        {"kind": "instructions", "text": "Do it."},
        {"kind": "activity", "text": "First"},
    ]
    assert older["extensions"] == ["developer", "memory"]
    assert older["parameters"] == ["repo"]
    as_dict = recipe_payload({"title": "T", "activities": "not a list"})
    assert as_dict["steps"] == []


def test_older_database_without_mode_or_schedule_columns(tmp_path):
    db = _make_db(
        tmp_path, _SESSION_COLS,
        {"id": "old-1", "name": "Old", "session_type": "scheduled",
         "working_dir": "/tmp", "created_at": "2026-05-25 19:51:12"},
        [("user", _text("hello"), 1779738672, None),
         ("assistant", "plain string, not JSON", 1779738673, None)],
    )
    events = list(GooseAdapter(db_path=db).iter_replay_events("old-1"))
    assert [validate(e) for e in events] == [[]] * len(events)
    assert [e["kind"] for e in events] == [
        "mode.changed", "llm.call", "llm.response"]
    assert events[0]["mode"] == {
        "permission": "unknown", "collaboration": "cron"}
    assert events[0]["payload"]["goose_mode"] == ""


def test_unmapped_mode_is_unknown_with_the_native_value(tmp_path):
    db = _make_db(
        tmp_path, _MODERN_COLS,
        {"id": "chat-1", "session_type": "user", "working_dir": "/tmp",
         "created_at": "2026-05-25 19:51:12", "goose_mode": "chat"},
        [("user", _text("hello"), 1779738672, None)],
    )
    (mode, _call) = GooseAdapter(db_path=db).iter_replay_events("chat-1")
    assert mode["mode"] == {"permission": "unknown"}
    assert mode["payload"]["goose_mode"] == "chat"


# -- daemon hook + endpoint --------------------------------------------------


def test_sync_hook_writes_rows_the_endpoint_serves(store, cron_adapter,
                                                   monkeypatch):
    from clawmetry import sync

    n = sync._ingest_family_replay_events(
        store, cron_adapter, "cron-1", "goose:cron-1", "goose")
    assert n == 8
    # A second pass over the same transcript upserts, never duplicates.
    sync._ingest_family_replay_events(
        store, cron_adapter, "cron-1", "goose:cron-1", "goose")
    rows = store.query_replay_events(session_id="goose:cron-1")
    assert [r["kind"] for r in rows] == [
        "mode.changed", "workflow.start", "llm.call", "llm.response",
        "thinking", "tool.call", "tool.result", "llm.response",
    ]
    assert all(r["session_id"] == "goose:cron-1" for r in rows)
