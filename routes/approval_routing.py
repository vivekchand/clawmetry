"""routes/approval_routing.py: OSS stub after the impl moved to clawmetry-pro.

Approval DELIVERY — per-runtime routing, the channel senders, the inbound
decision poller and the signed ``/a/<id>`` decision page — ships in the
closed-source ``clawmetry-pro`` package as
``clawmetry_pro/routes/approval_routing.py`` plus
``clawmetry_pro/lib/approval_{notify,inbound,delivery}.py``. When that
package is installed its blueprint registers via the
``clawmetry.extensions`` entry point at app startup and wins these URLs.
When it is NOT installed this stub returns HTTP 402 ``upgrade_required``
at every URL the impl used to serve.

``dashboard.py`` decides which blueprint to register by inspecting
``clawmetry_pro.is_loaded()``, so the two never coexist on the URL map.

What is NOT here, deliberately: everything that PAUSES an agent stays open
source — the policy engine (``clawmetry/approvals.py``), the Claude Code
pre-tool gate and permission-prompt mirror installer
(``clawmetry/claude_code_gate.py``), both hook receivers
(``routes/hooks.py``) and the approval queue (``routes/policy.py``). They
reach the paid layer only through ``clawmetry/approval_events.py``, and
they all behave correctly when nothing answers: approvals still park and
still render in the Approvals tab, and the mirror simply never arms.

The decision-page URLs 402 rather than 404 on purpose. A user whose
license lapsed still has real notification links in their chat history;
"this needs a subscription" is a truthful answer to those, and "not found"
is not.
"""
from __future__ import annotations

import logging

from flask import Blueprint, jsonify

from clawmetry._paywall import upgrade_required_body

logger = logging.getLogger("clawmetry.routes.approval_routing")

bp_approval_routing = Blueprint("approval_routing", __name__)


_HINT = (
    "Sending approvals to Slack, Telegram, WhatsApp, email or a phone "
    "needs a ClawMetry plan. Approvals still appear in the Approvals tab "
    "on every install. See clawmetry.com/pricing."
)

_HINT_MIRROR = (
    "Answering a runtime's own permission prompts from your phone is a "
    "ClawMetry Pro feature. See clawmetry.com/pricing."
)


def _upgrade(feature: str = "approval_queue", hint: str = _HINT):
    return jsonify(upgrade_required_body(feature, hint=hint)), 402


@bp_approval_routing.route("/api/approvals/routing", methods=["GET"])
def _routing_get_stub():
    return _upgrade()


@bp_approval_routing.route("/api/approvals/routing", methods=["PUT"])
def _routing_put_stub():
    return _upgrade()


@bp_approval_routing.route("/api/approvals/routing/test", methods=["POST"])
def _routing_test_stub():
    return _upgrade()


@bp_approval_routing.route("/a/<approval_id>", methods=["GET"])
def _decision_page_stub(approval_id: str):
    return _upgrade()


@bp_approval_routing.route("/a/<approval_id>/decide", methods=["POST"])
def _decision_decide_stub(approval_id: str):
    return _upgrade()
