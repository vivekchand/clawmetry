// Setup map: runtime-aware rules, skills, commands, agents, and hooks.
//
// This view builds on the existing read-only runtime memory catalog. It gives
// users a single place to understand what shapes an agent's behaviour without
// adding a second scanner or writing to agent configuration files.

var _cmSetupState = {
  catalog: null,
  kind: 'all',
  selectedRuntime: null,
  selectedGroups: [],
  cloudGroups: null,
  requestId: 0,
  fileRequestId: 0,
  scope: null,
};

function _cmSetupScope() {
  return typeof _cmRuntimeFilter === 'function' ? (_cmRuntimeFilter() || 'all') : 'all';
}

function _cmSetupRuntimes() {
  var scope = _cmSetupScope();
  return ((_cmSetupState.catalog && _cmSetupState.catalog.runtimes) || []).filter(function(runtime) {
    return scope === 'all' || runtime.id === scope;
  });
}

function _cmSetupCloudCatalog(groups) {
  var runtimes = {};
  groups.forEach(function(group) {
    var id = group.runtime;
    if (!id || !group.exists) return;
    var runtime = runtimes[id] || (runtimes[id] = {
      id: id, label: group.runtime_label || id, present: true, counts: {}, roots: []
    });
    var count = (group.files || []).length;
    runtime.counts[group.category] = (runtime.counts[group.category] || 0) + count;
    runtime.roots.push({exists: true, scope: group.scope, count: count});
  });
  return {runtimes: Object.keys(runtimes).map(function(id) { return runtimes[id]; })};
}

function _cmSetupUnavailable(message, needKey) {
  _cmSetupState.catalog = null;
  _cmSetupState.cloudGroups = null;
  setupCloseFiles();
  var grid = document.getElementById('setup-runtime-grid');
  if (grid) {
    grid.textContent = message;
    if (needKey && typeof window._cmRenderKeyPrompt === 'function') {
      window._cmRenderKeyPrompt(grid, {title: 'Encrypted setup', onUnlock: function() { loadSetup(true); }});
      var note = document.getElementById('cm-mem-err');
      if (note) { note.textContent = message; note.style.display = ''; }
    }
  }
  var empty = document.getElementById('setup-empty');
  if (empty) empty.style.display = 'none';
  ['runtimes', 'files', 'projects', 'global'].forEach(function(name) {
    var count = document.getElementById('setup-summary-' + name);
    if (count) count.textContent = 'Unavailable';
  });
}

function _cmSetupEscape(value) {
  if (typeof escHtml === 'function') return escHtml(value == null ? '' : String(value));
  return String(value == null ? '' : value).replace(/[&<>"']/g, function(c) {
    return {'&':'&amp;', '<':'&lt;', '>':'&gt;', '"':'&quot;', "'":'&#39;'}[c];
  });
}

function _cmSetupFileCount(runtime, kind) {
  var counts = (runtime && runtime.counts) || {};
  if (kind && kind !== 'all') return Number(counts[kind] || 0);
  return Object.keys(counts).reduce(function(total, key) {
    return total + Number(counts[key] || 0);
  }, 0);
}

function _cmSetupKindLabel(kind) {
  return ({memory:'instructions', skills:'skills', commands:'commands', agents:'agents', hooks:'hooks'})[kind] || kind;
}

function _cmSetupFetch(url, options, timeoutMs) {
  options = options || {};
  var controller = typeof AbortController === 'function' ? new AbortController() : null;
  if (controller) options.signal = controller.signal;
  var timer = controller ? setTimeout(function() { controller.abort(); }, timeoutMs || 8000) : null;
  return fetch(url, options).finally(function() {
    if (timer) clearTimeout(timer);
  });
}

