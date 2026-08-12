"""macOS "app-vanished" watchdog.

macOS has no OS-level uninstall hook — dragging ``/Applications/ClawMetry.app``
to the Trash removes the app bundle but leaves the runtime venv, the cloud
sign-in token, and the DuckDB event history on disk. On the next install the
daemon reads the leftover token and silently signs the user back in, which
reads as "uninstall didn't work" (support thread 2026-08-12).

This module installs a LaunchAgent that polls every ``INTERVAL_SECS`` and,
when the .app is missing but the runtime dir is present, invokes
``clawmetry uninstall --unattended``. That command removes the runtime dir
AND unloads this very plist (its step 1 sweeps every
``~/Library/LaunchAgents/com.clawmetry.*.plist``), so the watchdog is
self-cleaning.

The watchdog is macOS-only. On Windows the MSI/uninstaller flow already
runs a proper uninstall hook; on Linux there is no "drag to Trash" surface
to fix. Callers on other platforms get a silent no-op.

Called from ``desktop/app.py::_boot`` on every launch, so the plist stays
in sync with the runtime path (which can move if the user switches homes
or the OS Application Support path changes across major macOS versions).
"""

from __future__ import annotations

import os
import platform
import subprocess
import sys
from pathlib import Path
from typing import Optional

LABEL = "com.clawmetry.app-watchdog"
INTERVAL_SECS = 300  # 5 minutes — small enough to feel immediate, big
# enough that launchd doesn't complain about churn.
DEFAULT_APP_PATH = "/Applications/ClawMetry.app"


def _plist_path() -> Path:
    return Path.home() / "Library" / "LaunchAgents" / f"{LABEL}.plist"


def _running_from_bundle() -> Optional[Path]:
    """Return the path to the enclosing ``.app`` bundle if this process
    was launched from one, else None. Used to (a) skip watchdog install
    in dev (running ``python desktop/app.py`` shouldn't drop a plist)
    and (b) prefer the actual bundle path over the ``/Applications``
    default when the user installed to a non-standard location."""
    # PyInstaller / py2app set sys.frozen. dev mode: no bundle.
    if not getattr(sys, "frozen", False):
        return None
    # sys.executable inside a .app is
    # /Applications/ClawMetry.app/Contents/MacOS/ClawMetry. Walk up to
    # the .app boundary.
    exe = Path(sys.executable).resolve()
    for p in [exe, *exe.parents]:
        if p.suffix == ".app":
            return p
    return None


def _render_plist(
    *,
    app_path: Path,
    runtime_dir: Path,
    venv_clawmetry: Path,
    interval_secs: int = INTERVAL_SECS,
) -> str:
    """Build the LaunchAgent XML. The shell command is idempotent — safe
    to re-run every interval. Two guards keep it from doing anything
    surprising:

      * ``[ ! -e "$APP" ]`` — the .app is gone (either uninstalled OR
        moved, both cases we want to wipe).
      * ``[ -x "$CLI" ]`` — the runtime venv's clawmetry binary is
        present and runnable. Prevents a partial-install state from
        firing the uninstall again after we already ran it.
    """
    # Quote each path for a POSIX shell double-quoted context. The paths
    # come from Python's Path objects and can contain spaces
    # (``Application Support``) but not double-quotes on any sane macOS
    # setup, so a simple str() is safe.
    app = str(app_path)
    cli = str(venv_clawmetry)
    marker = str(runtime_dir)
    # Two-layer teardown so this still works when the venv is half-broken:
    #   1. Preferred path — ``clawmetry uninstall --unattended`` in the
    #      runtime venv. Gets the full teardown (server-side unregister,
    #      NemoClaw sandboxes, symlinks, launchd plists).
    #   2. Fallback — if the CLI is missing or non-executable (partial
    #      pip install / half-deleted venv), a small shell block does
    #      the minimum wipe: cloud token, runtime dir, OpenClaw sidecar
    #      files, and the LaunchAgent itself. Without this the user's
    #      reported bug (drag-to-trash → auto-login on reinstall) can
    #      persist even after the watchdog fires.
    fallback = (
        'rm -f "$HOME/.openclaw/clawmetry.db"* '
        '"$HOME/.openclaw/clawmetry-alerts.json" '
        '"$HOME/.openclaw/workspace/.clawmetry-fleet.db"* '
        '"$HOME/.openclaw/workspace/.clawmetry-metrics.json"; '
        'rm -rf "$HOME/.openclaw/.clawmetry"; '
        # Strip clawmetry key from openclaw.json — python is the safe way,
        # /usr/bin/python3 ships with macOS Big Sur+.
        '/usr/bin/python3 -c \'import json,os,sys\n'
        'p=os.path.expanduser("~/.openclaw/openclaw.json")\n'
        'try:\n'
        '  d=json.load(open(p))\n'
        '  if isinstance(d,dict) and "clawmetry" in d:\n'
        '    del d["clawmetry"]\n'
        '    if d: json.dump(d,open(p,"w"),indent=2)\n'
        '    else: os.unlink(p)\n'
        'except Exception: pass\' 2>/dev/null; '
        'rm -rf "$MARKER"; '
        f'launchctl bootout "gui/$(id -u)/{LABEL}" 2>/dev/null; '
        f'rm -f "$HOME/Library/LaunchAgents/{LABEL}.plist"'
    )
    cmd = (
        f'APP="{app}"; CLI="{cli}"; MARKER="{marker}"; '
        f'if [ ! -e "$APP" ] && [ -e "$MARKER" ]; then '
        f'  if [ -x "$CLI" ]; then '
        f'    "$CLI" uninstall --unattended; '
        f'  else '
        f'    {fallback}; '
        f'  fi; '
        f'fi'
    )
    # The shell command sits inside <string>…</string>. It contains `&&`,
    # which is a bare ampersand as far as XML is concerned. Escape the
    # five predefined XML entities so plutil / plist parsers accept us.
    from xml.sax.saxutils import escape as _xml_escape
    cmd_xml = _xml_escape(cmd, {'"': "&quot;", "'": "&apos;"})
    stdout_log = str(runtime_dir / "watchdog.log")
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>{LABEL}</string>
  <key>ProgramArguments</key>
  <array>
    <string>/bin/sh</string>
    <string>-c</string>
    <string>{cmd_xml}</string>
  </array>
  <key>RunAtLoad</key>
  <true/>
  <key>StartInterval</key>
  <integer>{interval_secs}</integer>
  <key>StandardOutPath</key>
  <string>{stdout_log}</string>
  <key>StandardErrorPath</key>
  <string>{stdout_log}</string>
