"""Node-wide storage and sealed relay integration.

AC-GOV-NODE-003.3: host detail stays in the encrypted snapshot.
AC-OBS-NODE-006.1: request reads use daemon observations.
AC-OBS-NODE-006.2: hosted fallback cannot collect the cloud host.
AC-OBS-NODE-006.4: the view stays explicitly node-wide.
"""
from pathlib import Path
import json
import logging
import time

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="session", autouse=True)
def server():
    """These integration tests need no gateway or network server."""
    yield


@pytest.fixture(autouse=True)
def isolated_sync_environment(monkeypatch, tmp_path):
    """Importing sync must not send test warnings to the live daemon log."""
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("CLAWMETRY_AUDIT_DB", str(tmp_path / "audit.db"))
    monkeypatch.setattr(logging.getLogger("clawmetry-sync"), "handlers", [logging.NullHandler()])


@pytest.fixture
def relay(monkeypatch, tmp_path):
    from clawmetry import sync, local_store
    monkeypatch.setenv("CLAWMETRY_AUDIT_DB", str(tmp_path / "relay-audit.db"))

    class Store:
        def __init__(self):
            self.settings = {}
            self.preferences = {"enabled": True}
            self.reviews = []
        def _fetch(self, sql, params):
            return [(self.settings[params[0]],)] if params[0] in self.settings else []
        def set_node_setting(self, key, value):
            self.settings[key] = value
        def set_node_activity_preferences(self, preferences):
            if not isinstance(preferences, dict) or any(k != "enabled" or type(v) is not bool for k, v in preferences.items()):
                raise ValueError("invalid preferences")
            self.preferences.update(preferences)
            return {"ok": True, "saved": True, "preferences": dict(self.preferences)}
        def review_node_activity_event(self, event_id, decision, reason=""):
            if event_id != "observed-event" or decision not in {"expected", "investigate"}:
                raise ValueError("invalid review")
            self.reviews.append((event_id, decision, reason))
            return {"ok": True, "saved": True, "review": {"decision": decision, "reason": reason}}
        def query_node_activity(self):
            events = [{"id": e, "review": {"decision": d, "reason": r}} for e, d, r in self.reviews]
            return {"preferences": dict(self.preferences), "events": events}
    store = Store()
    results = []
    monkeypatch.setattr(local_store, "get_store", lambda *a, **k: store)
    monkeypatch.setattr(sync, "_post_process_control_result", lambda c, a, r: results.append(r))
    config = {"encryption_key": sync.generate_encryption_key(), "node_id": "node-one"}
    def send(body, drop_preferences=False, **overrides):
        request = {"operation": "preferences", "preferences": {"enabled": False},
                   "node_id": "node-one", "request_id": "a" * 32, "sent_at": time.time()}
        request.update(body)
        if drop_preferences:
            request.pop("preferences", None)
        action = {"type": "node_activity_update", "sealed": sync.encrypt_payload(request, config["encryption_key"])}
        action.update(overrides)
        sync._dispatch_pending_action(config, action)
        return results[-1]
    return store, send, sync


def test_sealed_update_confirms_persisted_readback_and_binding(relay):
    # AC-GOV-NODE-004.1, AC-GOV-NODE-004.3
    store, send, _ = relay
    result = send({})
    assert result["ok"] and result["saved"] and result["applied"]
    assert result["node_id"] == "node-one" and result["request_id"] == "a" * 32
    assert result["data"]["preferences"]["enabled"] is False
    assert store.preferences["enabled"] is False
    assert send({}) is result  # Duplicate leaves the original result intact.


@pytest.mark.parametrize("body", [
    {"node_id": "node-two"}, {"request_id": "invalid"},
    {"sent_at": time.time() - 1000}, {"sent_at": True},
    {"preferences": {"enabled": "false"}}, {"operation": "kill"},
    {"unexpected": "field"},
])
def test_invalid_or_cross_node_request_cannot_mutate(relay, body):
    store, send, _ = relay
    assert send(body)["applied"] is False
    assert store.preferences["enabled"] is True


