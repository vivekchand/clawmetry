"""
clawmetry/sync.py — Cloud sync daemon for clawmetry connect.

Reads local OpenClaw sessions/logs, encrypts with AES-256-GCM (E2E),
and streams to ingest.clawmetry.com. The encryption key never leaves
the local machine — cloud stores ciphertext only.
"""
from __future__ import annotations
import json
import os
import sys
import time
import glob
import base64
import secrets
import logging
import platform
import urllib.request
import urllib.error
from pathlib import Path
from datetime import datetime, timezone

INGEST_URL = os.environ.get("CLAWMETRY_INGEST_URL", "https://ingest.clawmetry.com")
CONFIG_DIR  = Path.home() / ".clawmetry"
CONFIG_FILE = CONFIG_DIR / "config.json"
STATE_FILE  = CONFIG_DIR / "sync-state.json"
LOG_FILE    = CONFIG_DIR / "sync.log"

POLL_INTERVAL = 15    # seconds between sync cycles
BATCH_SIZE    = 50    # events per encrypted POST

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [clawmetry-sync] %(levelname)s %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(str(LOG_FILE), encoding="utf-8"),
    ],
)
log = logging.getLogger("clawmetry.sync")


# ── Encryption (AES-256-GCM) ─────────────────────────────────────────────────

def generate_encryption_key() -> str:
    """Generate a new 256-bit key. Returns base64url string."""
    return base64.urlsafe_b64encode(secrets.token_bytes(32)).decode()


def _get_aesgcm(key_b64: str):
    """Return an AESGCM cipher from a base64url key."""
    try:
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
        raw = base64.urlsafe_b64decode(key_b64 + "==")
        return AESGCM(raw)
    except ImportError:
        raise RuntimeError(
            "E2E encryption requires the 'cryptography' package.\n"
            "  pip install cryptography"
        )


def encrypt_payload(data: dict, key_b64: str) -> str:
    """
    Encrypt a dict as AES-256-GCM.
    Returns base64url(nonce || ciphertext) — a single opaque string.
    Cloud stores this blob and never sees plaintext.
    """
    cipher = _get_aesgcm(key_b64)
    nonce  = secrets.token_bytes(12)          # 96-bit nonce (GCM standard)
    plain  = json.dumps(data).encode()
    ct     = cipher.encrypt(nonce, plain, None)
    return base64.urlsafe_b64encode(nonce + ct).decode()


def decrypt_payload(blob: str, key_b64: str) -> dict:
    """Decrypt a blob produced by encrypt_payload. Used by clients."""
    cipher = _get_aesgcm(key_b64)
    raw    = base64.urlsafe_b64decode(blob + "==")
    nonce, ct = raw[:12], raw[12:]
    return json.loads(cipher.decrypt(nonce, ct, None))


# ── Config ─────────────────────────────────────────────────────────────────────

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


# ── HTTP ──────────────────────────────────────────────────────────────────────

def _post(path: str, payload: dict, api_key: str, timeout: int = 15) -> dict:
    url  = INGEST_URL.rstrip("/") + path
    body = json.dumps(payload).encode()
    req  = urllib.request.Request(
        url, data=body,
        headers={"Content-Type": "application/json", "X-Api-Key": api_key},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"HTTP {e.code} from {url}: {e.read().decode()[:200]}")


def validate_key(api_key: str) -> dict:
    return _post("/auth", {"api_key": api_key}, api_key)


# ── Path detection ─────────────────────────────────────────────────────────────

def detect_paths() -> dict:
    home = Path.home()
    sessions_candidates = [
        home / ".openclaw" / "agents" / "main" / "sessions",
        Path("/data/agents/main/sessions"),
        Path("/app/agents/main/sessions"),
    ]
    sessions_dir = next((str(p) for p in sessions_candidates if p.exists()),
                        str(sessions_candidates[0]))

    log_candidates = [Path("/tmp/openclaw"), home / ".openclaw" / "logs", Path("/data/logs")]
    log_dir = next((str(p) for p in log_candidates if p.exists()), "/tmp/openclaw")

    return {"sessions_dir": sessions_dir, "log_dir": log_dir}


# ── Sync: session events (full content, encrypted) ────────────────────────────

