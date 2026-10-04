"""The generic daemon RPC must not bypass a paid route's mutation gate.

These tests use the real host store/extension dispatch with a minimal test
plugin. No private implementation, installed preference or device is used.
"""
import json

import pytest
from flask import Flask


@pytest.fixture
def generic_rpc(monkeypatch):
    from clawmetry import local_server
    from routes import local_query

    monkeypatch.setattr(local_server, "_token", None)
    app = Flask("isolated-dashboard-rpc")
    app.register_blueprint(local_query.bp_local_query)
    return local_query, local_server, app.test_client()


@pytest.mark.parametrize("operation", ["set_observation_only", "guard_ack"])
@pytest.mark.parametrize("daemon_token,authorization", [
    (None, None), (None, "Bearer guessed"),
    ("private-test-token", None), ("private-test-token", "Bearer wrong"),
    ("private-test-token", "Bearer non-ascii-🔒"),
])
def test_dashboard_generic_mutation_refused_before_store(
        generic_rpc, monkeypatch, operation, daemon_token, authorization):
    query, local_server, client = generic_rpc
    monkeypatch.setattr(local_server, "_token", daemon_token)
    monkeypatch.setattr(query, "_store", lambda: pytest.fail("Unauthorized mutation reached writer"))
    headers = {"Origin": "https://untrusted.example"}
    if authorization:
        headers["Authorization"] = authorization
    response = client.post("/__local_query__/robotics_query",
        json={"kwargs": {"operation": operation, "args": {"enabled": True}}},
        headers=headers, environ_overrides={"REMOTE_ADDR": "10.0.0.2"})
    assert response.status_code == 401
    assert response.json == {"error": "unauthorized"}


@pytest.mark.parametrize("body", [[], [1], False, 0, "", "invalid", None,
    {"kwargs": []}, {"kwargs": False}, {"kwargs": 0},
    {"kwargs": {"operation": []}}, {"kwargs": {"operation": {}}}])
def test_malformed_generic_rpc_never_reaches_writer(generic_rpc, monkeypatch, body):
    query, _, client = generic_rpc
    monkeypatch.setattr(query, "_store", lambda: pytest.fail("Malformed body reached writer"))
    response = client.post("/__local_query__/robotics_query",
                           data=json.dumps(body), content_type="application/json")
    assert response.status_code == 400


@pytest.fixture
def actual_plugin_store(tmp_path, monkeypatch):
    from clawmetry import extensions, local_store
    from routes import local_query

    db_path = tmp_path / "rpc-review.duckdb"
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(db_path))
    monkeypatch.setattr(local_store, "DB_PATH", db_path)
    monkeypatch.setattr(extensions, "_registry", {})
    store = local_store.LocalStore()
    calls = []

    def handler(payload):
        assert payload["store"] is store
        calls.append((payload["operation"], payload["args"]))
        if payload["operation"] == "runs":
            return {"runs": []}
        # A harmless isolated write proves authorization preceded the real
        # LocalStore -> extension registry -> handler mutation path.
        store.set_node_setting("test.robotics.rpc", json.dumps(payload["args"]))
        return {"saved": True, "operation": payload["operation"]}

    extensions.register("robotics.query", handler)
    monkeypatch.setattr(local_query, "_store", lambda: store)
    yield store, calls
    store.stop()


@pytest.mark.parametrize("operation,args", [
    ("set_observation_only", {"enabled": True}),
    ("guard_ack", {"run_id": "a" * 32, "incident_id": "b" * 32}),
])
def test_real_daemon_bearer_dispatches_through_store_and_extension(
        actual_plugin_store, monkeypatch, operation, args):
    from clawmetry import local_server

    store, calls = actual_plugin_store
    token = "isolated-daemon-token"
    monkeypatch.setattr(local_server, "_token", token)
    client = local_server._make_app().test_client()
    path = "/__local_query__/robotics_query"
    body = {"kwargs": {"operation": operation, "args": args}}
    assert client.post(path, json=body).status_code == 401
    assert calls == [] and store.get_node_setting("test.robotics.rpc") is None
    response = client.post(path, json=body, headers={"Authorization": "Bearer " + token})
    assert response.status_code == 200
    assert response.json == {"result": {"saved": True, "operation": operation}}
    assert calls == [(operation, args)]
    assert json.loads(store.get_node_setting("test.robotics.rpc")) == args


@pytest.mark.parametrize("shape", ["robotics_query", "set_observation_only", "robotics_guard_ack"])
def test_cloud_query_contract_cannot_select_mutations(generic_rpc, monkeypatch, shape):
    from clawmetry.query_contract import QUERY_CONTRACT

    query, _, _ = generic_rpc
    assert shape not in QUERY_CONTRACT
    monkeypatch.setattr(query, "_store", lambda: pytest.fail("Cloud mutation reached writer"))
    result = query.relay_dispatch(shape, {"operation": "set_observation_only", "enabled": True})
    assert "unknown shape" in result["error"]


def test_cloud_read_shape_cannot_smuggle_mutation_arguments(actual_plugin_store, monkeypatch):
    from routes import local_query

    store, calls = actual_plugin_store
    def no_proxy(*_args, **_kwargs):
        raise FileNotFoundError("Isolated query has no external daemon")
    monkeypatch.setattr(local_query, "_proxy_dispatch", no_proxy)
    result = local_query.relay_dispatch("robotics_runs", {
        "operation": "set_observation_only", "enabled": True,
        "args": {"enabled": True}, "kwargs": {"operation": "set_observation_only"},
    })
    assert result["runs"] == []
    assert calls == [("runs", {"limit": 50, "before_ns": None, "before_run_id": None})]
    assert store.get_node_setting("test.robotics.rpc") is None
