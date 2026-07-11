"""OpenClawAdapter — thin wrapper around existing dashboard.py helpers.

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

import hashlib
import json
import logging
import os
import time as _time
from typing import List, Optional, Set

from .base import AgentAdapter, Capability, DetectResult, Event, Session

logger = logging.getLogger("clawmetry.adapters.openclaw")

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
    18789 listening). Never raises."""
    home = os.environ.get("OPENCLAW_HOME") or os.path.expanduser("~/.openclaw")
    pid_file = os.path.join(home, "gateway", "gateway.pid")
    try:
        if os.path.exists(pid_file):
            with open(pid_file) as fh:
                pid = int((fh.read() or "0").strip())
            if pid > 0:
                os.kill(pid, 0)
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


def _openshell_sandbox_logs(name: str, count: int = 20) -> list:
    """Retrieve OCSF JSON audit log lines for a NemoClaw sandbox.

    Arms OCSF output first (idempotent settings set), then calls
    ``openshell logs <name> -n <count> --source all``.  For container-backed
    (non-terminal) sandboxes also merges the last ``count`` lines from the
    OpenClaw gateway log at ``/tmp/gateway.log`` (override with
    ``OPENSHELL_GATEWAY_LOG``), matching the harness's two-source merge in
    ``showSandboxLogsWithDeps`` (#3571).  Returns a list of parsed OCSF event
    dicts; silently drops non-JSON lines.  Never raises; returns ``[]`` when
    openshell is absent or any call fails.
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
        # /tmp/gateway.log (asserted in test/sandbox-logs-terminal.test.ts).
        # Read runtime kind via the existing phase-policy helper and merge when
        # the sandbox is not terminal-kind.
        phase_info = _openshell_sandbox_phase_policy(name)
        if phase_info.get("sandboxRuntimeKind", "").lower() != "terminal":
            _gw_log = os.environ.get("OPENSHELL_GATEWAY_LOG", "/tmp/gateway.log")
            try:
                with open(_gw_log, "r", encoding="utf-8", errors="replace") as _gf:
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


def _openshell_sandbox_logs_tail(name: str):
    """Spawn ``openshell logs <name> --source all --tail`` as a long-lived child
    process and return the ``subprocess.Popen`` handle.

    The caller owns process lifetime — drain stdout non-blockingly each sync
    tick and call ``proc.terminate()`` + ``proc.wait()`` on daemon shutdown.
    Returns ``None`` when openshell is absent or the spawn fails; never raises.
    """
    try:
        import shutil as _sh
        if not _sh.which("openshell"):
            return None
        import subprocess as _sp
        return _sp.Popen(
            ["openshell", "logs", name, "--source", "all", "--tail"],
            stdout=_sp.PIPE, stderr=_sp.DEVNULL, text=True, bufsize=1,
        )
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
                out.append(entry)
                continue
            elif provider in ("minimax", "minimax-api"):
                provider_key = "minimax"
                primary = f"minimax/{model}" if model else ""
                base_url = _resolve_minimax_base_url()
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


def _model_router_health_ok(port: int) -> bool:
    """True if the model-router ``/health`` endpoint answers 2xx on localhost.

    Falls back to a raw TCP connect (port accepting connections) when the HTTP
    probe errors, so a wedged-but-listening router still reads as up. Short
    timeouts keep detect() fast. Never raises.
    """
    try:
        import urllib.request as _u
        req = _u.Request(f"http://127.0.0.1:{port}/health", method="GET")
        with _u.urlopen(req, timeout=0.3) as resp:  # nosec B310 - localhost only
            status = getattr(resp, "status", None) or resp.getcode()
            return 200 <= int(status) < 300
    except Exception:
        pass
    try:
        import socket as _sock
        s = _sock.socket(_sock.AF_INET, _sock.SOCK_STREAM)
        s.settimeout(0.2)
        rc = s.connect_ex(("127.0.0.1", port))
        s.close()
        return rc == 0
    except Exception:
        return False


def _model_router_live() -> dict:
    """Runtime-liveness signal for the NemoClaw model-router proxy (#2795).

    ``_model_router_fingerprint`` only proves the router was *installed*;
    without a runtime probe a crashed router is indistinguishable from a
    healthy one. This discovers the live proxy and polls its ``/health``
    endpoint, surfacing the distinct liveness signal on ``DetectResult.meta``.

    Returns ``{"modelRouterRunning": bool}`` (plus ``modelRouterPort`` when the
    listening port is discoverable). Read-only, best-effort, never raises.
    """
    port = _discover_model_router_port()
    if port is None:
        return {"modelRouterRunning": False}
    return {"modelRouterPort": port, "modelRouterRunning": _model_router_health_ok(port)}


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

    Returns a dict with two keys when any plugin data is present:
    - ``"gatewayPluginHealth"`` — the raw list of plugin entries
      (``[{"name": str, "state": str, "type": str|None}, ...]``).
    - ``"gatewayPluginHealthSummary"`` — a ``{state: count}`` tally for quick
      health assessment (e.g. ``{"loaded": 3, "errored": 1}``).

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
        for entry in raw_plugins:
            if not isinstance(entry, dict):
                continue
            name = entry.get("name") or entry.get("id") or ""
            state = str(entry.get("state") or "").lower()
            ptype = entry.get("type") or entry.get("kind") or None
            if not name or not state:
                continue
            plugins.append({"name": name, "state": state, **({"type": ptype} if ptype else {})})
            summary[state] = summary.get(state, 0) + 1
        if not plugins:
            return {}
        return {"gatewayPluginHealth": plugins, "gatewayPluginHealthSummary": summary}
    except Exception:
        return {}


def _gateway_host_status() -> dict:
    """Host/system fields from the OpenClaw gateway.status RPC (#3551).

    As of harness CHANGELOG #100478 the gateway.status response includes
    host name, network address, OS, runtime, uptime, CPU, memory, and disk
    details alongside the existing ``plugins`` list.

    Returns a dict with whichever fields are present:
    - ``"gatewayHostName"``       — machine hostname
    - ``"gatewayNetworkAddress"`` — primary network address / IP
    - ``"gatewayHostOS"``         — OS name or platform string
    - ``"gatewayHostRuntime"``    — runtime identifier (e.g. Node version)
    - ``"gatewayHostUptime"``     — uptime in seconds
    - ``"gatewayHostCPU"``        — CPU usage value or dict
    - ``"gatewayHostMemory"``     — memory info (bytes or dict)
    - ``"gatewayHostDisk"``       — disk info (bytes or dict)

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
        return result
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
            # Gateway plugin health (#3200): per-plugin state (loaded/errored/
            # disabled) added to gateway.status in harness 2026.6.9 (#93395).
            # Only meaningful — and safe to query — when the gateway is live.
            if running:
                meta.update(_gateway_plugin_health())
                # Gateway host/system status (#3551): host name, OS, runtime,
                # uptime, CPU, memory, disk from the same gateway.status RPC.
                meta.update(_gateway_host_status())
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
        }

    # ── Span reconstruction (issue #1010 / Trace 4) ───────────────────────────────────────────────

    @staticmethod
    def _span_id(*parts: str) -> str:
        return hashlib.sha256(":".join(parts).encode()).hexdigest()[:16]

    @staticmethod
    def _trace_id(session_id: str) -> str:
        return hashlib.sha256(session_id.encode()).hexdigest()[:32]

    @staticmethod
    def _build_spans_from_events(events: list, session_id: str) -> list:
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
                    "agent_type": "openclaw",
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
                    "agent_type": "openclaw",
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
                            "agent_type": "openclaw",
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
                spans.append({
                    "span_id": _sid("spawn", session_id, str(raw_ts), sub_id),
                    "trace_id": trace_id,
                    "parent_span_id": session_span_id,
                    "name": "agent.spawn",
                    "kind": "INTERNAL",
                    "start_ts": ts,
                    "session_id": session_id,
                    "agent_type": "openclaw",
                    "links": [{"trace_id": child_trace, "span_id": "0" * 16}] if child_trace else None,
                    "attributes": {"subagent_id": sub_id} if sub_id else None,
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
                    "agent_type": "openclaw",
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
                    "agent_type": "openclaw",
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
                    "agent_type": "openclaw",
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
                    "agent_type": "openclaw",
                    "attributes": retry_attrs,
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
