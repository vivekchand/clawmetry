"""routes/runtime_ingest.py: OSS stub after the impl moved to clawmetry-pro.

The real custom-runtime HTTP ingest API ships in the closed-source
``clawmetry-pro`` package as ``clawmetry_pro/routes/runtime_ingest.py``.
When that package is installed (license key or cloud Pro plan), its
blueprint registers via the ``clawmetry.extensions`` entry point at app
startup and wins the URL routes.

When clawmetry-pro is NOT installed (vanilla OSS), this stub blueprint
registers in its place and returns HTTP 402 ``upgrade_required`` on
every write endpoint. The read-only ``/api/v1/runtimes`` listing stays
free; it's the catalogue.

dashboard.py decides which blueprint to register by inspecting
``clawmetry_pro.is_loaded()`` so the two never coexist on the URL map.
"""
from __future__ import annotations

import logging

from flask import Blueprint, jsonify

logger = logging.getLogger("clawmetry.routes.runtime_ingest")

bp_runtime_ingest = Blueprint("runtime_ingest", __name__)


# Shared 402 body so the wire format is identical to ``@gate`` enforce-mode.
_UPGRADE = {
    "error": "upgrade_required",
    "feature": "custom_runtime_ingest",
    "hint": (
        "Custom runtime ingest is a Pro feature. Install ``clawmetry-pro`` "
        "with a valid license key, or use Cloud Pro at clawmetry.com/pricing."
    ),
}


@bp_runtime_ingest.route("/api/v1/runtimes", methods=["GET"])
def list_runtimes():
    """List runtimes ClawMetry knows about. Free. Same data the runtime
    switcher in the header reads. Useful for SDK clients introspecting
    what they can push to before they hit the paid write routes."""
    try:
        from clawmetry import entitlements as _ent
        rows = _ent.runtime_catalog() if hasattr(_ent, "runtime_catalog") else []
    except Exception as exc:
        logger.warning("runtime_ingest stub: runtime catalog read failed: %s", exc)
        rows = []
    return jsonify({"runtimes": rows})


@bp_runtime_ingest.route("/api/v1/runs", methods=["POST"])
def start_run_stub():
    return jsonify(_UPGRADE), 402


@bp_runtime_ingest.route("/api/v1/runs/<run_id>/events", methods=["POST"])
def append_events_stub(run_id: str):
    return jsonify(_UPGRADE), 402


@bp_runtime_ingest.route("/api/v1/runs/<run_id>/end", methods=["POST"])
def end_run_stub(run_id: str):
    return jsonify(_UPGRADE), 402


@bp_runtime_ingest.route("/api/v1/runs/<run_id>", methods=["GET"])
def get_run_stub(run_id: str):
    return jsonify(_UPGRADE), 402
