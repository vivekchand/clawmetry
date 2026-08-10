# Clawmetry — One-line installer for Windows
# Usage: irm https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.ps1 | iex
$ErrorActionPreference = "Stop"

Write-Host "🦞 ClawMetry  Real-time observability & governance for AI agents" -ForegroundColor Cyan
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

# ── Stale-duplicate sweep ────────────────────────────────────────────────
# The dedicated venv above is the ONLY environment auto-update keeps current.
# A clawmetry copy left behind in some OTHER interpreter (e.g. a system-wide
# `pip install --user clawmetry` from before this installer switched to a
# per-app venv, or a leftover from install.cmd) never updates, and if it
# happens to resolve first on PATH it shadows the venv binary — `clawmetry
# --version` then reports a stale version while the real install is current.
# Sweep every python interpreter reachable on PATH and uninstall clawmetry
# from all of them except the one we're about to (re)build.
$seenPython = New-Object System.Collections.Generic.HashSet[string]
$pyCandidates = @()
foreach ($cmd in @("python", "python3")) {
    try {
        $cmdInfo = Get-Command $cmd -All -ErrorAction SilentlyContinue
        foreach ($c in $cmdInfo) { $pyCandidates += $c.Source }
    } catch {}
}
try {
    $launcherList = & py -0p 2>&1
    foreach ($line in $launcherList) {
        if ($line -match '(?m)^\s*\S+\s+(.+\\python\.exe)\s*$') {
            $pyCandidates += $Matches[1]
        }
    }
} catch {}

foreach ($pyExe in $pyCandidates) {
    if (-not $pyExe) { continue }
    $resolved = $null
    try { $resolved = (Resolve-Path -LiteralPath $pyExe -ErrorAction Stop).Path } catch { $resolved = $pyExe }
    if (-not $seenPython.Add($resolved.ToLowerInvariant())) { continue }
    if ($resolved.ToLowerInvariant().StartsWith($installDir.ToLowerInvariant())) { continue }
    try {
        & $resolved -m pip show clawmetry 2>&1 | Out-Null
        if ($LASTEXITCODE -eq 0) {
            Write-Host "→ Removing stale clawmetry copy from $resolved..."
            & $resolved -m pip uninstall -y clawmetry 2>&1 | Out-Null
        }
    } catch {}
}

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

# Upgrade pip (using python -m pip to avoid in-use upgrade error on Windows)
& "$installDir\Scripts\python.exe" -m pip install --upgrade pip 2>&1 | Out-Null

# Install clawmetry
Write-Host "→ Installing clawmetry from PyPI..."
& "$installDir\Scripts\pip.exe" install --no-cache-dir clawmetry 2>&1 | Out-Null
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Failed to install clawmetry." -ForegroundColor Red
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
