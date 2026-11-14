/* Node observations are persisted evidence. No host collection runs here. */
(function () {
  'use strict';
  var state = {data:null, scope:null, generation:0, pending:null, controller:null, timer:null,
    replay:null, selected:null, view:'observe', lastLoaded:0, bound:false, mutation:false,
    mutationRequest:null, unconfirmed:null, readRequest:null, processQuery:'', processPage:0, liveData:null, liveUnsupported:false, liveMisses:0, liveStarted:Date.now()};
  var PROCESS_ROLES={collector:'Collector',dashboard:'Dashboard',desktop:'Desktop app',cli:'CLI'};
  var UNCONFIRMED='Save not confirmed. The change may still apply. Refresh this node before you retry.';
  var PREFS = [
    ['enabled','Node monitoring','Collect node observations. Turn this off to stop all collection.'],
    ['processes','Processes','Record bounded process identity and resource observations.'],
    ['listeners','Listening ports','Record listeners and their process ownership where available.'],
    ['sensitive_files','Selected settings','Compare fingerprints of selected access and startup settings. File contents are not shown.'],
    ['rule_new_listener','Review new listeners','Include newly observed listeners in the Guard view.'],
    ['rule_sensitive_change','Review setting changes','Include changes to selected settings in the Guard view.']
  ];
  var COVERAGE_LABELS = {resources:'Resource measurements',processes:'Processes',listeners:'Listening ports',
    sensitive_files:'Selected settings',logins:'Login sessions'};
  function el(id) { return document.getElementById(id); }
  function esc(value) { return String(value == null ? '' : value).replace(/[&<>"']/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c];}); }
  function text(id, value) { var node=el(id); if(node) node.textContent=String(value == null ? 'Unknown' : value); }
  function finite(value) { return typeof value === 'number' && Number.isFinite(value); }
  function number(value,suffix) { return finite(value) ? value.toLocaleString(undefined,{maximumFractionDigits:1})+(suffix||'') : 'Unknown'; }
  function bytes(value) { if(!finite(value)) return 'Unknown'; var gb=value/1073741824; return gb>=1 ? number(gb,' GB') : number(value/1048576,' MB'); }
  function epoch(value) { if(finite(value)) return value < 1e11 ? value*1000 : value; var result=Date.parse(value); return Number.isFinite(result)?result:null; }
  function when(value) { var ms=epoch(value); return ms == null?'Time not recorded':new Date(ms).toLocaleString(undefined,{month:'short',day:'numeric',hour:'2-digit',minute:'2-digit',second:'2-digit'}); }
  function age(value) { var ms=epoch(value); if(ms==null)return 'Observation time unavailable'; var seconds=Math.max(0,Math.floor((Date.now()-ms)/1000)); return seconds<60?'Observed '+seconds+'s ago':seconds<3600?'Observed '+Math.floor(seconds/60)+'m ago':'Observed '+Math.floor(seconds/3600)+'h ago'; }
  function active() { return window._cmCurrentTab === 'node-activity' && !document.hidden; }
  function scope() {
    var key='';
    try { if(window.CLOUD_MODE) key=localStorage.getItem('cm-enc-key-'+(window.CLOUD_NODE_ID||'')+'-'+(window.CLOUD_TOKEN||'').slice(0,16))||''; } catch(e) {}
    return JSON.stringify([!!window.CLOUD_MODE,window.CLOUD_NODE_ID||'',window.CLOUD_TOKEN||'',key]);
  }
  function valid(generation,key) { return active() && state.generation===generation && scope()===key; }
  function actor(value) {
    value=value||{};
    var kind=value.kind==='agent'?'agent':value.kind==='human'?'human':'unattributed';
    return {kind:kind,label:kind==='unattributed'?'Unattributed':(value.label||(kind==='agent'?'Agent':'Human session')),
      evidence:Array.isArray(value.evidence)?value.evidence.join('; '):(value.evidence||''),runtime:value.runtime,session_id:value.session_id};
  }
  function events() { return ((state.data||{}).events||[]).filter(function(e){return e&&e.id!=null;}).slice(0,2000).sort(function(a,b){return (epoch(a.observed_at)||0)-(epoch(b.observed_at)||0)||String(a.id).localeCompare(String(b.id));}); }
  function writable(name) { var data=state.data||{}, caps=data.capabilities||{};return data[name]!==false&&caps[name]!==false; }
  function selected() { var rows=events(); return rows.find(function(e){return String(e.id)===String(state.selected);})||null; }
  function sampleForEvent(event,samples) {
    var eventTime=event&&epoch(event.observed_at);if(eventTime==null)return null;
    return (samples||[]).filter(function(sample){var at=epoch(sample.observed_at);return at!=null&&at<=eventTime;})
      .sort(function(a,b){return epoch(b.observed_at)-epoch(a.observed_at);})[0]||null;
  }
  function resourceEvidence(event) {
    var sample=sampleForEvent(event,(state.data||{}).samples);
    if(!sample)return '<div class="na-resource-history"><strong>Resource history at this event</strong><p>No retained resource measurement precedes this event. Usage at this time is unknown.</p></div>';
    return '<div class="na-resource-history"><strong>Resource history at this event</strong><p>'+esc(epoch(sample.observed_at)===epoch(event.observed_at)?'Measured with this event':'Last retained measurement before this event')+'<br>'+esc(when(sample.observed_at))+'</p><div><span>CPU <b>'+esc(number(sample.cpu_percent,'%'))+'</b></span><span>Memory <b>'+esc(bytes(sample.memory_used_bytes))+'</b></span></div><small>Recorded measurement. Values between collections are unknown.</small></div>';
  }
  function status(message,tone) { text('na-status',message); if(el('na-status'))el('na-status').dataset.tone=tone||''; }
  function observedCount(data,source,totalKey) {
    var coverage=(data.coverage||{})[source]||{}, rows=Array.isArray(data[source])?data[source]:[];
    var label=source==='processes'?'processes':'listening ports', count=null;
    if(data.available===false)return {value:'No data',note:'No recorded collection is available.'};
    if(coverage.state==='disabled')return {value:'Off',note:'Collection is turned off in Govern.'};
    if(coverage.state==='unsupported')return {value:'Not supported',note:'This source is not supported on this system.'};
    if(coverage.state==='unavailable')return {value:'Unavailable',note:sourceReason(data,source)};
    function validCount(n){return Number.isSafeInteger(n)&&n>=0;}
    if(['complete','partial'].includes(coverage.state)&&validCount(coverage.count))count=coverage.count;
    else if(coverage.state==='complete'&&validCount((data.summary||{})[totalKey]))count=data.summary[totalKey];
    else {
      var at=epoch(data.collected_at), current=rows.filter(function(r){return r.stale===false&&at!=null&&epoch(r.observed_at)===at;});
      if(current.length)count=current.length;
    }
    if(count==null)return {value:'Not measured',note:'No current '+label+' count was recorded.'};
    var exact=coverage.state==='complete'&&(data.summary||{})[totalKey]===count;
    var stale=epoch(data.collected_at)==null||Date.now()-epoch(data.collected_at)>(data.stale_after_seconds||120)*1000;
    return {value:count.toLocaleString(),note:stale?'Last recorded count. This observation is stale.':
      exact?'At the last collection.':'Observed in this scan; total is not known.'};
  }
  function sourceReason(data,source) {
    var c=(data.coverage||{})[source]||{}, reason=c.reason||c.detail||'';
    if(/permission|denied/i.test(reason))return (data.node||{}).platform==='Darwin'?
      'macOS did not allow this collector to read this source.':'The operating system did not permit this collection.';
    if(c.state==='disabled')return 'Collection is turned off. You can change this in Govern.';
    if(c.state==='unsupported')return 'This collection is not supported on this system.';
    return reason||'The collector has not reported this source yet.';
  }
  function emptyInventory(data,source) {
    var c=(data.coverage||{})[source]||{}, name=source==='processes'?'processes':'TCP listening ports', message;
    if(c.state==='complete')message='No '+name+' were observed at the last collection.';
    else if(c.state==='partial')message='No '+name+' were visible in this scan. Others may still exist.';
    else if(c.state==='disabled')message='Collection is turned off for '+name+'.';
    else message='There are no recorded '+name+' to show.';
    return '<div class="na-empty"><p>'+esc(message)+'</p><p>'+esc(sourceReason(data,source))+'</p><button type="button" data-na-coverage>View coverage</button></div>';
  }
  function summary(data) {
    var s=data.summary||{}, at=epoch(data.collected_at), stale=at==null||Date.now()-at>(data.stale_after_seconds||120)*1000;
    text('na-node-name',(data.node||{}).hostname||(data.node||{}).id||'This node');
    text('na-freshness',age(data.collected_at)+(stale?' (stale)':''));
    var freshness=el('na-freshness'); if(freshness&&freshness.parentNode)freshness.parentNode.dataset.fresh=String(!stale);
    text('na-cpu',number(s.cpu_percent,'%')); text('na-memory',bytes(s.memory_used_bytes));
    var samples=data.samples||[], cpuGap=samples.some(function(v){return !finite(v.cpu_percent);}), memoryGap=samples.some(function(v){return !finite(v.memory_used_bytes);});
    text('na-cpu-note','Node total'+(cpuGap?'. History has gaps.':''));
    text('na-memory-note',(finite(s.memory_total_bytes)?'Of '+bytes(s.memory_total_bytes)+' on this node':'Resource usage only, without memory contents')+(memoryGap?'. History has gaps.':''));
    var processCount=observedCount(data,'processes','process_count'), listenerCount=observedCount(data,'listeners','listening_port_count');
    text('na-process-count',processCount.value);text('na-process-note',processCount.note);
    text('na-listener-count',listenerCount.value);text('na-listener-note',listenerCount.note);
    var cov=data.coverage||{}, incomplete=Object.keys(cov).filter(function(k){return !['complete','available','collecting','ok'].includes(cov[k].state);});
    if(data.available===false)status(data.detail||data.message||data.reason||'Node observations are not available. Check that this node has an updated collector.','warning');
    else if((data.preferences||{}).enabled===false)status('Node monitoring is off. Historical observations remain available. Turn monitoring on in Govern to collect again.','warning');
    else if(stale)status('The latest observation is stale. Current activity cannot be verified. Open Govern to check collection coverage.','warning');
    else if((cov.processes||{}).sighting_history_limited)status('Process sighting history is incomplete. Some observations are not included in event history. Open Govern for coverage details.','warning');
    else if(incomplete.length)status('Some activity is outside our view. Open Govern for coverage and collection limits.','warning');
    else status('Reading recorded node activity. Periodic observations can miss changes between collections.');
    if(state.unconfirmed&&state.unconfirmed.scope===scope())status(state.unconfirmed.message,'warning');
    spark('na-cpu-spark',data.samples||[],'cpu_percent'); spark('na-memory-spark',data.samples||[],'memory_used_bytes');
    var retention=data.retention||{};
    text('na-retention',(retention.hours?'History retained for '+retention.hours+' hours. ':'')+(data.truncated?'Some results are omitted by collection limits.':''));
  }
  function spark(id,samples,key) {
    var svg=el(id); if(!svg)return; var line=svg.querySelector('polyline');if(!line)return;
    // Missing values break continuity rather than becoming invented zeroes.
    var values=samples.slice(-40).map(function(s){return s[key];}), start=0;
    values.forEach(function(v,i){if(!finite(v))start=i+1;});
    var suffix=values.slice(start);
    if(suffix.length<2) { line.setAttribute('points','');return; }
    var low=Math.min.apply(null,suffix), high=Math.max.apply(null,suffix), span=high-low||1;
    line.setAttribute('points',suffix.map(function(v,i){return ((start+i)*160/(values.length-1)).toFixed(1)+','+(23-(v-low)*21/span).toFixed(1);}).join(' '));
  }
  function showView(view) {
    state.view=['observe','govern','guard'].includes(view)?view:'observe';
    document.querySelectorAll('[data-na-view]').forEach(function(button){ if(button.dataset.naView===state.view)button.setAttribute('aria-current','page');else button.removeAttribute('aria-current'); });
    document.querySelectorAll('[data-na-panel]').forEach(function(panel){panel.hidden=panel.dataset.naPanel!==state.view;});
    if(state.view!=='observe')stopReplay();
  }
  function renderEvents() {
    var rows=events(), list=el('na-events'), scrub=el('na-scrub'), play=el('na-play');
    if(!rows.some(function(e){return String(e.id)===String(state.selected);}))state.selected=rows.length?rows[rows.length-1].id:null;
    var idx=rows.findIndex(function(e){return String(e.id)===String(state.selected);});
    var preview=rows.slice(-100);if(idx>=0&&idx<rows.length-100)preview.unshift(rows[idx]);
    if(list)list.innerHTML=rows.length?preview.map(function(e){return '<button type="button" class="na-event" data-na-event="'+esc(e.id)+'" aria-current="'+(String(e.id)===String(state.selected)?'step':'false')+'"><small>'+esc(when(e.observed_at))+'</small><strong>'+esc(eventStory(e).title)+'</strong><small>'+esc(attributed(e).label)+'</small></button>';}).join(''):'<p class="na-empty">No events were recorded in this history window. This does not establish that no activity occurred.</p>';
    if(scrub){scrub.max=Math.max(0,rows.length-1);scrub.value=Math.max(0,idx);scrub.disabled=!rows.length;scrub.setAttribute('aria-valuetext',rows[idx]?when(rows[idx].observed_at)+': '+(rows[idx].title||'Recorded event'):'No recorded events');}
    if(play)play.disabled=rows.length<2;
    text('na-step',rows.length?(idx+1)+' / '+rows.length: '0 events');
    text('na-history-note',(rows.length>100?'Latest 100 of '+rows.length+' events. Use the slider for earlier events.':rows.length+' recorded events.')+' Resource totals above show the latest collection.');
    renderEvidence(false);
  }
  function pretty(value) { if(value==null)return 'Not recorded';if(typeof value==='string')return value;try{return JSON.stringify(value,null,2);}catch(e){return 'Not available';} }
  function eventStory(event) {
    var process=event.process||{}, target=event.target||{}, row=event.after||event.before||{};
    var name=typeof process==='string'?process:(process.name||row.name||target.label||'A process');
    var title=event.title||'A recorded observation', meaning=event.detail||'Review the recorded details below.', limit='';
    if(event.kind==='process_observed'){
      title=name+' was seen running';meaning='This is its first retained sighting in a partial scan.';
      limit='It may have started earlier. This observation alone does not indicate an attack.';
    }else if(event.kind==='process_added'){
      title=name+' was seen running';meaning='This process was present in a later scan and absent from an earlier comparable scan.';
      limit='This does not tell us its exact start time or why it ran.';
    }else if(event.kind==='process_removed'){
      title=name+' was no longer seen';meaning='This process was absent from a later comparable scan.';
      limit='The scan does not tell us why it disappeared.';
    }else if(event.kind==='process_changed'){
      title=name+' had different recorded details';meaning='Comparable scans recorded a difference in the process details.';
    }else if(/^listener_/.test(event.kind||'')){
      title=event.kind==='listener_removed'?'A listening port was no longer seen':'A listening port was observed';
      meaning='The recorded address was '+(target.label||'a TCP endpoint')+'.';
      limit='A listening port accepts connections. This does not prove that it can be reached from the Internet.';
    }
    return {title:title,meaning:meaning,limit:limit};
  }
  function attributed(event) {
    var a=actor(event.actor);
    return a.kind!=='unattributed'&&a.evidence?{label:a.label,detail:a.evidence}:{label:'Not identified',
      detail:'This scan does not link the observation to you, an AI agent, or a remote session.'};
  }
  function renderEvidence(animate) {
    var event=selected(), box=el('na-evidence');if(!box)return;
    if(!event){
      delete box.dataset.eventId;
      box.innerHTML='<p class="na-empty">No observation is selected. Collection starts with a baseline before it can show changes.</p>';
    }else{
      var a=attributed(event), story=eventStory(event), target=event.target||{}, process=event.process||{}, review=event.review;
      var reason=el('na-review-reason'), same=box.dataset.eventId===String(event.id), draft=reason&&same?reason.value:null;
      var focused=reason&&document.activeElement===reason, selection=focused?[reason.selectionStart,reason.selectionEnd]:null;
      var details=box.querySelector?box.querySelector('.na-technical'):null, keepOpen=same&&details&&details.open;
      box.dataset.eventId=String(event.id);
      var processLabel=typeof process==='string'?process:[process.name,process.pid!=null?'PID '+process.pid:''].filter(Boolean).join(' ');
      var resource=processLabel||target.label||'Resource not recorded', evidence=Array.isArray(event.evidence)?event.evidence:[];
      var who=/^process_/.test(event.kind||'')?'Who started it':'Who was responsible';
      box.innerHTML='<div class="na-story-heading"><div><p class="na-observation-label">'+esc(event.finding===true?'Change to review':'Recorded observation')+'</p><h3>'+esc(story.title)+'</h3></div><time class="na-event-time">'+esc(when(event.observed_at))+'</time></div>'+
        '<p class="na-story-meaning">'+esc(story.meaning)+'</p><dl class="na-facts"><div><dt>Program or resource</dt><dd>'+esc(resource)+'</dd></div><div><dt>Observed on</dt><dd>'+esc((state.data.node||{}).hostname||'This node')+'</dd></div><div><dt>'+esc(who)+'</dt><dd>'+esc(a.label)+'</dd></div></dl>'+
        '<div class="na-observation-grid"><div><div class="na-identity-note"><strong>'+esc(a.label==='Not identified'?'Why we cannot identify who acted':'Recorded attribution evidence')+'</strong><p>'+esc(a.detail)+'</p>'+(story.limit?'<p>'+esc(story.limit)+'</p>':'')+'</div>'+resourceEvidence(event)+'</div>'+
        '<form id="na-review-form" class="na-review-form"><label for="na-review-reason">Add context for this past event</label><textarea id="na-review-reason" maxlength="300" placeholder="What you know about this change">'+esc(review&&review.reason||'')+'</textarea><div class="na-review-buttons"><button type="button" data-na-decision="expected">Mark expected</button><button type="button" data-na-decision="investigate">Investigate</button></div><div id="na-review-message" role="status" class="na-review-note">'+esc(review?'Reviewed: '+review.decision+'. This does not authorize future actions.':'A review adds historical context. It does not authorize future actions.')+'</div></form></div>'+
        '<details class="na-technical"'+(keepOpen?' open':'')+'><summary>Technical details and original evidence</summary><p>'+esc(event.title||'Recorded change')+'</p><p>'+esc(event.detail||'No additional description recorded.')+'</p><div class="na-diff"><div><small>Before</small><pre>'+esc(pretty(event.before))+'</pre></div><div><small>After</small><pre>'+esc(pretty(event.after))+'</pre></div></div><div class="na-source">'+(evidence.length?evidence.map(function(e){return esc(typeof e==='string'?e:pretty(e));}).join('<br>'):'No additional source evidence was recorded.')+'</div></details>';
      if(draft!=null&&el('na-review-reason')){el('na-review-reason').value=draft;if(focused){el('na-review-reason').focus({preventScroll:true});if(selection)el('na-review-reason').setSelectionRange(selection[0],selection[1]);}}
      if(!writable('reviews_writable')){box.querySelectorAll('[data-na-decision],textarea').forEach(function(n){n.disabled=true;});text('na-review-message',state.data.write_reason||'Reviews are unavailable here. Open this node’s local dashboard.');}
    }
    if(box.classList){box.classList.remove('na-animate');if(animate&&!reducedMotion()){void box.offsetWidth;box.classList.add('na-animate');}}
  }
  function chooseEvent(id,animate) {
    state.selected=id;renderEvents();if(animate)renderEvidence(true);
  }
  function table(rows,cols,empty) {
    if(!rows.length)return '<p class="na-empty">'+esc(empty)+'</p>';
    return (rows.length>100?'<p class="na-table-limit">Showing 100 of '+rows.length+' retained rows.</p>':'')+'<table><thead><tr>'+cols.map(function(c){return '<th scope="col">'+esc(c[0])+'</th>';}).join('')+'</tr></thead><tbody>'+rows.slice(0,100).map(function(row){return '<tr>'+cols.map(function(c){return '<td>'+c[1](row)+'</td>';}).join('')+'</tr>';}).join('')+'</tbody></table>';
  }
  function cpuCell(row) {
    if(finite(row.cpu_percent)&&row.cpu_percent>=0){
      return '<span class="na-cpu-meter" style="--na-cpu-fill:'+Math.min(100,row.cpu_percent)+'%">'+esc(number(row.cpu_percent,'%'))+'</span><small>'+esc(finite(row.cpu_interval_seconds)&&row.cpu_interval_seconds>0?
        'Over '+number(row.cpu_interval_seconds)+'s':'Measurement interval not recorded')+'</small>';
    }
    return '<span class="na-not-measured">Not measured</span><small>'+esc(row.cpu_reason||'No comparable CPU samples were recorded.')+'</small>';
  }
  function processRole(row){return Object.prototype.hasOwnProperty.call(PROCESS_ROLES,row.clawmetry_role)?PROCESS_ROLES[row.clawmetry_role]:'';}
  function observed(row){var at=epoch(row.observed_at);return row.stale?'Stale observation; '+(at==null?'Observation time unknown':'last observed '+when(row.observed_at)):(at==null?'Observation time unknown':'Observed '+when(row.observed_at));}
  function processColumns(){return [['Process',function(p){var a=actor(p.actor), role=processRole(p);return (role?'<strong class="na-process-role">ClawMetry '+esc(role)+'</strong><small>'+esc(p.name||'Unnamed process')+'</small>':esc(p.name||'Unnamed process'))+'<small>PID '+esc(p.pid)+(a.kind!=='unattributed'&&a.evidence?' / '+esc(a.label):'')+'</small><small class="na-row-age">'+esc(observed(p))+'</small>';}],['CPU between scans',cpuCell],['Memory',function(p){return finite(p.memory_bytes)?esc(bytes(p.memory_bytes)):'<span class="na-not-measured">Not measured</span>';}]];}
  function renderProcesses(data){
    var processes=Array.isArray(data.processes)?data.processes:[], query=state.processQuery.trim().toLowerCase();
    var ranked=processes.filter(function(p){return !query||[p.name,p.pid,processRole(p)?'ClawMetry '+processRole(p):''].join(' ').toLowerCase().indexOf(query)>=0;}).sort(function(a,b){
      return Number(!!a.stale)-Number(!!b.stale)||Number(finite(b.cpu_percent))-Number(finite(a.cpu_percent))||
        (finite(b.cpu_percent)&&finite(a.cpu_percent)?b.cpu_percent-a.cpu_percent:0);
    });
    state.processPage=Math.max(0,Math.min(state.processPage,Math.ceil(ranked.length/100)-1));
    var start=state.processPage*100;
    text('na-process-results',ranked.length?(start+1)+' to '+Math.min(start+100,ranked.length)+' of '+ranked.length+(query?' matches':' retained processes'):
      query?'No matching processes in '+processes.length+' retained observations.':'No retained processes.');
    if(el('na-process-prev'))el('na-process-prev').disabled=state.processPage===0;
    if(el('na-process-next'))el('na-process-next').disabled=start+100>=ranked.length;
    if(el('na-process-clear'))el('na-process-clear').disabled=!state.processQuery;
    if(el('na-processes'))el('na-processes').innerHTML=ranked.length?table(ranked.slice(start,start+100),processColumns()):
      query?'<p class="na-empty">No matching processes were recorded. Clear the search or check collection coverage.</p>':emptyInventory(data,'processes');
  }
  function renderClawmetry(data){
    var rows=(Array.isArray(data.processes)?data.processes:[]).filter(function(p){return !!processRole(p);});
    var coverage=(data.coverage||{}).processes||{}, at=epoch(data.collected_at);
    var stale=at==null||Date.now()-at>(data.stale_after_seconds||120)*1000||rows.some(function(p){return p.stale;});
    text('na-clawmetry-note',rows.length?'Identified processes on this node'+(coverage.state==='disabled'?'. Collection is off.':stale?'. These observations are stale.':'.'):
      'ClawMetry may appear under a Python process name.');
    if(el('na-clawmetry-processes'))el('na-clawmetry-processes').innerHTML=rows.length?table(rows,processColumns()):
      '<p class="na-empty">'+esc(coverage.state==='disabled'?'Process collection is off. Turn it on in Govern to measure ClawMetry usage.':
        coverage.state==='unavailable'||coverage.state==='unsupported'?sourceReason(data,'processes')+' Check process coverage in Govern.':
        'No ClawMetry process was identified in these observations. An updated collector is required. Check process coverage in Govern.')+'</p>';
  }
  function inventoryData() {
    var base=state.data||{}, live=state.liveData;
    if(!live||epoch(live.collected_at)<epoch(base.collected_at))return base;
    var coverage=Object.assign({},base.coverage||{});
    ['resources','processes'].forEach(function(k){coverage[k]=Object.assign({},coverage[k]||{},(live.coverage||{})[k]||{});});
    return Object.assign({},base,{collected_at:live.collected_at,stale_after_seconds:8,summary:live.summary,processes:live.processes,coverage:coverage,preferences:live.preferences||base.preferences});
  }
  function liveStatus() {
    var data=state.liveData, at=data&&epoch(data.collected_at), measured=data&&(data.processes||[]).some(function(p){return finite(p.cpu_percent);});
    var fresh=at!=null&&Date.now()-at<8000;
    text('na-live-state',state.liveUnsupported?'Snapshot updates':!data?(Date.now()-state.liveStarted>10000?'Waiting for live data':'Starting live measurements'):!fresh?'Live updates delayed':measured?'Live · every 2 seconds':'Sampling CPU');
    if(el('na-live-state'))el('na-live-state').dataset.live=String(!!(fresh&&measured));
  }
  function renderInventory(data) {
    var processes=Array.isArray(data.processes)?data.processes:[], listeners=Array.isArray(data.listeners)?data.listeners:[];
    function note(rows){return rows.some(function(r){return r.stale;})?'Includes stale observations':rows.some(function(r){return epoch(r.observed_at)==null;})?'Some observation times are unknown':'From the latest collection';}
    text('na-process-observation-note',note(processes));text('na-listener-observation-note',note(listeners));
    text('na-process-coverage-note','Names identify programs, not who started them. CPU is measured between scans; 100% means one CPU core. '+sourceReason(data,'processes'));
    text('na-listener-coverage-note',sourceReason(data,'listeners')+' A listening port does not prove Internet access.');
    renderProcesses(data);renderClawmetry(data);
    if(el('na-listeners'))el('na-listeners').innerHTML=listeners.length?table(listeners,[['Listening address',function(l){var address=l.address||'Address not recorded';if(address.indexOf(':')>=0&&address[0]!=='[')address='['+address+']';return esc(address)+':'+esc(l.port)+'<small>'+esc(l.protocol||'Protocol not recorded')+'</small><small class="na-row-age">'+esc(observed(l))+'</small>';}],['Reported process',function(l){return l.pid!=null?'PID '+esc(l.pid):'Not identified';}],['Connections accepted from',function(l){return esc(l.exposure==='loopback'?'This machine only':l.exposure==='nonloopback'?'Other network interfaces':'Scope not established');}]]):emptyInventory(data,'listeners');
  }
  function coverageHtml(data) {
    var coverage=data.coverage||{}, rows=Array.isArray(coverage)?coverage.map(function(r){return [r.id,r];}):Object.keys(coverage).map(function(k){return [k,coverage[k]];});
    if(!rows.length)return '<p class="na-empty">The collector did not report coverage. Activity cannot be verified.</p>';
    return rows.map(function(entry){var key=entry[0], c=entry[1]||{}, complete=['complete','available','collecting','ok'].includes(c.state)&&!c.sighting_history_limited;return '<div class="na-coverage-row"><div>'+esc(c.label||COVERAGE_LABELS[key]||key)+'<small>'+esc(c.reason||c.detail||'No collection detail reported')+'<br>Visible scope: '+esc(c.scope||'unknown')+(c.method?' / '+esc(c.method):'')+(c.observed_at?'<br>'+esc(when(c.observed_at)):'')+(c.truncated?'<br>Collection limit reached. More activity may exist.':'')+(c.sighting_history_limited?'<br>Process sighting history is limited. Some observations are not included in event history.':'')+'</small></div><span class="na-coverage-state" data-complete="'+complete+'">'+esc(c.state||'Unknown')+(c.sighting_history_limited?' / history limited':'')+'</span></div>';}).join('');
  }
  function renderGovern(data) {
    var fields=el('na-preference-fields'), prefs=data.preferences||{};
    // Keep unsaved input intact during refreshes while the form has focus.
    var form=el('na-preferences'), editing=form&&form.contains(document.activeElement);
    if(fields&&!editing)fields.innerHTML=PREFS.map(function(p){return '<label class="na-pref"><span>'+esc(p[1])+'<small>'+esc(p[2])+'</small></span><input type="checkbox" name="'+p[0]+'"'+(prefs[p[0]]===true?' checked':'')+(typeof prefs[p[0]]!=='boolean'||!writable('preferences_writable')?' disabled':'')+'></label>';}).join('');
    if(form){var save=form.querySelector('button[type=submit]');if(save)save.disabled=!writable('preferences_writable')||!Object.keys(prefs).length;}
    if(!writable('preferences_writable'))text('na-preference-message',data.write_reason||'Settings are unavailable here. Open this node’s local dashboard.');
    ['na-coverage','na-guard-coverage'].forEach(function(id){if(el(id))el(id).innerHTML=coverageHtml(data);});
    var reviewed=events().filter(function(e){return e.review&&e.review.decision;});
    if(el('na-reviews'))el('na-reviews').innerHTML=table(reviewed,[['Event',function(e){return '<button type="button" data-na-open="'+esc(e.id)+'">'+esc(e.title||'Recorded change')+'</button><small>'+esc(when(e.observed_at))+'</small>';}],['Review',function(e){return esc(e.review.decision)+'<small>'+esc(e.review.reason||'No reason added')+'</small>';}]],'No reviewed events are present in the current history window.');
  }
  function renderFindings() {
    var rows=events().filter(function(e){return e.finding===true||(e.review||{}).decision==='investigate';}), box=el('na-findings');if(!box)return;
    box.innerHTML=rows.length?rows.map(function(e){return '<article class="na-finding"><h3>'+esc(e.title||'Recorded change')+'</h3><p>'+esc(e.detail||'Open the event to inspect the evidence.')+'</p><small>'+esc(when(e.observed_at))+' / '+esc(actor(e.actor).label)+(e.review?' / '+esc(e.review.decision):'')+'</small><button type="button" data-na-open="'+esc(e.id)+'">Review evidence</button></article>';}).join(''):'<div class="na-panel"><p class="na-empty">No changes in this history window are marked for review. Check coverage before drawing conclusions about activity.</p></div>';
  }
  function render(data) {summary(data);renderEvents();renderInventory(data);renderGovern(data);renderFindings();showView(state.view);}
  function reducedMotion() { return !!(window.matchMedia&&window.matchMedia('(prefers-reduced-motion: reduce)').matches); }
  function stopReplay() {clearTimeout(state.replay);state.replay=null;text('na-play','Replay events');}
  function replayStep() {
    if(!active()||state.view!=='observe'){stopReplay();return;}
    var rows=events(), index=rows.findIndex(function(e){return String(e.id)===String(state.selected);});
    if(index>=rows.length-1){stopReplay();return;}
    chooseEvent(rows[index+1].id,true);state.replay=setTimeout(replayStep,1200);
  }
  function startReplay() {
    if(state.replay){stopReplay();return;}
    var rows=events();if(rows.length<2||!active())return;
    if(String(state.selected)===String(rows[rows.length-1].id))chooseEvent(rows[0].id,true);
    text('na-play','Pause replay');state.replay=setTimeout(replayStep,1200);
  }
  function schedule() {clearTimeout(state.timer);state.timer=null;if(active())state.timer=setTimeout(function(){load(true,!!state.data&&!state.liveUnsupported&&Date.now()-state.lastLoaded<30000);},state.liveUnsupported?(window.CLOUD_MODE?15000:10000):2000);}
  function invalidate() {
    state.generation++;if(state.controller)state.controller.abort();state.controller=null;state.pending=null;
    if(state.readRequest){clearTimeout(state.readRequest.timeout);state.readRequest=null;}
    var write=state.mutationRequest;
    if(write){
      state.unconfirmed={scope:write.scope,message:UNCONFIRMED};
      clearTimeout(write.timeout);write.controller.abort();
      state.mutationRequest=null;state.mutation=false;
    }
    clearTimeout(state.timer);state.timer=null;stopReplay();
  }
  function resetScope(key) {
    invalidate();state.scope=key;state.data=null;state.selected=null;state.lastLoaded=0;
    state.liveData=null;state.liveUnsupported=false;state.liveMisses=0;state.liveStarted=Date.now();liveStatus();state.processQuery='';state.processPage=0;if(el('na-process-search'))el('na-process-search').value='';
    render({available:false,reason:'Reading this node’s recorded observations.',summary:{},coverage:{},events:[],preferences:{}});
    text('na-preference-message','');
  }
  async function load(force,live) {
    if(!active())return;
    var key=scope();if(state.scope!==key)resetScope(key);
    if(state.pending)return state.pending;
    if(!force&&Date.now()-state.lastLoaded<5000){schedule();return;}
    var generation=state.generation, controller=new AbortController();state.controller=controller;
    var read={controller:controller,timeout:null,timedOut:false};state.readRequest=read;
    function readError(message){
      if(!valid(generation,key))return;
      if(state.data)summary(inventoryData());liveStatus();
      status(message,'warning');
    }
    read.timeout=setTimeout(function(){
      if(state.readRequest!==read)return;
      read.timedOut=true;controller.abort();
      readError('The node did not respond in time. Current activity cannot be verified. Refresh to try again.');
    },15000);
    var pending=(async function(){
      try {
        var response=await fetch(live?'/api/node-activity?live=1':'/api/node-activity?limit=100',{signal:controller.signal}),data=await response.json();
        if(!valid(generation,key))return;
        if(controller.signal.aborted)return;
        if(!response.ok)throw new Error(data.detail||data.message||data.error||data.reason||'The recorded observations could not be loaded.');
        if(!data||typeof data!=='object')throw new Error('The node returned an unreadable observation.');
        if(live&&data.live===true){
          if(data.available!==false&&(!state.liveData||epoch(data.collected_at)>=epoch(state.liveData.collected_at))){state.liveData=data;state.liveMisses=0;var display=inventoryData();summary(display);renderInventory(display);}
          else if(++state.liveMisses>=5&&!((state.data.capabilities||{}).live_metrics)){state.liveUnsupported=true;}
          liveStatus();
        }else{
          if(live)state.liveUnsupported=true;
          else if((data.capabilities||{}).live_metrics)state.liveUnsupported=false;
          state.data=data;state.lastLoaded=Date.now();render(data);
          if(state.liveData){summary(inventoryData());renderInventory(inventoryData());}
          liveStatus();
        }
      } catch(error) {
        if(read.timedOut)readError('The node did not respond in time. Current activity cannot be verified. Refresh to try again.');
        else if(error.name!=='AbortError')readError(error.message||'The node did not return observations. Try Refresh.');
      } finally {
        clearTimeout(read.timeout);
        if(state.readRequest===read){state.readRequest=null;state.pending=null;state.controller=null;schedule();}
      }
    })();state.pending=pending;return pending;
  }
  async function mutate(path,body,messageId) {
    if(state.mutation||!active())return;
    var key=scope(),generation=state.generation;
    if(state.scope!==null&&state.scope!==key){
      load(true);status('Node selection changed. Review this node before you save.','warning');return;
    }
    var write={scope:key,generation:generation,controller:new AbortController(),timeout:null};
    state.mutationRequest=write;state.mutation=true;
    write.timeout=setTimeout(function(){
      if(state.mutationRequest!==write)return;
      state.unconfirmed={scope:key,message:UNCONFIRMED};write.controller.abort();
      if(valid(generation,key)){text(messageId,UNCONFIRMED);status(UNCONFIRMED,'warning');}
    },45000);
    text(messageId,'Waiting for this node to confirm the change.');
    try {
      var response=await fetch('/api/node-activity/'+path,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body),signal:write.controller.signal}),data=await response.json();
      if(write.controller.signal.aborted||!valid(generation,key))return;
      if(!response.ok||data.ok!==true||(data.saved!==true&&data.applied!==true))throw new Error(data.detail||data.message||data.error||data.reason||'The node did not confirm the change. Nothing is marked as saved.');
      clearTimeout(write.timeout);
      if(state.mutationRequest===write){state.mutationRequest=null;state.mutation=false;}
      state.unconfirmed=null;text(messageId,'Saved on this node.');state.lastLoaded=0;await load(true);
    } catch(error) {
      if(write.controller.signal.aborted||error.name==='AbortError'){
        if(state.mutationRequest===write)state.unconfirmed={scope:key,message:UNCONFIRMED};
        if(valid(generation,key)){text(messageId,UNCONFIRMED);status(UNCONFIRMED,'warning');}
      }else if(valid(generation,key))text(messageId,error.message||'The change could not be confirmed.');
    } finally {
      clearTimeout(write.timeout);
      if(state.mutationRequest===write){state.mutationRequest=null;state.mutation=false;}
    }
  }
  function bind() {
    var root=el('page-node-activity');if(!root||state.bound)return;state.bound=true;
    root.addEventListener('click',function(event){
      var button=event.target.closest('button');if(!button)return;
      if(button.hasAttribute('data-na-coverage'))showView('govern');
      else if(button.dataset.naView)showView(button.dataset.naView);
      else if(button.dataset.naEvent!=null){stopReplay();chooseEvent(button.dataset.naEvent,true);}
      else if(button.dataset.naOpen!=null){stopReplay();showView('observe');chooseEvent(button.dataset.naOpen,true);if(el('na-evidence'))el('na-evidence').scrollIntoView({block:'nearest',behavior:reducedMotion()?'auto':'smooth'});}
      else if(button.id==='na-refresh')load(true);
      else if(button.id==='na-process-clear'){state.processQuery='';state.processPage=0;if(el('na-process-search')){el('na-process-search').value='';el('na-process-search').focus();}renderProcesses(inventoryData());}
      else if(button.id==='na-process-prev'||button.id==='na-process-next'){state.processPage+=button.id==='na-process-next'?1:-1;renderProcesses(inventoryData());if(el('na-processes'))el('na-processes').scrollTop=0;}
      else if(button.id==='na-play')startReplay();
      else if(button.id==='na-open-guard'&&typeof window.switchTab==='function'){window.switchTab('guard');if(window.guardShowView)window.guardShowView('checks');}
      else if(button.dataset.naDecision){var e=selected();if(e)mutate('reviews',{event_id:e.id,decision:button.dataset.naDecision,reason:el('na-review-reason')?el('na-review-reason').value.replace(/[\r\n\t]/g,' ').trim():''},'na-review-message');}
    });
    root.addEventListener('submit',function(event){event.preventDefault();if(event.target.id!=='na-preferences')return;var body={};PREFS.forEach(function(p){var input=event.target.elements.namedItem(p[0]);if(input&&!input.disabled)body[p[0]]=input.checked;});mutate('preferences',body,'na-preference-message');});
    root.addEventListener('input',function(event){if(event.target.id==='na-process-search'){state.processQuery=event.target.value;state.processPage=0;renderProcesses(inventoryData());if(el('na-processes'))el('na-processes').scrollTop=0;}});
    if(el('na-scrub'))el('na-scrub').addEventListener('input',function(){stopReplay();var e=events()[Number(this.value)];if(e)chooseEvent(e.id,true);});
  }
  window.loadNodeActivity=function(){bind();return load(false);};
  window.nodeActivityStop=function(){invalidate();var box=el('na-evidence');if(box)box.classList.remove('na-animate');};
  document.addEventListener('visibilitychange',function(){if(document.hidden)window.nodeActivityStop();else if(active())window.loadNodeActivity();});
  window.addEventListener('cm:node-change',function(){if(active())window.loadNodeActivity();else{invalidate();state.scope=null;}});
  // Small pure helpers and lifecycle state exposed for focused offline tests.
  window.cmNodeActivity={actor:actor,number:number,bytes:bytes,epoch:epoch,reducedMotion:reducedMotion,
    getState:function(){return state;},select:chooseEvent,play:startReplay,stopReplay:stopReplay,sampleForEvent:sampleForEvent,spark:spark,mutate:mutate};
})();
