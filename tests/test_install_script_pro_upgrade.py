"""install.sh must upgrade clawmetry-pro too, not just the core (2026-08-28).

The core wheel and the closed-source ``clawmetry-pro`` wheel (the paid runtime
adapters) ship on separate cadences. The installer only ever upgraded the core,
and its "already up to date" early exit returned without looking at pro at all
-- so an entitled node sitting on a stale pro wheel could re-run
``curl … | bash`` forever and never be brought current.

install.sh now calls ``clawmetry.license.auto_provision_pro()`` (the same
entitlement-gated, idempotent, never-raises helper the sync daemon uses) on
both paths, and restarts the daemons when the wheel on disk actually moved.

The tests source the helper block out of install.sh (between the
``CM_PRO_SYNC_BLOCK_START`` / ``END`` sentinels) and drive it against a stub
``clawmetry.license`` module, so they exercise the real shell + Python the
installer runs -- not a paraphrase of it.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
INSTALL_SH = REPO_ROOT / "install.sh"

posix_only = pytest.mark.skipif(
    os.name != "posix", reason="install.sh is the macOS/Linux installer"
)


def _install_sh() -> str:
    assert INSTALL_SH.exists(), f"install.sh missing at {INSTALL_SH}"
    return INSTALL_SH.read_text()


def _helper_block() -> str:
    body = _install_sh()
    start = body.index("# >>> CM_PRO_SYNC_BLOCK_START")
    end = body.index("# <<< CM_PRO_SYNC_BLOCK_END")
    return body[start:end]


def _write_stub_license(root: Path, *, before: str, after: str, ok: bool, msg: str) -> None:
    """A fake ``clawmetry.license`` whose provision step moves the installed
    version from ``before`` to ``after`` (same value = "already current")."""
    pkg = root / "clawmetry"
    pkg.mkdir(parents=True, exist_ok=True)
    (pkg / "__init__.py").write_text("")
    (pkg / "license.py").write_text(
        textwrap.dedent(
            f"""
            _BEFORE = {before!r}
            _AFTER = {after!r}
            _OK = {bool(ok)!r}
            _MSG = {msg!r}
            _state = {{"v": _BEFORE}}

            def ensure_pro_on_path():
                pass

            def _pro_installed_version():
                return _state["v"] or None

            def auto_provision_pro(api_key, node_id=None):
                assert api_key.startswith("cm_"), api_key
                _state["v"] = _AFTER
                return _OK, _MSG
            """
        ).lstrip()
    )


def _run_sync_pro(tmp_path: Path, *, config: dict | None, stub: dict | None) -> dict:
    """Run ``_cm_sync_pro`` from the extracted block. Returns
    {stdout, CM_PRO_STATE, CM_PRO_CHANGED, ...}."""
    home = tmp_path / "home"
    (home / ".clawmetry").mkdir(parents=True, exist_ok=True)
    if config is not None:
        (home / ".clawmetry" / "config.json").write_text(json.dumps(config))
    site = tmp_path / "site"
    site.mkdir(exist_ok=True)
    if stub is not None:
        _write_stub_license(site, **stub)

    script = _helper_block() + textwrap.dedent(
        f"""
        INSTALL_DIR="{home}/.clawmetry"
        OS="Darwin"
        _cm_sync_pro "{sys.executable}"
        echo "RESULT state=$CM_PRO_STATE changed=$CM_PRO_CHANGED from=$CM_PRO_FROM to=$CM_PRO_TO"
        """
    )
    env = dict(os.environ)
    env["HOME"] = str(home)
    env["PYTHONPATH"] = str(site)
    env.pop("CLAWMETRY_API_KEY", None)
    proc = subprocess.run(
        ["bash", "-c", script], capture_output=True, text=True, timeout=60, env=env,
        cwd=str(tmp_path), check=False,
    )
    assert proc.returncode == 0, proc.stderr
    result = {"stdout": proc.stdout}
    for line in proc.stdout.splitlines():
        if line.startswith("RESULT "):
            for pair in line[len("RESULT "):].split():
                k, _, v = pair.partition("=")
                result[k] = v
    return result


# ── The wiring: both installer paths must call the helper ───────────────────

def test_early_exit_path_syncs_pro():
    """The "already up to date" exit must reconcile pro before returning --
    that path is exactly where a user re-runs the installer to get current."""
    body = _install_sh()
    head = body[body.index("# ── Early exit: already up to date"):]
    head = head[: head.index("# ── Install into venv")]
    assert "_cm_sync_pro" in head, (
        "install.sh's early exit returns without checking clawmetry-pro; an "
        "entitled node with a stale pro wheel can never be repaired by "
        "re-running the installer."
    )
    assert "_cm_kick_daemons" in head, (
        "a pro wheel installed under a running daemon is not imported until "
        "the daemon restarts"
    )


def test_pro_sync_runs_before_the_daemon_restarts():
    """Order matters: pro must land BEFORE launchd/systemd restart the
    daemons, or they come back on the old adapters."""
    body = _install_sh()
    main_call = body.rindex("_cm_sync_pro ")
    launchd = body.index("# ── Restart launchd jobs (macOS)")
    assert main_call < launchd, (
        "install.sh refreshes clawmetry-pro after restarting the daemons; "
        "they would import the old adapters"
    )


# ── The helper itself ───────────────────────────────────────────────────────

@posix_only
def test_free_account_installs_nothing_and_says_nothing(tmp_path):
    """No cloud key on disk -> no probe, no output, no failure."""
    out = _run_sync_pro(tmp_path, config={"node_id": "box"}, stub=None)
    assert out["state"] == "none"
    assert out["changed"] == "0"
    assert "clawmetry-pro" not in out["stdout"]


@posix_only
def test_self_hosted_license_key_is_not_treated_as_a_cloud_key(tmp_path):
    """A signed license (CLAW1.…) provisions the wheel through `clawmetry
    license activate`, not here -- and must not be sent to the cloud probe."""
    out = _run_sync_pro(
        tmp_path, config={"api_key": "CLAW1.abc", "node_id": "box"}, stub=None
    )
    assert out["state"] == "none"


@posix_only
def test_entitled_node_upgrades_a_stale_pro_wheel(tmp_path):
    out = _run_sync_pro(
        tmp_path,
        config={"api_key": "cm_live_x", "node_id": "box"},
        stub={"before": "0.7.15", "after": "0.7.16", "ok": True, "msg": "installed"},
    )
    assert out["state"] == "updated"
    assert out["changed"] == "1", "a moved wheel must signal that a restart is owed"
    assert out["from"] == "0.7.15" and out["to"] == "0.7.16"
    assert "0.7.15" in out["stdout"] and "0.7.16" in out["stdout"]


@posix_only
def test_entitled_node_already_current_is_quiet_and_restarts_nothing(tmp_path):
    out = _run_sync_pro(
        tmp_path,
        config={"api_key": "cm_live_x", "node_id": "box"},
        stub={"before": "0.7.16", "after": "0.7.16", "ok": True, "msg": "already"},
    )
    assert out["state"] == "current"
    assert out["changed"] == "0", "no wheel change must not trigger a daemon restart"
    assert "0.7.16" in out["stdout"]


@posix_only
def test_first_install_of_pro_reports_an_install_not_an_upgrade(tmp_path):
    out = _run_sync_pro(
        tmp_path,
        config={"api_key": "cm_live_x", "node_id": "box"},
        stub={"before": "", "after": "0.7.16", "ok": True, "msg": "installed"},
    )
    assert out["state"] == "updated"
    assert out["changed"] == "1"
    assert "installed" in out["stdout"]


@posix_only
def test_unreachable_license_server_keeps_the_installed_wheel(tmp_path):
    """auto_provision_pro returns (False, …) for a free account AND for a
    failed probe. With pro already on disk we must neither claim it is current
    nor pretend it was removed."""
    out = _run_sync_pro(
        tmp_path,
        config={"api_key": "cm_live_x", "node_id": "box"},
        stub={"before": "0.7.15", "after": "0.7.15", "ok": False, "msg": ""},
    )
    assert out["state"] == "kept"
    assert out["changed"] == "0"
    assert "0.7.15" in out["stdout"]


@posix_only
def test_broken_license_module_never_fails_the_install(tmp_path):
    """A CLI too old to expose the helper (or any import error) degrades to a
    silent no-op -- the installer must still exit 0."""
    site = tmp_path / "site"
    site.mkdir()
    pkg = site / "clawmetry"
    pkg.mkdir()
    (pkg / "__init__.py").write_text("")
    (pkg / "license.py").write_text("raise RuntimeError('boom')\n")
    out = _run_sync_pro(
        tmp_path, config={"api_key": "cm_live_x", "node_id": "box"}, stub=None
    )
    assert out["state"] in ("none", "")
    assert out["changed"] == "0"
