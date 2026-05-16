"""E2E tests for the LoopDetector → DuckDB → /api/loop-signals path (#1364).

Three surfaces:
  1. Schema round-trip — ``LocalStore.ingest_loop_signal`` writes a row
     and ``query_recent_loop_signals`` reads it back, ordered newest-first
     and respecting ``limit`` + ``since_minutes``.
  2. Upsert semantics — re-ingesting the same ``(session_id, signature)``
     bumps ``repeat_count`` (kept = max of incoming vs existing) and
     refreshes ``last_seen``, instead of duplicating the row.
  3. Route fast path — ``GET /api/loop-signals`` returns the DuckDB rows
     in ``signals`` with the same shape, gracefully degrading to ``[]``
     when nothing is detected.

Driver matches the pattern in ``test_alert_rules_local_store.py`` —
reload ``clawmetry.local_store`` against a tmp DuckDB, exercise the
public surface, then reload the route module so its late ``_ls_call``
points at the fresh store.
"""
from __future__ import annotations

import importlib
import os
import sys
import time

import pytest


_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)


# ── Fixtures ───────────────────────────────────────────────────────────────


@pytest.fixture
def fresh_store(tmp_path, monkeypatch):
    """Reload ``clawmetry.local_store`` against a fresh DuckDB file."""
    monkeypatch.setenv(
        "CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "loops.duckdb")
    )
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_SECS", "0.05")
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_BATCH", "1")

    sys.modules.pop("clawmetry.local_store", None)
    import clawmetry.local_store as ls
    importlib.reload(ls)

    store = ls.get_store()
    yield ls, store

    try:
        store.stop(flush=False)
    except Exception:
        pass


# ── 1. Schema round-trip ───────────────────────────────────────────────────


def test_ingest_and_query_loop_signal_round_trip(fresh_store):
    ls, store = fresh_store
    store.ingest_loop_signal(
        session_id="sess-001",
        signature="abc123def456",
        repeat_count=5,
        first_seen="2026-05-15T10:00:00",
        last_seen="2026-05-15T10:05:00",
        severity="warning",
        details={"window_seconds": 300, "model": "claude-sonnet-4"},
    )
    rows = store.query_recent_loop_signals(limit=10, since_minutes=0)
    assert len(rows) == 1
    r = rows[0]
    assert r["session_id"] == "sess-001"
    assert r["signature"] == "abc123def456"
    assert r["repeat_count"] == 5
    assert r["severity"] == "warning"
    assert r["agent_type"] == "openclaw"
    assert r["first_seen"].startswith("2026-05-15T10:00:00")
    assert r["last_seen"].startswith("2026-05-15T10:05:00")
    # details BLOB is decoded back to a dict by the read path.
    assert isinstance(r["details"], dict)
    assert r["details"]["window_seconds"] == 300
    assert r["details"]["model"] == "claude-sonnet-4"


def test_query_recent_loop_signals_orders_newest_first(fresh_store):
    ls, store = fresh_store
    store.ingest_loop_signal(
        session_id="s-a", signature="sig-a", repeat_count=3,
        first_seen="2026-05-15T09:00:00", last_seen="2026-05-15T09:00:00",
    )
    store.ingest_loop_signal(
        session_id="s-b", signature="sig-b", repeat_count=4,
        first_seen="2026-05-15T11:00:00", last_seen="2026-05-15T11:00:00",
    )
    store.ingest_loop_signal(
        session_id="s-c", signature="sig-c", repeat_count=5,
        first_seen="2026-05-15T10:00:00", last_seen="2026-05-15T10:00:00",
    )
    rows = store.query_recent_loop_signals(limit=10, since_minutes=0)
    assert [r["session_id"] for r in rows] == ["s-b", "s-c", "s-a"]
    # Repeat counts come back unchanged (no double-counting on insert).
    assert [r["repeat_count"] for r in rows] == [4, 5, 3]


def test_query_recent_loop_signals_respects_limit(fresh_store):
    ls, store = fresh_store
    for i in range(5):
        store.ingest_loop_signal(
            session_id=f"s-{i}", signature=f"sig-{i}", repeat_count=i + 2,
            first_seen=f"2026-05-15T10:0{i}:00",
            last_seen=f"2026-05-15T10:0{i}:00",
        )
    assert len(store.query_recent_loop_signals(limit=3, since_minutes=0)) == 3
    assert len(store.query_recent_loop_signals(limit=10, since_minutes=0)) == 5


