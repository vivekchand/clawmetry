"""
Security tests for ClawMetry - path traversal prevention.

Tests that file access endpoints properly sanitize user input
to prevent reading files outside the sessions directory.
"""

import pytest
import requests


def get(api, base_url, path):
    """Make an authenticated GET request and return the response."""
    return api.get(f"{base_url}{path}", timeout=10)


class TestPathTraversal:
    """Tests for path traversal vulnerability prevention.

    Attackers may try to access files outside the sessions directory
    by providing session_ids containing path traversal sequences like
    '../' or absolute paths. Endpoints must sanitize these inputs.
    """

    def test_cron_run_log_rejects_path_traversal(self, api, base_url):
        """api/cron-run-log should reject session_id with '../' sequences.

        A malicious session_id like '../../../etc/passwd' could otherwise
        read sensitive system files. The endpoint must return 403.
        """
        r = get(api, base_url, "/api/cron-run-log?session_id=../../../etc/passwd")
        assert r.status_code == 403, (
            f"Expected 403 for path traversal attempt, got {r.status_code}. "
            f"Response: {r.text[:200]}"
        )
        d = r.json()
        assert "error" in d
        assert d["error"] == "Access denied"

    def test_cron_run_log_rejects_absolute_path(self, api, base_url):
        """api/cron-run-log should reject session_id that is an absolute path.

        Passing an absolute path like '/etc/passwd' should be rejected.
        """
        r = get(api, base_url, "/api/cron-run-log?session_id=/etc/passwd")
        assert r.status_code == 403, (
            f"Expected 403 for absolute path attempt, got {r.status_code}. "
            f"Response: {r.text[:200]}"
        )

    def test_cron_run_log_rejects_null_bytes(self, api, base_url):
        """api/cron-run-log should reject session_id with null bytes.

        Null byte injection could bypass extension checks like '.jsonl'.
        """
        r = get(
            api, base_url, "/api/cron-run-log?session_id=../../../etc/passwd%00test"
        )
        assert r.status_code == 403, (
            f"Expected 403 for null byte injection, got {r.status_code}. "
            f"Response: {r.text[:200]}"
        )

    def test_cron_run_log_accepts_normal_session_id(self, api, base_url):
        """api/cron-run-log should accept normal session_ids and return 404.

        A valid session_id format should reach the file-check logic.
        404 means the path was valid but file doesn't exist - that's expected.
        """
        r = get(api, base_url, "/api/cron-run-log?session_id=abc123def456")
        assert r.status_code in (404, 400), (
            f"Expected 404 or 400 for non-existent session, got {r.status_code}. "
            f"Response: {r.text[:200]}"
        )
