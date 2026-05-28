"""
routes/selfevolve.py -- ClawMetry Self-Evolve: the agent reviews its own trajectory.

Where Advisor answers one question at a time, Self-Evolve runs a standing
review of recent activity and emits structured findings: cost hotspots,
failing tools, looping paths, over-eager models, prompts that are burning
tokens without moving the needle. Each finding has a category, severity,
evidence, and a concrete suggestion.

The LLM path, auth, and privacy model are the same as Advisor -- we just
build a richer context and ask for JSON output instead of prose.

Results are cached to ``~/.openclaw/.clawmetry/selfevolve_latest.json`` so
the UI can render instantly on subsequent page loads without re-billing
the LLM. The operator triggers a fresh analysis explicitly.
"""

from __future__ import annotations

import json
import os
import re
import time
from collections import Counter, defaultdict

from flask import Blueprint, jsonify, request

from clawmetry import error_signal as _error_signal
from routes.advisor import (
    _call_anthropic_api,
    _call_via_claude_cli,
    _extract_answer,
    _load_anthropic_auth,
)

bp_selfevolve = Blueprint("selfevolve", __name__)

MAX_CONTEXT_EVENTS = 300
MAX_FINDINGS = 8
REQUEST_TIMEOUT_SEC = 60


# ── Cache location ────────────────────────────────────────────────────────────


def _cache_path() -> str:
    base = os.environ.get("OPENCLAW_HOME") or os.path.expanduser("~/.openclaw")
    d = os.path.join(base, ".clawmetry")
    os.makedirs(d, exist_ok=True)
    return os.path.join(d, "selfevolve_latest.json")


def _load_cached() -> dict | None:
    p = _cache_path()
    if not os.path.isfile(p):
        return None
    try:
        with open(p) as f:
            return json.load(f)
    except Exception:
        return None


def _save_cached(payload: dict) -> None:
    try:
        with open(_cache_path(), "w") as f:
            json.dump(payload, f)
    except Exception:
        pass


# ── Context assembly ──────────────────────────────────────────────────────────


def _classify_event(ev: dict) -> tuple[str, bool]:
    """Return (bucket, is_error). Buckets: exec | tool | llm | context | agent | user | other."""
    typ = (ev.get("type") or "").lower()
    detail_raw = str(ev.get("detail") or "")
    detail = detail_raw.lower()
    is_error = (
        "error" in detail
        or "failed" in detail
        or "timeout" in detail
        or typ == "error"
    )
    # Don't count benign read-guards / transient timeouts as errors — they were
    # inflating the Self-Evolve error buckets (see clawmetry.error_signal).
    if is_error and _error_signal.is_benign_tool_error(detail_raw):
        is_error = False
    if typ in ("exec", "execution"):
        return "exec", is_error
    if typ in ("tool", "tool_use", "tool_result"):
        return "tool", is_error
    if typ in ("assistant", "llm", "model"):
        return "llm", is_error
    if typ == "context":
        return "context", is_error
    if typ == "agent":
        return "agent", is_error
    if typ == "user":
        return "user", is_error
    return "other", is_error


