// Persistent Home dashboard panels.
// A panel is a saved Dives question + validated SELECT + chart specification.
// The data is always re-read from DuckDB when the Home tab opens.
(function () {
  'use strict';

  var _charts = {};
  var _loadGeneration = 0;
  var _activeControllers = [];
  var LOAD_TIMEOUT_MS = 15000;

  function removeController(controller) {
    var index = _activeControllers.indexOf(controller);
    if (index >= 0) _activeControllers.splice(index, 1);
  }

  function stopActiveLoads() {
    _loadGeneration += 1;
    _activeControllers.slice().forEach(function (controller) {
      try { controller.abort(); } catch (e) {}
    });
    _activeControllers = [];
  }

  function isCurrentLoad(generation) {
    return generation === _loadGeneration;
  }

  function loadError(error, subject) {
    if (error && error.code === 'timeout') return subject + ' timed out. Try again.';
    if (error && error.status) return subject + ' failed to load (HTTP ' + error.status + ').';
    return subject + ' could not be loaded. Try again.';
  }

  function requestJson(url, options, timeoutMs) {
    options = options || {};
    var controller = typeof AbortController !== 'undefined' ? new AbortController() : null;
    var requestOptions = {};
    Object.keys(options).forEach(function (key) { requestOptions[key] = options[key]; });
    if (controller) {
      requestOptions.signal = controller.signal;
      _activeControllers.push(controller);
    }
    var timer;
    var timeout = timeoutMs || LOAD_TIMEOUT_MS;
    var timeoutPromise = new Promise(function (_, reject) {
      timer = setTimeout(function () {
        if (controller) controller.abort();
        var error = new Error('dashboard request timed out');
        error.code = 'timeout';
        reject(error);
      }, timeout);
    });
    var fetchPromise = Promise.resolve().then(function () { return fetch(url, requestOptions); }).then(function (response) {
      return response.text().then(function (body) {
        var data = {};
        try { data = body ? JSON.parse(body) : {}; } catch (e) { data = {}; }
        if (!response.ok) {
          var error = new Error('dashboard request failed');
          error.status = response.status;
          error.data = data;
          throw error;
        }
        return data;
      });
    });
    return Promise.race([fetchPromise, timeoutPromise]).then(function (data) {
      clearTimeout(timer);
      if (controller) removeController(controller);
      return data;
    }, function (error) {
      clearTimeout(timer);
      if (controller) removeController(controller);
      throw error;
    });
  }

  function esc(value) {
    return String(value == null ? '' : value)
      .replace(/&/g, '&amp;').replace(/</g, '&lt;')
      .replace(/>/g, '&gt;').replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;');
  }

  function fmt(value) {
    if (value == null) return 'Not measured';
    if (value === '') return '';
    if (typeof value === 'number') return Number.isFinite(value) ? value.toLocaleString(undefined, { maximumFractionDigits: 4 }) : 'Not measured';
    if (typeof value === 'string' && /^-?\d+(?:\.\d+)?$/.test(value.trim())) {
      var numeric = Number(value);
      if (Number.isFinite(numeric)) return numeric.toLocaleString(undefined, { maximumFractionDigits: 4 });
    }
    return String(value);
  }

  function displayCategory(value) {
    var raw = String(value == null ? '' : value);
    if (typeof window._cmRuntimeLabel === 'function') {
      try {
        var known = window._cmRuntimeLabel(raw);
        if (known && String(known) !== raw) return String(known);
      } catch (e) {}
    }
    if (window._CM_RT_LABEL && typeof window._CM_RT_LABEL === 'object' && window._CM_RT_LABEL[raw]) {
      return String(window._CM_RT_LABEL[raw]);
    }
    return raw.split(/[_-]+/).filter(Boolean).map(function (part) {
      return part.charAt(0).toUpperCase() + part.slice(1);
    }).join(' ') || raw;
  }

  function panelTarget(id) {
    return String(id || '').replace(/[^a-zA-Z0-9_-]/g, '_');
  }

  function destroyCharts() {
    Object.keys(_charts).forEach(function (key) {
      try { _charts[key].destroy(); } catch (e) {}
    });
    _charts = {};
  }

  function renderTable(container, rows) {
    if (!rows.length) {
      container.innerHTML = '<div class="cm-dashboard-empty">No matching data in the selected window.</div>';
      return;
    }
    var normalized = rows.map(function (row) {
      return row && typeof row === 'object' && !Array.isArray(row) ? row : { value: row };
    });
    var cols = [];
    normalized.forEach(function (row) {
      Object.keys(row).forEach(function (col) {
        if (cols.indexOf(col) < 0 && cols.length < 16) cols.push(col);
      });
    });
    var runtimeIndex = cols.findIndex(function (col) { return col.toLowerCase() === 'runtime'; });
    if (runtimeIndex > 0) cols.unshift(cols.splice(runtimeIndex, 1)[0]);
    var html = '<div class="cm-dashboard-table-wrap"><table class="usage-table cm-dashboard-table"><thead><tr>';
    cols.forEach(function (col) { html += '<th>' + esc(displayCategory(col)) + '</th>'; });
    html += '</tr></thead><tbody>';
    normalized.slice(0, 100).forEach(function (row) {
      html += '<tr>';
      cols.forEach(function (col) { html += '<td>' + esc(col.toLowerCase() === 'runtime' && row[col] != null ? displayCategory(row[col]) : fmt(row[col])) + '</td>'; });
      html += '</tr>';
    });
    html += '</tbody></table></div>';
    container.innerHTML = html;
  }

  function renderChart(container, panel, rows) {
    var spec = panel.chart_spec || {};
    var type = String(spec.chart_type || 'table').toLowerCase();
    if (type === 'number') {
      var numberRow = rows[0] && typeof rows[0] === 'object' && !Array.isArray(rows[0]) ? rows[0] : { value: rows[0] };
      var numberKey = spec.y || Object.keys(numberRow)[0] || 'value';
      var rawValue = numberRow[numberKey];
      var numericValue = rawValue == null || rawValue === '' ? null : Number(rawValue);
      var displayValue = Number.isFinite(numericValue) ? fmt(numericValue) : 'Not measured';
      container.innerHTML = '<div class="cm-dashboard-number">' + esc(displayValue) + '</div>';
      return;
    }
    if (type === 'table' || !rows.length || typeof window.Chart === 'undefined') {
      renderTable(container, rows);
      return;
    }
    var xKey = spec.x;
    var yKey = spec.y;
    if (!xKey || !yKey || rows.some(function (row) {
      return !row || typeof row !== 'object' || Array.isArray(row) || !(xKey in row) || !(yKey in row);
    })) {
      renderTable(container, rows);
      return;
    }
    var values = rows.map(function (row) {
      if (row[yKey] == null || row[yKey] === '') return null;
      var value = Number(row[yKey]);
      return Number.isFinite(value) ? value : undefined;
    });
    if (values.some(function (value) { return value === undefined; }) || values.every(function (value) { return value === null; }) || (type === 'pie' && values.some(function (value) { return value === null; }))) {
      renderTable(container, rows);
      container.insertAdjacentHTML('beforeend', '<div class="cm-dashboard-panel-error">Some chart values are missing or not numeric. Missing values are shown as Not measured.</div>');
      return;
    }
    var canvasId = 'cm-dashboard-canvas-' + panelTarget(panel.panel_id);
    var labels = rows.map(function (row) { return displayCategory(row[xKey]); });
    var horizontal = type === 'bar' && (labels.length > 10 || labels.some(function (label) { return label.length > 16; }));
    var showAllLabels = labels.length <= 20;
    container.innerHTML = '<div class="cm-dashboard-chart-wrap"><canvas id="' + canvasId + '"></canvas></div>';
    var chartWrap = container.firstElementChild;
    if (chartWrap && horizontal) chartWrap.style.height = Math.max(220, labels.length * 26) + 'px';
    var canvas = document.getElementById(canvasId);
    if (!canvas) return;
    var chartType = type === 'area' ? 'line' : type;
    var area = type === 'area';
    try {
      _charts[panel.panel_id] = new Chart(canvas, {
        type: chartType,
        data: {
          labels: labels,
          datasets: [{
            label: yKey,
            data: values,
            backgroundColor: chartType === 'pie' ? rows.map(function (_, i) { return 'hsl(' + ((i * 47) % 360) + ',55%,55%)'; }) : area ? 'rgba(59,130,246,.18)' : 'rgba(59,130,246,.72)',
            borderColor: '#3b82f6',
            borderWidth: 2,
            fill: area,
            tension: .25,
          }],
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: { legend: { display: chartType === 'pie' } },
          indexAxis: horizontal ? 'y' : 'x',
          scales: chartType === 'pie' ? {} : {
            x: { ticks: { color: '#9ca3af', autoSkip: horizontal ? false : !showAllLabels, maxTicksLimit: showAllLabels ? labels.length : 12, maxRotation: horizontal ? 0 : 45, minRotation: horizontal ? 0 : (labels.length > 10 ? 45 : 0) }, grid: { color: 'rgba(255,255,255,.06)' } },
            y: { ticks: { color: '#9ca3af', autoSkip: horizontal ? false : !showAllLabels, maxTicksLimit: showAllLabels ? labels.length : 12 }, grid: { color: 'rgba(255,255,255,.06)' } },
          },
        },
      });
    } catch (e) {
      renderTable(container, rows);
    }
  }

  function renderPanel(panel) {
    var id = panelTarget(panel.panel_id);
    var card = document.createElement('article');
    card.className = 'cm-dashboard-panel card';
    card.dataset.panelId = panel.panel_id || '';
    card.innerHTML = ''
      + '<div class="cm-dashboard-panel-head">'
      + '  <div style="min-width:0;">'
      + '    <h3>' + esc(panel.name || 'Saved panel') + '</h3>'
      + '    <div class="cm-dashboard-panel-question" title="' + esc(panel.question || '') + '">' + esc(panel.question || '') + '</div>'
      + '  </div>'
      + '  <button type="button" class="btn btn-xs cm-dashboard-delete" data-panel-id="' + esc(panel.panel_id) + '" title="Remove this panel">Remove</button>'
      + '</div>'
      + '<div class="cm-dashboard-panel-body" id="cm-dashboard-body-' + id + '"><div class="cm-dashboard-loading">Loading panel…</div></div>';
    card.querySelector('.cm-dashboard-delete').addEventListener('click', function () {
      deletePanel(panel.panel_id, card);
    });
    return card;
  }

  function renderPanelBody(body, panel) {
    if (panel.detail_error) {
      body.innerHTML = '<div class="cm-dashboard-panel-error">' + esc(panel.detail_error) + '</div>';
      return;
    }
    if (panel.run_error) {
      body.innerHTML = '<div class="cm-dashboard-panel-error">' + esc(panel.run_error) + '</div>';
      return;
    }
    renderChart(body, panel, Array.isArray(panel.rows) ? panel.rows : []);
    if (panel.truncated) {
      var notice = document.createElement('div');
      notice.className = 'cm-dashboard-panel-description';
      notice.textContent = 'Showing a limited result. Narrow the question to see more detail.';
      body.appendChild(notice);
    }
  }

  async function loadCustomDashboardPanels() {
    var section = document.getElementById('custom-dashboard-section');
    var grid = document.getElementById('custom-dashboard-grid');
    if (!section || !grid) return;
    stopActiveLoads();
    var generation = _loadGeneration;
    destroyCharts();
    if (window.CLOUD_MODE) {
      section.style.display = '';
      grid.textContent = 'Your custom panels are saved on your agent’s computer. Open the local ClawMetry dashboard to create or view them.';
      return;
    }
    grid.innerHTML = '<div class="cm-dashboard-loading">Loading saved panels…</div>';
    try {
      var payload = await requestJson('/api/dashboard/panels?limit=50', {}, LOAD_TIMEOUT_MS);
      if (!isCurrentLoad(generation)) return;
      var panels = Array.isArray(payload.panels) ? payload.panels : [];
      section.style.display = '';
      if (!panels.length) {
        grid.innerHTML = '<div class="cm-dashboard-empty-state">Ask a question in <a href="#" onclick="switchTab(\'assistant\');return false;">Assistant</a>, then add the result here as a permanent panel.</div>';
        return;
      }
      grid.innerHTML = '';
      var records = panels.map(function (panel) {
        var card = renderPanel(panel);
        grid.appendChild(card);
        return { panel: panel, body: card.querySelector('.cm-dashboard-panel-body') };
      });
      var nextRecord = 0;
      async function loadPanelDetails() {
        while (isCurrentLoad(generation)) {
          var record = records[nextRecord++];
          if (!record) return;
          try {
            var detail = await requestJson('/api/dashboard/panels/' + encodeURIComponent(record.panel.panel_id), {}, LOAD_TIMEOUT_MS);
            if (!isCurrentLoad(generation)) return;
            renderPanelBody(record.body, detail);
          } catch (error) {
            if (!isCurrentLoad(generation)) return;
            renderPanelBody(record.body, Object.assign({}, record.panel, { detail_error: loadError(error, 'This panel') }));
          }
        }
      }
      var workerCount = Math.min(4, records.length);
      await Promise.all(Array.from({ length: workerCount }, loadPanelDetails));
    } catch (e) {
      if (!isCurrentLoad(generation)) return;
      section.style.display = '';
      grid.innerHTML = '<div class="cm-dashboard-empty-state">Saved panels could not be loaded right now. Try refreshing the Home tab.</div>';
    }
  }

  async function deletePanel(panelId, card) {
    if (!panelId || !window.confirm('Remove this dashboard panel?')) return;
    var generation = _loadGeneration;
    try {
      await requestJson('/api/dashboard/panels/' + encodeURIComponent(panelId), { method: 'DELETE' }, LOAD_TIMEOUT_MS);
      if (!isCurrentLoad(generation)) return;
      if (_charts[panelId]) { _charts[panelId].destroy(); delete _charts[panelId]; }
      if (card) card.remove();
      var grid = document.getElementById('custom-dashboard-grid');
      if (grid && !grid.querySelector('.cm-dashboard-panel')) loadCustomDashboardPanels();
    } catch (e) {
      if (!isCurrentLoad(generation)) return;
      window.alert('The panel could not be removed right now.');
    }
  }

  window.loadCustomDashboardPanels = loadCustomDashboardPanels;
}());
