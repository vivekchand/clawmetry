"""ClawMetry desktop app — standalone native window (thin shell).

Runs as a real desktop application (like Cursor, Claude Desktop): the
dashboard renders inside a native window backed by the OS webview
(WKWebView on macOS, WebView2 on Windows, GTK webkit2 on Linux). No
browser tab, no menubar-only helper.

**Architecture — thin shell, pip-managed clawmetry.**
The .app bundles only the pywebview shell + this supervisor. The
actual `clawmetry` package lives outside the bundle, in a private
runtime venv the shell manages. On every launch the shell runs
`pip install --upgrade clawmetry` in that venv, so the user always
gets the current PyPI release without redownloading the .dmg.

    ~/Library/Application Support/ClawMetry/runtime/          (macOS)
    %LOCALAPPDATA%/ClawMetry/runtime/                         (Windows)
    ~/.local/share/ClawMetry/runtime/                         (Linux)

    runtime/
      venv/                    ← created on first launch (python -m venv)
        bin/clawmetry          ← spawned as the daemon child
      last-upgrade.json        ← timestamp of the last pip upgrade
      bootstrap.log            ← create/upgrade logs

Threading:
    main thread   → pywebview event loop (Cocoa needs the main thread)
    worker thread → bootstrap runtime venv, pip install/upgrade
                    clawmetry, spawn the daemon, wait for Flask to
                    bind, then swap the window from splash to the
                    real dashboard
"""

from __future__ import annotations

import base64
import json
import os
import platform
import signal
import socket
import subprocess
import sys
import threading
import time
import urllib.request
from pathlib import Path
from typing import Callable, Optional

# Top-level import so PyInstaller's static analysis bundles onboarding.py
# into the .app (lazy imports inside DesktopAPI methods otherwise get
# missed by the analyser and 500 at runtime with ModuleNotFoundError).
# onboarding.py sits next to app.py in the bundle (build_mac.spec's
# pathex includes desktop/).
sys.path.insert(0, str(Path(__file__).resolve().parent))
import onboarding  # noqa: E402  (must follow sys.path insert)

APP_TITLE = "ClawMetry"
STARTUP_TIMEOUT_SECS = 45.0
POLL_INTERVAL_SECS = 0.15
SHUTDOWN_WAIT_SECS = 5.0
# Blueprint "Desktop Application Distribution" contract: poll PyPI for a
# newer clawmetry release. `_should_upgrade()` is the gate on the actual
# update call; the watcher's own tick is separate — see WATCHER_TICK_SECS.
#
# Was 6h. Lowered to 60s (founder call 2026-08-15) so a desktop user picks
# up a release within about a minute of it landing, matching the daemon's
# own update worker (routes/update_check.py, CLAWMETRY_UPDATE_CHECK_SECS,
# default 60s) instead of lagging it by up to a quarter of a day.
#
# What forced it: 0.12.707 armed the post-trial paywall, so the upgrade
# overlay became the ONLY surface a lapsed user can reach — and a layout
# bug there is a lockout, not a cosmetic defect. Shipping the fix in
# 0.12.708 and then making trapped users wait up to six hours plus a
# relaunch, with no in-app way to trigger it, is not a recovery path.
#
# Two guards landed with this, and it is worth being precise about why,
# because the obvious story is wrong. They are NOT "safe at 6h, unsafe at
# 60s" -- they were already broken at 6h.
#
# This interval is enforced ONLY through the stamp file, and the failure
# paths never wrote one. So `_should_upgrade()` stayed True after any failed
# update and the watcher retried on the very next tick: a failing update
# re-ran every WATCHER_TICK_SECS (60s) forever, whatever this constant said.
# The 6h number only ever throttled the SUCCESS path. Verified against the
# pre-change code, three consecutive failures, stamp never written.
#
# So: stamp every attempt (making the interval mean something on the failure
# path for the first time), and give the watcher's update its own shorter
# timeout so a hung PyPI cannot sit inside pip while crash-respawn waits.
# See WATCHER_UPDATE_TIMEOUT_SECS. Lowering the cadence did not create these;
# it just removed the last reason to keep tolerating them.
UPGRADE_CHECK_INTERVAL_SECS = 60
# How often the watcher thread checks for drift and crashes while the
# app is running. Short enough that clicking "Update now" in the
# dashboard translates into a visible restart within ~a minute. The
# pip-upgrade cadence is enforced by _should_upgrade(), NOT by this
# constant — do not read this as an upgrade frequency.
WATCHER_TICK_SECS = 60

# Timeout for the watcher's periodic `clawmetry update`, as distinct from
# the 300s first-install timeout in bootstrap().
#
# These two are NOT the same job. A first install has no runtime yet, must
# succeed, and may pull ~100MB on a slow link — 300s is right. A periodic
# refresh already has a working, launchable ClawMetry, so waiting five
# minutes on an unreachable PyPI buys nothing.
#
# It buys LESS than nothing here: watch() calls this synchronously, and the
# same loop is what respawns a crashed daemon. Every second spent blocked in
# pip is a second the app cannot notice its daemon died.
#
# This was never bounded by the 6h cadence, contrary to how it reads. A
# timed-out update wrote no stamp, so the next tick retried immediately --
# an unreachable PyPI meant 300s blocked, 60s tick, 300s blocked, forever,
# silently disabling crash-respawn the whole time. The 6h setting throttled
# only successful updates. 90s bounds the starvation window to ~1-2 missed
# crash checks instead of five minutes of them.
WATCHER_UPDATE_TIMEOUT_SECS = 90

BRAND_RED = "#E94644"
BRAND_BG_DARK = "#0b0e14"

# Injected after every navigation. WKWebView (macOS) and EdgeWebView2
# (Windows) silently drop `window.open(...)` and `target="_blank"`
# clicks that would need a new native window — so the Self-Host OAuth
# flow (`cloudOauth` in gw-setup.js → `window.open(oauthUrl, '_blank')`)
# never reaches a browser and the modal spins forever on
# "Finish sign-in in the new browser tab."
#
# Route absolute cross-origin https URLs through the existing
# DesktopAPI.open_external bridge (which already hands them to
# webbrowser.open); leave same-origin and relative URLs (e.g. the
# `/api/usage/export` download click) to the webview.
_OPEN_EXTERNAL_SHIM = r"""
(function(){
  if (window.__clawmetryExternalShim) return;
  window.__clawmetryExternalShim = true;
  function isExternalHttps(u) {
    try {
      var url = new URL(String(u), window.location.href);
      if (url.protocol !== 'https:') return false;
      return url.host !== window.location.host;
    } catch (e) { return false; }
  }
  function toBrowser(u) {
    try {
      if (window.pywebview && window.pywebview.api && window.pywebview.api.open_external) {
        window.pywebview.api.open_external(String(u));
        return true;
      }
    } catch (e) {}
    return false;
  }
  var _open = window.open;
  window.open = function(u, target, features) {
    if (u && isExternalHttps(u) && toBrowser(u)) return null;
    return _open.apply(window, arguments);
  };
  document.addEventListener('click', function(e){
    var a = e.target && e.target.closest ? e.target.closest('a[href]') : null;
    if (!a) return;
    var href = a.getAttribute('href') || '';
    if (!href || href.charAt(0) === '#') return;
    if (isExternalHttps(href) && toBrowser(a.href)) {
      e.preventDefault();
    }
  }, true);
})();
"""

