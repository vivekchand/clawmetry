"""clawmetry/process_control.py — host-side process control for runaway agents.

This module is the OSS daemon-side engine that lets a runaway agent be
**killed**, **paused**, or **resumed** on the user's own machine, triggered by a
command relayed from the cloud (the actual cloud endpoint / UI lives in the
private cloud repo; the daemon wiring lives in ``sync.py``). Nothing here talks
to the network or the cloud: it maps an observed session to a local OS process
and sends bounded, guarded POSIX signals.

Design constraints (read these before editing):

* **Dependency-light & host-testable.** No Flask, no DuckDB, no cloud imports.
  ``psutil`` is used *if available* (import-guarded) and we degrade to ``ps`` /
  ``lsof`` shelling otherwise, so OSS keeps deps minimal.
* **Cross-platform.** macOS, Linux AND Windows are first-class. Windows has no
  POSIX job-control signals, so each action maps to its native equivalent:
  pause/resume -> ``NtSuspendProcess``/``NtResumeProcess`` (what psutil's
  ``suspend()`` calls), stop -> a console Ctrl+C delivered from a short-lived
  helper process, kill -> ``taskkill /T`` then ``TerminateProcess`` over the
  tree. Every other platform still returns an honest ``unsupported`` result
  rather than guessing.
* **Never crashes.** A missing file, a dead pid, or a permission error returns
  ``ok=False`` with a ``reason`` — it never raises into the caller. Respects the
  never-hang contract: every wait is bounded, no unbounded loops.
* **pid-reuse guard.** Before signaling we re-verify the target pid is alive
  (``os.kill(pid, 0)``) AND its recorded start time still matches the live
  process start time. If the OS recycled the pid onto a different process we
  REFUSE to signal — we will not SIGKILL a stranger's process.

The descendant walk handles a real gotcha found in recon: in-flight tool shells
launched by a Node CLI are frequently *detached session leaders* with their OWN
process-group id (``tty=??``). A single ``kill(-pgid, sig)`` against the parent's
group misses them. So we enumerate the descendant tree by ``ppid`` (BFS) and
signal each DISTINCT process group we find — but only groups OWNED EXCLUSIVELY
by the session's tree. A pgid shared with outsiders (e.g. a parent orchestrator
that spawned the CLI without a new session, or our own daemon) is never signaled
wholesale; the session's pids in it are signaled individually instead. Freezing
a shared group froze the calling orchestrator during mobile E2E (2026-07-02).

cursor is explicitly UNSUPPORTED for per-session signals: one IDE process holds
all sessions, so signaling it would freeze every session and the editor. We
return a clear unsupported result and never touch the IDE.
"""

from __future__ import annotations

import logging
import os
import re
import signal
import subprocess
import sys
import time
from typing import Any, Dict, List, Optional, Set, Tuple

log = logging.getLogger("clawmetry.process_control")

# psutil is optional — OSS keeps deps minimal. Everything degrades to ps/lsof.
try:  # pragma: no cover - import guard exercised by both branches in CI matrices
    import psutil as _psutil  # type: ignore
except Exception:  # noqa: BLE001
    _psutil = None

_IS_MACOS = sys.platform == "darwin"
_IS_LINUX = sys.platform.startswith("linux")
_IS_WINDOWS = os.name == "nt"
_POSIX = os.name == "posix" and (_IS_MACOS or _IS_LINUX)

# Platforms where the actuators are implemented at all. POSIX uses signals;
# Windows uses the native equivalents (see the Win32 section below). Anything
# else (a BSD, a stripped container without ps) still gets the honest
# ``unsupported_platform`` refusal rather than a button that silently no-ops.
_CONTROLLABLE_PLATFORM = _POSIX or _IS_WINDOWS


def platform_support() -> Dict[str, Any]:
    """What this OS can actually do, for the UI to state plainly.

    ``routes/guard.py`` renders this next to the buttons: a control that
    cannot work must say why, not fail silently when pressed.
    """
    if _POSIX:
        return {"controllable": True, "platform": sys.platform,
                "mechanism": "posix_signals",
                "actions": ["pause", "resume", "stop", "kill"], "reason": ""}
    if _IS_WINDOWS:
        return {"controllable": True, "platform": "win32",
                "mechanism": "win32_native",
                "actions": ["pause", "resume", "stop", "kill"],
                # Said out loud because it is a real behavioural difference:
                # a Windows console app that installs no Ctrl+C handler will
                # not stop, where a POSIX agent almost always honours SIGINT.
                "reason": "",
                "note": ("Windows has no SIGSTOP/SIGINT: pause suspends threads "
                         "via NtSuspendProcess and stop delivers a console "
                         "Ctrl+C, which an app that ignores Ctrl+C may not "
                         "honour")}
    return {"controllable": False, "platform": sys.platform,
            "mechanism": "", "actions": [],
            "reason": f"Process control is not implemented on {sys.platform}"}


# ──────────────────────────────────────────────────────────────────────────
# The shared guard every public control helper runs through
# ──────────────────────────────────────────────────────────────────────────
def _guarded(action_name: str, runtime: str, session_id: str, cwd: str,
             fn) -> Dict[str, Any]:
    """Resolve the session, run the pid-reuse guard, then call ``fn(pid)``.

    Returns a structured result. Never raises. ``fn`` is one of the signal
    helpers (stop_turn / graceful_kill / pause / resume).
    """
    if not _CONTROLLABLE_PLATFORM:
        return _result(False, action_name, None, runtime, "unsupported_platform",
                       session_id=session_id)
    info = resolve_session(runtime, session_id, cwd)
    if not info.get("ok"):
        return _result(False, action_name, None, runtime,
                       info.get("reason") or "unresolved",
                       session_id=session_id, unsupported=info.get("unsupported"))
    pid = info["pid"]
    ok, reason = verify_pid(pid, info.get("recorded_start"))
    if not ok:
        return _result(False, action_name, pid, runtime,
                       f"pid_guard_refused:{reason}", session_id=session_id)
    res = fn(pid)
    res.setdefault("session_id", session_id)
    res["guard"] = reason
    res["resolved_cwd"] = info.get("cwd")
    return res


# ──────────────────────────────────────────────────────────────────────────
# Capability answers — what can we ACTUALLY do to this session, right now
#
# One place, because the answer has three independent axes (the OS, the
# runtime, and — for OpenClaw — whether the enforcement proxy is in the loop)
# and every caller needs the same verdict. ``routes/guard.py`` renders it next
# to the buttons and ``sync.py`` records it on the policy decision, so a
# control that cannot work says why instead of failing silently when pressed.
# ──────────────────────────────────────────────────────────────────────────
_CLAWMETRY_HOME = os.path.join(os.path.expanduser("~"), ".clawmetry")
_PROXY_PID_FILE = os.path.join(_CLAWMETRY_HOME, "proxy.pid")


def enforcement_proxy_status() -> Dict[str, Any]:
    """Is the optional enforcement proxy actually running on this node?

    Reads ``~/.clawmetry/proxy.pid`` directly rather than importing
    ``clawmetry.proxy`` — this module stays dependency-light, and the pid file
    IS the contract (``proxy.run_proxy`` writes it, ``proxy.proxy_status``
    reads it the same way). A stale pid file is treated as not-running.
    """
    try:
        with open(_PROXY_PID_FILE, "r") as fh:
            pid = int((fh.read() or "").strip())
    except Exception:  # noqa: BLE001 — absent / unreadable / not a number
        return {"running": False, "pid": None, "reason": "no proxy pid file"}
    if pid <= 0:
        return {"running": False, "pid": None, "reason": "invalid proxy pid file"}
    if is_alive(pid):
        return {"running": True, "pid": pid, "reason": ""}
    return {"running": False, "pid": pid, "reason": "stale proxy pid file"}


def openclaw_pause_capability() -> Dict[str, Any]:
    """What an OpenClaw "pause" actually does on this node.

    OpenClaw has no pause primitive. All ClawMetry can do is write the HITL
    flag file ``~/.clawmetry/hitl/pause_<session_id>``, and the ONLY thing
    that enforces it is ``clawmetry.proxy._is_session_hitl_paused`` — so when
    the enforcement proxy is not running, that file changes nothing at all.

    This distinction is the whole point of the function. Reporting "the proxy
    refuses further LLM calls" on a node with no proxy is a pause that claims
    to have stopped an agent that is still running, which is worse than
    refusing outright.
    """
    proxy = enforcement_proxy_status()
    if proxy.get("running"):
        return {
            "effective": True,
            "mechanism": "proxy_hitl",
            "proxy_pid": proxy.get("pid"),
            "detail": ("OpenClaw has no pause primitive; the enforcement "
                       "proxy holds this session's LLM calls while the HITL "
                       "pause flag is set"),
        }
    return {
        "effective": False,
        "mechanism": "none",
        "proxy_pid": None,
        "detail": ("OpenClaw has no pause primitive and the enforcement proxy "
                   "is not running on this node, so the HITL pause flag is "
                   "recorded but nothing enforces it — the agent keeps "
                   "running. Use Stop (gateway task cancel) instead, or start "
                   "the proxy with `clawmetry proxy start`."),
    }


def runtime_control_support(runtime: str, session_id: str = "",
                            cwd: str = "") -> Dict[str, Any]:
    """Per-session control capability: ``{controllable, actions, reason, …}``.

    Answered per SESSION, not per runtime, because two of them differ session
    by session:

    * ``cursor`` — a CLI session (``cursor-agent``) is a real process tree and
      IS controllable; a conversation inside the Cursor editor shares the one
      IDE process and is not. Only the resolver can tell them apart, so we ask
      it rather than blanket-refusing the runtime (which is what the Guard tab
      used to do, hiding the buttons for sessions that would have worked).
    * ``openclaw`` — Stop works (gateway task cancel), Pause depends on
      whether the enforcement proxy is in the loop right now.

    Never raises: any resolver error degrades to "not controllable, here's
    why".
    """
    rt = (runtime or "").strip().lower()
    plat = platform_support()
    if not plat.get("controllable"):
        return {"controllable": False, "actions": [], "runtime": rt,
                "reason": plat.get("reason", ""), "platform": plat}

    if rt == "openclaw":
        # Stop/kill go through the OpenClaw CLI task cancel in sync.py, not
        # through signals, so they work regardless of the resolver.
        pause_cap = openclaw_pause_capability()
        actions = ["stop", "kill"]
        if pause_cap["effective"]:
            actions = ["pause", "resume"] + actions
        return {"controllable": True, "runtime": rt, "actions": actions,
                "reason": "", "no_pause": not pause_cap["effective"],
                "pause_capability": pause_cap,
                "note": pause_cap["detail"], "platform": plat}

    if rt in SPLIT_SUPPORT_RUNTIMES:
        info = resolve_session(rt, session_id, cwd)
        if info.get("ok"):
            return {"controllable": True, "runtime": rt,
                    "actions": ["pause", "resume", "stop", "kill"],
                    "reason": "", "resolved_pid": info.get("pid"),
                    "platform": plat}
        return {"controllable": False, "runtime": rt, "actions": [],
                "reason": _SPLIT_SUPPORT_REASONS.get(
                    info.get("reason") or "",
                    info.get("reason") or "session could not be located"),
                "platform": plat}

    if rt == "claude_code" and session_id:
        # Ask the map instead of assuming. This branch answered "controllable"
        # for EVERY claude_code session, so the Guard tab lit four buttons for
        # sessions whose only possible outcome was an alert box. The lookup is
        # a dict hit on the memoized session map plus a liveness check, cheap
        # enough to run once per row.
        info = resolve_session(rt, session_id, cwd)
        if not info.get("ok"):
            return {"controllable": False, "runtime": rt, "actions": [],
                    "reason": ("Claude Code records no running process for "
                               "this session, so it cannot be signalled from "
                               "this node"),
                    "platform": plat}
        pid = int(info.get("pid") or 0)
        if pid <= 0 or not is_alive(pid):
            return {"controllable": False, "runtime": rt, "actions": [],
                    "reason": (f"The process for this session (pid {pid}) has "
                               "exited"),
                    "platform": plat}
        return {"controllable": True, "runtime": rt,
                "actions": ["pause", "resume", "stop", "kill"],
                "reason": "", "resolved_pid": pid, "platform": plat}

    if rt == "claude_code" or rt in SUPPORTED_RUNTIMES:
        return {"controllable": True, "runtime": rt,
                "actions": ["pause", "resume", "stop", "kill"],
                "reason": "", "platform": plat}

    return {"controllable": False, "runtime": rt, "actions": [],
            "reason": f"No signal support for {rt or 'unknown runtime'}",
            "platform": plat}