def test_query_recent_loop_signals_window_filters_old_rows(fresh_store):
    """``since_minutes>0`` should hide rows whose ``last_seen`` is older
    than the window. Use an explicit very-old timestamp so the window
    arithmetic has unambiguous behaviour regardless of test wallclock."""
    ls, store = fresh_store
    store.ingest_loop_signal(
        session_id="recent", signature="sig-recent", repeat_count=3,
        # Now-ish — DuckDB ``now() - 60min`` will keep this row.
    )
    store.ingest_loop_signal(
        session_id="ancient", signature="sig-ancient", repeat_count=99,
        first_seen="2020-01-01T00:00:00",
        last_seen="2020-01-01T00:00:00",
    )
    in_window = store.query_recent_loop_signals(limit=10, since_minutes=60)
    sids = {r["session_id"] for r in in_window}
    assert "recent" in sids
    assert "ancient" not in sids
    # Disabling the window with since_minutes<=0 returns both.
    all_rows = store.query_recent_loop_signals(limit=10, since_minutes=0)
    assert {r["session_id"] for r in all_rows} == {"recent", "ancient"}


# ── 2. Upsert semantics ────────────────────────────────────────────────────


def test_ingest_loop_signal_upserts_increments_repeat(fresh_store):
    ls, store = fresh_store
    store.ingest_loop_signal(
        session_id="s-up", signature="sig-up", repeat_count=3,
        first_seen="2026-05-15T10:00:00", last_seen="2026-05-15T10:00:00",
    )
    # Detector fires again moments later with a higher running count —
    # the row is upserted, not duplicated.
    store.ingest_loop_signal(
        session_id="s-up", signature="sig-up", repeat_count=7,
        first_seen="2026-05-15T10:01:00", last_seen="2026-05-15T10:02:30",
    )
    rows = store.query_recent_loop_signals(limit=10, since_minutes=0)
    assert len(rows) == 1
    r = rows[0]
    # GREATEST(existing, incoming) => 7 wins.
    assert r["repeat_count"] == 7
    # last_seen advances, first_seen stays at the earlier timestamp.
    assert r["last_seen"].startswith("2026-05-15T10:02:30")
    assert r["first_seen"].startswith("2026-05-15T10:00:00")


def test_ingest_loop_signal_invalid_inputs_are_dropped(fresh_store):
    """Bad input never raises — the proxy is on the request hot path."""
    ls, store = fresh_store
    # Missing fields → silently dropped.
    store.ingest_loop_signal(session_id="", signature="x", repeat_count=3)
    store.ingest_loop_signal(session_id="s", signature="", repeat_count=3)
    # Zero / negative count → dropped.
    store.ingest_loop_signal(session_id="s", signature="x", repeat_count=0)
    store.ingest_loop_signal(session_id="s", signature="x", repeat_count=-2)
    # Non-numeric count → dropped.
    store.ingest_loop_signal(session_id="s", signature="x", repeat_count="abc")  # type: ignore[arg-type]
    assert store.query_recent_loop_signals(limit=10, since_minutes=0) == []


# ── 3. Route fast path ─────────────────────────────────────────────────────


def test_api_loop_signals_returns_rows_from_local_store(fresh_store, monkeypatch):
    """``GET /api/loop-signals`` reads the DuckDB rows and returns them
    in ``signals`` with the right shape and ordering.

    Force the Pro path so the OSS row-cap (#1376) doesn't truncate the
    seeded fixture; the cap behaviour has its own dedicated test below.
    """
    ls, store = fresh_store
    store.ingest_loop_signal(
        session_id="ss-1", signature="abcd1234efgh", repeat_count=8,
        first_seen="2026-05-15T10:00:00", last_seen="2026-05-15T10:05:00",
        severity="warning",
        details={"model": "claude-sonnet-4"},
    )
    store.ingest_loop_signal(
        session_id="ss-2", signature="zzzz9999yyyy", repeat_count=4,
        first_seen="2026-05-15T11:00:00", last_seen="2026-05-15T11:01:00",
    )

    # Reload routes.health so its module-level _ls_call sees the fresh store.
    sys.modules.pop("routes.health", None)
    import routes.health as rh
    importlib.reload(rh)

    # Default this round-trip test to a Pro user so the OSS cap added in
    # #1376 doesn't drop the second seeded row.
    import dashboard as _d
    monkeypatch.setattr(_d, "_is_pro_user", lambda: True)

    from flask import Flask
    app = Flask(__name__)
    app.register_blueprint(rh.bp_health)
    client = app.test_client()

    resp = client.get("/api/loop-signals?limit=20&since_minutes=0")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["count"] == 2
    assert body["total_count"] == 2
    assert body["capped_pro_gated"] is False
    sigs = body["signals"]
    assert len(sigs) == 2
    # Newest last_seen first.
    assert sigs[0]["session_id"] == "ss-2"
    assert sigs[1]["session_id"] == "ss-1"
    # Round-trip of the loaded fields.
    s1 = next(s for s in sigs if s["session_id"] == "ss-1")
    assert s1["signature"] == "abcd1234efgh"
    assert s1["repeat_count"] == 8
    assert s1["severity"] == "warning"
    assert isinstance(s1["details"], dict)
    assert s1["details"]["model"] == "claude-sonnet-4"


