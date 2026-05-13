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
import threading
import subprocess
import urllib.request
import urllib.error
import uuid
from pathlib import Path
from datetime import datetime, timezone
from itertools import islice


def _get_openclaw_dir():
    """Return the OpenClaw config directory, respecting CLAWMETRY_OPENCLAW_DIR env var."""
    return os.environ.get("CLAWMETRY_OPENCLAW_DIR", os.path.expanduser("~/.openclaw"))


# ── Single-instance PID lock ──────────────────────────────────────────────────
def _pid_file() -> Path:
    return Path(os.path.expanduser("~/.clawmetry/sync.pid"))


def _acquire_pid_lock() -> bool:
    """Atomically claim the PID file. Return False if another instance is
    already running. Uses ``O_CREAT|O_EXCL`` to win the create race when
    two daemons start simultaneously — the previous ``exists()`` then
    ``write_text()`` pattern had a TOCTOU window where both processes
    could pass the check and both write their PIDs.

    Identified by @dumko2001 in #512.
    """
    pid_path = _pid_file()
    pid_path.parent.mkdir(parents=True, exist_ok=True)
    pid_str = str(os.getpid()).encode()
    while True:
        try:
            fd = os.open(str(pid_path), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            try:
                os.write(fd, pid_str)
            finally:
                os.close(fd)
            return True
        except FileExistsError:
            try:
                existing_pid = int(pid_path.read_text().strip())
            except (ValueError, OSError):
                try:
                    pid_path.unlink()
                except OSError:
                    return False
                continue
            try:
                os.kill(existing_pid, 0)
                return False
            except ProcessLookupError:
                try:
                    pid_path.unlink()
                except OSError:
                    pass
                continue


def _release_pid_lock() -> None:
    try:
        _pid_file().unlink(missing_ok=True)
    except Exception:
        pass


def _validate_log_offsets(state: dict, paths: dict) -> None:
    """Validate stored log offsets on startup.

    Prevents silent data gaps caused by log rotation or file truncation:
    after a restart the stored offset may be beyond the current file end, or
    the file may have shrunk and grown back past the offset (so offset < size
    but the bytes there are new content, not what was originally at that
    position).  We reset any offset >= current file size to 0 so the daemon
    re-reads from the start and catches up on missed events.
    """
    offsets = state.get("last_log_offsets", {})
    if not offsets:
        return
    log_dir = paths.get("log_dir", "")
    if not log_dir:
        return
    for fname in list(offsets.keys()):
        fpath = os.path.join(log_dir, fname)
        try:
            size = os.path.getsize(fpath)
            if offsets[fname] > size:
                log.warning(
                    f"Stale log offset for {fname}: stored={offsets[fname]}, "
                    f"file size={size}. Resetting to 0 to catch up on missed events."
                )
                offsets[fname] = 0
        except FileNotFoundError:
            log.warning(f"Log file {fname} gone — removing stale offset entry.")
            del offsets[fname]
        except Exception as e:
            log.warning(f"Could not validate offset for {fname}: {e}")


INGEST_URL = os.environ.get("CLAWMETRY_INGEST_URL", "https://ingest.clawmetry.com")
CONFIG_DIR = Path.home() / ".clawmetry"
CONFIG_FILE = CONFIG_DIR / "config.json"
STATE_FILE = CONFIG_DIR / "sync-state.json"
LOG_FILE = CONFIG_DIR / "sync.log"

POLL_INTERVAL = 15  # seconds between sync cycles
STREAM_INTERVAL = 2  # seconds between real-time stream pushes

# Adaptive heartbeat cadence (epic #775 — adaptive sync, PR 2/3).
# When a viewer has the cloud dashboard open, the cloud sets `viewer_active:
# true` on the heartbeat response and we tighten the loop so Telegram /
# tool / brain events appear in the cloud Brain tab in ~3s instead of up to
# 60s. When nobody is watching we drop back to the default 60s cadence to
# keep idle bandwidth + Cloud Run cost flat. Back-compat: a cloud that
# hasn't deployed PR 1 of the epic yet won't return the field, and the
# missing-field branch falls through to SLOW.
HEARTBEAT_INTERVAL_FAST = 3
HEARTBEAT_INTERVAL_SLOW = 60
BATCH_SIZE = (
    200  # events per encrypted POST (was 10; fewer HTTP requests = faster sync)
)
MAX_EVENTS_PER_CYCLE = (
    5000  # cap per sync cycle so initial sync doesn't block the main loop
)

CONFIG_DIR.mkdir(parents=True, exist_ok=True)
log = logging.getLogger("clawmetry-sync")
log.setLevel(logging.INFO)
if not log.handlers:
    _fmt = logging.Formatter("%(asctime)s [clawmetry-sync] %(levelname)s %(message)s")
    # Detect if stdout is already redirected to our log file (e.g. launchd).
    # In that case, only use StreamHandler to avoid duplicate lines.
    _stdout_is_log = False
    try:
        import os as _os

        if hasattr(sys.stdout, "fileno"):
            _stdout_is_log = (
                _os.path.samefile(
                    _os.fstat(sys.stdout.fileno()).st_ino
                    and f"/proc/self/fd/{sys.stdout.fileno()}"
                    or "",
                    str(LOG_FILE),
                )
                if _os.path.exists(str(LOG_FILE))
                else False
            )
    except Exception:
        try:
            _stdout_stat = _os.fstat(sys.stdout.fileno())
            _log_stat = _os.stat(str(LOG_FILE))
            _stdout_is_log = (
                _stdout_stat.st_dev == _log_stat.st_dev
                and _stdout_stat.st_ino == _log_stat.st_ino
            )
        except Exception:
            pass
    _sh = logging.StreamHandler(sys.stdout)
    _sh.setFormatter(_fmt)
    log.addHandler(_sh)
    if not _stdout_is_log:
        try:
            _fh = logging.FileHandler(str(LOG_FILE), encoding="utf-8")
            _fh.setFormatter(_fmt)
            log.addHandler(_fh)
        except Exception:
            pass
    log.propagate = False


# ── Daemon-error → DuckDB event handler (PRD #1133 layer 4, daemon side) ────
#
# Why: PR #1139 surfaced daemon errors on the System Health card by parsing
# ``~/.clawmetry/sync.log`` text on every /api/system-health call — a clear
# violation of the DuckDB-first rule (memory feedback_duckdb_first_rule.md).
# This handler tees every ERROR-level log line into a structured
# ``daemon.error`` event row in the local DuckDB so the read side can do a
# single indexed query instead of re-tailing the log on each request.
#
# Rate-limit: at most one row per (first-80-chars-of-message, 60s bucket).
# Important because the original ALERTS_EVAL_INTERVAL_SEC NameError fired
# 4×/min on every install, and we don't want that pattern to spam DuckDB
# 5,760 rows/day when one row/minute carries the same signal.
#
# Failure mode: any exception inside the handler is swallowed and counted —
# the daemon must never crash because telemetry plumbing broke.

import uuid as _uuid
import socket as _socket

_DAEMON_ERROR_AGENT_ID = "clawmetry-daemon"
_DAEMON_ERROR_AGENT_TYPE = "clawmetry"
_DAEMON_ERROR_EVENT_TYPE = "daemon.error"
_DAEMON_ERROR_DEDUP_PREFIX_LEN = 80
_DAEMON_ERROR_DEDUP_BUCKET_SEC = 60


class _DaemonErrorDuckDBHandler(logging.Handler):
    """Logging handler that mirrors ERROR records into DuckDB ``events``.

    One row per (message-prefix, 60-second-bucket) — repeated identical
    errors within the bucket are dropped so a 4×/min NameError doesn't
    flood the table. The cap is enforced in-memory; we don't query
    DuckDB to dedup (would defeat the point).
    """

    def __init__(self) -> None:
        super().__init__(level=logging.ERROR)
        # Map[prefix → last-emitted-bucket]. Single-process daemon, so a
        # plain dict guarded by a Lock is fine. Bounded eviction below
        # keeps memory flat under pathological churn.
        self._last_emit: dict[str, int] = {}
        self._lock = threading.Lock()
        self._dropped = 0
        self._emitted = 0
        self._node_id_cache: str | None = None

    def _node_id(self) -> str:
        if self._node_id_cache:
            return self._node_id_cache
        try:
            cfg = load_config()
            nid = cfg.get("node_id") or _socket.gethostname() or "unknown"
        except Exception:
            nid = _socket.gethostname() or "unknown"
        self._node_id_cache = str(nid)
        return self._node_id_cache

    def _should_emit(self, msg: str, now_ts: float) -> bool:
        """Return True iff this prefix hasn't been emitted in the current
        60-second bucket. Updates the bookkeeping atomically."""
        prefix = (msg or "")[:_DAEMON_ERROR_DEDUP_PREFIX_LEN]
        bucket = int(now_ts // _DAEMON_ERROR_DEDUP_BUCKET_SEC)
        with self._lock:
            last = self._last_emit.get(prefix)
            if last == bucket:
                self._dropped += 1
                return False
            self._last_emit[prefix] = bucket
            # Bounded eviction — keep the table from growing unbounded if
            # a misbehaving caller logs millions of unique error messages.
            if len(self._last_emit) > 1024:
                # Drop entries older than 2 buckets (~120s).
                stale_cutoff = bucket - 2
                for k in [k for k, v in self._last_emit.items() if v < stale_cutoff]:
                    del self._last_emit[k]
            return True

    def emit(self, record: logging.LogRecord) -> None:  # noqa: D401
        try:
            if record.levelno < logging.ERROR:
                return
            try:
                msg = record.getMessage()
            except Exception:
                msg = str(getattr(record, "msg", ""))
            now_ts = time.time()
            if not self._should_emit(msg, now_ts):
                return

            exc_str: str | None = None
            if record.exc_info:
                try:
                    exc_str = logging.Formatter().formatException(record.exc_info)
                except Exception:
                    exc_str = None

            from clawmetry import local_store as _ls
            store = _ls.get_store()
            event = {
                "id": _uuid.uuid4().hex,
                "agent_id": _DAEMON_ERROR_AGENT_ID,
                "agent_type": _DAEMON_ERROR_AGENT_TYPE,
                "node_id": self._node_id(),
                "event_type": _DAEMON_ERROR_EVENT_TYPE,
                "ts": datetime.now(timezone.utc).isoformat(),
                "data": {
                    "message": (msg or "")[:1000],
                    "exception": (exc_str or "")[:2000] if exc_str else None,
                    "logger": record.name,
                },
            }
            store.ingest(event)
            self._emitted += 1
        except Exception:
            # Never raise from a logging handler — would break the daemon's
            # own error logging.
            try:
                self._dropped += 1
            except Exception:
                pass


def install_daemon_error_event_handler(logger: logging.Logger | None = None) -> _DaemonErrorDuckDBHandler | None:
    """Attach the DuckDB-mirroring handler to the daemon logger.

    Idempotent: re-running won't add a second handler. Returns the handler
    instance (so tests can introspect ``_emitted`` / ``_dropped``) or None
    when installation fails — the daemon should keep running either way.
    """
    target = logger if logger is not None else log
    for h in target.handlers:
        if isinstance(h, _DaemonErrorDuckDBHandler):
            return h  # type: ignore[return-value]
    try:
        h = _DaemonErrorDuckDBHandler()
        target.addHandler(h)
        return h
    except Exception as e:  # pragma: no cover — defensive
        try:
            log.warning("install_daemon_error_event_handler failed: %s", e)
        except Exception:
            pass
        return None


# ── Encryption (AES-256-GCM) ─────────────────────────────────────────────────


def generate_encryption_key() -> str:
    """Generate a new 256-bit key. Returns base64url string."""
    return base64.urlsafe_b64encode(secrets.token_bytes(32)).decode()


def _normalize_encryption_key(key_str: str) -> str:
    """Ensure key is a valid base64url AES key. If not, derive one via SHA-256."""
    import hashlib as _hl_norm

    try:
        raw = base64.urlsafe_b64decode(key_str + "==")
        if len(raw) in (16, 24, 32):
            return key_str
    except Exception:
        pass
    derived = _hl_norm.sha256(key_str.encode()).digest()
    return base64.urlsafe_b64encode(derived).decode().rstrip("=")


def _get_aesgcm(key_b64: str):
    """Return an AESGCM cipher from a base64url key (auto-derives if passphrase)."""
    try:
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM

        key_b64 = _normalize_encryption_key(key_b64)
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
    nonce = secrets.token_bytes(12)  # 96-bit nonce (GCM standard)
    plain = json.dumps(data).encode()
    ct = cipher.encrypt(nonce, plain, None)
    return base64.urlsafe_b64encode(nonce + ct).decode()


def decrypt_payload(blob: str, key_b64: str) -> dict:
    """Decrypt a blob produced by encrypt_payload. Used by clients."""
    cipher = _get_aesgcm(key_b64)
    raw = base64.urlsafe_b64decode(blob + "==")
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


# ── Initial-sync progress (vivekchand/clawmetry#748) ─────────────────────────
# Tracks per-phase progress to ~/.clawmetry/sync_progress.json so the local
# dashboard can show a "syncing…" banner on fresh installs instead of empty
# tabs. Written atomically (tmp + rename) because the dashboard reads this
# file on every banner poll.
SYNC_PROGRESS_FILE = CONFIG_DIR / "sync_progress.json"
_sync_progress_started_at: str | None = None


def _record_sync_progress(
    phase: str, done: int, total: int = 0, status: str = "running"
) -> None:
    global _sync_progress_started_at
    try:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        now = datetime.now(timezone.utc).isoformat()
        if _sync_progress_started_at is None:
            _sync_progress_started_at = now
        try:
            cfg = load_config()
            node_id = cfg.get("node_id", "")
        except Exception:
            node_id = ""
        payload = {
            "node_id": node_id,
            "phase": phase,
            "done": int(done),
            "total": int(total),
            "status": status,
            "started_at": _sync_progress_started_at,
            "updated_at": now,
        }
        tmp = SYNC_PROGRESS_FILE.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(payload, indent=2))
        os.replace(tmp, SYNC_PROGRESS_FILE)
    except Exception as e:
        log.debug(f"Could not record sync progress ({phase}): {e}")


# ── HTTP ──────────────────────────────────────────────────────────────────────


def _post(path: str, payload: dict, api_key: str, timeout: int = 45) -> dict:
    url = INGEST_URL.rstrip("/") + path
    body = json.dumps(payload).encode()
    headers = {"Content-Type": "application/json", "X-Api-Key": api_key}
    if payload.get("node_id"):
        headers["X-Node-Id"] = payload["node_id"]
    req = urllib.request.Request(
        url,
        data=body,
        headers=headers,
        method="POST",
    )
    last_err = None
    for attempt in range(2):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                resp_body = json.loads(resp.read())
            # Cloud heartbeat (and any other endpoint) may attach the user's
            # plan / sync_allowed / trial_days_left / upgrade_url. We mirror
            # those into _TRIAL_STATE so subsequent uploads can self-throttle
            # before paying the network round-trip. Best-effort: missing
            # fields leave the cache untouched.
            if isinstance(resp_body, dict) and "sync_allowed" in resp_body:
                _update_trial_state(resp_body)
            return resp_body
        except urllib.error.HTTPError as e:
            code = e.code
            msg = e.read().decode()[:200]
            last_err = RuntimeError(f"HTTP {code} from {url}: {msg}")
            # Retry on 401/503 (cloud cold-start transient errors)
            if code in (401, 503) and attempt == 0:
                time.sleep(2)
                continue
            # Server-side throttle — surface a friendly "upgrade to resume"
            # message and remember we're paused so next call short-circuits.
            if code == 429:
                try:
                    plan = json.loads(msg).get("plan", "")
                except Exception:
                    plan = ""
                _update_trial_state({
                    "sync_allowed": False,
                    "plan": plan or "trial_expired",
                    "upgrade_url": "https://app.clawmetry.com/cloud",
                })
            raise last_err
    raise last_err


# ── Client-side trial gating ────────────────────────────────────────────────
# Cloud /ingest/heartbeat returns {plan, sync_allowed, trial_days_left,
# upgrade_url} on every beat. We cache it here so:
#   - Large blob uploads (events / snapshots / memory / sessions / logs /
#     autonomy) skip themselves when sync_allowed=False, saving bandwidth.
#   - Heartbeats and approvals/alerts polls KEEP firing so the daemon
#     detects the moment the user upgrades (sync_allowed flips True →
#     uploads resume automatically, no daemon restart needed).
#   - A clear "upgrade to resume" log line prints once per UTC day so the
#     user knows why their dashboard stopped updating.

_TRIAL_STATE = {
    "sync_allowed": True,    # default: assume allowed until cloud says otherwise
    "plan": None,
    "trial_days_left": None,
    "upgrade_url": "https://app.clawmetry.com/cloud",
    "last_log_day": "",     # YYYY-MM-DD of the last "sync paused" log
}


def _update_trial_state(resp: dict) -> None:
    """Mirror plan info from a cloud response into the local cache + log
    a one-line "upgrade to resume" message once per UTC day on transition."""
    prev_allowed = _TRIAL_STATE["sync_allowed"]
    new_allowed = bool(resp.get("sync_allowed", True))
    _TRIAL_STATE["sync_allowed"] = new_allowed
    if "plan" in resp:
        _TRIAL_STATE["plan"] = resp.get("plan")
    if "trial_days_left" in resp:
        _TRIAL_STATE["trial_days_left"] = resp.get("trial_days_left")
    if resp.get("upgrade_url"):
        _TRIAL_STATE["upgrade_url"] = resp["upgrade_url"]
    reason = (resp.get("reason") or "").strip()
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    if not new_allowed and _TRIAL_STATE["last_log_day"] != today:
        _TRIAL_STATE["last_log_day"] = today
        if reason == "intent_pending":
            # KiloClaw / similar auto-provisioned flows. The user hasn't
            # asked to view their dashboard yet, so we heartbeat (so the
            # cloud knows we're alive) but upload nothing else. The moment
            # they click "View Observability", the heartbeat response
            # flips and uploads resume — no daemon restart needed.
            log.info(
                "Cloud sync deferred — waiting for the user to open their "
                "dashboard. Heartbeats continue; no sessions / events / "
                "logs / memory will leave this machine until then."
            )
        else:
            log.warning(
                "⚠ Trial expired (plan=%s). Cloud sync paused — heartbeats "
                "continue so we detect the moment you upgrade. Upgrade to Pro at "
                "%s to resume event/session/memory sync.",
                _TRIAL_STATE["plan"], _TRIAL_STATE["upgrade_url"],
            )
    elif new_allowed and not prev_allowed:
        if reason == "intent_started" or _TRIAL_STATE.get("plan") in (None, "free", "trial"):
            log.info("✓ Cloud sync activated — uploads resumed.")
        else:
            log.info(
                "✓ Pro plan detected (plan=%s). Cloud sync resumed.",
                _TRIAL_STATE["plan"],
            )


def _sync_allowed() -> bool:
    """Gate for large blob uploads. Heartbeats + approvals/alerts polls
    bypass this — they MUST keep firing so we detect the upgrade (or, for
    KiloClaw-provisioned accounts, the moment the user clicks "View
    Observability" and the cloud flips reason='intent_pending' off)."""
    return _TRIAL_STATE.get("sync_allowed", True)


def get_machine_id() -> str:
    """Generate a stable hardware fingerprint for this machine."""
    import hashlib, platform

    mid = ""
    # macOS: IOPlatformUUID (stable across reboots/reinstalls)
    if platform.system() == "Darwin":
        try:
            import subprocess

            out = subprocess.check_output(
                ["ioreg", "-rd1", "-c", "IOPlatformExpertDevice"],
                timeout=5,
                stderr=subprocess.DEVNULL,
            ).decode()
            for line in out.splitlines():
                if "IOPlatformUUID" in line:
                    mid = line.split('"')[-2]
                    break
        except Exception:
            pass
    # Linux: /etc/machine-id
    if not mid:
        # In Docker containers, /etc/machine-id is identical across clones
        # Use cgroup inode as container-specific fallback
        if _is_running_in_container():
            try:
                import stat

                st = os.stat("/proc/1")
                mid = f"container-{st.st_ino}"
            except Exception:
                pass
        if not mid:
            for path in ["/etc/machine-id", "/var/lib/dbus/machine-id"]:
                try:
                    with open(path) as f:
                        mid = f.read().strip()
                        if mid:
                            break
                except Exception:
                    pass
    # Windows: WMIC
    if not mid and platform.system() == "Windows":
        try:
            import subprocess

            out = subprocess.check_output(
                ["wmic", "csproduct", "get", "uuid"],
                timeout=5,
                stderr=subprocess.DEVNULL,
            ).decode()
            lines = [
                l.strip() for l in out.splitlines() if l.strip() and l.strip() != "UUID"
            ]
            if lines:
                mid = lines[0]
        except Exception:
            pass
    # Fallback: MAC address (less stable but better than nothing)
    if not mid:
        import uuid as _uuid_mod

        mid = str(_uuid_mod.getnode())
    return hashlib.sha256(mid.encode()).hexdigest()[:32]


def validate_key(
    api_key: str, hostname: str = "", existing_node_id: str = "", **kwargs
) -> dict:
    payload = {"api_key": api_key}
    if hostname:
        payload["hostname"] = hostname
    if existing_node_id:
        payload["existing_node_id"] = existing_node_id
    payload["machine_id"] = get_machine_id()
    return _post("/auth", payload, api_key)


# ── Path detection ─────────────────────────────────────────────────────────────


def _find_openclaw_dirs(root, max_depth=4):
    """Search a directory tree for OpenClaw sessions and workspace dirs."""
    sessions_dir = None
    workspace_dir = None
    try:
        for dirpath, dirnames, filenames in os.walk(root):
            depth = dirpath.replace(root, "").count(os.sep)
            if depth > max_depth:
                dirnames.clear()
                continue
            # Skip noisy dirs
            base = os.path.basename(dirpath)
            if base in ("node_modules", ".git", "__pycache__", "venv", ".venv"):
                dirnames.clear()
                continue
            if dirpath.endswith(
                os.sep + "agents" + os.sep + "main" + os.sep + "sessions"
            ) or dirpath.endswith("/agents/main/sessions"):
                if not sessions_dir:
                    sessions_dir = dirpath
                    log.info(f"  Found sessions: {dirpath}")
            if os.path.basename(dirpath) == "workspace" and os.path.isfile(
                os.path.join(dirpath, "AGENTS.md")
            ):
                if not workspace_dir:
                    workspace_dir = dirpath
                    log.info(f"  Found workspace: {dirpath}")
            if sessions_dir and workspace_dir:
                break
    except PermissionError:
        pass
    return sessions_dir, workspace_dir


def _is_running_in_container() -> bool:
    """Detect whether ClawMetry itself is running inside a Docker/OpenShell container."""
    # Check for /.dockerenv (present in Docker containers)
    if os.path.exists("/.dockerenv"):
        return True
    # Check cgroup for container indicators
    try:
        with open("/proc/1/cgroup", "r") as f:
            cgroup = f.read()
        if any(
            k in cgroup
            for k in ("docker", "kubepods", "containerd", "lxc", "opencontainer")
        ):
            return True
    except Exception:
        pass
    return False


def _detect_nemoclaw() -> dict:
    """Detect NemoClaw (NVIDIA's OpenClaw wrapper) presence on the host.

    Returns a dict with fields:
      detected (bool), binary (str), version (str),
      sandbox_name (str), sandbox_status (str), sandbox_type (str),
      inference_provider (str), inference_model (str),
      security_sandbox_enabled (bool), security_network_policy (bool)
    """
    import subprocess, shutil

    result: dict = {"detected": False}

    # 1. Check for the nemoclaw binary
    nemo_bin = shutil.which("nemoclaw")
    if not nemo_bin:
        for candidate in [
            "/usr/local/bin/nemoclaw",
            "/opt/nemoclaw/bin/nemoclaw",
            "/usr/bin/nemoclaw",
        ]:
            if os.path.isfile(candidate):
                nemo_bin = candidate
                break

    if not nemo_bin:
        # Also accept NEMOCLAW_SANDBOX env as a hint even without binary
        if not os.environ.get("NEMOCLAW_SANDBOX"):
            return result

    result["detected"] = True
    result["binary"] = nemo_bin or "(env-only)"

    # 2. Get version
    if nemo_bin:
        try:
            ver = (
                subprocess.check_output(
                    [nemo_bin, "--version"], stderr=subprocess.DEVNULL, timeout=5
                )
                .decode()
                .strip()
            )
            result["version"] = ver
        except Exception:
            result["version"] = "unknown"

    # 3. Collect sandbox status via `nemoclaw status`
    sandbox_name = os.environ.get("NEMOCLAW_SANDBOX", "")
    result["sandbox_name"] = sandbox_name
    result["sandbox_type"] = "nemoclaw"
    result["security_sandbox_enabled"] = True
    result["security_network_policy"] = True

    if nemo_bin:
        try:
            status_out = subprocess.check_output(
                [nemo_bin, "status", "--json"]
                + ([sandbox_name] if sandbox_name else []),
                stderr=subprocess.DEVNULL,
                timeout=10,
            ).decode()
            import json as _j

            status_data = _j.loads(status_out)
            result["sandbox_status"] = status_data.get("status", "unknown")
            result["inference_provider"] = status_data.get("inferenceProvider", "")
            result["inference_model"] = status_data.get("inferenceModel", "")
            if not sandbox_name:
                result["sandbox_name"] = status_data.get("name", "")
        except Exception:
            result["sandbox_status"] = "unknown"
            result["inference_provider"] = ""
            result["inference_model"] = ""
    else:
        result["sandbox_status"] = "unknown"
        result["inference_provider"] = ""
        result["inference_model"] = ""

    # 4. Try `openshell sandbox list` as alternative discovery
    openshell_bin = _find_openshell_bin()
    if openshell_bin and not result.get("sandbox_name"):
        try:
            import json as _j

            sb_out = subprocess.check_output(
                [openshell_bin, "sandbox", "list", "--json"],
                stderr=subprocess.DEVNULL,
                timeout=10,
            ).decode()
            sandboxes = _j.loads(sb_out)
            for sb in sandboxes if isinstance(sandboxes, list) else []:
                if any(
                    k in (sb.get("image", "") + sb.get("name", "")).lower()
                    for k in ("openclaw", "clawd", "nemoclaw")
                ):
                    result["sandbox_name"] = sb.get("name", "")
                    result["sandbox_status"] = sb.get("status", "unknown")
                    break
        except Exception:
            pass

    return result


def _find_openshell_bin() -> str | None:
    """Find the openshell CLI binary."""
    import shutil

    for name in ("openshell", "openshell-cli"):
        p = shutil.which(name)
        if p:
            return p
    for candidate in [
        "/usr/local/bin/openshell",
        "/opt/openshell/bin/openshell",
        "/usr/bin/openshell",
    ]:
        if os.path.isfile(candidate):
            return candidate
    return None


def _detect_docker_openclaw() -> dict:
    """Auto-detect OpenClaw running in Docker and find its data paths on the host.

    Detects both standard OpenClaw containers and NemoClaw/OpenShell sandboxes
    (ghcr.io/nvidia/openshell-community/* images).
    """
    import subprocess, json as _json

    result = {}
    try:
        # Find containers with openclaw/clawd/nemoclaw/openshell/nvidia in name or image
        out = subprocess.run(
            [
                "docker",
                "ps",
                "--format",
                "{{.ID}}\t{{.Names}}\t{{.Image}}\t{{.Mounts}}",
            ],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if out.returncode != 0:
            return {}
        for line in out.stdout.strip().splitlines():
            parts = line.split("\t")
            if len(parts) < 3:
                continue
            cid, name, image = parts[0], parts[1], parts[2]
            if not any(
                k in (name + image).lower()
                for k in [
                    "openclaw",
                    "clawd",
                    "claw",
                    "nemoclaw",
                    "openshell",
                    "nvidia",
                ]
            ):
                continue

            # Determine runtime: nemoclaw/openshell vs plain docker
            is_nemoclaw = any(
                k in (name + image).lower() for k in ("nemoclaw", "openshell", "nvidia")
            )
            runtime_tag = "nemoclaw" if is_nemoclaw else "docker"
            log.info(f"Found {runtime_tag} container: {name} ({image}) id={cid}")

            # NemoClaw sessions live at /sandbox/.openclaw/ inside the container
            # Plain OpenClaw containers use /root/.openclaw or /data
            nemoclaw_paths = ["/sandbox/.openclaw", "/sandbox/agents/main/sessions"]
            standard_paths = ["/root/.openclaw", "/data", "/app"]
            preferred_paths = (
                (nemoclaw_paths + standard_paths) if is_nemoclaw else standard_paths
            )

            # Get volume mounts via docker inspect
            try:
                insp = subprocess.run(
                    ["docker", "inspect", "--format", "{{json .Mounts}}", cid],
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                mounts = (
                    _json.loads(insp.stdout.strip()) if insp.returncode == 0 else []
                )
                for m in mounts:
                    src = m.get("Source", "")
                    dst = m.get("Destination", "")
                    # Look for data/workspace/sessions mounts
                    if (
                        "agents" in dst
                        or "sessions" in dst
                        or "/data" == dst
                        or "openclaw" in dst.lower()
                        or "/sandbox" in dst
                    ):
                        log.info(f"  Mount: {src} -> {dst}")
                        if "sessions" in dst:
                            result["sessions_dir"] = src
                        elif "agents" in dst:
                            result["sessions_dir"] = os.path.join(
                                src, "main", "sessions"
                            )
                        elif dst in (
                            "/data",
                            "/app",
                            "/home",
                            "/root",
                            "/opt",
                            "/sandbox",
                        ):
                            # Search mount point for sessions + workspace (up to 3 levels deep)
                            _found_s, _found_w = _find_openclaw_dirs(src)
                            if _found_s:
                                result["sessions_dir"] = _found_s
                            if _found_w:
                                result["workspace"] = _found_w
                    if "workspace" in dst:
                        result["workspace"] = src
                    if "logs" in dst or "tmp" in dst:
                        result["log_dir"] = src
            except Exception as e:
                log.debug(f"Docker inspect error: {e}")
            # If no volume mounts found, try docker exec to find paths
            if not result:
                try:
                    for check_path in preferred_paths:
                        sessions_path = (
                            f"{check_path}/agents/main/sessions"
                            if not check_path.endswith("sessions")
                            else check_path
                        )
                        chk = subprocess.run(
                            ["docker", "exec", cid, "ls", sessions_path],
                            capture_output=True,
                            text=True,
                            timeout=5,
                        )
                        if chk.returncode == 0 and chk.stdout.strip():
                            log.info(
                                f"  Found sessions inside container at {check_path}"
                            )
                            # Copy files out to host
                            mirror_subdir = (
                                "nemoclaw-mirror" if is_nemoclaw else "docker-mirror"
                            )
                            host_dir = Path.home() / ".clawmetry" / mirror_subdir
                            host_dir.mkdir(parents=True, exist_ok=True)
                            sessions_mirror = host_dir / "sessions"
                            workspace_mirror = host_dir / "workspace"
                            sessions_mirror.mkdir(exist_ok=True)
                            workspace_mirror.mkdir(exist_ok=True)
                            # rsync from container
                            subprocess.run(
                                [
                                    "docker",
                                    "cp",
                                    f"{cid}:{sessions_path}/.",
                                    str(sessions_mirror),
                                ],
                                capture_output=True,
                                timeout=30,
                            )
                            workspace_root = (
                                check_path
                                if check_path.endswith(".openclaw")
                                else os.path.dirname(check_path)
                            )
                            subprocess.run(
                                [
                                    "docker",
                                    "cp",
                                    f"{cid}:{workspace_root}/workspace/.",
                                    str(workspace_mirror),
                                ],
                                capture_output=True,
                                timeout=30,
                            )
                            # Copy logs
                            for log_path in ["/tmp/openclaw", f"{check_path}/logs"]:
                                subprocess.run(
                                    [
                                        "docker",
                                        "cp",
                                        f"{cid}:{log_path}/.",
                                        str(host_dir / "logs"),
                                    ],
                                    capture_output=True,
                                    timeout=15,
                                )
                            result["sessions_dir"] = str(sessions_mirror)
                            result["workspace"] = str(workspace_mirror)
                            result["log_dir"] = str(host_dir / "logs")
                            result["docker_container"] = cid
                            result["docker_path"] = check_path
                            result["container_id"] = cid
                            result["runtime"] = runtime_tag
                            log.info(f"  Mirrored {runtime_tag} data to {host_dir}")
                            break
                except Exception as e:
                    log.debug(f"Docker exec fallback error: {e}")
            if result:
                return result
    except FileNotFoundError:
        log.debug("Docker not installed or not in PATH")
    except Exception as e:
        log.debug(f"Docker detection error: {e}")
    return {}


def detect_paths() -> dict:
    Path.home()
    # Try Docker/NemoClaw container detection first
    docker_paths = _detect_docker_openclaw()
    if docker_paths.get("sessions_dir"):
        log.info(f"Using container-detected paths: {docker_paths}")

    sessions_candidates = [
        Path(_get_openclaw_dir()) / "agents" / "main" / "sessions",
        Path("/data/agents/main/sessions"),
        Path("/app/agents/main/sessions"),
        Path("/root/.openclaw/agents/main/sessions"),
        Path("/opt/openclaw/agents/main/sessions"),
        # NemoClaw/OpenShell sandbox paths (sessions live inside /sandbox)
        Path("/sandbox/.openclaw/agents/main/sessions"),
        Path("/sandbox/agents/main/sessions"),
    ]
    oc_home = os.environ.get("OPENCLAW_HOME", "")
    if oc_home:
        sessions_candidates.insert(0, Path(oc_home) / "agents" / "main" / "sessions")
    # Support explicit NemoClaw sandbox name via env var
    nemoclaw_sandbox = os.environ.get("NEMOCLAW_SANDBOX", "")
    if nemoclaw_sandbox:
        sessions_candidates.insert(
            0, Path(f"/sandbox/{nemoclaw_sandbox}/.openclaw/agents/main/sessions")
        )
        sessions_candidates.insert(
            1,
            Path(
                f"/var/lib/openshell/sandboxes/{nemoclaw_sandbox}/.openclaw/agents/main/sessions"
            ),
        )
    def _safe_exists(p):
        try:
            return p.exists()
        except (PermissionError, OSError):
            return False

    found_sessions = docker_paths.get("sessions_dir") or next(
        (str(p) for p in sessions_candidates if _safe_exists(p)), None
    )
    sessions_dir = found_sessions or str(sessions_candidates[0])

    if not found_sessions:
        log.warning("OpenClaw not detected — no session directories found.")
        log.warning("  Install: npm install -g openclaw  (https://openclaw.ai/docs)")
        log.warning("  Daemon will keep retrying every 60s.")
    else:
        # Warn if NemoClaw is detected and sync daemon appears to be inside the sandbox
        if _is_running_in_container():
            log.warning(
                "⚠️  NemoClaw/container detected: ClawMetry sync daemon appears to be running INSIDE the sandbox."
            )
            log.warning(
                "   Recommended: run the sync daemon on the HOST for unrestricted network access."
            )
            log.warning(
                "   If you must run inside the sandbox, add this to your NemoClaw network policy:"
            )
            log.warning("     network:")
            log.warning("       egress:")
            log.warning("         - host: ingest.clawmetry.com")
            log.warning("           port: 443")
            log.warning("           protocol: https")

    log_candidates = [
        Path("/tmp/openclaw"),
        Path(_get_openclaw_dir()) / "logs",
        Path("/data/logs"),
    ]
    log_dir = docker_paths.get("log_dir") or next(
        (str(p) for p in log_candidates if p.exists()), "/tmp/openclaw"
    )

    workspace_candidates = [
        Path(_get_openclaw_dir()) / "workspace",
        Path("/data/workspace"),
        Path("/app/workspace"),
    ]
    workspace = docker_paths.get("workspace") or next(
        (str(p) for p in workspace_candidates if p.exists()),
        str(workspace_candidates[0]),
    )

    log.info(f"Paths: sessions={sessions_dir} logs={log_dir} workspace={workspace}")
    return {"sessions_dir": sessions_dir, "log_dir": log_dir, "workspace": workspace}


def discover_workspaces(home: Path | None = None) -> list[dict]:
    """Discover all OpenClaw workspace profiles on this machine.

    Power users sometimes keep multiple OpenClaw workspaces (work / personal /
    experiments). Today ClawMetry auto-detects a single ``~/.openclaw`` dir;
    this helper scans for the common multi-profile patterns so the dashboard
    can offer a switcher.

    Discovery paths (all safe, no symlink-following, read-only):
      1. ``~/.openclaw`` — the canonical single-workspace location.
      2. ``~/.openclaw-*`` — suffix-style profiles (e.g. ``~/.openclaw-work``).
      3. ``~/.openclaw/profiles/<name>`` — explicit profiles convention.
      4. ``~/.clawmetry/workspaces.json`` — user-curated list (highest trust).

    A path is treated as a workspace when it contains an ``agents/`` or
    ``workspace/`` subdir or one of the conventional context files
    (``SOUL.md`` / ``AGENTS.md`` / ``MEMORY.md``). The check tolerates
    ``PermissionError`` and never crashes.

    Returns a list of ``{name, path, agent_count, last_active_ts}`` dicts,
    sorted by ``last_active_ts`` desc. The single-workspace zero-config
    case still works — it just returns a one-element list.
    """
    home = home or Path.home()
    discovered: dict[str, dict] = {}  # path -> entry (de-dup by abs path)

    def _is_workspace_like(p: Path) -> bool:
        try:
            if not p.is_dir() or p.is_symlink():
                return False
            # Strong signal: agents/ subdir (OpenClaw's standard layout)
            if (p / "agents").is_dir():
                return True
            if (p / "workspace").is_dir():
                return True
            for marker in ("SOUL.md", "AGENTS.md", "MEMORY.md"):
                if (p / marker).exists():
                    return True
        except (PermissionError, OSError):
            return False
        return False

    def _agent_count(p: Path) -> int:
        try:
            agents_dir = p / "agents"
            if not agents_dir.is_dir():
                return 0
            return sum(
                1
                for child in agents_dir.iterdir()
                if child.is_dir() and not child.is_symlink()
            )
        except (PermissionError, OSError):
            return 0

    def _last_active(p: Path) -> float:
        """Most-recent mtime across sessions/logs as a rough activity timestamp."""
        latest = 0.0
        try:
            sessions = p / "agents" / "main" / "sessions"
            if sessions.is_dir():
                for f in sessions.iterdir():
                    if f.is_symlink():
                        continue
                    try:
                        m = f.stat().st_mtime
                        if m > latest:
                            latest = m
                    except (PermissionError, OSError):
                        continue
            # Fallback: dir mtime
            if latest == 0.0:
                latest = p.stat().st_mtime
        except (PermissionError, OSError):
            pass
        return latest

    def _add(name: str, path: Path) -> None:
        try:
            abs_path = path.resolve(strict=False)
        except (OSError, RuntimeError):
            abs_path = path
        key = str(abs_path)
        if key in discovered:
            return
        if not _is_workspace_like(path):
            return
        discovered[key] = {
            "name": name,
            "path": key,
            "agent_count": _agent_count(path),
            "last_active_ts": _last_active(path),
        }

    # 1. Canonical ~/.openclaw
    default = home / ".openclaw"
    _add("default", default)

    # 2. Suffix-style profiles: ~/.openclaw-<name>
    try:
        for entry in home.iterdir():
            try:
                if entry.is_symlink() or not entry.is_dir():
                    continue
            except (PermissionError, OSError):
                continue
            name = entry.name
            if not name.startswith(".openclaw-"):
                continue
            profile = name[len(".openclaw-"):]
            if profile:
                _add(profile, entry)
    except (PermissionError, OSError, FileNotFoundError):
        pass

    # 3. ~/.openclaw/profiles/<name> convention
    profiles_dir = default / "profiles"
    try:
        if profiles_dir.is_dir() and not profiles_dir.is_symlink():
            for entry in profiles_dir.iterdir():
                try:
                    if entry.is_symlink() or not entry.is_dir():
                        continue
                except (PermissionError, OSError):
                    continue
                _add(entry.name, entry)
    except (PermissionError, OSError):
        pass

    # 4. User-curated ~/.clawmetry/workspaces.json
    cfg_path = home / ".clawmetry" / "workspaces.json"
    try:
        if cfg_path.is_file() and not cfg_path.is_symlink():
            with open(cfg_path) as f:
                cfg = json.load(f)
            entries = cfg.get("workspaces") if isinstance(cfg, dict) else cfg
            if isinstance(entries, list):
                for item in entries:
                    if not isinstance(item, dict):
                        continue
                    raw_path = item.get("path")
                    name = item.get("name") or ""
                    if not raw_path or not isinstance(raw_path, str):
                        continue
                    p = Path(os.path.expanduser(raw_path))
                    # Stay within the user's home dir as a safety boundary
                    # (don't follow paths outside ~ that the JSON might point at).
                    try:
                        rp = p.resolve(strict=False)
                    except (OSError, RuntimeError):
                        continue
                    try:
                        rp.relative_to(home.resolve(strict=False))
                    except ValueError:
                        # Allow explicit absolute paths outside home only when
                        # they exist & are not symlinks — power-user override.
                        if p.is_symlink():
                            continue
                    _add(name or p.name or "workspace", p)
    except (PermissionError, OSError, json.JSONDecodeError, ValueError):
        pass

    out = sorted(
        discovered.values(),
        key=lambda d: d.get("last_active_ts", 0.0),
        reverse=True,
    )
    return out


# ── Sync: session events (full content, encrypted) ────────────────────────────


def _list_session_jsonls(sessions_dir) -> list[str]:
    """Return all session transcript paths in sessions_dir.

    Includes both live `*.jsonl` and archived `*.jsonl.reset.<ts>` files.
    OpenClaw renames a session jsonl with a `.reset.<iso-ts>` suffix when
    the session is reset; the archive still holds real token usage and
    transcript content. Filtering by `endswith('.jsonl')` alone (the old
    behaviour) silently dropped every archived day's data from cloud,
    making the per-day Tokens chart pile every session onto today.
    """
    sessions_dir = str(sessions_dir)
    out: list[str] = []
    try:
        for fname in os.listdir(sessions_dir):
            if fname.endswith(".jsonl") or ".jsonl.reset." in fname:
                # Skip OpenClaw trace-artifact sidecars that live next to
                # real session files. Without this filter the daemon
                # ingests <sid>.trajectory.jsonl etc., and
                # _canonical_session_file() splits at the first `.jsonl`
                # producing phantom session_ids like '<uuid>.trajectory'
                # that pollute DuckDB and downstream APIs. The dashboard
                # read-path applies the same exclusion (dashboard.py,
                # routes/sessions.py, routes/brain.py, routes/usage.py).
                if (
                    ".trajectory." in fname
                    or ".checkpoint." in fname
                    or ".deleted." in fname
                ):
                    continue
                out.append(os.path.join(sessions_dir, fname))
    except OSError:
        pass
    return out


def _canonical_session_file(name: str) -> str:
    """Return the canonical `<session_id>.jsonl` form for a session path.

    `name` may be a basename (`<uuid>.jsonl` or `<uuid>.jsonl.reset.<ts>`)
    or a full path. Cloud keys session rows on this string -- for an
    archived reset, we want events to land under the same session_id as
    the original live session, not a per-archive ghost row.
    """
    base = os.path.basename(name)
    sid = base.split(".jsonl", 1)[0]
    return sid + ".jsonl"


def sync_sessions(config: dict, state: dict, paths: dict) -> int:
    # Skipped when sync is paused (expired trial). The state dict still
    # tracks last_event_ids so when the user upgrades, we resume from
    # exactly where we paused -- no event loss, no double-send.
    if not _sync_allowed():
        return 0
    _record_sync_progress("sessions", 0)
    sessions_dir = paths["sessions_dir"]
    api_key = config["api_key"]
    enc_key = config.get("encryption_key")
    node_id = config["node_id"]
    last_ids: dict = state.setdefault("last_event_ids", {})
    total = 0

    # Build file-basename → subagent_id map from sessions.json index.
    # Each sub-agent session has a *different* UUID as its key vs. its .jsonl filename.
    # Without this mapping the cloud UI cannot correlate blobs → sub-agent sessions.
    file_to_subagent_id: dict[str, str] = {}
    index_path = os.path.join(sessions_dir, "sessions.json")
    if os.path.isfile(index_path):
        try:
            with open(index_path) as _fi:
                _idx = json.load(_fi)
            for _k, _meta in _idx.items():
                if ":subagent:" in _k and isinstance(_meta, dict):
                    _sf = _meta.get("sessionFile", "")
                    if _sf:
                        _fn = os.path.basename(_sf)  # e.g. "00b5b41b-…jsonl"
                        file_to_subagent_id[_fn] = _k.split(":")[
                            -1
                        ]  # e.g. "317db68b-…"
        except Exception:
            pass

    jsonl_files = _list_session_jsonls(sessions_dir)
    # Sort newest-first so recent sessions sync before old ones
    jsonl_files.sort(key=lambda p: os.path.getmtime(p), reverse=True)

    for fpath in jsonl_files:
        if total >= MAX_EVENTS_PER_CYCLE:
            break  # continue next cycle; progress is saved per-file

        fname = os.path.basename(fpath)
        # Cloud keys session rows on the canonical `<uuid>.jsonl`. For an
        # archived `<uuid>.jsonl.reset.<ts>` we want events to land under
        # the same session row, not spawn a per-archive ghost.
        cloud_fname = _canonical_session_file(fname)
        last_line = last_ids.get(fname, 0)
        batch: list[dict] = []
        subagent_id = file_to_subagent_id.get(cloud_fname) or file_to_subagent_id.get(fname)

        try:
            with open(fpath, "r", errors="replace") as f:
                new_lines = list(islice(f, last_line, None))

            line_cursor = last_line
            for i, raw in enumerate(new_lines, start=last_line):
                raw = raw.strip()
                if not raw:
                    line_cursor = i + 1
                    continue
                try:
                    obj = json.loads(raw)
                except Exception:
                    line_cursor = i + 1
                    continue

                # Full content — encrypted before leaving machine
                batch.append(obj)
                line_cursor = i + 1

                if len(batch) >= BATCH_SIZE:
                    _flush_session_batch(
                        batch, cloud_fname, api_key, enc_key, node_id, subagent_id
                    )
                    total += len(batch)
                    batch = []
                    # Save progress after each batch so restarts don't re-upload
                    last_ids[fname] = line_cursor
                    if total >= MAX_EVENTS_PER_CYCLE:
                        break

            if batch:
                _flush_session_batch(
                    batch, cloud_fname, api_key, enc_key, node_id, subagent_id
                )
                total += len(batch)

            # line_cursor tracks our furthest position in the file (inclusive
            # of lines we skipped as blank/malformed), so it is always the
            # correct "next start offset". The previous `len(all_lines)` ref
            # was stale from a pre-islice implementation that read the whole
            # file — it raised NameError on every call, spamming warnings
            # and preventing the cursor from advancing past the last BATCH_SIZE
            # flush.
            last_ids[fname] = line_cursor

        except Exception as e:
            log.warning(f"Session sync error ({fname}): {e}")

    _record_sync_progress("sessions", total, total)
    return total


def _flush_session_batch(
    batch: list,
    fname: str,
    api_key: str,
    enc_key: str | None,
    node_id: str,
    subagent_id: str | None = None,
) -> None:
    # Write-through to local SQLite first (epic #964 / phase 1 / issue #958).
    # Local is the durable store; cloud is a hot cache. If the cloud POST fails
    # below, the events are still recorded locally and the dashboard's local
    # read paths will surface them. Failures here never block cloud sync — the
    # broad except keeps the legacy behaviour intact for users who somehow
    # land on a corrupt SQLite or a read-only ~/.clawmetry/.
    try:
        _local_ingest_session_batch(batch, fname, node_id, subagent_id)
    except Exception as _e:
        log.warning("local-store ingest failed (cloud sync continues): %s", _e)

    payload = {"session_file": fname, "node_id": node_id, "events": batch}
    # Include subagent_id so the cloud can correlate blobs → sub-agent sessions.
    # The session key UUID (subagent_id) differs from the .jsonl filename UUID.
    if subagent_id:
        payload["subagent_id"] = subagent_id
    if enc_key:
        _post(
            "/ingest/events",
            {
                "node_id": node_id,
                "encrypted": True,
                "blob": encrypt_payload(payload, enc_key),
            },
            api_key,
        )
    else:
        _post("/ingest/events", payload, api_key)


def _extract_cost_tokens_model(obj: dict) -> tuple:
    """Pull (cost_usd, token_count, model) out of a raw OpenClaw transcript event.

    Real OpenClaw events nest these under ``obj["message"]["usage"]``:

        {
          "type": "message",
          "message": {
            "model": "claude-opus-4-7",
            "usage": {
              "totalTokens": 162,
              "cost": {"total": 0.00495, ...}
            }
          }
        }

    Older / synthesised events sometimes carry top-level ``cost_usd`` /
    ``tokens`` / ``model``. We accept either shape so tests, sub-agent
    adapters, and the real OpenClaw harness all populate the columns
    (previously the nested shape silently became NULL — see MOAT_E2E_REPORT
    2026-05-13 root-cause #4)."""
    cost_usd = obj.get("cost_usd")
    if cost_usd is None:
        cost_usd = obj.get("costUsd")
    token_count = obj.get("token_count")
    if token_count is None:
        token_count = obj.get("tokens")
    model = obj.get("model")

    msg = obj.get("message")
    if isinstance(msg, dict):
        if model is None:
            model = msg.get("model")
        usage = msg.get("usage")
        if isinstance(usage, dict):
            if token_count is None:
                tt = usage.get("totalTokens")
                if tt is None:
                    tt = usage.get("total_tokens")
                if tt is not None:
                    try:
                        token_count = int(tt)
                    except (TypeError, ValueError):
                        token_count = None
            if cost_usd is None:
                cost = usage.get("cost")
                if isinstance(cost, dict):
                    cv = cost.get("total")
                    if cv is None:
                        cv = cost.get("total_usd")
                else:
                    cv = cost  # rare: cost itself is a number
                if cv is not None:
                    try:
                        cost_usd = float(cv)
                    except (TypeError, ValueError):
                        cost_usd = None
    return cost_usd, token_count, model


def _extract_channel_message(
    obj: dict,
    *,
    session_id: str,
) -> dict | None:
    """Best-effort projection of a transcript event into a
    ``channel_messages`` row.

    Issue #1088 Phase 4. Returns ``None`` when the event is not a chat
    message OR carries no recoverable channel signal — the daemon then
    just records the event in ``events`` and moves on.

    Two recognition paths:

    1. **Inbound** — a ``user``-role message whose text starts with one of
       the known adapter wrappers (e.g. ``[Telegram Alice id:123]…``,
       ``[iMessage +14155551234]…``). The Connector layer prefixes every
       inbound channel message with this bracket-tag so downstream
       routing / observability can attribute it without scanning the
       gateway log. We mirror that parser here so the local DuckDB has a
       single canonical row per inbound message — the same key the
       dashboard uses for dedupe.
    2. **Outbound** — an ``assistant``-role message in a session whose
       session_id was previously seen carrying an inbound channel
       message. The session_id is the join key so we don't have to
       re-parse the session metadata blob — the inbound path stamps
       the channel and chat-id on a sentinel row this code reads
       opportunistically (a future PR can plumb the session→channel
       index more directly).

    The shape is intentionally narrow: ``provider``, ``channel_id``,
    ``sender_*``, ``body``, ``ts``, ``direction``. Per-provider extras
    (attachments, reactions, message_id) ride along in ``raw_blob`` so
    we don't widen the schema for adapter-specific fields.
    """
    import re as _re
    if not isinstance(obj, dict):
        return None
    if obj.get("type") != "message":
        return None
    msg = obj.get("message")
    if not isinstance(msg, dict):
        return None
    role = msg.get("role")
    if role not in ("user", "assistant"):
        return None
    content = msg.get("content")
    text = ""
    if isinstance(content, str):
        text = content
    elif isinstance(content, list):
        for c in content:
            if isinstance(c, dict) and c.get("type") == "text":
                text = c.get("text", "") or ""
                if text:
                    break
    if not text:
        return None
    # Skip system/heartbeat noise — these aren't user-facing channel msgs.
    stripped = text.strip()
    if stripped.startswith("System:") or "HEARTBEAT" in stripped:
        return None
    ts = obj.get("timestamp") or obj.get("ts") or ""
    if not ts:
        return None
    eid = (
        obj.get("id")
        or obj.get("eventId")
        or obj.get("messageId")
        or f"{session_id}:{ts}:{role}"
    )
    if role == "user":
        # Recognised inbound formats — the Connector layer tags every
        # inbound message with one of these prefixes. We try Telegram /
        # iMessage / WhatsApp / Signal / Discord / Slack first because
        # those cover ~95% of installed adapters; the rest fall through
        # to the generic ``[Provider …]`` matcher.
        m = _re.match(
            r"\[(?P<prov>Telegram|iMessage|WhatsApp|Signal|Discord|Slack|"
            r"IRC|WebChat|GoogleChat|MSTeams|BlueBubbles|Matrix|Mattermost|"
            r"LINE|Nostr|Twitch|Feishu|Zalo|Tlon|SynologyChat|NextcloudTalk)"
            r"\s+(?P<sender>.+?)\s+id:(?P<sid>[^\]]+?)\]\s*(?P<body>.*)",
            stripped,
            flags=_re.IGNORECASE | _re.DOTALL,
        )
        if not m:
            return None
        provider = m.group("prov").lower()
        sender_name = m.group("sender").strip()
        chan_id = m.group("sid").strip()
        body = m.group("body").strip() or stripped
        return {
            "id":          str(eid),
            "agent_id":    "main",
            "provider":    provider,
            "channel_id":  chan_id,
            "sender_id":   chan_id,
            "sender_name": sender_name,
            "body":        body[:4000],
            "ts":          str(ts),
            "direction":   "in",
            "session_key": session_id,
            "raw_blob":    None,
        }
    # Assistant turn — outbound. We don't know the channel from the
    # event alone (the session-metadata blob carries it, processed in
    # _local_ingest_sessions_batch). Skip here; the per-session metadata
    # writer takes care of attribution via the ``openclaw_channels``
    # table. The summary endpoint joins on session_key so outbound
    # counts populate from a follow-up adapter PR. Returning None here
    # keeps this PR's footprint minimal and avoids stamping the wrong
    # provider on assistant turns from sessions we haven't classified.
    return None


# ── v3 underscore-schema parser (#1135) ───────────────────────────────────────
#
# OpenClaw writes TWO different jsonl shapes per session:
#
#   1. ``<sid>.trajectory.jsonl`` — runtime debug trace sidecar.
#      Dot.separated event types (``trace.artifacts``, ``model.completed``,
#      ``prompt.submitted``, ``session.ended``…) with content under
#      ``data.*``. The trajectory parser path (``_local_ingest_session_batch``
#      below) was originally written for this shape.
#
#   2. ``<sid>.jsonl`` — the canonical user-facing transcript ("v3" schema,
#      tagged by the leading ``{"type": "session", "version": 3, ...}`` line).
#      Underscore_separated event types (``message``, ``model_change``,
#      ``thinking_level_change``, ``tool_use_result``…) with the LLM payload
#      nested under ``message.{role,content,usage,model}``. Until #1135 the
#      ingest path stamped ``event_type="message"`` onto these rows AND left
#      the data shape un-translated, so the dashboard's transcript expander
#      (designed for the dot.separated shape from PR #1132) saw none of the
#      content.
#
# ``_parse_v3_event`` maps a v3 underscore event to the SAME row shape that
# the trajectory path produces — same dot-separated ``event_type`` values,
# same ``data.{finalPromptText,completionText,toolMetas,promptCache.…}``
# nested keys — so the read-side handlers in PR #1132 work unchanged. It
# returns ``None`` for plumbing types we deliberately drop
# (``thinking_level_change``, ``cwd_change``, …) and unknown types.

# Top-level v3 event types we recognise. Anything else falls through to the
# trajectory parser, which itself drops unknowns. Keep this set narrow to
# avoid mis-routing trajectory events that happen to have a synonym name.
_V3_KNOWN_TYPES = frozenset({
    "session",
    "model_change",
    "thinking_level_change",
    "cwd_change",
    "message",
    "tool_use",
    "tool_use_result",
})

# Plumbing event types that carry no transcript-visible content. Returning
# None here is intentional — the dashboard's brain feed and transcript view
# are noisier, not richer, when these are surfaced.
_V3_SKIP_TYPES = frozenset({
    "thinking_level_change",
    "cwd_change",
})


def _is_v3_event(obj: dict) -> bool:
    """Sniff a single parsed JSONL event for the v3 underscore schema.

    The first line of a v3 file is always ``{"type": "session", "version": N,
    ...}`` — that's the strongest signal. For subsequent lines we look for
    type-name + structural cues that only the v3 shape carries:

    * ``model_change``, ``thinking_level_change``, ``cwd_change``,
      ``tool_use``, ``tool_use_result`` — these names are NEW in v3 and
      never appear in trajectory or legacy synthesised events.
    * ``message`` is overloaded: legacy synthesised events use
      ``{"type":"message","role":"user","text":"…"}`` (top-level fields)
      while v3 nests under ``{"type":"message","message":{role,content,…}}``.
      We require the nested ``message`` dict to disambiguate; without it
      the line is treated as legacy and falls through to the trajectory
      parser (which preserves the existing event_type and data).
    """
    if not isinstance(obj, dict):
        return False
    t = obj.get("type")
    if not isinstance(t, str):
        return False
    if t == "session" and obj.get("version") is not None:
        return True
    if t == "message":
        # Disambiguate v3 (nested message dict) from legacy synthesised
        # events that ALSO use type=message but with top-level role/text.
        return isinstance(obj.get("message"), dict)
    return t in _V3_KNOWN_TYPES


def _v3_content_to_text(content) -> str:
    """Flatten a v3 ``message.content`` (string OR list of typed blocks)
    into a single plain-text string. Tool-use blocks and other non-text
    blocks are preserved separately by the caller — this helper deliberately
    drops them so the resulting text mirrors what the trajectory schema
    stored in ``finalPromptText``/``completionText`` (the printable bit)."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for block in content:
            if isinstance(block, dict) and block.get("type") == "text":
                txt = block.get("text") or ""
                if txt:
                    parts.append(txt)
        return "\n".join(parts)
    if content is None:
        return ""
    return str(content)


def _v3_extract_tool_metas(content) -> list[dict]:
    """Pull tool_use blocks out of an assistant ``message.content`` array
    and project them onto the ``toolMetas`` shape PR #1132's expander reads
    (``{name, input}``). Returns [] when there are no tool calls."""
    out: list[dict] = []
    if not isinstance(content, list):
        return out
    for block in content:
        if not isinstance(block, dict):
            continue
        if block.get("type") != "tool_use":
            continue
        out.append({
            "id": block.get("id"),
            "name": block.get("name") or "tool",
            "input": block.get("input") or {},
        })
    return out


def _parse_v3_event(
    obj: dict,
    session_id: str,
    node_id: str,
) -> dict | None:
    """Map ONE v3 underscore-schema event to a normalised local-store row.

    Returns ``None`` for plumbing events we deliberately skip
    (``thinking_level_change``, ``cwd_change``) and for anything unrecognised
    inside the v3 namespace — the caller treats ``None`` as "drop this row"
    rather than re-routing through the trajectory path (the v3 sniff already
    classified it).

    The output row carries the dot.separated ``event_type`` values and the
    nested ``data.*`` key paths the trajectory parser produces, so the read
    side (``_try_local_store_transcript`` / ``_try_local_store_transcript_events``
    in routes/sessions.py) works unchanged on both shapes.
    """
    t = obj.get("type")
    if not isinstance(t, str):
        return None
    if t in _V3_SKIP_TYPES:
        return None

    ts = obj.get("timestamp") or obj.get("ts") or ""
    if not ts:
        # The local store indexes on ts; without it we cannot place the
        # event on the timeline. Safer to drop than to fabricate.
        return None

    eid = obj.get("id") or obj.get("eventId") or f"{session_id}:{ts}:{t}"

    # Defaults; overridden per type below.
    event_type = "unknown"
    # ``data`` mirrors the TRAJECTORY shape that routes/sessions.py expects:
    # top-level ``type`` + ``timestamp`` + sometimes ``modelId`` for the
    # discriminator / model picker, and a NESTED ``data`` sub-dict carrying
    # the content fields (``finalPromptText``, ``completionText``,
    # ``promptCache``, ``toolMetas`` …) that ``_expand_openclaw_event`` and
    # ``_openclaw_event_tokens`` read. The legacy flat keys that #1135's
    # parser stored at the top level are kept alongside the nested copy so
    # existing brain-feed / debug consumers keep working.
    data: dict = {"_v3_type": t}  # preserve the original tag for debugging
    inner: dict = {}  # nested ``data.data`` payload — matches trajectory shape
    cost_usd: float | None = None
    token_count: int | None = None
    model: str | None = None

    if t == "session":
        # First line of every v3 file. Project onto session.started so the
        # brain feed and per-session sidebar see a session-creation marker.
        event_type = "session.started"
        data.update({
            "id": obj.get("id"),
            "version": obj.get("version"),
            "cwd": obj.get("cwd"),
            "timestamp": ts,
        })
        inner.update({
            "id": obj.get("id"),
            "version": obj.get("version"),
            "cwd": obj.get("cwd"),
        })

    elif t == "model_change":
        event_type = "model.changed"
        model = obj.get("modelId") or obj.get("model")
        data.update({
            "modelId": model,
            "provider": obj.get("provider"),
            "timestamp": ts,
        })
        inner.update({
            "modelId": model,
            "provider": obj.get("provider"),
        })

    elif t == "message":
        msg = obj.get("message") if isinstance(obj.get("message"), dict) else {}
        role = msg.get("role")
        content = msg.get("content")
        text = _v3_content_to_text(content)
        usage = msg.get("usage") if isinstance(msg.get("usage"), dict) else {}
        # v3 uses Anthropic-style camelCase keys: input / output / totalTokens.
        # PR #1132's _openclaw_event_tokens reads
        # data.promptCache.lastCallUsage.{total,input,output}, so we project
        # there. Cost lives under usage.cost.{total,input,output}.
        last_call_usage: dict = {}
        if usage:
            inp = usage.get("input") or usage.get("input_tokens")
            outp = usage.get("output") or usage.get("output_tokens")
            tot = (
                usage.get("totalTokens")
                or usage.get("total_tokens")
                or usage.get("total")
            )
            if inp is not None:
                last_call_usage["input"] = int(inp)
            if outp is not None:
                last_call_usage["output"] = int(outp)
            if tot is not None:
                try:
                    last_call_usage["total"] = int(tot)
                    token_count = int(tot)
                except (TypeError, ValueError):
                    pass
            elif inp is not None and outp is not None:
                token_count = int(inp) + int(outp)

            cost = usage.get("cost")
            if isinstance(cost, dict):
                cv = cost.get("total")
                if cv is None and cost.get("input") is not None and cost.get("output") is not None:
                    try:
                        cv = float(cost["input"]) + float(cost["output"])
                    except (TypeError, ValueError):
                        cv = None
                if cv is not None:
                    try:
                        cost_usd = float(cv)
                    except (TypeError, ValueError):
                        cost_usd = None

        if role == "user":
            event_type = "prompt.submitted"
            data.update({
                "finalPromptText": text,
                "timestamp": ts,
            })
            inner["finalPromptText"] = text
            if last_call_usage:
                data["promptCache"] = {"lastCallUsage": last_call_usage}
                inner["promptCache"] = {"lastCallUsage": last_call_usage}
        elif role == "assistant":
            event_type = "model.completed"
            model = msg.get("model") or model
            tool_metas = _v3_extract_tool_metas(content)
            data.update({
                "completionText": text,
                "assistantTexts": [text] if text else [],
                "modelId": model,
                "provider": msg.get("provider"),
                "timestamp": ts,
                "stopReason": msg.get("stopReason"),
            })
            inner.update({
                "completionText": text,
                "assistantTexts": [text] if text else [],
                "modelId": model,
                "provider": msg.get("provider"),
                "stopReason": msg.get("stopReason"),
            })
            if tool_metas:
                data["toolMetas"] = tool_metas
                inner["toolMetas"] = tool_metas
            if last_call_usage:
                data["promptCache"] = {"lastCallUsage": last_call_usage}
                inner["promptCache"] = {"lastCallUsage": last_call_usage}
        else:
            # Unknown role — be conservative, drop rather than mis-classify.
            return None

    elif t == "tool_use":
        # Top-level tool_use is rare in v3 (most tool calls live inside
        # assistant message.content), but if/when one does appear, project
        # it onto the dot.separated tool.call shape.
        event_type = "tool.call"
        data.update({
            "name": obj.get("name") or "tool",
            "input": obj.get("input") or {},
            "id": obj.get("id"),
            "timestamp": ts,
        })
        inner.update({
            "name": obj.get("name") or "tool",
            "input": obj.get("input") or {},
            "id": obj.get("id"),
        })

    elif t == "tool_use_result":
        event_type = "tool.result"
        # ``content`` is typically a list of {type:"text",text:"..."} blocks
        # or a plain string; flatten so PR #1132's expander finds it under
        # ``data.output`` / ``data.result``.
        result_text = _v3_content_to_text(obj.get("content"))
        data.update({
            "tool_use_id": obj.get("tool_use_id"),
            "output": result_text,
            "result": result_text,
            "is_error": obj.get("is_error"),
            "timestamp": ts,
        })
        inner.update({
            "tool_use_id": obj.get("tool_use_id"),
            "output": result_text,
            "result": result_text,
            "is_error": obj.get("is_error"),
        })

    else:
        # Unknown v3 event — log + drop so future schema additions don't
        # silently land as event_type="unknown" rows that pollute analytics.
        log.debug("unknown v3 event type %r — skipping (session=%s)", t, session_id)
        return None

    # MOAT fix: stamp the dot.separated event_type onto data.type so
    # routes/sessions.py::_is_openclaw_event (PR #1132) recognises this
    # row as an OpenClaw event. Without this the discriminator sees
    # data.type == None, falls back to the Anthropic shape, and
    # /api/transcript/<sid> renders 0 messages even though brain-history
    # (which reads the event_type column directly) works fine.
    data["type"] = event_type
    # MOAT fix part 2: attach the nested ``data`` payload that the
    # trajectory parser produces (``data: obj`` of the raw event line) so
    # ``_expand_openclaw_event`` / ``_openclaw_event_tokens`` find the
    # content + usage at the same key paths as for trajectory events.
    data["data"] = inner

    return {
        "id": str(eid),
        "agent_type": "openclaw",
        "node_id": node_id,
        "agent_id": "main",
        "session_id": session_id,
        "workspace_id": None,
        "event_type": event_type,
        "ts": str(ts),
        "data": data,
        "cost_usd": cost_usd,
        "token_count": token_count,
        "model": model,
    }


def _local_ingest_session_batch(
    batch: list,
    session_file: str,
    node_id: str,
    subagent_id: str | None,
) -> None:
    """Translate a batch of raw OpenClaw transcript events into the local
    store's normalised shape and queue them for write. Idempotent at the
    store level — INSERT OR IGNORE on event id.

    Schema-aware: events that carry the v3 underscore schema (see
    ``_is_v3_event`` / ``_parse_v3_event``) are routed through the v3 mapper,
    which projects them onto the SAME dot.separated event_types and nested
    data shape that the trajectory parser produces. Everything else falls
    through to the legacy trajectory path. This per-event sniff (vs. a
    per-batch one) keeps the code correct when a single batch happens to
    mix shapes — e.g. the streaming reader hands us tail-of-file v3 lines
    after a checkpoint switchover.
    """
    from clawmetry import local_store  # local import: keeps cli/sync importable on Pythons missing sqlite3

    store = local_store.get_store()
    rows: list[dict] = []
    # session_file is like '<uuid>.jsonl' — use the uuid as the canonical
    # session_id so the dashboard's per-session views can correlate.
    session_id = subagent_id or session_file.split(".jsonl", 1)[0]
    for obj in batch:
        if not isinstance(obj, dict):
            continue
        # Issue #1088 Phase 4: opportunistically project inbound channel
        # messages into the channel_messages table. Best-effort — never
        # blocks the events ingest below on a per-row failure. The channel
        # extractor reads ``message.{role,content}``, which is the v3 shape,
        # so it works regardless of which parser branch we take next.
        try:
            ch_row = _extract_channel_message(obj, session_id=session_id)
            if ch_row is not None:
                store.ingest_channel_message(ch_row)
        except Exception as _e:
            log.debug("channel_message extract failed (continuing): %s", _e)

        # v3 underscore schema (#1135) — translate onto the trajectory shape
        # so the read path works unchanged. ``_parse_v3_event`` returns None
        # for plumbing/unknown types; we drop those rather than fall back to
        # the trajectory parser (which would stamp event_type="message"
        # etc. and re-introduce the bug).
        if _is_v3_event(obj):
            row = _parse_v3_event(obj, session_id, node_id)
            if row is not None:
                rows.append(row)
            continue

        # Stable per-event id: prefer an explicit id from the transcript, then
        # the openclaw eventId, else compose from session_id + timestamp +
        # message-id-ish hint. INSERT OR IGNORE makes re-delivery harmless.
        eid = (
            obj.get("id")
            or obj.get("eventId")
            or obj.get("messageId")
            or f"{session_id}:{obj.get('timestamp','?')}:{obj.get('type','?')}"
        )
        ts = obj.get("timestamp") or obj.get("ts") or ""
        if not ts:
            # Skip events with no timestamp — the local store's index assumes
            # ts is set, and filtering them out is safer than synthesising one.
            continue
        # Cost / token / model live UNDER ``message.usage`` in OpenClaw's real
        # transcript shape (verified 2026-05-13 against
        # ~/.openclaw/agents/main/sessions/*.jsonl). Top-level ``cost_usd`` /
        # ``tokens`` only appear in synthesised events (e.g. our own tests).
        # See MOAT_E2E_REPORT_2026-05-13 root-cause #4.
        cost_usd, token_count, model = _extract_cost_tokens_model(obj)
        rows.append({
            "id": str(eid),
            "node_id": node_id,
            "agent_id": "main",  # OpenClaw harness; Claude Code adapter will use 'claude-code'
            "session_id": session_id,
            "workspace_id": obj.get("workspace") or obj.get("workspace_id"),
            "event_type": str(obj.get("type") or obj.get("event_type") or "unknown"),
            "ts": str(ts),
            "data": obj,
            "cost_usd": cost_usd,
            "token_count": token_count,
            "model": model,
        })
    if rows:
        store.ingest_many(rows)


def _local_ingest_sessions_batch(rows: list, node_id: str) -> None:
    """Mirror a batch of session rows (the same dicts we push to /ingest/sessions)
    into the local DuckDB ``sessions`` table. One upsert per row; safe to call
    on a store that already has these sessions (ON CONFLICT DO UPDATE)."""
    if not rows:
        return
    from clawmetry import local_store

    store = local_store.get_store()
    for s in rows:
        sid = s.get("session_id") or s.get("session_key") or s.get("id")
        if not sid:
            continue
        # Cost field has been called several things in different code paths
        # (total_cost, cost_usd, totalCostUsd). Take the first non-None.
        cost = s.get("cost_usd")
        if cost is None:
            cost = s.get("total_cost") or s.get("totalCostUsd") or 0
        # Channel/chat_type/subject move into a separate metadata blob —
        # they're OpenClaw-specific and (per the multi-agent design) will get
        # promoted into the openclaw_channels extension table later.
        meta_extras = {
            k: v for k, v in s.items()
            if k in ("channel", "chat_type", "subject", "recent_model",
                     "session_key")
            and v
        }
        store.ingest_session({
            "agent_type": s.get("agent_type") or "openclaw",
            "session_id": sid,
            "node_id": node_id,
            "agent_id": s.get("agent_id") or "main",
            "title": s.get("subject") or s.get("title"),
            "started_at": s.get("started_at"),
            "last_active_at": s.get("updated_at") or s.get("last_active_at"),
            "ended_at": s.get("ended_at"),
            "status": s.get("status"),
            "total_tokens": s.get("total_tokens") or 0,
            "cost_usd": cost,
            "message_count": s.get("message_count") or 0,
            "metadata": meta_extras or None,
        })


def _local_ingest_memory_files(all_files: list, changed_paths: list) -> None:
    """Persist plaintext memory blobs to local DuckDB. ``all_files`` is the
    full list of (name, content) tuples; ``changed_paths`` is the subset
    that changed since last sync. We only write the changed ones — the
    store's sha256 dedup means it's a no-op anyway, but skipping the
    encode round-trip is cheaper."""
    if not changed_paths:
        return
    from clawmetry import local_store

    store = local_store.get_store()
    changed_set = set(changed_paths)
    now_iso = datetime.now(timezone.utc).isoformat()
    for name, content in all_files:
        if name not in changed_set:
            continue
        store.ingest_memory_blob({
            "agent_type": "openclaw",  # OpenClaw harness writes these files
            "agent_id": "main",
            "path": name,
            "ts": now_iso,
            "blob": content,
        })


_sessions_json_cache: dict = {"ts": 0.0, "data": None, "mtime": 0.0}


def sync_sessions_recent(
    config: dict, state: dict, paths: dict, minutes: int = 60
) -> int:
    """Sync only events from the last N minutes, reading files from the tail.

    This gives the dashboard immediate visibility into *current* activity.
    The normal ``sync_sessions`` loop then backfills older events in the
    background without blocking the Brain feed.

    Strategy:
      1. For each session file (newest-modified first), binary-search for the
         first line whose timestamp falls within the window.
      2. Sync from that line to EOF.
      3. Advance ``last_event_ids`` so the normal loop skips already-synced
         recent lines and continues backfilling from where it left off.
    """
    if not _sync_allowed():
        return 0
    _record_sync_progress("sessions_recent", 0)
    from datetime import timedelta

    sessions_dir = paths["sessions_dir"]
    api_key = config["api_key"]
    enc_key = config.get("encryption_key")
    node_id = config["node_id"]
    last_ids: dict = state.setdefault("last_event_ids", {})
    total = 0

    cutoff = datetime.now(timezone.utc) - timedelta(minutes=minutes)
    cutoff_iso = cutoff.isoformat()

    # Build subagent map (same logic as sync_sessions)
    # Cache sessions.json for 60 seconds to avoid re-parsing every call
    global _sessions_json_cache
    file_to_subagent_id: dict[str, str] = {}
    index_path = os.path.join(sessions_dir, "sessions.json")
    if os.path.isfile(index_path):
        try:
            current_mtime = os.path.getmtime(index_path)
            if _sessions_json_cache["data"] is not None and _sessions_json_cache["mtime"] == current_mtime:
                file_to_subagent_id = _sessions_json_cache["data"]
            else:
                with open(index_path) as _fi:
                    _idx = json.load(_fi)
                for _k, _meta in _idx.items():
                    if ":subagent:" in _k and isinstance(_meta, dict):
                        _sf = _meta.get("sessionFile", "")
                        if _sf:
                            file_to_subagent_id[os.path.basename(_sf)] = _k.split(":")[-1]
                _sessions_json_cache = {"ts": time.time(), "data": file_to_subagent_id.copy(), "mtime": current_mtime}
        except Exception:
            pass

    jsonl_files = _list_session_jsonls(sessions_dir)
    jsonl_files.sort(key=lambda p: os.path.getmtime(p), reverse=True)

    for fpath in jsonl_files:
        if total >= MAX_EVENTS_PER_CYCLE:
            break

        fname = os.path.basename(fpath)
        cloud_fname = _canonical_session_file(fname)
        subagent_id = file_to_subagent_id.get(cloud_fname) or file_to_subagent_id.get(fname)

        try:
            with open(fpath, "r", errors="replace") as f:
                all_lines = list(islice(f, None))  # read all for backwards scan

            n = len(all_lines)
            if n == 0:
                continue

            # Find the first line >= cutoff by scanning backwards.
            # Most lines have a "timestamp" field we can compare lexicographically.
            start_idx = n  # default: nothing recent
            for idx in range(n - 1, -1, -1):
                raw = all_lines[idx].strip()
                if not raw:
                    continue
                try:
                    obj = json.loads(raw)
                    ts = obj.get("timestamp", "")
                    if ts and ts < cutoff_iso:
                        start_idx = idx + 1
                        break
                except Exception:
                    continue
            else:
                # All lines are within the window (or no timestamps found)
                start_idx = 0

            if start_idx >= n:
                continue  # nothing recent in this file

            # Only sync lines that haven't been synced yet
            already_synced = last_ids.get(fname, 0)
            effective_start = max(start_idx, already_synced)
            if effective_start >= n:
                continue

            batch: list[dict] = []
            for i in range(effective_start, n):
                raw = all_lines[i].strip()
                if not raw:
                    continue
                try:
                    obj = json.loads(raw)
                except Exception:
                    continue
                batch.append(obj)
                if len(batch) >= BATCH_SIZE:
                    _flush_session_batch(
                        batch, cloud_fname, api_key, enc_key, node_id, subagent_id
                    )
                    total += len(batch)
                    batch = []
                    if total >= MAX_EVENTS_PER_CYCLE:
                        break

            if batch:
                _flush_session_batch(
                    batch, cloud_fname, api_key, enc_key, node_id, subagent_id
                )
                total += len(batch)

            # Advance cursor to EOF so backfill loop doesn't re-send these.
            # But DON'T advance past what the normal loop would have started at
            # — keep the old cursor so it backfills the gap between old cursor
            # and start_idx.
            last_ids[fname] = max(last_ids.get(fname, 0), n)

        except Exception as e:
            log.warning(f"Recent sync error ({fname}): {e}")

    _record_sync_progress("sessions_recent", total, total)
    return total


# ── Sync: claude-cli backend transcripts ──────────────────────────────────────
# OpenClaw routes most chat (TUI, Telegram, etc.) through the agent/cli-backend
# plugin, which delegates to the Claude Code CLI. Claude CLI writes the actual
# transcript to ~/.claude/projects/<cwd-slug>/<cli-session-id>.jsonl -- keyed on
# the agent process CWD, which is usually *not* the OpenClaw workspace. Without
# this adapter the cloud Brain feed stays frozen at the last bootstrap event
# and misses every real message.


def _claude_projects_root() -> Path:
    """Return Claude Code's projects directory."""
    custom = os.environ.get("CLAUDE_CONFIG_DIR")
    if custom:
        return Path(os.path.expanduser(custom)) / "projects"
    return Path(os.path.expanduser("~/.claude/projects"))


def _translate_claude_cli_event(obj: dict) -> dict:
    """Map claude-cli jsonl event keys onto OpenClaw event keys.

    The cloud Brain parser keys off 'id', 'parentId', 'type', 'timestamp',
    and 'message'. Claude CLI uses 'uuid' / 'parentUuid' for the first two;
    everything else lines up. We rename in-place and pass the rest through
    so cost/usage/tool fields survive without per-version translation.
    """
    out = dict(obj)
    if "uuid" in out and "id" not in out:
        out["id"] = out.pop("uuid")
    if "parentUuid" in out and "parentId" not in out:
        out["parentId"] = out.pop("parentUuid")
    return out


def sync_claude_cli_sessions(config: dict, state: dict, paths: dict) -> int:
    """Tail claude-cli transcripts and push them under the OpenClaw session_file.

    For each entry in `agents/main/sessions/sessions.json` that carries a
    `claudeCliSessionId`, locate the matching jsonl under
    `~/.claude/projects/*/` (scanning all project dirs, since Claude Code
    derives the slug from the agent's CWD rather than the OpenClaw workspace),
    tail new lines, translate them, and push via `_flush_session_batch` using
    the OpenClaw session_file basename. The cloud correlates events to the
    existing session row by that basename, so no cloud-side change is required.
    """
    if not _sync_allowed():
        return 0
    sessions_dir = paths.get("sessions_dir") or ""
    if not sessions_dir:
        return 0

    api_key = config["api_key"]
    enc_key = config.get("encryption_key")
    node_id = config["node_id"]

    index_path = os.path.join(sessions_dir, "sessions.json")
    if not os.path.isfile(index_path):
        return 0
    try:
        with open(index_path) as fi:
            idx = json.load(fi)
    except Exception:
        return 0

    # Claude Code derives the project slug from the *agent process CWD*, not the
    # OpenClaw workspace — a Telegram session spawned from ~/clawd writes to
    # `-home-vivek-clawd/`, even though OpenClaw's workspace is
    # ~/.openclaw/workspace. Scan every project dir and index transcripts by
    # their session-id filename so we find the right file regardless of CWD.
    projects_root = _claude_projects_root()
    if not projects_root.is_dir():
        return 0
    cli_id_to_path: dict[str, Path] = {}
    try:
        for proj_dir in projects_root.iterdir():
            if not proj_dir.is_dir():
                continue
            for jp in proj_dir.glob("*.jsonl"):
                cli_id_to_path[jp.stem] = jp
    except OSError:
        return 0

    targets: list[tuple[str, str]] = []  # (claude_jsonl_path, openclaw_basename)
    for sess_key, meta in idx.items():
        if not isinstance(meta, dict):
            continue
        cli_id = meta.get("claudeCliSessionId") or (
            meta.get("cliSessionIds", {}) or {}
        ).get("claude-cli")
        if not cli_id:
            continue
        cli_path = cli_id_to_path.get(cli_id)
        if cli_path is None:
            continue
        oc_sf = meta.get("sessionFile", "")
        # Fall back to <openclaw_session_id>.jsonl when sessionFile is absent
        # (e.g. Telegram session metadata exists but the OpenClaw jsonl was
        # never written). Cloud will create the session row from these events.
        oc_basename = (
            os.path.basename(oc_sf)
            if oc_sf
            else f"{meta.get('sessionId', cli_id)}.jsonl"
        )
        targets.append((str(cli_path), oc_basename))

    if not targets:
        return 0

    # Separate offset namespace so it can't collide with OpenClaw jsonl offsets.
    cli_offsets: dict = state.setdefault("last_event_ids_cli", {})
    total = 0

    for cli_path, oc_basename in targets:
        if total >= MAX_EVENTS_PER_CYCLE:
            break

        offset_key = os.path.basename(cli_path)
        last_line = cli_offsets.get(offset_key, 0)
        batch: list[dict] = []

        try:
            with open(cli_path, "r", errors="replace") as f:
                new_lines = list(islice(f, last_line, None))

            line_cursor = last_line
            for i, raw in enumerate(new_lines, start=last_line):
                raw = raw.strip()
                if not raw:
                    line_cursor = i + 1
                    continue
                try:
                    obj = json.loads(raw)
                except Exception:
                    line_cursor = i + 1
                    continue
                batch.append(_translate_claude_cli_event(obj))
                line_cursor = i + 1
                if len(batch) >= BATCH_SIZE:
                    _flush_session_batch(
                        batch, oc_basename, api_key, enc_key, node_id
                    )
                    total += len(batch)
                    batch = []
                    cli_offsets[offset_key] = line_cursor
                    if total >= MAX_EVENTS_PER_CYCLE:
                        break

            if batch:
                _flush_session_batch(batch, oc_basename, api_key, enc_key, node_id)
                total += len(batch)

            cli_offsets[offset_key] = line_cursor

        except Exception as e:
            log.warning(f"claude-cli sync error ({offset_key}): {e}")

    return total


# ── Sync: logs (full lines, encrypted) ────────────────────────────────────────


def sync_logs(config: dict, state: dict, paths: dict) -> int:
    # Skipped when sync is paused (expired trial). Offsets persist so
    # nothing is lost on resume.
    if not _sync_allowed():
        return 0
    log_dir = paths["log_dir"]
    api_key = config["api_key"]
    enc_key = config.get("encryption_key")
    node_id = config["node_id"]
    offsets: dict = state.setdefault("last_log_offsets", {})
    total = 0

    log_files = sorted(glob.glob(os.path.join(log_dir, "openclaw-*.log")))[-5:]
    for fpath in log_files:
        fname = os.path.basename(fpath)
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


def _flush_log_batch(
    entries: list, fname: str, api_key: str, enc_key: str | None, node_id: str
) -> None:
    payload = {"log_file": fname, "node_id": node_id, "lines": entries}
    if enc_key:
        _post(
            "/ingest/logs",
            {
                "node_id": node_id,
                "encrypted": True,
                "blob": encrypt_payload(payload, enc_key),
            },
            api_key,
        )
    else:
        _post("/ingest/logs", payload, api_key)


# ── Heartbeat ─────────────────────────────────────────────────────────────────


def _detect_ollama_for_heartbeat():
    """Detect Ollama status for heartbeat reporting."""
    import shutil

    result = {"installed": False, "running": False, "models": []}

    # Check if binary exists
    ollama_bin = shutil.which("ollama")
    if not ollama_bin:
        common_paths = [
            "/opt/homebrew/bin/ollama",
            "/usr/local/bin/ollama",
            "/usr/bin/ollama",
            os.path.expanduser("~/.ollama/ollama"),
        ]
        if os.name == "nt":
            common_paths.extend(
                [
                    os.path.expandvars(r"%LOCALAPPDATA%\Programs\Ollama\ollama.exe"),
                    os.path.expandvars(r"%LOCALAPPDATA%\Ollama\ollama.exe"),
                ]
            )
        for p in common_paths:
            if os.path.isfile(p):
                ollama_bin = p
                break

    if ollama_bin:
        result["installed"] = True

    # Check if running + get models
    try:
        import json as _json

        req = urllib.request.Request("http://localhost:11434/api/tags", method="GET")
        with urllib.request.urlopen(req, timeout=3) as resp:
            if resp.status == 200:
                result["running"] = True
                data = _json.loads(resp.read())
                result["models"] = [
                    m.get("name", "") for m in data.get("models", [])[:10]
                ]
                result["installed"] = True  # If running, definitely installed
    except Exception:
        pass

    return result


# ── Gateway process-metric capture (#852 follow-up) ──────────────────────────
# PR #1146 added a *live* gateway-health snapshot (RSS/CPU/uptime). That's
# fine for "is it green right now?" but the gateway's slow memory-bloat-OOM
# pattern (~600 MB → ~945 MB) is only visible if you SEE THE TREND.
#
# Per the DuckDB-first rule, historical data lives in DuckDB. We capture
# gateway vitals every 30s in the daemon loop and write them as
# ``event_type="gateway.metric"`` events. The dashboard's
# ``/api/gateway-health/history`` then plots a 24h sparkline.
#
# Constraints:
#   * Every 30s max (rate-cap to keep DB writes cheap).
#   * Dedupe: if a fresh sample matches the previous one closely (within
#     5 min and small variance) we skip writing — the gateway is largely
#     idle between agent calls so otherwise we'd write ~2,880 near-identical
#     rows/day. With dedupe a typical day is ~50-300 rows.
#   * Skip writes when the gateway isn't running — no point flooding the
#     event log with "not_running" rows during dev or after a crash.
#   * Best-effort: any failure (compute_gateway_health, local_store import,
#     ingest) is swallowed; the daemon loop keeps ticking.

GATEWAY_METRIC_INTERVAL_SEC = 30
GATEWAY_METRIC_DEDUP_WINDOW_SEC = 300        # 5 min
GATEWAY_METRIC_DEDUP_RSS_TOLERANCE_MB = 5.0  # don't re-write within ±5 MB
GATEWAY_METRIC_DEDUP_CPU_TOLERANCE_PCT = 2.0  # don't re-write within ±2% CPU

# Module-level state for rate-capping + dedupe. (last_write_ts, last_payload).
# Reset on import; the daemon runs as one long-lived process, so this is fine.
# Sentinel ``None`` means "no sample written yet" — the rate-cap check skips
# the comparison so the very first call always falls through to capture.
_LAST_GATEWAY_METRIC_TS: float | None = None
_LAST_GATEWAY_METRIC: dict | None = None


def _should_dedupe_gateway_metric(prev: dict | None, curr: dict) -> bool:
    """Return True when *curr* is close enough to *prev* that we should skip
    the write. The five-minute time window is enforced by the caller — this
    helper just answers the value-similarity question.
    """
    if not isinstance(prev, dict):
        return False
    # PID changed → gateway restarted; always write.
    if prev.get("pid") != curr.get("pid"):
        return False
    prev_rss = prev.get("rss_mb")
    curr_rss = curr.get("rss_mb")
    if prev_rss is None or curr_rss is None:
        # Vitals went missing/recovered → write so the gap is visible.
        return prev_rss == curr_rss
    if abs(float(curr_rss) - float(prev_rss)) > GATEWAY_METRIC_DEDUP_RSS_TOLERANCE_MB:
        return False
    prev_cpu = prev.get("cpu_pct") or 0.0
    curr_cpu = curr.get("cpu_pct") or 0.0
    if abs(float(curr_cpu) - float(prev_cpu)) > GATEWAY_METRIC_DEDUP_CPU_TOLERANCE_PCT:
        return False
    return True


def capture_gateway_metric(config: dict) -> bool:
    """Capture one ``gateway.metric`` event into local DuckDB.

    Returns True when a row was written, False when skipped (rate-capped,
    deduped, gateway not running, or any failure).

    Imports ``routes.health.compute_gateway_health`` lazily so the daemon
    doesn't pull the dashboard module graph at import time (the daemon is
    optional; ``routes/`` is a peer of ``clawmetry/`` at the repo root).
    """
    global _LAST_GATEWAY_METRIC_TS, _LAST_GATEWAY_METRIC
    now_mono = time.monotonic()
    if (
        _LAST_GATEWAY_METRIC_TS is not None
        and (now_mono - _LAST_GATEWAY_METRIC_TS) < GATEWAY_METRIC_INTERVAL_SEC
    ):
        return False

    try:
        import routes.health as _rh  # late import — daemon is optional
    except Exception as _e:
        log.debug("gateway.metric: cannot import routes.health (%s)", _e)
        return False

    try:
        # Attribute lookup (NOT a bound reference) so tests + future
        # hot-reloads pick up monkeypatched implementations.
        snap = _rh.compute_gateway_health()
    except Exception as _e:
        log.debug("gateway.metric: compute_gateway_health failed (%s)", _e)
        return False

    if not snap or snap.get("status") == "not_running":
        # Skip noise when the gateway isn't found at all.
        _LAST_GATEWAY_METRIC_TS = now_mono
        return False

    curr = {
        "rss_mb":         snap.get("rss_mb"),
        "cpu_pct":        snap.get("cpu_pct"),
        "pid":            snap.get("pid"),
        "uptime_seconds": snap.get("uptime_seconds"),
    }

    # Dedupe within DEDUP_WINDOW: if this sample looks like the last one and
    # we wrote that one less than 5 min ago, skip the write.
    if _LAST_GATEWAY_METRIC is not None:
        elapsed = now_mono - _LAST_GATEWAY_METRIC_TS
        if elapsed < GATEWAY_METRIC_DEDUP_WINDOW_SEC and _should_dedupe_gateway_metric(
            _LAST_GATEWAY_METRIC, curr
        ):
            return False

    try:
        from clawmetry import local_store as _ls
        store = _ls.get_store()
        store.ingest({
            "id":         uuid.uuid4().hex,
            "node_id":    config.get("node_id") or "unknown",
            "agent_id":   "openclaw-gateway",
            "agent_type": "openclaw",
            "event_type": "gateway.metric",
            "ts":         datetime.now(timezone.utc).isoformat(),
            "data":       curr,
        })
    except Exception as _e:
        log.debug("gateway.metric: ingest failed (%s)", _e)
        return False

    _LAST_GATEWAY_METRIC_TS = now_mono
    _LAST_GATEWAY_METRIC = curr
    return True


# ── Daemon-collected snapshots ────────────────────────────────────────────────
# Cloud's tabs (Security, Models, Upgrades, Clusters, …) need data the OSS
# routes/* endpoints derive from local state — host filesystem checks,
# `openclaw --version` output, gateway WebSocket, etc. None of that exists
# on Cloud Run. The daemon collects locally and pushes on the heartbeat;
# cloud stores the latest blob per node and serves it via cloud-side
# `/api/<feature>` handlers that mirror the OSS shape.
#
# Each collector caches its result in `_snapshot_cache` so we don't
# recompute every heartbeat (most of these are ~100ms-1s and don't change
# minute-to-minute). Re-collected at the interval below or when missing.

_snapshot_cache: dict = {}            # name → (value, computed_at_unix_ts)
_SNAPSHOT_TTL_SEC = 300               # 5 min — security posture etc.


def _collect_security_posture() -> dict | None:
    """Run OSS `_scan_security_posture()` locally and return its result.

    Imports OSS dashboard.py via importlib so we don't pull the whole Flask
    app into the daemon process. Cached for 5 min — the underlying checks
    are filesystem reads (~50 ms total) but we don't need fresher data than
    that for a posture overview.
    """
    cached = _snapshot_cache.get("security_posture")
    if cached and (time.time() - cached[1]) < _SNAPSHOT_TTL_SEC:
        return cached[0]
    try:
        # Resolve OSS dashboard.py from the installed clawmetry package
        # (parent dir holds dashboard.py per setup.py's `py_modules`).
        import clawmetry as _cm_pkg
        import importlib.util as _ilu
        oss_dashboard_path = os.path.join(
            os.path.dirname(os.path.dirname(_cm_pkg.__file__)),
            "dashboard.py",
        )
        if not os.path.isfile(oss_dashboard_path):
            return None
        spec = _ilu.spec_from_file_location("_oss_dashboard_for_snapshot", oss_dashboard_path)
        mod = _ilu.module_from_spec(spec)
        # OSS dashboard.py uses sys.modules.setdefault("dashboard", ...) at
        # load — register first so it doesn't KeyError.
        import sys as _sys
        _sys.modules.setdefault("_oss_dashboard_for_snapshot", mod)
        spec.loader.exec_module(mod)
        scan = getattr(mod, "_scan_security_posture", None)
        if not scan:
            return None
        result = scan()
        _snapshot_cache["security_posture"] = (result, time.time())
        return result
    except Exception as e:
        log.warning(f"_collect_security_posture failed: {e}")
        return None


# Adaptive heartbeat: the most recent /ingest/heartbeat response body so the
# main loop (and tests) can derive the next sleep interval without changing
# `send_heartbeat`'s `bool` return type (callers in tests assert `is True`).
# `None` when no successful heartbeat has been received yet OR after a 5xx.
_LAST_HEARTBEAT_RESPONSE: dict | None = None


def _pick_heartbeat_interval(resp_json: dict | None) -> int:
    """Adaptive cadence (#775 PR 2/3): FAST when a viewer is watching the
    cloud dashboard, SLOW otherwise. Pure function so it can be unit-tested
    without booting the daemon loop.

    Back-compat: a cloud that hasn't deployed PR 1 yet won't return the
    `viewer_active` field, so missing → SLOW. Same for `None` (no successful
    heartbeat yet) and any non-dict input.
    """
    if not isinstance(resp_json, dict):
        return HEARTBEAT_INTERVAL_SLOW
    return (
        HEARTBEAT_INTERVAL_FAST
        if resp_json.get("viewer_active", False)
        else HEARTBEAT_INTERVAL_SLOW
    )


def send_heartbeat(config: dict) -> bool:
    """Send heartbeat to cloud. Returns True on success, False on failure.

    Side effect: on success, stashes the parsed response body in
    `_LAST_HEARTBEAT_RESPONSE` so the main loop can read `viewer_active`
    via `_pick_heartbeat_interval()` and adapt the next sleep interval.
    """
    global _LAST_HEARTBEAT_RESPONSE
    payload = {
        "node_id": config["node_id"],
        "ts": datetime.now(timezone.utc).isoformat(),
        "platform": platform.system(),
        "version": _get_version(),
        "e2e": bool(config.get("encryption_key")),
        "ollama": _detect_ollama_for_heartbeat(),
    }
    # Daemon-collected snapshots (see _collect_security_posture docstring)
    sec = _collect_security_posture()
    if sec is not None:
        payload["security_posture"] = sec
    # Local-store health (epic #964 phase 1 → rollout gate for phase 2).
    # We need ≥80% of active nodes reporting healthy local stores before
    # slimming cloud retention to 24h. Best-effort; never blocks heartbeat.
    try:
        from clawmetry import local_store
        h = local_store.get_store().health()
        payload["local_store"] = {
            "engine":       h.get("engine"),
            "size_bytes":   h.get("size_bytes", 0),
            "events_total": h.get("events_total", 0),
            "ring_depth":   h.get("ring_depth", 0),
        }
        # Convenience field the cloud rollout playbook can group/aggregate on.
        size_mb = (h.get("size_bytes") or 0) / (1024 * 1024)
        payload["local_store_size_mb"] = round(size_mb, 3)
    except Exception:
        pass  # local store optional — never break heartbeat over it
    # Phase 2 of relay-v2 (epic #1032): proactively push the top-50 brain
    # events to the cloud cache so the Brain page paints in <100ms on first
    # load instead of waiting for a relay round-trip. The blob is the same
    # E2E ciphertext we use for /ingest/cache, so the cloud never sees
    # plaintext. Best-effort — heartbeat MUST succeed even if this fails.
    try:
        pushes = _build_brain_cache_pushes(config)
        if pushes:
            payload["cache_pushes"] = pushes
    except Exception as _bp_e:
        log.debug("brain cache_push build failed (continuing): %s", _bp_e)
    # Phase 5 of relay-v2 (#1032): channel adapter status. Non-secret
    # status summary (provider, enabled, last_test_at/ok/error) pushed to
    # `channels:{owner_hash}:status` TTL 3600s so the cloud Channels tab
    # paints from Redis. Encrypted blob with config tokens NEVER traverses
    # this push — that ciphertext lives only in local DuckDB.
    try:
        ch_pushes = _build_channel_config_status_cache_pushes(config)
        if ch_pushes:
            payload.setdefault("cache_pushes", []).extend(ch_pushes)
    except Exception as _cp_e:
        log.debug("channel-config cache_push build failed (continuing): %s", _cp_e)
    # Phase 3 of relay-v2 (#1032): also push the user's alert-rule list so the
    # cloud Alerts tab paints from cache. Same envelope (`cache_pushes`) — the
    # cloud's _accept_cache_pushes handler iterates the array regardless of
    # which Phase contributed which entry.
    try:
        alert_pushes = _build_alert_rules_cache_pushes(config)
        if alert_pushes:
            payload.setdefault("cache_pushes", []).extend(alert_pushes)
    except Exception as _ap_e:
        log.debug("alert-rules cache_push build failed (continuing): %s", _ap_e)
    # Phase 4 of epic #1032: push the user's pending approvals queue so the
    # cloud Approvals inbox paints from cache. Same envelope (`cache_pushes`)
    # — cloud's _accept_cache_pushes iterates the array regardless of which
    # phase produced which entry. TTL is short (60s) by acceptance criterion:
    # "approval appears in cloud inbox within 2s", and a stale cache row
    # would block a fresh request from showing up; the next heartbeat
    # overwrites it anyway.
    try:
        ap_pushes = _build_approvals_cache_pushes(config)
        if ap_pushes:
            payload.setdefault("cache_pushes", []).extend(ap_pushes)
    except Exception as _ap_e2:
        log.debug("approvals cache_push build failed (continuing): %s", _ap_e2)
    # Local-first: persist this heartbeat to local DuckDB so the dashboard
    # has a per-node liveness history even when offline. Best-effort.
    try:
        from clawmetry import local_store
        local_store.get_store().ingest_heartbeat(payload)
    except Exception as _le:
        log.debug("local-store heartbeat ingest failed (continuing): %s", _le)
    last_err = None
    for attempt in range(3):
        try:
            resp_json = _post("/ingest/heartbeat", payload, config["api_key"])
            if attempt > 0:
                log.info(f"Heartbeat succeeded after {attempt + 1} attempts")
            # Stash for adaptive-cadence pick (#775 PR 2/3). Normalise to dict
            # so `_pick_heartbeat_interval` always sees a sensible shape even
            # if `_post` ever decides to return None on a 204.
            _LAST_HEARTBEAT_RESPONSE = resp_json if isinstance(resp_json, dict) else {}
            # Phase 1 of relay-v2 (#1053): the cloud may piggyback a small
            # batch of `pending_queries` on the heartbeat response. Each is
            # a shape-allowlisted read against the local DuckDB; we run them,
            # encrypt the result, and POST back to /ingest/cache so the
            # cloud-side dashboard can serve subsequent requests from the
            # warm cache without ever touching the local node.
            pending = (resp_json or {}).get("pending_queries") or []
            if pending:
                _dispatch_pending_queries(config, pending)
            return True
        except Exception as e:
            last_err = e
            if attempt < 2:
                time.sleep(2**attempt)  # 1s, 2s backoff
    # Heartbeat failed: clear the stashed response so the next interval pick
    # falls back to SLOW (don't burn tighter cadence on a stale viewer flag).
    _LAST_HEARTBEAT_RESPONSE = None
    log.warning(f"Heartbeat failed after 3 attempts: {last_err}")
    return False


# ── Heartbeat-piggyback query dispatch (relay-v2 phase 1, #1053) ─────────────
# Allowlist mirrors routes.local_query._SHAPES. Duplicated here so the
# daemon stays safe when `routes/` isn't on sys.path (some installs run the
# sync daemon without the dashboard module loaded).
_PENDING_SHAPES = {"events", "sessions", "aggregates", "health", "transcript"}


def _canonical_args_hash(args: dict) -> str:
    """Stable sha256 of the args dict — sorted keys, no whitespace. Used as
    the cache_key fingerprint so the cloud can detect arg drift even if the
    same `cache_key` label is reused."""
    import hashlib
    canonical = json.dumps(args or {}, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _local_dispatch_fallback(shape: str, args: dict) -> dict:
    """Fallback dispatcher used when `routes.local_query` isn't importable
    (daemon-only installs). Mirrors the minimal shape→method bridge."""
    from clawmetry import local_store
    store = local_store.get_store(read_only=True)
    if shape == "health":
        return store.health()
    method_map = {
        "events":     "query_events",
        "sessions":   "query_sessions",
        "aggregates": "query_aggregates",
        "transcript": "query_events",
    }
    method = method_map.get(shape)
    if not method:
        raise ValueError(f"unknown shape: {shape}")
    rows = getattr(store, method)(**(args or {}))
    return {"rows": rows, "count": len(rows), "_shape": shape, "_via": "fallback"}


def _rows_to_brain_events(rows: list) -> list:
    """Return raw OpenClaw event payloads ready for the cloud browser's
    ``transformEvents`` to unwrap.

    The cloud Brain ``_cm_decryptBrain`` decrypts the blob, reads
    ``dec.events``, then runs ``transformEvents(rawEvs, ...)`` over each
    item — which expects the ORIGINAL JSONL shape:
    ``{type, message:{role, content}, timestamp}``. It walks
    ``message.content[].type === 'text'/'tool_use'/'thinking'`` to extract
    the human-readable detail.

    Earlier we pre-flattened to ``{type:'ASSISTANT', detail:'', src, ...}``
    (the OSS-local shape). That made ``transformEvents`` fall through to its
    empty-detail fallback and DROP every event — cloud Brain showed "No
    brain activity events found" even with hundreds of rows in DuckDB.
    Bug confirmed live 2026-05-13 (Diya/Telegram messages).

    For each row we forward ``row['data']`` as-is. We backfill
    ``timestamp`` from the column-level ``ts`` only when the inner JSONL
    didn't already carry one (transformEvents needs ``obj.timestamp ||
    obj.time``).

    The OSS-local Brain tab uses ``routes/brain.py:_try_local_store_brain``
    which builds the display shape directly — that path is unchanged.
    """
    out = []
    for r in rows or []:
        if not isinstance(r, dict):
            continue
        data = r.get("data")
        if isinstance(data, dict):
            if not data.get("timestamp") and not data.get("time") and r.get("ts"):
                data = {**data, "timestamp": r.get("ts")}
            out.append(data)
        elif isinstance(data, str):
            out.append({
                "type":      r.get("event_type") or "raw",
                "timestamp": r.get("ts", ""),
                "detail":    data[:2000],
            })
    return out


# ── Phase 2: proactive brain cache_push (epic #1032) ─────────────────────────
# The Brain page is the first thing most users hit on the cloud dashboard. In
# Phase 1 the cloud only had data for it after a browser /api/cloud/subscribe
# round-trip (one full heartbeat cycle, up to 60s). Phase 2 pushes the top-50
# brain events on EVERY heartbeat so the page paints from cache in <100ms.
#
# Key shape: `brain:{owner_hash}:{node_id}:recent`. The cloud derives
# owner_hash from the cm_ token (sha256 hex) — we compute the same value here
# so both sides agree on the key without needing the daemon to know the
# cloud's internal user id.
#
# TTL: 6h. Each heartbeat overwrites the entry, so TTL only matters when the
# daemon goes offline — after 6h the cloud treats the cache as cold and
# re-subscribes. Long enough to cover a typical work-day pause; short enough
# that stale data doesn't linger after a node is decommissioned.
BRAIN_CACHE_TTL_SEC = 21600
BRAIN_CACHE_LIMIT = 50


def _owner_hash_for_token(api_key: str) -> str:
    """Mirror of cloud's `_owner_hash_for(token)` — sha256 hex of the cm_
    token. The daemon computes it locally so the cache key it sends matches
    exactly what the cloud derives from the same token on read."""
    import hashlib
    return hashlib.sha256((api_key or "").encode("utf-8")).hexdigest()


def _build_brain_cache_pushes(config: dict) -> list:
    """Return the heartbeat `cache_pushes` array — currently a single entry
    holding the encrypted top-50 brain events for this node.

    Returns an empty list when:
      - The local store has no events yet (fresh install) — nothing to push.
      - Encryption key is unset — we never push plaintext.
      - The local store import fails — degrade silently.

    The blob shape mirrors `routes.brain._try_local_store_brain` so the cloud
    read path can hand the decrypted dict straight to the existing dashboard
    JS without translation.
    """
    enc_key = config.get("encryption_key")
    if not enc_key:
        return []
    api_key = config.get("api_key", "")
    node_id = config.get("node_id", "")
    if not (api_key and node_id):
        return []
    try:
        from clawmetry import local_store
    except Exception:
        return []
    try:
        store = local_store.get_store(read_only=True)
        rows = store.query_events(limit=BRAIN_CACHE_LIMIT)
    except Exception:
        return []
    if not rows:
        return []
    # Same translation as routes/brain.py:_try_local_store_brain so the
    # browser sees an identical event shape regardless of which path served
    # the data (cache hit vs. relay subscribe vs. JSONL fallback).
    events = _rows_to_brain_events(rows)
    payload = {
        "events":  events,
        "count":   len(events),
        "_source": "local_store",
        "_shape":  "brain_history",
    }
    try:
        blob = encrypt_payload(payload, enc_key)
    except Exception:
        return []
    owner_hash = _owner_hash_for_token(api_key)
    return [{
        "key":    f"brain:{owner_hash}:{node_id}:recent",
        "ttl_s":  BRAIN_CACHE_TTL_SEC,
        "blob":   blob,
    }]


# ── Phase 5: channel adapter config (epic #1032) ────────────────────────────
# Channel adapter configs (Telegram bot tokens, Slack OAuth, Signal phone
# numbers, etc.) live in local DuckDB only. Cloud UI authors them via
# pending_queries actions; the daemon persists the E2E-encrypted blob in
# `channel_config`. Per-provider non-secret status (enabled, last_test_at,
# last_test_ok) gets pushed back to `channels:{owner_hash}:status` on every
# heartbeat so the cloud Channels tab paints from Redis.
#
# Invariant: cloud NEVER sees plaintext tokens. The encrypted blob only ever
# rests in local DuckDB; the cache_push carries STATUS ONLY (per provider).

CHANNEL_STATUS_CACHE_TTL_SEC = 3600

# Action-style pending entries the daemon handles in-process (no /ingest/cache
# POST). Phase 5 added the channel-config actions; Phase 3 of #1032 (alert
# rules) and Phase 4 of #1032 (approvals) extend the set so cloud-authored
# rules and Approve/Deny clicks land in local DuckDB on the next heartbeat
# cycle. Mirrors the cloud-side allowlists used by
# clawmetry-cloud/routes/alerts.py:_enqueue_alert_rule_change and the
# approvals enqueue path.
_PENDING_ACTIONS = frozenset({
    "channel_config_upsert",
    "channel_test",
    "alert_rule_upsert",
    "alert_rule_delete",
    "approval_decision",
})


def _build_channel_config_status_cache_pushes(config: dict) -> list:
    """Build the heartbeat cache_push entries for channel adapter status.

    Returns ``[]`` when:
      - No encryption key configured (status fields are non-secret BUT we
        encrypt by convention so the cloud cache contract is uniform —
        every cache_push blob is ciphertext).
      - The local store has no channel_config rows yet.
      - The local_store import fails.

    Single entry shape:
        {
          key:   "channels:{owner_hash}:status",
          ttl_s: 3600,
          blob:  encrypt_payload({channels: [...], _source: "local_store",
                                   _shape: "channel_config_status"}, key),
        }

    The ``channels`` payload is a list of per-provider status dicts —
    NEVER the encrypted config blob. Plaintext tokens NEVER traverse the
    wire, even encrypted, on this key.
    """
    enc_key = config.get("encryption_key")
    if not enc_key:
        return []
    api_key = config.get("api_key", "")
    node_id = config.get("node_id", "")
    if not (api_key and node_id):
        return []
    try:
        from clawmetry import local_store
    except Exception:
        return []
    try:
        store = local_store.get_store(read_only=True)
        rows = store.query_channel_config_status()
    except Exception:
        return []
    if not rows:
        return []
    channels = []
    for r in rows:
        channels.append({
            "provider":        r.get("provider"),
            "enabled":         bool(r.get("enabled")) if r.get("enabled") is not None else False,
            "last_test_at":    r.get("last_test_at"),
            "last_test_ok":    r.get("last_test_ok"),
            "last_test_error": r.get("last_test_error"),
            "updated_at":      r.get("updated_at"),
        })
    payload = {
        "channels": channels,
        "count":    len(channels),
        "_source":  "local_store",
        "_shape":   "channel_config_status",
    }
    try:
        blob = encrypt_payload(payload, enc_key)
    except Exception:
        return []
    owner_hash = _owner_hash_for_token(api_key)
    return [{
        "key":   f"channels:{owner_hash}:status",
        "ttl_s": CHANNEL_STATUS_CACHE_TTL_SEC,
        "blob":  blob,
    }]


# ── Phase 3: proactive alert-rules cache_push (epic #1032) ───────────────────
# Alert rules live in local DuckDB after Phase 3 — the cloud UI authors them,
# the relay's pending_queries channel pipes them into the local store, and the
# evaluator (in-process daemon) reads from DuckDB. To keep the cloud Alerts
# tab paint-fast, we also push the current rule list to the cloud cache on
# every heartbeat under `alerts:{owner_hash}:rules`.
#
# Why a flat (no node) key: alert rules are owner-scoped, not node-scoped — a
# user with three nodes sees one rules list across all of them. Cloud-side
# read path uses the same key shape (see clawmetry-cloud routes/alerts.py).
#
# TTL: 3600s. Each heartbeat overwrites the entry, so TTL only matters when
# the daemon goes offline.
ALERT_RULES_CACHE_TTL_SEC = 3600
ALERT_RULES_CACHE_LIMIT = 500


def _build_alert_rules_cache_pushes(config: dict) -> list:
    """Return the heartbeat `cache_pushes` array for alert rules — currently
    a single entry holding the full enabled+disabled rule list owned by this
    cm_ token.

    Returns an empty list when:
      - The local store has no alert rules yet (no cloud has authored any).
      - Encryption key is unset — we never push plaintext.
      - The local store import fails — degrade silently.

    The blob shape mirrors `/api/alerts/rules` so the cloud read path can
    hand the decrypted dict straight to the existing dashboard JS.
    """
    enc_key = config.get("encryption_key")
    if not enc_key:
        return []
    api_key = config.get("api_key", "")
    if not api_key:
        return []
    try:
        from clawmetry import local_store
    except Exception:
        return []
    owner_hash = _owner_hash_for_token(api_key)
    try:
        store = local_store.get_store(read_only=True)
        # Filter by owner_hash so a multi-tenant local store (rare today, but
        # cheap to be correct about) only pushes the calling token's rules.
        rows = store.query_alert_rules(
            owner_hash=owner_hash, limit=ALERT_RULES_CACHE_LIMIT
        )
    except Exception:
        return []
    if not rows:
        return []
    # Same shape `/api/alerts/rules` returns when the local-store fast path
    # is enabled — cloud Alerts tab + integration tests can compare against
    # this without translation.
    payload = {
        "rules":   rows,
        "count":   len(rows),
        "_source": "local_store",
        "_shape":  "alert_rules",
    }
    try:
        blob = encrypt_payload(payload, enc_key)
    except Exception:
        return []
    return [{
        "key":    f"alerts:{owner_hash}:rules",
        "ttl_s":  ALERT_RULES_CACHE_TTL_SEC,
        "blob":   blob,
    }]


def _dispatch_pending_action(config: dict, action: dict) -> None:
    """Handle a single action-style pending entry. Routes by ``type``.

    Supported types (union across phases of epic #1032):

      * ``channel_config_upsert`` (Phase 5) — cloud-submitted channel
        adapter config → local DuckDB ``channel_config`` table.
      * ``channel_test`` (Phase 5) — run upstream-adapter test + stamp
        the result back into ``channel_config``.
      * ``alert_rule_upsert`` (Phase 3) — cloud-authored alert rule →
        ``alert_rules`` table via ``ingest_alert_rule``.
      * ``alert_rule_delete`` (Phase 3) — delete one alert rule by id.
      * ``approval_decision`` (Phase 4) — flip a row in ``approvals``
        from ``pending`` to approved/denied based on a cloud-relayed
        click. Idempotent — the approvals watcher polls for the new
        status and unblocks the agent.

    Unknown / malformed types are silently dropped (defensive — cloud
    should already have filtered). Per-action errors are logged but never
    raise — one bad action must not block the heartbeat batch."""
    atype = action.get("type")
    if atype not in _PENDING_ACTIONS:
        return
    if atype == "channel_config_upsert":
        _action_channel_config_upsert(config, action)
        return
    if atype == "channel_test":
        _action_channel_test(config, action)
        return
    if atype in ("alert_rule_upsert", "alert_rule_delete"):
        _apply_pending_write(atype, action)
        return
    if atype == "approval_decision":
        _apply_approval_decision(action)
        return


def _action_channel_config_upsert(config: dict, action: dict) -> None:
    """Persist a cloud-submitted channel adapter config to local DuckDB.

    Wire shape (mirrors the cloud-side relay POST):
        {type: "channel_config_upsert", provider, encrypted_blob, enabled}

    ``encrypted_blob`` is the user-key-encrypted config (bot token, OAuth
    secret, etc.) — base64url-encoded over the wire, decoded to bytes
    before storage. The cloud relay strips any plaintext fields before
    queueing; the daemon does NOT decrypt either, just stores. The local
    adapter binary picks the ciphertext up out-of-band when it actually
    needs to dial the upstream provider."""
    provider = (action.get("provider") or "").strip().lower()
    if not provider:
        log.warning("channel_config_upsert: missing provider")
        return
    blob_raw = action.get("encrypted_blob")
    enabled = action.get("enabled")
    blob_bytes = None
    if blob_raw is not None:
        if isinstance(blob_raw, (bytes, bytearray)):
            blob_bytes = bytes(blob_raw)
        elif isinstance(blob_raw, str):
            # Cloud sends base64url (matches encrypt_payload output). Accept
            # std base64 too; raw plaintext-only string falls back to utf-8.
            import base64 as _b64
            try:
                blob_bytes = _b64.urlsafe_b64decode(blob_raw + "==")
            except Exception:
                try:
                    blob_bytes = _b64.b64decode(blob_raw + "==")
                except Exception:
                    blob_bytes = blob_raw.encode("utf-8")
        else:
            log.warning("channel_config_upsert: bad blob type %s", type(blob_raw))
            return
    try:
        from clawmetry import local_store
    except Exception as e:
        log.warning("channel_config_upsert: local_store import failed: %s", e)
        return
    try:
        local_store.get_store().ingest_channel_config(
            provider=provider,
            encrypted_blob=blob_bytes,
            enabled=bool(enabled) if enabled is not None else None,
            status_meta=None,
        )
        log.info("channel_config_upsert provider=%s enabled=%s blob_bytes=%s",
                 provider, enabled, len(blob_bytes) if blob_bytes else 0)
    except Exception as e:
        log.warning("channel_config_upsert ingest failed (provider=%s): %s",
                    provider, e)


def _action_channel_test(config: dict, action: dict) -> None:
    """Run a local test of the channel adapter and stamp the result.

    Wire shape: ``{type: "channel_test", provider}``.

    The actual upstream ping (Telegram getMe, Slack auth.test, ...) is
    delegated to ``_run_channel_test_local``. We persist the result via
    ``ingest_channel_config`` with status_meta only — the blob remains
    untouched. Status flows back to cloud on the next heartbeat
    cache_push."""
    provider = (action.get("provider") or "").strip().lower()
    if not provider:
        log.warning("channel_test: missing provider")
        return
    try:
        from clawmetry import local_store
    except Exception as e:
        log.warning("channel_test: local_store import failed: %s", e)
        return
    ok, err = _run_channel_test_local(config, provider)
    try:
        local_store.get_store().ingest_channel_config(
            provider=provider,
            encrypted_blob=None,
            enabled=None,
            status_meta={
                "last_test_at": time.strftime(
                    "%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "last_test_ok": bool(ok),
                "last_test_error": (err or "")[:240] if not ok else "",
            },
        )
        log.info("channel_test provider=%s ok=%s", provider, ok)
    except Exception as e:
        log.warning("channel_test status persist failed (provider=%s): %s",
                    provider, e)


def _run_channel_test_local(config: dict, provider: str):
    """Run the upstream ping for ``provider``. Returns (ok, error_msg|None).

    For Phase 5 this is a minimal stub: it confirms an encrypted blob
    exists in the local store (proof the user has actually configured
    the provider) and returns success. Actual provider-specific upstream
    pings (Telegram getMe, Slack auth.test, …) are owned by the OpenClaw
    adapter binary — bridging them here would duplicate decryption surface
    unnecessarily and weaken the "cloud never sees plaintext, daemon
    never decrypts" invariant. The adapter binary writes its own real
    test results back via the gateway in a follow-up phase."""
    try:
        from clawmetry import local_store
    except Exception as e:
        return False, f"local_store unavailable: {e}"
    try:
        # Daemon owns the writer; using the same RW handle for the read
        # avoids the "cannot open RO when file doesn't exist yet" edge case
        # on first-channel-test-before-any-config.
        rows = local_store.get_store().query_channel_configs(
            provider=provider, limit=1)
    except Exception as e:
        return False, f"local-store read failed: {e}"
    if not rows:
        return False, "not configured"
    blob = rows[0].get("config_json_encrypted")
    if blob is None or (isinstance(blob, (bytes, bytearray)) and len(blob) == 0):
        return False, "config blob empty"
    return True, None


# ── Phase 4: proactive approvals cache_push (epic #1032) ─────────────────────
# Approvals are now authoritative in local DuckDB — the policy watcher writes
# the row, the daemon pushes the pending-queue snapshot to the cloud cache on
# every heartbeat under `approvals:{owner_hash}:queue`, and the cloud Approvals
# inbox paints from cache (no Cloud SQL row).
#
# TTL is short (60s) so the inbox stays close to real time even between
# heartbeats — acceptance criterion is "appears in cloud inbox within 2s",
# which the cache_push interval (60s default) bounds at the upper end and the
# next heartbeat overwrites at the lower end. A request that arrives BETWEEN
# heartbeats is still visible at next-heartbeat-cache-write; the 60s TTL just
# protects against a daemon that goes silent.
APPROVALS_CACHE_TTL_SEC = 60
APPROVALS_CACHE_LIMIT = 200


def _build_approvals_cache_pushes(config: dict) -> list:
    """Return the heartbeat `cache_pushes` array for pending approvals —
    a single entry holding the current pending queue owned by this cm_ token.

    Returns an empty list when:
      - The local store has no pending approvals (the cloud inbox correctly
        renders empty in that case — no push needed).
      - Encryption key is unset — we never push plaintext.
      - The local store import fails — degrade silently.

    The blob shape mirrors `/api/cloud/approvals` (cloud-side list endpoint)
    so the cloud read path can return the decrypted dict straight to the
    dashboard JS without translation."""
    enc_key = config.get("encryption_key")
    if not enc_key:
        return []
    api_key = config.get("api_key", "")
    if not api_key:
        return []
    try:
        from clawmetry import local_store
    except Exception:
        return []
    owner_hash = _owner_hash_for_token(api_key)
    try:
        store = local_store.get_store(read_only=True)
        rows = store.query_approvals(
            owner_hash=owner_hash,
            status="pending",
            limit=APPROVALS_CACHE_LIMIT,
        )
    except Exception:
        return []
    if not rows:
        return []
    payload = {
        "approvals": rows,
        "count":     len(rows),
        "_source":   "local_store",
        "_shape":    "approvals_queue",
    }
    try:
        blob = encrypt_payload(payload, enc_key)
    except Exception:
        return []
    return [{
        "key":    f"approvals:{owner_hash}:queue",
        "ttl_s":  APPROVALS_CACHE_TTL_SEC,
        "blob":   blob,
    }]


def _dispatch_pending_queries(config: dict, pending: list) -> None:
    """Run each cloud-requested query against the local store, encrypt the
    result, and POST back to /ingest/cache. Failures on individual queries
    are swallowed (logged) so one bad query never blocks the rest.

    Two flavors of pending entry are recognized:

    1. ``{shape, id, cache_key, args}`` — read query. Dispatched via
       routes.local_query (or fallback) and the result is encrypted +
       POSTed to /ingest/cache.
    2. ``{type, …}`` — local action (write or side-effect). Routed
       through ``_dispatch_pending_action``. The unified ``_PENDING_ACTIONS``
       allowlist covers Phase 5 channel-config actions
       (``channel_config_upsert``, ``channel_test``), Phase 3 alert-rule
       writes (``alert_rule_upsert``, ``alert_rule_delete``), and Phase 4
       approval decisions (``approval_decision``). Writes are
       fire-and-forget — no /ingest/cache POST; the next heartbeat's
       cache_push surfaces the new state to the cloud.
    """
    try:
        from routes.local_query import _dispatch as _local_dispatch  # type: ignore
    except Exception:
        _local_dispatch = _local_dispatch_fallback
    api_key = config.get("api_key", "")
    enc_key = config.get("encryption_key")
    node_id = config.get("node_id", "")
    for q in pending or []:
        try:
            if not isinstance(q, dict):
                continue
            # Action-style entry (epic #1032 Phase 5 onwards): no shape,
            # has a `type`. Dispatched locally; no /ingest/cache POST —
            # the next heartbeat's cache_push carries the new state.
            qtype = q.get("type")
            if qtype:
                try:
                    _dispatch_pending_action(config, q)
                except Exception as e:
                    log.warning("pending_action dispatch failed (type=%s): %s",
                                qtype, e)
                continue
            shape = q.get("shape")
            if shape not in _PENDING_SHAPES:
                continue  # defensive — cloud should have already filtered
            qid = q.get("id")
            cache_key = q.get("cache_key")
            args = q.get("args") or {}
            result = _local_dispatch(shape, args)
            if not enc_key:
                log.debug("pending_query %s: no encryption key; skipping", qid)
                continue
            # Bug 2026-05-13 (real MOAT fix): when this pending_query targets
            # the Brain cache key (`brain:*:recent`), the cloud's browser-side
            # `_cm_decryptBrain` reads `dec.events` from the decrypted blob.
            # `_local_dispatch('events', ...)` returns the raw shape
            # `{rows: [...], count, _shape, _via}` though — so the browser
            # sees `dec.events || []` = empty and shows "No brain activity
            # events found" even with hundreds of events in DuckDB. Translate
            # to the dashboard-display shape via `_rows_to_brain_events` so
            # both this writer and `_build_brain_cache_pushes` produce
            # identical blobs (one shouldn't silently overwrite the other
            # with a wrong-shape payload).
            payload = result
            if shape == "events" and isinstance(cache_key, str) \
                    and cache_key.startswith("brain:"):
                rows = (result or {}).get("rows") if isinstance(result, dict) else None
                events = _rows_to_brain_events(rows or [])
                payload = {
                    "events":  events,
                    "count":   len(events),
                    "_source": "local_store",
                    "_shape":  "brain_history",
                }
            blob = encrypt_payload(payload, enc_key)
            _post("/ingest/cache", {
                "node_id": node_id,
                "id": qid,
                "cache_key": cache_key,
                "blob": blob,
                "shape": shape,
                "args_hash": _canonical_args_hash(args),
                "ttl": 3600,
            }, api_key)
        except Exception as e:
            log.warning("pending_query dispatch failed (id=%s shape=%s): %s",
                        (q or {}).get("id") if isinstance(q, dict) else None,
                        (q or {}).get("shape") if isinstance(q, dict) else None,
                        e)


# ── Write-through helper (Phase 3 of #1032) ─────────────────────────────────
# Applies alert-rule writes from the cloud-relayed pending_queries channel to
# the local DuckDB. Dispatched from ``_dispatch_pending_action`` via the
# unified ``_PENDING_ACTIONS`` allowlist. Mirrors the cloud-side enqueue path
# (clawmetry-cloud/routes/alerts.py:_enqueue_alert_rule_change).


def _apply_pending_write(qtype: str, q: dict) -> None:
    """Apply one cloud-authored write to the local DuckDB.

    Routed by ``type``:

      ``alert_rule_upsert`` → ``ingest_alert_rule(body)``
      ``alert_rule_delete`` → ``delete_alert_rule(id)``

    Raises on bad input so the caller's per-item logger flags it. Cloud is
    already responsible for shape validation, so this is defense-in-depth.
    """
    from clawmetry import local_store
    store = local_store.get_store()
    if qtype == "alert_rule_upsert":
        body = q.get("body") or {}
        if not isinstance(body, dict):
            raise ValueError("alert_rule_upsert: body must be a dict")
        # The cloud uses `alert_type` (its own column) — translate into the
        # OSS local-store shape: condition_json holds the whole cloud body so
        # the evaluator + dashboard get everything without a follow-up fetch.
        rule = {
            "id":            body.get("id") or q.get("id"),
            "owner_hash":    body.get("owner_hash"),
            "name":          body.get("name"),
            "condition_json": body,
            "enabled":       body.get("enabled", True),
            "created_at":    body.get("created_at"),
            "updated_at":    body.get("updated_at"),
            "last_fired_at": body.get("last_triggered_at"),
            "fire_count":    body.get("trigger_count") or 0,
        }
        if not rule["id"]:
            raise ValueError("alert_rule_upsert: id required")
        store.ingest_alert_rule(rule)
        log.info("local store: applied alert_rule_upsert id=%s", rule["id"])
        return
    if qtype == "alert_rule_delete":
        rid = q.get("id")
        if not rid:
            raise ValueError("alert_rule_delete: id required")
        n = store.delete_alert_rule(rid)
        log.info("local store: applied alert_rule_delete id=%s (rows=%d)", rid, n)
        return
    # Unknown write — caller already gated via _PENDING_ACTIONS; reaching
    # here means the allowlist was changed without wiring this dispatcher.
    raise ValueError(f"unhandled write type: {qtype}")


def _apply_approval_decision(q: dict) -> None:
    """Flip an approvals row in local DuckDB based on a cloud-relayed
    decision. Used by `_dispatch_pending_queries`.

    Expected shape: ``{type: "approval_decision", id, decision, resolver,
    reason}``. ``id`` and ``decision`` are required; ``resolver`` defaults
    to a cloud-attribution string when unset; ``reason`` is optional.

    Idempotent: ``update_approval_decision`` only flips rows still in
    ``pending`` state, so a duplicate relay delivery is a no-op."""
    approval_id = (q.get("id") or "").strip()
    decision = (q.get("decision") or "").strip()
    if not approval_id or not decision:
        log.warning("approval_decision pending_query missing id/decision: %r", q)
        return
    resolver = (q.get("resolver") or "cloud-relay").strip()
    reason = q.get("reason")
    try:
        from clawmetry import local_store
        store = local_store.get_store()
    except Exception as e:
        log.warning("approval_decision %s: local_store unavailable: %s",
                    approval_id, e)
        return
    try:
        n = store.update_approval_decision(approval_id, decision, resolver,
                                            reason)
    except Exception as e:
        log.warning("approval_decision %s: update failed: %s", approval_id, e)
        return
    if n:
        log.info("[approval] %s relayed decision=%s by %s (status flipped)",
                 approval_id, decision, resolver)
    else:
        # Either unknown id or already decided — both safe to ignore.
        log.debug("[approval] %s relayed decision=%s — no-op (row missing or "
                  "already decided)", approval_id, decision)


def _get_version() -> str:
    try:
        import re

        src = (Path(__file__).parent.parent / "dashboard.py").read_text(
            errors="replace"
        )
        m = re.search(r'^__version__\s*=\s*["\'](.+?)["\']', src, re.M)
        return m.group(1) if m else "unknown"
    except Exception:
        return "unknown"


# ── Daemon loop ────────────────────────────────────────────────────────────────


# Heartbeat interval: re-emit an unchanged cron_state after this many seconds
# so the server's "last seen" TTL doesn't expire the job. See issue #599.
CRON_STATE_HEARTBEAT_SEC = 300  # 5 minutes


def sync_crons(config: dict, state: dict, paths: dict) -> int:
    """Sync cron job definitions to cloud.

    Skipped when the cloud has flagged this account's sync as paused (e.g.
    expired trial). Heartbeats keep firing so we detect upgrade.

    Dedup strategy (issue #599): emit a cron_state event per job only when the
    per-job state hash differs from the last emission, OR when the heartbeat
    interval (CRON_STATE_HEARTBEAT_SEC) has elapsed since the last emission
    for that job. Dedup tracking is persisted in the sync state dict so it
    survives daemon restarts.
    """
    if not _sync_allowed():
        return 0
    _record_sync_progress("crons", 0)
    api_key = config["api_key"]
    node_id = config["node_id"]
    last_hash = state.get("cron_hash", "")
    # Per-job dedup tracking: job_id -> [sha1_hash, last_emit_unix_ts]
    # Stored as list (not tuple) because JSON round-trip turns tuples into lists.
    job_dedup: dict = state.setdefault("cron_state_dedup", {})

    # Find cron jobs.json
    Path.home()
    cron_candidates = [
        Path(_get_openclaw_dir()) / "cron" / "jobs.json",
        Path(_get_openclaw_dir()) / "agents" / "main" / "cron" / "jobs.json",
    ]
    cron_file = next((str(p) for p in cron_candidates if p.exists()), None)
    if not cron_file:
        return 0

    try:
        import hashlib

        raw = open(cron_file, "rb").read()
        h = hashlib.md5(raw).hexdigest()
        file_unchanged = h == last_hash
        data = json.loads(raw)
        jobs = data.get("jobs", []) if isinstance(data, dict) else data

        now_ts = time.time()
        events = []
        emitted_job_ids: list = []
        for j in jobs:
            sched = j.get("schedule", {})
            kind = sched.get("kind", "")
            expr = (
                sched.get("interval", "")
                if kind == "interval"
                else (
                    f"at {sched.get('at', '')}"
                    if kind == "at"
                    else sched.get("cron", "")
                    if kind == "cron"
                    else ""
                )
            )
            job_state = j.get("state", {})
            job_id = j.get("id", "")
            event_data = {
                "job_id": job_id,
                "name": j.get("name", ""),
                "enabled": j.get("enabled", True),
                "expr": expr,
                "schedule": sched,
                "task": (j.get("task") or "")[:200],
                "state": {
                    "lastStatus": job_state.get("lastStatus"),
                    "lastRunAtMs": job_state.get("lastRunAtMs"),
                    "nextRunAtMs": job_state.get("nextRunAtMs"),
                    "lastDurationMs": job_state.get("lastDurationMs"),
                    "lastError": job_state.get("lastError"),
                    "consecutiveFailures": job_state.get("consecutiveFailures"),
                },
            }

            # Dedup: sha1 over the full event payload with sorted keys so the
            # hash is stable across poll iterations when nothing changed.
            job_hash = hashlib.sha1(
                json.dumps(event_data, sort_keys=True).encode("utf-8")
            ).hexdigest()
            prev = job_dedup.get(job_id) or [None, 0.0]
            prev_hash = prev[0] if len(prev) >= 1 else None
            prev_ts = prev[1] if len(prev) >= 2 else 0.0
            changed = job_hash != prev_hash
            stale = (now_ts - float(prev_ts or 0.0)) >= CRON_STATE_HEARTBEAT_SEC
            if not changed and not stale:
                continue

            events.append(
                {
                    "type": "cron_state",
                    "session_id": "",
                    "data": event_data,
                }
            )
            emitted_job_ids.append((job_id, job_hash))

            # Local-store write-through (epic #964 / DuckDB MOAT). Mirrors
            # what we just emitted to cloud — the dashboard's
            # /api/local/* path reads from `crons` table directly so this
            # has to land BEFORE cloud sync acks. Failures are logged
            # but non-fatal: legacy gateway-fetch path still works.
            try:
                from clawmetry import local_store as _ls
                _ls.get_store().ingest_cron({
                    "cron_id":     job_id,
                    "agent_type":  "openclaw",
                    "name":        j.get("name", ""),
                    "schedule":    expr,
                    "enabled":     bool(j.get("enabled", True)),
                    "last_run_at": str(job_state.get("lastRunAtMs") or ""),
                    "last_status": str(job_state.get("lastStatus") or ""),
                    "next_run_at": str(job_state.get("nextRunAtMs") or ""),
                    # All other freeform fields go into the BLOB
                    "task":        (j.get("task") or "")[:500],
                    "lastDurationMs":      job_state.get("lastDurationMs"),
                    "lastError":           job_state.get("lastError"),
                    "consecutiveFailures": job_state.get("consecutiveFailures"),
                })
            except Exception as _e:
                log.debug("local_store: ingest_cron failed for %s: %s",
                          job_id, _e)

        if events:
            _post("/api/ingest", {"events": events, "node_id": node_id}, api_key)
            # Only record new hashes/timestamps after the POST succeeds so a
            # transient ingest failure re-emits next cycle.
            for job_id, job_hash in emitted_job_ids:
                job_dedup[job_id] = [job_hash, now_ts]
            state["cron_hash"] = h
            _record_sync_progress("crons", len(events), len(events))
            return len(events)
        elif not file_unchanged:
            # File mtime/content changed but every job was deduped — still
            # record the new file hash so we don't re-parse it next tick.
            state["cron_hash"] = h
    except Exception as e:
        log.warning(f"Cron sync error: {e}")
    _record_sync_progress("crons", 0, 0)
    return 0


# ── Cron-run JSONL → DuckDB ingest (issue #605 DuckDB follow-up) ─────────
#
# OpenClaw's cron writer appends one JSON record per run to
# ``~/.openclaw/cron/runs/<jobId>.jsonl``. PR #1147 had the dashboard route
# parse those files on every request; this helper moves the parse into the
# sync daemon so the API can read from columnar DuckDB instead.
#
# Per-file offset tracking lives under ``state["cron_run_offsets"]`` so the
# daemon only re-reads new bytes each cycle. Offsets that point past the
# current file size (post-rotation, truncation) reset to 0 — the
# ``INSERT OR IGNORE`` on the cron_runs table makes the catch-up scan a
# no-op for already-stored rows.
#
# The function is deliberately resilient: any per-file or per-line failure
# is logged at debug level and skipped, never raised. ClawMetry is
# read-only-by-default; a malformed cron jsonl line must not break the
# rest of the sync cycle.


def _cron_run_dirs() -> list[Path]:
    """Candidate ``cron/runs`` directories, in resolution order. Mirrors
    ``routes/crons.py:_resolve_cron_runs_jsonl`` so the daemon picks up the
    same files the API would have read.
    """
    roots: list[str] = []
    data_dir = os.environ.get("OPENCLAW_DATA_DIR", "").strip()
    if data_dir:
        roots.append(os.path.expanduser(data_dir))
    home = os.environ.get("OPENCLAW_HOME", "").strip()
    if home:
        roots.append(os.path.expanduser(home))
    roots.append(_get_openclaw_dir())
    roots.append(os.path.expanduser("~/.clawdbot"))
    out: list[Path] = []
    seen: set[str] = set()
    for r in roots:
        p = Path(r) / "cron" / "runs"
        rp = str(p)
        if rp in seen:
            continue
        seen.add(rp)
        if p.exists() and p.is_dir():
            out.append(p)
    return out


def _parse_cron_run_line(line: str, job_id: str, node_id: str) -> dict | None:
    """Parse one JSONL line into the ``LocalStore.ingest_cron_run`` shape.

    Returns ``None`` on malformed JSON or non-dict payloads. The local
    store dedups by ``id``; when the writer didn't supply one we
    synthesise it from ``job_id`` + ``started_at`` so re-reads remain
    idempotent.
    """
    line = line.strip()
    if not line:
        return None
    try:
        obj = json.loads(line)
    except Exception:
        return None
    if not isinstance(obj, dict):
        return None
    # Field-name normalisation matches the older
    # ``routes/crons.py:_read_cron_run_lines`` so OpenClaw writers shipped
    # by every gateway version round-trip cleanly.
    started_at = (
        obj.get("started_at")
        or obj.get("startedAt")
        or obj.get("ts")
        or obj.get("timestamp")
    )
    ended_at = obj.get("ended_at") or obj.get("endedAt")
    duration_ms = obj.get("duration_ms") or obj.get("durationMs") or obj.get("duration")
    status = obj.get("status") or obj.get("result") or "unknown"
    err = obj.get("error") or obj.get("err") or obj.get("error_message") or ""
    if err and not isinstance(err, str):
        err = str(err)
    usage = obj.get("usage") if isinstance(obj.get("usage"), dict) else {}
    token_count = (
        obj.get("token_count")
        or obj.get("tokens")
        or (usage.get("total_tokens") if isinstance(usage, dict) else None)
        or (usage.get("totalTokens") if isinstance(usage, dict) else None)
    )
    cost_usd = obj.get("cost_usd") or obj.get("costUsd")
    delivered_at = obj.get("delivered_at") or obj.get("deliveredAt")
    if not delivered_at and isinstance(obj.get("deliveryStatus"), dict):
        delivered_at = obj["deliveryStatus"].get("deliveredAt")
    next_run_at = (
        obj.get("next_run_at")
        or obj.get("nextRunAt")
        or obj.get("nextRunAtMs")
    )
    # Coerce timestamps to ISO strings — the DuckDB column is VARCHAR
    # because the gateway writer hasn't been consistent about epoch-ms
    # vs ISO-8601 (issue #605 has examples of both). Keeping the column
    # opaque lets us re-parse on read without a schema change.
    def _norm_ts(v: Any) -> str | None:
        if v is None:
            return None
        if isinstance(v, (int, float)):
            return str(int(v))
        return str(v)
    rid = obj.get("id") or obj.get("run_id") or obj.get("runId")
    if not rid:
        rid = f"{job_id}:{_norm_ts(started_at) or ''}"
    run = {
        "id": str(rid),
        "node_id": node_id,
        "job_id": job_id,
        "agent_type": "openclaw",
        "started_at": _norm_ts(started_at),
        "ended_at": _norm_ts(ended_at),
        "duration_ms": duration_ms,
        "status": str(status) if status is not None else None,
        "error_message": err,
        "token_count": token_count,
        "cost_usd": cost_usd,
        "delivered_at": _norm_ts(delivered_at),
        "next_run_at": _norm_ts(next_run_at),
        "raw_jsonl_line": line[:8000],
        # Preserve the freeform payload (usage dict, gateway extras) so
        # ``query_cron_runs`` callers can introspect input/output token
        # splits without losing fidelity.
        "usage": usage,
    }
    return run


def sync_cron_runs(config: dict, state: dict, paths: dict) -> int:
    """Ingest new lines from ``~/.openclaw/cron/runs/*.jsonl`` into
    ``cron_runs`` in the local DuckDB store.

    Returns the number of rows newly ingested. Idempotent: lines already
    in the table (matched on the synthesised ``id``) are skipped by the
    ``ON CONFLICT DO NOTHING`` clause in ``LocalStore.ingest_cron_run``.
    Per-file byte offsets are persisted in ``state["cron_run_offsets"]``
    so subsequent cycles only read appended bytes.

    Failure modes (all degrade silently):
      * ``local_store`` not importable → return 0, no state mutation.
      * ``~/.openclaw/cron/runs`` missing → return 0.
      * Single file unreadable / line malformed → skip that file/line,
        keep going.
    """
    try:
        from clawmetry import local_store as _ls
    except Exception as e:
        log.debug("sync_cron_runs: local_store unavailable: %s", e)
        return 0

    node_id = config.get("node_id", "") if isinstance(config, dict) else ""
    offsets: dict = state.setdefault("cron_run_offsets", {})
    runs_dirs = _cron_run_dirs()
    if not runs_dirs:
        return 0

    try:
        store = _ls.get_store()
    except Exception as e:
        log.debug("sync_cron_runs: get_store failed: %s", e)
        return 0

    n_ingested = 0
    for runs_dir in runs_dirs:
        try:
            jsonl_files = sorted(runs_dir.glob("*.jsonl"))
        except OSError:
            continue
        for fpath in jsonl_files:
            try:
                job_id = fpath.stem  # filename without ``.jsonl``
                if not job_id:
                    continue
                # Per-file offset key includes the parent dir so two
                # candidate roots don't collide on the same jobId.
                key = f"{runs_dir}/{fpath.name}"
                last_offset = int(offsets.get(key, 0))
                try:
                    size = fpath.stat().st_size
                except OSError:
                    continue
                # Truncation / rotation guard: an offset past EOF means
                # the file was rewritten — reset to 0 and rely on
                # INSERT OR IGNORE for dedup.
                if last_offset > size:
                    last_offset = 0
                if last_offset == size:
                    continue
                with open(fpath, "r", errors="replace") as fh:
                    fh.seek(last_offset)
                    for line in fh:
                        run = _parse_cron_run_line(line, job_id, node_id)
                        if run is None:
                            continue
                        try:
                            store.ingest_cron_run(run)
                            n_ingested += 1
                        except Exception as e_in:
                            log.debug(
                                "sync_cron_runs: ingest failed for %s: %s",
                                job_id, e_in,
                            )
                    new_offset = fh.tell()
                offsets[key] = new_offset
            except Exception as e_f:
                log.debug("sync_cron_runs: file %s failed: %s", fpath, e_f)
                continue
    if n_ingested:
        log.debug("sync_cron_runs: ingested %d new rows", n_ingested)
    return n_ingested


def sync_session_metadata(config: dict, state: dict = None) -> int:
    """Sync OpenClaw session metadata rows to cloud sessions table.

    Skipped when the cloud has flagged sync as paused (expired trial).
    Heartbeats continue so the daemon detects the moment the user upgrades.

    Uses mtime tracking to only re-parse files that changed since last sync.
    Reads JSONL session files directly (HTTP API returns HTML, not JSON).
    Extracts session_id, model, timestamps from the event stream.
    """
    if not _sync_allowed():
        return 0
    _record_sync_progress("session_metadata", 0)
    api_key = config["api_key"]
    node_id = config["node_id"]
    if state is None:
        state = {}
    last_mtimes: dict = state.setdefault("session_mtimes", {})
    try:
        Path.home()
        sessions_candidates = [
            Path(_get_openclaw_dir()) / "agents" / "main" / "sessions",
            Path("/data/agents/main/sessions"),
        ]
        sessions_dir = next((p for p in sessions_candidates if p.exists()), None)
        if not sessions_dir:
            return 0

        # Sort by mtime descending so the newest files are processed and
        # uploaded first — the user sees today's sessions in the cloud
        # dashboard within seconds, and older history backfills over the
        # rest of the cycle. Previously a lexical sort + [-100:] slice
        # gave a non-deterministic sample of files and silently dropped
        # the rest. mtime-skip below keeps subsequent syncs cheap.
        jsonl_files = []
        for fpath_str in _list_session_jsonls(sessions_dir):
            fpath = Path(fpath_str)
            try:
                jsonl_files.append((fpath, fpath.stat().st_mtime))
            except OSError:
                continue
        jsonl_files.sort(key=lambda pair: pair[1], reverse=True)

        # Resolve a default model up front from sessions.json (the
        # canonical source). If absent we fall back to a running mode of
        # models actually seen during the parse — the count is updated
        # as batches flush, so later batches benefit from a stronger
        # signal at the cost of slightly less consistent fallback.
        _default_model = ""
        _sid_to_key: dict[str, str] = {}  # sessionId → session key (for channel info)
        _sid_to_meta: dict[str, dict] = {}  # sessionId → {provider, chatType, subject}
        _idx_path = sessions_dir / "sessions.json"
        if _idx_path.exists():
            try:
                with open(_idx_path) as _fi:
                    _idx = json.load(_fi)
                for _k, _meta in _idx.items():
                    if isinstance(_meta, dict):
                        _sid = _meta.get("sessionId", "")
                        if _sid:
                            _sid_to_key[_sid] = _k
                            _sid_to_meta[_sid] = {
                                "provider": _meta.get("provider", ""),
                                "chatType": _meta.get("chatType", ""),
                                "subject": _meta.get("subject") or _meta.get("displayName") or "",
                            }
                        if "subagent" not in _k:
                            _m = (_meta.get("model") or "").strip()
                            if _m and not _default_model:
                                _default_model = _m
            except Exception:
                pass
        model_counts: dict = {}

        def _flush(rows):
            if not rows:
                return 0
            fallback = _default_model
            if not fallback and model_counts:
                fallback = max(model_counts.items(), key=lambda kv: kv[1])[0]
            if fallback:
                for s in rows:
                    if not s.get("model"):
                        s["model"] = fallback
            # Local-first: write through to ~/.clawmetry/events.duckdb FIRST.
            # Best-effort — never blocks cloud sync on a local-store failure.
            try:
                _local_ingest_sessions_batch(rows, node_id)
            except Exception as _e:
                log.warning("local-store sessions ingest failed (cloud sync continues): %s", _e)
            _post("/ingest/sessions", {"node_id": node_id, "sessions": rows}, api_key)
            return len(rows)

        batch: list = []
        total_uploaded = 0
        BATCH_SIZE = 50
        for fpath, current_mtime in jsonl_files:
            if last_mtimes.get(fpath.name) == current_mtime:
                continue
            try:
                # `<uuid>.jsonl` -> stem is `<uuid>`. For an archived
                # `<uuid>.jsonl.reset.<ts>` Path.stem only strips the last
                # extension (.<ts>), leaving `<uuid>.jsonl.reset`. Split on
                # the first `.jsonl` instead so live and reset archives
                # both map to the same canonical session_id.
                sid = fpath.name.split(".jsonl", 1)[0]
                started_at = ""
                updated_at = ""
                total_tokens = 0
                total_cost = 0.0
                label = ""
                # Aggregate model usage across the session — a single session
                # can span several models (model_change mid-conversation, or
                # an orchestrator that routes to different backends). Previously
                # we stored "last model seen," which was arbitrary for multi-
                # model sessions. Now we keep the per-model token count and
                # pick the dominant one as the primary.
                model_tokens: dict = {}
                last_seen_model = ""

                # Scan session file for metadata, tokens, cost, model
                # Read head for start info, scan all for usage, tail for end
                with open(fpath, "r", errors="replace") as f:
                    for raw in f:
                        raw = raw.strip()
                        if not raw:
                            continue
                        try:
                            ev = json.loads(raw)
                        except Exception:
                            continue
                        ts = ev.get("timestamp", "")
                        if not started_at and ts:
                            started_at = ts
                        if ts:
                            updated_at = ts
                        etype = ev.get("type", "")
                        if etype == "model_change" and ev.get("modelId"):
                            last_seen_model = ev["modelId"]
                        elif etype == "session" and ev.get("label"):
                            label = ev["label"]
                        elif etype == "message":
                            msg = ev.get("message", {})
                            msg_model = msg.get("model", "") or last_seen_model
                            usage = msg.get("usage", {})
                            if usage:
                                tks = int(usage.get("totalTokens", 0))
                                total_tokens += tks
                                if msg_model and tks:
                                    model_tokens[msg_model] = model_tokens.get(msg_model, 0) + tks
                                cost_obj = usage.get("cost", {})
                                if isinstance(cost_obj, dict):
                                    total_cost += float(cost_obj.get("total", 0))
                                elif isinstance(cost_obj, (int, float)):
                                    total_cost += float(cost_obj)
                            if msg_model:
                                last_seen_model = msg_model

                # Primary = model that consumed the most tokens in this session,
                # with last_seen_model as a tiebreaker for sessions that had a
                # model_change but no message-level usage yet.
                if model_tokens:
                    model = max(model_tokens.items(), key=lambda kv: kv[1])[0]
                else:
                    model = last_seen_model

                if model:
                    model_counts[model] = model_counts.get(model, 0) + 1
                # Resolve display name from session key when available
                _sk = _sid_to_key.get(sid, "")
                _sm = _sid_to_meta.get(sid, {})
                _dn = label or _sm.get("subject") or _sk or sid[:8]
                batch.append(
                    {
                        "session_id": sid,
                        "display_name": _dn,
                        "session_key": _sk,
                        "channel": _sm.get("provider", ""),
                        "chat_type": _sm.get("chatType", ""),
                        "status": "completed",
                        "model": model,
                        "recent_model": last_seen_model or model,
                        "total_tokens": total_tokens,
                        "total_cost": total_cost,
                        "started_at": started_at,
                        "updated_at": updated_at,
                    }
                )
                last_mtimes[fpath.name] = current_mtime
                if len(batch) >= BATCH_SIZE:
                    total_uploaded += _flush(batch)
                    batch = []
            except Exception as e:
                log.debug(f"Session parse error ({fpath.name}): {e}")

        total_uploaded += _flush(batch)
        _record_sync_progress("session_metadata", total_uploaded, total_uploaded)
        return total_uploaded
    except Exception as e:
        log.warning(f"Session metadata sync failed: {e}")
        _record_sync_progress("session_metadata", 0, 0)
        return 0


def sync_memory(config: dict, state: dict, paths: dict) -> int:
    """Sync memory files (MEMORY.md + memory/*.md) to cloud.

    Skipped when sync is paused (expired trial)."""
    if not _sync_allowed():
        return 0
    _record_sync_progress("memory", 0)
    workspace = paths.get("workspace", "")
    api_key = config["api_key"]
    enc_key = config.get("encryption_key")
    node_id = config["node_id"]
    last_hashes: dict = state.setdefault("memory_hashes", {})
    synced = 0

    # Collect all workspace memory files (same list as OSS dashboard)
    memory_files = []
    for name in [
        "MEMORY.md",
        "SOUL.md",
        "IDENTITY.md",
        "USER.md",
        "AGENTS.md",
        "TOOLS.md",
        "HEARTBEAT.md",
    ]:
        fpath = os.path.join(workspace, name)
        if os.path.isfile(fpath):
            memory_files.append((name, fpath))
    mem_dir = os.path.join(workspace, "memory")
    if os.path.isdir(mem_dir):
        for f in sorted(os.listdir(mem_dir)):
            if f.endswith(".md"):
                memory_files.append((f"memory/{f}", os.path.join(mem_dir, f)))

    if not memory_files:
        _record_sync_progress("memory", 0, 0)
        return 0

    # Check for changes via content hash; always send all file contents so the
    # Memory tab can display any file, not just files changed in the last cycle.
    import hashlib

    changed_files = []
    all_file_contents = []
    file_list = []
    for name, path in memory_files:
        try:
            content_bytes = open(path, "rb").read()
            h = hashlib.md5(content_bytes).hexdigest()
            text = content_bytes.decode("utf-8", errors="replace")
            file_list.append(
                {
                    "name": name,
                    "size": len(content_bytes),
                    "modified": os.path.getmtime(path),
                }
            )
            all_file_contents.append((name, text))
            if h != last_hashes.get(name):
                changed_files.append(name)
                last_hashes[name] = h
        except Exception as e:
            log.debug(f"Memory file read error ({name}): {e}")

    if not changed_files:
        _record_sync_progress("memory", len(memory_files), len(memory_files))
        return 0

    # Push memory files as encrypted blob (like session events).
    # Always include ALL file contents so the Memory tab can render any file.
    payload = {
        "node_id": node_id,
        "memory_state": {"files": file_list},
        "memory_content": [
            {"path": name, "content": content[:100000]}
            for name, content in all_file_contents
        ],
    }
    try:
        # Local-first: write changed memory files to local DuckDB BEFORE cloud.
        # The local store gets PLAINTEXT (it's the user's own machine); cloud
        # gets ciphertext when E2E is on. Best-effort.
        try:
            _local_ingest_memory_files(all_file_contents, changed_files)
        except Exception as _le:
            log.warning("local-store memory ingest failed (cloud sync continues): %s", _le)

        if enc_key:
            from clawmetry.sync import encrypt_payload

            _post(
                "/ingest/memory",
                {
                    "node_id": node_id,
                    "encrypted": True,
                    "blob": encrypt_payload(payload, enc_key),
                },
                api_key,
            )
        else:
            _post("/ingest/memory", payload, api_key)
        synced = len(changed_files)
    except Exception as e:
        log.warning(f"Memory sync error: {e}")

    _record_sync_progress("memory", synced, len(memory_files))
    return synced

    # ── Real-time log streaming ────────────────────────────────────────────────────

    """Build memory file list for the Memory popup."""


# ── BOOTSTRAP.md "First Contact" capture (issue #690) ─────────────────────────
#
# OpenClaw's BOOTSTRAP.md runs once at first startup to negotiate agent identity
# and then SELF-DELETES. We watch for it on every daemon tick and snapshot the
# file (plus the session id active when we saw it) into the local DuckDB
# `bootstrap_archive` table BEFORE OpenClaw removes it. The store is the
# authority — once captured, the artifact is read-only and survives any
# subsequent re-init / workspace move.
#
# Idempotent: `local_store.ingest_bootstrap_archive` dedups on
# (node_id, agent_id, content_sha256), so re-running the capture on an
# unchanged file is a no-op. If OpenClaw rewrites BOOTSTRAP.md with new content
# (re-negotiated identity), a fresh row is inserted, preserving the full
# first-contact history.

_BOOTSTRAP_CANDIDATE_PATHS = (
    # Documented spec location.
    ("agents", "main", "memory", "BOOTSTRAP.md"),
    # Some OpenClaw builds keep the file at the workspace root.
    ("agents", "main", "BOOTSTRAP.md"),
    ("BOOTSTRAP.md",),
)


def _find_bootstrap_file(workspace: str | None = None) -> Path | None:
    """Return the path to a present BOOTSTRAP.md, or None when absent.

    Checks the documented location first, then a couple of fallbacks that
    have been observed in the wild. Returns the first hit — bootstrap files
    don't coexist."""
    bases: list[Path] = [Path(_get_openclaw_dir())]
    if workspace:
        try:
            bases.append(Path(workspace))
        except Exception:
            pass
    for base in bases:
        for parts in _BOOTSTRAP_CANDIDATE_PATHS:
            candidate = base.joinpath(*parts)
            try:
                if candidate.is_file():
                    return candidate
            except OSError:
                continue
    return None


def _latest_session_id(workspace: str | None = None) -> str | None:
    """Best-effort: return the session id of the most-recently-modified
    JSONL transcript when the bootstrap was captured. We link the artifact
    to it so the dashboard can show "First Contact ⇄ first session" together.
    None when no session transcripts exist (bootstrap captured before any
    session, which is the normal first-boot case)."""
    candidates: list[Path] = [
        Path(_get_openclaw_dir()) / "agents" / "main" / "sessions",
    ]
    if workspace:
        try:
            candidates.append(Path(workspace) / "agents" / "main" / "sessions")
        except Exception:
            pass
    for sessions_dir in candidates:
        try:
            if not sessions_dir.is_dir():
                continue
        except OSError:
            continue
        newest_mtime = -1.0
        newest: Path | None = None
        try:
            for p in sessions_dir.iterdir():
                if p.suffix != ".jsonl":
                    continue
                try:
                    mt = p.stat().st_mtime
                except OSError:
                    continue
                if mt > newest_mtime:
                    newest_mtime = mt
                    newest = p
        except OSError:
            continue
        if newest is not None:
            # File name is the session id; strip the suffix.
            return newest.stem
    return None


def capture_bootstrap_if_present(
    config: dict | None = None,
    paths: dict | None = None,
    *,
    store=None,
) -> bool:
    """Daemon tick hook: snapshot BOOTSTRAP.md to the local store when
    present. Returns True when a NEW row was written, False otherwise
    (file absent, unchanged, or write failure — failure is logged but
    never raised, the daemon must keep ticking).

    ``store`` is overridable for tests; defaults to the process-wide
    LocalStore singleton."""
    try:
        config = config or {}
        node_id = config.get("node_id") or ""
        if not node_id:
            # Defensive — run_daemon backfills this on startup. Without it
            # we can't dedup, so skip silently.
            return False
        workspace = ""
        if paths:
            workspace = paths.get("workspace") or ""
        bootstrap_path = _find_bootstrap_file(workspace=workspace)
        if bootstrap_path is None:
            return False
        try:
            content_bytes = bootstrap_path.read_bytes()
        except OSError as e:
            log.warning("bootstrap capture: read failed for %s: %s",
                        bootstrap_path, e)
            return False
        try:
            content = content_bytes.decode("utf-8", errors="replace")
        except Exception:
            content = content_bytes.decode("latin-1", errors="replace")
        if not content.strip():
            # Empty BOOTSTRAP.md is meaningless — wait until OpenClaw fills it.
            return False
        import hashlib
        from datetime import datetime, timezone

        sha = hashlib.sha256(content.encode("utf-8")).hexdigest()
        try:
            mtime_iso = datetime.fromtimestamp(
                bootstrap_path.stat().st_mtime, tz=timezone.utc
            ).isoformat()
        except OSError:
            mtime_iso = None

        # Defer the import so a missing duckdb dep (older installs) doesn't
        # take the daemon down — bootstrap capture is best-effort.
        if store is None:
            try:
                from clawmetry import local_store as _ls
                store = _ls.get_store()
            except Exception as e:
                log.warning("bootstrap capture: local_store unavailable: %s", e)
                return False

        first_session = _latest_session_id(workspace=workspace)
        try:
            wrote = store.ingest_bootstrap_archive({
                "node_id": node_id,
                "agent_id": "main",
                "captured_at": datetime.now(timezone.utc).isoformat(),
                "file_mtime": mtime_iso,
                "content": content,
                "content_sha256": sha,
                "first_session_id": first_session,
                "size_bytes": len(content_bytes),
                "source_path": str(bootstrap_path),
            })
        except Exception as e:
            log.warning("bootstrap capture: ingest failed: %s", e)
            return False
        if wrote:
            log.info(
                "bootstrap capture: archived %s (sha=%s, session=%s)",
                bootstrap_path, sha[:12], first_session or "n/a",
            )
        return wrote
    except Exception as e:
        # Catch-all so a bug in this helper never crashes the daemon loop.
        log.warning("bootstrap capture: unexpected error: %s", e)
        return False


def _build_machine_info():
    """Build machine hardware info for the Machine popup."""
    try:
        import platform, subprocess, socket

        items = []
        items.append(
            {"label": "Hostname", "value": socket.gethostname(), "status": "ok"}
        )
        # IP
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            items.append({"label": "IP", "value": ip, "status": "ok"})
        except Exception:
            items.append({"label": "IP", "value": "unknown", "status": "warning"})
        # CPU
        items.append({"label": "CPU", "value": platform.machine(), "status": "ok"})
        # CPU Cores
        try:
            import multiprocessing

            items.append(
                {
                    "label": "CPU Cores",
                    "value": str(multiprocessing.cpu_count()),
                    "status": "ok",
                }
            )
        except Exception:
            pass
        # Load average
        try:
            load = os.getloadavg()
            items.append(
                {
                    "label": "Load (1/5/15m)",
                    "value": f"{load[0]:.2f} / {load[1]:.2f} / {load[2]:.2f}",
                    "status": "ok",
                }
            )
        except Exception:
            pass
        # GPU
        try:
            gpu = (
                subprocess.check_output(
                    ["nvidia-smi", "--query-gpu=name", "--format=csv,noheader"],
                    timeout=5,
                )
                .decode()
                .strip()
            )
            items.append({"label": "GPU", "value": gpu, "status": "ok"})
        except Exception:
            items.append(
                {"label": "GPU", "value": "N/A (no nvidia-smi)", "status": "ok"}
            )
        # Kernel
        items.append({"label": "Kernel", "value": platform.release(), "status": "ok"})
        return {"items": items}
    except Exception as e:
        log.warning(f"Machine info error: {e}")
        return {"items": []}


def _build_runtime_info():
    """Build runtime environment info for the Runtime popup."""
    try:
        import platform, subprocess

        items = []
        items.append(
            {"label": "Python", "value": platform.python_version(), "status": "ok"}
        )
        items.append(
            {
                "label": "OS",
                "value": f"{platform.system()} {platform.release()}",
                "status": "ok",
            }
        )
        items.append(
            {"label": "Architecture", "value": platform.machine(), "status": "ok"}
        )
        # OpenClaw version
        try:
            oc_ver = (
                subprocess.check_output(
                    ["openclaw", "--version"], stderr=subprocess.STDOUT, timeout=5
                )
                .decode()
                .strip()
            )
            items.append({"label": "OpenClaw", "value": oc_ver, "status": "ok"})
        except Exception:
            items.append({"label": "OpenClaw", "value": "unknown", "status": "warning"})
        # Disk /
        try:
            df = (
                subprocess.check_output(["df", "-h", "/"], timeout=5)
                .decode()
                .strip()
                .split("\n")
            )
            if len(df) >= 2:
                parts = df[1].split()
                pct = int(parts[4].replace("%", ""))
                st = "critical" if pct > 90 else "warning" if pct > 80 else "ok"
                items.append(
                    {
                        "label": "Disk /",
                        "value": f"{parts[2]} / {parts[1]} ({parts[4]} used)",
                        "status": st,
                    }
                )
        except Exception:
            pass
        # Node.js
        try:
            nv = (
                subprocess.check_output(["node", "--version"], timeout=5)
                .decode()
                .strip()
            )
            items.append({"label": "Node.js", "value": nv, "status": "ok"})
        except Exception:
            pass
        return {"items": items}
    except Exception as e:
        log.warning(f"Runtime info error: {e}")
        return {"items": []}


def _build_memory_files(workspace):
    """Build memory file list for the Memory popup."""
    if not workspace or not os.path.isdir(workspace):
        return []
    files = []
    for name in [
        "MEMORY.md",
        "SOUL.md",
        "IDENTITY.md",
        "USER.md",
        "AGENTS.md",
        "TOOLS.md",
        "HEARTBEAT.md",
    ]:
        fpath = os.path.join(workspace, name)
        if os.path.isfile(fpath):
            try:
                st = os.stat(fpath)
                files.append(
                    {"name": name, "size": st.st_size, "modified": st.st_mtime}
                )
            except Exception:
                pass
    mem_dir = os.path.join(workspace, "memory")
    if os.path.isdir(mem_dir):
        for f in sorted(os.listdir(mem_dir)):
            if f.endswith(".md"):
                fpath = os.path.join(mem_dir, f)
                try:
                    st = os.stat(fpath)
                    files.append(
                        {
                            "name": f"memory/{f}",
                            "size": st.st_size,
                            "modified": st.st_mtime,
                        }
                    )
                except Exception:
                    pass
    return files


def _build_brain_data():
    """Build LLM call data for the Brain/AI Model popup."""
    try:
        import collections

        home = str(Path.home())
        session_dir = os.path.join(_get_openclaw_dir(), "agents", "main", "sessions")
        if not os.path.isdir(session_dir):
            return {"stats": {}, "calls": []}

        calls = []
        total_cost = 0.0
        total_tokens_in = 0
        total_tokens_out = 0
        total_cache_read = 0
        total_cache_write = 0
        total_duration = 0
        thinking_calls = 0
        cache_hit_calls = 0
        model_name = "unknown"

        today = datetime.now().strftime("%Y-%m-%d")

        files = sorted(
            glob.glob(os.path.join(session_dir, "*.jsonl")),
            key=os.path.getmtime,
            reverse=True,
        )[:20]

        for fp in files:
            try:
                session_name = os.path.basename(fp).split(".")[0][:12]
                prev_user_ts = None  # for duration calculation
                for line_raw in open(fp, errors="ignore"):
                    try:
                        ev = json.loads(line_raw)

                        # Track user message timestamps for duration calc
                        if ev.get("type") == "message":
                            msg_role = (ev.get("message") or {}).get("role", "")
                            if msg_role == "user":
                                prev_user_ts = ev.get("timestamp")

                        if ev.get("type") != "message":
                            continue
                        msg = ev.get("message", {})
                        role = msg.get("role", "")
                        if role != "assistant":
                            continue

                        usage = msg.get("usage") or ev.get("usage") or {}
                        if not usage:
                            continue

                        ts = ev.get("timestamp", "")
                        if not ts or today not in ts[:10]:
                            continue

                        # OpenClaw JSONL format uses: input/output/cacheRead/cacheWrite/cost.total
                        tok_in = (
                            usage.get("input")
                            or usage.get("inputTokens")
                            or usage.get("input_tokens")
                            or 0
                        )
                        tok_out = (
                            usage.get("output")
                            or usage.get("outputTokens")
                            or usage.get("output_tokens")
                            or 0
                        )
                        cr = (
                            usage.get("cacheRead")
                            or usage.get("cacheReadInputTokens")
                            or usage.get("cache_read_input_tokens")
                            or 0
                        )
                        cw = (
                            usage.get("cacheWrite")
                            or usage.get("cacheCreationInputTokens")
                            or usage.get("cache_creation_input_tokens")
                            or 0
                        )

                        # Use actual cost from usage.cost.total if available, else estimate
                        cost_obj = usage.get("cost", {})
                        if isinstance(cost_obj, dict) and cost_obj.get("total"):
                            cost = float(cost_obj["total"])
                        else:
                            cost = (
                                tok_in * 3 + tok_out * 15 + cr * 0.3 + cw * 3.75
                            ) / 1_000_000

                        # Duration: compute from prev user msg timestamp (durationMs rarely stored)
                        dur_ms = int(
                            ev.get("durationMs", 0) or ev.get("duration_ms", 0) or 0
                        )
                        if not dur_ms and prev_user_ts and ts:
                            try:
                                from datetime import timezone

                                t1 = datetime.fromisoformat(
                                    prev_user_ts.replace("Z", "+00:00")
                                )
                                t2 = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                                d = int((t2 - t1).total_seconds() * 1000)
                                if 0 < d < 300000:
                                    dur_ms = d
                            except Exception:
                                pass

                        has_thinking = False
                        tools_used = []
                        if isinstance(msg.get("content"), list):
                            for c in msg["content"]:
                                if c.get("type") == "thinking":
                                    has_thinking = True
                                elif c.get("type") == "toolCall":
                                    tn = c.get("name", "")
                                    if tn and tn not in tools_used:
                                        tools_used.append(tn)

                        m = msg.get("model") or ev.get("model") or ""
                        if m and m != "unknown":
                            model_name = m.split("/")[-1] if "/" in m else m

                        total_tokens_in += tok_in
                        total_tokens_out += tok_out
                        total_cache_read += cr
                        total_cache_write += cw
                        total_cost += cost
                        total_duration += dur_ms
                        if has_thinking:
                            thinking_calls += 1
                        if cr > 0:
                            cache_hit_calls += 1

                        calls.append(
                            {
                                "timestamp": ts,
                                "session": session_name,
                                "tokens_in": tok_in,
                                "tokens_out": tok_out,
                                "cost": "$" + format(cost, ".4f"),
                                "duration_ms": dur_ms,
                                "thinking": has_thinking,
                                "cache_read": cr,
                                "tools_used": tools_used[:5],
                            }
                        )
                    except Exception:
                        continue
            except Exception:
                continue

        calls.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        calls = calls[:100]

        n = len(calls)
        avg_ms = int(total_duration / n) if n > 0 else 0

        stats = {
            "model": model_name,
            "today_calls": n,
            "today_cost": "$" + format(total_cost, ".2f"),
            "avg_response_ms": avg_ms,
            "thinking_calls": thinking_calls,
            "cache_hits": cache_hit_calls,
            "today_tokens": {
                "input": total_tokens_in,
                "output": total_tokens_out,
                "cache_read": total_cache_read,
                "cache_write": total_cache_write,
            },
        }

        return {"stats": stats, "calls": calls, "total": n}
    except Exception as e:
        log.warning(f"Brain data error: {e}")
        return {"stats": {}, "calls": [], "total": 0}


def _build_tool_stats():
    """Build tool usage stats from recent session logs."""
    try:
        import collections, glob

        home = str(Path.home())
        session_dir = os.path.join(_get_openclaw_dir(), "agents", "main", "sessions")
        if not os.path.isdir(session_dir):
            return {}

        tool_counts = collections.Counter()
        tool_recent = {}  # tool_name -> last few entries
        channel_msgs = collections.defaultdict(
            lambda: {"in": 0, "out": 0, "messages": []}
        )

        today = datetime.now().strftime("%Y-%m-%d")

        # Read last 20 active sessions
        files = sorted(
            glob.glob(os.path.join(session_dir, "*.jsonl")),
            key=os.path.getmtime,
            reverse=True,
        )[:20]

        # Pre-load session-level channel info from sessions.json
        _session_channels = {}
        _sessions_json = os.path.join(session_dir, "sessions.json")
        try:
            with open(_sessions_json) as _sjf:
                _sj = json.load(_sjf)
            for _sk, _sv in _sj.items():
                _sf = os.path.basename(_sv.get("sessionFile", ""))
                _dc = _sv.get("deliveryContext", {}) or {}
                _ori = _sv.get("origin", {}) or {}
                _ch = (
                    _dc.get("channel", "")
                    or _ori.get("provider", "")
                    or _ori.get("surface", "")
                )
                if _sf and _ch:
                    _session_channels[_sf] = _ch
        except Exception:
            pass

        for fp in files:
            _file_channel = _session_channels.get(os.path.basename(fp), "")
            try:
                for line in open(fp, errors="ignore"):
                    try:
                        ev = json.loads(line)
                        if ev.get("type") != "message":
                            continue
                        msg = ev.get("message", {})
                        ts = ev.get("timestamp", "")
                        role = msg.get("role", "")

                        if isinstance(msg.get("content"), list):
                            for c in msg["content"]:
                                if c.get("type") == "toolCall":
                                    name = c.get("name", "?")
                                    tool_counts[name] += 1
                                    args = (
                                        c.get("arguments", {})
                                        or c.get("input", {})
                                        or c.get("args", {})
                                        or {}
                                    )
                                    if isinstance(args, str):
                                        try:
                                            args = json.loads(args)
                                        except:
                                            args = {}

                                    # Track recent entries for specific tools
                                    if name == "web_search":
                                        q = args.get("query", "")
                                        if q and name not in tool_recent:
                                            tool_recent[name] = []
                                        if q:
                                            tool_recent.setdefault(name, []).append(
                                                {"query": q[:200], "ts": ts}
                                            )
                                    elif name == "web_fetch":
                                        url = args.get("url", "")
                                        if url:
                                            tool_recent.setdefault(name, []).append(
                                                {"url": url[:200], "ts": ts}
                                            )
                                    elif name == "browser":
                                        action = args.get("action", "")
                                        url = args.get("url", "")
                                        tool_recent.setdefault(name, []).append(
                                            {
                                                "action": action,
                                                "url": url[:200] if url else "",
                                                "ts": ts,
                                            }
                                        )
                                    elif name == "exec":
                                        cmd = args.get("command", "")
                                        if cmd:
                                            tool_recent.setdefault(name, []).append(
                                                {"command": cmd[:300], "ts": ts}
                                            )
                                    elif name == "message":
                                        target = args.get("target", "") or args.get(
                                            "channel", ""
                                        )
                                        tool_recent.setdefault(name, []).append(
                                            {"target": target, "ts": ts}
                                        )

                        # Track channel messages (inbound + outbound)
                        if role in ("user", "assistant"):
                            text = ""
                            if isinstance(msg.get("content"), str):
                                text = msg["content"][:300]
                            elif isinstance(msg.get("content"), list):
                                for c in msg["content"]:
                                    if c.get("type") == "text":
                                        text = c.get("text", "")[:300]
                                        break

                            # Try to detect channel from metadata, fall back to session-level channel
                            meta = ev.get("metadata", {}) or {}
                            channel = (
                                meta.get("channel", "")
                                or meta.get("surface", "")
                                or _file_channel
                            )
                            if channel and text:
                                direction = "in" if role == "user" else "out"
                                channel_msgs[channel][direction] += 1
                                channel_msgs[channel]["messages"].append(
                                    {
                                        "direction": direction,
                                        "content": text[:200],
                                        "timestamp": ts,
                                        "sender": meta.get("sender", "User")
                                        if role == "user"
                                        else "Agent",
                                    }
                                )
                    except Exception:
                        continue
            except Exception:
                continue

        # Cap recent entries
        for name in tool_recent:
            tool_recent[name] = tool_recent[name][-30:]
            tool_recent[name].reverse()

        for ch in channel_msgs:
            channel_msgs[ch]["messages"] = channel_msgs[ch]["messages"][-30:]
            channel_msgs[ch]["messages"].reverse()

        return {
            "counts": dict(tool_counts.most_common(30)),
            "recent": {k: v for k, v in tool_recent.items()},
            "channelMsgs": dict(channel_msgs),
        }
    except Exception as e:
        log.warning(f"Tool stats error: {e}")
        return {}


def _build_channel_list(config):
    """Build list of configured channels."""
    try:
        str(Path.home())
        oc_config = os.path.join(_get_openclaw_dir(), "openclaw.json")
        if not os.path.isfile(oc_config):
            return []
        data = json.load(open(oc_config))
        channels = []
        ch_section = data.get("channels", {})
        if isinstance(ch_section, dict):
            for key in ch_section:
                channels.append({"name": key, "enabled": True})
        # Also check top-level channel keys
        for key in (
            "telegram",
            "discord",
            "slack",
            "whatsapp",
            "signal",
            "irc",
            "webchat",
            "imessage",
        ):
            if key in data and key not in [c["name"] for c in channels]:
                cfg = data[key]
                if isinstance(cfg, dict):
                    channels.append({"name": key, "enabled": cfg.get("enabled", True)})
        return channels
    except Exception:
        return []


def _build_channel_data(config):
    """Build channel message data from gateway.log (outgoing) + session files (incoming)."""
    import re as _re

    try:
        str(Path.home())
        today = datetime.now().strftime("%Y-%m-%d")
        gw_log = os.path.join(_get_openclaw_dir(), "logs", "gateway.log")
        session_dir = os.path.join(_get_openclaw_dir(), "agents", "main", "sessions")
        channels = {}

        known_channels = {
            "telegram",
            "imessage",
            "whatsapp",
            "signal",
            "discord",
            "slack",
            "webchat",
            "irc",
            "googlechat",
            "msteams",
        }

        # ── Outgoing: parse gateway.log ──────────────────────────────────────
        if os.path.exists(gw_log):
            with open(gw_log, errors="ignore") as f:
                for raw in f:
                    raw = raw.strip()
                    if not raw:
                        continue
                    ts_match = _re.match(r"(\d{4}-\d{2}-\d{2}T[\d:.]+Z)", raw)
                    if not ts_match or today not in ts_match.group(1):
                        continue
                    ts = ts_match.group(1)
                    ch_match = _re.search(r"\[(\w+)\]", raw)
                    if not ch_match:
                        continue
                    ch_name = ch_match.group(1).lower()
                    if ch_name not in known_channels:
                        continue
                    if ch_name not in channels:
                        channels[ch_name] = {
                            "messages": [],
                            "todayIn": 0,
                            "todayOut": 0,
                            "total": 0,
                        }
                    rest = raw[ts_match.end() :].strip()
                    if any(
                        x in rest
                        for x in (
                            "sendMessage ok",
                            "send ok",
                            "delivered",
                            "sendPhoto ok",
                            "sendAudio ok",
                            "sendDocument ok",
                        )
                    ):
                        channels[ch_name]["todayOut"] += 1
                        channels[ch_name]["total"] += 1
                        channels[ch_name]["messages"].append(
                            {
                                "direction": "out",
                                "content": "",
                                "timestamp": ts,
                                "sender": "Diya",
                            }
                        )

        # ── Incoming: parse session JSONL files ──────────────────────────────
        # Telegram sessions contain "message_id" in first user message
        # iMessage sessions contain media paths or iMessage-specific metadata
        if os.path.isdir(session_dir):
            for fname in sorted(os.listdir(session_dir)):
                if not fname.endswith(".jsonl"):
                    continue
                fpath = os.path.join(session_dir, fname)
                try:
                    mtime = datetime.fromtimestamp(os.path.getmtime(fpath)).strftime(
                        "%Y-%m-%d"
                    )
                    if mtime != today:
                        continue
                    detected_ch = None
                    first_user_ts = None
                    first_user_text = ""
                    with open(fpath, errors="ignore") as f2:
                        for line in f2:
                            try:
                                obj = json.loads(line)
                                if (
                                    obj.get("type") == "message"
                                    and obj.get("message", {}).get("role") == "user"
                                ):
                                    content = obj["message"].get("content", "")
                                    text = (
                                        content
                                        if isinstance(content, str)
                                        else " ".join(
                                            c.get("text", "")
                                            for c in content
                                            if isinstance(c, dict)
                                        )
                                    )
                                    if "message_id" in text and "sender_id" in text:
                                        if "imessage" in text.lower() or "+" in text:
                                            detected_ch = "imessage"
                                        else:
                                            detected_ch = "telegram"
                                        first_user_ts = obj.get("timestamp", "")
                                        first_user_text = text[:100]
                                    break
                            except Exception:
                                continue
                    if detected_ch and first_user_ts:
                        if detected_ch not in channels:
                            channels[detected_ch] = {
                                "messages": [],
                                "todayIn": 0,
                                "todayOut": 0,
                                "total": 0,
                            }
                        channels[detected_ch]["todayIn"] += 1
                        channels[detected_ch]["total"] += 1
                        channels[detected_ch]["messages"].append(
                            {
                                "direction": "in",
                                "content": first_user_text,
                                "timestamp": first_user_ts,
                                "sender": "User",
                            }
                        )
                except Exception:
                    continue

        # Cap and reverse (newest first)
        for ch in channels.values():
            ch["messages"] = ch["messages"][-50:]
            ch["messages"].sort(key=lambda x: x.get("timestamp", ""), reverse=True)

        return channels
    except Exception as e:
        log.warning(f"Channel data error: {e}")
        return {}


def _build_cron_jobs(paths):
    """Build cron jobs list for snapshot."""
    import json as _j2

    home = str(Path.home())
    cron_candidates = [
        os.path.join(_get_openclaw_dir(), "cron", "jobs.json"),
        os.path.join(_get_openclaw_dir(), "agents", "main", "cron", "jobs.json"),
    ]
    cron_file = next((p for p in cron_candidates if os.path.isfile(p)), None)
    if not cron_file:
        return []
    try:
        data = _j2.load(open(cron_file))
        jobs = data.get("jobs", []) if isinstance(data, dict) else data
        result = []
        for j in jobs:
            sched = j.get("schedule", {})
            kind = sched.get("kind", "")
            expr = (
                sched.get("interval", "")
                if kind == "interval"
                else (
                    f"at {sched.get('at', '')}"
                    if kind == "at"
                    else sched.get("cron", "")
                    if kind == "cron"
                    else ""
                )
            )
            sched_obj = j.get("schedule", {})
            result.append(
                {
                    "id": j.get("id", ""),
                    "name": j.get("name", ""),
                    "enabled": j.get("enabled", True),
                    "schedule": sched_obj,
                    "task": j.get("task", "")[:200],
                    "state": j.get("state", {}),
                    "lastRun": None,
                    "lastStatus": None,
                }
            )
        return result
    except Exception:
        return []


def sync_system_snapshot(config: dict, state: dict, paths: dict) -> int:
    """Push system info + subagent data as encrypted snapshot.

    Skipped when sync is paused (expired trial)."""
    if not _sync_allowed():
        return 0
    import subprocess, platform, json as _json

    api_key = config["api_key"]
    enc_key = config.get("encryption_key")
    node_id = config["node_id"]
    if not enc_key:
        return 0

    # System info
    system = []
    try:
        disk = (
            subprocess.run(["df", "-h", "/"], capture_output=True, text=True, timeout=5)
            .stdout.strip()
            .split("\n")[-1]
            .split()
        )
        disk_pct = int(disk[4].replace("%", "")) if len(disk) > 4 else 0
        disk_color = (
            "green" if disk_pct < 80 else ("yellow" if disk_pct < 90 else "red")
        )
        system.append(["Disk /", f"{disk[2]} / {disk[1]} ({disk[4]})", disk_color])
    except Exception:
        system.append(["Disk /", "--", ""])
    # Check for additional data drives
    for extra_mount in ["/mnt/data-drive", "/data", "/mnt/data", "/home"]:
        try:
            ed = (
                subprocess.run(
                    ["df", "-h", extra_mount], capture_output=True, text=True, timeout=3
                )
                .stdout.strip()
                .split("\n")[-1]
                .split()
            )
            if len(ed) > 4 and ed[5] != "/":
                ep = int(ed[4].replace("%", ""))
                ec = "green" if ep < 80 else ("yellow" if ep < 90 else "red")
                system.append([f"Disk {ed[5]}", f"{ed[2]} / {ed[1]} ({ed[4]})", ec])
        except Exception:
            pass

    try:
        if sys.platform == "darwin":
            import re as _re

            vm = subprocess.run(
                ["vm_stat"], capture_output=True, text=True, timeout=5
            ).stdout
            pages = {
                m.group(1): int(m.group(2))
                for m in _re.finditer(r'"(.+?)"\s*:\s*(\d+)', vm)
            }
            page_size = 16384
            used = (
                pages.get("Pages active", 0) + pages.get("Pages wired down", 0)
            ) * page_size
            total_raw = subprocess.run(
                ["sysctl", "-n", "hw.memsize"],
                capture_output=True,
                text=True,
                timeout=5,
            ).stdout.strip()
            total = int(total_raw) if total_raw else 0
            system.append(["RAM", f"{used // (1024**3)}G / {total // (1024**3)}G", ""])
        else:
            mem = (
                subprocess.run(
                    ["free", "-h"], capture_output=True, text=True, timeout=5
                )
                .stdout.strip()
                .split("\n")[1]
                .split()
            )
            system.append(["RAM", f"{mem[2]} / {mem[1]}", ""])
    except Exception:
        system.append(["RAM", "--", ""])

    try:
        if sys.platform == "darwin":
            up = subprocess.run(
                ["uptime"], capture_output=True, text=True, timeout=5
            ).stdout.strip()
            system.append(["Uptime", up.split(",")[0].split("up")[-1].strip(), ""])
        else:
            up = subprocess.run(
                ["uptime", "-p"], capture_output=True, text=True, timeout=5
            ).stdout.strip()
            system.append(["Uptime", up.replace("up ", ""), ""])
    except Exception:
        system.append(["Uptime", "--", ""])

    # Gateway status
    try:
        gw = subprocess.run(
            ["pgrep", "-f", "openclaw"], capture_output=True, text=True, timeout=5
        )
        gw_running = gw.returncode == 0
        system.append(
            [
                "Gateway",
                "Running" if gw_running else "Stopped",
                "green" if gw_running else "red",
            ]
        )
    except Exception:
        system.append(["Gateway", "--", ""])

    # Infra
    uname = platform.uname()
    infra = {
        "machine": uname.node,
        "runtime": f"Node.js - {uname.system} {uname.release.split('-')[0]}",
        "storage": system[0][1] if system else "--",
    }

    # Session info
    sessions_dir = paths.get("sessions_dir", "")
    session_count = 0
    model_name = ""
    main_tokens = 0
    subagents_list = []
    active_count = 0

    index_path = os.path.join(sessions_dir, "sessions.json") if sessions_dir else ""
    if index_path and os.path.isfile(index_path):
        try:
            with open(index_path) as f:
                index = _json.load(f)
            now_ms = time.time() * 1000
            for key, meta in index.items():
                if not isinstance(meta, dict):
                    continue
                session_count += 1
                if ":subagent:" in key:
                    age_ms = now_ms - meta.get("updatedAt", 0)
                    status = (
                        "active"
                        if age_ms < 120000
                        else ("idle" if age_ms < 3600000 else "stale")
                    )
                    if status == "active":
                        active_count += 1
                    subagents_list.append(
                        {
                            "label": meta.get("label", key.split(":")[-1][:12]),
                            "status": status,
                            "model": meta.get("model", ""),
                            "task": meta.get("task", "")[:100],
                            "tokens": meta.get("totalTokens", 0),
                            "sessionId": key.split(":")[-1],
                            "key": key,
                            # sessionFile basename lets the cloud map file-UUID → subagent-UUID
                            # for brain blobs that were synced before subagent_id was added.
                            "sessionFile": os.path.basename(
                                meta.get("sessionFile", "")
                            ),
                            "displayName": meta.get(
                                "label", meta.get("task", key.split(":")[-1][:12])
                            )[:80],
                            "updatedAt": meta.get("updatedAt", 0),
                            "runtimeMs": int(
                                now_ms
                                - meta.get("createdAt", meta.get("updatedAt", now_ms))
                            ),
                        }
                    )
                elif "subagent" not in key:
                    if not model_name:
                        model_name = meta.get("model", "")
                    main_tokens = max(main_tokens, meta.get("totalTokens", 0))
        except Exception as e:
            log.debug(f"Session index read error: {e}")

    # Crons
    cron_enabled = 0
    cron_disabled = 0
    try:
        os.path.expanduser("~")
        cron_candidates = [
            os.path.join(_get_openclaw_dir(), "cron", "jobs.json"),
            os.path.join(_get_openclaw_dir(), "agents", "main", "cron", "jobs.json"),
            os.path.join(paths.get("workspace", ""), "..", "crons.json"),
        ]
        cron_path = next((p for p in cron_candidates if os.path.isfile(p)), None)
        if cron_path:
            cron_data = _json.load(open(cron_path))
            crons = (
                cron_data.get("jobs", cron_data)
                if isinstance(cron_data, dict)
                else cron_data
            )
            if isinstance(crons, list):
                for c in crons:
                    if c.get("enabled", True):
                        cron_enabled += 1
                    else:
                        cron_disabled += 1
    except Exception:
        pass

    # Memory files
    _mem_files = _build_memory_files(paths.get("workspace", ""))

    # Spending (from state if available)
    spending = state.get("spending", {"today": 0, "week": 0, "month": 0})

    payload = {
        "system": system,
        "infra": infra,
        "model": model_name or "unknown",
        "provider": "",
        "sessionCount": session_count,
        "mainTokens": main_tokens,
        "contextWindow": 200000,
        "cronCount": cron_enabled + cron_disabled,
        "cronEnabled": cron_enabled,
        "cronDisabled": cron_disabled,
        "memoryCount": len(_mem_files),
        "memorySize": sum(f.get("size", 0) for f in _mem_files),
        "memoryFiles": _mem_files,
        "subagents": subagents_list,
        "subagentCounts": {
            "active": active_count,
            "idle": len([s for s in subagents_list if s["status"] == "idle"]),
            "stale": len([s for s in subagents_list if s["status"] == "stale"]),
            "total": len(subagents_list),
        },
        "totalActive": active_count,
        "spending": spending,
        "cronJobs": _build_cron_jobs(paths),
        "channels": _build_channel_data(config),
        "toolStats": _build_tool_stats(),
        "brainData": _build_brain_data(),
        "gateway": {},
        "runtimeInfo": _build_runtime_info(),
        "machineInfo": _build_machine_info(),
        "channelList": _build_channel_list(config),
        "ollamaInfo": _detect_ollama_for_heartbeat(),
    }

    # ── NemoClaw / sandbox enrichment ────────────────────────────────────────
    # Detect NemoClaw and add optional sandbox metadata to the snapshot.
    # The cloud stores this as generic key-value metadata — no NemoClaw-
    # specific UI logic lives in the dashboard.
    nemo = _detect_nemoclaw()
    if nemo.get("detected"):
        sandbox_meta = {
            "sandbox.name": nemo.get("sandbox_name", ""),
            "sandbox.status": nemo.get("sandbox_status", "unknown"),
            "sandbox.type": nemo.get("sandbox_type", "nemoclaw"),
            "inference.provider": nemo.get("inference_provider", ""),
            "inference.model": nemo.get("inference_model", ""),
            "security.sandbox_enabled": nemo.get("security_sandbox_enabled", True),
            "security.network_policy": nemo.get("security_network_policy", True),
        }
        payload["sandbox"] = sandbox_meta
        log.info(
            f"NemoClaw detected: sandbox={nemo.get('sandbox_name')} status={nemo.get('sandbox_status')}"
        )
    elif _is_running_in_container():
        # Generic container (Docker without NemoClaw) — still tag it
        payload["sandbox"] = {
            "sandbox.name": "",
            "sandbox.status": "running",
            "sandbox.type": "docker",
            "security.sandbox_enabled": True,
            "security.network_policy": False,
        }

    # Propagate container_id + runtime tag from path detection (set by _detect_docker_openclaw)
    docker_meta = _detect_docker_openclaw() if not nemo.get("detected") else {}
    if docker_meta.get("container_id") or docker_meta.get("runtime"):
        payload.setdefault("sandbox", {})
        if docker_meta.get("container_id"):
            payload["sandbox"]["container_id"] = docker_meta["container_id"]
        if docker_meta.get("runtime"):
            payload["sandbox"]["runtime"] = docker_meta["runtime"]
    elif nemo.get("detected"):
        payload.setdefault("sandbox", {})
        payload["sandbox"]["runtime"] = "nemoclaw"

    log.info(
        f"System snapshot: {len(subagents_list)} subagents ({active_count} active)"
    )

    # Local-store write-through (epic #964 / DuckDB MOAT). The dashboard
    # reads system + subagent state from these tables — without this
    # write, /api/local/system-snapshot + /api/local/subagents return
    # empty even though the cloud has the data. Failures non-fatal:
    # cloud sync still proceeds.
    try:
        from clawmetry import local_store as _ls
        _store = _ls.get_store()
        ts_iso = datetime.now(timezone.utc).isoformat()

        # One snapshot row per "kind" so the dashboard can query just the
        # part it needs (cpu / mem / disk / system) without loading the
        # full payload every time.
        _store.ingest_system_snapshot({
            "node_id":    node_id,
            "ts":         ts_iso,
            "kind":       "system",
            "rows":       payload.get("system", []),
            "infra":      payload.get("infra", {}),
            "session_count":     payload.get("sessionCount", 0),
            "model":             payload.get("model", ""),
            "main_tokens":       payload.get("mainTokens", 0),
            "subagent_count":    len(subagents_list),
            "active_subagents":  active_count,
        })

        for sa in subagents_list:
            sid = sa.get("sessionId") or sa.get("key")
            if not sid:
                continue
            _store.ingest_subagent({
                "subagent_id":       sid,
                "agent_type":        "openclaw",
                "task":              sa.get("task", ""),
                "status":            sa.get("status", ""),
                "token_count":       sa.get("tokens", 0),
                "model":             sa.get("model", ""),
                "label":             sa.get("label", ""),
                "displayName":       sa.get("displayName", ""),
                "session_file":      sa.get("sessionFile", ""),
                "updated_at_ms":     sa.get("updatedAt", 0),
                "runtime_ms":        sa.get("runtimeMs", 0),
            })
    except Exception as _e:
        log.debug("local_store: snapshot/subagent write-through failed: %s", _e)

    try:
        _post(
            "/ingest/system-snapshot",
            {
                "node_id": node_id,
                "encrypted": True,
                "blob": encrypt_payload(payload, enc_key),
            },
            api_key,
        )
        return 1
    except Exception as e:
        log.warning(f"System snapshot sync error: {e}")
        return 0


# ── Real-time log streaming ────────────────────────────────────────────────────


def start_log_streamer(config: dict, paths: dict) -> threading.Thread:
    """Start a background thread that tails the local log file and POSTs lines to cloud in real-time."""


def start_log_streamer(config: dict, paths: dict) -> threading.Thread:
    """Start a background thread that tails the local log file and POSTs lines to cloud in real-time."""
    api_key = config["api_key"]
    node_id = config["node_id"]
    log_dir = paths.get("log_dir", "")

    def _find_latest_log():
        if not log_dir or not os.path.isdir(log_dir):
            return None
        today = datetime.now().strftime("%Y-%m-%d")
        candidates = sorted(
            glob.glob(os.path.join(log_dir, f"*{today}*")), reverse=True
        )
        if candidates:
            return candidates[0]
        # Fallback: most recent log file
        all_logs = sorted(
            glob.glob(os.path.join(log_dir, "*.log")),
            key=os.path.getmtime,
            reverse=True,
        )
        return all_logs[0] if all_logs else None

    def _stream_worker():
        log.info(f"Log streamer started — watching {log_dir}")
        current_file = None
        proc = None
        batch = []
        last_push = time.time()

        while True:
            try:
                # Find/rotate to latest log file
                latest = _find_latest_log()
                if latest != current_file:
                    if proc:
                        try:
                            proc.kill()
                        except Exception:
                            pass
                    current_file = latest
                    if not current_file:
                        time.sleep(5)
                        continue
                    proc = subprocess.Popen(
                        ["tail", "-f", "-n", "0", current_file],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True,
                    )
                    log.info(f"Tailing {current_file}")

                if not proc or not proc.stdout:
                    time.sleep(2)
                    continue

                # Non-blocking read with select
                import select

                ready, _, _ = select.select([proc.stdout], [], [], STREAM_INTERVAL)
                if ready:
                    line = proc.stdout.readline()
                    if line:
                        batch.append(line.rstrip())

                # Push batch every STREAM_INTERVAL seconds
                now = time.time()
                if batch and (now - last_push >= STREAM_INTERVAL or len(batch) >= 50):
                    try:
                        _post(
                            "/ingest/stream",
                            {"node_id": node_id, "lines": batch},
                            api_key,
                        )
                    except Exception as e:
                        log.debug(f"Stream push error: {e}")
                    batch = []
                    last_push = now

            except Exception as e:
                log.debug(f"Stream worker error: {e}")
                time.sleep(5)
                if proc:
                    try:
                        proc.kill()
                    except Exception:
                        pass
                    proc = None
                    current_file = None

    t = threading.Thread(target=_stream_worker, daemon=True, name="log-streamer")
    t.start()
    return t


def start_event_streamer(config: dict, state: dict, paths: dict) -> threading.Thread:
    """Real-time session event streamer — watches JSONL files for changes
    and pushes new events immediately (like Dropbox file sync).

    Only makes API calls when new data appears. Tracks file sizes locally
    to detect changes without polling the server.
    """
    api_key = config["api_key"]
    enc_key = config.get("encryption_key")
    node_id = config["node_id"]
    sessions_dir = paths["sessions_dir"]

    # Track file sizes to detect changes
    _file_sizes: dict[str, int] = {}
    _file_offsets: dict[str, int] = {}  # line offsets per file

    def _scan_and_push():
        """Check all JSONL files for new content. Push immediately if found."""
        if not os.path.isdir(sessions_dir):
            return 0
        total_pushed = 0
        jsonl_files = _list_session_jsonls(sessions_dir)
        # Only check recently modified files (last 2 hours) to avoid scanning stale ones
        cutoff = time.time() - 7200
        active = [f for f in jsonl_files if os.path.getmtime(f) > cutoff]

        # Build subagent map (reuse sync_sessions logic)
        file_to_subagent: dict[str, str] = {}
        idx_path = os.path.join(sessions_dir, "sessions.json")
        if os.path.isfile(idx_path):
            try:
                with open(idx_path) as _fi:
                    _idx = json.load(_fi)
                for _k, _meta in _idx.items():
                    if ":subagent:" in _k and isinstance(_meta, dict):
                        _sf = _meta.get("sessionFile", "")
                        if _sf:
                            file_to_subagent[os.path.basename(_sf)] = _k.split(":")[-1]
            except Exception:
                pass

        for fpath in active:
            fname = os.path.basename(fpath)
            try:
                cur_size = os.path.getsize(fpath)
            except OSError:
                continue
            prev_size = _file_sizes.get(fname, 0)
            if cur_size <= prev_size:
                # No change — skip (no API call)
                _file_sizes[fname] = cur_size
                continue

            # File grew — read only the new lines
            _file_sizes[fname] = cur_size
            offset = _file_offsets.get(fname, state.get("last_event_ids", {}).get(fname, 0))
            batch: list[dict] = []
            new_offset = offset
            try:
                with open(fpath, "r", errors="replace") as f:
                    for i, raw in enumerate(f):
                        if i < offset:
                            continue
                        raw = raw.strip()
                        new_offset = i + 1
                        if not raw:
                            continue
                        try:
                            batch.append(json.loads(raw))
                        except Exception:
                            continue
            except Exception as e:
                log.debug(f"Event streamer read error ({fname}): {e}")
                continue

            if batch:
                cloud_fname = _canonical_session_file(fname)
                subagent_id = file_to_subagent.get(cloud_fname) or file_to_subagent.get(fname)
                try:
                    _flush_session_batch(batch, cloud_fname, api_key, enc_key, node_id, subagent_id)
                    total_pushed += len(batch)
                    _file_offsets[fname] = new_offset
                    # Update shared state so main loop doesn't re-push
                    state.setdefault("last_event_ids", {})[fname] = new_offset
                except Exception as e:
                    log.debug(f"Event streamer push error ({fname}): {e}")
            else:
                _file_offsets[fname] = new_offset

        return total_pushed

    def _streamer_loop():
        log.info(f"Event streamer started — watching {sessions_dir}")
        # Initialize sizes so we don't re-push old data
        if os.path.isdir(sessions_dir):
            for f in _list_session_jsonls(sessions_dir):
                fname = os.path.basename(f)
                _file_sizes[fname] = os.path.getsize(f)
                _file_offsets[fname] = state.get("last_event_ids", {}).get(fname, 0)

        while True:
            try:
                pushed = _scan_and_push()
                if pushed:
                    log.debug(f"Event streamer pushed {pushed} events")
                    # Save state after each push so main loop stays in sync
                    save_state(state)
            except Exception as e:
                log.debug(f"Event streamer error: {e}")
            # Fast check — only sleeps 1s between scans (stat() is cheap)
            time.sleep(1)

    t = threading.Thread(target=_streamer_loop, daemon=True, name="event-streamer")
    t.start()
    return t


def run_daemon() -> None:
    if not _acquire_pid_lock():
        print(
            "[clawmetry-sync] Another instance is already running. Exiting.", flush=True
        )
        sys.exit(0)
    import atexit

    atexit.register(_release_pid_lock)
    config = load_config()
    # If node_id looks like email prefix (contains + or @), use hostname instead
    nid = config.get("node_id", "")
    if not nid:
        import socket

        config["node_id"] = socket.gethostname() or platform.node() or "unknown"
        save_config(config)
        log.info(f"Auto-set node_id:  → {config['node_id']!r}")
    paths = detect_paths()
    enc = "🔒 E2E encrypted" if config.get("encryption_key") else "⚠️  unencrypted"
    log.info(f"Starting sync daemon — node={config['node_id']} → {INGEST_URL} ({enc})")

    # ── Install daemon-error → DuckDB tee (PRD #1133 layer 4, daemon side) ──
    # Must happen AFTER the start-banner so we don't tee that line as an
    # event. Failure here is non-fatal — the read side keeps its sync.log
    # fallback.
    try:
        install_daemon_error_event_handler()
    except Exception as _e:
        log.warning("daemon-error event handler: failed to install: %s", _e)

    # ── Startup sync: recent-first so Brain feed shows current activity ──
    send_heartbeat(config)
    log.info("Initial heartbeat sent")

    # WS relay deleted 2026-05-13: replaced by heartbeat-piggyback
    # (see project_relay_transport_decision). The cloud endpoint
    # /api/node/relay was killed 2026-05-12 (returns 404 in prod) after
    # the simple-websocket handshake-400 dead end documented in
    # reference_ws_handshake_400_unsolved.md. The reconnect loop was
    # spamming `relay: error: Handshake status 404 Not Found ...
    # reconnecting in 60s` forever — wasting bandwidth and burying real
    # errors. Cold-data reads now ride `pending_queries` piggybacked on
    # the heartbeat response and answered via /ingest/cache (issue #1053).
    # `clawmetry/relay.py` is retained as a stub so any third-party
    # importers don't crash, but `start_relay_thread` is no longer called.

    # ── Local query HTTP server (cross-process DuckDB read fix) ────────
    # Daemon owns the DuckDB writer lock; the dashboard process can't
    # open the same file (DuckDB exclusive lock blocks RO too). We host
    # the same routes/local_query.py shapes on a localhost port; the
    # dashboard's /api/local/* proxies through. Discovery+auth via
    # ~/.clawmetry/local_query.json. Failure here is non-fatal — the
    # dashboard falls back to direct DuckDB access (works in
    # single-process mode).
    try:
        from clawmetry import local_server as _local_server
        _ls_port = _local_server.start()
        if _ls_port:
            log.info("local query server: listening on 127.0.0.1:%d", _ls_port)
    except Exception as _e:
        log.warning("local query server: failed to start: %s", _e)

    state = load_state()

    # Always sync recent events first (last hour) — makes the dashboard
    # immediately useful even when there's a large backlog of old events.
    log.info("Syncing recent activity (last 60 min) first...")
    # Snapshot BOOTSTRAP.md immediately at startup — it may self-delete before
    # the first poll cycle on a fast-init OpenClaw. Idempotent; no-op when
    # the file isn't present (issue #690).
    try:
        if capture_bootstrap_if_present(config, paths):
            log.info("  Bootstrap: archived first-contact snapshot")
    except Exception as e:
        log.warning(f"  Bootstrap capture error: {e}")
    try:
        mem = sync_memory(config, state, paths)
        if mem:
            log.info(f"  Memory: {mem} files synced")
    except Exception as e:
        log.warning(f"  Memory sync error: {e}")
    try:
        recent_ev = sync_sessions_recent(config, state, paths, minutes=60)
        save_state(state)
        log.info(f"  Recent sessions: {recent_ev} events synced")
    except Exception as e:
        log.warning(f"  Recent session sync error: {e}")
    try:
        sm = sync_session_metadata(config, state)
        if sm:
            log.info(f"  Session metadata: {sm} rows synced")
    except Exception as e:
        log.warning(f"  Session metadata error: {e}")
    try:
        cr = sync_crons(config, state, paths)
        if cr:
            log.info(f"  Crons: {cr} synced")
    except Exception as e:
        log.warning(f"  Cron sync error: {e}")
    # Issue #605 DuckDB follow-up: ingest cron-run JSONL files so the
    # ``/api/crons/<jobId>/runs`` endpoint can read from DuckDB instead of
    # re-parsing JSONL on every request.
    try:
        crr = sync_cron_runs(config, state, paths)
        if crr:
            log.info(f"  Cron runs: {crr} rows ingested")
    except Exception as e:
        log.warning(f"  Cron-run ingest error: {e}")
    # Sync today's log lines immediately so Brain tab shows the most recent
    # activity right away — older log history is backfilled later
    try:
        lg = sync_logs(config, state, paths)
        if lg:
            log.info(f"  Recent logs: {lg} lines synced")
    except Exception as e:
        log.warning(f"  Recent log sync error: {e}")

    state["last_sync"] = datetime.now(timezone.utc).isoformat()
    save_state(state)
    send_heartbeat(config)
    _record_sync_progress("complete", 0, 0, status="complete")
    log.info("Recent sync complete — Brain feed should show current activity")

    # Validate stored log offsets on startup — prevents silent gaps
    # after log rotation, file truncation, or daemon restarts
    _validate_log_offsets(state, paths)
    save_state(state)

    # Start real-time streamers in background
    start_log_streamer(config, paths)
    start_event_streamer(config, state, paths)

    # Backfill older sessions in a background thread so the main loop
    # (and Brain tab) shows current activity immediately. The backfill
    # thread waits for the first main-loop cycle to complete before
    # sending historical data — recent events always reach the cloud first.
    first_run = not state.get("initial_backfill_done")
    _backfill_done = threading.Event()
    if first_run:

        def _backfill_worker():
            # Give the main loop one full cycle (≈15s) to post recent events
            time.sleep(20)
            log.info("Background backfill starting — syncing older sessions...")
            try:
                bf_state = load_state()
                ev = sync_sessions(config, bf_state, paths)
                bf_state["initial_backfill_done"] = True
                bf_state["last_sync"] = datetime.now(timezone.utc).isoformat()
                save_state(bf_state)
                log.info(f"Background backfill: {ev} older events synced")
            except Exception as e:
                log.warning(f"Background backfill error: {e}")
            try:
                bf_state = load_state()
                lg = sync_logs(config, bf_state, paths)
                save_state(bf_state)
                log.info(f"Background backfill: {lg} log lines synced")
            except Exception as e:
                log.warning(f"Background backfill log error: {e}")
            _backfill_done.set()
            log.info("Background backfill complete")

        t = threading.Thread(target=_backfill_worker, daemon=True, name="backfill")
        t.start()

    # ── Cloud-mediated approvals watcher (vivekchand/clawmetry#667) ──
    # Background thread that tails session JSONLs for risky toolCalls and
    # blocks the agent (via gateway sessions_kill) when a human denies in
    # the cloud. No-op when ~/.clawmetry/policies.yml is empty/missing,
    # so this is a non-breaking default-off feature for OSS users.
    try:
        from clawmetry import approvals as _approvals
        _approvals_stop = threading.Event()
        # Route the approvals logger through the same handlers as our sync
        # logger so watcher activity (policy fires, decisions, kills) shows
        # up in ~/.clawmetry/sync.log alongside the sync line items.
        try:
            _ap_log = logging.getLogger("clawmetry-approvals")
            _ap_log.setLevel(logging.INFO)
            _ap_log.propagate = False
            for _h in list(log.handlers):
                if _h not in _ap_log.handlers:
                    _ap_log.addHandler(_h)
        except Exception:
            pass

        def _approvals_worker():
            try:
                _approvals.watcher_loop(
                    api_key=config["api_key"],
                    node_id=config["node_id"],
                    interval_sec=2.0,
                    stop_event=_approvals_stop,
                )
            except Exception as _ape:
                log.warning(f"approvals watcher exited: {_ape}")

        t_app = threading.Thread(
            target=_approvals_worker, daemon=True, name="approvals-watcher"
        )
        t_app.start()
        log.info("approvals watcher thread started "
                 f"(policies: {_approvals.POLICIES_PATH})")
    except Exception as _e:
        log.warning(f"approvals watcher failed to start: {_e}")

    # Default to SLOW; flips to FAST after a heartbeat response with
    # `viewer_active: true` (epic #775 PR 2/3, adaptive sync cadence).
    # Seed from the startup heartbeat so the very first cycle picks up
    # FAST cadence when the user already has the cloud Brain tab open
    # at daemon start — otherwise the first 60s after startup is stuck
    # on SLOW even with an active viewer (2026-05-13 real-time MOAT fix).
    heartbeat_interval = _pick_heartbeat_interval(_LAST_HEARTBEAT_RESPONSE)
    snapshot_interval = 60  # system snapshot (subagents, flow metrics) every 60s
    log_sync_interval = 60  # log lines are low-priority; streamer covers real-time
    last_heartbeat = time.time()
    last_snapshot = 0  # force first snapshot immediately
    last_log_sync = (
        time.time()
    )  # already synced at startup; next run after log_sync_interval
    consecutive_hb_failures = 0
    # Alerts evaluator (PRD #779 PR-D pt2). 0 = fire on first cycle so we
    # exercise the dispatch path immediately if rules + matching events are
    # already present from startup backfill.
    last_alerts_eval = 0.0

    while True:
        try:
            state = load_state()

            # ── BOOTSTRAP.md "First Contact" capture (issue #690) ─────────
            # Best-effort; runs early in the tick so we snapshot the file
            # BEFORE any other helper notices OpenClaw has self-deleted it.
            # Idempotent — duplicate captures dedup at the local-store layer.
            try:
                capture_bootstrap_if_present(config, paths)
            except Exception as _be:
                log.warning("bootstrap capture failed: %s", _be)

            # ── High-priority: memory, flow metrics, subagents, recent sessions ──
            mem = sync_memory(config, state, paths)
            snap = 0
            now_snap = time.time()
            if now_snap - last_snapshot > snapshot_interval:
                snap = sync_system_snapshot(config, state, paths)  # subagents + flow
                last_snapshot = now_snap

            # ── Gateway process metric capture (#852 follow-up) ──
            # Persists RSS/CPU into DuckDB every 30s (rate-capped + deduped
            # inside the helper) so the dashboard can render a 24h sparkline
            # of memory pressure, not just a live snapshot. Best-effort.
            try:
                capture_gateway_metric(config)
            except Exception as _gm_e:
                log.debug("gateway.metric capture failed (continuing): %s", _gm_e)

            ev = sync_sessions(config, state, paths)
            ev += sync_claude_cli_sessions(config, state, paths)
            sm = sync_session_metadata(config, state)
            crons = sync_crons(config, state, paths)
            # Issue #605 DuckDB follow-up: tail cron-run JSONL files into
            # DuckDB so the dashboard's per-job timeline reads from the
            # columnar store. Failure is non-fatal — the legacy JSONL-read
            # fallback in routes/crons.py still works.
            try:
                cron_runs = sync_cron_runs(config, state, paths)
            except Exception as _e_cr:
                log.debug("sync_cron_runs error (non-fatal): %s", _e_cr)
                cron_runs = 0

            # ── Low-priority: log lines (real-time covered by streamer) ──
            lg = 0
            now_log = time.time()
            if now_log - last_log_sync > log_sync_interval:
                lg = sync_logs(config, state, paths)
                last_log_sync = now_log

            state["last_sync"] = datetime.now(timezone.utc).isoformat()
            save_state(state)
            if ev or lg or mem or crons or sm or snap or cron_runs:
                log.info(
                    f"Synced {ev} events, {lg} log lines, {mem} memory files, {crons} crons, {cron_runs} cron-runs, {sm} session rows ({enc})"
                )

            # ── Alerts evaluator (PRD #779 PR-D pt2, audit P0 #1 + #2) ──
            # Reads cached rules + recent events from the local DuckDB and
            # POSTs each match to the cloud's /api/cloud/alerts/dispatch
            # endpoint for notification fan-out. Throttled to
            # ALERTS_EVAL_INTERVAL_SEC. Failure is logged but never raises
            # into the sync cycle — alerts are best-effort relative to the
            # ingest path.
            now_alerts = time.time()
            if (now_alerts - last_alerts_eval) >= ALERTS_EVAL_INTERVAL_SEC:
                try:
                    n_alerts = evaluate_alerts(config, state)
                    if n_alerts:
                        log.info(
                            f"alerts: dispatched {n_alerts} match(es)"
                        )
                except Exception as _ae:
                    log.warning(f"alerts: evaluator tick errored: {_ae}")
                last_alerts_eval = now_alerts
                # Persist the eval state (last_eval_ts, cooldown memo) so
                # cooldown survives a daemon restart.
                try:
                    save_state(state)
                except Exception:
                    pass

            # Re-mirror Docker data if running in Docker mode
            if hasattr(detect_paths, "_docker_cid") or any(
                "docker-mirror" in str(v) for v in paths.values()
            ):
                try:
                    fresh = _detect_docker_openclaw()
                    if fresh.get("sessions_dir"):
                        paths.update({k: v for k, v in fresh.items() if k in paths})
                except Exception:
                    pass

            now = time.time()
            if now - last_heartbeat > heartbeat_interval:
                if send_heartbeat(config):
                    if consecutive_hb_failures > 0:
                        log.info(
                            f"Heartbeat recovered after {consecutive_hb_failures} consecutive failures"
                        )
                    consecutive_hb_failures = 0
                    last_heartbeat = now
                    # Adaptive cadence (#775 PR 2/3): if the cloud signalled a
                    # live viewer, drop to FAST so Telegram / brain events
                    # appear in the dashboard within seconds. Otherwise stay
                    # at SLOW. Missing field → SLOW (back-compat with a cloud
                    # that hasn't deployed PR 1 of the epic yet).
                    heartbeat_interval = _pick_heartbeat_interval(
                        _LAST_HEARTBEAT_RESPONSE
                    )
                else:
                    consecutive_hb_failures += 1
                    if consecutive_hb_failures >= 5:
                        log.error(
                            f"CRITICAL: {consecutive_hb_failures} consecutive heartbeat failures — node appears offline in cloud"
                        )
                    # On failure stay on SLOW so we don't hammer a flapping
                    # cloud. The existing 1s/2s in-call backoff inside
                    # `send_heartbeat` already covers retry, and the next
                    # cycle inherits whatever interval we set here.
                    heartbeat_interval = HEARTBEAT_INTERVAL_SLOW

        except Exception as e:
            log.error(f"Sync cycle error: {e}")

        # Adaptive cycle sleep (P0 real-time MOAT, 2026-05-13). The
        # original `time.sleep(POLL_INTERVAL=15)` floored the heartbeat
        # latency at 15s even when `heartbeat_interval` had dropped to
        # FAST (3s) on viewer_active. That hard-capped Brain-tab
        # freshness at ~15s instead of the target 1-2s. We now sleep at
        # most `heartbeat_interval` so the next cycle (and its
        # heartbeat-piggyback brain push) fires on the FAST cadence
        # whenever a viewer is active. When idle (SLOW=60s),
        # POLL_INTERVAL still rules, so bandwidth + Cloud Run cost stay
        # flat.
        time.sleep(max(1, min(POLL_INTERVAL, heartbeat_interval)))


def _build_gateway_data(paths: dict = None) -> dict:
    """Parse gateway.log (plain text) for routing events."""
    import re

    try:
        from datetime import datetime as _dt

        today = _dt.now().strftime("%Y-%m-%d")
        gw_log = os.path.join(_get_openclaw_dir(), "logs", "gateway.log")

        routes = []
        stats = {
            "today_messages": 0,
            "today_heartbeats": 0,
            "today_crons": 0,
            "today_errors": 0,
            "active_sessions": 0,
        }

        _KNOWN_CHANNELS = {
            "telegram",
            "imessage",
            "whatsapp",
            "signal",
            "discord",
            "slack",
            "irc",
            "webchat",
            "googlechat",
            "msteams",
        }

        if os.path.exists(gw_log):
            with open(gw_log, errors="ignore") as f:
                for line in f:
                    line = line.strip()
                    if not line or not line.startswith(today):
                        continue
                    # Format: 2026-03-10T10:00:59.952Z [channel] rest...
                    m = re.match(r"(\S+Z)\s+\[(\w+)\]\s+(.*)", line)
                    if not m:
                        continue
                    ts, tag, rest = m.group(1), m.group(2), m.group(3)
                    route = {
                        "timestamp": ts,
                        "from": tag,
                        "to": "brain",
                        "session": "",
                        "type": "message",
                        "status": "ok",
                    }
                    if tag == "heartbeat":
                        route["type"] = "heartbeat"
                        stats["today_heartbeats"] += 1
                        routes.append(route)
                    elif tag == "cron":
                        route["type"] = "cron"
                        stats["today_crons"] += 1
                        routes.append(route)
                    elif tag in _KNOWN_CHANNELS:
                        if (
                            "sendMessage ok" in rest
                            or "send ok" in rest
                            or "delivered" in rest.lower()
                        ):
                            # Extract message_id for display
                            m_id = re.search(r"message=(\d+)", rest)
                            if m_id:
                                route["session"] = m_id.group(1)
                            route["to"] = "user"
                            stats["today_messages"] += 1
                            routes.append(route)
                    elif tag in ("warn", "error") or "error" in rest.lower()[:30]:
                        stats["today_errors"] += 1

        routes.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        return {
            "stats": stats,
            "routes": routes[:100],
            "total": len(routes),
            "status": "running",
            "port": 18789,
        }
    except Exception as e:
        return {
            "stats": {
                "today_messages": 0,
                "today_heartbeats": 0,
                "today_crons": 0,
                "today_errors": 0,
                "active_sessions": 0,
            },
            "routes": [],
            "total": 0,
            "status": "running",
            "port": 18789,
        }


def _compute_autonomy_daily_series(sessions_dir, days=90):
    """
    Compute per-day autonomy aggregates from local session transcripts.

    Returns a list of ``{day, median_gap_sec, autonomy_ratio, sample_count}``
    covering the last ``days`` days (UTC). Days with no user activity are
    skipped — we don't send empty days to cloud.

    The heavy lifting happens **here, on the user's machine**. Only the tiny
    aggregate leaves the box. See memory note ``local_compute_cloud_display``.
    """
    from collections import defaultdict
    from datetime import datetime as _dt_ad, timedelta as _td_ad, timezone as _tz_ad

    if not sessions_dir or not os.path.isdir(sessions_dir):
        return []

    now_utc = _dt_ad.now(tz=_tz_ad.utc)
    cutoff_ts = now_utc.timestamp() - days * 86400

    try:
        files = [
            f for f in os.listdir(sessions_dir)
            if f.endswith(".jsonl") and ".deleted." not in f and ".reset." not in f
        ]
    except OSError:
        return []

    daily = defaultdict(lambda: {"gaps": [], "no_nudge_sessions": 0, "sessions": 0, "user_msgs": 0})

    def _ts_of(msg_or_ev, fallback):
        for key in ("timestamp", "ts", "created_at", "time"):
            val = msg_or_ev.get(key)
            if val is None:
                continue
            if isinstance(val, (int, float)):
                return float(val) / (1000.0 if val > 10**12 else 1.0)
            if isinstance(val, str):
                try:
                    if val.endswith("Z"):
                        val = val[:-1] + "+00:00"
                    return _dt_ad.fromisoformat(val).timestamp()
                except (ValueError, TypeError):
                    continue
        return fallback

    for fname in files:
        fpath = os.path.join(sessions_dir, fname)
        try:
            file_mtime = os.path.getmtime(fpath)
        except OSError:
            file_mtime = now_utc.timestamp()
        if file_mtime < cutoff_ts:
            continue

        user_timestamps = []
        try:
            with open(fpath, "r", errors="replace") as fh:
                for raw in fh:
                    raw = raw.strip()
                    if not raw:
                        continue
                    try:
                        ev = json.loads(raw)
                    except (json.JSONDecodeError, ValueError):
                        continue
                    if not isinstance(ev, dict):
                        continue
                    msg = ev.get("message") if ev.get("type") == "message" else ev
                    if not isinstance(msg, dict):
                        continue
                    if msg.get("role") != "user":
                        continue
                    ts = _ts_of(msg, file_mtime)
                    if ts == file_mtime and ev.get("type") == "message":
                        ts = _ts_of(ev, file_mtime)
                    if ts < cutoff_ts:
                        continue
                    user_timestamps.append(ts)
        except OSError:
            continue

        if not user_timestamps:
            continue
        user_timestamps.sort()

        # Gaps between consecutive user messages in this session.
        session_gaps = [
            user_timestamps[i + 1] - user_timestamps[i]
            for i in range(len(user_timestamps) - 1)
            if user_timestamps[i + 1] - user_timestamps[i] > 0
        ]
        is_no_nudge = len(user_timestamps) <= 1

        day_key = _dt_ad.fromtimestamp(user_timestamps[0], tz=_tz_ad.utc).strftime("%Y-%m-%d")
        daily[day_key]["gaps"].extend(session_gaps)
        daily[day_key]["sessions"] += 1
        daily[day_key]["user_msgs"] += len(user_timestamps)
        if is_no_nudge:
            daily[day_key]["no_nudge_sessions"] += 1

    def _median(xs):
        xs = [x for x in xs if x is not None]
        if not xs:
            return None
        xs.sort()
        n = len(xs)
        m = n // 2
        return float(xs[m]) if n % 2 else (xs[m - 1] + xs[m]) / 2.0

    series = []
    # Build trailing 7-day slopes so cloud can see "improving/declining" hint.
    day_keys_sorted = sorted(daily.keys())
    for day_key in day_keys_sorted:
        bucket = daily[day_key]
        if bucket["sessions"] <= 0:
            continue
        series.append({
            "day": day_key,
            "median_gap_sec": _median(bucket["gaps"]),
            "autonomy_ratio": bucket["no_nudge_sessions"] / bucket["sessions"],
            "sample_count": bucket["user_msgs"],
            "trend_slope": None,  # filled in below if we can
        })

    # Rolling 7-day slope (normalized by running median).
    for i, entry in enumerate(series):
        window = series[max(0, i - 6): i + 1]
        if len(window) < 2:
            continue
        gaps = [w["median_gap_sec"] for w in window if w["median_gap_sec"] is not None]
        if len(gaps) < 2:
            continue
        xs = list(range(len(gaps)))
        n = len(xs)
        mean_x = sum(xs) / n
        mean_y = sum(gaps) / n
        num = sum((xs[k] - mean_x) * (gaps[k] - mean_y) for k in range(n))
        den = sum((xs[k] - mean_x) ** 2 for k in range(n))
        raw = num / den if den else 0.0
        med = _median(gaps)
        entry["trend_slope"] = round(raw / med, 6) if med else 0.0

    return series


def sync_autonomy(config, state, paths):
    """
    Push a daily autonomy aggregate to cloud (if opted in).

    Runs at most once per local-day: we record the last pushed UTC day in
    ``state['autonomy_last_day']`` and skip until that rolls over. On first
    run, pushes up to 90 days of history. Each subsequent run pushes
    whatever has changed.

    Skipped when sync is paused (expired trial).
    """
    if not _sync_allowed():
        return 0
    api_key = config.get("api_key") or ""
    if not api_key:
        return 0
    # User can opt out of sending analytics even if cloud sync is on.
    if config.get("cloud_autonomy_sync") is False:
        return 0

    from datetime import datetime as _dt_as, timezone as _tz_as
    today = _dt_as.now(tz=_tz_as.utc).strftime("%Y-%m-%d")
    last_pushed = state.get("autonomy_last_day", "")
    # Skip if we already pushed today, unless we've never pushed anything.
    if last_pushed == today and state.get("autonomy_pushed_any"):
        return 0

    sessions_dir = paths.get("sessions_dir") or paths.get("sessions")
    series = _compute_autonomy_daily_series(sessions_dir, days=90)
    if not series:
        return 0

    # Only send days we haven't pushed yet — or all of them on first run.
    if state.get("autonomy_pushed_any"):
        series = [s for s in series if s["day"] >= last_pushed]
    if not series:
        state["autonomy_last_day"] = today
        return 0

    node_id = config.get("node_id") or get_machine_id()
    payload = {"node_id": node_id, "snapshots": series}
    try:
        _post("/ingest/autonomy", payload, api_key, timeout=30)
        state["autonomy_last_day"] = today
        state["autonomy_pushed_any"] = True
        return len(series)
    except Exception as e:
        log.warning(f"sync_autonomy failed: {e}")
        return 0


ALERTS_EVAL_INTERVAL_SEC = 60  # Re-evaluate alerts every 60s (PRD #779)
# Window for the events read from DuckDB on each tick. Wider than the
# evaluation interval so a slow tick doesn't drop events on the floor.
_ALERTS_EVENT_LOOKBACK_SEC = 600
# Cap rows fetched per tick. Generous for a single-node alert evaluator;
# rolling-window math is O(N²) in the worst case but N is small.
_ALERTS_EVENT_LIMIT = 2000


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _iso_now_minus(seconds: int) -> str:
    from datetime import timedelta as _td
    return (datetime.now(timezone.utc) - _td(seconds=seconds)).isoformat()


def evaluate_alerts(config: dict, state: dict) -> int:
    """Local DuckDB evaluation -> cloud dispatch on match (PRD #779 PR-D pt2).

    Closes the architectural inversion called out in the 2026-05-13 audit
    (P0 #1 + P0 #2): the daemon now reads the events it just wrote to
    DuckDB, walks the cloud-cached alert rules locally via
    ``clawmetry.alert_evaluator``, and POSTs each match to the cloud's
    ``/api/cloud/alerts/dispatch`` endpoint (which fans out to Slack/email/
    PagerDuty). Cloud no longer evaluates rules — it just dispatches
    notifications for matches the local node certifies.

    Returns the count of dispatched matches. Persists ``alerts_last_eval_ts``
    + ``alerts_eval_memo`` into ``state`` so cooldown survives daemon
    restart. Skipped silently when:
      * the user is OSS-only (no ``cm_`` api key) — alerts is Cloud-Pro only,
      * no rules are cached locally (cloud hasn't authored or pushed any),
      * the local store is unreachable (the function never raises into the
        daemon loop — at most logs a WARNING and returns 0).

    See PRD ``clawmetry-cloud#779`` and the cloud endpoint shipped in
    ``clawmetry-cloud#785`` for the dispatch payload contract.
    """
    api_key = config.get("api_key", "")
    node_id = config.get("node_id", "")
    if not api_key or not api_key.startswith("cm_") or not node_id:
        return 0  # OSS / unconfigured node: nothing to dispatch.

    try:
        from clawmetry import local_store, alert_evaluator
    except Exception as e:
        log.warning("alerts: local_store/alert_evaluator import failed: %s", e)
        return 0

    try:
        store = local_store.get_store()
    except Exception as e:
        log.warning("alerts: local store unavailable: %s", e)
        return 0

    # Scope to rules owned by this token. Same hash the cloud uses, so a
    # multi-tenant local store (rare today) only fires this token's rules.
    try:
        owner_hash = _owner_hash_for_token(api_key)
    except Exception:
        owner_hash = None
    try:
        rules = store.query_alert_rules(
            owner_hash=owner_hash,
            enabled_only=True,
            limit=200,
        )
    except Exception as e:
        log.warning("alerts: query_alert_rules failed: %s", e)
        return 0
    if not rules:
        return 0

    # Read the recent slice of events. ``since`` is whichever is more recent
    # of (last successful eval ts) or (now - lookback) — bounds the window
    # so a daemon restart doesn't replay the entire DuckDB history.
    last_eval_ts = state.get("alerts_last_eval_ts")
    since = last_eval_ts or _iso_now_minus(_ALERTS_EVENT_LOOKBACK_SEC)
    try:
        events = store.query_events(since=since, limit=_ALERTS_EVENT_LIMIT)
    except Exception as e:
        log.warning("alerts: query_events failed: %s", e)
        return 0

    last_eval_state = state.setdefault("alerts_eval_memo", {})
    if not isinstance(last_eval_state, dict):
        last_eval_state = {}
        state["alerts_eval_memo"] = last_eval_state

    try:
        matches = alert_evaluator.evaluate(rules, events, last_eval_state)
    except Exception as e:
        log.warning("alerts: evaluator errored: %s", e)
        state["alerts_last_eval_ts"] = _iso_now()
        return 0

    dispatched = 0
    for m in matches:
        rule = m.get("rule") or {}
        evt = m.get("event") or {}
        try:
            resp = _post(
                "/api/cloud/alerts/dispatch",
                {
                    "rule_id":       rule.get("id"),
                    "rule_name":     rule.get("name") or "",
                    "node_id":       node_id,
                    "event_id":      evt.get("id"),
                    "event_summary": (m.get("summary") or "")[:500],
                    "evaluated_at":  _iso_now(),
                    "metadata":      m.get("metadata") or {},
                },
                api_key,
                timeout=10,
            )
        except Exception as e:
            log.warning("alerts: dispatch failed (rule=%s): %s",
                        rule.get("id"), e)
            continue
        if isinstance(resp, dict) and resp.get("ok"):
            dispatched += 1
            if resp.get("deduped"):
                log.debug("alerts: rule=%s dispatched (cloud deduped)",
                          rule.get("id"))
            else:
                log.info("alerts: rule=%s dispatched -> %s",
                         rule.get("id"), resp.get("dispatched") or [])

    state["alerts_last_eval_ts"] = _iso_now()
    return dispatched


if __name__ == "__main__":
    while True:
        try:
            run_daemon()
            break  # clean exit
        except KeyboardInterrupt:
            break
        except Exception as e:
            import traceback

            log.error(f"Daemon crashed: {e}")
            log.error(traceback.format_exc())
            log.info("Restarting in 15 seconds...")
            time.sleep(15)
