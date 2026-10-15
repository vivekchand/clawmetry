"""A desktop notification has somewhere to go, on all three desktops.

Burned 2026-10-15: a CRITICAL "your claude code agent changed 38 files at
once" banner appeared on macOS and clicking it did nothing. Three separate
holes behind one symptom:

* macOS sent the banner through AppleScript's ``display notification``, which
  has no click action at all, so there was nothing to click through to;
* Linux sent ``notify-send`` with no action, same dead end;
* Windows sent **nothing** - ``send_desktop`` fell through to ``return False``
  for every non-mac, non-linux platform, so that whole user base had no
  desktop alerting whatsoever.

These tests pin the fix per platform, and pin the two properties that must
survive it: the incident text never becomes executable script on any backend,
and a notification nobody can click says so instead of pretending.

Every test drives the platform branch with a fake ``subprocess.run``; none of
them puts a notification on the machine running the suite.
"""
from __future__ import annotations

import base64
import os
import subprocess
import sys

import pytest

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from clawmetry import desktop_notify as dn  # noqa: E402

_URL = "http://127.0.0.1:8900/#session=codex%3Aabc"
# A title that is script in three languages at once.
_EVIL = 'x" & do shell script "rm -rf ~" & "; $(rm -rf /); <img src=x>'


@pytest.fixture
def on(monkeypatch):
    monkeypatch.setenv("CLAWMETRY_DESKTOP_ALERTS", "1")
    monkeypatch.setattr(dn, "_notify_send_actions", None)
    # Module-level state: a refusal observed by one test must not leak into
    # the next one's capability report.
    monkeypatch.setattr(dn, "_tn_refusal", {"reason": ""})
    monkeypatch.setattr(dn, "_tn_versions", {})


@pytest.fixture
def run_spy(monkeypatch):
    """Capture argv instead of running a notifier."""
    calls = []

    def fake_run(argv, **kw):
        calls.append(list(argv))
        return subprocess.CompletedProcess(argv, 0, stdout=b"", stderr=b"")

    monkeypatch.setattr(dn.subprocess, "run", fake_run)
    return calls


# ── macOS ───────────────────────────────────────────────────────────────────

def test_macos_attaches_the_url_with_terminal_notifier(on, run_spy, monkeypatch):
    monkeypatch.setattr(dn.sys, "platform", "darwin")
    monkeypatch.setattr(dn, "_macos_notifier", lambda: "/opt/homebrew/bin/terminal-notifier")
    monkeypatch.setattr(dn, "_macos_notifier_version", lambda p: (3, 1, 0))
    assert dn.notify("t", "m", url=_URL, group="codex:abc") is True
    argv = run_spy[0]
    assert argv[0].endswith("terminal-notifier")
    assert "-open" in argv and argv[argv.index("-open") + 1] == _URL
    # One live banner per session rather than a growing stack.
    assert argv[argv.index("-group") + 1] == "codex:abc"


def test_macos_without_terminal_notifier_still_notifies(on, run_spy, monkeypatch):
    """A Mac with nothing installed must still see the incident. It cannot be
    clicked, which `capability()` is required to admit (below)."""
    monkeypatch.setattr(dn.sys, "platform", "darwin")
    monkeypatch.setattr(dn, "_macos_notifier", lambda: "")
    monkeypatch.setattr(dn.shutil, "which", lambda n: "/usr/bin/osascript")
    assert dn.notify("t", "m", url=_URL) is True
    assert run_spy[0][0].endswith("osascript")


def test_macos_incident_text_is_argv_on_both_backends(on, run_spy, monkeypatch):
    monkeypatch.setattr(dn.sys, "platform", "darwin")
    for notifier in ("/opt/homebrew/bin/terminal-notifier", ""):
        run_spy.clear()
        monkeypatch.setattr(dn, "_macos_notifier", lambda n=notifier: n)
        monkeypatch.setattr(dn, "_macos_notifier_version", lambda p: (3, 1, 0))
        monkeypatch.setattr(dn.shutil, "which", lambda n: "/usr/bin/osascript")
        dn.notify(_EVIL, "body", url=_URL)
        argv = run_spy[0]
        assert _EVIL in argv, "the title must be its own argv element"
        script_parts = [a for a in argv if a != _EVIL]
        assert not any("rm -rf" in a for a in script_parts), \
            "incident text must never reach a script body"