function _cmSetupRuntimeCard(runtime) {
  var count = _cmSetupFileCount(runtime, _cmSetupState.kind);
  var selected = _cmSetupState.selectedRuntime === runtime.id;
  var status = _cmSetupState.kind === 'all'
    ? count + ' setup file' + (count === 1 ? '' : 's')
    : count + ' ' + _cmSetupKindLabel(_cmSetupState.kind);
  var counts = runtime.counts || {};
  var chips = ['memory','skills','commands','agents','hooks'].map(function(kind) {
    var n = Number(counts[kind] || 0);
    return n ? '<span class="cm-setup-mini-chip">' + _cmSetupEscape(_cmSetupKindLabel(kind)) + ' ' + n + '</span>' : '';
  }).join('');
  return '<button type="button" class="cm-setup-runtime-card' + (selected ? ' is-selected' : '') + '"'
    + ' onclick="setupSelectRuntime(\'' + _cmSetupEscape(runtime.id) + '\')"'
    + ' title="' + _cmSetupEscape(runtime.label || runtime.id) + '">'
    + '<span class="cm-setup-runtime-mark" aria-hidden="true">●</span>'
    + '<span class="cm-setup-runtime-main"><span class="cm-setup-runtime-name">' + _cmSetupEscape(runtime.label || runtime.id) + '</span>'
    + '<span class="cm-setup-runtime-status">' + _cmSetupEscape(status) + '</span></span>'
    + '<span class="cm-setup-runtime-count">' + count + '</span>'
    + '<span class="cm-setup-runtime-chips">' + chips + '</span>'
    + '</button>';
}

function _cmSetupRenderCatalog() {
  var grid = document.getElementById('setup-runtime-grid');
  var empty = document.getElementById('setup-empty');
  if (!grid) return;
  if (!_cmSetupState.catalog) return;
  var runtimes = _cmSetupRuntimes().filter(function(runtime) {
    return runtime.present && _cmSetupFileCount(runtime, _cmSetupState.kind) > 0;
  });
  runtimes.sort(function(a, b) {
    var ac = _cmSetupFileCount(a, _cmSetupState.kind);
    var bc = _cmSetupFileCount(b, _cmSetupState.kind);
    if (ac !== bc) return bc - ac;
    return String(a.label || a.id).localeCompare(String(b.label || b.id));
  });
  if (!runtimes.length) {
    grid.innerHTML = '';
    if (empty) {
      empty.style.display = '';
      var heading = empty.querySelector('strong');
      var detail = empty.querySelector('span');
      if (heading) heading.textContent = window.CLOUD_MODE ? 'No synced files in this view.' : 'No setup files found in this view.';
      if (detail) detail.textContent = window.CLOUD_MODE && _cmSetupState.kind === 'hooks'
        ? 'Hook settings can contain credentials and stay on the agent machine. Instructions, skills, commands and agents are available in the other categories.'
        : (window.CLOUD_MODE ? 'Try another category or refresh after your node syncs.' : 'Try another category or rescan after using this runtime.');
    }
    return;
  }
  if (empty) empty.style.display = 'none';
  grid.innerHTML = runtimes.map(_cmSetupRuntimeCard).join('');
}

function _cmSetupRenderSummary() {
  var runtimes = _cmSetupRuntimes();
  var found = runtimes.filter(function(r) { return r.present; });
  var files = runtimes.reduce(function(total, r) {
    return total + _cmSetupFileCount(r, 'all');
  }, 0);
  var projects = runtimes.reduce(function(total, r) {
    return total + ((r.roots || []).filter(function(root) {
      return root.exists && root.scope === 'project' && root.count;
    }).length);
  }, 0);
  var global = runtimes.reduce(function(total, r) {
    return total + ((r.roots || []).filter(function(root) {
      return root.exists && root.scope === 'global' && root.count;
    }).length);
  }, 0);
  var set = function(id, value) {
    var el = document.getElementById(id);
    if (el) el.textContent = String(value);
  };
  set('setup-summary-runtimes', found.length);
  set('setup-summary-files', files);
  set('setup-summary-projects', projects);
  set('setup-summary-global', global);
}

