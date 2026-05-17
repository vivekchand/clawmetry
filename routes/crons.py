"""
routes/crons.py — Cron CRUD + health + run-log endpoints.

Extracted from dashboard.py as Phase 5.4 of the incremental modularisation.
Owns the 13 routes registered on bp_crons:

  GET  /api/crons                     — job list with cost attribution
  POST /api/cron/fix                  — submit AI fix request
  POST /api/cron/run                  — trigger a run via gateway
  POST /api/cron/toggle               — enable/disable a job
  POST /api/cron/delete               — remove a job
  POST /api/cron/update               — patch a job
  POST /api/cron/create               — create a new job
  GET  /api/cron/<job_id>/runs        — run history with p50/p95 stats
  POST /api/cron/<job_id>/kill        — disable a single job
  GET  /api/cron-run-log              — session transcript for a run
  GET  /api/cron/health-summary       — per-job health, costs, anomalies
  POST /api/cron/kill-all             — emergency disable all jobs
  GET  /api/cron-health               — normalised health shape (GH #306)

Module-level helpers (``_gw_invoke``, ``_get_crons``, ``_get_sessions_dir``,
``_compute_transcript_analytics``, ``_score_cron_match``, ``_ext_emit``,
``_budget_paused``, ``_enrich_cron_runs``, ``_cron_runs_from_transcripts``,
``app``) stay in ``dashboard.py`` and are reached via late
``import dashboard as _d``. Pure mechanical move — zero behaviour change.
"""

import json
import os
from collections import defaultdict
from datetime import datetime

from flask import Blueprint, jsonify, request
from clawmetry.config import is_local_store_read_enabled

bp_crons = Blueprint('crons', __name__)


# ── Local DuckDB fast path (epic #964 phase 4 — Crons tab) ──────────────────
#
# Opt-in via CLAWMETRY_LOCAL_STORE_READ=1. Mirrors the same pattern used by
# routes/sessions.py and routes/heartbeat.py: a dedicated helper attempts a
# DuckDB read and returns ``None`` on any error / empty table so the legacy
# gateway/JSONL path runs untouched. Fast paths NEVER replace the legacy
# code — they sit *in front of it*, so a fresh install with no local store
# (or a non-OpenClaw user) sees the same data as before.
#
# The local ``crons`` table is populated by sync.py via LocalStore.ingest_cron
# (Engineer B's missing-writers PR #1045). Schema:
#
#   crons (
#     agent_type, cron_id, agent_id, name, schedule, enabled,
#     last_run_at, last_status, next_run_at, data BLOB, updated_at
#   )
#
# We deliberately keep the fast-path response shape identical to the
# gateway-backed contract — only adding a ``_source: "local_store"`` tag so
# tests can assert which path served the response.


def _ls_call(method_name, **kwargs):
    """Cross-process LocalStore call with single-process fallback.

    Issue #1088: every direct ``get_store().query_*`` call is dead code in
    the standard install (daemon owns the writer lock, dashboard's open
    raises ``IOException: Could not set lock``). This wrapper hits the
    daemon's HTTP proxy first, then falls back to direct open for
    single-process boots (tests + dev mode). Returns ``None`` on miss so
    callers can defer to the legacy fallback path.
    """
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


def _parse_iso_to_ms(ts):
    """Best-effort ISO-8601 → epoch-ms. Returns 0 on any failure."""
    if not ts:
        return 0
    if isinstance(ts, (int, float)):
        return int(ts)
    if isinstance(ts, str):
        try:
            from datetime import datetime as _dt
            return int(_dt.fromisoformat(ts.replace("Z", "+00:00")).timestamp() * 1000)
        except Exception:
            try:
                from dateutil import parser as _dtp
                return int(_dtp.parse(ts).timestamp() * 1000)
            except Exception:
                return 0
    return 0


def _row_to_cron_job(row):
    """Convert a DuckDB ``crons`` row (as returned by ``query_crons``) into
    the gateway-shaped job dict that the dashboard JS / cost-attribution
    code expects:

        {id, name, schedule, enabled, createdAtMs,
         state: {lastRunAtMs, lastStatus, nextRunAtMs, ...}}

    Extras stashed in the freeform ``data`` blob (createdAtMs, runHistory,
    consecutiveFailures, lastDurationMs, lastError, sched-extras, ...) are
    spliced through. ``schedule`` may be a JSON-encoded string in the
    column — try to decode so the JS gets a dict.
    """
    state_extras = {}
    extras = row.get("data") if isinstance(row.get("data"), dict) else {}
    # Pull state-shaped fields out of the data blob if present.
    for k in (
        "lastDurationMs", "consecutiveFailures", "lastError",
        "runHistory", "lastCostUsd",
    ):
        if k in extras:
            state_extras[k] = extras[k]

    schedule = row.get("schedule")
    if isinstance(schedule, str):
        # gateway returns schedule as a dict; if our store has a JSON string
        # (or a cron expression) try to decode → dict, else keep as-is.
        try:
            decoded = json.loads(schedule)
            if isinstance(decoded, dict):
                schedule = decoded
        except Exception:
            pass
    if schedule is None and isinstance(extras.get("schedule"), (dict, str)):
        schedule = extras["schedule"]

    job = {
        "id": row.get("cron_id", ""),
        "name": row.get("name") or row.get("cron_id", ""),
        "schedule": schedule or {},
        "enabled": bool(row.get("enabled", True)),
        "createdAtMs": int(extras.get("createdAtMs") or 0),
        "state": {
            "lastRunAtMs": _parse_iso_to_ms(row.get("last_run_at")),
            "lastStatus": row.get("last_status") or "pending",
            "nextRunAtMs": _parse_iso_to_ms(row.get("next_run_at")),
            **state_extras,
        },
    }
    # Carry through any extra top-level fields (prompt, channel, model, ...)
    for k, v in extras.items():
        if k not in {"createdAtMs", "schedule", "lastDurationMs",
                     "consecutiveFailures", "lastError", "runHistory",
                     "lastCostUsd"}:
            job.setdefault(k, v)
    return job


