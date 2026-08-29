"""The desktop shell's FIRST install must survive a hostile Windows.

Field failure 2026-08-29: a Windows 11 machine (dual-stack home network,
IPv6-first) showed "PyPI install failed. See bootstrap.log." on every
launch, forever. The bootstrap had exactly one pip attempt, no retry, no
--no-input (a keyring prompt in a windowless app hangs until the 300s
timeout), no pip self-upgrade (a stale bundled pip can't pick current
wheels), logged only stderr[:2000] (pip's resolver explains itself on
stdout), and — the brick — treated `venv/Scripts/python.exe` *existing*
as the venv being usable. On Windows that file is a launcher resolving
the base interpreter through pyvenv.cfg: a Store-Python update or a
python.org minor upgrade relocates the base, the launcher keeps existing,
and every pip run fails identically on every relaunch until someone
manually deletes the venv.

Properties under test:

  1. A venv whose python cannot run is detected as broken (existence is
     not health) and bootstrap() rebuilds it instead of dead-ending.
  2. The pip install retries once with a cold cache, and always carries
     --no-input / --prefer-binary.
  3. pip failure output is classified into an actionable message that
     includes nothing generic for the known failure families.
  4. A log line that the Windows locale codepage cannot encode does not
     raise (the old `except OSError` missed UnicodeEncodeError).
"""
from __future__ import annotations

import subprocess
import sys
import threading
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

import desktop.app as dapp  # noqa: E402


def _sup(tmp_path):
    """A real RuntimeSupervisor over a temp runtime dir (no __init__:
    these tests drive bootstrap-path methods directly)."""
    runtime = tmp_path / "runtime"
    runtime.mkdir(parents=True, exist_ok=True)
    sup = dapp.RuntimeSupervisor.__new__(dapp.RuntimeSupervisor)
    sup.port = 8999
    sup.statuses = []
    sup.on_status = sup.statuses.append
    sup.proc = None
    sup.runtime = runtime
    sup.venv = runtime / "venv"
    sup.stamp_file = runtime / "last-upgrade.json"
    sup.log_file = runtime / "bootstrap.log"
    sup.instance_file = runtime / "app-instance.json"
    sup._last_sync_start = 0.0
    sup.shutting_down = threading.Event()
    sup._pending_drift = None
    sup._last_tick = 0.0
    sup._tick_count = 0
    return sup


def _break_venv(sup):
    """Reproduce the Windows base-interpreter-upgrade brick: the venv
    python still exists on disk but can no longer run."""
    vpy = sup._venv_python()
    cfg = sup.venv / "pyvenv.cfg"
    if cfg.exists():
        cfg.write_text(cfg.read_text().replace("home = ", "home = /nonexistent-"))
    vpy.unlink()
    vpy.write_text("#!/nonexistent/python\n")
    vpy.chmod(0o755)
    assert vpy.exists()


# ── 1. health check + rebuild ────────────────────────────────────────────


def test_missing_venv_is_not_runnable(tmp_path):
    assert not _sup(tmp_path)._venv_is_runnable()


def test_broken_venv_is_detected_and_rebuilt(tmp_path):
    sup = _sup(tmp_path)
    py = dapp._bootstrap_python()
    assert py, "no bootstrap python on this machine"
    assert sup._create_venv(py)
    assert sup._venv_is_runnable()

    _break_venv(sup)
    assert not sup._venv_is_runnable(), (
        "a venv python that exists but cannot run must fail the health "
        "check — existence was the check that bricked Windows installs"
    )
    assert sup._create_venv(py), "rebuild over the broken venv must succeed"
    assert sup._venv_is_runnable()


def test_bootstrap_rebuilds_broken_venv_instead_of_dead_ending(tmp_path, monkeypatch):
    """End-to-end over bootstrap() with pip stubbed out (no network):
    broken venv in, runnable clawmetry out."""
    sup = _sup(tmp_path)
    py = dapp._bootstrap_python()
    assert py
    assert sup._create_venv(py)
    _break_venv(sup)

    calls = []

    def fake_pip():
        calls.append(True)
        # what a successful pip install leaves behind
        exe = sup._venv_clawmetry()
        exe.parent.mkdir(parents=True, exist_ok=True)
        exe.write_text("#!/bin/sh\nexit 0\n")
        exe.chmod(0o755)
        return 0, "Successfully installed clawmetry"

    monkeypatch.setattr(sup, "_pip_install_clawmetry", fake_pip)
    assert sup.bootstrap() is True
    assert calls, "bootstrap must reach the install after rebuilding"
    assert sup._venv_is_runnable(), "the venv must have been rebuilt runnable"


# ── 2. pip attempt shape ─────────────────────────────────────────────────


def test_pip_install_retries_with_cold_cache_and_safe_flags(tmp_path, monkeypatch):
    sup = _sup(tmp_path)
    seen = []

    def fake_run(argv, timeout):
        seen.append(argv)
        rc = 1
        # self-upgrade of pip succeeds; first clawmetry attempt fails;
        # the cold-cache attempt succeeds.
        if argv[-1] == "pip" or "--no-cache-dir" in argv:
            rc = 0
        return subprocess.CompletedProcess(argv, rc, stdout="", stderr="boom")

    monkeypatch.setattr(sup, "_run_child", fake_run)
    rc, _out = sup._pip_install_clawmetry()
    assert rc == 0
    install_attempts = [a for a in seen if a[-1] == "clawmetry"]
    assert len(install_attempts) == 2, "one retry, no more"
    assert "--no-cache-dir" in install_attempts[1], "retry must bypass the cache"
    for a in install_attempts:
        assert "--no-input" in a, "windowless app: pip must never prompt"
        assert "--prefer-binary" in a, "never build duckdb/cryptography from sdist"


def test_pip_install_gives_up_after_two_attempts(tmp_path, monkeypatch):
    sup = _sup(tmp_path)
    seen = []

    def fake_run(argv, timeout):
        seen.append(argv)
        return subprocess.CompletedProcess(
            argv, 0 if argv[-1] == "pip" else 1, stdout="resolver said no", stderr="")

    monkeypatch.setattr(sup, "_run_child", fake_run)
    rc, out = sup._pip_install_clawmetry()
    assert rc != 0
    assert len([a for a in seen if a[-1] == "clawmetry"]) == 2
    assert "resolver said no" in out, "stdout must be part of the reported output"


# ── 3. failure classification ────────────────────────────────────────────


@pytest.mark.parametrize(
    "snippet,expect",
    [
        ("Error: No Python at 'C:\\Python312\\python.exe'", "broken"),
        ("ERROR: No matching distribution found for clawmetry", "python.org"),
        ("SSLError(SSLCertVerificationError: certificate verify failed)", "proxy"),
        ("Connection to pypi.org timed out. (connect timeout=20)", "pypi.org"),
        ("PermissionError: [WinError 5] Access is denied", "antivirus"),
    ],
)
def test_pip_failures_classify_to_actionable_hints(snippet, expect):
    hint = dapp.RuntimeSupervisor._explain_pip_failure(snippet)
    assert expect.lower() in hint.lower()
    assert "bootstrap.log" not in hint, "the status line names the full log path"


def test_unknown_pip_failure_still_points_at_the_log():
    assert "log" in dapp.RuntimeSupervisor._explain_pip_failure("???").lower()


# ── 4. logging must never kill the boot thread ───────────────────────────


def test_log_survives_unencodable_characters(tmp_path):
    sup = _sup(tmp_path)
    sup._log("pip said: ✓ — ünïcode \u2713")
    assert "ünïcode" in sup.log_file.read_text(encoding="utf-8")
