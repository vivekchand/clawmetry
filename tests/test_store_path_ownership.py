"""A registered daemon only owns ITS DuckDB file — never proxy to it from a
process pointed at a different file.

Regression for 2026-08-19: ``pytest tests/test_alert_rules_local_store.py``
run on a dev box with the sync daemon up forwarded every fixture write into
the operator's LIVE ``~/.clawmetry/clawmetry.duckdb``. ``get_store()`` saw
``~/.clawmetry/local_query.json`` and handed the test a ``_ProxyStore`` even
though the fixture had pointed ``CLAWMETRY_LOCAL_STORE_PATH`` at a tmp file;
thirteen ``rule 0`` / ``owner-A`` / ``Via dispatch`` rows then rendered in the
Alerts tab as "unrecognized".

Three guards, all exercised here:
  * ``local_server.discovery_serves_this_db`` — the single predicate.
  * ``local_store._daemon_registered`` — ``get_store()`` opens the file
    directly when the daemon owns a different one.
  * ``routes.local_query._read_discovery`` — the HTTP proxy refuses too.
"""
from __future__ import annotations

import importlib
import json
import os
import sys

import pytest

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)


@pytest.fixture
def srv():
    from clawmetry import local_server
    return local_server


# ── the predicate ─────────────────────────────────────────────────────────────


def test_legacy_discovery_without_db_path_means_default_file(srv, tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.delenv("CLAWMETRY_LOCAL_STORE_PATH", raising=False)
    legacy = {"port": 1, "token": "t", "pid": 4242}
    # Process on the default file → the legacy daemon is ours.
    assert srv.discovery_serves_this_db(legacy) is True
    # Process on a scratch file → it is NOT ours.
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "scratch.duckdb"))
    assert srv.discovery_serves_this_db(legacy) is False


def test_discovery_db_path_must_match_process_path(srv, tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    mine = tmp_path / "mine.duckdb"
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(mine))
    assert srv.discovery_serves_this_db({"pid": 1, "db_path": str(mine)}) is True
    assert srv.discovery_serves_this_db({"pid": 1, "db_path": str(tmp_path / "other.duckdb")}) is False
    assert srv.discovery_serves_this_db({"pid": 1, "db_path": srv.default_db_path()}) is False
    # Explicit override beats the env-derived path.
    assert srv.discovery_serves_this_db({"pid": 1, "db_path": str(mine)},
                                        db_path=str(tmp_path / "x.duckdb")) is False
    # Garbage never raises; a missing payload reads as the default file.
    assert srv.discovery_serves_this_db(None) is False
    monkeypatch.delenv("CLAWMETRY_LOCAL_STORE_PATH")
    assert srv.discovery_serves_this_db(None) is True


def test_discovery_file_records_db_path(srv, tmp_path, monkeypatch):
    db = tmp_path / "events.duckdb"
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(db))
    monkeypatch.setenv("HOME", str(tmp_path))
    import clawmetry.local_store as ls
    importlib.reload(ls)
    monkeypatch.setattr(srv, "DISCOVERY_PATH", tmp_path / "local_query.json", raising=False)
    srv._write_discovery_file(12345, "tok")
    disc = json.loads((tmp_path / "local_query.json").read_text())
    assert disc["port"] == 12345 and disc["pid"] == os.getpid()
    assert os.path.realpath(disc["db_path"]) == os.path.realpath(str(db))
    assert srv.discovery_serves_this_db(disc) is True


# ── get_store(): opens the fixture file, never the daemon's ───────────────────


def _fake_daemon_discovery(home, *, db_path=None, pid=None):
    d = home / ".clawmetry"
    d.mkdir(parents=True, exist_ok=True)
    payload = {"port": 1, "token": "x" * 32, "pid": pid or (os.getpid() + 100000)}
    if db_path is not None:
        payload["db_path"] = str(db_path)
    (d / "local_query.json").write_text(json.dumps(payload))


def test_get_store_ignores_daemon_that_owns_a_different_file(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    mine = tmp_path / "fixture.duckdb"
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(mine))
    # A "live" daemon (different pid) on the DEFAULT file. Legacy discovery
    # shape (no db_path) — the exact file the 2026-08-19 leak went through.
    _fake_daemon_discovery(tmp_path)

    sys.modules.pop("clawmetry.local_store", None)
    import clawmetry.local_store as ls
    importlib.reload(ls)
    ls._reset_singleton_for_tests()
    try:
        assert ls._daemon_registered() is False
        store = ls.get_store()
        assert isinstance(store, ls.LocalStore), type(store)
        assert not isinstance(store, ls._ProxyStore)
        store.ingest_alert_rule({
            "id": "fixture-rule", "owner_hash": "owner-A",
            "name": "must stay in tmp",
            "condition_json": {"alert_type": "daily_spend"}, "enabled": True,
        })
        assert [r["id"] for r in store.query_alert_rules()] == ["fixture-rule"]
        assert mine.exists()
    finally:
        ls._reset_singleton_for_tests()


def test_get_store_still_proxies_when_daemon_owns_our_file(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    mine = tmp_path / "shared.duckdb"
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(mine))
    _fake_daemon_discovery(tmp_path, db_path=mine)

    sys.modules.pop("clawmetry.local_store", None)
    import clawmetry.local_store as ls
    importlib.reload(ls)
    ls._reset_singleton_for_tests()
    try:
        assert ls._daemon_registered() is True
        assert isinstance(ls.get_store(), ls._ProxyStore)
    finally:
        ls._reset_singleton_for_tests()


# ── routes.local_query: the HTTP proxy refuses too ────────────────────────────


def test_read_discovery_refuses_daemon_on_other_file(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "fixture.duckdb"))
    disc_path = tmp_path / "local_query.json"
    # Own pid → passes the liveness probe; only the ownership check can veto.
    disc_path.write_text(json.dumps({"port": 65001, "token": "y" * 32, "pid": os.getpid()}))
    import routes.local_query as lq
    importlib.reload(lq)
    monkeypatch.setattr(lq, "_DISCOVERY_PATH", str(disc_path))
    assert lq._read_discovery() is None

    disc_path.write_text(json.dumps({"port": 65001, "token": "y" * 32, "pid": os.getpid(),
                                     "db_path": str(tmp_path / "fixture.duckdb")}))
    assert lq._read_discovery() == {"port": 65001, "token": "y" * 32}


def test_conftest_isolates_the_session_store_path():
    """Every in-process test runs against a scratch DuckDB unless it chose
    its own path — the suite can no longer touch ``~/.clawmetry``."""
    p = os.environ.get("CLAWMETRY_LOCAL_STORE_PATH", "")
    assert p, "conftest must set CLAWMETRY_LOCAL_STORE_PATH for the session"
    from clawmetry.local_server import default_db_path
    assert os.path.realpath(p) != os.path.realpath(default_db_path())
