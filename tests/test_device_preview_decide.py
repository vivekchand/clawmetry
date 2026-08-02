"""Tests for the device-preview write path (routes/device.py → routes/policy.py).

The /device-preview page is the software stand-in for the physical desk
device: when an approval is pending it renders Approve / Deny buttons — the
same buttons the hardware ships with. Those buttons MUST write through the
real decision endpoint, ``POST /api/approvals/<id>/decide`` with a JSON
``{"decision": "approve"|"deny"}`` body (routes/policy.py). An earlier
draft POSTed to ``/api/approvals/<id>/approve`` / ``.../deny`` — routes
that do not exist — making the buttons silent no-ops.

These tests pin:
  1. The page's JS targets the real ``/decide`` route with a JSON decision
     body (and the phantom ``'/'+decision`` URL never comes back).
  2. Driving that exact request against an app serving both blueprints
     flips a pending approval row: approve → approved, deny → denied.

Fixture shape mirrors tests/test_device_snapshot.py (hermetic tmp DuckDB,
daemon discovery stubbed out) + tests/test_approvals_local_blocking.py
(entitlement pinned so @gate("approval_queue") passes regardless of the
dev machine's license / CLAWMETRY_ENFORCE).
"""

from __future__ import annotations

import importlib
import re
import sys

import pytest
from flask import Flask


@pytest.fixture
def preview_app(tmp_path, monkeypatch):
    """Flask app serving BOTH bp_device (the page) and bp_policy (the decide
    endpoint) over a hermetic tmp DuckDB store."""
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "events.duckdb"))
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_SECS", "0.05")
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_BATCH", "1")
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_READ", "1")

    sys.modules.pop("clawmetry.local_store", None)
    import clawmetry.local_store as ls
    importlib.reload(ls)
    # Own the writer so the tmp store opens here, not via a dev daemon.
    ls.mark_writer_owner()

    # Stub daemon discovery so both read and write paths fall through to the
    # in-process store (same as the device snapshot fixture).
    import routes.local_query as lq
    monkeypatch.setattr(lq, "_read_discovery", lambda: None)
    monkeypatch.setattr(lq, "_cached_discovery", lambda: None)

    # Pin entitlement so @gate("approval_queue") on the decide route passes.
    import clawmetry.entitlements as ent
    e = ent.Entitlement(
        tier="pro", source="test", grace=False,
        features=frozenset({"approval_queue"}), runtimes=frozenset(),
    )
    monkeypatch.setattr(ent, "get_entitlement", lambda force=False: e)

    sys.modules.pop("routes.policy", None)
    import routes.policy as pol
    importlib.reload(pol)
    import routes.device as dev
    importlib.reload(dev)
    dev._snapshot_cache["payload"] = None
    dev._snapshot_cache["ts"] = 0.0

    a = Flask(__name__)
    a.register_blueprint(dev.bp_device)
    a.register_blueprint(pol.bp_policy)
    yield a, ls
    try:
        ls.get_store().stop(flush=True)
    except Exception:
        pass


def _seed_pending(store, aid):
    store.ingest_approval({
        "id":                   aid,
        "owner_hash":           "oh-device",
        "requestor_session_id": "claude_code:sess-device",
        "action":               "Bash: rm -rf /tmp/x",
        "args":                 {"command": "rm -rf /tmp/x"},
        "status":               "pending",
        "created_at":           "2026-08-01T10:00:00Z",
    })
    return aid


def test_preview_page_targets_real_decide_endpoint(preview_app):
    """The page's JS must POST to /api/approvals/<id>/decide with a JSON
    {"decision": ...} body — and the phantom per-verb routes must be gone."""
    a, _ls = preview_app
    r = a.test_client().get("/device-preview")
    assert r.status_code == 200
    html = r.get_data(as_text=True)

    # The real route, with the decision in the JSON body.
    assert re.search(r"/api/approvals/'\s*\+[^+]+\+\s*'/decide'", html), (
        "device page must POST to /api/approvals/<id>/decide"
    )
    assert re.search(r"JSON\.stringify\(\{decision", html), (
        "decision must travel in the JSON body, not the URL"
    )
    # The old broken shape: decision appended to the URL as the verb.
    assert "+'/'+decision" not in html.replace(" ", ""), (
        "phantom /api/approvals/<id>/<decision> route must not come back"
    )
    # And the phantom routes really don't exist on the served app.
    for verb in ("approve", "deny"):
        resp = a.test_client().post(f"/api/approvals/some-id/{verb}")
        assert resp.status_code == 404


def test_device_page_approve_flips_row_to_approved(preview_app):
    """The exact request the page's Approve button sends flips the pending
    row to approved (resolver 'local')."""
    a, ls = preview_app
    aid = _seed_pending(ls.get_store(), "device-approve-1")

    resp = a.test_client().post(
        f"/api/approvals/{aid}/decide",
        json={"decision": "approve", "reason": "device button"},
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["ok"] is True
    assert body["status"] == "approved"

    row = next(r for r in ls.get_store().query_approvals(limit=10)
               if r["id"] == aid)
    assert row["status"] == "approved"
    assert row["decision"] == "approve"
    assert row["resolver"] == "local"


def test_device_page_deny_flips_row_to_denied(preview_app):
    """The exact request the page's Deny button sends flips the pending row
    to denied."""
    a, ls = preview_app
    aid = _seed_pending(ls.get_store(), "device-deny-1")

    resp = a.test_client().post(
        f"/api/approvals/{aid}/decide",
        json={"decision": "deny", "reason": "device button"},
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["ok"] is True
    assert body["status"] == "denied"

    row = next(r for r in ls.get_store().query_approvals(limit=10)
               if r["id"] == aid)
    assert row["status"] == "denied"
    assert row["decision"] == "deny"