def _summarize_events(events: list[dict]) -> dict:
    """Derive structured signals from the recent brain feed."""
    by_bucket: Counter = Counter()
    errors_by_bucket: Counter = Counter()
    error_details: list[str] = []
    recent_sources: Counter = Counter()
    by_hour: defaultdict = defaultdict(int)

    # Loop detection: same (source, bucket, first-80-chars-of-detail) fingerprint
    # repeating within a 120s window signals an agent that's spinning.
    loop_candidates: defaultdict = defaultdict(list)

    for ev in events:
        bucket, is_error = _classify_event(ev)
        by_bucket[bucket] += 1
        recent_sources[ev.get("source") or "main"] += 1
        if is_error:
            errors_by_bucket[bucket] += 1
            detail = str(ev.get("detail") or "")[:160].replace("\n", " ")
            if detail:
                error_details.append(detail)
        ts = ev.get("ts") or 0
        if ts:
            by_hour[time.strftime("%Y-%m-%d %H:00", time.localtime(ts))] += 1

        fp = (
            (ev.get("source") or "main"),
            bucket,
            str(ev.get("detail") or "")[:80],
        )
        if ts:
            loop_candidates[fp].append(ts)

    loops: list[dict] = []
    for fp, tss in loop_candidates.items():
        if len(tss) < 3:
            continue
        tss_sorted = sorted(tss)
        # A tight cluster: 3+ occurrences within 120 seconds.
        for i in range(len(tss_sorted) - 2):
            if tss_sorted[i + 2] - tss_sorted[i] <= 120:
                loops.append(
                    {
                        "source": fp[0],
                        "bucket": fp[1],
                        "fingerprint": fp[2],
                        "count": len(tss_sorted),
                    }
                )
                break

    # Top recurring error lines (dedup by first 60 chars)
    err_counter: Counter = Counter()
    for line in error_details:
        err_counter[line[:60]] += 1
    top_errors = [{"pattern": k, "count": v} for k, v in err_counter.most_common(5)]

    return {
        "total_events": len(events),
        "by_bucket": dict(by_bucket),
        "errors_by_bucket": dict(errors_by_bucket),
        "top_errors": top_errors,
        "sources": dict(recent_sources.most_common(6)),
        "events_per_hour": dict(sorted(by_hour.items())[-12:]),
        "loops_detected": loops[:5],
    }


def _summarize_sessions(sessions: list[dict]) -> dict:
    """Cost / token / model distribution across recent sessions."""
    by_model_tokens: Counter = Counter()
    by_model_cost: defaultdict = defaultdict(float)
    total_tokens = 0
    total_cost = 0.0
    for s in sessions:
        model = s.get("model") or "?"
        tok = int(s.get("tokens", 0) or 0)
        cost = float(s.get("cost_usd", 0.0) or 0.0)
        by_model_tokens[model] += tok
        by_model_cost[model] += cost
        total_tokens += tok
        total_cost += cost
    return {
        "total_tokens": total_tokens,
        "total_cost_usd": round(total_cost, 4),
        "models": [
            {
                "model": m,
                "tokens": by_model_tokens[m],
                "cost_usd": round(by_model_cost[m], 4),
                "share_pct": round(100.0 * by_model_tokens[m] / max(1, total_tokens), 1),
            }
            for m in sorted(by_model_tokens, key=by_model_tokens.get, reverse=True)[:6]
        ],
        "session_count": len(sessions),
    }


def _gather_context(limit_events: int = MAX_CONTEXT_EVENTS) -> dict:
    """Richer than Advisor's context -- adds aggregated signals."""
    import dashboard as _d

    out: dict = {}

    # Brain events — raw sample + derived signals
    try:
        from routes.brain import api_brain_history

        with _d.app.test_request_context(
            "/api/brain-history?limit=" + str(limit_events)
        ):
            resp = api_brain_history()
            payload = resp.get_json() if hasattr(resp, "get_json") else None
        events = (payload or {}).get("events") or []
        out["brain_signals"] = _summarize_events(events)
    except Exception as e:
        out["brain_signals_error"] = str(e)[:200]

    # Sessions rollup
    try:
        analytics = _d._compute_transcript_analytics()
        sessions = analytics.get("sessions") or []
        sessions.sort(key=lambda s: s.get("updated_ts") or 0, reverse=True)
        out["sessions_rollup"] = _summarize_sessions(sessions[:30])
    except Exception as e:
        out["sessions_error"] = str(e)[:200]

    # Daily cost trajectory last 14d -- reveals cost creep
    try:
        daily_tokens = analytics.get("daily_tokens", {})  # type: ignore[name-defined]
        daily_cost = analytics.get("daily_cost", {})  # type: ignore[name-defined]
        keys = sorted(daily_tokens.keys())[-14:]
        out["daily_trend"] = [
            {
                "date": k,
                "tokens": daily_tokens.get(k, 0),
                "cost_usd": round(daily_cost.get(k, 0.0), 4),
            }
            for k in keys
        ]
    except Exception:
        pass

    return out


# ── Prompt construction ───────────────────────────────────────────────────────


