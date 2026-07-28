"""Auto-update gating: default ON for the supervised sync-daemon role
(0.12.494+), opt-in for the dashboard role; never re-triggers pip once a
restart is pending; honours the CLAWMETRY_AUTO_UPDATE kill switch and the
release-age stability rail.

The upgrade itself goes through the same vetted path as the manual "Update
now" button (routes.meta.perform_self_update), which is mocked here — these
tests are about the *gating*, not the pip/restart mechanics.
"""
from __future__ import annotations

import importlib
import os
import time


def _uc():
    import routes.update_check as uc
    return importlib.reload(uc)


def _as_daemon(uc, monkeypatch):
    """Run the checker as the supervised sync daemon (the default-on role)."""
    monkeypatch.delenv("CLAWMETRY_AUTO_UPDATE", raising=False)
    uc._process_role = "daemon"
    monkeypatch.setattr(uc, "_daemon_supervised", lambda: True)


def _mock_self_update(monkeypatch, calls, ok=True, restarts=None):
    import routes.meta as meta

    def _fake(reason="manual", restart=True, target_version=None):
        calls.append(reason)
        if restarts is not None:
            restarts.append(restart)
        return ({"ok": ok, "old_version": "0.12.1", "new_version": "0.12.2"},
                200 if ok else 500)

    monkeypatch.setattr(meta, "perform_self_update", _fake)


def test_auto_update_off_does_not_upgrade(monkeypatch):
    uc = _uc()
    _as_daemon(uc, monkeypatch)
    monkeypatch.setattr(uc, "_get_update_check_config", lambda: {"auto_update": False})
    calls = []
    _mock_self_update(monkeypatch, calls)
    uc._maybe_auto_update("0.12.1", "0.12.2")
    assert calls == [], "must not upgrade when auto_update is off"


def test_auto_update_on_upgrades_once(monkeypatch):
    uc = _uc()
    _as_daemon(uc, monkeypatch)
    monkeypatch.setattr(uc, "_get_update_check_config", lambda: {"auto_update": True})
    calls = []
    _mock_self_update(monkeypatch, calls)
    uc._maybe_auto_update("0.12.1", "0.12.2")
    assert calls == ["auto"], "must upgrade once when auto_update is on"
    # Guard: a second check before the restart lands must NOT re-trigger pip.
    uc._maybe_auto_update("0.12.1", "0.12.2")
    assert calls == ["auto"], "must not re-trigger while a restart is pending"


def test_auto_update_failure_allows_retry_after_backoff(monkeypatch):
    """A failed install is retryable, but only after the failure backoff —
    with the 60s check loop an immediately-retryable failure would re-run
    pip against a broken target every minute."""
    uc = _uc()
    _as_daemon(uc, monkeypatch)
    monkeypatch.setattr(uc, "_get_update_check_config", lambda: {"auto_update": True})
    calls = []
    _mock_self_update(monkeypatch, calls, ok=False)
    uc._maybe_auto_update("0.12.1", "0.12.2")
    assert calls == ["auto"]
    # Within the backoff window the same target is NOT retried.
    uc._maybe_auto_update("0.12.1", "0.12.2")
    assert calls == ["auto"], "failed target must back off, not retry every check"
    # A DIFFERENT (newer) target is not blocked by the failed one's backoff.
    uc._maybe_auto_update("0.12.1", "0.12.3")
    assert calls == ["auto", "auto"], "a new target must not inherit the backoff"
    # Once the backoff deadline passes, the original target is retryable.
    import time as _t
    uc._failed_update_attempts["0.12.2"] = _t.monotonic() - 1
    uc._maybe_auto_update("0.12.1", "0.12.2")
    assert calls == ["auto", "auto", "auto"], \
        "a failed auto-update must be retryable after the backoff"


