/* First-install readiness. One bounded request at a time, only while visible.
 * Cloud reads the shared decrypted snapshot, never the cloud host's store. */
(function () {
  'use strict';
  var timer = null, deadline = null, busy = false, stopped = false, started = false;
  var shown = false, failures = 0, priorFocus = null;
  var resolveCheck;
  var api = window.cmFirstRun = {
    active: false, checking: true,
    checked: new Promise(function (resolve) { resolveCheck = resolve; }),
    start: start
  };
  var keyPrefix = 'cm-first-run-opened:' + window.location.pathname + ':';
  var key = keyPrefix + 'pending';
  function el(id) { return document.getElementById('first-run' + (id ? '-' + id : '')); }
  function text(id, value) { var node = el(id); if (node) node.textContent = value; }
  function checked() { api.checking = false; resolveCheck(); }
  // The onboarding state request itself can fail or hang. Keep ordinary
  // dashboard boot usable even when this optional feature cannot start.
  setTimeout(checked, 6500);

  function show() {
    if (!el('') || shown) return;
    shown = true;
    api.active = true;
    priorFocus = document.activeElement;
    el('').hidden = false;
    document.body.classList.add('first-run-active');
    var dashboard = document.getElementById('zoom-wrapper');
    if (dashboard) dashboard.inert = true;
    el('title').focus();
  }
  function stop() {
    stopped = true;
    clearTimeout(timer); clearTimeout(deadline);
    document.removeEventListener('visibilitychange', onVisible);
  }
  function close(remember, refreshed) {
    stop(); checked(); api.active = false;
    if (remember) try { localStorage.setItem(key, '1'); } catch (e) {}
    if (el('')) el('').hidden = true;
    document.body.classList.remove('first-run-active');
    var dashboard = document.getElementById('zoom-wrapper');
    if (dashboard) dashboard.inert = false;
    if (shown && priorFocus && priorFocus.isConnected) priorFocus.focus();
    // Refresh only the screen the user is about to see. It may have loaded
    // before ingestion finished; do not expose that stale empty rendering.
    if (shown && !refreshed && typeof window.switchTab === 'function') {
      var active = document.querySelector('.page.active');
      if (active) window.switchTab(active.id.replace(/^page-/, ''));
    }
  }
  async function openReady() {
    var active = document.querySelector('.page.active');
    if (shown && active && active.id === 'page-transcripts' && typeof window.loadTranscripts === 'function') {
      // Keep the screen covered until the landing list has fetched the newly
      // ingested history. The boot-time list may still contain zero rows.
      stop();
      step('history', 'done', '2'); step('dashboard', 'active', '3');
      text('status', 'Opening your dashboard…');
      var timeout;
      try {
        var rendered = await Promise.race([
          window.loadTranscripts(),
          new Promise(function (_, reject) { timeout = setTimeout(function () { reject(new Error('dashboard delayed')); }, 10000); })
        ]);
        if (rendered === false) throw new Error('dashboard unavailable');
      } catch (e) { if (api.active) settle('delayed'); return; }
      finally { clearTimeout(timeout); }
      if (api.active) close(true, true);
      return;
    }
    close(true);
  }
  function step(id, state, number) {
    var node = el(id);
    if (!node) return;
    node.dataset.state = state;
    node.querySelector('.first-run-check').textContent = state === 'done' ? '✓' : number;
    node.querySelector('small').textContent = state === 'done' ? 'Ready' : state === 'active' ? 'In progress' : 'Waiting';
  }
  function settle(kind) {
    stop(); show(); checked();
    el('').dataset.settled = kind;
    el('retry').hidden = false;
    text('continue', 'Open dashboard');
    if (kind === 'empty') {
      step('discover', 'done', '1'); step('history', 'done', '2');
      text('title', 'Ready for your first activity');
      text('description', 'Setup has finished. There is no agent activity to show yet.');
      text('status', 'Run a task with your AI agent to get started.');
      text('help', 'Activity on this machine appears automatically. You can open the dashboard now and come back after your first task.');
    } else {
      text('title', 'Your dashboard is taking a little longer');
      text('description', 'ClawMetry has not confirmed that your agent history is ready yet.');
      text('status', 'You can check again or open the dashboard now.');
      text('help', 'If activity stays missing, open Settings to check the connection to this machine.');
    }
  }
  async function read() {
    var controller = new AbortController();
    var timeout;
    try {
      return await Promise.race([
        (async function () {
          if (window.CLOUD_MODE) {
            if (typeof window.__cmSnap !== 'function') throw new Error('snapshot unavailable');
            var snapshot = await window.__cmSnap();
            if (!snapshot) throw new Error('snapshot pending');
            var fr = snapshot.firstRun;
            if (fr && fr.readiness) return fr.readiness;
            // Compatibility with already-installed daemons. A populated
            // snapshot is enough to avoid gating an established install.
            var hasData = Number(snapshot.sessionCount) > 0 || (Array.isArray(snapshot.transcripts) && snapshot.transcripts.length > 0);
            return { available: true, initialized: hasData || !!(fr && fr.done), has_data: hasData, phase: fr && fr.phase };
          }
          var response = await fetch('/api/onboarding/readiness', { signal: controller.signal });
          if (!response.ok) throw new Error('readiness unavailable');
          return await response.json();
        })(),
        new Promise(function (_, reject) {
          timeout = setTimeout(function () { controller.abort(); reject(new Error('readiness delayed')); }, 5000);
        })
      ]);
    } finally { clearTimeout(timeout); }
  }
  async function poll() {
    if (stopped || busy || document.hidden) return;
    busy = true;
    try {
      var status = await read();
      if (stopped) return;
      if (!status || status.available !== true || typeof status.initialized !== 'boolean' || typeof status.has_data !== 'boolean') throw new Error('invalid readiness');
      // Scope dismissal to this installation's durable startup record. A
      // reinstall on the same localhost origin must get its own preparation.
      key = keyPrefix + (status.started_at || 'pending');
      try { if (localStorage.getItem(key) === '1') { close(false); return; } } catch (e) {}
      failures = 0;
      if (status.initialized) {
        if (status.has_data) { await openReady(); return; }
        settle('empty'); return;
      }
      show(); checked();
      var discovered = !!status.phase && status.phase !== 'discovering';
      step('discover', discovered ? 'done' : 'active', '1');
      step('history', discovered ? 'active' : '', '2');
      if (status.phase === 'preparing') {
        step('history', 'done', '2'); step('dashboard', 'active', '3');
        text('status', 'Preparing your dashboard…');
      } else {
        text('status', discovered ? 'Preparing your recent agent history…' : 'Looking for your agent activity…');
      }
      if (Number.isFinite(Number(status.total)) && Number(status.done) > 0 && Number(status.total) >= Number(status.done)) {
        text('status', Number(status.done).toLocaleString() + ' of ' + Number(status.total).toLocaleString() + ' items prepared in this step');
      }
    } catch (e) {
      if (stopped) return;
      failures++;
      // Unknown is not empty, and a failed probe must not silently reveal
      // an apparently broken dashboard to a first-time user.
      show(); checked();
      text('status', 'Waiting for ClawMetry to report progress…');
      if (failures >= 3) text('help', 'The first collection can take a few minutes. You can open the dashboard while ClawMetry keeps preparing.');
    } finally { busy = false; }
    if (!stopped) timer = setTimeout(poll, window.CLOUD_MODE ? 8000 : 5000);
  }
  function onVisible() {
    if (!document.hidden && !stopped) { clearTimeout(timer); poll(); }
  }
  function run() {
    stopped = false; failures = 0;
    if (el('')) delete el('').dataset.settled;
    el('retry').hidden = true;
    text('title', 'Getting your dashboard ready');
    text('description', 'ClawMetry is gathering your agent activity and preparing your history. Your first setup may take a few minutes.');
    text('help', 'This page will open automatically when it is ready.');
    step('discover', 'active', '1'); step('history', '', '2'); step('dashboard', '', '3');
    document.addEventListener('visibilitychange', onVisible);
    deadline = setTimeout(function () { settle('delayed'); }, 180000);
    poll();
  }
  function start(onboarding) {
    if (started) return;
    started = true;
    // The cloud key prompt reloads after unlocking. Let that prerequisite
    // finish before waiting for a snapshot; support view has no data key.
    if (window.CLOUD_MODE && (window._cmKeyNeeded || window.CM_SUPPORT_VIEW)) { checked(); return; }
    if (!el('') || (!window.CLOUD_MODE && (!onboarding || onboarding.required || ['ci', 'env_skip', 'error'].indexOf(onboarding.source) !== -1))) { checked(); return; }
    el('continue').addEventListener('click', function () { close(true); });
    el('retry').addEventListener('click', run);
    el('').addEventListener('keydown', function (event) {
      if (event.key !== 'Tab') return;
      var first = el('retry').hidden ? el('continue') : el('retry');
      var last = el('continue');
      if (event.shiftKey && (document.activeElement === first || document.activeElement === el('title'))) {
        event.preventDefault(); last.focus();
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault(); first.focus();
      }
    });
    run();
  }
  document.addEventListener('DOMContentLoaded', function () { if (window.CLOUD_MODE) start(); });
})();
