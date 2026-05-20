"""
OSS all-tabs post-auth gate (E2E criterion C5).

Verifies that every canonical dashboard tab renders without an auth overlay
when the gateway token is correctly passed. Acceptance gate for:

  C5: Every OSS dashboard tab must screenshot post-login.
  (User-reported 2026-05-17: "gateway token not passed for OSS,
   it never displays other screens".)

Run against a booted dashboard:
    OPENCLAW_GATEWAY_TOKEN=ci-test-token python dashboard.py --port 8900 --no-debug &
    pytest tests/test_e2e_oss_all_tabs.py -v

Environment variables (mirrors tests/test_e2e.py):
    CLAWMETRY_URL   -- base URL of the running dashboard (default: http://localhost:8900)
    CLAWMETRY_TOKEN -- gateway token (default: ci-test-token)
"""

import json
import os
import urllib.request

import pytest

try:
    import playwright  # noqa: F401  -- used by _shared_chromium fixture

    _PLAYWRIGHT_AVAILABLE = True
except ImportError:
    _PLAYWRIGHT_AVAILABLE = False

BASE_URL = os.environ.get("CLAWMETRY_URL", "http://localhost:8900")
TOKEN = os.environ.get("CLAWMETRY_TOKEN", "ci-test-token")


# Per-test page off the session-shared Chromium (defined in conftest.py).
# sync_playwright() can only be entered once per process, so we reuse the
# shared browser rather than calling sync_playwright() here.
@pytest.fixture
def _overlay_page(_shared_chromium):
    ctx = _shared_chromium.new_context(viewport={"width": 1280, "height": 720})
    # Seed the gateway token into localStorage before any page script runs.
    # Mirrors the approach in .github/scripts/visual-diff.mjs.
    ctx.add_init_script(
        "try { "
        f"localStorage.setItem('clawmetry-token', {json.dumps(TOKEN)}); "
        f"localStorage.setItem('clawmetry-gw-token', {json.dumps(TOKEN)}); "
        "} catch(e) {}"
    )
    page = ctx.new_page()
    yield page
    ctx.close()

# Canonical tabs that must load without auth overlay post-login.
# Matches PR_SCREENSHOT_TABS in .github/workflows/pr-screenshots.yml
# so the Playwright gate covers the same surface as the visual-diff workflow.
CANONICAL_TABS = [
    "overview",
    "flow",
    "brain",
    "usage",
    "crons",
    "memory",
    "security",
    "subagents",
    "transcripts",
    "logs",
    "skills",
    "models",
    "approvals",
    "alerts",
    "notifications",
    "context",
    "limits",
    "clusters",
    "history",
]

# Overlay element IDs that signal the auth overlay is blocking the UI.
# Any of these being visible after token injection means the token was not accepted.
_BLOCKING_OVERLAY_IDS = [
    "login-overlay",
    "gw-setup-overlay",
    "auth-overlay",
    "setup-overlay",
]

pytestmark = pytest.mark.skipif(
    not _PLAYWRIGHT_AVAILABLE,
    reason="playwright not installed -- pip install pytest-playwright",
)


class TestAllTabsPostAuth:
    """Every canonical OSS dashboard tab must render without auth overlay post-login.

    Acceptance test for C5: 'gateway token not passed for OSS, never displays
    other screens' (user-reported 2026-05-17).

    If a test fails with 'overlay still visible', check that:
      1. The server was started with OPENCLAW_GATEWAY_TOKEN matching CLAWMETRY_TOKEN.
      2. The /api/auth/check endpoint returns {valid: true} with the token.
    """

    def test_auth_check_api_returns_valid(self):
        """Server must return {valid: true} from /api/auth/check with the token."""
        req = urllib.request.Request(
            f"{BASE_URL}/api/auth/check",
            headers={"Authorization": f"Bearer {TOKEN}"},
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read())

        assert data.get("valid") is True, (
            f"/api/auth/check returned valid=False. "
            f"Response: {data}. "
            f"Ensure the server was started with OPENCLAW_GATEWAY_TOKEN={TOKEN!r}."
        )

    @pytest.mark.parametrize("tab", CANONICAL_TABS)
    def test_tab_loads_without_auth_overlay(self, _overlay_page, tab):
        """Tab must be reachable and must NOT show an auth-blocking overlay."""
        page = _overlay_page
        page.goto(BASE_URL + "/", wait_until="domcontentloaded", timeout=15000)

        if tab != "overview":
            page.evaluate(
                "typeof window.switchTab === 'function' && "
                f"window.switchTab({json.dumps(tab)})"
            )

        page.wait_for_timeout(1000)

        blocking = []
        for oid in _BLOCKING_OVERLAY_IDS:
            el = page.query_selector(f"#{oid}")
            if el is None:
                continue
            display = el.evaluate("el => getComputedStyle(el).display")
            visibility = el.evaluate("el => getComputedStyle(el).visibility")
            if display != "none" and visibility != "hidden":
                blocking.append(
                    f"#{oid} display={display!r} visibility={visibility!r}"
                )

        assert not blocking, (
            f"Tab '{tab}': auth overlay(s) still visible after token injection: "
            + ", ".join(blocking)
            + f". Ensure OPENCLAW_GATEWAY_TOKEN={TOKEN!r} matches CLAWMETRY_TOKEN."
        )
