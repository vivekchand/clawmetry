"""Tests for epic #964 — local-store fast paths on 5 Health/Reliability routes.

Routes covered:
  GET /api/reliability       — derived from heartbeats + events
  GET /api/sandbox-status    — read from system_snapshots(kind='sandbox')
  GET /api/mcp-stats         — aggregated from events(event_type='mcp_call')
  GET /api/loop-detection    — derived from rapid-repeat tool_call events
  GET /api/service-status    — composite from heartbeats + system_snapshots

Each route's fast path is opt-in via CLAWMETRY_LOCAL_STORE_READ=1. Without
that flag every route falls through to the legacy implementation — pinned
by the dedicated `*_falls_back_when_env_unset` tests. We don't exercise
the legacy paths' detail (those are covered elsewhere); we just confirm
the fast path doesn't fire when the flag is missing.
"""

from __future__ import annotations

import importlib
import sys
import time
import types
from datetime import datetime, timedelta, timezone

import pytest
from flask import Flask


def _iso(dt: datetime) -> str:
    return dt.isoformat()


def _wait_flush(store, t: float = 2.0) -> None:
    """Block until the in-memory ring buffer has drained to DuckDB."""
    deadline = time.monotonic() + t
    while time.monotonic() < deadline:
        if store.health()["ring_depth"] == 0:
            return
        time.sleep(0.02)


def _stub_dashboard() -> None:
    """Install a tiny stub `dashboard` module so routes/health.py's late
    `import dashboard as _d` succeeds inside the test process. The stub
    only needs the attributes the LEGACY paths reach for — the fast paths
    we test never touch `_d`. We still set the attributes the fast paths
    SOMETIMES read (e.g. `SESSIONS_DIR`) to /nonexistent so any accidental
    fall-through fails fast instead of scanning the user's real workspace.
    """
    if "dashboard" in sys.modules:
        return
    stub = types.ModuleType("dashboard")
    # Reliability legacy path needs these — set to None so it returns the
    # "History module not available" branch if the fast path defers.
    stub._history_db = None
    stub.AgentReliabilityScorer = None
    # Sandbox / loop / mcp / service-status legacy paths need these.
    stub.SESSIONS_DIR = "/nonexistent/clawmetry-test-sessions"
    stub._detect_sandbox_metadata = lambda: None
    stub._detect_inference_metadata = lambda: None
    stub._detect_security_metadata = lambda: None
    stub._load_gw_config = lambda: {}
    stub._detect_gateway_port = lambda: 18789
    stub._gw_invoke = lambda *a, **kw: None
    sys.modules["dashboard"] = stub


@pytest.fixture
def app(tmp_path, monkeypatch):
    """Isolated Flask app with the health blueprint and a tmp DuckDB.

    ``CLAWMETRY_LOCAL_STORE_READ=1`` is set so the fast path is active for
    every test that uses this fixture; the dedicated negative tests build
    their own app without the flag.
    """
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "clawmetry.duckdb"))
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_SECS", "0.05")
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_BATCH", "5")
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_READ", "1")

    _stub_dashboard()

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


# ─────────────────────────────────────────────────────────────────────────────
# /api/reliability
# ─────────────────────────────────────────────────────────────────────────────


def test_reliability_fast_path_serves_from_local_store(app):
    """Heartbeats + a couple of error events → fast path returns the
    documented reliability shape with _source=local_store."""
    a, ls = app
    store = ls.get_store()

    now = datetime.now(timezone.utc)
    # 5 days × 4 heartbeats per day, no errors → delivery=1.0 across the window.
    for d in range(5):
        for h in range(4):
            store.ingest_heartbeat({
                "node_id": "agent+test",
                "ts": _iso(now - timedelta(days=d, hours=h)),
                "version": "0.12.162",
                "e2e": True,
            })
    # A small set of events to make sure the events path is exercised.
    for i in range(3):
        store.ingest({
            "id": f"ev-ok-{i}",
            "node_id": "agent+test",
            "session_id": "sess-r1",
            "event_type": "tool_call",
            "ts": _iso(now - timedelta(days=i)),
        })
    _wait_flush(store)

    r = a.test_client().get("/api/reliability?window=7")
    assert r.status_code == 200, r.get_data(as_text=True)[:300]
    body = r.get_json()

    assert body["_source"] == "local_store"
    assert body["window_days"] == 7
    assert body["session_count"] >= 1
    assert body["direction"] in {"improving", "degrading", "stable", "insufficient_data"}
    assert "points" in body and isinstance(body["points"], list)
    # Pure-OK window → success_rate should be 1.0, error_rate 0.0.
    assert body["success_rate"] == 1.0
    assert body["error_rate"] == 0.0
    # Every point should carry the per-day rates.
    for p in body["points"]:
        assert "ts" in p and "delivery" in p and "error_rate" in p


