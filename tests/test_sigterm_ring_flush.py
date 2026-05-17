"""E2E tests for graceful-shutdown ring-buffer drain (#1593).

Sibling failure-mode to #1590 (concurrent flush race, fixed via PR #1608).
#1590 = mid-flight ring loss; this PR = shutdown-eviction ring loss.

Test surface (per Eng NN failure-mode taxonomy):
  1. SIGTERM  — `kill -TERM <pid>` (launchctl bootout, systemctl stop)
  2. SIGINT   — Ctrl+C in foreground
  3. sys.exit — Python `sys.exit(0)` from inside the daemon
  4. Timeout  — hung flush must NOT block shutdown past 5s
  5. Re-entrancy — signal then atexit must flush exactly once

Per memory `feedback_synthetic_tests_missed_real_event_shape`, we run a
real subprocess and send a real OS signal — NOT a mocked
``signal.signal()`` call. The whole point of #1593 is that Python's
default SIGTERM handler bypasses atexit; only a live process + real
signal exercises that path.

Driver shape:
  * tmp DuckDB via ``CLAWMETRY_LOCAL_STORE_PATH``
  * subprocess runs a payload script that installs the handlers, ingests
    N events, prints PID, idles
  * parent reads PID, sends signal, waits for clean exit
  * parent re-opens DuckDB read-only and counts rows
"""
from __future__ import annotations

import os
import signal
import subprocess
import sys
import time
from pathlib import Path

import pytest


_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)


# ── Subprocess payloads ────────────────────────────────────────────────────

# Common preamble: import sync (so handlers can be installed) + ingest N
# events synchronously into the ring. We deliberately set
# CLAWMETRY_LOCAL_FLUSH_SECS to a value LARGER than the test's shutdown
# window so the background flusher CANNOT have drained the ring on its
# own — any rows we observe in DuckDB came from the shutdown handler.
_PAYLOAD_INGEST_THEN_WAIT = """
import os, sys, time
sys.path.insert(0, {repo_root!r})
from clawmetry import sync as _sync
from clawmetry import local_store as _ls

_sync._install_shutdown_handlers()
store = _ls.get_store(read_only=False)
for i in range(50):
    store.ingest({{
        "id": f"evt-{{i:03d}}",
        "node_id": "test-node",
        "event_type": "model.completed",
        "ts": f"2026-05-17T10:00:{{i:02d}}",
        "session_id": "sess-shutdown",
        "data": "{{}}",
    }})
print("READY", os.getpid(), flush=True)
# Idle — wait for signal/exit. Sleep in 100ms slices so the signal
# handler can preempt cleanly on platforms where `time.sleep` would
# otherwise swallow the interrupt.
while True:
    time.sleep(0.1)
"""


_PAYLOAD_INGEST_THEN_SYS_EXIT = """
import os, sys, time
sys.path.insert(0, {repo_root!r})
from clawmetry import sync as _sync
from clawmetry import local_store as _ls

_sync._install_shutdown_handlers()
store = _ls.get_store(read_only=False)
for i in range(50):
    store.ingest({{
        "id": f"evt-{{i:03d}}",
        "node_id": "test-node",
        "event_type": "model.completed",
        "ts": f"2026-05-17T10:00:{{i:02d}}",
        "session_id": "sess-shutdown",
        "data": "{{}}",
    }})
print("READY", os.getpid(), flush=True)
# Tiny pause to let the parent read READY before we exit.
time.sleep(0.2)
sys.exit(0)
"""


_PAYLOAD_HUNG_FLUSH = """
import os, sys, time
sys.path.insert(0, {repo_root!r})
from clawmetry import sync as _sync
from clawmetry import local_store as _ls

# Shrink the timeout so we don't wait the full 5s default for the
# "abandon" branch. 1.5s gives the test budget margin while still
# proving the abandon path runs.
_sync._SHUTDOWN_FLUSH_TIMEOUT_SECS = 1.5

# Sabotage the flush to hang for 30s — well past the timeout. The
# shutdown handler must abandon and exit anyway.
def _hung_drain():
    time.sleep(30)
    return (0, 30.0)

_sync._drain_local_store_now = _hung_drain
_sync._install_shutdown_handlers()
print("READY", os.getpid(), flush=True)
while True:
    time.sleep(0.1)
"""


