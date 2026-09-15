"""clawmetry/fleet_install.py — register the collector for shared and virtual
desktops (multi-session Windows hosts, pooled images, shared Linux hosts).

Design (Factory requirement "Fleet Install on Shared and Virtual Desktops"):
one collector PER USER, running AS that user. The collector reads agent files
in the user's own profile and writes a local store holding their session
content, so a single privileged service reading every profile would break
per-user isolation and collapse every user into one node identity.

* Linux: the per-user systemd unit (daemon_registration.register_systemd)
  plus logind linger, so the user manager keeps the collector alive after the
  user's last session ends. Without linger, logout stops the unit.
* Windows: one machine-wide Scheduled Task whose principal is the built-in
  Users group (S-1-5-32-545) with a logon trigger for any user. Task
  Scheduler starts a separate instance in each signed-in user's session under
  that user's own token, least privilege. It ends at logoff with the session;
  data already on disk is picked up again at next logon.

Every function here returns an explicit state instead of raising, so the CLI
can print what was achieved and what was not.
"""

from __future__ import annotations

import getpass
import os
import stat
import subprocess
import sys
from pathlib import Path

#: Machine-wide task registered by ``clawmetry service install --all-users``.
#: Distinct from daemon_registration.WINDOWS_TASK_NAME (the per-user task) so
#: removing one never removes the other.
WINDOWS_ALL_USERS_TASK_NAME = "ClawMetrySyncDaemonAllUsers"

#: Well-known SID of BUILTIN\\Users. A SID, not the localized group name, so
#: registration works on non-English Windows images.
_USERS_GROUP_SID = "S-1-5-32-545"


def data_dir() -> Path:
    return Path.home() / ".clawmetry"


# ── data-directory privacy ────────────────────────────────────────────────────


def data_dir_private(path: Path | None = None) -> dict:
    """Is the local data directory unreadable by other local users?

    POSIX only: checks group/other permission bits. On Windows the profile
    directory ACL (owner, SYSTEM, Administrators) already restricts it, which
    we report rather than claim to have verified bit by bit.
    """
    path = path or data_dir()
    if os.name == "nt":
        # Not verified: redirected or roaming (FSLogix) profiles can carry a
        # different ACL, so "unknown" is the honest answer, never "yes".
        return {"path": str(path), "private": None,
                "basis": "windows_profile_acl_not_checked"}
    try:
        mode = stat.S_IMODE(path.stat().st_mode)
    except FileNotFoundError:
        return {"path": str(path), "private": True, "basis": "absent"}
    except OSError as exc:
        return {"path": str(path), "private": False,
                "basis": f"unreadable: {exc.__class__.__name__}"}
    return {"path": str(path), "private": (mode & 0o077) == 0,
            "basis": "mode", "mode": oct(mode)}


def restrict_data_dir(path: Path | None = None) -> dict:
    """Create the data dir 0700, or remove group/other bits from an existing
    one owned by this user. Never touches a directory owned by someone else."""
    path = path or data_dir()
    if os.name == "nt":
        return data_dir_private(path)
    try:
        path.mkdir(mode=0o700, parents=True, exist_ok=True)
        st = path.stat()
        if hasattr(os, "geteuid") and st.st_uid != os.geteuid():
            out = data_dir_private(path)
            out["basis"] = "owned_by_another_user"
            return out
        mode = stat.S_IMODE(st.st_mode)
        if mode & 0o077:
            os.chmod(path, mode & 0o700)
    except OSError:
        pass
    return data_dir_private(path)


# ── self-update in an administrator-owned install ─────────────────────────────


def _isolated_env() -> bool:
    """A venv (or virtualenv) interpreter: pip cannot fall back to a per-user
    install there, so an unwritable environment cannot be upgraded at all."""
    return (getattr(sys, "base_prefix", sys.prefix) != sys.prefix
            or hasattr(sys, "real_prefix"))


