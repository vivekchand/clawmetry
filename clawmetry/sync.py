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
    """Write PID file. Return False if another instance is already running."""
    pid_path = _pid_file()
    pid_path.parent.mkdir(parents=True, exist_ok=True)
    if pid_path.exists():
        try:
            existing_pid = int(pid_path.read_text().strip())
            os.kill(existing_pid, 0)
            return False
        except (ProcessLookupError, ValueError):
            pass
    pid_path.write_text(str(os.getpid()))
    return True


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
                return json.loads(resp.read())
        except urllib.error.HTTPError as e:
            code = e.code
            msg = e.read().decode()[:200]
            last_err = RuntimeError(f"HTTP {code} from {url}: {msg}")
            # Retry on 401/503 (cloud cold-start transient errors)
            if code in (401, 503) and attempt == 0:
                time.sleep(2)
                continue
            raise last_err
    raise last_err


def get_machine_id() -> str:
    """Generate a stable hardware fingerprint for this machine."""
    import hashlib
    import platform

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
                ln.strip() for ln in out.splitlines() if ln.strip() and ln.strip() != "UUID"
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
    import shutil

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
    import json as _json

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
    found_sessions = docker_paths.get("sessions_dir") or next(
        (str(p) for p in sessions_candidates if p.exists()), None
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


# ── Sync: session events (full content, encrypted) ────────────────────────────


def sync_sessions(config: dict, state: dict, paths: dict) -> int:
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

    jsonl_files = glob.glob(os.path.join(sessions_dir, "*.jsonl"))
    # Sort newest-first so recent sessions sync before old ones
    jsonl_files.sort(key=lambda p: os.path.getmtime(p), reverse=True)

    for fpath in jsonl_files:
        if total >= MAX_EVENTS_PER_CYCLE:
            break  # continue next cycle; progress is saved per-file

        fname = os.path.basename(fpath)
        last_line = last_ids.get(fname, 0)
        batch: list[dict] = []
        subagent_id = file_to_subagent_id.get(fname)  # None for main session

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
                        batch, fname, api_key, enc_key, node_id, subagent_id
                    )
                    total += len(batch)
                    batch = []
                    # Save progress after each batch so restarts don't re-upload
                    last_ids[fname] = line_cursor
                    if total >= MAX_EVENTS_PER_CYCLE:
                        break

            if batch:
                _flush_session_batch(
                    batch, fname, api_key, enc_key, node_id, subagent_id
                )
                total += len(batch)

            last_ids[fname] = (
                len(all_lines) if total < MAX_EVENTS_PER_CYCLE else line_cursor
            )

        except Exception as e:
            log.warning(f"Session sync error ({fname}): {e}")

    return total


def _flush_session_batch(
    batch: list,
    fname: str,
    api_key: str,
    enc_key: str | None,
    node_id: str,
    subagent_id: str | None = None,
) -> None:
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

    jsonl_files = glob.glob(os.path.join(sessions_dir, "*.jsonl"))
    jsonl_files.sort(key=lambda p: os.path.getmtime(p), reverse=True)

    for fpath in jsonl_files:
        if total >= MAX_EVENTS_PER_CYCLE:
            break

        fname = os.path.basename(fpath)
        subagent_id = file_to_subagent_id.get(fname)

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
                        batch, fname, api_key, enc_key, node_id, subagent_id
                    )
                    total += len(batch)
                    batch = []
                    if total >= MAX_EVENTS_PER_CYCLE:
                        break

            if batch:
                _flush_session_batch(
                    batch, fname, api_key, enc_key, node_id, subagent_id
                )
                total += len(batch)

            # Advance cursor to EOF so backfill loop doesn't re-send these.
            # But DON'T advance past what the normal loop would have started at
            # — keep the old cursor so it backfills the gap between old cursor
            # and start_idx.
            last_ids[fname] = max(last_ids.get(fname, 0), n)

        except Exception as e:
            log.warning(f"Recent sync error ({fname}): {e}")

    return total


# ── Sync: logs (full lines, encrypted) ────────────────────────────────────────


