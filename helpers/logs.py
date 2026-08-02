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
import subprocess
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


# ── Runtime-aware log reading (adapter LogSource dispatch) ─────────────────
#
# The endpoints above are OpenClaw-hardcoded (dated openclaw-*.log files).
# Everything below serves /api/logs?runtime=<rt> for every OTHER runtime by
# dispatching through the adapter registry's ``log_sources()`` contract
# (clawmetry/adapters/base.py::LogSource). Honest gating: a runtime with no
# real log source gets ``available=False`` + a reason — never a fake path.

# Hard cap on how long a command-kind source may run for a one-shot tail.
RUNTIME_LOG_CMD_TIMEOUT = 10.0
# Hard cap on lines returned regardless of the ?lines= param.
RUNTIME_LOG_MAX_LINES = 2000


def _source_display(source):
    """Human-readable identity of a LogSource: path or command string."""
    if getattr(source, "kind", "") == "file":
        return source.path or ""
    return " ".join(source.command or [])


def resolve_runtime_log_sources(runtime):
    """Look up *runtime*'s adapter and its log sources.

    Returns ``(adapter, sources, reason)`` — ``sources`` is possibly empty,
    in which case ``reason`` is an honest human-readable explanation.
    Never raises.
    """
    from clawmetry.adapters import registry

    adapter = registry.get(runtime)
    if adapter is None:
        return None, [], f"unknown runtime '{runtime}' (no adapter registered)"
    try:
        sources = list(adapter.log_sources() or [])
    except Exception as exc:  # adapter bug must not 500 the Logs tab
        return adapter, [], f"{runtime} log_sources() failed: {exc}"
    if not sources:
        label = adapter.display_name or runtime
        return (
            adapter,
            [],
            f"{label} has no daemon log stream on this machine",
        )
    return adapter, sources, None


def _read_source_tail(source, lines_count, timeout=RUNTIME_LOG_CMD_TIMEOUT):
    """Tail one LogSource. Returns a list of lines, or ``None`` when the
    source is unreadable/absent (caller tries the next source)."""
    lines_count = max(1, min(int(lines_count), RUNTIME_LOG_MAX_LINES))
    if source.kind == "file":
        if not source.path or not os.path.isfile(source.path):
            return None
        return _tail_lines(source.path, lines_count)
    if source.kind == "command" and source.command:
        cmd = [
            str(lines_count) if a == "{lines}" else a for a in source.command
        ]
        try:
            r = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,  # docker logs writes to stderr
                text=True,
                timeout=timeout,
            )
        except (OSError, subprocess.SubprocessError):
            return None
        out = r.stdout or ""
        if r.returncode != 0 and not out.strip():
            return None
        return out.splitlines()[-lines_count:]
    return None


def read_runtime_logs(runtime, lines_count=100):
    """Serve /api/logs?runtime=<rt> for non-openclaw runtimes.

    Response contract (HTTP 200 in ALL cases — "no logs" is a state, not
    an error):
        {"runtime": rt, "available": bool, "label": str|None,
         "source": str|None, "format": "text"|"jsonl"|None,
         "lines": [...], "reason": str|None}
    """
    adapter, sources, reason = resolve_runtime_log_sources(runtime)
    if not sources:
        return {
            "runtime": runtime,
            "available": False,
            "label": None,
            "source": None,
            "format": None,
            "lines": [],
            "reason": reason,
        }
    unreadable = []
    for src in sources:
        lines = _read_source_tail(src, lines_count)
        if lines is None:
            unreadable.append(_source_display(src) or src.id)
            continue
        return {
            "runtime": runtime,
            "available": True,
            "label": src.label,
            "source": _source_display(src),
            "format": src.format,
            "lines": lines,
            "reason": None,
        }
    return {
        "runtime": runtime,
        "available": False,
        "label": None,
        "source": None,
        "format": None,
        "lines": [],
        "reason": "log source(s) not readable: " + ", ".join(unreadable),
    }
