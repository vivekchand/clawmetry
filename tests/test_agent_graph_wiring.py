"""Guards for the Agent Graph tab wiring (founder report 2026-07-02).

The bug class: dashboard.py defines DASHBOARD_HTML twice and only the SECOND
renders. #3315 added `if (name === 'agents') loadAgentGraph();` to the inline
switchTab inside the DEAD first block, so the loader never fired and the tab
sat on its static "Loading..." forever, on localhost and cloud alike.

Guards:
  1. The LIVE switchTab (static/js/app.js) wires every nav tab that has a
     dedicated loader - specifically 'agents' -> loadAgentGraph.
  2. Class-wide: any `if (name === '<tab>') load...()` wiring that exists ONLY
     in dashboard.py (the dead inline switchTab) and not in app.js is flagged.
  3. The loader renders an honest message on the cloud's 410 (disabled
     /api/local/*) instead of pretending there is no data.
"""

from __future__ import annotations

import os
import re

_HERE = os.path.dirname(os.path.abspath(__file__))
_DASH = os.path.join(_HERE, "..", "dashboard.py")
_APP_JS = os.path.join(_HERE, "..", "clawmetry", "static", "js", "app.js")


def _read(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def test_live_switchtab_wires_agent_graph():
    js = _read(_APP_JS)
    assert re.search(r"if \(name === 'agents'\) loadAgentGraph\(\);", js), (
        "app.js switchTab must call loadAgentGraph() for the 'agents' tab - "
        "wiring it only in dashboard.py's dead inline switchTab leaves the tab "
        "on 'Loading...' forever"
    )


def test_no_wiring_exists_only_in_dead_block():
    """Class guard: every dead-block tab wiring must also exist in app.js."""
    dash = _read(_DASH)
    js = _read(_APP_JS)
    dead_wirings = set(re.findall(r"if \(name === '([a-z-]+)'\) load\w+\(\);", dash))
    live_wirings = set(re.findall(r"if \(name === '([a-z-]+)'\)", js))
    # Tabs that exist only in the dead block AND are reachable from the live
    # nav (data-tab present in the live DASHBOARD_HTML) are broken.
    live_html_start = dash.rindex('<aside id="left-nav"')
    nav = dash[live_html_start:dash.index("</aside>", live_html_start)]
    nav_tabs = set(re.findall(r'data-tab="([a-z-]+)"', nav))
    orphaned = (dead_wirings - live_wirings) & nav_tabs
    assert not orphaned, (
        f"tab loader(s) wired ONLY in the dead first DASHBOARD_HTML: {sorted(orphaned)} - "
        "move the wiring to static/js/app.js switchTab or the tab never loads"
    )


def test_loader_handles_cloud_410_honestly():
    js = _read(_APP_JS)
    m = re.search(r"function loadAgentGraph\(\).*?\n\}", js, re.S)
    assert m, "loadAgentGraph missing"
    body = m.group(0)
    assert "410" in body and "agent_graph_local_only" in body, (
        "loadAgentGraph must show the honest local-only message on the cloud's "
        "410, not an empty-data state"
    )
