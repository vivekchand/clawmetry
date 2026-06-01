"""routes/nemoclaw.py: OSS stub after the impl moved to clawmetry-pro.

The real NeMo Guardrails governance + approval-queue implementation ships
in the closed-source ``clawmetry-pro`` package as
``clawmetry_pro/routes/nemoclaw.py``. When that package is installed
(license key or cloud Pro plan), its blueprint registers via
``clawmetry_pro.register_all()`` -> ``_register_blueprints(app)`` at app
startup and wins the URL routes.

When clawmetry-pro is NOT installed (vanilla OSS), this stub blueprint
registers in its place and returns HTTP 402 ``upgrade_required`` on every
governance endpoint (governance summary, drift ack, daemon status, policy,
approve, reject, pending-approvals, rule CRUD, guardrail events, metrics).

dashboard.py decides which blueprint to register by inspecting
``clawmetry_pro.is_loaded()`` so the two never coexist on the URL map.

Mirrors the precedent set by ``routes/runtime_ingest.py`` (custom-runtime
ingest), ``routes/otel_export.py`` (OTel push), ``routes/selfevolve.py``
and ``routes/assets.py`` (asset registry) — all OSS 402-stubs whose real
impls live in clawmetry-pro.

Import-light and never-raise: the blueprint object name (``bp_nemoclaw``)
and every URL rule match the real impl so swapping the two is transparent.
"""
from __future__ import annotations

import logging

from flask import Blueprint, jsonify

logger = logging.getLogger("clawmetry.routes.nemoclaw")

bp_nemoclaw = Blueprint("nemoclaw", __name__)


# Shared 402 body so the wire format is identical across every governance
# route (and matches the ``@gate`` enforce-mode shape used elsewhere).
_UPGRADE = {
    "error": "upgrade_required",
    "feature": "nemo_governance",
    "hint": (
        "NeMo governance is a paid feature. Install clawmetry-pro with a "
        "license key, or use Cloud at clawmetry.com/pricing."
    ),
}


def _upgrade():
    return jsonify(_UPGRADE), 402


# ── NeMo governance summary + drift ─────────────────────────────────────────


@bp_nemoclaw.route('/api/nemoclaw/governance')
def api_nemoclaw_governance():
    return _upgrade()


@bp_nemoclaw.route('/api/nemoclaw/governance/acknowledge-drift', methods=['POST'])
def api_nemoclaw_acknowledge_drift():
    return _upgrade()


# ── NeMo status + policy ────────────────────────────────────────────────────


@bp_nemoclaw.route('/api/nemoclaw/status')
def api_nemoclaw_status():
    return _upgrade()


@bp_nemoclaw.route('/api/nemoclaw/policy')
def api_nemoclaw_policy():
    return _upgrade()


# ── Approval queue actions ──────────────────────────────────────────────────


@bp_nemoclaw.route('/api/nemoclaw/approve', methods=['POST'])
def api_nemoclaw_approve():
    return _upgrade()


@bp_nemoclaw.route('/api/nemoclaw/reject', methods=['POST'])
def api_nemoclaw_reject():
    return _upgrade()


@bp_nemoclaw.route('/api/nemoclaw/pending-approvals')
def api_nemoclaw_pending_approvals():
    return _upgrade()


# ── Guardrail events + metrics ──────────────────────────────────────────────


@bp_nemoclaw.route('/api/nemoclaw/events')
def api_nemoclaw_events():
    return _upgrade()


@bp_nemoclaw.route('/api/nemoclaw/metrics')
def api_nemoclaw_metrics():
    return _upgrade()


# ── Approval policy rule CRUD ───────────────────────────────────────────────


@bp_nemoclaw.route('/api/nemoclaw/rules', methods=['GET'])
def api_nemoclaw_rules_list():
    return _upgrade()


@bp_nemoclaw.route('/api/nemoclaw/rules', methods=['POST'])
def api_nemoclaw_rules_create():
    return _upgrade()


@bp_nemoclaw.route('/api/nemoclaw/rules/<path:rule_key>', methods=['DELETE'])
def api_nemoclaw_rules_delete(rule_key):
    return _upgrade()
