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


def test_builtin_navigation_preserves_installed_workbench_and_explicit_history(client, monkeypatch):
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
    assert [e["href"] for e in body["navigation"]] == ["/robotics", "/workbench"]
    assert body["physical_ai_advanced"] == [{"label": "Physical AI", "href": "/robotics"}]
    assert http.get("/physical-ai").status_code == 302
    assert http.get("/physical-ai").headers["Location"] == "/robotics"
    page = http.get("/physical-ai?hardware=jumper").text
    assert 'href="/robotics"' in page
    assert "More installed tools" not in page
    assert 'href="https://example.com"' not in page


def test_recorded_history_uses_dark_dashboard_and_hardware_picker(client):
    http, _ = client
    page = http.get('/physical-ai?hardware=jumper').text
    assert 'data-theme="dark"' in page
    assert 'name="color-scheme" content="dark"' in page
    assert 'id="physical-ai-hardware"' in page and 'aria-label="Hardware"' in page
    assert 'value="jumper" selected' in page
    assert 'value="asimov_1"' in page


def test_supported_hardware_metadata_survives_plugin_failure(client, monkeypatch):
    from routes.extensions import bp_extensions
    from clawmetry import extensions
    http, _ = client
    http.application.register_blueprint(bp_extensions)
    monkeypatch.setattr(extensions, 'loaded_plugins', lambda: (_ for _ in ()).throw(RuntimeError('unavailable')))
    body = http.get('/api/extensions').json
    assert body['physical_ai_hardware'] == [
        {'id': 'jumper', 'label': 'Jumper', 'href': '/physical-ai?hardware=jumper'},
        {'id': 'asimov_1', 'label': 'Asimov 1', 'href': '/physical-ai?hardware=asimov_1'},
    ]


def test_unknown_hardware_is_rejected_without_reflecting_input(client):
    http, calls = client
    response = http.get('/physical-ai?hardware=%3Cscript%3E')
    assert response.status_code == 400
    assert '<script>' not in response.text
    assert not calls


def test_node_ui_metadata_uses_declared_entitled_plugin_navigation(monkeypatch):
    from clawmetry import extensions
    from clawmetry.physical_ai.catalog import snapshot_metadata
    calls = []
    def declared(event, payload, **kwargs):
        calls.append((event, payload))
        return {"navigation": [{"label": "Physical AI", "href": "/robotics", "view_group": "physical_ai"}, {"href": "/other", "private_data": "never copy this"}],
                "private_data": "never copy this"}
    monkeypatch.setattr(extensions, 'call', declared)
    metadata = snapshot_metadata()
    assert metadata['navigation'][0]['href'] == '/robotics'
    assert calls == [('ui.snapshot', {})]
    assert 'private_data' not in str(metadata)
    assert len(metadata['navigation']) == 1
    assert len(metadata['physical_ai_hardware']) == 2


@pytest.mark.parametrize('declared', [None, [], {'navigation': [{'href': '//evil.example', 'view_group': 'physical_ai'}]}])
def test_node_ui_metadata_has_safe_old_plugin_fallback(monkeypatch, declared):
    from clawmetry import extensions
    from clawmetry.physical_ai.catalog import snapshot_metadata
    monkeypatch.setattr(extensions, 'call', lambda *_a, **_kw: declared)
    assert snapshot_metadata()['navigation'][0]['href'] == '/physical-ai'
