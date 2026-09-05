// Trail page: one session as a story a newcomer can follow.
//
//   1. What it was asked  (INPUTS)    the request + what the agent knew
//   2. What it did        (DECISIONS) replay / trace / turn timing / replay tree
//   3. How it ended       (OUTCOME)   verdict, quality score, code produced, spend
//
// Design rules (FLYWHEEL.md):
//   * REUSE the existing renderers. The transcript replay, the span waterfall
//     and the turn waterfall are the same DOM nodes the Sessions / Tracing /
//     Turn anatomy tabs own (#transcript-viewer, #trace-detail, #ta-detail).
//     While the Trail is open they are re-parented into this page's hosts and
//     driven through their public entry points (viewTranscript, viewTrace,
//     viewTurnAnatomy). On leave they go back where they came from, so
//     openSessionDeepDive() and the three tabs keep working unchanged.
//   * Never invent data. Endpoints that other work streams are still landing
//     (/api/sessions/<id>/context, /api/sessions/<id>/git-outcomes,
//     /api/trail/coverage) may 404 today and on the hosted dashboard; every
//     card renders a plain "not captured yet" state on any non-OK answer.
//   * No blank cards. Every slot has copy for the empty, locked and error case.
//
// Globals used from app.js / i18n.js: t, escHtml, timeAgo, switchTab,
// viewTranscript, viewTrace, viewTurnAnatomy, _cmRuntimeOf, _cmRuntimeLabel,
// _evalsLockedHtml, _cmAttentionBadge, _scoreBadgeColor, cmSafeMarkdown.

