# ClawMetry Installer for Windows (PowerShell)
# Usage: iwr -useb https://clawmetry.com/install.ps1 | iex

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "  🦞 ClawMetry Installer" -ForegroundColor Red
Write-Host "  Real-time observability for OpenClaw agents" -ForegroundColor DarkGray
Write-Host ""

# Check for Python
$python = $null
foreach ($cmd in @("python3", "python", "py")) {
    try {
        $ver = & $cmd --version 2>&1
        if ($ver -match "Python 3\.(\d+)") {
            $minor = [int]$Matches[1]
            if ($minor -ge 10) {
                $python = $cmd
                Write-Host "  ✓ Found $ver" -ForegroundColor Green
                break
            }
        }
    } catch {}
}

if (-not $python) {
    Write-Host "  ✗ Python 3.10+ not found." -ForegroundColor Red
    Write-Host "  Install Python from https://python.org/downloads" -ForegroundColor Yellow
    Write-Host ""
    exit 1
}

# Install clawmetry
Write-Host "  → Installing clawmetry..." -ForegroundColor Cyan
& $python -m pip install --upgrade clawmetry 2>&1 | Out-Null
if ($LASTEXITCODE -ne 0) {
    & $python -m pip install --user --upgrade clawmetry 2>&1 | Out-Null
}

# Verify
try {
    $ver = & $python -m pip show clawmetry 2>&1 | Select-String "Version:"
    Write-Host "  ✓ Installed clawmetry $($ver -replace 'Version: ', '')" -ForegroundColor Green
} catch {
    Write-Host "  ✗ Installation failed. Try: pip install clawmetry" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "  Ready! Run 'clawmetry' to start the dashboard." -ForegroundColor Green
Write-Host "  Then open http://localhost:8900 in your browser." -ForegroundColor DarkGray
Write-Host ""
