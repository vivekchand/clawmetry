# PyInstaller spec for the ClawMetry macOS desktop app (thin shell).
#
# Usage (from repo root):
#     pip install -r desktop/requirements-dev.txt
#     pyinstaller --clean --noconfirm desktop/build_mac.spec
#
# Produces `dist/ClawMetry.app` — a first-class desktop app with a
# native WKWebView window (like Cursor / Claude Desktop). Dock icon
# is shown, Cmd+Tab works. Not menubar-only.
#
# THIN SHELL. This spec deliberately does NOT bundle the clawmetry
# package, dashboard.py, routes/, or helpers/. The app.py supervisor
# pip-installs clawmetry into a runtime venv under the user's app-data
# directory on first launch and pip-upgrades it on subsequent launches,
# so users always run the current PyPI release without redownloading
# the .dmg. Bundle contents = pywebview + Python interpreter + assets.

# -*- mode: python ; coding: utf-8 -*-
import os
from PyInstaller.utils.hooks import collect_all

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(SPEC), '..'))
ASSETS_SRC = os.path.join(REPO_ROOT, 'desktop', 'assets')

block_cipher = None

webview_datas, webview_binaries, webview_hidden = collect_all('webview')

# certifi's cacert.pem must land inside the bundle, or the frozen
# shell's onboarding sign-in POSTs fail CERTIFICATE_VERIFY_FAILED
# (support 2026-08-12). truststore is preferred at runtime — it uses
# the OS-native trust store — but is Python 3.10+ only, so certifi
# stays the guaranteed fallback for older bundled interpreters.
try:
    certifi_datas, _, certifi_hidden = collect_all('certifi')
except Exception:
    certifi_datas, certifi_hidden = [], []
try:
    _, _, truststore_hidden = collect_all('truststore')
except Exception:
    truststore_hidden = []

# app.py reads the horizontal-darkbg SVG from bundled assets at
# runtime (via sys._MEIPASS). The .icns is picked up by BUNDLE().
brand_datas = [
    (os.path.join(ASSETS_SRC, 'clawmetry-logo-horizontal-darkbg.svg'),
     'desktop/assets'),
    (os.path.join(ASSETS_SRC, 'clawmetry-logo.svg'),
     'desktop/assets'),
    (os.path.join(ASSETS_SRC, 'ClawMetry.icns'),
     'desktop/assets'),
]

extra_hidden = [
    'PIL',
    'webview',
    'webview.platforms.cocoa',
    # onboarding is imported from app.py via `sys.path.insert(0, .)` and
    # picked up by static analysis on macOS builds. Listed explicitly so
    # a future refactor that moves the import behind a runtime guard
    # doesn't silently drop it from the bundle.
    'onboarding',
]

a = Analysis(
    [os.path.join(REPO_ROOT, 'desktop', 'app.py')],
    # Only desktop/ on the search path. app.py has no imports of
    # clawmetry / dashboard / routes / helpers — those get installed
    # into the runtime venv on first launch.
    pathex=[os.path.join(REPO_ROOT, 'desktop')],
    binaries=webview_binaries,
    datas=webview_datas + brand_datas + certifi_datas,
    hiddenimports=(webview_hidden + extra_hidden
                   + certifi_hidden + truststore_hidden),
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Belt-and-braces: even if REPO_ROOT leaks onto sys.path via
        # some PyInstaller hook, do NOT let the local worktree's
        # dashboard.py or clawmetry package sneak into the bundle.
        # The runtime venv is the single source of truth for these.
        'clawmetry', 'dashboard', 'routes', 'helpers',
        'flask', 'waitress', 'duckdb', 'cryptography',
    ],
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='ClawMetry',
    debug=False,
    strip=False,
    upx=False,          # UPX corrupts codesigned Mach-O binaries on macOS
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='ClawMetry',
)

app = BUNDLE(
    coll,
    name='ClawMetry.app',
    icon=os.path.join(ASSETS_SRC, 'ClawMetry.icns'),
    bundle_identifier='com.clawmetry.desktop',
    info_plist={
        'CFBundleName': 'ClawMetry',
        'CFBundleDisplayName': 'ClawMetry',
        'CFBundleShortVersionString': '0.1.0',
        'CFBundleVersion': '0.1.0',
        'LSUIElement': False,
        'LSMinimumSystemVersion': '11.0',
        'NSHighResolutionCapable': True,
        # WKWebView needs an ATS exception to hit http://127.0.0.1.
        'NSAppTransportSecurity': {
            'NSAllowsLocalNetworking': True,
        },
    },
)
