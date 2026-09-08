"""Alive-state truthfulness for the Overview hero (founder report 2026-08-02).

The hero's "It's working / It's idle right now" used to read ONLY the
subagent registry (``/api/subagents``), which lists SPAWNED children — main
terminal sessions (Claude Code in N terminals) never appear there, so a node
hard at work said "It's idle right now."

The fix threads a per-runtime recency signal, ``last_activity_ms`` (epoch ms
of the newest event ts / session ``last_active_at``), through every layer the
hero can read:

  store.query_model_rollup()["by_runtime"][rt]["last_activity_ms"]
    -> sync._build_runtime_summary()[rt]["last_activity_ms"]   (cloud snapshot)
    -> GET /api/runtime-summary  runtimes[rt]["last_activity_ms"] (local route)
    -> app.js _cmRtRecentlyActive() OR-ed into the hero's ``busy``

These tests pin each hop; the JS hop is guarded mechanically (the busy
expression must reference the recency helper, and the helper must read
``last_activity_ms``) so a frontend refactor can't silently drop it.
"""

from __future__ import annotations

import importlib
import os
import re
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
    monkeypatch.setattr(lq, "local_store_via_daemon", lambda *a, **k: None)
    monkeypatch.setattr(lq, "_read_discovery", lambda: None)
    monkeypatch.setattr(lq, "_cached_discovery", lambda: None)
    import routes.usage as usage_mod
    importlib.reload(usage_mod)
    a = Flask(__name__)
    a.register_blueprint(usage_mod.bp_usage)
    yield a, ls
    try:
        ls.get_store().stop(flush=True)
    except Exception:
        pass


def _seed(store, sid: str, ts: float, *, model: str = "claude-opus-4-8") -> None:
    store.ingest({
        "id": sid + "-" + str(int(ts * 1000)),
        "node_id": "agent+test",
        "agent_id": "main",
        "session_id": sid,
        "event_type": "tool_call",
        "ts": _iso(ts),
        "data": {"tool_name": "X"},
        "cost_usd": 0.01,
        "token_count": 100,
        "model": model,
    })


# ── 1. store rollup carries per-runtime recency ─────────────────────────────


def test_rollup_carries_last_activity_ms(app_and_store):
    _, ls = app_and_store
    store = ls.get_store()
    now = time.time()
    _seed(store, "claude_code:c1", now - 3000)
    _seed(store, "claude_code:c1", now - 30)          # fresh main-session event
    _seed(store, "goose:g1", now - 7200)              # 2h old
    _wait_flush(store)

    by_rt = store.query_model_rollup()["by_runtime"]
    cc = by_rt["claude_code"]["last_activity_ms"]
    go = by_rt["goose"]["last_activity_ms"]
    # Newest event wins, in epoch ms (±5s slack for flush timing).
    assert abs(cc - (now - 30) * 1000) < 5000, cc
    assert abs(go - (now - 7200) * 1000) < 5000, go


def test_rollup_recency_falls_back_to_session_last_active(app_and_store):
    """Family adapters keep activity on the sessions row (events may carry no
    usable recency for them) — sessions.last_active_at must feed the signal."""
    _, ls = app_and_store
    store = ls.get_store()
    now = time.time()
    store.ingest_session({
        "session_id": "cursor:k1", "agent_type": "cursor", "agent_id": "main",
        "status": "active", "total_tokens": 500, "cost_usd": 0.05,
        "last_active_at": _iso(now - 45),
    })
    _wait_flush(store)

    by_rt = store.query_model_rollup()["by_runtime"]
    k = by_rt["cursor"]["last_activity_ms"]
    assert abs(k - (now - 45) * 1000) < 5000, k


# ── 2. the snapshot builder emits it (the cloud hero's source) ──────────────


def test_runtime_summary_snapshot_emits_last_activity(app_and_store, monkeypatch):
    _, ls = app_and_store
    store = ls.get_store()
    now = time.time()
    _seed(store, "claude_code:c1", now - 20)
    _wait_flush(store)

    import clawmetry.sync as sync
    monkeypatch.setattr(ls, "get_store", lambda *a, **k: store)
    rs = sync._build_runtime_summary()
    assert "claude_code" in rs
    ms = rs["claude_code"]["last_activity_ms"]
    assert abs(ms - (now - 20) * 1000) < 5000, ms


# ── 3. the local route serves it (self-hosted hero's source) ────────────────


def test_local_runtime_summary_route_serves_last_activity(app_and_store):
    a, ls = app_and_store
    store = ls.get_store()
    now = time.time()
    _seed(store, "claude_code:c1", now - 20)
    _wait_flush(store)

    body = a.test_client().get("/api/runtime-summary").get_json() or {}
    cc = (body.get("runtimes") or {}).get("claude_code") or {}
    ms = int(cc.get("last_activity_ms") or 0)
    assert abs(ms - (now - 20) * 1000) < 5000, body


# ── 4. the frontend actually reads it (mechanical drift guard) ──────────────


def _appjs() -> str:
    path = os.path.join(os.path.dirname(__file__), "..",
                        "clawmetry", "static", "js", "app.js")
    with open(path, encoding="utf-8") as f:
        return f.read()


def test_hero_busy_ors_in_main_session_recency():
    js = _appjs()
    # The busy expression must OR the subagent flag with the recency helper —
    # subagents alone regress to "idle while terminals are busy."
    assert re.search(
        r"var busy = !!window\._cmAgentBusy \|\| _cmRtRecentlyActive\(\)", js
    ), "hero busy no longer includes main-session recency"
    # And the helper must read the snapshot/route field by name.
    assert "last_activity_ms" in js, "recency helper lost the last_activity_ms read"


def test_hero_tps_chip_guards_scope_jumps():
    """The live tok/s chip diffs _cmTodayTokensRaw between renders. A runtime
    switch swaps that counter's source, so an unguarded delta rendered
    '23,058,079 tok/s' the moment busy became true for main sessions. The
    sample pair must be same-scope and the result bounded."""
    js = _appjs()
    assert "_prevT.rt === _tpsRt" in js, "tok/s chip lost the same-scope guard"
    assert re.search(r"_tps > 0\.5 && _tps < 50000", js), \
        "tok/s chip lost its sanity ceiling"
