"""clawmetry/daemon_registration.py — one place that knows how to make the
sync daemon survive a reboot/logoff/crash, on every OS.

Root cause this exists to fix: three call sites (``clawmetry connect``,
``clawmetry onboard`` self-host, and the browser cloud-connect flow in
dashboard.py) each carried their own slightly-different copy of "register a
persistent daemon" -- and the browser SELF-HOST onboarding gate
(routes/onboarding.py, the now-default install path since the 2026-07-31
hard-gate rollout) carried none at all, so a plain
``pip install clawmetry && clawmetry`` that finished onboarding in the
browser never got a background service. The only thing polling PyPI was the
foreground dashboard process's in-thread checker (dashboard.py
start_update_check_thread), which stops the moment that process exits --
closed terminal, sleep, reboot, crash. Auto-update then silently never
resumes until the user manually relaunches ``clawmetry``.

``ensure_persistent_daemon(config)`` is the single entry point every one of
those call sites should use. It registers real OS-level supervision
(launchd KeepAlive / systemd Restart=always / Windows Scheduled Task with
restart-on-failure) so *something* is always alive to run the sync daemon's
fast auto-update loop, independent of whether the dashboard is open.
"""

from __future__ import annotations

import os
import sys


def _log_file_path() -> str:
    try:
        from clawmetry.sync import LOG_FILE
        return str(LOG_FILE)
    except Exception:
        return os.path.expanduser("~/.clawmetry/sync.log")


def _is_root() -> bool:
    return hasattr(os, "geteuid") and os.geteuid() == 0


def _is_sync_running() -> bool:
    """Liveness probe for the sync daemon.

    Prefers the daemon's own PID lock (``~/.clawmetry/sync.pid`` +
    ``process_control.is_alive``) over a ``pgrep -f`` substring match:
    ``pgrep -f "clawmetry.*sync"`` matches against a process's *entire*
    command line, so it false-positives on anything that merely mentions
    both words — a shell wrapper, an editor, a CI step, even an unrelated
    diagnostic command — not just a genuinely running daemon. A false
    positive here makes ``register_systemd``'s post-registration check
    silently report success on containers without systemd (the exact case
    this module exists to cover), leaving nothing actually supervising the
    daemon. Fall back to pgrep only if the PID file is unreadable.
    """
    try:
        from clawmetry.sync import _pid_file
        from clawmetry.process_control import is_alive

        pid_path = _pid_file()
        if pid_path.exists():
            return is_alive(int(pid_path.read_text().strip()))
        return False
    except Exception:
        pass

    import subprocess
    try:
        r = subprocess.run(
            ["pgrep", "-f", "clawmetry.*sync"], capture_output=True, timeout=3
        )
        return r.returncode == 0
    except Exception:
        return False


def register_launchd(config: dict) -> bool:
    """macOS: install + bootstrap a launchd agent with KeepAlive."""
    import pathlib
    import subprocess

    label = "com.clawmetry.sync"
    plist_path = pathlib.Path.home() / "Library" / "LaunchAgents" / f"{label}.plist"
    python = sys.executable
    plist = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>             <string>{label}</string>
    <key>ProgramArguments</key>
    <array>
        <string>{python}</string>
        <string>-m</string>
        <string>clawmetry.sync</string>
    </array>
    <key>EnvironmentVariables</key>
    <dict>
        <key>CLAWMETRY_ENABLE_WS_TAP</key><string>1</string>
    </dict>
    <key>RunAtLoad</key>         <true/>
    <key>KeepAlive</key>         <true/>
    <key>StandardOutPath</key>   <string>{_log_file_path()}</string>
    <key>StandardErrorPath</key> <string>{_log_file_path()}</string>
    <key>ThrottleInterval</key>  <integer>30</integer>
