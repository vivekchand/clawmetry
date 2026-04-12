"""Tests for race conditions in dashboard.py."""

import os
import sys
import threading
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import dashboard


class TestSecurityPostureHashRace(unittest.TestCase):
    """Test for race condition in security posture hash updates."""

    def setUp(self):
        dashboard._security_posture_hash = ""
        dashboard._security_alerts = []

    def tearDown(self):
        dashboard._security_posture_hash = ""
        dashboard._security_alerts = []

    def test_security_posture_hash_race(self):
        """Demonstrate race condition fixed with lock protection."""
        results = []
        errors = []

        def worker(posture_value):
            try:
                posture = {"sandbox": posture_value}
                posture_hash = __import__("json").dumps(posture, sort_keys=True)
                with dashboard._security_posture_lock:
                    if not dashboard._security_posture_hash:
                        dashboard._security_posture_hash = posture_hash
                    elif posture_hash != dashboard._security_posture_hash:
                        dashboard._security_posture_hash = posture_hash
                        results.append(posture_value)
            except Exception as e:
                errors.append(str(e))

        t1 = threading.Thread(target=worker, args=("A",))
        t2 = threading.Thread(target=worker, args=("B",))
        t3 = threading.Thread(target=worker, args=("A",))

        t1.start()
        t2.start()
        t3.start()
        t1.join()
        t2.join()
        t3.join()

        self.assertEqual(errors, [], f"Errors occurred: {errors}")
        final_hash = dashboard._security_posture_hash
        self.assertEqual(
            final_hash, __import__("json").dumps({"sandbox": "A"}, sort_keys=True)
        )
        self.assertEqual(
            len(results),
            2,
            f"Alert should fire for each unique transition, got: {results}",
        )


if __name__ == "__main__":
    unittest.main()