def test_reliability_picks_up_error_events(app):
    """A burst of error events should drag error_rate above 0.0."""
    a, ls = app
    store = ls.get_store()
    now = datetime.now(timezone.utc)
    # Mix: 4 ok, 4 errors on the same day.
    for i in range(4):
        store.ingest({
            "id": f"ev-ok-{i}",
            "node_id": "agent+test",
            "session_id": "sess-r2",
            "event_type": "tool_call",
            "ts": _iso(now - timedelta(minutes=i)),
        })
    for i in range(4):
        store.ingest({
            "id": f"ev-err-{i}",
            "node_id": "agent+test",
            "session_id": "sess-r2",
            "event_type": "tool_error",
            "ts": _iso(now - timedelta(minutes=10 + i)),
        })
    _wait_flush(store)

    r = a.test_client().get("/api/reliability?window=30")
    assert r.status_code == 200
    body = r.get_json()
    assert body["_source"] == "local_store"
    assert body["error_rate"] > 0.0
    assert body["success_rate"] < 1.0


def test_reliability_falls_back_when_env_unset(tmp_path, monkeypatch):
    """No CLAWMETRY_LOCAL_STORE_READ → fast path never runs even with a
    populated heartbeats table. Legacy path gets the request and returns
    the 'History module not available' branch (because we stub
    _history_db=None)."""
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "clawmetry.duckdb"))
    monkeypatch.delenv("CLAWMETRY_LOCAL_STORE_READ", raising=False)
    _stub_dashboard()

    import clawmetry.local_store as ls
    importlib.reload(ls)
    import routes.health as hp
    importlib.reload(hp)

    store = ls.get_store()
    store.ingest_heartbeat({
        "node_id": "agent+x",
        "ts": _iso(datetime.now(timezone.utc)),
        "version": "0.12.162",
        "e2e": True,
    })

    a = Flask(__name__)
    a.register_blueprint(hp.bp_health)
    body = a.test_client().get("/api/reliability").get_json()
    assert body.get("_source") != "local_store"
    try:
        store.stop(flush=True)
    except Exception:
        pass


# ─────────────────────────────────────────────────────────────────────────────
# /api/sandbox-status
# ─────────────────────────────────────────────────────────────────────────────


def test_sandbox_status_fast_path_returns_snapshot_data(app):
    """A 'sandbox' kind snapshot in DuckDB → fast path returns its
    payload, normalised to the canonical shape."""
    a, ls = app
    store = ls.get_store()
    store.ingest_system_snapshot({
        "node_id": "agent+test",
        "ts": _iso(datetime.now(timezone.utc)),
        "kind": "sandbox",
        "sandbox": {
            "name": "nemoclaw-prod",
            "status": "running",
            "type": "nemoclaw",
        },
        "inference": {
            "provider": "Anthropic",
            "model": "claude-opus-4-7",
        },
        "security": {
            "sandbox_enabled": True,
            "network_policy": "deny",
        },
    })

    r = a.test_client().get("/api/sandbox-status")
    assert r.status_code == 200
    body = r.get_json()
    assert body["_source"] == "local_store"
    assert body["sandbox"]["name"] == "nemoclaw-prod"
    assert body["sandbox"]["status"] == "running"
    assert body["sandbox"]["type"] == "nemoclaw"
    assert body["inference"]["provider"] == "Anthropic"
    assert body["inference"]["model"] == "claude-opus-4-7"
    assert body["security"]["sandbox_enabled"] is True
    assert body["security"]["network_policy"] == "deny"


def test_sandbox_status_falls_back_when_env_unset(tmp_path, monkeypatch):
    """No env flag → never read from DuckDB even with a fresh snapshot."""
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "clawmetry.duckdb"))
    monkeypatch.delenv("CLAWMETRY_LOCAL_STORE_READ", raising=False)
    _stub_dashboard()

    import clawmetry.local_store as ls
    importlib.reload(ls)
    import routes.health as hp
    importlib.reload(hp)

    store = ls.get_store()
    store.ingest_system_snapshot({
        "node_id": "agent+x",
        "ts": _iso(datetime.now(timezone.utc)),
        "kind": "sandbox",
        "sandbox": {"name": "should-not-show", "type": "docker"},
    })

    a = Flask(__name__)
    a.register_blueprint(hp.bp_health)
    body = a.test_client().get("/api/sandbox-status").get_json()
    assert body.get("_source") != "local_store"
    # Legacy path with our stubbed _detect_*=None returns nulls.
    assert body["sandbox"] is None
    assert body["inference"] is None
    assert body["security"] is None
    try:
        store.stop(flush=True)
    except Exception:
        pass


