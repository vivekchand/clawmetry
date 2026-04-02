"""
ClawMetry Proxy — opt-in enforcement layer between OpenClaw and LLM providers.

Sits at localhost:4100 (configurable) and forwards requests to Anthropic/OpenAI
while enforcing budgets, detecting loops, and routing models.

Architecture:
    OpenClaw → ClawMetry Proxy (localhost:4100) → Anthropic/OpenAI

Activate with one env var:
    ANTHROPIC_BASE_URL=http://localhost:4100/v1

Config in ~/.clawmetry/proxy.json:
    {
        "enabled": true,
        "port": 4100,
        "budget": { "daily_usd": 10.0, "monthly_usd": 100.0, "action": "block" },
        "loop_detection": { "enabled": true, "window_seconds": 300, "max_similar": 5 },
        "routing": { "rules": [] },
        "providers": {
            "anthropic": { "api_key_env": "ANTHROPIC_API_KEY", "base_url": "https://api.anthropic.com" },
            "openai": { "api_key_env": "OPENAI_API_KEY", "base_url": "https://api.openai.com" }
        }
    }
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import re
import sqlite3
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Generator, List, Optional, Tuple
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

logger = logging.getLogger("clawmetry.proxy")

# ── Constants ──────────────────────────────────────────────────────────

DEFAULT_PORT = 4100
CONFIG_DIR = Path.home() / ".clawmetry"
PROXY_CONFIG_FILE = CONFIG_DIR / "proxy.json"
PROXY_DB_FILE = CONFIG_DIR / "proxy.db"
PROXY_PID_FILE = CONFIG_DIR / "proxy.pid"
PROXY_LOG_FILE = CONFIG_DIR / "proxy.log"

# Model pricing per 1M tokens (input, output) — kept in sync with dashboard.py
MODEL_PRICING = {
    "claude-opus-4": (15.0, 75.0),
    "claude-sonnet-4": (3.0, 15.0),
    "claude-3-5-sonnet": (3.0, 15.0),
    "claude-3-opus": (15.0, 75.0),
    "claude-3-sonnet": (3.0, 15.0),
    "claude-3-haiku": (0.25, 1.25),
    "gpt-4o": (2.5, 10.0),
    "gpt-4-turbo": (10.0, 30.0),
    "gpt-4": (30.0, 60.0),
    "gpt-3.5-turbo": (0.5, 1.5),
    "default": (15.0, 45.0),
}


# ── Configuration ──────────────────────────────────────────────────────


@dataclass
class BudgetConfig:
    daily_usd: float = 0.0
    monthly_usd: float = 0.0
    action: str = "block"  # "block" | "warn" | "downgrade"
    downgrade_model: str = "claude-3-haiku-20240307"


@dataclass
class LoopDetectionConfig:
    enabled: bool = True
    window_seconds: int = 300
    max_similar: int = 5
    similarity_threshold: float = 0.85


@dataclass
class RoutingRule:
    """Route requests matching a pattern to a different model."""

    match_model: str = ""  # regex pattern for model name
    match_session: str = ""  # regex pattern for session header
    target_model: str = ""  # model to route to
    target_provider: str = ""  # provider to route to


@dataclass
class ProviderConfig:
    api_key_env: str = ""
    base_url: str = ""


@dataclass
class ProxyConfig:
    enabled: bool = True
    port: int = DEFAULT_PORT
    host: str = "127.0.0.1"
    budget: BudgetConfig = field(default_factory=BudgetConfig)
    loop_detection: LoopDetectionConfig = field(default_factory=LoopDetectionConfig)
    routing_rules: List[RoutingRule] = field(default_factory=list)
    providers: Dict[str, ProviderConfig] = field(default_factory=dict)
    log_requests: bool = False

    @classmethod
    def load(cls) -> "ProxyConfig":
        """Load config from ~/.clawmetry/proxy.json, with env var overrides."""
        config = cls()
        config.providers = {
            "anthropic": ProviderConfig(
                api_key_env="ANTHROPIC_API_KEY",
                base_url="https://api.anthropic.com",
            ),
            "openai": ProviderConfig(
                api_key_env="OPENAI_API_KEY",
                base_url="https://api.openai.com",
            ),
        }

        if PROXY_CONFIG_FILE.exists():
            try:
                raw = json.loads(PROXY_CONFIG_FILE.read_text())
                config.enabled = raw.get("enabled", True)
                config.port = raw.get("port", DEFAULT_PORT)
                config.host = raw.get("host", "127.0.0.1")
                config.log_requests = raw.get("log_requests", False)

                if "budget" in raw:
                    b = raw["budget"]
                    config.budget = BudgetConfig(
                        daily_usd=b.get("daily_usd", 0.0),
                        monthly_usd=b.get("monthly_usd", 0.0),
                        action=b.get("action", "block"),
                        downgrade_model=b.get(
                            "downgrade_model", "claude-3-haiku-20240307"
                        ),
                    )

                if "loop_detection" in raw:
                    ld = raw["loop_detection"]
                    config.loop_detection = LoopDetectionConfig(
                        enabled=ld.get("enabled", True),
                        window_seconds=ld.get("window_seconds", 300),
                        max_similar=ld.get("max_similar", 5),
                        similarity_threshold=ld.get("similarity_threshold", 0.85),
                    )

                if "routing" in raw and "rules" in raw["routing"]:
                    for r in raw["routing"]["rules"]:
                        config.routing_rules.append(
                            RoutingRule(
                                match_model=r.get("match_model", ""),
                                match_session=r.get("match_session", ""),
                                target_model=r.get("target_model", ""),
                                target_provider=r.get("target_provider", ""),
                            )
                        )

                if "providers" in raw:
                    for name, prov in raw["providers"].items():
                        config.providers[name] = ProviderConfig(
                            api_key_env=prov.get("api_key_env", ""),
                            base_url=prov.get("base_url", ""),
                        )
            except (json.JSONDecodeError, KeyError) as e:
                logger.warning(f"Failed to parse proxy config: {e}")

        # Env var overrides
        config.port = int(os.environ.get("CLAWMETRY_PROXY_PORT", config.port))
        config.host = os.environ.get("CLAWMETRY_PROXY_HOST", config.host)

        if os.environ.get("CLAWMETRY_PROXY_DAILY_USD"):
            config.budget.daily_usd = float(os.environ["CLAWMETRY_PROXY_DAILY_USD"])
        if os.environ.get("CLAWMETRY_PROXY_MONTHLY_USD"):
            config.budget.monthly_usd = float(os.environ["CLAWMETRY_PROXY_MONTHLY_USD"])

        return config

    def save(self) -> None:
        """Persist config to ~/.clawmetry/proxy.json."""
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        data = {
            "enabled": self.enabled,
            "port": self.port,
            "host": self.host,
            "log_requests": self.log_requests,
            "budget": {
                "daily_usd": self.budget.daily_usd,
                "monthly_usd": self.budget.monthly_usd,
                "action": self.budget.action,
                "downgrade_model": self.budget.downgrade_model,
            },
            "loop_detection": {
                "enabled": self.loop_detection.enabled,
                "window_seconds": self.loop_detection.window_seconds,
                "max_similar": self.loop_detection.max_similar,
                "similarity_threshold": self.loop_detection.similarity_threshold,
            },
            "routing": {
                "rules": [
                    {
                        "match_model": r.match_model,
                        "match_session": r.match_session,
                        "target_model": r.target_model,
                        "target_provider": r.target_provider,
                    }
                    for r in self.routing_rules
                ]
            },
            "providers": {
                name: {
                    "api_key_env": p.api_key_env,
                    "base_url": p.base_url,
                }
                for name, p in self.providers.items()
            },
        }
        PROXY_CONFIG_FILE.write_text(json.dumps(data, indent=2))
        PROXY_CONFIG_FILE.chmod(0o600)


# ── Database (usage tracking & event log) ──────────────────────────────


class ProxyDB:
    """SQLite-based storage for proxy usage data and enforcement events."""

    def __init__(self, db_path: Path = PROXY_DB_FILE):
        self._db_path = db_path
        self._lock = threading.Lock()
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self._db_path), timeout=5)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        return conn

    def _init_db(self):
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        with self._lock:
            conn = self._connect()
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS proxy_usage (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp REAL NOT NULL,
                    provider TEXT NOT NULL,
                    model TEXT NOT NULL,
                    input_tokens INTEGER DEFAULT 0,
                    output_tokens INTEGER DEFAULT 0,
                    cache_read_tokens INTEGER DEFAULT 0,
                    cache_creation_tokens INTEGER DEFAULT 0,
                    cost_usd REAL DEFAULT 0.0,
                    session_id TEXT DEFAULT '',
                    request_hash TEXT DEFAULT '',
                    latency_ms REAL DEFAULT 0.0,
                    status TEXT DEFAULT 'ok'
                );

                CREATE TABLE IF NOT EXISTS proxy_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp REAL NOT NULL,
                    event_type TEXT NOT NULL,
                    severity TEXT DEFAULT 'info',
                    message TEXT NOT NULL,
                    details TEXT DEFAULT '{}'
                );

                CREATE INDEX IF NOT EXISTS idx_proxy_usage_ts
                    ON proxy_usage(timestamp DESC);
                CREATE INDEX IF NOT EXISTS idx_proxy_usage_model
                    ON proxy_usage(model, timestamp DESC);
                CREATE INDEX IF NOT EXISTS idx_proxy_events_ts
                    ON proxy_events(timestamp DESC);
                CREATE INDEX IF NOT EXISTS idx_proxy_events_type
                    ON proxy_events(event_type, timestamp DESC);
            """)
            conn.commit()
            conn.close()

    def record_usage(
        self,
        provider: str,
        model: str,
        input_tokens: int,
        output_tokens: int,
        cost_usd: float,
        session_id: str = "",
        request_hash: str = "",
        latency_ms: float = 0.0,
        status: str = "ok",
        cache_read_tokens: int = 0,
        cache_creation_tokens: int = 0,
    ) -> None:
        with self._lock:
            conn = self._connect()
            conn.execute(
                """INSERT INTO proxy_usage
                   (timestamp, provider, model, input_tokens, output_tokens,
                    cache_read_tokens, cache_creation_tokens,
                    cost_usd, session_id, request_hash, latency_ms, status)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    time.time(),
                    provider,
                    model,
                    input_tokens,
                    output_tokens,
                    cache_read_tokens,
                    cache_creation_tokens,
                    cost_usd,
                    session_id,
                    request_hash,
                    latency_ms,
                    status,
                ),
            )
            conn.commit()
            conn.close()

    def record_event(
        self,
        event_type: str,
        message: str,
        severity: str = "info",
        details: dict = None,
    ) -> None:
        with self._lock:
            conn = self._connect()
            conn.execute(
                """INSERT INTO proxy_events (timestamp, event_type, severity, message, details)
                   VALUES (?, ?, ?, ?, ?)""",
                (time.time(), event_type, severity, message, json.dumps(details or {})),
            )
            conn.commit()
            conn.close()

    def get_spending(self, since_ts: float) -> float:
        """Get total USD spent since a timestamp."""
        conn = self._connect()
        row = conn.execute(
            "SELECT COALESCE(SUM(cost_usd), 0.0) as total FROM proxy_usage WHERE timestamp >= ?",
            (since_ts,),
        ).fetchone()
        conn.close()
        return row["total"] if row else 0.0

    def get_daily_spending(self) -> float:
        today_start = (
            datetime.now(timezone.utc)
            .replace(hour=0, minute=0, second=0, microsecond=0)
            .timestamp()
        )
        return self.get_spending(today_start)

    def get_monthly_spending(self) -> float:
        month_start = (
            datetime.now(timezone.utc)
            .replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            .timestamp()
        )
        return self.get_spending(month_start)

    def get_recent_events(self, limit: int = 50, event_type: str = None) -> List[dict]:
        conn = self._connect()
        if event_type:
            rows = conn.execute(
                "SELECT * FROM proxy_events WHERE event_type = ? ORDER BY timestamp DESC LIMIT ?",
                (event_type, limit),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM proxy_events ORDER BY timestamp DESC LIMIT ?",
                (limit,),
            ).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def get_usage_summary(self, since_ts: float = 0) -> dict:
        """Get aggregated usage stats since a timestamp."""
        with self._lock:
            conn = self._connect()
            row = conn.execute(
                """SELECT
                    COUNT(*) as request_count,
                    COALESCE(SUM(input_tokens), 0) as total_input,
                    COALESCE(SUM(output_tokens), 0) as total_output,
                    COALESCE(SUM(cost_usd), 0.0) as total_cost,
                    COALESCE(AVG(latency_ms), 0.0) as avg_latency
                FROM proxy_usage WHERE timestamp >= ?""",
                (since_ts,),
            ).fetchone()
            conn.close()
            return dict(row) if row else {}

    def get_recent_request_hashes(
        self, session_id: str, window_seconds: int
    ) -> List[str]:
        """Get recent request hashes for loop detection."""
        since = time.time() - window_seconds
        with self._lock:
            conn = self._connect()
            rows = conn.execute(
                """SELECT request_hash FROM proxy_usage
                   WHERE session_id = ? AND timestamp >= ? AND request_hash != ''
                   ORDER BY timestamp DESC""",
                (session_id, since),
            ).fetchall()
            conn.close()
            return [r["request_hash"] for r in rows]

    def prune_old_data(self, retention_days: int = 30) -> None:
        """Remove data older than retention period."""
        cutoff = time.time() - (retention_days * 86400)
        with self._lock:
            conn = self._connect()
            conn.execute("DELETE FROM proxy_usage WHERE timestamp < ?", (cutoff,))
            conn.execute("DELETE FROM proxy_events WHERE timestamp < ?", (cutoff,))
            conn.commit()
            conn.close()


# ── Cost Calculation ───────────────────────────────────────────────────


def calculate_cost(
    model: str,
    input_tokens: int,
    output_tokens: int,
    cache_read_tokens: int = 0,
    cache_creation_tokens: int = 0,
) -> float:
    """Calculate cost in USD for a request based on model and token counts."""
    model_lower = model.lower()
    pricing = MODEL_PRICING.get("default")

    for key, prices in MODEL_PRICING.items():
        if key == "default":
            continue
        if key in model_lower:
            pricing = prices
            break

    input_price, output_price = pricing

    # Cache read tokens are typically 90% cheaper
    regular_input = input_tokens - cache_read_tokens
    cache_read_cost = (cache_read_tokens / 1_000_000) * (input_price * 0.1)
    cache_create_cost = (cache_creation_tokens / 1_000_000) * (input_price * 1.25)
    input_cost = (max(0, regular_input) / 1_000_000) * input_price
    output_cost = (output_tokens / 1_000_000) * output_price

    return round(input_cost + cache_read_cost + cache_create_cost + output_cost, 6)


# ── Loop Detection ─────────────────────────────────────────────────────


def compute_request_hash(body: dict) -> str:
    """Compute a content-based hash for loop detection.

    Hashes the last user message + model + system prompt to detect
    repeated identical requests (a common sign of agent loops).
    """
    parts = []

    # Model
    parts.append(body.get("model", ""))

    # System prompt (Anthropic format)
    system = body.get("system", "")
    if isinstance(system, list):
        system = " ".join(b.get("text", "") for b in system if isinstance(b, dict))
    if system:
        parts.append(system[:500])  # Truncate for efficiency

    # Last user message
    messages = body.get("messages", [])
    if messages:
        last_msg = messages[-1]
        content = last_msg.get("content", "")
        if isinstance(content, list):
            content = " ".join(
                b.get("text", "") for b in content if isinstance(b, dict)
            )
        parts.append(str(content)[:2000])

    combined = "|".join(parts)
    return hashlib.sha256(combined.encode()).hexdigest()[:16]


# ── SSE Stream Parsing ─────────────────────────────────────────────────


@dataclass
class StreamUsage:
    """Accumulated usage from a streaming response."""

    input_tokens: int = 0
    output_tokens: int = 0
    cache_read_tokens: int = 0
    cache_creation_tokens: int = 0
    model: str = ""
    stop_reason: str = ""


def parse_anthropic_sse_chunk(line: str, usage: StreamUsage) -> None:
    """Parse a single Anthropic SSE data line and update usage in-place."""
    if not line.startswith("data: "):
        return

    data_str = line[6:].strip()
    if data_str == "[DONE]":
        return

    try:
        data = json.loads(data_str)
    except json.JSONDecodeError:
        return

    event_type = data.get("type", "")

    if event_type == "message_start":
        msg = data.get("message", {})
        u = msg.get("usage", {})
        usage.input_tokens = u.get("input_tokens", 0)
        usage.cache_read_tokens = u.get("cache_read_input_tokens", 0)
        usage.cache_creation_tokens = u.get("cache_creation_input_tokens", 0)
        usage.model = msg.get("model", usage.model)

    elif event_type == "message_delta":
        u = data.get("usage", {})
        usage.output_tokens = u.get("output_tokens", 0)
        usage.stop_reason = data.get("delta", {}).get("stop_reason", "")


def parse_openai_sse_chunk(line: str, usage: StreamUsage) -> None:
    """Parse a single OpenAI SSE data line and update usage in-place."""
    if not line.startswith("data: "):
        return

    data_str = line[6:].strip()
    if data_str == "[DONE]":
        return

    try:
        data = json.loads(data_str)
    except json.JSONDecodeError:
        return

    usage.model = data.get("model", usage.model)

    # OpenAI includes usage in final chunk when stream_options.include_usage=true
    u = data.get("usage")
    if u:
        usage.input_tokens = u.get("prompt_tokens", 0)
        usage.output_tokens = u.get("completion_tokens", 0)

    choices = data.get("choices", [])
    if choices and choices[0].get("finish_reason"):
        usage.stop_reason = choices[0]["finish_reason"]


# ── Provider Detection ─────────────────────────────────────────────────


def detect_provider(path: str, headers: dict, body: dict) -> str:
    """Detect whether a request is for Anthropic or OpenAI based on path and headers."""
    if "/messages" in path:
        return "anthropic"
    if "/chat/completions" in path:
        return "openai"
    if headers.get("x-api-key") or headers.get("anthropic-version"):
        return "anthropic"
    auth = headers.get("authorization", "")
    if auth.startswith("Bearer sk-"):
        return "openai"
    model = body.get("model", "")
    if "claude" in model.lower():
        return "anthropic"
    if "gpt" in model.lower() or "o1" in model.lower():
        return "openai"
    return "anthropic"  # Default


# ── Budget Enforcer ────────────────────────────────────────────────────


class BudgetEnforcer:
    """Checks spending against configured limits and decides whether to allow requests."""

    def __init__(self, config: BudgetConfig, db: ProxyDB):
        self.config = config
        self.db = db

    def check(self, model: str = "") -> Tuple[bool, str]:
        """Check if a request should be allowed.

        Returns:
            (allowed, reason) - True if allowed, reason explains why not
        """
        if self.config.daily_usd <= 0 and self.config.monthly_usd <= 0:
            return True, ""

        daily_spent = self.db.get_daily_spending()
        monthly_spent = self.db.get_monthly_spending()

        if self.config.daily_usd > 0 and daily_spent >= self.config.daily_usd:
            reason = f"Daily budget exceeded: ${daily_spent:.2f} / ${self.config.daily_usd:.2f}"
            return False, reason

        if self.config.monthly_usd > 0 and monthly_spent >= self.config.monthly_usd:
            reason = f"Monthly budget exceeded: ${monthly_spent:.2f} / ${self.config.monthly_usd:.2f}"
            return False, reason

        return True, ""

    def get_status(self) -> dict:
        """Get current budget status for the API."""
        daily_spent = self.db.get_daily_spending()
        monthly_spent = self.db.get_monthly_spending()
        return {
            "daily_spent": round(daily_spent, 4),
            "monthly_spent": round(monthly_spent, 4),
            "daily_limit": self.config.daily_usd,
            "monthly_limit": self.config.monthly_usd,
            "daily_remaining": round(max(0, self.config.daily_usd - daily_spent), 4)
            if self.config.daily_usd > 0
            else None,
            "monthly_remaining": round(
                max(0, self.config.monthly_usd - monthly_spent), 4
            )
            if self.config.monthly_usd > 0
            else None,
            "action": self.config.action,
        }


# ── Loop Detector ──────────────────────────────────────────────────────


class LoopDetector:
    """Detects repeated request patterns that indicate agent loops."""

    def __init__(self, config: LoopDetectionConfig, db: ProxyDB):
        self.config = config
        self.db = db

    def check(self, session_id: str, request_hash: str) -> Tuple[bool, str]:
        """Check if this request looks like a loop.

        Returns:
            (is_loop, reason) - True if loop detected
        """
        if not self.config.enabled or not session_id:
            return False, ""

        recent = self.db.get_recent_request_hashes(
            session_id, self.config.window_seconds
        )

        match_count = sum(1 for h in recent if h == request_hash)

        if match_count >= self.config.max_similar:
            reason = (
                f"Loop detected: {match_count} identical requests from session "
                f"'{session_id}' in the last {self.config.window_seconds}s"
            )
            return True, reason

        return False, ""


# ── Model Router ───────────────────────────────────────────────────────


class ModelRouter:
    """Routes requests to different models/providers based on rules."""

    def __init__(self, rules: List[RoutingRule]):
        self.rules = rules

    def route(
        self, model: str, session_id: str = ""
    ) -> Tuple[Optional[str], Optional[str]]:
        """Apply routing rules. Returns (new_model, new_provider) or (None, None)."""
        for rule in self.rules:
            model_match = True
            session_match = True

            if rule.match_model:
                model_match = bool(re.search(rule.match_model, model, re.IGNORECASE))
            if rule.match_session:
                session_match = bool(
                    re.search(rule.match_session, session_id, re.IGNORECASE)
                )

            if model_match and session_match:
                return (
                    rule.target_model or None,
                    rule.target_provider or None,
                )

        return None, None


# ── Proxy Server (Flask) ───────────────────────────────────────────────


def create_proxy_app(config: ProxyConfig = None) -> "Flask":
    """Create the Flask proxy application."""
    from flask import Flask, request, Response, jsonify

    if config is None:
        config = ProxyConfig.load()

    app = Flask(__name__)
    app.config["MAX_CONTENT_LENGTH"] = 50 * 1024 * 1024  # 50MB max

    db = ProxyDB()
    budget = BudgetEnforcer(config.budget, db)
    loop_detector = LoopDetector(config.loop_detection, db)
    router = ModelRouter(config.routing_rules)

    _stats = {
        "requests": 0,
        "blocked": 0,
        "loops_detected": 0,
        "started_at": time.time(),
    }
    _stats_lock = threading.Lock()

    def _error_response(
        status_code: int, error_type: str, message: str, provider: str = "anthropic"
    ) -> Response:
        """Return an error response in the provider's expected format."""
        if provider == "openai":
            body = {
                "error": {
                    "message": message,
                    "type": error_type,
                    "code": error_type,
                }
            }
        else:
            body = {
                "type": "error",
                "error": {
                    "type": error_type,
                    "message": message,
                },
            }
        return Response(
            json.dumps(body),
            status=status_code,
            content_type="application/json",
        )

    def _get_upstream_url(provider: str, path: str) -> str:
        """Build the upstream URL for a provider."""
        prov_config = config.providers.get(provider)
        if not prov_config or not prov_config.base_url:
            raise ValueError(f"No base URL configured for provider '{provider}'")
        base = prov_config.base_url.rstrip("/")
        clean_path = path
        if base.endswith("/v1") and clean_path.startswith("/v1"):
            clean_path = clean_path[3:]
        return base + clean_path

    def _get_api_key(provider: str, original_headers: dict) -> str:
        """Get the API key for a provider, from original request or env."""
        if provider == "anthropic":
            key = original_headers.get("x-api-key", "")
            if key:
                return key
        elif provider == "openai":
            auth = original_headers.get("authorization", "")
            if auth.startswith("Bearer ") and auth[7:].startswith("sk-"):
                return auth[7:]

        prov_config = config.providers.get(provider)
        if prov_config and prov_config.api_key_env:
            return os.environ.get(prov_config.api_key_env, "")
        return ""

    def _build_upstream_headers(
        provider: str, api_key: str, original_headers: dict
    ) -> dict:
        """Build headers for the upstream request."""
        headers = {"Content-Type": "application/json"}

        if provider == "anthropic":
            headers["x-api-key"] = api_key
            for h in ["anthropic-version", "anthropic-beta"]:
                val = original_headers.get(h)
                if val:
                    headers[h] = val
            if "anthropic-version" not in headers:
                headers["anthropic-version"] = "2023-06-01"
        elif provider == "openai":
            headers["Authorization"] = f"Bearer {api_key}"

        return headers

    def _forward_non_streaming(
        upstream_url: str, headers: dict, body_bytes: bytes, provider: str
    ) -> Tuple[bytes, int, dict, StreamUsage]:
        """Forward a non-streaming request and return the full response."""
        usage = StreamUsage()
        req = Request(upstream_url, data=body_bytes, headers=headers, method="POST")

        try:
            resp = urlopen(req, timeout=300)
            resp_body = resp.read()
            resp_status = resp.status
            resp_headers = dict(resp.headers)
        except HTTPError as e:
            resp_body = e.read()
            resp_status = e.code
            resp_headers = dict(e.headers)
            usage.stop_reason = f"error_{e.code}"
            return resp_body, resp_status, resp_headers, usage
        except URLError as e:
            error_body = json.dumps(
                {"error": {"type": "proxy_error", "message": str(e)}}
            ).encode()
            return error_body, 502, {}, usage

        try:
            resp_data = json.loads(resp_body)
            if provider == "anthropic":
                u = resp_data.get("usage", {})
                usage.input_tokens = u.get("input_tokens", 0)
                usage.output_tokens = u.get("output_tokens", 0)
                usage.cache_read_tokens = u.get("cache_read_input_tokens", 0)
                usage.cache_creation_tokens = u.get("cache_creation_input_tokens", 0)
                usage.model = resp_data.get("model", "")
                usage.stop_reason = resp_data.get("stop_reason", "")
            elif provider == "openai":
                u = resp_data.get("usage", {})
                usage.input_tokens = u.get("prompt_tokens", 0)
                usage.output_tokens = u.get("completion_tokens", 0)
                usage.model = resp_data.get("model", "")
                choices = resp_data.get("choices", [])
                if choices:
                    usage.stop_reason = choices[0].get("finish_reason", "")
        except (json.JSONDecodeError, KeyError):
            pass

        return resp_body, resp_status, resp_headers, usage

    # ── Routes ─────────────────────────────────────────────────────────

    @app.route("/health", methods=["GET"])
    def health():
        return jsonify({"status": "ok", "service": "clawmetry-proxy"})

    @app.route("/proxy/status", methods=["GET"])
    def proxy_status_route():
        with _stats_lock:
            stats = dict(_stats)
        uptime = time.time() - stats["started_at"]
        return jsonify(
            {
                "status": "running",
                "uptime_seconds": round(uptime, 1),
                "requests_total": stats["requests"],
                "requests_blocked": stats["blocked"],
                "loops_detected": stats["loops_detected"],
                "budget": budget.get_status(),
                "config": {
                    "port": config.port,
                    "host": config.host,
                    "budget_action": config.budget.action,
                    "loop_detection": config.loop_detection.enabled,
                    "routing_rules": len(config.routing_rules),
                },
            }
        )

    @app.route("/proxy/events", methods=["GET"])
    def proxy_events():
        limit = request.args.get("limit", 50, type=int)
        event_type = request.args.get("type", None)
        events = db.get_recent_events(limit=limit, event_type=event_type)
        return jsonify({"events": events})

    @app.route("/proxy/usage", methods=["GET"])
    def proxy_usage():
        period = request.args.get("period", "day")
        if period == "day":
            since = (
                datetime.now(timezone.utc)
                .replace(hour=0, minute=0, second=0, microsecond=0)
                .timestamp()
            )
        elif period == "month":
            since = (
                datetime.now(timezone.utc)
                .replace(day=1, hour=0, minute=0, second=0, microsecond=0)
                .timestamp()
            )
        else:
            since = 0
        summary = db.get_usage_summary(since)
        return jsonify(summary)

    @app.route("/proxy/config", methods=["GET"])
    def get_proxy_config():
        return jsonify(
            {
                "budget": {
                    "daily_usd": config.budget.daily_usd,
                    "monthly_usd": config.budget.monthly_usd,
                    "action": config.budget.action,
                },
                "loop_detection": {
                    "enabled": config.loop_detection.enabled,
                    "window_seconds": config.loop_detection.window_seconds,
                    "max_similar": config.loop_detection.max_similar,
                },
                "routing_rules": len(config.routing_rules),
            }
        )

    @app.route("/proxy/config", methods=["PATCH"])
    def update_proxy_config():
        """Update proxy config at runtime (budget limits, loop detection, etc.)."""
        data = request.get_json(silent=True) or {}

        if "budget" in data:
            b = data["budget"]
            if "daily_usd" in b:
                config.budget.daily_usd = float(b["daily_usd"])
            if "monthly_usd" in b:
                config.budget.monthly_usd = float(b["monthly_usd"])
            if "action" in b:
                config.budget.action = b["action"]

        if "loop_detection" in data:
            ld = data["loop_detection"]
            if "enabled" in ld:
                config.loop_detection.enabled = ld["enabled"]
            if "window_seconds" in ld:
                config.loop_detection.window_seconds = int(ld["window_seconds"])
            if "max_similar" in ld:
                config.loop_detection.max_similar = int(ld["max_similar"])

        config.save()
        db.record_event(
            "config_updated",
            "Proxy configuration updated via API",
            severity="info",
            details=data,
        )
        return jsonify({"ok": True})

    # ── Main proxy endpoint: catch-all for /v1/* ───────────────────────

    @app.route("/v1/<path:subpath>", methods=["POST"])
    def proxy_request(subpath):
        start_time = time.time()
        path = f"/v1/{subpath}"
        req_headers = {k.lower(): v for k, v in request.headers}

        body_bytes = request.get_data()
        try:
            body = json.loads(body_bytes) if body_bytes else {}
        except json.JSONDecodeError:
            body = {}

        model = body.get("model", "unknown")
        is_streaming = body.get("stream", False)

        provider = detect_provider(path, req_headers, body)
        session_id = req_headers.get("x-session-id", "")

        with _stats_lock:
            _stats["requests"] += 1

        if config.log_requests:
            logger.info(
                f"Proxy request: {provider} {path} model={model} stream={is_streaming}"
            )

        # ── Budget check ───────────────────────────────────────────────
        allowed, reason = budget.check(model)
        if not allowed:
            with _stats_lock:
                _stats["blocked"] += 1
            db.record_event(
                "budget_blocked",
                reason,
                severity="warning",
                details={"model": model, "session_id": session_id},
            )
            logger.warning(f"Budget blocked: {reason}")

            if config.budget.action == "downgrade":
                original_model = model
                model = config.budget.downgrade_model
                body["model"] = model
                body_bytes = json.dumps(body).encode()
                db.record_event(
                    "model_downgraded",
                    f"Downgraded {original_model} -> {model} (budget)",
                    severity="info",
                    details={"original": original_model, "downgraded_to": model},
                )
            elif config.budget.action == "warn":
                pass  # Allow through with warning
            else:
                return _error_response(429, "budget_exceeded", reason, provider)

        # ── Loop detection ─────────────────────────────────────────────
        req_hash = compute_request_hash(body)
        is_loop, loop_reason = loop_detector.check(session_id, req_hash)
        if is_loop:
            with _stats_lock:
                _stats["loops_detected"] += 1
            db.record_event(
                "loop_detected",
                loop_reason,
                severity="warning",
                details={
                    "model": model,
                    "session_id": session_id,
                    "request_hash": req_hash,
                },
            )
            logger.warning(f"Loop detected: {loop_reason}")
            return _error_response(429, "loop_detected", loop_reason, provider)

        # ── Model routing ──────────────────────────────────────────────
        new_model, new_provider = router.route(model, session_id)
        if new_model:
            original_model = model
            model = new_model
            body["model"] = model
            body_bytes = json.dumps(body).encode()
            db.record_event(
                "model_routed",
                f"Routed {original_model} -> {model}",
                severity="info",
                details={"original": original_model, "routed_to": model},
            )
        if new_provider:
            provider = new_provider

        # ── Forward to upstream ────────────────────────────────────────
        api_key = _get_api_key(provider, req_headers)
        if not api_key:
            return _error_response(
                401,
                "authentication_error",
                f"No API key found for provider '{provider}'. "
                f"Set {config.providers.get(provider, ProviderConfig()).api_key_env} env var.",
                provider,
            )

        upstream_url = _get_upstream_url(provider, path)
        upstream_headers = _build_upstream_headers(provider, api_key, req_headers)

        if is_streaming:
            usage_holder = [StreamUsage()]

            def stream_generator():
                usage = StreamUsage()
                parse_fn = (
                    parse_anthropic_sse_chunk
                    if provider == "anthropic"
                    else parse_openai_sse_chunk
                )

                req = Request(
                    upstream_url,
                    data=body_bytes,
                    headers=upstream_headers,
                    method="POST",
                )
                try:
                    resp = urlopen(req, timeout=300)
                except HTTPError as e:
                    error_body = e.read()
                    yield error_body
                    usage.stop_reason = f"error_{e.code}"
                    usage_holder[0] = usage
                    return
                except URLError as e:
                    error_msg = json.dumps(
                        {"error": {"type": "proxy_error", "message": str(e)}}
                    )
                    yield error_msg.encode()
                    usage.stop_reason = "connection_error"
                    usage_holder[0] = usage
                    return

                buf = b""
                try:
                    while True:
                        chunk = resp.read(4096)
                        if not chunk:
                            break
                        yield chunk
                        buf += chunk
                        while b"\n" in buf:
                            line_bytes, buf = buf.split(b"\n", 1)
                            line = line_bytes.decode("utf-8", errors="replace").strip()
                            if line:
                                parse_fn(line, usage)
                except Exception as e:
                    logger.error(f"Stream error: {e}")
                    usage.stop_reason = "stream_error"

                usage_holder[0] = usage

            def generate_and_record():
                for chunk in stream_generator():
                    yield chunk

                usage = usage_holder[0]
                latency_ms = (time.time() - start_time) * 1000
                cost = calculate_cost(
                    usage.model or model,
                    usage.input_tokens,
                    usage.output_tokens,
                    usage.cache_read_tokens,
                    usage.cache_creation_tokens,
                )
                db.record_usage(
                    provider=provider,
                    model=usage.model or model,
                    input_tokens=usage.input_tokens,
                    output_tokens=usage.output_tokens,
                    cache_read_tokens=usage.cache_read_tokens,
                    cache_creation_tokens=usage.cache_creation_tokens,
                    cost_usd=cost,
                    session_id=session_id,
                    request_hash=req_hash,
                    latency_ms=latency_ms,
                    status=usage.stop_reason or "ok",
                )

            return Response(
                generate_and_record(),
                content_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "X-ClawMetry-Proxy": "true",
                },
            )
        else:
            resp_body, resp_status, resp_headers, usage = _forward_non_streaming(
                upstream_url, upstream_headers, body_bytes, provider
            )

            latency_ms = (time.time() - start_time) * 1000
            cost = calculate_cost(
                usage.model or model,
                usage.input_tokens,
                usage.output_tokens,
                usage.cache_read_tokens,
                usage.cache_creation_tokens,
            )
            db.record_usage(
                provider=provider,
                model=usage.model or model,
                input_tokens=usage.input_tokens,
                output_tokens=usage.output_tokens,
                cache_read_tokens=usage.cache_read_tokens,
                cache_creation_tokens=usage.cache_creation_tokens,
                cost_usd=cost,
                session_id=session_id,
                request_hash=req_hash,
                latency_ms=latency_ms,
                status=usage.stop_reason or "ok",
            )

            resp = Response(
                resp_body, status=resp_status, content_type="application/json"
            )
            resp.headers["X-ClawMetry-Proxy"] = "true"
            return resp

    # ── Maintenance thread ─────────────────────────────────────────────

    def _maintenance_loop():
        while True:
            time.sleep(3600)
            try:
                db.prune_old_data()
            except Exception as e:
                logger.error(f"Maintenance error: {e}")

    maintenance_thread = threading.Thread(target=_maintenance_loop, daemon=True)
    maintenance_thread.start()

    return app