# ── Windows (the platform that got nothing at all before) ───────────────────

def test_windows_sends_a_toast_that_opens_the_url(on, run_spy, monkeypatch):
    monkeypatch.setattr(dn.sys, "platform", "win32")
    monkeypatch.setattr(dn, "_windows_powershell", lambda: r"C:\ps\powershell.exe")
    assert dn.notify("t", "m", url=_URL) is True
    argv = run_spy[0]
    assert argv[0].endswith("powershell.exe")
    assert "-EncodedCommand" in argv
    script = base64.b64decode(argv[argv.index("-EncodedCommand") + 1]).decode("utf-16-le")
    assert "ToastNotificationManager" in script
    # The URL rides in the base64 toast XML, not in the PowerShell source.
    xml_b64 = script.split("FromBase64String('")[1].split("'")[0]
    xml = base64.b64decode(xml_b64).decode("utf-8")
    assert 'activationType="protocol"' in xml
    assert _URL.replace("&", "&amp;") in xml


def test_windows_is_no_longer_a_silent_no_op(on, run_spy, monkeypatch):
    """The regression this file exists for: before the fix every Windows
    install returned False and showed nothing, forever."""
    monkeypatch.setattr(dn.sys, "platform", "win32")
    monkeypatch.setattr(dn, "_windows_powershell", lambda: r"C:\ps\powershell.exe")
    assert dn.notify("t", "m") is True
    assert run_spy, "Windows must actually invoke a notifier"


def test_windows_incident_text_cannot_escape_the_toast_xml(on, run_spy, monkeypatch):
    monkeypatch.setattr(dn.sys, "platform", "win32")
    monkeypatch.setattr(dn, "_windows_powershell", lambda: r"C:\ps\powershell.exe")
    dn.notify(_EVIL, "</text></binding></visual></toast><toast>", url=_URL)
    script = base64.b64decode(
        run_spy[0][run_spy[0].index("-EncodedCommand") + 1]).decode("utf-16-le")
    # Nothing from the incident appears as PowerShell source, and the XML it
    # does reach is escaped rather than structural.
    assert "rm -rf" not in script
    xml = base64.b64decode(
        script.split("FromBase64String('")[1].split("'")[0]).decode("utf-8")
    assert "&lt;/text&gt;" in xml
    assert xml.count("<toast") == 1


def test_windows_uses_windows_powershell_not_pwsh(monkeypatch, tmp_path):
    """PowerShell 7 does not project the WinRT namespaces, so the same script
    throws there. A machine with only `pwsh` must resolve to nothing rather
    than to a shell that will fail at runtime."""
    monkeypatch.setattr(dn.shutil, "which",
                        lambda n: "/usr/bin/pwsh" if n == "pwsh" else None)
    monkeypatch.setenv("SystemRoot", str(tmp_path))
    assert dn._windows_powershell() == ""

    monkeypatch.setattr(dn.shutil, "which",
                        lambda n: r"C:\ps\powershell.exe" if n.startswith("powershell") else None)
    assert dn._windows_powershell().endswith("powershell.exe")


# ── Linux ───────────────────────────────────────────────────────────────────

def test_linux_adds_a_default_action_and_opens_on_click(on, monkeypatch):
    monkeypatch.setattr(dn.sys, "platform", "linux")
    monkeypatch.setattr(dn.shutil, "which",
                        lambda n: "/usr/bin/" + n if n in ("notify-send", "xdg-open") else None)
    monkeypatch.setattr(dn, "_notify_send_supports_actions", lambda p: True)
    started = {}

    class _Thread:
        def __init__(self, target=None, args=(), **kw):
            started["target"], started["args"] = target, args

        def start(self):
            started["started"] = True

    monkeypatch.setattr(dn.threading, "Thread", _Thread)
    assert dn.notify("t", "m", url=_URL) is True
    assert started["started"] is True
    argv = started["args"][0]
    assert "-A" in argv and argv[argv.index("-A") + 1] == "default=Open"

    # Now play the click: libnotify prints the invoked action key.
    opened = []
    monkeypatch.setattr(dn.subprocess, "run",
                        lambda a, **kw: subprocess.CompletedProcess(a, 0, stdout=b"default\n"))
    monkeypatch.setattr(dn, "_open_url_linux", lambda u: opened.append(u))
    dn._wait_for_click(argv, _URL)
    assert opened == [_URL]


