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
# Operator data (config.json, the DuckDB store, sync state) lives OUTSIDE the
# venv, in the home directory, and must survive every upgrade.
$dataDir = "$env:USERPROFILE\.clawmetry"

# ── Pre-flight: stop a running install before touching its files ─────────
# Windows locks the files of a running process. Re-running this installer on a
# machine where the sync daemon is live (the common case: this script is also
# the upgrade path) fails on "file in use" the moment pip or Remove-Item tries
# to replace `python.exe`/a loaded `.pyd`. Stop the scheduled task and any
# leftover clawmetry process first, remember that it WAS running, and start it
# again once the new code is in place.
$cmTaskName = "ClawMetrySyncDaemon"
$cmTaskRegistered = $false
try {
    & schtasks /query /tn $cmTaskName 2>&1 | Out-Null
    $cmTaskRegistered = ($LASTEXITCODE -eq 0)
} catch {}

# Only ClawMetry's OWN processes are stopped: the sync daemon, and anything
# running out of the install dir whose files this upgrade replaces. A python
# script of the operator's that merely imports clawmetry is left alone.
$cmDaemonWasRunning = $false
$cmOtherStopped = 0
$cmProcs = @()
try {
    $cmProcs = @(Get-CimInstance Win32_Process -ErrorAction SilentlyContinue | Where-Object {
        $_.CommandLine -and $_.ProcessId -ne $PID -and (
            $_.CommandLine -match "clawmetry\.sync" -or
            $_.CommandLine -like "*$installDir*"
        )
    })
} catch { $cmProcs = @() }

foreach ($proc in $cmProcs) {
    if ($proc.CommandLine -match "clawmetry\.sync") { $cmDaemonWasRunning = $true }
    else { $cmOtherStopped++ }
}

if ($cmProcs.Count -gt 0) {
    Write-Host "→ Stopping $($cmProcs.Count) running ClawMetry process(es) so the upgrade can replace their files..."
    if ($cmTaskRegistered -and $cmDaemonWasRunning) {
        try { & schtasks /end /tn $cmTaskName 2>&1 | Out-Null } catch {}
    }
    foreach ($proc in $cmProcs) {
        try { Stop-Process -Id $proc.ProcessId -Force -ErrorAction SilentlyContinue } catch {}
    }
    Start-Sleep -Seconds 1
}

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

# Upgrade the existing venv in place; only rebuild when there isn't a usable
# one. Wiping it on every run threw away a working environment (and, with a
# live daemon, failed outright on locked files) for no benefit -- pip upgrades
# the distribution just fine.
$venvPython = "$installDir\Scripts\python.exe"
if ((Test-Path $venvPython) -and (Test-Path "$installDir\pyvenv.cfg")) {
    Write-Host "→ Upgrading the existing install at $installDir..."
} else {
    if (Test-Path $installDir) {
        Write-Host "→ Removing previous (incomplete) installation..."
        try {
            Remove-Item -Recurse -Force $installDir -ErrorAction Stop
        } catch {
            Write-Host "❌ Could not remove $installDir (a ClawMetry process may still be running)." -ForegroundColor Red
            Write-Host "   Close it and re-run this installer." -ForegroundColor Red
            exit 1
        }
    }
    # Create venv
    Write-Host "→ Creating virtual environment at $installDir..."
    & $python -m venv $installDir
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Failed to create virtual environment." -ForegroundColor Red
        exit 1
    }
}

# Upgrade pip (using python -m pip to avoid in-use upgrade error on Windows)
& $venvPython -m pip install --upgrade pip 2>&1 | Out-Null

# Install/upgrade clawmetry (python -m pip, so a running pip.exe can't lock it)
Write-Host "→ Installing clawmetry from PyPI..."
& $venvPython -m pip install --no-cache-dir --upgrade clawmetry 2>&1 | Out-Null
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

