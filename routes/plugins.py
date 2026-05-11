"""
routes/plugins.py — Plugin registry: unified view of installed plugins (#692).

GET /api/plugins  — list all installed plugins, categorised by type,
                    with per-plugin 30-day invocation counts from JSONL sessions.

Plugin types mirror the four OpenClaw extensibility axes (slide 26 of
Alexander Krentsel's Berkeley talk):
  connector  — channel adapters (Telegram, Discord, Slack, …)
  memory     — alternative memory backends (vector DBs, …)
  tool       — additional agent tools
  provider   — custom LLM providers

Blueprint: bp_plugins
"""

import json
import os
import time

from flask import Blueprint, jsonify

bp_plugins = Blueprint("plugins", __name__)

# ── Classifier name tables ────────────────────────────────────────────────

_CONNECTOR_NAMES = frozenset({
    "telegram", "discord", "slack", "signal", "whatsapp", "irc",
    "imessage", "webchat", "matrix", "msteams", "mattermost",
    "bluebubbles", "googlechat", "line", "nostr", "twitch", "feishu",
    "synology-chat", "nextcloud-talk", "sms", "email", "twitter",
    "instagram", "linkedin", "facebook", "messenger", "viber", "wechat",
})

_MEMORY_NAMES = frozenset({
    "pinecone", "weaviate", "qdrant", "chroma", "redis", "mongo",
    "faiss", "milvus", "pgvector", "lancedb", "chromadb",
})

_MEMORY_KEYWORDS = ("vector", "embed", "rag", "chromadb", "pinecone")

_PROVIDER_NAMES = frozenset({
    "openai", "anthropic", "google", "gemini", "ollama", "openrouter",
    "groq", "mistral", "cohere", "together", "perplexity", "fireworks",
    "bedrock", "azure", "vertex",
})


def _classify(name: str) -> str:
    """Return the plugin type for a given plugin name."""
    n = name.lower().replace("-", "_").replace(" ", "_")
    if n in _CONNECTOR_NAMES:
        return "connector"
    if n in _MEMORY_NAMES or any(kw in n for kw in _MEMORY_KEYWORDS):
        return "memory"
    if n in _PROVIDER_NAMES:
        return "provider"
    return "tool"


# ── Config readers ────────────────────────────────────────────────────────

def _read_config_plugins() -> dict:
    """
    Parse gateway.yaml + openclaw.json for installed plugins.
    Returns {key: {name, type, version, enabled}} where key is name.lower().
    """
    plugins: dict = {}

    def _add(name: str, conf=None) -> None:
        key = name.strip().lower()
        if not key:
            return
        if key not in plugins:
            plugins[key] = {
                "name": name.strip(),
                "type": _classify(name),
                "version": None,
                "enabled": True,
            }
        if isinstance(conf, dict):
            if conf.get("version"):
                plugins[key]["version"] = str(conf["version"])
            if "enabled" in conf:
                plugins[key]["enabled"] = bool(conf["enabled"])

    def _scan_section(section, section_hint: str = "") -> None:
        if isinstance(section, dict):
            for name, conf in section.items():
                _add(name, conf if isinstance(conf, dict) else {})
        elif isinstance(section, list):
            for item in section:
                if isinstance(item, str):
                    _add(item)
                elif isinstance(item, dict) and item.get("name"):
                    _add(item["name"], item)

    # gateway.yaml / gateway.yml
    yaml_candidates = [
        os.path.expanduser("~/.openclaw/gateway.yaml"),
        os.path.expanduser("~/.openclaw/gateway.yml"),
        os.path.expanduser("~/.clawdbot/gateway.yaml"),
        os.path.expanduser("~/.clawdbot/gateway.yml"),
    ]
    for yf in yaml_candidates:
        try:
            import yaml as _yaml  # optional dep — skip gracefully if missing

            with open(yf) as fh:
                ydata = _yaml.safe_load(fh)
            if not isinstance(ydata, dict):
                continue
            for section_key in ("channels", "plugins", "tools", "providers", "memory"):
                _scan_section(ydata.get(section_key, {}), section_key)
        except Exception:
            continue

    # openclaw.json / clawdbot.json / moltbot.json
    json_candidates = [
        os.path.expanduser("~/.openclaw/openclaw.json"),
        os.path.expanduser("~/.clawdbot/openclaw.json"),
        os.path.expanduser("~/.clawdbot/clawdbot.json"),
        os.path.expanduser("~/.clawdbot/moltbot.json"),
    ]
    for cf in json_candidates:
        try:
            with open(cf) as fh:
                data = json.load(fh)
            for section_key in ("plugins", "tools", "providers", "channels", "memory"):
                raw_section = data.get(section_key, {})
                # Some JSON configs nest entries under "entries"
                if isinstance(raw_section, dict) and "entries" in raw_section:
                    raw_section = raw_section["entries"]
                _scan_section(raw_section, section_key)
        except Exception:
            continue

    return plugins


