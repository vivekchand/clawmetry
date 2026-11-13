"""Process discovery and monitoring cost retain their evidence limits.

AC-OBS-NODE-SEARCH-001.1
AC-OBS-NODE-SEARCH-001.2
AC-OBS-NODE-SEARCH-001.3
AC-OBS-NODE-SEARCH-002.1
AC-OBS-NODE-SEARCH-002.2
AC-OBS-NODE-SEARCH-002.3
AC-OBS-NODE-SEARCH-002.4
"""
import json
from pathlib import Path
from types import SimpleNamespace as Obj

import pytest

from clawmetry import node_activity as collector
from tests.test_node_activity_collector_clarity import Sensor


@pytest.mark.parametrize("argv,role", [
    (["/usr/bin/python3", "-m", "clawmetry", "sync"], "collector"),
    (["python", "-u", "-m", "clawmetry.sync"], "collector"),
    (["python", "/venv/bin/clawmetry", "--port", "8900"], "dashboard"),
    ([r"C:\venv\Scripts\clawmetry.exe", "sync"], "collector"),
    (["python", "-m", "clawmetry", "--port", "8900"], "dashboard"),
    (["python", str(Path(collector.__file__).resolve().parents[1] / "dashboard.py")], "dashboard"),
    (["python", "other.py", "clawmetry", "sync"], None),
    (["python", "-c", "import clawmetry; print('sync')"], None),
    (["python", "-m", "unrelated", "clawmetry"], None),
    (["python", "/tmp/dashboard.py"], None),
    (["python", "-m", "clawmetry", "status"], "cli"),
    (["sh", "-c", "clawmetry sync"], None),
])
def test_exact_launch_roles(argv, role):
    assert collector._clawmetry_launch_role(argv) == role


def test_self_is_collected_before_enumeration_and_survives_cap(tmp_path, monkeypatch):
    from tests.test_node_activity import Store
    monkeypatch.setattr(collector, "MAX_PROCESSES", 2)
    monkeypatch.setattr(collector.os, "getpid", lambda: 10)
    clock = Obj(now=100.0)
    monkeypatch.setattr(collector.time, "monotonic", lambda: clock.now)
    sensor = Sensor()
    base = dict(sensor.processes[0].info)
    self_process = Obj(as_dict=lambda **kwargs: dict(base))
    sensor.Process = lambda pid: self_process if pid == 10 else None
    # The collector is absent from the bounded enumeration entirely.
    sensor.processes = [Obj(info=dict(base, pid=pid, create_time=pid)) for pid in range(20, 30)]
    sensor.error = None

    def scan():
        return collector.collect_node_activity(psutil_module=sensor, home=tmp_path,
                                               fingerprint_key=b"k" * 32, node_id="test")

    store = Store()
    try:
        first = store.record_node_activity(scan())
        row = next(row for row in first["processes"] if row["pid"] == 10)
        assert row["clawmetry_role"] == "collector" and row["cpu_percent"] is None
        assert len(first["processes"]) == 2 and first["coverage"]["processes"]["truncated"]
        clock.now += 30
        measured = store.record_node_activity(scan())
        row = next(row for row in measured["processes"] if row["pid"] == 10)
        assert row["cpu_percent"] == 0 and row["cpu_interval_seconds"] == 30
        assert row["memory_bytes"] == 40 and not row["stale"]
        assert row["actor"]["kind"] == "unknown"
        assert len(collector._PROCESS_CPU_SAMPLES[sensor]["samples"]) == 2
        disabled = collector.collect_node_activity(
            psutil_module=sensor, preferences={"processes": False}, home=tmp_path)
        assert disabled["public"]["processes"] == []
        assert disabled["public"]["coverage"]["processes"]["state"] == "disabled"
    finally:
        store._conn.close()


def test_role_survives_storage_without_arguments_or_false_attribution(tmp_path):
    from tests.test_node_activity import Store
    sensor = Sensor()
    sensor.error = None
    proc = sensor.processes[0]
    proc.info["name"] = "python3.12"
    proc.cmdline = lambda: ["python3", "-m", "clawmetry", "--token", "private-secret"]
    store = Store()
    try:
        observation = collector.collect_node_activity(psutil_module=sensor, home=tmp_path)
        data = store.record_node_activity(observation)
        row = next(row for row in data["processes"] if row["pid"] == 10)
        assert row["name"] == "python3.12" and row["clawmetry_role"] == "dashboard"
        assert row["actor"]["kind"] == "unknown"
        assert "private-secret" not in json.dumps(observation)
        assert "cmdline" not in json.dumps(data)
    finally:
        store._conn.close()


