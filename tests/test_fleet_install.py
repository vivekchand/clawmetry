"""Fleet install on shared and virtual desktops (#5942).

Factory requirement: Fleet Install on Shared and Virtual Desktops
(d673cdaa-3bdb-4b10-8a2d-d40ccb5ae630). The collector is per user, running as
that user; these tests pin the three things that design depends on.

* AC-OBS-FLEET-001.1 -- Linux fleet registration requests linger and, when
  refused, reports the exact administrator command: ``test_enable_linger_denied_reports_admin_command``.
* AC-OBS-FLEET-001.2 -- the Windows all-users task starts a collector as each
  signed-in user and never under a privileged account: ``test_all_users_task_runs_as_each_user_not_system``.
* AC-OBS-FLEET-001.3 -- unregister removes every task it created: ``test_uninstall_windows_removes_both_tasks``.
* AC-OBS-FLEET-001.4 -- a collector in an administrator-owned environment never
  attempts an unattended self-update, and status says why:
  ``test_auto_update_never_attempted_from_unwritable_fleet_install``,
  ``test_self_update_blocked_only_for_unwritable_isolated_env``,
  ``test_status_reports_auto_update_off_for_unwritable_install``.
* AC-OBS-FLEET-002.1 -- status says whether collection survives logoff, with a
  reason: ``test_status_linux_without_linger_does_not_survive_logoff``.
* AC-OBS-FLEET-002.2 -- a data dir readable by other users is reported and
  fleet registration restricts it: ``test_restrict_data_dir_removes_group_and_other_bits``.
* AC-OBS-FLEET-003.1 -- each recipe is exercised on its own OS in CI: ``test_recipes_are_exercised_on_their_os_in_ci``.
* AC-OBS-FLEET-003.2 -- the recipes embed no enrollment credential: ``test_recipes_embed_no_credential``.
"""
from __future__ import annotations

import os
import re
import stat
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import clawmetry.fleet_install as fi

REPO = Path(__file__).resolve().parent.parent
NS = {"t": "http://schemas.microsoft.com/windows/2004/02/mit/task"}


class _Res:
    def __init__(self, rc=0, stdout="", stderr=""):
        self.returncode = rc
        self.stdout = stdout
        self.stderr = stderr


# ── Windows all-users task ────────────────────────────────────────────────────


def _task(python=r"C:\Program Files\ClawMetry\venv\Scripts\python.exe"):
    xml = fi.build_all_users_task_xml(python)
    # The declared UTF-16 encoding is for schtasks; ElementTree wants bytes
    # without a conflicting declaration.
    body = xml.split("?>", 1)[1]
    return ET.fromstring(body)


def test_all_users_task_runs_as_each_user_not_system():
    root = _task()
    principals = root.findall("t:Principals/t:Principal", NS)
    assert len(principals) == 1
    p = principals[0]
    # BUILTIN\Users by SID: every signed-in user, each under their own token.
    assert p.findtext("t:GroupId", namespaces=NS) == "S-1-5-32-545"
    assert p.findtext("t:RunLevel", namespaces=NS) == "LeastPrivilege"
    # Never a service account: no UserId (SYSTEM is S-1-5-18) and no
    # HighestAvailable elevation.
    assert p.find("t:UserId", NS) is None
    assert "S-1-5-18" not in fi.build_all_users_task_xml("python")
    assert "HighestAvailable" not in fi.build_all_users_task_xml("python")


def test_all_users_task_starts_one_instance_per_user_at_any_logon():
    root = _task()
    trig = root.find("t:Triggers/t:LogonTrigger", NS)
    assert trig is not None
    # No UserId on the trigger: fires for ANY user's logon, not one account.
    assert trig.find("t:UserId", NS) is None
    # IgnoreNew would drop the second user's logon while the first runs.
    assert root.findtext("t:Settings/t:MultipleInstancesPolicy", namespaces=NS) == "Parallel"
    assert root.find("t:Settings/t:RestartOnFailure", NS) is not None
    assert root.findtext("t:Actions/t:Exec/t:Arguments", namespaces=NS) == "-m clawmetry.sync"


def test_all_users_task_escapes_interpreter_path():
    xml = fi.build_all_users_task_xml(r"C:\A&B\python.exe")
    assert "A&amp;B" in xml
    _task(r"C:\A&B\python.exe")  # still parses


