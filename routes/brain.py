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

from flask import Blueprint, Response, jsonify, request
from clawmetry.config import is_local_store_read_enabled

bp_brain = Blueprint('brain', __name__)


_BRAIN_HISTORY_CACHE = {}
_BRAIN_HISTORY_CACHE_TTL_SECONDS = 3.0
_BRAIN_HISTORY_TAIL_BYTES = 512 * 1024

# ── Task-type classifier (issue #571) ──────────────────────────────────
_FACTUAL_KW = frozenset([
    "extract", "list", "summarize", "find", "what is", "how many",
    "cite", "return json", "schema", "lookup", "search for", "retrieve",
    "get the", "fetch", "query", "select", "filter", "count", "calculate",
    "convert", "parse", "format", "validate", "check if", "verify",
    "translate", "describe", "define", "explain what", "what are",
    "show me", "give me", "tell me", "output", "return a",
])
_CREATIVE_KW = frozenset([
    "brainstorm", "write", "imagine", "draft", "generate idea",
    "story", "poem", "essay", "blog post", "ideate", "invent",
    "compose", "suggest creative", "come up with", "make up",
    "creative writing", "fiction", "novel", "screenplay", "narrative", "slogan",
    "copywriting",
])
_REASONING_KW = frozenset([
    "analyze", "analyse", "explain why", "how does", "compare", "evaluate",
    "assess", "plan", "strategy", "debug", "diagnose", "reason", "decide",
    "prioritize", "prioritise", "review", "optimize", "optimise", "refactor",
    "improve", "think through", "step by step", "consider", "tradeoff",
    "trade-off", "pros and cons", "should i", "which is better",
])


def _classify_task_type(text):
    """Return 'creative', 'factual', 'reasoning', 'mixed', or None."""
    if not text:
        return None
    t = text.lower()
    f = sum(1 for kw in _FACTUAL_KW if kw in t)
    c = sum(1 for kw in _CREATIVE_KW if kw in t)
    r = sum(1 for kw in _REASONING_KW if kw in t)
    if not (f or c or r):
        return None
    top = max(f, c, r)
    if sum(1 for s in (f, c, r) if s == top) > 1:
        return "mixed"
    if f == top:
        return "factual"
    if c == top:
        return "creative"
    return "reasoning"


def _brain_history_bool_arg(value):
    return str(value or "").strip().lower() in {"1", "true", "yes", "on", "all"}


def _v3_message_content_to_text(content) -> str:
    """Flatten an OpenClaw v3 ``data.message.content`` payload into plain text.

    The trajectory ingest path (sync.py L2090-L2102) stores the WHOLE raw event
    on ``data``, so user/assistant rows arrive with content nested under
    ``data.message.content`` — either a plain string (user) or a list of typed
    blocks (assistant: ``[{type:"text", text:...}, {type:"tool_use", ...}]``).
    Only the ``text`` and ``thinking`` blocks carry transcript content; the
    rest (tool_use, image, etc.) are summarised separately upstream.
    """
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for block in content:
            if not isinstance(block, dict):
                continue
            btype = block.get("type")
            if btype == "text":
                t = block.get("text") or ""
                if t:
                    parts.append(t)
            elif btype == "thinking":
                t = block.get("thinking") or block.get("text") or ""
                if t:
                    parts.append(t)
        return "\n".join(parts)
    return ""


