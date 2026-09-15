"""routes/projects.py — project attribution and per-project budgets (REQ-OBS-PRJ-001).

  GET    /api/projects                      — spend per project over ?days= (default 30)
  GET    /api/projects/assignments          — assignment history, superseded rows marked
  POST   /api/projects/assignments          — assign a project or a session to a named project
  GET    /api/projects/budgets              — budgets with current-period burn
  POST   /api/projects/budgets              — create or replace a project's budget
  DELETE /api/projects/budgets/<budget_id>  — remove a budget
  GET    /api/projects/budgets/alerts       — threshold crossings recorded so far

The per-project CSV is ``GET /api/usage/export?by=project`` (``routes/usage.py``),
built by :func:`project_usage_csv` here so both share one column contract.

A project is derived when read from where each session ran
(``clawmetry/project_attribution.py``); the store surface is
``clawmetry/local_store_projects.py``. Published rows carry a label and an
opaque id, never the local path. Budget alerts are notifications: nothing
here pauses, stops or blocks an agent.

CLOUD CONTRACT: every handler never raises and answers HTTP 200 with
``available: false`` and a reason when there is no local store (the hosted
container), so a fall-through renders an honest empty state, not an error.
"""
from __future__ import annotations

import csv
import io
import logging

from flask import Blueprint, jsonify, request

from clawmetry._gate import gate
from clawmetry import cost_basis as _cost_basis
from clawmetry import provenance as _prov
from clawmetry.config import is_local_store_read_enabled

logger = logging.getLogger("clawmetry.routes.projects")

bp_projects = Blueprint("projects", __name__)

_READ_METHODS = frozenset({
    "query_project_usage", "query_project_assignments", "query_project_budgets",
    "project_budget_status", "query_project_budget_alerts",
})


def _store_call(method_name: str, **kwargs):
    """Daemon proxy first (the daemon owns the writer lock), direct open as a
    single-process fallback. ``None`` when neither answers."""
    try:
        from routes.local_query import local_store_via_daemon

        result = local_store_via_daemon(method_name, **kwargs)
        if result is not None:
            return result
    except Exception:  # noqa: BLE001
        pass
    try:
        from clawmetry import local_store

        store = local_store.get_store(read_only=method_name in _READ_METHODS)
        return getattr(store, method_name)(**kwargs)
    except Exception as e:  # noqa: BLE001
        logger.debug("projects: %s unavailable: %s", method_name, e)
        return None


def _unavailable(reason: str, **extra):
    body = {"available": False, "reason": reason}
    body.update(extra)
    return jsonify(body), 200


def _actor() -> str:
    try:
        return request.headers.get("X-Cm-User") or request.remote_addr or "dashboard"
    except Exception:  # noqa: BLE001
        return "dashboard"


def _audit(action: str, **kwargs) -> None:
    try:
        from clawmetry import audit as _a
        _a.audit_event(action, **kwargs)
    except Exception:  # noqa: BLE001
        pass


def _days_arg(default: int = 30) -> int:
    try:
        return max(1, min(366, int(request.args.get("days", default))))
    except (TypeError, ValueError):
        return default


# ── What kind of money these figures are (REQ-OBS-CEA-025) ─────────────────
#
# Every dollar figure here is the same sum the Cost tab shows: the runtime's
# own per-call cost, else the published price table. That is usage value at
# published rates, not an invoice, and it says so through the shared
# cost_basis vocabulary rather than a word of its own.

_PROJECT_COST_SOURCE = "duckdb:events joined to sessions, git_repos and project_assignments"
_PROJECT_COST_FORMULA = ("sum of each deduplicated event's cost in the window, "
                         "grouped by the project its session resolves to")
_BUDGET_COST_FORMULA = ("sum of each deduplicated event's cost in 15-minute UTC "
                        "buckets inside the budget period on the budget's timezone, "
                        "over the sessions that resolve to or ran in the project")


def _cost_labels() -> dict:
    return {"cost_basis": _cost_basis.PUBLISHED_RATE,
            "cost_basis_label": _cost_basis.COST_BASIS_LABEL[_cost_basis.PUBLISHED_RATE],
            "cost_basis_hint": _cost_basis.COST_BASIS_HINT[_cost_basis.PUBLISHED_RATE]}


