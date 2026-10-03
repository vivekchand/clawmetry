"""AC-OBS-INV-002.1/2 and 004.2: evidence stays readable during live updates."""
import pathlib
import shutil
import subprocess

import pytest

from tests.test_incident_lifecycle import server  # noqa: F401

SCRIPT = pathlib.Path(__file__).resolve().parents[1] / 'clawmetry/static/js/investigations.js'


def run(case, script=SCRIPT):
    node = shutil.which('node')
    if not node:
        pytest.skip('node not installed')
    harness = r'''
const assert = require('node:assert/strict');
class Element {
  constructor(tag){this.tag=tag;this.children=[];this.dataset={};this.style={};this.handlers={};this.open=false;this._text='';}
  append(...children){this.children.push(...children);}
  replaceChildren(...children){this.children=children;this._text='';}
  set textContent(text){this._text=String(text);this.children=[];}
  get textContent(){return this._text+this.children.map(child=>child.textContent).join(' ');}
  set innerHTML(value){throw Error('Untrusted content must use textContent');}
  setAttribute(key,value){this[key]=value;}
  addEventListener(key,fn){this.handlers[key]=fn;}
  querySelectorAll(selector){
    const found=[];
    for(const child of this.children){
      if((selector==='details[open]' && child.tag==='details' && child.open) ||
         (selector==='[data-evidence="true"]' && child.dataset.evidence==='true'))found.push(child);
      found.push(...child.querySelectorAll(selector));
    } return found;
  }
  querySelector(selector){return this.querySelectorAll(selector)[0]||null;}
}
const root=new Element('main');
for(const id of ['trace-list','trace-detail','trace-back-btn','trace-standard-detail','trace-investigation','triage-groups','triage-groups-body']){
 const element=new Element('div'); element.id=id; root.append(element);
}
function byId(id,element=root){if(element.id===id)return element;for(const c of element.children){const result=byId(id,c);if(result)return result;}return null;}
global.window=global;global.document={createElement:tag=>new Element(tag),getElementById:byId,hidden:false,addEventListener:()=>{}};
const scope={node_id:'n',runtime:'codex',session_id:'codex:s'};
const row={id:'original',ts:'2026-10-02T10:00:00Z',event_type:'tool_result',data:{message:'<script>untrusted()</script>'}};
let payload={scope,rows:[row],evidence_rows:[row],selected_event_ids:['original'],coverage:{},execution:{status:'running'}};
global.fetch=async()=>({ok:true,json:async()=>structuredClone(payload)});
let live,stops=0;
window.cmWatchActivity=(scope,callback)=>{live=callback;return ()=>stops++;};
window.switchTab=()=>{};
__SCRIPT__
(async()=>{
__CASE__
console.log('ok');
})().catch(error=>{console.error(error);process.exitCode=1;});
'''
    program = harness.replace('__SCRIPT__', script.read_text()).replace('__CASE__', case)
    result = subprocess.run([node, '-e', program], capture_output=True, text=True, timeout=10, check=False)
    assert result.returncode == 0, result.stderr


def test_selected_error_stays_expanded_across_upserts_and_respects_manual_close():
    run(r'''
await cmLoadInvestigation({...scope,event_id:'original'});
let evidence=byId('investigation-events').querySelector('[data-evidence="true"]');
assert.equal(evidence.open,true);
assert(root.textContent.includes('<script>untrusted()</script>'));
assert(!root.textContent.includes('Finding: Unavailable'));
live({rows:[{...row,data:{message:'updated'}}],cursor:'new'});
evidence=byId('investigation-events').querySelector('[data-evidence="true"]');
assert.equal(evidence.open,true); assert(evidence.textContent.includes('updated'));
evidence.open=false;
live({rows:[],cursor:'quiet'});
assert.equal(byId('investigation-events').querySelector('[data-evidence="true"]').open,false);
''')


