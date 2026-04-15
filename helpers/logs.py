"""
helpers/logs.py — Filesystem helpers for OpenClaw log discovery + tail + grep.

Extracted from dashboard.py as Phase 6.2 of the incremental modularisation.
Pure filesystem helpers with no module-level state — `_find_log_file` uses
a late `import dashboard as _d` to reach the runtime-set ``LOG_DIR``
override, matching the pattern used by route modules.

Re-exported from dashboard.py so `_d._get_log_dirs()` etc. in routes/*.py
keep working without changes.
"""

import os
import re
import sys
import tempfile


def _grep_log_file(filepath, pattern):
    """Cross-platform grep: return list of lines matching pattern (case-insensitive)."""
    results = []
    try:
        with open(filepath, "r", errors="replace") as _f:
            for _line in _f:
                if re.search(pattern, _line, re.IGNORECASE):
                    results.append(_line.rstrip("\n"))
    except (OSError, IOError):
        pass
    return results


def _tail_lines(filepath, n=200):
    """Cross-platform tail: return last n lines of a file as a list of strings."""
    try:
        fsize = os.path.getsize(filepath)
        with open(filepath, "rb") as _f:
            try:
                _f.seek(-min(n * 500, fsize), 2)
            except OSError:
                _f.seek(0)
            return _f.read().decode("utf-8", errors="replace").splitlines()[-n:]
    except (OSError, IOError):
        return []


def _get_log_dirs():
    """Return candidate log directories.

    OpenClaw 2026.4+ writes to ~/.openclaw/logs/. Older versions and Docker
    setups still drop into /tmp/openclaw or /tmp/moltbot. We probe all of
    them so the dashboard works regardless of installation age.
    """
    home_logs = os.path.expanduser("~/.openclaw/logs")
    home_logs_alt = os.path.expanduser("~/.openclaw-dev/logs")  # `--dev` profile
    if sys.platform == "win32":
        return [
            home_logs,
            os.path.join(os.environ.get("APPDATA", ""), "openclaw", "logs"),
            os.path.join(tempfile.gettempdir(), "openclaw"),
            os.path.join(tempfile.gettempdir(), "moltbot"),
        ]
    return [home_logs, home_logs_alt, "/tmp/openclaw", "/tmp/moltbot"]


def _find_log_file(ds):
    """Find log file for a given date string, trying multiple prefixes and dirs.

    Consults dashboard's runtime ``LOG_DIR`` override (set from `--log-dir`
    / env) as a first-pass dir, falling back to the standard discovery set
    from `_get_log_dirs()`.
    """
    import dashboard as _d  # late import — LOG_DIR is set at runtime
    log_dir = getattr(_d, "LOG_DIR", None)
    dirs = ([log_dir] if log_dir else []) + _get_log_dirs()
    prefixes = ["openclaw-", "moltbot-"]
    for d in dirs:
        if not d or not os.path.isdir(d):
            continue
        for p in prefixes:
            f = os.path.join(d, f"{p}{ds}.log")
            if os.path.exists(f):
                return f
    return None