def _try_local_store_crons():
    """Return jobs list shaped like ``/api/crons`` from the local DuckDB.

    Returns ``None`` to defer to the legacy gateway/file fallback if:
      - the ``local_store`` module isn't importable
      - the ``crons`` table is empty (fresh install / non-OpenClaw user)
      - any unexpected error happens (we'd rather degrade than 500)

    Cost attribution (``cost_usd`` / ``cost_session_count`` /
    ``cost_session_ids``) is intentionally returned as zeros from this path
    — wiring it up requires the transcript analytics pipeline that lives in
    ``dashboard.py`` and would defeat the whole point of the fast path. The
    dashboard JS treats missing/zero costs as "not yet attributed" and
    renders fine.
    """
    # Issue #1256: route through _ls_call (daemon HTTP proxy first, direct
    # open as single-process fallback). Direct get_store() always raised
    # IOException on multi-process installs because DuckDB's file lock is
    # exclusive across processes — the read_only=True hint doesn't help.
    rows = _ls_call("query_crons", limit=500)
    if rows is None:
        return None
    if not rows:
        return None
    jobs = []
    for r in rows:
        try:
            j = _row_to_cron_job(r)
        except Exception:
            continue
        # Match the contract from /api/crons cost-enrichment.
        j.setdefault("cost_usd", 0.0)
        j.setdefault("cost_session_count", 0)
        j.setdefault("cost_session_ids", [])
        jobs.append(j)
    return {"jobs": jobs, "_source": "local_store"}


def _try_local_store_cron_runs(job_id):
    """Return run history for a single cron job from the local DuckDB.

    Reads the ``events`` table filtered by ``event_type='cron_run'`` and
    matches rows whose ``agent_id`` or ``data.cron_id`` / ``data.jobId``
    equals ``job_id``. Each row is shaped into the run-record contract
    documented by ``_enrich_cron_runs``:

        {sessionId, timestamp, status, durationMs, costUsd, tokens}

    Returns ``None`` to defer to the legacy gateway/transcript fallback.
    """
    # Issue #1256: route through _ls_call (see _try_local_store_crons).
    evs = _ls_call("query_events", event_type="cron_run", limit=500)
    if evs is None:
        return None
    if not evs:
        return None
    runs = []
    for ev in evs:
        data = ev.get("data") if isinstance(ev.get("data"), dict) else {}
        # Match by agent_id (gateway emits cron_run with agent_id=cron_id) OR
        # by cron_id/jobId in the data blob (sync.py / future emitters).
        if (ev.get("agent_id") != job_id
                and data.get("cron_id") != job_id
                and data.get("jobId") != job_id):
            continue
        runs.append({
            "sessionId": ev.get("session_id", "") or data.get("sessionId", ""),
            "timestamp": _parse_iso_to_ms(ev.get("ts")),
            "status": data.get("status", "ok"),
            "durationMs": int(data.get("durationMs") or 0),
            "costUsd": round(float(ev.get("cost_usd") or data.get("costUsd") or 0.0), 6),
            "tokens": int(ev.get("token_count") or data.get("tokens") or 0),
        })
    if not runs:
        return None
    runs.sort(key=lambda r: r.get("timestamp", 0), reverse=True)
    return runs[:50]


def _try_local_store_cron_health_summary():
    """Return ``/api/cron/health-summary`` payload from the local DuckDB.

    Mirrors :func:`api_cron_health_summary`'s logic but sources jobs from
    ``query_crons()`` instead of the gateway. Cost-spike / duration-spike
    anomaly detection requires ``runHistory`` (carried in the ``data``
    blob if the writer included it) — when absent we report no anomalies
    but every other field stays meaningful.

    Returns ``None`` on empty/missing store.
    """
    # Issue #1256: route through _ls_call (see _try_local_store_crons).
    rows = _ls_call("query_crons", limit=500)
    if rows is None:
        return None
    if not rows:
        return None

    now_ms = int(datetime.now().timestamp() * 1000)
    summary = []
    total_ok = total_err = total_silent = 0

    for r in rows:
        try:
            job = _row_to_cron_job(r)
        except Exception:
            continue
        job_id = job.get("id", "")
        job_name = job.get("name", job_id)
        state = job.get("state") or {}
        enabled = bool(job.get("enabled", True))

        last_run_ms = state.get("lastRunAtMs") or 0
        last_status = state.get("lastStatus", "pending")
        last_duration_ms = state.get("lastDurationMs") or 0
        consecutive_failures = state.get("consecutiveFailures") or 0
        last_error = state.get("lastError", "") or ""
        next_run_ms = state.get("nextRunAtMs") or 0

        is_silent = False
        expected_interval_ms = None
        sched = job.get("schedule") or {}
        if isinstance(sched, dict):
            every_ms = sched.get("everyMs")
            if every_ms:
                try:
                    expected_interval_ms = int(every_ms)
                    if (enabled and last_run_ms
                            and (now_ms - last_run_ms) > expected_interval_ms * 2.5):
                        is_silent = True
                except (TypeError, ValueError):
                    pass

        # Cost attribution + anomaly stats are intentionally zero on the
        # fast path — see _try_local_store_crons docstring.
        cost_usd = 0.0
        cost_session_count = 0
        cost_spike = False
        duration_spike = False
        avg_cost = None

        run_history = state.get("runHistory") or []
        if run_history and len(run_history) > 2:
            historical_costs = [
                rh.get("costUsd", 0) for rh in run_history[1:] if rh.get("costUsd")
            ]
            if historical_costs:
                avg_cost = sum(historical_costs) / len(historical_costs)
                last_cost = run_history[0].get("costUsd", 0)
                if avg_cost > 0 and last_cost > avg_cost * 2.5:
                    cost_spike = True
            historical_durations = [
                rh.get("durationMs", 0) for rh in run_history[1:] if rh.get("durationMs")
            ]
            if historical_durations and last_duration_ms:
                avg_dur = sum(historical_durations) / len(historical_durations)
                if avg_dur > 0 and last_duration_ms > avg_dur * 3:
                    duration_spike = True

        if not enabled:
            health = "disabled"
        elif is_silent:
            health = "silent"
            total_silent += 1
        elif consecutive_failures >= 3 or last_status == "error":
            health = "error"
            total_err += 1
        elif cost_spike or duration_spike:
            health = "warning"
        else:
            health = "ok"
            total_ok += 1

        summary.append({
            "id": job_id,
            "name": job_name,
            "enabled": enabled,
            "health": health,
            "lastStatus": last_status,
            "lastRunAtMs": last_run_ms,
            "lastDurationMs": last_duration_ms,
            "nextRunAtMs": next_run_ms,
            "consecutiveFailures": consecutive_failures,
            "lastError": last_error,
            "costUsd": round(float(cost_usd), 6),
            "costSessionCount": cost_session_count,
            "monthlyProjectedCost": 0.0,
            "avgCost": round(avg_cost, 6) if avg_cost else None,
            "isSilent": is_silent,
            "costSpike": cost_spike,
            "durationSpike": duration_spike,
            "expectedIntervalMs": expected_interval_ms,
        })

    total_jobs = len(summary)
    has_anomalies = any(j["costSpike"] or j["durationSpike"] for j in summary)
    has_errors = total_err > 0
    has_silent = total_silent > 0
    return {
        "jobs": summary,
        "totals": {
            "total": total_jobs,
            "ok": total_ok,
            "error": total_err,
            "silent": total_silent,
            "disabled": sum(1 for j in summary if j["health"] == "disabled"),
            "warning": sum(1 for j in summary if j["health"] == "warning"),
        },
        "hasAnomalies": has_anomalies,
        "hasErrors": has_errors,
        "hasSilent": has_silent,
        "_source": "local_store",
    }


