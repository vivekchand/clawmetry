"""Weekly Insights Digest — LLM-over-DuckDB summary of the last 7 days.

First piece of the "AI wiki over your agent data" moat: 10 hand-authored
SELECT templates run on the local DuckDB store, results are fed to Claude
Sonnet for synthesis, output dispatched via channel adapters (Pro) or
rendered at ``/insights`` (OSS).

Safety: SQL templates are STATIC and pass ``dives_sql_safety.validate_sql``
at import. The LLM never generates SQL — only summarises rows. This sidesteps
the AI-SQL prompt-injection class (Vanna.AI CVE-2024-5565 et al).

Hallucination guardrail: every narrative is paired with the raw rows it
summarised — auditable in the UI; rows are source of truth.

Cost: ~$0.05–$0.60/user/week (synthesis only; templates are free).

Gate: ``CLAWMETRY_INSIGHTS=1`` for v1 soak. Per-Pro flip-on follows
``project_alerts_pro_feature.md`` after 1-week soak.

Config: ``~/.openclaw/.clawmetry/insights_config.json``.
"""
from __future__ import annotations

import datetime
import json
import logging
import os
import time
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

log = logging.getLogger("clawmetry.insights")

# ── Config / paths ─────────────────────────────────────────────────────────

_WORKSPACE = os.environ.get("OPENCLAW_HOME") or os.path.expanduser("~/.openclaw")
CONFIG_PATH = Path(_WORKSPACE) / ".clawmetry" / "insights_config.json"

SYNTHESIS_MODEL = "claude-3-5-sonnet-20241022"
ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"
ANTHROPIC_VERSION = "2023-06-01"
SYNTHESIS_TIMEOUT_SECS = 30
SQL_TIMEOUT_SECS = 5


# ── Data shapes ────────────────────────────────────────────────────────────


@dataclass
class InsightResult:
    """One canned-prompt's contribution to the digest.

    ``rows`` is the raw DuckDB result — the hallucination guardrail. The UI
    renders ``narrative`` over ``rows`` so the operator can spot-check.
    """
    key: str
    title: str
    narrative: str
    rows: list[dict]
    error: str | None = None


@dataclass
class WeeklyDigest:
    generated_at: str
    week_start: str
    week_end: str
    insights: list[InsightResult] = field(default_factory=list)
    summary: str = ""
    cost_usd: float = 0.0
    tokens_used: int = 0

    def to_dict(self) -> dict:
        return {
            "generated_at": self.generated_at,
            "week_start": self.week_start,
            "week_end": self.week_end,
            "summary": self.summary,
            "cost_usd": round(self.cost_usd, 4),
            "tokens_used": self.tokens_used,
            "insights": [asdict(i) for i in self.insights],
        }

    def to_text(self) -> str:
        """Plain-text form for email / Slack / Telegram bodies."""
        lines = [
            f"ClawMetry Weekly Insights — Week of {self.week_start}",
            "",
            self.summary or "(no summary)",
            "",
        ]
        for ins in self.insights:
            lines.append(f"## {ins.title}")
            lines.append(ins.narrative or "(no data)")
            lines.append("")
        lines.append(f"Generated {self.generated_at}.")
        return "\n".join(lines)


# ── Canned insight prompts (10) ────────────────────────────────────────────
# Each: (key, title, sql_template, synthesis_hint). Templates use $name
# DuckDB bind params filled in by ``_bind_params``.

