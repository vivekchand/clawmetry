"""Escalation ladders: pause, wait, then kill if still stuck.

Before this a policy fired ONE action ONCE. The ladder existed only as an
ordering of action names ("kill is stronger than pause"), never as a sequence
over time, so the shape real operations want — *pause it, tell me, give it
five minutes, then kill it if it is still stuck* — could not be expressed.

Covered here: the pure timing rules, the durable per-rung latch (including
the DuckDB PK migration), and that a ladder cannot slip any of the three
safety locks.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest  # noqa: E402

from clawmetry import policy_engine as pe  # noqa: E402


def _incident(session_id="s1"):
    return {"kind": "no_progress", "session_id": session_id,
            "runtime": "claude_code", "severity": "warning",
            "title": "agent not advancing",
            "evidence": {"total_tool_calls": 40}}


_FACTS = {"s1": {"cost_usd": 9.0, "bad_for_seconds": 600,
                 "runtime": "claude_code", "cwd": "/tmp/x", "agent_id": "main"}}

_LADDER = [{"action": "pause", "after_secs": 0},
           {"action": "alert", "after_secs": 60},
           {"action": "kill", "after_secs": 300}]


def _policy(steps=None, action="monitor", policy_id="p1"):
    p = {"policy_id": policy_id, "enabled": True, "scope_runtime": "",
         "scope_agent_id": "", "trigger_kind": "", "min_severity": "info",
         "min_repeat": 0, "min_duration_s": 0, "min_spend_usd": 0,
         "action": action}
    if steps is not None:
        p["steps"] = steps
    return p


def _state(step, at):
    return {"s1": {"p1": {"last_step": step, "last_fired_at": at}}}


# ── normalize_steps ───────────────────────────────────────────────────────
def test_a_policy_without_steps_is_a_one_rung_ladder():
    """The compatibility guarantee: every pre-ladder policy is untouched."""
    steps = pe.normalize_steps(_policy(action="kill"))
    assert steps == [{"action": "kill", "after_secs": 0}]


def test_step_zero_delay_is_forced_to_zero():
    steps = pe.normalize_steps(_policy([{"action": "pause", "after_secs": 999}]))
    assert steps[0]["after_secs"] == 0


def test_unknown_actions_are_dropped_never_coerced():
    """Coercing 'terminate' to some default would silently change what the
    rule does to someone's agent."""
    steps = pe.normalize_steps(_policy([
        {"action": "pause", "after_secs": 0},
        {"action": "terminate", "after_secs": 10},
        {"action": "kill", "after_secs": 30},
    ]))
    assert [s["action"] for s in steps] == ["pause", "kill"]


def test_a_ladder_of_only_bad_rungs_falls_back_to_the_action():
    steps = pe.normalize_steps(_policy([{"action": "nope"}], action="monitor"))
    assert steps == [{"action": "monitor", "after_secs": 0}]


def test_ladder_length_is_capped():
    steps = pe.normalize_steps(_policy(
        [{"action": "alert", "after_secs": 1}] * 40))
    assert len(steps) == pe.MAX_LADDER_STEPS


def test_absurd_delays_are_clamped():
    """A typo of 300000 for 300 would otherwise park a ladder for 3 days."""
    steps = pe.normalize_steps(_policy([
        {"action": "pause", "after_secs": 0},
        {"action": "kill", "after_secs": 999999999},
    ]))
    assert steps[1]["after_secs"] == pe.MAX_STEP_DELAY_SECS


def test_steps_stored_as_json_text_are_understood():
    """The store round-trips steps as a JSON column; both forms must behave
    identically or a policy would act differently after a restart."""
    import json
    steps = pe.normalize_steps(_policy(json.dumps(_LADDER)))
    assert [s["action"] for s in steps] == ["pause", "alert", "kill"]


# ── ladder timing ─────────────────────────────────────────────────────────
def test_first_rung_fires_immediately():
    d = pe.evaluate([_incident()], [_policy(_LADDER)], _FACTS, now=1000)[0]
    assert d["action"] == "pause" and d["step_index"] == 0
    assert d["step_count"] == 3 and d["is_final_step"] is False
    assert d["next_action"] == "alert" and d["next_after_secs"] == 60


