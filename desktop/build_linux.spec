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
from PyInstaller.utils.hooks import collect_all, collect_submodules

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

# --- PyGObject override modules (gi/overrides/*.py) ------------------
# `gi.repository.Gtk` is not a package on disk: gi/importer.py builds
# each namespace from its typelib at import time, then layers
# PyGObject's *Python* override modules (gi/overrides/GLib.py, Gtk.py,
# …) on top. PyInstaller's static analyser cannot see those, so they
# only enter a bundle if some hook names them explicitly — and
# `gi.overrides.load_overrides()` swallows the miss by design
# (`find_spec(...) is None → return introspection_module`), leaving the
# RAW introspected API in their place with no error anywhere.
#
# That silent degradation is exactly what shipped. PyInstaller's own
# gi hook (PyInstaller/utils/hooks/gi.py) needs the `GIRepository`
# namespace to introspect anything, and PyGObject 3.52+ wants
# GIRepository-3.0.typelib, which Ubuntu 24.04 does not package (it
# ships only the girepository-1.0-era GIRepository-2.0.typelib). So
# every `hook-gi.repository.*` bailed with "Namespace GIRepository not
# available" — a WARNING, not an error — and the bundle got zero
# overrides while the build stayed green.
#
# Runtime symptom: the GLib override is `idle_add(function, *user_data)`
# while raw girepository exposes `g_idle_add_full(priority, function,
# *user_data)`. pywebview's gtk.py:430 calls
# `glib.idle_add(webview.set_opacity, 1.0)` after every page load, so
# the bound method lands in the `priority` gint slot:
# `TypeError: Must be number, not method`. The WebView never leaves
# opacity 0 — a black window plus one traceback per navigation
# (support report 2026-08-15, Ubuntu 24.04 AppImage).
#
# Naming the overrides here fixes it independently of whether the gi
# hooks can run, which is the point: the hooks degrade quietly on any
# distro missing the GIRepository typelib, so the bundle must not
# depend on them. The assert below turns a future silent regression
# back into a red build.
gi_hidden = collect_submodules('gi')
_required_overrides = {'gi.overrides.GLib', 'gi.overrides.Gtk',
                       'gi.overrides.Gdk', 'gi.overrides.Gio',
                       'gi.overrides.GObject'}
_missing = _required_overrides - set(gi_hidden)
assert not _missing, (
    'PyGObject override modules missing from the build set: '
    f'{sorted(_missing)}. Without them the frozen app gets the raw '
    'girepository API and pywebview crashes on every page load with '
    '"TypeError: Must be number, not method". Is PyGObject installed '
    'in the interpreter running PyInstaller?'
)

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
    hiddenimports=(webview_hidden + extra_hidden + gi_hidden
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
