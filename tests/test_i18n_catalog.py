"""
i18n catalog + wiring guards (Phase 0).

Pure unit tests, no running server needed. These enforce the invariant that
makes the i18n initiative maintainable: English is the source of truth, and
every shipped locale file must carry exactly the English key set (no missing
keys -> no silent English-fallback gaps; no extra keys -> no orphans). The
automated translation bot (Phase 2) keeps locales in sync; this test fails CI
if a hand-edited locale drifts from en.json.

See docs/PRD_I18N.md.
"""
import json
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
LOCALES = REPO / "clawmetry" / "static" / "locales"


def _load(name):
    return json.loads((LOCALES / name).read_text(encoding="utf-8"))


def test_locales_dir_exists():
    assert LOCALES.is_dir(), f"missing locales dir: {LOCALES}"
    assert (LOCALES / "en.json").is_file(), "en.json (source of truth) must exist"
    assert (LOCALES / "_meta.json").is_file(), "_meta.json language registry must exist"


def test_meta_registry_shape():
    meta = _load("_meta.json")
    assert isinstance(meta, list) and meta, "_meta.json must be a non-empty list"
    codes = set()
    for entry in meta:
        for field in ("code", "endonym", "dir"):
            assert field in entry, f"meta entry missing {field!r}: {entry}"
        assert entry["dir"] in ("ltr", "rtl"), f"bad dir for {entry['code']}: {entry['dir']}"
        assert entry["code"] not in codes, f"duplicate locale code: {entry['code']}"
        codes.add(entry["code"])
    assert "en" in codes, "English must be registered"


def _shipped_locale_files():
    # every <code>.json that physically ships (en-XA is generated at runtime, no file).
    # underscore-prefixed files (_meta.json, _glossary.json) are config, not locales.
    return sorted(p for p in LOCALES.glob("*.json") if not p.name.startswith("_"))


def test_all_locale_files_are_valid_json():
    for p in _shipped_locale_files():
        json.loads(p.read_text(encoding="utf-8"))  # raises on malformed


@pytest.mark.parametrize("path", _shipped_locale_files(), ids=lambda p: p.stem)
def test_locale_key_parity_with_english(path):
    """Every shipped locale must have exactly the English key set."""
    en = _load("en.json")
    if path.name == "en.json":
        return
    loc = json.loads(path.read_text(encoding="utf-8"))
    en_keys, loc_keys = set(en), set(loc)
    missing = en_keys - loc_keys
    extra = loc_keys - en_keys
    assert not missing, f"{path.name} is missing keys: {sorted(missing)}"
    assert not extra, f"{path.name} has orphan keys not in en.json: {sorted(extra)}"
    empty = [k for k, v in loc.items() if not isinstance(v, str) or not v.strip()]
    assert not empty, f"{path.name} has empty/non-string values: {empty}"


def test_runtime_and_wiring_present():
    """Guard that the runtime ships and the dashboard loads it before app.js."""
    js = (REPO / "clawmetry" / "static" / "js" / "i18n.js").read_text(encoding="utf-8")
    assert "window.i18n" in js and "data-i18n" in js, "i18n.js runtime looks incomplete"

    html = (REPO / "dashboard.py").read_text(encoding="utf-8")
    assert "js/i18n.js" in html, "dashboard must load i18n.js"
    assert 'id="i18n-switcher"' in html, "top-right language switcher must be in the nav"
    # i18n.js must load before app.js so window.t exists when app.js runs
    assert html.index("js/i18n.js") < html.rindex("js/app.js"), "i18n.js must load before app.js"
