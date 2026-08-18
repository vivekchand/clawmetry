"""Windows parity for install.sh's "you're already connected" gate (2026-08-18).

`install.sh` learned to detect an already-linked account, report it, and ask
before replaying `clawmetry onboard` (PR #4996). The Windows installers are the
same one-liner promise on another OS -- and they had a second problem: neither
`install.ps1` nor `install.cmd` ever ran onboarding at all, and `install.ps1`
wiped and rebuilt the venv on every run, which fails outright on a machine
whose daemon is live (Windows locks the files of a running process).

These tests pin the Windows behaviour:

* an already-connected node is reported and left alone unless the operator says
  yes (`CLAWMETRY_REONBOARD` decides it without a prompt; a non-interactive run
  keeps the setup);
* a node with no account linked goes straight into the wizard;
* a placeholder (auto-registered) account does not count as connected;
* the PowerShell installer upgrades the existing venv in place and restarts a
  daemon it had to stop.

The PowerShell behaviour is exercised with `pwsh` where it exists (GitHub's
ubuntu/macOS runners ship it); the end-to-end proof on real Windows lives in
`.github/workflows/install-test.yml`.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import textwrap
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
INSTALL_PS1 = REPO_ROOT / "install.ps1"
INSTALL_CMD = REPO_ROOT / "install.cmd"
INSTALL_SH = REPO_ROOT / "install.sh"

PWSH = shutil.which("pwsh")
needs_pwsh = pytest.mark.skipif(PWSH is None, reason="pwsh not installed")


def _ps1() -> str:
    return INSTALL_PS1.read_text(encoding="utf-8")


def _cmd() -> str:
    return INSTALL_CMD.read_text(encoding="utf-8")


def _helper_block() -> str:
    body = _ps1()
    start = body.index("# >>> CM_EXISTING_SETUP_BLOCK_START")
    end = body.index("# <<< CM_EXISTING_SETUP_BLOCK_END")
    return body[start:end]


def _run_pwsh(script: str, env_extra: dict | None = None, cwd: Path | None = None) -> str:
    env = dict(os.environ)
    for key in ("CLAWMETRY_REONBOARD", "CLAWMETRY_SKIP_ONBOARD", "CLAWMETRY_API_KEY", "CLAWMETRY_NO_CLOUD"):
        env.pop(key, None)
    env.update(env_extra or {})
    result = subprocess.run(
        [PWSH, "-NoProfile", "-Command", script],
        capture_output=True, text=True, env=env, timeout=180,
        cwd=str(cwd) if cwd else None, stdin=subprocess.DEVNULL,
    )
    assert result.returncode == 0, f"pwsh failed: {result.stdout}\n{result.stderr}"
    return result.stdout


# ── Static parity guards ────────────────────────────────────────────────────


def test_ps1_has_the_gate_helpers() -> None:
    body = _ps1()
    for needle in (
        "# >>> CM_EXISTING_SETUP_BLOCK_START",
        "# <<< CM_EXISTING_SETUP_BLOCK_END",
        "function Get-ClawmetryExistingSetup",
        "function Show-ClawmetryExistingSetup",
        "function Confirm-ClawmetryReonboard",
        "function Invoke-ClawmetryOnboard",
    ):
        assert needle in body, f"install.ps1 lost {needle!r}"


def test_ps1_runs_the_wizard_when_no_account_is_linked() -> None:
    """The whole point of the gate is that it only gates CONNECTED nodes."""
    body = _ps1()
    tail = body[body.index("if ($env:CLAWMETRY_SKIP_ONBOARD -eq \"1\")") :]
    assert "if ($setup.Connected)" in tail
    assert tail.count("Invoke-ClawmetryOnboard") >= 2, (
        "both branches must be able to onboard: after a yes, and unconditionally "
        "when no account is linked"
    )


def test_ps1_upgrades_in_place_instead_of_wiping_the_venv() -> None:
    """Windows locks a running process's files: `Remove-Item -Recurse` on the
    venv fails on any machine whose daemon is up -- which is exactly the
    machine this gate exists for."""
    body = _ps1()
    assert "pyvenv.cfg" in body, "install.ps1 must detect a reusable venv"
    assert "--upgrade clawmetry" in body, "install.ps1 must upgrade in place"
    assert "Removing previous (incomplete) installation" in body, (
        "the wipe must be reserved for a venv that is not usable"
    )


def test_ps1_stops_and_restarts_a_running_daemon() -> None:
    body = _ps1()
    assert "schtasks /end" in body, "a live daemon must be stopped before the upgrade"
    assert "schtasks /run" in body, "the daemon must come back on the NEW code"
    assert "ClawMetrySyncDaemon" in body


def test_cmd_has_the_gate() -> None:
    body = _cmd()
    assert "CLAWMETRY_SKIP_ONBOARD" in body
    assert "CLAWMETRY_REONBOARD" in body
    assert ":cm_reonboard" in body and ":cm_keep" in body and ":cm_onboard_done" in body
    assert "-m clawmetry onboard" in body, (
        "install.cmd must be able to onboard without depending on the Scripts "
        "dir already being on PATH in this session"
    )
    assert "clawmetry status --json" in body


def test_all_three_installers_share_one_contract() -> None:
    """Same env overrides and the same placeholder rule on every platform."""
    sh, ps1, cmd = INSTALL_SH.read_text(), _ps1(), _cmd()
    for body, name in ((sh, "install.sh"), (ps1, "install.ps1"), (cmd, "install.cmd")):
        assert "CLAWMETRY_REONBOARD" in body, f"{name} missing the re-onboard override"
        assert "CLAWMETRY_SKIP_ONBOARD" in body, f"{name} missing the skip override"
        assert "@clawmetry.auto" in body, f"{name} must not treat a placeholder as connected"
        assert "@clawmetry.linked" in body, f"{name} must not treat a placeholder as connected"


# ── PowerShell behaviour ────────────────────────────────────────────────────


def _probe_script(data_dir: Path, exe: Path | str) -> str:
    return (
        _helper_block()
        + textwrap.dedent(
            f"""
            $s = Get-ClawmetryExistingSetup -ClawmetryExe '{exe}' -DataDir '{data_dir}'
            "connected={{0}}|email={{1}}|plan={{2}}|sync={{3}}|node={{4}}|ver={{5}}" -f `
                $s.Connected, $s.Email, $s.Plan, $s.Sync, $s.Node, $s.Version
            """
        )
    )


def _probe(data_dir: Path, exe: Path | str = "no-such-exe") -> dict:
    out = _run_pwsh(_probe_script(data_dir, exe))
    line = [ln for ln in out.splitlines() if ln.startswith("connected=")][-1]
    return dict(kv.split("=", 1) for kv in line.split("|"))


def _stub_cli(directory: Path, snapshot: dict | None, marker: Path | None = None) -> Path:
    """A fake clawmetry that answers --version / status --json and records an
    onboard invocation. POSIX-only (these tests run under pwsh on Linux/macOS)."""
    exe = directory / "clawmetry-stub"
    exe.write_text(
        "#!/bin/bash\n"
        "case \"$1\" in\n"
        "  --version) echo 'clawmetry 0.12.999' ;;\n"
        f"  status) cat <<'JSON'\n{json.dumps(snapshot or {})}\nJSON\n  ;;\n"
        + (f"  onboard) echo STUB-ONBOARD-RAN; touch '{marker}' ;;\n" if marker else "")
        + "esac\n"
    )
    exe.chmod(0o755)
    return exe


@needs_pwsh
def test_probe_fresh_machine_is_not_connected(tmp_path: Path) -> None:
    assert _probe(tmp_path)["connected"] == "False"


@needs_pwsh
def test_probe_local_only_without_account_is_not_connected(tmp_path: Path) -> None:
    (tmp_path / "config.json").write_text(json.dumps({"api_key": "", "node_id": "box-1", "local_only": True}))
    (tmp_path / "nocloud").touch()
    vals = _probe(tmp_path)
    assert vals["connected"] == "False"
    assert vals["sync"] == "local-only"


@needs_pwsh
def test_probe_placeholder_account_is_not_connected(tmp_path: Path) -> None:
    (tmp_path / "config.json").write_text(
        json.dumps({"api_key": "cm_abc123456789", "account_email": "node-77@clawmetry.auto"})
    )
    vals = _probe(tmp_path)
    assert vals["connected"] == "False"
    assert vals["email"] == ""


@needs_pwsh
def test_probe_falls_back_to_config_files(tmp_path: Path) -> None:
    (tmp_path / "config.json").write_text(
        json.dumps({"api_key": "cm_abc123456789", "node_id": "box-3", "account_email": "a@b.com"})
    )
    (tmp_path / "cloud_plan.json").write_text(json.dumps({"plan": "cloud_starter"}))
    vals = _probe(tmp_path)
    assert vals["connected"] == "True"
    assert vals["email"] == "a@b.com"
    assert vals["plan"] == "Starter"
    assert vals["sync"] == "cloud"


@needs_pwsh
def test_probe_prefers_the_cli_snapshot(tmp_path: Path) -> None:
    (tmp_path / "config.json").write_text(
        json.dumps({"api_key": "cm_abc123456789", "node_id": "stale", "account_email": "old@b.com"})
    )
    exe = _stub_cli(
        tmp_path,
        {
            "version": "0.12.999",
            "cloud_sync": {
                "api_key_masked": "cm_abc...6789",
                "account": {"email": "founder@example.com", "plan": "cloud_pro", "placeholder": False},
                "node_id": "test-box",
                "local_only": True,
            },
        },
    )
    vals = _probe(tmp_path, exe)
    assert vals["connected"] == "True"
    assert vals["email"] == "founder@example.com"
    assert vals["plan"] == "Pro"
    assert vals["sync"] == "local-only"
    assert vals["node"] == "test-box"
    assert vals["ver"] == "0.12.999"


@needs_pwsh
def test_probe_survives_corrupt_config(tmp_path: Path) -> None:
    (tmp_path / "config.json").write_text("not json at all")
    assert _probe(tmp_path)["connected"] == "False"


@needs_pwsh
def test_gate_keeps_setup_when_not_interactive(tmp_path: Path) -> None:
    """No controlling terminal (CI, a provisioning script) must never
    re-onboard a machine behind the operator's back."""
    out = _run_pwsh(_helper_block() + "\nif (Confirm-ClawmetryReonboard) { 'RESULT=onboard' } else { 'RESULT=keep' }\n")
    assert "RESULT=keep" in out
    assert "keeping your current setup" in out.lower()


@needs_pwsh
@pytest.mark.parametrize("flag,expected", [("1", "onboard"), ("yes", "onboard"), ("0", "keep"), ("no", "keep")])
def test_gate_env_override(flag: str, expected: str) -> None:
    out = _run_pwsh(
        _helper_block() + "\nif (Confirm-ClawmetryReonboard) { 'RESULT=onboard' } else { 'RESULT=keep' }\n",
        {"CLAWMETRY_REONBOARD": flag},
    )
    assert f"RESULT={expected}" in out
    if expected == "keep":
        # Keeping a setup is never silent -- an operator who forced the skip
        # still needs to see that nothing changed and how to change it.
        assert "Keeping your current setup" in out


@needs_pwsh
def test_summary_reports_account_plan_sync_and_version(tmp_path: Path) -> None:
    exe = _stub_cli(
        tmp_path,
        {
            "version": "0.12.999",
            "cloud_sync": {
                "api_key_masked": "cm_abc...6789",
                "account": {"email": "founder@example.com", "plan": "cloud_pro", "placeholder": False},
                "node_id": "test-box",
                "local_only": True,
            },
        },
    )
    (tmp_path / "config.json").write_text(json.dumps({"api_key": "cm_abc123456789"}))
    script = _helper_block() + textwrap.dedent(
        f"""
        $s = Get-ClawmetryExistingSetup -ClawmetryExe '{exe}' -DataDir '{tmp_path}'
        Show-ClawmetryExistingSetup -Setup $s
        """
    )
    out = _run_pwsh(script)
    assert "already connected" in out
    assert "founder@example.com" in out
    assert "Pro plan" in out
    assert "Local-only" in out
    assert "0.12.999" in out
    assert "test-box" in out


@needs_pwsh
def test_summary_never_promises_a_dead_dashboard(tmp_path: Path) -> None:
    """Port 1 can't be a dashboard: the URL line must not be invented."""
    (tmp_path / "config.json").write_text(json.dumps({"api_key": "cm_abc123456789"}))
    (tmp_path / "server.json").write_text(json.dumps({"port": 1}))
    script = _helper_block() + f"\n'DASH=' + (Get-ClawmetryDashboardUrl -DataDir '{tmp_path}')\n"
    out = _run_pwsh(script)
    dash = [ln for ln in out.splitlines() if ln.startswith("DASH=")][-1]
    assert dash in ("DASH=", "DASH=http://localhost:8900"), dash


@needs_pwsh
def test_ps1_parses_cleanly() -> None:
    out = _run_pwsh(
        "$errors = $null; $tokens = $null; "
        f"[System.Management.Automation.Language.Parser]::ParseFile('{INSTALL_PS1}', [ref]$tokens, [ref]$errors) | Out-Null; "
        "if ($errors) { $errors | ForEach-Object { $_.Message } } else { 'PARSE OK' }"
    )
    assert "PARSE OK" in out, out


# ── The CMD probe is plain Python: run it directly, on any OS ───────────────


def _cmd_probe_source() -> str:
    """Pull the one-liner install.cmd hands to `python -c` out of the script."""
    for line in _cmd().splitlines():
        stripped = line.strip()
        # install.cmd also runs a short `python -c` for the version check --
        # the probe is the one that reads the account state.
        if stripped.startswith("%PYTHON% -c ") and "cloud_sync" in stripped:
            body = stripped[len("%PYTHON% -c ") :]
            assert body.startswith('"'), body[:40]
            end = body.rindex('"')
            return body[1:end]
    raise AssertionError("install.cmd no longer has a python probe one-liner")


def _run_cmd_probe(home: Path, status: dict | None = None) -> tuple[int, str]:
    env = dict(os.environ, HOME=str(home), USERPROFILE=str(home))
    for key in ("CLAWMETRY_API_KEY", "CLAWMETRY_NO_CLOUD"):
        env.pop(key, None)
    if status is not None:
        status_file = home / "status.json"
        status_file.write_text(json.dumps(status))
        env["CM_STATUS_FILE"] = str(status_file)
    else:
        env["CM_STATUS_FILE"] = str(home / "missing.json")
    import sys as _sys

    proc = subprocess.run(
        [_sys.executable, "-c", _cmd_probe_source()],
        capture_output=True, text=True, env=env, timeout=60,
    )
    return proc.returncode, proc.stdout


def _cm_data(home: Path) -> Path:
    d = home / ".clawmetry"
    d.mkdir(parents=True, exist_ok=True)
    return d


def test_cmd_probe_reports_not_connected_on_a_fresh_machine(tmp_path: Path) -> None:
    _cm_data(tmp_path)
    rc, out = _run_cmd_probe(tmp_path)
    assert rc == 1, "exit code carries the answer: non-zero means run the wizard"
    assert out.strip() == ""


def test_cmd_probe_reports_a_connected_node(tmp_path: Path) -> None:
    data = _cm_data(tmp_path)
    (data / "config.json").write_text(
        json.dumps({"api_key": "cm_abc123456789", "node_id": "box-9", "account_email": "a@b.com"})
    )
    (data / "cloud_plan.json").write_text(json.dumps({"plan": "cloud_pro"}))
    (data / "nocloud").touch()
    rc, out = _run_cmd_probe(tmp_path)
    assert rc == 0
    assert "already connected" in out
    assert "a@b.com" in out
    assert "Pro plan" in out
    assert "Local-only" in out
    assert "box-9" in out


def test_cmd_probe_prefers_the_status_snapshot(tmp_path: Path) -> None:
    data = _cm_data(tmp_path)
    (data / "config.json").write_text(
        json.dumps({"api_key": "cm_abc123456789", "node_id": "stale", "account_email": "old@b.com"})
    )
    rc, out = _run_cmd_probe(
        tmp_path,
        {
            "version": "0.12.999",
            "cloud_sync": {
                "api_key_masked": "cm_abc...6789",
                "account": {"email": "founder@example.com", "plan": "cloud_starter", "placeholder": False},
                "node_id": "test-box",
                "local_only": False,
            },
        },
    )
    assert rc == 0
    assert "founder@example.com" in out
    assert "Starter plan" in out
    assert "app.clawmetry.com" in out
    assert "0.12.999" in out


def test_cmd_probe_rejects_a_placeholder_account(tmp_path: Path) -> None:
    data = _cm_data(tmp_path)
    (data / "config.json").write_text(
        json.dumps({"api_key": "cm_abc123456789", "account_email": "node-77@clawmetry.auto"})
    )
    rc, out = _run_cmd_probe(tmp_path)
    assert rc == 1
    assert out.strip() == ""


def test_cmd_probe_degrades_to_not_connected_on_a_corrupt_config(tmp_path: Path) -> None:
    """A crash here must read as "no account" (wizard runs), never as a
    half-rendered summary or a failed install."""
    data = _cm_data(tmp_path)
    (data / "config.json").write_text("not json at all")
    rc, out = _run_cmd_probe(tmp_path)
    assert rc != 0
    assert "already connected" not in out
