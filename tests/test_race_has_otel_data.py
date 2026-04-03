"""Test for race condition in _has_otel_data."""

import threading
import time
import unittest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestHasOtelDataRace(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import dashboard

        cls.dashboard = dashboard
        cls.dashboard.metrics_store.clear()

    @classmethod
    def tearDownClass(cls):
        cls.dashboard.metrics_store.clear()

    def test_has_otel_data_no_race_with_lock(self):
        errors = []
        stop_flag = threading.Event()

        def writer_thread():
            i = 0
            while not stop_flag.is_set():
                try:
                    with self.dashboard._metrics_lock:
                        self.dashboard.metrics_store["tokens"].append(
                            {"timestamp": time.time(), "data": i}
                        )
                        if len(self.dashboard.metrics_store["tokens"]) > 100:
                            self.dashboard.metrics_store["tokens"] = []
                except Exception as e:
                    pass
                i += 1

        def reader_thread():
            while not stop_flag.is_set():
                try:
                    self.dashboard._has_otel_data()
                except Exception as e:
                    errors.append(e)

        writer = threading.Thread(target=writer_thread, daemon=True)
        readers = [
            threading.Thread(target=reader_thread, daemon=True) for _ in range(5)
        ]

        writer.start()
        for r in readers:
            r.start()

        time.sleep(0.5)
        stop_flag.set()

        writer.join(timeout=2)
        for r in readers:
            r.join(timeout=2)

        self.assertEqual(
            errors, [], f"Race condition detected in _has_otel_data: {errors[:3]}"
        )


if __name__ == "__main__":
    unittest.main()