def _extract_brain_detail(row: dict) -> str:
    """Pull a human-readable ``detail`` snippet from a DuckDB event row.

    Two ingest paths populate ``data`` with different shapes (P0 #1143 fix
    landed the v3 mapper alongside the legacy trajectory parser); this helper
    handles both plus the original flat-key fallback so brain-history never
    returns empty strings for events that DO have content:

      * Legacy/trajectory (event_type=user/assistant/attachment/queue-operation):
        content lives under ``data.message.content`` (string or block list),
        ``data.content``, or ``data.attachment.{name,filename}``.
      * v3 underscore (event_type=prompt.submitted/model.completed/tool.result/
        model.changed/session.started): content lives at the TOP of ``data``
        under ``finalPromptText`` / ``completionText`` / ``output`` /
        ``result`` / ``modelId`` / ``cwd``, with a mirror under ``data.data``.
      * Anything older: the original ``input/summary/text/name`` flat keys.
    """
    data = row.get("data") if isinstance(row, dict) else None
    if isinstance(data, str):
        return data
    if not isinstance(data, dict):
        return ""

    # --- Legacy/trajectory shape: data.message.content ---------------------
    msg = data.get("message")
    has_message_envelope = isinstance(msg, dict)
    if has_message_envelope:
        text = _v3_message_content_to_text(msg.get("content"))
        if text:
            return text
        # Encrypted-thinking-only assistant turns ship as
        # ``[{type:"thinking", thinking:"", signature:"…"}]``. The text is
        # genuinely absent — bail out with a stable placeholder rather than
        # falling through to noisy fallbacks like cwd / id.
        role = msg.get("role")
        if role in ("assistant", "user"):
            return "(thinking)" if role == "assistant" else ""

    # --- v3 mapper shape: top-level projection -----------------------------
    for k in ("finalPromptText", "completionText", "output", "result",
              "input", "summary", "text", "name", "content"):
        v = data.get(k)
        if isinstance(v, str) and v:
            return v
        if isinstance(v, list):
            text = _v3_message_content_to_text(v)
            if text:
                return text

    # --- v3 mirror shape: data.data.* --------------------------------------
    inner = data.get("data")
    if isinstance(inner, dict):
        for k in ("finalPromptText", "completionText", "output", "result",
                  "input", "summary", "text", "name"):
            v = inner.get(k)
            if isinstance(v, str) and v:
                return v
            if isinstance(v, list):
                text = _v3_message_content_to_text(v)
                if text:
                    return text
        # Assistant texts list (v3 model.completed)
        atexts = inner.get("assistantTexts")
        if isinstance(atexts, list):
            joined = "\n".join(str(x) for x in atexts if isinstance(x, str) and x)
            if joined:
                return joined

    # --- Type-specific fallbacks ------------------------------------------
    # attachment events: surface filename
    att = data.get("attachment")
    if isinstance(att, dict):
        for k in ("filename", "name", "path", "url"):
            v = att.get(k)
            if isinstance(v, str) and v:
                return v
    # session.started / model.changed: useful identifying labels
    for k in ("modelId", "cwd", "id", "operation"):
        v = data.get(k)
        if isinstance(v, str) and v:
            return v

    return ""


