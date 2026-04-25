"""
routes/sessions.py — Session / transcript / sub-agent API endpoints.

Extracted from dashboard.py as the first step of an incremental modularisation.
This Blueprint owns the 13 HTTP routes that power the Sessions tab, the
transcript viewer, the sub-agent tree, the cost-split view, OTLP export,
and emergency session-stop.

All module-level helpers (``_get_sessions``, ``_augment_sessions_with_burn``,
``_gw_invoke``, ``_compute_transcript_analytics``, ``SESSIONS_DIR`` etc.) remain
in ``dashboard.py``. Each route handler does a late ``import dashboard as _d``
so we avoid a circular import at module-load time, matching the convention
used by ``clawmetry-cloud/routes/cloud.py``.

Pure mechanical move — zero behaviour change from the previous in-file
definitions.
"""

import json
import os
import sys
import time
from datetime import datetime

from flask import Blueprint, jsonify, request

bp_sessions = Blueprint('sessions', __name__)


@bp_sessions.route("/api/sessions")
def api_sessions():
    """Return sessions with sessionType classification and optional type filter.

    Query params:
      type (optional): filter by session type — main | heartbeat | user | sub-agent
        "all" or omitted returns every session.
    """
    import dashboard as _d
    type_filter = (request.args.get("type", "") or "").strip().lower()

    gw_data = _d._gw_invoke("sessions_list", {"limit": 50, "messageLimit": 0})
    if gw_data and "sessions" in gw_data:
        sessions = _d._augment_sessions_with_burn(gw_data["sessions"])
    else:
        sessions = _d._augment_sessions_with_burn(_d._get_sessions())

    # Build per-type summary before filtering
    type_counts: dict = {}
    type_cost: dict = {}
    for s in sessions:
        t = s.get("sessionType", "main")
        type_counts[t] = type_counts.get(t, 0) + 1
        cost = float(s.get("burnRateUsd", 0) or s.get("totalCostUsd", 0) or 0)
        type_cost[t] = round(type_cost.get(t, 0.0) + cost, 6)

    summary = {
        t: {"count": type_counts.get(t, 0), "total_cost_usd": type_cost.get(t, 0.0)}
        for t in ("main", "heartbeat", "user", "sub-agent")
    }
    summary["total"] = len(sessions)

    if type_filter and type_filter != "all":
        sessions = [s for s in sessions if s.get("sessionType", "main") == type_filter]

    return jsonify({"sessions": sessions, "summary": summary})


@bp_sessions.route("/api/compactions")
def api_compactions():
    """Return OpenClaw session-compaction events.

    OpenClaw compacts long sessions: when context fills up, it summarises
    earlier messages into a markdown `summary` and drops the originals.
    The compaction summary is often the single best "what did my agent do"
    artifact for a long session — we weren't surfacing any of it.

    Params:
      session_id (optional): filter to one session; returns full summary text.
      summary_chars (optional, default=500 when no session_id): truncate
        `summary` to this many chars to keep list responses compact.
    """
    import dashboard as _d
    wanted_sid = request.args.get("session_id", "").strip()
    try:
        summary_chars = max(100, min(int(request.args.get("summary_chars", "500")), 50000))
    except ValueError:
        summary_chars = 500
    full_summary = bool(wanted_sid)

    sessions_dir = _d.SESSIONS_DIR or os.path.expanduser(
        "~/.openclaw/agents/main/sessions"
    )
    if not os.path.isdir(sessions_dir):
        return jsonify({
            "compactions": [],
            "total_compactions": 0,
            "total_tokens_compacted": 0,
            "note": "sessions dir not found",
        })

    try:
        all_files = [
            f
            for f in os.listdir(sessions_dir)
            if f.endswith(".jsonl") and ".deleted." not in f and ".reset." not in f
        ]
    except OSError:
        all_files = []

    if wanted_sid:
        files = [f for f in all_files if f.startswith(wanted_sid)]
    else:
        files = sorted(
            all_files,
            key=lambda f: os.path.getmtime(os.path.join(sessions_dir, f)),
            reverse=True,
        )[:100]

    compactions: list = []
    total_tokens = 0
    for fname in files:
        fpath = os.path.join(sessions_dir, fname)
        sid = fname[:-len(".jsonl")] if fname.endswith(".jsonl") else fname
        try:
            with open(fpath, "r", errors="replace") as fh:
                for raw in fh:
                    raw = raw.strip()
                    if not raw or '"compaction"' not in raw:
                        continue
                    try:
                        ev = json.loads(raw)
                    except Exception:
                        continue
                    if ev.get("type") != "compaction":
                        continue
                    ts = ev.get("timestamp", "")
                    ts_ms = 0
                    if isinstance(ts, str) and ts:
                        try:
                            from datetime import datetime as _dt
                            ts_ms = int(
                                _dt.fromisoformat(ts.replace("Z", "+00:00")).timestamp()
                                * 1000
                            )
                        except Exception:
                            ts_ms = 0
                    summary = ev.get("summary", "") or ""
                    tokens_before = int(ev.get("tokensBefore", 0) or 0)
                    total_tokens += tokens_before
                    entry = {
                        "session_id": sid,
                        "timestamp": ts,
                        "ts_ms": ts_ms,
                        "tokens_before": tokens_before,
                        "first_kept_entry_id": ev.get("firstKeptEntryId", "") or "",
                        "from_hook": bool(ev.get("fromHook", False)),
                    }
                    if full_summary or len(summary) <= summary_chars:
                        entry["summary"] = summary
                    else:
                        entry["summary"] = summary[:summary_chars]
                        entry["summary_truncated"] = True
                    compactions.append(entry)
        except Exception:
            continue

    compactions.sort(key=lambda c: c.get("ts_ms", 0), reverse=True)
    return jsonify({
        "compactions": compactions,
        "total_compactions": len(compactions),
        "total_tokens_compacted": total_tokens,
    })