def _package_parent() -> Path:
    """The directory pip writes the clawmetry package into (site-packages)."""
    import clawmetry
    return Path(clawmetry.__file__).resolve().parent.parent


def _dir_writable(path: Path) -> bool:
    """Try ONE exclusive create of a probe file, then delete it.

    ``os.access`` is not used: on Windows it ignores ACLs, so it reports
    Program Files writable for every user. ``tempfile.mkstemp`` is not used
    either: on Windows, when a create is denied but ``os.access`` says the
    directory is writable, it keeps retrying new names up to ``TMP_MAX``
    (hundreds of millions on current CPython). Under a deny ACL that ran for
    24 minutes on a CI runner, and a collector would hang the same way.
    """
    import secrets

    probe = os.path.join(str(path), f".clawmetry-write-probe-{os.getpid()}-{secrets.token_hex(6)}")
    try:
        fd = os.open(probe, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError:
        return True  # someone created that name in this directory, so it is writable
    except OSError:
        return False
    try:
        os.close(fd)
        os.remove(probe)
    except OSError:
        pass
    return True


def self_update_blocked(package_parent: Path | None = None,
                        isolated: bool | None = None) -> dict:
    """Can this process upgrade its own install (AC-OBS-FLEET-001.4)?

    ``blocked`` is True only for an isolated environment the running user
    cannot write, which is exactly what both fleet recipes create
    (``C:\\Program Files\\ClawMetry\\venv``, ``/opt/clawmetry-fleet``). There
    an unattended update can only fail, and on Windows each attempt costs the
    user's collector minutes of downtime. A non-isolated interpreter is not
    blocked: pip falls back to a per-user install.
    """
    parent = package_parent or _package_parent()
    isolated = _isolated_env() if isolated is None else isolated
    writable = _dir_writable(parent)
    return {"blocked": bool(isolated and not writable), "path": str(parent),
            "isolated_env": bool(isolated), "writable": writable}


def auto_update_status() -> dict:
    """What the collector's automatic updates will do on this install, in
    words an administrator can act on."""
    try:
        blocked = self_update_blocked()
    except Exception as exc:  # never crash status on a probe
        blocked = {"blocked": False, "error": f"{exc.__class__.__name__}: {exc}"[:200]}
    if blocked.get("blocked"):
        return {"state": "off", "basis": "install_not_writable",
                "path": blocked.get("path"), "probe": blocked,
                "reason": (f"this user cannot write {blocked.get('path')}; update the "
                           "fleet by re-running the install recipe with a new pin")}
    try:
        from routes.update_check import _env_auto_update_disabled
        env_off = _env_auto_update_disabled()
    except Exception:
        env_off = os.environ.get("CLAWMETRY_AUTO_UPDATE", "").strip().lower() in (
            "0", "false", "no", "off")
    if env_off:
        return {"state": "off", "basis": "env", "probe": blocked,
                "reason": "CLAWMETRY_AUTO_UPDATE=0 or a CI environment"}
    return {"state": "on", "basis": "default", "probe": blocked,
            "reason": "new releases install automatically unless CLAWMETRY_AUTO_UPDATE=0 "
                      "or automatic updates are turned off in settings"}


# ── Linux: logind linger ──────────────────────────────────────────────────────


def _run(cmd: list, timeout: int = 10):
    return subprocess.run(cmd, capture_output=True, text=True,
                          check=False, timeout=timeout)


def linger_state(user: str | None = None) -> dict:
    """Is logind linger on for ``user``? States: enabled, disabled,
    unavailable (no loginctl, e.g. a container)."""
    user = user or getpass.getuser()
    import shutil
    if not shutil.which("loginctl"):
        return {"user": user, "state": "unavailable",
                "reason": "loginctl not found (no systemd-logind here)"}
    try:
        r = _run(["loginctl", "show-user", user, "--property=Linger", "--value"])
    except Exception as exc:  # timeout, OSError
        return {"user": user, "state": "unavailable",
                "reason": f"loginctl failed: {exc.__class__.__name__}"}
    value = (r.stdout or "").strip().lower()
    if r.returncode == 0 and value in ("yes", "no"):
        return {"user": user, "state": "enabled" if value == "yes" else "disabled"}
    # show-user fails for a user with no session and linger off.
    try:
        if Path("/var/lib/systemd/linger", user).exists():
            return {"user": user, "state": "enabled"}
    except OSError:
        pass
    return {"user": user, "state": "disabled"}


def enable_linger(user: str | None = None) -> dict:
    """Ask logind to keep ``user``'s services running after logout.

    Unprivileged users may enable their own linger when polkit allows it
    (the usual default for an active local session). When it is refused, the
    result carries the exact administrator command instead of failing
    silently.
    """
    user = user or getpass.getuser()
    before = linger_state(user)
    if before["state"] in ("enabled", "unavailable"):
        return before
    admin_cmd = f"sudo loginctl enable-linger {user}"
    try:
        # --no-ask-password: a polkit prompt on a TTY would otherwise sit
        # until the timeout instead of refusing.
        r = _run(["loginctl", "enable-linger", "--no-ask-password", user], timeout=15)
    except Exception as exc:
        return {"user": user, "state": "denied", "admin_command": admin_cmd,
                "reason": f"loginctl failed: {exc.__class__.__name__}"}
    after = linger_state(user)
    if r.returncode == 0 and after["state"] == "enabled":
        return after
    reason = ((r.stderr or r.stdout or "").strip().splitlines() or ["refused"])[0]
    return {"user": user, "state": "denied", "admin_command": admin_cmd,
            "reason": reason[:200]}


# ── Windows: all-users logon task ─────────────────────────────────────────────


def build_all_users_task_xml(python: str) -> str:
    """Task definition: any user logon, BUILTIN\\Users principal, least
    privilege, one instance per user session, restart on failure."""
    from xml.sax.saxutils import escape

    return f"""<?xml version="1.0" encoding="UTF-16"?>
<Task version="1.2" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">
  <RegistrationInfo>
    <Description>ClawMetry collector: runs as each signed-in user and reads only that user's profile.</Description>
  </RegistrationInfo>
  <Triggers>
    <LogonTrigger>
      <Enabled>true</Enabled>
    </LogonTrigger>
  </Triggers>
  <Principals>
    <Principal id="Author">
      <GroupId>{_USERS_GROUP_SID}</GroupId>
      <RunLevel>LeastPrivilege</RunLevel>
    </Principal>
  </Principals>
  <Settings>
    <MultipleInstancesPolicy>Parallel</MultipleInstancesPolicy>
    <DisallowStartIfOnBatteries>false</DisallowStartIfOnBatteries>
    <StopIfGoingOnBatteries>false</StopIfGoingOnBatteries>
    <StartWhenAvailable>true</StartWhenAvailable>
    <RestartOnFailure>
      <Interval>PT1M</Interval>
      <Count>999</Count>
    </RestartOnFailure>
    <ExecutionTimeLimit>PT0S</ExecutionTimeLimit>
  </Settings>
  <Actions Context="Author">
    <Exec>
      <Command>{escape(python)}</Command>
      <Arguments>-m clawmetry.sync</Arguments>
    </Exec>
  </Actions>
</Task>"""


def register_windows_all_users_task(python: str | None = None) -> dict:
    """Register the machine-wide per-user logon task. Needs an elevated
    (administrator) process; reports ``needs_admin`` otherwise."""
    import tempfile

    python = python or sys.executable
    xml = build_all_users_task_xml(python)
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".xml", delete=False, encoding="utf-16"
        ) as fh:
            fh.write(xml)
            xml_path = fh.name
    except OSError as exc:
        return {"state": "failed", "reason": f"temp file: {exc}"}
    try:
        r = _run(["schtasks", "/create", "/tn", WINDOWS_ALL_USERS_TASK_NAME,
                  "/xml", xml_path, "/f"], timeout=20)
    except Exception as exc:
        return {"state": "failed", "reason": f"schtasks: {exc.__class__.__name__}"}
    finally:
        try:
            os.remove(xml_path)
        except OSError:
            pass
    if r.returncode == 0:
        return {"state": "registered", "task": WINDOWS_ALL_USERS_TASK_NAME}
    msg = ((r.stderr or r.stdout or "").strip().splitlines() or ["refused"])[0]
    if "denied" in msg.lower():
        return {"state": "needs_admin", "task": WINDOWS_ALL_USERS_TASK_NAME,
                "reason": "run from an elevated (administrator) prompt"}
    return {"state": "failed", "task": WINDOWS_ALL_USERS_TASK_NAME,
            "reason": msg[:200]}


