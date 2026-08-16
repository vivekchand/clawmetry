"""Per-runtime quality conformance — Phase 0 of the 2026-08-15 rebuild, as a
live gate rather than a one-off research artifact.

The audit's root cause was a signal that silently did not apply to a runtime.
The parser found no tool calls in Claude Code's events, so the guard that
prevents false positives never ran, and nobody noticed because "no tool calls
parsed" and "the agent made no tool calls" were indistinguishable.

This test makes them distinguishable. For every runtime fixture in the repo it
ingests the REAL capture and asserts:

  1. events land with a runtime-namespaced session id,
  2. the capability probe reports what that runtime actually emits, and
  3. **if the raw events contain tool calls, the probe MUST see them.**

(3) is the anti-blindness assertion. It fails loudly the moment an adapter
lands a payload shape ``quality_signals.normalize_events`` cannot read —
instead of quietly grading that runtime on a dead signal.

Skips cleanly without clawmetry-pro (OSS CI has no paid adapters).
"""
from __future__ import annotations

import importlib
import importlib.util
import json
import os
import time
from unittest.mock import patch

import pytest

pytest.importorskip(
    "clawmetry_pro", reason="paid runtime adapters live in clawmetry-pro")

from clawmetry.quality_signals import (  # noqa: E402
    SIGNALS, normalize_events, probe_capabilities,
)

_FIX_ROOT = os.path.join(os.path.dirname(__file__), "fixtures", "runtimes")


