/* Focused offline contract and lifecycle checks. No browser dependency. */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const source = fs.readFileSync(require('node:path').join(__dirname, '../clawmetry/static/js/node-activity.js'), 'utf8');
function harness() {
  const listeners = {}, timers = new Map(), delays = new Map(), requests = [], nodes = new Map(); let seq = 0;
  let now=Date.now();class ClockDate extends Date {static now(){return now;}}
  const context = {
    document: {hidden: false, activeElement: null, getElementById: id => nodes.get(id) || null,
      querySelectorAll: () => [], addEventListener: (name, fn) => {listeners[name] = fn;}},
    AbortController, Date:ClockDate, JSON, Number, String, Array, Object, Promise, console,
    localStorage: {getItem: () => null},
    setTimeout: (fn,delay) => {timers.set(++seq, fn);delays.set(seq,delay); return seq;}, clearTimeout: id => timers.delete(id),
    fetch: (url, opts) => new Promise((resolve,reject) => requests.push({url, opts, resolve,reject})),
    _cmCurrentTab: 'node-activity', matchMedia: () => ({matches: true}),
    addEventListener: (name, fn) => {listeners[name] = fn;}
  };
  context.window = context; vm.createContext(context); vm.runInContext(source, context);
  const payload = (name, events = []) => ({available: true, node: {hostname: name}, collected_at: ClockDate.now(),
    summary: {cpu_percent: null, process_count: null}, samples: [], coverage: {}, preferences: {}, events});
  const answer = (request, body, ok = true) => request.resolve({ok, json: async () => body});
  return {context, requests, timers, delays, listeners, nodes, payload, answer,advance:ms=>{now+=ms;}};
}
async function run() {
  let h = harness(), c = h.context;
  assert.equal(c.cmNodeActivity.number(null), 'Unknown');
  assert.equal(c.cmNodeActivity.number(undefined), 'Unknown');
  assert.equal(c.cmNodeActivity.number(0, '%'), '0%');
  assert.equal(c.cmNodeActivity.bytes(null), 'Unknown');
  assert.equal(c.cmNodeActivity.actor({kind: 'unknown', label: 'Trusted human'}).label, 'Unattributed');
  assert.equal(c.cmNodeActivity.actor({kind: 'attacker', label: 'attacker'}).kind, 'unattributed');
  assert.equal(c.cmNodeActivity.reducedMotion(), true);
  const points = {};
  h.nodes.set('test-spark', {querySelector: () => ({setAttribute: (name, value) => {points[name] = value;}})});
  c.cmNodeActivity.spark('test-spark', [{cpu_percent:null},{cpu_percent:10},{cpu_percent:20}], 'cpu_percent');
  assert.equal(points.points, '80.0,23.0 160.0,2.0', 'warm-up gaps do not hide later measured history');
  c.cmNodeActivity.spark('test-spark', [{cpu_percent:10},{cpu_percent:null},{cpu_percent:20},{cpu_percent:30}], 'cpu_percent');
  assert.equal(points.points, '106.7,23.0 160.0,2.0', 'a gap is never bridged with an invented segment');
  const samples = [{observed_at: 1000, cpu_percent: 11}, {observed_at: 3000, cpu_percent: 33}];
  assert.equal(c.cmNodeActivity.sampleForEvent({observed_at: 2000}, samples).cpu_percent, 11);
  assert.equal(c.cmNodeActivity.sampleForEvent({observed_at: 3000}, samples).cpu_percent, 33);
  assert.equal(c.cmNodeActivity.sampleForEvent({observed_at: 500}, samples), null, 'future measurements never describe an earlier event');
  const p1 = c.loadNodeActivity(); c.loadNodeActivity();
  assert.equal(h.requests.length, 1, 'in-flight requests must deduplicate');
  h.answer(h.requests[0], h.payload('first')); await p1;
  assert.equal(c.cmNodeActivity.getState().data.node.hostname, 'first');
  assert.equal(h.timers.size, 1, 'one scheduled refresh');
  await c.loadNodeActivity(); assert.equal(h.requests.length, 1, 'fresh data is reused');
  c.nodeActivityStop(); assert.equal(h.timers.size, 0);
  c._cmCurrentTab = 'guard'; await c.loadNodeActivity();
  assert.equal(h.requests.length, 1, 'off-tab loading is gated');

  h = harness(); c = h.context;
  const old = c.loadNodeActivity();
  const oldReadDeadline=c.cmNodeActivity.getState().readRequest.timeout;
  c.CLOUD_MODE = true; c.CLOUD_NODE_ID = 'new-node';
  const fresh = c.loadNodeActivity();
  assert.equal(h.requests.length, 2); assert.equal(h.requests[0].opts.signal.aborted, true);
  assert.equal(h.timers.has(oldReadDeadline),false,'switching nodes removes the obsolete read deadline');
  assert.notEqual(c.cmNodeActivity.getState().readRequest.timeout,oldReadDeadline);
  h.answer(h.requests[1], h.payload('new')); await fresh;
  h.answer(h.requests[0], h.payload('old')); await old;
  assert.equal(c.cmNodeActivity.getState().data.node.hostname, 'new', 'old node responses cannot paint');
  c.document.hidden = true; h.listeners.visibilitychange();
  assert.equal(h.timers.size, 0, 'hidden pages stop timers');
  await c.loadNodeActivity(); assert.equal(h.requests.length, 2);

  h = harness(); c = h.context;
  const pending = c.loadNodeActivity(); c.nodeActivityStop();
  h.answer(h.requests[0], h.payload('late')); await pending;
  assert.equal(c.cmNodeActivity.getState().data, null, 'responses after stop cannot paint');
  assert.equal(h.timers.size, 0, 'stopped responses cannot restart polling');

  h = harness(); c = h.context;
  const load = c.loadNodeActivity();
  h.answer(h.requests[0], h.payload('ordered', [
    {id: 'new', observed_at: 3000}, {id: 'old', observed_at: 1000}, {id: 'mid', observed_at: 2000}
  ])); await load;
  assert.equal(c.cmNodeActivity.getState().selected, 'new', 'replay selection begins at latest chronological event');
  const oldFinding={id:'retained-finding',observed_at:1,finding:true};
  c.cmNodeActivity.getState().data.events=[oldFinding,...Array.from({length:150},(_,i)=>({id:'routine-'+i,observed_at:i+2}))];
  c.cmNodeActivity.select(oldFinding.id,false);
  assert.equal(c.cmNodeActivity.getState().selected,oldFinding.id,'retained findings remain selectable beyond the Observe preview');
  c.cmNodeActivity.play();
  assert.notEqual(c.cmNodeActivity.getState().replay,null,'user-triggered replay schedules recorded events');
  c.document.hidden=true;h.listeners.visibilitychange();
  assert.equal(c.cmNodeActivity.getState().replay,null,'hidden pages stop replay as well as collection polling');
  assert.equal(c.cmNodeActivity.getState().selected,oldFinding.id,'stopping replay retains the selected evidence');

  h=harness();c=h.context;
  const initial=c.loadNodeActivity();h.answer(h.requests[0],h.payload('write-node'));await initial;
  const write=c.cmNodeActivity.mutate('preferences',{enabled:false},'unused-message');
  assert.ok(h.requests[1].opts.signal,'writes must pass a signal through to the hosted bridge');
  c.document.hidden=true;h.listeners.visibilitychange();
  assert.equal(h.requests[1].opts.signal.aborted,true,'leaving a view aborts mutation confirmation polling');
  assert.equal(h.timers.size,0,'leaving clears the write deadline and poll timers');
  assert.match(c.cmNodeActivity.getState().unconfirmed.message,/may still apply/,'aborting confirmation does not claim to undo a queued change');
  // A fetch implementation that settles late cannot clear a new node's write.
  c.document.hidden=false;
  c.CLOUD_MODE=true;c.CLOUD_NODE_ID='other-node';
  const other=c.loadNodeActivity();h.answer(h.requests[2],h.payload('other'));await other;
  const newWrite=c.cmNodeActivity.mutate('preferences',{enabled:true},'unused-message');
  const newer=c.cmNodeActivity.getState().mutationRequest;
  h.answer(h.requests[1],{ok:true,saved:true});await write;
  assert.equal(c.cmNodeActivity.getState().mutationRequest,newer,'obsolete finally cannot clear a newer mutation');
  assert.equal(c.cmNodeActivity.getState().mutation,true);
  assert.match(c.cmNodeActivity.getState().unconfirmed.message,/not confirmed/,'late success cannot clear an unconfirmed old write');
  c.nodeActivityStop();h.requests[3].reject(Object.assign(new Error('aborted'),{name:'AbortError'}));await newWrite;

  h=harness();c=h.context;
  const timeoutWrite=c.cmNodeActivity.mutate('reviews',{event_id:'event',decision:'expected',reason:''},'unused-message');
  const deadline=c.cmNodeActivity.getState().mutationRequest.timeout;
  assert.equal(h.delays.get(deadline),45000,'confirmation wait has a fixed overall deadline');
  h.timers.get(deadline)();
  assert.equal(h.requests[0].opts.signal.aborted,true,'the overall confirmation deadline aborts a stalled network request');
  h.requests[0].reject(Object.assign(new Error('aborted'),{name:'AbortError'}));await timeoutWrite;
  assert.equal(c.cmNodeActivity.getState().mutation,false);
  assert.match(c.cmNodeActivity.getState().unconfirmed.message,/Refresh this node/);

  h=harness();c=h.context;
  const confirmed=c.cmNodeActivity.mutate('preferences',{enabled:true},'unused-message');
  const confirmedDeadline=c.cmNodeActivity.getState().mutationRequest.timeout;
  h.answer(h.requests[0],{ok:true,saved:true});
  for(let index=0;index<20&&h.requests.length<2;index++)await Promise.resolve();
  assert.equal(h.timers.has(confirmedDeadline),false,'confirmed persistence clears its deadline before refresh completes');
  assert.equal(c.cmNodeActivity.getState().mutationRequest,null);
  assert.equal(h.requests.length,2,'confirmed persistence starts a separate readback request');
  h.answer(h.requests[1],h.payload('confirmed'));await confirmed;
  assert.equal(c.cmNodeActivity.getState().unconfirmed,null,'a delayed refresh cannot revoke a persistence confirmation');

  h=harness();c=h.context;
  const obsolete=c.cmNodeActivity.mutate('preferences',{enabled:false},'unused-message');
  c.nodeActivityStop();c.CLOUD_MODE=true;c.CLOUD_NODE_ID='current';
  const current=c.cmNodeActivity.mutate('preferences',{enabled:true},'unused-message');
  const currentDeadline=c.cmNodeActivity.getState().mutationRequest.timeout;
  h.timers.get(currentDeadline)();
  const currentNotice=c.cmNodeActivity.getState().unconfirmed;
  h.requests[0].reject(Object.assign(new Error('late abort'),{name:'AbortError'}));await obsolete;
  assert.equal(c.cmNodeActivity.getState().unconfirmed,currentNotice,'obsolete AbortError cannot overwrite a newer node warning');
  h.requests[1].reject(Object.assign(new Error('timeout'),{name:'AbortError'}));await current;

  h=harness();c=h.context;
  const prior=c.loadNodeActivity();h.answer(h.requests[0],h.payload('prior'));await prior;
  c.CLOUD_MODE=true;c.CLOUD_NODE_ID='new-selection';
  await c.cmNodeActivity.mutate('preferences',{enabled:false},'unused-message');
  assert.equal(h.requests.length,2);
  assert.equal(h.requests[1].url,'/api/node-activity?limit=100','an old node form triggers a fresh read, never a write to the new node');
  assert.equal(c.cmNodeActivity.getState().mutation,false);
  h.answer(h.requests[1],h.payload('new-selection'));await c.loadNodeActivity();

  h=harness();c=h.context;
  const freshness={textContent:'',parentNode:{dataset:{}}},readStatus={textContent:'',dataset:{}};
  h.nodes.set('na-freshness',freshness);h.nodes.set('na-status',readStatus);
  const firstRead=c.loadNodeActivity();h.answer(h.requests[0],h.payload('read-node'));await firstRead;
  assert.equal(freshness.parentNode.dataset.fresh,'true');
  h.advance(130000);h.timers.get(c.cmNodeActivity.getState().timer)();
  const stalled=c.cmNodeActivity.getState().pending,readDeadline=c.cmNodeActivity.getState().readRequest.timeout;
  assert.equal(h.delays.get(readDeadline),15000,'read deadlines are independent from the 45-second write deadline');
  h.advance(15000);h.timers.get(readDeadline)();
  assert.equal(h.requests[1].opts.signal.aborted,true,'a hanging GET is aborted at the read deadline');
  assert.equal(freshness.parentNode.dataset.fresh,'false','timeout recomputes freshness from the last real observation');
  assert.match(freshness.textContent,/stale/);
  assert.match(readStatus.textContent,/did not respond in time/);
  h.requests[1].reject(Object.assign(new Error('aborted'),{name:'AbortError'}));await stalled;
  assert.equal(c.cmNodeActivity.getState().pending,null);
  assert.equal(h.timers.has(readDeadline),false);
  assert.notEqual(c.cmNodeActivity.getState().timer,null,'a timed-out read schedules recovery');
  h.timers.get(c.cmNodeActivity.getState().timer)();
  const recovered=c.cmNodeActivity.getState().pending;
  h.answer(h.requests[2],h.payload('recovered-node'));await recovered;
  assert.equal(c.cmNodeActivity.getState().data.node.hostname,'recovered-node');
  assert.equal(freshness.parentNode.dataset.fresh,'true','a later valid read restores actual freshness');
  h.advance(130000);h.timers.get(c.cmNodeActivity.getState().timer)();
  const failed=c.cmNodeActivity.getState().pending;
  h.requests[3].reject(new Error('The node connection is unavailable.'));await failed;
  assert.match(freshness.textContent,/stale/,'ordinary connection errors also age retained evidence');
  assert.equal(freshness.parentNode.dataset.fresh,'false');
  assert.match(readStatus.textContent,/connection is unavailable/);
  h=harness();c=h.context;
  const processTable={innerHTML:''},listenerTable={innerHTML:''},coverage={innerHTML:''};
  const processAge={textContent:''},listenerAge={textContent:''},mixedStatus={textContent:'',dataset:{}};
  h.nodes.set('na-processes',processTable);h.nodes.set('na-listeners',listenerTable);h.nodes.set('na-coverage',coverage);
  h.nodes.set('na-process-observation-note',processAge);h.nodes.set('na-listener-observation-note',listenerAge);h.nodes.set('na-status',mixedStatus);
  const mixed=h.payload('mixed-observations');
  mixed.processes=[{pid:31,name:'current-worker',observed_at:mixed.collected_at,stale:false},
    {pid:32,name:'previous-worker',observed_at:mixed.collected_at-300000,stale:true},
    {pid:33,name:'legacy-worker',observed_at:null,stale:true}];
  mixed.listeners=[{pid:32,address:'127.0.0.1',port:8123,observed_at:mixed.collected_at-300000,stale:true}];
  mixed.coverage={processes:{state:'partial',reason:'Collection limit reached.',scope:'account',sighting_history_limited:true}};
  const mixedRead=c.loadNodeActivity();h.answer(h.requests[0],mixed);await mixedRead;
  assert.match(processTable.innerHTML,/Observed [^<]+/,'fresh rows show their own positive observation time');
  assert.match(processTable.innerHTML,/Stale observation; last observed /,'retained evidence preserves its own last observation time');
  assert.match(processTable.innerHTML,/Observation time unknown/,'legacy missing times are not replaced with the latest scan time');
  assert.match(listenerTable.innerHTML,/Stale observation; last observed /);
  assert.match(processAge.textContent,/Includes stale observations/,'mixed inventory headings do not claim every row is current');
  assert.match(listenerAge.textContent,/Includes stale observations/);
  assert.match(coverage.innerHTML,/Process sighting history is limited/,'the explicit history limit is visible independently of the collection reason');
  assert.match(mixedStatus.textContent,/Process sighting history is incomplete/);
  assert.equal(mixed.processes[1].observed_at,mixed.collected_at-300000,'rendering does not refresh stale evidence timestamps');
  // AC-OBS-NODE-CLARITY-001.1 / 001.2: positive counts are not exact totals or stale rows.
  h=harness();c=h.context;
  const processCount={textContent:''},processCountNote={textContent:''},listenerCount={textContent:''};
  h.nodes.set('na-process-count',processCount);h.nodes.set('na-process-note',processCountNote);
  h.nodes.set('na-listener-count',listenerCount);
  const bounded=h.payload('bounded');bounded.summary={process_count:null,listening_port_count:null};
  bounded.coverage={processes:{state:'partial',count:512,truncated:true},listeners:{state:'unavailable',count:0,reason:'Permission denied.'}};
  bounded.processes=[{pid:1,stale:true,observed_at:bounded.collected_at-90000}];
  const boundedRead=c.loadNodeActivity();h.answer(h.requests[0],bounded);await boundedRead;
  assert.equal(processCount.textContent,'512','show the recorded positive count even when the exact total is not known');
  assert.match(processCountNote.textContent,/total.*not known/i);
  assert.equal(listenerCount.textContent,'Unavailable','permission failure cannot become zero listeners');
  const cases=[
    [{state:'complete',count:0},'0'],
    [{state:'partial',count:0},'0'],
    [{state:'disabled',count:99},'Off'],
    [{state:'unsupported',count:99},'Not supported'],
    [{state:'unavailable',count:99},'Unavailable']
  ];
  for(const [coverage,expected] of cases){
    const state=h.payload('counts');state.coverage={processes:coverage};
    h.advance(15001);h.timers.get(c.cmNodeActivity.getState().timer)();
    const pending=c.cmNodeActivity.getState().pending;h.answer(h.requests.at(-1),state);await pending;
    assert.equal(processCount.textContent,expected);
  }
  // Legacy totals cannot become current observations without complete source coverage.
  for(const legacyCoverage of [{state:'partial'},{}]){
    const legacy=h.payload('legacy-count');legacy.summary={process_count:42};
    legacy.coverage={processes:legacyCoverage};
    legacy.processes=[{pid:42,stale:true,observed_at:legacy.collected_at-90000}];
    h.advance(15001);h.timers.get(c.cmNodeActivity.getState().timer)();
    const pending=c.cmNodeActivity.getState().pending;h.answer(h.requests.at(-1),legacy);await pending;
    assert.equal(processCount.textContent,'Not measured','a legacy total and stale rows do not establish a current count');
    legacy.processes=[{pid:43,stale:false,observed_at:legacy.collected_at}];
    h.advance(15001);h.timers.get(c.cmNodeActivity.getState().timer)();
    const current=c.cmNodeActivity.getState().pending;h.answer(h.requests.at(-1),legacy);await current;
    assert.equal(processCount.textContent,'1','timestamped positive current evidence remains usable');
  }
  // AC-OBS-NODE-CLARITY-004.1 / 004.2: primary prose tells the story; original detail remains disclosed.
  h=harness();c=h.context;
  const eventBox={innerHTML:'',dataset:{},classList:{remove(){},add(){}},querySelectorAll:()=>[]};
  h.nodes.set('na-evidence',eventBox);
  const story=h.payload('my-machine',[{id:'observed-gh',observed_at:Date.now(),kind:'process_observed',
    title:'A process was first observed',detail:'Original partial-scan qualification.',
    process:{name:'gh',pid:31},target:{label:'gh',kind:'processes'},actor:{kind:'unknown',label:'Trusted human'},
    before:null,after:{name:'gh',pid:31},evidence:['Original source evidence.']}]);
  const storyRead=c.loadNodeActivity();h.answer(h.requests[0],story);await storyRead;
  assert.match(eventBox.innerHTML,/gh was seen running/);
  assert.match(eventBox.innerHTML,/Who started it/);
  assert.match(eventBox.innerHTML,/Not identified/);
  assert.doesNotMatch(eventBox.innerHTML,/Trusted human/,'unverified actor labels must not become identity claims');
  assert.match(eventBox.innerHTML,/<details[^>]*class="na-technical"/);
  assert.match(eventBox.innerHTML,/Original partial-scan qualification/);
  assert.match(eventBox.innerHTML,/Original source evidence/);
  assert.equal(eventBox.dataset.eventId,'observed-gh');
  h=harness();c=h.context;
  const measuredTable={innerHTML:''},emptyPorts={innerHTML:''};
  h.nodes.set('na-processes',measuredTable);h.nodes.set('na-listeners',emptyPorts);
  const measured=h.payload('measured');measured.node.platform='Darwin';
  measured.processes=[{pid:11,name:'multicore-worker',cpu_percent:125,cpu_interval_seconds:30,memory_bytes:1234,observed_at:measured.collected_at,stale:false},
    {pid:12,name:'idle-worker',cpu_percent:0,cpu_interval_seconds:30,observed_at:measured.collected_at,stale:false},
    {pid:13,name:'new-worker',cpu_percent:null,cpu_reason:'Needs two comparable observations.',observed_at:measured.collected_at,stale:false}];
  measured.coverage={listeners:{state:'unavailable',reason:'Permission denied.'}};
  const measuredRead=c.loadNodeActivity();h.answer(h.requests[0],measured);await measuredRead;
  assert.match(measuredTable.innerHTML,/125%/,'multicore process usage is not capped at100');
  assert.match(measuredTable.innerHTML,/Over 30s/);
  assert.match(measuredTable.innerHTML,/>0%</,'an actually measured idle interval stays zero');
  assert.match(measuredTable.innerHTML,/Needs two comparable observations/);
  assert.match(emptyPorts.innerHTML,/macOS did not allow/);
  assert.match(emptyPorts.innerHTML,/View coverage/);
  assert.doesNotMatch(emptyPorts.innerHTML,/No TCP listening ports were observed/,'denial is not a complete measured zero');

  h=harness();c=h.context;
  const handlers={},root={addEventListener:(name,fn)=>{handlers[name]=fn;}};
  h.nodes.set('page-node-activity',root);
  for(const id of ['na-processes','na-process-results','na-clawmetry-processes','na-clawmetry-note'])h.nodes.set(id,{innerHTML:'',textContent:''});
  const input={id:'na-process-search',value:'',focus:()=>{}};
  h.nodes.set(input.id,input);
  for(const id of ['na-process-clear','na-process-prev','na-process-next'])h.nodes.set(id,{id,disabled:true,hasAttribute:()=>false,dataset:{}});
  function click(id){handlers.click({target:{closest:()=>h.nodes.get(id)}});}
  function search(value){input.value=value;handlers.input({target:input});}
  const inventory=h.payload('search-node');
  inventory.processes=Array.from({length:205},(_,i)=>({name:'worker-'+i,pid:i+1,cpu_percent:205-i,stale:false,observed_at:inventory.collected_at}));
  inventory.processes.push({name:'python3.12',pid:9876,clawmetry_role:'collector',cpu_percent:0,cpu_interval_seconds:30,memory_bytes:1048576,observed_at:inventory.collected_at,stale:false});
  const read=c.loadNodeActivity();h.answer(h.requests[0],inventory);await read;
  const searchTable=h.nodes.get('na-processes'),selfTable=h.nodes.get('na-clawmetry-processes');
  assert.doesNotMatch(searchTable.innerHTML,/worker-204/);
  assert.match(h.nodes.get('na-process-results').textContent,/1 to 100 of 206/);
  assert.match(selfTable.innerHTML,/ClawMetry Collector/,'own usage is independent of the visible process page');
  assert.match(selfTable.innerHTML,/>0%</,'zero CPU is measured, not missing');
  assert.match(selfTable.innerHTML,/1 MB/);
  click('na-process-next');click('na-process-next');
  assert.match(searchTable.innerHTML,/worker-204/,'pagination exposes rows beyond the first hundred');
  assert.equal(h.nodes.get('na-process-next').disabled,true);
  search('WORKER-204');
  assert.match(searchTable.innerHTML,/worker-204/,'case-insensitive search happens before the page cap');
  assert.match(h.nodes.get('na-process-results').textContent,/1 to 1 of 1/);
  search('9876');assert.match(searchTable.innerHTML,/ClawMetry Collector/);
  search('clawmetry');assert.match(searchTable.innerHTML,/python3.12/);
  const refreshed=c.cmNodeActivity.getState().timer;h.timers.get(refreshed)();
  const reloading=c.cmNodeActivity.getState().pending;h.answer(h.requests[1],inventory);await reloading;
  assert.equal(input.value,'clawmetry','refresh preserves the focused search field');
  assert.match(searchTable.innerHTML,/ClawMetry Collector/);
  assert.doesNotMatch(searchTable.innerHTML,/worker-/,'refresh reapplies the search');
  search('<img src=x onerror=alert(1)>');
  assert.match(searchTable.innerHTML,/No matching processes/);
  assert.doesNotMatch(searchTable.innerHTML,/<img/);
  assert.equal(h.requests.length,2,'all searches and pagination use cached observations');
  click('na-process-clear');
  assert.equal(input.value,'');assert.match(h.nodes.get('na-process-results').textContent,/1 to 100 of 206/);
  inventory.processes[205].stale=true;
  h.timers.get(c.cmNodeActivity.getState().timer)();
  const staleRead=c.cmNodeActivity.getState().pending;h.answer(h.requests[2],inventory);await staleRead;
  assert.match(h.nodes.get('na-clawmetry-note').textContent,/stale/);
  assert.match(selfTable.innerHTML,/Stale observation/);
  search('clawmetry');c.CLOUD_MODE=true;c.CLOUD_NODE_ID='another';
  const newNode=c.loadNodeActivity();
  assert.equal(input.value,'','switching nodes clears the old search');
  h.answer(h.requests[3],h.payload('old-collector'));await newNode;
  assert.match(selfTable.innerHTML,/updated collector/,'old snapshots provide upgrade guidance without an invented total');
  assert.doesNotMatch(selfTable.innerHTML,/0%/);
  h=harness();c=h.context;
  h.nodes.set('na-live-state',{textContent:'',dataset:{}});
  h.nodes.set('na-processes',{innerHTML:''});
  const fullRead=c.loadNodeActivity();h.answer(h.requests[0],h.payload('live-node'));await fullRead;
  assert.equal(h.delays.get(c.cmNodeActivity.getState().timer),2000,'live refresh uses one two-second timer');
  const savedFull=c.cmNodeActivity.getState().data;
  c.cmNodeActivity.getState().processQuery='clawmetry';
  for(let i=0;i<2;i++){
    h.advance(2000);h.timers.get(c.cmNodeActivity.getState().timer)();
    assert.equal(h.requests[i+1].url,'/api/node-activity?live=1');
    const frame=Object.assign(h.payload('live-node'),{live:true,processes:[{pid:99,name:'python3',clawmetry_role:'collector',cpu_percent:12+i,memory_bytes:1048576,observed_at:c.Date.now()}]});
    const pending=c.cmNodeActivity.getState().pending;h.answer(h.requests[i+1],frame);await pending;
    assert.equal(c.cmNodeActivity.getState().data,savedFull,'live frames do not refetch or replace event history');
    assert.match(h.nodes.get('na-processes').innerHTML,new RegExp((12+i)+'%'));
    assert.equal(c.cmNodeActivity.getState().processQuery,'clawmetry');
  }
  assert.match(h.nodes.get('na-live-state').textContent,/Live/);
  assert.equal(h.nodes.get('na-live-state').dataset.live,'true');
  c.document.hidden=true;h.listeners.visibilitychange();assert.equal(h.timers.size,0,'hidden pages stop the live loop');
  console.log('Node activity JS contracts and lifecycle passed.');
}
run().catch(error => {console.error(error); process.exit(1);});
