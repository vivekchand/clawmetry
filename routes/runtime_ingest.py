"""
routes/runtime_ingest.py — Custom runtime HTTP ingest API stub.

Reserves the /api/v1/runs/* and /api/v1/engines/* namespaces so the paid
plugin (clawmetry-pro) can attach a real handler at startup. OSS installs
without the plugin get a graceful 402 with an upgrade hint rather than a
confusing 404.

  POST /api/v1/runs/<path>     — create / update a run record
  GET  /api/v1/runs/<path>     — read a run record (discovery)
  POST /api/v1/engines/<path>  — engine-side ingest (reserved)
  GET  /api/v1/engines/<path>  — engine catalog (discovery)
  (PUT, PATCH, DELETE also forwarded for completeness)

Extension hook: register a callable under event "runtime_ingest.request" via
clawmetry.extensions.register(). The handler receives:
  {"path": str, "method": str, "body": dict | None, "args": dict}
and must return a Flask response object / tuple, or None to fall through to
the 402 stub.
"""

from __future__ import annotations

import logging

from flask import Blueprint, jsonify, request

logger = logging.getLogger("clawmetry.routes.runtime_ingest")

bp_runtime_ingest = Blueprint("runtime_ingest", __name__)

_METHODS = ["GET", "POST", "PUT", "PATCH", "DELETE"]


def _try_plugin(path: str):
    """Delegate to a paid-plugin handler registered under 'runtime_ingest.request'.

    Returns the handler's Flask response tuple/object, or None if no handler
    is registered or every handler returns None.
    """
    try:
        from clawmetry.extensions import dispatch

        return dispatch(
            "runtime_ingest.request",
            {
                "path": path,
                "method": request.method,
                "body": request.get_json(silent=True),
                "args": dict(request.args),
            },
        )
    except Exception as exc:
        logger.warning("runtime_ingest: plugin dispatch error: %s", exc)
        return None


def _stub_402():
    """Return the standard 402 upgrade hint for this feature."""
    try:
        from clawmetry import entitlements as _ent

        tier = _ent.get_entitlement().to_dict().get("tier", "oss")
    except Exception:
        tier = "oss"
    return (
        jsonify(
            {
                "error": "upgrade_required",
                "feature": "custom_runtime_ingest",
                "tier": tier,
                "hint": (
                    "Custom runtime HTTP ingest is a Pro+ feature. "
                    "https://clawmetry.com/pricing"
                ),
            }
        ),
        402,
    )


@bp_runtime_ingest.route(
    "/api/v1/runs/",
    defaults={"run_path": ""},
    methods=_METHODS,
)
@bp_runtime_ingest.route("/api/v1/runs/<path:run_path>", methods=_METHODS)
def api_v1_runs(run_path: str):
    result = _try_plugin(f"runs/{run_path}" if run_path else "runs/")
    if result is not None:
        return result
    return _stub_402()


@bp_runtime_ingest.route(
    "/api/v1/engines/",
    defaults={"engine_path": ""},
    methods=_METHODS,
)
@bp_runtime_ingest.route("/api/v1/engines/<path:engine_path>", methods=_METHODS)
def api_v1_engines(engine_path: str):
    result = _try_plugin(f"engines/{engine_path}" if engine_path else "engines/")
    if result is not None:
        return result
    return _stub_402()
