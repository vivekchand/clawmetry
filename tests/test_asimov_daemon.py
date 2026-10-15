"""Exercise journal ingestion lifecycle and writer/query/snapshot boundaries.

No robot state is inserted and no SDK, hardware or listening socket is needed.
REQ-ASIMOV-001/005/006: automatic local tailing is not a robot connection.
"""
import builtins
import socket
import threading

import pytest


@pytest.fixture(scope="session", autouse=True)
def server():
    yield None


@pytest.fixture
def writer(tmp_path, monkeypatch):
    from clawmetry import local_store

    path = tmp_path / "daemon.duckdb"
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(path))
    monkeypatch.setattr(local_store, "DB_PATH", path)
    store = local_store.LocalStore()
    yield store
    store.stop()


@pytest.fixture
def daemon(tmp_path, monkeypatch):
    from clawmetry.asimov import daemon

    assert daemon._worker is None or not daemon._worker.is_alive()
    monkeypatch.setattr(daemon, "_worker", None)
    monkeypatch.setattr(daemon, "_lock", threading.Lock())
    monkeypatch.setattr(daemon, "_stop", threading.Event())
    directory = tmp_path / "journal"
    directory.mkdir()
    monkeypatch.setenv("CLAWMETRY_ROBOTICS_DIR", str(directory))
    yield daemon
    daemon.stop()


def test_start_only_tails_existing_journals_without_sdk_pro_or_connection(
        daemon, writer, monkeypatch):
    from clawmetry.asimov.store import AsimovLocalStore

    entered = threading.Event()
    ingest = AsimovLocalStore.ingest
    imported = builtins.__import__

    def reject_optional_import(name, *args, **kwargs):
        forbidden = ("menlo", "livekit", "clawmetry_pro", "clawmetry.asimov.sdk",
                     "clawmetry.asimov.observer")
        if any(name == prefix or name.startswith(prefix + ".") for prefix in forbidden):
            raise AssertionError("Journal tailing imported optional robot code: " + name)
        return imported(name, *args, **kwargs)

    def reject_connection(*args, **kwargs):
        raise AssertionError("Journal ingestion attempted a network connection")

    def observed_ingest(self, directory, **kwargs):
        result = ingest(self, directory, **kwargs)
        entered.set()
        return result

    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    monkeypatch.setattr(builtins, "__import__", reject_optional_import)
    monkeypatch.setattr(socket, "create_connection", reject_connection)
    monkeypatch.setattr(AsimovLocalStore, "ingest", observed_ingest)
    daemon.start(writer)
    assert entered.wait(3), "actual journal worker did not complete a tail pass"
    assert daemon._worker.is_alive()
    assert AsimovLocalStore(writer).runs()["runs"] == []
    first_worker = daemon._worker
    daemon.start(writer)
    assert daemon._worker is first_worker, "repeated startup duplicated the ingestion worker"


def test_transient_ingest_failure_retries_on_the_same_live_worker(
        daemon, writer, monkeypatch, caplog):
    from clawmetry.asimov.store import AsimovLocalStore

    recovered = threading.Event()
    attempts = []
    ingest = AsimovLocalStore.ingest

    def fail_once(self, directory, **kwargs):
        attempts.append(threading.get_ident())
        if len(attempts) == 1:
            raise OSError("temporary test journal read failure")
        result = ingest(self, directory, **kwargs)
        recovered.set()
        return result

    monkeypatch.setattr(AsimovLocalStore, "ingest", fail_once)
    daemon.start(writer)
    worker = daemon._worker
    assert recovered.wait(4), "worker did not retry after the transient journal error"
    assert len(attempts) >= 2 and len(set(attempts)) == 1
    assert daemon._worker is worker and worker.is_alive()
    assert "collector will try again" in caplog.text


def test_start_replaces_an_actually_terminated_thread(daemon, writer, monkeypatch):
    from clawmetry.asimov.store import AsimovLocalStore

    ended = threading.Thread(target=lambda: None)
    ended.start()
    ended.join(timeout=3)
    assert not ended.is_alive(), "a terminated Thread must report its actual state"
    monkeypatch.setattr(daemon, "_worker", ended)
    ingested = threading.Event()
    ingest = AsimovLocalStore.ingest

    def observe(self, directory, **kwargs):
        result = ingest(self, directory, **kwargs)
        ingested.set()
        return result

    monkeypatch.setattr(AsimovLocalStore, "ingest", observe)
    daemon.start(writer)
    assert ingested.wait(3)
    assert daemon._worker is not ended
    assert daemon._worker.is_alive()


def test_dashboard_read_proxy_dispatches_authenticated_rpc_to_existing_writer(
        writer, monkeypatch):
    from clawmetry import local_server, local_store
    from clawmetry.asimov.store import AsimovLocalStore
    from routes import asimov, local_query

    AsimovLocalStore(writer, initialize=True)
    monkeypatch.setattr(local_query, "_store", lambda: writer)
    monkeypatch.setattr(local_server, "_token", "isolated-daemon-test-token")
    daemon_http = local_server._make_app().test_client()
    calls = []

    def in_process_transport(method, **kwargs):
        calls.append((method, kwargs))
        response = daemon_http.post("/__local_query__/" + method,
            headers={"Authorization": "Bearer isolated-daemon-test-token"},
            json={"kwargs": kwargs})
        assert response.status_code == 200
        return response.json["result"]

    def reject_new_connection(*args, **kwargs):
        raise AssertionError("The dashboard must not open another DuckDB connection")

    monkeypatch.setattr(local_store, "_store_rw", None)
    monkeypatch.setattr(local_store, "_store_ro", None)
    monkeypatch.setattr(local_store, "_store_proxy", None)
    monkeypatch.setattr(local_store, "_writer_owner", False)
    monkeypatch.setenv("CLAWMETRY_ROLE", "dashboard")
    monkeypatch.setattr(local_store, "_open_connection", reject_new_connection)
    monkeypatch.setattr(local_query, "local_store_via_daemon", in_process_transport)
    assert asimov._call("query_asimov_runs", limit=3)["runs"] == []
    assert calls == [("query_asimov_runs", {"limit": 3})]
    assert isinstance(local_store.get_store(read_only=True), local_store._ProxyStore)
    assert local_store._store_rw is None and local_store._store_ro is None
    assert writer._fetch("SELECT count(*) FROM asimov_runs", [])[0][0] == 0


def test_snapshot_reads_existing_writer_without_view_or_journal_scan(writer, monkeypatch):
    from clawmetry.asimov import daemon
    from clawmetry.asimov.store import AsimovLocalStore

    AsimovLocalStore(writer, initialize=True)

    def reject_ingest(*args, **kwargs):
        raise AssertionError("Snapshot building must not ingest journals or invoke a view")

    monkeypatch.setattr(AsimovLocalStore, "ingest", reject_ingest)
    monkeypatch.setattr(daemon, "journal_directory", reject_ingest)
    snapshot = daemon.snapshot(writer)
    assert snapshot["schema"] == "clawmetry.asimov.snapshot.v1"
    assert snapshot["runs"] == []
    assert isinstance(snapshot["generated_at_ns"], str)
    assert writer._fetch("SELECT count(*) FROM asimov_events", [])[0][0] == 0