def test_register_all_users_task_reports_needs_admin(monkeypatch):
    monkeypatch.setattr(fi, "_run", lambda cmd, timeout=10: _Res(1, "", "ERROR: Access is denied."))
    out = fi.register_windows_all_users_task("python")
    assert out["state"] == "needs_admin"
    assert "elevated" in out["reason"]


def test_uninstall_windows_removes_both_tasks(monkeypatch):
    from clawmetry.daemon_registration import WINDOWS_TASK_NAME

    present = {fi.WINDOWS_ALL_USERS_TASK_NAME, WINDOWS_TASK_NAME}
    deleted = []

    def _run(cmd, timeout=10):
        name = cmd[cmd.index("/tn") + 1]
        if "/query" in cmd:
            return _Res(0 if name in present else 1)
        if "/delete" in cmd:
            deleted.append(name)
            present.discard(name)
            return _Res(0)
        return _Res(1)

    monkeypatch.setattr(fi, "_run", _run)
    out = fi.uninstall(system="Windows")
    assert set(deleted) == {fi.WINDOWS_ALL_USERS_TASK_NAME, WINDOWS_TASK_NAME}
    assert out["ok"] is True and not out["remaining"]
    assert len(out["removed"]) == 2


def test_uninstall_windows_reports_task_it_could_not_remove(monkeypatch):
    def _run(cmd, timeout=10):
        return _Res(0) if "/query" in cmd else _Res(1, "", "Access is denied.")

    monkeypatch.setattr(fi, "_run", _run)
    out = fi.uninstall(system="Windows")
    assert out["ok"] is False
    assert any("elevated" in r for r in out["remaining"])


def test_install_all_users_is_windows_only():
    out = fi.install(all_users=True, system="Linux")
    assert out["ok"] is False
    assert out["steps"]["all_users"]["state"] == "unsupported"


def test_windows_status_never_claims_to_survive_logoff(monkeypatch):
    monkeypatch.setattr(fi, "windows_task_exists", lambda name: True)
    out = fi.fleet_status(system="Windows")
    assert out["supervisor"] == "task_all_users"
    assert out["survives_logoff"] is False
    assert "logoff" in out["reason"]


# ── Linux linger ──────────────────────────────────────────────────────────────


def test_enable_linger_denied_reports_admin_command(monkeypatch):
    monkeypatch.setattr("shutil.which", lambda name: "/usr/bin/" + name)

    def _run(cmd, timeout=10):
        if cmd[:2] == ["loginctl", "show-user"]:
            return _Res(0, "no\n")
        if cmd[:2] == ["loginctl", "enable-linger"]:
            return _Res(1, "", "Could not enable linger: Access denied\n")
        return _Res(1)

    monkeypatch.setattr(fi, "_run", _run)
    out = fi.enable_linger("alice")
    assert out["state"] == "denied"
    assert out["admin_command"] == "sudo loginctl enable-linger alice"
    assert "Access denied" in out["reason"]


def test_enable_linger_success_is_verified_not_assumed(monkeypatch):
    monkeypatch.setattr("shutil.which", lambda name: "/usr/bin/" + name)
    state = {"linger": "no"}

    def _run(cmd, timeout=10):
        if cmd[:2] == ["loginctl", "show-user"]:
            return _Res(0, state["linger"] + "\n")
        if cmd[:2] == ["loginctl", "enable-linger"]:
            state["linger"] = "yes"
            return _Res(0)
        return _Res(1)

    monkeypatch.setattr(fi, "_run", _run)
    assert fi.enable_linger("alice")["state"] == "enabled"

    # rc 0 but logind still says "no" (e.g. a policy override): not enabled.
    state["linger"] = "no"
    monkeypatch.setattr(fi, "_run", lambda cmd, timeout=10: _Res(0, "no\n"))
    assert fi.enable_linger("alice")["state"] == "denied"


def test_linger_unavailable_without_loginctl(monkeypatch):
    monkeypatch.setattr("shutil.which", lambda name: None)
    assert fi.linger_state("alice")["state"] == "unavailable"
    assert fi.enable_linger("alice")["state"] == "unavailable"


