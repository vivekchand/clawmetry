"""ClawMetry MCP server — exposes local telemetry as MCP tools (stdio transport).

Start with: clawmetry mcp
Protocol: JSON-RPC 2.0, newline-delimited (MCP 2024-11-05).
Data source: the sync daemon's localhost query server (no DuckDB lock
contention): ``/api/local/query`` for the public shapes and
``/__local_query__/<method>`` for the allowlisted store methods.

Two kinds of tool live here (WO-59):

* **Read tools** — sessions, cost, traces, events, health, and now
  incidents, per-session guard status, signal rates and self-reports. A
  developer's editor can ask ClawMetry questions from where they already are.
* **One write tool** — ``report_to_operator``. An agent files a short note
  about what got in the way of its task. It is framed as feedback to the
  people who run the agent, never as a confession, because that framing is
  what current models will actually use.

**No tool here acts on a process.** Pause, stop and kill stay behind the
Guard surfaces named in CLAUDE.md's conventions. Adding an actuating tool to
this server means adding it to that list with locks of equal strength.

Every tool answers through the daemon and returns an honest error when the
daemon is not running, never an empty result that looks like "nothing
happened".
"""
from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

_DISCOVERY_PATH = Path(os.path.expanduser("~/.clawmetry/local_query.json"))
_CONFIG_PATH = Path(os.path.expanduser("~/.clawmetry/config.json"))

DAEMON_DOWN_MSG = "ClawMetry daemon is not running. Start it with: clawmetry sync"
_TIMEOUT_SECS = 10


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


