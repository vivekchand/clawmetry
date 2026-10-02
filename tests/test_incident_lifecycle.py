"""Incident identity, recurrence and missing evidence on a real isolated DuckDB.

AC-OBS-INV-001.1: identity and first evidence survive observations and restart.
AC-OBS-INV-001.2: positive later evidence closes one episode before recurrence.
AC-OBS-INV-001.3: absent evidence cannot establish recovery.
AC-OBS-INV-001.4: acknowledgement does not change incident state or policy latches.
"""
from __future__ import annotations

import importlib

import pytest

NOW = 1_790_900_000_000


@pytest.fixture(scope="session", autouse=True)
def server():
    """Pure store contracts: do not start or contact the operator's dashboard."""
    yield None


@pytest.fixture
def store(tmp_path, monkeypatch):
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "incidents.duckdb"))
    from clawmetry import local_store
    importlib.reload(local_store)
    instance = local_store.LocalStore()
    yield instance
    instance.stop(flush=True)


def finding(event="bad-1", at=NOW, **kwargs):
    row = {
        "session_id": "codex:session", "runtime": "codex",
        "kind": "repeated_tool_failure", "severity": "warning",
        "title": "Bash failed 3 times", "detail": "The same tool failed repeatedly.",
        "evidence": {"tool": "Bash", "failures": 3, "threshold": 3},
        "evidence_refs": [{"event_id": event, "ts": at,
                           "tool_call_id": "call-1"}],
        "spend_at_risk_usd": 0.0, "spend_basis": "unknown",
    }
    row.update(kwargs)
    return row


def observe(store, row=None, now=NOW, node="node-a"):
    return store.record_incident_observation(
        incident=row or finding(), node_id=node, observed_at=now)


def test_identity_evidence_and_severity_survive_new_window_and_restart(store):
    first = observe(store)
    changed = observe(store, finding("bad-2", NOW + 1000, severity="critical"), NOW + 1000)
    assert changed["incident_id"] == first["incident_id"]
    assert changed["first_seen"] == NOW
    assert changed["last_seen"] == NOW + 1000
    assert changed["severity"] == "critical"
    assert [r["event_id"] for r in changed["evidence_refs"]] == ["bad-1", "bad-2"]
    store.stop(flush=True)
    from clawmetry.local_store import LocalStore
    reopened = LocalStore()
    try:
        again = observe(reopened, finding("bad-2", NOW + 1000), NOW + 2000)
        assert again["incident_id"] == first["incident_id"]
        assert again["first_seen"] == NOW
        assert len(reopened.query_incidents()) == 1
    finally:
        reopened.stop(flush=True)


def test_recovery_and_recurrence_keep_separate_episodes(store):
    first = observe(store)
    recovered = store.recover_incident(
        incident_id=first["incident_id"],
        recovery_ref={"event_id": "success", "ts": NOW + 1000,
                      "reason": "tool_succeeded"}, observed_at=NOW + 2000)
    assert recovered["state"] == "recovered"
    assert recovered["recovery_ref"]["event_id"] == "success"
    # A restarted pass looking at the old window cannot resurrect old trouble.
    assert observe(store, now=NOW + 3000)["incident_id"] == first["incident_id"]
    recurrence = observe(store, finding("new-failure", NOW + 4000), NOW + 4000)
    assert recurrence["incident_id"] != first["incident_id"]
    assert recurrence["state"] == "active"
    rows = store.query_incidents(session_id="codex:session", runtime="codex")
    assert len(rows) == 2
    assert {r["state"] for r in rows} == {"active", "recovered"}


@pytest.mark.parametrize("proof", [None, {}, {"event_id": "old", "ts": NOW - 1,
                                          "reason": "tool_succeeded"},
                                  {"event_id": "missing", "ts": NOW + 1},
                                  {"event_id": "same", "ts": NOW,
                                   "reason": "tool_succeeded"}])
def test_empty_or_older_evidence_never_recovers(store, proof):
    first = observe(store)
    store.recover_incident(incident_id=first["incident_id"], recovery_ref=proof,
                          observed_at=NOW + 1000)
    row = store.query_incidents(incident_id=first["incident_id"])[0]
    assert row["state"] == "active"
    assert row["recovered_at"] is None


def test_stale_is_not_recovered_and_same_old_evidence_does_not_revive(store):
    first = observe(store)
    store.age_incidents(observed_at=NOW + 2_000_000)
    stale = store.query_incidents(incident_id=first["incident_id"])[0]
    assert stale["state"] == "stale"
    assert stale["recovered_at"] is None
    replay = observe(store, now=NOW + 2_000_001)
    assert replay["state"] == "stale"
    assert replay["incident_id"] == first["incident_id"]


