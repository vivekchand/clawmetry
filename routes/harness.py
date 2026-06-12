"""``bp_harness`` — the per-harness custom-tab API.

Two read-only endpoints back the "Harness" tab:

* ``GET /api/harness/templates`` — the registered harness templates
  (``{runtime: template}``). OSS ships openclaw + nemoclaw; clawmetry-pro
  registers its 10 closed templates through the plugin seam, so this endpoint
  returns exactly what the running node is entitled to render.
* ``GET /api/harness/data?runtime=<rt>`` — the per-runtime data blob the
  template's ``source`` paths resolve against (summary + recent sessions, plus
  room for adapter-``extra`` aggregates as the gap issues land). Cloud-safe:
  reads DuckDB through ``routes.local_query._dispatch`` (the daemon proxy), not
  raw files, so it works in the cloud container too.
"""
from __future__ import annotations

import logging

from flask import Blueprint, jsonify, request

logger = logging.getLogger("clawmetry.routes.harness")

bp_harness = Blueprint("harness", __name__)

# Session-id prefix → runtime. Mirrors ``_NON_OPENCLAW_RUNTIME_PREFIXES`` in
# clawmetry/local_store.py (agent_type is always "openclaw"; the runtime is the
# session_id prefix). nemoclaw is a free OpenClaw wrapper that tags its sessions
# with a ``nemoclaw:`` prefix; everything without a known prefix is OpenClaw.
_NON_OPENCLAW_PREFIXES = frozenset({
    "picoclaw", "nanoclaw", "hermes", "nemoclaw",
    "claude_code", "codex", "cursor", "aider", "goose", "opencode", "qwen_code",
})


def _prefix_of(session_id: str) -> str:
    if not session_id or ":" not in session_id:
        return "openclaw"
    head = session_id.split(":", 1)[0]
    return head if head in _NON_OPENCLAW_PREFIXES else "openclaw"


def _runtime_match(session_id: str, runtime: str) -> bool:
    """Does ``session_id`` belong to ``runtime``? openclaw = anything without a
    known non-openclaw prefix; otherwise an exact prefix match."""
    return _prefix_of(session_id) == (runtime or "openclaw").lower()


def _num(v) -> float:
    try:
        return float(v or 0)
    except (TypeError, ValueError):
        return 0.0


@bp_harness.route("/api/harness/templates", methods=["GET"])
def http_harness_templates():
    """Registered harness templates the node is entitled to render."""
    try:
        from clawmetry import harness_templates as _ht
        tmpls = _ht.all_templates()
        return jsonify({"templates": tmpls, "runtimes": sorted(tmpls.keys())})
    except Exception as exc:  # never crash the tab
        logger.warning("harness templates failed: %s", exc)
        return jsonify({"templates": {}, "runtimes": []})


@bp_harness.route("/api/harness/data", methods=["GET"])
def http_harness_data():
    """Per-runtime data blob the template ``source`` paths resolve against.

    Shape (the source mini-DSL maps onto this):
        {
          "runtime": "goose",
          "summary": {"sessions": N, "cost_usd": X, "tokens": T},
          "sessions": [{session_id, session_type, started_at, ended_at,
                        cost_usd, tokens}, ...],   # newest first, capped
          "extra": { ... }   # runtime-wide adapter-extra aggregates (grows as
                             # the harness-observability gap issues land)
        }
    """
    runtime = (request.args.get("runtime") or "openclaw").strip().lower()
    return jsonify(_harness_data_for(runtime))


def _harness_data_for(runtime):
    """Compute the per-runtime harness data blob, shared by the HTTP route and
    the cloud snapshot builder (trial-bug #10: the Harness tab was blank on the
    hosted dashboard). Never raises; returns the dict."""
    runtime = (runtime or "openclaw").strip().lower()
    blob = {"runtime": runtime, "summary": {"sessions": 0, "cost_usd": 0.0, "tokens": 0},
            "sessions": [], "extra": {}}
    try:
        from routes.local_query import _dispatch
        body = _dispatch("sessions", {"limit": 500})
        rows = body.get("rows") or body.get("sessions") or []
    except Exception as exc:
        logger.warning("harness data dispatch failed: %s", exc)
        return blob

    mine = [r for r in rows if _runtime_match(r.get("session_id", ""), runtime)]
    total_cost = sum(_num(r.get("cost_usd")) for r in mine)
    total_tok = sum(_num(r.get("token_count", r.get("tokens"))) for r in mine)

    def _sort_key(r):
        return r.get("updated_at") or r.get("ended_at") or r.get("started_at") or ""

    mine.sort(key=_sort_key, reverse=True)

    # Per-session adapter `extra` + runtime-wide aggregates, harvested from the
    # events stream (the adapters stash their unique surface in event/session
    # `data.extra` — goose scheduleId/recipe, codex cliVersion/rolloutFile,
    # claude_code cache-token splits, …). Reusing the cloud-safe `events`
    # dispatch means no new store code and this works in the cloud container.
    per_session_extra, models = _harvest_event_extra(runtime)

    sessions = [{
        "session_id": r.get("session_id", ""),
        "session_type": r.get("session_type") or r.get("agent_id") or "",
        "started_at": r.get("started_at", ""),
        "ended_at": r.get("updated_at") or r.get("ended_at") or "",
        "cost_usd": round(_num(r.get("cost_usd")), 4),
        "tokens": int(_num(r.get("token_count", r.get("tokens")))),
        "extra": per_session_extra.get(r.get("session_id", ""), {}),
    } for r in mine[:50]]

    blob["summary"] = {
        "sessions": len(mine),
        "cost_usd": round(total_cost, 4),
        "tokens": int(total_tok),
    }
    blob["sessions"] = sessions
    if models:
        blob["extra"]["models"] = models
    return blob


def _harvest_event_extra(runtime: str):
    """Aggregate per-session ``data.extra`` (last value wins per key) and the
    distinct models seen, from the runtime's recent events. Returns
    ``({session_id: extra_dict}, [models])``. Never raises — returns empties."""
    import json
    per_session: dict = {}
    models: list = []
    seen_models: set = set()
    try:
        from routes.local_query import _dispatch
        body = _dispatch("events", {"limit": 2000})
        rows = body.get("rows") or []
    except Exception as exc:
        logger.warning("harness extra harvest failed: %s", exc)
        return per_session, models
    for r in rows:
        sid = r.get("session_id", "")
        if not _runtime_match(sid, runtime):
            continue
        m = r.get("model")
        if m and m not in seen_models:
            seen_models.add(m)
            models.append(m)
        d = r.get("data")
        if isinstance(d, str):
            try:
                d = json.loads(d)
            except Exception:
                d = None
        ex = d.get("extra") if isinstance(d, dict) else None
        if isinstance(ex, dict) and ex:
            bucket = per_session.setdefault(sid, {})
            for k, v in ex.items():
                # keep concise, JSON-friendly scalars; skip the noisy token
                # split keys that already have first-class tiles
                if k in ("inputTokens", "outputTokens", "cacheReadInputTokens",
                         "cacheCreationInputTokens"):
                    continue
                if isinstance(v, (str, int, float, bool)) or v is None:
                    bucket[k] = v
    return per_session, models
