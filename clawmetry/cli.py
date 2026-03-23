"""CLI entry point for the clawmetry package."""
from __future__ import annotations
import sys
import os


def _get_openclaw_dir():
    """Return the OpenClaw config directory, respecting CLAWMETRY_OPENCLAW_DIR env var."""
    import os
    return os.environ.get('CLAWMETRY_OPENCLAW_DIR', os.path.expanduser('~/.openclaw'))



_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _root not in sys.path:
    sys.path.insert(0, _root)



def _stop_existing_daemon() -> None:
    """Stop any running sync daemon, deregister old node, clear stale state."""
    import subprocess, platform, json
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
        plist = __import__("pathlib").Path.home() / "Library" / "LaunchAgents" / f"{label}.plist"
        subprocess.run(["launchctl", "unload", str(plist)], check=False, capture_output=True)
    elif system == "Linux":
        subprocess.run(["systemctl", "--user", "stop", "clawmetry-sync"], check=False, capture_output=True)
    
    # Send offline heartbeat for old node to deregister it from cloud
    if old_node_id and old_api_key:
        try:
            from clawmetry.sync import _post
            from datetime import datetime, timezone
            _post("/ingest/heartbeat", {
                "node_id": old_node_id,
                "ts": datetime.now(timezone.utc).isoformat(),
                "status": "offline",
                "platform": platform.system(),
            }, old_api_key, timeout=5)
        except Exception:
            pass  # Best effort
    
    # Clear stale state so the new daemon does a fresh initial sync
    if STATE_FILE.exists():
        STATE_FILE.unlink()
    # Clear old log so it's clean
    if LOG_FILE.exists():
        LOG_FILE.write_text("")

def _get_api_key_interactive() -> str:
    """Interactive API key acquisition: email OTP or direct paste."""
    import getpass, urllib.request, urllib.error, json as _json

    # When stdin is piped (e.g. curl | bash install), open /dev/tty so prompts work
    _tty = None
    if not sys.stdin.isatty():
        try:
            _tty = open('/dev/tty', 'r')
        except OSError:
            pass

    def _input(prompt):
        """input() that reads from /dev/tty when stdin is a pipe."""
        if _tty is not None:
            sys.stdout.write(prompt)
            sys.stdout.flush()
            line = _tty.readline()
            return line.rstrip('\n')
        return input(prompt)

    INGEST_URL = os.environ.get("CLAWMETRY_INGEST_URL", "https://ingest.clawmetry.com")

    def _api_call(path, body):
        url = INGEST_URL.rstrip("/") + path
        data = _json.dumps(body).encode()
        req = urllib.request.Request(url, data=data,
                                     headers={"Content-Type": "application/json"},
                                     method="POST")
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                return _json.loads(resp.read())
        except urllib.error.HTTPError as e:
            return {"error": e.read().decode()[:200]}
        except Exception as e:
            return {"error": str(e)}

    print()
    entry = _input("  📧 Enter your email: ").strip()

    # If it's already an API key, return it directly
    if entry.startswith("cm_"):
        return entry

    # Email flow: send OTP
    import re as _re
    if not _re.match(r'^[^@]+@[^@]+\.[^@]+$', entry):
        print("  ❌  That doesn't look like a valid email.")
        return getpass.getpass("  API key (cm_…): ").strip()

    email = entry.lower()
    print(f"\n  📨 Sending code to {email}…", end="", flush=True)
    r = _api_call("/api/auth/email-otp", {"action": "send", "email": email})
    if r.get("error"):
        print(f" ❌  {r['error']}")
        print("  Visit https://clawmetry.com/connect to get your API key.")
        return getpass.getpass("  API key (cm_…): ").strip()
    print(" ✅")
    print()

    # Ask for OTP
    for attempt in range(3):
        otp = _input("  🔑 Enter the 6-digit code: ").strip()
        if not otp:
            continue
        print("  Verifying…", end="", flush=True)
        r2 = _api_call("/api/auth/email-otp", {"action": "verify", "email": email, "otp": otp})
        if r2.get("error"):
            print(f" ❌  {r2['error']}")
            if attempt < 2:
                print("  Try again.")
            continue
        api_key = r2.get("api_key", "")
        if api_key.startswith("cm_"):
            is_new = r2.get("is_new", False)
            print(f" ✅  {'Account created' if is_new else 'Welcome back'}!")
            print()
            return api_key
        print(" ❌  Server returned an unexpected response.")
        break

    print()
    print("  Couldn't verify. Visit https://clawmetry.com/connect to get your key.")
    return getpass.getpass("  API key (cm_…): ").strip()


