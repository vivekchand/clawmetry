"""Agent Inventory tab — daemon slice + route + agent_meta store contract.

Covers, with a real seeded DuckDB (no synthetic snapshot fixtures):

1. ``_build_agent_inventory`` produces exactly one row per runtimeSummary key,
   openclaw is present even when family-detect returns it nowhere, and
   cost/sessions mirror runtimeSummary verbatim.
2. PER-RUNTIME NO-LEAK: ``agentInventoryByRuntime['claude_code']`` carries ONLY
   the claude_code row; an absent runtime is not a key (the cloud interceptor
   then returns ZERO).
3. GET /api/inventory never-raises -> 200 {agents:[],total:0} when get_store is
   patched to raise, AND scopes to ?runtime=<rt> with only that row.
4. agent_meta round-trip + partial-update COALESCE + the daemon-proxy path.
5. lock-safety: query_agent_meta is NOT nested in an outer _write_lock.
"""
from __future__ import annotations

import importlib
import time
from datetime import datetime, timezone

import pytest
from flask import Flask


def _iso(s: float) -> str:
    return datetime.fromtimestamp(s, tz=timezone.utc).isoformat()


def _wait_flush(store, t: float = 2.0) -> None:
    deadline = time.monotonic() + t
    while time.monotonic() < deadline:
        if store.health()["ring_depth"] == 0:
            return
        time.sleep(0.02)


@pytest.fixture
def app_and_store(tmp_path, monkeypatch):
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "events.duckdb"))
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_SECS", "0.05")
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_BATCH", "1")
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_READ", "1")
    import clawmetry.local_store as ls
    importlib.reload(ls)
    ls.mark_writer_owner()
    import routes.local_query as lq
    importlib.reload(lq)
    # Single-process: skip the HTTP proxy, hit the in-process store directly.
    monkeypatch.setattr(lq, "local_store_via_daemon", lambda *a, **k: None)
    monkeypatch.setattr(lq, "_read_discovery", lambda: None)
    monkeypatch.setattr(lq, "_cached_discovery", lambda: None)
    import routes.inventory as inv_mod
    importlib.reload(inv_mod)
    a = Flask(__name__)
    a.register_blueprint(inv_mod.bp_inventory)
    yield a, ls, inv_mod
    try:
        ls.get_store().stop(flush=True)
    except Exception:
        pass


def _seed(store, sid: str, model: str, ts: float, cost: float = 0.01) -> None:
    store.ingest({
        "id": sid + "-" + str(int(ts * 1000)),
        "node_id": "agent+test",
        "agent_id": "main",
        "session_id": sid,
        "event_type": "tool_call",
        "ts": _iso(ts),
        "data": {"tool_name": "X"},
        "cost_usd": cost,
        "token_count": 100,
        "model": model,
    })


# ── 1. _build_agent_inventory: one row per runtimeSummary key ───────────────


def test_build_agent_inventory_one_row_per_runtime(app_and_store):
    a, ls, _ = app_and_store
    import clawmetry.sync as sync
    importlib.reload(sync)
    store = ls.get_store()
    now = time.time()
    seeds = {
        "claude_code:c1": "claude-opus-4-7",
        "codex:x1":       "gpt-5",
        "bareuuid-zzz":   "claude-opus-4-7",   # → openclaw bucket
    }
    for i, (sid, m) in enumerate(seeds.items()):
        _seed(store, sid, m, now - 600 + i, cost=0.05)
    _wait_flush(store)

    rs = sync._build_runtime_summary()
    assert set(rs.keys()) == {"claude_code", "codex", "openclaw"}, rs.keys()

    node_wide, by_rt = sync._build_agent_inventory(
        rs, {}, {}, {"builtin": 2, "mcp": 1, "plugin": 0}, {"avg_score": 0.9},
        detected_runtimes=[], agent_meta={}, node_id="agent+test",
    )
    keys = {r["agentKey"] for r in node_wide["agents"]}
    assert keys == {"claude_code", "codex", "openclaw"}
    assert node_wide["total"] == 3
    # openclaw present even though family-detect returned nothing.
    oc = [r for r in node_wide["agents"] if r["agentKey"] == "openclaw"][0]
    assert oc["detected"] is True
    # cost/sessions mirror runtimeSummary verbatim.
    for r in node_wide["agents"]:
        rt = r["agentKey"]
        assert r["costUsd"] == round(rs[rt]["cost_usd"], 4)
        assert r["sessions"] == rs[rt]["sessions"]
    # node-wide strip rides along, NOT as a per-row column.
    assert node_wide["nodeWideToolGroups"] == {"builtin": 2, "mcp": 1, "plugin": 0}
    assert node_wide["nodeWideEval"] == {"avg_score": 0.9}
    assert all("nodeWideToolGroups" not in r for r in node_wide["agents"])


