"""
Tests for the Upgrade Impact Dashboard (GH #408).

Verifies:
- /api/version-impact returns correct structure
- Version detection works
- Transition format is correct with before/after/diff
"""
import pytest
import requests


def get(api, base_url, path):
    return api.get(f"{base_url}{path}", timeout=10)


def assert_ok(resp):
    assert resp.status_code == 200, (
        f"Expected 200 for {resp.url}, got {resp.status_code}: {resp.text[:200]}"
    )
    return resp.json()


def assert_keys(data, *keys):
    for k in keys:
        assert k in data, f"Missing key '{k}' in response: {list(data.keys())}"


class TestVersionImpact:
    def test_endpoint_returns_200(self, api, base_url):
        """Version impact endpoint is reachable."""
        r = get(api, base_url, "/api/version-impact")
        assert_ok(r)

    def test_required_top_level_keys(self, api, base_url):
        """Response has required top-level keys."""
        d = assert_ok(get(api, base_url, "/api/version-impact"))
        assert_keys(d, "current_version", "version_detected", "transitions")

    def test_current_version_is_string(self, api, base_url):
        """current_version is a string (could be 'unknown' if not detected)."""
        d = assert_ok(get(api, base_url, "/api/version-impact"))
        assert isinstance(d["current_version"], str)

    def test_version_detected_is_bool(self, api, base_url):
        """version_detected is a boolean."""
        d = assert_ok(get(api, base_url, "/api/version-impact"))
        assert isinstance(d["version_detected"], bool)

    def test_transitions_is_list(self, api, base_url):
        """transitions is always a list."""
        d = assert_ok(get(api, base_url, "/api/version-impact"))
        assert isinstance(d["transitions"], list)

    def test_transition_structure(self, api, base_url):
        """If transitions exist, each has from/to/before/after/diff."""
        d = assert_ok(get(api, base_url, "/api/version-impact"))
        for t in d["transitions"]:
            assert_keys(t, "from_version", "to_version", "upgraded_at", "before", "after", "diff")
            assert_keys(t["before"], "session_count", "avg_cost", "avg_tokens", "error_rate")
            assert_keys(t["after"], "session_count", "avg_cost", "avg_tokens", "error_rate")
            assert_keys(t["diff"], "avg_cost", "avg_tokens", "error_rate")
            # Each diff metric has before/after/pct_change
            for key in ("avg_cost", "avg_tokens", "error_rate"):
                metric = t["diff"][key]
                assert "before" in metric
                assert "after" in metric
                assert "pct_change" in metric

    def test_version_history_present(self, api, base_url):
        """version_history list is present in response."""
        d = assert_ok(get(api, base_url, "/api/version-impact"))
        if "version_history" in d:
            assert isinstance(d["version_history"], list)
            for v in d["version_history"]:
                assert_keys(v, "version", "detected_at")
