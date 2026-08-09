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
!include "WinMessages.nsh"

!ifndef VERSION
  !define VERSION "0.0.0-dev"
!endif
; Numeric x.y.z.w file version for VIProductVersion. CI passes
; /DVIVERSION=<major>.<minor>.<patch>.0 so deployment tools can compare
; installed exe versions; local dev builds fall back to 0.0.0.0.
!ifndef VIVERSION
  !define VIVERSION "0.0.0.0"
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

VIProductVersion "${VIVERSION}"
VIAddVersionKey "ProductName" "ClawMetry"
VIAddVersionKey "CompanyName" "ClawMetry"
VIAddVersionKey "FileDescription" "ClawMetry desktop installer"
VIAddVersionKey "FileVersion" "${VERSION}"
VIAddVersionKey "ProductVersion" "${VERSION}"
VIAddVersionKey "LegalCopyright" "ClawMetry"

!define UNINSTALL_KEY "Software\Microsoft\Windows\CurrentVersion\Uninstall\ClawMetry"

; --- Authenticode signing (CI passes /DSIGN_CMD=<path to sign wrapper>) ---
; Both the installer AND the uninstaller stub must be signed, and the
; uninstaller can only be signed HERE, at compile time: WriteUninstaller
; regenerates $INSTDIR\Uninstall.exe from the stub embedded in this
; installer on every (re)install, so a post-hoc signature on an installed
; Uninstall.exe would be wiped by the next setup run. !uninstfinalize signs
; the stub before it is embedded, making every regenerated copy signed.
;
; Why this matters (lab repro 2026-08-10): Windows 11 Smart App Control in
; enforce mode blocks the NSIS uninstaller's temp-copy relaunch
; (%TEMP%\Un_A.exe) when Uninstall.exe is unsigned - "Error launching
; installer" - so users cannot uninstall from Settings > Apps at all. The
; Authenticode signature travels with the temp copy, which is exactly what
; SAC checks.
;
; %1 is the file NSIS wants signed. The wrapper (written by CI) calls
; signtool with the cert; a nonzero exit fails the build loudly.
!ifdef SIGN_CMD
  !finalize '"${SIGN_CMD}" "%1"'
  !uninstfinalize '"${SIGN_CMD}" "%1"'
!endif

; Python 3 is a hard dependency of the thin-shell architecture (app.py
; needs a real interpreter to build the runtime venv it pip-installs
; clawmetry into - PyInstaller's own frozen interpreter can't run
; `-m venv`). Treat it as an auto-installing dependency: probe for a
; usable interpreter and, if none, download the python.org installer and
; run it silently, per-user (InstallAllUsers=0 + InstallLauncherAllUsers=0
; keeps it UAC-free, matching RequestExecutionLevel user). Best-effort:
; any failure here is logged and the install continues - app.py has a
; winget fallback at first launch, and worst case shows the
; "install python.org" guidance it always had.
!define PYTHON_VERSION "3.12.10"
!define PYTHON_INSTALLER_URL "https://www.python.org/ftp/python/${PYTHON_VERSION}/python-${PYTHON_VERSION}-amd64.exe"
; SHA-256 of python-3.12.10-amd64.exe, verified 2026-08-10 against the MD5
; python.org publishes on the 3.12.10 release page (5eddb0b6f12c852725de071ae681dde4).
; Bump BOTH constants together when PYTHON_VERSION changes.
!define PYTHON_INSTALLER_SHA256 "67B5635E80EA51072B87941312D00EC8927C4DB9BA18938F7AD2D27B328B95FB"

