"""
routes/infra.py — Infrastructure / security / config / logs endpoints.

Extracted from dashboard.py as Phase 5.11 of the incremental modularisation.
Four related Blueprints bundled because each is small (3–4 routes) and they
are logically adjacent observability concerns:

  bp_logs     (4 routes) — /api/logs, /api/flow[-events], /api/logs-stream
  bp_memory   (4 routes) — /api/memory[-files], /api/file, /api/memory-analytics
  bp_security (3 routes) — /api/security/{threats,signatures,posture}
  bp_config   (4 routes) — /api/llmfit, /api/cost-optimizer, /api/cost-optimization,
                           /api/automation-analysis

Module-level helpers (``_find_log_file``, ``_tail_lines``, ``_ext_emit``,
``SSE_MAX_SECONDS``, ``SESSIONS_DIR``, ``_acquire_stream_slot``,
``_release_stream_slot``, ``_get_memory_files``, ``WORKSPACE``, ``MEMORY_DIR``,
``_THREAT_SIGNATURES``, ``_scan_events_for_threats``, ``_scan_security_posture``,
``_fire_alert``, ``_get_cost_summary``, ``_get_expensive_operations``,
``_detect_ollama``, ``_detect_host_hardware``, ``_get_crons``,
``_check_ollama_availability``, ``_generate_cost_recommendations``,
``_get_llmfit_recommendations``, ``_generate_savings_opportunities``,
``_analyze_work_patterns``, ``_generate_automation_suggestions``) stay in
``dashboard.py`` and are reached via late ``import dashboard as _d``. Pure
mechanical move — zero behaviour change.
"""

import json
import os
import select
import sqlite3
import subprocess
import time
from datetime import datetime, timedelta, timezone

from flask import Blueprint, Response, jsonify, request
from clawmetry.config import is_local_store_read_enabled, hide_clawmetry_session

bp_logs = Blueprint('logs', __name__)
bp_memory = Blueprint('memory', __name__)
bp_security = Blueprint('security', __name__)
bp_config = Blueprint('config', __name__)


# ── Logs / Flow SSE ────────────────────────────────────────────────────────


@bp_logs.route("/api/logs")
def api_logs():
    import dashboard as _d
    lines_count = int(request.args.get("lines", 100))
    date_str = request.args.get("date", datetime.now().strftime("%Y-%m-%d"))
    hour_start = request.args.get("hour_start", None)
    hour_end = request.args.get("hour_end", None)
    log_file = _d._find_log_file(date_str)
    lines = []
    if log_file:
        if hour_start is not None or hour_end is not None:
            # Time-filtered reading
            h_start = int(hour_start) if hour_start is not None else 0
            h_end = int(hour_end) if hour_end is not None else 23
            try:
                with open(log_file) as f:
                    for line in f:
                        try:
                            obj = json.loads(line.strip())
                            ts = obj.get("time") or ""
                            if "T" in ts:
                                hour = int(ts.split("T")[1][:2])
                                if h_start <= hour <= h_end:
                                    lines.append(line.strip())
                            else:
                                lines.append(line.strip())
                        except (json.JSONDecodeError, ValueError):
                            lines.append(line.strip())
                lines = lines[-lines_count:]
            except Exception:
                pass
        else:
            lines = _d._tail_lines(log_file, lines_count)
    try:
        _d._ext_emit("log.ingested", {"count": len(lines)})
    except Exception:
        pass
    return jsonify({"lines": lines, "date": date_str})


# Tool-name → flow-tab short key. OpenClaw emits these tool names verified
# against production session JSONLs. Mapped to the short key our Flow SVG
# path ids expect (exec / browser / search / memory / session / cron / tts).
# Shared between the legacy SSE parser and the DuckDB fast-path helper so
# both surfaces emit the same `tool` field for the front-end.
_FLOW_TOOL_MAP = {
    "exec": "exec", "process": "exec", "read": "exec", "write": "exec",
    "write_file": "exec", "edit": "exec", "Bash": "exec", "Read": "exec",
    "Write": "exec", "Edit": "exec",
    "web_search": "search", "ollama_web_search": "search",
    "web_fetch": "browser", "ollama_web_fetch": "browser",
    "browser": "browser", "image": "browser",
    "memory_search": "memory", "memory_get": "memory",
    "sessions_spawn": "session",
    "cron": "cron", "tts": "tts",
}

# Channel-label hints carried inside `Sender (untrusted metadata)` user blocks.
_FLOW_CHANNEL_LABELS = {
    "openclaw-tui":        "tui",
    "openclaw-control-ui": "webchat",
    "openclaw-webchat":    "webchat",
}


def _try_local_store_flow_events(limit=200, since=None):
    """DuckDB fast path for /api/flow-events. Returns a chronologically-
    ordered list of normalised flow events ({type, channel|tool, ts,
    session_id}) drawn from the daemon-ingested ``events`` table, OR
    ``None`` when the local store has no relevant rows (callers fall
    through to the legacy JSONL/gateway-log tail).

    Shape mirrors what the SSE parser yields (msg_in / msg_out /
    tool_call / tool_result) so downstream consumers can treat the JSON
    envelope as a snapshot prefix of the live stream. Tagged
    ``_source: 'local_store'`` by the caller. Closes the Tier-1 audit
    candidate for `/api/flow-events` (refs #1565)."""
    from routes.sessions import _ls_call  # late import to avoid cycle
    rows = _ls_call("query_events", since=since, limit=limit) or []
    if not rows:
        return None

    # The daemon-normalised v3 event types that map to flow lanes. Real
    # OpenClaw v3 ingest emits these (see
    # reference_openclaw_v3_event_types.md); we also accept legacy and
    # tool-call alternates so older sessions still surface. If NONE of
    # the rows match we return None so the legacy parser still drives
    # the SSE timeline (pre-v3 / non-OpenClaw agents).
    _FLOW_TYPES = frozenset({
        "prompt.submitted", "model.completed", "model.changed",
        "tool.call", "tool_call", "tool.result", "tool_use_result",
        "message", "assistant", "user",
    })
    matched = [r for r in rows if r.get("event_type") in _FLOW_TYPES]
    if not matched:
        return None

    def _extract_channel(payload):
        """Pull a channel hint from a `data` blob. Looks at top-level
        ``channel``/``provider`` first, then walks Sender-metadata in
        prompt text the same way the SSE parser does."""
        if not isinstance(payload, dict):
            return None
        for key in ("channel", "provider", "origin"):
            v = payload.get(key)
            if isinstance(v, str) and v:
                lk = v.lower()
                return _FLOW_CHANNEL_LABELS.get(lk, lk)
        text = payload.get("finalPromptText") or ""
        if not isinstance(text, str) or "Sender (untrusted metadata)" not in text:
            return None
        try:
            start = text.index("```json")
            end = text.index("```", start + 8)
            meta = json.loads(text[start + 7:end].strip())
            label = str(meta.get("label") or meta.get("id") or "").lower()
            return _FLOW_CHANNEL_LABELS.get(label, label) or None
        except Exception:
            return None

    events: list = []
    for row in matched:
        et = row.get("event_type") or ""
        data = row.get("data") if isinstance(row.get("data"), dict) else {}
        sid = row.get("session_id") or ""
        ts = row.get("ts") or ""

        if et == "prompt.submitted" or (et in ("message", "user")
                                         and (data.get("role") == "user")):
            ch = _extract_channel(data) or "telegram"
            events.append({"type": "msg_in", "channel": ch,
                           "ts": ts, "session_id": sid,
                           "_source": "local_store"})
            continue

        if et == "model.completed" or (et in ("message", "assistant")
                                        and data.get("role") == "assistant"):
            # Surface tool invocations carried inside the assistant turn
            # as separate tool_call events so the Flow timeline matches
            # the SSE shape. Outer assistant reply itself is the
            # "gateway bubble" — emitted as msg_out so the channel lane
            # lights up.
            tool_metas = []
            inner = data.get("data") if isinstance(data.get("data"), dict) else {}
            for src in (data.get("toolMetas"), inner.get("toolMetas")):
                if isinstance(src, list):
                    tool_metas.extend(src)
            for tm in tool_metas:
                if not isinstance(tm, dict):
                    continue
                name = tm.get("name") or ""
                tool_key = _FLOW_TOOL_MAP.get(name, name)
                events.append({"type": "tool_call", "tool": tool_key,
                               "ts": ts, "session_id": sid,
                               "_source": "local_store"})
            ch = _extract_channel(data) or "telegram"
            events.append({"type": "msg_out", "channel": ch,
                           "ts": ts, "session_id": sid,
                           "_source": "local_store"})
            continue

        if et in ("tool.call", "tool_call"):
            name = (data.get("tool") or data.get("tool_name")
                    or data.get("name") or "")
            tool_key = _FLOW_TOOL_MAP.get(name, name)
            events.append({"type": "tool_call", "tool": tool_key,
                           "ts": ts, "session_id": sid,
                           "_source": "local_store"})
            continue

        if et in ("tool.result", "tool_use_result"):
            name = (data.get("tool") or data.get("tool_name")
                    or data.get("name") or "")
            tool_key = _FLOW_TOOL_MAP.get(name, name or "exec")
            events.append({"type": "tool_result", "tool": tool_key,
                           "ts": ts, "session_id": sid,
                           "_source": "local_store"})
            continue

    # query_events returns DESC; reverse so the caller gets a
    # chronological snapshot prefix (matches what the SSE stream emits).
    events.reverse()
    return events


