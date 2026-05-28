"""Per-event resolved-error triage (#2196 item #5)."""
from __future__ import annotations

import importlib
import time

import pytest


def _store(tmp_path, monkeypatch):
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "ev.duckdb"))
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_SECS", "0.05")
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_BATCH", "2")
    monkeypatch.delenv("CLAWMETRY_ROLE", raising=False)
    import clawmetry.local_store as ls
    importlib.reload(ls)
    monkeypatch.setattr(ls, "_daemon_registered", lambda: False)
    return ls, ls.get_store()


def _patch_daemon_proxy(monkeypatch, store):
    def fake(method, **kwargs):
        return getattr(store, method)(**kwargs)
    monkeypatch.setattr(
        "routes.local_query.local_store_via_daemon", fake, raising=False,
    )


def _client_with_route():
    from flask import Flask
    import routes.sessions as sessions_mod
    a = Flask(__name__)
    a.register_blueprint(sessions_mod.bp_sessions)
    return a.test_client()


# ── store layer ────────────────────────────────────────────────────────────

def test_mark_and_query_roundtrip(tmp_path, monkeypatch):
    _, store = _store(tmp_path, monkeypatch)
    try:
        assert store.mark_error_resolved("ev:abc", note="known flaky test") is True
        assert store.mark_error_resolved("ev:def") is True
        m = store.query_resolved_errors()
        assert "ev:abc" in m and "ev:def" in m
        assert m["ev:abc"]["note"] == "known flaky test"
        assert m["ev:def"]["note"] is None
        assert m["ev:abc"]["resolved_at"] > 0
    finally:
        store.stop(flush=True)


def test_mark_is_idempotent_and_refreshes_note(tmp_path, monkeypatch):
    _, store = _store(tmp_path, monkeypatch)
    try:
        store.mark_error_resolved("ev:1", note="first")
        first_ts = store.query_resolved_errors()["ev:1"]["resolved_at"]
        time.sleep(0.01)
        store.mark_error_resolved("ev:1", note="second")
        m = store.query_resolved_errors()
        assert m["ev:1"]["note"] == "second"
        assert m["ev:1"]["resolved_at"] >= first_ts  # refreshed (or equal-on-fast-clock)
    finally:
        store.stop(flush=True)


def test_unmark_removes_row(tmp_path, monkeypatch):
    _, store = _store(tmp_path, monkeypatch)
    try:
        store.mark_error_resolved("ev:x")
        assert "ev:x" in store.query_resolved_errors()
        assert store.unmark_error_resolved("ev:x") is True
        assert "ev:x" not in store.query_resolved_errors()
        # idempotent: removing a non-existent key returns False rather than raising
        assert store.unmark_error_resolved("ev:not-there") is False
    finally:
        store.stop(flush=True)


def test_bad_input_never_raises(tmp_path, monkeypatch):
    _, store = _store(tmp_path, monkeypatch)
    try:
        assert store.mark_error_resolved("") is False
        assert store.mark_error_resolved(None) is False  # type: ignore[arg-type]
        assert store.unmark_error_resolved("") is False
        assert store.unmark_error_resolved(None) is False  # type: ignore[arg-type]
        assert store.query_resolved_errors() == {}
    finally:
        store.stop(flush=True)


# ── route layer ─────────────────────────────────────────────────────────────


def test_routes_full_lifecycle(tmp_path, monkeypatch):
    _, store = _store(tmp_path, monkeypatch)
    try:
        _patch_daemon_proxy(monkeypatch, store)
        client = _client_with_route()

        # Empty to start
        body = client.get("/api/error-triage/resolved").get_json()
        assert body == {"resolved": {}, "count": 0}

        # POST resolves
        r = client.post(
            "/api/error-triage/resolve",
            json={"event_id": "ev:rt", "note": "flaky"},
        )
        assert r.status_code == 200, r.get_data(as_text=True)
        assert r.get_json()["ok"] is True

        # GET sees it
        listing = client.get("/api/error-triage/resolved").get_json()
        assert "ev:rt" in listing["resolved"]
        assert listing["resolved"]["ev:rt"]["note"] == "flaky"
        assert listing["count"] == 1

        # DELETE removes it
        r = client.delete("/api/error-triage/resolve?event_id=ev:rt")
        assert r.status_code == 200
        assert r.get_json() == {"ok": True, "removed": True, "event_id": "ev:rt"}

        # GET is empty again
        assert client.get("/api/error-triage/resolved").get_json()["count"] == 0

        # Bad input -> 400, never 500
        r = client.post("/api/error-triage/resolve", json={})
        assert r.status_code == 400
        r = client.delete("/api/error-triage/resolve")
        assert r.status_code == 400
    finally:
        store.stop(flush=True)


def test_snapshot_inclusion_via_build_resolved_errors(tmp_path, monkeypatch):
    """The snapshot's resolvedErrors slice mirrors query_resolved_errors —
    test the daemon-side builder directly."""
    ls, store = _store(tmp_path, monkeypatch)
    try:
        store.mark_error_resolved("ev:snap-1", note="snapshot test")
        from clawmetry import sync as syncmod
        out = syncmod._build_resolved_errors()
        assert isinstance(out, dict)
        assert "ev:snap-1" in out
        assert out["ev:snap-1"]["note"] == "snapshot test"
    finally:
        store.stop(flush=True)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
