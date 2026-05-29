"""routes/selfevolve.py: OSS stub after the impl moved to clawmetry-pro.

The real Self-Evolve impl (analyze, fix, fix-status, save-as-asset)
ships in the closed-source ``clawmetry-pro`` package as
``clawmetry_pro/routes/selfevolve.py``. When that package is installed
its blueprint registers via the ``clawmetry.extensions`` entry point at
app startup and wins the URL routes. When clawmetry-pro is NOT installed
this stub returns HTTP 402 ``upgrade_required`` at every URL the impl
used to serve.

dashboard.py decides which blueprint to register by inspecting
``clawmetry_pro.is_loaded()`` so the two never coexist on the URL map.
"""
from __future__ import annotations

import logging

from flask import Blueprint, jsonify

logger = logging.getLogger("clawmetry.routes.selfevolve")

bp_selfevolve = Blueprint("selfevolve", __name__)


_UPGRADE = {
    "error": "upgrade_required",
    "feature": "self_evolve",
    "hint": (
        "Self-Evolve is a Pro feature. Install ``clawmetry-pro`` with a "
        "valid license key, or use Cloud Pro at clawmetry.com/pricing."
    ),
}


@bp_selfevolve.route("/api/selfevolve/status")
def _status_stub():
    return jsonify(_UPGRADE), 402


@bp_selfevolve.route("/api/selfevolve/latest")
def _latest_stub():
    return jsonify(_UPGRADE), 402


@bp_selfevolve.route("/api/selfevolve/analyze", methods=["POST"])
def _analyze_stub():
    return jsonify(_UPGRADE), 402


@bp_selfevolve.route("/api/selfevolve/fix", methods=["POST"])
def _fix_stub():
    return jsonify(_UPGRADE), 402


@bp_selfevolve.route("/api/selfevolve/fix/status")
def _fix_status_stub():
    return jsonify(_UPGRADE), 402


@bp_selfevolve.route(
    "/api/selfevolve/findings/<finding_id>/save-as-asset",
    methods=["POST"],
)
def _save_as_asset_stub(finding_id: str):
    return jsonify(_UPGRADE), 402