def test_propagation_lag_gets_short_backoff(monkeypatch):
    """'No matching distribution' is the PyPI simple-index propagation race
    (the JSON API advertises a release 1-3 minutes before pip can install
    it) — it must retry in ~2 minutes, NOT the full broken-target backoff.
    Caught live 2026-07-10: the very first fast-loop update attempt hit this
    and sat out a 30-minute backoff for a 2-minute lag."""
    import time as _t
    import routes.meta as meta
    uc = _uc()
    _as_daemon(uc, monkeypatch)
    monkeypatch.setattr(uc, "_get_update_check_config", lambda: {"auto_update": True})

    def _fake(reason="manual", restart=True, target_version=None):
        return ({"ok": False,
                 "error": "pip exit 1: No matching distribution found for "
                          "clawmetry==0.12.551"}, 500)

    monkeypatch.setattr(meta, "perform_self_update", _fake)
    t0 = _t.monotonic()
    uc._maybe_auto_update("0.12.550", "0.12.551")
    deadline = uc._failed_update_attempts.get("0.12.551")
    assert deadline is not None
    wait = deadline - t0
    assert wait <= uc._propagation_retry_secs() + 5, (
        f"propagation lag backed off {wait:.0f}s; must be ~"
        f"{uc._propagation_retry_secs():.0f}s, not the broken-target backoff"
    )
    # A non-propagation failure still gets the long backoff.
    def _fake_broken(reason="manual", restart=True, target_version=None):
        return ({"ok": False, "error": "pip exit 1: some real build error"}, 500)

    monkeypatch.setattr(meta, "perform_self_update", _fake_broken)
    uc._maybe_auto_update("0.12.550", "0.12.552")
    deadline2 = uc._failed_update_attempts.get("0.12.552")
    assert deadline2 is not None
    assert (deadline2 - _t.monotonic()) > uc._propagation_retry_secs() + 60, \
        "a real install failure must keep the long backoff"


def test_auto_update_in_allowed_config_keys(monkeypatch):
    """The config setter must accept `auto_update` (else the toggle is a no-op)."""
    from flask import Flask
    uc = _uc()
    captured = {}
    monkeypatch.setattr(uc, "_set_update_check_config", lambda u: captured.update(u))
    app = Flask(__name__)
    with app.test_request_context(json={"auto_update": True, "bogus": "x"}):
        uc.api_update_check_config_post()
    assert captured == {"auto_update": True}, "auto_update must pass the allow-list, bogus keys filtered"


def test_auto_update_installs_given_target(monkeypatch):
    """The stability-window rail now lives in target SELECTION
    (_newest_aged_in_version, covered in test_autoupdate_newest_aged.py). Once a
    concrete aged-in ``target`` reaches _maybe_auto_update, it installs it and
    passes it through to perform_self_update as ``target_version``."""
    uc = _uc()
    _as_daemon(uc, monkeypatch)
    monkeypatch.setattr(uc, "_get_update_check_config", lambda: {"auto_update": True})
    import routes.meta as meta
    seen = {}

    def _fake(reason="manual", restart=True, target_version=None):
        seen["reason"] = reason
        seen["target"] = target_version
        return ({"ok": True}, 200)

    monkeypatch.setattr(meta, "perform_self_update", _fake)
    uc._maybe_auto_update("0.12.1", "0.12.10", latest="0.12.18")
    assert seen == {"reason": "auto", "target": "0.12.10"}, \
        "must install the chosen aged-in target, pinned via target_version"


def test_auto_update_ignores_target_not_newer(monkeypatch):
    """A target equal to or older than current is a no-op (defensive)."""
    uc = _uc()
    _as_daemon(uc, monkeypatch)
    calls = []
    _mock_self_update(monkeypatch, calls)
    monkeypatch.setattr(uc, "_get_update_check_config", lambda: {"auto_update": True})
    uc._maybe_auto_update("0.12.10", "0.12.10")
    assert calls == [], "must not upgrade to the same (or an older) version"


# ── Default-on policy + rails (0.12.494) ────────────────────────────────────


def test_auto_update_default_is_on(monkeypatch):
    """REGRESSION GUARD for the 2026-06-09 stale-fleet audit: with no stored
    config at all, auto_update must default to True. (Fails on the old
    opt-in default — that default left 92% of active nodes months stale.)"""
    uc = _uc()
    # Empty config store: every read falls through to the defaults dict.
    monkeypatch.setattr(uc, "_get_fleet_db_lock", lambda: __import__("threading").Lock())

    class _EmptyDb:
        def execute(self, *a, **k):
            class _R:
                def fetchall(self):
                    return []

                def fetchone(self):
                    return None
            return _R()

        def close(self):
            pass

    monkeypatch.setattr(uc, "_get_fleet_db", lambda: _EmptyDb())
    assert uc._get_update_check_config()["auto_update"] is True


def test_env_kill_switch_blocks_auto_update(monkeypatch):
    uc = _uc()
    _as_daemon(uc, monkeypatch)
    monkeypatch.setenv("CLAWMETRY_AUTO_UPDATE", "0")
    monkeypatch.setattr(uc, "_get_update_check_config", lambda: {"auto_update": True})
    calls = []
    _mock_self_update(monkeypatch, calls)
    uc._maybe_auto_update("0.12.1", "0.12.2")
    assert calls == [], "CLAWMETRY_AUTO_UPDATE=0 must hard-disable auto-update"


