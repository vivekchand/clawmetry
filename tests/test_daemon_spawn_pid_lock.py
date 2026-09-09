"""The background daemon spawn must not write the daemon's lock file.

`_start_daemon_background()` used to write `~/.clawmetry/sync.pid` with the
CHILD's pid before the child ran. `sync._acquire_pid_lock()` claims that same
file with O_CREAT|O_EXCL, so the child found it present, read the pid, asked
`is_alive()` about it -- which is True, it is that process -- and exited with
"Another instance is already running."

The function could therefore never start a daemon, on any platform. That is
the mechanism behind #5740: `pip install clawmetry && clawmetry` rendered an
empty dashboard on a machine full of sessions, because the ingest daemon it
was supposed to rely on quietly refused to start.
"""
from __future__ import annotations

import os
import re
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


def _spawn_source() -> str:
    import inspect
    import dashboard
    return inspect.getsource(dashboard._start_daemon_background)


def test_spawn_does_not_pre_write_the_lock_file() -> None:
    src = _spawn_source()
    # The pid path may be *referenced* (to clean up after a failed start), but
    # it must never be written before the child has claimed it.
    writes = re.findall(r"pid_file\.write_text", src)
    assert not writes, (
        "_start_daemon_background writes sync.pid; that file is the daemon's "
        "singleton lock and the child claims it itself. Pre-writing it makes "
        "the child lose the race against its own pid and exit."
    )


def test_spawn_reports_a_daemon_that_died() -> None:
    """Announcing success unconditionally is what kept this invisible."""
    src = _spawn_source()
    assert "proc.wait(timeout=" in src, "spawn does not check the child survived"
    assert "exited immediately" in src, "spawn cannot report a dead child"


def test_spawn_captures_output_to_the_log_it_tells_users_to_read() -> None:
    src = _spawn_source()
    assert "sync.log" in src, "daemon output is not captured"
    assert "os.devnull" not in src.split("except OSError")[0], (
        "daemon stdout still goes to devnull on the happy path"
    )


def test_spawn_leaves_the_lock_to_the_daemon() -> None:
    """The daemon authors sync.pid together with the identity record that
    `_lock_holder_verdict` checks. A pid file written by the dashboard carries
    no such record, so the daemon must treat its own lock as stale and reclaim
    it before it can start -- work that exists only because we wrote it."""
    from clawmetry import sync
    src = __import__("inspect").getsource(sync._acquire_pid_lock)
    assert "_write_lock_identity" in src, (
        "the daemon no longer records lock identity; re-check whether the "
        "dashboard may write sync.pid"
    )
