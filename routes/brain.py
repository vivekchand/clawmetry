"""
routes/brain.py — Brain event feed endpoints.

Extracted from dashboard.py as Phase 5.2 of the incremental modularisation.
Owns the two routes that power the Brain tab:

  GET  /api/brain-history   — unified JSONL + log scan, returns list
  GET  /api/brain-stream    — SSE tail of the same sources

Module-level helpers (``SESSIONS_DIR``, ``SSE_MAX_SECONDS``,
``_get_log_dirs``, ``_tail_lines``, ``_acquire_stream_slot``,
``_release_stream_slot``, ``_ext_emit``) stay in ``dashboard.py`` and are
reached via late ``import dashboard as _d``. Pure mechanical move — zero
behaviour change.
"""

import glob
import json
import os
import time

from flask import Blueprint, Response, jsonify

bp_brain = Blueprint('brain', __name__)


@bp_brain.route("/api/brain-history")
def api_brain_history():
    import dashboard as _d
    # Return unified event stream - v2 no truncation
    events = []

    # Build sessionId to displayName + channel map
    session_dir = _d.SESSIONS_DIR or os.path.expanduser("~/.openclaw/agents/main/sessions")
    index_path = os.path.join(session_dir, "sessions.json")
    sid_to_label = {}
    sid_to_channel = {}  # sessionId → {channel, chatType, subject}
    try:
        with open(index_path, "r") as f:
            index = json.load(f)
        for key, meta in index.items():
            sid = meta.get("sessionId", "")
            label = meta.get("displayName") or meta.get("label") or ""
            if sid and label:
                sid_to_label[sid] = label
            if sid:
                # Parse channel from session key: agent:<id>:<channel>:group|channel:<chatId>
                # or from metadata fields
                channel = meta.get("provider", "")
                chat_type = meta.get("chatType", "")
                subject = meta.get("subject") or meta.get("displayName") or ""
                if not channel:
                    # Parse from key: agent:main:telegram:group:-100...
                    parts = key.split(":")
                    if len(parts) >= 3 and parts[2] not in ("main", "subagent"):
                        channel = parts[2]
                    elif len(parts) == 3 and parts[2] == "main":
                        channel = "cli"
                if channel:
                    sid_to_channel[sid] = {"channel": channel, "chatType": chat_type, "subject": subject}
    except Exception:
        pass

    # Color assignment
    color_palette = [
        "#06b6d4",
        "#f59e0b",
        "#ec4899",
        "#8b5cf6",
        "#10b981",
        "#f97316",
        "#6366f1",
    ]
    agent_colors = {}
    color_idx = [0]

    def get_agent_color(source):
        if source == "main":
            return "#a855f7"
        if source not in agent_colors:
            agent_colors[source] = color_palette[color_idx[0] % len(color_palette)]
            color_idx[0] += 1
        return agent_colors[source]

    # Tool name to event type
    def tool_to_type(tn):
        tn = tn.lower()
        if tn == "exec" or "shell" in tn or "bash" in tn or tn == "process":
            return "EXEC"
        if "read" in tn:
            return "READ"
        if "write" in tn or "edit" in tn:
            return "WRITE"
        if "browser" in tn or "canvas" in tn or "image" in tn:
            return "BROWSER"
        if tn == "message" or "tts" in tn:
            return "MSG"
        if "web_search" in tn or "web_fetch" in tn or "search" in tn:
            return "SEARCH"
        if "subagent" in tn or "spawn" in tn:
            return "SPAWN"
        return "TOOL"

    # Extract FULL detail from tool input - no truncation
    def extract_detail(tn, inp):
        tn = tn.lower()
        if not isinstance(inp, dict):
            return str(inp)
        if tn == "exec" or "shell" in tn or "bash" in tn or tn == "process":
            return inp.get("command") or inp.get("action") or ""
        if "read" in tn:
            return inp.get("path") or inp.get("file_path") or ""
        if "write" in tn or "edit" in tn:
            return inp.get("path") or inp.get("file_path") or ""
        if "browser" in tn:
            return inp.get("url") or inp.get("targetUrl") or inp.get("action") or ""
        if tn == "message":
            return inp.get("message") or inp.get("target") or ""
        if "search" in tn or "fetch" in tn:
            return inp.get("query") or inp.get("url") or ""
        if "subagent" in tn or "spawn" in tn:
            return inp.get("label") or str(inp.get("message", ""))
        vals = list(inp.values())
        return str(vals[0]) if vals else ""

    # Source 1: OpenClaw log files (main agent)
    import re as _re

    log_tool_re = _re.compile(r"^\[(\w+)\]\s*(.*)", _re.DOTALL)

    log_dirs = _d._get_log_dirs()
    log_files = []
    for d in log_dirs:
        log_files += sorted(glob.glob(os.path.join(d, "openclaw-*.log")))
    log_files += sorted(glob.glob("/tmp/openclaw/openclaw-*.log"))
    log_files = list(dict.fromkeys(log_files))

    for lf in log_files[-3:]:
        try:
            lines = _d._tail_lines(lf, 2000)
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except Exception:
                    continue
                ts = obj.get("time") or obj.get("timestamp")
                if not ts:
                    continue
                msg = obj.get("0") or obj.get("message") or ""
                if isinstance(msg, dict):
                    msg = json.dumps(msg)
                m = log_tool_re.match(msg.strip())
                if m:
                    tool_kw = m.group(1).lower()
                    rest = m.group(2).strip()
                    ev_type = tool_to_type(tool_kw)
                    detail = rest.split("\n")[0]
                    events.append(
                        {
                            "time": ts,
                            "source": "main",
                            "sourceLabel": "main",
                            "type": ev_type,
                            "detail": detail,
                            "color": "#a855f7",
                        }
                    )
                else:
                    msg_lower = msg.lower()
                    for kw in (
                        "exec",
                        "browser",
                        "web_search",
                        "web_fetch",
                        "read",
                        "write",
                        "edit",
                        "message",
                        "spawn",
                        "subagents",
                        "tts",
                        "nodes",
                        "canvas",
                    ):
                        if kw in msg_lower:
                            ev_type = tool_to_type(kw)
                            try:
                                start = msg_lower.index(kw)
                                detail = msg[start : start + 300].split("\n")[0].strip()
                            except Exception:
                                detail = ""
                            events.append(
                                {
                                    "time": ts,
                                    "source": "main",
                                    "sourceLabel": "main",
                                    "type": ev_type,
                                    "detail": detail,
                                    "color": "#a855f7",
                                }
                            )
                            break
        except Exception:
            pass

    # Source 2: Session JSONL files (sub-agent activity)
    session_files = sorted(glob.glob(os.path.join(session_dir, "*.jsonl")))

    for sf in session_files:
        try:
            fname = os.path.basename(sf).replace(".jsonl", "")
            label = sid_to_label.get(fname, "")
            source_id = fname
            ch_info = sid_to_channel.get(fname, {})
            import re as _re

            source_label = (
                label
                if label
                else (
                    "agent:" + fname[:8]
                    if _re.match(r"[0-9a-f-]{36}", fname)
                    else fname
                )
            )
            color = get_agent_color(source_id)

            with open(sf, "r", errors="replace") as fh:
                all_lines = fh.readlines()
                raw_lines = (
                    all_lines[:20] + all_lines[-600:]
                )  # first 20 (system context) + last 600

            for raw in raw_lines:
                raw = raw.strip()
                if not raw:
                    continue
                try:
                    obj = json.loads(raw)
                except Exception:
                    continue
                ts = obj.get("timestamp") or obj.get("time")
                role = obj.get("role", "")
                content_obj = obj.get("content", "")

                if obj.get("type") == "message":
                    inner = obj.get("message", {})
                    role = inner.get("role", "")
                    content_obj = inner.get("content", [])

                # System context (injected files, workspace context)
                if role == "system" and ts:
                    text = ""
                    if isinstance(content_obj, str):
                        text = content_obj
                    elif isinstance(content_obj, list):
                        parts = [
                            b.get("text", "")
                            for b in content_obj
                            if isinstance(b, dict) and b.get("type") == "text"
                        ]
                        text = " ".join(parts)
                    if text:
                        # Extract file references from system context
                        import re as _re2

                        file_refs = _re2.findall(r"## (/[^ ]+\.md)", text)
                        detail = (
                            "Context loaded: " + ", ".join(file_refs)
                            if file_refs
                            else text[:300]
                        )
                        events.append(
                            {
                                "time": ts,
                                "source": source_id,
                                "sourceLabel": source_label,
                                "type": "CONTEXT",
                                "detail": detail,
                                "color": color,
                            }
                        )

                # Tool results
                if role == "tool" and ts:
                    tool_id = obj.get("tool_use_id", "") or (
                        isinstance(content_obj, list)
                        and content_obj[0].get("tool_use_id", "")
                        if isinstance(content_obj, list) and content_obj
                        else ""
                    )
                    text = ""
                    if isinstance(content_obj, str):
                        text = content_obj
                    elif isinstance(content_obj, list):
                        parts = [
                            b.get("text", "")
                            for b in content_obj
                            if isinstance(b, dict) and b.get("type") == "text"
                        ]
                        text = " ".join(parts)
                    if text:
                        events.append(
                            {
                                "time": ts,
                                "source": source_id,
                                "sourceLabel": source_label,
                                "type": "RESULT",
                                "detail": text[:300],
                                "color": color,
                            }
                        )

                # User prompt
                if role == "user" and ts:
                    text = ""
                    if isinstance(content_obj, str):
                        text = content_obj
                    elif isinstance(content_obj, list):
                        parts = [
                            b.get("text", "")
                            for b in content_obj
                            if isinstance(b, dict) and b.get("type") == "text"
                        ]
                        text = " ".join(parts)
                    if text:
                        events.append(
                            {
                                "time": ts,
                                "source": source_id,
                                "sourceLabel": source_label,
                                "type": "USER",
                                "detail": text[:300],
                                "color": color,
                            }
                        )

                if role == "assistant" and isinstance(content_obj, list):
                    for block in content_obj:
                        if not isinstance(block, dict):
                            continue
                        btype = block.get("type", "")

                        # Thinking / reasoning block
                        if btype == "thinking" and ts:
                            thinking_text = block.get("thinking", "")
                            if thinking_text:
                                events.append(
                                    {
                                        "time": ts,
                                        "source": source_id,
                                        "sourceLabel": source_label,
                                        "type": "THINK",
                                        "detail": thinking_text[:300],
                                        "color": color,
                                    }
                                )
                            continue

                        # Assistant text block
                        if btype == "text" and ts:
                            text = block.get("text", "")
                            if text:
                                events.append(
                                    {
                                        "time": ts,
                                        "source": source_id,
                                        "sourceLabel": source_label,
                                        "type": "AGENT",
                                        "detail": text[:300],
                                        "color": color,
                                    }
                                )
                            continue

                        # Tool calls
                        if btype == "tool_use":
                            tool_name = block.get("name", "")
                            inp = block.get("input", {})
                        elif btype == "toolCall":
                            tool_name = block.get("name", "")
                            inp = block.get("arguments", {})
                        else:
                            continue
                        if not tool_name:
                            continue
                        ev_type = tool_to_type(tool_name)
                        detail = extract_detail(tool_name, inp)
                        if ts:
                            events.append(
                                {
                                    "time": ts,
                                    "source": source_id,
                                    "sourceLabel": source_label,
                                    "type": ev_type,
                                    "detail": str(detail),
                                    "color": color,
                                }
                            )
        except Exception:
            pass

    # Add synthetic CONTEXT events showing workspace files loaded at session start
    workspace = os.environ.get("OPENCLAW_WORKSPACE") or os.path.expanduser(
        "~/.openclaw/workspace"
    )
    context_files = [
        "SOUL.md",
        "USER.md",
        "MEMORY.md",
        "AGENTS.md",
        "IDENTITY.md",
        "TOOLS.md",
        "HEARTBEAT.md",
    ]
    loaded_files = [
        f for f in context_files if os.path.isfile(os.path.join(workspace, f))
    ]
    if loaded_files and events:
        earliest = min(
            (ev.get("time", "") for ev in events if ev.get("time")), default=""
        )
        if earliest:
            events.append(
                {
                    "time": earliest,
                    "source": "main",
                    "sourceLabel": "main",
                    "type": "CONTEXT",
                    "detail": "System context loaded: " + ", ".join(loaded_files),
                    "color": "#64748b",
                }
            )
            # Show which files contain key info
            for f in loaded_files:
                fpath = os.path.join(workspace, f)
                try:
                    first_lines = (
                        open(fpath, "r", errors="replace").read(500).split("\n")[:5]
                    )
                    preview = " | ".join(l.strip() for l in first_lines if l.strip())[
                        :200
                    ]
                    events.append(
                        {
                            "time": earliest,
                            "source": "main",
                            "sourceLabel": "main",
                            "type": "CONTEXT",
                            "detail": f + ": " + preview,
                            "color": "#64748b",
                        }
                    )
                except Exception:
                    pass

    events.sort(
        key=lambda ev: ev.get("time", "") or "", reverse=True
    )  # ISO string sort - correct across days
    # Keep CONTEXT events + most recent 300
    context_evts = [e for e in events if e.get("type") == "CONTEXT"]
    other_evts = [e for e in events if e.get("type") != "CONTEXT"][:300]
    events = context_evts + other_evts
    sources_seen = []
    seen_set = set()
    for ev in events:
        s = ev["source"]
        if s not in seen_set:
            seen_set.add(s)
            sources_seen.append(
                {
                    "id": s,
                    "label": ev.get("sourceLabel", s),
                    "color": ev.get("color", "#888"),
                }
            )
    # Enrich events with channel info from session index
    for ev in events:
        src = ev.get("source", "")
        if src in sid_to_channel:
            ev["channel"] = sid_to_channel[src].get("channel", "")
            ev["channelSubject"] = sid_to_channel[src].get("subject", "")
            ev["chatType"] = sid_to_channel[src].get("chatType", "")
        elif src == "main":
            ev["channel"] = "cli"

    # Enrich with skill info — detect /skills/ paths in event details
    import re as _re_skill
    _skill_pat = _re_skill.compile(r'/skills/([^/\s]+)')
    for ev in events:
        detail = ev.get("detail", "")
        m = _skill_pat.search(detail)
        if m:
            ev["skill"] = m.group(1)

    # Build channel summary for filter chips
    channel_counts = {}
    for ev in events:
        ch = ev.get("channel", "")
        if ch:
            channel_counts[ch] = channel_counts.get(ch, 0) + 1

    try:
        _d._ext_emit("brain.event", {"count": len(events)})
    except Exception:
        pass
    return jsonify({"events": events, "total": len(events), "sources": sources_seen, "channels": channel_counts})


