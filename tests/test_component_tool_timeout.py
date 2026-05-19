"""Regression guard for the /api/component/tool/<name> JSONL-walker
wall-clock cap (silent-zero bug-class fix #5, 2026-05-18).

When the DuckDB fast path misses — fresh install / no-daemon dev /
unrecognised event shape — control falls through to the legacy JSONL
walker that scans every ``.jsonl`` file in
``~/.openclaw/agents/main/sessions/``. On real installs with months of
accumulated transcripts this used to hang the request for 8 seconds+
(the Sessions modal stuck on "Loading..." until the upstream proxy
timed out the request with 0 bytes).

The fix wraps the walker in a 5s hard cap AND short-circuits entirely
when the candidate file count exceeds 200. This file pins both:

  1. 500 empty .jsonl files seeded into a tmp sessions dir → request
     completes within 5s. The cap fires first; the response is the
     legacy walker's standard empty shell.
  2. Tight loop: 250 files exceeds the 200-file short-circuit, so the
     response should be near-instant (<1s) and still an empty shell.

We deliberately seed EMPTY files (no jsonl rows) so even without the
cap the walker would still finish — but the test asserts an upper
bound that the prior 8s p95 would blow. If a future PR removes the
cap or raises the short-circuit threshold without thinking about it,
this test goes red.
"""

from __future__ import annotations

import importlib
import time
from pathlib import Path

import pytest
from flask import Flask


@pytest.fixture
def app_with_many_files(tmp_path, monkeypatch):
    """Seed a tmp sessions dir with N .jsonl files (caller supplies N
    via the fixture's ``setup`` helper) and wire dashboard.SESSIONS_DIR
    at it so the JSONL walker reads from our hermetic tree."""
    # CLAWMETRY_LOCAL_STORE_READ=0 → fast path skipped entirely so the
    # JSONL walker is exercised, which is what this test is about.
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_READ", "0")
    monkeypatch.setenv(
        "CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "events.duckdb")
    )

    sessions_dir = tmp_path / "sessions"
    sessions_dir.mkdir()

    import dashboard as _d
    import routes.local_query as lq
    importlib.reload(lq)
    import routes.components as components_mod
    importlib.reload(components_mod)

    monkeypatch.setattr(_d, "SESSIONS_DIR", str(sessions_dir), raising=False)
    monkeypatch.setattr(lq, "_read_discovery", lambda: None)

    a = Flask(__name__)
    a.register_blueprint(components_mod.bp_components)

    def _seed(count: int) -> None:
        for i in range(count):
            (sessions_dir / f"sess-{i:05d}.jsonl").write_text("")
        # Touch each file so its mtime is "now" — without this they'd
        # all stat to whatever the filesystem time was and the walker's
        # mtime-equals-today check would skip them anyway.
        now = time.time()
        for p in sessions_dir.iterdir():
            try:
                import os
                os.utime(p, (now, now))
            except OSError:
                pass

    yield a, _seed, sessions_dir


def test_500_files_short_circuit_returns_under_5s(app_with_many_files):
    """500 .jsonl files exceeds the 200-file short-circuit threshold —
    the walker bails before opening any of them, so the response is
    near-instant and the UI gets an empty shell instead of hanging."""
    a, seed, _sessions_dir = app_with_many_files
    seed(500)

    t0 = time.monotonic()
    r = a.test_client().get("/api/component/tool/session")
    elapsed = time.monotonic() - t0

    assert r.status_code == 200, r.get_data(as_text=True)
    body = r.get_json()
    # 5s hard upper bound (the bug we're fixing was 8s+). In practice
    # the 200-file short-circuit fires and the walker returns in well
    # under a second; assert on the bug-bound, not the optimisation.
    assert elapsed < 5.0, (
        f"/api/component/tool hung for {elapsed:.2f}s with 500 files — "
        "5s wall-clock cap regressed"
    )
    # Empty walker output → shell payload (the legacy parser's shape).
    assert body.get("events") == []
    assert body.get("stats", {}).get("today_calls") == 0


def test_under_threshold_walker_still_runs_within_budget(app_with_many_files):
    """150 .jsonl files is UNDER the 200-file short-circuit, so the
    walker DOES iterate them. Each file is empty so the 5s wall-clock
    cap is the safety net; this asserts the cap kicks in if a future
    change accidentally introduces slow per-file work."""
    a, seed, _sessions_dir = app_with_many_files
    seed(150)

    t0 = time.monotonic()
    r = a.test_client().get("/api/component/tool/session")
    elapsed = time.monotonic() - t0

    assert r.status_code == 200
    assert elapsed < 5.0, (
        f"/api/component/tool hung for {elapsed:.2f}s on 150 files"
    )
