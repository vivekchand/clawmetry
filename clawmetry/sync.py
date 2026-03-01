"""
clawmetry/sync.py — Cloud sync daemon for clawmetry connect.

Reads local OpenClaw sessions/logs and streams to ingest.clawmetry.com.
Runs as a standalone process; the dashboard never needs to know about it.
"""
from __future__ import annotations
import json
import os
import sys
import time
import glob
import hashlib
import logging
import threading
import platform
import subprocess
import urllib.request
import urllib.error
from pathlib import Path
from datetime import datetime, timezone

INGEST_URL = os.environ.get("CLAWMETRY_INGEST_URL", "https://ingest.clawmetry.com")
CONFIG_DIR = Path.home() / ".clawmetry"
CONFIG_FILE = CONFIG_DIR / "config.json"
STATE_FILE  = CONFIG_DIR / "sync-state.json"
LOG_FILE    = CONFIG_DIR / "sync.log"

POLL_INTERVAL = 15   # seconds between sync cycles
BATCH_SIZE    = 100  # max events per POST

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [clawmetry-sync] %(levelname)s %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(str(LOG_FILE), encoding="utf-8"),
    ],
)
log = logging.getLogger("clawmetry.sync")


# ── Config ────────────────────────────────────────────────────────────────────

def load_config() -> dict:
    if not CONFIG_FILE.exists():
        raise FileNotFoundError(f"No config at {CONFIG_FILE}. Run: clawmetry connect")
    return json.loads(CONFIG_FILE.read_text())


def save_config(data: dict) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(json.dumps(data, indent=2))
    CONFIG_FILE.chmod(0o600)


def load_state() -> dict:
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text())
        except Exception:
            pass
    return {"last_event_ids": {}, "last_log_offsets": {}, "last_sync": None}


def save_state(state: dict) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, indent=2))


# ── HTTP helper ───────────────────────────────────────────────────────────────

def _post(path: str, payload: dict, api_key: str, timeout: int = 15) -> dict:
    url = INGEST_URL.rstrip("/") + path
    body = json.dumps(payload).encode()
    req = urllib.request.Request(
        url, data=body,
        headers={"Content-Type": "application/json", "X-Api-Key": api_key},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"HTTP {e.code} from {url}: {e.read().decode()[:200]}")


# ── Key validation ────────────────────────────────────────────────────────────

def validate_key(api_key: str) -> dict:
    """Validate cm_ key against ingest.clawmetry.com/auth. Returns {node_id, user}."""
    return _post("/auth", {"api_key": api_key}, api_key)


# ── Path detection (mirrors dashboard.py logic) ───────────────────────────────

def detect_paths() -> dict:
    home = Path.home()
    candidates = [
        home / ".openclaw" / "agents" / "main" / "sessions",
        Path("/data/agents/main/sessions"),   # Docker
        Path("/app/agents/main/sessions"),
    ]
    sessions_dir = next((str(p) for p in candidates if p.exists()), str(candidates[0]))

    log_candidates = [
        Path("/tmp/openclaw"),
        home / ".openclaw" / "logs",
        Path("/data/logs"),
    ]
    log_dir = next((str(p) for p in log_candidates if p.exists()), "/tmp/openclaw")

    workspace_candidates = [
        home / ".openclaw" / "workspace",
        Path("/data/workspace"),
    ]
    workspace = next((str(p) for p in workspace_candidates if p.exists()), str(home / ".openclaw" / "workspace"))

    return {"sessions_dir": sessions_dir, "log_dir": log_dir, "workspace": workspace}


# ── Sync: session events ──────────────────────────────────────────────────────

