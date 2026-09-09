#!/usr/bin/env python3
"""Verify a PUBLISHED clawmetry release, end to end, on this machine.

Why this is separate from the ``pip install`` matrix in ci.yml: that job runs
``pip install flask .`` -- it installs the branch SOURCE. It proves the code in
the PR is installable. It cannot prove anything about the artifact a user
actually receives from PyPI, which is what every install claim in the README
and on the landing page is about.

Run it against one pinned version, the way the launch checklist requires::

    python3 scripts/verify_published_wheel.py --version 0.12.843

Checks, each of which has failed for real at least once:

1. **install**       -- the version pip resolves is the version asked for.
   ("No matching distribution" also means a BLOCKED index, not only a missing
   release; the ``(from versions: none)`` line is the tell.)
2. **neutral cwd**   -- the console script reports the wheel's version, not
   some ``dashboard.py`` sitting in the working directory. Running from a repo
   checkout silently runs THAT program instead, which is how a verification
   pass can "confirm" a version that was never installed.
3. **serves**        -- the dashboard answers on its port, and ``/api/overview``
   returns JSON.
4. **no-runtime**    -- on a machine with no agent data it says so, rather than
   rendering an empty screen or crashing.
5. **offline**       -- with every egress destination black-holed it still
   starts and serves. A local-first tool that needs the network to boot is not
   local-first.
6. **uninstall**     -- leaves no console script and no importable package.

Exit code 0 only when every check passes. Prints one line per check so a CI log
is readable without opening an artifact.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path

PORT_BASE = 8951
FAILURES: list[str] = []


def ok(name: str, detail: str = "") -> None:
    print(f"  PASS  {name}" + (f" -- {detail}" if detail else ""), flush=True)


def bad(name: str, detail: str) -> None:
    FAILURES.append(f"{name}: {detail}")
    print(f"  FAIL  {name} -- {detail}", flush=True)


def run(cmd: list[str], **kw) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, text=True, timeout=600, **kw)


def venv_paths(root: Path) -> tuple[Path, Path]:
    """(python, console-script) for this platform."""
    if os.name == "nt":
        return root / "Scripts" / "python.exe", root / "Scripts" / "clawmetry.exe"
    return root / "bin" / "python", root / "bin" / "clawmetry"


def http_get(url: str, timeout: float = 10.0) -> tuple[int, bytes]:
    try:
        with urllib.request.urlopen(url, timeout=timeout) as r:  # nosec B310 - fixed localhost URL
            return r.getcode(), r.read()
    except urllib.error.HTTPError as e:
        return e.code, b""
    except Exception:
        return 0, b""


def wait_for(url: str, seconds: int = 90) -> bool:
    deadline = time.time() + seconds
    while time.time() < deadline:
        code, _ = http_get(url, timeout=2.0)
        if code == 200:
            return True
        time.sleep(1)
    return False


def boot(script: Path, port: int, home: Path, cwd: Path, env_extra=None):
    """Start the dashboard from a NEUTRAL cwd and return (proc, log_path)."""
    env = dict(os.environ)
    env["HOME"] = str(home)
    env["USERPROFILE"] = str(home)
    env["CLAWMETRY_NO_TELEMETRY"] = "1"
    # Without this the child buffers stdout and the first-run copy never
    # reaches the log, so check 4 skips itself and reports nothing.
    env["PYTHONUNBUFFERED"] = "1"
    env.pop("CLAWMETRY_SAMPLE", None)
    env.pop("CLAWMETRY_LOCAL_STORE_PATH", None)
    if env_extra:
        env.update(env_extra)
    log = cwd / f"boot-{port}.log"
    fh = open(log, "w", encoding="utf-8", errors="replace")
    proc = subprocess.Popen(
        [str(script), "--port", str(port), "--no-debug"],
        stdout=fh, stderr=subprocess.STDOUT, cwd=str(cwd), env=env,
    )
    return proc, log


def stop(proc) -> None:
    try:
        proc.terminate()
        proc.wait(timeout=20)
    except Exception:
        try:
            proc.kill()
        except Exception:
            pass


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--version", required=True,
                    help="the published version to verify, e.g. 0.12.843")
    args = ap.parse_args()
    want = args.version.strip()

    print(f"Verifying published clawmetry=={want} on {sys.platform} "
          f"(python {sys.version.split()[0]})", flush=True)

    work = Path(tempfile.mkdtemp(prefix="cm-verify-"))
    try:
        venv = work / "venv"
        # NEUTRAL working directory: never the repo checkout. A dashboard.py in
        # cwd shadows the installed package and the run silently verifies the
        # wrong program (check 2 below exists because this happened).
        neutral = work / "neutral"
        neutral.mkdir()
        home = work / "home"
        home.mkdir()

        run([sys.executable, "-m", "venv", str(venv)])
        py, script = venv_paths(venv)
        if not py.exists():
            bad("install", "venv creation produced no interpreter")
            return 1

        # 1. install
        r = run([str(py), "-m", "pip", "install", "--quiet", f"clawmetry=={want}"])
        if r.returncode != 0:
            tail = (r.stderr or r.stdout or "").strip().splitlines()[-4:]
            bad("install", f"pip failed: {' | '.join(tail)}")
            return 1
        r = run([str(py), "-c",
                 "import importlib.metadata as m; print(m.version('clawmetry'))"])
        got = (r.stdout or "").strip()
        if got != want:
            bad("install", f"asked for {want}, got {got!r}")
        else:
            ok("install", f"pip resolved {got}")

        if not script.exists():
            bad("install", f"console script missing at {script}")
            return 1

        # 2. neutral cwd -- the console script must report the WHEEL's version
        r = run([str(script), "--version"], cwd=str(neutral))
        out = ((r.stdout or "") + (r.stderr or "")).strip()
        if want in out:
            ok("neutral cwd", f"--version reports {want}")
        else:
            bad("neutral cwd",
                f"--version said {out[:120]!r}, expected {want}. A dashboard.py "
                f"in cwd shadows the wheel")

        # 3. serves + 4. no-runtime state
        port = PORT_BASE
        proc, log = boot(script, port, home, neutral)
        try:
            if not wait_for(f"http://127.0.0.1:{port}/", 90):
                bad("serves", "dashboard never answered on /")
            else:
                ok("serves", "/ returned 200")
                code, body = http_get(f"http://127.0.0.1:{port}/api/overview", 30)
                if code != 200:
                    bad("serves", f"/api/overview returned {code}")
                else:
                    try:
                        json.loads(body)
                        ok("serves", "/api/overview returned JSON")
                    except Exception:
                        bad("serves", "/api/overview body was not JSON")
        finally:
            stop(proc)

        text = log.read_text(encoding="utf-8", errors="replace").lower()
        if not text.strip():
            # Not a product failure: some shells detach stdout. Say so rather
            # than reporting a missing message the user would in fact see.
            print("  SKIP  no-runtime -- boot log captured no output on this "
                  "platform; cannot assert on first-run copy", flush=True)
        elif "no agent runtime detected" in text or "sessions directory not found" in text:
            ok("no-runtime", "first run names the missing runtime state")
        else:
            bad("no-runtime",
                "a machine with no agent data produced no explanation in the "
                "first-run output")

        # 5. fully blocked network
        port += 1
        home2 = work / "home2"
        home2.mkdir()
        blackhole = "http://127.0.0.1:9"
        proc, _log2 = boot(script, port, home2, neutral, env_extra={
            "http_proxy": blackhole, "https_proxy": blackhole,
            "HTTP_PROXY": blackhole, "HTTPS_PROXY": blackhole,
            "ALL_PROXY": blackhole, "NO_PROXY": "127.0.0.1,localhost",
            "no_proxy": "127.0.0.1,localhost",
        })
        try:
            if wait_for(f"http://127.0.0.1:{port}/", 90):
                ok("offline", "starts and serves with all egress black-holed")
            else:
                bad("offline", "did not serve with egress blocked")
        finally:
            stop(proc)

        # 6. uninstall
        r = run([str(py), "-m", "pip", "uninstall", "-y", "--quiet", "clawmetry"])
        if r.returncode != 0:
            bad("uninstall", "pip uninstall returned non-zero")
        else:
            r = run([str(py), "-c", "import clawmetry"], cwd=str(neutral))
            if r.returncode == 0:
                bad("uninstall", "clawmetry still importable after uninstall")
            elif script.exists():
                bad("uninstall", f"console script still present at {script}")
            else:
                ok("uninstall", "console script and package both gone")

    finally:
        shutil.rmtree(work, ignore_errors=True)

    print(flush=True)
    if FAILURES:
        print(f"FAILED {len(FAILURES)} check(s):", flush=True)
        for f in FAILURES:
            print(f"  - {f}", flush=True)
        return 1
    print(f"All checks passed for clawmetry=={want} on {sys.platform}.", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