def test_dashboard_role_default_on_installs(monkeypatch):
    """REGRESSION GUARD for the 2026-07-28 founder directive: a release must
    reach EVERY install within minutes, so the dashboard role acts on the
    default-on policy too. (Fails on the old daemon-only rail, which left
    every local-only install — no daemon — permanently stale: the founder's
    Windows demo box sat a full release behind with the banner reporting
    update_available=true.)"""
    uc = _uc()
    monkeypatch.delenv("CLAWMETRY_AUTO_UPDATE", raising=False)
    assert uc._process_role == "dashboard"  # reload resets the role
    monkeypatch.setattr(uc, "_get_update_check_config", lambda: {"auto_update": True})
    monkeypatch.setattr(uc, "_dashboard_supervised", lambda: False)
    scheduled = []
    monkeypatch.setattr(uc, "_schedule_exec_restart", lambda: scheduled.append("exec"))
    monkeypatch.setattr(uc, "_schedule_windows_respawn", lambda: scheduled.append("respawn"))
    calls, restarts = [], []
    _mock_self_update(monkeypatch, calls, restarts=restarts)
    uc._maybe_auto_update("0.12.1", "0.12.2")
    assert calls == ["auto"], "dashboard role must install on the default-on policy"
    # Unsupervised process must not exit-and-die: it restarts in place.
    assert restarts == [False]
    assert scheduled in (["exec"], ["respawn"])  # POSIX vs Windows runner


def test_restart_plan_matrix():
    """Every role/platform/supervision combination actively restarts."""
    uc = _uc()
    # Windows: always the detached respawn (no supervisor, no usable execv).
    assert uc._restart_plan("daemon", "win32", False) == "respawn"
    assert uc._restart_plan("dashboard", "win32", True) == "respawn"
    # POSIX supervised: exit and let launchd/systemd respawn.
    assert uc._restart_plan("daemon", "darwin", True) == "exit"
    assert uc._restart_plan("dashboard", "linux", True) == "exit"
    # POSIX unsupervised: in-place re-exec.
    assert uc._restart_plan("daemon", "linux", False) == "exec"
    assert uc._restart_plan("dashboard", "darwin", False) == "exec"


def test_respawn_cmdline_console_script_vs_module(monkeypatch, tmp_path):
    uc = _uc()
    import sys as _sys
    exe = tmp_path / "clawmetry.exe"
    exe.write_bytes(b"MZ")
    monkeypatch.setattr(_sys, "argv", [str(exe), "--port", "8900"])
    assert uc._respawn_cmdline() == [str(exe), "--port", "8900"], \
        "console-script installs must relaunch via the launcher exe"
    monkeypatch.setattr(_sys, "argv", ["dashboard.py", "--port", "8900"])
    assert uc._respawn_cmdline() == [_sys.executable, "dashboard.py", "--port", "8900"], \
        "module runs must relaunch via the interpreter"


def test_update_lock_serializes_concurrent_updaters(monkeypatch, tmp_path):
    """Daemon + dashboard both run the fast loop now; only one may pip at a
    time in a shared environment."""
    uc = _uc()
    lock = tmp_path / "update.lock"
    monkeypatch.setattr(uc, "_UPDATE_LOCK_PATH", str(lock))
    assert uc._acquire_update_lock() is True
    assert uc._acquire_update_lock() is False, "second acquire must skip"
    uc._release_update_lock()
    assert uc._acquire_update_lock() is True, "released lock must reacquire"
    # Stale lock (crashed updater) is broken rather than wedging the fleet.
    uc._release_update_lock()
    lock.write_text("999 0")
    old = time.time() - uc._UPDATE_LOCK_STALE_SECS - 60
    os.utime(lock, (old, old))
    assert uc._acquire_update_lock() is True, "stale lock must be broken"
    uc._release_update_lock()


def test_dashboard_fast_loop_gating(monkeypatch):
    """The dashboard polls on the fast cadence iff auto-update is on."""
    uc = _uc()
    monkeypatch.delenv("CLAWMETRY_AUTO_UPDATE", raising=False)
    assert uc._process_role == "dashboard"
    monkeypatch.setattr(uc, "_get_update_check_config", lambda: {"auto_update": True})
    assert uc._fast_loop_active() is True, \
        "default-on dashboard must poll on the install cadence"
    monkeypatch.setattr(uc, "_get_update_check_config", lambda: {"auto_update": False})
    assert uc._fast_loop_active() is False, "opted-out dashboard keeps the banner cadence"
    monkeypatch.setattr(uc, "_get_update_check_config", lambda: {"auto_update": True})
    monkeypatch.setenv("CLAWMETRY_AUTO_UPDATE", "0")
    assert uc._fast_loop_active() is False, "kill switch wins"
    uc._process_role = "daemon"
    assert uc._fast_loop_active() is True, "daemon always polls fast"


