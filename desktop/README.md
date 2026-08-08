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

Subsequent launches skip 2–3 if the venv exists and the last upgrade
is under 6 hours old, AND skip 5–6 because
`~/Library/Application Support/ClawMetry/runtime/onboarding-completed.json`
is present. Every launch, the daemon child is fresh.

**Why this shape and not "freeze clawmetry into the bundle":**

- The bundled version would drift the moment PyPI ships a new
  release. Users would see a permanent "Update available" banner
  they can't act on — because PyInstaller bundles are frozen and
  have no writable site-packages to `pip install --upgrade` into.
- The `.dmg` doesn't need to change to ship a new clawmetry.
- The user's single-download promise still holds: `open ClawMetry.dmg`
  → drag → launch → dashboard. The pip install happens once, invisibly.

The tradeoff is that first launch requires internet and a system
Python 3 (macOS/Linux ship one; on Windows it uses `py`). The shell
shows a helpful error and points at python.org if none is found.

## Files

| File | Purpose |
|------|---------|
| `app.py` | Native-window entry point. Splash → bootstrap venv → pip install/upgrade clawmetry → spawn daemon → swap to dashboard. |
| `tray.py` | Earlier menubar-only variant, retained for future "quit to menubar" polish. |
| `build_mac.spec` | PyInstaller: WKWebView, Dock icon (`ClawMetry.icns`), ATS exception for `127.0.0.1`. |
| `build_windows.spec` | PyInstaller: WebView2, `ClawMetry.ico`. |
| `build_linux.spec` | PyInstaller: GTK WebKit2. |
| `assets/` | Brand SVGs (`clawmetry-logo*.svg`), generated `ClawMetry.icns`, `ClawMetry.ico`, `clawmetry-512.png`. |
| `requirements-dev.txt` | pywebview, Pillow, PyInstaller (build-only). |
| `setup_py2app.py` | Retained for the day py2app catches up to macOS 26 Tahoe — not on the shipping path. |

## Try it locally (macOS, verified working)

```bash
pip install -r desktop/requirements-dev.txt
pyinstaller --clean --noconfirm desktop/build_mac.spec
hdiutil create -volname ClawMetry \
  -srcfolder dist/ClawMetry.app -ov -format UDZO \
  dist/ClawMetry.dmg
open dist/ClawMetry.dmg
```

Drag `ClawMetry.app` into `/Applications`, launch it, and watch the
runtime bootstrap in ~10 seconds on first launch. Subsequent launches
are near-instant.

Windows and Linux use the sibling specs. Cross-compiling from macOS
is not supported — those builds happen in
[`.github/workflows/desktop-artifacts.yml`](../.github/workflows/desktop-artifacts.yml)
on push of a `v*.*.*` tag or manual dispatch.

### Stable download URLs

Each build job also copies its artifact to a fixed, version-less
filename (`ClawMetry-mac.dmg`, `ClawMetry-windows.zip`,
`clawmetry-linux.tar.gz`) alongside the version-suffixed one, both
uploaded to the same GitHub Release. That makes
`https://github.com/vivekchand/clawmetry/releases/latest/download/<fixed-name>`
a URL that always resolves to the current release with no version
bookkeeping anywhere else — clawmetry-landing's `/download/<os>`
routes (see that repo's `app.py`) redirect straight to these.

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

## Roadmap

- Native app menu (Cmd-Q / Cmd-W / About, Preferences).
- macOS signing + notarization (Apple Developer ID, `notarytool`).
- Windows EV code-signing cert → SmartScreen clean.
- Linux AppImage / `.deb` / `.rpm` wrappers around the PyInstaller
  single-folder distribution.
- **Bundle-mode "Update now"** — currently the pip-install click in
  the dashboard's update banner does upgrade the runtime venv (because
  the daemon's `sys.executable` is the venv's Python), but the user
  has to quit and relaunch to pick it up. A nicer UX would restart
  the daemon automatically after upgrade.
- Bundle `uv` instead of relying on system Python — removes the
  "install python.org first" fallback path on Windows.
- Optional "quit to menubar" mode by merging `tray.py`'s icon into
  the main app.