# ── Helpers ────────────────────────────────────────────────────────────────


def _spawn(tmp_path: Path, payload_template: str, log_file: Path) -> subprocess.Popen:
    """Spawn the payload as a subprocess with a tmp DuckDB. Returns the
    Popen with stdout piped (parent reads PID + log lines from it — the
    daemon's logger writes to stdout via a StreamHandler) and stderr
    streamed to a file for post-mortem inspection.
    """
    payload = payload_template.format(repo_root=_REPO_ROOT)
    env = os.environ.copy()
    env["CLAWMETRY_LOCAL_STORE_PATH"] = str(tmp_path / "shutdown.duckdb")
    # Flush interval LARGER than the test's shutdown window — proves the
    # rows landed via the shutdown handler, not the background flusher.
    env["CLAWMETRY_LOCAL_FLUSH_SECS"] = "60"
    # Batch threshold higher than the 50 events we ingest — proves the
    # ingest-side inline flush (when ring crosses FLUSH_BATCH) didn't
    # drain it either.
    env["CLAWMETRY_LOCAL_FLUSH_BATCH"] = "10000"
    log_fp = open(log_file, "w")
    return subprocess.Popen(
        [sys.executable, "-c", payload],
        stdout=subprocess.PIPE,
        stderr=log_fp,
        env=env,
        text=True,
        bufsize=1,  # line-buffered so READY is readable immediately
    )


def _wait_for_ready(proc: subprocess.Popen, timeout: float = 10.0) -> int:
    """Read the READY line; return the child PID."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        line = proc.stdout.readline()
        if line:
            parts = line.strip().split()
            if len(parts) == 2 and parts[0] == "READY":
                return int(parts[1])
        if proc.poll() is not None:
            raise RuntimeError(
                f"subprocess exited before READY (code={proc.returncode})"
            )
        time.sleep(0.05)
    raise TimeoutError("subprocess never printed READY")


def _count_events(db_path: Path) -> int:
    """Open the DuckDB read-only and count rows in `events`."""
    import duckdb
    conn = duckdb.connect(str(db_path), read_only=True)
    try:
        row = conn.execute("SELECT COUNT(*) FROM events").fetchone()
        return int(row[0]) if row else 0
    finally:
        conn.close()


# ── 1. SIGTERM drains the ring ─────────────────────────────────────────────


def test_sigterm_flushes_ring_before_exit(tmp_path):
    db_path = tmp_path / "shutdown.duckdb"
    log_path = tmp_path / "child.log"
    proc = _spawn(tmp_path, _PAYLOAD_INGEST_THEN_WAIT, log_path)
    try:
        pid = _wait_for_ready(proc)
        # Real SIGTERM — what launchctl / systemctl / `kill` actually send.
        os.kill(pid, signal.SIGTERM)
        rc = proc.wait(timeout=10)
        # Process exited cleanly via os._exit(0) from the handler.
        assert rc == 0, f"unexpected exit code {rc}; log={log_path.read_text()}"
    finally:
        if proc.poll() is None:
            proc.kill()
            proc.wait(timeout=5)

    count = _count_events(db_path)
    assert count == 50, (
        f"SIGTERM dropped events: got {count}/50 in DuckDB. "
        f"log={log_path.read_text()}"
    )


# ── 2. SIGINT (Ctrl+C) drains the ring ─────────────────────────────────────


def test_sigint_flushes_ring_before_exit(tmp_path):
    db_path = tmp_path / "shutdown.duckdb"
    log_path = tmp_path / "child.log"
    proc = _spawn(tmp_path, _PAYLOAD_INGEST_THEN_WAIT, log_path)
    try:
        pid = _wait_for_ready(proc)
        os.kill(pid, signal.SIGINT)
        rc = proc.wait(timeout=10)
        assert rc == 0, f"unexpected exit code {rc}; log={log_path.read_text()}"
    finally:
        if proc.poll() is None:
            proc.kill()
            proc.wait(timeout=5)

    count = _count_events(db_path)
    assert count == 50, (
        f"SIGINT dropped events: got {count}/50 in DuckDB. "
        f"log={log_path.read_text()}"
    )


# ── 3. sys.exit(0) — atexit handler drains the ring ────────────────────────


def test_sys_exit_atexit_flushes_ring(tmp_path):
    """No signal — just `sys.exit(0)` from inside the daemon. The atexit
    handler is the only thing that can drain the ring here; this test
    proves it's wired up."""
    db_path = tmp_path / "shutdown.duckdb"
    log_path = tmp_path / "child.log"
    proc = _spawn(tmp_path, _PAYLOAD_INGEST_THEN_SYS_EXIT, log_path)
    try:
        _wait_for_ready(proc)
        rc = proc.wait(timeout=10)
        assert rc == 0, f"unexpected exit code {rc}; log={log_path.read_text()}"
    finally:
        if proc.poll() is None:
            proc.kill()
            proc.wait(timeout=5)

    count = _count_events(db_path)
    assert count == 50, (
        f"sys.exit() dropped events: got {count}/50 in DuckDB. "
        f"log={log_path.read_text()}"
    )


