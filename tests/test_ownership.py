"""Ownership resolved at ingest: who owns this agent, which team pays.

Before this, a session row carried ``agent_id`` and ``node_id`` and answered
neither question. Ownership existed as a runtime->team label that ONE cost
endpoint applied at query time, and a runtime->owner chip on ONE tab —
so nothing else on the node could scope by either.

These tests use a real DuckDB store (isolated by the conftest scratch path),
not a mock, because the thing under test is the stamping and the re-stamping.

Acceptance criteria proven here (docs/acceptance_criteria.json):

* AC-OBS-004.1 -- a rule attributes matching activity to an owner and a team:
  ``test_rule_stamps_owner_and_team_onto_sessions``,
  ``test_a_new_session_is_stamped_on_arrival``.
* AC-OBS-004.2 -- most specific scope wins, and owner and team resolve
  independently: ``test_most_specific_scope_wins``,
  ``test_owner_and_team_resolve_independently``,
  ``test_blank_field_falls_through_instead_of_erasing``.
* AC-OBS-004.3 -- a rule change re-attributes activity already recorded:
  ``test_existing_sessions_are_restamped_not_just_future_ones``,
  ``test_legacy_team_mapping_write_reaches_the_session_rows``,
  ``test_inventory_owner_edit_reaches_the_session_rows``.
* AC-OBS-004.4 -- removing every matching rule clears the attribution:
  ``test_removing_every_rule_clears_the_stamp``,
  ``test_deleting_a_rule_falls_back_rather_than_keeping_a_stale_owner``.
* AC-OBS-004.5 -- no match reads as unassigned, never a default:
  ``test_no_match_is_unassigned_not_a_guess``,
  ``test_sessions_start_unassigned``.
* AC-OBS-004.6 -- views scope to one owner or team, and to the unassigned
  remainder: ``test_sessions_can_be_filtered_by_team``,
  ``test_unassigned_is_selectable``.
* AC-OBS-004.7 -- a summary reports the unassigned remainder explicitly:
  ``test_summary_reports_the_unassigned_remainder``.
"""
from __future__ import annotations

import importlib
import time

import pytest

from clawmetry.local_store import (
    _OWNERSHIP_SCOPE_ORDER,
    _resolve_ownership,
    _runtime_of_session_id,
)


def _now():
    return time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime())


@pytest.fixture()
def store(tmp_path, monkeypatch):
    # DB_PATH is resolved at import time, so the module is reloaded after the
    # env var is set — same isolation idiom as tests/test_rollup_usage_by_model.
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "t.duckdb"))
    import clawmetry.local_store as ls
    ls = importlib.reload(ls)
    st = ls.LocalStore()
    now = _now()
    st.ingest_sessions_batch([
        {"session_id": "claude_code:aaa", "agent_type": "openclaw",
         "agent_id": "main", "node_id": "box1", "workspace_id": "repoA",
         "last_active_at": now, "cost_usd": 3.0, "total_tokens": 100},
        {"session_id": "bbb-openclaw-uuid", "agent_type": "openclaw",
         "agent_id": "research", "node_id": "box2", "workspace_id": "repoB",
         "last_active_at": now, "cost_usd": 1.0, "total_tokens": 50},
    ])
    return st


def _own(store):
    return {
        r["session_id"]: (r["owner"], r["team"])
        for r in store.query_sessions_table()
    }


# ── the resolver itself (pure) ──────────────────────────────────────────

def test_most_specific_scope_wins():
    rules = {
        ("runtime", "claude_code"): {"owner": "Ada", "team": "Platform"},
        ("agent", "main"): {"owner": "Grace", "team": None},
    }
    owner, team = _resolve_ownership(
        rules, runtime="claude_code", agent_id="main",
        node_id=None, workspace_id=None,
    )
    assert owner == "Grace"       # agent beats runtime
    assert team == "Platform"     # ...but only for the field it sets


def test_owner_and_team_resolve_independently():
    """A team owns the machine; a person owns an agent on it. Forcing both
    fields to come from one rule would make that unexpressible."""
    rules = {
        ("node", "box2"): {"owner": None, "team": "Research"},
        ("agent", "research"): {"owner": "Linus", "team": None},
    }
    owner, team = _resolve_ownership(
        rules, runtime="openclaw", agent_id="research",
        node_id="box2", workspace_id=None,
    )
    assert (owner, team) == ("Linus", "Research")


def test_blank_field_falls_through_instead_of_erasing():
    rules = {
        ("agent", "main"): {"owner": "", "team": ""},
        ("runtime", "claude_code"): {"owner": "Ada", "team": "Platform"},
    }
    assert _resolve_ownership(
        rules, runtime="claude_code", agent_id="main",
        node_id=None, workspace_id=None,
    ) == ("Ada", "Platform")


def test_no_match_is_unassigned_not_a_guess():
    assert _resolve_ownership(
        {}, runtime="openclaw", agent_id="main",
        node_id="box", workspace_id="repo",
    ) == (None, None)


def test_resolver_never_raises_on_garbage():
    assert _resolve_ownership(
        {("runtime", "x"): None}, runtime="x", agent_id=None,
        node_id=None, workspace_id=None,
    ) == (None, None)


def test_scope_order_is_most_specific_first():
    assert _OWNERSHIP_SCOPE_ORDER == ("agent", "workspace", "node", "runtime")


def test_runtime_bucketing_matches_the_runtime_switcher():
    """A rule keyed on a runtime has to bucket sessions the same way the
    runtime switcher does, or it silently matches nothing."""
    assert _runtime_of_session_id("claude_code:aaa", "openclaw") == "claude_code"
    assert _runtime_of_session_id("bbb-uuid", "openclaw") == "openclaw"
    assert _runtime_of_session_id("notaruntime:x", "openclaw") == "openclaw"


