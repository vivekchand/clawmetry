from __future__ import annotations
import sys
import os
from pathlib import Path


def _post_json(url, body, timeout=15):
    """POST JSON and return (result_dict, status).

    On 2xx: returns (parsed_json, 200).
    On HTTPError: returns ({"error": msg, "retry_after": int|None}, status_code).
    On other errors: returns ({"error": str(e)}, 0).
    """
    import urllib.request
    import urllib.error
    import json as _json

    data = _json.dumps(body).encode()
    req = urllib.request.Request(
        url, data=data, headers={"Content-Type": "application/json"}, method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return _json.loads(resp.read()), 200
    except urllib.error.HTTPError as e:
        raw = e.read().decode()
        try:
            payload = _json.loads(raw)
        except Exception:
            payload = {}
        return (
            {
                "error": payload.get("error") or raw[:200],
                "retry_after": payload.get("retry_after"),
            },
            e.code,
        )
    except Exception as e:
        return {"error": str(e)}, 0

# Auto-activate HTTP interceptor when CLAWMETRY_INTERCEPT=1
if os.environ.get("CLAWMETRY_INTERCEPT") == "1":
    try:
        from clawmetry import interceptor as _interceptor  # noqa: F401
    except Exception:
        pass


def _get_openclaw_dir():
    """Return the OpenClaw config directory, respecting CLAWMETRY_OPENCLAW_DIR env var."""
    import os

    return os.environ.get("CLAWMETRY_OPENCLAW_DIR", os.path.expanduser("~/.openclaw"))


def _get_nemoclaw_preset_script() -> str | None:
    """Return the local NemoClaw preset helper when nemoclaw is installed."""
    import shutil

    if not shutil.which("nemoclaw"):
        return None

    script_path = (
        Path(__file__).resolve().parent
        / "resources"
        / "add-nemoclaw-clawmetry-preset.sh"
    )
    if script_path.exists():
        return str(script_path)
    return None


def _print_nemoclaw_preset_hint(BOLD, CYAN, DIM) -> None:
    """Suggest installing the NemoClaw preset when the local helper is available."""
    script_path = _get_nemoclaw_preset_script()
    if not script_path:
        return

    print(f"  {BOLD('NemoClaw detected')}")
    print(f"  {DIM('To allow your NemoClaw sandboxes to reach ClawMetry Cloud, run:')}")
    print(f"    {CYAN(f'bash {script_path}')}")
    print()


def _maybe_apply_nemoclaw_preset(_input, BOLD, CYAN, DIM) -> None:
    """Offer to apply the NemoClaw preset immediately after onboarding."""
    import subprocess

    script_path = _get_nemoclaw_preset_script()
    if not script_path:
        return

    print(f"  {BOLD('NemoClaw detected')}")
    print(f"  {DIM('Apply the ClawMetry preset to your NemoClaw sandboxes now?')}")

    try:
        choice = _input("  → [Y/n]: ").strip().lower() or "y"
    except (EOFError, KeyboardInterrupt):
        choice = "n"
        print()

    if choice not in ("y", "yes"):
        print(
            f"  {DIM('Run this later if you want cloud access inside NemoClaw sandboxes:')}"
        )
        print(f"    {CYAN(f'bash {script_path}')}")
        print()
        return

    print()
    # The preset helper is a .sh script. Windows has no bash on PATH by
    # default, and Popen raises FileNotFoundError rather than returning a
    # non-zero code, which would abort onboarding instead of falling through
    # to the "run this manually" hint below.
    try:
        result = subprocess.run(["bash", script_path], check=False)
    except (FileNotFoundError, OSError):
        print(f"  {DIM('bash was not found on PATH.')}")
        result = None
    if result is not None and result.returncode == 0:
        print()
        return

    print(f"  {DIM('Preset setup did not complete. Run this manually:')}")
    print(f"    {CYAN(f'bash {script_path}')}")
    print()


def _maybe_offer_secure(_input, BOLD, CYAN, DIM) -> None:
    """Offer monitor-only agent security monitoring (numbat) after onboarding.

    Default-yes, but always ASKED: the hook install edits each harness's own
    config (Claude settings.json, Codex hooks.json, ...), which crosses
    ClawMetry's read-only default, so onboard never enables it silently
    (founder 2026-08-02 — visible [Y/n] over auto-on). The wizard answer IS
    the consent, so cmd_enable runs with yes=True and doesn't re-prompt."""
    try:
        from clawmetry.secure import cmd_enable, find_numbat
    except Exception:
        return
    try:
        if find_numbat():
            return  # already set up (or user's own install) — don't re-nag
    except Exception:
        return

    print(f"  {BOLD('Agent security monitoring')} {DIM('(recommended)')}")
    print(f"  {DIM('numbat (Perplexity, Apache-2.0) watches your agents for secret')}")
    print(f"  {DIM('exfiltration, permission bypasses and persistence; findings land in')}")
    print(f"  {DIM('the Security tab. Monitor-only: nothing is ever blocked. Installs')}")
    print(f"  {DIM('hooks into your agent configs; undo anytime: clawmetry secure disable')}")

    try:
        choice = _input("  → [Y/n]: ").strip().lower() or "y"
    except (EOFError, KeyboardInterrupt):
        # No interactive answer: never touch agent configs.
        choice = "n"
        print()
    if choice not in ("y", "yes"):
        print(f"  {DIM('Enable later:')} {CYAN('clawmetry secure enable')}")
        print()
        return

    print()
    import argparse as _ap

    try:
        rc = cmd_enable(_ap.Namespace(
            yes=True, port=None, emit_all=False, reinstall=False,
        ))
    except Exception as e:
        print(f"  ⚠️  Security setup did not complete: {e}")
        rc = 1
    if rc != 0:
        print(f"  {DIM('Try again later:')} {CYAN('clawmetry secure enable')}")
    print()


def _post_onboard_offers(_input, BOLD, CYAN, DIM) -> None:
    """Every terminal path of onboard runs the same optional extras."""
    _maybe_apply_nemoclaw_preset(_input, BOLD, CYAN, DIM)
    _maybe_offer_secure(_input, BOLD, CYAN, DIM)


_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _root not in sys.path:
    sys.path.insert(0, _root)


def _is_sync_running() -> bool:
    """Check if clawmetry.sync is running — no pgrep needed."""
    import os

    try:
        import psutil

        for p in psutil.process_iter(["cmdline"]):
            try:
                cmd = " ".join(p.info.get("cmdline") or [])
                if "clawmetry.sync" in cmd or "clawmetry/sync.py" in cmd:
                    return True
            except Exception:
                pass
        return False
    except ImportError:
        pass
    try:
        for pid_str in os.listdir("/proc"):
            if not pid_str.isdigit():
                continue
            try:
                cmdline = open(f"/proc/{pid_str}/cmdline").read().replace("\x00", " ")
                if "clawmetry.sync" in cmdline or "clawmetry/sync.py" in cmdline:
                    return True
            except Exception:
                pass
    except Exception:
        pass
    return False


def _count_sync_daemons() -> int:
    """Return number of running clawmetry.sync processes (best-effort)."""
    import subprocess as _sp
    try:
        r = _sp.run(
            ["pgrep", "-f", "clawmetry.sync"],
            capture_output=True, text=True, check=False,
        )
        if r.returncode == 0:
            return len([l for l in r.stdout.splitlines() if l.strip()])
    except Exception:
        pass
    return 0


def _kill_sync_daemon() -> None:
    """Kill clawmetry.sync processes — no pkill needed."""
    import os
    import signal

    try:
        import psutil

        for p in psutil.process_iter(["pid", "cmdline"]):
            try:
                cmd = " ".join(p.info.get("cmdline") or [])
                if "clawmetry.sync" in cmd or "clawmetry/sync.py" in cmd:
                    os.kill(p.pid, signal.SIGTERM)
            except Exception:
                pass
        return
    except ImportError:
        pass
    try:
        for pid_str in os.listdir("/proc"):
            if not pid_str.isdigit():
                continue
            try:
                cmdline = open(f"/proc/{pid_str}/cmdline").read().replace("\x00", " ")
                if "clawmetry.sync" in cmdline or "clawmetry/sync.py" in cmdline:
                    os.kill(int(pid_str), signal.SIGTERM)
            except Exception:
                pass
    except Exception:
        pass
    # macOS without psutil + no /proc — fall back to pkill (universally
    # available on Darwin/Linux/BSD).
    import shutil as _sh
    import subprocess as _sp2
    if _sh.which("pkill"):
        _sp2.run(
            ["pkill", "-f", "clawmetry.sync"],
            check=False, capture_output=True,
        )


def _kill_dashboard_processes() -> int:
    """SIGTERM running clawmetry dashboard/server processes (best-effort).

    Skips the current process and its parent so `clawmetry uninstall`
    (which itself runs from bin/clawmetry) never kills itself mid-run.
    Returns the number of processes signalled.
    """
    import signal
    import subprocess as _sp

    patterns = ("bin/clawmetry", "clawmetry/dashboard.py")
    skip = {os.getpid(), os.getppid()}
    killed = 0
    try:
        r = _sp.run(
            ["ps", "-axo", "pid=,command="],
            capture_output=True, text=True, check=False,
        )
        for line in r.stdout.splitlines():
            pid_str, _, cmd = line.strip().partition(" ")
            if not pid_str.isdigit() or int(pid_str) in skip:
                continue
            if any(p in cmd for p in patterns):
                try:
                    os.kill(int(pid_str), signal.SIGTERM)
                    killed += 1
                except Exception:
                    pass
    except Exception:
        pass
    return killed


def _windows_clawmetry_pids() -> list:
    """Enumerate ``(pid, cmdline)`` of clawmetry processes on Windows.

    CIM via PowerShell (no psutil dependency), restricted to python /
    clawmetry executables so an editor with a clawmetry file open can
    never match. Skips the current process and its parent so
    ``clawmetry uninstall`` (running from clawmetry.exe) never kills
    itself mid-run. Returns [] on any failure and on non-Windows.
    """
    if os.name != "nt":
        return []
    import json as _json
    import subprocess as _sp

    _patterns = (
        "-m clawmetry",
        "clawmetry.exe",
        "clawmetry\\sync.py",
        "clawmetry/sync.py",
        "clawmetry\\dashboard.py",
        "clawmetry/dashboard.py",
    )
    skip = {os.getpid(), os.getppid()}
    try:
        r = _sp.run(
            [
                "powershell", "-NoProfile", "-Command",
                "Get-CimInstance Win32_Process -Filter "
                "\"Name='python.exe' OR Name='pythonw.exe' OR Name='clawmetry.exe'\" "
                "| Select-Object ProcessId,CommandLine | ConvertTo-Json -Compress",
            ],
            capture_output=True, text=True, check=False, timeout=30,
        )
        if r.returncode != 0 or not (r.stdout or "").strip():
            return []
        data = _json.loads(r.stdout)
        if isinstance(data, dict):
            data = [data]
        out = []
        for entry in data:
            try:
                pid = int(entry.get("ProcessId") or 0)
            except (TypeError, ValueError):
                continue
            cmd = entry.get("CommandLine") or ""
            if pid and pid not in skip and any(p in cmd for p in _patterns):
                out.append((pid, cmd))
        return out
    except Exception:
        return []


def _stop_windows_processes() -> int:
    """Terminate clawmetry daemon/dashboard processes on Windows.

    Windows cannot delete files a live process holds open (WinError 32),
    so uninstall MUST take every clawmetry process down BEFORE purging
    files; skipping this crashed uninstall mid-purge on sync.log (#3914).
    Returns the number of processes terminated. Never raises.
    """
    import subprocess as _sp

    killed = 0
    for pid, _cmd in _windows_clawmetry_pids():
        try:
            r = _sp.run(
                ["taskkill", "/PID", str(pid), "/T", "/F"],
                capture_output=True, check=False, timeout=30,
            )
            if r.returncode == 0:
                killed += 1
        except Exception:
            pass
    return killed


def _safe_unlink(path, retries: int = 3, delay: float = 0.5) -> bool:
    """``unlink()`` that survives Windows file locks. True when the file is gone.

    A file some process still holds open (WinError 32) must produce a
    warning and let the purge continue; one locked file aborting the whole
    uninstall midway is how #3914 left half-uninstalled nodes behind.
    """
    import time as _time

    for attempt in range(retries):
        try:
            path.unlink(missing_ok=True)
            return True
        except OSError:
            if attempt + 1 < retries:
                _time.sleep(delay)
    print(f"  ⚠️  Could not remove {path} (still in use). Remove it manually.")
    return False


def _stop_existing_daemon() -> None:
    """Stop any running sync daemon, deregister old node, clear stale state."""
    import subprocess
    import platform
    import json
    from clawmetry.sync import STATE_FILE, LOG_FILE, CONFIG_FILE

    system = platform.system()

    # Read old config before stopping (to deregister old node_id)
    old_node_id = None
    old_api_key = None
    if CONFIG_FILE.exists():
        try:
            old_cfg = json.loads(CONFIG_FILE.read_text())
            old_node_id = old_cfg.get("node_id")
            old_api_key = old_cfg.get("api_key")
        except Exception:
            pass

    # Stop the daemon
    if system == "Darwin":
        label = "com.clawmetry.sync"
        plist = (
            __import__("pathlib").Path.home()
            / "Library"
            / "LaunchAgents"
            / f"{label}.plist"
        )
        subprocess.run(
            ["launchctl", "unload", str(plist)], check=False, capture_output=True
        )
    elif system == "Linux":
        if __import__("shutil").which("systemctl"):
            # Stop whichever scope owns it: --user (non-root) or system (root).
            for _scope in (["--user"], []):
                subprocess.run(
                    ["systemctl", *_scope, "stop", "clawmetry-sync"],
                    check=False,
                    capture_output=True,
                )
        # Belt-and-braces: also kill any bare background subprocess daemon.
        _kill_sync_daemon()

    # Send offline heartbeat for old node to deregister it from cloud
    if old_node_id and old_api_key:
        try:
            from clawmetry.sync import _post
            from datetime import datetime, timezone

            _post(
                "/ingest/heartbeat",
                {
                    "node_id": old_node_id,
                    "ts": datetime.now(timezone.utc).isoformat(),
                    "status": "offline",
                    "platform": platform.system(),
                },
                old_api_key,
                timeout=5,
            )
        except Exception:
            pass  # Best effort

    # Clear stale state so the new daemon does a fresh initial sync
    if STATE_FILE.exists():
        STATE_FILE.unlink()
    # Clear old log so it's clean
    if LOG_FILE.exists():
        LOG_FILE.write_text("")


def _is_headless() -> bool:
    """True when webbrowser.open() almost certainly can't reach a GUI on THIS host.

    Used only to ORDER the auth flows, never as a hard gate: the headless path is
    an interactive paste prompt (not a timed wait), so a wrong guess can never
    hang the CLI. macOS/Windows always have a usable browser. On Linux, no
    DISPLAY/WAYLAND or an SSH session means the browser would open on a DIFFERENT
    machine (the loopback callback can't reach this box). CLAWMETRY_NO_BROWSER=1
    forces it (for users who know their box, and for the live test).
    """
    if os.environ.get("CLAWMETRY_NO_BROWSER") == "1":
        return True
    if sys.platform in ("darwin", "win32"):
        return False
    no_display = not os.environ.get("DISPLAY") and not os.environ.get("WAYLAND_DISPLAY")
    ssh = bool(os.environ.get("SSH_CONNECTION") or os.environ.get("SSH_TTY") or os.environ.get("SSH_CLIENT"))
    return no_display or ssh


def _oauth_browser_login(provider: str, input_fn=input, api_call=None) -> str:
    """OAuth sign-in for `clawmetry connect` (GitHub / Google).

    Desktop: a one-shot 127.0.0.1 loopback server captures the cm_ key the cloud
    callback redirects back (the key never leaves 127.0.0.1). Headless/remote
    (SSH/VPS, no GUI): the loopback can't be reached by a browser on another
    machine, so we use a Claude-Code-style paste-code path instead. The CLI
    generates a PKCE verifier (kept in memory; only its SHA256 challenge leaves
    the process), the cloud shows a short single-use code, the user pastes it,
    and the CLI redeems code+verifier at /api/oauth/cli/exchange over INGEST_URL.
    Returns "" on timeout/skip/error so the caller falls back to email OTP.
    """
    import http.server
    import urllib.parse
    import webbrowser
    import time as _time
    import secrets as _secrets
    import hashlib as _hashlib
    import base64 as _base64

    from clawmetry.endpoints import app_url as _resolve_app_url
    app_base = _resolve_app_url()

    # PKCE: the verifier stays in CLI memory only; only its SHA256 (the
    # challenge) ever leaves this process, in the start URL.
    verifier = _base64.urlsafe_b64encode(_secrets.token_bytes(32)).rstrip(b"=").decode()
    challenge = _base64.urlsafe_b64encode(
        _hashlib.sha256(verifier.encode()).digest()).rstrip(b"=").decode()

    def _paste_path() -> str:
        """Headless paste-code path. No loopback; redeem over INGEST_URL."""
        url = f"{app_base}/api/oauth/{provider}/start?cli_paste=1&cc={challenge}"
        print(f"\n  Browser didn't open? Use the url below to sign in with {provider.title()}:\n  {url}\n")
        try:
            webbrowser.open(url)  # best-effort; no-ops on a headless box
        except Exception:
            pass
        code = input_fn("  Paste code here if prompted > ").strip()
        if not code or api_call is None:
            return ""
        resp = api_call("/api/oauth/cli/exchange", {"code": code, "verifier": verifier})
        if isinstance(resp, dict) and str(resp.get("api_key", "")).startswith("cm_"):
            print("  Account created. Welcome to ClawMetry." if resp.get("is_new")
                  else "  Welcome back.")
            return resp["api_key"]
        err = (resp or {}).get("error", "that code did not work") if isinstance(resp, dict) else "network error"
        print(f"  Sign-in could not be completed ({err}).")
        return ""

    # Headless/remote: skip loopback entirely and use the interactive paste path.
    if _is_headless():
        return _paste_path()

    # Desktop: one-shot loopback fast-path.
    captured = {}

    class _Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):  # noqa: N802
            params = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
            captured["token"] = (params.get("token") or [""])[0]
            ok = captured["token"].startswith("cm_")
            msg = ("You're connected. Return to your terminal."
                   if ok else "Sign-in failed. Return to your terminal and use email instead.")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(
                ("<!DOCTYPE html><html><head><meta charset='utf-8'><title>ClawMetry</title></head>"
                 "<body style='font-family:sans-serif;background:#0b0f1a;color:#e2e8f0;display:flex;"
                 "align-items:center;justify-content:center;height:100vh;margin:0'>"
                 "<div style='text-align:center'><div style='font-size:40px'>\U0001F99E</div>"
                 "<h2 style='font-weight:700'>" + msg + "</h2></div></body></html>").encode("utf-8")
            )

        def log_message(self, *args):  # silence default stderr request logging
            pass

    try:
        srv = http.server.HTTPServer(("127.0.0.1", 0), _Handler)
    except OSError:
        # Can't bind loopback -> fall through to the paste path rather than fail.
        return _paste_path()
    port = srv.server_address[1]
    url = f"{app_base}/api/oauth/{provider}/start?cli_port={port}"
    print(f"\n  Opening your browser to sign in with {provider.title()}.")
    print(f"  Browser didn't open? Use the url below to sign in:\n  {url}\n")
    try:
        webbrowser.open(url)
    except Exception:
        pass

    srv.timeout = 1
    deadline = _time.time() + 180
    try:
        while "token" not in captured and _time.time() < deadline:
            srv.handle_request()
    finally:
        srv.server_close()

    tok = captured.get("token", "")
    return tok if tok.startswith("cm_") else ""


def _get_api_key_interactive() -> str:
    """Interactive API key acquisition: GitHub/Google OAuth, email OTP, or paste."""
    import getpass
    import urllib.request
    import urllib.error
    import json as _json

    # When stdin is piped (e.g. curl | bash install), open /dev/tty so prompts work
    _tty = None
    if not sys.stdin.isatty():
        try:
            _tty = open("/dev/tty", "r")
        except OSError:
            pass

    if _tty is None and not sys.stdin.isatty():
        print("\n  ❌  Interactive sign-in needs a terminal.")
        print("  Run this in your own shell, or pass --key cm_xxx to skip the prompt.\n")
        sys.exit(1)

    def _input(prompt):
        """input() that reads from /dev/tty when stdin is a pipe."""
        if _tty is not None:
            sys.stdout.write(prompt)
            sys.stdout.flush()
            line = _tty.readline()
            return line.rstrip("\n")
        try:
            return input(prompt)
        except EOFError:
            print("\n  ❌  Interactive sign-in needs a terminal.")
            print("  Run this in your own shell, or pass --key cm_xxx to skip the prompt.\n")
            sys.exit(1)

    from clawmetry.endpoints import ingest_url as _resolve_ingest_url
    INGEST_URL = _resolve_ingest_url()

    def _api_call(path, body):
        result, status = _post_json(INGEST_URL.rstrip("/") + path, body)
        if isinstance(result, dict) and status and status >= 400:
            result["_status"] = status
        return result

    print()
    print("  Sign in with:")
    print("    [1] GitHub      [2] Google")
    print("    …or type your email to get a 6-digit code.")
    entry = _input("  > ").strip()

    # OAuth (GitHub / Google). Desktop uses a loopback browser hand-off; a
    # headless/remote box (SSH/VPS) uses a paste-code path. Falls back to email
    # on failure. _input is /dev/tty-aware (piped installs) and _api_call talks
    # to INGEST_URL, both required by the headless exchange.
    _provider = {"1": "github", "github": "github", "2": "google", "google": "google"}.get(entry.lower())
    if _provider:
        _key = _oauth_browser_login(_provider, input_fn=_input, api_call=_api_call)
        if _key:
            return _key
        print("  Couldn't complete browser sign-in. Let's use email instead.")
        entry = _input("  📧 Enter your email: ").strip()

    # If it's already an API key, return it directly
    if entry.startswith("cm_"):
        return entry

    # Email flow: send OTP
    import re as _re

    if not _re.match(r"^[^@]+@[^@]+\.[^@]+$", entry):
        print("  ❌  That doesn't look like a valid email.")
        entry = _input("  📧 Try again — your email: ").strip()
        if not _re.match(r"^[^@]+@[^@]+\.[^@]+$", entry):
            return getpass.getpass("  API key (cm_…): ").strip()

    email = entry.lower()

    def _send_code(addr):
        """Send an OTP to ``addr`` with the 503 backoff. Returns the response."""
        print(f"\n  📨 Sending code to {addr}…", end="", flush=True)
        rr = _api_call("/api/auth/email-otp", {"action": "send", "email": addr})
        if rr.get("_status") == 503:
            import time as _time

            retry_after = rr.get("retry_after") or 5
            try:
                retry_after = max(1, min(int(retry_after), 30))
            except (TypeError, ValueError):
                retry_after = 5
            print(f"\n  ⏳ Server's busy — retrying in {retry_after}s…", flush=True)
            _time.sleep(retry_after)
            print(f"  📨 Sending code to {addr}…", end="", flush=True)
            rr = _api_call("/api/auth/email-otp", {"action": "send", "email": addr})
        return rr

    # OTP loop with RECOVERY: a typo'd email or a code that never arrives must
    # never force a restart of the whole wizard (founder live-hit 2026-07-30).
    # At the code prompt: `r` resends, typing a different email switches to it,
    # blank input never burns an attempt; even three wrong codes offer a way
    # back before falling to the paste-an-API-key exit.
    while True:
        r = _send_code(email)
        if r.get("_status") == 503:
            print(" ❌")
            print("\n  Couldn't reach our servers right now.")
            print("  Please try `clawmetry connect` again in a minute.\n")
            sys.exit(1)
        if r.get("error"):
            print(f" ❌  {r['error']}")
            fix = _input("  Type a corrected email to retry, or press Enter to use an API key instead: ").strip()
            if "@" in fix:
                email = fix.lower()
                continue
            print("  Visit https://clawmetry.com/connect to get your API key.")
            return getpass.getpass("  API key (cm_…): ").strip()
        print(" ✅")
        print("  Typo in the email, or no code arriving? Type r to resend, or just type the right email.")
        print()

        wrong = 0
        switched = False
        while wrong < 3:
            otp = _input("  🔑 Enter the 6-digit code (r = resend): ").strip()
            if not otp:
                continue  # a stray Enter must not burn an attempt
            if otp.lower() in ("r", "resend"):
                rr = _send_code(email)
                print(" ✅" if not rr.get("error") and rr.get("_status") != 503 else f" ❌  {rr.get('error', 'server busy')}")
                continue
            if "@" in otp:
                # They typed an email at the code prompt: that IS the typo fix.
                email = otp.lower()
                switched = True
                break
            print("  Verifying…", end="", flush=True)
            r2 = _api_call(
                "/api/auth/email-otp", {"action": "verify", "email": email, "otp": otp}
            )
            if r2.get("error"):
                print(f" ❌  {r2['error']}")
                wrong += 1
                if wrong < 3:
                    print("  Try again (r = resend, or type a different email).")
                continue
            api_key = r2.get("api_key", "")
            if api_key.startswith("cm_"):
                is_new = r2.get("is_new", False)
                print(f" ✅  {'Account created' if is_new else 'Welcome back'}!")
                print()
                return api_key
            print(" ❌  Server returned an unexpected response.")
            wrong += 1
        if switched:
            continue  # send a code to the corrected address
        fix = _input("  Still stuck? Type a different email, r to resend, or press Enter to stop: ").strip()
        if fix.lower() in ("r", "resend"):
            continue
        if "@" in fix:
            email = fix.lower()
            continue
        break

    print()
    print("  Couldn't verify. Visit https://clawmetry.com/connect to get your key.")
    return getpass.getpass("  API key (cm_…): ").strip()


def _verify_key_ownership(api_key: str) -> None:
    """Require email OTP to prove key ownership (prevents misuse on shared machines)."""
    import urllib.request
    import urllib.error
    import json as _json

    _tty = None
    if not sys.stdin.isatty():
        try:
            _tty = open("/dev/tty", "r")
        except OSError:
            print("\n  ❌  OTP verification requires an interactive terminal.")
            print("  Run 'clawmetry connect --key cm_xxx' from an interactive shell,")
            print("  or use 'clawmetry setup' for the full setup wizard.\n")
            sys.exit(1)

    def _input(prompt):
        if _tty is not None:
            sys.stdout.write(prompt)
            sys.stdout.flush()
            return _tty.readline().rstrip("\n")
        return input(prompt)

    from clawmetry.endpoints import ingest_url as _resolve_ingest_url
    INGEST_URL = _resolve_ingest_url()

    def _api(path, body):
        result, status = _post_json(INGEST_URL.rstrip("/") + path, body)
        if isinstance(result, dict) and status and status >= 400:
            result["_status"] = status
        return result

    print()
    print("  🔐 Verify account ownership")
    print("  📨 Sending verification code…", end="", flush=True)
    r = _api("/api/auth/email-otp", {"action": "send_by_key", "api_key": api_key})
    if r.get("_status") == 503:
        import time as _time

        retry_after = r.get("retry_after") or 5
        try:
            retry_after = max(1, min(int(retry_after), 30))
        except (TypeError, ValueError):
            retry_after = 5
        print(f"\n  ⏳ Server's busy — retrying in {retry_after}s…", flush=True)
        _time.sleep(retry_after)
        print("  📨 Sending verification code…", end="", flush=True)
        r = _api("/api/auth/email-otp", {"action": "send_by_key", "api_key": api_key})
        if r.get("_status") == 503:
            print(" ❌")
            print("\n  Couldn't reach our servers right now.")
            print("  Please try this command again in a minute.\n")
            sys.exit(1)
    if r.get("error"):
        print(f" ❌  {r['error']}")
        sys.exit(1)
    _masked = r.get("masked_email", "your email")
    print(" ✅")
    print(f"  📧 Code sent to {_masked}")
    print()

    for attempt in range(3):
        otp = _input("  🔑 Enter the 6-digit code: ").strip()
        if not otp:
            continue
        # Verify using the masked email — server resolves from key
        # We need the real email for verify, so use a key-based verify too
        print("  Verifying…", end="", flush=True)
        r2 = _api(
            "/api/auth/email-otp",
            {"action": "verify_by_key", "api_key": api_key, "otp": otp},
        )
        if r2.get("error"):
            print(f" ❌  {r2['error']}")
            if attempt < 2:
                print("  Try again.")
            continue
        print(" ✅  Verified!")
        print()
        return

    print("  ❌  Verification failed.")
    sys.exit(1)


def _keychain_get(node_id: str) -> str:
    """Return workspace enc_key from OS keychain, or '' if unavailable."""
    try:
        import keyring  # optional: pip install keyring
        return keyring.get_password("clawmetry", f"workspace-key:{node_id}") or ""
    except Exception:
        return ""


def _keychain_set(node_id: str, key: str) -> None:
    """Store workspace enc_key in OS keychain; silently no-ops if keyring absent."""
    try:
        import keyring  # optional: pip install keyring
        keyring.set_password("clawmetry", f"workspace-key:{node_id}", key)
    except Exception:
        pass


def _reset_family_sync_marks() -> int:
    """Drop the family-runtime high-water marks so the next daemon pass
    re-ingests every session and pushes the full set to the cloud.

    Sessions ingested during local-only operation are stamped "done" in
    ``family_event_high_water``; without this reset, the first pass after
    ``clawmetry connect`` skips them all and the cloud account never sees
    the node's history. Local re-ingest is idempotent (PK upserts), so the
    only cost is one full re-read. Returns the number of session marks
    cleared (0 when there is nothing to backfill)."""
    import json as _json
    state_file = Path.home() / ".clawmetry" / "sync-state.json"
    try:
        with open(state_file, encoding="utf-8") as fh:
            state = _json.load(fh)
    except (FileNotFoundError, ValueError, OSError):
        return 0
    marks = state.pop("family_event_high_water", None)
    if not marks:
        return 0
    tmp = state_file.with_suffix(".json.tmp")
    with open(tmp, "w", encoding="utf-8") as fh:
        _json.dump(state, fh)
    os.replace(tmp, state_file)
    return len(marks)


