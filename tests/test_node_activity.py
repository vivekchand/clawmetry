"""Node evidence stays bounded, attributable and honest across missing scans.

AC-OBS-NODE-001.1
AC-OBS-NODE-001.2
AC-OBS-NODE-001.3
AC-OBS-NODE-002.1
AC-OBS-NODE-002.2
AC-OBS-NODE-002.3
AC-OBS-NODE-002.4
AC-GOV-NODE-003.1
AC-GOV-NODE-003.2
AC-GOV-NODE-004.1
AC-GOV-NODE-004.2
AC-GOV-NODE-004.3
AC-GOV-NODE-005.1
AC-GOV-NODE-005.2
AC-GOV-NODE-005.3
AC-OBS-NODE-006.1
"""
import copy
import json
import socket
import threading
from types import SimpleNamespace as Obj

import duckdb
import pytest
from flask import Flask

from clawmetry import node_activity as collector
from clawmetry.node_activity_store import NODE_ACTIVITY_DDL, NodeActivityStoreMixin
from routes import node_activity as routes


class Store(NodeActivityStoreMixin):
    def __init__(self, path=":memory:"):
        self._conn = duckdb.connect(path)
        self._write_lock = threading.Lock()
        self._read_only = False
        for sql in NODE_ACTIVITY_DDL:
            self._conn.execute(sql)

    def _fetch(self, sql, params):
        with self._write_lock:
            return self._conn.execute(sql, params).fetchall()


@pytest.fixture
def store():
    result = Store()
    yield result
    result._conn.close()


class Sensor:
    def __init__(self):
        self.start = 100
        self.processes = [Obj(info={"pid": 10, "ppid": 1, "name": "codex", "create_time": self.start,
                                   "memory_info": Obj(rss=40)})]
        self.connections = []
        self.fail_connections = False

    def boot_time(self): return 1
    def cpu_percent(self, interval=None): return 12.5
    def virtual_memory(self): return Obj(used=200, total=1000)
    def process_iter(self, attrs, ad_value=None): return iter(self.processes)
    def users(self): return []
    def net_connections(self, kind):
        if self.fail_connections:
            raise PermissionError()
        return self.connections


def observe(sensor, tmp_path, now=1000, **kwargs):
    return collector.collect_node_activity(psutil_module=sensor, home=tmp_path,
                                           fingerprint_key=b"k" * 32, now=now, **kwargs)


def test_quiet_baseline_pid_reuse_and_name_is_not_agent(store, tmp_path, monkeypatch):
    monkeypatch.setattr(collector.platform, "system", lambda: "Darwin")
    sensor = Sensor()
    first = store.record_node_activity(observe(sensor, tmp_path))
    assert first["events"] == []
    assert first["processes"][0]["actor"]["kind"] == "unknown"
    first_id = first["processes"][0]["id"]
    sensor.processes[0].info["create_time"] = 101
    second = store.record_node_activity(observe(sensor, tmp_path, now=1030))
    assert second["processes"][0]["id"] != first_id
    assert {e["kind"] for e in second["events"]} == {"process_added", "process_removed"}
    ids = [e["id"] for e in second["events"]]
    assert [e["id"] for e in store.record_node_activity(observe(sensor, tmp_path, now=1030))["events"]] == ids


def test_partial_and_namespace_change_never_infer_removal(store, tmp_path, monkeypatch):
    sensor = Sensor()
    store.record_node_activity(observe(sensor, tmp_path))
    monkeypatch.setattr(collector, "MAX_PROCESSES", 0)
    capped = store.record_node_activity(observe(sensor, tmp_path, now=1030))
    assert capped["processes"][0]["stale"]
    assert capped["summary"]["process_count"] is None
    assert capped["coverage"]["processes"]["state"] == "partial"
    assert capped["events"] == []
    monkeypatch.setattr(collector, "MAX_PROCESSES", 512)
    sensor.processes = []
    # Re-establish a baseline after the gap; no retrospective disappearance.
    assert store.record_node_activity(observe(sensor, tmp_path, now=1060))["events"] == []
    sensor.processes = Sensor().processes
    changed = observe(sensor, tmp_path, now=1090)
    changed["sources"]["processes"]["identity"] = "new-visible-namespace"
    assert store.record_node_activity(changed)["events"] == []


