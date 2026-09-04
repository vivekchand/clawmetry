"""
This adapter does NOT re-implement OpenClaw session parsing. It delegates
to the long-standing helpers in ``dashboard.py`` via a late import, the
same way ``routes/*.py`` modules do. The point of this file is to expose
the existing OpenClaw observability surface through the unified
:class:`~clawmetry.adapters.base.AgentAdapter` interface, so the dashboard
treats OpenClaw exactly like any other agent.

Zero behavior change: when no other adapter is registered, the UI looks
identical to the pre-refactor dashboard.
"""
from __future__ import annotations

import glob
import hashlib
import json
import logging
import os
import re
import tempfile
import time as _time
from typing import List, Optional, Set

from .base import AgentAdapter, Capability, DetectResult, Event, Session

logger = logging.getLogger("clawmetry.adapters.openclaw")

# Gateway log filename patterns (#4055, #4056):
#   default profile          : openclaw-YYYY-MM-DD.log
#   named profiles (#4055)   : openclaw-{name}-YYYY-MM-DD.log
#   rotation archives (#4056): openclaw-YYYY-MM-DD.N.log
#   named + rotated          : openclaw-{name}-YYYY-MM-DD.N.log
# (.+-)? matches named profiles; (\.\d+)? matches rotation archives; the date
# anchor excludes unrelated files (openclaw-debug.log, etc.).
_DEFAULT_LOG_RE = re.compile(r"openclaw-(.+-)?\d{4}-\d{2}-\d{2}(\.\d+)?\.log$")

# NeMo Guardrails compact tool-catalog injects these three meta-tool names into
# the JSONL transcript when NEMOCLAW_TOOL_CATALOG is active. They are guardrail
# dispatches, not real agent actions; tag them so consumers can filter/style
# them separately from ordinary tool calls.
_NEMOCLAW_CATALOG_TOOLS: frozenset = frozenset({
    "tool_search",
    "tool_describe",
    "tool_call",
})

# Reasoning / extended-thinking token key variants (#2876). Anthropic
# extended-thinking sessions emit a reasoning-token share inside the per-turn
# usage object under one of several spellings; older code only read
# input/output/cache keys, so Session.reasoning_tokens was always 0 and per-turn
# token counts were under-reported for reasoning-capable models.
_REASONING_TOKEN_KEYS: tuple = (
    "reasoning_tokens",
    "reasoningTokens",
    "thinking_tokens",
    "thinkingTokens",
    "thinking_input_tokens",
    "thinkingInputTokens",
    "reasoning_output_tokens",
    "reasoningOutputTokens",
)


def _reasoning_tokens(usage: dict) -> int:
    """Return the reasoning/thinking token count from a usage dict.

    Accepts any of the known key spellings (snake/camel, thinking/reasoning)
    and coerces to a non-negative int. Returns 0 when absent or unparsable.
    """
    if not isinstance(usage, dict):
        return 0
    for k in _REASONING_TOKEN_KEYS:
        v = usage.get(k)
        if v is None:
            continue
        try:
            return max(0, int(v))
        except (TypeError, ValueError):
            return 0
    return 0


def _d():
    """Late import to avoid circular init with dashboard module."""
    import dashboard as _dash

    return _dash


def _gateway_live() -> bool:
    """True only if the OpenClaw gateway is actually up (pid alive or port
    18789 listening). Never raises.

    When ``OPENCLAW_SUPERVISOR_MODE=external`` is set, a ``False`` return
    during a restart-handoff is an expected transient, not a failure.
    Callers should check ``gatewayInRestartHandoff`` in
    ``DetectResult.meta`` (set by ``detect()``) for the full picture.
    """
    home = os.environ.get("OPENCLAW_HOME") or os.path.expanduser("~/.openclaw")
    pid_file = os.path.join(home, "gateway", "gateway.pid")
    try:
        if os.path.exists(pid_file):
            with open(pid_file) as fh:
                pid = int((fh.read() or "0").strip())
            if pid > 0:
                # Portable probe: os.kill(pid, 0) never raises on Windows,
                # so a stale gateway.pid would read as "running" forever.
                from clawmetry.process_control import is_alive as _pid_alive

                if _pid_alive(pid):
                    return True
    except (OSError, ValueError):
        pass
    try:
        import socket as _sock
        s = _sock.socket(_sock.AF_INET, _sock.SOCK_STREAM)
        s.settimeout(0.2)
        rc = s.connect_ex(("127.0.0.1", 18789))
        s.close()
        return rc == 0
    except Exception:
        return False


def _is_docker_runtime_down() -> Optional[bool]:
    """True when Docker daemon is present but not responding, False when
    healthy, None when docker CLI is absent (not a Docker-backed environment).
    Never raises.
    """
    try:
        import shutil as _sh
        if not _sh.which("docker"):
            return None
        import subprocess as _sp
        rc = _sp.run(
            ["docker", "info"],
            capture_output=True, timeout=3,
        ).returncode
        return rc != 0
    except Exception:
        return None


def _openclaw_doctor_findings() -> list:
    """Run ``openclaw doctor --json`` and return the list of structured
    diagnostic findings (auth-profile, workspace, device-pairing,
    channel-plugin, memory-provider, systemd-exhaustion, LAN-firewall).
    Available since OpenClaw harness 2026.7.1 (#97125+). Returns [] when
    openclaw is absent, the --json flag is unsupported, or output is not
    valid JSON. Never raises.
    """
    try:
        import shutil as _sh
        if not _sh.which("openclaw"):
            return []
        import subprocess as _sp
        res = _sp.run(
            ["openclaw", "doctor", "--json"],
            capture_output=True, text=True, timeout=15,
        )
        raw = (res.stdout or "").strip()
        if not raw:
            return []
        import json as _json
        data = _json.loads(raw)
        if isinstance(data, list):
            return data
        if isinstance(data, dict):
            for _key in ("findings", "results", "diagnostics"):
                if isinstance(data.get(_key), list):
                    return data[_key]
        return []
    except Exception:
        return []


def _clawrouter_detect() -> dict:
    """Detect the ClawRouter bundled provider plugin (OpenClaw 2026.7.1, #99658).

    ClawRouter adds credential-scoped dynamic model discovery,
    OpenAI-compatible + native Anthropic/Gemini transports, and managed
    budget/quota reporting across OpenClaw usage surfaces. Config and quota
    data are written to ``~/.openclaw/clawrouter/`` by the harness onboarding
    step (override with ``OPENCLAW_CLAWROUTER_HOME``).

    Returns a dict with zero or more of:
    - ``clawRouterEnabled`` (bool)
    - ``clawRouterVersion`` (str)
    - ``clawRouterTransports`` (list[str])
    - ``clawRouterModels`` (list[str])
    - ``clawRouterBudgetUsd`` (float) — aggregate managed budget in USD
    - ``clawRouterQuotaCredentials`` (int) — number of credential scopes

    Returns ``{}`` when the plugin is absent (pre-2026.7.1 or unconfigured).
    Read-only, never raises.
    """
    import json as _json

    home = os.environ.get("OPENCLAW_CLAWROUTER_HOME") or os.path.expanduser(
        os.path.join("~", ".openclaw", "clawrouter"))
    config_path = os.path.join(home, "config.json")
    quota_path = os.path.join(home, "quota.json")

    out: dict = {}

    # Main config: enabled flag, version, transport list, model catalog
    try:
        with open(config_path, encoding="utf-8") as _fh:
            cfg = _json.load(_fh)
        out["clawRouterEnabled"] = bool(cfg.get("enabled", True))
        version = cfg.get("version") or cfg.get("pluginVersion")
        if version:
            out["clawRouterVersion"] = str(version)
        transports = cfg.get("transports") or cfg.get("transport") or []
        if isinstance(transports, list) and transports:
            out["clawRouterTransports"] = [str(t) for t in transports if t]
        models = cfg.get("models") or cfg.get("modelCatalog") or []
        if isinstance(models, list) and models:
            out["clawRouterModels"] = [
                str(m.get("name") or m) if isinstance(m, dict) else str(m)
                for m in models if m
            ]
    except (OSError, ValueError, KeyError):
        pass

    # Quota file: aggregate managed budget + credential-scope count
    try:
        with open(quota_path, encoding="utf-8") as _fh:
            quota = _json.load(_fh)
        budget = quota.get("totalBudgetUsd") or quota.get("budgetUsd")
        if budget is not None:
            try:
                out["clawRouterBudgetUsd"] = float(budget)
            except (TypeError, ValueError):
                pass
        creds = quota.get("credentials") or quota.get("credentialScopes") or []
        if isinstance(creds, list) and creds:
            out["clawRouterQuotaCredentials"] = len(creds)
    except (OSError, ValueError, KeyError):
        pass

    # Promos file: ClawHub promotional model offers (#3570, openclaw#100236)
    promos_path = os.path.join(home, "promos.json")
    try:
        with open(promos_path, encoding="utf-8") as _fh:
            promos_data = _json.load(_fh)
        # List-of-claims format: {"claimedPromos": [...]} or {"claims": [...]}
        claims = (
            promos_data.get("claimedPromos")
            or promos_data.get("claims")
            or promos_data.get("activeClaims")
            or []
        )
        if isinstance(claims, list) and claims:
            active = [c for c in claims if isinstance(c, dict) and c.get("active", True)]
            if active:
                out["clawRouterPromoActive"] = True
                out["clawRouterPromoCount"] = len(active)
                first_model = active[0].get("modelRef") or active[0].get("model")
                if first_model:
                    out["clawRouterPromoModel"] = str(first_model)
        elif isinstance(promos_data.get("active"), bool):
            # Single-promo format: {"active": true, "modelRef": "...", ...}
            if promos_data["active"]:
                out["clawRouterPromoActive"] = True
                promo_model = promos_data.get("modelRef") or promos_data.get("model")
                if promo_model:
                    out["clawRouterPromoModel"] = str(promo_model)
    except (OSError, ValueError, KeyError):
        pass

    return out


def _real_install(sessions_dir: str) -> bool:
    """A genuine OpenClaw install signal, NOT the bare ~/.openclaw dir that
    ClawMetry itself creates as a scratch workspace. Any one of: the openclaw
    CLI/app, a gateway.pid, real session .jsonl files, or workspace markers."""
    import shutil as _shutil
    if _shutil.which("openclaw") or os.path.isdir("/Applications/OpenClaw.app"):
        return True
    home = os.environ.get("OPENCLAW_HOME") or os.path.expanduser("~/.openclaw")
    if os.path.exists(os.path.join(home, "gateway", "gateway.pid")):
        return True
    if sessions_dir and os.path.isdir(sessions_dir):
        try:
            if any(n.endswith(".jsonl") for n in os.listdir(sessions_dir)):
                return True
        except OSError:
            pass
    ws = os.path.join(home, "workspace")
    return any(os.path.exists(os.path.join(ws, m))
               for m in ("SOUL.md", "AGENTS.md", "MEMORY.md"))


def _model_router_fingerprint() -> dict:
    """Read the NemoClaw model-router source fingerprint (``git:<sha>``)
    written by harness onboarding to ``<venv>/.nemoclaw-source-fingerprint``
    (model-router.ts writeModelRouterInstalledFingerprint). Surfaces the
    install-provenance / version-drift signal on DetectResult.meta (#2608).

    Read-only and never raises. Returns ``{}`` when the file/venv is absent
    (plain OpenClaw or old NemoClaw installs), so the meta dict is unchanged.
    """
    venv = os.environ.get("NEMOCLAW_MODEL_ROUTER_VENV") or os.path.expanduser(
        os.path.join("~", ".nemoclaw", "model-router-venv"))
    fp_path = os.path.join(venv, ".nemoclaw-source-fingerprint")
    try:
        with open(fp_path, encoding="utf-8") as fh:
            raw = (fh.read() or "").strip()
        if not raw:
            return {}
        out = {"modelRouterFingerprint": raw}
        # raw looks like "git:<40hex>" / "gitlink:<40hex>" / "files:<hex>"
        if ":" in raw:
            kind, _, val = raw.partition(":")
            out["modelRouterFingerprintKind"] = kind
            if kind in ("git", "gitlink") and val:
                out["modelRouterSourceSha"] = val[:12]
        return out
    except (OSError, ValueError):
        return {}


def _model_router_currency() -> dict:
    """Compute the NemoClaw model-router currency verdict (#3652).

    Mirrors ``isManagedModelRouterCurrent()`` from harness
    ``src/lib/onboard/model-router.ts``: compares the installed fingerprint
    (``<venv>/.nemoclaw-source-fingerprint``) against the expected/current
    source pin (``<venv>/.nemoclaw-expected-fingerprint``) written by the
    harness during onboarding to record the SHA the current NemoClaw version
    pins its model-router to.

    Returns ``{"modelRouterCurrent": bool}`` when both files are present and
    readable; ``{}`` when either is absent (plain OpenClaw, old NemoClaw
    installs that pre-date the expected-pin file, or no venv at all).
    Never raises.
    """
    venv = os.environ.get("NEMOCLAW_MODEL_ROUTER_VENV") or os.path.expanduser(
        os.path.join("~", ".nemoclaw", "model-router-venv"))
    try:
        with open(os.path.join(venv, ".nemoclaw-source-fingerprint"), encoding="utf-8") as fh:
            installed = (fh.read() or "").strip()
        with open(os.path.join(venv, ".nemoclaw-expected-fingerprint"), encoding="utf-8") as fh:
            expected = (fh.read() or "").strip()
        if not installed or not expected:
            return {}
        return {"modelRouterCurrent": installed == expected}
    except (OSError, ValueError):
        return {}


def _resolve_ollama_host() -> str:
    """Return the active Ollama base URL from env vars or the default.

    Mirrors getOllamaModelOptions() priority in nemoclaw/dist/lib/inference/local.js:
    OLLAMA_HOST_DOCKER_INTERNAL → OLLAMA_LOCALHOST → http://localhost:11434.
    """
    from urllib.parse import urlparse
    for var in ("OLLAMA_HOST_DOCKER_INTERNAL", "OLLAMA_LOCALHOST"):
        val = os.environ.get(var, "").strip()
        if not val:
            continue
        if not val.startswith("http"):
            val = f"http://{val}"
        if not urlparse(val).port:
            val = f"{val}:11434"
        return val
    return "http://localhost:11434"


def _resolve_minimax_base_url() -> str:
    """Return the active Minimax base URL from env var or the default.

    Mirrors the MINIMAX_BASE_URL env var consumed by completeSimple()
    in openclaw/plugin-sdk/llm. Falls back to the standard Minimax API.
    """
    val = os.environ.get("MINIMAX_BASE_URL", "").strip()
    return val or "https://api.minimax.chat/v1"


def _resolve_llamacpp_base_url() -> str:
    """Return the active llama.cpp server base URL from env var or the default.

    LLAMA_CPP_HOST overrides; falls back to the llama.cpp server default port.
    """
    val = os.environ.get("LLAMA_CPP_HOST", "").strip()
    return val or "http://localhost:8080/v1"


def _resolve_lmstudio_base_url() -> str:
    """Return the active LM Studio server base URL from env var or the default.

    LMSTUDIO_HOST overrides; falls back to LM Studio's default port.
    """
    val = os.environ.get("LMSTUDIO_HOST", "").strip()
    return val or "http://localhost:1234/v1"


def _list_ollama_models(host: str) -> list:
    """Return available Ollama model names. Never raises; returns [] on failure.

    Tries GET {host}/api/tags first (same as the harness HTTP path). For
    loopback hosts only, also falls back to ``ollama list`` CLI on HTTP
    failure — matching the harness's getOllamaModelOptions() which skips the
    CLI fallback when OLLAMA_HOST_DOCKER_INTERNAL is set, so ollamaModels is
    never populated from the local workstation daemon for Docker-internal hosts.
    """
    import urllib.request
    from urllib.parse import urlparse
    try:
        url = host.rstrip("/") + "/api/tags"
        with urllib.request.urlopen(url, timeout=2) as resp:  # noqa: S310
            data = json.loads(resp.read())
            return [m["name"] for m in data.get("models", []) if m.get("name")]
    except Exception:
        pass
    # CLI fallback only for loopback hosts (#3391: harness parity)
    _hostname = urlparse(host).hostname or ""
    if _hostname not in ("localhost", "127.0.0.1", "::1"):
        return []
    try:
        import subprocess
        result = subprocess.run(
            ["ollama", "list"], capture_output=True, text=True, timeout=5
        )
        lines = result.stdout.strip().splitlines()
        return [ln.split()[0] for ln in lines[1:] if ln.split()]
    except Exception:
        return []



def _openshell_sandbox_phase_policy(name: str) -> dict:
    """Call 'openshell sandbox get <name>' and parse Phase / Policy / Runtime fields.

    Returns a dict with 'sandboxPhase', 'sandboxPolicy', and/or
    'sandboxRuntimeKind' keys from the CLI output.  Never raises; returns {}
    when the openshell binary is absent (plain OpenClaw installs) or the
    subprocess call fails, so existing entries are left unchanged.
    """
    try:
        import shutil as _sh
        if not _sh.which("openshell"):
            return {}
        import subprocess as _sp
        res = _sp.run(
            ["openshell", "sandbox", "get", name],
            capture_output=True, text=True, timeout=5,
        )
        out: dict = {}
        for line in (res.stdout or "").splitlines():
            if line.startswith("Phase:"):
                out["sandboxPhase"] = line.split(":", 1)[1].strip()
            elif line.startswith("Policy:"):
                out["sandboxPolicy"] = line.split(":", 1)[1].strip()
            elif line.startswith("Runtime:"):
                out["sandboxRuntimeKind"] = line.split(":", 1)[1].strip()
        return out
    except Exception:
        return {}


def _openshell_sandbox_ocsf_enabled(name: str) -> dict:
    """Call 'openshell settings get <name>' and surface sandboxOcsfJsonEnabled.

    Returns {"sandboxOcsfJsonEnabled": bool} when the ocsf_json_enabled key
    is present in the settings output, {} otherwise.  Never raises; returns {}
    when openshell is absent (plain OpenClaw installs) or the call fails.
    """
    try:
        import shutil as _sh
        if not _sh.which("openshell"):
            return {}
        import subprocess as _sp
        res = _sp.run(
            ["openshell", "settings", "get", name],
            capture_output=True, text=True, timeout=5,
        )
        for line in (res.stdout or "").splitlines():
            stripped = line.strip()
            if stripped.startswith("ocsf_json_enabled:"):
                val = stripped.split(":", 1)[1].strip().lower()
                return {"sandboxOcsfJsonEnabled": val == "true"}
        return {}
    except Exception:
        return {}


def _read_logging_file_config() -> str:
    """Read ``logging.file`` from openclaw.json and return the path string.

    openclaw.json can redirect gateway log output to an arbitrary path via
    ``{"logging": {"file": "/custom/path/openclaw.log"}}``.  Returns the
    string value when present, empty string otherwise.  Never raises (#4054).
    """
    try:
        home = os.environ.get("OPENCLAW_HOME") or os.path.expanduser("~/.openclaw")
        cfg_path = os.path.join(home, "openclaw.json")
        if not os.path.isfile(cfg_path):
            alt = os.path.expanduser("~/.clawdbot/openclaw.json")
            if os.path.isfile(alt):
                cfg_path = alt
            else:
                return ""
        with open(cfg_path) as _fh:
            cfg = json.load(_fh)
        if not isinstance(cfg, dict):
            return ""
        logging_cfg = cfg.get("logging")
        if not isinstance(logging_cfg, dict):
            return ""
        log_file = logging_cfg.get("file")
        return str(log_file) if log_file else ""
    except Exception:
        return ""