def _cmd_connect(args) -> None:
    """clawmetry connect — validate key, save config, start daemon."""
    # #1937: respect the persistent local-only marker. If the user did
    # `clawmetry disconnect` (or set CLAWMETRY_NO_CLOUD=1), don't silently
    # re-prompt for an email on the next update / install.sh run. The
    # `--force` flag lets the user override after explicit confirmation.
    from clawmetry.config import is_cloud_disabled, NOCLOUD_MARKER_PATH
    # Sign in while KEEPING the nocloud marker: account + trial license yes,
    # data egress no. Set by the Case-B "keep local-only" answer below, or
    # passed in directly by onboard's Self-Hosted trial path (args.keep_local),
    # which has already asked its own questions and must not be re-prompted.
    _keep_local_signin = bool(getattr(args, "keep_local", False))
    if _keep_local_signin:
        # A fresh self-host machine has NO marker yet (the interactive
        # Case-B path below only runs when one already exists). Write it
        # BEFORE any config/daemon work: the daemon must never observe a
        # cm_ key without the marker, or it starts pushing (founder
        # live-hit 2026-08-09; the end-of-flow touch alone leaves a
        # window where a respawning daemon sees key-without-marker).
        try:
            from pathlib import Path as _P

            _P(NOCLOUD_MARKER_PATH).parent.mkdir(parents=True, exist_ok=True)
            _P(NOCLOUD_MARKER_PATH).touch(exist_ok=True)
        except Exception:
            pass
    if is_cloud_disabled() and not getattr(args, "force", False) and not _keep_local_signin:
        # Two cases here:
        #
        # (A) AUTOMATED invocation -- install.sh / curl|bash / wrappers that
        #     pass --key-only, --no-daemon, --key, or --enc-key. Refuse
        #     silently: the WHOLE point of #1937 was that updates must not
        #     silently re-prompt for an email. install.sh's `|| true`
        #     swallows the exit so the install completes cleanly.
        #
        # (B) INTERACTIVE invocation -- a human typed `clawmetry connect` in
        #     a terminal. Offer a one-time conversion choice: sign up for
        #     cloud (which removes the marker and proceeds with the normal
        #     flow), or stay local-only (which exits gracefully). This is the
        #     conversion moment without re-introducing the #1937 silent
        #     re-prompt.
        _automation_flag = (
            getattr(args, "key_only", False)
            or getattr(args, "no_daemon", False)
            or getattr(args, "key", None)
            or getattr(args, "enc_key", None)
        )
        _has_tty = sys.stdin.isatty()
        if not _has_tty:
            try:
                _tty_test = open("/dev/tty", "r")
                _tty_test.close()
                _has_tty = True
            except OSError:
                _has_tty = False

        if _automation_flag or not _has_tty:
            # Case A: silent refuse (preserves #1937 fix for install.sh).
            print("Cloud sync is disabled on this machine (local-only mode).")
            print(f"  Marker: {NOCLOUD_MARKER_PATH}")
            print( "  Env:    CLAWMETRY_NO_CLOUD=" + (os.environ.get("CLAWMETRY_NO_CLOUD") or "(unset)"))
            print()
            print("The local dashboard at http://localhost:8900 keeps working.")
            print("To re-enable cloud sync, remove the marker and re-run:")
            print(f"    rm {NOCLOUD_MARKER_PATH}")
            print( "    clawmetry connect")
            print("or run `clawmetry connect --force` to override once.")
            return

        # Case B: interactive conversion prompt.
        print()
        print("✨ ClawMetry is currently in LOCAL-ONLY mode.")
        print(f"   (marker: {NOCLOUD_MARKER_PATH})")
        print()
        print("Cloud sync is opt-in. With it you get:")
        print("   • a hosted dashboard at https://app.clawmetry.com/cloud")
        print("   • E2E-encrypted snapshot (your key never leaves the machine)")
        print("   • alerts, multi-node fleet view, weekly insights")
        print()
        print("What would you like to do?")
        print("   [1] Sign up for cloud (free trial, ~30s)")
        print("   [2] Keep local-only (no change)")
        print()
        try:
            _choice_src = (
                open("/dev/tty", "r") if not sys.stdin.isatty() else sys.stdin
            )
            sys.stdout.write("Choice [1/2]: ")
            sys.stdout.flush()
            _choice = (_choice_src.readline() or "").strip()
        except (OSError, KeyboardInterrupt, EOFError):
            _choice = ""

        if _choice != "1":
            # Keeping data local must NOT mean staying anonymous: identity is
            # what unlocks runtimes (the trial license), egress is a separate
            # decision (founder spec 2026-07-30 — answering "keep local-only"
            # used to silently drop the sign-in the user had just chosen).
            print()
            print("Staying local-only: your data will not leave this machine.")
            try:
                sys.stdout.write(
                    "Sign in anyway to unlock every runtime here with a free "
                    "7-day Pro trial license? [Y/n]: "
                )
                sys.stdout.flush()
                _t2 = (_choice_src.readline() or "").strip().lower()
            except (OSError, KeyboardInterrupt, EOFError):
                _t2 = "n"
            if _t2 in ("n", "no"):
                print()
                print("Staying local-only. Dashboard: http://localhost:8900")
                print(f"(To convert later: rm {NOCLOUD_MARKER_PATH} && clawmetry connect)")
                return
            _keep_local_signin = True
            print()

        # User chose cloud signup -- remove the marker, then fall through to
        # the normal connect flow below (it'll prompt for email + OTP).
        try:
            os.unlink(NOCLOUD_MARKER_PATH)
            print(f"✅ Removed local-only marker ({NOCLOUD_MARKER_PATH})")
        except FileNotFoundError:
            pass
        except OSError as _e:
            print(f"⚠️  Could not remove marker: {_e}")
            print("    Continuing anyway -- the connect flow may re-fail.")
        print()
    # Support piped stdin (curl | bash) — read from /dev/tty if needed
    _tty = None
    if not sys.stdin.isatty():
        try:
            _tty = open("/dev/tty", "r")
        except OSError:
            pass

    def _input(prompt):
        if _tty is not None:
            sys.stdout.write(prompt)
            sys.stdout.flush()
            return _tty.readline().rstrip("\n")
        return input(prompt)

    # Read existing config BEFORE stopping daemon (preserve node_id + encryption_key)
    _saved_node_id = ""
    _saved_enc_key = ""
    try:
        import json as _jcfg_pre

        _cfgpath_pre = os.path.expanduser("~/.clawmetry/config.json")
        _cfg_pre = _jcfg_pre.load(open(_cfgpath_pre))
        _saved_node_id = _cfg_pre.get("node_id", "")
        _saved_enc_key = _cfg_pre.get("encryption_key", "")
        _saved_api_key = _cfg_pre.get("api_key", "")
    except Exception:
        _saved_api_key = ""

    _stop_existing_daemon()
    from clawmetry.sync import validate_key, save_config
    import platform
    import socket

    api_key = getattr(args, "key", None) or os.environ.get("CLAWMETRY_API_KEY") or ""
    if not api_key:
        api_key = _get_api_key_interactive()

    if not api_key.startswith("cm_"):
        print("❌  Key must start with cm_")
        sys.exit(1)

    # Verify ownership via OTP when key is passed directly (not from interactive flow)
    # Skip if this key is already verified (saved in config) — enables Docker restarts
    # Skip too when --start-sync-now was passed: that is the flag the cloud
    # dashboard's copy-paste connect command carries, and a key shown there was
    # minted inside an already-authenticated (OTP-verified) web session, so a
    # second OTP here is pure onboarding friction. This does not lower the
    # actual security bar: the cm_ key is a bearer credential the server
    # accepts directly on /auth and ingest, so the client-side OTP never
    # stopped anyone who already holds the key.
    if getattr(args, "key", None):
        if _saved_api_key and api_key == _saved_api_key:
            pass  # Already verified — reconnecting with same key
        elif (
            getattr(args, "start_sync_now", False)
            or getattr(args, "defer_sync", False)
            or getattr(args, "keep_local", False)
        ):
            # Key from the authenticated dashboard command (--start-sync-now)
            # or the desktop onboarding's self-host path (--defer-sync). Both
            # flags only exist on machine-generated invocations whose key was
            # just minted in an OAuth/OTP-verified session. --defer-sync runs
            # non-interactively (no stdin), so an OTP prompt here doesn't just
            # add friction, it kills the sign-in: _verify_key_ownership exits 1
            # without a tty, the trial never provisions, and a self-host user
            # is left on the OSS tier with every runtime locked.
            pass
        else:
            from clawmetry.endpoints import is_custom_endpoint as _is_custom_ep
            if _is_custom_ep():
                pass  # Self-hosted server — no email-OTP service; /auth is the gate
            else:
                _verify_key_ownership(api_key)

    custom_name = getattr(args, "custom_node_id", None) or ""
    machine_hostname = custom_name or socket.gethostname()
    _existing_node_id = _saved_node_id
    _server_e2e = None
    print("Verifying your account… " if _keep_local_signin
          else "Connecting to ClawMetry Cloud… ", end="", flush=True)
    try:
        result = validate_key(
            api_key, hostname=machine_hostname, existing_node_id=_existing_node_id
        )
        node_id = result.get("node_id") or machine_hostname
        # Self-hosted servers may answer {"e2e": false} — data stays inside the
        # customer deployment, so blob encryption is optional there and the
        # server needs plaintext to serve fleet views / audit export.
        _server_e2e = result.get("e2e") if isinstance(result, dict) else None
        print("✅")
    except Exception as e:
        err = str(e)
        # Allow saving config if network/server issues (ingest may not be live yet)
        if any(
            x in err
            for x in ["443", "Connection", "unreachable", "405", "404", "timed out"]
        ):
            node_id = machine_hostname
            print(
                "⚠️  Could not reach server right now. Your config has been saved and will sync when connected."
            )
        else:
            print(f"❌  {e}")
            sys.exit(1)

    from clawmetry.sync import generate_encryption_key, _derive_key_for_storage

    # Accept CM_KEY=scroll://<mnemonic> env var — v5 node pairing flow (#1522).
    # Strip the scroll:// URI prefix; the bare mnemonic/key material then feeds
    # into the existing _derive_key_for_storage path just like --enc-key does.
    _cm_key_env = os.environ.get("CM_KEY", "")
    if _cm_key_env.startswith("scroll://"):
        _cm_key_env = _cm_key_env[len("scroll://"):]
    if _cm_key_env and not getattr(args, "enc_key", None):
        setattr(args, "enc_key", _cm_key_env)

    # Always prompt for encryption key — be transparent.
    # A typed passphrase is run through a strong salted KDF (scrypt) and we store
    # the DERIVED key, never the raw passphrase. A pasted real key is kept as-is.
    # Use --enc-key if provided (non-interactive sandbox/automated use).
    _enc_key_arg = getattr(args, "enc_key", None) or ""
    _kc_key = _keychain_get(node_id)  # '' when keyring not installed

    if _keep_local_signin:
        # No snapshots ever leave on this path — the E2E key ceremony is
        # noise (and printing a "keep this safe" secret mid-Self-Hosted run
        # reads like a cloud signup; founder live-hit 2026-07-30).
        enc_key = _kc_key or _saved_enc_key or generate_encryption_key()
    # A self-hosted server answering {"e2e": false} opts this node into
    # plaintext ingest (data never leaves the deployment; the server needs
    # plaintext for fleet views + audit export). An explicit --enc-key wins.
    _server_plaintext = (
        _server_e2e is False and not _enc_key_arg and not _keep_local_signin
    )
    print()
    if not _keep_local_signin and not _server_plaintext:
        print("🔐 Encryption key protects your data end-to-end.")

    # Non-interactive callers (--start-sync-now / --keep-local from the
    # dashboard's OTP paste-and-go and the desktop pane's apply_cm_key
    # subprocess; also any pipe/redirect where stdin isn't a TTY) must
    # never hit `input()` — the desktop pane runs connect with
    # capture_output=True and `input()` raises EOFError, killing the
    # whole subprocess and leaving the user paired-but-trial-less.
    # Founder 2026-08-13 hit exactly this: signed up via the desktop
    # pane cloud pane, saw `Cloud Connected` in the dashboard (my
    # _fallback_persist_cm_key from #4776 caught the failure and saved
    # the token), but `clawmetry status` showed Free with no trial
    # because the subprocess crashed BEFORE reaching
    # _activate_signup_trial. In non-interactive mode we silently keep
    # the existing key (keychain/config) or auto-generate one — the
    # user can re-key later from Settings if they want a custom secret.
    _non_interactive = (
        bool(getattr(args, "start_sync_now", False))
        or _keep_local_signin
        or not sys.stdin.isatty()
    )

    if _keep_local_signin:
        pass  # enc_key already chosen above, silently
    elif _server_plaintext:
        enc_key = ""
        print("🔓 Server requested plaintext ingest (self-hosted, E2E off).")
    elif _enc_key_arg:
        enc_key = _derive_key_for_storage(_enc_key_arg)
        print("  Using provided encryption key.")
    elif _kc_key:
        masked = _kc_key[:6] + "…" + _kc_key[-4:]
        print(f"  Key from OS keychain: {masked}")
        if _non_interactive:
            enc_key = _kc_key
        else:
            custom_key = _input("  Press Enter to keep it, or type a new one: ").strip()
            enc_key = _derive_key_for_storage(custom_key) if custom_key else _kc_key
    elif _saved_enc_key:
        masked = _saved_enc_key[:6] + "…" + _saved_enc_key[-4:]
        print(f"  Existing key: {masked}")
        if _non_interactive:
            enc_key = _saved_enc_key
        else:
            custom_key = _input("  Press Enter to keep it, or type a new one: ").strip()
            enc_key = _derive_key_for_storage(custom_key) if custom_key else _saved_enc_key
    else:
        if _non_interactive:
            enc_key = generate_encryption_key()
            print("  Encryption key auto-generated (change in Settings).")
        else:
            custom_key = _input(
                "  Enter a custom secret key (or press Enter to auto-generate): "
            ).strip()
            enc_key = _derive_key_for_storage(custom_key) if custom_key else generate_encryption_key()

    if enc_key:
        _keychain_set(node_id, enc_key)  # persist to OS keychain when available

    config = {
        "api_key": api_key,
        "node_id": node_id,
        "platform": platform.system(),
        "connected_at": __import__("datetime").datetime.now().isoformat(),
    }
    if enc_key:
        config["encryption_key"] = enc_key
    save_config(config)

    # Explicit connect is an opt-in to cloud: clear any local-only marker so the
    # daemon actually pushes (otherwise a prior local-only install / disconnect
    # leaves it ingesting to DuckDB only and the node never appears in cloud).
    # EXCEPT the keep-local sign-in: there the marker staying put is the point.
    if not _keep_local_signin:
        try:
            from clawmetry.config import enable_cloud as _enable_cloud
            if _enable_cloud():
                print("  Re-enabled cloud sync (was local-only)")
        except Exception:
            pass

    # Backfill guarantee: sessions ingested while the node ran local-only are
    # stamped "done" in the family high-water marks, so the first cloud-
    # connected pass would skip them all and the cloud dashboard would sit at
    # 0 sessions forever (founder live-hit 2026-07-29: local said Connected,
    # cloud said "No machines connected yet"). Clearing the marks makes the
    # next family pass re-ingest every session (idempotent PK upserts locally)
    # and push the full set to the newly connected account.
    if not _keep_local_signin:
        try:
            _cleared = _reset_family_sync_marks()
            if _cleared:
                print(f"  Queued {_cleared} existing session(s) for cloud backfill")
        except Exception:
            pass  # connect must never fail because of backfill housekeeping

    print()
    print(f"  Connected as: {node_id}")

    # Every successful sign-in mints-or-reuses the account's 7-day trial
    # license and activates it HERE (idempotent server-side) — including the
    # keep-local path, where the license is the entire reason to sign in.
    # Must run BEFORE the entitlement probe below: on a brand-new signup the
    # account is still FREE until this trial is minted, so a probe that ran
    # first would see "not entitled", install nothing, and print nothing —
    # even though the trial (unlocking every runtime) was about to activate
    # a moment later. (2026-08-06 Straive Windows onboarding: OTP verified,
    # `clawmetry status` correctly showed the trial active, but Runtimes
    # stayed "NOT syncing" because the wheel was probed-for before it existed
    # to be entitled to, and only the 30-min pro-entitlement watcher in
    # sync.py ever caught up.)
    _trial_activated = _activate_signup_trial()

    # Auto-provision clawmetry-pro for entitled cloud accounts (Starter/Pro/
    # Trial/Enterprise). The cloud is the single source of truth: license.py
    # probes /api/license/entitlement with this cm_ key first and only then
    # downloads+installs the closed-source wheel over HTTPS. A FREE account
    # installs nothing and this prints nothing. This NEVER blocks or crashes
    # connect — any failure (offline, server down, install error) is swallowed
    # and the node keeps running on the free runtimes (OpenClaw + NemoClaw).
    try:
        from clawmetry.license import auto_provision_pro
        _pro_installed, _pro_msg = auto_provision_pro(api_key, node_id)
        if _pro_installed:
            print("  Pro adapters installed - all 14 runtimes available.")
        elif _pro_msg:
            # Entitled but the wheel could not be installed right now; surface a
            # quiet hint without alarming the user (connect still succeeded).
            print(f"  Note: {_pro_msg}")
        elif _trial_activated:
            # The trial just activated (see message above) but this probe still
            # came back empty-handed - e.g. entitlement propagation lag rather
            # than an error. Don't leave the terminal looking like nothing
            # happened; the pro-entitlement watcher retries every ~30 min.
            print("  Pro runtimes are activating - run `clawmetry status` in "
                  "a few minutes to check, or they'll pick up automatically.")
    except Exception:
        pass  # connect must never fail because of pro provisioning

    if _keep_local_signin:
        # Belt-and-braces: the marker was never removed on this path, but a
        # future refactor must not accidentally flip a keep-local sign-in
        # into cloud sync.
        try:
            from pathlib import Path as _P

            _P(NOCLOUD_MARKER_PATH).parent.mkdir(parents=True, exist_ok=True)
            _P(NOCLOUD_MARKER_PATH).touch()
        except Exception:
            pass
        print()
        print("  Local-only kept: your data stays on this machine.")
        # --defer-sync means a supervisor (the desktop app) manages the
        # daemon and dashboard itself — spawning a second dashboard here
        # would race it for the DuckDB writer lock.
        if not getattr(args, "defer_sync", False):
            _dash_up = _ensure_local_dashboard()
            if _dash_up:
                print("  Dashboard: http://localhost:8900 (live now)")
            else:
                print("  Dashboard did not come up at http://localhost:8900. Start it: clawmetry")

    print()

    # --key-only: just save config, don't start daemon (for host-side NemoClaw OTP flow)
    if getattr(args, "key_only", False):
        print(f"  API key:      {api_key}")
        print(f"  Enc key:      {enc_key}")
        print()
        return

    # Skip enc key reminder when --enc-key was passed (automated/sandbox use)
    # and on keep-local sign-ins (no snapshot ever leaves; the secret is
    # cloud-viewer material and printing it reads like a cloud signup).
    if not _enc_key_arg and not _keep_local_signin:
        print("  Keep this secret key safe (like a password):")
        print(f"  {enc_key}")
        print()

    # --no-daemon: skip daemon start (managed by supervisord externally)
    if getattr(args, "no_daemon", False):
        print()
        return

    # Default (2026-06-01): start the sync daemon immediately on connect, so
    # the dashboard populates without an extra step. A user who runs
    # `clawmetry connect` wants their observability now; the previous deferred
    # default ("Sync is paused") was a confusing trap where the node never
    # heartbeated and the dashboard stayed empty. Pass `--defer-sync` to keep
    # the old behavior (e.g. provisioning a node you do not want syncing yet).
    # `--start-sync-now` no longer changes anything here (sync-on-connect is
    # the default); its remaining effect is upstream — it skips the ownership
    # OTP for keys pasted from the authenticated dashboard command.
    if getattr(args, "defer_sync", False):
        print("  Sync is paused (--defer-sync). Start it whenever you're ready:")
        print("    clawmetry sync")
        print()
    else:
        _start_daemon(config, args)

    if _keep_local_signin:
        # Self-Hosted stays self-hosted: no cloud dashboard URL, no secret
        # in a URL fragment, no browser hand-off to app.clawmetry.com
        # (founder live-hit 2026-07-30: the keep-local run ended by OPENING
        # the cloud fleet page — a betrayal of "everything stays on your
        # devices" even though zero data had synced).
        print()
        print("  All done! Your dashboard: http://localhost:8900")
        print()
        if not getattr(args, "defer_sync", False):
            try:
                import webbrowser
                webbrowser.open("http://localhost:8900")
            except Exception:
                pass
        return

    # Open browser with encryption key in URL fragment (never sent to server)
    # The #key=... fragment stays client-side — true E2E encryption
    _node_id = config.get("node_id", "")
    from clawmetry.endpoints import app_url as _resolve_app_url2
    _app_base_done = _resolve_app_url2()
    _dashboard_url = f"{_app_base_done}/cloud?token={api_key}#key={enc_key}&node={_node_id}"

    # Cloud includes the local dashboard too (the onboard copy promises
    # BOTH app.clawmetry.com and localhost:8900) — make it true, best-effort.
    _local_dash_up = _ensure_local_dashboard()

    print()
    print("  All done! Opening your dashboard...")
    print(f"  {_app_base_done}/cloud")
    if _local_dash_up:
        print("  Also on this machine: http://localhost:8900")
    print()

    # If this was a zero-friction connect (no real key), the node landed on a
    # temporary placeholder account and will NOT show under the user's real
    # login. Warn loudly with the exact relink command instead of letting them
    # discover a silent "0 nodes" later. No-op (+ skipped) for a keyed connect.
    _warn_if_placeholder_account(api_key)

    try:
        import webbrowser
        webbrowser.open(_dashboard_url)
    except Exception:
        pass


def _ensure_local_dashboard(port: int = 8900, wait_secs: float = 12.0) -> bool:
    """Make ``http://localhost:<port>`` actually serve the dashboard.

    For a local-only install the URL IS the product, and onboard used to
    print it while nothing listened (founder report 2026-07-29:
    ERR_CONNECTION_REFUSED straight after "Watching your agents locally") —
    the sync daemon was the only thing ever started. Any HTTP answer counts
    as alive (an auth page or 404 still proves a server); when the port is
    silent, register a KeepAlive launchd job on macOS or fall back to a
    detached subprocess, then poll within a hard bound (NEVER-HANG: this
    returns within ~``wait_secs`` no matter what). Returns True only when
    the port actually answered — callers print the truth either way.
    """
    import platform as _plat
    import subprocess as _sp
    import time as _t
    import urllib.error as _ue
    import urllib.request as _ur

    def _alive() -> bool:
        try:
            _ur.urlopen(f"http://127.0.0.1:{port}/", timeout=2)
            return True
        except _ue.HTTPError:
            return True  # the server answered; status code is irrelevant here
        except Exception:
            return False

    if _alive():
        return True

    exe = os.path.join(os.path.dirname(sys.executable), "clawmetry")
    cmd = ([exe, "--port", str(port)] if os.path.exists(exe)
           else [sys.executable, "-m", "clawmetry", "--port", str(port)])
    log_path = os.path.expanduser("~/.clawmetry/dashboard.log")
    system = _plat.system()
    started = False

    if system == "Darwin":
        try:
            from pathlib import Path as _P

            label = "com.clawmetry.dashboard"
            plist_path = _P.home() / "Library" / "LaunchAgents" / f"{label}.plist"
            # Use `python -m clawmetry` (not the console-script path) so the
            # plist stays valid if the venv is rebuilt without entry points.
            # The console-script path rots silently; the interpreter path is
            # stable across venv rebuilds (#4297).
            _launchd_cmd = [sys.executable, "-m", "clawmetry", "--port", str(port)]
            _args_xml = "\n".join(f"        <string>{a}</string>" for a in _launchd_cmd)
            plist = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>             <string>{label}</string>
    <key>ProgramArguments</key>
    <array>
{_args_xml}
    </array>
    <key>RunAtLoad</key>         <true/>
    <key>KeepAlive</key>         <true/>
    <key>StandardOutPath</key>   <string>{log_path}</string>
    <key>StandardErrorPath</key> <string>{log_path}</string>
    <key>ThrottleInterval</key>  <integer>30</integer>
</dict>
</plist>"""
            plist_path.parent.mkdir(parents=True, exist_ok=True)
            plist_path.write_text(plist)
            uid = os.getuid()
            r = _sp.run(
                ["launchctl", "bootstrap", f"gui/{uid}", str(plist_path)],
                capture_output=True, check=False,
            )
            if r.returncode != 0:
                # Already bootstrapped (e.g. re-onboard) — restart it; legacy
                # load for pre-10.11 launchctl.
                _sp.run(["launchctl", "kickstart", "-k", f"gui/{uid}/{label}"],
                        capture_output=True, check=False)
                _sp.run(["launchctl", "load", "-w", str(plist_path)],
                        capture_output=True, check=False)
            started = True
        except Exception:
            started = False

    if not started:
        try:
            os.makedirs(os.path.dirname(log_path), exist_ok=True)
            log = open(log_path, "ab")
            kw = {"stdout": log, "stderr": log, "stdin": _sp.DEVNULL}
            if system == "Windows":
                # CREATE_NO_WINDOW | CREATE_NEW_PROCESS_GROUP. NO_WINDOW (a
                # hidden console the daemon's own console-subsystem children
                # inherit), NOT DETACHED_PROCESS (no console at all): a
                # console-less parent's unflagged children each get a fresh
                # VISIBLE console — on Win11, a Windows Terminal tab that sits
                # on the user's screen for the daemon's lifetime (founder
                # report 2026-08-09, "open forever" window after self-update).
                kw["creationflags"] = 0x08000200
            else:
                kw["start_new_session"] = True
            _sp.Popen(cmd, **kw)
        except Exception:
            return False

    deadline = _t.time() + wait_secs
    while _t.time() < deadline:
        if _alive():
            return True
        _t.sleep(0.5)
    return _alive()


def _activate_signup_trial() -> bool:
    """Mint-or-reuse the signed-in account's 7-day trial license and
    activate it locally, unlocking every runtime on the license rail.

    Called at the end of every successful connect (founder spec 2026-07-30:
    identity is what unlocks runtimes — including when the user keeps their
    data local-only). Server-side it is idempotent: repeats reissue the
    SAME license with its ORIGINAL expiry, an expired trial comes back
    ``expired: true`` and gets an honest notice instead of a key.
    Best-effort: returns True only when a live trial key ended up
    activated; every failure path leaves the install exactly as it was.
    """
    try:
        import json as _jk
        import time as _tm
        import urllib.request as _ur

        cfg_path = os.path.expanduser("~/.clawmetry/config.json")
        try:
            with open(cfg_path, "r", encoding="utf-8") as _fh:
                api_key = (_jk.load(_fh).get("api_key") or "").strip()
        except Exception:
            return False
        if not api_key.startswith("cm_"):
            return False

        from clawmetry import license as _lic

        req = _ur.Request(
            _lic._cloud_base() + "/api/license/trial/signup",
            data=_jk.dumps({"api_key": api_key}).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with _ur.urlopen(req, timeout=15) as resp:
            body = _jk.loads(resp.read().decode())
        if not (isinstance(body, dict) and body.get("ok") and body.get("key")):
            return False
        if body.get("expired"):
            print("  Your 7-day Pro trial has ended. Keep every runtime: https://clawmetry.com/pricing")
            return False
        ok, _msg = _lic.activate(body["key"], node_id=_lic._node_id())
        if not ok:
            return False
        _left = max(1, int((float(body.get("expires_at", 0)) - _tm.time() + 86399) // 86400))
        _days = "day" if _left == 1 else "days"
        print(f"  Pro trial active: every runtime unlocked on this machine, {_left} {_days} left.")
        return True
    except Exception:
        return False


def _start_daemon(config: dict, args) -> None:
    """Start the sync daemon (as background process or system service)."""

    system = __import__("platform").system()

    if getattr(args, "foreground", False):
        print("Running in foreground (Ctrl+C to stop)…")
        from clawmetry.sync import run_daemon

        run_daemon()
        return

    if system == "Darwin":
        _register_launchd(config)
    elif system == "Linux":
        _register_systemd(config)
    elif os.name == "nt":
        # Windows has no launchd/systemd equivalent short of Task Scheduler.
        # Without a registered task the daemon (and with it, all auto-update
        # polling) does not survive a reboot/logoff/crash -- confirmed live
        # on the founder's own Windows box (2026-07-28, CHANGELOG #4146).
        # Register a logon-triggered, restart-on-failure scheduled task;
        # fall back to the old unsupervised subprocess if schtasks fails
        # (e.g. sandboxed/locked-down environments with no Task Scheduler
        # access) so `clawmetry connect`/`onboard` never hard-fails here.
        from clawmetry.daemon_registration import register_windows_task
        if not register_windows_task(config):
            _start_subprocess()
    else:
        _start_subprocess()


def _cmd_sync(args) -> None:
    """clawmetry sync — start the deferred sync daemon for an already-connected node."""
    import json
    from clawmetry.sync import CONFIG_FILE

    if not CONFIG_FILE.exists():
        print("❌  No clawmetry config found. Run `clawmetry connect` first.")
        sys.exit(1)

    try:
        config = json.loads(CONFIG_FILE.read_text())
    except Exception as e:
        print(f"❌  Could not read {CONFIG_FILE}: {e}")
        sys.exit(1)

    if not config.get("api_key"):
        print("❌  Config has no api_key. Run `clawmetry connect` first.")
        sys.exit(1)

    _verb = "Restarting" if getattr(args, "restart", False) else "Starting"
    print(f"  {_verb} sync daemon for {config.get('node_id', '<unknown>')}…")
    # _start_daemon already bootout+bootstraps (launchd) / restarts (systemd),
    # so it is itself a safe restart — `--restart` just makes the intent explicit.
    _start_daemon(config, args)
    if getattr(args, "restart", False):
        print("  ✅  Daemon restarted — re-checking entitlement & provisioning runtimes.")
    if not getattr(args, "foreground", False):
        print("  ✅  Sync daemon started.")


def _register_nemoclaw_sandbox_daemons() -> None:
    """Register a LaunchAgent per NemoClaw sandbox that keeps sync daemon alive via kubectl exec."""
    import subprocess
    import shutil
    import os
    import platform
    from xml.sax.saxutils import escape

    if platform.system() != "Darwin":
        return
    if not shutil.which("docker"):
        return

    try:
        r = subprocess.run(
            ["docker", "ps", "--format", "{{.Names}}"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        cluster = next(
            (n for n in r.stdout.splitlines() if "openshell-cluster" in n), None
        )
    except Exception:
        return
    if not cluster:
        return

    try:
        r = subprocess.run(
            [
                "docker",
                "exec",
                cluster,
                "kubectl",
                "get",
                "pods",
                "-n",
                "openshell",
                "--no-headers",
                "-o",
                "custom-columns=NAME:.metadata.name",
            ],
            capture_output=True,
            text=True,
            timeout=10,
        )
        pods = [
            p for p in r.stdout.splitlines() if p and not p.startswith("openshell-")
        ]
    except Exception:
        return

    launch_agents = __import__("pathlib").Path.home() / "Library" / "LaunchAgents"
    launch_agents.mkdir(parents=True, exist_ok=True)
    docker_path = shutil.which("docker") or "/usr/local/bin/docker"

    for pod in pods:
        label = f"com.clawmetry.sandbox.{escape(pod)}"
        pod_xml = escape(pod)
        plist_path = launch_agents / f"com.clawmetry.sandbox.{pod}.plist"
        sync_script = "/usr/local/lib/python3.11/dist-packages/clawmetry/sync.py"
        plist = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>             <string>{label}</string>
    <key>ProgramArguments</key>
    <array>
        <string>{docker_path}</string>
        <string>exec</string>
        <string>{cluster}</string>
        <string>kubectl</string>
        <string>exec</string>
        <string>-n</string>
        <string>openshell</string>
        <string>{pod_xml}</string>
        <string>--</string>
        <string>python3</string>
        <string>{sync_script}</string>
    </array>
    <key>RunAtLoad</key>         <true/>
    <key>KeepAlive</key>         <true/>
    <key>ThrottleInterval</key>  <integer>30</integer>
    <key>StandardOutPath</key>   <string>/tmp/clawmetry-{pod_xml}.log</string>
    <key>StandardErrorPath</key> <string>/tmp/clawmetry-{pod_xml}.log</string>
</dict>
</plist>"""
        plist_path.write_text(plist)
        uid = os.getuid()
        # Unload first in case it was already registered
        subprocess.run(
            ["launchctl", "bootout", f"gui/{uid}", str(plist_path)],
            capture_output=True,
            check=False,
        )
        r = subprocess.run(
            ["launchctl", "bootstrap", f"gui/{uid}", str(plist_path)],
            capture_output=True,
            check=False,
        )
        if r.returncode != 0:
            subprocess.run(
                ["launchctl", "load", "-w", str(plist_path)],
                capture_output=True,
                check=False,
            )
        print(f"  ✅  Sandbox daemon registered (launchd: {label})")


def _register_launchd(config: dict) -> None:
    from clawmetry.sync import LOG_FILE

    label = "com.clawmetry.sync"
    plist_path = (
        __import__("pathlib").Path.home()
        / "Library"
        / "LaunchAgents"
        / f"{label}.plist"
    )
    # Use the current interpreter (venv-aware) so the daemon finds clawmetry
    python = sys.executable
    plist = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>             <string>{label}</string>
    <key>ProgramArguments</key>
    <array>
        <string>{python}</string>
        <string>-m</string>
        <string>clawmetry.sync</string>
    </array>
    <key>EnvironmentVariables</key>
    <dict>
        <!-- Issue #1310: gateway WS tap is opt-in (PR #1228) because
             OpenClaw upstream may not grant operator.read scope. Default
             ON in the daemon plist so Telegram/Signal/Slack channel
             messages reach DuckDB on a fresh install; the tap silently
             no-ops on scope rejection (with a single warning) so this
             can't make things worse. -->
        <key>CLAWMETRY_ENABLE_WS_TAP</key><string>1</string>
    </dict>
    <key>RunAtLoad</key>         <true/>
    <key>KeepAlive</key>         <true/>
    <key>StandardOutPath</key>   <string>{LOG_FILE}</string>
    <key>StandardErrorPath</key> <string>{LOG_FILE}</string>
    <key>ThrottleInterval</key>  <integer>30</integer>
</dict>
</plist>"""

    plist_path.parent.mkdir(parents=True, exist_ok=True)
    plist_path.write_text(plist)
    import subprocess as _sp
    import os as _os

    uid = _os.getuid()
    # Use modern bootstrap (macOS 10.11+), fall back silently to legacy
    r = _sp.run(
        ["launchctl", "bootstrap", f"gui/{uid}", str(plist_path)],
        capture_output=True,
        check=False,
    )
    if r.returncode != 0:
        _sp.run(
            ["launchctl", "load", "-w", str(plist_path)],
            capture_output=True,
            check=False,
        )
    print(f"  Running in the background. {_daemon_mode_line(config)}")
    print("  To stop: clawmetry disconnect")


def _daemon_mode_line(config: dict) -> str:
    """Truthful one-liner for daemon registration: a LOCAL-ONLY node must
    never be told its data is syncing to the cloud (founder report
    2026-07-29 — this printed right above "Nothing leaves this machine")."""
    local = bool(isinstance(config, dict) and config.get("local_only"))
    if not local:
        try:
            from clawmetry.config import is_cloud_disabled

            local = is_cloud_disabled()
        except Exception:
            pass
    return ("Nothing leaves this machine." if local
            else "Your data is syncing to the cloud.")


def _register_systemd(config: dict) -> None:
    from clawmetry.sync import LOG_FILE
    import subprocess
    import shutil
    import os as _os
    from pathlib import Path as _Path

    label = "clawmetry-sync"
    python = sys.executable  # current interpreter (venv-aware)
    # `systemctl --user` needs a per-user D-Bus session, which root over SSH on a
    # VPS usually does NOT have (enable --now then fails with "Failed to connect
    # to bus" and the daemon silently never starts). So for root we install a
    # SYSTEM service (persists across reboots + actually starts); non-root uses a
    # --user service. Either way we VERIFY it came up and fall back to a detached
    # background subprocess if systemd is unavailable / failed.
    try:
        _is_root = _os.geteuid() == 0
    except Exception:
        _is_root = False

    if _is_root:
        service_dir = _Path("/etc/systemd/system")
        wanted_by = "multi-user.target"
        scope = []            # system scope: `systemctl ...`
        extra_unit = "User=root\n"
    else:
        service_dir = _Path.home() / ".config" / "systemd" / "user"
        wanted_by = "default.target"
        scope = ["--user"]    # user scope: `systemctl --user ...`
        extra_unit = ""

    unit = f"""[Unit]
Description=ClawMetry Cloud Sync Daemon
After=network.target

[Service]
ExecStart={python} -m clawmetry.sync
# Issue #1310 — gateway WS tap default-on so Telegram/Signal/Slack
# channel messages reach DuckDB. Tap silently no-ops on scope rejection.
Environment=CLAWMETRY_ENABLE_WS_TAP=1
{extra_unit}Restart=always
RestartSec=30
StandardOutput=append:{LOG_FILE}
StandardError=append:{LOG_FILE}

