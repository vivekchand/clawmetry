"""Hosted surfaces use the encrypted node transport and reject stale output.

AC-ASSIST-007.5 -- node/account/key changes clear decrypted content before render.
AC-ASSIST-007.7 -- missing or incorrect keys offer unlock and a usable retry.

Real encryption and exact owner authorization are also exercised in the cloud
relay suite; these browser tests check the shared UI after that boundary.
"""
from pathlib import Path
import shutil
import subprocess

import pytest

ROOT = Path(__file__).parents[1]


def test_hosted_assistant_without_relay_never_calls_plaintext_cloud_endpoints():
    if not shutil.which('node'):
        pytest.skip('Node.js is not installed')
    script = r'''
const fs = require('fs'), vm = require('vm'), assert = require('assert');
global.window = global;
window.CLOUD_MODE = true;
const ids = ['page-assistant','cm-assistant-thread','cm-assistant-input',
  'cm-assistant-send','cm-assistant-status-label','cm-assistant-status-message',
  'cm-assistant-setup-title','cm-assistant-setup-description',
  'cm-assistant-data-notice','cm-assistant-history-list','cm-assistant-managed-note',
  'cm-assistant-voice','cm-assistant-new-chat',
  'custom-dashboard-section','custom-dashboard-grid'];
const nodes = Object.fromEntries(ids.map(id => [id, {
  textContent:'', style:{}, childElementCount:1, disabled:false,
  addEventListener(){}, setAttribute(){}, querySelector(){return null},
  classList:{toggle(){}}
}]));
global.document = {readyState:'loading', getElementById:id=>nodes[id]||null,
  addEventListener(){}};
let hits = [];
global.fetch = (url) => {hits.push(url); throw Error('A local endpoint reached the cloud');};
for (const file of ['assistant.js','custom-dashboard.js'])
  vm.runInThisContext(fs.readFileSync('clawmetry/static/js/'+file,'utf8'));
(async()=>{
  loadAssistantPage();
  await loadCustomDashboardPanels();
  assert.deepEqual(hits, []);
  assert.equal(nodes['cm-assistant-send'].disabled,true);
  assert.equal(nodes['cm-assistant-input'].disabled,true);
  assert.equal(nodes['cm-assistant-voice'].disabled,true);
  assert.equal(nodes['cm-assistant-managed-note'].hidden,true);
  for (const id of ['cm-assistant-status-message','cm-assistant-history-list',
    'custom-dashboard-grid']) {
    assert.match(nodes[id].textContent,/computer/);
    assert.doesNotMatch(nodes[id].textContent,/Loading|Scanning|No data/);
  }
})().catch(e=>{console.error(e);process.exitCode=1;});
'''
    result = subprocess.run(['node', '-e', script], cwd=ROOT, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr


def _cloud_page_script():
    from tests.test_assistant_frontend import _PAGE_STREAM_JS

    return _PAGE_STREAM_JS.replace('context.window = context;', r'''
context.window = context;
context.CLOUD_MODE = true;
let identity = 'account-node-key-A';
const scopeListeners = [];
context._cmAssistantRelay = {version:1, identity: () => identity};
context.addEventListener = (name, fn) => {
  if (name === 'cm-assistant-scope-changed') scopeListeners.push(fn);
};
function changeScope(next) { identity = next; scopeListeners.forEach(fn => fn()); }
main.appendChild(add('cm-assistant-recovery', 'div'));
''')


def test_cloud_assistant_streams_before_done_and_saves_through_the_shared_panel_api():
    from tests.test_assistant_frontend import _run_node

    _run_node(_cloud_page_script() + r'''
assert.equal(send.disabled, false, 'ready remote node enables Send');
assert.match(elements.get('cm-assistant-history-list').textContent, /Conversation B/);
const stream = await startChat('Show recorded sessions by runtime');
stream.push(frame('delta', {text:'Claude Code has '}));
await flush();
assert.match(thread.textContent, /Claude Code has/);
assert.ok(!status.textContent.includes('Answer ready'));
stream.push(frame('done', {...saved, answer:'Claude Code has 3 sessions.'}));
await flush();
assert.match(status.textContent, /Answer ready/);
assert.equal(byClass(thread, 'cm-assistant-panel').length, 1);
const originalFetch = context.fetch;
let savedBody;
context.fetch = async (url, options) => {
  if (url === '/api/dashboard/panels') {
    assert.equal(options.method, 'POST');
    savedBody = JSON.parse(options.body);
    return jsonResponse({panel_id:'kept-panel'});
  }
  return originalFetch(url, options);
};
byClass(thread, 'cm-assistant-panel-button').find(n => n.textContent === 'Save to dashboard').dispatch('click');
const buttons = byClass(thread, 'cm-assistant-panel-button');
buttons.find(n => n.textContent === 'Save').dispatch('click');
await flush();
assert.ok(savedBody, 'Save sends a real shared panel request');
assert.equal(savedBody.question, 'Show recorded sessions by runtime');
assert.match(thread.textContent, /Saved to Home/);
assertIdle();
context.assistantLeave();
assert.equal(timers.size, 0, 'no standing cloud poller in this surface');
''')


def test_new_conversation_while_connecting_preserves_node_readiness_and_history():
    from tests.test_assistant_frontend import _run_node

    script = _cloud_page_script().replace('context.loadAssistantPage();', r'''
let finishStatus, finishHistory;
context.fetch = async url => new Promise(resolve => {
  if (url.endsWith('/status')) finishStatus = resolve;
  else if (url.endsWith('/conversations')) finishHistory = resolve;
  else assert.fail('unexpected request: ' + url);
});
context.loadAssistantPage();
''')
    _run_node(script + r'''
assert.equal(send.disabled, true);
elements.get('cm-assistant-new-chat').dispatch('click');
finishStatus(jsonResponse({available:true,data_available:true,providers:[],managed:{}}));
finishHistory(jsonResponse({conversations:[{id:'kept',title:'Saved before this visit'}]}));
await flush();
assert.equal(send.disabled, false, 'New conversation must not discard node readiness');
assert.match(elements.get('cm-assistant-history-list').textContent, /Saved before this visit/);
context.assistantLeave();
''')


@pytest.mark.parametrize('reason', ['missing_key', 'decrypt_failed'])
def test_cloud_assistant_unlock_retries_status_and_history(reason):
    from tests.test_assistant_frontend import _run_node

    script = _cloud_page_script().replace('context.loadAssistantPage();', r'''
let unlocked = false;
let unlockCallback;
const originalFetch = context.fetch;
context._cmRenderKeyPrompt = (host, options) => {
  host.textContent = 'Unlock your node'; unlockCallback = options.onUnlock;
};
context.fetch = async (url, options) => {
  if (!unlocked) return {
    ok:false, status:423, text:async () => JSON.stringify({
      error:'Unlock your node to use Assistant.', reason:REASON,
    }),
  };
  return originalFetch(url, options);
};
context.loadAssistantPage();
'''.replace('REASON', repr(reason)))
    _run_node(script + r'''
assert.equal(send.disabled, true);
assert.match(elements.get('cm-assistant-recovery').textContent, /Unlock your node/);
assert.equal(typeof unlockCallback, 'function');
unlocked = true;
identity = 'unlocked-node';
unlockCallback();
await flush(); await flush();
assert.equal(send.disabled, false);
assert.match(elements.get('cm-assistant-history-list').textContent, /Conversation B/);
assert.equal(elements.get('cm-assistant-recovery').hidden, true);
context.assistantLeave();
''')


def test_hosted_home_loads_bounded_panel_details_and_drops_old_scope_or_off_tab_results():
    from tests.test_assistant_frontend import _DOM_JS, _run_node

    _run_node(_DOM_JS + r'''
const assert = require('assert');
const flush = () => new Promise(resolve => setImmediate(resolve));
const originalQuery = Node.prototype.querySelector;
Node.prototype.querySelector = function (selector) {
  if (selector.startsWith('.') && this.className.split(/\s+/).includes(selector.slice(1))) return this;
  return originalQuery.call(this, selector);
};
Object.defineProperty(Node.prototype, 'innerHTML', {
  get() { return this._html || ''; },
  set(value) {
    this._html = value; this.children = []; this._text = null;
    // Parse only the card scaffolding; assertions inspect real rendered body HTML.
    if (value.includes('cm-dashboard-delete')) {
      const remove = new Node('button'); remove.className = 'cm-dashboard-delete'; this.appendChild(remove);
      const body = new Node('div'); body.className = 'cm-dashboard-panel-body'; this.appendChild(body);
    }
  },
});
document.createElement = tag => { const node = new Node(tag); node.dataset = {}; return node; };
const grid = add('custom-dashboard-grid', 'div');
add('custom-dashboard-section', 'section');
let identity = 'node-A', listeners = [], pending = [], listCalls = 0, detailCalls = 0;
let heldList = null, holdList = false;
let panels = Array.from({length:6}, (_, i) => ({panel_id:'panel-'+i, name:'Saved '+i}));
const context = {document, console, AbortController,
  setTimeout, clearTimeout, CLOUD_MODE:true,
  _cmAssistantRelay:{version:1, identity:()=>identity},
  addEventListener(name, fn) { if (name === 'cm-assistant-scope-changed') listeners.push(fn); },
  fetch:async (url, options) => {
    if (url.includes('?limit=')) {
      listCalls++;
      if (holdList) return new Promise(resolve => { heldList = resolve; });
      return response({panels});
    }
    detailCalls++;
    return new Promise(resolve => pending.push({resolve,signal:options.signal}));
  },
};
function response(body) { return {ok:true,status:200,text:async()=>JSON.stringify(body)}; }
function detail(value) { return response({chart_spec:{chart_type:'number',y:'count'}, rows:[{count:value}]}); }
context.window = context;
vm.runInNewContext(fs.readFileSync('clawmetry/static/js/custom-dashboard.js','utf8'), context);
const first = context.loadCustomDashboardPanels(); await flush();
assert.equal(listCalls,1); assert.equal(detailCalls,4,'at most four simultaneous detail reads');
pending.splice(0).forEach((item,i)=>item.resolve(detail(i+1))); await flush();
assert.equal(detailCalls,6);
pending.splice(0).forEach(item=>item.resolve(detail(6))); await first;
assert.equal(grid.children.length,6);
assert.match(grid.children[0].querySelector('.cm-dashboard-panel-body').innerHTML,/>1</);

const reload = context.loadCustomDashboardPanels(); await flush();
assert.equal(listCalls,2,'Home reload reruns saved panels');
const abandoned = pending.splice(0);
context.customDashboardLeave();
assert.ok(abandoned.every(item=>item.signal.aborted));
abandoned.forEach(item=>item.resolve(detail(999))); await reload;
assert.ok(grid.children.every(card=>!card.querySelector('.cm-dashboard-panel-body').innerHTML.includes('999')));
assert.equal(detailCalls,10,'no extra queued detail requests after leaving Home');

holdList = true;
const oldLoad = context.loadCustomDashboardPanels(); await flush();
const oldList = heldList;
identity = 'node-B';
panels=[]; holdList=false;
listeners.forEach(fn=>fn());
assert.equal(grid.textContent,'','identity event clears old cards synchronously');
await flush();
oldList(response({panels:[{panel_id:'secret-A',name:'Old private panel'}]})); await oldLoad;
assert.equal(grid.children.length,0);
assert.ok(!grid.innerHTML.includes('Old private panel'));
assert.match(grid.innerHTML,/Ask a question/);
context.customDashboardLeave();
''')


def test_scope_rotation_clears_visible_content_and_rejects_late_conversation_and_stream():
    from tests.test_assistant_frontend import _run_node

    _run_node(_cloud_page_script() + r'''
const stream = await startChat('Private question on node A');
stream.push(frame('delta', {text:'Private answer on node A'}));
await flush();
elements.get('cm-assistant-api-key').value = 'ephemeral-provider-key';
const originalFetch = context.fetch;
context.fetch = async (url, options) => url.endsWith('/conversations')
  ? jsonResponse({conversations:[]}) : originalFetch(url, options);
changeScope('account-node-key-B');
assert.equal(thread.textContent, '', 'scope event clears immediately');
assert.equal(elements.get('cm-assistant-api-key').value, '');
stream.push(frame('done', {...saved, answer:'late private answer'}));
await flush(); await flush();
assert.ok(!thread.textContent.includes('private'));
assert.ok(!elements.get('cm-assistant-history-list').textContent.includes('Conversation B'));
assert.ok(chatCalls[0].options.signal.aborted);

let resolveHistory;
context.fetch = async (url, options) => url.endsWith('/conversations')
  ? new Promise(resolve => { resolveHistory = resolve; }) : originalFetch(url, options);
context.assistantLeave();
changeScope('account-node-key-C');
context.loadAssistantPage();
await flush();
identity = 'account-node-key-D'; // change between decrypt and DOM publication, even without event
resolveHistory(jsonResponse({conversations:[{id:'leaked',title:'Secret old title'}]}));
await flush();
assert.ok(!elements.get('cm-assistant-history-list').textContent.includes('Secret old title'));
context.assistantLeave();
''')