</dict>
</plist>
"""


def ensure_app_watchdog_installed(
    *,
    runtime_dir: Path,
    venv_clawmetry: Path,
    force: bool = False,
) -> bool:
    """Install (or refresh) the app-vanished watchdog LaunchAgent.

    Idempotent — safe to call on every desktop launch. Returns True if
    the plist ended up on disk and loaded, False if we skipped (dev
    mode, non-macOS, or launchd rejected the load).

    Args:
        runtime_dir: the desktop shell's runtime dir. Its presence is
            the "did the app leave data behind" marker the watchdog
            script tests.
        venv_clawmetry: absolute path to the ``clawmetry`` binary in
            the runtime venv. The watchdog invokes this on trigger.
        force: refresh even if the plist already matches — useful in
            tests. Under normal launch we only rewrite on content drift.
    """
    if platform.system() != "Darwin":
        return False

    bundle = _running_from_bundle()
    if bundle is None:
        # Dev mode. Never drop a LaunchAgent from `python desktop/app.py`
        # — it would keep pointing at the developer's checkout after they
        # move on to something else.
        return False

    # Prefer the actual bundle path we booted from. If the user installed
    # to a non-standard location (~/Applications, /Applications/Utilities/,
    # a Homebrew Cask, etc.) the watchdog should watch THAT path, not the
    # canonical /Applications one, or it will misfire every 5 minutes.
    app_path = bundle if bundle.exists() else Path(DEFAULT_APP_PATH)

    plist_path = _plist_path()
    new_xml = _render_plist(
        app_path=app_path,
        runtime_dir=runtime_dir,
        venv_clawmetry=venv_clawmetry,
    )
    old_xml = ""
    if plist_path.exists():
        try:
            old_xml = plist_path.read_text()
        except OSError:
            old_xml = ""
    if old_xml == new_xml and not force:
        # Already installed with correct contents. Assume launchd still
        # has it loaded — a cold boot would have re-loaded it via the
        # ~/Library/LaunchAgents autoload.
        return True

    plist_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        plist_path.write_text(new_xml)
    except OSError:
        return False

    # Reload the plist so launchd picks up the new contents. bootout+bootstrap
    # is the current-generation API; unload+load is the pre-Big Sur fallback.
    uid = os.getuid()
    target = f"gui/{uid}"
    subprocess.run(
        ["launchctl", "bootout", f"{target}/{LABEL}"],
        check=False, capture_output=True,
    )
    r = subprocess.run(
        ["launchctl", "bootstrap", target, str(plist_path)],
        check=False, capture_output=True,
    )
    if r.returncode != 0:
        # Older macOS (pre-10.11). load handles the register+start pair.
        subprocess.run(
            ["launchctl", "load", str(plist_path)],
            check=False, capture_output=True,
        )
    return True