def test_unsupervised_daemon_execs_in_place(monkeypatch):
    """A daemon with no launchd/systemd supervisor installs the new wheel and
    must NOT exit (nothing would respawn it → ingest stops); it re-execs the
    process image in place instead (POSIX plan)."""
    uc = _uc()
    monkeypatch.delenv("CLAWMETRY_AUTO_UPDATE", raising=False)
    uc._process_role = "daemon"
    monkeypatch.setattr(uc, "_daemon_supervised", lambda: False)
    monkeypatch.setattr(uc, "_restart_plan", lambda r, p, s: "exec")
    scheduled = []
    monkeypatch.setattr(uc, "_schedule_exec_restart", lambda: scheduled.append("exec"))
    monkeypatch.setattr(uc, "_get_update_check_config", lambda: {"auto_update": True})
    calls, restarts = [], []
    _mock_self_update(monkeypatch, calls, restarts=restarts)
    uc._maybe_auto_update("0.12.1", "0.12.2")
    assert calls == ["auto"]
    assert restarts == [False], "unsupervised daemon must not exit-to-restart"
    assert scheduled == ["exec"], "unsupervised daemon must re-exec onto the new wheel"


def test_supervised_daemon_restarts(monkeypatch):
    uc = _uc()
    _as_daemon(uc, monkeypatch)
    monkeypatch.setattr(uc, "_restart_plan", lambda r, p, s: "exit")
    monkeypatch.setattr(uc, "_get_update_check_config", lambda: {"auto_update": True})
    calls, restarts = [], []
    _mock_self_update(monkeypatch, calls, restarts=restarts)
    uc._maybe_auto_update("0.12.1", "0.12.2")
    assert calls == ["auto"]
    assert restarts == [True], "supervised daemon restarts to apply the wheel"


def test_windows_always_respawns(monkeypatch):
    """Windows has no supervisor: even a 'supervised-looking' process must use
    the detached respawn, never exit-and-die."""
    uc = _uc()
    monkeypatch.delenv("CLAWMETRY_AUTO_UPDATE", raising=False)
    uc._process_role = "daemon"
    monkeypatch.setattr(uc, "_daemon_supervised", lambda: True)
    monkeypatch.setattr(uc, "_restart_plan", lambda r, p, s: "respawn")
    scheduled = []
    monkeypatch.setattr(uc, "_schedule_windows_respawn", lambda: scheduled.append("respawn"))
    monkeypatch.setattr(uc, "_get_update_check_config", lambda: {"auto_update": True})
    calls, restarts = [], []
    _mock_self_update(monkeypatch, calls, restarts=restarts)
    uc._maybe_auto_update("0.12.1", "0.12.2")
    assert calls == ["auto"]
    assert restarts == [False]
    assert scheduled == ["respawn"]


def test_entitled_plan_enables_auto_update(monkeypatch):
    import clawmetry.sync as S
    import routes.update_check as uc
    state = {"auto_update": False}
    monkeypatch.setattr(uc, "_get_update_check_config", lambda: dict(state))
    monkeypatch.setattr(uc, "_set_update_check_config", lambda upd: state.update(upd))
    monkeypatch.delenv("CLAWMETRY_AUTO_UPDATE", raising=False)
    # free / inactive → unchanged
    S._sync_auto_update_with_plan("cloud_free"); assert state["auto_update"] is False
    S._sync_auto_update_with_plan(None);         assert state["auto_update"] is False
    # entitled → enabled
    S._sync_auto_update_with_plan("trial");      assert state["auto_update"] is True
    S._sync_auto_update_with_plan("cloud_pro");  assert state["auto_update"] is True


def test_entitled_plan_respects_optout_and_never_disables(monkeypatch):
    import clawmetry.sync as S
    import routes.update_check as uc
    state = {"auto_update": False}
    monkeypatch.setattr(uc, "_get_update_check_config", lambda: dict(state))
    monkeypatch.setattr(uc, "_set_update_check_config", lambda upd: state.update(upd))
    monkeypatch.setenv("CLAWMETRY_AUTO_UPDATE", "0")
    S._sync_auto_update_with_plan("cloud_pro");  assert state["auto_update"] is False  # opt-out
    # never auto-DISABLES a user's manual choice on downgrade
    monkeypatch.delenv("CLAWMETRY_AUTO_UPDATE", raising=False)
    state["auto_update"] = True
    S._sync_auto_update_with_plan("cloud_free"); assert state["auto_update"] is True
