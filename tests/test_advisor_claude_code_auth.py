"""_load_anthropic_auth must recognize Claude Code's own OAuth so Dives ride
the default agent harness on standalone Claude Code nodes (live-hit
2026-07-21: node with 150 Claude Code sessions told to export an API key)."""
import json
import os
from unittest.mock import patch

import pytest


@pytest.fixture
def clean_env(monkeypatch, tmp_path):
    for v in ("ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN", "CLAUDE_API_KEY"):
        monkeypatch.delenv(v, raising=False)
    monkeypatch.setenv("HOME", str(tmp_path))
    return tmp_path


def _load():
    from routes.advisor import _load_anthropic_auth
    with patch("routes.advisor._read_anthropic_key_from_openclaw_config",
               return_value=None), \
         patch("shutil.which", return_value="/usr/local/bin/claude"):
        return _load_anthropic_auth()


def test_claude_code_credentials_file_enables_cli_mode(clean_env):
    cc = clean_env / ".claude"
    cc.mkdir()
    (cc / ".credentials.json").write_text('{"claudeAiOauth": {"accessToken": "x"}}')
    mode, cred = _load()
    assert mode == "claude_cli"


def test_claude_code_oauth_marker_enables_cli_mode(clean_env):
    (clean_env / ".claude.json").write_text(json.dumps(
        {"oauthAccount": {"emailAddress": "u@x.test"}}))
    mode, cred = _load()
    assert mode == "claude_cli"


def test_no_auth_anywhere_stays_none(clean_env):
    mode, cred = _load()
    assert mode is None and cred is None
