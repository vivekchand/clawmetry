"""The desktop shell's auto-upgrade must honor the daemon's update policy.

Bug pinned here: desktop/app.py's watcher shelled a plain `clawmetry update`
(a bare pip upgrade that ignores CLAWMETRY_AUTOUPDATE_MIN_AGE_HOURS and
CLAWMETRY_AUTO_UPDATE) and its own kill-switch pre-check compared the env
var to the literal string "0" only, missing false/no/off and the implicit
CI disable that routes/update_check.py::_env_auto_update_disabled applies.
Now the shell passes --unattended (the CLI applies the daemon policy) and
the pre-check mirrors the daemon's parser exactly.
"""
from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

import desktop.app as dapp  # noqa: E402
import routes.update_check as uc  # noqa: E402


# ── kill-switch parsing parity with the daemon ───────────────────────────────

@pytest.mark.parametrize("val", ["0", "false", "no", "off", "FALSE", " Off "])
def test_explicit_falsy_disables(monkeypatch, val):
    monkeypatch.setenv("CLAWMETRY_AUTO_UPDATE", val)
    assert dapp._auto_update_disabled() is True


@pytest.mark.parametrize("val", ["1", "true", "yes", "on", "TRUE"])
def test_explicit_truthy_rearms_even_in_ci(monkeypatch, val):
    monkeypatch.setenv("CLAWMETRY_AUTO_UPDATE", val)
    monkeypatch.setenv("CI", "true")
    assert dapp._auto_update_disabled() is False


def test_ci_implicitly_disables_when_unset(monkeypatch):
    monkeypatch.delenv("CLAWMETRY_AUTO_UPDATE", raising=False)
    monkeypatch.setenv("CI", "true")
    assert dapp._auto_update_disabled() is True


def test_enabled_by_default_outside_ci(monkeypatch):
    monkeypatch.delenv("CLAWMETRY_AUTO_UPDATE", raising=False)
    monkeypatch.delenv("CI", raising=False)
    assert dapp._auto_update_disabled() is False


@pytest.mark.parametrize("auto_update", ["", "0", "1", "false", "no", "off",
                                         "true", "yes", "on", "garbage"])
@pytest.mark.parametrize("ci", ["", "0", "false", "true", "1"])
def test_parity_with_daemon_parser(monkeypatch, auto_update, ci):
    """Drift guard: the shell's duplicated parser must agree with
    routes/update_check.py::_env_auto_update_disabled for every combo."""
    if auto_update:
        monkeypatch.setenv("CLAWMETRY_AUTO_UPDATE", auto_update)
    else:
        monkeypatch.delenv("CLAWMETRY_AUTO_UPDATE", raising=False)
    if ci:
        monkeypatch.setenv("CI", ci)
    else:
        monkeypatch.delenv("CI", raising=False)
    assert dapp._auto_update_disabled() == uc._env_auto_update_disabled()


# ── the watcher's upgrade shell-out ──────────────────────────────────────────

def _stub_shell(tmp_path):
    cli = tmp_path / "clawmetry"
    cli.write_text("stub")
    stub = SimpleNamespace(
        logs=[], upgraded=[],
    )
    stub._log = stub.logs.append
    stub._venv_clawmetry = lambda: cli
    stub._get_installed_version = lambda: "0.12.999"
    stub._mark_upgraded = stub.upgraded.append
    return stub, cli


def test_upgrade_passes_unattended_flag(monkeypatch, tmp_path):
    monkeypatch.setenv("CLAWMETRY_AUTO_UPDATE", "1")
    stub, cli = _stub_shell(tmp_path)
    calls = []

    def _fake_run(cmd, **kw):
        calls.append(cmd)
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr(dapp.subprocess, "run", _fake_run)
    dapp.RuntimeSupervisor._background_pip_upgrade(stub)
    assert calls == [[str(cli), "update", "--unattended"]]
    assert stub.upgraded == ["0.12.999"]


def test_kill_switch_skips_shell_out_entirely(monkeypatch, tmp_path):
    monkeypatch.setenv("CLAWMETRY_AUTO_UPDATE", "no")  # not just "0"
    stub, _cli = _stub_shell(tmp_path)

    def _boom(cmd, **kw):
        raise AssertionError("must not shell out when the kill switch is on")

    monkeypatch.setattr(dapp.subprocess, "run", _boom)
    dapp.RuntimeSupervisor._background_pip_upgrade(stub)
    assert any("disabled" in line for line in stub.logs)


def test_pre_unattended_venv_falls_back_to_plain_update_once(monkeypatch, tmp_path):
    """Bootstrap: a venv still running a clawmetry from before the flag
    existed rejects --unattended (argparse rc=2). The shell must retry a
    plain update once so the venv can reach a version that understands the
    policy flag, instead of failing on every cycle forever."""
    monkeypatch.setenv("CLAWMETRY_AUTO_UPDATE", "1")
    stub, cli = _stub_shell(tmp_path)
    calls = []

    def _fake_run(cmd, **kw):
        calls.append(cmd)
        if "--unattended" in cmd:
            return SimpleNamespace(
                returncode=2, stdout="",
                stderr="clawmetry: error: unrecognized arguments: --unattended",
            )
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr(dapp.subprocess, "run", _fake_run)
    dapp.RuntimeSupervisor._background_pip_upgrade(stub)
    assert calls == [
        [str(cli), "update", "--unattended"],
        [str(cli), "update"],
    ]
    assert stub.upgraded == ["0.12.999"]


def test_real_update_failure_does_not_trigger_plain_fallback(monkeypatch, tmp_path):
    """Only the unrecognized-flag signature may demote to a plain update;
    a genuine failure (network, pip) must NOT bypass the policy."""
    monkeypatch.setenv("CLAWMETRY_AUTO_UPDATE", "1")
    stub, cli = _stub_shell(tmp_path)
    calls = []

    def _fake_run(cmd, **kw):
        calls.append(cmd)
        return SimpleNamespace(returncode=1, stdout="", stderr="network unreachable")

    monkeypatch.setattr(dapp.subprocess, "run", _fake_run)
    dapp.RuntimeSupervisor._background_pip_upgrade(stub)
    assert calls == [[str(cli), "update", "--unattended"]]
    # The stamp IS written on a genuine failure now (changed 2026-08-15 with
    # the 60s cadence). This assertion used to require the opposite, which
    # pinned the retry-storm bug in place: the upgrade interval is enforced
    # only via the stamp, so never stamping a failure meant a broken update
    # re-ran on every watcher tick forever. See
    # tests/test_desktop_upgrade_cadence.py. What this test is actually about
    # -- that a real failure must NOT demote to a plain, policy-bypassing
    # `clawmetry update` -- is the `calls` assertion above, and is unchanged.
    assert stub.upgraded == ["0.12.999"]