def windows_task_exists(name: str) -> bool:
    try:
        return _run(["schtasks", "/query", "/tn", name]).returncode == 0
    except Exception:
        return False


def remove_windows_task(name: str) -> bool:
    """Delete a task; True when it is gone afterwards (absent counts)."""
    if not windows_task_exists(name):
        return True
    try:
        _run(["schtasks", "/delete", "/tn", name, "/f"], timeout=20)
    except Exception:
        pass
    return not windows_task_exists(name)


# ── status / install / uninstall ──────────────────────────────────────────────


def fleet_status(system: str | None = None) -> dict:
    """Capability report: does collection continue after logoff, and is the
    data private to this user? Every ``False`` carries a reason."""
    import platform

    system = system or platform.system()
    out: dict = {"os": system, "user": getpass.getuser(),
                 "collector": "per_user", "data_dir": data_dir_private(),
                 "auto_update": auto_update_status()}
    if system == "Linux":
        unit = Path.home() / ".config" / "systemd" / "user" / "clawmetry-sync.service"
        root = hasattr(os, "geteuid") and os.geteuid() == 0
        if root and Path("/etc/systemd/system/clawmetry-sync.service").exists():
            out.update(supervisor="systemd_system", survives_logoff=True,
                       reason="system unit is not tied to a login session")
            return out
        linger = linger_state()
        out["linger"] = linger
        out["supervisor"] = "systemd_user" if unit.exists() else "none"
        if not unit.exists():
            out.update(survives_logoff=False,
                       reason="no systemd user unit registered; run `clawmetry service install`")
        elif linger["state"] == "enabled":
            out.update(survives_logoff=True,
                       reason="linger is enabled, so the user manager outlives logout")
        else:
            out.update(survives_logoff=False,
                       reason="linger is off: logout stops the user unit; "
                              f"enable with `sudo loginctl enable-linger {linger['user']}`")
    elif system == "Windows":
        from clawmetry.daemon_registration import WINDOWS_TASK_NAME

        all_users = windows_task_exists(WINDOWS_ALL_USERS_TASK_NAME)
        per_user = windows_task_exists(WINDOWS_TASK_NAME)
        out["all_users_task"] = all_users
        out["per_user_task"] = per_user
        out["supervisor"] = ("task_all_users" if all_users
                             else "task_per_user" if per_user else "none")
        out.update(survives_logoff=False,
                   reason="Windows collectors run inside the user's session and stop at "
                          "logoff; data on disk is resumed at the next logon")
    elif system == "Darwin":
        plist = Path.home() / "Library" / "LaunchAgents" / "com.clawmetry.sync.plist"
        out["supervisor"] = "launchd" if plist.exists() else "none"
        out.update(survives_logoff=False,
                   reason="a LaunchAgent runs in the user's login session")
    else:
        out.update(supervisor="none", survives_logoff=False,
                   reason=f"no fleet registration for {system}")
    return out


