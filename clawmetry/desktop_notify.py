"""clawmetry/desktop_notify.py: a desktop notification you can click.

Until now an urgent incident popped a notification that was a dead end. On
macOS it went out through ``osascript``'s ``display notification``, which has
no click action in AppleScript at all: the banner was attributed to Script
Editor and clicking it did nothing. On Linux ``notify-send`` fired with no
action, so clicking it only dismissed it. On Windows nothing was sent, ever.
A person who saw "CRITICAL: your agent changed 38 files" had to go and find
the dashboard themselves, which is the moment you least want friction.

This module is the one place that knows how to put a notification on a
desktop *with somewhere to go*. It carries a URL, and a click opens the
session that caused the alert.

Per platform, using each one's own supported mechanism:

* **macOS** - ``terminal-notifier``, whose ``-open <url>`` is the documented
  way to attach a URL to a notification. It is a real signed application
  bundle, which is also why the banner can carry an identity at all. We do
  not reimplement it: a notification with a click handler needs a Cocoa app
  with a run loop, and shelling out to a maintained one beats generating an
  app bundle at runtime. Found on ``PATH``, in the ClawMetry desktop app's
  Resources (where the ``.app`` build vendors it), or at the Homebrew
  prefixes. With none of those we still send the old ``osascript`` banner,
  which tells the person what happened even though it cannot be clicked.
* **Windows** - a native toast through ``ToastNotificationManager``, whose
  root ``launch`` attribute plus ``activationType="protocol"`` hands the URL
  to the shell on click. No module to install: the WinRT types are loaded
  from Windows PowerShell, and the script is passed as ``-EncodedCommand`` so
  no incident text is ever parsed as PowerShell. This platform had no desktop
  alert at all before.
* **Linux** - ``notify-send`` with ``-A default=Open``. libnotify prints the
  invoked action key on stdout and blocks until then, so the wait happens on
  a daemon thread and the URL is opened with ``xdg-open``. Where libnotify is
  older than 0.8 (no ``-A``) we send the plain banner as before.

Everything the incident text touches travels as ``argv`` or as base64, never
inside a script body, so a crafted session title cannot become AppleScript,
PowerShell or shell. Off with ``CLAWMETRY_DESKTOP_ALERTS=0``. Nothing here
raises: a notification that fails is logged and the other alert channels
still carry the incident.
"""
from __future__ import annotations

import base64
import logging
import os
import shutil
import subprocess  # noqa: S404 - fixed argv, never shell=True
import sys
import threading
import urllib.parse

log = logging.getLogger("clawmetry.desktop_notify")

#: How long a sender may take before we give up on it. The daemon calls this
#: from inside the detector pass (FLYWHEEL 1e), so it never waits long.
_SEND_TIMEOUT = 10

#: How long the Linux action listener may sit on a notification waiting for a
#: click before it gives up and frees the thread. Clicking after this still
#: dismisses the banner; it just will not open anything.
_LINUX_ACTION_TIMEOUT = int(os.environ.get("CLAWMETRY_NOTIFY_ACTION_WAIT", "1800"))

#: Windows needs a registered AUMID to show a toast; an unknown one is
#: silently dropped. Windows PowerShell's own Start-menu id is the documented
#: fallback every module-free recipe uses, and it is present on every machine
#: that has powershell.exe at all.
_WIN_APP_ID = (r"{1AC14E77-02E7-4E5D-B744-2EB1AE5198B7}"
               r"\WindowsPowerShell\v1.0\powershell.exe")


def enabled() -> bool:
    """Desktop notifications are on unless the operator turned them off."""
    return os.environ.get("CLAWMETRY_DESKTOP_ALERTS", "1").strip() != "0"


_warned_unclickable = False


def _warn_unclickable_once(reason: str) -> None:
    """Say once, in the daemon log, that a click will not land here.

    A control that cannot work has to say why rather than quietly doing
    nothing. Once per process, because the alternative is a line in the log
    for every incident on a machine that is never going to grow the
    capability mid-run.
    """
    global _warned_unclickable
    if _warned_unclickable:
        return
    _warned_unclickable = True
    log.warning("%s", reason)