@bp_sessions.route("/api/session-tools")
def api_session_tools():
    """Return the tool_call / tool_result timeline for a single session."""
    import dashboard as _d
    sid = (request.args.get("session_id", "") or "").strip()
    if not sid:
        return jsonify({"error": "session_id required"}), 400
    try:
        args_chars = max(0, min(int(request.args.get("args_chars", "400")), 10000))
    except ValueError:
        args_chars = 400
    try:
        result_chars = max(0, min(int(request.args.get("result_chars", "400")), 10000))
    except ValueError:
        result_chars = 400
    include_unpaired = str(request.args.get("include_unpaired", "")).lower() in (
        "1", "true", "yes"
    )
    sessions_dir = _d.SESSIONS_DIR or os.path.expanduser(
        "~/.openclaw/agents/main/sessions"
    )
    if not os.path.isdir(sessions_dir):
        return jsonify({"error": "sessions dir not found"}), 404
    matches = [
        f for f in os.listdir(sessions_dir)
        if f.startswith(sid) and f.endswith(".jsonl")
        and ".deleted." not in f and ".reset." not in f
    ]
    if not matches:
        return jsonify({"error": "session not found"}), 404
    fpath = os.path.join(sessions_dir, sorted(matches)[0])

    def _parse_ts(ts):
        if not ts or not isinstance(ts, str):
            return 0
        try:
            from datetime import datetime as _dt
            return int(_dt.fromisoformat(ts.replace("Z", "+00:00")).timestamp() * 1000)
        except Exception:
            return 0

    def _truncate(val, limit):
        if limit <= 0 or val is None:
            return val
        if isinstance(val, str):
            return val if len(val) <= limit else val[:limit] + "…"
        try:
            s = json.dumps(val, separators=(",", ":"))
        except Exception:
            s = str(val)
        return s if len(s) <= limit else s[:limit] + "…"

    calls: dict = {}
    result_by_id: dict = {}
    turn_index = 0
    try:
        with open(fpath, "r", errors="replace") as fh:
            for raw in fh:
                raw = raw.strip()
                if not raw:
                    continue
                try:
                    ev = json.loads(raw)
                except Exception:
                    continue
                if ev.get("type") != "message":
                    continue
                msg = ev.get("message", {}) or {}
                role = msg.get("role", "")
                ev_ts_ms = _parse_ts(ev.get("timestamp", ""))
                if role == "assistant":
                    turn_index += 1
                    content = msg.get("content") or []
                    if not isinstance(content, list):
                        continue
                    usage = msg.get("usage", {}) or {}
                    cost_obj = usage.get("cost", {}) or {}
                    msg_cost = float(cost_obj.get("total", 0) or 0) if isinstance(cost_obj, dict) else 0.0
                    msg_model = msg.get("model", "")
                    msg_provider = msg.get("provider", "")
                    for blk in content:
                        if not isinstance(blk, dict) or blk.get("type") != "toolCall":
                            continue
                        tcid = blk.get("id", "")
                        if not tcid:
                            continue
                        calls[tcid] = {
                            "tool_call_id": tcid,
                            "tool_name": blk.get("name", ""),
                            "arguments": _truncate(blk.get("arguments"), args_chars),
                            "start_ms": ev_ts_ms,
                            "turn_index": turn_index,
                            "model": msg_model,
                            "provider": msg_provider,
                            "message_cost_usd": msg_cost,
                        }
                elif role == "toolResult":
                    tcid = msg.get("toolCallId", "")
                    if not tcid:
                        continue
                    details = msg.get("details")
                    result_by_id[tcid] = {
                        "end_ms": ev_ts_ms,
                        "is_error": bool(msg.get("isError", False)),
                        "result_size": len(json.dumps(details)) if details is not None else 0,
                        "result_preview": _truncate(details, result_chars),
                    }
    except Exception as e:
        return jsonify({"error": "parse error: " + str(e)}), 500

    tools: list = []
    tool_counts: dict = {}
    for tcid, call in calls.items():
        res = result_by_id.get(tcid)
        if not res and not include_unpaired:
            continue
        rec = dict(call)
        if res:
            rec["end_ms"] = res["end_ms"]
            rec["duration_ms"] = max(0, res["end_ms"] - call["start_ms"]) if res["end_ms"] and call["start_ms"] else 0
            rec["is_error"] = res["is_error"]
            rec["result_size"] = res["result_size"]
            rec["result_preview"] = res["result_preview"]
            rec["paired"] = True
        else:
            rec["end_ms"] = 0
            rec["duration_ms"] = 0
            rec["is_error"] = False
            rec["result_size"] = 0
            rec["result_preview"] = None
            rec["paired"] = False
        tools.append(rec)
        tn = rec["tool_name"] or "unknown"
        agg = tool_counts.setdefault(tn, {"calls": 0, "errors": 0, "total_duration_ms": 0, "total_cost_usd": 0.0})
        agg["calls"] += 1
        if rec["is_error"]:
            agg["errors"] += 1
        agg["total_duration_ms"] += rec["duration_ms"]
        agg["total_cost_usd"] += float(rec.get("message_cost_usd") or 0.0)

    tools.sort(key=lambda r: r.get("start_ms", 0))
    by_tool = [
        {"tool_name": k, **v, "error_rate_pct": round(v["errors"] / v["calls"] * 100, 1) if v["calls"] else 0}
        for k, v in sorted(tool_counts.items(), key=lambda kv: -kv[1]["calls"])
    ]
    first_start = min((r["start_ms"] for r in tools if r.get("start_ms")), default=0)
    last_end = max((r.get("end_ms", 0) for r in tools), default=0)
    return jsonify({
        "session_id": sid,
        "tools": tools,
        "by_tool": by_tool,
        "stats": {
            "total_calls": len(tools),
            "paired_calls": sum(1 for r in tools if r.get("paired")),
            "error_calls": sum(1 for r in tools if r.get("is_error")),
            "distinct_tools": len(tool_counts),
            "first_start_ms": first_start,
            "last_end_ms": last_end,
            "span_ms": max(0, last_end - first_start) if first_start and last_end else 0,
        },
    })


