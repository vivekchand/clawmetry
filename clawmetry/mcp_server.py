"""ClawMetry MCP server — exposes local telemetry as MCP tools (stdio transport).

Start with: clawmetry mcp
Protocol: JSON-RPC 2.0, newline-delimited (MCP 2024-11-05).
Data source: daemon /api/local/query endpoint (no DuckDB lock contention).
"""
from __future__ import annotations

import json
import os
import sys
import urllib.request
from pathlib import Path
from typing import Any

_DISCOVERY_PATH = Path(os.path.expanduser("~/.clawmetry/local_query.json"))


def _read_discovery() -> dict[str, Any] | None:
    try:
        data = json.loads(_DISCOVERY_PATH.read_text())
        port = int(data.get("port") or 0)
        token = data.get("token") or ""
        pid = int(data.get("pid") or 0)
        if not (port and token and pid):
            return None
        # os.kill(pid, 0) never raises on Windows, so a stale discovery
        # file would point every query at a dead daemon. is_alive() is
        # portable.
        from clawmetry.process_control import is_alive as _pid_alive

        if not _pid_alive(pid):
            return None
        return {"port": port, "token": token}
    except (FileNotFoundError, OSError, ValueError, json.JSONDecodeError):
        return None


def _query(shape: str, args: dict[str, Any] | None = None) -> dict[str, Any]:
    disc = _read_discovery()
    if not disc:
        return {
            "error": "ClawMetry daemon is not running. Start it with: clawmetry sync"
        }
    payload = json.dumps({"shape": shape, "args": args or {}}).encode()
    req = urllib.request.Request(
        f"http://127.0.0.1:{disc['port']}/api/local/query",
        data=payload,
        headers={
            "Authorization": f"Bearer {disc['token']}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode())
    except Exception as exc:
        return {"error": str(exc)}


_TOOLS = [
    {
        "name": "list_sessions",
        "description": (
            "List recent ClawMetry agent sessions. "
            "Each row includes session ID, model, token usage, cost, and status."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "limit": {
                    "type": "integer",
                    "description": "Maximum sessions to return (default 20, max 100)",
                },
                "since": {
                    "type": "string",
                    "description": "Return sessions after this ISO 8601 timestamp",
                },
            },
        },
    },
    {
        "name": "get_cost_summary",
        "description": (
            "Get aggregated token and cost summary. "
            "Returns totals for input tokens, output tokens, cached tokens, and USD cost."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "since": {
                    "type": "string",
                    "description": "Start of the aggregation window (ISO 8601)",
                },
                "until": {
                    "type": "string",
                    "description": "End of the aggregation window (ISO 8601)",
                },
            },
        },
    },
    {
        "name": "get_session_trace",
        "description": (
            "Get all events for a specific session — messages, tool calls, "
            "errors, and timing."
        ),
        "inputSchema": {
            "type": "object",
            "required": ["session_id"],
            "properties": {
                "session_id": {
                    "type": "string",
                    "description": "The session ID to retrieve events for",
                },
                "limit": {
                    "type": "integer",
                    "description": "Max events to return (default 500)",
                },
            },
        },
    },
    {
        "name": "list_events",
        "description": (
            "List raw events from the local store. "
            "Optionally filter by session ID, event type, or time range."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "session_id": {"type": "string", "description": "Filter to one session"},
                "event_type": {
                    "type": "string",
                    "description": "e.g. message, tool_call, tool_result, error",
                },
                "since": {"type": "string", "description": "ISO 8601 start timestamp"},
                "limit": {"type": "integer", "description": "Max events (default 200)"},
            },
        },
    },
    {
        "name": "get_health",
        "description": (
            "Get ClawMetry daemon health: DuckDB file size, session count, "
            "last sync time, and event ingestion rate."
        ),
        "inputSchema": {"type": "object", "properties": {}},
    },
    # ── Human-in-the-loop tools (clawmetry/questions.py) ──────────────────
    {
        "name": "send_notification",
        "description": (
            "Send a push notification to the operator's configured channels "
            "(phone push, Slack, webhook). Use when a long task finishes, a "
            "build/test/deploy fails, or a status update is worth sharing. "
            "Optionally include structured context (summary, filesChanged, "
            "errorMessage, nextSteps) for a richer message."
        ),
        "inputSchema": {
            "type": "object",
            "required": ["title", "body"],
            "properties": {
                "title": {"type": "string", "description": "Notification title (aim for under 60 chars)"},
                "body": {"type": "string", "description": "Notification body (aim for under 200 chars)"},
                "agentName": {
                    "type": "string",
                    "description": "Which agent sent this, e.g. 'Claude Code - myproject'",
                },
                "context": {
                    "type": "object",
                    "description": "Structured context: {type: task_complete|error|info, summary, details, filesChanged, errorMessage, errorFile, nextSteps}",
                },
            },
        },
    },
    {
        "name": "ask_user",
        "description": (
            "Ask the operator a question via push notification and wait for "
            "the answer. Types: 'confirm' (yes/no — use before destructive or "
            "irreversible actions), 'select' (2-6 options), 'input' (free "
            "text). Blocks until answered or timeout. If it returns "
            "answered: false, do NOT proceed with the risky action."
        ),
        "inputSchema": {
            "type": "object",
            "required": ["question"],
            "properties": {
                "question": {"type": "string", "description": "The question (max 500 chars). Be specific — the user is on their phone."},
                "type": {
                    "type": "string",
                    "enum": ["confirm", "select", "input"],
                    "description": "Question type (default confirm)",
                },
                "options": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Choices for select type (2-6). Required when type is select.",
                },
                "placeholder": {"type": "string", "description": "Placeholder for input type"},
                "context": {"type": "string", "description": "What you're working on, shown with the question (max 500 chars)"},
                "wait": {"type": "boolean", "description": "Block for the answer (default true). false returns a correlationId for wait_for_answer."},
                "timeoutMs": {"type": "integer", "description": "Max wait in ms (max 55000). Uses the configured wait ladder if omitted."},
                "agentName": {"type": "string", "description": "Which agent is asking, e.g. 'Claude Code - myproject'"},
                "sessionId": {"type": "string", "description": "Session ID for the audit trail"},
            },
        },
    },
    {
        "name": "wait_for_answer",
        "description": (
            "Poll for the operator's answer to a question created with "
            "ask_user wait: false. Returns {answered, value} or a timeout."
        ),
        "inputSchema": {
            "type": "object",
            "required": ["correlationId"],
            "properties": {
                "correlationId": {"type": "string", "description": "The correlationId returned by ask_user"},
                "timeoutMs": {"type": "integer", "description": "How long to wait in ms (default 30000, max 55000)"},
            },
        },
    },
    {
        "name": "cancel_question",
        "description": (
            "Cancel a pending question so it can no longer be answered. Use "
            "when the question became irrelevant (e.g. the user answered in "
            "chat first)."
        ),
        "inputSchema": {
            "type": "object",
            "required": ["correlationId"],
            "properties": {
                "correlationId": {"type": "string", "description": "The correlationId of the question to cancel"},
            },
        },
    },
]