# Written by `clawmetry connect`; presence means this node has an account
# key and the sync daemon can run.
SYNC_CONFIG_FILE = Path.home() / ".clawmetry" / "config.json"
# Written by the sync daemon's localhost query server on startup
# ({"port": N, "token": "...", "pid": M}) — our liveness probe.
SYNC_DISCOVERY_FILE = Path.home() / ".clawmetry" / "local_query.json"
# Minimum seconds between `clawmetry sync` (re)start attempts, so a
# persistently failing daemon can't turn the watcher into a spawn loop.
SYNC_START_RETRY_SECS = 300


def _auto_update_disabled() -> bool:
    """Kill-switch parse for the shell's unattended upgrades, mirroring the
    daemon's routes/update_check.py::_env_auto_update_disabled (the shell
    cannot import the venv's clawmetry package, so the semantics are
    duplicated here — keep the two in sync): an explicit truthy value
    re-arms, any explicit falsy value disables (not just the literal "0"),
    and CI environments are implicitly disabled so an ephemeral runner
    never swaps its code out mid-job."""
    val = os.environ.get("CLAWMETRY_AUTO_UPDATE", "").strip().lower()
    if val in ("1", "true", "yes", "on"):
        return False
    if val in ("0", "false", "no", "off"):
        return True
    ci = os.environ.get("CI", "").strip().lower()
    return ci not in ("", "0", "false")


def _pid_alive(pid: int) -> bool:
    """Best-effort 'is this PID a live process'. Never raises."""
    if pid <= 0:
        return False
    if os.name == "nt":
        try:
            import ctypes
            import ctypes.wintypes
            PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
            STILL_ACTIVE = 259
            h = ctypes.windll.kernel32.OpenProcess(
                PROCESS_QUERY_LIMITED_INFORMATION, False, pid
            )
            if not h:
                return False
            try:
                code = ctypes.wintypes.DWORD()
                ok = ctypes.windll.kernel32.GetExitCodeProcess(
                    h, ctypes.byref(code)
                )
                return bool(ok) and code.value == STILL_ACTIVE
            finally:
                ctypes.windll.kernel32.CloseHandle(h)
        except Exception:
            return False
    try:
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    except OSError:
        return False


def _sync_daemon_alive() -> bool:
    """True when the sync/ingest daemon is up: its discovery file names a
    live PID AND its localhost query server accepts connections. Both
    checks together survive stale files and PID reuse."""
    try:
        info = json.loads(SYNC_DISCOVERY_FILE.read_text())
        port, pid = int(info.get("port", 0)), int(info.get("pid", 0))
    except Exception:
        return False
    if not port or not _pid_alive(pid):
        return False
    try:
        with socket.create_connection(("127.0.0.1", port), timeout=1.0):
            return True
    except OSError:
        return False


def _assets_dir() -> Path:
    """Locate the desktop/assets directory in dev and frozen contexts."""
    if getattr(sys, "frozen", False):
        base = Path(getattr(sys, "_MEIPASS", os.path.dirname(sys.executable)))
        for candidate in (base / "desktop" / "assets", base / "assets"):
            if candidate.is_dir():
                return candidate
        return base
    return Path(__file__).resolve().parent / "assets"


def _brand_logo_data_uri() -> str:
    p = _assets_dir() / "clawmetry-logo-horizontal-darkbg.svg"
    try:
        b = p.read_bytes()
    except OSError:
        return ""
    return "data:image/svg+xml;base64," + base64.b64encode(b).decode()


def _splash_html(status: str = "Preparing runtime") -> str:
    logo = _brand_logo_data_uri()
    logo_block = (
        f'<img class="logo" src="{logo}" alt="ClawMetry"/>'
        if logo
        else '<div class="title">ClawMetry</div>'
    )
    safe_status = status.replace("<", "&lt;")
    return f"""
<!doctype html>
<html><head>
  <meta charset="utf-8"/>
  <title>ClawMetry</title>
  <style>
    html, body {{ margin:0; padding:0; height:100%;
      background:{BRAND_BG_DARK}; color:#e2e8f0;
      font-family:-apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }}
    .wrap {{ height:100%; display:flex; flex-direction:column;
      align-items:center; justify-content:center; gap:22px; padding:24px; }}
    .logo {{ width:min(360px, 60vw); height:auto; opacity:.98; }}
    .title {{ font-size:22px; font-weight:600; letter-spacing:.4px; }}
    .sub {{ font-size:12px; color:#94a3b8;
      display:flex; align-items:center; gap:8px; }}
    .dot {{ width:8px; height:8px; border-radius:50%;
      background:{BRAND_RED};
      box-shadow:0 0 12px {BRAND_RED}88;
      animation:pulse 1.4s ease-in-out infinite; }}
    @keyframes pulse {{ 0%,100% {{ transform:scale(.8); opacity:.5 }}
      50% {{ transform:scale(1); opacity:1 }} }}
  </style>
</head><body>
  <div class="wrap">
    {logo_block}
    <div class="sub"><span class="dot"></span>{safe_status}</div>
  </div>
</body></html>
"""


def _runtime_dir() -> Path:
    """Where the shell keeps its runtime venv + logs. Standard OS
    per-user app-data directory so nothing lives inside the .app."""
    system = platform.system()
    if system == "Darwin":
        base = Path.home() / "Library" / "Application Support" / "ClawMetry"
    elif system == "Windows":
        base = Path(os.environ.get("LOCALAPPDATA", str(Path.home()))) / "ClawMetry"
    else:
        base = Path(
            os.environ.get("XDG_DATA_HOME", str(Path.home() / ".local" / "share"))
        ) / "ClawMetry"
    d = base / "runtime"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _win_subprocess_kwargs() -> dict:
    """Extra Popen/run kwargs that stop Windows from flashing a console
    window. The desktop app is built windowed (console=False), but every
    subprocess it spawns (python.exe, pip, clawmetry.exe) is a console
    executable — without CREATE_NO_WINDOW, Windows opens a new console
    for each one, visible for the duration of the call. No-op elsewhere."""
    if platform.system() == "Windows":
        return {"creationflags": subprocess.CREATE_NO_WINDOW}  # type: ignore[attr-defined]
    return {}


