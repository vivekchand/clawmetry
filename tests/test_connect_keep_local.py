"""Regression tests for `clawmetry connect --keep-local` (desktop Self-host).

Bug pinned here (founder live-hit 2026-08-09): the desktop onboarding's
Self-host choice ran `connect --key cm_… --defer-sync`. But --defer-sync only
skips the daemon start — cmd_connect still rode the full cloud rail
(enable_cloud(), family-mark reset) and never wrote the nocloud marker, and
the shell then started `clawmetry sync` itself. Net effect: a machine whose
user explicitly chose "data stays local" pushed snapshots to cloud.

`--keep-local` is the contract the desktop now uses:
  * writes the local-only marker BEFORE any config/daemon work (the daemon
    must never observe a cm_ key without it)
  * never calls enable_cloud()
  * skips the ownership OTP (the key comes from the shell's own OAuth
    loopback — same authenticated provenance as --start-sync-now — and the
    subprocess runs headless, where a prompt would hang onboarding)
  * skips the :8900 dashboard spawn on automated (--key) invocations
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pytest

import clawmetry.cli as cli

REPO_ROOT = Path(__file__).resolve().parents[1]


def _connect_args(**overrides):
    base = dict(
        key="cm_test1234567890",
        enc_key="test-enc-key",
        key_only=False,
        no_daemon=True,
        start_sync_now=False,
        defer_sync=True,
        keep_local=False,
        force=False,
        custom_node_id="test-node",
        foreground=False,
    )
    base.update(overrides)
    return argparse.Namespace(**base)


@pytest.fixture
def keep_local_env(monkeypatch, tmp_path):
    """Neuter network/daemon/disk; record marker + cloud-rail calls."""
    import clawmetry.config as config
    import clawmetry.license as license_mod
    import clawmetry.sync as sync

    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.delenv("CLAWMETRY_API_KEY", raising=False)
    monkeypatch.delenv("CM_KEY", raising=False)

    marker = tmp_path / ".clawmetry" / "nocloud"
    monkeypatch.setattr(config, "NOCLOUD_MARKER_PATH", str(marker))
    monkeypatch.setattr(config, "is_cloud_disabled", lambda: marker.exists())

    enable_calls = []
    monkeypatch.setattr(
        config, "enable_cloud", lambda: enable_calls.append(1) or False
    )
    monkeypatch.setattr(cli, "_stop_existing_daemon", lambda: None)
    monkeypatch.setattr(
        sync, "validate_key", lambda *a, **k: {"node_id": "test-node"}
    )
    monkeypatch.setattr(sync, "save_config", lambda cfg: None)
    monkeypatch.setattr(sync, "_derive_key_for_storage", lambda k: k)
    monkeypatch.setattr(
        license_mod, "auto_provision_pro", lambda *a, **k: (False, "")
    )
    otp_calls = []
    monkeypatch.setattr(
        cli, "_verify_key_ownership", lambda key: otp_calls.append(key)
    )
    dash_calls = []
    monkeypatch.setattr(
        cli, "_ensure_local_dashboard",
        lambda *a, **k: dash_calls.append(1) or True,
    )
    return marker, enable_calls, otp_calls, dash_calls


def test_keep_local_writes_marker_and_skips_cloud_rail(keep_local_env):
    marker, enable_calls, otp_calls, dash_calls = keep_local_env
    cli._cmd_connect(_connect_args(keep_local=True))
    assert marker.exists(), "keep-local must write the nocloud marker"
    assert enable_calls == [], "keep-local must never call enable_cloud()"
    assert otp_calls == [], "OAuth-loopback key needs no second OTP"
    assert dash_calls == [], \
        "automated (--key) keep-local must not spawn a :8900 dashboard"


def test_plain_cloud_connect_still_rides_cloud_rail(keep_local_env):
    marker, enable_calls, otp_calls, dash_calls = keep_local_env
    cli._cmd_connect(_connect_args(start_sync_now=True))
    assert not marker.exists(), "cloud connect must not write the marker"
    assert enable_calls == [1], "cloud connect clears the local-only marker"


def test_connect_parser_and_desktop_wiring():
    """The flag must exist on the connect subparser and the desktop
    Self-host path must pass it (with --defer-sync; the shell starts
    local-only ingest itself)."""
    cli_src = (REPO_ROOT / "clawmetry" / "cli.py").read_text(encoding="utf-8")
    assert '"--keep-local"' in cli_src
    desk_src = (REPO_ROOT / "desktop" / "onboarding.py").read_text(
        encoding="utf-8"
    )
    assert '"--keep-local", "--defer-sync"' in desk_src
    assert '"--defer-sync" if mode == "selfhost"' not in desk_src
