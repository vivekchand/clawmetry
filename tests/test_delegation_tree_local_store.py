"""Regression guard for /api/delegation-tree DuckDB fast path (Tier-1 #1778).

``routes/sessions.py:_try_local_store_delegation_tree`` reads the
pre-aggregated ``subagents`` table (same source as
``_try_local_store_subagents``) instead of opening + walking
``sessions.json``. Groups by ``parent_session_id`` (or ``spawnedBy``
when the full canonical key is in the row's data blob), then sums
each chain's token + cost totals server-side.

Tests:

1. Two children for one parent surface with the correct chain
   rollups and ``_source='local_store'``.
2. Empty store returns the empty shell directly (no legacy fallback
   trigger) since reaching the daemon and finding zero subagents is
   the right answer.
3. Per-row ``cost_usd`` from the daemon (already deduped at the
   ``query_sessions`` SQL layer for v3 sibling pairs) is honored
   verbatim — we do NOT re-estimate from tokens when the daemon
   already wrote a cost.
"""

from __future__ import annotations

import importlib
import time

import pytest
from flask import Flask


@pytest.fixture
def app(tmp_path, monkeypatch):
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "events.duckdb"))
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_SECS", "0.05")
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_READ", "1")

    import clawmetry.local_store as ls
    importlib.reload(ls)
    import routes.local_query as lq
    importlib.reload(lq)
    import routes.sessions as sessions_mod
    importlib.reload(sessions_mod)

    # Isolate the fixture from a contributor's locally running daemon
    # (same shim as ``test_subagents_local_store_v3``).
    monkeypatch.setattr(lq, "_read_discovery", lambda: None)

    a = Flask(__name__)
    a.register_blueprint(sessions_mod.bp_sessions)
    yield a, ls
    try:
        ls.get_store().stop(flush=True)
    except Exception:
        pass


def test_delegation_tree_local_store_groups_by_parent(app):
    """Two children sharing one parent -> one chain with token + cost
    rollups, tagged ``_source='local_store'``."""
    a, ls = app
    store = ls.get_store()
    parent_sid = "parent-session-xyz"

    store.ingest_subagent({
        "subagent_id":       "child-a",
        "agent_type":        "openclaw",
        "parent_session_id": parent_sid,
        "spawned_at":        "2026-05-17T10:00:00Z",
        "task":              "refactor auth.py",
        "status":            "active",
        "cost_usd":          0.0234,
        "token_count":       4200,
        "model":             "claude-opus-4-7",
        "label":             "auth-refactor",
        "tokensIn":          3000,
        "tokensOut":         1200,
        "updated_at_ms":     int(time.time() * 1000),
    })
    store.ingest_subagent({
        "subagent_id":       "child-b",
        "agent_type":        "openclaw",
        "parent_session_id": parent_sid,
        "spawned_at":        "2026-05-17T10:01:00Z",
        "task":              "summarise transcripts",
        "status":            "completed",
        "cost_usd":          0.0089,
        "token_count":       1800,
        "model":             "claude-opus-4-7",
        "label":             "summariser",
        "updated_at_ms":     int(time.time() * 1000),
    })

    r = a.test_client().get("/api/delegation-tree")
    assert r.status_code == 200, r.get_data(as_text=True)
    body = r.get_json()
    assert body.get("_source") == "local_store", body
    assert body.get("total_subagents") == 2
    chains = body.get("chains") or []
    assert len(chains) == 1, f"expected one chain, got {chains!r}"
    chain = chains[0]
    assert chain["parent_key"] == parent_sid
    assert chain["child_count"] == 2
    assert chain["chain_tokens"] == 6000  # 4200 + 1800
    # Per-row cost_usd from the daemon is honored verbatim (no token-based
    # re-estimation). 0.0234 + 0.0089 = 0.0323.
    assert abs(chain["chain_cost_usd"] - 0.0323) < 1e-6, chain
    # total_chain_cost_usd is rounded to 4 dp (legacy parity).
    assert abs(body["total_chain_cost_usd"] - 0.0323) < 1e-4

    # Children sorted by total_tokens DESC.
    child_ids = [c["key"].rsplit(":", 1)[-1] for c in chain["children"]]
    assert child_ids == ["child-a", "child-b"], child_ids
    first = chain["children"][0]
    assert first["total_tokens"] == 4200
    assert first["input_tokens"] == 3000
    assert first["output_tokens"] == 1200
    assert first["status"] == "active"
    assert first["model"] == "claude-opus-4-7"
    assert first["prov_agent_type"] == "subagent"
    assert first["prov_session_turn"] == 2


def test_delegation_tree_local_store_empty_returns_shell(app):
    """Empty subagents table -> reachable-but-empty shell with
    ``_source='local_store'``. Avoids triggering the sessions.json
    fallback on installs where the daemon is healthy but no subagents
    have been spawned yet."""
    a, ls = app
    assert ls.get_store().query_subagents(limit=10) == []

    import routes.sessions as sessions_mod
    fast = sessions_mod._try_local_store_delegation_tree()
    assert fast is not None, "reachable empty store must return shell, not None"
    assert fast["_source"] == "local_store"
    assert fast["chains"] == []
    assert fast["total_subagents"] == 0
    assert fast["total_chain_cost_usd"] == 0.0


def test_delegation_tree_local_store_honors_spawned_by_full_key(app):
    """When the row's data blob carries ``spawnedBy`` (the OpenClaw
    canonical parent key), the fast path groups by it instead of the
    bare ``parent_session_id`` column. Keeps the response shape
    byte-compatible with the legacy walker (which grouped by full key)."""
    a, ls = app
    store = ls.get_store()
    full_parent_key = "agent:main:session:abc123"

    store.ingest_subagent({
        "subagent_id":       "child-fk",
        "agent_type":        "openclaw",
        "parent_session_id": "abc123",
        "spawnedBy":         full_parent_key,
        "spawned_at":        "2026-05-17T10:00:00Z",
        "task":              "lookup",
        "status":            "active",
        "cost_usd":          0.001,
        "token_count":       500,
        "model":             "claude-haiku-4-5",
        "displayName":       "user inbox triage",
        "updated_at_ms":     int(time.time() * 1000),
    })

    r = a.test_client().get("/api/delegation-tree")
    body = r.get_json()
    assert body["_source"] == "local_store"
    chains = body["chains"]
    assert len(chains) == 1
    ch = chains[0]
    assert ch["parent_key"] == full_parent_key
    assert ch["parent_channel"] == "session"  # parts[2] of canonical key
    assert ch["parent_display"] == "user inbox triage"
    assert ch["children"][0]["prov_parent_key"] == full_parent_key