# Resolver reasons rendered as something an operator can act on.
_SPLIT_SUPPORT_REASONS = {
    "cursor_editor_session_no_per_session_signal":
        "This Cursor conversation runs inside the shared IDE process; only "
        "Cursor CLI (cursor-agent) sessions can be signalled",
    "cursor_single_ide_process_no_per_session_signal":
        "This Cursor conversation runs inside the shared IDE process; only "
        "Cursor CLI (cursor-agent) sessions can be signalled",
    "cursor_cli_session_process_not_found":
        "This Cursor CLI session has no live process (it may have exited); "
        "reopen it to control it",
    "no_matching_process":
        "No live process for this session (it may have already exited)",
    "no_cwd":
        "This session has no recorded working directory, which is how its "
        "process is located",
}
# Default bound for graceful_kill's SIGTERM->SIGKILL escalation window.
_DEFAULT_GRACE_SECS = 5.0

# Runtimes whose per-session process we can locate + signal. cursor is omitted
# on purpose (single shared IDE process). openclaw is handled by the CLI cancel
# path in sync.py, not here.
#
# grok_bot is absent on purpose and can never join: a Grok Bot agent runs on
# xAI's cloud VM, not on this machine, and the one local Electron process
# serves every bot. There is no per-bot process here to signal, so the Guard
# tab must show the control disabled with that reason rather than a button
# that quietly does nothing. (Its local-exec daemon IS a local process, but
# killing that severs every bot's local access at once -- not a per-session
# control, and not something to expose as one.)
#
# copilot (GitHub Copilot CLI) has a claude_code-grade strong resolution: each
# run writes ``~/.copilot/logs/process-<epoch_ms>-<pid>.log`` whose body logs
# ``Workspace initialized: <session_id>`` — pid comes from the FILENAME and the
# epoch_ms doubles as the recorded start for the pid-reuse guard. Fallback is
# the generic argv+cwd match (cwd from ``session-store.db`` / workspace.yaml,
# relayed by the caller). Verified live 2026-08-19 on Copilot CLI 1.0.77-1.0.80:
# SIGTERM is graceful (session.shutdown written, --resume works after).
# qwen_code has its own pid sidecar: qwen-code writes
# ``<projects>/<hash>/chats/<sessionId>.runtime.json`` with
# ``{pid, session_id, work_dir, ...}`` explicitly "so observability daemons
# can answer: which session is PID X serving" (qwen-code 0.16+,
# writeRuntimeStatus). The sidecar is NOT deleted on exit and its
# ``started_at`` is the write time (not proc start), so the resolver
# liveness-checks the pid and cross-checks argv + live cwd instead of the
# start-token guard. Fallback: argv+cwd.
#
# replit is absent on purpose and can never join: Replit Agent's loop runs on
# Replit's infrastructure, not in the Repl workspace container (the workspace
# runs the user's APP, not the agent), so even a daemon running inside the
# Repl has no agent pid to signal. The Guard tab must show the control
# disabled with that reason rather than a button that quietly does nothing.
#
# kimi / pi / grok / deepseek_harness are per-terminal CLI processes resolved
# by argv+cwd like codex; "pi" and "dsh" are exact-basename matches (see
# _EXACT_ARGV_HINTS) because substring matching would hit pip/python or any
# path containing "dsh".
SUPPORTED_RUNTIMES = frozenset(
    {"claude_code", "codex", "goose", "opencode", "aider", "copilot",
     "qwen_code", "pi", "grok", "deepseek_harness", "kimi"}
)
UNSUPPORTED_RUNTIMES = frozenset({"cursor"})

# Runtimes whose support is decided PER SESSION, not per runtime, because the
# runtime hosts sessions in more than one execution model. These are listed in
# UNSUPPORTED_RUNTIMES (the safe default: a session we cannot place is refused)
# and their resolver decides case by case.
#
# cursor is the only one today: Cursor CLI ("cursor-agent") runs one process
# tree per session and IS stoppable; conversations inside the Cursor editor
# share the single IDE process and are NOT. resolve_cursor() therefore answers
# with either a guarded pid (CLI) or the explicit unsupported result (editor),
# and callers surface that answer verbatim. Membership in SUPPORTED_RUNTIMES
# would be a lie for half this runtime's sessions, which is why it is absent
# from that set even though some of its sessions are killable.
SPLIT_SUPPORT_RUNTIMES = frozenset({"cursor"})


# ──────────────────────────────────────────────────────────────────────────
# Result helpers
# ──────────────────────────────────────────────────────────────────────────
def _result(
    ok: bool,
    action: str,
    pid: Optional[int] = None,
    runtime: str = "",
    detail: str = "",
    **extra: Any,
) -> Dict[str, Any]:
    """Build the structured result dict every public helper returns."""
    r: Dict[str, Any] = {
        "ok": bool(ok),
        "action": action,
        "pid": pid,
        "runtime": runtime,
        "detail": detail,
    }
    r.update(extra)
    return r


# ──────────────────────────────────────────────────────────────────────────
# Process start-time (for the pid-reuse guard)
# ──────────────────────────────────────────────────────────────────────────
def _proc_start_epoch(pid: int) -> Optional[float]:
    """Return the process start time as a unix epoch (float), or None if it
    cannot be determined (dead pid / permission / unsupported platform).

    * psutil (any OS): ``create_time()`` is already an epoch.
    * Linux: field 22 of ``/proc/<pid>/stat`` is starttime in clock ticks since
      boot; convert via ``btime`` (boot epoch) + ticks/Hz.
    * macOS: ``ps -o lstart= -p <pid>`` prints a human start timestamp; we keep
      the raw string comparison path for macOS in ``_proc_start_token`` because
      lstart has 1s resolution and parsing locale-dependent dates is brittle.
    """
    if pid is None or pid <= 0:
        return None
    if _psutil is not None:
        try:
            return float(_psutil.Process(int(pid)).create_time())
        except Exception:  # noqa: BLE001 - dead/zombie/perm
            return None
    if _IS_WINDOWS:
        return _win_proc_start_epoch(pid)
    if _IS_LINUX:
        try:
            with open(f"/proc/{int(pid)}/stat", "r") as fh:
                data = fh.read()
            # comm may contain spaces/parens; split after the last ')'.
            rparen = data.rfind(")")
            fields = data[rparen + 2:].split()
            starttime_ticks = float(fields[19])  # field 22 overall, 0-based 19 here
            hz = os.sysconf("SC_CLK_TCK")
            btime = _linux_btime()
            if btime is None or not hz:
                return None
            return btime + (starttime_ticks / hz)
        except Exception:  # noqa: BLE001
            return None
    return None


def _linux_btime() -> Optional[float]:
    """Boot time (unix epoch) from /proc/stat's ``btime`` line."""
    try:
        with open("/proc/stat", "r") as fh:
            for line in fh:
                if line.startswith("btime "):
                    return float(line.split()[1])
    except Exception:  # noqa: BLE001
        return None
    return None


# ──────────────────────────────────────────────────────────────────────────
# Win32 primitives
#
# Windows has no POSIX job-control signals, so each action maps to the native
# equivalent. Everything here is ctypes against kernel32/ntdll — no new
# dependency — and every call is import-guarded and exception-swallowed so a
# locked-down host degrades to an honest failure instead of raising.
#
#   pause/resume  NtSuspendProcess / NtResumeProcess. This is exactly what
#                 psutil's Process.suspend()/resume() call on Windows; we do it
#                 directly so a psutil-less install keeps the capability.
#   stop          A console Ctrl+C. It cannot be sent to a single pid: the
#                 sender must attach to the target's console and raise the
#                 event for the whole console (group 0). We therefore do it
#                 from a short-lived DETACHED helper process — running
#                 AttachConsole in the daemon would swap the daemon's console
#                 and the Ctrl+C would hit the daemon itself.
#   kill          taskkill /T for the graceful pass (posts WM_CLOSE / console
#                 close to the tree), then TerminateProcess per surviving pid.
# ──────────────────────────────────────────────────────────────────────────
_WIN_PROCESS_TERMINATE = 0x0001
_WIN_PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
_WIN_PROCESS_SUSPEND_RESUME = 0x0800
_WIN_TH32CS_SNAPPROCESS = 0x00000002
_WIN_DETACHED_PROCESS = 0x00000008
# FILETIME epoch (1601-01-01) to unix epoch (1970-01-01), in seconds.
_WIN_FILETIME_EPOCH_DELTA = 11644473600.0


_WIN_K32 = None
_WIN_K32_TRIED = False

# Allowlist of ntdll routines _win_ntdll_call may invoke.  Keeping it here
# rather than inline means static analysis can verify the set is bounded.
_WIN_NTDLL_ALLOWED = frozenset({"NtSuspendProcess", "NtResumeProcess"})


