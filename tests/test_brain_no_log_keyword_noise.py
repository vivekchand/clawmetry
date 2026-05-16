"""Regression test — ``/api/brain-history`` must NOT mis-classify benign
OpenClaw console messages as tool-invocation events.

Background: ``routes/brain.py`` previously did substring keyword matching on
every OpenClaw log line — any message containing ``"browser"``, ``"read"``,
``"write"``, ``"exec"``, ``"message"``, ``"spawn"`` etc. was tagged as a
BROWSER / READ / WRITE / EXEC / MSG / SPAWN event and pushed into the Brain
feed. That contaminated the live event stream with onboarding/lifecycle text
like:

  ``Opened in your browser. Keep that tab to control OpenClaw.``
  ``Token auto-auth included in browser/clipboard URL.``

These lines are NOT tool calls — they are info-level startup messages from
the OpenClaw CLI. They must not appear as tool events in the Brain feed.

This test seeds a temp OpenClaw log directory with realistic console-log
lines + one legitimately bracketed ``[browser] ...`` tool log line, points
``routes.brain`` at it via the ``_get_log_dirs`` shim, hits the JSONL/log
fallback path (local-store disabled), and asserts:

  1. The "Keep that tab" / "clipboard URL" lines do NOT appear as events
     (no BROWSER event with detail referring to the lifecycle string).
  2. The bracketed ``[browser] ...`` line still produces a BROWSER event
     (we only want to remove the noisy fallback, not the legit format).
"""

from __future__ import annotations

import importlib
import json
import os

import pytest
from flask import Flask


@pytest.fixture
def fallback_app(tmp_path, monkeypatch):
    # Force the legacy JSONL/log fallback path so the keyword-noise branch is
    # exercised. With CLAWMETRY_LOCAL_STORE_READ=0 the DuckDB fast path bails
    # out before the log scan runs, which is what we want to inspect.
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_READ", "0")

    log_dir = tmp_path / "openclaw-logs"
    log_dir.mkdir()
    log_file = log_dir / "openclaw-2026-05-13.log"

    def _line(msg, ts="2026-05-13T22:50:00.911Z"):
        return json.dumps({"0": msg, "message": msg, "time": ts}) + "\n"

    log_file.write_text(
        # Two real-world OpenClaw console messages that USED to be misclassified
        # as BROWSER events because the substring keyword matcher saw "browser".
        _line("Opened in your browser. Keep that tab to control OpenClaw.")
        + _line("Token auto-auth included in browser/clipboard URL.",
                ts="2026-05-13T22:50:00.912Z")
        # And one legitimate bracketed tool-log line that MUST still produce
        # a BROWSER event — we only want to drop the fallback noise, not the
        # well-formed log format.
        + _line("[browser] navigate https://example.com",
                ts="2026-05-13T22:50:01.000Z")
    )

    # Empty session dir so the JSONL scan finds nothing and we isolate the
    # log-path branch.
    sessions_dir = tmp_path / "sessions"
    sessions_dir.mkdir()

    import routes.brain as br
    importlib.reload(br)

    # Patch the late-imported helpers from dashboard.py that the route uses.
    import dashboard as _d
    monkeypatch.setattr(_d, "_get_log_dirs", lambda: [str(log_dir)], raising=True)
    monkeypatch.setattr(_d, "SESSIONS_DIR", str(sessions_dir), raising=True)
    monkeypatch.setattr(_d, "_ext_emit", lambda *a, **k: None, raising=True)
    # 2026-05-13 fixture timestamps fall outside the OSS 24h cap (#1448).
    # Default to Pro so the BROWSER-classification assertion still sees
    # the seeded log line.
    monkeypatch.setattr(_d, "_is_pro_user", lambda: True, raising=True)

    # The route ALSO hard-codes a glob of ``/tmp/openclaw/openclaw-*.log`` and
    # then trims to the last 3 files. On a dev machine with real daemon logs
    # in /tmp/openclaw/, our seeded test log gets shoved out of the window.
    # Wrap glob.glob inside the brain module to drop those real files so the
    # only log file the scan sees is our fixture.
    real_glob = br.glob.glob

    def _scoped_glob(pattern):
        results = real_glob(pattern)
        if "/tmp/openclaw" in pattern:
            return []
        return results

    monkeypatch.setattr(br.glob, "glob", _scoped_glob)

    a = Flask(__name__)
    a.register_blueprint(br.bp_brain)
    return a


def test_lifecycle_console_lines_do_not_become_browser_events(fallback_app):
    c = fallback_app.test_client()
    r = c.get("/api/brain-history?limit=300")
    assert r.status_code == 200, r.get_data(as_text=True)[:300]
    body = r.get_json()

    # Must NOT have come from the local-store fast path (we forced legacy on).
    assert body.get("_source") != "local_store"

    events = body.get("events", [])

    # The two onboarding/lifecycle strings must not appear ANYWHERE in the feed.
    BANNED_FRAGMENTS = (
        "Keep that tab to control OpenClaw",
        "browser/clipboard URL",
    )
    leaked = [
        ev for ev in events
        if any(frag in (ev.get("detail") or "") for frag in BANNED_FRAGMENTS)
    ]
    assert not leaked, (
        f"Brain feed leaked OpenClaw onboarding/lifecycle text as events: "
        f"{[(ev.get('type'), ev.get('detail')) for ev in leaked]}"
    )

    # Sanity: a properly bracketed [browser] log line MUST still classify as
    # BROWSER (we only want to drop the fallback noise, not the legit format).
    browser_evts = [ev for ev in events if ev.get("type") == "BROWSER"]
    assert browser_evts, (
        "Bracketed [browser] log line should still produce a BROWSER event; "
        "removed substring fallback must not have killed the legit path."
    )
    assert any(
        "navigate https://example.com" in (ev.get("detail") or "")
        for ev in browser_evts
    ), [ev.get("detail") for ev in browser_evts]
