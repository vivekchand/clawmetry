"""Regression test for the P0 bug where /api/brain-history returned
``detail=""`` for every event after PR #1143's v3 sync mapper landed.

Root cause: the local-store fast path in ``routes/brain.py`` looked for
``data.input/summary/text/name`` only — flat keys that NEITHER the legacy
trajectory parser (which nests under ``data.message.content``) nor the v3
underscore mapper (which projects onto ``data.{finalPromptText,
completionText, output, result}`` and mirrors under ``data.data``) populates.
Result: the Brain tab rendered event-type chips with NO content body.

This test pins down the read contract for ALL three shapes by seeding one
synthetic row of each into a real DuckDB store and asserting the
brain-history JSON carries non-empty ``detail`` for every one of them.
"""

from __future__ import annotations

import importlib
import time

import pytest
from flask import Flask


def _wait_flush(store, t=2.0):
    deadline = time.monotonic() + t
    while time.monotonic() < deadline:
        if store.health()["ring_depth"] == 0:
            return
        time.sleep(0.02)


@pytest.fixture
def brain_app(tmp_path, monkeypatch):
    """Isolated Flask app + tmp DuckDB with the fast path enabled.

    Critically: redirect the daemon-discovery path to a tmp non-existent
    file. Without this, ``routes.brain._try_local_store_brain`` would proxy
    over HTTP to a real running clawmetry daemon (whose discovery file
    sits at ``~/.clawmetry/local_query.json``) and our seed rows would be
    invisible — the test would assert on production data instead.
    """
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "events.duckdb"))
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_SECS", "0.05")
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_BATCH", "5")
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_READ", "1")

    import clawmetry.local_store as ls
    importlib.reload(ls)
    import routes.local_query as lq
    importlib.reload(lq)
    monkeypatch.setattr(
        lq, "_DISCOVERY_PATH", str(tmp_path / "local_query_absent.json"),
    )
    import routes.brain as br
    importlib.reload(br)

    app = Flask(__name__)
    app.register_blueprint(br.bp_brain)
    yield app, ls, br
    try:
        ls.get_store().stop(flush=True)
    except Exception:
        pass


def _events_by_type(body):
    """Map ``event_type`` (lowercased) → first matching event from the response."""
    out = {}
    for ev in body.get("events", []):
        out.setdefault((ev.get("type") or "").lower(), ev)
    return out


