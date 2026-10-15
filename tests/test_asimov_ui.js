/* AC-ASIMOV-002.3 AC-ASIMOV-002.4 AC-ASIMOV-003.2 AC-ASIMOV-006.1 */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const source = fs.readFileSync(path.join(__dirname, '../clawmetry/static/js/asimov.js'), 'utf8');
class Element {
  constructor(tag='div') { this.tagName=tag; this.children=[]; this.dataset={}; this.attributes={}; this.style={}; this.listeners={}; this._text=''; this.hidden=false; }
  set textContent(value) { this._text=String(value); this.children=[]; }
  get textContent() { return this._text + this.children.map(c=>c.textContent).join(''); }
  set innerHTML(value) { throw new Error('Untrusted HTML assignment'); }
  append(...children) { this.children.push(...children); }
  replaceChildren(...children) { this._text=''; this.children=children; }
  setAttribute(key,value) { this.attributes[key]=value; }
  removeAttribute(key) { delete this.attributes[key]; }
  addEventListener(key,value) { this.listeners[key]=value; }
  appendChild(child) { this.children.push(child); }
  insertBefore(child,reference) { const index=this.children.indexOf(reference); if(index<0)this.children.push(child);else this.children.splice(index,0,child); }
  querySelector() { return null; }
}
function harness(snapshot) {
  const listeners={}, timers=new Map(), requests=[], nodes=new Map(); let timerId=0;
  const ids=['app','runs','more-runs','empty','workbench','robot','source','status','freshness','mode','battery','battery-detail','event-count','dropped','joints','orientation','angular','gravity','alerts','health','run-id','clock','events','trace-empty','trace-loaded','more-events','message'];
  ids.forEach(id=>nodes.set('asimov-'+id,new Element()));
  let now=Date.now(); class ClockDate extends Date { static now(){return now;} }
  const c={document:{readyState:'loading',hidden:false,getElementById:id=>nodes.get(id),createElement:tag=>new Element(tag),addEventListener:(name,fn)=>{listeners[name]=fn;}},
    addEventListener:(name,fn)=>{listeners[name]=fn;},setTimeout:(fn,delay)=>{timers.set(++timerId,{fn,delay});return timerId;},clearTimeout:id=>timers.delete(id),
    fetch:(url,options)=>new Promise((resolve,reject)=>requests.push({url,options,resolve,reject})),AbortController,URLSearchParams,Date:ClockDate,Number,Set,JSON,Promise,console};
  if(snapshot!==undefined)c.__CM_ASIMOV_SNAPSHOT__=snapshot;
  c.window=c;vm.createContext(c);vm.runInContext(source,c);
  return {c,listeners,timers,requests,nodes,advance:ms=>{now+=ms;},node:id=>nodes.get('asimov-'+id),answer:(request,body)=>request.resolve({ok:true,json:async()=>body})};
}
const id='a'.repeat(32), id2='b'.repeat(32);
function runData(extra={}) { return {run_id:id,robot_id:'my-asimov',source_kind:'asimov_sdk',environment:'hardware',status:'live',started_ns:'1790000000000000001',event_count:4,dropped_total:0,observation_age_s:0.4,
  observation:{mode:'STAND',joints:[{name:'hip',position_rad:0,velocity_rad_s:null,current_amp:null,temperature_c:23.5}],base:{quaternion_wxyz:[1,0,0,0]},battery:{soc_percent:50,voltage_v:48},alerts:[]},...extra}; }