def test_status_linux_without_linger_does_not_survive_logoff(monkeypatch, tmp_path):
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: tmp_path))
    if hasattr(os, "geteuid"):
        monkeypatch.setattr(os, "geteuid", lambda: 1000)
    unit = tmp_path / ".config" / "systemd" / "user" / "clawmetry-sync.service"
    unit.parent.mkdir(parents=True)
    unit.write_text("[Service]\n")

    monkeypatch.setattr(fi, "linger_state", lambda user=None: {"user": "alice", "state": "disabled"})
    out = fi.fleet_status(system="Linux")
    assert out["supervisor"] == "systemd_user"
    assert out["survives_logoff"] is False
    assert "sudo loginctl enable-linger alice" in out["reason"]

    monkeypatch.setattr(fi, "linger_state", lambda user=None: {"user": "alice", "state": "enabled"})
    assert fi.fleet_status(system="Linux")["survives_logoff"] is True


def test_status_linux_without_unit_says_so(monkeypatch, tmp_path):
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: tmp_path))
    if hasattr(os, "geteuid"):
        monkeypatch.setattr(os, "geteuid", lambda: 1000)
    monkeypatch.setattr(fi, "linger_state", lambda user=None: {"user": "alice", "state": "enabled"})
    out = fi.fleet_status(system="Linux")
    assert out["survives_logoff"] is False
    assert "clawmetry service install" in out["reason"]


def test_install_linux_fails_when_linger_refused(monkeypatch, tmp_path):
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: tmp_path))
    if hasattr(os, "geteuid"):
        monkeypatch.setattr(os, "geteuid", lambda: 1000)
    import clawmetry.daemon_registration as dreg

    order = []
    monkeypatch.setattr(dreg, "register_systemd", lambda cfg: order.append("unit") or True)

    def _linger(user=None):
        order.append("linger")
        return {"user": "alice", "state": "denied",
                "admin_command": "sudo loginctl enable-linger alice"}

    monkeypatch.setattr(fi, "enable_linger", _linger)
    out = fi.install(system="Linux")
    # A unit that stops at logout is not a fleet install: report failure.
    assert out["ok"] is False
    assert out["steps"]["systemd_user_unit"]["state"] == "active"
    assert out["steps"]["linger"]["admin_command"].endswith("alice")
    # Linger first: it is what starts a user manager for a user with no session.
    assert order == ["linger", "unit"]


def test_enable_linger_never_waits_on_a_password_prompt(monkeypatch):
    monkeypatch.setattr("shutil.which", lambda name: "/usr/bin/" + name)
    seen = []

    def _run(cmd, timeout=10):
        if cmd[:2] == ["loginctl", "enable-linger"]:
            seen.append(cmd)
            return _Res(1, "", "Access denied")
        return _Res(0, "no\n")

    monkeypatch.setattr(fi, "_run", _run)
    fi.enable_linger("alice")
    assert seen and "--no-ask-password" in seen[0]


# ── self-update from an administrator-owned install ───────────────────────────


def _update_check_as_user_machine(monkeypatch):
    import importlib
    import routes.update_check as uc

    uc = importlib.reload(uc)
    monkeypatch.delenv("CLAWMETRY_AUTO_UPDATE", raising=False)
    monkeypatch.delenv("CI", raising=False)
    uc._process_role = "daemon"
    monkeypatch.setattr(uc, "_running_from_source_checkout", lambda: False)
    monkeypatch.setattr(uc, "_get_update_check_config", lambda: {"auto_update": True})
    monkeypatch.setattr(uc, "_daemon_supervised", lambda: False)
    # The Windows plan, where the harm was: exit, pip x3, relaunch, repeat.
    monkeypatch.setattr(uc, "_restart_plan", lambda r, p, s: "respawn")
    monkeypatch.setattr(uc, "_record_update_attempt", lambda *a, **k: None)
    monkeypatch.setattr(uc, "_acquire_update_lock", lambda: True)
    monkeypatch.setattr(uc, "_release_update_lock", lambda: None)
    actions = []
    monkeypatch.setattr(uc, "_schedule_windows_respawn", lambda: actions.append("respawn"))
    monkeypatch.setattr(uc, "_schedule_exec_restart", lambda *a, **k: actions.append("exec"))
    import routes.meta as meta
    monkeypatch.setattr(meta, "perform_self_update",
                        lambda **kw: actions.append("pip") or ({"ok": True}, 200))
    return uc, actions


