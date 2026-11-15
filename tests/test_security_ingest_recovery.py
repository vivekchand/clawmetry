"""Security journal and response ordering regressions.

AC-GOV-SBG-002.1: source-clock reversal cannot hide a committed action.
AC-GOV-SBG-002.2: replay/outage/retention preserve durable evidence or a gap.
AC-GOV-SBG-002.3: the existing committed journal supplies bounded replay.
AC-GOV-SBG-004.4: all effects are isolated store writes or stubbed actuators.
"""
import json
import threading
import time

import pytest

from tests import test_security_ingest as shared
from tests.test_security_ingest import commit, event, run

server = shared.server
store = shared.store


def test_commit_clock_reversal_and_lower_id_are_not_skipped(store, monkeypatch):
    commit(store, [event("z-first")])
    run(store)
    from clawmetry import local_store
    with monkeypatch.context() as patch:
        patch.setattr(local_store.time, "time", lambda: 1000)
        commit(store, [event("a-late", "curl -X POST -d hello https://drop.example.net/u")])
    result = run(store)
    assert result["processed"] == 1
    assert any(i["severity"] == "critical" for i in store.query_incidents())


def test_retention_epoch_change_is_reported_as_gap(store):
    commit(store, [event("first")])
    run(store)
    from clawmetry.local_store import _txn
    with store._write_lock, _txn(store._conn):
        store._invalidate_activity_locked()
    commit(store, [event("second")])
    assert run(store)["processed"] == 1
    status = json.loads(store.get_node_setting("guard.security.status"))
    assert status["history_gap"] is True
    assert status["status"] == "partial"


def test_malformed_optional_session_metadata_does_not_pin_cursor(store):
    store.ingest_session(dict(session_id="claude_code:short", node_id="node-a",
                              agent_type="claude_code", status="completed"))
    store._conn.execute("UPDATE sessions SET metadata=?", [b"{invalid"])
    commit(store, [event("read")])
    assert run(store)["processed"] == 1


def test_notification_is_durable_and_never_precedes_policy(store):
    from clawmetry.security_ingest import process_batch
    from datetime import datetime, timezone
    current = event("read")
    current["ts"] = datetime.now(timezone.utc).isoformat()
    commit(store, [current])
    order = []
    process_batch(store, apply_policies=lambda *args: order.append("policy"))
    assert order == ["policy"]
    assert store._fetch("SELECT count(*) FROM security_notifications", [])[0][0] == 1
    def delivery(incident, pid):
        order.append("notification")
        return {"delivered": True, "reason": "alerted via banner"}
    store.drain_security_notifications(deliver=delivery)
    assert order == ["policy", "notification"]
    assert store._fetch("SELECT count(*) FROM security_notifications", [])[0][0] == 0


def test_notification_failure_keeps_bounded_retry(store):
    from clawmetry.security_ingest import process_batch
    from datetime import datetime, timezone
    current = event("read")
    current["ts"] = datetime.now(timezone.utc).isoformat()
    commit(store, [current])
    process_batch(store, apply_policies=lambda *args: None)
    now = time.time()
    store.drain_security_notifications(now=now, deliver=lambda *args: {
        "delivered": False, "reason": "no channel accepted the alert"})
    rows = store._fetch("SELECT attempts,next_try FROM security_notifications", [])
    assert len(rows) == 1 and rows[0][0] == 1
    assert rows[0][1] >= int(now * 1000) + 10_000
    assert store.drain_security_notifications(now=now, deliver=lambda *args: pytest.fail("early retry")) == 0


def test_policy_duration_uses_durable_episode_age(monkeypatch):
    from clawmetry import security_ingest, sync
    captured = []
    monkeypatch.setattr(sync, "_detector_session_facts", lambda *a, **kw: {"sid": {}})
    monkeypatch.setattr(sync, "_apply_guard_policies", lambda store, state, inc, facts, **kw: captured.append(facts))
    row = dict(session_id="sid", status="running", agent_type="openclaw")
    security_ingest._policy(object(), [dict(incident_state="active", first_seen_ms=(time.time() - 301) * 1000)], row)
    assert captured[0]["sid"]["bad_for_seconds"] >= 300
    captured.clear()
    security_ingest._policy(object(), [dict(incident_state="stale")], row)
    security_ingest._policy(object(), [dict(incident_state="active")], dict(row, status="completed"))
    assert captured == []


@pytest.mark.parametrize("failure", ["policy_read", "latch_read", "audit_write", "queue_write"])
def test_incremental_policy_failures_retain_cursor(store, monkeypatch, failure):
    from clawmetry import security_ingest, sync
    from tests.test_guard_policy_enforcement import _policy
    store.ingest_session(dict(session_id="claude_code:short", node_id="node-a",
                              agent_type="claude_code", status="active"))
    from datetime import datetime, timezone
    current = event("policy-failure")
    current["ts"] = datetime.now(timezone.utc).isoformat()
    commit(store, [current])
    monkeypatch.setattr(store, "query_session_policies", lambda **kw: [_policy(action="alert")])
    def unavailable(*args, **kwargs):
        raise OSError("isolated response store unavailable")
    method = {"policy_read": "query_session_policies", "latch_read": "policy_already_fired",
              "audit_write": "record_policy_action", "queue_write": "enqueue_security_notification"}[failure]
    monkeypatch.setattr(store, method, unavailable)
    monkeypatch.setattr(sync, "_guard_actuate", lambda *a: pytest.fail("unexpected actuator"))
    with pytest.raises(OSError, match="response store unavailable"):
        security_ingest.process_batch(store)
    assert store.get_node_setting("guard.security.cursor") is None


