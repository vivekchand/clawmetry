/* Bounded error groups, loaded only while the triage details are open. */
(function () {
  'use strict';
  var inFlight = null, cached = null, loadedAt = 0, generation = 0;
  function el(tag, text) { var item = document.createElement(tag); if (text != null) item.textContent = text; return item; }
  function visible() {
    var panel = document.getElementById('triage-groups');
    return panel && panel.open && !document.hidden && (!window._cmCurrentTab || window._cmCurrentTab === 'overview');
  }
  function runtime() { var rt = typeof _cmRuntimeFilter === 'function' ? _cmRuntimeFilter() : ''; return rt && rt !== 'all' ? rt : ''; }
  function render(body) {
    var host = document.getElementById('triage-groups-body'); if (!host) return;
    host.replaceChildren();
    if (body.available === false) { host.append(el('p', body.reason || 'Error groups are unavailable. Reconnect this node and try again.')); return; }
    var coverage = body.coverage || {}, groups = body.rows || [];
    host.append(el('p', 'Counts cover ' + (coverage.events_scanned || 0) + ' recorded errors in the selected window' +
      (coverage.truncated ? '. More errors exist beyond this read limit.' : '.') +
      ' Resolving an event applies only to that occurrence.'));
    if (coverage.from_ms) host.append(el('p', new Date(coverage.from_ms).toLocaleString() + ' to ' + new Date(coverage.to_ms).toLocaleString()));
    if (!groups.length) host.append(el('p', 'No recorded errors in this window.'));
    groups.forEach(function (group) {
      var card = el('details'); card.className = 'investigation-event';
      var summary = el('summary');
      summary.append(el('strong', group.message), el('span', group.occurrence_count + ' occurrences · ' +
        group.session_count + (group.session_count === 1 ? ' session · ' : ' sessions · ') + group.unresolved_count + ' unresolved'));
      card.append(summary, el('p', [group.runtime, group.provider, group.tool, group.category].join(' · ')));
      if (!group.normalization_eligible) card.append(el('p', 'Details are incomplete. This occurrence is kept separate.'));
      if (group.first_seen) card.append(el('p', 'First observed ' + new Date(group.first_seen).toLocaleString() +
        ' · Latest observed ' + new Date(group.last_seen).toLocaleString()));
      (group.representatives || []).forEach(function (row) {
        var example = el('div'); example.append(el('p', row.preview || 'No retained message preview'));
        var link = el('button', row.resolved ? 'See resolved occurrence' : 'See what happened');
        link.type = 'button'; link.className = 'refresh-btn';
        link.disabled = !(row.node_id && row.runtime && row.session_id && row.event_id);
        link.addEventListener('click', function () { window.cmOpenEvidence(row.runtime, row.session_id, row.node_id, row.event_id); });
        example.append(link); card.append(example);
      });
      host.append(card);
    });
  }
  window.cmLoadErrorGroups = function (force) {
    if (!visible()) return Promise.resolve();
    var rt = runtime(), node = window.CLOUD_NODE_ID || '', key = node + ':' + rt, current = ++generation;
    if (!force && cached && cached.key === key && Date.now() - loadedAt < 30000) { render(cached.body); return Promise.resolve(); }
    if (!inFlight || inFlight.key !== key) {
      if (inFlight) inFlight.controller.abort();
      var controller = new AbortController();
      var task = fetch('/api/error-triage/groups?days=7&limit=500&runtime=' + encodeURIComponent(rt), {signal: controller.signal})
        .then(function (response) { return response.json().then(function (body) {
          if (!response.ok) return {available:false, reason:body.reason || body.hint || 'Error groups are unavailable on this node.'};
          return body;
        }); });
      inFlight = {key:key, task:task, controller:controller};
      task.finally(function () { if (inFlight && inFlight.task === task) inFlight = null; }).catch(function () {});
    }
    return inFlight.task.then(function (body) {
      if (current !== generation || !visible() || rt !== runtime() || node !== (window.CLOUD_NODE_ID || '')) return;
      cached = {key:key, body:body}; loadedAt = Date.now(); render(body);
    }).catch(function () {
      if (current === generation && visible()) render({available:false, reason:'Error groups could not be read. Reconnect this node and try again.'});
    });
  };
  window.cmErrorGroupsVisibilityChanged = function () {
    if (!visible() && inFlight) { generation += 1; inFlight.controller.abort(); }
  };
  document.addEventListener('visibilitychange', function () {
    if (document.hidden && inFlight) { generation += 1; inFlight.controller.abort(); }
  });
}());
