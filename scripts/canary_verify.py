#!/usr/bin/env python3
"""Verify a PUBLISHED version of clawmetry actually works, from PyPI.

At 5.4 releases a day, every one going to 100% of users the moment it uploads,
perfect pre-publish testing is not on the table. Escapes are arithmetic. What
IS on the table is shrinking the window: detect a bad release in minutes rather
than whenever the first user complains, so the damage is measured in
user-minutes instead of user-days.

This runs AFTER publication against the real index, which is a different
question from the pre-publish smoke. That one tests the wheel that was built;
this one tests the artifact users receive, and catches the gap between them:
upload corruption, index propagation, a dependency that resolves differently on
a clean machine, a platform-specific wheel that never got built.

Deliberately NOT auto-yanking. FLYWHEEL makes yanking manual so a human signs
off, and that is the right call: an automated yank on a false positive is worse
than the bad release. This prints the exact command instead, so the human
decision takes seconds rather than research.

Usage::

    python3 scripts/canary_verify.py --version 0.12.748
    python3 scripts/canary_verify.py --latest
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request

PYPI_JSON = "https://pypi.org/pypi/clawmetry/json"

# Every subcommand a user can reach. `uninstall` is on this list deliberately:
# when 0.12.753 died at import, it took uninstall with it, so affected users had
# no supported way OFF the product. A release that cannot be uninstalled is a
# strictly worse failure than one that merely does not work.
SUBCOMMANDS = ("status", "sync", "connect", "uninstall")


def latest_version(timeout: int = 30) -> str:
    with urllib.request.urlopen(PYPI_JSON, timeout=timeout) as resp:
        return json.loads(resp.read())["info"]["version"]


def version_is_available(version: str, timeout: int = 30) -> bool:
    """Is this version visible on the JSON API yet?

    The JSON API and the simple index do not propagate together; the JSON API
    routinely shows a version minutes before `pip install` can resolve it. That
    race has already broken cloud Docker builds and image builds, so treat this
    as a hint, never as proof -- the install below is the real check.
    """
    try:
        with urllib.request.urlopen(PYPI_JSON, timeout=timeout) as resp:
            data = json.loads(resp.read())
        return version in (data.get("releases") or {})
    except urllib.error.URLError:
        return False


def _run(cmd: list, timeout: int = 300) -> tuple:
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    return proc.returncode, (proc.stdout or "") + (proc.stderr or "")


def verify(version: str, verbose: bool = True) -> list:
    """Install the published version into a throwaway venv and exercise it.

    Returns a list of failure strings; empty means the release is healthy.
    """
    failures: list = []

    with tempfile.TemporaryDirectory(prefix="cm-canary-") as tmp:
        venv_dir = f"{tmp}/venv"
        code, out = _run([sys.executable, "-m", "venv", venv_dir])
        if code != 0:
            return [f"could not create venv: {out[-400:]}"]

        py = f"{venv_dir}/bin/python"
        cli = f"{venv_dir}/bin/clawmetry"

        if verbose:
            print(f"  installing clawmetry=={version} from PyPI ...")
        code, out = _run(
            [py, "-m", "pip", "install", "--no-cache-dir", f"clawmetry=={version}"],
            timeout=900,
        )
        if code != 0:
            return [f"pip install clawmetry=={version} FAILED:\n{out[-1200:]}"]

        # A resolvable install is not a working one. This is the exact gap
        # 0.12.753 fell through: pip succeeded, then every entry point died.
        checks = [
            (
                "import clawmetry",
                [py, "-c", "import clawmetry; print(clawmetry.__file__)"],
            ),
            (
                "import clawmetry.cli",
                [py, "-c", "import clawmetry.cli; print('cli ok')"],
            ),
            ("clawmetry --version", [cli, "--version"]),
            ("clawmetry --help", [cli, "--help"]),
        ]
        for label, cmd in checks:
            code, out = _run(cmd)
            if code != 0:
                failures.append(f"{label} FAILED:\n{out[-600:]}")
            elif verbose:
                print(f"    ok: {label}")

        for sub in SUBCOMMANDS:
            code, out = _run([cli, sub, "--help"])
            if code != 0:
                failures.append(
                    f"clawmetry {sub} --help FAILED (dead at import?):\n{out[-400:]}"
                )
            elif verbose:
                print(f"    ok: clawmetry {sub} --help")

    return failures


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    group = ap.add_mutually_exclusive_group(required=True)
    group.add_argument("--version", help="the published version to verify")
    group.add_argument(
        "--latest", action="store_true", help="verify whatever PyPI calls latest"
    )
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()

    try:
        version = latest_version() if args.latest else args.version
    except Exception as exc:  # noqa: BLE001
        print(f"FAIL: could not reach PyPI: {exc}")
        return 2

    print(f"Canary: verifying published clawmetry=={version}")
    failures = verify(version, verbose=not args.quiet)

    if not failures:
        print(f"\nPASS: clawmetry=={version} installs and runs from PyPI.")
        return 0

    print(f"\nFAIL: clawmetry=={version} is BROKEN for users installing right now.")
    print("=" * 72)
    for failure in failures:
        print(f"  * {failure}")
    print("=" * 72)
    print("\nThis release is live on PyPI and every new install gets it.")
    print("Decide now: hotfix forward, or yank.")
    print("\nYank (a human signs this off deliberately -- see FLYWHEEL):")
    print(f"    https://pypi.org/manage/project/clawmetry/release/{version}/")
    print("\nA yank stops NEW installs resolving this version. It does not")
    print("repair machines that already installed it, so ship the hotfix too.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
