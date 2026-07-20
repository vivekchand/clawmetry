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
* **Cross-platform.** macOS and Linux are first-class. Windows / other POSIX
  return an honest ``unsupported`` result rather than guessing (POSIX job-control
  signals like SIGSTOP/SIGCONT do not exist on Windows).
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
_POSIX = os.name == "posix" and (_IS_MACOS or _IS_LINUX)

# Default bound for graceful_kill's SIGTERM->SIGKILL escalation window.
_DEFAULT_GRACE_SECS = 5.0

# Runtimes whose per-session process we can locate + signal. cursor is omitted
# on purpose (single shared IDE process). openclaw is handled by the CLI cancel
# path in sync.py, not here.
SUPPORTED_RUNTIMES = frozenset(
    {"claude_code", "codex", "goose", "opencode", "aider"}
)
UNSUPPORTED_RUNTIMES = frozenset({"cursor"})


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
    can't report it on this platform).
    """
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


def stop_turn(pid: int, runtime: str = "") -> Dict[str, Any]:
    """Cancel the CURRENT turn of a Node-CLI agent by sending SIGINT to the
    MAIN pid only (the cleanest non-destructive stop — mirrors the user hitting
    Ctrl-C in the CLI). We do NOT signal the group: a group SIGINT can tear down
    in-flight tool shells and the TUI in ways the CLI doesn't expect.
    """
    if not _POSIX:
        return _result(False, "stop_turn", pid, runtime, "unsupported_platform")
    if not is_alive(pid):
        return _result(False, "stop_turn", pid, runtime, "pid_not_alive")
    ok = _signal_pid(pid, signal.SIGINT)
    return _result(ok, "stop_turn", pid, runtime,
                   "sigint_sent" if ok else "sigint_failed")


def graceful_kill(pid: int, runtime: str = "",
                  grace_secs: float = _DEFAULT_GRACE_SECS) -> Dict[str, Any]:
    """SIGTERM the main pid, wait up to ``grace_secs`` for it to exit, then
    escalate to SIGKILL of the FULL descendant set if it is still alive.

    The escalation kills the whole tree (descendants first, then the parent) so
    a detached tool shell can't outlive its agent. Bounded poll, never hangs.
    """
    if not _POSIX:
        return _result(False, "graceful_kill", pid, runtime, "unsupported_platform")
    if not is_alive(pid):
        return _result(True, "graceful_kill", pid, runtime, "already_dead")

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
    if not _POSIX:
        return _result(False, "pause", pid, runtime, "unsupported_platform")
    if not is_alive(pid):
        return _result(False, "pause", pid, runtime, "pid_not_alive")

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
    if not _POSIX:
        return _result(False, "resume", pid, runtime, "unsupported_platform")
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

    out: Dict[str, Dict[str, Any]] = {}
    d = _claude_sessions_dir()
    try:
        names = os.listdir(d)
    except Exception:  # noqa: BLE001 - dir absent
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
}


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
                    if not any(h in os.path.basename(name).lower() or h in blob
                               for h in hints):
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
            base = os.path.basename(argv[0]).lower() if argv else ""
            if not any(h in base or h in blob for h in hints):
                continue
            pcwd = _proc_cwd(cpid)
            if pcwd and os.path.realpath(pcwd) == target_cwd:
                candidates.append(cpid)

    if not candidates:
        return {"ok": False, "runtime": runtime, "reason": "no_matching_process",
                "cwd": target_cwd}
    pid = min(candidates)
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


def resolve_session(runtime: str, session_id: str = "",
                    cwd: str = "") -> Dict[str, Any]:
    """Resolve any supported runtime's session to a process descriptor.

    * claude_code -> per-pid session-json map (primary).
    * codex/goose/opencode/aider -> generic cwd+argv match.
    * cursor -> explicit unsupported (single IDE process).
    * anything else -> unsupported.
    """
    runtime = (runtime or "").lower()
    if runtime in UNSUPPORTED_RUNTIMES:
        return {"ok": False, "runtime": runtime, "unsupported": True,
                "reason": "cursor_single_ide_process_no_per_session_signal"}
    if runtime == "claude_code":
        return resolve_claude_code(session_id)
    if runtime in _RUNTIME_ARGV_HINTS:
        return resolve_by_cwd(runtime, cwd)
    return {"ok": False, "runtime": runtime, "unsupported": True,
            "reason": "runtime_not_signal_supported"}


# ──────────────────────────────────────────────────────────────────────────
# High-level, guarded session control (what sync.py calls)
# ──────────────────────────────────────────────────────────────────────────
def _guarded(action_name: str, runtime: str, session_id: str, cwd: str,
             fn) -> Dict[str, Any]:
    """Resolve the session, run the pid-reuse guard, then call ``fn(pid)``.

    Returns a structured result. Never raises. ``fn`` is one of the signal
    helpers (stop_turn / graceful_kill / pause / resume).
    """
    if not _POSIX:
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