[Install]
WantedBy={wanted_by}
"""

    _installed = False
    if shutil.which("systemctl"):
        try:
            service_dir.mkdir(parents=True, exist_ok=True)
            (service_dir / f"{label}.service").write_text(unit)
            subprocess.run(["systemctl", *scope, "daemon-reload"],
                           check=False, capture_output=True)
            subprocess.run(["systemctl", *scope, "enable", "--now", label],
                           check=False, capture_output=True)
            # Verify it actually started (systemd may have refused, e.g. no
            # --user bus). Give it a moment, then check active OR the process.
            import time as _t
            _t.sleep(1.0)
            _chk = subprocess.run(["systemctl", *scope, "is-active", label],
                                  capture_output=True, text=True)
            _installed = _chk.stdout.strip() == "active" or _is_sync_running()
        except Exception:
            _installed = False

    if _installed:
        _how = "system service" if _is_root else "user service"
        print(f"  Running in the background as a systemd {_how}. {_daemon_mode_line(config)}")
        print("  To stop: clawmetry disconnect")
    else:
        if sys.stdout.isatty():
            print("  systemd unavailable here (container, or root with no --user session)")
            print("  — starting a background process instead…")
        _start_subprocess()


def _start_subprocess() -> None:
    import subprocess
    import shutil

    import os as _os

    sync_script = str(__import__("pathlib").Path(__file__).parent / "sync.py")
    log_path = __import__("pathlib").Path.home() / ".clawmetry" / "sync.log"
    # A fresh install may not have ~/.clawmetry yet; open(..., "a") would raise.
    try:
        log_path.parent.mkdir(parents=True, exist_ok=True)
    except Exception:
        pass
    log_file = str(log_path)

    # Use setsid if available — ensures daemon survives kubectl exec session end
    cmd = (
        ["setsid", sys.executable, sync_script]
        if shutil.which("setsid")
        else [sys.executable, sync_script]
    )

    spawn_kwargs = {"stdin": subprocess.DEVNULL, "close_fds": True}
    if _os.name == "nt":
        # start_new_session is POSIX-only and silently no-ops on Windows, which
        # left the daemon inside the launching console's process group: closing
        # that window delivered CTRL_CLOSE_EVENT and killed the daemon with it.
        # CREATE_NO_WINDOW gives the daemon its OWN (hidden) console — cut
        # loose from the launching terminal like DETACHED_PROCESS, but unlike
        # DETACHED its console-subsystem children inherit the hidden console
        # instead of each allocating a fresh VISIBLE one (founder report
        # 2026-08-09: persistent Windows Terminal tab after self-update).
        # The new process group still stops parent-terminal Ctrl+C propagating.
        spawn_kwargs["creationflags"] = (
            subprocess.CREATE_NO_WINDOW | subprocess.CREATE_NEW_PROCESS_GROUP
        )
    else:
        spawn_kwargs["start_new_session"] = True

    # The child inherits a duplicate of this handle, so closing ours right
    # after the spawn is correct and avoids leaking it for the CLI's lifetime.
    log_fh = open(log_file, "a")
    try:
        proc = subprocess.Popen(
            cmd, stdout=log_fh, stderr=subprocess.STDOUT, **spawn_kwargs
        )
    finally:
        try:
            log_fh.close()
        except Exception:
            pass
    print(f"✅  Sync daemon started (pid {proc.pid})")


def _cmd_disconnect(args) -> None:
    """clawmetry disconnect — stop daemon and remove key."""
    import subprocess
    from clawmetry.sync import CONFIG_FILE, STATE_FILE
    import platform

    system = platform.system()
    if system == "Darwin":
        label = "com.clawmetry.sync"
        plist = (
            __import__("pathlib").Path.home()
            / "Library"
            / "LaunchAgents"
            / f"{label}.plist"
        )
        subprocess.run(
            ["launchctl", "unload", str(plist)], check=False, capture_output=True
        )
        if plist.exists():
            plist.unlink()
        print(f"✅  Stopped launchd daemon ({label})")
    elif system == "Linux":
        if __import__("shutil").which("systemctl"):
            # Disable + stop whichever scope owns it (--user for non-root, system
            # for root) so Restart=always can't bring it back, then remove the
            # unit file from both possible locations.
            from pathlib import Path as _P2
            for _scope in (["--user"], []):
                subprocess.run(
                    ["systemctl", *_scope, "disable", "--now", "clawmetry-sync"],
                    check=False,
                    capture_output=True,
                )
            for _svc in (_P2.home() / ".config" / "systemd" / "user" / "clawmetry-sync.service",
                         _P2("/etc/systemd/system/clawmetry-sync.service")):
                try:
                    if _svc.exists():
                        _svc.unlink()
                except Exception:
                    pass
            subprocess.run(["systemctl", "--user", "daemon-reload"], check=False, capture_output=True)
            subprocess.run(["systemctl", "daemon-reload"], check=False, capture_output=True)
        _kill_sync_daemon()  # also kill any bare subprocess daemon
        print("✅  Stopped sync daemon")

    if CONFIG_FILE.exists():
        CONFIG_FILE.unlink()
        print(f"✅  Removed config ({CONFIG_FILE})")
    if STATE_FILE.exists():
        STATE_FILE.unlink()

    # Drop the stale sync-progress file so the dashboard banner ("Step:
    # crons · about 2m remaining") doesn't freeze on the last phase the
    # daemon was in before we unloaded it. The file only ever describes
    # cloud-sync progress; with cloud off it's pure misinformation.
    from pathlib import Path as _Path
    _prog = _Path.home() / ".clawmetry" / "sync_progress.json"
    if _prog.exists():
        try:
            _prog.unlink()
            print(f"✅  Cleared sync-progress file ({_prog})")
        except Exception as _e:
            print(f"⚠️  Could not remove {_prog}: {_e}")

    # Drop the persistent local-only marker so a future `clawmetry update`
    # / `install.sh` / `clawmetry connect` won't silently re-prompt for an
    # email and reconnect. Survives across updates. Undo with:
    #     rm ~/.clawmetry/nocloud
    # or env CLAWMETRY_NO_CLOUD=0 for a one-off override (#1937).
    from clawmetry.config import NOCLOUD_MARKER_PATH
    try:
        _Path(NOCLOUD_MARKER_PATH).parent.mkdir(parents=True, exist_ok=True)
        _Path(NOCLOUD_MARKER_PATH).touch()
        print(f"✅  Cloud sync disabled persistently ({NOCLOUD_MARKER_PATH})")
        print("   The local dashboard at http://localhost:8900 still works.")
        print(f"   To re-enable later: rm {NOCLOUD_MARKER_PATH} && clawmetry connect")
    except Exception as _e:
        print(f"⚠️  Could not write opt-out marker: {_e}")

    print("Disconnected from ClawMetry Cloud.")


def _get_nemoclaw_sandboxes() -> list:
    """Return list of NemoClaw sandbox pod names if docker + nemoclaw available."""
    import subprocess
    import shutil
    import os

    # Augment PATH with common macOS install locations
    extra = ["/opt/homebrew/bin", "/usr/local/bin", os.path.expanduser("~/.local/bin")]
    env = os.environ.copy()
    env["PATH"] = ":".join(extra) + ":" + env.get("PATH", "")

    def _which(cmd):
        return shutil.which(cmd, path=env["PATH"])

    if not _which("docker") or not _which("nemoclaw"):
        return []
    try:
        docker = _which("docker")
        r = subprocess.run(
            [docker, "ps", "--format", "{{.Names}}"],
            capture_output=True,
            text=True,
            timeout=5,
            env=env,
        )
        cluster = next(
            (n for n in r.stdout.splitlines() if "openshell-cluster" in n), None
        )
        if not cluster:
            return []
        r2 = subprocess.run(
            [
                docker,
                "exec",
                cluster,
                "kubectl",
                "get",
                "pods",
                "-n",
                "openshell",
                "--no-headers",
                "-o",
                "custom-columns=NAME:.metadata.name",
            ],
            capture_output=True,
            text=True,
            timeout=10,
            env=env,
        )
        return [
            p for p in r2.stdout.splitlines() if p and not p.startswith("openshell-")
        ]
    except Exception:
        return []


def _uninstall_nemoclaw_sandbox(
    cluster: str, pod: str, docker_bin: str = "docker"
) -> None:
    """Stop supervisord daemon and remove ClawMetry config from a NemoClaw sandbox."""
    import subprocess

    cmd = (
        "supervisorctl -c /etc/supervisor/supervisord.conf stop clawmetry-sync 2>/dev/null || true; "
        "supervisorctl -c /etc/supervisor/supervisord.conf shutdown 2>/dev/null || true; "
        "sleep 1; "
        "rm -rf /sandbox/.clawmetry /root/.clawmetry; "
        "rm -f /etc/supervisor/conf.d/clawmetry-sync.conf /etc/supervisor/supervisord.conf; "
        "pip uninstall -y --break-system-packages clawmetry 2>/dev/null || true"
    )
    try:
        subprocess.run(
            [
                docker_bin,
                "exec",
                cluster,
                "kubectl",
                "exec",
                "-n",
                "openshell",
                pod,
                "--",
                "bash",
                "-c",
                cmd,
            ],
            capture_output=True,
            timeout=30,
        )
    except Exception:
        pass


def _desktop_runtime_dir() -> "Path":
    """Where the desktop thin-shell keeps its runtime venv + logs.
    Mirrors ``desktop/app.py::_runtime_dir`` (kept in sync there). We
    reimplement it here so the uninstall path doesn't have to import
    the desktop package (which pulls pywebview into the CLI process).

        macOS   ~/Library/Application Support/ClawMetry
        Windows %LOCALAPPDATA%/ClawMetry
        Linux   ~/.local/share/ClawMetry  (or $XDG_DATA_HOME/ClawMetry)
    """
    import platform as _pl
    from pathlib import Path as _P

    system = _pl.system()
    if system == "Darwin":
        return _P.home() / "Library" / "Application Support" / "ClawMetry"
    if system == "Windows":
        return _P(os.environ.get("LOCALAPPDATA", str(_P.home()))) / "ClawMetry"
    return _P(
        os.environ.get("XDG_DATA_HOME", str(_P.home() / ".local" / "share"))
    ) / "ClawMetry"


def _openclaw_sidecar_paths() -> list:
    """Files under ``~/.openclaw`` that ClawMetry owns and is safe to
    remove on uninstall. Deliberately excludes ``openclaw.json`` — that
    file belongs to OpenClaw; we only strip our ``clawmetry`` key from
    it in a separate step."""
    from pathlib import Path as _P

    home = _P.home()
    oc = home / ".openclaw"
    paths = [
        oc / "clawmetry.db",
        oc / "clawmetry.db-shm",
        oc / "clawmetry.db-wal",
        oc / "clawmetry-alerts.json",
        oc / ".clawmetry",  # insights_config.json lives here
        oc / "workspace" / ".clawmetry-fleet.db",
        oc / "workspace" / ".clawmetry-fleet.db-shm",
        oc / "workspace" / ".clawmetry-fleet.db-wal",
        oc / "workspace" / ".clawmetry-metrics.json",
    ]
    return [p for p in paths if p.exists()]


def _strip_clawmetry_from_openclaw_json() -> "tuple[bool, str]":
    """Remove the ``clawmetry`` key from ``~/.openclaw/openclaw.json``.

    Leaves the rest of the file intact so OpenClaw keeps working. If
    the resulting object is empty, delete the file so a fresh install
    doesn't inherit an empty stub. Returns (changed, path)."""
    import json as _json
    from pathlib import Path as _P

    p = _P.home() / ".openclaw" / "openclaw.json"
    if not p.exists():
        return False, str(p)
    try:
        with p.open() as f:
            data = _json.load(f)
    except Exception:
        return False, str(p)
    if not isinstance(data, dict) or "clawmetry" not in data:
        return False, str(p)
    del data["clawmetry"]
    try:
        if not data:
            p.unlink()
        else:
            with p.open("w") as f:
                _json.dump(data, f, indent=2)
        return True, str(p)
    except Exception:
        return False, str(p)


def _cmd_uninstall(args=None) -> None:
    """clawmetry uninstall — fully remove clawmetry, stop daemons, delete all files.

    Flags (all optional; if ``args`` is None the interactive default holds):

        --yes / -y     skip the interactive "type uninstall to confirm" prompt.
                       Required for the desktop-app menu shell-out and the
                       app-vanished watchdog.
        --unattended   non-interactive, quiet, exit 0 even on partial failure.
                       Implies --yes. This is what the macOS app-vanished
                       watchdog uses.
        --keep-data    preserve DuckDB local store + history.db (users who
                       want their event history to survive a reinstall).
        --dry-run      list everything that would be removed without touching
                       disk.
    """
    import shutil
    import platform
    import subprocess
    from pathlib import Path
    from clawmetry.sync import CONFIG_FILE, STATE_FILE, LOG_FILE

    _yes = bool(getattr(args, "yes", False) or getattr(args, "unattended", False))
    _unattended = bool(getattr(args, "unattended", False))
    _keep_data = bool(getattr(args, "keep_data", False))
    _dry_run = bool(getattr(args, "dry_run", False))

    def _say(msg: str) -> None:
        if not _unattended:
            print(msg)

    # Under --unattended (watchdog-driven), silence every remaining `print`
    # in this function so the LaunchAgent's log stays clean. We restore
    # stdout on the way out.
    _orig_stdout = sys.stdout
    if _unattended:
        try:
            sys.stdout = open(os.devnull, "w")  # noqa: SIM115 — restored below
        except Exception:
            pass

    home = Path.home()
    system = platform.system()

    # Collect what will be removed
    items = []

    # 1. Daemons — every com.clawmetry.* job (sync, dashboard, sandbox.*),
    # not just sync. The dashboard agent has KeepAlive, so missing it here
    # leaves a launchd job that resurrects the server after uninstall.
    daemon_plists: list = []
    daemon_units: list = []
    if system == "Darwin":
        la_dir = home / "Library" / "LaunchAgents"
        daemon_plists = sorted(la_dir.glob("com.clawmetry.*.plist"))
        for plist in daemon_plists:
            items.append(("Daemon", f"launchd service: {plist}"))
    elif system == "Linux":
        sysd_user = home / ".config" / "systemd" / "user"
        daemon_units = sorted(sysd_user.glob("clawmetry*.service"))
        for svc in daemon_units:
            items.append(("Daemon", f"systemd service: {svc}"))
        if _is_sync_running():
            items.append(("Daemon", "Running sync process"))

    # 2. Config files
    clawmetry_dir = home / ".clawmetry"
    if clawmetry_dir.exists():
        items.append(("Config", f"Config directory: {clawmetry_dir}"))
    if CONFIG_FILE.exists():
        items.append(("Config", f"Cloud config: {CONFIG_FILE}"))
    if STATE_FILE.exists():
        items.append(("State", f"Sync state: {STATE_FILE}"))
    if LOG_FILE.exists():
        items.append(("Logs", f"Sync log: {LOG_FILE}"))

    # 3. Venv install paths
    venv_paths = [
        Path("/opt/clawmetry"),
        home / ".clawmetry",
    ]
    for vp in venv_paths:
        if vp.exists() and (vp / "bin" / "clawmetry").exists():
            items.append(("Install", f"Venv install: {vp}"))

    # 4. Symlinks
    symlinks = [
        Path("/usr/local/bin/clawmetry"),
        home / ".local" / "bin" / "clawmetry",
    ]
    for sl in symlinks:
        if sl.exists() or sl.is_symlink():
            items.append(("Symlink", f"Binary: {sl}"))

    # 5. NemoClaw sandboxes
    _nemoclaw_sandboxes = _get_nemoclaw_sandboxes()
    for _sb in _nemoclaw_sandboxes:
        items.append(
            ("NemoClaw", f"Sandbox {_sb}: stop daemon, remove config + clawmetry")
        )

    # 6. Desktop thin-shell runtime (~/Library/Application Support/ClawMetry etc.)
    # The .app itself lives in /Applications and is user-managed (drag-to-trash),
    # but the pip-managed venv, bootstrap.log, and onboarding-completed.json
    # under the runtime dir are ours to wipe. This is the piece that was
    # silently surviving drag-to-trash and auto-logging the user back in on
    # reinstall (support thread 2026-08-12).
    _desktop_runtime = _desktop_runtime_dir()
    if _desktop_runtime.exists():
        items.append(("Desktop", f"Desktop runtime dir: {_desktop_runtime}"))

    # 7. OpenClaw sidecar files ClawMetry owns (SQLite anomalies, fleet DB,
    # insights config, alerts JSON). We DON'T touch ~/.openclaw/openclaw.json
    # here — that file belongs to OpenClaw. The clawmetry.cloudToken key
    # inside it is stripped separately (see step 8).
    _oc_sidecar = _openclaw_sidecar_paths()
    for _p in _oc_sidecar:
        items.append(("Sidecar", f"OpenClaw sidecar file: {_p}"))

    # 8. Cloud token embedded in ~/.openclaw/openclaw.json — the *file* is
    # OpenClaw's, but the `clawmetry.cloudToken` key inside it is what caused
    # the "auto-logged-in after drag-to-trash reinstall" surprise. Strip that
    # key only. If openclaw.json ends up empty, the strip step deletes it.
    _oc_json = home / ".openclaw" / "openclaw.json"
    if _oc_json.exists():
        try:
            import json as _json_probe
            with _oc_json.open() as _f:
                _oc_data = _json_probe.load(_f)
            if isinstance(_oc_data, dict) and "clawmetry" in _oc_data:
                items.append(
                    ("Token", f"Strip clawmetry.cloudToken from: {_oc_json}")
                )
        except Exception:
            pass

    # 9. pip package
    items.append(("Package", "pip package: clawmetry"))

    if _keep_data:
        # Filter out the DuckDB/SQLite/fleet DBs while keeping the runtime,
        # config, and daemon teardown intact. This is the "I want to reinstall
        # later and pick up where I left off" path.
        def _is_data(cat: str, detail: str) -> bool:
            data_hints = (
                "clawmetry.db",
                ".clawmetry-fleet",
                "clawmetry.duckdb",
                "history.db",
                "Config directory",  # ~/.clawmetry holds the DuckDB
            )
            return any(hint in detail for hint in data_hints)

        items = [(c, d) for (c, d) in items if not _is_data(c, d)]

    def _restore_stdout():
        if sys.stdout is not _orig_stdout:
            try:
                sys.stdout.close()
            except Exception:
                pass
            sys.stdout = _orig_stdout

    if not items:
        _say("  Nothing to uninstall. ClawMetry does not appear to be installed.")
        _restore_stdout()
        return

    if _dry_run:
        _say("")
        _say("  \033[1mDry run — no files touched.\033[0m")
        _say("")
        for category, detail in items:
            _say(f"    \033[93m•\033[0m  [{category}] {detail}")
        _say("")
        _restore_stdout()
        return

    # Show confirmation (skipped under --yes / --unattended)
    if not _yes:
        print()
        print("  \033[1m\033[91m⚠️  ClawMetry Uninstall\033[0m")
        print("  \033[2m" + "─" * 50 + "\033[0m")
        print()
        print("  The following will be removed:")
        print()
        for category, detail in items:
            print(f"    \033[91m✗\033[0m  [{category}] {detail}")
        print()
        print("  \033[2mThis action is irreversible. Your encryption key and cloud")
        print("  config will be permanently deleted.\033[0m")
        print()

        try:
            confirm = input("  Type 'uninstall' to confirm: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n  Cancelled.")
            return

        if confirm != "uninstall":
            print("  Cancelled.")
            return

        print()

    # Execute uninstall
    # 0. Purge server-side registration (node_registry + node data)
    try:
        import json as _json_u
        cfg_path = home / ".clawmetry" / "config.json"
        if cfg_path.exists():
            with open(cfg_path) as _f:
                _cfg = _json_u.load(_f)
            _api_key = _cfg.get("api_key", "")
            _node_id = _cfg.get("node_id", "")
            if _api_key:
                import socket, threading
                _hostname = socket.gethostname()
                def _purge_server():
                    try:
                        import urllib.request
                        from clawmetry.endpoints import app_url as _resolve_app_url
                        _req = urllib.request.Request(
                            _resolve_app_url() + "/api/unregister",
                            data=_json_u.dumps({
                                "node_id": _node_id,
                                "hostname": _hostname,
                            }).encode(),
                            headers={
                                "X-Api-Key": _api_key,
                                "Content-Type": "application/json",
                            },
                            method="POST",
                        )
                        with urllib.request.urlopen(_req, timeout=120) as _resp:
                            pass
                    except Exception:
                        pass
                _t = threading.Thread(target=_purge_server, daemon=True)
                _t.start()
                print("  ⏳  Purging server-side registration (background)...")
    except Exception:
        pass

    # 1. Stop daemons. Boot the launchd jobs out BEFORE deleting any files:
    # the dashboard agent has KeepAlive, so a plist left registered restarts
    # the server (even from a deleted ~/.clawmetry, whose files it holds open).
    if system == "Darwin":
        uid = os.getuid()
        for plist in daemon_plists:
            label = plist.stem
            r = subprocess.run(
                ["launchctl", "bootout", f"gui/{uid}/{label}"],
                check=False, capture_output=True,
            )
            if r.returncode != 0:  # older macOS without bootout
                subprocess.run(
                    ["launchctl", "unload", str(plist)],
                    check=False, capture_output=True,
                )
            plist.unlink(missing_ok=True)
            print(f"  ✅  Stopped and removed launchd service: {label}")
        # Belt-and-suspenders: kill any sync daemons started by hand (not via
        # launchd). Without this, install.sh's pkill is the only thing that takes
        # them down, which surfaces to the user as "Killed stray pre-existing
        # daemon" right after a 'clean' uninstall — undermining trust that
        # uninstall actually worked.
        _stray = _count_sync_daemons()
        if _stray > 0:
            _kill_sync_daemon()
            print(f"  ✅  Killed {_stray} stray sync process(es)")
    elif system == "Linux":
        _unit_names = {svc.stem for svc in daemon_units} | {"clawmetry-sync"}
        _svcs = list(daemon_units) + [
            __import__("pathlib").Path("/etc/systemd/system/clawmetry-sync.service")
        ]
        if shutil.which("systemctl"):
            for _unit in sorted(_unit_names):
                for _scope in (["--user"], []):  # --user (non-root) + system (root)
                    subprocess.run(
                        ["systemctl", *_scope, "disable", "--now", _unit],
                        check=False,
                        capture_output=True,
                    )
        _stray = _count_sync_daemons()
        _kill_sync_daemon()
        for svc in _svcs:
            try:
                if svc.exists():
                    svc.unlink()
            except Exception:
                pass
        print("  ✅  Stopped and removed sync daemon" + (f" + {_stray} stray process(es)" if _stray else ""))
    elif system == "Windows":
        # No service manager here (daemon runs as a plain process or a
        # Scheduled Task child). Stop every clawmetry process BEFORE the
        # purge: Windows cannot delete files a live process holds open, so
        # a running daemon crashed uninstall on its own sync.log (#3914).
        _stray_win = _stop_windows_processes()
        if _stray_win:
            print(f"  ✅  Stopped {_stray_win} clawmetry process(es)")
    # The bootout above kills launchd-managed processes; this sweeps up
    # dashboards started by hand (clawmetry --port ...). POSIX only; the
    # Windows sweep above already covers dashboards.
    _stray_dash = 0 if system == "Windows" else _kill_dashboard_processes()
    if _stray_dash:
        print(f"  ✅  Killed {_stray_dash} dashboard process(es)")

    # 2. Pip uninstall (BEFORE removing venv, since sys.executable may live there)
    print("  ⏳  Uninstalling pip package...")
    subprocess.run(
        [sys.executable, "-m", "pip", "uninstall", "-y", "clawmetry"],
        check=False,
        capture_output=True,
    )
    print("  ✅  Uninstalled clawmetry pip package")

    # 2b. Windows: pip cannot remove Scripts\clawmetry.exe while this very
    # uninstall runs through it (a running exe is locked). Left alone it
    # becomes a zombie launcher whose every later invocation dies with
    # ModuleNotFoundError. A running exe CAN'T be overwritten but its file
    # CAN be deleted after exit, so hand the delete to a detached cmd that
    # fires once this process is gone.
    if os.name == "nt":
        for _cand in (
            Path(sys.executable).parent / "Scripts" / "clawmetry.exe",
            Path(sys.executable).parent / "clawmetry.exe",
        ):
            if _cand.exists():
                try:
                    subprocess.Popen(
                        f'cmd /c ping -n 3 127.0.0.1 >nul & del /f /q "{_cand}"',
                        creationflags=0x00000008 | 0x08000000,  # DETACHED | NO_WINDOW
                    )
                    print(f"  ✅  Scheduled removal of {_cand} (in use by this uninstall)")
                except Exception:
                    print(f"  ⚠️  Could not schedule removal of {_cand}. Remove it manually.")

    # 3. Remove config directory (includes venv). ignore_errors hides
    # locked-file failures, so verify and re-try instead of printing a
    # false success over a directory that is still there (#3914).
    #
    # --keep-data: skip the whole directory wipe so the DuckDB / history.db
    # survive. The pip-uninstall above already deregistered the package, so
    # leaving the venv on disk is harmless (it's just files).
    if clawmetry_dir.exists() and not _keep_data:
        shutil.rmtree(clawmetry_dir, ignore_errors=True)
        if clawmetry_dir.exists():
            import time as _time_u

            _time_u.sleep(0.5)
            shutil.rmtree(clawmetry_dir, ignore_errors=True)
        if clawmetry_dir.exists():
            _say(f"  ⚠️  Could not fully remove {clawmetry_dir} (files in use). Remove it manually.")
        else:
            _say(f"  ✅  Removed {clawmetry_dir}")

    # 4. Remove config/state/log files. A locked file (e.g. sync.log under
    # a daemon that survived the stop) warns and continues, never aborts.
    for f in [CONFIG_FILE, STATE_FILE, LOG_FILE]:
        if f.exists():
            if _safe_unlink(f):
                _say(f"  ✅  Removed {f}")

    # 5. Remove venv installs
    for vp in venv_paths:
        if vp.exists() and (vp / "bin" / "clawmetry").exists():
            try:
                shutil.rmtree(vp)
                print(f"  ✅  Removed {vp}")
            except PermissionError:
                subprocess.run(["sudo", "rm", "-rf", str(vp)], check=False)
                print(f"  ✅  Removed {vp} (sudo)")

    # 6. Remove symlinks
    for sl in symlinks:
        if sl.exists() or sl.is_symlink():
            try:
                sl.unlink()
                print(f"  ✅  Removed {sl}")
            except PermissionError:
                subprocess.run(["sudo", "rm", "-f", str(sl)], check=False)
                print(f"  ✅  Removed {sl} (sudo)")

    # 7. NemoClaw sandboxes
    if _nemoclaw_sandboxes:
        import subprocess as _sp
        import os as _os

        _extra = ["/opt/homebrew/bin", "/usr/local/bin"]
        _env = _os.environ.copy()
        _env["PATH"] = ":".join(_extra) + ":" + _env.get("PATH", "")
        import shutil as _sh

        _docker = _sh.which("docker", path=_env["PATH"]) or "docker"
        try:
            r = _sp.run(
                [_docker, "ps", "--format", "{{.Names}}"],
                capture_output=True,
                text=True,
                timeout=5,
                env=_env,
            )
            cluster = next(
                (n for n in r.stdout.splitlines() if "openshell-cluster" in n), None
            )
        except Exception:
            cluster = None
        if cluster:
            for sb in _nemoclaw_sandboxes:
                _say(f"  ⏳  Uninstalling from sandbox {sb}...")
                _uninstall_nemoclaw_sandbox(cluster, sb, docker_bin=_docker)
                _say(f"  ✅  Sandbox {sb} cleaned")

    # 8. OpenClaw sidecar files ClawMetry owns. Skipped under --keep-data
    # (the fleet DB + anomalies count as "data").
    if not _keep_data:
        for _p in _oc_sidecar:
            try:
                if _p.is_dir():
                    shutil.rmtree(_p, ignore_errors=True)
                    if not _p.exists():
                        _say(f"  ✅  Removed {_p}")
                else:
                    if _safe_unlink(_p):
                        _say(f"  ✅  Removed {_p}")
            except Exception as _e:
                _say(f"  ⚠️  Could not remove {_p}: {_e}")

    # 9. Strip clawmetry.cloudToken from ~/.openclaw/openclaw.json. This is
    # what caused the "auto-logged-in after drag-to-trash reinstall" surprise
    # — a stale token in a file OpenClaw owns. We only remove our own key;
    # the rest of openclaw.json is preserved (or the file is deleted if our
    # key was the only thing in it).
    _stripped, _oc_json_path = _strip_clawmetry_from_openclaw_json()
    if _stripped:
        _say(f"  ✅  Stripped clawmetry section from {_oc_json_path}")

    # 10. Desktop thin-shell runtime dir (~/Library/Application Support/ClawMetry
    # on macOS, %LOCALAPPDATA%/ClawMetry on Windows, ~/.local/share/ClawMetry
    # on Linux). Holds the pip-managed venv + bootstrap.log + onboarding
    # state. Removed LAST so we don't yank the venv out from under a running
    # `clawmetry` process (this uninstall itself may be executing from that
    # venv). On Windows the `.exe` self-delete pattern already handled by
    # step 2b lets us delete the parent dir after this process exits.
    #
    # We don't touch /Applications/ClawMetry.app itself — that's the user's
    # to manage (Finder → drag to Trash, or macOS Ventura+ "Move to Bin"). If
    # this uninstall was triggered from an in-app menu the caller is expected
    # to quit the app after the uninstall returns.
    _desktop_runtime = _desktop_runtime_dir()
    if _desktop_runtime.exists():
        try:
            shutil.rmtree(_desktop_runtime, ignore_errors=True)
            if _desktop_runtime.exists():
                # Retry once — venv teardown occasionally races the process
                # exit on macOS (open file handles under load_url).
                import time as _time_dr
                _time_dr.sleep(0.5)
                shutil.rmtree(_desktop_runtime, ignore_errors=True)
            if _desktop_runtime.exists():
                _say(
                    f"  ⚠️  Could not fully remove {_desktop_runtime} "
                    "(files in use). Remove it manually."
                )
            else:
                _say(f"  ✅  Removed desktop runtime dir {_desktop_runtime}")
        except Exception as _e:
            _say(f"  ⚠️  Could not remove {_desktop_runtime}: {_e}")

    if not _unattended:
        print()
        print("  \033[1m\033[92m✓ ClawMetry fully uninstalled.\033[0m")
        # Reinstall hint matches the host OS — a curl|bash line pasted into
        # cmd.exe would just error, so Windows gets the .cmd fetch+run pair.
        _reinstall_cmd = (
            "curl -fsSL https://clawmetry.com/install.cmd -o install.cmd && install.cmd"
            if sys.platform.startswith("win")
            else "curl -fsSL https://clawmetry.com/install.sh | bash"
        )
        print(f"  \033[2mTo reinstall: {_reinstall_cmd}\033[0m")
        print()

    # Restore stdout if we swapped it out under --unattended.
    if sys.stdout is not _orig_stdout:
        try:
            sys.stdout.close()
        except Exception:
            pass
        sys.stdout = _orig_stdout


def _status_live_line(rows, prev, now):
    """Build the one-line live status from session rows. ``prev`` is the last
    ``(total_tokens, time)`` sample (or None); ``now`` is the current time.
    Returns ``(line, (total_tokens, now))``. Pure so it's unit-testable — the
    refresh loop is the only impure part. Live tokens/sec is the total-token
    delta over wall time (so it's ~0 when idle, and climbs while an agent works).
    """
    rows = rows or []
    tot_tok = sum(int(r.get("total_tokens") or 0) for r in rows)
    tot_cost = sum(float(r.get("cost_usd") or 0) for r in rows)
    cur, best = {}, ""
    for r in rows:
        k = r.get("last_active_at") or r.get("updated_at") or r.get("started_at") or ""
        if k >= best:
            best, cur = k, r
    _md = cur.get("metadata") if isinstance(cur.get("metadata"), dict) else {}
    model = cur.get("model") or _md.get("model") or "—"
    tps = 0.0
    if prev is not None and now > prev[1]:
        tps = max(0.0, (tot_tok - prev[0]) / (now - prev[1]))
    line = f"\U0001F99E {len(rows)} sessions · {tot_tok:,} tokens · ${tot_cost:,.4f} · {model} · {tps:,.0f} tok/s"
    return line, (tot_tok, now)


def _status_live() -> None:
    """clawmetry status --live — a refreshing one-line terminal status bar
    (sessions · tokens · cost · model · live tokens/sec), read from the running
    daemon's local store via the read-only proxy. Ctrl-C to exit."""
    import sys as _sys
    import time as _t
    from clawmetry.local_store import get_store
    try:
        store = get_store(read_only=True)
    except Exception as exc:
        print(f"  Cannot open the local store (is the sync daemon running?): {exc}")
        return
    print("ClawMetry live  ·  Ctrl-C to exit\n")
    prev = None
    try:
        while True:
            try:
                rows = store.query_sessions_table(limit=300) or []
            except Exception:
                rows = []
            line, prev = _status_live_line(rows, prev, _t.time())
            _sys.stdout.write("\r\033[2K" + line)
            _sys.stdout.flush()
            _t.sleep(2)
    except KeyboardInterrupt:
        _sys.stdout.write("\n")
        _sys.stdout.flush()


def _is_placeholder_account(email) -> bool:
    """True when the account is a zero-friction PLACEHOLDER (the daemon
    auto-registered without a real login). Such an account is invisible from
    the user's real dashboard, so the node silently never shows up under their
    email -- the recurring 'I installed it but see 0 nodes' trap."""
    e = (email or "").strip().lower()
    return e.endswith("@clawmetry.auto") or e.endswith("@clawmetry.linked")


def _warn_if_placeholder_account(api_key: str, email=None) -> bool:
    """If this node is bound to a placeholder account, print a LOUD, actionable
    warning (it will NOT appear in the user's dashboard until linked). Returns
    True when it warned. Best-effort: resolves the email itself if not given,
    never raises, no-ops offline."""
    try:
        if email is None:
            email, _ = _resolve_account_email(api_key)
        if not _is_placeholder_account(email):
            return False
        print()
        print("  \033[33m⚠  This machine is on a TEMPORARY account, not your ClawMetry login.\033[0m")
        print("     It will NOT show up at app.clawmetry.com/cloud under your email.")
        print("     Link it to your account (copy the command from the '+ Add node'")
        print("     box at app.clawmetry.com/cloud -- it carries YOUR key):")
        print("        \033[36mclawmetry connect --key cm_xxxxxxxxxxxx\033[0m")
        print()
        return True
    except Exception:
        return False


def _resolve_account_email(api_key: str):
    """Best-effort: ask the cloud which ACCOUNT this node's api_key is linked to,
    so `clawmetry status` can show the email (and plan). This is the fastest way
    to catch the "my node is on the wrong account" trap. Short timeout + never
    raises, so status stays fast and works offline (returns (None, None) then)."""
    try:
        if not api_key or not str(api_key).startswith("cm_"):
            return None, None
        import json as _json
        import os as _os
        import urllib.parse as _up
        import urllib.request as _ur

        from clawmetry.endpoints import app_url as _resolve_app_url
        base = _resolve_app_url()
        url = base + "/api/cloud/account?token=" + _up.quote(api_key)
        with _ur.urlopen(url, timeout=2.5) as resp:
            data = _json.loads(resp.read() or b"{}")
        email = (data.get("email") or "").strip()
        plan = (data.get("plan") or "").strip()
        return (email or None), (plan or None)
    except Exception:
        return None, None