SYSTEM_PROMPT = (
    "You are ClawMetry Self-Evolve. You read the operator's own agent "
    "telemetry and propose concrete improvements they can act on today: a "
    "failing tool, a model overused relative to its value, a prompt burning "
    "tokens without progress, a looping path, a cost trend that will break "
    "their budget.\n\n"
    "ACCURACY RULES — a single wrong finding destroys trust, so follow these "
    "exactly:\n"
    "1. Claim ONLY what the numbers in the data directly show. You see usage "
    "metrics, NOT configuration or internals — never speculate about a cause "
    "you cannot see (router config, model availability, why a value is what "
    "it is).\n"
    "2. Do NOT call anything 'broken', 'a regression', 'disabled', 'stuck', or "
    "'frozen' unless the data shows an actual error, failure, or a clear "
    "before->after change. A model with zero or flat usage is almost always a "
    "deliberate config choice (the primary model does the work), NOT a fault — "
    "treat absence of usage as expected unless errors in the data prove "
    "otherwise. Never call a value anomalous and rule out the benign "
    "explanation in the same breath.\n"
    "3. When a metric looks unusual but its cause is not in the data, phrase it "
    "as an observation to verify ('X is N; if you expected otherwise, check "
    "Z'), never as an asserted defect.\n"
    "4. Severity: 'high' is ONLY for active harm shown in the data (tool errors, "
    "loops causing failures, runaway cost). Unused capacity, style, or "
    "could-be-better items are 'low' or 'medium'. Never mark a config-design "
    "observation 'high'.\n\n"
    "Return STRICT JSON only, no preamble, no markdown fences. Shape: "
    '{"findings":[{"category":"cost|reliability|latency|prompt|model|loop",'
    '"severity":"high|medium|low","title":"...","evidence":"cite the specific '
    'numbers/events from the data that PROVE this finding","suggestion":"one '
    'concrete action"}]}. '
    f"At most {MAX_FINDINGS} findings, ordered by severity. If the data is too "
    "sparse to draw a confident conclusion, return "
    '{"findings":[],"insufficient":true,"reason":"..."}.'
)


def _build_prompt(ctx: dict) -> str:
    parts: list[str] = []
    parts.append("=== Aggregated telemetry for this agent ===\n")
    parts.append(json.dumps(ctx, default=str, indent=2)[:6000])
    parts.append("")
    parts.append("Analyse and return the JSON described in the system prompt.")
    return "\n".join(parts)


# ── JSON extraction from LLM output ───────────────────────────────────────────


def _extract_findings(raw_text: str) -> tuple[list[dict], dict]:
    """LLMs sometimes wrap JSON in prose or code fences. Be defensive."""
    if not raw_text:
        return [], {"insufficient": True, "reason": "empty response"}

    # Strip code fences if present
    text = raw_text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```[a-zA-Z]*\n?", "", text)
        text = re.sub(r"\n?```\s*$", "", text)

    # Grab the first top-level JSON object
    m = re.search(r"\{.*\}", text, re.DOTALL)
    if not m:
        return [], {"insufficient": True, "reason": "no JSON in response"}

    try:
        obj = json.loads(m.group(0))
    except Exception as e:
        return [], {"insufficient": True, "reason": f"JSON parse error: {e}"}

    findings = obj.get("findings") or []
    if not isinstance(findings, list):
        findings = []

    # Normalise each finding, cap length
    clean: list[dict] = []
    for f in findings[:MAX_FINDINGS]:
        if not isinstance(f, dict):
            continue
        clean.append(
            {
                "category": str(f.get("category", "other"))[:40],
                "severity": str(f.get("severity", "medium"))[:10],
                "title": str(f.get("title", ""))[:200],
                "evidence": str(f.get("evidence", ""))[:600],
                "suggestion": str(f.get("suggestion", ""))[:600],
            }
        )

    meta = {
        "insufficient": bool(obj.get("insufficient")),
        "reason": str(obj.get("reason", ""))[:200],
    }
    return clean, meta


# ── Endpoints ─────────────────────────────────────────────────────────────────