_MAX_WAIT_MS = 55_000


def _call_hitl_tool(name: str, arguments: dict[str, Any]) -> dict[str, Any] | None:
    """Dispatch the human-in-the-loop tools. Returns None for other names."""
    try:
        from clawmetry import questions as _q
    except ImportError as exc:  # never crash the server loop
        return {"error": f"questions engine unavailable: {exc}"}
    if name == "send_notification":
        try:
            return _q.send_notification(
                title=arguments.get("title") or "",
                body=arguments.get("body") or "",
                agent_name=arguments.get("agentName") or "",
                context=arguments.get("context") or None,
            )
        except Exception as exc:
            return {"error": str(exc)}
    if name == "ask_user":
        try:
            wait = arguments.get("wait", True)
            timeout_ms = min(int(arguments.get("timeoutMs") or 0) or 30_000, _MAX_WAIT_MS)
            if wait:
                return _q.ask_blocking(
                    question=arguments.get("question") or "",
                    qtype=(arguments.get("type") or "confirm").strip().lower(),
                    options=arguments.get("options"),
                    placeholder=arguments.get("placeholder") or "",
                    context=arguments.get("context") or "",
                    agent_name=arguments.get("agentName") or "",
                    session_id=arguments.get("sessionId") or "",
                    source="mcp",
                    timeout_s=timeout_ms / 1000.0,
                )
            row = _q.create_question(
                question=arguments.get("question") or "",
                qtype=(arguments.get("type") or "confirm").strip().lower(),
                options=arguments.get("options"),
                placeholder=arguments.get("placeholder") or "",
                context=arguments.get("context") or "",
                agent_name=arguments.get("agentName") or "",
                session_id=arguments.get("sessionId") or "",
                source="mcp",
            )
            expires = row.get("expires_at") or ""
            return {"correlationId": row["id"], "status": "pending",
                    "expiresAt": expires,
                    "notifiedChannels": row.get("notified_channels", [])}
        except ValueError as exc:
            return {"error": str(exc)}
        except Exception as exc:
            return {"error": str(exc)}
    if name == "wait_for_answer":
        timeout_ms = min(int(arguments.get("timeoutMs") or 30_000), _MAX_WAIT_MS)
        return _q.wait_for_answer(
            arguments.get("correlationId") or "", timeout_s=timeout_ms / 1000.0)
    if name == "cancel_question":
        return _q.cancel_question(arguments.get("correlationId") or "", actor="agent")
    return None


