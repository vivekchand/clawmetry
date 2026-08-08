"""ClawMetry desktop tray/menubar supervisor.

Runs as a background menubar/tray app. Spawns the `clawmetry`
process (dashboard + daemon) as a child, exposes menu items for
opening the dashboard, checking status, restarting, and quitting.

Usage:
    python -m desktop.tray

Cross-platform via pystray. On macOS the menubar shows an icon; on
Windows and most Linux desktops the system tray does the same. The
Flask UI itself is unchanged and opens in the user's default browser
via `Open Dashboard`.

This is the Phase 1 shell for the "single downloadable" packaging
path (see desktop/README.md). The py2app / PyInstaller specs bundle
this module together with the clawmetry package into a signed app.
"""

from __future__ import annotations

import os
import signal
import subprocess
import sys
import threading
import time
import urllib.request
import webbrowser
from pathlib import Path
from typing import Optional

DASHBOARD_URL = os.environ.get("CLAWMETRY_TRAY_URL", "http://localhost:8900")
CLOUD_LOGIN_URL = os.environ.get(
    "CLAWMETRY_TRAY_LOGIN_URL", "https://clawmetry.com/login"
)
POLL_INTERVAL_SECS = 3.0
STARTUP_WAIT_SECS = 20.0
SHUTDOWN_WAIT_SECS = 5.0
LOCK_PATH = Path.home() / ".clawmetry" / "desktop.lock"


CHILD_ROLE_FLAG = "--role=clawmetry"


def _resolve_clawmetry_command() -> list[str]:
    """Return the argv to invoke the clawmetry CLI.

    Frozen bundle (`sys.frozen`): re-exec ourselves with
    `CHILD_ROLE_FLAG`, which `main()` intercepts and routes to
    `clawmetry.cli.main()` in-process. PyInstaller doesn't support
    `-m` on the bundle exe, so this dispatcher pattern is how we
    launch bundled Python code as a subprocess.

    Dev / source checkout: prefer `clawmetry` on PATH; fall back to
    `python -m clawmetry.cli`.
    """
    override = os.environ.get("CLAWMETRY_TRAY_CMD")
    if override:
        return override.split()
    extra = ["--no-debug"]  # never launch the Werkzeug reloader from
    # the tray: the reloader re-execs sys.executable, which in a
    # PyInstaller bundle drops our --role flag from argv and falls
    # through to the tray main / singleton lock. --no-debug picks the
    # waitress path in dashboard.main().
    if getattr(sys, "frozen", False):
        return [sys.executable, CHILD_ROLE_FLAG, *extra]
    import shutil

    on_path = shutil.which("clawmetry")
    if on_path:
        return [on_path, *extra]
    return [sys.executable, "-m", "clawmetry.cli", *extra]


def _make_icon_image(color: tuple[int, int, int] = (74, 144, 226)):
    """Generate a 64x64 tray icon in-memory. Avoids shipping an asset
    file until we add real branding to the bundle."""
    from PIL import Image, ImageDraw

    size = 64
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.ellipse((4, 4, size - 4, size - 4), fill=color)
    d.text((22, 18), "C", fill=(255, 255, 255))
    return img