def test_socket_finding_and_permission_gap(store, tmp_path, monkeypatch):
    monkeypatch.setattr(collector.platform, "system", lambda: "Darwin")
    sensor = Sensor()
    store.record_node_activity(observe(sensor, tmp_path))
    sensor.connections = [Obj(type=socket.SOCK_STREAM, status="LISTEN", laddr=("0.0.0.0", 8765), pid=10)]
    new = store.record_node_activity(observe(sensor, tmp_path, now=1030))
    finding = next(e for e in new["events"] if e["kind"] == "listener_added")
    assert finding["finding"] and finding["after"]["port"] == 8765
    assert finding["actor"]["kind"] == "unknown"
    assert "kill" not in json.dumps(new)
    sensor.fail_connections = True
    failed = store.record_node_activity(observe(sensor, tmp_path, now=1060))
    assert failed["coverage"]["listeners"]["state"] == "unavailable"
    assert failed["listeners"][0]["stale"]
    assert len(failed["events"]) == len(new["events"])


def test_sensitive_change_fingerprints_private_and_review_keeps_original(store, tmp_path, monkeypatch):
    monkeypatch.setattr("clawmetry.node_activity_store.time.time", lambda: 1030)
    target = tmp_path / ".ssh" / "authorized_keys"
    target.parent.mkdir()
    target.write_text("secret-original")
    sensor = Sensor()
    store.record_node_activity(observe(sensor, tmp_path))
    target.write_text("secret-replacement")
    body = store.record_node_activity(observe(sensor, tmp_path, now=1030))
    event = next(e for e in body["events"] if e["kind"] == "sensitive_config_changed")
    assert event["finding"]
    assert "contents" in event["changed_fields"]
    assert any("file contents changed" in line for line in event["evidence"])
    public = json.dumps(body)
    assert "secret-original" not in public and "secret-replacement" not in public
    assert "fingerprint" not in json.dumps(body["events"]) and "_fingerprint" not in public
    original = copy.deepcopy(event)
    result = store.review_node_activity_event(event["id"], "expected", "A planned update")
    assert result["saved"]
    reviewed = next(e for e in store.query_node_activity()["events"] if e["id"] == event["id"])
    assert reviewed.pop("review")["decision"] == "expected"
    assert reviewed == original
    with pytest.raises(ValueError):
        store.review_node_activity_event("missing", "expected")


def test_preferences_persist_and_disabled_means_no_sensor_calls(tmp_path):
    path = str(tmp_path / "node.duckdb")
    first = Store(path)
    first.set_node_activity_preferences({"enabled": False})
    first._conn.close()
    second = Store(path)
    try:
        state = second.get_node_activity_state()
        assert not state["preferences"]["enabled"]
        class NoSensor:
            def boot_time(self): raise AssertionError("Disabled monitoring read the host")
        observation = collector.collect_node_activity(preferences=state["preferences"], psutil_module=NoSensor())
        assert {s["state"] for s in observation["public"]["coverage"].values()} == {"disabled"}
        body = second.record_node_activity(observation)
        assert body["events"][0]["kind"] == "monitoring_preferences_changed"
        assert len(body["samples"]) == 0
        with pytest.raises(ValueError): second.set_node_activity_preferences({"arbitrary_pid": True})
        with pytest.raises(ValueError): second.set_node_activity_preferences({"enabled": 1})
    finally:
        second._conn.close()


def test_selected_symlink_is_not_read_and_container_scope_is_explicit(tmp_path, monkeypatch):
    target = tmp_path / ".ssh" / "config"
    target.parent.mkdir()
    foreign = tmp_path / "unrelated-secret"
    foreign.write_text("secret")
    target.symlink_to(foreign)
    monkeypatch.setattr(collector, "_namespace", lambda: ("container", "container-identity"))
    observation = observe(Sensor(), tmp_path)
    assert observation["public"]["coverage"]["sensitive_files"]["state"] == "partial"
    assert all(c["scope"] == "container" for c in observation["public"]["coverage"].values())
    assert all(r["id"] != "ssh_config" for r in observation["sources"]["sensitive_files"]["rows"])