@bp_sessions.route("/api/cost-split")
def api_cost_split():
    """Per-token-type token + cost breakdown per session.

    OpenClaw messages carry granular usage with input/output/cacheRead/
    cacheWrite tokens AND costs. ClawMetry was summing only totalTokens,
    hiding the cache-hit ratio (typically 40-70% of volume at ~10% cost).
    """
    import dashboard as _d
    wanted_sid = (request.args.get("session_id", "") or "").strip()
    try:
        limit = max(1, min(int(request.args.get("limit", "30")), 500))
    except ValueError:
        limit = 30
    sessions_dir = _d.SESSIONS_DIR or os.path.expanduser(
        "~/.openclaw/agents/main/sessions"
    )
    if not os.path.isdir(sessions_dir):
        return jsonify({"sessions": [], "totals": {}, "note": "sessions dir not found"})
    try:
        all_files = [
            f
            for f in os.listdir(sessions_dir)
            if f.endswith(".jsonl") and ".deleted." not in f and ".reset." not in f
        ]
    except OSError:
        all_files = []
    if wanted_sid:
        files = [f for f in all_files if f.startswith(wanted_sid)]
    else:
        files = sorted(
            all_files,
            key=lambda f: os.path.getmtime(os.path.join(sessions_dir, f)),
            reverse=True,
        )[:100]

    def _compute_for_file(fpath):
        sid = os.path.basename(fpath)
        if sid.endswith(".jsonl"):
            sid = sid[: -len(".jsonl")]
        tokens = {"input": 0, "output": 0, "cacheRead": 0, "cacheWrite": 0}
        costs = {"input": 0.0, "output": 0.0, "cacheRead": 0.0, "cacheWrite": 0.0, "total": 0.0}
        model_tokens: dict = {}
        last_seen_model = ""
        try:
            with open(fpath, "r", errors="replace") as fh:
                for raw in fh:
                    raw = raw.strip()
                    if not raw:
                        continue
                    try:
                        ev = json.loads(raw)
                    except Exception:
                        continue
                    t = ev.get("type", "")
                    if t == "model_change":
                        m = ev.get("modelId") or ev.get("model") or ""
                        if m:
                            last_seen_model = m
                        continue
                    if t != "message":
                        continue
                    msg = ev.get("message", {}) or {}
                    if not isinstance(msg, dict):
                        continue
                    usage = msg.get("usage", {}) or {}
                    if not isinstance(usage, dict) or not usage:
                        continue
                    msg_model = msg.get("model") or last_seen_model
                    if msg_model:
                        last_seen_model = msg_model
                    for k in ("input", "output", "cacheRead", "cacheWrite"):
                        tokens[k] += int(usage.get(k, 0) or 0)
                    cost_obj = usage.get("cost", {}) or {}
                    if isinstance(cost_obj, dict):
                        for k in ("input", "output", "cacheRead", "cacheWrite", "total"):
                            costs[k] += float(cost_obj.get(k, 0) or 0)
                    mt = int(usage.get("totalTokens", 0) or 0)
                    if mt and msg_model:
                        model_tokens[msg_model] = model_tokens.get(msg_model, 0) + mt
        except Exception:
            return None
        total_tokens = sum(tokens.values())
        if total_tokens == 0 and costs["total"] == 0:
            return None
        primary_model = (
            max(model_tokens.items(), key=lambda kv: kv[1])[0]
            if model_tokens
            else last_seen_model
        )
        input_plus_cache = tokens["input"] + tokens["cacheRead"]
        cache_hit_ratio_pct = (
            round(tokens["cacheRead"] / input_plus_cache * 100, 1)
            if input_plus_cache
            else 0.0
        )
        est_fresh_input_cost = costs["cacheRead"] * 10.0
        savings = max(0.0, est_fresh_input_cost - costs["cacheRead"])
        est_savings_pct = (
            round(savings / (costs["input"] + est_fresh_input_cost) * 100, 1)
            if (costs["input"] + est_fresh_input_cost)
            else 0.0
        )
        return {
            "session_id": sid,
            "primary_model": primary_model,
            "input_tokens": tokens["input"],
            "output_tokens": tokens["output"],
            "cache_read_tokens": tokens["cacheRead"],
            "cache_write_tokens": tokens["cacheWrite"],
            "total_tokens": total_tokens,
            "input_cost_usd": round(costs["input"], 6),
            "output_cost_usd": round(costs["output"], 6),
            "cache_read_cost_usd": round(costs["cacheRead"], 6),
            "cache_write_cost_usd": round(costs["cacheWrite"], 6),
            "total_cost_usd": round(costs["total"], 6),
            "cache_hit_ratio_pct": cache_hit_ratio_pct,
            "est_cache_savings_pct": est_savings_pct,
        }

    rows = []
    for fname in files:
        r = _compute_for_file(os.path.join(sessions_dir, fname))
        if r:
            rows.append(r)
    rows.sort(key=lambda r: r.get("total_cost_usd", 0), reverse=True)
    if wanted_sid and rows:
        return jsonify({"sessions": rows, "totals": {}})
    top = rows[:limit]
    totals = {
        "input_tokens": sum(r["input_tokens"] for r in rows),
        "output_tokens": sum(r["output_tokens"] for r in rows),
        "cache_read_tokens": sum(r["cache_read_tokens"] for r in rows),
        "cache_write_tokens": sum(r["cache_write_tokens"] for r in rows),
        "total_tokens": sum(r["total_tokens"] for r in rows),
        "input_cost_usd": round(sum(r["input_cost_usd"] for r in rows), 4),
        "output_cost_usd": round(sum(r["output_cost_usd"] for r in rows), 4),
        "cache_read_cost_usd": round(sum(r["cache_read_cost_usd"] for r in rows), 4),
        "cache_write_cost_usd": round(sum(r["cache_write_cost_usd"] for r in rows), 4),
        "total_cost_usd": round(sum(r["total_cost_usd"] for r in rows), 4),
        "session_count": len(rows),
    }
    tot_in_cache = totals["input_tokens"] + totals["cache_read_tokens"]
    totals["cache_hit_ratio_pct"] = (
        round(totals["cache_read_tokens"] / tot_in_cache * 100, 1)
        if tot_in_cache
        else 0.0
    )
    return jsonify({"sessions": top, "totals": totals})


@bp_sessions.route("/api/task-runs")
def api_task_runs():
    """Read ~/.openclaw/tasks/runs.sqlite — the canonical subagent/task registry."""
    import sqlite3
    p = os.path.expanduser("~/.openclaw/tasks/runs.sqlite")
    if not os.path.isfile(p):
        return jsonify({"tasks": [], "counts": {}, "note": "runs.sqlite not found"})
    try:
        limit = max(1, min(int(request.args.get("limit", "500")), 5000))
    except ValueError:
        limit = 500
    status_filter = (request.args.get("status", "") or "").strip()
    parent_filter = (request.args.get("parent_task_id", "") or "").strip()
    where = []
    args = []
    if status_filter:
        where.append("status = ?")
        args.append(status_filter)
    if parent_filter:
        where.append("parent_task_id = ?")
        args.append(parent_filter)
    where_sql = ("WHERE " + " AND ".join(where)) if where else ""
    tasks: list = []
    counts: dict = {}
    try:
        conn = sqlite3.connect(p)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute(
            f"""SELECT task_id, parent_task_id, child_session_key, requester_session_key,
                       agent_id, run_id, label, task, status, delivery_status,
                       task_kind, parent_flow_id,
                       created_at, started_at, ended_at, last_event_at,
                       error, progress_summary, terminal_summary, terminal_outcome
                FROM task_runs {where_sql}
                ORDER BY COALESCE(started_at, created_at, 0) DESC
                LIMIT ?""",
            args + [limit],
        )
        for r in cur.fetchall():
            d = dict(r)
            started = d.get("started_at") or 0
            ended = d.get("ended_at") or 0
            d["duration_ms"] = max(0, ended - started) if started and ended else 0
            tasks.append(d)
            st = d.get("status") or "unknown"
            counts[st] = counts.get(st, 0) + 1
        conn.close()
    except Exception as e:
        return jsonify({"tasks": [], "counts": {}, "error": str(e)}), 500
    total = len(tasks)
    failed = counts.get("failed", 0)
    err_rate = round(failed / total * 100, 1) if total else 0
    return jsonify({
        "tasks": tasks,
        "counts": counts,
        "stats": {
            "total": total,
            "succeeded": counts.get("succeeded", 0),
            "failed": failed,
            "running": counts.get("running", 0),
            "error_rate_pct": err_rate,
        },
    })


