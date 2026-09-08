"""The desktop shell's supervisor must outlive anything its child can do.

Incident 2026-08-17, reconstructed from the live machine. The user's window
sat frozen for 6h39m across every tab: "Failed to load: TypeError: Load
failed", "Connection lost. Reconnecting...", Cost panels stuck on
"Loading...". The app process was alive and responsive; it simply had no
backend and no way to say so.

What happened, to the millisecond:

  16:51:41.518  pip (the daemon's OWN in-process updater, not the shell's)
                creates clawmetry-0.12.730.dist-info/ in the shared runtime
                venv and unlinks the old dist -- taking venv/bin/clawmetry
                with it.
  16:51:44.345  The watcher tick reads "0.12.730" off the dist-info
                DIRECTORY NAME of a still-in-flight install, compares it to
                the running daemon's 0.12.729, and declares version drift.
  16:51:44.532  restart_daemon() -> stop() SIGTERMs a perfectly healthy,
                serving daemon and unlinks app-instance.json.
  16:51:45.032  start_daemon() -> subprocess.Popen([venv/bin/clawmetry, ...])
                raises FileNotFoundError. The script does not exist yet.
  16:51:45.580  pip re-creates venv/bin/clawmetry -- 548ms too late.

The Popen was unguarded, watch() had no try/except, and the thread was a
bare daemon thread in a PyInstaller windowed .app with no stderr sink. So
the exception vanished, the watcher thread died, and nothing was left to
respawn the daemon, reload the window, or even write a log line. The last
line in bootstrap.log is the drift message.

Three properties are load-bearing and each test below fails if one regresses:

  1. A spawn that cannot happen costs one tick, not the supervisor.
  2. A healthy daemon is never destroyed to make way for a replacement that
     was never proven launchable.
  3. Version drift is only acted on once the install has settled.
"""
from __future__ import annotations

import os
import sys
import threading
import time
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

import desktop.app as dapp  # noqa: E402


def _sup(tmp_path, *, with_entrypoint: bool = True):
    """A real RuntimeSupervisor over a temp runtime dir.

    Built via __new__ rather than a stub: these tests are about the actual
    interplay of entrypoint_ready / start_daemon / restart_daemon / _tick,
    so replacing any of them would test nothing.
    """
    runtime = tmp_path / "runtime"
    (runtime / "venv" / "bin").mkdir(parents=True, exist_ok=True)
    cli = runtime / "venv" / "bin" / "clawmetry"
    if with_entrypoint:
        cli.write_text("#!/bin/sh\nsleep 300\n")
        cli.chmod(0o755)

    sup = dapp.RuntimeSupervisor.__new__(dapp.RuntimeSupervisor)
    sup.port = 8999
    sup.on_status = lambda *a, **k: None
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


def _log_text(sup) -> str:
    try:
        return sup.log_file.read_text()
    except OSError:
        return ""


# ── property 1: a failed spawn costs one tick, never the supervisor ──────────

def test_start_daemon_returns_false_when_entrypoint_is_missing(tmp_path):
    """The exact 548ms hole: pip has deleted bin/clawmetry and not yet
    written it back."""
    sup = _sup(tmp_path, with_entrypoint=False)
    assert sup.entrypoint_ready() is False
    assert sup.start_daemon() is False
    assert sup.proc is None
    assert "start_daemon:" in _log_text(sup)


def test_start_daemon_swallows_oserror_from_popen(tmp_path, monkeypatch):
    """Even if the probe passes, the exec can still lose the race. Popen
    must never propagate -- that raise is what killed the watcher."""
    sup = _sup(tmp_path)

    def _boom(*a, **k):
        raise FileNotFoundError(2, "No such file or directory")

    monkeypatch.setattr(dapp.subprocess, "Popen", _boom)
    assert sup.start_daemon() is False
    assert sup.proc is None
    assert "Popen failed" in _log_text(sup)


