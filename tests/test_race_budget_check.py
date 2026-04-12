"""
Test for race condition: budget_check called outside lock in _add_metric.

This test demonstrates that _budget_check() is invoked after the lock is released
in _add_metric(), creating a race condition window where metrics_store can be
modified by another thread before the budget check runs.

GH #013 - Budget Check Outside Lock
"""

import os
import sys
import threading
import time
import unittest

os.environ["CLAWMETRY_NO_INTERCEPT"] = "1"

import dashboard


class TestBudgetCheckRaceCondition(unittest.TestCase):
    """Test that budget_check is called INSIDE the metrics lock, not outside."""

    def setUp(self):
        dashboard.metrics_store = {
            "tokens": [],
            "cost": [],
            "runs": [],
            "messages": [],
            "webhooks": [],
            "queues": [],
        }
        dashboard._budget_paused = False
        dashboard._budget_alert_cooldowns = {}

    def test_concurrent_add_metrics_budget_check(self):
        """
        Test that concurrent _add_metric calls don't cause race condition.

        With the bug: budget_check can be called when another thread holds the lock.
        After fix: budget_check should always see consistent state inside lock.
        """
        lock_state_during_budget_check = []
        add_count = 10
        barrier = threading.Barrier(add_count + 1)

        original_budget_check = dashboard._budget_check

        def tracking_budget_check():
            is_locked = dashboard._metrics_lock.locked()
            lock_state_during_budget_check.append(is_locked)
            return original_budget_check()

        dashboard._budget_check = tracking_budget_check

        def worker():
            barrier.wait()
            try:
                dashboard._add_metric("cost", {"timestamp": time.time(), "usd": 0.01})
            except Exception:
                pass

        threads = [
            threading.Thread(target=worker, name=f"worker-{i}")
            for i in range(add_count)
        ]

        for t in threads:
            t.start()

        barrier.wait()

        for t in threads:
            t.join()

        unlocked_calls = [x for x in lock_state_during_budget_check if not x]
        self.assertEqual(
            len(unlocked_calls),
            0,
            f"budget_check was called {len(unlocked_calls)} times WITHOUT lock held. "
            "This is the race condition!",
        )


if __name__ == "__main__":
    unittest.main()
