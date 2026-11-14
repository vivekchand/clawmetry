"""The free Asimov HTTP surface reads bounded persisted evidence only.

AC-ASIMOV-001.1 AC-ASIMOV-005.3 AC-ASIMOV-006.1
"""
from pathlib import Path
from types import SimpleNamespace

import pytest
from flask import Flask

from routes import asimov


@pytest.fixture(scope="session", autouse=True)
def server():
    """Route tests use an isolated Flask client, without a live dashboard."""
    yield None


@pytest.fixture
def client(monkeypatch):
    root = Path(__file__).resolve().parents[1] / "clawmetry"
    app = Flask(__name__, template_folder=str(root / "templates"), static_folder=str(root / "static"))
    app.register_blueprint(asimov.bp_asimov)
    calls = []

    def call(method, **kwargs):
        calls.append((method, kwargs))
        if method == "query_asimov_runs":
            return {"runs": [{"run_id": "a" * 32, "robot_id": "test"}], "has_more": False}
        return {"events": [{"sequence": 1, "kind": "command.returned", "data": {"outcome": "unknown"}}], "has_more": False, "next_after": 1}

    monkeypatch.setattr(asimov, "_call", call)
    return app.test_client(), calls


def test_free_runs_use_persisted_bounded_query(client):
    http, calls = client
    response = http.get("/api/asimov/runs?robot_id=my-robot&limit=7&before_ns=123&before_run_id=" + "b" * 32)
    assert response.status_code == 200
    assert response.json["runs"][0]["robot_id"] == "test"
    assert calls == [("query_asimov_runs", {"robot_id": "my-robot", "limit": 7, "before_ns": 123, "before_run_id": "b" * 32})]


@pytest.mark.parametrize("query", ["limit=0", "limit=101", "limit=-1", "limit=3.0", "limit=nan", "limit=99999999999999999999999", "robot_id=", "robot_id=" + "a" * 201, "robot_id=%00", "before_ns=3", "before_run_id=" + "a" * 32, "before_ns=1&before_run_id=not-a-run", "before_ns=9223372036854775808&before_run_id=" + "a" * 32, "unknown=yes"])
def test_invalid_run_filters_do_not_reach_store(client, query):
    http, calls = client
    assert http.get("/api/asimov/runs?" + query).status_code == 400
    assert calls == []


def test_event_cursor_preserves_command_evidence(client):
    http, calls = client
    response = http.get("/api/asimov/runs/" + "a" * 32 + "/events?after=4&limit=12")
    assert response.status_code == 200
    assert response.json["events"][0]["data"]["outcome"] == "unknown"
    assert calls[0] == ("query_asimov_events", {"run_id": "a" * 32, "after": 4, "limit": 12})


@pytest.mark.parametrize("suffix", ["bad/events", "A" * 32 + "/events", "a" * 32 + "/events?after=-1", "a" * 32 + "/events?limit=501", "a" * 32 + "/events?other=1"])
def test_bad_event_queries_do_not_reach_store(client, suffix):
    http, calls = client
    assert http.get("/api/asimov/runs/" + suffix).status_code == 400
    assert not calls


@pytest.mark.parametrize("endpoint", ["/api/asimov/runs", "/api/asimov/runs/" + "a" * 32 + "/events"])
def test_collector_failure_has_useful_503_without_raw_exception(client, monkeypatch, endpoint):
    http, _ = client

    def fail(*args, **kwargs):
        raise RuntimeError("credential SECRET and private path")

    monkeypatch.setattr(asimov, "_call", fail)
    response = http.get(endpoint)
    assert response.status_code == 503
    assert response.json["available"] is False
    assert "sync daemon" in response.json["message"]
    assert "SECRET" not in response.text


def test_public_read_helper_requests_read_only_store(monkeypatch):
    """The handler uses the public read-only store query boundary.

    AC-ASIMOV-005.3
    """
    from clawmetry import local_store
    calls = []

    def store(**kwargs):
        calls.append(kwargs)
        return SimpleNamespace(query_asimov_runs=lambda **args: args)

    monkeypatch.setattr(local_store, "get_store", store)
    assert asimov._call("query_asimov_runs", limit=2) == {"limit": 2}
    assert calls == [{"read_only": True}]


def test_page_states_observation_limits_and_actionable_import(client):
    """The rendered page states that physical qualification is pending.

    AC-ASIMOV-006.1
    """
    http, calls = client
    response = http.get("/asimov")
    assert response.status_code == 200
    assert "Hardware qualification is pending" in response.text
    assert "--robot-id my-asimov" in response.text
    assert "Position (rad)" in response.text
    assert "Temperature (°C)" in response.text
    assert "Source and receipt clocks" in response.text
    assert "does not confirm movement" in response.text
    assert not calls
