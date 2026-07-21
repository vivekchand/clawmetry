"""Regression tests for save_config on Windows (#windows-connect-crash).

`clawmetry connect` crashed at the very last step on Windows:

    File "clawmetry/sync.py", line 824, in save_config
        os.fchmod(tmp_fd, 0o600)
    AttributeError: module 'os' has no attribute 'fchmod'

os.fchmod is POSIX-only. The user had completed the whole flow (OTP, key
validation, encryption key) and lost it all at the final write. save_config
must succeed on platforms without os.fchmod while keeping the 0o600
tighten-up where the API exists.
"""

import json
import os
import stat
import sys

import pytest

import clawmetry.sync as sync


@pytest.fixture
def config_paths(monkeypatch, tmp_path):
    """Point CONFIG_DIR/CONFIG_FILE at a sandbox so tests never touch ~/.clawmetry."""
    monkeypatch.setattr(sync, "CONFIG_DIR", tmp_path)
    monkeypatch.setattr(sync, "CONFIG_FILE", tmp_path / "config.json")
    return tmp_path / "config.json"


def test_save_config_without_fchmod(monkeypatch, config_paths):
    """Windows has no os.fchmod — save_config must still write the file.

    Simulates Windows on any platform by removing the attribute; on a real
    Windows runner delattr is a no-op and this exercises the genuine path.
    """
    monkeypatch.delattr(os, "fchmod", raising=False)
    sync.save_config({"api_key": "cm_test", "node_id": "win-node"})
    assert json.loads(config_paths.read_text()) == {
        "api_key": "cm_test",
        "node_id": "win-node",
    }


def test_save_config_atomic_no_temp_left_behind(monkeypatch, config_paths):
    """The temp file must be replaced, not orphaned, on the no-fchmod path."""
    monkeypatch.delattr(os, "fchmod", raising=False)
    sync.save_config({"probe": True})
    leftovers = [p for p in config_paths.parent.iterdir() if p.name != "config.json"]
    assert leftovers == []


@pytest.mark.skipif(
    not hasattr(os, "fchmod"), reason="POSIX-only mode check (no fchmod here)"
)
def test_save_config_mode_0600_on_posix(config_paths):
    """Where fchmod exists the config must stay owner-only (0o600)."""
    sync.save_config({"api_key": "cm_test"})
    assert stat.S_IMODE(config_paths.stat().st_mode) == 0o600