class Supervisor:
    """Owns the `clawmetry` child process lifecycle + a status poller.

    Not thread-safe against concurrent restart/quit calls, which is
    fine because menu clicks are serialized by pystray.
    """

    def __init__(self):
        self.proc: Optional[subprocess.Popen] = None
        self.status: str = "starting"
        self._stop_poll = threading.Event()
        self._poll_thread: Optional[threading.Thread] = None

    def start(self) -> None:
        if self.proc and self.proc.poll() is None:
            return
        argv = _resolve_clawmetry_command()
        # Force production mode in the bundle. Werkzeug's dev reloader
        # re-execs sys.executable — inside a PyInstaller bundle that
        # strips our --role flag from argv and the second process falls
        # through to the tray main and hits the singleton lock. Setting
        # WERKZEUG_RUN_MAIN + FLASK_DEBUG=0 keeps Flask on a single
        # process.
        env = os.environ.copy()
        env.setdefault("WERKZEUG_RUN_MAIN", "true")
        env.setdefault("FLASK_DEBUG", "0")
        env.setdefault("FLASK_ENV", "production")
        env.setdefault("CLAWMETRY_DEBUG", "0")
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
        try:
            self.proc = subprocess.Popen(argv, **kwargs)
            self.status = "starting"
        except FileNotFoundError:
            self.status = "clawmetry-not-installed"

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
        self.status = "stopped"

    def restart(self) -> None:
        self.stop()
        self.start()

    def _probe_once(self) -> str:
        try:
            with urllib.request.urlopen(DASHBOARD_URL + "/api/version", timeout=2) as r:
                if 200 <= r.status < 300:
                    return "running"
        except Exception:
            pass
        try:
            with urllib.request.urlopen(DASHBOARD_URL, timeout=2) as r:
                if 200 <= r.status < 400:
                    return "running"
        except Exception:
            pass
        return "starting" if self.proc and self.proc.poll() is None else "stopped"

    def _poll_loop(self) -> None:
        deadline = time.time() + STARTUP_WAIT_SECS
        while not self._stop_poll.is_set():
            self.status = self._probe_once()
            if self.status == "starting" and time.time() > deadline:
                if not self.proc or self.proc.poll() is not None:
                    self.status = "crashed"
            self._stop_poll.wait(POLL_INTERVAL_SECS)

    def begin_polling(self) -> None:
        self._poll_thread = threading.Thread(target=self._poll_loop, daemon=True)
        self._poll_thread.start()

    def end_polling(self) -> None:
        self._stop_poll.set()


def _acquire_singleton_lock() -> Optional[object]:
    """Best-effort single-instance guard. Returns a lock handle to hold
    open for the process lifetime, or None if another instance is
    already running."""
    LOCK_PATH.parent.mkdir(parents=True, exist_ok=True)
    try:
        fh = open(LOCK_PATH, "w")
    except OSError:
        return object()
    try:
        if os.name == "nt":
            import msvcrt

            msvcrt.locking(fh.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl

            fcntl.flock(fh, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except (OSError, BlockingIOError):
        fh.close()
        return None
    fh.write(str(os.getpid()))
    fh.flush()
    return fh


def _run_as_clawmetry_child() -> int:
    """Bundle dispatcher: re-invoked by the tray as a subprocess when
    frozen. Strips our role flag from argv and hands off to the real
    clawmetry CLI, so the exe doubles as both the tray and the daemon
    without needing a second bundled executable."""
    from clawmetry.cli import main as cli_main

    sys.argv = ["clawmetry"] + [a for a in sys.argv[1:] if a != CHILD_ROLE_FLAG]
    return cli_main() or 0


def main() -> int:
    if CHILD_ROLE_FLAG in sys.argv[1:]:
        return _run_as_clawmetry_child()

    lock = _acquire_singleton_lock()
    if lock is None:
        print("clawmetry tray already running", file=sys.stderr)
        webbrowser.open(DASHBOARD_URL)
        return 0

    try:
        import pystray
        from pystray import MenuItem as Item, Menu
    except ImportError:
        print(
            "pystray is required. install with: pip install -r desktop/requirements-dev.txt",
            file=sys.stderr,
        )
        return 2

    sup = Supervisor()
    sup.start()
    sup.begin_polling()

    def _open_dashboard(_icon, _item):
        webbrowser.open(DASHBOARD_URL)

    def _open_login(_icon, _item):
        webbrowser.open(CLOUD_LOGIN_URL)

    def _restart(_icon, _item):
        sup.restart()

    def _status_label(_item) -> str:
        return {
            "running": "Status: running",
            "starting": "Status: starting…",
            "stopped": "Status: stopped",
            "crashed": "Status: crashed",
            "clawmetry-not-installed": "Status: clawmetry not installed",
        }.get(sup.status, f"Status: {sup.status}")

    def _quit(icon, _item):
        sup.end_polling()
        sup.stop()
        icon.stop()

    menu = Menu(
        Item("Open Dashboard", _open_dashboard, default=True),
        Item(_status_label, None, enabled=False),
        Menu.SEPARATOR,
        Item("Restart", _restart),
        Item("Sign In / Cloud", _open_login),
        Menu.SEPARATOR,
        Item("Quit ClawMetry", _quit),
    )

    icon = pystray.Icon("clawmetry", _make_icon_image(), "ClawMetry", menu)

    def _refresh():
        while not sup._stop_poll.is_set():
            icon.update_menu()
            time.sleep(POLL_INTERVAL_SECS)

    threading.Thread(target=_refresh, daemon=True).start()

    icon.run()
    return 0


if __name__ == "__main__":
    sys.exit(main())
