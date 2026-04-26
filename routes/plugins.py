"""
routes/plugins.py — Plugin Registry endpoints (GH #692).

Unified view of all installed OpenClaw plugins, categorized by type:
  - Connector: channel adapters (Telegram, Discord, etc.)
  - Provider: LLM providers (Ollama, OpenAI, etc.)
  - Tool: search, browser, ACP tools
  - Observability: telemetry exporters (ClawMetry, OTEL, etc.)

Endpoints:
  GET /api/plugins — list all plugins with type, enabled status, config summary

Blueprint: bp_plugins
"""

import json
import os

from flask import Blueprint, jsonify

bp_plugins = Blueprint("plugins", __name__)

# ── Type classification maps ─────────────────────────────────────────────────

_CONNECTORS = frozenset({
    "telegram", "whatsapp", "discord", "slack", "irc", "signal", "webchat",
    "matrix", "mattermost", "line", "nostr", "twitch", "feishu", "zalo",
    "tlon", "synology-chat", "nextcloud-talk", "google-chat", "ms-teams",
    "bluebubbles",
})

_PROVIDERS = frozenset({
    "ollama", "openai", "anthropic", "google", "deepseek", "groq",
    "together", "fireworks", "xai",
})

_TOOLS = frozenset({
    "brave", "duckduckgo", "openclaw-web-search", "browser", "acpx",
})

_OBSERVABILITY = frozenset({
    "clawmetry", "opik-openclaw", "diagnostics-otel",
})


def _classify(name: str) -> str:
    """Return the plugin type for a given plugin name."""
    n = name.lower()
    if n in _CONNECTORS:
        return "connector"
    if n in _PROVIDERS:
        return "provider"
    if n in _TOOLS:
        return "tool"
    if n in _OBSERVABILITY:
        return "observability"
    # Fallback heuristics
    return "tool"


def _get_plugins():
    """Read plugins from openclaw.json and return categorized list + summary."""
    import dashboard as _d

    oc_dir = _d._get_openclaw_dir()
    config_path = os.path.join(oc_dir, "openclaw.json")

    plugins = []
    if not os.path.isfile(config_path):
        return plugins, {"total": 0, "enabled": 0, "byType": {}}

    try:
        with open(config_path, "r") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError):
        return plugins, {"total": 0, "enabled": 0, "byType": {}}

    entries = (data.get("plugins") or {}).get("entries") or {}

    by_type = {"connector": 0, "provider": 0, "tool": 0, "observability": 0}
    enabled_count = 0

    for name, info in sorted(entries.items()):
        ptype = _classify(name)
        enabled = bool(info.get("enabled", False)) if isinstance(info, dict) else False
        has_config = bool(info.get("config")) if isinstance(info, dict) else False

        plugins.append({
            "name": name,
            "type": ptype,
            "enabled": enabled,
            "hasConfig": has_config,
        })

        by_type[ptype] = by_type.get(ptype, 0) + 1
        if enabled:
            enabled_count += 1

    summary = {
        "total": len(plugins),
        "enabled": enabled_count,
        "byType": by_type,
    }

    return plugins, summary


@bp_plugins.route("/api/plugins")
def api_plugins():
    """Return all installed plugins with type classification and summary."""
    plugins, summary = _get_plugins()
    return jsonify({"plugins": plugins, "summary": summary})
