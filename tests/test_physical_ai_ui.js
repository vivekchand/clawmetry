/* Physical AI evidence, unknown-state honesty, source rendering and polling lifecycle. */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const source = fs.readFileSync(path.join(__dirname, '../clawmetry/static/js/physical_ai.js'), 'utf8');
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
function harness(snapshot, search='') {
  const listeners={}, timers=new Map(), requests=[], nodes=new Map(); let timerId=0;
  const ids=['app','detail','runs','more-runs','empty','workbench','robot','source','status','freshness','mode','battery','battery-detail','event-count','dropped','joints','orientation','angular','gravity','alerts','health','run-id','clock','events','trace-empty','trace-loaded','more-events','message','task','margin','tilt','position','linear','footprint','workspace','guard','hardware','filter-empty'];
  ids.forEach(id=>nodes.set('physical-ai-'+id,new Element()));
  const picker=nodes.get('physical-ai-hardware'); picker.options=['all','jumper','asimov_1'].map(value=>({value})); picker.value='all';
  let now=Date.now(); class ClockDate extends Date { static now(){return now;} }
  const c={location:{search},document:{readyState:'loading',hidden:false,getElementById:id=>nodes.get(id),createElement:tag=>new Element(tag),addEventListener:(name,fn)=>{listeners[name]=fn;}},
    addEventListener:(name,fn)=>{listeners[name]=fn;},setTimeout:(fn,delay)=>{timers.set(++timerId,{fn,delay});return timerId;},clearTimeout:id=>timers.delete(id),
    fetch:(url,options)=>new Promise((resolve,reject)=>requests.push({url,options,resolve,reject})),AbortController,URLSearchParams,Date:ClockDate,Number,Set,JSON,Promise,console};
  if(snapshot!==undefined)c.__CM_PHYSICAL_AI_SNAPSHOT__=snapshot;
  c.window=c;vm.createContext(c);vm.runInContext(source,c);
  return {c,listeners,timers,requests,nodes,advance:ms=>{now+=ms;},node:id=>nodes.get('physical-ai-'+id),answer:(request,body)=>request.resolve({ok:true,json:async()=>body})};
}
const id='a'.repeat(32), id2='b'.repeat(32);
function runData(extra={}) { return {run_id:id,robot_id:'my-jumper',source_kind:'jumper_simulation',environment:'hardware',status:'live',started_ns:'1790000000000000001',event_count:4,dropped_total:0,observation_age_s:0.4,
  observation:{mode:'STAND',joints:[{name:'hip',position_rad:0,velocity_rad_s:null,current_amp:null,temperature_c:23.5}],base:{quaternion_wxyz:[1,0,0,0]},battery:{soc_percent:50,voltage_v:48},alerts:[]},...extra}; }
