"""routes/signals.py: Behaviour Signals read API (WO-58).

What people and agents *say* about a run, counted over every transcript the
store already holds: frustration, praise, refusals, work handed back, giving
up, retries. Three read-only endpoints, all served from the local DuckDB
store through the daemon query proxy (never raw files), so the hosted
dashboard can serve the same shape from the snapshot slice
(``sync_system_snapshot`` -> ``signals`` / ``signalsByRuntime``).

  GET /api/signals?window=1d|7d|30d&runtime=<id>
      per signal: rate, count, eligible turns, trend vs the previous
      window, per-day series, by_model, by_runtime_version; plus
      ``coverage`` per runtime and a plain-words ``headline``.
  GET /api/signals/<name>/sessions?window=&runtime=
      matching sessions (id, runtime, model, started, cost, match count).
      Never the matched phrases.
  GET /api/signals/coverage
      which runtimes expose user text, assistant text, both or neither.

Signal shifts + briefs (WO-62, clawmetry/signal_shifts.py, briefs.py):

  GET  /api/signals/issues?status=open|resolved|ignored|all&runtime=
      issues opened when a rate left its learned band, each with a
      plain-words headline and the ranked breakdown. Never text.
  POST /api/signals/issues/<id>/status   {status: resolved|ignored|open}
  GET  /api/briefs            saved questions on a schedule (+ the built-in
                              daily digest offer when it is not saved yet)
  POST /api/briefs            create or update one (capped per node)
  DELETE /api/briefs/<id>
  POST /api/briefs/<id>/run   run it now and post to its channel
  The mutating routes are origin-checked like the Guard controls.

Entitlement: free on every tier. Paid runtimes are gated where they are
ingested (the daemon loads only entitled adapters), so a runtime with rows
in the store is one the install is entitled to see; the response is also
filtered through ``Entitlement.allows_runtime`` so a lapsed key never
shows a paid runtime's numbers.
"""
from __future__ import annotations

import logging
import time

from flask import Blueprint, jsonify, request

log = logging.getLogger("clawmetry.routes.signals")

bp_signals = Blueprint("signals", __name__)

_WINDOWS = {"1d": 1, "7d": 7, "30d": 30}
_DAY_MS = 86400 * 1000


def _ls_call(method_name, **kwargs):
    """Cross-process LocalStore call with single-process fallback (mirror of
    ``routes/guard.py::_ls_call``). Returns ``None`` when neither the daemon
    proxy nor a read-only open is available, which the endpoints turn into
    an honest ``store: "unavailable"`` rather than a fabricated zero."""
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


class _ProxyStore:
    """Duck-typed store the pure helpers in ``behaviour_signals`` call; every
    read goes through :func:`_ls_call`. ``None`` results are remembered so
    the endpoint can say the store was unreachable."""

    def __init__(self):
        self.unavailable = False

    def _call(self, method, **kw):
        r = _ls_call(method, **kw)
        if r is None:
            self.unavailable = True
        return r

    def query_signal_grouped(self, **kw):
        return self._call("query_signal_grouped", **kw)

    def query_signal_coverage(self, **kw):
        return self._call("query_signal_coverage", **kw)

    def query_signal_sessions(self, **kw):
        return self._call("query_signal_sessions", **kw)

    def _call_nullable(self, method, probe, probe_kw, **kw):
        """For store methods whose honest answer can be ``None`` ("no such
        row"): a ``None`` is only "unavailable" when a cheap probe read is
        ``None`` too."""
        r = _ls_call(method, **kw)
        if r is None and _ls_call(probe, **probe_kw) is None:
            self.unavailable = True
        return r

    def query_signal_issues(self, **kw):
        return self._call("query_signal_issues", **kw)

    def get_signal_issue(self, **kw):
        return self._call_nullable("get_signal_issue", "query_signal_issues", {"limit": 1}, **kw)

    def set_signal_issue_status(self, **kw):
        return self._call_nullable("set_signal_issue_status", "query_signal_issues", {"limit": 1}, **kw)

    def list_briefs(self, **kw):
        return self._call("list_briefs", **kw)

    def get_brief(self, **kw):
        return self._call_nullable("get_brief", "list_briefs", {"limit": 1}, **kw)

    def upsert_brief(self, **kw):
        return self._call("upsert_brief", **kw)

    def delete_brief(self, **kw):
        return self._call("delete_brief", **kw)

    def mark_brief_run(self, **kw):
        return self._call("mark_brief_run", **kw)

    def raw_select_safe(self, **kw):
        return self._call("raw_select_safe", **kw)

    def dives_table_columns(self, table=None, **kw):
        if table is not None:
            kw["table"] = table
        return self._call("dives_table_columns", **kw)


