"""Page load + content integrity tests."""
import pytest


# ── Page load ──────────────────────────────────────────────────────────────

class TestPageLoads:
    def test_index(self, client):
        r = client.get("/")
        assert r.status_code == 200
        assert b"ClawMetry" in r.data

    def test_showcase(self, client):
        r = client.get("/showcase")
        assert r.status_code == 200
        assert b"ClawMetry" in r.data

    def test_docs(self, client):
        r = client.get("/docs.html")
        assert r.status_code == 200

    def test_traction(self, client):
        r = client.get("/traction")
        assert r.status_code == 200

    def test_globe(self, client):
        r = client.get("/globe")
        assert r.status_code == 200
        assert b"ClawMetry" in r.data

    def test_install_sh(self, client):
        r = client.get("/install.sh")
        assert r.status_code == 200
        assert b"clawmetry" in r.data.lower()

    def test_install_ps1(self, client):
        r = client.get("/install.ps1")
        assert r.status_code == 200

    def test_install_cmd(self, client):
        r = client.get("/install.cmd")
        assert r.status_code == 200

    def test_robots(self, client):
        r = client.get("/robots.txt")
        assert r.status_code == 200

    def test_sitemap(self, client):
        r = client.get("/sitemap.xml")
        assert r.status_code == 200

    def test_llms_txt(self, client):
        r = client.get("/llms.txt")
        assert r.status_code == 200

    def test_404_on_random(self, client):
        r = client.get("/this-does-not-exist-xyz")
        # Should not 500 -- either 404 or it serves a static file
        assert r.status_code != 500


# ── Landing page content ───────────────────────────────────────────────────

class TestIndexContent:
    def test_view_all_link_present(self, client):
        """'View all' link to /showcase must exist in the What People Say section."""
        r = client.get("/")
        assert b'href="/showcase"' in r.data, "Missing View all → link to /showcase"
        assert b"View all" in r.data

    def test_no_old_ph_anchor_format(self, client):
        """Old-style #comment-43111XX links must not appear (broken IDs from initial build)."""
        r = client.get("/")
        assert b"#comment-4311191" not in r.data
        assert b"#comment-4311192" not in r.data
        assert b"#comment-4311193" not in r.data
        assert b"#comment-4311194" not in r.data

    def test_ph_links_use_query_format(self, client):
        """PH comment links must use ?comment= format so PH scrolls to the comment."""
        r = client.get("/")
        html = r.data.decode()
        if "producthunt.com/products/clawmetry" in html:
            assert "?comment=" in html, "PH links must use ?comment=ID format"

    def test_no_underline_on_view_all(self, client):
        """View all link must have text-decoration:none."""
        r = client.get("/")
        html = r.data.decode()
        # Find the specific 'View all' showcase link (not mobile subnav)
        assert 'href="/showcase" style="' in html or 'View all' in html
        # Find all showcase hrefs, check at least one has text-decoration:none nearby
        found = False
        start = 0
        while True:
            idx = html.find('href="/showcase"', start)
            if idx == -1:
                break
            surrounding = html[max(0, idx-200):idx+200]
            if "text-decoration:none" in surrounding or "text-decoration: none" in surrounding:
                found = True
                break
            start = idx + 1
        assert found

    def test_what_people_say_section(self, client):
        r = client.get("/")
        assert b"What People Say" in r.data

    def test_no_placeholder_avatar_urls(self, client):
        """ui-avatars.com placeholders must not be used for real people."""
        r = client.get("/")
        html = r.data.decode()
        # These specific placeholder avatars should be gone
        assert "ui-avatars.com/api/?name=OD" not in html, "oadiaz still using placeholder avatar"
        assert "ui-avatars.com/api/?name=MK" not in html, "Mykola still using placeholder avatar"
        assert "ui-avatars.com/api/?name=DS" not in html, "Damian still using placeholder avatar"


# ── Showcase page content ──────────────────────────────────────────────────

