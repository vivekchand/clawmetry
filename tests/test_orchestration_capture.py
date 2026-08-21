"""Orchestration capture (workflows + sub-agents) — the /api/session-orchestration
and /api/orchestration-summary routes plus LocalStore.query_subagents_lite.

The family adapters emit every spawned child as a Session with parent_id set
and extra.kind in {subagent, workflow, workflow_agent}; the daemon lands them
on the ``subagents`` table with the orchestration facts (context handed to the
child, its reply, the tool it is on right now) in the data blob (see
``_SUBAGENT_EXTRA_PASSTHROUGH`` in clawmetry/sync.py). These tests seed that
table directly and assert the two routes shape it into the tree the Sessions
tab + Activity feed render:

1. query_subagents_lite: exact-id + LIKE parent matching, no events join.
2. /api/session-orchestration/<sid>: workflow run + its agents nested under
   it, plain sub-agents separate, live counts derived from the rows.
3. A running workflow agent surfaces in summary.running_now with nowTool.
4. /api/orchestration-summary bulk shape + sessions with no children omitted.
5. Bare-uuid and runtime-prefixed parent ids resolve to the same tree.
"""

from __future__ import annotations

import importlib
import json

import pytest
from flask import Flask


PARENT = "097c0000-1111-2222-3333-444455556666"
NS_PARENT = f"claude_code:{PARENT}"
RUN = f"claude_code:{PARENT}::wf_test1234-abc"


@pytest.fixture
def app(tmp_path, monkeypatch):
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "events.duckdb"))
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_SECS", "0.05")
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_READ", "1")

    import clawmetry.local_store as ls
    importlib.reload(ls)
    import routes.local_query as lq
    importlib.reload(lq)
    import routes.sessions as sessions_mod
    importlib.reload(sessions_mod)

    # Isolate from a locally running daemon (issue #1538 pattern) — otherwise
    # _ls_call proxies into the contributor's production DuckDB, and
    # get_store() hands back a _ProxyStore instead of the tmp_path writer.
    monkeypatch.setattr(lq, "_read_discovery", lambda: None)
    monkeypatch.setattr(ls, "_daemon_registered", lambda: False)

    a = Flask(__name__)
    a.register_blueprint(sessions_mod.bp_sessions)
    yield a, ls
    try:
        ls.get_store().stop(flush=True)
    except Exception:
        pass


def _seed(ls):
    store = ls.get_store()
    # The workflow RUN (child of the parent session).
    store.ingest_subagent({
        "subagent_id": RUN,
        "agent_type": "openclaw",
        "parent_session_id": NS_PARENT,
        "spawned_at": "2026-08-19T10:00:00+00:00",
        "ended_at": None,
        "task": "orchestration-e2e",
        "status": "running",
        "cost_usd": 0.0,
        "token_count": 0,
        "kind": "workflow",
        "workflowRunId": "wf_test1234-abc",
        "workflowName": "orchestration-e2e",
        "agentCount": 2,
        "agentsRunning": 1,
        "agentsDone": 1,
        "agentsFailed": 0,
        "phases": [{"title": "Audit", "detail": "look"}],
        "runtime": "claude_code",
    })
    # A finished workflow agent (child of the run — depth 2).
    store.ingest_subagent({
        "subagent_id": f"{RUN}::agent-adead1",
        "agent_type": "openclaw",
        "parent_session_id": RUN,
        "spawned_at": "2026-08-19T10:00:05+00:00",
        "ended_at": "2026-08-19T10:05:00+00:00",
        "task": "audit:disk",
        "status": "completed",
        "cost_usd": 1.25,
        "token_count": 5000,
        "kind": "workflow_agent",
        "workflowRunId": "wf_test1234-abc",
        "label": "audit:disk",
        "phase": "Audit",
        "prompt": "You are a research agent. Inventory X.",
        "reply": '{"found": 3}',
        "lastTool": "Bash",
        "runtime": "claude_code",
    })
    # A still-running workflow agent with a live tool.
    store.ingest_subagent({
        "subagent_id": f"{RUN}::agent-abeef2",
        "agent_type": "openclaw",
        "parent_session_id": RUN,
        "spawned_at": "2026-08-19T10:00:06+00:00",
        "ended_at": None,
        "task": "audit:web",
        "status": "running",
        "cost_usd": 0.5,
        "token_count": 2000,
        "kind": "workflow_agent",
        "workflowRunId": "wf_test1234-abc",
        "label": "audit:web",
        "phase": "Audit",
        "prompt": "Search upstream docs.",
        "nowTool": "WebFetch",
        "lastTool": "WebFetch",
        "runtime": "claude_code",
    })
    # A plain (non-workflow) sub-agent, direct child of the parent.
    store.ingest_subagent({
        "subagent_id": f"{NS_PARENT}::agent-acafe3",
        "agent_type": "openclaw",
        "parent_session_id": NS_PARENT,
        "spawned_at": "2026-08-19T09:00:00+00:00",
        "ended_at": "2026-08-19T09:02:00+00:00",
        "task": "explore the repo",
        "status": "completed",
        "cost_usd": 0.10,
        "token_count": 800,
        "kind": "subagent",
        "agentType": "Explore",
        "prompt": "Find the config loader.",
        "reply": "It lives in clawmetry/config.py.",
        "runtime": "claude_code",
    })
    # Noise: a child of an UNRELATED session must never leak into the tree.
    store.ingest_subagent({
        "subagent_id": "claude_code:ffff0000-aaaa-bbbb-cccc-dddd11112222::agent-a9",
        "agent_type": "openclaw",
        "parent_session_id": "claude_code:ffff0000-aaaa-bbbb-cccc-dddd11112222",
        "spawned_at": "2026-08-19T10:00:00+00:00",
        "task": "other",
        "status": "completed",
        "kind": "subagent",
    })


