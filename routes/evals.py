"""
routes/evals.py — Eval (LLM-as-judge) endpoints.

Phase 1 of issue #1619. The scoring path runs in ``clawmetry/eval_runner.py``
on the user's own API key; these endpoints just expose the persisted scores
(local DuckDB) to the dashboard UI and to ad-hoc re-score requests.

Routes:
  GET   /api/evals/recent           — recent scored sessions
  GET   /api/evals/summary          — aggregate avg/p50/p10 over a window
  POST  /api/evals/rescore/<sid>    — manual re-eval trigger for one session
  GET   /api/evals/rubric           — raw rubric YAML text
  POST  /api/evals/rubric           — replace rubric YAML text (validates parse)

All endpoints degrade gracefully when the local store or eval runner is
unavailable — the dashboard treats an empty payload as "evals not yet
populated" rather than an error.
"""

from __future__ import annotations

from flask import Blueprint, jsonify, request

bp_evals = Blueprint("evals", __name__)


def _store_via_daemon_or_direct(method_name: str, **kwargs):
    """Mirror of routes/sessions.py:_ls_call — daemon HTTP proxy first,
    then direct DuckDB open as fallback. Returns ``None`` on miss."""
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


@bp_evals.route("/api/evals/recent", methods=["GET"])
def evals_recent():
    """Recent scored sessions. ``?limit=`` defaults to 50, capped at 200."""
    try:
        limit = max(1, min(200, int(request.args.get("limit", "50"))))
    except (TypeError, ValueError):
        limit = 50
    rows = _store_via_daemon_or_direct("query_recent_evals", limit=limit) or []
    return jsonify({"evals": rows, "limit": limit})


@bp_evals.route("/api/evals/summary", methods=["GET"])
def evals_summary():
    """Aggregate over the recent window. ``?window=1d`` (1d, 6h, 24h ok)."""
    raw = (request.args.get("window") or "24h").strip().lower()
    # Tiny human-readable window parser; defaults to 24h on anything weird.
    hours = 24
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
        hours = 24
    hours = max(1, min(24 * 30, hours))
    payload = _store_via_daemon_or_direct(
        "query_eval_summary", window_hours=hours,
    )
    if not payload:
        payload = {
            "avg_score":    0.0,
            "total":        0,
            "scored":       0,
            "p50":          0.0,
            "p10":          0.0,
            "window_hours": hours,
        }
    return jsonify(payload)


@bp_evals.route("/api/evals/rescore/<session_id>", methods=["POST"])
def evals_rescore(session_id: str):
    """Manually trigger a re-score for one session. Synchronous — returns
    the new score (or skip / failure) so the UI can flash a toast.

    We deliberately keep this synchronous: the user's intent is "I want
    to see the new score NOW", and a Haiku judge call typically returns
    in under 2 seconds.
    """
    try:
        from clawmetry import eval_runner
    except Exception as e:
        return jsonify({"error": f"eval runner unavailable: {e}"}), 503
    if not eval_runner.is_enabled():
        return jsonify({
            "error": "evals are disabled (CLAWMETRY_EVALS_ENABLED=0)",
        }), 409
    runner = eval_runner.EvalRunner()
    try:
        result = runner.score_session(session_id)
    except Exception as e:
        return jsonify({"error": f"score_session failed: {e}"}), 500
    if result is None:
        return jsonify({"error": "evals disabled"}), 409
    return jsonify(result.to_dict())


@bp_evals.route("/api/evals/rubric", methods=["GET"])
def evals_rubric_get():
    """Return the raw rubric YAML text + the parsed default for reference."""
    try:
        from clawmetry import eval_runner
    except Exception as e:
        return jsonify({"error": f"eval runner unavailable: {e}"}), 503
    return jsonify({
        "yaml":           eval_runner.get_rubric_yaml(),
        "rubric_path":    str(eval_runner.RUBRIC_PATH),
        "default":        eval_runner.DEFAULT_RUBRIC,
        "enabled":        eval_runner.is_enabled(),
    })


@bp_evals.route("/api/evals/rubric", methods=["POST"])
def evals_rubric_save():
    """Replace the rubric YAML. Validates parse before writing.

    Body: ``{"yaml": "<text>"}``. Returns the parsed default merged with
    the saved rubric so the UI can confirm the round-trip worked.
    """
    try:
        from clawmetry import eval_runner
    except Exception as e:
        return jsonify({"error": f"eval runner unavailable: {e}"}), 503
    body = request.get_json(silent=True) or {}
    text = body.get("yaml")
    if not isinstance(text, str) or not text.strip():
        return jsonify({"error": "missing 'yaml' field"}), 400
    try:
        eval_runner.save_rubric_yaml(text)
    except Exception as e:
        return jsonify({"error": f"rubric save failed: {e}"}), 400
    return jsonify({
        "ok":      True,
        "rubric":  eval_runner.load_rubric("default"),
    })
