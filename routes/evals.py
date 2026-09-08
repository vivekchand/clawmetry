"""
routes/evals.py — Eval (LLM-as-judge) endpoints.

Phase 1 of issue #1619. The scoring path runs in ``clawmetry/eval_runner.py``
on the user's own API key; these endpoints just expose the persisted scores
(local DuckDB) to the dashboard UI and to ad-hoc re-score requests.

Routes:
  GET   /api/evals/recent              — recent scored sessions
  GET   /api/evals/summary             — aggregate avg/p50/p10 over a window
  POST  /api/evals/rescore/<sid>       — manual re-eval trigger for one session
  GET   /api/evals/rubric              — raw rubric YAML text
  POST  /api/evals/rubric              — replace rubric YAML text (validates parse)
  GET   /api/evals/regression-summary  — Phase 3: aggregate replay outcomes
  GET   /api/evals/metrics             — per-session per-metric verdicts (#2862)

All endpoints degrade gracefully when the local store or eval runner is
unavailable — the dashboard treats an empty payload as "evals not yet
populated" rather than an error.
"""

from __future__ import annotations

from flask import Blueprint, jsonify, request

from clawmetry._gate import gate

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


@bp_evals.route("/api/evaluators", methods=["GET"])
def evaluators_catalogue():
    """The named evaluator library — ClawMetry's shipped quality / reliability /
    efficiency / safety / agent signals, surfaced as a branded catalogue.

    Cloud-safe and never-raise. The catalogue is static data so it returns the
    same list whether or not a DuckDB store is reachable (the cloud container
    has none). When a store is available we attach best-effort live coverage
    counts; when it is not, ``coverage`` is null and the catalogue still renders
    — no silent blank.

    Pro entries (faithfulness, agent-efficiency, agent-tool-error-detector) are
    declared here and carry ``locked: true`` until the clawmetry-pro plugin
    registers their compute hook, at which point they report ``live``.
    """
    try:
        from clawmetry import evaluators
    except Exception as e:  # pragma: no cover - defensive
        return jsonify({"evaluators": [], "error": f"catalogue unavailable: {e}"})

    store = None
    try:
        # Best-effort store handle for live coverage. Daemon proxy first (so we
        # never grab the writer lock), then a read-only open. Both are optional:
        # on the cloud container there is no store and we return the catalogue
        # with coverage=null rather than blank.
        from routes.local_query import local_store_via_daemon  # noqa: F401

        class _DaemonStore:
            def query_eval_summary(self, **kw):
                return local_store_via_daemon("query_eval_summary", **kw)

            def query_outcomes(self, **kw):
                return local_store_via_daemon("query_outcomes", **kw)

        probe = local_store_via_daemon("query_eval_summary", window_hours=24)
        if probe is not None:
            store = _DaemonStore()
    except Exception:
        store = None
    if store is None:
        try:
            from clawmetry import local_store
            store = local_store.get_store(read_only=True)
        except Exception:
            store = None

    # Honest per-box judge state: the answer-quality entry is only "Live" when
    # a judge API key actually exists on this box (env or the UI-saved store).
    # judge_ready=None (lookup failed / cloud) keeps the static status.
    judge_ready = None
    judge_meta = None
    try:
        from clawmetry import eval_runner
        keys = eval_runner.judge_keys_present()
        enabled = eval_runner.is_enabled()
        rubric = eval_runner.load_rubric("default") or {}
        provider = eval_runner.judge_provider_for(rubric)
        # Honest per-box readiness: the key must exist for the provider the
        # judge is actually configured to use, not just any provider.
        provider_key = bool(keys.get(provider))
        last = eval_runner.last_judge_status()
        judge_ready = bool(enabled and provider_key)
        judge_meta = {
            "enabled": enabled,
            "key_present": provider_key,
            "keys": keys,
            "provider": provider,
            "model": str(
                rubric.get("judge_model")
                or eval_runner.DEFAULT_RUBRIC["judge_model"]
            ),
            # issue #4313: a present-but-rejected key must not read as healthy.
            "last_error": last.get("error"),
            "last_ok_at": last.get("at") if last.get("ok") else None,
        }
    except Exception:
        judge_ready = None

    try:
        payload = evaluators.catalogue_with_coverage(store, judge_ready=judge_ready)
    except Exception as e:  # pragma: no cover - defensive
        try:
            payload = {"evaluators": evaluators.catalogue(), "coverage": None}
        except Exception:
            payload = {"evaluators": [], "error": f"catalogue failed: {e}"}
    if judge_meta is not None:
        payload["judge"] = judge_meta
    return jsonify(payload)


