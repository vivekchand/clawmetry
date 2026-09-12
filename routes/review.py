"""routes/review.py — decision sampling review surface (issue #1615).

Production-grade monitoring per the OpenClaw blog ("AI Agent Observability
Complete Guide 2026") mandates sampling: a daily cron picks N random
sessions per agent, the reviewer marks each correct / wrong / borderline,
and the dashboard charts accuracy over time. Without sampling users
either skip review entirely (and miss drift) or try to review every
transcript manually (and stop after 3 days). 10 random/day is the
cheapest tier that actually catches drift.

Endpoints
---------
* ``GET  /api/review/queue``           — pending + recently-decided rows
                                         joined with session summary so
                                         the UI renders one row per card.
                                         Carries ``store_available`` so a
                                         caller can tell an empty queue
                                         apart from an unreadable store.
* ``POST /api/review/<session_id>``    — body ``{status, notes}``;
                                         updates the row.
* ``GET  /api/review/accuracy``        — per-agent + global accuracy
                                         over a rolling window
                                         (``?window=30`` days, default 30).
* ``POST /api/review/sample``          — manual trigger of the nightly
                                         sampler (useful for tests + the
                                         "Sample now" button on an empty
                                         queue).

The nightly cron lives in ``sample_yesterday_for_review`` and is invoked
from a daemon background thread in ``clawmetry/sync.py``.
"""

from __future__ import annotations

import os
import random
from datetime import datetime, timedelta, timezone

from flask import Blueprint, jsonify, request

bp_review = Blueprint("review", __name__)


_VALID_STATUSES = frozenset({
    "reviewed_correct", "reviewed_wrong", "reviewed_borderline",
})

# Default sample size per agent per day. Tunable via env so heavy installs
# can dial it up to 25 without a code change; light installs can drop it
# to 5 to avoid review fatigue.
DEFAULT_SAMPLE_SIZE = int(os.environ.get("CLAWMETRY_REVIEW_SAMPLE_SIZE", "10"))


def _env_float(name, default=0.0):
    try:
        return float(os.environ.get(name, "") or default)
    except ValueError:
        return default


# Percentage sampling: review a share of each agent's sessions instead of a
# fixed count (the AgentOps practice is "review 5%"). Off by default so an
# existing install keeps its fixed 10 a day; ``CLAWMETRY_REVIEW_SAMPLE_PCT=5``
# turns it on. Every agent with any session gets at least one row, and
# ``CLAWMETRY_REVIEW_SAMPLE_MAX`` caps a busy agent so the queue stays usable.
DEFAULT_SAMPLE_PCT = _env_float("CLAWMETRY_REVIEW_SAMPLE_PCT", 0.0)
MAX_SAMPLE_PER_AGENT = int(_env_float("CLAWMETRY_REVIEW_SAMPLE_MAX", 200))


def per_agent_quota(pool_size: int, count: int, pct: float) -> int:
    """How many of one agent's ``pool_size`` sessions to sample."""
    if pool_size <= 0:
        return 0
    if pct and pct > 0:
        import math
        want = math.ceil(pool_size * min(float(pct), 100.0) / 100.0)
        return max(1, min(want, max(1, MAX_SAMPLE_PER_AGENT)))
    return max(0, int(count))


def _store_call(method_name, **kwargs):
    """Cross-process LocalStore call with single-process fallback. Mirrors
    the helper used by routes/sessions.py — daemon HTTP proxy first
    (production install), direct open second (tests + dev mode)."""
    try:
        from routes.local_query import local_store_via_daemon
        result = local_store_via_daemon(method_name, **kwargs)
        if result is not None:
            return result
    except Exception:
        pass
    try:
        from clawmetry import local_store
        # read_only=True so a NON-daemon process (the dashboard) never grabs
        # the DuckDB writer lock and starves the sync daemon — that steals the
        # writer during a daemon-restart window and blanks every snapshot read
        # (Models/Embodied go empty). In the daemon get_store(read_only=True)
        # returns the existing writer, so writes here still work; in the
        # dashboard writes go through the daemon proxy above.
        store = local_store.get_store(read_only=True)
        return getattr(store, method_name)(**kwargs)
    except Exception:
        return None


# ── nightly sampler ────────────────────────────────────────────────────────


