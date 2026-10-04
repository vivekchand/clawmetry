(function () {
"use strict";
/* Read-only guidance candidates. Suggestions and file changes stay behind
 * the explicit review flow and the Pro self-evolve implementation. */
var _cmImproveState = window._cmImproveState || { kind: 'all', data: null, loaded: false };
var _improveRequest = 0, _improvePending = null, _improveController = null;
var _improveCacheScope = null;
window._cmImproveState = _cmImproveState;

function currentScope() {
  var runtime = typeof window._cmRuntimeFilter === 'function' ? window._cmRuntimeFilter() : 'all';
  var secret = null;
  if (window.CLOUD_MODE) {
    try { secret = localStorage.getItem('cm-enc-key-' + (window.CLOUD_NODE_ID || '') + '-' +
      (window.CLOUD_TOKEN || '').slice(0,16)); } catch (e) {}
  }
  return {runtime: runtime || 'all', node: window.CLOUD_NODE_ID || '',
    secret: secret, key: JSON.stringify([window.CLOUD_MODE ? 'cloud' : 'local', window.CLOUD_TOKEN || '',
      window.CLOUD_NODE_ID || '', runtime || 'all'])};
}

function sameScope(left, right) {
  return !!left && left.key === right.key && left.secret === right.secret;
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
    if (source) {
      var cov = data.coverage || {};
      var scope = currentScope();
      var label = scope.runtime === 'all' ? 'All runtimes' :
        (typeof window._cmRuntimeLabel === 'function' ? window._cmRuntimeLabel(scope.runtime) : scope.runtime);
      var sampled = cov.status === 'partial' || cov.truncated || cov.sampled;
      var description = (data.message_count || 0) + ' user turns reviewed. ' + label + '.';
      if (sampled) description += ' Partial coverage: a bounded sample of recent conversations.';
      if (cov.inspected_events != null && cov.candidate_events != null) {
        description += ' ' + cov.inspected_events + ' of ' + cov.candidate_events + ' message records inspected.';
      }
      if (cov.omitted_payloads) description += ' ' + cov.omitted_payloads + ' records could not be read within the size limit.';
      if (cov.candidates_truncated) description += ' Showing a limited set of candidates.';
      var generated = Date.parse(data.generated_at || '');
      if (Number.isFinite(generated)) {
        description += (data.stale || Date.now() - generated > 600000 ? ' Saved results from ' : ' Updated ') +
          new Date(generated).toLocaleString() + '.';
      } else if (data.stale) description += ' Saved results may be out of date.';
      if (data.stale) description += ' Refresh when the computer is connected.';
      source.textContent = description;
      addRefresh(source);
    }
    var note = document.getElementById('improve-capability-note');
    if (note && data.capabilities && data.capabilities.note) {
      var noteText = note.querySelector('span:last-child');
      if (noteText) noteText.textContent = data.capabilities.note;
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
    if (!sameScope(_improveCacheScope, currentScope())) return null;
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
    if (_cmImproveState.data && !sameScope(_improveCacheScope, currentScope())) {
      loadImprove(true); return;
    }
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

  function addRefresh(node) {
    if (!node || !document.createElement) return;
    var button = document.createElement('button');
    button.type = 'button';
    button.textContent = 'Refresh';
    button.className = 'cm-improve-refresh';
    button.addEventListener('click', function() { loadImprove(true); });
    node.appendChild(document.createTextNode(' '));
    node.appendChild(button);
  }

  function renderUnavailable(data) {
    var reasons = {
      missing_key: 'Unlock this computer with its encryption key to review guidance.',
      key_required: 'Unlock this computer with its encryption key to review guidance.',
      key_missing: 'Unlock this computer with its encryption key to review guidance.',
      decrypt_failed: 'The saved guidance could not be unlocked. Check the encryption key and try again.',
      decryption_failed: 'The saved guidance could not be unlocked. Check the encryption key and try again.',
      pending: 'Waiting for guidance from your connected computer.',
      cache_pending: 'Waiting for guidance from your connected computer.',
      snapshot_pending: 'Waiting for guidance from your connected computer.',
      missing_snapshot: 'No saved guidance snapshot is available for this computer. Refresh after it syncs.',
      old_collector: 'This saved snapshot does not include guidance. Update ClawMetry on this computer, then refresh.',
      offline: 'This computer is offline. Reconnect it, then refresh to review guidance.',
      node_offline: 'This computer is offline. Reconnect it, then refresh to review guidance.',
      missing_slice: 'Guidance has not synced for this selection. Update ClawMetry on this computer, then refresh.',
      slice_missing: 'Guidance has not synced for this selection. Update ClawMetry on this computer, then refresh.',
      locked: 'This runtime is not available with the computer’s current access.',
      invalid_scope: 'Guidance is not available for this selection.',
      unsupported_window: 'The hosted view shows the last 30 days. Refresh to use that window.',
      context_changed: 'The selected computer or key changed. Refresh to review its guidance.',
      timeout: 'Guidance took too long to load. Refresh to try again.',
      unauthorized: 'Your sign-in could not be verified. Sign in again, then refresh.'
    };
    var message = reasons[data.reason] || reasons[data.state] ||
      'Guidance is unavailable for this computer. Refresh to try again.';
    var list = document.getElementById('improve-list');
    if (list) {
      list.textContent = message;
      var reason = data.reason || data.state;
      var needsKey = ['missing_key','key_required','key_missing','decrypt_failed','decryption_failed'].indexOf(reason) !== -1;
      if (window.CLOUD_MODE && needsKey && typeof window._cmRenderKeyPrompt === 'function') {
        var promptScope = currentScope();
        window._cmRenderKeyPrompt(list, {title: 'Unlock guidance', onUnlock: function() {
          // Unlock intentionally changes the key, but must not refresh a
          // different account, computer or runtime from an obsolete prompt.
          if (promptScope.key === currentScope().key) return loadImprove(true);
        }});
      } else addRefresh(list);
    }
    ['candidates', 'conversations', 'projects', 'window'].forEach(function(name) {
      setText('improve-summary-' + name, 'Unavailable');
    });
    setText('improve-source-note', message);
    setText('improve-summary-candidates-note', '');
    var empty = document.getElementById('improve-empty');
    if (empty) empty.style.display = 'none';
  }

  function loadImprove(force) {
    var list = document.getElementById('improve-list');
    if (!list) return Promise.resolve();
    var scope = currentScope();
    if (_improvePending && sameScope(_improvePending.scope, scope) && !force) return _improvePending.promise;
    if (!force && sameScope(_improveCacheScope, scope) && _cmImproveState.data &&
        Date.now() - (_cmImproveState.at || 0) < 15000) {
      renderSummary(_cmImproveState.data); renderList(); return Promise.resolve();
    }
    if (_improveController) _improveController.abort();
    var controller = typeof AbortController === 'function' ? new AbortController() : null;
    _improveController = controller;
    var identity = ++_improveRequest;
    var stillCurrent = function() { return identity === _improveRequest && sameScope(scope, currentScope()); };
    _cmImproveState.data = null;
    _improveCacheScope = null;
    _cmImproveState.loaded = false;
    improveCloseReview();
    ['candidates', 'conversations', 'projects', 'window'].forEach(function(name) {
      setText('improve-summary-' + name, '…');
    });
    setText('improve-source-note', 'Reading recent conversations…');
    var empty = document.getElementById('improve-empty');
    if (empty) empty.style.display = 'none';
    list.textContent = 'Reading recent conversations…';
    var url = '/api/improve/candidates?window=30&runtime=' + encodeURIComponent(scope.runtime);
    // Cloud transport belongs to the hosted interceptor. Never fall through to
    // a cloud-container filesystem/store when an older server lacks that hook.
    var work = (async function() {
      if (window.CLOUD_MODE && !document.getElementById('cm-cloud-improve')) {
        if (stillCurrent()) renderUnavailable({reason: 'missing_slice'});
        return;
      }
      var timer;
      try {
        var timeout = new Promise(function(_, reject) {
          timer = setTimeout(function() {
            if (controller) controller.abort();
            reject(new Error('timeout'));
          }, 8000);
        });
        var request = (async function() {
          var response = await fetch(url, {cache: 'no-store', signal: controller ? controller.signal : undefined});
          var data = await response.json();
          return {response: response, data: data};
        })();
        var result = await Promise.race([request, timeout]);
        if (!stillCurrent()) {
          if (identity === _improveRequest) renderUnavailable({reason:
            window.CLOUD_MODE && !currentScope().secret ? 'missing_key' : 'context_changed'});
          return;
        }
        var data = result.data || {};
        if (!result.response.ok || data.available === false || data.store_available === false ||
            !Array.isArray(data.signals)) {
          renderUnavailable(data); return;
        }
        var responseScope = data.scope || {};
        if ((scope.runtime !== 'all' && responseScope.runtime !== scope.runtime) ||
            (responseScope.runtime && responseScope.runtime !== scope.runtime)) {
          renderUnavailable({reason:'invalid_scope'}); return;
        }
        if (scope.node && responseScope.node_id && responseScope.node_id !== scope.node) {
          renderUnavailable({reason:'invalid_scope'}); return;
        }
        _cmImproveState.data = data;
        _cmImproveState.loaded = true;
        _cmImproveState.key = scope.key;
        _improveCacheScope = scope;
        _cmImproveState.at = Date.now();
        renderSummary(data); renderList();
      } catch (error) {
        if (stillCurrent()) renderUnavailable({reason: error.message === 'timeout' ? 'timeout' : 'unavailable'});
      } finally {
        if (timer) clearTimeout(timer);
      }
    })();
    _improvePending = {scope: scope, promise: work};
    work.finally(function() {
      if (identity === _improveRequest) { _improvePending = null; _improveController = null; }
    });
    return work;
  }

window.improveSetKind = improveSetKind;
window.improveToggleEvidence = improveToggleEvidence;
window.improveOpenReview = improveOpenReview;
window.improveCloseReview = improveCloseReview;
window.improveOpenSetup = improveOpenSetup;
window.loadImprove = loadImprove;
}());
