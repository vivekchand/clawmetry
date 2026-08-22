"""The repo's own test suite must not ship to users.

Two separate problems, and the second is the one that matters.

**Size.** In 0.12.756 the top-level ``tests/`` package was 958 of the wheel's
1299 entries and 11.3 MB of 28.8 MB uncompressed, or 39%. Every
``pip install clawmetry`` downloaded and unpacked it, and nothing in the shipped
code imports it.

**Correctness.** Several suites here resolve repo-relative paths that are
deliberately not packaged: ``verification/guards.json``,
``verification/matrix.json``, ``scripts/e2e_gate.py``,
``.github/workflows/``. Shipped inside a wheel those tests cannot pass no
matter what a user does.

A check with no path to green is a trap. It teaches whoever meets it that red
is normal, or invites them to weaken the assertion so it passes. Both outcomes
are worse than the check not existing. The compliant fix is to stop shipping
tests that cannot run, never to loosen them so they can.

**This file is deliberately dependency-free.** An earlier draft imported
``setuptools`` to resolve the package list, which is absent from the lint job's
minimal environment, so the guard itself would have errored there. A guard that
cannot run in its own environment is the same trap one level up. The static
declaration is checked here; the empirical half lives in ``ci.yml``'s
wheel-asset job, which already builds and installs a real wheel and now asserts
``import tests`` fails inside it.
"""
from __future__ import annotations

import os
import re

import pytest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SETUP_PY = os.path.join(REPO_ROOT, "setup.py")
CI_WORKFLOW = os.path.join(REPO_ROOT, ".github", "workflows", "ci.yml")


def _read(path: str) -> str:
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def test_setup_py_exists() -> None:
    assert os.path.isfile(SETUP_PY), "setup.py is missing"


def test_find_packages_excludes_the_test_suite() -> None:
    """The declaration must exclude tests, not merely happen to omit them."""
    source = _read(SETUP_PY)
    match = re.search(r"find_packages\(([^)]*)\)", source)
    assert match, "setup.py no longer calls find_packages()"
    args = match.group(1)
    assert "exclude" in args, (
        "setup.py calls find_packages() with no exclude, so the repo test "
        "suite would ship to users again: 39% of the wheel, and several suites "
        "here cannot pass from an installed wheel because they read "
        "verification/, scripts/ and .github/workflows/, none of which are "
        "packaged."
    )
    assert re.search(r"['\"]tests['\"]", args), (
        f"find_packages(exclude=...) no longer excludes tests: {args!r}"
    )


def test_runtime_packages_are_still_declared() -> None:
    """The exclusion must not take anything the product needs with it."""
    source = _read(SETUP_PY)
    for required in ("routes", "helpers"):
        assert f'"{required}"' in source, (
            f"{required} is no longer added to packages. dashboard imports it "
            "at module load, so the wheel would be unusable."
        )
    assert "py_modules=[\"dashboard\"]" in source, (
        "dashboard is no longer shipped as a top-level module."
    )


def test_ci_asserts_the_test_package_is_absent_from_a_real_wheel() -> None:
    """The empirical half must stay wired.

    The static checks above prove the DECLARATION is right. Only building and
    installing a wheel proves the RESULT is right, and ci.yml's wheel-asset job
    already does both, so the negative assertion belongs there rather than in a
    slow new job here.
    """
    source = _read(CI_WORKFLOW)
    assert "purelib" in source, (
        "ci.yml's wheel-asset job must inspect site-packages directly.\n\n"
        "An import-based check does not work here: the step runs from the repo "
        "checkout and `python -c` puts cwd on sys.path, so `import tests` "
        "resolves the SOURCE tree whether or not the wheel contains it. The "
        "first version of this assertion did exactly that and failed a wheel "
        "that was already correct."
    )
    assert "the repo test package is installed in" in source, (
        "ci.yml's wheel-asset job no longer asserts that `import tests` fails "
        "inside an installed wheel. Without it, only the declaration is "
        "checked, and a packaging change elsewhere (MANIFEST.in, "
        "include_package_data, a build backend switch) could put the suite "
        "back into the wheel with this file none the wiser."
    )


@pytest.mark.parametrize(
    "path",
    [
        "verification/guards.json",
        "verification/matrix.json",
        "scripts/e2e_gate.py",
        ".github/workflows",
    ],
)
def test_the_paths_these_tests_need_still_exist_and_are_unpackaged(path: str) -> None:
    """Documents WHY the suite cannot ship: it depends on unpackaged paths.

    If one of these ever became part of the distribution, the reasoning in this
    file would be stale rather than silently wrong.
    """
    assert os.path.exists(os.path.join(REPO_ROOT, path)), (
        f"{path} no longer exists; update this guard to name the real paths "
        "the suite depends on."
    )
    source = _read(SETUP_PY)
    top = path.split("/")[0]
    assert f'packages=find_packages' in source, "packages declaration moved"
    assert f'"{top}"' not in source.split("packages=")[1].split("\n")[0], (
        f"{top} appears in the packages line, so it may now ship. Re-evaluate "
        "whether the test suite can ship after all."
    )