def _window() -> tuple[str, int]:
    w = str(request.args.get("window") or "7d").strip().lower()
    if w not in _WINDOWS:
        w = "7d"
    return w, _WINDOWS[w]


def _runtime() -> str | None:
    rt = str(request.args.get("runtime") or "").strip().lower()
    if not rt or rt == "all":
        return None
    return rt[:64]


def _runtime_allowed(rt: str) -> bool:
    try:
        from clawmetry import entitlements as _ent
        return bool(_ent.get_entitlement().allows_runtime(rt))
    except Exception:
        return True


def _strip_unentitled(body: dict) -> dict:
    """Drop paid runtimes the install is not entitled to from the per-runtime
    buckets and the coverage strip. Fails open on an entitlement error: the
    daemon never ingested a runtime it was not entitled to."""
    try:
        cov = body.get("coverage") or {}
        for rt in list(cov):
            if not _runtime_allowed(rt):
                cov.pop(rt, None)
        for s in (body.get("signals") or {}).values():
            by_rt = s.get("by_runtime") or {}
            for rt in list(by_rt):
                if not _runtime_allowed(rt):
                    by_rt.pop(rt, None)
    except Exception:
        pass
    return body


@bp_signals.route("/api/signals")
def api_signals():
    """Rates for every preset signal over the window, scoped to ``runtime``
    when one is given (the runtime switcher's contract: every number on the
    surface re-derives from this filter)."""
    from clawmetry import behaviour_signals as _bs
    win, days = _window()
    rt = _runtime()
    if rt and not _runtime_allowed(rt):
        return jsonify({"error": "runtime not entitled", "runtime": rt,
                        "window": win}), 402
    store = _ProxyStore()
    try:
        body = _bs.full_report(store, days, rt)
    except Exception as e:  # noqa: BLE001
        log.warning("signals: report failed: %s", e)
        body = _bs.shape_rates([], [], window_days=days, runtime=rt)
        body["coverage"] = {}
        body["headline"] = _bs.headline(body)
    body["store"] = "unavailable" if store.unavailable else "ok"
    body["window"] = win
    return jsonify(_strip_unentitled(body))


@bp_signals.route("/api/signals/coverage")
def api_signals_coverage():
    """Per runtime: does the store hold user text, assistant text, both or
    neither. An adapter that declares ``signal_coverage()`` overrides the
    inference. A runtime with ``state: "none"`` must read "not exposed by
    this runtime" on the surface, never 0%."""
    from clawmetry import behaviour_signals as _bs
    store = _ProxyStore()
    try:
        cov = _bs.coverage_for(store, days=30)
    except Exception as e:  # noqa: BLE001
        log.warning("signals: coverage failed: %s", e)
        cov = {}
    body = {"coverage": cov, "store": "unavailable" if store.unavailable else "ok",
            "states": ["user_text", "assistant_text", "user_text+assistant_text", "none"]}
    return jsonify(_strip_unentitled(body))


