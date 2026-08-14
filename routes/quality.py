"""
routes/quality.py — the Quality tab endpoint (redesigned Evals surface).

One endpoint, one question: "is my agent doing good work?". The payload
is intentionally shaped to power the whole tab in a single fetch — grade,
headline, per-day dots, ranked failure patterns, and the rough runs list.

Design note (2026-08-14 redesign — carries clawmetry PR that ships this):
  * Free-tier by design. The grade blends OUTCOME (always available after
    the classifier runs) with the OPTIONAL LLM-judge score, so a fresh
    install with no judge key still gets a real grade from deterministic
    signals. This closes the pre-redesign vaporbox where "Recently Scored
    Sessions" showed "--" on every row until a judge key was set.
  * Never raises. On any storage miss the endpoint returns the honest
    empty-state envelope so the tab renders "Nothing to grade yet."
  * Cloud-safe. On the hosted dashboard the local store is absent; the
    passthrough returns the empty envelope and the tab reads honestly.
    A cm-cloud-quality interceptor can serve a snapshot slice later.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from flask import Blueprint, jsonify, request

bp_quality = Blueprint("quality", __name__)


def _store_via_daemon_or_direct(method_name: str, **kwargs):
    """Daemon HTTP proxy first (writer-lock owner), direct DuckDB fallback,
    None on miss. Same pattern as routes/evals.py:_store_via_daemon_or_direct."""
    try:
        from routes.local_query import local_store_via_daemon
        result = local_store_via_daemon(method_name, **kwargs)
        if result is not None:
            return result
    except Exception:
        pass
    try:
        from clawmetry import local_store
        store = local_store.get_store(read_only=True)
        return getattr(store, method_name)(**kwargs)
    except Exception:
        return None


def _parse_window(raw: str, default_hours: int = 168) -> int:
    """Human-readable window → hours. 1d, 6h, 7d, 30m all work.
    Bounded to [1, 30*24]. Defaults to 7d (a week — the report-card cadence)."""
    raw = (raw or "").strip().lower()
    if not raw:
        return default_hours
    try:
        if raw.endswith("d"):
            hours = int(float(raw[:-1]) * 24)
        elif raw.endswith("h"):
            hours = int(float(raw[:-1]))
        elif raw.endswith("m"):
            hours = max(1, int(float(raw[:-1]) // 60))
        else:
            hours = int(float(raw))
    except (TypeError, ValueError):
        hours = default_hours
    return max(1, min(24 * 30, hours))


def _iso_cutoff(hours: int) -> str:
    return (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat()


@bp_quality.route("/api/quality/report-card", methods=["GET"])
def quality_report_card():
    """Everything the Quality tab renders, in one fetch.

    ``?window=7d`` (default), ``?runtime=<id>`` (optional scope). No auth
    gate — this is the free-tier home for the "is my agent OK?" answer,
    same rationale as /api/evaluators (the shop-menu catalogue) and
    /api/evals/metrics (deterministic verdicts)."""
    window_hours = _parse_window(request.args.get("window", "7d"))
    runtime = (request.args.get("runtime") or "").strip() or None

    since = _iso_cutoff(window_hours)
    prior_since = _iso_cutoff(window_hours * 2)  # for vs_prior diff

    # Pull all-runtime sessions in the window. query_outcomes hard-filters
    # by agent_type, so we ask for one canonical bucket and one supplementary
    # sweep across the family adapters. Cheap: rows are already indexed by
    # last_active_at + agent_type.
    all_rows: list[dict] = []
    prior_rows: list[dict] = []
    agent_types = _known_agent_types()
    for at in agent_types:
        rows = _store_via_daemon_or_direct(
            "query_outcomes",
            agent_type=at,
            since=since,
            runtime=runtime,
            limit=2000,
        ) or []
        # Enrich each row with the runtime tag + judge score if the sessions
        # row carries one. query_outcomes drops eval_score; pull it via a
        # single-shot follow-up per-session in bulk isn't worth it for MVP.
        for r in rows:
            r.setdefault("agent_type", at)
        all_rows.extend(rows)

        prior = _store_via_daemon_or_direct(
            "query_outcomes",
            agent_type=at,
            since=prior_since,
            until=since,
            runtime=runtime,
            limit=2000,
        ) or []
        prior_rows.extend(prior)

    # Bolt on eval_score + eval_reason for the sessions in this window so
    # the grade can blend the judge signal when present. Cheap: one call
    # returns up to 200 rows keyed by session_id.
    _attach_eval_scores(all_rows)

    from clawmetry import quality as _q

    prior_avg = _quick_avg_score(prior_rows)
    payload = _q.compute_report_card(
        all_rows,
        max_patterns=6,
        max_rough_runs=5,
        prior_grade_score=prior_avg,
    )
    payload["window_hours"] = window_hours
    payload["runtime"] = runtime
    payload["week"] = _bucket_week(all_rows, window_hours)
    payload["judge_key_set"] = _judge_key_present()
    return jsonify(payload)


def _known_agent_types() -> list[str]:
    """Canonical agent types ClawMetry tracks. Kept in one list so the
    endpoint sweeps them all without hard-coding the loop. Ordered by
    expected volume so early bucks fill first."""
    return [
        "claude_code",
        "openclaw",
        "codex",
        "cursor",
        "goose",
        "opencode",
        "aider",
        "hermes",
        "picoclaw",
        "nanoclaw",
        "nemoclaw",
        "qwen_code",
        "n8n",
        "antigravity",
        "copilot",
        "deepagents",
        "pi",
    ]


def _attach_eval_scores(rows: list[dict]) -> None:
    """Best-effort: read recent evals + attach eval_score / eval_reason to
    matching session rows. Silent on miss — the grade will fall back to
    outcome-only weighting, which is correct + honest."""
    ids = {str(r.get("session_id")) for r in rows if r.get("session_id")}
    if not ids:
        return
    evals = _store_via_daemon_or_direct(
        "query_recent_evals",
        limit=min(len(ids) + 20, 200),
    ) or []
    by_sid = {str(e.get("session_id")): e for e in evals}
    for r in rows:
        e = by_sid.get(str(r.get("session_id")))
        if e:
            r["eval_score"] = e.get("eval_score")
            r["eval_reason"] = e.get("eval_reason")


def _quick_avg_score(rows: list[dict]) -> float | None:
    """The average of the "prior" window's session scores, used for the
    vs_prior arrow in the headline (down from a C+ last week)."""
    if not rows:
        return None
    from clawmetry.quality import _session_score
    scores = [_session_score(r) for r in rows]
    scores = [s for s in scores if s is not None]
    if not scores:
        return None
    return sum(scores) / len(scores)


def _bucket_week(rows: list[dict], window_hours: int) -> list[dict]:
    """Bucket session scores into per-day grades for the trend dots.
    Days with no runs get a null grade so the UI can render an empty dot.
    Emits at most 7 days (or fewer if the window is shorter)."""
    from collections import defaultdict
    from clawmetry.quality import _session_score, grade_for

    days = min(7, max(1, window_hours // 24 or 1))
    now = datetime.now(timezone.utc).date()
    buckets: dict[str, list[float]] = defaultdict(list)

    for r in rows:
        ts = (r.get("last_active_at") or r.get("ended_at")
              or r.get("started_at") or "")
        if not ts:
            continue
        try:
            d = datetime.fromisoformat(str(ts).replace("Z", "+00:00")).date()
        except (ValueError, TypeError):
            continue
        s = _session_score(r)
        if s is None:
            continue
        buckets[d.isoformat()].append(s)

    out: list[dict] = []
    for i in range(days - 1, -1, -1):
        d = now - timedelta(days=i)
        scores = buckets.get(d.isoformat(), [])
        avg = sum(scores) / len(scores) if scores else None
        out.append({
            "date":  d.isoformat(),
            "label": ("Today" if i == 0
                      else ("Yesterday" if i == 1
                            else d.strftime("%a"))),
            "grade": grade_for(avg) if avg is not None else "—",
            "runs":  len(scores),
        })
    return out


@bp_quality.route("/api/quality/checks", methods=["POST"])
def quality_checks_save():
    """Save an eval check built from a real rough run — the aha moment
    from the 2026-08-14 redesign: pick a real trace, turn it into a
    "next time this happens, fail-fast" rule.

    v1 scope (this release): validate + persist the check to
    ``~/.clawmetry/quality_checks.jsonl`` (append-only, chmod 600) and
    return ``{ok: true, id, deferred_enforcement: true}``. The runner
    that acts on saved checks (fail-fast at ingest, alert on match)
    lands in the follow-up PR — the UI already surfaces "Saved locally.
    Live enforcement lands in the next release." so users see what shipped
    and what's coming.

    Body: ``{session_id, name, fail_when}``. All three are strings; the
    endpoint never raises on bad input — returns 400 with a plain error.
    """
    body = request.get_json(silent=True) or {}
    fail_when = (body.get("fail_when") or "").strip()
    name = (body.get("name") or "").strip()
    session_id = (body.get("session_id") or "").strip()
    if not fail_when:
        return jsonify({"ok": False, "error": "fail_when required"}), 400
    if not name:
        # Auto-name from the first few words so a user who skipped naming
        # still gets a persisted, addressable check.
        name = " ".join(fail_when.split()[:4]).rstrip(",.") or "Untitled check"

    from datetime import datetime, timezone
    import hashlib
    ts = datetime.now(timezone.utc).isoformat()
    stable_id = hashlib.sha256((name + "|" + fail_when).encode("utf-8")).hexdigest()[:12]

    record = {
        "id":                    stable_id,
        "name":                  name[:120],
        "fail_when":             fail_when[:500],
        "source_session_id":     session_id[:200],
        "created_at":            ts,
        "deferred_enforcement":  True,
    }
    try:
        _append_check_record(record)
    except Exception as e:
        return jsonify({"ok": False, "error": f"persist failed: {e}"}), 500
    return jsonify({
        "ok":                   True,
        "id":                   stable_id,
        "deferred_enforcement": True,
        "message":              "Saved locally. Live enforcement lands in the next release.",
    })


def _append_check_record(record: dict) -> None:
    """chmod-600 append to ~/.clawmetry/quality_checks.jsonl. Creates the
    parent directory on first save. Never raises past its caller."""
    import json, os
    from pathlib import Path
    home = Path(os.environ.get("HOME") or os.path.expanduser("~"))
    d = home / ".clawmetry"
    d.mkdir(parents=True, exist_ok=True)
    p = d / "quality_checks.jsonl"
    # Open with restrictive mode on first write; existing files keep perms.
    exists = p.exists()
    with p.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, separators=(",", ":")) + "\n")
    if not exists:
        try:
            os.chmod(p, 0o600)
        except OSError:
            pass


def _judge_key_present() -> bool:
    """Cheap check for judge key presence so the footer nudge can hide
    when the user already turned scoring on. Never raises."""
    try:
        from clawmetry import eval_runner
        keys = eval_runner.judge_keys_present() or {}
        return any(bool(v) for v in keys.values())
    except Exception:
        return False
