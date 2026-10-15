/* Node observations are persisted evidence. No host collection runs here. */
(function () {
  'use strict';
  var state = {data:null, scope:null, generation:0, pending:null, controller:null, timer:null,
    replay:null, selected:null, view:'observe', lastLoaded:0, bound:false, mutation:false,
    mutationRequest:null, unconfirmed:null, readRequest:null};
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
  function summary(data) {
    var s=data.summary||{}, at=epoch(data.collected_at), stale=at==null||Date.now()-at>(data.stale_after_seconds||120)*1000;
    text('na-node-name',(data.node||{}).hostname||(data.node||{}).id||'This node');
    text('na-map-host',(data.node||{}).hostname||'This node');
    text('na-freshness',age(data.collected_at)+(stale?' (stale)':''));
    var freshness=el('na-freshness'); if(freshness&&freshness.parentNode)freshness.parentNode.dataset.fresh=String(!stale);
    text('na-cpu',number(s.cpu_percent,'%')); text('na-memory',bytes(s.memory_used_bytes));
    var samples=data.samples||[], cpuGap=samples.some(function(v){return !finite(v.cpu_percent);}), memoryGap=samples.some(function(v){return !finite(v.memory_used_bytes);});
    text('na-cpu-note','Node total'+(cpuGap?'. History has gaps.':''));
    text('na-memory-note',(finite(s.memory_total_bytes)?'Of '+bytes(s.memory_total_bytes)+' on this node':'Resource usage only, without memory contents')+(memoryGap?'. History has gaps.':''));
    text('na-process-count',number(s.process_count)); text('na-listener-count',number(s.listening_port_count));
    text('na-process-note',data.truncated?'Collection is bounded. More processes may exist.':'Observed at the last collection');
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
    if(list)list.innerHTML=rows.length?preview.map(function(e){return '<button type="button" class="na-event" data-na-event="'+esc(e.id)+'" aria-current="'+(String(e.id)===String(state.selected)?'step':'false')+'"><small>'+esc(when(e.observed_at))+'</small><strong>'+esc(e.title||'Recorded event')+'</strong><small>'+esc(actor(e.actor).label)+'</small></button>';}).join(''):'<p class="na-empty">No events were recorded in this history window. This does not establish that no activity occurred.</p>';
    if(scrub){scrub.max=Math.max(0,rows.length-1);scrub.value=Math.max(0,idx);scrub.disabled=!rows.length;scrub.setAttribute('aria-valuetext',rows[idx]?when(rows[idx].observed_at)+': '+(rows[idx].title||'Recorded event'):'No recorded events');}
    if(play)play.disabled=rows.length<2;
    text('na-step',rows.length?(idx+1)+' / '+rows.length: '0 events');
    text('na-history-note',(rows.length>100?'Latest 100 of '+rows.length+' events. Use the slider for earlier events.':rows.length+' recorded events.')+' Resource totals above show the latest collection.');
    renderEvidence(false);
  }
  function pretty(value) { if(value==null)return 'Not recorded';if(typeof value==='string')return value;try{return JSON.stringify(value,null,2);}catch(e){return 'Not available';} }
  function renderEvidence(animate) {
    var event=selected(), box=el('na-evidence'), map=el('na-map');
    if(!box)return;
    if(!event){box.innerHTML='<p class="na-empty">Select a recorded event to see its actor, change and source evidence. Collection starts with a baseline before it can show differences.</p>';text('na-map-target','Select an event');text('na-map-target-kind','A resource it affected');}
    else {
      var a=actor(event.actor), target=event.target||{}, process=event.process||{}, evidence=Array.isArray(event.evidence)?event.evidence:[], review=event.review;
      var reason=el('na-review-reason'), draft=reason&&box.dataset.eventId===String(event.id)?reason.value:null;
      var focused=reason&&document.activeElement===reason, selection=focused?[reason.selectionStart,reason.selectionEnd]:null;
      box.dataset.eventId=String(event.id);
      var processLabel=typeof process==='string'?process:[process.name,process.pid!=null?'PID '+process.pid:''].filter(Boolean).join(' ');
      box.innerHTML='<div class="na-event-time">'+esc(when(event.observed_at))+'</div><h3>'+esc(event.title||'Recorded change')+'</h3><p>'+esc(event.detail||'Review the recorded evidence below.')+'</p><dl class="na-facts"><div><dt>Actor</dt><dd>'+esc(a.label)+(a.runtime?' / '+esc(a.runtime):'')+'</dd></div><div><dt>Attribution evidence</dt><dd>'+esc(a.evidence||'Identity is not established by this observation.')+'</dd></div><div><dt>Process</dt><dd>'+esc(processLabel||'Not attributed')+'</dd></div><div><dt>Affected resource</dt><dd>'+esc(target.label||target.id||'Not recorded')+'</dd></div></dl>'+resourceEvidence(event)+'<div class="na-diff"><div><small>Before</small><pre>'+esc(pretty(event.before))+'</pre></div><div><small>After</small><pre>'+esc(pretty(event.after))+'</pre></div></div><div class="na-source">'+(evidence.length?evidence.map(function(e){return esc(typeof e==='string'?e:pretty(e));}).join('<br>'):'No additional source evidence was recorded.')+'</div><form id="na-review-form" class="na-review-form"><label for="na-review-reason">Add context for this past event</label><textarea id="na-review-reason" maxlength="300" placeholder="What you know about this change">'+esc(review&&review.reason||'')+'</textarea><div class="na-review-buttons"><button type="button" data-na-decision="expected">Mark expected</button><button type="button" data-na-decision="investigate">Investigate</button></div><div id="na-review-message" role="status" class="na-review-note">'+esc(review?'Reviewed: '+review.decision+'. This does not authorize future actions.':'A review adds historical context. It does not authorize future actions.')+'</div></form>';
      if(draft!=null&&el('na-review-reason')){el('na-review-reason').value=draft;if(focused){el('na-review-reason').focus({preventScroll:true});if(selection)el('na-review-reason').setSelectionRange(selection[0],selection[1]);}}
      if(!writable('reviews_writable')) {box.querySelectorAll('[data-na-decision],textarea').forEach(function(n){n.disabled=true;});text('na-review-message',state.data.write_reason||'Reviews are unavailable here. Open this node’s local dashboard.');}
      text('na-map-target',target.label||target.id||'Recorded resource');text('na-map-target-kind',target.kind||'Resource');
    }
    if(map){map.dataset.event=String(!!event);map.dataset.eventId=event?String(event.id):'';map.querySelectorAll('[data-na-actor]').forEach(function(node){node.classList.toggle('na-selected',!!event&&node.dataset.naActor===actor(event.actor).kind);});map.querySelectorAll('.na-map-host,.na-map-target').forEach(function(node){node.classList.toggle('na-selected',!!event);});map.classList.remove('na-animate');if(animate&&!reducedMotion()){void map.offsetWidth;map.classList.add('na-animate');}}
  }
  function chooseEvent(id,animate) {
    state.selected=id;renderEvents();if(animate)renderEvidence(true);
  }
  function table(rows,cols,empty) {
    if(!rows.length)return '<p class="na-empty">'+esc(empty)+'</p>';
    return (rows.length>100?'<p class="na-table-limit">Showing 100 of '+rows.length+' retained rows.</p>':'')+'<table><thead><tr>'+cols.map(function(c){return '<th scope="col">'+esc(c[0])+'</th>';}).join('')+'</tr></thead><tbody>'+rows.slice(0,100).map(function(row){return '<tr>'+cols.map(function(c){return '<td>'+c[1](row)+'</td>';}).join('')+'</tr>';}).join('')+'</tbody></table>';
  }
  function renderInventory(data) {
    var processes=Array.isArray(data.processes)?data.processes:[], listeners=Array.isArray(data.listeners)?data.listeners:[];
    function observed(row){var at=epoch(row.observed_at);return row.stale?'Stale observation; '+(at==null?'Observation time unknown':'last observed '+when(row.observed_at)):(at==null?'Observation time unknown':'Observed '+when(row.observed_at));}
    function note(rows){return rows.some(function(r){return r.stale;})?'Includes stale observations':rows.some(function(r){return epoch(r.observed_at)==null;})?'Some observation times are unknown':'From the latest collection';}
    text('na-process-observation-note',note(processes));text('na-listener-observation-note',note(listeners));
    if(el('na-processes'))el('na-processes').innerHTML=table(processes,[['Process',function(p){return esc(p.name||'Unnamed process')+'<small>PID '+esc(p.pid)+' / '+esc(actor(p.actor).label)+'</small><small class="na-row-age">'+esc(observed(p))+'</small>';}],['CPU',function(p){return esc(number(p.cpu_percent,'%'));}],['Memory',function(p){return esc(bytes(p.memory_bytes));}]],'No process rows are available. Check collection coverage in Govern.');
    if(el('na-listeners'))el('na-listeners').innerHTML=table(listeners,[['Listener',function(l){return esc(l.address||'Unknown address')+':'+esc(l.port)+'<small>'+esc(l.protocol||'Protocol unknown')+'</small><small class="na-row-age">'+esc(observed(l))+'</small>';}],['Process',function(l){return l.pid!=null?'PID '+esc(l.pid):'Unattributed';}],['Scope',function(l){return esc(l.exposure==='loopback'?'Local only':l.exposure==='nonloopback'?'Nonlocal bind':'Unknown');}]],'No listener rows are available. Check collection coverage in Govern.');
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
  function schedule() {clearTimeout(state.timer);state.timer=null;if(active())state.timer=setTimeout(function(){load(true);},window.CLOUD_MODE?15000:10000);}
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
    render({available:false,reason:'Reading this node’s recorded observations.',summary:{},coverage:{},events:[],preferences:{}});
    text('na-preference-message','');
  }
  async function load(force) {
    if(!active())return;
    var key=scope();if(state.scope!==key)resetScope(key);
    if(state.pending)return state.pending;
    if(!force&&Date.now()-state.lastLoaded<5000){schedule();return;}
    var generation=state.generation, controller=new AbortController();state.controller=controller;
    var read={controller:controller,timeout:null,timedOut:false};state.readRequest=read;
    function readError(message){
      if(!valid(generation,key))return;
      if(state.data)summary(state.data);
      status(message,'warning');
    }
    read.timeout=setTimeout(function(){
      if(state.readRequest!==read)return;
      read.timedOut=true;controller.abort();
      readError('The node did not respond in time. Current activity cannot be verified. Refresh to try again.');
    },15000);
    var pending=(async function(){
      try {
        var response=await fetch('/api/node-activity?limit=100',{signal:controller.signal}),data=await response.json();
        if(!valid(generation,key))return;
        if(controller.signal.aborted)return;
        if(!response.ok)throw new Error(data.detail||data.message||data.error||data.reason||'The recorded observations could not be loaded.');
        if(!data||typeof data!=='object')throw new Error('The node returned an unreadable observation.');
        state.data=data;state.lastLoaded=Date.now();render(data);
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
      if(button.dataset.naView)showView(button.dataset.naView);
      else if(button.dataset.naEvent!=null){stopReplay();chooseEvent(button.dataset.naEvent,true);}
      else if(button.dataset.naOpen!=null){stopReplay();showView('observe');chooseEvent(button.dataset.naOpen,true);if(el('na-evidence'))el('na-evidence').scrollIntoView({block:'nearest',behavior:reducedMotion()?'auto':'smooth'});}
      else if(button.id==='na-refresh')load(true);
      else if(button.id==='na-play')startReplay();
      else if(button.id==='na-open-guard'&&typeof window.switchTab==='function'){window.switchTab('guard');if(window.guardShowView)window.guardShowView('checks');}
      else if(button.dataset.naDecision){var e=selected();if(e)mutate('reviews',{event_id:e.id,decision:button.dataset.naDecision,reason:el('na-review-reason')?el('na-review-reason').value.replace(/[\r\n\t]/g,' ').trim():''},'na-review-message');}
    });
    root.addEventListener('submit',function(event){event.preventDefault();if(event.target.id!=='na-preferences')return;var body={};PREFS.forEach(function(p){var input=event.target.elements.namedItem(p[0]);if(input&&!input.disabled)body[p[0]]=input.checked;});mutate('preferences',body,'na-preference-message');});
    if(el('na-scrub'))el('na-scrub').addEventListener('input',function(){stopReplay();var e=events()[Number(this.value)];if(e)chooseEvent(e.id,true);});
  }
  window.loadNodeActivity=function(){bind();return load(false);};
  window.nodeActivityStop=function(){invalidate();var map=el('na-map');if(map)map.classList.remove('na-animate');};
  document.addEventListener('visibilitychange',function(){if(document.hidden)window.nodeActivityStop();else if(active())window.loadNodeActivity();});
  window.addEventListener('cm:node-change',function(){if(active())window.loadNodeActivity();else{invalidate();state.scope=null;}});
  // Small pure helpers and lifecycle state exposed for focused offline tests.
  window.cmNodeActivity={actor:actor,number:number,bytes:bytes,epoch:epoch,reducedMotion:reducedMotion,
    getState:function(){return state;},select:chooseEvent,play:startReplay,stopReplay:stopReplay,sampleForEvent:sampleForEvent,spark:spark,mutate:mutate};
})();