def _try_local_store_cost_optimizer():
    """DuckDB fast path for /api/cost-optimizer's data-derived fields.

    Tier-1 surface #12 in the 2026-05-17 DuckDB coverage audit
    (issue #1565). The legacy handler reads ``todayCost`` and
    ``projectedMonthlyCost`` from ``dashboard._metrics_store`` (an
    in-memory ring populated by the OTLP/HTTP interceptor) and
    ``expensiveOps`` from the same ring. On a fresh install or after a
    process restart the ring is empty — the optimizer renders $0 / no
    optimisation candidates even when DuckDB holds weeks of real usage
    rows. This helper closes that gap.

    Returns a dict the route merges into its response (keeps host-state
    fields — system, localModels, taskRecommendations, ollamaInstalled,
    llmfitAvailable — on the legacy path; only swaps the data slice).
    Returns ``None`` when DuckDB has zero cost-bearing rows so the
    caller can keep the legacy in-memory values.

    Source preference (same call order as ``_try_local_store_usage_forecast``
    in routes/usage.py — see ``feedback_usage_dedupe_pattern.md``):
      * ``query_aggregates`` — SQL-deduped daily rollup over the FULL
        events table; safe for cost (covers tool retries / fallback
        rows the splits walker drops).
      * ``query_events`` — recent high-cost individual rows for
        ``expensiveOps`` (descending by cost). Capped at 200 rows so a
        many-week DuckDB stays cheap to scan.
    """
    from routes.sessions import _ls_call  # late import to avoid cycle
    from datetime import datetime as _dt, timezone as _tz

    agg_rows = _ls_call("query_aggregates") or []
    if not agg_rows:
        # No cost-bearing rows in DuckDB → defer to legacy path so a
        # fresh install still gets the in-memory ring values (which
        # may have been populated by the live interceptor before the
        # daemon flushed anything to disk).
        return None

    today = _dt.now(_tz.utc).date().isoformat()
    month_prefix = today[:7]  # "YYYY-MM"
    today_cost = 0.0
    month_cost = 0.0
    days_seen: set[str] = set()
    for r in agg_rows:
        day = (r.get("day") or "")
        if not day:
            continue
        c = float(r.get("cost_usd") or 0.0)
        if day == today:
            today_cost += c
        if day.startswith(month_prefix):
            month_cost += c
            days_seen.add(day)

    # Daily-average projection over the days we actually observed this
    # month, scaled to a 30-day month so the figure matches the legacy
    # _get_cost_summary formula (which projects month/days * 30).
    days_in_window = max(1, len(days_seen))
    projected = (month_cost / days_in_window) * 30.0 if month_cost > 0 else 0.0

    # expensiveOps: top recent rows by cost_usd. Walk the same row shape
    # _get_expensive_operations builds (model + cost + tokens + timeAgo).
    expensive_ops: list[dict] = []
    try:
        evs = _ls_call("query_events", limit=200) or []
    except Exception:
        evs = []
    candidates = []
    for ev in evs:
        cost = float(ev.get("cost_usd") or 0.0)
        if cost <= 0.01:
            continue
        model = (ev.get("model") or "").strip() or "unknown"
        tokens = int(ev.get("token_count") or 0)
        ts = ev.get("ts") or ""
        time_ago = ""
        if ts:
            try:
                time_ago = _dt.fromisoformat(
                    ts.replace("Z", "+00:00")
                ).strftime("%H:%M")
            except Exception:
                time_ago = ""
        candidates.append({
            "model": model,
            "cost": cost,
            "tokens": f"{tokens:,}" if tokens > 0 else "unknown",
            "timeAgo": time_ago,
            "canOptimize": False,
        })
    expensive_ops = sorted(
        candidates, key=lambda x: x["cost"], reverse=True
    )[:10]

    return {
        "todayCost": round(today_cost, 4),
        "projectedMonthlyCost": round(projected, 4),
        "expensiveOps": expensive_ops,
        "_source": "local_store",
    }


def _try_local_store_cost_optimization():
    """DuckDB fast path for /api/cost-optimization's data slice.

    Sibling of ``_try_local_store_cost_optimizer`` (which serves
    /api/cost-optimizer). Both endpoints suffer the same in-memory-ring
    silent-zero hazard: ``dashboard._get_cost_summary`` and
    ``_get_expensive_operations`` both read ``metrics_store`` which
    resets on every dashboard restart, so the panel renders $0 even
    when DuckDB holds weeks of usage rows. This route returns a
    different envelope shape (``costs`` dict with today/week/month/
    projected) so we extend the sibling's projection with week+month
    rollups derived from the same ``query_aggregates`` rows.

    Returns ``{"costs": {today, week, month, projected}, "expensiveOps":
    [...], "_source": "local_store"}`` when DuckDB has rows; ``None``
    otherwise (no canary on empty store — caller defers to the legacy
    in-memory path, matching the pattern pinned by
    ``test_cost_optimizer_local_store_v3``).
    """
    from routes.sessions import _ls_call  # late import to avoid cycle
    from datetime import datetime as _dt, timezone as _tz, timedelta as _td

    # Sibling handles today + projected + expensiveOps from the same
    # query_aggregates + query_events rows; reuse it so the two
    # endpoints can't drift.
    sibling = _try_local_store_cost_optimizer()
    if sibling is None:
        return None

    # Compute the week + month rollups the sibling doesn't surface.
    agg_rows = _ls_call("query_aggregates") or []
    now = _dt.now(_tz.utc)
    week_start = (now - _td(days=7)).date().isoformat()
    month_start = (now - _td(days=30)).date().isoformat()
    week_cost = 0.0
    month_cost = 0.0
    for r in agg_rows:
        day = (r.get("day") or "")
        if not day:
            continue
        c = float(r.get("cost_usd") or 0.0)
        if day >= week_start:
            week_cost += c
        if day >= month_start:
            month_cost += c

    return {
        "costs": {
            "today":     sibling["todayCost"],
            "week":      round(week_cost, 4),
            "month":     round(month_cost, 4),
            "projected": sibling["projectedMonthlyCost"],
        },
        "expensiveOps": sibling["expensiveOps"],
        "_source": "local_store",
    }