def test_next_rung_waits_for_its_delay():
    args = ([_incident()], [_policy(_LADDER)], _FACTS)
    assert pe.evaluate(*args, ladder_state=_state(0, 1000), now=1030) == []
    assert pe.evaluate(*args, ladder_state=_state(0, 1000), now=1059) == []
    d = pe.evaluate(*args, ladder_state=_state(0, 1000), now=1061)[0]
    assert d["action"] == "alert" and d["step_index"] == 1


def test_delay_is_measured_from_the_previous_rung_not_the_incident():
    """'kill 5 minutes after the pause', not '5 minutes after it got stuck'."""
    args = ([_incident()], [_policy(_LADDER)], _FACTS)
    # Rung 1 fired late (t=5000); rung 2 is due at 5300, not at 1000+300.
    assert pe.evaluate(*args, ladder_state=_state(1, 5000), now=5299) == []
    d = pe.evaluate(*args, ladder_state=_state(1, 5000), now=5301)[0]
    assert d["action"] == "kill"


def test_final_rung_is_marked_and_the_ladder_then_stops():
    args = ([_incident()], [_policy(_LADDER)], _FACTS)
    d = pe.evaluate(*args, ladder_state=_state(1, 1000), now=9999)[0]
    assert d["action"] == "kill" and d["is_final_step"] is True
    assert d["next_action"] == ""
    # Exhausted: nothing more, however long we wait.
    assert pe.evaluate(*args, ladder_state=_state(2, 1000), now=10**9) == []


def test_a_recovered_session_stops_the_ladder():
    """'kill if STILL stuck' must mean still stuck: no incident, no rung."""
    assert pe.evaluate([], [_policy(_LADDER)], _FACTS,
                       ladder_state=_state(0, 1000), now=10**9) == []


def test_unknown_fire_time_delays_rather_than_fires():
    """The safe way to be wrong when the next rung might be a kill."""
    args = ([_incident()], [_policy(_LADDER)], _FACTS)
    state = {"s1": {"p1": {"last_step": 0, "last_fired_at": None}}}
    assert pe.evaluate(*args, ladder_state=state, now=10**9) == []


def test_reason_names_the_rung_and_what_comes_next():
    d = pe.evaluate([_incident()], [_policy(_LADDER)], _FACTS, now=1000)[0]
    assert "[step 1/3]" in d["reason"]
    assert "then alert in 1m if still matching" in d["reason"]


def test_single_action_policy_reason_is_unchanged():
    d = pe.evaluate([_incident()], [_policy(action="kill")], _FACTS, now=1000)[0]
    assert "step" not in d["reason"]
    assert d["step_count"] == 1 and d["is_final_step"] is True


def test_still_one_decision_per_session_across_ladders():
    """Two ladders on one session must not produce two signals in a tick."""
    ds = pe.evaluate([_incident()],
                     [_policy(_LADDER, policy_id="p1"),
                      _policy([{"action": "kill", "after_secs": 0}],
                              policy_id="p2")],
                     _FACTS, now=1000)
    assert len(ds) == 1
    assert ds[0]["action"] == "kill"  # strongest wins, as before


# ── durable per-rung latch, against a real DuckDB store ──────────────────
@pytest.fixture
def store(tmp_path, monkeypatch):
    """A throwaway DuckDB store.

    CLAWMETRY_LOCAL_STORE_PATH is set BEFORE the reload so the module-level
    default path is rebound to tmp_path — the store must never touch the real
    ~/.clawmetry database.
    """
    pytest.importorskip("duckdb")
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "cm.duckdb"))
    import importlib

    import clawmetry.local_store as ls
    importlib.reload(ls)
    st = ls.LocalStore()
    assert str(tmp_path) in str(getattr(ls, "DB_PATH", tmp_path)), \
        "refusing to run against the real store"
    try:
        yield st
    finally:
        try:
            st.close()
        except Exception:
            pass
        # Restore the module to the real default path. Leaving it bound to a
        # deleted tmp_path would make a later test in the same session fail
        # for a reason that has nothing to do with it.
        monkeypatch.undo()
        importlib.reload(ls)


