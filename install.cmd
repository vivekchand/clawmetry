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
echo   Ready! Run 'clawmetry' to start the dashboard.
echo   Then open http://localhost:8900 in your browser.
echo.
