"""HTTP contract tests for persistent, user-authored dashboard panels."""

import pytest

from routes.dashboards import bp_dashboards


@pytest.fixture()
def panel_stack(monkeypatch, tmp_path):
    from flask import Flask
    from clawmetry import local_store, assistant_executor as execution, assistant_http, assistant_service
    monkeypatch.setattr(local_store,"DB_PATH",tmp_path/"panels.duckdb")
    store=local_store.LocalStore()
    executor=execution.Executor(store,"test-node")

    app = Flask(__name__)
    app.register_blueprint(bp_dashboards)
    stored = {}
    calls = []
    no_override = object()
    state = {
        "query_result": {"rows": [{"day": "today", "tokens": 12}]},
        "panel_override": no_override,
    }

    def fake_call(method, **kwargs):
        calls.append((method, kwargs))
        if method == "upsert_dashboard_panel":
            row = {
                "panel_id": kwargs["panel_id"],
                "name": kwargs["name"],
                "question": kwargs["question"],
                "sql": kwargs["sql"],
                "chart_spec": kwargs["chart_spec"],
                "created_at": kwargs["created_at"],
                "updated_at": kwargs["created_at"],
            }
            stored[row["panel_id"]] = row
            return row
        if method == "query_dashboard_panels":
            return list(stored.values())
        if method == "query_dashboard_panel":
            if state["panel_override"] is not no_override:
                if state["panel_override"] is None:
                    raise assistant_service._ChatFailure("Saved panels are unavailable.",503)
                return state["panel_override"]
            return stored.get(kwargs["panel_id"])
        if method == "query_assistant_sql":
            return state["query_result"]
        if method == "delete_dashboard_panel":
            return bool(stored.pop(kwargs["panel_id"], None))
        raise AssertionError(method)

    monkeypatch.setattr(executor.service,'call',fake_call)
    monkeypatch.setattr(assistant_http,'rpc',lambda method,**kwargs:{
        'start_assistant_job':executor.start,'read_assistant_job':executor.read,
        'cancel_assistant_job':executor.cancel}[method](**kwargs))
    original=executor.receipts.finish
    def finish(rid,outcome,check, **kwargs):
        m=outcome.mutation or {}
        if m.get('kind')=='panel_create':
            fake_call('upsert_dashboard_panel',**{k:m[k] for k in ('panel_id','name','question','sql','chart_spec','created_at')})
        return original(rid,outcome,check, **kwargs)
    monkeypatch.setattr(executor.receipts,'finish',finish)
    yield {
        "client": app.test_client(),
        "stored": stored,
        "calls": calls,
        "state": state,
        "no_override": no_override,
    }
    for job in executor.jobs.values():
        job.abort()
        if job.worker and job.worker.ident is not None:job.worker.join(3)
    store.stop(flush=False)


@pytest.fixture()
def client(panel_stack):
    return panel_stack["client"]


def _panel_payload(**overrides):
    payload = {
        "name": "Tokens by day",
        "question": "How many tokens did I use today?",
        "sql": "SELECT 'today' AS day, 12 AS tokens",
        "chart_spec": {"chart_type": "bar", "x": "day", "y": "tokens"},
    }
    payload.update(overrides)
    return payload


def _query_calls(stack):
    return [
        method for method, _kwargs in stack["calls"] if method == "query_assistant_sql"
    ]


def test_create_and_read_panel_reruns_the_saved_query(client):
    response = client.post("/api/dashboard/panels", json=_panel_payload())
    assert response.status_code == 201
    panel = response.get_json()["panel"]
    assert panel["chart_spec"]["chart_type"] == "bar"
    assert panel["rows"] == [{"day": "today", "tokens": 12}]

    loaded = client.get("/api/dashboard/panels/" + panel["panel_id"])
    assert loaded.status_code == 200
    assert loaded.get_json()["question"] == "How many tokens did I use today?"


def test_create_uses_strict_query_result_before_persisting_invalid_sql(panel_stack):
    panel_stack["state"]["query_result"] = {
        "rows": [],
        "error": "SQL rejected: only SELECT queries are allowed",
    }

    response = panel_stack["client"].post(
        "/api/dashboard/panels",
        json=_panel_payload(sql="REPLACE INTO events VALUES (1)"),
    )

    assert response.status_code == 400
    assert "SQL rejected" in response.get_json()["error"]
    assert panel_stack["stored"] == {}
    methods = [method for method, _kwargs in panel_stack["calls"]]
    assert methods == ["query_assistant_sql"]


def test_create_allows_read_only_replace_function_and_does_not_use_legacy_guard(
    panel_stack,
):
    response = panel_stack["client"].post(
        "/api/dashboard/panels",
        json=_panel_payload(
            name="Normalized runtime",
            sql="SELECT replace('claude_code', '_', '-') AS runtime",
        ),
    )

    assert response.status_code == 201
    assert response.get_json()["panel"]["rows"]
    assert len(_query_calls(panel_stack)) == 1


def test_create_returns_503_for_unavailable_query_without_persisting(panel_stack):
    panel_stack["state"]["query_result"] = None

    response = panel_stack["client"].post(
        "/api/dashboard/panels", json=_panel_payload()
    )

    assert response.status_code == 503
    assert panel_stack["stored"] == {}
    assert [method for method, _kwargs in panel_stack["calls"]] == [
        "query_assistant_sql"
    ]


def test_post_and_get_retain_truncated_notice_and_reuse_post_rows(panel_stack):
    panel_stack["state"]["query_result"] = {
        "rows": [{"day": "today", "tokens": 12}],
        "truncated": True,
        "notice": "Results truncated to 100 rows.",
    }

    response = panel_stack["client"].post(
        "/api/dashboard/panels", json=_panel_payload()
    )
    assert response.status_code == 201
    panel = response.get_json()["panel"]
    assert panel["truncated"] is True
    assert panel["notice"] == "Results truncated to 100 rows."
    assert len(_query_calls(panel_stack)) == 1
    assert [method for method, _kwargs in panel_stack["calls"]] == [
        "query_assistant_sql",
        "upsert_dashboard_panel",
    ]

    loaded = panel_stack["client"].get(
        "/api/dashboard/panels/" + panel["panel_id"]
    )
    assert loaded.status_code == 200
    loaded_panel = loaded.get_json()
    assert loaded_panel["truncated"] is True
    assert loaded_panel["notice"] == "Results truncated to 100 rows."
    assert len(_query_calls(panel_stack)) == 2


def test_question_limit_matches_assistant_at_4000_characters(panel_stack):
    accepted = panel_stack["client"].post(
        "/api/dashboard/panels",
        json=_panel_payload(question="q" * 4_000),
    )
    assert accepted.status_code == 201

    rejected = panel_stack["client"].post(
        "/api/dashboard/panels",
        json=_panel_payload(question="q" * 4_001),
    )
    assert rejected.status_code == 400
    assert "4,000" in rejected.get_json()["error"]


def test_get_distinguishes_missing_panel_from_unavailable_store(panel_stack):
    panel_stack["state"]["panel_override"] = {}
    missing = panel_stack["client"].get("/api/dashboard/panels/missing")
    assert missing.status_code == 404

    panel_stack["state"]["panel_override"] = None
    unavailable = panel_stack["client"].get("/api/dashboard/panels/anything")
    assert unavailable.status_code == 503