def test_retention_and_review_history_are_bounded(store, tmp_path):
    sensor = Sensor()
    store.record_node_activity(observe(sensor, tmp_path, now=1000))
    for index in range(5):
        sensor.processes[0].info["create_time"] += 1
        store.record_node_activity(observe(sensor, tmp_path, now=1030 + index), max_events=3)
    assert len(store.query_node_activity()["events"]) == 3
    store.record_node_activity(observe(sensor, tmp_path, now=100000), max_events=3)
    assert not store.query_node_activity()["events"]


def test_route_stored_only_and_unconfirmed_write_is_failure(monkeypatch):
    app = Flask(__name__)
    app.register_blueprint(routes.bp_node_activity)
    monkeypatch.setattr(routes, "store_is_authoritative", lambda: True)
    monkeypatch.setattr(routes, "_write_allowed", lambda: True)
    calls = []
    def call(method, **kwargs):
        calls.append((method, kwargs))
        return collector.unavailable() if method == "query_node_activity" else None
    monkeypatch.setattr(routes, "_call", call)
    client = app.test_client()
    assert client.get("/api/node-activity").status_code == 200
    assert calls == [("query_node_activity", {})]
    result = client.post("/api/node-activity/preferences", json={"enabled": False})
    assert result.status_code == 503 and result.json["saved"] is False
    assert client.post("/api/node-activity/preferences", json={"pid": 10}).status_code == 400
    assert client.post("/api/node-activity/reviews", json={"event_id": "a", "decision": "kill"}).status_code == 400
    monkeypatch.setattr(routes, "store_is_authoritative", lambda: False)
    assert client.get("/api/node-activity").json["available"] is False


def test_service_cadence_and_failure_preserve_stored_evidence(store, monkeypatch):
    from clawmetry import node_activity_service as service
    service._LAST_TICKS.clear()
    calls = []
    def collect(**kwargs):
        calls.append(kwargs)
        raise PermissionError()
    monkeypatch.setattr(service, "collect_node_activity", collect)
    assert service.tick_node_activity(store)["available"] is False
    monkeypatch.setattr(store, "query_node_activity", lambda: pytest.fail("Skipped ticks must not read history"))
    assert service.tick_node_activity(store) is None
    assert len(calls) == 1


def test_cpu_warmup_unknown_and_private_home_change_gets_quiet_baseline(store, tmp_path):
    sensor = Sensor()
    first = observe(sensor, tmp_path)
    assert first["public"]["summary"]["cpu_percent"] is None
    assert first["public"]["coverage"]["resources"]["state"] == "partial"
    assert "second observation" in first["public"]["coverage"]["resources"]["reason"]
    store.record_node_activity(first)
    other = tmp_path / "another-home"
    (other / ".ssh").mkdir(parents=True)
    (other / ".ssh/config").write_text("Unrelated home settings")
    next_observation = observe(sensor, other, now=1030)
    assert next_observation["public"]["summary"]["cpu_percent"] == 12.5
    assert store.record_node_activity(next_observation)["events"] == []


def test_restricted_linux_sockets_never_claim_complete_or_zero(tmp_path, monkeypatch):
    monkeypatch.setattr(collector.platform, "system", lambda: "Linux")
    monkeypatch.setattr(collector.os, "geteuid", lambda: 1000)
    body = observe(Sensor(), tmp_path)["public"]
    assert body["coverage"]["listeners"]["state"] == "partial"
    assert body["summary"]["listening_port_count"] is None
    assert "omitted" in body["coverage"]["listeners"]["reason"]


def test_all_findings_survive_more_than_128_routine_changes(store, tmp_path, monkeypatch):
    monkeypatch.setattr(collector.platform, "system", lambda: "Darwin")
    sensor = Sensor()
    store.record_node_activity(observe(sensor, tmp_path))
    sensor.processes = [Obj(info={"pid": pid, "ppid": 1, "name": "ordinary-process", "create_time": 100,
                                 "memory_info": Obj(rss=40)}) for pid in range(200, 400)]
    sensor.connections = [Obj(type=socket.SOCK_STREAM, status="LISTEN", laddr=("0.0.0.0", 8765), pid=200)]
    (tmp_path / ".ssh").mkdir()
    (tmp_path / ".ssh/config").write_text("A changed setting")
    body = store.record_node_activity(observe(sensor, tmp_path, now=1030))
    kinds = [event["kind"] for event in body["events"]]
    assert len(kinds) > 128
    assert "listener_added" in kinds and "sensitive_config_changed" in kinds
    assert len([event for event in body["events"] if event["finding"]]) == 2
    assert not body["truncated"]


