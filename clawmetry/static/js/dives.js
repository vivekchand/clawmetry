// Dives tab — plain-English questions → SQL → Chart.js / table
// Backend: POST /api/dives/query, /api/dives/save, GET /api/dives, /api/dives/<slug>
(function () {
  'use strict';

  var _divesChart = null;
  var _currentSpec = null;
  var _currentSql = null;
  var _currentQuestion = null;

  // ── Tab entry point (called by switchTab in app.js) ────────────────────────
  function loadDivesPage() {
    _loadSidebar();
  }

  // ── Run query ──────────────────────────────────────────────────────────────
  function divesRun() {
    var question = (document.getElementById('dives-question').value || '').trim();
    if (!question) return;

    var btn = document.getElementById('dives-run-btn');
    btn.disabled = true;
    btn.textContent = 'Running…';

    document.getElementById('dives-result-area').style.display = 'none';
    document.getElementById('dives-error').style.display = 'none';
    document.getElementById('dives-noauth-banner').style.display = 'none';

    fetch('/api/dives/query', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question: question }),
    })
      .then(function (r) { return r.json().then(function (d) { return { status: r.status, data: d }; }); })
      .then(function (res) {
        btn.disabled = false;
        btn.textContent = 'Run';
        if (res.status === 412 || res.data.error === 'no_auth') {
          document.getElementById('dives-noauth-banner').style.display = '';
          return;
        }
        if (res.data.error && !(res.data.rows && res.data.rows.length)) {
          _showError(res.data.error + (res.data.detail ? ': ' + res.data.detail : ''));
          return;
        }
        _currentQuestion = question;
        _currentSpec = res.data.chart_spec;
        _currentSql = res.data.sql;
        _renderResult(res.data);
      })
      .catch(function (err) {
        btn.disabled = false;
        btn.textContent = 'Run';
        _showError('Network error: ' + err.message);
      });
  }

  // ── Toggle SQL box ─────────────────────────────────────────────────────────
  function divesToggleSql() {
    var show = document.getElementById('dives-show-sql').checked;
    document.getElementById('dives-sql-box').style.display = show ? '' : 'none';
  }

  // ── Save current dive ──────────────────────────────────────────────────────
  function divesSave() {
    if (!_currentSql || !_currentQuestion) return;
    var name = window.prompt('Save as:', _currentQuestion.slice(0, 60)) || '';
    if (!name.trim()) return;
    fetch('/api/dives/save', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        question: _currentQuestion,
        sql: _currentSql,
        chart_spec: _currentSpec || {},
        name: name.trim(),
      }),
    })
      .then(function (r) { return r.json(); })
      .then(function (d) { if (d.slug) _loadSidebar(); })
      .catch(function () {});
  }

  // ── Load a saved dive ──────────────────────────────────────────────────────
  function divesLoadSaved(slug) {
    fetch('/api/dives/' + encodeURIComponent(slug))
      .then(function (r) { return r.json(); })
      .then(function (d) {
        if (d.error) { _showError(d.error); return; }
        _currentQuestion = d.question || '';
        _currentSpec = d.chart_spec;
        _currentSql = d.sql;
        if (_currentQuestion) document.getElementById('dives-question').value = _currentQuestion;
        _renderResult({ chart_spec: d.chart_spec, sql: d.sql, rows: d.rows || [], run_error: d.run_error });
      })
      .catch(function () {});
  }

  // ── Internal helpers ───────────────────────────────────────────────────────

  function _loadSidebar() {
    fetch('/api/dives')
      .then(function (r) { return r.json(); })
      .then(function (d) {
        var list = document.getElementById('dives-saved-list');
        if (!list) return;
        var dives = d.dives || [];
        if (!dives.length) {
          list.innerHTML = '<div style="color:var(--text-muted);font-size:12px;padding:4px 0;">No saved Dives yet.</div>';
          return;
        }
        list.innerHTML = dives.map(function (dive) {
          return '<div class="left-nav-item" style="padding:6px 8px;margin-bottom:4px;border-radius:6px;cursor:pointer;" onclick="divesLoadSaved(\'' + _esc(dive.slug) + '\')">'
            + '<div style="font-size:12px;color:var(--text-primary);white-space:nowrap;overflow:hidden;text-overflow:ellipsis;" title="' + _esc(dive.name || dive.question) + '">' + _esc(dive.name || dive.question) + '</div>'
            + '<div style="font-size:10px;color:var(--text-muted);">' + (dive.chart_type || 'table') + (dive.saved_at ? ' · ' + dive.saved_at.slice(0, 10) : '') + '</div>'
            + '</div>';
        }).join('');
      })
      .catch(function () {});
  }

  function _showError(msg) {
    var el = document.getElementById('dives-error');
    el.textContent = msg;
    el.style.display = '';
    document.getElementById('dives-result-area').style.display = '';
  }

  function _renderResult(data) {
    var spec = data.chart_spec || {};
    var rows = data.rows || [];

    document.getElementById('dives-result-title').textContent = spec.title || _currentQuestion || '';
    document.getElementById('dives-description').textContent = spec.description || '';
    document.getElementById('dives-timing').textContent = data.ms ? 'Query took ' + data.ms + 'ms' : '';
    document.getElementById('dives-sql-box').textContent = data.sql || '';
    document.getElementById('dives-show-sql').checked = false;
    document.getElementById('dives-sql-box').style.display = 'none';

    var errEl = document.getElementById('dives-error');
    if (data.error || data.run_error) {
      errEl.textContent = data.error || data.run_error;
      errEl.style.display = '';
    } else {
      errEl.style.display = 'none';
    }

    document.getElementById('dives-result-area').style.display = '';
    _renderChart(spec.chart_type || 'table', spec, rows);
  }

  function _renderChart(chartType, spec, rows) {
    var chartWrap = document.getElementById('dives-chart-wrap');
    var tableWrap = document.getElementById('dives-table-wrap');

    if (chartType === 'table' || !rows.length) {
      chartWrap.style.display = 'none';
      tableWrap.style.display = '';
      _renderTable(rows);
      if (_divesChart) { _divesChart.destroy(); _divesChart = null; }
      return;
    }

    chartWrap.style.display = '';
    tableWrap.style.display = 'none';

    var xKey = spec.x;
    var yKey = spec.y;
    var labels = rows.map(function (r) { return r[xKey] != null ? String(r[xKey]) : ''; });
    var values = rows.map(function (r) { var v = r[yKey]; return v != null ? parseFloat(v) || 0 : 0; });

    var canvas = document.getElementById('dives-chart');
    if (_divesChart) { _divesChart.destroy(); _divesChart = null; }

    var type = chartType === 'area' ? 'line' : chartType;
    var isArea = chartType === 'area';
    var isPie = type === 'pie';

    _divesChart = new Chart(canvas, {
      type: type,
      data: {
        labels: labels,
        datasets: [{
          label: yKey || 'value',
          data: values,
          backgroundColor: isPie
            ? labels.map(function (_, i) { return 'hsl(' + ((i * 47) % 360) + ',55%,55%)'; })
            : isArea ? 'rgba(58,123,213,0.2)' : 'rgba(58,123,213,0.7)',
          borderColor: (isArea || type === 'line') ? '#3a7bd5' : undefined,
          fill: isArea,
          tension: 0.3,
        }],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { display: isPie, labels: { color: '#ccc' } } },
        scales: isPie ? {} : {
          x: { ticks: { color: '#999', maxTicksLimit: 14 }, grid: { color: 'rgba(255,255,255,0.05)' } },
          y: { ticks: { color: '#999' }, grid: { color: 'rgba(255,255,255,0.05)' } },
        },
      },
    });
  }

  function _renderTable(rows) {
    var tbody = document.querySelector('#dives-table tbody');
    if (!rows.length) {
      tbody.innerHTML = '<tr><td style="color:#666;" colspan="99">No results.</td></tr>';
      return;
    }
    var cols = Object.keys(rows[0]);
    var header = '<tr>' + cols.map(function (c) { return '<th>' + _esc(c) + '</th>'; }).join('') + '</tr>';
    var body = rows.map(function (r) {
      return '<tr>' + cols.map(function (c) { return '<td>' + _esc(r[c] != null ? String(r[c]) : '') + '</td>'; }).join('') + '</tr>';
    }).join('');
    tbody.innerHTML = header + body;
  }

  function _esc(s) {
    return String(s || '')
      .replace(/&/g, '&amp;').replace(/</g, '&lt;')
      .replace(/>/g, '&gt;').replace(/"/g, '&quot;');
  }

  // ── Keyboard shortcut: Ctrl/Cmd+Enter submits the question ─────────────────
  document.addEventListener('DOMContentLoaded', function () {
    var ta = document.getElementById('dives-question');
    if (ta) {
      ta.addEventListener('keydown', function (e) {
        if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') divesRun();
      });
    }
  });

  // ── Expose to global scope (onclick attrs + app.js switchTab hook) ─────────
  window.loadDivesPage = loadDivesPage;
  window.divesRun = divesRun;
  window.divesToggleSql = divesToggleSql;
  window.divesSave = divesSave;
  window.divesLoadSaved = divesLoadSaved;
}());
