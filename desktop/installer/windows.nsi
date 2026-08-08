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