def _status_snapshot(args) -> dict:
    """Return a stable dict describing what ``clawmetry status`` shows.

    Sibling of the JSON payloads on ``tier`` / ``license`` / ``runtimes`` /
    ``features`` / ``channels`` / ``diagnose`` / ``verify-integrity`` — every
    read-only CLI diagnostic emits a jq-friendly envelope so wrapper scripts
    stop screen-scraping the human table. Called by ``_cmd_status(--json)``.

    Contract (fields are stable; new ones may be added, existing ones do not
    change shape or type):

    * ``version``: installed clawmetry version, or ``null`` when the metadata
      lookup fails (e.g. a very locked-down environment).
    * ``cloud_sync``: config-file view, or ``null`` when no config exists yet
      (fresh install). Carries the SAME masked identifiers the human path
      prints; ``api_key`` / ``encryption.secret_key`` are only populated when
      the operator passes ``--show-key`` (same policy as the human path).
    * ``sync_state``: last-sync timestamp + event-file count, or ``null``
      when the daemon has never written a state file.
    * ``runtimes``: whether the account entitles paid runtimes to sync,
      which runtimes the sync-daemon adapter detects locally, and whether
      the ``clawmetry-pro`` wheel is installed. Shape matches what the human
      path prints under the ``Runtimes:`` block.
    * ``daemon``: whether the sync daemon is running + how it's supervised
      (``launchd`` on macOS; ``systemd`` / ``systemd-user`` / ``background``
      on Linux; ``null`` when the platform doesn't check daemon status).
    * ``log``: log-file path + the same three-line tail the human path prints,
      or ``null`` when the log file is absent.
    * ``sandboxes``: reserved list-shaped placeholder — always ``[]`` in the
      JSON payload so scripts have a stable key to iterate over. The human
      path shells out to ``docker exec kubectl`` per NemoClaw pod, which is
      too slow for a scriptable diagnostic; scripts that need per-pod state
      should target that surface directly.
    * ``extensions``: side-effect-free probe of the ``clawmetry.extensions``
      entry points via :func:`clawmetry.extensions.probe_plugins`, so an
      operator can tell from a fresh ``clawmetry status`` whether the
      ``clawmetry-pro`` wheel is not only installed on disk (that lives in
      ``runtimes.pro_installed_version``) but also *importable* — catching
      the trap where the wheel extracted but its entry-point module raises
      on import. Shape: ``{"discovered": [{"name", "value", "importable",
      "error"}], "importable_count": int, "broken_count": int}``. Empty
      ``discovered`` on installs with no plugins registered.
    * ``license``: state of the self-hosted Pro/Enterprise license key at
      ``~/.clawmetry/license.key`` — the same envelope
      ``clawmetry license status --json`` emits, folded into the composite
      snapshot so an operator can answer *"is my node on Pro?"* in one
      command. Shape:
      ``{"installed": bool, "valid": bool, "status": str,
        "tier": str | null, "nodes": int | null, "sub": str | null,
        "days_left": int | null,
        "pubkey_fingerprint_sha256": str | null,
        "permissions_safe": bool | null, "file_mode": str | null}``.
      ``installed`` distinguishes *no license file yet* (status ``"none"``,
      all other fields ``null``) from *file present but broken* (status
      ``"invalid"`` / ``"expired"``). Complements
      ``runtimes.plan`` (cloud entitlement mirror) and
      ``extensions.discovered`` (whether the paid wheel imports): the
      three together triage every "why isn't Pro on this box?" question
      without a second command.

    Best-effort throughout: every helper is wrapped so a broken corner (e.g.
    an unreadable config file, an unavailable network) degrades to ``null``
    or a sensible zero-shape default instead of raising — same never-crash
    contract as every other CLI diagnostic.
    """
    import json as _json
    import platform as _platform
    from clawmetry.sync import CONFIG_FILE, STATE_FILE, LOG_FILE

    show_key = bool(getattr(args, "show_key", False))
    snap: dict = {
        "version": None,
        "cloud_sync": None,
        "sync_state": None,
        "runtimes": {
            "entitled": False,
            "plan": "",
            "pro_installed_version": None,
            "openclaw": {"detected": True, "syncing": True},
            "nemoclaw": {"detected": False, "syncing": False},
            "detected": [],
        },
        "daemon": {"running": False, "manager": None},
        "log": None,
        "sandboxes": [],
        "extensions": {
            "discovered": [],
            "importable_count": 0,
            "broken_count": 0,
        },
        "license": {
            "installed": False,
            "valid": False,
            "status": "none",
            "tier": None,
            "nodes": None,
            "sub": None,
            "days_left": None,
            "pubkey_fingerprint_sha256": None,
            "permissions_safe": None,
            "file_mode": None,
        },
    }

    # Installed version (lightweight metadata read; no dashboard import).
    try:
        import importlib.metadata as _md
        snap["version"] = _md.version("clawmetry") or None
    except Exception:
        snap["version"] = None

    # Config block.
    if CONFIG_FILE.exists():
        cloud: dict = {
            "connected": True,
            "config_error": None,
            "api_key_masked": "",
            "api_key": None,
            "account": {"email": None, "plan": None, "placeholder": False},
            "node_id": None,
            "connected_at": None,
            "encryption": {
                "enabled": False,
                "secret_key_masked": None,
                "secret_key": None,
            },
        }
        try:
            cfg = _json.loads(CONFIG_FILE.read_text())
            api_key = str(cfg.get("api_key", "") or "")
            enc_key = str(cfg.get("encryption_key", "") or "")
            cloud["api_key_masked"] = (
                api_key[:6] + "…" + api_key[-4:] if len(api_key) > 10 else api_key
            )
            if show_key:
                cloud["api_key"] = api_key
            email, plan = _resolve_account_email(api_key)
            cloud["account"]["email"] = email or None
            cloud["account"]["plan"] = plan or None
            cloud["account"]["placeholder"] = _is_placeholder_account(email)
            cloud["node_id"] = cfg.get("node_id") or None
            _ca = cfg.get("connected_at") or ""
            cloud["connected_at"] = (_ca[:19] or None) if _ca else None
            if enc_key:
                cloud["encryption"]["enabled"] = True
                cloud["encryption"]["secret_key_masked"] = (
                    enc_key[:6] + "…" + enc_key[-4:] if len(enc_key) > 10 else enc_key
                )
                if show_key:
                    cloud["encryption"]["secret_key"] = enc_key
        except Exception as exc:
            cloud["config_error"] = str(exc)
        try:
            from clawmetry.config import is_cloud_disabled as _icd_json
            cloud["local_only"] = _icd_json()
        except Exception:
            cloud["local_only"] = None
        snap["cloud_sync"] = cloud

    # Sync state.
    if STATE_FILE.exists():
        try:
            st = _json.loads(STATE_FILE.read_text())
            _ls = st.get("last_sync") or ""
            snap["sync_state"] = {
                "last_sync": (_ls[:19] or None) if _ls else None,
                "files_seen": len(st.get("last_event_ids") or {}),
            }
        except Exception:
            snap["sync_state"] = {"last_sync": None, "files_seen": 0}

    # Runtimes. Same resolution as the human path.
    try:
        _plan = ""
        try:
            _cp = Path(os.path.expanduser("~/.clawmetry/cloud_plan.json"))
            if _cp.is_file():
                _plan = str((_json.loads(_cp.read_text()) or {}).get("plan", "")).lower()
        except Exception:
            _plan = ""
        _entitled = _plan not in ("", "cloud_free", "free")
        snap["runtimes"]["plan"] = _plan
        snap["runtimes"]["entitled"] = _entitled
        try:
            from clawmetry.license import _pro_installed_version as _pv
            snap["runtimes"]["pro_installed_version"] = _pv() or None
        except Exception:
            snap["runtimes"]["pro_installed_version"] = None
        try:
            from clawmetry.adapters.nemo import NemoClawAdapter as _NCA
            _nemo = _NCA().detect()
            if getattr(_nemo, "detected", False):
                snap["runtimes"]["nemoclaw"] = {"detected": True, "syncing": True}
        except Exception:
            pass
        try:
            from clawmetry.sync import _detect_family_runtimes as _dfr
            _det = _dfr() or []
        except Exception:
            _det = []
        snap["runtimes"]["detected"] = [
            {
                "name": (r.get("name") or ""),
                "display_name": (r.get("displayName") or r.get("name") or "runtime"),
                "session_count": int(r.get("sessionCount") or 0),
                "syncing": bool(_entitled),
            }
            for r in _det
        ]
    except Exception:
        pass

    # Daemon.
    system = _platform.system()
    try:
        if system == "Darwin":
            import subprocess as _sp
            r = _sp.run(
                ["launchctl", "list", "com.clawmetry.sync"],
                capture_output=True, text=True,
            )
            if r.returncode == 0:
                snap["daemon"] = {"running": True, "manager": "launchd"}
            else:
                snap["daemon"] = {"running": False, "manager": "launchd"}
        elif system == "Linux":
            import subprocess as _sp
            import shutil as _sh
            running = _is_sync_running()
            manager: str | None = None
            if running:
                # Default to ``background`` whenever the daemon is up but we
                # can't identify a supervisor; only upgrade to ``systemd`` /
                # ``systemd-user`` when systemctl confirms an active unit.
                # A shell wrapper reading ``.daemon.manager`` expects a label
                # once ``.daemon.running`` is true — a null there is easy to
                # mistake for "not running".
                manager = "background"
                if _sh.which("systemctl"):
                    for _scope in (["--user"], []):
                        try:
                            _a = _sp.run(
                                ["systemctl", *_scope, "is-active", "clawmetry-sync"],
                                capture_output=True, text=True, timeout=5,
                            )
                            if _a.stdout.strip() == "active":
                                manager = "systemd" if _scope == [] else "systemd-user"
                                break
                        except Exception:
                            pass
            snap["daemon"] = {"running": bool(running), "manager": manager}
        else:
            snap["daemon"] = {"running": False, "manager": None}
    except Exception:
        snap["daemon"] = {"running": False, "manager": None}

    # Log tail — same three-line window the human path prints.
    if LOG_FILE.exists():
        try:
            lines = LOG_FILE.read_text(errors="replace").splitlines()[-3:]
        except Exception:
            lines = []
        snap["log"] = {"path": str(LOG_FILE), "tail": lines}

    # Extensions — side-effect-free probe of the ``clawmetry.extensions`` entry
    # points. Complements ``runtimes.pro_installed_version`` (which only reads
    # the disk marker after ``clawmetry activate``): the probe catches the case
    # where the wheel is on disk but its entry point fails to import (partial
    # extract, incompatible core, mismatched entry-point path). This is a fresh
    # CLI process — ``loaded_plugins()`` / ``failed_plugins()`` would read empty
    # here because ``load_plugins`` is only called in the daemon/dashboard — so
    # ``probe_plugins`` is the meaningful signal for the ``status`` snapshot.
    try:
        from clawmetry.extensions import probe_plugins as _probe
        rows = _probe() or []
        snap["extensions"] = {
            "discovered": rows,
            "importable_count": sum(1 for r in rows if r.get("importable")),
            "broken_count": sum(1 for r in rows if not r.get("importable")),
        }
    except Exception:
        pass

    # License — self-hosted Pro/Enterprise key at ``~/.clawmetry/license.key``.
    # Sibling of the ``extensions`` block above: extensions answer "would the
    # paid wheel import?", this block answers "is a valid signed key on
    # disk?". The two orthogonally cover the two failure modes an operator
    # hits when Pro doesn't turn on — a broken wheel install vs. a
    # missing / expired / tampered license file — so folding both into
    # ``status --json`` collapses "why isn't Pro on this box?" from a
    # multi-command dance to one jq pipeline. ``current_license_info``
    # returns ``None`` when no file is on disk (fresh install / OSS mode)
    # and a fully-populated dict on every file-exists branch (active /
    # expired / signature-invalid). Never raises — a broken corner keeps
    # the default ``status: "none"`` shape.
    try:
        from clawmetry.license import current_license_info as _license_info
        info = _license_info()
        if info is None:
            # File not on disk yet — leave the default ``installed=False``
            # / ``status="none"`` shape from ``snap`` initialisation intact
            # so a script never sees ``null`` on a field it does not need
            # to special-case.
            pass
        else:
            snap["license"] = {
                "installed": True,
                "valid": bool(info.get("valid")),
                "status": str(info.get("status") or "unknown"),
                "tier": info.get("tier"),
                "nodes": info.get("nodes"),
                "sub": info.get("sub"),
                "days_left": info.get("days_left"),
                "pubkey_fingerprint_sha256": info.get("pubkey_fingerprint_sha256"),
                "permissions_safe": info.get("permissions_safe"),
                "file_mode": info.get("file_mode"),
            }
    except Exception:
        pass

    # Installs — this CLI copy vs the daemon environment the auto-updater
    # keeps current. ``version`` (above) is THIS process's package version,
    # which on a machine with a stale duplicate install (a pre-venv
    # ``pip install --user`` shadowing ``~/.clawmetry/bin`` on PATH) is NOT
    # the version the daemon runs — that mismatch read as "auto-update is
    # broken" (founder live-hit 2026-07-31). ``daemon.installed_version`` is
    # the on-disk truth for the daemon env; ``installs.stale_cli`` is the
    # one-bit answer scripts can alert on.
    try:
        from clawmetry.installs import installs_snapshot as _installs_snap
        _inst = _installs_snap()
        snap["installs"] = _inst
        _dver = (_inst.get("daemon_env") or {}).get("version")
        if _dver and isinstance(snap.get("daemon"), dict):
            snap["daemon"]["installed_version"] = _dver
    except Exception:
        snap["installs"] = None

    return snap


def _cmd_status(args) -> None:
    """clawmetry status — show local + cloud sync status."""
    if getattr(args, "live", False):
        _status_live()
        return
    if getattr(args, "as_json", False):
        import json as _json
        # Sibling of `tier --json` / `license --json` / `runtimes --json` /
        # `features --json` / `channels --json` / `diagnose --json` /
        # `verify-integrity --json` — one dict, no side-effect prints.
        print(_json.dumps(_status_snapshot(args), sort_keys=True))
        return
    import platform
    from clawmetry.sync import CONFIG_FILE, STATE_FILE, LOG_FILE

    print("ClawMetry Status\n" + "─" * 40)

    # Installed version — so it's obvious at a glance whether this box is on the
    # latest (the #1 "why is my node behaving like an old build" clue). Uses the
    # lightweight package metadata, not the heavy dashboard import.
    try:
        import importlib.metadata as _md
        _cm_ver = _md.version("clawmetry")
    except Exception:
        _cm_ver = ""
    if _cm_ver:
        print(f"  Version:     {_cm_ver}")
    # Stale-duplicate guard: when this CLI is a separate copy that is OLDER
    # than the daemon's auto-updated install, the version above is misleading
    # (the node itself IS current). Say so, with the daemon's real version.
    try:
        from clawmetry.installs import installs_snapshot as _inst_snap, \
            stale_warning_lines as _stale_lines
        _inst = _inst_snap()
        _dver = (_inst.get("daemon_env") or {}).get("version")
        if _dver and _dver != _cm_ver:
            print(f"  Daemon ver:  {_dver}  (auto-updated install at "
                  f"{(_inst.get('daemon_env') or {}).get('home')})")
        for _ln in _stale_lines(_inst):
            print("  " + _ln)
    except Exception:
        pass

    # Config
    if CONFIG_FILE.exists():
        try:
            import json

            cfg = json.loads(CONFIG_FILE.read_text())
            api_key = cfg.get("api_key", "")
            enc_key = cfg.get("encryption_key", "")
            masked_api = (
                api_key[:6] + "…" + api_key[-4:] if len(api_key) > 10 else api_key
            )
            try:
                from clawmetry.config import is_cloud_disabled as _icd_status
                _status_local_only = _icd_status()
            except Exception:
                _status_local_only = False
            if _status_local_only:
                # Signed-in Self-Hosted: the account exists (it holds the
                # trial license) but nothing syncs — saying "Connected"
                # here read as a betrayal (founder 2026-07-30).
                print("  Cloud sync:  ⏸   Local-only (account linked; data stays on this machine)")
            else:
                print("  Cloud sync:  ✅  Connected")
            print(f"  API key:     {masked_api}")
            _acct_email, _acct_plan = _resolve_account_email(api_key)
            # Self-heal the local plan cache from the LIVE account. The runtime
            # entitlement gate below (and the daemon + dashboard) read
            # ~/.clawmetry/cloud_plan.json, which only the daemon refreshes on a
            # heartbeat. If the daemon is down, or hasn't heartbeated since the
            # user upgraded (free -> trial/pro), that cache is stale and status
            # contradicts itself ("trial" in the header, "FREE plan" in the gate).
            # Mirroring the live plan here makes the gate reflect the real plan
            # immediately and seeds the entitlement resolver so paid runtimes
            # flip on without waiting for the daemon. Best-effort; never raises.
            if _acct_plan:
                try:
                    from clawmetry.sync import _persist_cloud_plan_to_disk as _pcp
                    _pcp(_acct_plan)
                except Exception:
                    pass
            if _acct_email:
                _plan_suffix = f"  ({_acct_plan})" if _acct_plan else ""
                _acct_note = "  ⚠ temporary, not linked" if _is_placeholder_account(_acct_email) else ""
                print(f"  Account:     {_acct_email}{_plan_suffix}{_acct_note}")
            print(f"  Node ID:     {cfg.get('node_id', '?')}")
            print(f"  Connected:   {cfg.get('connected_at', '?')[:19]}")
            if enc_key:
                if getattr(args, "show_key", False):
                    print(f"  Secret key:     {enc_key}")
                else:
                    masked_enc = enc_key[:6] + "…" + enc_key[-4:]
                    print(f"  Secret key:     {masked_enc}  (--show-key to reveal)")
                print("  E2E:         🔒 enabled")
            else:
                print("  E2E:         ⚠️  disabled (no secret key in config)")
            # Loud, actionable block when the node is on a placeholder account
            # (the recurring 'connected but 0 nodes in my dashboard' trap).
            _warn_if_placeholder_account(api_key, _acct_email)
        except Exception as e:
            print(f"  Config error: {e}")
    else:
        print("  Cloud sync:  ○  Not connected  (run: clawmetry connect)")

    # Sync state
    if STATE_FILE.exists():
        try:
            import json

            st = json.loads(STATE_FILE.read_text())
            print(f"  Last sync:   {(st.get('last_sync') or '?')[:19]}")
            print(f"  Files seen:  {len(st.get('last_event_ids', {}))}")
        except Exception:
            pass

    # Runtimes — which agent runtimes this node detects + actually SYNCS, so it's
    # obvious at a glance whether Claude Code / Codex / etc. are being captured
    # (the #1 "why don't I see my runtime?" question). The honest distinction:
    # the adapter may DETECT a runtime locally, but paid runtimes only SYNC to
    # the cloud on a Trial/Pro account — so we read the daemon's plan cache.
    try:
        print()
        # Is this node entitled? Resolve through clawmetry.entitlements — the
        # SAME source the dashboard and gate use (license.key first, cloud
        # plan cache second). Reading only cloud_plan.json here made status
        # contradict itself on a self-hosted trial: "License: Trial" in the
        # header while this gate said "FREE plan, NOT syncing" because the
        # user's OLD cloud account was trial_expired (founder live-hit
        # 2026-07-28).
        _entitled = False
        _plan = ""
        _e = None
        try:
            from clawmetry import entitlements as _ent_st
            _e = _ent_st.get_entitlement(force=True)
            # is_paid / expired are properties — calling them raised and the
            # fallback silently reported the stale cloud plan ("FREE plan")
            # under a valid trial key (founder live-hit 2026-07-28, twice).
            _entitled = bool(_e.is_paid and not _e.expired)
            _plan = _e.tier or ""
        except Exception:
            # Fallback: the old cloud-plan cache read (entitlements missing
            # on a very old install).
            try:
                import json as _j2
                _cp = Path(os.path.expanduser("~/.clawmetry/cloud_plan.json"))
                if _cp.is_file():
                    _plan = str((json.loads(_cp.read_text()) or {}).get("plan", "")).lower()
                    _entitled = _plan not in ("", "cloud_free", "free")
            except Exception:
                pass

        # Plan: — one unambiguous line for Free / Trial / Trial Expired /
        # Starter / Pro / Enterprise, unlike the old License: block below
        # (silent unless a local key FILE exists, so a cloud-only Free/Trial
        # account showed nothing at all here). `_e.tier` + `_e.expired`
        # already carry an expired trial correctly — the resolver preserves
        # tier="trial" with expiry in the past rather than silently falling
        # through to oss (entitlements.py's own allows_runtime/allows_feature
        # rely on that same distinction to deny paid access even in GRACE
        # mode) — so no new plumbing is needed here, just an honest label.
        if _e is not None:
            _tier_lc = (_e.tier or "").strip().lower()
            if _tier_lc == "trial" and _e.expired:
                _plan_label = "Trial Expired"
            else:
                _plan_label = {
                    "oss": "Free",
                    "cloud_free": "Free",
                    "trial": "Trial",
                    "cloud_starter": "Starter",
                    "cloud_pro": "Pro",
                    "pro": "Pro",
                    "enterprise": "Enterprise",
                }.get(_tier_lc, (_e.tier or "Free").capitalize())
            if _tier_lc == "trial" and _e.expired:
                print(f"  Plan:        ⚠️  {_plan_label} — upgrade at "
                      f"https://clawmetry.com/pricing to keep paid runtimes")
            elif _tier_lc == "trial":
                _left = _e.days_until_expiry()
                _left_txt = f", {_left}d left" if isinstance(_left, int) else ""
                print(f"  Plan:        {_plan_label}{_left_txt}")
            else:
                print(f"  Plan:        {_plan_label}")

        _prover = None
        try:
            from clawmetry.license import _pro_installed_version as _pv
            _prover = _pv()
        except Exception:
            _prover = None
        _det = []
        try:
            from clawmetry.sync import _detect_family_runtimes as _dfr
            _det = _dfr() or []
        except Exception:
            _det = []
        print("  Runtimes:")
        # OpenClaw line is DETECTION-GATED: this used to print
        # "OpenClaw syncing" unconditionally, telling a machine with no
        # OpenClaw install that OpenClaw was detected and syncing (founder
        # live-hit 2026-07-28). Wording: "watching (local)" is the local
        # DuckDB ingest that renders the dashboard; "syncing" is reserved
        # for the separate Cloud sync line above — one word per concept.
        try:
            import dashboard as _dash_det
            _oc_present = bool(_dash_det._detect_openclaw_install())
        except Exception:
            _oc_present = False
        # One bullet style for every runtime — no runtime gets a logo (the
        # 🦞/⚡ prefixes made OpenClaw/NemoClaw look privileged next to the
        # plain-bullet family rows, and the emoji width broke column
        # alignment; founder live-hit 2026-07-31).
        if _oc_present:
            print(f"    • {'OpenClaw':<18} ✅ watching (local)  (free)")
        try:
            from clawmetry.adapters.nemo import NemoClawAdapter as _NCA
            _nemo = _NCA().detect()
            if _nemo.detected:
                print(f"    • {'NemoClaw':<18} ✅ watching (local)  (free)")
        except Exception:
            pass
        for _r in _det:
            _n = int(_r.get("sessionCount") or 0)
            _nm = _r.get("displayName") or _r.get("name") or "runtime"
            _state = "✅ watching (local)" if _entitled else "○ detected, NOT watched"
            print(f"    • {_nm:<18} {_state}  ({_n} session{'s' if _n != 1 else ''})")
        if not _prover:
            print("    ⚠ Claude Code / Codex / Cursor / Aider / Goose / opencode / Qwen — NOT syncing")
            if _entitled:
                print("      → your account is entitled — the daemon auto-downloads the paid runtime")
                print("        pack on start (no pip needed). If it hasn't yet: clawmetry sync --restart")
            else:
                print("      → paid runtimes need a Trial/Pro account. The daemon auto-downloads the")
                print("        runtime pack on start once entitled — link your account in the dashboard.")
        elif _det and not _entitled:
            print(f"    clawmetry-pro {_prover} installed and detecting the above — but this node")
            print(f"      has no active Trial/Pro entitlement ({_plan or 'free'}), so paid runtimes")
            print("      are not watched. Start the free trial from the dashboard to turn them on.")
        elif _det and _entitled:
            _lbl = {"trial": "Trial"}.get((_plan or "").lower(), _plan or "entitled")
            print(f"    clawmetry-pro {_prover} watching the above locally ({_lbl} plan).")
        elif _prover and not _det:
            print(f"    clawmetry-pro {_prover} installed — no other runtimes found on this machine yet.")
    except Exception:
        pass

    # Extensions — a side-effect-free probe of ``clawmetry.extensions`` entry
    # points. Complements the disk-marker check above: catches the case where
    # ``clawmetry-pro`` is on disk but its entry point cannot be imported.
    # ``load_plugins`` never runs in this CLI process, so we can't read
    # ``loaded_plugins``; ``probe_plugins`` is the meaningful signal here.
    try:
        from clawmetry.extensions import probe_plugins as _probe
        _rows = _probe() or []
        if _rows:
            _ok = sum(1 for r in _rows if r.get("importable"))
            _bad = sum(1 for r in _rows if not r.get("importable"))
            print()
            print("  Extensions:")
            for _r in _rows:
                _name = str(_r.get("name") or "?")
                if _r.get("importable"):
                    print(f"    ✅ {_name}  (importable)")
                else:
                    _err = str(_r.get("error") or "import failed")
                    print(f"    ❌ {_name}  — {_err}")
            if _bad:
                print(f"    → {_bad} plugin(s) will NOT load on daemon start; {_ok} will.")
    except Exception:
        pass

    # License — one-line summary when a self-hosted key is on disk. Silent
    # when there is no key file (fresh OSS install), matching the extensions
    # block's silence-on-empty policy so the human snapshot doesn't grow a
    # section that carries no information for the default operator. Points
    # to ``clawmetry license`` for the full envelope; this line is a triage
    # hint, not a replacement.
    try:
        from clawmetry.license import current_license_info as _lic_info
        _lic = _lic_info()
        if _lic is not None:
            print()
            if _lic.get("valid"):
                _tier = str(_lic.get("tier") or "pro").capitalize()
                _days = _lic.get("days_left")
                _days_txt = f", expires in {_days}d" if isinstance(_days, int) else ""
                print(f"  License:     ✅ {_tier} (self-hosted{_days_txt})")
            else:
                _status = str(_lic.get("status") or "invalid")
                print(f"  License:     ⚠️  {_status}  (run `clawmetry license` for details)")
    except Exception:
        pass

    # Daemon status
    system = platform.system()
    print()
    if system == "Darwin":
        import subprocess

        r = subprocess.run(
            ["launchctl", "list", "com.clawmetry.sync"], capture_output=True, text=True
        )
        if r.returncode == 0:
            print("  Daemon:      ✅  Running (launchd)")
        else:
            print("  Daemon:      ○  Not running")
    elif system == "Linux":
        import subprocess
        import shutil

        # The actual process check is the source of truth: the daemon can run as
        # a `systemctl --user` service, a system service (root/VPS), or a bare
        # background subprocess. Reporting "Not running" off `systemctl --user`
        # alone false-negatives on a root VPS (no --user D-Bus session) even
        # when the daemon is up. Check the process first, then label how it's
        # managed for a helpful hint.
        running = _is_sync_running()
        _how = ""
        if running and shutil.which("systemctl"):
            for _scope in (["--user"], []):  # user service, then system service
                try:
                    _a = subprocess.run(
                        ["systemctl", *_scope, "is-active", "clawmetry-sync"],
                        capture_output=True, text=True, timeout=5,
                    )
                    if _a.stdout.strip() == "active":
                        _how = " (systemd)" if _scope == [] else " (systemd --user)"
                        break
                except Exception:
                    pass
            if not _how:
                _how = " (background process)"
        print(
            f"  Daemon:      {'✅  Running' + _how if running else '○  Not running'}"
        )

    if LOG_FILE.exists():
        print(f"  Log:         {LOG_FILE}")
        # Last 3 lines
        lines = LOG_FILE.read_text(errors="replace").splitlines()[-3:]
        for ln in lines:
            print(f"    {ln}")

    # NemoClaw sandbox nodes (if docker + kubectl available)
    _print_nemoclaw_nodes(args)