def _bootstrap_python(cache_file: Optional[Path] = None) -> Optional[str]:
    """A real Python interpreter the shell can use to create a venv.
    PyInstaller's bundled interpreter can't (its `sys.executable` is
    the bundle exe and `python -m venv` mispoints), so we use the
    system Python. On macOS this is `/usr/bin/python3` (ships with the
    OS since Big Sur). On Linux, `python3` on PATH. On Windows, `py`
    or the Store Python.

    Each candidate probe spawns an interpreter (slow, worst-case ~6s
    per dud candidate), so the winner is cached in ``cache_file`` and
    revalidated with a cheap existence check on later launches."""
    if cache_file is not None:
        try:
            cached = json.loads(cache_file.read_text()).get("python", "")
            if cached and Path(cached).exists():
                return cached
        except Exception:
            pass

    candidates = ["python3", "/usr/bin/python3", "python", "py"]
    if platform.system() == "Windows":
        candidates = ["py", "python", "python3"]
    import shutil

    paths = [shutil.which(c) for c in candidates]
    if platform.system() == "Windows":
        # A Python that the NSIS installer (or the winget fallback below)
        # just put down is NOT on this process's PATH — ClawMetry.exe
        # inherited its environment before that install ran. Probe the
        # per-user python.org install location directly, newest first.
        local = Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "Python"
        paths += [
            str(p) for p in sorted(local.glob("Python3*/python.exe"), reverse=True)
        ]
    for p in paths:
        if not p:
            continue
        try:
            r = subprocess.run(
                [p, "-c", "import sys,venv,pip; print(sys.version_info[:2])"],
                capture_output=True, text=True, timeout=6,
                **_win_subprocess_kwargs(),
            )
            if r.returncode == 0:
                if cache_file is not None:
                    try:
                        cache_file.write_text(json.dumps({"python": p}))
                    except OSError:
                        pass
                return p
        except Exception:
            continue
    return None


def _winget_install_python(log: Callable[[str], None]) -> None:
    """Windows-only last resort: pull Python 3 in via winget, silently,
    per-user (no UAC). Called when no usable interpreter was found — the
    NSIS installer normally handles this at install time, but portable
    .zip users and machines where that step failed land here. Best
    effort: the caller re-probes `_bootstrap_python()` regardless of the
    outcome, because winget's exit codes are unreliable (nonzero for
    "already installed", "newer version present", etc.)."""
    import shutil

    winget = shutil.which("winget")
    if not winget:
        # The WindowsApps alias dir is occasionally missing from a
        # stripped-down PATH even though winget itself is present.
        alias = (
            Path(os.environ.get("LOCALAPPDATA", ""))
            / "Microsoft" / "WindowsApps" / "winget.exe"
        )
        if alias.exists():
            winget = str(alias)
    if not winget:
        log("winget not available; cannot auto-install python")
        return
    try:
        r = subprocess.run(
            [winget, "install", "-e", "--id", "Python.Python.3.12",
             "--scope", "user", "--silent", "--disable-interactivity",
             "--accept-package-agreements", "--accept-source-agreements"],
            capture_output=True, text=True, timeout=600,
            **_win_subprocess_kwargs(),
        )
        log(f"winget python install rc={r.returncode}")
    except Exception as e:
        log(f"winget python install failed: {e}")


