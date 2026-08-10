# ClawMetry Desktop

Ships ClawMetry as a **standalone desktop application** — a
double-clickable `.dmg` / `.exe` / `.deb`, with a native window
rendering the dashboard the same way Cursor / Claude Desktop /
ChatGPT Desktop do. No `pip install` for end users, no browser tab,
no curl-piped installer.

## Architecture — thin shell, pip-managed clawmetry

The bundle is intentionally **tiny (~17 MB on macOS)** and ships
only three things: the pywebview shell, a Python interpreter, and the
brand assets. **It does NOT ship the `clawmetry` package.**

On every launch the shell manages a private runtime venv:

```
~/Library/Application Support/ClawMetry/runtime/    (macOS)
%LOCALAPPDATA%/ClawMetry/runtime/                   (Windows)
$XDG_DATA_HOME/ClawMetry/runtime/                   (Linux)

runtime/
  venv/                 ← created on first launch (python -m venv)
    bin/clawmetry       ← spawned as the daemon child
  last-upgrade.json     ← timestamp of last pip check
  bootstrap.log         ← create/upgrade logs
```

Sequence on first launch (~15 seconds on a fast connection):

1. Cross-sell **carousel** appears (Ubuntu-installer style) with a top-bar
   status line: *"Preparing runtime"*
2. `/usr/bin/python3 -m venv runtime/venv/`
3. Status line updates: *"Installing ClawMetry from PyPI"*
4. `runtime/venv/bin/python -m pip install --upgrade clawmetry`
5. **Auth pane** swaps in (`desktop/onboarding.py::render_auth_pane`):
   headline personalised with any paid runtimes detected on this machine,
   three buttons — GitHub / Google / Email OTP. User signs in (OAuth
   goes out via system browser + loopback callback, OTP is in-window)
   or clicks *"Skip for now"*.
6. If a `cm_` key was captured: `runtime/venv/bin/clawmetry connect
   --key cm_… --start-sync-now` — this validates the key, saves config,
   calls `auto_provision_pro` (Pro wheel downloads iff Trial/Starter/
   Pro/Enterprise entitled), and starts the sync daemon.
7. Status line: *"Starting local daemon"*, spawn
   `runtime/venv/bin/clawmetry --no-debug --port <free>`
8. **Ready-gate spinner** appears while the shell polls
   `/api/overview` from Python (avoids CORS from a `load_html` origin);
   swaps to the real dashboard when there's content OR after 20s.

Subsequent launches skip 2–4 entirely whenever the venv already holds
a runnable clawmetry — the shell **never blocks launch on pip**. The
watcher thread owns the 6h upgrade cadence in the background and
restarts the daemon on version drift, so users still track PyPI
releases without ever staring at a "Checking for updates" splash.
Steps 5–6 are skipped because
`~/Library/Application Support/ClawMetry/runtime/onboarding-completed.json`
is present. Every launch, the daemon child is fresh.

**Global CLI:** every boot also runs `ensure_global_cli()` off the
boot path — Windows writes `%LOCALAPPDATA%\ClawMetry\bin\clawmetry.cmd`
(a shim delegating to the venv exe, immune to venv upgrades), adds
that dir to the per-user PATH (HKCU, no admin) and broadcasts
`WM_SETTINGCHANGE`; macOS/Linux symlink `~/.local/bin/clawmetry`. So
desktop users get a working `clawmetry` in any new terminal without a
separate pip install. The NSIS uninstaller removes the shim and its
PATH entry.

**Why this shape and not "freeze clawmetry into the bundle":**

- The bundled version would drift the moment PyPI ships a new
  release. Users would see a permanent "Update available" banner
  they can't act on — because PyInstaller bundles are frozen and
  have no writable site-packages to `pip install --upgrade` into.
- The `.dmg` doesn't need to change to ship a new clawmetry.
- The user's single-download promise still holds: `open ClawMetry.dmg`
  → drag → launch → dashboard. The pip install happens once, invisibly.

The tradeoff is that first launch requires internet and a system
Python 3. That is treated as an **auto-installing dependency**, not a
user-facing prerequisite:

- **macOS / Linux** ship a usable `python3` (macOS via the OS,
  Linux via every mainstream distro).
- **Windows** — the NSIS installer (`installer/windows.nsi`,
  `-PythonRuntime` section) probes for a working interpreter and, if
  none, downloads the python.org installer and runs it silently,
  per-user, no UAC. As a second line (portable-.zip users, or the
  install-time bootstrap failed), `app.py` falls back to a silent
  `winget install Python.Python.3.12 --scope user` at first launch.
  `_bootstrap_python()` also probes
  `%LOCALAPPDATA%\Programs\Python\Python3*\python.exe` directly,
  because a just-installed Python isn't on the already-running
  process's PATH.

Only when every rung fails does the shell show the old
"install python.org 3.11+ then relaunch" guidance.

## Files

| File | Purpose |
|------|---------|
| `app.py` | Native-window entry point. Splash → bootstrap venv → pip install/upgrade clawmetry → spawn daemon → swap to dashboard. |
| `tray.py` | Earlier menubar-only variant, retained for future "quit to menubar" polish. |
| `build_mac.spec` | PyInstaller: WKWebView, Dock icon (`ClawMetry.icns`), ATS exception for `127.0.0.1`. |
| `build_windows.spec` | PyInstaller: WebView2, `ClawMetry.ico`. |
| `build_linux.spec` | PyInstaller: GTK WebKit2. |
| `installer/windows.nsi` | NSIS script wrapping `build_windows.spec`'s output into a real `.exe` installer (Start Menu + Desktop shortcuts, uninstaller, per-user install, no admin/UAC prompt). |
| `assets/` | Brand SVGs (`clawmetry-logo*.svg`), generated `ClawMetry.icns`, `ClawMetry.ico`, `clawmetry-512.png`. |
| `requirements-dev.txt` | pywebview, Pillow, PyInstaller (build-only). |
| `setup_py2app.py` | Retained for the day py2app catches up to macOS 26 Tahoe — not on the shipping path. |

## Try it locally (macOS, verified working)

```bash
pip install -r desktop/requirements-dev.txt
pyinstaller --clean --noconfirm desktop/build_mac.spec
mkdir -p dist/dmg-staging
cp -R dist/ClawMetry.app dist/dmg-staging/
ln -s /Applications dist/dmg-staging/Applications
hdiutil create -volname ClawMetry \
  -srcfolder dist/dmg-staging -ov -format UDZO \
  dist/ClawMetry.dmg
open dist/ClawMetry.dmg
```

Drag `ClawMetry.app` onto the `Applications` shortcut shown next to it
in the mounted volume, launch it, and watch the runtime bootstrap in
~10 seconds on first launch. Subsequent launches are near-instant.

Windows and Linux use the sibling specs (`build_windows.spec`,
`build_linux.spec`), wrapped into real installers by
`desktop/installer/windows.nsi` (NSIS) and an AppImage-staging step
in CI, respectively — see `## Real installers, not bare archives`
below. Cross-compiling from macOS is not supported — the Windows/Linux
builds happen in
[`.github/workflows/desktop-artifacts.yml`](../.github/workflows/desktop-artifacts.yml)
on push of a `v*.*.*` tag or manual dispatch.

## Real installers, not bare archives (FLYWHEEL.md §0b)

Each platform ships a first-class installer, not a build artifact that
happens to be downloadable:

| Platform | Artifact | What it gives the user |
|---|---|---|
| macOS | `.dmg` | Mount → drag `ClawMetry.app` onto the `Applications` shortcut in the same window → done. Signed + notarized when the Apple secrets below are set. |
| Windows | `.exe` (NSIS) | Double-click → Start Menu + Desktop shortcuts, registers in "Apps & features" with a real uninstaller. Per-user install (`%LOCALAPPDATA%\Programs\ClawMetry`), no admin/UAC prompt — matches where the runtime venv already lives. Auto-installs Python 3 (python.org, silent, per-user) when the machine has none. Authenticode-signed (installer + uninstaller + app exe) when the Windows cert secrets below are set; unsigned until then (SmartScreen warns, and Smart App Control enforce mode blocks uninstall). |
| Linux | `.AppImage` | Download, `chmod +x`, double-click or run. No root, no distro package manager, works across Ubuntu/Fedora/Arch/etc via FUSE (or `--appimage-extract-and-run` where FUSE is unavailable). |