def install(all_users: bool = False, system: str | None = None) -> dict:
    """Register the collector for fleet use on this OS. Returns a result dict
    with ``ok`` plus per-step states; never raises."""
    import platform

    system = system or platform.system()
    result: dict = {"os": system, "steps": {}}
    if system == "Windows":
        if all_users:
            step = register_windows_all_users_task()
            result["steps"]["all_users_task"] = step
            result["ok"] = step["state"] == "registered"
        else:
            from clawmetry.daemon_registration import register_windows_task
            ok = register_windows_task({})
            result["steps"]["per_user_task"] = {"state": "registered" if ok else "failed"}
            result["ok"] = ok
        return result
    if all_users:
        result["ok"] = False
        result["steps"]["all_users"] = {
            "state": "unsupported",
            "reason": "--all-users is Windows only; on Linux run `clawmetry service install` "
                      "as each user (see deploy/fleet/ansible)"}
        return result
    result["steps"]["data_dir"] = restrict_data_dir()
    if system == "Linux":
        from clawmetry.daemon_registration import register_systemd
        root = hasattr(os, "geteuid") and os.geteuid() == 0
        # Linger FIRST: for a user with no running user manager (installed
        # over sudo / ssh without a session) linger is what starts the
        # manager the unit is registered with.
        if root:
            linger = {"state": "not_needed", "reason": "root installs a system unit"}
        else:
            linger = enable_linger()
        result["steps"]["linger"] = linger
        unit_ok = register_systemd({})
        result["steps"]["systemd_user_unit"] = {"state": "active" if unit_ok else "failed"}
        result["ok"] = unit_ok and (root or linger["state"] == "enabled")
        return result
    if system == "Darwin":
        from clawmetry.daemon_registration import register_launchd
        ok = register_launchd({})
        result["steps"]["launchd"] = {"state": "registered" if ok else "failed"}
        result["ok"] = ok
        return result
    result["ok"] = False
    result["steps"]["supervisor"] = {"state": "unsupported"}
    return result