def test_linux_dismissal_opens_nothing(on, monkeypatch):
    """Closing a notification is not clicking it."""
    opened = []
    monkeypatch.setattr(dn.subprocess, "run",
                        lambda a, **kw: subprocess.CompletedProcess(a, 0, stdout=b""))
    monkeypatch.setattr(dn, "_open_url_linux", lambda u: opened.append(u))
    dn._wait_for_click(["notify-send"], _URL)
    assert opened == []


def test_linux_old_libnotify_still_notifies(on, run_spy, monkeypatch):
    """libnotify below 0.8 has no --action. The banner must still appear."""
    monkeypatch.setattr(dn.sys, "platform", "linux")
    monkeypatch.setattr(dn.shutil, "which", lambda n: "/usr/bin/notify-send")
    monkeypatch.setattr(dn, "_notify_send_supports_actions", lambda p: False)
    assert dn.notify("t", "m", url=_URL) is True
    assert "-A" not in run_spy[0]


def test_linux_action_support_is_probed_not_assumed(on, monkeypatch):
    monkeypatch.setattr(
        dn.subprocess, "run",
        lambda a, **kw: subprocess.CompletedProcess(a, 0, stdout=b"  -A, --action=\n", stderr=b""))
    assert dn._notify_send_supports_actions("/usr/bin/notify-send") is True
    dn._notify_send_actions = None
    monkeypatch.setattr(
        dn.subprocess, "run",
        lambda a, **kw: subprocess.CompletedProcess(a, 0, stdout=b"  -u, --urgency\n", stderr=b""))
    assert dn._notify_send_supports_actions("/usr/bin/notify-send") is False


# ── Shared contract ─────────────────────────────────────────────────────────

def test_the_url_is_the_session_page_on_the_port_the_dashboard_bound(monkeypatch):
    monkeypatch.setattr("clawmetry.claude_code_gate.dashboard_base",
                        lambda: "http://127.0.0.1:8931")
    url = dn.dashboard_url("codex:01a1-ef5a")
    # loadTranscripts() reads `#session=` through decodeURIComponent, so the
    # runtime-prefixing colon has to be encoded.
    assert url == "http://127.0.0.1:8931/#session=codex%3A01a1-ef5a"
    assert dn.dashboard_url() == "http://127.0.0.1:8931/"


def test_a_broken_port_file_costs_the_link_not_the_notification(monkeypatch):
    def boom():
        raise OSError("no server.json")
    monkeypatch.setattr("clawmetry.claude_code_gate.dashboard_base", boom)
    assert dn.dashboard_url("s1").startswith("http://127.0.0.1:8900/#session=")


@pytest.mark.parametrize("bad", [
    "file:///etc/passwd", "javascript:alert(1)", "clawmetry://x", "ftp://h/f",
])
def test_only_http_urls_are_ever_handed_to_the_shell(on, run_spy, monkeypatch, bad):
    """A click is a launch. An incident does not get to choose the scheme."""
    monkeypatch.setattr(dn.sys, "platform", "darwin")
    monkeypatch.setattr(dn, "_macos_notifier", lambda: "/bin/terminal-notifier")
    monkeypatch.setattr(dn, "_macos_notifier_version", lambda p: (3, 1, 0))
    dn.notify("t", "m", url=bad)
    assert "-open" not in run_spy[0], f"{bad} must never reach -open"


def test_the_env_kill_switch_still_silences_everything(monkeypatch, run_spy):
    monkeypatch.setenv("CLAWMETRY_DESKTOP_ALERTS", "0")
    assert dn.notify("t", "m", url=_URL) is False
    assert run_spy == []


def test_a_notifier_that_fails_never_raises(on, monkeypatch):
    monkeypatch.setattr(dn.sys, "platform", "darwin")
    monkeypatch.setattr(dn, "_macos_notifier", lambda: "/bin/terminal-notifier")
    monkeypatch.setattr(dn, "_macos_notifier_version", lambda p: (3, 1, 0))
    monkeypatch.setattr(dn.shutil, "which", lambda n: None)

    def boom(*a, **kw):
        raise OSError("notifier exploded")

    monkeypatch.setattr(dn.subprocess, "run", boom)
    assert dn.notify("t", "m", url=_URL) is False


