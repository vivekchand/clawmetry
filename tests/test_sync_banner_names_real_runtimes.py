"""Guards for the sync banner's runtime honesty (issue: hardcoded OpenClaw).

The banner shipped the literal string "Syncing your OpenClaw workspace", so it
asserted OpenClaw on every machine, including the majority that only run Claude
Code / Codex / Cursor and have never installed OpenClaw. These tests pin the
three halves of the fix:

  1. no hardcoded runtime name in the served template or the JS fallback,
  2. ``/api/sync-progress`` carries a ``runtimes`` list the banner can name,
  3. detection is honest (sessions on disk, never presence alone) and never
     runs inline in the polled request handler.

Each assertion fails against the pre-fix tree, which is the point.
"""
from __future__ import annotations

import json
import os
import re
import time

import pytest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BANNERS = os.path.join(REPO, "clawmetry", "templates", "partials", "banners.html")
APP_JS = os.path.join(REPO, "clawmetry", "static", "js", "app.js")


def _read(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


# ── 1. No hardcoded runtime in the banner's static copy ──────────────────────

def test_banner_template_does_not_hardcode_a_runtime():
    """The static default must be runtime-neutral: it renders before any
    detection has landed, on machines that may have no OpenClaw at all."""
    html = _read(BANNERS)
    title = re.search(r'id="sync-status-title"[^>]*>([^<]*)<', html)
    assert title, "sync-status-title element disappeared from banners.html"
    text = title.group(1)
    assert "OpenClaw" not in text, (
        f"sync banner still asserts OpenClaw in its static default: {text!r}"
    )


def test_banner_js_fallback_is_runtime_neutral():
    """_cmSyncScopeTitle must fall back to a neutral phrase, never to a
    named runtime, when detection is empty or the endpoint 404s."""
    js = _read(APP_JS)
    assert "function _cmSyncScopeTitle(" in js, "_cmSyncScopeTitle helper is gone"
    fn = js[js.index("function _cmSyncScopeTitle("):]
    fn = fn[: fn.index("\n}\n") + 3]
    assert "Syncing your AI agents" in fn, "neutral fallback copy missing"
    for runtime in ("OpenClaw", "Claude Code", "Codex", "Cursor"):
        assert runtime not in fn, (
            f"{runtime!r} is hardcoded in the title builder; the name must come "
            "from prog.runtimes, never from source"
        )


def test_render_sets_the_title_from_detected_runtimes():
    """A helper nobody calls is dead code: pin the wiring too."""
    js = _read(APP_JS)
    body = js[js.index("function _cmSyncRender(prog, health) {"):]
    body = body[: body.index("\nasync function _cmSyncTick")]
    assert "_cmSyncScopeTitle(prog)" in body, (
        "_cmSyncRender no longer sets the title from the detected runtimes"
    )


# ── 2. The endpoint carries the runtimes ─────────────────────────────────────

class _NullArgs:
    """Stands in for the CLI argparse Namespace.

    ``detect_config()`` registers these routes, and its ``args=None`` path
    builds a bare ``argparse.Namespace`` that then AttributeErrors on
    ``args.log_dir``. Every attribute here answers None, so each ``if args and
    args.x`` falls through to the normal auto-detection.
    """

    def __getattr__(self, name):
        return None


@pytest.fixture(scope="module")
def client():
    import dashboard as _d
    # The sync-progress route is registered inside detect_config(), not at
    # import, so a bare `import dashboard` has an empty url_map.
    if not any("/api/sync-progress" in str(r) for r in _d.app.url_map.iter_rules()):
        _d.detect_config(_NullArgs())
    _d.app.config["TESTING"] = True
    return _d.app.test_client()


def test_sync_progress_includes_runtimes_when_file_present(client, monkeypatch, tmp_path):
    prog = tmp_path / "sync_progress.json"
    prog.write_text(json.dumps({"phase": "session_metadata", "status": "running"}))

    real_expanduser = os.path.expanduser

    def fake_expanduser(p):
        if p == "~/.clawmetry/sync_progress.json":
            return str(prog)
        return real_expanduser(p)

    monkeypatch.setattr(os.path, "expanduser", fake_expanduser)
    r = client.get("/api/sync-progress")
    assert r.status_code == 200
    body = r.get_json()
    assert "runtimes" in body, "banner has nothing to name without a runtimes list"
    assert isinstance(body["runtimes"], list)


def test_sync_progress_includes_runtimes_even_on_404(client, monkeypatch):
    """Cold install: no progress file yet, but the banner still renders. It
    must still be able to name the runtimes rather than falling back to a lie."""
    real_isfile = os.path.isfile
    monkeypatch.setattr(
        os.path, "isfile",
        lambda p: False if str(p).endswith("sync_progress.json") else real_isfile(p),
    )
    r = client.get("/api/sync-progress")
    assert r.status_code == 404
    assert isinstance(r.get_json().get("runtimes"), list)


# ── 3. Detection is off the request path, and honest ─────────────────────────

def test_scope_lookup_never_blocks_the_request():
    """Detection globs session dirs and measured ~3.3s. The banner polls, so a
    blocking lookup would stall every poll. It must serve a cache."""
    import dashboard as _d
    t0 = time.monotonic()
    out = _d._sync_scope_runtimes()
    elapsed = time.monotonic() - t0
    assert isinstance(out, list)
    assert elapsed < 0.5, f"_sync_scope_runtimes blocked for {elapsed:.2f}s"


def test_zero_session_runtimes_are_never_named(monkeypatch):
    """Presence is not usage. The Cursor IDE creates its state dir whether or
    not the agent was ever run; naming it would be a different lie."""
    import dashboard as _d
    from clawmetry import sync as _sync_mod

    monkeypatch.setattr(
        _sync_mod, "_detect_runtimes_lite",
        lambda: [{"id": "cursor", "label": "Cursor", "sessions": 0},
                 {"id": "codex", "label": "Codex", "sessions": 7}],
        raising=False,
    )
    monkeypatch.setattr(_sync_mod, "_detect_family_runtimes", lambda: [], raising=False)
    monkeypatch.setattr(
        "clawmetry.adapters.registry.detect_all", lambda: [], raising=False
    )
    monkeypatch.setattr(
        _d, "_SYNC_SCOPE_CACHE",
        {"ts": 0.0, "runtimes": [], "running": False}, raising=False,
    )
    ids = {r["id"] for r in _d._sync_scope_refresh()}
    assert "codex" in ids, "a runtime with real sessions must be named"
    assert "cursor" not in ids, "a 0-session runtime must never be named"


def test_detection_failure_clears_the_inflight_flag(monkeypatch):
    """A raise inside the refresh thread must not wedge the cache forever."""
    import dashboard as _d
    monkeypatch.setattr(
        _d, "_SYNC_SCOPE_CACHE",
        {"ts": 0.0, "runtimes": [], "running": True}, raising=False,
    )
    def boom():
        raise RuntimeError("detector exploded")
    monkeypatch.setattr(_d, "_sync_scope_refresh", boom, raising=False)
    _d._sync_scope_refresh_safe()
    assert _d._SYNC_SCOPE_CACHE["running"] is False