def _scan_spawn_events_from_jsonl(sessions_dir):
    """Walk every session JSONL and pair SPAWN toolCall/toolResult rows.

    OpenClaw's subagent lifecycle is:
      1. Parent session's assistant turn emits a `toolCall` with name
         `subagents` (action=spawn) or legacy `sessions_spawn`. The
         `arguments` dict carries `name`/`label`, `task`, `channel`.
      2. OpenClaw fires back a `toolResult` with the SAME `toolCallId`.
         On success: `details = {childSessionKey, runId, mode, note,
         modelApplied, ...}`. On failure: `details = {status:"error",
         error:"..."}`.

    This gives us the FULL subagent history regardless of whether the
    gateway registry still knows about them (registry rolls over at 30
    min; JSONL persists until TTL cleanup). Returns a list of subagent
    dicts ready to merge into /api/subagents response.
    """
    import glob as _glob
    import re as _re
    subs = []
    if not sessions_dir or not os.path.isdir(sessions_dir):
        return subs

    _completion_re = _re.compile(
        r"<<<BEGIN_UNTRUSTED_CHILD_RESULT>>>\s*(.*?)\s*<<<END_UNTRUSTED_CHILD_RESULT>>>",
        _re.DOTALL,
    )
    _stats_re = _re.compile(
        r"Stats:\s*runtime\s+([\w.]+)\s*[•·]?\s*tokens\s+(\d+)\s*\(in\s*(\d+)\s*/\s*out\s*(\d+)\)",
        _re.IGNORECASE,
    )
    _session_key_re = _re.compile(r"session_key:\s*(agent:main:subagent:[\w-]+)")
    _task_name_re = _re.compile(r"^task:\s*(.+)$", _re.MULTILINE)
    _status_re = _re.compile(r"^status:\s*(.+)$", _re.MULTILINE)

    for fpath in _glob.glob(os.path.join(sessions_dir, "*.jsonl")):
        if ".deleted." in fpath:
            continue
        # Skip checkpoints - their content is duplicated into the main file
        # and they'd cause double-counting.
        if ".checkpoint." in fpath:
            continue
        parent_sid = os.path.basename(fpath).replace(".jsonl", "").split(".")[0]
        calls = {}       # toolCallId → {name, args, ts}
        results = {}     # toolCallId → {details, isError, ts, content_text}
        completions = {} # childSessionKey → {task, status, result, stats, ts}
        try:
            with open(fpath, "r", errors="replace") as fh:
                for raw in fh:
                    raw = raw.strip()
                    if not raw:
                        continue
                    try:
                        ev = json.loads(raw)
                    except Exception:
                        continue
                    if ev.get("type") != "message":
                        continue
                    msg = ev.get("message") or {}
                    role = msg.get("role", "")
                    ts = ev.get("timestamp", "")
                    if role == "assistant":
                        for blk in msg.get("content") or []:
                            if not isinstance(blk, dict):
                                continue
                            if blk.get("type") != "toolCall":
                                continue
                            nm = (blk.get("name") or "").lower()
                            if "subagent" not in nm and "spawn" not in nm:
                                continue
                            args = blk.get("arguments") or {}
                            action = (args.get("action") or "spawn").lower()
                            if action not in ("spawn", "create"):
                                continue
                            calls[blk.get("id", "")] = {
                                "name": blk.get("name"),
                                "args": args,
                                "ts": ts,
                            }
                    elif role == "toolResult":
                        nm = (msg.get("toolName") or "").lower()
                        if "subagent" not in nm and "spawn" not in nm:
                            continue
                        tcid = msg.get("toolCallId", "")
                        if not tcid:
                            continue
                        content_text = ""
                        content = msg.get("content")
                        if isinstance(content, list) and content:
                            first = content[0]
                            if isinstance(first, dict):
                                content_text = first.get("text") or ""
                        results[tcid] = {
                            "details": msg.get("details"),
                            "isError": bool(msg.get("isError")),
                            "ts": ts,
                            "content_text": content_text[:2000],
                        }
                    elif role == "user":
                        # OpenClaw injects subagent completion events as
                        # synthetic user messages bracketed by
                        # <<<BEGIN_OPENCLAW_INTERNAL_CONTEXT>>>. Parse them
                        # so we can show the child's output even after its
                        # transcript is GC'd.
                        for blk in msg.get("content") or []:
                            if not isinstance(blk, dict):
                                continue
                            if blk.get("type") != "text":
                                continue
                            txt = blk.get("text") or ""
                            if "Internal task completion event" not in txt:
                                continue
                            if "source: subagent" not in txt:
                                continue
                            sk_m = _session_key_re.search(txt)
                            if not sk_m:
                                continue
                            child_key = sk_m.group(1)
                            res_m = _completion_re.search(txt)
                            stats_m = _stats_re.search(txt)
                            task_m = _task_name_re.search(txt)
                            status_m = _status_re.search(txt)
                            completions[child_key] = {
                                "task_label": task_m.group(1).strip() if task_m else "",
                                "status": status_m.group(1).strip() if status_m else "",
                                "result": (res_m.group(1).strip() if res_m else "")[:8000],
                                "runtime": stats_m.group(1) if stats_m else "",
                                "tokens_total": int(stats_m.group(2)) if stats_m else 0,
                                "tokens_in": int(stats_m.group(3)) if stats_m else 0,
                                "tokens_out": int(stats_m.group(4)) if stats_m else 0,
                                "ts": ts,
                            }
        except Exception:
            continue

        for tcid, call in calls.items():
            res = results.get(tcid, {})
            det = res.get("details") if isinstance(res.get("details"), dict) else {}
            error_msg = None
            child_key = None
            if det:
                if det.get("status") == "error":
                    error_msg = det.get("error")
                child_key = det.get("childSessionKey") or det.get("key")
            # Some OpenClaw error shapes return empty `details` but set
            # `isError=true` with the message in content[0].text. Fall back
            # to that so the dashboard can surface validation errors.
            if res.get("isError") and not error_msg:
                ct = res.get("content_text") or ""
                error_msg = ct.split("\n")[0][:400] if ct else "Unknown OpenClaw error"
            args = call.get("args") or {}
            name = args.get("name") or args.get("label") or "subagent"
            completion = completions.get(child_key, {}) if child_key else {}
            subs.append({
                "parentSessionId": parent_sid,
                "parentKey": f"agent:main:session:{parent_sid}",
                "childKey": child_key,
                "name": name,
                "task": (args.get("task") or "")[:500],
                "callTs": call.get("ts"),
                "resultTs": res.get("ts"),
                "error": error_msg,
                "runId": det.get("runId") if det else None,
                "mode": det.get("mode") if det else None,
                "modelApplied": det.get("modelApplied") if det else None,
                # Spawn acknowledgment text (e.g. "accepted" note) — useful when
                # the spawn succeeded but no completion event is present yet.
                "spawnAck": res.get("content_text") or "",
                # Completion payload — populated if OpenClaw emitted a
                # completion event for this child in the parent transcript.
                "completionStatus": completion.get("status") or "",
                "completionResult": completion.get("result") or "",
                "completionTs": completion.get("ts") or "",
                "runtimeFormatted": completion.get("runtime") or "",
                "tokensIn": completion.get("tokens_in") or 0,
                "tokensOut": completion.get("tokens_out") or 0,
                "tokensTotal": completion.get("tokens_total") or 0,
            })
    return subs


