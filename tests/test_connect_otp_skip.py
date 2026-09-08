"""Regression tests for the connect ownership-OTP gate (#onboarding-friction).

`clawmetry connect --key cm_xxx --start-sync-now` is the command the cloud
dashboard tells a freshly authenticated user to paste. That key was minted in
an OTP-verified web session, so the CLI must NOT demand a second OTP on this
path. A bare `--key` connect (key from anywhere else) still verifies.
"""

import argparse

import pytest

import clawmetry.cli as cli


def _connect_args(**overrides):
    base = dict(
        key="cm_test1234567890",
        enc_key="test-enc-key",
        key_only=False,
        no_daemon=True,
        start_sync_now=False,
        defer_sync=False,
        force=False,
        custom_node_id="test-node",
        foreground=False,
    )
    base.update(overrides)
    return argparse.Namespace(**base)


@pytest.fixture
def connect_env(monkeypatch, tmp_path):
    """Neuter everything in _cmd_connect that touches network/daemon/disk."""
    import clawmetry.sync as sync
    import clawmetry.config as config
    import clawmetry.license as license_mod

    monkeypatch.setenv("HOME", str(tmp_path))  # no pre-existing saved config
    monkeypatch.delenv("CLAWMETRY_API_KEY", raising=False)
    monkeypatch.delenv("CM_KEY", raising=False)

    monkeypatch.setattr(config, "is_cloud_disabled", lambda: False)
    monkeypatch.setattr(config, "enable_cloud", lambda: False)
    monkeypatch.setattr(cli, "_stop_existing_daemon", lambda: None)
    monkeypatch.setattr(
        sync, "validate_key", lambda *a, **k: {"node_id": "test-node"}
    )
    monkeypatch.setattr(sync, "save_config", lambda cfg: None)
    monkeypatch.setattr(sync, "_derive_key_for_storage", lambda k: k)
    monkeypatch.setattr(
        license_mod, "auto_provision_pro", lambda *a, **k: (False, "")
    )

    calls = []
    monkeypatch.setattr(
        cli, "_verify_key_ownership", lambda key: calls.append(key)
    )
    return calls


def test_start_sync_now_skips_ownership_otp(connect_env):
    cli._cmd_connect(_connect_args(start_sync_now=True))
    assert connect_env == []


def test_defer_sync_skips_ownership_otp(connect_env):
    """The desktop onboarding's self-host path runs
    `connect --key cm_… --defer-sync` non-interactively (no stdin). The key
    was just minted by the pane's own OAuth/OTP flow, so a second OTP is not
    only friction — without a tty _verify_key_ownership exits 1, the trial
    never provisions, and the self-host user lands on OSS with every runtime
    locked (2026-08-09 lab-machine regression)."""
    cli._cmd_connect(_connect_args(defer_sync=True))
    assert connect_env == []


def test_keep_local_skips_otp_and_never_reenables_cloud(
    connect_env, monkeypatch, tmp_path
):
    """`connect --key cm_… --keep-local --defer-sync` is the desktop app's
    Self-Hosted onboarding command. It must (a) skip the ownership OTP
    (non-interactive subprocess), (b) leave the nocloud marker in place, and
    (c) never call enable_cloud — signing in must not switch a self-host
    install to cloud sync."""
    import clawmetry.config as config

    marker = tmp_path / "nocloud"
    marker.write_text("")
    monkeypatch.setattr(config, "NOCLOUD_MARKER_PATH", str(marker))
    enable_calls = []
    monkeypatch.setattr(
        config, "enable_cloud", lambda: enable_calls.append(True)
    )
    monkeypatch.setattr(cli, "_activate_signup_trial", lambda: False)

    cli._cmd_connect(_connect_args(keep_local=True, defer_sync=True))

    assert connect_env == []
    assert marker.exists()
    assert enable_calls == []


def test_plain_key_connect_still_asks_otp(connect_env):
    cli._cmd_connect(_connect_args(start_sync_now=False))
    assert connect_env == ["cm_test1234567890"]


def test_reconnect_with_saved_key_skips_otp(connect_env, tmp_path):
    import json

    cfg_dir = tmp_path / ".clawmetry"
    cfg_dir.mkdir()
    (cfg_dir / "config.json").write_text(
        json.dumps({"api_key": "cm_test1234567890", "node_id": "test-node"})
    )
    cli._cmd_connect(_connect_args(start_sync_now=False))
    assert connect_env == []
