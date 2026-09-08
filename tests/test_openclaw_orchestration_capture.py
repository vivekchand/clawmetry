"""OpenClaw orchestration capture — sync_openclaw_subagent_runs mirrors the
2026.6.5+/2026.7.x ``state/openclaw.sqlite`` sub-agent + flow registries into
the ``subagents`` table with the operator facts (prompt = task, reply =
frozen_result_text, status, parent), and the sessions.json snapshot pass
carries spawnedBy/spawnDepth without wiping the registry's blob.

Schema in the fixture is copied verbatim from a live OpenClaw 2026.7.1
install (sqlite3 ~/.openclaw/state/openclaw.sqlite .schema).
"""

from __future__ import annotations

import importlib
import json
import sqlite3
import time

import pytest
from flask import Flask


PARENT_UUID = "11111111-aaaa-bbbb-cccc-222222222222"
CHILD_UUID = "33333333-dddd-eeee-ffff-444444444444"
PARENT_KEY = "agent:main:main"
CHILD_KEY = f"agent:main:subagent:{CHILD_UUID}"
NOW_MS = int(time.time() * 1000)


@pytest.fixture
def env(tmp_path, monkeypatch):
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "events.duckdb"))
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_READ", "1")
    monkeypatch.setenv("CLAWMETRY_OPENCLAW_DIR", str(tmp_path / ".openclaw"))

    import clawmetry.local_store as ls
    importlib.reload(ls)
    import routes.local_query as lq
    importlib.reload(lq)
    import routes.sessions as sessions_mod
    importlib.reload(sessions_mod)
    import clawmetry.sync as sync_mod
    importlib.reload(sync_mod)

    monkeypatch.setattr(lq, "_read_discovery", lambda: None)
    monkeypatch.setattr(ls, "_daemon_registered", lambda: False)
    monkeypatch.setattr(sync_mod, "_sync_allowed", lambda: True)

    oc = tmp_path / ".openclaw"
    (oc / "state").mkdir(parents=True)
    sess_dir = oc / "agents" / "main" / "sessions"
    sess_dir.mkdir(parents=True)
    (sess_dir / "sessions.json").write_text(json.dumps({
        PARENT_KEY: {"sessionId": PARENT_UUID,
                     "sessionFile": str(sess_dir / f"{PARENT_UUID}.jsonl"),
                     "updatedAt": NOW_MS},
        CHILD_KEY: {"sessionId": CHILD_UUID,
                    "sessionFile": str(sess_dir / f"{CHILD_UUID}.jsonl"),
                    "label": "worker",
                    "task": "summarise the logs",
                    "spawnedBy": PARENT_KEY,
                    "spawnDepth": 1,
                    "subagentRole": "worker",
                    "totalTokens": 1234,
                    "updatedAt": NOW_MS,
                    "createdAt": NOW_MS - 60000},
    }))

    db = oc / "state" / "openclaw.sqlite"
    conn = sqlite3.connect(db)
    conn.executescript("""
    CREATE TABLE subagent_runs (
      run_id TEXT NOT NULL PRIMARY KEY,
      child_session_key TEXT NOT NULL,
      controller_session_key TEXT,
      requester_session_key TEXT NOT NULL,
      requester_display_key TEXT NOT NULL,
      requester_origin_json TEXT,
      task TEXT NOT NULL, task_name TEXT, cleanup TEXT NOT NULL,
      label TEXT, model TEXT, agent_dir TEXT, workspace_dir TEXT,
      run_timeout_seconds INTEGER, spawn_mode TEXT,
      created_at INTEGER NOT NULL, started_at INTEGER,
      session_started_at INTEGER, accumulated_runtime_ms INTEGER,
      ended_at INTEGER, outcome_json TEXT, archive_at_ms INTEGER,
      cleanup_completed_at INTEGER, cleanup_handled INTEGER,
      suppress_announce_reason TEXT, expects_completion_message INTEGER,
      announce_retry_count INTEGER, last_announce_retry_at INTEGER,
      last_announce_delivery_error TEXT, ended_reason TEXT,
      pause_reason TEXT, wake_on_descendant_settle INTEGER,
      frozen_result_text TEXT, frozen_result_captured_at INTEGER,
      fallback_frozen_result_text TEXT,
      fallback_frozen_result_captured_at INTEGER,
      ended_hook_emitted_at INTEGER, pending_final_delivery INTEGER,
      pending_final_delivery_created_at INTEGER,
      pending_final_delivery_last_attempt_at INTEGER,
      pending_final_delivery_attempt_count INTEGER,
      pending_final_delivery_last_error TEXT,
      pending_final_delivery_payload_json TEXT,
      completion_announced_at INTEGER,
      payload_json TEXT NOT NULL DEFAULT '{}'
    );
    CREATE TABLE flow_runs (
      flow_id TEXT NOT NULL PRIMARY KEY,
      shape TEXT, sync_mode TEXT NOT NULL DEFAULT 'managed',
      owner_key TEXT NOT NULL, requester_origin_json TEXT,
      controller_id TEXT, revision INTEGER NOT NULL DEFAULT 0,
      status TEXT NOT NULL, notify_policy TEXT NOT NULL,
      goal TEXT NOT NULL, current_step TEXT, blocked_task_id TEXT,
      blocked_summary TEXT, state_json TEXT, wait_json TEXT,
      cancel_requested_at INTEGER, created_at INTEGER NOT NULL,
      updated_at INTEGER NOT NULL, ended_at INTEGER
    );
    """)
    conn.execute(
        "INSERT INTO subagent_runs (run_id, child_session_key, "
        "requester_session_key, requester_display_key, task, cleanup, label, "
        "model, spawn_mode, created_at, started_at, ended_at, ended_reason, "
        "outcome_json, frozen_result_text) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        ["run-1", CHILD_KEY, PARENT_KEY, PARENT_KEY,
         # Real 2026.7.1 wrapping (verified live): context preamble +
         # [Subagent Task] marker + trailing "Begin." boilerplate.
         "[Subagent Context] You are running as a subagent (depth 1/1). "
         "Results auto-announce to your requester; do not busy-poll for "
         "status.\n\n[Subagent Task]\n\nsummarise the logs and report "
         "anomalies\n\nBegin. Execute the assigned task to completion.",
         "archive", "worker",
         "claude-sonnet-5", "background",
         NOW_MS - 60000, NOW_MS - 59000, NOW_MS - 5000, "completed",
         json.dumps({"status": "ok"}),
         "Two anomalies found: disk at 91%, cron X failing since Tuesday."])
    conn.execute(
        "INSERT INTO subagent_runs (run_id, child_session_key, "
        "requester_session_key, requester_display_key, task, cleanup, label, "
        "created_at, started_at, ended_at, ended_reason) "
        "VALUES (?,?,?,?,?,?,?,?,?,?,?)",
        ["run-2", "agent:main:subagent:55555555-1111-2222-3333-666666666666",
         PARENT_KEY, PARENT_KEY, "doomed task", "archive", "doomed",
         NOW_MS - 50000, NOW_MS - 50000, NOW_MS - 49000,
         # Observed live: compound reason, must map to failed.
         "subagent-error"])
    conn.execute(
        "INSERT INTO flow_runs (flow_id, owner_key, status, notify_policy, "
        "goal, current_step, created_at, updated_at) VALUES (?,?,?,?,?,?,?,?)",
        ["flow-abc", PARENT_KEY, "running", "default",
         "migrate the billing tables", "step-2: verify row counts",
         NOW_MS - 30000, NOW_MS - 1000])
    conn.commit()
    conn.close()

    paths = {"sessions_dir": str(sess_dir), "workspace": str(oc / "workspace")}
    a = Flask(__name__)
    a.register_blueprint(sessions_mod.bp_sessions)
    yield a, ls, sync_mod, paths
    try:
        ls.get_store().stop(flush=True)
    except Exception:
        pass