# ── Where a click should land ───────────────────────────────────────────────

def dashboard_url(session_id: str = "", tab: str = "") -> str:
    """The local dashboard URL a notification should open.

    With a session id this is that session's page, which is what someone who
    just read "your agent changed 38 files" wants to see. The base comes from
    ``claude_code_gate.dashboard_base()``, the one resolver that already
    knows the port the dashboard actually bound (``~/.clawmetry/server.json``),
    so a dashboard on a non-default port still gets a working link.
    """
    base = "http://127.0.0.1:8900"
    try:
        from clawmetry.claude_code_gate import dashboard_base
        base = dashboard_base() or base
    except Exception:  # noqa: BLE001 - a bad config file must not cost the alert
        pass
    base = base.rstrip("/")
    sid = str(session_id or "").strip()
    if sid:
        # loadTranscripts() reads `#session=` with decodeURIComponent, and a
        # store session id is runtime-prefixed ("codex:01a1...").
        return base + "/#session=" + urllib.parse.quote(sid, safe="")
    t = str(tab or "").strip()
    return base + "/#" + t if t else base + "/"


# ── macOS ───────────────────────────────────────────────────────────────────

#: terminal-notifier 3 rebuilt on Apple's UserNotifications framework. Version
#: 2 still posts a banner, but its click callback depends on the old
#: NSUserNotification activation path, which modern macOS does not deliver:
#: measured dead on macOS 26.3.1 against 2.0.0, where `-execute` never ran.
#: Below this version we do not pretend a click will land.
_MIN_CLICKABLE_TN = (3, 0, 0)

_tn_versions: dict = {}

#: Set when terminal-notifier actually refused a notification on this machine
#: (version 3 exits non-zero when the user has not allowed it to post). A
#: capability report that ignores this advertises a click the machine has
#: already proven it will not deliver.
_tn_refusal: dict = {"reason": ""}


def _macos_notifier_version(path: str) -> tuple:
    """``(3, 1, 0)`` for terminal-notifier 3.1.0, or ``()`` when unreadable.

    Cached per path: this runs inside the detector pass and the answer only
    changes when the operator installs a different build.
    """
    if path in _tn_versions:
        return _tn_versions[path]
    version: tuple = ()
    try:
        done = subprocess.run(  # noqa: S603 - fixed argv
            [path, "-help"], capture_output=True, timeout=5)
        blob = ((done.stdout or b"") + (done.stderr or b"")).decode("utf-8", "replace")
        import re
        match = re.search(r"\((\d+)\.(\d+)(?:\.(\d+))?\)", blob)
        if match:
            version = tuple(int(g) for g in match.groups() if g is not None)
    except Exception:  # noqa: BLE001 - an unreadable version is not fatal
        version = ()
    _tn_versions[path] = version
    return version


def _macos_notifier() -> str:
    """Path to ``terminal-notifier``, or "" when this Mac has none."""
    env = os.environ.get("CLAWMETRY_TERMINAL_NOTIFIER", "").strip()
    if env and os.path.isfile(env) and os.access(env, os.X_OK):
        return env
    inner = "Contents/MacOS/terminal-notifier"
    candidates = [
        # Vendored into the ClawMetry desktop app, so a .dmg install has a
        # clickable notification with nothing else to install.
        "/Applications/ClawMetry.app/Contents/Resources/terminal-notifier.app/" + inner,
        shutil.which("terminal-notifier") or "",
        "/opt/homebrew/bin/terminal-notifier",
        "/usr/local/bin/terminal-notifier",
        "/Applications/terminal-notifier.app/" + inner,
    ]
    for path in candidates:
        if path and os.path.isfile(path) and os.access(path, os.X_OK):
            return path
    return ""