@bp_logs.route("/api/flow-events")
@bp_logs.route("/api/flow")
def api_flow_events():
    """SSE endpoint — emits typed flow events (msg_in, msg_out, tool_call, tool_result).
    No auth required. Tails gateway.log + active session JSONL on disk.
    Returns JSON status for non-SSE clients (HEAD requests or Accept: application/json).
    """
    import dashboard as _d
    # E2E health checks and non-SSE clients get a lightweight JSON response
    accept = request.headers.get("Accept", "")
    if request.method == "HEAD" or "text/event-stream" not in accept:
        # Always include `events` (default empty list) so the JSON envelope
        # shape is stable for non-SSE callers — including the keystone E2E
        # verifier. Without this, an empty/disabled local store would emit
        # `{ok, streaming, type}` and the verifier's shape probe would fail
        # on the missing `.events` key (refs #1763).
        envelope = {"ok": True, "type": "flow-events", "streaming": True, "events": []}
        # DuckDB fast path (refs #1565). Hydrate the JSON envelope with a
        # snapshot of recent flow events so callers that can't (or don't
        # want to) hold an SSE connection still see real data. SSE is the
        # only path that yields LIVE updates; this path is the snapshot.
        if is_local_store_read_enabled():
            try:
                snap = _try_local_store_flow_events(limit=200)
            except Exception:
                snap = None
            if snap is not None:
                envelope["events"] = snap
                envelope["_source"] = "local_store"
        return jsonify(envelope)
    import glob as _glob

    def _find_active_jsonl():
        sd = _d.SESSIONS_DIR
        if not sd or not os.path.isdir(sd):
            return None
        files = [
            f
            for f in _glob.glob(os.path.join(sd, "*.jsonl"))
            if "deleted" not in f and os.path.getsize(f) > 0
        ]
        return max(files, key=os.path.getmtime) if files else None

    gw_log = os.path.join(os.path.expanduser("~"), ".openclaw", "logs", "gateway.log")

    # OpenClaw emits tool names verified in production session JSONLs.
    # Map → the short tool-key our Flow SVG path ids expect:
    #   node-exec / path-brain-exec     ← exec, process, read, write, edit, write_file
    #   node-browser / path-brain-browser ← web_fetch, ollama_web_fetch, image
    #   node-search  / path-brain-search  ← web_search, ollama_web_search
    #   node-memory  / path-brain-memory  ← memory_search, memory_get
    #   node-session / path-brain-session ← sessions_spawn
    #   node-cron    / path-brain-cron    ← cron
    #   node-tts     / path-brain-tts     ← tts
    # Missing mappings fall through to raw tool name (which may not have a path).
    _TOOL_MAP = {
        "exec": "exec",
        "process": "exec",
        "read": "exec",
        "write": "exec",
        "write_file": "exec",
        "edit": "exec",
        "web_search": "search",
        "ollama_web_search": "search",
        "web_fetch": "browser",
        "ollama_web_fetch": "browser",
        "browser": "browser",
        "image": "browser",
        "memory_search": "memory",
        "memory_get": "memory",
        "sessions_spawn": "session",
        "cron": "cron",
        "tts": "tts",
    }

    # Inbound messages arrive as user.content[0].text with a `Sender (untrusted
    # metadata)` JSON block identifying the channel label. Map known labels to
    # our channel keys; fall back to "telegram" for unknown (current UI default).
    _CHANNEL_LABELS = {
        "openclaw-tui":         "tui",
        "openclaw-control-ui":  "webchat",
        "openclaw-webchat":     "webchat",
    }

    def _extract_channel(text):
        """Parse `Sender (untrusted metadata)` JSON block from user message text.

        Returns channel key ("tui" / "webchat" / "telegram" / ...) or None.
        Telegram/Signal/WhatsApp don't set a special label, so fall through to
        "telegram" as the legacy default (matches pre-fix behaviour).
        """
        if not isinstance(text, str) or "Sender (untrusted metadata)" not in text:
            return None
        try:
            start = text.index("```json")
            end = text.index("```", start + 8)
            meta = json.loads(text[start + 7:end].strip())
            label = str(meta.get("label") or meta.get("id") or "").lower()
            if label in _CHANNEL_LABELS:
                return _CHANNEL_LABELS[label]
            if label:
                return label
        except Exception:
            pass
        return None

    def _parse_gw(line):
        """Parse gateway.log for channel I/O events. OpenClaw 2026.4+ logs format:
        `YYYY-MM-DDTHH:MM:SS... [telegram] sendMessage ok chat=... message=...`"""
        for ch in ("telegram", "imessage", "whatsapp", "signal", "discord",
                   "slack", "irc", "webchat", "bluebubbles"):
            if f"[{ch}]" in line:
                if "sendMessage ok" in line or "send ok" in line or "sent ok" in line:
                    return {"type": "msg_out", "channel": ch}
                # Inbound via logs is rare; most arrive via session JSONL instead.
        return None

    def _parse_jsonl(obj, last_tool):
        """Parse a session JSONL line. OpenClaw wraps conversation entries in
        a `type=message` envelope with a nested `message.role` and
        `message.content[]` array. Tool calls live in `content[].type=toolCall`,
        NOT the outer type. Tool results arrive as `role=toolResult`.
        """
        if obj.get("type") != "message":
            return None
        msg = obj.get("message") or {}
        if not isinstance(msg, dict):
            return None
        role = msg.get("role", "")
        content = msg.get("content") or []

        # Assistant tool invocations — walk content[] for toolCall items.
        if role == "assistant" and isinstance(content, list):
            for item in content:
                if isinstance(item, dict) and item.get("type") == "toolCall":
                    name = item.get("name") or ""
                    tool_key = _TOOL_MAP.get(name, name)
                    last_tool[0] = tool_key
                    return {"type": "tool_call", "tool": tool_key}
            # Pure-text assistant reply has no explicit channel (the reply leg
            # is better driven by gateway.log `sendMessage ok`); skip here.
            return None

        # Tool results — `role=toolResult` with `toolName` on the envelope.
        if role == "toolResult":
            name = msg.get("toolName") or ""
            tool_key = _TOOL_MAP.get(name, last_tool[0] or "exec")
            return {"type": "tool_result", "tool": tool_key}

        # User inbound — extract channel from the Sender metadata block.
        if role == "user":
            text = ""
            if isinstance(content, list) and content:
                first = content[0]
                if isinstance(first, dict):
                    text = first.get("text") or ""
            ch = _extract_channel(text) or "telegram"
            return {"type": "msg_in", "channel": ch}
        return None

    def generate():
        gw_pos = 0
        jsonl_pos = 0
        jsonl_path = None
        last_tool = ["exec"]
        last_jsonl_check = 0.0
        started = time.time()

        # Seek to end of existing files — only emit NEW events
        if os.path.exists(gw_log):
            with open(gw_log, "rb") as f:
                f.seek(0, 2)
                gw_pos = f.tell()
        jsonl_path = _find_active_jsonl()
        if jsonl_path:
            with open(jsonl_path, "rb") as f:
                f.seek(0, 2)
                jsonl_pos = f.tell()

        try:
            while True:
                if time.time() - started > _d.SSE_MAX_SECONDS:
                    yield "event: done\ndata: {}\n\n"
                    break

                events = []

                # Tail gateway.log
                if os.path.exists(gw_log):
                    try:
                        with open(gw_log, "rb") as f:
                            f.seek(gw_pos)
                            data = f.read()
                            gw_pos = f.tell()
                        for line in data.decode("utf-8", errors="replace").splitlines():
                            ev = _parse_gw(line)
                            if ev:
                                events.append(ev)
                    except Exception:
                        pass

                # Re-detect active JSONL every 10s
                now = time.time()
                if now - last_jsonl_check > 10:
                    new_path = _find_active_jsonl()
                    if new_path and new_path != jsonl_path:
                        jsonl_path = new_path
                        jsonl_pos = 0
                        with open(jsonl_path, "rb") as f:
                            f.seek(0, 2)
                            jsonl_pos = f.tell()
                    last_jsonl_check = now

                # Tail session JSONL
                if jsonl_path:
                    try:
                        with open(jsonl_path, "rb") as f:
                            f.seek(jsonl_pos)
                            data = f.read()
                            jsonl_pos = f.tell()
                        for line in data.decode("utf-8", errors="replace").splitlines():
                            line = line.strip()
                            if not line:
                                continue
                            try:
                                ev = _parse_jsonl(json.loads(line), last_tool)
                                if ev:
                                    events.append(ev)
                            except Exception:
                                pass
                    except Exception:
                        pass

                for ev in events:
                    yield f"data: {json.dumps(ev)}\n\n"

                time.sleep(0.5)
        except GeneratorExit:
            pass

    return Response(
        generate(),
        mimetype="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@bp_logs.route("/api/flow/runs")
def api_flow_runs():
    """Historical flow-runs list — closes #611.

    Each row is one session_id's worth of events, aggregated from the local
    DuckDB ``events`` table:

      session_id, agent_id, started_at, duration_seconds, channels_touched,
      models_invoked, tools_called, total_cost, status (completed/failed),
      models[], channel

    Query params:
      ``limit``  — max rows (default 30, hard cap 200)
      ``since``  — ISO timestamp lower-bound on event ts
      ``until``  — ISO timestamp upper-bound

    Returns ``{runs: [...], _source: "local_store"|"empty",
    capped_at_24h: bool}``. Never raises — on any store failure we return
    an empty list with the legacy tag so the Flow tab degrades gracefully.

    Retention gating (issue #1173): OSS / Cloud-Free users are capped to
    the last 24 hours of ``started_at``. Cloud-Pro users (validated by
    ``dashboard._is_pro_user``) get unlimited history. When the cap is
    enforced we set ``capped_at_24h=true`` so the UI can surface the
    Cloud-Pro upgrade CTA.
    """
    try:
        limit_raw = int(request.args.get("limit", 30))
    except (TypeError, ValueError):
        limit_raw = 30
    limit = max(1, min(200, limit_raw))
    since = request.args.get("since") or None
    until = request.args.get("until") or None
    agent_id = request.args.get("agent_id") or None

    # OSS retention cap (issue #1173). Pro users bypass the cap entirely;
    # everyone else gets clamped to last 24h of started_at.
    capped_at_24h = False
    try:
        import dashboard as _d
        is_pro = bool(_d._is_pro_user())
    except Exception:
        is_pro = False
    if not is_pro:
        cap_iso = (
            datetime.now(timezone.utc) - timedelta(hours=24)
        ).strftime("%Y-%m-%dT%H:%M:%SZ")
        # If caller asked for a window older than the cap (or no `since`
        # at all), clamp to the cap and flag the response so the UI can
        # render the upgrade CTA.
        if not since or since < cap_iso:
            since = cap_iso
            capped_at_24h = True

    # MOAT Tier-1 sweep (refs #1565): route through the daemon HTTP proxy
    # first. The previous direct ``local_store.get_store(read_only=True)``
    # open silently failed on multi-process installs (DuckDB exclusive lock
    # blocks even RO opens — see memory
    # ``reference_duckdb_process_lock.md``), so every standard launchd /
    # systemd user saw an empty Past-flow-runs list. The daemon owns the
    # writer connection and serves reads via HTTP from the same process.
    runs: list | None = None
    source = "empty"
    try:
        from routes.local_query import local_store_via_daemon
        runs = local_store_via_daemon(
            "query_flow_runs",
            agent_id=agent_id, since=since, until=until, limit=limit,
        )
    except Exception:
        runs = None
    if runs is None:
        # Single-process fallback (tests / dev mode with no sync daemon).
        # NB: this path WILL fail on a multi-process install because of the
        # DuckDB process lock — but in that scenario the daemon proxy above
        # should always succeed. Logging here surfaces drift if it doesn't.
        try:
            from clawmetry import local_store
            store = local_store.get_store(read_only=True)
            runs = store.query_flow_runs(
                agent_id=agent_id, since=since, until=until, limit=limit,
            ) or []
        except Exception as exc:
            import logging
            logging.getLogger(__name__).warning(
                "api_flow_runs: daemon proxy AND direct DuckDB open both "
                "failed — returning empty list (%s)", exc,
            )
            runs = []
    if runs:
        source = "local_store"

    return jsonify({
        "runs": runs,
        "count": len(runs),
        "_source": source,
        "capped_at_24h": capped_at_24h,
    })


@bp_logs.route("/api/logs-stream")
def api_logs_stream():
    """SSE endpoint - streams new log lines in real-time."""
    import dashboard as _d
    if not _d._acquire_stream_slot("log"):
        return jsonify({"error": "Too many active log streams"}), 429

    today = datetime.now().strftime("%Y-%m-%d")
    log_file = _d._find_log_file(today)

    def generate():
        started_at = time.time()
        if not log_file:
            yield 'data: {"line":"No log file found"}\n\n'
            _d._release_stream_slot("log")
            return
        proc = subprocess.Popen(
            ["tail", "-f", "-n", "0", log_file],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        try:
            while True:
                if time.time() - started_at > _d.SSE_MAX_SECONDS:
                    yield 'event: done\ndata: {"reason":"max_duration_reached"}\n\n'
                    break
                ready, _, _ = select.select([proc.stdout], [], [], 1.0)
                if not ready:
                    continue
                line = proc.stdout.readline()
                if line:
                    yield f"data: {json.dumps({'line': line.rstrip()})}\n\n"
        except GeneratorExit:
            pass
        finally:
            try:
                proc.kill()
            except Exception:
                pass
            _d._release_stream_slot("log")

    return Response(
        generate(),
        mimetype="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


# ── Memory files ───────────────────────────────────────────────────────────
#
# Local-store fast path (DuckDB MOAT mandate): when
# CLAWMETRY_LOCAL_STORE_READ=1 AND the local memory_blobs table has rows for
# this agent, serve directly from DuckDB. Falls through to the legacy
# filesystem path otherwise (so a fresh install with no local store, or a
# user who hasn't enabled the gate, sees the same data as before — zero-
# change default). The POST handler at /api/file intentionally stays on
# disk; writes are a future ingest hook (sync.py owns memory ingest today).


def _try_local_store_memory_files():
    """Read memory file metadata directly from the local DuckDB. Returns
    a list shaped identically to ``_get_memory_files()`` (``[{"path":
    str, "size": int}, ...]``). Returns ``None`` to defer to the
    filesystem fallback if:
      - the local_store module isn't importable
      - the memory_blobs table is empty
      - any unexpected error happens (we'd rather degrade than 500)
    """
    # CRITICAL (regression #1228): the sync daemon (separate process)
    # holds DuckDB's exclusive lock — even RO opens block on macOS, which
    # is why the Memory tab spinner stuck on "Loading…". Route through
    # the daemon's local_query proxy first; fall back to direct open in
    # single-process boots.
    rows = None
    try:
        from routes.local_query import local_store_via_daemon
        rows = local_store_via_daemon("query_memory_blobs", limit=500)
    except Exception:
        rows = None
    if rows is None:
        try:
            from clawmetry import local_store
            store = local_store.get_store(read_only=True)
            rows = store.query_memory_blobs(limit=500)
        except Exception:
            return None
    if not rows:
        return None
    out = []
    seen: set[str] = set()
    for r in rows:
        path = r.get("path") or ""
        if not path or path in seen:
            continue
        seen.add(path)
        size = r.get("size_bytes")
        if size is None:
            blob = r.get("blob")
            if isinstance(blob, str):
                size = len(blob.encode("utf-8", errors="replace"))
            elif isinstance(blob, (bytes, bytearray)):
                size = len(blob)
            else:
                size = 0
        out.append({"path": path, "size": int(size or 0)})
    return out


def _try_local_store_file(path: str):
    """Read one memory file directly from the local DuckDB. Returns the
    same response shape as the legacy filesystem-backed endpoint
    (``{"path", "content", "size", "mtime"}``). Returns ``None`` to
    defer to the filesystem fallback if:
      - the local_store module isn't importable
      - no memory_blobs row matches the requested path
      - the blob payload isn't UTF-8 text (rare; punt to disk path)
    """
    # See #1228 — proxy through the daemon when present (cross-process
    # DuckDB lock blocks even RO opens), fall back to direct read.
    rows = None
    try:
        from routes.local_query import local_store_via_daemon
        rows = local_store_via_daemon(
            "query_memory_blobs", path_prefix=path, limit=50,
        )
    except Exception:
        rows = None
    if rows is None:
        try:
            from clawmetry import local_store
            store = local_store.get_store(read_only=True)
            # query_memory_blobs has no exact-path filter (path_prefix is the
            # closest), so use prefix=path to narrow then exact-match below.
            rows = store.query_memory_blobs(path_prefix=path, limit=50)
        except Exception:
            return None
    for r in rows:
        if (r.get("path") or "") != path:
            continue
        blob = r.get("blob")
        if blob is None:
            content = ""
        elif isinstance(blob, str):
            content = blob
        else:
            # Binary blob (non-utf8) — defer to filesystem path which can
            # at least raise a sensible error to the user.
            return None
        size = r.get("size_bytes")
        if size is None:
            size = len(content.encode("utf-8", errors="replace"))
        # ts is an ISO string; convert to epoch seconds for parity with
        # os.path.getmtime() which returns float seconds.
        mtime = 0
        ts = r.get("ts")
        if ts:
            try:
                from datetime import datetime as _dt
                mtime = int(_dt.fromisoformat(
                    ts.replace("Z", "+00:00")
                ).timestamp())
            except Exception:
                pass
        return {
            "path": path,
            "content": content[:500_000],
            "size": int(size or 0),
            "mtime": mtime,
            "_source": "local_store",
        }
    return None


def _try_local_store_memory_analytics(bloat_warn_kb: int, bloat_crit_kb: int):
    """Compute memory analytics from the local DuckDB. Same response
    shape as the filesystem-backed endpoint. Returns ``None`` to defer
    when the local store has no memory_blobs rows."""
    files = _try_local_store_memory_files()
    if files is None:
        return None
    return _build_memory_analytics(files, bloat_warn_kb, bloat_crit_kb,
                                   source="local_store")


def _build_memory_analytics(files, bloat_warn_kb, bloat_crit_kb, *, source=None):
    """Pure analytics builder over a ``[{path, size}, ...]`` list. Shared
    between the local-store fast path and the filesystem fallback so the
    response shape stays identical regardless of source."""
    total_bytes = sum(f.get("size", 0) for f in files)
    root_files = [f for f in files if "/" not in f["path"]]
    daily_files = [f for f in files if f["path"].startswith("memory/")]
    est_tokens = total_bytes // 4

    analysis = []
    recommendations = []
    for f in files:
        entry = {
            "path": f["path"],
            "sizeBytes": f["size"],
            "sizeKB": round(f["size"] / 1024, 1),
            "estTokens": f["size"] // 4,
            "status": "ok",
        }
        kb = f["size"] / 1024
        if kb >= bloat_crit_kb:
            entry["status"] = "critical"
            recommendations.append({
                "file": f["path"],
                "severity": "critical",
                "message": f"{f['path']} is {kb:.1f}KB ({f['size'] // 4} est. tokens). "
                f"Consider pruning to keep context window budget lean.",
            })
        elif kb >= bloat_warn_kb:
            entry["status"] = "warning"
            recommendations.append({
                "file": f["path"],
                "severity": "warning",
                "message": f"{f['path']} is {kb:.1f}KB. Growing large, review for stale content.",
            })
        analysis.append(entry)

    daily_growth = []
    date_sizes = {}
    for f in daily_files:
        basename = f["path"].replace("memory/", "")
        date_part = basename.replace(".md", "")[:10]
        if len(date_part) == 10 and date_part[4] == "-":
            date_sizes[date_part] = date_sizes.get(date_part, 0) + f["size"]
    for d in sorted(date_sizes.keys())[-30:]:
        daily_growth.append({"date": d, "bytes": date_sizes[d]})

    context_budgets = {}
    for name, limit in [
        ("claude_200k", 200000),
        ("gpt4_128k", 128000),
        ("gemini_1m", 1000000),
    ]:
        pct = round((est_tokens / limit) * 100, 1) if limit > 0 else 0
        context_budgets[name] = {
            "limit": limit,
            "memoryTokens": est_tokens,
            "percentUsed": min(pct, 100),
            "status": "critical" if pct > 25 else ("warning" if pct > 10 else "ok"),
        }

    top_files = sorted(analysis, key=lambda x: x["sizeBytes"], reverse=True)[:5]
    has_bloat = any(r["severity"] == "critical" for r in recommendations)
    has_warnings = any(r["severity"] == "warning" for r in recommendations)

    payload = {
        "totalBytes": total_bytes,
        "totalKB": round(total_bytes / 1024, 1),
        "estTokens": est_tokens,
        "fileCount": len(files),
        "rootFileCount": len(root_files),
        "dailyFileCount": len(daily_files),
        "files": analysis,
        "topFiles": top_files,
        "dailyGrowth": daily_growth,
        "contextBudgets": context_budgets,
        "recommendations": recommendations,
        "hasBloat": has_bloat,
        "hasWarnings": has_warnings,
        "thresholds": {"warnKB": bloat_warn_kb, "critKB": bloat_crit_kb},
    }
    if source:
        payload["_source"] = source
    return payload


@bp_memory.route("/api/memory-files")
@bp_memory.route("/api/memory")
def api_memory_files():
    import dashboard as _d
    if is_local_store_read_enabled():
        fast = _try_local_store_memory_files()
        if fast is not None:
            return jsonify({"files": fast, "_source": "local_store"})
    # Wrap the workspace-scan fallback in the same `{files: [...]}` envelope
    # the fast path returns, so the on-the-wire shape is stable regardless
    # of whether the local store is enabled. The bare-list fallback used to
    # break the keystone E2E verifier's shape probe (refs #1763) and any
    # caller that already correctly handled the local_store shape.
    return jsonify({"files": _d._get_memory_files()})


@bp_memory.route("/api/file", methods=["GET"])
def api_view_file():
    """Return the contents of a memory file."""
    import dashboard as _d
    path = request.args.get("path", "")
    if is_local_store_read_enabled() and path:
        fast = _try_local_store_file(path)
        if fast is not None:
            return jsonify(fast)
    full = os.path.normpath(os.path.join(_d.WORKSPACE, path))
    if not full.startswith(os.path.normpath(_d.WORKSPACE)):
        return jsonify({"error": "Access denied"}), 403
    if not os.path.exists(full):
        return jsonify({"error": "File not found"}), 404
    try:
        with open(full, "r") as f:
            content = f.read(500_000)
        return jsonify({
            "path": path,
            "content": content,
            "size": os.path.getsize(full),
            "mtime": int(os.path.getmtime(full)),
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@bp_memory.route("/api/file", methods=["POST", "PUT"])
def api_write_file():
    """Write content to a memory file (user-initiated edit)."""
    import dashboard as _d
    body = request.get_json(silent=True) or {}
    path = body.get("path", "")
    content = body.get("content")
    if not path or content is None or not isinstance(content, str):
        return jsonify({"error": "path and content (string) are required"}), 400
    if len(content.encode("utf-8")) > 500_000:
        return jsonify({"error": "File too large (>500 KB)"}), 413
    full = os.path.normpath(os.path.join(_d.WORKSPACE, path))
    if not full.startswith(os.path.normpath(_d.WORKSPACE)):
        return jsonify({"error": "Access denied"}), 403
    try:
        os.makedirs(os.path.dirname(full) or ".", exist_ok=True)
        with open(full, "w", encoding="utf-8") as f:
            f.write(content)
        return jsonify({
            "ok": True,
            "path": path,
            "size": os.path.getsize(full),
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@bp_memory.route("/api/memory-analytics")
def api_memory_analytics():
    """Memory usage analytics with bloat detection and recommendations."""
    import dashboard as _d

    # Configurable thresholds (bytes)
    bloat_warn_kb = int(request.args.get("warn_kb", 8))
    bloat_crit_kb = int(request.args.get("crit_kb", 16))

    if is_local_store_read_enabled():
        fast = _try_local_store_memory_analytics(bloat_warn_kb, bloat_crit_kb)
        if fast is not None:
            return jsonify(fast)

    files = _d._get_memory_files()
    return jsonify(_build_memory_analytics(files, bloat_warn_kb, bloat_crit_kb))


# ── Memory RAG / SQLite inspector (issue #610) ─────────────────────────────


def _open_rag_db():
    """Open ~/.openclaw/memory/main.sqlite read-only.

    Returns a sqlite3.Connection, or None when the file is absent, the
    memory dir is unknown, or any other error prevents opening (we prefer a
    graceful empty response over a 500).
    """
    import dashboard as _d
    mem_dir = getattr(_d, "MEMORY_DIR", None) or ""
    if not mem_dir:
        return None
    db_path = os.path.join(mem_dir, "main.sqlite")
    if not os.path.isfile(db_path):
        return None
    try:
        uri = f"file:{db_path}?mode=ro"
        return sqlite3.connect(uri, uri=True, timeout=2.0)
    except Exception:
        return None


@bp_memory.route("/api/memory-rag")
def api_memory_rag():
    """Return RAG document-store stats and file list from main.sqlite.

    Response shape:
      {"available": bool, "stats": {...}, "files": [...]}
    When main.sqlite does not exist, returns {"available": false, ...} with
    HTTP 200 so the frontend can render a "not yet indexed" state without
    treating it as an error.
    """
    conn = _open_rag_db()
    if conn is None:
        return jsonify({"available": False, "stats": {}, "files": []})

    try:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()

        try:
            file_rows = cur.execute(
                "SELECT f.path, f.size, f.mtime, COUNT(c.id) AS chunk_count "
                "FROM files f LEFT JOIN chunks c ON c.file_id = f.id "
                "GROUP BY f.id ORDER BY f.size DESC"
            ).fetchall()
            files = [
                {
                    "path": r["path"],
                    "size": r["size"] or 0,
                    "mtime": r["mtime"] or 0,
                    "chunkCount": r["chunk_count"] or 0,
                }
                for r in file_rows
            ]
        except Exception:
            files = []

        stats: dict = {}
        try:
            agg = cur.execute(
                "SELECT COUNT(*) AS file_count, "
                "       COALESCE(SUM(size), 0) AS total_bytes, "
                "       MAX(mtime) AS last_indexed "
                "FROM files"
            ).fetchone()
            stats = {
                "fileCount": agg["file_count"] or 0,
                "totalBytes": agg["total_bytes"] or 0,
                "lastIndexed": agg["last_indexed"],
            }
        except Exception:
            pass

        try:
            chunk_row = cur.execute("SELECT COUNT(*) AS n FROM chunks").fetchone()
            stats["chunkCount"] = chunk_row["n"] or 0
        except Exception:
            pass

        return jsonify({"available": True, "stats": stats, "files": files})
    except Exception as exc:
        return jsonify({"available": False, "error": str(exc), "stats": {}, "files": []})
    finally:
        conn.close()


@bp_memory.route("/api/memory-rag/search")
def api_memory_rag_search():
    """FTS5 full-text search over RAG chunks.

    Query params:
      q      — search terms (required)
      limit  — max results (default 20, max 100)

    Result shape:
      {"available": bool, "query": str, "total": int, "results": [
        {"path": str, "snippet": str, "rank": float}, ...
      ]}
    """
    q = (request.args.get("q") or "").strip()
    if not q:
        return jsonify({"available": True, "query": "", "total": 0, "results": []})

    try:
        limit = min(int(request.args.get("limit", 20)), 100)
    except ValueError:
        limit = 20

    conn = _open_rag_db()
    if conn is None:
        return jsonify({"available": False, "query": q, "total": 0, "results": []})

    try:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        try:
            rows = cur.execute(
                "SELECT f.path, "
                "       snippet(chunks_fts, 0, '<mark>', '</mark>', '...', 16) AS snippet, "
                "       rank "
                "FROM chunks_fts "
                "JOIN chunks c  ON c.id  = chunks_fts.rowid "
                "JOIN files  f  ON f.id  = c.file_id "
                "WHERE chunks_fts MATCH ? "
                "ORDER BY rank "
                "LIMIT ?",
                (q, limit),
            ).fetchall()
            results = [
                {"path": r["path"], "snippet": r["snippet"], "rank": r["rank"]}
                for r in rows
            ]
        except Exception as exc:
            return jsonify({
                "available": True, "query": q, "total": 0,
                "results": [], "error": str(exc),
            })
        return jsonify({"available": True, "query": q, "total": len(results), "results": results})
    finally:
        conn.close()


# ── Memory access history (issue #1896) ────────────────────────────────────
# OpenClaw reads memory via the MCP tools mcp__openclaw__memory_get /
# memory_search. Each call shows up as a `tool_use` block in the assistant
# turn that triggered it, carrying the search query (or fetched key) plus the
# session id + timestamp. We surface those as an access timeline so users can
# see when a memory was accessed and click through to the conversation that
# triggered it (verified against real events 2026-05-22).
_MEMORY_TOOL_PREFIX = "mcp__openclaw__memory_"


def _walk_tool_uses(node):
    """Yield every dict in ``node`` whose type is 'tool_use' (depth-first).
    Handles the nested message/content shapes OpenClaw v3 + claude-cli use."""
    if isinstance(node, dict):
        if node.get("type") == "tool_use" and node.get("name"):
            yield node
        for v in node.values():
            yield from _walk_tool_uses(v)
    elif isinstance(node, list):
        for item in node:
            yield from _walk_tool_uses(item)


def _extract_memory_accesses(rows, limit=200):
    """Pull memory tool calls out of raw events into access records.

    Returns a recent-first list of
    ``{op, target, session_id, ts, tool_use_id}``. ``op`` is "search"/"get",
    ``target`` is the search query or fetched key. Never raises.
    """
    accesses = []
    for ev in rows or []:
        # Hide ClawMetry's own helper sessions (clawmetry-selfevolve /
        # clawmetry-mem-probe …) — their memory reads are plumbing, not the
        # user's activity. Override: CLAWMETRY_SHOW_INTERNAL_SESSIONS=1.
        if hide_clawmetry_session(ev.get("session_id")):
            continue
        data = ev.get("data")
        if not isinstance(data, dict):
            continue
        try:
            tool_uses = list(_walk_tool_uses(data))
        except Exception:
            tool_uses = []
        for tu in tool_uses:
            name = tu.get("name") or ""
            if not name.startswith(_MEMORY_TOOL_PREFIX):
                continue
            op = name[len(_MEMORY_TOOL_PREFIX):] or "access"  # "search" / "get"
            inp = tu.get("input") if isinstance(tu.get("input"), dict) else {}
            target = (
                inp.get("query") or inp.get("key") or inp.get("id")
                or inp.get("name") or inp.get("path") or ""
            )
            if not target and inp:
                try:
                    target = json.dumps(inp)[:200]
                except Exception:
                    target = ""
            accesses.append({
                "op": op,
                "target": str(target)[:300],
                "session_id": ev.get("session_id") or "",
                "ts": ev.get("ts"),
                "tool_use_id": tu.get("id") or "",
            })
    # Recent-first. ``ts`` is an ISO-8601 string for v3 events; sort as string
    # which is chronologically correct for that format, defensive for others.
    accesses.sort(key=lambda a: str(a.get("ts") or ""), reverse=True)
    return accesses[:limit]


@bp_memory.route("/api/memory-access")
def api_memory_access():
    """Timeline of memory tool accesses (memory_get / memory_search).

    DuckDB-first: reads already-ingested events via the daemon proxy and
    extracts memory tool calls. Returns HTTP 200 with ``available: false``
    when the store can't be read so the UI degrades gracefully.

    Query params:
      limit — max records (default 200, max 1000)
    """
    try:
        limit = min(int(request.args.get("limit", 200)), 1000)
    except (ValueError, TypeError):
        limit = 200

    rows = None
    try:
        from routes.local_query import local_store_via_daemon
        rows = local_store_via_daemon("query_events", limit=12000)
    except Exception:
        rows = None
    if rows is None and is_local_store_read_enabled():
        # Single-process fallback (tests/dev with no sync daemon), mirroring
        # routes.sessions._try_local_store_transcript.
        try:
            from clawmetry import local_store
            store = local_store.get_store(read_only=True)
            rows = store.query_events(limit=12000)
        except Exception:
            rows = None
    if rows is None:
        return jsonify({"available": False, "accesses": [], "total": 0})

    accesses = _extract_memory_accesses(rows, limit=limit)
    return jsonify({"available": True, "accesses": accesses, "total": len(accesses)})


# ── Security ───────────────────────────────────────────────────────────────


@bp_security.route("/api/security/threats")
def api_security_threats():
    """Scan recent agent activity for security threats using built-in signatures."""
    import dashboard as _d
    from routes.brain import api_brain_history
    try:
        # Call brain-history endpoint internally
        brain_resp = api_brain_history()
        brain_data = brain_resp.get_json()
        events = brain_data.get("events", [])
    except Exception:
        events = []

    threats, counts = _d._scan_events_for_threats(events)

    # Fire alerts for critical/high threats (with cooldown via _fire_alert)
    for t in threats:
        if t["severity"] in ("critical", "high"):
            _d._fire_alert(
                rule_id=f"security_{t['rule_id']}",
                alert_type="security_threat",
                message=f"🛡️ Security: {t['severity'].upper()} - {t['description']}\n{t['detail'][:200]}",
                channels=["banner", "telegram"],
            )

    return jsonify(
        {"threats": threats, "counts": counts, "scanned_events": len(events)}
    )


@bp_security.route("/api/security/signatures")
def api_security_signatures():
    """Return the built-in threat signature catalog."""
    import dashboard as _d
    sigs = []
    for sig in _d._THREAT_SIGNATURES:
        sigs.append(
            {
                "id": sig["id"],
                "severity": sig["severity"],
                "description": sig["description"],
                "tool_types": sig["tool_types"],
                "pattern": " | ".join(sig["patterns"][:2])
                + ("..." if len(sig["patterns"]) > 2 else ""),
                "pattern_count": len(sig["patterns"]),
            }
        )
    return jsonify({"signatures": sigs, "total": len(sigs)})


@bp_security.route("/api/security/posture")
def api_security_posture():
    """Scan OpenClaw configuration for security misconfigurations and return a posture score."""
    import dashboard as _d
    try:
        result = _d._scan_security_posture()
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e), "score": "U", "checks": []}), 500


# ── Config / Cost optimization ─────────────────────────────────────────────


@bp_config.route("/api/llmfit")
def api_llmfit():
    """Passthrough: run llmfit recommend and return raw JSON."""
    import shutil

    if not shutil.which("llmfit"):
        return jsonify({"error": "llmfit not installed", "models": [], "system": {}})
    try:
        result = subprocess.run(
            ["llmfit", "recommend", "--json", "--limit", "20"],
            capture_output=True,
            text=True,
            timeout=20,
        )
        data = json.loads(result.stdout) if result.returncode == 0 else {}
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e), "models": [], "system": {}})


@bp_config.route("/api/cost-optimizer")
def api_cost_optimizer():
    """Enhanced cost optimizer: llmfit recommendations + task-level suggestions."""
    import dashboard as _d
    import shutil

    try:
        # Cost data from existing helpers
        costs = _d._get_cost_summary()
        expensive_ops = _d._get_expensive_operations()
        ollama_installed = _d._detect_ollama()
        # DuckDB fast path (refs #1565). The legacy ``_get_cost_summary``
        # + ``_get_expensive_operations`` helpers read from the in-memory
        # ``metrics_store`` ring (populated by the HTTP interceptor);
        # that ring resets on process restart so the optimizer renders
        # $0 / no candidates even when DuckDB holds weeks of real usage
        # rows. When the local store has data, swap in its values for
        # the data-derived slice (todayCost / projectedMonthlyCost /
        # expensiveOps) and tag _source so the audit canary fires.
        ls_slice = None
        if is_local_store_read_enabled():
            try:
                ls_slice = _try_local_store_cost_optimizer()
            except Exception:
                ls_slice = None

        # Run llmfit
        llmfit_raw = {}
        if shutil.which("llmfit"):
            try:
                r = subprocess.run(
                    ["llmfit", "recommend", "--json", "--limit", "10"],
                    capture_output=True,
                    text=True,
                    timeout=20,
                )
                if r.returncode == 0:
                    llmfit_raw = json.loads(r.stdout)
            except Exception:
                pass

        # When llmfit doesn't return a `system` block, fall back to actual
        # detection (sysctl on macOS, /proc on Linux, wmic on Windows) instead
        # of the previous hardcoded "Apple M2 Pro / 12 cores / 32 GB" values
        # which misrepresented every non-Mac box.
        sys_info = llmfit_raw.get("system", {})
        host = _d._detect_host_hardware()
        cpu = sys_info.get("cpu_name") or host["cpu"]
        is_apple = any(s in cpu for s in ("Apple", "M1", "M2", "M3", "M4"))

        system_out = {
            "cpu": cpu,
            "cores": sys_info.get("cpu_cores") or host["cores"],
            "ram_gb": sys_info.get("total_ram_gb") or host["ram_gb"],
            "backend": (
                "Apple Metal (unified)"
                if is_apple
                else (sys_info.get("backend") or host["backend"])
            ),
        }

        # Map llmfit models to localModels format
        use_case_map = {
            "coding": ["coding", "code generation"],
            "chat": ["chat", "instruction following"],
        }
        ollama_shortcuts = {
            "deepseek-ai/DeepSeek-Coder-V2-Lite-Instruct": "deepseek-coder-v2:16b",
            "lmstudio-community/Qwen3-4B-Instruct-2507-MLX-8bit": "qwen3:4b",
            "bigcode/starcoder2-7b": "starcoder2:7b",
            "alpindale/Llama-3.2-1B-Instruct": "llama3.2:1b",
        }
        savings_by_cat = {
            "coding": "~$0.50/day for coding crons",
            "chat": "~$0.30/day for heartbeats",
        }

        local_models = []
        for m in llmfit_raw.get("models", [])[:8]:
            full_name = m.get("name", "")
            short = full_name.split("/")[-1] if "/" in full_name else full_name
            cat = (m.get("category") or "Chat").lower()
            use_case_str = m.get("use_case", cat)
            ollama_name = ollama_shortcuts.get(full_name)
            if not ollama_name:
                ollama_name = (
                    short.lower()
                    .replace("-instruct", "")
                    .replace("-fp8", "")
                    .replace("-awq", "")
                    .replace("-mlx-8bit", "")
                )
                ollama_name = "".join(
                    c if c in "abcdefghijklmnopqrstuvwxyz0123456789.-:" else "-"
                    for c in ollama_name
                ).strip("-")
            tps = m.get("estimated_tps", 0) or 0
            local_models.append(
                {
                    "name": short,
                    "fullName": full_name,
                    "useCase": use_case_str,
                    "estimatedTps": round(tps * 3.5, 1),  # Metal multiplier
                    "ramRequired": f"{m.get('memory_required_gb', '?')}GB",
                    "score": m.get("score", 0),
                    "ollamaName": ollama_name,
                    "savingsEstimate": savings_by_cat.get(cat, "~$0.20/day"),
                    "memoryRequiredGb": m.get("memory_required_gb", 0),
                }
            )

        # Task recommendations
        task_recs = []
        # Check cron jobs
        try:
            crons = _d._get_crons()
            for cron in crons[:5]:
                model = cron.get("model", cron.get("modelRef", "claude-sonnet-4-6"))
                name = cron.get("name", cron.get("label", "Cron job"))
                prompt = (cron.get("prompt", "") or "").lower()
                is_heartbeat = any(
                    w in prompt
                    for w in ["heartbeat", "check", "status", "health", "ping"]
                )
                if is_heartbeat or not prompt.strip():
                    task_recs.append(
                        {
                            "task": f"Cron: {name}",
                            "currentModel": model or "claude-sonnet-4-6",
                            "suggestedLocal": "qwen3:4b",
                            "reason": "Simple periodic checks don't need frontier models",
                            "estimatedSavings": "~$2-5/month",
                        }
                    )
        except Exception:
            pass

        # Generic recommendations
        task_recs.append(
            {
                "task": "Heartbeat / periodic checks",
                "currentModel": "claude-sonnet-4-6",
                "suggestedLocal": "qwen3:4b",
                "reason": "Heartbeats (email, calendar, weather) work well with tiny fast models",
                "estimatedSavings": "~$2-5/month",
            }
        )
        task_recs.append(
            {
                "task": "Coding sub-agents",
                "currentModel": "claude-sonnet-4-6",
                "suggestedLocal": "deepseek-coder-v2:16b",
                "reason": "Well-scoped coding tasks (linting, formatting, small fixes) run locally",
                "estimatedSavings": "~$3-8/month",
            }
        )
        task_recs.append(
            {
                "task": "Main conversation (Diya)",
                "currentModel": "claude-sonnet-4-6",
                "suggestedLocal": None,
                "reason": "Complex reasoning, tool use, and planning still benefit from frontier models",
                "estimatedSavings": "Keep as-is",
            }
        )

        today = costs.get("today", 0) or 0
        projected = costs.get("projected", 0) or (today * 30)

        payload = {
            "system": system_out,
            "localModels": local_models,
            "taskRecommendations": task_recs[:6],
            "todayCost": today,
            "projectedMonthlyCost": projected,
            "potentialSavings": "60-80% with local models for crons/heartbeats",
            "expensiveOps": expensive_ops,
            "ollamaInstalled": ollama_installed,
            "llmfitAvailable": bool(llmfit_raw),
        }
        if ls_slice is not None:
            payload["todayCost"] = ls_slice["todayCost"]
            payload["projectedMonthlyCost"] = ls_slice["projectedMonthlyCost"]
            # Only override expensiveOps when DuckDB actually surfaced
            # candidates — keep the in-memory list if the local store is
            # populated but no row crossed the $0.01 threshold.
            if ls_slice.get("expensiveOps"):
                payload["expensiveOps"] = ls_slice["expensiveOps"]
            payload["_source"] = "local_store"
        return jsonify(payload)
    except Exception as e:
        # Hard fallback path: even llmfit + everything else broke. Use real
        # host detection so we never lie about the user's machine.
        return jsonify(
            {
                "system": _d._detect_host_hardware(),
                "localModels": [],
                "taskRecommendations": [],
                "todayCost": 0,
                "projectedMonthlyCost": 0,
                "potentialSavings": "Install llmfit for recommendations",
                "error": str(e),
                "ollamaInstalled": False,
                "llmfitAvailable": False,
            }
        )


@bp_config.route("/api/cost-optimization")
def api_cost_optimization():
    """Cost optimization analysis and local model fallback recommendations.

    Tier-1 DuckDB fast path (refs #1565): the legacy ``_get_cost_summary``
    / ``_get_expensive_operations`` helpers read ``dashboard._metrics_store``
    (an in-memory ring populated by the HTTP interceptor) which resets on
    every dashboard restart — the panel renders $0 with no candidates even
    when DuckDB holds weeks of real usage rows. When the local store has
    data, swap in its values for the data-derived slice (costs +
    expensiveOps). Falls back to the legacy in-memory ring on empty store
    or when ``CLAWMETRY_LOCAL_STORE_READ`` is off.
    """
    import dashboard as _d
    try:
        # Get cost metrics
        costs = _d._get_cost_summary()

        # Check Ollama availability
        local_models_ollama = _d._check_ollama_availability()

        # Generate recommendations
        recommendations = _d._generate_cost_recommendations(costs, local_models_ollama)

        # Get recent expensive operations
        expensive_ops = _d._get_expensive_operations()

        # DuckDB fast path — swap in DuckDB-derived values for the data
        # slice when the local store has rows. Keeps host-state slices
        # (localModels / llmfit / ollamaInstalled / savingsOpportunities)
        # on the legacy path; only swaps the data-derived fields.
        source_local = False
        if is_local_store_read_enabled():
            try:
                ls_slice = _try_local_store_cost_optimization()
            except Exception:
                ls_slice = None
            if ls_slice is not None:
                costs = ls_slice["costs"]
                # Only override expensiveOps when DuckDB actually surfaced
                # candidates — mirrors the sibling cost-optimizer behavior
                # so a populated store with no $0.01+ rows keeps the ring.
                if ls_slice.get("expensiveOps"):
                    expensive_ops = ls_slice["expensiveOps"]
                # Recompute recommendations against the DuckDB costs so the
                # banner copy matches the displayed numbers.
                recommendations = _d._generate_cost_recommendations(
                    costs, local_models_ollama
                )
                source_local = True

        # Get llmfit local model recommendations
        llmfit_data = _d._get_llmfit_recommendations()

        # Check if ollama binary is installed
        ollama_installed = _d._detect_ollama()

        # Build savings opportunities
        savings = _d._generate_savings_opportunities()

        payload = {
            "costs": costs,
            "localModels": local_models_ollama,
            "recommendations": recommendations,
            "expensiveOps": expensive_ops,
            "llmfit": llmfit_data,
            "ollamaInstalled": ollama_installed,
            "llmfitAvailable": llmfit_data.get("available", False),
            "savingsOpportunities": savings,
        }
        if source_local:
            payload["_source"] = "local_store"
        return jsonify(payload)
    except Exception as e:
        return jsonify(
            {
                "costs": {"today": 0, "week": 0, "month": 0, "projected": 0},
                "localModels": {"available": False, "count": 0, "models": []},
                "recommendations": [
                    {"title": "API Error", "description": str(e), "priority": "low"}
                ],
                "expensiveOps": [],
                "llmfit": {
                    "available": False,
                    "recommendations": [],
                    "codingModels": [],
                    "chatModels": [],
                    "system": {},
                },
                "ollamaInstalled": False,
                "llmfitAvailable": False,
                "savingsOpportunities": [],
            }
        )


# Tool keys that the legacy log-scanner tracked as "command" patterns. We
# preserve the exact shape here so the unchanged ``_generate_automation_suggestions``
# transformer (in ``dashboard.py``) still emits the same suggestion rows
# for cron / skill candidates (curl, git, npm, systemctl, grep, find, ls).
# Real OpenClaw v3 tool names are mapped onto these legacy buckets so the
# fast path produces equivalent recommendations without re-walking
# moltbot-*.log files that don't exist on most installs.
_AUTOMATION_TOOL_TO_LEGACY = {
    # Bash/exec family → "curl"/"git"/"npm"/"systemctl" classification is
    # delegated to the suggestion transformer via raw tool name. For tools
    # without a legacy bucket we still surface the pattern but the
    # transformer skips the cron/skill upsell — fine, the universal
    # suggestions still land.
    "Bash": "bash",
    "exec": "bash",
    "process": "bash",
    "Read": "read",
    "read": "read",
    "Write": "write",
    "write": "write",
    "write_file": "write",
    "Edit": "edit",
    "edit": "edit",
    "Grep": "grep",
    "grep": "grep",
    "Glob": "find",
    "find": "find",
    "web_search": "curl",       # external HTTP → same bucket as curl
    "ollama_web_search": "curl",
    "web_fetch": "curl",
    "ollama_web_fetch": "curl",
}


def _try_local_store_automation_analysis():
    """Tier-1 DuckDB fast path for /api/automation-analysis (refs #1565).

    Replaces the legacy ``dashboard._analyze_work_patterns`` scanner,
    which reads ``~/.openclaw/logs/moltbot-YYYY-MM-DD.log`` files and
    journalctl output to count tool/command frequency. On modern OpenClaw
    installs those log files don't exist (the agent runtime now writes
    structured JSONL events into the session transcripts, ingested into
    DuckDB by the sync daemon) — so the legacy path silently returns an
    empty pattern list on every fresh install, which then makes the
    suggestion transformer emit ONLY universal fallback rows (no
    tool-driven cron / skill candidates). Same silent-zero hazard as the
    cost-optimizer in-memory ring (see PR #1576).

    This helper queries the daemon-normalised ``events`` table for the
    last 7 days of tool invocations, buckets them by tool name, and
    builds the same ``{title, description, frequency, confidence,
    priority, type, target}`` rows the legacy scanner produced. The
    downstream transformer (``_generate_automation_suggestions``) is
    pure-Python and unchanged — same suggestion shape, same dedupe, same
    8-row cap.

    Returns ``None`` when:
      * the daemon proxy is unreachable AND direct DuckDB open fails
      * the events table has no tool-call rows in the 7d window
        (caller falls back to the legacy log scanner so journalctl users
        keep working)
    """
    from routes.sessions import _ls_call  # late import: avoid cycle
    since_iso = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
    rows = _ls_call(
        "query_tool_call_invocations", since=since_iso, limit=50_000
    ) or []
    if not rows:
        return None

    # Bucket invocations by legacy tool key. We accept both the v3 native
    # name (e.g. "Bash") and the legacy log-scanner key (e.g. "bash") so
    # the suggestion transformer's hard-coded match list keeps working.
    freq: dict = {}
    for r in rows:
        if not isinstance(r, dict):
            continue
        raw = (r.get("name") or "").strip()
        if not raw:
            continue
        key = _AUTOMATION_TOOL_TO_LEGACY.get(raw, raw.lower())
        freq[key] = freq.get(key, 0) + 1

    if not freq:
        return None

    patterns: list = []
    for cmd, count in freq.items():
        # Same threshold as the legacy scanner — 5+ uses/week. Keeps the
        # noise floor identical so callers don't see a flood of new low-
        # confidence rows just because DuckDB has every event.
        if count < 5:
            continue
        confidence = min(90, count * 10)
        priority = "high" if count >= 15 else "medium" if count >= 10 else "low"
        patterns.append({
            "title": f'Frequent "{cmd}" command usage',
            "description": (
                f'Command "{cmd}" has been used {count} times in the past '
                f'week. This might be a candidate for automation.'
            ),
            "frequency": f"{count} times/week",
            "confidence": confidence,
            "priority": priority,
            "type": "command",
            "target": cmd,
            "_source": "local_store",
        })

    if not patterns:
        return None
    patterns.sort(
        key=lambda x: (
            x["priority"] == "high",
            x["priority"] == "medium",
            x["confidence"],
        ),
        reverse=True,
    )
    return patterns


@bp_config.route("/api/automation-analysis")
def api_automation_analysis():
    """Automation pattern analysis and suggestions for new cron jobs or skills."""
    import dashboard as _d
    try:
        patterns = None
        source = None
        if is_local_store_read_enabled():
            try:
                patterns = _try_local_store_automation_analysis()
            except Exception:
                patterns = None
            if patterns is not None:
                source = "local_store"
        if patterns is None:
            # Legacy log-scanner fallback (journalctl + moltbot-*.log).
            patterns = _d._analyze_work_patterns()

        # Pure-Python transformer — unchanged shape. Works on both the
        # DuckDB rows and the legacy log-scanner rows since they share
        # the same {type, target, ...} schema.
        suggestions = _d._generate_automation_suggestions(patterns)

        body = {
            'patterns': patterns,
            'suggestions': suggestions,
            'lastAnalysis': datetime.now(timezone.utc).isoformat(),
        }
        if source:
            body['_source'] = source
        return jsonify(body)
    except Exception as e:
        return jsonify({
            'patterns': [],
            'suggestions': [],
            'error': str(e),
            'lastAnalysis': datetime.now(timezone.utc).isoformat()
        })


def _try_local_store_session_history_tokens():
    """Tier-1 DuckDB fast path for /api/context-anatomy session-history bucket.

    Replaces a 5-file × N-line JSONL scan (the single hottest blocking
    read in this endpoint) with a single SQL aggregate over the events
    table. Returns the most recent non-zero ``usage.input_tokens``
    reading from the latest active session, mirroring the legacy
    behaviour exactly. Returns ``None`` to defer to the JSONL scanner if:
      * the daemon proxy isn't reachable AND direct open fails
      * the events table has no message events with non-zero usage yet
    """
    result = None
    try:
        from routes.local_query import local_store_via_daemon
        result = local_store_via_daemon("query_context_window_peek", scan_sessions=5)
    except Exception:
        result = None
    if result is None:
        # Single-process boots (tests, dev mode) never hit the daemon —
        # open the local store directly.
        try:
            from clawmetry import local_store
            store = local_store.get_store(read_only=True)
            result = store.query_context_window_peek(scan_sessions=5)
        except Exception:
            return None
    if not isinstance(result, dict):
        return None
    tok = result.get("input_tokens") or 0
    try:
        return int(tok)
    except (TypeError, ValueError):
        return None


@bp_config.route("/api/context-anatomy")
def api_context_anatomy():
    """Estimate context window consumption broken down by source (#566).

    Returns a list of buckets with token estimates derived from:
      - Workspace file sizes (SOUL.md, AGENTS.md, TOOLS.md, …)
      - memory/ directory total
      - A fixed tool-definition estimate (~1,500 tok)
      - Session history = last observed input_tokens minus known static buckets

    Token counts are approximations (file_bytes / 3.5 chars-per-token).
    """
    import dashboard as _d

    CHARS_PER_TOKEN = 3.5
    CONTEXT_LIMIT = 200_000  # Claude 200K window

    def _file_tokens(path):
        try:
            return max(1, int(os.path.getsize(path) / CHARS_PER_TOKEN))
        except OSError:
            return 0

    workspace = _d.WORKSPACE or ""
    sessions_dir = _d.SESSIONS_DIR or ""

    buckets = []

    # Static workspace files — each gets its own bucket if present
    _SYSTEM_FILES = [
        ("SOUL.md",      "#a855f7"),
        ("AGENTS.md",    "#3b82f6"),
        ("TOOLS.md",     "#06b6d4"),
        ("HEARTBEAT.md", "#22c55e"),
        ("IDENTITY.md",  "#ec4899"),
        ("USER.md",      "#f59e0b"),
    ]
    for fname, color in _SYSTEM_FILES:
        fpath = os.path.join(workspace, fname) if workspace else ""
        if fpath and os.path.isfile(fpath):
            buckets.append({
                "label": fname,
                "tokens": _file_tokens(fpath),
                "color": color,
                "category": "system",
            })

    # Memory files — summed into one bucket
    memory_dir = os.path.join(workspace, "memory") if workspace else ""
    if memory_dir and os.path.isdir(memory_dir):
        try:
            mem_tokens = sum(
                _file_tokens(os.path.join(memory_dir, f))
                for f in os.listdir(memory_dir)
                if f.endswith(".md")
            )
        except OSError:
            mem_tokens = 0
        if mem_tokens > 0:
            buckets.append({
                "label": "Memory files",
                "tokens": mem_tokens,
                "color": "#059669",
                "category": "memory",
            })

    # Tool definitions — fixed estimate (built-ins + common MCPs)
    TOOL_EST = 1_500
    buckets.append({
        "label": "Tool defs (est.)",
        "tokens": TOOL_EST,
        "color": "#d97706",
        "category": "tools",
    })

    # Session history: total input_tokens from last active session minus known static
    session_history_tokens = 0
    fast_tok = None
    if is_local_store_read_enabled():
        fast_tok = _try_local_store_session_history_tokens()
    if fast_tok is not None and fast_tok > 0:
        session_history_tokens = fast_tok
    elif sessions_dir and os.path.isdir(sessions_dir):
        # Legacy JSONL fallback — preserved verbatim so endpoint stays
        # working when the local store hasn't been ingested yet.
        try:
            files = sorted(
                [
                    f for f in os.listdir(sessions_dir)
                    if f.endswith(".jsonl")
                    and ".deleted." not in f
                    and ".reset." not in f
                ],
                key=lambda f: os.path.getmtime(os.path.join(sessions_dir, f)),
                reverse=True,
            )
            for fname in files[:5]:
                last_input = 0
                try:
                    with open(os.path.join(sessions_dir, fname), errors="replace") as fh:
                        for line in fh:
                            try:
                                ev = json.loads(line.strip())
                                u = (ev.get("message") or {}).get("usage") or {}
                                inp = u.get("input_tokens", 0)
                                if inp:
                                    last_input = inp
                            except Exception:
                                pass
                except Exception:
                    pass
                if last_input > 0:
                    session_history_tokens = last_input
                    break
        except Exception:
            pass

    if session_history_tokens > 0:
        known_static = sum(b["tokens"] for b in buckets)
        dynamic = max(0, session_history_tokens - known_static)
        if dynamic > 0:
            buckets.append({
                "label": "Session history",
                "tokens": dynamic,
                "color": "#0891b2",
                "category": "history",
            })

    total = sum(b["tokens"] for b in buckets)
    return jsonify({
        "buckets": buckets,
        "total_estimated": total,
        "context_limit": CONTEXT_LIMIT,
        "pct_used": round(total / CONTEXT_LIMIT * 100, 1) if CONTEXT_LIMIT else 0,
    })
