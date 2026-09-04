"""Runtime-aware security posture registry.

Historically the Security tab's posture panel was OpenClaw-hardcoded:
``dashboard._scan_security_posture()`` looked for ``openclaw.json`` (local
file → docker exec → gateway API) and returned the infamous "No
openclaw.json found" fail state for every other runtime. This module makes
posture a per-runtime concern:

    register_posture_provider("openclaw", fn)   # fn() -> dict
    get_posture("claude_code")                  # dispatches, never raises
                                                # for unknown runtimes

Providers return the SAME envelope the frontend already consumes::

    {"runtime": rt, "status": "ok",
     "score": "A".."F"|"U", "score_label": str, "score_color": "#hex",
     "score_pct": float, "checks": [{id, label, status: pass|warn|fail,
     detail, remediation, severity, weight}, ...],
     "passed": n, "failed": n, "warnings": n, "total": n,
     "config_path": str|None, "scanned_at": iso8601}

Runtimes with no registered provider get an honest ``not_available``
envelope (HTTP 200 at the route — "no checks yet" is a state, not a
failure)::

    {"runtime": rt, "status": "not_available", "checks": [],
     "detail": "No security posture checks implemented for <label> yet", ...}

``dashboard._scan_security_posture`` is now a thin delegate to
``get_posture("openclaw")`` so existing callers (sync.py shadow scan,
tests) keep working unchanged.
"""
from __future__ import annotations

import json
import logging
import os
import re
import threading
from datetime import datetime
from typing import Any, Callable

logger = logging.getLogger("clawmetry.security_posture")

_providers: dict[str, Callable[[], dict]] = {}
_lock = threading.Lock()


def register_posture_provider(runtime: str, fn: Callable[[], dict]) -> None:
    """Register (or replace) the posture provider for *runtime*."""
    if not runtime:
        raise ValueError("runtime name required")
    with _lock:
        _providers[runtime.strip().lower()] = fn


def registered_runtimes() -> list[str]:
    with _lock:
        return sorted(_providers)


def get_posture(runtime: str) -> dict:
    """Run the posture provider for *runtime*.

    Unknown runtimes get the honest ``not_available`` envelope. Provider
    exceptions propagate — the route maps them to a 500 exactly as the
    legacy openclaw path did.
    """
    rt = (runtime or "openclaw").strip().lower()
    with _lock:
        fn = _providers.get(rt)
    if fn is None:
        return _with_node_checks(_not_available(rt))
    result = fn()
    if isinstance(result, dict):
        result.setdefault("runtime", rt)
        result.setdefault("status", "ok")
    return _with_node_checks(result)


def _with_node_checks(env: dict) -> dict:
    """Append the checks that are true of the NODE, whichever runtime is
    selected: today, the personal-data redaction line (WO-61). The line
    states the operator's setting; it does not move the runtime's score,
    because a redaction switch is not a misconfiguration of that runtime.
    """
    if not isinstance(env, dict):
        return env
    try:
        from clawmetry.redaction import pii_posture_check
        check = pii_posture_check()
    except Exception:
        return env
    checks = env.get("checks")
    if not isinstance(checks, list):
        checks = []
        env["checks"] = checks
    if any(isinstance(c, dict) and c.get("id") == check["id"] for c in checks):
        return env
    checks.append(check)
    for key, status in (("passed", "pass"), ("warnings", "warn"), ("failed", "fail")):
        if check["status"] == status:
            env[key] = int(env.get(key) or 0) + 1
    env["total"] = int(env.get("total") or 0) + 1
    return env


def _runtime_label(rt: str) -> str:
    """Best-effort display name via the adapter registry."""
    try:
        from clawmetry.adapters import registry

        adapter = registry.get(rt)
        if adapter is not None and adapter.display_name:
            return adapter.display_name
    except Exception:
        pass
    return rt


def _not_available(rt: str) -> dict:
    label = _runtime_label(rt)
    return {
        "runtime": rt,
        "status": "not_available",
        "detail": f"No security posture checks implemented for {label} yet",
        "checks": [],
        "score": "U",
        "score_label": "Not available",
        "score_color": "#64748b",
        "passed": 0,
        "failed": 0,
        "warnings": 0,
        "total": 0,
    }


def _score_envelope(checks: list[dict], *, runtime: str,
                    config_path: str | None = None,
                    extra: dict | None = None) -> dict:
    """Weight-based A–F scoring shared by all providers.

    pass = full weight, warn = half, fail = zero — identical math to the
    legacy openclaw scan so scores are comparable across runtimes.
    """
    total_weight = sum(c["weight"] for c in checks)
    earned = sum(c["weight"] for c in checks if c["status"] == "pass")
    earned += sum(c["weight"] * 0.5 for c in checks if c["status"] == "warn")
    pct = (earned / total_weight * 100) if total_weight > 0 else 0

    if pct >= 90:
        score, label, color = "A", "Excellent", "#22c55e"
    elif pct >= 75:
        score, label, color = "B", "Good", "#84cc16"
    elif pct >= 60:
        score, label, color = "C", "Fair", "#f59e0b"
    elif pct >= 40:
        score, label, color = "D", "Poor", "#f97316"
    else:
        score, label, color = "F", "Critical", "#ef4444"

    env = {
        "runtime": runtime,
        "status": "ok",
        "score": score,
        "score_label": label,
        "score_color": color,
        "score_pct": round(pct, 1),
        "checks": checks,
        "passed": sum(1 for c in checks if c["status"] == "pass"),
        "failed": sum(1 for c in checks if c["status"] == "fail"),
        "warnings": sum(1 for c in checks if c["status"] == "warn"),
        "total": len(checks),
        "config_path": config_path,
        "scanned_at": datetime.now().isoformat(),
    }
    if extra:
        env.update(extra)
    return env


def _check(cid: str, label: str, status: str, detail: str,
           remediation: str | None, severity: str, weight: int) -> dict:
    return {
        "id": cid,
        "label": label,
        "status": status,
        "detail": detail,
        "remediation": remediation,
        "severity": severity,
        "weight": weight,
    }


# ═══════════════════════════════════════════════════════════════════════════
# OpenClaw provider — the ENTIRE legacy scan, moved verbatim from
# dashboard.py::_scan_security_posture (which is now a thin delegate here).
# ═══════════════════════════════════════════════════════════════════════════