# ── 2. PER-RUNTIME NO-LEAK ──────────────────────────────────────────────────


def test_agent_inventory_by_runtime_no_leak(app_and_store):
    a, ls, _ = app_and_store
    import clawmetry.sync as sync
    importlib.reload(sync)
    store = ls.get_store()
    now = time.time()
    for i, (sid, m) in enumerate({
        "openclaw:o1":    "claude-opus-4-7",
        "claude_code:c1": "claude-opus-4-7",
        "codex:x1":       "gpt-5",
    }.items()):
        _seed(store, sid, m, now - 600 + i)
    _wait_flush(store)

    rs = sync._build_runtime_summary()
    _node, by_rt = sync._build_agent_inventory(
        rs, {}, {}, {}, {}, detected_runtimes=[], agent_meta={}, node_id="n",
    )
    # claude_code slice has ONLY the claude_code row.
    cc = by_rt["claude_code"]
    assert cc["total"] == 1
    assert [r["agentKey"] for r in cc["agents"]] == ["claude_code"]
    assert all(r["agentKey"] != "openclaw" for r in cc["agents"])
    assert all(r["agentKey"] != "codex" for r in cc["agents"])
    # An absent runtime is simply not a key (interceptor returns ZERO for it).
    assert "cursor" not in by_rt
    assert "picoclaw" not in by_rt


# ── 3. Route never-raise + ?runtime= scoping ────────────────────────────────


def test_api_inventory_never_raises_on_store_error(app_and_store, monkeypatch):
    a, ls, inv_mod = app_and_store
    # Force the builder to blow up: patch sync import to raise inside the route.
    import clawmetry.local_store as lsmod

    def _boom(*args, **kwargs):
        raise RuntimeError("store gone")

    monkeypatch.setattr(lsmod, "get_store", _boom)
    cli = a.test_client()
    r = cli.get("/api/inventory")
    assert r.status_code == 200
    body = r.get_json()
    assert body == {"agents": [], "total": 0}


def test_api_inventory_runtime_scopes_to_single_row(app_and_store):
    a, ls, _ = app_and_store
    store = ls.get_store()
    now = time.time()
    for i, (sid, m) in enumerate({
        "openclaw:o1":    "claude-opus-4-7",
        "claude_code:c1": "claude-opus-4-7",
    }.items()):
        _seed(store, sid, m, now - 600 + i)
    _wait_flush(store)
    cli = a.test_client()

    full = cli.get("/api/inventory").get_json()
    keys = {r["agentKey"] for r in full["agents"]}
    assert {"openclaw", "claude_code"} <= keys

    scoped = cli.get("/api/inventory?runtime=claude_code").get_json()
    assert scoped["total"] == 1
    assert [r["agentKey"] for r in scoped["agents"]] == ["claude_code"]

    # Absent runtime -> honest zero, never the node-wide set.
    absent = cli.get("/api/inventory?runtime=cursor").get_json()
    assert absent == {"agents": [], "total": 0}


# ── 4. agent_meta round-trip + COALESCE + daemon-proxy path ─────────────────


def test_agent_meta_roundtrip_and_partial_update(app_and_store):
    a, ls, _ = app_and_store
    store = ls.get_store()
    store.set_agent_meta("claude_code", owner="ana")
    meta = store.query_agent_meta()
    assert meta["claude_code"]["owner"] == "ana"
    # Partial update: setting only notes preserves the owner (COALESCE).
    store.set_agent_meta("claude_code", notes="my coding agent")
    meta = store.query_agent_meta()
    assert meta["claude_code"]["owner"] == "ana"
    assert meta["claude_code"]["notes"] == "my coding agent"


