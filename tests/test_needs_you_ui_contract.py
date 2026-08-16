"""The needs-you strip's UI contract.

The four-state honesty rule lives in JavaScript, which the Python suite cannot
execute — but the two ways it actually breaks are both checkable here:

  1. A locale key is renamed or dropped, and the strip renders a raw key or an
     English fallback that no longer matches the catalogue.
  2. Someone simplifies the renderer down to waiting/not-waiting, quietly
     deleting the "can't tell" and "never asks" branches. That is the exact
     regression the whole design exists to prevent: an empty list from a
     detector that is not running must never render as all-clear.

These are grep-level guards on purpose. They are cheap, they run in the
existing CI with no browser, and they fail loudly on the changes most likely
to be made by someone who has not read the design.
"""

from __future__ import annotations

import json
import pathlib

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
APP_JS = ROOT / "clawmetry" / "static" / "js" / "app.js"
CSS = ROOT / "clawmetry" / "static" / "css" / "dashboard.css"
OVERVIEW = ROOT / "clawmetry" / "templates" / "tabs" / "overview.html"
EN = ROOT / "clawmetry" / "static" / "locales" / "en.json"

#: Every key the renderer asks for. Keep in step with app.js.
REQUIRED_KEYS = [
    "needs.clear_title", "needs.one_working", "needs.n_working",
    "needs.none_running", "needs.one_waiting", "needs.n_waiting",
    "needs.confident", "needs.inferred", "needs.inferred_note",
    "needs.unknown_title", "needs.unknown_sub", "needs.cloud_sub",
    "needs.never_asks", "needs.more",
    "needs.badge_waiting", "needs.badge_maybe",
]


@pytest.fixture(scope="module")
def app_js() -> str:
    return APP_JS.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def catalogue() -> dict:
    return json.loads(EN.read_text(encoding="utf-8"))


# ── locale ──────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("key", REQUIRED_KEYS)
def test_locale_key_exists(catalogue, key):
    assert key in catalogue, f"{key} is requested by app.js but missing from en.json"
    assert catalogue[key].strip(), f"{key} is empty"


def test_every_needs_key_in_the_renderer_is_catalogued(app_js, catalogue):
    """Catches a key added to app.js and forgotten in en.json."""
    import re
    used = set(re.findall(r"t\('(needs\.[a-z_]+)'", app_js))
    missing = sorted(used - set(catalogue))
    assert not missing, f"used in app.js, absent from en.json: {missing}"


def test_placeholders_match_their_arguments(catalogue):
    """A `{n}` in the catalogue with no `n` passed renders a literal brace."""
    for key in ("needs.n_working", "needs.n_waiting", "needs.more"):
        assert "{n}" in catalogue[key], f"{key} should interpolate {{n}}"
    assert "{runtime}" in catalogue["needs.never_asks"]


def test_the_four_states_read_differently(catalogue):
    """If two states share wording the distinction is invisible, which is the
    same as not having it."""
    states = {
        "clear":  catalogue["needs.clear_title"],
        "waiting": catalogue["needs.one_waiting"],
        "unknown": catalogue["needs.unknown_title"],
        "never":   catalogue["needs.never_asks"],
    }
    assert len(set(states.values())) == 4, f"states share wording: {states}"


def test_unknown_state_does_not_claim_all_clear(catalogue):
    """'Can't tell' must not be worded as reassurance."""
    unknown = (catalogue["needs.unknown_title"] + " "
               + catalogue["needs.unknown_sub"]).lower()
    for forbidden in ("nothing needs you", "all clear", "no agents need"):
        assert forbidden not in unknown, (
            f"the unknown state says {forbidden!r} — that is a confident "
            "claim we cannot support")


def test_inferred_wording_hedges_and_confirmed_does_not(catalogue):
    """The three words the feature's credibility rests on."""
    assert catalogue["needs.confident"].lower() == "waiting for you"
    hedged = catalogue["needs.inferred"].lower()
    assert any(w in hedged for w in ("looks like", "maybe", "might", "seems")), (
        "the inferred label must read as a guess")
    assert catalogue["needs.badge_maybe"].lower() != \
        catalogue["needs.badge_waiting"].lower()


# ── renderer branches ───────────────────────────────────────────────────────

def test_renderer_keeps_the_unknown_branch(app_js):
    """The branch that makes an all-clear trustworthy."""
    assert "d.fresh === false" in app_js, (
        "the freshness branch is gone — an empty list from a stopped daemon "
        "would now render as 'nothing needs you'")


def test_renderer_keeps_the_never_asks_branch(app_js):
    assert "runtimes_without_approval" in app_js


def test_confidence_is_decided_in_one_place(app_js):
    """A second inline signal comparison is how a source ends up rendering as
    certain on one surface and hedged on another.

    Exactly one comparison is allowed: the one inside _cmAttnConfirmed that
    defines the rule. Any other is a callsite that will not learn about the
    next signal we add.
    """
    assert "function _cmAttnConfirmed" in app_js
    comparisons = [ln for ln in app_js.splitlines()
                   if "signal === 'hook'" in ln or 'signal === "hook"' in ln]
    assert len(comparisons) == 1, (
        f"expected only the _cmAttnConfirmed definition, found "
        f"{len(comparisons)}: {comparisons}")
    # ...and that one must be the definition, not a callsite that happens to
    # be alone today.
    idx = app_js.index(comparisons[0])
    helper_at = app_js.index("function _cmAttnConfirmed")
    assert 0 <= idx - helper_at < 300, (
        "the surviving comparison is not inside _cmAttnConfirmed; route it "
        "through the helper so 'queue' is not silently treated as a guess")


def test_queue_counts_as_confirmed(app_js):
    assert "signal === 'queue'" in app_js, (
        "_cmAttnConfirmed no longer recognises 'queue' — approval-derived "
        "rows would render as guesses")


# ── wiring ──────────────────────────────────────────────────────────────────

def test_strip_is_in_the_live_template(app_js):
    """dashboard.py defines DASHBOARD_HTML twice and only the second renders.
    The strip must live in the template that is actually included."""
    assert 'id="needs-you"' in OVERVIEW.read_text(encoding="utf-8")
    assert "loadNeedsYou" in app_js


def test_strip_styles_exist(app_js):
    css = CSS.read_text(encoding="utf-8")
    for cls in (".cm-needs", ".cm-needs-dot", ".cm-attn-badge"):
        assert cls in css, f"{cls} missing from dashboard.css"


def test_confidence_is_not_carried_by_colour_alone():
    """The dot's SHAPE distinguishes confirmed from inferred, so the
    distinction survives for a colour-blind reader."""
    css = CSS.read_text(encoding="utf-8")
    assert ".cm-needs-dot.is-hook" in css
    assert ".cm-needs-dot.is-inferred" in css
    # is-inferred is a half fill, not merely a different hue.
    block = css.split(".cm-needs-dot.is-inferred")[1][:200]
    assert "gradient" in block, (
        "the inferred dot no longer differs in shape — confidence would be "
        "carried by colour alone")
