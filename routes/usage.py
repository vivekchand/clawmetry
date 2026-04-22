"""
routes/usage.py — Usage / analytics / anomaly / attribution endpoints.

Extracted from dashboard.py as Phase 5.3 of the incremental modularisation.
Owns the 12 routes registered on bp_usage:

  GET  /api/usage                         — headline token/cost tracker
  GET  /api/usage/anomalies               — cost anomaly summary
  GET  /api/anomalies                     — rolling-baseline detector output
  POST /api/anomalies/<id>/ack            — acknowledge an anomaly
  GET  /api/usage/by-plugin               — plugin token/cost breakdown
  GET  /api/usage/by-plugin/trend         — plugin breakdown over time
  GET  /api/sessions/clusters             — behavioural session clustering
  GET  /api/usage/cost-comparison         — alt-model savings estimate
  GET  /api/usage/export                  — CSV export of usage
  GET  /api/model-attribution             — per-model turn/session split
  GET  /api/skill-attribution             — per-skill cost attribution
  GET  /api/token-velocity                — runaway-loop detection

Module-level helpers (``_usage_cache``, ``_compute_transcript_analytics``,
``_detect_and_store_anomalies``, ``_get_anomaly_db``, ``SESSIONS_DIR`` etc.)
stay in ``dashboard.py`` and are reached via late ``import dashboard as _d``.
Pure mechanical move — zero behaviour change.
"""

import json
import os
import time
from collections import defaultdict
from datetime import datetime, timedelta

from flask import Blueprint, jsonify, make_response, request

bp_usage = Blueprint('usage', __name__)


@bp_usage.route("/api/usage")
def api_usage():
    """Token/cost tracking from transcript files - Enhanced OTLP workaround."""
    import dashboard as _d
    import time as _time

    now = _time.time()
    if (
        _d._usage_cache["data"] is not None
        and (now - _d._usage_cache["ts"]) < _d._USAGE_CACHE_TTL
    ):
        return jsonify(_d._usage_cache["data"])

    # Prefer OTLP data when available
    if _d._has_otel_data():
        result = _d._get_otel_usage_data()
        _d._usage_cache["data"] = result
        _d._usage_cache["ts"] = now
        try:
            _d._ext_emit("usage.compiled", {"ok": True})
        except Exception:
            pass
        return jsonify(result)

    analytics = _d._compute_transcript_analytics()
    daily_tokens = analytics.get("daily_tokens", {})
    daily_cost = analytics.get("daily_cost", {})
    daily_input_tokens = analytics.get("daily_input_tokens", {})
    daily_output_tokens = analytics.get("daily_output_tokens", {})
    daily_cache_read_tokens = analytics.get("daily_cache_read_tokens", {})
    daily_cache_write_tokens = analytics.get("daily_cache_write_tokens", {})
    model_usage = analytics.get("model_usage", {})
    session_summaries = analytics.get("sessions", [])
    session_costs = {
        s.get("session_id", ""): round(float(s.get("cost_usd", 0.0) or 0.0), 6)
        for s in session_summaries
    }
    anomalies = _d._compute_session_cost_anomalies(session_summaries)

    # Build response data with cache token breakdown
    today = datetime.now()
    days = []
    for i in range(13, -1, -1):
        d = today - timedelta(days=i)
        ds = d.strftime("%Y-%m-%d")
        days.append(
            {
                "date": ds,
                "tokens": daily_tokens.get(ds, 0),
                "cost": daily_cost.get(ds, 0),
                "inputTokens": daily_input_tokens.get(ds, 0),
                "outputTokens": daily_output_tokens.get(ds, 0),
                "cacheReadTokens": daily_cache_read_tokens.get(ds, 0),
                "cacheWriteTokens": daily_cache_write_tokens.get(ds, 0),
            }
        )

    # Calculate aggregations
    today_str = today.strftime("%Y-%m-%d")
    week_start = (today - timedelta(days=today.weekday())).strftime("%Y-%m-%d")
    month_start = today.strftime("%Y-%m-01")

    today_tok = daily_tokens.get(today_str, 0)
    week_tok = sum(v for k, v in daily_tokens.items() if k >= week_start)
    month_tok = sum(v for k, v in daily_tokens.items() if k >= month_start)

    today_cost = daily_cost.get(today_str, 0)
    week_cost = sum(v for k, v in daily_cost.items() if k >= week_start)
    month_cost = sum(v for k, v in daily_cost.items() if k >= month_start)

    # Trend analysis & predictions
    trend_data = _d._analyze_usage_trends(daily_tokens)

    # Model breakdown for display
    model_breakdown = [
        {"model": k, "tokens": v}
        for k, v in sorted(model_usage.items(), key=lambda x: -x[1])
    ]
    model_billing, billing_summary = _d._build_model_billing(model_usage)

    # Cost warnings
    warnings = _d._generate_cost_warnings(
        today_cost, week_cost, month_cost, trend_data, month_tok, billing_summary
    )

    result = {
        "source": "transcripts",
        "days": days,
        "today": today_tok,
        "week": week_tok,
        "month": month_tok,
        "todayCost": round(today_cost, 4),
        "weekCost": round(week_cost, 4),
        "monthCost": round(month_cost, 4),
        "modelBreakdown": model_breakdown,
        "modelBilling": model_billing,
        "billingSummary": billing_summary,
        "sessionCosts": session_costs,
        "anomalies": anomalies,
        "anomalySessionIds": [a.get("session_id") for a in anomalies],
        "trend": trend_data,
        "warnings": warnings,
    }
    import time as _time

    _d._usage_cache["data"] = result
    _d._usage_cache["ts"] = _time.time()
    return jsonify(result)


