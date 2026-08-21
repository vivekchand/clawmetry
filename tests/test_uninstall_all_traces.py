"""Guards for the Windows installer/uninstaller trace hygiene.

Bugs pinned here (founder report 2026-08-10)
--------------------------------------------

A "fresh" desktop install landed straight on the signed-in dashboard with
zero login prompt, because three kinds of leftover state survived a broken
(Smart-App-Control-blocked) uninstall:

1. ``%LOCALAPPDATA%\\ClawMetry\\runtime\\onboarding-completed.json`` — its
   mere existence suppressed the auth pane.
2. ``~/.openclaw/openclaw.json`` → ``clawmetry.cloudToken`` — the FIRST
   source ``_read_cloud_token`` checks; no uninstall path touched OpenClaw's
   home, so the identity re-attached silently.
3. The shared pywebview WebView2 profile and the OS-keychain workspace-key
   entry — never removed by anything.

Founder directive (same day): uninstall removes EVERY file ClawMetry
created. We cannot run the NSIS uninstaller in this CI job, so these tests
assert the .nsi encodes the sweep (and the install-time fresh-install
defense), the same pattern as test_installer_stale_sweep.py.
"""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
NSI = REPO_ROOT / "desktop" / "installer" / "windows.nsi"


def _read() -> str:
    assert NSI.exists(), f"windows.nsi missing at {NSI}"
    return NSI.read_text(encoding="utf-8")


def test_nsi_is_pure_ascii() -> None:
    # makensis reads the BOM-less file in the system codepage and aborts
    # with "Bad text encoding" on any multi-byte char (burned 2026-08-09
    # and again 2026-08-10 on em-dashes in comments).
    raw = NSI.read_bytes()
    assert all(b < 0x80 for b in raw), "windows.nsi must stay pure ASCII"


def test_uninstall_removes_entire_appdata_tree() -> None:
    body = _read()
    assert 'RMDir /r "$LOCALAPPDATA\\ClawMetry"' in body, (
        "uninstall must remove the whole %LOCALAPPDATA%\\ClawMetry tree "
        "(runtime venv, onboarding stamp, bin shim, webview profile, legacy "
        "stray venv layouts), not just runtime/ and bin/"
    )


def test_uninstall_strips_cloud_token_surgically() -> None:
    body = _read()
    assert "openclaw.json" in body, "uninstall must handle ~/.openclaw/openclaw.json"
    # Surgical: remove only the 'clawmetry' JSON section...
    assert re.search(r"Properties\.Remove\('clawmetry'\)", body), (
        "cloudToken cleanup must surgically remove the 'clawmetry' key"
    )
    # ...and never delete OpenClaw's own home or config wholesale.
    assert 'RMDir /r "$PROFILE\\.openclaw"' not in body, (
        "must never delete the whole ~/.openclaw dir - it belongs to OpenClaw"
    )
    assert 'Delete "$PROFILE\\.openclaw\\openclaw.json"' not in body, (
        "must never delete openclaw.json itself - only ClawMetry's section"
    )


def test_uninstall_removes_clawmetry_owned_openclaw_files() -> None:
    body = _read()
    for path in (
        '"$PROFILE\\.openclaw\\.clawmetry"',
        '"$PROFILE\\.openclaw\\clawmetry.db"',
    ):
        assert path in body, f"uninstall must remove ClawMetry-owned {path}"


def test_uninstall_prefers_cli_cleanup_with_native_fallback() -> None:
    # The CLI is the single source of cleanup truth (server-side
    # /api/unregister, token mirror, keychain, ~/.clawmetry); the native
    # NSIS steps stay as the fallback for a broken venv - the exact
    # failure class that motivated this uninstaller.
    body = _read()
    cli_call = body.index('uninstall --yes')
    native = body.index('RMDir /r "$PROFILE\\.clawmetry"')
    assert cli_call < native, (
        "the CLI cleanup (`clawmetry uninstall --yes`) must run before the "
        "native fallback deletions"
    )


def test_uninstall_deletes_keychain_entry_before_venv_removal() -> None:
    body = _read()
    assert "keyring.delete_password" in body, (
        "uninstall must remove the OS-keychain workspace-key entry"
    )
    # The keychain cleanup shells out to the runtime venv's python, so the
    # data section that runs it must execute before UnSecMain deletes the
    # venv - i.e. be declared first (NSIS runs sections in declaration order).
    data_pos = body.index("keyring.delete_password")
    main_pos = body.index('RMDir /r "$LOCALAPPDATA\\ClawMetry"')
    assert data_pos < main_pos, (
        "UnSecData (keychain cleanup, needs venv python) must be declared "
        "before UnSecMain (which deletes the venv)"
    )


def test_uninstall_kills_processes_before_sections_run() -> None:
    # A live daemon would re-write config/token files behind the data
    # purge, so the process kill must live in un.onInit, not inside a
    # section that may run after the data sweep.
    body = _read()
    m = re.search(r"Function un\.onInit(.*?)FunctionEnd", body, re.DOTALL)
    assert m, "uninstaller must define un.onInit"
    assert "taskkill" in m.group(1), "un.onInit must kill ClawMetry.exe"
    assert "Win32_Process" in m.group(1), (
        "un.onInit must sweep processes running out of the app-data tree"
    )


def test_uninstall_removes_legacy_webview_profile() -> None:
    body = _read()
    assert 'RMDir /r "$APPDATA\\pywebview"' in body, (
        "uninstall must remove the legacy shared pywebview profile "
        "(pre-storage_path builds kept ClawMetry cookies/localStorage there)"
    )


def test_uninstall_path_strip_broadcasts_settingchange() -> None:
    body = _read()
    assert "WM_WININICHANGE" in body or "WM_SETTINGCHANGE" in body, (
        "PATH removal must broadcast WM_SETTINGCHANGE like the app does "
        "when adding the entry"
    )
    assert "TrimEnd" in body, "PATH strip must tolerate trailing backslashes"


def test_install_purges_stale_onboarding_state_on_fresh_install_only() -> None:
    body = _read()
    sec = re.search(r'Section "ClawMetry" SecMain(.*?)SectionEnd', body, re.DOTALL)
    assert sec, "SecMain missing"
    sec_body = sec.group(1)
    assert "onboarding-completed.json" in sec_body, (
        "fresh installs must purge a leftover onboarding stamp (manual/"
        "blocked uninstalls leave one behind and it skips sign-in)"
    )
    assert "app-instance.json" in sec_body, (
        "fresh installs must purge a leftover instance file (it attaches "
        "the window to an orphan daemon, bypassing onboarding)"
    )
    # Gated on registry state so UPGRADES keep their stamp (never re-onboard).
    assert re.search(r"ReadRegStr.*UNINSTALL_KEY.*UninstallString", sec_body), (
        "the purge must be gated on 'no registered install' so upgrades "
        "keep auth"
    )


def test_install_verifies_python_download_hash_before_executing() -> None:
    body = _read()
    assert "PYTHON_INSTALLER_SHA256" in body, "python download must be hash-pinned"
    check = body.index("Get-FileHash")
    execute = body.index('ExecWait \'"$TEMP\\clawmetry-python-setup.exe"')
    assert check < execute, "hash check must run before executing the download"
