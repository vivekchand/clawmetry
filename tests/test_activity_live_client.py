"""AC-OBS-INV-004.1/2: replay, bounded buffers and active-view request budgets."""
import json
import pathlib
import shutil
import subprocess

import pytest

from tests.test_incident_lifecycle import server  # noqa: F401

SCRIPT = pathlib.Path(__file__).resolve().parents[1] / 'clawmetry/static/js/activity-live.js'


def run(case, setup=''):
    node = shutil.which('node')
    if not node:
        pytest.skip('node not installed')
    harness = r'''
const assert = require('node:assert/strict');
global.window=global; window._cmCurrentTab='brain'; window.CLOUD_MODE=false;
const hooks={}; global.document={hidden:false,addEventListener:(k,fn)=>hooks[k]=fn};
const timers=new Map(); let timerId=0;
global.setTimeout=(fn,delay)=>{timers.set(++timerId,{fn,delay});return timerId;};
global.clearTimeout=(id)=>timers.delete(id);
let pages=[], hits=[], fail=false, pending=null;
global.fetch=async url=>{
 hits.push(url);
 if(pending) return await pending;
 if(fail) throw new Error('offline');
 return {ok:true,json:async()=>pages.shift() || {cursor:'quiet',rows:[],brain_events:[]}};
};
async function tick(){
 const pair=Array.from(timers.entries()).sort((a,b)=>a[1].delay-b[1].delay)[0];
 if(!pair)return false; timers.delete(pair[0]); pair[1].fn();
 for(let i=0;i<8;i++)await Promise.resolve();
 return true;
}
const row=(id,text=id)=>({id,ts:'2026-10-02T00:00:00Z',data:{text}});
const page=(cursor,rows=[],more=false)=>({cursor,rows,brain_events:rows.map(r=>({eventId:r.id,detail:r.data.text})),has_more:more});
__SCRIPT__
__SETUP__
(async()=>{
__CASE__
console.log(JSON.stringify({ok:true,hits,timers:timers.size}));
})().catch(e=>{console.error(e);process.exitCode=1;});
'''
    program = harness.replace('__SCRIPT__', SCRIPT.read_text()).replace('__SETUP__', setup).replace('__CASE__', case)
    result = subprocess.run([node, '-e', program], text=True, capture_output=True, timeout=10, check=False)
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout)


def test_shared_scope_uses_one_fetch_and_no_off_tab_or_hidden_poller():
    run(r'''
let left=[],right=[]; pages=[page('one',[row('a')])];
const a=cmWatchActivity({runtime:'codex'},(p,e)=>left.push(p),'brain');
const b=cmWatchActivity({runtime:'codex'},(p,e)=>right.push(p),'brain');
await tick(); assert.equal(hits.length,1); assert.equal(left.length,1);assert.equal(right.length,1);
assert(hits[0].includes('runtime=codex'));
window._cmCurrentTab='guard';cmActivityVisibilityChanged();assert.equal(timers.size,0);
document.hidden=true;window._cmCurrentTab='brain';hooks.visibilitychange();assert.equal(timers.size,0);
document.hidden=false;hooks.visibilitychange();await tick();assert.equal(hits.length,2);
a();b();assert.equal(timers.size,0);
''')


def test_failed_read_keeps_cursor_and_reconnect_replays_it():
    run(r'''
let received=[],errors=0; pages=[page('committed',[row('a')])];
cmWatchActivity({},(p,e)=>e?errors++:received.push(p),'brain');
await tick();fail=true;await tick();assert.equal(errors,1);
fail=false;pages=[page('later',[row('late')])];await tick();
assert(hits[1].includes('cursor=committed'));assert(hits[2].includes('cursor=committed'));
assert.equal(received[1].rows[0].id,'late');
''')


def test_scope_change_and_hidden_inflight_read_do_not_advance_cursor():
    run(r'''
let received=[];let resolve;
pending=new Promise(r=>resolve=r);
cmWatchActivity({runtime:'codex'},(p,e)=>received.push(p),'brain');
await tick();document.hidden=true;
resolve({ok:true,json:async()=>page('missed',[row('a')])});
for(let i=0;i<8;i++)await Promise.resolve();
assert.equal(received.length,0);assert.equal(timers.size,0);
pending=null;document.hidden=false;pages=[page('replayed',[row('a')])];
hooks.visibilitychange();await tick();
assert(!hits[1].includes('cursor='));assert.equal(received[0].rows[0].id,'a');
''')


