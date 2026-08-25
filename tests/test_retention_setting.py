"""Retention the buyer can set, and can never use to keep MORE data.

"How long do you keep my data, and can I change it?" is the first question a
security reviewer asks. The answer used to be implicit (your billing tier) and
only changeable through an environment variable set before the daemon started
— which no UI could set, and which does not survive a reinstall.

The invariant that makes exposing this safe is shrink-only: an operator can
always ask for LESS retention and can never grant themselves more than the
plan allows. Half these tests exist to pin that, because the failure that
matters is the one where a settings box quietly extends retention.

Acceptance criteria proven here (docs/acceptance_criteria.json):

* AC-OBS-LADC-004.1 -- the period in force is presented with what is setting
  it: ``test_the_answer_says_which_thing_is_setting_it``,
  ``test_unlimited_says_so_rather_than_showing_a_blank``,
  ``test_env_sourced_window_names_the_env_var``.
* AC-OBS-LADC-004.2 -- the operator can shorten it and the choice persists:
  ``test_asking_for_less_than_the_plan_allows_works``,
  ``test_the_setting_round_trips_through_the_store``.
* AC-OBS-LADC-004.3 -- retention is never lengthened past the ceiling, and
  both numbers are reported:
  ``test_asking_for_more_than_the_plan_allows_changes_nothing``,
  ``test_the_smallest_binding_value_wins``,
  ``test_env_var_still_binds_when_it_is_the_smallest``.
* AC-OBS-LADC-004.4 -- a bad value is rejected, not defaulted:
  ``test_a_bad_value_is_rejected_not_reinterpreted``,
  ``test_a_bad_value_does_not_overwrite_a_good_one``,
  ``test_coerce_rejects_everything_that_is_not_a_positive_whole_number``.
* AC-OBS-LADC-004.5 -- the deletion worker uses the reported period:
  ``test_the_daemon_prune_loop_reads_this_resolver``.
* AC-OBS-LADC-004.6 -- the choice can be cleared:
  ``test_clearing_falls_back_to_the_plan``,
  ``test_clearing_removes_the_row_rather_than_writing_a_sentinel``.
"""
from __future__ import annotations

import importlib

import pytest

from clawmetry import retention as R


class _Ent:
    """Entitlement stub. ``cap=None`` is the unlimited (Enterprise) tier."""

    def __init__(self, cap, tier="oss"):
        self._cap = cap
        self.tier = tier

    def event_retention_days(self):
        return self._cap


@pytest.fixture()
def store(tmp_path, monkeypatch):
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "t.duckdb"))
    monkeypatch.delenv(R.ENV_KEY, raising=False)
    import clawmetry.local_store as ls
    ls = importlib.reload(ls)
    return ls.LocalStore()


# ── the shrink-only invariant ───────────────────────────────────────────

def test_asking_for_more_than_the_plan_allows_changes_nothing(store):
    """The number is stored as asked, so the operator sees their own request
    — but the plan ceiling is what actually prunes. Both are reported, so
    nobody concludes they bought more retention by typing a bigger number."""
    R.set_configured_days(store, 365, entitlement=_Ent(7))
    state = R.resolve(store=store, entitlement=_Ent(7))
    assert state["configured_days"] == 365
    assert state["effective_days"] == 7
    assert state["source"] == "plan"


def test_asking_for_less_than_the_plan_allows_works(store):
    R.set_configured_days(store, 3, entitlement=_Ent(7))
    state = R.resolve(store=store, entitlement=_Ent(7))
    assert state["effective_days"] == 3
    assert state["source"] == "configured"


def test_a_setting_cannot_extend_an_unlimited_tier_downwards_by_accident(store):
    """Enterprise keeps everything by default, but an operator who WANTS a
    shorter window must be able to have one — that is a compliance need, not
    a downgrade."""
    assert R.resolve(store=store, entitlement=_Ent(None))["effective_days"] is None
    R.set_configured_days(store, 30, entitlement=_Ent(None))
    assert R.resolve(store=store, entitlement=_Ent(None))["effective_days"] == 30


def test_the_smallest_binding_value_wins(store, monkeypatch):
    monkeypatch.setenv(R.ENV_KEY, "5")
    R.set_configured_days(store, 2, entitlement=_Ent(30))
    state = R.resolve(store=store, entitlement=_Ent(30))
    assert state["effective_days"] == 2
    assert state["source"] == "configured"


def test_env_var_still_binds_when_it_is_the_smallest(store, monkeypatch):
    """Scripted and fleet installs set the env var; it must not stop working
    just because a UI control now exists."""
    monkeypatch.setenv(R.ENV_KEY, "2")
    R.set_configured_days(store, 10, entitlement=_Ent(30))
    state = R.resolve(store=store, entitlement=_Ent(30))
    assert state["effective_days"] == 2
    assert state["source"] == "env"


# ── clearing, and the difference between "unset" and "zero" ─────────────

def test_clearing_falls_back_to_the_plan(store):
    R.set_configured_days(store, 3, entitlement=_Ent(7))
    R.set_configured_days(store, None, entitlement=_Ent(7))
    state = R.resolve(store=store, entitlement=_Ent(7))
    assert state["configured_days"] is None
    assert state["effective_days"] == 7
    assert state["source"] == "plan"


@pytest.mark.parametrize("bad", [0, -1, "abc", "", "  ", 0.5, [], {}])
def test_a_bad_value_is_rejected_not_reinterpreted(store, bad):
    """Reading 0 or -5 as "some default" is how you end up keeping MORE than
    the operator asked for, so a typo has to be an error."""
    with pytest.raises(ValueError):
        R.set_configured_days(store, bad, entitlement=_Ent(7))