def test_start_daemon_does_not_raise_on_permission_error(tmp_path, monkeypatch):
    """The written-but-not-yet-chmod+x variant of the same race."""
    sup = _sup(tmp_path)
    monkeypatch.setattr(
        dapp.subprocess, "Popen",
        lambda *a, **k: (_ for _ in ()).throw(PermissionError(13, "denied")),
    )
    assert sup.start_daemon() is False


def test_instance_file_exists_only_alongside_a_live_proc(tmp_path, monkeypatch):
    """app-instance.json's absence is what proved Popen raised. Keep that
    signal honest: a failed spawn must not leave a stale instance file, and
    must not be mistaken for a clean shutdown."""
    sup = _sup(tmp_path)
    monkeypatch.setattr(
        dapp.subprocess, "Popen",
        lambda *a, **k: (_ for _ in ()).throw(FileNotFoundError(2, "gone")),
    )
    assert sup.start_daemon() is False
    assert not sup.instance_file.exists()
    assert sup.proc is None


def _quiet_tick(sup, monkeypatch, *, drift: bool = False):
    """Neutralise every collaborator a tick touches so a test can make
    exactly one of them misbehave. Without this the tick shells out for
    real (ensure_sync_daemon, _background_pip_upgrade) and the timing
    assertions measure pip, not the loop."""
    monkeypatch.setattr(sup, "ensure_sync_daemon", lambda: None)
    monkeypatch.setattr(sup, "_should_upgrade", lambda: False)
    monkeypatch.setattr(sup, "_background_pip_upgrade", lambda: None)
    monkeypatch.setattr(
        sup, "_get_installed_version", lambda: "9.9.9" if drift else "0.12.729",
    )
    monkeypatch.setattr(sup, "_get_running_daemon_version", lambda: "0.12.729")
    if drift:
        # Pre-arm the debounce so the very first tick reaches restart_daemon.
        sup._pending_drift = "9.9.9"


@pytest.mark.parametrize(
    "victim",
    [
        "_get_installed_version",
        "_get_running_daemon_version",
        "ensure_sync_daemon",
        "restart_daemon",
        "_should_upgrade",
    ],
)
def test_watch_survives_a_raising_tick(tmp_path, monkeypatch, victim):
    """Whatever blows up inside a tick, supervision continues. This is the
    guard that turns a 6h39m outage into a 60s one."""
    sup = _sup(tmp_path)
    monkeypatch.setattr(dapp, "WATCHER_TICK_SECS", 0.05)
    # restart_daemon is only reached on the drift path.
    _quiet_tick(sup, monkeypatch, drift=(victim == "restart_daemon"))
    monkeypatch.setattr(
        sup, victim,
        lambda *a, **k: (_ for _ in ()).throw(RuntimeError(f"boom in {victim}")),
    )

    t = threading.Thread(target=sup.watch, args=(lambda: None,), daemon=True)
    t.start()
    time.sleep(0.6)
    ticks = sup._tick_count
    sup.shutting_down.set()
    assert ticks >= 2, f"watcher stopped ticking after {ticks} ticks"
    assert t.is_alive(), "watcher thread died on a raising tick"
    t.join(timeout=3)
    assert "watcher tick raised" in _log_text(sup)


def test_watch_logs_its_own_exit(tmp_path, monkeypatch):
    """A vanished watcher must leave a trace. In the incident it left none."""
    sup = _sup(tmp_path)
    monkeypatch.setattr(dapp, "WATCHER_TICK_SECS", 0.05)
    _quiet_tick(sup, monkeypatch)
    t = threading.Thread(target=sup.watch, args=(lambda: None,), daemon=True)
    t.start()
    time.sleep(0.2)
    sup.shutting_down.set()
    t.join(timeout=3)
    assert not t.is_alive()
    log = _log_text(sup)
    assert "watcher: started" in log
    assert "watcher: thread exiting" in log


# ── property 2: never destroy a backend you cannot replace ───────────────────