@bp_sessions.route("/api/subagents")
def api_subagents():
    """Return sub-agent list with depth/parent fields for the tree view.

    Data sources merged (in priority order):

    1. OpenClaw's canonical `subagents action=list` registry — live +
       last-30-min recent, with status explicitly.
    2. `sessions_list` gateway RPC filtered by key substring — catches
       subagents still in the session roster but outside the 30-min
       registry window.
    3. JSONL spawn event scan — pairs `toolCall` / `toolResult` for
       subagents-spawn across every session file on disk. Captures both
       succeeded spawns (via `details.childSessionKey`) and attempted
       spawns that errored (visible so the user knows the agent tried).
    """
    import dashboard as _d
    now_ms = time.time() * 1000

    # Source 1: canonical subagent registry
    reg_active = []
    reg_recent = []
    try:
        reg = _d._gw_invoke("subagents", {"action": "list"})
        if reg and isinstance(reg, dict):
            reg_active = reg.get("active", []) or []
            reg_recent = reg.get("recent", []) or []
    except Exception:
        pass

    # Source 2: full session list for the depth/parent filter.
    # IMPORTANT: copy the list before mutating. `_d._get_sessions()` returns a
    # reference to _sessions_cache["data"]; calling `.insert()` on the return
    # value would append registry + spawn entries to the cache itself, so
    # every subsequent /api/subagents call inherits the previous call's
    # appends — subagents get duplicated exponentially (6x, 8x, 10x...).
    gw_data = _d._gw_invoke("sessions_list", {"limit": 100, "messageLimit": 0})
    if gw_data and "sessions" in gw_data:
        all_sessions = list(gw_data["sessions"])
    else:
        all_sessions = list(_d._get_sessions() or [])

    # Prepend registry entries — normalise to the same shape so the filter
    # below treats them uniformly. Registry-provided entries always pass
    # the is_subagent check (they're by definition subagents).
    seen_keys = set()
    for entry in reg_active + reg_recent:
        if not isinstance(entry, dict):
            continue
        k = entry.get("key") or entry.get("sessionKey") or ""
        if not k or k in seen_keys:
            continue
        seen_keys.add(k)
        all_sessions.insert(0, {
            "key": k,
            "sessionId": entry.get("sessionId") or k.split(":")[-1],
            "displayName": entry.get("name") or entry.get("label") or entry.get("displayName") or "",
            "status": entry.get("status") or "active",
            "updatedAt": entry.get("updatedAt") or entry.get("lastActiveMs") or now_ms,
            "startedAt": entry.get("startedAt") or entry.get("createdAt") or now_ms,
            "model": entry.get("model") or "",
            "totalTokens": entry.get("totalTokens") or 0,
            "depth": entry.get("depth") or 1,  # registry entries are subagents
            "spawnedBy": entry.get("parentKey") or entry.get("spawnedBy"),
            "_from_registry": True,
        })

    # Source 3: JSONL spawn event scan — merge into all_sessions where the
    # child isn't already covered by sources 1/2. Errored spawns also get
    # included (with status="failed") so the user sees "agent tried to
    # spawn X but it failed with Y" instead of a silently empty panel.
    sessions_dir = _d.SESSIONS_DIR or os.path.expanduser(
        "~/.openclaw/agents/main/sessions"
    )
    try:
        spawn_events = _scan_spawn_events_from_jsonl(sessions_dir)
    except Exception:
        spawn_events = []
    # Build a lookup by childKey so we can enrich entries from sources 1/2
    # with the spawn metadata + completion logs, even when they were already
    # present in the registry / session roster.
    spawn_by_key = {}
    for sp in spawn_events:
        ck = sp.get("childKey")
        if ck:
            spawn_by_key[ck] = sp
    for sp in spawn_events:
        k = sp.get("childKey") or f"spawn:attempt:{sp.get('parentSessionId')}:{sp.get('callTs')}"
        if k in seen_keys:
            continue
        seen_keys.add(k)
        # Parse timestamp to epoch ms
        try:
            from datetime import datetime as _dt
            ts_ms = int(_dt.fromisoformat(
                (sp.get("resultTs") or sp.get("callTs") or "").replace("Z", "+00:00")
            ).timestamp() * 1000)
        except Exception:
            ts_ms = int(now_ms)
        status = "failed" if sp.get("error") else ""  # let main filter classify active/idle/stale
        all_sessions.insert(0, {
            "key": k,
            "sessionId": (sp.get("childKey") or "").split(":")[-1] or "",
            "displayName": sp.get("name"),
            "task": sp.get("task"),
            "error": sp.get("error"),
            "runId": sp.get("runId"),
            # modelApplied in legacy OpenClaw spawn results is a bool "was a
            # model override applied?", not the model name. Coerce non-string
            # values to "" so the UI doesn't render "True" in a model slot.
            "model": sp.get("modelApplied") if isinstance(sp.get("modelApplied"), str) else "",
            "updatedAt": ts_ms,
            "startedAt": ts_ms,
            "depth": 1,
            "spawnedBy": sp.get("parentKey"),
            "_status_override": status,
            "_from_spawn_scan": True,
            "spawnAck": sp.get("spawnAck") or "",
            "completionResult": sp.get("completionResult") or "",
            "completionStatus": sp.get("completionStatus") or "",
            "completionTs": sp.get("completionTs") or "",
            "runtimeFormatted": sp.get("runtimeFormatted") or "",
            "tokensIn": sp.get("tokensIn") or 0,
            "tokensOut": sp.get("tokensOut") or 0,
        })

    subagents = []
    counts = {"total": 0, "active": 0, "idle": 0, "stale": 0, "failed": 0}
    for s in all_sessions:
        sid = s.get("sessionId") or ""
        key = s.get("key") or ""
        if not sid and not key:
            continue
        age_ms = now_ms - (s.get("updatedAt") or s.get("lastActiveMs", 0) or 0)
        override = s.get("_status_override")
        if override:
            status = override   # "failed" (errored spawn attempt)
        elif age_ms < 120000:
            status = "active"
        elif age_ms < 600000:
            status = "idle"
        else:
            status = "stale"
        depth = int(s.get("depth", 0) or 0)
        parent = s.get("spawnedBy") or s.get("parentKey") or None
        # OpenClaw keys subagents as `agent:main:subagent:<uuid>` — check the
        # KEY (not the sessionId UUID) for the substring. Previously we
        # checked sessionId, which is always a bare UUID → `subagent` match
        # never fired → subagents never appeared in Active Tasks.
        is_subagent = (
            depth > 0
            or "subagent" in key.lower()
            or bool(parent)
        )
        if not is_subagent:
            continue
        tokens = int(s.get("totalTokens") or 0)
        model = s.get("model") or s.get("modelRef") or "unknown"
        display = s.get("displayName") or s.get("label") or sid[:20]
        started = s.get("startedAt") or s.get("updatedAt") or now_ms
        elapsed_ms = max(0, int(now_ms - started))
        elapsed_s = elapsed_ms // 1000
        if elapsed_s < 60:
            runtime = f"{elapsed_s}s"
        elif elapsed_s < 3600:
            runtime = f"{elapsed_s // 60}m"
        else:
            runtime = f"{elapsed_s // 3600}h {(elapsed_s % 3600) // 60}m"
        counts["total"] += 1
        counts[status] += 1
        # Enrich from the spawn scan by childKey — this gives us the task
        # description and completion output even for subagents that only
        # showed up via the gateway registry / session roster.
        sp_match = spawn_by_key.get(key, {}) if key else {}
        task_text = s.get("task") or sp_match.get("task") or ""
        error_text = s.get("error") or sp_match.get("error") or ""
        subagents.append({
            "sessionId": sid,
            "key": key,                 # used by Active Tasks openTaskModal
            "displayName": display,
            "model": model,
            "status": status,
            "depth": depth,
            "parent": parent,
            "totalTokens": tokens,
            "runtime": runtime,         # formatted string (legacy)
            "runtimeMs": elapsed_ms,    # numeric ms — used by Active Tasks card
            "startedAt": started,
            "updatedAt": s.get("updatedAt") or s.get("lastActiveMs", 0),
            "task": task_text,
            "error": error_text,
            # Completion payload reconstructed from parent JSONL. Populated
            # for subagents whose parent emitted an Internal task completion
            # event (OpenClaw's auto-announce). Modal uses these fields to
            # render the child's output when its own transcript is GC'd.
            # Prefer the session-level fields (propagated for spawn-only
            # entries without a childKey) over the childKey-indexed lookup.
            "completionResult": s.get("completionResult") or sp_match.get("completionResult") or "",
            "completionStatus": s.get("completionStatus") or sp_match.get("completionStatus") or "",
            "completionTs":     s.get("completionTs")     or sp_match.get("completionTs") or "",
            "runtimeFormatted": s.get("runtimeFormatted") or sp_match.get("runtimeFormatted") or "",
            "tokensIn":  s.get("tokensIn")  or sp_match.get("tokensIn")  or 0,
            "tokensOut": s.get("tokensOut") or sp_match.get("tokensOut") or 0,
            "spawnAck":  s.get("spawnAck")  or sp_match.get("spawnAck")  or "",
            "runId":     s.get("runId") or sp_match.get("runId") or "",
        })

    _status_rank = {"active": 0, "idle": 1, "stale": 2, "failed": 3}
    subagents.sort(key=lambda x: (_status_rank.get(x["status"], 9), x["depth"]))
    return jsonify({"subagents": subagents, "counts": counts})