</dict>
</plist>"""
    try:
        plist_path.parent.mkdir(parents=True, exist_ok=True)
        plist_path.write_text(plist)
        uid = os.getuid()
        r = subprocess.run(
            ["launchctl", "bootstrap", f"gui/{uid}", str(plist_path)],
            capture_output=True, check=False, timeout=8,
        )
        if r.returncode != 0:
            subprocess.run(
                ["launchctl", "load", "-w", str(plist_path)],
                capture_output=True, check=False, timeout=8,
            )
        return True
    except Exception:
        return False


def register_systemd(config: dict) -> bool:
    """Linux: install a systemd unit (system scope for root, --user otherwise)
    with Restart=always, and verify it actually came up."""
    import pathlib
    import shutil
    import subprocess
    import time

    label = "clawmetry-sync"
    python = sys.executable
    root = _is_root()
    service_dir = (
        pathlib.Path("/etc/systemd/system") if root
        else pathlib.Path.home() / ".config" / "systemd" / "user"
    )
    wanted_by = "multi-user.target" if root else "default.target"
    scope = [] if root else ["--user"]
    extra_unit = "User=root\n" if root else ""

    unit = f"""[Unit]
Description=ClawMetry Cloud Sync Daemon
After=network.target

[Service]
ExecStart={python} -m clawmetry.sync
Environment=CLAWMETRY_ENABLE_WS_TAP=1
{extra_unit}Restart=always
RestartSec=30
StandardOutput=append:{_log_file_path()}
StandardError=append:{_log_file_path()}

[Install]
WantedBy={wanted_by}
"""
    if not shutil.which("systemctl"):
        return False
    try:
        service_dir.mkdir(parents=True, exist_ok=True)
        (service_dir / f"{label}.service").write_text(unit)
        # Root cause of a real CI regression (2026-08-06): these three calls
        # had no timeout, and this whole function runs synchronously inside
        # the onboarding-complete HTTP handler. A CI/container runner with no
        # user systemd instance / dbus session can make `systemctl --user
        # enable --now` hang rather than fail fast, which blocked the
        # browser's onboarding-complete request indefinitely -- the visible
        # symptom was the dashboard stuck forever on "Initializing
        # ClawMetry". Bound every call so the worst case is a few seconds,
        # never a hang.
        subprocess.run(["systemctl", *scope, "daemon-reload"],
                        check=False, capture_output=True, timeout=8)
        subprocess.run(["systemctl", *scope, "enable", "--now", label],
                        check=False, capture_output=True, timeout=8)
        time.sleep(1.0)
        chk = subprocess.run(["systemctl", *scope, "is-active", label],
                              capture_output=True, text=True, timeout=8)
        return chk.stdout.strip() == "active" or _is_sync_running()
    except Exception:
        return False


WINDOWS_TASK_NAME = "ClawMetrySyncDaemon"


def register_windows_task(config: dict) -> bool:
    """Windows: register a Scheduled Task that runs the daemon at logon and
    restarts it on failure, matching launchd KeepAlive / systemd
    Restart=always. Windows has no user-mode equivalent of a supervised
    service short of Task Scheduler; without this, nothing brings the daemon
    back after a reboot or logoff, so a node silently stops polling PyPI
    until someone manually relaunches ``clawmetry``.
    """
    import subprocess
    import tempfile

    python = sys.executable
    # pythonw would hide console output entirely; use the same interpreter
    # the rest of the daemon-registration paths use so `-m clawmetry.sync`
    # behaves identically to a manual launch.
    command = f'"{python}" -m clawmetry.sync'
    xml = f"""<?xml version="1.0" encoding="UTF-16"?>
