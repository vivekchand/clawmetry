"""The sync daemon's singleton lock must never be able to lock the daemon out
forever.

Field failure (2026-09-08, a Pro node): ``~/.clawmetry/sync.pid`` named a pid
that ``is_alive()`` reported as alive but that belonged to some *other*
process — the OS had recycled the number after the daemon died without running
its atexit hook. ``_acquire_pid_lock`` only asked "is that pid alive?", so every
launchd respawn (KeepAlive, ThrottleInterval 30) printed "Another instance is
already running. Exiting." and quit. Sync stopped for 12 hours while
``clawmetry status`` still printed a green "Daemon: Running".

The lock must therefore identify the *holder*, not just probe the number:
a live pid that is not our daemon is a stale lock, and stale locks get reclaimed.
"""
import json
import os
import subprocess
import sys
import time

import pytest

from clawmetry import sync


@pytest.fixture()
def home(tmp_path, monkeypatch):
    """Point the lock at an isolated ~/.clawmetry (never the real one)."""
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
    (tmp_path / ".clawmetry").mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(sync, "_pid_file",
                        lambda: tmp_path / ".clawmetry" / "sync.pid")
    monkeypatch.setattr(sync, "_lock_heartbeat_file",
                        lambda: tmp_path / ".clawmetry" / "sync.heartbeat",
                        raising=False)
    monkeypatch.setattr(sync, "_lock_identity_file",
                        lambda: tmp_path / ".clawmetry" / "sync.lock.json",
                        raising=False)
    yield tmp_path
    sync._release_pid_lock()


@pytest.fixture()
def foreign_process():
    """A live process that is emphatically NOT a clawmetry daemon."""
    p = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(120)"])
    try:
        yield p
    finally:
        p.kill()
        p.wait(timeout=10)


@pytest.fixture()
def lookalike_daemon():
    """A live process whose argv looks like the real sync daemon."""
    p = subprocess.Popen(
        [sys.executable, "-c", "import time; time.sleep(120)",
         "clawmetry.sync", "--daemon"]
    )
    try:
        yield p
    finally:
        p.kill()
        p.wait(timeout=10)


def _write_lock(home, payload):
    """Plant a lock file. A dict also plants the identity sidecar, which is
    where the start-time token lives."""
    path = home / ".clawmetry" / "sync.pid"
    if isinstance(payload, dict):
        path.write_text(str(payload["pid"]))
        (home / ".clawmetry" / "sync.lock.json").write_text(json.dumps(payload))
    else:
        path.write_text(payload)
    return path


# ── The field failure ────────────────────────────────────────────────────────
def test_reclaims_a_lock_held_by_a_recycled_pid(home, foreign_process):
    """A live pid that is not our daemon is a recycled number, not a rival."""
    _write_lock(home, str(foreign_process.pid))
    assert sync._acquire_pid_lock() is True, (
        "the daemon refused to start because an unrelated live process "
        "happened to own the pid recorded in sync.pid"
    )


def test_reclaims_when_the_recorded_start_time_does_not_match(home, foreign_process):
    """Identity is (pid, start-time). Same number + different start = recycled."""
    _write_lock(home, {"pid": foreign_process.pid,
                       "start": "epoch:1",  # 1970; certainly not this process
                       "owner": "clawmetry-sync"})
    assert sync._acquire_pid_lock() is True


def test_reclaims_an_unreadable_lock_file(home):
    _write_lock(home, "not a pid at all")
    assert sync._acquire_pid_lock() is True


def test_reclaims_a_lock_naming_our_own_pid(home):
    """Defence in depth: a caller that pre-writes the child's pid must not
    lock that child out of its own lock."""
    _write_lock(home, str(os.getpid()))
    assert sync._acquire_pid_lock() is True


# ── The lock must still be a lock ────────────────────────────────────────────
def test_refuses_when_a_real_daemon_holds_it(home, lookalike_daemon):
    """A live process that identifies as the sync daemon still wins."""
    _write_lock(home, {"pid": lookalike_daemon.pid,
                       "start": sync._proc_start_token_safe(lookalike_daemon.pid),
                       "owner": "clawmetry-sync"})
    assert sync._acquire_pid_lock() is False


def test_refuses_a_legacy_lock_when_the_holder_looks_like_the_daemon(
        home, lookalike_daemon):
    """Back-compat: a bare-int pid file written by an older release is honoured
    when the process it names really is a sync daemon."""
    _write_lock(home, str(lookalike_daemon.pid))
    assert sync._acquire_pid_lock() is False


# ── What the new lock records ────────────────────────────────────────────────
def test_acquired_lock_records_verifiable_identity(home):
    assert sync._acquire_pid_lock() is True
    # sync.pid stays a bare int: daemon_registration, the dashboard spawn and
    # install.sh all read it that way.
    assert (home / ".clawmetry" / "sync.pid").read_text().strip() == str(os.getpid())
    rec = json.loads((home / ".clawmetry" / "sync.lock.json").read_text())
    assert rec["pid"] == os.getpid()
    assert rec["owner"] == "clawmetry-sync"
    assert rec["start"], "no start-time token recorded: pid reuse stays undetectable"


