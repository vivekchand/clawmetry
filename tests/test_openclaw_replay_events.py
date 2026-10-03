"""Replay-event mapper for OpenClaw (#4816, schema #4813).

Covers ``OpenClawAdapter.iter_replay_events`` over the shipped v3 fixture
and a transcript in the live 2026.9.x shape (millisecond timestamps,
string user content, ``__openclaw`` metadata), the state-database joins
(``exec_approvals_config`` -> ``mode.changed``, ``operator_approvals`` ->
``approval.*``, ``subagent_runs`` -> ``agent.spawn``) against the real
table shapes, the daemon hook ``sync._ingest_openclaw_replay_events`` and
the replay-tree endpoint reading the written rows. The transcript
``parentId`` is a chain, so no event carries a ``parent_span_id``.
"""
from __future__ import annotations

import json
import os
import shutil
import sqlite3
from pathlib import Path

import pytest

from clawmetry.adapters.openclaw import OpenClawAdapter
from clawmetry.adapters import openclaw_replay as ocr
from clawmetry.replay_schema import validate

_FIXTURE = os.path.join(os.path.dirname(__file__), "fixtures", "openclaw",
                        "v3-session.jsonl")
SID = "b4641cf9-700d-4af6-886f-9e0cd5519224"
KEY = "agent:main:main"
CHILD_SID = "11111111-2222-4333-8444-555555555555"
CHILD_KEY = "agent:main:subagent:child-1"

# Table shapes as OpenClaw 2026.9.3 creates them (STRICT dropped so the
# oldest SQLite CI runs on still accepts the DDL; column set is identical).
_STATE_SCHEMA = """
CREATE TABLE exec_approvals_config (
  config_key TEXT NOT NULL PRIMARY KEY, raw_json TEXT NOT NULL,
  socket_path TEXT, has_socket_token INTEGER NOT NULL,
  default_security TEXT, default_ask TEXT, default_ask_fallback TEXT,
  auto_allow_skills INTEGER, agent_count INTEGER NOT NULL,
  allowlist_count INTEGER NOT NULL, updated_at_ms INTEGER NOT NULL);
CREATE TABLE operator_approvals (
  approval_id TEXT NOT NULL PRIMARY KEY, resolution_ref TEXT, kind TEXT,
  status TEXT, presentation_json TEXT, requested_by_device_id TEXT,
  requested_by_client_id TEXT, requested_by_device_token_auth INTEGER,
  reviewer_device_ids_json TEXT, source_agent_id TEXT,
  source_session_key TEXT, source_session_id TEXT, source_run_id TEXT,
  source_tool_call_id TEXT, source_tool_name TEXT,
  audience_session_keys_json TEXT, runtime_epoch INTEGER,
  created_at_ms INTEGER, expires_at_ms INTEGER, updated_at_ms INTEGER,
  decision TEXT, terminal_reason TEXT, resolved_at_ms INTEGER,
  resolver_kind TEXT, resolver_id TEXT, consumed_at_ms INTEGER,
  consumed_by TEXT);
CREATE TABLE subagent_runs (
  run_id TEXT NOT NULL PRIMARY KEY, child_session_key TEXT NOT NULL,
  controller_session_key TEXT, requester_session_key TEXT NOT NULL,
  created_at INTEGER NOT NULL, payload_json TEXT NOT NULL DEFAULT '{}');
"""

T0 = 1_759_400_000_000  # unix milliseconds


def _rec(rid, parent, ts_ms, rtype, **extra):
    base = {"type": rtype, "id": rid, "parentId": parent, "timestamp": ts_ms}
    base.update(extra)
    return json.dumps(base)


