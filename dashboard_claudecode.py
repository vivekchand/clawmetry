"""ClawMetry — Claude Code Observability Dashboard.

A standalone Flask application that provides observability into Claude Code
sessions stored in ``~/.claude/projects/``.  Designed to be deployed alongside
the main ClawMetry dashboard (e.g. at ``clawmetry.com/claudecode``).

This module follows the same single-file architecture as ``dashboard.py`` and
can be run independently or mounted as a Blueprint inside the main app.

Usage::

    # Standalone
    python dashboard_claudecode.py --port 8901

    # Or import the blueprint
    from dashboard_claudecode import bp_claudecode
    app.register_blueprint(bp_claudecode, url_prefix='/claudecode')

Environment variables::

    CLAWMETRY_CLAUDE_HOME   Override Claude Code home directory (default: ~/.claude)
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import time
from collections import defaultdict
from datetime import datetime
from typing import Any, Dict, List, Optional

from flask import (
    Blueprint,
    Flask,
    Response,
    jsonify,
    render_template_string,
    request,
)

__version__ = "0.1.0"

logger = logging.getLogger("clawmetry.claudecode")

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

CLAUDE_CODE_DIR: Optional[str] = None  # Resolved at startup


def _get_claude_home() -> str:
    """Return the Claude Code home directory."""
    return os.environ.get(
        "CLAWMETRY_CLAUDE_HOME", os.path.expanduser("~/.claude")
    )


def _get_claude_projects_dir() -> Optional[str]:
    """Return the Claude Code projects directory, or ``None``."""
    global CLAUDE_CODE_DIR
    if CLAUDE_CODE_DIR and os.path.isdir(CLAUDE_CODE_DIR):
        return CLAUDE_CODE_DIR
    projects = os.path.join(_get_claude_home(), "projects")
    if os.path.isdir(projects):
        CLAUDE_CODE_DIR = projects
        return projects
    return None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _project_display_name(slug: str) -> str:
    """Convert a Claude Code project directory slug to a human-readable name.

    Example::

        >>> _project_display_name("-Users-tushargupta-Developer-clawmetry")
        'clawmetry'
    """
    if not slug:
        return "unknown"
    parts = slug.replace("-", "/").strip("/").split("/")
    return parts[-1] if parts else slug


def _project_full_path(slug: str) -> str:
    """Reconstruct the original filesystem path from a project slug.

    Example::

        >>> _project_full_path("-Users-tushargupta-Developer-clawmetry")
        '/Users/tushargupta/Developer/clawmetry'
    """
    if not slug:
        return ""
    return "/" + slug.lstrip("-").replace("-", "/")


def _parse_timestamp(
    ts_val: Any, fallback: Optional[datetime] = None
) -> Optional[datetime]:
    """Best-effort timestamp parsing for Claude Code JSONL events."""
    if ts_val is None:
        return fallback
    try:
        if isinstance(ts_val, (int, float)):
            return datetime.fromtimestamp(
                ts_val / 1000 if ts_val > 1e12 else ts_val
            )
        if isinstance(ts_val, str):
            return datetime.fromisoformat(ts_val.replace("Z", "+00:00"))
    except Exception:
        pass
    return fallback


# ---------------------------------------------------------------------------
# Pricing — Claude models only (from docs.anthropic.com/en/docs/pricing)
# USD per 1 M tokens — last updated 2025-03
# ---------------------------------------------------------------------------

_MODEL_PRICING: Dict[str, Dict[str, float]] = {
    # Opus 4.x
    "claude-opus-4-6": {"input": 5.00, "output": 25.00},
    "claude-opus-4-5": {"input": 5.00, "output": 25.00},
    "claude-opus-4-20250514": {"input": 5.00, "output": 25.00},
    # Opus 3
    "claude-3-opus-20240229": {"input": 15.00, "output": 75.00},
    # Sonnet 4.x
    "claude-sonnet-4-6": {"input": 3.00, "output": 15.00},
    "claude-sonnet-4-5": {"input": 3.00, "output": 15.00},
    "claude-sonnet-4-20250514": {"input": 3.00, "output": 15.00},
    # Sonnet 3.x
    "claude-3-7-sonnet-20250219": {"input": 3.00, "output": 15.00},
    "claude-3-5-sonnet-20241022": {"input": 3.00, "output": 15.00},
    "claude-3-5-sonnet-20240620": {"input": 3.00, "output": 15.00},
    "claude-3-sonnet-20240229": {"input": 3.00, "output": 15.00},
    # Haiku 4.x
    "claude-haiku-4-5": {"input": 1.00, "output": 5.00},
    "claude-haiku-4-5-20251001": {"input": 1.00, "output": 5.00},
    # Haiku 3.x
    "claude-3-5-haiku-20241022": {"input": 0.80, "output": 4.00},
    "claude-3-haiku-20240307": {"input": 0.25, "output": 1.25},
}


def _estimate_cost(
    model: str,
    input_tokens: int,
    output_tokens: int,
    cache_creation: int = 0,
    cache_read: int = 0,
) -> float:
    """Estimate USD cost for a Claude API call.

    Cache write tokens are billed at 1.25x input price; cache read tokens at
    0.1x input price (per Anthropic prompt caching pricing).
    """
    pricing = _MODEL_PRICING.get(model or "")
    if not pricing:
        for key, val in _MODEL_PRICING.items():
            if model and model.startswith(key.rsplit("-", 1)[0]):
                pricing = val
                break
    if not pricing:
        pricing = {"input": 3.00, "output": 15.00}

    cost = (
        (input_tokens * pricing["input"] / 1_000_000)
        + (output_tokens * pricing["output"] / 1_000_000)
        + (cache_creation * pricing["input"] * 1.25 / 1_000_000)
        + (cache_read * pricing["input"] * 0.10 / 1_000_000)
    )
    return round(cost, 6)


# ---------------------------------------------------------------------------
# Session parsing
# ---------------------------------------------------------------------------


def _parse_session(fpath: str) -> Optional[Dict[str, Any]]:
    """Parse a single Claude Code JSONL file into a normalised session dict."""
    try:
        session_id = os.path.splitext(os.path.basename(fpath))[0]
        project_slug = os.path.basename(os.path.dirname(fpath))
        project_name = _project_display_name(project_slug)

        total_input = 0
        total_output = 0
        total_cache_create = 0
        total_cache_read = 0
        model = "unknown"
        start_ts: Optional[datetime] = None
        end_ts: Optional[datetime] = None
        msg_count = 0
        tool_calls: List[str] = []
        first_user_text = ""
        cwd = ""
        git_branch = ""
        version = ""
        entrypoint = ""

        with open(fpath, "r", encoding="utf-8", errors="replace") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except (json.JSONDecodeError, ValueError):
                    continue

                msg_count += 1
                evt_type = obj.get("type", "")

                ts = _parse_timestamp(obj.get("timestamp"))
                if ts:
                    if start_ts is None or ts < start_ts:
                        start_ts = ts
                    if end_ts is None or ts > end_ts:
                        end_ts = ts

                if evt_type == "user":
                    if not cwd:
                        cwd = obj.get("cwd", "")
                    if not git_branch:
                        git_branch = obj.get("gitBranch", "")
                    if not version:
                        version = obj.get("version", "")
                    if not entrypoint:
                        entrypoint = obj.get("entrypoint", "")
                    if not first_user_text and not obj.get("isMeta"):
                        msg_obj = obj.get("message") or {}
                        content = msg_obj.get("content", "")
                        if isinstance(content, str) and content:
                            first_user_text = content[:200]
                        elif isinstance(content, list):
                            for block in content:
                                if (
                                    isinstance(block, dict)
                                    and block.get("type") != "tool_result"
                                ):
                                    text = block.get("text", "")
                                    if text:
                                        first_user_text = text[:200]
                                        break

                if evt_type == "assistant":
                    message = obj.get("message") or {}
                    m = message.get("model")
                    if m:
                        model = m
                    usage = message.get("usage") or {}
                    total_input += int(usage.get("input_tokens", 0) or 0)
                    total_output += int(usage.get("output_tokens", 0) or 0)
                    total_cache_create += int(
                        usage.get("cache_creation_input_tokens", 0) or 0
                    )
                    total_cache_read += int(
                        usage.get("cache_read_input_tokens", 0) or 0
                    )
                    for block in message.get("content") or []:
                        if (
                            isinstance(block, dict)
                            and block.get("type") == "tool_use"
                        ):
                            tool_calls.append(block.get("name", "unknown"))

        if msg_count == 0:
            return None

        fallback_dt = datetime.fromtimestamp(os.path.getmtime(fpath))
        if start_ts is None:
            start_ts = fallback_dt
        if end_ts is None:
            end_ts = fallback_dt

        total_tokens = (
            total_input + total_output + total_cache_create + total_cache_read
        )
        cost_usd = _estimate_cost(
            model, total_input, total_output,
            total_cache_create, total_cache_read,
        )

        return {
            "session_id": session_id,
            "source": "claude_code",
            "project": project_name,
            "project_slug": project_slug,
            "project_path": _project_full_path(project_slug),
            "tokens": total_tokens,
            "input_tokens": total_input,
            "output_tokens": total_output,
            "cache_creation_tokens": total_cache_create,
            "cache_read_tokens": total_cache_read,
            "cost_usd": cost_usd,
            "model": model,
            "start_ts": start_ts.timestamp() if start_ts else 0,
            "end_ts": end_ts.timestamp() if end_ts else 0,
            "day": start_ts.strftime("%Y-%m-%d") if start_ts else "",
            "messages": msg_count,
            "tool_calls": tool_calls,
            "tool_call_count": len(tool_calls),
            "first_user_text": first_user_text,
            "cwd": cwd,
            "git_branch": git_branch,
            "version": version,
            "entrypoint": entrypoint,
            "size": os.path.getsize(fpath),
        }
    except Exception:
        logger.debug("Failed to parse session: %s", fpath, exc_info=True)
        return None


def _list_sessions() -> List[Dict[str, Any]]:
    """Scan all Claude Code project directories and return parsed sessions."""
    projects_dir = _get_claude_projects_dir()
    if not projects_dir:
        return []

    sessions: List[Dict[str, Any]] = []
    try:
        for project_slug in os.listdir(projects_dir):
            project_path = os.path.join(projects_dir, project_slug)
            if not os.path.isdir(project_path):
                continue
            for fname in os.listdir(project_path):
                if not fname.endswith(".jsonl"):
                    continue
                fpath = os.path.join(project_path, fname)
                parsed = _parse_session(fpath)
                if parsed:
                    sessions.append(parsed)
    except OSError:
        logger.debug("Error scanning Claude Code projects", exc_info=True)

    sessions.sort(key=lambda s: s.get("start_ts", 0), reverse=True)
    return sessions


_sessions_cache: Dict[str, Any] = {"data": None, "ts": 0}
_SESSIONS_CACHE_TTL = 15  # seconds


def _get_sessions_cached() -> List[Dict[str, Any]]:
    """Return cached session list, refreshing if stale."""
    now = time.time()
    if (
        _sessions_cache["data"] is not None
        and (now - _sessions_cache["ts"]) < _SESSIONS_CACHE_TTL
    ):
        return _sessions_cache["data"]
    data = _list_sessions()
    _sessions_cache["data"] = data
    _sessions_cache["ts"] = now
    return data


def _resolve_session_path(session_id: str) -> Optional[str]:
    """Find the JSONL file path for a Claude Code session ID."""
    projects_dir = _get_claude_projects_dir()
    if not projects_dir:
        return None
    target = session_id + ".jsonl"
    try:
        for project_slug in os.listdir(projects_dir):
            candidate = os.path.join(projects_dir, project_slug, target)
            if os.path.isfile(candidate):
                return candidate
    except OSError:
        pass
    return None


# ---------------------------------------------------------------------------
# Transcript parsing — correctly maps Claude Code JSONL event types
#
# Claude Code JSONL structure:
#   type=user       → message.content is string (human text) OR list containing
#                     {type:"tool_result", tool_use_id, content, is_error} blocks
#   type=assistant  → message.content is list of:
#                     {type:"text"}, {type:"thinking"}, {type:"tool_use"}
#   type=progress   → hook/progress events (ignored in chat view)
#   type=file-history-snapshot → file tracking (ignored)
#   type=last-prompt → session metadata (ignored)
# ---------------------------------------------------------------------------


def _parse_transcript_messages(fpath: str) -> Dict[str, Any]:
    """Parse a Claude Code JSONL into structured messages for the chat viewer."""
    messages: List[Dict[str, Any]] = []
    model = None
    total_input = 0
    total_output = 0
    first_ts: Optional[int] = None
    last_ts: Optional[int] = None
    project_slug = os.path.basename(os.path.dirname(fpath))

    with open(fpath, "r", encoding="utf-8", errors="replace") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except (json.JSONDecodeError, ValueError):
                continue

            evt_type = obj.get("type", "")
            ts_raw = obj.get("timestamp")
            ts_ms: Optional[int] = None
            if ts_raw:
                parsed_ts = _parse_timestamp(ts_raw)
                if parsed_ts:
                    ts_ms = int(parsed_ts.timestamp() * 1000)
                    if first_ts is None or ts_ms < first_ts:
                        first_ts = ts_ms
                    if last_ts is None or ts_ms > last_ts:
                        last_ts = ts_ms

            message_obj = obj.get("message") or {}

            # ── User events ──────────────────────────────────────────
            if evt_type == "user":
                if obj.get("isMeta"):
                    continue
                content = message_obj.get("content", "")

                # String content = direct human message
                if isinstance(content, str) and content:
                    # Skip system/command XML tags
                    if content.startswith("<") and "command" in content[:50]:
                        continue
                    messages.append({
                        "role": "human",
                        "content": content,
                        "timestamp": ts_ms,
                    })

                # List content = may contain tool_result blocks
                elif isinstance(content, list):
                    for block in content:
                        if not isinstance(block, dict):
                            continue
                        btype = block.get("type", "")
                        if btype == "tool_result":
                            rc = block.get("content", "")
                            if isinstance(rc, list):
                                parts = []
                                for p in rc:
                                    if isinstance(p, dict):
                                        parts.append(p.get("text", str(p)))
                                    else:
                                        parts.append(str(p))
                                rc = "\n".join(parts)
                            is_err = block.get("is_error", False)
                            messages.append({
                                "role": "tool_result",
                                "content": str(rc)[:3000],
                                "is_error": is_err,
                                "timestamp": ts_ms,
                            })
                        elif btype == "text":
                            txt = block.get("text", "")
                            if txt and not (
                                txt.startswith("<") and "command" in txt[:50]
                            ):
                                messages.append({
                                    "role": "human",
                                    "content": txt,
                                    "timestamp": ts_ms,
                                })

            # ── Assistant events ──────────────────────────────────────
            elif evt_type == "assistant":
                m = message_obj.get("model")
                if m:
                    model = m
                usage = message_obj.get("usage") or {}
                total_input += int(usage.get("input_tokens", 0) or 0)
                total_output += int(usage.get("output_tokens", 0) or 0)

                for block in message_obj.get("content") or []:
                    if not isinstance(block, dict):
                        continue
                    btype = block.get("type", "")

                    if btype == "text":
                        text = block.get("text", "")
                        if text:
                            messages.append({
                                "role": "assistant",
                                "content": text,
                                "timestamp": ts_ms,
                            })
                    elif btype == "thinking":
                        thinking = block.get("thinking", "")
                        if thinking:
                            messages.append({
                                "role": "thinking",
                                "content": thinking,
                                "timestamp": ts_ms,
                            })
                    elif btype == "tool_use":
                        tool_name = block.get("name", "tool")
                        tool_input = block.get("input", {})
                        # Format tool input nicely
                        if isinstance(tool_input, dict):
                            formatted = json.dumps(
                                tool_input, indent=2, ensure_ascii=False
                            )[:1000]
                        else:
                            formatted = str(tool_input)[:1000]
                        messages.append({
                            "role": "tool_use",
                            "tool_name": tool_name,
                            "content": formatted,
                            "timestamp": ts_ms,
                        })

    duration = None
    if first_ts and last_ts and last_ts > first_ts:
        dur_sec = (last_ts - first_ts) / 1000
        if dur_sec < 60:
            duration = f"{dur_sec:.0f}s"
        elif dur_sec < 3600:
            duration = f"{dur_sec / 60:.0f}m"
        else:
            duration = f"{dur_sec / 3600:.1f}h"

    session_id = os.path.splitext(os.path.basename(fpath))[0]
    return {
        "name": f"[{_project_display_name(project_slug)}] {session_id[:20]}",
        "session_id": session_id,
        "project": _project_display_name(project_slug),
        "messageCount": len(messages),
        "model": model,
        "totalTokens": total_input + total_output,
        "inputTokens": total_input,
        "outputTokens": total_output,
        "duration": duration,
        "messages": messages[:500],
    }


# ---------------------------------------------------------------------------
# Analytics aggregation
# ---------------------------------------------------------------------------


def _compute_analytics() -> Dict[str, Any]:
    """Aggregate analytics across all Claude Code sessions."""
    sessions = _get_sessions_cached()

    daily_tokens: Dict[str, int] = defaultdict(int)
    daily_cost: Dict[str, float] = defaultdict(float)
    model_usage: Dict[str, int] = defaultdict(int)
    project_usage: Dict[str, Dict[str, Any]] = defaultdict(
        lambda: {"tokens": 0, "cost": 0.0, "sessions": 0}
    )
    tool_stats: Dict[str, int] = defaultdict(int)
    total_tokens = 0
    total_cost = 0.0

    for sess in sessions:
        day = sess.get("day", "")
        if day:
            daily_tokens[day] += sess.get("tokens", 0)
            daily_cost[day] += sess.get("cost_usd", 0.0)
        model_usage[sess.get("model", "unknown")] += sess.get("tokens", 0)
        proj = sess.get("project", "unknown")
        project_usage[proj]["tokens"] += sess.get("tokens", 0)
        project_usage[proj]["cost"] += sess.get("cost_usd", 0.0)
        project_usage[proj]["sessions"] += 1
        for tool in sess.get("tool_calls", []):
            tool_stats[tool] += 1
        total_tokens += sess.get("tokens", 0)
        total_cost += sess.get("cost_usd", 0.0)

    return {
        "total_sessions": len(sessions),
        "total_tokens": total_tokens,
        "total_cost_usd": round(total_cost, 4),
        "daily_tokens": dict(daily_tokens),
        "daily_cost": {k: round(v, 4) for k, v in daily_cost.items()},
        "model_usage": dict(model_usage),
        "project_usage": dict(project_usage),
        "tool_stats": dict(
            sorted(tool_stats.items(), key=lambda x: x[1], reverse=True)[:30]
        ),
    }


# ---------------------------------------------------------------------------
# Flask Blueprint
# ---------------------------------------------------------------------------

bp_claudecode = Blueprint("claudecode", __name__)


@bp_claudecode.route("/")
def index():
    """Claude Code observability dashboard."""
    return render_template_string(_INDEX_HTML, version=__version__)


@bp_claudecode.route("/api/sessions")
def api_sessions():
    """List all Claude Code sessions with metadata."""
    sessions = _get_sessions_cached()
    project_filter = request.args.get("project", "")
    model_filter = request.args.get("model", "")
    limit = min(int(request.args.get("limit", 200)), 1000)

    if project_filter:
        sessions = [
            s for s in sessions if s.get("project") == project_filter
        ]
    if model_filter:
        sessions = [s for s in sessions if s.get("model") == model_filter]

    return jsonify({"sessions": sessions[:limit], "total": len(sessions)})


@bp_claudecode.route("/api/session/<session_id>")
def api_session_detail(session_id: str):
    """Return detailed parsed transcript for a session."""
    fpath = _resolve_session_path(session_id)
    if not fpath:
        return jsonify({"error": "Session not found"}), 404
    try:
        return jsonify(_parse_transcript_messages(fpath))
    except Exception as exc:
        logger.error("Error parsing session %s: %s", session_id, exc)
        return jsonify({"error": str(exc)}), 500


@bp_claudecode.route("/api/analytics")
def api_analytics():
    """Aggregated analytics across all Claude Code sessions."""
    return jsonify(_compute_analytics())


@bp_claudecode.route("/api/projects")
def api_projects():
    """List all detected Claude Code projects."""
    projects_dir = _get_claude_projects_dir()
    if not projects_dir:
        return jsonify({"projects": []})

    projects = []
    try:
        for slug in sorted(os.listdir(projects_dir)):
            ppath = os.path.join(projects_dir, slug)
            if not os.path.isdir(ppath):
                continue
            jsonl_count = sum(
                1 for f in os.listdir(ppath) if f.endswith(".jsonl")
            )
            memory_path = os.path.join(ppath, "memory", "MEMORY.md")
            has_memory = os.path.isfile(memory_path)
            memory_preview = ""
            if has_memory:
                try:
                    with open(memory_path, "r", encoding="utf-8") as mf:
                        memory_preview = mf.read(2000)
                except OSError:
                    pass
            projects.append({
                "slug": slug,
                "name": _project_display_name(slug),
                "path": _project_full_path(slug),
                "sessions": jsonl_count,
                "has_memory": has_memory,
                "memory_preview": memory_preview,
            })
    except OSError:
        pass

    return jsonify({"projects": projects})


@bp_claudecode.route("/api/health")
def api_health():
    """Health check endpoint."""
    projects_dir = _get_claude_projects_dir()
    return jsonify({
        "status": "ok",
        "version": __version__,
        "claude_home": _get_claude_home(),
        "projects_dir": projects_dir,
        "projects_found": bool(projects_dir),
    })


@bp_claudecode.route("/favicon.ico")
def favicon():
    """Serve ClawMetry favicon with Anthropic orange tint."""
    # Minimal 16x16 ICO with Anthropic brand color
    svg = (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32">'
        '<circle cx="16" cy="16" r="14" fill="#c96442"/>'
        '<text x="16" y="22" text-anchor="middle" font-size="18" '
        'font-family="serif" fill="#fff">C</text></svg>'
    )
    return Response(svg, mimetype="image/svg+xml")


# ---------------------------------------------------------------------------
# HTML Template — Anthropic dark mode design
# ---------------------------------------------------------------------------

_INDEX_HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>ClawMetry · Claude Code</title>
<link rel="icon" href="/favicon.ico" type="image/svg+xml">
<style>
:root {
  --bg: #191919;
  --surface: #232323;
  --surface-raised: #2a2a2a;
  --surface-hover: #303030;
  --border: #333;
  --border-light: #3a3a3a;
  --text: #ececec;
  --text-secondary: #a0a0a0;
  --text-tertiary: #6e6e6e;
  --accent: #d4764e;
  --accent-dim: rgba(212,118,78,0.15);
  --accent-bright: #e8946a;
  --green: #4caf50;
  --green-dim: rgba(76,175,80,0.12);
  --blue: #64b5f6;
  --blue-dim: rgba(100,181,246,0.12);
  --purple: #b39ddb;
  --purple-dim: rgba(179,157,219,0.12);
  --yellow: #ffd54f;
  --yellow-dim: rgba(255,213,79,0.12);
  --red: #ef5350;
  --red-dim: rgba(239,83,80,0.12);
  --mono: 'SF Mono','Fira Code','Consolas',monospace;
  --sans: -apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif;
  --radius: 8px;
  --shadow: 0 2px 8px rgba(0,0,0,0.3);
}
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:var(--sans);background:var(--bg);color:var(--text);
  line-height:1.55;-webkit-font-smoothing:antialiased}
.container{max-width:1320px;margin:0 auto;padding:0 20px}

/* Header */
header{background:var(--surface);border-bottom:1px solid var(--border);
  padding:14px 0;position:sticky;top:0;z-index:50}
header .inner{display:flex;align-items:center;gap:12px;max-width:1320px;
  margin:0 auto;padding:0 20px}
header h1{font-size:1.05rem;font-weight:600;letter-spacing:-0.01em}
header h1 .hl{color:var(--accent)}
.vbadge{background:var(--accent-dim);color:var(--accent);padding:2px 8px;
  border-radius:10px;font-size:0.65rem;font-weight:700}
.live-dot{width:7px;height:7px;border-radius:50%;background:var(--green);
  display:inline-block;margin-left:8px;animation:pulse 2s infinite}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:0.4}}

/* Stats */
.stats{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin:20px 0}
.stat{background:var(--surface);border:1px solid var(--border);border-radius:var(--radius);
  padding:16px 20px;transition:border-color 0.15s}
.stat:hover{border-color:var(--border-light)}
.stat .lbl{font-size:0.68rem;font-weight:600;color:var(--text-tertiary);
  text-transform:uppercase;letter-spacing:0.08em;margin-bottom:4px}
.stat .val{font-size:1.7rem;font-weight:700;letter-spacing:-0.02em;line-height:1.1}
.stat .sub{font-size:0.75rem;color:var(--text-secondary);margin-top:3px}
.stat.c-accent .val{color:var(--accent)}
.stat.c-green .val{color:var(--green)}

/* Tabs */
.tabs{display:flex;gap:0;border-bottom:1px solid var(--border);margin-bottom:20px}
.tab{padding:10px 18px;cursor:pointer;border:none;background:none;
  color:var(--text-tertiary);font-size:0.84rem;font-weight:500;
  border-bottom:2px solid transparent;transition:all 0.15s;font-family:inherit}
.tab:hover{color:var(--text-secondary)}
.tab.active{color:var(--accent);border-bottom-color:var(--accent)}
.panel{display:none}.panel.active{display:block}

/* Tables */
.tw{background:var(--surface);border:1px solid var(--border);
  border-radius:var(--radius);overflow:hidden}
table{width:100%;border-collapse:collapse;font-size:0.83rem}
th{text-align:left;padding:10px 14px;color:var(--text-tertiary);font-weight:600;
  font-size:0.7rem;text-transform:uppercase;letter-spacing:0.06em;
  background:var(--surface-raised);border-bottom:1px solid var(--border)}
td{padding:10px 14px;border-bottom:1px solid var(--border);vertical-align:middle}
tr:last-child td{border-bottom:none}
tbody tr{cursor:pointer;transition:background 0.1s}
tbody tr:hover td{background:var(--surface-hover)}

/* Badges */
.b{display:inline-block;padding:2px 8px;border-radius:4px;font-size:0.72rem;font-weight:600}
.b-proj{background:var(--accent-dim);color:var(--accent-bright)}
.b-model{background:var(--purple-dim);color:var(--purple);font-family:var(--mono);font-size:0.68rem}
.b-tool{background:var(--green-dim);color:var(--green);font-family:var(--mono);font-size:0.68rem}

.cost{color:var(--green);font-weight:600;font-family:var(--mono)}
.tok{font-family:var(--mono);font-weight:500}
.dim{color:var(--text-secondary)}
.sm{font-size:0.78rem}
.trunc{max-width:260px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}

/* Filters */
.filters{display:flex;gap:8px;margin-bottom:16px;flex-wrap:wrap}
.filters select,.filters input{background:var(--surface);border:1px solid var(--border);
  color:var(--text);padding:7px 12px;border-radius:6px;font-size:0.83rem;font-family:inherit}
.filters select:focus,.filters input:focus{outline:none;border-color:var(--accent);
  box-shadow:0 0 0 2px var(--accent-dim)}
.filters input{min-width:200px}

/* Charts */
.chart-card{background:var(--surface);border:1px solid var(--border);
  border-radius:var(--radius);padding:20px;margin-bottom:16px}
.chart-title{font-size:0.78rem;font-weight:600;color:var(--text-tertiary);
  margin-bottom:14px;text-transform:uppercase;letter-spacing:0.04em}
.bar-chart{display:flex;align-items:flex-end;gap:2px;height:120px}
.bar{background:var(--accent);border-radius:2px 2px 0 0;min-width:5px;
  transition:opacity 0.15s;position:relative;cursor:pointer;opacity:0.8}
.bar:hover{opacity:1}
.bar .tip{display:none;position:absolute;bottom:calc(100% + 6px);left:50%;
  transform:translateX(-50%);background:var(--surface-raised);border:1px solid var(--border);
  padding:4px 8px;border-radius:4px;font-size:0.68rem;white-space:nowrap;z-index:10;
  box-shadow:var(--shadow);color:var(--text)}
.bar:hover .tip{display:block}
.g2{display:grid;grid-template-columns:1fr 1fr;gap:16px}

/* Memory preview */
.mem-card{background:var(--surface-raised);border:1px solid var(--border);
  border-radius:var(--radius);padding:16px;margin-top:12px;
  font-family:var(--mono);font-size:0.78rem;line-height:1.6;
  color:var(--text-secondary);max-height:300px;overflow-y:auto;
  white-space:pre-wrap;word-break:break-word}
.mem-card h1,.mem-card h2,.mem-card h3{color:var(--text);font-family:var(--sans);
  margin:12px 0 6px;font-size:0.9rem}
.mem-card h1{font-size:1rem}

/* Modal */
.overlay{display:none;position:fixed;inset:0;background:rgba(0,0,0,0.6);
  backdrop-filter:blur(3px);z-index:100;justify-content:center;
  align-items:flex-start;padding-top:4vh;overflow-y:auto}
.overlay.on{display:flex}
.modal{background:var(--surface);border:1px solid var(--border);
  border-radius:12px;width:92%;max-width:880px;max-height:88vh;
  overflow-y:auto;padding:28px;box-shadow:var(--shadow);margin-bottom:4vh}
.modal-hdr{display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:16px}
.modal-hdr h3{font-size:1.05rem;font-weight:600}
.modal-x{background:var(--surface-raised);border:1px solid var(--border);
  color:var(--text-tertiary);width:30px;height:30px;border-radius:50%;
  display:flex;align-items:center;justify-content:center;cursor:pointer;
  font-size:1rem;flex-shrink:0}
.modal-x:hover{background:var(--border);color:var(--text)}
.modal-meta{display:flex;gap:16px;flex-wrap:wrap;padding:10px 14px;
  background:var(--surface-raised);border-radius:6px;margin-bottom:16px;
  font-size:0.8rem;color:var(--text-secondary)}
.modal-meta strong{color:var(--text);font-weight:600}

/* Chat messages */
.msg{margin-bottom:8px;padding:12px 16px;border-radius:var(--radius);
  border-left:3px solid transparent;font-size:0.85rem;line-height:1.55}
.msg.human{background:var(--blue-dim);border-left-color:var(--blue)}
.msg.assistant{background:var(--surface-raised);border-left-color:var(--accent)}
.msg.tool_use{background:var(--green-dim);border-left-color:var(--green);
  font-family:var(--mono);font-size:0.76rem}
.msg.tool_result{background:var(--yellow-dim);border-left-color:var(--yellow);
  font-family:var(--mono);font-size:0.76rem}
.msg.tool_result.err{background:var(--red-dim);border-left-color:var(--red)}
.msg.thinking{background:var(--purple-dim);border-left-color:var(--purple);
  font-style:italic;opacity:0.85}
.msg .rl{font-size:0.65rem;font-weight:700;text-transform:uppercase;
  letter-spacing:0.06em;color:var(--text-tertiary);margin-bottom:5px;
  display:flex;align-items:center;gap:6px}
.msg .rl .tool-icon{font-style:normal}
.msg pre{white-space:pre-wrap;word-break:break-word;font-family:inherit;margin:0}
.msg .md-content h1,.msg .md-content h2,.msg .md-content h3{margin:10px 0 4px;
  font-size:0.92rem;font-weight:700;color:var(--text)}
.msg .md-content code{background:var(--surface-hover);padding:1px 5px;
  border-radius:3px;font-family:var(--mono);font-size:0.82em}
.msg .md-content pre code{display:block;padding:10px;border-radius:6px;
  overflow-x:auto;background:var(--bg);border:1px solid var(--border)}
.msg .md-content ul,.msg .md-content ol{margin:4px 0 4px 20px}
.msg .md-content p{margin:4px 0}
.msg .md-content strong{color:var(--text);font-weight:700}
.msg .md-content blockquote{border-left:3px solid var(--border);
  padding-left:12px;color:var(--text-secondary);margin:6px 0}

@media(max-width:768px){
  .stats{grid-template-columns:repeat(2,1fr)}
  .stat .val{font-size:1.3rem}
  .g2{grid-template-columns:1fr}
  .modal{padding:18px;width:96%}
}
@media(max-width:480px){.stats{grid-template-columns:1fr}}
</style>
</head>
<body>
<header>
  <div class="inner">
    <h1>✦ ClawMetry · <span class="hl">Claude Code</span></h1>
    <span class="vbadge">v{{ version }}</span>
    <span class="live-dot" title="Live — refreshes every 10s"></span>
  </div>
</header>

<div class="container">
  <div class="stats">
    <div class="stat"><div class="lbl">Sessions</div>
      <div class="val" id="s-sessions">—</div>
      <div class="sub" id="s-sessions-sub"></div></div>
    <div class="stat"><div class="lbl">Total Tokens</div>
      <div class="val" id="s-tokens">—</div>
      <div class="sub" id="s-tokens-sub"></div></div>
    <div class="stat c-green"><div class="lbl">Total Cost</div>
      <div class="val" id="s-cost">—</div></div>
    <div class="stat c-accent"><div class="lbl">Projects</div>
      <div class="val" id="s-projects">—</div></div>
  </div>

  <div class="tabs">
    <button class="tab active" data-tab="sessions">Sessions</button>
    <button class="tab" data-tab="analytics">Analytics</button>
    <button class="tab" data-tab="projects">Projects</button>
  </div>

  <div class="panel active" id="panel-sessions">
    <div class="filters">
      <select id="fp"><option value="">All Projects</option></select>
      <select id="fm"><option value="">All Models</option></select>
      <input type="text" id="fs" placeholder="Search sessions…">
    </div>
    <div class="tw">
      <table><thead><tr>
        <th>Project</th><th>Task</th><th>Model</th>
        <th style="text-align:right">Tokens</th>
        <th style="text-align:right">Cost</th>
        <th style="text-align:right">Tools</th>
        <th>Time</th>
      </tr></thead><tbody id="stb"></tbody></table>
    </div>
  </div>

  <div class="panel" id="panel-analytics">
    <div class="chart-card">
      <div class="chart-title">Daily Token Usage</div>
      <div class="bar-chart" id="ch-daily"></div>
    </div>
    <div class="g2">
      <div class="chart-card">
        <div class="chart-title">Model Usage</div>
        <div class="tw"><table><thead><tr><th>Model</th><th style="text-align:right">Tokens</th></tr></thead>
        <tbody id="mu-tb"></tbody></table></div>
      </div>
      <div class="chart-card">
        <div class="chart-title">Top Tools</div>
        <div class="tw"><table><thead><tr><th>Tool</th><th style="text-align:right">Calls</th></tr></thead>
        <tbody id="ts-tb"></tbody></table></div>
      </div>
    </div>
  </div>

  <div class="panel" id="panel-projects">
    <div id="projects-list"></div>
  </div>
</div>

<div class="overlay" id="ov">
  <div class="modal">
    <div class="modal-hdr">
      <h3 id="m-title">Session</h3>
      <button class="modal-x" onclick="closeM()">×</button>
    </div>
    <div class="modal-meta" id="m-meta"></div>
    <div id="m-msgs"></div>
  </div>
</div>

<script>
(function(){
var D=document,Q=function(s){return D.querySelector(s)},QA=function(s){return D.querySelectorAll(s)};

// Tabs
QA('.tab').forEach(function(t){t.addEventListener('click',function(){
  QA('.tab').forEach(function(x){x.classList.remove('active')});
  QA('.panel').forEach(function(x){x.classList.remove('active')});
  t.classList.add('active');
  Q('#panel-'+t.dataset.tab).classList.add('active');
})});

var allS=[];
function fmt(n){if(n>=1e6)return(n/1e6).toFixed(1)+'M';if(n>=1e3)return(n/1e3).toFixed(1)+'K';return String(n)}
function fmtC(c){return'$'+c.toFixed(4)}
function fmtT(ts){if(!ts)return'—';var d=new Date(ts*1000);
  return d.toLocaleDateString(undefined,{day:'2-digit',month:'short'})+' '+d.toLocaleTimeString(undefined,{hour:'2-digit',minute:'2-digit'})}
function esc(s){var d=D.createElement('div');d.textContent=s||'';return d.innerHTML}
function sm(m){return(m||'').replace('claude-','').replace(/-202\d+$/,'').substring(0,24)}

// Simple markdown to HTML
function md(text){
  if(!text)return'';
  var h=esc(text);
  // Code blocks
  h=h.replace(/```(\w*)\n([\s\S]*?)```/g,function(_,lang,code){
    return'<pre><code>'+code+'</code></pre>'});
  // Inline code
  h=h.replace(/`([^`]+)`/g,'<code>$1</code>');
  // Headers
  h=h.replace(/^### (.+)$/gm,'<h3>$1</h3>');
  h=h.replace(/^## (.+)$/gm,'<h2>$1</h2>');
  h=h.replace(/^# (.+)$/gm,'<h1>$1</h1>');
  // Bold
  h=h.replace(/\*\*(.+?)\*\*/g,'<strong>$1</strong>');
  // Italic
  h=h.replace(/\*(.+?)\*/g,'<em>$1</em>');
  // Lists
  h=h.replace(/^- (.+)$/gm,'<li>$1</li>');
  h=h.replace(/(<li>.*<\/li>\n?)+/g,'<ul>$&</ul>');
  // Blockquote
  h=h.replace(/^> (.+)$/gm,'<blockquote>$1</blockquote>');
  // Paragraphs (double newline)
  h=h.replace(/\n\n/g,'</p><p>');
  h=h.replace(/\n/g,'<br>');
  return'<p>'+h+'</p>';
}

// Memory preview markdown
function mdMem(text){
  if(!text)return'';
  var h=esc(text);
  h=h.replace(/^### (.+)$/gm,'<h3>$1</h3>');
  h=h.replace(/^## (.+)$/gm,'<h2>$1</h2>');
  h=h.replace(/^# (.+)$/gm,'<h1>$1</h1>');
  h=h.replace(/\*\*(.+?)\*\*/g,'<strong>$1</strong>');
  h=h.replace(/`([^`]+)`/g,'<code style="background:var(--surface-hover);padding:1px 4px;border-radius:2px;font-size:0.85em">$1</code>');
  h=h.replace(/^- (.+)$/gm,'• $1');
  h=h.replace(/\n/g,'<br>');
  return h;
}

function renderS(sessions){
  var tb=Q('#stb');
  if(!sessions.length){tb.innerHTML='<tr><td colspan="7" style="text-align:center;padding:40px;color:var(--text-tertiary)">No sessions found</td></tr>';return}
  tb.innerHTML=sessions.slice(0,200).map(function(s){
    return'<tr onclick="openS(\''+esc(s.session_id)+'\')">'
      +'<td><span class="b b-proj">'+esc(s.project)+'</span></td>'
      +'<td class="trunc">'+esc(s.first_user_text||'—')+'</td>'
      +'<td><span class="b b-model">'+esc(sm(s.model))+'</span></td>'
      +'<td class="tok" style="text-align:right">'+fmt(s.tokens||0)+'</td>'
      +'<td class="cost" style="text-align:right">'+fmtC(s.cost_usd||0)+'</td>'
      +'<td style="text-align:right">'+(s.tool_call_count||0)+'</td>'
      +'<td class="dim sm">'+fmtT(s.start_ts)+'</td></tr>'
  }).join('')}

function applyF(){
  var p=Q('#fp').value,m=Q('#fm').value,q=Q('#fs').value.toLowerCase();
  var f=allS.filter(function(s){
    if(p&&s.project!==p)return false;
    if(m&&s.model!==m)return false;
    if(q){var h=((s.first_user_text||'')+' '+(s.project||'')+' '+(s.session_id||'')).toLowerCase();
      if(h.indexOf(q)===-1)return false}
    return true});
  renderS(f)}
Q('#fp').addEventListener('change',applyF);
Q('#fm').addEventListener('change',applyF);
Q('#fs').addEventListener('input',applyF);

function loadSessions(){
  fetch('api/sessions?limit=500').then(function(r){return r.json()}).then(function(data){
    allS=data.sessions||[];
    Q('#s-sessions').textContent=allS.length;
    var tt=0,tc=0,projs={},models={};
    allS.forEach(function(s){tt+=s.tokens||0;tc+=s.cost_usd||0;
      projs[s.project]=(projs[s.project]||0)+1;if(s.model)models[s.model]=true});
    Q('#s-tokens').textContent=fmt(tt);
    Q('#s-tokens-sub').textContent=tt.toLocaleString()+' tokens';
    Q('#s-cost').textContent=fmtC(tc);
    Q('#s-projects').textContent=Object.keys(projs).length;
    // Filters (only update if empty)
    var psel=Q('#fp');if(psel.options.length<=1){
      Object.keys(projs).sort().forEach(function(p){var o=D.createElement('option');
        o.value=p;o.textContent=p+' ('+projs[p]+')';psel.appendChild(o)})}
    var msel=Q('#fm');if(msel.options.length<=1){
      Object.keys(models).sort().forEach(function(m){var o=D.createElement('option');
        o.value=m;o.textContent=sm(m);msel.appendChild(o)})}
    renderS(allS)})
}

function loadAnalytics(){
  fetch('api/analytics').then(function(r){return r.json()}).then(function(data){
    var daily=data.daily_tokens||{},days=Object.keys(daily).sort();
    var mx=Math.max.apply(null,days.map(function(d){return daily[d]}).concat([1]));
    Q('#ch-daily').innerHTML=days.slice(-30).map(function(d){
      var h=Math.max(3,(daily[d]/mx)*110);
      return'<div class="bar" style="height:'+h+'px;flex:1"><div class="tip">'+d+'<br>'+fmt(daily[d])+' tokens</div></div>'
    }).join('');
    var mu=data.model_usage||{};
    Q('#mu-tb').innerHTML=Object.keys(mu).sort(function(a,b){return mu[b]-mu[a]}).map(function(m){
      return'<tr style="cursor:default"><td><span class="b b-model">'+esc(sm(m))+'</span></td><td class="tok" style="text-align:right">'+fmt(mu[m])+'</td></tr>'
    }).join('');
    var ts=data.tool_stats||{};
    Q('#ts-tb').innerHTML=Object.keys(ts).map(function(t){
      return'<tr style="cursor:default"><td><span class="b b-tool">'+esc(t)+'</span></td><td style="text-align:right;font-weight:600">'+ts[t]+'</td></tr>'
    }).join('')})}

function loadProjects(){
  fetch('api/projects').then(function(r){return r.json()}).then(function(data){
    var el=Q('#projects-list'),ps=data.projects||[];
    el.innerHTML=ps.map(function(p){
      var memHtml='';
      if(p.memory_preview){
        memHtml='<div class="mem-card">'+mdMem(p.memory_preview)+'</div>'
      }
      return'<div class="chart-card" style="margin-bottom:12px">'
        +'<div style="display:flex;justify-content:space-between;align-items:center">'
        +'<div><span class="b b-proj" style="font-size:0.85rem">'+esc(p.name)+'</span>'
        +'<span class="dim sm" style="margin-left:10px;font-family:var(--mono)">'+esc(p.path)+'</span></div>'
        +'<div><span class="tok">'+p.sessions+' sessions</span>'
        +(p.has_memory?'<span class="b b-tool" style="margin-left:8px">MEMORY.md</span>':'')+'</div></div>'
        +memHtml+'</div>'
    }).join('')})}

// Initial load
loadSessions();loadAnalytics();loadProjects();

// Real-time polling every 10s
setInterval(loadSessions,10000);

// Modal
window.openS=function(sid){
  Q('#ov').classList.add('on');
  Q('#m-title').textContent='Loading…';
  Q('#m-meta').innerHTML='';
  Q('#m-msgs').innerHTML='';
  fetch('api/session/'+encodeURIComponent(sid)).then(function(r){return r.json()}).then(function(d){
    Q('#m-title').textContent=d.name||sid;
    Q('#m-meta').innerHTML=
      '<span><strong>Model</strong> '+(d.model||'—')+'</span>'
      +'<span><strong>Messages</strong> '+(d.messageCount||0)+'</span>'
      +'<span><strong>Tokens</strong> '+fmt(d.totalTokens||0)
      +' <span class="dim">('+fmt(d.inputTokens||0)+'↓ '+fmt(d.outputTokens||0)+'↑)</span></span>'
      +'<span><strong>Duration</strong> '+(d.duration||'—')+'</span>';
    var msgs=d.messages||[];
    Q('#m-msgs').innerHTML=msgs.map(function(m){
      var role=m.role||'unknown';
      var cls=role;
      if(role==='tool_result'&&m.is_error)cls+=' err';
      var label=role;
      var content='';
      if(role==='human'){
        label='👤 You';
        content='<div class="md-content">'+md(m.content||'')+'</div>';
      } else if(role==='assistant'){
        label='✦ Claude';
        content='<div class="md-content">'+md(m.content||'')+'</div>';
      } else if(role==='thinking'){
        label='💭 Thinking';
        content='<pre>'+esc(m.content||'')+'</pre>';
      } else if(role==='tool_use'){
        label='🔧 Tool: '+(m.tool_name||'');
        content='<pre>'+esc(m.content||'')+'</pre>';
      } else if(role==='tool_result'){
        label=(m.is_error?'❌':'📋')+' Tool Result';
        content='<pre>'+esc(m.content||'')+'</pre>';
      }
      return'<div class="msg '+cls+'">'
        +'<div class="rl">'+label+'</div>'
        +content+'</div>'
    }).join('')
  }).catch(function(){
    Q('#m-title').textContent='Error';
    Q('#m-msgs').innerHTML='<p class="dim" style="text-align:center;padding:40px">Failed to load session.</p>'
  })};

window.closeM=function(){Q('#ov').classList.remove('on')};
Q('#ov').addEventListener('click',function(e){if(e.target===this)closeM()});
D.addEventListener('keydown',function(e){if(e.key==='Escape')closeM()});
})();
</script>
</body>
</html>"""