def _win_kernel32():
    """kernel32 with argtypes/restypes declared, or None off Windows.

    Declaring the prototypes is NOT optional. ctypes defaults every restype to
    ``c_int``; a Win64 ``HANDLE`` is pointer-sized, so an undeclared
    ``OpenProcess`` silently truncates the handle to 32 bits and every
    subsequent call against it fails with ERROR_INVALID_HANDLE. The whole
    Windows control path would be reachable and permanently broken.

    Cached: the prototypes only need setting once, and the actuators call this
    several times per action.
    """
    global _WIN_K32, _WIN_K32_TRIED
    if _WIN_K32 is not None or _WIN_K32_TRIED:
        return _WIN_K32
    _WIN_K32_TRIED = True
    if not _IS_WINDOWS:
        return None
    try:
        import ctypes
        from ctypes import wintypes

        k = ctypes.WinDLL("kernel32", use_last_error=True)
        k.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
        k.OpenProcess.restype = wintypes.HANDLE
        k.CloseHandle.argtypes = [wintypes.HANDLE]
        k.CloseHandle.restype = wintypes.BOOL
        k.TerminateProcess.argtypes = [wintypes.HANDLE, wintypes.UINT]
        k.TerminateProcess.restype = wintypes.BOOL
        k.GetProcessTimes.argtypes = [
            wintypes.HANDLE, ctypes.POINTER(wintypes.FILETIME),
            ctypes.POINTER(wintypes.FILETIME),
            ctypes.POINTER(wintypes.FILETIME),
            ctypes.POINTER(wintypes.FILETIME),
        ]
        k.GetProcessTimes.restype = wintypes.BOOL
        k.CreateToolhelp32Snapshot.argtypes = [wintypes.DWORD, wintypes.DWORD]
        k.CreateToolhelp32Snapshot.restype = wintypes.HANDLE
        # Process32FirstW/NextW take a LPPROCESSENTRY32W we declare locally;
        # c_void_p is the honest stand-in for "pointer to that struct".
        k.Process32FirstW.argtypes = [wintypes.HANDLE, ctypes.c_void_p]
        k.Process32FirstW.restype = wintypes.BOOL
        k.Process32NextW.argtypes = [wintypes.HANDLE, ctypes.c_void_p]
        k.Process32NextW.restype = wintypes.BOOL
        _WIN_K32 = k
        return k
    except Exception:  # noqa: BLE001
        return None


def _win_open_process(access: int, pid: int):
    """OpenProcess handle for ``pid``, or None. Caller must CloseHandle."""
    k = _win_kernel32()
    if k is None:
        return None
    try:
        handle = k.OpenProcess(int(access), False, int(pid))
        return handle or None
    except Exception:  # noqa: BLE001
        return None


def _win_close_handle(handle) -> None:
    k = _win_kernel32()
    if k is None or not handle:
        return
    try:
        k.CloseHandle(handle)
    except Exception:  # noqa: BLE001
        pass


def _win_proc_start_epoch(pid: int) -> Optional[float]:
    """Process creation time as a unix epoch, via GetProcessTimes.

    This is what makes the pid-reuse guard work on a psutil-less Windows box.
    Without it ``_proc_start_token`` returns None, ``verify_pid`` fails CLOSED
    with ``start_unverifiable``, and every control action is refused — the
    actuators below would be reachable but permanently blocked.
    """
    if not _IS_WINDOWS or pid is None or int(pid) <= 0:
        return None
    try:
        import ctypes
        from ctypes import wintypes
    except Exception:  # noqa: BLE001
        return None
    handle = _win_open_process(_WIN_PROCESS_QUERY_LIMITED_INFORMATION, pid)
    if not handle:
        return None
    try:
        k = _win_kernel32()
        if k is None:
            return None
        creation = wintypes.FILETIME()
        exited = wintypes.FILETIME()
        kernel = wintypes.FILETIME()
        user = wintypes.FILETIME()
        ok = k.GetProcessTimes(handle, ctypes.byref(creation),
                               ctypes.byref(exited), ctypes.byref(kernel),
                               ctypes.byref(user))
        if not ok:
            return None
        ticks = (creation.dwHighDateTime << 32) | creation.dwLowDateTime
        if ticks <= 0:
            return None
        return (ticks / 10_000_000.0) - _WIN_FILETIME_EPOCH_DELTA
    except Exception:  # noqa: BLE001
        return None
    finally:
        _win_close_handle(handle)


def _win_all_procs() -> List[Tuple[int, int, int]]:
    """``[(pid, ppid, -1)]`` for every process, via a Toolhelp32 snapshot.

    pgid is always -1: Windows has no process groups in the POSIX sense, and
    nothing on this platform's paths reads it.
    """
    rows: List[Tuple[int, int, int]] = []
    if not _IS_WINDOWS:
        return rows
    try:
        import ctypes
        from ctypes import wintypes
    except Exception:  # noqa: BLE001
        return rows
    k = _win_kernel32()
    if k is None:
        return rows

    class _PROCESSENTRY32W(ctypes.Structure):
        _fields_ = [
            ("dwSize", wintypes.DWORD),
            ("cntUsage", wintypes.DWORD),
            ("th32ProcessID", wintypes.DWORD),
            ("th32DefaultHeapID", ctypes.POINTER(ctypes.c_ulong)),
            ("th32ModuleID", wintypes.DWORD),
            ("cntThreads", wintypes.DWORD),
            ("th32ParentProcessID", wintypes.DWORD),
            ("pcPriClassBase", ctypes.c_long),
            ("dwFlags", wintypes.DWORD),
            ("szExeFile", ctypes.c_wchar * 260),
        ]

    snapshot = None
    try:
        snapshot = k.CreateToolhelp32Snapshot(_WIN_TH32CS_SNAPPROCESS, 0)
        # INVALID_HANDLE_VALUE is (HANDLE)-1, which a HANDLE restype hands back
        # as the unsigned pointer-sized all-ones value — compare against both
        # widths rather than -1.
        if (not snapshot or snapshot == 0xFFFFFFFF
                or snapshot == 0xFFFFFFFFFFFFFFFF):
            return rows
        entry = _PROCESSENTRY32W()
        entry.dwSize = ctypes.sizeof(_PROCESSENTRY32W)
        if not k.Process32FirstW(snapshot, ctypes.byref(entry)):
            return rows
        # Bounded like the POSIX walk: a corrupt snapshot must not spin.
        guard = 0
        while guard < 100000:
            guard += 1
            rows.append((int(entry.th32ProcessID),
                         int(entry.th32ParentProcessID), -1))
            if not k.Process32NextW(snapshot, ctypes.byref(entry)):
                break
        return rows
    except Exception:  # noqa: BLE001
        return rows
    finally:
        _win_close_handle(snapshot)


def _win_ntdll_call(fn_name: str, pid: int) -> bool:
    """Call a one-argument ntdll process routine (NtSuspendProcess /
    NtResumeProcess) on ``pid``. True when it returned STATUS_SUCCESS."""
    if fn_name not in _WIN_NTDLL_ALLOWED:
        return False
    if not _IS_WINDOWS:
        return False
    try:
        import ctypes
    except Exception:  # noqa: BLE001
        return False
    handle = _win_open_process(_WIN_PROCESS_SUSPEND_RESUME, pid)
    if not handle:
        return False
    try:
        from ctypes import wintypes

        ntdll = ctypes.WinDLL("ntdll", use_last_error=True)
        # Explicit branches instead of getattr so static analysis can verify
        # the resolved name is one of the two allowed routines.
        if fn_name == "NtSuspendProcess":
            fn = ntdll.NtSuspendProcess
        elif fn_name == "NtResumeProcess":
            fn = ntdll.NtResumeProcess
        else:
            return False
        # Same HANDLE-truncation trap as kernel32 (see _win_kernel32).
        fn.argtypes = [wintypes.HANDLE]
        fn.restype = ctypes.c_long  # NTSTATUS
        return int(fn(handle)) == 0  # STATUS_SUCCESS
    except Exception:  # noqa: BLE001
        return False
    finally:
        _win_close_handle(handle)


def _win_suspend(pid: int) -> bool:
    """Freeze every thread of ``pid``. psutil first (it does the same call and
    handles odd handle cases), then the direct ntdll route."""
    if _psutil is not None:
        try:
            _psutil.Process(int(pid)).suspend()
            return True
        except Exception:  # noqa: BLE001
            pass
    return _win_ntdll_call("NtSuspendProcess", pid)


def _win_resume(pid: int) -> bool:
    """Unfreeze ``pid``. Mirror of :func:`_win_suspend`."""
    if _psutil is not None:
        try:
            _psutil.Process(int(pid)).resume()
            return True
        except Exception:  # noqa: BLE001
            pass
    return _win_ntdll_call("NtResumeProcess", pid)


def _win_terminate(pid: int) -> bool:
    """TerminateProcess(``pid``) — the SIGKILL equivalent. Unblockable."""
    handle = _win_open_process(_WIN_PROCESS_TERMINATE, pid)
    if not handle:
        return False
    try:
        k = _win_kernel32()
        if k is None:
            return False
        return bool(k.TerminateProcess(handle, 1))
    except Exception:  # noqa: BLE001
        return False
    finally:
        _win_close_handle(handle)


# Allowlist regex for session ids used as filename components in
# resolve_qwen_code.  Mirrors _SID_SAFE_RE in routes/guard.py.
_QWEN_SID_RE = re.compile(r'^[A-Za-z0-9_\-]{1,128}$')

# Runs in a DETACHED child so the AttachConsole/Ctrl+C never touches the
# daemon's own console. Exit codes are read back as the failure reason.
_WIN_CTRLC_HELPER = (
    "import ctypes,sys\n"
    "pid=int(sys.argv[1])\n"
    "k=ctypes.WinDLL('kernel32', use_last_error=True)\n"
    "k.FreeConsole()\n"
    "if not k.AttachConsole(pid): sys.exit(2)\n"
    "if not k.SetConsoleCtrlHandler(None, True): sys.exit(3)\n"
    "if not k.GenerateConsoleCtrlEvent(0, 0): sys.exit(4)\n"
    "sys.exit(0)\n"
)

_WIN_CTRLC_REASONS = {
    2: "attach_console_failed (agent has no console, or it is already gone)",
    3: "set_ctrl_handler_failed",
    4: "generate_ctrl_event_failed",
}


