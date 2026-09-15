<#
.SYNOPSIS
  Silent, machine-wide ClawMetry install for multi-session / pooled Windows
  hosts (Intune Win32 app or platform script, image build, or GPO startup).

.DESCRIPTION
  Runs elevated (Intune runs platform scripts as SYSTEM). It:
    1. creates a machine-wide virtual environment under Program Files,
    2. installs the pinned ClawMetry package into it,
    3. registers ONE logon task for the built-in Users group, so every user
       who signs in gets their own collector running as themselves, reading
       only their own profile (clawmetry service install --all-users).

  Collectors do not update themselves from this administrator-owned location
  (they detect they cannot write it). Update the fleet by re-running this
  script with a new -Package pin.

  It deliberately does NOT enroll the host with ClawMetry Cloud. Enrollment
  credentials must never be baked into a shared image; see deploy/fleet/README.md
  for per-user enrollment delivered at sign-in.

  Exit codes: 0 registered, 1 failure (Intune reports the app as failed).

.PARAMETER Package
  pip requirement to install. Pin it for a fleet, e.g. "clawmetry==0.12.876",
  or pass a local wheel path.

.PARAMETER PythonExe
  Python 3.9+ interpreter used to create the environment. It must be installed
  machine-wide: the environment runs through it for every user, so one inside
  a user profile (C:\Users\...) is refused.

.PARAMETER InstallDir
  Machine-wide install location.

.EXAMPLE
  powershell.exe -ExecutionPolicy Bypass -NoProfile -File Install-ClawMetry.ps1 -Package "clawmetry==0.12.876"

.EXAMPLE
  Uninstall:
  & "$env:ProgramFiles\ClawMetry\venv\Scripts\clawmetry.exe" service uninstall
  Remove-Item -Recurse -Force "$env:ProgramFiles\ClawMetry"
#>
[CmdletBinding()]
param(
    [string]$Package = "clawmetry",
    [string]$PythonExe = "python",
    [string]$InstallDir = (Join-Path $env:ProgramFiles "ClawMetry")
)

$ErrorActionPreference = "Stop"

function Write-Step([string]$Message) { Write-Output "[clawmetry] $Message" }

try {
    $principal = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
    if (-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
        Write-Step "This script must run elevated (administrator or SYSTEM)."
        exit 1
    }

    $venv = Join-Path $InstallDir "venv"
    $venvPython = Join-Path $venv "Scripts\python.exe"
    $cli = Join-Path $venv "Scripts\clawmetry.exe"

    $basePrefix = (& $PythonExe -c "import sys; print(sys.base_prefix)" | Out-String).Trim()
    if ($LASTEXITCODE -ne 0 -or -not $basePrefix) { throw "cannot run $PythonExe" }
    $profilesRoot = Split-Path -Parent $env:PUBLIC
    if ($basePrefix.StartsWith($profilesRoot + "\", [StringComparison]::OrdinalIgnoreCase)) {
        throw "$PythonExe lives in a user profile ($basePrefix); other users could not run the collector. Use a machine-wide Python."
    }

    # Every user's collector imports code from this directory, so no desktop
    # user may write it. Program Files already ensures that, but a custom
    # -InstallDir (e.g. C:\ClawMetry) would inherit "Authenticated Users:
    # Modify" from the drive root. Set the ACL explicitly: SYSTEM and
    # Administrators full control, Users read and execute, nothing inherited.
    New-Item -ItemType Directory -Force -Path $InstallDir | Out-Null
    & icacls.exe $InstallDir /inheritance:r /grant:r "*S-1-5-18:(OI)(CI)F" "*S-1-5-32-544:(OI)(CI)F" "*S-1-5-32-545:(OI)(CI)RX" /Q | Out-Null
    if ($LASTEXITCODE -ne 0) { throw "could not restrict $InstallDir ($LASTEXITCODE)" }

    if (-not (Test-Path $venvPython)) {
        Write-Step "Creating environment at $venv"
        & $PythonExe -m venv $venv
        if ($LASTEXITCODE -ne 0) { throw "venv creation failed ($LASTEXITCODE)" }
    }

    Write-Step "Installing $Package"
    & $venvPython -m pip install --disable-pip-version-check --no-input --quiet $Package
    if ($LASTEXITCODE -ne 0) { throw "pip install failed ($LASTEXITCODE)" }

    Write-Step "Registering the per-user collector for all users"
    $result = & $cli service install --all-users --json | Out-String
    $code = $LASTEXITCODE
    Write-Output $result
    if ($code -ne 0) { throw "clawmetry service install --all-users failed ($code)" }

    Write-Step "Done. Each user's collector starts at their next sign-in."
    exit 0
}
catch {
    Write-Step "FAILED: $($_.Exception.Message)"
    exit 1
}