@bp_evals.route("/api/evals/recent", methods=["GET"])
@gate("eval_suite")
def evals_recent():
    """Recent scored sessions. ``?limit=`` defaults to 50, capped at 200."""
    try:
        limit = max(1, min(200, int(request.args.get("limit", "50"))))
    except (TypeError, ValueError):
        limit = 50
    rows = _store_via_daemon_or_direct("query_recent_evals", limit=limit) or []
    return jsonify({"evals": rows, "limit": limit})


@bp_evals.route("/api/evals/session/<session_id>", methods=["GET"])
@gate("eval_suite")
def evals_session_detail(session_id: str):
    """Per-session drill-down for the Recently Scored row-click drawer.

    Returns everything a user needs to answer "why did this session get this
    score?" without leaving the Evals tab: the judge's full reason (not the
    truncated one-liner the table shows), the rubric text the judge used, the
    outcome + reliability + faithfulness signals the tile grid used to bury,
    and every deterministic metric verdict the session accumulated.

    Ungated (mirrors ``/api/evals/metrics`` + ``/api/evaluators``): the shape
    is a read of already-computed values, no LLM call. 404 on unknown session.
    """
    sid = (session_id or "").strip()
    if not sid:
        return jsonify({"error": "session_id required"}), 400
    detail = _store_via_daemon_or_direct("query_session_eval_detail", session_id=sid)
    if not detail:
        return jsonify({"error": "session not found"}), 404
    metrics = _store_via_daemon_or_direct(
        "query_eval_metrics", session_id=sid, metric_slug=None, limit=100,
    ) or []
    # Attach the catalogue name for each metric slug so the drawer can render
    # a plain-language label ("Did the agent finish the job?") instead of a
    # raw slug. Best-effort — a missing catalogue keeps the raw slug.
    try:
        from clawmetry import evaluators as _evaluators
        by_slug = {e["slug"]: e for e in _evaluators.EVALUATOR_CATALOGUE}
    except Exception:
        by_slug = {}
    for m in metrics:
        spec = by_slug.get(m.get("metric_slug"))
        if spec:
            m["label"] = spec["name"]
            m["category"] = spec["category"]
    return jsonify({
        "session":  detail,
        "metrics":  metrics,
    })


@bp_evals.route("/api/evals/metrics", methods=["GET"])
def evals_metrics():
    """Per-session, per-metric verdicts (#2862 resurrected). The built-in
    deterministic checks are free-tier (they run on the user's box at zero
    LLM cost), so this read is ungated — mirroring ``/api/evaluators``.
    Filters: ``?session_id=`` and/or ``?metric=``; ``?limit=`` capped at 500."""
    try:
        limit = max(1, min(500, int(request.args.get("limit", "100"))))
    except (TypeError, ValueError):
        limit = 100
    session_id = (request.args.get("session_id") or "").strip() or None
    metric = (request.args.get("metric") or "").strip() or None
    rows = _store_via_daemon_or_direct(
        "query_eval_metrics",
        session_id=session_id, metric_slug=metric, limit=limit,
    ) or []
    return jsonify({"metrics": rows, "limit": limit})


@bp_evals.route("/api/evals/summary", methods=["GET"])
@gate("eval_suite")
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
@gate("eval_suite")
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
@gate("eval_suite")
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