class RuntimeSupervisor:
    """Owns the runtime venv, upgrade cadence, and the clawmetry child.

    Not thread-safe against concurrent start/stop; fine because the UI
    only drives it from the boot thread."""

    def __init__(self, port: int, on_status: Callable[[str], None]):
        self.port = port
        self.on_status = on_status
        self.proc: Optional[subprocess.Popen] = None
        self.runtime = _runtime_dir()
        self.venv = self.runtime / "venv"
        self.stamp_file = self.runtime / "last-upgrade.json"
        self.log_file = self.runtime / "bootstrap.log"
        # {"app_pid": ..., "daemon_pid": ..., "port": ...} of the live
        # instance — the single-instance guard and orphan cleanup key.
        self.instance_file = self.runtime / "app-instance.json"
        self._last_sync_start = 0.0
        # Set to True by main() when the user closes the window so the
        # watcher stops trying to respawn the daemon on the way out.
        self.shutting_down = threading.Event()

    def _venv_python(self) -> Path:
        return self.venv / ("Scripts" if platform.system() == "Windows" else "bin") / (
            "python.exe" if platform.system() == "Windows" else "python"
        )

    def _venv_clawmetry(self) -> Path:
        return self.venv / ("Scripts" if platform.system() == "Windows" else "bin") / (
            "clawmetry.exe" if platform.system() == "Windows" else "clawmetry"
        )

    def _log(self, line: str) -> None:
        try:
            with self.log_file.open("a") as f:
                f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} {line}\n")
        except OSError:
            pass

    def _should_upgrade(self) -> bool:
        if not self.stamp_file.exists():
            return True
        try:
            ts = json.loads(self.stamp_file.read_text()).get("ts", 0)
            return (time.time() - ts) > UPGRADE_CHECK_INTERVAL_SECS
        except Exception:
            return True

    def _mark_upgraded(self, version: Optional[str]) -> None:
        try:
            self.stamp_file.write_text(
                json.dumps({"ts": time.time(), "version": version})
            )
        except OSError:
            pass

    def _get_installed_version(self) -> Optional[str]:
        """Version of clawmetry installed in the runtime venv, read
        straight from the dist-info directory name — no interpreter
        spawn (the old subprocess probe cost ~1s per call, on the boot
        path and on every watcher tick). Falls back to the subprocess
        probe only if no dist-info is found.

        Multiple dist-infos can coexist: a pip upgrade that runs while
        the daemon holds .pyd/.exe files open half-fails its uninstall
        of the OLD version and leaves its dist-info behind (five stale
        ones observed live, 2026-08-10). Pick the highest parsed
        version, not the newest mtime — a partially-uninstalled stale
        dir can carry a fresher mtime than the real install."""
        if platform.system() == "Windows":
            sp_globs = ["Lib/site-packages"]
        else:
            sp_globs = ["lib/python*/site-packages"]

        def _ver_key(d: Path):
            v = d.name[len("clawmetry-"):-len(".dist-info")]
            try:
                return tuple(int(x) for x in v.split("."))
            except ValueError:
                return (-1,)

        try:
            infos = [
                d
                for g in sp_globs
                for d in self.venv.glob(f"{g}/clawmetry-*.dist-info")
                if d.is_dir()
            ]
            if infos:
                newest = max(infos, key=_ver_key)
                return newest.name[len("clawmetry-"):-len(".dist-info")]
        except OSError:
            pass

        py = self._venv_python()
        if not py.exists():
            return None
        try:
            r = subprocess.run(
                [str(py), "-c",
                 "import importlib.metadata as m; print(m.version('clawmetry'))"],
                capture_output=True, text=True, timeout=8,
                **_win_subprocess_kwargs(),
            )
            if r.returncode == 0:
                return r.stdout.strip()
        except Exception:
            pass
        return None

    def bootstrap(self) -> bool:
        """Create the venv if missing; pip-install clawmetry if missing.
        Idempotent. Returns True if a runnable clawmetry ends up in
        the venv; False on any hard failure.

        Warm launches never touch the network here: if the venv already
        has a runnable clawmetry we return immediately and let the
        watcher thread apply the 6h upgrade cadence in the background
        (it restarts the daemon on version drift, so users still pick
        up releases without ever staring at a "Checking for updates"
        splash)."""
        if self._venv_clawmetry().exists():
            return True

        py = _bootstrap_python(self.runtime / "bootstrap-python.json")
        if not py and platform.system() == "Windows":
            # Python is a dependency we install, not one we ask for: the
            # NSIS installer bootstraps it at install time, and this
            # covers portable-.zip users / machines where that failed.
            self.on_status("Installing Python 3 runtime (one-time, ~1 min)")
            self._log("no system python3; attempting winget auto-install")
            _winget_install_python(self._log)
            py = _bootstrap_python(self.runtime / "bootstrap-python.json")
        if not py:
            self.on_status(
                "Python 3 not found and automatic install failed. "
                "Install python.org 3.11+ then relaunch."
            )
            self._log("no system python3 available")
            return False

        if not self._venv_python().exists():
            self.on_status("Creating runtime environment")
            try:
                subprocess.run(
                    [py, "-m", "venv", str(self.venv)],
                    check=True, capture_output=True, text=True, timeout=60,
                    **_win_subprocess_kwargs(),
                )
                self._log(f"venv created via {py}")
            except subprocess.CalledProcessError as e:
                self._log(f"venv creation failed: {e.stderr}")
                self.on_status("Runtime setup failed. Check bootstrap.log.")
                return False

        self.on_status("Installing ClawMetry from PyPI")
        try:
            r = subprocess.run(
                [str(self._venv_python()), "-m", "pip", "install",
                 "--upgrade", "--disable-pip-version-check", "clawmetry"],
                capture_output=True, text=True, timeout=300,
                **_win_subprocess_kwargs(),
            )
            self._log(f"pip install rc={r.returncode}")
            if r.returncode != 0:
                self._log(r.stderr[:2000])
                self.on_status("PyPI install failed. See bootstrap.log.")
                return False
            new_version = self._get_installed_version()
            self._mark_upgraded(new_version)
            self._log(f"clawmetry now at {new_version}")
        except subprocess.TimeoutExpired:
            self._log("pip install timed out")
            self.on_status("Install timed out. Check your connection.")
            return False

        return self._venv_clawmetry().exists()

    def ensure_sync_daemon(self) -> None:
        """Local ingest is the product: without the sync daemon every
        dashboard page renders its empty state, regardless of what data
        sits on disk. Called at boot and from every watcher tick, and
        deliberately independent of cloud sign-in — `clawmetry sync`
        runs local-only ingest even when cloud sync is paused.

        No-ops when the node has never been connected (no
        ~/.clawmetry/config.json — onboarding's connect step starts sync
        itself), when the daemon is already alive, or within
        SYNC_START_RETRY_SECS of the previous attempt (a persistently
        broken daemon must not become a 60s spawn loop)."""
        if not SYNC_CONFIG_FILE.exists():
            return
        if _sync_daemon_alive():
            return
        if (time.time() - self._last_sync_start) < SYNC_START_RETRY_SECS:
            return
        self._last_sync_start = time.time()
        cli = self._venv_clawmetry()
        if not cli.exists():
            return
        try:
            r = subprocess.run(
                [str(cli), "sync"],
                capture_output=True, text=True, timeout=120,
                **_win_subprocess_kwargs(),
            )
            self._log(f"ensure_sync: clawmetry sync rc={r.returncode}")
            if r.returncode != 0:
                self._log((r.stderr or r.stdout or "")[:1000])
        except subprocess.TimeoutExpired:
            self._log("ensure_sync: clawmetry sync timed out")
        except Exception as exc:
            self._log(f"ensure_sync failed: {exc}")

    def _write_instance_file(self) -> None:
        try:
            self.instance_file.write_text(json.dumps({
                "app_pid": os.getpid(),
                "daemon_pid": self.proc.pid if self.proc else 0,
                "port": self.port,
            }))
        except OSError:
            pass

    def _clear_instance_file(self) -> None:
        try:
            self.instance_file.unlink()
        except OSError:
            pass

    def start_daemon(self) -> None:
        argv = [
            str(self._venv_clawmetry()),
            "--no-debug",
            "--port", str(self.port),
        ]
        env = os.environ.copy()
        # WERKZEUG_RUN_MAIN handled by --no-debug (waitress path).
        env.pop("PYTHONHOME", None)
        env.pop("PYTHONPATH", None)
        kwargs: dict = {
            "stdout": subprocess.DEVNULL,
            "stderr": subprocess.DEVNULL,
            "stdin": subprocess.DEVNULL,
            "env": env,
        }
        if os.name == "nt":
            # CREATE_NEW_PROCESS_GROUP lets stop() target the child alone
            # with CTRL_BREAK_EVENT; CREATE_NO_WINDOW stops it from
            # flashing a console (stdout/stderr going to DEVNULL doesn't
            # suppress the window itself — console allocation happens
            # regardless of stream redirection).
            kwargs["creationflags"] = (  # type: ignore[attr-defined]
                subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.CREATE_NO_WINDOW
            )
        else:
            kwargs["start_new_session"] = True
        self.proc = subprocess.Popen(argv, **kwargs)
        self._write_instance_file()

    def wait_ready(self, deadline_secs: float = STARTUP_TIMEOUT_SECS) -> bool:
        url = f"http://127.0.0.1:{self.port}/"
        deadline = time.time() + deadline_secs
        while time.time() < deadline:
            if self.proc and self.proc.poll() is not None:
                return False
            try:
                with urllib.request.urlopen(url, timeout=1.5) as r:
                    if 200 <= r.status < 400:
                        return True
            except Exception:
                pass
            time.sleep(POLL_INTERVAL_SECS)
        return False

    def stop(self) -> None:
        p = self.proc
        if not p:
            return
        try:
            if os.name == "nt":
                p.send_signal(signal.CTRL_BREAK_EVENT)  # type: ignore[attr-defined]
            else:
                os.killpg(os.getpgid(p.pid), signal.SIGTERM)
        except (ProcessLookupError, OSError):
            pass
        try:
            p.wait(timeout=SHUTDOWN_WAIT_SECS)
        except subprocess.TimeoutExpired:
            try:
                if os.name == "nt":
                    p.kill()
                else:
                    os.killpg(os.getpgid(p.pid), signal.SIGKILL)
            except (ProcessLookupError, OSError):
                pass
        self.proc = None
        self._clear_instance_file()

    def _get_running_daemon_version(self) -> Optional[str]:
        """Ask the CHILD daemon what version it thinks it is via its own
        /api/version endpoint. Returns None if the daemon is down or
        unreachable — which is normal during restarts."""
        try:
            with urllib.request.urlopen(
                f"http://127.0.0.1:{self.port}/api/version", timeout=1.5
            ) as r:
                return json.loads(r.read()).get("current")
        except Exception:
            return None

    def _background_pip_upgrade(self) -> None:
        """Upgrade via the venv's `clawmetry update --unattended`
        subcommand — the flag makes the CLI apply the daemon's own update
        policy (routes/update_check.py): the CLAWMETRY_AUTO_UPDATE kill
        switch (incl. implicit CI disable) and the
        CLAWMETRY_AUTOUPDATE_MIN_AGE_HOURS stability window, pinning to the
        newest aged-in release. Matches the blueprint contract "the shell
        defers to the daemon's update policy rather than shipping its own";
        the local _auto_update_disabled() check is only a cheap pre-flight
        with the same semantics. Errors are logged and swallowed — a
        transient PyPI failure should never take down the running app.

        "Background" here means off the UI thread, NOT asynchronous: the
        caller (watch()) blocks for the duration, and that same loop owns
        crash-respawn. Hence WATCHER_UPDATE_TIMEOUT_SECS rather than the
        300s first-install budget.

        Stamps the attempt on EVERY outcome, including failure. Stamping only
        successes meant a persistently failing update (offline, broken venv,
        PyPI down) re-ran on every single watcher tick forever — and that was
        already true at the OLD 6h cadence, not something the shorter interval
        introduced. UPGRADE_CHECK_INTERVAL_SECS is enforced purely through the
        stamp file, so a path that never stamps is a path with no interval at
        all; 6h only ever throttled successes. A failed attempt is still an
        attempt.
        """
        if _auto_update_disabled():
            self._log(
                "watcher upgrade: auto-update disabled "
                "(CLAWMETRY_AUTO_UPDATE kill switch or CI env), skipping"
            )
            return
        cli = self._venv_clawmetry()
        if not cli.exists():
            return
        try:
            r = subprocess.run(
                [str(cli), "update", "--unattended"],
                capture_output=True, text=True,
                timeout=WATCHER_UPDATE_TIMEOUT_SECS,
                **_win_subprocess_kwargs(),
            )
            if r.returncode != 0 and "--unattended" in (r.stderr or "") \
                    and "unrecognized arguments" in (r.stderr or ""):
                # Bootstrap compat: the venv still runs a clawmetry from
                # before the flag existed, so no unattended run can ever
                # succeed — one plain update to get onto a version that
                # understands the policy flag.
                self._log(
                    "watcher upgrade: venv clawmetry predates --unattended; "
                    "falling back to plain update once"
                )
                r = subprocess.run(
                    [str(cli), "update"],
                    capture_output=True, text=True,
                    timeout=WATCHER_UPDATE_TIMEOUT_SECS,
                    **_win_subprocess_kwargs(),
                )
            self._log(f"watcher clawmetry-update rc={r.returncode}")
            if r.returncode != 0:
                self._log(r.stderr[:2000])
            # Stamp regardless of rc: see the docstring. A failed attempt
            # still consumed an interval, and not stamping it turns the
            # 60s cadence into "retry forever, every tick".
            self._mark_upgraded(self._get_installed_version())
        except subprocess.TimeoutExpired:
            self._log("watcher clawmetry-update timed out")
            # Same reasoning, and this is the case that matters most: a
            # hanging PyPI is exactly the failure that would otherwise
            # re-enter pip on every tick and starve crash-respawn.
            self._mark_upgraded(self._get_installed_version())

    def restart_daemon(self) -> bool:
        """Stop the current daemon and spawn a fresh one on the same
        port. Returns True if the new daemon binds and answers before
        the startup timeout. Idempotent; safe to call repeatedly."""
        self.stop()
        # Give TCP TIME_WAIT a moment on the freed port; on most systems
        # SO_REUSEADDR handles this, but on macOS a bare Popen can lose.
        time.sleep(0.5)
        self.start_daemon()
        return self.wait_ready()

    def watch(self, on_restart: Callable[[], None]) -> None:
        """Blocking watcher loop, meant to run in a daemon thread.

        Every WATCHER_TICK_SECS:
          1. If the child crashed, respawn (unless shutting down).
          2. Compare the venv's installed clawmetry version to what the
             running daemon reports. If they differ (user clicked
             "Update now" in the dashboard, or any other mechanism
             upgraded the venv), restart the daemon and invoke
             on_restart() so the caller can refresh the webview.
             This is how the blueprint contract "auto-upgrade it in
             place" is actually delivered end-to-end — the pip install
             changes the venv, and this loop makes the running process
             pick it up without a manual quit-and-relaunch.
          3. If 6 hours have elapsed since the last stamped upgrade
             (`_should_upgrade()`), run a background `clawmetry update`
             so users who never quit still get PyPI releases on the
             blueprint's 6h cadence. Any resulting version change is
             caught by step 2 on the next tick.
        """
        while not self.shutting_down.is_set():
            if self.shutting_down.wait(WATCHER_TICK_SECS):
                return

            if self.proc is not None and self.proc.poll() is not None:
                self._log(f"daemon exited with code {self.proc.returncode}; respawning")
                if self.restart_daemon():
                    on_restart()
                continue

            # Heal the sync/ingest daemon too — same contract as the
            # dashboard child: the shell owns it while the app runs.
            self.ensure_sync_daemon()

            installed = self._get_installed_version()
            running = self._get_running_daemon_version()
            if installed and running and installed != running:
                self._log(
                    f"version drift: venv={installed} running={running}; restarting"
                )
                self.on_status(f"Applying update to v{installed}")
                if self.restart_daemon():
                    on_restart()
                continue

            if self._should_upgrade():
                self._log("watcher: 6h elapsed, running clawmetry update")
                self._background_pip_upgrade()


