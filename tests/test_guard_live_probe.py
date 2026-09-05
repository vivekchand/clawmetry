"""Guard lists a running session before the store has heard of it.

The Guard tab read its "what is running right now" list purely from DuckDB, so
its freshness was the sync daemon's whole cycle. Measured on a founder laptop:
passes took 60-78s normally, and one took **288s** immediately after a
``runtime_backfill`` raised the claude_code ingest depth to 1088 sessions. A
Claude Code session started 2m18s into that window had no row and no Kill
button for over three minutes, while its pid was resolvable in ~5ms the whole
time.

These tests pin the two halves of the fix: ``process_control.live_sessions()``
reports only genuinely-live processes, and ``/api/guard/sessions`` merges them
in without duplicating the rows the store already has.
"""
import json

import clawmetry.process_control as pc
import pytest
from flask import Flask

import routes.guard as guard


@pytest.fixture
def client():
    """The Guard blueprint alone — no dashboard boot, no DuckDB."""
    app = Flask(__name__)
    app.register_blueprint(guard.bp_guard)
    return app.test_client()


ALIVE = 4242
DEAD = 4243


@pytest.fixture
def fake_map(monkeypatch):
    """Two claude_code sessions on disk; only one still has a process.

    `started_at` / `updated_at` are stored RAW, in epoch milliseconds, exactly
    as claude_code writes them — #5543 keeps them unconverted so the pid-reuse
    guard's own `procStart` (a ctime string) is never confused with them. The
    conversion to seconds is `live_sessions`' job, and these values are the
    reason that is worth asserting.
    """
    monkeypatch.setattr(pc, "claude_code_session_map", lambda: {
        "aaaa-1111": {"pid": ALIVE, "cwd": "/w/one", "status": "busy",
                      "name": "Father of India",
                      "procStart": "Sat Sep  5 00:36:32 2026",
                      "started_at": 1788568592909, "updated_at": 1788568631928},
        "bbbb-2222": {"pid": DEAD, "cwd": "/w/two", "status": "idle",
                      "name": "stale row",
                      "procStart": "Fri Sep  4 12:00:00 2026",
                      "started_at": 1788500000000, "updated_at": 1788500001000},
    })
    monkeypatch.setattr(pc, "is_alive", lambda pid: pid == ALIVE)


# ── the probe ─────────────────────────────────────────────────────────────
def test_probe_lists_the_live_session_with_its_native_id(fake_map):
    live = pc.live_sessions()
    assert [s["session_id"] for s in live] == ["aaaa-1111"]
    row = live[0]
    assert row["runtime"] == "claude_code"
    assert row["pid"] == ALIVE
    assert row["cwd"] == "/w/one"
    # The title comes from claude_code's own `name`, so a brand-new row is not
    # a bare uuid in the UI.
    assert row["title"] == "Father of India"
    # Milliseconds in, SECONDS out. Publishing the raw value would date the row
    # to the year 58000 and sort it above everything forever.
    assert row["updated_at"] == 1788568631.928
    assert row["started_at"] == 1788568592.909


def test_probe_drops_a_session_whose_process_is_gone(fake_map):
    # A stale <pid>.json outlives its process. Listing it would render a Kill
    # button attached to nothing.
    assert all(s["session_id"] != "bbbb-2222" for s in pc.live_sessions())


def test_probe_never_raises_when_the_map_is_unreadable(monkeypatch):
    def boom():
        raise OSError("sessions dir exploded")
    monkeypatch.setattr(pc, "claude_code_session_map", boom)
    assert pc.live_sessions() == []


# ── the merge ─────────────────────────────────────────────────────────────
def _rows(client):
    resp = client.get("/api/guard/sessions")
    assert resp.status_code == 200
    return json.loads(resp.data)["sessions"]


@pytest.fixture
def store_rows(monkeypatch):
    """Let each test set what the store returns, with no DuckDB involved."""
    state = {"sessions": [], "signals": []}

    def _call(method, **kwargs):
        if method == "query_sessions_table":
            return state["sessions"]
        if method == "query_recent_loop_signals":
            return state["signals"]
        return None

    monkeypatch.setattr(guard, "_ls_call", _call)
    return state


