"""Investigation HTTP uses the q/1 shape and reports failed reads honestly."""
import pytest
from flask import Flask

from tests import test_incident_lifecycle as lifecycle

server = lifecycle.server
store = lifecycle.store
from routes import investigations as route


@pytest.fixture
def client():
    app = Flask(__name__)
    app.register_blueprint(route.bp_investigations)
    return app.test_client()


def test_read_dispatch_preserves_scope_and_cursor(client, monkeypatch):
    calls = []
    def dispatch(shape, args):
        calls.append((shape, args))
        return {"rows": [], "coverage": {"node_reachable": True}}
    monkeypatch.setattr(route, "_dispatch", dispatch)
    result = client.get('/api/investigation?session_id=codex%3Aa&runtime=codex&node_id=n&cursor=c')
    assert result.status_code == 200
    assert calls == [("investigation", {"session_id": "codex:a", "runtime": "codex", "node_id": "n", "cursor": "c"})]


def test_failed_store_read_is_unavailable_not_empty_success(client, monkeypatch):
    def broken(*args, **kwargs):
        raise RuntimeError("private path must not leak")
    monkeypatch.setattr(route, "_dispatch", broken)
    result = client.get('/api/guard/incidents')
    assert result.status_code == 503
    assert result.json["available"] is False
    assert result.json["coverage"]["node_reachable"] is False
    assert b"private path" not in result.data


def test_acknowledgement_blocks_cross_site_and_non_boolean_input(client):
    url = '/api/guard/incidents/inc_' + 'a' * 32 + '/acknowledge'
    assert client.post(url, json={"acknowledged": True}, headers={"Origin": "https://other.test"}).status_code == 403
    assert client.post(url, json={"acknowledged": "false"}).status_code == 400


def test_shared_contract_is_content_scoped_and_daemon_allowlisted():
    from clawmetry.query_contract import QUERY_CONTRACT
    from routes.local_query import _DAEMON_METHODS
    for shape in ("incidents", "investigation", "error_groups", "session_catalog"):
        assert QUERY_CONTRACT[shape]["trust"] == "e2e"
        assert QUERY_CONTRACT[shape]["scope"] == "read:content"
        assert QUERY_CONTRACT[shape]["backing"] in _DAEMON_METHODS
    assert "acknowledge_incident" in _DAEMON_METHODS


def test_pending_investigation_and_activity_use_real_encrypted_daemon_contract(store, monkeypatch):
    import base64
    import json

    from clawmetry import sync
    from routes import local_query
    sent = []
    def missing(*args):
        raise FileNotFoundError('test has no daemon socket')
    monkeypatch.setattr(local_query, '_proxy_dispatch', missing)
    monkeypatch.setattr(local_query, '_store', lambda: store)
    monkeypatch.setattr(sync, '_post', lambda path, payload, token: sent.append((path, payload)))
    key = base64.urlsafe_b64encode(bytes(range(32))).decode().rstrip('=')
    scope = {"node_id": 'node-a', "runtime": 'codex', "session_id": 'codex:session'}
    store.ingest(dict(id='event', agent_type='codex', event_type='tool_result',
                      ts='2026-10-02T10:00:00Z', data={'text': 'private result'}, **{k:v for k,v in scope.items() if k != 'runtime'}))
    store._flush_now()
    requests = [{'id': str(i), 'shape': shape, 'args': scope, 'cache_key': 'opaque-' + shape}
                for i, shape in enumerate(['incidents', 'investigation', 'activity'])]
    sync._dispatch_pending_queries({"api_key": 'test-only', "encryption_key": key, "node_id": 'node-a'}, requests)
    assert len(sent) == 3
    for path, payload in sent:
        assert path == '/ingest/cache' and payload['ttl'] == 15
        assert 'private result' not in json.dumps(payload)
        decoded = sync.decrypt_payload(payload['blob'], key)
        assert decoded['_shape'] == payload['shape']
        if payload['shape'] != 'incidents':
            assert decoded['rows'][0]['id'] == 'event'
            assert decoded['scope'] == scope
        if payload['shape'] == 'activity':
            assert decoded['cursor'] and decoded['brain_events'][0]['eventId'] == 'event'


def test_sse_checkpoints_after_batch_and_releases_slot(monkeypatch):
    import sys
    from types import SimpleNamespace

    from routes import activity
    calls = []
    monkeypatch.setitem(sys.modules, 'dashboard', SimpleNamespace(
        _acquire_stream_slot=lambda key: True,
        _release_stream_slot=lambda key: calls.append(key), SSE_MAX_SECONDS=60))
    monkeypatch.setattr(activity, '_dispatch', lambda shape, args: {
        'brain_events': [{'eventId': 'a', 'time': 'now'}], 'cursor': 'committed-position'})
    app = Flask(__name__)
    app.add_url_rule('/stream', view_func=activity.brain_stream)
    with app.test_request_context('/stream'):
        response = activity.brain_stream()
        iterator = iter(response.response)
        assert next(iterator).startswith('event: connected')
        assert next(iterator).startswith('data: ')
        assert next(iterator).startswith('id: committed-position\nevent: checkpoint')
        response.close()
    assert calls == ['brain']
