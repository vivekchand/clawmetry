"""
routes/components.py — Per-panel component detail endpoints.

Extracted from dashboard.py as Phase 5.9 of the incremental modularisation.
Owns the 5 routes registered on ``bp_components``:

  GET  /api/component/tool/<name>  — tool-panel detail (exec/browser/search/cron/tts/memory/session)
  GET  /api/component/runtime      — runtime environment info (Python, OS, uptime, disk)
  GET  /api/component/machine      — machine/host hardware info (CPU, GPU, load)
  GET  /api/component/gateway      — gateway routing events + stats
  GET  /api/component/brain        — LLM API call details (tokens, cost, duration)
  GET  /api/component/mcp          — MCP server aggregates (call counts, error rates, top tools)

Module-level helpers (``SESSIONS_DIR``, ``LOG_DIR``, ``_get_log_dirs``,
``_grep_log_file``, ``_record_heartbeat``, ``_provider_from_model``,
``_get_sessions``, ``_get_crons``, ``_get_memory_files``, ``get_local_ip``)
stay in ``dashboard.py`` and are reached via late ``import dashboard as _d``.
Pure mechanical move — zero behaviour change.
"""

import json
import os
import socket
import subprocess
import sys
import time
from datetime import datetime

from flask import Blueprint, jsonify, request
from clawmetry.config import is_local_store_read_enabled

bp_components = Blueprint('components', __name__)

# Per-tool response cache (15s TTL) — only used by api_component_tool
_api_tool_cache = {}
_api_tool_cache_time = {}

# Per-MCP response cache (15s TTL) — used by api_component_mcp
_api_mcp_cache: dict = {}
_api_mcp_cache_time: float = 0.0


# Map tool key to tool names in transcripts (also used by the local-store
# fast path so the fast path stays in lock-step with the legacy parser).
#
# Coverage for both OpenClaw-native tool ids (``exec`` / ``web_search`` /
# ``web_fetch``) and the claude-cli runner's canonical PascalCase ids
# (``Bash`` / ``WebSearch`` / ``WebFetch`` / ``Grep``). The keystone E2E
# silent-zero probe in ``scripts/accuracy_harness/keystone_e2e.py`` flags
# any new on-the-wire tool name that isn't surfaced under one of these
# families — keep the two in lock-step.
_TOOL_MAP = {
    "session": [
        "sessions_spawn",
        "sessions_send",
        "sessions_list",
        "sessions_poll",
    ],
    "exec": ["exec", "process", "Bash", "bash"],
    "browser": ["browser", "web_fetch", "WebFetch", "webfetch"],
    "search": ["web_search", "WebSearch", "websearch", "Grep", "grep"],
    "cron": ["cron"],
    "tts": ["tts"],
    "memory": ["Read", "read", "Write", "write", "Edit", "edit"],
}


def _mcp_server_from_tool_name(name: str):
    """Return the MCP server slug from ``mcp__<server>__<tool>``, or None."""
    parts = name.split("__", 2)
    if len(parts) >= 3 and parts[0] == "mcp" and parts[1]:
        return parts[1]
    return None


def _iter_tool_call_blocks(row: dict):
    """Yield ``(tool_name, arguments, status)`` for every tool-call block
    embedded in a DuckDB ``events`` row.

    Three shapes are handled (silent-zero bug-class fix — see
    ``feedback_synthetic_tests_missed_real_event_shape.md``):

    1. Legacy trajectory ``message`` event — ``data.message.content[]``
       carries ``toolCall`` (current) or ``tool_use`` (Anthropic-style
       legacy) blocks.
    2. v3 daemon-normalised ``model.completed`` event with the nested
       message preserved — same ``data.message.content[]`` walk as (1).
    3. v3 daemon-normalised ``model.completed`` event with ONLY
       ``data.toolMetas[]`` (the post-#1135 normalised shape, where the
       inner ``message`` block has been stripped). Each toolMeta carries
       ``{id, name, input}``.

    Audit P0 #4: the previous implementation queried for
    ``event_type='tool_call'`` rows that the daemon never writes — every
    row in DuckDB has the raw OpenClaw type (``message`` / ``assistant``
    / ``model.completed`` / …). All 10 component-tool endpoints fell
    through to the legacy JSONL parser as a result. Today's silent-zero
    fix (5th instance) extends that fix to cover model.completed.
    """
    data = row.get("data") if isinstance(row, dict) else None
    if not isinstance(data, dict):
        return

    # Shape 3 — v3 normalised ``toolMetas[]`` on model.completed. Surface
    # these FIRST so installs with only-normalised events still light up.
    tool_metas = data.get("toolMetas")
    if isinstance(tool_metas, list):
        for meta in tool_metas:
            if not isinstance(meta, dict):
                continue
            tname = meta.get("name") or meta.get("tool") or ""
            args = meta.get("input") or meta.get("arguments") or {}
            if not isinstance(args, dict):
                args = {"_raw": str(args)[:200]}
            # toolMetas have no error flag — daemon strips it. We default
            # to ok; if a paired tool.result event later carries
            # is_error=true, the legacy parser's toolResult branch will
            # surface that. Fast path keeps the simpler "ok" default.
            if tname:
                yield tname, args, "ok"

    # Shapes 1 + 2 — both walk data.message.content[]. May coexist with
    # toolMetas on a model.completed row; dedupe by tool name+args is
    # left to the caller (counts are per-block, which matches the legacy
    # parser).
    msg = data.get("message")
    if not isinstance(msg, dict):
        return
    # Only the assistant's turn carries tool calls; user turns carry tool
    # results (which we surface via the role==toolResult branch in the
    # legacy parser — out of scope here, the modal already shows ok/error
    # via the toolCall block alone).
    if msg.get("role") not in (None, "assistant"):
        return
    content = msg.get("content")
    if not isinstance(content, list):
        return
    for blk in content:
        if not isinstance(blk, dict):
            continue
        btype = blk.get("type")
        if btype not in ("toolCall", "tool_use"):
            continue
        tool_name = blk.get("name") or blk.get("tool") or ""
        args = blk.get("arguments") or blk.get("input") or {}
        if not isinstance(args, dict):
            args = {"_raw": str(args)[:200]}
        # Per-block error flag (Anthropic uses isError on tool_use_result;
        # toolCall blocks don't carry it directly — we leave it ok and let
        # the toolResult branch in the legacy parser surface failures).
        status = "error" if blk.get("isError") else "ok"
        yield tool_name, args, status


