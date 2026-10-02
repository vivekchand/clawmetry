"""Guards for the Agents-roster consistency + fold fixes (founder report
2026-07-30, supersedes the #3482 "promote the selected runtime" approach).

The roster is node-wide by design (it carries the blue "this view is
node-wide" banner). The old behaviour promoted the selected runtime out of the
"Show N inactive" fold and re-sorted it to row 0, so the visible row set AND
the fold count changed on every switcher change - exactly what the banner
promised would not happen. New contract:

  1. the active/inactive partition depends ONLY on activity (running or 24h
     cost/tokens), never on the runtime switcher;
  2. no switcher-dependent re-sort - identical order across runtime changes;
  3. the selected runtime is highlighted in place (inv-row-active), not moved;
  4. the fold toggle actually works: the toggle <tr> lives in an explicit
     <tbody> (a bare <tr> as a direct <table> child gets wrapped in an
     implicit anonymous tbody by the HTML parser, which broke the handler's
     sibling lookup and made the fold permanently un-openable), and the
     handler resolves the fold body from the enclosing <table>;
  5. the fold toggle LOOKS clickable (cursor:pointer CSS exists).
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
_APP_JS = os.path.join(_HERE, "..", "clawmetry", "static", "js", "app.js")
_CSS = os.path.join(_HERE, "..", "clawmetry", "static", "css", "dashboard.css")
_EN_JSON = os.path.join(_HERE, "..", "clawmetry", "static", "locales", "en.json")


def _read(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def _fn(js, name):
    start = js.find("function " + name)
    assert start != -1, name + " missing"
    nxt = js.find("\nfunction ", start + 1)
    a = js.find("\nasync function ", start + 1)
    ends = [x for x in (nxt, a) if x != -1]
    return js[start:min(ends) if ends else start + 20000]


def test_partition_is_switcher_independent():
    body = _fn(_read(_APP_JS), "_invIsRecentlyActive")
    assert "rtFilter" not in body and "agentKey ===" not in body, (
        "_invIsRecentlyActive must not consult the runtime switcher - the "
        "selected-runtime promotion made the node-wide roster's row set shift "
        "on every switcher change"
    )


def test_no_switcher_dependent_resort():
    body = _fn(_read(_APP_JS), "_invRenderRoster")
    assert "active.sort" not in body, (
        "the active list must not be re-sorted by the selected runtime - "
        "order must be identical across switcher changes"
    )


def test_selected_row_still_highlighted():
    body = _fn(_read(_APP_JS), "_invRosterRow")
    assert "inv-row-active" in body, (
        "the selected runtime's row must still be highlighted in place"
    )


def test_fold_toggle_row_in_explicit_tbody():
    body = _fn(_read(_APP_JS), "_invRenderRoster")
    assert '<tbody class="inv-fold-head"><tr class="inv-fold-toggle"' in body, (
        "the fold toggle <tr> must live in its own explicit <tbody> - as a "
        "bare <table> child the HTML parser wraps it in an anonymous tbody "
        "and the toggle handler cannot find .inv-fold-body"
    )


def test_fold_handler_resolves_body_via_table():
    body = _fn(_read(_APP_JS), "_invToggleInactive")
    assert "closest" in body and ".inv-fold-body" in body, (
        "_invToggleInactive must resolve the fold body from the enclosing "
        "<table> (parentNode/nextElementSibling lookups miss the sibling "
        "tbody and silently no-op)"
    )


def test_fold_toggle_looks_clickable():
    css = _read(_CSS)
    assert ".inv-fold-toggle" in css and "cursor: pointer" in css.split(
        ".inv-fold-toggle", 1)[1][:200], (
        "the fold toggle row needs cursor:pointer CSS - without it the row "
        "reads as inert text"
    )


def test_coverage_chip_markup_and_i18n():
    body = _fn(_read(_APP_JS), "_invRosterRow")
    assert "inv-cov-sub" in body and "inv-cov-met" in body, (
        "roster rows must carry the device-parity covered/metered chip"
    )
    en = json.load(open(_EN_JSON, encoding="utf-8"))
    assert en.get("inventory.covered_chip") == "subscription"
    assert en.get("inventory.metered_chip") == "metered"


@pytest.mark.parametrize("plan,extra", [
    ({"mode": "subscription", "label": "Claude Max 20x"}, 0),
    ({"mode": "subscription", "label": "Claude Max 20x"}, 12.5),
    (None, None),
])
def test_today_tile_estimates_usage_without_inventing_a_subscription_invoice(plan, extra):
    node = shutil.which("node")
    if not node:
        pytest.skip("Node.js is not installed")
    js = _read(_APP_JS)
    start = js.index("  setSub('inv-tile-agents-sub',")
    start = js.index("\n", start) + 1
    end = js.index("  var health = _invHealth(agents);", start)
    code = "\n".join([
        "var inv = " + json.dumps({"accountPlan": plan, "extraCost24hUsd": extra}) + ";",
        "var totalCost24h = 1121.38; var shown = {};",
        "var subtitle = {textContent: '', style: {}};",
        "var document = {getElementById: () => subtitle};",
        "function setTxt(id, value) { shown[id] = value; }",
        "function _invFmtUsd(n) { return '$' + Number(n).toFixed(2); }",
        js[start:end],
        "console.log(JSON.stringify({value: shown['inv-tile-today'], sub: subtitle.textContent}));",
    ])
    out = subprocess.run([node, "-e", code], capture_output=True, text=True, timeout=20)
    assert out.returncode == 0, out.stderr
    got = json.loads(out.stdout)
    assert got["value"] == "$1121.38"
    assert "API-equivalent estimate" in got["sub"]
    assert "provider account" in got["sub"]
    assert "covers it" not in got["sub"]
    assert "extra" not in got["value"]


def test_subscription_row_does_not_promise_unobserved_billing_coverage():
    body = _fn(_read(_APP_JS), "_invRosterRow")
    assert "sign-in detected" in body
    assert "check your provider account" in body
    assert "not an extra bill" not in body