def _wait_for_flush(store, timeout=5.0):
    """Drain the async ring buffer before reading, like the sibling ingest
    tests. Reading too early yields an empty store and a hollow skip."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            if store.health()["ring_depth"] == 0:
                return
        except Exception:
            return
        time.sleep(0.02)

# Runtime → how to point its adapter at the committed fixture.
#
# ``(env_var, relative_path)``; the path resolves under this runtime's fixture
# directory. Harvested from each adapter's own env lookups and the sibling
# ingest tests, NOT guessed — a wrong mapping shows up as a skip, and a silent
# skip is how a conformance gate becomes decorative.
_FIXTURE_ENV = {
    "claude_code":  ("CLAUDE_CONFIG_DIR",           "."),
    "codex":        ("CODEX_HOME",                  "REAL"),
    "copilot":      ("CLAWMETRY_COPILOT_HOME",      "REAL"),
    "antigravity":  ("CLAWMETRY_ANTIGRAVITY_HOME",  "REAL"),
    "n8n":          ("CLAWMETRY_N8N_DB",   "REAL/database.sqlite"),
    "picoclaw":     ("PICOCLAW_HOME",               "."),
    "nanoclaw":     ("CLAWMETRY_NANOCLAW_DIR",      "REAL"),
    "qwen_code":    ("QWEN_HOME",                   "REAL"),
    "opencode":     ("CLAWMETRY_OPENCODE_DB",       "opencode.db"),
    "cursor":       ("CLAWMETRY_CURSOR_DB",
                     "data/User/globalStorage/state.vscdb"),
    "aider":        ("AIDER_HISTORY_DIRS",          "e5ff42609174"),
    # goose reads XDG_DATA_HOME and expects <XDG>/goose/sessions/sessions.db,
    # but the fixture keeps sessions/ at its root. The test builds the expected
    # layout in tmp rather than moving the committed fixture.
    "goose":        ("XDG_DATA_HOME",               "@goose-xdg"),
}


def _fixture_runtimes():
    if not os.path.isdir(_FIX_ROOT):
        return []
    return sorted(
        d for d in os.listdir(_FIX_ROOT)
        if os.path.isdir(os.path.join(_FIX_ROOT, d)) and not d.startswith("_")
    )


def _raw_tool_call_hint(rows) -> bool:
    """Do the ingested rows LOOK like they contain tool use?

    Deliberately independent of ``normalize_events`` — it sniffs the raw JSON
    for tool markers. If this says yes and the probe says no, the reader has a
    blind spot, which is precisely the bug class this file guards.
    """
    for r in rows:
        et = (r.get("event_type") or "").lower()
        if et in ("tool_call", "tool.use", "tool.call", "tool_use"):
            return True
        blob = r.get("data")
        if isinstance(blob, (bytes, bytearray)):
            blob = blob.decode("utf-8", "replace")
        if not isinstance(blob, str):
            try:
                blob = json.dumps(blob, default=str)
            except Exception:
                continue
        if '"tool_calls"' in blob or '"tool_use"' in blob or '"tool_name"' in blob:
            return True
    return False


def _raw_tool_input_hint(rows) -> bool:
    """Do the raw rows carry tool-call INPUTS, independent of the normalizer?

    Structural on purpose. A substring search for ``"input"`` also matches the
    ``inputTokens`` usage counters that ride along on most family events, which
    would make this assert against runtimes whose tool calls genuinely carry no
    arguments. Same independence rationale as ``_raw_tool_call_hint``: parse
    the payload ourselves rather than asking the code under test.
    """
    for r in rows:
        blob = r.get("data")
        if isinstance(blob, (bytes, bytearray)):
            blob = blob.decode("utf-8", "replace")
        if isinstance(blob, str):
            try:
                blob = json.loads(blob)
            except Exception:
                continue
        if not isinstance(blob, dict):
            continue
        for tc in (blob.get("tool_calls") or []):
            if isinstance(tc, dict) and isinstance(
                    tc.get("input") or tc.get("arguments"), dict):
                if tc.get("input") or tc.get("arguments"):
                    return True
        if isinstance(blob.get("input"), dict) and blob.get("name"):
            return True
    return False


@pytest.mark.parametrize("runtime", _fixture_runtimes())
def test_runtime_quality_conformance(runtime, tmp_path, monkeypatch):
    """Ingest a runtime's real capture and prove the quality reader sees it."""
    fixture_home = os.path.join(_FIX_ROOT, runtime)
    mapping = _FIXTURE_ENV.get(runtime)
    if not mapping:
        pytest.fail(
            f"{runtime} has a committed fixture but no env mapping here. "
            f"Add one so the runtime is actually graded — an unmapped runtime "
            f"silently skips, which is how this gate goes hollow."
        )
    env, rel = mapping
    if rel == "@goose-xdg":
        import shutil
        xdg = tmp_path / "xdg"
        (xdg / "goose").mkdir(parents=True, exist_ok=True)
        shutil.copytree(os.path.join(_FIX_ROOT, runtime, "sessions"),
                        str(xdg / "goose" / "sessions"), dirs_exist_ok=True)
        fixture_home = str(xdg)
    elif rel != ".":
        fixture_home = os.path.join(_FIX_ROOT, runtime, rel)

    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "e.duckdb"))
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_SECS", "0.05")
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_BATCH", "5")
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv(env, fixture_home)

    import clawmetry.local_store as ls
    import clawmetry.sync as sync
    importlib.reload(ls)
    importlib.reload(sync)
    monkeypatch.setattr(ls, "_daemon_registered", lambda: False)
    monkeypatch.delenv("CLAWMETRY_ROLE", raising=False)

    try:
        config = {"node_id": "test-node", "api_key": "test-key"}
        try:
            with patch.object(sync, "_sync_allowed", return_value=True), \
                 patch.object(sync, "_post", return_value={}):
                sync.sync_family_runtimes(config, {}, {})
        except Exception as e:
            pytest.skip(f"{runtime} adapter unavailable in this build: {e}")
        store = ls.get_store()
        _wait_for_flush(store)

        rows = store.query_events(runtime=runtime, limit=4000) or []
        if not rows:
            pytest.skip(f"{runtime} fixture ingested no events")

        # 1. runtime-namespaced ids, so the Quality tab can scope by prefix
        #    instead of the hardcoded agent_type column.
        assert all(str(r.get("session_id", "")).startswith(f"{runtime}:")
                   for r in rows), f"{runtime}: events not namespaced"

        # 2. the probe reports what this runtime emits
        events = normalize_events(rows)
        caps = probe_capabilities(events, runtime=runtime)
        assert caps.sample_events > 0

        # 3. THE ANTI-BLINDNESS ASSERTIONS
        if _raw_tool_call_hint(rows):
            assert caps.has_tool_calls, (
                f"{runtime}: the raw events contain tool calls but "
                f"normalize_events parsed NONE of them. This is the exact "
                f"failure that made the old cognitive-loop detector flag "
                f"sessions with 60+ real tool calls. Teach "
                f"quality_signals._tool_calls_of this runtime's payload shape."
            )
        # Names alone are not enough. Thrash detection digests the INPUT and
        # no_forward_progress reads the file path out of it, so a reader that
        # recovers the tool name but drops its input leaves both signals dead
        # while the capability probe still looks healthy — a quieter version
        # of the original bug. Assert the input survives whenever the raw
        # payload carried one.
        if _raw_tool_input_hint(rows):
            assert caps.has_tool_inputs, (
                f"{runtime}: tool calls carry inputs in the raw events, but "
                f"normalize_events dropped every one. Thrash and "
                f"forward-progress detection both read the input; without it "
                f"they silently never fire for this runtime."
            )

        # A runtime that reports tool errors must expose the error-rate signal;
        # one that does not must NOT silently look healthy.
        if caps.has_error_flags:
            assert caps.supports("tool_error_rate")
        else:
            assert not caps.supports("tool_error_rate")

        # Whatever it supports must be a real, declared signal.
        for name in caps.as_dict()["supported_signals"]:
            assert name in SIGNALS
    finally:
        try:
            ls.get_store().stop(flush=True)
        except Exception:
            pass


