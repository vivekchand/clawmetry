"""MOAT Tier-1 sweep (2026-05-19 mandate) — daemon-proxy migration for
the last two routes that opened DuckDB directly.

Both endpoints used to call ``local_store.get_store(read_only=True)`` from
the dashboard process. On the standard launchd / systemd install where
the sync daemon owns the writer connection, DuckDB's exclusive file lock
blocked even read-only opens (per memory ``reference_duckdb_process_lock
.md``), so the routes silently degraded:

* ``/api/flow/runs`` — returned an empty list (``_source: 'empty'``) for
  every standard install. The Flow tab "Past flow runs" panel painted
  blank.
* ``/api/service-status`` — returned ``None`` from the fast path, forced
  fall-through to a live gateway port probe + ``pgrep`` on every poll.

The fix routes both through ``routes.local_query.local_store_via_daemon``
first, with a single-process direct-open fallback for tests / dev mode.
These tests pin BOTH behaviours so we don't regress:

1. With the daemon proxy mocked to return rows, the endpoint serves
   those rows (proves the daemon-proxy path is wired).
2. With the daemon proxy mocked to fail, the single-process fallback
   still answers from a tmp DuckDB (proves graceful degradation).
"""
from __future__ import annotations

import importlib
import time
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import pytest
from flask import Flask


def _wait_flush(store, t: float = 2.0) -> None:
    deadline = time.monotonic() + t
    while time.monotonic() < deadline:
        if store.health()["ring_depth"] == 0:
            return
        time.sleep(0.02)


def _iso(dt: datetime) -> str:
    return dt.isoformat()


# ── /api/flow/runs ────────────────────────────────────────────────────────


@pytest.fixture
def flow_runs_app(tmp_path, monkeypatch):
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "events.duckdb"))
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_SECS", "0.05")
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_BATCH", "5")
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_READ", "1")

    import clawmetry.local_store as ls
    importlib.reload(ls)
    import routes.infra as infra_mod
    importlib.reload(infra_mod)

    import dashboard as _d
    monkeypatch.setattr(_d, "_is_pro_user", lambda: True)  # bypass 24h cap

    a = Flask(__name__)
    a.register_blueprint(infra_mod.bp_logs)
    yield a, ls
    try:
        ls.get_store().stop(flush=True)
    except Exception:
        pass


def test_flow_runs_uses_daemon_proxy_when_available(flow_runs_app):
    """When ``local_store_via_daemon`` returns rows, /api/flow/runs
    surfaces them verbatim — proves the daemon-proxy code path is wired.
    """
    a, _ls = flow_runs_app
    fake_rows = [
        {
            "session_id":       "sess-via-daemon",
            "agent_id":         "main",
            "started_at":       "2026-05-19T10:00:00Z",
            "duration_seconds": 60.0,
            "event_count":      4,
            "tools_called":     2,
            "models_invoked":   1,
            "models":           ["claude-opus-4-7"],
            "total_cost":       0.45,
            "channels_touched": 1,
            "channel":          "telegram",
            "status":           "completed",
        }
    ]
    with patch(
        "routes.local_query.local_store_via_daemon",
        return_value=fake_rows,
    ) as mock:
        r = a.test_client().get("/api/flow/runs?limit=10")
    assert r.status_code == 200
    body = r.get_json()
    assert body["_source"] == "local_store"
    assert body["count"] == 1
    assert body["runs"][0]["session_id"] == "sess-via-daemon"
    # The daemon proxy MUST have been called with the right method name.
    assert mock.called
    assert mock.call_args.args[0] == "query_flow_runs"


def test_flow_runs_falls_back_to_direct_open_when_daemon_unreachable(
    flow_runs_app,
):
    """When the daemon proxy returns None (unreachable in tests), the
    single-process direct-open fallback still answers from the tmp DuckDB.
    """
    a, ls = flow_runs_app
    store = ls.get_store()
    now = datetime.now(timezone.utc)
    store.ingest({
        "id":         "fb-1",
        "node_id":    "n1",
        "agent_id":   "main",
        "session_id": "sess-fallback",
        "event_type": "message",
        "ts":         (now - timedelta(minutes=5)).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "data":       {"role": "user"},
        "cost_usd":   0.01,
        "token_count": 10,
        "model":      "claude-opus-4-7",
    })
    _wait_flush(store)

    with patch(
        "routes.local_query.local_store_via_daemon",
        return_value=None,  # Simulate daemon unreachable
    ):
        r = a.test_client().get("/api/flow/runs?limit=10")
    assert r.status_code == 200
    body = r.get_json()
    assert body["_source"] == "local_store"
    sids = {row["session_id"] for row in body["runs"]}
    assert "sess-fallback" in sids


