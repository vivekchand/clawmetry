"""Briefs (WO-62): a saved question, a schedule, and a destination channel.

Dives already turns a question into SQL and a table, the narrator already
writes a few sentences over a payload, and the daemon already runs a
scheduler thread. A brief wires those three together so an operator reads
one message on Monday morning instead of opening a dashboard:

    brief = {id, title, question, cron_expr, tz, channel_ref, enabled, ...}

    every ~30 s the daemon asks: is any enabled brief due this minute and
    not yet run this minute?  ->  run_brief(brief, store)  ->  post

``run_brief`` never raises and never goes silent: a failed run posts the
failure to the same channel and records ``last_status`` / ``last_error``
on the row, so a brief that stopped working is visible where its answers
used to arrive.

Credentials. Turning a free-text question into SQL needs a model, so a
brief without a credential fails honestly ("no model credential"). The
built-in *Daily digest* carries its own canned SQL and therefore runs
without one. Narration is a second, optional call: when the narrator has
no credential the post carries the raw table and says so.

Metering. Every narrated run is counted (``narrations`` in the run record
and in the daemon state the scheduler keeps) so the cost of "one model call
per run" is a number the operator can see.

Cron. A minimal five-field matcher written in-house (minute hour
day-of-month month day-of-week; ``*``, lists, ranges, steps). No new
dependency.
"""
from __future__ import annotations

import datetime as _dt
import json
import logging
import os
import threading
import time
import urllib.request
import uuid
from collections.abc import Callable
from typing import Any

log = logging.getLogger("clawmetry.briefs")

BRIEFS_MAX = int(os.environ.get("CLAWMETRY_BRIEFS_MAX", "10"))
SCHEDULER_INTERVAL_SEC = int(os.environ.get("CLAWMETRY_BRIEFS_INTERVAL", "30"))
CHANNELS = ("dashboard", "webhook", "slack", "discord", "telegram")
_ALERTS_CONFIG_FILE = os.path.expanduser("~/.openclaw/clawmetry-alerts.json")
_POST_TIMEOUT_SEC = 10
_MAX_ROWS_IN_POST = 12

BUILTIN_DAILY_DIGEST_ID = "builtin_daily_digest"
BUILTIN_DAILY_DIGEST = {
    "id": BUILTIN_DAILY_DIGEST_ID,
    "title": "Daily digest",
    "question": "What ran yesterday: sessions, spend and tokens per runtime.",
    "cron_expr": "0 9 * * *",
    "tz": "",
    "channel_ref": "dashboard",
    "enabled": False,
    "builtin": True,
}
# Canned SQL for the built-in brief so it runs without a model credential.
# Only allowlisted tables (clawmetry/dives_sql_safety.py), read-only.
_BUILTIN_SQL = {
    BUILTIN_DAILY_DIGEST_ID: (
        "SELECT agent_type AS runtime, COUNT(*) AS sessions, "
        "ROUND(COALESCE(SUM(cost_usd), 0), 2) AS cost_usd, "
        "COALESCE(SUM(total_tokens), 0) AS tokens "
        "FROM sessions WHERE started_at >= '{since}' "
        "GROUP BY 1 ORDER BY 3 DESC LIMIT 20"
    ),
}


# ── cron ────────────────────────────────────────────────────────────────────

_FIELD_RANGES = ((0, 59), (0, 23), (1, 31), (1, 12), (0, 7))


def _parse_field(field: str, lo: int, hi: int) -> set[int]:
    out: set[int] = set()
    for part in str(field).split(","):
        part = part.strip()
        if not part:
            raise ValueError("empty cron field")
        step = 1
        if "/" in part:
            part, step_s = part.split("/", 1)
            step = int(step_s)
            if step <= 0:
                raise ValueError("cron step must be positive")
        if part == "*":
            a, b = lo, hi
        elif "-" in part:
            a_s, b_s = part.split("-", 1)
            a, b = int(a_s), int(b_s)
        else:
            a = b = int(part)
            if step > 1:
                b = hi
        if a < lo or b > hi or a > b:
            raise ValueError(f"cron value out of range: {part}")
        out.update(range(a, b + 1, step))
    return out


