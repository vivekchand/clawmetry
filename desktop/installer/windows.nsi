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
!insertmacro MUI_UNPAGE_COMPONENTS
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

; Founder bug 2026-08-08: uninstall + reinstall showed no onboarding, because
; the old uninstaller removed only $INSTDIR and left the app runtime (venv,
; onboarding stamp, logs) under %LOCALAPPDATA%\ClawMetry behind. Uninstalling
; now removes everything the app created. Account data (~\.clawmetry) is its
; own checkbox because it holds the E2E encryption key: deleting it makes
; already-synced cloud snapshots permanently undecryptable, so the user must
; see that choice, not have it made silently.

Section "un.ClawMetry program + runtime" UnSecMain
  SectionIn RO  ; always removed — this IS the uninstall

  ; Stop the shell and any daemon running out of the runtime venv so file
  ; locks don't leave half the tree behind. ExecWait + /F: no prompts.
  ExecWait `taskkill /F /T /IM ClawMetry.exe`
  ExecWait `powershell -NoProfile -Command "Get-CimInstance Win32_Process | Where-Object { $$_.ExecutablePath -like '$LOCALAPPDATA\ClawMetry\runtime\*' } | ForEach-Object { Stop-Process -Id $$_.ProcessId -Force }"`

  RMDir /r "$INSTDIR"

  ; Global CLI shim (written by the app at runtime into
  ; %LOCALAPPDATA%\ClawMetry\bin) + its user-PATH entry. Once the app
  ; is gone the shim points at a venv nobody manages, so clean both.
  RMDir /r "$LOCALAPPDATA\ClawMetry\bin"
  nsExec::ExecToLog `powershell -NoProfile -Command "$$b='$LOCALAPPDATA\ClawMetry\bin'; $$p=[Environment]::GetEnvironmentVariable('Path','User'); $$n=($$p -split ';' | Where-Object { $$_ -and $$_ -ne $$b }) -join ';'; if ($$n -ne $$p) { [Environment]::SetEnvironmentVariable('Path',$$n,'User') }"`

  Delete "$SMPROGRAMS\ClawMetry\ClawMetry.lnk"
  Delete "$SMPROGRAMS\ClawMetry\Uninstall ClawMetry.lnk"
  RMDir "$SMPROGRAMS\ClawMetry"
  Delete "$DESKTOP\ClawMetry.lnk"
  DeleteRegKey HKCU "${UNINSTALL_KEY}"

  ; App-created runtime state: the venv, the onboarding-completed stamp, and
  ; logs. Removing the stamp is what makes a reinstall re-onboard.
  RMDir /r "$LOCALAPPDATA\ClawMetry\runtime"
  ; Global CLI shim dir (present on installs whose app.py wrote it). The
  ; user-PATH entry it registered is stripped by the shim-aware uninstaller
  ; work; deleting the dir here keeps a stale shim from shadowing pip's.
  RMDir /r "$LOCALAPPDATA\ClawMetry\bin"
  ; Remove the parent only if nothing else claimed it (RMDir without /r is
  ; a no-op on a non-empty dir).
  RMDir "$LOCALAPPDATA\ClawMetry"
SectionEnd

Section "un.Account data + E2E encryption keys (~\.clawmetry)" UnSecData
  ; WARNING surfaced in the components page description: this deletes the
  ; node identity and the AES-256-GCM key — encrypted snapshots already in
  ; the cloud can never be decrypted again.
  RMDir /r "$PROFILE\.clawmetry"
SectionEnd

!insertmacro MUI_UNFUNCTION_DESCRIPTION_BEGIN
  !insertmacro MUI_DESCRIPTION_TEXT ${UnSecMain} "Removes the ClawMetry app, its runtime (bundled Python environment, onboarding state, logs), shortcuts, and registry entries."
  !insertmacro MUI_DESCRIPTION_TEXT ${UnSecData} "Also deletes ~\.clawmetry: your node identity, API key, and end-to-end encryption key. WARNING: encrypted snapshots already synced to ClawMetry Cloud become permanently unreadable. Uncheck to keep your keys for a later reinstall."
!insertmacro MUI_UNFUNCTION_DESCRIPTION_END
