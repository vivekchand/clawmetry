"""Guard for the runtime pixel-logo set on the LOCAL (OSS) dashboard.

The hosted dashboard (cloud PR #1642) decorates the runtime switcher, session
rows and brain chips with per-runtime pixel mascots keyed off the runtime id
from ``GET /api/runtimes``. This ships the same set to the OSS local dashboard:

  - clawmetry/static/runtime-logos/sprite.svg  — atlas of <symbol id="rt-<id>">
    (+ rt-<id>-chip variants + rt-generic / rt-generic-chip fallback)
  - clawmetry/static/runtime-logos/manifest.json — {id: {label, brand}}
  - clawmetry/static/js/runtime-logos.js — window.cmRuntimeIcon / cmRuntimeBrand

This guard fails if the shipped sprite is missing a <symbol> for ANY runtime in
the entitlements runtime catalog, if the neutral fallback symbol is gone, or if
the helper wiring is dropped. Revert-proof: delete a <symbol> from sprite.svg,
or drop the rt-generic fallback, and the matching assertion goes red.
"""

from __future__ import annotations

import json
import os
import re

_HERE = os.path.dirname(os.path.abspath(__file__))
_STATIC = os.path.join(_HERE, "..", "clawmetry", "static")
_LOGO_DIR = os.path.join(_STATIC, "runtime-logos")
_SPRITE = os.path.join(_LOGO_DIR, "sprite.svg")
_MANIFEST = os.path.join(_LOGO_DIR, "manifest.json")
_HELPER = os.path.join(_STATIC, "js", "runtime-logos.js")
_APP_JS = os.path.join(_STATIC, "js", "app.js")


def _runtime_catalog_ids() -> set[str]:
    """The runtime ids the dashboard can show, sourced from the declared
    entitlements catalog (never a hardcoded copy of the 12-list)."""
    import sys

    sys.path.insert(0, os.path.join(_HERE, ".."))
    from clawmetry import entitlements  # noqa: E402

    return set(entitlements.RUNTIME_LABELS.keys())


def _sprite_symbol_ids() -> set[str]:
    with open(_SPRITE, encoding="utf-8") as fh:
        return set(re.findall(r'<symbol id="([^"]+)"', fh.read()))


def test_sprite_asset_ships() -> None:
    assert os.path.exists(_SPRITE), "sprite.svg must ship in clawmetry/static/runtime-logos/"
    assert os.path.exists(_MANIFEST), "manifest.json must ship alongside the sprite"
    assert os.path.exists(_HELPER), "runtime-logos.js helper must ship"


def test_every_runtime_has_a_symbol() -> None:
    """Every runtime in the entitlements catalog has a base + chip symbol."""
    syms = _sprite_symbol_ids()
    missing = []
    for rid in _runtime_catalog_ids():
        if f"rt-{rid}" not in syms:
            missing.append(f"rt-{rid}")
        if f"rt-{rid}-chip" not in syms:
            missing.append(f"rt-{rid}-chip")
    assert not missing, f"sprite.svg is missing symbol(s): {missing}"


def test_generic_fallback_symbols_present() -> None:
    """Unknown ids resolve to rt-generic; the symbol must exist in the atlas."""
    syms = _sprite_symbol_ids()
    assert "rt-generic" in syms, "rt-generic fallback symbol missing from sprite.svg"
    assert "rt-generic-chip" in syms, "rt-generic-chip fallback symbol missing from sprite.svg"


def test_manifest_covers_catalog() -> None:
    with open(_MANIFEST, encoding="utf-8") as fh:
        manifest = json.load(fh)
    missing = [r for r in _runtime_catalog_ids() if r not in manifest]
    assert not missing, f"manifest.json missing brand entry for: {missing}"
    for rid, meta in manifest.items():
        assert re.fullmatch(r"#[0-9a-fA-F]{6}", meta.get("brand", "")), f"{rid} brand not a hex"


def test_helper_defines_public_api() -> None:
    with open(_HELPER, encoding="utf-8") as fh:
        js = fh.read()
    for name in ("window.cmRuntimeIcon", "window.cmRuntimeBrand", "rt-generic"):
        assert name in js, f"runtime-logos.js must define/reference {name}"


def test_surfaces_wired_in_app_js() -> None:
    """The switcher, session rows and brain chips must call cmRuntimeIcon."""
    with open(_APP_JS, encoding="utf-8") as fh:
        app = fh.read()
    assert "cmRuntimeIcon" in app, "app.js never calls cmRuntimeIcon — no surface wired"
    assert 'data-cm-runtime=' in app, "session rows must tag the runtime via data-cm-runtime"


def test_helper_loaded_before_app_js() -> None:
    """runtime-logos.js must be included in the live dashboard HTML before app.js."""
    with open(os.path.join(_HERE, "..", "dashboard.py"), encoding="utf-8") as fh:
        dash = fh.read()
    assert "js/runtime-logos.js" in dash, "dashboard.py must load runtime-logos.js"
    rl = dash.index("js/runtime-logos.js")
    # The LIVE (second) DASHBOARD_HTML loads app.js after the helper.
    app_after = dash.find("js/app.js", rl)
    assert app_after > rl, "runtime-logos.js must be loaded before app.js"
