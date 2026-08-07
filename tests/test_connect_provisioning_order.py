"""Regression test for the pro-provisioning ordering bug.

`_cmd_connect` used to probe `/api/license/entitlement` (via
`auto_provision_pro`) BEFORE minting the account's trial license (via
`_activate_signup_trial`). On a brand-new signup the account is still FREE
at probe time, so the probe silently found nothing to install and the trial
activation moments later never re-triggered it -- `clawmetry status` showed
a live trial while `Runtimes: ... NOT syncing` persisted until the 30-min
watcher in sync.py eventually caught up (2026-08-06, Straive Windows
onboarding). This pins the fix: the trial must activate first, and
`auto_provision_pro` must run afterward so it sees the freshly-minted
entitlement in the same `connect` call.
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
        start_sync_now=True,  # skip the ownership-OTP prompt, not under test here
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

    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.delenv("CLAWMETRY_API_KEY", raising=False)
    monkeypatch.delenv("CM_KEY", raising=False)

    monkeypatch.setattr(config, "is_cloud_disabled", lambda: False)
    monkeypatch.setattr(config, "enable_cloud", lambda: False)
    monkeypatch.setattr(cli, "_stop_existing_daemon", lambda: None)
    monkeypatch.setattr(sync, "validate_key", lambda *a, **k: {"node_id": "test-node"})
    monkeypatch.setattr(sync, "save_config", lambda cfg: None)
    monkeypatch.setattr(sync, "_derive_key_for_storage", lambda k: k)
    monkeypatch.setattr(cli, "_verify_key_ownership", lambda key: None)


def test_trial_activates_before_pro_is_probed(connect_env, monkeypatch, capsys):
    """The freshly-minted trial must be visible to `auto_provision_pro` -- i.e.
    `_activate_signup_trial` must run to completion first."""
    order = []

    def _fake_activate_trial():
        order.append("trial")
        return True

    def _fake_auto_provision(api_key, node_id):
        order.append("provision")
        # A correct ordering means the trial is ALREADY active by the time
        # this probes entitlement -- assert that, not just call order, so a
        # future refactor that reorders the calls but drops the return-value
        # dependency still fails loudly.
        assert order == ["trial", "provision"]
        return True, ""

    monkeypatch.setattr(cli, "_activate_signup_trial", _fake_activate_trial)
    import clawmetry.license as license_mod
    monkeypatch.setattr(license_mod, "auto_provision_pro", _fake_auto_provision)

    cli._cmd_connect(_connect_args())

    assert order == ["trial", "provision"]


def test_pro_still_empty_after_trial_prints_activating_hint(connect_env, monkeypatch, capsys):
    """If provisioning still comes back empty-handed right after a successful
    trial activation, the terminal must say SOMETHING instead of nothing --
    this is what made Straive's onboarding look like it silently failed."""
    monkeypatch.setattr(cli, "_activate_signup_trial", lambda: True)
    import clawmetry.license as license_mod
    monkeypatch.setattr(license_mod, "auto_provision_pro", lambda *a, **k: (False, ""))

    cli._cmd_connect(_connect_args())

    out = capsys.readouterr().out
    assert "activating" in out.lower()


def test_pro_provision_error_message_still_surfaces(connect_env, monkeypatch, capsys):
    """An explicit provisioning message (e.g. a real install failure) must
    still win over the generic "activating" hint."""
    monkeypatch.setattr(cli, "_activate_signup_trial", lambda: True)
    import clawmetry.license as license_mod
    monkeypatch.setattr(
        license_mod, "auto_provision_pro",
        lambda *a, **k: (False, "clawmetry-pro install failed: boom"),
    )

    cli._cmd_connect(_connect_args())

    out = capsys.readouterr().out
    assert "boom" in out
    assert "activating" not in out.lower()