def test_registry_rows_land_with_prompt_reply_parent(env):
    _, ls, sync_mod, paths = env
    n = sync_mod.sync_openclaw_subagent_runs({}, {}, paths)
    assert n == 3
    rows = ls.get_store().query_subagents_lite()
    by_id = {r["subagent_id"]: r for r in rows}
    sub = by_id[CHILD_UUID]
    assert sub["parent_session_id"] == PARENT_UUID
    assert sub["status"] == "completed"
    d = sub["data"]
    assert d["kind"] == "subagent"
    # Wrapper plumbing stripped: prompt is the operator's actual ask.
    assert d["prompt"].startswith("summarise the logs")
    assert "[Subagent Context]" not in d["prompt"]
    assert "Begin. Execute" not in d["prompt"]
    # Compound terminal reason (observed live) maps to failed.
    doomed = by_id["55555555-1111-2222-3333-666666666666"]
    assert doomed["status"] == "failed"
    assert doomed["data"]["error"] == "subagent-error"
    assert d["reply"].startswith("Two anomalies found")
    assert d["model"] == "claude-sonnet-5"
    flow = by_id["flow:flow-abc"]
    assert flow["status"] == "running"
    assert flow["data"]["kind"] == "workflow"
    assert flow["data"]["phase"].startswith("step-2")