def test_listener_identity_stable_when_process_owner_evidence_is_missing(store, tmp_path, monkeypatch):
    monkeypatch.setattr(collector.platform, "system", lambda: "Darwin")
    sensor = Sensor()
    sensor.connections = [Obj(type=socket.SOCK_STREAM, status="LISTEN", laddr=("0.0.0.0", 8765), pid=10)]
    baseline = store.record_node_activity(observe(sensor, tmp_path))
    assert baseline["listeners"][0]["process_id"] is not None
    monkeypatch.setattr(collector, "MAX_PROCESSES", 0)
    missing_owner = store.record_node_activity(observe(sensor, tmp_path, now=1030))
    assert missing_owner["listeners"][0]["process_id"] is None
    assert missing_owner["listeners"][0]["id"] == baseline["listeners"][0]["id"]
    assert missing_owner["events"] == []
    monkeypatch.setattr(collector, "MAX_PROCESSES", 512)
    assert store.record_node_activity(observe(sensor, tmp_path, now=1060))["events"] == []


def test_reviews_bounded_and_latest_even_when_clock_does_not_advance(store, monkeypatch):
    from clawmetry import node_activity_store as module
    monkeypatch.setattr(module.time, "time", lambda: 1000)
    monkeypatch.setattr(module, "MAX_REVIEWS_PER_EVENT", 3)
    monkeypatch.setattr(module, "MAX_REVIEWS", 4)
    store.set_node_activity_preferences({"processes": False})
    first = store.query_node_activity()["events"][0]["id"]
    for index in range(10):
        store.review_node_activity_event(first, "expected", str(index))
    assert store._conn.execute("SELECT COUNT(*) FROM node_activity_reviews").fetchone()[0] == 3
    assert store.query_node_activity()["events"][0]["review"]["reason"] == "9"
    store.set_node_activity_preferences({"processes": True})
    second = next(e["id"] for e in store.query_node_activity()["events"] if e["id"] != first)
    for index in range(10):
        store.review_node_activity_event(second, "investigate", str(index))
    assert store._conn.execute("SELECT COUNT(*) FROM node_activity_reviews").fetchone()[0] == 4
    # No collection is required to apply age retention on a governance write.
    monkeypatch.setattr(module.time, "time", lambda: 100000)
    store.set_node_activity_preferences({"processes": False})
    assert store._conn.execute("SELECT COUNT(*) FROM node_activity_reviews").fetchone()[0] == 0
    assert len(store.query_node_activity()["events"]) == 1


def test_bounded_process_candidates_keep_recent_work_not_first_pids(tmp_path, monkeypatch):
    monkeypatch.setattr(collector, "MAX_PROCESSES", 3)
    monkeypatch.setattr(collector, "MAX_PROCESS_CANDIDATES", 6)
    sensor = Sensor()
    sensor.processes = [Obj(info={"pid": pid, "ppid": 1, "name": "ordinary-process", "create_time": pid,
                                 "memory_info": Obj(rss=pid)}) for pid in range(10, 17)]
    body = observe(sensor, tmp_path)["public"]
    assert [p["pid"] for p in body["processes"]] == [15, 14, 13]
    assert body["coverage"]["processes"]["truncated"] is True
    assert body["summary"]["process_count"] is None
    assert body["coverage"]["sensitive_files"]["state"] == "complete"


