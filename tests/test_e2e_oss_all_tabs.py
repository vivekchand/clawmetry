"""OSS all-tabs post-auth gate (E2E criterion C5).

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

import importlib
import json
import os
import pathlib
import urllib.request

import pytest

try:
    import playwright  # noqa: F401  -- used by _shared_chromium fixture

    _PLAYWRIGHT_AVAILABLE = True
except ImportError:
    _PLAYWRIGHT_AVAILABLE = False

BASE_URL = os.environ.get("CLAWMETRY_URL", "http://localhost:8900")
TOKEN = os.environ.get("CLAWMETRY_TOKEN", "ci-test-token")


# Class-scoped page shared across all 33 parametrized tab tests.
#
# Why class-scoped instead of function-scoped:
#   The original fixture created a fresh browser context per test
#   (function scope). With 33 parametrized tab cases each doing
#   page.goto("/"), auth-bootstrap.js + gw-setup.js + ~5 API calls
#   per page load overwhelmed the single-threaded waitress WSGI server
#   (queue depth spiked to 5-12) and the last ~10 page.goto() calls
#   timed out with TimeoutError (not auth failures).
#
#   Sharing one context + one page load across the whole class reduces
#   33 page loads to 1. Auth runs once in the fixture; each test just
#   calls switchTab() and checks overlays on the already-loaded page.
@pytest.fixture(scope="class")
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
    # One page load for the entire 33-tab suite.
    page.goto(BASE_URL + "/", wait_until="domcontentloaded", timeout=15000)
    # Let auth-bootstrap.js fetch /api/auth/check and gw-setup.js fetch
    # /api/gw/config settle before any tab test checks for overlays.
    page.wait_for_timeout(2000)
    yield page
    ctx.close()

# Canonical tabs that must load without auth overlay post-login.
#
# These are all tabs that have a template file in clawmetry/templates/tabs/
# or are served by a dedicated route module (e.g. channels via routes/channels.py).
# Kept in sync with the filesystem: if a new tab template is added, add the
# switchTab() identifier here so the post-auth sweep covers it immediately.
#
# The test only checks that none of the four auth-blocking overlay IDs are
# visible -- it does NOT require data to be present. Pro/enterprise gating
# overlays use distinct IDs and will not cause false failures here.
CANONICAL_TABS = [
    # Core dashboard
    "overview",
    "flow",
    "brain",
    "usage",
    "crons",
    "memory",
    "security",
    "subagents",
    "transcripts",
    # Infrastructure / ops
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
    # Tabs added after initial C5 coverage -- verified present in
    # clawmetry/templates/tabs/ or routes/ as of 2026-06-09.
    "channels",          # routes/channels.py: 21 chat-channel adapters
    "dives",             # dives.html / dives.js: session deep-dive feature
    "harness",           # harness.html: harness observability
    "inventory",         # inventory.html: tool/resource inventory
    "nemoclaw",          # nemoclaw.html: NeMo Guardrails governance
    "policy",            # policy.html: policy management
    "selfevolve",        # selfevolve.html: self-evolve feature
    "swimlane",          # swimlane.html: swimlane visualization
    "tool-catalog",      # tool-catalog.html: tool catalog
    "tracing",           # tracing.html: OpenTelemetry tracing view
    "turn-anatomy",      # turn-anatomy.html: turn anatomy analysis
    "version-impact",    # version-impact.html: version impact view
    "context-economics", # context-economics.html: context economics
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


def test_canonical_tabs_cover_all_templates():
    """Every clawmetry/templates/tabs/*.html stem must be in CANONICAL_TABS.

    Catches the silent-drift gap: a new tab template added to
    clawmetry/templates/tabs/ without updating CANONICAL_TABS (and
    pr-screenshots.yml + visual-diff.mjs) would never receive the
    post-auth overlay sweep required by C5, and could silently ship
    with a login overlay blocking the new tab in production.

    When this test fails it lists every missing stem and names the
    three files that need to be updated.
    """
    try:
        clawmetry_mod = importlib.import_module("clawmetry")
    except ImportError:
        pytest.skip("clawmetry package not installed -- run 'pip install -e .'")

    tabs_dir = pathlib.Path(clawmetry_mod.__file__).parent / "templates" / "tabs"
    if not tabs_dir.exists():
        pytest.skip(f"templates/tabs/ not found at {tabs_dir} -- check package layout")

    template_stems = {p.stem for p in tabs_dir.glob("*.html")}
    canonical_set = set(CANONICAL_TABS)

    uncovered = template_stems - canonical_set
    assert not uncovered, (
        f"Tab template(s) in clawmetry/templates/tabs/ are NOT in CANONICAL_TABS "
        f"and will never be post-auth swept (C5 gap): {sorted(uncovered)}. "
        f"Add each missing name to:\n"
        f"  1. CANONICAL_TABS in tests/test_e2e_oss_all_tabs.py\n"
        f"  2. PR_SCREENSHOT_TABS in .github/workflows/pr-screenshots.yml\n"
        f"  3. DEFAULT_TABS in .github/scripts/visual-diff.mjs"
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
        """Tab must NOT show an auth-blocking overlay after token injection.

        The page is loaded once per class (class-scoped fixture); this test
        only calls switchTab() and checks the overlay state. Re-navigating
        to "/" per test caused 33 sequential page loads that saturated the
        waitress WSGI queue and produced spurious TimeoutErrors.
        """
        page = _overlay_page

        if tab != "overview":
            page.evaluate(
                "typeof window.switchTab === 'function' && "
                f"window.switchTab({json.dumps(tab)})"
            )

        page.wait_for_timeout(500)

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
