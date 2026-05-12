"""Tests for the approvals-queue local-store fast paths + cache_push +
decision-relay handler (epic #1032 Phase 4).

Mirrors the pattern used by ``test_crons_local_store.py`` and
``test_brain_cache_push.py``:

  * Schema + ingest/query/update helpers live on ``LocalStore``.
  * ``CLAWMETRY_LOCAL_STORE_READ=1`` + populated ``approvals`` table →
    ``/api/nemoclaw/pending-approvals`` serves from DuckDB and tags
    ``_source: local_store``. Flag unset → fast path skipped, legacy
    ``openshell draft get`` CLI path runs (here: returns the
    ``{installed: False, approvals: []}`` no-binary response).
  * ``_build_approvals_cache_pushes`` emits one heartbeat ``cache_pushes``
    entry per token, keyed by ``approvals:{owner_hash}:queue`` with the
    encrypted pending-queue payload.
  * ``_dispatch_pending_queries`` recognises ``{type: "approval_decision",
    id, decision, resolver, reason}`` entries and flips the local DuckDB
    row through ``update_approval_decision``.
"""

from __future__ import annotations

import importlib
import os
import sys

import pytest
from flask import Flask


_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)


# ── fixtures ───────────────────────────────────────────────────────────────


def _build_app(tmp_path, monkeypatch, *, enable_fast_path: bool):
    """Build an isolated Flask app with bp_nemoclaw + a tmp DuckDB.

    Reload order matters: ``local_store`` first (so its module-level path
    constants pick up the env var), then ``routes.nemoclaw`` so its lazy
    imports resolve against the freshly-loaded store.
    """
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "events.duckdb"))
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_SECS", "0.05")
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_BATCH", "5")
    if enable_fast_path:
        monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_READ", "1")
    else:
        monkeypatch.delenv("CLAWMETRY_LOCAL_STORE_READ", raising=False)

    import clawmetry.local_store as ls
    importlib.reload(ls)
    import routes.nemoclaw as nm
    importlib.reload(nm)

    app = Flask(__name__)
    app.register_blueprint(nm.bp_nemoclaw)
    return app, ls, nm


@pytest.fixture
def fast_path_app(tmp_path, monkeypatch):
    app, ls, nm = _build_app(tmp_path, monkeypatch, enable_fast_path=True)
    yield app, ls, nm
    try:
        ls.get_store().stop(flush=True)
    except Exception:
        pass


@pytest.fixture
def no_flag_app(tmp_path, monkeypatch):
    """Same shape as fast_path_app but with CLAWMETRY_LOCAL_STORE_READ unset.
    Used by the negative test that asserts the env gate is honoured."""
    app, ls, nm = _build_app(tmp_path, monkeypatch, enable_fast_path=False)
    yield app, ls, nm
    try:
        ls.get_store().stop(flush=True)
    except Exception:
        pass


def _seed_two_pending(store, owner_hash="oh-test"):
    """Insert two pending approvals typical of a policy-watcher fire."""
    store.ingest_approval({
        "id":                   "app-1",
        "owner_hash":           owner_hash,
        "requestor_session_id": "sess-A",
        "action":               "bash",
        "args":                 {"cmd": "rm -rf /tmp/x"},
        "status":               "pending",
        "created_at":           "2026-05-12T10:00:00+00:00",
    })
    store.ingest_approval({
        "id":                   "app-2",
        "owner_hash":           owner_hash,
        "requestor_session_id": "sess-B",
        "action":               "write_file",
        "args":                 {"path": "/etc/passwd", "content": "..."},
        "status":               "pending",
        "created_at":           "2026-05-12T10:01:00+00:00",
    })


# ── 1. schema + helpers: seed → query → assert ─────────────────────────────


def test_query_approvals_returns_seeded_rows(fast_path_app):
    """ingest_approval rows show up in query_approvals, owner_hash + status
    filters work, args BLOB round-trips back to a dict."""
    _app, ls, _nm = fast_path_app
    store = ls.get_store()
    _seed_two_pending(store)

    rows = store.query_approvals(owner_hash="oh-test")
    assert len(rows) == 2
    by_id = {r["id"]: r for r in rows}
    assert set(by_id) == {"app-1", "app-2"}
    assert by_id["app-1"]["action"] == "bash"
    # args BLOB → dict round-trip.
    assert by_id["app-1"]["args"] == {"cmd": "rm -rf /tmp/x"}
    # Status filter narrows the result.
    pending_only = store.query_approvals(owner_hash="oh-test", status="pending")
    assert len(pending_only) == 2
    decided_only = store.query_approvals(owner_hash="oh-test", status="approved")
    assert decided_only == []
    # Wrong owner_hash → empty result (multi-tenant isolation).
    other = store.query_approvals(owner_hash="oh-other")
    assert other == []


