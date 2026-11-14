"""Measured rates and permitted listeners retain their actual evidence limits.

AC-OBS-NODE-CLARITY-002.1
AC-OBS-NODE-CLARITY-002.2
AC-OBS-NODE-CLARITY-003.1
AC-OBS-NODE-CLARITY-003.2
"""
import socket
import subprocess
import sys
import time
from types import SimpleNamespace as Obj

import pytest

from clawmetry import node_activity as collector


class Sensor:
    def __init__(self):
        self.processes = [Obj(info={"pid": 10, "ppid": 1, "name": "worker", "create_time": 100,
                                   "memory_info": Obj(rss=40), "cpu_times": Obj(user=2, system=1)})]
        self.error = PermissionError()

    def boot_time(self): return 1
    def cpu_percent(self, interval=None): return 12
    def virtual_memory(self): return Obj(used=200, total=1000)
    def process_iter(self, attrs, ad_value=None): return iter(self.processes)
    def users(self): return []
    def net_connections(self, kind):
        if self.error:
            raise self.error
        return []


@pytest.fixture
def scan(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("CLAWMETRY_AUDIT_DB", str(tmp_path / "audit.db"))
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "store.duckdb"))
    monkeypatch.setattr(collector.platform, "system", lambda: "Darwin")
    clock = Obj(now=100.0)
    monkeypatch.setattr(collector.time, "monotonic", lambda: clock.now)
    sensor = Sensor()

    def run(**kwargs):
        return collector.collect_node_activity(psutil_module=sensor, home=tmp_path,
                                               fingerprint_key=b"k" * 32, **kwargs)
    return sensor, clock, run


def test_cpu_measures_one_core_interval_without_priming(scan, monkeypatch):
    sensor, clock, run = scan
    monkeypatch.setattr(collector, "_read_lsof", lambda deadline: (b"", False), raising=False)
    first = run()["public"]["processes"][0]
    assert first["cpu_percent"] is None and first["cpu_reason"]
    clock.now += 2
    sensor.processes[0].info["cpu_times"] = Obj(user=5, system=2)
    measured = run()["public"]["processes"][0]
    assert measured["cpu_percent"] == 200  # 4 CPU seconds / 2 wall seconds.
    assert measured["cpu_interval_seconds"] == 2 and not measured["cpu_reason"]


@pytest.mark.parametrize("change", ["pid_reuse", "missing", "regression", "short", "long", "source", "disable", "omitted"])
def test_cpu_discontinuity_is_unavailable(scan, monkeypatch, change):
    sensor, clock, run = scan
    monkeypatch.setattr(collector, "_read_lsof", lambda deadline: (b"", False), raising=False)
    run()
    clock.now += 30
    if change == "pid_reuse":
        sensor.processes[0].info["create_time"] += 1
    elif change == "missing":
        sensor.processes[0].info["cpu_times"] = None
    elif change == "regression":
        sensor.processes[0].info["cpu_times"] = Obj(user=0, system=0)
    elif change == "short":
        clock.now = 100.05
    elif change == "long":
        clock.now = 221
    elif change == "source":
        monkeypatch.setattr(collector, "_namespace", lambda: ("unknown", "changed"))
    elif change == "disable":
        run(preferences={"enabled": False})
    elif change == "omitted":
        rows = sensor.processes
        sensor.processes = []
        run()
        sensor.processes = rows
        clock.now += 30
    row = run()["public"]["processes"][0]
    assert row["cpu_percent"] is None and row["cpu_interval_seconds"] is None and row["cpu_reason"]


def test_cpu_restart_and_retained_sample_bound(scan, monkeypatch):
    sensor, clock, run = scan
    monkeypatch.setattr(collector, "_read_lsof", lambda deadline: (b"", False), raising=False)
    base = sensor.processes[0].info
    sensor.processes = [Obj(info=dict(base, pid=pid, create_time=pid)) for pid in range(1, 700)]
    run()
    assert len(collector._PROCESS_CPU_SAMPLES[sensor]["samples"]) == 512
    clock.now += 30
    collector._PROCESS_CPU_SAMPLES.clear()  # A fresh daemon has no sampler memory.
    assert all(row["cpu_percent"] is None for row in run()["public"]["processes"])


