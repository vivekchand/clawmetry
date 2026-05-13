"""
helpers/system.py — Portable system uptime helpers.

The legacy callers shelled out to `uptime -p`, which only exists on
GNU/coreutils (Linux). On macOS / BSD `uptime` has no `-p` flag and the
subprocess returns non-zero, so the dashboard rendered "Unknown" on
every Mac install. Issue #1127.

This module computes boot time using only stdlib:
  - psutil.boot_time() when psutil is installed (most reliable cross-OS)
  - /proc/uptime on Linux
  - `sysctl kern.boottime` on macOS / BSD
  - WMIC / GetTickCount64 on Windows (best-effort)

Returns a pretty string like "up 3 days, 4 hours, 12 minutes" — matching
the legacy `uptime -p` output the dashboard JS expects.
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
import time


def boot_time() -> float | None:
    """Return the POSIX timestamp the host booted at, or None if unknown.

    Never raises — every failure path returns None so callers can render
    a graceful fallback.
    """
    # 1. psutil — most accurate, works on every platform we ship to.
    try:
        import psutil  # type: ignore

        return float(psutil.boot_time())
    except Exception:
        pass

    # 2. Linux: /proc/uptime is "<uptime_seconds> <idle_seconds>".
    if sys.platform.startswith("linux"):
        try:
            with open("/proc/uptime") as f:
                up_seconds = float(f.read().split()[0])
            return time.time() - up_seconds
        except Exception:
            pass

    # 3. macOS / BSD: sysctl kern.boottime prints e.g.
    # `kern.boottime: { sec = 1715000000, usec = 0 } Thu May  7 ...`
    if sys.platform == "darwin" or "bsd" in sys.platform:
        try:
            out = subprocess.run(
                ["sysctl", "-n", "kern.boottime"],
                capture_output=True,
                text=True,
                timeout=2,
            ).stdout
            m = re.search(r"sec\s*=\s*(\d+)", out)
            if m:
                return float(m.group(1))
        except Exception:
            pass

    # 4. Windows: GetTickCount64 via ctypes (no extra deps).
    if os.name == "nt":
        try:
            import ctypes  # type: ignore

            ms = ctypes.windll.kernel32.GetTickCount64()  # type: ignore[attr-defined]
            return time.time() - (ms / 1000.0)
        except Exception:
            pass

    return None


def uptime_seconds() -> int | None:
    """Return seconds since boot, or None if we couldn't determine it."""
    bt = boot_time()
    if bt is None:
        return None
    return max(0, int(time.time() - bt))


def format_uptime(seconds: int | None) -> str:
    """Format seconds-since-boot as a human string matching `uptime -p`.

    Examples:
      None      -> "unknown"
      59        -> "up less than a minute"
      120       -> "up 2 minutes"
      3700      -> "up 1 hour, 1 minute"
      90061     -> "up 1 day, 1 hour, 1 minute"

    Plural form mirrors GNU coreutils so existing JS that strips the
    leading "up " keeps working.
    """
    if seconds is None:
        return "unknown"
    if seconds < 60:
        return "up less than a minute"

    days, rem = divmod(seconds, 86400)
    hours, rem = divmod(rem, 3600)
    minutes = rem // 60

    parts = []
    if days:
        parts.append(f"{days} day{'s' if days != 1 else ''}")
    if hours:
        parts.append(f"{hours} hour{'s' if hours != 1 else ''}")
    if minutes:
        parts.append(f"{minutes} minute{'s' if minutes != 1 else ''}")
    if not parts:
        # >=60s but <60min where minutes==0 (e.g. exactly 60s) — fall back
        # to minutes so we never emit a bare "up".
        parts.append("1 minute")
    return "up " + ", ".join(parts)


def uptime_pretty() -> str:
    """Convenience: portable replacement for `subprocess.run(['uptime', '-p'])`."""
    return format_uptime(uptime_seconds())