def _post(path: str, payload: dict[str, Any]) -> dict[str, Any]:
    """POST to the daemon. Returns the parsed body, or ``{"error", "code"}``
    where ``code`` is ``daemon_down`` / ``refused`` / ``http`` / ``transport``
    so callers can tell "no daemon" from "this daemon does not know that
    method" and say the right thing."""
    disc = _read_discovery()
    if not disc:
        return {"error": DAEMON_DOWN_MSG, "code": "daemon_down"}
    req = urllib.request.Request(
        f"http://127.0.0.1:{disc['port']}{path}",
        data=json.dumps(payload).encode(),
        headers={
            "Authorization": f"Bearer {disc['token']}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=_TIMEOUT_SECS) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as exc:
        try:
            body = json.loads(exc.read().decode())
        except Exception:
            body = {}
        msg = str(body.get("error") or exc.reason or exc)
        code = "refused" if exc.code == 400 and "not allowed" in msg else "http"
        return {"error": msg, "code": code, "status": exc.code}
    except Exception as exc:
        import socket as _socket
        is_timeout = isinstance(exc, (_socket.timeout, TimeoutError)) or isinstance(
            getattr(exc, "reason", None), (_socket.timeout, TimeoutError))
        if is_timeout:
            # The daemon IS running (its pid answered the liveness probe); it
            # did not answer in time. Saying "not running" here would send
            # the operator to restart something that is merely busy.
            return {"error": "ClawMetry daemon is running but did not answer within "
                             f"{_TIMEOUT_SECS}s; it may be busy. Try again shortly.",
                    "code": "timeout"}
        return {"error": f"{DAEMON_DOWN_MSG} ({exc})", "code": "transport"}


def _query(shape: str, args: dict[str, Any] | None = None) -> dict[str, Any]:
    return _post("/api/local/query", {"shape": shape, "args": args or {}})


def _method(name: str, **kwargs: Any) -> dict[str, Any]:
    """Call one allowlisted LocalStore method through the daemon. Returns
    ``{"result": ...}`` or ``{"error", "code"}``. A daemon that predates the
    method says so in plain words (``code: refused``) instead of leaking the
    allowlist error, because the fix is an upgrade, not a different call."""
    res = _post(f"/__local_query__/{name}", {"kwargs": kwargs})
    if res.get("code") == "refused":
        res["error"] = (f"This ClawMetry daemon does not provide {name} yet. "
                        "Upgrade and restart it with: clawmetry update")
    return res


def _node_id() -> str:
    try:
        data = json.loads(_CONFIG_PATH.read_text())
        return str(data.get("node_id") or "")[:128]
    except Exception:
        return ""


# ── Tool catalogue ───────────────────────────────────────────────────────────

_WINDOW_PROP = {
    "type": "string",
    "description": "Lookback window such as 30m, 24h, 7d (default 24h)",
}

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
    # ── WO-59: self-diagnostics ─────────────────────────────────────────
    {
        "name": "report_to_operator",
        "description": (
            "Send a short note to your operators, the people who run this "
            "agent, about anything that got in the way of the task: a tool "
            "that kept failing, context or a permission you were missing, "
            "something you could not do, a task you could not finish, a "
            "block you worked around, or anything else they would want to "
            "know. One or two sentences is plenty. Notes go to the ClawMetry "
            "dashboard next to this session; they help your operators fix "
            "the setup for next time."
        ),
        "inputSchema": {
            "type": "object",
            "required": ["category", "summary"],
            "properties": {
                "category": {
                    "type": "string",
                    "description": (
                        "One of: missing_context (you lacked information you "
                        "needed), repeatedly_broken_tool (a tool failed more "
                        "than once), capability_gap (something you had no way "
                        "to do), task_failure (you could not finish), "
                        "bypassed_block (you worked around a refusal or a "
                        "block), noteworthy (anything else worth knowing). "
                        "Operators may add categories."
                    ),
                },
                "summary": {
                    "type": "string",
                    "description": "What happened, in plain words (up to 500 characters)",
                },
                "session_id": {
                    "type": "string",
                    "description": (
                        "The session this note belongs to. Optional: inferred "
                        "from the environment or the working directory when absent"
                    ),
                },
                "runtime": {
                    "type": "string",
                    "description": "The agent runtime (claude_code, cursor, codex, ...). Optional",
                },
            },
        },
    },
    {
        "name": "list_incidents",
        "description": (
            "List detector incidents ClawMetry recorded from outside the agent: "
            "stuck loops, no progress, repeated tool failures, action "
            "discrepancies, file blast radius, credential access, network "
            "egress, privilege changes. Each carries session, runtime, "
            "severity, first/last seen and the spend at risk."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "window": _WINDOW_PROP,
                "runtime": {"type": "string", "description": "Filter to one runtime id"},
                "session_id": {"type": "string", "description": "Filter to one session"},
                "limit": {"type": "integer", "description": "Max rows (default 100)"},
            },
        },
    },
    {
        "name": "get_guard_status",
        "description": (
            "Guard status for one session: whether this node can control it "
            "(and which actions apply, with the reason when it cannot), any "
            "policy decisions recorded for it, and its open incidents. Read "
            "only: this tool never pauses, stops or kills anything."
        ),
        "inputSchema": {
            "type": "object",
            "required": ["session_id"],
            "properties": {
                "session_id": {"type": "string", "description": "The session to inspect"},
                "runtime": {
                    "type": "string",
                    "description": "Runtime id when the session id carries no prefix",
                },
            },
        },
    },
    {
        "name": "get_signal_rates",
        "description": (
            "Per-runtime signal rates (incidents, denials, self-reports per "
            "hour) over a window, when this daemon version provides them."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "window": _WINDOW_PROP,
                "runtime": {"type": "string", "description": "Filter to one runtime id"},
            },
        },
    },
    {
        "name": "list_self_reports",
        "description": (
            "List notes agents sent to their operators through "
            "report_to_operator, newest first, with whether each was "
            "corroborated by an independent detector incident or permission "
            "denial. Uncorroborated means no independent evidence was found, "
            "which is not the same as false."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "window": _WINDOW_PROP,
                "runtime": {"type": "string", "description": "Filter to one runtime id"},
                "category": {"type": "string", "description": "Filter to one category"},
                "session_id": {"type": "string", "description": "Filter to one session"},
                "limit": {"type": "integer", "description": "Max rows (default 100)"},
            },
        },
    },
]

#: Guard: nothing on this server may act on a process. The test suite pins
#: this list against the tool names above.
ACTUATING_WORDS = ("pause", "resume", "stop", "kill", "terminate", "suspend")


def tools_catalogue() -> list[dict[str, Any]]:
    """The tool list as served, with the category enum resolved at call time
    so an operator-added category (config.json ``self_diagnostics.categories``)
    is offered to the agent without a restart."""
    import copy
    from clawmetry.self_diagnostics import allowed_categories

    tools = copy.deepcopy(_TOOLS)
    for tool in tools:
        if tool.get("name") == "report_to_operator":
            tool["inputSchema"]["properties"]["category"]["enum"] = list(allowed_categories())
    return tools


def _window_secs(value: Any, default: int = 86400) -> int:
    from clawmetry.self_diagnostics import parse_window_secs
    return parse_window_secs(value, default)


def _unwrap(res: dict[str, Any], key: str = "rows") -> dict[str, Any]:
    """``{"result": x}`` -> ``{key: x, "count": n}``; errors pass through."""
    if "error" in res:
        return res
    val = res.get("result")
    if isinstance(val, list):
        return {key: val, "count": len(val)}
    return {key: val}


# ── Tool implementations ─────────────────────────────────────────────────────