def test_missing_cpu_baseline_recovers_only_after_another_readable_interval(scan, monkeypatch):
    sensor, clock, run = scan
    monkeypatch.setattr(collector, "_read_lsof", lambda deadline: (b"", False))
    run()
    sensor.processes[0].info["cpu_times"] = None
    clock.now += 30
    run()
    sensor.processes[0].info["cpu_times"] = Obj(user=3, system=1)
    clock.now += 30
    assert run()["public"]["processes"][0]["cpu_percent"] is None
    clock.now += 30
    measured = run()
    assert measured["public"]["processes"][0]["cpu_percent"] == 0
    assert b"cpu_times" not in repr(measured).encode()  # Cumulative inputs are private memory only.


@pytest.mark.parametrize("elapsed", [0.1, 120])
def test_cpu_interval_boundaries_are_comparable(elapsed):
    result, _ = collector._process_cpu(Obj(user=2, system=1), (1, 1, 0), elapsed)
    assert result["cpu_percent"] == 100 / elapsed and result["cpu_interval_seconds"] == elapsed


LSOF = (b"p10\0\nf5\0tIPv4\0n127.0.0.1:43210\0TST=LISTEN\0\n"
        b"f6\0tIPv6\0n[::1]:43211\0TST=LISTEN\0\n"
        b"f7\0tIPv6\0n*:43212\0TST=LISTEN\0\n")


def test_darwin_fallback_is_partial_method_scoped_and_unattributed(scan, monkeypatch):
    _, _, run = scan
    monkeypatch.setattr(collector, "_read_lsof", lambda deadline: (LSOF, False), raising=False)
    result = run()
    rows = result["public"]["listeners"]
    assert [row["port"] for row in rows] == [43210, 43211, 43212]
    assert [row["exposure"] for row in rows] == ["loopback", "loopback", "unknown"]
    assert all(row["pid"] == 10 and row["process_id"] is None and row["actor"]["kind"] == "unknown" for row in rows)
    coverage = result["public"]["coverage"]["listeners"]
    assert coverage["state"] == "partial" and coverage["method"] == "lsof_polling" and coverage["count"] == 3
    assert result["public"]["summary"]["listening_port_count"] is None
    assert result["sources"]["listeners"]["identity"] != result["sources"]["processes"]["identity"]


@pytest.mark.parametrize("os_name,error", [("Linux", PermissionError()), ("Windows", NotImplementedError()), ("Darwin", RuntimeError())])
def test_fallback_only_after_supported_darwin_failure(scan, monkeypatch, os_name, error):
    sensor, _, run = scan
    sensor.error = error
    monkeypatch.setattr(collector.platform, "system", lambda: os_name)
    monkeypatch.setattr(collector, "_read_lsof", lambda deadline: pytest.fail("Unexpected fallback"), raising=False)
    assert not run()["public"]["listeners"]


def test_lsof_parser_ignores_malformed_remote_and_incomplete_records(scan, monkeypatch):
    _, _, run = scan
    bad = (b"f8\0tIPv4\0nexample.test:80\0TST=LISTEN\0\n"
           b"f9\0tIPv4\0n127.0.0.1:0\0TST=LISTEN\0\n"
           b"f10\0tIPv4\0n127.0.0.1:22->127.0.0.1:33\0TST=ESTABLISHED\0\n"
           b"f11\0tIPv4\0n127.0.0.1:99\0TST=LISTEN\0")
    monkeypatch.setattr(collector, "_read_lsof", lambda deadline: (LSOF + bad, True), raising=False)
    result = run()["public"]
    assert [row["port"] for row in result["listeners"]] == [43210, 43211, 43212]
    assert result["coverage"]["listeners"]["truncated"]


def test_lsof_missing_binary_is_explicitly_unavailable(scan, monkeypatch):
    _, _, run = scan
    def missing(deadline): raise FileNotFoundError()
    monkeypatch.setattr(collector, "_read_lsof", missing, raising=False)
    coverage = run()["public"]["coverage"]["listeners"]
    assert coverage["method"] == "lsof_polling" and coverage["state"] == "unavailable" and coverage["reason"]