def openclaw_posture() -> dict:
    """Scan OpenClaw configuration for security misconfigurations.

    Returns a list of checks with pass/fail/warn status, remediation hints,
    and an overall A-F security score.

    Supports three config detection strategies:
    1. Local filesystem (native install)
    2. Docker container (reads config via docker exec/cp)
    3. Live gateway API (works for any deployment, including Hostinger/VPS Docker)
    """
    checks = []
    is_docker = False

    # --- Locate openclaw.json config ---
    config_data = None
    config_path = None

    # Strategy 1: Local filesystem
    for cf in [
        os.path.expanduser("~/.openclaw/openclaw.json"),
        os.path.expanduser("~/.clawdbot/openclaw.json"),
        os.path.expanduser("~/.clawdbot/clawdbot.json"),
    ]:
        try:
            with open(cf) as f:
                config_data = json.load(f)
                config_path = cf
                break
        except Exception:
            continue

    # Strategy 2: Docker container (if not found locally)
    if config_data is None:
        try:
            import subprocess as _sp

            # Find OpenClaw containers
            out = _sp.run(
                ["docker", "ps", "--format", "{{.ID}}\t{{.Names}}\t{{.Image}}"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if out.returncode == 0:
                for line in out.stdout.strip().splitlines():
                    parts = line.split("\t")
                    if len(parts) < 3:
                        continue
                    cid, name, image = parts[0], parts[1], parts[2]
                    if not any(
                        k in (name + image).lower()
                        for k in ["openclaw", "clawd", "claw"]
                    ):
                        continue
                    # Try to read config from inside container
                    for container_path in [
                        "/root/.openclaw/openclaw.json",
                        "/home/node/.openclaw/openclaw.json",
                        "/data/openclaw.json",
                        "/app/openclaw.json",
                    ]:
                        try:
                            cat_out = _sp.run(
                                ["docker", "exec", cid, "cat", container_path],
                                capture_output=True,
                                text=True,
                                timeout=8,
                            )
                            if cat_out.returncode == 0 and cat_out.stdout.strip():
                                config_data = json.loads(cat_out.stdout)
                                config_path = f"docker:{cid[:12]}:{container_path}"
                                is_docker = True
                                break
                        except Exception:
                            continue
                    if config_data:
                        break
        except (FileNotFoundError, Exception):
            pass  # Docker not available

    # Strategy 3: Live gateway API (works for any deployment including remote Docker)
    if config_data is None:
        try:
            import dashboard as _d  # late import — gateway config is runtime state

            gw_cfg = _d._load_gw_config()
            gw_url = gw_cfg.get("url", _d.GATEWAY_URL)
            gw_token = gw_cfg.get("token", _d.GATEWAY_TOKEN)
            if gw_url and gw_token:
                import urllib.request

                req = urllib.request.Request(
                    f"{gw_url}/api/config",
                    headers={
                        "Authorization": f"Bearer {gw_token}",
                        "Accept": "application/json",
                    },
                )
                with urllib.request.urlopen(req, timeout=8) as resp:
                    if resp.status == 200:
                        config_data = json.loads(resp.read().decode())
                        config_path = f"gateway:{gw_url}"
                        # Check if gateway reports Docker environment
                        runtime = config_data.get("runtime", {})
                        if runtime.get("container") or os.path.exists("/.dockerenv"):
                            is_docker = True
        except Exception:
            pass

    if config_data is None:
        return {
            "runtime": "openclaw",
            "status": "ok",
            "score": "U",
            "score_label": "Unknown",
            "score_color": "#64748b",
            "checks": [
                {
                    "id": "config_found",
                    "label": "Configuration file",
                    "status": "fail",
                    "detail": "No openclaw.json found (checked local files, Docker containers, and gateway API)",
                    "remediation": "Ensure OpenClaw is installed and configured. For Docker: verify the container is running. For remote: configure GATEWAY_URL and GATEWAY_TOKEN.",
                    "severity": "critical",
                    "weight": 20,
                }
            ],
            "passed": 0,
            "failed": 1,
            "warnings": 0,
            "total": 1,
        }

    # Config found — add pass check with source info
    source_label = (
        "local file"
        if not config_path.startswith(("docker:", "gateway:"))
        else (
            "Docker container" if config_path.startswith("docker:") else "gateway API"
        )
    )
    checks.append(
        {
            "id": "config_found",
            "label": "Configuration file",
            "status": "pass",
            "detail": f"Config loaded from {source_label} ({config_path})",
            "remediation": None,
            "severity": "critical",
            "weight": 20,
        }
    )

    # Docker-specific checks
    if is_docker:
        checks.append(
            {
                "id": "docker_isolation",
                "label": "Container isolation",
                "status": "pass",
                "detail": "OpenClaw is running inside a Docker container (network/filesystem isolation).",
                "remediation": None,
                "severity": "high",
                "weight": 5,
            }
        )

    gateway = config_data.get("gateway", {})
    plugins = config_data.get("plugins", {})

    # Check 1: Gateway auth token configured
    auth_token = (
        gateway.get("auth", {}).get("token")
        or gateway.get("authToken")
        or os.environ.get("OPENCLAW_AUTH_TOKEN")
    )
    if auth_token and len(str(auth_token)) >= 8:
        checks.append(
            {
                "id": "auth_enabled",
                "label": "Gateway authentication",
                "status": "pass",
                "detail": "Auth token is configured (length: {})".format(
                    len(str(auth_token))
                ),
                "remediation": None,
                "severity": "critical",
                "weight": 25,
            }
        )
    else:
        checks.append(
            {
                "id": "auth_enabled",
                "label": "Gateway authentication",
                "status": "fail",
                "detail": "No auth token configured. Anyone on the network can control your agent.",
                "remediation": "Set gateway.auth.token in openclaw.json to a strong random string (32+ chars).",
                "severity": "critical",
                "weight": 25,
            }
        )

    # Check 2: Auth token strength (not default/weak)
    weak_tokens = {
        "test",
        "password",
        "12345678",
        "changeme",
        "openclaw",
        "clawdbot",
        "default",
        "admin",
    }
    if auth_token:
        token_str = str(auth_token).lower()
        if token_str in weak_tokens or len(token_str) < 16:
            checks.append(
                {
                    "id": "auth_strength",
                    "label": "Auth token strength",
                    "status": "warn",
                    "detail": "Token is too short or uses a common/default value.",
                    "remediation": "Use a cryptographically random token: openssl rand -hex 32",
                    "severity": "high",
                    "weight": 15,
                }
            )
        else:
            checks.append(
                {
                    "id": "auth_strength",
                    "label": "Auth token strength",
                    "status": "pass",
                    "detail": "Token appears strong ({} chars)".format(len(token_str)),
                    "remediation": None,
                    "severity": "high",
                    "weight": 15,
                }
            )

    # Check 3: Gateway bind address (should be localhost, not 0.0.0.0)
    # In Docker, binding to 0.0.0.0 is expected (Docker manages port exposure)
    bind_host = gateway.get("host") or gateway.get("bind") or "127.0.0.1"
    if bind_host in ("0.0.0.0", "::") and is_docker:
        checks.append(
            {
                "id": "bind_address",
                "label": "Gateway bind address",
                "status": "pass",
                "detail": "Gateway binds to {} inside Docker container (Docker manages network exposure via port mapping).".format(
                    bind_host
                ),
                "remediation": None,
                "severity": "critical",
                "weight": 20,
            }
        )
    elif bind_host in ("0.0.0.0", "::"):
        checks.append(
            {
                "id": "bind_address",
                "label": "Gateway bind address",
                "status": "fail",
                "detail": "Gateway binds to {} (all interfaces). Exposed to the network.".format(
                    bind_host
                ),
                "remediation": 'Set gateway.host to "127.0.0.1" unless you need remote access. Use a reverse proxy with TLS for remote.',
                "severity": "critical",
                "weight": 20,
            }
        )
    else:
        checks.append(
            {
                "id": "bind_address",
                "label": "Gateway bind address",
                "status": "pass",
                "detail": "Gateway binds to {} (local only)".format(bind_host),
                "remediation": None,
                "severity": "critical",
                "weight": 20,
            }
        )

    # Check 4: Exec tool permissions
    tools_config = config_data.get("tools", {})
    exec_policy = tools_config.get("exec", {})
    exec_security = exec_policy.get("security") or exec_policy.get("mode") or "full"
    if exec_security == "full":
        checks.append(
            {
                "id": "exec_permissions",
                "label": "Exec tool permissions",
                "status": "warn",
                "detail": 'Exec security is "full" (unrestricted shell access).',
                "remediation": 'Consider "allowlist" mode with specific commands, or "deny" for high-risk environments.',
                "severity": "high",
                "weight": 10,
            }
        )
    elif exec_security == "deny":
        checks.append(
            {
                "id": "exec_permissions",
                "label": "Exec tool permissions",
                "status": "pass",
                "detail": "Exec tool is disabled (deny mode).",
                "remediation": None,
                "severity": "high",
                "weight": 10,
            }
        )
    else:
        checks.append(
            {
                "id": "exec_permissions",
                "label": "Exec tool permissions",
                "status": "pass",
                "detail": "Exec security mode: {}".format(exec_security),
                "remediation": None,
                "severity": "high",
                "weight": 10,
            }
        )

    # Check 5: TLS / HTTPS for gateway
    gw_tls = gateway.get("tls", {})
    has_tls = bool(gw_tls.get("cert") or gw_tls.get("key") or gw_tls.get("enabled"))
    if has_tls:
        checks.append(
            {
                "id": "tls_enabled",
                "label": "TLS encryption",
                "status": "pass",
                "detail": "TLS is configured for the gateway.",
                "remediation": None,
                "severity": "high",
                "weight": 10,
            }
        )
    elif bind_host in ("0.0.0.0", "::") and is_docker:
        checks.append(
            {
                "id": "tls_enabled",
                "label": "TLS encryption",
                "status": "warn",
                "detail": "No TLS configured on gateway (Docker). TLS is typically handled by the hosting provider or reverse proxy.",
                "remediation": "Verify your hosting provider (Hostinger, etc.) or reverse proxy terminates TLS before reaching the container.",
                "severity": "high",
                "weight": 10,
            }
        )
    elif bind_host in ("0.0.0.0", "::"):
        checks.append(
            {
                "id": "tls_enabled",
                "label": "TLS encryption",
                "status": "fail",
                "detail": "No TLS configured and gateway is network-exposed. Traffic is unencrypted.",
                "remediation": "Configure gateway.tls.cert and gateway.tls.key, or use a reverse proxy (nginx/caddy) with TLS.",
                "severity": "high",
                "weight": 10,
            }
        )
    else:
        checks.append(
            {
                "id": "tls_enabled",
                "label": "TLS encryption",
                "status": "pass",
                "detail": "TLS not needed (gateway is localhost only).",
                "remediation": None,
                "severity": "high",
                "weight": 10,
            }
        )

    # Check 6: Plugin/channel security (telegram/discord tokens not in plaintext env)
    plugin_entries = plugins.get("entries", {})
    exposed_secrets = []
    for pname, pconf in plugin_entries.items():
        if isinstance(pconf, dict):
            for key in ["token", "apiKey", "api_key", "secret", "webhook_secret"]:
                val = pconf.get(key)
                if (
                    val
                    and isinstance(val, str)
                    and not val.startswith("$")
                    and not val.startswith("env:")
                ):
                    exposed_secrets.append("{}.{}".format(pname, key))
    if exposed_secrets:
        checks.append(
            {
                "id": "secrets_in_config",
                "label": "Secrets in config file",
                "status": "warn",
                "detail": "{} secret(s) stored as plaintext in config: {}".format(
                    len(exposed_secrets), ", ".join(exposed_secrets[:3])
                ),
                "remediation": 'Use environment variables instead. E.g., set TELEGRAM_TOKEN env var and reference as "$TELEGRAM_TOKEN" in config.',
                "severity": "medium",
                "weight": 5,
            }
        )
    else:
        checks.append(
            {
                "id": "secrets_in_config",
                "label": "Secrets in config file",
                "status": "pass",
                "detail": "No plaintext secrets detected in plugin config.",
                "remediation": None,
                "severity": "medium",
                "weight": 5,
            }
        )

    # Check 7: Workspace permissions (AGENTS.md, SOUL.md not world-readable)
    oc_home = os.path.expanduser("~/.openclaw")
    if os.name == "nt":
        # POSIX mode bits are meaningless on Windows: st_mode reports 0o777
        # for every normal directory, so the world-readable branch below
        # would warn (and dock the score) on every Windows install with a
        # chmod remediation that cannot be run. Access there is governed by
        # NTFS ACLs, and the user-profile dir is owner-scoped by default.
        if os.path.isdir(oc_home):
            checks.append(
                {
                    "id": "workspace_perms",
                    "label": "Workspace permissions",
                    "status": "pass",
                    "detail": "Access to the OpenClaw home directory is governed by Windows ACLs (user-profile scoped).",
                    "remediation": None,
                    "severity": "medium",
                    "weight": 5,
                }
            )
    elif os.path.isdir(oc_home):
        try:
            mode = oct(os.stat(oc_home).st_mode)[-3:]
            if mode[-1] != "0":  # world-readable
                checks.append(
                    {
                        "id": "workspace_perms",
                        "label": "Workspace permissions",
                        "status": "warn",
                        "detail": "OpenClaw home directory is world-readable (mode: {})".format(
                            mode
                        ),
                        "remediation": "Run: chmod 700 ~/.openclaw",
                        "severity": "medium",
                        "weight": 5,
                    }
                )
            else:
                checks.append(
                    {
                        "id": "workspace_perms",
                        "label": "Workspace permissions",
                        "status": "pass",
                        "detail": "Workspace directory permissions are restrictive (mode: {})".format(
                            mode
                        ),
                        "remediation": None,
                        "severity": "medium",
                        "weight": 5,
                    }
                )
        except Exception:
            checks.append(
                {
                    "id": "workspace_perms",
                    "label": "Workspace permissions",
                    "status": "warn",
                    "detail": "Could not check workspace permissions.",
                    "remediation": "Run: chmod 700 ~/.openclaw",
                    "severity": "medium",
                    "weight": 5,
                }
            )
    else:
        checks.append(
            {
                "id": "workspace_perms",
                "label": "Workspace permissions",
                "status": "pass",
                "detail": "Default workspace directory not found (custom location or containerized).",
                "remediation": None,
                "severity": "medium",
                "weight": 5,
            }
        )

    # Check 8: Node/remote access configuration
    nodes_config = config_data.get("nodes", {})
    auto_approve = nodes_config.get("autoApprove", False)
    if auto_approve:
        checks.append(
            {
                "id": "node_auto_approve",
                "label": "Node auto-approve",
                "status": "warn",
                "detail": "Nodes are auto-approved without manual review.",
                "remediation": "Set nodes.autoApprove to false so you review each device before granting access.",
                "severity": "medium",
                "weight": 5,
            }
        )
    else:
        checks.append(
            {
                "id": "node_auto_approve",
                "label": "Node auto-approve",
                "status": "pass",
                "detail": "Node pairing requires manual approval.",
                "remediation": None,
                "severity": "medium",
                "weight": 5,
            }
        )

    # Check 9: Elevated exec permissions
    elevated = tools_config.get("elevated", {}) or exec_policy.get("elevated", {})
    elevated_enabled = (
        elevated.get("enabled", False) if isinstance(elevated, dict) else bool(elevated)
    )
    if elevated_enabled:
        checks.append(
            {
                "id": "elevated_exec",
                "label": "Elevated (sudo) exec",
                "status": "warn",
                "detail": "Elevated/sudo exec is enabled. Agent can run commands as root.",
                "remediation": "Disable unless absolutely necessary. Use specific sudoers rules instead of blanket elevation.",
                "severity": "high",
                "weight": 10,
            }
        )
    else:
        checks.append(
            {
                "id": "elevated_exec",
                "label": "Elevated (sudo) exec",
                "status": "pass",
                "detail": "Elevated exec is disabled.",
                "remediation": None,
                "severity": "high",
                "weight": 10,
            }
        )

    return _score_envelope(
        checks,
        runtime="openclaw",
        config_path=config_path,
        extra={"is_docker": is_docker},
    )


# ═══════════════════════════════════════════════════════════════════════════
# Claude Code provider — real checks against settings.json /
# settings.local.json under $CLAUDE_CONFIG_DIR (default ~/.claude).
# ═══════════════════════════════════════════════════════════════════════════


def _claude_config_dir() -> str:
    return os.environ.get("CLAUDE_CONFIG_DIR") or os.path.expanduser("~/.claude")


# Allow-rules that grant effectively unrestricted execution.
_CC_DANGEROUS_ALLOW = {"*", "bash", "bash(*)", "bash(*:*)", "bash(::*)"}


def claude_code_posture() -> dict:
    """Posture checks for Claude Code's permission/settings model."""
    cfg_dir = _claude_config_dir()
    files: list[tuple[str, dict]] = []
    parse_errors: list[str] = []
    for fname in ("settings.json", "settings.local.json"):
        fpath = os.path.join(cfg_dir, fname)
        if not os.path.isfile(fpath):
            continue
        try:
            with open(fpath, encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict):
                files.append((fpath, data))
            else:
                parse_errors.append(f"{fname}: not a JSON object")
        except (OSError, ValueError) as exc:
            parse_errors.append(f"{fname}: {exc}")

    # (a) config file found
    if not files:
        detail = (
            "No settings.json / settings.local.json under {} ".format(cfg_dir)
            + ("(parse errors: " + "; ".join(parse_errors) + ")" if parse_errors
               else "(checked CLAUDE_CONFIG_DIR and ~/.claude)")
        )
        return {
            "runtime": "claude_code",
            "status": "ok",
            "score": "U",
            "score_label": "Unknown",
            "score_color": "#64748b",
            "checks": [
                _check(
                    "config_found",
                    "Settings file",
                    "fail",
                    detail,
                    "Run Claude Code once (it creates ~/.claude/settings.json), "
                    "or point CLAUDE_CONFIG_DIR at the config directory.",
                    "critical",
                    20,
                )
            ],
            "passed": 0,
            "failed": 1,
            "warnings": 0,
            "total": 1,
            "config_path": None,
        }

    checks: list[dict] = []
    config_path = ", ".join(p for p, _ in files)
    checks.append(
        _check(
            "config_found",
            "Settings file",
            "pass",
            "Loaded {} ({})".format(
                " + ".join(os.path.basename(p) for p, _ in files), cfg_dir
            ),
            None,
            "critical",
            20,
        )
    )

    # Union of permissions across both files (local overlays global).
    allow: list[str] = []
    deny: list[str] = []
    default_mode = None
    for _, data in files:
        perms = data.get("permissions")
        if isinstance(perms, dict):
            if isinstance(perms.get("allow"), list):
                allow.extend(str(r) for r in perms["allow"])
            if isinstance(perms.get("deny"), list):
                deny.extend(str(r) for r in perms["deny"])
            if perms.get("defaultMode"):
                default_mode = str(perms["defaultMode"])

    # (b) permissions block present
    if not allow and not deny:
        checks.append(
            _check(
                "permissions_present",
                "Permission rules",
                "warn",
                "No allow or deny permission rules configured — every tool "
                "call falls back to interactive prompting defaults.",
                'Add a "permissions" block with explicit allow/deny rules to '
                "settings.json.",
                "high",
                20,
            )
        )
    else:
        checks.append(
            _check(
                "permissions_present",
                "Permission rules",
                "pass",
                "{} allow rule(s), {} deny rule(s) configured.".format(
                    len(allow), len(deny)
                ),
                None,
                "high",
                20,
            )
        )

    # (c) deny list present for sensitive tools — informational
    if deny:
        checks.append(
            _check(
                "deny_rules",
                "Deny rules",
                "pass",
                "{} deny rule(s), e.g. {}".format(len(deny), ", ".join(deny[:3])),
                None,
                "medium",
                10,
            )
        )
    else:
        checks.append(
            _check(
                "deny_rules",
                "Deny rules",
                "warn",
                "No deny rules for sensitive tools/paths.",
                'Consider denying secrets and destructive commands, e.g. '
                '"Read(.env)", "Read(**/*.pem)", "Bash(rm -rf*)".',
                "medium",
                10,
            )
        )

    # (d) hooks configured — informational pass either way
    hook_events: list[str] = []
    for _, data in files:
        hooks = data.get("hooks")
        if isinstance(hooks, dict):
            hook_events.extend(k for k in hooks.keys() if k not in hook_events)
    if hook_events:
        checks.append(
            _check(
                "hooks_configured",
                "Hooks",
                "pass",
                "Hooks configured for: {}".format(", ".join(hook_events)),
                None,
                "low",
                5,
            )
        )
    else:
        # Was "pass" — which meant this check passed on EVERY code path and
        # could not fail, quietly donating its whole weight to the score. A
        # posture check that cannot fail is padding, not a measurement.
        checks.append(
            _check(
                "hooks_configured",
                "Hooks",
                "warn",
                "No hooks configured, so nothing inspects a tool call before "
                "it runs.",
                "Add a PreToolUse hook, or run `clawmetry secure enable` to "
                "install monitor-only agent-EDR hooks.",
                "low",
                5,
            )
        )

    # (e) enableAllProjectMcpServers → auto-trusts project MCP servers
    auto_mcp = any(
        data.get("enableAllProjectMcpServers") is True for _, data in files
    )
    if auto_mcp:
        checks.append(
            _check(
                "mcp_auto_trust",
                "Project MCP auto-trust",
                "warn",
                "enableAllProjectMcpServers is true — every MCP server in a "
                "project's .mcp.json is trusted automatically.",
                "Set enableAllProjectMcpServers to false and approve project "
                "MCP servers individually.",
                "high",
                15,
            )
        )
    else:
        checks.append(
            _check(
                "mcp_auto_trust",
                "Project MCP auto-trust",
                "pass",
                "Project MCP servers require explicit approval.",
                None,
                "high",
                15,
            )
        )

    # (f) apiKeyHelper — informational, weight 0. Both states are legitimate
    # (a custom helper and default credential handling are each fine), so this
    # can never fail. It stays visible for context but must not contribute
    # weight: a check that always passes inflates the grade for free.
    helper = next(
        (data.get("apiKeyHelper") for _, data in files if data.get("apiKeyHelper")),
        None,
    )
    if helper:
        checks.append(
            _check(
                "api_key_helper",
                "API key helper",
                "pass",
                "apiKeyHelper is set ({}) — credentials come from a custom "
                "script, keep it non-world-readable.".format(helper),
                None,
                "low",
                0,
            )
        )
    else:
        checks.append(
            _check(
                "api_key_helper",
                "API key helper",
                "pass",
                "No apiKeyHelper configured (default credential handling).",
                None,
                "low",
                0,
            )
        )

    # (g) dangerous wildcard allow rules / bypass mode
    dangerous = sorted(
        {r for r in allow if r.strip().lower() in _CC_DANGEROUS_ALLOW}
    )
    if default_mode == "bypassPermissions":
        dangerous.append('defaultMode: "bypassPermissions"')
    if dangerous:
        checks.append(
            _check(
                "wildcard_allow",
                "Dangerous permission grants",
                "warn",
                "Unrestricted grant(s) found: {}".format(", ".join(dangerous)),
                "Replace blanket grants with scoped rules, e.g. "
                '"Bash(npm run test:*)" instead of "Bash(*)".',
                "high",
                15,
            )
        )
    else:
        checks.append(
            _check(
                "wildcard_allow",
                "Dangerous permission grants",
                "pass",
                "No unrestricted wildcard allow rules detected.",
                None,
                "high",
                15,
            )
        )

    return _score_envelope(checks, runtime="claude_code", config_path=config_path)


# ═══════════════════════════════════════════════════════════════════════════
# Codex provider — approval_policy + sandbox_mode from $CODEX_HOME/config.toml.
# Registered from OSS (pure file read); no TOML dependency needed for these
# two flat top-level keys, so we regex-scan (python_requires >= 3.8 rules
# out tomllib).
# ═══════════════════════════════════════════════════════════════════════════

_TOML_KEY_RE = r'^\s*{key}\s*=\s*"([^"]+)"'


def _codex_home() -> str:
    return os.environ.get("CODEX_HOME") or os.path.expanduser("~/.codex")


def codex_posture() -> dict:
    """Posture from Codex CLI's config.toml (approval policy + sandbox)."""
    config_path = os.path.join(_codex_home(), "config.toml")
    if not os.path.isfile(config_path):
        env = _not_available("codex")
        env["detail"] = (
            "No config.toml under {} — Codex is running on its built-in "
            "defaults; nothing to scan.".format(_codex_home())
        )
        return env
    try:
        with open(config_path, encoding="utf-8") as f:
            text = f.read()
    except OSError as exc:
        env = _not_available("codex")
        env["detail"] = f"config.toml unreadable: {exc}"
        return env

    def _top_level_key(key: str) -> str | None:
        # Only scan the top-level section (before the first [table]).
        top = text.split("\n[", 1)[0]
        m = re.search(_TOML_KEY_RE.format(key=key), top, re.MULTILINE)
        return m.group(1) if m else None

    approval = _top_level_key("approval_policy")
    sandbox = _top_level_key("sandbox_mode")

    checks = [
        _check(
            "config_found",
            "Configuration file",
            "pass",
            f"Config loaded from local file ({config_path})",
            None,
            "critical",
            20,
        )
    ]

    if approval == "never":
        checks.append(
            _check(
                "approval_policy",
                "Approval policy",
                "warn",
                'approval_policy is "never" — commands run without asking.',
                'Use "untrusted" or "on-request" so escalations need approval.',
                "high",
                20,
            )
        )
    elif approval:
        checks.append(
            _check(
                "approval_policy",
                "Approval policy",
                "pass",
                f'approval_policy is "{approval}".',
                None,
                "high",
                20,
            )
        )
    else:
        checks.append(
            _check(
                "approval_policy",
                "Approval policy",
                "warn",
                "approval_policy is not set, so Codex falls back to its built-in "
                "default, which varies by version. We can only report what the "
                "config actually declares.",
                'Set approval_policy explicitly (e.g. "on-request") so the '
                "behaviour is pinned rather than inherited.",
                "high",
                20,
            )
        )

    if sandbox == "danger-full-access":
        checks.append(
            _check(
                "sandbox_mode",
                "Sandbox mode",
                "fail",
                'sandbox_mode is "danger-full-access" — no filesystem/network '
                "sandbox at all.",
                'Use "workspace-write" (or "read-only") unless full access is '
                "genuinely required.",
                "critical",
                25,
            )
        )
    elif sandbox:
        checks.append(
            _check(
                "sandbox_mode",
                "Sandbox mode",
                "pass",
                f'sandbox_mode is "{sandbox}".',
                None,
                "critical",
                25,
            )
        )
    else:
        checks.append(
            _check(
                "sandbox_mode",
                "Sandbox mode",
                "warn",
                "sandbox_mode is not set, so Codex falls back to its built-in "
                "default, which varies by version. An empty config should not "
                "read as a verified sandbox.",
                'Set sandbox_mode explicitly (e.g. "workspace-write") so the '
                "sandbox is pinned rather than inherited.",
                "critical",
                25,
            )
        )

    return _score_envelope(checks, runtime="codex", config_path=config_path)


# ═══════════════════════════════════════════════════════════════════════════
# Cursor provider.
#
# GRADING DISCIPLINE (read before adding a check here): Cursor is CLOSED
# SOURCE. We cannot read the code that consumes any of its settings, so a
# setting's presence never proves the behaviour is enforced. Checks split
# into two grades:
#
#   FAIL-grade  — a filesystem FACT, where "is it honored?" does not arise:
#                 a file exists or not, a mode bit, a literal byte in a file.
#   WARN-grade  — documented or observed-on-disk only. Never fail these.
#
# A posture check that fails on a clean install is worse than no check at
# all: it teaches the operator to ignore the grade. (Near miss, 2026-08-18:
# a proposed Cline check keyed on ``executeAllCommands``, a field the code
# never reads, which would have failed every clean install.)
# ═══════════════════════════════════════════════════════════════════════════

# Unicode tag block + zero-width/bidi characters. Tag chars (U+E0000-U+E007F)
# are invisible in every editor and are the standard carrier for instructions
# smuggled into an agent rules file.
_INVISIBLE_RANGES = (
    (0xE0000, 0xE007F),  # Unicode tag characters
    (0x200B, 0x200F),    # zero-width space/non-joiner/joiner, LRM/RLM
    (0x202A, 0x202E),    # bidi embedding/override
    (0x2060, 0x2064),    # word joiner, invisible operators
)

_SECRET_KEY_HINT = re.compile(
    r"(token|api[_-]?key|secret|password|passwd|credential|authorization|bearer)",
    re.I,
)


def _cursor_home() -> str:
    return os.environ.get("CURSOR_HOME") or os.path.expanduser("~/.cursor")


def _read_json(path: str):
    try:
        with open(path, encoding="utf-8") as fh:
            text = fh.read()
    except OSError:
        return None
    # Cursor writes JSONC (the CLI's own config.json ships with // comments).
    lines = [ln for ln in text.splitlines() if not ln.lstrip().startswith("//")]
    try:
        return json.loads("\n".join(lines))
    except (ValueError, TypeError):
        return None


def _invisible_hits(text: str) -> int:
    n = 0
    for ch in text:
        cp = ord(ch)
        for lo, hi in _INVISIBLE_RANGES:
            if lo <= cp <= hi:
                n += 1
                break
    return n


def _looks_like_literal_secret(value) -> bool:
    """True when a config value carries a secret inline rather than by
    reference. ``$FOO``/``${FOO}``/``env:FOO`` are references, not secrets."""
    if not isinstance(value, str) or len(value.strip()) < 8:
        return False
    v = value.strip()
    if v.startswith("$") or v.startswith("env:") or v.startswith("${"):
        return False
    return True


def cursor_posture() -> dict:
    """Security posture for Cursor.

    Leans on filesystem facts (hook wiring, secrets written literally into
    MCP config, invisible Unicode in rules files) because those hold true
    whatever the closed-source client does with its settings.
    """
    home = _cursor_home()
    cli_cfg = _read_json(os.path.join(home, "cli-config.json"))
    hooks = _read_json(os.path.join(home, "hooks.json"))
    mcp = _read_json(os.path.join(home, "mcp.json"))
    sandbox = _read_json(os.path.join(home, "sandbox.json"))

    found = [
        name for name, data in (
            ("cli-config.json", cli_cfg), ("hooks.json", hooks),
            ("mcp.json", mcp), ("sandbox.json", sandbox),
        ) if data is not None
    ]
    if not os.path.isdir(home):
        return _not_available("cursor")

    checks: list[dict] = []
    checks.append(_check(
        "config_found", "Configuration",
        "pass" if found else "warn",
        "Read {} from {}".format(", ".join(found), home) if found
        else "Cursor directory exists at {} but no readable config files.".format(home),
        None if found else "Run Cursor once so it writes its configuration.",
        "low", 20,
    ))

    # (a) Hook wiring. FAIL-grade: the file either declares a pre-execution
    # hook or it does not. Nothing about enforcement is assumed.
    hook_map = (hooks or {}).get("hooks") if isinstance(hooks, dict) else None
    hook_names = sorted(hook_map) if isinstance(hook_map, dict) else []
    pre_exec = [h for h in hook_names if h in ("beforeShellExecution", "beforeMCPExecution")]
    if pre_exec:
        checks.append(_check(
            "pre_exec_hooks", "Pre-execution hooks", "pass",
            "Hooks inspect actions before they run: {}.".format(", ".join(pre_exec)),
            None, "medium", 15,
        ))
    else:
        checks.append(_check(
            "pre_exec_hooks", "Pre-execution hooks", "warn",
            "No beforeShellExecution or beforeMCPExecution hook, so nothing "
            "inspects a shell command or MCP call before it runs."
            + ("" if hooks is None else " (hooks.json is present but declares none.)"),
            "Add a beforeShellExecution hook, or run `clawmetry secure enable` "
            "to install monitor-only agent-EDR hooks.",
            "medium", 15,
        ))

    # (b) Secrets written literally into MCP server config. FAIL-grade: the
    # bytes are either in the file or they are not.
    literal_secrets = []
    servers = (mcp or {}).get("mcpServers") if isinstance(mcp, dict) else None
    if isinstance(servers, dict):
        for sname, sconf in servers.items():
            if not isinstance(sconf, dict):
                continue
            for block in ("env", "headers"):
                blk = sconf.get(block)
                if not isinstance(blk, dict):
                    continue
                for k, v in blk.items():
                    if _SECRET_KEY_HINT.search(str(k)) and _looks_like_literal_secret(v):
                        literal_secrets.append("{}.{}.{}".format(sname, block, k))
    if literal_secrets:
        checks.append(_check(
            "mcp_secrets_inline", "Secrets in MCP config", "fail",
            "Credential values are written directly into mcp.json: {}.".format(
                ", ".join(literal_secrets[:5])),
            "Replace the literal values with environment references such as "
            "\"$MY_TOKEN\" so the secret is not stored in a config file.",
            "critical", 20,
        ))
    else:
        checks.append(_check(
            "mcp_secrets_inline", "Secrets in MCP config", "pass",
            "No credential values written directly into mcp.json."
            if servers else "No MCP servers configured.",
            None, "critical", 20,
        ))

    # (c) Invisible Unicode in rules files. FAIL-grade byte-level fact. One
    # occurrence is enough: these characters have no legitimate use in a
    # human-authored rules file.
    rule_files = []
    rules_dir = os.path.join(home, "rules")
    if os.path.isdir(rules_dir):
        try:
            rule_files += [
                os.path.join(rules_dir, f) for f in sorted(os.listdir(rules_dir))
                if f.endswith((".mdc", ".md"))
            ]
        except OSError:
            pass
    legacy = os.path.expanduser("~/.cursorrules")
    if os.path.isfile(legacy):
        rule_files.append(legacy)
    tainted = []
    for rf in rule_files[:200]:
        try:
            with open(rf, encoding="utf-8", errors="replace") as fh:
                hits = _invisible_hits(fh.read())
        except OSError:
            continue
        if hits:
            tainted.append("{} ({} char{})".format(
                os.path.basename(rf), hits, "" if hits == 1 else "s"))
    if tainted:
        checks.append(_check(
            "rules_invisible_unicode", "Hidden text in rules", "fail",
            "Invisible characters found in {}. Text you cannot see in an "
            "editor is instructing the agent.".format(", ".join(tainted[:5])),
            "Open the file, strip the invisible characters, and confirm the "
            "visible text is all the agent is being told.",
            "critical", 20,
        ))
    else:
        checks.append(_check(
            "rules_invisible_unicode", "Hidden text in rules", "pass",
            "No invisible characters in {} rules file(s).".format(len(rule_files))
            if rule_files else "No rules files found.",
            None, "critical", 20,
        ))

    # (d) CLI permission grants.
    perms = (cli_cfg or {}).get("permissions") if isinstance(cli_cfg, dict) else None
    allow = [str(r) for r in (perms or {}).get("allow", []) if isinstance(perms, dict)]
    deny = [str(r) for r in (perms or {}).get("deny", []) if isinstance(perms, dict)]
    wild = sorted({r for r in allow if r.strip().lower() in _CC_DANGEROUS_ALLOW
                   or r.strip() in ("Shell(*)", "*")})
    if wild:
        checks.append(_check(
            "cli_wildcard_allow", "Blanket command grants", "warn",
            "Unrestricted grant(s) in cli-config.json: {}.".format(", ".join(wild)),
            "Replace blanket grants with scoped rules, e.g. \"Shell(git status)\".",
            "high", 15,
        ))
    elif not deny:
        checks.append(_check(
            "cli_wildcard_allow", "Blanket command grants", "warn",
            "{} allow rule(s) and no deny rules in cli-config.json.".format(len(allow)),
            "Add deny rules for sensitive paths and destructive commands.",
            "high", 15,
        ))
    else:
        checks.append(_check(
            "cli_wildcard_allow", "Blanket command grants", "pass",
            "{} allow rule(s), {} deny rule(s), no blanket grants.".format(
                len(allow), len(deny)),
            None, "high", 15,
        ))

    # (e) Sandbox. WARN-grade: documented, but we cannot confirm the closed
    # client applies it, so this never fails.
    stype = (sandbox or {}).get("type") if isinstance(sandbox, dict) else None
    if stype == "insecure_none":
        checks.append(_check(
            "sandbox_mode", "Sandbox", "warn",
            "sandbox.json sets type \"insecure_none\", which the documentation "
            "describes as no sandbox at all.",
            "Choose a sandbox type other than \"insecure_none\".",
            "high", 10,
        ))
    elif stype:
        checks.append(_check(
            "sandbox_mode", "Sandbox", "pass",
            "sandbox.json sets type \"{}\".".format(stype), None, "high", 10,
        ))
    else:
        checks.append(_check(
            "sandbox_mode", "Sandbox", "warn",
            "No sandbox.json, so the sandbox is whatever Cursor defaults to. "
            "An unset value is unmeasured, not proven safe.",
            "Write a sandbox.json with an explicit type so the setting is "
            "pinned rather than inherited.",
            "high", 10,
        ))

    # (f) Honest unknown, weight 0. Cursor's auto-run / Run Mode level has no
    # documented on-disk key: a dump of state.vscdb turned up telemetry flags
    # only. Saying so beats inventing a key, and weight 0 keeps an unmeasured
    # thing out of the grade entirely.
    checks.append(_check(
        "auto_run_level", "Auto-run level", "pass",
        "Cursor does not record its auto-run (Run Mode) level anywhere "
        "ClawMetry can read, so this cannot be verified from disk. Check it "
        "in Cursor's own settings.",
        None, "low", 0,
    ))

    return _score_envelope(checks, runtime="cursor", config_path=home)


# ═══════════════════════════════════════════════════════════════════════════
# GitHub Copilot CLI provider.
#
# Same grading discipline as the Cursor provider above: the CLI ships as a
# closed bundled package, so a grant's presence in the file is a fact but its
# enforcement is not observable. Blanket grants therefore WARN; only the
# indefensible cases (trusting "/" or the whole home directory, an
# allow-everything switch wired into a shell profile) FAIL.
# ═══════════════════════════════════════════════════════════════════════════

_COPILOT_ALLOW_ALL_RE = re.compile(
    r"(COPILOT_ALLOW_ALL\s*=\s*[\"']?(1|true|yes)|copilot\b[^\n|;]*--(yolo|allow-all))",
    re.I,
)


def _copilot_home() -> str:
    return os.environ.get("COPILOT_HOME") or os.path.expanduser("~/.copilot")


def copilot_posture() -> dict:
    """Security posture for GitHub Copilot CLI."""
    home = _copilot_home()
    if not os.path.isdir(home):
        return _not_available("copilot")

    perms = _read_json(os.path.join(home, "permissions-config.json"))
    cfg = _read_json(os.path.join(home, "config.json"))
    settings = _read_json(os.path.join(home, "settings.json"))
    found = [n for n, d in (("permissions-config.json", perms),
                            ("config.json", cfg),
                            ("settings.json", settings)) if d is not None]

    checks: list[dict] = []
    checks.append(_check(
        "config_found", "Configuration",
        "pass" if found else "warn",
        "Read {} from {}".format(", ".join(found), home) if found
        else "Copilot directory exists at {} but no readable config.".format(home),
        None if found else "Run Copilot CLI once so it writes its configuration.",
        "low", 20,
    ))

    home_dir = os.path.expanduser("~")
    locations = (perms or {}).get("locations") if isinstance(perms, dict) else None
    blanket_write = []
    indefensible = []
    relative_grants = []
    if isinstance(locations, dict):
        for loc, conf in locations.items():
            approvals = (conf or {}).get("tool_approvals") if isinstance(conf, dict) else None
            if not isinstance(approvals, list):
                continue
            for ap in approvals:
                if not isinstance(ap, dict):
                    continue
                if ap.get("kind") == "write" and not ap.get("paths"):
                    # A write grant with no path restriction: every file under
                    # this location, for every future session.
                    if str(loc).rstrip("/") in ("", home_dir):
                        indefensible.append(str(loc))
                    else:
                        blanket_write.append(str(loc))
                for pth in (ap.get("paths") or []):
                    if isinstance(pth, str) and not pth.startswith("/"):
                        relative_grants.append("{} -> {}".format(loc, pth))

    if indefensible:
        checks.append(_check(
            "blanket_write_grant", "Standing write access", "fail",
            "An unrestricted write grant covers {}, which is the whole home "
            "directory or the filesystem root.".format(", ".join(indefensible[:3])),
            "Revoke the grant and re-approve writes for a specific project "
            "directory instead.",
            "critical", 25,
        ))
    elif blanket_write:
        checks.append(_check(
            "blanket_write_grant", "Standing write access", "warn",
            "A standing write grant with no path restriction covers {}. Every "
            "future session can write anywhere under it without asking.".format(
                ", ".join(blanket_write[:3])),
            "Remove the {\"kind\": \"write\"} entry so writes are approved per "
            "file, or scope it with an explicit paths list.",
            "high", 25,
        ))
    else:
        checks.append(_check(
            "blanket_write_grant", "Standing write access", "pass",
            "No unrestricted standing write grants."
            if locations else "No stored tool approvals.",
            None, "high", 25,
        ))

    # Documented footgun: a relative path matches by trailing components, so
    # a grant for ".env" matches a file named .env in ANY directory.
    if relative_grants:
        checks.append(_check(
            "relative_path_grants", "Relative path grants", "warn",
            "Grant(s) use a relative path: {}. A relative path matches by "
            "trailing components, so it applies to a file of that name in any "
            "directory.".format(", ".join(relative_grants[:3])),
            "Re-approve using absolute paths.",
            "medium", 10,
        ))
    else:
        checks.append(_check(
            "relative_path_grants", "Relative path grants", "pass",
            "No relative-path grants.", None, "medium", 10,
        ))

    trusted = (cfg or {}).get("trustedFolders") if isinstance(cfg, dict) else None
    trusted = [str(t) for t in trusted] if isinstance(trusted, list) else []
    broad = [t for t in trusted if t.rstrip("/") in ("", home_dir)]
    if broad:
        checks.append(_check(
            "trusted_folders", "Trusted folders", "fail",
            "Trusted folders include {}, which trusts everything below it.".format(
                ", ".join(broad)),
            "Trust individual project directories instead of the home "
            "directory or the filesystem root.",
            "critical", 20,
        ))
    elif trusted:
        checks.append(_check(
            "trusted_folders", "Trusted folders", "pass",
            "{} project folder(s) trusted, none of them broad.".format(len(trusted)),
            None, "high", 20,
        ))
    else:
        checks.append(_check(
            "trusted_folders", "Trusted folders", "pass",
            "No folders trusted yet.", None, "high", 20,
        ))

    # Sandbox. WARN-grade: documented as shipping disabled, enforcement not
    # observable. Copilot's own help text: shell commands run directly on your
    # machine with the same access your user account has.
    sbox = (settings or {}).get("sandbox") if isinstance(settings, dict) else None
    enabled = (sbox or {}).get("enabled") if isinstance(sbox, dict) else None
    if enabled is True:
        checks.append(_check(
            "sandbox_enabled", "Sandbox", "pass",
            "Sandbox is enabled in settings.json.", None, "high", 15,
        ))
    else:
        checks.append(_check(
            "sandbox_enabled", "Sandbox", "warn",
            "Sandbox is not enabled, so shell commands run directly on this "
            "machine with your user account's access.",
            "Set sandbox.enabled to true in Copilot's settings.json.",
            "high", 15,
        ))

    # Allow-everything switch wired into a shell profile. FAIL-grade: this is
    # text in a file, not a behaviour we have to trust the client about.
    rc_hits = []
    for rc in ("~/.zshrc", "~/.bashrc", "~/.bash_profile", "~/.zprofile", "~/.profile"):
        path = os.path.expanduser(rc)
        try:
            with open(path, encoding="utf-8", errors="replace") as fh:
                for line in fh:
                    if line.lstrip().startswith("#"):
                        continue
                    if _COPILOT_ALLOW_ALL_RE.search(line):
                        rc_hits.append(rc)
                        break
        except OSError:
            continue
    if rc_hits:
        checks.append(_check(
            "allow_all_switch", "Approval bypass in shell profile", "fail",
            "An allow-everything switch is set in {}, so approvals are "
            "bypassed for every session started from that shell.".format(
                ", ".join(rc_hits)),
            "Remove the setting and approve actions per session instead.",
            "critical", 10,
        ))
    else:
        checks.append(_check(
            "allow_all_switch", "Approval bypass in shell profile", "pass",
            "No allow-everything switch in your shell profiles.",
            None, "critical", 10,
        ))

    return _score_envelope(checks, runtime="copilot", config_path=home)


# ── built-in provider registration ─────────────────────────────────────────

register_posture_provider("openclaw", openclaw_posture)
register_posture_provider("claude_code", claude_code_posture)
register_posture_provider("codex", codex_posture)
register_posture_provider("cursor", cursor_posture)
register_posture_provider("copilot", copilot_posture)
