"""Guards for the "anatomy of an AI harness" explainer on the Harness tab.

The Harness tab teaches newcomers what a harness is (loop, tools, memory,
context, sandbox, guardrails, orchestration, interfaces) and links every part
to the live ClawMetry tab that shows it. These guards keep that promise:

- the anatomy section exists and covers all eight parts,
- every "watch it live" link targets a tab page that actually renders,
- the Harness nav entry is always visible (it no longer hides when no
  runtime-specific template is registered),
- copy obeys the no-em-dash rule for user-facing text.
"""
import json
import os
import re

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TAB = os.path.join(REPO, "clawmetry", "templates", "tabs", "harness.html")
TABS_DIR = os.path.join(REPO, "clawmetry", "templates", "tabs")
APP_JS = os.path.join(REPO, "clawmetry", "static", "js", "app.js")
DASHBOARD = os.path.join(REPO, "dashboard.py")
EN_JSON = os.path.join(REPO, "clawmetry", "static", "locales", "en.json")

ANATOMY_PARTS = [
    "The loop", "Tools", "Memory", "Context",
    "Sandbox", "Guardrails", "Teamwork", "Interfaces",
]


def _read(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def test_anatomy_section_covers_all_parts():
    html = _read(TAB)
    assert 'id="harness-anatomy"' in html
    for part in ANATOMY_PARTS:
        assert part in html, f"anatomy card missing: {part}"
    # the primer link that credits the source article
    assert "read.technically.dev/p/whats-harness-engineering" in html


def test_anatomy_links_target_real_tab_pages():
    html = _read(TAB)
    targets = re.findall(r"switchTab\('([a-z0-9-]+)'\)", html)
    assert len(set(targets)) >= 8, f"expected 8+ live-tab links, got {targets}"
    for tab in set(targets):
        page = os.path.join(TABS_DIR, f"{tab}.html")
        assert os.path.exists(page), f"anatomy links to switchTab('{tab}') but {tab}.html does not exist"
        assert f'id="page-{tab}"' in _read(page), f"{tab}.html lacks id=page-{tab}"


def test_harness_nav_always_visible():
    js = _read(APP_JS)
    m = re.search(r"function _cmRefreshHarnessNav\(\)\s*\{(.*?)\n\}", js, re.S)
    assert m, "app.js lost _cmRefreshHarnessNav"
    body = m.group(1)
    assert "'none'" not in body, "Harness nav must not hide again (anatomy applies to every runtime)"
    # the nav element itself must not ship pre-hidden either
    dash = _read(DASHBOARD)
    el = re.search(r'<div[^>]*id="left-nav-harness"[^>]*>', dash)
    assert el, "dashboard.py lost the left-nav-harness entry"
    assert "display:none" not in el.group(0), "left-nav-harness must render visible by default"


def test_nav_label_and_i18n_key():
    dash = _read(DASHBOARD)
    assert 'data-i18n="nav.harness"' in dash
    with open(EN_JSON, encoding="utf-8") as fh:
        en = json.load(fh)
    assert en.get("nav.harness") == "Harness"


def test_no_em_dashes_in_harness_copy():
    html = _read(TAB)
    assert "—" not in html, "em-dash found in user-facing Harness copy (banned)"