def _live_transcript() -> str:
    """A 2026.9.x transcript: ms timestamps, string user content, a tool
    round trip inside messages, a thinking block and a compaction."""
    return "\n".join([
        json.dumps({"type": "session", "version": 3, "id": SID,
                    "timestamp": T0, "cwd": "/Users/demo/project"}),
        _rec("u1", None, T0 + 1_000, "message", message={
            "role": "user", "content": "List the repo.", "timestamp": T0 + 1_000,
            "idempotencyKey": "k1", "__openclaw": {"channel": "telegram"}}),
        _rec("a1", "u1", T0 + 4_000, "message", message={
            "role": "assistant", "api": "anthropic-messages",
            "provider": "anthropic", "model": "claude-opus-4-7",
            "stopReason": "toolUse", "timestamp": T0 + 4_000,
            "content": [
                {"type": "thinking", "thinking": "I should look first."},
                {"type": "text", "text": "Looking."},
                {"type": "tool_use", "id": "toolu_1", "name": "exec",
                 "input": {"command": "ls"}},
            ],
            "usage": {"input": 2, "output": 9, "cacheRead": 48_590,
                      "cacheWrite": 172, "totalTokens": 48_773, "cost": 0.0}}),
        _rec("r1", "a1", T0 + 5_000, "message", message={
            "role": "user", "timestamp": T0 + 5_000,
            "content": [{"type": "tool_result", "tool_use_id": "toolu_1",
                         "is_error": False,
                         "content": [{"type": "text", "text": "README.md"}]}]}),
        _rec("c1", "r1", T0 + 5_500, "compaction", tokensBefore=50_000,
             tokensAfter=12_000),
        _rec("a2", "c1", T0 + 7_000, "message", message={
            "role": "assistant", "provider": "anthropic",
            "model": "claude-opus-4-7", "stopReason": "end_turn",
            "timestamp": T0 + 7_000,
            "content": [{"type": "text", "text": "One file: README.md."}],
            "usage": {"input": 3, "output": 7, "cacheRead": 12_000,
                      "cacheWrite": 0, "totalTokens": 12_010, "cost": 0.0}}),
        "not json at all",
        "",
    ]) + "\n"


@pytest.fixture
def sessions_dir(tmp_path) -> str:
    d = tmp_path / "sessions"
    d.mkdir()
    (d / ("%s.jsonl" % SID)).write_text(_live_transcript())
    shutil.copy(_FIXTURE, str(d / "fixture-v3.jsonl"))
    (d / "sessions.json").write_text(json.dumps({
        KEY: {"sessionId": SID, "sessionFile": "%s.jsonl" % SID,
              "updatedAt": T0 + 7_000},
        CHILD_KEY: {"sessionId": CHILD_SID, "updatedAt": T0 + 3_000},
        "agent:main:cron:job-9": {"sessionId": "fixture-v3"},
        "broken": "not an entry",
    }))
    return str(d)


def _state_db(path: Path, *, security="allowlist", ask="on-miss",
              approvals=(), spawns=()) -> str:
    conn = sqlite3.connect(str(path))
    conn.executescript(_STATE_SCHEMA)
    conn.execute(
        "INSERT INTO exec_approvals_config VALUES ('current', '{}', NULL, 0, "
        "?, ?, 'deny', 1, 1, 0, ?)", (security, ask, T0))
    for row in approvals:
        conn.execute(
            "INSERT INTO operator_approvals (approval_id, kind, status, "
            "source_session_key, source_session_id, source_tool_call_id, "
            "source_tool_name, created_at_ms, resolved_at_ms, updated_at_ms, "
            "decision, terminal_reason, resolver_kind, presentation_json) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", row)
    for row in spawns:
        conn.execute("INSERT INTO subagent_runs VALUES (?, ?, ?, ?, ?, ?)", row)
    conn.commit()
    conn.close()
    return str(path)