def test_unreadable_launch_does_not_drop_resource_observation(tmp_path):
    sensor = Sensor()
    sensor.error = None
    sensor.processes[0].info["name"] = "python3.12"
    def denied():
        raise PermissionError()
    sensor.processes[0].cmdline = denied
    result = collector.collect_node_activity(psutil_module=sensor, home=tmp_path)
    row = result["public"]["processes"][0]
    assert "clawmetry_role" not in row and row["memory_bytes"] == 40


def test_relative_dashboard_requires_matching_working_directory():
    root = Path(collector.__file__).resolve().parents[1]
    assert collector._clawmetry_launch_role(["python", "dashboard.py"], cwd=root) == "dashboard"
    assert collector._clawmetry_launch_role(["python", "dashboard.py"], cwd="/tmp") is None


@pytest.mark.parametrize("enumeration_denied", [False, True])
def test_self_is_deduplicated_and_preserved_when_enumeration_fails(tmp_path, monkeypatch, enumeration_denied):
    sensor = Sensor()
    sensor.error = None
    monkeypatch.setattr(collector.os, "getpid", lambda: 10)
    sensor.Process = lambda pid: Obj(as_dict=lambda **kwargs: dict(sensor.processes[0].info))
    if enumeration_denied:
        def denied(*args, **kwargs):
            raise PermissionError()
        sensor.process_iter = denied
    result = collector.collect_node_activity(psutil_module=sensor, home=tmp_path)["public"]
    assert len(result["processes"]) == 1
    assert result["processes"][0]["clawmetry_role"] == "collector"
    assert result["coverage"]["processes"]["state"] == ("partial" if enumeration_denied else "complete")


def test_live_worker_measures_during_blocked_ingest_and_expires_view(tmp_path, monkeypatch):
    """Live collection proceeds while ingest is blocked.

    AC-OBS-NODE-SEARCH-003.1
    AC-OBS-NODE-SEARCH-003.2
    """
    import threading
    import time
    from clawmetry import node_activity_service as service
    from tests.test_node_activity import Store
    service.stop_node_activity()
    service._LAST_TICKS.clear()
    monkeypatch.setattr(service, 'INTERVAL_SECONDS', .3)
    monkeypatch.setattr(service, 'LIVE_INTERVAL_SECONDS', .1)
    monkeypatch.setattr(service, 'VIEW_LEASE_SECONDS', .15)
    monkeypatch.setattr(collector, '_read_lsof', lambda deadline: (b'', False))
    sensor = Sensor()
    sensor.error = None
    def collect(**kwargs):
        return collector.collect_node_activity(psutil_module=sensor, home=tmp_path, **kwargs)
    monkeypatch.setattr(service, 'collect_node_activity', collect)
    store = Store()
    gate = threading.Event()
    ingest = threading.Thread(target=lambda: gate.wait(3))
    ingest.start()
    try:
        assert service.start_node_activity(store, node_id='live-test') is True
        assert service.start_node_activity(store, node_id='live-test') is False
        deadline = time.monotonic() + 3
        stamps = set()
        frame = None
        while time.monotonic() < deadline:
            frame = store.query_node_activity_live()
            if frame.get('collected_at'):
                stamps.add(frame['collected_at'])
            if len(stamps) >= 2 and frame.get('processes') and frame['processes'][0]['cpu_percent'] is not None:
                break
            time.sleep(.03)
        assert not gate.is_set(), 'Ingest has not completed'
        assert len(stamps) >= 2 and frame['processes'][0]['cpu_percent'] == 0
        assert frame['processes'][0]['cpu_interval_seconds'] < .5
        assert 'events' not in frame and 'samples' not in frame
        time.sleep(.2)
        assert not service._view_active(), 'A stopped browser cannot leave a permanent fast poller'
    finally:
        service.stop_node_activity()
        gate.set()
        ingest.join(3)
        store._conn.close()


def test_resource_only_pass_does_not_scan_listeners_files_or_logins(tmp_path):
    sensor = Sensor()
    def forbidden(*a, **kw):
        pytest.fail('A fast metric pass must not collect slow sources')
    sensor.net_connections = forbidden
    sensor.users = forbidden
    result = collector.collect_node_activity(psutil_module=sensor, resources_only=True,
                                               home=tmp_path, fingerprint_key=b'k'*32)
    assert result['public']['processes']
    assert result['public']['coverage']['listeners']['state'] == 'disabled'
    assert result['public']['coverage']['sensitive_files']['state'] == 'disabled'


