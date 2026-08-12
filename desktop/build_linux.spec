# PyInstaller spec for the ClawMetry Linux desktop app (thin shell).
#
# Usage (from repo root, on Linux):
#     pip install -r desktop/requirements-dev.txt
#     pyinstaller --clean --noconfirm desktop/build_linux.spec
#
# Produces `dist/clawmetry/clawmetry` — a native GTK WebKit2 desktop
# app. Wrap in AppImage / .deb / .rpm in a follow-up CI step.
#
# THIN SHELL. Does NOT bundle clawmetry / dashboard / routes /
# helpers. app.py's supervisor creates a runtime venv under
# $XDG_DATA_HOME/ClawMetry/runtime/ on first launch and
# pip-install/upgrades clawmetry into it.

# -*- mode: python ; coding: utf-8 -*-
import os
from PyInstaller.utils.hooks import collect_all

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(SPEC), '..'))
ASSETS_SRC = os.path.join(REPO_ROOT, 'desktop', 'assets')

block_cipher = None

webview_datas, webview_binaries, webview_hidden = collect_all('webview')

# certifi's cacert.pem must land inside the bundle so onboarding sign-in
# POSTs verify (support 2026-08-12). truststore is preferred at runtime
# but Python 3.10+ only.
try:
    certifi_datas, _, certifi_hidden = collect_all('certifi')
except Exception:
    certifi_datas, certifi_hidden = [], []
try:
    _, _, truststore_hidden = collect_all('truststore')
except Exception:
    truststore_hidden = []

brand_datas = [
    (os.path.join(ASSETS_SRC, 'clawmetry-logo-horizontal-darkbg.svg'),
     'desktop/assets'),
    (os.path.join(ASSETS_SRC, 'clawmetry-logo.svg'),
     'desktop/assets'),
    (os.path.join(ASSETS_SRC, 'clawmetry-512.png'),
     'desktop/assets'),
]

extra_hidden = [
    'PIL',
    'webview',
    'webview.platforms.gtk',
    'webview.platforms.qt',
    'onboarding',  # ships next to app.py; see build_mac.spec for rationale
]

a = Analysis(
    [os.path.join(REPO_ROOT, 'desktop', 'app.py')],
    pathex=[os.path.join(REPO_ROOT, 'desktop')],
    binaries=webview_binaries,
    datas=webview_datas + brand_datas + certifi_datas,
    hiddenimports=(webview_hidden + extra_hidden
                   + certifi_hidden + truststore_hidden),
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
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
    name='clawmetry',
    debug=False,
    strip=False,
    upx=True,
    console=False,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='clawmetry',
)
