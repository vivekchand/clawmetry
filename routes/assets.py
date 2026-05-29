"""routes/assets.py: OSS stub after the impl moved to clawmetry-pro.

The real asset-registry impl (list, get, upsert, review) ships in the
closed-source ``clawmetry-pro`` package as
``clawmetry_pro/routes/assets.py``. When that package is installed its
blueprint registers via the ``clawmetry.extensions`` entry point at app
startup and wins the URL routes. When clawmetry-pro is NOT installed
this stub returns HTTP 402 ``upgrade_required`` at every URL the impl
used to serve.

dashboard.py decides which blueprint to register by inspecting
``clawmetry_pro.is_loaded()`` so the two never coexist on the URL map.
"""
from __future__ import annotations

import logging

from flask import Blueprint, jsonify

logger = logging.getLogger("clawmetry.routes.assets")

bp_assets = Blueprint("assets", __name__)


_UPGRADE = {
    "error": "upgrade_required",
    "feature": "asset_registry",
    "hint": (
        "Asset registry is a Pro feature. Install ``clawmetry-pro`` with a "
        "valid license key, or use Cloud Pro at clawmetry.com/pricing."
    ),
}


@bp_assets.route("/api/assets", methods=["GET"])
def _list_stub():
    return jsonify(_UPGRADE), 402


@bp_assets.route("/api/assets/<asset_id>", methods=["GET"])
def _get_stub(asset_id: str):
    return jsonify(_UPGRADE), 402


@bp_assets.route("/api/assets", methods=["POST"])
def _create_stub():
    return jsonify(_UPGRADE), 402


@bp_assets.route("/api/assets/<asset_id>/review", methods=["POST"])
def _review_stub(asset_id: str):
    return jsonify(_UPGRADE), 402