def _ensure_user_path_windows(bin_dir: str, log: Callable[[str], None]) -> None:
    """Append ``bin_dir`` to the per-user PATH (HKCU\\Environment) if it
    isn't already there, then broadcast WM_SETTINGCHANGE so newly opened
    cmd/PowerShell windows pick it up without a logoff. Per-user only —
    never touches the machine PATH, no admin rights involved."""
    import winreg

    with winreg.OpenKey(
        winreg.HKEY_CURRENT_USER, "Environment", 0,
        winreg.KEY_READ | winreg.KEY_SET_VALUE,
    ) as key:
        try:
            current, kind = winreg.QueryValueEx(key, "Path")
        except FileNotFoundError:
            current, kind = "", winreg.REG_EXPAND_SZ
        entries = [e for e in current.split(";") if e]
        if any(e.strip().lower().rstrip("\\") == bin_dir.lower().rstrip("\\")
               for e in entries):
            return
        new_value = ";".join(entries + [bin_dir])
        winreg.SetValueEx(key, "Path", 0, kind or winreg.REG_EXPAND_SZ, new_value)
        log(f"added {bin_dir} to user PATH")

    try:
        import ctypes
        HWND_BROADCAST, WM_SETTINGCHANGE, SMTO_ABORTIFHUNG = 0xFFFF, 0x1A, 0x0002
        ctypes.windll.user32.SendMessageTimeoutW(
            HWND_BROADCAST, WM_SETTINGCHANGE, 0, "Environment",
            SMTO_ABORTIFHUNG, 5000, None,
        )
    except Exception:
        pass  # PATH is set; existing shells just won't see it until reopened