def test_each_rung_latches_independently(store):
    store.record_policy_action("s1", "p1", action="pause", step_index=0)
    assert store.policy_already_fired("s1", "p1", 0) is True
    # The whole point: rung 1 is NOT latched by rung 0's row.
    assert store.policy_already_fired("s1", "p1", 1) is False
    store.record_policy_action("s1", "p1", action="kill", step_index=1)
    assert store.policy_already_fired("s1", "p1", 1) is True


def test_re_recording_a_rung_updates_it_rather_than_duplicating(store):
    store.record_policy_action("s1", "p1", action="pause", step_index=0,
                               result_detail="pending")
    store.record_policy_action("s1", "p1", action="pause", step_index=0,
                               result_ok=True, result_detail="paused")
    rows = [r for r in store.query_policy_actions(limit=50)
            if r["session_id"] == "s1"]
    assert len(rows) == 1
    assert rows[0]["result_detail"] == "paused" and rows[0]["result_ok"] is True


def test_ladder_state_survives_a_restart(store):
    """The reason the latch is durable: a restart must resume at the rung it
    reached, not replay a ladder that ends in kill."""
    store.record_policy_action("s1", "p1", action="pause", step_index=0)
    store.record_policy_action("s1", "p1", action="alert", step_index=1)
    state = store.query_policy_ladder_state()
    assert state["s1"]["p1"]["last_step"] == 1
    assert state["s1"]["p1"]["last_fired_at"] > 0
    # Fed back to the engine, it resumes at rung 2 rather than rung 0.
    d = pe.evaluate([_incident()], [_policy(_LADDER)], _FACTS,
                    ladder_state=state, now=state["s1"]["p1"]["last_fired_at"] + 400)[0]
    assert d["action"] == "kill" and d["step_index"] == 2


def test_ladder_state_is_epoch_seconds_not_milliseconds(store):
    """A unit mismatch here would make every delay look 1000x satisfied."""
    import time
    store.record_policy_action("s1", "p1", action="pause", step_index=0)
    fired = store.query_policy_ladder_state()["s1"]["p1"]["last_fired_at"]
    assert abs(fired - time.time()) < 60


def test_policy_round_trips_its_ladder(store):
    store.upsert_session_policy(_policy(_LADDER))
    row = [r for r in store.query_session_policies()
           if r["policy_id"] == "p1"][0]
    assert [s["action"] for s in row["steps"]] == ["pause", "alert", "kill"]
    assert row["steps"][2]["after_secs"] == 300


def test_a_plain_policy_reads_back_with_no_ladder(store):
    store.upsert_session_policy(_policy(action="kill"))
    row = [r for r in store.query_session_policies()
           if r["policy_id"] == "p1"][0]
    assert row["steps"] == []
    # …and the engine still treats it as a one-rung ladder.
    assert pe.normalize_steps(row) == [{"action": "kill", "after_secs": 0}]


def test_audit_rows_carry_the_rung(store):
    store.record_policy_action("s1", "p1", action="kill", step_index=2)
    row = [r for r in store.query_policy_actions(limit=10)
           if r["session_id"] == "s1"][0]
    assert row["step_index"] == 2


# ── the migration from the two-column latch ──────────────────────────────
def test_migration_widens_the_latch_and_keeps_existing_rows(tmp_path):
    duckdb = pytest.importorskip("duckdb")
    path = str(tmp_path / "old.duckdb")
    conn = duckdb.connect(path)
    conn.execute("""
        CREATE TABLE policy_actions (
            session_id VARCHAR NOT NULL, policy_id VARCHAR NOT NULL,
            runtime VARCHAR, action VARCHAR, kind VARCHAR, reason VARCHAR,
            evidence BLOB, enforced BOOLEAN DEFAULT FALSE,
            result_ok BOOLEAN DEFAULT FALSE, result_detail VARCHAR,
            created_at BIGINT NOT NULL,
            PRIMARY KEY (session_id, policy_id))
    """)
    conn.execute("INSERT INTO policy_actions (session_id, policy_id, action, "
                 "created_at) VALUES ('old-s', 'old-p', 'kill', 1000)")
    conn.close()

    from clawmetry.local_store import _migrate_policy_actions_ladder
    conn = duckdb.connect(path)
    _migrate_policy_actions_ladder(conn)
    cols = {r[1] for r in conn.execute("PRAGMA table_info('policy_actions')").fetchall()}
    assert "step_index" in cols
    # The historical decision is preserved, at rung 0 where it belongs.
    row = conn.execute("SELECT session_id, policy_id, step_index, action "
                       "FROM policy_actions").fetchone()
    assert row == ("old-s", "old-p", 0, "kill")
    # And rung 1 is now insertable without colliding with it.
    conn.execute("INSERT INTO policy_actions (session_id, policy_id, "
                 "step_index, action, created_at) "
                 "VALUES ('old-s', 'old-p', 1, 'kill', 2000)")
    assert conn.execute("SELECT COUNT(*) FROM policy_actions").fetchone()[0] == 2

    # Idempotent: a second pass is a no-op, not a data-losing rebuild.
    _migrate_policy_actions_ladder(conn)
    assert conn.execute("SELECT COUNT(*) FROM policy_actions").fetchone()[0] == 2
    conn.close()


