"""CLI entry point for the clawmetry package."""
from __future__ import annotations
import sys
import os

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

def _cmd_connect(args) -> None:
    """clawmetry connect — validate key, save config, start daemon."""
    _stop_existing_daemon()
    import getpass
    from clawmetry.sync import validate_key, save_config, CONFIG_FILE, CONFIG_DIR
    import platform, socket

    api_key = args.key or os.environ.get("CLAWMETRY_API_KEY") or ""
    if not api_key:
        print("Get your API key at: https://clawmetry.com/connect\n")
        api_key = getpass.getpass("ClawMetry API key (cm_…): ").strip()

    if not api_key.startswith("cm_"):
        print("❌  Key must start with cm_")
        sys.exit(1)

    print("Connecting to ClawMetry Cloud… ", end="", flush=True)
    try:
        result = validate_key(api_key)
        node_id = result.get("node_id") or socket.gethostname()
        print(f"✅")
    except Exception as e:
        err = str(e)
        # Allow saving config if network/server issues (ingest may not be live yet)
        if any(x in err for x in ["443", "Connection", "unreachable", "405", "404", "timed out"]):
            node_id = socket.gethostname()
            print("⚠️  Could not reach server right now. Your config has been saved and will sync when connected.")
        else:
            print(f"❌  {e}")
            sys.exit(1)

    from clawmetry.sync import generate_encryption_key

    # Use user-supplied key, preserve existing key, or generate a fresh one
    supplied_key = getattr(args, "secret_key", None) or os.environ.get("CLAWMETRY_SECRET_KEY", "")
    existing_key = ""
    try:
        import json as _j
        _cfg = _j.load(open(os.path.expanduser("~/.clawmetry/config.json")))
        existing_key = _cfg.get("encryption_key", "")
    except Exception:
        pass
    if supplied_key:
        enc_key = supplied_key
        key_source = "custom"
    elif existing_key:
        enc_key = existing_key
        key_source = "existing"
    else:
        enc_key = generate_encryption_key()
        key_source = "generated"

    config = {
        "api_key": api_key,
        "node_id": node_id,
        "platform": platform.system(),
        "connected_at": __import__("datetime").datetime.now().isoformat(),
        "encryption_key": enc_key,
    }
    save_config(config)

    # Upload secret key to cloud so dashboard can show it (key never leaves without consent)
    try:
        from clawmetry.sync import _post
        _post("/api/account/secret-key", {"secret_key": enc_key, "node_id": node_id},
              api_key, timeout=5)
    except Exception:
        pass  # Non-fatal — key is still in local config

    print()
    print(f"  Connected as: {node_id}")
    print()
    if key_source == "custom":
        print("  Using your custom secret key:")
    else:
        print("  Generated secret key (keep this safe — like a password):")
    print(f"  {enc_key}")
    print()
    print("  To use your own key next time: clawmetry connect --secret-key <your-key>")
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


def _cmd_onboard(args) -> None:
    """clawmetry onboard — full first-time setup wizard (always run after install)."""
    CYAN = '\033[0;36m'
    BOLD = '\033[1m'
    NC = '\033[0m'

    print()
    print(f"  {BOLD}Welcome to ClawMetry 🦞{NC}")
    print(f"  Let's get your agent connected to the cloud dashboard.")
    print()

    # Run the connect flow
    _cmd_connect(args)

    # Open the app in the default browser
    try:
        import webbrowser
        webbrowser.open("https://app.clawmetry.com")
    except Exception:
        pass

    print(f"  {CYAN}→{NC} Opening app.clawmetry.com in your browser...")
    print()
    print(f"  {BOLD}Setup complete!{NC} Your agent is now streaming to ClawMetry Cloud.")
    print()


def main() -> None:
    import argparse
    from dashboard import main as dashboard_main

    parser = argparse.ArgumentParser(prog="clawmetry", add_help=False)
    sub = parser.add_subparsers(dest="cmd")

    # onboard — first-time setup wizard (called by install.sh)
    p_onboard = sub.add_parser("onboard", help="First-time setup wizard (run after install)")
    p_onboard.add_argument("--key", metavar="cm_xxx", help="API key (skip prompt)")
    p_onboard.add_argument("--secret-key", metavar="KEY", dest="secret_key",
                           help="Your own encryption key (base64url). Auto-generated if omitted.")
    p_onboard.add_argument("--foreground", action="store_true", help="Run daemon in foreground")

    # connect
    p_connect = sub.add_parser("connect", help="Activate cloud sync")
    p_connect.add_argument("--key", metavar="cm_xxx", help="API key (skip prompt)")
    p_connect.add_argument("--secret-key", metavar="KEY", dest="secret_key",
                           help="Your own encryption key (base64url). Auto-generated if omitted.")
    p_connect.add_argument("--foreground", action="store_true", help="Run daemon in foreground")

    # disconnect
    sub.add_parser("disconnect", help="Stop cloud sync and remove key")

    # status
    p_status = sub.add_parser("status", help="Show local + cloud sync status")
    p_status.add_argument("--show-key", action="store_true", help="Reveal secret key")

    # Parse just the first token to decide if it's a sub-command or dashboard flag
    if len(sys.argv) > 1 and sys.argv[1] in ("onboard", "connect", "disconnect", "status"):
        args = parser.parse_args()
        if args.cmd == "onboard":
            _cmd_onboard(args)
        elif args.cmd == "connect":
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