def ensure_global_cli(sup: RuntimeSupervisor) -> None:
    """Make the runtime venv's `clawmetry` globally invocable, so users
    of the desktop app also get the CLI (`clawmetry` in any terminal)
    without a separate pip install.

    Windows: writes a tiny shim at %LOCALAPPDATA%\\ClawMetry\\bin\\
    clawmetry.cmd (delegates to the venv exe, so venv upgrades need no
    shim change) and adds that dir to the user PATH. macOS/Linux:
    symlinks ~/.local/bin/clawmetry at the venv binary. Idempotent,
    best-effort, and called off the boot path — a failure here must
    never break the app, so everything is logged and swallowed."""
    cli = sup._venv_clawmetry()
    if not cli.exists():
        return
    try:
        if platform.system() == "Windows":
            bin_dir = sup.runtime.parent / "bin"
            bin_dir.mkdir(parents=True, exist_ok=True)
            shim = bin_dir / "clawmetry.cmd"
            content = f'@echo off\r\n"{cli}" %*\r\n'
            if not shim.exists() or shim.read_text() != content:
                shim.write_text(content)
                sup._log(f"global CLI shim written: {shim}")
            _ensure_user_path_windows(str(bin_dir), sup._log)
        else:
            local_bin = Path.home() / ".local" / "bin"
            local_bin.mkdir(parents=True, exist_ok=True)
            link = local_bin / "clawmetry"
            if link.is_symlink() or link.exists():
                try:
                    if link.is_symlink() and os.readlink(link) == str(cli):
                        return
                    link.unlink()
                except OSError:
                    return  # something else owns that name; leave it alone
            link.symlink_to(cli)
            sup._log(f"global CLI symlink: {link} -> {cli}")
            if str(local_bin) not in os.environ.get("PATH", ""):
                sup._log(f"note: {local_bin} not on PATH in this session")
    except Exception as exc:
        sup._log(f"global CLI setup failed: {exc}")


def _find_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _dashboard_alive(port: int) -> bool:
    try:
        with urllib.request.urlopen(
            f"http://127.0.0.1:{port}/api/version", timeout=1.5
        ) as r:
            return 200 <= r.status < 400
    except Exception:
        return False


def _kill_pid_tree(pid: int) -> None:
    """Terminate a process (and its children on Windows). Used only for
    orphaned daemons we positively identified via the instance file."""
    try:
        if os.name == "nt":
            subprocess.run(
                ["taskkill", "/PID", str(pid), "/T", "/F"],
                capture_output=True, timeout=10,
                **_win_subprocess_kwargs(),
            )
        else:
            os.kill(pid, signal.SIGTERM)
    except Exception:
        pass


def _check_existing_instance(runtime: Path):
    """Single-instance guard. Reads runtime/app-instance.json and returns:

    - ("attach", port)      — another ClawMetry window is alive and its
                              daemon answers: reuse it instead of
                              stacking a second daemon.
    - ("orphan", daemon_pid) — the app that owned the daemon is gone but
                              the daemon still runs (pre-fix versions
                              leaked these on every relaunch): caller
                              kills it and boots fresh.
    - None                  — no instance / stale file: boot normally.
    """
    instance_file = runtime / "app-instance.json"
    try:
        info = json.loads(instance_file.read_text())
        app_pid = int(info.get("app_pid", 0))
        daemon_pid = int(info.get("daemon_pid", 0))
        port = int(info.get("port", 0))
    except Exception:
        return None
    if port and _dashboard_alive(port):
        if app_pid and _pid_alive(app_pid) and app_pid != os.getpid():
            return ("attach", port)
        if daemon_pid and _pid_alive(daemon_pid):
            return ("orphan", daemon_pid)
    try:
        instance_file.unlink()
    except OSError:
        pass
    return None


# ─── Boot orchestration ────────────────────────────────────────────────────────────────────
# The first-launch onboarding flow is a small state machine driven from
# a single worker thread. Phases:
#
#   1. bootstrap runtime venv + pip-install clawmetry (with the
#      Ubuntu-installer-style carousel showing progress)
#   2. if first launch AND cloud reachable: show sign-in pane and block
#      the worker thread on `_auth_done` until user completes or skips
#   3. if a cm_ key landed: run `clawmetry connect --key --start-sync-now`
#      which validates, saves config, provisions the Pro wheel (only if
#      the account is Trial/Starter/Pro/Enterprise entitled), and starts
#      the sync daemon (cloud sync is default-ON per product spec)
#   4. start the dashboard daemon on a free port
#   5. load the ready-gate splash, which polls /api/overview and swaps
#      to the real dashboard when there's content to show (capped at 20s)
#
# The DesktopAPI class below is what JS in the auth pane calls into via
# ``window.pywebview.api.*``. Each method returns a small dict the pane
# renders as inline status text.

