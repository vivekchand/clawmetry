"""Synthetic regression guard for /api/automation-analysis on v3 sessions.

Closes the Tier-1 audit checkbox for ``/api/automation-analysis`` in
#1565: the legacy ``dashboard._analyze_work_patterns`` scanner reads
``~/.openclaw/logs/moltbot-YYYY-MM-DD.log`` and journalctl, neither of
which exist on a fresh OpenClaw v3 install — so the endpoint silently
returned an empty pattern list to every user, and the suggestion
transformer fell back to its three universal recommendations only.
Same silent-zero hazard Eng L caught in cost-optimizer (PR #1576).

This file seeds DuckDB with daemon-normalised tool-call events (the
shape the OSS sync daemon writes for real OpenClaw v3 sessions — see
``clawmetry/sync.py::_parse_v3_event`` + reference_openclaw_v3_event_types.md)
and asserts:

1. An empty local store returns the legacy fallback (still works for
   pre-v3 installs that have moltbot logs / journalctl).
2. A populated store hydrates ``patterns[]`` with the same {title,
   description, frequency, confidence, priority, type, target} shape
   the legacy scanner produced, tagged ``_source: 'local_store'``.
3. Frequency thresholds match the legacy scanner (≥5 = surface, ≥10 =
   medium, ≥15 = high) so downstream suggestion transformer behaviour
   is identical.
4. Tool-name mapping covers both legacy ("bash"/"grep") and v3
   ("Bash"/"Grep") shapes — real-shape regression guard per
   ``feedback_synthetic_tests_missed_real_event_shape``.
"""

from __future__ import annotations

import importlib
import json
import time

import pytest
from flask import Flask


@pytest.fixture
def app(tmp_path, monkeypatch):
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "events.duckdb"))
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_SECS", "0.05")
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_READ", "1")

    import clawmetry.local_store as ls
    importlib.reload(ls)
    import routes.local_query as lq
    importlib.reload(lq)
    import routes.sessions as sessions_mod
    importlib.reload(sessions_mod)
    import routes.infra as infra_mod
    importlib.reload(infra_mod)

    # Issue #1538: isolate fixture from a developer's locally-running
    # daemon (otherwise ``_ls_call`` proxies into the prod DuckDB and
    # our seeded rows are invisible to the fast path).
    monkeypatch.setattr(lq, "_read_discovery", lambda: None)

    a = Flask(__name__)
    a.register_blueprint(infra_mod.bp_config)
    yield a, ls
    try:
        ls.get_store().stop(flush=True)
    except Exception:
        pass


def _drain(store):
    store._flush_now()
    for _ in range(10):
        if not store._ring:
            break
        time.sleep(0.05)


def _tool_call_row(event_id, sid, ts, tool_name):
    """A standalone ``tool.call`` row — the shape v3 emits for explicit
    tool invocations outside an assistant turn (matches what
    ``query_tool_call_invocations`` picks up via ``_TOOL_CALL_TOPLEVEL_EVENT_TYPES``)."""
    return {
        "id":           event_id,
        "node_id":      "node-test",
        "agent_type":   "openclaw",
        "agent_id":     "main",
        "session_id":   sid,
        "workspace_id": None,
        "event_type":   "tool.call",
        "ts":           ts,
        "data":         json.dumps({
            "_v3_type": "tool_call",
            "type": "tool.call",
            "name": tool_name,
        }),
    }


def test_empty_local_store_falls_through_to_legacy(app, monkeypatch):
    """When DuckDB has zero tool-call rows the helper returns None and
    the route falls back to ``_analyze_work_patterns``. Critical: this
    keeps the journalctl/moltbot scanner intact for users still on
    pre-v3 transports."""
    a, _ls = app
    # Stub the legacy path so we don't depend on the host filesystem.
    import dashboard as _d
    monkeypatch.setattr(_d, "_analyze_work_patterns", lambda: [])
    monkeypatch.setattr(_d, "_generate_automation_suggestions", lambda p: [])

    r = a.test_client().get("/api/automation-analysis")
    assert r.status_code == 200, r.get_data(as_text=True)
    body = r.get_json()
    assert body.get("patterns") == []
    assert body.get("suggestions") == []
    assert "_source" not in body, (
        f"_source must NOT be tagged when falling through to legacy; got {body!r}"
    )


