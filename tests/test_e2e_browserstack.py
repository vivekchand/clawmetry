"""
BrowserStack E2E tests for ClawMetry.
Uses BrowserStack's pytest-playwright integration via browserstack.yml.
Run via: browserstack-sdk python3 -m pytest tests/test_e2e_browserstack.py
"""
import os
import pytest

CLAWMETRY_URL = os.environ.get("CLAWMETRY_URL", "http://localhost:8900")
CLAWMETRY_TOKEN = os.environ.get("CLAWMETRY_TOKEN", "")


@pytest.fixture(autouse=True)
def set_auth(page):
    """Inject auth token into localStorage before each test."""
    page.goto(CLAWMETRY_URL)
    if CLAWMETRY_TOKEN:
        page.evaluate(f"localStorage.setItem('clawmetry_token', '{CLAWMETRY_TOKEN}')")
        page.reload()
        page.wait_for_load_state("networkidle", timeout=10000)


class TestCrossBrowserLoad:
    def test_page_loads(self, page):
        page.goto(CLAWMETRY_URL)
        assert page.title() != ""

    def test_has_nav_tabs(self, page):
        page.goto(CLAWMETRY_URL)
        page.wait_for_selector("nav, .tab, [role=tab], .nav-tab", timeout=10000)

    def test_flow_svg_renders(self, page):
        page.goto(CLAWMETRY_URL)
        page.wait_for_selector("svg", timeout=10000)
        assert page.query_selector("svg") is not None

    def test_no_critical_js_errors(self, page):
        errors = []
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.goto(CLAWMETRY_URL)
        page.wait_for_timeout(3000)
        critical = [e for e in errors if "TypeError" in e or "ReferenceError" in e]
        assert len(critical) == 0, f"JS errors: {critical}"

    def test_overview_tab(self, page):
        page.goto(CLAWMETRY_URL)
        overview = page.query_selector("text=Overview")
        if overview:
            overview.click()
            page.wait_for_timeout(2000)

    def test_flow_tab(self, page):
        page.goto(CLAWMETRY_URL)
        flow = page.query_selector("text=Flow")
        if flow:
            flow.click()
            page.wait_for_selector("svg", timeout=5000)

    def test_responsive_1920(self, page):
        page.set_viewport_size({"width": 1920, "height": 1080})
        page.goto(CLAWMETRY_URL)
        page.wait_for_timeout(1000)
        scroll_width = page.evaluate("document.body.scrollWidth")
        assert scroll_width <= 1940

    def test_responsive_768(self, page):
        page.set_viewport_size({"width": 768, "height": 1024})
        page.goto(CLAWMETRY_URL)
        page.wait_for_timeout(1000)
        scroll_width = page.evaluate("document.body.scrollWidth")
        assert scroll_width <= 790
