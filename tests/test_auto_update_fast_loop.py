"""Fast auto-update (founder call 2026-07-10): a release must reach the
fleet in MINUTES, not days. ClawMetry ships 20+ releases a day.

Covers the four changes, each revert-proven red on the old code:

  1. The daemon role polls every ``CLAWMETRY_UPDATE_CHECK_SECS`` (default
     60s, clamped) instead of once a day after 9AM.
  2. The silent-install age gate defaults to 0 (track the absolute latest;
     ``CLAWMETRY_AUTOUPDATE_MIN_AGE_HOURS`` restores a window; the boot
     rollback guard is the safety net for a bad wheel).
  3. The sync daemon starts the checker with role="daemon" — the LOAD-
     BEARING wiring that was missing: without it the default-on policy
     never acted on free/local-only nodes (no plan sync ever wrote the
     auto_update flag), which is why "auto-update" felt like it didn't
     exist.
  4. An UNSUPERVISED daemon (containers, kubectl-exec wrappers) re-execs
     its own process image after installing, instead of holding the old
     wheel in memory until someone bounces it by hand. Gated: daemon role
     only, not Windows, ``CLAWMETRY_AUTOUPDATE_EXEC_RESTART=0`` kill switch.
"""
from __future__ import annotations

import importlib
import os
import re


def _uc():
    import routes.update_check as uc
    return importlib.reload(uc)


# ── 1. check cadence ─────────────────────────────────────────────────────────


def test_check_interval_default_and_env(monkeypatch):
    uc = _uc()
    monkeypatch.delenv("CLAWMETRY_UPDATE_CHECK_SECS", raising=False)
    assert uc._update_check_interval_secs() == 60.0
    monkeypatch.setenv("CLAWMETRY_UPDATE_CHECK_SECS", "300")
    assert uc._update_check_interval_secs() == 300.0
    # Clamps: never hammer PyPI sub-30s, never exceed a day.
    monkeypatch.setenv("CLAWMETRY_UPDATE_CHECK_SECS", "1")
    assert uc._update_check_interval_secs() == 30.0
    monkeypatch.setenv("CLAWMETRY_UPDATE_CHECK_SECS", "999999999")
    assert uc._update_check_interval_secs() == 86400.0
    monkeypatch.setenv("CLAWMETRY_UPDATE_CHECK_SECS", "junk")
    assert uc._update_check_interval_secs() == 60.0


def test_daemon_worker_checks_every_interval(monkeypatch):
    """The daemon-role worker must call _check_for_update once per interval
    tick — not once per day. We drive the loop with a stub stop_event whose
    wait() returns False (timeout) a few times, then True (stop)."""
    uc = _uc()
    uc._process_role = "daemon"
    monkeypatch.setattr(uc, "_get_update_check_config",
                        lambda: {"enabled": True, "check_on_startup": False})
    checks = []
    monkeypatch.setattr(uc, "_check_for_update", lambda: checks.append(1))

    class _Ev:
        def __init__(self, ticks):
            self.ticks = ticks
            self.waits = []

        def wait(self, timeout=None):
            self.waits.append(timeout)
            self.ticks -= 1
            return self.ticks < 0  # False (timed out) N times, then stop

        def is_set(self):
            return self.ticks < 0

    ev = _Ev(ticks=4)  # 1 boot-settle wait + 3 interval ticks
    uc._update_check_worker(ev)
    assert len(checks) == 3, f"expected one check per tick, got {len(checks)}"
    # Every post-boot wait uses the fast interval, not 3600s / daily gating.
    assert all(w == uc._update_check_interval_secs() for w in ev.waits[1:]), ev.waits


def test_dashboard_worker_keeps_daily_cadence(monkeypatch):
    """The dashboard role must NOT inherit the fast loop (it only shows the
    banner; per-minute PyPI polls belong to the installing daemon only)."""
    uc = _uc()
    uc._process_role = "dashboard"
    monkeypatch.setattr(uc, "_get_update_check_config",
                        lambda: {"enabled": True, "check_on_startup": False,
                                 "check_daily": True})
    checks = []
    monkeypatch.setattr(uc, "_check_for_update", lambda: checks.append(1))

    class _Ev:
        def __init__(self, ticks):
            self.ticks = ticks
            self.waits = []

        def wait(self, timeout=None):
            self.waits.append(timeout)
            self.ticks -= 1
            return self.ticks < 0

        def is_set(self):
            return self.ticks < 0

    ev = _Ev(ticks=3)
    uc._update_check_worker(ev)
    # Daily loop waits an hour between wakeups; at most one check fires.
    assert 3600 in ev.waits, ev.waits
    assert len(checks) <= 1