def test_invalid_seal_cannot_mutate(relay):
    store, send, _ = relay
    assert send({}, sealed="invalid")["applied"] is False
    assert store.preferences["enabled"] is True


def test_review_requires_existing_event_and_valid_decision(relay):
    # AC-GOV-NODE-004.2: review is historical and preserves evidence.
    store, send, _ = relay
    body = {"operation": "review", "event_id": "observed-event", "decision": "expected", "reason": "My change"}
    # Preference field is not legal on review requests.
    assert send(body)["applied"] is False
    assert store.reviews == []
    result = send(body, drop_preferences=True)
    assert result["applied"] and result["saved"]
    assert store.reviews == [("observed-event", "expected", "My change")]


def test_snapshot_uses_store_and_declares_remote_capability(relay):
    _, _, sync = relay
    data = sync._build_node_activity_snapshot()
    assert data["capabilities"]["remote_mutations"] is True
    source = (ROOT / "clawmetry/sync.py").read_text()
    assert '"nodeActivity": _build_node_activity_snapshot()' in source
    # Collection precedes snapshot and its local-only early return.
    loop = source[source.index("    while True:", source.index("last_git_scan = 0.0")):]
    assert loop.index("tick_node_activity(") < loop.index("sync_system_snapshot(")


def test_tab_is_live_node_wide_and_routes_registered():
    app = (ROOT / "clawmetry/static/js/app.js").read_text()
    dashboard = (ROOT / "dashboard.py").read_text()
    assert "'node-activity': 1" in app
    assert "var _CM_NODE_TABS = ['node-activity'" in app
    assert "loadNodeActivity();" in app and "nodeActivityStop();" in app
    assert "{% include 'tabs/node-activity.html' %}" in dashboard
    assert "app.register_blueprint(bp_node_activity)" in dashboard


def test_replay_ledger_never_evicts_valid_nonces(relay):
    store, send, _ = relay
    store.settings["node_activity.request_ids"] = json.dumps({format(i, "032x"): time.time() for i in range(512)})
    assert send({})["applied"] is False
    assert len(json.loads(store.settings["node_activity.request_ids"])) == 512
    assert store.preferences["enabled"] is True


def test_replay_ledger_read_failure_fails_closed(relay):
    store, send, _ = relay
    def broken(*args):
        raise RuntimeError("store unavailable")
    store._fetch = broken
    assert send({})["applied"] is False
    assert store.preferences["enabled"] is True


def test_review_not_in_readback_cannot_claim_confirmed(relay):
    store, send, _ = relay
    store.query_node_activity = lambda: {"preferences": store.preferences, "events": []}
    result = send({"operation": "review", "event_id": "observed-event", "decision": "expected"}, drop_preferences=True)
    assert result["applied"] is False


@pytest.mark.parametrize("method", ["query_node_activity", "set_node_activity_preferences", "review_node_activity_event"])
def test_internal_node_method_requires_daemon_token_on_public_app(relay, monkeypatch, method):
    from flask import Flask
    from clawmetry import local_server
    from routes.local_query import bp_local_query
    store, _, _ = relay
    monkeypatch.setattr(local_server, "_token", None)
    app = Flask(__name__)
    app.register_blueprint(bp_local_query)
    response = app.test_client().post('/__local_query__/' + method,
                                      json={"kwargs": {"preferences": {"enabled": False}}})
    assert response.status_code == 401
    assert store.preferences["enabled"] is True


def test_authenticated_daemon_rpc_persists_typed_choice(relay, monkeypatch):
    from clawmetry import local_server
    store, _, _ = relay
    monkeypatch.setattr(local_server, "_token", "isolated-unit-token")
    app = local_server._make_app()
    response = app.test_client().post('/__local_query__/set_node_activity_preferences',
            headers={"Authorization": "Bearer isolated-unit-token"},
            json={"kwargs": {"preferences": {"enabled": False}}})
    assert response.status_code == 200
    assert response.json["result"]["saved"] is True
    assert store.preferences["enabled"] is False


