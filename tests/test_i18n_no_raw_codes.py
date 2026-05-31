"""Guard against raw codes/keys leaking into the rendered UI.

Two bug classes that shipped to live prod (2026-05-31, user-reported with
screenshots) and that this pins so they cannot recur:

1. **HTML-entity emoji/arrows render literally.** Labels written as
   ``&#x1F50D;`` / ``&rarr;`` decode fine inside plain HTML, but the Flow
   diagram (SVG ``<text>``) and the i18n applier (``textContent = locale
   value``) do NOT decode them — so users saw ``&#x1F50D; Search`` and
   ``prompt &rarr; model call``. Real Unicode (🔍 / →) renders in every
   context, so emoji/arrow entities are banned from tab templates AND locale
   JSON values.

2. **Missing i18n keys leak the raw key.** A ``data-i18n="overview.run_health_title"``
   whose key is absent from ``en.json`` rendered ``OVERVIEW.RUN_HEALTH_TITLE``
   on screen. Every ``data-i18n*`` key used in a template must exist in
   ``en.json`` (the i18n applier also now falls back to the element's English
   markup text, but the catalog must still carry the key).

These are static checks over the shipped assets — fast, deterministic, no
server needed.
"""

from __future__ import annotations

import glob
import json
import os
import re

import pytest

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_TEMPLATES = glob.glob(os.path.join(_ROOT, "clawmetry", "templates", "**", "*.html"),
                       recursive=True)
_LOCALES = [p for p in glob.glob(os.path.join(_ROOT, "clawmetry", "static", "locales", "*.json"))
            # _meta.json (language list) + _glossary.json are metadata arrays, not
            # rendered translation catalogs — exclude from the value check.
            if not os.path.basename(p).startswith("_")]

# Emoji (hex), decimal symbols >= U+2000, and named arrows that DON'T decode in
# SVG <text> / textContent contexts. Structural entities (&amp; &lt; &gt;
# &nbsp; &#39; &quot;) are intentionally NOT matched — those are legitimate.
_EMOJI_ENTITY = re.compile(
    r"&#x[0-9A-Fa-f]+;|&rarr;|&larr;|&uarr;|&darr;|&hellip;|&mdash;|&ndash;"
    r"|&times;|&middot;")
_HIGH_DECIMAL = re.compile(r"&#(\d+);")


def _emoji_entities(text: str) -> list[str]:
    hits = _EMOJI_ENTITY.findall(text)
    hits += [m.group(0) for m in _HIGH_DECIMAL.finditer(text)
             if int(m.group(1)) >= 8192]  # >=U+2000 = symbols/emoji, not ASCII
    return hits


@pytest.mark.parametrize("path", _TEMPLATES, ids=[os.path.basename(p) for p in _TEMPLATES])
def test_no_emoji_entities_in_templates(path):
    """Templates must use real Unicode for emoji/arrows — entities render
    literally in the Flow SVG and the i18n textContent path."""
    hits = _emoji_entities(open(path, encoding="utf-8").read())
    assert not hits, (
        f"{os.path.basename(path)} contains emoji/arrow HTML entities that "
        f"render literally in SVG/textContent contexts — use real Unicode "
        f"(🔍 not &#x1F50D;, → not &rarr;): {sorted(set(hits))[:10]}"
    )


@pytest.mark.parametrize("path", _LOCALES, ids=[os.path.basename(p) for p in _LOCALES])
def test_no_emoji_entities_in_locale_values(path):
    """Locale JSON values are applied via textContent (no HTML decoding), so an
    entity-laden value shows literally. Ban them across every locale."""
    data = json.load(open(path, encoding="utf-8"))
    offenders = {k: v for k, v in data.items()
                 if isinstance(v, str) and _emoji_entities(v)}
    assert not offenders, (
        f"{os.path.basename(path)} has {len(offenders)} value(s) with emoji/arrow "
        f"entities that render literally; use real Unicode. e.g. "
        f"{dict(list(offenders.items())[:3])}"
    )


def test_every_template_i18n_key_exists_in_en():
    """A data-i18n key missing from en.json renders the RAW KEY on screen
    (e.g. OVERVIEW.RUN_HEALTH_TITLE). Every template key must be catalogued."""
    en = set(json.load(open(
        os.path.join(_ROOT, "clawmetry", "static", "locales", "en.json"),
        encoding="utf-8")).keys())
    used: dict[str, str] = {}
    pat = re.compile(r'data-i18n(?:-title|-placeholder|-aria-label)?="([^"]+)"')
    for f in _TEMPLATES:
        for m in pat.finditer(open(f, encoding="utf-8").read()):
            used.setdefault(m.group(1), os.path.basename(f))
    missing = {k: v for k, v in used.items() if k not in en}
    assert not missing, (
        f"{len(missing)} data-i18n key(s) used in templates are absent from "
        f"en.json and would render the raw key on screen: {missing}"
    )