@bp_signals.route("/api/signals/<name>/sessions")
def api_signal_sessions(name):
    """Sessions that matched ``name`` in the window. Lists sessions, never
    phrases: the transcript viewer shows the turn under its own access
    rules."""
    from clawmetry import behaviour_signals as _bs
    sig = str(name or "").strip()
    if sig not in _bs.SIGNALS:
        return jsonify({"error": "unknown signal", "signal": sig,
                        "allowed": sorted(_bs.SIGNALS)}), 404
    win, days = _window()
    rt = _runtime()
    if rt and not _runtime_allowed(rt):
        return jsonify({"error": "runtime not entitled", "runtime": rt}), 402
    try:
        limit = max(1, min(int(request.args.get("limit", 50)), 200))
    except (TypeError, ValueError):
        limit = 50
    since_ms = int(time.time() * 1000) - days * _DAY_MS
    store = _ProxyStore()
    rows = store.query_signal_sessions(signal=sig, since_ms=since_ms,
                                       runtime=rt, limit=limit) or []
    rows = [r for r in rows if isinstance(r, dict)
            and _runtime_allowed(str(r.get("runtime") or ""))]
    return jsonify({
        "signal": sig, "label": _bs.SIGNALS[sig]["label"],
        "window": win, "runtime": rt or "all",
        "sessions": rows, "count": len(rows),
        "store": "unavailable" if store.unavailable else "ok",
    })


# ── Signal shifts: issues (WO-62) ──────────────────────────────────────────

def _origin_ok() -> bool:
    try:
        from routes.guard import _same_origin_ok
        return bool(_same_origin_ok())
    except Exception:  # noqa: BLE001
        return True


def _with_headline(issue: dict) -> dict:
    from clawmetry import signal_shifts as _shifts
    out = dict(issue)
    try:
        out["headline"] = _shifts.issue_headline(out)
    except Exception:  # noqa: BLE001
        out["headline"] = ""
    return out


@bp_signals.route("/api/signals/issues")
def api_signal_issues():
    """Issues newest first. ``status`` defaults to ``open``; ``all`` lists
    every state. Scoped to ``runtime`` when the switcher names one."""
    from clawmetry import signal_shifts as _shifts
    status = str(request.args.get("status") or "open").strip().lower()
    if status not in ("open", "resolved", "ignored", "all"):
        status = "open"
    rt = _runtime()
    if rt and not _runtime_allowed(rt):
        return jsonify({"error": "runtime not entitled", "runtime": rt}), 402
    try:
        limit = max(1, min(int(request.args.get("limit", 100)), 500))
    except (TypeError, ValueError):
        limit = 100
    store = _ProxyStore()
    rows = store.query_signal_issues(status=None if status == "all" else status,
                                     runtime=rt, limit=limit) or []
    items = [_with_headline(r) for r in rows if isinstance(r, dict)
             and _runtime_allowed(str(r.get("agent_type") or ""))]
    return jsonify({
        "issues": items, "count": len(items), "status": status, "runtime": rt or "all",
        "store": "unavailable" if store.unavailable else "ok",
        "min_samples": {"short": _shifts.MIN_SHORT, "history": _shifts.MIN_HISTORY,
                        "short_hours": _shifts.SHORT_HOURS, "history_days": _shifts.HISTORY_DAYS},
    })


@bp_signals.route("/api/signals/issues/<issue_id>/status", methods=["POST"])
def api_signal_issue_status(issue_id):
    """Operator transition. ``resolved`` lets the issue reopen if the rate
    shifts again later; ``ignored`` keeps it silent until reopened here."""
    if not _origin_ok():
        return jsonify({"ok": False, "error": "cross-origin request refused"}), 403
    body = request.get_json(silent=True) or {}
    status = str(body.get("status") or "").strip().lower()
    if status not in ("open", "resolved", "ignored"):
        return jsonify({"ok": False, "error": "status must be open, resolved or ignored"}), 400
    store = _ProxyStore()
    issue = store.set_signal_issue_status(issue_id=str(issue_id)[:64], status=status)
    if not issue:
        code = 503 if store.unavailable else 404
        return jsonify({"ok": False, "error": "store unavailable" if store.unavailable
                        else "no such issue"}), code
    return jsonify({"ok": True, "issue": _with_headline(issue)})


# ── Briefs (WO-62) ─────────────────────────────────────────────────────────