def sync_logs(config: dict, state: dict, paths: dict) -> int:
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


def send_heartbeat(config: dict) -> bool:
    """Send heartbeat to cloud. Returns True on success, False on failure."""
    payload = {
        "node_id": config["node_id"],
        "ts": datetime.now(timezone.utc).isoformat(),
        "platform": platform.system(),
        "version": _get_version(),
        "e2e": bool(config.get("encryption_key")),
        "ollama": _detect_ollama_for_heartbeat(),
    }
    last_err = None
    for attempt in range(3):
        try:
            _post("/ingest/heartbeat", payload, config["api_key"])
            if attempt > 0:
                log.info(f"Heartbeat succeeded after {attempt + 1} attempts")
            return True
        except Exception as e:
            last_err = e
            if attempt < 2:
                time.sleep(2**attempt)  # 1s, 2s backoff
    log.warning(f"Heartbeat failed after 3 attempts: {last_err}")
    return False


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


def sync_crons(config: dict, state: dict, paths: dict) -> int:
    """Sync cron job definitions to cloud."""
    api_key = config["api_key"]
    node_id = config["node_id"]
    last_hash = state.get("cron_hash", "")

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
        if h == last_hash:
            return 0
        data = json.loads(raw)
        jobs = data.get("jobs", []) if isinstance(data, dict) else data

        events = []
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
            state = j.get("state", {})
            events.append(
                {
                    "type": "cron_state",
                    "session_id": "",
                    "data": {
                        "job_id": j.get("id", ""),
                        "name": j.get("name", ""),
                        "enabled": j.get("enabled", True),
                        "expr": expr,
                        "schedule": sched,
                        "task": (j.get("task") or "")[:200],
                        "state": {
                            "lastStatus": state.get("lastStatus"),
                            "lastRunAtMs": state.get("lastRunAtMs"),
                            "nextRunAtMs": state.get("nextRunAtMs"),
                            "lastDurationMs": state.get("lastDurationMs"),
                            "lastError": state.get("lastError"),
                            "consecutiveFailures": state.get("consecutiveFailures"),
                        },
                    },
                }
            )

        if events:
            _post("/api/ingest", {"events": events, "node_id": node_id}, api_key)
            state["cron_hash"] = h
            return len(events)
    except Exception as e:
        log.warning(f"Cron sync error: {e}")
    return 0


def sync_session_metadata(config: dict, state: dict = None) -> int:
    """Sync OpenClaw session metadata rows to cloud sessions table.

    Uses mtime tracking to only re-parse files that changed since last sync.
    Reads JSONL session files directly (HTTP API returns HTML, not JSON).
    Extracts session_id, model, timestamps from the event stream.
    """
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

        session_rows = []
        for fpath in sorted(sessions_dir.glob("*.jsonl"))[-100:]:
            # Skip files that haven't changed since last sync
            try:
                current_mtime = fpath.stat().st_mtime
                if last_mtimes.get(fpath.name) == current_mtime:
                    continue
            except OSError:
                continue
            try:
                sid = fpath.stem  # UUID filename = session_id
                model = ""
                started_at = ""
                updated_at = ""
                total_tokens = 0
                total_cost = 0.0
                label = ""

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
                            model = ev["modelId"]
                        elif etype == "session" and ev.get("label"):
                            label = ev["label"]
                        elif etype == "message":
                            msg = ev.get("message", {})
                            usage = msg.get("usage", {})
                            if usage:
                                total_tokens += int(usage.get("totalTokens", 0))
                                cost_obj = usage.get("cost", {})
                                if isinstance(cost_obj, dict):
                                    total_cost += float(cost_obj.get("total", 0))
                                elif isinstance(cost_obj, (int, float)):
                                    total_cost += float(cost_obj)
                            # Use last model seen in messages
                            msg_model = msg.get("model", "")
                            if msg_model:
                                model = msg_model

                session_rows.append(
                    {
                        "session_id": sid,
                        "display_name": label or sid[:8],
                        "status": "completed",
                        "model": model,
                        "total_tokens": total_tokens,
                        "total_cost": total_cost,
                        "started_at": started_at,
                        "updated_at": updated_at,
                    }
                )
                last_mtimes[fpath.name] = current_mtime
            except Exception as e:
                log.debug(f"Session parse error ({fpath.name}): {e}")

        if not session_rows:
            return 0

        # Also try reading default model from sessions.json index
        _default_model = ""
        _idx_path = sessions_dir / "sessions.json"
        if _idx_path.exists():
            try:
                with open(_idx_path) as _fi:
                    _idx = json.load(_fi)
                for _k, _meta in _idx.items():
                    if isinstance(_meta, dict) and "subagent" not in _k:
                        _m = (_meta.get("model") or "").strip()
                        if _m:
                            _default_model = _m
                            break
            except Exception:
                pass

        # Fallback: use most common model from sessions that have one
        if not _default_model:
            _models = [s["model"] for s in session_rows if s.get("model")]
            if _models:
                _default_model = max(set(_models), key=_models.count)

        # Fill empty model fields with the default
        if _default_model:
            for s in session_rows:
                if not s.get("model"):
                    s["model"] = _default_model

        # Batch in groups of 50
        for i in range(0, len(session_rows), 50):
            batch = session_rows[i : i + 50]
            _post("/ingest/sessions", {"node_id": node_id, "sessions": batch}, api_key)
        return len(session_rows)
    except Exception as e:
        log.warning(f"Session metadata sync failed: {e}")
        return 0