@bp_selfevolve.route("/api/selfevolve/status")
def api_selfevolve_status():
    mode, credential = _load_anthropic_auth()
    cached = _load_cached()

    # Issue #1721: when auto-detect comes up empty, give the UI enough info
    # to render the same OpenClaw-setup CTA the rest of the dashboard uses
    # (not a "paste your API key here" input box). The hint surfaces what
    # paths were probed so a curious operator can see exactly where to drop
    # the credential -- zero-config first, then opt-in env var, never a
    # blocking modal.
    home = os.environ.get("OPENCLAW_HOME") or os.path.expanduser("~/.openclaw")
    setup_hint = None
    if not credential:
        setup_hint = {
            "headline": "Self-Evolve needs an Anthropic credential.",
            "subhead": (
                "Run `claude` once to sign in with OAuth (free, recommended), "
                "or export ANTHROPIC_API_KEY in your shell."
            ),
            "probed": [
                "$ANTHROPIC_API_KEY / $ANTHROPIC_AUTH_TOKEN / $CLAUDE_API_KEY",
                os.path.join(home, ".clawmetry", "insights_config.json"),
                os.path.join(home, "openclaw.json"),
                os.path.join(home, "service-env", "ai.openclaw.gateway.env"),
                os.path.join(home, "agents", "main", "agent", "auth-profiles.json"),
            ],
            "claude_cli_url": "https://docs.anthropic.com/en/docs/claude-code",
        }
    return jsonify(
        {
            "available": bool(credential),
            "auth_mode": mode or "none",
            "has_cached": bool(cached),
            "cached_at": (cached or {}).get("generated_at"),
            "setup_hint": setup_hint,
        }
    )


@bp_selfevolve.route("/api/selfevolve/latest")
def api_selfevolve_latest():
    cached = _load_cached()
    if not cached:
        return jsonify({"findings": [], "cached": False})
    cached["cached"] = True
    return jsonify(cached)


@bp_selfevolve.route("/api/selfevolve/analyze", methods=["POST"])
def api_selfevolve_analyze():
    mode, credential = _load_anthropic_auth()
    if not credential:
        return (
            jsonify(
                {
                    "error": "no_auth",
                    "message": (
                        "Self-Evolve needs an Anthropic key. Set "
                        "ANTHROPIC_API_KEY in your shell, "
                        "or paste one in Settings."
                    ),
                }
            ),
            412,
        )

    ctx = _gather_context()
    prompt = _build_prompt(ctx)

    if mode == "claude_cli":
        resp = _call_via_claude_cli(
            credential, prompt, system=SYSTEM_PROMPT, timeout=REQUEST_TIMEOUT_SEC
        )
    else:
        resp = _call_anthropic_api(
            credential,
            prompt,
            system=SYSTEM_PROMPT,
            max_tokens=1500,
            timeout=REQUEST_TIMEOUT_SEC,
        )

    if resp.get("_error"):
        return (
            jsonify(
                {
                    "error": "upstream_error",
                    "status": resp.get("status"),
                    "detail": resp.get("body", "")[:300],
                }
            ),
            502,
        )

    raw = _extract_answer(resp)
    findings, meta = _extract_findings(raw)
    usage = resp.get("usage") or {}

    payload = {
        "findings": findings,
        "insufficient": meta.get("insufficient", False),
        "reason": meta.get("reason", ""),
        "generated_at": int(time.time()),
        "model": resp.get("model", ""),
        "input_tokens": usage.get("input_tokens", 0),
        "output_tokens": usage.get("output_tokens", 0),
        "events_considered": (ctx.get("brain_signals") or {}).get("total_events", 0),
    }
    _save_cached(payload)
    return jsonify(payload)


# ── "Fix with AI": apply a finding by dispatching it to the local agent ────────
# A finding's suggestion is sent to `openclaw agent` (OpenClaw's own creds —
# ClawMetry's gateway token is read-only), the same mechanism Self-Evolve uses
# to *generate* findings. The agent actually makes the change. Jobs run in a
# background thread; the UI polls /api/selfevolve/fix/status. Local-only: on a
# host with no `openclaw` CLI (e.g. the cloud server) this returns 412 and the
# cloud relay path (queue a node command) takes over instead.

import threading as _threading
import subprocess as _subprocess

_FIX_JOBS: dict = {}  # job_id -> {status, summary, error, started_at}
_FIX_LOCK = _threading.Lock()
_FIX_MAX = 50
_FIX_SESSION_ID = "clawmetry-fix"