async function settle(){await new Promise(setImmediate);}
async function run(){
  let h=harness();
  assert.equal(h.c.cmPhysicalAi.number(null),'Not reported');
  assert.equal(h.c.cmPhysicalAi.number(undefined),'Not reported');
  assert.equal(h.c.cmPhysicalAi.number(NaN),'Not reported');
  assert.equal(h.c.cmPhysicalAi.number(0),'0');
  assert.equal(h.c.cmPhysicalAi.status(runData({source_kind:'jumper_recording',status:'live'})),'recorded');
  assert.equal(h.c.cmPhysicalAi.source(runData({source_kind:'jumper_recording'})),'Physical agent / Imported recording');
  h.c.localStorage={getItem:key=>key==='clawmetry-token'?'local-test-token':null};
  const first=h.c.cmPhysicalAi.start(); h.c.cmPhysicalAi.refresh(); await settle();
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
  assert.equal(h.c.cmPhysicalAi.status(h.c.cmPhysicalAi.getState().runs[0]),'stale','retained summaries cannot keep old live badges');
  assert.equal(h.timers.size,1,'only one poll remains after requests settle');
  assert.equal([...h.timers.values()][0].delay,3000);
  h.c.document.hidden=true;h.listeners.visibilitychange();
  assert.equal(h.timers.size,0,'hidden pages clear scheduled polls');
  await h.c.cmPhysicalAi.refresh();assert.equal(h.requests.length,2,'hidden pages do not fetch');
  h.c.document.hidden=false;h.listeners.visibilitychange();await settle();
  assert.equal(h.requests.length,3);
  h.c.cmPhysicalAi.stop();assert.equal(h.requests[2].options.signal.aborted,true);
  assert.equal(h.timers.size,0,'stop clears the request deadline');
  h.answer(h.requests[2],{runs:[runData({robot_id:'late'})],has_more:false});await settle();
  assert.equal(h.node('robot').textContent,'my-jumper','responses after stop cannot paint');
  h.listeners.pageshow({persisted:true});await settle();
  assert.equal(h.requests.length,4,'back navigation resumes observation polling');
  h.c.cmPhysicalAi.stop();

  const attack='<img src=x onerror=alert(1)>';
  const commands=[{kind:'command.returned',sequence:2,wall_time_ns:'1790000000000000001',data:{name:attack,source_timestamp_s:0,outcome:'unknown',result:attack}},
    {kind:'controller.receipt',sequence:3,wall_time_ns:'1790000000000000002',data:{from:'gesture_hello',to:'locomotion',receipt_type:'mode_transition'}}];
  h=harness({runs:[runData({robot_id:attack,source_kind:'jumper_recording',status:'live',observation:{joints:[{name:attack,position_rad:null}],alerts:[attack],source_timestamp_s:4}})],events:{[id]:commands}});
  await h.c.cmPhysicalAi.start();
  assert.equal(h.requests.length,0,'injected decrypted snapshots do not fetch local endpoints');
  assert.equal(h.node('robot').textContent,attack);
  assert.equal(h.node('status').textContent,'Recorded');
  assert.match(h.node('freshness').textContent,/does not report a live connection/);
  assert.equal(h.node('joints').children[0].children[0].textContent,attack);
  assert.equal(h.node('alerts').children[0].textContent,attack);
  assert.match(h.node('events').textContent,/Outcome unknown/);
  assert.match(h.node('events').textContent,/command response does not confirm movement/);
  assert.match(h.node('events').textContent,/Receipt time:/);
  assert.match(h.node('events').textContent,/<img src=x/,'source text is retained without HTML parsing');
  assert.match(h.node('events').textContent,/Controller mode changed from gesture hello to locomotion/);
  assert.match(h.node('clock').textContent,/Recording time \(s\): 4/);
  await h.c.cmPhysicalAi.refresh();
  assert.equal(h.c.cmPhysicalAi.getState().events.length,2,'incremental trace does not duplicate events');
  await h.c.cmPhysicalAi.reset({runs:[runData({run_id:id2,robot_id:'new-node'})],events:{}});
  assert.equal(h.c.cmPhysicalAi.getState().events.length,0,'switching snapshot sources discards prior evidence');
  assert.equal(h.node('robot').textContent,'new-node');

  h=harness({runs:[runData({observation:null,start:{joint_names:Array.from({length:25},(_,i)=>'joint-'+i)}})]});
  await h.c.cmPhysicalAi.start();
  assert.equal(h.node('joints').children.length,25,'all declared joints remain present without a sample');
  assert.equal(h.node('joints').children[24].children[5].textContent,'Not reported');
  assert.equal(h.node('orientation').textContent,'Not reported');
  assert.equal(h.node('battery').textContent,'Not reported');
  assert.equal(h.node('alerts').textContent,'Alerts are not reported.');

  const received=String(BigInt(Date.now()-1000)*1000000n);
  h=harness({runs:[runData({observation_received_at_ns:received})],events:{[id]:commands},trace_window:{[id]:{scope:'recent',retained:1,truncated:true}}});
  await h.c.cmPhysicalAi.start();
  assert.equal(h.node('status').textContent,'Receiving state');
  assert.match(h.node('trace-loaded').textContent,/Recent evidence from the node snapshot/);
  assert.match(h.node('trace-loaded').textContent,/Earlier evidence is omitted/);
  h.advance(6000);await h.c.cmPhysicalAi.refresh();
  assert.equal(h.node('status').textContent,'State is stale','a frozen snapshot cannot remain live');
  await h.c.cmPhysicalAi.reset({runs:[runData({observation_received_at_ns:String(BigInt(Date.now()+60000)*1000000n)})]});
  assert.equal(h.node('status').textContent,'State unknown','future receipt clocks cannot establish freshness');
  assert.match(h.node('freshness').textContent,/freshness is unknown/);
  assert.match(h.node('trace-loaded').textContent,/not included in this snapshot/);
  await h.c.cmPhysicalAi.reset({runs:[runData({observation_received_at_ns:null})]});
  assert.equal(h.node('status').textContent,'State unknown');
  await h.c.cmPhysicalAi.reset({runs:[runData({observation_received_at_ns:'not-a-clock'})]});
  assert.equal(h.node('status').textContent,'State unknown');
  h=harness({runs:[]});await h.c.cmPhysicalAi.start();assert.equal(h.node('empty').hidden,false);
  h=harness();const read=h.c.cmPhysicalAi.start();await settle();
  h.requests[0].resolve({ok:false});await read;
  assert.match(h.node('message').textContent,/cannot read robot evidence/);
  assert.equal(h.node('empty').hidden,false,'unavailable state does not invent data');

  h=harness();let current=h.c.cmPhysicalAi.start();await settle();h.answer(h.requests[0],{runs:[runData()],has_more:false});await settle();h.answer(h.requests[1],{events:[],has_more:false});await current;
  current=h.c.cmPhysicalAi.refresh();await settle();h.requests[2].resolve({ok:false});await current;
  assert.equal(h.node('status').textContent,'Stored state unavailable','failed polling cannot retain a live badge');
  assert.match(h.node('freshness').textContent,/may be old/);
  h=harness();h.c.CLOUD_MODE=true;h.c.localStorage={getItem:()=> 'private-local-token'};
  await h.c.cmPhysicalAi.start();
  assert.equal(h.requests.length,0,'a cloud page waits for decrypted data without local fallback');
  assert.match(h.node('message').textContent,/cannot read robot evidence/);
  h=harness();let providerSignal;
  h.c.cmPhysicalAiProvider={runs:(_args,options)=>{providerSignal=options.signal;return new Promise(()=>{});}};
  current=h.c.cmPhysicalAi.start();await settle();
  const timeout=[...h.timers.values()].find(timer=>timer.delay===12000);
  assert.ok(timeout,'provider reads have a deadline');timeout.fn();await current;
  assert.equal(providerSignal.aborted,true);
  assert.equal(h.c.cmPhysicalAi.getState().loading,null,'a hung shared snapshot cannot hold the renderer forever');
  assert.equal([...h.timers.values()].some(timer=>timer.delay===3000),true,'polling recovers after provider timeout');
  // Task decisions, actual measurements, and incidents are separate records.
  const events = [
    {kind:'guard.decision',sequence:2,wall_time_ns:received,data:{request_id:'r1',task_id:'greeting',action:'jump',status:'denied',reason:attack}},
    {kind:'guard.incident',sequence:3,wall_time_ns:received,data:{kind:'boundary_crossed',severity:'critical',evidence_kind:'simulation',physical_stop_confirmed:false}},
    {kind:'observation',sequence:4,data:{mode:'ignored in trace'}},
    {kind:'observation.raw',sequence:5,data:{source_payload:'ignored in trace'}}
  ];
  h=harness({runs:[runData({start:{robot_type:'jumper'},observation_received_at_ns:received,observation:{table_margin_m:0,tilt_deg:0,task_id:'greeting',joints:[{name:'claw',effort_nm:0}],base:{position_m:[0,0,0],linear_velocity_m_s:[0,0,0]}}})],events:{[id]:events}});
  await h.c.cmPhysicalAi.start();
  assert.match(h.node('source').textContent,/Jumper/);
  assert.equal(h.node('margin').textContent,'0 m');
  assert.equal(h.node('tilt').textContent,'0°');
  assert.equal(h.node('task').textContent,'greeting');
  assert.equal(h.node('joints').children[0].children[3].textContent,'0');
  assert.equal(h.node('events').children.length,2);
  assert.match(h.node('events').textContent,/Task decision: denied/);
  assert.match(h.node('events').textContent,/Workspace boundary crossed/);
  assert.match(h.node('events').textContent,/does not confirm a physical stop/);
  assert.match(h.node('events').textContent,/<img src=x/);
  assert.equal(h.node('events').children[1].dataset.severity,'critical');
  await h.c.cmPhysicalAi.reset({runs:[runData({run_id:id2,start:{robot_type:'asimov_1'},observation:null})],events:{}});
  assert.match(h.node('source').textContent,/Asimov 1/);
  assert.equal(h.node('margin').textContent,'Not reported');
  assert.equal(h.node('task').textContent,'Not reported');
  h=harness({runs:[runData(),runData({run_id:id2,robot_id:'requested-robot'})],events:{}},'?run='+id2);
  await h.c.cmPhysicalAi.start();
  assert.equal(h.node('robot').textContent,'requested-robot','an incident deep link opens the requested run');
  h=harness({runs:[runData()],events:{}},'?run='+id2);
  await h.c.cmPhysicalAi.start();
  assert.equal(h.c.cmPhysicalAi.getState().selected,null,'a missing requested run never silently selects a different robot');
  assert.equal(h.node('detail').hidden,true);
  assert.equal(h.node('workbench').hidden,false,'the run rail remains available to choose or load older runs');
  assert.match(h.node('message').textContent,/requested run is not in this evidence window/);
  await h.c.cmPhysicalAi.select(id);
  assert.equal(h.node('robot').textContent,'my-jumper');
  h=harness({runs:[runData()],events:{}},'?run=invalid');await h.c.cmPhysicalAi.start();
  assert.equal(h.c.cmPhysicalAi.getState().selected,id,'invalid run query is ignored');
  const jumper=runData({start:{robot_type:'jumper'}});
  const asimov=runData({run_id:id2,robot_id:'my-asimov',start:{robot_type:'asimov_1'}});
  h=harness({runs:[jumper,asimov],events:{[id]:events,[id2]:[]}},'?hardware=jumper');
  await h.c.cmPhysicalAi.start();
  assert.equal(h.node('runs').children.length,1,'Hardware filters recorded runs');
  assert.equal(h.node('robot').textContent,'my-jumper');
  assert.equal(h.node('hardware').value,'jumper');
  await h.c.cmPhysicalAi.setHardware('asimov_1');
  assert.equal(h.node('runs').children.length,1);
  assert.equal(h.node('robot').textContent,'my-asimov');
  assert.equal(h.c.cmPhysicalAi.getState().events.length,0,'changing Hardware clears previous robot events');
  assert.equal(h.requests.length,0,'filtering decrypted data does not fetch a local API');
  await h.c.cmPhysicalAi.setHardware('all');
  assert.equal(h.node('runs').children.length,2);
  h=harness({runs:[asimov],events:{}},'?hardware=jumper');
  await h.c.cmPhysicalAi.start();
  assert.equal(h.c.cmPhysicalAi.getState().selected,null,'a hardware filter never silently opens another robot');
  assert.equal(h.node('filter-empty').hidden,false);
  assert.equal(h.node('detail').hidden,true);
  h=harness({runs:[jumper,asimov],events:{}},'?hardware=jumper&run='+id2);
  await h.c.cmPhysicalAi.start();
  assert.equal(h.c.cmPhysicalAi.getState().selected,null,'a deep link cannot bypass its hardware filter');
  console.log('Physical AI UI evidence, hardware selection and polling checks passed');
}
run().catch(error=>{console.error(error);process.exitCode=1;});
