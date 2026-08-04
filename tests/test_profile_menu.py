"""Header account menu (top-right avatar) — self-hosted sign-in parity.

Self-hosted installs sign in (trial/license) just like Cloud, so the local
dashboard header carries the same profile affordance app.clawmetry.com has:
identity + plan in a dropdown, billing/plan management links, and sign-out.

These tests pin the markup/JS/i18n contract:
1. DASHBOARD_HTML ships the #cm-profile-wrap trigger + menu container and
   tags <body> with .has-profile-menu (which supersedes the bare
   #logout-btn icon via dashboard.css — sign-out moved into the dropdown).
2. gw-setup.js ships the cmProfile* module wired to /api/license/status
   (the only identity a local-only node has: license sub/tier/days_left)
   and /api/cloud-cta/status (signed-out detection).
3. en.json carries every profile.* key the module references.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

STATIC = ROOT / "clawmetry" / "static"


def _dashboard_html():
    import dashboard

    return dashboard.DASHBOARD_HTML


def test_header_ships_profile_menu_markup():
    html = _dashboard_html()
    assert 'id="cm-profile-wrap"' in html
    assert 'id="cm-profile-btn"' in html
    assert 'id="cm-profile-menu"' in html
    # Trigger opens the JS module, not an inline handler soup.
    assert "cmProfileToggle(event)" in html


def test_profile_menu_renders_in_both_nav_variants():
    """The avatar sits after the legacy/sidebar {% endif %} so both header
    variants (legacy_nav=1 and the default sidebar IA) render it."""
    html = _dashboard_html()
    endif_positions = [m.start() for m in re.finditer(r"\{% endif %\}", html)]
    wrap_pos = html.index('id="cm-profile-wrap"')
    nav_close = html.index("{% include 'partials/banners.html' %}")
    assert any(p < wrap_pos for p in endif_positions)
    assert wrap_pos < nav_close, "profile wrap must live inside .nav"


def test_body_class_supersedes_bare_logout_icon():
    html = _dashboard_html()
    assert "has-profile-menu" in html
    css = (STATIC / "css" / "dashboard.css").read_text()
    assert "body.has-profile-menu #logout-btn" in css
    # Must out-rank auth-bootstrap.js's inline style flip.
    rule = css.split("body.has-profile-menu #logout-btn", 1)[1].split("}", 1)[0]
    assert "!important" in rule


def test_gw_setup_module_wiring():
    js = (STATIC / "js" / "gw-setup.js").read_text()
    for needle in (
        "function cmProfileToggle",
        "function cmProfileClose",
        "function cmProfileInit",
        "/api/license/status",
        "/api/cloud-cta/status",
        "clawmetryLogout()",
        "openCloudModal()",
        "app.clawmetry.com/settings",
    ):
        assert needle in js, f"gw-setup.js missing: {needle}"


def test_selfhosted_upgrade_goes_to_selfhosted_pricing():
    """A self-hosted trial's "Upgrade plan" must sell the self-hosted license
    (clawmetry.com/pricing?deploy=self preselects the buy modal), never the
    cloud-account funnel: app.clawmetry.com/upgrade either hits a login wall
    or silently starts a CLOUD trial for the wrong product."""
    js = (STATIC / "js" / "gw-setup.js").read_text()
    assert "clawmetry.com/pricing?deploy=self" in js
    assert "app.clawmetry.com/upgrade" not in js


def test_cloud_billing_link_gated_on_linked_account():
    """"Billing & plan" opens app.clawmetry.com/settings, so it may only
    render when the node is linked to a cloud account — a license-only
    install has no account there to manage."""
    js = (STATIC / "js" / "gw-setup.js").read_text()
    assert "accountLinked" in js
    settings_pos = js.index("app.clawmetry.com/settings")
    gate_pos = js.index("st.accountLinked")
    assert gate_pos < settings_pos, "settings link must sit behind the accountLinked gate"


def test_gateway_settings_entry_points_removed():
    """The gw-setup overlay is a first-run wizard, not a settings surface:
    no "Gateway settings" gear in the topbar, no profile-menu item, no
    orphaned i18n keys (founder call 2026-08-04)."""
    js = (STATIC / "js" / "gw-setup.js").read_text()
    assert "profile.gateway_settings" not in js
    html = _dashboard_html()
    assert 'title="Gateway settings"' not in html
    assert "topbar.gateway_settings" not in html
    catalog = json.loads((STATIC / "locales" / "en.json").read_text())
    assert "profile.gateway_settings" not in catalog
    assert "topbar.gateway_settings" not in catalog


def test_sign_out_sticks_and_offers_local_signin():
    """Explicit sign-out must survive the zero-click loopback auto-login
    (otherwise Sign out is a no-op on localhost), and the wall must offer
    the one-click local re-login instead."""
    js = (STATIC / "js" / "auth-bootstrap.js").read_text()
    for needle in (
        "cm-signed-out",
        "function clawmetryLocalSignin",
        "function offerLocalSignin",
        "login-local-btn",
    ):
        assert needle in js, f"auth-bootstrap.js missing: {needle}"
    overlay = (
        ROOT / "clawmetry" / "templates" / "partials" / "overlays.html"
    ).read_text()
    assert 'id="login-local-btn"' in overlay
    assert "clawmetryLocalSignin()" in overlay
    catalog = json.loads((STATIC / "locales" / "en.json").read_text())
    assert "login.local_signin" in catalog


def test_en_catalog_has_every_profile_key_the_module_uses():
    js = (STATIC / "js" / "gw-setup.js").read_text()
    used = set(re.findall(r"[t(\"']+(profile\.[a-z_]+)", js))
    assert used, "expected profile.* t() keys in gw-setup.js"
    catalog = json.loads((STATIC / "locales" / "en.json").read_text())
    missing = sorted(k for k in used if k not in catalog)
    assert not missing, f"en.json missing i18n keys: {missing}"