def _send_macos(title: str, message: str, url: str, group: str) -> bool:
    """terminal-notifier when it can really carry a click, osascript always.

    The fallback is not a nicety. terminal-notifier 3 refuses outright when
    the user has not allowed it to post notifications, and an alert that
    silently vanishes because a helper was unauthorised is worse than the
    unclickable banner we shipped for years. So every path that cannot
    deliver falls through to osascript rather than returning failure.
    """
    notifier = _macos_notifier()
    if notifier:
        version = _macos_notifier_version(notifier)
        if version >= _MIN_CLICKABLE_TN:
            argv = [notifier, "-title", title, "-message", message, "-sound", "Basso"]
            if url:
                argv += ["-open", url]
            if group:
                # One live banner per session: a second alert for the same
                # session replaces the first instead of stacking up.
                argv += ["-group", group]
            ok, err = _run_capturing(argv)
            if ok:
                _tn_refusal["reason"] = ""
                return True
            # Remember it, so capability() stops advertising a click that
            # this machine has already demonstrated it will not deliver.
            _tn_refusal["reason"] = (err.strip().splitlines() or ["refused"])[-1]
            _warn_unclickable_once(
                "terminal-notifier would not post this notification (%s). "
                "Allow it under System Settings > Notifications, then alerts "
                "will open the session on click. Falling back to a banner "
                "that cannot be clicked."
                % (err.strip().splitlines()[-1] if err.strip() else "no reason given"))
        else:
            # 2.x shows a banner, but its click callback rides the
            # NSUserNotification relaunch path that modern macOS no longer
            # delivers: the banner appears and clicking it does nothing.
            # Verified dead on macOS 26.3.1 with terminal-notifier 2.0.0.
            seen = ".".join(str(n) for n in version) if version else "below 3"
            _warn_unclickable_once(
                "terminal-notifier %s is too old to carry a click: its "
                "notification activation rides an API modern macOS no longer "
                "delivers, so the banner appears and clicking it does "
                "nothing. Run `brew upgrade terminal-notifier` for version 3 "
                "or newer and the next alert will open the session." % seen)
    if not shutil.which("osascript"):
        return False
    if url and not notifier:
        _warn_unclickable_once(
            "This notification cannot be clicked through to the session: "
            "macOS notifications sent through AppleScript carry no click "
            "action. `brew install terminal-notifier`, or install the "
            "ClawMetry desktop app, and the next alert will open %s" % url)
    # No click target is possible here: AppleScript's `display notification`
    # has no activation handler. The text still travels as argv so an
    # incident title can never be evaluated as script.
    argv = ["osascript",
            "-e", "on run argv",
            "-e", "display notification (item 2 of argv) with title "
                  "(item 1 of argv) sound name \"Basso\"",
            "-e", "end run", title, message]
    return _run(argv)


# ── Windows ─────────────────────────────────────────────────────────────────