@bp_brain.route("/api/brain-stream")
def api_brain_stream():
    """SSE endpoint — streams real-time brain activity events.
    Tails OpenClaw log files + all session JSONL files for new tool calls,
    agent messages, and sub-agent activity. Emits each event as SSE data.
    """
    import dashboard as _d
    if not _d._acquire_stream_slot("brain"):
        return jsonify({"error": "Too many active brain streams"}), 429

    import re as _re_bs

    log_tool_re = _re_bs.compile(r"^\[(\w+)\]\s*(.*)", _re_bs.DOTALL)

    session_dir = _d.SESSIONS_DIR or os.path.expanduser("~/.openclaw/agents/main/sessions")

    # Color assignment
    color_palette = [
        "#06b6d4",
        "#f59e0b",
        "#ec4899",
        "#8b5cf6",
        "#10b981",
        "#f97316",
        "#6366f1",
    ]
    agent_colors = {}
    color_idx = [0]

    def get_agent_color(source):
        if source == "main":
            return "#a855f7"
        if source not in agent_colors:
            agent_colors[source] = color_palette[color_idx[0] % len(color_palette)]
            color_idx[0] += 1
        return agent_colors[source]

    def tool_to_type(tn):
        tn = tn.lower()
        if tn == "exec" or "shell" in tn or "bash" in tn or tn == "process":
            return "EXEC"
        if "read" in tn:
            return "READ"
        if "write" in tn or "edit" in tn:
            return "WRITE"
        if "browser" in tn or "canvas" in tn or "image" in tn:
            return "BROWSER"
        if tn == "message" or "tts" in tn:
            return "MSG"
        if "web_search" in tn or "web_fetch" in tn or "search" in tn:
            return "SEARCH"
        if "subagent" in tn or "spawn" in tn:
            return "SPAWN"
        return "TOOL"

    def extract_detail(tn, inp):
        tn = tn.lower()
        if not isinstance(inp, dict):
            return str(inp)[:300]
        if tn == "exec" or "shell" in tn or "bash" in tn or tn == "process":
            return (inp.get("command") or inp.get("action") or "")[:300]
        if "read" in tn:
            return (inp.get("path") or inp.get("file_path") or "")[:300]
        if "write" in tn or "edit" in tn:
            return (inp.get("path") or inp.get("file_path") or "")[:300]
        if "browser" in tn:
            return (inp.get("url") or inp.get("targetUrl") or inp.get("action") or "")[
                :300
            ]
        if tn == "message":
            return (inp.get("message") or inp.get("target") or "")[:300]
        if "search" in tn or "fetch" in tn:
            return (inp.get("query") or inp.get("url") or "")[:300]
        if "subagent" in tn or "spawn" in tn:
            return (inp.get("label") or str(inp.get("message", "")))[:300]
        vals = list(inp.values())
        return (str(vals[0]) if vals else "")[:300]

    def _parse_jsonl_event(obj, source_id, source_label, color):
        """Parse a JSONL line into a brain event dict, or return None."""
        ts = obj.get("timestamp") or obj.get("time")
        if not ts:
            return None
        role = obj.get("role", "")
        content_obj = obj.get("content", "")
        if obj.get("type") == "message":
            inner = obj.get("message", {})
            role = inner.get("role", "")
            content_obj = inner.get("content", [])

        if role == "assistant" and isinstance(content_obj, list):
            for block in content_obj:
                if not isinstance(block, dict):
                    continue
                btype = block.get("type", "")
                if btype == "thinking":
                    thinking_text = block.get("thinking", "")
                    if thinking_text:
                        return {
                            "time": ts,
                            "source": source_id,
                            "sourceLabel": source_label,
                            "type": "THINK",
                            "detail": thinking_text[:300],
                            "color": color,
                        }
                if btype == "text":
                    text = block.get("text", "")
                    if text:
                        return {
                            "time": ts,
                            "source": source_id,
                            "sourceLabel": source_label,
                            "type": "AGENT",
                            "detail": text[:300],
                            "color": color,
                        }
                if btype == "tool_use":
                    tool_name = block.get("name", "")
                    inp = block.get("input", {})
                elif btype == "toolCall":
                    tool_name = block.get("name", "")
                    inp = block.get("arguments", {})
                else:
                    continue
                if tool_name:
                    return {
                        "time": ts,
                        "source": source_id,
                        "sourceLabel": source_label,
                        "type": tool_to_type(tool_name),
                        "detail": extract_detail(tool_name, inp),
                        "color": color,
                    }
        if role == "user":
            text = ""
            if isinstance(content_obj, str):
                text = content_obj
            elif isinstance(content_obj, list):
                parts = [
                    b.get("text", "")
                    for b in content_obj
                    if isinstance(b, dict) and b.get("type") == "text"
                ]
                text = " ".join(parts)
            if text:
                return {
                    "time": ts,
                    "source": source_id,
                    "sourceLabel": source_label,
                    "type": "USER",
                    "detail": text[:300],
                    "color": color,
                }
        return None

    # Build session label map
    index_path = os.path.join(session_dir, "sessions.json")
    sid_to_label = {}
    try:
        with open(index_path, "r") as f:
            index = json.load(f)
        for key, meta in index.items():
            sid = meta.get("sessionId", "")
            label = meta.get("displayName") or meta.get("label") or ""
            if sid and label:
                sid_to_label[sid] = label
    except Exception:
        pass

    def generate():
        started = time.time()

        # Track file positions for tailing
        log_dirs = _d._get_log_dirs()
        log_files = []
        for d in log_dirs:
            log_files += sorted(glob.glob(os.path.join(d, "openclaw-*.log")))
        log_files += sorted(glob.glob("/tmp/openclaw/openclaw-*.log"))
        log_files = list(dict.fromkeys(log_files))

        # Seek to end of all files
        log_positions = {}
        for lf in log_files[-3:]:
            try:
                with open(lf, "rb") as f:
                    f.seek(0, 2)
                    log_positions[lf] = f.tell()
            except Exception:
                pass

        jsonl_positions = {}
        jsonl_files = (
            sorted(glob.glob(os.path.join(session_dir, "*.jsonl")))
            if os.path.isdir(session_dir)
            else []
        )
        for jf in jsonl_files:
            try:
                with open(jf, "rb") as f:
                    f.seek(0, 2)
                    jsonl_positions[jf] = f.tell()
            except Exception:
                pass

        last_jsonl_scan = time.time()

        try:
            # Send initial heartbeat
            yield 'event: connected\ndata: {"status":"live"}\n\n'

            while True:
                if time.time() - started > _d.SSE_MAX_SECONDS:
                    yield 'event: done\ndata: {"reason":"max_duration"}\n\n'
                    break

                events = []

                # Tail log files for main agent events
                for lf in list(log_positions.keys()):
                    try:
                        with open(lf, "rb") as f:
                            f.seek(log_positions[lf])
                            data = f.read()
                            log_positions[lf] = f.tell()
                        for line in data.decode("utf-8", errors="replace").splitlines():
                            line = line.strip()
                            if not line:
                                continue
                            try:
                                obj = json.loads(line)
                            except Exception:
                                continue
                            ts = obj.get("time") or obj.get("timestamp")
                            if not ts:
                                continue
                            msg = obj.get("0") or obj.get("message") or ""
                            if isinstance(msg, dict):
                                msg = json.dumps(msg)
                            m = log_tool_re.match(msg.strip())
                            if m:
                                tool_kw = m.group(1).lower()
                                rest = m.group(2).strip()
                                ev_type = tool_to_type(tool_kw)
                                detail = rest.split("\n")[0][:300]
                                events.append(
                                    {
                                        "time": ts,
                                        "source": "main",
                                        "sourceLabel": "main",
                                        "type": ev_type,
                                        "detail": detail,
                                        "color": "#a855f7",
                                    }
                                )
                    except Exception:
                        pass

                # Tail session JSONL files for sub-agent events
                for jf in list(jsonl_positions.keys()):
                    try:
                        with open(jf, "rb") as f:
                            f.seek(jsonl_positions[jf])
                            data = f.read()
                            jsonl_positions[jf] = f.tell()
                        if not data:
                            continue
                        fname = os.path.basename(jf).replace(".jsonl", "")
                        label = sid_to_label.get(fname, "")
                        source_label = (
                            label
                            if label
                            else (
                                "agent:" + fname[:8]
                                if _re_bs.match(r"[0-9a-f-]{36}", fname)
                                else fname
                            )
                        )
                        color = get_agent_color(fname)
                        for line in data.decode("utf-8", errors="replace").splitlines():
                            line = line.strip()
                            if not line:
                                continue
                            try:
                                obj = json.loads(line)
                                ev = _parse_jsonl_event(obj, fname, source_label, color)
                                if ev:
                                    events.append(ev)
                            except Exception:
                                pass
                    except Exception:
                        pass

                # Periodically check for new JSONL files (new sub-agents)
                now = time.time()
                if now - last_jsonl_scan > 10:
                    new_files = (
                        sorted(glob.glob(os.path.join(session_dir, "*.jsonl")))
                        if os.path.isdir(session_dir)
                        else []
                    )
                    for nf in new_files:
                        if nf not in jsonl_positions:
                            try:
                                with open(nf, "rb") as f:
                                    f.seek(0, 2)
                                    jsonl_positions[nf] = f.tell()
                            except Exception:
                                pass
                    last_jsonl_scan = now

                # Emit events
                for ev in events:
                    yield f"data: {json.dumps(ev)}\n\n"

                # Heartbeat every cycle to keep connection alive
                if not events:
                    yield ":\n\n"

                time.sleep(0.5)
        except GeneratorExit:
            pass
        finally:
            _d._release_stream_slot("brain")

    return Response(
        generate(),
        mimetype="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
