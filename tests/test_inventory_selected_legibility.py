"""Guards for the Agents-roster legibility fix (founder report 2026-07-02).

The roster is node-wide by design; the runtime switcher promotes the selected
runtime's row out of the "Show N inactive" fold (_invIsRecentlyActive counts
"is the selected runtime" as active). Two legibility bugs made that read as
"the tab shows different data on every dropdown change":

  1. the promoted row landed wherever roster order put it (OpenClaw above
     Claude Code, Hermes below) - unstable ordering;
  2. nothing explained WHY an idle runtime's row suddenly appeared.

Fix: the selected runtime is always the FIRST row, and a "selected" chip (with
a plain-words tooltip) marks a row that is only visible because it is selected.
"""

from __future__ import annotations

import json
import os
import re

_HERE = os.path.dirname(os.path.abspath(__file__))
_APP_JS = os.path.join(_HERE, "..", "clawmetry", "static", "js", "app.js")
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


def test_selected_runtime_pinned_first():
    body = _fn(_read(_APP_JS), "_invRenderRoster")
    assert "active.sort" in body and "agentKey === rtFilter" in body, (
        "the selected runtime's row must be pinned to the top of the active "
        "list - unstable ordering reads as the roster changing arbitrarily"
    )


def test_promoted_row_carries_selected_chip():
    body = _fn(_read(_APP_JS), "_invRosterRow")
    assert "inv-selected-chip" in body, "promoted row must carry the selected chip"
    # The chip only marks rows visible BECAUSE they are selected (idle otherwise).
    assert "_invIsRecentlyActive(a, 'all')" in body, (
        "the chip must check activity WITHOUT the selected-runtime promotion "
        "(rtFilter 'all'), so genuinely-active selected rows are not mislabeled"
    )


def test_promotion_rule_unchanged():
    """The deliberate promotion itself stays (a selected runtime must be
    visible), this fix only makes it legible."""
    body = _fn(_read(_APP_JS), "_invIsRecentlyActive")
    assert "a.agentKey === rtFilter" in body


def test_i18n_keys():
    en = json.load(open(_EN_JSON, encoding="utf-8"))
    assert en.get("inventory.selected_chip") == "selected"
    assert "inventory.selected_chip_tip" in en
