"""The free install's one announcement pill advertises Physical AI.

Static checks over the shipped template + locale catalog. No server, no data
store, so this runs in the plain unit leg.

What these pin, and why each one can actually fail:

1. The pill is reachable UI. ``partials/banners.html`` must be ``{% include %}``d
   by ``DASHBOARD_HTML``, or the pill is dead markup nobody renders.
2. It points at the Physical AI funnel, with the UTM triple the landing page
   already measures. On the previous revision this href was
   ``build.clawmetry.com`` (Agent Builder), so the assertion flips.
3. The visible English in the markup and the English in ``en.json`` are the same
   sentence. The i18n applier replaces ``textContent`` with the catalog value,
   so a drift between them silently changes the copy for every reader.
4. The retired ``banners.agent_builder_pill`` is gone from *every* locale.
   ``test_i18n_catalog`` fails hard on a locale key that ``en.json`` lacks, so a
   half-done rename is a red build, and this says which half.
5. The dismiss key written by the dismiss handler is the key the show-logic
   reads, and it is not the retired one. Reusing ``cm_ab_pill_dismissed`` would
   hide this different message from everyone who dismissed the old pill, which
   is the whole audience the change is for.
6. The README screenshot script dismisses the key the pill actually reads. That
   pairing lives in two files and rots silently: the screenshots would quietly
   grow a pill across every tab.
"""

from __future__ import annotations

import ast
import json
import os
import re

import pytest

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_BANNERS = os.path.join(_ROOT, "clawmetry", "templates", "partials", "banners.html")
_EN = os.path.join(_ROOT, "clawmetry", "static", "locales", "en.json")
_LOCALE_DIR = os.path.join(_ROOT, "clawmetry", "static", "locales")
_CAPTURE = os.path.join(_ROOT, "tests", "e2e", "capture-readme.mjs")

_I18N_KEY = "banners.physical_ai_pill"
_RETIRED_I18N_KEY = "banners.agent_builder_pill"
_RETIRED_DISMISS_KEY = "cm_ab_pill_dismissed"


def _read(path: str) -> str:
    with open(path, encoding="utf-8") as handle:
        return handle.read()


def _pill_block() -> str:
    """The pill's own markup, from its div to the close of its script."""
    source = _read(_BANNERS)
    start = source.index('<div id="cm-device-pill"')
    end = source.index("</script>", start)
    return source[start:end]


def test_banners_partial_is_included_by_the_dashboard():
    """A pill in a partial nothing includes is dead UI (FLYWHEEL 0a.4)."""
    dashboard = os.path.join(_ROOT, "dashboard.py")
    literals = [node.value for node in ast.parse(_read(dashboard)).body
                if isinstance(node, ast.Assign)
                and any(isinstance(t, ast.Name) and t.id == "DASHBOARD_HTML"
                        for t in node.targets)]
    assert len(literals) == 1, "DASHBOARD_HTML must be assigned exactly once"
    assert "{% include 'partials/banners.html' %}" in ast.literal_eval(literals[0]), (
        "DASHBOARD_HTML no longer includes partials/banners.html, so the "
        "announcement pill renders nowhere")


def test_exactly_one_announcement_pill():
    """'ONE announcement pill at a time' is the rule the markup states."""
    source = _read(_BANNERS)
    assert source.count('<div id="cm-device-pill"') == 1, (
        "more than one announcement pill in banners.html; they stack on screen")


def test_pill_links_to_the_physical_ai_funnel():
    block = _pill_block()
    hrefs = re.findall(r'<a\s[^>]*href="([^"]+)"', block)
    assert len(hrefs) == 1, f"expected a single link in the pill, found {hrefs}"
    href = hrefs[0].replace("&amp;", "&")
    assert href.startswith("https://clawmetry.com/physical-ai?"), (
        f"the pill must lead to the Physical AI page, not {href!r}")
    for param in ("utm_source=oss-dashboard", "utm_medium=pill",
                  "utm_campaign=physical-ai"):
        assert param in href, (
            f"{param!r} missing from the pill href; clawmetry.com/physical-ai "
            f"reports this campaign, so an untagged click is invisible: {href!r}")


def test_pill_does_not_still_advertise_agent_builder():
    assert "build.clawmetry.com" not in _pill_block(), (
        "the pill still points at Agent Builder")


def test_pill_copy_matches_the_english_catalog_exactly():
    """i18n replaces textContent, so markup and catalog must agree."""
    block = _pill_block()
    spans = re.findall(r'<span data-i18n="([^"]+)">([^<]+)</span>', block)
    assert len(spans) == 1, f"expected one translated span in the pill, found {spans}"
    key, markup_text = spans[0]
    assert key == _I18N_KEY, f"unexpected i18n key on the pill: {key!r}"
    catalog = json.loads(_read(_EN))
    assert key in catalog, f"{key} missing from en.json; the raw key renders on screen"
    assert catalog[key] == markup_text, (
        "the pill's English markup and en.json disagree, so the rendered copy "
        f"changes once i18n applies:\n  markup:  {markup_text!r}\n  en.json: "
        f"{catalog[key]!r}")


def test_pill_copy_has_no_banned_punctuation():
    """FLYWHEEL 2: no em-dash and no double-dash in user-facing copy."""
    copy = json.loads(_read(_EN))[_I18N_KEY]
    assert "—" not in copy, f"em-dash in pill copy: {copy!r}"
    assert "--" not in copy, f"double-dash in pill copy: {copy!r}"


@pytest.mark.parametrize("name", sorted(
    f for f in os.listdir(_LOCALE_DIR)
    if f.endswith(".json") and not f.startswith("_")))
def test_retired_key_is_gone_from_every_locale(name):
    """An orphan key (in a locale, absent from en.json) fails test_i18n_catalog."""
    catalog = json.loads(_read(os.path.join(_LOCALE_DIR, name)))
    assert _RETIRED_I18N_KEY not in catalog, (
        f"{name} still carries {_RETIRED_I18N_KEY}, which en.json no longer has")


def _dismiss_keys() -> tuple[str, str]:
    """(key the dismiss handler writes, key the show-logic reads)."""
    source = _read(_BANNERS)
    written = re.search(r"function dismissDevicePill\(\)\s*\{[^}]*"
                        r"localStorage\.setItem\('([^']+)'", source)
    read = re.search(r"if\(!localStorage\.getItem\('([^']+)'\)\)", source)
    assert written and read, "could not locate the pill's dismiss wiring"
    return written.group(1), read.group(1)


def test_dismiss_key_is_consistent_and_fresh():
    written, read = _dismiss_keys()
    assert written == read, (
        f"the pill writes {written!r} on dismiss but checks {read!r} on load, so "
        "dismissing it does not stick")
    assert written != _RETIRED_DISMISS_KEY, (
        "the pill reuses the Agent Builder dismiss key, so every reader who "
        "dismissed that pill never sees this different message")


def test_readme_screenshots_dismiss_the_key_the_pill_reads():
    _, read = _dismiss_keys()
    capture = _read(_CAPTURE)
    assert f"localStorage.setItem('{read}'" in capture, (
        f"tests/e2e/capture-readme.mjs does not pre-dismiss {read!r}, so the "
        "announcement pill appears in every README screenshot")