@pytest.mark.parametrize('node,runtime', [('node-a', 'claude_code'), ('node-b', 'claude_code'), ('node-a', 'codex')])
def test_exact_scoped_ladders_survive_restart_without_identity_rewriting(store, node, runtime):
    """AC-GOV-SBG-002.2/.4: scoped durable rungs keep readable native IDs."""
    from clawmetry import local_store
    sid, pid = 'native-' + 's' * 160, 'policy-' + 'p' * 160
    store.record_policy_action(sid, pid, node_id=node, runtime=runtime, action='pause', step_index=0)
    store.record_policy_action(sid, pid, node_id=node, runtime=runtime, action='alert', step_index=1)
    store.stop(flush=True)
    reopened = local_store.LocalStore()
    try:
        assert reopened.policy_already_fired(sid, pid, 1, node_id=node, runtime=runtime, strict=True)
        assert not reopened.policy_already_fired(sid, pid, 2, node_id=node, runtime=runtime, strict=True)
        assert not reopened.policy_already_fired(sid, pid, 0, node_id='another', runtime=runtime, strict=True)
        state = reopened.query_policy_ladder_state(node_id=node, runtime=runtime, strict=True)
        assert state[sid][pid]['last_step'] == 1
        assert reopened.query_policy_ladder_state(node_id='another', runtime=runtime, strict=True) == {}
        row = reopened.query_policy_actions()[0]
        assert row['session_id'] == sid and row['policy_id'] == pid
        assert row['node_id'] == node and row['runtime'] == runtime
        assert row['scope_state'] == 'exact'
    finally:
        reopened.stop(flush=True)


@pytest.mark.parametrize('old_runtime', [None, 'claude_code'])
def test_scope_migration_keeps_ambiguous_history_without_replaying_or_escalating(store, old_runtime):
    """AC-GOV-SBG-002.2/.4: unknown old node scope never becomes authority."""
    from clawmetry import local_store
    # An actual pre-scope database, already using the old rung-aware schema.
    conn = store._conn
    conn.execute('DROP TABLE policy_actions')
    conn.execute('''CREATE TABLE policy_actions (
        session_id VARCHAR NOT NULL, policy_id VARCHAR NOT NULL,
        step_index INTEGER NOT NULL DEFAULT 0, runtime VARCHAR,
        action VARCHAR, kind VARCHAR, reason VARCHAR, evidence BLOB,
        enforced BOOLEAN DEFAULT FALSE, result_ok BOOLEAN DEFAULT FALSE,
        result_detail VARCHAR, created_at BIGINT NOT NULL,
        PRIMARY KEY(session_id, policy_id, step_index))''')
    conn.execute("INSERT INTO policy_actions(session_id,policy_id,step_index,runtime,action,created_at) "
                 "VALUES ('native-session','operator-policy',1,?,'pause',1000)", [old_runtime])
    conn.execute('DELETE FROM schema_version WHERE version>=19')
    store.stop(flush=True)
    migrated = local_store.LocalStore()
    try:
        row = migrated.query_policy_actions()[0]
        assert row['session_id'] == 'native-session' and row['policy_id'] == 'operator-policy'
        assert row['runtime'] == (old_runtime or '') and row['node_id'] == ''
        assert row['scope_state'] == 'legacy_unscoped'
        assert migrated.query_policy_ladder_state(node_id='node-a', runtime='claude_code', strict=True) == {}
        # Neither restarting at rung zero nor advancing to kill is justified.
        for step in (0, 1, 2):
            assert migrated.policy_already_fired('native-session', 'operator-policy', step,
                node_id='node-a', runtime='claude_code', strict=True)
        assert migrated.policy_already_fired('native-session', 'operator-policy', 0,
            node_id='node-a', runtime='codex', strict=True) is (old_runtime is None)
        # Idempotent startup preserves the historical row and its identity.
        migrated._migrate()
        assert len(migrated.query_policy_actions()) == 1
    finally:
        migrated.stop(flush=True)


