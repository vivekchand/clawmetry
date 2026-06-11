"""Guards for the OSS hardening batch.

- #1572 interceptor: never force-read a streaming response (would consume the
  caller's stream); write the sidecar into ~/.clawmetry, not the agent's
  ~/.openclaw workspace (read-only contract).
- #1577 config.json (api_key + encryption_key) is created 0600 atomically, with
  no brief world-readable window.
"""
import importlib
import os
import stat
from pathlib import Path

import pytest

interceptor = importlib.import_module("clawmetry.interceptor")
sync = importlib.import_module("clawmetry.sync")


# ── interceptor ────────────────────────────────────────────────────────────

def test_output_file_is_in_clawmetry_dir_not_openclaw(monkeypatch):
    monkeypatch.delenv("CLAWMETRY_HOME", raising=False)
    p = str(interceptor._get_output_file())
    assert ".clawmetry" in p
    assert ".openclaw" not in p


def test_no_forced_stream_read_in_body_capture():
    src = Path(interceptor.__file__).read_text()
    # The agent-breaking forced reads must be gone...
    assert "response.read()" not in src
    assert "await response.read()" not in src
    # ...replaced by a stream-kwarg guard at all three capture sites.
    assert src.count('if not kwargs.get("stream", False):') >= 3


# ── config.json atomic 0600 ────────────────────────────────────────────────

def test_save_config_is_0600(tmp_path, monkeypatch):
    cfg = tmp_path / "config.json"
    monkeypatch.setattr(sync, "CONFIG_DIR", tmp_path, raising=False)
    monkeypatch.setattr(sync, "CONFIG_FILE", cfg, raising=False)
    sync.save_config({"api_key": "cm_secret", "encryption_key": "k"})
    assert cfg.exists()
    mode = stat.S_IMODE(cfg.stat().st_mode)
    assert mode == 0o600, oct(mode)
    import json
    assert json.loads(cfg.read_text())["api_key"] == "cm_secret"
    # no leftover temp files
    assert not list(tmp_path.glob("config.json.tmp*"))