def test_process_iterator_cache_is_cleared_before_each_identity_scan(store, tmp_path):
    """AC-OBS-NODE-002.4: fresh creation times survive library Process caching."""
    sensor = Sensor()

    class CachedIterator:
        def __init__(self):
            self.actual_start = 100
            self.cached = None
            self.clears = 0

        def cache_clear(self):
            self.cached = None
            self.clears += 1

        def __call__(self, attrs, ad_value=None):
            if self.cached is None:
                self.cached = Obj(info={"pid": 10, "ppid": 1, "name": "ordinary-process",
                                        "create_time": self.actual_start, "memory_info": Obj(rss=40)})
            return iter([self.cached])

    sensor.process_iter = CachedIterator()
    baseline = store.record_node_activity(observe(sensor, tmp_path))
    assert baseline["events"] == []
    previous_id = baseline["processes"][0]["id"]
    sensor.process_iter.actual_start = 200
    reused = store.record_node_activity(observe(sensor, tmp_path, now=1030))
    assert reused["processes"][0]["id"] != previous_id
    assert reused["processes"][0]["started_at"] == 200000
    assert {event["kind"] for event in reused["events"]} == {"process_added", "process_removed"}
    assert sensor.process_iter.clears == 2


def partial_batch(source, ids, now, *, state="partial", source_id="same-source"):
    """A daemon batch, with no live host dependency."""
    rows = [{"id": str(key), "pid": key, "started_at": key * 1000,
             "name": "ordinary-process", "actor": {"kind": "unknown", "label": "Unattributed"}}
            for key in ids]
    body = collector.unavailable()
    body.update(available=True, collected_at=now)
    body["coverage"] = {key: {"state": "disabled"} for key in
                        ("resources", "processes", "listeners", "sensitive_files", "logins")}
    body["coverage"][source] = {"state": state, "observed_at": now, "reason": "Partial scan."}
    body[source] = copy.deepcopy(rows)
    return {"public": body, "sources": {source: {"identity": source_id, "rows": rows}}}


@pytest.mark.parametrize("source,cap", [("processes", 512), ("listeners", 256),
                                         ("sensitive_files", 5), ("logins", 64)])
def test_partial_incoming_rows_win_each_source_cap(store, source, cap):
    """
    AC-OBS-NODE-PART-001.1: a full stale cap cannot hide fresh rows.
    """
    store.record_node_activity(partial_batch(source, range(cap), 1000))
    body = store.record_node_activity(partial_batch(source, [cap], 2000))
    assert len(body[source]) == cap
    assert body[source][0]["id"] == str(cap)
    assert body[source][0]["stale"] is False
    assert {row["id"] for row in body[source]} == {str(key) for key in range(cap - 1)} | {str(cap)}


def test_row_times_distinguish_current_stale_and_legacy_unknown(store):
    """
    AC-OBS-NODE-PART-001.2: stale evidence never receives the new scan time.
    """
    first = store.record_node_activity(partial_batch("processes", [1, 2], 1000))
    assert all(row["observed_at"] == 1000 and row["stale"] is False for row in first["processes"])
    legacy = store._node_meta_locked("public")
    del legacy["processes"][1]["observed_at"]
    store._node_put_locked("public", legacy)
    second = store.record_node_activity(partial_batch("processes", [3], 2000))
    assert [(r["id"], r["observed_at"], r["stale"]) for r in second["processes"]] == [
        ("3", 2000, False), ("1", 1000, True), ("2", None, True)]


def test_partial_process_positive_sighting_is_qualified_and_private(store):
    """
    AC-OBS-NODE-PART-002.1: first readable partial batch is quiet.

    AC-OBS-NODE-PART-002.2: later positive evidence does not prove a start.
    """
    assert not store.record_node_activity(partial_batch("processes", [1, 2], 1000))["events"]
    body = store.record_node_activity(partial_batch("processes", [2, 3], 2000))
    assert len(body["events"]) == 1
    event = body["events"][0]
    assert event["kind"] == "process_observed" and event["target"]["id"] == "3"
    assert event["title"] == "A process was first observed"
    assert not event["finding"] and event["severity"] == "info"
    assert event["actor"]["kind"] == "unknown" and event["before"] is None
    assert event["after"]["observed_at"] == 2000
    evidence = " ".join([event["detail"], *event["evidence"]]).lower()
    for qualification in ("retained history", "partial", "actual start", "complete inventory", "malicious"):
        assert qualification in evidence
    assert "process_sightings" not in json.dumps(body)
    assert store._node_meta_locked("process_sightings")["seen"]["3"] == 2000


