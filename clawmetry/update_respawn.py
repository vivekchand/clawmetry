"""clawmetry/update_respawn.py — Windows out-of-process updater.

Why this exists: on Windows, pip cannot replace ``Scripts/clawmetry.exe``
while any process is running it, and — measured on a real Windows 10 box,
2026-07-28 — even RENAMING the running launcher fails with WinError 32, so
the pre-rename trick in ``perform_self_update`` silently does nothing there
and every in-process auto-update dies with
``WinError 32 ... clawmetry.exe``. The only reliable order on Windows is:

  1. this helper is spawned DETACHED by the process that wants to update,
  2. the parent exits (its locks vanish with it),
  3. the helper waits for the parent pid to terminate,
  4. the helper runs ``pip install --upgrade clawmetry==<target>``,
  5. the helper relaunches the parent's exact command line, detached,
  6. output goes to ``~/.clawmetry/restart.log``.

The helper deliberately runs the OLD wheel's copy of this module (it is
spawned before pip runs) and therefore keeps zero non-stdlib imports and no
imports from the rest of clawmetry.

Usage (spawned by routes/update_check.py, not humans):

    python -m clawmetry.update_respawn <parent_pid> <target_version> \
        <log_path> <relaunch_cmd...>
"""

from __future__ import annotations

import os
import subprocess
import sys
import time

_DETACHED = 0x00000008 | 0x00000200  # DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP
# This helper runs DETACHED (no console). Any console-subsystem child it
# spawns WITHOUT this flag gets a brand-new VISIBLE console window — pip
# runs for seconds-to-minutes, so users watch a mystery cmd window sit on
# their screen (live-hit during an enterprise demo, 2026-08-08).
_NO_WINDOW = 0x08000000  # CREATE_NO_WINDOW


def _wait_for_pid_exit(pid: int, timeout_secs: float = 60.0) -> bool:
    """Block until ``pid`` is gone (True) or the timeout passes (False)."""
    if os.name == "nt":
        try:
            import ctypes

            SYNCHRONIZE = 0x00100000
            h = ctypes.windll.kernel32.OpenProcess(SYNCHRONIZE, False, int(pid))
            if not h:
                return True  # already gone
            try:
                # WAIT_OBJECT_0 == 0 means the process terminated.
                rc = ctypes.windll.kernel32.WaitForSingleObject(
                    h, int(timeout_secs * 1000)
                )
                return rc == 0
            finally:
                ctypes.windll.kernel32.CloseHandle(h)
        except Exception:
            pass
    # POSIX / fallback: poll for existence.
    deadline = time.time() + timeout_secs
    while time.time() < deadline:
        try:
            os.kill(int(pid), 0)
        except OSError:
            return True
        time.sleep(0.5)
    return False


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if len(argv) < 4:
        print("usage: update_respawn <parent_pid> <target> <log> <cmd...>")
        return 2
    parent_pid, target, log_path = argv[0], argv[1], argv[2]
    relaunch_cmd = argv[3:]
    try:
        int(parent_pid)
    except (TypeError, ValueError):
        print(f"update_respawn: invalid parent pid {parent_pid!r}")
        return 2

    try:
        os.makedirs(os.path.dirname(log_path), exist_ok=True)
    except Exception:
        pass
    log = open(log_path, "ab", buffering=0)

    def _say(msg: str) -> None:
        try:
            log.write((time.strftime("%Y-%m-%d %H:%M:%S ") + msg + "\n").encode())
        except Exception:
            pass

    _say(f"[update-respawn] waiting for parent pid {parent_pid} to exit")
    if not _wait_for_pid_exit(int(parent_pid), timeout_secs=90.0):
        _say("[update-respawn] parent did not exit in 90s; aborting (no relaunch, "
             "the still-running parent keeps serving)")
        return 1

    spec = f"clawmetry=={target}" if target and target != "latest" else "clawmetry"
    _say(f"[update-respawn] parent gone; pip install --upgrade {spec}")
    ok = False
    try:
        # Retry ladder sized for the two real failure modes seen live
        # (2026-07-28): the PyPI simple-index propagation lag (the JSON API
        # advertises a release 1-3 minutes before pip can install it) and a
        # sibling process briefly holding the launcher exe. 10s+10s was too
        # short for either.
        for attempt, wait in ((1, 20), (2, 60), (3, 120)):
            pip_kwargs = {"stdout": log, "stderr": log, "timeout": 300}
            if os.name == "nt":
                pip_kwargs["creationflags"] = _NO_WINDOW
            proc = subprocess.run(
                [sys.executable, "-m", "pip", "install", "--upgrade",
                 "--no-cache-dir", spec],
                **pip_kwargs,
            )
            if proc.returncode == 0:
                ok = True
                break
            _say(f"[update-respawn] pip attempt {attempt} failed "
                 f"(exit {proc.returncode}); retrying in {wait}s")
            time.sleep(wait)
    finally:
        # Release the cross-process update lock the PARENT was holding when
        # it handed off (see routes/update_check.py): the lock now rides
        # through the handoff so a sibling process cannot start a concurrent
        # pip while this helper works — the exact race that bricked
        # site-packages metadata on the 0.12.580 run.
        try:
            os.remove(os.path.expanduser("~/.clawmetry/update-in-progress.lock"))
        except OSError:
            pass

    _say(f"[update-respawn] install {'succeeded' if ok else 'FAILED'}; "
         f"relaunching: {relaunch_cmd}")
    # Relaunch EITHER WAY: a failed install must still bring the service back
    # on the old version rather than leaving the machine with nothing running.
    #
    # PYTHONIOENCODING / PYTHONUTF8 are load-bearing: the relaunched process
    # writes stdout to THIS LOG FILE (not a console), so Python picks the
    # locale codec — cp1252 on Windows — and the startup banner's arrows and
    # emoji die with UnicodeEncodeError, killing the freshly updated
    # dashboard right after a perfect install (live-hit on the 0.12.579
    # unattended run, 2026-07-28; same encoding class as the #3791 CLI bug).
    env = dict(os.environ)
    env.setdefault("PYTHONIOENCODING", "utf-8")
    env.setdefault("PYTHONUTF8", "1")
    kwargs = {"stdin": subprocess.DEVNULL, "stdout": log, "stderr": log,
              "close_fds": True, "env": env}
    if os.name == "nt":
        kwargs["creationflags"] = _DETACHED
    else:
        kwargs["start_new_session"] = True
    subprocess.Popen(relaunch_cmd, **kwargs)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
