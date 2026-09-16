"""The visible switch changes real detection, not just the UI.

AC-GUX-001.1 -- catalogue matches the registry and every declared family.
AC-GUX-001.2 -- unknown preferences remain unknown, not on.
AC-GUX-001.3 -- unavailable node state never claims enabled protection.
AC-GUX-002.1 -- session, workspace, fleet and legacy paths skip disabled checks.
AC-GUX-002.2 -- actual settings survive database close/reopen.
AC-GUX-002.3 -- failed writes and invalid remote seals cannot claim success.
AC-GUX-002.4 -- administrator override wins over the configured preference.
AC-GUX-003.1 -- settings and activity are separate live template panels.
AC-GUX-003.2 -- process control confirmation dialog remains in the rendered page.
AC-GUX-003.3 -- related history/settings hooks remain addressable.
AC-GUX-003.4 -- catalogue declares its node-wide scope.
"""
import time
from pathlib import Path

import pytest
from flask import Flask

from clawmetry import detectors, guard_checks, repo_scan, sync
from routes import guard


@pytest.fixture
def server():
    """Unit and store integration tests own their Flask client, never a live node."""
    yield None


@pytest.fixture
def local_store():
    # Other store integration tests replace this module in sys.modules. Resolve
    # it at test time, just as the daemon does, so both use the same instance.
    from clawmetry import local_store as current_store
    return current_store


@pytest.fixture
def store(tmp_path, monkeypatch, local_store):
    monkeypatch.setattr(local_store, 'DB_PATH', tmp_path / 'guard.duckdb')
    monkeypatch.setattr(local_store, '_daemon_registered', lambda: False)
    monkeypatch.setattr(local_store, '_writer_owner', True)
    s = local_store.LocalStore()
    yield s
    s.stop()


@pytest.fixture
def client(store, monkeypatch):
    monkeypatch.setattr(guard, '_ls_call', lambda name, **kw: getattr(store, name)(**kw))
    monkeypatch.setattr(guard, '_ls_write', lambda name, **kw: getattr(store, name)(**kw))
    app = Flask(__name__)
    app.register_blueprint(guard.bp_guard)
    return app.test_client()


def test_catalogue_matches_registry_and_declares_every_check():
    # AC-GUX-001.1: a new detector cannot silently disappear from the catalogue.
    assert set(guard_checks.DESCRIPTIONS) == set(detectors.ALL_INCIDENT_KINDS)
    data = guard_checks.catalogue({})
    assert {c['kind'] for c in data['checks']} == set(detectors.ALL_INCIDENT_KINDS)
    assert {c['family'] for c in data['checks']} == {f['id'] for f in data['families']}
    assert data['total'] == len(detectors.ALL_INCIDENT_KINDS)
    assert not data['recent_pass']


def test_unknown_state_is_not_reported_as_enabled():
    # AC-GUX-001.2
    # AC-GUX-001.3
    data = guard_checks.catalogue()
    assert not data['available']
    assert all(c['state'] == 'unknown' and c['effective_enabled'] is None for c in data['checks'])
    data = guard_checks.catalogue({guard_checks.PREFIX + 'stuck_loop': 'bad'})
    assert data['checks'][0]['state'] == 'unknown'
    assert guard_checks.disabled_kinds({guard_checks.PREFIX + 'stuck_loop': 'bad'}) == set()


def test_engine_override_wins_and_scope_is_node_wide():
    # AC-GUX-002.4
    # AC-GUX-003.4
    data = guard_checks.catalogue({}, environ={'CLAWMETRY_DETECTORS': '0'})
    assert not data['engine_enabled'] and data['scope'] == 'node'
    assert all(c['state'] == 'overridden' for c in data['checks'])


def test_toggle_round_trips_and_survives_reopen(client, store, local_store):
    # AC-GUX-002.1
    # AC-GUX-002.2
    response = client.post('/api/guard/checks/stuck_loop', json={'enabled': False})
    assert response.status_code == 200 and response.json['applied']
    assert client.get('/api/guard/checks').json['checks'][0]['state'] == 'off'
    store.stop()
    reopened = local_store.LocalStore()
    try:
        assert reopened.query_guard_checks()['checks'][0]['state'] == 'off'
    finally:
        reopened.stop()


@pytest.mark.parametrize('body', [{'enabled': 'false'}, {'enabled': 0}, {}, []])
def test_malformed_switch_is_rejected(client, body):
    assert client.post('/api/guard/checks/stuck_loop', json=body).status_code == 400


def test_unknown_check_and_cross_site_write_are_rejected(client):
    assert client.post('/api/guard/checks/no_such_check', json={'enabled': False}).status_code == 400
    assert client.post('/api/guard/checks/stuck_loop', json={'enabled': False},
                       headers={'Origin': 'https://unrelated.example'}).status_code == 403


def test_validation_failure_does_not_expose_exception_details(client, monkeypatch):
    def invalid(*args):
        raise ValueError('private implementation detail')

    monkeypatch.setattr(guard_checks, 'validate', invalid)
    response = client.post('/api/guard/checks/stuck_loop', json={'enabled': False})
    assert response.status_code == 400
    assert response.json == {'ok': False, 'message': 'Choose a known check and turn it on or off.'}


