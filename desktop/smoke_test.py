#!/usr/bin/env python3
"""Launch a BUILT desktop artifact and fail if it isn't healthy.

Every desktop bug that reached users so far was invisible to the build:
`pyinstaller` exits 0, the artifact uploads, the release publishes, and
the app is broken the moment someone double-clicks it.

    2026-08-08  frozen binary couldn't `import gi` at all
                (system python3-gi built for the wrong ABI)
    2026-08-12  every HTTPS POST failed CERTIFICATE_VERIFY_FAILED
                (no CA bundle in the .app)
    2026-08-15  black window, one traceback per page load
                (PyGObject overrides silently absent — build_linux.spec)

None of those were detectable by a unit test, because none of them
exist outside a frozen bundle. What they share is that *running the
artifact for ten seconds* would have caught all three. That is what
this script does, in CI, on all three platforms, before upload.

    python desktop/smoke_test.py dist/clawmetry/clawmetry
    python desktop/smoke_test.py dist/ClawMetry.app
    python desktop/smoke_test.py dist\\ClawMetry\\ClawMetry.exe
    python desktop/smoke_test.py dist/clawmetry-linux.AppImage

The artifact is launched with CLAWMETRY_DESKTOP_SELFTEST=1, which puts
`desktop/app.py` into a mode that opens a real window, loads the real
onboarding page, round-trips through JS and quits (see `_run_self_test`
there). This script judges the result:

  * exit code must be 0
  * output must contain CLAWMETRY_SELFTEST_OK
  * output must contain no CLAWMETRY_SELFTEST_FAIL line
  * output must contain no Python traceback

That last rule is the load-bearing one. GUI toolkits catch exceptions
raised inside their own callbacks and *print* them — the process stays
alive with exit code 0, which is exactly how a black window shipped as
a green build. Any traceback at all fails the run.
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

MARKER_OK = "CLAWMETRY_SELFTEST_OK"
MARKER_FAIL = "CLAWMETRY_SELFTEST_FAIL"
MARKER_TRACEBACK = "Traceback (most recent call last)"

DEFAULT_TIMEOUT_SECS = 180


def resolve_executable(target: Path) -> Path:
    """Accept whatever shape the platform's build step produced."""
    if target.suffix == ".app":  # macOS bundle
        macos = target / "Contents" / "MacOS"
        candidates = sorted(p for p in macos.iterdir() if p.is_file()) \
            if macos.is_dir() else []
        if not candidates:
            raise SystemExit(f"no executable inside {macos}")
        # Prefer the one named after the bundle; fall back to the only one.
        named = macos / target.stem
        return named if named.exists() else candidates[0]
    if target.is_dir():  # PyInstaller COLLECT folder
        for name in ("clawmetry", "ClawMetry", "ClawMetry.exe", "clawmetry.exe"):
            if (target / name).is_file():
                return target / name
        raise SystemExit(f"no known executable inside {target}")
    if not target.is_file():
        raise SystemExit(f"not found: {target}")
    return target


def build_env(scratch: Path) -> dict:
    """Isolate the run from any real ClawMetry install on the machine.

    `_runtime_dir()` in app.py mkdir's its per-user app-data directory on
    import path, so point every OS's app-data root at a throwaway dir —
    a smoke test must never adopt (or clobber) a developer's runtime venv
    and sign-in token."""
    env = dict(os.environ)
    env["CLAWMETRY_DESKTOP_SELFTEST"] = "1"
    env["HOME"] = str(scratch)
    env["XDG_DATA_HOME"] = str(scratch / "share")       # Linux
    env["LOCALAPPDATA"] = str(scratch / "AppData")      # Windows
    env["USERPROFILE"] = str(scratch)                   # Windows
    # WebKitGTK picks a GPU path that needs a real compositor; both of
    # these are no-ops off Linux and keep Xvfb runs from hanging.
    env.setdefault("WEBKIT_DISABLE_COMPOSITING_MODE", "1")
    env.setdefault("WEBKIT_DISABLE_DMABUF_RENDERER", "1")
    # AppImages need FUSE unless told to unpack themselves first, and CI
    # containers rarely have it.
    env.setdefault("APPIMAGE_EXTRACT_AND_RUN", "1")
    return env


def wrap_headless(cmd: list) -> list:
    """On a Linux box with no display, run under Xvfb."""
    if not sys.platform.startswith("linux"):
        return cmd
    if os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY"):
        return cmd
    xvfb = shutil.which("xvfb-run")
    if not xvfb:
        raise SystemExit(
            "no DISPLAY and no xvfb-run — install xvfb to smoke test headless"
        )
    return [xvfb, "-a", *cmd]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("target", type=Path,
                        help="built executable, COLLECT dir, .app or .AppImage")
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT_SECS,
                        help=f"seconds before the run is killed "
                             f"(default {DEFAULT_TIMEOUT_SECS})")
    args = parser.parse_args()

    exe = resolve_executable(args.target.resolve())
    if not os.access(exe, os.X_OK):  # AppImages arrive without +x from CI
        exe.chmod(exe.stat().st_mode | 0o111)

    with tempfile.TemporaryDirectory(prefix="clawmetry-smoke-") as tmp:
        scratch = Path(tmp)
        cmd = wrap_headless([str(exe)])
        print(f"[smoke] running {' '.join(cmd)}", flush=True)
        try:
            proc = subprocess.run(
                cmd,
                env=build_env(scratch),
                cwd=scratch,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                timeout=args.timeout,
                text=True,
                errors="replace",
            )
            output, code = proc.stdout, proc.returncode
        except subprocess.TimeoutExpired as expired:
            output = expired.output or ""
            if isinstance(output, bytes):
                output = output.decode("utf-8", "replace")
            code = None

    print("[smoke] ---- artifact output ----")
    print(output.rstrip() or "(no output)")
    print("[smoke] ---------------------------")

    failures = []
    if code is None:
        failures.append(
            f"the app never exited within {args.timeout}s — the self test "
            "hangs, which usually means the window never finished loading"
        )
    elif code != 0:
        failures.append(f"exit code {code}, expected 0")
    if MARKER_TRACEBACK in output:
        failures.append(
            "a Python traceback was printed — GUI toolkits swallow "
            "exceptions raised in their callbacks, so this is a real crash "
            "even though the process survived it"
        )
    for line in output.splitlines():
        if MARKER_FAIL in line:
            failures.append(line.strip())
    if MARKER_OK not in output:
        failures.append(f"{MARKER_OK} was never printed")

    if failures:
        print(f"[smoke] FAILED ({exe})", file=sys.stderr)
        for failure in failures:
            print(f"[smoke]   - {failure}", file=sys.stderr)
        return 1

    print(f"[smoke] OK — {exe} opens a window and runs JS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