@bp_sessions.route("/api/delegation-tree")
def api_delegation_tree():
    """Agent delegation chains -- inspired by AgentWeave provenance tracing.

    Reads sessions.json, groups subagents by their spawnedBy parent key,
    and returns per-chain token totals and estimated cost.
    """
    import dashboard as _d
    sessions_dir = _d._get_sessions_dir()
    index_path = os.path.join(sessions_dir, "sessions.json")
    try:
        with open(index_path) as f:
            all_sessions = json.load(f)
    except Exception:
        return jsonify(
            {"chains": [], "total_subagents": 0, "total_chain_cost_usd": 0.0}
        )

    usd_per_tok = _d._estimate_usd_per_token()
    now_ms = time.time() * 1000

    main_sessions = {}
    subagent_sessions = []
    for key, val in all_sessions.items():
        if not isinstance(val, dict):
            continue
        if ":subagent:" in key:
            subagent_sessions.append((key, val))
        else:
            main_sessions[key] = val

    chains_map = {}
    for key, sa in subagent_sessions:
        parent_key = sa.get("spawnedBy", "unknown")
        if parent_key not in chains_map:
            chains_map[parent_key] = []
        age_ms = now_ms - sa.get("updatedAt", 0)
        status = (
            "active" if age_ms < 120000 else ("idle" if age_ms < 600000 else "stale")
        )
        total_tok = int(sa.get("totalTokens") or 0)
        chains_map[parent_key].append(
            {
                "key": key,
                "label": sa.get("label") or key.split(":")[-1],
                "model": sa.get("model", "unknown"),
                "prov_agent_type": "subagent",
                "prov_session_turn": 2,
                "prov_parent_key": parent_key,
                "prov_total_tokens": total_tok,
                "input_tokens": int(sa.get("inputTokens") or 0),
                "output_tokens": int(sa.get("outputTokens") or 0),
                "total_tokens": total_tok,
                "cost_usd": round(total_tok * usd_per_tok, 6),
                "status": status,
                "updated_at": sa.get("updatedAt", 0),
            }
        )

    chains = []
    total_chain_cost = 0.0
    for parent_key, children in chains_map.items():
        parts = parent_key.split(":")
        channel = parts[2] if len(parts) > 2 else "unknown"
        display = parts[-1] if len(parts) > 0 else parent_key
        chain_tokens = sum(c["total_tokens"] for c in children)
        chain_cost = round(chain_tokens * usd_per_tok, 6)
        total_chain_cost += chain_cost
        parent_meta = main_sessions.get(parent_key, {})
        chains.append(
            {
                "parent_key": parent_key,
                "parent_display": parent_meta.get("displayName")
                or parent_meta.get("subject")
                or display,
                "parent_channel": channel,
                "children": sorted(
                    children, key=lambda x: x["total_tokens"], reverse=True
                ),
                "chain_tokens": chain_tokens,
                "chain_cost_usd": chain_cost,
                "child_count": len(children),
            }
        )

    chains.sort(key=lambda x: x["chain_tokens"], reverse=True)
    return jsonify(
        {
            "chains": chains,
            "total_subagents": len(subagent_sessions),
            "total_chain_cost_usd": round(total_chain_cost, 4),
        }
    )