def test_live_recovery_refreshes_explanation_and_cost_without_replacing_event_details():
    run(r'''
const incident={incident_id:'episode',state:'active',title:'Repeated failure',detail:'Needs review',kind:'repeated_tool_failure',
 last_evidence_at:Date.now(),first_seen:Date.now(),cost_provenance:'unknown',evidence_refs:[{event_id:'original'}]};
payload.incident=incident;
await cmLoadInvestigation({...scope,incident_id:'episode'});
assert(root.textContent.includes('Unknown'));
live({rows:[],incidents:[{...incident,state:'recovered',recovered_at:Date.now(),detail:'Successful tool result observed',
 spend_at_risk_usd:1.25,cost_provenance:'estimated',spend_basis:'window_fraction'}],execution:{status:'running'}});
assert(root.textContent.includes('Finding: Recovered'));
assert(root.textContent.includes('Execution: running'));
assert(root.textContent.includes('$1.2500 estimated'));
assert(root.textContent.includes('Recovery observed'));
assert(root.textContent.includes('Successful tool result observed'));
assert.equal(byId('investigation-events').querySelector('[data-evidence="true"]').open,true);
''')


def test_old_live_callback_cannot_reopen_closed_investigation():
    run(r'''
await cmLoadInvestigation({...scope,event_id:'original'});
const old=live; cmCloseInvestigation();
old({rows:[{...row,id:'late'}],cursor:'late'});
assert.equal(byId('trace-investigation').hidden,true);
assert.equal(stops,1);
''')


def test_live_recovery_reference_missing_from_page_is_explicit_until_loaded():
    run(r'''
const incident={incident_id:'episode',state:'active',evidence_refs:[{event_id:'original'}]};
payload.incident=incident;
await cmLoadInvestigation({...scope,incident_id:'episode'});
live({rows:[],incidents:[{...incident,state:'recovered',recovery_ref:{event_id:'later'}}]});
assert(byId('investigation-evidence-coverage').textContent.includes('1 referenced events are not loaded'));
live({rows:[{...row,id:'later'}]});
assert(!byId('investigation-evidence-coverage').textContent.includes('not loaded'));
assert(root.textContent.includes('Recovery evidence'));
''')


@pytest.mark.parametrize('applied', [False, True])
def test_acknowledgement_reports_authoritative_application(applied):
    run(r'''
const applied=__APPLIED__;
const incident={incident_id:'episode',state:'active',acknowledged_at:null,evidence_refs:[]};
payload.incident=incident;
await cmLoadInvestigation({...scope,incident_id:'episode'});
function findButton(element){
 if(element.tag==='button' && element.textContent==='Acknowledge finding')return element;
 for(const child of element.children){const found=findButton(child);if(found)return found;}
}
const button=findButton(root);assert(button);
payload={ok:true,applied,incident:{...incident,acknowledged_at:applied?Date.now():null}};
button.handlers.click({currentTarget:button});
for(let i=0;i<15;i++)await Promise.resolve();
const message=byId('investigation-message').textContent;
assert.equal(message.includes('Acknowledgement saved'),applied);
if(!applied){assert(message.includes('not applied'));assert(findButton(root));}
'''.replace('__APPLIED__', 'true' if applied else 'false'))


def test_group_reads_are_lazy_shared_and_cached():
    run(r"""
window._cmCurrentTab='overview'; window._cmRuntimeFilter=()=> 'codex';
let hits=0,resolve;
global.fetch=(url,opts)=>{hits++;assert(url.includes('runtime=codex'));return new Promise(r=>resolve=r);};
await cmLoadErrorGroups(); assert.equal(hits,0);
byId('triage-groups').open=true;
const a=cmLoadErrorGroups(),b=cmLoadErrorGroups(); assert.equal(hits,1);
resolve({ok:true,json:async()=>({available:true,rows:[],coverage:{events_scanned:0}})});
await Promise.all([a,b]);await cmLoadErrorGroups();assert.equal(hits,1);
assert(root.textContent.includes('No recorded errors in this window'));
""", SCRIPT.with_name('error-groups.js'))


def test_group_read_cancels_off_tab_and_never_renders_stale_reply():
    run(r"""
window._cmCurrentTab='overview'; byId('triage-groups').open=true;
let signal,resolve;
global.fetch=(url,opts)=>{signal=opts.signal;return new Promise(r=>resolve=r);};
const loading=cmLoadErrorGroups();
window._cmCurrentTab='tracing';cmErrorGroupsVisibilityChanged();assert.equal(signal.aborted,true);
resolve({ok:true,json:async()=>({available:true,rows:[],coverage:{events_scanned:100}})});
await loading;assert.equal(byId('triage-groups-body').textContent,'');
""", SCRIPT.with_name('error-groups.js'))
