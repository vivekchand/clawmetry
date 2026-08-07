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

APP_TITLE = "ClawMetry"
STARTUP_TIMEOUT_SECS = 45.0
POLL_INTERVAL_SECS = 0.4
SHUTDOWN_WAIT_SECS = 5.0
# Skip the pip-upgrade if we ran one this recently.
UPGRADE_CHECK_INTERVAL_SECS = 6 * 3600

BRAND_RED = "#E94644"
BRAND_BG_DARK = "#0b0e14"


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


def _bootstrap_python() -> Optional[str]:
    """A real Python interpreter the shell can use to create a venv.
    PyInstaller's bundled interpreter can't (its `sys.executable` is
    the bundle exe and `python -m venv` mispoints), so we use the
    system Python. On macOS this is `/usr/bin/python3` (ships with the
    OS since Big Sur). On Linux, `python3` on PATH. On Windows, `py`
    or the Store Python."""
    candidates = ["python3", "/usr/bin/python3", "python", "py"]
    if platform.system() == "Windows":
        candidates = ["py", "python", "python3"]
    import shutil

    for c in candidates:
        p = shutil.which(c)
        if p:
            try:
                r = subprocess.run(
                    [p, "-c", "import sys,venv,pip; print(sys.version_info[:2])"],
                    capture_output=True, text=True, timeout=6,
                )
                if r.returncode == 0:
                    return p
            except Exception:
                continue
    return None


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
        py = self._venv_python()
        if not py.exists():
            return None
        try:
            r = subprocess.run(
                [str(py), "-c",
                 "import importlib.metadata as m; print(m.version('clawmetry'))"],
                capture_output=True, text=True, timeout=8,
            )
            if r.returncode == 0:
                return r.stdout.strip()
        except Exception:
            pass
        return None

    def bootstrap(self) -> bool:
        """Create the venv if missing; pip-install/upgrade clawmetry.
        Idempotent. Returns True if a runnable clawmetry ends up in
        the venv; False on any hard failure."""
        py = _bootstrap_python()
        if not py:
            self.on_status(
                "System Python 3 not found. Install python.org 3.11+ then relaunch."
            )
            self._log("no system python3 available")
            return False

        if not self._venv_python().exists():
            self.on_status("Creating runtime environment")
            try:
                subprocess.run(
                    [py, "-m", "venv", str(self.venv)],
                    check=True, capture_output=True, text=True, timeout=60,
                )
                self._log(f"venv created via {py}")
            except subprocess.CalledProcessError as e:
                self._log(f"venv creation failed: {e.stderr}")
                self.on_status("Runtime setup failed. Check bootstrap.log.")
                return False

        needs_upgrade = self._should_upgrade()
        currently_installed = self._get_installed_version()
        if currently_installed is None or needs_upgrade:
            action = "Installing" if currently_installed is None else "Checking for updates"
            self.on_status(f"{action} ClawMetry from PyPI")
            try:
                r = subprocess.run(
                    [str(self._venv_python()), "-m", "pip", "install",
                     "--upgrade", "--disable-pip-version-check", "clawmetry"],
                    capture_output=True, text=True, timeout=300,
                )
                self._log(f"pip install rc={r.returncode}")
                if r.returncode != 0:
                    self._log(r.stderr[:2000])
                    # If we already have a version installed, keep it — a
                    # transient PyPI failure shouldn't block launch.
                    if currently_installed is None:
                        self.on_status("PyPI install failed. See bootstrap.log.")
                        return False
                new_version = self._get_installed_version()
                self._mark_upgraded(new_version)
                self._log(f"clawmetry now at {new_version}")
            except subprocess.TimeoutExpired:
                self._log("pip install timed out")
                if currently_installed is None:
                    self.on_status("Install timed out. Check your connection.")
                    return False

        return self._venv_clawmetry().exists()

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
            kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP  # type: ignore[attr-defined]
        else:
            kwargs["start_new_session"] = True
        self.proc = subprocess.Popen(argv, **kwargs)

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


def _find_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def main() -> int:
    import webview

    port = int(os.environ.get("CLAWMETRY_APP_PORT") or _find_free_port())

    window = webview.create_window(
        APP_TITLE,
        html=_splash_html("Preparing runtime"),
        width=1280,
        height=820,
        min_size=(900, 600),
        background_color=BRAND_BG_DARK,
    )

    def _set_status(msg: str) -> None:
        try:
            window.load_html(_splash_html(msg))
        except Exception:
            pass

    sup = RuntimeSupervisor(port, _set_status)

    def _boot():
        ok = sup.bootstrap()
        if not ok:
            return  # status HTML already shown
        _set_status("Starting local daemon")
        sup.start_daemon()
        ready = sup.wait_ready()
        if ready:
            try:
                window.load_url(f"http://127.0.0.1:{port}/")
            except Exception:
                pass
        else:
            _set_status("Daemon did not come up. See bootstrap.log.")

    def _on_closed():
        sup.stop()

    window.events.closed += _on_closed
    threading.Thread(target=_boot, daemon=True).start()

    webview.start(private_mode=False)
    return 0


if __name__ == "__main__":
    sys.exit(main())