def _try_local_store_component_tool(name: str):
    """Tier-1 DuckDB fast path for /api/component/tool/<name>.

    Pulls today's ``message`` / ``assistant`` rows from the local store
    (the actual OpenClaw event types — see ``clawmetry/sync.py:1375``),
    walks the ``message.content[]`` blocks for ``toolCall`` / ``tool_use``
    entries, filters by the tool family for ``name`` (per ``_TOOL_MAP``),
    and shapes them into the same response the legacy JSONL parser
    returns (``{events, stats, total, name}``).

    Returns ``None`` to defer to the legacy fallback if:
      - the ``local_store`` module isn't importable
      - the events table is empty / has no matching tool-call blocks
      - any unexpected error happens (we'd rather degrade than 500)
    """
    # Issue #1291: route through daemon HTTP proxy. The previous direct
    # ``local_store.get_store()`` open collided with the sync daemon's
    # exclusive DuckDB lock (per memory `reference_duckdb_process_lock.md`),
    # forcing the call to error out → fall through to the slow JSONL
    # walker → 7s p95 the latency probe (#1287) surfaced.
    #
    # 2026-05-18 silent-zero bug-class fix (5th instance today): also
    # query ``model.completed`` — the daemon-normalised v3 assistant
    # event (per memory `reference_openclaw_v3_event_types.md`). Real
    # user installs in the wild have 0 ``message`` rows + only
    # ``model.completed`` rows, so the prior two-shape query silently
    # returned an empty events[] and the caller fell through to the 8s+
    # JSONL walker → modal stuck on "Loading...".
    #
    # ``subagent:assistant`` is included alongside ``message`` / ``assistant``
    # because OpenClaw v3's sub-agent turns carry the bulk of tool_use
    # blocks on real installs (per the keystone E2E silent-zero probe in
    # ``scripts/accuracy_harness/keystone_e2e.py`` and memory
    # ``feedback_synthetic_tests_missed_real_event_shape.md``). Without it,
    # WebSearch / WebFetch / Bash / Grep invocations from sub-agents
    # disappeared from /api/component/tool/<family> even though the
    # daemon's ``query_tool_call_invocations`` index found them.
    rows: list = []
    _TOOL_HOST_EVENT_TYPES = (
        "message",
        "assistant",
        "model.completed",      # from #1663 — daemon-normalised v3 assistant event
        "subagent:assistant",   # from #1682 — sub-agent tool_use blocks
    )
    try:
        from routes.local_query import local_store_via_daemon
        for et in _TOOL_HOST_EVENT_TYPES:
            try:
                got = local_store_via_daemon("query_events", event_type=et, limit=2000)
                if got:
                    rows.extend(got)
            except Exception:
                continue
    except Exception:
        rows = []

    # Single-process fallback (only when daemon proxy returns nothing — eg
    # local pytest run with no sync daemon). NEVER on a paired install:
    # daemon is the gatekeeper.
    if not rows:
        try:
            from clawmetry import local_store
            store = local_store.get_store(read_only=True)
            for et in _TOOL_HOST_EVENT_TYPES:
                try:
                    rows.extend(store.query_events(event_type=et, limit=2000))
                except Exception:
                    continue
        except Exception:
            pass

    tool_names = set(_TOOL_MAP.get(name, [name]))
    today = datetime.now().strftime("%Y-%m-%d")

    events = []
    today_calls = 0
    today_errors = 0
    for r in rows:
        ts = (r.get("ts") or "")
        if not ts.startswith(today):
            continue
        for tn, args, status in _iter_tool_call_blocks(r):
            if not tn or tn not in tool_names:
                continue
            today_calls += 1
            if status == "error":
                today_errors += 1

            evt = {"timestamp": ts, "status": status, "tool": tn}
            if name == "exec":
                evt["detail"] = (args.get("command") or str(args))[:200]
                evt["action"] = "exec"
            elif name == "browser":
                evt["action"] = args.get("action", "unknown")
                evt["detail"] = (args.get("targetUrl") or args.get("url")
                                 or args.get("selector") or evt["action"])
            elif name == "search":
                evt["detail"] = args.get("query", "?")
                evt["action"] = "search"
            elif name == "tts":
                evt["detail"] = (args.get("text") or "")[:100]
                evt["action"] = "tts"
                evt["voice"] = args.get("voice", "")
            elif name == "memory":
                path = args.get("file_path") or args.get("path") or "?"
                evt["detail"] = path
                evt["action"] = ("write" if tn in ("Write", "write", "Edit", "edit")
                                 else "read")
            elif name == "session":
                evt["detail"] = (args.get("sessionId") or args.get("name") or tn)
                evt["action"] = tn
                evt["session_status"] = "running"
            elif name == "cron":
                evt["detail"] = (args.get("expr") or args.get("action")
                                 or str(args)[:80])
                evt["action"] = "cron"
            else:
                evt["detail"] = str(args)[:120]
                evt["action"] = tn
            events.append(evt)

    # Issue #1291 / PR #1266 pattern: an empty result is NOT a miss — it's
    # a legitimate "no tool calls today for this tool family." Returning
    # None here would fall through to the 7s JSONL walker for every empty
    # tool, which is what the latency probe caught at p95=7.3s. Return a
    # populated shell instead.
    events.sort(key=lambda e: e.get("timestamp", ""), reverse=True)
    events = events[:50]
    return {
        "name":    name,
        "stats":   {"today_calls": today_calls, "today_errors": today_errors},
        "events":  events,
        "total":   today_calls,
        "_source": "local_store",
    }


