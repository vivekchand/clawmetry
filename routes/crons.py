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

bp_crons = Blueprint('crons', __name__)


@bp_crons.route("/api/crons")
def api_crons():
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


@bp_crons.route("/api/cron-run-log")
def api_cron_run_log():
    """Return a parsed session transcript for a cron run (for the run-log modal)."""
    import dashboard as _d
    session_id = request.args.get("session_id", "")
    if not session_id:
        return jsonify({"error": "session_id required"}), 400
    sessions_dir = _d._get_sessions_dir()
    fpath = os.path.join(sessions_dir, f"{session_id}.jsonl")
    if not os.path.isfile(fpath):
        return jsonify({"error": "Session not found"}), 404
    events = []
    try:
        with open(fpath, "r", errors="replace") as f:
            for line in f:
                try:
                    obj = json.loads(line.strip())
                    if obj.get("type") == "message":
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

    return jsonify(
        {
            "crons": crons_out,
            "totals": raw.get("totals", {}),
            "has_anomalies": bool(raw.get("hasAnomalies", False)),
        }
    )