@pytest.fixture
def state_db(tmp_path) -> str:
    return _state_db(
        tmp_path / "openclaw.sqlite",
        approvals=[
            # The real 2026.9.3 row shape: exec denied by the system because
            # no reviewer device could be reached (keyed on session key).
            ("apr-1", "exec", "denied", KEY, None, "toolu_1", "exec",
             T0 + 4_100, T0 + 4_200, T0 + 4_200, "deny", "no-route",
             "system", '{"secret": "never-read"}'),
            # An operator approving, keyed on session id.
            ("apr-2", "exec", "resolved", None, SID, "toolu_2", "exec",
             T0 + 6_000, T0 + 6_500, T0 + 6_500, "approve", None,
             "operator", "{}"),
            # Still pending: only approval.requested.
            ("apr-3", "exec", "pending", KEY, None, "toolu_3", "exec",
             T0 + 6_800, None, T0 + 6_800, None, None, None, "{}"),
            # Another session's approval: never ours.
            ("apr-9", "exec", "denied", "agent:main:other", "other-sid",
             "toolu_9", "exec", T0 + 100, T0 + 200, T0 + 200, "deny", "x",
             "system", "{}"),
        ],
        spawns=[
            ("run-1", CHILD_KEY, KEY, KEY, T0 + 2_000,
             json.dumps({"task": "Scan the tree", "model": "claude-haiku-4-5",
                         "spawn_mode": "background", "nested": {"x": 1}})),
            ("run-9", "agent:main:elsewhere", None, "agent:main:other",
             T0 + 2_500, "{}"),
        ],
    )


@pytest.fixture
def adapter(sessions_dir, state_db) -> OpenClawAdapter:
    return OpenClawAdapter(sessions_dir=sessions_dir, state_db=state_db)


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


# -- shipped v3 fixture (ISO timestamps, top-level tool_use_result) -----------


def test_fixture_maps_to_valid_unique_events_without_a_state_db(sessions_dir, tmp_path):
    a = OpenClawAdapter(sessions_dir=sessions_dir,
                        state_db=str(tmp_path / "missing.sqlite"))
    events = list(a.iter_replay_events("fixture-v3"))
    assert [validate(e) for e in events] == [[]] * len(events)
    assert len({e["span_id"] for e in events}) == len(events)
    assert [e["kind"] for e in events] == [
        "mode.changed", "llm.call", "llm.response", "tool.call",
        "tool.result", "llm.response"]
    assert events[0]["mode"] == {"permission": "unknown", "collaboration": "cron"}
    assert events[0]["payload"]["source"] is None
    assert events[0]["payload"]["cwd"] == "/Users/test/.openclaw/workspace"
    assert events[0]["payload"]["version"] == "3"
    assert events[3]["payload"] == {
        "tool_use_id": "toolu_01moat", "name": "bash",
        "input": {"command": "echo moat"}}
    assert events[4]["span_id"] == "openclaw:fixture-v3:result:toolu_01moat"
    assert events[4]["payload"]["is_error"] is False
    assert events[4]["payload"]["content_types"] == ["text"]
    assert all(e["parent_span_id"] is None for e in events)
    assert all(e["runtime"] == "openclaw" for e in events)
    assert all(e["session_id"] == "fixture-v3" for e in events)
    # ISO timestamps become unix seconds and never go backwards.
    ts = [e["ts"] for e in events]
    assert ts == sorted(ts) and ts[0] > 1_600_000_000


# -- live 2026.9.x transcript shape -------------------------------------------