def uninstall(system: str | None = None) -> dict:
    """Remove the registrations ``install`` creates. Linger is left as is:
    it is a per-user logind setting other software may rely on, so we report
    the command instead of silently changing it."""
    import platform

    system = system or platform.system()
    removed: list = []
    remaining: list = []
    if system == "Windows":
        from clawmetry.daemon_registration import WINDOWS_TASK_NAME
        for name in (WINDOWS_ALL_USERS_TASK_NAME, WINDOWS_TASK_NAME):
            existed = windows_task_exists(name)
            if remove_windows_task(name):
                if existed:
                    removed.append(f"scheduled task {name}")
            else:
                remaining.append(f"scheduled task {name} (needs an elevated prompt)")
    elif system == "Linux":
        unit = Path.home() / ".config" / "systemd" / "user" / "clawmetry-sync.service"
        if unit.exists():
            try:
                _run(["systemctl", "--user", "disable", "--now", "clawmetry-sync"], timeout=15)
            except Exception:
                pass
            try:
                unit.unlink()
                removed.append(f"systemd user unit {unit}")
                _run(["systemctl", "--user", "daemon-reload"], timeout=15)
            except Exception:
                remaining.append(f"systemd user unit {unit}")
    elif system == "Darwin":
        plist = Path.home() / "Library" / "LaunchAgents" / "com.clawmetry.sync.plist"
        if plist.exists():
            try:
                _run(["launchctl", "bootout", f"gui/{os.getuid()}", str(plist)], timeout=10)
            except Exception:
                pass
            try:
                plist.unlink()
                removed.append(f"launchd agent {plist}")
            except OSError:
                remaining.append(f"launchd agent {plist}")
    out = {"os": system, "removed": removed, "remaining": remaining,
           "ok": not remaining}
    if system == "Linux":
        out["note"] = (f"linger left unchanged; disable with "
                       f"`sudo loginctl disable-linger {getpass.getuser()}`")
    return out
