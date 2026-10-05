"""Cross-layer Assistant and saved-dashboard-panel regression tests.

These tests keep the provider/model boundary mocked, but use a real temporary
DuckDB LocalStore behind both blueprints.  That is intentional: the route's
``sources.rows`` field is a row count integer while a query result also has a
top-level ``rows`` list, and fake stores can hide shape or persistence bugs.
"""

from __future__ import annotations

import importlib
import json

import pytest
from flask import Flask

from clawmetry import assistant_service as assistant
from clawmetry import assistant_executor as execution, assistant_http
from routes.assistant import bp_assistant
import routes.dashboards as dashboards


@pytest.fixture()
def real_stack(tmp_path, monkeypatch):
    monkeypatch.setenv("CLAWMETRY_URL", "http://127.0.0.1:8911")
    monkeypatch.setenv("CLAWMETRY_TOKEN", "ci-test-token")
    monkeypatch.setenv(
        "CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "assistant-pipeline.duckdb")
    )

    import clawmetry.local_store as local_store

    local_store._reset_singleton_for_tests()
    importlib.reload(local_store)
    store_ref = {"store": local_store.get_store()}

    with store_ref["store"]._write_lock:
        store_ref["store"]._conn.executemany(
            """
            INSERT INTO sessions
                (agent_type, session_id, node_id, agent_id, started_at,
                 last_active_at, status, total_tokens, cost_usd,
                 message_count, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    "openclaw",
                    "openclaw:session-1",
                    "node-1",
                    "agent-1",
                    "2026-10-01T10:00:00Z",
                    "2026-10-01T10:05:00Z",
                    "completed",
                    12,
                    0.25,
                    3,
                    1,
                ),
                (
                    # Legacy rows still carry agent_type=openclaw; runtime is
                    # authoritative in the session_id prefix.
                    "openclaw",
                    "codex:session-2",
                    "node-1",
                    "agent-2",
                    "2026-10-01T11:00:00Z",
                    "2026-10-01T11:06:00Z",
                    "completed",
                    30,
                    1.50,
                    4,
                    2,
                ),
            ],
        )

    executor_ref={'executor':execution.Executor(store_ref['store'],'test-node')}
    def dispatch(method, **kwargs):
        executor=executor_ref['executor']
        if executor.store is not store_ref['store']:
            executor=execution.Executor(store_ref['store'],'test-node')
            executor_ref['executor']=executor
        return {'start_assistant_job':executor.start,'read_assistant_job':executor.read,
                'cancel_assistant_job':executor.cancel}[method](**kwargs)
    monkeypatch.setattr(assistant_http,'rpc',dispatch)
    monkeypatch.setattr(assistant,'_egress_suppressed',lambda:False)
    monkeypatch.setattr(assistant,'_provider',lambda requested='auto',api_key=None:('test-provider','test-credential'))
    app=Flask(__name__)
    app.register_blueprint(bp_assistant)
    app.register_blueprint(dashboards.bp_dashboards)
    try:
        yield {'app':app,'client':app.test_client(),'local_store':local_store,'store_ref':store_ref}
    finally:
        for job in executor_ref['executor'].jobs.values():
            job.abort()
            if job.worker and job.worker.ident is not None:job.worker.join(3)
        local_store._reset_singleton_for_tests()


@pytest.mark.parametrize('mode', ['claude_cli', 'anthropic', 'managed'])
def test_improve_reference_survives_http_executor_save_and_followup(real_stack, monkeypatch, mode):
    """AC-IMPROVE-CHAT-001.6: persisted provenance reaches a later HTTP turn."""
    from types import SimpleNamespace
    from clawmetry import entitlements
    from tests.test_assistant_evidence import event

    monkeypatch.setattr(entitlements, 'get_entitlement', lambda: SimpleNamespace(allows_runtime=lambda _: True))
    monkeypatch.setattr(assistant, '_provider', lambda *args: (mode, 'test-credential'))
    store = real_stack['store_ref']['store']
    sid = 'codex:session-2'
    reference = {'session_id': sid, 'runtime': 'codex', 'event_id': 'events:selected'}
    store._conn.execute('UPDATE sessions SET node_id=? WHERE session_id=?', ['test-node', sid])
    event(store, 'selected', sid=sid, node='test-node', data={'role': 'user', 'content': 'Please start the service again.'})
    calls = []

    def generate(control, mode, credential, system, prompt, **kwargs):
        packet = json.loads(prompt)
        calls.append(packet)
        assert packet['improve_review']['event_id'] == reference['event_id']
        assert 'future run' in system
        if system.startswith(assistant._PLAN):
            return json.dumps({'session_reads': [{**reference, 'mode': 'event'}]})
        return 'Confirm the intended service and check its recorded status [1].'

    monkeypatch.setattr(assistant, '_stream_generate', generate)
    client = real_stack['client']
    response = client.post('/api/assistant/chat', json={'message': 'Explain this moment', 'improve': reference})
    body = response.get_json()
    assert response.status_code == 200, body
    saved = client.get('/api/assistant/conversations/' + body['conversation_id']).get_json()
    assert saved['title'] == 'Explain: Please start the service again.'
    assert saved['messages'][0]['improve'] == reference
    assert saved['messages'][1]['sources'][0]['read']['event_id'] == reference['event_id']
    followup = client.post('/api/assistant/chat', json={
        'message': 'What would show that it helped?', 'conversation_id': body['conversation_id']})
    assert followup.status_code == 200, followup.get_json()
    assert len(calls) == 4
    saved_again = client.get('/api/assistant/conversations/' + body['conversation_id']).get_json()
    assert saved_again['title'] == saved['title']
    assert len(saved_again['messages']) == 4


def _two_chart_plan():
    runtime_case = (
        "CASE WHEN split_part(session_id, ':', 1) IN ('codex') "
        "THEN split_part(session_id, ':', 1) ELSE 'openclaw' END"
    )
    return {
        "answer": "Codex used more tokens and cost more in the seeded sessions.",
        "queries": [
            {
                "title": "Tokens by runtime",
                "sql": (
                    f"SELECT {runtime_case} AS runtime, "
                    "SUM(total_tokens) AS rows FROM sessions "
                    f"GROUP BY {runtime_case} ORDER BY runtime"
                ),
                "visual": True,
                "chart_type": "bar",
                "x": "runtime",
                "y": "rows",
            },
            {
                "title": "Cost by runtime",
                "sql": (
                    f"SELECT {runtime_case} AS runtime, "
                    "SUM(cost_usd) AS cost, "
                    "COUNT(*) - COUNT(cost_usd) AS unknown_costs "
                    "FROM sessions "
                    f"GROUP BY {runtime_case} ORDER BY runtime"
                ),
                "visual": True,
                "chart_type": "line",
                "x": "runtime",
                "y": "cost",
            },
        ],
    }


def _followup_cost_table_plan():
    runtime_case = (
        "CASE WHEN split_part(session_id, ':', 1) IN ('codex') "
        "THEN split_part(session_id, ':', 1) ELSE 'openclaw' END"
    )
    return {
        "answer": "Here is the cost table with normalized runtime names.",
        "queries": [
            {
                "title": "Cost table by runtime",
                "sql": (
                    "SELECT replace(" + runtime_case + ", 'openclaw', 'OpenClaw') "
                    "AS runtime, SUM(cost_usd) AS cost_usd, "
                    "COUNT(*) - COUNT(cost_usd) AS unknown_costs "
                    "FROM sessions GROUP BY " + runtime_case + " ORDER BY runtime"
                ),
                "visual": True,
                "chart_type": "table",
                "x": "runtime",
                "y": "cost_usd",
            }
        ],
    }


def test_real_store_chat_panel_rerun_and_reopen_preserve_production_shapes(
    real_stack, monkeypatch
):
    plan = _two_chart_plan()
    followup_plan = _followup_cost_table_plan()
    generations = []
    plans = [plan, followup_plan]

    def fake_generate(mode, credential, system, prompt):
        generations.append((mode, credential, system, prompt))
        if system.startswith(assistant._PLAN):
            return json.dumps(plans.pop(0))
        if system == assistant._SYNTHESIS:
            return plan["answer"] if len(generations) <= 2 else followup_plan["answer"]
        raise AssertionError("unexpected assistant generation prompt")

    monkeypatch.setattr(assistant, "_stream_generate", lambda control, mode, credential, system, prompt, **kw: fake_generate(mode, credential, system, prompt))
    client = real_stack["client"]

    response = client.post(
        "/api/assistant/chat",
        json={"message": "Build two runtime cost and token charts"},
    )
    body = response.get_json()

    assert response.status_code == 200, body
    assert len(generations) == 2
    assert {"answer", "panels", "sources", "conversation_id"} <= body.keys()
    assert len(body["panels"]) == 2
    assert [panel["chart_spec"]["chart_type"] for panel in body["panels"]] == [
        "bar",
        "line",
    ]

    # The query result has a list called ``rows`` and each row has a scalar
    # column also called ``rows``.  The public source summary must keep its
    # production integer-count shape instead of leaking the result list.
    assert all(isinstance(source["rows"], int) for source in body["sources"])
    assert body["sources"][0]["rows"] == 2
    assert all(isinstance(row["rows"], int) for row in body["panels"][0]["rows"])
    assert body["panels"][0]["rows"]
    assert {row["runtime"] for row in body["panels"][0]["rows"]} == {
        "openclaw",
        "codex",
    }
    assert all(isinstance(row["unknown_costs"], int) for row in body["panels"][1]["rows"])
    assert all("sql" in source and source["sql"].startswith("SELECT ") for source in body["sources"])

    conversation_id = body["conversation_id"]
    conversation = real_stack["store_ref"]["store"].query_assistant_conversation(
        conversation_id=conversation_id
    )
    assert conversation["id"] == conversation_id
    assert conversation["messages"][-1]["sources"][0]["rows"] == 2
    conversation_http = client.get(
        "/api/assistant/conversations/" + conversation_id
    )
    assert conversation_http.status_code == 200
    assert conversation_http.get_json()["id"] == conversation_id

    followup = client.post(
        "/api/assistant/chat",
        json={
            "conversation_id": conversation_id,
            "message": "Now show the cost table with normalized runtime names.",
        },
    )
    followup_body = followup.get_json()
    assert followup.status_code == 200, followup_body
    assert len(generations) == 4
    assert len(followup_body["panels"]) == 1
    followup_panel = followup_body["panels"][0]
    assert "replace(" in followup_panel["sql"].lower()
    assert {row["runtime"] for row in followup_panel["rows"]} == {
        "OpenClaw",
        "codex",
    }
    assert all(isinstance(row["unknown_costs"], int) for row in followup_panel["rows"])
    assert "normalized runtime" in generations[2][3]

    source_panel = followup_panel
    save = client.post(
        "/api/dashboard/panels",
        json={
            "name": "Cost table by runtime",
            "question": "Now show the cost table with normalized runtime names.",
            "sql": source_panel["sql"],
            "chart_spec": source_panel["chart_spec"],
        },
    )
    saved_body = save.get_json()
    assert save.status_code == 201, saved_body
    saved_panel = saved_body["panel"]
    assert saved_panel["rows"] == source_panel["rows"]
    assert all(isinstance(row["unknown_costs"], int) for row in saved_panel["rows"])

    rerun = client.get("/api/dashboard/panels/" + saved_panel["panel_id"])
    rerun_body = rerun.get_json()
    assert rerun.status_code == 200, rerun_body
    assert rerun_body["sql"] == source_panel["sql"]
    assert rerun_body["rows"] == source_panel["rows"]

    # Close and reopen the actual DuckDB file, then use the same route-facing
    # dispatch closure to prove both persisted objects survive a process turn.
    old_store = real_stack["store_ref"]["store"]
    old_store.stop(flush=False)
    real_stack["local_store"]._reset_singleton_for_tests()
    reopened = real_stack["local_store"].get_store()
    real_stack["store_ref"]["store"] = reopened

    reopened_conversation = reopened.query_assistant_conversation(
        conversation_id=conversation_id
    )
    reopened_panel = reopened.query_dashboard_panel(panel_id=saved_panel["panel_id"])
    assert reopened_conversation["messages"][-1]["sources"][0]["rows"] == 2
    assert reopened_panel["sql"] == source_panel["sql"]
    assert json.loads(reopened_panel["chart_spec"]) == source_panel["chart_spec"]
    reopened_conversation_http = client.get(
        "/api/assistant/conversations/" + conversation_id
    )
    reopened_panel_http = client.get(
        "/api/dashboard/panels/" + saved_panel["panel_id"]
    )
    assert reopened_conversation_http.status_code == 200
    assert reopened_panel_http.status_code == 200
    assert reopened_panel_http.get_json()["rows"] == source_panel["rows"]


def test_real_store_keeps_empty_results_distinct_from_sql_errors(real_stack, monkeypatch):
    plan = {
        "answer": "The first query is empty; the second query failed.",
        "queries": [
            {
                "title": "Empty result",
                "sql": "SELECT 1 AS value WHERE 1 = 0",
                "visual": True,
                "chart_type": "table",
            },
            {
                "title": "SQL error",
                "sql": "SELECT FROM sessions",
                "visual": True,
                "chart_type": "table",
            },
        ],
    }

    def fake_generate(mode, credential, system, prompt):
        if system.startswith(assistant._PLAN):
            return json.dumps(plan)
        if system == assistant._SYNTHESIS:
            return plan["answer"]
        raise AssertionError("unexpected assistant generation prompt")

    monkeypatch.setattr(assistant, "_stream_generate", lambda control, mode, credential, system, prompt, **kw: fake_generate(mode, credential, system, prompt))
    response = real_stack["client"].post(
        "/api/assistant/chat", json={"message": "Compare empty and failed queries"}
    )
    body = response.get_json()

    assert response.status_code == 200, body
    assert body["panels"][0]["rows"] == []
    assert "error" not in body["panels"][0]
    assert body["panels"][1]["rows"] == []
    assert body["panels"][1]["error"]
    assert body["sources"][0]["rows"] == 0
    assert body["sources"][0]["error"] is None
    assert body["sources"][1]["rows"] == 0
    assert body["sources"][1]["error"]


def test_stream_persists_only_complete_answer_in_real_duckdb(real_stack, monkeypatch):
    """AC-ASSIST-005.3 Completed text, sources and panels survive a store reopen."""
    import threading
    from clawmetry import assistant_providers

    finish = threading.Event()
    jobs = []

    def generate(mode, credential, system, prompt, **kwargs):
        jobs.append(kwargs["control"])
        if system.startswith(assistant._PLAN):
            return json.dumps(_two_chart_plan())
        kwargs["on_text"]("Recorded ")
        assert finish.wait(3)
        kwargs["on_text"]("runtime totals.")
        return "Recorded runtime totals."

    monkeypatch.setattr(assistant_providers, "generate", generate)
    response = real_stack["client"].post("/api/assistant/chat", json={
        "message": "Compare runtime costs", "stream": True,
    }, buffered=False)
    iterator = iter(response.response)
    try:
        for chunk in iterator:
            if chunk.startswith(b"event: delta"):
                break
        assert real_stack["store_ref"]["store"].query_assistant_conversations() == []
        finish.set()
        done = None
        for chunk in iterator:
            if chunk.startswith(b"event: done"):
                done = json.loads(chunk.decode().split("data: ", 1)[1])
        assert done is not None
        cid = done["conversation_id"]
        store = real_stack["store_ref"]["store"]
        assert len(store.query_assistant_conversations()) == 1
        stored = store.query_assistant_conversation(conversation_id=cid)["messages"][-1]
        assert stored["content"] == "Recorded runtime totals."
        assert stored["panels"] == done["panels"]
        assert stored["sources"] == done["sources"]
        assert len(stored["panels"]) == 2
        store.stop(flush=False)
        real_stack["local_store"]._reset_singleton_for_tests()
        reopened = real_stack["local_store"].get_store()
        real_stack["store_ref"]["store"] = reopened
        assert reopened.query_assistant_conversation(conversation_id=cid)["messages"][-1] == stored
    finally:
        finish.set()
        response.close()
        for job in jobs:
            job.worker.join(2)
