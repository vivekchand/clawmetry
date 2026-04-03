"""
Tests for TTL cleanup of _last_cron_runs in HistoryCollector.

GH #XXX: _last_cron_runs grows unboundedly as cron timestamps are never cleaned up.
"""

import time
import pytest
from unittest.mock import MagicMock

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from history import HistoryCollector, CRON_RUN_TTL_SECS


class TestLastCronRunsTTL:
    """Tests for TTL-based cleanup of _last_cron_runs."""

    def test_old_timestamps_cleaned_up_after_ttl(self):
        """Old timestamps (>7 days) should be cleaned from _last_cron_runs."""
        mock_db = MagicMock()
        mock_gw = MagicMock()
        mock_gw.return_value = {"jobs": []}

        collector = HistoryCollector(mock_db, mock_gw)

        job_id = "test_job_456"
        old_ts = time.time() - (8 * 86400)  # 8 days ago (should be cleaned)
        recent_ts = time.time() - 3600  # 1 hour ago (should be kept)

        collector._last_cron_runs[job_id] = {old_ts, recent_ts}

        assert len(collector._last_cron_runs[job_id]) == 2

        mock_gw.return_value = {"jobs": []}
        collector._collect()

        remaining = collector._last_cron_runs.get(job_id, set())
        assert recent_ts in remaining, "Recent timestamp should be kept"
        assert old_ts not in remaining, (
            f"Old timestamp (8 days) should be cleaned, but got: {remaining}"
        )

    def test_ttl_cleanup_preserves_recent_timestamps(self):
        """Only timestamps older than TTL (7 days) should be removed."""
        mock_db = MagicMock()
        mock_gw = MagicMock()
        mock_gw.return_value = {"jobs": []}

        collector = HistoryCollector(mock_db, mock_gw)

        job_id = "test_job_789"
        now = time.time()

        timestamps = {
            now - (1 * 86400),  # 1 day ago - keep
            now - (3 * 86400),  # 3 days ago - keep
            now - (6 * 86400),  # 6 days ago - keep
            now - (8 * 86400),  # 8 days ago - clean
            now - (30 * 86400),  # 30 days ago - clean
        }

        collector._last_cron_runs[job_id] = set(timestamps)

        collector._collect()

        remaining = collector._last_cron_runs.get(job_id, set())

        assert now - (1 * 86400) in remaining
        assert now - (3 * 86400) in remaining
        assert now - (6 * 86400) in remaining
        assert now - (8 * 86400) not in remaining
        assert now - (30 * 86400) not in remaining
        assert len(remaining) == 3

    def test_cleanup_applies_to_all_jobs(self):
        """Cleanup should run for all jobs, not just the ones in current collect."""
        mock_db = MagicMock()
        mock_gw = MagicMock()
        mock_gw.return_value = {"jobs": []}

        collector = HistoryCollector(mock_db, mock_gw)

        old_ts = time.time() - (8 * 86400)
        recent_ts = time.time() - 3600

        collector._last_cron_runs["job1"] = {old_ts, recent_ts}
        collector._last_cron_runs["job2"] = {old_ts, recent_ts}
        collector._last_cron_runs["job3"] = {old_ts, recent_ts}

        collector._collect()

        for job_id in ["job1", "job2", "job3"]:
            assert recent_ts in collector._last_cron_runs[job_id]
            assert old_ts not in collector._last_cron_runs[job_id]
            assert len(collector._last_cron_runs[job_id]) == 1

    def test_empty_jobs_removed_after_cleanup(self):
        """Job entries with only old timestamps should be removed entirely."""
        mock_db = MagicMock()
        mock_gw = MagicMock()
        mock_gw.return_value = {"jobs": []}

        collector = HistoryCollector(mock_db, mock_gw)

        old_ts = time.time() - (8 * 86400)

        collector._last_cron_runs["old_job"] = {old_ts}
        collector._last_cron_runs["mixed_job"] = {old_ts, time.time() - 3600}

        collector._collect()

        assert "old_job" not in collector._last_cron_runs
        assert "mixed_job" in collector._last_cron_runs
        assert len(collector._last_cron_runs["mixed_job"]) == 1

    def test_ttl_constant_is_7_days(self):
        """CRON_RUN_TTL_SECS should be 7 days (604800 seconds)."""
        assert CRON_RUN_TTL_SECS == 7 * 86400

    def test_cleanup_only_runs_once_per_collect(self):
        """Calling _collect multiple times should not cause issues."""
        mock_db = MagicMock()
        mock_gw = MagicMock()
        mock_gw.return_value = {"jobs": []}

        collector = HistoryCollector(mock_db, mock_gw)

        job_id = "test_job"
        recent_ts = time.time() - 3600
        collector._last_cron_runs[job_id] = {recent_ts}

        for _ in range(5):
            collector._collect()

        assert len(collector._last_cron_runs[job_id]) == 1
        assert recent_ts in collector._last_cron_runs[job_id]