@pytest.fixture
def real_relay(monkeypatch, tmp_path):
    """Real DuckDB methods, with no production paths, host scans or HTTP posts."""
    from types import SimpleNamespace
    from clawmetry import local_store, sync
    from clawmetry.node_activity import DEFAULT_PREFERENCES
    path = tmp_path / "real-relay.duckdb"
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(path))
    monkeypatch.setenv("CLAWMETRY_AUDIT_DB", str(tmp_path / "audit.db"))
    monkeypatch.setattr(local_store, "DB_PATH", path)
    monkeypatch.setattr(local_store, "LEGACY_DB_PATH", tmp_path / "legacy.duckdb")
    monkeypatch.setattr(local_store, "AUTO_COMPACT_ENABLED", False)
    stores = [local_store.LocalStore()]
    clock = [time.time()]
    monkeypatch.setattr(sync.time, "time", lambda: clock[0])
    results = []
    monkeypatch.setattr(local_store, "get_store", lambda *a, **k: stores[0])
    monkeypatch.setattr(sync, "_post_process_control_result", lambda c, a, r: results.append(r))
    config = {"encryption_key": sync.generate_encryption_key(), "node_id": "node-one"}
    def request(**overrides):
        body = {"operation": "preferences", "preferences": dict(DEFAULT_PREFERENCES),
                "node_id": "node-one", "request_id": "a" * 32, "sent_at": clock[0]}
        body.update(overrides)
        return body
    def deliver(body):
        action = {"type": "node_activity_update", "id": "isolated-action", "cache_key": "isolated-cache",
                  "sealed": sync.encrypt_payload(body, config["encryption_key"])}
        sync._action_node_activity(config, action)
    def reopen():
        stores[0]._conn.close()
        stores[0] = local_store.LocalStore()
    harness = SimpleNamespace(stores=stores, clock=clock, results=results, request=request,
                              deliver=deliver, reopen=reopen, sync=sync)
    yield harness
    stores[0]._conn.close()


def test_real_store_duplicate_preserves_original_confirmation(real_relay):
    """
    AC-GOV-NODE-ACK-001.1: one claimant executes a duplicated hosted action.
    AC-GOV-NODE-ACK-001.2: duplicates do not replace the claimant's acknowledgement.
    """
    h = real_relay
    body = h.request()
    h.deliver(body)
    assert len(h.results) == 1 and h.results[0]["applied"] is True
    original = json.dumps(h.results[0], sort_keys=True)
    h.deliver(body)
    assert len(h.results) == 1
    assert json.dumps(h.results[0], sort_keys=True) == original
    assert len(json.loads(h.stores[0].get_node_setting("node_activity.request_ids"))) == 1
    assert all(h.stores[0].query_node_activity()["preferences"].values())


def test_real_store_changed_body_and_expired_duplicate_do_not_post(real_relay):
    """
    AC-GOV-NODE-ACK-001.3: retained duplicate claims take priority over expiry errors.
    """
    h = real_relay
    body = h.request(preferences={"enabled": False})
    h.deliver(body)
    assert h.results[0]["applied"] is True
    # A reused nonce never applies a different choice or manufactures another result.
    h.deliver(dict(body, preferences={"enabled": True}))
    h.deliver(dict(body, operation="unsupported", unexpected="field"))
    h.clock[0] += 301
    h.deliver(body)
    assert len(h.results) == 1
    assert h.stores[0].query_node_activity()["preferences"]["enabled"] is False
    # Fresh nonce still requires ordinary envelope validation.
    h.deliver(dict(body, request_id="b" * 32))
    assert len(h.results) == 2 and h.results[-1]["applied"] is False
    assert len(json.loads(h.stores[0].get_node_setting("node_activity.request_ids"))) == 1


def test_real_store_duplicate_after_reopen_does_not_repeat_mutation(real_relay):
    h = real_relay
    body = h.request(preferences={"enabled": False})
    h.deliver(body)
    h.reopen()
    h.deliver(body)
    assert len(h.results) == 1 and h.results[0]["applied"] is True
    events = h.stores[0].query_node_activity()["events"]
    assert len(events) == 1 and events[0]["kind"] == "monitoring_preferences_changed"