def test_a_bad_value_does_not_overwrite_a_good_one(store):
    R.set_configured_days(store, 3, entitlement=_Ent(7))
    with pytest.raises(ValueError):
        R.set_configured_days(store, 0, entitlement=_Ent(7))
    assert R.resolve(store=store, entitlement=_Ent(7))["configured_days"] == 3


def test_coerce_rejects_everything_that_is_not_a_positive_whole_number():
    for bad in (None, "", "  ", "abc", "0", "-3", 0, -3, 1.5, [], {}):
        assert R._coerce_days(bad) is None
    assert R._coerce_days(1) == 1
    assert R._coerce_days(" 30 ") == 30


# ── the explanation, which is the actual deliverable ────────────────────

def test_the_answer_says_which_thing_is_setting_it(store):
    plan = R.resolve(store=store, entitlement=_Ent(7))["explanation"]
    assert "7 days" in plan and "your plan" in plan

    R.set_configured_days(store, 3, entitlement=_Ent(7))
    mine = R.resolve(store=store, entitlement=_Ent(7))["explanation"]
    assert "3 days" in mine and "You chose this" in mine
    assert "up to 7" in mine  # names the headroom the plan still allows


def test_unlimited_says_so_rather_than_showing_a_blank(store):
    state = R.resolve(store=store, entitlement=_Ent(None, tier="enterprise"))
    assert state["effective_days"] is None
    assert "indefinitely" in state["explanation"]


def test_env_sourced_window_names_the_env_var(store, monkeypatch):
    monkeypatch.setenv(R.ENV_KEY, "2")
    assert R.ENV_KEY in R.resolve(store=store, entitlement=_Ent(30))["explanation"]


def test_singular_day_reads_correctly(store):
    R.set_configured_days(store, 1, entitlement=_Ent(7))
    assert "1 day " in R.resolve(store=store, entitlement=_Ent(7))["explanation"]


# ── never crash: this is a background prune and a settings panel ────────

def test_resolve_survives_a_broken_entitlement(store):
    class Boom:
        tier = "oss"

        def event_retention_days(self):
            raise RuntimeError("boom")

    state = R.resolve(store=store, entitlement=Boom())
    assert state["effective_days"] is None  # conservative: prune nothing


def test_resolve_survives_a_broken_store():
    class Boom:
        def get_node_setting(self, key):
            raise RuntimeError("boom")

    assert R.resolve(store=Boom(), entitlement=_Ent(7))["effective_days"] == 7


def test_resolve_with_no_store_at_all_still_answers():
    assert R.resolve(store=None, entitlement=_Ent(7))["effective_days"] == 7


# ── the setting has to reach the process that actually prunes ───────────

def test_the_setting_round_trips_through_the_store(store):
    R.set_configured_days(store, 4, entitlement=_Ent(30))
    assert store.get_node_setting(R.SETTING_KEY) == "4"
    assert store.list_node_settings()[R.SETTING_KEY] == "4"


def test_clearing_removes_the_row_rather_than_writing_a_sentinel(store):
    R.set_configured_days(store, 4, entitlement=_Ent(30))
    R.set_configured_days(store, None, entitlement=_Ent(30))
    assert store.get_node_setting(R.SETTING_KEY) is None
    assert R.SETTING_KEY not in store.list_node_settings()


def test_the_daemon_prune_loop_reads_this_resolver():
    """The control is worthless if the prune loop keeps its own definition.
    Pinned by source inspection because the loop is a background thread."""
    import inspect

    from clawmetry import sync

    src = inspect.getsource(sync)
    assert "retention as _ret" in src
    assert "_ret.resolve(store=store)" in src


# ── the hosted dashboard must not offer a control it cannot honour ──────

def _app_js():
    from pathlib import Path
    return (Path(__file__).resolve().parent.parent
            / "clawmetry" / "static" / "js" / "app.js").read_text(encoding="utf-8")


def _security_html():
    from pathlib import Path
    return (Path(__file__).resolve().parent.parent
            / "clawmetry" / "templates" / "tabs" / "security.html"
            ).read_text(encoding="utf-8")


def test_hosted_panel_hides_the_control_it_cannot_honour():
    """On cloud there is no node to write to, so the input and its buttons
    must not render. Offering a Save that always fails is worse than not
    offering one."""
    html = _security_html()
    assert 'id="retention-controls"' in html, (
        "the editable controls need their own id so the hosted view can hide them"
    )
    js = _app_js()
    i = js.index("function _renderRetention(")
    body = js[i:i + 2000]
    assert "window.CLOUD_MODE" in body
    assert "retention-controls" in body


def test_hosted_panel_does_not_state_the_plan_number_as_the_machines_setting():
    """The hosted answer comes from the entitlement alone and cannot see a
    shorter period set on the machine. It must be worded as the plan's
    period, not as what this machine actually does."""
    js = _app_js()
    i = js.index("function _renderRetention(")
    body = js[i:i + 2000]
    assert "Your plan keeps event history" in body
    assert "on the machine itself" in body
    # and it must read cap_days (the plan ceiling), never effective_days,
    # which on cloud is the same number wearing a claim it cannot support.
    cloud_branch = body[body.index("window.CLOUD_MODE"):body.index("label.textContent = (state")]
    assert "cap_days" in cloud_branch
    assert "effective_days" not in cloud_branch