def parse_cron(expr: str) -> tuple[set[int], set[int], set[int], set[int], set[int]]:
    """Five fields: minute hour day-of-month month day-of-week. Raises
    ``ValueError`` on anything else. Day-of-week 7 is folded to 0 (Sunday)."""
    parts = str(expr or "").split()
    if len(parts) != 5:
        raise ValueError("cron expression needs five fields")
    sets = []
    for raw, (lo, hi) in zip(parts, _FIELD_RANGES):
        sets.append(_parse_field(raw, lo, hi))
    dow = sets[4]
    if 7 in dow:
        dow.discard(7)
        dow.add(0)
    return sets[0], sets[1], sets[2], sets[3], dow


def cron_matches(expr: str, when: _dt.datetime) -> bool:
    """True when ``when`` (to the minute) satisfies ``expr``. Standard cron
    rule: when BOTH day-of-month and day-of-week are restricted, either one
    matching is enough."""
    minutes, hours, doms, months, dows = parse_cron(expr)
    if when.minute not in minutes or when.hour not in hours or when.month not in months:
        return False
    dom_star = str(expr).split()[2] == "*"
    dow_star = str(expr).split()[4] == "*"
    dom_ok = when.day in doms
    dow_ok = ((when.weekday() + 1) % 7) in dows  # python Mon=0 -> cron Sun=0
    if dom_star and dow_star:
        return True
    if dom_star:
        return dow_ok
    if dow_star:
        return dom_ok
    return dom_ok or dow_ok


def _now_in_tz(now: _dt.datetime, tz: str | None) -> _dt.datetime:
    """``now`` in the brief's timezone; falls back to the given clock when
    zoneinfo is missing or the name is unknown (never raises)."""
    if not tz:
        return now
    try:
        from zoneinfo import ZoneInfo
        base = now if now.tzinfo else now.astimezone()
        return base.astimezone(ZoneInfo(str(tz)))
    except Exception:  # noqa: BLE001
        return now


def is_due(brief: dict, now: _dt.datetime) -> bool:
    """Due when the cron matches this minute and the brief has not already
    run inside this minute. Disabled briefs are never due."""
    if not isinstance(brief, dict) or not brief.get("enabled"):
        return False
    local = _now_in_tz(now, brief.get("tz"))
    try:
        if not cron_matches(str(brief.get("cron_expr") or ""), local):
            return False
    except ValueError:
        return False
    last = brief.get("last_run_at")
    if last:
        try:
            last_dt = _dt.datetime.fromtimestamp(int(last) / 1000, tz=_dt.timezone.utc)
            now_utc = (now if now.tzinfo else now.astimezone()).astimezone(_dt.timezone.utc)
            if last_dt.replace(second=0, microsecond=0) == now_utc.replace(second=0, microsecond=0):
                return False
        except (TypeError, ValueError, OverflowError):
            pass
    return True


# ── validation ──────────────────────────────────────────────────────────────

def validate_brief(raw: dict) -> tuple[dict | None, str | None]:
    """Normalise an operator-supplied brief. ``(brief, None)`` or
    ``(None, reason)``."""
    if not isinstance(raw, dict):
        return None, "body must be an object"
    title = str(raw.get("title") or "").strip()[:200]
    question = str(raw.get("question") or "").strip()[:2000]
    cron_expr = " ".join(str(raw.get("cron_expr") or "").split())[:64]
    if not title:
        return None, "title is required"
    if not question:
        return None, "question is required"
    try:
        parse_cron(cron_expr)
    except ValueError as e:
        return None, f"schedule: {e}"
    channel = str(raw.get("channel_ref") or "dashboard").strip().lower()[:64]
    if channel not in CHANNELS:
        return None, f"channel must be one of {', '.join(CHANNELS)}"
    tz = str(raw.get("tz") or "").strip()[:64]
    bid = str(raw.get("id") or "").strip()[:64]
    if not bid:
        bid = "brief_" + uuid.uuid4().hex[:12]
    if not all(c.isalnum() or c in "_-" for c in bid):
        return None, "id may only contain letters, digits, _ and -"
    return {
        "id": bid, "title": title, "question": question, "cron_expr": cron_expr,
        "tz": tz, "channel_ref": channel, "enabled": bool(raw.get("enabled", False)),
    }, None


# ── running one brief ───────────────────────────────────────────────────────

