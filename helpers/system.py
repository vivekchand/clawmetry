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

import ctypes
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


# ── Disk / memory / CPU ─────────────────────────────────────────────────
#
# The legacy callers shelled out to `df -h /`, `free -h` and read
# /proc/loadavg directly. None of those exist on Windows, and because every
# call site wraps them in a bare `except`, Windows didn't error — it just
# rendered "--" for Disk, RAM and Load on the main dashboard and dropped the
# CPU/Load rows from the machine panel entirely. Same class of bug as #1127
# (`uptime -p` on macOS), so the fix lives in the same module.
#
# Everything below is stdlib-only (psutil is used when present but is NOT a
# dependency) and returns None rather than raising, so callers keep their
# existing graceful-fallback shape.


def _system_root() -> str:
    """Root path to measure for "disk used" — ``/`` on POSIX, the system
    drive (usually ``C:\\``) on Windows."""
    if os.name == "nt":
        return os.environ.get("SystemDrive", "C:") + "\\"
    return "/"


def disk_usage(path: str | None = None) -> dict | None:
    """Portable replacement for parsing ``df -h /``.

    Returns ``{"mount", "total_gb", "used_gb", "free_gb", "pct"}`` or None.
    ``shutil.disk_usage`` wraps GetDiskFreeSpaceEx / statvfs, so this is
    accurate on all three platforms without a subprocess.
    """
    import shutil

    target = path or _system_root()
    try:
        total, used, free = shutil.disk_usage(target)
    except Exception:
        return None
    if not total:
        return None
    return {
        "mount": target,
        "total_gb": round(total / (1024 ** 3), 1),
        "used_gb": round(used / (1024 ** 3), 1),
        "free_gb": round(free / (1024 ** 3), 1),
        "pct": round(used * 100.0 / total, 1),
    }


class _MEMORYSTATUSEX(ctypes.Structure):
    """Win32 MEMORYSTATUSEX — ctypes is stdlib on every platform, so the
    struct definition is harmless where it is never instantiated."""

    _fields_ = [
        ("dwLength", ctypes.c_ulong),
        ("dwMemoryLoad", ctypes.c_ulong),
        ("ullTotalPhys", ctypes.c_ulonglong),
        ("ullAvailPhys", ctypes.c_ulonglong),
        ("ullTotalPageFile", ctypes.c_ulonglong),
        ("ullAvailPageFile", ctypes.c_ulonglong),
        ("ullTotalVirtual", ctypes.c_ulonglong),
        ("ullAvailVirtual", ctypes.c_ulonglong),
        ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
    ]


def memory_usage() -> dict | None:
    """Portable replacement for parsing ``free -h`` / ``free -m``.

    Returns ``{"total_mb", "used_mb", "available_mb", "pct"}`` or None.
    """
    # 1. psutil when available — most accurate everywhere.
    try:
        import psutil  # type: ignore

        vm = psutil.virtual_memory()
        return {
            "total_mb": int(vm.total / (1024 ** 2)),
            "used_mb": int((vm.total - vm.available) / (1024 ** 2)),
            "available_mb": int(vm.available / (1024 ** 2)),
            "pct": round(vm.percent, 1),
        }
    except Exception:
        pass

    # 2. Windows: GlobalMemoryStatusEx via ctypes.
    if os.name == "nt":
        try:
            stat = _MEMORYSTATUSEX()
            stat.dwLength = ctypes.sizeof(_MEMORYSTATUSEX)
            if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(stat)):  # type: ignore[attr-defined]
                total = int(stat.ullTotalPhys)
                avail = int(stat.ullAvailPhys)
                return {
                    "total_mb": int(total / (1024 ** 2)),
                    "used_mb": int((total - avail) / (1024 ** 2)),
                    "available_mb": int(avail / (1024 ** 2)),
                    "pct": round((total - avail) * 100.0 / total, 1) if total else 0.0,
                }
        except Exception:
            pass

    # 3. Linux: /proc/meminfo. Prefer MemAvailable (kernel's own estimate of
    #    reclaimable memory) over MemFree, which understates by page cache.
    if sys.platform.startswith("linux"):
        try:
            info = {}
            with open("/proc/meminfo") as f:
                for line in f:
                    k, _, rest = line.partition(":")
                    parts = rest.split()
                    if parts:
                        info[k] = int(parts[0])  # kB
            total_kb = info.get("MemTotal", 0)
            avail_kb = info.get("MemAvailable", info.get("MemFree", 0))
            if total_kb:
                return {
                    "total_mb": int(total_kb / 1024),
                    "used_mb": int((total_kb - avail_kb) / 1024),
                    "available_mb": int(avail_kb / 1024),
                    "pct": round((total_kb - avail_kb) * 100.0 / total_kb, 1),
                }
        except Exception:
            pass

    # 4. macOS / BSD: hw.memsize for the total; vm_stat for the free pages.
    if sys.platform == "darwin" or "bsd" in sys.platform:
        try:
            total = int(
                subprocess.run(
                    ["sysctl", "-n", "hw.memsize"],
                    capture_output=True, text=True, timeout=2,
                ).stdout.strip()
            )
            free_bytes = 0
            vm = subprocess.run(
                ["vm_stat"], capture_output=True, text=True, timeout=2
            ).stdout
            page = 4096
            m = re.search(r"page size of (\d+) bytes", vm)
            if m:
                page = int(m.group(1))
            for key in ("Pages free", "Pages inactive", "Pages speculative"):
                m = re.search(rf"{key}:\s+(\d+)", vm)
                if m:
                    free_bytes += int(m.group(1)) * page
            if total:
                return {
                    "total_mb": int(total / (1024 ** 2)),
                    "used_mb": int((total - free_bytes) / (1024 ** 2)),
                    "available_mb": int(free_bytes / (1024 ** 2)),
                    "pct": round((total - free_bytes) * 100.0 / total, 1),
                }
        except Exception:
            pass

    return None