async function loadSetup(force) {
  var grid = document.getElementById('setup-runtime-grid');
  if (!grid) return;
  var scope = _cmSetupScope();
  var requestId = ++_cmSetupState.requestId;
  if (scope !== _cmSetupState.scope || force) {
    setupCloseFiles();
    _cmSetupState.scope = scope;
  }
  var source = document.getElementById('setup-source-note');
  if (source) source.textContent = window.CLOUD_MODE
    ? 'Synced setup files for ' + (scope === 'all' ? 'all runtimes' : (typeof _cmRuntimeLabel === 'function' ? _cmRuntimeLabel(scope) : scope)) + '. Contents are decrypted in your browser. Runtime configuration stays on the node.'
    : 'Pick a harness to review the files it exposes.';
  var refresh = document.getElementById('setup-refresh');
  if (refresh) refresh.textContent = window.CLOUD_MODE ? 'Refresh synced setup' : 'Rescan setup';
  if (_cmSetupState.catalog && !force && !window.CLOUD_MODE) {
    _cmSetupRenderSummary();
    _cmSetupRenderCatalog();
    return;
  }
  grid.innerHTML = '<div class="cm-setup-loading">Loading setup files…</div>';
  ['runtimes', 'files', 'projects', 'global'].forEach(function(name) {
    var count = document.getElementById('setup-summary-' + name);
    if (count) count.textContent = 'Loading';
  });
  try {
    var catalog;
    if (window.CLOUD_MODE) {
      if (typeof window._cmCloudRuntimeFiles !== 'function') throw new Error('Reload this page to reconnect to your synced files.');
      var data = await window._cmCloudRuntimeFiles('all', null, {force: !!force});
      if (requestId !== _cmSetupState.requestId || scope !== _cmSetupScope()) return;
      if (data.decrypt_error) { _cmSetupUnavailable('Your saved key could not unlock this node’s setup files. Unlock with the node’s current key, then refresh.', true); return; }
      if (data.needkey) { _cmSetupUnavailable('Unlock your encrypted setup files, then refresh this view.', true); return; }
      if (data.pending) { _cmSetupUnavailable(data.node_online === false ? 'Your node is offline and no setup snapshot is available. Refresh when it reconnects.' : 'Waiting for your node to sync its setup files. Refresh in a moment.'); return; }
      if (!Array.isArray(data.groups)) throw new Error('Setup files could not be loaded. Try refreshing this view.');
      _cmSetupState.cloudGroups = data.groups;
      catalog = _cmSetupCloudCatalog(data.groups);
    } else {
      var response = await _cmSetupFetch('/api/runtimes/memory-catalog', { credentials: 'same-origin' }, 8000);
      if (!response.ok) throw new Error('Setup scan could not be loaded. Try again.');
      catalog = await response.json();
    }
    if (requestId !== _cmSetupState.requestId || scope !== _cmSetupScope()) return;
    _cmSetupState.catalog = catalog;
    _cmSetupRenderSummary();
    _cmSetupRenderCatalog();
  } catch (error) {
    if (requestId !== _cmSetupState.requestId || scope !== _cmSetupScope()) return;
    _cmSetupUnavailable('Setup files could not be loaded. Check the node connection and refresh this view.');
  }
}

function setupSetKind(kind) {
  _cmSetupState.kind = kind || 'all';
  document.querySelectorAll('.cm-setup-filter').forEach(function(button) {
    button.classList.toggle('is-active', button.getAttribute('data-setup-kind') === _cmSetupState.kind);
  });
  _cmSetupRenderCatalog();
  setupCloseFiles();
}

async function setupSelectRuntime(runtimeId) {
  if (_cmSetupScope() !== 'all' && _cmSetupScope() !== runtimeId) return;
  var requestId = ++_cmSetupState.fileRequestId;
  _cmSetupState.selectedRuntime = runtimeId;
  _cmSetupRenderCatalog();
  var runtime = ((_cmSetupState.catalog && _cmSetupState.catalog.runtimes) || []).find(function(item) {
    return item.id === runtimeId;
  });
  var panel = document.getElementById('setup-files-panel');
  var list = document.getElementById('setup-files-list');
  var title = document.getElementById('setup-files-title');
  var note = document.getElementById('setup-files-note');
  if (!panel || !list || !runtime) return;
  panel.style.display = '';
  if (title) title.textContent = (runtime.label || runtime.id) + ' setup';
  if (note) note.textContent = 'Read-only view of the ' + (_cmSetupState.kind === 'all' ? 'known setup files' : _cmSetupKindLabel(_cmSetupState.kind)) + '.';
  list.innerHTML = '<div class="cm-setup-loading">Loading files…</div>';
  var preview = document.getElementById('setup-file-preview');
  if (preview) preview.innerHTML = '<div class="cm-setup-preview-empty">Choose a file to inspect its contents.</div>';
  try {
    var url = '/api/runtimes/' + encodeURIComponent(runtimeId) + '/files';
    if (_cmSetupState.kind !== 'all') url += '?category=' + encodeURIComponent(_cmSetupState.kind);
    var payload;
    if (window.CLOUD_MODE) {
      payload = {groups: (_cmSetupState.cloudGroups || []).filter(function(group) {
        return group.runtime === runtimeId && (_cmSetupState.kind === 'all' || group.category === _cmSetupState.kind);
      })};
    } else {
      var response = await _cmSetupFetch(url, { credentials: 'same-origin' }, 8000);
      if (!response.ok) throw new Error('Files could not be loaded. Try again.');
      payload = await response.json();
    }
    if (requestId !== _cmSetupState.fileRequestId || _cmSetupState.selectedRuntime !== runtimeId) return;
    var groups = (payload.groups || []).filter(function(group) {
      return group.exists && (group.files || []).length;
    });
    _cmSetupState.selectedGroups = groups;
    if (!groups.length) {
      list.innerHTML = '<div class="cm-setup-files-empty">No matching files were found for this harness.</div>';
      return;
    }
    list.innerHTML = groups.map(function(group, groupIndex) {
      var files = (group.files || []).map(function(file, fileIndex) {
        var name = file.path || group.label || '(file)';
        var size = Number(file.size || 0);
        var sizeText = size >= 1024 ? (size / 1024).toFixed(1) + ' KB' : size + ' B';
        return '<button type="button" class="cm-setup-file-row" onclick="setupOpenFile(' + groupIndex + ',' + fileIndex + ')">'
          + '<span><strong>' + _cmSetupEscape(name.split('/').pop() || name) + '</strong><small>' + _cmSetupEscape(group.scope) + ' · ' + _cmSetupEscape(group.category) + '</small></span>'
          + '<em>' + _cmSetupEscape(sizeText) + '</em></button>';
      }).join('');
      return '<div class="cm-setup-file-group"><div class="cm-setup-file-group-title">' + _cmSetupEscape(group.label || group.category) + '</div>'
        + '<div class="cm-setup-file-group-path">' + _cmSetupEscape(group.root) + '</div>' + files + '</div>';
    }).join('');
    panel.scrollIntoView({ behavior: 'smooth', block: 'start' });
  } catch (error) {
    if (requestId !== _cmSetupState.fileRequestId || _cmSetupState.selectedRuntime !== runtimeId) return;
    list.innerHTML = '<div class="cm-setup-error">Could not read setup files. ' + _cmSetupEscape(error && error.message || error) + '</div>';
  }
}