# Restart the daemon we stopped in the pre-flight so it runs the NEW code.
# (A daemon left down after an upgrade is the "my node went quiet after
# updating" bug; a daemon left up is running the version we just replaced.)
if ($cmDaemonWasRunning) {
    Write-Host "→ Restarting the ClawMetry daemon..."
    if ($cmTaskRegistered) {
        try { & schtasks /run /tn $cmTaskName 2>&1 | Out-Null } catch {}
    } else {
        try {
            Start-Process -FilePath $venvPython -ArgumentList "-m", "clawmetry.sync" -WindowStyle Hidden | Out-Null
        } catch {}
    }
}

# Get version
$version = "installed"
try {
    $version = & "$binDir\clawmetry.exe" --version 2>&1
} catch {}

if ($cmOtherStopped -gt 0) {
    Write-Host "→ Your dashboard was stopped for the upgrade. Start it again with: clawmetry"
}

Write-Host ""
Write-Host "✅ Clawmetry installed successfully!" -ForegroundColor Green
Write-Host ""
Write-Host "  Version: $version"
if ($workspace) {
    Write-Host "  OpenClaw workspace detected: $workspace"
}
Write-Host ""

# >>> CM_EXISTING_SETUP_BLOCK_START (tests source everything between these
# sentinels; keep them around the helpers) >>>
# ── Existing setup: account probe + "re-onboard?" gate ──────────────────
# Re-running this installer on a machine that is ALREADY set up used to say
# nothing about the setup already on disk. It is also the upgrade path, so on
# a connected machine the useful thing to do is report what this node is
# linked to and offer the setup wizard, not replay it blind. A machine with NO
# account linked goes straight into `clawmetry onboard`, same as macOS/Linux.
#
# Mirrors the block of the same name in install.sh; keep the two in step.

function Get-ClawmetryTierLabel {
    param([string]$Tier)
    switch (($Tier + "").Trim().ToLowerInvariant()) {
        ""                { return "" }
        "oss"             { return "OSS" }
        "cloud_free"      { return "Free" }
        "free"            { return "Free" }
        "trial"           { return "Trial" }
        "cloud_starter"   { return "Starter" }
        "cloud_pro"       { return "Pro" }
        "pro"             { return "Self-hosted Pro" }
        "enterprise"      { return "Enterprise" }
        default           { return (Get-Culture).TextInfo.ToTitleCase($Tier.Replace("cloud_", "").Replace("_", " ")) }
    }
}

# Never promise a dashboard URL that nothing answers on, and never guess the
# port: the daemon records the live one in server.json. Any HTTP answer --
# including 401/302 -- counts as "up".
function Get-ClawmetryDashboardUrl {
    param([string]$DataDir)
    $ports = @()
    try {
        $srv = Join-Path $DataDir "server.json"
        if (Test-Path $srv) {
            $port = (Get-Content -Raw $srv | ConvertFrom-Json).port
            if ($port) { $ports += [int]$port }
        }
    } catch {}
    if ($ports -notcontains 8900) { $ports += 8900 }
    foreach ($port in $ports) {
        try {
            Invoke-WebRequest -Uri "http://127.0.0.1:$port/" -TimeoutSec 2 -UseBasicParsing | Out-Null
            return "http://localhost:$port"
        } catch {
            if ($_.Exception.Response) { return "http://localhost:$port" }
        }
    }
    return ""
}

