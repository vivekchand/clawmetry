"""Regression tests for the installers' stale-duplicate sweep.

Bug pinned by these tests
--------------------------

``install.ps1``/``install.sh`` only ever cleaned up a previous install at
their OWN target directory. A clawmetry copy left behind in some OTHER
Python environment (a pre-venv ``pip install --user clawmetry``, or a run of
the no-venv ``install.cmd`` on a machine that later switched to the venv
installer) was never touched. Auto-update only keeps the daemon's own venv
current, so the stray copy goes stale forever, and if it happens to resolve
first on PATH it *shadows* the real binary — ``clawmetry --version`` then
reports a stale version while the real install is current (see
``clawmetry/doctor.py``'s install census, which only warns about this after
the fact; it never removes anything).

Live-reproduced on a user machine (2026-08-07): a plain ``pip install
--user`` into a system Python left clawmetry 0.11.99 installed and dormant
next to a current 0.12.655 dedicated-venv install. All three installers now
sweep every python/python3 interpreter reachable on PATH and
``pip uninstall`` clawmetry from every one of them except the venv/target
they are about to (re)build, before installing fresh.

We can't run a full installer against a real second Python interpreter in
CI's default job (see ``.github/workflows/install-test.yml`` for the
behavioural run), so these tests assert the sweep code is present, ordered
before the install step, and that install.sh remains valid bash / install.ps1
remains valid PowerShell after the edit.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
INSTALL_SH = REPO_ROOT / "install.sh"
INSTALL_PS1 = REPO_ROOT / "install.ps1"
INSTALL_CMD = REPO_ROOT / "install.cmd"


def _read(path: Path) -> str:
    assert path.exists(), f"{path.name} missing at {path}"
    return path.read_text()


# ── install.sh ────────────────────────────────────────────────────────────

def test_install_sh_syntax_is_valid() -> None:
    bash = shutil.which("bash")
    assert bash, "bash not found on PATH — required to syntax-check install.sh"
    result = subprocess.run(
        [bash, "-n", str(INSTALL_SH)], capture_output=True, text=True,
    )
    assert result.returncode == 0, f"bash -n failed: {result.stderr}"


def test_install_sh_sweeps_other_pythons_before_installing() -> None:
    body = _read(INSTALL_SH)
    sweep_idx = body.find("Stale-duplicate sweep")
    venv_idx = body.find("Install into venv")
    assert sweep_idx != -1, "install.sh must contain the stale-duplicate sweep"
    assert venv_idx != -1
    assert sweep_idx < venv_idx, (
        "the sweep must run BEFORE the real install so a stray copy can't "
        "keep shadowing the freshly (re)built venv"
    )
    assert '-m pip show clawmetry' in body
    assert '-m pip uninstall -y clawmetry' in body


def test_install_sh_sweep_never_touches_own_install_dir() -> None:
    """The sweep must skip interpreters INSIDE $INSTALL_DIR — that copy is
    the one about to be (re)built, not a stale duplicate."""
    body = _read(INSTALL_SH)
    sweep = body[body.find("Stale-duplicate sweep"): body.find("Install into venv")]
    assert '"$INSTALL_DIR"/*) continue ;;' in sweep


def test_install_sh_sweep_is_best_effort_under_set_dash_e() -> None:
    """install.sh runs with `set -e`; a pip uninstall failure on some
    unrelated interpreter must never abort the whole install."""
    body = _read(INSTALL_SH)
    assert "set -e" in body.splitlines()[3], "expected `set -e` near the top of install.sh"
    sweep = body[body.find("Stale-duplicate sweep"): body.find("Install into venv")]
    assert "pip uninstall -y clawmetry >/dev/null 2>&1 || true" in sweep


# ── install.ps1 ───────────────────────────────────────────────────────────

def test_install_ps1_sweeps_other_pythons_before_installing() -> None:
    body = _read(INSTALL_PS1)
    sweep_idx = body.find("Stale-duplicate sweep")
    venv_idx = body.find("Create venv")
    assert sweep_idx != -1, "install.ps1 must contain the stale-duplicate sweep"
    assert venv_idx != -1
    assert sweep_idx < venv_idx, (
        "the sweep must run BEFORE the venv is created so a stray copy "
        "can't keep shadowing it"
    )
    assert "-m pip show clawmetry" in body
    assert "-m pip uninstall -y clawmetry" in body


def test_install_ps1_sweep_never_touches_own_install_dir() -> None:
    body = _read(INSTALL_PS1)
    sweep = body[body.find("Stale-duplicate sweep"): body.find("Create venv")]
    assert "$installDir" in sweep
    assert "StartsWith($installDir" in sweep


def test_install_ps1_syntax_is_valid() -> None:
    pwsh = shutil.which("pwsh") or shutil.which("powershell")
    if not pwsh:
        import pytest

        pytest.skip("no PowerShell interpreter on PATH to syntax-check install.ps1")
    script = (
        "$e=$null; [System.Management.Automation.Language.Parser]::ParseFile("
        f"'{INSTALL_PS1}', [ref]$null, [ref]$e) | Out-Null; "
        "if ($e) { $e | ForEach-Object { Write-Error $_ }; exit 1 } else { exit 0 }"
    )
    result = subprocess.run(
        [pwsh, "-NoProfile", "-Command", script], capture_output=True, text=True,
    )
    assert result.returncode == 0, f"PowerShell parse failed: {result.stderr}"


# ── install.cmd ───────────────────────────────────────────────────────────

def test_install_cmd_sweeps_other_pythons_before_installing() -> None:
    body = _read(INSTALL_CMD)
    sweep_idx = body.find(":cm_sweep_stale")
    install_idx = body.find("Installing clawmetry...")
    assert sweep_idx != -1, "install.cmd must contain the stale-duplicate sweep"
    assert install_idx != -1
    assert sweep_idx < install_idx, (
        "the sweep must run BEFORE the pip install so a stray copy elsewhere "
        "on PATH can't keep shadowing the fresh one"
    )
    assert "pip show clawmetry" in body
    assert "pip uninstall -y clawmetry" in body


def test_install_cmd_also_removes_the_dedicated_venv_install() -> None:
    """install.cmd installs straight into system Python with no venv of its
    own; a leftover install.ps1-created venv at %LOCALAPPDATA%\\clawmetry
    would otherwise coexist and whichever wins PATH order shadows the other."""
    body = _read(INSTALL_CMD)
    assert '"%LOCALAPPDATA%\\clawmetry"' in body
    assert "rmdir /s /q" in body


def test_install_cmd_sweep_has_matching_goto_labels() -> None:
    body = _read(INSTALL_CMD)
    assert ":cm_sweep_stale" in body
    assert ":cm_sweep_done" in body
    assert "goto :cm_sweep_done" in body
    assert "goto :eof" in body
