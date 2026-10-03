"""Hosted/local Improve uses scoped evidence and truthful transport states.

AC-ASSIST-006.2 -- encrypted candidate/evidence responses render in hosted UI.
AC-ASSIST-006.3 -- distinct recoverable states and actionable key unlock.
AC-ASSIST-006.4 -- scope isolation, partial/stale coverage, unavailable and retry.
"""
from pathlib import Path
import shutil
import subprocess

import pytest

ROOT = Path(__file__).parents[1]
BOOT = r'''
const fs = require('fs'), vm = require('vm'), assert = require('assert');
global.window = global;
let runtime = 'codex';
window.CLOUD_MODE = true;
window.CLOUD_NODE_ID = 'node-a';
window.CLOUD_TOKEN = 'account-a';
let encryptionKey = 'key-a';
global.localStorage = {getItem:()=>encryptionKey};
window._cmRuntimeFilter = () => runtime;
function element() {
  return {_text:'', _html:'', hidden:true, style:{}, children:[],
    get textContent(){return this._text},
    set textContent(v){this._text=v;this._html='';this.children=[]},
    get innerHTML(){return this._html},
    set innerHTML(v){this._html=v;this._text='';this.children=[]},
    setAttribute(){}, classList:{toggle(){}}, querySelector(){return null},
    appendChild(child){this.children.push(child);return child},
    addEventListener(type, fn){this[type]=fn}};
}
const ids = ['improve-list', 'improve-empty', 'improve-source-note',
  'improve-summary-candidates','improve-summary-candidates-note',
  'improve-summary-conversations','improve-summary-projects','improve-summary-window',
  'improve-review-modal','cm-cloud-improve'];
const nodes = Object.fromEntries(ids.map(id => [id, element()]));
global.document = {getElementById:id=>nodes[id]||null, querySelectorAll:()=>[],
  createElement:()=>element(), createTextNode:text=>({textContent:text})};
function payload(rt='codex', excerpt='Always keep changes small.') {
 return {available:true, generated_at:new Date().toISOString(), window_days:30,
   scope:{node_id:'node-a',runtime:rt}, message_count:2, candidate_count:1,
   conversation_count:2, project_count:1,
   signals:[{id:rt,kind:'preference',excerpt,seen_count:2,
     runtimes:[rt],evidence:[{excerpt,workspace:'project'}]}]};
}
const response = (data,status=200) => ({ok:status<400, json:async()=>data});
let calls=[];
global.fetch = async url => {calls.push(url);return response(payload(runtime));};
vm.runInThisContext(fs.readFileSync('clawmetry/static/js/improve.js','utf8'));
'''


def run_node(script):
    if not shutil.which('node'):
        pytest.skip('Node.js required for the existing frontend contract harness')
    result = subprocess.run(['node','-e', BOOT+'\n(async()=>{'+script+'\n})().catch(e=>{console.error(e);process.exitCode=1;});'],
                            cwd=ROOT, capture_output=True, text=True, timeout=15)
    assert result.returncode == 0, result.stderr


def test_hosted_candidate_evidence_staleness_sampling_and_escape():
    run_node(r'''
fetch = async url => {
 calls.push(url); let data=payload('codex','Always escape <script>alert(1)</script>.');
 data.generated_at='2026-01-01T00:00:00Z'; data.stale=true;
 data.coverage={status:'partial',inspected_events:150,candidate_events:800,omitted_payloads:1,candidates_truncated:true};
 return response(data);
};
await loadImprove();
assert.equal(calls.length,1); assert.match(calls[0],/runtime=codex/);
assert.match(nodes['improve-list'].innerHTML,/&lt;script&gt;/);
assert.doesNotMatch(nodes['improve-list'].innerHTML,/<script>/);
assert.equal(nodes['improve-summary-candidates'].textContent,'1');
const note=nodes['improve-source-note'];
assert.match(note.textContent,/Partial coverage/);
assert.match(note.textContent,/150 of 800/);
assert.match(note.textContent,/Saved results from/);
assert.match(note.textContent,/1 records/);
assert(note.children.some(child=>child.textContent==='Refresh'));
''')