def test_lsof_row_bound_and_duplicate_fields_rejected(scan, monkeypatch):
    _, _, run = scan
    payload = b"p10\0\n" + b"".join(
        b"f5\0tIPv4\0n127.0.0.1:" + str(port).encode() + b"\0TST=LISTEN\0\n"
        for port in range(10000, 10300))
    monkeypatch.setattr(collector, "_read_lsof", lambda deadline: (payload, False))
    result = run()["public"]
    assert len(result["listeners"]) == 256 and result["coverage"]["listeners"]["truncated"]
    duplicate = b"p10\0\nf5\0tIPv4\0n127.0.0.1:20\0n127.0.0.1:21\0TST=LISTEN\0\n"
    assert collector._lsof_listeners(duplicate, "scope", 256) == ([], True, False)


def test_malformed_process_header_cannot_reassign_prior_listener_owner():
    payload = (b"p10\0\nf5\0tIPv4\0n127.0.0.1:40000\0TST=LISTEN\0\n"
               b"p20\nf6\0tIPv4\0n127.0.0.1:40001\0TST=LISTEN\0\n"
               b"p30\0\nf7\0tIPv4\0n127.0.0.1:40002\0TST=LISTEN\0\n")
    rows, malformed, _ = collector._lsof_listeners(payload, "scope", 256)
    assert malformed
    assert [(row["pid"], row["port"]) for row in rows] == [(10, 40000), (30, 40002)]


@pytest.mark.parametrize("family,endpoint", [(b"IPv4", b"[127.0.0.1:40001"),
                                             (b"IPv6", b"::1]:40002"),
                                             (b"IPv4", b"[127.0.0.1]:40003"),
                                             (b"IPv6", b"::1:40004")])
def test_lsof_endpoint_brackets_must_match_documented_family(family, endpoint):
    payload = b"p10\0\nf5\0t" + family + b"\0n" + endpoint + b"\0TST=LISTEN\0\n"
    assert collector._lsof_listeners(payload, "scope", 256) == ([], True, False)


def test_lsof_method_changes_and_missing_partial_rows_never_remove(scan, monkeypatch):
    from tests.test_node_activity import Store
    sensor, clock, run = scan
    store = Store()
    try:
        sensor.error = None
        sensor.net_connections = lambda kind: [Obj(type=socket.SOCK_STREAM, status="LISTEN", laddr=("127.0.0.1", 43210), pid=10)]
        store.record_node_activity(run())
        def denied(kind): raise PermissionError()
        sensor.net_connections = denied
        monkeypatch.setattr(collector, "_read_lsof", lambda deadline: (LSOF, False))
        clock.now += 30
        first = store.record_node_activity(run())
        first_ids = {row["id"] for row in first["listeners"]}
        clock.now += 30
        assert first_ids == {row["id"] for row in run()["public"]["listeners"]}
        monkeypatch.setattr(collector, "_read_lsof", lambda deadline: (b"", False))
        assert store.record_node_activity(run())["events"] == []
        sensor.net_connections = lambda kind: []
        clock.now += 30
        assert store.record_node_activity(run())["events"] == []
    finally:
        store._conn.close()


@pytest.fixture
def lsof_child(monkeypatch):
    state = Obj(now=100.0, chunks=[], timeout=False, killed=False, closed=False, waits=[], argv=None)
    monkeypatch.setattr(collector.time, "monotonic", lambda: state.now)

    class Output:
        def fileno(self): return 123
        def close(self): state.closed = True

    class Child:
        stdout = Output()
        def poll(self): return -9 if state.killed else None
        def wait(self, timeout):
            state.waits.append(timeout)
            return 0
        def kill(self): state.killed = True

    def spawn(argv, **kwargs):
        state.argv, state.kwargs = argv, kwargs
        return Child()

    class Selector:
        def __enter__(self): return self
        def __exit__(self, *args): pass
        def register(self, file, events): pass
        def select(self, timeout):
            if state.timeout:
                state.now += timeout
                return []
            return [object()]

    def read(fd, size):
        assert fd == 123 and 0 < size <= 16384
        if not state.chunks:
            return b""
        data = state.chunks[0][:size]
        state.chunks[0] = state.chunks[0][size:]
        if not state.chunks[0]:
            state.chunks.pop(0)
        return data

    monkeypatch.setattr(collector.subprocess, "Popen", spawn)
    monkeypatch.setattr(collector.selectors, "DefaultSelector", Selector)
    monkeypatch.setattr(collector.os, "read", read)
    return state