class DesktopAPI:
    """pywebview JS bridge for the onboarding pane.

    Methods are called synchronously from JS; the pywebview runtime
    dispatches them onto a worker thread and marshals the return value
    back. They must be idempotent-safe (a page reload can double-invoke)
    and quick to return — long-running work (OAuth loopback, OTP) is
    fine because pywebview never blocks the UI thread on them."""

    def __init__(self, sup: "RuntimeSupervisor", app_base_override: Optional[str] = None):
        self._sup = sup
        self._app_base = app_base_override
        self._auth_done = threading.Event()
        self._mode_done = threading.Event()
        self._captured_key: str = ""
        self._captured_email: str = ""
        self._captured_provider: str = ""
        self._captured_mode: str = ""

    # ── OAuth (GitHub / Google) ────────────────────────────────────────────
    def start_oauth(self, provider: str) -> dict:
        provider = (provider or "").lower()
        if provider not in ("github", "google"):
            return {"ok": False, "error": "unknown provider"}
        ok, msg_or_key = onboarding.oauth_loopback_flow(
            provider, app_base=self._app_base,
        )
        if not ok:
            return {"ok": False, "error": msg_or_key}
        self._captured_key = msg_or_key
        self._captured_provider = provider
        self._auth_done.set()
        return {"ok": True}

    # ── Email OTP ───────────────────────────────────────────────────────
    def send_email_otp(self, email: str) -> dict:
        ok, msg = onboarding.send_email_otp(email, app_base=self._app_base)
        return {"ok": ok, "error": "" if ok else msg}

    def verify_email_otp(self, email: str, otp: str) -> dict:
        ok, key_or_err = onboarding.verify_email_otp(
            email, otp, app_base=self._app_base,
        )
        if not ok:
            return {"ok": False, "error": key_or_err}
        self._captured_key = key_or_err
        self._captured_email = email
        self._captured_provider = "email"
        self._auth_done.set()
        return {"ok": True}

    # ── Hosting choice (cloud vs local/self-host) ───────────────────────────
    def choose_mode(self, mode: str) -> dict:
        mode = (mode or "").lower()
        if mode not in ("cloud", "selfhost"):
            return {"ok": False, "error": "unknown mode"}
        self._captured_mode = mode
        self._mode_done.set()
        return {"ok": True}

    # ── Skip (dismiss without auth) ──────────────────────────────────────────
    def skip_auth(self) -> dict:
        # No key captured; downstream `_apply_and_boot_daemon` will
        # just skip the connect step and go straight to the dashboard.
        self._auth_done.set()
        return {"ok": True}

    # ── External links (carousel CTAs) ──────────────────────────────────────
    def open_external(self, url: str) -> dict:
        # Restrict to https:// to keep the pane from being weaponised
        # into launching arbitrary schemes if a slide is ever
        # user-editable in the future.
        if not (url or "").startswith("https://"):
            return {"ok": False, "error": "only https:// URLs are opened"}
        try:
            import webbrowser
            webbrowser.open(url)
            return {"ok": True}
        except Exception as exc:
            return {"ok": False, "error": str(exc)}


