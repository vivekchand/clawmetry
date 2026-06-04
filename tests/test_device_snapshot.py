"""Tests for the device snapshot endpoint (routes/device.py).

The device snapshot is the compact, all-runtime payload a hardware companion
(ESP32) polls. It must:
  1. Always return a well-formed shape, even on an empty store (never crash —
     a device must always get a valid payload).
  2. Count active sessions across runtimes and surface the OLDEST pending
     approval with its tool action + runtime.
  3. Flip overall health to ``amber`` when a human is needed (firing alert or
     waiting approval).
"""

from __future__ import annotations

import importlib

import pytest
from flask import Flask


@pytest.fixture
def device_app(tmp_path, monkeypatch):
    """Flask app with bp_device on a hermetic tmp DuckDB store."""
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "events.duckdb"))
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_SECS", "0.05")
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_BATCH", "5")
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_READ", "1")

    import clawmetry.local_store as ls
    importlib.reload(ls)
    # Force this process to own the writer so the fixture's tmp store opens
    # here instead of being proxied to a dev machine's running daemon.
    ls.mark_writer_owner()

    # The handler reads through local_store_via_daemon; stub discovery so it
    # falls through to the in-process read-only open.
    import routes.local_query as lq
    monkeypatch.setattr(lq, "_read_discovery", lambda: None)
    monkeypatch.setattr(lq, "_cached_discovery", lambda: None)

    import routes.device as dev
    importlib.reload(dev)
    # Defeat the TTL cache between assertions within one test.
    dev._snapshot_cache["payload"] = None
    dev._snapshot_cache["ts"] = 0.0

    a = Flask(__name__)
    a.register_blueprint(dev.bp_device)
    yield a, ls, dev
    try:
        ls.get_store().stop(flush=True)
    except Exception:
        pass


def _expected_keys():
    return (
        "schema", "generated_at", "cost_today_usd", "tokens_today",
        "active_sessions", "runtimes_active", "health", "alert", "approval",
    )


def test_empty_store_returns_valid_zero_payload(device_app):
    """No data → a well-formed, all-zero payload (the device never sees a 500
    or a missing field)."""
    a, _ls, _dev = device_app
    r = a.test_client().get("/api/device/snapshot")
    assert r.status_code == 200, r.get_data(as_text=True)[:300]
    body = r.get_json()
    for k in _expected_keys():
        assert k in body, f"missing key: {k}"
    assert body["schema"] == 1
    assert body["active_sessions"] == 0
    assert body["runtimes_active"] == []
    assert body["alert"] is None
    assert body["approval"] is None
    assert body["health"] == "green"
    assert isinstance(body["cost_today_usd"], (int, float))
    assert isinstance(body["tokens_today"], int)


def test_active_sessions_counted(device_app):
    """Only status=='active' sessions are counted."""
    a, ls, _dev = device_app
    store = ls.get_store()
    store.ingest_session({
        "session_id": "sess-active",
        "agent_type": "openclaw",
        "status": "active",
        "started_at": "2026-06-04T10:00:00+00:00",
        "last_active_at": "2026-06-04T11:00:00+00:00",
    })
    store.ingest_session({
        "session_id": "sess-ended",
        "agent_type": "openclaw",
        "status": "ended",
        "started_at": "2026-06-03T09:00:00+00:00",
        "last_active_at": "2026-06-03T10:00:00+00:00",
    })
    body = a.test_client().get("/api/device/snapshot").get_json()
    assert body["active_sessions"] == 1
    # OSS-Free resolves every prefix to openclaw; the runtime list is still
    # derived per-session, so the all-runtime wiring is exercised.
    assert body["runtimes_active"] == ["openclaw"]


def test_oldest_pending_approval_surfaces_and_flips_health(device_app):
    """The OLDEST pending approval is surfaced (not the newest), with its tool
    action + runtime, and overall health goes amber while a human is needed."""
    a, ls, _dev = device_app
    store = ls.get_store()
    store.ingest_approval({
        "id": "app-new",
        "requestor_session_id": "sess-A",
        "action": "write_file",
        "status": "pending",
        "created_at": "2026-06-04T10:05:00+00:00",
    })
    store.ingest_approval({
        "id": "app-old",
        "requestor_session_id": "sess-A",
        "action": "bash",
        "status": "pending",
        "created_at": "2026-06-04T10:00:00+00:00",  # older
    })
    store.ingest_approval({
        "id": "app-done",
        "requestor_session_id": "sess-A",
        "action": "delete",
        "status": "approved",
        "created_at": "2026-06-04T09:00:00+00:00",  # resolved, ignored
    })

    body = a.test_client().get("/api/device/snapshot").get_json()
    assert body["approval"] is not None
    assert body["approval"]["id"] == "app-old"  # oldest pending, not newest
    assert body["approval"]["action"] == "bash"
    assert body["approval"]["runtime"] == "openclaw"
    # Waiting on a human → amber (unless something is broken → red).
    assert body["health"] in ("amber", "red")
