"""
`clawmetry login` + `--turn-on-cloud-sync` / `--turn-off-cloud-sync` tests.

The toggles are a pure flip of the ~/.clawmetry/nocloud marker — the daemon
checks is_cloud_disabled() on every cloud POST, so no restart is involved.
OFF must keep the account key (only `disconnect` removes it). The help text
must advertise all of it (explicit product requirement).
"""
from __future__ import annotations

import sys

import pytest

from clawmetry import cli
from clawmetry import config as cm_config


@pytest.fixture()
def marker(tmp_path, monkeypatch):
    path = tmp_path / "nocloud"
    monkeypatch.setattr(cm_config, "NOCLOUD_MARKER_PATH", str(path))
    monkeypatch.delenv("CLAWMETRY_NO_CLOUD", raising=False)
    monkeypatch.setenv("HOME", str(tmp_path))  # isolate ~/.clawmetry reads
    return path


def test_turn_off_creates_marker_and_keeps_config(marker, tmp_path, capsys):
    cfg = tmp_path / ".clawmetry" / "config.json"
    cfg.parent.mkdir(parents=True)
    cfg.write_text('{"api_key": "cm_test", "node_id": "n1"}')
    rc = cli._cmd_cloud_toggle(False)
    assert rc == 0
    assert marker.is_file()
    assert cm_config.is_cloud_disabled()
    # the login/key must survive the toggle (that's the disconnect difference)
    assert "cm_test" in cfg.read_text()
    out = capsys.readouterr().out
    assert "OFF" in out
    assert "--turn-on-cloud-sync" in out


def test_turn_on_removes_marker(marker, tmp_path, capsys):
    marker.write_text("x")
    cfg = tmp_path / ".clawmetry" / "config.json"
    cfg.parent.mkdir(parents=True)
    cfg.write_text('{"api_key": "cm_test"}')
    rc = cli._cmd_cloud_toggle(True)
    assert rc == 0
    assert not marker.exists()
    assert not cm_config.is_cloud_disabled()
    assert "ON" in capsys.readouterr().out


def test_turn_on_without_login_points_to_login(marker, capsys):
    marker.write_text("x")
    rc = cli._cmd_cloud_toggle(True)
    assert rc == 0
    assert not marker.exists()
    assert "clawmetry login" in capsys.readouterr().out


def test_turn_on_warns_when_env_forces_local(marker, monkeypatch, capsys):
    monkeypatch.setenv("CLAWMETRY_NO_CLOUD", "1")
    rc = cli._cmd_cloud_toggle(True)
    assert rc == 1
    assert "CLAWMETRY_NO_CLOUD" in capsys.readouterr().out


def test_toggle_flags_dispatch_from_main(marker, monkeypatch):
    monkeypatch.setattr(sys, "argv", ["clawmetry", "--turn-off-cloud-sync"])
    with pytest.raises(SystemExit) as e:
        cli.main()
    assert e.value.code == 0
    assert marker.is_file()
    monkeypatch.setattr(sys, "argv", ["clawmetry", "--turn-on-cloud-sync"])
    with pytest.raises(SystemExit) as e:
        cli.main()
    assert e.value.code == 0
    assert not marker.exists()


def test_login_subcommand_registered(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["clawmetry", "login", "--help"])
    with pytest.raises(SystemExit) as e:
        cli.main()
    assert e.value.code == 0
    out = capsys.readouterr().out.lower()
    assert "usage: clawmetry login" in out
    assert "signup" in out


def test_help_text_advertises_cloud_commands():
    import dashboard

    for token in (
        "login",
        "connect",
        "disconnect",
        "doctor",
        "--turn-on-cloud-sync",
        "--turn-off-cloud-sync",
    ):
        assert token in dashboard.HELP_TEXT, token
