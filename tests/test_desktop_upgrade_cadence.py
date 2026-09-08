"""The desktop shell polls PyPI every 60s, and the guards that makes necessary.

Founder call 2026-08-15: drop the shell's upgrade cadence from 6h to ~1 minute
so a desktop user picks up a release about as fast as the daemon's own update
worker does (routes/update_check.py, default 60s) instead of lagging it by up
to a quarter of a day.

What forced it: 0.12.707 armed the post-trial paywall, making the upgrade
overlay the only surface a lapsed user can reach. A layout bug there is a
lockout, not a cosmetic defect, and "wait up to six hours, then relaunch, with
no in-app way to trigger it" is not a recovery path for a trapped user.

The cadence change is one constant. This file exists for the two guards that
landed with it -- and the reason they were needed is NOT the obvious one.

They are not "safe at 6h, unsafe at 60s". They were already broken at 6h:

  1. `_background_pip_upgrade` stamped only on success. UPGRADE_CHECK_INTERVAL_SECS
     is enforced purely through that stamp, so after any failure
     `_should_upgrade()` stayed True and the watcher retried on the very next
     tick. A failing update re-ran every WATCHER_TICK_SECS (60s) forever, no
     matter what the interval said -- the 6h number only ever throttled the
     success path. Verified directly against the pre-change code: three
     consecutive failures, stamp never written, _should_upgrade() True each
     time.
  2. That retry ran a 300s-timeout subprocess synchronously inside the same
     watcher loop that respawns a crashed daemon. So an unreachable PyPI meant
     300s blocked, 60s tick, 300s blocked, indefinitely -- crash-respawn
     silently disabled the whole time, at any cadence.

Lowering the interval did not create either bug. It removed the last reason to
keep tolerating them, because now the success path runs at the same frequency
the failure path always did.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

import desktop.app as dapp  # noqa: E402


# ── the cadence itself ───────────────────────────────────────────────────────

def test_upgrade_cadence_is_about_a_minute():
    assert dapp.UPGRADE_CHECK_INTERVAL_SECS == 60


def test_cadence_is_not_slower_than_the_daemons_own_update_worker():
    """The shell must not be the bottleneck. routes/update_check.py polls on
    CLAWMETRY_UPDATE_CHECK_SECS (default 60); a shell that checks less often
    than the daemon it supervises just adds latency for no benefit."""
    import routes.update_check as uc  # noqa: F401  (import-ability is the point)
    daemon_default = 60
    assert dapp.UPGRADE_CHECK_INTERVAL_SECS <= daemon_default


def test_watcher_tick_is_not_slower_than_the_upgrade_interval():
    """_should_upgrade() is only consulted once per watcher tick, so the tick
    is the real floor on upgrade latency. A tick slower than the interval
    would make the interval a lie."""
    assert dapp.WATCHER_TICK_SECS <= dapp.UPGRADE_CHECK_INTERVAL_SECS


# ── guard 1: a failing update must not retry every tick ──────────────────────

def _shell(tmp_path):
    """A RuntimeSupervisor with just enough wired for _background_pip_upgrade.

    Deliberately the REAL class via __new__ rather than a SimpleNamespace:
    these tests are about _mark_upgraded / _should_upgrade actually agreeing
    on the stamp file, so stubbing them would test nothing.
    """
    runtime = tmp_path / "runtime"
    (runtime / "venv" / "bin").mkdir(parents=True, exist_ok=True)
    cli = runtime / "venv" / "bin" / "clawmetry"
    cli.write_text("#!/bin/sh\n")
    cli.chmod(0o755)

    sup = dapp.RuntimeSupervisor.__new__(dapp.RuntimeSupervisor)
    sup.runtime = runtime
    sup.stamp_file = runtime / "last-upgrade.json"
    sup.log_file = runtime / "bootstrap.log"
    sup.on_status = lambda *a, **k: None
    sup._venv_clawmetry = lambda: cli
    sup._get_installed_version = lambda: "0.12.708"
    return sup


def _run_upgrade(monkeypatch, sup, rc=0, raises=None):
    def fake_run(cmd, **kw):
        if raises is not None:
            raise raises
        return subprocess.CompletedProcess(cmd, rc, stdout="", stderr="")
    monkeypatch.setattr(dapp.subprocess, "run", fake_run)
    monkeypatch.setenv("CLAWMETRY_AUTO_UPDATE", "1")
    sup._background_pip_upgrade()


def test_successful_update_stamps(monkeypatch, tmp_path):
    sup = _shell(tmp_path)
    _run_upgrade(monkeypatch, sup, rc=0)
    assert sup.stamp_file.exists()
    assert sup._should_upgrade() is False


def test_failed_update_also_stamps(monkeypatch, tmp_path):
    """THE RETRY-STORM GUARD. Before: only rc==0 stamped, so an update that
    fails every time was re-attempted on every watcher tick, forever -- at the
    old 6h cadence just as much as at 60s, because the interval lives entirely
    in the stamp."""
    sup = _shell(tmp_path)
    _run_upgrade(monkeypatch, sup, rc=1)
    assert sup.stamp_file.exists(), (
        "a failed update left no stamp, so _should_upgrade() stays True and "
        "the watcher re-enters pip on every tick"
    )
    assert sup._should_upgrade() is False


def test_timed_out_update_also_stamps(monkeypatch, tmp_path):
    """The case that matters most: a hanging PyPI is exactly the failure that
    would otherwise re-enter pip every tick AND block crash-respawn while it
    does -- the two bugs compounding each other."""
    sup = _shell(tmp_path)
    _run_upgrade(
        monkeypatch, sup,
        raises=subprocess.TimeoutExpired(cmd="clawmetry update", timeout=90),
    )
    assert sup.stamp_file.exists()
    assert sup._should_upgrade() is False


# ── guard 2: the watcher's update must not hold the loop for 5 minutes ───────

def test_watcher_update_timeout_is_far_below_the_first_install_budget():
    """A first install must be patient (no runtime yet, big download). A
    periodic refresh already has a launchable ClawMetry, so waiting minutes on
    an unreachable PyPI buys nothing -- and costs crash-respawn latency,
    because watch() calls it synchronously."""
    assert dapp.WATCHER_UPDATE_TIMEOUT_SECS <= 120
    assert dapp.WATCHER_UPDATE_TIMEOUT_SECS < 300


def test_watcher_uses_the_short_timeout_not_the_install_one(monkeypatch, tmp_path):
    """Pins the wiring, not just the constant: a constant nobody passes is a
    comment."""
    seen = {}

    def fake_run(cmd, **kw):
        seen["timeout"] = kw.get("timeout")
        return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")

    sup = _shell(tmp_path)
    monkeypatch.setattr(dapp.subprocess, "run", fake_run)
    monkeypatch.setenv("CLAWMETRY_AUTO_UPDATE", "1")
    sup._background_pip_upgrade()

    assert seen["timeout"] == dapp.WATCHER_UPDATE_TIMEOUT_SECS, (
        "watcher update ran with timeout=%r; at a 60s cadence a 300s timeout "
        "would let an unreachable PyPI starve crash-respawn" % (seen["timeout"],)
    )


def test_worst_case_block_is_shorter_than_a_handful_of_ticks():
    """Bounds the starvation window in the units that matter: how many crash
    checks can a single hung update cost?"""
    missed = dapp.WATCHER_UPDATE_TIMEOUT_SECS / dapp.WATCHER_TICK_SECS
    assert missed <= 2.0, (
        "a hung update can cost %.1f crash-respawn checks; keep it to ~1-2"
        % missed
    )


# ── the kill switch still wins ───────────────────────────────────────────────

def test_disabled_auto_update_skips_entirely(monkeypatch, tmp_path):
    """Polling more often must not erode the opt-out. CLAWMETRY_AUTO_UPDATE=0
    means no subprocess at all, at any cadence."""
    sup = _shell(tmp_path)
    called = []
    monkeypatch.setattr(dapp.subprocess, "run",
                        lambda *a, **k: called.append(a) or None)
    monkeypatch.setenv("CLAWMETRY_AUTO_UPDATE", "0")
    sup._background_pip_upgrade()
    assert called == []