_INSIGHT_TEMPLATES: list[tuple[str, str, str, str]] = [
    (
        "top_cost_drivers",
        "Top cost drivers (tool × model)",
        """
        SELECT model,
               COALESCE(json_extract_string(data, '$.tool_name'), 'unknown') AS tool,
               SUM(cost_usd) AS cost,
               COUNT(*) AS calls
        FROM events
        WHERE ts >= $since AND cost_usd > 0
        GROUP BY model, tool
        ORDER BY cost DESC
        LIMIT 3
        """,
        "Name each driver, dollar cost, call count. Flag if any single driver > 40% of total.",
    ),
    (
        "wow_change",
        "Week-over-week change",
        """
        WITH win AS (
          SELECT
            CASE WHEN ts >= $since THEN 'this' ELSE 'prev' END AS bucket,
            cost_usd, token_count, session_id
          FROM events
          WHERE ts >= $prev_since AND ts <= $now_ts
        )
        SELECT bucket,
               COALESCE(SUM(cost_usd), 0) AS cost,
               COALESCE(SUM(token_count), 0) AS tokens,
               COUNT(DISTINCT session_id) AS sessions,
               COUNT(*) AS events
        FROM win
        GROUP BY bucket
        """,
        "Report this-week totals, % change vs previous week, and cost-per-event change.",
    ),
    (
        "anomalous_sessions",
        "Anomalous sessions",
        """
        SELECT session_id,
               COUNT(*) AS events,
               SUM(CASE WHEN event_type LIKE '%error%' THEN 1 ELSE 0 END) AS errors,
               SUM(cost_usd) AS cost
        FROM events
        WHERE ts >= $since AND session_id IS NOT NULL
        GROUP BY session_id
        HAVING errors > 0 OR events > 500
        ORDER BY errors DESC, events DESC
        LIMIT 5
        """,
        "List sessions with > 0 errors or > 500 events. Truncate session_id to first 6 chars.",
    ),
    (
        "new_tools",
        "New tools used this week",
        """
        WITH this_week AS (
          SELECT DISTINCT json_extract_string(data, '$.tool_name') AS tool
          FROM events
          WHERE ts >= $since
            AND json_extract_string(data, '$.tool_name') IS NOT NULL
        ),
        prior AS (
          SELECT DISTINCT json_extract_string(data, '$.tool_name') AS tool
          FROM events
          WHERE ts < $since AND ts >= $prior_window_start
            AND json_extract_string(data, '$.tool_name') IS NOT NULL
        )
        SELECT t.tool FROM this_week t
        LEFT JOIN prior p ON t.tool = p.tool
        WHERE p.tool IS NULL AND t.tool != ''
        LIMIT 10
        """,
        "List any tool names that are new vs the prior 4-week window. Say 'none' if empty.",
    ),
    (
        "subagent_regressions",
        "Subagent performance regressions",
        """
        SELECT task,
               COUNT(*) AS runs,
               AVG(cost_usd) AS avg_cost,
               AVG(token_count) AS avg_tokens
        FROM subagents
        WHERE spawned_at >= $since
        GROUP BY task
        ORDER BY runs DESC
        LIMIT 5
        """,
        "Highlight any subagent task whose avg_cost is > 2x median across the row set.",
    ),
    (
        "approval_health",
        "Approval queue health",
        """
        SELECT
          COUNT(*) AS total,
          SUM(CASE WHEN decision = 'approved' THEN 1 ELSE 0 END) AS approved,
          SUM(CASE WHEN decision = 'denied' THEN 1 ELSE 0 END) AS denied,
          SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) AS pending
        FROM approvals
        WHERE created_at >= $since_str
        """,
        "Report total, approval ratio, deny rate, pending count. Skip if total=0.",
    ),
    (
        "alert_fires",
        "Alert fire history",
        """
        SELECT name,
               fire_count,
               last_fired_at
        FROM alert_rules
        WHERE last_fired_at >= $since_str OR fire_count > 0
        ORDER BY fire_count DESC
        LIMIT 5
        """,
        "List rules that fired and how many times. If empty, say 'no alerts tripped'.",
    ),
    (
        "model_fallbacks",
        "Model fallback frequency",
        """
        SELECT model,
               COUNT(*) AS uses,
               SUM(cost_usd) AS cost
        FROM events
        WHERE ts >= $since AND model IS NOT NULL
        GROUP BY model
        ORDER BY uses DESC
        LIMIT 6
        """,
        "If Haiku/Sonnet appear alongside Opus, estimate $$ saved by the cheaper fallbacks.",
    ),
    (
        "channel_activity",
        "Channel activity",
        """
        SELECT provider,
               COUNT(*) AS msgs,
               SUM(CASE WHEN direction='inbound' THEN 1 ELSE 0 END) AS inbound
        FROM channel_messages
        WHERE ts >= $since
        GROUP BY provider
        ORDER BY msgs DESC
        LIMIT 8
        """,
        "Rank channels by inbound volume; call out any new provider not seen before.",
    ),
    (
        "trend_summary",
        "The week in 30 seconds",
        """
        SELECT
          COUNT(*) AS events,
          COUNT(DISTINCT session_id) AS sessions,
          SUM(cost_usd) AS cost,
          SUM(token_count) AS tokens
        FROM events
        WHERE ts >= $since
        """,
        "One short paragraph: total events, sessions, cost, tokens. Punchy.",
    ),
]


# ── SQL safety: validate templates at import time ──────────────────────────


