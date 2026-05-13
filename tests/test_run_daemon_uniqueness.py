"""Regression test for the duplicate ``run_daemon`` shadow in clawmetry/sync.py.

Audit on 2026-05-13 (P0 #2 + P0 #3) found that ``clawmetry/sync.py`` defined
``run_daemon`` twice:

- ~line 4641: the LIVE definition that ``python -m clawmetry.sync`` actually
  executes via the module-level ``if __name__ == "__main__"`` guard.
- ~line 5281: a 24-line dead SHADOW that overwrote the live name at import
  time. ``from clawmetry import sync; sync.run_daemon()`` resolved to this
  shadow, and ``cli.py`` (``clawmetry sync``) called it -- meaning two of the
  three ways to run the daemon executed completely different code paths.

The shadow was deleted in PR ``cleanup/delete-duplicate-run-daemon-2026-05-13``.
This test ensures it doesn't sneak back in (e.g., a future PR copy-pasting a
helper from the bottom of the file).
"""

import inspect


def test_run_daemon_resolves_to_live_definition():
    """``sync.run_daemon`` must resolve to the live def near the top of the
    file (the one that acquires the PID lock, starts the relay thread, etc.),
    not a shadow defined later in the file.
    """
    from clawmetry import sync

    line = inspect.getsourcelines(sync.run_daemon)[1]
    # Threshold bumped 2026-05-13 (#1135) when the v3 underscore parser
    # added ~326 lines above run_daemon. Bumped again 2026-05-13 (#690)
    # when the BOOTSTRAP.md capture helper added ~190 lines above
    # run_daemon. The shadow that prompted this test lived at ~5281 in
    # the pre-cleanup file, so we keep a generous margin above the live def.
    assert line < 5400, (
        f"sync.run_daemon resolves to line {line}, but the live def lives "
        f"near the top of the file. A duplicate def has likely been "
        f"re-introduced further down -- check `grep -n '^def run_daemon' "
        f"clawmetry/sync.py` and delete the shadow."
    )


def test_run_daemon_defined_exactly_once():
    """Belt-and-braces: scan the source file for ``def run_daemon`` at column 0
    and assert there is exactly one occurrence. Catches the regression even if
    someone manages to add a shadow that happens to be picked up first.
    """
    from clawmetry import sync

    src_path = inspect.getsourcefile(sync)
    assert src_path is not None
    with open(src_path, "r", encoding="utf-8") as f:
        src = f.read()
    count = sum(1 for line in src.splitlines() if line.startswith("def run_daemon"))
    assert count == 1, (
        f"Expected exactly one top-level `def run_daemon` in {src_path}, "
        f"found {count}. See tests/test_run_daemon_uniqueness.py docstring "
        f"for the history."
    )