# ── 2. route fast-path: flag on + rows present → _source=local_store ───────


def test_pending_approvals_fast_path_serves_from_duckdb(fast_path_app):
    _app, ls, _nm = fast_path_app
    _seed_two_pending(ls.get_store())

    body = _app.test_client().get("/api/nemoclaw/pending-approvals").get_json()
    assert body.get("_source") == "local_store"
    assert body.get("installed") is True
    approvals = body.get("approvals") or []
    assert len(approvals) == 2

    by_id = {a["id"]: a for a in approvals}
    assert set(by_id) == {"app-1", "app-2"}
    # Legacy fields the dashboard JS reads — present + populated.
    assert by_id["app-1"]["status"] == "pending"
    assert by_id["app-1"]["action"] == "bash"
    assert by_id["app-1"]["chunk_id"] == "app-1"
    assert by_id["app-1"]["session_id"] == "sess-A"
    assert by_id["app-1"]["args"] == {"cmd": "rm -rf /tmp/x"}


# ── 3. route fast-path: flag off → fast path skipped ───────────────────────


def test_pending_approvals_flag_off_skips_fast_path(no_flag_app):
    """CLAWMETRY_LOCAL_STORE_READ unset: even with DuckDB rows present, the
    fast path is skipped and the legacy openshell CLI path runs. On a system
    without `openshell` on PATH the legacy path returns
    ``{installed: False, approvals: []}`` — and crucially, NO ``_source``."""
    _app, ls, _nm = no_flag_app
    _seed_two_pending(ls.get_store())

    body = _app.test_client().get("/api/nemoclaw/pending-approvals").get_json()
    assert body.get("_source") != "local_store"
    # The legacy path may return installed=False (no openshell binary in CI)
    # or installed=True with an empty list (binary present but no sandbox).
    # Either way the response must NOT carry the fast-path tag.


# ── 4. route fast-path: empty store → fast path returns None → legacy ──────


def test_pending_approvals_empty_store_falls_through(fast_path_app):
    """Flag on but no rows in DuckDB: ``_try_local_store_approvals`` returns
    None and the legacy CLI path runs (and degrades to installed=False on a
    bare CI image)."""
    _app, _ls, _nm = fast_path_app
    body = _app.test_client().get("/api/nemoclaw/pending-approvals").get_json()
    assert body.get("_source") != "local_store"


# ── 5. update_approval_decision flips status idempotently ──────────────────


def test_update_approval_decision_flips_status(fast_path_app):
    _app, ls, _nm = fast_path_app
    store = ls.get_store()
    _seed_two_pending(store)

    n = store.update_approval_decision("app-1", "approve", "user@x", "lgtm")
    assert n == 1

    rows = store.query_approvals(owner_hash="oh-test")
    by_id = {r["id"]: r for r in rows}
    assert by_id["app-1"]["status"] == "approved"
    assert by_id["app-1"]["decision"] == "approve"
    assert by_id["app-1"]["resolver"] == "user@x"
    assert by_id["app-1"]["decision_reason"] == "lgtm"
    # resolved_at gets stamped with an ISO timestamp.
    assert by_id["app-1"]["resolved_at"]

    # Idempotent: a second call on the same id returns 0 (already decided).
    again = store.update_approval_decision("app-1", "approve", "user@x", "lgtm")
    assert again == 0

    # Unknown id: 0, not an exception.
    missing = store.update_approval_decision("nope", "approve", "user@x")
    assert missing == 0


# ── 6. _build_approvals_cache_pushes round-trip ────────────────────────────


def test_build_approvals_cache_pushes_round_trip(fast_path_app):
    """Pending rows seeded under owner_hash X → cache_push emits one entry
    keyed by ``approvals:{owner_hash}:queue`` with a ttl_s of 60 (acceptance:
    cloud inbox within 2s, so short TTL keeps it fresh)."""
    _app, ls, _nm = fast_path_app
    import clawmetry.sync as s
    importlib.reload(s)

    api_key = "cm_test_token_approvals"
    expected_owner = s._owner_hash_for_token(api_key)
    _seed_two_pending(ls.get_store(), owner_hash=expected_owner)

    config = {
        "node_id":        "node-test",
        "api_key":        api_key,
        "encryption_key": s.generate_encryption_key(),
    }

    pushes = s._build_approvals_cache_pushes(config)
    assert isinstance(pushes, list)
    assert len(pushes) == 1
    entry = pushes[0]
    assert entry["key"] == f"approvals:{expected_owner}:queue"
    assert entry["ttl_s"] == s.APPROVALS_CACHE_TTL_SEC == 60
    blob = entry["blob"]
    assert isinstance(blob, str) and len(blob) > 0
    # Plaintext markers must not appear in the encrypted blob.
    assert "rm -rf" not in blob
    assert "sess-A" not in blob

    # Decrypt round-trip: blob → dict with approvals_queue shape.
    decoded = s.decrypt_payload(blob, config["encryption_key"])
    assert decoded["_shape"] == "approvals_queue"
    assert decoded["_source"] == "local_store"
    assert decoded["count"] == 2
    ids = {a["id"] for a in decoded["approvals"]}
    assert ids == {"app-1", "app-2"}