@bp_evals.route("/api/evals/regression-summary", methods=["GET"])
@gate("eval_suite")
def evals_regression_summary():
    """Phase 3 (refs #1619) — aggregate replay outcomes over a window.

    ``?window=7d`` (1d, 7d, 30d ok; bounded to 90d). Returns the same
    payload shape ``run_regression`` builds, except aggregated from the
    persisted ``eval_regression_runs`` table:

        {tested: N, improved: X, regressed: Y, same: Z, errored: E,
         window_days: D, last_run_at: <epoch_ms | null>}

    Empty payload (all zeros + ``last_run_at: null``) on a fresh install
    where the user hasn't run ``clawmetry eval --regression`` yet.
    """
    raw = (request.args.get("window") or "7d").strip().lower()
    days = 7
    try:
        if raw.endswith("d"):
            days = int(float(raw[:-1]))
        elif raw.endswith("h"):
            days = max(1, int(float(raw[:-1]) // 24))
        else:
            days = int(float(raw))
    except (TypeError, ValueError):
        days = 7
    days = max(1, min(90, days))
    try:
        from clawmetry import eval_regression_replay as err
        payload = err.regression_summary(window_days=days)
    except Exception:
        payload = {
            "tested": 0, "improved": 0, "regressed": 0, "same": 0,
            "errored": 0, "window_days": days, "last_run_at": None,
        }
    return jsonify(payload)


@bp_evals.route("/api/evals/suites", methods=["GET"])
@gate("eval_suite")
def evals_suites():
    """List golden test suites (~/.clawmetry/evals/<name>.yaml) so the Evals
    tab can show them alongside the CLI hint. Empty list on a fresh install."""
    try:
        from clawmetry import eval_suite_runner
        names = eval_suite_runner.list_suites()
    except Exception:
        names = []
    return jsonify({
        "suites": names,
        "suites_dir": "~/.clawmetry/evals",
        "cli": "clawmetry eval --suite <name>",
    })


@bp_evals.route("/api/evals/key", methods=["GET"])
@gate("eval_suite")
def evals_key_get():
    """Judge configuration for the UI: which providers have credentials (env
    or UI-saved), the provider catalogue (labels, default models), the current
    selection, and the last judge-call outcome. NEVER returns key values."""
    try:
        from clawmetry import eval_runner
    except Exception as e:
        return jsonify({"error": f"eval runner unavailable: {e}"}), 503
    try:
        present = eval_runner.judge_keys_present()
    except Exception:
        present = {}
    providers = {}
    try:
        for pid, info in eval_runner.JUDGE_PROVIDERS_INFO.items():
            providers[pid] = {
                "label": info["label"],
                "default_model": info["default_model"],
                "key_hint": info["key_hint"],
                "needs_base_url": info["needs_base_url"],
                "env": list(info["env"]),
            }
    except Exception:
        pass
    selection = {}
    try:
        rubric = eval_runner.load_rubric("default") or {}
        selection = {
            "provider": eval_runner.judge_provider_for(rubric),
            "model": str(rubric.get("judge_model") or ""),
        }
    except Exception:
        pass
    payload = {
        "present": present,
        "any": any(present.values()),
        "providers": providers,
        "selection": selection,
    }
    try:
        payload["base_url_set"] = bool(eval_runner.judge_base_url())
        payload["last_status"] = eval_runner.last_judge_status()
    except Exception:
        pass
    return jsonify(payload)


@bp_evals.route("/api/evals/key", methods=["POST"])
@gate("eval_suite")
def evals_key_save():
    """Save a judge credential + provider/model selection in one step.

    Body: ``{"provider": <id>, "api_key": "<key>", "model": "<optional>",
    "base_url": "<custom provider only>", "validate": true}``.

    By default the key is VERIFIED with a tiny real call before anything is
    written — a mistyped paste comes back as a 400 with a plain reason instead
    of being saved and silently failing forever (issue #4313). ``validate:
    false`` skips the check. An empty ``api_key`` clears the stored key for
    that provider (no validation). Keys live chmod 600 on disk only and are
    never echoed back or synced to the cloud."""
    try:
        from clawmetry import eval_runner
    except Exception as e:
        return jsonify({"error": f"eval runner unavailable: {e}"}), 503
    body = request.get_json(silent=True) or {}
    provider = str(body.get("provider", "")).strip().lower()
    api_key = body.get("api_key", "")
    model = str(body.get("model", "") or "").strip()
    base_url = body.get("base_url")
    do_validate = body.get("validate", True) not in (False, "false", "0", 0)
    if provider not in eval_runner._JUDGE_PROVIDERS:
        return jsonify({
            "error": f"provider must be one of {list(eval_runner._JUDGE_PROVIDERS)}",
        }), 400
    if not isinstance(api_key, str):
        return jsonify({"error": "api_key must be a string"}), 400
    if base_url is not None and not isinstance(base_url, str):
        return jsonify({"error": "base_url must be a string"}), 400

    clearing = not api_key.strip()
    if clearing and provider == "custom" and (base_url or "").strip():
        # Local OpenAI-compatible servers legitimately have no key.
        clearing = False
    if not clearing and do_validate:
        ok, detail = eval_runner.validate_judge_key(
            provider,
            api_key=api_key.strip() or None,
            model=model or None,
            base_url=(base_url or "").strip() or None,
        )
        if not ok:
            return jsonify({"ok": False, "error": detail}), 400
    try:
        eval_runner.save_judge_key(
            provider, api_key,
            base_url=base_url if provider == "custom" else None,
        )
        if not clearing:
            eval_runner.set_judge_selection(provider, model)
    except Exception as e:
        return jsonify({"error": f"save failed: {e}"}), 400
    return jsonify({
        "ok": True,
        "present": eval_runner.judge_keys_present(),
        "provider": provider,
        "model": model or eval_runner.JUDGE_PROVIDERS_INFO[provider]["default_model"],
        "validated": bool(not clearing and do_validate),
    })


@bp_evals.route("/api/evals/rubric", methods=["POST"])
@gate("eval_suite")
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
