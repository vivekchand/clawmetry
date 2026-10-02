"""Guards for the Trail page + the session-first landing.

The contract:
  * ``tabs/trail.html`` is included by the LIVE (second) ``DASHBOARD_HTML``
    and its wrapper is ``<div class="page" id="page-trail">`` (template stem
    == tab id, #5476), with the three section ids a newcomer reads top to
    bottom: ``trail-inputs`` / ``trail-decisions`` / ``trail-outcome``.
  * The product opens on the Sessions list (``page-transcripts`` carries the
    default ``active`` class; Overview no longer does) and the Sessions nav
    item is the highlighted landing entry, first in the nav.
  * Overview sits under a "Monitoring" section label along with Cost, Models
    and Context usage; every pre-existing tab is still reachable.
  * ``static/js/trail.js`` ships, is referenced by the live HTML, and app.js
    routes ``#trail=`` deep links + dispatches ``switchTab('trail')``.
  * Every string the page shows has an ``en.json`` key, and no user-facing
    copy carries an em-dash or a double hyphen.

The Jinja render below is the proof the markup is in the SERVED page, not
just in a template file nobody includes (FLYWHEEL 0a.4: no dead UI).
"""

from __future__ import annotations

import json
import os
import re
import sys
import shutil
import subprocess

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.abspath(os.path.join(_HERE, ".."))
_DASH = os.path.join(_ROOT, "dashboard.py")
_APP_JS = os.path.join(_ROOT, "clawmetry", "static", "js", "app.js")
_TRAIL_JS = os.path.join(_ROOT, "clawmetry", "static", "js", "trail.js")
_TRAIL_HTML = os.path.join(_ROOT, "clawmetry", "templates", "tabs", "trail.html")
_EN_JSON = os.path.join(_ROOT, "clawmetry", "static", "locales", "en.json")
_CSS = os.path.join(_ROOT, "clawmetry", "static", "css", "dashboard.css")
_CI = os.path.join(_ROOT, ".github", "workflows", "ci.yml")


def _read(p: str) -> str:
    with open(p, encoding="utf-8") as fh:
        return fh.read()


def test_tab_navigation_survives_reload_and_preserves_session_links():
    """A Home click must replace a stale Assistant hash before reload."""
    node = shutil.which("node")
    if not node:
        pytest.skip("Node.js is not installed")
    source = _read(_APP_JS)
    switch_head = source[source.index("function switchTab(name)"):source.index("  // Tell the user, on every tab")]
    router = source[source.index("function _cmTabFromHash()"):source.index("function _cmBootLanding()")]
    script = r"""
      const assert = require('assert');
      const pages = new Set(['assistant', 'overview', 'setup', 'improve', 'guard', 'trail', 'transcripts']);
      const window = {location: {hash:'#assistant', pathname:'/', search:''}};
      window.history = {replaceState(_state,_title,url) { window.location.hash=url.slice(url.indexOf('#')); }};
      const document = {body:{classList:{toggle(){}}},querySelectorAll(){return []},
        getElementById(id){return pages.has(id.replace('page-','')) ? {classList:{add(){}}} : null}};
      function cancelAllPendingSSEDwell() {}
      let _cmCurrentTab;
    """ + switch_head + "\n}\n" + router + r"""
      switchTab('overview');
      assert.equal(window.location.hash, '#overview');
      assert.equal(_cmTabFromHash(), 'overview');
      switchTab('setup'); assert.equal(_cmTabFromHash(), 'setup');
      switchTab('guard'); assert.equal(_cmTabFromHash(), 'guard');
      window.location.hash='#trail=codex%3Atest'; switchTab('trail');
      assert.equal(window.location.hash, '#trail=codex%3Atest');
      window.location.hash='#session=codex%3Atest'; switchTab('transcripts');
      assert.equal(window.location.hash, '#session=codex%3Atest');
      switchTab('assistant'); assert.equal(_cmTabFromHash(), 'assistant');
      window.location.hash='#does-not-exist'; assert.equal(_cmTabFromHash(), null);
    """
    subprocess.run([node, "-e", script], check=True, capture_output=True, text=True)


def _live_html_source() -> str:
    """The second ``DASHBOARD_HTML`` literal (the one that renders)."""
    src = _read(_DASH)
    start = src.rindex('DASHBOARD_HTML = r"""')
    end = src.index('"""', start + len('DASHBOARD_HTML = r"""'))
    return src[start:end]


_INCLUDE_RE = re.compile(r"""\{%\s*include\s+['"]([^'"]+)['"]\s*%\}""")


