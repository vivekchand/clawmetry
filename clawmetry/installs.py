"""
Install census — find every clawmetry copy on this machine and flag stale ones.

The auto-updater keeps exactly ONE environment current: the one the supervised
sync daemon runs from (the installer's venv at ``~/.clawmetry``). Any other
copy (a ``pip install --user`` from before the venv existed, a system-python
install, a stray pyenv shim) is inert files that no updater thread ever runs
in — and when such a copy shadows the venv binary on PATH, ``clawmetry
--version`` / ``clawmetry status`` report a stale version while the daemon is
actually up to date. That mismatch reads as "auto-update is broken" (founder
live-hit 2026-07-31: PATH resolved to a Python 3.9 user install at 0.12.601
while the daemon venv ran 0.12.606).

This module detects that state cheaply (directory globs, no subprocess) so the
CLI can warn on startup, ``status`` can report both versions honestly, and
``clawmetry doctor`` can print the exact fix. Never raises — every helper
degrades to ``None`` / empty on any error.
"""
from __future__ import annotations

import os
import re
import sys
from pathlib import Path

_DIST_INFO_RE = re.compile(r"^clawmetry-(\d[\w.]*)\.dist-info$")


def daemon_home() -> Path:
    """The daemon's install root (the installer venv), ``~/.clawmetry``."""
    return Path.home() / ".clawmetry"


def parse_version(v) -> tuple:
    """Tolerant version tuple for comparison; non-numeric parts become 0."""
    parts = []
    for piece in str(v or "").split("."):
        m = re.match(r"\d+", piece)
        parts.append(int(m.group(0)) if m else 0)
    return tuple(parts) if parts else (0,)


def version_gt(a, b) -> bool:
    """True when version string ``a`` is strictly newer than ``b``."""
    return parse_version(a) > parse_version(b)


def daemon_env_version(home: Path = None) -> str | None:
    """clawmetry version installed in the daemon venv, from dist-info dirs.

    Reads the ``clawmetry-<version>.dist-info`` directory name under the
    venv's site-packages (POSIX ``lib/python*/site-packages`` and Windows
    ``Lib/site-packages``) — a pure filesystem read, safe to run on every CLI
    start. Multiple dist-info dirs (debris from an interrupted pip run) pick
    the newest. ``None`` when the venv or the package is absent.
    """
    try:
        root = home or daemon_home()
        candidates = []
        site_dirs = list(root.glob("lib/python*/site-packages"))
        site_dirs += [root / "Lib" / "site-packages"]
        for sp in site_dirs:
            try:
                if not sp.is_dir():
                    continue
                for entry in sp.iterdir():
                    m = _DIST_INFO_RE.match(entry.name)
                    if m:
                        candidates.append(m.group(1))
            except Exception:
                continue
        if not candidates:
            return None
        return max(candidates, key=parse_version)
    except Exception:
        return None


def running_in_daemon_env(home: Path = None) -> bool:
    """True when THIS process's interpreter lives inside the daemon venv."""
    try:
        root = (home or daemon_home()).resolve()
        prefix = Path(sys.prefix).resolve()
        return prefix == root or root in prefix.parents
    except Exception:
        return False


def cli_version() -> str | None:
    """This process's clawmetry version (package metadata; never raises)."""
    try:
        import importlib.metadata as _md
        return _md.version("clawmetry") or None
    except Exception:
        return None


def cli_entry_path() -> str | None:
    """The script the user invoked (argv[0]), best-effort."""
    try:
        p = sys.argv[0] or ""
        # `-c` / `-m` style invocations have no meaningful script path.
        return p if p and not p.startswith("-") else None
    except Exception:
        return None


def _pip_for_current_env() -> str:
    """The pip invocation that upgrades THIS process's environment."""
    py = sys.executable or "python3"
    user_flag = " --user" if _is_user_site_install() else ""
    return "{0} -m pip install{1} -U clawmetry".format(py, user_flag)


def _is_user_site_install() -> bool:
    """True when this clawmetry import resolves from the user site-packages
    (a ``pip install --user`` copy needs ``--user`` on the upgrade too, or
    pip targets the system site and the stale copy keeps shadowing it)."""
    try:
        import site
        base = site.getusersitepackages()
        import clawmetry
        return bool(base) and Path(clawmetry.__file__).is_relative_to(base)
    except Exception:
        return False


