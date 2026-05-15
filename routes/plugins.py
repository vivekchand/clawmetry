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
from datetime import datetime, timezone

from flask import Blueprint, jsonify
from clawmetry.config import is_local_store_read_enabled

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


# ── DuckDB fast-path (Tier-1 MOAT, issue #1364) ───────────────────────────


def _ls_call(method_name, **kwargs):
    """Cross-process LocalStore call with single-process fallback.

    Mirrors :func:`routes.sessions._ls_call` — daemon HTTP proxy first
    (cross-process safe; tests/dev mode without a daemon fall through to
    a direct read-only DuckDB open). Returns ``None`` when neither path
    can answer, so the caller defers to the legacy JSONL walker.
    """
    try:
        from routes.local_query import local_store_via_daemon
        result = local_store_via_daemon(method_name, **kwargs)
        if result is not None:
            return result
    except Exception:
        pass
    try:
        from clawmetry import local_store
        store = local_store.get_store(read_only=True)
        return getattr(store, method_name)(**kwargs)
    except Exception:
        return None


def _try_local_store_invocations(plugin_keys: frozenset, cutoff_ts: float):
    """Tier-1 DuckDB fast path for plugin invocation counts.

    Replaces the legacy JSONL walker (60 files × every line) with a
    single SQL pull from the events table. Returns the same
    ``{key: {count, last_ts}}`` shape :func:`_count_invocations` returns
    (``last_ts`` in seconds-since-epoch, ``count`` only counts events
    whose ts ≥ ``cutoff_ts``).

    Returns ``None`` to defer to the legacy walker if:
      * the daemon proxy is unreachable AND direct DuckDB open fails
      * the events table has no tool_call rows in the 30d window
      * any unexpected error happens (we'd rather degrade than 500)
    """
    if not plugin_keys:
        return {k: {"count": 0, "last_ts": 0.0} for k in plugin_keys}

    # 30d window matches the legacy ``cutoff_ts`` exactly. We pull a
    # little extra (32d) to give last_used_ts the same "any historical
    # invocation" semantics the JSONL walker provides — invocations
    # outside the 30d window still update last_ts but don't contribute
    # to the count.
    since_dt = datetime.fromtimestamp(cutoff_ts - 2 * 86400, tz=timezone.utc)
    since_iso = since_dt.isoformat().replace("+00:00", "Z")
    rows = _ls_call("query_tool_call_invocations", since=since_iso, limit=50_000)
    if rows is None:
        return None

    # Empty-shell pattern (#1266 lesson): even when the events table has
    # no tool calls, return a populated result so the route returns
    # ``invocations_30d=0`` instantly instead of falling through to the
    # 5-7s JSONL walker for the same answer.
    out = {k: {"count": 0, "last_ts": 0.0} for k in plugin_keys}

    def _ts_to_seconds(ts) -> float:
        if not ts:
            return 0.0
        if isinstance(ts, (int, float)):
            return float(ts) / 1000.0 if ts > 1e12 else float(ts)
        try:
            return datetime.fromisoformat(
                str(ts).replace("Z", "+00:00")
            ).timestamp()
        except (ValueError, TypeError):
            return 0.0

    for r in rows:
        name = (r.get("name") or "").lower()
        if not name:
            continue
        ts_secs = _ts_to_seconds(r.get("ts"))
        for pkey in plugin_keys:
            if pkey in name:
                if ts_secs >= cutoff_ts:
                    out[pkey]["count"] += 1
                if ts_secs > out[pkey]["last_ts"]:
                    out[pkey]["last_ts"] = ts_secs

    return out


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

    # Tier-1 DuckDB fast path (issue #1364) — opt-in via
    # CLAWMETRY_LOCAL_STORE_READ=1. Skips the 60-file × every-line JSONL
    # walk by reading tool-call rows from DuckDB. Falls through to the
    # legacy walker on miss.
    invocations = None
    source = "jsonl_walker"
    if is_local_store_read_enabled():
        fast = _try_local_store_invocations(frozenset(plugins), cutoff_30d)
        if fast is not None:
            invocations = fast
            source = "local_store"
    if invocations is None:
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
        "_source": source,
    })