# ── Invocation counter ────────────────────────────────────────────────────

_SCAN_MAX_FILES = 60  # limit JSONL files scanned per request


def _count_invocations(plugin_keys: frozenset, cutoff_ts: float) -> dict:
    """
    Scan recent JSONL sessions for tool_use blocks whose name contains a
    plugin key. Returns {key: {"count": int, "last_ts": float}}.

    Approximate: matches tool call names, not channel-level traffic.
    """
    result = {k: {"count": 0, "last_ts": 0.0} for k in plugin_keys}
    if not plugin_keys:
        return result

    import dashboard as _d  # late import avoids circular dependency

    sessions_dir = _d.SESSIONS_DIR
    if not sessions_dir or not os.path.isdir(sessions_dir):
        return result

    try:
        all_files = [
            f
            for f in os.listdir(sessions_dir)
            if f.endswith(".jsonl")
            and ".deleted." not in f
            and ".reset." not in f
        ]
        # Newest files first so we hit the 30d window quickly
        all_files.sort(
            key=lambda f: os.path.getmtime(os.path.join(sessions_dir, f)),
            reverse=True,
        )
        all_files = all_files[:_SCAN_MAX_FILES]
    except OSError:
        return result

    for fname in all_files:
        fpath = os.path.join(sessions_dir, fname)
        # Skip files older than cutoff entirely (mtime heuristic)
        try:
            if os.path.getmtime(fpath) < cutoff_ts:
                break  # files are sorted newest-first; safe to stop
        except OSError:
            continue

        try:
            with open(fpath, errors="replace") as fh:
                for raw in fh:
                    raw = raw.strip()
                    if not raw:
                        continue
                    try:
                        msg = json.loads(raw)
                    except Exception:
                        continue

                    content = msg.get("content") or []
                    if not isinstance(content, list):
                        continue

                    msg_ts_raw = msg.get("timestamp", 0)
                    try:
                        msg_ts = float(msg_ts_raw) if msg_ts_raw else 0.0
                    except (TypeError, ValueError):
                        msg_ts = 0.0

                    for block in content:
                        if not isinstance(block, dict):
                            continue
                        if block.get("type") != "tool_use":
                            continue
                        tool_name = (block.get("name") or "").lower()
                        for pkey in plugin_keys:
                            if pkey in tool_name:
                                if msg_ts >= cutoff_ts:
                                    result[pkey]["count"] += 1
                                if msg_ts > result[pkey]["last_ts"]:
                                    result[pkey]["last_ts"] = msg_ts
        except Exception:
            continue

    return result


# ── Route ─────────────────────────────────────────────────────────────────

@bp_plugins.route("/api/plugins")
def api_plugins():
    """
    Return the installed plugin registry with 30-day invocation counts.

    Response shape:
      {
        "plugins": [{name, type, version, enabled, invocations_30d,
                      last_used_ts, last_used_ago_seconds, unused}, …],
        "total": int,
        "unused_count": int,
        "by_type": {connector: […], memory: […], tool: […], provider: […]},
      }
    """
    plugins = _read_config_plugins()
    now = time.time()
    cutoff_30d = now - 30 * 86400

    invocations = _count_invocations(frozenset(plugins), cutoff_30d)

    result = []
    for key, info in plugins.items():
        inv = invocations.get(key, {"count": 0, "last_ts": 0.0})
        last_ts = inv["last_ts"]
        result.append({
            "name": info["name"],
            "type": info["type"],
            "version": info["version"],
            "enabled": info["enabled"],
            "invocations_30d": inv["count"],
            "last_used_ts": last_ts if last_ts > 0 else None,
            "last_used_ago_seconds": int(now - last_ts) if last_ts > 0 else None,
            "unused": inv["count"] == 0,
        })

    # Sort: most-used first, then by type, then alphabetically
    result.sort(key=lambda p: (-p["invocations_30d"], p["type"], p["name"]))

    by_type = {t: [] for t in ("connector", "memory", "tool", "provider")}
    for p in result:
        by_type.get(p["type"], by_type["tool"]).append(p)

    return jsonify({
        "plugins": result,
        "total": len(result),
        "unused_count": sum(1 for p in result if p["unused"]),
        "by_type": by_type,
    })