@bp_crons.route("/api/crons")
def api_crons():
    # Epic #964 phase 4: opt-in local-store fast path. When
    # CLAWMETRY_LOCAL_STORE_READ=1 AND the local crons table has rows,
    # serve directly from DuckDB. Falls through to gateway/file otherwise
    # (so a fresh install with no local store sees the same data as before
    # — zero-change default).
    if is_local_store_read_enabled():
        fast = _try_local_store_crons()
        if fast is not None:
            return jsonify(fast)
    import dashboard as _d

    def _with_costs(jobs):
        if not isinstance(jobs, list):
            return jobs
        analytics = _d._compute_transcript_analytics()
        sessions = [
            s for s in analytics.get("sessions", []) if s.get("is_cron_candidate")
        ]
        if not sessions:
            return jobs

        cost_by_job = defaultdict(float)
        count_by_job = defaultdict(int)
        session_ids_by_job = defaultdict(list)

        for sess in sessions:
            best_idx = None
            best_score = 0
            for idx, job in enumerate(jobs):
                score = _d._score_cron_match(sess, job if isinstance(job, dict) else {})
                if score > best_score:
                    best_score = score
                    best_idx = idx
            if best_idx is not None and best_score >= 20:
                cost = float(sess.get("cost_usd", 0.0) or 0.0)
                cost_by_job[best_idx] += cost
                count_by_job[best_idx] += 1
                if len(session_ids_by_job[best_idx]) < 10:
                    session_ids_by_job[best_idx].append(sess.get("session_id", ""))

        out = []
        for idx, job in enumerate(jobs):
            if not isinstance(job, dict):
                out.append(job)
                continue
            j2 = dict(job)
            j2["cost_usd"] = round(cost_by_job.get(idx, 0.0), 6)
            j2["cost_session_count"] = int(count_by_job.get(idx, 0))
            j2["cost_session_ids"] = session_ids_by_job.get(idx, [])
            # Normalize nextRunAtMs to number (closes #685)
            state = j2.get("state") or {}
            normalized_next_run = _d._normalize_next_run_at_ms(state)
            if normalized_next_run is not None:
                state["nextRunAtMs"] = normalized_next_run
            j2["state"] = state
            out.append(j2)
        return out

    # Try gateway API first
    gw_data = _d._gw_invoke("cron", {"action": "list", "includeDisabled": True})
    if gw_data and "jobs" in gw_data:
        jobs = _with_costs(gw_data.get("jobs", []))
        try:
            _d._ext_emit("cron.run", {"count": len(gw_data.get("jobs", []))})
        except Exception:
            pass
        return jsonify({"jobs": jobs})
    return jsonify({"jobs": _with_costs(_d._get_crons())})


@bp_crons.route("/api/cron/fix", methods=["POST"])
def api_cron_fix():
    import dashboard as _d
    data = request.get_json(silent=True) or {}
    job_id = data.get("jobId", "")
    if not job_id:
        return jsonify({"error": "Missing jobId"}), 400
    # Find the job name for context
    job_name = job_id
    for j in _d._get_crons():
        if j.get("id") == job_id:
            job_name = j.get("name", job_id)
            break
    # TODO: integrate with AI agent messaging system
    return jsonify({"ok": True, "message": f'Fix request submitted for "{job_name}"'})


@bp_crons.route("/api/cron/run", methods=["POST"])
def api_cron_run():
    import dashboard as _d
    data = request.get_json(silent=True) or {}
    job_id = data.get("jobId", "")
    if not job_id:
        return jsonify({"error": "Missing jobId"}), 400
    if _d._budget_paused:
        return jsonify(
            {"error": "Auto-pause active: refusing new session starts", "paused": True}
        ), 429
    result = _d._gw_invoke("cron", {"action": "run", "jobId": job_id})
    if result is None:
        return jsonify({"error": "Gateway unavailable"}), 502
    return jsonify({"ok": True, "message": "Job triggered", "result": result})


@bp_crons.route("/api/cron/toggle", methods=["POST"])
def api_cron_toggle():
    import dashboard as _d
    data = request.get_json(silent=True) or {}
    job_id = data.get("jobId", "")
    enabled = data.get("enabled", True)
    if not job_id:
        return jsonify({"error": "Missing jobId"}), 400
    result = _d._gw_invoke(
        "cron", {"action": "update", "jobId": job_id, "patch": {"enabled": enabled}}
    )
    if result is None:
        return jsonify({"error": "Gateway unavailable"}), 502
    return jsonify(
        {"ok": True, "message": "Job enabled" if enabled else "Job disabled"}
    )


@bp_crons.route("/api/cron/delete", methods=["POST"])
def api_cron_delete():
    import dashboard as _d
    data = request.get_json(silent=True) or {}
    job_id = data.get("jobId", "")
    if not job_id:
        return jsonify({"error": "Missing jobId"}), 400
    result = _d._gw_invoke("cron", {"action": "remove", "jobId": job_id})
    if result is None:
        return jsonify({"error": "Gateway unavailable"}), 502
    return jsonify({"ok": True, "message": "Job deleted"})


