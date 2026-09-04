"""The Signals tab's UI contract (WO-58, REQ-SIG-005).

Grep-level guards, in the style of ``test_needs_you_ui_contract.py``: cheap,
no browser, and they fail on exactly the edits most likely to be made by
someone who has not read the design.

  1. The wrapper is ``class="page" id="page-signals"``. The dashboard hides
     and shows ``.page`` panels keyed ``#page-<tab>``; any other wrapper draws
     the tab on top of every other tab (the 0.12.806 Guard regression).
  2. Every id-scoped CSS rule targets an id that exists in the template, so
     renaming the panel cannot silently orphan the styling.
  3. The tab is wired end to end: nav item, template include, switchTab
     dispatch, loader function, node-level tab list, blueprint registration.
  4. Every locale key the renderer asks for is catalogued, and the honest
     empty states read differently from each other (no daemon, nothing yet,
     not exposed by the runtime).
  5. No em dashes and no double-dash joins in any user-facing string.
"""
from __future__ import annotations

import json
import pathlib
import re

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
APP_JS = ROOT / "clawmetry" / "static" / "js" / "app.js"
ALERTS_JS = ROOT / "clawmetry" / "static" / "js" / "alerts.js"
CSS = ROOT / "clawmetry" / "static" / "css" / "dashboard.css"
TAB = ROOT / "clawmetry" / "templates" / "tabs" / "signals.html"
ALERTS_TAB = ROOT / "clawmetry" / "templates" / "tabs" / "alerts.html"
DASHBOARD = ROOT / "dashboard.py"
EN = ROOT / "clawmetry" / "static" / "locales" / "en.json"


