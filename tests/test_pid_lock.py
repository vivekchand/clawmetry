"""
Test PID lock race condition in sync.py _acquire_pid_lock()

This test demonstrates the TOCTOU race: between pid_path.exists() check
and pid_path.write_text(), another process can create the file.
"""

import os
import sys
import time
import signal
import tempfile
import multiprocessing
from pathlib import Path

import pytest


def _acquire_pid_lock_vulnerable(pid_path_str: str) -> bool:
    """Vulnerable version that demonstrates the TOCTOU race."""
    from pathlib import Path

    pid_path = Path(pid_path_str)
    pid_path.parent.mkdir(parents=True, exist_ok=True)
    if pid_path.exists():  # TOCTOU: check
        try:
            existing_pid = int(pid_path.read_text().strip())
            os.kill(existing_pid, 0)
            return False
        except (ProcessLookupError, ValueError):
            pass
    # Race window here: another process can create the file between the check and write
    time.sleep(0.1)  # Simulates the race window
    pid_path.write_text(str(os.getpid()))
    return True


def _acquire_pid_lock_fixed(pid_path_str: str) -> bool:
    """Fixed version using O_CREAT|O_EXCL for atomic creation."""
    pid_path = Path(pid_path_str)
    pid_path.parent.mkdir(parents=True, exist_ok=True)
    flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY
    try:
        fd = os.open(str(pid_path), flags, 0o644)
        os.write(fd, str(os.getpid()).encode())
        os.close(fd)
        return True
    except FileExistsError:
        return False


def worker_vulnerable(ready_event, start_event, pid_path_str, results, idx):
    """Worker process using vulnerable lock."""
    ready_event.set()
    start_event.wait()
    result = _acquire_pid_lock_vulnerable(pid_path_str)
    results[idx] = result


def worker_fixed(ready_event, start_event, pid_path_str, results, idx):
    """Worker process using fixed lock."""
    ready_event.set()
    start_event.wait()
    result = _acquire_pid_lock_fixed(pid_path_str)
    results[idx] = result


def worker_actual_sync(
    ready_event, start_event, pid_path_str, results, idx, original_pid_file_func
):
    """Worker process using the actual _acquire_pid_lock from sync module."""
    import clawmetry.sync as sync

    # Monkeypatch the pid file path
    original = sync._pid_file
    sync._pid_file = lambda: Path(pid_path_str)

    ready_event.set()
    start_event.wait()

    result = sync._acquire_pid_lock()
    results[idx] = result

    # Restore
    sync._pid_file = original


def test_pid_lock_vulnerable_implementation_has_race(tmp_path):
    """
    Test that demonstrates the race: two processes both succeed with vulnerable lock.

    The vulnerable implementation has a TOCTOU race between exists() check and write_text().
    This test asserts that the race CAN occur (at least once in many trials).
    """
    pid_path = tmp_path / "sync.pid"
    pid_path_str = str(pid_path)

    num_trials = 50
    race_detected = 0

    for trial in range(num_trials):
        # Reset state
        if pid_path.exists():
            pid_path.unlink()

        manager = multiprocessing.Manager()
        results = manager.list([None, None])

        ready_events = [multiprocessing.Event() for _ in range(2)]
        start_event = multiprocessing.Event()

        # Two processes trying to acquire the lock simultaneously
        p1 = multiprocessing.Process(
            target=worker_vulnerable,
            args=(ready_events[0], start_event, pid_path_str, results, 0),
        )
        p2 = multiprocessing.Process(
            target=worker_vulnerable,
            args=(ready_events[1], start_event, pid_path_str, results, 1),
        )

        p1.start()
        p2.start()

        # Wait for both to be ready
        for e in ready_events:
            e.wait()

        # Signal both to start at the same time
        start_event.set()

        p1.join(timeout=5)
        p2.join(timeout=5)

        # Count how many succeeded
        successes = sum(1 for r in results if r is True)

        # With the race, both processes might succeed (both get the lock)
        if successes == 2:
            race_detected += 1

        p1.terminate()
        p2.terminate()

    # The race should be detected at least once in 50 trials
    # This assertion verifies the vulnerable implementation is indeed vulnerable
    assert race_detected > 0, (
        f"Vulnerable implementation race not detected in {num_trials} trials"
    )