def test_failed_write_does_not_claim_success(client, monkeypatch):
    # AC-GUX-002.3
    monkeypatch.setattr(guard, '_ls_write', lambda *a, **k: None)
    response = client.post('/api/guard/checks/stuck_loop', json={'enabled': False})
    assert response.status_code == 503 and not response.json['ok']


def test_older_remote_retry_cannot_undo_newer_choice(store):
    now = int(time.time() * 1000)
    store.set_guard_check('stuck_loop', False, now - 1000)
    store.set_guard_check('stuck_loop', True, now)
    store.set_guard_check('stuck_loop', False, now - 1000)
    assert store.query_guard_checks()['checks'][0]['state'] == 'on'


def test_session_check_is_not_called_when_disabled(monkeypatch):
    calls = []
    original = detectors.stuck_loop
    def stuck_loop(*a, **k):
        calls.append(1)
        return original(*a, **k)
    monkeypatch.setattr(detectors, '_ALL_DETECTORS', (stuck_loop,))
    detectors.run_all([], 'codex:x', disabled={'stuck_loop'})
    assert calls == []
    detectors.run_all([], 'codex:x')
    assert calls == [1]


def test_workspace_disable_invalidates_cache_and_skips_scan(tmp_path, monkeypatch):
    calls = []
    def scan(*a):
        calls.append(1)
        return [{'kind': 'repo_config_exec'}]
    monkeypatch.setattr(repo_scan, 'scan_git_config', scan)
    state = {}
    a = (state, str(tmp_path), 'codex:x', 'codex', time.time())
    assert sync._workspace_incidents(*a)
    assert sync._workspace_incidents(*a, disabled={'repo_config_exec'}) == []
    assert len(calls) == 1
    assert sync._workspace_incidents(*a)
    assert len(calls) == 2


def test_legacy_stuck_path_obeys_same_switch(store, monkeypatch):
    store.set_guard_check('stuck_loop', False)
    monkeypatch.setattr(sync, '_detect_stuck_sessions', lambda s: pytest.fail('disabled check ran'))
    monkeypatch.setattr(sync, '_refresh_attention_cache', lambda s: None)
    assert sync._emit_stuck_signals(store, {}) == 0


def test_fleet_switch_skips_detection_and_dependent_policies(store, monkeypatch):
    store.set_guard_check('coordinated_action', False)
    monkeypatch.setattr(sync, '_candidate_active_sessions', lambda s: [{'session_id': 'codex:x'}])
    monkeypatch.setattr(sync, '_detector_session_facts', lambda *a, **kw: {})
    monkeypatch.setattr(sync, '_record_guard_observation', lambda *a, **kw: None)
    monkeypatch.setattr(sync, '_workspace_incidents', lambda *a, **kw: [])
    monkeypatch.setattr(sync, '_emit_fleet_incidents', lambda *a: pytest.fail('disabled fleet check ran'))
    monkeypatch.setattr(sync, '_apply_guard_policies', lambda *a: pytest.fail('policy received a disabled finding'))
    assert sync._emit_detector_incidents(store, {}) == 0