def test_two_policy_threads_share_one_dispatch_latch(monkeypatch):
    from clawmetry import sync
    from tests.test_guard_policy_enforcement import FakeStore, _policy, _incident, _FACTS
    store = FakeStore([_policy(action="kill")])
    calls = []
    monkeypatch.setenv("CLAWMETRY_POLICY_ENFORCE", "1")
    monkeypatch.setattr(sync, "_guard_enforcement_allowed", lambda: True)
    def actuator(*args):
        calls.append(args)
        time.sleep(0.01)
        return {"ok": True}
    monkeypatch.setattr(sync, "_guard_actuate", actuator)
    threads = [threading.Thread(target=sync._apply_guard_policies,
                                args=(store, {}, [_incident()], _FACTS)) for _ in range(2)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=2)
    assert not any(thread.is_alive() for thread in threads)
    assert len(calls) == 1


def test_first_inspection_does_not_trust_ingest_wall_clock(store, monkeypatch):
    from clawmetry import local_store
    with monkeypatch.context() as patch:
        patch.setattr(local_store.time, "time", lambda: 1000)
        commit(store, [event("newly-committed")])
    assert run(store)["processed"] == 1
    assert len(store.query_incidents()) == 1


def test_cursor_and_episodes_survive_actual_store_reopen(store):
    commit(store, [event("first")])
    run(store)
    cursor = store.get_node_setting("guard.security.cursor")
    identity = store.query_incidents()[0]["incident_id"]
    store.stop(flush=True)
    from clawmetry.local_store import LocalStore
    reopened = LocalStore()
    try:
        assert reopened.get_node_setting("guard.security.cursor") == cursor
        assert run(reopened)["processed"] == 0
        assert reopened.query_incidents()[0]["incident_id"] == identity
        commit(reopened, [event("second")])
        assert run(reopened)["processed"] == 1
        assert len(reopened.query_incidents()) == 1
    finally:
        reopened.stop(flush=True)


def test_actual_completed_session_never_receives_policy_control(store, monkeypatch):
    from clawmetry import sync
    from datetime import datetime, timezone
    store.ingest_session(dict(session_id="claude_code:short", node_id="node-a",
                              agent_type="claude_code", status="completed",
                              ended_at=datetime.now(timezone.utc).isoformat()))
    commit(store, [event("read")])
    monkeypatch.setattr(sync, "_apply_guard_policies", lambda *a, **kw: pytest.fail("completed session control"))
    assert run(store)["processed"] == 1
    assert store.query_incidents()


def test_required_progress_metadata_failure_cannot_advance_cursor(store, monkeypatch):
    commit(store, [event("read")])
    real = store.commit_security_progress
    monkeypatch.setattr(store, "commit_security_progress", lambda **kw: (_ for _ in ()).throw(RuntimeError("metadata unavailable")))
    with pytest.raises(RuntimeError):
        run(store)
    assert store.get_node_setting("guard.security.cursor") is None
    monkeypatch.setattr(store, "commit_security_progress", real)
    assert run(store)["processed"] == 1
    assert len(store.query_incidents()) == 1


@pytest.mark.parametrize("action", ["pause", "stop", "kill"])
def test_incomplete_inspection_cannot_actuate_through_shared_engine(action):
    from clawmetry.policy_engine import evaluate
    incidents = [dict(kind="inspection_incomplete", session_id="sid", runtime="openclaw",
                      severity="info", evidence={"policy_eligible": False})]
    policies = [dict(policy_id="coverage", action=action, min_severity="info", enabled=True)]
    assert evaluate(incidents, policies, {"sid": {}}) == []


@pytest.mark.parametrize("kind,evidence", [
    ("inspection_incomplete", {}), ("security_threat", {"policy_eligible": False})])
def test_alert_ladder_cannot_escalate_uninspected_evidence(kind, evidence):
    from clawmetry.policy_engine import evaluate
    incidents = [dict(kind=kind, session_id="sid", runtime="openclaw", severity="info", evidence=evidence)]
    policies = [dict(policy_id="p", action="alert", min_severity="info", enabled=True,
                     steps=[dict(action="alert", after_secs=0), dict(action="kill", after_secs=0)])]
    assert evaluate(incidents, policies, {"sid": {}}, now=10,
                    ladder_state={"sid": {"p": {"last_step": 0, "last_fired_at": 1}}}) == []