@bp_usage.route("/api/usage/anomalies")
def api_usage_anomalies():
    """Return session cost anomalies vs rolling 7-day baseline."""
    import dashboard as _d

    analytics = _d._compute_transcript_analytics()
    session_summaries = analytics.get("sessions", [])
    anomalies = _d._compute_session_cost_anomalies(session_summaries)
    baseline_costs = [
        float(s.get("cost_usd", 0.0) or 0.0)
        for s in session_summaries
        if (time.time() - float(s.get("start_ts", 0) or 0)) <= (7 * 86400)
        and float(s.get("cost_usd", 0.0) or 0.0) > 0
    ]
    baseline_avg = (
        (sum(baseline_costs) / float(len(baseline_costs))) if baseline_costs else 0.0
    )
    return jsonify(
        {
            "anomalies": anomalies,
            "baseline_7d_avg_usd": round(baseline_avg, 6),
            "threshold_multiplier": 2.0,
        }
    )


@bp_usage.route("/api/anomalies")
def api_anomalies():
    """Rolling-baseline anomaly detection endpoint.

    Returns recent anomalies stored in ~/.openclaw/clawmetry.db with:
    - severity: critical/high/medium
    - metric: cost_spike / token_spike / error_rate_spike
    - value: the observed value that triggered the anomaly
    - baseline: the 7-day rolling average used as baseline
    - ratio: value / baseline
    - session_key: session ID (or '__error_rate__' for aggregate)
    - detected_at: Unix timestamp of detection
    """
    import dashboard as _d

    now = time.time()
    if (
        _d._anomaly_detection_cache["data"] is not None
        and (now - _d._anomaly_detection_cache["ts"]) < _d._ANOMALY_CACHE_TTL
    ):
        return jsonify(_d._anomaly_detection_cache["data"])

    anomalies, baselines = _d._detect_and_store_anomalies()
    active = [a for a in anomalies if not a.get("acknowledged")]
    result = {
        "anomalies": anomalies,
        "active_count": len(active),
        "has_active": bool(active),
        "baselines": baselines,
        "threshold_cost_multiplier": 2.0,
        "threshold_token_multiplier": 2.0,
        "threshold_error_multiplier": 3.0,
    }
    _d._anomaly_detection_cache["data"] = result
    _d._anomaly_detection_cache["ts"] = now
    return jsonify(result)


@bp_usage.route("/api/anomalies/<int:anomaly_id>/ack", methods=["POST"])
def api_anomaly_ack(anomaly_id):
    """Acknowledge an anomaly so it no longer appears in the active banner."""
    import dashboard as _d

    try:
        db = _d._get_anomaly_db()
        with _d._anomaly_db_lock:
            db.execute(
                "UPDATE anomalies SET acknowledged = 1 WHERE id = ?", (anomaly_id,)
            )
            db.commit()
        _d._anomaly_detection_cache["data"] = None  # invalidate cache
        return jsonify({"ok": True, "id": anomaly_id})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@bp_usage.route("/api/usage/by-plugin")
def api_usage_by_plugin():
    """Return plugin/skill token and cost attribution from transcript tool calls.

    Enhanced with trend direction (GH#201): compares recent 7-day vs prior 7-day
    cost share to flag plugins getting more expensive. Also emits threshold warnings
    when a plugin's cost share exceeds the configured limit (default 50%).
    """
    import dashboard as _d

    analytics = _d._compute_transcript_analytics()
    plugin_stats = analytics.get("plugin_stats", {})
    plugin_daily_stats = analytics.get("plugin_daily_stats", {})
    total_tokens = sum(
        float(v.get("tokens", 0.0) or 0.0) for v in plugin_stats.values()
    )
    total_tokens = total_tokens if total_tokens > 0 else 1.0

    try:
        threshold_pct = float(request.args.get("threshold", 50.0))
    except (ValueError, TypeError):
        threshold_pct = 50.0

    warnings = []
    rows = []
    for plugin, stats in plugin_stats.items():
        toks = float(stats.get("tokens", 0.0) or 0.0)
        cost = float(stats.get("cost", 0.0) or 0.0)
        calls = int(stats.get("calls", 0) or 0)
        pct = round((toks / total_tokens) * 100.0, 2)
        trend = _d._compute_plugin_trend(plugin, plugin_daily_stats)
        rows.append(
            {
                "plugin": plugin,
                "total_tokens": int(round(toks)),
                "cost_usd": round(cost, 6),
                "call_count": calls,
                "pct_of_total": pct,
                "trend": trend,
            }
        )
        if pct >= threshold_pct:
            warnings.append(
                {
                    "plugin": plugin,
                    "pct_of_total": pct,
                    "message": f"{plugin} accounts for {pct:.1f}% of total token usage "
                               f"(threshold: {threshold_pct:.0f}%)",
                    "trend": trend,
                }
            )
    rows.sort(key=lambda r: r["total_tokens"], reverse=True)
    return jsonify({"plugins": rows, "warnings": warnings})


