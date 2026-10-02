/* Durable Guard findings inside Tracing. All content is persisted and scoped. */
(function () {
  'use strict';
  var state = {generation: 0, scope: null, data: null, rows: new Map(), cursor: null, loading: false};
  var stopWatching = null, watchGeneration = 0;
  var historyRequests = new Map(), historyGeneration = 0;
  function byId(id) { return document.getElementById(id); }
  function el(tag, text, className) {
    var node = document.createElement(tag);
    if (text !== undefined) node.textContent = text;
    if (className) node.className = className;
    return node;
  }
  function button(text, click) {
    var node = el('button', text, 'btn btn-sm');
    node.type = 'button'; node.addEventListener('click', click); return node;
  }
  function when(value) {
    if (!value) return 'Not observed';
    var date = new Date(value);
    return Number.isNaN(date.getTime()) ? 'Time unavailable' : date.toLocaleString();
  }
  function args(scope) {
    var query = new URLSearchParams();
    Object.keys(scope).forEach(function (key) { if (scope[key]) query.set(key, scope[key]); });
    return query.toString();
  }
  function request(path, options) {
    return fetch(path, options).then(function (r) {
      if (!r.ok) throw new Error('unavailable');
      return r.json();
    }).then(function (data) {
      if (!data || data.available === false) throw new Error('unavailable');
      return data;
    });
  }
  function incidentState(incident) {
    if (!incident) return 'Unavailable';
    if (incident.state === 'active' && (!incident.last_evidence_at || Date.now() - incident.last_evidence_at >= 1800000)) return 'Stale';
    return {active: 'Active', recovered: 'Recovered', stale: 'Stale'}[incident.state] || 'Unknown';
  }
  function message(text) {
    var target = byId('investigation-message');
    if (target) target.textContent = text;
  }

  window.cmCloseInvestigation = function () {
    stopLive();
    state.generation += 1; state.scope = null; state.data = null; state.loading = false;
    var panel = byId('trace-investigation'), regular = byId('trace-standard-detail');
    if (panel) panel.hidden = true;
    if (regular) regular.hidden = false;
  };
  window.cmOpenIncident = function (id, runtime, session, node) {
    window._pendingInvestigation = {incident_id: id, runtime: runtime, session_id: session, node_id: node};
    switchTab('tracing');
  };
  window.cmLoadInvestigation = function (scope) {
    stopLive();
    var generation = ++state.generation;
    state.scope = scope; state.data = null; state.rows = new Map(); state.loading = true;
    byId('trace-list').style.display = 'none';
    byId('trace-detail').style.display = '';
    byId('trace-back-btn').style.display = '';
    byId('trace-standard-detail').hidden = true;
    var panel = byId('trace-investigation');
    panel.hidden = false; panel.replaceChildren(el('p', 'Reading this finding and its evidence...', 'section-sub'));
    // Older Guard previews may carry the episode ID without its node. Resolve
    // that exact ID first; never guess a node or use a wildcard session read.
    var resolve = scope.node_id ? Promise.resolve(scope) : request('/api/guard/incidents?' + args(scope)).then(function (data) {
      var incident = (data.rows || []).find(function (row) { return row.incident_id === scope.incident_id; });
      if (!incident) throw new Error('missing');
      return {incident_id: incident.incident_id, session_id: incident.session_id,
              runtime: incident.runtime, node_id: incident.node_id};
    });
    return resolve.then(function (resolved) {
      if (generation !== state.generation) return null;
      state.scope = resolved;
      return request('/api/investigation?' + args(resolved));
    }).then(function (data) {
      if (!data || generation !== state.generation) return;
      state.data = data;
      (data.evidence_rows || []).concat(data.rows || []).forEach(function (row) { state.rows.set(row.id, row); });
      state.cursor = (data.coverage || {}).next_cursor;
      render(); startLive();
    }).catch(function () {
      if (generation !== state.generation) return;
      panel.replaceChildren(el('h3', 'Evidence is unavailable'),
        el('p', 'Reconnect to this node and try again. A missing read does not mean the finding recovered.'),
        button('Try again', function () { window.cmLoadInvestigation(scope); }));
    }).finally(function () { if (generation === state.generation) state.loading = false; });
  };

  function render() {
    var data = state.data, incident = data.incident, coverage = data.coverage || {};
    var panel = byId('trace-investigation');
    panel.replaceChildren();
    var head = el('header', undefined, 'investigation-head');
    head.append(el('h3', incident ? incident.title || 'Guard finding' : 'Session investigation'));
    head.append(el('p', [data.scope.runtime, data.scope.session_id, 'Node ' + data.scope.node_id].join(' · '), 'investigation-scope'));
    var states = el('div', undefined, 'investigation-states');
    var findingState = el('span', 'Finding: ' + incidentState(incident), 'investigation-state'); findingState.id = 'investigation-finding-state';
    var executionState = el('span', 'Execution: ' + ((data.execution || {}).status || 'unknown')); executionState.id = 'investigation-execution-state';
    states.append(findingState, executionState);
    if (incident && incident.acknowledged_at) states.append(el('span', 'Acknowledged ' + when(incident.acknowledged_at)));
    head.append(states); panel.append(head);
    if (incident) {
      panel.append(el('p', incident.detail || 'Review the recorded evidence below.', 'investigation-explanation'));
      var facts = el('dl', undefined, 'investigation-facts');
      function fact(name, value) { var group = el('div'); group.append(el('dt', name), el('dd', value)); facts.append(group); }
      fact('First observed', when(incident.first_seen));
      fact('Latest evidence', when(incident.last_evidence_at));
      var cost = incident.spend_at_risk_usd;
      fact('Cost at risk', incident.cost_provenance === 'unknown' || cost == null ? 'Unknown' :
        '$' + Number(cost).toFixed(4) + ' estimated (' + String(incident.spend_basis || '').replace(/_/g, ' ') + ')');
      if (incident.recovered_at) fact('Recovery observed', when(incident.recovered_at));
      panel.append(facts);
      var next = incidentState(incident) === 'Recovered' ? 'Review the successful result to see what changed.' :
        incidentState(incident) === 'Stale' ? 'Reconnect the node or resume observing before deciding whether this is still happening.' :
        incident.kind === 'repeated_tool_failure' ? 'Review the first failed result, then check the tool inputs and permissions.' :
        'Review the repeated calls and their inputs before deciding how to respond.';
      panel.append(el('p', next, 'investigation-next'));
      panel.append(button(incident.acknowledged_at ? 'Undo acknowledgement' : 'Acknowledge finding', acknowledge));
    }
    var notice = el('div', undefined, 'investigation-coverage');
    notice.setAttribute('role', 'status');
    var missing = coverage.missing_event_ids || [];
    notice.append(el('p', missing.length ? missing.length + ' referenced events are outside the retained history or unavailable on this node.' :
      'The available referenced evidence is highlighted below.'));
    if (coverage.retention_days != null) notice.append(el('p', 'This node keeps up to ' + coverage.retention_days + ' days of event history.'));
    if ((coverage.payload_truncated_ids || []).length) notice.append(el('p', 'Large event bodies are shortened and marked as previews.'));
    if (coverage.incident_available === false) notice.append(el('p', 'This finding is unavailable in the selected scope. No recovery has been inferred.'));
    panel.append(notice);
    var msg = el('p', '', 'investigation-message'); msg.id = 'investigation-message'; msg.setAttribute('role', 'status'); panel.append(msg);
    var live = el('p', 'Reading persisted activity...', 'section-sub'); live.id = 'investigation-live-status'; live.setAttribute('role', 'status'); panel.append(live);
    panel.append(button('Follow latest activity', startLive));
    panel.append(el('h4', 'Recorded activity'));
    var list = el('div', undefined, 'investigation-events'); list.id = 'investigation-events'; panel.append(list);
    renderEvents();
    var more = button('Load older activity', loadMore); more.id = 'investigation-more'; more.hidden = !state.cursor; panel.append(more);
    var selected = list.querySelector('[data-evidence="true"]');
    if (selected) selected.open = true;
  }

  function renderEvents() {
    var list = byId('investigation-events'); if (!list) return;
    list.replaceChildren();
    var incident = state.data.incident || {};
    var refs = new Set((incident.evidence_refs || []).map(function (r) { return r.event_id; }));
    var recovery = (incident.recovery_ref || {}).event_id;
    var rows = Array.from(state.rows.values()).sort(function (a, b) {
      return String(a.ts).localeCompare(String(b.ts)) || String(a.id).localeCompare(String(b.id));
    });
    if (!rows.length) list.append(el('p', 'No retained events are available in this scope.'));
    rows.forEach(function (row) {
      var evidence = refs.has(row.id), recovered = row.id === recovery;
      var item = el('details', undefined, 'investigation-event');
      item.dataset.eventId = row.id; item.dataset.evidence = String(evidence);
      if (recovered) item.dataset.recovery = 'true';
      var summary = el('summary');
      summary.append(el('time', when(row.ts)), el('strong', row.event_type || 'Event'));
      if (evidence || recovered) summary.append(el('span', recovered ? 'Recovery evidence' : 'Finding evidence', 'investigation-evidence-label'));
      item.append(summary, el('p', row.id, 'investigation-event-id'));
      var pre = el('pre', JSON.stringify(row.data, null, 2)); item.append(pre);
      list.append(item);
    });
  }

  function loadMore() {
    if (state.loading || !state.cursor) return;
    stopLive();
    var generation = state.generation; state.loading = true;
    var more = byId('investigation-more'); more.disabled = true;
    request('/api/investigation?' + args(Object.assign({}, state.scope, {cursor: state.cursor}))).then(function (data) {
      if (generation !== state.generation) return;
      if (data.resync_required) { message('The continuation is no longer available. Reopen this finding to refresh.'); return; }
      (data.rows || []).forEach(function (row) { state.rows.set(row.id, row); });
      state.cursor = (data.coverage || {}).next_cursor;
      trimRows(); renderEvents(); more.hidden = !state.cursor;
      message(state.rows.size + ' retained events loaded.');
    }).catch(function () { if (generation === state.generation) message('Could not load older activity. Reconnect to the node and try again.'); })
      .finally(function () { if (generation === state.generation) { state.loading = false; more.disabled = false; } });
  }

  function stopLive() {
    watchGeneration += 1;
    if (stopWatching) stopWatching();
    stopWatching = null;
    var status = byId('investigation-live-status');
    if (status) status.textContent = 'Reading older activity. Follow latest activity to resume updates.';
  }
  function trimRows() {
    var keep = new Set(((state.data.incident || {}).evidence_refs || []).map(function (ref) { return ref.event_id; }));
    keep.add(((state.data.incident || {}).recovery_ref || {}).event_id);
    for (var id of state.rows.keys()) {
      if (state.rows.size <= 1000) break;
      if (!keep.has(id)) state.rows.delete(id);
    }
  }
  function startLive() {
    if (!window.cmWatchActivity || !state.scope || !state.data) return;
    stopLive();
    var generation = state.generation, watching = watchGeneration;
    stopWatching = window.cmWatchActivity(state.scope, function (page, error) {
      if (generation !== state.generation || watching !== watchGeneration) return;
      var status = byId('investigation-live-status');
      if (error) { if (status) status.textContent = 'Connection unavailable. Recorded activity remains visible; recovery has not been inferred.'; return; }
      if (page.resync_required) { window.cmLoadInvestigation(state.scope); return; }
      var finding = (page.incidents || []).find(function (row) { return row.incident_id === state.scope.incident_id; });
      if (finding) state.data.incident = finding;
      if (page.execution) state.data.execution = page.execution;
      var findingState = byId('investigation-finding-state'), executionState = byId('investigation-execution-state');
      if (findingState) findingState.textContent = 'Finding: ' + incidentState(state.data.incident);
      if (executionState) executionState.textContent = 'Execution: ' + ((state.data.execution || {}).status || 'unknown');
      (page.removed_ids || []).forEach(function (id) { state.rows.delete(id); });
      (page.rows || []).forEach(function (row) { state.rows.set(row.id, row); });
      trimRows(); renderEvents();
      var latest = Array.from(state.rows.values()).reduce(function (last, row) {
        var at = new Date(row.ts).getTime(); return Number.isFinite(at) ? Math.max(last, at) : last;
      }, 0);
      if (status) status.textContent = (page.from_cache ? 'Showing recorded activity while reconnecting. ' : 'Connected to persisted activity. ') + 'Latest observed: ' + when(latest) + '. Showing up to 1,000 events.';
    }, 'tracing');
  }

  function acknowledge(event) {
    var control = event.currentTarget, incident = state.data.incident, generation = state.generation;
    control.disabled = true;
    request('/api/guard/incidents/' + encodeURIComponent(incident.incident_id) + '/acknowledge', {
      method: 'POST', headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({acknowledged: !incident.acknowledged_at})
    }).then(function (data) {
      if (generation !== state.generation) return;
      if (!data.incident) { message('Awaiting confirmation from the node.'); return; }
      state.data.incident = data.incident; render(); message('Acknowledgement saved. Recovery and session controls are unchanged.');
    }).catch(function () { if (generation === state.generation) message('Acknowledgement was not confirmed. Reconnect and try again.'); })
      .finally(function () { control.disabled = false; });
  }

  window.cmLoadIncidentHistory = function () {
    var target = byId('guard-incident-history'); if (!target) return Promise.resolve();
    var runtime = typeof _cmRuntimeFilter === 'function' ? _cmRuntimeFilter() : '';
    var scope = runtime && runtime !== 'all' ? {runtime: runtime} : {};
    var key = args(scope), generation = ++historyGeneration;
    var pending = historyRequests.get(key);
    if (!pending) {
      pending = request('/api/guard/incidents?' + key).finally(function () { historyRequests.delete(key); });
      historyRequests.set(key, pending);
    }
    return pending.then(function (data) {
      if (generation !== historyGeneration) return;
      target.replaceChildren();
      if (!(data.rows || []).length) { target.append(el('p', 'No recorded loop or repeated tool failure episodes yet.', 'section-sub')); return; }
      data.rows.forEach(function (incident) {
        var row = el('article', undefined, 'investigation-history-row');
        var copy = el('div'); copy.append(el('strong', incident.title || incident.kind),
          el('p', incident.runtime + ' · ' + incidentState(incident) + ' · First observed ' + when(incident.first_seen)));
        row.append(copy, button('See what happened', function () {
          window.cmOpenIncident(incident.incident_id, incident.runtime, incident.session_id, incident.node_id);
        })); target.append(row);
      });
    }).catch(function () {
      if (generation === historyGeneration) target.replaceChildren(el('p', 'Finding history is unavailable. Reconnect to this node, then refresh.'));
    });
  };
}());
