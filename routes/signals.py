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