def _tool_report_to_operator(arguments: dict[str, Any]) -> dict[str, Any]:
    from clawmetry import self_diagnostics as _sd

    category = _sd.normalize_category(arguments.get("category"))
    if not category:
        return {
            "error": f"category {arguments.get('category')!r} is not one of the "
                     f"allowed categories",
            "allowed": list(_sd.allowed_categories()),
        }
    summary = _sd.clip_summary(arguments.get("summary"))
    if not summary:
        return {"error": "summary is empty; say in a sentence what got in the way"}

    session_id = str(arguments.get("session_id") or "").strip()
    runtime = str(arguments.get("runtime") or "").strip().lower()
    inferred_from = "argument"
    if not session_id:
        session_id = _sd.infer_session_from_env()
        inferred_from = "environment" if session_id else ""
    if not runtime:
        runtime = _sd.runtime_from_session_id(session_id) or _sd.infer_runtime_from_env()
    if not session_id:
        # Last resort: the session whose working directory contains ours.
        try:
            cwd = os.getcwd()
        except OSError:
            cwd = ""
        if cwd:
            found = _method("find_session_by_cwd", cwd=cwd, runtime=runtime)
            if "error" in found and found.get("code") in ("daemon_down", "transport"):
                return {"error": found["error"], "code": found["code"]}
            hit = found.get("result")
            if isinstance(hit, dict) and hit.get("session_id"):
                session_id = str(hit["session_id"])
                inferred_from = "working directory"
                if not runtime:
                    runtime = (_sd.runtime_from_session_id(session_id)
                               or str(hit.get("agent_type") or ""))

    res = _method(
        "ingest_self_report",
        session_id=session_id, category=category, summary=summary,
        agent_type=runtime, node_id=_node_id(),
    )
    if "error" in res:
        if res.get("code") == "refused":
            return {"error": "This ClawMetry daemon is too old to accept self-reports. "
                             "Upgrade with: clawmetry update", "code": "refused"}
        return res
    row = res.get("result")
    if isinstance(row, dict) and row.get("error"):
        return row
    out = {
        "ok": True,
        "report": row,
        "session_id": session_id or "",
        "session_source": inferred_from,
    }
    if not session_id:
        out["note"] = ("No session could be inferred; the note was stored without a "
                       "session and cannot be corroborated. Pass session_id next time.")
    return out


def _tool_list_incidents(arguments: dict[str, Any]) -> dict[str, Any]:
    res = _method(
        "query_guard_incidents",
        since_secs=_window_secs(arguments.get("window")),
        runtime=str(arguments.get("runtime") or ""),
        session_id=str(arguments.get("session_id") or ""),
        limit=int(arguments.get("limit") or 100),
    )
    out = _unwrap(res, "incidents")
    if "error" not in out:
        for inc in out.get("incidents") or []:
            if isinstance(inc, dict):
                inc.pop("details", None)  # evidence is large; the summary fields stay
    return out


def _tool_get_guard_status(arguments: dict[str, Any]) -> dict[str, Any]:
    from clawmetry import self_diagnostics as _sd

    session_id = str(arguments.get("session_id") or "").strip()
    if not session_id:
        return {"error": "session_id is required"}
    runtime = (str(arguments.get("runtime") or "").strip().lower()
               or _sd.runtime_from_session_id(session_id))

    loc = _method("get_session_location", session_id=session_id)
    if "error" in loc and loc.get("code") in ("daemon_down", "transport"):
        return {"error": loc["error"], "code": loc["code"]}
    location = loc.get("result") if isinstance(loc.get("result"), dict) else {}
    cwd = str((location or {}).get("cwd") or "")
    if not runtime:
        runtime = str((location or {}).get("agent_type") or "openclaw")

    # The single capability verdict every Guard surface reads. Resolved
    # here, on the node, because the answer depends on this OS and on
    # whether the session is a real process tree.
    try:
        from clawmetry import process_control as _pc
        support = _pc.runtime_control_support(runtime, session_id, cwd)
    except Exception as exc:  # noqa: BLE001
        support = {"controllable": False, "actions": [],
                   "reason": f"capability check failed: {exc}"}

    actions = _method("query_policy_actions", limit=500)
    policy_actions = [
        a for a in (actions.get("result") or [])
        if isinstance(a, dict) and _sd.same_session(a.get("session_id"), session_id)
    ] if "error" not in actions else []
    for a in policy_actions:
        a.pop("evidence", None)

    incidents = _method("query_guard_incidents", since_secs=86400,
                        session_id=session_id, limit=50)
    inc_rows = incidents.get("result") if "error" not in incidents else []
    for inc in inc_rows or []:
        if isinstance(inc, dict):
            inc.pop("details", None)

    return {
        "session_id": session_id,
        "runtime": runtime,
        "cwd": cwd,
        "control": {
            "controllable": bool(support.get("controllable")),
            "actions": support.get("actions", []),
            "reason": support.get("reason", ""),
            "note": support.get("note", ""),
        },
        "policy_actions": policy_actions,
        "incidents": inc_rows or [],
        "read_only": True,
        "how_to_act": ("Use the Guard tab or POST /api/guard/control on the node; "
                       "this MCP server does not act on processes."),
    }


