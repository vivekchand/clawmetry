"""Windows uninstaller cleanup contract (founder bug 2026-08-08).

Uninstall + reinstall showed no onboarding: the uninstaller removed only
$INSTDIR and left %LOCALAPPDATA%\\ClawMetry\\runtime (venv + the
onboarding-completed.json stamp + logs) behind, so `is_first_launch()`
stayed False forever. These assertions pin the uninstall contract:

  * the runtime dir (and with it the onboarding stamp) is always removed;
  * running processes are stopped first so file locks can't strand the tree;
  * account data (~\\.clawmetry, holding the E2E encryption key) is removed
    only via a user-visible components-page choice, never silently as part
    of the mandatory section.

Static contract-pinning on the .nsi source: makensis only runs in the
desktop-artifacts workflow, so this is the guard that runs on every PR.
"""

import re
from pathlib import Path

NSI = Path(__file__).resolve().parents[1] / "desktop" / "installer" / "windows.nsi"


def _nsi_text() -> str:
    return NSI.read_text(encoding="utf-8")


def _uninstall_sections(text: str) -> dict:
    """Map uninstaller section header line -> section body."""
    sections = {}
    for m in re.finditer(
        r'^Section\s+"(un\.[^"]+)"[^\n]*\n(.*?)^SectionEnd',
        text,
        re.M | re.S,
    ):
        sections[m.group(1)] = m.group(2)
    return sections


def test_uninstaller_removes_runtime_dir_in_mandatory_section():
    sections = _uninstall_sections(_nsi_text())
    mandatory = [body for body in sections.values() if "SectionIn RO" in body]
    assert mandatory, "uninstaller must have a mandatory (SectionIn RO) section"
    assert any(
        r'RMDir /r "$LOCALAPPDATA\ClawMetry\runtime"' in body for body in mandatory
    ), (
        "the mandatory uninstall section must remove "
        r"%LOCALAPPDATA%\ClawMetry\runtime - leaving it behind strands the "
        "onboarding-completed.json stamp and a reinstall never re-onboards"
    )


def test_uninstaller_stops_running_processes_before_removal():
    text = _nsi_text()
    assert "taskkill" in text, "uninstaller must stop ClawMetry.exe before removal"
    assert "Stop-Process" in text, (
        "uninstaller must stop daemon processes running from the runtime venv, "
        "or Windows file locks leave a half-deleted tree"
    )


def test_account_data_removal_is_a_visible_choice_not_silent():
    text = _nsi_text()
    sections = _uninstall_sections(text)
    data_sections = [
        (name, body) for name, body in sections.items() if ".clawmetry" in body
    ]
    assert data_sections, (
        "uninstaller must offer removing ~\\.clawmetry (full cleanup was an "
        "explicit founder ask 2026-08-08)"
    )
    for name, body in data_sections:
        assert "SectionIn RO" not in body, (
            f"section '{name}' deletes ~\\.clawmetry (the E2E encryption key!) "
            "but is mandatory - key deletion must be a user-visible choice"
        )
    assert "MUI_UNPAGE_COMPONENTS" in text, (
        "uninstaller needs the components page so the account-data section is "
        "an actual visible checkbox"
    )
    assert re.search(r"MUI_DESCRIPTION_TEXT.*(encryption|unreadable)", text), (
        "the account-data checkbox must warn that deleting the key makes "
        "synced snapshots unreadable"
    )