def test_live_shape_turns_tools_thinking_and_compaction(adapter):
    events = list(adapter.iter_replay_events(SID))
    assert [validate(e) for e in events] == [[]] * len(events)
    assert len({e["span_id"] for e in events}) == len(events)
    kinds = [e["kind"] for e in events]
    assert kinds == [
        "mode.changed",
        "llm.call",                                   # u1 (+1s)
        "agent.spawn",                                # run-1 (+2s)
        "thinking", "llm.response", "tool.call",      # a1 (+4s)
        "approval.requested", "approval.decided",     # apr-1 (+4.1s, +4.2s)
        "tool.result",                                # r1 (+5s)
        "compaction",                                 # c1 (+5.5s)
        "approval.requested", "approval.decided",     # apr-2 (+6s, +6.5s)
        "approval.requested",                         # apr-3 pending (+6.8s)
        "llm.response",                               # a2 (+7s)
    ]
    by_kind = {}
    for e in events:
        by_kind.setdefault(e["kind"], []).append(e)
    call = by_kind["llm.call"][0]
    assert call["span_id"] == "openclaw:%s:call:u1" % SID
    assert call["payload"] == {"turn": 1, "text": "List the repo."}
    assert call["ts"] == (T0 + 1_000) / 1000.0
    think = by_kind["thinking"][0]
    assert think["payload"] == {"text": "I should look first."}
    resp = by_kind["llm.response"][0]
    assert resp["payload"]["text"] == "Looking."
    assert resp["payload"]["model"] == "claude-opus-4-7"
    assert resp["payload"]["stop_reason"] == "toolUse"
    assert resp["payload"]["tool_calls"] == 1
    assert resp["payload"]["api"] == "anthropic-messages"
    assert resp["payload"]["usage"] == {
        "input": 2, "output": 9, "cache_read": 48_590, "cache_write": 172,
        "total": 48_773, "cost_usd": 0.0}
    tool = by_kind["tool.call"][0]
    assert tool["span_id"] == "openclaw:%s:tool:toolu_1" % SID
    assert tool["payload"] == {"tool_use_id": "toolu_1", "name": "exec",
                               "input": {"command": "ls"}}
    result = by_kind["tool.result"][0]
    assert result["span_id"] == "openclaw:%s:result:toolu_1" % SID
    assert result["payload"] == {"tool_use_id": "toolu_1", "is_error": False,
                                 "output": "README.md", "content_types": ["text"]}
    assert by_kind["compaction"][0]["payload"] == {
        "tokens_before": 50_000, "tokens_after": 12_000}
    # The user turn carrying only a tool_result is not a prompt.
    assert len(by_kind["llm.call"]) == 1
    # parentId is a chain, never a delegation edge. The only parent is an
    # approval's gate: the tool.call it decided (apr-1 -> toolu_1); an
    # approval for a call the transcript does not show stays unattached.
    gated = [e for e in events if e["parent_span_id"] is not None]
    assert [e["span_id"].rsplit(":", 2)[1] for e in gated] == ["apr-1", "apr-1"]
    assert {e["parent_span_id"] for e in gated} == {"openclaw:%s:tool:toolu_1" % SID}
    # No event besides mode.changed carries a mode; only approval.* carry one.
    assert all(e.get("mode") is None for e in events[1:])
    assert all((e.get("approval") is not None) == e["kind"].startswith("approval.")
               for e in events)


# -- mode chip from exec_approvals_config -------------------------------------


def test_mode_chip_from_exec_approvals_config(adapter):
    first = next(adapter.iter_replay_events(SID))
    assert first["kind"] == "mode.changed"
    assert first["span_id"] == "openclaw:%s:mode" % SID
    assert first["ts"] == T0 / 1000.0
    assert first["mode"] == {"permission": "default", "collaboration": "direct"}
    assert first["payload"] == {
        "source": "exec_approvals_config", "session_key": KEY,
        "security": "allowlist", "ask": "on-miss", "ask_fallback": "deny",
        "auto_allow_skills": True, "agent_overrides": 1, "allowlist_entries": 0,
        "cwd": "/Users/demo/project", "version": "3"}


def test_full_security_that_never_asks_is_yolo(sessions_dir, tmp_path):
    db = _state_db(tmp_path / "yolo.sqlite", security="full", ask="never")
    first = next(OpenClawAdapter(sessions_dir=sessions_dir, state_db=db)
                 .iter_replay_events(SID))
    assert first["mode"]["permission"] == "yolo"


@pytest.mark.parametrize("row,expected", [
    (None, "unknown"),
    ({"default_security": "full", "default_ask": "never"}, "yolo"),
    ({"default_security": "full", "default_ask": "always"}, "default"),
    ({"default_security": "allowlist", "default_ask": "never"}, "default"),
    ({"default_security": "deny", "default_ask": "on-miss"}, "default"),
    ({"default_security": None, "default_ask": None}, "unknown"),
])
def test_permission_mapping(row, expected):
    assert ocr.permission_from_exec(row) == expected