<Task version="1.2" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">
  <Triggers>
    <LogonTrigger>
      <Enabled>true</Enabled>
    </LogonTrigger>
  </Triggers>
  <Principal>
    <LogonType>InteractiveToken</LogonType>
    <RunLevel>LeastPrivilege</RunLevel>
  </Principal>
  <Settings>
    <MultipleInstancesPolicy>IgnoreNew</MultipleInstancesPolicy>
    <DisallowStartIfOnBatteries>false</DisallowStartIfOnBatteries>
    <StopIfGoingOnBatteries>false</StopIfGoingOnBatteries>
    <StartWhenAvailable>true</StartWhenAvailable>
    <RestartOnFailure>
      <Interval>PT1M</Interval>
      <Count>999</Count>
    </RestartOnFailure>
    <ExecutionTimeLimit>PT0S</ExecutionTimeLimit>
  </Settings>
  <Actions>
    <Exec>
      <Command>{python}</Command>
      <Arguments>-m clawmetry.sync</Arguments>
    </Exec>
  </Actions>
</Task>"""
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".xml", delete=False, encoding="utf-16"
        ) as fh:
            fh.write(xml)
            xml_path = fh.name
        try:
            r = subprocess.run(
                ["schtasks", "/create", "/tn", WINDOWS_TASK_NAME,
                 "/xml", xml_path, "/f"],
                capture_output=True, check=False, timeout=8,
            )
            created = r.returncode == 0
            if created:
                # /create with a LogonTrigger doesn't start it immediately —
                # run it now so the daemon starts this session too, not just
                # after the next logon.
                subprocess.run(["schtasks", "/run", "/tn", WINDOWS_TASK_NAME],
                                capture_output=True, check=False, timeout=8)
            return created
        finally:
            try:
                os.remove(xml_path)
            except OSError:
                pass
    except Exception:
        return False


def windows_task_registered() -> bool:
    """Best-effort probe: is the scheduled task from register_windows_task
    present? Mirrors the launchd-plist / systemd-unit existence checks
    routes/update_check.py uses for _daemon_supervised()."""
    import subprocess
    try:
        r = subprocess.run(
            ["schtasks", "/query", "/tn", WINDOWS_TASK_NAME],
            capture_output=True, check=False, timeout=8,
        )
        return r.returncode == 0
    except Exception:
        return False


def start_background_subprocess() -> bool:
    """Last-resort fallback when no OS-level supervisor is available
    (systemd missing in a container, schtasks failed, etc.): a detached
    subprocess that at least survives the launching terminal closing, even
    though it will not survive a reboot/crash."""
    import subprocess
    import pathlib

    sync_script = str(pathlib.Path(__file__).parent / "sync.py")
    log_path = pathlib.Path.home() / ".clawmetry" / "sync.log"
    try:
        log_path.parent.mkdir(parents=True, exist_ok=True)
    except Exception:
        pass

    import shutil
    cmd = (
        ["setsid", sys.executable, sync_script]
        if shutil.which("setsid")
        else [sys.executable, sync_script]
    )
    spawn_kwargs = {"stdin": subprocess.DEVNULL, "close_fds": True}
    if os.name == "nt":
        spawn_kwargs["creationflags"] = (
            subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP
        )
    else:
        spawn_kwargs["start_new_session"] = True
    try:
        log_fh = open(str(log_path), "a")
        try:
            subprocess.Popen(cmd, stdout=log_fh, stderr=subprocess.STDOUT, **spawn_kwargs)
        finally:
            log_fh.close()
        return True
    except Exception:
        return False


def ensure_persistent_daemon(config: dict | None = None) -> bool:
    """Register (or start) a persistent sync daemon appropriate for this OS.

    Returns True on a best-effort success signal, False if every mechanism
    failed (still safe to call — never raises). Idempotent: safe to call
    repeatedly (e.g. once per onboarding-completion request).
    """
    config = config or {}
    try:
        from clawmetry.sync import ensure_local_config
        ensure_local_config()
    except Exception:
        pass

    system = __import__("platform").system()
    if system == "Darwin":
        if register_launchd(config):
            return True
    elif system == "Linux":
        if register_systemd(config):
            return True
    elif os.name == "nt":
        if register_windows_task(config):
            return True
    return start_background_subprocess()