# ─────────────────────────────────────────────────────────────────────────────
# /api/mcp-stats
# ─────────────────────────────────────────────────────────────────────────────


def test_mcp_stats_fast_path_aggregates_from_events(app):
    """A handful of mcp_call events → the fast path returns per-tool
    counts/errors/avg_latency_ms."""
    a, ls = app
    store = ls.get_store()
    base = datetime.now(timezone.utc)

    for i in range(5):
        store.ingest({
            "id": f"mcp-search-{i}",
            "node_id": "agent+test",
            "session_id": f"sess-{i % 2}",
            "event_type": "mcp_call",
            "ts": _iso(base - timedelta(seconds=i)),
            "data": {
                "name": "mcp.search",
                "latency_ms": 120 + i * 10,
                "is_error": False,
            },
        })
    # One error to bump the rate.
    store.ingest({
        "id": "mcp-search-err",
        "node_id": "agent+test",
        "session_id": "sess-0",
        "event_type": "mcp_call",
        "ts": _iso(base - timedelta(seconds=10)),
        "data": {"name": "mcp.search", "is_error": True},
    })
    # A second tool with one call.
    store.ingest({
        "id": "mcp-fetch-0",
        "node_id": "agent+test",
        "session_id": "sess-1",
        "event_type": "mcp_call",
        "ts": _iso(base - timedelta(seconds=15)),
        "data": {"name": "mcp.fetch", "latency_ms": 80},
    })
    # A built-in name should be filtered out.
    store.ingest({
        "id": "mcp-bash-0",
        "node_id": "agent+test",
        "session_id": "sess-1",
        "event_type": "mcp_call",
        "ts": _iso(base - timedelta(seconds=20)),
        "data": {"name": "Bash"},
    })
    _wait_flush(store)

    r = a.test_client().get("/api/mcp-stats")
    assert r.status_code == 200
    body = r.get_json()
    assert body["_source"] == "local_store"
    assert body["checked"] == 2  # two distinct sessions saw mcp calls
    by_name = {t["name"]: t for t in body["tools"]}
    assert "mcp.search" in by_name
    assert "mcp.fetch" in by_name
    assert "Bash" not in by_name  # built-ins are filtered
    assert by_name["mcp.search"]["calls"] == 6
    assert by_name["mcp.search"]["errors"] == 1
    assert by_name["mcp.search"]["error_rate_pct"] > 0
    assert by_name["mcp.search"]["avg_latency_ms"] is not None
    # mcp.search appeared more often → first in sorted output.
    assert body["tools"][0]["name"] == "mcp.search"


def test_mcp_stats_falls_back_when_env_unset(tmp_path, monkeypatch):
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "clawmetry.duckdb"))
    monkeypatch.delenv("CLAWMETRY_LOCAL_STORE_READ", raising=False)
    _stub_dashboard()

    import clawmetry.local_store as ls
    importlib.reload(ls)
    import routes.health as hp
    importlib.reload(hp)

    store = ls.get_store()
    store.ingest({
        "id": "mcp-x",
        "node_id": "agent+x",
        "session_id": "s1",
        "event_type": "mcp_call",
        "ts": _iso(datetime.now(timezone.utc)),
        "data": {"name": "mcp.search"},
    })
    _wait_flush(store)

    a = Flask(__name__)
    a.register_blueprint(hp.bp_health)
    body = a.test_client().get("/api/mcp-stats").get_json()
    # Legacy scanner ran (sessions_dir=/nonexistent) → empty result, no _source.
    assert body.get("_source") != "local_store"
    assert body["checked"] == 0
    assert body["tools"] == []
    try:
        store.stop(flush=True)
    except Exception:
        pass


# ─────────────────────────────────────────────────────────────────────────────
# /api/loop-detection
# ─────────────────────────────────────────────────────────────────────────────


def test_loop_detection_fast_path_finds_repeats(app):
    """Same tool + identical args N times in one session → flagged."""
    a, ls = app
    store = ls.get_store()
    base = datetime.now(timezone.utc)

    # 5 identical calls in one session (>=3 repeats inside default window=10).
    for i in range(5):
        store.ingest({
            "id": f"tc-loop-{i}",
            "node_id": "agent+test",
            "session_id": "sess-loop",
            "event_type": "tool_call",
            "ts": _iso(base + timedelta(seconds=i)),
            "data": {"name": "Bash", "input": {"cmd": "ls /tmp"}},
        })
    # A few unrelated calls in a second session — should NOT be flagged.
    for i in range(3):
        store.ingest({
            "id": f"tc-no-{i}",
            "node_id": "agent+test",
            "session_id": "sess-clean",
            "event_type": "tool_call",
            "ts": _iso(base + timedelta(seconds=i)),
            "data": {"name": f"Tool{i}", "input": {"x": i}},
        })
    _wait_flush(store)

    r = a.test_client().get("/api/loop-detection")
    assert r.status_code == 200
    body = r.get_json()
    assert body["_source"] == "local_store"
    assert body["checked"] == 2
    assert body["loop_count"] >= 1
    flagged = [l for l in body["loops"] if l["session_id"] == "sess-loop"]
    assert flagged, "expected sess-loop to be flagged"
    assert flagged[0]["tool_name"] == "Bash"
    assert flagged[0]["repeat_count"] >= 3
    assert "first_seen_ts" in flagged[0]


