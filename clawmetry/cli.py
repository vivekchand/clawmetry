"""CLI entry point for the clawmetry package."""
from __future__ import annotations
import sys
import os

_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _root not in sys.path:
    sys.path.insert(0, _root)


def _cmd_connect(args) -> None:
    """clawmetry connect — validate key, save config, start daemon."""
    import getpass
    from clawmetry.sync import validate_key, save_config, CONFIG_FILE, CONFIG_DIR
    import platform, socket

    api_key = args.key or os.environ.get("CLAWMETRY_API_KEY") or ""
    if not api_key:
        print("Get your API key at: https://app.clawmetry.com/connect\n")
        api_key = getpass.getpass("ClawMetry API key (cm_…): ").strip()

    if not api_key.startswith("cm_"):
        print("❌  Key must start with cm_")
        sys.exit(1)

    print(f"Validating key… ", end="", flush=True)
    try:
        result = validate_key(api_key)
        node_id = result.get("node_id") or socket.gethostname()
        print(f"✅")
    except Exception as e:
        err = str(e)
        # Allow saving config if network/server issues (ingest may not be live yet)
        if any(x in err for x in ["443", "Connection", "unreachable", "405", "404", "timed out"]):
            node_id = socket.gethostname()
            print(f"⚠️  Ingest server not reachable ({e}). Saving config locally.")
        else:
            print(f"❌  {e}")
            sys.exit(1)

    from clawmetry.sync import generate_encryption_key
    enc_key = generate_encryption_key()

    config = {
        "api_key": api_key,
        "node_id": node_id,
        "platform": platform.system(),
        "connected_at": __import__("datetime").datetime.now().isoformat(),
        "encryption_key": enc_key,
    }
    save_config(config)

    print()
    print(f"  ✅  Config saved  {CONFIG_FILE}")
    print(f"  Node ID:          {node_id}")
    print()
    print("  🔒  Encryption key (keep this safe — you need it to view your data):")
    print()
    print(f"      {enc_key}")
    print()
    print("  Store this key in your password manager.")
    print("  You'll paste it into app.clawmetry.com / iOS / Mac app to decrypt your data.")
    print("  The server never sees it — lose it and your cloud data is unreadable.")
    print()

    # Start daemon
    _start_daemon(config, args)


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
    python = sys.executable
    sync_script = str(__import__("pathlib").Path(__file__).parent / "sync.py")

    plist = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>             <string>{label}</string>
    <key>ProgramArguments</key>
    <array>
        <string>{python}</string>
        <string>{sync_script}</string>
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
    __import__("subprocess").run(["launchctl", "load", "-w", str(plist_path)], check=False)
    print(f"✅  Sync daemon registered with launchd ({label})")
    print(f"    Logs: {LOG_FILE}")
    print(f"    Stop: clawmetry disconnect")


def _register_systemd(config: dict) -> None:
    from clawmetry.sync import LOG_FILE
    import subprocess
    label = "clawmetry-sync"
    service_dir = __import__("pathlib").Path.home() / ".config" / "systemd" / "user"
    service_dir.mkdir(parents=True, exist_ok=True)
    service_path = service_dir / f"{label}.service"
    python = sys.executable
    sync_script = str(__import__("pathlib").Path(__file__).parent / "sync.py")

    unit = f"""[Unit]
Description=ClawMetry Cloud Sync Daemon
After=network.target

[Service]
ExecStart={python} {sync_script}
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
    print(f"✅  Sync daemon registered with systemd ({label})")
    print(f"    Logs: {LOG_FILE}")
    print(f"    Stop: clawmetry disconnect")


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
                    print(f"  Enc key:     {enc_key}")
                else:
                    masked_enc = enc_key[:6] + "…" + enc_key[-4:]
                    print(f"  Enc key:     {masked_enc}  (--show-key to reveal)")
                print(f"  E2E:         🔒 enabled")
            else:
                print(f"  E2E:         ⚠️  disabled (no encryption key in config)")
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
    from dashboard import main as dashboard_main

    parser = argparse.ArgumentParser(prog="clawmetry", add_help=False)
    sub = parser.add_subparsers(dest="cmd")

    # connect
    p_connect = sub.add_parser("connect", help="Activate cloud sync")
    p_connect.add_argument("--key", metavar="cm_xxx", help="API key (skip prompt)")
    p_connect.add_argument("--foreground", action="store_true", help="Run daemon in foreground")

    # disconnect
    sub.add_parser("disconnect", help="Stop cloud sync and remove key")

    # status
    p_status = sub.add_parser("status", help="Show local + cloud sync status")
    p_status.add_argument("--show-key", action="store_true", help="Reveal encryption key")

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
