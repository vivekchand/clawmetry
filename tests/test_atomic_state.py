"""Tests for atomic state writes in sync.py."""

import os
import sys
import json
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestAtomicStateWrite(unittest.TestCase):
    """Test that save_state uses atomic write (temp file + rename)."""

    def test_atomic_write_uses_temp_file_and_rename(self):
        """Verify save_state writes to temp file then renames."""
        from clawmetry import sync

        with tempfile.TemporaryDirectory() as tmpdir:
            state_file = os.path.join(tmpdir, "sync-state.json")
            tmp_state_file = os.path.join(tmpdir, "sync-state.tmp")

            with patch.object(sync, "STATE_FILE", sync.Path(state_file)):
                with patch.object(sync, "CONFIG_DIR", sync.Path(tmpdir)):
                    sync.save_state({"last_event_ids": {"x": 999}, "last_sync": 2000})

            self.assertTrue(os.path.exists(state_file))
            self.assertFalse(os.path.exists(tmp_state_file))

            with open(state_file) as f:
                data = json.load(f)
            self.assertEqual(data["last_event_ids"]["x"], 999)
            self.assertEqual(data["last_sync"], 2000)

    def test_atomic_write_preserves_state_on_failed_rename(self):
        """Verify old state is preserved when rename fails."""
        from clawmetry import sync

        with tempfile.TemporaryDirectory() as tmpdir:
            state_file = os.path.join(tmpdir, "sync-state.json")

            original_state = {
                "last_event_ids": {"a": 1},
                "last_sync": 1000,
                "last_log_offsets": {},
            }
            with open(state_file, "w") as f:
                json.dump(original_state, f)

            original_rename = os.rename

            def failing_rename(src, dst):
                if ".tmp" in str(src):
                    raise OSError("Simulated disk full during rename")
                return original_rename(src, dst)

            with patch.object(sync, "STATE_FILE", sync.Path(state_file)):
                with patch.object(sync, "CONFIG_DIR", sync.Path(tmpdir)):
                    with patch("os.rename", failing_rename):
                        try:
                            sync.save_state(
                                {"last_event_ids": {"x": 999}, "last_sync": 2000}
                            )
                        except OSError:
                            pass

            with open(state_file) as f:
                data = json.load(f)

            self.assertEqual(data["last_event_ids"]["a"], 1)
            self.assertEqual(data["last_sync"], 1000)


if __name__ == "__main__":
    unittest.main()