@bp_crons.route("/api/cron/update", methods=["POST"])
def api_cron_update():
    import dashboard as _d
    data = request.get_json(silent=True) or {}
    job_id = data.get("jobId", "")
    patch = data.get("patch", {})
    if not job_id:
        return jsonify({"error": "Missing jobId"}), 400
    if not patch:
        return jsonify({"error": "Missing patch"}), 400
    result = _d._gw_invoke("cron", {"action": "update", "jobId": job_id, "patch": patch})
    if result is None:
        return jsonify({"error": "Gateway unavailable"}), 502
    return jsonify({"ok": True, "message": "Job updated"})


@bp_crons.route("/api/cron/create", methods=["POST"])
def api_cron_create():
    import dashboard as _d
    data = request.get_json(silent=True) or {}
    name = data.get("name", "").strip()
    schedule = data.get("schedule")
    enabled = data.get("enabled", True)
    if not name:
        return jsonify({"error": "Missing name"}), 400
    if not schedule:
        return jsonify({"error": "Missing schedule"}), 400
    if _d._budget_paused:
        return jsonify(
            {"error": "Auto-pause active: refusing new session starts", "paused": True}
        ), 429
    args = {
        "action": "add",
        "name": name,
        "schedule": schedule,
        "enabled": enabled,
    }
    if data.get("prompt"):
        args["prompt"] = data["prompt"]
    if data.get("channel"):
        args["channel"] = data["channel"]
    if data.get("model"):
        args["model"] = data["model"]
    result = _d._gw_invoke("cron", args)
    if result is None:
        return jsonify({"error": "Gateway unavailable"}), 502
    return jsonify({"ok": True, "message": f'Job "{name}" created', "result": result})


@bp_crons.route("/api/cron/<job_id>/runs")
def api_cron_runs(job_id):
    """Return run history for a specific cron job.

    Tries gateway RPC first; falls back to parsing JSONL session transcripts
    for cron candidate sessions attributed to this job.
    Returns enriched list with p50/p95 duration stats.
    """
    # Epic #964 phase 4: opt-in local-store fast path.
    if is_local_store_read_enabled():
        fast_runs = _try_local_store_cron_runs(job_id)
        if fast_runs is not None:
            import dashboard as _d
            payload = _d._enrich_cron_runs(job_id, fast_runs)
            if isinstance(payload, dict):
                payload["_source"] = "local_store"
            return jsonify(payload)
    import dashboard as _d
    # Try gateway API first
    result = _d._gw_invoke("cron", {"action": "runs", "jobId": job_id, "limit": 50})
    if result is not None:
        runs = result.get("runs", result) if isinstance(result, dict) else result
        if isinstance(runs, list) and runs:
            return jsonify(_d._enrich_cron_runs(job_id, runs))

    # Fallback: derive runs from transcript analytics
    runs = _d._cron_runs_from_transcripts(job_id)
    return jsonify(_d._enrich_cron_runs(job_id, runs))


def _resolve_cron_runs_jsonl(job_id):
    """Return the first `~/.openclaw/cron/runs/<jobId>.jsonl` path that exists.

    Candidate roots (in order):
      1. ``$OPENCLAW_DATA_DIR/cron/runs/<jobId>.jsonl``
      2. ``$OPENCLAW_HOME/cron/runs/<jobId>.jsonl``
      3. ``~/.openclaw/cron/runs/<jobId>.jsonl``
      4. ``~/.clawdbot/cron/runs/<jobId>.jsonl``

    Returns ``None`` when nothing exists. Path-traversal-safe: normalises
    ``job_id`` and rejects anything containing ``/`` or ``..``.
    """
    # Defence in depth: refuse anything that could escape the runs dir.
    if not job_id or "/" in job_id or "\\" in job_id or ".." in job_id:
        return None
    candidates_roots = []
    data_dir = os.environ.get("OPENCLAW_DATA_DIR", "").strip()
    if data_dir:
        candidates_roots.append(os.path.expanduser(data_dir))
    home = os.environ.get("OPENCLAW_HOME", "").strip()
    if home:
        candidates_roots.append(os.path.expanduser(home))
    candidates_roots.extend([
        os.path.expanduser("~/.openclaw"),
        os.path.expanduser("~/.clawdbot"),
    ])
    for root in candidates_roots:
        runs_dir = os.path.join(root, "cron", "runs")
        fpath = os.path.normpath(os.path.join(runs_dir, f"{job_id}.jsonl"))
        # Make sure we didn't escape runs_dir
        norm_runs_dir = os.path.normpath(runs_dir)
        if not (fpath == norm_runs_dir or fpath.startswith(norm_runs_dir + os.sep)):
            continue
        if os.path.isfile(fpath):
            return fpath
    return None