Section "-PythonRuntime"
  ; Probe exactly what app.py's _bootstrap_python() needs: an interpreter
  ; whose venv + pip modules import. (`py` launcher first, then PATH
  ; python - the bare probe also weeds out the Microsoft Store alias stub,
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

  ; Integrity check before executing a binary we just pulled off the
  ; network: refuse to run it on any hash mismatch (truncated download,
  ; middlebox tampering). PowerShell exits 1 on mismatch via the if().
  nsExec::ExecToStack 'powershell -NoProfile -ExecutionPolicy Bypass -Command "if ((Get-FileHash \"$TEMP\clawmetry-python-setup.exe\" -Algorithm SHA256).Hash -ne \"${PYTHON_INSTALLER_SHA256}\") { exit 1 }"'
  Pop $0
  Pop $1
  StrCmp $0 "0" +4
    DetailPrint "Python installer failed its SHA-256 check - discarding. ClawMetry will retry at first launch."
    Delete "$TEMP\clawmetry-python-setup.exe"
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
  ; Upgrade-in-place: a running instance holds file locks File /r cannot
  ; overwrite (NSIS would throw per-file retry/abort prompts). Stop the
  ; shell and anything running out of the app-data tree first.
  ExecWait `taskkill /F /T /IM ClawMetry.exe`
  ExecWait `powershell -NoProfile -Command "Get-CimInstance Win32_Process | Where-Object { $$_.ExecutablePath -like '$LOCALAPPDATA\ClawMetry\*' } | ForEach-Object { Stop-Process -Id $$_.ProcessId -Force }"`

  ; Fresh-install defense (founder bug 2026-08-10): when Windows has no
  ; ClawMetry registered, any leftover runtime state is debris from a
  ; broken or manual uninstall (e.g. an AV/Smart-App-Control-blocked
  ; uninstaller). A stale onboarding stamp skips sign-in and a stale
  ; instance file attaches to an orphan daemon - a "fresh" install then
  ; lands on the dashboard without ever asking the user to log in. Purge
  ; the debris on fresh installs only; a REGISTERED install (upgrade)
  ; keeps its runtime + stamp so upgrades never re-onboard.
  ReadRegStr $0 HKCU "${UNINSTALL_KEY}" "UninstallString"
  StrCmp $0 "" 0 not_fresh
    Delete "$LOCALAPPDATA\ClawMetry\runtime\onboarding-completed.json"
    Delete "$LOCALAPPDATA\ClawMetry\runtime\app-instance.json"
not_fresh:

  SetOutPath "$INSTDIR"
  File /r "${SRC_DIR}\*.*"

  CreateDirectory "$SMPROGRAMS\ClawMetry"
  CreateShortcut "$SMPROGRAMS\ClawMetry\ClawMetry.lnk" "$INSTDIR\ClawMetry.exe" "" "$INSTDIR\ClawMetry.exe"
  CreateShortcut "$DESKTOP\ClawMetry.lnk" "$INSTDIR\ClawMetry.exe" "" "$INSTDIR\ClawMetry.exe"

  WriteUninstaller "$INSTDIR\Uninstall.exe"
  CreateShortcut "$SMPROGRAMS\ClawMetry\Uninstall ClawMetry.lnk" "$INSTDIR\Uninstall.exe"

  ; Per-user (HKCU) registration - matches RequestExecutionLevel user, no
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
; onboarding stamp, logs) under %LOCALAPPDATA%\ClawMetry behind.
; Founder directive 2026-08-10: uninstall removes EVERY file ClawMetry
; created - app, runtime, ~\.clawmetry, the cloudToken mirrored into
; OpenClaw's config, ClawMetry-owned files inside ~\.openclaw, the OS
; keychain entry, and the WebView browser profile. The account-data section
; stays a visible checkbox (selected by default) because deleting the E2E
; encryption key makes already-synced cloud snapshots permanently
; undecryptable - users who plan to reinstall can uncheck it; everyone
; else gets the clean sweep they asked for.

Function un.onInit
  ; Stop the shell and every process running out of the app-data tree
  ; BEFORE any section runs: a live daemon would re-write config/token
  ; files behind the data purge, and file locks would leave half the
  ; tree behind. ExecWait + /F: no prompts.
  ExecWait `taskkill /F /T /IM ClawMetry.exe`
  ExecWait `powershell -NoProfile -Command "Get-CimInstance Win32_Process | Where-Object { $$_.ExecutablePath -like '$LOCALAPPDATA\ClawMetry\*' } | ForEach-Object { Stop-Process -Id $$_.ProcessId -Force }"`
FunctionEnd