@pytest.fixture(scope="module")
def tab() -> str:
    return TAB.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def app_js() -> str:
    return APP_JS.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def catalogue() -> dict:
    return json.loads(EN.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def signals_js(app_js) -> str:
    """The Signals section of app.js only, so copy checks do not sweep the
    rest of the bundle."""
    i = app_js.index("SIGNALS TAB (WO-58")
    return app_js[i:]


# ── wrapper ─────────────────────────────────────────────────────────────────

def test_wrapper_is_page_with_page_id(tab):
    assert re.search(r'<div class="page" id="page-signals">', tab), (
        "signals.html must open with class=\"page\" id=\"page-signals\"; "
        "the dashboard only toggles .page panels keyed #page-<stem>")
    assert 'class="tab-content"' not in tab


def test_css_is_scoped_to_the_existing_panel_id(tab):
    css = CSS.read_text(encoding="utf-8")
    scoped = re.findall(r"^#page-signals\b", css, re.MULTILINE)
    assert scoped, "expected #page-signals-scoped rules in dashboard.css"
    for ident in set(re.findall(r"^#(page-signals)", css, re.MULTILINE)):
        assert f'id="{ident}"' in tab, f"#{ident} CSS has no element to match"
    assert not re.search(r"^#signals\b", css, re.MULTILINE), (
        "a bare #signals rule would match nothing after the .page wrapper")


# ── wiring ──────────────────────────────────────────────────────────────────

def test_nav_include_and_blueprint_registered():
    src = DASHBOARD.read_text(encoding="utf-8")
    assert "{% include 'tabs/signals.html' %}" in src
    assert 'data-tab="signals" onclick="switchTab(\'signals\')"' in src
    assert "from routes.signals import bp_signals" in src
    assert "app.register_blueprint(bp_signals)" in src
    assert "app.register_blueprint(bp_guard)" in src


def test_switch_tab_dispatches_to_loader(app_js):
    assert "if (name === 'signals') { if (typeof loadSignalsTab === 'function') loadSignalsTab(); }" in app_js
    assert "function loadSignalsTab()" in app_js
    assert "'signals'" in app_js.split("var _CM_NODE_TABS = ", 1)[1].split("\n", 1)[0], (
        "signals must be a node-level tab or it vanishes whenever a runtime is selected")
    all_tabs = app_js.split("var _CM_RT_ALL_TABS = ", 1)[1].split("];", 1)[0]
    assert "'signals'" in all_tabs


def test_loader_respects_runtime_filter_and_polls_only_while_active(signals_js):
    assert "_cmRuntimeFilter()" in signals_js
    assert "'&runtime=' + encodeURIComponent(rt)" in signals_js
    assert "_sigIsActive()" in signals_js and "clearInterval(_sigState.timer)" in signals_js
    assert "visibilitySetInterval" in signals_js


def test_drilldown_reuses_the_transcript_opener(signals_js):
    assert "cmOpenFindingSession" in signals_js
    assert "switchTab('transcripts')" in signals_js


def test_template_has_the_three_surfaces(tab):
    for el in ("signals-headline", "signals-table-body", "signals-coverage-body",
               "signals-sessions-body", "signals-window-seg"):
        assert f'id="{el}"' in tab, el
    for w in ("1d", "7d", "30d"):
        assert f'data-window="{w}"' in tab


def test_alert_builder_offers_the_signal_rule():
    assert 'data-type="signal_rate_above"' in ALERTS_TAB.read_text(encoding="utf-8")
    js = ALERTS_JS.read_text(encoding="utf-8")
    assert "signal_rate_above" in js and "alerts-rule-signal" in js
    assert "body.signal = " in js


def test_canonical_tabs_and_screenshot_sweep_cover_signals():
    e2e = (ROOT / "tests" / "test_e2e_oss_all_tabs.py").read_text(encoding="utf-8")
    assert '"signals",' in e2e
    shots = (ROOT / ".github" / "workflows" / "pr-screenshots.yml").read_text(encoding="utf-8")
    assert ",signals," in shots


# ── locale ──────────────────────────────────────────────────────────────────

def test_every_signals_key_in_the_renderer_is_catalogued(signals_js, catalogue):
    used = set(re.findall(r"_sigT\('(signals\.[a-z_0-9]+)'", signals_js))
    assert used, "renderer requests no locale keys?"
    missing = sorted(used - set(catalogue))
    assert not missing, f"used in app.js, absent from en.json: {missing}"


def test_template_i18n_keys_are_catalogued(tab, catalogue):
    used = set(re.findall(r'data-i18n="([a-z_.0-9]+)"', tab))
    missing = sorted(used - set(catalogue))
    assert not missing, missing
    assert "nav.signals" in catalogue and "nav.signals_tooltip" in catalogue


def test_empty_states_read_differently(catalogue):
    states = {k: catalogue[k] for k in ("signals.no_daemon", "signals.nothing_yet",
                                        "signals.not_exposed_headline")}
    assert len(set(states.values())) == 3
    assert "0%" not in catalogue["signals.not_exposed"]
    assert "{runtime}" in catalogue["signals.not_exposed"]
    assert "not exposed" in catalogue["signals.cov_none"]


# ── copy ────────────────────────────────────────────────────────────────────

def _user_facing_strings(signals_js: str) -> list[str]:
    return re.findall(r"'([^'\\]*(?:\\.[^'\\]*)*)'", signals_js)


def test_no_em_dashes_in_user_facing_copy(tab, signals_js, catalogue):
    for name, text in (("signals.html", tab), ("app.js signals section", signals_js)):
        assert "—" not in text and "&mdash;" not in text, f"em dash in {name}"
        assert " -- " not in text, f"double dash in {name}"
    for k, v in catalogue.items():
        if k.startswith("signals.") or k in ("nav.signals", "nav.signals_tooltip", "alerts.type_signal"):
            assert "—" not in v and " -- " not in v, k
    from clawmetry import behaviour_signals as bs
    for meta in bs.SIGNALS.values():
        assert "—" not in meta["label"]
    h = bs.headline({"signals": {}, "window": "7d"})
    assert "—" not in h["text"] and " -- " not in h["text"]
