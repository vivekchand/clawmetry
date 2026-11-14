/* Persisted robot evidence only. No SDK, media, or motion connection. */
(function () {
  'use strict';
  var state = {runs: [], selected: null, events: [], after: 0, moreEvents: false,
    traceWindow: null, cursor: null, moreRuns: false, loading: null, timer: null, generation: 0, stopped: false};
  var controller = null, deadline = null;
  function node(id) { return document.getElementById('asimov-' + id); }
  function text(id, value) { var el = node(id); if (el) el.textContent = value; }
  function hidden(id, value) { var el = node(id); if (el) el.hidden = value; }
  function element(tag, value, className) {
    var el = document.createElement(tag);
    if (value !== undefined) el.textContent = value;
    if (className) el.className = className;
    return el;
  }
  function number(value, unit) {
    return typeof value === 'number' && Number.isFinite(value)
      ? value.toLocaleString(undefined, {maximumFractionDigits: 4}) + (unit || '') : 'Not reported';
  }
  function plain(value) {
    if (value === undefined || value === null || value === '') return 'Not reported';
    return typeof value === 'object' ? JSON.stringify(value) : String(value);
  }
  function firstValue(values) {
    return values.find(function (value) { return value !== null && value !== undefined; });
  }
  function vector(value) { return Array.isArray(value) ? value.map(function (v) { return number(v); }).join(', ') : 'Not reported'; }
  function timestamp(value) {
    // Keep the original decimal string for evidence. Convert only for a human date.
    if (!/^[0-9]{1,19}$/.test(String(value))) return 'Not reported';
    var date = new Date(Number(value) / 1000000);
    return Number.isFinite(date.getTime()) ? date.toLocaleString() : 'Not reported';
  }
  function source(run) { return run.source_kind === 'asimov_recording' ? 'Imported recording' : 'SDK observation'; }
  function observationAge(run) {
    // Receipt time is an epoch clock from the collector. Never use a firmware clock.
    if (run.observation_received_at_ns !== undefined) {
      var stamp = run.observation_received_at_ns;
      if (typeof stamp !== 'string' || !/^[0-9]{1,19}$/.test(stamp)) return null;
      var receivedMs = Number(stamp) / 1000000;
      var elapsed = Date.now() - receivedMs;
      // Future receipt clocks can indicate clock skew. They do not prove freshness.
      return receivedMs > 0 && Number.isFinite(elapsed) && elapsed >= 0 ? elapsed / 1000 : null;
    }
    if (window.CLOUD_MODE || snapshot() !== undefined) return null;
    if (typeof run.observation_age_s !== 'number' || !Number.isFinite(run.observation_age_s) || run.observation_age_s < 0) return null;
    return Math.max(0, run.observation_age_s + (run._client_received_ms ? Math.max(0, Date.now() - run._client_received_ms) / 1000 : 0));
  }
  function status(run) {
    if (run.source_kind === 'asimov_recording') return 'recorded';
    if (run.status === 'live' && observationAge(run) === null) return 'unknown';
    if (run.status === 'live' && observationAge(run) >= 5) return 'stale';
    return ['live', 'stale', 'disconnected', 'ended'].indexOf(run.status) >= 0 ? run.status : 'unknown';
  }
  function visible() { return !state.stopped && !document.hidden && !!node('app'); }
  function setMessage(message) { text('message', message); }
  function selectedRun() { return state.runs.find(function (r) { return r.run_id === state.selected; }); }
  function renderRuns() {
    var list = node('runs');
    if (!list) return;
    list.replaceChildren();
    state.runs.forEach(function (run) {
      var button = element('button', undefined, 'asimov-run');
      button.type = 'button';
      button.setAttribute('aria-pressed', String(run.run_id === state.selected));
      button.append(element('strong', plain(run.robot_id)));
      button.append(element('span', source(run) + ' / ' + plain(run.environment)));
      button.append(element('span', timestamp(run.started_ns)));
      button.addEventListener('click', function () { select(run.run_id); });
      list.append(button);
    });
    hidden('more-runs', !state.moreRuns);
  }
  function renderRun() {
    var run = selectedRun();
    hidden('empty', state.runs.length > 0);
    hidden('workbench', !run);
    if (!run) return;
    var observation = run.observation || {}, base = observation.base || {}, battery = observation.battery;
    text('robot', plain(run.robot_id));
    text('source', source(run) + ' / ' + plain(run.environment));
    var label = status(run);
    text('status', {recorded: 'Recorded', live: 'Receiving state', stale: 'State is stale',
      disconnected: 'Disconnected', ended: 'Run ended', unknown: 'State unknown'}[label]);
    node('status').dataset.status = label;
    text('freshness', label === 'recorded' ? 'Recorded evidence. This source does not report a live connection.'
      : observationAge(run) === null ? 'Observation freshness is unknown. Check the collector clock and connection.'
      : 'Latest stored observation age: ' + number(observationAge(run), ' s') + '.');
    text('mode', plain(observation.mode));
    text('battery', battery ? number(battery.soc_percent, '%') : 'Not reported');
    if (battery) node('battery').title = 'Voltage: ' + number(battery.voltage_v, ' V') + '. Current: ' + number(battery.current_amp, ' A') + '.';
    else node('battery').removeAttribute('title');
    text('event-count', number(run.event_count));
    text('dropped', number(run.dropped_total));
    text('battery-detail', 'Voltage: ' + number(battery && battery.voltage_v, ' V') + '\nCurrent: ' + number(battery && battery.current_amp, ' A') + '\nMaximum cell temperature: ' + number(battery && battery.max_cell_temperature_c, ' °C') + '\nProtection flags: ' + plain(battery && battery.protection_flags));
    var joints = Array.isArray(observation.joints) ? observation.joints : [];
    var names = run.start && Array.isArray(run.start.joint_names) ? run.start.joint_names : [];
    // An absent sample may still have a declared joint catalogue. Do not invent positions.
    if (!joints.length && names.length) joints = names.map(function (name) { return {name: name}; });
    var table = node('joints'); table.replaceChildren();
    joints.forEach(function (joint) {
      var tr = element('tr'); tr.append(element('td', plain(joint.name)));
      ['position_rad', 'velocity_rad_s', 'current_amp', 'temperature_c'].forEach(function (key) {
        var value = number(joint[key]), cell = element('td', value);
        cell.dataset.missing = String(value === 'Not reported'); tr.append(cell);
      });
      table.append(tr);
    });
    if (!joints.length) {
      var row = element('tr'), cell = element('td', 'Joint measurements are not reported.'); cell.colSpan = 5; row.append(cell); table.append(row);
    }
    text('orientation', vector(base.quaternion_wxyz));
    text('angular', vector(base.angular_velocity_rad_s));
    text('gravity', vector(base.gravity_body));
    var alerts = node('alerts'); alerts.replaceChildren();
    var values = Array.isArray(observation.alerts) ? observation.alerts : observation.alerts == null ? [] : [observation.alerts];
    values.forEach(function (alert) { alerts.append(element('li', plain(alert))); });
    if (!values.length) alerts.append(element('li', observation.alerts == null ? 'Alerts are not reported.' : 'No source alerts in this sample.'));
    text('health', run.health && run.health.incomplete ? 'Some evidence is incomplete. Check the recorder status.' : '');
    text('run-id', 'Run ID: ' + run.run_id);
    text('clock', 'Collector receipt time (ns): ' + plain(run.observation_received_at_ns) + '. Source clock: ' + plain(observation.source_clock) + '. Source wall time (ns): ' + plain(observation.source_wall_time_ns) + '. Firmware time (µs): ' + plain(observation.fw_timestamp_us) + '. Recording time (s): ' + plain(observation.source_timestamp_s) + '.');
    renderEvents();
  }
  function isCommand(event) { return /^command[._]/.test(event.kind || event.type || ''); }
  function renderEvents() {
    var list = node('events'); if (!list) return;
    list.replaceChildren();
    var commands = state.events.filter(isCommand);
    var scope = state.traceWindow && state.traceWindow.scope;
    text('trace-loaded', scope === 'recent'
      ? 'Recent evidence from the node snapshot. ' + number(state.traceWindow.retained) + ' events retained.' + (state.traceWindow.truncated ? ' Earlier evidence is omitted.' : '')
      : scope === 'unavailable' ? 'Command evidence is not included in this snapshot.'
      : number(state.events.length) + ' events loaded from the run history. Only command evidence is shown below.');
    text('trace-empty', scope ? 'No command evidence is present in this snapshot window.' : 'No command evidence is stored in the loaded events.');
    hidden('trace-empty', commands.length > 0);
    commands.forEach(function (event) {
      var kind = event.kind || event.type, data = event.data || {};
      var row = element('li', undefined, 'asimov-event');
      row.append(element('h4', plain(kind) + (data.name || data.method || data.command ? ': ' + plain(data.name || data.method || data.command) : '')));
      row.append(element('p', 'Sequence ' + plain(event.sequence) + '. Receipt time: ' + timestamp(event.wall_time_ns) + '.'));
      row.append(element('p', 'Source clock: ' + plain(firstValue([data.source_wall_time_ns, data.source_time_ns, data.source_timestamp_ns, data.source_timestamp_s])) + '. Outcome unknown.'));
      var detail = element('details'); detail.append(element('summary', 'Recorded evidence'));
      detail.append(element('pre', JSON.stringify(data, null, 2))); row.append(detail); list.append(row);
    });
    hidden('more-events', !state.moreEvents);
  }
  function snapshot() {
    return typeof window.__CM_ASIMOV_SNAPSHOT__ === 'function' ? window.__CM_ASIMOV_SNAPSHOT__() : window.__CM_ASIMOV_SNAPSHOT__;
  }
  function abortable(work, signal) {
    if (!signal) return Promise.resolve(work);
    return new Promise(function (resolve, reject) {
      function cleanup() { signal.removeEventListener('abort', abort); }
      function abort() { cleanup(); reject(new Error('Evidence read was canceled')); }
      if (signal.aborted) { abort(); return; }
      signal.addEventListener('abort', abort, {once: true});
      Promise.resolve(work).then(function (value) { cleanup(); resolve(value); }, function (error) { cleanup(); reject(error); });
    });
  }
  async function read(kind, args, runId, signal) {
    var provider = window.cmAsimovProvider;
    if (provider && typeof provider[kind] === 'function') {
      var provided = kind === 'events' ? provider.events(runId, args, {signal: signal}) : provider.runs(args, {signal: signal});
      return abortable(provided, signal);
    }
    var data = snapshot();
    if (data !== undefined) {
      if (!data || data.available === false) throw new Error('snapshot unavailable');
      if (kind === 'runs') return Array.isArray(data.runs) ? {runs: data.runs, has_more: false} : data.runs || {runs: [], has_more: false};
      var events = (data.events || {})[runId] || [];
      if (!Array.isArray(events)) events = events.events || [];
      var filtered = events.filter(function (event) { return event.sequence > (args.after || 0); });
      var page = filtered.slice(0, args.limit);
      return {events: page, has_more: filtered.length > page.length,
        next_after: page.length ? page[page.length - 1].sequence : args.after,
        trace_window: (data.trace_window || {})[runId] || {scope: data.events ? 'recent' : 'unavailable', retained: events.length, truncated: false}};
    }
    var query = new URLSearchParams();
    Object.keys(args).forEach(function (key) { if (args[key] !== null && args[key] !== undefined) query.set(key, args[key]); });
    var headers = {};
    // Standalone local pages use the same saved gateway token as the dashboard.
    // It stays in a header on this origin and is never sent by a cloud provider.
    if (!window.CLOUD_MODE) {
      try {
        var token = window.localStorage && window.localStorage.getItem('clawmetry-token');
        if (token) headers.Authorization = 'Bearer ' + token;
      } catch (error) { /* Local storage may be unavailable. The server still enforces auth. */ }
    }
    var response = await fetch('/api/asimov/runs' + (kind === 'events' ? '/' + encodeURIComponent(runId) + '/events' : '') + '?' + query,
      {credentials: 'same-origin', headers: headers, signal: signal});
    if (response.status === 401) { var unauthorized = new Error('Sign in required'); unauthorized.code = 401; throw unauthorized; }
    if (!response.ok) throw new Error('evidence unavailable');
    return response.json();
  }
  function schedule() {
    if (state.timer) clearTimeout(state.timer);
    state.timer = null;
    if (visible()) state.timer = setTimeout(function () { state.timer = null; refresh(); }, 3000);
  }
  async function loadEvents(generation, signal) {
    if (!state.selected) return;
    var runId = state.selected;
    var result = await read('events', {after: state.after, limit: 200}, runId, signal);
    if (generation !== state.generation || !visible() || runId !== state.selected) return;
    if (!result || !Array.isArray(result.events)) throw new Error('invalid events');
    var sequences = new Set(state.events.map(function (event) { return event.sequence; }));
    result.events.forEach(function (event) { if (!sequences.has(event.sequence)) { state.events.push(event); sequences.add(event.sequence); } });
    // Bound browser memory while retaining the most recent command evidence.
    if (state.events.length > 2000) state.events = state.events.slice(-2000);
    var last = result.events.length ? result.events[result.events.length - 1].sequence : state.after;
    state.after = Math.max(state.after, Number(result.next_after) || Number(last) || 0);
    state.moreEvents = result.has_more === true;
    state.traceWindow = result.trace_window || null;
    renderEvents();
  }
  function begin(work) {
    if (!visible()) return Promise.resolve();
    if (state.loading) return state.loading;
    var generation = state.generation;
    controller = new AbortController();
    var current = controller;
    var timeout = setTimeout(function () { current.abort(); }, 12000);
    deadline = timeout;
    state.loading = Promise.resolve().then(function () { return work(generation, current.signal); })
      .catch(function (error) {
        if (generation === state.generation && visible()) {
          setMessage(error.code === 401 ? 'Open the dashboard to sign in. Then reopen this robot page.'
            : 'ClawMetry cannot read robot evidence. Check the sync daemon or the selected cloud node.');
          if (selectedRun() && status(selectedRun()) !== 'recorded') {
            text('status', 'Stored state unavailable'); node('status').dataset.status = 'stale';
            text('freshness', 'Displayed values may be old. The connection to stored evidence is unavailable.');
          }
        }
      }).finally(function () {
        clearTimeout(timeout);
        if (generation !== state.generation) return;
        controller = null; deadline = null; state.loading = null; schedule();
      });
    return state.loading;
  }
  function refresh(older) {
    return begin(async function (generation, signal) {
      var args = {limit: 20};
      if (older && state.cursor) { args.before_ns = state.cursor.before_ns; args.before_run_id = state.cursor.before_run_id; }
      var result = await read('runs', args, null, signal);
      if (generation !== state.generation || !visible()) return;
      if (!result || !Array.isArray(result.runs)) throw new Error('invalid runs');
      result.runs = result.runs.map(function (run) { return Object.assign({}, run, {_client_received_ms: Date.now()}); });
      if (older) {
        var ids = new Set(state.runs.map(function (r) { return r.run_id; }));
        result.runs.forEach(function (run) { if (!ids.has(run.run_id)) state.runs.push(run); });
      } else {
        var freshIds = new Set(result.runs.map(function (r) { return r.run_id; }));
        state.runs = result.runs.concat(state.runs.filter(function (r) { return !freshIds.has(r.run_id); }));
      }
      if (older || !state.cursor) { state.cursor = result.next_cursor || null; state.moreRuns = result.has_more === true; }
      if (!state.selected && state.runs.length) state.selected = state.runs[0].run_id;
      setMessage(''); renderRuns(); renderRun();
      await loadEvents(generation, signal);
    });
  }
  function select(runId) {
    if (runId === state.selected) return state.loading || Promise.resolve();
    cancel(); state.stopped = false; state.selected = runId; state.events = []; state.after = 0; state.moreEvents = false; state.traceWindow = null;
    renderRuns(); renderRun();
    return begin(loadEvents);
  }
  function cancel() {
    state.generation += 1;
    if (controller) controller.abort();
    if (deadline) clearTimeout(deadline);
    deadline = null;
    if (state.timer) clearTimeout(state.timer);
    controller = null; state.timer = null; state.loading = null;
  }
  function stop() { state.stopped = true; cancel(); }
  function start() { state.stopped = false; return refresh(); }
  function reset(data) {
    cancel(); state.runs = []; state.selected = null; state.events = []; state.after = 0;
    state.cursor = null; state.moreRuns = false; state.moreEvents = false; state.traceWindow = null;
    if (arguments.length) window.__CM_ASIMOV_SNAPSHOT__ = data;
    renderRuns(); renderRun(); return start();
  }
  window.cmAsimov = {reset: reset, start: start, stop: stop, refresh: refresh, select: select,
    number: number, source: source, status: status, timestamp: timestamp, getState: function () { return state; }};
  document.addEventListener('visibilitychange', function () { if (document.hidden) cancel(); else if (!state.stopped) refresh(); });
  window.addEventListener('pagehide', stop);
  window.addEventListener('pageshow', function (event) { if (event.persisted) start(); });
  function init() {
    if (!node('app')) return;
    if (node('more-runs')) node('more-runs').addEventListener('click', function () { refresh(true); });
    if (node('more-events')) node('more-events').addEventListener('click', function () { begin(loadEvents); });
    start();
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init); else init();
}());