@bp_components.route("/api/component/tool/<name>")
def api_component_tool(name):
    """Parse session transcripts for tool-specific events. Cached for 15s."""
    import dashboard as _d
    import time as _time

    now = _time.time()
    if name in _api_tool_cache and (now - _api_tool_cache_time.get(name, 0)) < 15:
        return jsonify(_api_tool_cache[name])

    # Tier-1 DuckDB fast path — opt-in via CLAWMETRY_LOCAL_STORE_READ=1.
    # Falls through to legacy JSONL parser when flag is unset, store is
    # empty, or no matching events for `name`.
    if is_local_store_read_enabled():
        fast = _try_local_store_component_tool(name)
        if fast is not None:
            _api_tool_cache[name] = fast
            _api_tool_cache_time[name] = now
            return jsonify(fast)
    sessions_dir = _d.SESSIONS_DIR or os.path.expanduser(
        "~/.openclaw/agents/main/sessions"
    )
    if not os.path.isdir(sessions_dir):
        for p in [
            os.path.expanduser("~/.clawdbot/agents/main/sessions"),
            os.path.expanduser("~/.moltbot/agents/main/sessions"),
            os.path.expanduser("~/.openclaw/agents/main/sessions"),
        ]:
            if os.path.isdir(p):
                sessions_dir = p
                break
    if not os.path.isdir(sessions_dir):
        sessions_dir = os.path.expanduser("~/.clawdbot/agents/main/sessions")

    today = datetime.now().strftime("%Y-%m-%d")

    # Map tool key to tool names in transcripts
    TOOL_MAP = {
        "session": [
            "sessions_spawn",
            "sessions_send",
            "sessions_list",
            "sessions_poll",
        ],
        "exec": ["exec", "process"],
        "browser": ["browser", "web_fetch"],
        "search": ["web_search"],
        "cron": ["cron"],
        "tts": ["tts"],
        "memory": ["Read", "read", "Write", "write", "Edit", "edit"],
    }

    tool_names = TOOL_MAP.get(name, [name])
    events = []
    today_calls = 0
    today_errors = 0

    # Hard 5s wall-clock cap on the legacy JSONL walker (silent-zero
    # bug-class fix, 2026-05-18). With a healthy DuckDB fast path the
    # walker should never fire, but installs without the daemon — or
    # with months of accumulated sessions/*.jsonl files — used to hang
    # the Sessions modal for 8s+ when the fast path missed (eg
    # model.completed-only stores before today's fix). Better to return
    # what we have within budget than to leave the UI stuck on
    # "Loading...".
    _jsonl_deadline = _time.time() + 5.0

    if os.path.isdir(sessions_dir):
        try:
            _files = os.listdir(sessions_dir)
        except OSError:
            _files = []
        # Bail entirely if there are too many candidate files — opening
        # + stat-ing 500+ jsonl files in one request blows the 5s budget
        # before any parsing happens. Return an empty shell so the UI
        # renders "no recent activity" instead of hanging.
        if len(_files) > 200:
            _files = []
        for fname in _files:
            if _time.time() > _jsonl_deadline:
                break  # 5s cap reached → return what we have so far
            if not fname.endswith(".jsonl"):
                continue
            fpath = os.path.join(sessions_dir, fname)
            try:
                mtime = os.path.getmtime(fpath)
                if datetime.fromtimestamp(mtime).strftime("%Y-%m-%d") != today:
                    continue

                with open(fpath, "r") as f:
                    for line in f:
                        try:
                            obj = json.loads(line.strip())
                        except json.JSONDecodeError:
                            continue

                        if obj.get("type") != "message":
                            continue
                        msg = obj.get("message", {})

                        # Tool calls (assistant side)
                        if msg.get("role") == "assistant":
                            for c in msg.get("content") or []:
                                if (
                                    isinstance(c, dict)
                                    and c.get("type") == "toolCall"
                                    and c.get("name") in tool_names
                                ):
                                    ts = obj.get("timestamp", "")
                                    if not ts.startswith(today):
                                        continue
                                    tn = c.get("name", "")
                                    args = c.get("arguments", {})
                                    today_calls += 1

                                    evt = {"timestamp": ts, "status": "ok", "tool": tn}

                                    if name == "exec":
                                        evt["detail"] = (
                                            args.get("command") or str(args)
                                        )[:200]
                                        evt["action"] = "exec"
                                    elif name == "browser":
                                        evt["action"] = args.get("action", "unknown")
                                        evt["detail"] = (
                                            args.get("targetUrl")
                                            or args.get("url")
                                            or args.get("selector")
                                            or evt["action"]
                                        )
                                    elif name == "search":
                                        evt["detail"] = args.get("query", "?")
                                        evt["action"] = "search"
                                    elif name == "tts":
                                        evt["detail"] = (args.get("text") or "")[:100]
                                        evt["action"] = "tts"
                                        evt["voice"] = args.get("voice", "")
                                    elif name == "memory":
                                        path = (
                                            args.get("file_path")
                                            or args.get("path")
                                            or "?"
                                        )
                                        evt["detail"] = path
                                        evt["action"] = (
                                            "write"
                                            if tn in ("Write", "write", "Edit", "edit")
                                            else "read"
                                        )
                                    elif name == "session":
                                        evt["detail"] = (
                                            args.get("sessionId")
                                            or args.get("name")
                                            or tn
                                        )
                                        evt["action"] = tn
                                        evt["session_status"] = "running"
                                    elif name == "cron":
                                        evt["detail"] = (
                                            args.get("expr")
                                            or args.get("action")
                                            or str(args)[:80]
                                        )
                                        evt["action"] = "cron"
                                    else:
                                        evt["detail"] = str(args)[:120]
                                        evt["action"] = tn

                                    events.append(evt)

                        # Tool results
                        elif (
                            msg.get("role") == "toolResult"
                            and msg.get("toolName") in tool_names
                        ):
                            ts = obj.get("timestamp", "")
                            if not ts.startswith(today):
                                continue
                            details = msg.get("details", {})
                            is_error = msg.get("isError", False) or (
                                isinstance(details, dict)
                                and details.get("status") == "error"
                            )
                            if is_error:
                                today_errors += 1
                                # Mark last matching event as error
                                for e in reversed(events):
                                    if (
                                        e.get("tool") == msg.get("toolName")
                                        and e.get("status") == "ok"
                                    ):
                                        e["status"] = "error"
                                        break

                            # Add duration from details
                            if isinstance(details, dict) and details.get("duration_ms"):
                                for e in reversed(events):
                                    if e.get("tool") == msg.get(
                                        "toolName"
                                    ) and not e.get("duration_ms"):
                                        e["duration_ms"] = details["duration_ms"]
                                        break

                            # For sessions, update status from result
                            if name == "session" and isinstance(details, dict):
                                for e in reversed(events):
                                    if e.get("tool") == msg.get("toolName"):
                                        if details.get("status") == "done":
                                            e["session_status"] = "done"
                                        if details.get("model"):
                                            e["model"] = details["model"]
                                        if details.get("tokens"):
                                            e["tokens"] = details["tokens"]
                                        break

            except Exception:
                continue

    # For cron, also pull from cron jobs data
    if name == "cron" and not events:
        try:
            crons = _d._get_crons()
            for cj in crons[:20]:
                events.append(
                    {
                        "timestamp": cj.get("lastRun") or cj.get("createdAt") or "",
                        "action": "cron",
                        "detail": (cj.get("expr") or "")
                        + " -> "
                        + (cj.get("task") or cj.get("command") or "")[:60],
                        "status": "ok" if cj.get("lastStatus") != "error" else "error",
                    }
                )
        except Exception:
            pass

    # For sessions, also pull live session data
    if name == "session" and not events:
        try:
            sessions = _d._get_sessions()
            for sess in sessions[:20]:
                events.append(
                    {
                        "timestamp": datetime.fromtimestamp(
                            sess["updatedAt"] / 1000
                        ).isoformat()
                        if sess.get("updatedAt")
                        else "",
                        "action": "session",
                        "detail": sess.get("displayName")
                        or sess.get("sessionId", "?")[:20],
                        "session_status": "running",
                        "model": sess.get("model", ""),
                        "tokens": sess.get("totalTokens", 0),
                        "status": "ok",
                    }
                )
        except Exception:
            pass

    # Sort by timestamp descending, limit to 50
    events.sort(key=lambda e: e.get("timestamp", ""), reverse=True)
    events = events[:50]

    result = {
        "name": name,
        "stats": {"today_calls": today_calls, "today_errors": today_errors},
        "events": events,
        "total": today_calls,
    }

    # Enrich with tool-specific data
    if name == "session":
        # Add live sub-agent data
        try:
            sa_data = {}
            result["subagents"] = sa_data.get("subagents", [])
        except Exception:
            result["subagents"] = []

    elif name == "exec":
        # Check for running background processes
        running = []
        try:
            proc_dir = os.path.expanduser("~/.openclaw/processes")
            if not os.path.isdir(proc_dir):
                proc_dir = os.path.expanduser("~/.clawdbot/processes")
            if os.path.isdir(proc_dir):
                for pf in os.listdir(proc_dir):
                    try:
                        with open(os.path.join(proc_dir, pf)) as pfile:
                            pdata = json.load(pfile)
                            if pdata.get("running", False):
                                running.append(
                                    {
                                        "command": pdata.get("command", "?"),
                                        "pid": pdata.get("pid", ""),
                                    }
                                )
                    except Exception:
                        pass
        except Exception:
            pass
        result["running_commands"] = running

    elif name == "browser":
        # Extract unique URLs from events
        seen = set()
        urls = []
        for evt in events:
            url = evt.get("detail", "")
            if url.startswith("http") and url not in seen:
                seen.add(url)
                urls.append({"url": url, "timestamp": evt.get("timestamp", "")})
        result["recent_urls"] = urls[:20]

    elif name == "cron":
        # Add full cron job list
        try:
            crons = _d._get_crons()
            result["cron_jobs"] = []
            for cj in crons:
                result["cron_jobs"].append(
                    {
                        "id": cj.get("id", ""),
                        "name": cj.get("name") or cj.get("task") or cj.get("id", "?"),
                        "expr": (
                            cj["expr"].get("expr", str(cj["expr"]))
                            if isinstance(cj.get("expr"), dict)
                            else cj.get("expr") or cj.get("schedule", "")
                        ),
                        "task": cj.get("task") or cj.get("command", ""),
                        "channel": cj.get("channel", ""),
                        "lastRun": cj.get("lastRun") or cj.get("lastRunAt", ""),
                        "nextRun": cj.get("nextRun") or cj.get("nextRunAt", ""),
                        "lastStatus": cj.get("lastStatus", "ok"),
                        "lastError": cj.get("lastError", ""),
                    }
                )
        except Exception:
            result["cron_jobs"] = []

    elif name == "memory":
        # Add workspace file listing
        try:
            result["memory_files"] = _d._get_memory_files()
        except Exception:
            result["memory_files"] = []

    _api_tool_cache[name] = result
    _api_tool_cache_time[name] = _time.time()
    return jsonify(result)


def _try_local_store_component_runtime():
    """Tier-1 DuckDB fast path for /api/component/runtime.

    Reads the latest system snapshot from DuckDB (written each sync cycle by
    the daemon). The daemon enriches the ``infra`` blob with python_version,
    os_name, os_release, arch, node_version, openclaw_version alongside the
    existing disk/RAM/uptime rows. Returns ``None`` to defer to the live-probe
    fallback if the snapshot is absent or pre-dates the new infra fields.
    """
    try:
        from routes.local_query import local_store_via_daemon
        snaps = local_store_via_daemon("query_system_snapshots", kind="system", limit=1)
        if snaps is None:
            from clawmetry import local_store
            store = local_store.get_store(read_only=True)
            snaps = store.query_system_snapshots(kind="system", limit=1)
    except Exception:
        return None
    if not snaps:
        return None

    snap = snaps[0]
    infra = snap.get("infra") or {}
    py_ver = infra.get("python_version") or ""
    if not py_ver:
        # Snapshot predates the infra-enrichment change — fall through to live probe.
        return None

    items = []
    items.append({"label": "Python", "value": py_ver, "status": "ok"})

    os_name = infra.get("os_name") or ""
    os_rel = infra.get("os_release") or ""
    if os_name:
        items.append({"label": "OS", "value": f"{os_name} {os_rel}".strip(), "status": "ok"})

    arch = infra.get("arch") or ""
    if arch:
        items.append({"label": "Architecture", "value": arch, "status": "ok"})

    oc_ver = infra.get("openclaw_version") or ""
    items.append({
        "label": "OpenClaw",
        "value": oc_ver or "unknown",
        "status": "ok" if oc_ver else "warning",
    })

    # Disk, RAM, Uptime rows are already probed by the daemon each cycle.
    color_map = {"green": "ok", "yellow": "warning", "red": "critical", "": "ok"}
    label_remap = {"RAM": "Memory"}
    for row in (snap.get("rows") or []):
        if not (isinstance(row, list) and len(row) >= 2):
            continue
        label = row[0]
        if label not in ("Disk /", "RAM", "Uptime"):
            continue
        status = color_map.get(row[2] if len(row) > 2 else "", "ok")
        items.append({
            "label": label_remap.get(label, label),
            "value": row[1],
            "status": status,
        })

    node_ver = infra.get("node_version") or ""
    if node_ver:
        items.append({"label": "Node.js", "value": node_ver, "status": "ok"})

    return {"items": items, "_source": "local_store"}