# ── stamping at ingest ──────────────────────────────────────────────────

def test_sessions_start_unassigned(store):
    assert _own(store) == {
        "claude_code:aaa": (None, None),
        "bbb-openclaw-uuid": (None, None),
    }


def test_rule_stamps_owner_and_team_onto_sessions(store):
    res = store.set_ownership_rule(
        "runtime", "claude_code", owner="Ada", team="Platform"
    )
    assert res["sessions_restamped"] == 1
    assert _own(store)["claude_code:aaa"] == ("Ada", "Platform")
    assert _own(store)["bbb-openclaw-uuid"] == (None, None)


def test_existing_sessions_are_restamped_not_just_future_ones(store):
    """The rows were ingested BEFORE the rule existed. If a rule only
    applied going forward, the operator would edit it, see no change, and
    conclude the feature is broken."""
    store.set_ownership_rule("node", "box2", team="Research")
    assert _own(store)["bbb-openclaw-uuid"] == (None, "Research")


def test_reingest_preserves_ownership(store):
    store.set_ownership_rule("runtime", "claude_code", owner="Ada", team="Platform")
    store.ingest_sessions_batch([{
        "session_id": "claude_code:aaa", "agent_type": "openclaw",
        "agent_id": "main", "node_id": "box1", "workspace_id": "repoA",
        "last_active_at": _now(), "cost_usd": 4.0,
    }])
    assert _own(store)["claude_code:aaa"] == ("Ada", "Platform")


def test_deleting_a_rule_falls_back_rather_than_keeping_a_stale_owner(store):
    store.set_ownership_rule("runtime", "claude_code", owner="Ada", team="Platform")
    store.set_ownership_rule("agent", "main", owner="Grace")
    assert _own(store)["claude_code:aaa"] == ("Grace", "Platform")
    store.delete_ownership_rule("agent", "main")
    assert _own(store)["claude_code:aaa"] == ("Ada", "Platform")


def test_removing_every_rule_clears_the_stamp(store):
    """Assignment, not COALESCE. If a stamped owner could never be cleared,
    an employee who left would own agents forever."""
    store.set_ownership_rule("runtime", "claude_code", owner="Ada", team="Platform")
    store.delete_ownership_rule("runtime", "claude_code")
    assert _own(store)["claude_code:aaa"] == (None, None)


def test_a_new_session_is_stamped_on_arrival(store):
    store.set_ownership_rule("workspace", "repoC", owner="Ken", team="Compilers")
    store.ingest_session({
        "session_id": "codex:ccc", "agent_type": "openclaw", "agent_id": "x",
        "node_id": "box3", "workspace_id": "repoC", "last_active_at": _now(),
    })
    assert _own(store)["codex:ccc"] == ("Ken", "Compilers")


def test_restamp_is_a_noop_when_nothing_changed(store):
    store.set_ownership_rule("runtime", "claude_code", owner="Ada")
    assert store.restamp_ownership() == 0


# ── scoping by it (the reason to stamp at all) ──────────────────────────

def test_sessions_can_be_filtered_by_team(store):
    store.set_ownership_rule("runtime", "claude_code", team="Platform")
    ids = [r["session_id"] for r in store.query_sessions_table(team="Platform")]
    assert ids == ["claude_code:aaa"]


def test_unassigned_is_selectable(store):
    store.set_ownership_rule("runtime", "claude_code", owner="Ada")
    ids = [r["session_id"] for r in store.query_sessions_table(owner="unassigned")]
    assert ids == ["bbb-openclaw-uuid"]


def test_summary_reports_the_unassigned_remainder(store):
    """"Who owns what" is half the question; "what is not accounted for" is
    the other half, and dropping it would make the totals wrong."""
    store.set_ownership_rule("runtime", "claude_code", owner="Ada", team="Platform")
    s = store.query_ownership_summary(window_days=30)
    assert s["sessions_total"] == 2
    assert s["sessions_assigned"] == 1
    assert s["sessions_unassigned"] == 1
    assert {r["label"] for r in s["by_owner"]} == {"Ada", "unassigned"}
    assert sum(r["sessions"] for r in s["by_owner"]) == s["sessions_total"]


# ── the two older write paths must not diverge ──────────────────────────

def test_legacy_team_mapping_write_reaches_the_session_rows(store):
    store.upsert_team_mapping("runtime", "claude_code", "Legacy Team")
    assert _own(store)["claude_code:aaa"][1] == "Legacy Team"
    assert any(
        r["scope_type"] == "runtime" and r["team"] == "Legacy Team"
        for r in store.list_ownership_rules()
    )


def test_inventory_owner_edit_reaches_the_session_rows(store):
    store.set_agent_meta("openclaw", owner="Linus")
    assert _own(store)["bbb-openclaw-uuid"][0] == "Linus"


def test_new_rule_mirrors_back_into_the_legacy_table(store):
    """Both directions, so the by-team cost rollup and the ownership rules
    cannot show different teams for the same runtime."""
    store.set_ownership_rule("runtime", "claude_code", team="Platform")
    assert {
        (r["key_value"], r["team_label"]) for r in store.list_team_mappings()
    } == {("claude_code", "Platform")}


# ── input validation ────────────────────────────────────────────────────

def test_unknown_scope_type_is_rejected(store):
    with pytest.raises(ValueError):
        store.set_ownership_rule("galaxy", "andromeda", owner="Ada")


def test_empty_scope_value_is_rejected(store):
    with pytest.raises(ValueError):
        store.set_ownership_rule("runtime", "  ", owner="Ada")


def test_a_rule_that_sets_nothing_is_rejected(store):
    with pytest.raises(ValueError):
        store.set_ownership_rule("runtime", "claude_code")