def main() -> int:
    import webview

    runtime = _runtime_dir()
    existing = _check_existing_instance(runtime)
    if existing and existing[0] == "attach":
        # Another instance owns the daemon — open a window onto it and
        # get out of the way. No supervisor, no watcher, and closing
        # this window must not stop the other instance's daemon.
        webview.create_window(
            APP_TITLE,
            url=f"http://127.0.0.1:{existing[1]}/",
            width=1280, height=820, min_size=(900, 600),
            background_color=BRAND_BG_DARK,
        )
        webview.start(private_mode=False)
        return 0
    if existing and existing[0] == "orphan":
        # Daemon outlived its app (pre-guard versions leaked one per
        # relaunch). Kill it; we boot a fresh one on a fresh port.
        _kill_pid_tree(existing[1])

    port = int(os.environ.get("CLAWMETRY_APP_PORT") or _find_free_port())
    assets = _assets_dir()

    # Open with the carousel HTML directly — no more static splash.
    # bootstrap progress messages update the top-bar via `set_status`.
    initial_html = onboarding.render_bootstrap_carousel(
        assets_dir=assets, status="Preparing runtime",
    )

    # Instantiate API + supervisor before window so we can pass js_api
    # in at create_window time (pywebview binds the API namespace on
    # window creation, not after).
    sup = RuntimeSupervisor(port, lambda _msg: None)  # placeholder; real hook set below
    api = DesktopAPI(sup)

    window = webview.create_window(
        APP_TITLE,
        html=initial_html,
        js_api=api,
        width=1280,
        height=820,
        min_size=(900, 600),
        background_color=BRAND_BG_DARK,
    )

    def _set_status(msg: str) -> None:
        """Push a progress line into the carousel's top bar. When the
        pane isn't the carousel (e.g. we've swapped to the auth pane),
        the JS call is a no-op and we swallow the exception — status
        messages are hints, not load-bearing."""
        try:
            window.evaluate_js(f"window.set_status && window.set_status({json.dumps(msg)});")
        except Exception:
            pass

    # Late-bind the real status hook now that window exists.
    sup.on_status = _set_status

    dashboard_url = f"http://127.0.0.1:{port}/"

    def _reload_window() -> None:
        """Callback the watcher fires after a successful daemon
        restart. Reloading the same URL is enough — the WebView picks
        up whatever the fresh daemon serves, so users see the new
        version immediately without having to quit and relaunch."""
        try:
            window.load_url(dashboard_url)
        except Exception:
            pass

    def _do_uninstall_flow() -> None:
        """Menu handler — confirm, then shell out to
        ``clawmetry uninstall --yes`` in the runtime venv, then quit.

        The uninstall itself removes the runtime dir the venv lives in;
        that's safe on POSIX because the venv's clawmetry binary is
        already mmap'd by the child process (unlinked files stay open
        for the running process). On Windows the uninstall reschedules
        the exe delete for after we exit.
        """
        try:
            ok = window.evaluate_js(
                "confirm('Uninstall ClawMetry?\\n\\n"
                "This removes the runtime, local event history, and your "
                "sign-in token.\\n\\n"
                "The app in /Applications is not deleted — drag it to "
                "Trash separately.')"
            )
        except Exception:
            ok = True  # If we can't render a dialog, assume the menu click
            # is intent enough. The CLI would still refuse on a bad flag.
        if not ok:
            return

        _set_status("Uninstalling ClawMetry…")
        # Stop the daemon before removing its files: on Windows a live
        # process holds an exclusive lock on its exe; on macOS/Linux the
        # rmtree still works but the sync.log deletion races.
        try:
            sup.shutting_down.set()
        except Exception:
            pass
        try:
            sup.stop()
        except Exception:
            pass

        venv_cli = sup._venv_clawmetry()
        if venv_cli.exists():
            try:
                subprocess.run(
                    [str(venv_cli), "uninstall", "--yes"],
                    check=False,
                    timeout=300,
                )
            except Exception:
                pass

        # Quit the app. The runtime dir is gone; a relaunch would re-bootstrap.
        try:
            window.destroy()
        except Exception:
            os._exit(0)

    def _on_menu_uninstall() -> None:
        # Menu callbacks run on the GUI thread; move the confirm+shell-out
        # off it so evaluate_js and subprocess don't block the main loop.
        threading.Thread(target=_do_uninstall_flow, daemon=True).start()

    # Build the menu — tolerant of pywebview versions without a menu API.
    # macOS shows this alongside the standard app menu; the item name uses
    # the platform convention "Uninstall ClawMetry…" (ellipsis = confirms).
    menu_items: list = []
    try:
        from webview.menu import Menu, MenuAction  # type: ignore
        menu_items = [
            Menu(APP_TITLE, [
                MenuAction("Uninstall ClawMetry…", _on_menu_uninstall),
            ]),
        ]
    except Exception:
        menu_items = []

    def _boot():
        # Phase 1: bootstrap the runtime venv.
        ok = sup.bootstrap()
        if not ok:
            # bootstrap() already set a status message on failure; leave
            # the carousel up with the failure text at the top so the
            # user has something to read while filing a bug.
            return

        # Install the macOS app-vanished watchdog so drag-to-trash of
        # /Applications/ClawMetry.app triggers a full uninstall without
        # the user having to open a terminal. No-op on non-macOS and in
        # dev mode (sys.frozen unset). See clawmetry/watchdog.py.
        try:
            from clawmetry.watchdog import ensure_app_watchdog_installed
            ensure_app_watchdog_installed(
                runtime_dir=sup.runtime,
                venv_clawmetry=sup._venv_clawmetry(),
            )
        except Exception:
            # Never let a watchdog install failure block launch — the
            # in-app menu and manual CLI still work without it.
            pass

        # Expose the CLI globally (PATH shim / symlink) and make sure
        # local ingest is running — both in the background, neither may
        # delay the boot sequence. ensure_sync_daemon here is what turns
        # a "connected but sync died" install (empty dashboard, banner
        # blaming the user) back into a working product without anyone
        # touching a terminal.
        threading.Thread(
            target=ensure_global_cli, args=(sup,), daemon=True
        ).start()
        threading.Thread(
            target=sup.ensure_sync_daemon, daemon=True
        ).start()

        # Phase 2: onboarding — only on the very first launch.
        runtime = sup.runtime
        show_pane = onboarding.is_first_launch(runtime)
        if show_pane:
            _set_status("Ready — please sign in")
            detected = onboarding.detect_runtimes_via_venv(sup._venv_python())
            auth_html = onboarding.render_auth_pane(
                assets_dir=assets, detected_runtimes=detected,
            )
            try:
                window.load_html(auth_html)
            except Exception:
                # Non-fatal: proceed to boot the dashboard anyway. The
                # user can sign in from the dashboard later.
                pass
            # Block on the JS bridge until the user completes or skips.
            # Cap at 5 minutes: a user who walks away shouldn't leave
            # the app stuck on the pane forever.
            api._auth_done.wait(timeout=300)

        # Phase 2b: hosting choice — only when a key was captured. Both
        # options start the same 7-day trial; this decides whether
        # E2E-encrypted snapshots leave the machine (cloud) or the sync
        # daemon runs local-only ingest (selfhost). Explicit per product
        # spec: cloud-vs-selfhost must be a user decision, not a side
        # effect of which onboarding path happened to run.
        captured_key = api._captured_key
        if captured_key:
            try:
                window.load_html(onboarding.render_mode_pane(assets_dir=assets))
            except Exception:
                pass
            # Walked away? Default to cloud — matches the product spec
            # default (cloud sync ON) and the pre-pane behavior.
            api._mode_done.wait(timeout=180)
            if not api._captured_mode:
                api._captured_mode = "cloud"

        # Phase 3: apply the cm_ key if we captured one.
        if captured_key:
            # Swap back to the carousel while the connect subprocess
            # runs — it's the more informative surface than a spinner.
            try:
                window.load_html(onboarding.render_bootstrap_carousel(
                    assets_dir=assets, status="Setting up your account",
                ))
            except Exception:
                pass
            ok_key, msg_key = onboarding.apply_cm_key(
                sup._venv_clawmetry(), captured_key,
                mode=api._captured_mode or "cloud",
            )
            if not ok_key:
                _set_status(f"Sign-in step failed ({msg_key}) — continuing without cloud sync")
            # We got here because captured_key is a real cm_ key that
            # cloud minted in this same request (verify_email_otp /
            # oauth_loopback_flow returned it). Record signed_in=True
            # and pass the chosen mode regardless of apply_cm_key's exit
            # code — the subprocess failing is a downstream setup issue
            # (daemon start, permissions, Pro-wheel network hiccup), not
            # a sign-in failure. apply_cm_key's fallback has already
            # persisted the key to ~/.openclaw so the dashboard's cloud
            # status flips to connected either way. Recording
            # signed_in=False here used to make the dashboard's
            # onboarding gate re-prompt for the SAME cloud/self-host
            # choice on every relaunch even after a "successful" OTP
            # (founder report 2026-08-12).
            onboarding.mark_onboarding_completed(
                runtime,
                signed_in=True,
                provider=api._captured_provider,
                email=api._captured_email,
                mode=api._captured_mode or "cloud",
            )
        elif show_pane:
            # User skipped — stamp so we don't re-prompt.
            onboarding.mark_onboarding_completed(
                runtime, signed_in=False, provider="", email="",
            )

        # Phase 4: start the dashboard daemon.
        _set_status("Starting local daemon")
        sup.start_daemon()
        if not sup.wait_ready():
            _set_status("Daemon did not come up. See bootstrap.log.")
            return

        # Start the watcher after wait_ready so the initial startup exit
        # is never mistaken for a crash. Handles version drift ("Update
        # now") and unexpected exits by restarting + reloading the WebView.
        threading.Thread(
            target=sup.watch, args=(_reload_window,), daemon=True
        ).start()

        # Phase 5: load the ready-gate spinner, poll /api/overview
        # from Python (avoids CORS from a load_html origin), then load
        # the real dashboard. Capped at 20s so an offline user is
        # never stuck on a spinner.
        try:
            window.load_html(onboarding.render_ready_gate())
        except Exception:
            pass  # spinner is polish, not a gate
        onboarding.wait_for_dashboard_content(port, deadline_secs=20.0)
        try:
            window.load_url(dashboard_url)
        except Exception:
            pass

    def _on_closed():
        # Stop the watcher FIRST — otherwise it sees the daemon exit
        # from our stop() call below and respawns it while we're
        # trying to quit.
        sup.shutting_down.set()
        sup.stop()

    def _install_open_external_shim():
        # Fires on every navigation (splash, onboarding, dashboard,
        # daemon-restart reload) so the shim always covers the current
        # document. `window.__clawmetryExternalShim` guards against
        # double-install if the event fires twice on one page.
        try:
            window.evaluate_js(_OPEN_EXTERNAL_SHIM)
        except Exception:
            pass

    window.events.closed += _on_closed
    window.events.loaded += _install_open_external_shim
    threading.Thread(target=_boot, daemon=True).start()

    # js_api makes DesktopAPI methods callable as window.pywebview.api.*
    # Older pywebview versions don't accept `menu=`; fall back cleanly.
    try:
        webview.start(private_mode=False, menu=menu_items)
    except TypeError:
        webview.start(private_mode=False)
    return 0


if __name__ == "__main__":
    sys.exit(main())