A plain `.zip` (Windows) and `.tar.gz` (Linux) are still built and
published alongside the installers for anyone who wants a portable,
no-install copy — but the installer is the artifact the download
buttons link to.

**NSIS locally** (from repo root, after `pyinstaller --clean --noconfirm desktop/build_windows.spec` on Windows):
```
makensis /DVERSION=0.0.0-dev /DSRC_DIR=dist\ClawMetry desktop\installer\windows.nsi
```
`makensis` can also compile/validate the script's *syntax* from Linux/macOS (`apt install nsis` /
`brew install makensis`) even though the produced `.exe` obviously can't run there — useful for catching
script errors before a CI round-trip.

**AppImage locally** (from repo root, on Linux, after `pyinstaller --clean --noconfirm desktop/build_linux.spec`):
```bash
cd dist
mkdir -p ClawMetry.AppDir/usr/bin
cp -r clawmetry/. ClawMetry.AppDir/usr/bin/
printf '%s\n' '#!/bin/sh' 'HERE="$(dirname "$(readlink -f "$0")")"' 'exec "$HERE/usr/bin/clawmetry" "$@"' > ClawMetry.AppDir/AppRun
chmod +x ClawMetry.AppDir/AppRun
cp ../desktop/assets/clawmetry-512.png ClawMetry.AppDir/clawmetry.png
printf '%s\n' '[Desktop Entry]' 'Type=Application' 'Name=ClawMetry' 'Exec=AppRun' 'Icon=clawmetry' 'Categories=Development;Monitor;' 'Terminal=false' > ClawMetry.AppDir/clawmetry.desktop
curl -fsSL -o appimagetool https://github.com/AppImage/appimagetool/releases/download/continuous/appimagetool-x86_64.AppImage
chmod +x appimagetool
./appimagetool --appimage-extract-and-run ClawMetry.AppDir ClawMetry-0.0.0-dev-x86_64.AppImage
```

**Linux `gi`/PyGObject pin (read before touching `build_linux.spec` or `requirements-dev.txt`):**
pywebview's GTK backend does `import gi`. Without a `PyGObject` built specifically for the CI job's
`actions/setup-python` interpreter, PyInstaller bundles whatever `_gi.so` your build machine's *system*
python3 happens to have (e.g. apt's python3-gi, compiled for the system python3's ABI — cp312 on Ubuntu
24.04) — which the frozen binary's own cp311 interpreter cannot import at all, so it crashes on launch
before ever opening a window. This was undiscovered until 2026-08-08 (nobody had run the actual frozen
Linux binary — only the unfrozen `app.py` under Xvfb) because CI going green only proves PyInstaller *ran*,
not that the result *opens a window*. `requirements-dev.txt` pins `PyGObject==3.48.2; sys_platform ==
"linux"` (newer 3.56.3 hits a separate `TypeError: Must be number, not method` in pywebview's
`on_load_finish` against this webkit2gtk build) and the CI job's `pip install` uses `--ignore-installed`
so it always builds fresh against the job's own interpreter rather than trusting a stale "already
satisfied" check against a system package. Verify by actually launching `dist/clawmetry/clawmetry` under
Xvfb + `scrot` and looking at the screenshot — a clean exit code proves nothing per FLYWHEEL.md §0b.5.

### Stable download URLs

Each build job also copies its artifact to a fixed, version-less
filename alongside the version-suffixed one, both uploaded to the same
GitHub Release:

| Platform | Installer (stable name) | Portable fallback (stable name) |
|---|---|---|
| macOS | `ClawMetry-mac.dmg` | *(the `.dmg` IS the only artifact)* |
| Windows | `ClawMetry-windows-setup.exe` | `ClawMetry-windows.zip` |
| Linux | `clawmetry-linux.AppImage` | `clawmetry-linux.tar.gz` |