def test_restart_defers_instead_of_killing_a_healthy_daemon(tmp_path):
    """The incident in one assertion.

    Entrypoint is mid-rewrite, so restart_daemon must decline and leave the
    running daemon alone. Before the fix it called stop() first and only
    then discovered it could not spawn a replacement."""
    sup = _sup(tmp_path, with_entrypoint=False)

    class _LiveProc:
        pid = 4242
        terminated = False

        def poll(self):
            return None

    live = _LiveProc()
    sup.proc = live
    stopped = {"called": False}
    sup.stop = lambda: stopped.__setitem__("called", True)  # type: ignore[method-assign]

    assert sup.restart_daemon() is False
    assert stopped["called"] is False, "killed a healthy daemon it could not replace"
    assert sup.proc is live, "dropped the live daemon handle"
    assert "deferring restart" in _log_text(sup)


def test_restart_failure_is_logged_on_the_drift_branch(tmp_path, monkeypatch):
    """A failed restart used to be indistinguishable from a hang: both left
    the log ending at the drift line."""
    sup = _sup(tmp_path)
    monkeypatch.setattr(sup, "_get_installed_version", lambda: "9.9.9")
    monkeypatch.setattr(sup, "_get_running_daemon_version", lambda: "9.9.8")
    monkeypatch.setattr(sup, "ensure_sync_daemon", lambda: None)
    monkeypatch.setattr(sup, "restart_daemon", lambda: False)

    sup._tick(lambda: None)  # tick 1: observe drift
    sup._tick(lambda: None)  # tick 2: confirm and act
    log = _log_text(sup)
    assert "version drift:" in log
    assert "restart after drift -> False" in log


def test_status_never_gates_the_restart(tmp_path, monkeypatch):
    """Recovery first, cosmetics second. on_status is a synchronous RPC into
    a webview that can be wedged; it must not sit in front of the restart."""
    sup = _sup(tmp_path)
    order: list = []
    monkeypatch.setattr(sup, "_get_installed_version", lambda: "9.9.9")
    monkeypatch.setattr(sup, "_get_running_daemon_version", lambda: "9.9.8")
    monkeypatch.setattr(sup, "ensure_sync_daemon", lambda: None)
    monkeypatch.setattr(
        sup, "restart_daemon", lambda: (order.append("restart"), False)[1],
    )
    sup.on_status = lambda msg: order.append("status")

    sup._tick(lambda: None)
    sup._tick(lambda: None)
    assert order and order[0] == "restart", f"status ran before recovery: {order}"


# ── property 3: only act on a settled install ────────────────────────────────

def test_drift_is_debounced_across_two_ticks(tmp_path, monkeypatch):
    """A single tick's reading can describe an install still in flight. One
    transient disagreement must never trigger a restart."""
    sup = _sup(tmp_path)
    restarts = {"n": 0}
    monkeypatch.setattr(sup, "ensure_sync_daemon", lambda: None)
    monkeypatch.setattr(sup, "_should_upgrade", lambda: False)
    monkeypatch.setattr(
        sup, "restart_daemon",
        lambda: (restarts.__setitem__("n", restarts["n"] + 1), True)[1],
    )

    seen = iter(["0.12.730", "0.12.729"])  # drift for exactly one tick
    monkeypatch.setattr(sup, "_get_installed_version", lambda: next(seen))
    monkeypatch.setattr(sup, "_get_running_daemon_version", lambda: "0.12.729")

    sup._tick(lambda: None)
    sup._tick(lambda: None)
    assert restarts["n"] == 0, "restarted on a single-tick drift blip"
    assert "version drift seen:" in _log_text(sup)


def test_sustained_drift_still_restarts(tmp_path, monkeypatch):
    """The debounce must not break the feature it guards -- 'Update now'
    still has to land."""
    sup = _sup(tmp_path)
    restarts = {"n": 0}
    reloaded = {"n": 0}
    monkeypatch.setattr(sup, "ensure_sync_daemon", lambda: None)
    monkeypatch.setattr(sup, "_should_upgrade", lambda: False)
    monkeypatch.setattr(sup, "_get_installed_version", lambda: "0.12.730")
    monkeypatch.setattr(sup, "_get_running_daemon_version", lambda: "0.12.729")
    monkeypatch.setattr(
        sup, "restart_daemon",
        lambda: (restarts.__setitem__("n", restarts["n"] + 1), True)[1],
    )

    def on_restart():
        reloaded["n"] += 1

    sup._tick(on_restart)
    assert restarts["n"] == 0
    sup._tick(on_restart)
    assert restarts["n"] == 1, "sustained drift never restarted"
    assert reloaded["n"] == 1, "window was not reloaded onto the new daemon"