@bp_components.route("/api/component/runtime")
def api_component_runtime():
    """Return runtime environment info."""
    import platform

    if is_local_store_read_enabled():
        fast = _try_local_store_component_runtime()
        if fast is not None:
            return jsonify(fast)

    items = []
    items.append(
        {"label": "Python", "value": platform.python_version(), "status": "ok"}
    )
    items.append(
        {
            "label": "OS",
            "value": f"{platform.system()} {platform.release()}",
            "status": "ok",
        }
    )
    items.append({"label": "Architecture", "value": platform.machine(), "status": "ok"})
    # OpenClaw version
    try:
        oc_ver = (
            subprocess.check_output(
                ["openclaw", "--version"], stderr=subprocess.STDOUT, timeout=5
            )
            .decode()
            .strip()
        )
        items.append({"label": "OpenClaw", "value": oc_ver, "status": "ok"})
    except Exception:
        items.append({"label": "OpenClaw", "value": "unknown", "status": "warning"})
    # Uptime — portable across macOS/Linux/Win (GNU `uptime -p` is Linux-only).
    try:
        from helpers.system import uptime_pretty

        up = uptime_pretty()
        if up != "unknown":
            items.append({"label": "Uptime", "value": up, "status": "ok"})
    except Exception:
        pass
    # Memory
    try:
        mem = (
            subprocess.check_output(["free", "-h"], timeout=5)
            .decode()
            .strip()
            .split("\n")
        )
        if len(mem) >= 2:
            parts = mem[1].split()
            used, total = parts[2], parts[1]
            items.append(
                {"label": "Memory", "value": f"{used} / {total}", "status": "ok"}
            )
    except Exception:
        pass
    # Disk
    try:
        df = (
            subprocess.check_output(["df", "-h", "/"], timeout=5)
            .decode()
            .strip()
            .split("\n")
        )
        if len(df) >= 2:
            parts = df[1].split()
            items.append(
                {
                    "label": "Disk /",
                    "value": f"{parts[2]} / {parts[1]} ({parts[4]} used)",
                    "status": "critical"
                    if int(parts[4].replace("%", "")) > 90
                    else "warning"
                    if int(parts[4].replace("%", "")) > 80
                    else "ok",
                }
            )
    except Exception:
        pass
    # Node.js
    try:
        nv = subprocess.check_output(["node", "--version"], timeout=5).decode().strip()
        items.append({"label": "Node.js", "value": nv, "status": "ok"})
    except Exception:
        pass
    return jsonify({"items": items})


@bp_components.route("/api/component/machine")
def api_component_machine():
    """Return machine/host hardware info."""
    import dashboard as _d
    import platform

    items = []
    items.append({"label": "Hostname", "value": socket.gethostname(), "status": "ok"})
    # IP
    items.append({"label": "IP", "value": _d.get_local_ip(), "status": "ok"})
    # CPU
    try:
        with open("/proc/cpuinfo") as f:
            for line in f:
                if line.startswith("model name"):
                    items.append(
                        {
                            "label": "CPU",
                            "value": line.split(":")[1].strip(),
                            "status": "ok",
                        }
                    )
                    break
    except Exception:
        items.append(
            {"label": "CPU", "value": platform.processor() or "unknown", "status": "ok"}
        )
    # CPU cores
    items.append(
        {"label": "CPU Cores", "value": str(os.cpu_count() or "?"), "status": "ok"}
    )
    # Load average
    try:
        load = os.getloadavg()
        cores = os.cpu_count() or 1
        load_str = f"{load[0]:.2f} / {load[1]:.2f} / {load[2]:.2f}"
        status = (
            "critical"
            if load[0] > cores * 2
            else "warning"
            if load[0] > cores
            else "ok"
        )
        items.append({"label": "Load (1/5/15m)", "value": load_str, "status": status})
    except Exception:
        pass
    # GPU
    try:
        gpu = (
            subprocess.check_output(
                [
                    "nvidia-smi",
                    "--query-gpu=name,memory.used,memory.total,utilization.gpu",
                    "--format=csv,noheader,nounits",
                ],
                timeout=5,
            )
            .decode()
            .strip()
        )
        for line in gpu.split("\n"):
            parts = [p.strip() for p in line.split(",")]
            if len(parts) >= 4:
                items.append({"label": "GPU", "value": f"{parts[0]}", "status": "ok"})
                items.append(
                    {
                        "label": "GPU Memory",
                        "value": f"{parts[1]} MiB / {parts[2]} MiB",
                        "status": "ok",
                    }
                )
                items.append(
                    {
                        "label": "GPU Utilization",
                        "value": f"{parts[3]}%",
                        "status": "warning" if int(parts[3]) > 80 else "ok",
                    }
                )
    except Exception:
        items.append({"label": "GPU", "value": "N/A (no nvidia-smi)", "status": "ok"})
    # Kernel
    items.append({"label": "Kernel", "value": platform.release(), "status": "ok"})
    return jsonify({"items": items})


@bp_components.route("/api/component/storage")
def api_component_storage():
    """Disk usage per mount point. Same items shape as runtime/machine.

    Replaces the "Live view coming soon" stub on the Flow → Storage modal —
    every inch of the app needs to be 100% accurate per product mandate.
    """
    items = []
    try:
        # `df -h` excluding pseudo / overlay filesystems
        df_out = subprocess.check_output(
            ["df", "-h", "--output=source,target,used,size,pcent",
             "-x", "tmpfs", "-x", "devtmpfs", "-x", "squashfs",
             "-x", "overlay", "-x", "proc", "-x", "sysfs"],
            stderr=subprocess.DEVNULL, timeout=5,
        ).decode().strip().split("\n")[1:]  # skip header
        for line in df_out:
            parts = line.split()
            if len(parts) < 5:
                continue
            src, mount, used, size, pcent = parts[0], parts[1], parts[2], parts[3], parts[4]
            try:
                pct_int = int(pcent.rstrip("%"))
            except ValueError:
                pct_int = 0
            status = "critical" if pct_int > 90 else "warning" if pct_int > 80 else "ok"
            items.append({
                "label": f"📁 {mount}",
                "value": f"{used} / {size} ({pcent} used)",
                "status": status,
            })
    except Exception:
        # macOS df doesn't support --output / -x in the same way; fall back
        try:
            df_out = subprocess.check_output(
                ["df", "-h"], stderr=subprocess.DEVNULL, timeout=5,
            ).decode().strip().split("\n")[1:]
            for line in df_out:
                parts = line.split()
                if len(parts) < 6 or parts[5] in ("/dev", "/sys", "/proc"):
                    continue
                items.append({
                    "label": f"📁 {parts[5]}",
                    "value": f"{parts[2]} / {parts[1]} ({parts[4]} used)",
                    "status": "ok",
                })
        except Exception:
            items.append({
                "label": "Disk",
                "value": "Unable to read filesystem",
                "status": "warning",
            })
    if not items:
        items.append({
            "label": "Disk",
            "value": "No mounted filesystems detected",
            "status": "warning",
        })
    return jsonify({"items": items})


@bp_components.route("/api/component/network")
def api_component_network():
    """Network interfaces + connectivity check. Same items shape."""
    import dashboard as _d
    items = []
    # Hostname + primary IP from existing helper (also used by Machine modal)
    try:
        items.append({
            "label": "Hostname",
            "value": _d.platform.node() if hasattr(_d, "platform") else __import__("platform").node(),
            "status": "ok",
        })
    except Exception:
        pass
    try:
        ip = _d.get_local_ip() if hasattr(_d, "get_local_ip") else ""
        if ip:
            items.append({"label": "Primary IP", "value": ip, "status": "ok"})
    except Exception:
        pass
    # Interface list (Linux: /proc/net/dev; macOS: ifconfig fallback)
    try:
        with open("/proc/net/dev") as f:
            lines = f.read().strip().split("\n")[2:]
        for line in lines:
            parts = line.split(":")
            if len(parts) < 2:
                continue
            name = parts[0].strip()
            if name == "lo":
                continue
            stats = parts[1].split()
            try:
                rx_bytes = int(stats[0])
                tx_bytes = int(stats[8])
                def _h(n):
                    if n >= 1e9: return f"{n/1e9:.1f}G"
                    if n >= 1e6: return f"{n/1e6:.1f}M"
                    if n >= 1e3: return f"{n/1e3:.1f}K"
                    return f"{n}B"
                items.append({
                    "label": f"⇄ {name}",
                    "value": f"↓ {_h(rx_bytes)}  ↑ {_h(tx_bytes)}",
                    "status": "ok",
                })
            except Exception:
                continue
    except Exception:
        # macOS fallback — just list interfaces
        try:
            ifs = subprocess.check_output(
                ["ifconfig", "-l"], stderr=subprocess.DEVNULL, timeout=3,
            ).decode().strip().split()
            for name in ifs:
                if name == "lo0":
                    continue
                items.append({
                    "label": f"⇄ {name}",
                    "value": "active",
                    "status": "ok",
                })
        except Exception:
            pass
    # Connectivity check — quick HEAD to a known host
    try:
        out = subprocess.check_output(
            ["ping", "-c", "1", "-W", "1", "1.1.1.1"],
            stderr=subprocess.DEVNULL, timeout=3,
        ).decode()
        import re as _re_ping
        m = _re_ping.search(r"time=([\d.]+)\s*ms", out)
        if m:
            items.append({
                "label": "🌐 Internet",
                "value": f"Reachable ({m.group(1)} ms)",
                "status": "ok",
            })
    except Exception:
        items.append({
            "label": "🌐 Internet",
            "value": "Unreachable",
            "status": "warning",
        })
    if not items:
        items.append({
            "label": "Network",
            "value": "Unable to read interface info",
            "status": "warning",
        })
    return jsonify({"items": items})