def _tool_get_signal_rates(arguments: dict[str, Any]) -> dict[str, Any]:
    """Behaviour-signal rates (WO-58) shaped the same way the Signals tab
    shapes them: grouped counts come from the daemon, the rate arithmetic
    runs here. A daemon that predates the signals store says so."""
    import time as _time

    window = _window_secs(arguments.get("window"))
    runtime = str(arguments.get("runtime") or "").strip().lower()
    days = max(1, int(round(window / 86400.0)))
    res = _method(
        "query_signal_grouped",
        since_ms=int((_time.time() - window) * 1000),
        runtime=runtime or None,
    )
    if "error" in res:
        if res.get("code") == "refused":
            return {
                "available": False,
                "error": "signals not available on this daemon version",
                "hint": "Incidents and self-reports are still readable with "
                        "list_incidents and list_self_reports.",
            }
        return res
    grouped = res.get("result") if isinstance(res.get("result"), dict) else {}
    try:
        from clawmetry import behaviour_signals as _bs
        rates = _bs.shape_rates(grouped.get("turns") or [], grouped.get("matches") or [],
                                window_days=days, runtime=runtime or None)
    except Exception as exc:  # noqa: BLE001
        return {"available": True, "grouped": grouped,
                "note": f"raw grouped counts; rate shaping failed: {exc}"}
    return {"available": True, "window_secs": window, "runtime": runtime or "all",
            "rates": rates}


def _tool_list_self_reports(arguments: dict[str, Any]) -> dict[str, Any]:
    from clawmetry import self_diagnostics as _sd

    res = _method(
        "query_self_reports",
        since_secs=_window_secs(arguments.get("window")),
        runtime=str(arguments.get("runtime") or ""),
        category=str(arguments.get("category") or ""),
        session_id=str(arguments.get("session_id") or ""),
        limit=int(arguments.get("limit") or 100),
    )
    out = _unwrap(res, "reports")
    if "error" not in out:
        out["uncorroborated_means"] = (
            "No independent evidence was found for this report, which is not "
            "the same as false."
        )
        out["corroboration_window_secs"] = _sd.corroboration_window_secs()
    return out


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
    if name == "report_to_operator":
        return _tool_report_to_operator(arguments)
    if name == "list_incidents":
        return _tool_list_incidents(arguments)
    if name == "get_guard_status":
        return _tool_get_guard_status(arguments)
    if name == "get_signal_rates":
        return _tool_get_signal_rates(arguments)
    if name == "list_self_reports":
        return _tool_list_self_reports(arguments)
    return {"error": f"Unknown tool: {name!r}"}


def _write(obj: dict[str, Any]) -> None:
    sys.stdout.write(json.dumps(obj) + "\n")
    sys.stdout.flush()


def handle_request(req: dict[str, Any]) -> dict[str, Any] | None:
    """One JSON-RPC request -> one response dict (or ``None`` for a
    notification). Split out of :func:`run` so tests can drive the protocol
    without a stdin loop."""
    req_id = req.get("id")
    method = req.get("method", "")
    params = req.get("params") or {}

    if method == "initialize":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "clawmetry", "version": "1.1.0"},
            },
        }
    if method in ("initialized", "notifications/initialized"):
        return None  # client notification — no response
    if method == "tools/list":
        return {"jsonrpc": "2.0", "id": req_id, "result": {"tools": tools_catalogue()}}
    if method == "tools/call":
        tool_name = params.get("name", "")
        tool_args = params.get("arguments") or {}
        try:
            result = _call_tool(tool_name, tool_args)
        except Exception as exc:  # noqa: BLE001 — a tool bug must not kill the server
            result = {"error": f"tool {tool_name!r} failed: {exc}"}
        is_error = bool(isinstance(result, dict) and result.get("error"))
        return {
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
    if method == "ping" and req_id is not None:
        return {"jsonrpc": "2.0", "id": req_id, "result": {}}
    if req_id is not None:
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "error": {"code": -32601, "message": f"Method not found: {method}"},
        }
    return None


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
        resp = handle_request(req)
        if resp is not None:
            _write(resp)
