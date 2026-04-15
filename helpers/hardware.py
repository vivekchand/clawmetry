"""
helpers/hardware.py — Real host hardware detection (CPU / cores / RAM / backend).

Extracted from dashboard.py as Phase 6.4. Used by routes/infra.py as the
Cost Optimizer panel's fallback when llmfit isn't installed or doesn't
return a `system` block. Replaced the previous hardcoded "Apple M2 Pro /
12 cores / 32 GB" that misrepresented Linux x86 boxes (PR #625).

No module-level state. Pure cross-platform detection via sysctl (macOS),
/proc (Linux), wmic (Windows).
"""

import os
import sys


def _detect_host_hardware():
    """Return real CPU / cores / RAM / backend for the current host.

    Returns dict: {cpu, cores, ram_gb, backend}. Falls back gracefully to
    defaults on any tool failure — never raises.
    """
    cpu = "Unknown CPU"
    cores = os.cpu_count() or 0
    ram_gb = 0
    backend = "CPU"
    try:
        import subprocess as _sp
        if sys.platform == "darwin":
            try:
                cpu = _sp.run(
                    ["sysctl", "-n", "machdep.cpu.brand_string"],
                    capture_output=True, text=True, timeout=2,
                ).stdout.strip() or cpu
            except Exception:
                pass
            try:
                memb = _sp.run(
                    ["sysctl", "-n", "hw.memsize"],
                    capture_output=True, text=True, timeout=2,
                ).stdout.strip()
                if memb.isdigit():
                    ram_gb = round(int(memb) / (1024 ** 3))
            except Exception:
                pass
            if any(s in cpu for s in ("M1", "M2", "M3", "M4", "Apple")):
                backend = "Apple Metal (unified)"
        elif sys.platform.startswith("linux"):
            try:
                with open("/proc/cpuinfo") as _f:
                    for line in _f:
                        if line.lower().startswith("model name"):
                            cpu = line.split(":", 1)[1].strip()
                            break
            except Exception:
                pass
            try:
                with open("/proc/meminfo") as _f:
                    for line in _f:
                        if line.startswith("MemTotal:"):
                            kb = int(line.split()[1])
                            ram_gb = round(kb / (1024 ** 2))
                            break
            except Exception:
                pass
            try:
                if _sp.run(["which", "nvidia-smi"], capture_output=True, timeout=1).returncode == 0:
                    backend = "NVIDIA CUDA"
            except Exception:
                pass
        elif sys.platform == "win32":
            try:
                cpu_out = _sp.run(
                    ["wmic", "cpu", "get", "name", "/value"],
                    capture_output=True, text=True, timeout=3,
                ).stdout
                for line in cpu_out.splitlines():
                    if line.startswith("Name="):
                        cpu = line.split("=", 1)[1].strip()
                        break
            except Exception:
                pass
            try:
                mem = _sp.run(
                    ["wmic", "computersystem", "get", "TotalPhysicalMemory", "/value"],
                    capture_output=True, text=True, timeout=3,
                ).stdout
                for line in mem.splitlines():
                    if line.startswith("TotalPhysicalMemory="):
                        ram_gb = round(int(line.split("=", 1)[1].strip()) / (1024 ** 3))
                        break
            except Exception:
                pass
    except Exception:
        pass
    return {"cpu": cpu, "cores": cores, "ram_gb": ram_gb, "backend": backend}