def test_an_unknown_platform_is_honest_rather_than_crashing(on, monkeypatch):
    monkeypatch.setattr(dn.sys, "platform", "sunos5")
    assert dn.notify("t", "m", url=_URL) is False
    cap = dn.capability()
    assert cap["can_notify"] is False and cap["reason"]


def test_capability_admits_when_a_click_cannot_work(on, monkeypatch):
    """A control that cannot work has to say why. A Mac with no
    terminal-notifier still notifies, but it must not claim to be clickable."""
    monkeypatch.setattr(dn.sys, "platform", "darwin")
    monkeypatch.setattr(dn, "_macos_notifier", lambda: "")
    monkeypatch.setattr(dn.shutil, "which", lambda n: "/usr/bin/osascript")
    cap = dn.capability()
    assert cap["can_notify"] is True
    assert cap["clickable"] is False
    assert "terminal-notifier" in cap["reason"]

    monkeypatch.setattr(dn, "_macos_notifier", lambda: "/bin/terminal-notifier")
    monkeypatch.setattr(dn, "_macos_notifier_version", lambda p: (3, 1, 0))
    cap = dn.capability()
    assert cap["clickable"] is True and cap["reason"] == ""


def test_every_platform_branch_is_covered_by_capability(on, monkeypatch):
    """Auto-discovering guard: the branch set here must match notify()'s, so a
    new platform cannot be added to one and forgotten in the other."""
    # shutil.which() itself reaches into _winapi when sys.platform says
    # win32, which does not exist off Windows; the probe is not what is
    # under test here.
    monkeypatch.setattr(dn.shutil, "which", lambda n: "/usr/bin/" + n)
    for platform in ("darwin", "win32", "linux", "cygwin"):
        monkeypatch.setattr(dn.sys, "platform", platform)
        cap = dn.capability()
        assert cap["platform"] == platform
        # Either it can notify, or it explains why not. Never silently false.
        assert cap["can_notify"] or cap["reason"], platform


def test_an_unclickable_mac_says_so_in_the_log(on, run_spy, monkeypatch, caplog):
    """Never ship a control that quietly does nothing: the one Mac path that
    cannot carry a click has to name itself and the one-line fix."""
    monkeypatch.setattr(dn, "_warned_unclickable", False)
    monkeypatch.setattr(dn.sys, "platform", "darwin")
    monkeypatch.setattr(dn, "_macos_notifier", lambda: "")
    monkeypatch.setattr(dn.shutil, "which", lambda n: "/usr/bin/osascript")
    with caplog.at_level("WARNING", logger="clawmetry.desktop_notify"):
        dn.notify("t", "m", url=_URL)
        dn.notify("t", "m", url=_URL)
    warnings = [r for r in caplog.records if r.levelname == "WARNING"]
    assert len(warnings) == 1, "said once per process, not once per incident"
    assert "terminal-notifier" in warnings[0].getMessage()


# ── What the live macOS run actually exposed (2026-10-15) ───────────────────
#
# The first cut of this feature shipped two defects that only a real machine
# showed. Both are pinned here.

def test_a_terminal_notifier_too_old_to_click_is_not_called_clickable(on, run_spy,
                                                                      monkeypatch):
    """terminal-notifier 2.0.0 posts the banner and silently swallows the
    click: its activation rides the NSUserNotification relaunch path, which
    macOS 26 does not deliver. Measured on 26.3.1, where `-execute` never
    ran. Claiming `clickable` for it is the dead control the repo forbids.
    """
    monkeypatch.setattr(dn.sys, "platform", "darwin")
    monkeypatch.setattr(dn, "_macos_notifier", lambda: "/opt/homebrew/bin/terminal-notifier")
    monkeypatch.setattr(dn, "_macos_notifier_version", lambda p: (2, 0, 0))
    monkeypatch.setattr(dn.shutil, "which", lambda n: "/usr/bin/osascript")

    cap = dn.capability()
    assert cap["can_notify"] is True
    assert cap["clickable"] is False
    assert "upgrade" in cap["reason"]

    # And it must not be handed a -open it cannot honour: the banner goes out
    # through osascript instead, so the person still learns about the agent.
    assert dn.notify("t", "m", url=_URL) is True
    assert run_spy[-1][0].endswith("osascript")
    assert not any("-open" in a for a in run_spy[-1])