@pytest.mark.parametrize('reason,expected', [
    ('missing_key','Unlock'), ('missing_snapshot','No saved'),
    ('snapshot_pending','Waiting'), ('old_collector','Update ClawMetry'),
    ('missing_slice','Update ClawMetry'), ('node_offline','offline'),
    ('decrypt_failed','could not be unlocked'), ('unavailable','unavailable'),
    ('<script>private provider error</script>','unavailable'),
])
def test_unavailable_states_never_show_zero_or_raw_errors(reason, expected):
    import json
    run_node('fetch = async()=>response({available:false,reason:'+json.dumps(reason)+'});\n'+r'''
await loadImprove();
assert.equal(nodes['improve-summary-candidates'].textContent,'Unavailable');
assert.equal(nodes['improve-summary-conversations'].textContent,'Unavailable');
assert.equal(nodes['improve-empty'].style.display,'none');
assert.equal(window._cmImproveState.data,null);
assert.doesNotMatch(nodes['improve-list'].textContent,/private provider|<script>/);
assert(nodes['improve-list'].children.some(child=>child.textContent==='Refresh'));
'''+f"assert(nodes['improve-list'].textContent.includes({json.dumps(expected)}));")


def test_runtime_switch_rejects_slow_old_response_and_deduplicates():
    run_node(r'''
let releaseOld;
fetch = url => {calls.push(url);return calls.length===1
 ? new Promise(resolve=>{releaseOld=resolve;}) : Promise.resolve(response(payload('claude_code')));};
const old=loadImprove();
assert.equal(loadImprove(),old); assert.equal(calls.length,1);
runtime='claude_code'; await loadImprove();
releaseOld(response(payload('codex','Always show the wrong runtime.'))); await old;
assert.equal(calls.length,2);
assert.equal(window._cmImproveState.data.scope.runtime,'claude_code');
assert.doesNotMatch(nodes['improve-list'].innerHTML,/wrong runtime/);
await loadImprove(); assert.equal(calls.length,2);
await loadImprove(true); assert.equal(calls.length,3);
''')


def test_runtime_or_node_mismatch_and_missing_scoped_slice_never_fall_back():
    run_node(r'''
fetch=async()=>response(payload('all'));
await loadImprove(); assert.equal(nodes['improve-summary-candidates'].textContent,'Unavailable');
fetch=async()=>{let p=payload();p.scope.node_id='wrong-node';return response(p)};
await loadImprove(true); assert.equal(nodes['improve-summary-candidates'].textContent,'Unavailable');
fetch=async()=>{let p=payload();delete p.scope;return response(p)};
await loadImprove(true); assert.equal(nodes['improve-summary-candidates'].textContent,'Unavailable');
''')


def test_missing_interceptor_never_queries_cloud_container():
    run_node(r'''
delete nodes['cm-cloud-improve'];
await loadImprove();
assert.equal(calls.length,0);
assert.equal(nodes['improve-summary-candidates'].textContent,'Unavailable');
''')


def test_timeout_even_when_transport_ignores_abort_allows_retry():
    run_node(r'''
const realTimer=setTimeout;
global.setTimeout=(fn,ms)=>realTimer(fn,ms===8000?5:ms);
fetch=()=>new Promise(()=>{});
await loadImprove();
assert.equal(nodes['improve-summary-candidates'].textContent,'Unavailable');
fetch=async()=>response(payload());
await loadImprove(true);
assert.equal(nodes['improve-summary-candidates'].textContent,'1');
''')


def test_local_mode_works_without_hosted_helper_and_cache_is_node_scoped():
    run_node(r'''
window.CLOUD_MODE=false; window.CLOUD_NODE_ID=''; delete nodes['cm-cloud-improve'];
await loadImprove(); assert.equal(calls.length,1);
window.CLOUD_MODE=true; window.CLOUD_NODE_ID='node-b'; nodes['cm-cloud-improve']=element();
fetch=async url=>{calls.push(url);const p=payload();p.scope.node_id='node-b';return response(p)};
await loadImprove(); assert.equal(calls.length,2);
assert.equal(window._cmImproveState.data.scope.node_id,'node-b');
''')