def _dashboard_link() -> str:
    base = (os.environ.get("CLAWMETRY_DASHBOARD_URL") or "http://localhost:8900").rstrip("/")
    return f"{base}/#signals"


def _sql_for(brief: dict, store, now: _dt.datetime, llm_sql: Callable | None) -> tuple[str | None, str | None]:
    """``(sql, error)``. Built-ins carry canned SQL; everything else goes
    through the Dives question-to-SQL step, which needs a credential."""
    canned = _BUILTIN_SQL.get(str(brief.get("id") or ""))
    if canned:
        since = (now - _dt.timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%S")
        return canned.format(since=since), None
    if llm_sql is None:
        try:
            from routes.dives import (
                _call_llm_for_sql as llm_sql,  # type: ignore[no-redef]
            )
        except Exception as e:  # noqa: BLE001
            return None, f"question-to-query step unavailable: {e}"
    try:
        spec = llm_sql(str(brief.get("question") or ""), store) or {}
    except ValueError as e:
        msg = str(e)
        if msg.startswith("no_auth"):
            return None, "no model credential to turn the question into a query (set ANTHROPIC_API_KEY or sign in with the claude CLI)"
        return None, msg[:300]
    except Exception as e:  # noqa: BLE001
        return None, f"question-to-query failed: {str(e)[:200]}"
    sql = spec.get("sql") if isinstance(spec, dict) else None
    if not sql:
        return None, "question-to-query returned no SQL"
    return str(sql), None


def _execute(sql: str, store) -> tuple[list[dict], str | None]:
    try:
        from clawmetry.dives_sql_safety import validate_sql
        ok, reason = validate_sql(sql)
        if not ok:
            return [], f"query rejected: {reason}"
    except Exception as e:  # noqa: BLE001
        return [], f"query safety check unavailable: {e}"
    try:
        rows = store.raw_select_safe(sql=sql)
        return list(rows or []), None
    except Exception as e:  # noqa: BLE001
        return [], str(e)[:200]


def table_text(rows: list[dict], limit: int = _MAX_ROWS_IN_POST) -> str:
    """A plain-text table of the first rows, for a channel that has no
    model to narrate them."""
    if not rows:
        return "(no rows)"
    cols = list(rows[0].keys())[:8]
    lines = [" | ".join(str(c) for c in cols)]
    for r in rows[:limit]:
        lines.append(" | ".join(str(r.get(c, ""))[:32] for c in cols))
    if len(rows) > limit:
        lines.append(f"... {len(rows) - limit} more rows")
    return "\n".join(lines)


def _narrate(brief: dict, rows: list[dict], narrate: Callable | None) -> str | None:
    if narrate is None:
        try:
            from clawmetry.narrator import narrate  # type: ignore[no-redef]
        except Exception:  # noqa: BLE001
            return None
    try:
        return narrate("brief", {
            "brief_id": brief.get("id"), "title": brief.get("title"),
            "question": brief.get("question"), "rows": rows[:_MAX_ROWS_IN_POST],
            "row_count": len(rows),
        }, timeout_secs=20.0)
    except Exception as e:  # noqa: BLE001
        log.debug("briefs: narration failed: %s", e)
        return None


def compose_post(brief: dict, *, rows: list[dict] | None, narrative: str | None,
                 error: str | None, link: str | None = None) -> str:
    """The message body a channel receives. Failures are posted too."""
    link = link or _dashboard_link()
    title = str(brief.get("title") or "Brief")
    if error:
        return (f"{title}: this brief could not run.\n{error}\n"
                f"Fix it on the Signals tab: {link}")
    rows = rows or []
    if narrative:
        body = narrative.strip()
    else:
        body = ("No model credential was available to narrate this, so here is the raw table.\n"
                + table_text(rows))
    return f"{title}\n{body}\nOpen the dashboard: {link}"


def _load_channel_config() -> dict:
    try:
        with open(_ALERTS_CONFIG_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except Exception:  # noqa: BLE001
        return {}


def _http_post_json(url: str, payload: dict) -> bool:
    req = urllib.request.Request(
        url, data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", "User-Agent": "clawmetry-briefs"},
        method="POST")
    with urllib.request.urlopen(req, timeout=_POST_TIMEOUT_SEC) as resp:
        status = getattr(resp, "status", None) or 200
        return 200 <= int(status) < 300


def post_to_channel(channel_ref: str, title: str, text: str, *,
                    config: dict | None = None, poster: Callable | None = None) -> tuple[bool, str | None]:
    """Deliver ``text`` to the channel the operator configured on the
    Alerts tab. ``dashboard`` posts nowhere (the run record IS the post).
    ``(ok, error)``; never raises."""
    ch = str(channel_ref or "dashboard").strip().lower()
    if ch == "dashboard":
        return True, None
    cfg = config if config is not None else _load_channel_config()
    poster = poster or _http_post_json
    try:
        if ch == "webhook":
            url = str(cfg.get("webhook_url") or "").strip()
            if not url:
                return False, "no generic webhook configured on the Alerts tab"
            return poster(url, {"source": "clawmetry-brief", "title": title, "text": text}), None
        if ch == "slack":
            url = str(cfg.get("slack_webhook_url") or "").strip()
            if not url:
                return False, "no Slack webhook configured on the Alerts tab"
            return poster(url, {"text": f"*{title}*\n{text}"[:3500]}), None
        if ch == "discord":
            url = str(cfg.get("discord_webhook_url") or "").strip()
            if not url:
                return False, "no Discord webhook configured on the Alerts tab"
            return poster(url, {"content": f"**{title}**\n{text}"[:1900]}), None
        if ch == "telegram":
            token = str(cfg.get("telegram_bot_token") or "").strip()
            chat_id = str(cfg.get("telegram_chat_id") or "").strip()
            if not token or not chat_id:
                return False, "no Telegram bot configured on the Alerts tab"
            return poster(f"https://api.telegram.org/bot{token}/sendMessage",
                          {"chat_id": chat_id, "text": f"{title}\n{text}"[:3500]}), None
    except Exception as e:  # noqa: BLE001
        return False, f"{ch}: {str(e)[:200]}"
    return False, f"unknown channel {ch}"


def run_brief(brief: dict, store, *, now: _dt.datetime | None = None,
              llm_sql: Callable | None = None, narrate: Callable | None = None,
              poster: Callable | None = None, channel_config: dict | None = None) -> dict:
    """Run one brief end to end and post the result (or the failure).
    Returns ``{status: ok|failed, error, rows, narrated, posted, post_error,
    text}``. Never raises."""
    now = now or _dt.datetime.now(_dt.timezone.utc)
    out: dict[str, Any] = {"status": "failed", "error": None, "rows": 0,
                           "narrated": False, "posted": False, "post_error": None, "text": ""}
    try:
        sql, err = _sql_for(brief, store, now, llm_sql)
        rows: list[dict] = []
        narrative = None
        if not err:
            rows, err = _execute(sql or "", store)
        if not err:
            narrative = _narrate(brief, rows, narrate)
            out["narrated"] = bool(narrative)
            out["rows"] = len(rows)
            out["status"] = "ok"
        out["error"] = err
        text = compose_post(brief, rows=rows, narrative=narrative, error=err)
        out["text"] = text
        ok, perr = post_to_channel(str(brief.get("channel_ref") or "dashboard"),
                                   str(brief.get("title") or "Brief"), text,
                                   config=channel_config, poster=poster)
        out["posted"] = bool(ok)
        out["post_error"] = perr
        if not ok and out["status"] == "ok":
            out["status"] = "failed"
            out["error"] = perr or "post failed"
    except Exception as e:  # noqa: BLE001
        log.warning("briefs: run failed for %s: %s", brief.get("id"), e)
        out["error"] = str(e)[:300]
    return out


# ── snapshot slice ──────────────────────────────────────────────────────────

SNAPSHOT_MAX = 50
# What rides the cloud snapshot per brief: the same public fields
# GET /api/briefs serves. Title and question are the only free text.
SNAPSHOT_FIELDS = ("id", "title", "question", "cron_expr", "tz", "channel_ref", "enabled",
                   "last_run_at", "last_status", "last_error", "created_at", "builtin")


def build_snapshot_slice(store, *, limit: int = SNAPSHOT_MAX) -> dict:
    """``briefs`` for ``sync_system_snapshot``: the shape ``GET /api/briefs``
    returns (``briefs``, ``count``, ``max``, ``channels``, ``offered``) plus
    ``generated_at``, capped at ``limit`` rows so a node cannot inflate the
    snapshot. ``{}`` on any failure, so the snapshot never breaks here."""
    try:
        cap = max(1, min(int(limit or SNAPSHOT_MAX), SNAPSHOT_MAX))
        rows = store.list_briefs(limit=cap) or []
        out = []
        for b in rows[:cap]:
            if not isinstance(b, dict) or not b.get("id"):
                continue
            b = dict(b)
            b["builtin"] = str(b.get("id") or "") == BUILTIN_DAILY_DIGEST_ID
            out.append({k: b.get(k) for k in SNAPSHOT_FIELDS})
        offered = None
        if not any(b.get("id") == BUILTIN_DAILY_DIGEST_ID for b in out):
            offered = dict(BUILTIN_DAILY_DIGEST)
        return {"briefs": out, "count": len(out), "max": BRIEFS_MAX,
                "channels": list(CHANNELS), "offered": offered,
                "generated_at": int(time.time() * 1000)}
    except Exception as e:  # noqa: BLE001
        log.debug("briefs: snapshot slice failed: %s", e)
        return {}


# ── scheduler ───────────────────────────────────────────────────────────────

def due_briefs(briefs: list[dict], now: _dt.datetime, cap: int | None = None) -> list[dict]:
    """Enabled briefs that are due now, bounded to the first ``cap``
    enabled ones (creation order) so a node cannot fan out unboundedly."""
    cap = BRIEFS_MAX if cap is None else int(cap)
    enabled = [b for b in briefs or [] if isinstance(b, dict) and b.get("enabled")]
    return [b for b in enabled[:max(0, cap)] if is_due(b, now)]


def tick(store, *, now: _dt.datetime | None = None, runner: Callable | None = None,
         state: dict | None = None, cap: int | None = None) -> list[dict]:
    """One scheduler pass: run every due brief, record the outcome on its
    row. Returns the run records. Never raises."""
    now = now or _dt.datetime.now(_dt.timezone.utc)
    runner = runner or run_brief
    ran: list[dict] = []
    try:
        briefs = store.list_briefs(enabled_only=True) or []
    except Exception as e:  # noqa: BLE001
        log.debug("briefs: list failed: %s", e)
        return ran
    for b in due_briefs(briefs, now, cap):
        try:
            res = runner(b, store, now=now)
        except Exception as e:  # noqa: BLE001
            res = {"status": "failed", "error": str(e)[:300], "narrated": False}
        try:
            store.mark_brief_run(brief_id=b["id"], status=res.get("status") or "failed",
                                 error=res.get("error"),
                                 now_ms=int(now.timestamp() * 1000))
        except Exception as e:  # noqa: BLE001
            log.debug("briefs: mark run failed: %s", e)
        if isinstance(state, dict):
            st = state.setdefault("briefs", {})
            if isinstance(st, dict):
                st["runs"] = int(st.get("runs") or 0) + 1
                if res.get("narrated"):
                    st["narrations"] = int(st.get("narrations") or 0) + 1
                st["last_run"] = time.time()
        ran.append({"id": b["id"], **{k: v for k, v in res.items() if k != "text"}})
    return ran


_scheduler_lock = threading.Lock()
_scheduler_started = False


def start_scheduler(store_getter: Callable, *, state: dict | None = None,
                    interval: int | None = None) -> bool:
    """Idempotent daemon thread modelled on ``insights.start_weekly_scheduler``.
    ``CLAWMETRY_BRIEFS=0`` keeps it off. True when a thread started."""
    global _scheduler_started
    if os.environ.get("CLAWMETRY_BRIEFS", "1") == "0":
        return False
    with _scheduler_lock:
        if _scheduler_started:
            return False
        _scheduler_started = True
    every = max(5, int(interval or SCHEDULER_INTERVAL_SEC))

    def _loop() -> None:
        while True:
            try:
                store = store_getter()
                if store is not None:
                    tick(store, state=state)
            except Exception as exc:  # noqa: BLE001
                log.warning("briefs: scheduler tick failed: %s", exc)
            time.sleep(every)

    t = threading.Thread(target=_loop, name="clawmetry-briefs-cron", daemon=True)
    t.start()
    return True
