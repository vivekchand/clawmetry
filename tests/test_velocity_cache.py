"""Tests for _velocity_cache race condition."""

import os
import sys
import threading
import time
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import dashboard


class TestVelocityCacheRace:
    """Test that _velocity_cache is accessed with proper locking."""

    def setup_method(self):
        dashboard._velocity_cache = {"ts": 0, "result": None, "mtimes": {}}

    def test_concurrent_access_no_crash(self):
        """Multiple threads calling _compute_velocity_status concurrently should not crash."""
        errors = []

        def call_velocity():
            try:
                for _ in range(10):
                    dashboard._compute_velocity_status()
                    time.sleep(0.001)
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=call_velocity) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0, f"Errors during concurrent access: {errors}"

    def test_cache_write_protected(self):
        """The cache should be properly protected by a lock during read-modify-write."""
        lock_exists = hasattr(dashboard, "_velocity_lock")
        assert lock_exists, "_velocity_lock should exist to protect _velocity_cache"

    def test_cache_result_persists(self):
        """After computing, the result should be stored in the cache."""
        dashboard._velocity_cache = {"ts": 0, "result": None, "mtimes": {}}
        result = dashboard._compute_velocity_status()
        assert dashboard._velocity_cache["result"] is not None, (
            "Cache should store computed result"
        )
        assert dashboard._velocity_cache["ts"] > 0, "Cache timestamp should be set"