def _rendered_live_html() -> str:
    """The live template with every ``{% include %}`` expanded from
    ``clawmetry/templates`` (the folder Flask renders from), so the proof is
    about the markup that is actually served, not a template file nobody
    includes. Plain string expansion: no template engine needed in the lint
    job, and nothing here is rendered for a browser.
    """
    tpl_dir = os.path.join(_ROOT, "clawmetry", "templates")
    src = _live_html_source()
    body = src[src.index('r"""') + 4:]

    def expand(text: str, depth: int = 0) -> str:
        if depth > 5:
            return text

        def sub(m):
            with open(os.path.join(tpl_dir, m.group(1)), encoding="utf-8") as fh:
                return expand(fh.read(), depth + 1)

        return _INCLUDE_RE.sub(sub, text)

    return expand(body)


def test_trail_template_is_included_in_live_html():
    live = _live_html_source()
    assert "{% include 'tabs/trail.html' %}" in live, (
        "tabs/trail.html must be included by the LIVE (second) DASHBOARD_HTML"
    )
    assert "js/trail.js" in live, "static/js/trail.js must be loaded by the live HTML"


def test_trail_wrapper_and_sections_render():
    html = _rendered_live_html()
    assert re.search(r'<div class="page" id="page-trail"', html), (
        "the Trail wrapper must be <div class=\"page\" id=\"page-trail\"> (stem == tab id, #5476)"
    )
    for sec in ("trail-inputs", "trail-decisions", "trail-outcome"):
        assert f'id="{sec}"' in html, f"missing Trail section #{sec}"
    # Newcomer language on the three headings.
    for key in ("trail.inputs_title", "trail.decisions_title", "trail.outcome_title"):
        assert f'data-i18n="{key}"' in html, f"heading {key} must be i18n-keyed"
    # Sub-views inside "What it did": Trace + Turn timing are reachable here,
    # not (only) from the global nav.
    for view in ("replay", "trace", "turns", "tree"):
        assert f'data-view="{view}"' in html, f"missing decisions sub-view {view}"
    assert 'id="trail-export-btn"' in html


def test_default_landing_is_the_conversational_assistant():
    html = _rendered_live_html()
    actives = re.findall(r'<div class="page active" id="(page-[a-z-]+)"', html)
    assert actives == ["page-assistant"]
    nav_start = html.index('<aside id="left-nav"')
    nav = html[nav_start:html.index("</aside>", nav_start)]
    tabs = re.findall(r'data-tab="([a-z-]+)"', nav)
    prehighlighted = re.findall(r'<div class="left-nav-item active"[^>]*data-tab="([a-z-]+)"', nav)
    assert prehighlighted == ["assistant"]
    assert 'data-i18n="nav.section_monitoring"' in nav, "Overview must sit under a Monitoring label"
    # Monitoring holds Home, Agents, Sessions + the raw-signal views; order is stable.
    mon = nav.index('data-i18n="nav.section_monitoring"')
    ana = nav.index('data-i18n="nav.section_analyze"')
    assert re.findall(r'data-tab="([a-z-]+)"', nav[mon:ana]) == [
        "overview", "inventory", "setup", "improve", "transcripts", "brain", "usage", "models",
        "context-economics",
    ]
    # Nothing lost.
    for tab in ("overview", "inventory", "brain", "usage", "models", "context-economics",
                    "evals", "bench", "guard", "notifications",
                "flow", "tracing", "agents", "tool-catalog", "harness",
                "crons", "memory", "skills", "logs", "security", "policy",
                "selfevolve", "version-impact", "nemoclaw"):
        assert tab in tabs, f"tab {tab} lost from the nav"
    # Guard owns the review destinations, whose page ids and deep links stay.
    for tab in ("approvals", "alerts"):
        assert 'id="page-%s"' % tab in html
        assert "switchTab('%s')" % tab in html


def test_nav_default_highlight_equals_the_declared_landing_tab():
    """The markup default and CM_LANDING_TAB are one decision, so read both.

    The previous guards asserted each half against a literal, which is how
    they both passed while disagreeing would still be possible: change the
    constant, forget the template, and the reader sees a highlight on a
    screen they are not on until the first script runs. Compare them to
    each other instead of to a string typed twice.
    """
    html = _rendered_live_html()
    js = _read(_APP_JS)
    declared = re.search(r"var CM_LANDING_TAB = '([a-z-]+)';", js)
    assert declared, "app.js must declare CM_LANDING_TAB"
    landing = declared.group(1)
    nav_start = html.index('<aside id="left-nav"')
    nav = html[nav_start:html.index("</aside>", nav_start)]
    highlighted = re.findall(
        r'<div class="left-nav-item active"[^>]*data-tab="([a-z-]+)"', nav
    )
    assert highlighted == [landing], (
        f"nav pre-highlights {highlighted}, app.js lands on {landing!r}: "
        "they must be the same one tab"
    )
    # ...and so must the page that ships .active, or the highlight points at
    # one screen while another is on show.
    pages = re.findall(r'<div class="page active" id="page-([a-z-]+)"', html)
    assert pages == [landing], (
        f"the active page is {pages}, app.js lands on {landing!r}"
    )


