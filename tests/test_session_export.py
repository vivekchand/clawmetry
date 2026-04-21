"""Tests for /api/sessions/<session_id>/export — session data export (GH #593)."""

import pytest
import requests


def get(api, base_url, path):
    """Make an authenticated GET request and return the response."""
    return api.get(f"{base_url}{path}", timeout=10)


class TestSessionExport:
    """Tests for session data export endpoint."""

    def test_export_json_status(self, api, base_url):
        """Export endpoint accepts format=json parameter."""
        # First get a session ID
        r = get(api, base_url, "/api/transcripts")
        if r.status_code != 200:
            pytest.skip("No transcripts available")
        d = r.json()
        transcripts = d.get("transcripts", [])
        if not transcripts:
            pytest.skip("No transcripts available")
        session_id = transcripts[0].get("id", "")
        if not session_id:
            pytest.skip("No session ID found")

        r = get(api, base_url, f"/api/sessions/{session_id}/export?format=json")
        assert r.status_code == 200, (
            f"Expected 200, got {r.status_code}: {r.text[:200]}"
        )
        assert r.headers.get("Content-Type") == "application/json"
        assert "attachment" in r.headers.get("Content-Disposition", "")

    def test_export_csv_status(self, api, base_url):
        """Export endpoint accepts format=csv parameter."""
        r = get(api, base_url, "/api/transcripts")
        if r.status_code != 200:
            pytest.skip("No transcripts available")
        d = r.json()
        transcripts = d.get("transcripts", [])
        if not transcripts:
            pytest.skip("No transcripts available")
        session_id = transcripts[0].get("id", "")
        if not session_id:
            pytest.skip("No session ID found")

        r = get(api, base_url, f"/api/sessions/{session_id}/export?format=csv")
        assert r.status_code == 200, (
            f"Expected 200, got {r.status_code}: {r.text[:200]}"
        )
        assert r.headers.get("Content-Type") == "text/csv"
        assert "attachment" in r.headers.get("Content-Disposition", "")

    def test_export_invalid_format(self, api, base_url):
        """Invalid format returns 400."""
        r = get(api, base_url, "/api/sessions/invalid/export?format=xml")
        assert r.status_code == 400, (
            f"Expected 400 for invalid format, got {r.status_code}"
        )

    def test_export_session_not_found(self, api, base_url):
        """Non-existent session returns 404."""
        r = get(api, base_url, "/api/sessions/nonexistent123/export?format=json")
        assert r.status_code == 404, (
            f"Expected 404 for non-existent session, got {r.status_code}"
        )

    def test_export_json_structure(self, api, base_url):
        """JSON export has expected structure."""
        r = get(api, base_url, "/api/transcripts")
        if r.status_code != 200:
            pytest.skip("No transcripts available")
        d = r.json()
        transcripts = d.get("transcripts", [])
        if not transcripts:
            pytest.skip("No transcripts available")
        session_id = transcripts[0].get("id", "")
        if not session_id:
            pytest.skip("No session ID found")

        r = get(api, base_url, f"/api/sessions/{session_id}/export?format=json")
        d = r.json()
        assert "session_id" in d
        assert "exported_at" in d
        assert "messages" in d
        assert "tool_calls" in d
        assert "cost_data" in d
        assert "metadata" in d
        assert isinstance(d["messages"], list)
        assert isinstance(d["tool_calls"], list)

    def test_export_csv_content(self, api, base_url):
        """CSV export contains expected headers and data."""
        r = get(api, base_url, "/api/transcripts")
        if r.status_code != 200:
            pytest.skip("No transcripts available")
        d = r.json()
        transcripts = d.get("transcripts", [])
        if not transcripts:
            pytest.skip("No transcripts available")
        session_id = transcripts[0].get("id", "")
        if not session_id:
            pytest.skip("No session ID found")

        r = get(api, base_url, f"/api/sessions/{session_id}/export?format=csv")
        csv_content = r.text
        assert "# Session Export" in csv_content
        assert "## MESSAGES" in csv_content
        assert "Timestamp,Role,Model,Content" in csv_content