def test_a_running_session_appears_before_the_store_has_it(client, fake_map,
                                                           store_rows):
    # The store knows nothing yet — exactly the 288s backfill window.
    store_rows["sessions"] = []
    rows = _rows(client)
    assert [r["session_id"] for r in rows] == ["claude_code:aaaa-1111"]
    row = rows[0]
    # Namespaced like a store row, so the id posted back to /api/guard/control
    # is identical whichever source the row came from.
    assert row["runtime"] == "claude_code"
    assert row["title"] == "Father of India"
    assert row["pending_ingest"] is True
    # Cost is UNKNOWN, not zero. The tab sorts on money; inventing a figure
    # here would be worse than a blank.
    assert row["cost_usd"] == 0.0
    assert row["incident"] is None


def test_the_probe_does_not_duplicate_a_session_the_store_already_has(
        client, fake_map, store_rows):
    # Store rows carry the `<runtime>:` namespace, the probe reports the native
    # id. Matching on the raw string would list every session twice.
    store_rows["sessions"] = [{
        "session_id": "claude_code:aaaa-1111", "agent_type": "openclaw",
        "status": "active", "title": "Father of India", "cost_usd": 0.23,
        "last_active_at": "2026-09-05T00:38:13+00:00", "metadata": {},
    }]
    rows = _rows(client)
    assert len(rows) == 1
    # The store's row wins: it is the one carrying real cost.
    assert rows[0]["cost_usd"] == 0.23
    assert rows[0].get("pending_ingest") is not True


def test_no_duplicate_when_the_store_row_resolves_to_openclaw(
        client, fake_map, store_rows, monkeypatch):
    """The Free-tier shape, which is what CI runs and what most users install.

    ``_session_runtime`` resolves through ``waste_flags.runtime_from_session_id``,
    which returns "openclaw" for EVERY id unless clawmetry-pro is installed. A
    de-duplication keyed on the store row's runtime label therefore matched
    nothing on Free and listed every Claude Code session twice — once from the
    store and once from the probe. This passed on a Pro laptop and failed in
    CI, so it is pinned with the resolver forced to its Free answer.
    """
    monkeypatch.setattr(guard, "_session_runtime", lambda sid, agent: "openclaw")
    store_rows["sessions"] = [{
        "session_id": "claude_code:aaaa-1111", "agent_type": "openclaw",
        "status": "active", "title": "Father of India", "cost_usd": 0.23,
        "last_active_at": "2026-09-05T00:38:13+00:00", "metadata": {},
    }]
    rows = _rows(client)
    assert len(rows) == 1
    assert rows[0]["cost_usd"] == 0.23


def test_a_just_started_session_outranks_older_unflagged_ones(
        client, fake_map, store_rows):
    # A new row appended at the end of a 50-row table is still "not showing
    # up" to the person looking for it. Unflagged rows sort newest-first.
    store_rows["sessions"] = [{
        "session_id": "claude_code:old-9999", "agent_type": "openclaw",
        "status": "active", "title": "hours ago", "cost_usd": 1.0,
        "last_active_at": "2026-09-05T00:01:00+00:00", "metadata": {},
    }]
    rows = _rows(client)
    assert [r["title"] for r in rows] == ["Father of India", "hours ago"]


def test_a_flagged_session_still_outranks_a_newer_quiet_one(
        client, fake_map, store_rows):
    # Recency is the LAST sort key on purpose: money still decides the top of
    # the table, so the live probe cannot bury a $170 loop under a new tab.
    store_rows["sessions"] = [{
        "session_id": "claude_code:old-9999", "agent_type": "openclaw",
        "status": "active", "title": "expensive loop", "cost_usd": 170.0,
        "last_active_at": "2026-09-05T00:01:00+00:00", "metadata": {},
    }]
    store_rows["signals"] = [{
        "session_id": "claude_code:old-9999", "severity": "critical",
        "repeat_count": 8, "first_seen": "2026-09-05T00:00:00+00:00",
        "details": {"kind": "stuck_loop", "message": "stuck",
                    "spend_at_risk_usd": 170.0, "spend_basis": "burn_rate"},
    }]
    rows = _rows(client)
    assert [r["title"] for r in rows] == ["expensive loop", "Father of India"]


def test_the_list_survives_a_probe_that_throws(client, store_rows,
                                               monkeypatch):
    # A broken probe must cost us the extra rows, never the whole tab.
    def boom():
        raise RuntimeError("probe exploded")
    monkeypatch.setattr(pc, "live_sessions", boom)
    store_rows["sessions"] = [{
        "session_id": "claude_code:old-9999", "agent_type": "openclaw",
        "status": "active", "title": "still here", "cost_usd": 1.0,
        "last_active_at": "2026-09-05T00:01:00+00:00", "metadata": {},
    }]
    assert [r["title"] for r in _rows(client)] == ["still here"]