def test_partial_sighting_dedup_survives_restart_gaps_and_reenable(tmp_path, monkeypatch):
    """
    AC-OBS-NODE-PART-002.3: durable identity knowledge is separate from quiet epochs.
    """
    monkeypatch.setattr("clawmetry.node_activity_store.time.time", lambda: 1)
    path = str(tmp_path / "sightings.duckdb")
    first = Store(path)
    first.record_node_activity(partial_batch("processes", [1], 1000))
    first.record_node_activity(partial_batch("processes", [2], 2000))
    first._conn.close()
    second = Store(path)
    try:
        def sightings(body): return [e for e in body["events"] if e["kind"] == "process_observed"]
        assert len(sightings(second.record_node_activity(partial_batch("processes", [1, 2], 3000)))) == 1
        second.record_node_activity(partial_batch("processes", [], 4000, state="unavailable"))
        assert len(sightings(second.record_node_activity(partial_batch("processes", [3], 5000)))) == 1
        assert len(sightings(second.record_node_activity(partial_batch("processes", [1, 2, 3, 4], 6000)))) == 2
        second.set_node_activity_preferences({"enabled": False})
        second.set_node_activity_preferences({"enabled": True})
        assert len(sightings(second.record_node_activity(partial_batch("processes", [5], 7000)))) == 2
        assert len(sightings(second.record_node_activity(partial_batch("processes", [1, 5, 6], 8000)))) == 3
        # Re-establish a complete comparison quietly, then cap again with no repeated positives.
        assert len(sightings(second.record_node_activity(partial_batch("processes", [1, 2, 3, 4, 5, 6], 9000, state="complete")))) == 3
        body = second.record_node_activity(partial_batch("processes", [2, 6], 10000))
        assert len(sightings(body)) == 3
        assert not any(e["kind"] == "process_removed" for e in body["events"])
        assert len(sightings(second.record_node_activity(partial_batch("processes", [7], 11000, source_id="new-source")))) == 3
    finally:
        second._conn.close()


def test_sighting_saturation_is_sticky_and_complete_reset_quiet(store, monkeypatch):
    """
    AC-OBS-NODE-PART-003.1: forgotten overflow identities never manufacture novelty.
    """
    from clawmetry import node_activity_store as module
    monkeypatch.setattr(module, "MAX_PROCESS_SIGHTINGS", 2)
    store.record_node_activity(partial_batch("processes", [1, 2], 1000), retention_hours=1)
    overflow = store.record_node_activity(partial_batch("processes", [3], 2000), retention_hours=1)
    assert overflow["coverage"]["processes"]["sighting_history_limited"] is True
    assert "positive-sighting history is incomplete" in overflow["coverage"]["processes"]["reason"]
    assert overflow["processes"][0]["id"] == "3" and not overflow["processes"][0]["stale"]
    assert not overflow["events"]
    assert set(store._node_meta_locked("process_sightings")["seen"]) == {"1", "2"}
    # Expiry and a gap free capacity, but neither can erase knowledge of missing history.
    store.record_node_activity(partial_batch("processes", [], 3602001), retention_hours=1)
    resumed = store.record_node_activity(partial_batch("processes", [3], 3603000), retention_hours=1)
    again = store.record_node_activity(partial_batch("processes", [4], 3604000), retention_hours=1)
    assert resumed["coverage"]["processes"]["sighting_history_limited"]
    assert again["coverage"]["processes"]["sighting_history_limited"] and not again["events"]
    reset = store.record_node_activity(partial_batch("processes", [3, 4], 3605000, state="complete"), retention_hours=1)
    assert not reset["coverage"]["processes"]["sighting_history_limited"] and not reset["events"]
    assert not store.record_node_activity(partial_batch("processes", [3], 3606000), retention_hours=1)["events"]


