"""The topbar carries an always-visible refresh/reconnect control.

The desktop shell has no browser chrome: no address bar, no reload button,
and pywebview's Cocoa backend swallows Cmd-R and strips the context menu. On
2026-08-17 that left a user staring at a frozen dashboard for 6h39m whose
only escape was quitting the app. The control has to be in the page itself.

Two things are easy to get wrong and are pinned here:

1. `dashboard.py` defines DASHBOARD_HTML TWICE and the SECOND one wins (see
   CLAUDE.md). Markup added to the first block renders for nobody. This test
   asserts the button lands in the live block.
2. The button must not be a bare `location.reload()`. Against a dead port a
   reload swaps the frozen-but-readable dashboard for a blank WebKit error
   page with no buttons on it -- strictly worse. It routes through
   `cmReconnect()`, which probes first and heals before reloading.
"""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DASHBOARD = REPO_ROOT / "dashboard.py"
STATIC = REPO_ROOT / "clawmetry" / "static"

BTN_ID = 'id="cm-reconnect-btn"'


def _live_dashboard_html() -> str:
    """The SECOND DASHBOARD_HTML block -- the one actually served."""
    src = DASHBOARD.read_text()
    starts = [m.start() for m in re.finditer(r'^DASHBOARD_HTML = r"""', src, re.M)]
    assert len(starts) == 2, (
        f"expected exactly 2 DASHBOARD_HTML definitions, found {len(starts)}. "
        "If this changed, re-check which block is live before trusting this test."
    )
    return src[starts[1]:]


def test_refresh_button_is_in_the_live_html_block():
    assert BTN_ID in _live_dashboard_html(), (
        "the refresh button is missing from the live (second) DASHBOARD_HTML "
        "block -- if it was added to the first block it renders for nobody"
    )


def test_refresh_button_appears_exactly_once():
    assert DASHBOARD.read_text().count(BTN_ID) == 1


def test_refresh_button_routes_through_cmReconnect_not_a_bare_reload():
    live = _live_dashboard_html()
    at = live.index(BTN_ID)
    tag = live[at - 400:at + 400]
    assert "cmReconnect" in tag, "refresh button does not call cmReconnect()"
    assert "location.reload" not in tag, (
        "refresh button reloads directly; against a dead backend that leaves "
        "the user on a blank error page with no way back"
    )


def test_recovery_helpers_are_exported_from_auth_bootstrap():
    js = (STATIC / "js" / "auth-bootstrap.js").read_text()
    for needle in (
        "window.cmReconnect=",
        "window.cmShowBackendOutage=",
        "window.cmHideBackendOutage=",
        "window.cmBackendProbe=",
        "window.__cmOrigFetch=",
    ):
        assert needle in js, f"auth-bootstrap.js missing: {needle}"


def test_probe_uses_the_unwrapped_fetch():
    """A health probe that fails must not count toward the outage threshold
    that raised the overlay in the first place."""
    js = (STATIC / "js" / "auth-bootstrap.js").read_text()
    assert "window.__cmOrigFetch||window.fetch" in js


def test_button_has_a_busy_and_an_attention_style():
    css = (STATIC / "css" / "dashboard.css").read_text()
    assert "#cm-reconnect-btn.cm-attention" in css
    assert "#cm-reconnect-btn.cm-spinning" in css


def test_tooltip_key_is_translatable():
    import json
    en = json.loads((STATIC / "locales" / "en.json").read_text())
    assert "topbar.refresh" in en, "topbar.refresh missing from the en locale"