def _verify_key_ownership(api_key: str) -> None:
    """Require email OTP to prove key ownership (prevents misuse on shared machines)."""
    import urllib.request, urllib.error, json as _json

    _tty = None
    if not sys.stdin.isatty():
        try:
            _tty = open('/dev/tty', 'r')
        except OSError:
            print("\n  ❌  OTP verification requires an interactive terminal.")
            print("  Run 'clawmetry connect --key cm_xxx' from an interactive shell,")
            print("  or use 'clawmetry onboard' for the full setup wizard.\n")
            sys.exit(1)

    def _input(prompt):
        if _tty is not None:
            sys.stdout.write(prompt)
            sys.stdout.flush()
            return _tty.readline().rstrip('\n')
        return input(prompt)

    INGEST_URL = os.environ.get("CLAWMETRY_INGEST_URL", "https://ingest.clawmetry.com")

    def _api(path, body):
        url = INGEST_URL.rstrip("/") + path
        data = _json.dumps(body).encode()
        req = urllib.request.Request(url, data=data,
                                     headers={"Content-Type": "application/json"},
                                     method="POST")
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                return _json.loads(resp.read())
        except urllib.error.HTTPError as e:
            return {"error": e.read().decode()[:200]}
        except Exception as e:
            return {"error": str(e)}

    print()
    print("  🔐 Verify account ownership")
    print("  📨 Sending verification code…", end="", flush=True)
    r = _api("/api/auth/email-otp", {"action": "send_by_key", "api_key": api_key})
    if r.get("error"):
        print(f" ❌  {r['error']}")
        sys.exit(1)
    _masked = r.get("masked_email", "your email")
    print(f" ✅")
    print(f"  📧 Code sent to {_masked}")
    print()

    for attempt in range(3):
        otp = _input("  🔑 Enter the 6-digit code: ").strip()
        if not otp:
            continue
        # Verify using the masked email — server resolves from key
        # We need the real email for verify, so use a key-based verify too
        print("  Verifying…", end="", flush=True)
        r2 = _api("/api/auth/email-otp", {"action": "verify_by_key", "api_key": api_key, "otp": otp})
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