def test_real_store_original_failure_and_incomplete_claim_stay_unconfirmed(real_relay, monkeypatch):
    """
    AC-GOV-NODE-ACK-001.4: claimed failures cannot be retried or confirmed by duplicates.
    """
    h = real_relay
    body = h.request(preferences={"enabled": False})
    with monkeypatch.context() as patch:
        def fail_apply(*args, **kwargs):
            raise RuntimeError("isolated apply failure")
        patch.setattr(h.stores[0], "set_node_activity_preferences", fail_apply)
        h.deliver(body)
    assert len(h.results) == 1 and h.results[0]["applied"] is False
    h.deliver(body)
    assert len(h.results) == 1 and h.stores[0].query_node_activity()["preferences"]["enabled"] is True
    # Simulate a persisted claim followed by a crash before mutation or acknowledgement.
    ledger = json.loads(h.stores[0].get_node_setting("node_activity.request_ids"))
    ledger["b" * 32] = h.clock[0]
    h.stores[0].set_node_setting("node_activity.request_ids", json.dumps(ledger))
    h.deliver(h.request(request_id="b" * 32, preferences={"enabled": False}))
    assert len(h.results) == 1 and h.stores[0].query_node_activity()["preferences"]["enabled"] is True
    h.deliver(h.request(request_id="c" * 32, preferences={"enabled": False}))
    assert len(h.results) == 2 and h.results[-1]["applied"] is True
    assert h.stores[0].query_node_activity()["preferences"]["enabled"] is False


def test_real_store_lost_publication_cannot_be_replaced_by_duplicate(real_relay, monkeypatch):
    h = real_relay
    body = h.request(preferences={"enabled": False})
    with monkeypatch.context() as patch:
        def lose_result(*args, **kwargs):
            raise RuntimeError("isolated publication failure")
        patch.setattr(h.sync, "_post_process_control_result", lose_result)
        with pytest.raises(RuntimeError, match="isolated publication failure"):
            h.deliver(body)
    h.deliver(body)
    assert h.results == []
    assert h.stores[0].query_node_activity()["preferences"]["enabled"] is False


def test_real_store_concurrent_duplicate_claims_apply_and_ack_once(real_relay):
    from concurrent.futures import ThreadPoolExecutor
    import threading
    h = real_relay
    body = h.request(preferences={"enabled": False})
    start = threading.Barrier(2)
    def deliver():
        start.wait(timeout=5)
        h.deliver(body)
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(deliver) for _ in range(2)]
        for future in futures:
            future.result(timeout=10)
    assert len(h.results) == 1 and h.results[0]["applied"] is True
    assert len(h.stores[0].query_node_activity()["events"]) == 1


def test_real_store_review_duplicate_keeps_one_persisted_review(real_relay):
    h = real_relay
    h.stores[0].set_node_activity_preferences({"enabled": False})
    event_id = h.stores[0].query_node_activity()["events"][0]["id"]
    body = h.request(operation="review", event_id=event_id, decision="expected", reason="Isolated review")
    body.pop("preferences")
    h.deliver(body)
    original = h.stores[0].query_node_activity()["events"][0]["review"]
    h.deliver(body)
    assert len(h.results) == 1 and h.results[0]["applied"] is True
    assert h.stores[0].query_node_activity()["events"][0]["review"] == original
    assert h.stores[0]._fetch("SELECT COUNT(*) FROM node_activity_reviews", [])[0][0] == 1


def test_real_store_claim_retention_does_not_weaken_unclaimed_expiry(real_relay):
    h = real_relay
    body = h.request(preferences={"enabled": False})
    h.deliver(body)
    # The guarantee is bounded by retained claims, not perpetual nonce storage.
    h.clock[0] += 601
    h.deliver(body)
    assert len(h.results) == 2 and h.results[-1]["applied"] is False
    assert h.stores[0].query_node_activity()["preferences"]["enabled"] is False
    h.deliver(h.request(request_id="b" * 32, preferences={"enabled": True}))
    assert len(h.results) == 3 and h.results[-1]["applied"] is True
    assert set(json.loads(h.stores[0].get_node_setting("node_activity.request_ids"))) == {"b" * 32}