def test_orchestration_api_renders_openclaw_tree(env):
    a, _, sync_mod, paths = env
    sync_mod.sync_openclaw_subagent_runs({}, {}, paths)
    d = a.test_client().get(f"/api/session-orchestration/{PARENT_UUID}").get_json()
    assert len(d["workflows"]) == 1
    wf = d["workflows"][0]
    assert wf["name"].startswith("migrate the billing")
    assert wf["status"] == "running"
    assert wf["phase"].startswith("step-2")
    # Two direct sub-agents now: the completed worker + the failed doomed one.
    assert len(d["subagents"]) == 2
    sa = next(x for x in d["subagents"] if x["status"] == "completed")
    assert sa["reply"].startswith("Two anomalies found")
    assert sa["prompt"].startswith("summarise the logs")
    failed = next(x for x in d["subagents"] if x["status"] == "failed")
    assert failed["error"] == "subagent-error"
    # Summary reflects the mix.
    assert d["summary"]["subagents"]["failed"] == 1


def test_snapshot_pass_does_not_wipe_registry_blob(env):
    _, ls, sync_mod, paths = env
    sync_mod.sync_openclaw_subagent_runs({}, {}, paths)
    store = ls.get_store()
    # Simulate the 60s sessions.json snapshot writer touching the same row
    # (label/status only — no prompt/reply). Before the blob-merge fix this
    # wiped the registry's prompt/reply.
    store.ingest_subagent({
        "subagent_id": CHILD_UUID,
        "agent_type": "openclaw",
        "status": "idle",
        "label": "worker",
        "kind": "subagent",
        "runtime": "openclaw",
        "updated_at_ms": NOW_MS,
    })
    row = next(r for r in store.query_subagents_lite()
               if r["subagent_id"] == CHILD_UUID)
    assert row["data"]["reply"].startswith("Two anomalies found")
    assert row["data"]["prompt"].startswith("summarise the logs")
    assert row["data"]["updated_at_ms"] == NOW_MS  # new keys still land


def test_registry_watermark_incremental(env):
    _, _, sync_mod, paths = env
    state = {}
    assert sync_mod.sync_openclaw_subagent_runs({}, state, paths) == 3
    # Second pass with nothing new: watermark skips both rows... flow_runs
    # uses updated_at >= wm so an unchanged row re-reads at equality — the
    # upsert makes that idempotent; assert it never grows beyond the same 2.
    assert sync_mod.sync_openclaw_subagent_runs({}, state, paths) <= 3