def test_live_rpc_requires_daemon_token_and_carries_no_control_surface():
    """The private live-read RPC remains authenticated.

    AC-OBS-NODE-SEARCH-003.4
    """
    from flask import Flask
    from routes.local_query import bp_local_query
    app = Flask(__name__)
    app.register_blueprint(bp_local_query)
    assert app.test_client().post('/__local_query__/query_node_activity_live', json={'kwargs':{}}).status_code == 401


def test_live_worker_refuses_a_startup_proxy_instead_of_silently_polling_it():
    from clawmetry import node_activity_service as service
    from clawmetry.local_store import _ProxyStore
    with pytest.raises(RuntimeError,match='daemon writer'):
        service.start_node_activity(_ProxyStore())


def test_shutdown_during_collection_does_not_start_a_late_write(tmp_path,monkeypatch):
    import threading
    from clawmetry import node_activity_service as service
    from tests.test_node_activity import Store
    store = Store()
    stopping = threading.Event()
    def collect(**kwargs):
        stopping.set()
        return collector.collect_node_activity(psutil_module=Sensor(),home=tmp_path,**kwargs)
    service._LAST_TICKS.clear()
    monkeypatch.setattr(service,'collect_node_activity',collect)
    try:
        assert service.tick_node_activity(store,stop_event=stopping) is None
        assert not store.query_node_activity()['available']
    finally:
        store._conn.close()


def _concurrent_node_store():
    from tests.test_node_activity import Store
    class ConcurrentStore(Store):
        def _fetch(self, sql, params):
            cursor = self._conn.cursor()
            try:
                return cursor.execute(sql, params).fetchall()
            finally:
                cursor.close()
    return ConcurrentStore()


def test_initialized_live_reads_complete_while_ingestion_holds_writer():
    """AC-OBS-NODE-SEARCH-003.1: read-only preferences cannot queue behind ingest."""
    import threading
    store = _concurrent_node_store()
    expected = store.get_node_activity_state()
    store.record_node_activity_live({'live': True, 'available': True, 'processes': [], 'summary': {}})
    done = threading.Event()
    values, errors = [], []
    def read():
        try:
            values.append(store.get_node_activity_state())
            values.append(store.query_node_activity_live())
        except Exception as exc:
            errors.append(exc)
        finally:
            done.set()
    store._write_lock.acquire()
    thread = threading.Thread(target=read, daemon=True)
    try:
        thread.start()
        assert done.wait(2), 'Live reads waited for an unrelated writer transaction'
        assert not errors
        assert values[0] == expected
        assert values[1]['preferences']['enabled'] is True
    finally:
        store._write_lock.release()
        thread.join(2)
        store._conn.close()


def test_live_read_does_not_initialize_a_private_comparison_key():
    import threading
    store = _concurrent_node_store()
    done = threading.Event()
    errors = []
    def read():
        try:
            assert store.query_node_activity_live()['preferences']['enabled'] is True
        except Exception as exc:
            errors.append(exc)
        finally:
            done.set()
    store._write_lock.acquire()
    thread = threading.Thread(target=read, daemon=True)
    try:
        thread.start()
        assert done.wait(2), 'A frame read attempted comparison-key initialization'
        assert not errors
    finally:
        store._write_lock.release()
        thread.join(2)
    try:
        assert not store._fetch("SELECT value FROM node_activity_meta WHERE key='fingerprint_key'", [])
    finally:
        store._conn.close()


def test_initial_comparison_key_creation_remains_serialized():
    import threading
    store = _concurrent_node_store()
    observed_missing = threading.Barrier(3)
    fetch = store._fetch
    def read(sql, params):
        rows = fetch(sql, params)
        if 'WHERE key IN' in sql and not any(row[0] == 'fingerprint_key' for row in rows):
            observed_missing.wait(timeout=2)
        return rows
    store._fetch = read
    results, errors = [], []
    def initialize():
        try:
            results.append(store.get_node_activity_state()['fingerprint_key'])
        except Exception as exc:
            errors.append(exc)
    store._write_lock.acquire()
    threads = [threading.Thread(target=initialize, daemon=True) for _ in range(2)]
    try:
        for thread in threads:
            thread.start()
        observed_missing.wait(timeout=2)
        assert not results, 'Missing comparison keys require the daemon writer'
    finally:
        store._write_lock.release()
        for thread in threads:
            thread.join(2)
    try:
        assert not errors and len(results) == 2
        assert len(results[0]) == 32 and results[0] == results[1]
        assert store.get_node_activity_state()['fingerprint_key'] == results[0]
        assert len(store._fetch("SELECT value FROM node_activity_meta WHERE key='fingerprint_key'", [])) == 1
    finally:
        store._conn.close()