def test_auto_update_never_attempted_from_unwritable_fleet_install(monkeypatch):
    uc, actions = _update_check_as_user_machine(monkeypatch)
    probes = []
    monkeypatch.setattr(fi, "self_update_blocked", lambda: probes.append(1) or {
        "blocked": True, "path": r"C:\Program Files\ClawMetry\venv\Lib\site-packages",
        "isolated_env": True, "writable": False})
    for _ in range(3):
        uc._maybe_auto_update("0.12.1", "0.12.2")
    assert actions == [], "an unwritable fleet install must not exit, pip or respawn"
    assert uc._auto_update_in_progress is False
    assert len(probes) == 1, "ownership is probed once per process, not every check"

    # Control: the same harness on a writable install does reach the respawn,
    # so the assertion above is not passing for an unrelated reason.
    uc, actions = _update_check_as_user_machine(monkeypatch)
    monkeypatch.setattr(fi, "self_update_blocked", lambda: {"blocked": False})
    uc._maybe_auto_update("0.12.1", "0.12.2")
    assert actions == ["respawn"]


@pytest.mark.skipif(os.name == "nt" or (hasattr(os, "geteuid") and os.geteuid() == 0),
                    reason="POSIX permission bits; root ignores them")
def test_self_update_blocked_only_for_unwritable_isolated_env(tmp_path):
    site = tmp_path / "site-packages"
    site.mkdir()
    assert fi.self_update_blocked(site, isolated=True)["blocked"] is False
    os.chmod(site, stat.S_IRUSR | stat.S_IXUSR)
    try:
        r = fi.self_update_blocked(site, isolated=True)
        assert r["blocked"] is True and r["writable"] is False
        # Outside a venv pip falls back to a per-user install: not blocked.
        assert fi.self_update_blocked(site, isolated=False)["blocked"] is False
        assert not list(site.iterdir()), "the probe must leave nothing behind"
    finally:
        os.chmod(site, stat.S_IRWXU)


def test_write_probe_is_one_attempt_never_a_mkstemp_retry_loop(monkeypatch, tmp_path):
    """AC-OBS-FLEET-001.4: on Windows ``tempfile.mkstemp`` keeps retrying a
    denied create (up to ``TMP_MAX`` names) while ``os.access`` (ACL-blind)
    says the directory is writable. That hung the CI runner for 24 minutes under a deny ACE; the
    collector's probe must make exactly one attempt."""
    import tempfile

    def _no_mkstemp(*a, **k):
        raise AssertionError("the write probe must not use tempfile.mkstemp")

    monkeypatch.setattr(tempfile, "mkstemp", _no_mkstemp)
    calls = []
    real_open = os.open

    def _denied(path, flags, mode=0o777):
        calls.append(path)
        raise PermissionError(13, "Access is denied", path)

    monkeypatch.setattr(os, "open", _denied)
    assert fi._dir_writable(tmp_path) is False
    assert len(calls) == 1, calls

    monkeypatch.setattr(os, "open", real_open)
    assert fi._dir_writable(tmp_path) is True
    assert not list(tmp_path.iterdir()), "the probe must leave nothing behind"


def test_status_reports_auto_update_off_for_unwritable_install(monkeypatch, tmp_path):
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: tmp_path))
    monkeypatch.setattr(fi, "self_update_blocked", lambda: {
        "blocked": True, "path": "/opt/clawmetry-fleet/lib/site-packages"})
    au = fi.fleet_status(system="Darwin")["auto_update"]
    assert au["state"] == "off" and au["basis"] == "install_not_writable"
    assert "/opt/clawmetry-fleet" in au["reason"] and "re-running" in au["reason"]

    monkeypatch.setattr(fi, "self_update_blocked", lambda: {"blocked": False})
    monkeypatch.setenv("CLAWMETRY_AUTO_UPDATE", "0")
    assert fi.auto_update_status()["basis"] == "env"


def test_windows_data_dir_privacy_is_not_claimed_unchecked(monkeypatch, tmp_path):
    import types

    monkeypatch.setattr(fi, "os", types.SimpleNamespace(name="nt"))
    out = fi.data_dir_private(tmp_path)
    assert out["private"] is None
    assert out["basis"] == "windows_profile_acl_not_checked"


# ── data-directory privacy ────────────────────────────────────────────────────


def _dir_other_users_can_read(path):
    """A data dir as it arises in the field: a plain mkdir under the common
    022 umask (the daemon's import-time mkdir), which leaves it readable by
    every local user. No permissive chmod literal needed."""
    old = os.umask(0o022)
    try:
        path.mkdir()
    finally:
        os.umask(old)
    assert stat.S_IMODE(path.stat().st_mode) & 0o077, "fixture must be readable by others"
    return path


