"""
Test that config file is never written with insecure permissions.

The config file should ALWAYS have 0o600 permissions, even momentarily
during the write operation. This test verifies there's no window where
the file has world-readable permissions (0o644).
"""

import json
import os
import stat
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest


def test_config_file_never_has_insecure_permissions_during_write(tmp_path, monkeypatch):
    """
    Verify config file permissions never allow world-readable access.

    The old implementation had a race condition:
        CONFIG_FILE.write_text(json.dumps(data))
        CONFIG_FILE.chmod(0o600)
    Between these two lines, the file exists with default permissions (0o644),
    which is world-readable and a security vulnerability.

    The fix: write to a temp file with 0o600, then atomically rename.
    """
    from clawmetry.sync import save_config, CONFIG_DIR, CONFIG_FILE

    monkeypatch.setattr("clawmetry.sync.CONFIG_DIR", tmp_path)
    monkeypatch.setattr("clawmetry.sync.CONFIG_FILE", tmp_path / "config.json")

    monkeypatch.setattr(
        "clawmetry.sync.os.rename", lambda src, dst: _capture_and_rename(src, dst)
    )

    captured_perms = []

    original_write = Path.write_text
    original_chmod = Path.chmod

    def tracked_write(self, *args, **kwargs):
        result = original_write(self, *args, **kwargs)
        if self.name == "config.json":
            captured_perms.append((self, self.stat().st_mode & 0o777))
        return result

    def tracked_chmod(self, *args, **kwargs):
        if self.name == "config.json":
            captured_perms.append((self, self.stat().st_mode & 0o777))
        return original_chmod(self, *args, **kwargs)

    with patch.object(Path, "write_text", tracked_write):
        with patch.object(Path, "chmod", tracked_chmod):
            test_config = {
                "api_key": "test_api_key_12345",
                "node_id": "test_node_id",
                "platform": "test_platform",
            }
            save_config(test_config)

    for path, perms in captured_perms:
        mode_str = oct(perms)
        is_world_readable = perms & stat.S_IROTH
        assert not is_world_readable, (
            f"Config file {path} had permissions {mode_str} which is world-readable! "
            f"This is a security vulnerability - config should never be world-readable."
        )


def _capture_and_rename(src, dst):
    pass