def test_a_sidecar_from_an_earlier_holder_is_ignored(home, foreign_process):
    """A stale identity record naming a different pid must not be used to
    vouch for whoever holds the lock now."""
    (home / ".clawmetry" / "sync.pid").write_text(str(foreign_process.pid))
    (home / ".clawmetry" / "sync.lock.json").write_text(json.dumps(
        {"pid": foreign_process.pid + 100000, "start": "epoch:1",
         "owner": "clawmetry-sync"}))
    assert sync._acquire_pid_lock() is True


# ── A frozen holder ──────────────────────────────────────────────────────────
def test_reclaims_a_holder_that_stopped_heartbeating(home, lookalike_daemon,
                                                     monkeypatch):
    """A daemon that is alive but has stopped ticking its heartbeat is wedged;
    the next respawn takes the lock rather than exiting forever."""
    monkeypatch.setenv("CLAWMETRY_LOCK_STALE_SECS", "60")
    _write_lock(home, {"pid": lookalike_daemon.pid,
                       "start": sync._proc_start_token_safe(lookalike_daemon.pid),
                       "owner": "clawmetry-sync"})
    hb = home / ".clawmetry" / "sync.heartbeat"
    hb.write_text("1")
    old = time.time() - 3600
    os.utime(hb, (old, old))
    assert sync._acquire_pid_lock() is True
    assert lookalike_daemon.poll() is not None, "wedged holder was not stopped"


def test_a_holder_without_a_heartbeat_is_left_alone(home, lookalike_daemon,
                                                    monkeypatch):
    """An older daemon predates the heartbeat file. Absence is not evidence of
    a wedge, so an upgrade must not shoot a healthy running daemon."""
    monkeypatch.setenv("CLAWMETRY_LOCK_STALE_SECS", "60")
    _write_lock(home, {"pid": lookalike_daemon.pid,
                       "start": sync._proc_start_token_safe(lookalike_daemon.pid),
                       "owner": "clawmetry-sync"})
    assert sync._acquire_pid_lock() is False
    assert lookalike_daemon.poll() is None


def test_a_fresh_heartbeat_protects_the_holder(home, lookalike_daemon, monkeypatch):
    monkeypatch.setenv("CLAWMETRY_LOCK_STALE_SECS", "60")
    _write_lock(home, {"pid": lookalike_daemon.pid,
                       "start": sync._proc_start_token_safe(lookalike_daemon.pid),
                       "owner": "clawmetry-sync"})
    (home / ".clawmetry" / "sync.heartbeat").write_text("1")
    assert sync._acquire_pid_lock() is False
    assert lookalike_daemon.poll() is None


# ── identity without a command line (the Windows-without-psutil path) ────────
def test_a_holder_that_started_after_the_lock_is_a_recycled_pid(
        home, lookalike_daemon, monkeypatch):
    """Proof of reuse that needs neither a recorded token nor a command line:
    a process cannot have written a file that predates it.

    This is the only identity check available on a Windows host without psutil,
    where the command line reads back empty. The start epoch is injected
    because it is unavailable on a Mac without psutil too (``_proc_start_epoch``
    returns None there and this layer simply does not fire); what is pinned
    here is the DECISION, not the platform primitive.
    """
    path = _write_lock(home, str(lookalike_daemon.pid))
    old_time = time.time() - 3600
    os.utime(path, (old_time, old_time))
    monkeypatch.setattr("clawmetry.process_control._proc_start_epoch",
                        lambda pid: time.time())
    # Even a process whose command line says "clawmetry.sync" is not the writer
    # if it started an hour after the file was written.
    assert sync._acquire_pid_lock() is True


def test_a_holder_older_than_its_lock_file_is_left_alone(
        home, lookalike_daemon, monkeypatch):
    """The mirror case: a daemon that started before it wrote its lock is
    exactly what a healthy holder looks like."""
    path = _write_lock(home, str(lookalike_daemon.pid))
    os.utime(path, None)
    monkeypatch.setattr("clawmetry.process_control._proc_start_epoch",
                        lambda pid: time.time() - 3600)
    assert sync._acquire_pid_lock() is False


def test_an_unreadable_command_line_does_not_condemn_the_holder(home,
                                                                lookalike_daemon,
                                                                monkeypatch):
    """"I could not look" must not be read as "not ours": on a Windows host
    without psutil the command line is unreadable for every process, and
    treating that as foreign would let an upgrade reclaim a live daemon's lock.
    """
    monkeypatch.setattr(sync, "_holder_cmdline_verdict", lambda pid: "unknown")
    path = _write_lock(home, str(lookalike_daemon.pid))
    # Lock file written now, so the started-after-lock proof does not apply.
    os.utime(path, None)
    assert sync._acquire_pid_lock() is False