def _brief_public(b: dict) -> dict:
    from clawmetry import briefs as _briefs
    out = dict(b)
    out["builtin"] = str(out.get("id") or "") == _briefs.BUILTIN_DAILY_DIGEST_ID
    return out


@bp_signals.route("/api/briefs")
def api_briefs_list():
    from clawmetry import briefs as _briefs
    store = _ProxyStore()
    rows = [_brief_public(b) for b in (store.list_briefs() or []) if isinstance(b, dict)]
    offered = None
    if not any(b.get("id") == _briefs.BUILTIN_DAILY_DIGEST_ID for b in rows):
        offered = dict(_briefs.BUILTIN_DAILY_DIGEST)
    return jsonify({
        "briefs": rows, "count": len(rows), "max": _briefs.BRIEFS_MAX,
        "channels": list(_briefs.CHANNELS), "offered": offered,
        "store": "unavailable" if store.unavailable else "ok",
    })


@bp_signals.route("/api/briefs", methods=["POST"])
def api_briefs_save():
    """Create or update a brief. Sending ``{"id": "builtin_daily_digest",
    "enabled": true}`` saves the built-in digest with its defaults."""
    from clawmetry import briefs as _briefs
    if not _origin_ok():
        return jsonify({"ok": False, "error": "cross-origin request refused"}), 403
    raw = request.get_json(silent=True) or {}
    if not isinstance(raw, dict):
        return jsonify({"ok": False, "error": "body must be an object"}), 400
    if str(raw.get("id") or "") == _briefs.BUILTIN_DAILY_DIGEST_ID:
        merged = dict(_briefs.BUILTIN_DAILY_DIGEST)
        for k in ("cron_expr", "tz", "channel_ref", "enabled"):
            if k in raw:
                merged[k] = raw[k]
        raw = merged
    brief, err = _briefs.validate_brief(raw)
    if err:
        return jsonify({"ok": False, "error": err}), 400
    store = _ProxyStore()
    existing = store.list_briefs() or []
    if not any(b.get("id") == brief["id"] for b in existing if isinstance(b, dict)) \
            and len(existing) >= _briefs.BRIEFS_MAX:
        return jsonify({"ok": False, "error": f"this node already has {_briefs.BRIEFS_MAX} briefs",
                        "max": _briefs.BRIEFS_MAX}), 409
    saved = store.upsert_brief(brief=brief)
    if not saved:
        return jsonify({"ok": False, "error": "store unavailable"}), 503
    return jsonify({"ok": True, "brief": _brief_public(saved)})


@bp_signals.route("/api/briefs/<brief_id>", methods=["DELETE"])
def api_briefs_delete(brief_id):
    if not _origin_ok():
        return jsonify({"ok": False, "error": "cross-origin request refused"}), 403
    store = _ProxyStore()
    if not store.get_brief(brief_id=str(brief_id)[:64]):
        return jsonify({"ok": False, "error": "no such brief"}), 404
    ok = store.delete_brief(brief_id=str(brief_id)[:64])
    return jsonify({"ok": bool(ok)}), (200 if ok else 503)


@bp_signals.route("/api/briefs/<brief_id>/run", methods=["POST"])
def api_briefs_run(brief_id):
    """Run now, post to the brief's channel, record the outcome. A failure
    is posted too and returned here with ``status: failed``."""
    from clawmetry import briefs as _briefs
    if not _origin_ok():
        return jsonify({"ok": False, "error": "cross-origin request refused"}), 403
    store = _ProxyStore()
    brief = store.get_brief(brief_id=str(brief_id)[:64])
    if not brief:
        return jsonify({"ok": False, "error": "no such brief"}), 404
    res = _briefs.run_brief(brief, store)
    store.mark_brief_run(brief_id=brief["id"], status=res.get("status") or "failed",
                         error=res.get("error"))
    return jsonify({"ok": res.get("status") == "ok", "result": res,
                    "brief": _brief_public(store.get_brief(brief_id=brief["id"]) or brief)})