def _stamp_project_usage(data: dict) -> dict:
    """Label every cost figure in a ``query_project_usage`` payload. Never raises."""
    try:
        window = "the last %s days" % ((data.get("window") or {}).get("days") or "")
        entry = _cost_basis.published_rate(_PROJECT_COST_FORMULA, _PROJECT_COST_SOURCE,
                                           window=window.strip())
        data.update(_cost_labels())
        _prov.stamp(data, {k: entry for k in (
            "projects[].cost_usd", "totals.cost_usd", "totals.derived_cost_usd",
            "totals.assigned_cost_usd", "totals.unassigned_cost_usd")})
    except Exception as e:  # noqa: BLE001
        logger.debug("projects: provenance stamp failed: %s", e)
    return data


def _stamp_budget_payload(data: dict, collection: str) -> dict:
    """Label spend in a budget status or alerts payload. Never raises."""
    try:
        entry = _cost_basis.published_rate(_BUDGET_COST_FORMULA, _PROJECT_COST_SOURCE,
                                           window="the budget's period")
        keys = (f"{collection}[].spent_usd",)
        if collection == "budgets":
            keys += ("budgets[].previous_period.spent_usd", "budgets[].burn[].spent_usd",
                     "budgets[].alerts[].spent_usd")
        data.update(_cost_labels())
        _prov.stamp(data, {k: entry for k in keys})
    except Exception as e:  # noqa: BLE001
        logger.debug("projects: provenance stamp failed: %s", e)
    return data


@bp_projects.route("/api/projects", methods=["GET"])
def api_projects():
    if not is_local_store_read_enabled():
        return _unavailable("local_store_disabled", projects=[], totals={})
    data = _store_call("query_project_usage", days=_days_arg())
    if not isinstance(data, dict):
        return _unavailable("local_store_unavailable", projects=[], totals={})
    return jsonify(_stamp_project_usage(data))


@bp_projects.route("/api/projects/assignments", methods=["GET"])
def api_project_assignments():
    if not is_local_store_read_enabled():
        return _unavailable("local_store_disabled", assignments=[])
    rows = _store_call("query_project_assignments")
    if rows is None:
        return _unavailable("local_store_unavailable", assignments=[])
    return jsonify({"available": True, "assignments": rows})


@bp_projects.route("/api/projects/assignments", methods=["POST"])
def api_project_assignment_add():
    if not is_local_store_read_enabled():
        return jsonify({"ok": False, "error": "local store disabled"}), 200
    body = request.get_json(silent=True)
    if not isinstance(body, dict):
        return jsonify({"ok": False, "error": "request body must be a JSON object"}), 400
    actor = _actor()
    res = _store_call(
        "add_project_assignment",
        match_type=body.get("match_type") or "", match_value=body.get("match_value") or "",
        project_name=body.get("project_name") or "", reason=body.get("reason") or "",
        effective_from=body.get("effective_from"), effective_to=body.get("effective_to"),
        actor=actor)
    if not isinstance(res, dict):
        return jsonify({"ok": False, "error": "could not save the assignment"}), 200
    if not res.get("ok"):
        return jsonify(res), 400
    _audit("project.assign", actor=actor, target=res["assignment"].get("match_value"),
           result="recorded", source="dashboard",
           metadata={"project_name": res["assignment"].get("project_name"),
                     "match_type": res["assignment"].get("match_type")})
    return jsonify(res)


@bp_projects.route("/api/projects/budgets", methods=["GET"])
@gate("budget_limits")
def api_project_budgets():
    if not is_local_store_read_enabled():
        return _unavailable("local_store_disabled", budgets=[])
    data = _store_call("project_budget_status")
    if not isinstance(data, dict):
        return _unavailable("local_store_unavailable", budgets=[])
    return jsonify(_stamp_budget_payload(data, "budgets"))


@bp_projects.route("/api/projects/budgets", methods=["POST"])
@gate("budget_limits")
def api_project_budget_upsert():
    if not is_local_store_read_enabled():
        return jsonify({"ok": False, "error": "local store disabled"}), 200
    body = request.get_json(silent=True)
    if not isinstance(body, dict):
        return jsonify({"ok": False, "error": "request body must be a JSON object"}), 400
    actor = _actor()
    res = _store_call(
        "upsert_project_budget",
        project_id=body.get("project_id") or "", amount=body.get("amount"),
        currency=body.get("currency") or "", period=body.get("period") or "",
        timezone_name=body.get("timezone") or "", basis=body.get("basis") or "",
        actor=actor)
    if not isinstance(res, dict):
        return jsonify({"ok": False, "error": "could not save the budget"}), 200
    if not res.get("ok"):
        return jsonify(res), 400
    _audit("project.budget_set", actor=actor, target=body.get("project_id"),
           result="updated", source="dashboard", metadata=res.get("budget") or {})
    return jsonify(res)


