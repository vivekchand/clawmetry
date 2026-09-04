"""Every tab template must be a `.page` panel the tab switcher can hide.

The dashboard shows exactly one `<div class="page" id="page-<tab>">` at a
time: `.page { display:none }` and `.page.active { display:block }`, and
`switchTab(name)` toggles `.active` on `#page-<name>`. A template wrapped
in any other class is never hidden, so it renders on TOP of every tab.

That is precisely what shipped in 0.12.806 (#5367): guard.html opened with
`<div id="guard" class="tab-content">`, a class this app has no CSS or JS
for. Every tab (Agents, Activity, Sessions, Cost, Quality, ...) showed the
Guard cards stuck on "Loading..." above its own content, and the Guard
loader never fired because `#page-guard` did not exist.

Second half of the same field hit: `guard` sat in `_CM_RT_ALL_TABS`
(togglable per runtime) but in neither `_CM_NODE_TABS` nor any capability
map, so selecting any runtime hid the Guard nav item entirely.

Acceptance:
    pytest tests/test_tab_template_page_wrapper.py -q
"""
from __future__ import annotations

import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent.parent
TABS_DIR = ROOT / "clawmetry" / "templates" / "tabs"
APP_JS = ROOT / "clawmetry" / "static" / "js" / "app.js"


def test_every_tab_template_declares_a_page_panel() -> None:
    bad = []
    for tpl in sorted(TABS_DIR.glob("*.html")):
        text = tpl.read_text(encoding="utf-8")
        if 'id="page-' not in text:
            bad.append(f"{tpl.name}: no <div class=\"page\" id=\"page-...\"> wrapper")
        if "tab-content" in text:
            bad.append(f"{tpl.name}: uses class=\"tab-content\", which nothing hides")
    assert not bad, (
        "Tab templates that the switcher cannot hide (they will render on top of "
        "every other tab):\n" + "\n".join(f"  {b}" for b in bad)
    )


def test_guard_template_is_the_guard_page() -> None:
    text = (TABS_DIR / "guard.html").read_text(encoding="utf-8")
    first_div = re.search(r"<div[^>]*>", text)
    assert first_div is not None
    tag = first_div.group(0)
    assert 'class="page"' in tag and 'id="page-guard"' in tag, tag


def test_guard_nav_is_node_wide() -> None:
    """Guard ranks sessions from every runtime, so its nav item must survive
    the per-runtime tab filter (`_cmApplyRuntimeTabVisibility`)."""
    js = APP_JS.read_text(encoding="utf-8")
    m = re.search(r"^var _CM_NODE_TABS = \[(.*?)\];", js, re.MULTILINE)
    assert m, "_CM_NODE_TABS not found in app.js"
    node_tabs = re.findall(r"'([^']+)'", m.group(1))
    assert "guard" in node_tabs, node_tabs
    m2 = re.search(r"^var _CM_RT_ALL_TABS = \[(.*?)\];", js, re.MULTILINE | re.DOTALL)
    assert m2 and "'guard'" in m2.group(1), "guard must stay in _CM_RT_ALL_TABS so it re-shows on runtime switch"


def test_tab_css_scopes_target_an_id_that_exists() -> None:
    """A stylesheet block scoped to `#<stem> ...` is dead the moment the
    template's wrapper is renamed to `id="page-<stem>"`. Guard's 38 rules were
    scoped to `#guard` while the panel became `#page-guard`, leaving every
    button and pill unstyled."""
    css = (ROOT / "clawmetry" / "static" / "css" / "dashboard.css").read_text(encoding="utf-8")
    orphaned = []
    for tpl in sorted(TABS_DIR.glob("*.html")):
        stem = tpl.stem
        if not re.search(r"#" + re.escape(stem) + r"(?![-\w])", css):
            continue
        text = tpl.read_text(encoding="utf-8")
        if f'id="{stem}"' not in text:
            orphaned.append(f"{tpl.name}: dashboard.css scopes rules to #{stem} but no element has id=\"{stem}\"")
    assert not orphaned, "\n".join(orphaned)