@pytest.mark.parametrize('reason', ['missing_key', 'decrypt_failed'])
def test_key_prompt_unlock_retries_current_guidance(reason):
    import json
    run_node('const failure='+json.dumps(reason)+';'+r'''
let prompt;
window._cmRenderKeyPrompt=(container,options)=>{prompt={container,options};};
fetch=async url=>{calls.push(url);return response(calls.length===1
 ? {available:false,reason:failure} : payload());};
await loadImprove();
assert.equal(prompt.container,nodes['improve-list']);
assert.match(prompt.options.title,/guidance/i);
assert.equal(nodes['improve-summary-candidates'].textContent,'Unavailable');
encryptionKey='corrected-key';
await prompt.options.onUnlock();
assert.equal(calls.length,2);
assert.equal(nodes['improve-summary-candidates'].textContent,'1');
''')


@pytest.mark.parametrize('change', ["encryptionKey=null", "encryptionKey='key-b'",
                                   "window.CLOUD_TOKEN='account-b'", "window.CLOUD_NODE_ID='node-b'"])
def test_cached_guidance_is_not_reused_after_unlock_context_changes(change):
    run_node(r'''
await loadImprove();
assert.match(nodes['improve-list'].innerHTML,/Always keep/);
fetch=async url=>{calls.push(url);return response({available:false,reason:'missing_key'});};
'''+change+';'+r'''
await loadImprove();
assert.equal(calls.length,2);
assert.equal(window._cmImproveState.data,null);
assert.doesNotMatch(nodes['improve-list'].innerHTML,/Always keep/);
assert.equal(nodes['improve-summary-candidates'].textContent,'Unavailable');
''')


@pytest.mark.parametrize('change', ["encryptionKey=null", "encryptionKey='key-b'",
                                   "window.CLOUD_TOKEN='account-b'", "window.CLOUD_NODE_ID='node-b'"])
def test_pending_guidance_cannot_publish_after_unlock_context_changes(change):
    run_node(r'''
let release;
fetch=async url=>{calls.push(url);return {ok:true,json:()=>new Promise(resolve=>{release=resolve})};};
const pending=loadImprove();
await new Promise(resolve=>setImmediate(resolve));
'''+change+';'+r'''
release(payload('codex','Old private guidance'));
await pending;
assert.equal(window._cmImproveState.data,null);
assert.doesNotMatch(nodes['improve-list'].innerHTML,/Old private/);
assert.notEqual(nodes['improve-summary-candidates'].textContent,'1');
''')


def test_real_empty_is_measured_zero_with_the_empty_state():
    run_node(r'''
fetch=async()=>response({...payload(),signals:[],candidate_count:0,message_count:0,conversation_count:0,project_count:0});
await loadImprove();
assert.equal(nodes['improve-summary-candidates'].textContent,'0');
assert.equal(nodes['improve-empty'].style.display,'flex');
assert.equal(window._cmImproveState.loaded,true);
''')


def test_new_key_request_does_not_join_old_pending_request():
    run_node(r'''
let release;
fetch=url=>{calls.push(url);return calls.length===1
 ? new Promise(resolve=>{release=resolve}) : Promise.resolve(response(payload('codex','New guidance')));};
const old=loadImprove();
encryptionKey='key-b';
const current=loadImprove();
assert.notEqual(current,old);
await current;
release(response(payload('codex','Old private guidance')));await old;
assert.equal(calls.length,2);
assert.match(nodes['improve-list'].innerHTML,/New guidance/);
assert.doesNotMatch(nodes['improve-list'].innerHTML,/Old private/);
''')


def test_filter_click_cannot_render_cached_guidance_after_key_removal():
    run_node(r'''
await loadImprove();
encryptionKey=null;
fetch=async url=>{calls.push(url);return response({available:false,reason:'missing_key'});};
improveSetKind('preference');await loadImprove();
assert.equal(window._cmImproveState.data,null);
assert.doesNotMatch(nodes['improve-list'].innerHTML,/Always keep/);
''')


def test_obsolete_unlock_prompt_cannot_refresh_another_account():
    run_node(r'''
let unlock;
window._cmRenderKeyPrompt=(container,options)=>{unlock=options.onUnlock;};
fetch=async url=>{calls.push(url);return response({available:false,reason:'missing_key'});};
await loadImprove();
window.CLOUD_TOKEN='other-account';encryptionKey='other-key';
await unlock();
assert.equal(calls.length,1);
''')