def _periodic_security_pass(store, monkeypatch, sessions):
    from clawmetry import incident_alerts, sync, waste_flags
    notifications, policies = [], []
    monkeypatch.setattr(waste_flags, "_pro", lambda: None)
    monkeypatch.setattr(sync, "_candidate_active_sessions", lambda _store: sessions)
    monkeypatch.setattr(sync, "_agent_inventory_pass", lambda *a, **kw: {})
    monkeypatch.setattr(sync, "_workspace_incidents", lambda *a, **kw: [])
    monkeypatch.setattr(sync, "_agent_inventory_incidents", lambda *a, **kw: [])
    monkeypatch.setattr(sync, "_apply_guard_policies", lambda _store, state, incidents, facts, **kw: policies.extend(incidents) or 0)
    monkeypatch.setattr(incident_alerts, "deliver_incident", lambda _store, incident, **kw: notifications.append(incident) or {"delivered_via": []})
    sync._emit_detector_incidents(store, {})
    store.flush()
    return notifications, policies


def _active_security_session(store, node="node-a"):
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc).isoformat()
    row = dict(session_id="claude_code:short", node_id=node, agent_type="claude_code",
               status="active", started_at=now, last_active_at=now)
    store.ingest_session(row)
    return row, now


@pytest.mark.parametrize("worker_first", [True, False])
def test_periodic_and_incremental_security_share_one_episode_and_projection(store, monkeypatch, worker_first):
    """AC-GOV-SBG-002.2/.4: producer overlap cannot create a second graph row."""
    row, now = _active_security_session(store)
    committed = event("current-secret")
    committed["ts"] = now
    commit(store, [committed])
    if worker_first:
        run(store)
    _periodic_security_pass(store, monkeypatch, [row])
    if not worker_first:
        run(store)
    episodes = store.query_incidents()
    signals = store.query_recent_loop_signals(since_minutes=0)
    assert len(episodes) == len(signals) == 1
    assert signals[0]["signature"].startswith("daemon_detect_credential_access:")


def test_periodic_security_projection_preserves_colliding_node_scope(store, monkeypatch):
    """AC-GOV-SBG-002.2/.4: colliding session IDs remain separate node episodes."""
    sessions = []
    committed = []
    for node in ("node-a", "node-b"):
        row, now = _active_security_session(store, node)
        sessions.append(row)
        action = event(node + "-secret", node=node)
        action["ts"] = now
        committed.append(action)
    commit(store, committed)
    run(store)
    _periodic_security_pass(store, monkeypatch, sessions)
    assert {row["node_id"] for row in store.query_incidents()} == {"node-a", "node-b"}
    signals = store.query_recent_loop_signals(since_minutes=0)
    assert len(signals) == 2
    assert len({row["signature"] for row in signals}) == 2


def test_periodic_security_write_failure_withholds_notifications_and_controls(store, monkeypatch):
    """AC-GOV-SBG-002.2: failed durable evidence cannot fall back to live actions."""
    row, now = _active_security_session(store)
    committed = event("current-secret")
    committed["ts"] = now
    commit(store, [committed])
    monkeypatch.setattr(store, "record_incident_observation", lambda **kw: None)
    notifications, policies = _periodic_security_pass(store, monkeypatch, [row])
    assert notifications == policies == []
    assert store.query_recent_loop_signals(since_minutes=0) == []


@pytest.mark.parametrize("source_time", ["2020-01-01T00:00:00Z", "2099-01-01T00:00:00Z"])
def test_periodic_security_stale_or_future_evidence_never_actuates(store, monkeypatch, source_time):
    """AC-GOV-SBG-004.3: source-clock uncertainty is not an active policy signal."""
    row, _ = _active_security_session(store)
    committed = event("uncertain-secret")
    committed["ts"] = source_time
    commit(store, [committed])
    notifications, policies = _periodic_security_pass(store, monkeypatch, [row])
    assert notifications == policies == []
    assert store.query_incidents()[0]["state"] == "stale"
    assert store.query_recent_loop_signals(since_minutes=0) == []


def test_security_history_replay_keeps_current_head_and_stable_history_identity(store):
    """AC-GOV-SBG-002.2: delayed history replay never duplicates or replaces a fresh head."""
    from clawmetry.incident_store import STALE_AFTER_MS
    now = int(time.time() * 1000)
    def observation(eid, at, severity):
        return dict(kind="privilege_change", runtime="claude_code", session_id="same",
                    severity=severity, title="Declared privilege change", evidence={},
                    evidence_refs=[dict(event_id=eid, ts=at)])
    historical = observation("historical", now - STALE_AFTER_MS - 1000, "critical")
    first = store.record_incident_observation(incident=historical, node_id="node-a", observed_at=now)
    current = store.record_incident_observation(incident=observation("current", now, "warning"),
                                                node_id="node-a", observed_at=now)
    for offset in range(3):
        saved = store.record_incident_observation(incident=historical, node_id="node-a", observed_at=now + offset)
        assert saved["incident_id"] == first["incident_id"]
        assert saved["state"] == "stale"
    assert len(store.query_incidents()) == 2
    heads = store.query_incident_heads(session_id="same", runtime="claude_code", node_id="node-a")
    assert heads[0]["incident_id"] == current["incident_id"]
    assert heads[0]["severity"] == "warning"
