"""Every tab the runtime switcher toggles must be reachable by someone.

The `subagents` tab — "🤖 Sub-Agents & Queue Lanes" — shipped in every wheel
with a template, a page container, three loaders (`loadSubagents`,
`loadOrchestration`, `loadRunLedger`), an agent stop/pause control, a
five-second polling timer, and entries in both the per-runtime capability map
and the togglable-tab list.

`switchTab('subagents')` had **zero callers**. Not in the OSS sidebar, not in
clawmetry-cloud's nav, not from any in-app action. No user could open it.

That is the quietest kind of dead surface: it costs bundle size and
maintenance, the runtime switcher faithfully shows and hides it, capability
plumbing is kept in sync for it, and nothing ever fails — because nobody can
reach the thing that would fail.

The invariant is not "the subagents tab is gone". It is that a tab is reachable
**some** way:
  * a sidebar entry — `data-tab="<tab>"` or `switchTab('<tab>')` in the live
    dashboard HTML, or
  * an in-app action — a `switchTab('<tab>')` call in app.js. `turn-anatomy`
    is legitimately this: it has no nav item and is opened by the session
    deep-dive handler.

Anything in `_CM_RT_ALL_TABS` with neither is unreachable by construction.
"""
from __future__ import annotations

import re
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
APP_JS = (REPO / "clawmetry" / "static" / "js" / "app.js").read_text(encoding="utf-8")
DASHBOARD = (REPO / "dashboard.py").read_text(encoding="utf-8")

# The LAST DASHBOARD_HTML assignment is what serves. There used to be a dead
# first one whose nav entries rendered for nobody; it was deleted 2026-09-08.
# `rindex` keeps this correct either way.
_LIVE_HTML = DASHBOARD[DASHBOARD.rindex('DASHBOARD_HTML = r"""'):]


def _togglable_tabs():
    m = re.search(r"var _CM_RT_ALL_TABS = \[([\s\S]*?)\];", APP_JS)
    assert m, "_CM_RT_ALL_TABS not found — the guard has lost its subject"
    return re.findall(r"'([a-z0-9_-]+)'", m.group(1))


def test_the_togglable_tab_list_is_found():
    tabs = _togglable_tabs()
    assert len(tabs) > 5, f"suspiciously few togglable tabs: {tabs}"


def test_every_togglable_tab_is_reachable():
    unreachable = []
    for tab in _togglable_tabs():
        in_nav = (f'data-tab="{tab}"' in _LIVE_HTML) or (f"switchTab('{tab}')" in _LIVE_HTML)
        in_app = f"switchTab('{tab}')" in APP_JS
        if not (in_nav or in_app):
            unreachable.append(tab)
    assert not unreachable, (
        "these tabs are toggled by the runtime switcher but no user can open "
        f"them — no nav entry and no switchTab() caller: {unreachable}. Either "
        "give the tab a way in, or cut it: a surface nobody can reach still "
        "ships, still needs maintaining, and can never report that it is broken."
    )


def test_the_unreachable_subagents_tab_stays_cut():
    """The specific instance, so it cannot quietly return."""
    assert "switchTab('subagents')" not in APP_JS
    assert not (REPO / "clawmetry" / "templates" / "tabs" / "subagents.html").exists(), (
        "the Sub-Agents & Queue Lanes template is back; it had no way in"
    )
    for dead in ("function loadSubagents", "function loadOrchestration",
                 "function loadRunLedger", "function controlAgent"):
        assert dead not in APP_JS, f"{dead} belonged to the unreachable tab"


def test_the_live_session_orchestration_panel_survived():
    """A near-miss: _loadOrchestrationPanel is a DIFFERENT, live function.

    It renders the orchestration panel inside the session detail view
    (templates/tabs/transcripts.html) and merely shares a name prefix with the
    dead tab's loader. Deleting by substring match would have taken it.
    """
    assert "_loadOrchestrationPanel" in APP_JS, (
        "the session-detail orchestration panel was removed along with the "
        "dead tab — it is a different function and is live"
    )
