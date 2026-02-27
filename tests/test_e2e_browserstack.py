"""
BrowserStack E2E tests for ClawMetry.
Runs on real browsers via BrowserStack Automate.
Credentials passed via env vars (never committed to repo).
"""
import os
import pytest
from playwright.sync_api import sync_playwright

CLAWMETRY_URL = os.environ.get("CLAWMETRY_URL", "http://localhost:8900")
CLAWMETRY_TOKEN = os.environ.get("CLAWMETRY_TOKEN", "")
BS_USERNAME = os.environ.get("BROWSERSTACK_USERNAME", "")
BS_ACCESS_KEY = os.environ.get("BROWSERSTACK_ACCESS_KEY", "")
BS_BROWSER = os.environ.get("BS_BROWSER", "chrome")
BS_OS = os.environ.get("BS_OS", "Windows 11")
BS_LOCAL_ID = os.environ.get("BROWSERSTACK_LOCAL_IDENTIFIER", "")


def get_bs_cdp_url():
    caps = {
        "browser": BS_BROWSER,
        "browser_version": "latest",
        "os": BS_OS.split()[0],
        "os_version": " ".join(BS_OS.split()[1:]),
        "name": f"ClawMetry E2E - {BS_BROWSER}",
        "build": f"clawmetry-pr-{os.environ.get('GITHUB_RUN_ID', 'local')}",
        "browserstack.local": "true",
        "browserstack.localIdentifier": BS_LOCAL_ID,
    }
    import json
    from urllib.parse import quote
    caps_str = quote(json.dumps(caps))
    return f"wss://cdp.browserstack.com/playwright?caps={caps_str}&auth={BS_USERNAME}:{BS_ACCESS_KEY}"


@pytest.fixture(scope="module")
def bs_page():
    """BrowserStack remote browser page."""
    if not BS_USERNAME or not BS_ACCESS_KEY:
        pytest.skip("BrowserStack credentials not set")
    with sync_playwright() as p:
        browser = p.chromium.connect(get_bs_cdp_url())
        ctx = browser.new_context()
        page = ctx.new_page()
        # Set auth token in localStorage
        page.goto(CLAWMETRY_URL)
        if CLAWMETRY_TOKEN:
            page.evaluate(f"localStorage.setItem('clawmetry_token', '{CLAWMETRY_TOKEN}')")
            page.reload()
        yield page
        browser.close()


class TestCrossBrowserLoad:
    def test_page_loads(self, bs_page):
        bs_page.goto(CLAWMETRY_URL)
        assert bs_page.title() != ""

    def test_has_nav_tabs(self, bs_page):
        bs_page.goto(CLAWMETRY_URL)
        bs_page.wait_for_selector("nav, .tab, [role=tab], .nav-tab", timeout=10000)

    def test_flow_svg_renders(self, bs_page):
        bs_page.goto(CLAWMETRY_URL)
        bs_page.wait_for_selector("svg", timeout=10000)
        svg = bs_page.query_selector("svg")
        assert svg is not None

    def test_no_js_errors(self, bs_page):
        errors = []
        bs_page.on("pageerror", lambda e: errors.append(str(e)))
        bs_page.goto(CLAWMETRY_URL)
        bs_page.wait_for_timeout(3000)
        critical = [e for e in errors if "TypeError" in e or "ReferenceError" in e]
        assert len(critical) == 0, f"JS errors: {critical}"

    def test_overview_tab(self, bs_page):
        bs_page.goto(CLAWMETRY_URL)
        # Try clicking Overview tab
        overview = bs_page.query_selector("text=Overview")
        if overview:
            overview.click()
            bs_page.wait_for_timeout(1000)

    def test_flow_tab(self, bs_page):
        bs_page.goto(CLAWMETRY_URL)
        flow = bs_page.query_selector("text=Flow")
        if flow:
            flow.click()
            bs_page.wait_for_selector("svg", timeout=5000)

    def test_responsive_layout(self, bs_page):
        """Check layout doesn't break at common viewport sizes."""
        for width, height in [(1920, 1080), (1280, 800), (768, 1024)]:
            bs_page.set_viewport_size({"width": width, "height": height})
            bs_page.goto(CLAWMETRY_URL)
            bs_page.wait_for_timeout(500)
            # Page should not have horizontal scroll
            scroll_width = bs_page.evaluate("document.body.scrollWidth")
            assert scroll_width <= width + 20, f"Horizontal overflow at {width}px: scrollWidth={scroll_width}"