@bp_sessions.route("/api/export/otlp")
def api_export_otlp():
    """Export recent sessions as OTLP ResourceSpans JSON.

    Compatible with Grafana Tempo, Jaeger, and any OTLP-capable backend.
    """
    import dashboard as _d
    import hashlib

    sessions_dir = _d._get_sessions_dir()
    index_path = os.path.join(sessions_dir, "sessions.json")
    try:
        with open(index_path) as f:
            all_sessions = json.load(f)
    except Exception:
        return jsonify({"resourceSpans": []})

    cutoff_ms = (time.time() - 86400) * 1000
    resource_spans = []
    count = 0

    for key, val in all_sessions.items():
        if not isinstance(val, dict):
            continue
        if val.get("updatedAt", 0) < cutoff_ms:
            continue
        if count >= 100:
            break
        count += 1

        is_subagent = ":subagent:" in key
        agent_type = "subagent" if is_subagent else "main"
        session_id = val.get("sessionId", key.split(":")[-1])
        trace_id = hashlib.md5(session_id.encode()).hexdigest()
        span_id = trace_id[:16]
        total_tokens = int(val.get("totalTokens") or 0)

        attrs = [
            {"key": "service.name", "value": {"stringValue": "clawmetry"}},
            {"key": "prov.agent.id", "value": {"stringValue": key}},
            {"key": "prov.agent.type", "value": {"stringValue": agent_type}},
            {
                "key": "prov.agent.model",
                "value": {"stringValue": val.get("model", "unknown")},
            },
            {"key": "prov.llm.total_tokens", "value": {"intValue": total_tokens}},
            {
                "key": "prov.session.turn",
                "value": {"intValue": 2 if is_subagent else 1},
            },
        ]
        if is_subagent and val.get("spawnedBy"):
            attrs.append(
                {
                    "key": "prov.parent.session.id",
                    "value": {"stringValue": val["spawnedBy"]},
                }
            )
        if val.get("label"):
            attrs.append(
                {"key": "prov.task.label", "value": {"stringValue": val["label"]}}
            )

        updated_ns = int(val.get("updatedAt", 0)) * 1000000

        resource_spans.append(
            {
                "resource": {
                    "attributes": [
                        {"key": "service.name", "value": {"stringValue": "clawmetry"}},
                    ]
                },
                "scopeSpans": [
                    {
                        "scope": {"name": "clawmetry.agent", "version": "1.0"},
                        "spans": [
                            {
                                "traceId": trace_id,
                                "spanId": span_id,
                                "name": "agent.turn",
                                "kind": 3,
                                "startTimeUnixNano": updated_ns - 1000000000,
                                "endTimeUnixNano": updated_ns,
                                "attributes": attrs,
                                "status": {"code": 1},
                            }
                        ],
                    }
                ],
            }
        )

    return jsonify({"resourceSpans": resource_spans})


@bp_sessions.route("/api/sessions/cost-breakdown")
def api_sessions_cost_breakdown():
    """Per-session cost breakdown: top sessions by total cost, sorted descending."""
    import dashboard as _d
    analytics = _d._compute_transcript_analytics()
    sessions = analytics.get("sessions", [])
    usd_per_token = _d._estimate_usd_per_token()
    result = []
    for s in sessions:
        cost = s.get("cost_usd", 0.0) or 0.0
        tokens = s.get("tokens", 0) or 0
        # Estimate cost from tokens if cost is zero
        if cost == 0.0 and tokens > 0:
            cost = tokens * usd_per_token
        result.append(
            {
                "session_id": s.get("session_id", ""),
                "tokens": tokens,
                "cost_usd": round(cost, 6),
                "model": s.get("model", "unknown"),
                "day": s.get("day", ""),
                "start_ts": s.get("start_ts", 0),
            }
        )
    result.sort(key=lambda x: x["cost_usd"], reverse=True)
    top10 = result[:10]
    total_cost = sum(r["cost_usd"] for r in result)
    return jsonify(
        {"sessions": result, "top10": top10, "total_cost_usd": round(total_cost, 4)}
    )


@bp_sessions.route("/api/sessions/<session_id>/stop", methods=["POST"])
def api_session_stop(session_id):
    """Emergency stop for a session: SIGTERM if pid is known and/or .stop signal file."""
    import dashboard as _d
    target = _d._resolve_session_stop_target(session_id)
    sid = target.get("session_id", "")
    if not sid:
        return jsonify({"ok": False, "error": "Invalid session id"}), 400

    did_signal = False
    did_file = False
    errors = []
    pid = target.get("pid")
    if isinstance(pid, int) and pid > 1 and sys.platform != "win32":
        try:
            os.kill(pid, 15)  # SIGTERM
            did_signal = True
        except Exception as e:
            errors.append(f"sigterm_failed:{e}")

    stop_path = target.get("stop_path", "")
    try:
        if stop_path:
            with open(stop_path, "w") as f:
                f.write(
                    json.dumps(
                        {"timestamp": time.time(), "reason": "dashboard_emergency_stop"}
                    )
                )
            did_file = True
    except Exception as e:
        errors.append(f"stop_file_failed:{e}")

    if not did_signal and not did_file:
        return jsonify(
            {"ok": False, "error": "Unable to issue stop signal", "details": errors}
        ), 500
    return jsonify(
        {
            "ok": True,
            "session_id": sid,
            "sigterm_sent": did_signal,
            "stop_file_written": did_file,
            "errors": errors,
        }
    )


@bp_sessions.route('/api/transcripts')
def api_transcripts():
    """List available session transcript .jsonl files."""
    import dashboard as _d
    sessions_dir = _d.SESSIONS_DIR or os.path.expanduser(
        "~/.openclaw/agents/main/sessions"
    )
    transcripts = []
    if os.path.isdir(sessions_dir):
        for fname in sorted(
            os.listdir(sessions_dir),
            key=lambda f: os.path.getmtime(os.path.join(sessions_dir, f)),
            reverse=True,
        ):
            if not fname.endswith(".jsonl") or "deleted" in fname:
                continue
            fpath = os.path.join(sessions_dir, fname)
            try:
                msg_count = 0
                with open(fpath) as f:
                    for _ in f:
                        msg_count += 1
                transcripts.append(
                    {
                        "id": fname.replace(".jsonl", ""),
                        "name": fname.replace(".jsonl", "")[:40],
                        "messages": msg_count,
                        "size": os.path.getsize(fpath),
                        "modified": int(os.path.getmtime(fpath) * 1000),
                    }
                )
            except Exception:
                pass
    return jsonify({"transcripts": transcripts[:50]})