def _try_local_store_component_gateway(limit: int, offset: int):
    """Tier-1 DuckDB fast path for /api/component/gateway (refs #1565).

    Sources the routing-event list and the four "today_*" counters
    (messages / heartbeats / crons / errors) from the daemon-ingested
    ``events`` table instead of re-parsing today's ``gateway.log``.

    Row → route shape mapping (real OpenClaw v3 names per
    ``reference_openclaw_v3_event_types.md``; legacy aliases included so
    pre-v3 / non-OpenClaw installs still light up the panel):

      * ``prompt.submitted`` / ``user`` (data.role=user)  → message in
      * ``model.completed`` / ``assistant``               → message out
        (``message`` event whose ``data.message.role`` says ``assistant``
        is also accepted — that's the Anthropic-SDK envelope shape the
        daemon writes for v2 sessions.)
      * ``cron.run.*``                                    → cron
      * ``heartbeat.*`` / ``gateway.metric``              → heartbeat
      * any row whose data carries ``errorCode`` / ``error``/
        ``is_error`` / event_type endswith ``.error``    → bumps errors

    Returns ``None`` (defer to legacy log parser) when the local store
    isn't reachable, holds zero rows, or holds rows but NONE of them
    map to a gateway-flow lane (covers the "store present for unrelated
    agent type" case so legacy gateway.log still drives the panel).

    Side-channel fields (``active_sessions``, ``config``, ``uptime``,
    ``restarts``) come from live OS / FS state — exempt from the
    DuckDB-first rule per ``feedback_duckdb_first_rule.md`` (live OS
    snapshot is exempt; only historical TREND must persist).
    """
    # Late imports avoid pulling DuckDB / routes.sessions on Flask boot
    # for users who never hit the gateway component panel.
    try:
        from routes.sessions import _ls_call  # daemon-proxy wrapper
    except Exception:
        return None

    today = datetime.now().strftime("%Y-%m-%d")
    rows = _ls_call("query_events", since=today, limit=2000) or []
    if not rows:
        return None

    # Map daemon-normalised v3 names + legacy aliases to one of the four
    # routing categories. Unknown event_types are skipped so the panel
    # doesn't fill with telemetry noise.
    _MSG_IN = {"prompt.submitted", "user"}
    _MSG_OUT = {"model.completed", "assistant"}
    _CRON = {"cron.run.started", "cron.run.completed", "cron.run.failed"}
    _HEARTBEAT = {"heartbeat", "heartbeat.tick", "gateway.metric"}

    def _classify(et: str, data: dict):
        """Return (route_type, stat_bucket) or (None, None) to skip."""
        if et in _MSG_IN:
            return "message", "today_messages"
        if et in _MSG_OUT:
            return "message", "today_messages"
        if et == "message" and isinstance(data, dict):  # v3-shape-gate: allow (reason: defensive — v3 names already handled above via _MSG_IN/_MSG_OUT, this is the legacy fallback in the same classifier)
            inner = data.get("message") if isinstance(data.get("message"), dict) else data
            role = (inner or {}).get("role") if isinstance(inner, dict) else None
            if role in ("user", "assistant"):
                return "message", "today_messages"
        if et in _CRON or et.startswith("cron."):
            return "cron", "today_crons"
        if et in _HEARTBEAT or et.startswith("heartbeat"):
            return "heartbeat", "today_heartbeats"
        return None, None

    def _is_error_row(et: str, data: dict) -> bool:
        if et.endswith(".error") or et.endswith(".failed"):
            return True
        if not isinstance(data, dict):
            return False
        for k in ("errorCode", "error", "is_error"):
            v = data.get(k)
            if v not in (None, False, "", 0):
                return True
        return False

    def _extract_channel(data: dict) -> str:
        """Pull a channel hint mirroring the legacy parser's ``from`` slot."""
        if not isinstance(data, dict):
            return ""
        for key in ("channel", "messageChannel", "provider", "origin"):
            v = data.get(key)
            if isinstance(v, str) and v:
                return v
        return ""

    def _extract_model(data: dict) -> str:
        if not isinstance(data, dict):
            return ""
        for key in ("model", "modelId"):
            v = data.get(key)
            if isinstance(v, str) and v:
                return v
        inner = data.get("message") if isinstance(data.get("message"), dict) else None
        if isinstance(inner, dict):
            v = inner.get("model")
            if isinstance(v, str) and v:
                return v
        return ""

    routes_out: list = []
    stats = {
        "today_messages":   0,
        "today_heartbeats": 0,
        "today_crons":      0,
        "today_errors":     0,
    }

    for r in rows:
        ts = r.get("ts") or ""
        if not ts.startswith(today):
            continue
        et = (r.get("event_type") or "").strip()
        data = r.get("data") if isinstance(r.get("data"), dict) else {}
        rtype, bucket = _classify(et, data)
        if rtype is None:
            continue
        sid = (r.get("session_id") or "")[:12]
        is_err = _is_error_row(et, data)
        if is_err:
            stats["today_errors"] += 1
        if bucket:
            stats[bucket] = stats.get(bucket, 0) + 1
        # Subagent annotation matches the legacy parser's heuristic.
        if "subagent" in sid.lower() or "subagent" in (r.get("agent_id") or "").lower():
            rtype = "subagent"
        routes_out.append({
            "timestamp": ts,
            "from":      _extract_channel(data),
            "to":        _extract_model(data),
            "session":   sid,
            "type":      rtype,
            "status":    "error" if is_err else "ok",
        })

    # If the store HAS rows but NONE were gateway-shape, defer so the
    # legacy parser handles the gateway.log surface (non-OpenClaw agents
    # whose events live in DuckDB without touching the gateway flow).
    if not routes_out:
        return None

    routes_out.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
    total = len(routes_out)
    page = routes_out[offset: offset + limit]

    # --- Side-channel snapshot fields (live OS state — exempt from
    # DuckDB-first per feedback_duckdb_first_rule.md). Best-effort; any
    # failure leaves the field empty so the panel still renders.

    import dashboard as _d
    active_sessions = 0
    try:
        sess_file = os.path.join(
            _d.SESSIONS_DIR or os.path.expanduser("~/.openclaw/agents/main/sessions"),
            "sessions.json",
        )
        with open(sess_file) as f:
            sess_data = json.load(f)
        now_ts = time.time() * 1000
        for sid, sinfo in sess_data.items():
            updated = sinfo.get("updatedAt", 0)
            if now_ts - updated < 3600_000:
                active_sessions += 1
    except Exception:
        pass

    config_summary: dict = {}
    for cf in (
        os.path.expanduser("~/.clawdbot/openclaw.json"),
        os.path.expanduser("~/.openclaw/openclaw.json"),
    ):
        try:
            with open(cf) as f:
                cfg = json.load(f)
            plugins = cfg.get("plugins", {}).get("entries", {})
            config_summary["channels"] = [k for k, v in plugins.items() if v.get("enabled")]
            ad = cfg.get("agents", {}).get("defaults", {})
            config_summary["max_concurrent"] = ad.get("maxConcurrent", "?")
            config_summary["max_subagents"] = ad.get("subagents", {}).get("maxConcurrent", "?")
            config_summary["heartbeat"] = ad.get("heartbeat", {}).get("every", "?")
            config_summary["workspace"] = ad.get("workspace", "?")
            break
        except Exception:
            continue

    stats["active_sessions"] = active_sessions
    stats["config"]          = config_summary
    stats["uptime"]          = ""       # filled by legacy path; snapshot-only here
    stats["restarts"]        = []       # ditto

    return {
        "routes":  page,
        "stats":   stats,
        "total":   total,
        "_source": "local_store",
    }


