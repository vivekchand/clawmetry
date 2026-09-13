"""Ownership inherits up a ladder, and team is its own question.

Agent principals answer "who owns this agent" by DERIVING identity from what
sessions already carry -- no migration, retroactive, cannot go stale. Two
things they did not answer, which this adds:

* inheritance was one rung deep (an agent inherited only its RUNTIME's owner),
  so "everything on this build box belongs to Platform" was unsayable and
  labelling a fleet by hand is the labelling that does not get done;
* team shared the owner's free-text field, so naming a person cost you the
  team rollup.

Deliberately NOT here: ownership columns on the session record, resolution at
ingest, or a re-stamp when a label changes. That design was built and closed
unmerged (PR #5165) because deriving beat stamping -- see REQ-OBS-004's
rejected alternatives. ``test_ownership_is_not_stored_on_sessions`` keeps it
from creeping back.

Acceptance criteria proven here (docs/acceptance_criteria.json):

* AC-OBS-004.1 -- team distinct from owner: ``test_team_is_its_own_field``
* AC-OBS-004.2 -- inherit from the most specific enclosing scope:
  ``test_a_machine_label_covers_every_agent_on_it``,
  ``test_the_most_specific_rung_wins``
* AC-OBS-004.3 -- report which rung answered: ``test_each_value_names_its_rung``
* AC-OBS-004.4 -- owner and team resolve independently:
  ``test_owner_and_team_come_from_different_rungs``
* AC-OBS-004.5 -- no match reads as unassigned: ``test_unclaimed_is_unassigned``
* AC-OBS-004.6 -- derived, not stored: ``test_ownership_is_not_stored_on_sessions``,
  ``test_a_label_applies_to_history_already_collected``
"""
from __future__ import annotations

import importlib
import time

import pytest


@pytest.fixture()
def store(tmp_path, monkeypatch):
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "t.duckdb"))
    import clawmetry.local_store as ls
    ls = importlib.reload(ls)
    st = ls.LocalStore()
    now = time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime())
    st.ingest_sessions_batch([
        {"session_id": "claude_code:a", "agent_type": "openclaw",
         "agent_id": "main", "node_id": "box1", "last_active_at": now,
         "cost_usd": 3.0},
        {"session_id": "claude_code:b", "agent_type": "openclaw",
         "agent_id": "research", "node_id": "box1", "last_active_at": now,
         "cost_usd": 1.0},
        {"session_id": "codex:c", "agent_type": "openclaw",
         "agent_id": "main", "node_id": "box2", "last_active_at": now,
         "cost_usd": 2.0},
    ])
    return st


def _by(store, agent_id):
    return next(p for p in store.query_agent_principals()
                if p["agent_id"] == agent_id)


def _all(store):
    return store.query_agent_principals()


# ── the gaps this closes ────────────────────────────────────────────────

def test_a_machine_label_covers_every_agent_on_it(store):
    """One action, a whole box. Before this each runtime on each machine had
    to be labelled by hand, which is the labelling that does not happen."""
    store.set_agent_meta(store.node_scope_key("box1"), team="Platform")
    on_box1 = [p for p in _all(store) if p["node_id"] == "box1"]
    assert len(on_box1) == 2
    assert {p["team"] for p in on_box1} == {"Platform"}
    assert {p["team_source"] for p in on_box1} == {"node"}
    # and it stops at the machine boundary
    assert _by(store, "main")["team"] in ("Platform", "")
    assert next(p for p in _all(store) if p["node_id"] == "box2")["team"] == ""


def test_team_is_its_own_field(store):
    """Naming a person must not cost you the team rollup."""
    pid = _by(store, "research")["principal_id"]
    store.set_agent_meta(pid, owner="Grace", team="Research")
    p = _by(store, "research")
    assert p["owner"] == "Grace"
    assert p["team"] == "Research"


def test_owner_and_team_come_from_different_rungs(store):
    """A machine belongs to a team while a person owns one agent on it. Bind
    both to one rung and that pair becomes unexpressible."""
    store.set_agent_meta(store.node_scope_key("box1"), team="Platform")
    store.set_agent_meta("claude_code", owner="Ada")
    p = _by(store, "main")
    assert (p["owner"], p["owner_source"]) == ("Ada", "runtime")
    assert (p["team"], p["team_source"]) == ("Platform", "node")


def test_the_most_specific_rung_wins(store):
    store.set_agent_meta("claude_code", owner="Ada")
    store.set_agent_meta(store.node_scope_key("box1"), owner="Box Owner")
    pid = _by(store, "research")["principal_id"]
    store.set_agent_meta(pid, owner="Grace")
    assert _by(store, "research")["owner"] == "Grace"
    assert _by(store, "research")["owner_source"] == "agent"
    # the sibling with no label of its own takes the machine, not the runtime
    assert _by(store, "main")["owner"] == "Box Owner"
    assert _by(store, "main")["owner_source"] == "node"


def test_each_value_names_its_rung(store):
    """An inherited owner must never read as one somebody chose for this
    agent. The single-rung version already did this; a deeper ladder makes it
    matter more."""
    store.set_agent_meta("claude_code", owner="Ada")
    p = _by(store, "main")
    assert p["owner_source"] == "runtime"
    pid = p["principal_id"]
    store.set_agent_meta(pid, owner="Ada")
    assert _by(store, "main")["owner_source"] == "agent"


def test_unclaimed_is_unassigned(store):
    for p in _all(store):
        assert p["owner"] == "" and p["owner_source"] == ""
        assert p["team"] == "" and p["team_source"] == ""


# ── the design decision, guarded ────────────────────────────────────────

def test_ownership_is_not_stored_on_sessions(store):
    """PR #5165 stamped owner/team onto session rows at ingest. That needed a
    migration, a full-table re-stamp inside the write lock on an ordinary
    label edit, and stored values that drift from the labels producing them.
    Deriving does the same job with none of it -- so the columns must not
    come back."""
    cols = {r[1] for r in store._conn.execute(
        "PRAGMA table_info('sessions')").fetchall()}
    assert "owner" not in cols
    assert "team" not in cols


def test_a_label_applies_to_history_already_collected(store):
    """The property stamping gives up: a label set today covers sessions
    recorded before it existed, because nothing was written at ingest."""
    store.set_agent_meta("codex", team="Data")
    p = next(x for x in _all(store) if x["runtime"] == "codex")
    assert p["team"] == "Data"
    assert p["sessions"] == 1


def test_clearing_a_label_falls_back_down_the_ladder(store):
    store.set_agent_meta("claude_code", owner="Ada")
    pid = _by(store, "research")["principal_id"]
    store.set_agent_meta(pid, owner="Grace")
    assert _by(store, "research")["owner"] == "Grace"
    store.set_agent_meta(pid, owner="")
    p = _by(store, "research")
    assert p["owner"] == "Ada"
    assert p["owner_source"] == "runtime"


def test_scope_keys_cannot_collide(store):
    """Three key shapes share one free-form column: principal ids ("ap_..."),
    machine scopes ("node:...") and bare runtime names."""
    pid = _by(store, "main")["principal_id"]
    assert pid.startswith("ap_")
    assert store.node_scope_key("box1") == "node:box1"
    assert not store.node_scope_key("box1").startswith("ap_")
    assert ":" not in "claude_code"


def test_partial_update_leaves_the_other_field_alone(store):
    pid = _by(store, "main")["principal_id"]
    store.set_agent_meta(pid, owner="Ada", team="Platform")
    store.set_agent_meta(pid, owner="Linus")
    p = _by(store, "main")
    assert p["owner"] == "Linus"
    assert p["team"] == "Platform"
