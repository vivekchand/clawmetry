# PyInstaller spec for the ClawMetry Windows desktop app (thin shell).
#
# Usage (from repo root, on Windows):
#     pip install -r desktop/requirements-dev.txt
#     pyinstaller --clean --noconfirm desktop/build_windows.spec
#
# Produces `dist/ClawMetry/ClawMetry.exe` — a native Edge WebView2
# desktop app. Code-signing with an EV cert is a separate CI step.
#
# THIN SHELL. Does NOT bundle clawmetry / dashboard / routes /
# helpers. app.py's supervisor creates a runtime venv under
# %LOCALAPPDATA%/ClawMetry/runtime/ on first launch and
# pip-install/upgrades clawmetry into it, so users always run the
# latest PyPI release without redownloading the installer.

# -*- mode: python ; coding: utf-8 -*-
import os
from PyInstaller.utils.hooks import collect_all

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(SPEC), '..'))
ASSETS_SRC = os.path.join(REPO_ROOT, 'desktop', 'assets')

block_cipher = None

webview_datas, webview_binaries, webview_hidden = collect_all('webview')

brand_datas = [
    (os.path.join(ASSETS_SRC, 'clawmetry-logo-horizontal-darkbg.svg'),
     'desktop/assets'),
    (os.path.join(ASSETS_SRC, 'clawmetry-logo.svg'),
     'desktop/assets'),
    (os.path.join(ASSETS_SRC, 'ClawMetry.ico'),
     'desktop/assets'),
]

extra_hidden = [
    'PIL',
    'webview',
    'webview.platforms.edgechromium',
    'webview.platforms.mshtml',
]

a = Analysis(
    [os.path.join(REPO_ROOT, 'desktop', 'app.py')],
    pathex=[os.path.join(REPO_ROOT, 'desktop')],
    binaries=webview_binaries,
    datas=webview_datas + brand_datas,
    hiddenimports=webview_hidden + extra_hidden,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'clawmetry', 'dashboard', 'routes', 'helpers',
        'flask', 'waitress', 'duckdb', 'cryptography',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
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
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=os.path.join(ASSETS_SRC, 'ClawMetry.ico'),
)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='ClawMetry',
)