def _read_logging_level_config() -> str:
    """Read ``logging.level`` from openclaw.json and return the level string.

    openclaw.json can set a minimum severity for the file transport via
    ``{"logging": {"level": "warn"}}``.  Returns the level string (lower-cased)
    when present, empty string otherwise.  Never raises (#5060).
    """
    try:
        home = os.environ.get("OPENCLAW_HOME") or os.path.expanduser("~/.openclaw")
        cfg_path = os.path.join(home, "openclaw.json")
        if not os.path.isfile(cfg_path):
            alt = os.path.expanduser("~/.clawdbot/openclaw.json")
            if os.path.isfile(alt):
                cfg_path = alt
            else:
                return ""
        with open(cfg_path) as _fh:
            cfg = json.load(_fh)
        if not isinstance(cfg, dict):
            return ""
        logging_cfg = cfg.get("logging")
        if not isinstance(logging_cfg, dict):
            return ""
        level = logging_cfg.get("level")
        return str(level).lower() if level else ""
    except Exception:
        return ""


def _gateway_log_files() -> list:
    """Return the newest-5 rotating gateway log files across known candidate dirs.

    The gateway writes dated, rotating JSONL logs to ``{log_dir}/openclaw-YYYY-MM-DD.log``
    (rotates at 100 MB, keeps up to 5 archives). Candidate directories mirror the
    log_dir resolution logic in ``sync.py``'s ``_get_paths()``.
    Never raises; returns an empty list when no log files are found.
    """
    openclaw_dir = os.environ.get(
        "CLAWMETRY_OPENCLAW_DIR", os.path.expanduser("~/.openclaw")
    )
    candidates = [
        "/tmp/openclaw",
        os.path.join(openclaw_dir, "logs"),
    ]

    # If openclaw.json sets logging.file, check that path's parent directory
    # first so installs with a custom log location are visible (#4054).
    custom_log_file = _read_logging_file_config()
    if custom_log_file:
        custom_dir = os.path.dirname(os.path.abspath(custom_log_file))
        if custom_dir not in candidates:
            candidates.insert(0, custom_dir)

    # On Windows and on hosts where /tmp/openclaw is unsafe the gateway writes
    # to a user-scoped openclaw-* directory under the OS temp dir instead.
    tmp_base = tempfile.gettempdir()
    for entry in sorted(glob.glob(os.path.join(tmp_base, "openclaw-*"))):
        if os.path.isdir(entry):
            candidates.append(entry)
    for d in candidates:
        matches = sorted(
            m for m in glob.glob(os.path.join(d, "openclaw-*.log"))
            if _DEFAULT_LOG_RE.search(os.path.basename(m))
        )
        if matches:
            return matches[-5:]

    # Fallback: if logging.file points to a single file that doesn't match the
    # rotation naming pattern, return it directly so callers still see events.
    if custom_log_file and os.path.isfile(custom_log_file):
        return [custom_log_file]

    return []


def _gateway_log_meta() -> dict:
    """Return gateway log metadata for detect(): dir, archive count, current file size.

    Surfaces ``gatewayLogDir``, ``gatewayLogArchiveCount``, and
    ``gatewayLogCurrentSizeKb`` so the dashboard can show log location and
    rotation state for plain OpenClaw installs. Returns ``{}`` when no log
    files are present (non-OpenClaw host or gateway never started).
    Never raises.
    """
    try:
        files = _gateway_log_files()
        if not files:
            return {}
        result: dict = {
            "gatewayLogDir": os.path.dirname(files[0]),
            "gatewayLogArchiveCount": len(files),
        }
        try:
            result["gatewayLogCurrentSizeKb"] = round(
                os.path.getsize(files[-1]) / 1024, 1
            )
        except OSError:
            pass
        level = _read_logging_level_config()
        if level:
            result["gatewayLogLevel"] = level
        return result
    except Exception:
        return {}


def _gateway_log_events(count: int = 50) -> list:
    """Return the last ``count`` structured events from the gateway log file.

    The gateway writes line-delimited JSON to rotating ``openclaw-*.log`` files
    (same paths as ``_gateway_log_files()``).  Each line carries at minimum
    ``level`` and ``msg``; most also carry ``subsystem`` and a timestamp field
    (``time``, ``ts``, or ``timestamp``).

    Falls back to the ``gateway.logs`` WebSocket RPC when no local log files
    are accessible (remote / containerised gateway with no shared filesystem).
    Closes #4057.

    Returns a list of event dicts, newest-first.  Returns ``[]`` when no log
    file exists, on any parse error, or on non-OpenClaw hosts.  Never raises.

    Closes #3991.
    """
    try:
        files = _gateway_log_files()
        if not files:
            return _gateway_log_events_rpc(count)
        log_path = files[-1]
        # Read a trailing chunk large enough to hold ``count`` typical lines
        # (~300 bytes each) without loading the full (potentially large) log.
        chunk_size = max(8192, count * 300)
        try:
            with open(log_path, "rb") as fh:
                fh.seek(0, 2)
                size = fh.tell()
                fh.seek(max(0, size - chunk_size))
                raw_bytes = fh.read()
        except OSError:
            return _gateway_log_events_rpc(count)
        lines = raw_bytes.decode("utf-8", "replace").splitlines()
        events: list = []
        for raw in reversed(lines):
            raw = raw.strip()
            if not raw:
                continue
            try:
                obj = json.loads(raw)
            except (ValueError, TypeError):
                continue
            if not isinstance(obj, dict):
                continue
            evt: dict = {}
            # Timestamp — accept any common key name.
            for _ts_key in ("time", "ts", "timestamp"):
                _ts_val = obj.get(_ts_key)
                if _ts_val is not None:
                    evt["ts"] = _ts_val
                    break
            for _field, _key in (
                ("level", "level"),
                ("msg", "msg"),
                ("message", "msg"),
                ("subsystem", "subsystem"),
            ):
                _val = obj.get(_field)
                if _val is not None and _key not in evt:
                    evt[_key] = _val
            if evt:
                events.append(evt)
            if len(events) >= count:
                break
        return events or _gateway_log_events_rpc(count)
    except Exception:
        return []


def _gateway_log_events_rpc(count: int = 50) -> list:
    """Return the last ``count`` gateway log events via WebSocket RPC.

    Calls ``gateway.logs`` with ``{"count": count}``; the response payload is
    expected to carry an ``events`` (or ``lines`` / ``entries`` / ``logs``) list
    of structured event dicts.  Used as a fallback by ``_gateway_log_events``
    when no local log files are accessible (remote / containerised gateway).
    Closes #4057.  Never raises; returns ``[]`` on any failure.
    """
    try:
        rpc = getattr(_d(), "_gw_ws_rpc", None)
        if rpc is None:
            return []
        payload = rpc("gateway.logs", {"count": count})
        if not isinstance(payload, dict):
            return []
        raw_events = None
        for _key in ("events", "lines", "entries", "logs"):
            _val = payload.get(_key)
            if isinstance(_val, list):
                raw_events = _val
                break
        if not raw_events:
            return []
        events: list = []
        for obj in raw_events:
            if not isinstance(obj, dict):
                continue
            evt: dict = {}
            for _ts_key in ("time", "ts", "timestamp"):
                _ts_val = obj.get(_ts_key)
                if _ts_val is not None:
                    evt["ts"] = _ts_val
                    break
            for _field, _key in (
                ("level", "level"),
                ("msg", "msg"),
                ("message", "msg"),
                ("subsystem", "subsystem"),
            ):
                _val = obj.get(_field)
                if _val is not None and _key not in evt:
                    evt[_key] = _val
            if evt:
                events.append(evt)
            if len(events) >= count:
                break
        return events
    except Exception:
        return []


def _gateway_log_events_probe(count: int = 50) -> tuple:
    """Run _gateway_log_events with a NEMOCLAW_LOGS_PROBE_TIMEOUT_MS budget.

    The NemoClaw harness CLI has a bounded probe around fetching the
    OpenClaw-side log (NEMOCLAW_LOGS_PROBE_TIMEOUT_MS in
    test/cli/logs.test.ts): on timeout it emits a distinct degraded-mode
    signal rather than silently returning empty. This function mirrors that
    posture so ClawMetry can surface the same diagnostic (#5293).

    Returns (events, source_available) where source_available=False means
    the probe timed out, letting callers distinguish 'gateway log source
    unreachable / timing out' from 'source reachable but log is empty'.
    Never raises.
    """
    timeout_ms = int(os.environ.get("NEMOCLAW_LOGS_PROBE_TIMEOUT_MS", "5000"))
    timeout_s = max(0.5, timeout_ms / 1000.0)
    try:
        import concurrent.futures as _cf
        with _cf.ThreadPoolExecutor(max_workers=1) as _pool:
            _future = _pool.submit(_gateway_log_events, count)
            try:
                events = _future.result(timeout=timeout_s)
                return events, True
            except _cf.TimeoutError:
                return [], False
    except Exception:
        return [], False


def _openshell_sandbox_logs(name: str, count: int = 20) -> list:
    """Retrieve OCSF JSON audit log lines for a NemoClaw sandbox.

    Arms OCSF output first (idempotent settings set), then calls
    ``openshell logs <name> -n <count> --source all``.  For container-backed
    (non-terminal) sandboxes also merges the last ``count`` lines from the
    OpenClaw gateway log, matching the harness's two-source merge in
    ``showSandboxLogsWithDeps`` (#3571).

    Gateway log resolution order for non-terminal sandboxes:
    1. ``OPENSHELL_GATEWAY_LOG`` env override (for testing / explicit override).
    2. Host-side rotating log files found by ``_gateway_log_files()``.
    3. ``openshell sandbox exec -n <name> -- tail -n <count> /tmp/gateway.log``
       — the fallback for genuinely container-backed sandboxes where the
       gateway writes its log inside the container, not on the host (#5291).

    Returns a list of parsed OCSF event dicts; silently drops non-JSON lines.
    Never raises; returns ``[]`` when openshell is absent or any call fails.
    """
    try:
        import shutil as _sh
        if not _sh.which("openshell"):
            return []
        import subprocess as _sp
        _sp.run(
            ["openshell", "settings", "set", name,
             "--key", "ocsf_json_enabled", "--value", "true"],
            capture_output=True, text=True, timeout=5,
        )
        res = _sp.run(
            ["openshell", "logs", name, "-n", str(count), "--source", "all"],
            capture_output=True, text=True, timeout=10,
        )
        events = []
        for line in (res.stdout or "").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                events.append(json.loads(line))
            except Exception:
                pass
        # For container-backed (non-terminal) sandboxes the harness also tails
        # the gateway log. The gateway writes rotating dated files at
        # {log_dir}/openclaw-YYYY-MM-DD.log, not a static /tmp/gateway.log.
        # Use _gateway_log_files() so we find the actual current log regardless
        # of host layout; fall back to OPENSHELL_GATEWAY_LOG for test overrides.
        phase_info = _openshell_sandbox_phase_policy(name)
        if phase_info.get("sandboxRuntimeKind", "").lower() != "terminal":
            _gw_log_override = os.environ.get("OPENSHELL_GATEWAY_LOG")
            _gw_candidates = (
                [_gw_log_override] if _gw_log_override else _gateway_log_files()
            )
            _gw_log_path = _gw_candidates[-1] if _gw_candidates else None
            if _gw_log_path:
                try:
                    with open(_gw_log_path, "r", encoding="utf-8", errors="replace") as _gf:
                        _gw_lines = _gf.readlines()[-count:]
                    for _gw_line in _gw_lines:
                        _gw_line = _gw_line.strip()
                        if not _gw_line:
                            continue
                        try:
                            events.append(json.loads(_gw_line))
                        except Exception:
                            pass
                except OSError:
                    pass
            elif not _gw_log_override:
                # No host-side log found and no explicit override: the gateway log
                # lives inside the container.  Read it via `sandbox exec`, which is
                # exactly what the harness does in showSandboxLogsWithDeps (#5291).
                try:
                    _exec_res = _sp.run(
                        ["openshell", "sandbox", "exec", "-n", name, "--",
                         "tail", "-n", str(count), "/tmp/gateway.log"],
                        capture_output=True, text=True, timeout=10,
                    )
                    for _exec_line in (_exec_res.stdout or "").splitlines():
                        _exec_line = _exec_line.strip()
                        if not _exec_line:
                            continue
                        try:
                            events.append(json.loads(_exec_line))
                        except Exception:
                            pass
                except Exception:
                    pass
        return events
    except Exception:
        return []


def _sandbox_egress_denied_count(name: str, count: int = 100) -> dict:
    """Summarise OCSF audit events from recent sandbox logs (#3616).

    Fetches the <count> most-recent OCSF audit events for sandbox <name> and
    classifies every event into one of three buckets:

    - Network-egress denied  (class_uid 4001-4004 or endpoint fields, verdict==deny)
      → ``egressDeniedCount``
    - Network-egress allowed (class_uid 4001-4004 or endpoint fields, verdict==allow)
      → ``egressAllowedCount``
    - Non-network audit      (process-activity, file-activity, auth events, …)
      → ``processFileAuthAuditCount``

    Each key is omitted when its count is zero, preserving the .update()-friendly
    contract used by callers.  Never raises.
    """
    _NETWORK_CLASS_UIDS = frozenset([4001, 4002, 4003, 4004])
    try:
        events = _openshell_sandbox_logs(name, count=count)
        denied = 0
        allowed = 0
        non_network = 0
        for evt in events:
            if not isinstance(evt, dict):
                continue
            class_uid = evt.get("class_uid")
            is_network = (
                class_uid in _NETWORK_CLASS_UIDS
                or "dst_endpoint" in evt
                or "src_endpoint" in evt
            )
            if is_network:
                verdict = evt.get("verdict")
                if verdict == "deny":
                    denied += 1
                elif verdict == "allow":
                    allowed += 1
            else:
                non_network += 1
        result: dict = {}
        if denied:
            result["egressDeniedCount"] = denied
        if allowed:
            result["egressAllowedCount"] = allowed
        if non_network:
            result["processFileAuthAuditCount"] = non_network
        return result
    except Exception:
        return {}


class _MergedProc:
    """Wraps multiple Popen objects and merges their stdout into one stream.

    The sync daemon expects a single (proc, PipeLineReader) pair per sandbox.
    This shim provides the same interface — ``.stdout``, ``.poll()``,
    ``.terminate()``, ``.wait()`` — when the live-tail path needs two child
    processes simultaneously (OCSF audit stream + gateway log follow for
    container-backed sandboxes, issue #5398).
    """

    def __init__(self, procs):
        import os as _os
        import threading as _th
        self._procs = list(procs)
        r_fd, w_fd = _os.pipe()
        self.stdout = _os.fdopen(r_fd, "r", buffering=1)
        self._wfile = _os.fdopen(w_fd, "w", buffering=1)
        self._threads = []
        for p in self._procs:
            t = _th.Thread(target=self._pump, args=(p.stdout,), daemon=True)
            t.start()
            self._threads.append(t)
        closer = _th.Thread(target=self._close_write_end, daemon=True)
        closer.start()

    def _pump(self, src):
        try:
            for line in src:
                try:
                    self._wfile.write(line)
                    self._wfile.flush()
                except Exception:
                    break
        except Exception:
            pass

    def _close_write_end(self):
        for t in self._threads:
            t.join()
        try:
            self._wfile.close()
        except Exception:
            pass

    def poll(self):
        """Return None if any child is still alive; 0 when all have exited."""
        for p in self._procs:
            if p.poll() is None:
                return None
        return 0

    def terminate(self):
        for p in self._procs:
            try:
                p.terminate()
            except Exception:
                pass

    def wait(self):
        for p in self._procs:
            try:
                p.wait()
            except Exception:
                pass


def _openshell_sandbox_logs_tail(name: str):
    """Spawn ``openshell logs <name> --source all --tail`` as a long-lived child
    process and return the ``subprocess.Popen`` handle.

    For container-backed (non-terminal) sandboxes also spawns a ``tail -f`` on
    the OpenClaw gateway log, matching the harness's two-source merge in the
    live-follow path (issue #5398).  When both sources are active the return
    value is a :class:`_MergedProc` that multiplexes both streams under the
    same ``.stdout`` / ``.poll()`` / ``.terminate()`` / ``.wait()`` interface,
    so the sync daemon's drain loop in ``clawmetry/sync.py`` needs no changes.

    Gateway log resolution order for non-terminal sandboxes mirrors
    ``_openshell_sandbox_logs()``:
    1. ``OPENSHELL_GATEWAY_LOG`` env override.
    2. Host-side rotating log files from ``_gateway_log_files()``.
    3. ``openshell sandbox exec -n <name> -- tail -n 200 -f /tmp/gateway.log``
       for container-internal gateway logs.

    The caller owns process lifetime — drain stdout non-blockingly each sync
    tick and call ``proc.terminate()`` + ``proc.wait()`` on daemon shutdown.
    Returns ``None`` when openshell is absent or the spawn fails; never raises.
    """
    try:
        import shutil as _sh
        if not _sh.which("openshell"):
            return None
        import subprocess as _sp
        ocsf_proc = _sp.Popen(
            ["openshell", "logs", name, "--source", "all", "--tail"],
            stdout=_sp.PIPE, stderr=_sp.DEVNULL, text=True, bufsize=1,
        )
        # For container-backed (non-terminal) sandboxes also follow the gateway
        # log, matching the harness's two-source merge for `alpha logs --follow`
        # (#5398).  Follows the same resolution order as _openshell_sandbox_logs().
        phase_info = _openshell_sandbox_phase_policy(name)
        if phase_info.get("sandboxRuntimeKind", "").lower() != "terminal":
            _gw_log_override = os.environ.get("OPENSHELL_GATEWAY_LOG")
            _gw_candidates = (
                [_gw_log_override] if _gw_log_override else _gateway_log_files()
            )
            _gw_log_path = _gw_candidates[-1] if _gw_candidates else None
            gw_proc = None
            try:
                if _gw_log_path:
                    gw_proc = _sp.Popen(
                        ["tail", "-n", "200", "-f", _gw_log_path],
                        stdout=_sp.PIPE, stderr=_sp.DEVNULL, text=True, bufsize=1,
                    )
                elif not _gw_log_override:
                    gw_proc = _sp.Popen(
                        ["openshell", "sandbox", "exec", "-n", name, "--",
                         "tail", "-n", "200", "-f", "/tmp/gateway.log"],
                        stdout=_sp.PIPE, stderr=_sp.DEVNULL, text=True, bufsize=1,
                    )
            except Exception:
                gw_proc = None
            if gw_proc is not None:
                return _MergedProc([ocsf_proc, gw_proc])
        return ocsf_proc
    except Exception:
        return None