; NOTE: UnSecData is declared BEFORE UnSecMain on purpose - the keychain
; cleanup shells out to the runtime venv's python, which UnSecMain deletes.
Section "un.Account data + E2E encryption keys" UnSecData
  ; OS keychain copy of the workspace key (service 'clawmetry', account
  ; 'workspace-key:<node_id>'). Needs the venv python + config.json, so it
  ; must run before either is removed. Best-effort: missing venv/config/
  ; keyring just exits non-zero and we move on.
  nsExec::ExecToLog `"$LOCALAPPDATA\ClawMetry\runtime\venv\Scripts\python.exe" -c "import json,pathlib,keyring;cfg=json.load(open(pathlib.Path.home()/'.clawmetry'/'config.json'));keyring.delete_password('clawmetry','workspace-key:'+cfg.get('node_id',''))"`

  ; The cm_ bearer mirrored into OpenClaw's own config. Surgical JSON edit:
  ; remove ONLY the 'clawmetry' section - the file belongs to OpenClaw and
  ; must survive with its other keys intact.
  nsExec::ExecToLog `powershell -NoProfile -Command "try { $$f=\"$PROFILE\.openclaw\openclaw.json\"; if (Test-Path $$f) { $$j = Get-Content $$f -Raw | ConvertFrom-Json; if ($$j.PSObject.Properties['clawmetry']) { $$j.PSObject.Properties.Remove('clawmetry'); $$j | ConvertTo-Json -Depth 32 | Set-Content $$f -Encoding utf8 } } } catch {}"`

  ; ClawMetry-owned files inside the OpenClaw home (local DuckDB store +
  ; scratch dir). Never touch anything else under ~\.openclaw.
  RMDir /r "$PROFILE\.openclaw\.clawmetry"
  Delete "$PROFILE\.openclaw\clawmetry.db"
  Delete "$PROFILE\.openclaw\clawmetry.db-shm"
  Delete "$PROFILE\.openclaw\clawmetry.db-wal"

  ; Node identity, api key, E2E encryption key, license, telemetry ids,
  ; sync state, local history DB.
  RMDir /r "$PROFILE\.clawmetry"
SectionEnd

Section "un.ClawMetry program + runtime" UnSecMain
  SectionIn RO  ; always removed - this IS the uninstall

  RMDir /r "$INSTDIR"

  ; User-PATH entry for the global CLI shim. Tolerant match (case-
  ; insensitive by PS default, trailing-backslash agnostic), and broadcast
  ; WM_SETTINGCHANGE so open shells learn about the change - the app
  ; broadcasts when ADDING the entry; removal must mirror that.
  nsExec::ExecToLog `powershell -NoProfile -Command "$$b='$LOCALAPPDATA\ClawMetry\bin'; $$p=[Environment]::GetEnvironmentVariable('Path','User'); $$n=($$p -split ';' | Where-Object { $$_ -and ($$_.TrimEnd('\') -ne $$b) }) -join ';'; if ($$n -ne $$p) { [Environment]::SetEnvironmentVariable('Path',$$n,'User') }"`
  SendMessage ${HWND_BROADCAST} ${WM_WININICHANGE} 0 "STR:Environment" /TIMEOUT=5000

  Delete "$SMPROGRAMS\ClawMetry\ClawMetry.lnk"
  Delete "$SMPROGRAMS\ClawMetry\Uninstall ClawMetry.lnk"
  RMDir "$SMPROGRAMS\ClawMetry"
  Delete "$DESKTOP\ClawMetry.lnk"
  DeleteRegKey HKCU "${UNINSTALL_KEY}"

  ; The entire app-data tree: runtime venv, onboarding stamp, logs, global
  ; CLI shim (bin\), the private WebView profile (webview\), and any legacy
  ; stray venv layout older builds left at the top level. Removing the
  ; stamp is what makes a reinstall re-onboard.
  RMDir /r "$LOCALAPPDATA\ClawMetry"

  ; Legacy shared pywebview profile (%APPDATA%\pywebview) - builds before
  ; the private storage_path fix kept ClawMetry's cookies/localStorage
  ; here. ClawMetry is the only pywebview app we ship; per the 2026-08-10
  ; founder directive every file ClawMetry created goes.
  RMDir /r "$APPDATA\pywebview"
SectionEnd

!insertmacro MUI_UNFUNCTION_DESCRIPTION_BEGIN
  !insertmacro MUI_DESCRIPTION_TEXT ${UnSecMain} "Removes the ClawMetry app, its runtime (bundled Python environment, onboarding state, logs, browser profile), shortcuts, PATH entry, and registry entries. (The system-wide Python runtime the installer may have added is shared with other tools and is kept.)"
  !insertmacro MUI_DESCRIPTION_TEXT ${UnSecData} "Deletes all ClawMetry data: ~\.clawmetry (node identity, API key, end-to-end encryption key, local history), the cloud token stored in OpenClaw's config, ClawMetry's local database, and the OS keychain entry. WARNING: encrypted snapshots already synced to ClawMetry Cloud become permanently unreadable. Uncheck only if you plan to reinstall and keep your keys."
!insertmacro MUI_UNFUNCTION_DESCRIPTION_END