def _xml_escape(text: str) -> str:
    return (str(text).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


def _windows_powershell() -> str:
    """Windows PowerShell, which carries the WinRT types.

    Deliberately not ``pwsh``: PowerShell 7 does not project the WinRT
    namespaces, so the same script throws there.
    """
    for name in ("powershell.exe", "powershell"):
        found = shutil.which(name)
        if found:
            return found
    system_root = os.environ.get("SystemRoot", r"C:\Windows")
    fallback = os.path.join(system_root, "System32", "WindowsPowerShell",
                            "v1.0", "powershell.exe")
    return fallback if os.path.isfile(fallback) else ""


def _toast_xml(title: str, message: str, url: str) -> str:
    launch = (' launch="%s" activationType="protocol"' % _xml_escape(url)) if url else ""
    return (
        '<toast duration="long"%s>'
        '<visual><binding template="ToastGeneric">'
        '<text>%s</text><text>%s</text>'
        '</binding></visual>'
        '<audio src="ms-winsoundevent:Notification.Looping.Alarm2"/>'
        '</toast>'
    ) % (launch, _xml_escape(title), _xml_escape(message))


def _send_windows(title: str, message: str, url: str) -> bool:
    shell = _windows_powershell()
    if not shell:
        return False
    xml_b64 = base64.b64encode(_toast_xml(title, message, url).encode("utf-8")).decode("ascii")
    # The incident text reaches PowerShell only as base64 that is decoded into
    # a variable, so nothing in it is ever parsed as PowerShell source.
    script = (
        "$ErrorActionPreference='Stop';"
        "[void][Windows.UI.Notifications.ToastNotificationManager,"
        "Windows.UI.Notifications,ContentType=WindowsRuntime];"
        "[void][Windows.Data.Xml.Dom.XmlDocument,"
        "Windows.Data.Xml.Dom,ContentType=WindowsRuntime];"
        "$doc=New-Object Windows.Data.Xml.Dom.XmlDocument;"
        "$doc.LoadXml([System.Text.Encoding]::UTF8.GetString("
        "[System.Convert]::FromBase64String('" + xml_b64 + "')));"
        "$t=New-Object Windows.UI.Notifications.ToastNotification $doc;"
        "[Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier("
        "'" + _WIN_APP_ID + "').Show($t);"
    )
    encoded = base64.b64encode(script.encode("utf-16-le")).decode("ascii")
    argv = [shell, "-NoProfile", "-NonInteractive", "-WindowStyle", "Hidden",
            "-EncodedCommand", encoded]
    # Without this the daemon flashes a console window on every alert.
    flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    return _run(argv, creationflags=flags)


# ── Linux ───────────────────────────────────────────────────────────────────

_notify_send_actions: "bool | None" = None


def _notify_send_supports_actions(notify_send: str) -> bool:
    """libnotify grew ``-A/--action`` in 0.8 (2022). Older ones reject it."""
    global _notify_send_actions
    if _notify_send_actions is None:
        try:
            help_text = subprocess.run(  # noqa: S603 - fixed argv
                [notify_send, "--help"], capture_output=True, timeout=5,
            )
            blob = (help_text.stdout or b"") + (help_text.stderr or b"")
            _notify_send_actions = b"--action" in blob
        except Exception:  # noqa: BLE001
            _notify_send_actions = False
    return bool(_notify_send_actions)


def _open_url_linux(url: str) -> None:
    for opener in ("xdg-open", "gio"):
        path = shutil.which(opener)
        if not path:
            continue
        argv = [path, "open", url] if opener == "gio" else [path, url]
        try:
            subprocess.run(argv, timeout=_SEND_TIMEOUT,  # noqa: S603 - fixed argv
                           capture_output=True)
            return
        except Exception:  # noqa: BLE001
            continue


def _wait_for_click(argv: list, url: str) -> None:
    """Block on notify-send until the banner is clicked, then open the URL.

    Runs on a daemon thread: with ``-A`` notify-send does not return until the
    notification is acted on or closed, and the detector pass must not wait
    for a person.
    """
    try:
        done = subprocess.run(  # noqa: S603 - fixed argv
            argv, capture_output=True, timeout=_LINUX_ACTION_TIMEOUT)
    except Exception:  # noqa: BLE001 - a timeout here just means nobody clicked
        return
    if done.returncode == 0 and (done.stdout or b"").strip() == b"default":
        _open_url_linux(url)


def _send_linux(title: str, message: str, url: str) -> bool:
    notify_send = shutil.which("notify-send")
    if not notify_send:
        return False
    argv = [notify_send, "--urgency=critical", "--app-name=ClawMetry"]
    if url and _notify_send_supports_actions(notify_send):
        # "default" is the action id a notification daemon invokes when the
        # body itself is clicked, which is the gesture we want.
        argv += ["-A", "default=Open"]
        argv += [title, message]
        threading.Thread(target=_wait_for_click, args=(argv, url),
                         daemon=True, name="clawmetry-notify-click").start()
        return True
    argv += [title, message]
    return _run(argv)


# ── Entry point ─────────────────────────────────────────────────────────────

def _run_capturing(argv: list, **kwargs) -> tuple:
    """``(ok, stderr_text)``. The reason matters here: terminal-notifier 3
    refuses with a readable sentence when it has no notification permission,
    and that sentence is what the operator needs to see."""
    try:
        done = subprocess.run(  # noqa: S603 - fixed argv, never shell=True
            argv, timeout=_SEND_TIMEOUT, capture_output=True, **kwargs)
        err = ((done.stderr or b"") + (done.stdout or b"")).decode("utf-8", "replace")
        return done.returncode == 0, err
    except Exception as e:  # noqa: BLE001
        return False, str(e)


def _run(argv: list, **kwargs) -> bool:
    try:
        done = subprocess.run(  # noqa: S603 - fixed argv, never shell=True
            argv, timeout=_SEND_TIMEOUT, capture_output=True, **kwargs)
        if done.returncode != 0:
            log.debug("notifier %s exited %s: %s", argv[0], done.returncode,
                      (done.stderr or b"")[:200])
        return done.returncode == 0
    except Exception as e:  # noqa: BLE001
        log.debug("notifier %s failed: %s", argv[0] if argv else "?", e)
        return False


def notify(title: str, message: str, *, url: str = "", group: str = "") -> bool:
    """Put one notification on this desktop. ``url`` opens when it is clicked.

    Returns whether the notification was handed to the platform, not whether
    anyone saw it. Never raises.
    """
    if not enabled():
        return False
    try:
        t = str(title or "ClawMetry")[:120]
        m = str(message or "")[:400]
        u = str(url or "").strip()
        if u and not (u.startswith("http://") or u.startswith("https://")):
            # Only ever hand the shell an http(s) URL. A click is a launch,
            # and file:// or a custom scheme is not something an incident
            # gets to choose.
            u = ""
        if sys.platform == "darwin":
            return _send_macos(t, m, u, str(group or "")[:120])
        if sys.platform.startswith("win"):
            return _send_windows(t, m, u)
        if sys.platform.startswith("linux"):
            return _send_linux(t, m, u)
        return False
    except Exception as e:  # noqa: BLE001
        log.debug("desktop notification failed: %s", e)
        return False


def capability() -> dict:
    """What this machine can actually do, for diagnostics and the UI.

    A control that cannot work has to say why rather than quietly doing
    nothing, so this reports the mechanism and whether a click will land.
    """
    out = {"platform": sys.platform, "enabled": enabled(),
           "mechanism": "", "can_notify": False, "clickable": False, "reason": ""}
    if sys.platform == "darwin":
        notifier = _macos_notifier()
        version = _macos_notifier_version(notifier) if notifier else ()
        if notifier and version >= _MIN_CLICKABLE_TN and _tn_refusal["reason"]:
            out.update(
                mechanism="terminal-notifier (not permitted)", can_notify=True,
                clickable=False,
                reason="terminal-notifier is installed but macOS has not "
                       "allowed it to post notifications (%s). Allow it under "
                       "System Settings > Notifications; alerts fall back to "
                       "an unclickable banner until then."
                       % _tn_refusal["reason"])
        elif notifier and version >= _MIN_CLICKABLE_TN:
            out.update(mechanism="terminal-notifier", can_notify=True,
                       clickable=True, reason="")
        elif notifier:
            # It will post a banner, but the click is dead on modern macOS.
            out.update(
                mechanism="terminal-notifier (too old)", can_notify=True,
                clickable=False,
                reason="terminal-notifier %s cannot carry a click on this "
                       "macOS. `brew upgrade terminal-notifier` for 3 or newer."
                       % (".".join(str(n) for n in version) if version else "below 3"))
        elif shutil.which("osascript"):
            out.update(
                mechanism="osascript", can_notify=True, clickable=False,
                reason="AppleScript notifications cannot carry a click action. "
                       "Install terminal-notifier (brew install terminal-notifier) "
                       "or the ClawMetry desktop app to open the session on click.")
        else:
            out["reason"] = "no osascript on this Mac"
    elif sys.platform.startswith("win"):
        if _windows_powershell():
            out.update(mechanism="windows-toast", can_notify=True, clickable=True)
        else:
            out["reason"] = "Windows PowerShell not found, so no toast can be shown"
    elif sys.platform.startswith("linux"):
        notify_send = shutil.which("notify-send")
        if not notify_send:
            out["reason"] = "notify-send not installed (libnotify)"
        elif _notify_send_supports_actions(notify_send):
            out.update(mechanism="notify-send+action", can_notify=True, clickable=True)
        else:
            out.update(
                mechanism="notify-send", can_notify=True, clickable=False,
                reason="libnotify is older than 0.8, which has no --action, "
                       "so the notification cannot be clicked through.")
    else:
        out["reason"] = "no desktop notifier known for this platform"
    return out