def test_agent_meta_via_owner_route(app_and_store):
    a, ls, _ = app_and_store
    # Establish the writer singleton first so the route's _ls_call direct
    # fallback (get_store(read_only=True)) returns the in-process writer, not a
    # daemon proxy pointed at a real machine's daemon.
    store = ls.get_store()
    cli = a.test_client()
    r = cli.post("/api/inventory/claude_code/owner", json={"owner": "ana"})
    assert r.status_code == 200
    assert r.get_json()["ok"] is True
    # And it reads back through the store.
    meta = ls.get_store().query_agent_meta()
    assert meta.get("claude_code", {}).get("owner") == "ana"


def test_agent_meta_in_daemon_allowlist():
    import routes.local_query as lq
    importlib.reload(lq)
    assert "query_agent_meta" in lq._DAEMON_METHODS
    assert "set_agent_meta" in lq._DAEMON_METHODS


# ── 5. lock-safety: query_agent_meta must not nest the write lock ───────────


def test_query_agent_meta_not_nested_in_write_lock(app_and_store):
    """Regression guard for feedback_local_store_fetch_takes_writelock: _fetch
    self-locks, so query_agent_meta wrapping itself in _write_lock would
    deadlock a plain Lock. Acquiring the lock then calling the method must NOT
    hang (we run it in a thread and assert it completes)."""
    import threading
    a, ls, _ = app_and_store
    store = ls.get_store()
    store.set_agent_meta("openclaw", owner="me")

    done = {}

    def _run():
        done["meta"] = store.query_agent_meta()

    th = threading.Thread(target=_run, daemon=True)
    th.start()
    th.join(timeout=5.0)
    assert not th.is_alive(), "query_agent_meta deadlocked (nested write lock?)"
    assert "openclaw" in done["meta"]


# ── 6. snapshot wiring: both keys are emitted in the payload dict ───────────


def test_api_inventory_empty_store_with_detected_runtimes(app_and_store, monkeypatch):
    """When the local store is enabled but the roster is empty AND registry
    detects runtimes, /api/inventory must return detectedRuntimes + daemonRunning
    instead of the bare zero shape (issue #3917)."""
    a, ls, inv_mod = app_and_store
    from clawmetry.adapters.base import DetectResult

    fake_detect = DetectResult(
        name="openclaw",
        display_name="OpenClaw",
        detected=True,
    )
    monkeypatch.setattr(inv_mod, "_detected_runtimes", lambda: [fake_detect.to_dict()])
    monkeypatch.setattr(inv_mod, "_daemon_running", lambda: False)

    cli = a.test_client()
    body = cli.get("/api/inventory").get_json()
    assert body["agents"] == []
    assert body["total"] == 0
    assert body["daemonRunning"] is False
    detected = body["detectedRuntimes"]
    assert isinstance(detected, list) and len(detected) == 1
    assert detected[0]["name"] == "openclaw"
    assert detected[0]["displayName"] == "OpenClaw"


def test_api_inventory_empty_store_no_detected_runtimes_still_zero(app_and_store, monkeypatch):
    """When neither the store has agents nor any runtime is detected, the
    response must be the bare zero shape (the cloud cold-fallthrough contract)."""
    a, ls, inv_mod = app_and_store
    monkeypatch.setattr(inv_mod, "_detected_runtimes", lambda: [])

    cli = a.test_client()
    body = cli.get("/api/inventory").get_json()
    assert body == {"agents": [], "total": 0}


def test_snapshot_emits_both_inventory_keys():
    """Mechanical guard that ``sync_system_snapshot`` ships both inventory keys
    (node-wide + byRuntime) built from the already-computed rollups. A full
    snapshot build needs a live workspace; here we assert the payload wiring is
    present so a refactor can't silently drop the slice."""
    from pathlib import Path
    src = (Path(__file__).resolve().parents[1] / "clawmetry" / "sync.py").read_text(encoding="utf-8")
    assert '"agentInventory": _inv_node_wide' in src
    assert '"agentInventoryByRuntime": _inv_by_rt' in src
    # Built from rollups, not a new request-path scan.
    assert "_inv_node_wide, _inv_by_rt = _build_agent_inventory(" in src
    # The node-wide strip carries the honest cross-runtime tool/eval slices.
    assert "nodeWideToolGroups" in src
    assert "nodeWideEval" in src