# ── Server Runner ──────────────────────────────────────────────────────


def run_proxy(config: ProxyConfig = None, foreground: bool = True) -> None:
    """Start the proxy server."""
    if config is None:
        config = ProxyConfig.load()

    app = create_proxy_app(config)

    PROXY_PID_FILE.parent.mkdir(parents=True, exist_ok=True)
    PROXY_PID_FILE.write_text(str(os.getpid()))

    logger.info(f"ClawMetry Proxy starting on {config.host}:{config.port}")

    try:
        from waitress import serve
        serve(app, host=config.host, port=config.port,
              threads=64, channel_timeout=300,
              _quiet=not config.log_requests)
    except ImportError:
        app.run(host=config.host, port=config.port, threaded=True)
    finally:
        if PROXY_PID_FILE.exists():
            PROXY_PID_FILE.unlink(missing_ok=True)


def stop_proxy() -> bool:
    """Stop a running proxy server by PID file."""
    if not PROXY_PID_FILE.exists():
        return False

    try:
        pid = int(PROXY_PID_FILE.read_text().strip())
        os.kill(pid, 15)  # SIGTERM
        PROXY_PID_FILE.unlink(missing_ok=True)
        return True
    except (ValueError, ProcessLookupError, PermissionError):
        PROXY_PID_FILE.unlink(missing_ok=True)
        return False


def proxy_status() -> dict:
    """Check if the proxy is running."""
    if not PROXY_PID_FILE.exists():
        return {"running": False}

    try:
        pid = int(PROXY_PID_FILE.read_text().strip())
        os.kill(pid, 0)  # Check if process exists
        return {"running": True, "pid": pid}
    except (ValueError, ProcessLookupError, PermissionError):
        PROXY_PID_FILE.unlink(missing_ok=True)
        return {"running": False}


# ── CLI entry point (python -m clawmetry.proxy) ───────────────────────

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="ClawMetry Proxy Server")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument("--host", default="127.0.0.1")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    config = ProxyConfig.load()
    config.port = args.port
    config.host = args.host
    run_proxy(config)
