"""Sign-out / uninstall must clear the cloudToken mirror and keychain entry.

Bug pinned here (founder report 2026-08-10): the cm_ bearer written into
``~/.openclaw/openclaw.json`` (``clawmetry.cloudToken``) is the FIRST
source ``dashboard._read_cloud_token`` checks, and nothing ever removed
it — not ``clawmetry disconnect``, not ``clawmetry uninstall``, not the
desktop uninstaller. A later install silently re-adopted the old account
identity ("Cloud Connected" + email with zero login).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from clawmetry import config as cm_config  # noqa: E402


def _with_openclaw_config(tmp_path, monkeypatch, payload):
    path = tmp_path / "openclaw.json"
    if payload is not None:
        path.write_text(json.dumps(payload))
    monkeypatch.setattr(cm_config, "OPENCLAW_CONFIG_PATH", str(path))
    return path


def test_clear_cloud_token_removes_only_clawmetry_section(tmp_path, monkeypatch):
    path = _with_openclaw_config(tmp_path, monkeypatch, {
        "clawmetry": {"cloudToken": "cm_deadbeef"},
        "gateway": {"port": 18789},
        "agents": ["main"],
    })
    assert cm_config.clear_cloud_token() is True
    data = json.loads(path.read_text())
    assert "clawmetry" not in data
    # OpenClaw's own keys must survive untouched.
    assert data["gateway"] == {"port": 18789}
    assert data["agents"] == ["main"]


def test_clear_cloud_token_noop_when_no_section(tmp_path, monkeypatch):
    path = _with_openclaw_config(tmp_path, monkeypatch, {"gateway": {}})
    assert cm_config.clear_cloud_token() is False
    assert json.loads(path.read_text()) == {"gateway": {}}


def test_clear_cloud_token_noop_when_file_missing(tmp_path, monkeypatch):
    _with_openclaw_config(tmp_path, monkeypatch, None)
    assert cm_config.clear_cloud_token() is False


def test_clear_cloud_token_never_raises_on_garbage(tmp_path, monkeypatch):
    path = _with_openclaw_config(tmp_path, monkeypatch, None)
    path.write_text("{not json")
    assert cm_config.clear_cloud_token() is False
    # The unparseable file is left alone (it belongs to OpenClaw).
    assert path.read_text() == "{not json"


def test_delete_workspace_keychain_entry_is_best_effort():
    # Empty node_id → nothing to look up; must not raise even when the
    # keyring package is missing entirely.
    assert cm_config.delete_workspace_keychain_entry("") is False
    assert cm_config.delete_workspace_keychain_entry("node-without-entry") in (
        True,
        False,
    )


def test_disconnect_and_uninstall_clear_the_mirror():
    """The CLI sign-out paths must call the cleanup helpers — presence
    check on source (the flows themselves stop daemons/talk to launchd,
    which CI can't exercise)."""
    cli_src = (REPO_ROOT / "clawmetry" / "cli.py").read_text(encoding="utf-8")
    disconnect = cli_src.split("def _cmd_disconnect", 1)[1].split("\ndef ", 1)[0]
    assert "clear_cloud_token" in disconnect
    assert "delete_workspace_keychain_entry" in disconnect
    uninstall = cli_src.split("def _cmd_uninstall", 1)[1].split("\ndef _cmd_", 1)[0]
    assert "clear_cloud_token" in uninstall
    assert "delete_workspace_keychain_entry" in uninstall
    # ClawMetry-owned files inside the OpenClaw home go too — but never
    # the OpenClaw home itself.
    assert '".openclaw"' in uninstall or ".openclaw" in uninstall
    assert "clawmetry.db" in uninstall