def test_installed_version_ignores_an_install_without_RECORD(tmp_path):
    """pip creates dist-info/ seconds before the package is launchable.
    RECORD is pip's own completion marker; the directory name alone is a lie
    for the length of the install."""
    sup = _sup(tmp_path)
    sp = sup.venv / "lib" / "python3.11" / "site-packages"
    good = sp / "clawmetry-0.12.729.dist-info"
    good.mkdir(parents=True)
    (good / "RECORD").write_text("")
    partial = sp / "clawmetry-0.12.730.dist-info"
    partial.mkdir(parents=True)
    (partial / "METADATA").write_text("Name: clawmetry\n")  # no RECORD yet

    assert sup._get_installed_version() == "0.12.729"

    (partial / "RECORD").write_text("")
    assert sup._get_installed_version() == "0.12.730"


# ── one venv, one updater ────────────────────────────────────────────────────

def test_child_env_disarms_the_daemons_own_updater(tmp_path, monkeypatch):
    """Two updaters shared one venv: the shell's, and the child's in-process
    worker that pip-upgrades then calls os._exit(0) expecting a supervisor.
    That second writer is what raced pip against the shell's restart."""
    sup = _sup(tmp_path)
    captured = {}

    class _FakeProc:
        pid = 1234

        def poll(self):
            return None

    def _fake_popen(argv, **kwargs):
        captured["env"] = kwargs.get("env", {})
        return _FakeProc()

    monkeypatch.setattr(dapp.subprocess, "Popen", _fake_popen)
    monkeypatch.delenv("CLAWMETRY_AUTO_UPDATE", raising=False)

    assert sup.start_daemon() is True
    assert captured["env"].get("CLAWMETRY_AUTO_UPDATE") == "0"
    # The shell's own updater must stay armed.
    assert "CLAWMETRY_AUTO_UPDATE" not in os.environ


# ── the user could not get out ───────────────────────────────────────────────

def test_recovery_surface_exists_on_the_js_bridge(tmp_path):
    """A stranded page's only working channel is the JS bridge -- the HTTP
    origin is dead by definition. Without these the user's sole options were
    Quit and Uninstall."""
    sup = _sup(tmp_path)
    api = dapp.DesktopAPI(sup)
    for name in ("restart_backend", "reload_dashboard", "backend_state"):
        assert callable(getattr(api, name, None)), f"DesktopAPI.{name} missing"

    # Unwired is a clean refusal, never an exception.
    assert api.restart_backend()["ok"] is False
    assert api.reload_dashboard()["ok"] is False

    calls = []
    api._recover_backend = lambda: calls.append("recover")
    api._reload_window = lambda: calls.append("reload")
    assert api.restart_backend()["ok"] is True
    assert api.reload_dashboard()["ok"] is True
    time.sleep(0.3)
    assert set(calls) == {"recover", "reload"}


def test_backend_state_is_answerable_with_a_dead_backend(tmp_path):
    """The overlay polls this to decide what to show. It must not raise when
    there is no child at all -- that is precisely when it is called."""
    sup = _sup(tmp_path)
    sup.proc = None
    state = dapp.DesktopAPI(sup).backend_state()
    assert state["ok"] is True
    assert state["daemon_running"] is False
    assert state["port"] == sup.port


def test_gui_calls_are_bounded():
    """pywebview's Cocoa evaluate_js/load_url park the CALLING thread on an
    unbounded Semaphore.acquire(). Nothing on the supervision path may wait
    on the GUI forever."""
    assert dapp.GUI_CALL_TIMEOUT_SECS > 0
    assert dapp.GUI_CALL_TIMEOUT_SECS <= dapp.WATCHER_TICK_SECS
