"""Free, persisted Asimov evidence. Robot connections belong to the collector."""
import logging
import re

from flask import Blueprint, jsonify, render_template, request

log = logging.getLogger("clawmetry.routes.asimov")
bp_asimov = Blueprint("asimov", __name__)
_RUN_ID = re.compile(r"^[0-9a-f]{32}$")


def _integer(name, default, minimum, maximum):
    value = request.args.get(name)
    if value is None:
        return default
    if not re.fullmatch(r"[0-9]+", value) or len(value) > 19:
        raise ValueError("invalid integer")
    number = int(value)
    if not minimum <= number <= maximum:
        raise ValueError("out of bounds")
    return number


def _call(method, **kwargs):
    from clawmetry.local_store import get_store
    return getattr(get_store(read_only=True), method)(**kwargs)


def _unavailable():
    return jsonify(available=False, message="ClawMetry cannot read stored robot evidence. Check the sync daemon and try again."), 503


@bp_asimov.get("/asimov")
def asimov_page():
    return render_template("asimov.html")


@bp_asimov.get("/api/asimov/runs")
def asimov_runs():
    try:
        if set(request.args) - {"limit", "robot_id", "before_ns", "before_run_id"}:
            raise ValueError("unknown argument")
        limit = _integer("limit", 20, 1, 100)
        before_ns = _integer("before_ns", None, 0, 2**63 - 1)
        before_run_id = request.args.get("before_run_id")
        if (before_ns is None) != (before_run_id is None):
            raise ValueError("incomplete cursor")
        if before_run_id is not None and not _RUN_ID.fullmatch(before_run_id):
            raise ValueError("invalid cursor")
        robot_id = request.args.get("robot_id")
        if robot_id is not None and (not 1 <= len(robot_id) <= 200 or any(ord(c) < 32 for c in robot_id)):
            raise ValueError("invalid robot")
    except ValueError:
        return jsonify(message="Use a valid robot filter, limit, and complete run cursor."), 400
    try:
        result = _call("query_asimov_runs", limit=limit, robot_id=robot_id,
                       before_ns=before_ns, before_run_id=before_run_id)
        if not isinstance(result, dict) or not isinstance(result.get("runs"), list):
            raise TypeError("The persisted response has an unsupported shape")
        return jsonify(result)
    except Exception as exc:  # noqa: BLE001 - daemon outages must return a useful unavailable response
        log.warning("Asimov runs unavailable: %s", type(exc).__name__)
        return _unavailable()


@bp_asimov.get("/api/asimov/runs/<run_id>/events")
def asimov_events(run_id):
    try:
        if not _RUN_ID.fullmatch(run_id) or set(request.args) - {"after", "limit"}:
            raise ValueError("invalid run or arguments")
        after = _integer("after", 0, 0, 2**63 - 1)
        limit = _integer("limit", 200, 1, 500)
    except ValueError:
        return jsonify(message="Use a valid run ID, sequence, and event limit."), 400
    try:
        result = _call("query_asimov_events", run_id=run_id, after=after, limit=limit)
        if not isinstance(result, dict) or not isinstance(result.get("events"), list):
            raise TypeError("The persisted response has an unsupported shape")
        return jsonify(result)
    except Exception as exc:  # noqa: BLE001 - daemon outages must return a useful unavailable response
        log.warning("Asimov events unavailable: %s", type(exc).__name__)
        return _unavailable()