@bp_components.route("/api/component/gateway")
def api_component_gateway():
    """Parse gateway routing events from today's log file.

    Supports two on-disk formats:
      1. Legacy per-day JSONL: openclaw-YYYY-MM-DD.log / moltbot-YYYY-MM-DD.log
      2. Current rolling plain-text: gateway.log (OpenClaw 2026.4+)
         Format: "ISO-TS [tag] message", e.g.
           2026-04-15T09:36:55.977+02:00 [ws] ⇄ res ✗ cron.list 0ms errorCode=...

    Tier-1 DuckDB fast path (refs #1565): when
    ``CLAWMETRY_LOCAL_STORE_READ=1`` and the daemon-ingested ``events``
    table holds rows that map to a gateway-flow lane, serve the panel
    from DuckDB instead of re-parsing today's gateway.log. Falls through
    to the legacy parser on empty store / unreachable daemon / any
    error — never crashes the panel.
    """
    import dashboard as _d
    import re

    limit = int(request.args.get("limit", 50))
    offset = int(request.args.get("offset", 0))

    if is_local_store_read_enabled():
        try:
            fast = _try_local_store_component_gateway(limit, offset)
        except Exception:
            fast = None
        if fast is not None:
            return jsonify(fast)
    today = datetime.now().strftime("%Y-%m-%d")
    log_dirs = [d for d in [_d.LOG_DIR, *_d._get_log_dirs()] if d]
    log_dirs = list(dict.fromkeys(log_dirs))
    candidates = []
    for d in log_dirs:
        candidates.extend([
            os.path.join(d, f"openclaw-{today}.log"),
            os.path.join(d, f"moltbot-{today}.log"),
            os.path.join(d, "gateway.log"),  # OpenClaw 2026.4+ rolling log
        ])
    candidates = list(dict.fromkeys(candidates))  # deduplicate preserving order
    log_path = next((p for p in candidates if os.path.exists(p)), None)

    routes = []
    stats = {
        "today_messages": 0,
        "today_heartbeats": 0,
        "today_crons": 0,
        "today_errors": 0,
    }

    if not log_path:
        return jsonify({"routes": [], "stats": stats, "total": 0})

    is_plaintext = os.path.basename(log_path) == "gateway.log"

    def _parse_plaintext_line(line):
        """Parse one '[TS] [tag] message' line from gateway.log.

        Returns (route_dict, hit_category) or (None, None).
        """
        m = re.match(
            r"^(\d{4}-\d{2}-\d{2}T[\d:.+\-]+)\s+\[([^\]]+)\]\s+(.*)$",
            line,
        )
        if not m:
            return None, None
        ts, tag, body = m.group(1), m.group(2), m.group(3)
        if not ts.startswith(today):
            return None, None
        # Default route shape
        route = {
            "timestamp": ts,
            "from": tag,
            "to": "",
            "session": "",
            "type": "message",
            "status": "ok",
        }
        # Errors first (any line carrying errorCode or "res ✗")
        if "errorCode=" in body or "res ✗" in body:
            route["status"] = "error"
            m_meth = re.search(r"res\s+✗\s+(\S+)", body)
            if m_meth:
                route["to"] = m_meth.group(1)
            return route, "today_errors"
        # ws successful RPC
        if tag == "ws":
            m_meth = re.search(r"res\s+✓\s+(\S+)", body)
            if m_meth:
                route["to"] = m_meth.group(1)
                meth = m_meth.group(1)
                if meth.startswith("cron."):
                    route["type"] = "cron"
                    return route, "today_crons"
                if "heartbeat" in meth.lower():
                    route["type"] = "heartbeat"
                    return route, "today_heartbeats"
                return route, "today_messages"
            # Connection events still count as a message
            if "connected" in body or "disconnected" in body:
                return route, "today_messages"
            return None, None
        if tag == "heartbeat":
            route["type"] = "heartbeat"
            return route, "today_heartbeats"
        if tag in ("cron", "crons"):
            route["type"] = "cron"
            return route, "today_crons"
        # Fall through: count miscellaneous tags as messages so the panel isn't
        # silent when unfamiliar log lines appear.
        return route, "today_messages"

    try:
        with open(log_path, "r") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                # Plain-text branch for OpenClaw 2026.4+ rolling gateway.log
                if is_plaintext:
                    route, cat = _parse_plaintext_line(line)
                    if route is not None:
                        if cat:
                            stats[cat] = stats.get(cat, 0) + 1
                        routes.append(route)
                    continue
                try:
                    entry = json.loads(line)
                except json.JSONDecodeError:
                    continue

                msg = entry.get("1", "") or entry.get("0", "")
                ts = entry.get("time", "")
                level = entry.get("_meta", {}).get("logLevelName", "")

                # embedded run start - main routing event
                if "embedded run start:" in msg:
                    route = {
                        "timestamp": ts,
                        "from": "",
                        "to": "",
                        "session": "",
                        "type": "message",
                        "status": "ok",
                    }
                    # Extract fields: model, messageChannel, sessionId
                    m_model = re.search(r"model=(\S+)", msg)
                    m_chan = re.search(r"messageChannel=(\S+)", msg)
                    m_sid = re.search(r"sessionId=(\S+)", msg)
                    if m_model:
                        route["to"] = m_model.group(1)
                    if m_chan:
                        ch = m_chan.group(1)
                        route["from"] = ch
                        if ch == "heartbeat":
                            route["type"] = "heartbeat"
                            stats["today_heartbeats"] += 1
                            # Update heartbeat tracking for gap alerting
                            _d._record_heartbeat()
                        elif ch == "cron":
                            route["type"] = "cron"
                            stats["today_crons"] += 1
                        else:
                            stats["today_messages"] += 1
                    else:
                        stats["today_messages"] += 1
                    if m_sid:
                        route["session"] = m_sid.group(1)[:12]
                    # Check if it's a subagent
                    if "subagent" in msg.lower():
                        route["type"] = "subagent"
                    routes.append(route)
                    continue

                # Delivery failures
                if "Delivery failed" in msg or ("Delivery" in msg and level == "ERROR"):
                    stats["today_errors"] += 1
                    # Try to annotate the last route
                    route = {
                        "timestamp": ts,
                        "from": "",
                        "to": "",
                        "session": "",
                        "type": "message",
                        "status": "error",
                    }
                    m_chan = re.search(r"\((\w+) to", msg)
                    if m_chan:
                        route["from"] = m_chan.group(1)
                    route["to"] = "delivery"
                    routes.append(route)
                    continue

                pass  # Only count delivery errors for routing stats

    except Exception:
        pass

    # Sort by timestamp descending (newest first)
    routes.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
    total = len(routes)
    page = routes[offset : offset + limit]

    # --- Enhanced: active sessions, config summary, uptime, restart history ---

    # Active sessions
    active_sessions = 0
    try:
        sess_file = os.path.join(
            _d.SESSIONS_DIR or os.path.expanduser("~/.openclaw/agents/main/sessions"),
            "sessions.json",
        )
        with open(sess_file) as f:
            sess_data = json.load(f)
        now_ts = time.time() * 1000  # ms
        for sid, sinfo in sess_data.items():
            updated = sinfo.get("updatedAt", 0)
            if now_ts - updated < 3600_000:  # active in last hour
                active_sessions += 1
    except Exception:
        pass

    # Config summary
    config_summary = {}
    for cf in [
        os.path.expanduser("~/.clawdbot/openclaw.json"),
        os.path.expanduser("~/.openclaw/openclaw.json"),
    ]:
        try:
            with open(cf) as f:
                cfg = json.load(f)
            plugins = cfg.get("plugins", {}).get("entries", {})
            config_summary["channels"] = [
                k for k, v in plugins.items() if v.get("enabled")
            ]
            ad = cfg.get("agents", {}).get("defaults", {})
            config_summary["max_concurrent"] = ad.get("maxConcurrent", "?")
            config_summary["max_subagents"] = ad.get("subagents", {}).get(
                "maxConcurrent", "?"
            )
            hb = ad.get("heartbeat", {})
            config_summary["heartbeat"] = hb.get("every", "?")
            config_summary["workspace"] = ad.get("workspace", "?")
            break
        except Exception:
            continue

    # Gateway uptime (from systemd)
    uptime_str = ""
    try:
        r = subprocess.run(
            [
                "systemctl",
                "--user",
                "show",
                "openclaw-gateway",
                "--property=ActiveEnterTimestamp",
            ],
            capture_output=True,
            text=True,
            timeout=3,
        )
        ts_line = r.stdout.strip()
        if "=" in ts_line:
            uptime_str = ts_line.split("=", 1)[1].strip()
    except Exception:
        pass
    if not uptime_str and sys.platform != "win32":
        try:
            r = subprocess.run(
                ["pgrep", "-a", "openclaw"], capture_output=True, text=True, timeout=3
            )
            if r.stdout.strip():
                pid = r.stdout.strip().split()[0]
                r2 = subprocess.run(
                    ["ps", "-o", "etime=", "-p", pid],
                    capture_output=True,
                    text=True,
                    timeout=3,
                )
                uptime_str = r2.stdout.strip()
        except Exception:
            pass

    # Restart history from log (look for "gateway start" or "listening" entries)
    restarts = []
    if log_path:
        try:
            _restart_lines = _d._grep_log_file(
                log_path, r"gateway.*start|listening on|server started"
            )
            for line in _restart_lines[-5:]:  # last 5 restarts
                try:
                    obj = json.loads(line.strip())
                    restarts.append(obj.get("time", ""))
                except Exception:
                    pass
        except Exception:
            pass

    stats["active_sessions"] = active_sessions
    stats["config"] = config_summary
    stats["uptime"] = uptime_str
    stats["restarts"] = restarts

    return jsonify({"routes": page, "stats": stats, "total": total})


