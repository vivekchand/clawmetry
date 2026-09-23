"""Execute the shipping NSIS cleanup macro in an isolated Windows uninstaller.

Uses the normal (non-silent) progress page: /S would hide the exact UI cost
this test guards. No installed ClawMetry files, registry entries or processes
are touched. The output row count, rather than runner speed, is the guard.
"""

import argparse
import os
from pathlib import Path
import subprocess
import tempfile
import time


def run(makensis, include):
    with tempfile.TemporaryDirectory(prefix="clawmetry-cleanup-") as tmp:
        root = Path(tmp).resolve()
        tree = root / "runtime"
        tree.mkdir()
        for index in range(5000):
            (tree / ("file-%d.txt" % index)).write_text("old runtime")
        neighbor = root / "keep.txt"
        neighbor.write_text("unrelated data")
        report = root / "report.txt"
        script = root / "test.nsi"
        script.write_text(r'''
Unicode true
Name "ClawMetry cleanup regression test"
OutFile "@ROOT@\harness.exe"
RequestExecutionLevel user
AutoCloseWindow true
ShowUninstDetails show
UninstPage instfiles
!include "@INCLUDE@"
Section
  WriteUninstaller "@ROOT@\uninstall.exe"
SectionEnd
Section "Uninstall"
  ; AutoCloseWindow applies only to the installer. This test has no human
  ; to press Close after the non-silent uninstaller finishes.
  SetAutoClose true
  !insertmacro ClawMetryRemoveTree "@ROOT@\runtime" "test runtime"
  ; Missing directories are idempotent, not an uninstall failure.
  !insertmacro ClawMetryRemoveTree "@ROOT@\missing" "missing runtime"
  FindWindow $0 "#32770" "" $HWNDPARENT
  GetDlgItem $1 $0 1016
  StrCmp $1 0 no_list
  ; LVM_GETITEMCOUNT: fail if deletion logs grow with the file count.
  SendMessage $1 0x1004 0 0 $2
  Goto write_report
no_list:
  StrCpy $2 "missing-list-view"
write_report:
  FileOpen $3 "@ROOT@\report.txt" w
  FileWrite $3 "$2"
  FileClose $3
SectionEnd
'''.replace("@ROOT@", str(root)).replace("@INCLUDE@", str(include)),
                          encoding="utf-8")
        subprocess.run([makensis, "/V2", str(script)], check=True, timeout=60)
        subprocess.run([str(root / "harness.exe"), "/S"], check=True, timeout=30)
        start = time.monotonic()
        result = subprocess.run(
            [str(root / "uninstall.exe"), "_?=" + str(root)], timeout=120,
        )
        elapsed = time.monotonic() - start
        assert result.returncode == 0, result.returncode
        assert not tree.exists(), "runtime was not removed"
        assert neighbor.read_text() == "unrelated data"
        rows = int(report.read_text())
        assert 1 <= rows <= 6, "per-file UI logging returned: %d rows" % rows
        print("5000 files removed in %.2fs; %d progress rows" % (elapsed, rows))

        # A locked file must survive, make the process fail, and still
        # allow cleanup of unlocked siblings. Never claim complete removal.
        tree.mkdir()
        locked = tree / "locked.txt"
        unlocked = tree / "unlocked.txt"
        unlocked.write_text("remove me")
        with locked.open("w") as held:
            held.write("held open")
            held.flush()
            result = subprocess.run(
                [str(root / "uninstall.exe"), "_?=" + str(root)], timeout=30,
            )
            assert result.returncode == 1, "locked file was reported as success"
            assert locked.exists()
            assert not unlocked.exists()
        assert neighbor.read_text() == "unrelated data"
        print("Locked-file failure and unrelated-file preservation verified")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--makensis", default=r"C:\Program Files (x86)\NSIS\makensis.exe")
    parser.add_argument("--include", type=Path,
                        default=Path(__file__).parent / "installer" / "cleanup.nsh")
    parser.add_argument("--verify-regression", action="store_true")
    args = parser.parse_args()
    if os.name != "nt":
        parser.error("this behavioral test requires Windows")
    if args.verify_regression:
        with tempfile.TemporaryDirectory(prefix="clawmetry-old-cleanup-") as tmp:
            legacy = Path(tmp) / "cleanup.nsh"
            legacy.write_text(args.include.read_text().replace(
                "  SetDetailsPrint none\n", ""
            ).replace("  SetDetailsPrint lastused\n", ""))
            try:
                run(args.makensis, legacy)
            except AssertionError as exc:
                if "per-file UI logging returned" not in str(exc):
                    raise
                print("Old behavior rejected:", exc)
            else:
                raise AssertionError("regression guard did not reject old behavior")
    run(args.makensis, args.include.resolve())
