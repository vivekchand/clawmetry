"""sync_family_runtimes records adapter-emitted sub-agent children into the
``subagents`` table so they reach the snapshot ``subagents[]`` slice (the
Command River lanes), and excludes them from the top-level sessions list.

The Claude Code adapter (clawmetry-pro) surfaces each spawned sub-agent
transcript as a CHILD ``Session`` with ``parent_id`` set. This test uses a
FAKE family adapter (no pro dependency) that emits one parent + two children,
and asserts the daemon:

  * writes each child to ``subagents`` with ``parent_session_id`` = the
    parent's namespaced session id (so ``query_subagents`` / the snapshot
    surface them, and the cloud river filter — which normalises bare +
    prefixed forms — binds them to the parent),
  * carries the child's cache-aware cost + tokens + label + status onto the
    subagent row,
  * keeps children OUT of ``query_sessions_table`` (the top-level list) while
    keeping the parent in.

Revert-proof: dropping the ``if s.parent_id: store.ingest_subagent(...)`` block
makes ``test_child_lands_in_subagents_table`` go RED.
"""
from __future__ import annotations

import importlib
import time
from unittest.mock import patch

import pytest

from clawmetry.adapters.base import (
    AgentAdapter,
    Capability,
    DetectResult,
    Session,
)


_PARENT_UUID = "1aaf7ca1-ce93-4c96-9e5f-0ad496e36479"
_RUNTIME = "claude_code"


class _FakeFanoutAdapter(AgentAdapter):
    """Emits one parent session + two sub-agent children (parent_id set)."""

    name = _RUNTIME
    display_name = "Claude Code (fake)"

    def detect(self) -> DetectResult:
        return DetectResult(name=self.name, display_name=self.display_name,
                            detected=True, running=True)

    def list_sessions(self, limit: int = 100):
        parent = Session(
            agent=self.name, id=_PARENT_UUID,
            title="Review flywheel documentation across projects",
            model="claude-fable-5",
            started_at=1_780_000_000.0, ended_at=1_780_000_500.0,
            message_count=4, total_tokens=1000, cost_usd=0.50,
        )
        child_running = Session(
            agent=self.name, id=f"{_PARENT_UUID}::agent-a1111111",
            parent_id=_PARENT_UUID,
            title="Build Command River into Brain tab",
            display_name="Build Command River into Brain tab",
            model="claude-fable-5",
            started_at=1_780_000_100.0, ended_at=None,
            message_count=3, total_tokens=300, cost_usd=0.12,
            cost_status="running",
            extra={"depth": 1, "isSubagent": True,
                   "description": "Build Command River into Brain tab",
                   "agentFile": "agent-a1111111"},
        )
        child_failed = Session(
            agent=self.name, id=f"{_PARENT_UUID}::agent-a3333333",
            parent_id=_PARENT_UUID,
            title="Risky step", display_name="Risky step",
            model="claude-fable-5",
            started_at=1_780_000_050.0, ended_at=1_780_000_200.0,
            message_count=2, total_tokens=50, cost_usd=0.02,
            end_reason="error",
            extra={"depth": 1, "isSubagent": True,
                   "description": "Risky step", "agentFile": "agent-a3333333"},
        )
        return [parent, child_running, child_failed]

    def list_events(self, session_id: str, limit: int = 500):
        # One renderable event per session so the daemon's per-session read +
        # title-fallback paths run; children skip event ingest in the daemon.
        from clawmetry.adapters.base import Event
        return [Event(agent=self.name, session_id=session_id,
                      id=f"{session_id}:1", type="message", ts=1_780_000_100.0,
                      role="assistant", content="hi", tokens=10)]

    def capabilities(self):
        return {Capability.SESSIONS, Capability.EVENTS, Capability.COST,
                Capability.SUBAGENTS}


@pytest.fixture
def sync_with_isolated_store(tmp_path, monkeypatch):
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "events.duckdb"))
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_SECS", "0.05")
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_BATCH", "5")
    import clawmetry.local_store as ls
    import clawmetry.sync as sync
    importlib.reload(ls)
    importlib.reload(sync)
    monkeypatch.setattr(ls, "_daemon_registered", lambda: False)
    monkeypatch.delenv("CLAWMETRY_ROLE", raising=False)
    yield sync, ls
    try:
        ls.get_store().stop(flush=True)
    except Exception:
        pass


def _wait_for_flush(store, timeout=3.0):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if store.health()["ring_depth"] == 0:
            return
        time.sleep(0.02)
    raise AssertionError("flusher did not drain in time")


def _run(sync, ls):
    config = {"node_id": "test-node", "api_key": "test-key"}
    with patch.object(sync, "_sync_allowed", return_value=True), \
         patch.object(sync, "_post", return_value={}), \
         patch.object(sync, "_family_adapter_classes",
                      return_value=[_FakeFanoutAdapter]), \
         patch.object(sync, "_openclaw_spawned_claude_ids", return_value=set()):
        sync.sync_family_runtimes(config, {}, {})
    store = ls.get_store()
    _wait_for_flush(store)
    return store