def test_lsof_command_is_fixed_and_output_memory_bounded(lsof_child):
    state = lsof_child
    state.chunks = [b"x" * (collector.MAX_LSOF_BYTES + 80000)]
    data, limited = collector._read_lsof(103)
    assert limited and len(data) == 256 * 1024 and state.killed and state.closed
    assert state.argv == ["/usr/sbin/lsof", "-nP", "-a", "-iTCP", "-sTCP:LISTEN", "-F0pftnT"]
    assert state.kwargs["shell"] is False and state.kwargs["env"] == {"LC_ALL": "C"}
    assert state.kwargs["stderr"] == subprocess.DEVNULL and state.kwargs["stdin"] == subprocess.DEVNULL


@pytest.mark.parametrize("remaining", [0.25, 20])
def test_lsof_timeout_respects_remaining_budget_and_reaps_owned_child(lsof_child, remaining):
    state = lsof_child
    state.timeout = True
    assert collector._read_lsof(100 + remaining) == (b"", True)
    assert state.now == 100 + min(remaining, 0.75) and state.killed and state.closed
    assert state.waits == [0.1]


def test_lsof_does_not_spawn_after_budget_is_exhausted(lsof_child):
    with pytest.raises(TimeoutError):
        collector._read_lsof(99)
    assert lsof_child.argv is None


def test_actual_owned_process_listener_and_cpu_interval_reach_duckdb(tmp_path, monkeypatch):
    """Observe an owned process and listener through the actual local writer.

    AC-OBS-NODE-CLARITY-006.1

    Actual local component evidence only. Installed local and encrypted hosted
    views still require separate release acceptance; this guard cannot prove them.
    """
    pytest.importorskip("psutil")
    from tests.test_node_activity import Store
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("CLAWMETRY_AUDIT_DB", str(tmp_path / "audit.db"))
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "store.duckdb"))
    ready = tmp_path / "owned-listener-port"
    script = (
        "import pathlib,socket,sys,time; s=socket.socket(); "
        "s.bind(('127.0.0.1',0)); s.listen(1); "
        "pathlib.Path(sys.argv[1]).write_text(str(s.getsockname()[1])); "
        "deadline=time.monotonic()+15\n"
        "while time.monotonic()<deadline: sum(range(1000))\n"
    )
    child = subprocess.Popen([sys.executable, "-c", script, str(ready)],
                             stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    store = Store()
    try:
        deadline = time.monotonic() + 5
        while not ready.exists() and child.poll() is None and time.monotonic() < deadline:
            time.sleep(0.01)
        assert ready.exists(), "The owned loopback listener did not start within five seconds"
        port = int(ready.read_text())

        def observe():
            return collector.collect_node_activity(home=tmp_path, fingerprint_key=b"k" * 32,
                                                   node_id="isolated-owned-component-test")

        first = store.record_node_activity(observe())
        time.sleep(0.15)
        measured = store.record_node_activity(observe())
        process = next(row for row in measured["processes"] if row["pid"] == child.pid)
        warmup = next(row for row in first["processes"] if row["id"] == process["id"])
        assert warmup["cpu_percent"] is None and warmup["cpu_reason"]
        assert process["cpu_percent"] is not None and process["cpu_percent"] >= 0
        assert 0.1 <= process["cpu_interval_seconds"] <= 120 and not process["stale"]
        coverage = measured["coverage"]["listeners"]
        if coverage["state"] in ("unsupported", "unavailable"):
            pytest.skip("This account cannot read its owned listener: " + coverage["reason"])
        listener = next(row for row in measured["listeners"] if row["pid"] == child.pid and row["port"] == port)
        assert listener["address"] == "127.0.0.1" and listener["exposure"] == "loopback"
        assert not listener["stale"] and listener["actor"]["kind"] == process["actor"]["kind"] == "unknown"
    finally:
        if child.poll() is None:
            child.terminate()
        child.wait(timeout=3)
        store._conn.close()