def test_api_loop_signals_empty_when_no_rows(fresh_store, monkeypatch):
    """Empty DuckDB → ``signals=[]``, ``count=0``, HTTP 200. The Brain
    badge needs the empty path to be a clean 200, not a 500, so the
    ``display:none`` default sticks."""
    sys.modules.pop("routes.health", None)
    import routes.health as rh
    importlib.reload(rh)

    from flask import Flask
    app = Flask(__name__)
    app.register_blueprint(rh.bp_health)
    client = app.test_client()

    resp = client.get("/api/loop-signals")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["signals"] == []
    assert body["count"] == 0
    # Empty store → nothing to cap, regardless of Pro status.
    assert body["total_count"] == 0
    assert body["capped_pro_gated"] is False


# ── 5. OSS row-cap + Pro gate (issue #1376) ─────────────────────────────────


def test_api_loop_signals_oss_capped_to_single_teaser_row(fresh_store, monkeypatch):
    """OSS / Cloud-Free callers see one teaser row plus ``capped_pro_gated``
    so the UI can render the upgrade CTA. Loop history + alert dispatch is
    a Cloud-Pro value — shipping unbounded rows in OSS leaks it."""
    ls, store = fresh_store
    for i in range(5):
        store.ingest_loop_signal(
            session_id=f"sess-{i}",
            signature=f"sig-{i}",
            repeat_count=i + 3,
            first_seen=f"2026-05-15T10:0{i}:00",
            last_seen=f"2026-05-15T10:0{i}:00",
        )

    sys.modules.pop("routes.health", None)
    import routes.health as rh
    importlib.reload(rh)

    # Force OSS / non-Pro path.
    import dashboard as _d
    monkeypatch.setattr(_d, "_is_pro_user", lambda: False)

    from flask import Flask
    app = Flask(__name__)
    app.register_blueprint(rh.bp_health)
    client = app.test_client()

    resp = client.get("/api/loop-signals?limit=20&since_minutes=0")
    assert resp.status_code == 200
    body = resp.get_json()
    # Cap drops to 1 row; total_count reflects the un-capped value so the
    # badge can still show "5 loops" while the table only renders 1.
    assert body["count"] == 1
    assert body["total_count"] == 5
    assert body["capped_pro_gated"] is True
    assert len(body["signals"]) == 1

    # Pro caller sees the full list and the flag flips off.
    monkeypatch.setattr(_d, "_is_pro_user", lambda: True)
    resp_pro = client.get("/api/loop-signals?limit=20&since_minutes=0")
    body_pro = resp_pro.get_json()
    assert body_pro["count"] == 5
    assert body_pro["total_count"] == 5
    assert body_pro["capped_pro_gated"] is False


# ── 4. LoopDetector → LocalStore wiring ────────────────────────────────────


def test_loop_detector_persists_signal_on_positive(fresh_store, tmp_path, monkeypatch):
    """When ``LoopDetector.check`` flags a loop, it should also write a
    row to ``loop_signals`` (best-effort — single-process mode here makes
    the call succeed; in production where proxy + daemon are separate
    processes the call silently no-ops on the lock conflict, by design)."""
    ls, store = fresh_store

    # Use a tmp proxy SQLite so we don't touch the user's ~/.clawmetry.
    monkeypatch.setattr(
        "clawmetry.proxy.PROXY_DB_FILE", tmp_path / "proxy.db"
    )
    sys.modules.pop("clawmetry.proxy", None)
    import clawmetry.proxy as proxy
    importlib.reload(proxy)

    cfg = proxy.LoopDetectionConfig(
        enabled=True, window_seconds=300, max_similar=3
    )
    pdb = proxy.ProxyDB(db_path=tmp_path / "proxy.db")
    detector = proxy.LoopDetector(cfg, pdb)

    # Seed enough identical hashes to trip max_similar=3.
    sid = "loop-sess"
    rh = "deadbeef00112233"
    for _ in range(3):
        pdb.record_usage(
            provider="anthropic", model="claude-sonnet-4",
            input_tokens=10, output_tokens=10, cost_usd=0.0,
            session_id=sid, request_hash=rh,
        )

    is_loop, reason = detector.check(sid, rh)
    assert is_loop is True
    assert "Loop detected" in reason

    rows = store.query_recent_loop_signals(limit=10, since_minutes=0)
    assert len(rows) == 1
    r = rows[0]
    assert r["session_id"] == sid
    assert r["signature"] == rh
    # match_count is the >= max_similar value at detect time.
    assert r["repeat_count"] >= 3