def sync_sessions(config: dict, state: dict, paths: dict) -> int:
    sessions_dir = paths["sessions_dir"]
    api_key = config["api_key"]
    node_id = config["node_id"]
    last_ids: dict = state.setdefault("last_event_ids", {})
    total = 0

    jsonl_files = sorted(glob.glob(os.path.join(sessions_dir, "*.jsonl")))
    for fpath in jsonl_files:
        fname = os.path.basename(fpath)
        last_line = last_ids.get(fname, 0)
        events = []
        try:
            with open(fpath, "r", errors="replace") as f:
                for i, raw in enumerate(f):
                    if i < last_line:
                        continue
                    raw = raw.strip()
                    if not raw:
                        continue
                    try:
                        obj = json.loads(raw)
                    except Exception:
                        continue
                    # Anonymise: keep structure, drop raw text content for privacy
                    events.append({
                        "session_file": fname,
                        "line": i,
                        "role": obj.get("role", ""),
                        "type": obj.get("type", ""),
                        "timestamp": obj.get("timestamp") or obj.get("time", ""),
                        "tool_name": _extract_tool_name(obj),
                        "node_id": node_id,
                    })
                    if len(events) >= BATCH_SIZE:
                        _post("/ingest/events", {"events": events, "node_id": node_id}, api_key)
                        total += len(events)
                        last_ids[fname] = i + 1
                        events = []
            if events:
                _post("/ingest/events", {"events": events, "node_id": node_id}, api_key)
                total += len(events)
                last_ids[fname] = last_line + len(events)
        except Exception as e:
            log.warning(f"Session sync error ({fname}): {e}")

    return total


def _extract_tool_name(obj: dict) -> str:
    content = obj.get("content", [])
    if isinstance(content, list):
        for block in content:
            if isinstance(block, dict) and block.get("type") in ("tool_use", "toolCall"):
                return block.get("name", "")
    return ""


# ── Sync: log lines ───────────────────────────────────────────────────────────

def sync_logs(config: dict, state: dict, paths: dict) -> int:
    log_dir = paths["log_dir"]
    api_key = config["api_key"]
    node_id = config["node_id"]
    offsets: dict = state.setdefault("last_log_offsets", {})
    total = 0

    log_files = sorted(glob.glob(os.path.join(log_dir, "openclaw-*.log")))[-3:]
    for fpath in log_files:
        fname = os.path.basename(fpath)
        offset = offsets.get(fname, 0)
        entries = []
        try:
            with open(fpath, "r", errors="replace") as f:
                f.seek(0, 2)
                size = f.tell()
                if offset > size:
                    offset = 0
                f.seek(offset)
                for raw in f:
                    raw = raw.strip()
                    if not raw:
                        continue
                    try:
                        obj = json.loads(raw)
                    except Exception:
                        continue
                    entries.append({
                        "ts": obj.get("time") or obj.get("timestamp", ""),
                        "level": obj.get("level", "info"),
                        "node_id": node_id,
                    })
                    if len(entries) >= BATCH_SIZE:
                        _post("/ingest/logs", {"logs": entries, "node_id": node_id}, api_key)
                        total += len(entries)
                        entries = []
                offsets[fname] = f.tell()
            if entries:
                _post("/ingest/logs", {"logs": entries, "node_id": node_id}, api_key)
                total += len(entries)
        except Exception as e:
            log.warning(f"Log sync error ({fname}): {e}")

    return total


# ── Heartbeat ─────────────────────────────────────────────────────────────────

def send_heartbeat(config: dict, paths: dict) -> None:
    try:
        _post("/ingest/heartbeat", {
            "node_id": config["node_id"],
            "ts": datetime.now(timezone.utc).isoformat(),
            "platform": platform.system(),
            "version": _get_version(),
        }, config["api_key"])
    except Exception as e:
        log.debug(f"Heartbeat failed: {e}")


def _get_version() -> str:
    try:
        import re
        root = Path(__file__).parent.parent
        src = (root / "dashboard.py").read_text(errors="replace")
        m = re.search(r'^__version__\s*=\s*["\'](.+?)["\']', src, re.M)
        return m.group(1) if m else "unknown"
    except Exception:
        return "unknown"


# ── Main daemon loop ──────────────────────────────────────────────────────────

def run_daemon() -> None:
    config = load_config()
    paths  = detect_paths()
    log.info(f"Starting sync daemon — node_id={config['node_id']} → {INGEST_URL}")
    log.info(f"Sessions: {paths['sessions_dir']}")
    log.info(f"Logs:     {paths['log_dir']}")

    heartbeat_interval = 60  # seconds
    last_heartbeat = 0.0

    while True:
        try:
            state = load_state()
            ev = sync_sessions(config, state, paths)
            lg = sync_logs(config, state, paths)
            state["last_sync"] = datetime.now(timezone.utc).isoformat()
            save_state(state)
            if ev or lg:
                log.info(f"Synced {ev} events, {lg} log lines")

            now = time.time()
            if now - last_heartbeat > heartbeat_interval:
                send_heartbeat(config, paths)
                last_heartbeat = now

        except Exception as e:
            log.error(f"Sync cycle error: {e}")

        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    run_daemon()