def installs_snapshot(home: Path = None) -> dict:
    """Cheap (no-subprocess) view of this CLI vs the daemon environment.

    Shape::

        {"cli": {"version": str|None, "path": str|None,
                 "in_daemon_env": bool},
         "daemon_env": {"home": str, "present": bool, "version": str|None},
         "stale_cli": bool}

    ``stale_cli`` is True only in the confusing state worth warning about:
    this process runs OUTSIDE the daemon venv and its version is OLDER than
    what the auto-updater installed there.
    """
    root = home or daemon_home()
    cver = cli_version()
    dver = daemon_env_version(root)
    in_env = running_in_daemon_env(root)
    stale = bool(cver and dver and not in_env and version_gt(dver, cver))
    return {
        "cli": {
            "version": cver,
            "path": cli_entry_path(),
            "in_daemon_env": in_env,
        },
        "daemon_env": {
            "home": str(root),
            "present": bool(dver) or (root / "bin").is_dir()
            or (root / "Scripts").is_dir(),
            "version": dver,
        },
        "stale_cli": stale,
    }


def stale_warning_lines(snap: dict = None) -> list:
    """Human warning for a stale CLI copy, or ``[]`` when everything is fine."""
    try:
        snap = snap or installs_snapshot()
        if not snap.get("stale_cli"):
            return []
        cli = snap.get("cli") or {}
        denv = snap.get("daemon_env") or {}
        where = cli.get("path") or sys.executable or "this copy"
        return [
            "⚠ This clawmetry CLI is v{0}, but the ClawMetry daemon on this "
            "machine runs v{1}.".format(cli.get("version"), denv.get("version")),
            "  You are using a stale, separate copy at {0}. The daemon keeps "
            "its own install".format(where),
            "  ({0}) current automatically; copies outside it never "
            "auto-update.".format(denv.get("home")),
            "  Bring this copy up to date:  {0}".format(_pip_for_current_env()),
        ]
    except Exception:
        return []


def maybe_warn_stale_cli(stream=None) -> bool:
    """Print the stale-CLI warning to ``stream`` (default stderr) if needed.

    Returns True when a warning was printed. Honours
    ``CLAWMETRY_NO_STALE_WARN=1``. Never raises.
    """
    try:
        if os.environ.get("CLAWMETRY_NO_STALE_WARN", "").strip() == "1":
            return False
        lines = stale_warning_lines()
        if not lines:
            return False
        out = stream if stream is not None else sys.stderr
        for ln in lines:
            print(ln, file=out)
        return True
    except Exception:
        return False


# ── PATH census (subprocess-backed; doctor only) ─────────────────────────────

def path_executables() -> list:
    """Every distinct ``clawmetry`` executable on PATH, resolution order.

    Dedups by resolved real path (a symlink and its target count once) while
    keeping first-seen order — index 0 is what a bare ``clawmetry`` runs.
    """
    found = []
    seen = set()
    names = ("clawmetry", "clawmetry.exe", "clawmetry.cmd") \
        if sys.platform.startswith("win") else ("clawmetry",)
    try:
        for d in (os.environ.get("PATH") or "").split(os.pathsep):
            if not d:
                continue
            for name in names:
                p = Path(d) / name
                try:
                    if not (p.is_file() and os.access(str(p), os.X_OK)):
                        continue
                    real = str(p.resolve())
                except Exception:
                    continue
                if real in seen:
                    continue
                seen.add(real)
                found.append(p)
    except Exception:
        pass
    return found


def executable_version(path, timeout: float = 10.0) -> str | None:
    """Run ``<path> --version`` and parse the version. ``None`` on any failure."""
    try:
        import subprocess
        r = subprocess.run(
            [str(path), "--version"], capture_output=True, text=True,
            timeout=timeout,
        )
        m = re.search(r"clawmetry\s+(\d[\w.]*)", (r.stdout or "") + (r.stderr or ""))
        return m.group(1) if m else None
    except Exception:
        return None
