"""
Tests for HistoryDB connection management.
"""

import os
import tempfile
import threading
import pytest

from history import HistoryDB


class TestHistoryDBConnections:
    """Test SQLite connection lifecycle management."""

    def test_close_method_exists(self):
        """Test that HistoryDB has a close() method."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            db = HistoryDB(db_path)
            assert hasattr(db, "close"), "HistoryDB should have a close() method"

    def test_context_manager_support(self):
        """Test that HistoryDB supports context manager protocol."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            with HistoryDB(db_path) as db:
                db.insert_metric("context_metric", 42)

    def test_close_clears_connection(self):
        """Test that close() properly clears the thread-local connection."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test_close.db")
            db = HistoryDB(db_path)
            db.insert_metric("test_metric", 1)
            assert hasattr(db._local, "conn"), "Connection should exist after insert"
            assert db._local.conn is not None, "Connection should not be None"
            db.close()
            assert db._local.conn is None, "Connection should be None after close()"

    def test_multiple_threads_with_close(self):
        """Test that close() works properly for connections in different threads."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test_threads.db")

            def worker(db):
                db.insert_metric("thread_metric", 1)
                db.close()

            threads = []
            for i in range(3):
                t = threading.Thread(target=worker, args=(HistoryDB(db_path),))
                t.start()
                threads.append(t)

            for t in threads:
                t.join()
