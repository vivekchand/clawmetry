"""CLI entry point for the clawmetry package."""
from __future__ import annotations
import sys
import os





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

def _cmd_connect(args) -> None:
    """clawmetry connect — validate key, save config, start daemon."""
    # Read existing config FIRST — before stopping daemon (avoids race condition)
    _saved_key = ''
    _saved_node_id = ''
    try:
        import json as _jcfg_pre
        _cfgpath_pre = os.path.expanduser('~/.clawmetry/config.json')
        _cfg_pre_data = _jcfg_pre.load(open(_cfgpath_pre))
        _saved_key = _cfg_pre_data.get('encryption_key', '')
        _saved_node_id = _cfg_pre_data.get('node_id', '')
    except Exception:
        pass
    _stop_existing_daemon()
    import getpass
    from clawmetry.sync import validate_key, save_config, CONFIG_FILE, CONFIG_DIR
    import platform, socket

    api_key = args.key or os.environ.get("CLAWMETRY_API_KEY") or ""
    _email_authed = False

    # Terminal sign-up/sign-in: if no API key, collect email + OTP
    if not api_key:
        import urllib.request as _urlibsignup, json as _jsonsignup
        _CLOUD = 'https://app.clawmetry.com'
        def _signup_post(path, payload):
            _req = _urlibsignup.Request(_CLOUD + path,
                data=_jsonsignup.dumps(payload).encode(),
                headers={'Content-Type': 'application/json'}, method='POST')
            with _urlibsignup.urlopen(_req, timeout=12) as _r:
                return _jsonsignup.loads(_r.read())

        print()
        _email_in = input("  \U0001f4e7  Enter your email: ").strip().lower()
        if not _email_in:
            print("  \u274c  Email required.")
            sys.exit(1)
        print("  \U0001f510  Sending verification code...", end="", flush=True)
        try:
            _signup_post('/api/auth/email-otp', {'action': 'send', 'email': _email_in})
        except Exception as _se:
            print(f" failed ({_se})")
            sys.exit(1)
        print(" sent.")
        print(f"  \U0001f4ec  Check your inbox for the 6-digit code.")
        _otp_in = input("  Enter OTP: ").strip()
        try:
            _vfy = _signup_post('/api/auth/email-otp', {'action': 'verify', 'email': _email_in, 'otp': _otp_in})
        except Exception as _ve:
            print(f"\n  \u274c  Verification failed: {_ve}")
            sys.exit(1)
        if not _vfy.get('ok'):
            print(f"\n  \u274c  {_vfy.get('error', 'Incorrect OTP')}")
            sys.exit(1)
        api_key = _vfy['api_key']
        _email_authed = True
        if _vfy.get('is_new'):
            print(f"  \u2705  Account created! 7-day free trial started.")
        else:
            print(f"  \u2705  Signed in.")
        print()

    if not api_key:
        print("Get your API key at: https://clawmetry.com/connect\n")
        api_key = getpass.getpass("ClawMetry API key (cm_…): ").strip()

    if not api_key.startswith("cm_"):
        print("❌  Key must start with cm_")
        sys.exit(1)

    custom_name = getattr(args, 'custom_node_id', None) or ''
    machine_hostname = custom_name or socket.gethostname()
    # Use key saved at top of function (before daemon stop)
    _existing_node_id = _saved_node_id
    _existing_key = _saved_key
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
    # 🔐 Device OTP — skipped when already verified via email sign-in
    if not _email_authed:
        try:
            import socket as _sock, platform as _plat, urllib.request as _urlibr, json as _jsotp
            try:
                _udp = _sock.socket(_sock.AF_INET, _sock.SOCK_DGRAM)
                _udp.connect(('8.8.8.8', 80))
                _local_ips = [_udp.getsockname()[0]]
                _udp.close()
            except Exception:
                try:
                    _local_ips = [_sock.gethostbyname(_sock.gethostname())]
                except Exception:
                    _local_ips = []
            _sysinfo = {
                'Device': machine_hostname,
                'OS': _plat.system() + ' ' + _plat.release() + ' (' + _plat.machine() + ')',
                'IP': ', '.join(_local_ips) or 'unknown',
                'Node ID': node_id,
            }
            _otp_headers = {'Content-Type': 'application/json', 'Authorization': 'Bearer ' + api_key}
            def _cloud_otp(payload):
                _req = _urlibr.Request('https://app.clawmetry.com/api/account/connect-otp',
                    data=_jsotp.dumps(payload).encode(), headers=_otp_headers, method='POST')
                with _urlibr.urlopen(_req, timeout=10) as _r: return _jsotp.loads(_r.read())
            _otp_r = _cloud_otp({'api_key': api_key, 'action': 'send',
                                  'hostname': machine_hostname, 'sysinfo': _sysinfo})
            _otp_email = _otp_r.get('email', 'your registered email')
            print(f"\n  \U0001f510  Verification required.")
            print(f"  \U0001f4e7  OTP sent to {_otp_email} — check your inbox.")
            _otp_in = input("  Enter OTP: ").strip()
            _vfy = _cloud_otp({'api_key': api_key, 'action': 'verify', 'otp': _otp_in})
            if not _vfy.get('ok'):
                print(f"\n  \u274c  Verification failed: {_vfy.get('error', 'Incorrect OTP')}")
                sys.exit(1)
            print("  \u2705  Device authorised.")
        except (SystemExit, KeyboardInterrupt):
            raise
        except Exception as _otp_err:
            print(f"\n  \u274c  OTP verification failed: {_otp_err}")
            print("  Cannot connect without device verification. Try again or contact support.")
            sys.exit(1)

    from clawmetry.sync import generate_encryption_key

    # Handle --secret-key: require OTP confirmation before accepting new key
    supplied_key = getattr(args, 'secret_key', None) or os.environ.get('CLAWMETRY_SECRET_KEY', '')
    if supplied_key and supplied_key != _existing_key:
        # Send OTP to email
        try:
            from clawmetry.sync import _post
            _otp_resp = _post('/api/account/key-change-otp', {'api_key': api_key, 'action': 'send'}, api_key, timeout=8)
            _otp_email = _otp_resp.get('email', 'your registered email')
            print(f'\n  OTP sent to {_otp_email}.')
            _otp_entered = input('  Enter OTP to confirm key change: ').strip()
            _verify = _post('/api/account/key-change-otp', {'api_key': api_key, 'action': 'verify', 'otp': _otp_entered}, api_key, timeout=8)
            if not _verify.get('ok'):
                print(f"\n  OTP verification failed: {_verify.get('error', 'Unknown error')}")
                sys.exit(1)
            enc_key = supplied_key
            print('  Secret key updated.')
        except SystemExit:
            raise
        except Exception as _otp_err:
            print(f'\n  Could not complete OTP verification: {_otp_err}')
            sys.exit(1)
    else:
        if _existing_key:
            # Reuse existing key — no prompt needed
            enc_key = _existing_key
            _masked = enc_key[:6] + "…" + enc_key[-4:]
            print(f"  🔑  Encryption key: {_masked}  (run clawmetry status --show-key to reveal)")
        else:
            # New device / new account — prompt user
            print()
            print("  \U0001f510  E2E Encryption Key")
            print("  All your data is encrypted end-to-end. You need this key to decrypt and view it in the web app.")
            print("  ClawMetry never stores or sees this key.")
            print()
            _key_input = input("  Enter a secret key (or press Enter to auto-generate): ").strip()
            if _key_input:
                enc_key = _key_input
                print(f"  \u2705  Using your key.")
            else:
                enc_key = generate_encryption_key()
                print(f"  \U0001f511  Generated key: {enc_key}")
                print(f"  \u26a0\ufe0f   Save this somewhere safe — you need it to decrypt your data in the web app.")
            print()

    config = {
        "api_key": api_key,
        "node_id": node_id,
        "platform": platform.system(),
        "connected_at": __import__("datetime").datetime.now().isoformat(),
        "encryption_key": enc_key,
    }
    save_config(config)

    print()
    print(f"  \U0001f7e2  Connected as: {node_id}")
    print()

    # Start daemon
    _start_daemon(config, args)
    print()
    print("  All done!")
    print()
    input("  Press Enter to open your ClawMetry dashboard... ")
    try:
        import webbrowser as _wb, urllib.request as _wbr, json as _wbj
        _dashboard_url = 'https://app.clawmetry.com/cloud'
        try:
            # Create one-time setup token so browser gets enc key automatically
            _req = _wbr.Request(
                'https://app.clawmetry.com/api/cloud/setup-session',
                data=_wbj.dumps({'api_key': api_key, 'enc_key': enc_key, 'node_id': node_id}).encode(),
                headers={'Content-Type': 'application/json', 'Authorization': 'Bearer ' + api_key},
                method='POST')
            with _wbr.urlopen(_req, timeout=6) as _wr:
                _wresp = _wbj.loads(_wr.read())
            if _wresp.get('setup_token'):
                _dashboard_url = 'https://app.clawmetry.com/cloud?setup=' + _wresp['setup_token']
        except Exception:
            pass
        _wb.open(_dashboard_url)
    except Exception:
        print("  Open: https://app.clawmetry.com")
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
    # Resolve python3 at registration time, but use -m so pip upgrades take effect
    import shutil
    python = shutil.which("python3") or sys.executable
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
    import shutil
    python = shutil.which("python3") or sys.executable

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


def main() -> None:
    import argparse
    import importlib.util as _ilu, pathlib as _pl
    _dp = _pl.Path(__file__).parent.parent / "dashboard.py"
    _spec = _ilu.spec_from_file_location("_clawmetry_dashboard", str(_dp))
    _mod = _ilu.module_from_spec(_spec)
    _spec.loader.exec_module(_mod)  # type: ignore[union-attr]
    dashboard_main = _mod.main

    parser = argparse.ArgumentParser(prog="clawmetry", add_help=False)
    sub = parser.add_subparsers(dest="cmd")

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

    # Parse just the first token to decide if it's a sub-command or dashboard flag
    if len(sys.argv) > 1 and sys.argv[1] in ("connect", "disconnect", "status"):
        args = parser.parse_args()
        if args.cmd == "connect":
            _cmd_connect(args)
        elif args.cmd == "disconnect":
            _cmd_disconnect(args)
        elif args.cmd == "status":
            _cmd_status(args)
    else:
        # Fall through to dashboard (handles --host, --port, --version, start, stop, etc.)
        dashboard_main()


if __name__ == "__main__":
    main()