# ── 2. age gate default 0 ────────────────────────────────────────────────────


def test_min_age_defaults_to_zero_env_restores_window(monkeypatch):
    uc = _uc()
    monkeypatch.delenv("CLAWMETRY_AUTOUPDATE_MIN_AGE_HOURS", raising=False)
    assert uc._autoupdate_min_age_hours() == 0.0
    monkeypatch.setenv("CLAWMETRY_AUTOUPDATE_MIN_AGE_HOURS", "48")
    assert uc._autoupdate_min_age_hours() == 48.0


def test_zero_age_targets_absolute_latest():
    """With no age gate, a release published seconds ago is the target."""
    uc = _uc()
    from datetime import datetime, timedelta, timezone
    just_now = (datetime.now(timezone.utc) - timedelta(seconds=30)).isoformat()
    releases = {
        "0.12.550": [{"upload_time_iso_8601": just_now}],
    }
    assert uc._newest_aged_in_version(releases, "0.12.549", 0) == "0.12.550"
    # The old 48h default would have returned None here.
    assert uc._newest_aged_in_version(releases, "0.12.549", 48) is None


# ── 3. daemon role wiring in sync.py ─────────────────────────────────────────


def test_sync_daemon_starts_checker_with_daemon_role():
    """clawmetry/sync.py must pass role="daemon" — without it the default-on
    auto-update policy never acts (the 2026-07-10 stale-fleet root cause)."""
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    src = open(os.path.join(here, "clawmetry", "sync.py"), encoding="utf-8").read()
    calls = re.findall(r"_start_uc\(([^)]*)\)", src)
    assert calls, "sync.py no longer starts the update-check thread?"
    for args in calls:
        assert re.search(r"role\s*=\s*['\"]daemon['\"]", args), (
            "sync.py starts the update checker WITHOUT role='daemon'; "
            "default-on auto-update will silently never act: " + args
        )


# ── 4. unsupervised re-exec restart ──────────────────────────────────────────


def _gate(monkeypatch, uc, supervised, platform="darwin", kill=None):
    monkeypatch.delenv("CLAWMETRY_AUTO_UPDATE", raising=False)
    if kill is None:
        monkeypatch.delenv("CLAWMETRY_AUTOUPDATE_EXEC_RESTART", raising=False)
    else:
        monkeypatch.setenv("CLAWMETRY_AUTOUPDATE_EXEC_RESTART", kill)
    uc._process_role = "daemon"
    monkeypatch.setattr(uc, "_daemon_supervised", lambda: supervised)
    monkeypatch.setattr(uc, "_get_update_check_config",
                        lambda: {"auto_update": True})
    monkeypatch.setattr(uc.sys, "platform", platform)
    restarts = []
    execs = []
    monkeypatch.setattr(uc, "_schedule_exec_restart",
                        lambda *a, **k: execs.append(1))
    import routes.meta as meta
    monkeypatch.setattr(
        meta, "perform_self_update",
        lambda reason="auto", restart=True, target_version=None: (
            restarts.append(restart),
            ({"ok": True, "old_version": "0.12.1", "new_version": "0.12.2"}, 200),
        )[1],
    )
    return restarts, execs


def test_unsupervised_daemon_reexecs_after_install(monkeypatch):
    uc = _uc()
    restarts, execs = _gate(monkeypatch, uc, supervised=False)
    uc._maybe_auto_update("0.12.1", "0.12.2")
    assert restarts == [False], "unsupervised installs must not Timer-exit"
    assert execs == [1], "unsupervised daemon must re-exec onto the new wheel"


def test_supervised_daemon_uses_normal_restart(monkeypatch):
    uc = _uc()
    restarts, execs = _gate(monkeypatch, uc, supervised=True)
    uc._maybe_auto_update("0.12.1", "0.12.2")
    assert restarts == [True]
    assert execs == [], "supervised daemons restart via their supervisor"


def test_exec_restart_skipped_on_windows(monkeypatch):
    uc = _uc()
    restarts, execs = _gate(monkeypatch, uc, supervised=False, platform="win32")
    uc._maybe_auto_update("0.12.1", "0.12.2")
    assert restarts == [False]
    assert execs == [], "no execv semantics on Windows; defer to next start"


def test_exec_restart_kill_switch(monkeypatch):
    uc = _uc()
    restarts, execs = _gate(monkeypatch, uc, supervised=False, kill="0")
    uc._maybe_auto_update("0.12.1", "0.12.2")
    assert restarts == [False]
    assert execs == [], "CLAWMETRY_AUTOUPDATE_EXEC_RESTART=0 must disable re-exec"