@bp_projects.route("/api/projects/budgets/<budget_id>", methods=["DELETE"])
@gate("budget_limits")
def api_project_budget_delete(budget_id: str):
    if not is_local_store_read_enabled():
        return jsonify({"ok": False, "error": "local store disabled"}), 200
    res = _store_call("delete_project_budget", budget_id=budget_id)
    if not isinstance(res, dict):
        return jsonify({"ok": False, "error": "could not remove the budget"}), 200
    if not res.get("ok"):
        return jsonify(res), 400
    _audit("project.budget_delete", actor=_actor(), target=budget_id,
           result="deleted", source="dashboard", metadata={"deleted": res.get("deleted")})
    return jsonify(res)


@bp_projects.route("/api/projects/budgets/alerts", methods=["GET"])
@gate("budget_limits")
def api_project_budget_alerts():
    if not is_local_store_read_enabled():
        return _unavailable("local_store_disabled", alerts=[])
    rows = _store_call("query_project_budget_alerts", limit=200)
    if rows is None:
        return _unavailable("local_store_unavailable", alerts=[])
    return jsonify(_stamp_budget_payload({"available": True, "alerts": rows}, "alerts"))


# ── CSV (served from /api/usage/export?by=project) ────────────────────────

PROJECT_CSV_COLUMNS = [
    "row_type", "project_id", "project", "source", "confidence", "cost_usd",
    "priced_tokens", "unpriced_tokens", "unpriced_events", "sessions", "runtimes",
    "derived_cost_usd", "assigned_cost_usd", "unassigned_cost_usd",
    "priced_token_share", "attributed_cost_share", "currency", "basis",
    "window_since", "window_until", "cost_basis",
]


def _cell(v):
    s = "" if v is None else str(v)
    # A label that starts like a formula would execute in a spreadsheet.
    if s[:1] in ("=", "+", "-", "@", "\t", "\r"):
        s = "'" + s
    return s


def project_usage_csv(data: dict) -> str:
    """One row per project plus one ``total`` row carrying the assigned,
    derived, unassigned and unpriced figures and the completeness shares."""
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(PROJECT_CSV_COLUMNS)
    window = data.get("window") or {}
    common = {"currency": data.get("currency", "USD"), "basis": data.get("basis", ""),
              "window_since": window.get("since", ""), "window_until": window.get("until", ""),
              # Usage value at published rates (REQ-OBS-CEA-025), not an invoice.
              "cost_basis": _cost_basis.PUBLISHED_RATE}
    for p in data.get("projects") or []:
        row = dict(common, row_type="project", project_id=p.get("project_id"),
                   project=p.get("label"), source=p.get("source"),
                   confidence=p.get("confidence"), cost_usd=f"{float(p.get('cost_usd') or 0):.6f}",
                   priced_tokens=p.get("priced_tokens"), unpriced_tokens=p.get("unpriced_tokens"),
                   unpriced_events=p.get("unpriced_events"), sessions=p.get("sessions"),
                   runtimes=";".join(p.get("runtimes") or []))
        w.writerow([_cell(row.get(c)) for c in PROJECT_CSV_COLUMNS])
    t = data.get("totals") or {}
    comp = t.get("completeness") or {}
    row = dict(common, row_type="total", cost_usd=f"{float(t.get('cost_usd') or 0):.6f}",
               priced_tokens=t.get("priced_tokens"), unpriced_tokens=t.get("unpriced_tokens"),
               unpriced_events=t.get("unpriced_events"), sessions=t.get("sessions"),
               derived_cost_usd=f"{float(t.get('derived_cost_usd') or 0):.6f}",
               assigned_cost_usd=f"{float(t.get('assigned_cost_usd') or 0):.6f}",
               unassigned_cost_usd=f"{float(t.get('unassigned_cost_usd') or 0):.6f}",
               priced_token_share=comp.get("priced_token_share"),
               attributed_cost_share=comp.get("attributed_cost_share"))
    w.writerow([_cell(row.get(c)) for c in PROJECT_CSV_COLUMNS])
    return buf.getvalue()