def test_loop_detection_falls_back_when_env_unset(tmp_path, monkeypatch):
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "clawmetry.duckdb"))
    monkeypatch.delenv("CLAWMETRY_LOCAL_STORE_READ", raising=False)
    _stub_dashboard()

    import clawmetry.local_store as ls
    importlib.reload(ls)
    import routes.health as hp
    importlib.reload(hp)

    store = ls.get_store()
    for i in range(5):
        store.ingest({
            "id": f"tc-x-{i}",
            "node_id": "agent+x",
            "session_id": "sess-loop",
            "event_type": "tool_call",
            "ts": _iso(datetime.now(timezone.utc) + timedelta(seconds=i)),
            "data": {"name": "Bash", "input": {"cmd": "ls"}},
        })
    _wait_flush(store)

    a = Flask(__name__)
    a.register_blueprint(hp.bp_health)
    body = a.test_client().get("/api/loop-detection").get_json()
    assert body.get("_source") != "local_store"
    # Legacy path scans /nonexistent → 0 sessions, no loops.
    assert body["checked"] == 0
    assert body["loop_count"] == 0
    try:
        store.stop(flush=True)
    except Exception:
        pass


# ─────────────────────────────────────────────────────────────────────────────
# /api/service-status
# ─────────────────────────────────────────────────────────────────────────────


def test_service_status_fast_path_composes_from_heartbeats(app):
    """Recent heartbeat (<5min) → sync=True; missing snapshots → defaults."""
    a, ls = app
    store = ls.get_store()
    now = datetime.now(timezone.utc)
    store.ingest_heartbeat({
        "node_id": "agent+test",
        "ts": _iso(now),
        "version": "0.12.162",
        "e2e": True,
        "channels": [
            {"name": "telegram", "connected": True},
            {"name": "discord", "connected": False},
        ],
        "gateway_up": True,
    })

    r = a.test_client().get("/api/service-status")
    assert r.status_code == 200
    body = r.get_json()
    assert body["_source"] == "local_store"
    ss = body["service_status"]
    assert ss["sync"] is True
    assert ss["gateway"] is True
    assert ss["resources"] in {"ok", "warn", "critical"}
    names = {c["name"] for c in ss["channels"]}
    assert "telegram" in names and "discord" in names


def test_service_status_uses_snapshots_when_present(app):
    """A 'resources' snapshot with status='warn' → propagates to output."""
    a, ls = app
    store = ls.get_store()
    now = datetime.now(timezone.utc)
    store.ingest_heartbeat({
        "node_id": "agent+test",
        "ts": _iso(now),
        "version": "0.12.162",
    })
    store.ingest_system_snapshot({
        "node_id": "agent+test",
        "ts": _iso(now),
        "kind": "resources",
        "status": "warn",
    })
    store.ingest_system_snapshot({
        "node_id": "agent+test",
        "ts": _iso(now),
        "kind": "gateway",
        "up": False,
    })

    r = a.test_client().get("/api/service-status")
    assert r.status_code == 200
    body = r.get_json()
    assert body["_source"] == "local_store"
    ss = body["service_status"]
    assert ss["resources"] == "warn"
    assert ss["gateway"] is False


def test_service_status_falls_back_when_env_unset(tmp_path, monkeypatch):
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "clawmetry.duckdb"))
    monkeypatch.delenv("CLAWMETRY_LOCAL_STORE_READ", raising=False)
    _stub_dashboard()

    import clawmetry.local_store as ls
    importlib.reload(ls)
    import routes.health as hp
    importlib.reload(hp)

    store = ls.get_store()
    store.ingest_heartbeat({
        "node_id": "agent+x",
        "ts": _iso(datetime.now(timezone.utc)),
        "version": "0.12.162",
    })

    a = Flask(__name__)
    a.register_blueprint(hp.bp_health)
    body = a.test_client().get("/api/service-status").get_json()
    assert body.get("_source") != "local_store"
    assert "service_status" in body
    try:
        store.stop(flush=True)
    except Exception:
        pass
