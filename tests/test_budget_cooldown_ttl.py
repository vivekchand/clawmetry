"""Tests for budget alert cooldown memory leak fix."""

import os
import sys
import time
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import dashboard


class TestBudgetAlertCooldowns(unittest.TestCase):
    """Test that _budget_alert_cooldowns is properly bounded."""

    def setUp(self):
        dashboard._budget_alert_cooldowns = {}

    def test_cooldowns_bounded_via_cleanup(self):
        """Test that cooldown cleanup prevents unbounded growth."""
        now = time.time()
        dashboard._budget_alert_cooldowns = {}

        for i in range(100):
            rule_id = f"unique_rule_{i}_{now}"
            dashboard._budget_alert_cooldowns[rule_id] = now - 4000

        dashboard._expire_budget_cooldowns()

        final_size = len(dashboard._budget_alert_cooldowns)
        self.assertEqual(final_size, 0, "Old entries should be cleaned up by TTL")

    def test_cooldowns_ttl_cleanup(self):
        """Test that old cooldown entries are cleaned up based on TTL."""
        now = time.time()
        old_timestamp = now - 4000
        dashboard._budget_alert_cooldowns["old_rule_1"] = old_timestamp
        dashboard._budget_alert_cooldowns["old_rule_2"] = old_timestamp
        dashboard._budget_alert_cooldowns["recent_rule"] = now

        dashboard._expire_budget_cooldowns()

        remaining = dashboard._budget_alert_cooldowns
        self.assertNotIn(
            "old_rule_1", remaining, "Old entries should be cleaned up by TTL"
        )
        self.assertNotIn(
            "old_rule_2", remaining, "Old entries should be cleaned up by TTL"
        )
        self.assertIn(
            "recent_rule", remaining, "Recent entries should not be cleaned up"
        )

    def test_fire_alert_cleans_old_entries(self):
        """Test that _fire_alert cleans up old cooldown entries."""
        dashboard._budget_alert_cooldowns = {}

        old_rule_id = f"old_rule_{time.time() - 4000}"
        dashboard._budget_alert_cooldowns[old_rule_id] = time.time() - 4000

        self.assertIn(old_rule_id, dashboard._budget_alert_cooldowns)

        try:
            dashboard._fire_alert("new_rule_id", "test", "test message", channels=[])
        except Exception:
            pass

        self.assertNotIn(
            old_rule_id,
            dashboard._budget_alert_cooldowns,
            "Old entries should be cleaned when _fire_alert is called",
        )


if __name__ == "__main__":
    unittest.main()