def test_expired_cursor_discards_buffer_and_bootstraps():
    run(r'''
let received=[]; pages=[page('one',[row('a')]),{resync_required:true,rows:[]},page('fresh',[row('b')])];
cmWatchActivity({},(p,e)=>received.push(p),'brain');
await tick();await tick();await tick();
assert.equal(received[1].resync_required,true);assert(!hits[2].includes('cursor='));
let cached;cmWatchActivity({},(p,e)=>cached=p,'brain');
await Promise.resolve();assert.deepEqual(cached.rows.map(r=>r.id),['b']);
''')


def test_buffers_are_bounded_and_updates_replace_existing_id():
    run(r'''
let stop=cmWatchActivity({},()=>{},'brain');
for(let i=0;i<7;i++){pages=[page(String(i),Array.from({length:100},(_,j)=>row(String(i*100+j))),true)];await tick();}
pages=[page('updated',[row('699','updated')])];await tick();stop();
let cached;cmWatchActivity({},(p,e)=>cached=p,'brain');await Promise.resolve();
assert.equal(cached.rows.length,500);assert.equal(cached.brain_events.length,500);
assert.equal(cached.rows.filter(r=>r.id==='699').length,1);
assert.equal(cached.rows.find(r=>r.id==='699').data.text,'updated');
assert.equal(cached.brain_events.find(r=>r.eventId==='699').detail,'updated');
''')


def test_compatibility_stream_shares_reader_and_reports_resync():
    run(r'''
pages=[page('one',[row('a')])];let messages=[],connected=0,resync=0;
let stream=cmActivityEventSource({runtime:'codex'});
stream.onmessage=e=>messages.push(JSON.parse(e.data));
stream.addEventListener('connected',()=>connected++);stream.addEventListener('resync',()=>resync++);
let other=[];const stop=cmWatchActivity({runtime:'codex'},p=>other.push(p),'brain');
await tick();assert.equal(hits.length,1);assert.equal(connected,1);assert.equal(messages[0].eventId,'a');
pages=[{resync_required:true}];await tick();assert.equal(resync,1);
stream.close();stop();assert.equal(stream.readyState,2);assert.equal(timers.size,0);
''')


def test_brain_quiet_reconnect_preserves_cached_evidence_and_filters():
    app = SCRIPT.with_name('app.js').read_text()
    start = app.index('function _startBrainSSE() {')
    end = app.index('\nfunction _stopBrainSSE()', start)
    setup = r'''
let _brainRange=null, _brainSSE=null, _brainSSEConnected=false, _brainSSEEverConnected=false;
let _brainAllEvents=[], _brainFilter='selected-session', _brainTypeFilter='tool';
let _brainSSEFirstFailMs=0, _brainRefreshTimer=null;
function _cmRuntimeFilter(){return 'codex';}
function _updateBrainLiveIndicator(){}
function _resetBrainSSEReconnectState(){}
function _scheduleBrainSSEReconnect(){}
function renderBrainStream(){}
function renderBrainChart(){}
function renderBrainTypeChips(){}
function loadBrainPage(){}
document.getElementById=()=>null;
document.querySelector=()=>({});
''' + app[start:end]
    run(r'''
function brainPage(cursor, ids) {
 const result=page(cursor,ids.map(id=>row(id)));
 result.brain_events.forEach(event=>{event.time='2026-10-02T00:00:00Z';event.source='codex';});
 return result;
}
pages=[brainPage('first',['evidence'])];_startBrainSSE();await tick();
assert.deepEqual(_brainAllEvents.map(event=>event.eventId),['evidence']);
fail=true;await tick();assert.equal(_brainSSE,null);
fail=false;pages=[brainPage('quiet',[])];_startBrainSSE();
await Promise.resolve();await tick();
assert.deepEqual(_brainAllEvents.map(event=>event.eventId),['evidence']);
assert.equal(_brainFilter,'selected-session');assert.equal(_brainTypeFilter,'tool');
pages=[{resync_required:true}];await tick();
assert.deepEqual(_brainAllEvents,[]);
_brainSSE.close();
''', setup)