def test_query_subagents_lite_matches_exact_and_like(app):
    _, ls = app
    _seed(ls)
    store = ls.get_store()
    rows = store.query_subagents_lite(parent_session_ids=[NS_PARENT])
    assert {r["subagent_id"] for r in rows} == {RUN, f"{NS_PARENT}::agent-acafe3"}
    # LIKE patterns pull the run's agents (grandchildren) too.
    rows = store.query_subagents_lite(
        parent_session_ids=[NS_PARENT],
        parent_like=[f"%:{PARENT}::%"],
    )
    ids = {r["subagent_id"] for r in rows}
    assert f"{RUN}::agent-adead1" in ids and f"{RUN}::agent-abeef2" in ids
    # data blob round-trips the orchestration fields.
    agent = next(r for r in rows if r["subagent_id"].endswith("agent-abeef2"))
    assert agent["data"]["nowTool"] == "WebFetch"
    assert agent["data"]["kind"] == "workflow_agent"


def test_session_orchestration_tree(app):
    a, ls = app
    _seed(ls)
    client = a.test_client()
    d = client.get(f"/api/session-orchestration/{NS_PARENT}").get_json()
    assert d["_source"] == "local_store"
    assert len(d["workflows"]) == 1
    wf = d["workflows"][0]
    assert wf["name"] == "orchestration-e2e"
    assert wf["status"] == "running"
    assert len(wf["agents"]) == 2
    # Live counts derived from the agent rows.
    assert wf["agentsRunning"] == 1 and wf["agentsDone"] == 1
    done = next(x for x in wf["agents"] if x["status"] == "completed")
    assert done["prompt"].startswith("You are a research agent")
    assert done["reply"] == '{"found": 3}'
    running = next(x for x in wf["agents"] if x["status"] == "running")
    assert running["nowTool"] == "WebFetch"
    # Plain sub-agent rides separately with its context + reply.
    assert len(d["subagents"]) == 1
    assert d["subagents"][0]["reply"].startswith("It lives in")
    # The unrelated session's child never leaks in.
    all_ids = [x["id"] for x in wf["agents"]] + [x["id"] for x in d["subagents"]]
    assert not any("ffff0000" in x for x in all_ids)
    # Summary counts + running_now carry the live tool.
    s = d["summary"]
    assert s["workflows"]["running"] == 1
    assert s["agents"]["total"] == 2
    assert any(r["nowTool"] == "WebFetch" for r in s["running_now"])


def test_session_orchestration_accepts_bare_uuid(app):
    a, ls = app
    _seed(ls)
    client = a.test_client()
    d = client.get(f"/api/session-orchestration/{PARENT}").get_json()
    assert len(d["workflows"]) == 1
    assert len(d["workflows"][0]["agents"]) == 2


def test_orchestration_summary_bulk(app):
    a, ls = app
    _seed(ls)
    client = a.test_client()
    quiet = "claude_code:00000000-0000-0000-0000-000000000000"
    d = client.get(
        "/api/orchestration-summary",
        query_string={"session_ids": f"{NS_PARENT},{quiet}"},
    ).get_json()
    assert NS_PARENT in d["sessions"]
    assert quiet not in d["sessions"]  # honest omission, no zero-noise
    s = d["sessions"][NS_PARENT]
    assert s["workflows"]["total"] == 1
    assert s["agents"]["total"] == 2
    assert s["subagents"]["total"] == 1
    # Bulk shape is the polled one: no prompt/reply text anywhere.
    assert "prompt" not in json.dumps(d)


def test_orchestration_empty_session_is_honest(app):
    a, _ = app
    client = a.test_client()
    d = client.get("/api/session-orchestration/claude_code:no-such").get_json()
    assert d["workflows"] == [] and d["subagents"] == []
    assert d["summary"]["children"] == 0


def test_subagents_shaper_carries_orchestration_fields_for_cloud(app):
    """The /api/subagents shaper is ALSO what the sync daemon reads back to
    build the cloud snapshot's ``subagents[]`` slice. If the orchestration
    fields stop riding it, the hosted dashboard silently degrades to the
    legacy flat list — the feature goes inert in cloud while local keeps
    working (the classic silent-cloud-drift class). Lock the contract.
    """
    a, ls = app
    _seed(ls)
    import routes.sessions as sessions_mod
    rows = ls.get_store().query_subagents(limit=500)
    shaped = sessions_mod._try_local_store_subagents(_rows=rows)
    assert shaped and shaped["subagents"]
    by_id = {x["sessionId"]: x for x in shaped["subagents"]}

    run = by_id[RUN]
    assert run["kind"] == "workflow"
    assert run["workflowRunId"] == "wf_test1234-abc"
    assert run["workflowName"] == "orchestration-e2e"
    assert run["agentCount"] == 2

    agent = by_id[f"{RUN}::agent-adead1"]
    assert agent["kind"] == "workflow_agent"
    assert agent["phase"] == "Audit"
    assert agent["prompt"].startswith("You are a research agent")
    assert agent["reply"] == '{"found": 3}'

    live = by_id[f"{RUN}::agent-abeef2"]
    assert live["nowTool"] == "WebFetch"          # only while running

    plain = by_id[f"{NS_PARENT}::agent-acafe3"]
    assert plain["kind"] == "subagent"
    assert plain["agentType"] == "Explore"
    assert plain["reply"].startswith("It lives in")