def _read_cron_run_lines(fpath, limit):
    """Read the last ``limit`` JSONL records from ``fpath``.

    Returns a list of run dicts shaped as:

        {ts, duration_ms, status, error, usage, delivered_at, next_run_at}

    Malformed lines are skipped (with a debug log). Order: most-recent first.
    On any read error returns an empty list — callers expose a 200 with
    ``runs: []`` so the UI can show "no history yet" rather than a 500.
    """
    out = []
    try:
        with open(fpath, "r", errors="replace") as f:
            # Cheap-but-correct: keep only the last `limit` parsed records.
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except Exception:
                    # Malformed line — skip silently in prod, debug print in
                    # dev. Matches the "never crash on bad input" convention.
                    if os.environ.get("DEBUG"):
                        print(f"[crons] skip malformed line in {fpath}")
                    continue
                if not isinstance(obj, dict):
                    continue
                # Normalise field names (gateway writers have varied between
                # camelCase + snake_case over the years).
                ts = (
                    obj.get("ts")
                    or obj.get("timestamp")
                    or obj.get("startedAt")
                    or obj.get("started_at")
                )
                if isinstance(ts, str):
                    ts = _parse_iso_to_ms(ts)
                duration_ms = (
                    obj.get("duration_ms")
                    or obj.get("durationMs")
                    or obj.get("duration")
                    or 0
                )
                try:
                    duration_ms = int(duration_ms)
                except (TypeError, ValueError):
                    duration_ms = 0
                status = obj.get("status") or obj.get("result") or "unknown"
                err = obj.get("error") or obj.get("err") or ""
                if err and not isinstance(err, str):
                    err = str(err)
                if err and len(err) > 200:
                    err = err[:200]
                usage = obj.get("usage") or {}
                if not isinstance(usage, dict):
                    usage = {}
                delivered_at = (
                    obj.get("delivered_at")
                    or obj.get("deliveredAt")
                    or (
                        obj.get("deliveryStatus", {}).get("deliveredAt")
                        if isinstance(obj.get("deliveryStatus"), dict)
                        else None
                    )
                )
                if isinstance(delivered_at, str):
                    delivered_at = _parse_iso_to_ms(delivered_at) or None
                next_run_at = (
                    obj.get("next_run_at")
                    or obj.get("nextRunAt")
                    or obj.get("nextRunAtMs")
                )
                if isinstance(next_run_at, str):
                    next_run_at = _parse_iso_to_ms(next_run_at) or None
                out.append({
                    "ts": int(ts or 0),
                    "duration_ms": duration_ms,
                    "status": str(status),
                    "error": err,
                    "usage": usage,
                    "delivered_at": delivered_at,
                    "next_run_at": next_run_at,
                })
    except Exception as e:
        if os.environ.get("DEBUG"):
            print(f"[crons] failed to read {fpath}: {e}")
        return []
    # Most-recent first, then clamp to `limit`.
    out.sort(key=lambda r: r.get("ts") or 0, reverse=True)
    return out[:limit]


def _cron_runs_from_duckdb(job_id, limit):
    """Read cron-run rows from the local DuckDB store via the daemon proxy.

    Returns a list of run dicts shaped like the JSONL fallback below
    (``{ts, duration_ms, status, error, usage, delivered_at, next_run_at}``)
    so the UI sees a single canonical shape regardless of where the data
    came from. Returns ``[]`` on any failure or empty result so callers
    can decide whether to fall through to the JSONL read.

    Reads through ``_ls_call`` which hits the daemon's HTTP proxy first
    (cross-process DuckDB lock) before falling back to direct open for
    single-process boots — same pattern the other routes/* fast-paths use.
    """
    rows = _ls_call("query_cron_runs", job_id=job_id, limit=int(limit))
    if not rows:
        return []
    out = []
    for r in rows:
        try:
            ts = _parse_iso_to_ms(r.get("started_at"))
            duration_ms = int(r.get("duration_ms") or 0)
        except (TypeError, ValueError):
            ts = 0
            duration_ms = 0
        err = r.get("error_message") or ""
        if err and len(err) > 200:
            err = err[:200]
        # ``usage`` lives inside the freeform ``data`` blob that
        # ``query_cron_runs`` decodes from JSON. Surfaces null when the
        # writer didn't include one.
        data = r.get("data") if isinstance(r.get("data"), dict) else {}
        usage = data.get("usage") if isinstance(data.get("usage"), dict) else {}
        delivered_at = _parse_iso_to_ms(r.get("delivered_at")) or None
        next_run_at = _parse_iso_to_ms(r.get("next_run_at")) or None
        out.append({
            "ts": ts,
            "duration_ms": duration_ms,
            "status": str(r.get("status") or "unknown"),
            "error": err,
            "usage": usage,
            "delivered_at": delivered_at,
            "next_run_at": next_run_at,
        })
    # ``query_cron_runs`` already orders DESC by started_at, but the
    # numeric ``ts`` ordering may differ when the writer mixed ISO + epoch
    # representations across versions. Re-sort defensively.
    out.sort(key=lambda r: r.get("ts") or 0, reverse=True)
    return out


@bp_crons.route("/api/crons/<job_id>/runs")
def api_crons_job_runs(job_id):
    """Per-job run timeline for the Cron detail panel (closes #605).

    DuckDB-first (issue #605 DuckDB follow-up): the sync daemon ingests
    ``~/.openclaw/cron/runs/<jobId>.jsonl`` into the ``cron_runs`` table
    every cycle, and this endpoint reads from DuckDB. The legacy JSONL
    read remains as a fallback for graceful migration — used only when
    DuckDB has zero rows for the requested job (fresh install, daemon
    hasn't run yet, or a non-OpenClaw user).

    Returns the last ``limit`` runs (default 30, capped at 100) most
    recent first. Always 200, even when the file is missing and DuckDB
    is empty — the Cron UI treats an empty list as "no history yet".

    Path-traversal guard: ``job_id`` is rejected if it contains ``/``,
    ``\\``, or ``..`` before we touch any filesystem path. The DuckDB
    read is parameterised so it doesn't need the guard, but we apply it
    uniformly so both transports refuse the same inputs.
    """
    try:
        limit = int(request.args.get("limit", "30"))
    except (TypeError, ValueError):
        limit = 30
    limit = max(1, min(limit, 100))

    # Defence in depth — same as ``_resolve_cron_runs_jsonl``. Refuse
    # anything that could escape the runs dir before the JSONL fallback.
    if not job_id or "/" in job_id or "\\" in job_id or ".." in job_id:
        return jsonify({
            "jobId": job_id,
            "runs": [],
            "count": 0,
            "source": "duckdb",
            "file": None,
        })

    # DuckDB-first read (preferred path).
    runs = _cron_runs_from_duckdb(job_id, limit)
    if runs:
        return jsonify({
            "jobId": job_id,
            "runs": runs,
            "count": len(runs),
            "source": "duckdb",
            "file": None,
        })

    # Fallback: JSONL read. Only fires while the daemon is still building
    # the cron_runs table for this job — first cycle on a fresh install,
    # or when local_store isn't available (e.g. a stripped Docker image).
    fpath = _resolve_cron_runs_jsonl(job_id)
    if not fpath:
        return jsonify({
            "jobId": job_id,
            "runs": [],
            "count": 0,
            "source": "duckdb",
            "file": None,
        })
    runs = _read_cron_run_lines(fpath, limit)
    return jsonify({
        "jobId": job_id,
        "runs": runs,
        "count": len(runs),
        "source": "jsonl",
        "file": fpath,
    })


