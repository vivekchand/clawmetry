"""Tests for file handle leaks in sync.py."""

import json
import os
import sys
import tempfile
import warnings
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from clawmetry import sync


class TestFileHandleLeaks(unittest.TestCase):
    """Test that file handles are properly closed using context managers."""

    def _create_test_jsonl(self, tmpdir, filename, events):
        """Create a test JSONL file with given events."""
        filepath = os.path.join(tmpdir, filename)
        with open(filepath, "w") as f:
            for event in events:
                f.write(json.dumps(event) + "\n")
        return filepath

    def test_build_brain_data_no_resource_warning(self):
        """Test _build_brain_data() does not leak file handles."""
        events = [
            {
                "type": "message",
                "timestamp": "2024-01-01T12:00:00",
                "message": {"role": "user", "content": "Hello"},
            },
            {
                "type": "message",
                "timestamp": "2024-01-01T12:00:01",
                "message": {
                    "role": "assistant",
                    "content": "Hi there",
                    "usage": {"input_tokens": 10, "output_tokens": 20},
                },
            },
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            session_file = self._create_test_jsonl(
                tmpdir, "test_session_001.jsonl", events
            )

            with warnings.catch_warnings(record=True) as w:
                warnings.simplefilter("always", ResourceWarning)

                with patch.object(sync, "_get_openclaw_dir", return_value=tmpdir):
                    with patch.object(sync.os.path, "isdir", return_value=True):
                        with patch.object(
                            sync.glob, "glob", return_value=[session_file]
                        ):
                            result = sync._build_brain_data()

                resource_warnings = [
                    x for x in w if issubclass(x.category, ResourceWarning)
                ]
                self.assertEqual(
                    len(resource_warnings),
                    0,
                    f"ResourceWarning raised: {[str(w.message) for w in resource_warnings]}",
                )

    def test_build_tool_stats_no_resource_warning(self):
        """Test _build_tool_stats() does not leak file handles."""
        events = [
            {
                "type": "message",
                "timestamp": "2024-01-01T12:00:00",
                "message": {"role": "user", "content": "Search the web"},
            },
            {
                "type": "message",
                "timestamp": "2024-01-01T12:00:01",
                "message": {
                    "role": "assistant",
                    "content": [
                        {
                            "type": "toolCall",
                            "name": "web_search",
                            "arguments": {"query": "test"},
                        }
                    ],
                },
            },
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            session_file = self._create_test_jsonl(
                tmpdir, "test_session_002.jsonl", events
            )
            sessions_json = os.path.join(tmpdir, "sessions.json")
            with open(sessions_json, "w") as f:
                json.dump(
                    {"test_session_002": {"sessionFile": "test_session_002.jsonl"}}, f
                )

            with warnings.catch_warnings(record=True) as w:
                warnings.simplefilter("always", ResourceWarning)

                with patch.object(sync, "_get_openclaw_dir", return_value=tmpdir):
                    with patch.object(sync.os.path, "isdir", return_value=True):
                        with patch.object(
                            sync.glob, "glob", return_value=[session_file]
                        ):
                            result = sync._build_tool_stats()

                resource_warnings = [
                    x for x in w if issubclass(x.category, ResourceWarning)
                ]
                self.assertEqual(
                    len(resource_warnings),
                    0,
                    f"ResourceWarning raised: {[str(w.message) for w in resource_warnings]}",
                )


if __name__ == "__main__":
    unittest.main()