def sync_sessions(config: dict, state: dict, paths: dict) -> int:
    sessions_dir = paths["sessions_dir"]
    api_key      = config["api_key"]
    enc_key      = config.get("encryption_key")
    node_id      = config["node_id"]
    last_ids: dict = state.setdefault("last_event_ids", {})
    total = 0

    jsonl_files = sorted(glob.glob(os.path.join(sessions_dir, "*.jsonl")))
    for fpath in jsonl_files:
        fname    = os.path.basename(fpath)
        last_line = last_ids.get(fname, 0)
        batch: list[dict] = []

        try:
            with open(fpath, "r", errors="replace") as f:
                all_lines = f.readlines()

            new_lines = all_lines[last_line:]
            for i, raw in enumerate(new_lines, start=last_line):
                raw = raw.strip()
                if not raw:
                    continue
                try:
                    obj = json.loads(raw)
                except Exception:
                    continue

                # Full content — encrypted before leaving machine
                batch.append(obj)

                if len(batch) >= BATCH_SIZE:
                    _flush_session_batch(batch, fname, api_key, enc_key, node_id)
                    total += len(batch)
                    batch = []

            if batch:
                _flush_session_batch(batch, fname, api_key, enc_key, node_id)
                total += len(batch)

            last_ids[fname] = len(all_lines)

        except Exception as e:
            log.warning(f"Session sync error ({fname}): {e}")

    return total


def _flush_session_batch(batch: list, fname: str, api_key: str,
                          enc_key: str | None, node_id: str) -> None:
    payload = {"session_file": fname, "node_id": node_id, "events": batch}
    if enc_key:
        _post("/ingest/events", {
            "node_id": node_id,
            "encrypted": True,
            "blob": encrypt_payload(payload, enc_key),
        }, api_key)
    else:
        _post("/ingest/events", payload, api_key)


# ── Sync: logs (full lines, encrypted) ────────────────────────────────────────

def sync_logs(config: dict, state: dict, paths: dict) -> int:
    log_dir  = paths["log_dir"]
    api_key  = config["api_key"]
    enc_key  = config.get("encryption_key")
    node_id  = config["node_id"]
    offsets: dict = state.setdefault("last_log_offsets", {})
    total = 0

    log_files = sorted(glob.glob(os.path.join(log_dir, "openclaw-*.log")))[-5:]
    for fpath in log_files:
        fname  = os.path.basename(fpath)
        offset = offsets.get(fname, 0)
        entries: list[dict] = []

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
                        entries.append(json.loads(raw))
                    except Exception:
                        entries.append({"raw": raw})
                    if len(entries) >= BATCH_SIZE:
                        _flush_log_batch(entries, fname, api_key, enc_key, node_id)
                        total += len(entries)
                        entries = []
                offsets[fname] = f.tell()

            if entries:
                _flush_log_batch(entries, fname, api_key, enc_key, node_id)
                total += len(entries)

        except Exception as e:
            log.warning(f"Log sync error ({fname}): {e}")

    return total


def _flush_log_batch(entries: list, fname: str, api_key: str,
                      enc_key: str | None, node_id: str) -> None:
    payload = {"log_file": fname, "node_id": node_id, "lines": entries}
    if enc_key:
        _post("/ingest/logs", {
            "node_id": node_id,
            "encrypted": True,
            "blob": encrypt_payload(payload, enc_key),
        }, api_key)
    else:
        _post("/ingest/logs", payload, api_key)


# ── Heartbeat ─────────────────────────────────────────────────────────────────

def send_heartbeat(config: dict) -> None:
    try:
        _post("/ingest/heartbeat", {
            "node_id": config["node_id"],
            "ts": datetime.now(timezone.utc).isoformat(),
            "platform": platform.system(),
            "version": _get_version(),
            "e2e": bool(config.get("encryption_key")),
        }, config["api_key"])
    except Exception as e:
        log.debug(f"Heartbeat failed: {e}")


def _get_version() -> str:
    try:
        import re
        src = (Path(__file__).parent.parent / "dashboard.py").read_text(errors="replace")
        m = re.search(r'^__version__\s*=\s*["\'](.+?)["\']', src, re.M)
        return m.group(1) if m else "unknown"
    except Exception:
        return "unknown"


# ── Daemon loop ────────────────────────────────────────────────────────────────

def run_daemon() -> None:
    config = load_config()
    paths  = detect_paths()
    enc    = "🔒 E2E encrypted" if config.get("encryption_key") else "⚠️  unencrypted"
    log.info(f"Starting sync daemon — node={config['node_id']} → {INGEST_URL} ({enc})")

    heartbeat_interval = 60
    last_heartbeat = 0.0

    while True:
        try:
            state = load_state()
            ev = sync_sessions(config, state, paths)
            lg = sync_logs(config, state, paths)
            state["last_sync"] = datetime.now(timezone.utc).isoformat()
            save_state(state)
            if ev or lg:
                log.info(f"Synced {ev} events, {lg} log lines ({enc})")

            now = time.time()
            if now - last_heartbeat > heartbeat_interval:
                send_heartbeat(config)
                last_heartbeat = now

        except Exception as e:
            log.error(f"Sync cycle error: {e}")

        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    run_daemon()
