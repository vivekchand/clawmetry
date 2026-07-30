"""Regression tests for install.sh ghost-install self-heal (2026-07-30).

A pip/uv install killed mid-flight (the daemon self-update's 180s timeout, a
Ctrl-C'd installer) lays down the new wheel's package files but never
generates the console scripts: site-packages then claims the latest version
is installed while ``$INSTALL_DIR/bin/clawmetry`` is gone. Every later plain
``pip/uv install --upgrade`` no-ops against that metadata, so install.sh used
to "succeed" while leaving the ``$BIN_DIR/clawmetry`` symlink dangling
(``bash: ~/.local/bin/clawmetry: No such file or directory`` — seen live on
the founder's machine, forensics: dist-info with no INSTALLER file and no
``bin/`` entries in RECORD).

install.sh must therefore check for the entry point after the install step
and force-reinstall when it is missing. The behavioural proof lives in
``.github/workflows/install-test.yml`` (delete the entry point, re-run the
installer, assert ``clawmetry --version`` works); these tests pin the code
paths so they don't silently regress on a refactor.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
INSTALL_SH = REPO_ROOT / "install.sh"


def _read_install_sh() -> str:
    assert INSTALL_SH.exists(), f"install.sh missing at {INSTALL_SH}"
    return INSTALL_SH.read_text()


def test_install_sh_syntax_is_valid() -> None:
    bash = shutil.which("bash")
    assert bash, "bash not found on PATH — required to syntax-check install.sh"
    result = subprocess.run(
        [bash, "-n", str(INSTALL_SH)], capture_output=True, text=True,
    )
    assert result.returncode == 0, f"bash -n failed: {result.stderr}"


def test_selfheal_block_force_reinstalls_missing_entry_point() -> None:
    body = _read_install_sh()
    assert 'if [ ! -x "$INSTALL_DIR/bin/clawmetry" ]; then' in body, (
        "self-heal guard missing: install.sh must check the console script "
        "exists after the install step (a pip killed mid-install leaves "
        "metadata claiming latest with no bin/clawmetry)"
    )
    assert "--force-reinstall" in body, (
        "self-heal must use --force-reinstall — a plain install/--upgrade "
        "no-ops against the ghost install's (lying) 'latest' metadata"
    )


def test_selfheal_runs_before_symlink_creation() -> None:
    """The $BIN_DIR/clawmetry symlink must be created AFTER the self-heal so
    it can never point at a still-missing target."""
    body = _read_install_sh()
    heal_idx = body.find('if [ ! -x "$INSTALL_DIR/bin/clawmetry" ]; then')
    link_idx = body.find('ln -sf "$INSTALL_DIR/bin/clawmetry"')
    assert heal_idx != -1 and link_idx != -1
    assert heal_idx < link_idx, (
        "self-heal block must run before the $BIN_DIR/clawmetry symlink is "
        "created"
    )


def test_selfheal_covers_both_uv_and_pip_paths() -> None:
    """The repair must work whether or not uv is available: uv venvs ship
    without pip, so the pip fallback must bootstrap it via ensurepip."""
    body = _read_install_sh()
    heal = body[body.find('if [ ! -x "$INSTALL_DIR/bin/clawmetry" ]; then'):]
    heal = heal[: heal.find("# Create symlink")]
    assert '"$_UV_BIN" pip install' in heal, "uv repair path missing"
    assert "-m ensurepip" in heal, (
        "pip repair path must bootstrap pip via ensurepip (uv venvs have none)"
    )
    assert '"$INSTALL_DIR/bin/python3" -m pip install' in heal, (
        "pip repair fallback missing"
    )


def test_version_probe_uses_isolated_mode() -> None:
    """The installed-version banner must probe with ``python3 -I`` — run from
    a source checkout, CWD lands on sys.path and the repo's stale egg-info
    shadows the venv (the installer printed 0.12.552 while 0.12.595 was on
    disk, 2026-07-30)."""
    body = _read_install_sh()
    assert '-I -c "import importlib.metadata' in body, (
        "CLAWMETRY_VERSION probe must pass -I (isolated mode) so a source "
        "checkout's egg-info can't misreport the installed version"
    )
