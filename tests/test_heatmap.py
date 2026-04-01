"""
Tests for /api/heatmap endpoint.

Covers:
- ?days=7 and ?days=30 both return 200
- Response includes 'days_requested' field matching what was requested
- ?days=90 (max) works
- ?days=91 clamps to 90
- Response structure: 'days', 'max', 'days_requested' keys
- 'days' list length matches days_requested
"""
import pytest


def get_heatmap(api, base_url, days=None):
    """Fetch /api/heatmap with optional ?days= param."""
    url = f"{base_url}/api/heatmap"
    if days is not None:
        url += f"?days={days}"
    return api.get(url, timeout=10)


class TestHeatmapEndpoint:
    def test_default_returns_200(self, api, base_url):
        """Default (no params) returns 200."""
        r = get_heatmap(api, base_url)
        assert r.status_code == 200

    def test_days_7_returns_200(self, api, base_url):
        """`?days=7` returns 200."""
        r = get_heatmap(api, base_url, days=7)
        assert r.status_code == 200

    def test_days_30_returns_200(self, api, base_url):
        """`?days=30` returns 200."""
        r = get_heatmap(api, base_url, days=30)
        assert r.status_code == 200

    def test_days_90_returns_200(self, api, base_url):
        """`?days=90` (max) returns 200."""
        r = get_heatmap(api, base_url, days=90)
        assert r.status_code == 200

    def test_required_keys_present(self, api, base_url):
        """Response has 'days', 'max', and 'days_requested' keys."""
        d = get_heatmap(api, base_url, days=7).json()
        assert "days" in d, f"Missing 'days' key. Got: {list(d.keys())}"
        assert "max" in d, f"Missing 'max' key. Got: {list(d.keys())}"
        assert "days_requested" in d, f"Missing 'days_requested' key. Got: {list(d.keys())}"

    def test_days_requested_matches_7(self, api, base_url):
        """days_requested field matches the requested value for ?days=7."""
        d = get_heatmap(api, base_url, days=7).json()
        assert d["days_requested"] == 7, f"Expected days_requested=7, got {d['days_requested']}"

    def test_days_requested_matches_30(self, api, base_url):
        """days_requested field matches the requested value for ?days=30."""
        d = get_heatmap(api, base_url, days=30).json()
        assert d["days_requested"] == 30, f"Expected days_requested=30, got {d['days_requested']}"

    def test_days_requested_matches_90(self, api, base_url):
        """days_requested field matches 90 for ?days=90."""
        d = get_heatmap(api, base_url, days=90).json()
        assert d["days_requested"] == 90, f"Expected days_requested=90, got {d['days_requested']}"

    def test_days_91_clamps_to_90(self, api, base_url):
        """?days=91 is clamped to 90."""
        r = get_heatmap(api, base_url, days=91)
        assert r.status_code == 200
        d = r.json()
        assert "days_requested" in d, "Missing 'days_requested' key"
        assert d["days_requested"] == 90, (
            f"Expected days_requested=90 (clamped from 91), got {d['days_requested']}"
        )

    def test_days_list_length_matches_requested_7(self, api, base_url):
        """'days' list length equals days_requested for ?days=7."""
        d = get_heatmap(api, base_url, days=7).json()
        assert len(d["days"]) == 7, f"Expected 7 day entries, got {len(d['days'])}"

    def test_days_list_length_matches_requested_30(self, api, base_url):
        """'days' list length equals days_requested for ?days=30."""
        d = get_heatmap(api, base_url, days=30).json()
        assert len(d["days"]) == 30, f"Expected 30 day entries, got {len(d['days'])}"

    def test_each_day_has_24_hours(self, api, base_url):
        """Each day entry has exactly 24 hour buckets."""
        d = get_heatmap(api, base_url, days=7).json()
        for entry in d["days"]:
            assert "hours" in entry, f"Missing 'hours' in day entry: {entry}"
            assert len(entry["hours"]) == 24, (
                f"Expected 24 hour buckets, got {len(entry['hours'])} for {entry.get('label')}"
            )

    def test_max_is_non_negative(self, api, base_url):
        """'max' field is a non-negative number."""
        d = get_heatmap(api, base_url, days=7).json()
        assert isinstance(d["max"], (int, float)), f"'max' should be numeric, got {type(d['max'])}"
        assert d["max"] >= 0, f"'max' should be >= 0, got {d['max']}"

    def test_hour_values_are_non_negative(self, api, base_url):
        """All hour bucket values are non-negative integers."""
        d = get_heatmap(api, base_url, days=7).json()
        for day in d["days"]:
            for val in day["hours"]:
                assert isinstance(val, (int, float)), f"Hour value should be numeric: {val}"
                assert val >= 0, f"Hour value should be >= 0: {val}"