def test_sighting_expiry_is_retained_window_not_lifetime_novelty(store):
    """
    AC-OBS-NODE-PART-003.2: old unobserved keys expire under the declared window.
    """
    store.record_node_activity(partial_batch("processes", [1], 1000), retention_hours=1)
    store.record_node_activity(partial_batch("processes", [2], 2000), retention_hours=1)
    body = store.record_node_activity(partial_batch("processes", [1], 3602001), retention_hours=1)
    assert len(body["events"]) == 1 and body["events"][0]["target"]["id"] == "1"
    assert "retained history" in body["events"][0]["detail"]
    assert store._node_meta_locked("process_sightings")["seen"] == {"1": 3602001}
    assert body["retention"]["process_sighting_limit"] == 16384


def test_capped_real_collector_pid_start_observations_and_quiet_rebaseline(store, tmp_path, monkeypatch):
    """Partial process observations use the collector's measured PID/start identity."""
    monkeypatch.setattr(collector, "MAX_PROCESSES", 1)
    sensor = Sensor()
    sensor.processes.append(Obj(info={"pid": 20, "ppid": 1, "name": "worker", "create_time": 50,
                                      "memory_info": Obj(rss=40)}))
    assert not store.record_node_activity(observe(sensor, tmp_path))["events"]
    # Reused PID, new measured start: distinct positive identity, never a partial removal.
    sensor.processes[0].info["create_time"] = 200
    body = store.record_node_activity(observe(sensor, tmp_path, now=2000))
    assert [e["kind"] for e in body["events"]] == ["process_observed"]
    assert body["events"][0]["process"]["started_at"] == 200000
    monkeypatch.setattr(collector, "MAX_PROCESSES", 512)
    full = store.record_node_activity(observe(sensor, tmp_path, now=3000))
    assert [e["kind"] for e in full["events"]] == ["process_observed"]


def test_full_cap_rotation_and_duplicate_batch_do_not_repeat_positives(store):
    store.record_node_activity(partial_batch("processes", range(512), 1000))
    rotated = store.record_node_activity(partial_batch("processes", range(1, 513), 2000))
    assert len(rotated["processes"]) == 512 and rotated["processes"][-1]["id"] == "512"
    assert [e["target"]["id"] for e in rotated["events"]] == ["512"]
    repeat = partial_batch("processes", range(512), 3000)
    repeat["sources"]["processes"]["rows"] *= 2
    body = store.record_node_activity(repeat)
    assert len(body["processes"]) == 512 and len(body["events"]) == 1
    assert len(store._node_meta_locked("process_sightings")["seen"]) == 513


def test_migration_and_empty_partial_gap_initialize_quietly(store):
    first = store.record_node_activity(partial_batch("processes", [1], 1000, state="complete"))
    store._conn.execute("DELETE FROM node_activity_meta WHERE key IN ('process_sightings','inventory_sources')")
    migrated = store.record_node_activity(partial_batch("processes", [2], 2000))
    assert migrated["events"] == first["events"] == []
    assert migrated["processes"][0]["id"] == "2"
    store.record_node_activity(partial_batch("processes", [], 3000))
    assert not store.record_node_activity(partial_batch("processes", [3], 4000))["events"]
    assert len(store.record_node_activity(partial_batch("processes", [4], 5000))["events"]) == 1
    changed = store.record_node_activity(partial_batch("processes", [5], 6000, source_id="different-source"))
    assert [r["id"] for r in changed["processes"]] == ["5"]
    assert len(changed["events"]) == 1  # New source starts quietly, previous history remains.


def test_positive_dedup_and_event_are_atomic(store, monkeypatch):
    store.record_node_activity(partial_batch("processes", [1], 1000))
    original = store._node_put_locked
    def fail_ledger(key, value):
        if key == "process_sightings":
            raise RuntimeError("simulated writer failure")
        original(key, value)
    with monkeypatch.context() as patch:
        patch.setattr(store, "_node_put_locked", fail_ledger)
        with pytest.raises(RuntimeError, match="simulated writer failure"):
            store.record_node_activity(partial_batch("processes", [2], 2000))
    assert not store.query_node_activity()["events"]
    assert store._node_meta_locked("process_sightings")["seen"] == {"1": 1000}
    assert len(store.record_node_activity(partial_batch("processes", [2], 2000))["events"]) == 1