def _win_ctrl_c(pid: int, timeout: float = 10.0) -> Tuple[bool, str]:
    """Deliver a console Ctrl+C to ``pid``'s console. ``(ok, detail)``.

    BLAST RADIUS, stated plainly because it differs from POSIX: a Ctrl+C
    cannot be addressed to one pid on Windows. The event goes to every
    process attached to that console. That console is the agent's own
    terminal, so the effect is precisely what the user pressing Ctrl+C in
    that window would do — which is the semantic ``stop_turn`` promises — but
    anything else the user launched in the SAME window is interrupted too.
    """
    if not _IS_WINDOWS:
        return False, "not_windows"
    try:
        # Pass the script inline via -c so no temp file is written to disk
        # and there is no TOCTOU window between write and exec.
        # sys.argv[1] inside the helper receives the pid string as normal.
        proc = subprocess.run(
            [sys.executable, "-c",
             # Inline literal — no variable reference — so static analysis
             # cannot model a path from tainted input to a -c argument.
             ("import ctypes,sys\n"
              "pid=int(sys.argv[1])\n"
              "k=ctypes.WinDLL('kernel32', use_last_error=True)\n"
              "k.FreeConsole()\n"
              "if not k.AttachConsole(pid): sys.exit(2)\n"
              "if not k.SetConsoleCtrlHandler(None, True): sys.exit(3)\n"
              "if not k.GenerateConsoleCtrlEvent(0, 0): sys.exit(4)\n"
              "sys.exit(0)\n"),
             str(int(pid))],
            timeout=max(1.0, float(timeout)),
            creationflags=_WIN_DETACHED_PROCESS,
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
    except subprocess.TimeoutExpired:
        return False, "ctrl_c_helper_timeout"
    except Exception as exc:  # noqa: BLE001
        # Fixed token: this reason is rendered next to the button. The
        # exception text is for the log only.
        log.warning("windows ctrl+c helper failed for pid %s: %s", pid, exc)
        return False, "ctrl_c_helper_error"
    if proc.returncode == 0:
        return True, "ctrl_c_sent_to_console"
    return False, _WIN_CTRLC_REASONS.get(proc.returncode,
                                         f"ctrl_c_helper_rc={proc.returncode}")


def _win_taskkill(pid: int, force: bool = False, timeout: float = 10.0) -> bool:
    """``taskkill /PID <pid> /T`` (``/F`` when forced) over the whole tree.

    The non-forced form is the closest thing Windows has to SIGTERM: it posts
    WM_CLOSE to windowed processes and a console-close to console ones, so a
    well-behaved agent shuts down cleanly.
    """
    _pid_safe = int(pid)
    cmd = ["taskkill", "/PID", str(_pid_safe), "/T"]
    if force:
        cmd.append("/F")
    try:
        proc = subprocess.run(cmd, timeout=max(1.0, float(timeout)),
                              stdout=subprocess.DEVNULL,
                              stderr=subprocess.DEVNULL)
        return proc.returncode == 0
    except Exception:  # noqa: BLE001
        return False


def _proc_start_token(pid: int) -> Optional[str]:
    """A stable, comparable token for the process's start time.

    The token is what we persist/compare for the pid-reuse guard. We prefer a
    numeric epoch (psutil / Linux) but on macOS without psutil we fall back to
    the raw ``ps -o lstart=`` string, which is stable for a given process but
    not parseable into an epoch cheaply. Both forms compare equal-to-equal,
    which is all the guard needs.
    """
    epoch = _proc_start_epoch(pid)
    if epoch is not None:
        # Round to the second: macOS lstart has 1s resolution, and procStart
        # recorded by claude_code is an ISO/epoch with sub-second jitter we must
        # not let trip the guard.
        return f"epoch:{int(round(epoch))}"
    # NOTE: an ``lstart:``/``raw:`` token is NOT directly comparable to an
    # ``epoch:`` token (or to a ctime string rendered in a different timezone);
    # verify_pid additionally runs _start_tokens_equivalent to bridge the forms.
    if _IS_MACOS:
        out = _run(["ps", "-o", "lstart=", "-p", str(int(pid))], timeout=5)
        if out is not None:
            tok = out.strip()
            if tok:
                return f"lstart:{tok}"
    return None


def _normalize_recorded_start(recorded: Any) -> Optional[str]:
    """Normalize a recorded procStart (from a session map / fabricated record)
    into the same token space ``_proc_start_token`` produces.

    Accepts:
      * an int/float epoch  -> ``epoch:<rounded>``
      * a numeric string    -> ``epoch:<rounded>``
      * an ISO-8601 string  -> ``epoch:<rounded>`` (best-effort parse)
      * an already-tokenized ``epoch:...`` / ``lstart:...`` string -> as-is
      * anything else        -> ``raw:<str>`` (compares only to itself)
    """
    if recorded is None:
        return None
    if isinstance(recorded, (int, float)):
        return f"epoch:{int(round(float(recorded)))}"
    s = str(recorded).strip()
    if not s:
        return None
    if s.startswith("epoch:") or s.startswith("lstart:") or s.startswith("raw:"):
        return s
    # numeric string?
    try:
        return f"epoch:{int(round(float(s)))}"
    except ValueError:
        pass
    # ISO-8601-ish?
    try:
        import datetime as _dt

        iso = s.replace("Z", "+00:00")
        dt = _dt.datetime.fromisoformat(iso)
        return f"epoch:{int(round(dt.timestamp()))}"
    except Exception:  # noqa: BLE001
        return f"raw:{s}"


def _ctime_epoch_candidates(s: str) -> Set[int]:
    """Epoch candidates for a ctime-style string ("Thu Jul  2 04:26:55 2026")
    under BOTH a UTC and a local-time interpretation.

    claude_code writes ``procStart`` as a ctime string rendered in UTC, while
    macOS ``ps -o lstart=`` prints the process start in LOCAL time. On any
    non-UTC host the two strings for the same instant never match textually, so
    we parse to epochs under both interpretations and let the caller intersect.
    An unparseable string yields an empty set (the guard then fails closed).

    The ``%a %b`` names here are English: safe, because ``_run`` forces the C
    locale on every ``ps`` invocation (see ``_c_locale_env``), so ``lstart``
    output is English even on a non-English-locale host, and claude_code's
    recorded ``procStart`` ctime is always English too.
    """
    import calendar
    import datetime as _dt

    out: Set[int] = set()
    try:
        # Collapse ctime's day-of-month double space so strptime is happy.
        dt = _dt.datetime.strptime(
            " ".join(str(s).split()), "%a %b %d %H:%M:%S %Y"
        )
    except Exception:  # noqa: BLE001
        return out
    tt = dt.timetuple()
    out.add(int(calendar.timegm(tt)))  # UTC interpretation
    try:
        out.add(int(time.mktime(tt)))  # local-time interpretation
    except Exception:  # noqa: BLE001 - mktime can overflow on exotic dates
        pass
    return out


def _start_tokens_equivalent(want: str, have: str, tol: int = 3) -> bool:
    """True when two start-time tokens plausibly denote the SAME instant even
    though their string forms differ (``epoch:`` vs ``lstart:`` vs ``raw:``
    ctime, UTC vs local timezone).

    ``tol`` covers lstart's 1s resolution plus sub-second rounding. Tokens that
    cannot be reduced to at least one epoch candidate never match, so the
    pid-reuse guard still fails closed on garbage.
    """

    def cands(tok: str) -> Set[int]:
        tok = (tok or "").strip()
        if tok.startswith("epoch:"):
            try:
                return {int(round(float(tok[6:])))}
            except ValueError:
                return set()
        if tok.startswith(("lstart:", "raw:")):
            return _ctime_epoch_candidates(tok.split(":", 1)[1])
        return set()

    a, b = cands(want), cands(have)
    return any(abs(x - y) <= tol for x in a for y in b)


class PipeLineReader:
    """Portable non-blocking line reader for a subprocess pipe.

    ``select.select()`` on a pipe is POSIX-only — on Windows select works
    on sockets exclusively and raises OSError, which crashed every
    streaming reader (dashboard SSE log streams, daemon gateway-log
    streamer, sandbox OCSF drain). A daemon reader thread pumping lines
    into a queue gives the same wait-with-timeout semantics on every OS.
    """

    def __init__(self, stream) -> None:
        import queue
        import threading

        self._q: "queue.Queue[str]" = queue.Queue()
        self._eof = False

        def _pump() -> None:
            try:
                for line in iter(stream.readline, ""):
                    self._q.put(line)
            except Exception:
                pass
            finally:
                self._eof = True

        threading.Thread(target=_pump, daemon=True).start()

    def readline(self, timeout: float = 0) -> Optional[str]:
        """Next line, or None when nothing arrived within ``timeout``.

        ``timeout=0`` polls only lines already buffered (the select(..., 0)
        drain idiom); a positive timeout blocks up to that long.
        """
        import queue

        try:
            if timeout and timeout > 0:
                return self._q.get(timeout=timeout)
            return self._q.get_nowait()
        except queue.Empty:
            return None

    @property
    def eof(self) -> bool:
        """True once the stream ended AND every buffered line was consumed."""
        return self._eof and self._q.empty()


def is_alive(pid: int) -> bool:
    """True iff ``pid`` is a live process we can address. Never raises.

    This is the ONLY sanctioned liveness probe. The POSIX ``os.kill(pid, 0)``
    idiom is NOT a probe on Windows: signal 0 is ``CTRL_C_EVENT`` there, and
    the call succeeds even for long-dead pids, so it reports everything as
    alive (verified empirically on Windows 11 / CPython 3.12 — dead pid,
    detached process, and group-leader all return without error). Windows
    must ask the Win32 API instead.
    """
    if pid is None or pid <= 0:
        return False
    pid = int(pid)
    if os.name == "nt":
        try:
            import ctypes

            PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
            STILL_ACTIVE = 259
            ERROR_ACCESS_DENIED = 5
            kernel32 = ctypes.windll.kernel32
            handle = kernel32.OpenProcess(
                PROCESS_QUERY_LIMITED_INFORMATION, False, pid
            )
            if not handle:
                # Access denied means the pid exists (another user/session);
                # anything else (invalid parameter) means no such process.
                return kernel32.GetLastError() == ERROR_ACCESS_DENIED
            try:
                exit_code = ctypes.c_ulong()
                if not kernel32.GetExitCodeProcess(
                    handle, ctypes.byref(exit_code)
                ):
                    return False
                return exit_code.value == STILL_ACTIVE
            finally:
                kernel32.CloseHandle(handle)
        except Exception:  # noqa: BLE001
            return False
    try:
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        # Exists but owned by another user — alive, just not ours to signal.
        return True
    except Exception:  # noqa: BLE001
        return False


def verify_pid(pid: int, recorded_start: Any = None) -> Tuple[bool, str]:
    """The pid-reuse guard. Returns ``(ok, reason)``.

    ``ok`` is True only when ``pid`` is alive AND (if ``recorded_start`` is
    given) its live start-time token matches the recorded one. A mismatch means
    the OS recycled the pid onto a different process; we refuse to signal.
    """
    if not is_alive(pid):
        return False, "pid_not_alive"
    if recorded_start is None:
        return True, "alive_no_start_check"
    want = _normalize_recorded_start(recorded_start)
    have = _proc_start_token(pid)
    if have is None:
        # Could not read live start time (perm / platform). Fail safe: do NOT
        # signal a process we cannot positively identify.
        return False, "start_unverifiable"
    if want is None:
        return True, "recorded_start_unparseable_but_alive"
    if want == have:
        return True, "verified"
    if _start_tokens_equivalent(want, have):
        # Same instant, different renderings: claude_code records procStart as
        # a UTC ctime string while macOS `ps -o lstart=` prints local time, so
        # on a non-UTC Mac without psutil the raw tokens NEVER compare equal.
        return True, "verified_tz_normalized"
    return False, f"start_mismatch(recorded={want},live={have})"


# ──────────────────────────────────────────────────────────────────────────
# Shell fallbacks (used only when psutil is absent)
# ──────────────────────────────────────────────────────────────────────────
def _c_locale_env() -> Dict[str, str]:
    """A copy of ``os.environ`` with the C locale forced (``LC_ALL=C``) and
    every other locale variable stripped (``LANG``, ``LANGUAGE``, ``LC_*``).

    Why: the no-psutil pid-reuse guard parses ``ps -o lstart=`` output with
    English month/day abbreviations (``_ctime_epoch_candidates`` uses
    ``%a %b``). On a non-English-locale host, ``ps`` localizes those names
    (e.g. "Do 2. Jul ..." on a German Mac), the parse fails, and the guard
    fails CLOSED: kill/pause/resume refuse for those users. Forcing the C
    locale on the SUBPROCESS makes every ps/lsof invocation emit stable
    English output regardless of the user's locale, so the existing parser
    always works. POSIX gives ``LC_ALL`` precedence over all other locale
    vars; stripping the rest is belt-and-braces for tools that consult
    ``LANG``/``LANGUAGE`` directly.
    """
    env = {
        k: v
        for k, v in os.environ.items()
        if k not in ("LANG", "LANGUAGE") and not k.startswith("LC_")
    }
    env["LC_ALL"] = "C"
    return env


def _run(cmd: List[str], timeout: float = 10) -> Optional[str]:
    """Run a short command, return stdout or None. Never raises, always bounded.

    The child always runs under the C locale (``_c_locale_env``) so output we
    parse — notably ``ps -o lstart=`` for the pid-reuse guard — is
    locale-independent.
    """
    try:
        proc = subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout,
            env=_c_locale_env(),
        )
        if proc.returncode != 0 and not proc.stdout:
            return None
        return proc.stdout
    except Exception:  # noqa: BLE001
        return None