def test_policy_scope_migration_is_atomic_on_copy_failure(store, monkeypatch):
    from clawmetry import local_store
    conn = store._conn
    store.record_policy_action('readable-session', 'readable-policy', runtime='claude_code', action='pause')
    conn.execute('DELETE FROM schema_version WHERE version>=19')
    real = local_store._migrate_policy_actions_scope
    def failed_copy(connection):
        # Simulate DDL/copy failure after a mutation inside the outer schema
        # transaction. The original latch must survive rollback and retry.
        connection.execute('DELETE FROM policy_actions')
        raise OSError('isolated migration copy failure')
    with monkeypatch.context() as patch:
        patch.setattr(local_store, '_migrate_policy_actions_scope', failed_copy)
        with pytest.raises(RuntimeError, match='migration failed'):
            store._migrate()
    assert store.policy_already_fired('readable-session', 'readable-policy')
    assert store._fetch('SELECT count(*) FROM schema_version WHERE version>=19', [])[0][0] == 0
    assert local_store._migrate_policy_actions_scope is real
    store._migrate()
    assert store.policy_already_fired('readable-session', 'readable-policy')


def test_policy_history_renders_readable_exact_and_legacy_scope():
    """AC-GOV-SBG-002.2/.4: audit scope stays visible, escaped and honest."""
    import shutil
    import subprocess
    from pathlib import Path
    node = shutil.which('node')
    if not node:
        pytest.skip('node required for Guard audit rendering')
    source = (Path(__file__).parents[1] / 'clawmetry/static/js/app.js').read_text()
    body = 'function loadGuardActions()' + source.split('function loadGuardActions()', 1)[1].split('\nfunction ', 1)[0]
    script = '''
      const assert = require('assert');
      const element = {innerHTML: ''};
      const document = {getElementById: () => element};
      const rows = [
        {node_id:'node-<b>', runtime:'claude_code', session_id:'native-session', created_at:1000, action:'pause'},
        {node_id:'', runtime:'', session_id:'old-readable-session', created_at:1000, action:'pause'}];
      function fetch() { return Promise.resolve({json: () => Promise.resolve({actions:rows})}); }
      function guardEsc(value) { return String(value || '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;'); }
      function guardAgo(value) { return value; }
    ''' + body + '''
      loadGuardActions();
      setImmediate(() => {
        assert(element.innerHTML.includes('node-&lt;b&gt;'));
        assert(element.innerHTML.includes('claude_code'));
        assert(element.innerHTML.includes('native-session'));
        assert(element.innerHTML.includes('Node unknown'));
        assert(element.innerHTML.includes('Runtime unknown'));
        assert(!element.innerHTML.includes('node-<b>'));
      });
    '''
    subprocess.run([node, '-e', script], check=True, capture_output=True, text=True)