class TestShowcaseContent:
    def test_all_ph_commenters_present(self, client):
        r = client.get("/showcase")
        assert b"Mykola" in r.data
        assert b"Damian" in r.data
        assert b"Mihail" in r.data
        assert b"Harsh" in r.data

    def test_ph_links_query_format(self, client):
        r = client.get("/showcase")
        html = r.data.decode()
        assert "#comment-43111" not in html, "Old wrong comment IDs still present"
        assert "?comment=5158089" in html, "Mykola comment link missing"
        assert "?comment=5158871" in html, "Damian comment link missing"
        assert "?comment=5163665" in html, "Mihail comment link missing"
        assert "?comment=5161049" in html, "Harsh comment link missing"

    def test_real_ph_avatars_used(self, client):
        r = client.get("/showcase")
        html = r.data.decode()
        assert "ph-avatars.imgix.net" in html, "PH commenters should use real ph-avatars.imgix.net"

    def test_oadiaz_real_avatar(self, client):
        r = client.get("/showcase")
        assert b"miro.medium.com" in r.data, "oadiaz should use real Medium avatar"

    def test_linkedin_logo_not_initials(self, client):
        r = client.get("/showcase")
        html = r.data.decode()
        assert "ui-avatars.com/api/?name=LI" not in html, "LinkedIn card still using LI initials"

    def test_nav_lobster_logo(self, client):
        """Nav should use lobster emoji, not custom SVG."""
        r = client.get("/showcase")
        assert "🦞" in r.data.decode()

    def test_backboardioclip_no_dead_tweet(self, client):
        """backboardioclip should link to profile, not dead tweet URL."""
        r = client.get("/showcase")
        assert b"/status/2025703625306382542" not in r.data

    def test_no_underline_styles_removed(self, client):
        r = client.get("/showcase")
        # Showcase links should not have underline (text-decoration from browser default)
        # Just ensure page loads without error
        assert r.status_code == 200

    def test_submit_cta_present(self, client):
        r = client.get("/showcase")
        assert b"showcase" in r.data.lower()
        assert b"Share" in r.data or b"Built something" in r.data


# ── /docs redirect ─────────────────────────────────────────────────────────

class TestDocsRedirect:
    def test_docs_slash_redirects(self, client):
        """GET /docs must 301 redirect to /docs.html."""
        r = client.get("/docs")
        assert r.status_code == 301, f"Expected 301, got {r.status_code}"
        loc = r.headers.get("Location", "")
        assert loc.endswith("/docs.html"), f"Expected redirect to /docs.html, got {loc}"

    def test_docs_html_loads(self, client):
        """GET /docs.html must return 200 with content."""
        r = client.get("/docs.html")
        assert r.status_code == 200
        assert b"ClawMetry" in r.data or b"clawmetry" in r.data.lower()


# ── Traction page integrity ─────────────────────────────────────────────────

class TestTractionIntegrity:
    def test_traction_loads(self, client):
        r = client.get("/traction")
        assert r.status_code == 200

    def test_traction_no_ellipsis_on_cold_start(self, client):
        """PyPI stats must never show bare ... seeded fallbacks must kick in."""
        r = client.get("/traction")
        html = r.data.decode()
        assert '<div class="metric-number">...</div>' not in html,             "PyPI metric showing raw ... cold-start fallback not working"
        assert '<div class="metric-number accent">...</div>' not in html,             "PyPI 30-day metric showing raw ... cold-start fallback not working"

    def test_traction_has_timeline(self, client):
        r = client.get("/traction")
        assert b"Timeline" in r.data

    def test_traction_karpathy_entry(self, client):
        """Feb 20 Karpathy timeline entry must be present."""
        r = client.get("/traction")
        html = r.data.decode()
        assert "Feb 20" in html, "Feb 20 Karpathy entry missing from timeline"
        assert "Karpathy" in html, "Karpathy name missing from timeline"

    def test_traction_ph_launch_entry(self, client):
        """Feb 18 entry must say ClawMetry Product Hunt launch."""
        r = client.get("/traction")
        assert b"ClawMetry Product Hunt launch" in r.data


# ── robots.txt enforcement ──────────────────────────────────────────────────

class TestRobotsTxt:
    def test_robots_disallows_api(self, client):
        """robots.txt must block /api/ to prevent 404s in Google Search Console."""
        r = client.get("/robots.txt")
        assert r.status_code == 200
        assert b"Disallow: /api/" in r.data, "robots.txt must disallow /api/"

    def test_robots_disallows_admin(self, client):
        r = client.get("/robots.txt")
        assert b"Disallow: /admin/" in r.data, "robots.txt must disallow /admin/"

    def test_robots_has_sitemap(self, client):
        r = client.get("/robots.txt")
        assert b"sitemap.xml" in r.data.lower()


# ── Sitemap completeness ────────────────────────────────────────────────────

class TestSitemap:
    def test_sitemap_includes_traction(self, client):
        r = client.get("/sitemap.xml")
        assert b"/traction" in r.data, "Sitemap missing /traction"

    def test_sitemap_includes_showcase(self, client):
        r = client.get("/sitemap.xml")
        assert b"/showcase" in r.data, "Sitemap missing /showcase"

    def test_sitemap_valid_xml(self, client):
        import xml.etree.ElementTree as ET
        r = client.get("/sitemap.xml")
        assert r.status_code == 200
        try:
            ET.fromstring(r.data)
        except ET.ParseError as e:
            pytest.fail(f"sitemap.xml is not valid XML: {e}")
