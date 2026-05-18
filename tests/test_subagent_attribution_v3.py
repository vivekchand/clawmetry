"""Regression guard for sub-agent tool-call attribution (issue #1597).

Before this fix, ``_try_local_store_session_tools`` queried
``events WHERE session_id = ?`` and never followed the
``subagents.parent_session_id`` link. A parent session that delegated
50 tool calls to a child rendered as ``tool_calls=0`` in the UI even
though the tool events sat right next to it in DuckDB under the child's
own ``session_id``.

The new ``LocalStore.query_events_with_subagents`` helper UNIONs the
parent's events with every child session's events (matched on
``subagents.parent_session_id``) and tags child rows with
``data._via_subagent_id``. ``/api/session-tools`` propagates that marker
onto each row in the response so the UI can render "via sub-agent X".

Four scenarios are asserted to nail down the class bug:

1. Parent with 0 direct tool calls + 3 sub-agent calls → rollup == 3.
2. Parent with 2 direct + 3 sub-agent → rollup == 5, sub rows tagged.
3. Sub-agent rollup from the CHILD's perspective counts only its own
   tool calls (no upward bleed).
4. Orphan tool call whose session has no ``subagents`` row does NOT
   bleed into an unrelated parent's rollup.
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

    # Issue #1538 pattern: isolate the fixture from a contributor's locally
    # running clawmetry daemon. Without this, ``_ls_call`` proxies through
    # ``~/.clawmetry/local_query.json`` and the daemon queries its OWN
    # production DuckDB instead of our tmp_path fixture — seeded rows
    # become invisible to the fast path.
    monkeypatch.setattr(lq, "_read_discovery", lambda: None)

    a = Flask(__name__)
    a.register_blueprint(sessions_mod.bp_sessions)
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


def _row(event_id, sid, event_type, ts, data, **extra):
    """Build a DuckDB events row matching the daemon's v3 projection
    (see ``clawmetry/sync.py::_parse_v3_event``)."""
    base = {
        "id":           event_id,
        "node_id":      "node-test",
        "agent_type":   "openclaw",
        "agent_id":     "main",
        "session_id":   sid,
        "workspace_id": None,
        "event_type":   event_type,
        "ts":           ts,
        "data":         json.dumps(data),
    }
    base.update(extra)
    return base


def _seed_tool_call(store, *, event_id, sid, ts, tcid, tool_name, result_text=None):
    """Seed one model.completed event whose ``toolMetas`` carries a single
    ``tool_use`` block, optionally paired with a ``tool.result`` sibling."""
    store.ingest(_row(
        event_id, sid, "model.completed", ts,
        {
            "_v3_type": "message", "type": "model.completed",
            "completionText": f"calling {tool_name}",
            "modelId":  "claude-opus-4-7",
            "provider": "anthropic",
            "toolMetas": [
                {"id": tcid, "name": tool_name, "input": {"path": "/x"}},
            ],
        },
        model="claude-opus-4-7", cost_usd=0.001,
    ))
    if result_text is not None:
        # Result lands ~1s later under the SAME session_id as the call.
        result_id = f"{event_id}-r"
        # ts + 1s — keep it lexicographically sortable.
        result_ts = ts.replace(":02Z", ":03Z").replace(":00Z", ":01Z")
        store.ingest(_row(
            result_id, sid, "tool.result", result_ts,
            {
                "_v3_type": "tool_use_result", "type": "tool.result",
                "tool_use_id": tcid,
                "output":  result_text,
                "result":  result_text,
                "is_error": False,
            },
        ))


def _api_tools(client, sid):
    r = client.get(f"/api/session-tools?session_id={sid}&include_unpaired=1")
    assert r.status_code == 200, r.get_data(as_text=True)
    return r.get_json()


# ────────────────────────────────────────────────────────────────────────────
# Scenario 1: parent has 0 direct tool calls + 3 sub-agent tool calls.
# Rollup must report 3 (was reporting 0 pre-fix).
# ────────────────────────────────────────────────────────────────────────────
def test_parent_with_only_subagent_tool_calls_rolls_up(app):
    a, ls = app
    store = ls.get_store()
    parent_sid = "parent-only-subagent"
    child_sid = "child-with-tools"

    # Parent: just a lifecycle anchor so the fast path doesn't return None.
    store.ingest(_row(
        "p1", parent_sid, "session.started", "2026-05-17T12:00:00Z",
        {"_v3_type": "session", "type": "session.started", "id": parent_sid},
    ))
    # Register the sub-agent link.
    store.ingest_subagent({
        "subagent_id":       child_sid,
        "agent_type":        "openclaw",
        "parent_session_id": parent_sid,
        "spawned_at":        "2026-05-17T12:00:01Z",
        "task":              "do all the work",
        "status":            "active",
    })
    # Three tool calls under the CHILD's session_id.
    _seed_tool_call(store, event_id="c1", sid=child_sid,
                    ts="2026-05-17T12:00:02Z", tcid="t1",
                    tool_name="Read", result_text="contents-1")
    _seed_tool_call(store, event_id="c2", sid=child_sid,
                    ts="2026-05-17T12:01:02Z", tcid="t2",
                    tool_name="Write", result_text="ok")
    _seed_tool_call(store, event_id="c3", sid=child_sid,
                    ts="2026-05-17T12:02:02Z", tcid="t3",
                    tool_name="Read", result_text="contents-3")
    _drain(store)

    body = _api_tools(a.test_client(), parent_sid)
    assert body["_source"] == "local_store"
    assert body["stats"]["total_calls"] == 3, (
        f"parent rollup must include 3 sub-agent tool calls; "
        f"got total_calls={body['stats']['total_calls']!r} (tools={body['tools']!r})"
    )
    # Every tool row should be attributed to the child.
    for rec in body["tools"]:
        assert rec.get("via_subagent_id") == child_sid, (
            f"sub-agent rollup row missing via_subagent_id={child_sid!r}: {rec!r}"
        )
    # by_tool buckets remain correct.
    by_name = {t["tool_name"]: t for t in body["by_tool"]}
    assert by_name["Read"]["calls"] == 2
    assert by_name["Write"]["calls"] == 1


# ────────────────────────────────────────────────────────────────────────────
# Scenario 2: parent has 2 direct + 3 sub-agent tool calls → 5.
# ────────────────────────────────────────────────────────────────────────────
def test_parent_rollup_mixes_direct_and_subagent_calls(app):
    a, ls = app
    store = ls.get_store()
    parent_sid = "parent-mixed"
    child_sid = "child-mixed"

    store.ingest(_row(
        "p1", parent_sid, "session.started", "2026-05-17T13:00:00Z",
        {"_v3_type": "session", "type": "session.started", "id": parent_sid},
    ))
    # Direct parent calls.
    _seed_tool_call(store, event_id="p2", sid=parent_sid,
                    ts="2026-05-17T13:00:02Z", tcid="dp1",
                    tool_name="Glob", result_text="found 3")
    _seed_tool_call(store, event_id="p3", sid=parent_sid,
                    ts="2026-05-17T13:01:02Z", tcid="dp2",
                    tool_name="Grep", result_text="2 matches")

    # Sub-agent link + 3 child calls.
    store.ingest_subagent({
        "subagent_id":       child_sid,
        "agent_type":        "openclaw",
        "parent_session_id": parent_sid,
        "spawned_at":        "2026-05-17T13:00:01Z",
        "task":              "deep dive",
        "status":            "completed",
    })
    _seed_tool_call(store, event_id="c1", sid=child_sid,
                    ts="2026-05-17T13:02:02Z", tcid="t1",
                    tool_name="Read", result_text="x")
    _seed_tool_call(store, event_id="c2", sid=child_sid,
                    ts="2026-05-17T13:03:02Z", tcid="t2",
                    tool_name="Read", result_text="y")
    _seed_tool_call(store, event_id="c3", sid=child_sid,
                    ts="2026-05-17T13:04:02Z", tcid="t3",
                    tool_name="Bash", result_text="exit 0")
    _drain(store)

    body = _api_tools(a.test_client(), parent_sid)
    assert body["_source"] == "local_store"
    assert body["stats"]["total_calls"] == 5, (
        f"parent rollup must sum direct (2) + sub-agent (3) = 5; "
        f"got {body['stats']['total_calls']!r}"
    )
    by_attribution = {}
    for rec in body["tools"]:
        key = rec.get("via_subagent_id") or "_direct"
        by_attribution.setdefault(key, []).append(rec["tool_name"])
    assert sorted(by_attribution.get("_direct", [])) == ["Glob", "Grep"], (
        f"expected 2 direct calls (Glob, Grep); got {by_attribution.get('_direct')!r}"
    )
    assert sorted(by_attribution.get(child_sid, [])) == ["Bash", "Read", "Read"], (
        f"expected 3 sub-agent calls; got {by_attribution.get(child_sid)!r}"
    )


# ────────────────────────────────────────────────────────────────────────────
# Scenario 3: from the CHILD's perspective, the rollup contains the child's
# own tool calls only — not its parent's. The helper must be one-directional
# (parent → children), never children → parent.
# ────────────────────────────────────────────────────────────────────────────
def test_child_view_does_not_bleed_parent_tool_calls(app):
    a, ls = app
    store = ls.get_store()
    parent_sid = "parent-direction-test"
    child_sid = "child-direction-test"

    # Parent: 4 direct tool calls of its own.
    store.ingest(_row(
        "p1", parent_sid, "session.started", "2026-05-17T14:00:00Z",
        {"_v3_type": "session", "type": "session.started", "id": parent_sid},
    ))
    for i in range(4):
        _seed_tool_call(store, event_id=f"p{i+2}", sid=parent_sid,
                        ts=f"2026-05-17T14:0{i}:02Z", tcid=f"pt{i}",
                        tool_name="Read", result_text="ok")

    # Child: 1 tool call, registered as a sub-agent of parent.
    store.ingest_subagent({
        "subagent_id":       child_sid,
        "agent_type":        "openclaw",
        "parent_session_id": parent_sid,
        "spawned_at":        "2026-05-17T14:05:00Z",
        "status":            "active",
    })
    store.ingest(_row(
        "c0", child_sid, "session.started", "2026-05-17T14:05:00Z",
        {"_v3_type": "session", "type": "session.started", "id": child_sid},
    ))
    _seed_tool_call(store, event_id="c1", sid=child_sid,
                    ts="2026-05-17T14:05:02Z", tcid="ct1",
                    tool_name="Write", result_text="done")
    _drain(store)

    # Hitting the CHILD's session_id must return only the 1 tool — not 5.
    body = _api_tools(a.test_client(), child_sid)
    assert body["_source"] == "local_store"
    assert body["stats"]["total_calls"] == 1, (
        f"child view must NOT include parent's 4 tool calls; "
        f"got total_calls={body['stats']['total_calls']!r}"
    )
    assert body["tools"][0]["tool_name"] == "Write"
    assert body["tools"][0].get("via_subagent_id") in ("", None)


# ────────────────────────────────────────────────────────────────────────────
# Scenario 4: an orphan tool call (its session has no row in the subagents
# table) must NOT bleed into an unrelated parent's rollup.
# ────────────────────────────────────────────────────────────────────────────
def test_orphan_tool_call_does_not_bleed_into_unrelated_parent(app):
    a, ls = app
    store = ls.get_store()
    parent_sid = "parent-isolated"
    orphan_sid = "session-no-parent-link"

    # Parent: 1 direct tool call.
    store.ingest(_row(
        "p1", parent_sid, "session.started", "2026-05-17T15:00:00Z",
        {"_v3_type": "session", "type": "session.started", "id": parent_sid},
    ))
    _seed_tool_call(store, event_id="p2", sid=parent_sid,
                    ts="2026-05-17T15:00:02Z", tcid="pt1",
                    tool_name="Read", result_text="parent-data")

    # Orphan session with its own tool — NO ingest_subagent call, so no link.
    store.ingest(_row(
        "o1", orphan_sid, "session.started", "2026-05-17T15:00:10Z",
        {"_v3_type": "session", "type": "session.started", "id": orphan_sid},
    ))
    _seed_tool_call(store, event_id="o2", sid=orphan_sid,
                    ts="2026-05-17T15:00:12Z", tcid="ot1",
                    tool_name="Bash", result_text="exit 0")
    _drain(store)

    body = _api_tools(a.test_client(), parent_sid)
    assert body["_source"] == "local_store"
    assert body["stats"]["total_calls"] == 1, (
        f"parent rollup must not include orphan tool calls; "
        f"got total_calls={body['stats']['total_calls']!r}, tools={body['tools']!r}"
    )
    assert body["tools"][0]["tool_name"] == "Read"
    assert body["tools"][0].get("via_subagent_id") in ("", None)
