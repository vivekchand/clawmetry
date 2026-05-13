"""Regression test for install.sh duplicate-daemon detection + cleanup.

Bug pinned by these tests
-------------------------

Re-running ``curl install.sh | bash`` against an already-installed copy used
to leave the OLD pip-launched daemon (running stale code) alive next to the
fresh venv binary. Both processes raced for the DuckDB write lock and every
internal query 500'd with::

    Conflicting lock is held in /Users/vivek/.local/share/uv/python/
        cpython-3.11.15-macos-aarch64-none/bin/python3.11 (PID 74211)

The launchctl/systemd restart blocks DON'T kick a daemon the user started by
hand — only OS-managed jobs. We need an explicit pre-flight detect + a
post-install ``pkill -f`` to clean the strays.

We can't run a real installer in CI without spinning up a fresh OS, so this
test asserts the relevant code blocks are present *and* that the script
remains a valid bash script after the edit.
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
    """``bash -n install.sh`` must parse cleanly after the edits."""
    bash = shutil.which("bash")
    assert bash, "bash not found on PATH"
    result = subprocess.run(
        [bash, "-n", str(INSTALL_SH)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"bash -n failed: {result.stderr}"


def test_preflight_detects_existing_daemon() -> None:
    """Before touching anything, install.sh must check for a running daemon
    and remember the result for the post-install cleanup block."""
    body = _read_install_sh()
    # The detect block sets a flag the post-install block reads.
    assert "CLAWMETRY_RESTART_AFTER" in body, (
        "install.sh must remember pre-existing daemon detection in a flag "
        "so the post-install block can act on it"
    )
    # We don't pin the EXACT pgrep regex (it can grow as new entry-points
    # land) but it must (a) use pgrep -f, (b) match clawmetry.sync, and
    # (c) match the user-launched ``clawmetry`` invocation.
    assert "pgrep -f" in body, "must use pgrep -f to find Python procs"
    assert "clawmetry\\.sync" in body or "clawmetry.sync" in body, (
        "preflight must match the sync daemon"
    )


def test_postinstall_kills_strays_when_flag_set() -> None:
    """After the new venv is in place AND the launchctl/systemd block has
    run, kill any pre-existing pip-launched daemon so the new code wins
    the DuckDB write lock."""
    body = _read_install_sh()
    # Guarded by the pre-flight flag — we MUST NOT pkill if no daemon was
    # there at install start (could clobber an unrelated process started
    # mid-install by the launchctl/systemd block).
    assert 'if [ "$CLAWMETRY_RESTART_AFTER" = "1" ]; then' in body, (
        "kill block must be guarded by the pre-flight flag"
    )
    # Must use ``pkill -f`` so the match works against the sync daemon's
    # full ``python3 -m clawmetry.sync`` cmdline.
    assert 'pkill -f "clawmetry\\.sync"' in body or \
           "pkill -f 'clawmetry\\.sync'" in body, (
        "post-install block must pkill -f the stray sync daemon"
    )


def test_postinstall_block_runs_after_launchctl_systemd_blocks() -> None:
    """The kill block must run AFTER the launchctl/systemd restart blocks.
    Otherwise we'd kill a daemon, then immediately fail to restart it
    (no plist exists yet for a first install)."""
    body = _read_install_sh()
    # Find ordinal positions of each anchor.
    darwin_anchor = body.find('if [ "$OS" = "Darwin" ]; then')
    linux_anchor = body.find('if [ "$OS" = "Linux" ]; then')
    kill_anchor = body.find('if [ "$CLAWMETRY_RESTART_AFTER" = "1" ]; then')
    assert darwin_anchor != -1, "Darwin restart block missing"
    assert linux_anchor != -1, "Linux restart block missing"
    assert kill_anchor != -1, "post-install kill block missing"
    assert kill_anchor > darwin_anchor, (
        "kill block must come AFTER Darwin launchctl restart"
    )
    assert kill_anchor > linux_anchor, (
        "kill block must come AFTER Linux systemd restart"
    )


def test_no_kill_when_no_daemon_was_running() -> None:
    """If the pre-flight detect didn't see a daemon, we must NOT pkill —
    that would risk killing an unrelated process the launchctl block just
    started. The test asserts the kill is INSIDE the flag-guard, not at
    top level."""
    body = _read_install_sh()
    # Simple structural check: the pkill -f "clawmetry\.sync" line MUST
    # follow the flag-guard `if` line and PRECEDE its closing `fi`.
    guard = 'if [ "$CLAWMETRY_RESTART_AFTER" = "1" ]; then'
    g_idx = body.find(guard)
    assert g_idx != -1
    # Everything between the guard and the next "fi" is the kill block.
    block_end = body.find("\nfi", g_idx)
    assert block_end != -1, "guarded block has no closing fi"
    block = body[g_idx:block_end]
    assert "pkill -f" in block, (
        "pkill -f must live inside the CLAWMETRY_RESTART_AFTER guard"
    )
