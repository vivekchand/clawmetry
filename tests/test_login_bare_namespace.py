"""Regression test: `clawmetry login` with no saved account must not crash.

The `login` subparser defines only --force, but _cmd_login delegates to
_cmd_connect, which historically read `args.key` directly and blew up with
`AttributeError: 'Namespace' object has no attribute 'key'` for any
not-yet-logged-in user. _cmd_connect must treat every connect-only flag as
optional (getattr with a default), because login/onboard paths hand it a
Namespace that never saw the connect parser.
"""

import argparse

import pytest

import clawmetry.cli as cli


def _login_args():
    # Exactly what argparse produces for `clawmetry login`: cmd + --force only.
    return argparse.Namespace(cmd="login", force=False)


@pytest.fixture
def login_env(monkeypatch, tmp_path):
    """Neuter everything in _cmd_connect that touches network/daemon/disk."""
    import webbrowser

    import clawmetry.config as config
    import clawmetry.license as license_mod
    import clawmetry.sync as sync

    monkeypatch.setenv("HOME", str(tmp_path))  # no pre-existing saved config
    monkeypatch.delenv("CLAWMETRY_API_KEY", raising=False)
    monkeypatch.delenv("CM_KEY", raising=False)

    monkeypatch.setattr(config, "is_cloud_disabled", lambda: False)
    monkeypatch.setattr(config, "enable_cloud", lambda: False)
    monkeypatch.setattr(
        cli, "_get_api_key_interactive", lambda: "cm_test1234567890"
    )
    # _cmd_connect's nested _input() opens /dev/tty when stdin isn't a tty
    # (would hang the test run) — pretend stdin is a tty and stub input().
    class _FakeTTYStdin:
        def isatty(self):
            return True

    monkeypatch.setattr("sys.stdin", _FakeTTYStdin())
    monkeypatch.setattr("builtins.input", lambda *a, **k: "")
    monkeypatch.setattr(cli, "_keychain_get", lambda node_id: "")
    monkeypatch.setattr(cli, "_keychain_set", lambda node_id, key: None)
    monkeypatch.setattr(cli, "_reset_family_sync_marks", lambda: 0)
    monkeypatch.setattr(cli, "_activate_signup_trial", lambda: None)
    monkeypatch.setattr(cli, "_stop_existing_daemon", lambda: None)
    monkeypatch.setattr(cli, "_start_daemon", lambda config, args: None)
    monkeypatch.setattr(cli, "_ensure_local_dashboard", lambda: False)
    monkeypatch.setattr(cli, "_warn_if_placeholder_account", lambda key: None)
    monkeypatch.setattr(
        sync, "validate_key", lambda *a, **k: {"node_id": "test-node"}
    )
    monkeypatch.setattr(sync, "save_config", lambda cfg: None)
    monkeypatch.setattr(sync, "_derive_key_for_storage", lambda k: k)
    monkeypatch.setattr(
        license_mod, "auto_provision_pro", lambda *a, **k: (False, "")
    )
    monkeypatch.setattr(webbrowser, "open", lambda *a, **k: True)


def test_login_bare_namespace_reaches_connect(login_env):
    # Would raise AttributeError('key') before the getattr fix.
    cli._cmd_login(_login_args())


def test_connect_tolerates_namespace_without_key(login_env):
    # Same guarantee for any other caller handing over a partial Namespace.
    cli._cmd_connect(argparse.Namespace(force=False))