def _resolve_openclaw_bin_local():
    import shutil

    found = shutil.which("openclaw")
    if found:
        return found
    for cand in (
        "/opt/homebrew/bin/openclaw",
        "/usr/local/bin/openclaw",
        os.path.expanduser("~/.local/bin/openclaw"),
        "/usr/bin/openclaw",
    ):
        if os.path.isfile(cand) and os.access(cand, os.X_OK):
            return cand
    return None


def _build_fix_message(title, suggestion, category, evidence):
    return (
        "You are ClawMetry Self-Evolve in FIX mode. A review of your own agent "
        "telemetry surfaced the finding below. Apply the recommended change to "
        "your OpenClaw setup now, using your tools (edit config files, adjust "
        "model routing, set values, etc.).\n\n"
        "Finding (" + (category or "general") + "): " + (title or "") + "\n"
        "Evidence: " + (evidence or "(none)") + "\n"
        "Recommended action: " + (suggestion or "") + "\n\n"
        "Make the concrete change. If a step needs a human decision you cannot "
        "safely make on your own, do what you safely can and clearly state what "
        "remains for the operator. Keep it tight. End with a one-line summary "
        "that starts with 'DONE:' describing exactly what you changed."
    )


def _extract_fix_summary(stdout):
    """Pull a human summary from the `openclaw agent --json` envelope."""
    try:
        out = json.loads(stdout)
    except Exception:
        return ((stdout or "").strip()[:600]) or "Done."
    result = out.get("result") or {}
    txt = ""
    for p in result.get("payloads") or []:
        if isinstance(p, dict) and p.get("text"):
            txt = p["text"]
    txt = txt or result.get("text") or out.get("text") or ""
    m = re.search(r"DONE:.*", txt or "")
    if m:
        return m.group(0).strip()[:600]
    return ((txt or "Done.").strip()[:600]) or "Done."


def _run_fix_job(job_id, message, timeout=300):
    binp = _resolve_openclaw_bin_local()
    if not binp:
        with _FIX_LOCK:
            _FIX_JOBS[job_id].update(
                status="error", error="openclaw CLI not found on this machine"
            )
        return
    # `openclaw` is a Node script; under launchd's minimal PATH `node` isn't
    # found (rc 127). Prepend the bin dir + the usual Node locations.
    env = dict(os.environ)
    node_dirs = [
        os.path.dirname(binp),
        "/opt/homebrew/bin",
        "/usr/local/bin",
        os.path.expanduser("~/.local/bin"),
    ]
    env["PATH"] = os.pathsep.join(node_dirs + [env.get("PATH", "/usr/bin:/bin")])
    with _FIX_LOCK:
        _FIX_JOBS[job_id].update(status="running")
    try:
        proc = _subprocess.run(
            [
                binp,
                "agent",
                "--session-id",
                _FIX_SESSION_ID,
                "--message",
                message,
                "--json",
                "--timeout",
                str(timeout),
            ],
            capture_output=True,
            text=True,
            timeout=timeout + 30,
            env=env,
        )
        if proc.returncode != 0:
            with _FIX_LOCK:
                _FIX_JOBS[job_id].update(
                    status="error",
                    error=(proc.stderr or ("agent exited %d" % proc.returncode))[:400],
                )
            return
        summary = _extract_fix_summary(proc.stdout)
        with _FIX_LOCK:
            _FIX_JOBS[job_id].update(status="done", summary=summary)
    except _subprocess.TimeoutExpired:
        with _FIX_LOCK:
            _FIX_JOBS[job_id].update(status="error", error="agent timed out")
    except Exception as e:  # never crash the worker thread
        with _FIX_LOCK:
            _FIX_JOBS[job_id].update(status="error", error=str(e)[:400])