async function setupOpenFile(groupIndex, fileIndex) {
  var group = _cmSetupState.selectedGroups[groupIndex];
  var file = group && (group.files || [])[fileIndex];
  var runtimeId = _cmSetupState.selectedRuntime;
  var preview = document.getElementById('setup-file-preview');
  if (!group || !file || !preview || !runtimeId) return;
  var requestId = ++_cmSetupState.fileRequestId;
  preview.innerHTML = '<div class="cm-setup-loading">Reading ' + _cmSetupEscape(file.path || group.label) + '…</div>';
  try {
    var url = '/api/runtimes/' + encodeURIComponent(runtimeId) + '/file?root=' + encodeURIComponent(group.root) + '&path=' + encodeURIComponent(file.path || '');
    var data;
    if (window.CLOUD_MODE) {
      if (file.content_available === false || typeof file.content !== 'string') {
        preview.textContent = file.omitted_reason === 'snapshot_budget'
          ? 'This file is listed, but its contents were omitted to keep sync within its size limit. Open it on the node to read the full file.'
          : 'This file is listed in the synced inventory, but its contents have not been synced. Refresh after the next node sync.';
        return;
      }
      data = {content: file.content, language: file.language || 'text', truncated: !!file.truncated};
    } else {
      var response = await _cmSetupFetch(url, { credentials: 'same-origin' }, 8000);
      data = await response.json();
      if (!response.ok) throw new Error(data.error || 'File could not be read.');
    }
    if (requestId !== _cmSetupState.fileRequestId || _cmSetupState.selectedRuntime !== runtimeId) return;
    preview.innerHTML = '<div class="cm-setup-preview-head"><strong>' + _cmSetupEscape(file.path || group.label) + '</strong><span>' + _cmSetupEscape(data.language || 'text') + '</span></div>'
      + (data.truncated ? '<p class="cm-setup-section-note">Partial preview. This file exceeds the synced preview limit; open it on the node to read the full file.</p>' : '')
      + '<pre class="cm-setup-preview-code">' + _cmSetupEscape(data.content || '') + '</pre>';
  } catch (error) {
    if (requestId !== _cmSetupState.fileRequestId || _cmSetupState.selectedRuntime !== runtimeId) return;
    preview.innerHTML = '<div class="cm-setup-error">Could not read this file. ' + _cmSetupEscape(error && error.message || error) + '</div>';
  }
}

function setupCloseFiles() {
  ++_cmSetupState.fileRequestId;
  var panel = document.getElementById('setup-files-panel');
  if (panel) panel.style.display = 'none';
  _cmSetupState.selectedRuntime = null;
  _cmSetupState.selectedGroups = [];
  _cmSetupRenderCatalog();
}
