"""Regression test for install.sh Linux + WSL daemon-restart paths (issue #1182).

PR #1178 added a Darwin-only `launchctl kickstart` block that fixed the
stale-venv-after-upgrade bug for macOS but left ~half the install base
(Linux + WSL) silently broken. This test pins the three added code paths so
they don't regress:

1. Linux systemd --user restart of `clawmetry-sync.service`.
2. WSL detection via `/proc/version` + manual-restart hint.
3. Generic Linux fallback hint when no systemd unit is registered.

We can't actually run the installer cross-platform from CI without spinning up
real Linux/WSL VMs, so this test asserts the relevant code blocks exist *and*
that the script remains a valid bash script after the edit.
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
    """`bash -n install.sh` must parse cleanly."""
    bash = shutil.which("bash")
    assert bash, "bash not found on PATH — required to syntax-check install.sh"
    result = subprocess.run(
        [bash, "-n", str(INSTALL_SH)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"bash -n failed: {result.stderr}"


def test_linux_branch_restarts_systemd_user_unit() -> None:
    """The Linux branch must attempt to restart the clawmetry-sync user unit."""
    body = _read_install_sh()
    assert 'if [ "$OS" = "Linux" ]; then' in body, "Linux branch missing"
    # The systemd unit name is fixed by clawmetry/cli.py::_register_systemd
    # ("clawmetry-sync"). Don't let install.sh drift from that.
    assert "clawmetry-sync.service" in body, (
        "install.sh must reference clawmetry-sync.service "
        "(see clawmetry/cli.py::_register_systemd)"
    )
    assert "systemctl --user" in body, "must use --user (no root systemd)"
    assert "list-unit-files" in body, (
        "must check the unit is installed before restart"
    )
    assert "systemctl --user restart clawmetry-sync.service" in body


def test_wsl_detection_via_proc_version() -> None:
    """WSL has no systemd by default — the script must detect & handle it."""
    body = _read_install_sh()
    assert "grep -qi microsoft /proc/version" in body, (
        "WSL detection (grep microsoft /proc/version) missing"
    )
    assert "WSL detected" in body, "user-visible WSL hint missing"


def test_generic_linux_fallback_hint() -> None:
    """When no systemd unit is found, print a manual-restart hint."""
    body = _read_install_sh()
    # Both WSL and generic-Linux fall through to the same pkill hint.
    assert "pkill -f clawmetry" in body, "manual restart hint missing"
    assert "no systemd user unit found" in body, (
        "generic Linux fallback hint missing"
    )


def test_darwin_block_unchanged_kickstart() -> None:
    """Don't accidentally regress the working Darwin path."""
    body = _read_install_sh()
    assert 'if [ "$OS" = "Darwin" ]; then' in body
    assert "launchctl kickstart -k" in body
    assert "/usr/libexec/PlistBuddy" in body


def test_darwin_no_plist_prints_manual_hint() -> None:
    """Cross-platform sanity: Darwin without plists also prints the hint."""
    body = _read_install_sh()
    # The Darwin block tracks _DARWIN_PLIST_FOUND and falls back to the
    # same pkill hint when nothing is installed.
    assert "_DARWIN_PLIST_FOUND" in body
    # Hint text should match the Linux branch so users see one consistent
    # instruction across platforms.
    assert "pkill -f clawmetry && nohup clawmetry &" in body
