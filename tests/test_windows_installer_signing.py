"""Windows Authenticode signing contract (Smart App Control uninstall bug).

Lab repro 2026-08-10 (Windows 11, SAC VerifiedAndReputablePolicyState=1):
with Smart App Control in enforce mode, the unsigned NSIS uninstaller's
temp-copy relaunch (%TEMP%\\Un_A.exe) is blocked by the Application Control
policy - "Error launching installer" - so the app cannot be uninstalled
from Settings > Apps at all.

The subtle part is WHERE the uninstaller gets signed. WriteUninstaller
regenerates $INSTDIR\\Uninstall.exe from the stub embedded in the setup
exe on every (re)install, so a signature applied to an installed
Uninstall.exe is wiped by the next setup run. The only durable signature
is the one makensis applies to the embedded stub via !uninstfinalize.
(The in-app auto-updater never touches $INSTDIR - it pip-upgrades the
runtime venv - so the installer is the only regeneration path to cover.)

Static contract-pinning on the .nsi source + workflow YAML: makensis and
signtool only run in the desktop-artifacts workflow, so this is the guard
that runs on every PR.
"""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NSI = ROOT / "desktop" / "installer" / "windows.nsi"
WORKFLOW = ROOT / ".github" / "workflows" / "desktop-artifacts.yml"


def _nsi() -> str:
    return NSI.read_text(encoding="utf-8")


def _wf() -> str:
    return WORKFLOW.read_text(encoding="utf-8")


def test_uninstaller_stub_is_signed_at_compile_time():
    """!uninstfinalize is the ONLY way a WriteUninstaller-regenerated
    Uninstall.exe can carry a signature - without it, SAC enforce mode
    bricks uninstall even when everything else is signed."""
    text = _nsi()
    assert "!uninstfinalize" in text, (
        "windows.nsi must sign the embedded uninstaller stub via "
        "!uninstfinalize - post-hoc signing of an installed Uninstall.exe "
        "is undone by the next (re)install's WriteUninstaller"
    )
    assert "!finalize" in text, (
        "windows.nsi must also sign the setup exe itself via !finalize"
    )


def test_signing_is_optional_so_forks_still_build():
    """Both hooks must be gated on the /DSIGN_CMD define: PRs from forks
    (no secrets) and local dev builds must still compile unsigned."""
    text = _nsi()
    m = re.search(r"!ifdef SIGN_CMD(.*?)!endif", text, re.S)
    assert m, "signing hooks must live inside an !ifdef SIGN_CMD block"
    assert "!finalize" in m.group(1) and "!uninstfinalize" in m.group(1), (
        "both !finalize and !uninstfinalize must be inside the "
        "!ifdef SIGN_CMD guard"
    )


def test_workflow_wires_sign_cmd_into_makensis():
    wf = _wf()
    assert "/DSIGN_CMD=" in wf, (
        "the Windows job must pass /DSIGN_CMD to makensis when the cert "
        "secrets are set, or the .nsi signing hooks never fire"
    )
    assert "WINDOWS_CERT_PFX_BASE64" in wf and "WINDOWS_CERT_PASSWORD" in wf, (
        "signing must be driven by the documented repo secrets"
    )
    assert "HAS_WIN_CERT" in wf, (
        "signing steps must be if:-gated on secret presence (macOS-job "
        "pattern) so forks and unsigned dev builds still succeed"
    )


def test_app_exe_signed_before_zip_and_installer_pack():
    """ClawMetry.exe must be signed before Compress-Archive and makensis
    run, or the portable zip / installed tree ship an unsigned app that
    SAC blocks at launch."""
    wf = _wf()
    sign_at = wf.index("Sign ClawMetry.exe")
    assert sign_at < wf.index("Compress-Archive"), (
        "ClawMetry.exe must be signed before the portable zip is built"
    )
    assert sign_at < wf.index("Build NSIS installer"), (
        "ClawMetry.exe must be signed before makensis packs the install tree"
    )


def test_signatures_are_timestamped_and_verified():
    wf = _wf()
    assert re.search(r"/tr\s+http", wf), (
        "signtool must use an RFC 3161 timestamp (/tr) so signatures "
        "outlive cert expiry"
    )
    assert "verify /pa" in wf, (
        "the workflow must signtool-verify the produced artifacts "
        "(FLYWHEEL: verify the artifact, not the build log)"
    )