def test_collaboration_from_session_key():
    assert ocr._collaboration("agent:main:main") == "direct"
    assert ocr._collaboration("agent:main:cron:job-1") == "cron"
    assert ocr._collaboration(
        "agent:main:cm-investigation-2b8d07bf-10de-4f45-b13b-ae90b80749ad"
    ) == "cm-investigation"
    assert ocr._collaboration("agent:main") is None
    assert ocr._collaboration(None) is None


# -- approvals from operator_approvals ----------------------------------------


def test_approvals_join_on_key_or_id_and_skip_other_sessions(adapter):
    events = [e for e in adapter.iter_replay_events(SID)
              if e["kind"].startswith("approval.")]
    ids = [e["span_id"].rsplit(":", 2)[1] for e in events]
    assert ids == ["apr-1", "apr-1", "apr-2", "apr-2", "apr-3"]
    denied_req, denied, approved_req, approved, pending = events
    assert denied_req["approval"] == {
        "status": "requested", "decision_reason": None, "resolver": None,
        "edit_diff": None}
    assert denied_req["payload"] == {
        "approval_id": "apr-1", "kind": "exec", "tool_name": "exec",
        "tool_call_id": "toolu_1", "source": "operator_approvals"}
    assert denied["approval"] == {
        "status": "denied", "decision_reason": "no-route",
        "resolver": "policy", "edit_diff": None}
    assert denied["ts"] == (T0 + 4_200) / 1000.0
    assert approved["approval"]["status"] == "approved"
    assert approved["approval"]["resolver"] == "user"
    assert approved["approval"]["decision_reason"] is None
    assert pending["kind"] == "approval.requested"
    # presentation_json is never read into a payload.
    assert "secret" not in json.dumps(events)


@pytest.mark.parametrize("row,expected", [
    ({"decision": "deny"}, "denied"),
    ({"decision": "approve"}, "approved"),
    ({"status": "approved"}, "approved"),
    ({"status": "expired"}, "timeout"),
    ({"terminal_reason": "timeout"}, "timeout"),
    ({"status": "pending"}, None),
    ({}, None),
])
def test_approval_status_mapping(row, expected):
    assert ocr._approval_status(row) == expected


def test_resolver_mapping():
    assert ocr._resolver("system") == "policy"
    assert ocr._resolver("operator") == "user"
    assert ocr._resolver("device") == "user"
    assert ocr._resolver("hook") == "hook"
    assert ocr._resolver(None) == "unknown"
    assert ocr._resolver("something-new") == "unknown"


# -- sub-agent spawns from subagent_runs --------------------------------------


def test_subagent_run_becomes_agent_spawn_with_child_session_id(adapter):
    spawns = [e for e in adapter.iter_replay_events(SID) if e["kind"] == "agent.spawn"]
    assert len(spawns) == 1
    sp = spawns[0]
    assert sp["span_id"] == "openclaw:%s:spawn:run-1" % SID
    assert sp["ts"] == (T0 + 2_000) / 1000.0
    assert sp["parent_span_id"] is None  # the child lives in its own session
    assert sp["payload"] == {
        "run_id": "run-1", "child_session_key": CHILD_KEY,
        "child_session_id": CHILD_SID, "controller_session_key": KEY,
        "requester_session_key": KEY, "source": "subagent_runs",
        "task": "Scan the tree", "model": "claude-haiku-4-5",
        "spawn_mode": "background"}


# -- robustness ---------------------------------------------------------------


def test_unknown_session_bad_ids_and_limit(adapter):
    assert list(adapter.iter_replay_events("does-not-exist")) == []
    assert list(adapter.iter_replay_events("")) == []
    assert list(adapter.iter_replay_events("../sessions.json")) == []
    assert list(adapter.iter_replay_events(SID, limit=0)) == []
    assert len(list(adapter.iter_replay_events(SID, limit=3))) == 3
    assert len(list(adapter.iter_replay_events(SID, limit="x"))) == 14