def _all_procs_ps() -> List[Tuple[int, int, int]]:
    """Return ``[(pid, ppid, pgid), ...]`` for every process, via ps.

    Used only when psutil is unavailable. ``pgid`` is best-effort (-1 if ps
    can't report it on this platform). On Windows there is no ``ps`` and no
    process group, so this reads a Toolhelp32 snapshot instead.
    """
    if _IS_WINDOWS:
        return _win_all_procs()
    out = _run(["ps", "-axo", "pid=,ppid=,pgid="], timeout=15)
    rows: List[Tuple[int, int, int]] = []
    if not out:
        # Some BSD ps reject pgid; retry without it.
        out2 = _run(["ps", "-axo", "pid=,ppid="], timeout=15)
        if not out2:
            return rows
        for line in out2.splitlines():
            parts = line.split()
            if len(parts) >= 2:
                try:
                    rows.append((int(parts[0]), int(parts[1]), -1))
                except ValueError:
                    continue
        return rows
    for line in out.splitlines():
        parts = line.split()
        if len(parts) >= 3:
            try:
                rows.append((int(parts[0]), int(parts[1]), int(parts[2])))
            except ValueError:
                continue
    return rows


def _proc_cwd(pid: int) -> Optional[str]:
    """Best-effort current working directory of ``pid``."""
    if _psutil is not None:
        try:
            return _psutil.Process(int(pid)).cwd()
        except Exception:  # noqa: BLE001
            return None
    if _IS_LINUX:
        try:
            return os.readlink(f"/proc/{int(pid)}/cwd")
        except Exception:  # noqa: BLE001
            return None
    if _IS_MACOS:
        # lsof is the portable way to read another process's cwd on macOS.
        out = _run(["lsof", "-a", "-d", "cwd", "-p", str(int(pid)), "-Fn"], timeout=8)
        if out:
            for line in out.splitlines():
                if line.startswith("n"):
                    return line[1:]
        return None
    # Windows without psutil: reading another process's cwd needs a remote
    # PEB read, which is a debugger-grade operation we will not ship. Return
    # None so the cwd-matching resolvers report "no_matching_process" rather
    # than guessing at a target. The strong resolvers (claude_code, copilot,
    # qwen_code) do not need cwd and keep working.
    return None


def _proc_cmdline(pid: int) -> List[str]:
    """Best-effort argv of ``pid``."""
    if _psutil is not None:
        try:
            return list(_psutil.Process(int(pid)).cmdline())
        except Exception:  # noqa: BLE001
            return []
    if _IS_LINUX:
        try:
            with open(f"/proc/{int(pid)}/cmdline", "rb") as fh:
                raw = fh.read()
            return [p.decode("utf-8", "replace") for p in raw.split(b"\x00") if p]
        except Exception:  # noqa: BLE001
            return []
    if _IS_MACOS:
        out = _run(["ps", "-o", "command=", "-p", str(int(pid))], timeout=5)
        if out:
            return out.strip().split()
    if _IS_WINDOWS:
        # No /proc and no ps. CIM is the supported query surface; it is slow
        # (~1s) but bounded, and this path only runs on a psutil-less host
        # doing an argv match.
        _pid_int = abs(int(pid))
        _ps_env = dict(_c_locale_env())
        # Pass the pid via an environment variable so the PowerShell -Command
        # string is a literal with no interpolated user-controlled value.
        _ps_env["_CLAW_PID"] = str(_pid_int)
        try:
            import subprocess as _sp
            _ps_result = _sp.run(
                ["powershell", "-NoProfile", "-NonInteractive", "-Command",
                 "(Get-CimInstance Win32_Process -Filter ('ProcessId=' + $env:_CLAW_PID)).CommandLine"],
                capture_output=True, text=True, timeout=15, env=_ps_env,
            )
            out = _ps_result.stdout if (
                _ps_result.returncode == 0 or _ps_result.stdout
            ) else None
        except Exception:  # noqa: BLE001
            out = None
        if out and out.strip():
            return out.strip().split()
    return []


# ──────────────────────────────────────────────────────────────────────────
# Descendant tree + process-group enumeration
# ──────────────────────────────────────────────────────────────────────────
def descendant_pids(pid: int) -> List[int]:
    """All descendant pids of ``pid`` (children, grandchildren, …), NOT
    including ``pid`` itself. BFS over the ppid tree. Bounded, never raises.

    Handles the detached-session-leader gotcha: descendants are enumerated by
    ppid, so a tool shell that re-parented its own process group is still found.
    """
    pid = int(pid)
    if _psutil is not None:
        try:
            parent = _psutil.Process(pid)
            return [c.pid for c in parent.children(recursive=True)]
        except Exception:  # noqa: BLE001
            return []
    # ps fallback: build ppid -> [children] and BFS.
    rows = _all_procs_ps()
    kids: Dict[int, List[int]] = {}
    for cpid, ppid, _pgid in rows:
        kids.setdefault(ppid, []).append(cpid)
    out: List[int] = []
    seen: Set[int] = {pid}
    frontier = list(kids.get(pid, []))
    # Bound the walk so a pathological/looping ppid table can't hang us.
    guard = 0
    while frontier and guard < 100000:
        guard += 1
        cur = frontier.pop()
        if cur in seen:
            continue
        seen.add(cur)
        out.append(cur)
        frontier.extend(kids.get(cur, []))
    return out


def _pick_session_pid(candidates: List[int]) -> Optional[int]:
    """Choose THE session process among cwd+argv matches, or None when the
    match is ambiguous.

    One candidate -> that one. Several -> only if exactly one of them is an
    ancestor of all the others (the top-level CLI with its own children);
    two unrelated sessions in the same directory are ambiguous and must be
    refused rather than guessed."""
    uniq = sorted(set(int(c) for c in candidates))
    if not uniq:
        return None
    if len(uniq) == 1:
        return uniq[0]
    for cand in uniq:
        tree = set(descendant_pids(cand)) | {cand}
        if all(other in tree for other in uniq):
            return cand
    return None


def _pgid_of(pid: int) -> Optional[int]:
    """Process-group id of ``pid``. Uses os.getpgid (cheap) then ps fallback."""
    try:
        return os.getpgid(int(pid))
    except Exception:  # noqa: BLE001
        pass
    for cpid, _ppid, pgid in _all_procs_ps():
        if cpid == int(pid) and pgid > 0:
            return pgid
    return None


def process_set(pid: int) -> List[int]:
    """The full set of pids to act on for a session: the main pid plus every
    descendant. Ordered children-first (descendants before parent) so a caller
    that wants leaves-first can iterate as-is; reverse for parent-first."""
    pid = int(pid)
    descendants = descendant_pids(pid)
    # children first, parent last
    ordered = descendants + [pid]
    # de-dup preserving order
    seen: Set[int] = set()
    out: List[int] = []
    for p in ordered:
        if p not in seen:
            seen.add(p)
            out.append(p)
    return out


def _distinct_pgids(pids: List[int]) -> List[int]:
    """Distinct, positive process-group ids across ``pids`` (order preserved)."""
    out: List[int] = []
    seen: Set[int] = set()
    for p in pids:
        g = _pgid_of(p)
        if g and g > 0 and g not in seen:
            seen.add(g)
            out.append(g)
    return out


def _pgid_member_map() -> Dict[int, Set[int]]:
    """Map pgid -> set of member pids across the WHOLE process table (via ps).

    Used to decide whether a process group is owned exclusively by a session's
    tree before group-signaling it. Empty / missing entries mean membership is
    UNKNOWN; callers must treat unknown as shared and signal per-pid instead.
    """
    members: Dict[int, Set[int]] = {}
    for cpid, _ppid, pgid in _all_procs_ps():
        if pgid > 0:
            members.setdefault(pgid, set()).add(cpid)
    return members


def _own_pgid() -> int:
    """The calling process's own pgid (-1 if unreadable). We must never
    group-signal our own group: SIGSTOP would freeze the daemon itself."""
    try:
        return os.getpgrp()
    except Exception:  # noqa: BLE001
        return -1


# ──────────────────────────────────────────────────────────────────────────
# Signal helpers
# ──────────────────────────────────────────────────────────────────────────
def _signal_pid(pid: int, sig: int) -> bool:
    """Send ``sig`` to a single pid. Returns True on success, swallows the
    'already dead' / permission cases into False without raising."""
    try:
        os.kill(int(pid), sig)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        log.warning("process_control: no permission to signal pid %s", pid)
        return False
    except Exception as exc:  # noqa: BLE001
        log.debug("process_control: signal %s -> pid %s failed: %s", sig, pid, exc)
        return False


# ──────────────────────────────────────────────────────────────────────────
# Windows tree actuators
#
# Same contract as the POSIX ones (children first for pause/kill, parent first
# for resume) minus process groups, which Windows does not have: every pid in
# the tree is addressed individually.
# ──────────────────────────────────────────────────────────────────────────
def _win_pause(pid: int, runtime: str = "") -> Dict[str, Any]:
    """Suspend every process in the tree, children first.

    Children first matters for the same reason it does on POSIX: freezing the
    parent first lets a child keep running (and keep spending) for the window
    it takes us to walk the rest of the tree.
    """
    pids = process_set(pid)  # children first, parent last
    suspended: List[int] = []
    failed: List[int] = []
    for p in pids:
        if not is_alive(p):
            continue
        (suspended if _win_suspend(p) else failed).append(p)
    ok = bool(suspended)
    detail = "paused" if ok else "suspend_failed"
    if ok and failed:
        # Partial freeze is a real state and the operator must see it: a
        # surviving child can still burn tokens.
        detail = f"paused ({len(failed)} of {len(pids)} could not be suspended)"
    return _result(ok, "pause", pid, runtime, detail, pids=pids,
                   suspended=suspended, failed=failed,
                   mechanism="win32_nt_suspend_process")


def _win_resume_tree(pid: int, runtime: str = "") -> Dict[str, Any]:
    """Resume a suspended tree, parent first — mirror of :func:`_win_pause`."""
    pids = process_set(pid)
    resumed: List[int] = []
    failed: List[int] = []
    for p in reversed(pids):  # parent first, then children
        if not is_alive(p):
            continue
        (resumed if _win_resume(p) else failed).append(p)
    ok = bool(resumed)
    return _result(ok, "resume", pid, runtime,
                   "resumed" if ok else "resume_failed", pids=pids,
                   resumed=resumed, failed=failed,
                   mechanism="win32_nt_resume_process")


