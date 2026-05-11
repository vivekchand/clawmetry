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
    detail = str(ev.get("detail") or "").lower()
    is_error = (
        "error" in detail
        or "failed" in detail
        or "timeout" in detail
        or typ == "error"
    )
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
    "telemetry and propose concrete improvements. Focus on findings the "
    "operator can act on today: a failing tool, a model overused relative "
    "to its value, a prompt burning tokens without progress, a looping "
    "path, a cost trend that will break their budget. "
    "Return STRICT JSON only, no preamble, no markdown fences. Shape: "
    '{"findings":[{"category":"cost|reliability|latency|prompt|model|loop",'
    '"severity":"high|medium|low","title":"...","evidence":"cite specific '
    'numbers/events from the data","suggestion":"one concrete action"}]}. '
    f"At most {MAX_FINDINGS} findings, ordered by severity. If the data is "
    "too sparse to draw any conclusion, return "
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
    return jsonify(
        {
            "available": bool(credential),
            "auth_mode": mode or "none",
            "has_cached": bool(cached),
            "cached_at": (cached or {}).get("generated_at"),
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
                        "Self-Evolve needs an Anthropic credential. "
                        "Run `claude` CLI to set up OAuth, "
                        "or export ANTHROPIC_API_KEY."
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
