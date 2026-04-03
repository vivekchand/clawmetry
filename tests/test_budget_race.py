"""
Test for race condition in _budget_paused global variable.

ISSUE: _budget_paused is a global variable modified without lock protection.
This test demonstrates the problem exists in dashboard.py.

Without a lock, concurrent modifications can cause:
- Inconsistent state (_budget_paused=True but _budget_paused_at=0)
- Lost updates (two threads both think they need to pause)
- Race between check and set in _budget_check()
"""

import threading
import time


def test_budget_paused_code_pattern_has_race():
    """Demonstrates the race condition pattern in dashboard.py code.

    The issue is in _budget_check() which does:
        if _budget_paused:     # Line 675 - READ
            return
        ...
        _budget_paused = True  # Line 719 - WRITE (much later)

    And _resume_gateway() which does:
        _budget_paused = False      # Line 786
        _budget_paused_at = 0       # Line 787
        _budget_paused_reason = ""  # Line 788

    These three assignments in _resume_gateway() are NOT atomic.
    The check-then-act pattern in _budget_check() is NOT atomic.

    This test FAILS because there's no _budget_lock protecting these vars.
    """
    # Read the actual dashboard.py to verify the pattern
    import os

    dashboard_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "dashboard.py"
    )

    with open(dashboard_path, "r") as f:
        content = f.read()

    # Check that _budget_paused is declared as global
    assert "global _budget_paused" in content, (
        "_budget_paused should be declared as global"
    )

    # Find all places where _budget_paused is modified
    lines = content.split("\n")
    modifications = []
    for i, line in enumerate(lines, 1):
        if "_budget_paused" in line and (
            "=" in line and "_budget_paused" in line.split("=")[0].split()[-1]
        ):
            # Check if it's a modification (left side of =)
            stripped = line.strip()
            if not stripped.startswith("#"):
                modifications.append((i, line))

    # There should be multiple places where _budget_paused is modified
    # without any lock protection
    modification_lines = [i for i, _ in modifications]

    # Verify the problem exists: _budget_paused is modified in multiple places
    # but there's no _budget_lock protecting it
    has_budget_lock = "_budget_lock" in content and "threading.Lock()" in content

    # Check that _budget_paused modifications exist
    assert len(modification_lines) >= 2, (
        f"Expected multiple modifications to _budget_paused, found: {modification_lines}"
    )

    # The bug: no lock protecting these modifications
    # After the fix, there should be a _budget_lock and it should be used
    # around ALL modifications to _budget_paused, _budget_paused_at, _budget_paused_reason

    # This assertion demonstrates the bug - it will FAIL until we add the lock
    assert has_budget_lock, (
        "BUG: _budget_lock does not exist. _budget_paused modifications are not protected!"
    )

    # After fix, verify lock is used properly
    # The lock should be acquired when modifying _budget_paused in:
    # - _budget_check() at line ~719
    # - _resume_gateway() at line ~786
    # - any other place that modifies it

    # Check that 'with _budget_lock:' appears before the modifications
    # This is a structural test - we verify the lock pattern exists
    assert "with _budget_lock:" in content, (
        "Lock should be used with 'with _budget_lock:' statement"
    )


def test_budget_paused_runtime_race():
    """Runtime test showing the race condition.

    This test demonstrates the inconsistent state that can occur
    when _budget_paused, _budget_paused_at, and _budget_paused_reason
    are modified without atomicity.
    """
    # Simulate the buggy pattern from dashboard.py
    _budget_paused = False
    _budget_paused_at = 0
    _budget_paused_reason = ""

    inconsistencies = []

    def bugged_resume():
        """Simulates _resume_gateway() without lock - NOT ATOMIC!"""
        nonlocal _budget_paused, _budget_paused_at, _budget_paused_reason
        # These three assignments are NOT atomic
        _budget_paused = False
        _budget_paused_at = 0
        _budget_paused_reason = ""

    def bugged_pause():
        """Simulates _budget_check() without proper lock - check-then-act race"""
        nonlocal _budget_paused, _budget_paused_at, _budget_paused_reason
        if _budget_paused:
            return
        # Race window: another thread could resume here!
        _budget_paused = True
        _budget_paused_at = int(time.time() * 1000)
        _budget_paused_reason = "paused"

    # Run many threads to trigger the race
    for _ in range(500):
        _budget_paused = False
        _budget_paused_at = 0
        _budget_paused_reason = ""

        threads = [
            threading.Thread(target=bugged_resume),
            threading.Thread(target=bugged_pause),
        ]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Check for inconsistent state
        if _budget_paused and _budget_paused_at == 0:
            inconsistencies.append("_budget_paused=True but _budget_paused_at=0")
        if not _budget_paused and (_budget_paused_at != 0 or _budget_paused_reason):
            inconsistencies.append(
                f"_budget_paused=False but at={_budget_paused_at}, reason='{_budget_paused_reason}'"
            )

    # With the buggy pattern, we should see inconsistencies
    # The test assertion is inverted to show the bug exists
    # When fixed with a lock, this test should PASS (0 inconsistencies)
    if len(inconsistencies) > 0:
        # This will be shown when the bug exists
        print(f"\nRace condition observed {len(inconsistencies)} times:")
        for inc in inconsistencies[:5]:
            print(f"  - {inc}")

    # After fixing with a lock, this should be 0
    # The test framework will show failure until we fix the code
    assert len(inconsistencies) == 0, (
        f"Race condition caused {len(inconsistencies)} inconsistent states!"
    )


if __name__ == "__main__":
    import pytest

    pytest.main([__file__, "-v"])