def _print_nemoclaw_nodes(args) -> None:
    """Show status of ClawMetry on all NemoClaw sandboxes."""
    import subprocess
    import shutil

    if not shutil.which("docker"):
        return

    # Find cluster container
    try:
        r = subprocess.run(
            ["docker", "ps", "--format", "{{.Names}}"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        cluster = next(
            (n for n in r.stdout.splitlines() if "openshell-cluster" in n), None
        )
    except Exception:
        return

    if not cluster:
        return

    # Get sandbox pod names
    try:
        r = subprocess.run(
            [
                "docker",
                "exec",
                cluster,
                "kubectl",
                "get",
                "pods",
                "-n",
                "openshell",
                "--no-headers",
                "-o",
                "custom-columns=NAME:.metadata.name",
            ],
            capture_output=True,
            text=True,
            timeout=10,
        )
        pods = [
            p for p in r.stdout.splitlines() if p and not p.startswith("openshell-")
        ]
    except Exception:
        return

    if not pods:
        return

    print()
    print("NemoClaw Sandboxes\n" + "─" * 40)
    for pod in pods:
        try:
            r = subprocess.run(
                [
                    "docker",
                    "exec",
                    cluster,
                    "kubectl",
                    "exec",
                    "-n",
                    "openshell",
                    pod,
                    "--",
                    "bash",
                    "-c",
                    "cfg=/root/.clawmetry/config.json; "
                    "[ -f /sandbox/.clawmetry/config.json ] && cfg=/sandbox/.clawmetry/config.json; "
                    "test -f $cfg && "
                    'python3 -c "import json,sys; c=json.load(open(sys.argv[1])); '
                    "print(c.get('api_key','') + '|' + c.get('node_id','') + '|' + c.get('encryption_key',''))\" $cfg "
                    "2>/dev/null || echo 'NOT_CONNECTED'",
                ],
                capture_output=True,
                text=True,
                timeout=10,
            )
            out = r.stdout.strip()
        except Exception:
            out = ""

        print(f"\n  Sandbox:     {pod}")
        if out and out != "NOT_CONNECTED" and "|" in out:
            parts = out.split("|", 2)
            api_key = parts[0] if len(parts) > 0 else ""
            node_id = parts[1] if len(parts) > 1 else pod
            enc_key = parts[2] if len(parts) > 2 else ""
            masked_api = (
                api_key[:6] + "…" + api_key[-4:] if len(api_key) > 10 else api_key
            )
            print("  Cloud sync:  ✅  Connected")
            print(f"  API key:     {masked_api}")
            _acct_email, _acct_plan = _resolve_account_email(api_key)
            if _acct_email:
                _plan_suffix = f"  ({_acct_plan})" if _acct_plan else ""
                print(f"  Account:     {_acct_email}{_plan_suffix}")
            print(f"  Node ID:     {node_id}")
            if enc_key:
                if getattr(args, "show_key", False):
                    print(f"  Secret key:  {enc_key}")
                else:
                    masked_enc = enc_key[:6] + "…" + enc_key[-4:]
                    print(f"  Secret key:  {masked_enc}  (--show-key to reveal)")
                print("  E2E:         🔒 enabled")
            # Check daemon
            try:
                rd = subprocess.run(
                    [
                        "docker",
                        "exec",
                        cluster,
                        "kubectl",
                        "exec",
                        "-n",
                        "openshell",
                        pod,
                        "--",
                        "bash",
                        "-c",
                        "supervisorctl status clawmetry-sync 2>/dev/null | grep -q RUNNING && echo running || { "
                        "for pf in /sandbox/.clawmetry/sync.pid /root/.clawmetry/sync.pid; do "
                        "[ -f $pf ] && kill -0 $(cat $pf) 2>/dev/null && echo running && exit 0; "
                        "done; echo stopped; }",
                    ],
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                daemon_status = rd.stdout.strip()
                print(
                    f"  Daemon:      {'✅  Running' if daemon_status == 'running' else '○  Not running'}"
                )
            except Exception:
                pass
        else:
            print(
                "  Cloud sync:  ○  Not connected  (run: clawmetry connect inside sandbox)"
            )


def _instant_register(BOLD, GREEN, DIM):
    """Register a new cloud account without OTP. Returns (api_key, dashboard_url, node_id) or None."""
    import urllib.request
    import urllib.error
    import json as _json
    import socket
    import platform

    from clawmetry.endpoints import ingest_url as _resolve_ingest_url
    INGEST_URL = _resolve_ingest_url()
    url = INGEST_URL.rstrip("/") + "/api/register"

    hostname = socket.gethostname()
    try:
        from clawmetry.sync import get_machine_id

        machine_id = get_machine_id()
    except Exception:
        machine_id = hostname

    body = _json.dumps({
        "hostname": hostname,
        "machine_id": machine_id,
        "platform": platform.system(),
    }).encode()

    req = urllib.request.Request(
        url, data=body, headers={"Content-Type": "application/json"}, method="POST"
    )
    # Cloud Run scales `ingest.clawmetry.com` to zero between traffic bursts.
    # A cold start (container boot + DB pool warm-up) can exceed 15s on the
    # first hit, which used to drop fresh installs into "local mode" silently.
    # Match the cold-start-retry pattern we use for the daemon heartbeat
    # (OSS PR #135): 3 attempts, longer per-attempt timeout, exponential
    # backoff on timeout / 5xx / connection reset.
    import time as _t_reg
    _attempts = 3
    _per_attempt_timeout = 30
    _last_err = None
    for _i in range(_attempts):
        try:
            with urllib.request.urlopen(req, timeout=_per_attempt_timeout) as resp:
                result = _json.loads(resp.read())
                break
        except urllib.error.HTTPError as e:
            # Retry only on transient 5xx (502/503/504 = cold start / LB).
            if e.code in (502, 503, 504) and _i < _attempts - 1:
                _last_err = e
                _t_reg.sleep(2 * (_i + 1))
                continue
            print(f"  {DIM(f'Could not reach cloud: {e}')}")
            return None
        except Exception as e:
            _last_err = e
            if _i < _attempts - 1:
                _t_reg.sleep(2 * (_i + 1))
                continue
            print(f"  {DIM(f'Could not reach cloud: {e}')}")
            return None
    else:
        print(f"  {DIM(f'Could not reach cloud after {_attempts} attempts: {_last_err}')}")
        return None

    if not result.get("ok"):
        _reg_err = result.get("error", "unknown")
        print(f"  {DIM(f'Registration error: {_reg_err}')}")
        return None

    return result


def _cmd_onboard(args) -> None:
    """clawmetry onboard / setup -- interactive first-time setup wizard."""
    import os as _os

    _is_tty = sys.stdout.isatty()

    def _c(code, text):
        return f"\033[{code}m{text}\033[0m" if _is_tty else text

    def BOLD(t):
        return _c("1", t)

    def GREEN(t):
        return _c("32", t)

    def CYAN(t):
        return _c("36", t)

    def DIM(t):
        return _c("2", t)

    # When stdin is piped (curl | bash), read from /dev/tty
    _tty = None
    if not sys.stdin.isatty():
        try:
            _tty = open("/dev/tty", "r")
        except OSError:
            pass

    def _input(prompt):
        if _tty is not None:
            sys.stdout.write(prompt)
            sys.stdout.flush()
            return _tty.readline().rstrip("\n")
        return input(prompt)

    # Check if already connected
    already_connected = False
    try:
        import json as _jcfg
        _cfgpath = _os.path.expanduser("~/.clawmetry/config.json")
        if _os.path.exists(_cfgpath):
            _cfg = _jcfg.load(open(_cfgpath))
            if _cfg.get("api_key"):
                already_connected = True
    except Exception:
        pass
    if _os.environ.get("CLAWMETRY_API_KEY") or _os.environ.get("CLAWMETRY_NODE_ID"):
        already_connected = True

    # NOTE: we no longer early-return when already connected. `clawmetry onboard`
    # is the setup wizard, so it ALWAYS shows the [1]/[2]/[3] options and lets the
    # user switch how ClawMetry runs (e.g. cloud -> local, or add a license). When
    # already connected, an empty Enter keeps the current setup (handled in the
    # choice logic below) so re-running never silently changes anything.
    if already_connected:
        print(f"\n  {GREEN(BOLD('Already connected to ClawMetry.'))}")
        print(f"  {DIM('Pick an option below to change how ClawMetry runs, or press Enter to keep your current setup.')}")

    # Get version for banner
    try:
        import importlib.metadata
        _ver = importlib.metadata.version("clawmetry")
    except Exception:
        _ver = ""
    _ver_str = f" {_ver}" if _ver else ""

    if not already_connected:
        print(f"\n  {BOLD(f'ClawMetry{_ver_str} installed!')}")

    # Show what is actually on this machine before asking how to run:
    # a box full of Cursor/Claude Code sessions should hear, at the
    # conversion moment, that the free tier watches OpenClaw + NVIDIA
    # NemoClaw and the rest need a key or the Cloud plan (#3917).
    try:
        from clawmetry.runtime_probe import probe_runtimes, render_detection_lines

        _detect_lines = render_detection_lines(probe_runtimes())
    except Exception:
        _detect_lines = []
    if _detect_lines:
        print()
        for _i, _line in enumerate(_detect_lines):
            if _i == 0:
                print(f"  {BOLD(_line)}")
            elif "[x]" in _line:
                # Grid rows carry several "[x] Label" cells; the uniform
                # marker swap keeps the pure renderer's column padding intact.
                print(f"  {_line.replace('[x]', GREEN('✓'))}")
            else:
                print(f"  {DIM(_line)}" if _line else "")
    print()
    print(f"  {BOLD('Plans')} {DIM('(same either way; each tier includes the one before):')}")
    print(f"    {DIM('Free    $0          watch OpenClaw + NVIDIA NemoClaw, forever')}")
    print(f"    {DIM('Starter $9/node/mo  everything in Free + observability for all 14 runtimes')}")
    print(f"    {DIM('Pro    $19/node/mo  everything in Starter + governance (alerts, approvals, evals)')}")
    print()
    print(f"  {BOLD('How do you want to run ClawMetry?')}")
    print()
    print(f"    {BOLD('[1] Managed')}    {DIM('We host the dashboard for you: easy to manage when')}")
    print(f"                   {DIM('observing a large fleet of nodes. app.clawmetry.com from')}")
    print(f"                   {DIM('anywhere PLUS http://localhost:8900 on this machine; desk')}")
    print(f"                   {DIM('device at clawmetry.com/device. E2E-encrypted: snapshots')}")
    print(f"                   {DIM('are sealed here and only you hold the key.')}")
    print(f"    {BOLD('[2] Self-Host')}  {DIM('You host it: great for observing one node, difficult')}")
    print(f"                   {DIM('to manage for a fleet. Everything stays on your devices;')}")
    print(f"                   {DIM('dashboard at http://localhost:8900.')}")
    print()

    def _write_nocloud_marker():
        """Persist the local-only opt-out so updates can't silently re-enable
        cloud sync (clawmetry/config.py is_cloud_disabled / GitHub #1937)."""
        try:
            from clawmetry.config import NOCLOUD_MARKER_PATH
            from pathlib import Path as _P
            _P(NOCLOUD_MARKER_PATH).parent.mkdir(parents=True, exist_ok=True)
            _P(NOCLOUD_MARKER_PATH).touch()
        except Exception:
            pass

    def _finish_local():
        """Save an account-free config and start the daemon. The nocloud
        marker makes every cloud call a no-op while local DuckDB ingestion
        still feeds http://localhost:8900."""
        import platform as _plat
        import socket as _sock
        # The daemon reads config['node_id'] by subscript on start, so a
        # local-only config still needs one. Hostname matches the daemon's own
        # _node_id() fallback. No api_key/encryption_key -> the nocloud marker
        # short-circuits every cloud call regardless.
        _local_node_id = getattr(args, "custom_node_id", None) or _sock.gethostname() or "local"
        try:
            from clawmetry.sync import save_config as _save_config
            _save_config({
                # Empty api_key keeps the local-only config shape complete: the
                # daemon startup path subscripts config["api_key"], and an empty
                # string is safe because is_cloud_disabled() gates all egress.
                "api_key": "",
                "node_id": _local_node_id,
                "platform": _plat.system(),
                "connected_at": __import__("datetime").datetime.now().isoformat(),
                "local_only": True,
            })
        except Exception:
            pass
        print(f"  Starting background collector...")
        _stop_existing_daemon()
        _start_daemon({"local_only": True}, args)
        print(f"  Starting local dashboard...")
        # The URL below is the whole product for a local-only node — verify
        # the port ANSWERS before promising it (found live 2026-07-29:
        # onboard printed localhost:8900 while nothing was listening).
        _dash_up = _ensure_local_dashboard()
        print()
        if _dash_up:
            print(f"  {GREEN(BOLD('Watching your agents locally.'))}")
            print(f"     {BOLD('http://localhost:8900')} {DIM('(live now)')}")
        else:
            print(f"  ⚠️  The dashboard did not come up at {BOLD('http://localhost:8900')}.")
            print(f"     {DIM('Start it yourself:')} {CYAN('clawmetry')}   {DIM('logs: ~/.clawmetry/dashboard.log')}")
        print(f"     {DIM('Nothing leaves this machine. Enable cloud anytime: clawmetry connect')}")
        print()

    # Scriptable / non-interactive overrides. A headless install (curl | bash
    # with no /dev/tty) must NEVER silently create a cloud account, so the
    # EOF fallback is the free local tier ("0"), even though the interactive
    # default keypress is [1] Cloud (founder 2026-07-30: lead with the full
    # capability; self-host is the deliberate alternative).
    _env_local = _os.environ.get("CLAWMETRY_LOCAL_ONLY", "").strip().lower() in ("1", "true", "yes", "on")
    if getattr(args, "local", False) or _env_local:
        choice = "0"
    elif getattr(args, "cloud", False):
        choice = "1"
    else:
        # When already connected, the default on an empty Enter is "keep current
        # setup" (return without changes) so re-running onboard never silently
        # switches a connected user to local. A fresh install defaults to [1].
        _prompt = ("  Choose an option, or press Enter to keep your current setup: "
                   if already_connected else "  Choose [1]: ")
        try:
            choice = _input(_prompt).strip()
        except (EOFError, KeyboardInterrupt):
            # No interactive answer possible: never mint an account. A
            # connected node keeps its setup; a fresh one goes free-local.
            print()
            if already_connected:
                print(f"\n  {DIM('Keeping your current setup. Run  clawmetry status  to check sync health.')}\n")
                return
            choice = "0"
        if not choice:
            if already_connected:
                print(f"\n  {DIM('Keeping your current setup. Run  clawmetry status  to check sync health.')}\n")
                return
            choice = "1"

    print()

    if choice == "0":
        # ── Free local tier (no account): --local / env / EOF fallback ────
        print(f"  {GREEN(BOLD('Local only.'))} {DIM('No account, no cloud.')}")
        print()
        _write_nocloud_marker()
        _post_onboard_offers(_input, BOLD, CYAN, DIM)
        _finish_local()
        return

    def _config_api_key() -> str:
        try:
            import json as _jk
            with open(_os.path.expanduser("~/.clawmetry/config.json"), "r", encoding="utf-8") as _fh:
                return (_jk.load(_fh).get("api_key") or "").strip()
        except Exception:
            return ""

    import argparse as _ap

    if choice != "2":
        # ── [1] Cloud (default): sign in, fleet dashboard from anywhere ───
        # The keypress IS the cloud consent: clear the marker so connect goes
        # straight to sign-in; an incomplete sign-in re-writes it below.
        try:
            from clawmetry.config import NOCLOUD_MARKER_PATH as _nocloud_path

            _os.unlink(_nocloud_path)
        except Exception:
            pass
        _fake_args = _ap.Namespace(
            key=None, foreground=False, custom_node_id=None,
            enc_key=None, key_only=False, no_daemon=False,
        )
        _cmd_connect(_fake_args)
        print()
        if _config_api_key():
            # Trial mint + local activation already happened inside connect.
            _post_onboard_offers(_input, BOLD, CYAN, DIM)
            return
        print(f"  {DIM('No account connected. Running local-only; try again anytime:')} {CYAN('clawmetry onboard')}")
        print()
        _write_nocloud_marker()
        _post_onboard_offers(_input, BOLD, CYAN, DIM)
        _finish_local()
        return

    # ── [2] Self-Hosted: key if you have one, else trial sign-in ────────────
    # Data never leaves the machine on this path (nocloud marker). Identity
    # is still how the trial unlocks runtimes: no key -> sign in (Google /
    # GitHub / email OTP) via connect's keep-local mode, which mints and
    # activates the 7-day trial license with the marker KEPT.
    _write_nocloud_marker()
    try:
        _has_key = (_input("  Do you already have a license key? [y/N]: ").strip().lower() or "n")
    except (EOFError, KeyboardInterrupt):
        _has_key = "n"
        print()
    print()
    if _has_key in ("y", "yes"):
        try:
            _lic_key = _input("  Paste your license key (CLAW1...), or press Enter to do it later: ").strip()
        except (EOFError, KeyboardInterrupt):
            _lic_key = ""
            print()
        print()
        if _lic_key:
            try:
                from clawmetry import license as _lic
                ok, msg = _lic.activate(_lic_key, node_id=_lic._node_id())
                print(f"  {GREEN('Activated.') if ok else '⚠️  '}{msg}")
                if not ok:
                    print(f"     {DIM('Try again later:')} {CYAN('clawmetry activate <key>')}")
            except Exception as _e:
                print(f"  ⚠️  Activation failed: {_e}")
                print(f"     {DIM('Try again later:')} {CYAN('clawmetry activate <key>')}")
        else:
            _pricing_url = "https://clawmetry.com/pricing?deploy=self"
            print(f"  {DIM('Get one at')} {CYAN(_pricing_url)} {DIM('then run')} {CYAN('clawmetry activate <key>')}")
        print()
        _post_onboard_offers(_input, BOLD, CYAN, DIM)
        _finish_local()
        return

    # No key: offer the trial (the default), free tier if declined.
    try:
        _want_trial = (_input(
            "  Start your free 7-day Pro trial? Sign in with Google, GitHub, or an\n"
            "  email code; your data still stays on this machine. [Y/n]: "
        ).strip().lower() or "y")
    except (EOFError, KeyboardInterrupt):
        _want_trial = "n"
        print()
    print()
    if _want_trial in ("n", "no"):
        print(f"  {DIM('Free plan: OpenClaw + NeMo at http://localhost:8900.')}")
        print(f"  {DIM('Trial or license anytime:')} {CYAN('clawmetry onboard')} {DIM('·')} {CYAN('https://clawmetry.com/pricing?deploy=self')}")
        print()
        _post_onboard_offers(_input, BOLD, CYAN, DIM)
        _finish_local()
        return

    _fake_args = _ap.Namespace(
        key=None, foreground=False, custom_node_id=None,
        enc_key=None, key_only=False, no_daemon=False, keep_local=True,
    )
    _cmd_connect(_fake_args)
    print()
    if _config_api_key():
        # Connect (keep-local mode) minted + activated the trial, kept the
        # marker, and ensured the local dashboard.
        _post_onboard_offers(_input, BOLD, CYAN, DIM)
        return

    # Sign-in didn't complete: free local tier, no account.
    print(f"  {DIM('No account connected. Running the free plan; try again anytime:')} {CYAN('clawmetry onboard')}")
    print()
    _post_onboard_offers(_input, BOLD, CYAN, DIM)
    _finish_local()
    return


def _cmd_account(args) -> None:
    """clawmetry account -- link email to existing account or show account info."""
    import os as _os

    _is_tty = sys.stdout.isatty()

    def _c(code, text):
        return f"\033[{code}m{text}\033[0m" if _is_tty else text

    def BOLD(t):
        return _c("1", t)

    def GREEN(t):
        return _c("32", t)

    def CYAN(t):
        return _c("36", t)

    def DIM(t):
        return _c("2", t)

    # When stdin is piped (curl | bash), read from /dev/tty
    _tty = None
    if not sys.stdin.isatty():
        try:
            _tty = open("/dev/tty", "r")
        except OSError:
            pass

    def _input(prompt):
        if _tty is not None:
            sys.stdout.write(prompt)
            sys.stdout.flush()
            return _tty.readline().rstrip("\n")
        return input(prompt)

    # Load config
    cfg = {}
    try:
        import json as _jcfg
        _cfgpath = _os.path.expanduser("~/.clawmetry/config.json")
        if _os.path.exists(_cfgpath):
            cfg = _jcfg.load(open(_cfgpath))
    except Exception:
        pass

    api_key = cfg.get("api_key", "")
    if not api_key:
        print(f"\n  {DIM('Not connected to ClawMetry Cloud yet.')}")
        print(f"  {DIM('Run:')} {CYAN('clawmetry setup')}\n")
        return

    dashboard_id = cfg.get("dashboard_id", "")
    node_id = cfg.get("node_id", "")

    # Check if this account already has an email linked (not a placeholder)
    import urllib.request
    import urllib.error
    import json as _json

    from clawmetry.endpoints import ingest_url as _resolve_ingest_url
    INGEST_URL = _resolve_ingest_url()

    def _api_call(path, body):
        result, status = _post_json(INGEST_URL.rstrip("/") + path, body)
        if isinstance(result, dict) and status and status >= 400:
            result["_status"] = status
        return result

    # Show account info
    print()
    print(f"  {BOLD('ClawMetry Account')}")
    print()
    print(f"  Node:      {node_id}")
    if dashboard_id:
        from clawmetry.endpoints import app_url as _resolve_app_url_d
        print(f"  Dashboard: {_resolve_app_url_d()}/d/{dashboard_id}")
    print(f"  API key:   {api_key[:8]}...")
    print()

    # Prompt to link email if not yet linked
    print(f"  {BOLD('Link an email to secure your account:')}")
    print(f"  {DIM('This lets you recover access and manage multiple nodes.')}")
    print()

    try:
        email_input = _input("  Email (or press Enter to skip): ").strip().lower()
    except (EOFError, KeyboardInterrupt):
        email_input = ""
        print()

    if not email_input:
        print(f"\n  {DIM('Skipped. Run  clawmetry account  anytime to link an email.')}\n")
        return

    import re as _re
    if not _re.match(r"^[^@]+@[^@]+\.[^@]+$", email_input):
        print(f"\n  {DIM('That does not look like a valid email.')}\n")
        return

    # Send OTP
    print(f"\n  Sending verification code to {email_input}...", end="", flush=True)
    r = _api_call("/api/auth/email-otp", {"action": "send", "email": email_input})
    if r.get("_status") == 503:
        import time as _time

        retry_after = r.get("retry_after") or 5
        try:
            retry_after = max(1, min(int(retry_after), 30))
        except (TypeError, ValueError):
            retry_after = 5
        print(f"\n  {DIM(f'Server busy — retrying in {retry_after}s…')}", flush=True)
        _time.sleep(retry_after)
        print(f"  Sending verification code to {email_input}...", end="", flush=True)
        r = _api_call("/api/auth/email-otp", {"action": "send", "email": email_input})
        if r.get("_status") == 503:
            print(f" {DIM('could not reach servers — try again in a minute')}")
            return
    if r.get("error"):
        print(f" {DIM(r['error'])}")
        return
    print(f" {GREEN('sent')}")
    print()

    # Verify OTP
    for attempt in range(3):
        try:
            otp = _input("  Enter the 6-digit code: ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return
        if not otp:
            continue
        print("  Verifying...", end="", flush=True)
        r2 = _api_call(
            "/api/auth/email-otp",
            {"action": "verify", "email": email_input, "otp": otp, "link_key": api_key},
        )
        if r2.get("error"):
            print(f" {DIM(r2['error'])}")
            if attempt < 2:
                print("  Try again.")
            continue
        print(f" {GREEN('verified')}")
        print(f"\n  {GREEN(BOLD('Email linked to your account!'))}")
        if dashboard_id:
            from clawmetry.endpoints import app_url as _resolve_app_url_d
        print(f"  Dashboard: {_resolve_app_url_d()}/d/{dashboard_id}")
        print()
        return

    print(f"\n  {DIM('Could not verify. Try again later with: clawmetry account')}\n")


def _cmd_proxy(args) -> None:
    """clawmetry proxy — manage the enforcement proxy."""
    from clawmetry.proxy import (
        ProxyConfig,
        run_proxy,
        stop_proxy,
        proxy_status as _proxy_status,
        PROXY_CONFIG_FILE,
    )

    _is_tty = sys.stdout.isatty()

    def _c(code, text):
        return f"\033[{code}m{text}\033[0m" if _is_tty else text

    def BOLD(t):
        return _c("1", t)

    def GREEN(t):
        return _c("32", t)

    def CYAN(t):
        return _c("36", t)

    def DIM(t):
        return _c("2", t)

    def YELLOW(t):
        return _c("33", t)

    proxy_cmd = getattr(args, "proxy_cmd", None)

    if proxy_cmd == "start":
        config = ProxyConfig.load()

        # Apply CLI overrides
        if args.port is not None:
            config.port = args.port
        if args.host is not None:
            config.host = args.host
        if args.daily_budget is not None:
            config.budget.daily_usd = args.daily_budget
        if args.monthly_budget is not None:
            config.budget.monthly_usd = args.monthly_budget
        if args.no_loop_detection:
            config.loop_detection.enabled = False
        if args.log_requests:
            config.log_requests = True

        config.save()

        print()
        print(f"  {BOLD('ClawMetry Proxy')}")
        print()
        print(f"  Listening on {CYAN(f'http://{config.host}:{config.port}')}")
        print()
        print(f"  Budget:         {_format_budget(config, GREEN, YELLOW, DIM)}")
        print(
            f"  Loop detection: {GREEN('on') if config.loop_detection.enabled else DIM('off')}"
        )
        print(f"  Routing rules:  {len(config.routing_rules)}")
        print()
        print(f"  {BOLD('To activate, set in your environment:')}")
        print(f"    {CYAN(f'ANTHROPIC_BASE_URL=http://localhost:{config.port}')}")
        print(f"    {DIM('(OpenClaw will route all LLM calls through the proxy)')}")
        print()

        if not args.foreground:
            import subprocess

            proc = subprocess.Popen(
                [
                    sys.executable,
                    "-m",
                    "clawmetry.proxy",
                    "--port",
                    str(config.port),
                    "--host",
                    config.host,
                ],
                stdout=open(str(PROXY_CONFIG_FILE.parent / "proxy.log"), "a"),
                stderr=subprocess.STDOUT,
                start_new_session=True,
            )
            print(f"  {GREEN('✓')} Proxy started in background (pid {proc.pid})")
            _log_path = PROXY_CONFIG_FILE.parent / "proxy.log"
            print(f"  {DIM(f'Log: {_log_path}')} ")
            print()
        else:
            print("  Running in foreground (Ctrl+C to stop)")
            print()
            run_proxy(config, foreground=True)

    elif proxy_cmd == "stop":
        if stop_proxy():
            print(f"  {GREEN('✓')} Proxy stopped")
        else:
            print(f"  {DIM('Proxy is not running')}")

    elif proxy_cmd == "status":
        status = _proxy_status()
        if getattr(args, "as_json", False):
            import json

            print(json.dumps(status, indent=2))
            return

        if status.get("running"):
            print(f"  Proxy: {GREEN('running')} (pid {status['pid']})")
            try:
                import urllib.request
                import json

                config = ProxyConfig.load()
                url = f"http://{config.host}:{config.port}/proxy/status"
                with urllib.request.urlopen(url, timeout=3) as r:
                    detail = json.loads(r.read())
                print(f"  Uptime:    {_format_uptime(detail.get('uptime_seconds', 0))}")
                print(
                    f"  Requests:  {detail.get('requests_total', 0)} total, {detail.get('requests_blocked', 0)} blocked"
                )
                print(f"  Loops:     {detail.get('loops_detected', 0)} detected")
                b = detail.get("budget", {})
                if b.get("daily_limit", 0) > 0:
                    print(
                        f"  Daily:     ${b['daily_spent']:.2f} / ${b['daily_limit']:.2f}"
                    )
                if b.get("monthly_limit", 0) > 0:
                    print(
                        f"  Monthly:   ${b['monthly_spent']:.2f} / ${b['monthly_limit']:.2f}"
                    )
            except Exception:
                pass
        else:
            print(f"  Proxy: {DIM('not running')}")
            print(f"  Start with: {CYAN('clawmetry proxy start')}")

    elif proxy_cmd == "config":
        config = ProxyConfig.load()
        changed = False

        if args.daily_budget is not None:
            config.budget.daily_usd = args.daily_budget
            changed = True
        if args.monthly_budget is not None:
            config.budget.monthly_usd = args.monthly_budget
            changed = True
        if args.action is not None:
            config.budget.action = args.action
            changed = True
        if args.loop_detection is not None:
            config.loop_detection.enabled = args.loop_detection == "on"
            changed = True

        if changed:
            config.save()
            print(f"  {GREEN('✓')} Config updated")

        print(f"\n  {BOLD('Proxy Configuration')}")
        print(f"  {'─' * 40}")
        print(f"  Port:           {config.port}")
        print(f"  Host:           {config.host}")
        print(
            f"  Daily budget:   {'$' + str(config.budget.daily_usd) if config.budget.daily_usd > 0 else DIM('unlimited')}"
        )
        print(
            f"  Monthly budget: {'$' + str(config.budget.monthly_usd) if config.budget.monthly_usd > 0 else DIM('unlimited')}"
        )
        print(f"  Action:         {config.budget.action}")
        print(
            f"  Loop detection: {GREEN('on') if config.loop_detection.enabled else DIM('off')}"
        )
        print(f"  Routing rules:  {len(config.routing_rules)}")
        print(f"\n  Config file: {DIM(str(PROXY_CONFIG_FILE))}")
        print()

    else:
        print(f"\n  {BOLD('ClawMetry Proxy')}: enforcement layer for LLM API calls")
        print()
        print(f"  {BOLD('Commands:')}")
        print("    clawmetry proxy start    Start the proxy server")
        print("    clawmetry proxy stop     Stop the proxy server")
        print("    clawmetry proxy status   Show proxy status")
        print("    clawmetry proxy config   View/update proxy config")
        print()
        print(f"  {BOLD('Quick start:')}")
        print("    clawmetry proxy start --daily-budget 10")
        print("    export ANTHROPIC_BASE_URL=http://localhost:4100")
        print()


def _format_budget(config, GREEN, YELLOW, DIM):
    """Format budget display for CLI output."""
    parts = []
    if config.budget.daily_usd > 0:
        parts.append(f"${config.budget.daily_usd:.2f}/day")
    if config.budget.monthly_usd > 0:
        parts.append(f"${config.budget.monthly_usd:.2f}/mo")
    if parts:
        return f"{YELLOW(', '.join(parts))} ({config.budget.action})"
    return DIM("unlimited")


def _format_uptime(seconds):
    """Format uptime in human-readable form."""
    if seconds < 60:
        return f"{seconds:.0f}s"
    if seconds < 3600:
        return f"{seconds / 60:.0f}m"
    if seconds < 86400:
        return f"{seconds / 3600:.1f}h"
    return f"{seconds / 86400:.1f}d"


def _cmd_mcp(args) -> None:
    """Start the ClawMetry MCP server on stdio (refs #2859)."""
    from clawmetry.mcp_server import run
    run()


def _cmd_reports(args) -> None:
    """Open the reports browser (refs #1005)."""
    import webbrowser
    port = getattr(args, "port", None) or 8900
    url = f"http://localhost:{port}/reports/"
    print(f"Opening {url} …")
    print("(Make sure `clawmetry` is running. Write .md files to ~/.clawmetry/reports/.)")
    webbrowser.open(url)


def _cmd_eval(args) -> None:
    """Run a golden eval suite (Phase 2 evals, refs #1619).

    Exit code is 0 on all-pass, 1 on any-fail. The CI integration template
    relies on that — see docs/EVALS_CI_INTEGRATION.md.
    """
    import json as _json
    from clawmetry import eval_suite_runner as esr

    # Phase 3 — regression replay path. Mutually exclusive with --suite
    # (the two flows produce different table shapes; mixing them in one
    # invocation only confuses CI logs).
    if getattr(args, "regression", False):
        _cmd_eval_regression(args)
        return

    if getattr(args, "list_suites", False):
        suites = esr.list_suites()
        if not suites:
            print(
                f"No suites found in {esr.SUITES_DIR}.\n"
                f"Create one (see docs/EVALS_CI_INTEGRATION.md) and try again."
            )
            sys.exit(0)
        print("Available suites:")
        for s in suites:
            print(f"  {s}")
        sys.exit(0)

    suite_arg = getattr(args, "suite", None)
    if not suite_arg:
        print(
            "Error: --suite is required (or pass --list to see what's available).",
            file=sys.stderr,
        )
        sys.exit(2)

    # Watch mode wraps the same single-shot pipeline; --json is honoured
    # on every iteration so the dev loop can be piped into jq.
    def _print_result(run):
        if getattr(args, "as_json", False):
            print(_json.dumps({
                "suite":   run.suite_name,
                "ran_at":  run.ran_at,
                "sha":     run.sha,
                "passed":  run.passed,
                "failed":  run.failed,
                "exit":    run.exit_code,
                "results": [r.to_dict() for r in run.results],
            }, indent=2))
        else:
            print(esr.format_table(run))

    persist = not getattr(args, "no_persist", False)

    if getattr(args, "watch", False):
        try:
            esr.watch_suite(
                suite_arg,
                on_run=_print_result,
                persist=persist,
            )
        except KeyboardInterrupt:
            print("\nWatch stopped.")
            sys.exit(0)
        return

    try:
        suite = esr.load_suite(suite_arg)
    except (FileNotFoundError, ValueError) as e:
        # Keep error one-line and readable (per feedback_simple_ui_for_nontechnical).
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(2)
    run = esr.run_suite(suite, persist=persist)
    _print_result(run)
    sys.exit(run.exit_code)


def _cmd_eval_regression(args) -> None:
    """Phase 3 evals — replay last week's failed sessions against current
    config. MANUAL invocation only: every replay costs API tokens, so the
    runner enforces a hard ceiling (CLAWMETRY_EVALS_REGRESSION_MAX or the
    --limit flag, defaulting to 10).

    Exit code mirrors the eval-suite convention:
        0 → ran cleanly (any mix of improved/same is fine)
        1 → at least one regressed/errored row (signal worth investigating)
    """
    import json as _json
    from clawmetry import eval_regression_replay as err

    # Parse --window into days. Reuse the tiny human-readable parser style
    # from routes/evals.py so flags + URL params behave the same.
    raw = (getattr(args, "window", None) or "7d").strip().lower()
    try:
        if raw.endswith("d"):
            window_days = int(float(raw[:-1]))
        elif raw.endswith("h"):
            window_days = max(1, int(float(raw[:-1]) // 24))
        else:
            window_days = int(float(raw))
    except (TypeError, ValueError):
        window_days = 7
    window_days = max(1, min(90, window_days))

    limit = getattr(args, "limit", None)
    if limit is None:
        limit = err.DEFAULT_REPLAY_BUDGET
    limit = max(1, int(limit))

    if not err.is_enabled():
        print(
            "Regression replay is disabled "
            "(CLAWMETRY_EVALS_REGRESSION_ENABLED=0).",
            file=sys.stderr,
        )
        sys.exit(2)

    print(
        f"Replaying up to {limit} failed session(s) from the last "
        f"{window_days}d... (manual cost-guarded run)",
        flush=True,
    )
    run = err.run_regression(window_days=window_days, limit=limit)

    if getattr(args, "as_json", False):
        print(_json.dumps({
            "ran_at":       run.ran_at,
            "window_days":  run.window_days,
            "tested":       run.tested,
            "improved":     run.improved,
            "regressed":    run.regressed,
            "same":         run.same,
            "errored":      run.errored,
            "results":      [r.to_dict() for r in run.results],
        }, indent=2))
    else:
        if not run.results:
            print("No failed sessions in the window. Nothing to replay.")
        else:
            for r in run.results:
                old_s = "-" if r.original_score is None else f"{r.original_score:.1f}"
                new_s = "-" if r.new_score is None else f"{r.new_score:.1f}"
                print(
                    f"  {r.status.upper():<10} {r.session_id[:24]:<24} "
                    f"{old_s} -> {new_s}  {r.reason[:60]}"
                )
            print()
            print(
                f"{run.improved} improved, {run.regressed} regressed, "
                f"{run.same} same, {run.errored} errored "
                f"({run.tested} tested over last {window_days}d)"
            )
    exit_code = 1 if (run.regressed > 0 or run.errored > 0) else 0
    sys.exit(exit_code)


def _unattended_update_target(current: str):
    """Resolve what an unattended ``clawmetry update --unattended`` run may
    install, deferring to the DAEMON's policy helpers in
    ``routes/update_check.py`` so the two paths cannot drift:

      * ``_env_auto_update_disabled()`` — the CLAWMETRY_AUTO_UPDATE kill
        switch, including the implicit CI-environment disable.
      * ``_autoupdate_min_age_hours()`` + ``_newest_aged_in_version()`` —
        the CLAWMETRY_AUTOUPDATE_MIN_AGE_HOURS stability window, targeting
        the newest release that has aged past it (NOT the absolute latest).

    Returns ``(target_version_or_None, human_reason)``. ``None`` means
    "install nothing this cycle" — including when the policy helpers cannot
    be imported: an unattended caller must never do MORE than the policy
    allows, so an unevaluable policy fails closed (the caller's next
    scheduled cycle retries).
    """
    import json
    import urllib.request

    try:
        from routes.update_check import (
            _autoupdate_min_age_hours,
            _env_auto_update_disabled,
            _newest_aged_in_version,
        )
    except Exception as exc:
        return None, f"Update policy unavailable ({exc}); skipping unattended update"
    if _env_auto_update_disabled():
        return None, (
            "Unattended updates disabled "
            "(CLAWMETRY_AUTO_UPDATE kill switch or CI environment)"
        )
    try:
        req = urllib.request.Request(
            "https://pypi.org/pypi/clawmetry/json",
            headers={"User-Agent": f"clawmetry/{current}"},
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
    except Exception as exc:
        return None, f"PyPI check failed ({exc}); skipping unattended update"
    min_age = _autoupdate_min_age_hours()
    target = _newest_aged_in_version(data.get("releases", {}), current, min_age)
    if not target:
        latest = data.get("info", {}).get("version", "") or current
        if latest == current:
            return None, f"Already on latest version ({current})"
        return None, (
            f"Newest release v{latest} has not aged past the "
            f"{min_age:g}h stability window yet; nothing to install"
        )
    return target, (
        f"Unattended target: v{target} "
        f"(newest release aged past the {min_age:g}h stability window)"
    )


def _cmd_update(args=None) -> None:
    """Self-update clawmetry to the latest PyPI version.

    ``--unattended`` (the desktop shell's 6h background path) routes target
    selection through the daemon's update policy (kill switch + stability
    window) via ``_unattended_update_target`` and pins the pip install to
    that version; the plain interactive command keeps installing the
    absolute latest.
    """
    import subprocess

    unattended = bool(getattr(args, "unattended", False))
    try:
        from dashboard import __version__ as current
    except Exception:
        current = "unknown"
    print(f"Current version: {current}")
    install_spec = "clawmetry"
    if unattended:
        target, reason = _unattended_update_target(current)
        print(reason)
        if not target:
            return
        install_spec = f"clawmetry=={target}"
    print("Checking for updates...")
    try:
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "pip",
                "install",
                "--upgrade",
                "--break-system-packages",
                install_spec,
            ],
            capture_output=True,
            text=True,
            timeout=120,
        )
        if result.returncode == 0:
            # Check new version
            try:
                new_ver = subprocess.run(
                    [
                        sys.executable,
                        "-c",
                        "from dashboard import __version__; print(__version__)",
                    ],
                    capture_output=True,
                    text=True,
                    timeout=10,
                ).stdout.strip()
            except Exception:
                new_ver = "unknown"
            if new_ver == current:
                print(f"Already on latest version ({current})")
            else:
                print(f"Updated: {current} → {new_ver}")
                # Restart daemon if running
                try:
                    from clawmetry.sync import CONFIG_FILE

                    if CONFIG_FILE.exists():
                        print("Restarting sync daemon...")
                        # `clawmetry sync` re-registers the launchd/systemd unit
                        # (bootout+bootstrap) = a safe restart. The old call to
                        # the non-existent `daemon restart` subcommand silently
                        # failed, so the daemon kept running the OLD wheel.
                        subprocess.run(
                            ["clawmetry", "sync", "--restart"],
                            capture_output=True,
                            timeout=20,
                        )
                        print("Daemon restarted with new version")
                except Exception:
                    print("Tip: restart the daemon to use the new version")
        else:
            print(f"Update failed:\n{result.stderr}")
            sys.exit(1)
    except subprocess.TimeoutExpired:
        print("Update timed out. Try manually: pip install --upgrade clawmetry")
        sys.exit(1)
    except Exception as e:
        print(f"Update error: {e}")
        sys.exit(1)


def _read_key_from_file(path: str) -> tuple[bool, str, str]:
    """Read a license key from ``path`` for ``--file <path>``.

    Returns ``(ok, key, message)``. On success ``key`` is the trimmed contents
    (leading/trailing whitespace and a single trailing newline are stripped —
    the same shape ``activate()`` / ``inspect_key()`` accept) and ``message``
    is empty. On failure ``key`` is empty and ``message`` is a human-readable
    reason (missing file, unreadable, empty). Never raises: every OS error is
    caught and surfaced through ``message`` so the caller can render the same
    ``ok=false`` envelope both branches already use for a missing positional
    key. Kept as a module-level helper so the ``activate`` shortcut and
    ``license activate|verify`` share ONE reader — a bug fix in either lands
    for all three subcommands, and tests can exercise the reader once.
    """
    if not path:
        return False, "", "Usage: --file <path> requires a path"
    try:
        with open(path, "r", encoding="utf-8") as fh:
            raw = fh.read()
    except FileNotFoundError:
        return False, "", f"--file: not found: {path}"
    except IsADirectoryError:
        return False, "", f"--file: is a directory, expected a file: {path}"
    except PermissionError:
        return False, "", f"--file: permission denied: {path}"
    except OSError as exc:
        return False, "", f"--file: could not read {path}: {exc}"
    key = (raw or "").strip()
    if not key:
        return False, "", f"--file: {path} is empty"
    return True, key, ""


def _resolve_activate_key(args) -> tuple[bool, str, str]:
    """Resolve the license key from either ``args.key`` (positional) or
    ``args.file`` (``--file <path>``). Exactly one must be supplied — passing
    both is refused so a wrapper does not silently prefer one over the other
    on a mistake, and passing neither is refused with the same "Usage:" line
    the file-less path used before this flag existed.

    Returns ``(ok, key, message)`` matching :func:`_read_key_from_file` so the
    caller renders the same ``ok=false`` envelope regardless of which error
    branch fired.
    """
    file_path = (getattr(args, "file", None) or "").strip()
    key = (getattr(args, "key", None) or "").strip()
    if file_path and key:
        return (
            False,
            "",
            "Usage: pass either <KEY> or --file <path>, not both",
        )
    if file_path:
        return _read_key_from_file(file_path)
    if key:
        return True, key, ""
    return False, "", "Usage: clawmetry activate <KEY>  (or --file <path>)"


def _cmd_activate(args) -> None:
    """clawmetry activate <KEY> — install a self-hosted Pro/Enterprise license.

    Shortcut for ``clawmetry license activate <KEY>``. Accepts the same
    ``--json`` flag so a wrapper script can activate a key and read the
    outcome without screen-scraping. The JSON envelope is byte-identical to
    what ``clawmetry license activate <KEY> --json`` emits
    (``{action: "activate", ok, message}``) so a script that already parses
    the license subcommand does not need to branch on which spelling ran.

    ``--file <path>`` reads the key from a file instead of the command line,
    keeping the raw token out of shell history / ``ps`` listings. Exactly one
    of the positional key and ``--file`` must be supplied.
    """
    from clawmetry import license as _lic

    as_json = bool(getattr(args, "as_json", False))
    ok_read, key, read_msg = _resolve_activate_key(args)
    if not ok_read:
        if as_json:
            _license_json_dump({"action": "activate", "ok": False, "message": read_msg})
        else:
            print(f"❌  {read_msg}")
        sys.exit(1)
    ok, msg = _lic.activate(key, node_id=_lic._node_id(), actor="cli")
    if as_json:
        _license_json_dump({"action": "activate", "ok": bool(ok), "message": msg})
        if not ok:
            sys.exit(1)
        return
    if ok:
        print(f"✅  {msg}")
        print("    Run `clawmetry license` to see status. Restart the daemon to load Pro features.")
    else:
        print(f"❌  {msg}")
        print("    Need a key? Buy a self-hosted license at https://clawmetry.com/pricing")
        sys.exit(1)


def _resolve_license_action_key(args, action: str) -> tuple[bool, str, str]:
    """Same contract as :func:`_resolve_activate_key` but for ``clawmetry
    license <activate|verify>``, whose positional key is bound to
    ``license_key`` (not ``key``) by argparse. The ``action`` string just
    picks the ``Usage:`` line that best names the subcommand — the rest of
    the logic mirrors the shortcut resolver so a bug in either lands for
    both spellings.
    """
    file_path = (getattr(args, "file", None) or "").strip()
    key = (getattr(args, "license_key", None) or "").strip()
    if file_path and key:
        return (
            False,
            "",
            "Usage: pass either <KEY> or --file <path>, not both",
        )
    if file_path:
        return _read_key_from_file(file_path)
    if key:
        return True, key, ""
    return False, "", f"Usage: clawmetry license {action} <KEY>  (or --file <path>)"


def _license_json_dump(payload: dict) -> None:
    """Emit ``payload`` as pretty JSON on stdout for ``clawmetry license --json``.

    Isolated so tests can capture the exact serialisation shape and so the
    ``--json`` branches stay a single line each. Uses ``sort_keys=True`` to
    keep the envelope stable across Python versions and across whichever
    order the caller populated the dict.
    """
    import json as _json

    print(_json.dumps(payload, indent=2, sort_keys=True))


def _cmd_license(args) -> None:
    """clawmetry license [activate|status|deactivate|fingerprint|verify] — manage
    the self-hosted license.

    Human output mirrors the pre-``--json`` block character-for-character; the
    ``--json`` branch emits ``{action, ok, ...}`` on stdout so a wrapper script
    can parse license state (and exit code) without screen-scraping the human
    table. Every branch preserves the never-crash contract on
    :func:`clawmetry.license.current_license_info` / :func:`inspect_key` /
    :func:`pubkey_info` — a failure surfaces as ``ok=false`` on the payload
    AND a non-zero exit so pipes still detect it.
    """
    action = getattr(args, "license_action", None) or "status"
    as_json = bool(getattr(args, "as_json", False))

    if action == "activate":
        # ``license_key`` is the positional arg; ``file`` is the ``--file`` flag.
        # _resolve_license_action_key() normalises the two into a single trimmed
        # key or an ok=false envelope so the activate/verify branches share ONE
        # reader (matches the top-level ``clawmetry activate`` shortcut).
        ok_read, key, read_msg = _resolve_license_action_key(args, "activate")
        if not ok_read:
            if as_json:
                _license_json_dump({
                    "action": "activate",
                    "ok": False,
                    "message": read_msg,
                })
            else:
                print(f"❌  {read_msg}")
            sys.exit(1)
        from clawmetry import license as _lic
        ok, msg = _lic.activate(key, node_id=_lic._node_id(), actor="cli")
        if as_json:
            _license_json_dump({"action": "activate", "ok": bool(ok), "message": msg})
            if not ok:
                sys.exit(1)
            return
        if ok:
            print(f"✅  {msg}")
            print("    Run `clawmetry license status` to verify. Restart the daemon to load Pro features.")
        else:
            print(f"❌  {msg}")
            print("    Need a key? Buy a self-hosted license at https://clawmetry.com/pricing")
            sys.exit(1)

    elif action == "deactivate":
        from clawmetry import license as _lic
        ok, removed = _lic.deactivate(actor="cli")
        if as_json:
            _license_json_dump({
                "action": "deactivate",
                "ok": bool(ok),
                "removed": bool(removed),
            })
            if not ok:
                sys.exit(1)
            return
        if not ok:
            print("❌  Could not remove the license file. Check filesystem permissions.")
            sys.exit(1)
        if removed:
            print("✅  License removed. ClawMetry will revert to OSS tier on next restart.")
        else:
            print("ℹ️  No license key installed — nothing to deactivate.")

    elif action == "fingerprint":
        from clawmetry import license as _lic
        info = _lic.pubkey_info()
        fp = info.get("fingerprint_sha256")
        if as_json:
            _license_json_dump({
                "action": "fingerprint",
                "ok": bool(fp),
                "pubkey": info,
            })
            if not fp:
                sys.exit(1)
            return
        print("ClawMetry License Public Key\n" + "─" * 40)
        print(f"  Algorithm:   {info.get('algorithm', 'ed25519')}")
        print(f"  Format:      {info.get('format', '')}")
        if not fp:
            print("  Fingerprint: ⚠️  unavailable (embedded key failed to parse)")
            print("               This may indicate a corrupted or tampered install.")
            sys.exit(1)
        # Group the hex into 8-byte pairs for readability, mirroring SSH style.
        grouped = ":".join(fp[i : i + 4] for i in range(0, len(fp), 4))
        print(f"  SHA-256:     {fp}")
        print(f"  Grouped:     {grouped}")
        print(f"  Short:       {info.get('fingerprint_short')}")
        print("\n  Compare this fingerprint against the canonical value")
        print("  published at https://clawmetry.com/security to confirm your")
        print("  install carries the genuine license-verification key.")

    elif action == "verify":
        # Dry-run: verify a key OFFLINE and show what it would unlock,
        # WITHOUT writing anything to disk. Useful for support and pre-flight.
        ok_read, key, read_msg = _resolve_license_action_key(args, "verify")
        if not ok_read:
            if as_json:
                _license_json_dump({
                    "action": "verify",
                    "ok": False,
                    "status": "usage",
                    "inspection": None,
                    "message": read_msg,
                })
            else:
                print(f"❌  {read_msg}")
            sys.exit(1)
        from clawmetry import license as _lic
        info = _lic.inspect_key(key)
        if as_json:
            if info is None:
                _license_json_dump({
                    "action": "verify",
                    "ok": False,
                    "status": "invalid",
                    "inspection": None,
                })
                sys.exit(1)
            _license_json_dump({
                "action": "verify",
                "ok": bool(info.get("valid")),
                "status": info.get("status", "unknown"),
                "inspection": info,
            })
            if not info.get("valid"):
                sys.exit(1)
            return
        print("ClawMetry License Verify (dry-run)\n" + "─" * 40)
        if info is None:
            print("  Result:      ❌  Invalid or unrecognized license key")
            print("  Disk:        nothing written")
            sys.exit(1)
        status = info.get("status", "unknown")
        tier = str(info.get("tier", "pro")).capitalize()
        if not info.get("valid"):
            # Expired-but-parseable: show what it WAS for so support can confirm.
            print(f"  Result:      ⚠️  {status} (signature verified, but expired)")
            print(f"  Was for:     {tier} · {info.get('nodes', 1)} node(s)")
            if info.get("days_left") is not None:
                print(f"  Expired:     {abs(info['days_left'])} day(s) ago")
        else:
            print("  Result:      ✅  valid (signature verified offline)")
            print(f"  Would set:   {tier} (self-hosted)")
            print(f"  Nodes:       {info.get('nodes', 1)}")
            if info.get("days_left") is not None:
                print(f"  Expires:     in {info['days_left']} day(s)")
        if info.get("sub"):
            print(f"  Account:     {info['sub']}")
        print("  Disk:        nothing written (run `clawmetry license activate <KEY>` to install)")

    else:
        from clawmetry import license as _lic
        info = _lic.current_license_info()
        if as_json:
            if info is None:
                _license_json_dump({
                    "action": "status",
                    "ok": True,
                    "installed": False,
                    "plan": "oss",
                    "license": None,
                })
                return
            valid = bool(info.get("valid"))
            _license_json_dump({
                "action": "status",
                "ok": valid,
                "installed": True,
                "plan": (str(info.get("tier", "pro")) if valid else "oss"),
                "license": info,
            })
            return
        print("ClawMetry License\n" + "─" * 40)
        if not info:
            print("  Plan:        OSS (free)")
            print("  License:     none installed")
            print("  Unlocks:     OpenClaw runtime + NeMo governance + core observability")
            print("\n  Upgrade for all runtimes + advanced features:")
            print("    self-hosted key  →  clawmetry license activate <KEY>   (https://clawmetry.com/pricing)")
            return
        if not info.get("valid"):
            status = info.get("status", "invalid")
            print(f"  License:     ⚠️  {status} (run `clawmetry license activate <KEY>` with a current key)")
            return
        tier = str(info.get("tier", "pro")).capitalize()
        print(f"  Plan:        {tier} (self-hosted)")
        print(f"  Nodes:       {info.get('nodes', 1)}")
        if info.get("days_left") is not None:
            print(f"  Expires:     in {info['days_left']} day(s)")
        print("  E2E:         🔒 verified offline")
        fp = info.get("pubkey_fingerprint_sha256")
        if fp:
            print(f"  Trust key:   sha256:{fp[:16]}…  (clawmetry license fingerprint)")


def _entitlement_why_payload(kind: str, key: str) -> dict:
    """Resolve the lock-reason payload for a single feature/runtime/channels id.

    Same shape the ``/api/entitlement/lock-reason`` HTTP endpoint emits so
    ``clawmetry <features|runtimes|channels> --why <id> --json`` and the
    dashboard cannot drift on the upgrade affordance. Never raises: any
    resolver failure returns the OSS-free "not locked, unknown" fallback so
    a wrapper script always sees a parseable response — matches the
    never-crash contract documented on :func:`get_entitlement`.

    ``kind="channels"`` treats ``key`` as a concurrent-adapter *count* (the
    channels axis is capacity-scoped, every adapter itself is free) and
    resolves against :func:`min_tier_for_channel_count` /
    :meth:`Entitlement.allows_channel_count`, mirroring
    :func:`_lock_row`'s "channels" branch so CLI and HTTP stay in lockstep.
    A non-integer ``key`` collapses to the never-crash grace-shape row.

    ``kind="nodes"`` is the capacity-axis sibling of ``"channels"`` for the
    registered-node count (fleet size) -- ``key`` is a node count, not an
    id, so a non-integer ``key`` follows the same grace-shape fallback as
    the ``"channels"`` branch. Backed by :func:`min_tier_for_node_count`
    / :meth:`Entitlement.allows_node_count`; mirrors
    ``GET /api/entitlement/lock-reason?nodes=<int>`` byte-for-byte so
    ``clawmetry nodes --why N`` and the HTTP surface cannot drift.
    """
    key = (key or "").strip().lower()
    try:
        from clawmetry import entitlements as _ent

        ent = _ent.get_entitlement()
        cur_tier = ent.tier
        cur_rank = _ent.tier_rank(cur_tier)
        if kind == "runtime":
            allowed = ent.allows_runtime(key)
            required = _ent.min_tier_for_runtime(key)
            reason = ent.lock_reason(key, kind="runtime")
        elif kind == "channels":
            # Capacity axis: ``key`` is a concurrent-adapter count. A
            # non-int collapses to the grace-shape row so a typo (e.g.
            # ``--why abc``) never crashes and never dangles an upgrade CTA.
            try:
                n = int(key)
            except (TypeError, ValueError):
                return {
                    "key": key,
                    "kind": kind,
                    "reason": None,
                    "locked": False,
                    "allowed": True,
                    "required_tier": None,
                    "required_tier_label": None,
                    "required_tier_rank": -1,
                    "current_tier": cur_tier,
                    "current_tier_rank": cur_rank,
                    "upgrade_required": False,
                }
            allowed = ent.allows_channel_count(n)
            required = _ent.min_tier_for_channel_count(n)
            reason = ent.lock_reason(str(n), kind="channels")
            # Canonicalise the key in the response so a caller passing "05"
            # or "5" sees the same string back.
            key = str(n)
        elif kind == "nodes":
            # Capacity axis: ``key`` is a registered-node count. Same
            # never-crash posture as the ``channels`` branch above -- a
            # typo (e.g. ``--why abc``) collapses to the grace-shape row.
            try:
                n = int(key)
            except (TypeError, ValueError):
                return {
                    "key": key,
                    "kind": kind,
                    "reason": None,
                    "locked": False,
                    "allowed": True,
                    "required_tier": None,
                    "required_tier_label": None,
                    "required_tier_rank": -1,
                    "current_tier": cur_tier,
                    "current_tier_rank": cur_rank,
                    "upgrade_required": False,
                }
            allowed = ent.allows_node_count(n)
            required = _ent.min_tier_for_node_count(n)
            reason = ent.lock_reason(str(n), kind="nodes")
            key = str(n)
        elif kind == "retention_days":
            # Capacity axis: ``key`` is an event-history window in days.
            # Sibling of the ``channels`` branch -- a non-int collapses to
            # the grace-shape row so ``--why abc`` never crashes and never
            # dangles an upgrade CTA the operator can't act on.
            try:
                n = int(key)
            except (TypeError, ValueError):
                return {
                    "key": key,
                    "kind": kind,
                    "reason": None,
                    "locked": False,
                    "allowed": True,
                    "required_tier": None,
                    "required_tier_label": None,
                    "required_tier_rank": -1,
                    "current_tier": cur_tier,
                    "current_tier_rank": cur_rank,
                    "upgrade_required": False,
                }
            allowed = ent.allows_retention_window(n)
            required = _ent.min_tier_for_retention_window(n)
            reason = ent.lock_reason(str(n), kind="retention_days")
            key = str(n)
        else:  # feature
            allowed = ent.allows_feature(key)
            required = _ent.min_tier_for_feature(key)
            reason = ent.lock_reason(key, kind="feature")
        req_rank = _ent.tier_rank(required) if required else -1
        required_label = _ent.tier_label(required) if required else None
        return {
            "key": key,
            "kind": kind,
            "reason": reason,
            "locked": reason is not None,
            "allowed": bool(allowed),
            "required_tier": required,
            "required_tier_label": required_label,
            "required_tier_rank": req_rank,
            "current_tier": cur_tier,
            "current_tier_rank": cur_rank,
            "upgrade_required": bool(required) and req_rank > cur_rank,
        }
    except Exception as exc:
        print(f"⚠️  entitlement resolution failed: {exc}", file=sys.stderr)
        return {
            "key": key,
            "kind": kind,
            "reason": None,
            "locked": False,
            "allowed": True,
            "required_tier": None,
            "required_tier_label": None,
            "required_tier_rank": -1,
            "current_tier": "oss",
            "current_tier_rank": 0,
            "upgrade_required": False,
        }


def _print_why_block(payload: dict) -> None:
    """Human-readable render of :func:`_entitlement_why_payload`.

    Mirrors the ``clawmetry tier`` / ``clawmetry features`` output style
    (aligned two-column block, single upgrade CTA when a paid tier unlocks
    the item) so shell operators recognise the layout across subcommands.

    For ``kind="channels"`` / ``kind="nodes"`` / ``kind="retention_days"``
    the header phrases the capacity question naturally ("what tier unlocks
    N concurrent channels?" / "what tier unlocks N nodes?" / "what tier
    unlocks N-day event retention?") since the key is a count, not an id
    -- otherwise the shared "why is X locked?" phrasing wins.
    """
    key = payload.get("key") or "(unknown)"
    kind = payload.get("kind") or "?"
    locked = bool(payload.get("locked"))
    if kind == "channels":
        print(f'ClawMetry: what tier unlocks {key} concurrent channels?')
    elif kind == "nodes":
        print(f'ClawMetry: what tier unlocks {key} nodes?')
    elif kind == "retention_days":
        print(f'ClawMetry: what tier unlocks {key}-day event retention?')
    else:
        print(f'ClawMetry: why is "{key}" locked?')
    print("─" * 40)
    print(f"  Kind:            {kind}")
    print(f"  Current tier:    {payload.get('current_tier', 'oss')}")
    print(f"  Locked:          {'yes' if locked else 'no'}")
    reason = payload.get("reason")
    if reason:
        print(f"  Reason:          {reason}")
    req = payload.get("required_tier")
    req_label = payload.get("required_tier_label")
    if req:
        rank = payload.get("required_tier_rank", -1)
        rank_hint = f" (rank {rank})" if isinstance(rank, int) and rank >= 0 else ""
        print(f"  Required tier:   {req_label or req}{rank_hint}")
    if payload.get("upgrade_required"):
        print("  Upgrade:         clawmetry license activate <KEY>")
    elif not locked and not payload.get("reason"):
        # Free/allowed or unknown id: don't dangle an upgrade CTA. Give the
        # operator a one-line hint of which case they hit so a `--why` on a
        # typo doesn't silently look like a "no lock" all-clear.
        if not req:
            print("  Note:            not a paid capability on this install")


def _cmd_tier(args) -> None:
    """clawmetry tier — print the resolved open-core entitlement.

    Read-only, side-effect free. Useful for scripting (``clawmetry tier --json
    | jq -r .tier``) and for the "what tier am I on?" diagnostic that's
    cheaper than the full ``clawmetry status`` block. Never raises — on any
    resolution error it falls back to the OSS-free shape so a shell wrapper
    always sees a valid response.

    Output:
      default — compact human-readable block matching the project style
      --json  — :func:`Entitlement.to_dict` serialized (indent=2 for piping
                to jq / direct viewing)
    """
    import json as _json

    try:
        from clawmetry import entitlements as _ent

        ent = _ent.get_entitlement()
        info = ent.to_dict()
    except Exception as exc:
        # The resolver itself never raises, but a broken install (missing dep,
        # corrupt module) could. Match the never-crash contract — log the
        # warning to stderr and emit the OSS-free fallback so scripts keep
        # working.
        print(f"⚠️  tier resolution failed: {exc}", file=sys.stderr)
        info = {
            "tier": "oss",
            "source": "oss",
            "node_limit": 1,
            "expiry": None,
            "expired": False,
            "is_paid": False,
            "grace": True,
            "enforced": False,
            "runtimes": ["nemoclaw", "openclaw"],
            "features": [],
            "free_runtimes": ["nemoclaw", "openclaw"],
            "paid_runtimes": [],
            "all_runtimes": ["nemoclaw", "openclaw"],
        }

    if getattr(args, "as_json", False):
        print(_json.dumps(info, indent=2, sort_keys=True))
        return

    tier = str(info.get("tier", "oss")).lower()
    source = str(info.get("source", "oss"))
    grace = bool(info.get("grace", True))
    runtimes = list(info.get("runtimes") or [])
    all_runtimes = list(info.get("all_runtimes") or [])
    locked = [r for r in all_runtimes if r not in set(runtimes)]
    features = list(info.get("features") or [])

    tier_label = "OSS (free)" if tier == "oss" else tier.replace("_", " ").title()
    mode = "🟡 grace  (set CLAWMETRY_ENFORCE=1 to enforce)" if grace else "🔒 enforced"

    print("ClawMetry Tier\n" + "─" * 40)
    print(f"  Tier:        {tier_label}")
    print(f"  Source:      {source}")
    print(f"  Mode:        {mode}")
    expiry = info.get("expiry")
    if expiry:
        expired = "expired" if info.get("expired") else "valid"
        print(f"  Expiry:      {int(expiry)} ({expired})")
    if info.get("node_limit") and info["node_limit"] != 1:
        print(f"  Node limit:  {info['node_limit']}")
    if runtimes:
        print(f"  Runtimes:    {', '.join(runtimes)}")
    if locked:
        print(f"  Locked:      {', '.join(locked)}")
    print(f"  Features:    {len(features)} unlocked")


def _cmd_runtimes(args) -> None:
    """clawmetry runtimes — list every observable runtime and which are unlocked.

    Sibling of :func:`_cmd_tier`: that one answers "what tier am I on?", this
    one answers "which runtimes is this install cleared to observe?". Reads
    :func:`clawmetry.entitlements.runtime_catalog` -- the same source the
    dashboard's ``GET /api/runtimes`` consumes -- so the CLI and the UI cannot
    drift.

    Never raises. A poisoned catalog read surfaces the error inline (a warning
    row in the human table, or an ``error`` key on the JSON payload with
    ``runtimes=[]``) so a wrapper script always sees a parseable response.
    Matches the never-crash contract documented on :func:`get_entitlement`.

    Output:
      default -- compact table (id, label, tier, status)
      --json  -- ``{tier, grace, enforced, runtimes: [...], error?: str}``
    """
    import json as _json

    from clawmetry import entitlements as _ent

    why = (getattr(args, "why", None) or "").strip().lower()
    if why:
        payload = _entitlement_why_payload("runtime", why)
        if getattr(args, "as_json", False):
            print(_json.dumps(payload, indent=2, sort_keys=True))
        else:
            _print_why_block(payload)
        return

    try:
        ent = _ent.get_entitlement()
        tier = ent.tier
        grace = bool(ent.grace)
        enforced = _ent.is_enforced()
    except Exception as exc:
        # Mirror _cmd_tier's never-crash fallback: a broken install still gets
        # a parseable shape, with the failure surfaced to stderr so it isn't
        # silently lost in a pipeline.
        print(f"⚠️  entitlement resolution failed: {exc}", file=sys.stderr)
        tier, grace, enforced = "oss", True, False

    rows: list[dict] = []
    catalog_error: str | None = None
    try:
        rows = list(_ent.runtime_catalog())
    except Exception as exc:
        catalog_error = str(exc)

    if getattr(args, "as_json", False):
        payload: dict = {
            "tier": tier,
            "grace": grace,
            "enforced": enforced,
            "runtimes": rows,
        }
        if catalog_error:
            payload["error"] = catalog_error
        print(_json.dumps(payload, indent=2, sort_keys=True))
        return

    mode_line = "off (grace)" if not enforced else "on"
    print("ClawMetry Runtimes\n" + "─" * 40)
    print(f"  Tier:        {tier}")
    print(f"  Enforcement: {mode_line}")
    if catalog_error:
        print(f"  ⚠️  catalog error: {catalog_error}")
        return

    any_locked = False
    print()
    print(f"  {'ID':<14} {'Label':<14} {'Tier':<6} Status")
    print("  " + "─" * 50)
    for row in rows:
        rid = str(row.get("id", ""))
        label = str(row.get("label", rid))
        is_free = bool(row.get("free", False))
        locked = bool(row.get("locked", False))
        if locked:
            status = "🔒 locked"
            any_locked = True
        else:
            status = "✅ available"
        tier_tag = "free" if is_free else "paid"
        print(f"  {rid:<14} {label:<14} {tier_tag:<6} {status}")
    if any_locked:
        print()
        print("  Upgrade: clawmetry license activate <KEY>")


def _cmd_features(args) -> None:
    """clawmetry features — list every observable feature and which are unlocked.

    Sibling of :func:`_cmd_runtimes`: that one answers "which runtimes is
    this install cleared to observe?", this one answers the same question
    for features. Reads :func:`clawmetry.entitlements.feature_catalog` --
    the same source the dashboard's ``GET /api/features`` consumes -- so the
    CLI and the UI cannot drift on the locked-but-visible upgrade affordance.

    Never raises. A poisoned catalog read surfaces the error inline (a
    warning row in the human table, or an ``error`` key on the JSON payload
    with ``features=[]``) so a wrapper script always sees a parseable
    response. Matches the never-crash contract documented on
    :func:`get_entitlement`.

    Output:
      default -- compact table (id, label, tier, status)
      --json  -- ``{tier, grace, enforced, features: [...], error?: str}``
    """
    import json as _json

    from clawmetry import entitlements as _ent

    why = (getattr(args, "why", None) or "").strip().lower()
    if why:
        payload = _entitlement_why_payload("feature", why)
        if getattr(args, "as_json", False):
            print(_json.dumps(payload, indent=2, sort_keys=True))
        else:
            _print_why_block(payload)
        return

    try:
        ent = _ent.get_entitlement()
        tier = ent.tier
        grace = bool(ent.grace)
        enforced = _ent.is_enforced()
    except Exception as exc:
        # Mirror _cmd_runtimes' never-crash fallback: a broken install still
        # gets a parseable shape, with the failure surfaced to stderr so it
        # isn't silently lost in a pipeline.
        print(f"⚠️  entitlement resolution failed: {exc}", file=sys.stderr)
        tier, grace, enforced = "oss", True, False

    rows: list[dict] = []
    catalog_error: str | None = None
    try:
        rows = list(_ent.feature_catalog())
    except Exception as exc:
        catalog_error = str(exc)

    if getattr(args, "as_json", False):
        payload: dict = {
            "tier": tier,
            "grace": grace,
            "enforced": enforced,
            "features": rows,
        }
        if catalog_error:
            payload["error"] = catalog_error
        print(_json.dumps(payload, indent=2, sort_keys=True))
        return

    mode_line = "off (grace)" if not enforced else "on"
    print("ClawMetry Features\n" + "─" * 40)
    print(f"  Tier:        {tier}")
    print(f"  Enforcement: {mode_line}")
    if catalog_error:
        print(f"  ⚠️  catalog error: {catalog_error}")
        return

    any_locked = False
    print()
    print(f"  {'ID':<28} {'Label':<28} {'Tier':<14} Status")
    print("  " + "─" * 80)
    for row in rows:
        # Alias rows duplicate a canonical feature -- hide them so the table
        # mirrors the upgrade affordance shown in /pricing rather than
        # advertising deprecated names.
        if row.get("alias"):
            continue
        fid = str(row.get("id", ""))
        label = str(row.get("label", fid))
        feat_tier = str(row.get("tier", "oss"))
        is_free = bool(row.get("free", False))
        locked = bool(row.get("locked", False))
        if locked:
            status = "🔒 locked"
            any_locked = True
        else:
            status = "✅ available"
        tier_tag = "free" if is_free else feat_tier
        print(f"  {fid:<28} {label:<28} {tier_tag:<14} {status}")
    if any_locked:
        print()
        print("  Upgrade: clawmetry license activate <KEY>")


def _cmd_channels(args) -> None:
    """clawmetry channels — list every chat-channel adapter and the tier cap.

    Sibling of :func:`_cmd_runtimes` / :func:`_cmd_features` for the third
    entitlement axis. Every chat channel is FREE at every tier -- the
    ``channels`` capacity axis governs how many concurrent channels each
    plan admits, not which adapters unlock -- so every row surfaces as
    available. The tier-scoped concurrent-channel cap is what upgrades
    unlock, and it prints in the header block. Reads
    :func:`clawmetry.entitlements.channel_catalog` -- the same source the
    dashboard's channel-picker consumes -- so the CLI and the UI cannot
    drift on the adapter list.

    Never raises. A poisoned catalog read surfaces the error inline (a
    warning row in the human table, or an ``error`` key on the JSON payload
    with ``channels=[]``) so a wrapper script always sees a parseable
    response. Matches the never-crash contract documented on
    :func:`get_entitlement`.

    Output:
      default -- header block (tier / enforcement / channel cap) + table
                 (id, label, status) of every adapter
      --json  -- ``{tier, grace, enforced, channel_limit, channels: [...],
                 error?: str}``
      --why N -- lock-reason payload for N concurrent channels (same shape
                 as ``GET /api/entitlement/lock-reason?channels=N``); pair
                 with ``--json`` for scriptable output.
    """
    import json as _json

    from clawmetry import entitlements as _ent

    why = (getattr(args, "why", None) or "").strip().lower()
    if why:
        payload = _entitlement_why_payload("channels", why)
        if getattr(args, "as_json", False):
            print(_json.dumps(payload, indent=2, sort_keys=True))
        else:
            _print_why_block(payload)
        return

    try:
        ent = _ent.get_entitlement()
        tier = ent.tier
        grace = bool(ent.grace)
        enforced = _ent.is_enforced()
        channel_limit = ent.channel_limit()
    except Exception as exc:
        # Mirror _cmd_runtimes / _cmd_features never-crash fallback: a
        # broken install still gets a parseable shape, with the failure
        # surfaced to stderr so it isn't silently lost in a pipeline.
        print(f"⚠️  entitlement resolution failed: {exc}", file=sys.stderr)
        tier, grace, enforced, channel_limit = "oss", True, False, None

    rows: list[dict] = []
    catalog_error: str | None = None
    try:
        rows = list(_ent.channel_catalog())
    except Exception as exc:
        catalog_error = str(exc)

    if getattr(args, "as_json", False):
        payload: dict = {
            "tier": tier,
            "grace": grace,
            "enforced": enforced,
            "channel_limit": channel_limit,
            "channels": rows,
        }
        if catalog_error:
            payload["error"] = catalog_error
        print(_json.dumps(payload, indent=2, sort_keys=True))
        return

    mode_line = "off (grace)" if not enforced else "on"
    cap_line = "unlimited" if channel_limit in (None, 0) else str(channel_limit)
    print("ClawMetry Channels\n" + "─" * 40)
    print(f"  Tier:        {tier}")
    print(f"  Enforcement: {mode_line}")
    print(f"  Channel cap: {cap_line}  (concurrent adapters)")
    if catalog_error:
        print(f"  ⚠️  catalog error: {catalog_error}")
        return

    print()
    print(f"  {'ID':<16} {'Label':<20} Status")
    print("  " + "─" * 50)
    for row in rows:
        cid = str(row.get("id", ""))
        label = str(row.get("label", cid))
        # Every channel adapter is free at every tier; the cap is separate.
        # Surface the row identically to a free/available runtime row.
        status = "✅ available"
        print(f"  {cid:<16} {label:<20} {status}")


def _cmd_nodes(args) -> None:
    """clawmetry nodes — show the resolved node-count cap for this install.

    Capacity-axis sibling of :func:`_cmd_channels` for the ``nodes`` axis.
    There is no enumerable adapter list here -- ``nodes`` is purely a
    per-tier cap (Free / Cloud Free = 1; every paid tier is license-bound
    to the ``nodes`` field on the payload; Enterprise is unlimited) --
    so the default output is the header block alone. ``--why N`` answers
    "what tier admits N registered nodes?" using the same lock-reason
    payload ``clawmetry channels --why N`` emits so a wrapper script written
    against either surface works interchangeably.

    Reads :attr:`clawmetry.entitlements.Entitlement.node_limit` -- the same
    field the fleet-registration path checks -- so the CLI and the runtime
    cannot drift on the effective cap.

    Never raises. A poisoned resolver surfaces the error inline (a warning
    row in the human table, or an ``error`` key on the JSON payload with
    ``node_limit=null``) so a wrapper script always sees a parseable
    response. Matches the never-crash contract documented on
    :func:`get_entitlement`.

    Output:
      default -- header block (tier / enforcement / node cap)
      --json  -- ``{tier, grace, enforced, node_limit, error?: str}``
      --why N -- lock-reason payload for N registered nodes (same shape
                 as ``GET /api/entitlement/lock-reason?nodes=N``); pair
                 with ``--json`` for scriptable output.
    """
    import json as _json

    from clawmetry import entitlements as _ent

    why = (getattr(args, "why", None) or "").strip().lower()
    if why:
        payload = _entitlement_why_payload("nodes", why)
        if getattr(args, "as_json", False):
            print(_json.dumps(payload, indent=2, sort_keys=True))
        else:
            _print_why_block(payload)
        return

    resolve_error: str | None = None
    try:
        ent = _ent.get_entitlement()
        tier = ent.tier
        grace = bool(ent.grace)
        enforced = _ent.is_enforced()
        # ``node_limit`` is an int on the dataclass; <=0 is the unlimited
        # sentinel licenses use for Enterprise, so surface it as ``None``
        # (matches the ``channel_limit`` JSON convention).
        raw_limit = getattr(ent, "node_limit", None)
        if isinstance(raw_limit, int) and raw_limit > 0:
            node_limit: int | None = raw_limit
        else:
            node_limit = None
    except Exception as exc:
        # Mirror _cmd_channels never-crash fallback: a broken install still
        # gets a parseable shape, with the failure surfaced to stderr so it
        # isn't silently lost in a pipeline.
        print(f"⚠️  entitlement resolution failed: {exc}", file=sys.stderr)
        tier, grace, enforced, node_limit = "oss", True, False, None
        resolve_error = str(exc)

    if getattr(args, "as_json", False):
        payload: dict = {
            "tier": tier,
            "grace": grace,
            "enforced": enforced,
            "node_limit": node_limit,
        }
        if resolve_error:
            payload["error"] = resolve_error
        print(_json.dumps(payload, indent=2, sort_keys=True))
        return

    mode_line = "off (grace)" if not enforced else "on"
    cap_line = "unlimited" if node_limit is None else str(node_limit)
    print("ClawMetry Nodes\n" + "─" * 40)
    print(f"  Tier:        {tier}")
    print(f"  Enforcement: {mode_line}")
    print(f"  Node cap:    {cap_line}  (registered nodes)")
    if resolve_error:
        print(f"  ⚠️  resolver error: {resolve_error}")


def _cmd_retention(args) -> None:
    """clawmetry retention — event-retention window (capacity axis).

    Sibling of :func:`_cmd_channels` / :func:`_cmd_nodes` for the fourth
    entitlement axis. The ``retention_days`` capacity axis governs how far
    back in history each plan can hold event data before the store rolls
    over. Every event-store feature itself is free at every tier; what
    upgrades unlock is a longer window. The current tier cap prints in the
    header block alongside the effective cap (which applies the
    ``CLAWMETRY_RETENTION_DAYS`` env override, capped to the tier ceiling).

    Never raises: any resolver failure surfaces inline (a warning row in
    the human block, or the fields collapsed to ``null`` on the JSON
    payload) so a wrapper script always sees a parseable response. Matches
    the never-crash contract documented on :func:`get_entitlement`.

    Output:
      default -- header block (tier / enforcement / retention cap /
                 effective cap / env override)
      --json  -- ``{tier, grace, enforced, retention_days,
                 effective_retention_days, override_env_name,
                 override_env_value}``
      --why N -- lock-reason payload for an N-day retention window (same
                 shape as ``GET /api/entitlement/lock-reason?retention_days=N``);
                 pair with ``--json`` for scriptable output.
    """
    import json as _json

    from clawmetry import entitlements as _ent

    why = (getattr(args, "why", None) or "").strip().lower()
    if why:
        payload = _entitlement_why_payload("retention_days", why)
        if getattr(args, "as_json", False):
            print(_json.dumps(payload, indent=2, sort_keys=True))
        else:
            _print_why_block(payload)
        return

    override_env_name = getattr(_ent, "_RETENTION_OVERRIDE_ENV", "CLAWMETRY_RETENTION_DAYS")
    override_env_value = os.environ.get(override_env_name)

    try:
        ent = _ent.get_entitlement()
        tier = ent.tier
        grace = bool(ent.grace)
        enforced = _ent.is_enforced()
        retention_days = ent.event_retention_days()
        effective_days = ent.effective_retention_days()
    except Exception as exc:
        # Mirror the _cmd_channels never-crash fallback: a broken install
        # still gets a parseable shape, with the failure surfaced to stderr
        # so it isn't silently lost in a shell pipeline.
        print(f"⚠️  entitlement resolution failed: {exc}", file=sys.stderr)
        tier, grace, enforced = "oss", True, False
        retention_days, effective_days = None, None

    if getattr(args, "as_json", False):
        payload = {
            "tier": tier,
            "grace": grace,
            "enforced": enforced,
            "retention_days": retention_days,
            "effective_retention_days": effective_days,
            "override_env_name": override_env_name,
            "override_env_value": override_env_value,
        }
        print(_json.dumps(payload, indent=2, sort_keys=True))
        return

    mode_line = "off (grace)" if not enforced else "on"
    cap_line = "unlimited" if retention_days in (None, 0) else f"{retention_days} days"
    eff_line = (
        "unlimited" if effective_days in (None, 0) else f"{effective_days} days"
    )
    print("ClawMetry Retention\n" + "─" * 40)
    print(f"  Tier:            {tier}")
    print(f"  Enforcement:     {mode_line}")
    print(f"  Retention cap:   {cap_line}  (per-tier ceiling)")
    print(f"  Effective:       {eff_line}  (after env override)")
    env_display = override_env_value if override_env_value not in (None, "") else "(unset)"
    print(f"  {override_env_name}: {env_display}")


def _cmd_bundle(args) -> None:
    """clawmetry bundle — cheapest tier admitting a mixed 5-axis constraint bundle.

    Aggregate CLI sibling of :func:`_cmd_runtimes` / :func:`_cmd_features` /
    :func:`_cmd_channels` / :func:`_cmd_nodes` / :func:`_cmd_retention`: each
    of those answers ONE axis in isolation ("which runtimes does my tier
    unlock?", "how many concurrent channels?"), this one folds a mixed
    bundle across all five axes into ONE ``required_tier`` answer + the
    full ``affordable_tiers`` ladder that would qualify.

    Wraps :func:`clawmetry.entitlements.min_tier_for_all` (and
    :func:`affordable_tiers`) -- the same helpers ``/api/entitlement/
    required-tier`` and ``/api/entitlement/affordable-tiers`` consume --
    so the CLI, the JSON API, and any dashboard pricing tooltip cannot
    drift on the required-tier answer.

    Args:
      --features CSV       -- comma-separated feature ids (matches ``/required-tier?features=``)
      --runtimes CSV       -- comma-separated runtime ids (matches ``/required-tier?runtimes=``)
      --channels N         -- concurrent-channel count
      --retention-days N   -- desired retention window in days
      --nodes N            -- registered-node count
      --tier <perspective> -- resolve from a hypothetical perspective tier
                              (delegates to :func:`min_tier_for_all_at` /
                              :func:`affordable_tiers_at`; the answer is
                              perspective-independent by design, matching
                              the ``_at`` family's parity guarantee, but
                              the perspective is echoed on the payload so
                              a pricing tooltip's "if I were on X" copy
                              round-trips)
      --json               -- emit the payload as JSON (jq-friendly)

    Never raises. A poisoned resolver / helper collapses to the OSS-free
    "no constraints" fallback shape (``required_tier=None``,
    ``affordable_tiers=[]``, ``error`` populated on the JSON payload) so
    a wrapper script always sees a parseable response -- matches the
    never-crash contract documented on :func:`get_entitlement`.

    Output:
      default -- header block (tier / enforcement / perspective) + the
                 constraint bundle echoed back + ``Required tier`` line
                 + affordable-tiers table (id, label, status).
      --json  -- ``{tier, grace, enforced, perspective, constraints:
                 {features, runtimes, channels, retention_days, nodes},
                 required_tier, required_tier_label, required_tier_rank,
                 affordable_tiers:[...], error?: str}``
    """
    import json as _json

    from clawmetry import entitlements as _ent

    def _csv(raw):
        if raw is None:
            return []
        parts = [p.strip().lower() for p in str(raw).split(",")]
        return [p for p in parts if p]

    def _int_or_none(raw):
        if raw is None or raw == "":
            return None
        try:
            return int(raw)
        except (TypeError, ValueError):
            return None

    features = _csv(getattr(args, "features", None))
    runtimes = _csv(getattr(args, "runtimes", None))
    channels = _int_or_none(getattr(args, "channels", None))
    retention_days = _int_or_none(getattr(args, "retention_days", None))
    nodes = _int_or_none(getattr(args, "nodes", None))
    perspective_raw = getattr(args, "perspective", None)
    perspective = (perspective_raw or "").strip().lower() or None

    try:
        ent = _ent.get_entitlement()
        tier = ent.tier
        grace = bool(ent.grace)
        enforced = _ent.is_enforced()
    except Exception as exc:
        print(f"⚠️  entitlement resolution failed: {exc}", file=sys.stderr)
        tier, grace, enforced = "oss", True, False

    perspective_unknown = False
    if perspective is not None and perspective not in _ent._TIER_ORDER:
        perspective_unknown = True

    kwargs = dict(
        features=features or None,
        runtimes=runtimes or None,
        channels=channels,
        retention_days=retention_days,
        nodes=nodes,
    )

    required_tier: str | None = None
    ladder: list[dict] = []
    resolve_error: str | None = None
    if not perspective_unknown:
        try:
            if perspective:
                required_tier = _ent.min_tier_for_all_at(perspective, **kwargs)
                ladder_raw = _ent.affordable_tiers_at(perspective, **kwargs)
            else:
                required_tier = _ent.min_tier_for_all(**kwargs)
                ladder_raw = _ent.affordable_tiers(**kwargs)
            ladder = list(ladder_raw) if ladder_raw else []
        except Exception as exc:
            resolve_error = str(exc)

    required_tier_label = _ent.tier_label(required_tier) if required_tier else None
    required_tier_rank = _ent.tier_rank(required_tier) if required_tier else None

    payload: dict = {
        "tier": tier,
        "grace": grace,
        "enforced": enforced,
        "perspective": perspective,
        "constraints": {
            "features": features,
            "runtimes": runtimes,
            "channels": channels,
            "retention_days": retention_days,
            "nodes": nodes,
        },
        "required_tier": required_tier,
        "required_tier_label": required_tier_label,
        "required_tier_rank": required_tier_rank,
        "affordable_tiers": ladder,
    }
    if perspective_unknown:
        payload["error"] = f"unknown perspective tier: {perspective_raw}"
    elif resolve_error:
        payload["error"] = resolve_error

    if getattr(args, "as_json", False):
        print(_json.dumps(payload, indent=2, sort_keys=True))
        return

    mode_line = "off (grace)" if not enforced else "on"
    print("ClawMetry Bundle\n" + "─" * 40)
    print(f"  Tier:            {tier}")
    print(f"  Enforcement:     {mode_line}")
    if perspective:
        note = " (unknown -- ignored)" if perspective_unknown else ""
        print(f"  Perspective:     {perspective}{note}")
    print()
    print("  Constraints")
    feat_line = ", ".join(features) if features else "(none)"
    rt_line = ", ".join(runtimes) if runtimes else "(none)"
    ch_line = str(channels) if channels is not None else "(unset)"
    rd_line = str(retention_days) if retention_days is not None else "(unset)"
    nd_line = str(nodes) if nodes is not None else "(unset)"
    print(f"    Features:      {feat_line}")
    print(f"    Runtimes:      {rt_line}")
    print(f"    Channels:      {ch_line}")
    print(f"    Retention (d): {rd_line}")
    print(f"    Nodes:         {nd_line}")
    print()
    if payload.get("error"):
        print(f"  ⚠️  {payload['error']}")
        return
    if required_tier is None:
        print("  Required tier:   (no constraints supplied)")
        return
    label = required_tier_label or required_tier
    print(f"  Required tier:   {required_tier}  ({label})")

    if not ladder:
        return
    print()
    print(f"  {'ID':<20} {'Label':<24} Status")
    print("  " + "─" * 56)
    for row in ladder:
        rid = str(row.get("tier", ""))
        rlabel = str(row.get("tier_label", rid))
        status = "★ minimum" if row.get("is_minimum") else "  qualifies"
        print(f"  {rid:<20} {rlabel:<24} {status}")


def _cmd_diagnose(args) -> None:
    """clawmetry diagnose — surface the entitlement resolver inputs.

    Sibling of :func:`_cmd_tier` for operators who need to answer "why is
    my resolved tier what it is?": license file present or not, cloud
    plan cache present or not, enforcement env var, and the in-process
    resolver cache state. Reads
    :func:`clawmetry.entitlements.resolution_diagnostic` -- the same
    source ``GET /api/entitlement/diagnostic`` serves -- so the CLI and
    the HTTP surface cannot drift on the inputs they expose.

    Read-only, side-effect free. Never raises: any resolver failure
    surfaces inline (a warning line in the human block, or an ``error``
    key on the JSON payload with the partial dict intact) so a wrapper
    script always sees a parseable response. Matches the never-crash
    contract documented on :func:`get_entitlement`.

    Output:
      default -- human-readable block (license, cloud plan, enforce env,
                 cache state) matching the aligned two-column style
                 shared with ``clawmetry tier`` / ``features`` / ``runtimes``
      --json  -- :func:`resolution_diagnostic` dict serialized (indent=2,
                 sort_keys=True) so a shell wrapper can pipe it to jq
    """
    import json as _json

    from clawmetry import entitlements as _ent

    payload: dict = {}
    err: str | None = None
    try:
        payload = _ent.resolution_diagnostic()
    except Exception as exc:
        err = str(exc)
        print(f"⚠️  entitlement diagnostic failed: {exc}", file=sys.stderr)

    if getattr(args, "as_json", False):
        if err:
            payload = dict(payload)
            payload["error"] = err
        print(_json.dumps(payload, indent=2, sort_keys=True))
        return

    print("ClawMetry Diagnose\n" + "─" * 40)
    if err:
        print(f"  ⚠️  diagnostic error: {err}")
        return

    def _row(label: str, value) -> None:
        print(f"  {label:<24} {value}")

    lic_present = bool(payload.get("license_present"))
    lic_size = int(payload.get("license_size_bytes") or 0)
    lic_path = payload.get("license_path") or "?"
    _row("License file:", "yes" if lic_present else "no")
    _row("  path:", lic_path)
    if lic_present:
        _row("  size (bytes):", lic_size)
    if payload.get("license_error"):
        _row("  error:", payload["license_error"])

    cp_present = bool(payload.get("cloud_plan_present"))
    cp_size = int(payload.get("cloud_plan_size_bytes") or 0)
    cp_path = payload.get("cloud_plan_path") or "?"
    _row("Cloud plan cache:", "yes" if cp_present else "no")
    _row("  path:", cp_path)
    if cp_present:
        _row("  size (bytes):", cp_size)
    if payload.get("cloud_plan_error"):
        _row("  error:", payload["cloud_plan_error"])

    enforce_env = payload.get("enforce_env")
    is_enforced = bool(payload.get("is_enforced"))
    _row("Enforce env:", enforce_env if enforce_env not in (None, "") else "(unset)")
    _row("Enforced:", "yes" if is_enforced else "no (grace)")

    ret_env_name = payload.get("retention_override_env_name") or "?"
    ret_env_val = payload.get("retention_override_env_value")
    _row(
        f"{ret_env_name}:",
        ret_env_val if ret_env_val not in (None, "") else "(unset)",
    )

    age = payload.get("cache_age_seconds")
    ttl = payload.get("cache_ttl_seconds")
    hit = bool(payload.get("cache_hit_next_call"))
    cached_tier = payload.get("cache_cached_tier")
    _row("Cache age (s):", "-" if age is None else age)
    _row("Cache TTL (s):", "-" if ttl is None else ttl)
    _row("Cache hit next call:", "yes" if hit else "no")
    if cached_tier:
        _row("Cached tier:", cached_tier)
    if payload.get("cache_error"):
        _row("Cache error:", payload["cache_error"])



def _cmd_extensions(args) -> None:
    """clawmetry extensions -- surface loaded/failed entry-point plugins.

    Shell sibling of the always-Free, never-raise ``GET /api/extensions``
    endpoint. Answers the triage question an operator would otherwise tail
    daemon logs for: *did the paid package (``clawmetry-pro``) try to load,
    and if so did it succeed?* Payload also includes registered event hooks
    and their handler counts so a broken plugin that loaded but wired no
    handlers is visible at a glance.

    Reads :func:`clawmetry.extensions.loaded_plugins` /
    :func:`~clawmetry.extensions.failed_plugins` /
    :func:`~clawmetry.extensions.registered_events` /
    :func:`~clawmetry.extensions.handler_count` -- the same in-process
    introspection ``/api/extensions`` consumes -- so the CLI and HTTP
    surfaces cannot drift on loaded/failed/event/handler state.

    Never raises. If the extensions module itself is missing or the
    introspection helpers themselves raise, the shape falls back to empty
    lists / zero counts and the failure is surfaced to stderr so it isn't
    silently lost in a pipeline. A wrapper script always sees a parseable
    response -- matches the never-crash contract of :func:`_cmd_tier`,
    :func:`_cmd_runtimes`, and :func:`_cmd_features`.

    Output:
      default -- header + loaded / failed / events tables
      --json  -- ``{plugins, plugin_count, failed_plugins,
                    failed_plugin_count, events, handler_counts,
                    error?: str}`` (matches ``GET /api/extensions``)
    """
    import json as _json

    plugins: list[str] = []
    failed: list[dict] = []
    events: list[str] = []
    handler_counts: dict[str, int] = {}
    introspection_error: str | None = None

    try:
        from clawmetry import extensions as _ext

        try:
            plugins = list(_ext.loaded_plugins())
        except Exception as exc:
            introspection_error = f"loaded_plugins: {exc}"

        # ``failed_plugins`` shipped after ``loaded_plugins`` (see #33311f1)
        # so an older in-process ``clawmetry`` may not expose it. Degrade to
        # ``[]`` instead of crashing the whole command -- matches the
        # `/api/extensions` fallback posture.
        try:
            failed = [dict(entry) for entry in _ext.failed_plugins()]
        except AttributeError:
            failed = []
        except Exception as exc:
            introspection_error = (
                f"{introspection_error + '; ' if introspection_error else ''}"
                f"failed_plugins: {exc}"
            )

        try:
            events = list(_ext.registered_events())
        except Exception as exc:
            introspection_error = (
                f"{introspection_error + '; ' if introspection_error else ''}"
                f"registered_events: {exc}"
            )

        try:
            handler_counts = {evt: _ext.handler_count(evt) for evt in events}
        except Exception as exc:
            introspection_error = (
                f"{introspection_error + '; ' if introspection_error else ''}"
                f"handler_count: {exc}"
            )
    except Exception as exc:
        # Module import itself failed -- surface it to stderr but keep the
        # empty-shape fallback so a wrapper script still sees parseable
        # output.
        introspection_error = f"extensions module unavailable: {exc}"

    if introspection_error:
        print(f"⚠️  {introspection_error}", file=sys.stderr)

    if getattr(args, "as_json", False):
        payload: dict = {
            "plugins": plugins,
            "plugin_count": len(plugins),
            "failed_plugins": failed,
            "failed_plugin_count": len(failed),
            "events": events,
            "handler_counts": handler_counts,
        }
        if introspection_error:
            payload["error"] = introspection_error
        print(_json.dumps(payload, indent=2, sort_keys=True))
        return

    print("ClawMetry Extensions\n" + "─" * 40)
    print(f"  Loaded plugins: {len(plugins)}")
    print(f"  Failed plugins: {len(failed)}")
    print(f"  Event hooks:    {len(events)}")

    print()
    print("  Loaded")
    print("  " + "─" * 30)
    if plugins:
        for name in plugins:
            print(f"    ✅ {name}")
    else:
        print("    (none)")

    print()
    print("  Failed")
    print("  " + "─" * 30)
    if failed:
        for entry in failed:
            name = str(entry.get("name", ""))
            error = str(entry.get("error", ""))
            print(f"    ❌ {name}: {error}")
    else:
        print("    (none)")

    print()
    print("  Event hooks")
    print("  " + "─" * 30)
    if events:
        for evt in events:
            count = handler_counts.get(evt, 0)
            handler_word = "handler" if count == 1 else "handlers"
            print(f"    • {evt} ({count} {handler_word})")
    else:
        print("    (none)")


def _cmd_verify_integrity(args) -> None:
    """clawmetry verify-integrity — walk the hash chain and report validity.

    ``--json`` emits a stable envelope so wrapper scripts can branch on the
    outcome without screen-scraping the human table. The payload mirrors the
    ``LocalStore.verify_integrity`` return shape (``status``/``checked``/
    ``pre_chain``/``broken_at``/``error``/``node_id``) and adds two synthetic
    statuses for the environment errors that today only surface via exit
    code + text:

      - ``store_open_failed``  — cannot open the local store (exit 1)
      - ``daemon_too_old``     — daemon proxy returned None so ``verify_integrity``
                                 is not in its allowlist (exit 2)
      - ``error``              — ``verify_integrity`` itself raised (exit 1)

    Exit codes are unchanged from the human path: 0 for ``valid``/``empty``,
    1 for ``invalid``/``store_open_failed``/``error``, 2 for ``daemon_too_old``.
    Never crashes: any unexpected shape degrades to a parseable JSON payload
    with an ``error`` key so a shell pipeline always sees a valid response.

    Sibling of :func:`_cmd_tier` / :func:`_cmd_diagnose` / :func:`_cmd_license`
    which all carry ``--json`` for the same reason -- the CLI diagnostic
    surface stays uniformly scriptable.
    """
    import json as _json
    from clawmetry.local_store import get_store

    as_json = bool(getattr(args, "as_json", False))
    node_id = getattr(args, "node_id", None) or None
    scope_default = node_id or "all"

    def _emit_json(payload: dict, exit_code: int) -> None:
        print(_json.dumps(payload, indent=2, sort_keys=True))
        if exit_code:
            raise SystemExit(exit_code)

    if not as_json:
        print("ClawMetry Integrity Verify\n" + "─" * 40)

    try:
        store = get_store(read_only=True)
    except Exception as exc:
        if as_json:
            _emit_json(
                {
                    "status": "store_open_failed",
                    "node_id": scope_default,
                    "checked": 0,
                    "pre_chain": 0,
                    "broken_at": None,
                    "error": str(exc),
                },
                1,
            )
            return  # unreachable — _emit_json raises when exit_code != 0
        print(f"  Error: cannot open local store — {exc}")
        raise SystemExit(1) from exc

    try:
        result = store.verify_integrity(node_id=node_id)
    except Exception as exc:
        if as_json:
            _emit_json(
                {
                    "status": "error",
                    "node_id": scope_default,
                    "checked": 0,
                    "pre_chain": 0,
                    "broken_at": None,
                    "error": str(exc),
                },
                1,
            )
            return
        print(f"  Error: verification failed — {exc}")
        raise SystemExit(1) from exc

    # When a sync daemon is running, ``get_store(read_only=True)`` returns a
    # proxy that forwards through HTTP. Older daemons (< 0.12.343) do not
    # have ``verify_integrity`` in their method allowlist and return None.
    # Degrade gracefully instead of crashing on ``result["status"]``.
    if result is None:
        if as_json:
            _emit_json(
                {
                    "status": "daemon_too_old",
                    "node_id": scope_default,
                    "checked": 0,
                    "pre_chain": 0,
                    "broken_at": None,
                    "error": (
                        "daemon proxy returned None — verify_integrity is not in the"
                        " running daemon's method allowlist. Restart the sync daemon"
                        " to pick up the new wheel, then re-run."
                    ),
                },
                2,
            )
            return
        print("  Result:      ?  Could not reach the running daemon's verifier.")
        print("               This usually means the daemon is older than the CLI.")
        print("               Restart the sync daemon to pick up the new wheel, then re-run.")
        raise SystemExit(2)

    status = result.get("status") if isinstance(result, dict) else None
    checked = result.get("checked", 0) if isinstance(result, dict) else 0
    pre_chain = result.get("pre_chain", 0) if isinstance(result, dict) else 0
    scope = (result.get("node_id") if isinstance(result, dict) else None) or scope_default
    broken_at = result.get("broken_at") if isinstance(result, dict) else None
    error = result.get("error") if isinstance(result, dict) else None

    if as_json:
        exit_code = 1 if status == "invalid" else 0
        # Emit the store's shape verbatim so scripts pinning keys never drift
        # from what LocalStore.verify_integrity documents. Any non-dict result
        # (shouldn't happen, but the never-crash contract still applies)
        # collapses to a parseable error envelope.
        if isinstance(result, dict):
            payload = {
                "status": status or "error",
                "node_id": scope,
                "checked": int(checked or 0),
                "pre_chain": int(pre_chain or 0),
                "broken_at": broken_at,
                "error": error,
            }
        else:
            payload = {
                "status": "error",
                "node_id": scope_default,
                "checked": 0,
                "pre_chain": 0,
                "broken_at": None,
                "error": f"verify_integrity returned unexpected shape: {type(result).__name__}",
            }
            exit_code = 1
        _emit_json(payload, exit_code)
        return

    print(f"  Scope:       {scope}")
    print(f"  Checked:     {checked} stamped event(s)")
    if pre_chain:
        print(f"  Pre-chain:   {pre_chain} event(s) without hash (before integrity was enabled)")

    if status == "empty":
        print("  Result:      ○  No stamped events found")
        print("               (set CLAWMETRY_INTEGRITY=1 to enable stamping)")
    elif status == "valid":
        print(f"  Result:      ✅  VALID — chain intact across {checked} event(s)")
    else:
        print(f"  Result:      ❌  INVALID — {error}")
        print(f"  First break: {broken_at}")
        raise SystemExit(1)


def _cmd_login(args) -> None:
    """clawmetry login — sign in / sign up for ClawMetry Cloud.

    Friendly front door over the existing machinery: already logged in →
    show account info (same as `clawmetry account`); otherwise run the
    interactive connect flow (email OTP or Google/GitHub, incl. the
    headless paste-code path). `connect` stays for scripted/advanced use.
    """
    import json as _json

    cfg_path = os.path.expanduser("~/.clawmetry/config.json")
    api_key = ""
    try:
        with open(cfg_path, "r", encoding="utf-8") as f:
            api_key = (_json.load(f) or {}).get("api_key") or ""
    except Exception:
        pass
    if api_key:
        print("Already logged in — your account:")
        print()
        _cmd_account(args)
        print()
        print("Not you? `clawmetry disconnect` first, then `clawmetry login`.")
        return
    _cmd_connect(args)


def _purge_cloud_data(api_key: str, *, timeout: float = 15.0) -> tuple[bool, str]:
    """POST /api/account/purge-data — flush every trace of THIS account's
    telemetry from the cloud while keeping the account itself.

    Sister of the local ``--turn-off-cloud-sync`` marker flip: the marker
    stops future egress; this call deletes what already landed on the cloud.
    Best-effort — returns ``(ok, message)`` and never raises: if the network
    is down or the cloud rejects, local-only mode is still in effect and
    the user can retry the purge later. Skipped for self-hosted endpoints
    (``CLAWMETRY_ENDPOINT`` set) — the operator owns that data plane.
    """
    if not api_key:
        return (True, "no account linked")
    try:
        from clawmetry.endpoints import ingest_url, is_custom_endpoint
    except Exception as e:
        return (False, f"endpoints module unavailable: {e}")
    if is_custom_endpoint():
        return (True, "self-hosted endpoint — skipping managed-cloud purge")
    import json as _json
    import urllib.error as _ue
    import urllib.request as _ur
    url = ingest_url().rstrip("/") + "/api/account/purge-data"
    req = _ur.Request(
        url,
        data=_json.dumps({"confirm": "PURGE_DATA"}).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with _ur.urlopen(req, timeout=timeout) as resp:
            body = _json.loads(resp.read().decode("utf-8", errors="replace"))
    except _ue.HTTPError as e:
        detail = ""
        try:
            detail = e.read().decode("utf-8", errors="replace")[:200]
        except Exception:
            pass
        # A cloud that predates this endpoint answers 404. Fall back to
        # per-node DELETE so at least the visible node disappears.
        if e.code in (404, 405):
            return _purge_cloud_node_fallback(api_key, timeout=timeout)
        return (False, f"HTTP {e.code}{': ' + detail if detail else ''}")
    except (_ue.URLError, TimeoutError, OSError) as e:
        return (False, f"network error: {e}")
    except Exception as e:
        return (False, f"unexpected: {e}")
    purged = body.get("purged") or {}
    total = sum(v for v in purged.values() if isinstance(v, int) and v > 0)
    return (True, f"deleted {total} row(s) across {len(purged)} table(s)")


def _purge_cloud_node_fallback(api_key: str, *, timeout: float = 15.0) -> tuple[bool, str]:
    """Older cloud without ``/api/account/purge-data``: purge just this
    node via the per-node DELETE endpoint. Covers the visible fleet row
    even when the account-scoped purge isn't deployed yet.
    """
    import json as _json
    import urllib.error as _ue
    import urllib.parse as _up
    import urllib.request as _ur
    from clawmetry.endpoints import ingest_url
    from clawmetry.sync import CONFIG_FILE

    node_id = ""
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            node_id = (_json.load(f) or {}).get("node_id") or ""
    except Exception:
        pass
    if not node_id:
        return (False, "no node_id in config; cloud already has no /api/account/purge-data")
    url = (ingest_url().rstrip("/") + "/api/cloud/nodes/"
           + _up.quote(node_id, safe=""))
    req = _ur.Request(
        url,
        headers={"Authorization": f"Bearer {api_key}"},
        method="DELETE",
    )
    try:
        with _ur.urlopen(req, timeout=timeout) as resp:
            body = _json.loads(resp.read().decode("utf-8", errors="replace"))
    except _ue.HTTPError as e:
        return (False, f"per-node DELETE HTTP {e.code}")
    except (_ue.URLError, TimeoutError, OSError) as e:
        return (False, f"per-node DELETE network error: {e}")
    except Exception as e:
        return (False, f"per-node DELETE unexpected: {e}")
    purged = body.get("purged") or {}
    total = sum(v for v in purged.values() if isinstance(v, int) and v > 0)
    return (True, f"per-node fallback: deleted {total} row(s) (upgrade cloud for account-scoped purge)")


def _kick_daemon_for_toggle() -> None:
    """Bounce the sync daemon so any in-flight snapshot upload aborts.

    The nocloud marker gates every subsequent ``_post`` call, so the
    daemon self-stops within seconds even without a restart. But a
    snapshot POST that is ALREADY streaming its body can complete before
    the next marker check — restarting kills it mid-stream, so the user's
    "no more data goes to the cloud" expectation holds instantly. Best-
    effort; a machine without launchd/systemd (or without permission to
    poke either) just falls back to the marker-check behaviour.
    """
    import platform
    import subprocess as _sp
    system = platform.system()
    try:
        if system == "Darwin":
            uid = os.getuid()
            _sp.run(["launchctl", "kickstart", "-k",
                     f"gui/{uid}/com.clawmetry.sync"],
                    capture_output=True, check=False, timeout=5)
        elif system == "Linux":
            import shutil
            if shutil.which("systemctl"):
                for _scope in (["--user"], []):
                    _sp.run(["systemctl", *_scope, "restart", "clawmetry-sync"],
                            capture_output=True, check=False, timeout=5)
    except Exception:
        pass


def _cmd_cloud_toggle(enable: bool) -> int:
    """--turn-on-cloud-sync / --turn-off-cloud-sync.

    OFF: writes the ``~/.clawmetry/nocloud`` marker (stops future egress),
    then flushes every trace of this account's data from the cloud so the
    fleet page immediately shows zero data — best-effort; local-only still
    applies even if the purge call fails. Keeps the account key (unlike
    ``clawmetry disconnect``) so the user can flip sync back on later.

    ON: pure marker flip — the daemon checks ``is_cloud_disabled()`` on
    every cloud POST, so egress resumes within seconds without a restart.
    """
    import json as _json
    from clawmetry import config as _cfg

    if enable:
        removed = _cfg.enable_cloud()
        env = os.environ.get("CLAWMETRY_NO_CLOUD", "").strip().lower()
        if env in ("1", "true", "yes", "on"):
            print("⚠️  CLAWMETRY_NO_CLOUD=" + env + " is set in the environment.")
            print("   The marker was removed, but that env var still forces")
            print("   local-only mode — unset it (and restart the daemon's")
            print("   service) to actually resume cloud sync.")
            return 1
        api_key = ""
        try:
            with open(os.path.expanduser("~/.clawmetry/config.json"), "r",
                      encoding="utf-8") as f:
                api_key = (_json.load(f) or {}).get("api_key") or ""
        except Exception:
            pass
        if not api_key:
            print("✅  Cloud sync enabled — but no account is linked yet.")
            print("    Run `clawmetry login` to sign in / sign up, then the")
            print("    daemon starts syncing automatically.")
            return 0
        print("✅  Cloud sync is ON."
              + ("  (removed local-only marker)" if removed else "  (was already on)"))
        print("    The running daemon picks this up within seconds.")
        print("    Daemon not running? Start it with: clawmetry sync")
        print("    Dashboard: https://app.clawmetry.com/cloud")
        return 0
    # OFF: write the persistent marker (survives updates and restarts).
    marker = _cfg.NOCLOUD_MARKER_PATH
    try:
        os.makedirs(os.path.dirname(marker), exist_ok=True)
        with open(marker, "w", encoding="utf-8") as f:
            f.write("cloud sync disabled via clawmetry --turn-off-cloud-sync\n")
    except Exception as e:
        print("❌  Could not write the local-only marker: %s" % e)
        return 1
    print("✅  Cloud sync is OFF (local-only mode).")
    print("    • No data leaves this machine — heartbeats and snapshot")
    print("      uploads stop within seconds (no restart needed).")
    print("    • The local dashboard at http://localhost:8900 keeps working.")
    print("    • Your account login is kept; turn back on any time with:")
    print("        clawmetry --turn-on-cloud-sync")

    # Kick the daemon so an in-flight snapshot upload can't outrace the
    # marker check that gates the NEXT POST.
    _kick_daemon_for_toggle()

    # Flush every trace of this account's data from the cloud. Best-effort:
    # local-only is already in effect regardless of what the network does.
    api_key = ""
    try:
        with open(os.path.expanduser("~/.clawmetry/config.json"), "r",
                  encoding="utf-8") as f:
            api_key = (_json.load(f) or {}).get("api_key") or ""
    except Exception:
        pass
    if os.environ.get("CLAWMETRY_TOGGLE_SKIP_PURGE") == "1":
        print("    (skipping cloud purge: CLAWMETRY_TOGGLE_SKIP_PURGE=1)")
    elif api_key:
        print()
        print("  Deleting cloud copy of your data…")
        ok, msg = _purge_cloud_data(api_key)
        if ok:
            print(f"    ✅  Cloud data purged: {msg}")
            print("       Your account (login, plan) is kept.")
        else:
            print(f"    ⚠️  Cloud purge did not complete: {msg}")
            print("       Local-only is still in effect (nothing new is being")
            print("       uploaded). Retry the purge with:")
            print("         clawmetry --turn-off-cloud-sync")
    return 0


def _cmd_compliance(args) -> None:
    """``clawmetry compliance bundle --framework <id> --from --to --out``.

    Fetches an auditor-ready evidence bundle (zip) from the running local
    dashboard's Compliance Pack endpoint. The engine lives in clawmetry-pro;
    vanilla OSS answers HTTP 402 and we explain the upgrade path.
    """
    import urllib.error
    import urllib.parse
    import urllib.request

    verb = getattr(args, "compliance_cmd", None)
    if verb != "bundle":
        print("Usage: clawmetry compliance bundle "
              "[--framework nist-ai-rmf|soc2-cc] [--from DATE] [--to DATE] "
              "[--out FILE] [--port PORT]")
        sys.exit(2)
    port = getattr(args, "port", None) or 8900
    query = {"framework": getattr(args, "framework", None) or "nist-ai-rmf"}
    if getattr(args, "date_from", None):
        query["from"] = args.date_from
    if getattr(args, "date_to", None):
        query["to"] = args.date_to
    url = (f"http://127.0.0.1:{port}/api/compliance/bundle?"
           + urllib.parse.urlencode(query))
    req = urllib.request.Request(url, method="POST")
    try:
        resp = urllib.request.urlopen(req, timeout=120)
    except urllib.error.HTTPError as e:
        if e.code == 402:
            print("❌  The Compliance Pack is a paid feature (Pro and up).")
            print("    Install clawmetry-pro with a license key, or see "
                  "clawmetry.com/pricing.")
        elif e.code == 404:
            print(f"❌  Unknown framework {query['framework']!r} (or the "
                  "dashboard predates the Compliance Pack — update it).")
        else:
            print(f"❌  Bundle request failed: HTTP {e.code}")
        sys.exit(1)
    except (urllib.error.URLError, OSError):
        print(f"❌  No dashboard at http://127.0.0.1:{port} — start it with "
              "`clawmetry` first (or pass --port).")
        sys.exit(1)
    blob = resp.read()
    out = getattr(args, "out", None)
    if not out:
        frm = (query.get("from") or "start")[:10]
        to = (query.get("to") or "now")[:10]
        out = f"clawmetry-compliance_{query['framework']}_{frm}_{to}.zip"
    with open(out, "wb") as fh:
        fh.write(blob)
    sha = resp.headers.get("X-Clawmetry-Bundle-Sha256", "")
    n_controls = resp.headers.get("X-Clawmetry-Bundle-Controls", "?")
    print(f"✅  Wrote {out} ({len(blob):,} bytes, {n_controls} controls)")
    if sha:
        print(f"    sha256: {sha}")
    print("    Contents: manifest, integrity proof, controls.json, "
          "approvals.csv, violations.csv, audit_log.csv, attestation.md")


def _cmd_export(args) -> None:
    """``clawmetry export --from <date> --to <date> --format jsonl|csv``.

    Audit/compliance dump of the immutable event log for a time range,
    fetched from the configured endpoint (managed cloud or a self-hosted
    Enterprise server — resolution: CLAWMETRY_ENDPOINT env > config
    ``endpoint`` > cloud default) with the configured credentials.

    The server side is ``GET /api/export/events?from=&to=`` returning JSONL
    (one event per line). CSV conversion happens client-side so the server
    contract stays minimal. Exit codes: 0 ok, 1 error.
    """
    import csv as _csv
    import json
    import urllib.error
    import urllib.parse
    import urllib.request

    from clawmetry.endpoints import ingest_url as _resolve_ingest_url

    api_key = os.environ.get("CLAWMETRY_API_KEY", "").strip()
    if not api_key:
        try:
            from clawmetry.sync import CONFIG_FILE as _CFG
            api_key = json.loads(_CFG.read_text()).get("api_key", "")
        except Exception:
            api_key = ""
    if not api_key:
        print("❌  No API key. Set CLAWMETRY_API_KEY or run `clawmetry connect` first.")
        sys.exit(1)

    base = _resolve_ingest_url()
    query = []
    if getattr(args, "date_from", None):
        query.append("from=" + urllib.parse.quote(args.date_from))
    if getattr(args, "date_to", None):
        query.append("to=" + urllib.parse.quote(args.date_to))
    url = base + "/api/export/events"
    if query:
        url += "?" + "&".join(query)

    fmt = getattr(args, "format", "jsonl") or "jsonl"
    out_path = getattr(args, "out", None)

    req = urllib.request.Request(
        url, headers={"X-Api-Key": api_key, "Accept": "application/x-ndjson"}
    )
    try:
        resp = urllib.request.urlopen(req, timeout=120)
    except urllib.error.HTTPError as e:
        if e.code == 404:
            print(f"❌  {base} does not implement /api/export/events.")
            print("    Self-hosted servers support it from clawmetry 0.12.602;")
            print("    for ClawMetry Cloud, contact support to enable audit export.")
        elif e.code == 401:
            print("❌  Unauthorized — check your API key against the configured endpoint.")
        else:
            print(f"❌  Export failed: HTTP {e.code} {e.reason}")
        sys.exit(1)
    except Exception as e:
        print(f"❌  Could not reach {base}: {e}")
        sys.exit(1)

    sink = open(out_path, "w", encoding="utf-8", newline="") if out_path else sys.stdout
    count = 0
    try:
        if fmt == "csv":
            cols = (
                "id", "node_id", "agent_type", "agent_id", "session_id",
                "event_type", "ts", "model", "token_count", "cost_usd",
                "data", "received_at",
            )
            writer = _csv.writer(sink)
            writer.writerow(cols)
            for raw in resp:
                line = raw.decode("utf-8", errors="replace").strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                except Exception:
                    continue
                data = rec.get("data")
                if isinstance(data, (dict, list)):
                    data = json.dumps(data, separators=(",", ":"), default=str)
                writer.writerow(
                    [rec.get(c) if c != "data" else data for c in cols]
                )
                count += 1
        else:
            for raw in resp:
                line = raw.decode("utf-8", errors="replace").rstrip("\n")
                if line.strip():
                    sink.write(line + "\n")
                    count += 1
    finally:
        resp.close()
        if out_path:
            sink.close()

    dest = out_path or "stdout"
    print(f"✅  Exported {count} events to {dest}", file=sys.stderr)


def main() -> None:
    import argparse
    # FAST PATH — `clawmetry hooks …` must dispatch before the dashboard
    # import below (~300ms): `hooks run pretooluse` executes on EVERY Claude
    # Code tool call, and a policy-miss must cost ~40ms, not a third of a
    # second. Handled entirely in hooks_claude_code (stdlib-only imports).
    if len(sys.argv) > 1 and sys.argv[1] == "hooks":
        from clawmetry.hooks_claude_code import cli_main as _hooks_cli
        raise SystemExit(_hooks_cli(sys.argv[2:]))
    # FAST PATH — `clawmetry hook claude-code --base <url>`: the LOCAL-first
    # PreToolUse gate client (auto-installed by the policy watcher — see
    # clawmetry/claude_code_gate.py). Runs on every gated Claude Code tool
    # call; POSTs the stdin event to the local dashboard's
    # /api/hooks/claude-code/pretooluse receiver and prints the decision
    # JSON. ALWAYS exits 0 — any failure means "no opinion" (fail-open),
    # never a blocked agent. Stdlib-only imports.
    if len(sys.argv) > 1 and sys.argv[1] == "hook":
        from clawmetry.claude_code_gate import hook_main as _hook_cli
        raise SystemExit(_hook_cli(sys.argv[2:]))
    # FAST PATH — agent-facing read CLI (`clawmetry sessions|activity|waste|
    # progress|usage|selfevolve`, see docs/CLI.md + clawmetry/cli_cmds/).
    # Dispatches BEFORE the dashboard import (~300ms) and before this process
    # tags itself CLAWMETRY_ROLE=dashboard, so local_store.get_store()
    # resolves the transport ladder itself: daemon HTTP proxy when the sync
    # daemon owns the writer, direct read-only DuckDB in single-process
    # installs. These commands are read-only and never take the writer lock.
    try:
        from clawmetry.cli_cmds import AGENT_COMMANDS as _agent_cmds
    except Exception:
        _agent_cmds = ()
    if len(sys.argv) > 1 and sys.argv[1] in _agent_cmds:
        from clawmetry.cli_cmds import dispatch as _agent_dispatch
        raise SystemExit(_agent_dispatch(sys.argv[1:]))
    # Enterprise TLS/proxy bootstrap — OS trust store (truststore), 3.13
    # strict-flag relax, CLAWMETRY_CA_BUNDLE, proxy env vars — so every
    # outbound HTTPS call from the CLI/dashboard (connect, OTP, telemetry,
    # update check) works behind corporate TLS-intercepting proxies.
    try:
        from clawmetry.net import configure_outbound_network
        configure_outbound_network(role="cli")
    except Exception:
        pass
    # Stale-duplicate guard: the auto-updater keeps the DAEMON's environment
    # (~/.clawmetry venv) current, not every stray pip copy on the machine.
    # When this process is such a stray copy and it's older than the daemon
    # install, every version this CLI prints is misleading — warn once, on
    # stderr, with the exact upgrade command. Cheap (directory glob, no
    # subprocess, no network); skipped for JSON output so wrapper scripts
    # stay parseable on stdout AND quiet on stderr. CLAWMETRY_NO_STALE_WARN=1
    # silences it. The hooks / agent-read fast paths above return before this
    # line on purpose — they are latency-critical.
    try:
        if "--json" not in sys.argv:
            from clawmetry.installs import maybe_warn_stale_cli
            maybe_warn_stale_cli()
    except Exception:
        pass
    # Cloud-sync toggles — plain flags so a non-engineer can flip sync from
    # any docs snippet without learning subcommands. Handled before all
    # parsing (position-independent), exit immediately.
    if "--turn-on-cloud-sync" in sys.argv:
        raise SystemExit(_cmd_cloud_toggle(True))
    if "--turn-off-cloud-sync" in sys.argv:
        raise SystemExit(_cmd_cloud_toggle(False))
    # --v2 opt-in flag for the React SPA scaffold (see clawmetry/v2/routes.py).
    # Strip it from argv so dashboard.main's argparse doesn't choke on it.
    # Sets the env var that dashboard.py checks at blueprint registration time.
    if "--v2-default" in sys.argv:
        sys.argv = [a for a in sys.argv if a != "--v2-default"]
        os.environ["CLAWMETRY_V2"] = "1"
        os.environ["CLAWMETRY_V2_DEFAULT"] = "1"
        print(
            "v2 at / (default) · v1 at /v1",
            flush=True,
        )
    elif "--v2" in sys.argv:
        sys.argv = [a for a in sys.argv if a != "--v2"]
        os.environ["CLAWMETRY_V2"] = "1"
        print(
            "v2 preview at http://localhost:8900/v2 · back to v1 at /",
            flush=True,
        )
    # --otel-export <url>: stream agent traces as OpenTelemetry GenAI spans to
    # any OTLP/HTTP collector (Datadog, Grafana, Honeycomb, your own).
    # Sets the env var clawmetry/otel_exporter.py reads at boot. Strip from argv
    # so dashboard.main's argparse doesn't choke on it. Accepts both
    # `--otel-export URL` and `--otel-export=URL`.
    _otel_ep = None
    for _i, _a in enumerate(list(sys.argv)):
        if _a == "--otel-export" and _i + 1 < len(sys.argv):
            _otel_ep = sys.argv[_i + 1]
            del sys.argv[_i:_i + 2]
            break
        if _a.startswith("--otel-export="):
            _otel_ep = _a.split("=", 1)[1]
            sys.argv.remove(_a)
            break
    if _otel_ep:
        os.environ["CLAWMETRY_OTEL_EXPORT_ENDPOINT"] = _otel_ep
        print(f"OpenTelemetry export ON → {_otel_ep} (GenAI semconv)", flush=True)
    # Short-circuit --version before loading dashboard + DuckDB.
    # dashboard.py calls get_store() at module level when CLAWMETRY_ROLE=dashboard is
    # set; on some Linux runners duckdb init SIGSEGVs in that path. --version never
    # needs the store so we read __version__ directly and return immediately.
    if "--version" in sys.argv:
        try:
            import importlib.util as _ilu
            _spec = _ilu.find_spec("dashboard")
            if _spec and _spec.origin:
                import re as _re
                _src = open(_spec.origin, encoding="utf-8", errors="replace").read(50000)
                _m = _re.search(r'__version__\s*=\s*"(.+?)"', _src)
                _v = _m.group(1) if _m else "unknown"
            else:
                _v = "unknown"
        except Exception:
            _v = "unknown"
        print(f"clawmetry {_v}")
        return
    # Tag this process as the dashboard BEFORE importing dashboard, so every
    # get_store() in dashboard.py (module-level + handlers) is barred from the
    # DuckDB writer — only the sync daemon writes. Set before the import or a
    # module-level open would race in before the gate is active. The daemon
    # (-m clawmetry.sync) never takes this path and calls mark_writer_owner(),
    # which overrides the gate.
    os.environ["CLAWMETRY_ROLE"] = "dashboard"
    from dashboard import main as dashboard_main

    # Anonymous, opt-out install-lifecycle ping (install once ever, update
    # once per new version). See clawmetry/telemetry.py for the privacy
    # contract. Fires on a daemon thread so a network failure can't slow
    # CLI startup; honours CLAWMETRY_NO_TELEMETRY=1 and
    # ~/.clawmetry/notelemetry.
    try:
        from clawmetry import telemetry as _telemetry
        try:
            from dashboard import __version__ as _ver
        except Exception:
            _ver = "unknown"
        _telemetry.maybe_ping(_ver)
    except Exception:
        # Never let telemetry plumbing break startup.
        pass

    # Windows: protect against closed/detached stdout/stderr before any library
    # (argparse colour detection, click._winconsole) calls fileno() on them.
    #
    # Scenarios that close standard handles:
    #   - pythonw.exe: GUI launcher; no console attached at all
    #   - Start-Process / Task Scheduler: CreateProcess with no console
    #   - Any launcher that closes handles before exec
    #
    # click._winconsole._is_console() calls f.fileno() → ValueError when closed.
    # NO_COLOR suppresses argparse / click colour paths (Python 3.14+).
    # We *also* replace closed handles with devnull sinks so later code is safe.
    if sys.platform == "win32":
        import io as _io

        os.environ.setdefault("NO_COLOR", "1")
        for _attr in ("stdout", "stderr"):
            _stream = getattr(sys, _attr, None)
            if _stream is None:
                try:
                    setattr(sys, _attr, open(os.devnull, "w", encoding="utf-8"))
                except OSError:
                    setattr(sys, _attr, _io.StringIO())
                continue
            try:
                _stream.fileno()
            except (AttributeError, ValueError, OSError):
                # A dead stream on a process that HAD a console is a bug
                # signal, not a pythonw scenario: something closed the stream
                # after startup (the #3791 class). The swap below keeps the
                # CLI from crashing, but it also makes every print() vanish,
                # so leave a breadcrumb a human can find.
                if getattr(sys, "__%s__" % _attr, None) is not None:
                    try:
                        _bc = os.path.expanduser("~/.clawmetry/cli-stream-guard.log")
                        os.makedirs(os.path.dirname(_bc), exist_ok=True)
                        with open(_bc, "a", encoding="utf-8") as _fh:
                            _fh.write(
                                "sys.%s was closed at CLI startup; output is being "
                                "discarded. This should never happen on a normal "
                                "console run: see clawmetry#3791.\n" % _attr
                            )
                    except OSError:
                        pass
                try:
                    setattr(sys, _attr, open(os.devnull, "w", encoding="utf-8"))
                except OSError:
                    setattr(sys, _attr, _io.StringIO())

    parser = argparse.ArgumentParser(prog="clawmetry", add_help=False)
    parser.add_argument(
        "--openclaw-dir",
        type=str,
        help="OpenClaw config directory (default: ~/.openclaw). Env: CLAWMETRY_OPENCLAW_DIR",
    )
    sub = parser.add_subparsers(dest="cmd")

    # onboard — first-time setup wizard (called by install.sh)
    p_onboard = sub.add_parser(
        "onboard", help="First-time setup wizard (run after install)"
    )
    p_onboard.add_argument("--key", metavar="cm_xxx", help="API key (skip prompt)")
    p_onboard.add_argument(
        "--foreground", action="store_true", help="Run daemon in foreground"
    )
    p_onboard.add_argument(
        "--node-id",
        metavar="NAME",
        dest="custom_node_id",
        help="Custom node name (default: hostname)",
    )
    p_onboard.add_argument(
        "--local", "--no-cloud", action="store_true", dest="local",
        help="Local only: no cloud account, nothing leaves this machine",
    )
    p_onboard.add_argument(
        "--cloud", action="store_true", dest="cloud",
        help="Create a cloud account non-interactively (skip the prompt)",
    )

    # connect
    p_login = sub.add_parser(
        "login",
        help="Log in / sign up for ClawMetry Cloud (email or Google/GitHub)",
    )
    p_login.add_argument(
        "--force", action="store_true",
        help="Offer cloud signup even in local-only mode",
    )

    p_connect = sub.add_parser("connect", help="Activate cloud sync")
    p_connect.add_argument("--key", metavar="cm_xxx", help="API key (skip prompt)")
    p_connect.add_argument(
        "--enc-key",
        metavar="KEY",
        dest="enc_key",
        help="Encryption key (skip prompt, for automated/sandbox use)",
    )
    p_connect.add_argument(
        "--key-only",
        action="store_true",
        help="Save key + config only, do not start daemon (for NemoClaw host use)",
    )
    p_connect.add_argument(
        "--no-daemon",
        action="store_true",
        help="Connect but do not start daemon (daemon managed externally, e.g. supervisord)",
    )
    p_connect.add_argument(
        "--start-sync-now",
        action="store_true",
        dest="start_sync_now",
        help="Skip the ownership OTP and start syncing immediately "
        "(the command copied from the dashboard uses this; "
        "sync-on-connect is otherwise already the default)",
    )
    p_connect.add_argument(
        "--defer-sync",
        action="store_true",
        dest="defer_sync",
        help="Connect but leave sync paused; start it later with `clawmetry sync`",
    )
    p_connect.add_argument(
        "--foreground", action="store_true", help="Run daemon in foreground"
    )
    p_connect.add_argument(
        "--node-id",
        metavar="NAME",
        dest="custom_node_id",
        help="Custom node name (default: hostname)",
    )
    p_connect.add_argument(
        "--force",
        action="store_true",
        help="Override the persistent local-only marker (#1937) and connect anyway",
    )
    p_connect.add_argument(
        "--keep-local",
        action="store_true",
        dest="keep_local",
        help="Sign in for the account + trial license but keep this install "
        "local-only: the nocloud marker stays, no snapshots ever leave "
        "this machine (the desktop app's Self-Hosted choice uses this)",
    )

    # setup — alias for onboard (new user-facing name)
    p_setup = sub.add_parser(
        "setup", help="Setup wizard — connect to ClawMetry Cloud"
    )
    p_setup.add_argument("--key", metavar="cm_xxx", help="API key (skip prompt)")
    p_setup.add_argument(
        "--foreground", action="store_true", help="Run daemon in foreground"
    )
    p_setup.add_argument(
        "--node-id",
        metavar="NAME",
        dest="custom_node_id",
        help="Custom node name (default: hostname)",
    )
    p_setup.add_argument(
        "--local", "--no-cloud", action="store_true", dest="local",
        help="Local only: no cloud account, nothing leaves this machine",
    )
    p_setup.add_argument(
        "--cloud", action="store_true", dest="cloud",
        help="Create a cloud account non-interactively (skip the prompt)",
    )

    # account — link email or show account info
    sub.add_parser("account", help="Link email to account or show account info")

    # nemoclaw-daemons
    sub.add_parser(
        "nemoclaw-daemons",
        help="Register LaunchAgents to keep NemoClaw sandbox daemons alive (macOS)",
    )

    # disconnect
    sub.add_parser("disconnect", help="Stop cloud sync and remove key")

    # sync — start the deferred sync daemon (for nodes connected with default deferred-sync behavior)
    p_sync = sub.add_parser(
        "sync", help="Start the sync daemon (after `clawmetry connect`)"
    )
    p_sync.add_argument(
        "--foreground", action="store_true", help="Run daemon in foreground"
    )
    p_sync.add_argument(
        "--restart", action="store_true",
        help="Restart the running daemon (bounces launchd/systemd; safe, no SIGKILL)",
    )

    # status
    p_status = sub.add_parser("status", help="Show local + cloud sync status")
    p_status.add_argument("--show-key", action="store_true", help="Reveal secret key")
    p_status.add_argument("--live", action="store_true", help="Live one-line status bar (sessions · tokens · cost · model · tok/s); Ctrl-C to exit")
    p_status.add_argument(
        "--json",
        action="store_true",
        dest="as_json",
        help=(
            "Emit the status snapshot as JSON (jq-friendly) instead of the "
            "human table. Matches the sibling flag on `tier --json` / "
            "`license --json` / `runtimes --json` / `features --json` / "
            "`channels --json` / `diagnose --json` / `verify-integrity --json` "
            "so wrappers can parse cloud-sync / daemon / runtime state without "
            "screen-scraping. Ignored when combined with --live."
        ),
    )

    # proxy
    # secure — numbat (Perplexity agent-EDR) install + hook status
    p_secure = sub.add_parser(
        "secure",
        help="Agent security via numbat: install hooks, show status (docs/NUMBAT.md)",
    )
    secure_sub = p_secure.add_subparsers(dest="secure_cmd")
    p_secure_enable = secure_sub.add_parser(
        "enable", help="Install numbat + monitor-only hooks wired to ClawMetry"
    )
    p_secure_enable.add_argument(
        "--yes", action="store_true",
        help="Skip the confirmation prompt (hook install edits agent configs)",
    )
    p_secure_enable.add_argument(
        "--port", type=int, default=None,
        help="Dashboard port for the HTTP sink (default: 8900)",
    )
    p_secure_enable.add_argument(
        "--emit-all", action="store_true",
        help="Emit full event stream to the file sink, not just findings",
    )
    p_secure_enable.add_argument(
        "--reinstall", action="store_true",
        help="Re-download the numbat binary even if one is already installed",
    )
    secure_sub.add_parser(
        "status", help="Per-agent hook wiring + findings ingested by ClawMetry"
    )
    secure_sub.add_parser(
        "disable", help="Remove numbat hooks from all agent configs"
    )

    p_proxy = sub.add_parser(
        "proxy", help="Local enforcement proxy (budget, loops, routing)"
    )
    proxy_sub = p_proxy.add_subparsers(dest="proxy_cmd")

    p_proxy_start = proxy_sub.add_parser("start", help="Start the proxy server")
    p_proxy_start.add_argument("--port", type=int, help="Port (default: 4100)")
    p_proxy_start.add_argument(
        "--host", default=None, help="Bind host (default: 127.0.0.1)"
    )
    p_proxy_start.add_argument(
        "--foreground", action="store_true", help="Run in foreground"
    )
    p_proxy_start.add_argument(
        "--daily-budget", type=float, metavar="USD", help="Daily budget limit in USD"
    )
    p_proxy_start.add_argument(
        "--monthly-budget",
        type=float,
        metavar="USD",
        help="Monthly budget limit in USD",
    )
    p_proxy_start.add_argument(
        "--no-loop-detection", action="store_true", help="Disable loop detection"
    )
    p_proxy_start.add_argument(
        "--log-requests", action="store_true", help="Log all proxied requests"
    )

    proxy_sub.add_parser("stop", help="Stop the proxy server")

    p_proxy_status = proxy_sub.add_parser("status", help="Show proxy status")
    p_proxy_status.add_argument(
        "--json", action="store_true", dest="as_json", help="Output as JSON"
    )

    p_proxy_config = proxy_sub.add_parser("config", help="Show or update proxy config")
    p_proxy_config.add_argument(
        "--daily-budget", type=float, metavar="USD", help="Set daily budget"
    )
    p_proxy_config.add_argument(
        "--monthly-budget", type=float, metavar="USD", help="Set monthly budget"
    )
    p_proxy_config.add_argument(
        "--action", choices=["block", "warn", "downgrade"], help="Budget action"
    )
    p_proxy_config.add_argument(
        "--loop-detection", choices=["on", "off"], help="Toggle loop detection"
    )

    # reports — open the reports browser (refs #1005)
    p_reports = sub.add_parser(
        "reports",
        help="Open the reports browser (renders ~/.clawmetry/reports/*.md + DuckDB SQL)",
    )
    p_reports.add_argument(
        "--port", type=int, default=8900, help="Dashboard port (default: 8900)"
    )

    # eval — run a golden test suite (Phase 2 evals, refs #1619)
    p_eval = sub.add_parser(
        "eval",
        help="Run a golden eval suite (YAML in ~/.clawmetry/evals/)",
    )
    p_eval.add_argument(
        "--suite",
        metavar="NAME_OR_PATH",
        help="Suite name (e.g. customer_support) or absolute path to a YAML file",
    )
    p_eval.add_argument(
        "--list",
        action="store_true",
        dest="list_suites",
        help="List available suites and exit",
    )
    p_eval.add_argument(
        "--watch",
        action="store_true",
        help="Re-run on every change to the suite file (dev loop)",
    )
    p_eval.add_argument(
        "--no-persist",
        action="store_true",
        dest="no_persist",
        help="Do not write results to DuckDB (useful for dry runs)",
    )
    p_eval.add_argument(
        "--json",
        action="store_true",
        dest="as_json",
        help="Emit machine-readable JSON instead of the table",
    )
    # Phase 3 (refs #1619) — regression replay of last week's failed sessions.
    # MANUAL invocation only by design (no cron): replay costs API tokens, so
    # the user opts in every time. ``--regression`` is mutually-exclusive with
    # ``--suite`` at the handler level.
    p_eval.add_argument(
        "--regression",
        action="store_true",
        dest="regression",
        help=(
            "Replay last week's failed sessions against the current "
            "config (manual cost-guarded; see --window / --limit)"
        ),
    )
    p_eval.add_argument(
        "--window",
        metavar="DURATION",
        default="7d",
        help="Lookback window for --regression (e.g. 7d, 14d; default 7d)",
    )
    p_eval.add_argument(
        "--limit",
        type=int,
        default=None,
        help=(
            "Hard ceiling on replays per --regression invocation "
            "(default: CLAWMETRY_EVALS_REGRESSION_MAX or 10)"
        ),
    )

    # update — self-update to latest PyPI version
    p_update = sub.add_parser("update", help="Update clawmetry to the latest version")
    p_update.add_argument(
        "--unattended",
        action="store_true",
        help=(
            "Apply the daemon's unattended-update policy instead of blindly "
            "upgrading: honor the CLAWMETRY_AUTO_UPDATE kill switch (including "
            "implicit CI disable) and the CLAWMETRY_AUTOUPDATE_MIN_AGE_HOURS "
            "stability window, installing the newest aged-in release (pinned) "
            "rather than the absolute latest. Used by the desktop shell's 6h "
            "background upgrade."
        ),
    )

    # mcp — start MCP server on stdio (issue #2859)
    sub.add_parser(
        "mcp",
        help="Start ClawMetry MCP server (stdio) — lets agents query their own telemetry",
    )

    # uninstall — fully remove clawmetry
    p_uninstall = sub.add_parser(
        "uninstall", help="Fully uninstall clawmetry (stop daemons, remove all files)"
    )
    p_uninstall.add_argument(
        "-y", "--yes",
        action="store_true",
        help="Skip the interactive 'type uninstall to confirm' prompt "
        "(required for desktop-app menu shell-out and the app-vanished watchdog).",
    )
    p_uninstall.add_argument(
        "--unattended",
        action="store_true",
        help="Non-interactive, minimal output, always exit 0 even on partial "
        "failures. Implies --yes. This is what the macOS app-vanished watchdog uses "
        "when it detects that /Applications/ClawMetry.app has been dragged to trash.",
    )
    p_uninstall.add_argument(
        "--keep-data",
        action="store_true",
        help="Preserve the DuckDB local store and history DB. Removes runtime, "
        "config, and daemons; keeps event data on disk in case you reinstall.",
    )
    p_uninstall.add_argument(
        "--dry-run",
        action="store_true",
        dest="dry_run",
        help="List everything that would be removed without touching disk.",
    )

    # activate — install a self-hosted Pro/Enterprise license key
    p_activate = sub.add_parser(
        "activate", help="Activate a self-hosted Pro/Enterprise license key"
    )
    # ``key`` is nargs="?" now that ``--file <path>`` is accepted; the CLI
    # handler refuses the "neither supplied" branch itself so the same
    # ``ok=false`` envelope surfaces in both --json and human paths.
    p_activate.add_argument(
        "key",
        nargs="?",
        default=None,
        help="License key (CLAW1.…) — omit when using --file",
    )
    p_activate.add_argument(
        "--file",
        dest="file",
        default=None,
        metavar="PATH",
        help=(
            "Read the license key from PATH instead of the command line "
            "(keeps the raw token out of shell history and `ps` listings). "
            "Mutually exclusive with the positional <KEY>."
        ),
    )
    p_activate.add_argument(
        "--json",
        action="store_true",
        dest="as_json",
        help=(
            "Emit {action, ok, message} JSON (jq-friendly). Byte-identical "
            "to the envelope `clawmetry license activate <KEY> --json` "
            "already emits so wrappers do not need to branch on the "
            "shortcut spelling."
        ),
    )

    # license — manage the self-hosted Pro/Enterprise license
    p_license = sub.add_parser("license", help="Manage the self-hosted Pro/Enterprise license")
    p_license.add_argument(
        "license_action",
        nargs="?",
        default="status",
        choices=["status", "activate", "deactivate", "fingerprint", "verify"],
        help="status (default) | activate <KEY> | deactivate | fingerprint | verify <KEY>",
    )
    p_license.add_argument(
        "license_key",
        nargs="?",
        default=None,
        help="License key (CLAW1.…) — required for 'activate' / 'verify' unless --file is used",
    )
    p_license.add_argument(
        "--file",
        dest="file",
        default=None,
        metavar="PATH",
        help=(
            "For 'activate' / 'verify': read the license key from PATH "
            "instead of the command line (keeps the raw token out of shell "
            "history and `ps` listings). Mutually exclusive with the "
            "positional <KEY>."
        ),
    )
    p_license.add_argument(
        "--json",
        action="store_true",
        dest="as_json",
        help=(
            "Emit {action, ok, ...} JSON (jq-friendly). Matches the sibling "
            "flag on `tier --json` / `runtimes --json` / `features --json` / "
            "`channels --json` so wrappers can parse license state without "
            "screen-scraping the human-readable block."
        ),
    )

    # tier — print the resolved open-core entitlement (scriptable)
    p_tier = sub.add_parser(
        "tier",
        help="Print the resolved open-core entitlement (tier, runtimes, features)",
    )
    p_tier.add_argument(
        "--json",
        action="store_true",
        dest="as_json",
        help="Emit the full Entitlement.to_dict() as JSON (jq-friendly)",
    )

    # runtimes — list every observable runtime and which are unlocked (PR #3005)
    p_runtimes = sub.add_parser(
        "runtimes",
        help="List every observable runtime and which this install can unlock",
    )
    p_runtimes.add_argument(
        "--json",
        action="store_true",
        dest="as_json",
        help="Emit {tier, grace, enforced, runtimes:[...]} JSON (jq-friendly)",
    )
    p_runtimes.add_argument(
        "--why",
        metavar="ID",
        default=None,
        help=(
            "Print the lock-reason payload for a single runtime id "
            "(same shape as GET /api/entitlement/lock-reason?runtime=<id>)"
        ),
    )

    # features — list every observable feature and which are unlocked.
    # CLI sibling of `clawmetry runtimes` and of the dashboard's GET
    # /api/features so the operator can answer "what does this tier unlock?"
    # from the shell without parsing `tier --json`.
    p_features = sub.add_parser(
        "features",
        help="List every observable feature and which this install can unlock",
    )
    p_features.add_argument(
        "--json",
        action="store_true",
        dest="as_json",
        help="Emit {tier, grace, enforced, features:[...]} JSON (jq-friendly)",
    )
    p_features.add_argument(
        "--why",
        metavar="ID",
        default=None,
        help=(
            "Print the lock-reason payload for a single feature id "
            "(same shape as GET /api/entitlement/lock-reason?feature=<id>)"
        ),
    )

    # channels — list every chat-channel adapter and the tier-scoped cap.
    # CLI sibling of `clawmetry runtimes` / `clawmetry features` for the
    # third entitlement axis. Every adapter is FREE at every tier; the
    # concurrent-channel cap is what the header block advertises.
    p_channels = sub.add_parser(
        "channels",
        help="List every chat-channel adapter and the concurrent-channel cap",
    )
    p_channels.add_argument(
        "--json",
        action="store_true",
        dest="as_json",
        help=(
            "Emit {tier, grace, enforced, channel_limit, channels:[...]} "
            "JSON (jq-friendly)"
        ),
    )
    p_channels.add_argument(
        "--why",
        metavar="N",
        default=None,
        help=(
            "Print the lock-reason payload for N concurrent channels "
            "(same shape as GET /api/entitlement/lock-reason?channels=N). "
            "The channels axis is capacity-scoped -- every adapter itself "
            "is free -- so N is a count, not an adapter id."
        ),
    )

    # nodes — capacity-axis sibling of `clawmetry channels` for the
    # registered-node count. No enumerable adapter list -- ``nodes`` is
    # purely a per-tier cap -- so the default output is the header block
    # (tier / enforcement / node cap) alone. Fills the last capacity-axis
    # CLI gap left open after `channels` shipped in #3820.
    p_nodes = sub.add_parser(
        "nodes",
        help="Show the resolved node-count cap for this install",
    )
    p_nodes.add_argument(
        "--json",
        action="store_true",
        dest="as_json",
        help="Emit {tier, grace, enforced, node_limit} JSON (jq-friendly)",
    )
    p_nodes.add_argument(
        "--why",
        metavar="N",
        default=None,
        help=(
            "Print the lock-reason payload for N registered nodes "
            "(same shape as GET /api/entitlement/lock-reason?nodes=N). "
            "The nodes axis is capacity-scoped -- N is a count, not an id."
        ),
    )

    # retention — event-retention window cap (capacity axis sibling of
    # `clawmetry channels` / `clawmetry nodes`). Same header/JSON/--why
    # triad as the other capacity subcommands so the four-axis CLI surface
    # is uniform.
    p_retention = sub.add_parser(
        "retention",
        help="Show the event-retention window cap and the tier that would extend it",
    )
    p_retention.add_argument(
        "--json",
        action="store_true",
        dest="as_json",
        help=(
            "Emit {tier, grace, enforced, retention_days, "
            "effective_retention_days, override_env_name, "
            "override_env_value} JSON (jq-friendly)"
        ),
    )
    p_retention.add_argument(
        "--why",
        metavar="N",
        default=None,
        help=(
            "Print the lock-reason payload for an N-day retention window "
            "(same shape as GET /api/entitlement/lock-reason?retention_days=N). "
            "The retention axis is capacity-scoped, so N is a day count, "
            "not an event-store id."
        ),
    )

    # bundle — cheapest tier admitting a mixed 5-axis constraint bundle.
    # Aggregate CLI sibling of `clawmetry {runtimes,features,channels,
    # nodes,retention}` (each folds ONE axis); this folds a mixed bundle
    # across ALL five axes into ONE required_tier + affordable-tiers
    # ladder. Wraps `min_tier_for_all` / `affordable_tiers` so CLI, HTTP
    # (`/api/entitlement/required-tier` + `/affordable-tiers`), and the
    # dashboard pricing tooltip cannot drift on the fold answer.
    p_bundle = sub.add_parser(
        "bundle",
        help=(
            "Cheapest tier admitting a mixed features/runtimes/channels/"
            "retention/nodes bundle"
        ),
    )
    p_bundle.add_argument(
        "--features", metavar="CSV", default=None,
        help="Comma-separated feature ids (e.g. anomaly_detection,cost_optimizer)",
    )
    p_bundle.add_argument(
        "--runtimes", metavar="CSV", default=None,
        help="Comma-separated runtime ids (e.g. claude_code,cursor)",
    )
    p_bundle.add_argument(
        "--channels", metavar="N", default=None,
        help="Concurrent-channel count (capacity axis)",
    )
    p_bundle.add_argument(
        "--retention-days", dest="retention_days", metavar="N", default=None,
        help="Desired retention window in days (capacity axis)",
    )
    p_bundle.add_argument(
        "--nodes", metavar="N", default=None,
        help="Registered-node count (capacity axis)",
    )
    p_bundle.add_argument(
        "--tier", dest="perspective", metavar="TIER", default=None,
        help=(
            "Resolve from a hypothetical perspective tier (delegates to "
            "min_tier_for_all_at / affordable_tiers_at; the perspective is "
            "echoed on the payload but does not shape the answer)"
        ),
    )
    p_bundle.add_argument(
        "--json", action="store_true", dest="as_json",
        help=(
            "Emit {tier, grace, enforced, perspective, constraints, "
            "required_tier, affordable_tiers:[...], error?: str} JSON "
            "(jq-friendly). Mirrors /api/entitlement/required-tier + "
            "/affordable-tiers on the shared keys."
        ),
    )

    # extensions — surface loaded / failed entry-point plugins and event hooks
    # from the shell so an operator can answer "did clawmetry-pro actually
    # load on this node?" without curl'ing /api/extensions or tailing daemon
    # logs. In-process introspection of clawmetry.extensions state -- same
    # source /api/extensions consumes -- so the CLI and HTTP surfaces cannot
    # drift on loaded/failed/event/handler counts.
    p_extensions = sub.add_parser(
        "extensions",
        help="Show loaded / failed entry-point plugins and event-hook counts",
    )
    p_extensions.add_argument(
        "--json",
        action="store_true",
        dest="as_json",
        help=(
            "Emit {plugins, plugin_count, failed_plugins, failed_plugin_count, "
            "events, handler_counts} JSON (jq-friendly). Matches the response "
            "shape of GET /api/extensions byte-for-byte on shared keys."
        ),
    )


    # diagnose — surface the entitlement resolver inputs so an operator
    # can answer "why did my install resolve to <tier>?" without reading
    # ~/.clawmetry by hand. Same shape as GET /api/entitlement/diagnostic.
    p_diagnose = sub.add_parser(
        "diagnose",
        help=(
            "Show entitlement resolver inputs (license file, cloud plan "
            "cache, enforce env, in-process cache state)"
        ),
    )
    p_diagnose.add_argument(
        "--json",
        action="store_true",
        dest="as_json",
        help=(
            "Emit resolution_diagnostic() as JSON (same shape as "
            "GET /api/entitlement/diagnostic)"
        ),
    )

    # doctor — enterprise network/TLS connectivity diagnostics
    p_doctor = sub.add_parser(
        "doctor",
        help=(
            "Diagnose cloud connectivity: DNS, TCP, proxy, TLS "
            "(detects corporate TLS interception), heartbeat POST"
        ),
    )
    p_doctor.add_argument(
        "--host",
        dest="doctor_host",
        default=None,
        help="Override target (default: ingest.clawmetry.com / CLAWMETRY_INGEST_URL)",
    )

    # verify-integrity — walk hash chain and report validity (Issue #2200)
    p_verify = sub.add_parser(
        "verify-integrity",
        help="Verify the tamper-evident hash chain for local events",
    )
    p_verify.add_argument(
        "--node-id",
        dest="node_id",
        default=None,
        help="Limit verification to a single node (default: all nodes)",
    )
    p_verify.add_argument(
        "--json",
        action="store_true",
        dest="as_json",
        help=(
            "Emit the verify_integrity result as JSON (mirrors the store's "
            "return shape plus synthetic 'store_open_failed' / 'daemon_too_old'"
            " statuses; exit codes unchanged)"
        ),
    )

    # export — audit/compliance dump of the immutable event log (enterprise)
    p_export = sub.add_parser(
        "export",
        help=(
            "Export the event log for a time range from the configured "
            "endpoint (cloud or self-hosted) for compliance handoff"
        ),
    )
    p_export.add_argument(
        "--from",
        dest="date_from",
        default=None,
        metavar="DATE",
        help="Start of range (ISO date/datetime, e.g. 2026-07-01)",
    )
    p_export.add_argument(
        "--to",
        dest="date_to",
        default=None,
        metavar="DATE",
        help="End of range (ISO date/datetime, inclusive)",
    )
    p_export.add_argument(
        "--format",
        dest="format",
        choices=["jsonl", "csv"],
        default="jsonl",
        help="Output format (default: jsonl)",
    )
    p_export.add_argument(
        "--out",
        dest="out",
        default=None,
        metavar="FILE",
        help="Write to FILE instead of stdout",
    )

    p_compliance = sub.add_parser(
        "compliance",
        help=(
            "Compliance Pack — generate an auditor-ready evidence bundle "
            "from the running dashboard (Pro)"
        ),
    )
    comp_sub = p_compliance.add_subparsers(dest="compliance_cmd")
    p_comp_bundle = comp_sub.add_parser(
        "bundle",
        help="Build and download the evidence bundle zip",
    )
    p_comp_bundle.add_argument(
        "--framework",
        dest="framework",
        default="nist-ai-rmf",
        metavar="ID",
        help="Control map to evaluate (default: nist-ai-rmf; also: soc2-cc)",
    )
    p_comp_bundle.add_argument(
        "--from",
        dest="date_from",
        default=None,
        metavar="DATE",
        help="Start of reporting period (ISO date; default: 30 days ago)",
    )
    p_comp_bundle.add_argument(
        "--to",
        dest="date_to",
        default=None,
        metavar="DATE",
        help="End of reporting period (ISO date; default: now)",
    )
    p_comp_bundle.add_argument(
        "--out",
        dest="out",
        default=None,
        metavar="FILE",
        help="Write the zip to FILE (default: derived name in cwd)",
    )
    p_comp_bundle.add_argument(
        "--port",
        dest="port",
        type=int,
        default=None,
        metavar="PORT",
        help="Local dashboard port (default: 8900)",
    )

    # Parse just the first token to decide if it's a sub-command or dashboard flag
    # `hooks` is absent from this tuple ON PURPOSE: it's intercepted by the
    # fast path at the top of main() before the dashboard import. The parser
    # entry below exists only so `clawmetry --help`-style discovery shows it.
    p_hooks = sub.add_parser(
        "hooks",
        help="Claude Code approval hooks: install | uninstall | status | "
             "run {pretooluse|notification} (pre-execution gate + phone push)")
    p_hooks.add_argument("hooks_cmd", nargs="*")

    # `hook` (singular) is likewise intercepted by its fast path in main();
    # this parser entry exists only for --help discovery. It is the
    # LOCAL-first PreToolUse gate client the policy watcher auto-installs
    # into Claude Code's settings.json (clawmetry/claude_code_gate.py).
    p_hook = sub.add_parser(
        "hook",
        help="Runtime pre-tool hook client (auto-installed): "
             "hook claude-code --base <dashboard url>")
    p_hook.add_argument("hook_cmd", nargs="*")

    _subcmds = (
        "onboard",
        "setup",
        "account",
        "login",
        "connect",
        "disconnect",
        "sync",
        "status",
        "proxy",
        "secure",
        "reports",
        "eval",
        "mcp",
        "update",
        "uninstall",
        "activate",
        "license",
        "tier",
        "runtimes",
        "features",
        "channels",
        "nodes",
        "retention",
        "bundle",
        "extensions",
        "diagnose",
        "doctor",
        "verify-integrity",
        "export",
        "compliance",
        "nemoclaw-daemons",
    )
    if len(sys.argv) > 1 and sys.argv[1] in _subcmds:
        args = parser.parse_args()
        # Issue #322: Set OpenClaw config directory from CLI flag
        if getattr(args, "openclaw_dir", None):
            os.environ["CLAWMETRY_OPENCLAW_DIR"] = os.path.expanduser(args.openclaw_dir)

        if args.cmd in ("onboard", "setup"):
            _cmd_onboard(args)
        elif args.cmd == "account":
            _cmd_account(args)
        elif args.cmd == "login":
            _cmd_login(args)
        elif args.cmd == "connect":
            _cmd_connect(args)
        elif args.cmd == "disconnect":
            _cmd_disconnect(args)
        elif args.cmd == "sync":
            _cmd_sync(args)
        elif args.cmd == "status":
            _cmd_status(args)
        elif args.cmd == "proxy":
            _cmd_proxy(args)
        elif args.cmd == "secure":
            from clawmetry.secure import cmd_secure
            sys.exit(cmd_secure(args))
        elif args.cmd == "reports":
            _cmd_reports(args)
        elif args.cmd == "eval":
            _cmd_eval(args)
        elif args.cmd == "mcp":
            _cmd_mcp(args)
        elif args.cmd == "update":
            _cmd_update(args)
        elif args.cmd == "uninstall":
            _cmd_uninstall(args)
        elif args.cmd == "activate":
            _cmd_activate(args)
        elif args.cmd == "license":
            _cmd_license(args)
        elif args.cmd == "tier":
            _cmd_tier(args)
        elif args.cmd == "runtimes":
            _cmd_runtimes(args)
        elif args.cmd == "features":
            _cmd_features(args)
        elif args.cmd == "channels":
            _cmd_channels(args)
        elif args.cmd == "nodes":
            _cmd_nodes(args)
        elif args.cmd == "retention":
            _cmd_retention(args)
        elif args.cmd == "bundle":
            _cmd_bundle(args)
        elif args.cmd == "extensions":
            _cmd_extensions(args)
        elif args.cmd == "diagnose":
            _cmd_diagnose(args)
        elif args.cmd == "doctor":
            from clawmetry.doctor import run_doctor
            sys.exit(run_doctor(host=getattr(args, "doctor_host", None)))
        elif args.cmd == "verify-integrity":
            _cmd_verify_integrity(args)
        elif args.cmd == "export":
            _cmd_export(args)
        elif args.cmd == "compliance":
            _cmd_compliance(args)
        elif args.cmd == "nemoclaw-daemons":
            _register_nemoclaw_sandbox_daemons()
    else:
        # Fall through to dashboard (handles --host, --port, --version, start, stop, etc.)
        # Tag this process as the dashboard so local_store.get_store() never
        # opens the DuckDB writer here — only the sync daemon writes. The
        # daemon (-m clawmetry.sync) doesn't take this path, and even if it
        # inherited the env it calls mark_writer_owner() which overrides.
        os.environ["CLAWMETRY_ROLE"] = "dashboard"
        dashboard_main()


if __name__ == "__main__":
    main()