# ── 4. Flush timeout — shutdown completes in <6s with hung flush ───────────


def test_shutdown_timeout_does_not_hang(tmp_path):
    """If the flush hangs, shutdown must NOT wait forever — orchestrator
    SIGKILL after launchd's 30s grace would lose more events than the
    timeout itself. Hard ceiling: 5s flush + small overhead.
    """
    log_path = tmp_path / "child.log"
    proc = _spawn(tmp_path, _PAYLOAD_HUNG_FLUSH, log_path)
    try:
        pid = _wait_for_ready(proc)
        t0 = time.monotonic()
        os.kill(pid, signal.SIGTERM)
        # The hung path uses a 1.5s timeout (set inside the payload) +
        # signal-delivery + thread teardown overhead. 6s gives generous
        # margin while still proving we don't sit on the full 30s sleep.
        rc = proc.wait(timeout=6)
        elapsed = time.monotonic() - t0
    finally:
        if proc.poll() is None:
            proc.kill()
            proc.wait(timeout=5)
            pytest.fail(
                f"shutdown hung past timeout; log={log_path.read_text()}"
            )

    assert rc == 0, f"unexpected exit code {rc}; log={log_path.read_text()}"
    assert elapsed < 6.0, f"shutdown took {elapsed:.2f}s, expected <6s"

    # The abandon-with-warning message lands on stdout (sync.py's
    # logger uses a StreamHandler(sys.stdout)). Drain whatever is still
    # buffered after the child exited.
    remaining = proc.stdout.read() or ""
    assert "exceeded" in remaining and "timeout" in remaining, (
        f"expected timeout-warning log line; got stdout=\n{remaining!r}\n"
        f"stderr=\n{log_path.read_text()!r}"
    )


# ── 5. Re-entrancy guard — double-fire (signal + atexit) flushes once ──────


def test_shutdown_handler_is_reentrant_safe():
    """Unit-level: calling `_graceful_shutdown` twice in the same process
    must not raise, must not deadlock, and must flush exactly once.

    We exercise this in-process (no subprocess) because the second call
    is what atexit triggers AFTER a signal handler already exited via
    `os._exit(0)` — except `os._exit` bypasses atexit, so we manually
    invoke both paths to prove the guard works.
    """
    # Reload so each test gets a fresh `_shutdown_flushed` flag.
    import importlib
    sys.modules.pop("clawmetry.sync", None)
    from clawmetry import sync as _sync
    importlib.reload(_sync)

    calls = {"n": 0}

    def _fake_drain():
        calls["n"] += 1
        return (7, 0.001)

    _sync._drain_local_store_now = _fake_drain
    # force_exit=False so we don't os._exit out of the test.
    _sync._graceful_shutdown("first", force_exit=False)
    _sync._graceful_shutdown("second", force_exit=False)
    assert calls["n"] == 1, f"expected 1 drain, got {calls['n']}"