def _try_local_store_component_brain(limit: int, offset: int):
    """Tier-1 DuckDB fast path for /api/component/brain.

    Reads ``message`` events from the local store (assistant turns carry
    LLM usage), filters to today, and shapes them into the same
    ``{stats, calls, total}`` payload the legacy JSONL parser returns.

    Returns ``None`` to defer to the legacy fallback if:
      - the ``local_store`` module isn't importable
      - the events table is empty / no qualifying calls today
      - any unexpected error happens (we'd rather degrade than 500)
    """
    # Issue #1256: route through daemon HTTP proxy. Direct get_store()
    # raises IOException on multi-process installs (DuckDB's file lock is
    # exclusive across processes; read_only=True doesn't bypass it).
    try:
        from routes.local_query import local_store_via_daemon
        rows = local_store_via_daemon("query_events", event_type="message", limit=2000)
        if rows is None:
            # Daemon unreachable → single-process fallback (tests/dev mode).
            from clawmetry import local_store
            store = local_store.get_store(read_only=True)
            rows = store.query_events(event_type="message", limit=2000)
    except Exception:
        return None
    if not rows:
        return None

    today = datetime.now().strftime("%Y-%m-%d")
    calls = []
    total_input = 0
    total_output = 0
    total_cache_read = 0
    total_cache_write = 0
    total_cost = 0.0
    durations = []
    models_seen = set()

    for r in rows:
        ts = (r.get("ts") or "")
        if not ts.startswith(today):
            continue
        data = r.get("data") if isinstance(r, dict) else None
        if not isinstance(data, dict):
            continue
        msg = data.get("message") if isinstance(data.get("message"), dict) else data
        if not isinstance(msg, dict):
            continue
        if msg.get("role") and msg.get("role") != "assistant":
            continue
        usage = msg.get("usage")
        if not isinstance(usage, dict):
            continue

        model = msg.get("model") or r.get("model") or "unknown"
        models_seen.add(model)
        tokens_in = (usage.get("input", 0) + usage.get("cacheRead", 0)
                     + usage.get("cacheWrite", 0))
        tokens_out = usage.get("output", 0)
        cache_read = usage.get("cacheRead", 0)
        cache_write = usage.get("cacheWrite", 0)
        cost_data = usage.get("cost", {})
        call_cost = (float(cost_data.get("total", 0))
                     if isinstance(cost_data, dict) else 0.0)
        if call_cost == 0 and r.get("cost_usd"):
            try:
                call_cost = float(r["cost_usd"])
            except Exception:
                pass

        has_thinking = False
        tools_used = []
        for c in msg.get("content") or []:
            if isinstance(c, dict):
                if c.get("type") == "thinking":
                    has_thinking = True
                elif c.get("type") == "toolCall":
                    tn = c.get("name", "")
                    if tn and tn not in tools_used:
                        tools_used.append(tn)

        total_input += usage.get("input", 0)
        total_output += tokens_out
        total_cache_read += cache_read
        total_cache_write += cache_write
        total_cost += call_cost

        sid = r.get("session_id") or ""
        session_label = "subagent:" + sid[:8] if "subagent" in sid.lower() else "main"

        calls.append({
            "timestamp":   ts,
            "model":       model,
            "tokens_in":   tokens_in,
            "tokens_out":  tokens_out,
            "cache_read":  cache_read,
            "cache_write": cache_write,
            "thinking":    has_thinking,
            "cost":        "${:.4f}".format(call_cost),
            "cost_raw":    call_cost,
            "tools_used":  tools_used,
            "duration_ms": 0,
            "session":     session_label,
            "stop_reason": msg.get("stopReason", ""),
        })

    if not calls:
        return None

    calls.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
    total = len(calls)
    avg_ms = int(sum(durations) / len(durations)) if durations else 0
    primary_model = (
        max(models_seen, key=lambda m: sum(1 for c in calls if c["model"] == m))
        if models_seen else "unknown"
    )
    thinking_count = sum(1 for c in calls if c.get("thinking"))
    cache_hit_count = sum(1 for c in calls if c.get("cache_read", 0) > 0)

    return {
        "stats": {
            "today_calls":     total,
            "today_tokens":    {
                "input":       total_input,
                "output":      total_output,
                "cache_read":  total_cache_read,
                "cache_write": total_cache_write,
            },
            "today_cost":      "${:.2f}".format(total_cost),
            "model":           primary_model,
            "avg_response_ms": avg_ms,
            "thinking_calls":  thinking_count,
            "cache_hits":      cache_hit_count,
        },
        "calls":   calls[offset: offset + limit],
        "total":   total,
        "_source": "local_store",
    }