(function () {
  'use strict';

  // ── Small helpers ─────────────────────────────────────────────────────────
  function T(key, fallback, vars) {
    try { if (typeof t === 'function') return t(key, vars || null, fallback); } catch (e) {}
    return fallback;
  }
  // Attribute-safe: every value here may land inside a quoted attribute
  // (title="", data-full=""), and app.js's escHtml leaves double quotes alone.
  function esc(s) {
    return String(s == null ? '' : s)
      .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
  }
  function $(id) { return document.getElementById(id); }
  function setHtml(id, html) { var el = $(id); if (el) el.innerHTML = html; }
  function muted(text) { return '<div class="trail-muted">' + esc(text) + '</div>'; }
  function money(n) {
    var v = Number(n);
    if (!isFinite(v)) return '';
    if (v >= 1) return '$' + v.toFixed(2);
    if (v >= 0.01) return '$' + v.toFixed(3);
    return '$' + v.toFixed(4);
  }
  function fmtDuration(ms) {
    var s = Math.max(0, Math.round(Number(ms) / 1000));
    if (!isFinite(s)) return '';
    if (s < 60) return s + 's';
    var m = Math.floor(s / 60), h = Math.floor(m / 60);
    if (h) return h + 'h ' + (m % 60) + 'm';
    return m + 'm ' + (s % 60) + 's';
  }
  function toMs(v) {
    if (v == null || v === '') return 0;
    if (typeof v === 'number') return v > 1e12 ? v : v * 1000;
    var p = Date.parse(String(v));
    return isFinite(p) ? p : 0;
  }
  // fetch that never throws: {ok, status, data}. data is parsed JSON or null.
  async function jget(url) {
    try {
      var r = await fetch(url, { headers: { 'Accept': 'application/json' } });
      var data = null;
      try { data = await r.json(); } catch (e) { data = null; }
      return { ok: r.ok, status: r.status, data: data };
    } catch (e) {
      return { ok: false, status: 0, data: null };
    }
  }
  // Endpoints the hosted dashboard has no cm-cloud-* interceptor for yet.
  // Fetching them there would only log a 404 in the console (FLYWHEEL 0a.1),
  // so on cloud they resolve straight to the honest "not captured" state.
  var NOT_ON_CLOUD = { ok: false, status: 404, data: null };
  async function jgetLocal(url) {
    if (window.CLOUD_MODE) return NOT_ON_CLOUD;
    return jget(url);
  }
  function runtimeOf(sid) {
    try { if (typeof _cmRuntimeOf === 'function') return _cmRuntimeOf({ id: sid }) || 'openclaw'; } catch (e) {}
    var i = String(sid).indexOf(':');
    return i > 0 ? String(sid).slice(0, i) : 'openclaw';
  }
  function runtimeLabel(rt) {
    try { if (typeof _cmRuntimeLabel === 'function') return _cmRuntimeLabel(rt); } catch (e) {}
    return rt;
  }

  // ── Outcome vocabulary (the six labels in clawmetry/outcome_classifier.py)
  // Colour + a plain-English sentence for each. Anything else is "unknown".
  var OUTCOMES = {
    success:         { color: '#22c55e', name: 'Finished',       key: 'success',         fb: 'It finished the task and stopped cleanly.' },
    failed:          { color: '#ef4444', name: 'Failed',         key: 'failed',          fb: 'It hit an error or gave up before finishing.' },
    escalated:       { color: '#f59e0b', name: 'Asked for help', key: 'escalated',       fb: 'It stopped to ask a person before going on.' },
    cognitive_loop:  { color: '#f97316', name: 'Went in circles', key: 'cognitive_loop', fb: 'It kept repeating itself without making progress.' },
    tool_call_stuck: { color: '#f97316', name: 'Got stuck',      key: 'tool_call_stuck', fb: 'A tool it called never came back.' },
    ongoing:         { color: '#3b82f6', name: 'Still running',  key: 'ongoing',         fb: 'It is still working, or ended only moments ago.' }
  };
  function outcomeMeta(label) {
    var k = String(label || '').toLowerCase();
    var o = OUTCOMES[k];
    if (!o) return null;
    return {
      color: o.color,
      name: T('trail.outcome_' + o.key, o.name),
      explain: T('trail.outcome_' + o.key + '_why', o.fb)
    };
  }
  window._cmOutcomeMeta = outcomeMeta;

  // Verdict badge for a session row: outcome colour + quality score when known.
  // Returns '' when nothing is known: an absent badge is the quiet default,
  // never a "no data" badge on every row of a hosted trial.
  window._cmVerdictBadge = function (tx) {
    if (!tx) return '';
    var html = '';
    var m = outcomeMeta(tx.outcome);
    if (m) {
      html += '<span class="cm-verdict" style="--verdict:' + m.color + ';" title="' + esc(m.explain) + '">' +
        '<span class="cm-verdict-dot" aria-hidden="true"></span>' + esc(m.name) + '</span>';
    }
    var score = tx.eval_score;
    if ((score === null || score === undefined) && window._cmEvalScoresByRow) {
      var st = window._cmEvalScoresByRow[tx.id];
      if (st && st.score !== null && st.score !== undefined) score = st.score;
    }
    if (score !== null && score !== undefined && score !== '') {
      var n = Number(score);
      if (isFinite(n)) {
        var c = (typeof _scoreBadgeColor === 'function') ? _scoreBadgeColor(n) : 'var(--text-muted)';
        html += '<span class="cm-verdict cm-verdict-score" style="--verdict:' + c + ';" title="' +
          esc(T('trail.score_tooltip', 'Quality score from the judge, out of 5')) + '">&#9733; ' + n.toFixed(1) + '</span>';
      }
    }
    return html;
  };

  // ── State ─────────────────────────────────────────────────────────────────
  var state = {
    sid: null,
    row: null,          // the /api/transcripts row when we came from the list
    transcript: null,   // /api/transcript/<sid> payload
    loaded: { replay: false, trace: false, turns: false, tree: false },
    view: 'replay',
    seq: 0
  };
  // Re-parenting bookkeeping: element id -> {parent, next}
  var HOSTED = { 'transcript-viewer': 'trail-replay-host', 'trace-detail': 'trail-trace-host', 'ta-detail': 'trail-turns-host' };
  var origin = {};

  function mountHosts() {
    Object.keys(HOSTED).forEach(function (id) {
      var el = $(id), host = $(HOSTED[id]);
      if (!el || !host) return;
      if (el.parentNode === host) return;
      if (!origin[id]) origin[id] = { parent: el.parentNode, next: el.nextSibling };
      host.appendChild(el);
    });
  }
  function restoreHosts() {
    Object.keys(HOSTED).forEach(function (id) {
      var el = $(id), o = origin[id];
      if (!el || !o || !o.parent) return;
      if (el.parentNode === o.parent) return;
      el.style.display = 'none';
      if (o.next && o.next.parentNode === o.parent) o.parent.insertBefore(el, o.next);
      else o.parent.appendChild(el);
    });
  }
  // Called from switchTab() for every tab that is not the trail.
  window._trailRestoreHosts = restoreHosts;

  // ── Public entry points ───────────────────────────────────────────────────
  // openTrail(sessionId[, row]) - from a list row, a deep link, or code.
  window.openTrail = function (sessionId, row) {
    if (!sessionId) return;
    state.sid = String(sessionId);
    state.row = row || null;
    state.transcript = null;
    state.loaded = { replay: false, trace: false, turns: false, tree: false };
    try {
      var rt = runtimeOf(state.sid);
      var frag = state.sid.indexOf(':') === -1 ? (rt + ':' + state.sid) : state.sid;
      // Keep the runtime separator readable: #trail=claude_code:<uuid>.
      var want = '#trail=' + encodeURIComponent(frag).replace(/%3A/gi, ':');
      if (window.location.hash !== want) history.replaceState(null, '', window.location.pathname + window.location.search + want);
    } catch (e) {}
    if (typeof switchTab === 'function') switchTab('trail');
    else loadTrailTab();
  };

  // Parse "#trail=<agent_type>:<session_id>" into the session id the APIs
  // expect. Family runtimes already carry their prefix (claude_code:<uuid>);
  // OpenClaw ids are bare, so "openclaw:<id>" is unwrapped.
  window._trailSessionFromHash = function (hash) {
    var h = String(hash || window.location.hash || '').replace(/^#/, '');
    var m = /(?:^|&)trail=([^&]+)/.exec(h);
    if (!m) return null;
    var v = '';
    try { v = decodeURIComponent(m[1]); } catch (e) { v = m[1]; }
    if (v.indexOf('openclaw:') === 0) v = v.slice('openclaw:'.length);
    return v || null;
  };

  // switchTab('trail') lands here.
  window.loadTrailTab = function () {
    if (!state.sid) {
      var fromHash = window._trailSessionFromHash();
      if (fromHash) state.sid = fromHash;
    }
    var empty = $('trail-empty'), body = $('trail-body');
    if (!state.sid) {
      if (empty) empty.style.display = '';
      if (body) body.style.display = 'none';
      return;
    }
    if (empty) empty.style.display = 'none';
    if (body) body.style.display = '';
    mountHosts();
    render();
  };

  window.trailBackToSessions = function () {
    try { history.replaceState(null, '', window.location.pathname + window.location.search); } catch (e) {}
    if (typeof switchTab === 'function') switchTab('transcripts');
  };

  window.trailReload = function () {
    if (!state.sid) return;
    state.transcript = null;
    state.loaded = { replay: false, trace: false, turns: false, tree: false };
    render();
  };

  window.trailExport = function () {
    if (!state.sid) return;
    window.open('/api/sessions/' + encodeURIComponent(state.sid) + '/export?format=json', '_blank', 'noopener');
  };

  window.trailShowView = function (view) {
    state.view = view;
    document.querySelectorAll('#page-trail .trail-subtab').forEach(function (b) {
      var on = b.getAttribute('data-view') === view;
      b.classList.toggle('active', on);
      b.setAttribute('aria-selected', on ? 'true' : 'false');
    });
    document.querySelectorAll('#page-trail .trail-view').forEach(function (v) {
      v.style.display = v.getAttribute('data-view') === view ? '' : 'none';
    });
    loadView(view);
  };

  // ── Rendering ─────────────────────────────────────────────────────────────
  function render() {
    var sid = state.sid;
    var seq = ++state.seq;
    var rt = runtimeOf(sid);
    var short = sid.length > 14 ? sid.slice(0, 8) + '…' : sid;

    setHtml('trail-title', esc(T('trail.loading_title', 'Opening the trail…')));
    setHtml('trail-subtitle', '<span class="trail-chip">' + esc(runtimeLabel(rt)) + '</span> <span class="trail-mono" title="' + esc(sid) + '">' + esc(short) + '</span>');
    var exportBtn = $('trail-export-btn'), exportNote = $('trail-export-note');
    if (exportBtn) exportBtn.disabled = !!window.CLOUD_MODE;
    if (exportNote) exportNote.style.display = window.CLOUD_MODE ? '' : 'none';

    setHtml('trail-request', muted(T('app.loading', 'Loading...')));
    setHtml('trail-context', muted(T('app.loading', 'Loading...')));
    setHtml('trail-verdict', muted(T('app.loading', 'Loading...')));
    setHtml('trail-quality', muted(T('app.loading', 'Loading...')));
    setHtml('trail-spend', muted(T('app.loading', 'Loading...')));
    setHtml('trail-git', muted(T('app.loading', 'Loading...')));
    var cov = $('trail-coverage'); if (cov) { cov.style.display = 'none'; cov.innerHTML = ''; }

    // Section 2 first: the replay is the heart of the page and its loader is
    // the one users already know. Other views load on their first click.
    trailShowView(state.view || 'replay');

    // Everything else in parallel; each renderer guards on seq so a quick
    // second open cannot paint stale cards.
    loadRow(sid).then(function (row) {
      if (seq !== state.seq) return;
      state.row = row || state.row;
      renderTitle(sid, state.row, state.transcript);
      renderVerdict(state.row);
      renderSpend(state.row, state.transcript);
    });
    loadTranscript(sid).then(function (data) {
      if (seq !== state.seq) return;
      state.transcript = data;
      renderTitle(sid, state.row, data);
      renderRequest(data);
      renderSpend(state.row, data);
    });
    renderContext(sid, rt, seq);
    renderQuality(sid, seq);
    renderGit(sid, seq);
  }

  async function loadRow(sid) {
    if (state.row && state.row.id === sid) return state.row;
    // The list endpoint carries outcome / cost / attention per row. One
    // request, matched by id (exact, then prefix-less suffix for family ids).
    var r = await jget('/api/transcripts');
    var rows = (r.ok && r.data && Array.isArray(r.data.transcripts)) ? r.data.transcripts : [];
    var bare = sid.indexOf(':') >= 0 ? sid.slice(sid.indexOf(':') + 1) : sid;
    for (var i = 0; i < rows.length; i++) {
      var id = String(rows[i].id || '');
      if (id === sid || id === bare || (id.indexOf(':') >= 0 && id.slice(id.indexOf(':') + 1) === bare)) return rows[i];
    }
    return null;
  }

  async function loadTranscript(sid) {
    var r = await jget('/api/transcript/' + encodeURIComponent(sid));
    if (!r.ok || !r.data || r.data.error) return null;
    return r.data;
  }

  function renderTitle(sid, row, data) {
    var title = (row && (row.title || row.name)) || (data && data.name) || '';
    var UUIDISH = /^[0-9a-f]{6,}([-_][0-9a-f]+)*$/i;
    if (!title || title === sid || UUIDISH.test(title) || sid.indexOf(title) === 0) title = T('trail.untitled', 'Untitled session');
    setHtml('trail-title', esc(title));
    var bits = [];
    bits.push('<span class="trail-chip">' + esc(runtimeLabel(runtimeOf(sid))) + '</span>');
    var short = sid.length > 14 ? sid.slice(0, 8) + '…' : sid;
    bits.push('<span class="trail-mono" title="' + esc(sid) + '">' + esc(short) + '</span>');
    var when = row && (row.started || row.modified);
    if (when && typeof timeAgo === 'function') bits.push('<span>' + esc(T('trail.started', 'started')) + ' ' + esc(timeAgo(row.started || row.modified)) + '</span>');
    if (row && row.attention && typeof _cmAttentionBadge === 'function') bits.push(_cmAttentionBadge(row.attention, row.attention_signal, row.attention_tool));
    setHtml('trail-subtitle', bits.join(' <span class="trail-dot">·</span> '));
  }

  function firstUserPrompt(data) {
    var msgs = (data && Array.isArray(data.messages)) ? data.messages : [];
    for (var i = 0; i < msgs.length; i++) {
      var m = msgs[i];
      if (m && String(m.role || '').toLowerCase() === 'user') {
        var c = m.content;
        if (c && typeof c === 'object') c = c.text || JSON.stringify(c);
        c = String(c || '').trim();
        if (c) return c;
      }
    }
    return '';
  }

  function renderRequest(data) {
    if (!data) {
      setHtml('trail-request', muted(T('trail.request_missing', 'No messages were captured for this session, so the request is unknown.')));
      return;
    }
    var p = firstUserPrompt(data);
    if (!p) {
      setHtml('trail-request', muted(T('trail.request_none', 'This session has no user prompt on record. It may have been started by a schedule or another agent.')));
      return;
    }
    var CAP = 1200;
    var long = p.length > CAP;
    var html = '<div class="trail-request-text" id="trail-request-text">' + esc(long ? p.slice(0, CAP) + '…' : p) + '</div>';
    if (long) {
      html += '<button type="button" class="trail-link" onclick="(function(b){var el=document.getElementById(\'trail-request-text\');el.textContent=b.getAttribute(\'data-full\');b.remove();})(this)" data-full="' + esc(p) + '">' + esc(T('trail.show_full', 'Show the full request')) + ' (' + p.length + ' ' + esc(T('trail.chars', 'characters')) + ')</button>';
    }
    setHtml('trail-request', html);
  }

  // What the agent knew: system prompt / tools / MCP / model. Served by
  // /api/sessions/<id>/context once that stream lands; until then, and on
  // the hosted dashboard, it 404s and we say so.
  // On the hosted dashboard the cloud bundle installs
  // window._cmCloudSessionContext(sid) (cm-cloud-session-context), which
  // slices the E2E-encrypted snapshot's sessionContext bucket; the transcript
  // panel's _fetchSessionContext (app.js) already prefers it, so reuse that
  // path here and only fall back to the honest empty state when it is absent.
  async function fetchContext(sid) {
    if (window.CLOUD_MODE) {
      if (typeof window._cmCloudSessionContext !== 'function') return NOT_ON_CLOUD;
      try {
        var c = await window._cmCloudSessionContext(sid);
        if (c && !c.error) return { ok: true, status: 200, data: c };
      } catch (e) { /* fall through to the honest state */ }
      return NOT_ON_CLOUD;
    }
    return jget('/api/sessions/' + encodeURIComponent(sid) + '/context');
  }
  async function renderContext(sid, rt, seq) {
    var r = await fetchContext(sid);
    if (seq !== state.seq) return;
    var d = r.ok ? (r.data || {}) : null;
    var items = [];
    if (d) {
      var arr = Array.isArray(d.items) ? d.items : (Array.isArray(d.context) ? d.context : []);
      arr.forEach(function (it) { if (it && it.kind) items.push(it); });
      ['system_prompt', 'user_prompt', 'tools_available', 'mcp_servers', 'context_file', 'runtime_meta'].forEach(function (k) {
        if (d[k] !== undefined && d[k] !== null && !items.some(function (it) { return it.kind === k; })) items.push({ kind: k, content: d[k] });
      });
    }
    var model = (state.transcript && state.transcript.model) || (d && (d.model || (d.runtime_meta && d.runtime_meta.model))) || '';
    var html = '';
    if (model) html += '<div class="trail-kv"><span class="trail-k">' + esc(T('trail.model', 'Model')) + '</span><span class="badge model">' + esc(model) + '</span></div>';
    var KIND_LABEL = {
      system_prompt: T('trail.kind_system_prompt', 'Instructions it was given'),
      user_prompt: T('trail.kind_user_prompt', 'Opening prompt'),
      tools_available: T('trail.kind_tools', 'Tools it could use'),
      mcp_servers: T('trail.kind_mcp', 'Connected services (MCP)'),
      context_file: T('trail.kind_context_file', 'Project notes it read'),
      runtime_meta: T('trail.kind_runtime_meta', 'Runtime details')
    };
    items.forEach(function (it) {
      if (it.kind === 'user_prompt') return; // already shown as "The request"
      var label = KIND_LABEL[it.kind] || it.kind;
      var content = it.content;
      var body = '';
      if (Array.isArray(content)) {
        body = content.slice(0, 60).map(function (x) {
          var name = (x && typeof x === 'object') ? (x.name || x.id || JSON.stringify(x)) : String(x);
          return '<span class="trail-chip">' + esc(name) + '</span>';
        }).join(' ');
        if (content.length > 60) body += ' <span class="trail-muted">+' + (content.length - 60) + '</span>';
      } else if (content && typeof content === 'object') {
        body = '<pre class="trail-pre">' + esc(JSON.stringify(content, null, 2).slice(0, 4000)) + '</pre>';
      } else {
        var s = String(content == null ? '' : content);
        body = s ? '<pre class="trail-pre">' + esc(s.slice(0, 4000)) + (s.length > 4000 ? '…' : '') + '</pre>' : muted(T('trail.empty_slot', 'Empty'));
      }
      var meta = [];
      if (it.size) meta.push(it.size + ' ' + T('trail.bytes', 'bytes'));
      if (it.redacted) meta.push(T('trail.redacted', 'secrets redacted'));
      html += '<details class="trail-details"' + (it.kind === 'tools_available' || it.kind === 'mcp_servers' ? ' open' : '') + '><summary>' + esc(label) +
        (meta.length ? ' <span class="trail-muted">(' + esc(meta.join(', ')) + ')</span>' : '') + '</summary>' + body + '</details>';
    });
    if (!items.length) {
      var why = (d && d.reason) ? String(d.reason) : '';
      if (r.status === 404 || r.status === 0 || !d) {
        html += muted(T('trail.context_not_captured', 'Not captured yet. ClawMetry does not record the instructions and tool list for this runtime yet, so this card shows only what the transcript reveals.'));
      } else {
        html += muted(why || T('trail.context_empty_runtime', 'This runtime does not expose what the agent knew, so there is nothing to show here.', { runtime: runtimeLabel(rt) }));
      }
    }
    setHtml('trail-context', html);
    renderCoverage(rt, seq);
  }

  async function renderCoverage(rt, seq) {
    var el = $('trail-coverage');
    if (!el) return;
    if (!window._trailCoverageCache) window._trailCoverageCache = jgetLocal('/api/trail/coverage');
    var r = await window._trailCoverageCache;
    if (seq !== state.seq) return;
    if (!r.ok || !r.data) { el.style.display = 'none'; return; }
    var d = r.data;
    var entry = d[rt] || (d.runtimes && d.runtimes[rt]) || (d.coverage && d.coverage[rt]) || (d.adapters && d.adapters[rt]) || null;
    if (!entry || typeof entry !== 'object') { el.style.display = 'none'; return; }
    function grade(v) {
      var k = String(v || 'none').toLowerCase();
      // Levels from routes/trail.py: full | partial | none | unknown. "unknown"
      // means the adapter has not declared anything yet, which is not the
      // same claim as "the runtime does not expose it".
      var word = k === 'full' ? T('trail.cov_full', 'captured')
        : k === 'partial' ? T('trail.cov_partial', 'partly captured')
        : k === 'none' ? T('trail.cov_none', 'not exposed by this runtime')
        : T('trail.cov_unknown', 'not declared yet');
      return '<span class="trail-cov trail-cov-' + esc(k) + '">' + esc(word) + '</span>';
    }
    var html = '<span class="trail-k">' + esc(T('trail.coverage', 'Coverage for')) + ' ' + esc(runtimeLabel(rt)) + ':</span> ' +
      esc(T('trail.cov_inputs', 'inputs')) + ' ' + grade(entry.inputs) + ' <span class="trail-dot">·</span> ' +
      esc(T('trail.cov_reasoning', 'reasoning')) + ' ' + grade(entry.reasoning);
    if (entry.note) html += '<div class="trail-muted" style="margin-top:4px;">' + esc(entry.note) + '</div>';
    el.innerHTML = html;
    el.style.display = '';
  }

  function renderVerdict(row) {
    var label = row && row.outcome;
    var m = outcomeMeta(label);
    if (!m) {
      var html = '<div class="trail-verdict trail-verdict-unknown"><span class="cm-verdict-dot" aria-hidden="true"></span>' + esc(T('trail.outcome_unknown', 'Not classified yet')) + '</div>' +
        muted(T('trail.outcome_unknown_why', 'ClawMetry labels a session once it has ended and the classifier has seen it. On the hosted dashboard the label travels with the next sync.'));
      setHtml('trail-verdict', html + legend());
      return;
    }
    var conf = row.outcome_confidence;
    var confHtml = (conf !== null && conf !== undefined && isFinite(Number(conf)))
      ? '<span class="trail-muted">' + esc(T('trail.confidence', 'confidence')) + ' ' + Math.round(Number(conf) * 100) + '%</span>' : '';
    setHtml('trail-verdict',
      '<div class="trail-verdict" style="--verdict:' + m.color + ';"><span class="cm-verdict-dot" aria-hidden="true"></span>' + esc(m.name) + ' ' + confHtml + '</div>' +
      '<div class="trail-prose">' + esc(m.explain) + '</div>' + legend());
  }

  // Plain-English key to all six labels, collapsed by default.
  function legend() {
    var rows = Object.keys(OUTCOMES).map(function (k) {
      var m = outcomeMeta(k);
      return '<div class="trail-legend-row"><span class="cm-verdict-dot" style="--verdict:' + m.color + ';" aria-hidden="true"></span><strong>' + esc(m.name) + '</strong> <span class="trail-muted">' + esc(m.explain) + '</span></div>';
    }).join('');
    return '<details class="trail-details trail-legend"><summary>' + esc(T('trail.legend', 'What the labels mean')) + '</summary>' + rows + '</details>';
  }

  async function renderQuality(sid, seq) {
    var r = await jget('/api/evals/session/' + encodeURIComponent(sid));
    if (seq !== state.seq) return;
    if (r.status === 402 || r.status === 403) {
      // Existing entitlement copy + upgrade link (app.js).
      var locked = (typeof _evalsLockedHtml === 'function') ? _evalsLockedHtml() : muted(T('evals.locked', 'Session scoring is a Pro feature.'));
      setHtml('trail-quality', '<div class="trail-locked">&#128274; ' + locked + '</div>');
      return;
    }
    var s = (r.ok && r.data && r.data.session) ? r.data.session : (r.ok ? r.data : null);
    var score = s ? (s.eval_score !== undefined ? s.eval_score : s.score) : null;
    if ((score === null || score === undefined) && window._cmEvalScoresByRow && window._cmEvalScoresByRow[sid]) {
      score = window._cmEvalScoresByRow[sid].score;
      s = s || {}; s.eval_reason = s.eval_reason || window._cmEvalScoresByRow[sid].reason;
    }
    if (score === null || score === undefined || !isFinite(Number(score))) {
      setHtml('trail-quality', '<div class="trail-big trail-muted">&ndash;</div>' + muted(T('trail.quality_none', 'Not scored yet. The judge scores a session after it ends, on the machine your agent runs on.')));
      return;
    }
    var n = Number(score);
    var c = (typeof _scoreBadgeColor === 'function') ? _scoreBadgeColor(n) : 'var(--text-primary)';
    var reason = s && (s.eval_reason || s.reason) ? String(s.eval_reason || s.reason) : '';
    var metrics = (r.data && Array.isArray(r.data.metrics)) ? r.data.metrics : [];
    var chips = metrics.slice(0, 8).map(function (m) {
      var ok = m.passed === true || m.verdict === 'pass' || m.value === true;
      var bad = m.passed === false || m.verdict === 'fail' || m.value === false;
      return '<span class="trail-chip ' + (ok ? 'is-ok' : bad ? 'is-bad' : '') + '" title="' + esc(m.reason || '') + '">' + (ok ? '&#10003; ' : bad ? '&#10007; ' : '') + esc(m.label || m.metric_slug || '') + '</span>';
    }).join(' ');
    setHtml('trail-quality',
      '<div class="trail-big" style="color:' + c + ';">' + n.toFixed(1) + '<span class="trail-muted trail-big-denom">/5</span></div>' +
      (reason ? '<div class="trail-prose">' + esc(reason) + '</div>' : '') +
      (chips ? '<div class="trail-chips">' + chips + '</div>' : ''));
  }

  function renderSpend(row, data) {
    var parts = [];
    var cost = row && row.cost_usd;
    if (cost !== null && cost !== undefined && isFinite(Number(cost)) && Number(cost) > 0) {
      parts.push('<div class="trail-kv"><span class="trail-k">' + esc(T('trail.cost', 'Cost')) + '</span><span class="trail-big trail-inline">' + money(cost) + '</span></div>');
    } else if (data && data.totalTokens) {
      parts.push('<div class="trail-kv"><span class="trail-k">' + esc(T('trail.tokens', 'Tokens')) + '</span><span class="trail-big trail-inline">' + (Number(data.totalTokens) / 1000).toFixed(1) + 'k</span></div>' +
        muted(T('trail.cost_unknown', 'Cost not known for this session: no price for its model.')));
    } else if (row || data) {
      parts.push(muted(T('trail.cost_none', 'No cost was recorded for this session.')));
    }
    var dur = '';
    if (data && data.duration) dur = String(data.duration);
    else if (row) {
      var a = toMs(row.started), b = toMs(row.ended_at || row.modified);
      if (a && b && b >= a) dur = fmtDuration(b - a);
    }
    if (dur) parts.push('<div class="trail-kv"><span class="trail-k">' + esc(T('trail.duration', 'Took')) + '</span><span>' + esc(dur) + '</span></div>');
    if (data && data.messageCount) parts.push('<div class="trail-kv"><span class="trail-k">' + esc(T('trail.messages', 'Messages')) + '</span><span>' + esc(String(data.messageCount)) + '</span></div>');
    if (!parts.length) parts.push(muted(T('trail.spend_unknown', 'Spend and duration are not known for this session yet.')));
    setHtml('trail-spend', parts.join(''));
  }

  async function renderGit(sid, seq) {
    var r = await jgetLocal('/api/sessions/' + encodeURIComponent(sid) + '/git-outcomes');
    if (seq !== state.seq) return;
    if (!r.ok || !r.data) {
      setHtml('trail-git', muted(T('trail.git_not_captured', 'Not captured yet. ClawMetry does not link commits and pull requests to this session on this machine.')));
      return;
    }
    var d = r.data;
    if (d.enabled === false) {
      setHtml('trail-git', muted(T('trail.git_off', 'Git outcomes are off on this machine.') + (d.reason ? ' ' + String(d.reason) : '')));
      return;
    }
    var commits = Array.isArray(d.commits) ? d.commits : [];
    var prs = Array.isArray(d.prs) ? d.prs : (Array.isArray(d.pull_requests) ? d.pull_requests : []);
    if (!commits.length && !prs.length) {
      setHtml('trail-git', muted(T('trail.git_none', 'No commits or pull requests were made while this session ran.')));
      return;
    }
    var html = '';
    if (commits.length) {
      html += '<div class="trail-k">' + esc(T('trail.commits', 'Commits')) + ' (' + commits.length + ')</div><ul class="trail-list">' + commits.slice(0, 20).map(function (c) {
        var sha = String(c.sha || c.hash || c.commit || '').slice(0, 7);
        var msg = String(c.message || c.subject || c.title || '').split('\n')[0];
        return '<li><span class="trail-mono">' + esc(sha) + '</span> ' + esc(msg) + (c.branch ? ' <span class="trail-chip">' + esc(c.branch) + '</span>' : '') + '</li>';
      }).join('') + '</ul>';
    }
    if (prs.length) {
      html += '<div class="trail-k">' + esc(T('trail.prs', 'Pull requests')) + ' (' + prs.length + ')</div><ul class="trail-list">' + prs.slice(0, 20).map(function (p) {
        var num = p.number ? '#' + p.number : '';
        var url = String(p.url || p.html_url || '');
        var label = esc(num + ' ' + String(p.title || ''));
        var st = p.state || p.status ? ' <span class="trail-chip">' + esc(p.state || p.status) + '</span>' : '';
        return '<li>' + (/^https?:\/\//.test(url) ? '<a href="' + esc(url) + '" target="_blank" rel="noopener">' + label + '</a>' : label) + st + '</li>';
      }).join('') + '</ul>';
    }
    setHtml('trail-git', html);
  }

  // ── Section 2 views: reuse the existing renderers ─────────────────────────
  function loadView(view) {
    var sid = state.sid;
    if (!sid) return;
    if (state.loaded[view]) return;
    state.loaded[view] = true;
    if (view === 'replay') {
      if (typeof viewTranscript === 'function' && $('transcript-viewer')) {
        try { viewTranscript(sid); } catch (e) { hostError('trail-replay-host', e); }
      } else {
        setHtml('trail-replay-host', muted(T('trail.view_unavailable', 'This view is not available here.')));
      }
    } else if (view === 'trace') {
      if (typeof viewTrace === 'function' && $('trace-detail')) {
        try { viewTrace(sid); } catch (e) { hostError('trail-trace-host', e); }
      } else {
        setHtml('trail-trace-host', muted(T('trail.view_unavailable', 'This view is not available here.')));
      }
    } else if (view === 'turns') {
      if (typeof viewTurnAnatomy === 'function' && $('ta-detail')) {
        try { viewTurnAnatomy(sid); } catch (e) { hostError('trail-turns-host', e); }
      } else {
        setHtml('trail-turns-host', muted(T('trail.view_unavailable', 'This view is not available here.')));
      }
    } else if (view === 'tree') {
      renderTree(sid);
    }
  }
  function hostError(hostId, e) {
    var host = $(hostId);
    if (!host) return;
    var note = document.createElement('div');
    note.className = 'trail-muted';
    note.textContent = T('trail.view_failed', 'This view could not be drawn.') + ' ' + String((e && e.message) || '');
    host.appendChild(note);
  }

  // Replay tree (GET /api/replay-tree/<sid>): turns -> events, delegations,
  // approvals. Small, honest renderer; the flat replay stays the main view.
  async function renderTree(sid) {
    var seq = state.seq;
    setHtml('trail-tree-host', muted(T('app.loading', 'Loading...')));
    var r = await jgetLocal('/api/replay-tree/' + encodeURIComponent(sid));
    if (seq !== state.seq) return;
    if (!r.ok || !r.data) {
      setHtml('trail-tree-host', muted(T('trail.tree_unavailable', 'The replay tree is not available here. The Replay view has the full conversation.')));
      return;
    }
    var d = r.data;
    var turns = Array.isArray(d.turns) ? d.turns : [];
    var workflows = Array.isArray(d.workflows) ? d.workflows : [];
    if (!turns.length && !workflows.length) {
      setHtml('trail-tree-host', muted(T('trail.tree_empty', 'No replay tree yet for this runtime. The Replay view above has the full conversation.')));
      return;
    }
    var KIND_ICON = { 'llm.call': '&#128172;', 'llm.response': '&#129302;', 'tool.call': '&#128295;', 'tool.result': '&#8617;', 'thinking': '&#129504;', 'approval.request': '&#9995;', 'approval.decision': '&#9989;', 'compaction': '&#128230;', 'agent.spawn': '&#129516;', 'agent.return': '&#8617;' };
    function evLine(ev) {
      var kind = String(ev.kind || '');
      var icon = KIND_ICON[kind] || '&#8226;';
      var text = ev.tool_name || ev.tool || ev.summary || ev.text || ev.content || '';
      if (text && typeof text === 'object') text = JSON.stringify(text);
      text = String(text || '').replace(/\s+/g, ' ').slice(0, 160);
      var err = ev.is_error || ev.error ? ' <span class="trail-chip is-bad">' + esc(T('trail.error', 'error')) + '</span>' : '';
      return '<li><span aria-hidden="true">' + icon + '</span> <span class="trail-mono">' + esc(kind) + '</span> ' + esc(text) + err + '</li>';
    }
    function delegations(list, depth) {
      if (!list || !list.length || depth > 4) return '';
      return '<ul class="trail-tree-children">' + list.map(function (dl) {
        var evs = Array.isArray(dl.events) ? dl.events : [];
        return '<li><span aria-hidden="true">&#129516;</span> ' + esc(T('trail.delegation', 'Sub-agent')) + (dl.agent || dl.name ? ': ' + esc(dl.agent || dl.name) : '') +
          ' <span class="trail-muted">(' + evs.length + ' ' + esc(T('trail.events', 'events')) + ')</span>' +
          (evs.length ? '<ul class="trail-tree-events">' + evs.slice(0, 30).map(evLine).join('') + '</ul>' : '') +
          delegations(dl.delegations, depth + 1) + '</li>';
      }).join('') + '</ul>';
    }
    var html = '<div class="trail-kv"><span class="trail-k">' + esc(T('trail.tree_turns', 'Turns')) + '</span><span>' + turns.length + '</span>' +
      (d.mode ? '<span class="trail-k" style="margin-left:14px;">' + esc(T('trail.tree_mode', 'Mode')) + '</span><span class="trail-chip">' + esc(String(d.mode)) + '</span>' : '') + '</div>';
    html += '<ol class="trail-tree">' + turns.map(function (tn, i) {
      var evs = Array.isArray(tn.events) ? tn.events : [];
      var aps = Array.isArray(tn.approvals) ? tn.approvals : [];
      var first = evs.length ? (evs[0].summary || evs[0].text || evs[0].content || '') : '';
      if (first && typeof first === 'object') first = JSON.stringify(first);
      first = String(first || '').replace(/\s+/g, ' ').slice(0, 120);
      return '<li><details class="trail-details"' + (i < 2 ? ' open' : '') + '><summary><strong>' + esc(T('trail.turn', 'Turn')) + ' ' + (i + 1) + '</strong> <span class="trail-muted">' + esc(first) + '</span>' +
        ' <span class="trail-muted">(' + evs.length + ' ' + esc(T('trail.events', 'events')) + (aps.length ? ', ' + aps.length + ' ' + esc(T('trail.approvals', 'approvals')) : '') + ')</span></summary>' +
        (evs.length ? '<ul class="trail-tree-events">' + evs.slice(0, 80).map(evLine).join('') + (evs.length > 80 ? '<li class="trail-muted">+' + (evs.length - 80) + '</li>' : '') + '</ul>' : '') +
        delegations(tn.delegations, 0) + '</details></li>';
    }).join('') + '</ol>';
    if (workflows.length) {
      html += '<div class="trail-k" style="margin-top:10px;">' + esc(T('trail.workflows', 'Workflows')) + ' (' + workflows.length + ')</div><ul class="trail-tree-events">' +
        workflows.slice(0, 20).map(function (w) { var evs = Array.isArray(w.events) ? w.events : []; return '<li><span class="trail-mono">' + esc(w.kind || 'workflow') + '</span> ' + esc(String(w.name || w.span_id || '')) + ' <span class="trail-muted">(' + evs.length + ' ' + esc(T('trail.events', 'events')) + ')</span></li>'; }).join('') + '</ul>';
    }
    setHtml('trail-tree-host', html);
  }
})();
