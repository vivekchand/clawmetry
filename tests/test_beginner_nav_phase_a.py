"""Guards for the Phase A beginner-IA nav restructure (UX_AUDIT.md).

The contract:
  * Tier-1 = seven plain-words items (Home, Agents, Activity, Cost,
    Conversations, Approvals, Alerts), in that order, at the top level.
  * Every expert view lives inside the Developer drawer, which is COLLAPSED
    by default (hidden attribute + JS opens only on stored cm_live_open=1).
  * The Developer group header carries NO data-tab: overview belongs to the
    Home item alone (two elements with data-tab="overview" double-highlight).
  * data-tab ids are STABLE across the restructure - deep links, tests and
    the capability-derived visibility map key off them.
  * Crons keeps id="crons-tab" (capability gating hides it per runtime).
  * switchTab reveals a collapsed drawer when a tab inside it is selected.
"""

from __future__ import annotations

import json
import os
import re

_HERE = os.path.dirname(os.path.abspath(__file__))
_DASH = os.path.join(_HERE, "..", "dashboard.py")
_APP_JS = os.path.join(_HERE, "..", "clawmetry", "static", "js", "app.js")
_EN_JSON = os.path.join(_HERE, "..", "clawmetry", "static", "locales", "en.json")


def _nav_block() -> str:
    """The live left-nav markup (from the second DASHBOARD_HTML)."""
    with open(_DASH, encoding="utf-8") as fh:
        src = fh.read()
    start = src.rindex('<aside id="left-nav"')
    end = src.index("</aside>", start)
    return src[start:end]


def _ordered_tabs(html: str) -> list:
    return re.findall(r'data-tab="([a-z-]+)"', html)


def test_tier1_order_and_membership():
    nav = _nav_block()
    tabs = _ordered_tabs(nav)
    tier1 = tabs[:7]
    assert tier1 == [
        "overview", "inventory", "brain", "usage",
        "transcripts", "approvals", "alerts",
    ], f"Tier-1 must be the seven beginner items in order, got {tier1}"


def test_group_header_has_no_data_tab():
    nav = _nav_block()
    header = re.search(r'<div class="left-nav-item left-nav-item-group[^>]*>', nav)
    assert header, "Developer group header missing"
    assert "data-tab" not in header.group(0), (
        "the group header must NOT carry a data-tab: overview belongs to the "
        "Home item alone, or switchTab double-highlights"
    )


def test_developer_drawer_collapsed_by_default():
    nav = _nav_block()
    m = re.search(r'<div class="left-nav-group-list" id="left-nav-live-list"([^>]*)>', nav)
    assert m, "Developer drawer list missing"
    assert "hidden" in m.group(1), "Developer drawer must ship hidden (collapsed) by default"


def test_no_tab_lost_in_restructure():
    """Every pre-restructure destination still exists somewhere in the nav."""
    nav = _nav_block()
    tabs = set(_ordered_tabs(nav))
    expected = {
        # Tier-1
        "overview", "inventory", "brain", "usage", "transcripts",
        "approvals", "alerts",
        # Developer drawer
        "flow", "models", "context", "tracing", "agents", "turn-anatomy",
        "tool-catalog", "context-economics", "harness", "swimlane", "dives",
        # Advanced
        "crons", "memory", "notifications", "security", "policy", "skills",
        "selfevolve", "version-impact", "nemoclaw",
    }
    missing = expected - tabs
    assert not missing, f"tabs lost in the restructure: {sorted(missing)}"


def test_developer_drawer_membership():
    nav = _nav_block()
    m = re.search(
        r'id="left-nav-live-list".*?</div>\s*</div>\s*\n\s*</div>', nav, re.S
    )
    # Simpler: slice from the drawer open to the advanced toggle.
    start = nav.index('id="left-nav-live-list"')
    end = nav.index("left-nav-advanced-toggle", start)
    drawer = nav[start:end]
    got = set(_ordered_tabs(drawer))
    assert got == {
        "flow", "models", "context", "tracing", "agents", "turn-anatomy",
        "tool-catalog", "context-economics", "harness", "swimlane", "dives",
    }, f"Developer drawer membership drifted: {sorted(got)}"


def test_crons_keeps_capability_gating_id():
    nav = _nav_block()
    m = re.search(r'data-tab="crons"[^>]*', nav) or re.search(r'id="crons-tab"[^>]*', nav)
    assert m and ("crons-tab" in m.group(0) or 'data-tab="crons"' in m.group(0))
    # the id and the data-tab must be on the same element
    el = re.search(r'<div[^>]*data-tab="crons"[^>]*>', nav)
    assert el and 'id="crons-tab"' in el.group(0), (
        "crons must keep id='crons-tab' (per-runtime capability gating hides it by id)"
    )


def test_appjs_drawer_default_and_reveal():
    with open(_APP_JS, encoding="utf-8") as fh:
        js = fh.read()
    # Default-collapsed: the restore only OPENS on an explicit stored '1'.
    assert "localStorage.getItem('cm_live_open') === '1'" in js, (
        "drawer restore must open only on stored cm_live_open='1' (collapsed default)"
    )
    assert "var liveOpen = true" not in js, "old default-expanded restore logic is back"
    # Deep-link reveal: selecting a tab inside a hidden drawer un-hides it.
    assert "left-nav-live-list, #left-nav-advanced-list" in js, (
        "switchTab must reveal the collapsed drawer that contains the selected tab"
    )


def test_i18n_keys_present_and_renamed():
    with open(_EN_JSON, encoding="utf-8") as fh:
        en = json.load(fh)
    assert en["nav.home"] == "Home"
    assert en["nav.developer"] == "Developer"
    assert en["nav.brain"] == "Activity"
    assert en["nav.session_replay"] == "Conversations"
    assert en["nav.crons"] == "Schedules"
    for key in ("nav.agent_graph", "nav.turn_timing", "nav.tools",
                "nav.context_usage", "nav.compare_sessions", "nav.ask",
                "nav.runtime_extras", "nav.home_tooltip", "nav.developer_tooltip"):
        assert key in en, f"missing i18n key {key}"
