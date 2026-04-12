"""
Tests for CORS configuration on API endpoints.

Verifies that appropriate CORS headers are present for cross-origin requests.
"""

import pytest
import requests


class TestCORS:
    """Test CORS headers on API endpoints."""

    def test_preflight_request(self, base_url):
        """OPTIONS request should return CORS headers for cross-origin preflight."""
        r = requests.options(
            f"{base_url}/api/overview",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
                "Access-Control-Request-Headers": "Authorization",
            },
            timeout=5,
        )
        assert r.status_code == 200, (
            f"Expected 200 for OPTIONS preflight, got {r.status_code}"
        )
        assert "Access-Control-Allow-Origin" in r.headers, (
            "Missing Access-Control-Allow-Origin header in preflight response"
        )

    def test_cors_allow_origin_header(self, base_url):
        """GET request with Origin header should include CORS headers."""
        r = requests.get(
            f"{base_url}/api/overview",
            headers={"Origin": "http://localhost:3000"},
            timeout=5,
        )
        assert r.status_code == 200
        assert "Access-Control-Allow-Origin" in r.headers, (
            "Missing Access-Control-Allow-Origin header in response"
        )

    def test_cors_allow_methods_in_preflight(self, base_url):
        """Preflight response should include Access-Control-Allow-Methods."""
        r = requests.options(
            f"{base_url}/api/overview",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
            },
            timeout=5,
        )
        assert r.status_code == 200
        assert "Access-Control-Allow-Methods" in r.headers, (
            "Missing Access-Control-Allow-Methods header in preflight response"
        )

    def test_cors_allow_credentials(self, base_url):
        """Response should include Access-Control-Allow-Credentials when applicable."""
        r = requests.get(
            f"{base_url}/api/overview",
            headers={"Origin": "http://localhost:3000"},
            timeout=5,
        )
        assert r.status_code == 200
        assert "Access-Control-Allow-Credentials" in r.headers, (
            "Missing Access-Control-Allow-Credentials header in response"
        )
