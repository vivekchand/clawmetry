"""Tests for AgentReliabilityScorer in history.py."""
import os
import sys
import time
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from history import HistoryDB, AgentReliabilityScorer


class TestAgentReliabilityScorer(unittest.TestCase):

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.tmpdir, 'test_history.db')
        self.db = HistoryDB(self.db_path)
        self.scorer = AgentReliabilityScorer(self.db)

    def tearDown(self):
        try:
            os.remove(self.db_path)
            os.rmdir(self.tmpdir)
        except OSError:
            pass

    def test_insufficient_data_empty(self):
        result = self.scorer.score(window_days=30)
        self.assertEqual(result['direction'], 'insufficient_data')
        self.assertEqual(result['session_count'], 0)
        self.assertEqual(result['points'], [])

    def test_insufficient_data_few_sessions(self):
        now = time.time()
        for i in range(3):
            self.db.insert_session(f'sess-{i}', 100, 50, 0.01, 'claude', 'completed', ts=now - i * 3600)
        result = self.scorer.score(window_days=30, min_sessions=5)
        self.assertEqual(result['direction'], 'insufficient_data')
        self.assertEqual(result['session_count'], 3)

    def test_stable_sessions(self):
        now = time.time()
        for i in range(10):
            self.db.insert_session(f'sess-{i}', 100, 50, 0.01, 'claude', 'completed', ts=now - i * 3600)
        result = self.scorer.score(window_days=30, min_sessions=5)
        self.assertEqual(result['direction'], 'stable')
        self.assertTrue(result['session_count'] >= 5)
        self.assertFalse(result['significant'])
        self.assertEqual(result['degrading_dimensions'], [])

    def test_degrading_sessions(self):
        now = time.time()
        # Early sessions: all completed; later sessions: all errors
        for i in range(20):
            status = 'completed' if i < 10 else 'error'
            self.db.insert_session(f'sess-{i}', 100, 50, 0.01, 'claude', status, ts=now - (20 - i) * 3600)
        result = self.scorer.score(window_days=30, min_sessions=5)
        self.assertEqual(result['direction'], 'degrading')
        self.assertTrue(result['significant'])
        self.assertIn('delivery_score', result['degrading_dimensions'])

    def test_improving_sessions(self):
        now = time.time()
        # Early sessions: errors; later sessions: completed
        for i in range(20):
            status = 'error' if i < 10 else 'completed'
            self.db.insert_session(f'sess-{i}', 100, 50, 0.01, 'claude', status, ts=now - (20 - i) * 3600)
        result = self.scorer.score(window_days=30, min_sessions=5)
        self.assertEqual(result['direction'], 'improving')
        self.assertTrue(result['significant'])

    def test_sparkline_points_capped(self):
        now = time.time()
        for i in range(100):
            self.db.insert_session(f'sess-{i}', 100, 50, 0.01, 'claude', 'completed', ts=now - i * 3600)
        result = self.scorer.score(window_days=30, min_sessions=5)
        # Points capped at 60 for sparkline
        self.assertLessEqual(len(result['points']), 60)

    def test_latest_snapshot_per_session(self):
        now = time.time()
        # Same session key with multiple snapshots
        for i in range(5):
            self.db.insert_session('sess-dup', 100 * (i + 1), 50 * (i + 1), 0.01, 'claude', 'completed', ts=now - (5 - i) * 60)
        # Need at least min_sessions unique keys
        for i in range(5):
            self.db.insert_session(f'sess-{i}', 100, 50, 0.01, 'claude', 'completed', ts=now - i * 3600)
        result = self.scorer.score(window_days=30, min_sessions=5)
        # sess-dup should count as 1 session
        self.assertGreaterEqual(result['session_count'], 5)
        self.assertLessEqual(result['session_count'], 6)

    def test_window_filtering(self):
        now = time.time()
        # Sessions outside window
        for i in range(10):
            self.db.insert_session(f'old-{i}', 100, 50, 0.01, 'claude', 'completed', ts=now - 60 * 86400)
        # Sessions inside 7-day window
        for i in range(6):
            self.db.insert_session(f'new-{i}', 100, 50, 0.01, 'claude', 'completed', ts=now - i * 3600)
        result = self.scorer.score(window_days=7, min_sessions=5)
        self.assertEqual(result['session_count'], 6)
        self.assertEqual(result['window_days'], 7)


if __name__ == '__main__':
    unittest.main()