def load_average() -> tuple | None:
    """1/5/15-minute load averages, or None where the OS has no such concept.

    Windows genuinely has no load-average equivalent — callers should fall
    back to :func:`cpu_percent` rather than rendering a fake number.
    """
    try:
        return os.getloadavg()  # type: ignore[attr-defined]
    except (AttributeError, OSError):
        return None


# Previous CPU-time sample, so cpu_percent() can compute a delta without
# blocking. /api/overview is on the dashboard's hot path (fires on every
# refresh), so sleeping ~100ms for a sample window is not acceptable here.
_cpu_prev: tuple[float, float] | None = None


def cpu_percent() -> float | None:
    """System-wide CPU utilisation since the previous call, or None.

    Non-blocking by design: the first call primes the sample and returns
    None, and every subsequent call reports utilisation over the interval
    since the last one. The dashboard polls on a timer, so the value
    populates on the second refresh.
    """
    global _cpu_prev

    busy = idle = None

    if os.name == "nt":
        try:
            idle_t = ctypes.c_ulonglong()
            kern_t = ctypes.c_ulonglong()
            user_t = ctypes.c_ulonglong()
            if ctypes.windll.kernel32.GetSystemTimes(  # type: ignore[attr-defined]
                ctypes.byref(idle_t), ctypes.byref(kern_t), ctypes.byref(user_t)
            ):
                # kernel time already includes idle time.
                idle = float(idle_t.value)
                busy = float(kern_t.value) + float(user_t.value) - idle
        except Exception:
            return None
    elif sys.platform.startswith("linux"):
        try:
            with open("/proc/stat") as f:
                parts = [float(x) for x in f.readline().split()[1:]]
            # user nice system idle iowait irq softirq steal ...
            idle = parts[3] + (parts[4] if len(parts) > 4 else 0.0)
            busy = sum(parts) - idle
        except Exception:
            return None
    else:
        try:
            import psutil  # type: ignore

            return float(psutil.cpu_percent(interval=None))
        except Exception:
            return None

    if busy is None or idle is None:
        return None

    prev = _cpu_prev
    _cpu_prev = (busy, idle)
    if prev is None:
        return None
    d_busy = busy - prev[0]
    d_idle = idle - prev[1]
    total = d_busy + d_idle
    if total <= 0:
        return None
    return round(max(0.0, min(100.0, d_busy * 100.0 / total)), 1)


def cpu_model() -> str | None:
    """Human-readable CPU model name, or None."""
    if sys.platform.startswith("linux"):
        try:
            with open("/proc/cpuinfo") as f:
                for line in f:
                    if line.lower().startswith("model name"):
                        return line.split(":", 1)[1].strip()
        except Exception:
            pass
    elif sys.platform == "darwin":
        try:
            out = subprocess.run(
                ["sysctl", "-n", "machdep.cpu.brand_string"],
                capture_output=True, text=True, timeout=2,
            ).stdout.strip()
            if out:
                return out
        except Exception:
            pass
    elif os.name == "nt":
        # Registry, not `wmic` — wmic is deprecated and is absent from
        # Windows 11 24H2+, where shelling out to it fails outright.
        try:
            import winreg  # type: ignore

            with winreg.OpenKey(
                winreg.HKEY_LOCAL_MACHINE,
                r"HARDWARE\DESCRIPTION\System\CentralProcessor\0",
            ) as k:
                val = winreg.QueryValueEx(k, "ProcessorNameString")[0]
                if val:
                    return str(val).strip()
        except Exception:
            pass

    import platform

    return platform.processor() or None
