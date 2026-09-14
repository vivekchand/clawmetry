"""Regression test for #5984: the Python interceptor writes to
$CLAWMETRY_HOME/intercepted.jsonl (moved there in #2969), but the sync
daemon's sync_intercepted_events historically tailed only the legacy
~/.openclaw/clawmetry-intercepted.jsonl path. Every call captured by
`import clawmetry.track` / CLAWMETRY_TRACK=1 silently never reached the
store or the dashboard.
"""
from __future__ import annotations

import importlib
import json
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import clawmetry.interceptor as I


@pytest.fixture
def fresh_store(tmp_path, monkeypatch):
    """Reload `clawmetry.local_store` against a fresh DuckDB file."""
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "events.duckdb"))
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_SECS", "0.05")
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_BATCH", "1")
    sys.modules.pop("clawmetry.local_store", None)
    import clawmetry.local_store as ls
    importlib.reload(ls)
    # Own the writer so get_store() opens the test DB directly instead of
    # proxying to a daemon that may be running on the dev machine (CI has none).
    ls.mark_writer_owner()
    store = ls.get_store()
    yield ls, store
    try:
        store.stop(flush=False)
    except Exception:
        pass


def _ev(ts, source=None):
    e = {
        "type": "external_api_call", "ts": ts,
        "url": "https://api.openai.com/v1/x", "host": "api.openai.com",
        "method": "post", "status_code": 200, "latency_ms": 9.0, "library": "httpx",
    }
    if source is not None:
        e["source"] = source
    return e


def test_daemon_tails_current_interceptor_path(fresh_store, tmp_path, monkeypatch):
    """The daemon must ingest from the exact path the interceptor writes to."""
    _ls, store = fresh_store
    cm_home = tmp_path / "cm_home"
    monkeypatch.setenv("CLAWMETRY_HOME", str(cm_home))
    I.set_source("")
    os.environ.pop("CLAWMETRY_SOURCE", None)
    I._write_event(_ev("2026-06-02T00:00:06Z", "recon-agent"))
    out_file = I._get_output_file()
    assert out_file == cm_home / "intercepted.jsonl"
    assert out_file.exists(), "interceptor must write where it claims to"

    sys.modules.pop("clawmetry.sync", None)
    import clawmetry.sync as S
    state: dict = {}
    openclaw_dir = tmp_path / "openclaw_unused"
    ingested = S.sync_intercepted_events({}, state, {"openclaw_dir": str(openclaw_dir)})
    assert ingested == 1

    rows = store.query_external_calls(limit=10)
    assert any(r.get("source") == "recon-agent" for r in rows), (
        "a call captured by the interceptor must reach the store"
    )

    # a second tick with no new lines must not re-ingest
    again = S.sync_intercepted_events({}, state, {"openclaw_dir": str(openclaw_dir)})
    assert again == 0


def test_daemon_still_tails_legacy_openclaw_path(fresh_store, tmp_path):
    """Older installs whose events are already under ~/.openclaw keep working."""
    _ls, store = fresh_store
    openclaw_dir = tmp_path / "openclaw"
    openclaw_dir.mkdir()
    legacy_file = openclaw_dir / "clawmetry-intercepted.jsonl"
    legacy_file.write_text(
        json.dumps(_ev("2026-06-02T00:00:07Z", "legacy-agent")) + "\n"
    )

    sys.modules.pop("clawmetry.sync", None)
    import clawmetry.sync as S
    state: dict = {}
    ingested = S.sync_intercepted_events({}, state, {"openclaw_dir": str(openclaw_dir)})
    assert ingested == 1

    rows = store.query_external_calls(limit=10)
    assert any(r.get("source") == "legacy-agent" for r in rows), (
        "the legacy ~/.openclaw path must still be tailed for older installs"
    )


def test_daemon_tails_both_paths_with_independent_cursors(fresh_store, tmp_path, monkeypatch):
    """Both files can have unread lines at once; each keeps its own offset."""
    _ls, store = fresh_store
    cm_home = tmp_path / "cm_home"
    monkeypatch.setenv("CLAWMETRY_HOME", str(cm_home))
    openclaw_dir = tmp_path / "openclaw"
    openclaw_dir.mkdir()
    (openclaw_dir / "clawmetry-intercepted.jsonl").write_text(
        json.dumps(_ev("2026-06-02T00:00:08Z", "legacy-agent-2")) + "\n"
    )
    I.set_source("")
    I._write_event(_ev("2026-06-02T00:00:09Z", "current-agent-2"))

    sys.modules.pop("clawmetry.sync", None)
    import clawmetry.sync as S
    state: dict = {}
    ingested = S.sync_intercepted_events({}, state, {"openclaw_dir": str(openclaw_dir)})
    assert ingested == 2
    assert "last_intercepted_offset" in state
    assert "last_intercepted_offset_legacy" in state

    rows = store.query_external_calls(limit=10)
    sources = {r.get("source") for r in rows}
    assert "legacy-agent-2" in sources
    assert "current-agent-2" in sources