That makes `https://github.com/vivekchand/clawmetry/releases/latest/download/<fixed-name>`
a URL that always resolves to the current release with no version
bookkeeping anywhere else — clawmetry-landing's `/download/<os>`
routes (see that repo's `app.py`) redirect straight to the installer
name for each platform.

## Regenerating icons

The generated `.icns` / `.ico` / PNG are committed so CI doesn't need
image tooling. To regenerate from the source SVGs:

```bash
brew install librsvg imagemagick    # macOS
# then, from desktop/assets/:
for pair in "16 icon_16x16.png" "32 icon_16x16@2x.png" "32 icon_32x32.png" \
            "64 icon_32x32@2x.png" "128 icon_128x128.png" "256 icon_128x128@2x.png" \
            "256 icon_256x256.png" "512 icon_256x256@2x.png" "512 icon_512x512.png" \
            "1024 icon_512x512@2x.png"; do
  sz=${pair%% *}; name=${pair##* }
  rsvg-convert -w "$sz" -h "$sz" clawmetry-logo.svg -o "ClawMetry.iconset/$name"
done
iconutil --convert icns ClawMetry.iconset --output ClawMetry.icns
magick clawmetry-logo.svg -density 300 -background none \
  -define icon:auto-resize=16,32,48,64,128,256 ClawMetry.ico
rsvg-convert -w 512 -h 512 clawmetry-logo.svg -o clawmetry-512.png
```

## Sharp edges (kept for future maintainers)

1. **py2app 0.28.x is broken on macOS 26 Tahoe** — false-positive
   "macOS 26 (2603) or later required". PyInstaller is the shipping
   path on all three OSes.
2. **Flask's Werkzeug debug reloader breaks the frozen bundle** —
   inside PyInstaller, the reloader re-execs `sys.executable`. Always
   pass `--no-debug` when spawning clawmetry (waitress path). The
   `app.py` supervisor already does this.
3. **WKWebView needs an ATS exception for `http://127.0.0.1`** — the
   mac spec's plist sets `NSAppTransportSecurity.NSAllowsLocalNetworking
   = True`. Without this the WebView refuses to load the dashboard.
4. **PyInstaller silently leaks REPO_ROOT onto its sys.path** — when
   the spec lives under `desktop/` and `dashboard.py` sits at repo
   root, PyInstaller finds the local one instead of the venv's. The
   spec's `excludes=['clawmetry','dashboard','routes','helpers',…]`
   is a hard belt-and-braces guard so the bundle stays clean even if
   REPO_ROOT does leak in.

## Signing + notarization (macOS)

**One-time setup in the Apple Developer portal** (you already have
InstaLabs LLC, team `8LVH596RA5`):

1. **Certificates → Create a new "Developer ID Application" cert.**
   In Keychain Access on this Mac: Certificate Assistant → Request a
   Certificate From a Certificate Authority → save the `.certSigningRequest`
   to disk. Upload it to Apple, download the issued `.cer`, double-click
   to import into your login keychain. **Do NOT pick "Apple Development"
   or "Developer ID Installer" — only "Developer ID Application" works
   for a notarized .app distributed outside the App Store.**
2. **Registering the app ID (`com.clawmetry.desktop`) is NOT required**
   for Developer ID distribution. Skip the Identifiers screen.
3. **Create an app-specific password** at
   [appleid.apple.com → Sign-In and Security → App-Specific Passwords](https://appleid.apple.com).
   Name it `clawmetry-notarytool`. Copy the 4×4 password once — Apple
   won't show it again.

**Local signing** (one-off, after `pyinstaller`):

```bash
export MACOS_SIGN_IDENTITY="Developer ID Application: InstaLabs LLC (8LVH596RA5)"
export APPLE_ID=vivek@...                        # your Apple ID email
export APPLE_TEAM_ID=8LVH596RA5
export APPLE_APP_SPECIFIC_PASSWORD=xxxx-xxxx-xxxx-xxxx
desktop/sign_mac.sh dist/ClawMetry.app
# then re-wrap the signed .app in a fresh .dmg
```

**CI signing** — add these six repo secrets in
Settings → Secrets and variables → Actions → New repository secret,
then the workflow signs + notarizes + staples every tag build:

| Secret | What to paste |
|--------|---------------|
| `MACOS_CERT_P12_BASE64` | `security find-certificate -c "Developer ID Application" -p login.keychain \| base64` — or export the cert+key from Keychain Access as `.p12` and `base64 -i cert.p12 \| pbcopy` |
| `MACOS_CERT_P12_PASSWORD` | Password you set when exporting the .p12 |
| `MACOS_SIGN_IDENTITY` | `Developer ID Application: InstaLabs LLC (8LVH596RA5)` |
| `APPLE_ID` | Your Apple ID email |
| `APPLE_TEAM_ID` | `8LVH596RA5` |
| `APPLE_APP_SPECIFIC_PASSWORD` | The 4×4 password from appleid.apple.com |

The workflow steps are `if:`-guarded on secret presence, so PRs from
forks (which can't see secrets) still build unsigned artifacts
successfully. Everything hard-codes the entitlements at
`desktop/entitlements.plist` (Hardened Runtime plus the CPython-friendly
relaxations).

## Signing (Windows / Authenticode)

The Windows CI job signs three things once the cert secrets exist, and
NO-OPs (unsigned build) until then:

1. `ClawMetry.exe` (PyInstaller output) — signed before zipping/packing,
   so both the portable `.zip` and the installer ship a signed app.
2. **The uninstaller stub** — via `!uninstfinalize` in
   `desktop/installer/windows.nsi`. This is the only place the
   uninstaller can ever be signed: `WriteUninstaller` regenerates
   `Uninstall.exe` from the stub embedded in the installer on every
   (re)install, so signing an already-installed `Uninstall.exe` would be
   undone by the next setup run.
3. `ClawMetry-Setup-<version>.exe` itself — via `!finalize`.

Why it matters beyond SmartScreen: on Windows 11 with **Smart App
Control in enforce mode**, the unsigned NSIS uninstaller's temp-copy
relaunch (`%TEMP%\Un_A.exe`) is blocked outright ("Error launching
installer"), so users cannot uninstall the app from Settings > Apps
(lab repro 2026-08-10). The Authenticode signature travels with the
temp copy, which is exactly what SAC verifies.

Repo secrets (Settings → Secrets and variables → Actions):

| Secret | What to paste |
|--------|---------------|
| `WINDOWS_CERT_PFX_BASE64` | OV/EV code-signing cert + private key exported as `.pfx`, base64-encoded (`[Convert]::ToBase64String([IO.File]::ReadAllBytes("cert.pfx"))`) |
| `WINDOWS_CERT_PASSWORD` | Password protecting the `.pfx` |

Signatures use SHA-256 with an RFC 3161 timestamp
(`http://timestamp.digicert.com`), so they stay valid after the cert
expires. CI verifies both the setup exe and `ClawMetry.exe` with
`signtool verify /pa` before uploading; a hardware-token EV cert or
Azure Trusted Signing can replace the PFX secrets later by swapping the
`sign.cmd` wrapper the workflow writes.

Note the auto-updater never rewrites the installed app or uninstaller
in place — it only pip-upgrades the runtime venv under
`%LOCALAPPDATA%\ClawMetry\runtime`. `Uninstall.exe` changes only when a
newer setup exe is run, and that setup regenerates it from its own
signed embedded stub, so updater-refreshed installs stay signed.

## Roadmap

- Native app menu (Cmd-Q / Cmd-W / About, Preferences).
- Obtain the Windows code-signing cert and set the two secrets above
  (the pipeline is wired; unsigned builds SmartScreen-warn and cannot
  be uninstalled under Smart App Control enforce mode).
- Linux `.deb` / `.rpm` wrappers alongside the AppImage, for users who
  want the app to show up in their distro's own package manager.
- **Bundle-mode "Update now"** — currently the pip-install click in
  the dashboard's update banner does upgrade the runtime venv (because
  the daemon's `sys.executable` is the venv's Python), but the user
  has to quit and relaunch to pick it up. A nicer UX would restart
  the daemon automatically after upgrade.
- Bundle `uv` instead of relying on system Python — would replace the
  NSIS/winget Python bootstrap with a fully self-contained runtime.
- Optional "quit to menubar" mode by merging `tray.py`'s icon into
  the main app.
