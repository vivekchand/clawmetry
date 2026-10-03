"""Replay-event mapper for Qwen Code (#4813, clawmetry-pro#133).

Covers ``QwenCodeAdapter.iter_replay_events`` over the on-disk fixtures,
``LocalStore.ingest_replay_events``, the daemon hook
``sync._ingest_family_replay_events`` and the replay-tree endpoint reading
the written rows. Qwen Code's ``parentUuid`` is a chain, so no event
carries it as ``parent_span_id``; the only delegation edges come from
sub-agent transcripts under ``<project>/subagents/<sid>/``.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from clawmetry.adapters.qwen_code import QwenCodeAdapter
from clawmetry.replay_schema import validate

_FIXTURE_PROJECTS_DIR = os.path.join(
    os.path.dirname(__file__), "fixtures", "runtimes", "qwen_code", "projects",
)
_REAL_PROJECTS_DIR = os.path.join(
    os.path.dirname(__file__), "fixtures", "runtimes", "qwen_code", "REAL",
    "projects",
)


@pytest.fixture
def adapter() -> QwenCodeAdapter:
    return QwenCodeAdapter(projects_dir=_FIXTURE_PROJECTS_DIR)


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


def _record(uuid, parent, ts, rtype, **extra):
    base = {"uuid": uuid, "parentUuid": parent, "sessionId": "parent-1",
            "timestamp": ts, "type": rtype, "cwd": "/tmp/demo",
            "version": "0.21.14"}
    base.update(extra)
    return json.dumps(base)


@pytest.fixture
def subagent_projects(tmp_path) -> str:
    """A parent chat that spawns one sub-agent through a ``task`` call."""
    proj = tmp_path / "projects" / "-tmp-demo"
    chats = proj / "chats"
    chats.mkdir(parents=True)
    (chats / "parent-1.jsonl").write_text("\n".join([
        _record("u1", None, "2026-05-25T10:00:00.000Z", "user",
                message={"role": "user", "parts": [{"text": "Audit the repo."}]}),
        _record("a1", "u1", "2026-05-25T10:00:05.000Z", "assistant",
                model="qwen3:8b",
                message={"role": "model", "parts": [
                    {"functionCall": {"id": "call_task1", "name": "task",
                                      "args": {"prompt": "Scan files"}}}]},
                usageMetadata={"promptTokenCount": 10, "candidatesTokenCount": 5,
                               "totalTokenCount": 15}),
        _record("r1", "a1", "2026-05-25T10:01:00.000Z", "tool_result",
                message={"role": "user", "parts": [
                    {"functionResponse": {"id": "call_task1", "name": "task",
                                          "response": {"output": "done"}}}]},
                toolCallResult={"callId": "call_task1", "status": "success"}),
        _record("a2", "r1", "2026-05-25T10:01:05.000Z", "assistant",
                model="qwen3:8b",
                message={"role": "model", "parts": [{"text": "All good."}]},
                usageMetadata={"promptTokenCount": 20, "candidatesTokenCount": 3,
                               "totalTokenCount": 23}),
    ]) + "\n")
    sub = proj / "subagents" / "parent-1"
    sub.mkdir(parents=True)
    (sub / "agent-abc.jsonl").write_text("\n".join([
        json.dumps({"uuid": "c-u1", "parentUuid": None, "sessionId": "agent-abc",
                    "timestamp": "2026-05-25T10:00:10.000Z", "type": "user",
                    "message": {"role": "user", "parts": [{"text": "Scan files"}]}}),
        json.dumps({"uuid": "c-a1", "parentUuid": "c-u1", "sessionId": "agent-abc",
                    "timestamp": "2026-05-25T10:00:40.000Z", "type": "assistant",
                    "model": "qwen3:8b",
                    "message": {"role": "model", "parts": [{"text": "Two files."}]},
                    "usageMetadata": {"promptTokenCount": 5,
                                      "candidatesTokenCount": 2,
                                      "totalTokenCount": 7}}),
    ]) + "\n")
    (sub / "agent-abc.meta.json").write_text(json.dumps({
        "agentId": "abc", "agentType": "general-purpose",
        "description": "Scan files", "parentSessionId": "parent-1",
        "toolUseId": "call_task1", "parentAgentId": None,
        "status": "completed", "isBackgrounded": False,
        "resolvedApprovalMode": "yolo", "model": "qwen3:8b",
    }))
    return str(tmp_path / "projects")


# -- mapper over the shipped fixtures ----------------------------------------


def test_every_event_is_valid_and_unique(adapter):
    for sess in adapter.list_sessions():
        events = list(adapter.iter_replay_events(sess.id))
        assert events, sess.id
        assert [validate(e) for e in events] == [[]] * len(events)
        ids = [e["span_id"] for e in events]
        assert len(ids) == len(set(ids))
        assert all(e["runtime"] == "qwen_code" for e in events)
        assert all(e["session_id"] == sess.id for e in events)


def test_tool_session_kind_sequence(adapter):
    kinds = [e["kind"] for e in adapter.iter_replay_events("sess-tool-0001")]
    assert kinds == [
        "mode.changed", "llm.call", "thinking", "llm.response", "tool.call",
        "approval.decided", "tool.result", "thinking", "llm.response",
    ]


def test_parent_uuid_chain_is_not_a_delegation_edge(adapter):
    events = list(adapter.iter_replay_events("sess-tool-0001"))
    by_kind = {}
    for e in events:
        by_kind.setdefault(e["kind"], []).append(e)
    for kind in ("llm.call", "llm.response", "thinking", "tool.call",
                 "tool.result", "mode.changed"):
        assert all(e["parent_span_id"] is None for e in by_kind[kind]), kind
    # The one parented event is the approval, gated on its tool.call.
    (approval,) = by_kind["approval.decided"]
    assert approval["parent_span_id"] == by_kind["tool.call"][0]["span_id"]


def test_mode_chip_is_unknown_for_a_top_level_session(adapter):
    first = next(iter(adapter.iter_replay_events("sess-text-0002")))
    assert first["kind"] == "mode.changed"
    assert first["mode"] == {"permission": "unknown"}
    assert first["span_id"] == "qwen_code:sess-text-0002:mode"


def test_tool_call_result_and_decision_payloads(adapter):
    events = {e["kind"]: e for e in adapter.iter_replay_events("sess-tool-0001")}
    call = events["tool.call"]
    assert call["span_id"] == "qwen_code:sess-tool-0001:call:call_demo01"
    assert call["payload"] == {"tool": "list_directory", "call_id": "call_demo01",
                               "args": {"path": "/tmp/demo"}}
    result = events["tool.result"]
    assert result["payload"]["call_id"] == "call_demo01"
    assert result["payload"]["status"] == "success"
    assert "probe.txt" in result["payload"]["output"]
    decided = events["approval.decided"]
    assert decided["approval"] == {"status": "approved", "resolver": "policy",
                                   "decision_reason": "auto_accept"}
    assert decided["payload"]["tool"] == "list_directory"


def test_llm_response_carries_usage_and_model(adapter):
    responses = [e for e in adapter.iter_replay_events("sess-tool-0001")
                 if e["kind"] == "llm.response"]
    assert responses[0]["payload"]["model"] == "qwen3:8b"
    assert responses[0]["payload"]["usage"]["prompt_tokens"] == 1200
    assert responses[0]["payload"]["usage"]["output_tokens"] == 80
    assert responses[1]["payload"]["text"] == "The directory contains one file: probe.txt."


def test_user_turn_text_and_thinking(adapter):
    events = list(adapter.iter_replay_events("sess-tool-0001"))
    assert events[1]["kind"] == "llm.call"
    assert events[1]["payload"]["text"].startswith("List the files")
    assert events[2]["kind"] == "thinking"
    assert "directory listing" in events[2]["payload"]["text"]


def test_unknown_session_and_limit(adapter):
    assert list(adapter.iter_replay_events("no-such-session")) == []
    assert len(list(adapter.iter_replay_events("sess-tool-0001", limit=3))) == 3
    assert list(adapter.iter_replay_events("sess-tool-0001", limit=0)) == []


def test_garbage_file_yields_nothing(tmp_path):
    chats = tmp_path / "projects" / "-tmp-bad" / "chats"
    chats.mkdir(parents=True)
    (chats / "bad-1.jsonl").write_text("not json\n{\"uuid\": 1}\n[1,2]\n")
    a = QwenCodeAdapter(projects_dir=str(tmp_path / "projects"))
    events = list(a.iter_replay_events("bad-1"))
    assert [validate(e) for e in events] == [[]] * len(events)


@pytest.mark.skipif(
    not os.path.isdir(_REAL_PROJECTS_DIR), reason="REAL capture absent")
def test_real_capture_maps_cleanly():
    a = QwenCodeAdapter(projects_dir=_REAL_PROJECTS_DIR)
    for sess in a.list_sessions():
        events = list(a.iter_replay_events(sess.id))
        assert events
        assert [validate(e) for e in events] == [[]] * len(events)
        assert events[0]["kind"] == "mode.changed"


# -- sub-agent transcripts ---------------------------------------------------


def test_subagent_is_inlined_under_its_spawning_call(subagent_projects):
    a = QwenCodeAdapter(projects_dir=subagent_projects)
    events = list(a.iter_replay_events("parent-1"))
    assert [validate(e) for e in events] == [[]] * len(events)
    kinds = [e["kind"] for e in events]
    assert kinds == [
        "mode.changed", "llm.call", "llm.response", "tool.call", "agent.spawn",
        "llm.call", "llm.response", "agent.return", "tool.result",
        "llm.response",
    ]
    call = events[3]
    spawn = events[4]
    assert spawn["parent_span_id"] == call["span_id"]
    assert spawn["payload"]["permission"] == "yolo"
    assert spawn["payload"]["child_session_id"] == "parent-1::agent-abc"
    assert spawn["payload"]["status"] == "completed"
    assert events[5]["parent_span_id"] == spawn["span_id"]
    assert events[6]["parent_span_id"] == spawn["span_id"]
    assert events[7]["parent_span_id"] == spawn["span_id"]
    assert events[7]["ts"] == events[6]["ts"]
    # The inlined child never emits mode.changed, so the parent chip stays
    # honest, and all rows belong to the parent session.
    assert kinds.count("mode.changed") == 1
    assert all(e["session_id"] == "parent-1" for e in events)


def test_subagent_folds_into_the_parent_turn(subagent_projects):
    from routes.sessions import _build_replay_tree

    a = QwenCodeAdapter(projects_dir=subagent_projects)
    tree = _build_replay_tree("parent-1", list(a.iter_replay_events("parent-1")))
    assert len(tree["turns"]) == 1
    assert tree["mode"] == {"permission": "unknown"}
    (delegation,) = tree["turns"][0]["delegations"]
    assert delegation["span_id"].endswith(":spawn:agent-abc")
    assert [e["kind"] for e in delegation["events"]] == [
        "llm.call", "llm.response", "agent.return"]


def test_subagent_standalone_replay_uses_its_resolved_mode(subagent_projects):
    a = QwenCodeAdapter(projects_dir=subagent_projects)
    events = list(a.iter_replay_events("parent-1::agent-abc"))
    assert [validate(e) for e in events] == [[]] * len(events)
    assert events[0]["mode"] == {"permission": "yolo"}
    assert all(e["parent_span_id"] is None for e in events)
    assert all(e["session_id"] == "parent-1::agent-abc" for e in events)
    # Distinct span ids from the inlined copy under the parent.
    inlined = {e["span_id"] for e in a.iter_replay_events("parent-1")}
    assert not inlined & {e["span_id"] for e in events}


# -- store + daemon hook -----------------------------------------------------


def test_store_upsert_is_idempotent_and_skips_invalid(store, adapter):
    rows = list(adapter.iter_replay_events("sess-tool-0001"))
    assert store.ingest_replay_events(rows) == 9
    assert store.ingest_replay_events(rows) == 9
    got = store.query_replay_events(session_id="sess-tool-0001")
    assert len(got) == 9
    assert got[0]["kind"] == "mode.changed"
    assert got[0]["mode"] == {"permission": "unknown"}
    assert got[5]["approval"]["status"] == "approved"
    assert got[4]["payload"]["args"] == {"path": "/tmp/demo"}
    assert store.ingest_replay_events([
        {"kind": "nope", "span_id": "z", "session_id": "q", "runtime": "r",
         "ts": 1.0},
        "not a row",
    ]) == 0
    assert store.ingest_replay_events([]) == 0


def test_store_rejects_read_only(store, monkeypatch):
    monkeypatch.setattr(store, "_read_only", True)
    with pytest.raises(RuntimeError):
        store.ingest_replay_events([])


def test_sync_hook_rehomes_rows_onto_the_namespaced_id(store, adapter):
    from clawmetry import sync

    n = sync._ingest_family_replay_events(
        store, adapter, "sess-tool-0001", "qwen_code:sess-tool-0001", "qwen_code")
    assert n == 9
    assert store.query_replay_events(session_id="sess-tool-0001") == []
    rows = store.query_replay_events(session_id="qwen_code:sess-tool-0001")
    assert len(rows) == 9
    assert rows[0]["span_id"] == "qwen_code:sess-tool-0001:mode"


def test_sync_hook_is_best_effort(store):
    from clawmetry import sync

    class NoMapper:
        pass

    class Raising:
        def iter_replay_events(self, session_id):
            raise RuntimeError("boom")

    class Lazy:
        def iter_replay_events(self, session_id):
            yield {"kind": "llm.call", "span_id": "x:1", "session_id": session_id,
                   "runtime": "x", "ts": 1.0, "payload": {}}
            raise RuntimeError("late")

    assert sync._ingest_family_replay_events(store, NoMapper(), "a", "x:a", "x") == 0
    assert sync._ingest_family_replay_events(store, Raising(), "a", "x:a", "x") == 0
    assert sync._ingest_family_replay_events(store, Lazy(), "a", "x:a", "x") == 0
    assert store.query_replay_events(session_id="x:a") == []


def test_replay_tree_endpoint_serves_the_written_rows(store, adapter, monkeypatch):
    from flask import Flask
    from routes.sessions import bp_sessions
    from clawmetry import local_store as ls
    from clawmetry import sync

    monkeypatch.setattr(
        "routes.local_query.local_store_via_daemon", lambda *a, **kw: None)
    monkeypatch.setattr(ls, "get_store", lambda read_only=False: store)
    sync._ingest_family_replay_events(
        store, adapter, "sess-tool-0001", "qwen_code:sess-tool-0001", "qwen_code")

    app = Flask(__name__)
    app.register_blueprint(bp_sessions)
    body = app.test_client().get(
        "/api/replay-tree/qwen_code:sess-tool-0001").get_json()
    assert body["runtime"] == "qwen_code"
    assert body["mode"] == {"permission": "unknown"}
    assert body["row_count"] == 9
    assert len(body["turns"]) == 1
    turn = body["turns"][0]
    assert turn["turn_id"] == "qwen_code:sess-tool-0001:u-0001"
    assert len(turn["approvals"]) == 1
    assert turn["delegations"] == []
    assert body["workflows"] == []