@bp_components.route("/api/component/brain")
def api_component_brain():
    """Parse session transcripts for LLM API call details."""
    import dashboard as _d

    limit = int(request.args.get("limit", 50))
    offset = int(request.args.get("offset", 0))

    # Tier-1 DuckDB fast path — opt-in via CLAWMETRY_LOCAL_STORE_READ=1.
    # Falls through to legacy JSONL parser when flag is unset, store is
    # empty, or no qualifying assistant turns are present.
    if is_local_store_read_enabled():
        fast = _try_local_store_component_brain(limit, offset)
        if fast is not None:
            return jsonify(fast)

    sessions_dir = _d.SESSIONS_DIR or os.path.expanduser(
        "~/.openclaw/agents/main/sessions"
    )
    if not os.path.isdir(sessions_dir):
        sessions_dir = os.path.expanduser("~/.moltbot/agents/main/sessions")

    today = datetime.now().strftime("%Y-%m-%d")
    calls = []
    total_input = 0
    total_output = 0
    total_cache_read = 0
    total_cost = 0.0
    durations = []
    models_seen = set()

    if os.path.isdir(sessions_dir):
        for fname in os.listdir(sessions_dir):
            if not fname.endswith(".jsonl"):
                continue
            fpath = os.path.join(sessions_dir, fname)
            session_id = fname.replace(".jsonl", "")

            try:
                # Quick check: only process files modified today
                mtime = os.path.getmtime(fpath)
                file_date = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d")
                if file_date != today:
                    continue

                # Detect if subagent from session metadata
                session_label = "main"
                prev_ts = None
                with open(fpath, "r") as f:
                    for line in f:
                        try:
                            obj = json.loads(line.strip())
                        except json.JSONDecodeError:
                            continue

                        # Check session header for subagent hints
                        if obj.get("type") == "session":
                            continue
                        if (
                            obj.get("type") == "custom"
                            and obj.get("customType") == "openclaw.session-info"
                        ):
                            data = obj.get("data", {})
                            if "subagent" in str(data.get("session", "")):
                                session_label = "subagent:" + session_id[:8]

                        if obj.get("type") != "message":
                            # Track user message timestamps for duration calc
                            if obj.get("type") == "message" or (  # v3-shape-gate: allow (reason: JSONL on-disk walker; iterates per-line obj from .jsonl file)
                                isinstance(obj.get("message"), dict)
                                and obj["message"].get("role") == "user"
                            ):
                                pass
                            continue

                        msg = obj.get("message", {})
                        usage = msg.get("usage")
                        if not usage or not isinstance(usage, dict):
                            # Track user message time for duration
                            if msg.get("role") == "user":
                                prev_ts = obj.get("timestamp")
                            continue

                        if msg.get("role") != "assistant":
                            continue

                        ts = obj.get("timestamp", "")
                        if not ts:
                            continue

                        # Only include today's entries
                        if not ts.startswith(today):
                            prev_ts = None
                            continue

                        model = msg.get("model", "unknown") or "unknown"
                        models_seen.add(model)

                        tokens_in = (
                            usage.get("input", 0)
                            + usage.get("cacheRead", 0)
                            + usage.get("cacheWrite", 0)
                        )
                        tokens_out = usage.get("output", 0)
                        cache_read = usage.get("cacheRead", 0)
                        cost_data = usage.get("cost", {})
                        call_cost = (
                            float(cost_data.get("total", 0))
                            if isinstance(cost_data, dict)
                            else 0.0
                        )
                        # Fallback: if OpenClaw recorded $0 for this turn but
                        # tokens are non-zero (model not in OpenClaw's pricing
                        # table, e.g. @oi/beta or local providers), estimate
                        # from clawmetry's per-provider pricing so the panel
                        # doesn't lie that the call was free.
                        if call_cost == 0 and (tokens_in + tokens_out) > 0:
                            try:
                                from clawmetry.providers_pricing import estimate_cost_usd
                                provider = (msg.get("provider")
                                            or _d._provider_from_model(model)
                                            or "anthropic")
                                est = estimate_cost_usd(
                                    provider, tokens_in, tokens_out, model
                                )
                                if est > 0:
                                    call_cost = est
                            except Exception:
                                pass

                        total_input += usage.get("input", 0)
                        total_output += tokens_out
                        total_cache_read += cache_read
                        total_cost += call_cost

                        # Detect thinking blocks
                        has_thinking = False
                        for c in msg.get("content") or []:
                            if isinstance(c, dict) and c.get("type") == "thinking":
                                has_thinking = True
                                break

                        # Extract tools used
                        tools = []
                        for c in msg.get("content") or []:
                            if isinstance(c, dict) and c.get("type") == "toolCall":
                                tool_name = c.get("name", "")
                                if tool_name and tool_name not in tools:
                                    tools.append(tool_name)

                        # Compute duration from previous user message
                        duration_ms = 0
                        if prev_ts:
                            try:
                                t1 = datetime.fromisoformat(
                                    prev_ts.replace("Z", "+00:00")
                                )
                                t2 = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                                duration_ms = int((t2 - t1).total_seconds() * 1000)
                                if 0 < duration_ms < 300000:  # sanity: < 5 min
                                    durations.append(duration_ms)
                            except Exception:
                                pass

                        # Detect subagent from content context
                        if session_label == "main":
                            for c in msg.get("content") or []:
                                if isinstance(c, dict) and c.get("type") == "text":
                                    text = c.get("text", "")[:200]
                                    if "subagent" in text.lower():
                                        session_label = "subagent:" + session_id[:8]
                                        break

                        calls.append(
                            {
                                "timestamp": ts,
                                "model": model,
                                "tokens_in": tokens_in,
                                "tokens_out": tokens_out,
                                "cache_read": cache_read,
                                "cache_write": usage.get("cacheWrite", 0),
                                "thinking": has_thinking,
                                "cost": "${:.4f}".format(call_cost),
                                "cost_raw": call_cost,
                                "tools_used": tools,
                                "duration_ms": duration_ms,
                                "session": session_label,
                                "stop_reason": msg.get("stopReason", ""),
                            }
                        )

                        prev_ts = ts

            except Exception:
                continue

    # Sort by timestamp descending
    calls.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
    total = len(calls)
    avg_ms = int(sum(durations) / len(durations)) if durations else 0
    primary_model = (
        max(models_seen, key=lambda m: sum(1 for c in calls if c["model"] == m))
        if models_seen
        else "unknown"
    )
    thinking_count = sum(1 for c in calls if c.get("thinking"))
    cache_hit_count = sum(1 for c in calls if c.get("cache_read", 0) > 0)
    total_cache_write = sum(c.get("cache_write", 0) for c in calls)

    result = {
        "stats": {
            "today_calls": total,
            "today_tokens": {
                "input": total_input,
                "output": total_output,
                "cache_read": total_cache_read,
                "cache_write": total_cache_write,
            },
            "today_cost": "${:.2f}".format(total_cost),
            "model": primary_model,
            "avg_response_ms": avg_ms,
            "thinking_calls": thinking_count,
            "cache_hits": cache_hit_count,
        },
        "calls": calls[offset : offset + limit],
        "total": total,
    }
    return jsonify(result)


def _try_local_store_component_mcp():
    """DuckDB fast path for /api/component/mcp.

    Walks the same event shapes as _try_local_store_component_tool, extracts
    every tool call whose name matches ``mcp__<server>__<tool>``, and groups
    them by server: call count, error count, error_rate, top-5 tools, last_seen.

    Returns None on any unexpected failure so the caller can surface an empty
    response rather than 500-ing.
    """
    from collections import defaultdict

    _HOST_EVENT_TYPES = (
        "message",
        "assistant",
        "model.completed",
        "subagent:assistant",
    )
    rows: list = []
    try:
        from routes.local_query import local_store_via_daemon
        for et in _HOST_EVENT_TYPES:
            try:
                got = local_store_via_daemon("query_events", event_type=et, limit=2000)
                if got:
                    rows.extend(got)
            except Exception:
                continue
    except Exception:
        pass

    if not rows:
        try:
            from clawmetry import local_store
            store = local_store.get_store(read_only=True)
            for et in _HOST_EVENT_TYPES:
                try:
                    rows.extend(store.query_events(event_type=et, limit=2000))
                except Exception:
                    continue
        except Exception:
            pass

    server_calls: dict = defaultdict(int)
    server_errors: dict = defaultdict(int)
    server_tools: dict = defaultdict(lambda: defaultdict(int))
    server_tool_errors: dict = defaultdict(lambda: defaultdict(int))
    server_last_seen: dict = {}

    for r in rows:
        ts = r.get("ts") or ""
        for tool_name, _args, status in _iter_tool_call_blocks(r):
            server = _mcp_server_from_tool_name(tool_name)
            if server is None:
                continue
            bare_tool = tool_name.split("__", 2)[2] if tool_name.count("__") >= 2 else tool_name
            server_calls[server] += 1
            server_tools[server][bare_tool] += 1
            if status == "error":
                server_errors[server] += 1
                server_tool_errors[server][bare_tool] += 1
            if ts and (server not in server_last_seen or ts > server_last_seen[server]):
                server_last_seen[server] = ts

    servers = []
    for server in sorted(server_calls.keys()):
        calls = server_calls[server]
        errors = server_errors[server]
        tools_sorted = sorted(
            server_tools[server].items(), key=lambda x: x[1], reverse=True
        )
        top_tools = [
            {
                "tool": tool,
                "calls": cnt,
                "errors": server_tool_errors[server].get(tool, 0),
            }
            for tool, cnt in tools_sorted[:5]
        ]
        servers.append({
            "server": server,
            "calls": calls,
            "errors": errors,
            "error_rate": round(errors / calls, 3) if calls else 0.0,
            "top_tools": top_tools,
            "last_seen": server_last_seen.get(server, ""),
        })
    servers.sort(key=lambda s: s["calls"], reverse=True)

    return {
        "servers": servers,
        "total_calls": sum(server_calls.values()),
        "total_errors": sum(server_errors.values()),
        "_source": "local_store",
    }


@bp_components.route("/api/component/mcp")
def api_component_mcp():
    """Aggregate MCP server usage across all recorded events. Cached 15s."""
    global _api_mcp_cache_time
    now = time.time()
    if _api_mcp_cache and (now - _api_mcp_cache_time) < 15:
        return jsonify(_api_mcp_cache)

    if is_local_store_read_enabled():
        try:
            result = _try_local_store_component_mcp()
            if result is not None:
                _api_mcp_cache.clear()
                _api_mcp_cache.update(result)
                _api_mcp_cache_time = now
                return jsonify(result)
        except Exception:
            pass

    return jsonify({
        "servers": [],
        "total_calls": 0,
        "total_errors": 0,
        "_source": "unavailable",
    })
