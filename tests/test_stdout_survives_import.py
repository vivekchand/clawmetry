"""Regression guard: importing dashboard must not close sys.stdout.

dashboard.py's "Force UTF-8 output on Windows" blocks used to rebind
sys.stdout / sys.stderr to fresh io.TextIOWrapper objects around the same
underlying buffer. The module header appears twice in the file, so the
second rebind orphaned the first wrapper; when the garbage collector
finalized the orphan it closed the SHARED buffer, leaving sys.stdout
closed for the rest of the process. Net effect on Windows: `clawmetry
--help` printed nothing and exited 0, because clawmetry/cli.py's
closed-handle guard then swapped the dead stream for a devnull sink.
Fix: sys.stdout.reconfigure() in place, which is idempotent and never
orphans a wrapper.

Both tests run in a subprocess: the bug only manifests on a pristine
import, and pytest's capture machinery would mask it in-process.
"""
import os
import subprocess
import sys

import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def _run(argv):
    env = dict(os.environ)
    env["CLAWMETRY_NO_TELEMETRY"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"
    return subprocess.run(
        argv,
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        encoding="utf-8",
        errors="replace",
        timeout=180,
    )


def test_import_dashboard_keeps_stdout_open():
    """A bare `import dashboard` must leave sys.stdout writable."""
    code = (
        "import gc, sys\n"
        "import dashboard\n"
        "gc.collect()\n"  # force-finalize any orphaned TextIOWrapper
        "assert not sys.stdout.closed, 'dashboard import closed sys.stdout'\n"
        "assert not sys.stderr.closed, 'dashboard import closed sys.stderr'\n"
        "print('STDOUT_ALIVE')\n"
    )
    proc = _run([sys.executable, "-c", code])
    assert proc.returncode == 0, f"stderr:\n{proc.stderr}"
    assert "STDOUT_ALIVE" in proc.stdout, (
        "print() after importing dashboard produced no output -- "
        f"stdout was closed or redirected. stderr:\n{proc.stderr}"
    )


def test_cli_help_prints_usage():
    """`clawmetry --help` must print usage text and exit 0 (was: silent)."""
    proc = _run([sys.executable, "-m", "clawmetry", "--help"])
    assert proc.returncode == 0, f"stderr:\n{proc.stderr}"
    assert "usage" in proc.stdout.lower(), (
        "--help printed nothing -- the closed-stdout-on-import bug is back. "
        f"stdout={proc.stdout!r} stderr:\n{proc.stderr}"
    )
    assert "clawmetry" in proc.stdout.lower()


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
