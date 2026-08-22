"""Tests for #5060: _gateway_log_meta() surfaces logging.level from openclaw.json.

Covers:
- _read_logging_level_config() returns lower-cased level string when present.
- _read_logging_level_config() returns empty string when key is absent.
- _read_logging_level_config() returns empty string on missing / malformed config.
- _gateway_log_meta() propagates gatewayLogLevel when level is configured.
- _gateway_log_meta() omits gatewayLogLevel when level is not configured.
"""
import glob as _glob
import json
import os

import pytest

from clawmetry.adapters.openclaw import (
    _gateway_log_meta,
    _read_logging_level_config,
)


def _write_config(tmp_path, cfg: dict):
    cfg_path = tmp_path / "openclaw.json"
    cfg_path.write_text(json.dumps(cfg))
    return cfg_path


class TestReadLoggingLevelConfig:
    def test_returns_level_lower_cased(self, tmp_path, monkeypatch):
        _write_config(tmp_path, {"logging": {"level": "WARN"}})
        monkeypatch.setenv("OPENCLAW_HOME", str(tmp_path))
        assert _read_logging_level_config() == "warn"

    def test_returns_empty_when_level_absent(self, tmp_path, monkeypatch):
        _write_config(tmp_path, {"logging": {"file": "/tmp/openclaw.log"}})
        monkeypatch.setenv("OPENCLAW_HOME", str(tmp_path))
        assert _read_logging_level_config() == ""

    def test_returns_empty_when_logging_key_absent(self, tmp_path, monkeypatch):
        _write_config(tmp_path, {"other": "key"})
        monkeypatch.setenv("OPENCLAW_HOME", str(tmp_path))
        assert _read_logging_level_config() == ""

    def test_returns_empty_when_config_missing(self, tmp_path, monkeypatch):
        monkeypatch.setenv("OPENCLAW_HOME", str(tmp_path))
        assert _read_logging_level_config() == ""

    def test_returns_empty_on_malformed_json(self, tmp_path, monkeypatch):
        (tmp_path / "openclaw.json").write_text("{not valid json")
        monkeypatch.setenv("OPENCLAW_HOME", str(tmp_path))
        assert _read_logging_level_config() == ""

    def test_info_level(self, tmp_path, monkeypatch):
        _write_config(tmp_path, {"logging": {"level": "info"}})
        monkeypatch.setenv("OPENCLAW_HOME", str(tmp_path))
        assert _read_logging_level_config() == "info"


class TestGatewayLogMetaLevel:
    def _make_log_file(self, tmp_path):
        log_dir = tmp_path / "logs"
        log_dir.mkdir()
        log_file = log_dir / "openclaw-2026-08-22.log"
        log_file.write_text('{"level":"info","msg":"hello"}\n')
        return log_dir

    def test_gateway_log_meta_includes_level_when_configured(
        self, tmp_path, monkeypatch
    ):
        self._make_log_file(tmp_path)
        _write_config(tmp_path, {"logging": {"level": "warn"}})
        monkeypatch.setenv("OPENCLAW_HOME", str(tmp_path))
        monkeypatch.setenv("CLAWMETRY_OPENCLAW_DIR", str(tmp_path))
        result = _gateway_log_meta()
        assert result.get("gatewayLogLevel") == "warn"

    def test_gateway_log_meta_omits_level_when_not_configured(
        self, tmp_path, monkeypatch
    ):
        self._make_log_file(tmp_path)
        _write_config(tmp_path, {"logging": {"file": str(tmp_path / "openclaw.log")}})
        monkeypatch.setenv("OPENCLAW_HOME", str(tmp_path))
        monkeypatch.setenv("CLAWMETRY_OPENCLAW_DIR", str(tmp_path))
        result = _gateway_log_meta()
        assert "gatewayLogLevel" not in result
