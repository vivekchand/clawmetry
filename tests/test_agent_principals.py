"""Agent identity: a principal you can attach a policy, a role, or an owner to.

The Agent Inventory rolls up one row per *runtime*, so ownership attached to
"claude_code on this box" rather than to an agent. Without a principal a policy
cannot say *this agent may not do that*, RBAC has no subject, and the audit
chain has no actor beyond a session id.

These tests pin the primitive: identity is DERIVED (stable, reproducible, no
enrolment step, works on history already in the store), it is per-agent rather
than per-runtime, and ownership overlays honestly.
"""

from __future__ import annotations

import importlib
import uuid

import pytest


@pytest.fixture
def store(tmp_path, monkeypatch):
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "events.duckdb"))
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_SECS", "0.05")
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_BATCH", "5")
    import clawmetry.local_store as ls

    importlib.reload(ls)
    s = ls.LocalStore()
    s.start()
    yield s
    s.stop(flush=True)


def _sess(store, session_id, *, node_id="node-a", agent_id="main", **kw):
    row = {
        "session_id": session_id,
        "node_id": node_id,
        "agent_id": agent_id,
        "started_at": kw.pop("started_at", "2026-08-01T00:00:00Z"),
        "last_active_at": kw.pop("last_active_at", "2026-08-02T00:00:00Z"),
        "total_tokens": kw.pop("total_tokens", 10),
        "cost_usd": kw.pop("cost_usd", 0.5),
    }
    row.update(kw)
    store.ingest_session(row)


# ── the id itself ─────────────────────────────────────────────────────────

def test_principal_id_is_deterministic(store):
    a = store.principal_id("node-a", "claude_code", "main")
    b = store.principal_id("node-a", "claude_code", "main")
    assert a == b
    assert a.startswith("ap_")


def test_principal_id_is_case_and_whitespace_insensitive(store):
    """The same agent must not get two identities because a caller shouted."""
    assert store.principal_id("Node-A", "Claude_Code", " Main ") == store.principal_id(
        "node-a", "claude_code", "main"
    )


def test_principal_id_separates_every_axis(store):
    base = store.principal_id("node-a", "claude_code", "main")
    assert store.principal_id("node-b", "claude_code", "main") != base
    assert store.principal_id("node-a", "codex", "main") != base
    assert store.principal_id("node-a", "claude_code", "worker") != base


def test_principal_id_is_not_forgeable_by_field_smashing(store):
    """A separator, not concatenation: ('ab','c') must not collide with
    ('a','bc'). Without the delimiter two different agents share one identity,
    which is the whole point of having one."""
    assert store.principal_id("ab", "c", "main") != store.principal_id("a", "bc", "main")


def test_principal_id_defaults_blank_agent_to_main(store):
    assert store.principal_id("n", "r", "") == store.principal_id("n", "r", "main")


# ── the roster is per-AGENT, which is the entire gap ──────────────────────

def test_two_agents_on_one_runtime_are_two_principals(store):
    _sess(store, "claude_code:s1", agent_id="main")
    _sess(store, "claude_code:s2", agent_id="reviewer")
    rows = store.query_agent_principals()
    ids = {r["principal_id"] for r in rows}
    assert len(ids) == 2, rows
    assert {r["agent_id"] for r in rows} == {"main", "reviewer"}
    # ...and both are correctly attributed to the same runtime.
    assert {r["runtime"] for r in rows} == {"claude_code"}


def test_same_agent_id_on_different_runtimes_stays_distinct(store):
    _sess(store, "claude_code:s1", agent_id="main")
    _sess(store, "codex:s2", agent_id="main")
    rows = store.query_agent_principals()
    assert len({r["principal_id"] for r in rows}) == 2
    assert {r["runtime"] for r in rows} == {"claude_code", "codex"}


def test_runtime_comes_from_the_session_prefix_not_agent_type(store):
    """Same rule as sync._runtime_of_session / the frontend's _cmRuntimeOf."""
    _sess(store, "codex:s1", agent_type="openclaw")
    rows = store.query_agent_principals()
    assert rows and rows[0]["runtime"] == "codex"


def test_unprefixed_session_falls_back_to_the_openclaw_bucket(store):
    _sess(store, "plain-session-id")
    rows = store.query_agent_principals()
    assert rows and rows[0]["runtime"] == "openclaw"


def test_sessions_are_counted_and_aggregated_per_principal(store):
    _sess(store, "claude_code:s1", total_tokens=10, cost_usd=1.0)
    _sess(store, "claude_code:s2", total_tokens=5, cost_usd=0.25)
    rows = store.query_agent_principals()
    assert len(rows) == 1
    assert rows[0]["sessions"] == 2
    assert rows[0]["total_tokens"] == 15
    assert rows[0]["cost_usd"] == pytest.approx(1.25)


def test_filters_narrow_the_roster(store):
    _sess(store, "claude_code:s1", node_id="node-a")
    _sess(store, "codex:s2", node_id="node-b")
    assert len(store.query_agent_principals(runtime="codex")) == 1
    assert len(store.query_agent_principals(node_id="node-a")) == 1
    assert len(store.query_agent_principals()) == 2


def test_empty_store_returns_empty_not_an_error(store):
    assert store.query_agent_principals() == []


# ── ownership overlays honestly ───────────────────────────────────────────

def test_owner_attaches_to_the_agent_not_the_runtime(store):
    _sess(store, "claude_code:s1", agent_id="main")
    _sess(store, "claude_code:s2", agent_id="reviewer")
    rows = {r["agent_id"]: r for r in store.query_agent_principals()}
    store.set_agent_meta(rows["reviewer"]["principal_id"], owner="platform-team")

    after = {r["agent_id"]: r for r in store.query_agent_principals()}
    assert after["reviewer"]["owner"] == "platform-team"
    assert after["reviewer"]["owner_source"] == "agent"
    # The sibling agent on the SAME runtime must not inherit it.
    assert after["main"]["owner"] == ""


def test_unclaimed_agent_inherits_its_runtime_owner_but_says_so(store):
    """Inheritance is useful; pretending a human named this agent is not."""
    _sess(store, "claude_code:s1")
    store.set_agent_meta("claude_code", owner="sre")
    row = store.query_agent_principals()[0]
    assert row["owner"] == "sre"
    assert row["owner_source"] == "runtime"


def test_unowned_agent_reports_no_owner_source(store):
    _sess(store, "claude_code:s1")
    row = store.query_agent_principals()[0]
    assert row["owner"] == ""
    assert row["owner_source"] == ""


def test_agent_label_wins_over_the_runtime_label(store):
    _sess(store, "claude_code:s1")
    store.set_agent_meta("claude_code", owner="sre")
    pid = store.query_agent_principals()[0]["principal_id"]
    store.set_agent_meta(pid, owner="ml-team")
    row = store.query_agent_principals()[0]
    assert row["owner"] == "ml-team"
    assert row["owner_source"] == "agent"


def test_identity_is_stable_across_a_store_restart(store, tmp_path, monkeypatch):
    """Derived, not minted: nothing is persisted that a restart could lose."""
    _sess(store, "claude_code:s1")
    before = store.query_agent_principals()[0]["principal_id"]
    store.stop(flush=True)

    import clawmetry.local_store as ls

    reopened = ls.LocalStore()
    reopened.start()
    try:
        after = reopened.query_agent_principals()[0]["principal_id"]
    finally:
        reopened.stop(flush=True)
    assert before == after
