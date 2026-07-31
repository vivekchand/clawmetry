"""
clawmetry.winconsole — stop Windows console windows flashing.

The Windows sync daemon is started with DETACHED_PROCESS (cli.py
_start_subprocess), so it has NO console. Every subprocess it spawns —
the pip self-update check, ``node --version``, disk/gateway probes,
40+ call sites across sync.py — is a console program, and Windows
allocates a brand-new VISIBLE console window for each one because the
parent has none to inherit. Users see cmd windows randomly popping open
and closing while the daemon runs. Scary, and rightly flagged by
enterprise pilots.

``hide_child_console_windows()`` patches ``subprocess.Popen`` once, at
process start, to pass CREATE_NO_WINDOW (+ a SW_HIDE STARTUPINFO) to
every child that didn't explicitly ask for a console — one fix at the
spawn layer instead of touching every call site. No-op on macOS/Linux.

Children that explicitly request DETACHED_PROCESS or CREATE_NEW_CONSOLE
(e.g. the daemon relaunch itself) are left untouched: CREATE_NO_WINDOW
is mutually exclusive with those flags at the Win32 level.
"""
from __future__ import annotations

import logging
import os

log = logging.getLogger("clawmetry.winconsole")

# Win32 process-creation constants (stable ABI; subprocess only defines
# them on Windows, and the injector must be unit-testable everywhere).
CREATE_NO_WINDOW = 0x08000000
DETACHED_PROCESS = 0x00000008
CREATE_NEW_CONSOLE = 0x00000010
STARTF_USESHOWWINDOW = 0x00000001
SW_HIDE = 0

_CALLER_CONSOLE_FLAGS = DETACHED_PROCESS | CREATE_NEW_CONSOLE


def inject_no_window(kwargs, startupinfo_factory=None):
    """Add CREATE_NO_WINDOW (+ hidden STARTUPINFO) to Popen kwargs.

    Pure function so the logic is testable on any OS. Leaves kwargs
    untouched when the caller explicitly chose a console mode
    (DETACHED_PROCESS / CREATE_NEW_CONSOLE) or already passed a
    startupinfo of their own.
    """
    flags = kwargs.get("creationflags") or 0
    if flags & _CALLER_CONSOLE_FLAGS:
        return kwargs
    kwargs["creationflags"] = flags | CREATE_NO_WINDOW
    if kwargs.get("startupinfo") is None and startupinfo_factory is not None:
        try:
            si = startupinfo_factory()
            si.dwFlags |= STARTF_USESHOWWINDOW
            si.wShowWindow = SW_HIDE
            kwargs["startupinfo"] = si
        except Exception:
            pass
    return kwargs


def hide_child_console_windows() -> bool:
    """Patch subprocess.Popen so daemon children never open console windows.

    Windows-only; returns True when the patch is (already) active.
    Idempotent and never raises — a failed patch must not stop the daemon.
    """
    if os.name != "nt":
        return False
    try:
        import subprocess

        if getattr(subprocess.Popen.__init__, "_clawmetry_no_window", False):
            return True
        orig_init = subprocess.Popen.__init__
        si_factory = getattr(subprocess, "STARTUPINFO", None)

        def _no_window_init(self, *args, **kwargs):
            try:
                inject_no_window(kwargs, startupinfo_factory=si_factory)
            except Exception:
                pass
            return orig_init(self, *args, **kwargs)

        _no_window_init._clawmetry_no_window = True
        subprocess.Popen.__init__ = _no_window_init
        log.info("Windows: child console windows hidden (CREATE_NO_WINDOW)")
        return True
    except Exception as e:
        log.warning("could not hide child console windows: %s", e)
        return False
