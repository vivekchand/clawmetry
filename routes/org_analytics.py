"""routes/org_analytics.py: OSS stub after the impl lives in clawmetry-pro.

Org-wide Claude coverage answers the one question local ingest structurally
cannot: what is this org running on Claude surfaces that never touch this
disk — claude.ai chat, Cowork's cloud workspaces, Claude in Chrome? The real
implementation reads Anthropic's Enterprise Analytics API and ships in the
closed-source ``clawmetry-pro`` package as
``clawmetry_pro/routes/org_analytics.py``. When that package is installed its
blueprint registers via ``clawmetry_pro.register_all()`` at app startup and
wins the URL routes.

When clawmetry-pro is NOT installed (vanilla OSS), this stub registers in its
place and returns HTTP 402 ``upgrade_required`` on every endpoint. Mirrors the
precedent set by ``routes/compliance.py`` and the other OSS 402-stubs;
blueprint name + URL rules match the real impl exactly so the swap is
transparent.
"""
from __future__ import annotations

from flask import Blueprint, jsonify

from clawmetry._paywall import upgrade_required_body

bp_org_analytics = Blueprint("org_analytics", __name__)

_HINT = (
    "Org-wide Claude coverage rolls up the Claude surfaces that never reach "
    "this machine. Needs an Enterprise analytics token."
)


def _upgrade():
    return jsonify(upgrade_required_body("org_analytics", hint=_HINT)), 402


@bp_org_analytics.route('/api/org-analytics')
def api_org_analytics():
    return _upgrade()


@bp_org_analytics.route('/api/org-analytics/key')
def api_org_analytics_key():
    return _upgrade()


@bp_org_analytics.route('/api/org-analytics/key', methods=['POST'])
def api_org_analytics_save_key():
    return _upgrade()