def _validate_templates_once() -> None:
    """Crash-on-import if a template fails ``dives_sql_safety.validate_sql``."""
    try:
        from clawmetry.dives_sql_safety import validate_sql
    except Exception:
        return  # validator unavailable; safety relies on hand-authoring
    for key, _title, sql, _hint in _INSIGHT_TEMPLATES:
        # Strip the $param tokens — sqlglot doesn't recognise our $since/$prev_since
        # placeholder; replace with a literal so the SELECT-only check still runs.
        sanitized = (
            sql.replace("$since", "'2026-01-01T00:00:00Z'")
               .replace("$prev_since", "'2025-12-25T00:00:00Z'")
               .replace("$prior_window_start", "'2025-12-01T00:00:00Z'")
               .replace("$now_ts", "'2026-01-08T00:00:00Z'")
               .replace("$since_str", "'2026-01-01T00:00:00Z'")
        )
        ok, reason = validate_sql(sanitized)
        if not ok:
            raise RuntimeError(f"insights template {key!r} failed safety: {reason}")


_validate_templates_once()


# ── Config helpers ─────────────────────────────────────────────────────────


def _default_config() -> dict:
    return {
        "enabled": False,
        "channel": "dashboard_only",
        "anthropic_api_key": "",
        "opt_out": False,
        "last_sent_ts": 0,
        "weekday": 0,   # Monday
        "hour": 9,
    }


def load_config() -> dict:
    """Return the persisted config dict, falling back to defaults."""
    try:
        if CONFIG_PATH.exists():
            cfg = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
            out = _default_config()
            out.update({k: v for k, v in cfg.items() if k in out})
            return out
    except Exception as exc:  # noqa: BLE001
        log.warning("insights: failed to load config: %s", exc)
    return _default_config()


def save_config(updates: dict) -> dict:
    """Merge ``updates`` into the persisted config and return the result.

    Unknown keys are dropped silently — same shape contract as the budget /
    alerts config endpoints. Atomic write via temp-rename.
    """
    cfg = load_config()
    allowed = set(_default_config().keys())
    for k, v in (updates or {}).items():
        if k in allowed:
            cfg[k] = v
    try:
        CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        tmp = CONFIG_PATH.with_suffix(".tmp")
        tmp.write_text(json.dumps(cfg, indent=2), encoding="utf-8")
        tmp.replace(CONFIG_PATH)
    except Exception as exc:  # noqa: BLE001
        log.warning("insights: failed to save config: %s", exc)
    return cfg


# ── SQL execution via daemon proxy ─────────────────────────────────────────


def _filter_params_for_sql(sql: str, params: dict) -> dict:
    """DuckDB rejects bind dicts with extra (unused) keys. Pre-filter to
    only the ``$name`` placeholders that actually appear in the SQL.

    Uses a word-boundary regex (not substring) so ``$since_str`` doesn't
    falsely match ``since`` (and pull both binds in when only one belongs).
    """
    import re
    out: dict = {}
    for k, v in params.items():
        if re.search(rf"\${re.escape(k)}\b", sql):
            out[k] = v
    return out


def _run_sql_via_daemon(sql: str, params: dict) -> list[dict]:
    """Dispatch a canned query via daemon ``raw_select_safe``. Returns ``[]``
    on any failure (caller renders an empty result)."""
    bind = _filter_params_for_sql(sql, params)
    try:
        from routes.local_query import local_store_via_daemon
        rows = local_store_via_daemon(
            "raw_select_safe", sql=sql, params=bind,
            timeout_secs=SQL_TIMEOUT_SECS,
        )
        if rows is None:
            # Daemon down / not allowlisted — fall back to direct open.
            from clawmetry import local_store
            store = local_store.get_store(read_only=True)
            rows = store.raw_select_safe(
                sql=sql, params=bind, timeout_secs=SQL_TIMEOUT_SECS
            )
        return rows or []
    except Exception as exc:  # noqa: BLE001
        log.warning("insights: SQL run failed: %s", exc)
        return []


def _bind_params(now: datetime.datetime) -> dict:
    """Return the parameter dict that ALL canned templates share."""
    week_ago = now - datetime.timedelta(days=7)
    two_weeks = now - datetime.timedelta(days=14)
    five_weeks = now - datetime.timedelta(days=35)
    return {
        "since": week_ago.isoformat(),
        "prev_since": two_weeks.isoformat(),
        "prior_window_start": five_weeks.isoformat(),
        "now_ts": now.isoformat(),
        # ``approvals`` and ``alert_rules`` store created_at as a string
        # (varchar), no Z suffix — keep an alt-format binding for them.
        "since_str": week_ago.strftime("%Y-%m-%d %H:%M:%S"),
    }