@pytest.mark.skipif(os.name == "nt", reason="POSIX permission bits")
def test_restrict_data_dir_removes_group_and_other_bits(tmp_path):
    d = _dir_other_users_can_read(tmp_path / ".clawmetry")
    before = fi.data_dir_private(d)
    assert before["private"] is False
    after = fi.restrict_data_dir(d)
    assert after["private"] is True
    assert stat.S_IMODE(d.stat().st_mode) == 0o700


@pytest.mark.skipif(os.name == "nt", reason="POSIX permission bits")
def test_restrict_data_dir_creates_private(tmp_path):
    d = tmp_path / "fresh" / ".clawmetry"
    old = os.umask(0o022)
    try:
        out = fi.restrict_data_dir(d)
    finally:
        os.umask(old)
    assert out["private"] is True
    assert stat.S_IMODE(d.stat().st_mode) & 0o077 == 0


@pytest.mark.skipif(os.name == "nt", reason="POSIX ownership")
def test_restrict_data_dir_leaves_another_users_dir_alone(tmp_path, monkeypatch):
    d = _dir_other_users_can_read(tmp_path / ".clawmetry")
    mode_before = stat.S_IMODE(d.stat().st_mode)
    monkeypatch.setattr(os, "geteuid", lambda: d.stat().st_uid + 1)
    out = fi.restrict_data_dir(d)
    assert out["basis"] == "owned_by_another_user"
    assert stat.S_IMODE(d.stat().st_mode) == mode_before


# ── recipes ───────────────────────────────────────────────────────────────────

RECIPES = [
    REPO / "deploy" / "fleet" / "intune" / "Install-ClawMetry.ps1",
    REPO / "deploy" / "fleet" / "ansible" / "clawmetry.yml",
]


@pytest.mark.parametrize("path", RECIPES, ids=lambda p: p.name)
def test_recipes_embed_no_credential(path):
    text = path.read_text(encoding="utf-8")
    # No literal account/enrollment key in the file (keys start cm_).
    assert not re.search(r"cm_[A-Za-z0-9]{8,}", text)
    # Every recipe must use the fleet registration this module provides.
    assert "service install" in text


def test_recipes_keep_the_shared_environment_unwritable_by_desktop_users():
    """AC-OBS-FLEET-001.4 / 001.2: every user's collector imports the one shared
    environment, so a desktop user able to write it could run code as every
    other user. The first real Ubuntu run found the Ansible venv at 0777."""
    playbook = RECIPES[1].read_text(encoding="utf-8")
    assert playbook.count("umask 022 &&") == 2, "venv creation and pip install"
    assert 'mode: "u=rwX,go=rX"' in playbook and "recurse: true" in playbook
    assert "follow: false" in playbook, "must not chmod through the venv's python symlink"
    intune = RECIPES[0].read_text(encoding="utf-8")
    assert "/inheritance:r" in intune and "*S-1-5-32-545:(OI)(CI)RX" in intune
    wf = (REPO / ".github" / "workflows" / "fleet-install-test.yml").read_text(encoding="utf-8")
    assert "-perm -o+w" in _job_block(wf, "linux-ansible")
    assert "Desktop users cannot write the shared environment" in _job_block(wf, "windows-intune")


def _job_block(workflow: str, job: str) -> str:
    start = workflow.index(f"\n  {job}:\n")
    nxt = re.search(r"\n  [a-z][a-z0-9-]*:\n", workflow[start + 1:])
    return workflow[start: start + 1 + nxt.start()] if nxt else workflow[start:]


def test_recipes_are_exercised_on_their_os_in_ci():
    wf = (REPO / ".github" / "workflows" / "fleet-install-test.yml").read_text(encoding="utf-8")
    linux = _job_block(wf, "linux-ansible")
    windows = _job_block(wf, "windows-intune")
    assert "runs-on: ubuntu-latest" in linux
    assert "ansible-playbook" in linux and "deploy/fleet/ansible/clawmetry.yml" in linux
    assert "runs-on: windows-latest" in windows
    assert r"deploy\fleet\intune\Install-ClawMetry.ps1" in windows
    # Proof, not just a run: both jobs assert what the recipe registered.
    assert "service status --json" in linux and "service status --json" in windows
    assert "S-1-5-32-545" in windows
