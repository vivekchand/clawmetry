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
import subprocess
import time
from datetime import datetime, timezone

from flask import Blueprint, Response, jsonify, request

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
        return jsonify({"ok": True, "type": "flow-events", "streaming": True})
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


@bp_memory.route("/api/memory-files")
@bp_memory.route("/api/memory")
def api_memory_files():
    import dashboard as _d
    return jsonify(_d._get_memory_files())


@bp_memory.route("/api/file", methods=["GET"])
def api_view_file():
    """Return the contents of a memory file."""
    import dashboard as _d
    path = request.args.get("path", "")
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
    workspace = _d.WORKSPACE or os.getcwd()
    memory_dir = _d.MEMORY_DIR or os.path.join(workspace, "memory")

    # Configurable thresholds (bytes)
    bloat_warn_kb = int(request.args.get("warn_kb", 8))
    bloat_crit_kb = int(request.args.get("crit_kb", 16))

    files = _d._get_memory_files()
    total_bytes = sum(f.get("size", 0) for f in files)
    root_files = [f for f in files if "/" not in f["path"]]
    daily_files = [f for f in files if f["path"].startswith("memory/")]

    # Estimate tokens (rough: 1 token ~ 4 chars ~ 4 bytes for English text)
    est_tokens = total_bytes // 4

    # Per-file analysis with bloat flags
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
            recommendations.append(
                {
                    "file": f["path"],
                    "severity": "critical",
                    "message": f"{f['path']} is {kb:.1f}KB ({f['size'] // 4} est. tokens). "
                    f"Consider pruning to keep context window budget lean.",
                }
            )
        elif kb >= bloat_warn_kb:
            entry["status"] = "warning"
            recommendations.append(
                {
                    "file": f["path"],
                    "severity": "warning",
                    "message": f"{f['path']} is {kb:.1f}KB. Growing large, review for stale content.",
                }
            )
        analysis.append(entry)

    # Daily memory dir growth (count files per date from filenames)
    daily_growth = []
    if os.path.isdir(memory_dir):
        date_sizes = {}
        for f in daily_files:
            basename = f["path"].replace("memory/", "")
            date_part = basename.replace(".md", "")[:10]  # YYYY-MM-DD
            if len(date_part) == 10 and date_part[4] == "-":
                date_sizes[date_part] = date_sizes.get(date_part, 0) + f["size"]
        for d in sorted(date_sizes.keys())[-30:]:
            daily_growth.append({"date": d, "bytes": date_sizes[d]})

    # Context budget estimation
    # Common context windows: 200K tokens (Claude), 128K (GPT-4), 1M (Gemini)
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

    # Largest files
    top_files = sorted(analysis, key=lambda x: x["sizeBytes"], reverse=True)[:5]

    has_bloat = any(r["severity"] == "critical" for r in recommendations)
    has_warnings = any(r["severity"] == "warning" for r in recommendations)

    return jsonify(
        {
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
    )


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

        return jsonify(
            {
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
        )
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
    """Cost optimization analysis and local model fallback recommendations."""
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

        # Get llmfit local model recommendations
        llmfit_data = _d._get_llmfit_recommendations()

        # Check if ollama binary is installed
        ollama_installed = _d._detect_ollama()

        # Build savings opportunities
        savings = _d._generate_savings_opportunities()

        return jsonify(
            {
                "costs": costs,
                "localModels": local_models_ollama,
                "recommendations": recommendations,
                "expensiveOps": expensive_ops,
                "llmfit": llmfit_data,
                "ollamaInstalled": ollama_installed,
                "llmfitAvailable": llmfit_data.get("available", False),
                "savingsOpportunities": savings,
            }
        )
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


@bp_config.route("/api/automation-analysis")
def api_automation_analysis():
    """Automation pattern analysis and suggestions for new cron jobs or skills."""
    import dashboard as _d
    try:
        # Analyze recent patterns
        patterns = _d._analyze_work_patterns()

        # Generate automation suggestions
        suggestions = _d._generate_automation_suggestions(patterns)

        return jsonify({
            'patterns': patterns,
            'suggestions': suggestions,
            'lastAnalysis': datetime.now(timezone.utc).isoformat()
        })
    except Exception as e:
        return jsonify({
            'patterns': [],
            'suggestions': [],
            'error': str(e),
            'lastAnalysis': datetime.now(timezone.utc).isoformat()
        })
