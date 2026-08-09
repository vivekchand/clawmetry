; ClawMetry Windows installer (NSIS / Modern UI 2).
;
; Wraps the PyInstaller one-folder build (dist\ClawMetry\, produced by
; desktop\build_windows.spec) into a real installer: Start Menu + Desktop
; shortcuts, an uninstaller registered in Add/Remove Programs, and a
; per-user install directory so there is no UAC prompt and no admin
; requirement (matches where app.py already keeps the runtime venv,
; %LOCALAPPDATA%\ClawMetry\runtime).
;
; Built in CI by .github/workflows/desktop-artifacts.yml (Windows job):
;   makensis /DVERSION=<version> /DSRC_DIR=<abs path to dist\ClawMetry> desktop\installer\windows.nsi
;
; Local test (from repo root, after building the PyInstaller spec):
;   pyinstaller --clean --noconfirm desktop\build_windows.spec
;   makensis /DVERSION=0.0.0-dev /DSRC_DIR=dist\ClawMetry desktop\installer\windows.nsi

!include "MUI2.nsh"

!ifndef VERSION
  !define VERSION "0.0.0-dev"
!endif
!ifndef SRC_DIR
  !define SRC_DIR "..\..\dist\ClawMetry"
!endif

Name "ClawMetry"
OutFile "ClawMetry-Setup-${VERSION}.exe"
InstallDir "$LOCALAPPDATA\Programs\ClawMetry"
RequestExecutionLevel user
SetCompressor /SOLID lzma
Unicode true

!define MUI_ICON "..\assets\ClawMetry.ico"
!define MUI_UNICON "..\assets\ClawMetry.ico"
!define MUI_ABORTWARNING
!define MUI_FINISHPAGE_RUN "$INSTDIR\ClawMetry.exe"
!define MUI_FINISHPAGE_RUN_TEXT "Launch ClawMetry"

!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_LICENSE "..\..\LICENSE"
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES

!insertmacro MUI_LANGUAGE "English"

VIProductVersion "0.0.0.0"
VIAddVersionKey "ProductName" "ClawMetry"
VIAddVersionKey "CompanyName" "ClawMetry"
VIAddVersionKey "FileDescription" "ClawMetry desktop installer"
VIAddVersionKey "FileVersion" "${VERSION}"
VIAddVersionKey "ProductVersion" "${VERSION}"
VIAddVersionKey "LegalCopyright" "ClawMetry"

!define UNINSTALL_KEY "Software\Microsoft\Windows\CurrentVersion\Uninstall\ClawMetry"

; Python 3 is a hard dependency of the thin-shell architecture (app.py
; needs a real interpreter to build the runtime venv it pip-installs
; clawmetry into — PyInstaller's own frozen interpreter can't run
; `-m venv`). Treat it as an auto-installing dependency: probe for a
; usable interpreter and, if none, download the python.org installer and
; run it silently, per-user (InstallAllUsers=0 + InstallLauncherAllUsers=0
; keeps it UAC-free, matching RequestExecutionLevel user). Best-effort:
; any failure here is logged and the install continues — app.py has a
; winget fallback at first launch, and worst case shows the
; "install python.org" guidance it always had.
!define PYTHON_VERSION "3.12.10"
!define PYTHON_INSTALLER_URL "https://www.python.org/ftp/python/${PYTHON_VERSION}/python-${PYTHON_VERSION}-amd64.exe"