def test_same_native_session_facts_and_ladders_do_not_merge_scopes(store, monkeypatch):
    """AC-GOV-SBG-002.2/.4: facts and response state belong to the same scope."""
    import json
    from clawmetry import sync
    from tests.test_guard_policy_enforcement import _policy as enforcement_policy
    sid = 'same-native-session'
    rows = [dict(session_id=sid, node_id=node, agent_type=runtime, cost_usd=cost)
            for node, runtime, cost in [('node-a', 'claude_code', 9), ('node-b', 'codex', 99)]]
    state = {'detector_first_seen': {
        json.dumps(['scope', 'node-a', 'claude_code', sid], separators=(',', ':')): 10,
        json.dumps(['scope', 'node-b', 'codex', sid], separators=(',', ':')): 95}}
    facts = sync._detector_session_facts(rows, state, 100)
    first = facts[('node-a', 'claude_code', sid)]
    second = facts[('node-b', 'codex', sid)]
    assert first['cost_usd'] == 9 and first['bad_for_seconds'] == 90
    assert second['cost_usd'] == 99 and second['bad_for_seconds'] == 5
    assert facts[sid] is second  # single-row legacy alias is the same object
    json.dumps(state)  # persisted daemon memo keeps readable JSON keys
    policy = enforcement_policy(action='monitor')
    policy['min_spend_usd'] = 50
    store.upsert_session_policy(policy)
    incidents = [dict(session_id=sid, node_id=row['node_id'], runtime=row['agent_type'],
                      kind='credential_access', severity='critical', evidence={}) for row in rows]
    monkeypatch.setattr(sync, '_guard_actuate', lambda *args: pytest.fail('unexpected actuator'))
    assert sync._apply_guard_policies(store, {}, incidents, facts, strict=True) == 1
    recorded = store.query_policy_actions()
    assert len(recorded) == 1 and recorded[0]['node_id'] == 'node-b'
    assert recorded[0]['runtime'] == 'codex' and recorded[0]['session_id'] == sid


@pytest.mark.parametrize('strict', [False, True])
def test_scoped_periodic_and_strict_paths_use_the_same_exact_latch(store, monkeypatch, strict):
    from clawmetry import sync
    from tests.test_guard_policy_enforcement import _policy as enforcement_policy
    store.upsert_session_policy(enforcement_policy(action='monitor'))
    monkeypatch.setattr(sync, '_guard_actuate', lambda *args: pytest.fail('unexpected actuator'))
    def apply(node, mode):
        incident = dict(session_id='native', node_id=node, runtime='claude_code',
                        kind='credential_access', severity='critical', evidence={})
        facts = {'native': dict(node_id=node, runtime='claude_code')}
        return sync._apply_guard_policies(store, {}, [incident], facts, strict=mode)
    assert apply('node-a', strict) == 1
    assert apply('node-a', not strict) == 0
    assert apply('node-b', not strict) == 1
    assert len(store.query_policy_actions()) == 2


def test_legacy_truncated_history_cannot_authorize_a_full_identity_replay(store):
    sid, pid = 'native-' + 's' * 160, 'policy-' + 'p' * 160
    store._conn.execute('''INSERT INTO policy_actions
        (node_id,runtime,session_id,policy_id,step_index,action,created_at)
        VALUES ('','claude_code',?,?,1,'pause',1000)''', [sid[:128], pid[:128]])
    for rung in (0, 1, 2):
        assert store.policy_already_fired(sid, pid, rung, node_id='node-a', runtime='claude_code', strict=True)
    assert store.query_policy_ladder_state(node_id='node-a', runtime='claude_code', strict=True) == {}


def test_explicit_runtime_and_native_id_make_consistent_scoped_facts(store):
    from clawmetry import sync
    from tests.test_guard_policy_enforcement import _policy as enforcement_policy
    row = dict(session_id='native-id', node_id='node-a', runtime='codex')
    facts = sync._detector_session_facts([row], {}, 100)
    assert facts[('node-a', 'codex', 'native-id')]['runtime'] == 'codex'
    store.upsert_session_policy(enforcement_policy(action='monitor'))
    incident = dict(session_id='native-id', node_id='node-a', runtime='codex',
                    kind='credential_access', severity='critical', evidence={})
    assert sync._apply_guard_policies(store, {}, [incident], facts, strict=True) == 1


@pytest.mark.parametrize('strict', [False, True])
def test_scoped_incident_cannot_act_from_another_nodes_session_alias(store, strict):
    from clawmetry import sync
    from tests.test_guard_policy_enforcement import _policy as enforcement_policy
    store.upsert_session_policy(enforcement_policy(action='monitor'))
    incident = dict(session_id='native', node_id='node-a', runtime='claude_code',
                    kind='credential_access', severity='critical', evidence={})
    facts = {'native': dict(node_id='node-b', runtime='claude_code')}
    if strict:
        with pytest.raises(ValueError, match='different scopes'):
            sync._apply_guard_policies(store, {}, [incident], facts, strict=True)
    else:
        assert sync._apply_guard_policies(store, {}, [incident], facts) == 0
    assert store.query_policy_actions() == []