def test_populated_local_store_hydrates_patterns(app, monkeypatch):
    """A v3 session with frequent tool calls must surface as
    pattern rows tagged ``_source: 'local_store'`` with the exact legacy
    schema. We seed 15× Bash (→ high), 10× Grep (→ medium), 5× Read
    (→ low). The 4-call Write tool stays below threshold and is dropped,
    matching the legacy ≥5 floor."""
    a, ls = app
    store = ls.get_store()
    sid = "sess-auto-v3"

    # Stub the legacy transformer to a no-op so the assertion stays
    # focused on the pattern shape produced by the fast path.
    import dashboard as _d
    monkeypatch.setattr(_d, "_generate_automation_suggestions", lambda p: [])

    counts = {"Bash": 15, "Grep": 10, "Read": 5, "Write": 4}
    eid = 0
    ts_base = "2026-05-17T12:00:"
    for tool, n in counts.items():
        for i in range(n):
            store.ingest(_tool_call_row(
                f"e{eid}", sid,
                f"{ts_base}{eid % 60:02d}.{eid:03d}Z",
                tool,
            ))
            eid += 1
    _drain(store)

    r = a.test_client().get("/api/automation-analysis")
    assert r.status_code == 200, r.get_data(as_text=True)
    body = r.get_json()
    assert body.get("_source") == "local_store", (
        f"_source must be local_store on populated store; got {body.get('_source')!r}"
    )
    patterns = body.get("patterns") or []
    targets = {p["target"]: p for p in patterns}
    assert "bash" in targets, f"Bash (→ bash) missing: {list(targets)}"
    assert "grep" in targets, f"Grep (→ grep) missing: {list(targets)}"
    assert "read" in targets, f"Read (→ read) missing: {list(targets)}"
    assert "write" not in targets, (
        f"Write at 4 calls is below the 5-call floor; got: {list(targets)}"
    )

    bash = targets["bash"]
    assert bash["priority"] == "high", f"15 calls = high; got {bash!r}"
    assert bash["type"] == "command"
    assert bash["frequency"] == "15 times/week"
    # Confidence is min(90, count*10) — caps at 90 by 9 calls.
    assert bash["confidence"] == 90
    assert bash["_source"] == "local_store"
    assert "Frequent" in bash["title"] and "bash" in bash["title"]

    grep = targets["grep"]
    assert grep["priority"] == "medium", f"10 calls = medium; got {grep!r}"
    assert grep["frequency"] == "10 times/week"

    read = targets["read"]
    assert read["priority"] == "low", f"5 calls = low; got {read!r}"
    assert read["confidence"] == 50

    # Sort order: high first, then medium, then low (matches the legacy
    # sort key in _analyze_work_patterns).
    priorities = [p["priority"] for p in patterns]
    assert priorities == sorted(
        priorities, key=lambda p: {"high": 0, "medium": 1, "low": 2}[p]
    ), f"pattern ordering regressed: {priorities}"


def test_assistant_tool_metas_also_count(app, monkeypatch):
    """Real OpenClaw v3 carries tool invocations inside the assistant
    turn (``model.completed`` event with ``data.toolMetas``). Verify the
    fast path picks those up too — the silent-zero failure mode caught
    on /api/plugins and /api/fallbacks in the 2026-05-15 MOAT smoke
    (issue #1385)."""
    a, ls = app
    store = ls.get_store()
    sid = "sess-auto-meta"

    import dashboard as _d
    monkeypatch.setattr(_d, "_generate_automation_suggestions", lambda p: [])

    # Seed 6 assistant turns each carrying a Bash tool_use in toolMetas.
    for i in range(6):
        store.ingest({
            "id":           f"asst-{i}",
            "node_id":      "node-test",
            "agent_type":   "openclaw",
            "agent_id":     "main",
            "session_id":   sid,
            "workspace_id": None,
            "event_type":   "model.completed",
            "ts":           f"2026-05-17T13:00:{i:02d}Z",
            "data":         json.dumps({
                "_v3_type": "message",
                "type": "model.completed",
                "completionText": "running",
                "toolMetas": [
                    {"id": f"tu_{i}", "name": "Bash",
                     "input": {"command": "ls"}},
                ],
            }),
        })
    _drain(store)

    r = a.test_client().get("/api/automation-analysis")
    body = r.get_json()
    assert body.get("_source") == "local_store"
    targets = {p["target"]: p for p in body.get("patterns") or []}
    assert "bash" in targets, (
        f"toolMetas inside model.completed dropped (silent-zero regression); "
        f"got {list(targets)}"
    )
    assert targets["bash"]["frequency"] == "6 times/week"


def test_suggestion_transformer_still_runs(app, monkeypatch):
    """The transformer is pure-Python and unchanged. Verify the route
    still wires patterns → suggestions on the fast path (otherwise the
    UI gets patterns but no actionable cron/skill upsells)."""
    a, ls = app
    store = ls.get_store()
    sid = "sess-auto-suggest"

    for i in range(7):
        store.ingest(_tool_call_row(
            f"sg-{i}", sid, f"2026-05-17T14:00:{i:02d}Z", "Bash",
        ))
    _drain(store)

    r = a.test_client().get("/api/automation-analysis")
    body = r.get_json()
    assert body.get("_source") == "local_store"
    # Universal suggestions ALWAYS land (health monitoring, log rotation,
    # backup verification) — verify the transformer chain executed.
    titles = {s["title"] for s in body.get("suggestions") or []}
    assert "Health monitoring cron" in titles, (
        f"transformer didn't run on fast path; got {titles}"
    )