# ---------------------------------------------------------------------------
# Standalone server
# ---------------------------------------------------------------------------


def create_app(claude_home: Optional[str] = None) -> Flask:
    """Create and configure the Flask application."""
    global CLAUDE_CODE_DIR

    if claude_home:
        os.environ["CLAWMETRY_CLAUDE_HOME"] = claude_home

    projects_dir = _get_claude_projects_dir()
    if projects_dir:
        CLAUDE_CODE_DIR = projects_dir
        logger.info("Claude Code projects directory: %s", projects_dir)
    else:
        logger.warning(
            "Claude Code projects directory not found at %s/projects",
            _get_claude_home(),
        )

    app = Flask(__name__)
    app.register_blueprint(bp_claudecode, url_prefix="/")
    return app


def main() -> None:
    """CLI entry point for standalone operation."""
    parser = argparse.ArgumentParser(
        prog="dashboard_claudecode",
        description="ClawMetry — Claude Code Observability Dashboard",
    )
    parser.add_argument(
        "--port", "-p", type=int, default=8901,
        help="Port (default: 8901)",
    )
    parser.add_argument(
        "--host", "-H", type=str, default="127.0.0.1",
        help="Host (default: 127.0.0.1)",
    )
    parser.add_argument(
        "--claude-home", type=str, default=None,
        help="Claude Code home directory (default: ~/.claude)",
    )
    parser.add_argument(
        "--debug", action="store_true", default=False,
        help="Enable debug mode",
    )
    parser.add_argument(
        "--version", "-v", action="version",
        version=f"dashboard_claudecode {__version__}",
    )

    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.debug else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    app = create_app(claude_home=args.claude_home)
    logger.info(
        "Starting Claude Code dashboard on http://%s:%d",
        args.host,
        args.port,
    )
    app.run(host=args.host, port=args.port, debug=args.debug)


if __name__ == "__main__":
    main()