def _try_local_store_brain(limit: int, include_artifacts: bool):
    """Epic #964 phase 1b fast path. Returns a brain-history-shaped dict
    when CLAWMETRY_LOCAL_STORE_READ=1 AND the local DuckDB store has
    enough events to be useful. Returns ``None`` to defer to the JSONL
    parser so the caller can fall through cleanly.

    The shape returned is intentionally a SUBSET of the JSONL parser's
    rich UI metadata — channel icons, source labels, etc. are not yet
    enriched here. The full read-path migration is a follow-up; this
    is a measurable proof that the local store is the right answer for
    the simple list-of-events case.
    """
    rows = None
    # Issue #1088: cross-process fast-path. The standard install runs daemon
    # + dashboard as separate processes and DuckDB's exclusive writer lock
    # blocks the dashboard from opening the file even read-only. Ask the
    # daemon over HTTP first; fall back to direct open for single-process
    # boots (tests, dev mode).
    try:
        from routes.local_query import local_store_via_daemon
        rows = local_store_via_daemon("query_events", limit=limit)
    except Exception:
        rows = None
    if rows is None:
        try:
            from clawmetry import local_store
            # Issue #1240: read_only=True so the single-process fallback
            # doesn't pay DuckDB's writer-lock-retry tax under the standard
            # install (daemon proxy above is the happy path; this fallback
            # only fires in tests / dev mode).
            store = local_store.get_store(read_only=True)
            rows = store.query_events(limit=limit)
        except Exception:
            return None
    if not rows:
        # Empty store → fall through to JSONL parser so a fresh install
        # without a populated local DB still gets a useful brain feed.
        return None
    # Translate the local-store row shape (id/node_id/agent_id/session_id/
    # event_type/ts/data/cost_usd/...) into the brain-history event shape
    # the dashboard JS expects (time/type/detail/src/sessionId/...).
    out = []
    for r in rows:
        # P0 regression fix (#1143): the v3 sync mapper nests content under
        # ``data.data`` and the legacy trajectory parser nests it under
        # ``data.message.content`` — neither exposes the flat ``input/summary/
        # text/name`` keys this fast path used to read, so EVERY row came back
        # with detail="". ``_extract_brain_detail`` knows about all three
        # shapes (legacy, v3 mapper top-level, v3 mapper mirror).
        detail = _extract_brain_detail(r)
        evt_type = (r.get("event_type") or "").upper()
        row = {
            "time":       r.get("ts", ""),
            "type":       evt_type,
            "detail":     str(detail)[:200],
            "src":        (r.get("session_id") or r.get("agent_id") or "")[:32],
            "sessionId":  r.get("session_id") or "",
            "agentId":    r.get("agent_id") or "main",
            "tokens":     r.get("token_count") or 0,
            "cost":       float(r.get("cost_usd") or 0.0),
            "model":      r.get("model") or "",
        }
        # ── Channel-event enrichment (PR aca53ec8 / Telegram ingest) ─────
        # Channel turns land here as event_type=channel.in|channel.out with
        # the raw provider payload under ``data``. Surface a few flat fields
        # (provider, sender, chat_id, channel, direction) so the Brain row
        # renderer can paint a provider pill + sender name without having
        # to re-parse the data blob client-side.
        if evt_type.startswith("CHANNEL."):
            data = r.get("data") or {}
            if isinstance(data, dict):
                provider = (data.get("provider") or "").lower()
                if provider:
                    row["provider"] = provider
                    row["channel"] = provider
                # direction: channel.in → "in", channel.out → "out"
                row["direction"] = "out" if evt_type.endswith(".OUT") else "in"
                # sender: prefer flat sender_name, fall back to from/sender/user blocks
                sender = data.get("sender_name") or data.get("sender") or ""
                if not sender:
                    for blk_key in ("from", "user"):
                        blk = data.get(blk_key)
                        if isinstance(blk, dict):
                            sender = (
                                blk.get("username")
                                or blk.get("first_name")
                                or blk.get("name")
                                or ""
                            )
                            if sender:
                                break
                if sender:
                    row["sender"] = str(sender)[:80]
                # chat_id
                chat_id = data.get("chat_id") or data.get("channel_id") or ""
                if not chat_id and isinstance(data.get("chat"), dict):
                    chat_id = data["chat"].get("id") or ""
                if chat_id:
                    row["chat_id"] = str(chat_id)[:80]
        out.append(row)
    return {
        "events":  out,
        "count":   len(out),
        "_source": "local_store",
        "_shape":  "brain_history",
    }


def _brain_history_is_artifact(path):
    name = os.path.basename(path)
    return name.endswith(".trajectory.jsonl") or ".checkpoint." in name


def _brain_history_read_head_tail(path, head_lines=20, tail_bytes=_BRAIN_HISTORY_TAIL_BYTES):
    """Read a tiny context head plus byte-tail from a JSONL file.

    The old implementation used readlines() on every session file. On large
    installs that can mean hundreds of MB for every Brain refresh. This keeps
    context rows while bounding I/O per file.
    """
    try:
        with open(path, "rb") as fh:
            size = os.fstat(fh.fileno()).st_size
            if size <= tail_bytes:
                return fh.read().decode("utf-8", "replace").splitlines()

            head = []
            for _ in range(head_lines):
                line = fh.readline()
                if not line:
                    break
                head.append(line.decode("utf-8", "replace").rstrip("\r\n"))

            fh.seek(max(0, size - tail_bytes))
            fh.readline()  # drop a possibly partial JSONL row
            tail = fh.read().decode("utf-8", "replace").splitlines()
            return head + tail[-900:]
    except Exception:
        return []


