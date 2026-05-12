"""Tests for the daemon-hosted local query server + dashboard proxy.

Covers the cross-process DuckDB lock fix:
  - Daemon spawns local_server, writes discovery file (port + token + pid)
  - Dashboard's _dispatch() reads the file, forwards over HTTP
  - Auth: requests without the Bearer token return 401
  - Liveness: dead PID in the discovery file → discovery returns None,
    dashboard falls back to direct DuckDB
  - End-to-end: spawn local_server in this process, hit it via
    routes.local_query._proxy_dispatch — confirm same data shape as
    direct dispatch
"""

from __future__ import annotations

import importlib
import json
import os
import time
import uuid

import pytest
import requests


@pytest.fixture
def isolated_store(tmp_path, monkeypatch):
    """Fresh DuckDB + reset all module-level singletons. Uses get_store()
    so the singleton is registered — needed for the in-process local_server
    to share the writer connection (DuckDB rejects mixed RW+RO opens of
    the same file in the same process)."""
    db = tmp_path / "events.duckdb"
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(db))
    monkeypatch.setenv("HOME", str(tmp_path))
    import clawmetry.local_store as ls
    importlib.reload(ls)
    ls._reset_singleton_for_tests()
    s = ls.get_store(read_only=False)  # registers singleton
    # Seed a couple events
    for i in range(3):
        s.ingest({
            "id": f"e{i}-{uuid.uuid4()}",
            "node_id": "agent+test",
            "agent_id": "main",
            "event_type": "tool_call",
            "ts": int(time.time() * 1000),
        })
    time.sleep(0.2)  # let the flusher catch up
    yield s
    s.stop(flush=True)
    ls._reset_singleton_for_tests()


def test_discovery_file_round_trip(isolated_store, tmp_path, monkeypatch):
    """local_server.start() writes discovery file with port+token+pid."""
    monkeypatch.setattr(
        "clawmetry.local_server.DISCOVERY_PATH",
        tmp_path / "local_query.json",
    )
    import clawmetry.local_server as srv
    importlib.reload(srv)
    monkeypatch.setattr(
        srv, "DISCOVERY_PATH", tmp_path / "local_query.json", raising=False,
    )
    port = srv.start()
    try:
        assert port and isinstance(port, int)
        # Discovery file present + correct shape
        disc = json.loads((tmp_path / "local_query.json").read_text())
        assert disc["port"] == port
        assert disc["pid"] == os.getpid()
        assert len(disc["token"]) == 32
        # File mode 0600
        assert oct((tmp_path / "local_query.json").stat().st_mode & 0o777) == "0o600"
    finally:
        srv._cleanup_discovery_file()


def test_server_rejects_unauthenticated(isolated_store, tmp_path, monkeypatch):
    """Hits without Bearer token → 401."""
    monkeypatch.setattr(
        "clawmetry.local_server.DISCOVERY_PATH",
        tmp_path / "local_query.json",
        raising=False,
    )
    import clawmetry.local_server as srv
    importlib.reload(srv)
    monkeypatch.setattr(srv, "DISCOVERY_PATH", tmp_path / "local_query.json", raising=False)
    port = srv.start()
    try:
        # Wait for server up
        time.sleep(0.3)
        # No auth header
        r = requests.post(
            f"http://127.0.0.1:{port}/api/local/query",
            json={"shape": "health", "args": {}},
            timeout=2,
        )
        assert r.status_code == 401
        # Wrong token
        r = requests.post(
            f"http://127.0.0.1:{port}/api/local/query",
            json={"shape": "health", "args": {}},
            headers={"Authorization": "Bearer bogus"},
            timeout=2,
        )
        assert r.status_code == 401
        # Right token works
        r = requests.post(
            f"http://127.0.0.1:{port}/api/local/query",
            json={"shape": "health", "args": {}},
            headers={"Authorization": f"Bearer {srv.get_token()}"},
            timeout=2,
        )
        assert r.status_code == 200
        assert "_shape" in r.json()
    finally:
        srv._cleanup_discovery_file()


def test_proxy_loopbreak_when_running_in_daemon(isolated_store, tmp_path, monkeypatch):
    """Sanity check on the loop-break: when local_server is running in
    THIS process (the daemon case), _proxy_dispatch must refuse to
    forward — otherwise it'd hit its own handler and recurse."""
    monkeypatch.setattr(
        "clawmetry.local_server.DISCOVERY_PATH",
        tmp_path / "local_query.json",
        raising=False,
    )
    import clawmetry.local_server as srv
    importlib.reload(srv)
    monkeypatch.setattr(srv, "DISCOVERY_PATH", tmp_path / "local_query.json", raising=False)
    srv.start()
    try:
        time.sleep(0.3)
        import routes.local_query as lq
        importlib.reload(lq)
        monkeypatch.setattr(lq, "_DISCOVERY_PATH", str(tmp_path / "local_query.json"))
        # Loop-break should fire and skip the proxy hop entirely
        with pytest.raises(RuntimeError, match="in-daemon"):
            lq._proxy_dispatch("events", {"limit": 10})
        # And _dispatch should fall through to direct
        result = lq._dispatch("health", {})
        assert result["_via"] == "direct"
    finally:
        srv._cleanup_discovery_file()


def test_proxy_falls_back_when_daemon_dead(isolated_store, tmp_path, monkeypatch):
    """If discovery file references a dead PID, _dispatch should fall
    back to direct DuckDB (no crash, no 5s wait)."""
    # Write a bogus discovery file with a definitely-dead PID
    disc_path = tmp_path / "local_query.json"
    disc_path.write_text(json.dumps({
        "port": 65000, "token": "x" * 32, "pid": 999999,  # almost certainly not alive
    }))
    import routes.local_query as lq
    importlib.reload(lq)
    monkeypatch.setattr(lq, "_DISCOVERY_PATH", str(disc_path))
    started = time.monotonic()
    result = lq._dispatch("events", {"limit": 5})
    elapsed = time.monotonic() - started
    assert result["_via"] == "direct"
    assert elapsed < 1.0, f"Fallback took {elapsed:.2f}s — should be near-instant"


def test_proxy_falls_back_when_no_discovery(tmp_path, monkeypatch):
    """No discovery file at all → direct fallback."""
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "events.duckdb"))
    import clawmetry.local_store as ls
    importlib.reload(ls)
    ls._reset_singleton_for_tests()
    # Bootstrap the file
    s = ls.LocalStore(read_only=False)
    s.start()
    s.ingest({"id": "e", "node_id": "n", "event_type": "x", "ts": int(time.time() * 1000)})
    time.sleep(0.2)
    s.stop(flush=True)
    importlib.reload(ls)
    ls._reset_singleton_for_tests()

    import routes.local_query as lq
    importlib.reload(lq)
    monkeypatch.setattr(lq, "_DISCOVERY_PATH", str(tmp_path / "nonexistent.json"))
    result = lq._dispatch("health", {})
    assert result["_via"] == "direct"
