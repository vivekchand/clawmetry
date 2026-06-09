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

BUDGET_EXCEEDED abort contract (G3 of #1708):
    When ``budget.action == "block"`` and the daily/monthly cap is hit,
    the proxy returns HTTP 429 with a structured abort envelope so the
    agent runtime can hard-stop instead of retrying forever:

        Status: 429
        Header: X-Clawmetry-Budget-Status: exceeded
        Body  : {
            "type":  "error",
            "error": {"type": "budget_exceeded", "message": "<reason>"},
            "code":  "BUDGET_EXCEEDED",
            "should_abort":        true,
            "retry_after_seconds": null,
            "spent_today":         <float>,
            "budget_today":        <float>,
            "message":             "Daily budget reached. Halting agent. ..."
        }

    Agent runtimes SHOULD check for ``code == "BUDGET_EXCEEDED"`` (or
    the ``X-Clawmetry-Budget-Status`` header) and stop their loop.
    Runtimes that ignore these fields fall back to the legacy 429
    retry path, preserving backward compatibility with non-budget
    rate-limit semantics.
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
from typing import Dict, List, Optional, Tuple
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
_HITL_DIR = CONFIG_DIR / "hitl"


# Auto-backoff escalation ladder (#2818): minutes of cool-off by repeat count.
# 1st breach -> 5m, 2nd -> 10m, 3rd -> 20m, 4th+ -> 30m (capped).
_BACKOFF_LADDER_MINUTES = (5, 10, 20, 30)
# If a session's previous cool-off lapsed more than this long ago, it behaved
# well in between, so escalation resets to the bottom rung on its next breach
# (instead of jumping to the cap forever). Also the age past which an expired
# pause file is pruned by the maintenance loop so they can't accumulate.
_BACKOFF_RESET_SECS = 3600        # 1h quiet -> escalation decays to level 0
_BACKOFF_PRUNE_SECS = 6 * 3600    # expired >6h ago -> file pruned


def _is_session_hitl_paused(session_id: str) -> bool:
    """Return True if a session is paused for HITL review or auto-backoff.

    Two pause shapes are honored:

    1. Legacy operator pause — an empty file ``pause_<session_id>`` (no expiry).
       Stays paused until the operator deletes it (manual resume).
    2. Auto-backoff pause (#2818) — a JSON file ``pause_<session_id>.json``
       carrying ``{until_ts, level}``. The session is paused only until
       ``until_ts``; once elapsed this returns False (auto-resume). The file is
       left in place so ``_record_backoff_pause`` can read the escalation
       ``level`` on the next breach (it decays to 0 after ``_BACKOFF_RESET_SECS``
       of quiet). Long-expired files are pruned by ``_prune_backoff_pauses`` in
       the maintenance loop so they can't accumulate.

    Never crashes on bad input — a malformed JSON pause file is treated as a
    legacy/operator pause (fail safe: stay paused) so a corrupt file can't
    silently disable enforcement.
    """
    if not session_id:
        return False

    # Legacy operator pause file (no expiry) always wins.
    if (_HITL_DIR / f"pause_{session_id}").exists():
        return True

    json_path = _HITL_DIR / f"pause_{session_id}.json"
    if not json_path.exists():
        return False

    try:
        meta = json.loads(json_path.read_text())
        until_ts = float(meta.get("until_ts", 0))
    except Exception:  # noqa: BLE001 — corrupt file: fail safe, stay paused
        logger.debug("malformed auto-backoff pause file for %s; treating as paused", session_id)
        return True

    if time.time() < until_ts:
        return True

    # Cool-off elapsed: auto-resume. Leave the file so the escalation level is
    # available to _record_backoff_pause for the NEXT breach (it decays to 0
    # after _BACKOFF_RESET_SECS of quiet). _prune_backoff_pauses removes
    # long-expired files in the maintenance loop.
    return False


def _prune_backoff_pauses() -> int:
    """Delete auto-backoff pause files whose cool-off lapsed more than
    ``_BACKOFF_PRUNE_SECS`` ago, so one file per ever-tripped session can't
    accumulate forever. Returns the count removed. Never raises."""
    removed = 0
    try:
        if not _HITL_DIR.exists():
            return 0
        now = time.time()
        for p in _HITL_DIR.glob("pause_*.json"):
            try:
                until_ts = float(json.loads(p.read_text()).get("until_ts", 0))
            except Exception:  # noqa: BLE001 — corrupt file: leave it (fail-safe pause)
                continue
            if until_ts and (now - until_ts) > _BACKOFF_PRUNE_SECS:
                try:
                    p.unlink()
                    removed += 1
                except OSError:
                    pass
    except Exception as exc:  # noqa: BLE001 — never break the maintenance loop
        logger.debug("backoff-pause prune skipped: %s", exc)
    return removed


def _record_backoff_pause(session_id: str) -> Tuple[float, int]:
    """Set/escalate an auto-backoff pause for a session (#2818).

    Reads any existing ``pause_<session_id>.json`` to find the current
    escalation ``level``, bumps it, computes the new cool-off from
    ``_BACKOFF_LADDER_MINUTES``, and writes ``{until_ts, level}``. Returns
    ``(until_ts, level)``. Never crashes — on any IO/JSON error it falls back to
    the first ladder rung and logs.
    """
    json_path = _HITL_DIR / f"pause_{session_id}.json"
    prev_level = 0
    try:
        if json_path.exists():
            meta = json.loads(json_path.read_text())
            prev_level = int(meta.get("level", 0))
            prev_until = float(meta.get("until_ts", 0))
            # Escalation DECAY: if the previous cool-off lapsed more than
            # _BACKOFF_RESET_SECS ago, the agent behaved well in between, so
            # restart escalation from the bottom rung instead of jumping to the
            # cap on an isolated later breach.
            if prev_until and (time.time() - prev_until) > _BACKOFF_RESET_SECS:
                prev_level = 0
    except Exception:  # noqa: BLE001 — bad file: restart escalation at level 0
        prev_level = 0

    level = prev_level + 1
    idx = min(level - 1, len(_BACKOFF_LADDER_MINUTES) - 1)
    minutes = _BACKOFF_LADDER_MINUTES[idx]
    until_ts = time.time() + minutes * 60

    try:
        _HITL_DIR.mkdir(parents=True, exist_ok=True)
        json_path.write_text(json.dumps({"until_ts": until_ts, "level": level}))
    except Exception as exc:  # noqa: BLE001 — never break enforcement on IO error
        logger.warning("failed to write auto-backoff pause for %s: %s", session_id, exc)

    return until_ts, level


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
    per_session_usd: float = 0.0  # 0 = disabled; hard stop per-session
    action: str = "block"  # "block" | "warn" | "downgrade"
    downgrade_model: str = "claude-3-haiku-20240307"


@dataclass
class LoopDetectionConfig:
    enabled: bool = True
    window_seconds: int = 300
    max_similar: int = 5
    similarity_threshold: float = 0.85


@dataclass
class VelocityBreakerConfig:
    enabled: bool = False
    window_seconds: int = 300  # rolling window
    max_tokens: int = 0  # 0 = disabled; total input+output tokens in window


@dataclass
class RateBreakerConfig:
    """Content-agnostic rapid-fire request-rate breaker (#2817)."""

    enabled: bool = False
    window_seconds: int = 60  # rolling window
    max_requests: int = 20  # requests in window before breach


@dataclass
class CostSpiralConfig:
    """Dollar-based cost-spiral breaker (#2818)."""

    enabled: bool = False
    window_seconds: int = 300  # rolling window
    max_usd: float = 2.0  # $ spent in window before breach


@dataclass
class AutoRoutingConfig:
    """Heuristic cheap-task auto-downgrade router (#2816).

    When enabled, downgrades a request to a cheaper SAME-PROVIDER model when a
    request looks cheap/trivial: short user message, no tools, no images, short
    system prompt. ``downgrade_map`` is a per-family mapping (substring of the
    source model -> cheaper family name) so e.g. an ``opus`` model routes to
    ``haiku``. Explicit ``RoutingRule``s and budget action=downgrade still win
    (this is applied first; manual routing overrides it).
    """

    enabled: bool = False
    max_user_tokens: int = 200
    max_system_tokens: int = 500
    require_no_tools: bool = True
    include_heartbeat: bool = True  # also downgrade heartbeat-pattern requests
    downgrade_map: Dict[str, str] = field(default_factory=dict)


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
    velocity_breaker: VelocityBreakerConfig = field(default_factory=VelocityBreakerConfig)
    rate_breaker: RateBreakerConfig = field(default_factory=RateBreakerConfig)
    cost_spiral: CostSpiralConfig = field(default_factory=CostSpiralConfig)
    auto_routing: AutoRoutingConfig = field(default_factory=AutoRoutingConfig)
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
                        per_session_usd=b.get("per_session_usd", 0.0),
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

                if "velocity_breaker" in raw:
                    vb = raw["velocity_breaker"]
                    config.velocity_breaker = VelocityBreakerConfig(
                        enabled=vb.get("enabled", False),
                        window_seconds=vb.get("window_seconds", 300),
                        max_tokens=vb.get("max_tokens", 0),
                    )

                if "rate_breaker" in raw:
                    rb = raw["rate_breaker"]
                    config.rate_breaker = RateBreakerConfig(
                        enabled=rb.get("enabled", False),
                        window_seconds=rb.get("window_seconds", 60),
                        max_requests=rb.get("max_requests", 20),
                    )

                if "cost_spiral" in raw:
                    cs = raw["cost_spiral"]
                    config.cost_spiral = CostSpiralConfig(
                        enabled=cs.get("enabled", False),
                        window_seconds=cs.get("window_seconds", 300),
                        max_usd=cs.get("max_usd", 2.0),
                    )

                if "auto_routing" in raw:
                    ar = raw["auto_routing"]
                    config.auto_routing = AutoRoutingConfig(
                        enabled=ar.get("enabled", False),
                        max_user_tokens=ar.get("max_user_tokens", 200),
                        max_system_tokens=ar.get("max_system_tokens", 500),
                        require_no_tools=ar.get("require_no_tools", True),
                        include_heartbeat=ar.get("include_heartbeat", True),
                        downgrade_map=ar.get("downgrade_map", {}) or {},
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

        # #2816 auto-route env toggle (opt-in). Defaults OFF.
        if os.environ.get("CLAWMETRY_PROXY_AUTO_ROUTE"):
            config.auto_routing.enabled = (
                os.environ["CLAWMETRY_PROXY_AUTO_ROUTE"].strip().lower()
                in ("1", "true", "yes", "on")
            )

        # If the auto-router is on but no explicit downgrade_map was provided,
        # seed it from the pricing-table-derived defaults so it works out of the
        # box. Done after env so the env toggle can flip it on with no map.
        if config.auto_routing.enabled and not config.auto_routing.downgrade_map:
            try:
                from clawmetry.providers_pricing import default_auto_downgrade_map
                config.auto_routing.downgrade_map = default_auto_downgrade_map()
            except Exception as exc:  # noqa: BLE001 — never crash on config load
                logger.debug("auto-route default map load skipped: %s", exc)

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
                "per_session_usd": self.budget.per_session_usd,
                "action": self.budget.action,
                "downgrade_model": self.budget.downgrade_model,
            },
            "loop_detection": {
                "enabled": self.loop_detection.enabled,
                "window_seconds": self.loop_detection.window_seconds,
                "max_similar": self.loop_detection.max_similar,
                "similarity_threshold": self.loop_detection.similarity_threshold,
            },
            "velocity_breaker": {
                "enabled": self.velocity_breaker.enabled,
                "window_seconds": self.velocity_breaker.window_seconds,
                "max_tokens": self.velocity_breaker.max_tokens,
            },
            "rate_breaker": {
                "enabled": self.rate_breaker.enabled,
                "window_seconds": self.rate_breaker.window_seconds,
                "max_requests": self.rate_breaker.max_requests,
            },
            "cost_spiral": {
                "enabled": self.cost_spiral.enabled,
                "window_seconds": self.cost_spiral.window_seconds,
                "max_usd": self.cost_spiral.max_usd,
            },
            "auto_routing": {
                "enabled": self.auto_routing.enabled,
                "max_user_tokens": self.auto_routing.max_user_tokens,
                "max_system_tokens": self.auto_routing.max_system_tokens,
                "require_no_tools": self.auto_routing.require_no_tools,
                "include_heartbeat": self.auto_routing.include_heartbeat,
                "downgrade_map": self.auto_routing.downgrade_map,
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
                CREATE INDEX IF NOT EXISTS idx_proxy_usage_session
                    ON proxy_usage(session_id, timestamp DESC);
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

    def get_session_spending(self, session_id: str) -> float:
        """Get total USD cost for a session (all time)."""
        with self._lock:
            conn = self._connect()
            row = conn.execute(
                "SELECT COALESCE(SUM(cost_usd), 0.0) as total FROM proxy_usage WHERE session_id = ?",
                (session_id,),
            ).fetchone()
            conn.close()
            return row["total"] if row else 0.0

    def get_recent_token_count(self, session_id: str, window_seconds: int) -> int:
        """Get total input+output tokens for a session in the last window_seconds."""
        since = time.time() - window_seconds
        with self._lock:
            conn = self._connect()
            row = conn.execute(
                """SELECT COALESCE(SUM(input_tokens + output_tokens), 0) as total
                   FROM proxy_usage WHERE session_id = ? AND timestamp >= ?""",
                (session_id, since),
            ).fetchone()
            conn.close()
            return int(row["total"]) if row else 0

    def get_session_window_spending(self, session_id: str, since_ts: float) -> float:
        """Get total USD spent by one session since a timestamp (#2818).

        Per-session windowed counterpart to ``get_spending`` (which is global).
        Used by the CostSpiralBreaker so one session's burst can't be masked or
        amplified by other sessions' spend.
        """
        with self._lock:
            conn = self._connect()
            row = conn.execute(
                """SELECT COALESCE(SUM(cost_usd), 0.0) as total
                   FROM proxy_usage WHERE session_id = ? AND timestamp >= ?""",
                (session_id, since_ts),
            ).fetchone()
            conn.close()
            return float(row["total"]) if row else 0.0

    def get_recent_request_count(self, session_id: str, window_seconds: int) -> int:
        """Get the number of requests for a session in the last window_seconds.

        Content-agnostic counterpart to ``get_recent_token_count`` — used by the
        rapid-fire RateBreaker (#2817). Counts every recorded request row,
        regardless of token volume or content.
        """
        since = time.time() - window_seconds
        with self._lock:
            conn = self._connect()
            row = conn.execute(
                """SELECT COUNT(*) as cnt
                   FROM proxy_usage WHERE session_id = ? AND timestamp >= ?""",
                (session_id, since),
            ).fetchone()
            conn.close()
            return int(row["cnt"]) if row else 0

    def prune_old_data(self, retention_days: int | None = None) -> None:
        """Remove data older than the retention period.

        Per-tier retention enforcement (matches /pricing on clawmetry.com):
        Free=7d, Starter=30d, Pro=90d, Enterprise=custom (None = unlimited).
        The default reads from the install's entitlement; an explicit
        ``retention_days`` argument still wins (callers can voluntarily
        shrink, never silently expand past the tier cap).
        """
        if retention_days is None:
            # Resolve from entitlement; default to 30 (legacy fallback) if
            # the entitlement lookup fails or returns no cap.
            try:
                from clawmetry import entitlements as _ent
                tier_cap = _ent.get_entitlement().event_retention_days()
            except Exception:
                tier_cap = 30
            if tier_cap is None:
                # Enterprise / custom: read CLAWMETRY_RETENTION_DAYS or skip prune.
                env_override = os.environ.get("CLAWMETRY_RETENTION_DAYS", "").strip()
                if not env_override:
                    return
                try:
                    retention_days = max(1, int(env_override))
                except ValueError:
                    return
            else:
                # Customer can shrink via env (never expand past the tier cap).
                env_override = os.environ.get("CLAWMETRY_RETENTION_DAYS", "").strip()
                try:
                    requested = int(env_override) if env_override else tier_cap
                except ValueError:
                    requested = tier_cap
                retention_days = min(requested, tier_cap)
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


# ── Cache-bust detection (Headroom-inspired: #2839 / #2840 / #2841) ─────
# Per-session last stable-prefix hash, for prefix-drift detection. Best-effort,
# in-process, bounded; the proxy is a single long-lived process per node.
_SESSION_PREFIX: dict = {}

_VOLATILE_PATTERNS = {
    "iso_timestamp": re.compile(r"\d{4}-\d\d-\d\d[ T]\d\d:\d\d(?::\d\d)?"),
    "uuid": re.compile(
        r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-"
        r"[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b"),
    "jwt": re.compile(r"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{6,}\b"),
    "long_hex": re.compile(r"\b[0-9a-f]{32,}\b"),   # build / commit hashes
    "epoch_ms": re.compile(r"\b1[6-9]\d{11}\b"),     # 13-digit epoch ms (2022+)
}


def _sort_json(obj):
    """Recursively key-sort dicts so logically-identical structures fingerprint
    the same regardless of key order. Lists keep order (it can be meaningful)."""
    if isinstance(obj, dict):
        return {k: _sort_json(obj[k]) for k in sorted(obj.keys())}
    if isinstance(obj, list):
        return [_sort_json(x) for x in obj]
    return obj


def normalize_tools(tools) -> str:
    """Deterministic tool catalog (#2841): sort tools by name + recursively
    key-sort each schema, so defining the same tools in a different order does
    not bust the prompt cache or inflate the fingerprint. Returns a JSON string.
    Never raises."""
    try:
        if not isinstance(tools, list):
            return ""
        norm = [_sort_json(t) for t in tools if isinstance(t, dict)]
        norm.sort(key=lambda t: str(t.get("name", "")))
        return json.dumps(norm, separators=(",", ":"), ensure_ascii=False)
    except Exception:
        return ""


def scan_volatile_content(text: str) -> dict:
    """Count volatile tokens in cache-stable content (system prompt / tools) that
    silently bust the prompt cache every call (#2839 part 2). Returns per-pattern
    COUNTS only — never the matched values (they may be secrets). Never raises."""
    out: dict = {}
    try:
        if not text:
            return {}
        for name, rx in _VOLATILE_PATTERNS.items():
            n = len(rx.findall(text))
            if n:
                out[name] = n
    except Exception:
        return {}
    return out


def _system_text(body: dict) -> str:
    system = body.get("system", "")
    if isinstance(system, list):
        system = " ".join(b.get("text", "") for b in system if isinstance(b, dict))
    return system if isinstance(system, str) else ""


def stable_prefix_hash(body: dict) -> str:
    """Hash the cache-stable prefix (model + normalized tools + full system) so we
    can detect when a session's prefix DRIFTS turn-to-turn and self-busts its
    prompt cache (#2840). Tool order is normalized so reordering is not drift."""
    try:
        parts = [str(body.get("model", "")), normalize_tools(body.get("tools")),
                 _system_text(body)]
        return hashlib.sha256("|".join(parts).encode()).hexdigest()[:16]
    except Exception:
        return ""


def detect_cache_risk(body: dict) -> dict:
    """Cache-bust risk for one request: stable-prefix hash (for drift) + a
    volatile-content scan of system + tools (counts only). cache_risk_score is
    the total volatile-token count. Pure, best-effort; never raises."""
    try:
        sys_txt = _system_text(body)
        tools_txt = ""
        tools = body.get("tools")
        if isinstance(tools, list):
            try:
                tools_txt = json.dumps(tools, ensure_ascii=False)
            except Exception:
                tools_txt = ""
        volatile = scan_volatile_content(sys_txt + "\n" + tools_txt)
        return {
            "prefix_hash": stable_prefix_hash(body),
            "cache_risk_score": sum(volatile.values()),
            "volatile": volatile,
        }
    except Exception:
        return {"prefix_hash": "", "cache_risk_score": 0, "volatile": {}}


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
        # message_delta carries the running/final usage. Take the MAX so multiple
        # deltas (incl. extended-thinking reasoning streamed across blocks) never
        # undercount, and pick up cache/input token corrections if present (#2842).
        u = data.get("usage", {})
        usage.output_tokens = max(usage.output_tokens, int(u.get("output_tokens", 0) or 0))
        if u.get("input_tokens"):
            usage.input_tokens = int(u.get("input_tokens") or 0) or usage.input_tokens
        if u.get("cache_read_input_tokens"):
            usage.cache_read_tokens = int(u.get("cache_read_input_tokens") or 0) or usage.cache_read_tokens
        if u.get("cache_creation_input_tokens"):
            usage.cache_creation_tokens = int(u.get("cache_creation_input_tokens") or 0) or usage.cache_creation_tokens
        usage.stop_reason = data.get("delta", {}).get("stop_reason", "") or usage.stop_reason


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

    def check(self, model: str = "", session_id: str = "") -> Tuple[bool, str]:
        """Check if a request should be allowed.

        Returns:
            (allowed, reason) - True if allowed, reason explains why not
        """
        daily_spent = self.db.get_daily_spending()
        monthly_spent = self.db.get_monthly_spending()

        if self.config.daily_usd > 0 and daily_spent >= self.config.daily_usd:
            reason = f"Daily budget exceeded: ${daily_spent:.2f} / ${self.config.daily_usd:.2f}"
            return False, reason

        if self.config.monthly_usd > 0 and monthly_spent >= self.config.monthly_usd:
            reason = f"Monthly budget exceeded: ${monthly_spent:.2f} / ${self.config.monthly_usd:.2f}"
            return False, reason

        if session_id and self.config.per_session_usd > 0:
            session_spent = self.db.get_session_spending(session_id)
            if session_spent >= self.config.per_session_usd:
                reason = (
                    f"Per-session budget exceeded: ${session_spent:.4f} / "
                    f"${self.config.per_session_usd:.2f} for session '{session_id}'"
                )
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
            # Issue #1364: also persist to the shared DuckDB local store so
            # the dashboard can surface a "Loops detected" badge. Best-effort
            # — the proxy typically runs as its own process and the daemon
            # owns DuckDB's writer lock; in that case the open will fail and
            # we keep the legacy SQLite + log path. When proxy and daemon
            # share a process (single-process dev mode, tests), the row
            # lands in clawmetry.duckdb and the badge lights up.
            try:
                from clawmetry import local_store as _ls
                _ls.get_store().ingest_loop_signal(
                    session_id=session_id,
                    signature=request_hash,
                    repeat_count=match_count,
                    severity="warning",
                    details={"window_seconds": self.config.window_seconds},
                )
            except Exception as exc:  # noqa: BLE001 — never break detection
                logger.debug("loop signal duckdb ingest skipped: %s", exc)
            # Issue #1377: also emit a ``loop_detected`` event row so the
            # existing alert pipeline (``clawmetry/alert_evaluator.py`` driven
            # by ``clawmetry/sync.py::evaluate_alerts``) can fire a Cloud-Pro
            # rule of type ``count_over_threshold`` / ``event_type=loop_detected``
            # and fan out to Slack/email/PagerDuty. Same best-effort guard as
            # the badge write above — never let the alert hop break detection
            # or block the proxy hot path. Done inline (not threaded) because
            # ``LocalStore.ingest`` itself only appends to an in-memory ring
            # buffer and returns in microseconds; the actual DuckDB write is
            # already async on the flusher thread.
            try:
                from clawmetry import local_store as _ls
                import uuid as _uuid
                _ls.get_store().ingest({
                    "id":         _uuid.uuid4().hex,
                    "node_id":    os.environ.get("CLAWMETRY_NODE_ID") or "local",
                    "agent_id":   "clawmetry-proxy",
                    "agent_type": "openclaw",
                    "event_type": "loop_detected",
                    "ts":         datetime.now(timezone.utc).isoformat(),
                    "session_id": session_id,
                    "data": {
                        "signature":      request_hash,
                        "repeat_count":   match_count,
                        "window_seconds": self.config.window_seconds,
                        "reason":         reason,
                    },
                })
            except Exception as exc:  # noqa: BLE001 — never break detection
                logger.debug("loop_detected alert event skipped: %s", exc)
            return True, reason

        return False, ""


# ── Velocity Breaker ───────────────────────────────────────────────────


class VelocityBreaker:
    """Halts agents whose token burn-rate exceeds a rolling-window threshold."""

    def __init__(self, config: VelocityBreakerConfig, db: ProxyDB):
        self.config = config
        self.db = db

    def check(self, session_id: str) -> Tuple[bool, str]:
        """Check if this session is burning tokens too fast.

        Returns:
            (is_spike, reason) - True if velocity limit exceeded
        """
        if not self.config.enabled or not self.config.max_tokens or not session_id:
            return False, ""

        recent_tokens = self.db.get_recent_token_count(
            session_id, self.config.window_seconds
        )

        if recent_tokens >= self.config.max_tokens:
            reason = (
                f"Token velocity exceeded: {recent_tokens:,} tokens from session "
                f"'{session_id}' in the last {self.config.window_seconds}s "
                f"(limit: {self.config.max_tokens:,})"
            )
            try:
                from clawmetry import local_store as _ls
                import uuid as _uuid
                _ls.get_store().ingest({
                    "id":         _uuid.uuid4().hex,
                    "node_id":    os.environ.get("CLAWMETRY_NODE_ID") or "local",
                    "agent_id":   "clawmetry-proxy",
                    "agent_type": "openclaw",
                    "event_type": "velocity_exceeded",
                    "ts":         datetime.now(timezone.utc).isoformat(),
                    "session_id": session_id,
                    "data": {
                        "recent_tokens":   recent_tokens,
                        "max_tokens":      self.config.max_tokens,
                        "window_seconds":  self.config.window_seconds,
                        "reason":          reason,
                    },
                })
            except Exception as exc:  # noqa: BLE001 — never break enforcement
                logger.debug("velocity_exceeded event skipped: %s", exc)
            return True, reason

        return False, ""


def _emit_duckdb_event(event_type: str, session_id: str, data: dict) -> None:
    """Best-effort emit an enforcement event into the shared DuckDB store.

    Mirrors the ingest pattern used by LoopDetector / VelocityBreaker so the
    dashboard + alert pipeline can surface proxy enforcement. Never raises — the
    proxy typically runs as its own process and the daemon owns DuckDB's writer
    lock, so this may no-op; that's fine, the SQLite ``proxy_events`` row + log
    still record it.
    """
    try:
        from clawmetry import local_store as _ls
        import uuid as _uuid
        _ls.get_store().ingest({
            "id":         _uuid.uuid4().hex,
            "node_id":    os.environ.get("CLAWMETRY_NODE_ID") or "local",
            "agent_id":   "clawmetry-proxy",
            "agent_type": "openclaw",
            "event_type": event_type,
            "ts":         datetime.now(timezone.utc).isoformat(),
            "session_id": session_id,
            "data":       data,
        })
    except Exception as exc:  # noqa: BLE001 — never break enforcement
        logger.debug("%s duckdb event skipped: %s", event_type, exc)


# ── Rate Breaker (rapid-fire request count, content-agnostic) ──────────


class RateBreaker:
    """Halts agents firing too many requests per window, regardless of size.

    Content-agnostic counterpart to VelocityBreaker (which counts tokens): this
    counts raw request volume (#2817). Useful against tight retry loops that
    each spend little but hammer the upstream.
    """

    def __init__(self, config: RateBreakerConfig, db: ProxyDB):
        self.config = config
        self.db = db

    def check(self, session_id: str) -> Tuple[bool, str]:
        """Check if this session is firing requests too fast.

        Returns:
            (is_breach, reason) - True if request-rate limit exceeded
        """
        if not self.config.enabled or not self.config.max_requests or not session_id:
            return False, ""

        try:
            recent = self.db.get_recent_request_count(
                session_id, self.config.window_seconds
            )
        except Exception as exc:  # noqa: BLE001 — never break enforcement
            logger.debug("rate breaker count failed: %s", exc)
            return False, ""

        # >= because the current request is the (recent+1)th; tripping at the
        # configured ceiling means the 21st request with max_requests=20 blocks
        # once 20 are already recorded.
        if recent >= self.config.max_requests:
            reason = (
                f"Request rate exceeded: {recent:,} requests from session "
                f"'{session_id}' in the last {self.config.window_seconds}s "
                f"(limit: {self.config.max_requests:,})"
            )
            _emit_duckdb_event("rate_exceeded", session_id, {
                "recent_requests": recent,
                "max_requests":    self.config.max_requests,
                "window_seconds":  self.config.window_seconds,
                "reason":          reason,
            })
            return True, reason

        return False, ""


# ── Cost-Spiral Breaker (dollar burn-rate) ─────────────────────────────


class CostSpiralBreaker:
    """Halts a session whose dollar spend in a rolling window exceeds a cap.

    Where VelocityBreaker watches token count and RateBreaker watches request
    count, this watches actual USD burn (#2818). On breach the handler also
    arms an escalating auto-backoff pause for the session.
    """

    def __init__(self, config: CostSpiralConfig, db: ProxyDB):
        self.config = config
        self.db = db

    def check(self, session_id: str) -> Tuple[bool, str]:
        """Check if this session is spending money too fast.

        Returns:
            (is_breach, reason) - True if cost-spiral limit exceeded
        """
        if not self.config.enabled or self.config.max_usd <= 0 or not session_id:
            return False, ""

        try:
            since = time.time() - self.config.window_seconds
            recent_usd = self.db.get_session_window_spending(
                session_id, since
            )
        except Exception as exc:  # noqa: BLE001 — never break enforcement
            logger.debug("cost spiral spend lookup failed: %s", exc)
            return False, ""

        if recent_usd >= self.config.max_usd:
            reason = (
                f"Cost spiral detected: ${recent_usd:.2f} spent by session "
                f"'{session_id}' in the last {self.config.window_seconds}s "
                f"(limit: ${self.config.max_usd:.2f})"
            )
            _emit_duckdb_event("cost_spiral", session_id, {
                "recent_usd":     round(recent_usd, 4),
                "max_usd":        self.config.max_usd,
                "window_seconds": self.config.window_seconds,
                "reason":         reason,
            })
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


# ── Auto Router (heuristic cheap-task downgrade) ───────────────────────


def _estimate_tokens(text: str) -> int:
    """Cheap char/4 token estimate (no tokenizer dependency)."""
    if not text:
        return 0
    return max(0, len(text) // 4)


# Heartbeat / keep-alive style prompts that are cheap by nature (#2816).
_HEARTBEAT_PATTERNS = (
    "heartbeat",
    "are you there",
    "ping",
    "still working",
    "continue",
    "ok?",
)


def _body_user_text(body: dict) -> str:
    """Extract the last user-message text from an Anthropic/OpenAI body."""
    messages = body.get("messages") or []
    if not messages:
        return ""
    last = messages[-1] if isinstance(messages[-1], dict) else {}
    content = last.get("content", "")
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return " ".join(
            b.get("text", "")
            for b in content
            if isinstance(b, dict) and b.get("type") in (None, "text")
        )
    return str(content)


def _body_system_text(body: dict) -> str:
    """Extract the system prompt text from an Anthropic/OpenAI body."""
    system = body.get("system", "")
    if isinstance(system, list):
        return " ".join(
            b.get("text", "") for b in system if isinstance(b, dict)
        )
    if isinstance(system, str) and system:
        return system
    # OpenAI carries the system prompt as a message with role=system.
    for m in body.get("messages") or []:
        if isinstance(m, dict) and m.get("role") == "system":
            c = m.get("content", "")
            return c if isinstance(c, str) else str(c)
    return ""


def _body_has_tools(body: dict) -> bool:
    """True if the request defines tools/functions (Anthropic or OpenAI)."""
    return bool(body.get("tools") or body.get("functions"))


def _body_has_images(body: dict) -> bool:
    """True if any message carries an image/non-text content block."""
    for m in body.get("messages") or []:
        if not isinstance(m, dict):
            continue
        content = m.get("content")
        if isinstance(content, list):
            for b in content:
                if not isinstance(b, dict):
                    continue
                btype = b.get("type", "")
                if btype in ("image", "image_url", "input_image") or "image" in btype:
                    return True
    return False


class AutoRouter:
    """Heuristic cheap-task auto-downgrade router (#2816).

    Inspects the parsed request body and, when ALL cheap-task conditions hold
    (short user message, no tools, no images, short system prompt) — or it
    matches a heartbeat pattern when ``include_heartbeat`` is set — returns a
    cheaper SAME-PROVIDER model. Applied BEFORE the manual ModelRouter so
    explicit routing rules still win.
    """

    def __init__(self, config: AutoRoutingConfig):
        self.config = config

    def route(self, model: str, body: dict) -> Tuple[Optional[str], str]:
        """Return (downgraded_model, reason) or (None, '') if not downgraded."""
        if not self.config.enabled or not model:
            return None, ""

        try:
            user_text = _body_user_text(body)
            user_tokens = _estimate_tokens(user_text)
            system_tokens = _estimate_tokens(_body_system_text(body))
            has_tools = _body_has_tools(body)
            has_images = _body_has_images(body)

            # HARD disqualifiers — NEVER downgrade a request carrying images, or
            # tools when require_no_tools is set: a weaker model handles them
            # worse and this would be silent data-loss. Applies to BOTH the
            # cheap-task AND the heartbeat path, because a short
            # "continue"/"ok?"/"ping" turn in agent tool-use carries the FULL
            # tool set (and matches a heartbeat pattern) — without this gate it
            # would be downgraded mid-tool-loop.
            blocked = has_images or (has_tools and self.config.require_no_tools)

            is_heartbeat = self.config.include_heartbeat and any(
                p in user_text.lower() for p in _HEARTBEAT_PATTERNS
            ) and user_tokens <= self.config.max_user_tokens

            cheap = (
                user_tokens <= self.config.max_user_tokens
                and system_tokens <= self.config.max_system_tokens
                and not has_images
                and (not has_tools or not self.config.require_no_tools)
            )

            if blocked or not (cheap or is_heartbeat):
                return None, ""

            from clawmetry.providers_pricing import downgrade_model_name
            target = downgrade_model_name(model, self.config.downgrade_map or None)
            if not target or target.lower() == model.lower():
                return None, ""

            reason = (
                f"Auto-downgraded {model} -> {target} "
                f"(cheap task: user~{user_tokens}tok, sys~{system_tokens}tok, "
                f"tools={has_tools}, images={has_images}, heartbeat={is_heartbeat})"
            )
            return target, reason
        except Exception as exc:  # noqa: BLE001 — never break the request path
            logger.debug("auto-route skipped: %s", exc)
            return None, ""


def _estimate_saved_usd(from_model: str, to_model: str, est_input_tokens: int) -> float:
    """Rough $ saved estimate for an auto-downgrade (input-side only).

    Uses the proxy's MODEL_PRICING input rate delta over the estimated input
    token count. Best-effort — never raises.
    """
    try:
        def _input_rate(m: str) -> float:
            ml = m.lower()
            for key, prices in MODEL_PRICING.items():
                if key == "default":
                    continue
                if key in ml:
                    return prices[0]
            return MODEL_PRICING["default"][0]

        delta = max(0.0, _input_rate(from_model) - _input_rate(to_model))
        return round((est_input_tokens / 1_000_000) * delta, 6)
    except Exception:
        return 0.0


# ── Proxy Server (Flask) ───────────────────────────────────────────────


def create_proxy_app(config: ProxyConfig = None) -> "Flask":
    """Create the Flask proxy application."""
    from flask import Flask, request, Response, jsonify

    if config is None:
        config = ProxyConfig.load()

    app = Flask(__name__)
    app.config["MAX_CONTENT_LENGTH"] = 50 * 1024 * 1024  # 50MB max

    # Open-core plugin host: the enforcement proxy is a SEPARATE long-running
    # process (``python -m clawmetry.proxy``) from the dashboard and the sync
    # daemon, so its Flask app needs its own ``load_plugins(app)`` call.
    # Without this, a clawmetry-pro plugin that ships custom policy / routing
    # blueprints (e.g. budget overrides, tool-policy enforcement endpoints)
    # would register on the dashboard process but be missing here — the proxy
    # would silently fall back to OSS behaviour. The extensions module's
    # ``_loaded`` guard makes the call safe across processes (it is per-process
    # state). Errors are swallowed with a warning: a broken plugin must never
    # take the proxy down — it is the LLM-egress chokepoint.
    try:
        from clawmetry.extensions import load_plugins as _ext_load

        _ext_load(app)
    except Exception as _ext_e:
        logger.warning("extensions load_plugins failed: %s", _ext_e)

    db = ProxyDB()
    budget = BudgetEnforcer(config.budget, db)
    loop_detector = LoopDetector(config.loop_detection, db)
    velocity_breaker = VelocityBreaker(config.velocity_breaker, db)
    rate_breaker = RateBreaker(config.rate_breaker, db)
    cost_spiral_breaker = CostSpiralBreaker(config.cost_spiral, db)
    auto_router = AutoRouter(config.auto_routing)
    router = ModelRouter(config.routing_rules)

    _stats = {
        "requests": 0,
        "blocked": 0,
        "loops_detected": 0,
        "velocity_blocked": 0,
        "rate_blocked": 0,
        "cost_spiral_blocked": 0,
        "auto_downgraded": 0,
        "started_at": time.time(),
    }
    _stats_lock = threading.Lock()

    def _error_response(
        status_code: int,
        error_type: str,
        message: str,
        provider: str = "anthropic",
        extra: Optional[dict] = None,
        extra_headers: Optional[dict] = None,
    ) -> Response:
        """
        Return an error response in the provider's expected format.

        ``extra``: top-level fields merged into the JSON body (used to surface
        the structured ``BUDGET_EXCEEDED`` abort envelope per G3 of #1708).
        ``extra_headers``: additional response headers (e.g.
        ``X-Clawmetry-Budget-Status: exceeded`` so HTTP clients that respect
        headers can short-circuit retries without parsing the body).
        """
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
        if extra:
            body.update(extra)
        resp = Response(
            json.dumps(body),
            status=status_code,
            content_type="application/json",
        )
        if extra_headers:
            for k, v in extra_headers.items():
                resp.headers[k] = v
        return resp

    def _arm_backoff_pause(session_id: str, trigger: str, reason: str) -> None:
        """Arm an escalating auto-backoff pause for a session (#2818).

        Called when loop/rate/cost_spiral fires. Writes a HITL-style pause with
        an escalating expiry (5/10/20/30 min by repeat count) keyed by session,
        which ``_is_session_hitl_paused`` honors (auto-resume once elapsed).
        Best-effort — never breaks the request path.
        """
        if not session_id:
            return
        try:
            until_ts, level = _record_backoff_pause(session_id)
            db.record_event(
                "session_auto_paused",
                f"Session '{session_id}' auto-paused (level {level}) after {trigger}",
                severity="warning",
                details={
                    "session_id": session_id,
                    "trigger": trigger,
                    "level": level,
                    "until_ts": until_ts,
                    "reason": reason,
                },
            )
            _emit_duckdb_event("session_auto_paused", session_id, {
                "trigger": trigger,
                "level": level,
                "until_ts": until_ts,
                "reason": reason,
            })
        except Exception as exc:  # noqa: BLE001 — never break enforcement
            logger.debug("arm backoff pause skipped: %s", exc)

    def _budget_abort_response(reason: str, provider: str) -> Response:
        """Structured BUDGET_EXCEEDED abort signal (G3 of #1708).

        Agent runtimes that wrap the proxy should branch on either
        ``code == "BUDGET_EXCEEDED"`` in the JSON body or the
        ``X-Clawmetry-Budget-Status: exceeded`` response header and STOP
        their retry loop. Plain 429 retry behaviour is preserved for
        runtimes that do not read these fields, so the contract is
        backward compatible with non-budget rate limits.
        """
        status = budget.get_status()
        spent = status.get("daily_spent", 0.0)
        limit = status.get("daily_limit", 0.0)
        message = (
            "Daily budget reached. Halting agent. "
            "Raise the budget in ClawMetry Cloud settings to resume."
        )
        extra = {
            "code":                "BUDGET_EXCEEDED",
            "should_abort":        True,
            "retry_after_seconds": None,
            "spent_today":         spent,
            "budget_today":        limit,
            "message":             message,
        }
        return _error_response(
            429,
            "budget_exceeded",
            reason,
            provider,
            extra=extra,
            extra_headers={"X-Clawmetry-Budget-Status": "exceeded"},
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
                "velocity_blocked": stats["velocity_blocked"],
                "rate_blocked": stats.get("rate_blocked", 0),
                "cost_spiral_blocked": stats.get("cost_spiral_blocked", 0),
                "auto_downgraded": stats.get("auto_downgraded", 0),
                "budget": budget.get_status(),
                "config": {
                    "port": config.port,
                    "host": config.host,
                    "budget_action": config.budget.action,
                    "per_session_usd": config.budget.per_session_usd,
                    "loop_detection": config.loop_detection.enabled,
                    "velocity_breaker": {
                        "enabled": config.velocity_breaker.enabled,
                        "window_seconds": config.velocity_breaker.window_seconds,
                        "max_tokens": config.velocity_breaker.max_tokens,
                    },
                    "rate_breaker": {
                        "enabled": config.rate_breaker.enabled,
                        "window_seconds": config.rate_breaker.window_seconds,
                        "max_requests": config.rate_breaker.max_requests,
                    },
                    "cost_spiral": {
                        "enabled": config.cost_spiral.enabled,
                        "window_seconds": config.cost_spiral.window_seconds,
                        "max_usd": config.cost_spiral.max_usd,
                    },
                    "auto_routing": {
                        "enabled": config.auto_routing.enabled,
                        "max_user_tokens": config.auto_routing.max_user_tokens,
                        "max_system_tokens": config.auto_routing.max_system_tokens,
                    },
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
            if "per_session_usd" in b:
                config.budget.per_session_usd = float(b["per_session_usd"])
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

        if "velocity_breaker" in data:
            vb = data["velocity_breaker"]
            if "enabled" in vb:
                config.velocity_breaker.enabled = bool(vb["enabled"])
            if "window_seconds" in vb:
                config.velocity_breaker.window_seconds = int(vb["window_seconds"])
            if "max_tokens" in vb:
                config.velocity_breaker.max_tokens = int(vb["max_tokens"])

        if "rate_breaker" in data:
            rb = data["rate_breaker"]
            if "enabled" in rb:
                config.rate_breaker.enabled = bool(rb["enabled"])
            if "window_seconds" in rb:
                config.rate_breaker.window_seconds = int(rb["window_seconds"])
            if "max_requests" in rb:
                config.rate_breaker.max_requests = int(rb["max_requests"])

        if "cost_spiral" in data:
            cs = data["cost_spiral"]
            if "enabled" in cs:
                config.cost_spiral.enabled = bool(cs["enabled"])
            if "window_seconds" in cs:
                config.cost_spiral.window_seconds = int(cs["window_seconds"])
            if "max_usd" in cs:
                config.cost_spiral.max_usd = float(cs["max_usd"])

        if "auto_routing" in data:
            ar = data["auto_routing"]
            if "enabled" in ar:
                config.auto_routing.enabled = bool(ar["enabled"])
            if "max_user_tokens" in ar:
                config.auto_routing.max_user_tokens = int(ar["max_user_tokens"])
            if "max_system_tokens" in ar:
                config.auto_routing.max_system_tokens = int(ar["max_system_tokens"])
            if "require_no_tools" in ar:
                config.auto_routing.require_no_tools = bool(ar["require_no_tools"])
            if "downgrade_map" in ar and isinstance(ar["downgrade_map"], dict):
                config.auto_routing.downgrade_map = ar["downgrade_map"]

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

        # ── Auto smart routing (#2816) ─────────────────────────────────
        # Applied FIRST so cheap-task requests start on a cheaper model. Budget
        # action=downgrade (below) and explicit ModelRouter rules (later) both
        # run AFTER this, so they take precedence and override the auto choice.
        auto_model, auto_reason = auto_router.route(model, body)
        if auto_model:
            from_model = model
            est_input = _estimate_tokens(_body_user_text(body)) + _estimate_tokens(
                _body_system_text(body)
            )
            saved = _estimate_saved_usd(from_model, auto_model, est_input)
            model = auto_model
            body["model"] = model
            body_bytes = json.dumps(body).encode()
            with _stats_lock:
                _stats["auto_downgraded"] += 1
            db.record_event(
                "auto_downgraded",
                auto_reason,
                severity="info",
                details={
                    "from_model": from_model,
                    "to_model": model,
                    "session_id": session_id,
                    "estimated_saved_usd": saved,
                },
            )
            _emit_duckdb_event("auto_downgraded", session_id, {
                "from_model": from_model,
                "to_model": model,
                "estimated_saved_usd": saved,
                "reason": auto_reason,
            })
            if config.log_requests:
                logger.info("Auto-route: %s", auto_reason)

        # ── Budget check ───────────────────────────────────────────────
        allowed, reason = budget.check(model, session_id)
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
                return _budget_abort_response(reason, provider)

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
            _arm_backoff_pause(session_id, "loop_detected", loop_reason)
            return _error_response(429, "loop_detected", loop_reason, provider)

        # ── Rate breaker (#2817): rapid-fire request count ─────────────
        is_rate, rate_reason = rate_breaker.check(session_id)
        if is_rate:
            with _stats_lock:
                _stats["rate_blocked"] += 1
            db.record_event(
                "rate_exceeded",
                rate_reason,
                severity="warning",
                details={"model": model, "session_id": session_id},
            )
            logger.warning(f"Rate exceeded: {rate_reason}")
            _arm_backoff_pause(session_id, "rate_exceeded", rate_reason)
            return _error_response(429, "rate_exceeded", rate_reason, provider)

        # ── Cost-spiral breaker (#2818): dollar burn-rate ──────────────
        is_spiral, spiral_reason = cost_spiral_breaker.check(session_id)
        if is_spiral:
            with _stats_lock:
                _stats["cost_spiral_blocked"] += 1
            db.record_event(
                "cost_spiral",
                spiral_reason,
                severity="warning",
                details={"model": model, "session_id": session_id},
            )
            logger.warning(f"Cost spiral: {spiral_reason}")
            _arm_backoff_pause(session_id, "cost_spiral", spiral_reason)
            return _error_response(429, "cost_spiral", spiral_reason, provider)
        # ── Cache-bust risk (Headroom-inspired, #2839/#2840) ───────────
        # Detect prompts that self-bust the prompt cache: volatile content in the
        # cache-stable prefix (timestamps/UUIDs/JWTs) and prefix DRIFT turn over
        # turn. Detection only (never blocks, never stores raw prompt text); the
        # re-read-tax meter reads the emitted events.
        try:
            _risk = detect_cache_risk(body)
            _ph = _risk.get("prefix_hash") or ""
            _prev = _SESSION_PREFIX.get(session_id) if session_id else None
            if session_id and _ph:
                if len(_SESSION_PREFIX) > 2000:
                    _SESSION_PREFIX.clear()
                _SESSION_PREFIX[session_id] = _ph
            _drift = bool(_prev and _ph and _prev != _ph)
            if _drift or _risk.get("cache_risk_score", 0) >= 3:
                db.record_event(
                    "cache_risk",
                    ("prompt prefix drifted between turns (self-busting the cache)"
                     if _drift else "volatile content in the cache-stable prefix"),
                    severity="info",
                    details={
                        "session_id": session_id,
                        "model": model,
                        "cache_risk_score": _risk.get("cache_risk_score", 0),
                        "volatile": _risk.get("volatile", {}),
                        "prefix_drift": _drift,
                    },
                )
        except Exception as _exc:  # noqa: BLE001 — never break the proxy
            logger.debug("cache-risk detection skipped: %s", _exc)

        # ── Velocity check ─────────────────────────────────────────────
        is_spike, spike_reason = velocity_breaker.check(session_id)
        if is_spike:
            with _stats_lock:
                _stats["velocity_blocked"] += 1
            db.record_event(
                "velocity_exceeded",
                spike_reason,
                severity="warning",
                details={"model": model, "session_id": session_id},
            )
            logger.warning(f"Velocity exceeded: {spike_reason}")
            return _error_response(429, "velocity_exceeded", spike_reason, provider)

        # ── HITL / auto-backoff pause check ────────────────────────────
        # Honors both legacy operator pauses (manual resume) and auto-backoff
        # pauses (#2818, escalating expiry, auto-resume once elapsed).
        if _is_session_hitl_paused(session_id):
            with _stats_lock:
                _stats["blocked"] += 1
            # Surface auto-resume time + retry-after when this is a backoff pause.
            retry_after = None
            json_path = _HITL_DIR / f"pause_{session_id}.json"
            try:
                if json_path.exists():
                    until_ts = float(json.loads(json_path.read_text()).get("until_ts", 0))
                    retry_after = max(0, int(round(until_ts - time.time())))
            except Exception:  # noqa: BLE001
                retry_after = None
            db.record_event(
                "session_paused",
                f"Session '{session_id}' paused (HITL / auto-backoff)",
                severity="warning",
                details={
                    "model": model,
                    "session_id": session_id,
                    "retry_after_seconds": retry_after,
                },
            )
            logger.warning("Session '%s' blocked: paused (retry_after=%s)", session_id, retry_after)
            msg = (
                f"Session '{session_id}' is paused. "
                + (
                    f"Auto-resumes in ~{retry_after}s."
                    if retry_after is not None
                    else "Approve or reject via POST /api/hitl/decide."
                )
            )
            extra_headers = (
                {"Retry-After": str(retry_after)} if retry_after is not None else None
            )
            return _error_response(
                429,
                "session_paused",
                msg,
                provider,
                extra={"retry_after_seconds": retry_after},
                extra_headers=extra_headers,
            )

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
            try:
                # Prune long-expired auto-backoff pause files so one per
                # ever-tripped session can't accumulate (#2818).
                n = _prune_backoff_pauses()
                if n:
                    logger.info("pruned %d expired auto-backoff pause file(s)", n)
            except Exception as e:
                logger.error(f"Backoff-pause prune error: {e}")

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