@bp_usage.route("/api/usage/by-plugin/trend")
def api_usage_by_plugin_trend():
    """Return per-day plugin token and cost breakdown for trend analysis (GH#201).

    Response shape:
      {
        "days": ["2026-03-20", ...],
        "plugins": {
          "exec": [{"day": "2026-03-20", "tokens": 120, "cost_usd": 0.001, "calls": 3}, ...],
          ...
        }
      }
    """
    import dashboard as _d

    analytics = _d._compute_transcript_analytics()
    plugin_daily_stats = analytics.get("plugin_daily_stats", {})

    try:
        days_back = int(request.args.get("days", 14))
    except (ValueError, TypeError):
        days_back = 14
    days_back = min(max(days_back, 1), 90)

    from datetime import date, timedelta
    today = date.today()
    day_list = [(today - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(days_back - 1, -1, -1)]

    # Collect all plugin names that appear in the window
    plugin_names: set = set()
    for d in day_list:
        plugin_names.update(plugin_daily_stats.get(d, {}).keys())

    result: dict = {}
    for p in sorted(plugin_names):
        series = []
        for d in day_list:
            day_data = plugin_daily_stats.get(d, {}).get(p, {})
            series.append(
                {
                    "day": d,
                    "tokens": int(round(float(day_data.get("tokens", 0.0) or 0.0))),
                    "cost_usd": round(float(day_data.get("cost", 0.0) or 0.0), 6),
                    "calls": int(day_data.get("calls", 0) or 0),
                }
            )
        result[p] = series

    return jsonify({"days": day_list, "plugins": result})


@bp_usage.route("/api/sessions/clusters")
def api_sessions_clusters():
    """Cluster sessions by behavior pattern (tool usage, cost profile, error type, model).

    Implements trace clustering similar to PostHog's Clusters for LLM Analytics,
    but with OpenClaw-native dimensions (tool names, skill invocations, cron sessions).
    Closes vivekchand/clawmetry#406.
    """
    import dashboard as _d

    _CLUSTER_ANALYTICS_TTL = 120  # seconds
    now_ts = time.time()

    # Optional time window filter (days)
    try:
        days = int(request.args.get("days", 30))
    except (ValueError, TypeError):
        days = 30
    cutoff_ts = now_ts - (days * 86400)

    sessions_dir = _d._get_sessions_dir()
    if not sessions_dir or not os.path.isdir(sessions_dir):
        return jsonify(
            {
                "clusters": [],
                "total_sessions": 0,
                "days": days,
                "generated_at": int(now_ts * 1000),
            }
        )

    usd_per_tok = _d._estimate_usd_per_token()
    session_profiles = []

    for fname in os.listdir(sessions_dir):
        if not fname.endswith(".jsonl"):
            continue
        fpath = os.path.join(sessions_dir, fname)
        try:
            fmtime = os.path.getmtime(fpath)
            if fmtime < cutoff_ts:
                continue

            sid = fname.replace(".jsonl", "")
            tool_counts = defaultdict(int)
            error_count = 0
            s_tokens = 0
            s_model = "unknown"
            has_cron = False
            has_subagent = False
            turn_count = 0
            s_start = fmtime

            with open(fpath, "r") as f:
                for line in f:
                    try:
                        obj = json.loads(line.strip())
                    except Exception:
                        continue

                    # Detect model
                    message = (
                        obj.get("message", {})
                        if isinstance(obj.get("message"), dict)
                        else {}
                    )
                    model = message.get("model") or obj.get("model")
                    if model:
                        s_model = model

                    # Count tool calls
                    tools = _d._extract_tool_plugins(obj)
                    for t in tools:
                        tool_counts[t] += 1

                    # Count errors
                    if obj.get("type") in ("error", "tool_error") or (
                        isinstance(obj.get("error"), dict) and obj["error"]
                    ):
                        error_count += 1

                    # Detect cron / subagent hints
                    content_str = json.dumps(obj, default=str).lower()
                    if "cron" in content_str or "scheduled" in content_str:
                        has_cron = True
                    if "subagent" in content_str or "spawned" in content_str:
                        has_subagent = True

                    # Usage metrics
                    metrics = _d._extract_usage_metrics(obj)
                    if metrics["tokens"] > 0:
                        s_tokens += metrics["tokens"]
                        turn_count += 1

            if s_tokens == 0 and not tool_counts:
                continue

            total_tools = sum(tool_counts.values())
            top_tool = max(tool_counts, key=tool_counts.get) if tool_counts else "none"
            cost = round(s_tokens * usd_per_tok, 6)

            # Determine cost tier
            if cost >= 0.10:
                cost_tier = "expensive"
            elif cost >= 0.02:
                cost_tier = "medium"
            else:
                cost_tier = "cheap"

            session_profiles.append(
                {
                    "session_id": sid,
                    "model": s_model,
                    "top_tool": top_tool,
                    "tool_counts": dict(tool_counts),
                    "total_tools": total_tools,
                    "error_count": error_count,
                    "tokens": s_tokens,
                    "cost_usd": cost,
                    "cost_tier": cost_tier,
                    "has_cron": has_cron,
                    "has_subagent": has_subagent,
                    "turn_count": turn_count,
                    "fmtime": fmtime,
                }
            )
        except Exception:
            continue

    # ── Clustering logic ────────────────────────────────────────────────────────
    # Cluster key = (dominant_tool_category, cost_tier, error_presence, model_family)

    def _model_family(model_str):
        m = (model_str or "").lower()
        if "claude" in m:
            return "claude"
        if "gpt" in m or "openai" in m:
            return "gpt"
        if "gemini" in m or "google" in m:
            return "gemini"
        if "llama" in m or "mistral" in m or "groq" in m:
            return "open-source"
        return "other"

    def _tool_category(tool_name):
        t = (tool_name or "").lower()
        if t in ("none", ""):
            return "no-tools"
        if t in ("exec", "bash", "shell", "run"):
            return "code-execution"
        if t in ("read", "write", "edit", "file_read", "file_write"):
            return "file-ops"
        if t in ("web_search", "web_fetch", "browser"):
            return "web"
        if t in ("message", "tts", "send_message"):
            return "communication"
        if t in ("sessions_spawn", "sessions_send", "subagents"):
            return "orchestration"
        if t in ("memory_search", "memory_get"):
            return "memory"
        return "other-tools"

    clusters_map = defaultdict(
        lambda: {
            "sessions": [],
            "total_tokens": 0,
            "total_cost_usd": 0.0,
            "error_count": 0,
            "tool_freq": defaultdict(int),
        }
    )

    for sp in session_profiles:
        mf = _model_family(sp["model"])
        tc = _tool_category(sp["top_tool"])
        has_errors = "errors" if sp["error_count"] > 0 else "clean"
        cluster_key = f"{tc}|{sp['cost_tier']}|{has_errors}|{mf}"

        c = clusters_map[cluster_key]
        c["sessions"].append(sp["session_id"])
        c["total_tokens"] += sp["tokens"]
        c["total_cost_usd"] += sp["cost_usd"]
        c["error_count"] += sp["error_count"]
        for tool, cnt in sp["tool_counts"].items():
            c["tool_freq"][tool] += cnt

        # Tag attributes (set once)
        if "tool_category" not in c:
            c["tool_category"] = tc
            c["cost_tier"] = sp["cost_tier"]
            c["has_errors"] = has_errors == "errors"
            c["model_family"] = mf

    # ── Build response ──────────────────────────────────────────────────────────
    clusters_out = []
    for key, c in clusters_map.items():
        n = len(c["sessions"])
        avg_cost = c["total_cost_usd"] / n if n > 0 else 0.0
        top_tools_sorted = sorted(
            c["tool_freq"].items(), key=lambda x: x[1], reverse=True
        )[:5]

        # Auto-label cluster
        tc = c.get("tool_category", "other")
        cost_tier = c.get("cost_tier", "cheap")
        mf = c.get("model_family", "other")
        has_err = c.get("has_errors", False)
        label_parts = []
        if tc == "code-execution":
            label_parts.append("Code execution")
        elif tc == "file-ops":
            label_parts.append("File operations")
        elif tc == "web":
            label_parts.append("Web browsing")
        elif tc == "communication":
            label_parts.append("Messaging")
        elif tc == "orchestration":
            label_parts.append("Agent orchestration")
        elif tc == "memory":
            label_parts.append("Memory access")
        elif tc == "no-tools":
            label_parts.append("Conversational")
        else:
            label_parts.append("Mixed tools")
        if cost_tier == "expensive":
            label_parts.append("high-cost")
        elif cost_tier == "medium":
            label_parts.append("medium-cost")
        if has_err:
            label_parts.append("with errors")
        if mf not in ("claude", "other"):
            label_parts.append(mf)

        cluster_label = " ".join(label_parts)

        clusters_out.append(
            {
                "cluster_id": key,
                "label": cluster_label,
                "session_count": n,
                "session_ids": c["sessions"][:10],  # first 10 for drill-down
                "total_tokens": c["total_tokens"],
                "total_cost_usd": round(c["total_cost_usd"], 6),
                "avg_cost_usd": round(avg_cost, 6),
                "error_count": c["error_count"],
                "tool_category": tc,
                "cost_tier": cost_tier,
                "has_errors": has_err,
                "model_family": mf,
                "top_tools": [{"tool": t, "count": cnt} for t, cnt in top_tools_sorted],
            }
        )

    clusters_out.sort(key=lambda x: x["session_count"], reverse=True)

    return jsonify(
        {
            "clusters": clusters_out,
            "total_sessions": len(session_profiles),
            "days": days,
            "generated_at": int(now_ts * 1000),
        }
    )


@bp_usage.route("/api/usage/cost-comparison")
def api_usage_cost_comparison():
    """Return cost comparison: actual spend vs alternatives (GH#554)."""
    import dashboard as _d

    try:
        return jsonify(_d._build_cost_comparison())
    except Exception as e:
        return jsonify({"error": str(e), "alternatives": [], "actual": {}}), 500


@bp_usage.route("/api/usage/export")
def api_usage_export():
    """Export usage data as CSV."""
    import dashboard as _d

    try:
        # Get usage data
        if _d._has_otel_data():
            data = _d._get_otel_usage_data()
        else:
            # Call the same logic as /api/usage but get full data
            sessions_dir = _d.SESSIONS_DIR or os.path.expanduser(
                "~/.openclaw/agents/main/sessions"
            )
            daily_tokens = {}

            if os.path.isdir(sessions_dir):
                for fname in os.listdir(sessions_dir):
                    if not fname.endswith(".jsonl"):
                        continue
                    fpath = os.path.join(sessions_dir, fname)
                    try:
                        fmtime = datetime.fromtimestamp(os.path.getmtime(fpath))
                        with open(fpath, "r") as f:
                            for line in f:
                                try:
                                    obj = json.loads(line.strip())
                                    tokens = 0
                                    usage = (
                                        obj.get("usage") or obj.get("tokens_used") or {}
                                    )
                                    if isinstance(usage, dict):
                                        tokens = (
                                            usage.get("total_tokens")
                                            or usage.get("totalTokens")
                                            or (
                                                usage.get("input_tokens", 0)
                                                + usage.get("output_tokens", 0)
                                            )
                                            or 0
                                        )
                                    elif isinstance(usage, (int, float)):
                                        tokens = int(usage)
                                    if not tokens:
                                        content = obj.get("content", "")
                                        if (
                                            isinstance(content, str)
                                            and len(content) > 0
                                        ):
                                            tokens = max(1, len(content) // 4)
                                        elif isinstance(content, list):
                                            total_len = sum(
                                                len(str(c.get("text", "")))
                                                for c in content
                                                if isinstance(c, dict)
                                            )
                                            tokens = (
                                                max(1, total_len // 4)
                                                if total_len
                                                else 0
                                            )
                                    ts = (
                                        obj.get("timestamp")
                                        or obj.get("time")
                                        or obj.get("created_at")
                                    )
                                    if ts:
                                        if isinstance(ts, (int, float)):
                                            dt = datetime.fromtimestamp(
                                                ts / 1000 if ts > 1e12 else ts
                                            )
                                        else:
                                            try:
                                                dt = datetime.fromisoformat(
                                                    str(ts).replace("Z", "+00:00")
                                                )
                                            except Exception:
                                                dt = fmtime
                                    else:
                                        dt = fmtime
                                    day = dt.strftime("%Y-%m-%d")
                                    if tokens > 0:
                                        daily_tokens[day] = (
                                            daily_tokens.get(day, 0) + tokens
                                        )
                                except (json.JSONDecodeError, ValueError):
                                    pass
                    except Exception:
                        pass

            today = datetime.now()
            today_str = today.strftime("%Y-%m-%d")
            week_start = (today - timedelta(days=today.weekday())).strftime("%Y-%m-%d")
            month_start = today.strftime("%Y-%m-01")

            # Build data structure similar to OTLP
            days = []
            for i in range(30, -1, -1):  # Last 30 days for export
                d = today - timedelta(days=i)
                ds = d.strftime("%Y-%m-%d")
                tokens = daily_tokens.get(ds, 0)
                cost = round(tokens * (30.0 / 1_000_000), 4)  # Default pricing
                days.append({"date": ds, "tokens": tokens, "cost": cost})

            data = {'days': days}

        # Generate CSV content
        csv_lines = ['Date,Tokens,Cost']
        for day in data['days']:
            csv_lines.append(f"{day['date']},{day['tokens']},{day.get('cost', 0):.4f}")

        csv_content = '\n'.join(csv_lines)

        response = make_response(csv_content)
        response.headers['Content-Type'] = 'text/csv'
        response.headers['Content-Disposition'] = f'attachment; filename=openclaw-usage-{datetime.now().strftime("%Y%m%d")}.csv'
        return response

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp_usage.route('/api/model-attribution')
def api_model_attribution():
    """Per-model turn/session breakdown and switch history (GH #300)."""
    import dashboard as _d

    sessions_dir = _d.SESSIONS_DIR or os.path.expanduser('~/.openclaw/agents/main/sessions')
    model_turns = {}    # model -> assistant turn count
    model_sessions = {} # model -> session count
    switches = []       # list of {session, from_model, to_model}

    if os.path.isdir(sessions_dir):
        for fname in os.listdir(sessions_dir):
            if not fname.endswith('.jsonl') or 'deleted' in fname:
                continue
            sid = fname.replace('.jsonl', '')
            fpath = os.path.join(sessions_dir, fname)
            try:
                current_model = None
                session_start_model = None
                with open(fpath, 'r', encoding='utf-8', errors='replace') as f:
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            obj = json.loads(line)
                        except (json.JSONDecodeError, ValueError):
                            continue
                        t = obj.get('type', '')
                        # Detect model changes
                        if t == 'model_change':
                            new_model = obj.get('modelId') or obj.get('model') or ''
                            if new_model:
                                if current_model and current_model != new_model:
                                    switches.append({
                                        'session': sid,
                                        'from_model': current_model,
                                        'to_model': new_model,
                                    })
                                current_model = new_model
                                if session_start_model is None:
                                    session_start_model = new_model
                        elif t == 'custom':
                            ct = obj.get('customType', '')
                            if ct == 'model-snapshot':
                                d = obj.get('data', {})
                                m = d.get('modelId') or d.get('model') or ''
                                if m and current_model is None:
                                    current_model = m
                                    session_start_model = m
                        # Count assistant turns per model
                        msg = obj.get('message', {})
                        if isinstance(msg, dict) and msg.get('role') == 'assistant':
                            m = msg.get('model') or obj.get('model') or current_model or 'unknown'
                            if m:
                                model_turns[m] = model_turns.get(m, 0) + 1
                # Track which model a session primarily used (first detected)
                primary = session_start_model or current_model
                if primary:
                    model_sessions[primary] = model_sessions.get(primary, 0) + 1
            except Exception:
                pass

    total_turns = sum(model_turns.values())
    # Build sorted model list
    sorted_models = sorted(model_turns.items(), key=lambda x: -x[1])
    primary_model = sorted_models[0][0] if sorted_models else ''

    models_out = []
    for m, turns in sorted_models:
        models_out.append({
            'model': m,
            'turns': turns,
            'sessions': model_sessions.get(m, 0),
            'provider': _d._provider_from_model(m),
            'share_pct': round(turns / total_turns * 100, 2) if total_turns else 0,
        })

    return jsonify({
        'models': models_out,
        'primary_model': primary_model,
        'total_turns': total_turns,
        'model_count': len(model_turns),
        'switches': switches[:50],  # cap at 50 for response size
        'switch_count': len(switches),
    })


@bp_usage.route('/api/skill-attribution')
def api_skill_attribution():
    """Per-skill cost attribution with ClawHub integration hooks (GH #308).

    Detects skill invocations by scanning session transcripts for SKILL.md file
    reads. Each time a SKILL.md is read, the session's token cost is attributed
    to that skill (shared equally when multiple skills are read in one session).

    Returns:
        {
          "skills": [
            {
              "name": str,
              "invocations": int,
              "total_cost_usd": float,
              "avg_cost_usd": float,
              "last_used": str | null,   # ISO timestamp
              "clawhub_url": str,        # future ClawHub skill marketplace link
            }
          ],
          "top5_week": [...],            # top 5 by total_cost_usd in last 7 days
          "total_cost": float,
          "note": str,
          "clawhub": {"enabled": false, "url": null},
        }
    """
    import dashboard as _d
    import re as _re

    sessions_dir = _d._get_sessions_dir()
    if not sessions_dir or not os.path.isdir(sessions_dir):
        return jsonify({
            "skills": [], "top5_week": [], "total_cost": 0.0,
            "note": "No sessions directory found.",
            "clawhub": {"enabled": False, "url": None},
        })

    SKILL_MD_RE = _re.compile(r'[/\\]([^/\\]+)[/\\]SKILL\.md', _re.IGNORECASE)
    # Also match bare "SKILL.md" references with skill name in path context
    SKILL_PATH_RE = _re.compile(r'skills[/\\]([^/\\]+)', _re.IGNORECASE)

    skill_stats = {}   # name -> {invocations, total_cost, last_used_ts}
    now_ts = time.time()
    week_cutoff = now_ts - 7 * 86400
    usd_per_token = _d._estimate_usd_per_token()

    try:
        for fname in os.listdir(sessions_dir):
            if not fname.endswith('.jsonl'):
                continue
            fpath = os.path.join(sessions_dir, fname)
            session_skills = set()
            session_tokens = 0
            session_cost = 0.0
            session_ts = os.path.getmtime(fpath)

            try:
                with open(fpath, 'r', errors='replace') as f:
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            obj = json.loads(line)
                        except Exception:
                            continue

                        # Detect SKILL.md file reads in tool calls / tool results
                        raw = json.dumps(obj)
                        for m in SKILL_MD_RE.finditer(raw):
                            skill_name = m.group(1)
                            if skill_name and skill_name.lower() != 'skills':
                                session_skills.add(skill_name)
                        # Fallback: skills/ path pattern
                        if not session_skills:
                            for m in SKILL_PATH_RE.finditer(raw):
                                candidate = m.group(1)
                                if candidate and 'SKILL' in raw[m.start():m.end()+30].upper():
                                    session_skills.add(candidate)

                        # Accumulate session tokens/cost
                        usage = _d._extract_usage_metrics(obj)
                        if usage['tokens'] > 0:
                            session_tokens += usage['tokens']
                            session_cost += usage['cost'] if usage['cost'] > 0 else (
                                usage['tokens'] * usd_per_token
                            )
            except Exception:
                continue

            if not session_skills:
                continue

            share = session_cost / len(session_skills) if session_skills else 0.0
            for skill in session_skills:
                if skill not in skill_stats:
                    skill_stats[skill] = {'invocations': 0, 'total_cost': 0.0, 'last_used_ts': 0.0}
                skill_stats[skill]['invocations'] += 1
                skill_stats[skill]['total_cost'] += share
                if session_ts > skill_stats[skill]['last_used_ts']:
                    skill_stats[skill]['last_used_ts'] = session_ts
    except Exception:
        pass

    skills_out = []
    total_cost = 0.0
    for name, st in sorted(skill_stats.items(), key=lambda x: -x[1]['total_cost']):
        inv = st['invocations']
        tc = round(float(st['total_cost']), 6)
        avg = round(tc / inv, 6) if inv else 0.0
        lts = st['last_used_ts']
        last_used = datetime.utcfromtimestamp(lts).strftime('%Y-%m-%dT%H:%M:%SZ') if lts else None
        total_cost += tc
        skills_out.append({
            'name': name,
            'invocations': inv,
            'total_cost_usd': tc,
            'avg_cost_usd': avg,
            'last_used': last_used,
            'clawhub_url': f'https://clawhub.dev/skills/{name}',
        })

    # top5 this week
    top5_week = [
        s for s in skills_out
        if s['last_used'] and s['last_used'] >= datetime.utcfromtimestamp(week_cutoff).strftime('%Y-%m-%dT%H:%M:%SZ')
    ][:5]

    note = 'Skills detected from SKILL.md file reads in session transcripts.'

    return jsonify({
        'skills': skills_out,
        'top5_week': top5_week,
        'total_cost': round(total_cost, 6),
        'note': note,
        'clawhub': {'enabled': False, 'url': None},
    })


@bp_usage.route('/api/token-velocity')
def api_token_velocity():
    """Sliding 2-min token velocity endpoint — detects runaway agent loops (GH #313).

    Returns:
      {
        alert: bool,
        level: "ok" | "warning" | "critical",
        velocity_2min: int,       # total tokens in last 2 minutes
        cost_per_min: float,      # estimated USD/min burn rate
        flagged_sessions: [       # sessions exceeding thresholds
          {id, tokens_2min, tool_chain_len, cost_per_min}
        ]
      }

    Thresholds:
      warning:  velocity_2min >= 8000
      critical: velocity_2min >= 15000 OR tool_chain_len >= 20
    """
    import dashboard as _d

    WARN_TOKENS   = 8000
    CRIT_TOKENS   = 15000
    CRIT_TOOLS    = 20

    now        = time.time()
    window_2min = now - 120

    sessions_dir = _d.SESSIONS_DIR or os.path.expanduser('~/.openclaw/agents/main/sessions')
    total_tokens_2min = 0
    flagged = []

    try:
        if os.path.isdir(sessions_dir):
            candidates = sorted(
                [f for f in os.listdir(sessions_dir)
                 if f.endswith('.jsonl') and 'deleted' not in f],
                key=lambda f: os.path.getmtime(os.path.join(sessions_dir, f)),
                reverse=True
            )[:20]

            for fname in candidates:
                fpath = os.path.join(sessions_dir, fname)
                try:
                    mtime = os.path.getmtime(fpath)
                    if now - mtime > 300:          # skip inactive sessions > 5 min
                        continue
                    tokens_2min   = 0
                    consecutive   = 0
                    max_chain     = 0
                    with open(fpath, 'r', errors='replace') as fh:
                        lines = list(fh)
                    for line in lines:
                        try:
                            obj = json.loads(line.strip())
                        except Exception:
                            continue
                        ts = _d._json_ts_to_epoch(
                            obj.get('timestamp') or obj.get('time') or obj.get('created_at')
                        )
                        msg     = obj.get('message', {}) if isinstance(obj.get('message'), dict) else {}
                        role    = msg.get('role', '') or obj.get('role', '')
                        content = msg.get('content', [])
                        is_tool = False
                        if isinstance(content, list):
                            for blk in content:
                                if isinstance(blk, dict) and blk.get('type') == 'tool_use':
                                    is_tool = True
                                    break
                        if role == 'user' and not is_tool:
                            consecutive = 0
                        elif is_tool or role == 'assistant':
                            consecutive += 1
                            max_chain = max(max_chain, consecutive)
                        if ts and ts >= window_2min:
                            usage = msg.get('usage', {}) if isinstance(msg.get('usage'), dict) else {}
                            tok = float(
                                usage.get('total_tokens')
                                or usage.get('totalTokens')
                                or (usage.get('input_tokens', 0) + usage.get('output_tokens', 0))
                                or 0
                            )
                            tokens_2min += int(tok)

                    total_tokens_2min += tokens_2min
                    usd_per_token = _d._estimate_usd_per_token()
                    sess_tpm = _d._session_burn_stats(fname.replace('.jsonl', '')).get('tokensPerMin', 0)
                    sess_cpm = round(sess_tpm * usd_per_token, 5)

                    if tokens_2min >= WARN_TOKENS or max_chain >= CRIT_TOOLS:
                        flagged.append({
                            'id':           fname.replace('.jsonl', ''),
                            'tokens_2min':  tokens_2min,
                            'tool_chain_len': max_chain,
                            'cost_per_min': sess_cpm,
                        })
                except Exception:
                    continue
    except Exception:
        pass

    if total_tokens_2min >= CRIT_TOKENS or any(s['tool_chain_len'] >= CRIT_TOOLS for s in flagged):
        level = 'critical'
    elif total_tokens_2min >= WARN_TOKENS:
        level = 'warning'
    else:
        level = 'ok'

    usd_per_token  = _d._estimate_usd_per_token()
    cost_per_min   = round(total_tokens_2min / 2 * usd_per_token, 5)   # tokens/2min → per min

    return jsonify({
        'alert':            level != 'ok',
        'level':            level,
        'velocity_2min':    total_tokens_2min,
        'cost_per_min':     cost_per_min,
        'flagged_sessions': flagged,
    })


@bp_usage.route('/api/token-attribution')
def api_token_attribution():
    """Per-message cost attribution with cache token breakdown.

    Returns granular token/cost breakdown per message type (input, output, cache-read, cache-write)
    for the specified session or across recent sessions.
    """
    import dashboard as _d

    wanted_sid = request.args.get('session_id', '').strip()
    try:
        limit = max(1, min(int(request.args.get('limit', '100')), 1000))
    except ValueError:
        limit = 100

    sessions_dir = _d._get_sessions_dir()
    if not os.path.isdir(sessions_dir):
        return jsonify({"messages": [], "totals": {}, "note": "sessions dir not found"})

    try:
        all_files = [
            f for f in os.listdir(sessions_dir)
            if f.endswith('.jsonl') and '.deleted.' not in f and '.reset.' not in f
        ]
    except OSError:
        all_files = []

    if wanted_sid:
        files = [f for f in all_files if f.startswith(wanted_sid)]
    else:
        files = sorted(
            all_files,
            key=lambda f: os.path.getmtime(os.path.join(sessions_dir, f)),
            reverse=True
        )[:50]

    messages = []
    totals = {
        'input_tokens': 0,
        'output_tokens': 0,
        'cache_read_tokens': 0,
        'cache_write_tokens': 0,
        'total_tokens': 0,
        'input_cost': 0.0,
        'output_cost': 0.0,
        'cache_read_cost': 0.0,
        'cache_write_cost': 0.0,
        'total_cost': 0.0,
    }

    for fname in files:
        fpath = os.path.join(sessions_dir, fname)
        sid = fname[:-6] if fname.endswith('.jsonl') else fname

        try:
            with open(fpath, 'r', errors='replace') as fh:
                for raw in fh:
                    raw = raw.strip()
                    if not raw:
                        continue
                    try:
                        ev = json.loads(raw)
                    except Exception:
                        continue

                    if ev.get('type') != 'message':
                        continue

                    msg = ev.get('message', {}) or {}
                    if not isinstance(msg, dict):
                        continue

                    usage = msg.get('usage', {}) or {}
                    if not isinstance(usage, dict) or not usage:
                        continue

                    # Get token breakdown
                    input_tok = int(usage.get('input', usage.get('input_tokens', 0)) or 0)
                    output_tok = int(usage.get('output', usage.get('output_tokens', 0)) or 0)
                    cache_read = int(usage.get('cacheRead', usage.get('cache_read_tokens', 0)) or 0)
                    cache_write = int(usage.get('cacheWrite', usage.get('cache_write_tokens', 0)) or 0)

                    # Get cost breakdown
                    cost_obj = usage.get('cost', {}) or {}
                    if isinstance(cost_obj, dict):
                        input_cost = float(cost_obj.get('input', 0) or 0)
                        output_cost = float(cost_obj.get('output', 0) or 0)
                        cache_read_cost = float(cost_obj.get('cacheRead', 0) or 0)
                        cache_write_cost = float(cost_obj.get('cacheWrite', 0) or 0)
                        total_cost = float(cost_obj.get('total', cost_obj.get('usd', 0)) or 0)
                    else:
                        input_cost = output_cost = cache_read_cost = cache_write_cost = total_cost = 0.0

                    total_tok = input_tok + output_tok + cache_read + cache_write

                    if total_tok == 0:
                        continue

                    msg_data = {
                        'session_id': sid,
                        'timestamp': ev.get('timestamp') or ev.get('time') or ev.get('created_at'),
                        'model': msg.get('model', 'unknown'),
                        'role': msg.get('role', 'unknown'),
                        'tokens': {
                            'input': input_tok,
                            'output': output_tok,
                            'cache_read': cache_read,
                            'cache_write': cache_write,
                            'total': total_tok,
                        },
                        'cost': {
                            'input': round(input_cost, 8),
                            'output': round(output_cost, 8),
                            'cache_read': round(cache_read_cost, 8),
                            'cache_write': round(cache_write_cost, 8),
                            'total': round(total_cost, 8),
                        },
                        'cache_hit_ratio': round(cache_read / (input_tok + cache_read) * 100, 1) if (input_tok + cache_read) > 0 else 0.0,
                    }

                    messages.append(msg_data)

                    # Update totals
                    totals['input_tokens'] += input_tok
                    totals['output_tokens'] += output_tok
                    totals['cache_read_tokens'] += cache_read
                    totals['cache_write_tokens'] += cache_write
                    totals['total_tokens'] += total_tok
                    totals['input_cost'] += input_cost
                    totals['output_cost'] += output_cost
                    totals['cache_read_cost'] += cache_read_cost
                    totals['cache_write_cost'] += cache_write_cost
                    totals['total_cost'] += total_cost
        except Exception:
            continue

    # Round totals
    for k in ['input_cost', 'output_cost', 'cache_read_cost', 'cache_write_cost', 'total_cost']:
        totals[k] = round(totals[k], 6)

    # Sort by timestamp descending and apply limit
    messages.sort(key=lambda m: m.get('timestamp', ''), reverse=True)
    messages = messages[:limit]

    # Calculate cache hit ratio
    input_plus_cache = totals['input_tokens'] + totals['cache_read_tokens']
    totals['cache_hit_ratio_pct'] = round(totals['cache_read_tokens'] / input_plus_cache * 100, 1) if input_plus_cache else 0.0

    return jsonify({
        'messages': messages,
        'totals': totals,
        'session_id': wanted_sid if wanted_sid else None,
    })