def _cmd_connect(args) -> None:
    """clawmetry connect — validate key, save config, start daemon."""
    # Support piped stdin (curl | bash) — read from /dev/tty if needed
    _tty = None
    if not sys.stdin.isatty():
        try:
            _tty = open('/dev/tty', 'r')
        except OSError:
            pass

    def _input(prompt):
        if _tty is not None:
            sys.stdout.write(prompt)
            sys.stdout.flush()
            return _tty.readline().rstrip('\n')
        return input(prompt)

    # Read existing config BEFORE stopping daemon (preserve node_id + encryption_key)
    _saved_node_id = ''
    _saved_enc_key = ''
    try:
        import json as _jcfg_pre
        _cfgpath_pre = os.path.expanduser('~/.clawmetry/config.json')
        _cfg_pre = _jcfg_pre.load(open(_cfgpath_pre))
        _saved_node_id = _cfg_pre.get('node_id', '')
        _saved_enc_key = _cfg_pre.get('encryption_key', '')
    except Exception:
        pass

    _stop_existing_daemon()
    import getpass
    from clawmetry.sync import validate_key, save_config, CONFIG_FILE, CONFIG_DIR
    import platform, socket

    api_key = args.key or os.environ.get("CLAWMETRY_API_KEY") or ""
    if not api_key:
        api_key = _get_api_key_interactive()

    if not api_key.startswith("cm_"):
        print("❌  Key must start with cm_")
        sys.exit(1)

    # Verify ownership via OTP when key is passed directly (not from interactive flow)
    if args.key:
        _verify_key_ownership(api_key)

    custom_name = getattr(args, 'custom_node_id', None) or ''
    machine_hostname = custom_name or socket.gethostname()
    _existing_node_id = _saved_node_id
    print("Connecting to ClawMetry Cloud… ", end="", flush=True)
    try:
        result = validate_key(api_key, hostname=machine_hostname, existing_node_id=_existing_node_id)
        node_id = result.get("node_id") or machine_hostname
        print(f"✅")
    except Exception as e:
        err = str(e)
        # Allow saving config if network/server issues (ingest may not be live yet)
        if any(x in err for x in ["443", "Connection", "unreachable", "405", "404", "timed out"]):
            node_id = machine_hostname
            print("⚠️  Could not reach server right now. Your config has been saved and will sync when connected.")
        else:
            print(f"❌  {e}")
            sys.exit(1)

    from clawmetry.sync import generate_encryption_key

    # Always prompt for encryption key — be transparent
    # Store the raw passphrase as-is; normalization happens at encrypt/decrypt time
    print()
    print("🔐 Encryption key protects your data end-to-end.")
    if _saved_enc_key:
        masked = _saved_enc_key[:6] + '…' + _saved_enc_key[-4:]
        print(f"  Existing key: {masked}")
        custom_key = _input("  Press Enter to keep it, or type a new one: ").strip()
        enc_key = custom_key if custom_key else _saved_enc_key
    else:
        custom_key = _input("  Enter a custom secret key (or press Enter to auto-generate): ").strip()
        enc_key = custom_key if custom_key else generate_encryption_key()

    config = {
        "api_key": api_key,
        "node_id": node_id,
        "platform": platform.system(),
        "connected_at": __import__("datetime").datetime.now().isoformat(),
        "encryption_key": enc_key,
    }
    save_config(config)

    print()
    print(f"  Connected as: {node_id}")
    print()
    print("  Keep this secret key safe (like a password):")
    print(f"  {enc_key}")
    print()

    # Start daemon
    _start_daemon(config, args)
    print()
    print("  All done! Open app.clawmetry.com to see your dashboard.")
    print()


def _start_daemon(config: dict, args) -> None:
    """Start the sync daemon (as background process or system service)."""
    import subprocess, sys
    from clawmetry.sync import CONFIG_DIR, LOG_FILE

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
    else:
        # Windows / fallback: subprocess
        _start_subprocess()


def _register_launchd(config: dict) -> None:
    from clawmetry.sync import CONFIG_DIR, LOG_FILE
    label = "com.clawmetry.sync"
    plist_path = __import__("pathlib").Path.home() / "Library" / "LaunchAgents" / f"{label}.plist"
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
    <key>RunAtLoad</key>         <true/>
    <key>KeepAlive</key>         <true/>
    <key>StandardOutPath</key>   <string>{LOG_FILE}</string>
    <key>StandardErrorPath</key> <string>{LOG_FILE}</string>
    <key>ThrottleInterval</key>  <integer>30</integer>
</dict>
</plist>"""

    plist_path.parent.mkdir(parents=True, exist_ok=True)
    plist_path.write_text(plist)
    import subprocess as _sp, os as _os
    uid = _os.getuid()
    # Use modern bootstrap (macOS 10.11+), fall back silently to legacy
    r = _sp.run(["launchctl", "bootstrap", f"gui/{uid}", str(plist_path)],
                capture_output=True, check=False)
    if r.returncode != 0:
        _sp.run(["launchctl", "load", "-w", str(plist_path)],
                capture_output=True, check=False)
    print("  Running in the background. Your data is syncing to the cloud.")
    print('  To stop: clawmetry disconnect')


def _register_systemd(config: dict) -> None:
    from clawmetry.sync import LOG_FILE
    import subprocess
    label = "clawmetry-sync"
    service_dir = __import__("pathlib").Path.home() / ".config" / "systemd" / "user"
    service_dir.mkdir(parents=True, exist_ok=True)
    service_path = service_dir / f"{label}.service"
    # Use the current interpreter (venv-aware) so the daemon finds clawmetry
    python = sys.executable

    unit = f"""[Unit]
Description=ClawMetry Cloud Sync Daemon
After=network.target

[Service]
ExecStart={python} -m clawmetry.sync
Restart=always
RestartSec=30
StandardOutput=append:{LOG_FILE}
StandardError=append:{LOG_FILE}