# Prefers the installed CLI's `status --json` (authoritative: it resolves the
# live account email/plan and honours every local-only signal) and falls back
# to the config files on disk. Never throws: every broken corner degrades to
# "not connected", which just runs the wizard as before.
function Get-ClawmetryExistingSetup {
    param([string]$ClawmetryExe, [string]$DataDir)

    $setup = [ordered]@{
        Connected = $false; Email = ""; Plan = ""; Sync = "cloud"
        Node = ""; Version = ""; E2E = $false; Dashboard = ""
    }

    $snap = $null
    try {
        if (Test-Path $ClawmetryExe) {
            $raw = (& $ClawmetryExe status --json 2>$null | Out-String)
            if ($raw.Trim()) { $snap = $raw | ConvertFrom-Json }
        }
    } catch {}

    $cfg = $null
    try {
        $cfgPath = Join-Path $DataDir "config.json"
        if (Test-Path $cfgPath) { $cfg = Get-Content -Raw $cfgPath | ConvertFrom-Json }
    } catch {}

    $cloud = $null
    $acct = $null
    if ($snap) { $cloud = $snap.cloud_sync }
    if ($cloud) { $acct = $cloud.account }

    $apiKey = ""
    if ($cfg -and $cfg.api_key) { $apiKey = [string]$cfg.api_key }
    if (-not $apiKey -and $env:CLAWMETRY_API_KEY) { $apiKey = $env:CLAWMETRY_API_KEY }
    $connected = [bool]$apiKey
    if (-not $connected -and $cloud -and $cloud.api_key_masked) { $connected = $true }

    $email = ""
    if ($acct -and $acct.email) { $email = [string]$acct.email }
    elseif ($cfg -and $cfg.account_email) { $email = [string]$cfg.account_email }

    # A placeholder account (…@clawmetry.auto / …@clawmetry.linked) is the
    # daemon's zero-friction auto-registration, not the operator's login -- it
    # is invisible from their dashboard, so treat it as "not connected" and
    # let the wizard run.
    $lowered = $email.ToLowerInvariant()
    if (($acct -and $acct.placeholder) -or $lowered.EndsWith("@clawmetry.auto") -or $lowered.EndsWith("@clawmetry.linked")) {
        $connected = $false
        $email = ""
    }

    $plan = ""
    if ($acct -and $acct.plan) { $plan = [string]$acct.plan }
    if (-not $plan) {
        try {
            $planPath = Join-Path $DataDir "cloud_plan.json"
            if (Test-Path $planPath) { $plan = [string](Get-Content -Raw $planPath | ConvertFrom-Json).plan }
        } catch {}
    }

    $localOnly = $null
    if ($cloud -and $cloud.PSObject.Properties.Name -contains "local_only") { $localOnly = $cloud.local_only }
    if ($null -eq $localOnly) {
        $localOnly = $false
        if ($cfg -and $cfg.local_only) { $localOnly = $true }
        if (Test-Path (Join-Path $DataDir "nocloud")) { $localOnly = $true }
        if ($env:CLAWMETRY_NO_CLOUD -and @("1", "true", "yes", "on") -contains $env:CLAWMETRY_NO_CLOUD.ToLowerInvariant()) { $localOnly = $true }
    }

    $setup.Connected = $connected
    $setup.Email = $email
    $setup.Plan = (Get-ClawmetryTierLabel $plan)
    $setup.Sync = $(if ($localOnly) { "local-only" } else { "cloud" })
    if ($cloud -and $cloud.node_id) { $setup.Node = [string]$cloud.node_id }
    elseif ($cfg -and $cfg.node_id) { $setup.Node = [string]$cfg.node_id }
    if ($snap -and $snap.version) { $setup.Version = [string]$snap.version }
    if ($cloud -and $cloud.encryption -and $cloud.encryption.enabled) { $setup.E2E = $true }
    elseif ($cfg -and $cfg.encryption_key) { $setup.E2E = $true }
    $setup.Dashboard = (Get-ClawmetryDashboardUrl -DataDir $DataDir)
    return $setup
}

# Show the setup that is already on this machine, so the operator can tell at
# a glance which account/plan this node reports to before changing anything.
function Show-ClawmetryExistingSetup {
    param($Setup)
    Write-Host ""
    Write-Host "  ✓ You're already connected to ClawMetry" -ForegroundColor Green
    Write-Host ""
    if ($Setup.Email) {
        if ($Setup.Plan) {
            Write-Host "    Account:     $($Setup.Email)  ($($Setup.Plan) plan)"
        } else {
            Write-Host "    Account:     $($Setup.Email)"
        }
    }
    if ($Setup.Sync -eq "local-only") {
        Write-Host "    Cloud sync:  Local-only (data stays on this machine)"
    } elseif ($Setup.E2E) {
        Write-Host "    Cloud sync:  On (E2E-encrypted snapshots to app.clawmetry.com)"
    } else {
        Write-Host "    Cloud sync:  On (app.clawmetry.com)"
    }
    if ($Setup.Version) { Write-Host "    Version:     $($Setup.Version)" }
    if ($Setup.Node)    { Write-Host "    Node:        $($Setup.Node)" }
    if ($Setup.Dashboard) {
        Write-Host "    Dashboard:   $($Setup.Dashboard)"
    } else {
        Write-Host "    Dashboard:   not running (start it: clawmetry)"
    }
    Write-Host ""
}

