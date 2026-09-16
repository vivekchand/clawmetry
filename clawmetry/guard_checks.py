"""Guard's operator-facing catalogue and durable, node-wide preferences."""
from __future__ import annotations

import logging
import os
import time

log = logging.getLogger(__name__)
PREFIX = "guard.check."
LAST_PASS_KEY = "guard.last_pass_ms"
FAMILIES = (
    ("progress", "Run progress", "Is the agent getting the job done?"),
    ("access", "Access & changes", "What is it reaching or changing?"),
    ("silent", "Silent failures", "Has work stopped without an answer?"),
    ("injection", "Prompt injection", "Is content trying to give instructions?"),
    ("workspace", "Workspace risks", "What could run from this workspace?"),
    ("fleet", "Across sessions", "Are independent agents acting in step?"),
)
# Copy describes the declared registry; it does not define another detector set.
DESCRIPTIONS = {
    "stuck_loop": ("progress", "Stuck loops", "The same call repeats, or a short sequence cycles again and again."),
    "no_progress": ("progress", "No progress", "A run keeps calling tools without a file change or completion."),
    "repeated_tool_failure": ("progress", "Repeated tool failures", "The same tool keeps returning errors."),
    "action_discrepancy": ("progress", "Continuing after failure", "A failed command is followed by more work without a retry or acknowledgment."),
    "file_blast_radius": ("access", "Wide file changes", "Changes reach unusually many files or include destructive commands."),
    "credential_access": ("access", "Credential access", "Tool arguments reference credentials, keys or sensitive paths."),
    "network_egress": ("access", "Unusual network destinations", "An agent sends data to an unfamiliar destination."),
    "privilege_change": ("access", "Privilege changes", "Commands try to change permissions, identities or access controls."),
    "rate_limited": ("silent", "Provider rate limits", "A provider refuses work because of a usage or rate limit."),
    "blocked_on_user": ("silent", "Waiting for you", "A question or approval request is followed by an idle stretch."),
    "crashed": ("silent", "Repeated restarts", "The same run starts again repeatedly in a short window."),
    "prompt_injection": ("injection", "Prompt injection", "Text an agent reads matches known attempts to redirect its instructions."),
    "repo_config_exec": ("workspace", "Workspace commands", "Git settings or editor tasks name commands that can run when the workspace is used."),
    "agent_config_tamper": ("workspace", "Agent hooks", "Agent configuration contains commands that run during a session."),
    "package_manifest_exec": ("workspace", "Install scripts", "A package manifest names scripts that run when dependencies are installed."),
    "coordinated_action": ("fleet", "Coordinated actions", "Independent session families share an unusual pattern of network writes."),
}


def kinds():
    from clawmetry.detectors import ALL_INCIDENT_KINDS
    return ALL_INCIDENT_KINDS


def validate(kind, enabled):
    if kind not in kinds():
        raise ValueError("Choose a check from the Guard catalogue.")
    if type(enabled) is not bool:
        raise ValueError("Choose on or off for this check.")


def disabled_kinds(settings):
    """Only an explicit off disables detection; a corrupt value cannot mute it."""
    return {kind for kind in kinds() if settings.get(PREFIX + kind) == "false"}


def catalogue(settings=None, *, environ=None, now=None):
    env = os.environ if environ is None else environ
    now = time.time() if now is None else now
    available = isinstance(settings, dict)
    settings = settings if available else {}
    engine_on = all(env.get(k, "1") != "0" for k in
                    ("CLAWMETRY_DETECTORS", "CLAWMETRY_STUCK_DETECT"))
    workspace_on = str(env.get("CLAWMETRY_REPO_SCAN", "1")).strip().lower() not in ("0", "false", "no")
    try:
        last_pass = int(settings.get(LAST_PASS_KEY) or 0)
    except (ValueError, TypeError):
        last_pass = 0
    rows = []
    from clawmetry.detectors import WORKSPACE_KINDS, FLEET_KINDS
    for kind in kinds():
        family, title, description = DESCRIPTIONS.get(kind, (
            "workspace" if kind in WORKSPACE_KINDS else "progress",
            kind.replace("_", " ").capitalize(), "Review findings from this check."))
        scope = "workspace" if kind in WORKSPACE_KINDS else "fleet" if kind in FLEET_KINDS else "session"
        raw = settings.get(PREFIX + kind)
        valid = raw in (None, "true", "false")
        if not valid:
            log.warning("Invalid Guard preference for %s; detection keeps its default", kind)
        configured = raw != "false"
        overridden = not engine_on or (scope == "workspace" and not workspace_on)
        state = "unknown" if not available or not valid else "overridden" if overridden else "on" if configured else "off"
        rows.append(dict(kind=kind, family=family, title=title, description=description,
                         scope=scope, enabled=configured if available and valid else None,
                         effective_enabled=(configured and not overridden) if available and valid else None,
                         state=state))
    return dict(checks=rows, families=[dict(id=f[0], title=f[1], question=f[2]) for f in FAMILIES],
                total=len(rows), enabled=sum(r["effective_enabled"] is True for r in rows),
                available=available, engine_enabled=engine_on, scope="node",
                last_pass_ms=last_pass or None,
                recent_pass=bool(last_pass and 0 <= now * 1000 - last_pass < 180000),
                generated_at=int(now * 1000))