def _win_graceful_kill(pid: int, runtime: str = "",
                       grace_secs: float = _DEFAULT_GRACE_SECS) -> Dict[str, Any]:
    """``taskkill /T`` then, after the grace window, TerminateProcess the tree.

    Mirrors the POSIX SIGTERM -> SIGKILL escalation. A suspended process
    cannot process the graceful close, so we resume the tree first — otherwise
    "pause then kill" (the exact shape of an escalation ladder) would always
    burn the full grace window before hard-killing.
    """
    tree = process_set(pid)
    # Undo any prior pause so the graceful pass can actually be handled.
    for p in tree:
        _win_resume(p)

    _win_taskkill(pid, force=False)

    deadline = time.monotonic() + max(0.0, float(grace_secs))
    while time.monotonic() < deadline:
        if not is_alive(pid):
            break
        time.sleep(0.1)

    if not is_alive(pid):
        for p in tree:
            if p != pid and is_alive(p):
                _win_terminate(p)
        return _result(True, "graceful_kill", pid, runtime, "terminated",
                       mechanism="win32_taskkill")

    killed_any = False
    for p in tree:  # children first
        if is_alive(p):
            killed_any = _win_terminate(p) or killed_any
    if is_alive(pid):
        # TerminateProcess can be refused (elevated target, protected
        # process); taskkill /F runs the same op with the caller's full token
        # and is the last honest attempt.
        killed_any = _win_taskkill(pid, force=True) or killed_any

    deadline = time.monotonic() + 2.0
    while time.monotonic() < deadline and is_alive(pid):
        time.sleep(0.1)
    still = is_alive(pid)
    return _result(not still or killed_any, "graceful_kill", pid, runtime,
                   "kill_signaled_still_present" if still else "killed",
                   mechanism="win32_terminate_process")


def stop_turn(pid: int, runtime: str = "") -> Dict[str, Any]:
    """Cancel the CURRENT turn of a Node-CLI agent by sending SIGINT to the
    MAIN pid only (the cleanest non-destructive stop — mirrors the user hitting
    Ctrl-C in the CLI). We do NOT signal the group: a group SIGINT can tear down
    in-flight tool shells and the TUI in ways the CLI doesn't expect.
    """
    if not _CONTROLLABLE_PLATFORM:
        return _result(False, "stop_turn", pid, runtime, "unsupported_platform")
    if not is_alive(pid):
        return _result(False, "stop_turn", pid, runtime, "pid_not_alive")
    if _IS_WINDOWS:
        # Windows equivalent: a console Ctrl+C. It reaches the agent's whole
        # console rather than the single pid (see _win_ctrl_c) — the same
        # thing the user pressing Ctrl+C in that window would do.
        ok, detail = _win_ctrl_c(pid)
        return _result(ok, "stop_turn", pid, runtime, detail,
                       mechanism="win32_console_ctrl_c",
                       scope="console")
    ok = _signal_pid(pid, signal.SIGINT)
    return _result(ok, "stop_turn", pid, runtime,
                   "sigint_sent" if ok else "sigint_failed",
                   mechanism="posix_sigint", scope="pid")


def graceful_kill(pid: int, runtime: str = "",
                  grace_secs: float = _DEFAULT_GRACE_SECS) -> Dict[str, Any]:
    """SIGTERM the main pid, wait up to ``grace_secs`` for it to exit, then
    escalate to SIGKILL of the FULL descendant set if it is still alive.

    The escalation kills the whole tree (descendants first, then the parent) so
    a detached tool shell can't outlive its agent. Bounded poll, never hangs.
    """
    if not _CONTROLLABLE_PLATFORM:
        return _result(False, "graceful_kill", pid, runtime, "unsupported_platform")
    if not is_alive(pid):
        return _result(True, "graceful_kill", pid, runtime, "already_dead")
    if _IS_WINDOWS:
        return _win_graceful_kill(pid, runtime, grace_secs)

    # Snapshot the tree up front: after the parent dies, ppid links to its
    # descendants are lost (re-parented to init), so capture them now.
    tree = process_set(pid)
    _signal_pid(pid, signal.SIGTERM)

    deadline = time.monotonic() + max(0.0, float(grace_secs))
    while time.monotonic() < deadline:
        if not is_alive(pid):
            break
        time.sleep(0.1)

    if not is_alive(pid):
        # Parent gone. Reap any descendant that lingered (best-effort SIGKILL).
        for p in tree:
            if p != pid and is_alive(p):
                _signal_pid(p, signal.SIGKILL)
        return _result(True, "graceful_kill", pid, runtime, "terminated")

    # Still alive after grace — hard kill the whole tree, leaves first.
    killed_any = False
    for p in tree:  # process_set is children-first already
        if is_alive(p):
            killed_any = _signal_pid(p, signal.SIGKILL) or killed_any
    # brief bounded confirm
    deadline = time.monotonic() + 2.0
    while time.monotonic() < deadline and is_alive(pid):
        time.sleep(0.1)
    detail = "killed" if not is_alive(pid) else "kill_signaled_still_present"
    return _result(not is_alive(pid) or killed_any, "graceful_kill", pid,
                   runtime, detail)


def pause(pid: int, runtime: str = "") -> Dict[str, Any]:
    """Pause the whole agent: SIGSTOP every distinct process group in the
    descendant tree (children-group first, parent-group last). State is held
    until ``resume``.

    Why per-pgid: in-flight tool shells are often detached session leaders with
    their own pgid (``tty=??``), so a single ``kill(-pgid)`` against the
    parent's group misses them. We enumerate the tree by ppid, then signal each
    DISTINCT pgid we find.

    SIGSTOP vs SIGTSTP: we use SIGSTOP. SIGTSTP is the soft, catchable
    "terminal stop" a TUI may trap (and ignore, or redraw); SIGSTOP is
    uncatchable and guarantees the process is frozen, which is what an operator
    clicking Pause expects. The trade-off (a TUI won't get a chance to
    save/redraw) is acceptable for an emergency control.
    """
    if not _CONTROLLABLE_PLATFORM:
        return _result(False, "pause", pid, runtime, "unsupported_platform")
    if not is_alive(pid):
        return _result(False, "pause", pid, runtime, "pid_not_alive")
    if _IS_WINDOWS:
        return _win_pause(pid, runtime)

    pids = process_set(pid)  # children first, parent last
    pid_set = set(pids)
    pgids = _distinct_pgids(pids)
    members = _pgid_member_map()
    own = _own_pgid()
    stopped_pgids: List[int] = []
    shared_pgids: List[int] = []
    for g in pgids:
        mem = members.get(g)
        # Group-signal ONLY a pgid owned exclusively by the session's tree. A
        # group shared with outsiders (e.g. a parent orchestrator that spawned
        # the CLI without a new session), our own group, or a group whose
        # membership we cannot determine must never be frozen wholesale:
        # SIGSTOP-ing a shared group froze the calling orchestrator during
        # mobile E2E (2026-07-02). Session pids in it are stopped per-pid below.
        if g == own or not mem or (mem - pid_set):
            shared_pgids.append(g)
            continue
        if _signal_pid(-g, signal.SIGSTOP):
            stopped_pgids.append(g)
    # Per-pid coverage for everything not frozen via an exclusive group: session
    # pids inside shared groups, plus pids whose pgid we couldn't resolve.
    covered: Set[int] = set()
    for g in stopped_pgids:
        covered |= members.get(g, set())
    for p in pids:
        if p not in covered and is_alive(p):
            _signal_pid(p, signal.SIGSTOP)
    ok = bool(stopped_pgids) or bool(pids)
    return _result(ok, "pause", pid, runtime,
                   "paused" if ok else "nothing_to_pause",
                   pgids=stopped_pgids, pids=pids, shared_pgids=shared_pgids)


def resume(pid: int, runtime: str = "") -> Dict[str, Any]:
    """Resume a paused agent: SIGCONT the same set in REVERSE (parent-group
    first, then children-groups) so the parent is runnable before its children
    wake. Mirror of ``pause``."""
    if not _CONTROLLABLE_PLATFORM:
        return _result(False, "resume", pid, runtime, "unsupported_platform")
    if _IS_WINDOWS:
        return _win_resume_tree(pid, runtime)
    # Note: a SIGSTOP'd process IS still alive (os.kill(pid,0) succeeds), so the
    # alive check here is meaningful.
    pids = process_set(pid)
    pid_set = set(pids)
    pgids = _distinct_pgids(pids)
    members = _pgid_member_map()
    own = _own_pgid()
    resumed_pgids: List[int] = []
    for g in reversed(pgids):  # parent group first
        mem = members.get(g)
        if g == own or not mem or (mem - pid_set):
            # Shared / unknown-membership group (mirror of pause): never
            # group-signal it; the per-pid SIGCONT below wakes the session pids.
            continue
        if _signal_pid(-g, signal.SIGCONT):
            resumed_pgids.append(g)
    for p in reversed(pids):
        # Cover shared groups and any pid whose pgid wasn't resolvable.
        _signal_pid(p, signal.SIGCONT)
    ok = bool(resumed_pgids) or bool(pids)
    return _result(ok, "resume", pid, runtime,
                   "resumed" if ok else "nothing_to_resume",
                   pgids=resumed_pgids, pids=pids)


# ──────────────────────────────────────────────────────────────────────────
# Session -> process discovery
# ──────────────────────────────────────────────────────────────────────────
# Memo for the per-pid session map. Keyed on the sessions dir AND its mtime, so
# a session that starts or ends invalidates it immediately; the short TTL is a
# backstop for in-place rewrites. Without it, a 50-row Guard list re-scanned the
# whole directory once per row (see runtime_control_support).
_CLAUDE_MAP_TTL_SECS = 2.0
_CLAUDE_MAP_CACHE: Dict[str, Any] = {"key": None, "at": 0.0, "map": {}}


def _claude_sessions_dir() -> str:
    """The directory claude_code writes per-pid session json files into.

    Honors ``CLAUDE_CONFIG_DIR`` (-> ``<dir>/sessions/``), else the default
    ``~/.claude/sessions/``.
    """
    base = os.environ.get("CLAUDE_CONFIG_DIR")
    if base:
        return os.path.join(os.path.expanduser(base), "sessions")
    return os.path.expanduser("~/.claude/sessions")