def _sandbox_inference_configs() -> list:
    """Read per-sandbox inference config from ~/.nemoclaw/sandboxes.json.

    Mirrors getSandboxInferenceConfig() (nemoclaw/src/lib/inference/config.ts)
    to surface providerKey / primaryModelRef / inferenceBaseUrl / inferenceApi /
    inferenceCompat on DetectResult.meta (gap #2796). Ollama-backed sandboxes
    also receive ollamaHost + ollamaModels (gap #3201). The identical derivation
    lives in sync._read_nemoclaw_sandbox_routing (#2684); this helper makes it
    available in the adapter layer without importing the heavy sync module.
    Also calls _openshell_sandbox_phase_policy() per sandbox to surface live
    Phase / Policy fields (gap #3202).
    Never raises -- returns [] on plain OpenClaw (no sandboxes.json).
    """
    home = os.environ.get("HOME") or os.path.expanduser("~")
    reg = os.path.join(home, ".nemoclaw", "sandboxes.json")
    out: list = []
    try:
        with open(reg, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    except Exception:
        return out
    if not isinstance(data, dict):
        return out
    default_sb = data.get("defaultSandbox")
    sandboxes = data.get("sandboxes")
    if not isinstance(sandboxes, dict):
        return out
    _MANAGED = "inference"
    _MANAGED_URL = "https://inference.local/v1"
    for name, entry in sandboxes.items():
        try:
            if not isinstance(entry, dict):
                continue
            provider = entry.get("provider") or ""
            model = entry.get("model") or ""
            api = entry.get("preferredInferenceApi") or "openai-completions"
            # Read runtimeKind from JSON before the loop variable is shadowed
            # below. openshell output takes precedence; this is the fallback.
            json_runtime_kind = (
                entry.get("runtimeKind")
                or (entry.get("runtime") or {}).get("kind")
                or ""
            )
            # Read sandboxGpuProof before entry is reassigned (gap #3994).
            raw_gpu_proof = entry.get("sandboxGpuProof")
            base_url = _MANAGED_URL
            if provider == "openai-api":
                provider_key = "openai"
                primary = f"openai/{model}" if model else ""
                compat = "openai"
            elif provider == "anthropic-prod" or (
                provider == "compatible-anthropic-endpoint"
                and api != "openai-completions"
            ):
                provider_key = "anthropic"
                primary = f"anthropic/{model}" if model else ""
                base_url = "https://inference.local"
                api = "anthropic-messages"
                compat = "anthropic"
            elif provider == "ollama":
                ollama_host = _resolve_ollama_host()
                entry = {
                    "sandbox": name,
                    "isDefault": bool(default_sb and name == default_sb),
                    "provider": provider,
                    "model": model,
                    "providerKey": "ollama",
                    "primaryModelRef": f"ollama/{model}" if model else "",
                    "inferenceBaseUrl": ollama_host,
                    "inferenceApi": api,
                    "inferenceCompat": "openai",
                    "ollamaHost": ollama_host,
                    "ollamaModels": _list_ollama_models(ollama_host),
                }
                entry.update(_openshell_sandbox_phase_policy(name))
                entry.update(_openshell_sandbox_ocsf_enabled(name))
                entry.update(_sandbox_egress_denied_count(name))
                if json_runtime_kind and "sandboxRuntimeKind" not in entry:
                    entry["sandboxRuntimeKind"] = json_runtime_kind
                if isinstance(raw_gpu_proof, dict):
                    entry["sandboxGpuProof"] = raw_gpu_proof
                out.append(entry)
                continue
            elif provider in ("minimax", "minimax-api"):
                provider_key = "minimax"
                primary = f"minimax/{model}" if model else ""
                base_url = _resolve_minimax_base_url()
                compat = "openai"
            elif provider == "llama.cpp":
                provider_key = "llama-cpp"
                primary = f"llama-cpp/{model}" if model else ""
                base_url = _resolve_llamacpp_base_url()
                compat = "openai"
            elif provider in ("lmstudio", "lm-studio"):
                provider_key = "lmstudio"
                primary = f"lmstudio/{model}" if model else ""
                base_url = _resolve_lmstudio_base_url()
                compat = "openai"
            else:
                provider_key = _MANAGED
                primary = f"{_MANAGED}/{model}" if model else ""
                compat = "openai"
            entry = {
                "sandbox": name,
                "isDefault": bool(default_sb and name == default_sb),
                "provider": provider,
                "model": model,
                "providerKey": provider_key,
                "primaryModelRef": primary,
                "inferenceBaseUrl": base_url,
                "inferenceApi": api,
                "inferenceCompat": compat,
            }
            entry.update(_openshell_sandbox_phase_policy(name))
            entry.update(_openshell_sandbox_ocsf_enabled(name))
            entry.update(_sandbox_egress_denied_count(name))
            if json_runtime_kind and "sandboxRuntimeKind" not in entry:
                entry["sandboxRuntimeKind"] = json_runtime_kind
            if isinstance(raw_gpu_proof, dict):
                entry["sandboxGpuProof"] = raw_gpu_proof
            out.append(entry)
        except Exception:
            continue

    # -- gap #3503: terminal/agent-execution sandboxes not in sandboxes.json --
    # agents.yaml carries the *intent* roster; terminal-kind coding-agent
    # sandboxes (e.g. deepagents-code) have no inference-routing entry and are
    # invisible to the loop above. Discover them from agents.yaml and probe
    # each with the openshell helpers so Phase/Policy/Runtime/OCSF/egress data
    # reaches the dashboard exactly as it does for inference-routing sandboxes.
    _seen = {e["sandbox"] for e in out}
    try:
        _home2 = os.environ.get("HOME") or os.path.expanduser("~")
        _manifest = os.path.join(_home2, ".nemoclaw", "agents.yaml")
        if os.path.isfile(_manifest):
            with open(_manifest, "r", encoding="utf-8") as _fh:
                _mc = _fh.read()
            _agents: list = []
            try:
                import yaml as _yaml  # type: ignore[import]
                _md = _yaml.safe_load(_mc)
                if isinstance(_md, dict):
                    _raw = _md.get("agents", [])
                    if isinstance(_raw, list):
                        _agents = [a for a in _raw if isinstance(a, dict)]
                    elif isinstance(_raw, dict):
                        _agents = [
                            {"name": k, **(v if isinstance(v, dict) else {})}
                            for k, v in _raw.items()
                        ]
                elif isinstance(_md, list):
                    _agents = [a for a in _md if isinstance(a, dict)]
            except ImportError:
                # yaml unavailable: line-scan for sandbox:/name: entries
                for _line in _mc.splitlines():
                    _s = _line.strip()
                    for _pfx in ("sandbox:", "- sandbox:"):
                        if _s.startswith(_pfx):
                            _v = _s[len(_pfx):].strip().strip("\"'")
                            if _v:
                                _agents.append({"sandbox": _v})
                            break
                    else:
                        if _s.startswith("- name:"):
                            _, _, _v2 = _s.partition(":")
                            _v2 = _v2.strip().strip("\"'")
                            if _v2:
                                _agents.append({"name": _v2})
            except Exception:
                _agents = []
            for _agent in _agents:
                if not isinstance(_agent, dict):
                    continue
                _sb = (_agent.get("sandbox") or _agent.get("name") or "").strip()
                if not _sb or _sb in _seen:
                    continue
                _seen.add(_sb)
                _te: dict = {
                    "sandbox": _sb,
                    "isDefault": False,
                    "provider": "terminal",
                    "providerKey": "terminal",
                    "primaryModelRef": "",
                    "sandboxSource": "agents.yaml",
                }
                _te.update(_openshell_sandbox_phase_policy(_sb))
                _te.update(_openshell_sandbox_ocsf_enabled(_sb))
                _te.update(_sandbox_egress_denied_count(_sb))
                # dcode session-supervisor feasibility (#3675): the supervisor
                # (dcode-session-supervisor.py) requires Linux + an OpenShell
                # sandbox and exits immediately with a fail-closed diagnostic
                # otherwise.  Surface a flag so unsupervised dcode sessions are
                # distinguishable from healthy ones.  True means both conditions
                # are met (Linux platform AND openshell phase data present),
                # matching the supervisor's own gate exactly.
                if "deepagents-code" in _sb.lower() or _sb.lower() == "dcode":
                    import sys as _sys
                    import shutil as _shutil
                    _platform_ok = _sys.platform.startswith("linux")
                    _openshell_ok = bool(_shutil.which("openshell"))
                    _te["dcodeSupervisionFeasible"] = (
                        _platform_ok and bool(_te.get("sandboxPhase"))
                    )
                    _te["dcodeSupervisionPlatformOk"] = _platform_ok
                    _te["dcodeOpenshellAvailable"] = _openshell_ok
                    if not _platform_ok:
                        _te["dcodeSupervisionFailReason"] = "non-linux platform"
                    elif not _openshell_ok:
                        _te["dcodeSupervisionFailReason"] = "openshell absent"
                    else:
                        _te["dcodeSupervisionFailReason"] = None
                    # dcode proxy-env activation (#4810): the dcode login
                    # profile sources /tmp/nemoclaw-proxy-env.sh before any
                    # managed exec command, routing sandbox traffic through
                    # the managed proxy.  A missing or empty file means the
                    # sandbox may run unrouted/unguarded even when supervision
                    # is otherwise feasible.
                    _proxy_env = "/tmp/nemoclaw-proxy-env.sh"
                    _proxy_env_present = os.path.isfile(_proxy_env)
                    _proxy_env_nonempty = (
                        _proxy_env_present
                        and os.path.getsize(_proxy_env) > 0
                    )
                    _te["dcodeProxyEnvPresent"] = _proxy_env_present
                    _te["dcodeProxyEnvNonEmpty"] = _proxy_env_nonempty
                    if not _proxy_env_present:
                        _te["dcodeProxyEnvFailReason"] = "env file absent"
                    elif not _proxy_env_nonempty:
                        _te["dcodeProxyEnvFailReason"] = "env file empty"
                    else:
                        _te["dcodeProxyEnvFailReason"] = None
                out.append(_te)
    except Exception:
        pass

    return out


def _nemoclaw_agents_manifest() -> dict:
    """Read the NemoClaw agents.yaml onboard manifest (#3185).

    The harness writes this declarative roster during onboarding
    (commit 01e5525 feat(onboard): add agents.yaml declarative manifest
    #5440). It sits alongside sandboxes.json, proxy-config.yaml, and
    .nemoclaw-source-fingerprint in ~/.nemoclaw/.

    Surfaces agentsManifest (full per-agent entries), agentCount, and
    agentNames on DetectResult.meta. Tries yaml.safe_load first (optional
    PyYAML dep); falls back to a line scan for agent names. Never raises —
    returns {} when the file is absent (plain OpenClaw or pre-01e5525
    NemoClaw installs).
    """
    home = os.environ.get("HOME") or os.path.expanduser("~")
    manifest_path = os.path.join(home, ".nemoclaw", "agents.yaml")
    if not os.path.isfile(manifest_path):
        return {}
    try:
        with open(manifest_path, encoding="utf-8") as fh:
            content = fh.read()
    except OSError:
        return {}
    if not content.strip():
        return {}

    agents: list = []
    try:
        import yaml as _yaml  # type: ignore[import]
        data = _yaml.safe_load(content)
        if isinstance(data, dict):
            raw = data.get("agents", [])
            if isinstance(raw, list):
                agents = [e for e in raw if isinstance(e, dict)]
            elif isinstance(raw, dict):
                # keyed by agent name: {agentName: {sandbox: ..., ...}}
                agents = [
                    {"name": k, **v} if isinstance(v, dict) else {"name": k}
                    for k, v in raw.items()
                ]
        elif isinstance(data, list):
            agents = [e for e in data if isinstance(e, dict)]
    except ImportError:
        pass
    except Exception:
        return {}

    if not agents:
        # Fallback: line scan for "- name: <value>" under an "agents:" block
        in_agents = False
        for line in content.splitlines():
            stripped = line.strip()
            if stripped == "agents:":
                in_agents = True
                continue
            if in_agents:
                if stripped.startswith("- name:"):
                    _, _, name = stripped.partition(":")
                    name = name.strip().strip("\"'")
                    if name:
                        agents.append({"name": name})
                elif stripped and not stripped.startswith(("-", " ", "#")):
                    in_agents = False

    if not agents:
        return {}

    names = [a["name"] for a in agents if isinstance(a.get("name"), str) and a["name"]]
    out: dict = {"agentsManifest": agents, "agentCount": len(agents)}
    if names:
        out["agentNames"] = names
    return out


def _discover_model_router_port() -> Optional[int]:
    """Find the ``--port`` of a running ``model-router proxy`` process.

    Harness onboarding starts the proxy via ``model-router proxy --port <n>``
    (port ``44000 + pid % 10000``), so the port is not derivable without the
    pid — we read it back off the live process command line. psutil with a
    ``/proc`` fallback, mirroring ``clawmetry.cli``. Returns ``None`` when no
    such process is running. Read-only, never raises.
    """
    def _port_from_cmd(cmd: str) -> Optional[int]:
        if "model-router" not in cmd or "proxy" not in cmd:
            return None
        toks = cmd.split()
        for i, t in enumerate(toks):
            if t == "--port" and i + 1 < len(toks) and toks[i + 1].isdigit():
                return int(toks[i + 1])
            if t.startswith("--port=") and t.split("=", 1)[1].isdigit():
                return int(t.split("=", 1)[1])
        return None

    try:
        import psutil  # type: ignore
        for p in psutil.process_iter(["cmdline"]):
            try:
                port = _port_from_cmd(" ".join(p.info.get("cmdline") or []))
                if port is not None:
                    return port
            except Exception:
                pass
        return None
    except ImportError:
        pass
    try:
        for pid_str in os.listdir("/proc"):
            if not pid_str.isdigit():
                continue
            try:
                with open(f"/proc/{pid_str}/cmdline") as fh:
                    cmd = fh.read().replace("\x00", " ")
                port = _port_from_cmd(cmd)
                if port is not None:
                    return port
            except Exception:
                pass
    except Exception:
        pass
    return None


def _model_router_health_check(port: int):
    """Probe the model-router ``/health`` endpoint and parse the response body.

    Returns ``(is_running: bool, pool_detail: Optional[dict])`` where
    ``pool_detail`` carries ``healthy_endpoints`` and/or
    ``unhealthy_endpoints`` lists when the router returns a parseable JSON
    body (the NemoClaw ROUTER_HEALTHY_BODY shape). Both are ``None``/``False``
    on any failure. Falls back to a raw TCP connect when the HTTP probe errors;
    in that case ``pool_detail`` is always ``None``. Never raises.
    """
    import json as _json
    import urllib.request as _u

    try:
        req = _u.Request(f"http://127.0.0.1:{port}/health", method="GET")
        with _u.urlopen(req, timeout=0.3) as resp:  # nosec B310 - localhost only
            status = getattr(resp, "status", None) or resp.getcode()
            ok = 200 <= int(status) < 300
            pool_detail = None
            if ok:
                try:
                    raw = resp.read(65536).decode("utf-8", errors="replace")
                    parsed = _json.loads(raw)
                    if isinstance(parsed, dict):
                        detail = {}
                        if "healthy_endpoints" in parsed:
                            detail["healthy_endpoints"] = parsed["healthy_endpoints"]
                        if "unhealthy_endpoints" in parsed:
                            detail["unhealthy_endpoints"] = parsed["unhealthy_endpoints"]
                        if detail:
                            pool_detail = detail
                except Exception:
                    pass
            return ok, pool_detail
    except Exception:
        pass
    try:
        import socket as _sock
        s = _sock.socket(_sock.AF_INET, _sock.SOCK_STREAM)
        s.settimeout(0.2)
        rc = s.connect_ex(("127.0.0.1", port))
        s.close()
        return rc == 0, None
    except Exception:
        return False, None


def _model_router_health_ok(port: int) -> bool:
    """True if the model-router ``/health`` endpoint answers 2xx on localhost.

    Falls back to a raw TCP connect (port accepting connections) when the HTTP
    probe errors, so a wedged-but-listening router still reads as up. Short
    timeouts keep detect() fast. Never raises.
    """
    return _model_router_health_check(port)[0]


def _model_router_launch_log(tail_lines: int = 50) -> Optional[str]:
    """Read the NemoClaw model-router launch log (#3721).

    The provisioning path writes a startup log during harness onboarding
    (``readRouterLaunchLog`` in the harness test helper). ClawMetry surfaces
    the last ``tail_lines`` lines so a failed startup is diagnosable from the
    dashboard rather than just showing a binary not-running verdict.

    Path resolution (first match wins):
    1. ``NEMOCLAW_MODEL_ROUTER_LOG`` env var override.
    2. ``<venv>/model-router.log`` (same directory as fingerprint + proxy-config
       files — the canonical NemoClaw model-router directory).
    3. ``~/.nemoclaw/model-router.log`` (home-directory fallback).

    Returns the last ``tail_lines`` as a stripped string, or ``None`` when no
    log file is found. Never raises.
    """
    venv = os.environ.get("NEMOCLAW_MODEL_ROUTER_VENV") or os.path.expanduser(
        os.path.join("~", ".nemoclaw", "model-router-venv")
    )
    candidates = [
        os.environ.get("NEMOCLAW_MODEL_ROUTER_LOG", ""),
        os.path.join(venv, "model-router.log"),
        os.path.expanduser(os.path.join("~", ".nemoclaw", "model-router.log")),
    ]
    for path in candidates:
        if not path:
            continue
        try:
            with open(path, "r", encoding="utf-8", errors="replace") as fh:
                lines = fh.readlines()
            return "".join(lines[-tail_lines:]).strip() or None
        except OSError:
            continue
        except Exception:
            continue
    return None


def _model_router_live() -> dict:
    """Runtime-liveness signal for the NemoClaw model-router proxy (#2795).

    ``_model_router_fingerprint`` only proves the router was *installed*;
    without a runtime probe a crashed router is indistinguishable from a
    healthy one. This discovers the live proxy and polls its ``/health``
    endpoint, surfacing the distinct liveness signal on ``DetectResult.meta``.

    When the router is not running, includes ``modelRouterLaunchLog`` (last 50
    lines of the startup log, #3721) so a failed start is diagnosable from the
    dashboard. The key is absent when no log file exists.

    Returns ``{"modelRouterRunning": bool}`` (plus ``modelRouterPort`` when the
    listening port is discoverable, and ``modelRouterLaunchLog`` when a log
    file is present). Read-only, best-effort, never raises.
    """
    port = _discover_model_router_port()
    if port is None:
        result: dict = {"modelRouterRunning": False}
        log = _model_router_launch_log()
        if log is not None:
            result["modelRouterLaunchLog"] = log
        return result
    running, pool = _model_router_health_check(port)
    result = {"modelRouterPort": port, "modelRouterRunning": running}
    if pool is not None:
        if "healthy_endpoints" in pool:
            result["modelRouterHealthyEndpoints"] = pool["healthy_endpoints"]
        if "unhealthy_endpoints" in pool:
            result["modelRouterUnhealthyEndpoints"] = pool["unhealthy_endpoints"]
    if not running:
        log = _model_router_launch_log()
        if log is not None:
            result["modelRouterLaunchLog"] = log
    return result


def _nemoclaw_onboard_trace() -> dict:
    """Read NemoClaw onboarding OTel trace artifacts (#5193).

    When ``NEMOCLAW_TRACE`` is set the harness writes OpenTelemetry-style spans
    for each onboarding phase (e.g. ``nemoclaw.onboard.phase.gateway``,
    ``nemoclaw.onboard.phase.inference``) including span status (OK/ERROR/UNSET),
    duration_ms, events, sanitised attributes, and a ``summary.slowest_spans``
    list.  ClawMetry surfaces the worst-case status, error phase names, and the
    slowest-span summary so a failed or slow onboarding step is diagnosable from
    the dashboard rather than silently invisible.

    Path resolution (first match wins):
    1. ``NEMOCLAW_TRACE_FILE`` env var.
    2. ``NEMOCLAW_TRACE_DIR/trace.json``.
    3. ``.e2e/traces/trace.json`` (harness default, relative to cwd).

    Handles both the flat harness shape ``{spans:[...], summary:{...}}`` and the
    standard OTel ``resource_spans`` export.  Returns ``{}`` when
    ``NEMOCLAW_TRACE`` is unset/disabled or no file is found.  Never raises.
    """
    import json as _json

    trace_env = os.environ.get("NEMOCLAW_TRACE", "")
    if not trace_env or trace_env.lower() in ("0", "false", "no"):
        return {}

    candidates = []
    tf = os.environ.get("NEMOCLAW_TRACE_FILE", "")
    if tf:
        candidates.append(tf)
    td = os.environ.get("NEMOCLAW_TRACE_DIR", "")
    if td:
        candidates.append(os.path.join(td, "trace.json"))
    candidates.append(os.path.join(".e2e", "traces", "trace.json"))

    data = None
    for path in candidates:
        try:
            with open(path, "r", encoding="utf-8", errors="replace") as fh:
                data = _json.load(fh)
            break
        except (OSError, ValueError):
            continue
        except Exception:
            continue

    if data is None or not isinstance(data, dict):
        return {}

    try:
        spans: list = []
        if "spans" in data:
            raw = data["spans"]
            if isinstance(raw, list):
                spans = raw
        elif "resource_spans" in data:
            for rs in data.get("resource_spans", []):
                for ss in (rs.get("scope_spans") or rs.get("scopeSpans") or []):
                    spans.extend(ss.get("spans", []))

        _STATUS_RANK = {"ERROR": 2, "UNSET": 1, "OK": 0}
        # OTel status codes: 0 = UNSET, 1 = OK, 2 = ERROR (the JSON export
        # writes ``{"code": N}``; some exporters write ``STATUS_CODE_OK``).
        _CODE_TO_STATUS = {0: "UNSET", 1: "OK", 2: "ERROR"}

        def _norm_status(raw) -> str:
            if isinstance(raw, dict):
                raw = raw.get("code", raw.get("status_code", "UNSET"))
            if isinstance(raw, bool):
                return "UNSET"
            if isinstance(raw, (int, float)):
                return _CODE_TO_STATUS.get(int(raw), "UNSET")
            text = str(raw or "UNSET").upper().strip()
            if text.startswith("STATUS_CODE_"):
                text = text[len("STATUS_CODE_"):]
            return text if text in _STATUS_RANK else "UNSET"

        worst_rank = -1
        worst_status = "UNSET"
        error_names: list = []

        for span in spans:
            if not isinstance(span, dict):
                continue
            status = _norm_status(span.get("status", "UNSET"))
            rank = _STATUS_RANK[status]
            if rank > worst_rank:
                worst_rank = rank
                worst_status = status
            if status == "ERROR":
                name = span.get("name") or span.get("spanName") or ""
                if name:
                    error_names.append(str(name))

        result: dict = {}
        if spans:
            result["nemoclawOnboardTraceStatus"] = worst_status
            result["nemoclawOnboardTraceSpanCount"] = len(spans)
        if error_names:
            result["nemoclawOnboardTraceErrors"] = error_names[:10]

        summary = data.get("summary")
        if isinstance(summary, dict):
            slow = summary.get("slowest_spans")
            if isinstance(slow, list) and slow:
                result["nemoclawOnboardSlowSpans"] = slow[:5]

        return result
    except Exception:
        return {}


def _parse_proxy_config_model_list(content: str) -> Optional[List[str]]:
    """Extract model names from a LiteLLM-style proxy-config YAML (#2960).

    Tries ``yaml.safe_load`` first (PyYAML, optional dep); falls back to a
    line-by-line scan for ``model_name:`` keys so no new hard dependency is
    needed.  Returns ``None`` on parse failure so callers can omit the field.
    Never raises.
    """
    try:
        import yaml as _yaml  # type: ignore[import]
        data = _yaml.safe_load(content)
        items = data.get("model_list", []) if isinstance(data, dict) else []
        return [
            m["model_name"]
            for m in items
            if isinstance(m, dict) and "model_name" in m
        ]
    except ImportError:
        pass
    except Exception:
        return None

    # Fallback: line scan for ``model_name: <value>`` in a model_list block
    in_list = False
    names: List[str] = []
    for line in content.splitlines():
        stripped = line.strip()
        if stripped == "model_list:":
            in_list = True
            continue
        if in_list:
            if stripped.startswith("- model_name:"):
                _, _, name = stripped.partition(":")
                names.append(name.strip().strip("\"'"))
            elif stripped and not stripped.startswith("-") and not stripped.startswith(" "):
                in_list = False
    return names or None


def _model_router_proxy_config_models() -> dict:
    """Read the NeMoClaw model-router proxy-config model roster (#2960).

    The harness writes a proxy-config YAML during onboarding
    (test/onboard-model-router.test.ts). Checks ``<venv>/proxy-config.yaml``
    first; falls back to running ``model-router proxy-config --output <tmp>``
    if the binary is on PATH.

    Returns ``{"modelRouterProxyModels": ["name", ...]}`` or ``{}`` on any
    failure (file absent, binary missing, parse error).  Never raises.
    """
    import subprocess
    import shutil
    import tempfile

    venv = os.environ.get("NEMOCLAW_MODEL_ROUTER_VENV") or os.path.expanduser(
        os.path.join("~", ".nemoclaw", "model-router-venv"))

    # Fast path: static file written by harness onboarding
    static_path = os.path.join(venv, "proxy-config.yaml")
    content: Optional[str] = None
    if os.path.isfile(static_path):
        try:
            with open(static_path, encoding="utf-8") as fh:
                content = fh.read()
        except OSError:
            pass

    # Slow path: generate via model-router CLI
    if content is None:
        mr_bin_venv = os.path.join(venv, "bin", "model-router")
        mr_bin: Optional[str] = (
            mr_bin_venv if os.path.isfile(mr_bin_venv) else shutil.which("model-router")
        )
        if not mr_bin:
            return {}
        tmp_path: Optional[str] = None
        try:
            with tempfile.NamedTemporaryFile(suffix=".yaml", delete=False) as tmp:
                tmp_path = tmp.name
            subprocess.check_call(
                [mr_bin, "proxy-config", "--output", tmp_path],
                stderr=subprocess.DEVNULL,
                timeout=10,
            )
            with open(tmp_path, encoding="utf-8") as fh:
                content = fh.read()
        except Exception:
            return {}
        finally:
            if tmp_path:
                try:
                    os.unlink(tmp_path)
                except OSError:
                    pass

    models = _parse_proxy_config_model_list(content)
    return {"modelRouterProxyModels": models} if models is not None else {}


# NOTE (#2610, deferred): NemoClaw's skill-catalog version/provenance lives in
# ``skills/catalog-metadata.json`` (min/tested NemoClaw version, content shas),
# but that file is a SOURCE-repo build artifact — it is not shipped in the npm
# ``files`` list and no install/Docker step copies it to any host-readable path,
# and the NemoClaw skills bundle lives inside the sandbox container, not the host
# ``~/.openclaw`` ClawMetry reads. So there is no reliable on-disk location to
# read it from today. Deferred rather than ship a dead read; revisit if NemoClaw
# starts exporting the catalog to the host (e.g. ~/.nemoclaw/skills/).


def _scan_openclaw_selection_runtime() -> tuple[bool, bool, bool]:
    """Scan the pinned OpenClaw ``selection-*.js`` once and report whether
    (a) the NemoClaw compact-catalog patch marker is present,
    (b) the three base native tool-search symbols are present, and
    (c) the two enforcement symbols (visibleAllowedToolNames /
        replayAllowedToolNames) that distinguish a full-native build from a
        basic-native one are present (#2877).

    Returns ``(nemoclaw_patched, native_base, native_enforcement)``. Never raises.
    """
    nemoclaw_marker = b"/* nemoclaw compact tool catalog (#2600) */"
    # Mirror scripts/patch-openclaw-tool-catalog.js NATIVE_TOOL_SEARCH_PATTERNS
    # entries 1-3: catalog infrastructure symbols (#2732).
    native_base_markers = (
        b"applyToolSearchCatalog",
        b"buildToolSearchRunPlan",
        b"uncompactedEffectiveTools",
    )
    # Entries 4-5: enforcement signals added by the harness (#2877). Both must
    # be present to confirm the build actively enforces visible/replay allow-lists.
    native_enforcement_markers = (
        b"visibleAllowedToolNames",
        b"replayAllowedToolNames",
    )
    patched = False
    native_base = False
    native_enforcement = False
    try:
        home = os.environ.get("OPENCLAW_HOME") or os.path.expanduser("~/.openclaw")
        dist_dirs = [
            os.path.join(home, "node_modules", "openclaw", "dist"),
            "/usr/local/lib/node_modules/openclaw/dist",
        ]
        for dist in dist_dirs:
            if not os.path.isdir(dist):
                continue
            try:
                names = os.listdir(dist)
            except OSError:
                continue
            for n in names:
                if not (n.startswith("selection-") and n.endswith(".js")):
                    continue
                fp = os.path.join(dist, n)
                try:
                    with open(fp, "rb") as fh:
                        # Patch marker + native symbols sit early in the
                        # rewritten module; cap the read.
                        blob = fh.read(2_000_000)
                except OSError:
                    continue
                if not patched and nemoclaw_marker in blob:
                    patched = True
                if not native_base and all(m in blob for m in native_base_markers):
                    native_base = True
                if native_base and not native_enforcement and all(
                    m in blob for m in native_enforcement_markers
                ):
                    native_enforcement = True
                if patched and native_base and native_enforcement:
                    break
            if patched and native_base and native_enforcement:
                break
    except Exception:
        return patched, native_base, native_enforcement
    return patched, native_base, native_enforcement


def _nemoclaw_tool_catalog_state(
    tools_present: Optional[bool] = None,
) -> Optional[bool]:
    """Whether the NemoClaw compact tool-catalog wrapper is active for this
    runtime (#2683).

    The harness patch (scripts/patch-openclaw-tool-catalog.js) injects
    ``NEMOCLAW_TOOL_CATALOG !== "0"`` into every agent turn, after rewriting
    the pinned OpenClaw ``selection-*.js`` and stamping the marker
    ``/* nemoclaw compact tool catalog (#2600) */``. We surface a defensive
    session-level boolean so the dashboard can tell a guardrail-wrapped
    session from one where the catalog was disabled.

    Returns ``True``/``False`` ONLY when there is positive NemoClaw signal
    (the patch marker is present in the openclaw dist, or the env var is
    explicitly set); returns ``None`` on plain OpenClaw so we never assert a
    catalog state that doesn't exist. Never raises.

    Args:
        tools_present: When the caller knows whether the turn/session had any
            registered tools, pass ``True`` or ``False`` to mirror the
            tools-count half of the harness gate
            (``effectiveTools.length > 0 || clientTools?.length > 0``,
            #3432).  ``None`` (default) skips the tools-present check and
            falls back to the env-var-only gate — safe when the caller cannot
            determine tool count.
    """
    env = os.environ.get("NEMOCLAW_TOOL_CATALOG")
    patched, _native, _native_enf = _scan_openclaw_selection_runtime()
    if not patched and env is None:
        # No NemoClaw signal at all -> don't claim a catalog state.
        return None
    # Mirror the harness gate exactly: disabled when env var is "0" OR when
    # the caller knows no tools were registered for this turn/session (#3432).
    if env == "0":
        return False
    if tools_present is False:
        return False
    return True


def _openclaw_tool_catalog_kind() -> Optional[str]:
    """Provenance of the active OpenClaw tool-catalog mechanism, if any (#2732, #2877).

    Returns:
        ``"nemoclaw"`` when the NemoClaw compact-catalog patch is applied
        (matches ``_nemoclaw_tool_catalog_state() is True``).
        ``"native-full"`` when all five NATIVE_TOOL_SEARCH_PATTERNS are present:
        the three base infrastructure symbols plus ``visibleAllowedToolNames`` /
        ``replayAllowedToolNames`` (enforcement-active build).
        ``"native"`` when only the three base infrastructure symbols are present
        (catalog infrastructure present, enforcement inactive).
        ``None`` when neither signal is present.

    The NemoClaw patch wins over native detection: when both fire (e.g. a
    forward-port window) the patched wrapper is what's actually intercepting
    catalog calls. Never raises.
    """
    patched, native, native_enforcement = _scan_openclaw_selection_runtime()
    if patched:
        return "nemoclaw"
    if native_enforcement:
        return "native-full"
    if native:
        return "native"
    return None


def _gateway_plugin_health() -> dict:
    """Per-plugin health state from the OpenClaw gateway status RPC (#3200).

    As of harness 2026.6.9 (PR #93395) the gateway ``gateway.status`` response
    includes a ``plugins`` list where each entry carries the plugin ``name``,
    its ``state`` (``"loaded"`` / ``"errored"`` / ``"disabled"``), and an
    optional ``type`` field (``"channel"`` / ``"provider"``).

    As of harness 2026.7.21 (#3883), the shared plugin-SDK monitor introduces a
    ``phase`` field per plugin entry (``"admission"``, ``"claim-identity"``,
    ``"adoption-handoff"``, ``"pruning"``, ``"polling"``, ``"shutdown"``) so a
    plugin stuck mid-admission is distinguishable from a healthy ``"loaded"``
    one.  Per-step detail flags (``admission``, ``claim_identity``,
    ``adoption_handoff``, ``pruning``, ``polling``, ``shutdown``) are forwarded
    when present (#4058).

    Returns a dict with keys when any plugin data is present:
    - ``"gatewayPluginHealth"`` — the raw list of plugin entries.
    - ``"gatewayPluginHealthSummary"`` — a ``{state: count}`` tally.
    - ``"gatewayPluginPhaseSummary"`` — a ``{phase: count}`` tally (only present
      when at least one entry carries a ``phase`` field).

    Returns ``{}`` when the gateway RPC returns nothing, the response contains
    no ``plugins`` key, or the list is empty. Never raises.
    """
    try:
        d = _d()
        rpc = getattr(d, "_gw_ws_rpc", None)
        if rpc is None:
            return {}
        payload = rpc("gateway.status")
        if not isinstance(payload, dict):
            return {}
        raw_plugins = payload.get("plugins")
        if not isinstance(raw_plugins, list) or not raw_plugins:
            return {}
        plugins = []
        summary: dict = {}
        phase_summary: dict = {}
        for entry in raw_plugins:
            if not isinstance(entry, dict):
                continue
            name = entry.get("name") or entry.get("id") or ""
            state = str(entry.get("state") or "").lower()
            ptype = entry.get("type") or entry.get("kind") or None
            if not name or not state:
                continue
            plugin: dict = {"name": name, "state": state}
            if ptype:
                plugin["type"] = ptype
            # Lifecycle phase from the shared plugin-SDK monitor (#3883)
            phase = entry.get("phase") or None
            if phase:
                plugin["phase"] = str(phase).lower()
                phase_summary[plugin["phase"]] = phase_summary.get(plugin["phase"], 0) + 1
            # Per-step lifecycle detail flags (forwarded when present)
            for detail_key in ("admission", "claim_identity", "adoption_handoff", "pruning", "polling", "shutdown"):
                val = entry.get(detail_key)
                if val is not None:
                    plugin[detail_key] = val
            plugins.append(plugin)
            summary[state] = summary.get(state, 0) + 1
        if not plugins:
            return {}
        result: dict = {"gatewayPluginHealth": plugins, "gatewayPluginHealthSummary": summary}
        if phase_summary:
            result["gatewayPluginPhaseSummary"] = phase_summary
        return result
    except Exception:
        return {}


def _gateway_host_status() -> dict:
    """Host/system fields from the OpenClaw gateway.status RPC (#3551).

    As of harness CHANGELOG #100478 the gateway.status response includes
    host name, network address, OS, runtime, uptime, CPU, memory, and disk
    details alongside the existing ``plugins`` list.

    Returns a dict with whichever fields are present:
    - ``"gatewayHostName"``            — machine hostname
    - ``"gatewayNetworkAddress"``      — primary network address / IP
    - ``"gatewayHostOS"``              — OS name or platform string
    - ``"gatewayHostRuntime"``         — runtime identifier (e.g. Node version)
    - ``"gatewayHostUptime"``          — uptime in seconds
    - ``"gatewayHostCPU"``             — CPU usage value or dict
    - ``"gatewayHostMemory"``          — memory info (bytes or dict)
    - ``"gatewayHostDisk"``            — disk info (bytes or dict)
    - ``"gatewaySupervisorMode"``      — supervisor mode (e.g. ``"external"``)
    - ``"gatewaySupervisorModeVersion"`` — restart-handoff contract version

    Returns ``{}`` when the RPC is unavailable or the response carries no
    host fields. Never raises.
    """
    try:
        d = _d()
        rpc = getattr(d, "_gw_ws_rpc", None)
        if rpc is None:
            return {}
        payload = rpc("gateway.status")
        if not isinstance(payload, dict):
            return {}
        result: dict = {}
        host_name = (
            payload.get("hostName")
            or payload.get("host_name")
            or payload.get("hostname")
            or payload.get("host")
        )
        if host_name:
            result["gatewayHostName"] = str(host_name)
        address = (
            payload.get("networkAddress")
            or payload.get("network_address")
            or payload.get("address")
            or payload.get("ip")
        )
        if address:
            result["gatewayNetworkAddress"] = str(address)
        os_val = payload.get("os") or payload.get("platform")
        if os_val:
            result["gatewayHostOS"] = str(os_val)
        runtime = (
            payload.get("runtime")
            or payload.get("nodeVersion")
            or payload.get("node_version")
        )
        if runtime:
            result["gatewayHostRuntime"] = str(runtime)
        uptime = (
            payload.get("uptime")
            or payload.get("uptimeSeconds")
            or payload.get("uptime_seconds")
        )
        if uptime is not None:
            result["gatewayHostUptime"] = uptime
        cpu = payload.get("cpu") or payload.get("cpuUsage") or payload.get("cpu_usage")
        if cpu is not None:
            result["gatewayHostCPU"] = cpu
        memory = (
            payload.get("memory")
            or payload.get("memoryUsage")
            or payload.get("memory_usage")
        )
        if memory is not None:
            result["gatewayHostMemory"] = memory
        disk = (
            payload.get("disk")
            or payload.get("diskUsage")
            or payload.get("disk_usage")
        )
        if disk is not None:
            result["gatewayHostDisk"] = disk
        supervisor_mode = (
            payload.get("supervisorMode")
            or payload.get("supervisor_mode")
        )
        if supervisor_mode:
            result["gatewaySupervisorMode"] = str(supervisor_mode)
        supervisor_mode_version = (
            payload.get("supervisorModeVersion")
            or payload.get("supervisor_mode_version")
        )
        if supervisor_mode_version:
            result["gatewaySupervisorModeVersion"] = str(supervisor_mode_version)
        return result
    except Exception:
        return {}


def _gateway_supervisor_mode_env() -> dict:
    """Read OpenClaw external-supervisor mode from the local environment (#4023).

    ``OPENCLAW_SUPERVISOR_MODE`` is set by the operator when an external lifecycle
    owner (e.g. OCM) supervises the gateway.  When the gateway is down during a
    supervised restart handoff, ``_gateway_host_status()`` is not called (it
    requires a live RPC connection), so the supervisor context is invisible.

    This helper reads the env var unconditionally as a baseline fallback.  When
    the gateway IS live, ``_gateway_host_status()`` overwrites these keys with
    the authoritative RPC value.

    Returns ``{"gatewaySupervisorMode": ...}`` (and optionally
    ``"gatewaySupervisorModeVersion"``) when the env var is set, ``{}`` otherwise.
    Never raises.
    """
    try:
        mode = os.environ.get("OPENCLAW_SUPERVISOR_MODE")
        if not mode:
            return {}
        result: dict = {"gatewaySupervisorMode": str(mode)}
        version = os.environ.get("OPENCLAW_SUPERVISOR_MODE_VERSION")
        if version:
            result["gatewaySupervisorModeVersion"] = str(version)
        return result
    except Exception:
        return {}


def _gateway_is_in_restart_handoff(supervisor_mode: str, gateway_live: bool) -> bool:
    """True when the gateway is briefly offline during an externally-supervised
    restart-handoff (#4302).

    An external lifecycle owner (e.g. OCM) manages gateway restarts when
    ``OPENCLAW_SUPERVISOR_MODE=external``.  A ``False`` result from
    ``_gateway_live()`` is then an expected transient — the supervisor will
    bring the gateway back.  Callers surface "restarting (supervised)" rather
    than "gateway offline" in the UI.

    Never raises.
    """
    try:
        return supervisor_mode == "external" and not gateway_live
    except Exception:
        return False


def _gateway_presence_roster() -> dict:
    """Who's-online presence roster from the OpenClaw gateway.status RPC (#3884).

    As of the Control UI who's-online roster release, the gateway.status response
    includes a list of currently-connected users under a ``connectedUsers`` (or
    ``onlineUsers`` / ``presence``) key.  Each entry carries at minimum an
    ``email`` field; ``displayName`` and ``avatar`` (or ``avatarUrl``) are
    included when the user's profile is populated.

    Returns a dict with:
    - ``"gatewayPresenceRoster"`` — list of normalized user dicts, each with
      ``email`` (str), and optionally ``displayName`` (str) and ``avatar`` (str).
    - ``"gatewayPresenceCount"`` — number of online users.

    Returns ``{}`` when the RPC is unavailable, carries no user list, or the
    list is empty. Never raises.
    """
    try:
        d = _d()
        rpc = getattr(d, "_gw_ws_rpc", None)
        if rpc is None:
            return {}
        payload = rpc("gateway.status")
        if not isinstance(payload, dict):
            return {}
        raw_users = (
            payload.get("connectedUsers")
            or payload.get("connected_users")
            or payload.get("onlineUsers")
            or payload.get("online_users")
            or payload.get("presence")
        )
        if not isinstance(raw_users, list) or not raw_users:
            return {}
        roster = []
        for entry in raw_users:
            if not isinstance(entry, dict):
                continue
            email = (
                entry.get("email")
                or entry.get("emailAddress")
                or entry.get("email_address")
            )
            if not email:
                continue
            user: dict = {"email": str(email)}
            display_name = (
                entry.get("displayName")
                or entry.get("display_name")
                or entry.get("name")
            )
            if display_name:
                user["displayName"] = str(display_name)
            avatar = (
                entry.get("avatar")
                or entry.get("avatarUrl")
                or entry.get("avatar_url")
                or entry.get("photoUrl")
                or entry.get("photo_url")
            )
            if avatar:
                user["avatar"] = str(avatar)
            roster.append(user)
        if not roster:
            return {}
        return {"gatewayPresenceRoster": roster, "gatewayPresenceCount": len(roster)}
    except Exception:
        return {}


def _gateway_mcp_app_widgets() -> dict:
    """Pinned MCP app dashboard widgets from the OpenClaw gateway.status RPC (#3882).

    OpenClaw's Dashboard MCP apps feature (CHANGELOG.md 'Unreleased: Dashboard MCP
    apps') lets MCP app views be pinned as persistent dashboard widgets from an
    originating session.  Each widget has a view-lease that renews periodically and
    tool interactivity gated behind revision-bound grants.

    When the gateway exposes widget state the response carries the list under one of
    the candidate keys below.  Each entry is normalised to:
    - ``"widgetId"``               — stable widget identifier
    - ``"sessionId"``              — originating session that pinned the widget
    - ``"type"``                   — widget type / MCP app identifier (when present)
    - ``"leaseState"``             — ``"active"``, ``"expired"``, or ``"pending"``
    - ``"grantRevision"``          — revision token for the tool-interactivity grant
    - ``"toolInteractivityEnabled"`` — bool; whether tool calls are currently allowed

    Returns a dict with:
    - ``"gatewayMcpAppWidgets"``    — list of normalised widget dicts
    - ``"gatewayMcpAppWidgetCount"`` — total widget count
    - ``"gatewayMcpAppWidgetSummary"`` — ``{leaseState: count}`` tally

    Returns ``{}`` when the RPC is unavailable, carries no widget list, or the list
    is empty.  Never raises.
    """
    try:
        d = _d()
        rpc = getattr(d, "_gw_ws_rpc", None)
        if rpc is None:
            return {}
        payload = rpc("gateway.status")
        if not isinstance(payload, dict):
            return {}
        raw_widgets = (
            payload.get("mcp_app_widgets")
            or payload.get("mcpAppWidgets")
            or payload.get("dashboard_widgets")
            or payload.get("dashboardWidgets")
            or payload.get("pinned_widgets")
            or payload.get("pinnedWidgets")
        )
        if not isinstance(raw_widgets, list) or not raw_widgets:
            return {}
        widgets = []
        lease_summary: dict = {}
        for entry in raw_widgets:
            if not isinstance(entry, dict):
                continue
            widget_id = (
                entry.get("widgetId")
                or entry.get("widget_id")
                or entry.get("id")
            )
            if not widget_id:
                continue
            widget: dict = {"widgetId": str(widget_id)}
            session_id = entry.get("sessionId") or entry.get("session_id")
            if session_id:
                widget["sessionId"] = str(session_id)
            widget_type = entry.get("type") or entry.get("appId") or entry.get("app_id")
            if widget_type:
                widget["type"] = str(widget_type)
            lease_state = str(
                entry.get("leaseState")
                or entry.get("lease_state")
                or entry.get("lease")
                or ""
            ).lower() or None
            if lease_state:
                widget["leaseState"] = lease_state
                lease_summary[lease_state] = lease_summary.get(lease_state, 0) + 1
            grant_rev = entry.get("grantRevision") or entry.get("grant_revision")
            if grant_rev is not None:
                widget["grantRevision"] = grant_rev
            tool_ok = entry.get("toolInteractivityEnabled")
            if tool_ok is None:
                tool_ok = entry.get("tool_interactivity_enabled")
            if tool_ok is not None:
                widget["toolInteractivityEnabled"] = bool(tool_ok)
            widgets.append(widget)
        if not widgets:
            return {}
        result: dict = {
            "gatewayMcpAppWidgets": widgets,
            "gatewayMcpAppWidgetCount": len(widgets),
        }
        if lease_summary:
            result["gatewayMcpAppWidgetSummary"] = lease_summary
        return result
    except Exception:
        return {}


def _gateway_trusted_proxy_devices() -> dict:
    """Trusted-proxy device pairing state from the OpenClaw gateway (#3885).

    As of OpenClaw CHANGELOG (Unreleased: 'Trusted-proxy browser pairing'),
    devices (Control UI, WebChat) can be auto-approved from allowlisted
    trusted-proxy identities with non-admin scope caps, distinct from
    manually-approved existing-device upgrades.

    Tries two sources in order:
    1. ``gateway.status`` payload -- looks for a ``devices``,
       ``trustedDevices``, ``pairedDevices``, or ``trustedProxies`` list.
    2. A dedicated ``gateway.devices`` RPC as a fallback (anticipated in a
       future harness release alongside the status key).

    Returns a dict with keys when paired devices are present:
    - ``"gatewayTrustedProxyDevices"`` -- list of dicts with ``id``,
      ``autoApproved``, and optional ``label``, ``scopeCap``, ``approvedAt``.
    - ``"gatewayTrustedProxyDeviceSummary"`` -- ``{auto: N, manual: N}`` tally.

    Returns ``{}`` when the RPC is unavailable, returns no device data, or
    the harness hasn't shipped the pairing surface yet. Never raises.
    """
    try:
        d = _d()
        rpc = getattr(d, "_gw_ws_rpc", None)
        if rpc is None:
            return {}

        raw_devices = None
        # Primary: gateway.status (avoids an extra round-trip)
        payload = rpc("gateway.status")
        if isinstance(payload, dict):
            raw_devices = (
                payload.get("devices")
                or payload.get("trustedDevices")
                or payload.get("pairedDevices")
                or payload.get("trustedProxies")
                or payload.get("proxyDevices")
            )
        # Fallback: dedicated gateway.devices RPC (future harness release)
        if not raw_devices:
            devices_payload = rpc("gateway.devices")
            if isinstance(devices_payload, list):
                raw_devices = devices_payload
            elif isinstance(devices_payload, dict):
                raw_devices = (
                    devices_payload.get("devices")
                    or devices_payload.get("items")
                    or devices_payload.get("trustedDevices")
                )

        if not isinstance(raw_devices, list) or not raw_devices:
            return {}

        devices = []
        summary: dict = {"auto": 0, "manual": 0}
        for entry in raw_devices:
            if not isinstance(entry, dict):
                continue
            device_id = str(
                entry.get("id")
                or entry.get("deviceId")
                or entry.get("device_id")
                or ""
            )
            if not device_id:
                continue
            auto_approved = bool(
                entry.get("autoApproved")
                or entry.get("auto_approved")
                or entry.get("trustedProxy")
                or entry.get("trusted_proxy")
            )
            device: dict = {"id": device_id, "autoApproved": auto_approved}
            label = str(
                entry.get("label")
                or entry.get("name")
                or entry.get("displayName")
                or ""
            )
            if label:
                device["label"] = label
            scope_cap = entry.get("scopeCap") or entry.get("scope_cap") or entry.get("scopes")
            if scope_cap is not None:
                device["scopeCap"] = scope_cap
            approved_at = (
                entry.get("approvedAt")
                or entry.get("approved_at")
                or entry.get("createdAt")
                or entry.get("created_at")
            )
            if approved_at is not None:
                device["approvedAt"] = approved_at
            devices.append(device)
            if auto_approved:
                summary["auto"] += 1
            else:
                summary["manual"] += 1

        if not devices:
            return {}
        return {
            "gatewayTrustedProxyDevices": devices,
            "gatewayTrustedProxyDeviceSummary": summary,
        }
    except Exception:
        return {}


def _workshop_approval_config() -> dict:
    """Read Skill Workshop approval-policy from openclaw.json (#3992).

    Surfaces ``skills.workshop.approvalPolicy`` in the adapter's detect()
    metadata so cloud-synced fleet views can show whether agent-initiated
    skill apply/reject/quarantine actions are gated by human approval.

    Returns ``{"workshopApprovalPolicy": <value>}`` when the key is present,
    ``{}`` otherwise. Never raises.
    """
    try:
        import json as _json
        home = os.environ.get("OPENCLAW_HOME") or os.path.expanduser("~/.openclaw")
        cfg_path = os.path.join(home, "openclaw.json")
        if not os.path.isfile(cfg_path):
            alt = os.path.expanduser("~/.clawdbot/openclaw.json")
            if os.path.isfile(alt):
                cfg_path = alt
            else:
                return {}
        with open(cfg_path) as fh:
            cfg = _json.load(fh)
        if not isinstance(cfg, dict):
            return {}
        workshop = (cfg.get("skills") or {}).get("workshop")
        if not isinstance(workshop, dict):
            return {}
        policy = workshop.get("approvalPolicy")
        if policy is None:
            return {}
        return {"workshopApprovalPolicy": str(policy)}
    except Exception:
        return {}


class OpenClawAdapter(AgentAdapter):
    name = "openclaw"
    display_name = "OpenClaw"

    def detect(self) -> DetectResult:
        try:
            d = _d()
            workspace = getattr(d, "WORKSPACE", None) or ""
            sessions_dir = getattr(d, "SESSIONS_DIR", None) or ""
            gateway_url = getattr(d, "GATEWAY_URL", None) or ""
            sessions = []
            try:
                sessions = d._get_sessions() or []
            except Exception as exc:
                logger.debug(f"OpenClaw _get_sessions() failed in detect: {exc}")

            default_home = os.path.expanduser("~/.openclaw")
            running = _gateway_live()
            # Require a GENUINE signal: real sessions, or an actual install
            # artifact, or a live gateway. The bare ~/.openclaw (or its
            # workspace dir) is NOT a signal — ClawMetry creates it, which
            # false-positived OpenClaw on uninstalled machines.
            detected = bool(sessions) or running or _real_install(sessions_dir)
            meta = {
                "gatewayUrl": gateway_url,
                "sessionsDir": sessions_dir,
            }
            # NemoClaw install-provenance signal (#2608). Returns {} on plain
            # OpenClaw, so meta is unchanged there. (#2610 skill-catalog deferred
            # — see note above: no host-readable on-disk location.)
            meta.update(_model_router_fingerprint())
            # Currency verdict (#3652): is the installed router up-to-date?
            # Distinct from liveness (crashed vs alive); this catches the case
            # where NemoClaw upgraded but the router wasn't reinstalled.
            meta.update(_model_router_currency())
            meta.update(_model_router_proxy_config_models())
            # Runtime liveness (#2795). The fingerprint above only proves the
            # router was INSTALLED; probe /health so a crashed router is no
            # longer indistinguishable from a healthy one. Only meaningful when
            # a model-router install is actually present.
            if "modelRouterFingerprint" in meta:
                meta.update(_model_router_live())
            _tc_enabled = _nemoclaw_tool_catalog_state()
            if _tc_enabled is not None:
                meta["nemoclawToolCatalogEnabled"] = _tc_enabled
            # Provenance — distinguish NemoClaw patch from native OpenClaw
            # tool-search builds where the patch is a no-op (#2732). Stamped
            # in addition to the back-compat boolean above.
            _tc_kind = _openclaw_tool_catalog_kind()
            if _tc_kind is not None:
                meta["openclawToolCatalogKind"] = _tc_kind
            # Per-sandbox inference config (#2796): providerKey/primaryModelRef/
            # inferenceBaseUrl/inferenceApi/inferenceCompat from sandboxes.json.
            _sb_configs = _sandbox_inference_configs()
            if _sb_configs:
                meta["sandboxInferenceConfigs"] = _sb_configs
            # DNS-backed HTTPS fail-closed enforcement (#3471): aggregate denial
            # events across all known sandboxes.  Only written when >0 denials
            # so absence of the key on plain OpenClaw installs is unambiguous.
            _dns_denied_total = sum(
                c.get("egressDeniedCount", 0) for c in _sb_configs
            ) if _sb_configs else 0
            if _dns_denied_total:
                meta["dnsFailClosedCount"] = _dns_denied_total
                meta["networkEgressDenied"] = True
            # Agents manifest (#3185): agent roster + per-agent sandbox/config
            # from ~/.nemoclaw/agents.yaml (written by harness onboarding,
            # commit 01e5525).
            meta.update(_nemoclaw_agents_manifest())
            # External-supervisor mode env-var fallback (#4023): surface
            # OPENCLAW_SUPERVISOR_MODE even when the gateway is down (e.g. during
            # a supervised restart handoff). _gateway_host_status() below will
            # overwrite with the live RPC value when the gateway is up.
            meta.update(_gateway_supervisor_mode_env())
            # During an externally-supervised restart-handoff the gateway is
            # briefly down; flag this so callers show "restarting (supervised)"
            # rather than "gateway offline" (#4302).
            if _gateway_is_in_restart_handoff(
                meta.get("gatewaySupervisorMode", ""), running
            ):
                meta["gatewayInRestartHandoff"] = True
            # Gateway host/system status (#3551, #5431): host name, OS, runtime,
            # uptime, CPU, memory, disk from the gateway.status RPC. Called
            # unconditionally so remote/fleet gateways (where _gateway_live()
            # checks localhost and returns False) still surface host fields when
            # the WebSocket RPC connection is alive. The function self-guards:
            # returns {} when _gw_ws_rpc is None or the call throws.
            meta.update(_gateway_host_status())
            # Gateway plugin health (#3200): per-plugin state (loaded/errored/
            # disabled) added to gateway.status in harness 2026.6.9 (#93395).
            # Only meaningful — and safe to query — when the gateway is live.
            if running:
                meta.update(_gateway_plugin_health())
                # Who's-online presence roster (#3884): connected users from the
                # Control UI facepile, via the same gateway.status RPC.
                meta.update(_gateway_presence_roster())
                # Pinned MCP app dashboard widgets (#3882): widget list, lease
                # state, and revision-bound tool-grant status from the same RPC.
                # Returns {} on installs predating the Dashboard MCP apps release.
                meta.update(_gateway_mcp_app_widgets())
                # Trusted-proxy device pairing (#3885): paired/approved devices,
                # scope caps, and auto- vs manual-approval state.
                meta.update(_gateway_trusted_proxy_devices())
            # Docker runtime health (#3390): the NemoClaw harness treats Docker
            # daemon liveness as a distinct signal from gateway liveness. Only
            # written when docker CLI is present so non-Docker environments are
            # unaffected.
            _docker_down = _is_docker_runtime_down()
            if _docker_down is not None:
                meta["dockerRuntimeDown"] = _docker_down
            # Doctor findings (#3468): structured diagnostic findings from
            # `openclaw doctor --json` (harness 2026.7.1). Categories:
            # auth-profile, workspace, device-pairing, channel-plugin,
            # memory-provider, systemd-exhaustion, Windows LAN-firewall.
            _doctor = _openclaw_doctor_findings()
            if _doctor:
                meta["doctorFindings"] = _doctor
            # ClawRouter bundled provider plugin (#3524, OpenClaw 2026.7.1
            # #99658). Credential-scoped dynamic model discovery, multi-transport
            # routing, and managed budget/quota reporting across OpenClaw usage
            # surfaces. Returns {} on pre-2026.7.1 installs.
            _cr = _clawrouter_detect()
            if _cr:
                meta.update(_cr)
            # Gateway log location + rotation state (#3836): surface the
            # rotating log directory, archive count, and current file size so
            # the dashboard can show log presence for plain OpenClaw installs.
            # Runs unconditionally — log files exist even when the gateway is
            # not currently live. Returns {} gracefully when absent.
            _gw_log = _gateway_log_meta()
            if _gw_log:
                meta.update(_gw_log)
            _gw_events, _gw_available = _gateway_log_events_probe()
            if _gw_events:
                meta["gatewayLogEvents"] = _gw_events
            meta["gatewayLogSourceAvailable"] = _gw_available
            # Skill Workshop approval-policy (#3992): surfaces
            # skills.workshop.approvalPolicy from openclaw.json so cloud-synced
            # fleet views know whether autonomous skill actions are gated by
            # human approval.  Returns {} on installs without the key.
            meta.update(_workshop_approval_config())
            # NemoClaw onboarding OTel trace artifacts (#5193): surfaces
            # nemoclawOnboardTraceStatus/SpanCount/Errors/SlowSpans when
            # NEMOCLAW_TRACE is set and the harness wrote a trace file.
            # Returns {} when disabled or file absent — no guard needed.
            _ot = _nemoclaw_onboard_trace()
            if _ot:
                meta.update(_ot)
            return DetectResult(
                name=self.name,
                display_name=self.display_name,
                detected=detected,
                running=running,
                workspace=workspace or default_home,
                session_count=len(sessions),
                capabilities=[c.value for c in self.capabilities()],
                meta=meta,
            )
        except Exception as exc:
            logger.warning(f"OpenClaw detect() raised: {exc}")
            return DetectResult(
                name=self.name,
                display_name=self.display_name,
                detected=False,
                meta={"error": str(exc)},
            )

    def list_sessions(self, limit: int = 100) -> List[Session]:
        try:
            raw = _d()._get_sessions() or []
        except Exception as exc:
            logger.warning(f"OpenClaw list_sessions() failed: {exc}")
            return []
        # Catalog provenance (#2732): "nemoclaw" or "native" when either
        # signal is present, so native-tool-search OpenClaw builds are no
        # longer indistinguishable from "no catalog at all".
        _tc_kind = _openclaw_tool_catalog_kind()
        out: List[Session] = []
        for s in raw[:limit]:
            updated_ms = s.get("updatedAt") or 0
            started_at = (updated_ms / 1000.0) if updated_ms else 0.0
            _sk = (s.get("kind") or "").lower()
            extra = {
                "kind": s.get("kind") or "direct",
                "contextTokens": s.get("contextTokens"),
                "agentId": s.get("agent") or "main",
            }
            # Runtime-level NemoClaw tool-catalog state (#2683 / #3432): mirror
            # the full harness gate — env var AND tools-present. Derive
            # tools_present from whichever tool-count alias the session record
            # carries; fall back to None (unknown) when absent so existing
            # gateway records that lack the field keep today's behaviour.
            _raw_tc = (
                s.get("toolCallCount")
                or s.get("totalToolCalls")
                or s.get("toolCount")
            )
            _tools_present = bool(_raw_tc) if _raw_tc is not None else None
            _tc_enabled = _nemoclaw_tool_catalog_state(tools_present=_tools_present)
            if _tc_enabled is not None:
                extra["nemoclawToolCatalogEnabled"] = _tc_enabled
            if _tc_kind is not None:
                extra["openclawToolCatalogKind"] = _tc_kind
            # Fast-mode state (#3322): PR #85104 added fastMode to session records.
            _fm = s.get("fastMode") if s.get("fastMode") is not None else s.get("isFastMode")
            if _fm is not None:
                extra["fastMode"] = _fm if isinstance(_fm, str) else bool(_fm)
            # Fast-mode fallback/cutoff metadata (#3341): PR #85104 also emits
            # cutoff state, reason, transition count, delivery mode, and fallback
            # model for sessions where fast-mode reverts to normal mode.
            _fmc = s.get("fastModeCutoff")
            if _fmc is not None:
                extra["fastModeCutoff"] = bool(_fmc)
            _fmc_reason = s.get("fastModeCutoffReason") or s.get("cutoffReason")
            if _fmc_reason is not None:
                extra["fastModeCutoffReason"] = _fmc_reason
            _fmc_count = s.get("fastModeTransitionCount") or s.get("transitionCount")
            if _fmc_count is not None:
                try:
                    extra["fastModeTransitionCount"] = int(_fmc_count)
                except (TypeError, ValueError):
                    pass
            _fmc_mode = s.get("fastModeDeliveryMode") or s.get("deliveryMode")
            if _fmc_mode is not None:
                extra["fastModeDeliveryMode"] = _fmc_mode
            _fm_fallback = s.get("fallbackModel") or s.get("fastModeFallbackModel")
            if _fm_fallback is not None:
                extra["fallbackModel"] = _fm_fallback
            # Runtime-engine fallback dimension (#3649): CHANGELOG #98021 added
            # an atomic runtime (engine) selection alongside model and thinking;
            # capture it so engine switches (OpenClaw↔Codex) are distinguishable.
            _fb_runtime = (
                s.get("fallbackRuntime")
                or s.get("fallbackRuntimeEngine")
                or s.get("runtimeEngine")
            )
            if _fb_runtime is not None:
                extra["fallbackRuntime"] = _fb_runtime
            # Atomic runtime alias (#3672): CHANGELOG #98021 "GPT-5.6 Ultra
            # and runtime switching" added Sol/Terra/Luna as named runtime
            # variants switched atomically with model and thinking via /model
            # and fallback.  Capture the selected alias so cost/model
            # attribution can distinguish which variant served the session.
            _rt_alias = (
                s.get("runtimeAlias")
                or s.get("selectedRuntimeAlias")
                or s.get("modelRuntimeAlias")
            )
            if _rt_alias is not None:
                extra["runtimeAlias"] = _rt_alias
            # Thinking-mode selection (#3672): atomic alongside runtimeAlias;
            # surface as-is (bool or string) so the dashboard can show whether
            # extended thinking was active.  Use is-not-None guards so
            # thinkingMode=False (thinking disabled) is never silently dropped.
            _thinking_mode = s.get("thinkingMode")
            if _thinking_mode is None:
                _thinking_mode = s.get("isThinkingEnabled")
            if _thinking_mode is None:
                _thinking_mode = s.get("thinkingEnabled")
            if _thinking_mode is not None:
                extra["thinkingMode"] = (
                    _thinking_mode if isinstance(_thinking_mode, str) else bool(_thinking_mode)
                )
            # /think reasoning-level tier (#3324): PR #94067 stores the active
            # level (light/medium/deep) on session records; surface when present.
            _think_level = s.get("thinkLevel") or s.get("reasoningLevel")
            if _think_level is not None:
                extra["thinkLevel"] = _think_level
            # SDK transcript identity target (#3323): PR #95030 adds a target
            # identity field so consumers can identify which agent/session
            # context a transcript belongs to.
            _idt = s.get("target") or s.get("identityTarget")
            if _idt is not None:
                extra["identityTarget"] = _idt
            # External-harness attachment (#3470): `openclaw attach` resumes an
            # existing gateway session via an external harness (PR #96454).  The
            # gateway stamps kind='attached' and/or an externalHarness boolean.
            # Surface a typed flag so the frontend can distinguish these sessions.
            _ext = s.get("externalHarness") or (
                s.get("kind", "").lower() in ("attached", "external")
            )
            if _ext:
                extra["externalHarness"] = True
            # Cron delivery awareness (#3342): PR #93580 stamps a
            # cronDeliveryTarget marker on sessions that are delivery targets
            # of a cron job so they can be correlated with the originating
            # cron. Without this, cron-triggered sessions are indistinguishable
            # from direct sessions in the dashboard.
            _cdt = s.get("cronDeliveryTarget")
            if _cdt is None:
                _cdt = s.get("isCronDeliveryTarget") or s.get("cronTarget")
            if _cdt is not None:
                extra["cronDeliveryTarget"] = bool(_cdt)
            # Cron delivery outcome (#3365): PR #93580 also stamps the delivery
            # result (success/failure), failure reason, and delivered-content
            # reference on the session so the next turn can see what happened.
            _cds = s.get("cronDeliverySuccess")
            if _cds is None:
                _cds = s.get("cronDelivered") or s.get("deliverySuccess")
            if _cds is not None:
                extra["cronDeliverySuccess"] = bool(_cds)
            _cdfr = (
                s.get("cronDeliveryFailureReason")
                or s.get("deliveryFailureReason")
                or s.get("cronFailureReason")
            )
            if _cdfr is not None:
                extra["cronDeliveryFailureReason"] = str(_cdfr)
            _cdcont = s.get("cronDeliveredContent") or s.get("deliveredContent")
            if _cdcont is not None:
                extra["cronDeliveredContent"] = str(_cdcont)
            # PTY relay state (#3839): PR #107335 ('macOS paired-node terminals')
            # and PR #107086 ('Control UI catalog terminals') stamp relay state,
            # resume command, viewer preference, and paired-node identity on
            # session records so the Control UI can open native terminal sessions.
            # All four reads silently no-op when the fields are absent.
            _pty = s.get("ptyRelayState") or s.get("ptyRelay")
            if _pty is not None:
                extra["ptyRelayState"] = str(_pty)
            _rc = s.get("resumeCommand") or s.get("resumeCmd")
            if _rc is not None:
                extra["resumeCommand"] = str(_rc)
            _vp = s.get("viewerPreference") or s.get("terminalPreference")
            if _vp is not None:
                extra["viewerPreference"] = str(_vp)
            _pn = (
                s.get("pairedNodeId")
                or s.get("pairNodeId")
                or s.get("pairedNode")
            )
            if _pn is not None:
                extra["pairedNodeId"] = str(_pn)
            # On-exit cron trigger kind (#3526): OpenClaw 2026.7.1 (#92037)
            # stamps the schedule kind that triggered this session delivery
            # ("on-exit", "every", "interval", "cron", …) so callers can
            # distinguish exit-triggered runs from ordinary scheduled ones.
            _csk = s.get("cronScheduleKind") or s.get("cronTriggerKind")
            if _csk is not None:
                extra["cronScheduleKind"] = str(_csk)
            # Detached-run marker (#3526): OpenClaw 2026.7.1 (#98755) stamps
            # cronDetachedRun on sessions that were spawned as a detached
            # run (independent of the triggering session).
            _cdr = s.get("cronDetachedRun")
            if _cdr is None:
                _cdr = s.get("cronDetached")
            if _cdr is not None:
                extra["cronDetachedRun"] = bool(_cdr)
            # Cron-configured agent-turn model (#3552): OpenClaw PR #95341
            # stamps the model selected (or defaulted) for the cron job that
            # triggered this session so usage can be attributed per scheduled
            # job.  Key name varies across harness builds; try all known forms.
            _cm = (
                s.get("cronModel")
                or s.get("cronAgentModel")
                or s.get("cronConfiguredModel")
            )
            if _cm is not None:
                extra["cronModel"] = str(_cm)
            # GLM/Zhipu overload classification (#3343): PR #93241 classifies
            # Zhipu GLM overload as a distinct overload state for failover;
            # surface the tag so session views can indicate failover routing.
            _ovl = s.get("overloadClassification") or s.get("glmOverloadState")
            if _ovl is not None:
                extra["overloadClassification"] = _ovl
            # Failover model reference (#3343): PR #93241 also emits the model
            # name used when the primary GLM endpoint is overloaded.
            _glm_fov = s.get("failoverModel") or s.get("failoverModelRef")
            if _glm_fov is not None:
                extra["failoverModel"] = _glm_fov
            # Zai synthesized-model baseUrl (#3343): PR #94461 falls back to
            # the manifest baseUrl for synthesized GLM-5 models -- a distinct
            # URL from inferenceBaseUrl in sandboxInferenceConfigs.
            _zai = s.get("zaiBaseUrl") or s.get("synthesizedModelBaseUrl") or s.get("glm5BaseUrl")
            if _zai is not None:
                extra["zaiBaseUrl"] = _zai
            # Per-conversation capability profile (#3469): PR #98536 adds
            # capabilityProfile / conversationCapability to session records
            # (OpenClaw harness 2026.7.1, "Safer scoped conversations").
            _cap_profile = (
                s.get("capabilityProfile")
                or s.get("conversationCapability")
            )
            if _cap_profile is not None:
                extra["capabilityProfile"] = _cap_profile
            # Per-agent utilityModel routing (#3538): OpenClaw 2026.7.1 lets
            # cheaper models generate session/topic/thread titles via a
            # per-agent utilityModel setting. Surface the model name and its
            # usage so routes/usage.py can attribute costs correctly.
            _um = (
                s.get("utilityModel")
                or s.get("titleModel")
                or s.get("sessionTitleModel")
            )
            if _um is not None:
                extra["utilityModel"] = _um
            _um_tokens = (
                s.get("utilityModelTokens")
                or s.get("utilityModelTotalTokens")
            )
            if _um_tokens is not None:
                try:
                    extra["utilityModelTokens"] = int(_um_tokens)
                except (TypeError, ValueError):
                    pass
            _um_in = s.get("utilityModelInputTokens")
            if _um_in is not None:
                try:
                    extra["utilityModelInputTokens"] = int(_um_in)
                except (TypeError, ValueError):
                    pass
            _um_out = s.get("utilityModelOutputTokens")
            if _um_out is not None:
                try:
                    extra["utilityModelOutputTokens"] = int(_um_out)
                except (TypeError, ValueError):
                    pass
            _um_cost = s.get("utilityModelCostUsd") or s.get("utilityModelCost")
            if _um_cost is not None:
                try:
                    extra["utilityModelCostUsd"] = float(_um_cost)
                except (TypeError, ValueError):
                    pass
            # Talk/Voice Call session fields (#3553): OpenClaw 'Control UI Talk
            # controls' (harness PR #97170/#97738) stamps transcription-provider,
            # transport, voice model, and VAD config on talk-kind sessions.
            # Extract with multi-alias fallbacks for resilience across harness
            # versions; guard on _sk so non-voice sessions are unaffected.
            if _sk in ("talk", "voice", "realtime", "voice_call", "talk_call"):
                _tp = (
                    s.get("transcriptionProvider")
                    or s.get("talkTranscriptionProvider")
                    or s.get("speechProvider")
                )
                if _tp is not None:
                    extra["transcriptionProvider"] = str(_tp)
                _tt = (
                    s.get("talkTransport")
                    or s.get("voiceTransport")
                    or s.get("transport")
                )
                if _tt is not None:
                    extra["talkTransport"] = str(_tt)
                _vm = (
                    s.get("voiceModel")
                    or s.get("talkVoiceModel")
                    or s.get("realtimeModel")
                    or s.get("talkModel")
                )
                if _vm is not None:
                    extra["voiceModel"] = str(_vm)
                _vad = (
                    s.get("vadMode")
                    or s.get("talkVadMode")
                    or s.get("vadTimingMode")
                )
                if _vad is not None:
                    extra["vadMode"] = str(_vad)
            # Session classification facts (#4591): harness commit 2a0bbd23
            # (#106832) attaches per-session classification metadata describing
            # session type, purpose, and behavioural characteristics. Silently
            # no-ops when absent so existing sessions are unaffected.
            _clf = (
                s.get("classificationFacts")
                or s.get("classification_facts")
                or s.get("sessionClassification")
                or s.get("session_classification")
                or s.get("sessionFacts")
            )
            if _clf is not None:
                extra["classificationFacts"] = _clf
            tok_total = int(s.get("totalTokens") or 0)
            tok_in = int(s.get("inputTokens") or 0)
            tok_out = int(s.get("outputTokens") or 0)
            tok_cr = int(s.get("cacheReadTokens") or 0)
            tok_cw = int(s.get("cacheWriteTokens") or 0)
            # #2794: prefer explicit reasoning field; fall back to totalTokens
            # residual so reasoning_tokens is never silently zero for
            # extended-thinking sessions that don't emit a separate key.
            tok_reasoning: Optional[int] = s.get("reasoningTokens") or s.get("reasoning_tokens")
            if tok_reasoning is None and tok_total:
                tok_reasoning = max(0, tok_total - (tok_in + tok_out + tok_cr + tok_cw))
            out.append(
                Session(
                    agent=self.name,
                    id=s.get("sessionId") or s.get("key") or "",
                    display_name=s.get("displayName") or "",
                    model=s.get("model") or "",
                    source=s.get("channel") or (_sk if _sk in ("talk", "voice", "realtime") else "") or "",
                    started_at=started_at,
                    total_tokens=tok_total,
                    input_tokens=tok_in,
                    output_tokens=tok_out,
                    cache_read_tokens=tok_cr,
                    cache_write_tokens=tok_cw,
                    reasoning_tokens=int(tok_reasoning or 0),
                    cost_usd=float(s["costUsd"]) if s.get("costUsd") is not None else None,
                    ended_at=float(s["endedAt"]) / 1000.0 if s.get("endedAt") else None,
                    end_reason=s.get("endReason") or s.get("end_reason") or "",
                    parent_id=s.get("parentId") or None,
                    message_count=int(s.get("messageCount") or 0),
                    title=s.get("title") or "",
                    cost_status=s.get("costStatus") or "",
                    extra=extra,
                )
            )
        return out

    def read_session(self, session_id: str) -> Optional[Session]:
        for s in self.list_sessions(limit=1000):
            if s.id == session_id or s.id.startswith(session_id):
                return s
        return None

    def list_events(self, session_id: str, limit: int = 500) -> List[Event]:
        """Return events for a session in the unified Event shape.

        Reads from the DuckDB events table (filtered by agent_type='openclaw'
        and session_id) so per-agent session views and runtime-aware
        endpoints stay consistent with what /api/transcript would render.

        Falls back to ``[]`` on any error so a flaky local store never
        breaks the dashboard. The legacy rich transcript route in
        ``dashboard.py`` is unchanged.
        """
        events: List[Event] = []
        try:
            from clawmetry import local_store as _ls
            store = _ls.get_store(read_only=True)
            rows = store._fetch(
                "SELECT id, event_type, ts, model, token_count, data, agent_id, node_id "
                "FROM events WHERE agent_type = ? AND session_id = ? "
                "ORDER BY ts ASC LIMIT ?",
                ["openclaw", str(session_id), int(limit)],
            )
            for r in rows or []:
                # ts column is VARCHAR; coerce to float, default 0.0.
                ts_raw = r[2]
                try:
                    ts_f = float(ts_raw) if ts_raw not in (None, "") else 0.0
                except (TypeError, ValueError):
                    ts_f = 0.0
                extra: dict = {}
                content_text = ""
                if r[3]:
                    extra["model"] = r[3]
                # r[6] = agent_id, r[7] = node_id — surface structured log
                # context fields so callers can correlate events by agent and node.
                if r[6]:
                    extra["agent_id"] = r[6]
                if r[7]:
                    extra["node_id"] = r[7]
                # r[5] = data BLOB — decode and surface per-type token split
                # (input/output/cache_read/cache_write) so callers can measure
                # per-turn cache efficiency without re-reading the raw file.
                # Also extract channel/hostname from gateway log record top-level
                # fields when present (no dedicated DB columns for these).
                raw_data = r[5]
                if raw_data is not None:
                    try:
                        if isinstance(raw_data, (bytes, bytearray)):
                            raw_data = bytes(raw_data).decode("utf-8", "replace")
                        obj = json.loads(raw_data) if isinstance(raw_data, str) else raw_data
                        if isinstance(obj, dict):
                            # Surface gateway log-record top-level structured
                            # fields. channel/hostname keep their names; the
                            # severity level is exposed as ``log_level`` and the
                            # originating subsystem as ``subsystem`` so callers
                            # can filter or alert on log severity and origin
                            # (closes #3055 / #3013).
                            for _field, _key in (
                                ("channel", "channel"),
                                ("hostname", "hostname"),
                                ("level", "log_level"),
                                ("subsystem", "subsystem"),
                            ):
                                _val = obj.get(_field)
                                if _val:
                                    extra[_key] = _val
                            # SDK transcript identity target (#3323): PR #95030
                            # stores the target identity on event blobs so
                            # consumers can correlate events to agent/session context.
                            _idt = obj.get("target") or obj.get("identityTarget")
                            if _idt is not None:
                                extra["identityTarget"] = _idt
                            # Talk / realtime-voice / managed-room lifecycle
                            # fields (#2957). sync.py stores these top-level in
                            # the data blob for voice events (sync.py ~L4960);
                            # surface them so callers see voice/Talk metadata.
                            # String fields skip empties; numeric fields use an
                            # explicit None check so a legitimate 0 (e.g. a
                            # zero-byte payload) is preserved rather than dropped.
                            for _field in ("mode", "transport", "provider"):
                                _val = obj.get(_field)
                                if _val:
                                    extra[_field] = _val
                            for _field in ("duration_ms", "size_bytes"):
                                _val = obj.get(_field)
                                if _val is not None:
                                    extra[_field] = _val
                            # First-event latency + slow-reply diagnostic (#3016):
                            # harness-emitted fields surface into Event.extra so
                            # callers can filter/bucket without re-reading raw JSONL.
                            _fe = (
                                obj.get("firstEventLatencyMs")
                                or obj.get("first_event_latency_ms")
                            )
                            if _fe is not None:
                                try:
                                    extra["firstEventLatencyMs"] = float(_fe)
                                except (TypeError, ValueError):
                                    pass
                            _slow = obj.get("slowReply") or obj.get("slow_reply")
                            if _slow:
                                extra["slowReply"] = True
                            # Talk/voice/managed-room lifecycle fields stored by
                            # ingest_talk_lifecycle() under camelCase keys; map to
                            # unprefixed names so callers don't need to know the
                            # storage key.  talkFinal uses is-not-None because
                            # False is a meaningful value (non-final segment).
                            for _ekey, _bkey in (
                                ("mode",        "talkMode"),
                                ("transport",   "talkTransport"),
                                ("provider",    "talkProvider"),
                                ("brain",       "talkBrain"),
                                ("duration_ms", "talkDurationMs"),
                                ("byte_length", "talkByteLength"),
                            ):
                                _val = obj.get(_bkey)
                                if _val is not None:
                                    extra[_ekey] = _val
                            _final = obj.get("talkFinal")
                            if _final is not None:
                                extra["final"] = _final
                            # TTS gateway RPC fields (#3569): tts.speak records
                            # carry char_count, voice_id, and audio_bytes;
                            # surface them so cost and identity are observable.
                            for _field in ("char_count", "voice_id"):
                                _val = obj.get(_field) or obj.get(
                                    "characterCount" if _field == "char_count" else "voiceId"
                                )
                                if _val is not None:
                                    extra[_field] = _val
                            _abytes = obj.get("audio_bytes") or obj.get("audioBytes")
                            if _abytes is not None:
                                extra["audio_bytes"] = _abytes
                            # Fish Audio TTS fields (#4429): S2.1 hosted streaming
                            # synthesis and S2 Pro local reference-voice. Aliases
                            # follow harness naming conventions; isLocal routes S2
                            # Pro events to the $0 cost path in providers_pricing.
                            _fa_stream = (
                                obj.get("streamState")
                                or obj.get("streaming_state")
                                or obj.get("isStreaming")
                            )
                            if _fa_stream is not None:
                                extra["streamState"] = _fa_stream
                            _fa_tel = (
                                obj.get("telephonyCallId")
                                or obj.get("telephony_call_id")
                            )
                            if _fa_tel is not None:
                                extra["telephonyCallId"] = _fa_tel
                            _fa_model = obj.get("ttsModel") or obj.get("fishModel")
                            if _fa_model is not None:
                                extra["ttsModel"] = _fa_model
                            _fa_local = obj.get("isLocal") or obj.get("is_local")
                            if _fa_local is not None:
                                extra["isLocal"] = bool(_fa_local)
                            # Fast-mode state (#3322): PR #85104 emits fastMode on
                            # event blobs; try all three spellings in precedence order.
                            for _fmkey in ("fastMode", "isFastMode", "talkFastMode"):
                                _fmval = obj.get(_fmkey)
                                if _fmval is not None:
                                    extra["fastMode"] = _fmval if isinstance(_fmval, str) else bool(_fmval)
                                    break
                            # Fast-mode fallback/cutoff metadata (#3341): PR #85104
                            # also emits cutoff state on event blobs; extract reason,
                            # transition count, delivery mode, and fallback model.
                            _fmc = obj.get("fastModeCutoff")
                            if _fmc is not None:
                                extra["fastModeCutoff"] = bool(_fmc)
                            _fmc_reason = obj.get("fastModeCutoffReason") or obj.get("cutoffReason")
                            if _fmc_reason is not None:
                                extra["fastModeCutoffReason"] = _fmc_reason
                            _fmc_count = obj.get("fastModeTransitionCount") or obj.get("transitionCount")
                            if _fmc_count is not None:
                                try:
                                    extra["fastModeTransitionCount"] = int(_fmc_count)
                                except (TypeError, ValueError):
                                    pass
                            _fmc_mode = obj.get("fastModeDeliveryMode") or obj.get("deliveryMode")
                            if _fmc_mode is not None:
                                extra["fastModeDeliveryMode"] = _fmc_mode
                            _fm_fallback = obj.get("fallbackModel") or obj.get("fastModeFallbackModel")
                            if _fm_fallback is not None:
                                extra["fallbackModel"] = _fm_fallback
                            # Runtime-engine fallback dimension (#3649): same
                            # atomic engine field captured at the event level.
                            _fb_runtime = (
                                obj.get("fallbackRuntime")
                                or obj.get("fallbackRuntimeEngine")
                                or obj.get("runtimeEngine")
                            )
                            if _fb_runtime is not None:
                                extra["fallbackRuntime"] = _fb_runtime
                            # /think reasoning-level tier (#3324): PR #94067 stores
                            # the active level (light/medium/deep) on model-turn
                            # records; try camelCase then snake_case.
                            _tl = obj.get("thinkLevel") or obj.get("reasoningLevel")
                            if _tl is not None:
                                extra["thinkLevel"] = _tl
                            # GLM/Zhipu overload classification (#3343): PR #93241
                            # emits overload state tags on event blobs; surface
                            # both the classification and any failover model ref.
                            _ovl = obj.get("overloadClassification") or obj.get("glmOverloadState")
                            if _ovl is not None:
                                extra["overloadClassification"] = _ovl
                            _glm_fov = obj.get("failoverModel") or obj.get("failoverModelRef")
                            if _glm_fov is not None:
                                extra["failoverModel"] = _glm_fov
                            # Zai synthesized-model baseUrl (#3343): PR #94461.
                            _zai = obj.get("zaiBaseUrl") or obj.get("synthesizedModelBaseUrl") or obj.get("glm5BaseUrl")
                            if _zai is not None:
                                extra["zaiBaseUrl"] = _zai
                            # Per-conversation capability profile (#3469): PR #98536.
                            _cap_profile = (
                                obj.get("capabilityProfile")
                                or obj.get("conversationCapability")
                            )
                            if _cap_profile is not None:
                                extra["capabilityProfile"] = _cap_profile
                            # Normalized TTFR keys (#3054): also write ttfr_ms /
                            # slow_reply so callers that read the normalized form
                            # don't need to know the original key spellings.
                            for _lf in ("latency_ms", "ttfr_ms", "firstEventLatencyMs", "first_event_latency_ms"):
                                _lv = obj.get(_lf)
                                if _lv is not None:
                                    try:
                                        extra["ttfr_ms"] = float(_lv)
                                    except (TypeError, ValueError):
                                        pass
                                    break
                            _sr = obj.get("slow_reply") or obj.get("slowReply") or obj.get("is_slow")
                            if _sr:
                                extra["slow_reply"] = True
                            # NeMo Guardrails catalog dispatch tag (#3254):
                            # toolMetas carries tool_use blocks from the assistant
                            # turn; names in _NEMOCLAW_CATALOG_TOOLS are guardrail
                            # control-plane calls, not real agent actions.
                            _tool_metas = (
                                obj.get("toolMetas")
                                or (obj.get("data") or {}).get("toolMetas")
                                or []
                            )
                            if isinstance(_tool_metas, list):
                                _catalog = [
                                    m["name"] for m in _tool_metas
                                    if isinstance(m, dict)
                                    and m.get("name") in _NEMOCLAW_CATALOG_TOOLS
                                ]
                                if _catalog:
                                    extra["hasCatalogTools"] = True
                                    extra["catalogToolNames"] = _catalog
                            # Top-level tool.call events store the name at obj["name"].
                            _tname = obj.get("name") or (obj.get("data") or {}).get("name")
                            if isinstance(_tname, str) and _tname in _NEMOCLAW_CATALOG_TOOLS:
                                extra["isCatalogTool"] = True
                            msg = obj.get("message")
                            if isinstance(msg, str):
                                content_text = msg
                            src = msg if isinstance(msg, dict) else obj
                            usage = src.get("usage") if isinstance(src.get("usage"), dict) else {}
                            if usage:
                                for dst, *keys in [
                                    ("inputTokens", "input_tokens", "inputTokens", "input"),
                                    ("outputTokens", "output_tokens", "outputTokens", "output"),
                                    ("cacheReadTokens", "cache_read_input_tokens", "cacheReadInputTokens", "cacheRead"),
                                    ("cacheWriteTokens", "cache_creation_input_tokens", "cacheCreationInputTokens", "cacheWrite"),
                                    ("totalTokens", "totalTokens", "total_tokens"),
                                    ("contextTokens", "contextTokens", "context_tokens"),
                                ]:
                                    for k in keys:
                                        v = usage.get(k)
                                        if v is not None:
                                            extra[dst] = int(v)
                                            break
                                # Extended-thinking / reasoning tokens: prefer
                                # an explicit key (e.g. thinking_input_tokens);
                                # fall back to totalTokens residual for sessions
                                # that report totalTokens without a separate key.
                                _rt = _reasoning_tokens(usage)
                                if _rt:
                                    extra["reasoningTokens"] = _rt
                                else:
                                    _tt = extra.get("totalTokens")
                                    if _tt is not None:
                                        _split = (
                                            extra.get("inputTokens", 0)
                                            + extra.get("outputTokens", 0)
                                            + extra.get("cacheReadTokens", 0)
                                            + extra.get("cacheWriteTokens", 0)
                                        )
                                        _res = max(0, int(_tt) - _split)
                                        if _res:
                                            extra["reasoningTokens"] = _res
                            # Walk message.content blocks for tool_result.details (#3255).
                            # nemoClawBuildToolResult attaches a `details` dict on every
                            # tool_result block; _build_spans_from_events() already reads
                            # it for OTel spans but list_events() was not propagating it
                            # to Event.extra, so the live event stream lacked this data.
                            if isinstance(msg, dict):
                                _content = msg.get("content")
                                if isinstance(_content, list):
                                    _tr_details = [
                                        {
                                            "tool_use_id": (
                                                blk.get("tool_use_id")
                                                or blk.get("toolUseId")
                                            ),
                                            "details": blk["details"],
                                        }
                                        for blk in _content
                                        if isinstance(blk, dict)
                                        and blk.get("type") == "tool_result"
                                        and blk.get("details") is not None
                                    ]
                                    if _tr_details:
                                        extra["tool_result_details"] = _tr_details
                            # Cloud workspace conflict fields (#4747): sync.py stores
                            # conflictedPaths / resolution / stagedRef in the data blob
                            # but list_events never extracted them, so Event.extra was
                            # empty for these rows and transcript callers saw nothing.
                            if str(r[1] or "") == "workspace.conflict":
                                _wc_paths = (
                                    obj.get("conflictedPaths")
                                    or obj.get("conflicted_paths")
                                    or []
                                )
                                if isinstance(_wc_paths, list):
                                    extra["conflictedPaths"] = _wc_paths
                                _wc_res = (
                                    obj.get("resolution")
                                    or obj.get("resolutionAction")
                                    or obj.get("resolution_action")
                                )
                                if _wc_res is not None:
                                    extra["resolution"] = _wc_res
                                _wc_sr = obj.get("stagedRef") or obj.get("staged_ref")
                                if _wc_sr is not None:
                                    extra["stagedRef"] = _wc_sr
                                _wc_kept = (
                                    obj.get("keptLocalPaths")
                                    or obj.get("kept_local_paths")
                                    or obj.get("cloudWorkerKeptLocal")
                                    or obj.get("cloud_worker_kept_local")
                                    or []
                                )
                                if isinstance(_wc_kept, list) and _wc_kept:
                                    extra["keptLocalPaths"] = _wc_kept
                                _wc_path_str = (
                                    ", ".join(_wc_paths)
                                    if isinstance(_wc_paths, list) and _wc_paths
                                    else "(no paths)"
                                )
                                content_text = f"Cloud workspace conflict: {_wc_path_str}"
                                if _wc_res:
                                    content_text += f" — {_wc_res}"
                            # Canvas dashboard pin state (#4864): harness PR #124044
                            # surfaces failed pin events; extract pin state and failure
                            # reason so the dashboard can show them instead of leaving
                            # failed pins invisible. Covers camelCase + snake_case aliases
                            # since the harness has used both in adjacent features.
                            _canvas_pin_state = (
                                obj.get("canvasPinState")
                                or obj.get("canvas_pin_state")
                                or obj.get("pinState")
                            )
                            if _canvas_pin_state is not None:
                                extra["canvasPinState"] = _canvas_pin_state
                            _canvas_pin_id = (
                                obj.get("canvasPinId")
                                or obj.get("canvas_pin_id")
                                or obj.get("pinId")
                                or obj.get("dashboardPinId")
                            )
                            if _canvas_pin_id is not None:
                                extra["canvasPinId"] = str(_canvas_pin_id)
                            _canvas_pin_reason = (
                                obj.get("canvasPinFailureReason")
                                or obj.get("pinFailureReason")
                                or obj.get("canvas_pin_failure_reason")
                            )
                            if _canvas_pin_reason is not None:
                                extra["canvasPinFailureReason"] = _canvas_pin_reason
                            _canvas_id = (
                                obj.get("canvasId")
                                or obj.get("canvas_id")
                                or obj.get("dashboardId")
                            )
                            if _canvas_id is not None:
                                extra["canvasId"] = str(_canvas_id)
                            # Construct a readable content_text for canvas.* events so
                            # the Brain tab and transcript view show a useful label
                            # instead of an empty row.
                            _ev_type_str = str(r[1] or "")
                            if not content_text and _ev_type_str.startswith("canvas."):
                                if _canvas_pin_state == "failed":
                                    content_text = "Canvas pin failed"
                                    if _canvas_pin_id:
                                        content_text += f" ({_canvas_pin_id})"
                                    if _canvas_pin_reason:
                                        content_text += f": {_canvas_pin_reason}"
                                elif _canvas_pin_state:
                                    content_text = f"Canvas pin: {_canvas_pin_state}"
                    except Exception:
                        pass
                # #2794: DB token_count derives from input+output and under-counts
                # reasoning turns; prefer totalTokens from the blob when larger.
                _ev_tokens = int(r[4] or 0)
                _tt = extra.get("totalTokens")
                if _tt is not None and int(_tt) > _ev_tokens:
                    _ev_tokens = int(_tt)
                events.append(Event(
                    agent=self.name,
                    session_id=str(session_id),
                    id=str(r[0]),
                    type=str(r[1] or "event"),
                    ts=ts_f,
                    content=content_text,
                    tokens=_ev_tokens,
                    extra=extra,
                ))
        except Exception as exc:
            logger.debug("openclaw list_events read failed: %s", exc)
        return events

    def capabilities(self) -> Set[Capability]:
        return {
            Capability.SESSIONS,
            Capability.EVENTS,
            Capability.COST,
            Capability.SUBAGENTS,
            Capability.CRONS,
            Capability.SKILLS,
            Capability.MEMORY,
            Capability.BRAIN,
            Capability.LOGS,
            Capability.GATEWAY_RPC,
            Capability.CHANNELS,
            # The trajectory recorder writes ``context.compiled`` (system
            # prompt + tool definitions) next to every transcript; the daemon
            # ingests it into session_context (sync._sync_trajectory_context).
            Capability.INPUTS,
            # Reasoning: OpenClaw persists assistant ``message.content[]``
            # blocks of ``type: "thinking"`` (the transcript writer keeps them
            # when a thinking level is set); the tracing/anatomy readers turn
            # each block into a reasoning span. See trail_coverage().
            Capability.REASONING,
        }

    def trail_coverage(self) -> dict:
        """Decision-trail coverage for OpenClaw session JSONL.

        Inputs are ``full``: the trajectory sidecar's ``context.compiled``
        carries the system prompt, the prompt and the tool definitions on
        every model call, and the daemon reads that event out of the sidecar
        (``sync._sync_trajectory_context``). It is written only when
        ``OPENCLAW_TRAJECTORY`` is not turned off. Reasoning is ``partial``:
        the session transcript keeps assistant ``message.content[]`` blocks
        of ``type: "thinking"`` only when the session runs with a thinking
        level set (``thinking_level_change`` events record the switch); with
        thinking off, or a model that has no extended thinking, the
        transcript carries plain ``text`` blocks and there is nothing to show.
        """
        return {
            "inputs": "full",
            "reasoning": "partial",
            "note": ("<sid>.trajectory.jsonl context.compiled carries systemPrompt, "
                     "prompt, tools[] (name/description/parameters), transport, "
                     "streamStrategy, imagesCount plus workspaceDir/provider/modelId "
                     "on the line (written only when OPENCLAW_TRAJECTORY is not off); "
                     "assistant message.content[] thinking blocks are written only "
                     "while a thinking level is set for the session"),
        }

    # ── Span reconstruction (issue #1010 / Trace 4) ───────────────────────────────────────────────

    @staticmethod
    def _span_id(*parts: str) -> str:
        return hashlib.sha256(":".join(parts).encode()).hexdigest()[:16]

    @staticmethod
    def _trace_id(session_id: str) -> str:
        return hashlib.sha256(session_id.encode()).hexdigest()[:32]

    @staticmethod
    def _build_spans_from_events(
        events: list, session_id: str, agent_type: str = "openclaw"
    ) -> list:
        """Map raw JSONL objects to OTel-shaped span dicts.

        Mapping per issue #1010:
        - ``session`` (version set)    → root span (INTERNAL)
        - ``message`` (role=assistant) → llm.call span (CLIENT, child of root)
          - each tool_use block        → tool.<name> span (CLIENT, child of llm)
        - ``message`` (role=user)      → matched tool_result blocks fold their
          structured ``details`` payload + ``is_error`` flag + text content back
          onto the tool span identified by ``tool_use_id`` (#2733).
        - ``subagent_spawn``           → agent.spawn span (INTERNAL, link to child trace)
        - ``commentary`` / ``progress`` → commentary/progress span (INTERNAL,
          child of root) preserving the narration text + subtype (#3015).

        ``agent_type`` stamps every span's runtime identity (Agent Graph
        WS-A). It defaults to ``'openclaw'`` but callers ingesting the same
        transcript shape for another runtime (NemoClaw sandbox batches via
        ``sync._flush_session_batch(..., agent_type='nemoclaw')``) pass their
        own id so the Agent Graph doesn't mislabel their nodes. Spawn spans
        additionally carry ``agent_id=<child label>`` (subagent/agent label
        off the spawn event, fallback ``'subagent'``) so the graph's
        ``main → child`` edge survives the ``src == dst`` self-edge filter.

        Span IDs are deterministic SHA-256 prefixes so re-ingesting is idempotent.
        """
        _sid = OpenClawAdapter._span_id
        trace_id = OpenClawAdapter._trace_id(session_id)
        session_span_id = _sid("session", session_id)
        now = _time.time()
        spans: list = []
        # tool_use_id → tool span dict, populated as assistant tool_use blocks
        # are emitted; consumed when a later user tool_result block references
        # the same id (#2733).
        tool_span_by_id: dict = {}
        # First-event latency tracking (#3016): capture session start time so
        # we can record the wall-clock delta to the first assistant reply.
        _session_start_ts: float | None = None
        _first_assistant_done: bool = False

        for obj in events:
            if not isinstance(obj, dict):
                continue
            t = obj.get("type")
            raw_ts = obj.get("timestamp") or obj.get("ts") or now
            try:
                ts = float(raw_ts)
            except (TypeError, ValueError):
                ts = now

            if t == "session" and obj.get("version") is not None:
                _session_start_ts = ts
                spans.append({
                    "span_id": session_span_id,
                    "trace_id": trace_id,
                    "name": "session",
                    "kind": "INTERNAL",
                    "start_ts": ts,
                    "session_id": session_id,
                    "agent_type": agent_type,
                    "attributes": {"session.version": obj.get("version"), "session.id": session_id},
                })

            elif t == "message" and isinstance(obj.get("message"), dict):
                msg = obj["message"]
                role = msg.get("role")
                content = msg.get("content") or []
                if role == "user":
                    # Tool results live in user-role messages. Fold the
                    # structured details payload + is_error flag + text content
                    # back onto the originating tool span (#2733). Orphan
                    # tool_results (no matching tool_use_id) are skipped.
                    if not isinstance(content, list):
                        continue
                    for block in content:
                        if not isinstance(block, dict) or block.get("type") != "tool_result":
                            continue
                        tu_id = block.get("tool_use_id") or block.get("toolUseId") or ""
                        target = tool_span_by_id.get(tu_id)
                        if target is None:
                            continue
                        attrs = target.get("attributes") or {}
                        attrs["tool.result_present"] = True
                        if "is_error" in block:
                            attrs["tool.result_is_error"] = bool(block.get("is_error"))
                        # NemoClaw nemoClawBuildToolResult helper attaches a
                        # top-level structured ``details`` dict on the result
                        # (catalog hits, schemas, dispatch output). Surface it
                        # so downstream Tracing/Event.extra can render the real
                        # payload instead of just the stringified text wrapper.
                        details = block.get("details")
                        if details is not None:
                            attrs["tool.result_details"] = details
                            if isinstance(details, dict):
                                attrs["tool.result_details_keys"] = sorted(details.keys())
                        # Walk the tool_result content array. Text blocks
                        # collapse into a single string for quick read
                        # (NemoClaw JSON-stringified wrapper, or plain text
                        # from native tools). Non-text block types
                        # (resource_link, resource, audio, image) are
                        # surfaced by sorted type-list so downstream UI can
                        # see that MCP returned a non-text payload (#2731).
                        # Coercion metadata (the harness preserves the
                        # original block type when it materializes a
                        # resource_link / resource / audio / malformed-image
                        # into a text-safe shape) is recorded as
                        # {from, to} pairs. Accepts the common field-name
                        # variants seen in the wild.
                        result_content = block.get("content")
                        text_parts: list = []
                        types_seen: set = set()
                        coercions: list = []
                        if isinstance(result_content, str):
                            text_parts.append(result_content)
                        elif isinstance(result_content, list):
                            for inner in result_content:
                                if not isinstance(inner, dict):
                                    continue
                                inner_type = inner.get("type")
                                if isinstance(inner_type, str) and inner_type:
                                    types_seen.add(inner_type)
                                if inner_type == "text":
                                    val = inner.get("text")
                                    if isinstance(val, str):
                                        text_parts.append(val)
                                coerced_from = (
                                    inner.get("coerced_from")
                                    or inner.get("coercedFrom")
                                    or inner.get("original_type")
                                    or inner.get("originalType")
                                )
                                if isinstance(coerced_from, str) and coerced_from:
                                    coercions.append({
                                        "from": coerced_from,
                                        "to": inner_type if isinstance(inner_type, str) and inner_type else "unknown",
                                    })
                        if text_parts:
                            attrs["tool.result_text"] = "".join(text_parts)
                        if types_seen:
                            attrs["tool.result_content_types"] = sorted(types_seen)
                        if coercions:
                            attrs["tool.result_coercions"] = coercions
                        target["attributes"] = attrs
                        # End-time the tool span to whatever the result arrived
                        # at. start_ts ≤ end_ts isn't enforced (assistant emits
                        # tool_use and user tool_result share clock); but the
                        # signal is still useful for duration heuristics.
                        target["end_ts"] = ts
                    continue
                if role != "assistant":
                    continue
                model = msg.get("model") or ""
                usage = msg.get("usage") or {}
                tok_in = int(usage.get("input_tokens") or usage.get("inputTokens") or usage.get("input") or 0)
                tok_out = int(usage.get("output_tokens") or usage.get("outputTokens") or usage.get("output") or 0)
                # Reasoning/thinking tokens (#2876) are billed but not part of
                # input/output; fold them into token_count so LLM-span cost
                # totals are not systematically under-reported.
                tok_reasoning = _reasoning_tokens(usage)
                # totalTokens includes reasoning tokens on extended-thinking models;
                # prefer it when present so spans are not under-counted (#2794).
                tok_total = int(usage.get("totalTokens") or usage.get("total_tokens") or 0)
                llm_sid = _sid("llm", session_id, str(raw_ts))
                # First-event latency + slow-reply diagnostic (#3016): record
                # on the FIRST assistant span only — subsequent turns are not
                # the "initial reply delay" the harness tracks.
                llm_attrs: dict = {}
                if not _first_assistant_done:
                    _first_assistant_done = True
                    if _session_start_ts is not None and ts > _session_start_ts:
                        llm_attrs["llm.first_event_latency_s"] = round(
                            ts - _session_start_ts, 3
                        )
                    _fe_ms = (
                        obj.get("firstEventLatencyMs")
                        or obj.get("first_event_latency_ms")
                    )
                    if _fe_ms is not None:
                        try:
                            llm_attrs["llm.first_event_latency_ms"] = float(_fe_ms)
                        except (TypeError, ValueError):
                            pass
                    _slow = obj.get("slowReply") or obj.get("slow_reply")
                    if _slow:
                        llm_attrs["llm.slow_reply"] = True
                spans.append({
                    "span_id": llm_sid,
                    "trace_id": trace_id,
                    "parent_span_id": session_span_id,
                    "name": f"llm.call {model}".strip() if model else "llm.call",
                    "kind": "CLIENT",
                    "start_ts": ts,
                    "session_id": session_id,
                    "agent_type": agent_type,
                    "model": model or None,
                    "tokens_input": tok_in or None,
                    "tokens_output": tok_out or None,
                    "tokens_reasoning": tok_reasoning or None,
                    # max() is the only safe combination of #2876 and #2794:
                    # totalTokens (when the SDK emits it) ALREADY includes the
                    # reasoning share, so summing them would double-count, and
                    # either alone under-counts when the other key is present.
                    "token_count": max(tok_total, tok_in + tok_out + tok_reasoning) or None,
                    "attributes": llm_attrs or None,
                })
                if isinstance(content, list):
                    for block in content:
                        if not isinstance(block, dict) or block.get("type") != "tool_use":
                            continue
                        orig_name = block.get("name") or "tool"
                        tool_name = orig_name
                        tool_id = block.get("id") or ""
                        blk_input = block.get("input")
                        # NemoClaw compact tool-catalog dispatch (#2682): the
                        # injected meta-tool is named "tool_call" and carries the
                        # REAL dispatched tool in input.name (the wrapper
                        # dispatches via catalog.get(name)). Unwrap it so the
                        # Tracing tab shows the real tool, not a generic
                        # "tool_call" span. Falls back to the literal name on
                        # old/missing data so it never crashes.
                        attrs: dict = {}
                        if tool_name == "tool_call" and isinstance(blk_input, dict):
                            real = blk_input.get("name")
                            if isinstance(real, str) and real.strip():
                                real = real.strip()
                                attrs.update({
                                    "nemoclaw.catalog_dispatch": True,
                                    "nemoclaw.meta_tool": "tool_call",
                                    "nemoclaw.dispatched_tool": real,
                                })
                                tool_name = real
                        # Catalog meta-tools (tool_search/tool_describe/tool_call)
                        # are guardrail dispatches, not real agent actions — tag
                        # by the ORIGINAL name (tool_name may now be the unwrapped
                        # real tool).
                        if orig_name in _NEMOCLAW_CATALOG_TOOLS:
                            attrs["nemoclaw.catalog_guardrail"] = True
                        tool_span: dict = {
                            "span_id": _sid("tool", session_id, str(raw_ts), tool_id, tool_name),
                            "trace_id": trace_id,
                            "parent_span_id": llm_sid,
                            "name": f"tool.{tool_name}",
                            "kind": "CLIENT",
                            "start_ts": ts,
                            "session_id": session_id,
                            "agent_type": agent_type,
                            "tool_name": tool_name,
                            "input": blk_input,
                            "attributes": attrs or None,
                        }

                        spans.append(tool_span)
                        if tool_id:
                            tool_span_by_id[tool_id] = tool_span

            elif t in ("subagent_spawn", "agent_spawn"):
                sub_id = (
                    obj.get("subagent_id") or obj.get("agentId") or obj.get("agent_id") or ""
                )
                child_trace = hashlib.sha256(sub_id.encode()).hexdigest()[:32] if sub_id else ""
                # Child agent label (Agent Graph WS-A): the spawn span must
                # carry a DIFFERENT agent_id than the parent's 'main' or the
                # graph's src==dst filter drops the edge and the runtime
                # renders as one self-node. Prefer an explicit subagent/agent
                # type label off the event; fall back to the literal
                # 'subagent' — never the raw sub_id UUID (one node per spawn
                # would explode the graph).
                _child_label = (
                    obj.get("subagent_type") or obj.get("subagentType")
                    or obj.get("agentType") or obj.get("agent")
                    or obj.get("label") or ""
                )
                _child_label = (
                    str(_child_label).strip()
                    if isinstance(_child_label, str) and _child_label.strip()
                    else "subagent"
                )
                _spawn_attrs: dict = {"subagent.label": _child_label}
                if sub_id:
                    _spawn_attrs["subagent_id"] = sub_id
                spans.append({
                    "span_id": _sid("spawn", session_id, str(raw_ts), sub_id),
                    "trace_id": trace_id,
                    "parent_span_id": session_span_id,
                    "name": "agent.spawn",
                    "kind": "INTERNAL",
                    "start_ts": ts,
                    "session_id": session_id,
                    "agent_type": agent_type,
                    "agent_id": _child_label,
                    "links": [{"trace_id": child_trace, "span_id": "0" * 16}] if child_trace else None,
                    "attributes": _spawn_attrs,
                })

            elif t in ("commentary", "progress"):
                # The Claude CLI emits inter-tool commentary and long-running
                # progress updates as distinct JSONL event types (#89834,
                # #90883). These fell through every branch above, so the span
                # builder dropped them and their payload was silently discarded
                # (#3015). Emit a lightweight INTERNAL span under the session
                # root so the Tracing tab shows the narration/progress timeline
                # and downstream Event.extra can render the original payload.
                data = obj.get("data") if isinstance(obj.get("data"), dict) else {}
                comment_attrs: dict = {"event.kind": t}
                # The text lives under a handful of field-name variants
                # depending on which CLI path emitted it; surface the first
                # non-empty one as a quick-read string.
                text = (
                    obj.get("text") or obj.get("content") or obj.get("body")
                    or data.get("text") or data.get("content") or data.get("message")
                )
                if isinstance(text, str) and text.strip():
                    comment_attrs["commentary.text"] = text
                # A subtype/label distinguishes streams (e.g. "tool_progress"
                # vs "thinking" commentary); keep it when present.
                subtype = (
                    obj.get("subtype") or obj.get("label")
                    or data.get("subtype") or data.get("label")
                )
                if isinstance(subtype, str) and subtype.strip():
                    comment_attrs["commentary.subtype"] = subtype.strip()
                spans.append({
                    "span_id": _sid(t, session_id, str(raw_ts)),
                    "trace_id": trace_id,
                    "parent_span_id": session_span_id,
                    "name": t,
                    "kind": "INTERNAL",
                    "start_ts": ts,
                    "session_id": session_id,
                    "agent_type": agent_type,
                    "attributes": comment_attrs,
                })

            elif t == "first_assistant_event":
                latency_ms = (
                    obj.get("latency_ms")
                    or obj.get("ttfr_ms")
                    or obj.get("firstEventLatencyMs")
                    or obj.get("first_event_latency_ms")
                )
                slow_reply = bool(
                    obj.get("slow_reply")
                    or obj.get("slowReply")
                    or obj.get("is_slow")
                )
                fa_attrs: dict = {}
                if latency_ms is not None:
                    try:
                        fa_attrs["ttfr.latency_ms"] = float(latency_ms)
                    except (TypeError, ValueError):
                        pass
                if slow_reply:
                    fa_attrs["ttfr.slow_reply"] = True
                spans.append({
                    "span_id": _sid("ttfr", session_id, str(raw_ts)),
                    "trace_id": trace_id,
                    "parent_span_id": session_span_id,
                    "name": "first_response",
                    "kind": "INTERNAL",
                    "start_ts": ts,
                    "session_id": session_id,
                    "agent_type": agent_type,
                    "attributes": fa_attrs or None,
                })

            elif t == "compaction":
                # Harness fix #93084 preserves fresh usage data on compaction
                # records. Emit an INTERNAL span so the Tracing tab shows the
                # compaction boundary; surface tokens_before + any usage so
                # callers can see what was reclaimed and what was re-billed
                # (#3199).
                comp_attrs: dict = {"event.kind": "compaction"}
                summary = obj.get("summary")
                if isinstance(summary, str) and summary.strip():
                    comp_attrs["compaction.summary"] = summary[:500]
                tb = obj.get("tokensBefore") or obj.get("tokens_before")
                if tb is not None:
                    try:
                        comp_attrs["compaction.tokens_before"] = int(tb)
                    except (TypeError, ValueError):
                        pass
                from_hook = obj.get("fromHook") if obj.get("fromHook") is not None else obj.get("from_hook")
                if from_hook is not None:
                    comp_attrs["compaction.from_hook"] = bool(from_hook)
                comp_usage = obj.get("usage")
                if isinstance(comp_usage, dict):
                    tok_total = int(comp_usage.get("totalTokens") or comp_usage.get("total_tokens") or 0)
                    tok_in = int(comp_usage.get("input_tokens") or comp_usage.get("inputTokens") or comp_usage.get("input") or 0)
                    tok_out = int(comp_usage.get("output_tokens") or comp_usage.get("outputTokens") or comp_usage.get("output") or 0)
                    effective = tok_total or (tok_in + tok_out)
                    if effective:
                        comp_attrs["compaction.usage.total_tokens"] = effective
                spans.append({
                    "span_id": _sid("compaction", session_id, str(raw_ts)),
                    "trace_id": trace_id,
                    "parent_span_id": session_span_id,
                    "name": "compaction",
                    "kind": "INTERNAL",
                    "start_ts": ts,
                    "session_id": session_id,
                    "agent_type": agent_type,
                    "attributes": comp_attrs,
                })

            elif t == "retry":
                # Harness fix #92191/#93073 emits a retry event when the agent
                # retries a thinking-only or empty post-tool turn, carrying
                # retry reason and turn-kind metadata. Without this branch the
                # span builder drops retried turns silently, so the Tracing tab
                # shows a gap wherever a retry occurred (#3198).
                retry_reason = (
                    obj.get("reason") or obj.get("retry_reason") or obj.get("retryReason") or ""
                )
                turn_kind = (
                    obj.get("turn_kind") or obj.get("turnKind") or ""
                )
                retry_count = obj.get("count") or obj.get("retry_count") or obj.get("retryCount")
                retry_attrs: dict = {"event.kind": "retry"}
                if isinstance(retry_reason, str) and retry_reason.strip():
                    retry_attrs["retry.reason"] = retry_reason.strip()
                if isinstance(turn_kind, str) and turn_kind.strip():
                    retry_attrs["retry.turn_kind"] = turn_kind.strip()
                if retry_count is not None:
                    try:
                        retry_attrs["retry.count"] = int(retry_count)
                    except (TypeError, ValueError):
                        pass
                spans.append({
                    "span_id": _sid("retry", session_id, str(raw_ts)),
                    "trace_id": trace_id,
                    "parent_span_id": session_span_id,
                    "name": "retry",
                    "kind": "INTERNAL",
                    "start_ts": ts,
                    "session_id": session_id,
                    "agent_type": agent_type,
                    "attributes": retry_attrs,
                })

            elif t == "workspace.conflict":
                # Cloud workspace conflict span (#4747): surface in the Tracing
                # tab so the conflict marker appears at the right point in the
                # session timeline (same pattern as compaction/retry spans).
                _wc_paths = (
                    obj.get("conflictedPaths")
                    or obj.get("conflicted_paths")
                    or []
                )
                wc_attrs: dict = {"event.kind": "workspace.conflict"}
                if isinstance(_wc_paths, list) and _wc_paths:
                    wc_attrs["conflict.paths"] = _wc_paths
                    wc_attrs["conflict.path_count"] = len(_wc_paths)
                _wc_res = obj.get("resolution") or obj.get("resolutionAction")
                if _wc_res is not None:
                    wc_attrs["conflict.resolution"] = _wc_res
                _wc_sr = obj.get("stagedRef") or obj.get("staged_ref")
                if _wc_sr is not None:
                    wc_attrs["conflict.staged_ref"] = _wc_sr
                _wc_kept = (
                    obj.get("keptLocalPaths")
                    or obj.get("kept_local_paths")
                    or obj.get("cloudWorkerKeptLocal")
                    or obj.get("cloud_worker_kept_local")
                    or []
                )
                if isinstance(_wc_kept, list) and _wc_kept:
                    wc_attrs["conflict.kept_local"] = _wc_kept
                    wc_attrs["conflict.kept_local_count"] = len(_wc_kept)
                spans.append({
                    "span_id": _sid("workspace.conflict", session_id, str(raw_ts)),
                    "trace_id": trace_id,
                    "parent_span_id": session_span_id,
                    "name": "workspace.conflict",
                    "kind": "INTERNAL",
                    "start_ts": ts,
                    "session_id": session_id,
                    "agent_type": agent_type,
                    "attributes": wc_attrs,
                })

        return spans

    def reconstruct_spans(self, jsonl_path: str) -> list:
        """Read an OpenClaw JSONL transcript and return OTel-shaped span dicts.

        The returned list can be fed directly to ``local_store.ingest_span()``.
        Returns an empty list and logs a warning on I/O errors.
        """
        session_id = os.path.basename(jsonl_path).split(".jsonl", 1)[0]
        try:
            with open(jsonl_path, encoding="utf-8", errors="replace") as fh:
                events = []
                for line in fh:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        events.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
        except OSError as exc:
            logger.warning("reconstruct_spans: cannot read %s: %s", jsonl_path, exc)
            return []
        return self._build_spans_from_events(events, session_id)

    def running(self) -> bool:
        try:
            return bool(getattr(_d(), "GATEWAY_URL", None))
        except Exception:
            return False
