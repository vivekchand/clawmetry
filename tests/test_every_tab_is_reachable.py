"""Every tab that ships must be reachable by someone.

Two tabs shipped in every wheel with no way in.

`subagents` — "🤖 Sub-Agents & Queue Lanes" — carried a template, a page
container, three loaders (`loadSubagents`, `loadOrchestration`,
`loadRunLedger`), an agent stop/pause control, a five-second polling timer,
and entries in both the per-runtime capability map and the togglable-tab list.
Its nav item was pulled in 44acaa72f (2026-05-18) because it was stuck on
"Loading..."; the body stayed behind.

`clusters` — "🧔 Session Clusters" — kept a `switchTab()` branch and a
`loadClusters()` renderer that no nav item and no in-app action ever
triggered. It had also rotted: it reads `avg_cost`, `avg_tokens`,
`error_rate` and `rep_session`, and `/api/sessions/clusters` emits none of
those any more. Its live replacement is the Trace Clusters panel inside
Usage, which reads the same endpoint with the shape the endpoint actually
returns.

That is the quietest kind of dead surface: it costs bundle size and
maintenance, the runtime switcher faithfully shows and hides it, capability
plumbing is kept in sync for it, and nothing ever fails — because nobody can
reach the thing that would fail.

The invariant is not "those two tabs are gone". It is that a tab is reachable
**some** way:
  * a sidebar entry — `data-tab="<tab>"` or `switchTab('<tab>')` in the live
    dashboard HTML, or
  * an in-app action — a `switchTab('<tab>')` call in any shipped bundle
    under `clawmetry/static/js/`. Two tabs are legitimately this and neither
    may be flagged: `turn-anatomy`, opened by the session deep-dive handler
    in app.js, and `trail`, opened by `openTrail()` in trail.js. Scanning
    app.js alone would have called `trail` dead — which is why the subject is
    the whole bundle directory, not one file.

The subject is every template under `templates/tabs/` that the live
dashboard actually includes — not `_CM_RT_ALL_TABS`, which is only the
runtime-togglable subset and would have missed `clusters` entirely.
"""
from __future__ import annotations

import re
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
JS_DIR = REPO / "clawmetry" / "static" / "js"
TABS_DIR = REPO / "clawmetry" / "templates" / "tabs"
APP_JS = (JS_DIR / "app.js").read_text(encoding="utf-8")
DASHBOARD = (REPO / "dashboard.py").read_text(encoding="utf-8")

# dashboard.py defines DASHBOARD_HTML twice; the SECOND one wins and is what
# actually serves. The first is dead, so a nav entry found only there would be
# a false pass.
_LIVE_HTML = DASHBOARD[DASHBOARD.rindex('DASHBOARD_HTML = r"""'):]

# Every shipped bundle, not just app.js — trail.js owns the only switchTab()
# call that reaches the trail tab.
_ALL_JS = {p.name: p.read_text(encoding="utf-8") for p in sorted(JS_DIR.glob("*.js"))}


def _shipped_tabs():
    """Tab stems whose template the live dashboard actually includes."""
    return sorted(
        p.stem for p in TABS_DIR.glob("*.html")
        if f"tabs/{p.name}" in _LIVE_HTML
    )


def _reachable(tab: str) -> bool:
    if f'data-tab="{tab}"' in _LIVE_HTML or f"switchTab('{tab}')" in _LIVE_HTML:
        return True
    return any(f"switchTab('{tab}')" in src for src in _ALL_JS.values())


def test_the_subject_is_found():
    tabs = _shipped_tabs()
    assert len(tabs) > 20, f"suspiciously few included tabs: {tabs}"
    assert "app.js" in _ALL_JS and "trail.js" in _ALL_JS, sorted(_ALL_JS)


def test_every_shipped_tab_is_reachable():
    unreachable = [t for t in _shipped_tabs() if not _reachable(t)]
    assert not unreachable, (
        "these tabs ship in every wheel but no user can open them — no nav "
        f"entry and no switchTab() caller in any bundle: {unreachable}. Either "
        "give the tab a way in, or cut it: a surface nobody can reach still "
        "ships, still needs maintaining, and can never report that it is broken."
    )


def test_the_bundle_scan_covers_more_than_app_js():
    """Guard the guard: `trail` passes only because trail.js is scanned.

    A version of this rule that looked at app.js alone would have flagged a
    live, shipped, user-facing tab. That false positive is how a reachability
    rule gets deleted instead of fixed.
    """
    assert "trail" in _shipped_tabs()
    assert "switchTab('trail')" not in APP_JS
    assert "switchTab('trail')" in _ALL_JS["trail.js"]
    assert _reachable("trail")


def test_the_unreachable_subagents_tab_stays_cut():
    """The specific instances, so they cannot quietly return."""
    assert "switchTab('subagents')" not in APP_JS
    assert not (TABS_DIR / "subagents.html").exists(), (
        "the Sub-Agents & Queue Lanes template is back; it had no way in"
    )
    for dead in ("function loadSubagents", "function loadOrchestration",
                 "function loadRunLedger", "function controlAgent"):
        assert dead not in APP_JS, f"{dead} belonged to the unreachable tab"


def test_the_unreachable_clusters_tab_stays_cut():
    assert not (TABS_DIR / "clusters.html").exists(), (
        "the Session Clusters template is back; it had no way in"
    )
    assert "loadClusters" not in APP_JS
    assert "tabs/clusters.html" not in DASHBOARD


def test_the_live_trace_clusters_panel_survived():
    """A near-miss: Trace Clusters in Usage reads the SAME endpoint.

    `renderTraceClusters` is a different, live function that shares both the
    word "clusters" and `/api/sessions/clusters` with the dead tab's loader.
    Deleting by substring or by endpoint would have taken it.
    """
    assert "function renderTraceClusters" in APP_JS
    assert "trace-clusters-content" in APP_JS
    usage = (TABS_DIR / "usage.html").read_text(encoding="utf-8")
    assert 'id="trace-clusters-content"' in usage


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
