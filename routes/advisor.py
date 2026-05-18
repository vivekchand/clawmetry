"""
routes/advisor.py -- ClawMetry Advisor: natural-language Q&A over your agent.

A conversational layer on top of the data the dashboard already collects.
Users ask questions like "why did my last run cost so much?" or "which tool
is failing most often?" and get an answer with the relevant events cited.

Auth strategy (zero-config preferred, env-var fallback):
  1. Re-use OpenClaw's existing anthropic OAuth profile from
     `~/.openclaw/agents/main/agent/auth-profiles.json`. Most users already
     have this set up via `claude` CLI -- nothing new to configure.
  2. Fall back to `ANTHROPIC_API_KEY` env var for users who skipped that.
  3. If neither is present, return a structured 412 with setup instructions.

This is OSS-side only. The cloud counterpart can later proxy through a
managed key for Pro users -- not required for the local experience.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import time
import urllib.error
import urllib.request

from flask import Blueprint, jsonify, request
from clawmetry.config import is_local_store_read_enabled

bp_advisor = Blueprint("advisor", __name__)

ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"
ANTHROPIC_VERSION = "2023-06-01"
DEFAULT_MODEL = "claude-opus-4-5-20250929"
FALLBACK_MODEL = "claude-haiku-4-5-20251001"
MAX_CONTEXT_EVENTS = 40
MAX_ANSWER_TOKENS = 800
REQUEST_TIMEOUT_SEC = 30


# ── Auth ──────────────────────────────────────────────────────────────────────


def _read_anthropic_key_from_openclaw_config() -> str | None:
    """Best-effort scan of OpenClaw's config + insights store for an
    Anthropic API key the operator has already set up.

    We only look in well-known dashboard-managed JSON files; we never
    parse arbitrary user config blobs. Order is most-specific to most-
    general so a per-feature key (insights) wins over a global plugin
    key.

    Returns the raw key string or ``None`` if nothing usable is found.
    The key never leaves the process via /api/* responses (the only
    caller is the LLM dispatcher).
    """
    candidates: list[str] = []

    # 1. Insights config -- the user may have pasted a key here already.
    try:
        ins_path = os.path.expanduser(
            "~/.openclaw/.clawmetry/insights_config.json"
        )
        if os.path.isfile(ins_path):
            with open(ins_path) as f:
                cfg = json.load(f)
            k = (cfg.get("anthropic_api_key") or "").strip()
            if k:
                candidates.append(k)
    except Exception:
        pass

    # 2. OpenClaw root config -- gateway-pooled key paths used by the
    # anthropic plugin. We probe a small, conservative set of paths
    # rather than walking the whole tree; new ones can be added as we
    # discover them across installs.
    try:
        oc_path = os.path.expanduser("~/.openclaw/openclaw.json")
        if os.path.isfile(oc_path):
            with open(oc_path) as f:
                oc = json.load(f)
            probes = (
                ((oc.get("plugins") or {}).get("entries") or {}).get("anthropic") or {},
                ((oc.get("providers") or {}).get("anthropic") or {}),
                ((oc.get("auth") or {}).get("profiles") or {}).get("anthropic:api-key") or {},
            )
            for blob in probes:
                if not isinstance(blob, dict):
                    continue
                for field in ("apiKey", "api_key", "key", "token"):
                    v = blob.get(field)
                    if isinstance(v, str) and v.strip().startswith("sk-"):
                        candidates.append(v.strip())
    except Exception:
        pass

    return candidates[0] if candidates else None


def _load_anthropic_auth() -> tuple[str | None, str | None]:
    """Return (mode, credential).

    mode is one of:
      - "api_key"     : direct /v1/messages call with an Anthropic API key
                        (from ANTHROPIC_API_KEY, the Insights config, or
                        an OpenClaw plugin/provider config)
      - "claude_cli"  : shell out to `claude -p`; uses whatever OpenClaw's
                        claude-cli profile is already authenticated with
                        (works for OAuth users with no extra config)
      - None          : nothing configured; UI shows a single-line hint
                        instead of a blocking modal
    """
    # 1. Explicit env var wins -- operator-controlled, easy to override.
    api_key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    if api_key:
        return "api_key", api_key

    # 2. Auto-detect a key the user already configured in OpenClaw / the
    # dashboard's Insights tab. This is the "show some magic" path: a
    # fresh dashboard user who already has OpenClaw running with a key
    # gets Self-Evolve / Advisor working with zero extra input.
    auto_key = _read_anthropic_key_from_openclaw_config()
    if auto_key:
        return "api_key", auto_key

    # 3. claude CLI OAuth fallback. The binary uses whatever profile the
    # user already authenticated, so OAuth-only users still work.
    claude_bin = shutil.which("claude")
    if claude_bin:
        profile_path = os.path.expanduser(
            "~/.openclaw/agents/main/agent/auth-profiles.json"
        )
        has_profile = False
        if os.path.isfile(profile_path):
            try:
                with open(profile_path) as f:
                    data = json.load(f)
                has_profile = bool(
                    (data.get("profiles") or {}).get("anthropic:claude-cli", {}).get("access")
                )
            except Exception:
                pass
        # Only return claude_cli if the binary AND an OAuth profile exist.
        # Without the profile `claude -p` would prompt interactively, which
        # hangs the HTTP request.
        if has_profile:
            return "claude_cli", claude_bin

    return None, None


# ── Context assembly ──────────────────────────────────────────────────────────


def _summarise_event(ev: dict) -> str:
    """Compress a brain event into a single readable line for LLM context."""
    t = (ev.get("time") or ev.get("timestamp") or "")[:19]
    typ = ev.get("type") or "?"
    src = ev.get("source") or ev.get("sourceLabel") or "main"
    detail = ev.get("detail") or ""
    if isinstance(detail, (dict, list)):
        detail = json.dumps(detail)[:160]
    detail = str(detail).replace("\n", " ")[:200]
    return f"[{t}] {src} {typ}: {detail}"


def _try_local_store_advisor_context(limit_events: int = MAX_CONTEXT_EVENTS) -> dict | None:
    """Tier-1 DuckDB fast path for advisor context assembly.

    Reads recent events directly from the local store and emits the same
    ``{events, usage, recent_sessions, _source}`` shape ``_gather_context``
    produces from JSONL+brain-history. Used when CLAWMETRY_LOCAL_STORE_READ=1
    is set so the advisor stays on the same data plane the rest of the
    fast-path-enabled dashboard uses.

    Returns ``None`` to defer to the legacy gather when:
      - the ``local_store`` module isn't importable
      - the events table is empty
      - any unexpected error happens (we'd rather degrade than 500)
    """
    # Issue #1282 / memory `feedback_daemon_proxy_pattern.md`: the sync
    # daemon holds an exclusive writer lock on the DuckDB file in the
    # multi-process install case (launchd/systemd), so a direct
    # ``local_store.get_store()`` open here races the daemon and either
    # raises ``IOException`` or hangs. Ask the daemon over HTTP first;
    # fall back to a direct read-only open for single-process boots
    # (tests, dev mode).
    try:
        from routes.local_query import local_store_via_daemon
        rows = local_store_via_daemon("query_events", limit=limit_events)
    except Exception:
        rows = None
    if rows is None:
        try:
            from clawmetry import local_store
            store = local_store.get_store(read_only=True)
            rows = store.query_events(limit=limit_events)
        except Exception:
            return None
    if not rows:
        return None

    events: list[str] = []
    sessions_seen: dict[str, dict] = {}
    today_str = time.strftime("%Y-%m-%d")
    today_tokens = 0

    # Issue #1451: dedupe sibling-doubled billable turns before counting
    # tokens. On real OpenClaw v3 installs each LLM turn emits BOTH an
    # ``assistant`` and a sibling ``model.completed`` row ~100 ms apart,
    # both stamped with the same ``token_count`` value. Without dedup
    # per-session totals + today_tokens come out 2× reality and the
    # advisor's recommendations are based on inflated numbers. Shared
    # helper in ``routes/_dedupe.py``.
    from routes._dedupe import build_sibling_bucket_max, is_sibling_dup
    _bucket_max = build_sibling_bucket_max(rows)

    for r in rows:
        t = (r.get("ts") or "")[:19]
        typ = r.get("event_type") or "?"
        sid = r.get("session_id") or "main"
        data = r.get("data") if isinstance(r, dict) else None
        if isinstance(data, dict):
            detail = (data.get("input") or data.get("summary")
                      or data.get("text") or data.get("name") or "")
        elif isinstance(data, str):
            detail = data
        else:
            detail = ""
        if isinstance(detail, (dict, list)):
            try:
                detail = json.dumps(detail)[:160]
            except Exception:
                detail = str(detail)[:160]
        detail = str(detail).replace("\n", " ")[:200]
        events.append(f"[{t}] {sid[:12]} {typ}: {detail}")

        sid_key = r.get("session_id") or ""
        # Issue #1451: skip token + cost accumulation when this row is the
        # slim sibling of a richer envelope we already counted. We still
        # populate sessions_seen metadata (model, started_at) since those
        # are tag-set not totals.
        _is_dup = is_sibling_dup(r, _bucket_max)
        if sid_key:
            entry = sessions_seen.setdefault(sid_key, {
                "session_id": sid_key[:8],
                "model": r.get("model") or "",
                "tokens": 0,
                "cost_usd": 0.0,
                "started_at": t,
            })
            if not _is_dup:
                entry["tokens"] += int(r.get("token_count") or 0)
                try:
                    entry["cost_usd"] = round(entry["cost_usd"] + float(r.get("cost_usd") or 0), 4)
                except Exception:
                    pass
            if r.get("model") and not entry["model"]:
                entry["model"] = r["model"]
            if t and (not entry["started_at"] or t < entry["started_at"]):
                entry["started_at"] = t
        if t.startswith(today_str) and not _is_dup:
            today_tokens += int(r.get("token_count") or 0)

    return {
        "events": events[-limit_events:],
        "usage": {
            "today_tokens": today_tokens,
            "total_sessions": len(sessions_seen),
        },
        "recent_sessions": list(sessions_seen.values())[:8],
        "_source": "local_store",
    }


def _gather_context(limit_events: int = MAX_CONTEXT_EVENTS) -> dict:
    """Pull a compact snapshot of the user's current agent state.

    Reuses the same primitives the Brain and Tokens tabs already render --
    nothing new computed, just packaged for the LLM.
    """
    import dashboard as _d

    # Tier-1 DuckDB fast path — opt-in via CLAWMETRY_LOCAL_STORE_READ=1.
    # The legacy gather already calls into the brain endpoint (which has its
    # own fast path), but this short-circuit keeps the advisor on a single
    # data plane and avoids the cross-route Flask test_request_context dance
    # when the local store is the source of truth.
    if is_local_store_read_enabled():
        fast = _try_local_store_advisor_context(limit_events)
        if fast is not None:
            return fast

    out: dict = {"events": [], "usage": {}, "errors": []}

    # Recent brain events via the existing analytics
    try:
        analytics = _d._compute_transcript_analytics()
        sessions = analytics.get("sessions") or []
        # Most-recently-updated sessions, summarised
        sessions.sort(key=lambda s: s.get("updated_ts") or 0, reverse=True)
        out["recent_sessions"] = [
            {
                "session_id": s.get("session_id", "")[:8],
                "model": s.get("model", ""),
                "tokens": s.get("tokens", 0),
                "cost_usd": round(float(s.get("cost_usd", 0) or 0), 4),
                "started_at": s.get("start_iso", ""),
            }
            for s in sessions[:8]
        ]
        out["usage"] = {
            "today_tokens": sum(
                s.get("tokens", 0)
                for s in sessions
                if (s.get("start_iso") or "")[:10] == time.strftime("%Y-%m-%d")
            ),
            "total_sessions": len(sessions),
        }
    except Exception as e:
        out["analytics_error"] = str(e)[:200]

    # Tail the unified Brain feed for last few events
    try:
        from routes.brain import api_brain_history
        # Call the route function directly -- it returns a Flask Response
        with _d.app.test_request_context(
            "/api/brain-history?limit=" + str(limit_events)
        ):
            resp = api_brain_history()
            payload = resp.get_json() if hasattr(resp, "get_json") else None
        if payload and isinstance(payload.get("events"), list):
            out["events"] = [
                _summarise_event(ev)
                for ev in payload["events"][-limit_events:]
            ]
    except Exception as e:
        out["brain_error"] = str(e)[:200]

    return out


def _build_prompt(question: str, ctx: dict) -> str:
    """Compose the user-facing question with assembled context."""
    parts: list[str] = []
    parts.append("Recent agent activity (most recent last):")
    for line in ctx.get("events", []):
        parts.append("  " + line)
    if ctx.get("recent_sessions"):
        parts.append("")
        parts.append("Recent sessions:")
        for s in ctx["recent_sessions"]:
            parts.append(
                f"  - {s['session_id']} model={s['model']} "
                f"tokens={s['tokens']} cost=${s['cost_usd']} "
                f"started={s['started_at']}"
            )
    if ctx.get("usage"):
        u = ctx["usage"]
        parts.append("")
        parts.append(
            f"Usage today: {u.get('today_tokens', 0)} tokens across "
            f"{u.get('total_sessions', 0)} sessions"
        )
    parts.append("")
    parts.append("Question: " + question)
    return "\n".join(parts)


SYSTEM_PROMPT = (
    "You are ClawMetry Advisor. You help operators of OpenClaw AI agents "
    "understand what their agents are doing, why a run cost what it did, "
    "which tools are failing, and what to fix next. "
    "You are reading the operator's own dashboard data. "
    "Answer in 2-4 short paragraphs. Cite specific events or sessions by id. "
    "If the data is insufficient to answer, say so explicitly and suggest "
    "what the operator should look at next."
)


# ── LLM call ──────────────────────────────────────────────────────────────────


def _call_anthropic_api(
    api_key: str,
    prompt: str,
    system: str | None = None,
    max_tokens: int = MAX_ANSWER_TOKENS,
    timeout: int = REQUEST_TIMEOUT_SEC,
) -> dict:
    """Direct call to /v1/messages with a real ANTHROPIC_API_KEY."""
    body = {
        "model": DEFAULT_MODEL,
        "max_tokens": max_tokens,
        "system": system or SYSTEM_PROMPT,
        "messages": [{"role": "user", "content": prompt}],
    }
    headers = {
        "Content-Type": "application/json",
        "anthropic-version": ANTHROPIC_VERSION,
        "x-api-key": api_key,
    }
    req = urllib.request.Request(
        ANTHROPIC_URL,
        data=json.dumps(body).encode("utf-8"),
        headers=headers,
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8", errors="replace")
        return {"_error": True, "status": e.code, "body": raw[:500]}
    except Exception as e:
        return {"_error": True, "status": 0, "body": str(e)[:500]}


def _call_via_claude_cli(
    claude_bin: str,
    prompt: str,
    system: str | None = None,
    timeout: int = REQUEST_TIMEOUT_SEC,
) -> dict:
    """Shell out to `claude -p` so OAuth-only users still work.

    Normalise the response into the same shape `_call_anthropic_api`
    returns (content blocks + usage) so the endpoint stays uniform.
    """
    full_prompt = (system or SYSTEM_PROMPT) + "\n\n---\n\n" + prompt
    try:
        proc = subprocess.run(
            [claude_bin, "-p"],
            input=full_prompt,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return {"_error": True, "status": 504, "body": "claude CLI timed out"}
    except Exception as e:
        return {"_error": True, "status": 0, "body": str(e)[:500]}

    if proc.returncode != 0:
        err = (proc.stderr or proc.stdout or "").strip()
        return {"_error": True, "status": proc.returncode, "body": err[:500]}

    answer_text = (proc.stdout or "").strip()
    return {
        "model": "claude-cli",
        "content": [{"type": "text", "text": answer_text}],
        "usage": {"input_tokens": 0, "output_tokens": 0},
    }


def _extract_answer(api_response: dict) -> str:
    if api_response.get("_error"):
        return ""
    blocks = api_response.get("content") or []
    parts = [b.get("text", "") for b in blocks if isinstance(b, dict)]
    return "".join(parts).strip()


# ── Endpoint ──────────────────────────────────────────────────────────────────


@bp_advisor.route("/api/advisor/ask", methods=["POST"])
def api_advisor_ask():
    payload = request.get_json(silent=True) or {}
    question = (payload.get("question") or "").strip()
    if not question:
        return jsonify({"error": "Provide a non-empty 'question' field."}), 400
    if len(question) > 1000:
        return jsonify({"error": "Question too long (1000 char limit)."}), 400

    mode, credential = _load_anthropic_auth()
    if not credential:
        return (
            jsonify(
                {
                    "error": "no_auth",
                    "message": (
                        "Advisor needs an Anthropic credential. "
                        "Either run `claude` CLI to set up OAuth, "
                        "or export ANTHROPIC_API_KEY in your shell."
                    ),
                }
            ),
            412,
        )

    ctx = _gather_context()
    prompt = _build_prompt(question, ctx)
    if mode == "claude_cli":
        resp = _call_via_claude_cli(credential, prompt)
    else:
        resp = _call_anthropic_api(credential, prompt)

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

    answer = _extract_answer(resp)
    usage = resp.get("usage") or {}
    body = {
        "answer": answer or "(no answer returned)",
        "model": resp.get("model", DEFAULT_MODEL),
        "input_tokens": usage.get("input_tokens", 0),
        "output_tokens": usage.get("output_tokens", 0),
        "events_in_context": len(ctx.get("events", [])),
    }
    # Surface the data-plane the advisor used so audits/UIs can confirm
    # the advisor is on the local store when the fast path was taken.
    if ctx.get("_source") == "local_store":
        body["_source"] = "local_store"
    return jsonify(body)


def _try_local_store_advisor_status() -> dict | None:
    """Tier-1 DuckDB fast path for /api/advisor/status.

    Returns the probe payload tagged ``_source: local_store`` when the
    local store is reachable. The status probe doesn't actually need event
    data — it's auth-presence only — but we still surface the fast-path
    flag so the UI/audits can confirm the advisor is on the local plane.

    Returns ``None`` to defer when local_store import fails or any error.
    """
    # Issue #1282: read-only smoke probe. Daemon-proxy first (no lock
    # contention with the writer); direct read-only open as fallback for
    # single-process boots.
    try:
        from routes.local_query import local_store_via_daemon
        local_store_via_daemon("query_events", limit=1)
    except Exception:
        try:
            from clawmetry import local_store
            local_store.get_store(read_only=True)
        except Exception:
            return None
    mode, credential = _load_anthropic_auth()
    return {
        "available": bool(credential),
        "auth_mode": mode or "none",
        "model":     DEFAULT_MODEL,
        "_source":   "local_store",
    }


@bp_advisor.route("/api/advisor/status")
def api_advisor_status():
    """Cheap probe so the UI can decide whether to show the input."""
    if is_local_store_read_enabled():
        fast = _try_local_store_advisor_status()
        if fast is not None:
            return jsonify(fast)
    mode, credential = _load_anthropic_auth()
    return jsonify(
        {
            "available": bool(credential),
            "auth_mode": mode or "none",
            "model": DEFAULT_MODEL,
        }
    )
