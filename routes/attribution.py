"""routes/attribution.py: the Delivery read API.

What did the money buy? Every cost surface in ClawMetry answers "what did
this session / runtime / model cost"; this one answers "what did this pull
request cost", which is the question a team actually budgets and reviews by.

Data comes from ``session_artifacts``, written by the daemon's attribution
pass (``clawmetry/sync.py::_attribution_tick`` over
``clawmetry/attribution.py``). Handlers read DuckDB through the daemon
proxy and never scan a transcript themselves, so the hosted dashboard gets
the same shape from the snapshot that a local one gets from the store.

Two honesty rules the endpoints keep:

* **The remainder is always reported.** ``totals.unattributed_usd`` rides
  with every response. Attributed spend shown on its own reads as the whole
  bill, and on a real node most of the bill is not attributable to any pull
  request.
* **An empty answer says which empty it is.** "Attribution has not run
  yet", "this runtime delivered nothing in range" and "the store could not
  be reached" are three different situations and a bare ``[]`` blurs them.
"""
from __future__ import annotations

import logging

from flask import Blueprint, jsonify, request

logger = logging.getLogger("clawmetry.routes.attribution")

bp_attribution = Blueprint("attribution", __name__)

#: Artifact kinds a caller may ask for. ``pr`` is the default because it is
#: the only kind that carries money.
_KINDS = ("pr", "repo", "branch", "commit", "file")


def _via_daemon(method: str, **kwargs):
    """Read through the daemon (it owns the writer lock), else read-only.

    Returns ``None`` when neither path works, which the handlers turn into
    an honest "store unreachable" rather than an empty list.
    """
    try:
        from routes.local_query import local_store_via_daemon
        body = local_store_via_daemon(method, **kwargs)
        if body is not None:
            return body
    except Exception:
        pass
    try:
        from clawmetry import local_store
        return getattr(local_store.get_store(read_only=True), method)(**kwargs)
    except Exception as exc:  # noqa: BLE001
        logger.debug("attribution: %s unreachable: %s", method, exc)
        return None


def _runtime_filter():
    """The global runtime switcher's value, or None for node-wide.

    Filtering happens server-side in SQL (``query_delivery(runtime=...)``);
    slicing a pre-aggregated blob in the browser is the thing that silently
    shows node-wide numbers under a runtime filter.
    """
    value = (request.args.get("runtime") or "").strip()
    if not value or value.lower() in ("all", "any", "*"):
        return None
    return value[:64]


@bp_attribution.route("/api/delivery")
def api_delivery():
    """Delivered artifacts with the spend attributed to each.

    Query: ``runtime`` (scopes to one runtime), ``kind`` (default ``pr``),
    ``since`` (ISO timestamp), ``limit`` (1-500, default 100).
    """
    kind = (request.args.get("kind") or "pr").strip().lower()
    if kind not in _KINDS:
        return jsonify({
            "error": "unknown kind",
            "hint": f"kind must be one of: {', '.join(_KINDS)}",
        }), 400
    since = (request.args.get("since") or "").strip() or None
    try:
        limit = int(request.args.get("limit") or 100)
    except (TypeError, ValueError):
        limit = 100
    runtime = _runtime_filter()

    body = _via_daemon("query_delivery", kind=kind, runtime=runtime,
                       since=since, limit=limit)
    if not isinstance(body, dict):
        return jsonify({
            "rows": [], "totals": {}, "available": False,
            "kind": kind, "runtime": runtime,
            "reason": "The local store could not be reached, so delivery "
                      "could not be read. It is usually the sync daemon "
                      "being restarted.",
        })
    rows = body.get("rows") or []
    totals = body.get("totals") or {}
    out = {
        "rows": rows,
        "totals": totals,
        "available": True,
        "kind": kind,
        "runtime": runtime,
        # What the cost column means, carried next to the numbers so a
        # reader never has to guess whether it is a share or a total.
        "cost_note": (
            "Spend is split between the pull requests a session touched, "
            "not copied onto each. Work that named no pull request is "
            "counted in unattributed."
        ),
    }
    if not rows:
        attributed = 0.0
        try:
            attributed = float(totals.get("attributed_usd") or 0.0)
        except (TypeError, ValueError):
            attributed = 0.0
        if runtime and attributed == 0.0:
            out["reason"] = (
                f"No {kind} delivery recorded for this runtime yet. "
                "Switch to all runtimes to see the rest of this machine."
            )
        else:
            out["reason"] = (
                "Nothing attributed yet. Delivery is read from what your "
                "agents did, so it fills in as sessions reference a pull "
                "request, and the first pass over existing history can take "
                "a few minutes."
            )
    return jsonify(out)


@bp_attribution.route("/api/delivery/session/<path:session_id>")
def api_delivery_session(session_id):
    """Everything one session delivered, with the evidence for each link.

    The evidence string is why this endpoint exists: a file-touch or a
    reference is an association, never proof that this session caused that
    pull request, so a reviewer gets the literal text behind the claim and
    can judge it. Evidence is redacted before it is ever stored.
    """
    sid = (session_id or "").strip()
    if not sid or len(sid) > 300:
        return jsonify({"error": "session_id required"}), 400
    rows = _via_daemon("query_session_artifacts", session_id=sid)
    if rows is None:
        return jsonify({
            "session_id": sid, "artifacts": [], "available": False,
            "reason": "The local store could not be reached.",
        })
    if isinstance(rows, dict):
        rows = rows.get("rows") or []
    return jsonify({
        "session_id": sid,
        "artifacts": rows,
        "available": True,
        "basis_note": (
            "A link is an association, not proof that this session caused "
            "the change. Evidence shows the text the link was read from."
        ),
    })