Section "-PythonRuntime"
  ; Probe exactly what app.py's _bootstrap_python() needs: an interpreter
  ; whose venv + pip modules import. (`py` launcher first, then PATH
  ; python — the bare probe also weeds out the Microsoft Store alias stub,
  ; which fails the import.)
  nsExec::ExecToStack 'py -3 -c "import venv,pip"'
  Pop $0
  Pop $1
  StrCmp $0 "0" python_ok
  nsExec::ExecToStack 'python -c "import venv,pip"'
  Pop $0
  Pop $1
  StrCmp $0 "0" python_ok

  DetailPrint "Python 3 not found - downloading Python ${PYTHON_VERSION} (~26 MB)..."
  ; PowerShell is the downloader (ships on every supported Windows; the
  ; bundled NSISdl can't do HTTPS and inetc isn't on the CI runner's
  ; stock NSIS). \" survives NSIS's single-quoted string literally and
  ; PowerShell's command-line parser reads it as an escaped quote, so
  ; $TEMP paths with spaces stay intact.
  nsExec::ExecToLog 'powershell -NoProfile -ExecutionPolicy Bypass -Command "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri ${PYTHON_INSTALLER_URL} -OutFile \"$TEMP\clawmetry-python-setup.exe\""'
  Pop $0
  StrCmp $0 "0" +3
    DetailPrint "Python download failed - ClawMetry will retry at first launch."
    Goto python_done

  DetailPrint "Installing Python ${PYTHON_VERSION} (per-user, no admin needed)..."
  ExecWait '"$TEMP\clawmetry-python-setup.exe" /quiet InstallAllUsers=0 InstallLauncherAllUsers=0 PrependPath=1 Include_launcher=1 Include_test=0' $0
  Delete "$TEMP\clawmetry-python-setup.exe"
  StrCmp $0 "0" +2
    DetailPrint "Python installer exited with code $0 - ClawMetry will retry at first launch."
  Goto python_done

python_ok:
  DetailPrint "Python 3 found - skipping bundled runtime install."
python_done:
SectionEnd

Section "ClawMetry" SecMain
  SetOutPath "$INSTDIR"
  File /r "${SRC_DIR}\*.*"

  CreateDirectory "$SMPROGRAMS\ClawMetry"
  CreateShortcut "$SMPROGRAMS\ClawMetry\ClawMetry.lnk" "$INSTDIR\ClawMetry.exe" "" "$INSTDIR\ClawMetry.exe"
  CreateShortcut "$DESKTOP\ClawMetry.lnk" "$INSTDIR\ClawMetry.exe" "" "$INSTDIR\ClawMetry.exe"

  WriteUninstaller "$INSTDIR\Uninstall.exe"
  CreateShortcut "$SMPROGRAMS\ClawMetry\Uninstall ClawMetry.lnk" "$INSTDIR\Uninstall.exe"

  ; Per-user (HKCU) registration — matches RequestExecutionLevel user, no
  ; admin rights needed to show up in Windows' "Apps & features".
  WriteRegStr HKCU "${UNINSTALL_KEY}" "DisplayName" "ClawMetry"
  WriteRegStr HKCU "${UNINSTALL_KEY}" "UninstallString" '"$INSTDIR\Uninstall.exe"'
  WriteRegStr HKCU "${UNINSTALL_KEY}" "InstallLocation" "$INSTDIR"
  WriteRegStr HKCU "${UNINSTALL_KEY}" "DisplayIcon" "$INSTDIR\ClawMetry.exe"
  WriteRegStr HKCU "${UNINSTALL_KEY}" "DisplayVersion" "${VERSION}"
  WriteRegStr HKCU "${UNINSTALL_KEY}" "Publisher" "ClawMetry"
  WriteRegDWORD HKCU "${UNINSTALL_KEY}" "NoModify" 1
  WriteRegDWORD HKCU "${UNINSTALL_KEY}" "NoRepair" 1
SectionEnd

Section "Uninstall"
  ; Program files only — the runtime venv under %LOCALAPPDATA%\ClawMetry\runtime
  ; and the account config under %USERPROFILE%\.clawmetry are left in place,
  ; same as every other installer here: uninstalling the app doesn't wipe
  ; the user's synced data or a fresh reinstall's ability to skip re-onboarding.
  RMDir /r "$INSTDIR"
  Delete "$SMPROGRAMS\ClawMetry\ClawMetry.lnk"
  Delete "$SMPROGRAMS\ClawMetry\Uninstall ClawMetry.lnk"
  RMDir "$SMPROGRAMS\ClawMetry"
  Delete "$DESKTOP\ClawMetry.lnk"
  DeleteRegKey HKCU "${UNINSTALL_KEY}"
SectionEnd
