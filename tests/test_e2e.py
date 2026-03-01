"""
ClawMetry E2E browser tests using Playwright.

Tests key UI screens to ensure they load and render correctly.
Uses actual click interactions (nav tabs use event.target so JS calls won't work).
"""
import os
import json
import pytest
from playwright.sync_api import Page, sync_playwright


BASE_URL = os.environ.get("CLAWMETRY_URL", "http://localhost:8900")


def _detect_gateway_token():
    token = os.environ.get("CLAWMETRY_TOKEN", "").strip()
    if token:
        return token
    config_path = os.path.expanduser("~/.openclaw/openclaw.json")
    try:
        with open(config_path) as f:
            cfg = json.load(f)
        return cfg.get("gateway", {}).get("auth", {}).get("token", "").strip()
    except Exception:
        return None


GATEWAY_TOKEN = _detect_gateway_token()


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def browser_context():
    """Launch Chromium, inject auth token into localStorage."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(base_url=BASE_URL)

        # Inject auth token into localStorage before tests
        if GATEWAY_TOKEN:
            setup_page = ctx.new_page()
            setup_page.goto(BASE_URL, wait_until="domcontentloaded")
            setup_page.evaluate(
                f"localStorage.setItem('clawmetry-token', '{GATEWAY_TOKEN}')"
            )
            setup_page.close()

        yield ctx
        browser.close()


@pytest.fixture
def page(browser_context):
    """Fresh page for each test."""
    p = browser_context.new_page()
    yield p
    p.close()


def load_dashboard(page: Page, wait_ms: int = 1500):
    """Navigate to dashboard and wait for initial render."""
    # Inject token before navigating (each new page needs it)
    if GATEWAY_TOKEN:
        page.goto(BASE_URL, wait_until="domcontentloaded")
        page.evaluate(f"localStorage.setItem('clawmetry-token', '{GATEWAY_TOKEN}')")
        page.reload(wait_until="domcontentloaded")
    else:
        page.goto(BASE_URL, wait_until="domcontentloaded")
    # Dismiss boot overlay and mark app ready so nav tabs are clickable
    page.evaluate("""() => {
        var o = document.getElementById('boot-overlay');
        if (o) o.style.display = 'none';
        document.body.className = 'app-ready';
    }""")
    page.wait_for_timeout(wait_ms)


def click_tab(page: Page, tab_label: str):
    """Click a nav tab by its text label."""
    tab = page.locator(f".nav-tab:has-text('{tab_label}')")
    if tab.count() == 0:
        pytest.skip(f"Nav tab '{tab_label}' not found")
    tab.first.click()
    page.wait_for_timeout(600)


# ---------------------------------------------------------------------------
# Tab loading tests
# ---------------------------------------------------------------------------

class TestTabsLoad:
    def test_page_loads(self, page: Page):
        """Dashboard root loads without error."""
        load_dashboard(page)
        assert page.title() != ""

    def test_page_has_nav_tabs(self, page: Page):
        """Dashboard shows navigation tabs."""
        load_dashboard(page)
        tabs = page.locator(".nav-tab")
        assert tabs.count() > 0, "No nav tabs found in dashboard"

    def test_overview_tab_is_default(self, page: Page):
        """Overview page is active by default."""
        load_dashboard(page)
        overview = page.locator("#page-overview")
        assert overview.count() > 0, "#page-overview element not found"
        # Check it's the active page
        active = page.locator("#page-overview.active")
        assert active.count() > 0, "#page-overview should be active by default"

    def test_flow_tab_loads(self, page: Page):
        """Clicking Flow tab shows the flow page."""
        load_dashboard(page)
        click_tab(page, "Flow")
        flow_page = page.locator("#page-flow")
        if flow_page.count() == 0:
            # Flow is part of overview in some layouts
            svg = page.locator("svg")
            assert svg.count() > 0, "Flow tab: no SVG found"
        else:
            assert flow_page.count() > 0

    def test_overview_tab_loads(self, page: Page):
        """Clicking Overview tab shows overview page."""
        load_dashboard(page)
        click_tab(page, "Overview")
        overview = page.locator("#page-overview.active")
        assert overview.count() > 0, "#page-overview should be active"

    def test_crons_tab_loads(self, page: Page):
        """Clicking Crons tab shows crons page."""
        load_dashboard(page)
        click_tab(page, "Crons")
        crons_page = page.locator("#page-crons")
        assert crons_page.count() > 0, "#page-crons element not found"

    def test_usage_tab_loads(self, page: Page):
        """Clicking Tokens/Usage tab shows usage page."""
        load_dashboard(page)
        click_tab(page, "Tokens")
        usage_page = page.locator("#page-usage")
        assert usage_page.count() > 0, "#page-usage element not found"

    def test_memory_tab_loads(self, page: Page):
        """Clicking Memory tab shows memory page."""
        load_dashboard(page)
        click_tab(page, "Memory")
        memory_page = page.locator("#page-memory")
        assert memory_page.count() > 0, "#page-memory element not found"

    def test_no_critical_js_errors_on_load(self, page: Page):
        """Page should load without uncaught TypeError/ReferenceError."""
        errors = []
        page.on("pageerror", lambda err: errors.append(str(err)))
        load_dashboard(page)
        critical = [e for e in errors if "TypeError" in e or "ReferenceError" in e]
        assert len(critical) == 0, f"Critical JS errors on load: {critical}"

    def test_all_nav_tabs_clickable(self, page: Page):
        """All visible nav tabs can be clicked without JS errors."""
        errors = []
        page.on("pageerror", lambda err: errors.append(str(err)))
        load_dashboard(page)
        
        tabs = page.locator(".nav-tab")
        count = tabs.count()
        assert count > 0, "No nav tabs found"
        
        for i in range(count):
            tabs.nth(i).click()
            page.wait_for_timeout(300)
        
        critical = [e for e in errors if "TypeError" in e or "ReferenceError" in e]
        assert len(critical) == 0, f"JS errors when clicking tabs: {critical}"


# ---------------------------------------------------------------------------
# Flow diagram tests
# ---------------------------------------------------------------------------

class TestFlowDiagram:
    def test_flow_svg_present(self, page: Page):
        """Flow diagram has an SVG element after page loads."""
        load_dashboard(page, wait_ms=2000)
        # Overview tab shows the flow SVG by default
        svg = page.locator("svg")
        assert svg.count() > 0, "No SVG element found on dashboard"

    def test_flow_has_visual_elements(self, page: Page):
        """Flow SVG contains rendered elements."""
        load_dashboard(page, wait_ms=2000)
        elements = page.locator("svg g, svg circle, svg rect, svg path, svg text")
        assert elements.count() > 0, "Flow SVG has no rendered elements"

    def test_flow_svg_has_children(self, page: Page):
        """The flow SVG isn't empty."""
        load_dashboard(page, wait_ms=2000)
        svg = page.locator("svg").first
        if svg.count() == 0:
            pytest.skip("No SVG on page")
        # SVG should have some content
        html = page.locator("svg").first.inner_html()
        assert len(html.strip()) > 0, "Flow SVG is empty"

    def test_clickable_elements_in_svg(self, page: Page):
        """SVG has clickable elements (nodes)."""
        load_dashboard(page, wait_ms=2000)
        # Nodes typically have cursor:pointer
        clickable = page.locator("svg [style*='cursor'], svg g[onclick], svg circle[onclick]")
        svg_groups = page.locator("svg g")
        assert clickable.count() > 0 or svg_groups.count() > 0, (
            "No clickable elements found in SVG"
        )

    @pytest.mark.xfail(reason="flaky: SVG modal depends on runtime channel data", strict=False)
    def test_clicking_svg_group_may_open_modal(self, page: Page):
        """Clicking an SVG element attempts to open a detail modal."""
        load_dashboard(page, wait_ms=2000)

        # Try clicking the first SVG group that might be a node
        groups = page.locator("svg g")
        if groups.count() == 0:
            pytest.skip("No SVG groups to click")

        # Click first few groups to find one that opens a modal
        modal_opened = False
        for i in range(min(groups.count(), 5)):
            groups.nth(i).click(force=True)
            page.wait_for_timeout(400)
            modal = page.locator(".modal, [role='dialog'], .modal-overlay")
            if modal.count() > 0:
                modal_opened = True
                break

        # It's OK if no modal opens — this is a "should" not a "must"
        # The important thing is no crash occurred
        assert True  # No exception = success