async function settle(){await new Promise(setImmediate);}
async function run(){
  let h=harness();
  assert.equal(h.c.cmAsimov.number(null),'Not reported');
  assert.equal(h.c.cmAsimov.number(undefined),'Not reported');
  assert.equal(h.c.cmAsimov.number(NaN),'Not reported');
  assert.equal(h.c.cmAsimov.number(0),'0');
  assert.equal(h.c.cmAsimov.status(runData({source_kind:'asimov_recording',status:'live'})),'recorded');
  assert.equal(h.c.cmAsimov.source(runData({source_kind:'asimov_recording'})),'Imported recording');
  h.c.localStorage={getItem:key=>key==='clawmetry-token'?'local-test-token':null};
  const first=h.c.cmAsimov.start(); h.c.cmAsimov.refresh(); await settle();
  assert.equal(h.requests.length,1,'summary reads deduplicate in flight');
  assert.equal(h.requests[0].options.headers.Authorization,'Bearer local-test-token');
  assert.equal(h.requests[0].url.includes('local-test-token'),false,'credentials never enter URLs');
  h.answer(h.requests[0],{runs:[runData()],has_more:false});await settle();
  assert.equal(h.requests.length,2,'one selected trace read accompanies the summary');
  h.answer(h.requests[1],{events:[],next_after:0,has_more:false});await first;
  assert.equal(h.node('mode').textContent,'STAND');
  assert.equal(h.node('joints').children[0].children[1].textContent,'0');
  assert.equal(h.node('joints').children[0].children[2].textContent,'Not reported');
  assert.match(h.node('battery-detail').textContent,/48 V/);
  h.advance(6000);
  assert.equal(h.c.cmAsimov.status(h.c.cmAsimov.getState().runs[0]),'stale','retained summaries cannot keep old live badges');
  assert.equal(h.timers.size,1,'only one poll remains after requests settle');
  assert.equal([...h.timers.values()][0].delay,3000);
  h.c.document.hidden=true;h.listeners.visibilitychange();
  assert.equal(h.timers.size,0,'hidden pages clear scheduled polls');
  await h.c.cmAsimov.refresh();assert.equal(h.requests.length,2,'hidden pages do not fetch');
  h.c.document.hidden=false;h.listeners.visibilitychange();await settle();
  assert.equal(h.requests.length,3);
  h.c.cmAsimov.stop();assert.equal(h.requests[2].options.signal.aborted,true);
  assert.equal(h.timers.size,0,'stop clears the request deadline');
  h.answer(h.requests[2],{runs:[runData({robot_id:'late'})],has_more:false});await settle();
  assert.equal(h.node('robot').textContent,'my-asimov','responses after stop cannot paint');
  h.listeners.pageshow({persisted:true});await settle();
  assert.equal(h.requests.length,4,'back navigation resumes observation polling');
  h.c.cmAsimov.stop();

  const attack='<img src=x onerror=alert(1)>';
  const commands=[{kind:'command.returned',sequence:2,wall_time_ns:'1790000000000000001',data:{name:attack,source_timestamp_s:0,outcome:'unknown',result:attack}}];
  h=harness({runs:[runData({robot_id:attack,source_kind:'asimov_recording',status:'live',observation:{joints:[{name:attack,position_rad:null}],alerts:[attack],source_timestamp_s:4}})],events:{[id]:commands}});
  await h.c.cmAsimov.start();
  assert.equal(h.requests.length,0,'injected decrypted snapshots do not fetch local endpoints');
  assert.equal(h.node('robot').textContent,attack);
  assert.equal(h.node('status').textContent,'Recorded');
  assert.match(h.node('freshness').textContent,/does not report a live connection/);
  assert.equal(h.node('joints').children[0].children[0].textContent,attack);
  assert.equal(h.node('alerts').children[0].textContent,attack);
  assert.match(h.node('events').textContent,/Outcome unknown/);
  assert.match(h.node('events').textContent,/Source clock: 0/);
  assert.match(h.node('events').textContent,/Receipt time:/);
  assert.match(h.node('events').textContent,/<img src=x/,'source text is retained without HTML parsing');
  assert.match(h.node('clock').textContent,/Recording time \(s\): 4/);
  await h.c.cmAsimov.refresh();
  assert.equal(h.c.cmAsimov.getState().events.length,1,'incremental trace does not duplicate events');
  await h.c.cmAsimov.reset({runs:[runData({run_id:id2,robot_id:'new-node'})],events:{}});
  assert.equal(h.c.cmAsimov.getState().events.length,0,'switching snapshot sources discards prior evidence');
  assert.equal(h.node('robot').textContent,'new-node');

  h=harness({runs:[runData({observation:null,start:{joint_names:Array.from({length:25},(_,i)=>'joint-'+i)}})]});
  await h.c.cmAsimov.start();
  assert.equal(h.node('joints').children.length,25,'all declared joints remain present without a sample');
  assert.equal(h.node('joints').children[24].children[4].textContent,'Not reported');
  assert.equal(h.node('orientation').textContent,'Not reported');
  assert.equal(h.node('battery').textContent,'Not reported');
  assert.equal(h.node('alerts').textContent,'Alerts are not reported.');

  const received=String(BigInt(Date.now()-1000)*1000000n);
  h=harness({runs:[runData({observation_received_at_ns:received})],events:{[id]:commands},trace_window:{[id]:{scope:'recent',retained:1,truncated:true}}});
  await h.c.cmAsimov.start();
  assert.equal(h.node('status').textContent,'Receiving state');
  assert.match(h.node('trace-loaded').textContent,/Recent evidence from the node snapshot/);
  assert.match(h.node('trace-loaded').textContent,/Earlier evidence is omitted/);
  h.advance(6000);await h.c.cmAsimov.refresh();
  assert.equal(h.node('status').textContent,'State is stale','a frozen snapshot cannot remain live');
  await h.c.cmAsimov.reset({runs:[runData({observation_received_at_ns:String(BigInt(Date.now()+60000)*1000000n)})]});
  assert.equal(h.node('status').textContent,'State unknown','future receipt clocks cannot establish freshness');
  assert.match(h.node('freshness').textContent,/freshness is unknown/);
  assert.match(h.node('trace-loaded').textContent,/not included in this snapshot/);
  await h.c.cmAsimov.reset({runs:[runData({observation_received_at_ns:null})]});
  assert.equal(h.node('status').textContent,'State unknown');
  await h.c.cmAsimov.reset({runs:[runData({observation_received_at_ns:'not-a-clock'})]});
  assert.equal(h.node('status').textContent,'State unknown');
  h=harness({runs:[]});await h.c.cmAsimov.start();assert.equal(h.node('empty').hidden,false);
  h=harness();const read=h.c.cmAsimov.start();await settle();
  h.requests[0].resolve({ok:false});await read;
  assert.match(h.node('message').textContent,/cannot read robot evidence/);
  assert.equal(h.node('empty').hidden,false,'unavailable state does not invent data');

  h=harness();let current=h.c.cmAsimov.start();await settle();h.answer(h.requests[0],{runs:[runData()],has_more:false});await settle();h.answer(h.requests[1],{events:[],has_more:false});await current;
  current=h.c.cmAsimov.refresh();await settle();h.requests[2].resolve({ok:false});await current;
  assert.equal(h.node('status').textContent,'Stored state unavailable','failed polling cannot retain a live badge');
  assert.match(h.node('freshness').textContent,/may be old/);
  h=harness();h.c.CLOUD_MODE=true;h.c.localStorage={getItem:()=> 'private-local-token'};
  current=h.c.cmAsimov.start();await settle();
  assert.equal(h.requests[0].options.headers.Authorization,undefined,'cloud fallback never sends a saved local gateway token');
  h.requests[0].resolve({ok:false,status:401});await current;
  assert.match(h.node('message').textContent,/Open the dashboard to sign in/);
  h=harness();let providerSignal;
  h.c.cmAsimovProvider={runs:(_args,options)=>{providerSignal=options.signal;return new Promise(()=>{});}};
  current=h.c.cmAsimov.start();await settle();
  const timeout=[...h.timers.values()].find(timer=>timer.delay===12000);
  assert.ok(timeout,'provider reads have a deadline');timeout.fn();await current;
  assert.equal(providerSignal.aborted,true);
  assert.equal(h.c.cmAsimov.getState().loading,null,'a hung shared snapshot cannot hold the renderer forever');
  assert.equal([...h.timers.values()].some(timer=>timer.delay===3000),true,'polling recovers after provider timeout');
  const navigation=fs.readFileSync(path.join(__dirname,'../clawmetry/static/js/nav-dropdown.js'),'utf8');
  for(const cloud of [false,true]) {
    const callbacks={}, rail=new Element(), context={window:{CLOUD_MODE:cloud},document:{addEventListener:(name,fn)=>{callbacks[name]=fn;},getElementById:()=>null,querySelector:selector=>selector==='#left-nav .left-nav-section'?rail:null,createElement:tag=>new Element(tag)}};
    vm.createContext(context);vm.runInContext(navigation,context);callbacks.DOMContentLoaded();
    assert.equal(rail.children.length,cloud?0:1,'local navigation stays available without a private package');
    if(!cloud){assert.equal(rail.children[0].href,'/asimov');assert.match(rail.children[0].textContent,/Asimov 1/);}
  }
  if(process.argv[2]) {
    const persisted=JSON.parse(fs.readFileSync(process.argv[2],'utf8'));
    h=harness(persisted);h.c.CLOUD_MODE=true;await h.c.cmAsimov.start();
    assert.equal(h.requests.length,0,'decrypted persisted evidence never falls back to robot files or local API reads');
    assert.equal(h.node('robot').textContent,'lab-asimov');
    assert.equal(h.node('status').textContent,'Recorded');
    assert.equal(h.node('joints').children.length,25);
    assert.equal(h.node('joints').children[4].children[3].textContent,'Not reported');
    assert.equal(h.node('joints').children[7].children[1].textContent,'Not reported');
    assert.match(h.node('events').textContent,/command.sent: stand/);
    assert.match(h.node('events').textContent,/Outcome unknown/);
    assert.match(h.node('trace-loaded').textContent,/Recent evidence from the node snapshot/);
    console.log('Persisted encrypted snapshot rendered without local API reads');
  }
  console.log('Asimov UI evidence and polling checks passed');
}
run().catch(error=>{console.error(error);process.exitCode=1;});