def sample_yesterday_for_review(
    *,
    sample_size: int | None = None,
    pct: float | None = None,
    now: datetime | None = None,
    rng: random.Random | None = None,
) -> dict:
    """Pick sessions per agent_id from yesterday and insert them into the
    review queue: ``pct`` percent of each agent's sessions when a percentage
    is set (argument, else ``CLAWMETRY_REVIEW_SAMPLE_PCT``), otherwise a
    fixed ``sample_size`` (default ``CLAWMETRY_REVIEW_SAMPLE_SIZE``). An
    explicit ``sample_size`` wins over the env percentage. Idempotent:
    re-running the same day is a no-op because ``ingest_review_sample``
    short-circuits on duplicate session_id. Returns
    ``{sampled, skipped, agents, mode, pct}`` for logging.

    ``now`` + ``rng`` are injectable for deterministic tests.
    """
    if pct is None and sample_size is None:
        pct = DEFAULT_SAMPLE_PCT
    pct = float(pct or 0.0)
    n = int(sample_size or DEFAULT_SAMPLE_SIZE)
    mode = "percent" if pct > 0 else "count"
    if mode == "count" and n <= 0:
        return {"sampled": 0, "skipped": 0, "agents": 0, "mode": mode, "pct": None}
    when = now or datetime.now(timezone.utc)
    rng = rng or random.Random()
    yesterday = (when - timedelta(days=1)).date().isoformat()

    # Pull yesterday's sessions in one shot — the typed sessions table is
    # always small (capped well under the 2000 limit by the daemon).
    rows = _store_call("query_sessions_table", limit=2000) or []

    # Bucket by agent_id, scoping to rows started yesterday so we don't
    # re-sample stale sessions on every nightly tick. ``ingest_review_sample``
    # is idempotent anyway, so a stricter date filter is mostly hygiene —
    # it keeps the per-agent shuffle pool small and the log line honest.
    by_agent: dict[str, list[str]] = {}
    for row in rows:
        started = (row.get("started_at") or row.get("last_active_at") or "")[:10]
        if started != yesterday:
            continue
        sid = row.get("session_id")
        if not sid:
            continue
        by_agent.setdefault(row.get("agent_id") or "main", []).append(sid)

    sampled = 0
    skipped = 0
    for agent_id, session_ids in by_agent.items():
        rng.shuffle(session_ids)
        quota = per_agent_quota(len(session_ids), n, pct)
        for sid in session_ids[:quota]:
            inserted = _store_call(
                "ingest_review_sample",
                sample={
                    "session_id": sid,
                    "agent_id":   agent_id,
                    "sampled_at": when.isoformat(),
                    "status":     "pending",
                },
            )
            if inserted:
                sampled += 1
            else:
                skipped += 1
    return {"sampled": sampled, "skipped": skipped, "agents": len(by_agent),
            "mode": mode, "pct": pct if mode == "percent" else None}


# ── HTTP surface ───────────────────────────────────────────────────────────


@bp_review.route("/api/review/queue", methods=["GET"])
def get_review_queue():
    """Return pending + recently-decided review rows.

    Query params:
      * ``status``  — filter to one status (default: all)
      * ``limit``   — cap rows (default 100)
    """
    status = request.args.get("status") or None
    try:
        limit = int(request.args.get("limit") or 100)
    except (TypeError, ValueError):
        limit = 100
    rows = _store_call(
        "query_review_queue",
        status=status,
        limit=limit,
    )
    # None means the store could not be read at all (the hosted dashboard has
    # no local DuckDB; the daemon proxy can also be briefly down). That is a
    # different fact from "nothing is waiting for you", and a surface that
    # renders them identically tells a cloud user their queue is empty when
    # we simply cannot see it. Callers branch on ``store_available``.
    store_available = rows is not None
    rows = rows or []

    # Decorate with session summary (title + total_tokens) so the UI
    # renders one self-contained card per row without a second fetch.
    sessions = {
        s.get("session_id"): s for s in (
            _store_call("query_sessions_table", limit=2000) or []
        )
    }
    for row in rows:
        sess = sessions.get(row.get("session_id")) or {}
        row["session_summary"] = {
            "title":         sess.get("title"),
            "total_tokens":  sess.get("total_tokens"),
            "cost_usd":      sess.get("cost_usd"),
            "message_count": sess.get("message_count"),
            "started_at":    sess.get("started_at"),
        }
    return jsonify({
        "rows":  rows,
        "count": len(rows),
        "store_available": store_available,
    })


@bp_review.route("/api/review/<session_id>", methods=["POST"])
def post_review_decision(session_id: str):
    """Update the review row with the user's verdict + optional notes."""
    body = request.get_json(silent=True) or {}
    status = body.get("status") or ""
    notes = body.get("notes")
    if status not in _VALID_STATUSES:
        return jsonify({
            "error":   "invalid status",
            "allowed": sorted(_VALID_STATUSES),
        }), 400
    if notes is not None and not isinstance(notes, str):
        return jsonify({"error": "notes must be a string"}), 400
    updated = _store_call(
        "update_review_decision",
        session_id=session_id,
        status=status,
        notes=(notes or None),
    )
    if not updated:
        return jsonify({"error": "session not in review queue"}), 404
    return jsonify({"ok": True, "session_id": session_id, "status": status})


@bp_review.route("/api/review/accuracy", methods=["GET"])
def get_review_accuracy():
    """Per-agent + global accuracy over the trailing window."""
    raw = request.args.get("window") or "30"
    raw = raw.rstrip("d")  # accept "30d" or "30"
    try:
        window = max(1, int(raw))
    except (TypeError, ValueError):
        window = 30
    data = _store_call("query_review_accuracy", window_days=window)
    store_available = data is not None
    if not data:
        data = {
            "window_days": window,
            "global":      {"correct": 0, "wrong": 0, "borderline": 0, "accuracy": None},
            "per_agent":   [],
        }
    # Same distinction as the queue: an unreadable store is not a clean record.
    data["store_available"] = store_available
    return jsonify(data)


@bp_review.route("/api/review/sample", methods=["POST"])
def post_review_sample():
    """Manually trigger the nightly sampler.

    Powers the "Sample now" button on an empty Review tab so the user
    doesn't have to wait until midnight to see the workflow.
    """
    body = request.get_json(silent=True) or {}
    # ``pct`` samples a share of each agent's sessions, ``size`` a fixed
    # count; neither falls back to the node's configured default.
    pct = size = None
    try:
        if body.get("pct") is not None:
            pct = max(0.0, min(100.0, float(body.get("pct"))))
        elif body.get("size") is not None:
            size = int(body.get("size")) or DEFAULT_SAMPLE_SIZE
    except (TypeError, ValueError):
        return jsonify({"error": "pct must be a number from 0 to 100 and size a whole number"}), 400
    result = sample_yesterday_for_review(sample_size=size, pct=pct)
    return jsonify(result)
