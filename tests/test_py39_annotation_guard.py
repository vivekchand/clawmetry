"""Regression guard: the shipped modules must import on Python 3.9.

0.12.753 shipped ``def _get_nemoclaw_preset_script() -> str | None:`` at
module scope in ``clawmetry/cli.py``. PEP 604 unions *parse* on 3.9 but the
3.9 runtime raises ``TypeError: unsupported operand type(s) for |`` when the
signature is evaluated at ``def`` time, so every ``clawmetry`` subcommand —
including ``clawmetry uninstall`` — died before ``main()`` was reached on the
macOS desktop bundle's 3.9 venv and on any 3.9 pip install.

Three CI gates had a clear line of sight and all three missed it: the lint
gate only calls ``ast.parse`` (PEP 604 parses fine on 3.9), the 3.9 test leg
runs ``tests/test_api.py`` only and never imports the CLI, and
``install-test.yml`` smoke-tests ``clawmetry --version`` on 3.12 only.

This test drives ``scripts/check_py39_annotations.py`` over every module the
wheel imports, so the class is caught under ``make test`` as well as in CI.
"""
from __future__ import annotations

import importlib.util
import os
import subprocess
import textwrap

import pytest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT = os.path.join(REPO, "scripts", "check_py39_annotations.py")


def _guard():
    spec = importlib.util.spec_from_file_location("check_py39_annotations", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_no_py39_fatal_unions_in_shipped_modules():
    findings = _guard().check(REPO)
    assert not findings, "PEP 604 unions Python 3.9 evaluates at import time:\n" + "\n".join(
        f"  {f['file']}:{f['line']}: {f['expr']} ({f['why']})" for f in findings
    )


def test_guard_catches_a_signature_union(tmp_path):
    """The gate has to fail on the exact shape that shipped in 0.12.753."""
    guard = _guard()
    src = "def _get_nemoclaw_preset_script() -> str | None:\n    return None\n"
    findings = guard._scan_source("clawmetry/cli.py", src)
    assert [f["kind"] for f in findings] == ["signature"], findings


def test_future_import_excuses_signature_but_not_a_type_alias():
    guard = _guard()
    src = textwrap.dedent(
        """
        from __future__ import annotations

        Maybe = str | None            # evaluated -> still fatal on 3.9

        def f(x: str | None) -> int | None:   # deferred -> fine
            y: dict | None = None
            return None
        """
    )
    kinds = [f["kind"] for f in guard._scan_source("m.py", src)]
    assert kinds == ["runtime-expression"], kinds


def test_ordinary_bitwise_or_is_not_flagged():
    """`FREE_RUNTIMES | PAID_RUNTIMES` is a set union, not a type union."""
    guard = _guard()
    src = "ALL = FREE_RUNTIMES | PAID_RUNTIMES\nMASK = FLAG_A | FLAG_B\n"
    assert guard._scan_source("m.py", src) == []


@pytest.mark.skipif(
    not os.path.exists("/usr/bin/python3"), reason="no system python3 to probe"
)
def test_cli_imports_under_python39_when_available():
    """Empirical leg: import the CLI under a real 3.9 if this box has one."""
    probe = subprocess.run(
        ["/usr/bin/python3", "-c", "import sys; print('%d.%d' % sys.version_info[:2])"],
        capture_output=True, text=True,
    )
    if probe.returncode != 0 or probe.stdout.strip() != "3.9":
        pytest.skip(f"system python3 is {probe.stdout.strip() or 'unavailable'}, not 3.9")
    env = dict(os.environ, PYTHONPATH=REPO)
    run = subprocess.run(
        ["/usr/bin/python3", "-c", "import clawmetry.cli"],
        cwd=os.path.dirname(REPO), env=env, capture_output=True, text=True,
    )
    assert run.returncode == 0, run.stderr[-2000:]