@bp_selfevolve.route("/api/selfevolve/fix", methods=["POST"])
def api_selfevolve_fix():
    """Dispatch a finding's suggestion to the local agent to apply it."""
    if _resolve_openclaw_bin_local() is None:
        return (
            jsonify(
                {
                    "error": "no_agent",
                    "message": (
                        "OpenClaw CLI not found on this machine. Run the fix from "
                        "the host where your agent lives."
                    ),
                }
            ),
            412,
        )
    body = request.get_json(silent=True) or {}
    suggestion = (body.get("suggestion") or "").strip()
    if not suggestion:
        return jsonify({"error": "bad_request", "message": "suggestion is required"}), 400
    import secrets as _secrets

    job_id = _secrets.token_hex(8)
    message = _build_fix_message(
        (body.get("title") or "").strip(),
        suggestion,
        (body.get("category") or "").strip(),
        (body.get("evidence") or "").strip(),
    )
    with _FIX_LOCK:
        if len(_FIX_JOBS) >= _FIX_MAX:
            stale = sorted(_FIX_JOBS, key=lambda j: _FIX_JOBS[j].get("started_at", 0))
            for k in stale[: len(_FIX_JOBS) - _FIX_MAX + 1]:
                _FIX_JOBS.pop(k, None)
        _FIX_JOBS[job_id] = {
            "status": "queued",
            "summary": "",
            "error": "",
            "started_at": time.time(),
        }
    _threading.Thread(
        target=_run_fix_job, args=(job_id, message), daemon=True
    ).start()
    return jsonify({"job_id": job_id, "status": "queued"})


@bp_selfevolve.route("/api/selfevolve/fix/status")
def api_selfevolve_fix_status():
    job_id = request.args.get("job_id", "")
    with _FIX_LOCK:
        job = _FIX_JOBS.get(job_id)
    if not job:
        return jsonify({"error": "not_found"}), 404
    return jsonify(
        {
            "status": job["status"],
            "summary": job.get("summary", ""),
            "error": job.get("error", ""),
        }
    )


# ── #2201: file a Self-Evolve finding as a candidate asset ─────────────────
# Thin wrapper so the dashboard / cloud UI can promote a finding into the
# asset registry with one click — generates the asset id, packages the
# finding body as the asset content, and ties it to its source session_id.
# The reviewer still has to approve via POST /api/assets/<id>/review before
# the asset becomes searchable / recommendable.

@bp_selfevolve.route(
    "/api/selfevolve/findings/save-as-asset", methods=["POST"]
)
def api_selfevolve_save_as_asset():
    from datetime import datetime, timezone
    import secrets as _secrets

    data = request.get_json(silent=True) or {}
    finding_id = (data.get("finding_id") or "").strip()
    session_id = (data.get("session_id") or "").strip()
    summary = (data.get("summary") or data.get("name") or "").strip()
    body = data.get("body") or data.get("content") or ""
    if not summary:
        return jsonify({"error": "'summary' is required"}), 400
    valid_types = {
        "skill", "prompt", "workflow", "playbook",
        "memory_snippet", "tool_config", "evaluation_case",
    }
    asset_type = (data.get("asset_type") or "prompt").strip()
    if asset_type not in valid_types:
        return jsonify({
            "error": f"'asset_type' must be one of {sorted(valid_types)}",
        }), 400

    asset_id = data.get("id") or f"selfevolve:{finding_id or _secrets.token_hex(6)}"
    payload = {
        "id": asset_id,
        "asset_type": asset_type,
        "name": summary,
        "description": data.get("description") or "",
        "source_session_id": session_id,
        "source_run_id": data.get("source_run_id") or "",
        "author": data.get("author") or "self-evolve",
        "team_id": data.get("team_id") or "",
        "tags": (data.get("tags") or []) + ["self-evolve"],
        "content": {
            "finding_id": finding_id,
            "summary": summary,
            "body": body,
            "filed_at": datetime.now(timezone.utc).isoformat(),
        },
        "status": "pending",
    }

    try:
        from routes.local_query import local_store_via_daemon
        local_store_via_daemon("ingest_asset", asset=payload)
    except Exception:
        try:
            from clawmetry import local_store
            local_store.get_store().ingest_asset(payload)
        except Exception as exc:
            return jsonify({"error": f"asset store unavailable: {exc}"}), 503

    try:
        from routes.local_query import local_store_via_daemon
        row = local_store_via_daemon("get_asset", asset_id=asset_id)
    except Exception:
        row = None
    return jsonify(row or {"id": asset_id, "status": "pending"}), 201
