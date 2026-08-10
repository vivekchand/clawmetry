"""py2app bundler for the ClawMetry macOS menubar app.

Usage:
    pip install -r desktop/requirements-dev.txt
    python desktop/setup_py2app.py py2app

Produces `dist/ClawMetry.app`. Not signed / notarized — that step is
handled in CI by `xcrun notarytool` + `codesign` once we have Apple
Developer credentials wired up (see desktop/README.md roadmap).

The resulting .app is a LSUIElement (menubar-only, no Dock icon),
matching the intended Slack-lite UX.
"""

from setuptools import setup

APP = ["tray.py"]
OPTIONS = {
    "argv_emulation": False,
    "plist": {
        "CFBundleName": "ClawMetry",
        "CFBundleDisplayName": "ClawMetry",
        "CFBundleIdentifier": "com.clawmetry.desktop",
        "CFBundleShortVersionString": "0.1.0",
        "CFBundleVersion": "0.1.0",
        # Menubar-only app, no Dock tile.
        "LSUIElement": True,
        # Auto-launch at login is opt-in via SMAppService in a later phase.
        "LSMinimumSystemVersion": "11.0",
    },
    "packages": [
        "clawmetry",
        "routes",
        "helpers",
        "flask",
        "waitress",
        "cryptography",
        "duckdb",
        "websocket",
        "PIL",
        "pystray",
    ],
    "includes": ["dashboard"],
    # DuckDB ships prebuilt binaries that py2app needs to pick up.
    "frameworks": [],
    "iconfile": None,  # add branded .icns once available
}

setup(
    app=APP,
    name="ClawMetry",
    options={"py2app": OPTIONS},
    setup_requires=["py2app"],
)