def test_brain_history_detail_populated_for_v3_and_legacy_shapes(brain_app):
    """One synthetic row per known shape; every detail must be non-empty.

    Shapes covered:
      * Legacy assistant (data.message.content = list of {type:text})
      * Legacy user (data.message.content = string)
      * v3 mapper top-level (data.completionText)
      * v3 mapper mirror (data.data.finalPromptText)
      * v3 tool result (data.output)
    """
    app, ls, _br = brain_app
    store = ls.get_store()

    rows = [
        # 1. Legacy assistant: data.message.content as block list
        {
            "id": "ev-legacy-asst",
            "node_id": "agent+test", "agent_id": "main",
            "session_id": "sess-1", "event_type": "assistant",
            "ts": "2026-05-13T12:00:01Z",
            "data": {
                "type": "assistant",
                "message": {
                    "role": "assistant",
                    "content": [
                        {"type": "text", "text": "Hello from the assistant block list"}
                    ],
                },
            },
        },
        # 2. Legacy user: data.message.content as string
        {
            "id": "ev-legacy-user",
            "node_id": "agent+test", "agent_id": "main",
            "session_id": "sess-1", "event_type": "user",
            "ts": "2026-05-13T12:00:02Z",
            "data": {
                "type": "user",
                "message": {"role": "user", "content": "What is the weather today?"},
            },
        },
        # 3. v3 mapper top-level: data.completionText
        {
            "id": "ev-v3-completion",
            "node_id": "agent+test", "agent_id": "main",
            "session_id": "sess-1", "event_type": "model.completed",
            "ts": "2026-05-13T12:00:03Z",
            "data": {
                "type": "model.completed",
                "completionText": "v3 completion text body",
                "modelId": "claude-opus-4-7",
                "data": {"completionText": "v3 completion text body"},
            },
        },
        # 4. v3 mapper MIRROR ONLY (top-level keys absent): data.data.finalPromptText
        #    This is the exact shape that PR #1143 introduced and that the
        #    pre-fix reader missed entirely — top-level had no flat content.
        {
            "id": "ev-v3-prompt-mirror",
            "node_id": "agent+test", "agent_id": "main",
            "session_id": "sess-1", "event_type": "prompt.submitted",
            "ts": "2026-05-13T12:00:04Z",
            "data": {
                "type": "prompt.submitted",
                "_v3_type": "message",
                "data": {"finalPromptText": "v3 prompt nested under data.data"},
            },
        },
        # 5. v3 tool result: data.output
        {
            "id": "ev-v3-tool-result",
            "node_id": "agent+test", "agent_id": "main",
            "session_id": "sess-1", "event_type": "tool.result",
            "ts": "2026-05-13T12:00:05Z",
            "data": {
                "type": "tool.result",
                "output": "ls /tmp output: foo bar baz",
                "result": "ls /tmp output: foo bar baz",
                "data": {"output": "ls /tmp output: foo bar baz"},
            },
        },
    ]
    for r in rows:
        store.ingest(r)
    _wait_flush(store)

    body = app.test_client().get("/api/brain-history?limit=20").get_json()

    assert body["_source"] == "local_store", (
        "expected fast-path response (local_store), got: " + str(body)
    )
    assert body["count"] >= 5, body

    by_type = _events_by_type(body)

    # Each event_type must have non-empty detail.
    expected = {
        "assistant":         "Hello from the assistant block list",
        "user":              "What is the weather today?",
        "model.completed":   "v3 completion text body",
        "prompt.submitted":  "v3 prompt nested under data.data",
        "tool.result":       "ls /tmp output: foo bar baz",
    }
    for et, snippet in expected.items():
        ev = by_type.get(et)
        assert ev is not None, f"missing event of type {et!r} in response: {body}"
        assert ev["detail"], (
            f"P0 regression: detail empty for event_type={et!r} — pre-fix "
            f"behaviour. Event: {ev}"
        )
        assert snippet in ev["detail"], (
            f"detail for {et!r} did not include expected snippet "
            f"{snippet!r}; got {ev['detail']!r}"
        )


def test_extract_brain_detail_unit_handles_all_shapes():
    """Pure-Python unit cover for the helper, independent of DuckDB. Lets a
    failing assertion point straight at the extractor instead of a Flask
    integration suite."""
    import importlib
    import routes.brain as br
    importlib.reload(br)

    # Legacy assistant: block list with text
    assert br._extract_brain_detail({
        "data": {"message": {"role": "assistant", "content": [
            {"type": "text", "text": "alpha"},
        ]}},
    }) == "alpha"

    # Legacy user: string content
    assert br._extract_brain_detail({
        "data": {"message": {"role": "user", "content": "beta"}},
    }) == "beta"

    # v3 top-level
    assert br._extract_brain_detail({
        "data": {"completionText": "gamma"},
    }) == "gamma"

    # v3 mirror only
    assert br._extract_brain_detail({
        "data": {"data": {"finalPromptText": "delta"}},
    }) == "delta"

    # Encrypted-thinking-only assistant turn → placeholder, not cwd noise
    assert br._extract_brain_detail({
        "data": {
            "cwd": "/Users/x/workspace",
            "message": {"role": "assistant", "content": [
                {"type": "thinking", "thinking": "", "signature": "blob"},
            ]},
        },
    }) == "(thinking)"

    # Empty / non-dict data → empty string (no crash)
    assert br._extract_brain_detail({}) == ""
    assert br._extract_brain_detail({"data": None}) == ""
    assert br._extract_brain_detail({"data": "raw string"}) == "raw string"
