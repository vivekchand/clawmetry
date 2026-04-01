"""
Tests for the Agent Reliability Scorer (GH #464).

Verifies:
- /api/history/reliability returns correct structure
- Direction values are valid
- All required keys present
- Custom window parameter works
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


class TestReliability:
    def test_endpoint_returns_200(self, api, base_url):
        """Reliability endpoint is reachable."""
        r = get(api, base_url, "/api/history/reliability")
        assert_ok(r)

    def test_required_top_level_keys(self, api, base_url):
        """Response has required top-level keys."""
        d = assert_ok(get(api, base_url, "/api/history/reliability"))
        assert_keys(d, "direction", "slope_per_session", "significant",
                    "session_count", "window_days", "degrading_dimensions", "points")

    def test_direction_is_valid_string(self, api, base_url):
        """direction is one of the four valid values."""
        d = assert_ok(get(api, base_url, "/api/history/reliability"))
        assert d["direction"] in ("improving", "degrading", "stable", "insufficient_data"), \
            f"Unexpected direction: {d['direction']}"

    def test_significant_is_bool(self, api, base_url):
        """significant is a boolean."""
        d = assert_ok(get(api, base_url, "/api/history/reliability"))
        assert isinstance(d["significant"], bool)

    def test_degrading_dimensions_is_list(self, api, base_url):
        """degrading_dimensions is always a list."""
        d = assert_ok(get(api, base_url, "/api/history/reliability"))
        assert isinstance(d["degrading_dimensions"], list)

    def test_points_is_list_with_correct_structure(self, api, base_url):
        """points is a list; each point has ts, delivery, efficiency."""
        d = assert_ok(get(api, base_url, "/api/history/reliability"))
        assert isinstance(d["points"], list)
        for p in d["points"]:
            assert_keys(p, "ts", "delivery", "efficiency")

    def test_custom_window_parameter(self, api, base_url):
        """Custom window parameter is accepted and reflected."""
        d = assert_ok(get(api, base_url, "/api/history/reliability?window=7"))
        assert d["window_days"] == 7

    def test_slope_fields_present(self, api, base_url):
        """delivery_slope, efficiency_slope, cost_slope are in response."""
        d = assert_ok(get(api, base_url, "/api/history/reliability"))
        assert_keys(d, "delivery_slope", "efficiency_slope", "cost_slope")
