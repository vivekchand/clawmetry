"""Guards for Phase B of the beginner IA (UX_AUDIT.md): session deep-dive.

Tracing, Turn timing (turn-anatomy) and Compare sessions (swimlane) are
session-scoped, so Phase B moved them OUT of the global nav and into the
session drill-down: the Conversations viewer renders a "Deep dive" action row
whose buttons open each view WITH the session preselected
(openSessionDeepDive). The pages, data-tab ids and switchTab targets all stay,
so old bookmarks keep working.

These guards make sure the drill-down entry point can never silently vanish
while the nav rows are gone - that combination would strand the three views
entirely (the Agent-Graph bug class, but for a whole trio).
"""

from __future__ import annotations

import json
import os
import re

_HERE = os.path.dirname(os.path.abspath(__file__))
_DASH = os.path.join(_HERE, "..", "dashboard.py")
_APP_JS = os.path.join(_HERE, "..", "clawmetry", "static", "js", "app.js")
_EN_JSON = os.path.join(_HERE, "..", "clawmetry", "static", "locales", "en.json")


def _read(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def test_open_session_deep_dive_exists_and_routes():
    """openSessionDeepDive hands the session to the tab loader via the
    _pending* globals (calling viewTrace directly races loadTracing, whose
    async continuation resets the list's style.cssText and un-hides it under
    the detail - the list-bleed bug found during Phase B verification)."""
    js = _read(_APP_JS)
    m = re.search(r"function openSessionDeepDive\(kind, sessionId\).*?\n\}", js, re.S)
    assert m, "openSessionDeepDive missing from app.js"
    body = m.group(0)
    assert "window._pendingTraceSession = sessionId" in body
    assert "window._pendingTurnSession = sessionId" in body
    assert "swimlaneAddLane(sessionId)" in body, "compare deep-dive must add the session lane"


def test_loaders_honor_pending_deep_dive_session():
    js = _read(_APP_JS)
    for loader, pending, view in (
        ("loadTracing", "_pendingTraceSession", "viewTrace"),
        ("loadTurnAnatomy", "_pendingTurnSession", "viewTurnAnatomy"),
    ):
        start = js.find(f"async function {loader}()")
        assert start != -1, f"{loader} missing"
        head = js[start:start + 700]
        assert pending in head and view + "(" in head, (
            f"{loader} must open the pending deep-dive session directly "
            f"(window.{pending} -> {view}) instead of rendering the list"
        )


def test_conversations_viewer_renders_deep_dive_row():
    js = _read(_APP_JS)
    start = js.find("async function viewTranscript(sessionId)")
    assert start != -1, "viewTranscript missing"
    nxt = js.find("\nasync function ", start + 1)
    body = js[start:nxt if nxt != -1 else start + 30000]
    for kind in ("trace", "turns", "compare"):
        # In the JS source the onclick is built inside a single-quoted string,
        # so the quotes are backslash-escaped: openSessionDeepDive(\'trace\', ...
        assert re.search(r"openSessionDeepDive\(\\?'" + kind + r"\\?'", body), (
            f"the Conversations viewer must offer the '{kind}' deep-dive - with "
            "the nav rows gone this row is the ONLY entry point"
        )


def test_pages_still_included_in_live_html():
    """The three pages must keep rendering (deep links + switchTab targets)."""
    dash = _read(_DASH)
    live = dash[dash.rindex('<aside id="left-nav"'):]
    for tpl in ("tabs/tracing.html", "tabs/turn-anatomy.html", "tabs/swimlane.html"):
        assert tpl in live, f"{tpl} must stay included in the live DASHBOARD_HTML"


def test_switchtab_still_wires_the_three_loaders():
    """switchTab('tracing'|'turn-anatomy'|'swimlane') must keep loading - the
    views are reachable by deep link and by openSessionDeepDive even though
    they left the nav (the Agent-Graph dead-wiring class, extended past nav)."""
    js = _read(_APP_JS)
    for tab, loader in (
        ("tracing", "loadTracing"),
        ("turn-anatomy", "loadTurnAnatomy"),
        ("swimlane", "loadSwimlane"),
    ):
        assert re.search(r"if \(name === '%s'\) \{? ?%s\(" % (re.escape(tab), loader), js), (
            f"switchTab must wire '{tab}' -> {loader}()"
        )


def test_i18n_keys_for_deep_dive_row():
    en = json.load(open(_EN_JSON, encoding="utf-8"))
    for key in ("transcript.deep_dive", "transcript.view_trace",
                "transcript.turn_timing", "transcript.compare"):
        assert key in en, f"missing i18n key {key}"