# ── Anthropic synthesis ────────────────────────────────────────────────────


def _load_anthropic_key(cfg: dict) -> str | None:
    """config['anthropic_api_key'] → ``ANTHROPIC_API_KEY`` env. Cloud-Pro
    users get a relayed key via ``clawmetry connect`` (issue-728 follow-up)."""
    k = (cfg.get("anthropic_api_key") or "").strip()
    if k:
        return k
    env = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    return env or None


def _synthesize_narrative(
    api_key: str,
    title: str,
    hint: str,
    rows: list[dict],
) -> tuple[str, int]:
    """Sonnet → ≤3-sentence narrative. Returns ``(narrative, tokens_used)``;
    falls back to ``"<n> rows."`` on any error."""
    if not rows:
        return "no data this week.", 0
    prompt = (
        f"You are summarising ONE insight for an engineer's weekly digest.\n\n"
        f"Insight title: {title}\n"
        f"Hint: {hint}\n\n"
        f"Raw rows (DuckDB result):\n{json.dumps(rows[:20], default=str)}\n\n"
        f"Write 1-3 sentences. No preamble. No '\"Sure, here is\"'. "
        f"Use concrete numbers from the rows. If the rows are empty or "
        f"all zero, say so plainly."
    )
    body = {
        "model": SYNTHESIS_MODEL,
        "max_tokens": 220,
        "messages": [{"role": "user", "content": prompt}],
    }
    headers = {
        "Content-Type": "application/json",
        "anthropic-version": ANTHROPIC_VERSION,
        "x-api-key": api_key,
    }
    try:
        req = urllib.request.Request(
            ANTHROPIC_URL,
            data=json.dumps(body).encode("utf-8"),
            headers=headers,
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=SYNTHESIS_TIMEOUT_SECS) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        blocks = data.get("content") or []
        text = "".join(b.get("text", "") for b in blocks if isinstance(b, dict)).strip()
        usage = data.get("usage") or {}
        tokens = int(usage.get("input_tokens", 0)) + int(usage.get("output_tokens", 0))
        return text or f"{len(rows)} rows.", tokens
    except (urllib.error.HTTPError, urllib.error.URLError, OSError, ValueError) as exc:
        log.warning("insights: synthesis failed for %r: %s", title, exc)
        return f"{len(rows)} rows (LLM synthesis unavailable).", 0


def _estimate_cost(tokens_used: int) -> float:
    """Sonnet $3/$15 per 1M (providers_pricing.py); split 50/50 in/out."""
    half = tokens_used / 2
    return round((half / 1_000_000) * 3.0 + (half / 1_000_000) * 15.0, 4)


# ── Generator ──────────────────────────────────────────────────────────────


class WeeklyDigestGenerator:
    """Run the 10 canned templates and synthesise a digest. Cron + ``preview``
    button entry-point. Same week passed twice → same rows, drifty narrative."""

    def __init__(self, cfg: dict | None = None) -> None:
        self.cfg = cfg or load_config()

    def generate(self, now: datetime.datetime | None = None) -> WeeklyDigest:
        now = now or datetime.datetime.utcnow()
        week_ago = now - datetime.timedelta(days=7)
        digest = WeeklyDigest(
            generated_at=now.isoformat() + "Z",
            week_start=week_ago.strftime("%Y-%m-%d"),
            week_end=now.strftime("%Y-%m-%d"),
        )
        params = _bind_params(now)
        api_key = _load_anthropic_key(self.cfg)

        for key, title, sql, hint in _INSIGHT_TEMPLATES:
            t0 = time.monotonic()
            rows = _run_sql_via_daemon(sql, params)
            log.debug(
                "insights: %s ran in %.0fms, %d rows",
                key, (time.monotonic() - t0) * 1000, len(rows),
            )
            if api_key:
                narrative, tokens = _synthesize_narrative(api_key, title, hint, rows)
                digest.tokens_used += tokens
            else:
                narrative = (
                    f"{len(rows)} rows. (Set ANTHROPIC_API_KEY for narrative summaries.)"
                    if rows else "no data this week."
                )
            digest.insights.append(InsightResult(
                key=key, title=title, narrative=narrative, rows=rows,
            ))

        # 30-second summary is composed locally from the per-insight pulls
        # so we don't pay a second-order LLM call.
        trend = next((i for i in digest.insights if i.key == "trend_summary"), None)
        if trend and trend.rows:
            r = trend.rows[0]
            digest.summary = (
                f"{r.get('events') or 0:,} events across "
                f"{r.get('sessions') or 0} sessions; "
                f"${r.get('cost') or 0:.2f} spent; "
                f"{r.get('tokens') or 0:,} tokens."
            )
        else:
            digest.summary = "Quiet week — no events recorded in the local store."

        digest.cost_usd = _estimate_cost(digest.tokens_used)
        return digest


