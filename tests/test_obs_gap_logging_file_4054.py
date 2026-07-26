"""Tests for #4054: _gateway_log_files() respects openclaw.json logging.file.

Covers:
- Rotation-pattern file in a custom dir picked up via parent-dir candidate.
- Non-rotation single file returned via direct fallback path.
- Missing / malformed config falls back gracefully without raising.
"""
import json
import os

import pytest

from clawmetry.adapters.openclaw import _gateway_log_files, _read_logging_file_config


def _write_config(tmp_path, log_file_path):
    """Write a minimal openclaw.json pointing logging.file at log_file_path."""
    cfg = {"logging": {"file": str(log_file_path)}}
    cfg_path = tmp_path / "openclaw.json"
    cfg_path.write_text(json.dumps(cfg))
    return cfg_path


class TestReadLoggingFileConfig:
    def test_returns_path_from_config(self, tmp_path, monkeypatch):
        log_path = tmp_path / "custom" / "openclaw.log"
        _write_config(tmp_path, log_path)
        monkeypatch.setenv("OPENCLAW_HOME", str(tmp_path))
        assert _read_logging_file_config() == str(log_path)

    def test_missing_config_returns_empty(self, tmp_path, monkeypatch):
        monkeypatch.setenv("OPENCLAW_HOME", str(tmp_path))
        assert _read_logging_file_config() == ""

    def test_config_without_logging_key_returns_empty(self, tmp_path, monkeypatch):
        (tmp_path / "openclaw.json").write_text(json.dumps({"other": "key"}))
        monkeypatch.setenv("OPENCLAW_HOME", str(tmp_path))
        assert _read_logging_file_config() == ""

    def test_malformed_json_returns_empty(self, tmp_path, monkeypatch):
        (tmp_path / "openclaw.json").write_text("{not valid json")
        monkeypatch.setenv("OPENCLAW_HOME", str(tmp_path))
        assert _read_logging_file_config() == ""


class TestGatewayLogFilesCustomPath:
    def test_rotation_pattern_file_in_custom_dir(self, tmp_path, monkeypatch):
        """logging.file parent dir added to candidates; rotation file found there."""
        custom_dir = tmp_path / "custom_logs"
        custom_dir.mkdir()
        log_file = custom_dir / "openclaw-2026-07-26.log"
        log_file.write_text('{"level":"info","msg":"hello"}\n')

        _write_config(tmp_path, log_file)
        monkeypatch.setenv("OPENCLAW_HOME", str(tmp_path))
        # Prevent default candidates from matching anything real on this host.
        monkeypatch.setenv("CLAWMETRY_OPENCLAW_DIR", str(tmp_path / "nonexistent"))

        result = _gateway_log_files()
        assert str(log_file) in result

    def test_non_rotation_single_file_fallback(self, tmp_path, monkeypatch):
        """logging.file with non-standard name returned directly as fallback."""
        custom_dir = tmp_path / "logs"
        custom_dir.mkdir()
        log_file = custom_dir / "gateway.log"
        log_file.write_text('{"level":"info","msg":"hello"}\n')

        _write_config(tmp_path, log_file)
        monkeypatch.setenv("OPENCLAW_HOME", str(tmp_path))
        monkeypatch.setenv("CLAWMETRY_OPENCLAW_DIR", str(tmp_path / "nonexistent"))

        result = _gateway_log_files()
        assert result == [str(log_file)]

    def test_no_config_returns_empty_when_no_default_dirs(self, tmp_path, monkeypatch):
        """No openclaw.json and no default log dirs → empty list, no exception."""
        monkeypatch.setenv("OPENCLAW_HOME", str(tmp_path))
        monkeypatch.setenv("CLAWMETRY_OPENCLAW_DIR", str(tmp_path / "nonexistent"))
        result = _gateway_log_files()
        assert result == []

    def test_custom_dir_takes_priority_over_defaults(self, tmp_path, monkeypatch):
        """Custom dir inserted at front of candidates, checked before hardcoded dirs."""
        custom_dir = tmp_path / "priority_logs"
        custom_dir.mkdir()
        log_file = custom_dir / "openclaw-2026-07-26.log"
        log_file.write_text('{"level":"info","msg":"custom"}\n')

        # Also create a file in the openclaw_dir/logs default location.
        default_logs = tmp_path / "oc" / "logs"
        default_logs.mkdir(parents=True)
        default_log = default_logs / "openclaw-2026-07-25.log"
        default_log.write_text('{"level":"info","msg":"default"}\n')

        _write_config(tmp_path, log_file)
        monkeypatch.setenv("OPENCLAW_HOME", str(tmp_path))
        monkeypatch.setenv("CLAWMETRY_OPENCLAW_DIR", str(tmp_path / "oc"))

        result = _gateway_log_files()
        # Custom dir is checked first; its file wins.
        assert str(log_file) in result