@bp_sessions.route("/api/transcript/<session_id>")
def api_transcript(session_id):
    """Parse and return a session transcript for the chat viewer."""
    import dashboard as _d
    sessions_dir = _d.SESSIONS_DIR or os.path.expanduser(
        "~/.openclaw/agents/main/sessions"
    )
    fpath = os.path.join(sessions_dir, session_id + ".jsonl")
    # Sanitize path
    fpath = os.path.normpath(fpath)
    if not fpath.startswith(os.path.normpath(sessions_dir)):
        return jsonify({"error": "Access denied"}), 403
    if not os.path.exists(fpath):
        return jsonify({"error": "Transcript not found"}), 404

    messages = []
    model = None
    total_tokens = 0
    first_ts = None
    last_ts = None
    try:
        with open(fpath) as f:
            for line in f:
                try:
                    obj = json.loads(line.strip())
                    role = obj.get("role", obj.get("type", "unknown"))
                    content = obj.get("content", "")
                    if isinstance(content, list):
                        parts = []
                        for part in content:
                            if isinstance(part, dict):
                                parts.append(part.get("text", str(part)))
                            else:
                                parts.append(str(part))
                        content = "\n".join(parts)
                    elif not isinstance(content, str):
                        content = str(content) if content else ""
                    # Tool use handling
                    if obj.get("tool_calls") or obj.get("tool_use"):
                        tools = obj.get("tool_calls") or obj.get("tool_use") or []
                        if isinstance(tools, list):
                            for tc in tools:
                                tname = tc.get(
                                    "name", tc.get("function", {}).get("name", "tool")
                                )
                                messages.append(
                                    {
                                        "role": "tool",
                                        "content": f"[Tool Call: {tname}]\n{json.dumps(tc.get('input', tc.get('arguments', {})), indent=2)[:500]}",
                                        "timestamp": obj.get("timestamp")
                                        or obj.get("time"),
                                    }
                                )
                    if role == "tool_result":
                        role = "tool"
                    ts = (
                        obj.get("timestamp") or obj.get("time") or obj.get("created_at")
                    )
                    if ts:
                        if isinstance(ts, (int, float)):
                            ts_ms = int(ts * 1000) if ts < 1e12 else int(ts)
                        else:
                            try:
                                ts_ms = int(
                                    datetime.fromisoformat(
                                        str(ts).replace("Z", "+00:00")
                                    ).timestamp()
                                    * 1000
                                )
                            except Exception:
                                ts_ms = None
                        if ts_ms:
                            if not first_ts or ts_ms < first_ts:
                                first_ts = ts_ms
                            if not last_ts or ts_ms > last_ts:
                                last_ts = ts_ms
                    else:
                        ts_ms = None
                    if not model:
                        model = obj.get("model")
                    usage = obj.get("usage", {})
                    if isinstance(usage, dict):
                        total_tokens += usage.get("total_tokens", 0) or (
                            usage.get("input_tokens", 0) + usage.get("output_tokens", 0)
                        )
                    if content or role in ("user", "assistant", "system"):
                        messages.append(
                            {
                                "role": role,
                                "content": content,
                                "timestamp": ts_ms,
                            }
                        )
                except (json.JSONDecodeError, ValueError):
                    pass
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    duration = None
    if first_ts and last_ts and last_ts > first_ts:
        dur_sec = (last_ts - first_ts) / 1000
        if dur_sec < 60:
            duration = f"{dur_sec:.0f}s"
        elif dur_sec < 3600:
            duration = f"{dur_sec / 60:.0f}m"
        else:
            duration = f"{dur_sec / 3600:.1f}h"

    return jsonify(
        {
            "name": session_id[:40],
            "messageCount": len(messages),
            "model": model,
            "totalTokens": total_tokens,
            "duration": duration,
            "messages": messages[:500],  # Cap at 500 messages
        }
    )


@bp_sessions.route("/api/transcript-events/<session_id>")
def api_transcript_events(session_id):
    """Parse a session transcript JSONL into structured events for the detail modal."""
    import dashboard as _d
    sessions_dir = _d.SESSIONS_DIR or os.path.expanduser(
        "~/.openclaw/agents/main/sessions"
    )
    fpath = os.path.join(sessions_dir, session_id + ".jsonl")
    fpath = os.path.normpath(fpath)
    if not fpath.startswith(os.path.normpath(sessions_dir)):
        return jsonify({"error": "Access denied"}), 403
    if not os.path.exists(fpath):
        return jsonify({"error": "Transcript not found"}), 404

    events = []
    msg_count = 0
    try:
        with open(fpath) as f:
            for line in f:
                try:
                    obj = json.loads(line.strip())
                except (json.JSONDecodeError, ValueError):
                    continue

                ts = obj.get("timestamp") or obj.get("time") or obj.get("created_at")
                ts_val = None
                if ts:
                    if isinstance(ts, (int, float)):
                        ts_val = int(ts * 1000) if ts < 1e12 else int(ts)
                    else:
                        try:
                            ts_val = int(
                                datetime.fromisoformat(
                                    str(ts).replace("Z", "+00:00")
                                ).timestamp()
                                * 1000
                            )
                        except Exception:
                            pass

                obj_type = obj.get("type", "")
                if obj_type == "message":
                    msg = obj.get("message", {})
                    role = msg.get("role", "")
                    content = msg.get("content", "")
                    msg_count += 1

                    if isinstance(content, list):
                        for block in content:
                            if not isinstance(block, dict):
                                continue
                            btype = block.get("type", "")
                            if btype == "thinking":
                                events.append(
                                    {
                                        "type": "thinking",
                                        "text": block.get("thinking", "")[:2000],
                                        "thinking_chars": len(block.get("thinking", "")),
                                        "timestamp": ts_val,
                                    }
                                )
                            elif btype == "text":
                                text = block.get("text", "")
                                if role == "user":
                                    events.append(
                                        {
                                            "type": "user",
                                            "text": text[:3000],
                                            "timestamp": ts_val,
                                        }
                                    )
                                elif role == "assistant":
                                    events.append(
                                        {
                                            "type": "agent",
                                            "text": text[:3000],
                                            "timestamp": ts_val,
                                        }
                                    )
                            elif btype in ("toolCall", "tool_use"):
                                name = block.get("name", "?")
                                args = (
                                    block.get("arguments") or block.get("input") or {}
                                )
                                args_str = (
                                    json.dumps(args, indent=2)[:1000]
                                    if isinstance(args, dict)
                                    else str(args)[:1000]
                                )
                                if name == "exec":
                                    cmd = (
                                        args.get("command", "")
                                        if isinstance(args, dict)
                                        else ""
                                    )
                                    events.append(
                                        {
                                            "type": "exec",
                                            "command": cmd,
                                            "toolName": name,
                                            "args": args_str,
                                            "timestamp": ts_val,
                                        }
                                    )
                                elif name in ("Read", "read"):
                                    fp = (
                                        (
                                            args.get("file_path")
                                            or args.get("path")
                                            or ""
                                        )
                                        if isinstance(args, dict)
                                        else ""
                                    )
                                    events.append(
                                        {
                                            "type": "read",
                                            "file": fp,
                                            "toolName": name,
                                            "args": args_str,
                                            "timestamp": ts_val,
                                        }
                                    )
                                else:
                                    events.append(
                                        {
                                            "type": "tool",
                                            "toolName": name,
                                            "args": args_str,
                                            "timestamp": ts_val,
                                        }
                                    )
                    elif isinstance(content, str) and content:
                        if role == "user":
                            events.append(
                                {
                                    "type": "user",
                                    "text": content[:3000],
                                    "timestamp": ts_val,
                                }
                            )
                        elif role == "assistant":
                            events.append(
                                {
                                    "type": "agent",
                                    "text": content[:3000],
                                    "timestamp": ts_val,
                                }
                            )
                        elif role == "toolResult":
                            events.append(
                                {
                                    "type": "result",
                                    "text": content[:2000],
                                    "timestamp": ts_val,
                                }
                            )

                    if role == "toolResult" and isinstance(content, list):
                        text_parts = []
                        for block in content:
                            if isinstance(block, dict) and block.get("type") == "text":
                                text_parts.append(block.get("text", ""))
                        if text_parts:
                            events.append(
                                {
                                    "type": "result",
                                    "text": "\n".join(text_parts)[:2000],
                                    "timestamp": ts_val,
                                }
                            )

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    return jsonify(
        {"events": events[-500:], "messageCount": msg_count, "totalEvents": len(events)}
    )
