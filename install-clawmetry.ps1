# Clawmetry — One-line installer for Windows
# Usage: irm https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.ps1 | iex
$ErrorActionPreference = "Stop"

Write-Host "🔭 Installing Clawmetry — OpenClaw Observability Dashboard" -ForegroundColor Cyan
Write-Host ""

# Check for Python
$python = $null
foreach ($cmd in @("python3", "python")) {
    try {
        $ver = & $cmd --version 2>&1
        if ($ver -match "Python 3") {
            $python = $cmd
            break
        }
    } catch {}
}

if (-not $python) {
    Write-Host "→ Python 3 not found. Attempting install via winget..." -ForegroundColor Yellow
    try {
        winget install Python.Python.3.12 --accept-source-agreements --accept-package-agreements --silent
        $env:PATH = [System.Environment]::GetEnvironmentVariable("PATH", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("PATH", "User")
        $python = "python"
        # Verify
        & $python --version | Out-Null
    } catch {
        Write-Host "❌ Could not install Python automatically." -ForegroundColor Red
        Write-Host "   Please install Python 3 from https://www.python.org/downloads/" -ForegroundColor Red
        Write-Host "   Make sure to check 'Add Python to PATH' during installation." -ForegroundColor Red
        exit 1
    }
}

Write-Host "→ Using $python ($(& $python --version 2>&1))"

# Install directory
$installDir = "$env:LOCALAPPDATA\clawmetry"

# Remove old install for clean state
if (Test-Path $installDir) {
    Write-Host "→ Removing previous installation..."
    Remove-Item -Recurse -Force $installDir
}

# Create venv
Write-Host "→ Creating virtual environment at $installDir..."
& $python -m venv $installDir
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Failed to create virtual environment." -ForegroundColor Red
    exit 1
}

# Upgrade pip
& "$installDir\Scripts\python.exe" -m pip install --upgrade pip 2>&1 | Out-Null
# Install clawmetry
Write-Host "→ Installing clawmetry from PyPI..."
# --only-binary: no compiler on user machines; a missing wheel must fail
# clearly, not demand MSVC (field failure 2026-08-29, cffi on py3.14)
& "$installDir\Scripts\pip.exe" install --no-cache-dir --only-binary=:all: clawmetry 2>&1 | Out-Null
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Failed to install clawmetry." -ForegroundColor Red
    exit 1
}

# A pip run that "succeeded" is not necessarily a ClawMetry that works.
# Without a version floor pip does not FAIL when a dependency has no
# wheel for this interpreter -- it backtracks clawmetry ITSELF until the
# graph resolves, and installs whatever ancient release predates that
# dependency (issue #5639: a win32 interpreter silently resolves
# clawmetry 0.12.163, from before duckdb was a dependency at all).
# Nothing errors, so the user ends up running a 664-release-old
# ClawMetry against a current cloud.
#
# The tell is functional, not a version number: such a release does not
# carry today's dependency set. Importing it is threshold-free -- no
# "how old is too old" guess -- and it stays correct as the dependency
# set changes. A pre-install `clawmetry>=<latest>` pin was rejected on
# purpose: it also blocks the LEGITIMATE backtracking pip does when the
# newest release genuinely cannot be installed here (a propagation race
# right after a release, or a future python_requires bump), turning a
# transient into a hard failure.
& "$installDir\Scripts\python.exe" -c "import clawmetry, duckdb, cryptography" 2>&1 | Out-Null
if ($LASTEXITCODE -ne 0) {
    Write-Host "X Installed ClawMetry is missing its dependencies." -ForegroundColor Red
    Write-Host "   pip resolved an old release instead of failing, which means" -ForegroundColor Yellow
    Write-Host "   PyPI has no build of a current ClawMetry for this Python." -ForegroundColor Yellow
    Write-Host "   Install 64-bit python.org Python 3.12 and re-run, or if pip" -ForegroundColor Yellow
    Write-Host "   points at a private mirror, allow pypi.org." -ForegroundColor Yellow
    exit 1
}


# Add to PATH if not already there
$binDir = "$installDir\Scripts"
$userPath = [System.Environment]::GetEnvironmentVariable("PATH", "User")
if ($userPath -notlike "*$binDir*") {
    Write-Host "→ Adding clawmetry to PATH..."
    [System.Environment]::SetEnvironmentVariable("PATH", "$binDir;$userPath", "User")
    $env:PATH = "$binDir;$env:PATH"
}

# Detect OpenClaw workspace
$workspace = $null
$openclawDir = "$env:USERPROFILE\.openclaw"
if (Test-Path $openclawDir) {
    $workspace = $openclawDir
}

# Get version
$version = "installed"
try {
    $version = & "$binDir\clawmetry.exe" --version 2>&1
} catch {}

Write-Host ""
Write-Host "✅ Clawmetry installed successfully!" -ForegroundColor Green
Write-Host ""
Write-Host "  Version: $version"
Write-Host ""
Write-Host "  Start with:"
Write-Host "    clawmetry --host 0.0.0.0 --port 8900" -ForegroundColor White
Write-Host ""
if ($workspace) {
    Write-Host "  OpenClaw workspace detected: $workspace"
    Write-Host ""
}
Write-Host "  Then open http://YOUR_IP:8900 in your browser"
Write-Host ""
Write-Host "  To run in background (PowerShell):"
Write-Host "    Start-Process clawmetry -ArgumentList '--host 0.0.0.0 --port 8900' -WindowStyle Hidden" -ForegroundColor White
Write-Host ""
Write-Host "🔭 Happy observing!" -ForegroundColor Cyan