@bp_brain.route("/api/brain-history")
def api_brain_history():
    import dashboard as _d
    try:
        limit = max(1, min(500, int(request.args.get("limit", 300))))
    except (TypeError, ValueError):
        limit = 300
    include_artifacts = _brain_history_bool_arg(
        request.args.get("include_artifacts") or request.args.get("artifacts")
    )
    # Epic #964 phase 1b: opt-in local-store fast path. Skip the JSONL
    # parser entirely when CLAWMETRY_LOCAL_STORE_READ=1 AND the store
    # has data. Falls through to the full parser otherwise (so a fresh
    # install with an empty store still gets the rich brain feed).
    if is_local_store_read_enabled():
        fast = _try_local_store_brain(limit, include_artifacts)
        if fast is not None:
            return jsonify(fast)
    cache_key = (limit, include_artifacts)
    cached = _BRAIN_HISTORY_CACHE.get(cache_key)
    now_cache = time.time()
    if cached and now_cache - cached[0] < _BRAIN_HISTORY_CACHE_TTL_SECONDS:
        return jsonify(cached[1])

    # Return unified event stream - v2 bounded by limit + tail reads
    events = []

    # Build sessionId to displayName + channel map
    session_dir = _d.SESSIONS_DIR or os.path.expanduser("~/.openclaw/agents/main/sessions")
    index_path = os.path.join(session_dir, "sessions.json")
    sid_to_label = {}
    sid_to_channel = {}  # sessionId → {channel, chatType, subject}
    sid_to_meta = {}  # sessionId → {category, icon, human_label, last_ts, provider}

    # Channel-provider → emoji map. Mirrors dashboard.py's CHANNEL_ICONS;
    # inlined here so the route is self-contained for wheel imports.
    _CHANNEL_ICON = {
        "telegram": "📱", "signal": "📡", "whatsapp": "💬", "discord": "🎮",
        "slack": "💼", "imessage": "🍎", "webchat": "🌐", "matrix": "🔢",
        "msteams": "🏢", "irc": "📡", "googlechat": "🔵", "mattermost": "⚡",
        "line": "💚", "nostr": "🟣", "twitch": "💜", "bluebubbles": "💙",
        "cli": "⌨️", "tui": "⌨️",
    }

    def _classify(sess_key, meta):
        # Order matters: ":cron:" and ":subagent:" appear before channel infix.
        if ":cron:" in sess_key:
            return "cron"
        if ":subagent:" in sess_key:
            return "subagent"
        parts = sess_key.split(":")
        # agent:<id>:main  → main agent session
        if len(parts) >= 3 and parts[2] == "main":
            return "main"
        # agent:<id>:<provider>:…  → channel session
        if len(parts) >= 3 and parts[2] not in ("main", "subagent", "cron"):
            return "channel"
        return "other"

    def _icon_for(category, provider):
        if category == "main":
            return "🧠"
        if category == "cron":
            return "📅"
        if category == "subagent":
            return "🤖"
        if category == "channel":
            return _CHANNEL_ICON.get((provider or "").lower(), "💬")
        return "•"

    def _human_label(sess_key, meta, fallback_sid):
        # Channel: origin.label > displayName
        origin = meta.get("origin") or {}
        if isinstance(origin, dict) and origin.get("label"):
            return str(origin["label"])[:60]
        lbl = meta.get("displayName") or meta.get("label") or ""
        if lbl:
            return str(lbl)[:60]
        # Cron: sess_key pattern agent:main:cron:<id>[:run:<tail>]
        if ":cron:" in sess_key:
            parts = sess_key.split(":")
            try:
                cron_id = parts[parts.index("cron") + 1]
                return "cron:" + cron_id[:8]
            except (ValueError, IndexError):
                pass
        # Subagent: use task if present
        task = meta.get("task") or ""
        if task:
            return str(task)[:40]
        # Fall-through: preserve old `agent:<hex8>` behaviour
        import re as _re_fb
        if _re_fb.match(r"[0-9a-f-]{36}$", fallback_sid):
            return "agent:" + fallback_sid[:8]
        return fallback_sid[:40]

    try:
        with open(index_path, "r") as f:
            index = json.load(f)
        for key, meta in index.items():
            if not isinstance(meta, dict):
                continue
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

                cat = _classify(key, meta)
                sid_to_meta[sid] = {
                    "category":    cat,
                    "provider":    channel or (meta.get("origin") or {}).get("provider") or "",
                    "icon":        _icon_for(cat, channel or (meta.get("origin") or {}).get("provider") or ""),
                    "human_label": _human_label(key, meta, sid),
                    "last_ts":     meta.get("updatedAt") or 0,
                }
    except Exception:
        pass

    # Main-agent source has no sessions.json row; synthesize one.
    sid_to_meta.setdefault("main", {
        "category": "main", "provider": "cli", "icon": "🧠",
        "human_label": "Main", "last_ts": 0,
    })

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
                # NOTE: a previous implementation also did substring keyword
                # matching here ("if 'browser' in msg_lower → BROWSER event").
                # That mis-classified benign console messages (e.g. "Opened in
                # your browser. Keep that tab to control OpenClaw." or "Token
                # auto-auth included in browser/clipboard URL.") as BROWSER
                # tool invocations and contaminated the Brain stream with
                # onboarding/lifecycle text. Removed — only bracketed
                # ``[tool] ...`` log lines now produce events from this path.
                # DuckDB-first: real tool calls already arrive via local_store
                # ingestion, so this fallback is pure noise. (issue: brain
                # onboarding-text contamination, 2026-05-13.)
        except Exception:
            pass

    # Source 2: Session JSONL files (sub-agent activity)
    session_files_all = glob.glob(os.path.join(session_dir, "*.jsonl"))
    if not include_artifacts:
        session_files_all = [sf for sf in session_files_all if not _brain_history_is_artifact(sf)]

    def _session_file_mtime(sf):
        try:
            return os.path.getmtime(sf)
        except OSError:
            return 0

    session_files = sorted(session_files_all, key=_session_file_mtime, reverse=True)
    max_files = 250 if include_artifacts else max(50, min(250, limit * 2))
    session_files = session_files[:max_files]

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

            raw_lines = _brain_history_read_head_tail(sf)

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

                # OpenClaw uses type=message; claude-cli uses type=user/assistant
                # with the same {role,content} nested under obj.message.
                if obj.get("type") in ("message", "user", "assistant") and isinstance(
                    obj.get("message"), dict
                ):
                    inner = obj.get("message", {})
                    role = inner.get("role", role) or obj.get("type", "")
                    content_obj = inner.get("content", content_obj)

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
                                "taskType": _classify_task_type(text),
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
                                        "taskType": _classify_task_type(text),
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

    # Belt-and-suspenders dedupe: identical (time, source, type, detail) tuples
    # can sneak in from (a) overlapping file slices, (b) the same session being
    # recorded in two log paths, or (c) the synthetic CONTEXT pass replaying an
    # event already parsed from JSONL. Drop the second-and-later occurrence
    # rather than letting them double-render in the feed.
    seen_keys = set()
    deduped = []
    for ev in events:
        key = (
            ev.get("time", ""),
            ev.get("source", ""),
            ev.get("type", ""),
            (ev.get("detail") or "")[:200],
        )
        if key in seen_keys:
            continue
        seen_keys.add(key)
        deduped.append(ev)
    events = deduped

    events.sort(
        key=lambda ev: ev.get("time", "") or "", reverse=True
    )  # ISO string sort - correct across days
    # Keep CONTEXT events + most recent 300
    context_evts = [e for e in events if e.get("type") == "CONTEXT"]
    other_evts = [e for e in events if e.get("type") != "CONTEXT"][:limit]
    events = context_evts + other_evts
    sources_seen = []
    seen_set = set()
    for ev in events:
        s = ev["source"]
        if s not in seen_set:
            seen_set.add(s)
            extra = sid_to_meta.get(s, {})
            # Prefer the richer human label built from sessions.json. Fall
            # back to whatever the event carried (sourceLabel → sid).
            label = extra.get("human_label") or ev.get("sourceLabel") or s
            sources_seen.append(
                {
                    "id":       s,
                    "label":    label,
                    "color":    ev.get("color", "#888"),
                    "category": extra.get("category", "other"),
                    "icon":     extra.get("icon", "•"),
                    "provider": extra.get("provider", ""),
                    "last_ts":  extra.get("last_ts", 0),
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
    payload = {"events": events, "total": len(events), "sources": sources_seen, "channels": channel_counts}
    _BRAIN_HISTORY_CACHE[cache_key] = (time.time(), payload)
    if len(_BRAIN_HISTORY_CACHE) > 8:
        oldest_key = min(_BRAIN_HISTORY_CACHE, key=lambda k: _BRAIN_HISTORY_CACHE[k][0])
        _BRAIN_HISTORY_CACHE.pop(oldest_key, None)
    return jsonify(payload)


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
        # OpenClaw wraps via type=message; claude-cli uses type=user/assistant
        # with the same {role,content} nested under obj.message. Unwrap both.
        if obj.get("type") in ("message", "user", "assistant") and isinstance(
            obj.get("message"), dict
        ):
            inner = obj.get("message", {})
            role = inner.get("role", role) or obj.get("type", "")
            content_obj = inner.get("content", content_obj)

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
                            "taskType": _classify_task_type(text),
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
                    "taskType": _classify_task_type(text),
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
