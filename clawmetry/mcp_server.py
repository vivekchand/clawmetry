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
        os.kill(pid, 0)  # raises OSError if the daemon process is dead
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
]


def _call_tool(name: str, arguments: dict[str, Any]) -> dict[str, Any]:
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
