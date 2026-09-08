"""Per-runtime gate for /api/live-sessions (FLYWHEEL: "verify across ALL
runtimes, never just one").

The liveness fix (#4891) changed ingest for every runtime at once, but it was
verified live on Claude Code only — the exact shape of bug this repo has been
burned by before (a filter that hard-codes the first runtime passes a
one-runtime eyeball).

The runtime list is DERIVED from ``clawmetry.entitlements`` rather than
hand-maintained here, so a newly-landed runtime is covered the day it ships
instead of silently falling outside the gate.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from flask import Flask

from clawmetry.entitlements import ALL_RUNTIMES

RUNTIMES = sorted(ALL_RUNTIMES)


def _iso(delta_secs: float) -> str:
    return (datetime.now(timezone.utc) - timedelta(seconds=delta_secs)).isoformat()


def _rows_for_every_runtime():
    """One working, one waiting and one long-dead session per runtime."""
    rows = []
    for rt in RUNTIMES:
        rows.append({"session_id": "%s:live" % rt, "title": "%s working" % rt,
                     "last_active_at": _iso(10), "status": "active",
                     "metadata": {"runtime": rt}})
        rows.append({"session_id": "%s:parked" % rt, "title": "%s waiting" % rt,
                     "last_active_at": _iso(300), "status": "idle",
                     "metadata": {"runtime": rt}})
        rows.append({"session_id": "%s:dead" % rt, "title": "%s finished" % rt,
                     "last_active_at": _iso(90000), "status": "ended",
                     "metadata": {"runtime": rt}})
    return rows


@pytest.fixture
def client(monkeypatch):
    import routes.sessions as sessions_mod
    monkeypatch.setattr(sessions_mod, "_fetch_sessions_table_rows",
                        lambda limit=200: _rows_for_every_runtime())
    app = Flask(__name__)
    app.register_blueprint(sessions_mod.bp_sessions)
    return app.test_client()


def test_catalogue_is_not_empty():
    """Guard the guard: an import failure yielding [] would make every
    parametrised case below vacuously pass."""
    assert len(RUNTIMES) >= 20, RUNTIMES


@pytest.mark.parametrize("runtime", RUNTIMES)
def test_scopes_to_each_runtime(client, runtime):
    d = client.get("/api/live-sessions?runtime=%s" % runtime).get_json()

    leaked = [s for s in d["sessions"] if s["runtime"] != runtime]
    assert not leaked, "%s leaked other runtimes: %s" % (runtime, leaked)

    assert d["counts"] == {"working": 1, "waiting": 1}, (
        "%s should report exactly its own live pair" % runtime
    )
    titles = [s["title"] for s in d["sessions"]]
    assert titles == ["%s working" % runtime, "%s waiting" % runtime], (
        "%s: wrong rows or wrong order (expected most-recent first)" % runtime
    )
    assert all("finished" not in t for t in titles), (
        "%s: a long-dead session is being shown as live" % runtime
    )


def test_unscoped_covers_every_runtime(client):
    """all-runtimes mode must see every runtime, not just the first."""
    d = client.get("/api/live-sessions").get_json()
    assert d["counts"]["working"] == len(RUNTIMES)
    assert d["counts"]["waiting"] == len(RUNTIMES)


def test_unknown_runtime_returns_nothing_not_the_node_total(client):
    d = client.get("/api/live-sessions?runtime=not-a-runtime").get_json()
    assert d["sessions"] == []
    assert d["counts"] == {"working": 0, "waiting": 0}