def test_at_least_one_runtime_fixture_exists():
    """Guards against the parametrised suite silently becoming a no-op."""
    assert _fixture_runtimes(), "no runtime fixtures found — the gate is inert"


def test_quality_is_graded_at_ingest_and_persisted(tmp_path, monkeypatch):
    """The daemon must grade a session while it has the events in hand.

    This is what keeps the Quality tab a pure DuckDB read. If grading silently
    stops happening at ingest, the endpoint falls back to replaying events per
    request — correct, but a request storm on every tab load. Gate it.
    """
    fixture = os.path.join(_FIX_ROOT, "claude_code")
    if not os.path.isdir(fixture):
        pytest.skip("claude_code fixture missing")

    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "q.duckdb"))
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_SECS", "0.05")
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_BATCH", "5")
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", fixture)

    import clawmetry.local_store as ls
    import clawmetry.sync as sync
    importlib.reload(ls)
    importlib.reload(sync)
    monkeypatch.setattr(ls, "_daemon_registered", lambda: False)
    monkeypatch.delenv("CLAWMETRY_ROLE", raising=False)

    try:
        with patch.object(sync, "_sync_allowed", return_value=True), \
             patch.object(sync, "_post", return_value={}):
            sync.sync_family_runtimes({"node_id": "n", "api_key": "k"}, {}, {})
        store = ls.get_store()
        _wait_for_flush(store)
        rows = store._fetch(
            "SELECT metadata FROM sessions WHERE session_id LIKE 'claude_code:%'",
            (),
        )
        if not rows:
            pytest.skip("claude_code fixture ingested no sessions")
        meta = json.loads(rows[0][0]) if rows[0][0] else {}
        assert meta.get("runtime") == "claude_code"
        q = meta.get("quality")
        assert isinstance(q, dict), "quality assessment was not persisted at ingest"
        # Shape contract the endpoint reads back.
        assert "measurable" in q and "verdicts" in q
        assert q.get("runtime") == "claude_code"
        # And the invariant survives the round trip: no verdict without evidence.
        for v in q["verdicts"]:
            assert v["evidence"]["exhibits"], "persisted a verdict with no evidence"
    finally:
        try:
            ls.get_store().stop(flush=True)
        except Exception:
            pass
