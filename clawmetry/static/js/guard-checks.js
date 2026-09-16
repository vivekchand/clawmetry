/* Guard's catalogue is supplied by the node, never a second detector list. */
(function () {
  'use strict';
  var state = {view: 'checks', family: 'progress', data: null, loading: null, saving: {}, pending: {}};
  var pendingKey = 'cm-guard-pending-' + (window.CLOUD_NODE_ID || 'local') + '-' + (window.CLOUD_TOKEN || '').slice(0, 16);
  try {
    var saved = JSON.parse(window.sessionStorage.getItem(pendingKey) || '{}');
    Object.keys(saved).forEach(function (kind) {
      var p = saved[kind];
      if (p && typeof p.next === 'boolean' && Number.isFinite(p.at) && Date.now() - p.at < 600000) state.pending[kind] = p;
    });
  } catch (e) { /* Storage may be unavailable in a private browser. */ }
  function savePending() {
    try { window.sessionStorage.setItem(pendingKey, JSON.stringify(state.pending)); } catch (e) {}
  }
  function esc(value) { return guardEsc(value); }
  function byId(id) { return document.getElementById(id); }
  function say(message) { var el = byId('guard-check-message'); if (el) el.textContent = message; }

  window.guardShowView = function (view) {
    if (['checks', 'attention', 'activity', 'settings'].indexOf(view) < 0) return;
    state.view = view;
    document.querySelectorAll('[data-guard-panel]').forEach(function (el) { el.hidden = el.dataset.guardPanel !== view; });
    document.querySelectorAll('[data-guard-view]').forEach(function (el) {
      if (el.dataset.guardView === view) el.setAttribute('aria-current', 'page');
      else el.removeAttribute('aria-current');
    });
    if (view === 'checks') loadChecks();
    if (view === 'attention') { loadGuardSessions(); if (typeof guardLoadApprovalSummary === 'function') guardLoadApprovalSummary(); }
    if (view === 'activity') { loadGuardActions(); loadGuardSelfReports(); }
    if (view === 'settings') { loadGuardPolicies(); loadGuardNondeterminism(); }
  };
  window.guardOpenRelated = function (tab, panel) {
    switchTab(tab);
    var el = byId(panel); if (el) { el.open = true; el.scrollIntoView({block: 'start'}); }
  };
  window.guardLoadWorkspace = function () { window.guardShowView(state.view); };

  function render() {
    var d = state.data;
    if (!d) return;
    var checks = Array.isArray(d.checks) ? d.checks : [];
    var families = Array.isArray(d.families) ? d.families : [];
    var summary = byId('guard-check-summary');
    var status = !d.available ? 'Check settings are not available from this node yet.'
      : !d.engine_enabled ? 'Detection is turned off by an administrator on this node.'
      : d.last_pass_ms && Date.now() - d.last_pass_ms < 180000 ? 'Last detection pass ' + guardAgo(d.last_pass_ms) + '.'
      : 'Waiting for a recent detection pass. Enabled does not mean a check has run.';
    summary.innerHTML = '<div>' + (checks.length ? '<strong>' + checks.length + '</strong> checks available' : 'Waiting for the check catalogue') +
      (d.available ? '<span class="guard-coverage-divider"></span><strong>' + Number(d.enabled || 0) + '</strong> enabled' : '') +
      '</div><p>' + esc(d.reason || status) + '</p>';
    if (!families.some(function (f) { return f.id === state.family; })) state.family = families.length ? families[0].id : '';
    byId('guard-check-families').innerHTML = families.map(function (f) {
      var count = checks.filter(function (c) { return c.family === f.id; }).length;
      return '<button type="button" data-family="' + esc(f.id) + '" aria-pressed="' + (f.id === state.family) + '">' +
        '<span>' + esc(f.title) + '</span><span class="guard-family-count">' + count + '</span></button>';
    }).join('');
    var family = families.find(function (f) { return f.id === state.family; });
    byId('guard-check-question').textContent = family ? family.question : '';
    byId('guard-check-list').innerHTML = checks.filter(function (c) { return c.family === state.family; }).map(function (c) {
      var busy = !!state.saving[c.kind];
      var pending = state.pending[c.kind];
      var unavailable = !d.available || c.state === 'unknown';
      var label = busy ? 'Saving...' : pending ? 'Awaiting node' : c.state === 'overridden' ? 'Off on this node' : unavailable ? 'Unknown' : c.enabled ? 'On' : 'Off';
      var disabled = busy || !!pending || unavailable || c.state === 'overridden';
      return '<article class="guard-check-row"><div class="guard-check-copy"><h4>' + esc(c.title) + '</h4><p>' + esc(c.description) + '</p>' +
        '<details><summary>How this check works</summary><p>' +
        esc(c.scope === 'workspace' ? 'Inspects the workspace used by active sessions.' : c.scope === 'fleet' ? 'Compares independent active session families across this node.' : 'Examines the recent activity of each active session.') +
        ' Findings keep the matching evidence for review. Detection alone does not prevent an action.</p>' +
        '<p>Turning this off stops new findings and automatic responses that depend on this check. Previous findings and pending approvals stay in place.</p>' +
        '<button class="btn btn-sm" onclick="guardShowView(\'settings\')">Response settings</button></details></div>' +
        '<div class="guard-check-control"><span>' + esc(label) + '</span><button type="button" role="switch" class="guard-check-switch" aria-label="' + esc(c.title) +
        '" aria-checked="' + (c.effective_enabled === true) + '" data-check="' + esc(c.kind) + '"' + (disabled ? ' disabled' : '') + '><span></span></button></div></article>';
    }).join('') || '<p class="guard-scope-note">The check catalogue arrives with your node\'s next snapshot. Refresh once the node is connected.</p>';
  }

  function loadChecks() {
    if (state.loading) return state.loading;
    state.loading = fetch('/api/guard/checks').then(function (r) {
      if (!r.ok) throw new Error('unavailable');
      return r.json();
    }).then(function (d) {
      Object.keys(state.pending).forEach(function (kind) {
        var p = state.pending[kind], c = (d.checks || []).find(function (c) { return c.kind === kind; });
        if (d.available && c && Number(d.generated_at) >= p.at && c.enabled === p.next) {
          delete state.pending[kind]; say(c.title + (c.enabled ? ' is on.' : ' is off.'));
        } else if (Date.now() - p.at > 600000) {
          delete state.pending[kind]; say('The node did not confirm the change in time. Review its current setting before trying again.');
        }
      });
      savePending();
      state.data = d; render();
      if (Object.keys(state.pending).length) say('A change is awaiting your node. The last confirmed setting is still shown. Refresh when the node is connected.');
    }).catch(function () {
      if (state.data) { state.data.available = false; render(); }
      byId('guard-check-summary').textContent = 'Could not read check settings. Make sure this node is connected, then refresh.';
    }).finally(function () { state.loading = null; });
    return state.loading;
  }

  async function changeCheck(kind) {
    var check = state.data && state.data.checks.find(function (c) { return c.kind === kind; });
    if (!check || state.saving[kind] || state.pending[kind]) return;
    var next = !check.enabled;
    if (!next && !window.confirm('Turn off ' + check.title + '? This stops new findings and automatic responses that depend on this check. Existing findings and approvals stay in place.')) return;
    // A reload while the request is in flight must not forget a queued write.
    state.pending[kind] = {next: next, at: Date.now()}; savePending();
    state.saving[kind] = true; say('Saving this setting on your node...'); render();
    try {
      var r = await fetch('/api/guard/checks/' + encodeURIComponent(kind), {
        method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({enabled: next})
      });
      var d = await r.json();
      if (d.pending) {
        say('Your node has not confirmed this change yet. Its last confirmed setting is still shown. Refresh when the node is connected.');
        return;
      }
      if (!r.ok || !d.ok || d.applied !== true || d.kind !== kind || d.enabled !== next) {
        delete state.pending[kind]; savePending(); throw new Error('not saved');
      }
      delete state.pending[kind]; savePending();
      // A node-confirmed reply is newer than the cached cloud snapshot.
      check.enabled = next; check.effective_enabled = next; check.state = next ? 'on' : 'off';
      if (d.checks && d.checks.available) state.data = d.checks;
      state.data.enabled = state.data.checks.filter(function (c) { return c.effective_enabled === true; }).length;
      var confirmed = state.data.checks.find(function (c) { return c.kind === kind; });
      say(confirmed && confirmed.state === 'overridden' ? 'Preference saved. This check is still turned off by an administrator on this node.' :
        check.title + (next ? ' is on. It will run on the next detection pass.' : ' is off. Existing findings and approvals are unchanged.'));
    } catch (e) {
      say('Could not confirm the change. The last confirmed setting is still shown. Refresh to check your node\'s current setting.');
    } finally { delete state.saving[kind]; render(); }
  }

  document.addEventListener('click', function (event) {
    var family = event.target.closest('#guard-check-families [data-family]');
    if (family) { state.family = family.dataset.family; render(); }
    var toggle = event.target.closest('[data-check]');
    if (toggle && !toggle.disabled) changeCheck(toggle.dataset.check);
  });
})();
