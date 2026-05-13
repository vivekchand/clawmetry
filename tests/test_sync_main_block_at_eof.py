"""Regression test for the dead-code-after-__main__ bug in clawmetry/sync.py.

Background
----------
Between 0.12.179 and 0.12.x (this fix), `clawmetry/sync.py` had module-level
constants and functions defined AFTER the `if __name__ == "__main__":` block.
Because that block calls `run_daemon()` which never returns, every `python -m
clawmetry.sync` invocation skipped those definitions, and the daemon then
NameError'd every ~15s on `ALERTS_EVAL_INTERVAL_SEC` (PRD #779 alerts evaluator)
and silently stopped running `sync_autonomy`.

This test enforces, at the source level, that no top-level (non-indented,
non-blank, non-comment) statement may appear after the `if __name__ == "__main__":`
guard.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

SYNC_PY = Path(__file__).resolve().parent.parent / "clawmetry" / "sync.py"


def _read_source_lines() -> list[str]:
    return SYNC_PY.read_text().splitlines()


def test_sync_py_exists():
    assert SYNC_PY.exists(), f"{SYNC_PY} not found"


def test_main_block_is_last_top_level_statement():
    """No top-level (column-0) statement may follow `if __name__ == "__main__":`."""
    lines = _read_source_lines()

    main_idx = None
    for i, line in enumerate(lines):
        if line.startswith('if __name__ == "__main__":'):
            main_idx = i
            break

    assert main_idx is not None, (
        '`if __name__ == "__main__":` block not found in clawmetry/sync.py'
    )

    # Everything after main_idx must be either:
    #   - blank, or
    #   - a comment line (starts with '#'), or
    #   - indented (part of the block body)
    offenders: list[tuple[int, str]] = []
    for j in range(main_idx + 1, len(lines)):
        line = lines[j]
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("#"):
            continue
        if line.startswith((" ", "\t")):
            continue  # indented = part of __main__ block body
        offenders.append((j + 1, line))

    assert not offenders, (
        "Found top-level statement(s) AFTER `if __name__ == \"__main__\":` block. "
        "These will NEVER execute when running `python -m clawmetry.sync` because "
        "run_daemon() is an infinite loop. Move them ABOVE the __main__ block:\n"
        + "\n".join(f"  line {ln}: {src!r}" for ln, src in offenders[:10])
    )


def test_alerts_and_autonomy_symbols_importable():
    """Direct-import sanity check: these names must resolve when the module is imported."""
    import clawmetry.sync as sync  # noqa: WPS433 (intentional late import)

    for attr in ("ALERTS_EVAL_INTERVAL_SEC", "evaluate_alerts", "sync_autonomy"):
        assert hasattr(sync, attr), (
            f"clawmetry.sync.{attr} is missing — alerts evaluator / autonomy "
            f"sync would silently fail."
        )


def test_subprocess_can_resolve_alerts_constant():
    """A child process must be able to import the module and read the constant.

    This is the same import path the daemon uses on cold start, sans the
    `if __name__ == "__main__":` trigger.
    """
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "import clawmetry.sync as s; "
            "assert s.ALERTS_EVAL_INTERVAL_SEC == 60, s.ALERTS_EVAL_INTERVAL_SEC; "
            "assert callable(s.evaluate_alerts); "
            "assert callable(s.sync_autonomy); "
            "print('OK')",
        ],
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, (
        f"subprocess import failed.\nstdout={result.stdout!r}\nstderr={result.stderr!r}"
    )
    assert "NameError" not in result.stderr, result.stderr
    assert "OK" in result.stdout


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-q"]))