def test_child_lands_in_subagents_table(sync_with_isolated_store):
    sync, ls = sync_with_isolated_store
    store = _run(sync, ls)

    rows = store.query_subagents(parent_session_id=f"{_RUNTIME}:{_PARENT_UUID}",
                                 limit=100)
    ids = {r["subagent_id"] for r in rows}
    assert f"{_RUNTIME}:{_PARENT_UUID}::agent-a1111111" in ids
    assert f"{_RUNTIME}:{_PARENT_UUID}::agent-a3333333" in ids
    assert len(rows) == 2

    by_id = {r["subagent_id"]: r for r in rows}
    running = by_id[f"{_RUNTIME}:{_PARENT_UUID}::agent-a1111111"]
    assert running["parent_session_id"] == f"{_RUNTIME}:{_PARENT_UUID}"
    assert running["status"] == "running"
    assert running["task"] == "Build Command River into Brain tab"
    # cache-aware cost + tokens carried from the adapter (>= stored).
    assert running["cost_usd"] >= 0.12 - 1e-9
    assert running["token_count"] >= 300

    failed = by_id[f"{_RUNTIME}:{_PARENT_UUID}::agent-a3333333"]
    assert failed["status"] == "failed"


def test_subagents_snapshot_slice_contains_children(sync_with_isolated_store):
    """The /api/subagents shaper (same source the snapshot subagents[] uses)
    returns the children bound to the parent with the river fields."""
    sync, ls = sync_with_isolated_store
    store = _run(sync, ls)

    import routes.sessions as sa_routes
    rows = store.query_subagents(limit=500)
    shaped = sa_routes._try_local_store_subagents(_rows=rows)
    assert shaped is not None
    subs = shaped["subagents"]
    # The cloud river normalises ``parent`` via bareSid; assert the raw parent
    # carries the parent uuid (prefixed form is fine).
    river = [s for s in subs if str(s["parent"]).endswith(_PARENT_UUID)]
    assert len(river) == 2
    one = next(s for s in river if "a1111111" in s["sessionId"])
    assert one["displayName"] == "Build Command River into Brain tab"
    assert one["depth"] == 1
    assert one["totalTokens"] >= 300
    assert one["costUsd"] >= 0.12 - 1e-9


def test_children_excluded_from_sessions_list(sync_with_isolated_store):
    sync, ls = sync_with_isolated_store
    store = _run(sync, ls)

    rows = store.query_sessions_table(limit=200)
    ids = {r["session_id"] for r in rows}
    # Parent shows in the top-level list.
    assert f"{_RUNTIME}:{_PARENT_UUID}" in ids
    # Children do NOT.
    assert f"{_RUNTIME}:{_PARENT_UUID}::agent-a1111111" not in ids
    assert f"{_RUNTIME}:{_PARENT_UUID}::agent-a3333333" not in ids


def test_failed_subagent_write_is_retried_not_watermarked(sync_with_isolated_store):
    """A transient ``ingest_subagent`` failure must NOT advance the per-session
    high-water mark, so the very next pass retries the write and the child still
    reaches the ``subagents`` table (self-healing).

    This is the daemon-routing GAP that left the Command River showing 0 lanes
    for a real Claude Code session: the family loop ran and the child's
    ``ingest_subagent`` raised inside a transient DuckDB WAL-conflict window, but
    the watermark advanced anyway, so the child was permanently skipped on every
    later pass even after the store recovered.

    Revert-proof: with the OLD code (watermark set unconditionally, regardless of
    ``_subagent_ingested``), the second pass is short-circuited by the advanced
    high-water mark, the child is never re-attempted, and the final
    ``query_subagents`` returns 0 — RED. The fix gates the watermark on a
    successful write, so the retry lands it — GREEN.
    """
    sync, ls = sync_with_isolated_store
    config = {"node_id": "test-node", "api_key": "test-key"}
    state: dict = {}

    real_ingest = ls.LocalStore.ingest_subagent
    calls = {"n": 0}

    def flaky_ingest(self, sa):
        # Fail every child write on the FIRST family pass only; succeed after.
        if calls["n"] == 0 and str(sa.get("subagent_id", "")).count("::agent-"):
            calls["n"] += 1
            raise RuntimeError("transient WAL conflict (simulated)")
        return real_ingest(self, sa)

    with patch.object(sync, "_sync_allowed", return_value=True), \
         patch.object(sync, "_post", return_value={}), \
         patch.object(sync, "_family_adapter_classes",
                      return_value=[_FakeFanoutAdapter]), \
         patch.object(sync, "_openclaw_spawned_claude_ids", return_value=set()), \
         patch.object(ls.LocalStore, "ingest_subagent", flaky_ingest):
        # Pass 1: child writes raise; watermark MUST NOT advance for them.
        sync.sync_family_runtimes(config, state, {})
        # Pass 2: same SAME state dict — if the watermark wrongly advanced in
        # pass 1, this pass skips the child before ever calling ingest again.
        sync.sync_family_runtimes(config, state, {})

    store = ls.get_store()
    _wait_for_flush(store)
    rows = store.query_subagents(parent_session_id=f"{_RUNTIME}:{_PARENT_UUID}",
                                 limit=100)
    ids = {r["subagent_id"] for r in rows}
    # Both children land after the retry; with the bug present this set is empty.
    assert f"{_RUNTIME}:{_PARENT_UUID}::agent-a1111111" in ids
    assert f"{_RUNTIME}:{_PARENT_UUID}::agent-a3333333" in ids
    assert len(rows) == 2