def test_garbage_transcript_and_corrupt_state_db_yield_a_mode_only(tmp_path):
    d = tmp_path / "s"
    d.mkdir()
    (d / "junk.jsonl").write_text("{not json\n[]\n42\n")
    (d / "sessions.json").write_text("{broken")
    bad_db = tmp_path / "bad.sqlite"
    bad_db.write_bytes(b"not a database")
    a = OpenClawAdapter(sessions_dir=str(d), state_db=str(bad_db))
    events = list(a.iter_replay_events("junk"))
    assert [e["kind"] for e in events] == ["mode.changed"]
    assert events[0]["mode"] == {"permission": "unknown"}
    assert validate(events[0]) == []


def test_state_db_without_the_tables_only_drops_the_enrichment(sessions_dir, tmp_path):
    db = tmp_path / "old.sqlite"
    sqlite3.connect(str(db)).execute("CREATE TABLE schema_meta (k TEXT)").connection.commit()
    events = list(OpenClawAdapter(sessions_dir=sessions_dir, state_db=str(db))
                  .iter_replay_events(SID))
    kinds = [e["kind"] for e in events]
    assert "approval.requested" not in kinds and "agent.spawn" not in kinds
    assert kinds[:2] == ["mode.changed", "llm.call"]
    assert events[0]["mode"] == {"permission": "unknown", "collaboration": "direct"}


def test_timestamp_parsing():
    assert ocr._ts(1_759_400_000_000) == 1_759_400_000.0
    assert ocr._ts(1_759_400_000) == 1_759_400_000.0
    assert ocr._ts("1759400000000") == 1_759_400_000.0
    assert ocr._ts("2026-10-02T10:13:20.000Z") == 1_790_936_000.0
    assert ocr._ts("2026-10-02T10:13:20+00:00") == 1_790_936_000.0
    assert ocr._ts("2026-10-02T10:13:20") == 1_790_936_000.0
    assert ocr._ts("yesterday", 7.0) == 7.0
    assert ocr._ts(None, 3.0) == 3.0
    assert ocr._ts(True, 2.0) == 2.0
    assert ocr._ts(-5, 1.0) == 1.0


def test_state_db_is_opened_read_only(adapter, state_db):
    before = Path(state_db).read_bytes()
    list(adapter.iter_replay_events(SID))
    assert Path(state_db).read_bytes() == before
    conn = ocr._connect_ro(state_db)
    with pytest.raises(sqlite3.OperationalError):
        conn.execute("INSERT INTO subagent_runs VALUES ('w', 'a', NULL, 'b', 1, '{}')")
    conn.close()


def test_default_sources_resolve_through_sync(monkeypatch, sessions_dir, state_db):
    from clawmetry import sync

    monkeypatch.setattr(sync, "_openclaw_sessions_dir", lambda *a, **kw: sessions_dir)
    monkeypatch.setenv("CLAWMETRY_OPENCLAW_DIR", os.path.dirname(state_db))
    monkeypatch.setattr(ocr, "default_state_db",
                        lambda: state_db)
    events = list(OpenClawAdapter().iter_replay_events(SID))
    assert len(events) == 14
    assert events[0]["mode"]["permission"] == "default"


# -- store + daemon hook ------------------------------------------------------


def test_store_upsert_is_idempotent(store, adapter):
    rows = list(adapter.iter_replay_events(SID))
    assert store.ingest_replay_events(rows) == 14
    assert store.ingest_replay_events(rows) == 14
    got = store.query_replay_events(session_id=SID)
    assert len(got) == 14
    assert got[0]["kind"] == "mode.changed"
    assert got[0]["mode"] == {"permission": "default", "collaboration": "direct"}
    decided = [g for g in got if g["kind"] == "approval.decided"]
    assert decided[0]["approval"]["status"] == "denied"