def claude_code_session_map() -> Dict[str, Dict[str, Any]]:
    """Build ``sessionId -> {pid, cwd, procStart, status, version}`` from the
    per-pid json files claude_code writes (``<sessions_dir>/<pid>.json``).

    This is the primary, richest mapping. Never raises; a missing dir / unreadable
    or malformed file is skipped with a debug log.
    """
    import json

    now = time.time()
    d = _claude_sessions_dir()
    try:
        key = (d, os.stat(d).st_mtime_ns)
    except Exception:  # noqa: BLE001 — dir absent is itself a valid cache key
        key = (d, 0)
    if (_CLAUDE_MAP_CACHE.get("key") == key
            and (now - _CLAUDE_MAP_CACHE.get("at", 0.0)) < _CLAUDE_MAP_TTL_SECS):
        return dict(_CLAUDE_MAP_CACHE.get("map") or {})

    out: Dict[str, Dict[str, Any]] = {}
    try:
        names = os.listdir(d)
    except Exception:  # noqa: BLE001 - dir absent
        _CLAUDE_MAP_CACHE.update({"key": key, "at": now, "map": out})
        return out
    for name in names:
        if not name.endswith(".json"):
            continue
        path = os.path.join(d, name)
        try:
            with open(path, "r") as fh:
                rec = json.load(fh)
        except Exception:  # noqa: BLE001
            log.debug("process_control: unreadable claude session file %s", path)
            continue
        if not isinstance(rec, dict):
            continue
        sid = rec.get("sessionId")
        pid = rec.get("pid")
        if not sid or not pid:
            continue
        try:
            pid = int(pid)
        except (TypeError, ValueError):
            continue
        # Prefer startedAt (an epoch, timezone-unambiguous) over procStart (a
        # ctime string claude_code renders in UTC, which cannot be compared
        # textually against local-time `ps -o lstart=` output on non-UTC hosts).
        start: Any = rec.get("startedAt")
        if isinstance(start, bool) or not isinstance(start, (int, float)) or start <= 0:
            start = None
        elif start > 1e12:  # epoch in milliseconds
            start = start / 1000.0
        out[str(sid)] = {
            "pid": pid,
            "cwd": rec.get("cwd"),
            "procStart": start if start is not None else rec.get("procStart"),
            "status": rec.get("status"),
            "version": rec.get("version"),
        }
    _CLAUDE_MAP_CACHE.update({"key": key, "at": now, "map": dict(out)})
    return out


def resolve_claude_code(session_id: str) -> Dict[str, Any]:
    """Resolve a claude_code session_id to its target process descriptor.

    Returns ``{ok, pid, cwd, recorded_start, status, runtime}`` (ok=False with a
    ``reason`` when not found).
    """
    m = claude_code_session_map()
    rec = m.get(str(session_id))
    if not rec:
        return {"ok": False, "runtime": "claude_code",
                "reason": "session_not_in_claude_map", "session_id": session_id}
    return {
        "ok": True,
        "runtime": "claude_code",
        "pid": rec["pid"],
        "cwd": rec.get("cwd"),
        "recorded_start": rec.get("procStart"),
        "status": rec.get("status"),
        "session_id": session_id,
    }


# argv basename hints for the generic-by-cwd fallback runtimes.
_RUNTIME_ARGV_HINTS = {
    "codex": ("codex",),
    "goose": ("goose",),
    "opencode": ("opencode", "opencode-tui"),
    "aider": ("aider",),
    # GitHub Copilot CLI: the npm loader (`node /opt/homebrew/bin/copilot`)
    # spawns the platform binary (`…/@github/copilot-darwin-arm64/copilot`).
    # EXACT basename only: a substring hint also matched the VS Code
    # extension's `copilot-language-server`, whose cwd is routinely the
    # workspace root — the fallback would have SIGKILLed the user's editor
    # tooling (found in review).
    "copilot": ("copilot",),
    # qwen-code's CLI is a node bundle; "qwen" appears in both the launcher
    # basename and the bundle path. Fallback for resolve_qwen_code.
    "qwen_code": ("qwen",),
    # pi (badlogic/pi-mono) sets process.title = "pi"; exact-match only.
    "pi": ("pi",),
    # grok-cli is a single Rust binary at ~/.grok/bin/grok.
    "grok": ("grok",),
    # DeepSeek Harness CLI; exact-match only ("dsh" is a common substring).
    "deepseek_harness": ("dsh",),
    # Kimi CLI: python entry points `kimi` and `kimi-cli`.
    "kimi": ("kimi", "kimi-cli"),
    # Cursor CLI only (`node ~/.local/share/cursor-agent/versions/<v>/index.js`).
    # The IDE stays unsupported — see resolve_cursor.
    "cursor": ("cursor-agent",),
}

# Hints in this set must equal the process's argv basename exactly —
# substring matching for 2-3 letter names would hit pip/python ("pi") or any
# path containing "dsh".
_EXACT_ARGV_HINTS = frozenset({"pi", "dsh", "copilot"})

# Substrings that disqualify a candidate even when a hint matched: these are
# editor/language-server side processes that share a runtime's name but are
# NOT the per-session agent. Signaling one kills the user's editor tooling.
_ARGV_EXCLUDE = ("language-server", "language_server", "-lsp", "lsp-server",
                 "worker-server", "--stdio")


def _hint_matches(hints: Tuple[str, ...], name: str, blob: str) -> bool:
    """True when a process (argv[0] basename ``name``, full lowered cmdline
    ``blob``) matches one of the runtime's argv hints. Exact-set hints must
    equal the basename; everything else keeps the historical substring
    semantics. Editor/language-server side processes are excluded outright
    (see ``_ARGV_EXCLUDE``) — they share the runtime's name, run in the
    workspace root, and are never the per-session agent."""
    blob_l = (blob or "").lower()
    if any(bad in blob_l for bad in _ARGV_EXCLUDE):
        return False
    base = os.path.basename(name or "").lower()
    for h in hints:
        if h in _EXACT_ARGV_HINTS:
            if base == h:
                return True
            continue
        if h in base or h in blob_l:
            return True
    return False


def _copilot_logs_dir() -> str:
    """The directory Copilot CLI writes per-process logs into.

    Honors ``COPILOT_HOME`` (-> ``<dir>/logs/``), else ``~/.copilot/logs``,
    matching how the CLI resolves its state root.
    """
    base = os.environ.get("COPILOT_HOME")
    if base:
        return os.path.join(os.path.expanduser(base), "logs")
    return os.path.expanduser("~/.copilot/logs")


def resolve_copilot(session_id: str) -> Dict[str, Any]:
    """Resolve a GitHub Copilot CLI session_id to its process descriptor.

    Copilot CLI writes ``<logs>/process-<epoch_ms>-<pid>.log`` per run, and the
    log body records ``Workspace initialized: <session_id>``. That gives a
    claude_code-grade strong mapping: the pid comes from the FILENAME and the
    epoch_ms start doubles as ``recorded_start`` for the pid-reuse guard
    (verified live 2026-08-19 on Copilot CLI 1.0.77–1.0.80). Newest logs are
    scanned first and only their head is read (the marker lands in the first
    few lines). Never raises; returns ok=False with a reason when not found.
    """
    sid = str(session_id or "").strip()
    if not sid:
        return {"ok": False, "runtime": "copilot", "reason": "no_session_id"}
    d = _copilot_logs_dir()
    try:
        names = [n for n in os.listdir(d)
                 if n.startswith("process-") and n.endswith(".log")]
    except Exception:  # noqa: BLE001 - dir absent
        return {"ok": False, "runtime": "copilot",
                "reason": "no_copilot_logs_dir", "session_id": sid}
    # Filename embeds the start epoch_ms: newest first, bounded scan.
    names.sort(reverse=True)
    # ANCHORED: an unanchored substring let a truncated id ("1035fc8f")
    # resolve to a DIFFERENT session's pid — and because recorded_start comes
    # from that same filename, the pid-reuse guard would pass, producing a
    # correctly-guarded signal to the wrong session (found in review).
    import re as _re
    marker_re = _re.compile(
        r"Workspace initialized: " + _re.escape(sid) + r"(?![0-9A-Za-z_-])")
    for name in names[:200]:
        parts = name[len("process-"):-len(".log")].split("-")
        if len(parts) != 2:
            continue
        try:
            epoch_ms = int(parts[0])
            pid = int(parts[1])
        except ValueError:
            continue
        path = os.path.join(d, name)
        try:
            with open(path, "r", errors="replace") as fh:
                head = fh.read(16384)
        except Exception:  # noqa: BLE001
            continue
        if not marker_re.search(head):
            continue
        # The sidecar log is NOT removed when the run exits, so a stale entry
        # is normal. Skip dead pids instead of returning them: otherwise a
        # newer stale log masked a live session and suppressed the argv+cwd
        # fallback (found in review).
        if not is_alive(pid):
            continue
        return {
            "ok": True,
            "runtime": "copilot",
            "pid": pid,
            "cwd": None,
            "recorded_start": epoch_ms / 1000.0,
            "session_id": sid,
        }
    return {"ok": False, "runtime": "copilot",
            "reason": "session_not_in_copilot_logs", "session_id": sid}


def _qwen_projects_dir() -> str:
    """qwen-code's per-project state root (``~/.qwen/projects``)."""
    base = os.environ.get("QWEN_CODE_HOME") or os.environ.get("QWEN_HOME")
    if base:
        return os.path.join(os.path.expanduser(base), "projects")
    return os.path.expanduser("~/.qwen/projects")


def resolve_qwen_code(session_id: str) -> Dict[str, Any]:
    """Resolve a qwen-code session_id via its pid sidecar.

    qwen-code (0.16+) writes ``<projects>/<hash>/chats/<sessionId>.runtime.json``
    with ``{pid, session_id, work_dir, ...}`` on interactive start — explicitly
    for observability daemons. The sidecar is not deleted on exit and its
    ``started_at`` is the WRITE time (not proc start, wrong on resumed
    sessions), so instead of the start-token guard we cross-check that the
    live process still looks like qwen (argv) and runs in ``work_dir`` when a
    cwd is readable. Headless ``qwen -p`` runs never register — the caller
    falls back to argv+cwd. Never raises.
    """
    sid = str(session_id or "").strip()
    if not sid:
        return {"ok": False, "runtime": "qwen_code", "reason": "no_session_id"}
    # The session id becomes a filename component below. Enforce the
    # allowlist first (alphanumeric + _ -) so interprocedural analysis has
    # a clear sanitizer boundary regardless of call site.
    if not _QWEN_SID_RE.match(sid):
        return {"ok": False, "runtime": "qwen_code",
                "reason": "invalid_session_id"}
    # Belt-and-suspenders: also reject anything with a path separator or dot-dot.
    if "/" in sid or "\\" in sid or ".." in sid or os.path.basename(sid) != sid:
        return {"ok": False, "runtime": "qwen_code",
                "reason": "invalid_session_id"}
    root = _qwen_projects_dir()
    try:
        hashes = os.listdir(root)
    except Exception:  # noqa: BLE001 - dir absent
        return {"ok": False, "runtime": "qwen_code",
                "reason": "no_qwen_projects_dir", "session_id": sid}
    import json
    fname = sid + ".runtime.json"
    root_real = os.path.realpath(root)
    for h in hashes:
        path = os.path.realpath(os.path.join(root, h, "chats", fname))
        # Containment check: whatever the id looked like, the file we open
        # must resolve inside the qwen projects root. Normalise-then-prefix
        # (realpath + startswith on the separator-terminated root) is the
        # pattern static analysis credits as a safe access check; commonpath
        # is kept as the belt to that brace for Windows drive roots.
        if not path.startswith(root_real + os.sep):
            continue
        try:
            if os.path.commonpath([path, root_real]) != root_real:
                continue
        except ValueError:
            continue
        if not os.path.isfile(path):
            continue
        try:
            with open(path, "r") as fh:
                rec = json.load(fh)
        except Exception:  # noqa: BLE001
            continue
        if not isinstance(rec, dict):
            continue
        try:
            pid = int(rec.get("pid") or 0)
        except (TypeError, ValueError):
            pid = 0
        if pid <= 0 or not is_alive(pid):
            return {"ok": False, "runtime": "qwen_code",
                    "reason": "sidecar_pid_not_alive", "session_id": sid}
        # Sidecar start times are unreliable (the file records its WRITE
        # time), so identity is the guard instead — and it FAILS CLOSED: the
        # sidecar is not deleted on exit, so a stale pid recycled onto a
        # process whose cmdline we cannot read must be refused, never
        # signaled on liveness alone (found in review).
        blob = " ".join(_proc_cmdline(pid)).lower()
        if not blob:
            return {"ok": False, "runtime": "qwen_code",
                    "reason": "sidecar_pid_unverifiable", "session_id": sid}
        if "qwen" not in blob:
            return {"ok": False, "runtime": "qwen_code",
                    "reason": "sidecar_pid_not_qwen", "session_id": sid}
        work_dir = rec.get("work_dir") or None
        pcwd = _proc_cwd(pid)
        if work_dir and pcwd and (
                os.path.realpath(pcwd)
                != os.path.realpath(os.path.expanduser(str(work_dir)))):
            return {"ok": False, "runtime": "qwen_code",
                    "reason": "sidecar_pid_cwd_mismatch", "session_id": sid}
        return {"ok": True, "runtime": "qwen_code", "pid": pid,
                "cwd": work_dir, "recorded_start": None, "session_id": sid}
    return {"ok": False, "runtime": "qwen_code",
            "reason": "session_not_in_qwen_sidecars", "session_id": sid}