@bp_crons.route("/api/cron/<job_id>/kill", methods=["POST"])
def api_cron_kill(job_id):
    """Kill switch: disable a single cron job by ID.

    Sends update via gateway WebSocket RPC to disable the job immediately.
    Returns the updated job state or an error.
    """
    import dashboard as _d
    result = _d._gw_invoke(
        "cron", {"action": "update", "jobId": job_id, "patch": {"enabled": False}}
    )
    if result is None:
        return jsonify(
            {
                "ok": False,
                "error": "Gateway unavailable — cannot disable cron remotely. Try restarting the gateway.",
            }
        ), 502
    return jsonify({"ok": True, "jobId": job_id, "enabled": False, "result": result})


def _try_local_store_cron_run_log(session_id: str):
    """Fast path for /api/cron-run-log. Reads message events for the given
    session from DuckDB and projects ``role/timestamp/content`` for the modal.

    Issue #1088: routes through the daemon HTTP proxy first via ``_ls_call``,
    with the standard direct-open fallback for single-process boots. Returns
    ``None`` to defer to the JSONL parser when the events table has no
    message rows for this session.
    """
    rows = _ls_call("query_events", session_id=session_id, limit=5000)
    if not rows:
        return None
    rows = list(reversed(rows))  # query_events returns DESC
    events = []
    for ev in rows:
        if ev.get("event_type") != "message":
            continue
        data = ev.get("data") if isinstance(ev.get("data"), dict) else {}
        msg = data.get("message") if isinstance(data.get("message"), dict) else {}
        events.append({
            "role": msg.get("role", ""),
            "timestamp": data.get("timestamp") or ev.get("ts") or "",
            "content": str(msg.get("content", ""))[:500],
        })
    if not events:
        return None
    return {"sessionId": session_id, "events": events, "_source": "local_store"}


@bp_crons.route("/api/cron-run-log")
def api_cron_run_log():
    """Return a parsed session transcript for a cron run (for the run-log modal)."""
    import dashboard as _d
    session_id = request.args.get("session_id", "")
    if not session_id:
        return jsonify({"error": "session_id required"}), 400
    if is_local_store_read_enabled():
        fast = _try_local_store_cron_run_log(session_id)
        if fast is not None:
            return jsonify(fast)
    sessions_dir = _d._get_sessions_dir()
    fpath = os.path.join(sessions_dir, f"{session_id}.jsonl")
    # Guard against path-traversal via crafted session_id (e.g. "../../etc/passwd").
    # Originally reported by @dumko2001 in #507.
    norm_fpath = os.path.normpath(fpath)
    norm_sessions_root = os.path.normpath(sessions_dir)
    if not (
        norm_fpath == norm_sessions_root
        or norm_fpath.startswith(norm_sessions_root + os.sep)
    ):
        return jsonify({"error": "Invalid session_id"}), 400
    fpath = norm_fpath
    if not os.path.isfile(fpath):
        return jsonify({"error": "Session not found"}), 404
    events = []
    try:
        with open(fpath, "r", errors="replace") as f:
            for line in f:
                try:
                    obj = json.loads(line.strip())
                    if obj.get("type") == "message":  # v3-shape-gate: allow (reason: JSONL on-disk walker; reads per-line JSON from transcript files)
                        msg = obj.get("message", {})
                        events.append(
                            {
                                "role": msg.get("role", ""),
                                "timestamp": obj.get("timestamp", ""),
                                "content": str(msg.get("content", ""))[:500],
                            }
                        )
                except Exception:
                    continue
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    return jsonify({"sessionId": session_id, "events": events})


@bp_crons.route("/api/cron/health-summary")
def api_cron_health_summary():
    """Aggregate cron health: per-job success rate, cost, anomaly flags, silent detection."""
    # Epic #964 phase 4: opt-in local-store fast path.
    if is_local_store_read_enabled():
        fast = _try_local_store_cron_health_summary()
        if fast is not None:
            return jsonify(fast)
    import dashboard as _d
    gw_data = _d._gw_invoke("cron", {"action": "list", "includeDisabled": True}) or {}
    jobs = gw_data.get("jobs", []) or _d._get_crons()
    if not isinstance(jobs, list):
        jobs = []

    now_ms = int(datetime.now().timestamp() * 1000)
    summary = []
    total_ok = total_err = total_silent = 0

    for job in jobs:
        if not isinstance(job, dict):
            continue
        job_id = job.get("id", "")
        job_name = job.get("name", job_id)
        state = job.get("state") or {}
        enabled = job.get("enabled", True)

        last_run_ms = state.get("lastRunAtMs") or state.get("lastRunAt") or 0
        if isinstance(last_run_ms, str):
            try:
                from dateutil import parser as _dtp

                last_run_ms = int(_dtp.parse(last_run_ms).timestamp() * 1000)
            except Exception:
                last_run_ms = 0

        last_status = state.get("lastStatus", "pending")
        last_duration_ms = state.get("lastDurationMs") or 0
        consecutive_failures = state.get("consecutiveFailures") or 0
        last_error = state.get("lastError", "")
        next_run_ms = _d._normalize_next_run_at_ms(state) or 0

        # Detect silent jobs: enabled, has run before, but hasn't run in >2.5x expected interval
        is_silent = False
        expected_interval_ms = None
        sched = job.get("schedule") or {}
        if isinstance(sched, dict):
            every_ms = sched.get("everyMs")
            if every_ms:
                expected_interval_ms = int(every_ms)
                if enabled and last_run_ms and (now_ms - last_run_ms) > every_ms * 2.5:
                    is_silent = True

        # Cost attribution from existing api_crons enrichment
        cost_usd = job.get("cost_usd") or 0.0
        cost_session_count = job.get("cost_session_count") or 0

        # Anomaly: cost spike (last run vs average) — uses run history from gateway
        run_history = job.get("runHistory") or []
        cost_spike = False
        avg_cost = None
        if run_history and len(run_history) > 2:
            historical_costs = [
                r.get("costUsd", 0) for r in run_history[1:] if r.get("costUsd")
            ]
            if historical_costs:
                avg_cost = sum(historical_costs) / len(historical_costs)
                last_cost = run_history[0].get("costUsd", 0) if run_history else 0
                if avg_cost > 0 and last_cost > avg_cost * 2.5:
                    cost_spike = True

        # Duration anomaly: last run >3x average
        duration_spike = False
        if run_history and len(run_history) > 2:
            historical_durations = [
                r.get("durationMs", 0) for r in run_history[1:] if r.get("durationMs")
            ]
            if historical_durations and last_duration_ms:
                avg_dur = sum(historical_durations) / len(historical_durations)
                if avg_dur > 0 and last_duration_ms > avg_dur * 3:
                    duration_spike = True

        # Health status
        if not enabled:
            health = "disabled"
        elif is_silent:
            health = "silent"
            total_silent += 1
        elif consecutive_failures >= 3 or last_status == "error":
            health = "error"
            total_err += 1
        elif cost_spike or duration_spike:
            health = "warning"
        else:
            health = "ok"
            total_ok += 1

        # Monthly cost projection
        monthly_cost = 0.0
        if cost_usd and cost_session_count and cost_session_count > 0:
            avg_run_cost = cost_usd / cost_session_count
            if expected_interval_ms:
                runs_per_month = (30 * 24 * 3600 * 1000) / expected_interval_ms
                monthly_cost = avg_run_cost * runs_per_month

        summary.append(
            {
                "id": job_id,
                "name": job_name,
                "enabled": enabled,
                "health": health,
                "lastStatus": last_status,
                "lastRunAtMs": last_run_ms,
                "lastDurationMs": last_duration_ms,
                "nextRunAtMs": next_run_ms,
                "consecutiveFailures": consecutive_failures,
                "lastError": last_error,
                "costUsd": round(float(cost_usd), 6),
                "costSessionCount": cost_session_count,
                "monthlyProjectedCost": round(monthly_cost, 4),
                "avgCost": round(avg_cost, 6) if avg_cost else None,
                "isSilent": is_silent,
                "costSpike": cost_spike,
                "durationSpike": duration_spike,
                "expectedIntervalMs": expected_interval_ms,
            }
        )

    total_jobs = len(summary)
    has_anomalies = any(j["costSpike"] or j["durationSpike"] for j in summary)
    has_errors = total_err > 0
    has_silent = total_silent > 0

    return jsonify(
        {
            "jobs": summary,
            "totals": {
                "total": total_jobs,
                "ok": total_ok,
                "error": total_err,
                "silent": total_silent,
                "disabled": sum(1 for j in summary if j["health"] == "disabled"),
                "warning": sum(1 for j in summary if j["health"] == "warning"),
            },
            "hasAnomalies": has_anomalies,
            "hasErrors": has_errors,
            "hasSilent": has_silent,
        }
    )


