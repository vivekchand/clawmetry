"""Capability-gap read API (#5412).

One read-only endpoint over the events the daemon already stores:

* ``GET /api/capability-gaps``   recent failures mapped to the MIX E01..E08
  taxonomy, newest first, plus the contract a consumer needs.

The classification runs on request from recent store rows, so the endpoint
answers whether or not the JSONL export is on. Reads go through the daemon
proxy (``_ls_call``), never a raw file: the daemon owns the DuckDB writer
lock and this module runs in the dashboard process. Nothing here writes.
"""
from __future__ import annotations

import logging
import time
from datetime import datetime, timezone

from flask import Blueprint, jsonify, request

from routes import event_data

log = logging.getLogger("clawmetry.capability_gaps")

bp_capability_gaps = Blueprint("capability_gaps", __name__)

#: Default lookback and the ceiling on store rows one request may scan.
DEFAULT_WINDOW_SECS = 24 * 3600
MAX_SCAN_ROWS = 5000


def _ls_call(method_name, **kwargs):
    """Cross-process LocalStore read with single-process fallback. Mirror
    of ``routes/selfdiag.py::_ls_call``."""
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


def _since_iso(window_secs: int) -> str:
    return datetime.fromtimestamp(time.time() - window_secs, tz=timezone.utc).isoformat()


@bp_capability_gaps.route("/api/capability-gaps")
@event_data
def api_capability_gaps():
    """Gap records for the window, newest first. ``session`` narrows to one
    session, ``runtime`` to one runtime, ``code`` to one taxonomy code.
    ``limit`` caps the records returned (default 200, max 2000). Always HTTP
    200 with an honest empty list and ``store_available: false`` when the
    store did not answer."""
    from clawmetry import capability_gaps as _cg
    from clawmetry.self_diagnostics import parse_window_secs

    window = parse_window_secs(request.args.get("window"), DEFAULT_WINDOW_SECS)
    session = (request.args.get("session") or request.args.get("session_id") or "").strip()
    runtime = (request.args.get("runtime") or "").strip().lower()
    runtime = "" if runtime == "all" else runtime
    code = (request.args.get("code") or "").strip().upper()
    try:
        limit = max(1, min(int(request.args.get("limit", 200)), 2000))
    except (TypeError, ValueError):
        limit = 200

    kwargs = {"limit": MAX_SCAN_ROWS, "exclude_daemon": True}
    if session:
        kwargs["session_id"] = session
    else:
        kwargs["since"] = _since_iso(window)
    if runtime:
        kwargs["runtime"] = runtime
    rows = _ls_call("query_events", **kwargs)
    available = isinstance(rows, list)
    rows = rows if available else []

    gaps = _cg.classify_events(rows, runtime=runtime)
    if code:
        gaps = [g for g in gaps if g.get("code") == code]
    gaps.sort(key=lambda g: str(g.get("ts") or ""), reverse=True)
    truncated = len(gaps) > limit
    gaps = gaps[:limit]

    by_code = {}
    for g in gaps:
        by_code[g["code"]] = by_code.get(g["code"], 0) + 1

    body = _cg.describe()
    body.update({
        "gaps": gaps,
        "count": len(gaps),
        "by_code": by_code,
        "truncated": truncated,
        "window_secs": window,
        "scanned_rows": len(rows),
        "scan_cap": MAX_SCAN_ROWS,
        "store_available": available,
        "_source": "local_store",
    })
    return jsonify(body)
