"""routes/compliance.py: OSS stub after the impl lives in clawmetry-pro.

The real Compliance Pack (control-map engine + auditor-ready evidence
bundles, NIST AI RMF / SOC 2) ships in the closed-source ``clawmetry-pro``
package as ``clawmetry_pro/routes/compliance.py``. When that package is
installed its blueprint registers via ``clawmetry_pro.register_all()`` at
app startup and wins the URL routes.

When clawmetry-pro is NOT installed (vanilla OSS), this stub registers in
its place and returns HTTP 402 ``upgrade_required`` on every compliance
endpoint. Mirrors the precedent set by ``routes/nemoclaw.py`` and the other
OSS 402-stubs. Blueprint name + URL rules match the real impl exactly so
the swap is transparent.
"""
from __future__ import annotations

from flask import Blueprint, jsonify

from clawmetry._paywall import upgrade_required_body

bp_compliance = Blueprint("compliance", __name__)


def _upgrade():
    return jsonify(upgrade_required_body("compliance_pack")), 402


@bp_compliance.route('/api/compliance/frameworks')
def api_compliance_frameworks():
    return _upgrade()


@bp_compliance.route('/api/compliance/controls')
def api_compliance_controls():
    return _upgrade()


@bp_compliance.route('/api/compliance/bundle', methods=['POST'])
def api_compliance_bundle():
    return _upgrade()