def sync_memory(config: dict, state: dict, paths: dict) -> int:
    """Sync memory files (MEMORY.md + memory/*.md) to cloud."""
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

    return synced

    # ── Real-time log streaming ────────────────────────────────────────────────────

    """Build memory file list for the Memory popup."""


def _build_machine_info():
    """Build machine hardware info for the Machine popup."""
    try:
        import platform
        import subprocess
        import socket

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
        import platform
        import subprocess

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
        str(Path.home())
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
        import collections
        import glob

        str(Path.home())
        session_dir = os.path.join(_get_openclaw_dir(), "agents", "main", "sessions")
        if not os.path.isdir(session_dir):
            return {}

        tool_counts = collections.Counter()
        tool_recent = {}  # tool_name -> last few entries
        channel_msgs = collections.defaultdict(
            lambda: {"in": 0, "out": 0, "messages": []}
        )

        datetime.now().strftime("%Y-%m-%d")

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
                                        except Exception:
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

    str(Path.home())
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
            sched.get("interval", "") if kind == "interval" else (
                f"at {sched.get('at', '')}"
                if kind == "at"
                else sched.get("cron", "")
                if kind == "cron"
                else ""
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
    """Push system info + subagent data as encrypted snapshot."""
    import platform
    import json as _json

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


def run_daemon() -> None:
    if not _acquire_pid_lock():
        print("[clawmetry-sync] Another instance is already running. Exiting.", flush=True)
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
    paths  = detect_paths()
    enc    = "🔒 E2E encrypted" if config.get("encryption_key") else "⚠️  unencrypted"
    log.info(f"Starting sync daemon — node={config['node_id']} → {INGEST_URL} ({enc})")

    # ── Startup sync: recent-first so Brain feed shows current activity ──
    send_heartbeat(config)
    log.info("Initial heartbeat sent")

    state = load_state()

    # Always sync recent events first (last hour) — makes the dashboard
    # immediately useful even when there's a large backlog of old events.
    log.info("Syncing recent activity (last 60 min) first...")
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
    log.info("Recent sync complete — Brain feed should show current activity")

    # Validate stored log offsets on startup — prevents silent gaps
    # after log rotation, file truncation, or daemon restarts
    _validate_log_offsets(state, paths)
    save_state(state)

    # Start real-time log streamer in background
    start_log_streamer(config, paths)

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

    heartbeat_interval = 60
    snapshot_interval = 60   # system snapshot (subagents, flow metrics) every 60s
    log_sync_interval  = 60  # log lines are low-priority; streamer covers real-time
    last_heartbeat  = time.time()
    last_snapshot   = 0  # force first snapshot immediately
    last_log_sync   = time.time()  # already synced at startup; next run after log_sync_interval
    consecutive_hb_failures = 0

    while True:
        try:
            state = load_state()

            # ── High-priority: memory, flow metrics, subagents, recent sessions ──
            mem  = sync_memory(config, state, paths)
            snap = 0
            now_snap = time.time()
            if now_snap - last_snapshot > snapshot_interval:
                snap = sync_system_snapshot(config, state, paths)  # subagents + flow
                last_snapshot = now_snap
            ev = sync_sessions(config, state, paths)
            sm = sync_session_metadata(config, state)
            crons = sync_crons(config, state, paths)

            # ── Low-priority: log lines (real-time covered by streamer) ──
            lg = 0
            now_log = time.time()
            if now_log - last_log_sync > log_sync_interval:
                lg = sync_logs(config, state, paths)
                last_log_sync = now_log

            state["last_sync"] = datetime.now(timezone.utc).isoformat()
            save_state(state)
            if ev or lg or mem or crons or sm or snap:
                log.info(f"Synced {ev} events, {lg} log lines, {mem} memory files, {crons} crons, {sm} session rows ({enc})")

            # Re-mirror Docker data if running in Docker mode
            if hasattr(detect_paths, "_docker_cid") or any("docker-mirror" in str(v) for v in paths.values()):
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
                        log.info(f"Heartbeat recovered after {consecutive_hb_failures} consecutive failures")
                    consecutive_hb_failures = 0
                    last_heartbeat = now
                else:
                    consecutive_hb_failures += 1
                    if consecutive_hb_failures >= 5:
                        log.error(f"CRITICAL: {consecutive_hb_failures} consecutive heartbeat failures — node appears offline in cloud")

        except Exception as e:
            log.error(f"Sync cycle error: {e}")

        time.sleep(POLL_INTERVAL)



def _build_gateway_data(paths: dict = None) -> dict:
    """Parse gateway.log (plain text) for routing events."""
    import re
    try:
        from datetime import datetime as _dt
        today = _dt.now().strftime("%Y-%m-%d")
        gw_log = os.path.join(_get_openclaw_dir(), "logs", "gateway.log")

        routes = []
        stats = {"today_messages": 0, "today_heartbeats": 0, "today_crons": 0,
                 "today_errors": 0, "active_sessions": 0}

        _KNOWN_CHANNELS = {"telegram", "imessage", "whatsapp", "signal", "discord",
                           "slack", "irc", "webchat", "googlechat", "msteams"}

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
                    route = {"timestamp": ts, "from": tag, "to": "brain",
                             "session": "", "type": "message", "status": "ok"}
                    if tag == "heartbeat":
                        route["type"] = "heartbeat"
                        stats["today_heartbeats"] += 1
                        routes.append(route)
                    elif tag == "cron":
                        route["type"] = "cron"
                        stats["today_crons"] += 1
                        routes.append(route)
                    elif tag in _KNOWN_CHANNELS:
                        if "sendMessage ok" in rest or "send ok" in rest or "delivered" in rest.lower():
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
        return {"stats": {"today_messages": 0, "today_heartbeats": 0, "today_crons": 0,
                          "today_errors": 0, "active_sessions": 0},
                "routes": [], "total": 0, "status": "running", "port": 18789}


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



def run_daemon() -> None:
    """Run the sync daemon - main loop for continuous synchronization."""
    config = load_config()
    state = load_state()
    paths = detect_paths()

    log.info("Starting ClawMetry sync daemon...")

    while True:
        try:
            sync_session_metadata(config, state)
            sync_sessions(config, state, paths)
            sync_logs(config, state, paths)
            sync_crons(config, state, paths)
            sync_memory(config, state, paths)
            sync_system_snapshot(config, state, paths)
            save_state(state)
        except Exception as e:
            log.error(f"Sync error: {e}")

        time.sleep(60)