def test_a_refused_terminal_notifier_still_gets_a_banner_out(on, monkeypatch, caplog):
    """terminal-notifier 3 exits non-zero when the user has not allowed it to
    post notifications ("Notifications are not allowed for this application").
    Returning that failure meant NO alert at all, which is worse than the
    unclickable banner this feature replaced. It must fall through.
    """
    monkeypatch.setattr(dn, "_warned_unclickable", False)
    monkeypatch.setattr(dn.sys, "platform", "darwin")
    monkeypatch.setattr(dn, "_macos_notifier", lambda: "/opt/homebrew/bin/terminal-notifier")
    monkeypatch.setattr(dn, "_macos_notifier_version", lambda p: (3, 1, 0))
    monkeypatch.setattr(dn.shutil, "which", lambda n: "/usr/bin/osascript")
    seen = []

    def fake_run(argv, **kw):
        seen.append(list(argv))
        if argv[0].endswith("terminal-notifier"):
            return subprocess.CompletedProcess(
                argv, 3, stdout=b"",
                stderr=b"Could not request notification permission: "
                       b"Notifications are not allowed for this application\n")
        return subprocess.CompletedProcess(argv, 0, stdout=b"", stderr=b"")

    monkeypatch.setattr(dn.subprocess, "run", fake_run)
    with caplog.at_level("WARNING", logger="clawmetry.desktop_notify"):
        assert dn.notify("t", "m", url=_URL) is True, \
            "an unauthorised helper must never silence the alert"
    assert seen[0][0].endswith("terminal-notifier")
    assert seen[-1][0].endswith("osascript")
    said = " ".join(r.getMessage() for r in caplog.records)
    assert "Notifications are not allowed" in said
    assert "System Settings" in said


def test_the_version_probe_reads_what_the_binary_reports(monkeypatch):
    dn._tn_versions.clear()
    monkeypatch.setattr(
        dn.subprocess, "run",
        lambda a, **kw: subprocess.CompletedProcess(
            a, 0, stdout=b"terminal-notifier (3.1.0) is a command-line tool\n", stderr=b""))
    assert dn._macos_notifier_version("/x/tn") == (3, 1, 0)
    # Cached: a second call must not shell out again.
    monkeypatch.setattr(dn.subprocess, "run",
                        lambda a, **kw: (_ for _ in ()).throw(AssertionError("re-probed")))
    assert dn._macos_notifier_version("/x/tn") == (3, 1, 0)

    dn._tn_versions.clear()
    monkeypatch.setattr(
        dn.subprocess, "run",
        lambda a, **kw: subprocess.CompletedProcess(
            a, 0, stdout=b"terminal-notifier (2.0.0) is a command-line tool\n", stderr=b""))
    assert dn._macos_notifier_version("/x/tn") == (2, 0, 0)
    assert dn._macos_notifier_version("/x/tn") < dn._MIN_CLICKABLE_TN


def test_an_unreadable_version_does_not_cost_the_notification(on, run_spy, monkeypatch):
    dn._tn_versions.clear()
    monkeypatch.setattr(dn.sys, "platform", "darwin")
    monkeypatch.setattr(dn, "_macos_notifier", lambda: "/x/tn")
    monkeypatch.setattr(dn.shutil, "which", lambda n: "/usr/bin/osascript")
    monkeypatch.setattr(dn.subprocess, "run",
                        lambda a, **kw: subprocess.CompletedProcess(a, 0, stdout=b"??", stderr=b""))
    assert dn._macos_notifier_version("/x/tn") == ()
    assert dn.notify("t", "m", url=_URL) is True


def test_capability_stops_advertising_a_click_the_machine_refused(on, monkeypatch):
    """Once terminal-notifier has actually refused, the capability report has
    to say so. Version alone is not enough: a current build with no
    notification permission still cannot deliver a click."""
    monkeypatch.setattr(dn.sys, "platform", "darwin")
    monkeypatch.setattr(dn, "_macos_notifier", lambda: "/x/tn")
    monkeypatch.setattr(dn, "_macos_notifier_version", lambda p: (3, 1, 0))
    monkeypatch.setattr(dn, "_tn_refusal", {"reason": ""})
    assert dn.capability()["clickable"] is True

    monkeypatch.setattr(
        dn, "_tn_refusal",
        {"reason": "Notifications are not allowed for this application"})
    cap = dn.capability()
    assert cap["clickable"] is False
    assert "System Settings" in cap["reason"]
