(function () {
"use strict";
/* Read-only guidance candidates. Suggestions and file changes stay behind
 * the explicit review flow and the Pro self-evolve implementation. */
var _cmImproveState = window._cmImproveState || { kind: 'all', data: null, loaded: false };
window._cmImproveState = _cmImproveState;

function _cmImproveFetch(url, options, timeoutMs) {
  options = options || {};
  var controller = typeof AbortController === 'function' ? new AbortController() : null;
  if (controller) options.signal = controller.signal;
  var timer = controller ? setTimeout(function() { controller.abort(); }, timeoutMs || 8000) : null;
  return fetch(url, options).finally(function() {
    if (timer) clearTimeout(timer);
  });
}

  function escapeHtml(value) {
    return String(value == null ? '' : value).replace(/[&<>'"]/g, function(ch) {
      return {'&':'&amp;', '<':'&lt;', '>':'&gt;', "'":'&#39;', '"':'&quot;'}[ch];
    });
  }

  function setText(id, value) {
    var node = document.getElementById(id);
    if (node) node.textContent = value == null ? '--' : String(value);
  }

  function formatWhen(value) {
    if (!value) return 'recently';
    var time = Date.parse(value);
    if (!Number.isFinite(time)) return String(value).slice(0, 16);
    var minutes = Math.max(0, Math.round((Date.now() - time) / 60000));
    if (minutes < 60) return minutes + 'm ago';
    var hours = Math.round(minutes / 60);
    if (hours < 48) return hours + 'h ago';
    return Math.round(hours / 24) + 'd ago';
  }

  function kindLabel(kind) {
    return ({preference: 'Preference', correction: 'Correction', frustration: 'Friction'})[kind] || 'Signal';
  }

  function renderSummary(data) {
    var signals = data.signals || [];
    var conversations = {};
    var projects = {};
    signals.forEach(function(signal) {
      (signal.evidence || []).forEach(function(evidence) {
        if (evidence.ts) conversations[evidence.ts + '|' + (evidence.workspace || '')] = true;
        if (evidence.workspace) projects[evidence.workspace] = true;
      });
      (signal.projects || []).forEach(function(project) { projects[project] = true; });
    });
    setText('improve-summary-candidates', data.candidate_count || 0);
    var candidateNote = document.getElementById('improve-summary-candidates-note');
    if (candidateNote) {
      var totalCandidates = data.total_candidate_count || data.candidate_count || 0;
      candidateNote.textContent = totalCandidates > (data.candidate_count || 0)
        ? 'shown of ' + totalCandidates
        : 'signals to review';
    }
    setText('improve-summary-conversations', data.conversation_count || Object.keys(conversations).length || 0);
    setText('improve-summary-projects', data.project_count || Object.keys(projects).length || 0);
    setText('improve-summary-window', (data.window_days || 30) + 'd');
    var source = document.getElementById('improve-source-note');
    if (source) source.textContent = (data.message_count || 0) + ' user turns scanned from the local store.';
    var note = document.getElementById('improve-capability-note');
    if (note && data.capabilities && data.capabilities.note) {
      note.querySelector('span:last-child').textContent = data.capabilities.note;
    }
  }

  function renderSignal(signal) {
    var evidence = (signal.evidence || []).map(function(item) {
      return '<div class="cm-improve-evidence"><span>' + escapeHtml(item.excerpt || '') + '</span><small>'
        + escapeHtml(item.workspace || 'local workspace') + ' · ' + escapeHtml(formatWhen(item.ts)) + '</small></div>';
    }).join('');
    var projects = (signal.projects || []).join(', ');
    var runtimes = (signal.runtimes || []).join(', ');
    var pain = Number(signal.pain_score || 0);
    var scope = signal.scope || (signal.project_count === 1 ? 'project' : 'workspace');
    var details = [signal.seen_count + ' observed turn' + (signal.seen_count === 1 ? '' : 's')];
    if (signal.conversation_count) details.push(signal.conversation_count + ' conversation' + (signal.conversation_count === 1 ? '' : 's'));
    if (signal.project_count) details.push(signal.project_count + ' project' + (signal.project_count === 1 ? '' : 's'));
    return '<article class="cm-improve-card" data-improve-card-kind="' + escapeHtml(signal.kind) + '">'
      + '<div class="cm-improve-card-head"><span class="cm-improve-card-mark cm-improve-card-mark-' + escapeHtml(signal.kind) + '" aria-hidden="true">●</span>'
      + '<div class="cm-improve-card-heading"><strong>' + escapeHtml(kindLabel(signal.kind)) + '</strong><span>' + escapeHtml(formatWhen(signal.last_seen)) + '</span></div>'
      + '<span class="cm-improve-confidence">' + escapeHtml(signal.confidence || 'medium') + '</span></div>'
      + '<p class="cm-improve-excerpt">' + escapeHtml(signal.excerpt || '') + '</p>'
      + '<div class="cm-improve-card-meta"><span>' + escapeHtml(details.join(' · ')) + '</span><span class="cm-improve-card-actions"><span class="cm-improve-card-profile">' + escapeHtml(scope) + (pain ? ' · pain ' + pain + '/5' : '') + '</span><button type="button" onclick="improveToggleEvidence(\'' + escapeHtml(signal.id) + '\')">View evidence</button><button type="button" onclick="improveOpenReview(\'' + escapeHtml(signal.id) + '\')">Review candidate</button></span></div>'
      + '<div class="cm-improve-evidence-list" id="improve-evidence-' + escapeHtml(signal.id) + '" hidden>' + evidence
      + (projects ? '<small class="cm-improve-scope">Projects: ' + escapeHtml(projects) + '</small>' : '')
      + (runtimes ? '<small class="cm-improve-scope">Runtimes: ' + escapeHtml(runtimes) + '</small>' : '')
      + '</div></article>';
  }

  function findSignal(id) {
    var data = _cmImproveState.data || {};
    return (data.signals || []).find(function(signal) { return signal.id === id; }) || null;
  }

  function reviewDestination(kind) {
    return ({
      preference: 'Instruction or skill',
      correction: 'Instruction, skill, or agent',
      frustration: 'Evidence first, then the matching setup asset'
    })[kind] || 'Setup asset';
  }

  function reviewEvidenceHtml(signal) {
    return (signal.evidence || []).map(function(item) {
      return '<div class="cm-improve-review-evidence-item"><span>' + escapeHtml(item.excerpt || '') + '</span><small>'
        + escapeHtml(item.workspace || 'local workspace') + ' · ' + escapeHtml(formatWhen(item.ts)) + '</small></div>';
    }).join('') || '<div class="cm-improve-review-empty">No evidence excerpt is available.</div>';
  }

  function reviewProfileHtml(signal) {
    var scope = signal.scope || (signal.project_count === 1 ? 'project' : 'workspace');
    var harnesses = signal.harness_applicability || signal.runtimes || [];
    var confidence = signal.confidence_score == null ? signal.confidence : Math.round(Number(signal.confidence_score) * 100) + '%';
    var pain = signal.pain_score == null ? '—' : String(signal.pain_score) + '/5';
    var key = signal.normalized_key || 'candidate signal';
    return '<div class="cm-improve-profile-grid">'
      + '<span><small>Scope</small><strong>' + escapeHtml(scope) + '</strong></span>'
      + '<span><small>Pain</small><strong>' + escapeHtml(pain) + '</strong></span>'
      + '<span><small>Confidence</small><strong>' + escapeHtml(confidence) + '</strong></span>'
      + '</div><code>' + escapeHtml(key) + '</code>'
      + (harnesses.length ? '<small class="cm-improve-profile-harnesses">Harnesses: ' + escapeHtml(harnesses.join(', ')) + '</small>' : '');
  }

  function renderList() {
    var list = document.getElementById('improve-list');
    var empty = document.getElementById('improve-empty');
    if (!list) return;
    var data = _cmImproveState.data || {};
    var kind = _cmImproveState.kind || 'all';
    var signals = (data.signals || []).filter(function(signal) { return kind === 'all' || signal.kind === kind; });
    if (!signals.length) {
      list.innerHTML = '';
      if (empty) empty.style.display = 'flex';
      return;
    }
    if (empty) empty.style.display = 'none';
    list.innerHTML = signals.map(renderSignal).join('');
  }

  function improveSetKind(kind) {
    _cmImproveState.kind = kind;
    document.querySelectorAll('.cm-improve-filter').forEach(function(button) {
      button.classList.toggle('is-active', button.getAttribute('data-improve-kind') === kind);
    });
    renderList();
  }

  function improveToggleEvidence(id) {
    var node = document.getElementById('improve-evidence-' + id);
    if (node) node.hidden = !node.hidden;
  }

  function improveOpenReview(id) {
    var signal = findSignal(id);
    var modal = document.getElementById('improve-review-modal');
    if (!signal || !modal) return;
    var title = document.getElementById('improve-review-title');
    var summary = document.getElementById('improve-review-summary');
    var evidence = document.getElementById('improve-review-evidence');
    var profile = document.getElementById('improve-review-profile');
    var destination = document.getElementById('improve-review-destination');
    if (title) title.textContent = kindLabel(signal.kind) + ' worth reviewing';
    if (summary) summary.textContent = signal.excerpt || 'A repeated guidance signal was detected in local conversation history.';
    if (evidence) evidence.innerHTML = reviewEvidenceHtml(signal);
    if (profile) profile.innerHTML = reviewProfileHtml(signal);
    if (destination) destination.textContent = reviewDestination(signal.kind);
    modal.hidden = false;
    modal.setAttribute('aria-hidden', 'false');
  }

  function improveCloseReview() {
    var modal = document.getElementById('improve-review-modal');
    if (!modal) return;
    modal.hidden = true;
    modal.setAttribute('aria-hidden', 'true');
  }

  function improveOpenSetup() {
    improveCloseReview();
    if (typeof switchTab === 'function') switchTab('setup');
  }

  async function loadImprove() {
    var list = document.getElementById('improve-list');
    if (!list) return;
    if (window.CLOUD_MODE) {
      list.textContent = 'Guidance candidates use conversations saved on your agent’s computer. Open the local ClawMetry dashboard to review their evidence.';
      ['candidates', 'conversations', 'projects', 'window'].forEach(function (name) {
        var count = document.getElementById('improve-summary-' + name);
        if (count) count.textContent = 'Local only';
      });
      var source = document.getElementById('improve-source-note');
      if (source) source.textContent = 'Review available on your agent’s computer.';
      return;
    }
    if (_cmImproveState.loaded && _cmImproveState.data) {
      renderSummary(_cmImproveState.data);
      renderList();
      return;
    }
    list.innerHTML = '<div class="cm-improve-loading">Reading recent conversations…</div>';
    try {
      var response = await _cmImproveFetch('/api/improve/candidates?window=30', {cache: 'no-store'}, 8000);
      if (!response.ok) throw new Error('HTTP ' + response.status);
      var data = await response.json();
      _cmImproveState.data = data;
      _cmImproveState.loaded = true;
      renderSummary(data);
      renderList();
    } catch (error) {
      list.innerHTML = '<div class="cm-improve-error">Improve scan unavailable. ' + escapeHtml(error && error.message || error) + '</div>';
    }
  }

window.improveSetKind = improveSetKind;
window.improveToggleEvidence = improveToggleEvidence;
window.improveOpenReview = improveOpenReview;
window.improveCloseReview = improveCloseReview;
window.improveOpenSetup = improveOpenSetup;
window.loadImprove = loadImprove;
}());