def test_scope_is_exact_before_limit_and_id_lookup(store):
    a = observe(store)
    b = observe(store, node="node-b")
    c = observe(store, finding(runtime="openclaw"))
    assert len({r["incident_id"] for r in [a, b, c]}) == 3
    rows = store.query_incidents(runtime="codex", node_id="node-a", limit=1)
    assert [r["incident_id"] for r in rows] == [a["incident_id"]]
    assert store.query_incidents(incident_id=a["incident_id"], runtime="openclaw") == []
    assert store.query_incidents(session_id="session") == []


def test_acknowledgement_is_independent_and_reversible(store):
    first = observe(store)
    acked = store.acknowledge_incident(incident_id=first["incident_id"],
                                     acknowledged=True, observed_at=NOW + 1)
    assert acked["acknowledged_at"] == NOW + 1
    assert acked["state"] == "active"
    assert acked["recovered_at"] is None
    cleared = store.acknowledge_incident(incident_id=first["incident_id"],
                                       acknowledged=False, observed_at=NOW + 2)
    assert cleared["acknowledged_at"] is None
    assert cleared["state"] == "active"


def test_legacy_projection_carries_identity_and_clears_on_recovery(store):
    first = observe(store)
    signals = store.query_recent_loop_signals(since_minutes=0)
    assert signals[0]["details"]["incident_id"] == first["incident_id"]
    assert signals[0]["details"]["evidence_refs"][0]["event_id"] == "bad-1"
    store.recover_incident(incident_id=first["incident_id"], recovery_ref={
        "event_id": "success", "ts": NOW + 1000, "reason": "tool_succeeded"},
        observed_at=NOW + 1000)
    assert store.query_recent_loop_signals(since_minutes=0) == []
    assert len(store.query_incidents()) == 1


def test_missing_identity_or_evidence_cannot_create_episode(store):
    for changes in ({"session_id": ""}, {"runtime": ""}, {"evidence_refs": []},
                    {"kind": "unknown"}):
        assert observe(store, finding(**changes)) is None
    assert store.query_incidents() == []


def test_completed_session_final_success_closes_the_open_episode(store):
    from clawmetry.incident_evidence import reconcile_ended_sessions
    episode = observe(store)
    store.ingest({"id": "final-success", "node_id": "node-a", "agent_type": "codex",
                  "session_id": "codex:session", "event_type": "tool_result",
                  "ts": "2026-10-02T10:00:00Z", "data": {"tool": "Bash", "is_error": False}})
    store._flush_now()
    reconcile_ended_sessions(store, set(), observed_at=1790935201000)
    row = store.query_incidents(incident_id=episode["incident_id"])[0]
    assert row["state"] == "recovered"
    assert row["recovery_ref"]["event_id"] == "final-success"


def test_projection_failure_rolls_back_episode_and_head(store, monkeypatch):
    def broken(incident):
        raise RuntimeError("projection unavailable")
    monkeypatch.setattr(store, "_project_incident_locked", broken)
    with pytest.raises(RuntimeError, match="projection unavailable"):
        observe(store)
    assert store.query_incidents() == []
    assert store.query_incident_heads() == []


def test_real_detector_pass_updates_episode_during_cooldown_and_recovers_after_end(store, monkeypatch):
    """The actual daemon pass joins ingestion, detectors, persistence and delivery."""
    import time
    from datetime import datetime, timedelta, timezone

    from clawmetry import incident_alerts, sync
    monkeypatch.setattr(sync, "_agent_inventory_pass", lambda *a, **k: {})
    monkeypatch.setattr(sync, "_workspace_incidents", lambda *a, **k: [])
    monkeypatch.setattr(sync, "_agent_inventory_incidents", lambda *a, **k: [])
    monkeypatch.setattr(sync, "_apply_guard_policies", lambda *a, **k: 0)
    monkeypatch.setattr(incident_alerts, "deliver_incident", lambda *a, **k: {"delivered_via": ["banner"]})
    now = datetime.now(timezone.utc)
    def event(i, error=True):
        return {"id": "failure-" + str(i), "node_id": "node-a", "agent_type": "codex",
                "session_id": "codex:session", "event_type": "tool_result",
                "ts": (now + timedelta(seconds=i - 20)).isoformat(),
                "data": {"tool": "Bash", "is_error": error}}
    session = {"session_id": "codex:session", "node_id": "node-a", "agent_type": "codex",
               "status": "active", "started_at": now.isoformat(), "last_active_at": now.isoformat()}
    store.ingest_session(session)
    store.ingest_many([event(i) for i in range(3)])
    store._flush_now()
    state = {}
    sync._emit_detector_incidents(store, state)
    rows = store.query_incidents()
    assert len(rows) == 1
    episode = rows[0]
    assert episode["state"] == "active"
    assert episode["delivered_via"] == ["banner"]
    store.ingest(event(3)); store._flush_now()
    sync._emit_detector_incidents(store, state)
    updated = store.query_incidents()[0]
    assert updated["incident_id"] == episode["incident_id"]
    assert updated["delivered_via"] == ["banner"]
    assert "failure-3" in {r["event_id"] for r in updated["evidence_refs"]}
    assert updated["first_seen"] == episode["first_seen"]
    store.ingest(event(4, error=False)); store._flush_now()
    store.ingest_session(dict(session, status="completed", ended_at=now.isoformat()))
    # Pin each reconciliation input so a combined-suite failure identifies
    # whether session selection, persisted evidence or recovery is wrong.
    assert sync._candidate_active_sessions(store) == []
    from clawmetry import detectors
    from clawmetry.incident_evidence import positive_recovery
    window = store.query_incident_window(session_id="codex:session", runtime="codex", node_id="node-a")
    assert window[0]["id"] == "failure-4", window
    proof = positive_recovery(updated, detectors.normalize_events(window))
    assert proof and proof["event_id"] == "failure-4", (updated, window)
    sync._emit_detector_incidents(store, {})
    recovered = store.query_incidents()[0]
    assert recovered["state"] == "recovered"
    assert recovered["recovery_ref"]["event_id"] == "failure-4"
    assert recovered["recovered_at"] <= int(time.time() * 1000)
    assert not store.query_recent_loop_signals()


