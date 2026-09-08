@echo off
REM ClawMetry Installer for Windows (CMD)
REM Usage: curl -fsSL https://clawmetry.com/install.cmd -o install.cmd && install.cmd && del install.cmd

echo.
echo   🦞 ClawMetry Installer
echo   Real-time observability ^& governance for AI agents
echo.

REM Check for Python
where python >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    where python3 >nul 2>&1
    if %ERRORLEVEL% NEQ 0 (
        echo   ✗ Python not found.
        echo   Install Python from https://python.org/downloads
        echo.
        exit /b 1
    )
    set PYTHON=python3
) else (
    set PYTHON=python
)

REM Check Python version
%PYTHON% -c "import sys; exit(0 if sys.version_info >= (3, 10) else 1)" 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo   ✗ Python 3.10+ required.
    echo   Install from https://python.org/downloads
    exit /b 1
)

REM Stale-duplicate sweep: this installer puts clawmetry directly into
REM whichever python/python3 is on PATH, with no dedicated venv. If a
REM DIFFERENT python (or the install.ps1 dedicated venv) also has clawmetry,
REM whichever one PATH resolves first silently shadows the other and
REM `clawmetry --version` can report a stale version even though this
REM install is current. Sweep every python/python3 found on PATH and
REM uninstall clawmetry from all of them before installing fresh.
set "CM_SEEN="
for /f "delims=" %%P in ('where python 2^>nul') do call :cm_sweep_stale "%%P"
for /f "delims=" %%P in ('where python3 2^>nul') do call :cm_sweep_stale "%%P"
if exist "%LOCALAPPDATA%\clawmetry" (
    echo   → Removing stale dedicated-venv install...
    rmdir /s /q "%LOCALAPPDATA%\clawmetry" 2>nul
)
goto :cm_sweep_done

:cm_sweep_stale
set "CM_PYEXE=%~1"
echo %CM_SEEN%| findstr /I /C:"%CM_PYEXE%" >nul 2>&1
if not errorlevel 1 goto :eof
set "CM_SEEN=%CM_SEEN%;%CM_PYEXE%"
"%CM_PYEXE%" -m pip show clawmetry >nul 2>&1
if not errorlevel 1 (
    echo   → Removing stale clawmetry copy from %CM_PYEXE%...
    "%CM_PYEXE%" -m pip uninstall -y clawmetry >nul 2>&1
)
goto :eof

:cm_sweep_done

echo   → Installing clawmetry...
%PYTHON% -m pip install --upgrade clawmetry >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    %PYTHON% -m pip install --user --upgrade clawmetry >nul 2>&1
)

echo   ✓ Installed clawmetry
echo.

REM ── Existing setup: account probe + "re-onboard?" gate ──────────────────
REM Same contract as install.sh / install.ps1: this script is also the upgrade
REM path, so on a machine that is ALREADY linked to a ClawMetry account it
REM reports that setup and asks before replaying the wizard over it. With no
REM account linked it runs `clawmetry onboard` straight away.
REM
REM The probe below both PRINTS the summary and carries the answer in its exit
REM code (0 = connected), so batch never has to parse JSON. Any failure -- an
REM unreadable config, a CLI too old for `status --json`, no network -- exits
REM non-zero, which means "not connected" and simply runs the wizard as before.
if "%CLAWMETRY_SKIP_ONBOARD%"=="1" (
    echo   Skipping onboard ^(CLAWMETRY_SKIP_ONBOARD=1^) - set up later with: clawmetry onboard
    goto :cm_onboard_done
)

set "CM_STATUS_FILE=%TEMP%\clawmetry-status.json"
%PYTHON% -m clawmetry status --json > "%CM_STATUS_FILE%" 2>nul
%PYTHON% -c "import json,os;h=os.path.expanduser('~');d=os.path.join(h,'.clawmetry');g=lambda p:(json.loads(open(p).read()) if p and os.path.exists(p) else {});c=g(os.path.join(d,'config.json'));s=g(os.environ.get('CM_STATUS_FILE',''));cl=s.get('cloud_sync') or {};a=cl.get('account') or {};k=str(c.get('api_key') or '') or os.environ.get('CLAWMETRY_API_KEY','');e=str(a.get('email') or c.get('account_email') or '');ph=bool(a.get('placeholder')) or e.lower().endswith(('@clawmetry.auto','@clawmetry.linked'));conn=(bool(k) or bool(cl.get('api_key_masked'))) and not ph;pl=str(a.get('plan') or g(os.path.join(d,'cloud_plan.json')).get('plan') or '');lo=cl.get('local_only');lo=(bool(c.get('local_only')) or os.path.exists(os.path.join(d,'nocloud'))) if lo is None else bool(lo);L={'oss':'OSS','cloud_free':'Free','free':'Free','trial':'Trial','cloud_starter':'Starter','cloud_pro':'Pro','pro':'Self-hosted Pro','enterprise':'Enterprise'};lab=L.get(pl.lower(),pl.replace('cloud_','').replace('_',' ').title());n=str(cl.get('node_id') or c.get('node_id') or '');v=str(s.get('version') or '');out=[];out.append('  You are already connected to ClawMetry');out.append('');out.append('    Account:     '+e+('  ['+lab+' plan]' if lab else '')) if e else None;out.append('    Cloud sync:  '+('Local-only, data stays on this machine' if lo else 'On, syncing to app.clawmetry.com'));out.append('    Version:     '+v) if v else None;out.append('    Node:        '+n) if n else None;print(chr(10).join(out)) if conn else None;raise SystemExit(0 if conn else 1)" 2>nul
set "CM_PROBE_RC=%ERRORLEVEL%"
del "%CM_STATUS_FILE%" >nul 2>&1
set "CM_STATUS_FILE="

if not "%CM_PROBE_RC%"=="0" (
    %PYTHON% -m clawmetry onboard
    goto :cm_onboard_done
)

REM CLAWMETRY_REONBOARD forces the answer without asking; anything else asks,
REM and an empty answer (including a non-interactive run, where `set /p`
REM returns immediately) keeps the setup that is already on this machine.
if /I "%CLAWMETRY_REONBOARD%"=="1" goto :cm_reonboard
if /I "%CLAWMETRY_REONBOARD%"=="0" goto :cm_keep
echo.
set "CM_ANS="
set /p "CM_ANS=  Re-run setup [account, cloud vs local-only, license]? [y/N]: "
if /I "%CM_ANS%"=="y" goto :cm_reonboard
if /I "%CM_ANS%"=="yes" goto :cm_reonboard

:cm_keep
echo.
echo   Keeping your current setup.
echo   Change it anytime: clawmetry onboard
goto :cm_onboard_done

:cm_reonboard
%PYTHON% -m clawmetry onboard

:cm_onboard_done

echo.
echo   Ready! Run 'clawmetry' to start the dashboard.
echo   Then open http://localhost:8900 in your browser.
echo.
