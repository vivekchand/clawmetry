"""Wiring guards for the header trial pill + in-app upgrade modal.

``clawmetry/static/js/trial-pill.js`` renders the "Pro trial · N days
remaining" pill and the green Upgrade button, and owns the Starter/Pro x
Monthly/Annual chooser that takes a trialing customer to Stripe without
leaving the dashboard.

The component's own behaviour is covered by ``tests/test_trial_pill.js``
(run below via Node). What this file guards is the WIRING around it, every
piece of which fails silently:

  * the ``<script>`` tag and the ``#cm-trial-pill-slot`` div -- drop either
    and the pill simply never appears. No error, no console warning; the
    trial just expires quietly, which is the exact failure this feature
    exists to prevent.
  * the i18n keys -- ``t()`` falls back to the English literal when a key is
    missing, so a typo ships as "works fine in English, untranslated
    everywhere else" and no test would notice.
  * the price ladder -- the component must read ``window.CM_PLANS`` and
    never declare its own. A second hardcoded ladder is how a reprice ships
    half-done (it has happened: the in-app CTA sat on the pre-reprice Pro
    price for three days after /pricing had moved).
  * the profile menu -- its "Upgrade plan" item must reach the same modal,
    or we have two upgrade paths that drift.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
PILL_JS = REPO_ROOT / "clawmetry" / "static" / "js" / "trial-pill.js"
APP_JS = REPO_ROOT / "clawmetry" / "static" / "js" / "app.js"
GW_JS = REPO_ROOT / "clawmetry" / "static" / "js" / "gw-setup.js"
LOCALE = REPO_ROOT / "clawmetry" / "static" / "locales" / "en.json"
DASHBOARD = REPO_ROOT / "dashboard.py"
JS_TEST = Path(__file__).resolve().parent / "test_trial_pill.js"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


# ── the component ships and is wired into the page ──────────────────────────

def test_pill_module_exists() -> None:
    assert PILL_JS.is_file(), f"{PILL_JS} is missing"
    assert PILL_JS.stat().st_size > 0


def test_dashboard_loads_the_pill_module() -> None:
    """Without the script tag the pill silently never renders."""
    html = _read(DASHBOARD)
    assert "js/trial-pill.js" in html, (
        "DASHBOARD_HTML no longer loads static/js/trial-pill.js -- the trial "
        "pill and the whole in-app upgrade path are dead with no error"
    )


def test_dashboard_renders_the_pill_slot() -> None:
    """The mount point must be server-rendered exactly once.

    trial-pill.js falls back to appending into .nav when the slot is absent,
    so a missing slot degrades quietly rather than failing -- which is why it
    needs a test rather than a smoke check.
    """
    html = _read(DASHBOARD)
    hits = html.count('id="cm-trial-pill-slot"')
    assert hits == 1, (
        f"expected exactly 1 #cm-trial-pill-slot in dashboard.py, found {hits}. "
        "Two slots means two pills (the nav has a legacy_nav branch and a "
        "sidebar branch -- the slot belongs OUTSIDE both)"
    )


def test_pill_slot_is_outside_the_nav_branches() -> None:
    """The slot sits after the ``{% endif %}`` that closes the legacy_nav /
    sidebar split, so both navs get it from one line of markup."""
    html = _read(DASHBOARD)
    at = html.index('id="cm-trial-pill-slot"')
    # Walk back to the nearest Jinja control token; it must be an endif, not
    # an if/else that would scope the slot to one branch.
    before = html[:at]
    tokens = re.findall(r"\{%\s*(if|else|endif)\b", before)
    assert tokens and tokens[-1] == "endif", (
        "the pill slot is inside a legacy_nav if/else branch, so one of the "
        f"two navs will not render it (nearest preceding token: {tokens[-1:]})"
    )


def test_app_js_broadcasts_trial_state() -> None:
    """The pill rides app.js's existing /api/trial/status poll. Drop the
    broadcast and the pill falls back to its own 5-minute poll -- it still
    works, but the countdown goes stale for up to five minutes after a
    license lands, which is exactly when the user is watching."""
    src = _read(APP_JS)
    assert "cm:trial-state" in src, (
        "app.js no longer dispatches cm:trial-state; the pill loses its "
        "shared poll"
    )


def test_profile_menu_opens_the_in_app_modal() -> None:
    """One upgrade surface, not two."""
    src = _read(GW_JS)
    assert "cmOpenUpgradeModal" in src, (
        "the profile menu's 'Upgrade plan' item no longer opens the in-app "
        "chooser -- it is back to bouncing the user to a pricing page with "
        "the account context dropped"
    )
    # The external pricing page must survive as the fallback for a cached
    # page where trial-pill.js did not load.
    assert "clawmetry.com/pricing" in src, (
        "the pricing-page fallback was removed; a cached page without "
        "trial-pill.js now has no upgrade path at all"
    )


# ── the pricing ladder is not duplicated ────────────────────────────────────

def test_pill_reads_the_shared_price_ladder() -> None:
    src = _read(PILL_JS)
    assert "window.CM_PLANS" in src, (
        "trial-pill.js must read the shared ladder published by app.js"
    )


def test_pill_declares_no_prices_of_its_own() -> None:
    """A reprice must be one edit. Any dollar figure or plan-amount literal
    in this file is a second ladder waiting to go stale."""
    src = _read(PILL_JS)
    # Strip comments -- the rationale prose legitimately mentions money.
    body = re.sub(r"//[^\n]*", "", src)
    body = re.sub(r"/\*.*?\*/", "", body, flags=re.S)
    # A literal price is "$" immediately followed by a digit, or a bare
    # month/year amount assignment.
    offenders = re.findall(r"\$\d[\d,.]*", body)
    assert not offenders, (
        "trial-pill.js contains hardcoded price literals "
        f"{sorted(set(offenders))}; prices must come from window.CM_PLANS so a "
        "reprice is a single edit (see FLYWHEEL 7c pricing consistency)"
    )
    assert not re.search(r"\b(month|year)\s*:\s*\d+", body), (
        "trial-pill.js declares its own month/year plan amounts; use "
        "window.CM_PLANS"
    )


# ── i18n keys resolve ───────────────────────────────────────────────────────

def _keys_used() -> set:
    """Every tr('key', ...) literal in the component."""
    src = _read(PILL_JS)
    return set(re.findall(r"tr\(\s*'([^']+)'", src))


def test_uses_some_i18n_keys() -> None:
    """Guards the guard: if the tr() call shape changes, the extraction below
    would find nothing and the key test would pass vacuously."""
    used = _keys_used()
    assert len(used) >= 20, (
        f"only found {len(used)} tr() keys in trial-pill.js; the extraction "
        "regex has probably drifted from the call shape"
    )


def test_every_i18n_key_exists() -> None:
    catalog = json.loads(_read(LOCALE))
    missing = sorted(k for k in _keys_used() if k not in catalog)
    assert not missing, (
        f"trial-pill.js uses i18n keys absent from en.json: {missing}. "
        "t() silently returns the English fallback, so this ships as "
        "'untranslated everywhere' with no error"
    )


def test_locale_placeholders_match_the_call_sites() -> None:
    """A {days} in the catalog with no days= passed at the call site renders
    the literal braces to the user."""
    catalog = json.loads(_read(LOCALE))
    src = _read(PILL_JS)
    for key in sorted(_keys_used()):
        value = catalog.get(key)
        if not isinstance(value, str):
            continue
        placeholders = set(re.findall(r"\{(\w+)\}", value))
        if not placeholders:
            continue
        # Find the call site and confirm it passes a vars object naming each.
        call = re.search(
            r"tr\(\s*'" + re.escape(key) + r"'\s*,\s*(\{[^}]*\}|null)", src)
        assert call, f"could not locate the tr() call for {key}"
        passed = set(re.findall(r"(\w+)\s*:", call.group(1)))
        assert placeholders <= passed, (
            f"{key} renders {sorted(placeholders)} but the call site passes "
            f"{sorted(passed)}; the user would see literal braces"
        )


def test_pill_copy_says_remaining_not_a_bare_number() -> None:
    """The pill must always read as a countdown with a unit."""
    catalog = json.loads(_read(LOCALE))
    for key in ("trial.pill_days", "trial.pill_one_day"):
        assert "remaining" in catalog[key], (
            f"{key} lost its unit wording: {catalog[key]!r}"
        )


# ── the component's own behaviour (Node) ────────────────────────────────────

@pytest.mark.skipif(
    shutil.which("node") is None,
    reason="node not on PATH; JS unit tests only run when Node is available",
)
def test_trial_pill_js_suite() -> None:
    proc = subprocess.run(
        ["node", str(JS_TEST)],
        capture_output=True,
        text=True,
        timeout=60,
        cwd=str(REPO_ROOT),
    )
    output = (proc.stdout or "") + (proc.stderr or "")
    assert proc.returncode == 0, "trial-pill JS tests failed:\n" + output
    assert "PASS" in output, "no PASS line in output:\n" + output