def test_retention_removes_old_episode_but_preserves_new_recurrence_head(store):
    old = observe(store)
    store.recover_incident(incident_id=old["incident_id"],
                          recovery_ref={"event_id": "ok", "ts": NOW + 1000,
                                        "reason": "tool_succeeded"}, observed_at=NOW + 1000)
    later = NOW + 10 * 86_400_000
    fresh = observe(store, finding("again", later), now=later)
    store.acknowledge_incident(incident_id=old["incident_id"], observed_at=later)
    store.prune_events_by_age(7, now=later / 1000)
    assert [r["incident_id"] for r in store.query_incidents()] == [fresh["incident_id"]]
    assert store.query_incident_heads()[0]["incident_id"] == fresh["incident_id"]


def test_acknowledgement_replay_cannot_overwrite_a_later_decision(store):
    episode = observe(store)
    store.acknowledge_incident(incident_id=episode['incident_id'], acknowledged=True,
                              observed_at=NOW + 1000, requested_at_ms=NOW + 100)
    store.acknowledge_incident(incident_id=episode['incident_id'], acknowledged=False,
                              observed_at=NOW + 2000, requested_at_ms=NOW + 200)
    replay = store.acknowledge_incident(incident_id=episode['incident_id'], acknowledged=True,
                                       observed_at=NOW + 3000, requested_at_ms=NOW + 100)
    assert replay['acknowledged_at'] is None
    assert replay['state'] == 'active'


def test_encrypted_acknowledgement_is_node_bound_and_confirmed(store, monkeypatch):
    import time

    from clawmetry import local_store, sync
    monkeypatch.setattr(local_store, 'get_store', lambda *a, **k: store)
    results = []
    monkeypatch.setattr(sync, '_post_process_control_result', lambda c, a, r: results.append(r))
    episode = observe(store)
    key = sync.generate_encryption_key()
    config = {'encryption_key': key, 'node_id': 'node-a'}
    body = {'incident_id': episode['incident_id'], 'acknowledged': True, 'requested_at_ms': int(time.time() * 1000)}
    action = {'type': 'incident_acknowledge', 'sealed': sync.encrypt_payload(body, key)}
    sync._dispatch_pending_action(dict(config, node_id='other'), action)
    assert results[-1]['applied'] is False
    sync._dispatch_pending_action(config, action)
    assert results[-1]['applied'] is True
    assert results[-1]['incident']['state'] == 'active'
    assert results[-1]['incident']['acknowledged_at']
    action['sealed'] = sync.encrypt_payload(dict(body, acknowledged=False, requested_at_ms=1), key)
    sync._dispatch_pending_action(config, action)
    assert results[-1]['applied'] is False
    assert store.query_incidents()[0]['acknowledged_at']


def test_unchanged_evidence_does_not_rewrite_projection_or_extend_retention(store, monkeypatch):
    first = observe(store)
    def unexpected_write(*args):
        raise AssertionError('unchanged evidence must not rewrite the projection')
    monkeypatch.setattr(store, '_project_incident_locked', unexpected_write)
    repeat = observe(store, now=NOW + 1000)
    assert repeat['incident_id'] == first['incident_id']
    assert repeat['updated_at'] == first['updated_at']
    assert repeat['last_seen'] == first['last_seen']
