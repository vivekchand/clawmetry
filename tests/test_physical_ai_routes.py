"""The free Physical AI HTTP surface reads bounded persisted evidence only.

"""
from pathlib import Path
from types import SimpleNamespace

import pytest
from flask import Flask

from routes import physical_ai


@pytest.fixture(scope="session", autouse=True)
def server():
    """Route tests use an isolated Flask client, without a live dashboard."""
    yield None


@pytest.fixture
def client(monkeypatch):
    root = Path(__file__).resolve().parents[1] / "clawmetry"
    app = Flask(__name__, template_folder=str(root / "templates"), static_folder=str(root / "static"))
    app.register_blueprint(physical_ai.bp_physical_ai)
    calls = []

    def call(method, **kwargs):
        calls.append((method, kwargs))
        if method == "query_physical_ai_runs":
            return {"runs": [{"run_id": "a" * 32, "robot_id": "test"}], "has_more": False}
        return {"events": [{"sequence": 1, "kind": "command.returned", "data": {"outcome": "unknown"}}], "has_more": False, "next_after": 1}

    monkeypatch.setattr(physical_ai, "_call", call)
    return app.test_client(), calls


def test_free_runs_use_persisted_bounded_query(client):
    http, calls = client
    response = http.get("/api/physical-ai/runs?robot_id=my-robot&limit=7&before_ns=123&before_run_id=" + "b" * 32)
    assert response.status_code == 200
    assert response.json["runs"][0]["robot_id"] == "test"
    assert calls == [("query_physical_ai_runs", {"robot_id": "my-robot", "limit": 7, "before_ns": 123, "before_run_id": "b" * 32})]


@pytest.mark.parametrize("query", ["limit=0", "limit=101", "limit=-1", "limit=3.0", "limit=nan", "limit=99999999999999999999999", "robot_id=", "robot_id=" + "a" * 201, "robot_id=%00", "before_ns=3", "before_run_id=" + "a" * 32, "before_ns=1&before_run_id=not-a-run", "before_ns=9223372036854775808&before_run_id=" + "a" * 32, "unknown=yes"])
def test_invalid_run_filters_do_not_reach_store(client, query):
    http, calls = client
    assert http.get("/api/physical-ai/runs?" + query).status_code == 400
    assert calls == []


def test_event_cursor_preserves_command_evidence(client):
    http, calls = client
    response = http.get("/api/physical-ai/runs/" + "a" * 32 + "/events?after=4&limit=12")
    assert response.status_code == 200
    assert response.json["events"][0]["data"]["outcome"] == "unknown"
    assert calls[0] == ("query_physical_ai_events", {"run_id": "a" * 32, "after": 4, "limit": 12})


@pytest.mark.parametrize("suffix", ["bad/events", "A" * 32 + "/events", "a" * 32 + "/events?after=-1", "a" * 32 + "/events?limit=501", "a" * 32 + "/events?other=1"])
def test_bad_event_queries_do_not_reach_store(client, suffix):
    http, calls = client
    assert http.get("/api/physical-ai/runs/" + suffix).status_code == 400
    assert not calls


@pytest.mark.parametrize("endpoint", ["/api/physical-ai/runs", "/api/physical-ai/runs/" + "a" * 32 + "/events"])
def test_collector_failure_has_useful_503_without_raw_exception(client, monkeypatch, endpoint):
    http, _ = client

    def fail(*args, **kwargs):
        raise RuntimeError("credential SECRET and private path")

    monkeypatch.setattr(physical_ai, "_call", fail)
    response = http.get(endpoint)
    assert response.status_code == 503
    assert response.json["available"] is False
    assert "sync daemon" in response.json["message"]
    assert "SECRET" not in response.text


def test_public_read_helper_requests_read_only_store(monkeypatch):
    """The handler uses the public read-only store query boundary.

    """
    from clawmetry import local_store
    calls = []

    def store(**kwargs):
        calls.append(kwargs)
        return SimpleNamespace(query_physical_ai_runs=lambda **args: args)

    monkeypatch.setattr(local_store, "get_store", store)
    assert physical_ai._call("query_physical_ai_runs", limit=2) == {"limit": 2}
    assert calls == [{"read_only": True}]


def test_free_page_explains_published_telemetry_without_extra_package(client):
    http, calls = client
    response = http.get("/physical-ai")
    assert response.status_code == 200
    assert "No extra adapter package is needed" in response.text
    assert "cannot move or stop a robot" in response.text
    assert "Simulation evidence does not establish hardware performance" in response.text
    assert "Tasks, decisions, and incidents" in response.text
    assert "Effort (N·m)" in response.text
    assert "JUMPER.md" in response.text
    assert not calls


def test_builtin_navigation_survives_plugin_failure(client, monkeypatch):
    from routes.extensions import bp_extensions
    from clawmetry import extensions
    http, _ = client
    http.application.register_blueprint(bp_extensions)
    monkeypatch.setattr(extensions, "loaded_plugins", lambda: (_ for _ in ()).throw(RuntimeError("SECRET")))
    response = http.get("/api/extensions")
    assert response.status_code == 200
    assert response.json["navigation"] == [{"label": "Physical AI", "href": "/physical-ai", "view_group": "physical_ai"}]
    assert "SECRET" not in response.text


def test_builtin_navigation_deduplicates_paid_workbench_and_preserves_advanced_link(client, monkeypatch):
    from routes.extensions import bp_extensions
    from clawmetry import extensions
    http, _ = client
    http.application.register_blueprint(bp_extensions)
    monkeypatch.setattr(extensions, "call", lambda *a, **k: [
        {"label": "Physical AI", "href": "/robotics", "view_group": "physical_ai"},
        {"label": "Again", "href": "/robotics", "view_group": "physical_ai"},
        {"label": "Bad", "href": "https://example.com", "view_group": "physical_ai"},
        {"label": "Other", "href": "/workbench"},
    ])
    body = http.get("/api/extensions").json
    assert [e["href"] for e in body["navigation"]] == ["/physical-ai", "/workbench"]
    assert body["physical_ai_advanced"] == [{"label": "Physical AI", "href": "/robotics"}]
    page = http.get("/physical-ai").text
    assert 'href="/robotics"' in page
    assert 'href="https://example.com"' not in page