[Install]
WantedBy=default.target
"""
    service_path.write_text(unit)
    subprocess.run(["systemctl", "--user", "daemon-reload"], check=False)
    subprocess.run(["systemctl", "--user", "enable", "--now", label], check=False)
    print("  Running in the background. Your data is syncing to the cloud.")
    print('  To stop: clawmetry disconnect')


def _start_subprocess() -> None:
    import subprocess
    sync_script = str(__import__("pathlib").Path(__file__).parent / "sync.py")
    proc = subprocess.Popen(
        [sys.executable, sync_script],
        stdout=open(str(__import__("pathlib").Path.home() / ".clawmetry" / "sync.log"), "a"),
        stderr=subprocess.STDOUT,
        start_new_session=True,
    )
    print(f"✅  Sync daemon started (pid {proc.pid})")


def _cmd_disconnect(args) -> None:
    """clawmetry disconnect — stop daemon and remove key."""
    import subprocess
    from clawmetry.sync import CONFIG_FILE, STATE_FILE
    import platform

    system = platform.system()
    if system == "Darwin":
        label = "com.clawmetry.sync"
        plist = __import__("pathlib").Path.home() / "Library" / "LaunchAgents" / f"{label}.plist"
        subprocess.run(["launchctl", "unload", str(plist)], check=False, capture_output=True)
        if plist.exists():
            plist.unlink()
        print(f"✅  Stopped launchd daemon ({label})")
    elif system == "Linux":
        subprocess.run(["systemctl", "--user", "disable", "--now", "clawmetry-sync"], check=False, capture_output=True)
        svc = __import__("pathlib").Path.home() / ".config" / "systemd" / "user" / "clawmetry-sync.service"
        if svc.exists():
            svc.unlink()
        print("✅  Stopped systemd daemon (clawmetry-sync)")

    if CONFIG_FILE.exists():
        CONFIG_FILE.unlink()
        print(f"✅  Removed config ({CONFIG_FILE})")
    if STATE_FILE.exists():
        STATE_FILE.unlink()

    print("Disconnected from ClawMetry Cloud.")


def _cmd_status(args) -> None:
    """clawmetry status — show local + cloud sync status."""
    import platform
    from clawmetry.sync import CONFIG_FILE, STATE_FILE, LOG_FILE

    print("ClawMetry Status\n" + "─" * 40)

    # Config
    if CONFIG_FILE.exists():
        try:
            import json
            cfg = json.loads(CONFIG_FILE.read_text())
            api_key = cfg.get("api_key", "")
            enc_key = cfg.get("encryption_key", "")
            masked_api = api_key[:6] + "…" + api_key[-4:] if len(api_key) > 10 else api_key
            print(f"  Cloud sync:  ✅  Connected")
            print(f"  API key:     {masked_api}")
            print(f"  Node ID:     {cfg.get('node_id', '?')}")
            print(f"  Connected:   {cfg.get('connected_at', '?')[:19]}")
            if enc_key:
                if getattr(args, 'show_key', False):
                    print(f"  Secret key:     {enc_key}")
                else:
                    masked_enc = enc_key[:6] + "…" + enc_key[-4:]
                    print(f"  Secret key:     {masked_enc}  (--show-key to reveal)")
                print(f"  E2E:         🔒 enabled")
            else:
                print(f"  E2E:         ⚠️  disabled (no secret key in config)")
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

    # Daemon status
    system = platform.system()
    print()
    if system == "Darwin":
        import subprocess
        r = subprocess.run(["launchctl", "list", "com.clawmetry.sync"], capture_output=True, text=True)
        if r.returncode == 0:
            print("  Daemon:      ✅  Running (launchd)")
        else:
            print("  Daemon:      ○  Not running")
    elif system == "Linux":
        import subprocess
        r = subprocess.run(["systemctl", "--user", "is-active", "clawmetry-sync"], capture_output=True, text=True)
        running = r.stdout.strip() == "active"
        print(f"  Daemon:      {'✅  Running (systemd)' if running else '○  Not running'}")

    if LOG_FILE.exists():
        print(f"  Log:         {LOG_FILE}")
        # Last 3 lines
        lines = LOG_FILE.read_text(errors="replace").splitlines()[-3:]
        for ln in lines:
            print(f"    {ln}")


def _cmd_onboard(args) -> None:
    """clawmetry onboard — interactive first-time setup wizard."""
    import os as _os

    _is_tty = sys.stdout.isatty()
    def _c(code, text): return f"\033[{code}m{text}\033[0m" if _is_tty else text
    BOLD = lambda t: _c("1", t)
    GREEN = lambda t: _c("32", t)
    CYAN = lambda t: _c("36", t)
    DIM = lambda t: _c("2", t)

    # When stdin is piped (curl | bash), read from /dev/tty
    _tty = None
    if not sys.stdin.isatty():
        try:
            _tty = open('/dev/tty', 'r')
        except OSError:
            pass

    def _input(prompt):
        if _tty is not None:
            sys.stdout.write(prompt)
            sys.stdout.flush()
            return _tty.readline().rstrip('\n')
        return input(prompt)

    already_connected = bool(_os.environ.get("CLAWMETRY_API_KEY") or _os.environ.get("CLAWMETRY_NODE_ID"))
    if already_connected:
        print(f"\n  {GREEN(BOLD('✓ Already connected to ClawMetry Cloud'))}")
        print(f"  {DIM('Run  clawmetry status  to check sync health.')}\n")
        return

    print(f"\n  {BOLD('Connect to ClawMetry Cloud to monitor from anywhere:')}")
    print(f"  {BOLD('app.clawmetry.com')}")
    print(f"\n  {DIM('E2E encrypted. Only you can read it.')}\n")
    print(f"      {BOLD('[Y]')} Start 7-day trial {DIM('(then $5/node/mo)')}")
    print(f"      {BOLD('[n]')} Run locally for now")
    print(f"          {DIM('Enable cloud anytime: clawmetry connect')}\n")

    try:
        choice = _input("  → [Y/n]: ").strip().lower() or 'y'
    except (EOFError, KeyboardInterrupt):
        choice = 'n'
        print()

    print()

    if choice in ('y', 'yes'):
        print()
        import argparse as _ap
        _fake_args = _ap.Namespace(key=None, foreground=False, custom_node_id=None)
        _cmd_connect(_fake_args)

        print(f"\n  {BOLD('All done!')}\n")

        try:
            _input("  Press Enter to open your ClawMetry dashboard...")
        except (EOFError, KeyboardInterrupt):
            pass

        try:
            import webbrowser
            webbrowser.open("https://app.clawmetry.com")
        except Exception:
            pass
    else:
        print(f"  {GREEN('✓')} ClawMetry installed (local mode)\n")
        print(f"  Start your dashboard:")
        print(f"    {CYAN('clawmetry --host 0.0.0.0 --port 8900')}          {DIM('# foreground (LAN)')}")
        print(f"    {CYAN('clawmetry start --host 0.0.0.0 --port 8900')}    {DIM('# background service')}\n")
        print(f"  {DIM('Connect to cloud later: clawmetry connect')}\n")


def _cmd_proxy(args) -> None:
    """clawmetry proxy — manage the enforcement proxy."""
    from clawmetry.proxy import (
        ProxyConfig, run_proxy, stop_proxy, proxy_status as _proxy_status,
        PROXY_CONFIG_FILE,
    )

    _is_tty = sys.stdout.isatty()
    def _c(code, text): return f"\033[{code}m{text}\033[0m" if _is_tty else text
    BOLD = lambda t: _c("1", t)
    GREEN = lambda t: _c("32", t)
    CYAN = lambda t: _c("36", t)
    DIM = lambda t: _c("2", t)
    YELLOW = lambda t: _c("33", t)

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
        print(f"  {BOLD('🦞 ClawMetry Proxy')}")
        print()
        print(f"  Listening on {CYAN(f'http://{config.host}:{config.port}')}")
        print()
        print(f"  Budget:         {_format_budget(config, GREEN, YELLOW, DIM)}")
        print(f"  Loop detection: {GREEN('on') if config.loop_detection.enabled else DIM('off')}")
        print(f"  Routing rules:  {len(config.routing_rules)}")
        print()
        print(f"  {BOLD('To activate, set in your environment:')}")
        print(f"    {CYAN(f'ANTHROPIC_BASE_URL=http://localhost:{config.port}')}")
        print(f"    {DIM('(OpenClaw will route all LLM calls through the proxy)')}")
        print()

        if not args.foreground:
            import subprocess
            proc = subprocess.Popen(
                [sys.executable, "-m", "clawmetry.proxy",
                 "--port", str(config.port),
                 "--host", config.host],
                stdout=open(str(PROXY_CONFIG_FILE.parent / "proxy.log"), "a"),
                stderr=subprocess.STDOUT,
                start_new_session=True,
            )
            print(f"  {GREEN('✓')} Proxy started in background (pid {proc.pid})")
            _log_path = PROXY_CONFIG_FILE.parent / "proxy.log"
            print(f"  {DIM(f'Log: {_log_path}')} ")
            print()
        else:
            print(f"  Running in foreground (Ctrl+C to stop)")
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
                import urllib.request, json
                config = ProxyConfig.load()
                url = f"http://{config.host}:{config.port}/proxy/status"
                with urllib.request.urlopen(url, timeout=3) as r:
                    detail = json.loads(r.read())
                print(f"  Uptime:    {_format_uptime(detail.get('uptime_seconds', 0))}")
                print(f"  Requests:  {detail.get('requests_total', 0)} total, {detail.get('requests_blocked', 0)} blocked")
                print(f"  Loops:     {detail.get('loops_detected', 0)} detected")
                b = detail.get("budget", {})
                if b.get("daily_limit", 0) > 0:
                    print(f"  Daily:     ${b['daily_spent']:.2f} / ${b['daily_limit']:.2f}")
                if b.get("monthly_limit", 0) > 0:
                    print(f"  Monthly:   ${b['monthly_spent']:.2f} / ${b['monthly_limit']:.2f}")
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
            config.loop_detection.enabled = (args.loop_detection == "on")
            changed = True

        if changed:
            config.save()
            print(f"  {GREEN('✓')} Config updated")

        print(f"\n  {BOLD('Proxy Configuration')}")
        print(f"  {'─' * 40}")
        print(f"  Port:           {config.port}")
        print(f"  Host:           {config.host}")
        print(f"  Daily budget:   {'$' + str(config.budget.daily_usd) if config.budget.daily_usd > 0 else DIM('unlimited')}")
        print(f"  Monthly budget: {'$' + str(config.budget.monthly_usd) if config.budget.monthly_usd > 0 else DIM('unlimited')}")
        print(f"  Action:         {config.budget.action}")
        print(f"  Loop detection: {GREEN('on') if config.loop_detection.enabled else DIM('off')}")
        print(f"  Routing rules:  {len(config.routing_rules)}")
        print(f"\n  Config file: {DIM(str(PROXY_CONFIG_FILE))}")
        print()

    else:
        print(f"\n  {BOLD('🦞 ClawMetry Proxy')} — enforcement layer for LLM API calls")
        print()
        print(f"  {BOLD('Commands:')}")
        print(f"    clawmetry proxy start    Start the proxy server")
        print(f"    clawmetry proxy stop     Stop the proxy server")
        print(f"    clawmetry proxy status   Show proxy status")
        print(f"    clawmetry proxy config   View/update proxy config")
        print()
        print(f"  {BOLD('Quick start:')}")
        print(f"    clawmetry proxy start --daily-budget 10")
        print(f"    export ANTHROPIC_BASE_URL=http://localhost:4100")
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


def _cmd_update() -> None:
    """Self-update clawmetry to the latest PyPI version."""
    import subprocess
    try:
        from dashboard import __version__ as current
    except Exception:
        current = "unknown"
    print(f"Current version: {current}")
    print("Checking for updates...")
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "--upgrade", "clawmetry"],
            capture_output=True, text=True, timeout=120,
        )
        if result.returncode == 0:
            # Check new version
            try:
                new_ver = subprocess.run(
                    [sys.executable, "-c", "from dashboard import __version__; print(__version__)"],
                    capture_output=True, text=True, timeout=10,
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
                        subprocess.run(["clawmetry", "daemon", "restart"],
                                       capture_output=True, timeout=15)
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


def main() -> None:
    import argparse
    from dashboard import main as dashboard_main

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
                try:
                    setattr(sys, _attr, open(os.devnull, "w", encoding="utf-8"))
                except OSError:
                    setattr(sys, _attr, _io.StringIO())

    parser = argparse.ArgumentParser(prog="clawmetry", add_help=False)
    parser.add_argument('--openclaw-dir', type=str, help='OpenClaw config directory (default: ~/.openclaw). Env: CLAWMETRY_OPENCLAW_DIR')
    sub = parser.add_subparsers(dest="cmd")

    # onboard — first-time setup wizard (called by install.sh)
    p_onboard = sub.add_parser("onboard", help="First-time setup wizard (run after install)")
    p_onboard.add_argument("--key", metavar="cm_xxx", help="API key (skip prompt)")
    p_onboard.add_argument("--foreground", action="store_true", help="Run daemon in foreground")
    p_onboard.add_argument("--node-id", metavar="NAME", dest="custom_node_id", help="Custom node name (default: hostname)")

    # connect
    p_connect = sub.add_parser("connect", help="Activate cloud sync")
    p_connect.add_argument("--key", metavar="cm_xxx", help="API key (skip prompt)")
    p_connect.add_argument("--foreground", action="store_true", help="Run daemon in foreground")
    p_connect.add_argument("--node-id", metavar="NAME", dest="custom_node_id", help="Custom node name (default: hostname)")

    # disconnect
    sub.add_parser("disconnect", help="Stop cloud sync and remove key")

    # status
    p_status = sub.add_parser("status", help="Show local + cloud sync status")
    p_status.add_argument("--show-key", action="store_true", help="Reveal secret key")

    # proxy
    p_proxy = sub.add_parser("proxy", help="Local enforcement proxy (budget, loops, routing)")
    proxy_sub = p_proxy.add_subparsers(dest="proxy_cmd")

    p_proxy_start = proxy_sub.add_parser("start", help="Start the proxy server")
    p_proxy_start.add_argument("--port", type=int, help="Port (default: 4100)")
    p_proxy_start.add_argument("--host", default=None, help="Bind host (default: 127.0.0.1)")
    p_proxy_start.add_argument("--foreground", action="store_true", help="Run in foreground")
    p_proxy_start.add_argument("--daily-budget", type=float, metavar="USD", help="Daily budget limit in USD")
    p_proxy_start.add_argument("--monthly-budget", type=float, metavar="USD", help="Monthly budget limit in USD")
    p_proxy_start.add_argument("--no-loop-detection", action="store_true", help="Disable loop detection")
    p_proxy_start.add_argument("--log-requests", action="store_true", help="Log all proxied requests")

    proxy_sub.add_parser("stop", help="Stop the proxy server")

    p_proxy_status = proxy_sub.add_parser("status", help="Show proxy status")
    p_proxy_status.add_argument("--json", action="store_true", dest="as_json", help="Output as JSON")

    p_proxy_config = proxy_sub.add_parser("config", help="Show or update proxy config")
    p_proxy_config.add_argument("--daily-budget", type=float, metavar="USD", help="Set daily budget")
    p_proxy_config.add_argument("--monthly-budget", type=float, metavar="USD", help="Set monthly budget")
    p_proxy_config.add_argument("--action", choices=["block", "warn", "downgrade"], help="Budget action")
    p_proxy_config.add_argument("--loop-detection", choices=["on", "off"], help="Toggle loop detection")

    # update — self-update to latest PyPI version
    sub.add_parser("update", help="Update clawmetry to the latest version")

    # Parse just the first token to decide if it's a sub-command or dashboard flag
    _subcmds = ("onboard", "connect", "disconnect", "status", "proxy", "update")
    if len(sys.argv) > 1 and sys.argv[1] in _subcmds:
        args = parser.parse_args()
        # Issue #322: Set OpenClaw config directory from CLI flag
        if getattr(args, 'openclaw_dir', None):
            os.environ['CLAWMETRY_OPENCLAW_DIR'] = os.path.expanduser(args.openclaw_dir)

        if args.cmd == "onboard":
            _cmd_onboard(args)
        elif args.cmd == "connect":
            _cmd_connect(args)
        elif args.cmd == "disconnect":
            _cmd_disconnect(args)
        elif args.cmd == "status":
            _cmd_status(args)
        elif args.cmd == "proxy":
            _cmd_proxy(args)
        elif args.cmd == "update":
            _cmd_update()
    else:
        # Fall through to dashboard (handles --host, --port, --version, start, stop, etc.)
        dashboard_main()


if __name__ == "__main__":
    main()