def _call_tool(name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    hitl = _call_hitl_tool(name, arguments)
    if hitl is not None:
        return hitl
    if name == "list_sessions":
        return _query(
            "sessions",
            {
                "limit": arguments.get("limit", 20),
                "since": arguments.get("since"),
            },
        )
    if name == "get_cost_summary":
        return _query(
            "aggregates",
            {
                "since": arguments.get("since"),
                "until": arguments.get("until"),
            },
        )
    if name == "get_session_trace":
        return _query(
            "transcript",
            {
                "session_id": arguments.get("session_id", ""),
                "limit": arguments.get("limit", 500),
            },
        )
    if name == "list_events":
        return _query(
            "events",
            {
                "session_id": arguments.get("session_id"),
                "event_type": arguments.get("event_type"),
                "since": arguments.get("since"),
                "limit": arguments.get("limit", 200),
            },
        )
    if name == "get_health":
        return _query("health")
    return {"error": f"Unknown tool: {name!r}"}


def _write(obj: dict[str, Any]) -> None:
    sys.stdout.write(json.dumps(obj) + "\n")
    sys.stdout.flush()


def run() -> None:
    """Read JSON-RPC 2.0 from stdin, serve MCP protocol, write responses to stdout."""
    for raw_line in sys.stdin:
        raw_line = raw_line.strip()
        if not raw_line:
            continue
        try:
            req = json.loads(raw_line)
        except json.JSONDecodeError:
            continue

        req_id = req.get("id")
        method = req.get("method", "")
        params = req.get("params") or {}

        if method == "initialize":
            _write(
                {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {"tools": {}},
                        "serverInfo": {"name": "clawmetry", "version": "1.0.0"},
                    },
                }
            )
        elif method in ("initialized", "notifications/initialized"):
            pass  # client notification — no response
        elif method == "tools/list":
            _write(
                {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {"tools": _TOOLS},
                }
            )
        elif method == "tools/call":
            tool_name = params.get("name", "")
            tool_args = params.get("arguments") or {}
            result = _call_tool(tool_name, tool_args)
            is_error = bool(result.get("error"))
            _write(
                {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {
                        "content": [
                            {
                                "type": "text",
                                "text": json.dumps(result, indent=2, default=str),
                            }
                        ],
                        "isError": is_error,
                    },
                }
            )
        elif method == "ping" and req_id is not None:
            _write({"jsonrpc": "2.0", "id": req_id, "result": {}})
        elif req_id is not None:
            _write(
                {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "error": {
                        "code": -32601,
                        "message": f"Method not found: {method}",
                    },
                }
            )