def test_pid_lock_fixed_implementation_prevents_race(tmp_path):
    """
    Test that the fixed implementation using O_CREAT|O_EXCL prevents the race.
    Only one process should ever succeed in acquiring the lock.
    """
    pid_path = tmp_path / "sync.pid"
    pid_path_str = str(pid_path)

    num_trials = 50
    both_succeeded = 0

    for trial in range(num_trials):
        # Reset state
        if pid_path.exists():
            pid_path.unlink()

        manager = multiprocessing.Manager()
        results = manager.list([None, None])

        ready_events = [multiprocessing.Event() for _ in range(2)]
        start_event = multiprocessing.Event()

        # Two processes trying to acquire the lock simultaneously
        p1 = multiprocessing.Process(
            target=worker_fixed,
            args=(ready_events[0], start_event, pid_path_str, results, 0),
        )
        p2 = multiprocessing.Process(
            target=worker_fixed,
            args=(ready_events[1], start_event, pid_path_str, results, 1),
        )

        p1.start()
        p2.start()

        # Wait for both to be ready
        for e in ready_events:
            e.wait()

        # Signal both to start at the same time
        start_event.set()

        p1.join(timeout=5)
        p2.join(timeout=5)

        # Count how many succeeded
        successes = sum(1 for r in results if r is True)

        # With the fix, exactly one should succeed
        if successes == 2:
            both_succeeded += 1

        p1.terminate()
        p2.terminate()

    # The fixed implementation should never allow both to succeed
    assert both_succeeded == 0, (
        f"Race condition still present: {both_succeeded}/{num_trials} trials "
        "had both processes succeed"
    )


def test_sync_pid_lock_has_race_condition(tmp_path):
    """
    Test that the actual _acquire_pid_lock in sync.py has the TOCTOU race.

    This test FAILS with the vulnerable code and PASSES after the fix.
    It verifies that when two processes race, the atomic O_CREAT|O_EXCL
    is used to prevent both from acquiring the lock.
    """
    import clawmetry.sync as sync

    pid_path = tmp_path / "sync.pid"
    pid_path_str = str(pid_path)

    num_trials = 50
    both_succeeded = 0

    for trial in range(num_trials):
        # Reset state
        if pid_path.exists():
            pid_path.unlink()

        manager = multiprocessing.Manager()
        results = manager.list([None, None])

        ready_events = [multiprocessing.Event() for _ in range(2)]
        start_event = multiprocessing.Event()

        # Two processes trying to acquire the lock simultaneously
        p1 = multiprocessing.Process(
            target=worker_actual_sync,
            args=(
                ready_events[0],
                start_event,
                pid_path_str,
                results,
                0,
                sync._pid_file,
            ),
        )
        p2 = multiprocessing.Process(
            target=worker_actual_sync,
            args=(
                ready_events[1],
                start_event,
                pid_path_str,
                results,
                1,
                sync._pid_file,
            ),
        )

        p1.start()
        p2.start()

        # Wait for both to be ready
        for e in ready_events:
            e.wait()

        # Signal both to start at the same time
        start_event.set()

        p1.join(timeout=5)
        p2.join(timeout=5)

        # Count how many succeeded
        successes = sum(1 for r in results if r is True)

        if successes == 2:
            both_succeeded += 1

        p1.terminate()
        p2.terminate()

        # Clean up PID file
        if pid_path.exists():
            pid_path.unlink()

    # After fix: both processes should NEVER succeed simultaneously
    # Before fix: the race allows both to succeed
    assert both_succeeded == 0, (
        f"TOCTOU race detected in sync.py:_acquire_pid_lock: "
        f"{both_succeeded}/{num_trials} trials had both processes succeed. "
        "The function must use O_CREAT|O_EXCL for atomic file creation."
    )
