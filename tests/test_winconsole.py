"""
Windows console-window suppression tests (clawmetry/winconsole.py).

The injector is a pure function over Popen kwargs so its logic is
testable on any OS; the Popen patch itself is exercised on Windows CI
(sync matrix runs windows-latest).
"""
from __future__ import annotations

import os
import subprocess

from clawmetry import winconsole


class _FakeStartupInfo:
    def __init__(self):
        self.dwFlags = 0
        self.wShowWindow = 99


def test_inject_adds_no_window_flag():
    kwargs = {}
    winconsole.inject_no_window(kwargs, startupinfo_factory=_FakeStartupInfo)
    assert kwargs["creationflags"] & winconsole.CREATE_NO_WINDOW
    si = kwargs["startupinfo"]
    assert si.dwFlags & winconsole.STARTF_USESHOWWINDOW
    assert si.wShowWindow == winconsole.SW_HIDE


def test_inject_preserves_existing_flags():
    kwargs = {"creationflags": 0x00000200}  # CREATE_NEW_PROCESS_GROUP
    winconsole.inject_no_window(kwargs, startupinfo_factory=_FakeStartupInfo)
    assert kwargs["creationflags"] & 0x00000200
    assert kwargs["creationflags"] & winconsole.CREATE_NO_WINDOW


def test_inject_respects_explicit_console_modes():
    """DETACHED_PROCESS / CREATE_NEW_CONSOLE callers are left alone —
    CREATE_NO_WINDOW is mutually exclusive with them at the Win32 level
    (the daemon relaunch in cli._start_subprocess relies on this)."""
    for explicit in (winconsole.DETACHED_PROCESS, winconsole.CREATE_NEW_CONSOLE):
        kwargs = {"creationflags": explicit}
        winconsole.inject_no_window(kwargs, startupinfo_factory=_FakeStartupInfo)
        assert kwargs["creationflags"] == explicit
        assert "startupinfo" not in kwargs


def test_inject_keeps_caller_startupinfo():
    mine = _FakeStartupInfo()
    kwargs = {"startupinfo": mine}
    winconsole.inject_no_window(kwargs, startupinfo_factory=_FakeStartupInfo)
    assert kwargs["startupinfo"] is mine


def test_hide_is_noop_off_windows():
    if os.name == "nt":
        return
    assert winconsole.hide_child_console_windows() is False
    assert not getattr(subprocess.Popen.__init__, "_clawmetry_no_window", False)


def test_hide_patches_and_is_idempotent_on_windows():
    if os.name != "nt":
        return
    assert winconsole.hide_child_console_windows() is True
    assert winconsole.hide_child_console_windows() is True  # idempotent
    assert getattr(subprocess.Popen.__init__, "_clawmetry_no_window", False)
    # A real child spawns fine through the patched Popen and its
    # creationflags carried CREATE_NO_WINDOW (no console window).
    out = subprocess.run(
        ["cmd", "/c", "echo", "hi"], capture_output=True, text=True, timeout=15
    )
    assert out.returncode == 0
    assert "hi" in out.stdout