def test_sync_hook_writes_rows_under_the_bare_session_id(store, monkeypatch, sessions_dir, state_db):
    from clawmetry import sync

    monkeypatch.setattr(sync, "_openclaw_sessions_dir", lambda *a, **kw: sessions_dir)
    monkeypatch.setattr(ocr, "default_state_db", lambda: state_db)
    assert sync._ingest_openclaw_replay_events(store, SID) == 14
    rows = store.query_replay_events(session_id=SID)
    assert len(rows) == 14
    assert rows[0]["span_id"] == "openclaw:%s:mode" % SID
    # Family-style ids and unknown sessions are not ours.
    assert sync._ingest_openclaw_replay_events(store, "qwen_code:abc") == 0
    assert sync._ingest_openclaw_replay_events(store, "nope") == 0
    assert sync._ingest_openclaw_replay_events(store, "") == 0


def test_sync_hook_is_best_effort(store, monkeypatch):
    from clawmetry import sync

    class Raising:
        def iter_replay_events(self, session_id, limit=5000):
            raise RuntimeError("boom")

    monkeypatch.setattr("clawmetry.adapters.openclaw.OpenClawAdapter", Raising)
    assert sync._ingest_openclaw_replay_events(store, SID) == 0

    class Lazy:
        def iter_replay_events(self, session_id, limit=5000):
            yield {"kind": "llm.call", "span_id": "openclaw:x:1",
                   "session_id": session_id, "runtime": "openclaw", "ts": 1.0,
                   "payload": {}}
            raise RuntimeError("late")

    monkeypatch.setattr("clawmetry.adapters.openclaw.OpenClawAdapter", Lazy)
    assert sync._ingest_openclaw_replay_events(store, SID) == 0
    assert store.query_replay_events(session_id=SID) == []


def test_batch_ingest_calls_the_hook_for_openclaw_only(store, monkeypatch):
    from clawmetry import sync
    from clawmetry import local_store as ls

    monkeypatch.setattr(ls, "get_store", lambda read_only=False: store)
    calls = []
    monkeypatch.setattr(sync, "_ingest_openclaw_replay_events",
                        lambda st, sid, limit=5000: calls.append(sid) or 1)
    batch = [json.loads(l) for l in Path(_FIXTURE).read_text().splitlines() if l.strip()]
    sync._local_ingest_session_batch(batch, "fixture-v3.jsonl", "node-1", None)
    sync._local_ingest_session_batch(batch, "fixture-v3.jsonl", "node-1", "sub-key")
    sync._local_ingest_session_batch(batch, "fixture-v3.jsonl", "node-1", None,
                                     agent_type="nemoclaw")
    assert calls == ["fixture-v3"]


def test_replay_tree_endpoint_serves_the_written_rows(store, adapter, monkeypatch):
    from flask import Flask
    from routes.sessions import bp_sessions
    from clawmetry import local_store as ls

    monkeypatch.setattr(
        "routes.local_query.local_store_via_daemon", lambda *a, **kw: None)
    monkeypatch.setattr(ls, "get_store", lambda read_only=False: store)
    store.ingest_replay_events(list(adapter.iter_replay_events(SID)))

    app = Flask(__name__)
    app.register_blueprint(bp_sessions)
    body = app.test_client().get("/api/replay-tree/%s" % SID).get_json()
    assert body["runtime"] == "openclaw"
    assert body["mode"] == {"permission": "default", "collaboration": "direct"}
    assert body["row_count"] == 14
    assert len(body["turns"]) == 1
    turn = body["turns"][0]
    assert turn["turn_id"] == "openclaw:%s:call:u1" % SID
    # apr-1 hangs on the tool.call it decided; apr-2 / apr-3 name calls the
    # transcript never showed, so they are counted but not placed on a turn.
    assert [a["span_id"].rsplit(":", 2)[1] for a in turn["approvals"]] == ["apr-1", "apr-1"]
    assert len(turn["delegations"]) == 1
    assert turn["delegations"][0]["span_id"] == "openclaw:%s:spawn:run-1" % SID
    assert body["workflows"] == []
