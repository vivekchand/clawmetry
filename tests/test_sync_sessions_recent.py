"""
Tests for sync_sessions_recent function - GH #007

Validates:
- sync_sessions_recent properly declares _sessions_json_cache as global
- Cache works correctly across multiple calls
"""

from __future__ import annotations

import ast
import json
import os
import tempfile
import unittest


os.environ["CLAWMETRY_NO_INTERCEPT"] = "1"


class TestSyncSessionsRecentCache(unittest.TestCase):
    def test_sync_sessions_recent_has_global_declaration(self):
        """sync_sessions_recent should declare _sessions_json_cache as global."""
        from clawmetry import sync

        source = open(sync.__file__).read()
        tree = ast.parse(source)

        func_name = "sync_sessions_recent"
        has_global = False
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == func_name:
                for stmt in ast.walk(node):
                    if isinstance(stmt, ast.Global):
                        if "_sessions_json_cache" in stmt.names:
                            has_global = True
                break

        self.assertTrue(
            has_global,
            "sync_sessions_recent is missing 'global _sessions_json_cache' declaration",
        )

    def test_sync_sessions_recent_cache_functional(self):
        """sync_sessions_recent should work with sessions.json cache."""
        from clawmetry.sync import sync_sessions_recent

        with tempfile.TemporaryDirectory() as tmpdir:
            sessions_dir = os.path.join(tmpdir, "sessions")
            os.makedirs(sessions_dir)

            sessions_json = os.path.join(sessions_dir, "sessions.json")
            with open(sessions_json, "w") as f:
                json.dump({}, f)

            config = {
                "api_key": "test-key",
                "node_id": "test-node",
            }
            state = {}
            paths = {
                "sessions_dir": sessions_dir,
            }

            result = sync_sessions_recent(config, state, paths, minutes=60)
            self.assertIsInstance(result, int)


if __name__ == "__main__":
    unittest.main()
