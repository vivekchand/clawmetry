"""Guard the open-core boundary for approval delivery.

Paid implementations live in the private ``clawmetry-pro`` package; this
repo keeps the catalogue, the gate mechanism, and the 402 stubs. That rule
has no teeth without a test — the approval-delivery feature was written
straight into this repo in 0.12.713 and nothing objected, which is how it
came to need a four-PR migration back out.

These tests fail loudly if the impl returns, or if the stub drifts away
from the URLs the paid blueprint serves.

Deliberately NOT asserted here: that ``clawmetry/approvals.py``,
``claude_code_gate.py``, ``routes/hooks.py`` and ``routes/policy.py`` are
absent. They are open source ON PURPOSE — everything that pauses an agent
stays public, including for paid runtimes. Only DELIVERY moved.
"""
from __future__ import annotations

import os
import re
import sys

import pytest
from flask import Flask

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)


#: Modules that moved to clawmetry-pro and must not come back.
_MOVED = ("approval_notify", "approval_inbound", "approval_delivery")

#: OSS modules that talk to the delivery layer. They may import the SEAM
#: (clawmetry.approval_events) and nothing else from the paid side.
_SEAM_CONSUMERS = (
    "clawmetry/approvals.py",
    "clawmetry/claude_code_gate.py",
    "clawmetry/sync.py",
    "routes/hooks.py",
    "routes/policy.py",
    "routes/approval_routing.py",
)


def test_moved_modules_are_gone():
    for name in _MOVED:
        for path in (f"clawmetry/{name}.py", f"routes/{name}.py"):
            assert not os.path.exists(os.path.join(_REPO_ROOT, path)), (
                f"{path} is a paid implementation and belongs in "
                f"clawmetry-pro, not this repo"
            )


def test_no_oss_module_imports_the_delivery_impl():
    """The whole point of the seam: OSS never names a module that may not
    be installed."""
    offenders = []
    for rel in _SEAM_CONSUMERS:
        src = open(os.path.join(_REPO_ROOT, rel)).read()
        for name in _MOVED:
            if re.search(rf"\bimport\s+{name}\b", src) or \
               re.search(rf"\bfrom\s+\S*{name}\s+import\b", src):
                offenders.append(f"{rel} → {name}")
    assert not offenders, (
        "these modules import the paid delivery impl directly; talk to "
        "clawmetry.approval_events instead: " + ", ".join(offenders)
    )


def test_no_oss_module_imports_clawmetry_pro():
    """OSS may ASK whether pro is loaded (dashboard.py's blueprint switch
    does), but must never import its internals."""
    offenders = []
    for rel in _SEAM_CONSUMERS + ("clawmetry/approval_events.py",):
        src = open(os.path.join(_REPO_ROOT, rel)).read()
        if re.search(r"from\s+clawmetry_pro[.\s]", src):
            offenders.append(rel)
    assert not offenders, offenders


def test_stub_serves_every_url_the_paid_blueprint_owns():
    """If the paid side adds a route and the stub does not, an unlicensed
    node 404s where it should 402 — and the frontend's paywall handling,
    which keys on 402, silently stops working."""
    from routes.approval_routing import bp_approval_routing
    app = Flask(__name__)
    app.register_blueprint(bp_approval_routing)
    rules = {str(r.rule) for r in app.url_map.iter_rules()
             if not str(r.rule).startswith("/static")}
    assert rules == {
        "/api/approvals/routing",
        "/api/approvals/routing/test",
        "/a/<approval_id>",
        "/a/<approval_id>/decide",
    }, rules


@pytest.mark.parametrize("method,url", [
    ("get",  "/api/approvals/routing"),
    ("put",  "/api/approvals/routing"),
    ("post", "/api/approvals/routing/test"),
    ("get",  "/a/abc123"),
    ("post", "/a/abc123/decide"),
])
def test_stub_returns_402_with_the_documented_body(method, url):
    from routes.approval_routing import bp_approval_routing
    app = Flask(__name__)
    app.register_blueprint(bp_approval_routing)
    client = app.test_client()

    r = getattr(client, method)(url)
    assert r.status_code == 402
    body = r.get_json()
    assert body["error"] == "upgrade_required"
    assert body["feature"] == "approval_queue"
    assert body["hint"]


def test_entitlement_keys_exist_and_land_on_a_real_tier():
    """A gate naming a key that is in no tier set silently allows
    everything in grace mode and denies everything in enforce mode."""
    from clawmetry import entitlements as ent
    for key in ("approval_queue", "approval_mirror"):
        assert key in ent.FEATURE_LABELS, f"{key} missing from the catalogue"
        assert key in ent.PAID_FEATURES, f"{key} is in no paid tier"
    # The split: Starter is TOLD an approval is waiting (delivery rides on
    # approval_queue — a queue that cannot tell you is not the promised
    # feature); answering it hands-free from a phone is the Pro upsell.
    assert "approval_queue" in ent.STARTER_FEATURES
    assert "approval_mirror" in ent.PRO_ONLY_FEATURES
    # STARTER_FEATURES is locked to the /pricing card's exact keys
    # elsewhere; a new Starter key is a public pricing change, not a
    # code change. Do not add one here to route around that lock.