# ── 7. cache_push degenerate paths: empty store / no key ───────────────────


def test_build_approvals_cache_pushes_empty_store_returns_empty(fast_path_app):
    """No pending approvals → no push (empty inbox renders empty in cloud)."""
    _app, _ls, _nm = fast_path_app
    import clawmetry.sync as s
    importlib.reload(s)
    config = {
        "node_id":        "node-empty",
        "api_key":        "cm_test_token_empty",
        "encryption_key": s.generate_encryption_key(),
    }
    pushes = s._build_approvals_cache_pushes(config)
    assert pushes == []


def test_build_approvals_cache_pushes_no_encryption_key_no_push(fast_path_app):
    """No encryption key → never push (we'd leak plaintext otherwise)."""
    _app, ls, _nm = fast_path_app
    import clawmetry.sync as s
    importlib.reload(s)
    api_key = "cm_test_token_nokey"
    _seed_two_pending(ls.get_store(), owner_hash=s._owner_hash_for_token(api_key))
    config = {
        "node_id":        "node-nokey",
        "api_key":        api_key,
        "encryption_key": None,
    }
    assert s._build_approvals_cache_pushes(config) == []


# ── 8. _dispatch_pending_queries: approval_decision flips local row ─────────


def test_dispatch_pending_queries_applies_approval_decision(fast_path_app):
    """A ``{type: "approval_decision", id, decision, resolver, reason}`` entry
    in the heartbeat response's pending_queries array must flip the matching
    local DuckDB row through ``update_approval_decision`` — and crucially,
    NOT trigger the read-query dispatch path (no /ingest/cache POST)."""
    _app, ls, _nm = fast_path_app
    import clawmetry.sync as s
    importlib.reload(s)
    api_key = "cm_test_token_relay"
    owner_hash = s._owner_hash_for_token(api_key)
    _seed_two_pending(ls.get_store(), owner_hash=owner_hash)

    config = {
        "node_id":        "node-relay",
        "api_key":        api_key,
        "encryption_key": s.generate_encryption_key(),
    }

    # Sanity: _post would fail if the dispatch wrongly tried to POST a result
    # back. Fake it to detect that contamination.
    cache_post_calls: list[str] = []

    def fake_post(path, payload, api_key_arg, timeout=45):
        cache_post_calls.append(path)
        return None

    import clawmetry.sync as sync_mod
    orig_post = sync_mod._post
    sync_mod._post = fake_post
    try:
        sync_mod._dispatch_pending_queries(config, [
            {
                "type":     "approval_decision",
                "id":       "app-1",
                "decision": "approve",
                "resolver": "user@cloud",
                "reason":   "approved in dashboard",
            },
        ])
    finally:
        sync_mod._post = orig_post

    # Read path was NOT invoked.
    assert cache_post_calls == []

    rows = ls.get_store().query_approvals(owner_hash=owner_hash)
    by_id = {r["id"]: r for r in rows}
    assert by_id["app-1"]["status"] == "approved"
    assert by_id["app-1"]["decision"] == "approve"
    assert by_id["app-1"]["resolver"] == "user@cloud"
    assert by_id["app-1"]["decision_reason"] == "approved in dashboard"
    # The other row is untouched.
    assert by_id["app-2"]["status"] == "pending"


def test_dispatch_pending_queries_approval_decision_missing_id_is_noop(fast_path_app):
    """A malformed approval_decision entry (no id) must NOT crash dispatch
    and must NOT touch the store."""
    _app, ls, _nm = fast_path_app
    import clawmetry.sync as s
    importlib.reload(s)
    api_key = "cm_test_token_bad"
    owner_hash = s._owner_hash_for_token(api_key)
    _seed_two_pending(ls.get_store(), owner_hash=owner_hash)

    config = {
        "node_id":        "node-bad",
        "api_key":        api_key,
        "encryption_key": s.generate_encryption_key(),
    }
    # Missing id, missing decision — both ignored gracefully.
    s._dispatch_pending_queries(config, [
        {"type": "approval_decision", "decision": "approve"},
        {"type": "approval_decision", "id": "app-1"},
    ])
    rows = ls.get_store().query_approvals(owner_hash=owner_hash)
    # Neither row was touched.
    for r in rows:
        assert r["status"] == "pending"