def test_browser_switch_waits_for_ack_and_hidden_views_do_not_fetch():
    """Exercise the shipped script's async flow with an isolated DOM/transport.

    AC-GUX-002.3 -- queued writes retain confirmed state and show pending.
    AC-GUX-003.4 -- entering Checks never loads activity, policies or approvals.
    """
    import json
    import shutil
    import subprocess
    if not shutil.which('node'):
        pytest.skip('node unavailable')
    script = (Path(__file__).resolve().parents[1] / 'clawmetry/static/js/guard-checks.js').read_text()
    harness = r'''
      global.window = global;
      const elements = {}, events = {}, hits = [];
      global.document = {getElementById(id) {return elements[id] ||= {innerHTML:'',textContent:''};},
        querySelectorAll() {return [];}, addEventListener(n,f) {events[n]=f;}};
      global.guardEsc = s => String(s); global.guardAgo = () => 'just now';
      global.sessionStorage = {data:{},getItem(k){return this.data[k]||null;},setItem(k,v){this.data[k]=v;}};
      global.confirm = () => true;
      for (const name of ['loadGuardSessions','guardLoadApprovalSummary','loadGuardActions',
          'loadGuardSelfReports','loadGuardPolicies','loadGuardNondeterminism']) global[name]=()=>hits.push(name);
      let response = {ok:true,pending:true};
      global.fetch = async (url,opts) => {hits.push(url); return {ok:true,json:async()=>opts ? response : DATA};};
      const settle = () => new Promise(r=>setImmediate(r));
      async function click() {
        events.click({target:{closest:s=>s==='[data-check]' ? {dataset:{check:'stuck_loop'},disabled:false} : null}});
        await settle();
      }
    '''.replace('DATA', json.dumps(guard_checks.catalogue({})))
    exercise = r'''
      (async()=>{
        guardShowView('checks'); await settle();
        if(hits.length!==1 || hits[0]!=='/api/guard/checks') throw Error('hidden view fetched');
        await click();
        let list=elements['guard-check-list'].innerHTML;
        if(!list.includes('Awaiting node') || !list.includes('aria-checked="true" data-check="stuck_loop" disabled')) throw Error('queued write claimed saved');
        if(!elements['guard-check-message'].textContent.includes('not confirmed')) throw Error('missing pending message');
        RELOAD_SCRIPT
        guardShowView('checks'); await settle();
        if(!elements['guard-check-list'].innerHTML.includes('Awaiting node')) throw Error('reload lost pending change');
        const before=hits.length; await click();
        if(hits.length!==before) throw Error('pending change could be queued twice');
      })().catch(e=>{console.error(e);process.exitCode=1;});
    '''
    exercise = exercise.replace('RELOAD_SCRIPT', '(0,eval)(' + json.dumps(script) + ');')
    result = subprocess.run(['node', '-e', harness + script + exercise], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr


def test_remote_change_requires_valid_seal_and_returns_confirmation(store, monkeypatch, local_store):
    monkeypatch.setattr(local_store, 'get_store', lambda *a, **kw: store)
    results = []
    monkeypatch.setattr(sync, '_post_process_control_result', lambda c, a, r: results.append(r))
    key = sync.generate_encryption_key()
    config = {'encryption_key': key}
    body = {'kind': 'stuck_loop', 'enabled': False}
    action = {'type': 'guard_check_update', 'sealed': sync.encrypt_payload(body, key), 'created_at': time.time()}
    sync._dispatch_pending_action(config, action)
    assert results[-1]['applied'] and results[-1]['enabled'] is False
    action['sealed'] = 'invalid'
    sync._dispatch_pending_action(config, action)
    assert not results[-1]['applied']
    assert store.get_node_setting(guard_checks.PREFIX + 'stuck_loop') == 'false'


def test_guard_views_hide_settings_and_keep_controls():
    # AC-GUX-003.1
    # AC-GUX-003.2
    # AC-GUX-003.3: all existing control hooks remain in live templates.
    from jinja2 import Environment, FileSystemLoader
    root = Path(__file__).resolve().parents[1]
    env = Environment(loader=FileSystemLoader(str(root / 'clawmetry/templates')), autoescape=True)
    html = env.get_template('tabs/guard.html').render()
    assert 'data-guard-panel="checks"' in html
    assert 'data-guard-panel="settings" hidden' in html
    assert 'id="guard-control-modal"' in html
    assert 'id="guard-sessions-body"' in html
    assert 'id="guard-actions-body"' in html


def test_alert_review_groups_repeats_without_combining_sessions_or_resolution():
    import shutil
    import subprocess
    if not shutil.which('node'):
        pytest.skip('node unavailable')
    js = (Path(__file__).resolve().parents[1] / 'clawmetry/static/js/alerts.js').read_text()
    renderer = js[js.index('  function renderHistory()'):js.index('  // Always-on monitors —')]
    harness = r'''
      const elements = {'alerts-history-list':{},'guard-alert-search':{value:''},'guard-alert-state':{value:'all'}};
      const document={getElementById:id=>elements[id]}, ALERTS_HISTORY_MAX_AGE_MS=259200000, ALERT_TYPE_HINTS={};
      const _alertsTsMs=v=>v, formatTimeAgo=v=>String(v), escape=s=>String(s).replace(/</g,'&lt;');
      const now=Date.now();
      const a={alert_id:'a',fired_at:now,payload:{name:'tool_failure',session_id:'codex:one',message:'<unsafe>'}};
      const alertsState={history:[a,{...a,alert_id:'b'},{...a,fired_at:now-1000},
        {...a,resolved_at:now},{...a,payload:{...a.payload,session_id:'codex:two'}}]};
    '''
    exercise = r'''
      renderHistory(); let html=elements['alerts-history-list'].innerHTML;
      if((html.match(/class="alerts-hist-row"/g)||[]).length!==4 || !html.includes('× 2')) throw Error('group boundaries lost');
      if(html.includes('<unsafe>') || !html.includes('&lt;unsafe>')) throw Error('unsafe evidence');
      elements['guard-alert-state'].value='resolved'; renderHistory();
      if((elements['alerts-history-list'].innerHTML.match(/class="alerts-hist-row"/g)||[]).length!==1) throw Error('resolution filter failed');
      elements['guard-alert-search'].value='no such alert'; renderHistory();
      if(!elements['alerts-history-list'].innerHTML.includes('No recent alerts match')) throw Error('missing empty state');
      elements['guard-alert-search'].value=''; elements['guard-alert-state'].value='all';
      alertsState.history=[{...a,payload:{name:'daily_spend',actual_value:42,threshold_unit:'USD'}}];
      renderHistory();
      if(!elements['alerts-history-list'].innerHTML.includes('Observed: 42 USD')) throw Error('observed value lost');
    '''
    result = subprocess.run(['node', '-e', harness + renderer + exercise], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