def test_appjs_routes_trail():
    js = _read(_APP_JS)
    assert "if (name === 'trail')" in js, "switchTab must dispatch the trail tab"
    assert "loadTrailTab" in js and "_trailRestoreHosts" in js
    assert "_trailSessionFromHash(window.location.hash)" in js, "#trail= deep links must be routed"
    assert "function _cmBootLanding()" in js
    # The landing tab is declared once and the nav markup agrees with it
    # (checked above). A #session= deep link still opens the Sessions list.
    assert "var CM_LANDING_TAB = 'assistant';" in js, (
        "the boot landing must default to the conversational assistant"
    )
    assert "switchTab(CM_LANDING_TAB);" in js, "_cmBootLanding must use the declared landing tab"
    assert "/[#&]session=/.test" in js, "a #session= deep link must still land on Sessions"
    assert "_cmVerdictBadge(tx)" in js, "session rows must carry the verdict badge"
    assert "openTrail(this.getAttribute" in js, "session rows need a one-click Open trail"


def test_trail_js_public_surface_and_honest_states():
    js = _read(_TRAIL_JS)
    for fn in ("window.openTrail", "window.loadTrailTab", "window._trailRestoreHosts",
               "window.trailShowView", "window.trailExport", "window._trailSessionFromHash",
               "window._cmVerdictBadge"):
        assert fn in js, f"trail.js must define {fn}"
    # Reuse, not copies, of the existing renderers.
    for entry in ("viewTranscript(sid)", "viewTrace(sid)", "viewTurnAnatomy(sid)"):
        assert entry in js, f"trail.js must drive the existing renderer via {entry}"
    # Endpoints other streams are landing are consumed defensively.
    for url in ("/context", "/git-outcomes", "/api/trail/coverage", "/api/replay-tree/",
                "/api/evals/session/", "/export?format=json"):
        assert url in js, f"trail.js must call {url}"
    for key in ("trail.context_not_captured", "trail.git_off", "trail.git_not_captured",
                "trail.outcome_unknown", "trail.quality_none", "trail.tree_empty"):
        assert key in js, f"missing honest empty-state copy {key}"
    assert "_evalsLockedHtml" in js, "402 on the judge score must reuse the entitlement helper"
    # All six outcome labels are explained.
    for lbl in ("success", "failed", "escalated", "cognitive_loop", "tool_call_stuck", "ongoing"):
        assert f"{lbl}:" in js, f"outcome label {lbl} missing from the legend"


def test_i18n_keys_present_and_clean():
    en = json.loads(_read(_EN_JSON))
    html = _read(_TRAIL_HTML)
    js = _read(_TRAIL_JS)
    for key in re.findall(r'data-i18n(?:-title)?="([a-z0-9_.]+)"', html):
        assert key in en, f"missing i18n key {key}"
    # T('trail.outcome_' + label, ...) builds its key at runtime; the six
    # concrete keys are asserted in test_trail_js_public_surface_and_honest_states.
    for key in re.findall(r"T\('([a-z0-9_.]+)',", js):
        assert key in en, f"missing i18n key {key}"
    assert en["nav.section_monitoring"] == "Monitoring"
    for key, val in en.items():
        if key.startswith("trail.") or key == "nav.section_monitoring":
            assert "—" not in val and "--" not in val, f"banned dash in {key}"
    # The page's literal fallbacks are clean too.
    body = re.sub(r"<!--.*?-->", "", html, flags=re.S)
    assert "—" not in body and "--" not in body


def test_css_scoped_under_page_trail():
    css = _read(_CSS)
    assert "#page-trail .trail-section" in css
    assert ".cm-verdict" in css and ".cm-open-trail" in css


def test_registered_in_ci_explicit_lists():
    ci = _read(_CI)
    assert "tests/test_trail_tab_template.py" in ci, (
        "CI runs explicit file lists; this test must be named in ci.yml or it never runs"
    )