# ── /api/service-status ───────────────────────────────────────────────────


@pytest.fixture
def health_app(tmp_path, monkeypatch):
    """Isolated Flask app with the health blueprint and a tmp DuckDB."""
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "clawmetry.duckdb"))
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_SECS", "0.05")
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_BATCH", "5")
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_READ", "1")

    # Match the existing fixture's dashboard stubbing.
    import sys
    import types
    mod = sys.modules.get("dashboard")
    if mod is None:
        mod = types.ModuleType("dashboard")
        sys.modules["dashboard"] = mod
    monkeypatch.setattr(mod, "SESSIONS_DIR", "/nonexistent/clawmetry-test-sessions", raising=False)
    monkeypatch.setattr(mod, "_load_gw_config", lambda: {}, raising=False)
    monkeypatch.setattr(mod, "_detect_gateway_port", lambda: 18789, raising=False)
    monkeypatch.setattr(mod, "_gw_invoke", lambda *a, **kw: None, raising=False)

    import clawmetry.local_store as ls
    importlib.reload(ls)
    import routes.health as hp
    importlib.reload(hp)

    a = Flask(__name__)
    a.register_blueprint(hp.bp_health)
    yield a, ls
    try:
        ls.get_store().stop(flush=True)
    except Exception:
        pass


def test_service_status_uses_daemon_proxy_for_heartbeats(health_app):
    """When the daemon proxy returns a heartbeat row, /api/service-status
    composes the response from it — proves the daemon-proxy path is wired
    for the heartbeats query.
    """
    a, _ls = health_app
    now = datetime.now(timezone.utc)
    fake_hb = [{
        "node_id": "agent+via-daemon",
        "ts":      _iso(now),
        "data":    {
            "gateway_up": True,
            "channels":   [
                {"name": "telegram", "connected": True},
            ],
        },
    }]

    # Track method names hit so we can assert query_heartbeats fires.
    calls: list = []

    def _fake_proxy(method, **kwargs):
        calls.append(method)
        if method == "query_heartbeats":
            return fake_hb
        if method == "query_system_snapshots":
            return []  # No snapshots → fall back to heartbeat data
        return None

    with patch(
        "routes.local_query.local_store_via_daemon",
        side_effect=_fake_proxy,
    ):
        r = a.test_client().get("/api/service-status")
    assert r.status_code == 200
    body = r.get_json()
    assert body["_source"] == "local_store"
    ss = body["service_status"]
    assert ss["sync"] is True
    assert ss["gateway"] is True
    names = {c["name"] for c in ss["channels"]}
    assert "telegram" in names
    # The heartbeats query MUST be served via the daemon proxy.
    assert "query_heartbeats" in calls


def test_service_status_falls_back_when_daemon_unreachable(health_app):
    """When daemon proxy returns None (unreachable), single-process
    direct-open fallback still composes the response from the tmp store.
    """
    a, ls = health_app
    store = ls.get_store()
    now = datetime.now(timezone.utc)
    store.ingest_heartbeat({
        "node_id":    "agent+local-fallback",
        "ts":         _iso(now),
        "version":    "0.12.247",
        "channels":   [{"name": "discord", "connected": True}],
        "gateway_up": True,
    })
    _wait_flush(store)

    with patch(
        "routes.local_query.local_store_via_daemon",
        return_value=None,  # Force fallback
    ):
        r = a.test_client().get("/api/service-status")
    assert r.status_code == 200
    body = r.get_json()
    assert body["_source"] == "local_store"
    names = {c["name"] for c in body["service_status"]["channels"]}
    assert "discord" in names


# ── Daemon allowlist regression guard ────────────────────────────────────


def test_query_flow_runs_is_in_daemon_allowlist():
    """Lock the daemon allowlist entry in place. PR #1258 → #1260 → #1266
    cascade burned us when a new route called ``local_store_via_daemon``
    for a method the allowlist didn't carry, and the daemon returned 400
    silently. The MOAT linter (``scripts/lint_daemon_allowlist.py``) is
    the primary gate, but a unit test surfaces the breakage faster in
    the test loop.
    """
    from routes.local_query import _DAEMON_METHODS
    assert "query_flow_runs" in _DAEMON_METHODS, (
        "query_flow_runs missing from _DAEMON_METHODS — /api/flow/runs "
        "will silently return empty results on multi-process installs."
    )