# $true => re-run the wizard, $false => keep the current setup untouched.
# Never re-onboards without an explicit yes: a non-interactive re-install (CI,
# a provisioning script, `iex` with redirected input) keeps what is set up.
function Confirm-ClawmetryReonboard {
    if ($env:CLAWMETRY_REONBOARD) {
        $flag = $env:CLAWMETRY_REONBOARD.ToLowerInvariant()
        if (@("1", "true", "yes", "on") -contains $flag) { return $true }
        if (@("0", "false", "no", "off") -contains $flag) {
            Write-Host "  Keeping your current setup."
            Write-Host "  ↻ Change it anytime: clawmetry onboard"
            return $false
        }
    }
    $interactive = $true
    try { $interactive = (-not [Console]::IsInputRedirected) } catch {}
    if (-not $interactive) {
        Write-Host "  Non-interactive install: keeping your current setup."
        Write-Host "  ↻ Change it anytime: clawmetry onboard"
        return $false
    }
    $answer = ""
    try { $answer = Read-Host "  Re-run setup (account, cloud vs local-only, license)? [y/N]" } catch {}
    if (@("y", "yes") -contains ($answer + "").Trim().ToLowerInvariant()) { return $true }
    Write-Host ""
    Write-Host "  Keeping your current setup."
    Write-Host "  ↻ Change it anytime: clawmetry onboard"
    return $false
}

function Invoke-ClawmetryOnboard {
    param([string]$ClawmetryExe)
    try { & $ClawmetryExe onboard } catch {}
}
# <<< CM_EXISTING_SETUP_BLOCK_END <<<

# Local-only opt-out: CLAWMETRY_LOCAL_ONLY=1 means "never create a cloud
# account, nothing leaves this machine". Write the persistent marker now so it
# holds even when onboarding is skipped (onboard itself also defaults local).
if ($env:CLAWMETRY_LOCAL_ONLY -and @("1", "true", "yes", "on") -contains $env:CLAWMETRY_LOCAL_ONLY.ToLowerInvariant()) {
    try {
        New-Item -ItemType Directory -Force -Path $dataDir | Out-Null
        New-Item -ItemType File -Force -Path (Join-Path $dataDir "nocloud") | Out-Null
    } catch {}
    Write-Host "  Local-only mode (CLAWMETRY_LOCAL_ONLY set): no cloud account will be created."
}

$clawmetryExe = "$binDir\clawmetry.exe"
if ($env:CLAWMETRY_SKIP_ONBOARD -eq "1") {
    Write-Host "  Skipping onboard (CLAWMETRY_SKIP_ONBOARD=1). Set up later with: clawmetry onboard"
} else {
    $setup = Get-ClawmetryExistingSetup -ClawmetryExe $clawmetryExe -DataDir $dataDir
    if ($setup.Connected) {
        Show-ClawmetryExistingSetup -Setup $setup
        if (Confirm-ClawmetryReonboard) {
            Invoke-ClawmetryOnboard -ClawmetryExe $clawmetryExe
        }
    } else {
        Invoke-ClawmetryOnboard -ClawmetryExe $clawmetryExe
    }
}

Write-Host ""
Write-Host "  Dashboard:  clawmetry" -ForegroundColor White
Write-Host "              then open http://localhost:8900 in your browser"
Write-Host ""
Write-Host "🔭 Happy observing!" -ForegroundColor Cyan