def test_saturated_history_survives_restart_reenable_and_new_source_reset(tmp_path, monkeypatch):
    from clawmetry import node_activity_store as module
    monkeypatch.setattr(module, "MAX_PROCESS_SIGHTINGS", 1)
    monkeypatch.setattr(module.time, "time", lambda: 1)
    path = str(tmp_path / "overflow.duckdb")
    first = Store(path)
    first.record_node_activity(partial_batch("processes", [1], 1000))
    first.record_node_activity(partial_batch("processes", [2], 2000))
    first._conn.close()
    second = Store(path)
    try:
        second.set_node_activity_preferences({"processes": False})
        second.set_node_activity_preferences({"processes": True})
        body = second.record_node_activity(partial_batch("processes", [2], 3000))
        assert body["coverage"]["processes"]["sighting_history_limited"]
        assert not any(e["kind"] == "process_observed" for e in body["events"])
        assert second._node_meta_locked("process_sightings")["seen"] == {"1": 1000}
        changed = second.record_node_activity(partial_batch("processes", [2], 4000, source_id="new"))
        assert not changed["coverage"]["processes"]["sighting_history_limited"]
        assert not any(e["kind"] == "process_observed" for e in changed["events"])
    finally:
        second._conn.close()


@pytest.mark.parametrize("saturated", [False, True])
def test_real_disabled_batch_preserves_same_source_sightings_and_stale_inventory(store, tmp_path, monkeypatch, saturated):
    """Real disabled collector sentinel identities are gaps, never new namespaces."""
    from clawmetry import node_activity_store as module
    monkeypatch.setattr(module.time, "time", lambda: 1)
    monkeypatch.setattr(collector, "MAX_PROCESSES", 1)
    monkeypatch.setattr(module, "MAX_PROCESS_SIGHTINGS", 1 if saturated else 16384)
    sensor = Sensor()
    sensor.processes.append(Obj(info={"pid": 20, "ppid": 1, "name": "worker", "create_time": 50,
                                      "memory_info": Obj(rss=40)}))
    first = store.record_node_activity(observe(sensor, tmp_path))
    known_id = first["processes"][0]["id"]
    if saturated:
        sensor.processes[0].info["create_time"] = 200
        assert store.record_node_activity(observe(sensor, tmp_path, now=2000))["coverage"]["processes"]["sighting_history_limited"]
    before = store._node_meta_locked("process_sightings")
    store.set_node_activity_preferences({"enabled": False})
    disabled = store.record_node_activity(observe(sensor, tmp_path, now=3000,
                                                 preferences=store.get_node_activity_state()["preferences"]))
    assert disabled["coverage"]["processes"]["state"] == "disabled"
    assert disabled["processes"] and all(row["stale"] for row in disabled["processes"])
    state = store._node_meta_locked("process_sightings")
    assert state["identity"] == before["identity"] and state["seen"] == before["seen"]
    assert state["history_limited"] is saturated
    store.set_node_activity_preferences({"enabled": True})
    sensor.processes[0].info["create_time"] = 100
    resumed = store.record_node_activity(observe(sensor, tmp_path, now=4000))
    assert resumed["processes"][0]["id"] == known_id
    assert not any(e["kind"] == "process_observed" for e in resumed["events"])
    sensor.processes[0].info["create_time"] = 300
    later = store.record_node_activity(observe(sensor, tmp_path, now=5000))
    assert later["coverage"]["processes"]["sighting_history_limited"] is saturated
    assert len([e for e in later["events"] if e["kind"] == "process_observed"]) == (0 if saturated else 1)


@pytest.mark.parametrize("state", ["unavailable", "unsupported", "disabled", "partial"])
def test_unreadable_source_identity_is_not_a_new_namespace(store, state):
    store.record_node_activity(partial_batch("processes", [1], 1000))
    gap = store.record_node_activity(partial_batch("processes", [], 2000, state=state, source_id=state))
    ledger = store._node_meta_locked("process_sightings")
    assert ledger["identity"] == "same-source" and ledger["seen"] == {"1": 1000}
    assert gap["processes"][0]["id"] == "1" and gap["processes"][0]["stale"]
    assert not store.record_node_activity(partial_batch("processes", [2], 3000))["events"]
    # A cap rotation back to the old known identity must stay deduplicated.
    assert not store.record_node_activity(partial_batch("processes", [1, 2], 4000))["events"]