# ── Delivery ───────────────────────────────────────────────────────────────


def deliver(digest: WeeklyDigest, cfg: dict | None = None) -> dict:
    """Route digest body to the configured channel via dashboard.py's existing
    Telegram/Slack helpers. Returns ``{"sent": [..], "errors": [..]}``."""
    cfg = cfg or load_config()
    channel = (cfg.get("channel") or "dashboard_only").lower()
    body = digest.to_text()
    sent: list[str] = []
    errors: list[str] = []
    try:
        import dashboard as _d  # late import — only when delivering
    except Exception:
        _d = None  # type: ignore[assignment]

    if channel == "telegram" and _d is not None:
        try:
            _d._send_telegram_alert(body[:3500])
            sent.append("telegram")
        except Exception as exc:  # noqa: BLE001
            errors.append(f"telegram: {exc}")
    elif channel == "slack" and _d is not None:
        try:
            cfg2 = _d._load_alerts_webhook_config()
            url = (cfg2.get("slack_webhook_url") or "").strip()
            if url:
                _d._send_webhook_alert(url, {"message": body[:3500]},
                                       payload_type="slack")
                sent.append("slack")
            else:
                errors.append("slack: no webhook configured")
        except Exception as exc:  # noqa: BLE001
            errors.append(f"slack: {exc}")
    elif channel == "email":
        # Email dispatch is cloud-relayed for Pro; OSS prints a one-line
        # hint instead of opening an SMTP connection (no creds in OSS).
        errors.append("email: Cloud-Pro only (configure via cloud relay)")
    # dashboard_only — no-op; the user reads it on /insights.
    return {"sent": sent, "errors": errors}


# ── Cron scheduler (Monday 9am local) ──────────────────────────────────────
# Single daemon thread; recomputes next-fire on each cycle so DST / long
# suspend can't pile up missed runs.

import threading as _threading


def _seconds_until_next_run(now: datetime.datetime, weekday: int, hour: int) -> float:
    """Seconds until next ``weekday`` (0=Mon) at ``hour:00:00`` local time."""
    days_ahead = (weekday - now.weekday()) % 7
    target = now.replace(hour=hour, minute=0, second=0, microsecond=0)
    if days_ahead == 0 and now >= target:
        days_ahead = 7
    target = target + datetime.timedelta(days=days_ahead)
    return max(60.0, (target - now).total_seconds())


_scheduler_started = False
_scheduler_lock = _threading.Lock()


def start_weekly_scheduler() -> bool:
    """Idempotent. True if a new thread started; False if running or gated off."""
    global _scheduler_started
    if os.environ.get("CLAWMETRY_INSIGHTS", "").strip() != "1":
        return False
    with _scheduler_lock:
        if _scheduler_started:
            return False
        _scheduler_started = True

    def _loop() -> None:
        while True:
            try:
                cfg = load_config()
                if cfg.get("opt_out"):
                    time.sleep(3600)
                    continue
                wkday = int(cfg.get("weekday", 0))
                hour = int(cfg.get("hour", 9))
                wait = _seconds_until_next_run(
                    datetime.datetime.now(), wkday, hour,
                )
                log.info("insights: next digest in %.1f hours", wait / 3600)
                time.sleep(wait)
                cfg = load_config()
                if cfg.get("opt_out"):
                    continue
                digest = WeeklyDigestGenerator(cfg).generate()
                cfg["last_sent_ts"] = int(time.time())
                save_config({"last_sent_ts": cfg["last_sent_ts"]})
                deliver(digest, cfg)
                log.info("insights: weekly digest delivered")
            except Exception as exc:  # noqa: BLE001
                log.warning("insights: scheduler tick failed: %s", exc)
                time.sleep(3600)

    t = _threading.Thread(
        target=_loop, name="clawmetry-insights-cron", daemon=True,
    )
    t.start()
    return True