@bp_crons.route("/api/cron/kill-all", methods=["POST"])
def api_cron_kill_all():
    """Emergency: disable all enabled cron jobs. Returns count disabled."""
    import dashboard as _d
    gw_data = _d._gw_invoke("cron", {"action": "list", "includeDisabled": False}) or {}
    jobs = gw_data.get("jobs", []) or _d._get_crons()
    if not isinstance(jobs, list):
        jobs = []

    disabled_count = 0
    errors = []
    for job in jobs:
        if not isinstance(job, dict):
            continue
        if not job.get("enabled", True):
            continue
        job_id = job.get("id", "")
        if not job_id:
            continue
        result = _d._gw_invoke(
            "cron", {"action": "update", "jobId": job_id, "patch": {"enabled": False}}
        )
        if result is not None:
            disabled_count += 1
        else:
            errors.append(job_id)

    return jsonify(
        {
            "ok": True,
            "disabled": disabled_count,
            "errors": errors,
            "message": f"Emergency stop: {disabled_count} cron job(s) disabled.",
        }
    )


def _project_intentions(jobs, days: int, include_disabled: bool, max_events: int):
    """Walk the cron job list and produce the ``intentions`` + ``recently_added``
    payload ``/api/agent-intentions`` returns. Pulled out of the route so the
    fast-path can reuse the projection logic against ``query_crons`` rows
    without duplicating the timeline math."""
    now_ms = int(datetime.now().timestamp() * 1000)
    window_end_ms = now_ms + days * 24 * 3600 * 1000
    recent_threshold_ms = now_ms - 24 * 3600 * 1000

    intentions: list = []
    recently_added: list = []

    for job in jobs:
        if not isinstance(job, dict):
            continue
        enabled = bool(job.get("enabled", True))
        if not enabled and not include_disabled:
            continue
        job_id = job.get("id", "")
        job_name = job.get("name", job_id)
        sched = job.get("schedule") or {}
        state = job.get("state") or {}
        created_at_ms = job.get("createdAtMs") or 0
        if isinstance(created_at_ms, str):
            try:
                from dateutil import parser as _dtp
                created_at_ms = int(_dtp.parse(created_at_ms).timestamp() * 1000)
            except Exception:
                created_at_ms = 0
        is_recently_added = bool(created_at_ms and created_at_ms >= recent_threshold_ms)
        if is_recently_added:
            recently_added.append({
                "jobId":       job_id,
                "name":        job_name,
                "createdAtMs": created_at_ms,
                "schedule":    sched,
                "enabled":     enabled,
            })
        last_status = state.get("lastStatus", "pending")
        last_run_ms = state.get("lastRunAtMs") or 0
        if isinstance(last_run_ms, str):
            try:
                from dateutil import parser as _dtp
                last_run_ms = int(_dtp.parse(last_run_ms).timestamp() * 1000)
            except Exception:
                last_run_ms = 0
        next_run_ms = state.get("nextRunAtMs") or 0
        sched_kind = (sched.get("kind") or "").lower() if isinstance(sched, dict) else ""
        every_ms = sched.get("everyMs") if isinstance(sched, dict) else None
        try:
            every_ms = int(every_ms) if every_ms else 0
        except (TypeError, ValueError):
            every_ms = 0
        firings: list = []
        if sched_kind in ("every", "interval") and every_ms > 0:
            t = int(next_run_ms) if next_run_ms else now_ms + every_ms
            if t < now_ms:
                gap = now_ms - t
                t += ((gap // every_ms) + 1) * every_ms
            while t <= window_end_ms and len(firings) < 100:
                firings.append(t)
                t += every_ms
        elif next_run_ms and now_ms <= next_run_ms <= window_end_ms:
            firings.append(int(next_run_ms))
        for ts in firings:
            intentions.append({
                "jobId":           job_id,
                "name":            job_name,
                "scheduledForMs":  ts,
                "scheduleKind":    sched_kind or "unknown",
                "lastStatus":      last_status,
                "lastRunAtMs":     last_run_ms,
                "isRecentlyAdded": is_recently_added,
                "enabled":         enabled,
            })
            if len(intentions) >= max_events:
                break
        if len(intentions) >= max_events:
            break
    intentions.sort(key=lambda r: r.get("scheduledForMs", 0))
    recently_added.sort(key=lambda r: -(r.get("createdAtMs") or 0))
    return intentions, recently_added, now_ms, window_end_ms


def _try_local_store_agent_intentions(days: int, include_disabled: bool, max_events: int):
    """Fast path for /api/agent-intentions. Reads cron jobs from the local
    DuckDB ``crons`` table (already populated by sync.py) and runs the
    same projection ``/api/agent-intentions`` does against the gateway
    response.

    Issue #1088 phase 3. Returns ``None`` when the crons table is empty
    so the route falls through to the gateway RPC."""
    rows = _ls_call("query_crons", limit=500)
    if not rows:
        return None
    jobs = []
    for r in rows:
        try:
            jobs.append(_row_to_cron_job(r))
        except Exception:
            continue
    intentions, recently_added, now_ms, window_end_ms = _project_intentions(
        jobs, days, include_disabled, max_events
    )
    return {
        "intentions":     intentions,
        "recently_added": recently_added,
        "window": {
            "startMs": now_ms,
            "endMs":   window_end_ms,
            "days":    days,
        },
        "stats": {
            "total_intentions":     len(intentions),
            "recently_added_count": len(recently_added),
            "truncated":            len(intentions) >= max_events,
        },
        "_source": "local_store",
    }


@bp_crons.route("/api/agent-intentions")
def api_agent_intentions():
    """Cron jobs reframed as the agent's planned future actions.

    Returns the same job data as ``/api/crons`` projected onto a calendar
    timeline: every firing the agent has scheduled in the next ``days``
    window, plus a ``recently_added`` callout for jobs the agent created
    in the last 24 hours.

    Query params:
      days (int, default=7, max=30): timeline window in days from now.
      include_disabled (bool, default=false): also project disabled jobs.
      max_events (int, default=200, max=1000): cap on projected firings.

    Interval jobs (``schedule.kind`` ∈ {``every``, ``interval``}) are
    projected forward by repeatedly adding ``everyMs`` to ``nextRunAtMs``.
    Cron-expression jobs are surfaced with only their gateway-provided
    ``nextRunAtMs`` (full cron parsing is intentionally out of scope —
    needs a dependency we don't ship today).
    """
    import dashboard as _d

    try:
        days = max(1, min(int(request.args.get("days", "7")), 30))
    except ValueError:
        days = 7
    include_disabled = str(request.args.get("include_disabled", "")).lower() in (
        "1", "true", "yes"
    )
    try:
        max_events = max(10, min(int(request.args.get("max_events", "200")), 1000))
    except ValueError:
        max_events = 200

    if is_local_store_read_enabled():
        fast = _try_local_store_agent_intentions(days, include_disabled, max_events)
        if fast is not None:
            return jsonify(fast)

    gw_data = _d._gw_invoke("cron", {"action": "list", "includeDisabled": True}) or {}
    jobs = gw_data.get("jobs", []) or _d._get_crons()
    if not isinstance(jobs, list):
        jobs = []

    intentions, recently_added, now_ms, window_end_ms = _project_intentions(
        jobs, days, include_disabled, max_events
    )
    return jsonify({
        "intentions": intentions,
        "recently_added": recently_added,
        "window": {
            "startMs": now_ms,
            "endMs": window_end_ms,
            "days": days,
        },
        "stats": {
            "total_intentions": len(intentions),
            "recently_added_count": len(recently_added),
            "truncated": len(intentions) >= max_events,
        },
    })


@bp_crons.route("/api/cron-health")
def api_cron_health():
    """Cron health monitor — run history, success rate, cost per run (GH #306).

    Alias for /api/cron/health-summary with a normalised response shape:

        {
          "crons": [
            {
              "id": str,
              "name": str,
              "enabled": bool,
              "health": "ok" | "warning" | "error" | "silent" | "disabled",
              "stats": {
                "success_rate": float,     # 0-100 (derived from consecutive failures)
                "total_runs": int,
                "avg_duration_ms": float,
                "total_cost_usd": float,
              },
              "recent_runs": [],           # reserved for future run-log expansion
              "last_error": str | null,
            }
          ],
          "totals": { "total", "ok", "error", "silent", "disabled", "warning" },
          "has_anomalies": bool,
        }
    """
    import dashboard as _d
    with _d.app.test_request_context():
        inner = api_cron_health_summary()
    raw = inner.get_json(force=True) or {}

    crons_out = []
    for j in raw.get("jobs", []):
        cf = j.get("consecutiveFailures", 0) or 0
        total_runs = j.get("costSessionCount", 0) or 0
        # Estimate success rate: each consecutive failure counts against a window of 10
        window = max(total_runs, cf, 10)
        success_rate = round(max(0.0, (window - cf) / window * 100.0), 1)

        crons_out.append(
            {
                "id": j.get("id", ""),
                "name": j.get("name", ""),
                "enabled": bool(j.get("enabled", True)),
                "health": j.get("health", "ok"),
                "stats": {
                    "success_rate": success_rate,
                    "total_runs": total_runs,
                    "avg_duration_ms": float(j.get("lastDurationMs") or 0),
                    "total_cost_usd": float(j.get("costUsd") or 0),
                },
                "recent_runs": [],  # run history available via /api/cron/<id>/runs
                "last_error": j.get("lastError") or None,
            }
        )

    out = {
        "crons": crons_out,
        "totals": raw.get("totals", {}),
        "has_anomalies": bool(raw.get("hasAnomalies", False)),
    }
    # Propagate fast-path tag so callers can assert which source served the data.
    if raw.get("_source"):
        out["_source"] = raw["_source"]
    return jsonify(out)