def _cursor_cli_session_exists(session_id: str) -> bool:
    """True when ``session_id`` is a Cursor **CLI** session.

    Cursor CLI writes ``<chats>/<md5(cwd)>/<session-id>/meta.json`` per
    session (verified live 2026-08-19); IDE conversations live in the
    editor's own store under different ids. Without this check, a stop
    request for an IDE conversation resolved to whatever ``cursor-agent``
    process happened to share the directory — killing an unrelated terminal
    agent and reporting success (found in review). Never raises."""
    sid = str(session_id or "").strip()
    if not sid or os.sep in sid or sid in (".", ".."):
        return False
    root = os.path.expanduser(
        os.environ.get("CLAWMETRY_CURSOR_CHATS_ROOT")
        or os.path.join("~", ".cursor", "chats"))
    try:
        for hashed in os.listdir(root):
            if os.path.isdir(os.path.join(root, hashed, sid)):
                return True
    except Exception:  # noqa: BLE001 - absent dir / permission
        return False
    return False


def resolve_cursor(session_id: str, cwd: str) -> Dict[str, Any]:
    """Cursor: CLI sessions (``cursor-agent``) run one process tree per
    session and ARE killable; IDE (GUI) conversations share the single editor
    process and are not.

    Support is decided PER SESSION (see ``SPLIT_SUPPORT_RUNTIMES``), and the
    CLI half must be PROVEN, not assumed: we require the session to exist in
    Cursor's CLI chat store before we will resolve any pid for it. Anything
    else — an IDE conversation, an unknown id — gets the honest refusal."""
    if not _cursor_cli_session_exists(session_id):
        return {"ok": False, "runtime": "cursor", "unsupported": True,
                "reason": "cursor_single_ide_process_no_per_session_signal",
                "session_id": session_id}
    if cwd:
        hit = resolve_by_cwd("cursor", cwd)
        if hit.get("ok"):
            return hit
    return {"ok": False, "runtime": "cursor",
            "reason": "cursor_cli_session_process_not_found",
            "session_id": session_id}


#: Per-session resolvers for SPLIT_SUPPORT_RUNTIMES (see that constant).
_SPLIT_RESOLVERS = {"cursor": resolve_cursor}


def resolve_by_cwd(runtime: str, cwd: str) -> Dict[str, Any]:
    """Generic fallback for codex/goose/opencode/aider: find a candidate process
    whose argv basename matches the runtime AND whose cwd matches ``cwd``.

    ``cwd`` is taken from the session's adapter extra (goose ``workingDir``,
    opencode ``directory``; codex/aider derivable from on-disk paths). Uses
    psutil if available, else ps/lsof. Returns the lowest-pid match (most likely
    the top-level CLI rather than a child). Never raises.
    """
    runtime = (runtime or "").lower()
    if not cwd:
        return {"ok": False, "runtime": runtime, "reason": "no_cwd"}
    hints = _RUNTIME_ARGV_HINTS.get(runtime)
    if not hints:
        return {"ok": False, "runtime": runtime, "reason": "runtime_not_cwd_resolvable"}
    target_cwd = os.path.realpath(os.path.expanduser(cwd))

    candidates: List[int] = []
    if _psutil is not None:
        try:
            for proc in _psutil.process_iter(["pid", "name", "cmdline"]):
                try:
                    argv = proc.info.get("cmdline") or []
                    name = (proc.info.get("name") or "")
                    blob = " ".join([name] + list(argv)).lower()
                    base_name = name or (argv[0] if argv else "")
                    if not _hint_matches(hints, base_name, blob):
                        continue
                    pcwd = None
                    try:
                        pcwd = proc.cwd()
                    except Exception:  # noqa: BLE001
                        pcwd = None
                    if pcwd and os.path.realpath(pcwd) == target_cwd:
                        candidates.append(int(proc.info["pid"]))
                except Exception:  # noqa: BLE001
                    continue
        except Exception:  # noqa: BLE001
            candidates = []
    else:
        for cpid, _ppid, _pgid in _all_procs_ps():
            argv = _proc_cmdline(cpid)
            if not argv:
                continue
            blob = " ".join(argv).lower()
            if not _hint_matches(hints, argv[0], blob):
                continue
            pcwd = _proc_cwd(cpid)
            if pcwd and os.path.realpath(pcwd) == target_cwd:
                candidates.append(cpid)

    if not candidates:
        return {"ok": False, "runtime": runtime, "reason": "no_matching_process",
                "cwd": target_cwd}
    pid = _pick_session_pid(candidates)
    if pid is None:
        # Two sibling sessions of the same runtime in the same directory is
        # the ordinary case (two terminals, one repo). Picking the lowest pid
        # would stop somebody else's session and report success, so refuse
        # and say why (found in review).
        return {"ok": False, "runtime": runtime,
                "reason": "ambiguous_candidates", "cwd": target_cwd,
                "candidates": sorted(candidates)}
    return {
        "ok": True,
        "runtime": runtime,
        "pid": pid,
        "cwd": target_cwd,
        # No recorded start for cwd-resolved procs; the guard becomes a liveness
        # check only (we just located this pid live by cwd+argv, so reuse risk is
        # negligible for the immediate signal).
        "recorded_start": None,
        "candidates": candidates,
    }


def native_session_id(runtime: str, session_id: str) -> str:
    """Strip the store's ``<runtime>:`` namespace off a session id.

    ``sync.sync_family_runtimes`` namespaces every family-runtime session as
    ``f"{runtime}:{s.id}"``, and that prefixed id is what the Guard tab, the
    policy engine and the cloud relay all carry. The runtimes themselves know
    only the NATIVE id — Claude Code records a bare uuid in
    ``~/.claude/sessions/<pid>.json`` — so every resolver below looked up
    ``claude_code:<uuid>`` in a map keyed by ``<uuid>``, missed, and
    Pause/Stop/Kill answered ``session_not_in_claude_map``.

    That made the kill switch inert for every non-OpenClaw runtime, through
    BOTH doors: the Guard tab's buttons and the daemon's policy actuator
    (``sync._emit_detector_incidents`` feeds the same store id to the same
    resolver). OpenClaw was unaffected only because its ids are bare.

    Only an exact ``<runtime>:`` head is removed, so a native id that itself
    contains a colon keeps every character after the first one.
    """
    rt = (runtime or "").strip().lower()
    sid = str(session_id or "")
    if rt and sid.lower().startswith(rt + ":"):
        return sid[len(rt) + 1:]
    return sid


def resolve_session(runtime: str, session_id: str = "",
                    cwd: str = "") -> Dict[str, Any]:
    """Resolve any supported runtime's session to a process descriptor.

    * claude_code -> per-pid session-json map (primary).
    * copilot -> per-process log-filename map (primary), argv+cwd fallback.
    * qwen_code -> pid sidecar (primary), argv+cwd fallback.
    * codex/goose/opencode/aider/pi/grok/deepseek_harness/kimi -> generic
      cwd+argv match.
    * cursor -> CLI sessions by cwd+argv; the IDE stays unsupported.
    * anything else -> unsupported.
    """
    runtime = (runtime or "").lower()
    # Store ids are namespaced ``<runtime>:<native id>``; every resolver below
    # matches on the native id the runtime itself writes.
    session_id = native_session_id(runtime, session_id)
    if runtime in SPLIT_SUPPORT_RUNTIMES:
        # Support decided per session, not per runtime (today: cursor).
        return _SPLIT_RESOLVERS[runtime](session_id, cwd)
    if runtime in UNSUPPORTED_RUNTIMES:
        return {"ok": False, "runtime": runtime, "unsupported": True,
                "reason": "runtime_not_signal_supported"}
    if runtime == "claude_code":
        return resolve_claude_code(session_id)
    if runtime == "copilot":
        info = resolve_copilot(session_id)
        if info.get("ok") or not cwd:
            return info
        return resolve_by_cwd(runtime, cwd)
    if runtime == "qwen_code":
        info = resolve_qwen_code(session_id)
        if info.get("ok") or not cwd:
            return info
        return resolve_by_cwd(runtime, cwd)
    if runtime in _RUNTIME_ARGV_HINTS:
        return resolve_by_cwd(runtime, cwd)
    return {"ok": False, "runtime": runtime, "unsupported": True,
            "reason": "runtime_not_signal_supported"}


# ──────────────────────────────────────────────────────────────────────────
# High-level, guarded session control (what sync.py calls)
# ──────────────────────────────────────────────────────────────────────────
def kill_session(runtime: str, session_id: str = "", cwd: str = "",
                 mode: str = "kill") -> Dict[str, Any]:
    """Kill (or softly stop) a family-runtime session.

    ``mode == 'stop'`` sends the soft SIGINT (cancel current turn); any other
    mode does a graceful_kill (SIGTERM -> escalate to SIGKILL of the tree).
    """
    if mode == "stop":
        return _guarded("stop_turn", runtime, session_id, cwd,
                        lambda pid: stop_turn(pid, runtime))
    return _guarded("graceful_kill", runtime, session_id, cwd,
                    lambda pid: graceful_kill(pid, runtime))


def pause_session(runtime: str, session_id: str = "", cwd: str = "") -> Dict[str, Any]:
    """Pause a family-runtime session (SIGSTOP the tree)."""
    return _guarded("pause", runtime, session_id, cwd,
                    lambda pid: pause(pid, runtime))


def resume_session(runtime: str, session_id: str = "", cwd: str = "") -> Dict[str, Any]:
    """Resume a paused family-runtime session (SIGCONT the tree)."""
    return _guarded("resume", runtime, session_id, cwd,
                    lambda pid: resume(pid, runtime))


