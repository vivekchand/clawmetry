"""Guards for the expired-license / expired-trial banner (founder ask
2026-08-02: "localhost should show pay button to get pro licence key
beyond the trial period").

Before this, the only post-expiry surfaces were (a) the paywall modal,
whose CTA is "Start 7-day free trial" — a dead end for someone whose
trial already ended (one per account), and (b) the selfhost modal's
'ended' step, which only fires during a RE-signup attempt. A running
dashboard whose trial lapsed had no honest "buy a license" path.
"""

from __future__ import annotations

import json
import os


def _repo_root():
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _read(relpath):
    with open(os.path.join(_repo_root(), relpath), "r", encoding="utf-8") as fh:
        return fh.read()


def test_banner_markup_exists_with_buy_and_paste_paths():
    html = _read("clawmetry/templates/partials/banners.html")
    assert 'id="license-expired-banner"' in html
    # The buy CTA must exist and target self-host pricing with attribution.
    assert "clawmetry.com/pricing?deploy=self&source=expired-banner" in html
    # The already-bought path must exist (license paste via the selfhost modal).
    assert 'id="license-expired-have-key"' in html
    assert "shmShowLicense" in html


def test_banner_copy_avoids_em_and_double_dashes():
    html = _read("clawmetry/templates/partials/banners.html")
    start = html.find('id="license-expired-banner"')
    assert start != -1
    block = html[start:html.find("<!-- Onboarding", start)]
    assert "—" not in block and " -- " not in block


def test_js_gates_on_expired_entitlement_only():
    js = _read("clawmetry/static/js/app.js")
    anchor = js.find("async function checkLicenseExpiry")
    assert anchor != -1, "checkLicenseExpiry must exist in app.js"
    block = js[anchor:anchor + 3000]
    assert "/api/entitlement" in block
    assert "e.expired" in block, (
        "the banner must key off the entitlement's expired flag — an "
        "ACTIVE trial or license must never see it"
    )
    assert "e.tier === 'trial'" in block
    # No poller: one fetch on load (perf budget).
    assert "setInterval" not in block, (
        "no poller for the expiry banner — expiry changes once a week, "
        "one on-load check is enough (CPU/request budget)"
    )
    # Dismiss must be time-bound, not permanent (the user still needs the
    # nudge next session).
    assert "24 * 3600 * 1000" in block


def test_js_never_keys_countdown_on_grace_flag():
    """``grace`` on /api/entitlement is the GLOBAL paywall-rollout flag
    (``not is_enforced()`` — true on every install until enforcement goes
    live), not a per-trial expiry signal. Keying the countdown on it made
    a freshly-activated 7-day trial read "Your trial ends today"
    (2026-08-10 lab repro: license valid 6 more days, banner said ends
    today next to the license email saying Aug 17)."""
    js = _read("clawmetry/static/js/app.js")
    anchor = js.find("async function checkLicenseExpiry")
    assert anchor != -1
    block = js[anchor:anchor + 3000]
    assert "e.grace ===" not in block and "e.grace)" not in block, (
        "the trial-countdown banner must never gate on the grace flag — "
        "use days_until_expiry / expired only"
    )


def test_locale_keys_present_in_en():
    en = json.loads(_read("clawmetry/static/locales/en.json"))
    for key in ("banners.trial_expired_msg", "banners.license_expired_msg",
                "banners.get_license", "banners.have_license_key"):
        assert key in en, key + " missing from en.json"
    assert "trial has ended" in en["banners.trial_expired_msg"]
