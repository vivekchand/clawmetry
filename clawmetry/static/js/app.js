// === Budget & Alert Functions ===
function openBudgetModal() {
  document.getElementById('budget-modal').style.display = 'flex';
  loadBudgetConfig();
  loadBudgetStatus();
}

function switchBudgetTab(tab, el) {
  document.querySelectorAll('#budget-modal-tabs .modal-tab').forEach(function(t){t.classList.remove('active');});
  if(el) el.classList.add('active');
  ['limits','alerts','telegram','history'].forEach(function(t){
    var d = document.getElementById('budget-tab-'+t);
    if(d) d.style.display = t===tab ? 'block' : 'none';
  });
  if(tab==='alerts') { loadAlertRules(); loadWebhookConfig(); }
  if(tab==='telegram') loadTelegramConfig();
  if(tab==='history') loadAlertHistory();
}

async function loadBudgetConfig() {
  try {
    var cfg = await fetch('/api/budget/config').then(function(r){return r.json();});
    document.getElementById('budget-daily').value = cfg.daily_limit || 0;
    document.getElementById('budget-weekly').value = cfg.weekly_limit || 0;
    document.getElementById('budget-monthly').value = cfg.monthly_limit || 0;
    document.getElementById('budget-warn-pct').value = cfg.warning_threshold_pct || 80;
    document.getElementById('budget-autopause').checked = cfg.auto_pause_enabled || false;
  } catch(e) {}
}

async function loadBudgetStatus() {
  try {
    var s = await fetch('/api/budget/status').then(function(r){return r.json();});
    var html = '';
    function row(label, spent, limit, pct) {
      var color = pct > 90 ? 'var(--text-error)' : pct > 70 ? 'var(--text-warning)' : 'var(--text-success)';
      html += '<div style="display:flex;justify-content:space-between;padding:4px 0;">';
      html += '<span>' + label + '</span>';
      html += '<span style="font-weight:600;color:' + color + ';">$' + spent.toFixed(2);
      if(limit > 0) html += ' / $' + limit.toFixed(2) + ' (' + pct.toFixed(0) + '%)';
      html += '</span></div>';
    }
    row('Today', s.daily_spent, s.daily_limit, s.daily_pct);
    row('This Week', s.weekly_spent, s.weekly_limit, s.weekly_pct);
    row('This Month', s.monthly_spent, s.monthly_limit, s.monthly_pct);
    if(s.paused) {
      html += '<div style="margin-top:8px;padding:8px;background:var(--bg-error);border-radius:6px;color:var(--text-error);font-weight:600;">&#9888;&#65039; Gateway PAUSED: ' + escHtml(s.paused_reason) + '</div>';
    }
    document.getElementById('budget-status-content').innerHTML = html;
  } catch(e) {
    document.getElementById('budget-status-content').textContent = 'Failed to load';
  }
}

async function saveBudgetConfig() {
  var data = {
    daily_limit: parseFloat(document.getElementById('budget-daily').value) || 0,
    weekly_limit: parseFloat(document.getElementById('budget-weekly').value) || 0,
    monthly_limit: parseFloat(document.getElementById('budget-monthly').value) || 0,
    warning_threshold_pct: parseInt(document.getElementById('budget-warn-pct').value) || 80,
    auto_pause_enabled: document.getElementById('budget-autopause').checked,
  };
  await fetch('/api/budget/config', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(data)});
  loadBudgetStatus();
}

async function resumeGateway() {
  await fetch('/api/budget/resume', {method:'POST'});
  document.getElementById('alert-banner').style.display = 'none';
  document.getElementById('alert-resume-btn').style.display = 'none';
  loadBudgetStatus();
}

function showAddAlertForm() {
  document.getElementById('add-alert-form').style.display = 'block';
}

async function createAlertRule() {
  var channels = [];
  if(document.getElementById('alert-ch-banner').checked) channels.push('banner');
  if(document.getElementById('alert-ch-telegram').checked) channels.push('telegram');
  var data = {
    type: document.getElementById('alert-type').value,
    threshold: parseFloat(document.getElementById('alert-threshold').value) || 0,
    channels: channels,
    cooldown_min: parseInt(document.getElementById('alert-cooldown').value) || 30,
  };
  await fetch('/api/alerts/rules', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(data)});
  document.getElementById('add-alert-form').style.display = 'none';
  loadAlertRules();
}

async function loadAlertRules() {
  try {
    var data = await fetch('/api/alerts/rules').then(function(r){return r.json();});
    var rules = data.rules || [];
    if(rules.length === 0) {
      document.getElementById('alert-rules-list').innerHTML = '<div style="padding:20px;text-align:center;color:var(--text-muted);">No alert rules configured</div>';
      return;
    }
    var html = '';
    rules.forEach(function(r) {
      var channels = [];
      try { channels = JSON.parse(r.channels); } catch(e) { channels = [r.channels]; }
      html += '<div style="padding:10px;border-bottom:1px solid var(--border-secondary);display:flex;align-items:center;gap:8px;">';
      html += '<span style="font-weight:600;">' + escHtml(r.type) + '</span>';
      html += '<span style="color:var(--text-accent);">' + (r.type==='spike' ? r.threshold+'x' : '$'+r.threshold) + '</span>';
      html += '<span style="color:var(--text-muted);font-size:11px;">' + channels.join(', ') + '</span>';
      html += '<span style="color:var(--text-muted);font-size:11px;">' + r.cooldown_min + 'min cooldown</span>';
      html += '<span style="margin-left:auto;cursor:pointer;color:var(--text-error);font-size:16px;" data-rule-id="'+r.id+'" onclick="deleteAlertRule(this.dataset.ruleId)" title="Delete">&#x1f5d1;</span>';
      html += '</div>';
    });
    document.getElementById('alert-rules-list').innerHTML = html;
  } catch(e) {
    document.getElementById('alert-rules-list').textContent = 'Failed to load';
  }
}

async function deleteAlertRule(id) {
  await fetch('/api/alerts/rules/'+id, {method:'DELETE'});
  loadAlertRules();
}

async function loadWebhookConfig() {
  try {
    var cfg = await fetch('/api/alert-channels').then(function(r){return r.json();});
    document.getElementById('alert-webhook-url').value = cfg.webhook_url || '';
    document.getElementById('alert-slack-url').value = cfg.slack_webhook_url || '';
    document.getElementById('alert-discord-url').value = cfg.discord_webhook_url || '';
    document.getElementById('alert-toggle-cost-spike').checked = cfg.cost_spike_alerts !== false;
    document.getElementById('alert-toggle-agent-error').checked = cfg.agent_error_rate_alerts !== false;
    document.getElementById('alert-toggle-security').checked = cfg.security_posture_changes !== false;
    var minSevEl = document.getElementById('alert-min-severity');
    if (minSevEl) minSevEl.value = cfg.min_severity || 'warning';
    document.getElementById('alert-webhook-status').textContent = '';
  } catch(e) {}
}

async function saveWebhookConfig() {
  var status = document.getElementById('alert-webhook-status');
  status.textContent = 'Saving...';
  var minSevEl = document.getElementById('alert-min-severity');
  var payload = {
    webhook_url: document.getElementById('alert-webhook-url').value.trim(),
    slack_webhook_url: document.getElementById('alert-slack-url').value.trim(),
    discord_webhook_url: document.getElementById('alert-discord-url').value.trim(),
    cost_spike_alerts: document.getElementById('alert-toggle-cost-spike').checked,
    agent_error_rate_alerts: document.getElementById('alert-toggle-agent-error').checked,
    security_posture_changes: document.getElementById('alert-toggle-security').checked,
    min_severity: minSevEl ? minSevEl.value : 'warning',
  };
  try {
    var r = await fetch('/api/alert-channels', {
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body:JSON.stringify(payload)
    });
    if (!r.ok) throw new Error('Save failed');
    status.style.color = 'var(--text-success)';
    status.textContent = 'Saved';
  } catch(e) {
    status.style.color = 'var(--text-error)';
    status.textContent = 'Save failed';
  }
}

async function testWebhookConfig(target) {
  var status = document.getElementById('alert-webhook-status');
  status.style.color = 'var(--text-muted)';
  status.textContent = 'Sending test...';
  try {
    var r = await fetch('/api/alert-channels/test', {
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body:JSON.stringify({target: target || 'all', severity: 'warning'})
    });
    var data = await r.json();
    if(data.ok) {
      status.style.color = 'var(--text-success)';
      status.textContent = 'Test sent to: ' + (data.sent || []).join(', ');
    } else {
      status.style.color = 'var(--text-error)';
      status.textContent = data.error || 'No URL configured for ' + (target || 'all');
    }
  } catch(e) {
    status.style.color = 'var(--text-error)';
    status.textContent = 'Test failed';
  }
}

async function loadAlertHistory() {
  try {
    var data = await fetch('/api/alerts/history?limit=50').then(function(r){return r.json();});
    var alerts = data.alerts || [];
    if(alerts.length === 0) {
      document.getElementById('alert-history-list').innerHTML = '<div style="padding:20px;text-align:center;color:var(--text-muted);">No alerts fired yet</div>';
      return;
    }
    var html = '';
    alerts.forEach(function(a) {
      var ts = new Date(a.fired_at * 1000).toLocaleString();
      var ack = a.acknowledged ? '<span style="color:var(--text-success);">&#10003;</span>' : '<span style="color:var(--text-warning);">&#x25cf;</span>';
      html += '<div style="padding:8px;border-bottom:1px solid var(--border-secondary);font-size:12px;">';
      html += ack + ' <span style="color:var(--text-muted);">' + ts + '</span> ';
      html += '<span style="font-weight:600;">[' + escHtml(a.type) + ']</span> ';
      html += escHtml(a.message);
      html += '</div>';
    });
    document.getElementById('alert-history-list').innerHTML = html;
  } catch(e) {
    document.getElementById('alert-history-list').textContent = 'Failed to load';
  }
}

async function checkActiveAlerts() {
  try {
    var data = await fetch('/api/alerts/active').then(function(r){return r.json();});
    var alerts = data.alerts || [];
    var banner = document.getElementById('alert-banner');
    if(alerts.length === 0) {
      banner.style.display = 'none';
      return;
    }
    // Show most recent alert
    var latest = alerts[0];
    document.getElementById('alert-banner-msg').textContent = latest.message;
    banner.style.display = 'flex';
    // Show resume button if gateway is paused
    var status = await fetch('/api/budget/status').then(function(r){return r.json();});
    document.getElementById('alert-resume-btn').style.display = status.paused ? '' : 'none';
  } catch(e) {}
}

async function ackAllAlerts() {
  try {
    var data = await fetch('/api/alerts/active').then(function(r){return r.json();});
    var alerts = data.alerts || [];
    for(var i=0; i<alerts.length; i++) {
      await fetch('/api/alerts/history/'+alerts[i].id+'/ack', {method:'POST'});
    }
    document.getElementById('alert-banner').style.display = 'none';
  } catch(e) {}
}

// Check alerts every 30s
setInterval(checkActiveAlerts, 30000);
setTimeout(checkActiveAlerts, 3000);

// === Anomaly Detection Banner ===
var _anomalyBannerEl = null;
function _getOrCreateAnomalyBanner() {
  if (_anomalyBannerEl) return _anomalyBannerEl;
  var existing = document.getElementById('anomaly-engine-banner');
  if (existing) { _anomalyBannerEl = existing; return existing; }
  var el = document.createElement('div');
  el.id = 'anomaly-engine-banner';
  el.style.cssText = 'display:none;padding:10px 16px;background:#451a03;border-bottom:2px solid #f59e0b;color:#fbbf24;font-size:13px;font-weight:600;align-items:center;gap:10px;';
  el.innerHTML = '<span style="font-size:18px;">&#128680;</span><span id="anomaly-banner-msg" style="flex:1;"></span><a href="#" onclick="switchTab(\'usage\');loadAnomalyPanel();checkAnomalies();return false;" style="color:#fbbf24;text-decoration:underline;font-size:12px;margin-right:8px;">View Details</a><button onclick="document.getElementById(\'anomaly-engine-banner\').style.display=\'none\';" style="background:#92400e;color:#fef3c7;border:none;border-radius:6px;padding:4px 10px;font-size:12px;cursor:pointer;">Dismiss</button>';
  // Insert after alert-banner
  var alertBanner = document.getElementById('alert-banner');
  if (alertBanner && alertBanner.parentNode) {
    alertBanner.parentNode.insertBefore(el, alertBanner.nextSibling);
  } else {
    document.body.insertBefore(el, document.body.firstChild);
  }
  _anomalyBannerEl = el;
  return el;
}

async function checkAnomalies() {
  try {
    var data = await fetch('/api/anomalies').then(function(r){return r.json();});
    var banner = _getOrCreateAnomalyBanner();
    if (!data.has_active || data.active_count === 0) {
      banner.style.display = 'none';
      return;
    }
    var anomalies = (data.anomalies || []).filter(function(a){ return !a.acknowledged; });
    if (anomalies.length === 0) { banner.style.display = 'none'; return; }
    // Summarize: show most severe
    var bySeverity = {critical: [], high: [], medium: []};
    anomalies.forEach(function(a) {
      var sev = a.severity || 'medium';
      if (bySeverity[sev]) bySeverity[sev].push(a);
    });
    var topAnomaly = bySeverity.critical[0] || bySeverity.high[0] || bySeverity.medium[0];
    var metricLabels = {cost_spike: 'cost spike', token_spike: 'token spike', error_rate_spike: 'error rate spike', session_frequency_spike: 'session frequency spike'};
    var label = metricLabels[topAnomaly.metric] || topAnomaly.metric;
    var msg = 'Anomaly detected: ' + label + ' (' + Number(topAnomaly.ratio || 0).toFixed(1) + 'x baseline)';
    if (anomalies.length > 1) msg += ' + ' + (anomalies.length - 1) + ' more';
    document.getElementById('anomaly-banner-msg').textContent = msg;
    var isCritical = bySeverity.critical.length > 0;
    banner.style.background = isCritical ? '#7f1d1d' : '#451a03';
    banner.style.color = isCritical ? '#fca5a5' : '#fbbf24';
    banner.style.borderColor = isCritical ? '#ef4444' : '#f59e0b';
    banner.style.display = 'flex';
  } catch(e) {}
}

// Check anomalies every 5 minutes
setInterval(checkAnomalies, 300000);
setTimeout(checkAnomalies, 8000);

// === Anomaly Detection Panel (GH #304) ===
function _ensureAnomalyPanel() {
  var existing = document.getElementById('anomaly-panel');
  if (existing) return existing;
  // Create panel dynamically after system health panel
  var shPanel = document.getElementById('system-health-panel');
  if (!shPanel || !shPanel.parentNode) return null;
  var panel = document.createElement('div');
  panel.id = 'anomaly-panel';
  panel.style.cssText = 'background:var(--bg-secondary);border:1px solid var(--border-primary);border-radius:12px;padding:16px;margin-top:14px;box-shadow:var(--card-shadow);';
  panel.innerHTML = '<div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:12px;"><div style="font-size:14px;font-weight:700;color:var(--text-primary);">&#128269; Anomaly Detection</div><span id="anomaly-panel-badge" style="font-size:11px;font-weight:600;padding:2px 8px;border-radius:10px;display:none;"></span></div><div id="anomaly-baselines" style="display:flex;flex-wrap:wrap;gap:8px;margin-bottom:12px;font-size:11px;"></div><div id="anomaly-list" style="max-height:300px;overflow-y:auto;"></div>';
  shPanel.parentNode.insertBefore(panel, shPanel.nextSibling);
  return panel;
}

async function loadAnomalyPanel() {
  try {
    var data = await fetch('/api/anomalies').then(function(r){return r.json();});
    var panel = _ensureAnomalyPanel();
    if (!panel) return;
    var anomalies = data.anomalies || [];
    var baselines = data.baselines || {};
    var active = anomalies.filter(function(a){ return !a.acknowledged; });

    // Badge
    var badge = document.getElementById('anomaly-panel-badge');
    if (badge) {
      if (active.length > 0) {
        var hasCrit = active.some(function(a){ return a.severity === 'critical'; });
        badge.textContent = active.length + ' active';
        badge.style.background = hasCrit ? '#7f1d1d' : '#451a03';
        badge.style.color = hasCrit ? '#fca5a5' : '#fbbf24';
        badge.style.display = 'inline-block';
      } else {
        badge.textContent = 'all clear';
        badge.style.background = '#064e3b';
        badge.style.color = '#6ee7b7';
        badge.style.display = 'inline-block';
      }
    }

    // Baselines
    var blEl = document.getElementById('anomaly-baselines');
    if (blEl) {
      var blHtml = '';
      if (baselines.baseline_cost_7d > 0) blHtml += '<span style="background:var(--bg-hover);padding:3px 8px;border-radius:6px;color:var(--text-secondary);">Avg cost: $' + Number(baselines.baseline_cost_7d).toFixed(4) + '/session</span>';
      if (baselines.baseline_tokens_7d > 0) blHtml += '<span style="background:var(--bg-hover);padding:3px 8px;border-radius:6px;color:var(--text-secondary);">Avg tokens: ' + Math.round(baselines.baseline_tokens_7d).toLocaleString() + '/session</span>';
      if (baselines.baseline_sessions_per_day_7d > 0) blHtml += '<span style="background:var(--bg-hover);padding:3px 8px;border-radius:6px;color:var(--text-secondary);">Sessions/day: ' + Number(baselines.baseline_sessions_per_day_7d).toFixed(1) + '</span>';
      blEl.innerHTML = blHtml || '<span style="color:var(--text-muted);">Collecting baseline data...</span>';
    }

    // Anomaly list
    var listEl = document.getElementById('anomaly-list');
    if (!listEl) return;
    if (anomalies.length === 0) {
      listEl.innerHTML = '<div style="text-align:center;padding:16px;color:var(--text-muted);font-size:12px;">No anomalies in last 48h. Baselines from 7-day rolling window.</div>';
      return;
    }

    var metricIcons = {cost_spike:'&#128176;', token_spike:'&#128202;', error_rate_spike:'&#10060;', session_frequency_spike:'&#128200;'};
    var metricNames = {cost_spike:'Cost Spike', token_spike:'Token Spike', error_rate_spike:'Error Rate Spike', session_frequency_spike:'Session Frequency Spike'};
    var sevColors = {critical:'#ef4444', high:'#f59e0b', medium:'#6366f1'};
    var sevBgs = {critical:'#7f1d1d', high:'#451a03', medium:'#1e1b4b'};

    var html = '';
    anomalies.slice(0, 20).forEach(function(a) {
      var icon = metricIcons[a.metric] || '&#9888;';
      var name = metricNames[a.metric] || a.metric;
      var sevCol = sevColors[a.severity] || '#888';
      var sevBg = sevBgs[a.severity] || 'var(--bg-hover)';
      var acked = a.acknowledged;
      var dt = new Date(a.detected_at * 1000);
      var timeStr = dt.toLocaleTimeString([], {hour:'2-digit', minute:'2-digit'}) + ' ' + dt.toLocaleDateString([], {month:'short', day:'numeric'});
      var valStr = a.metric === 'cost_spike' ? '$' + Number(a.value).toFixed(4) : a.metric === 'error_rate_spike' ? (Number(a.value * 100).toFixed(1) + '%') : a.metric === 'session_frequency_spike' ? (Number(a.value) + ' sessions') : Number(a.value).toLocaleString();
      var baseStr = a.metric === 'cost_spike' ? '$' + Number(a.baseline).toFixed(4) : a.metric === 'error_rate_spike' ? (Number(a.baseline * 100).toFixed(1) + '%') : a.metric === 'session_frequency_spike' ? (Number(a.baseline).toFixed(1) + '/day') : Number(a.baseline).toLocaleString();

      html += '<div style="background:' + (acked ? 'var(--bg-hover)' : sevBg) + ';border:1px solid ' + (acked ? 'var(--border-primary)' : sevCol + '44') + ';border-left:3px solid ' + sevCol + ';border-radius:8px;padding:10px 12px;margin-bottom:6px;' + (acked ? 'opacity:0.5;' : '') + '">';
      html += '<div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:4px;">';
      html += '<span style="font-size:12px;font-weight:600;color:' + sevCol + ';">' + icon + ' ' + name + ' <span style="font-size:10px;color:var(--text-muted);">(' + Number(a.ratio).toFixed(1) + 'x baseline)</span></span>';
      if (!acked) html += '<button onclick="ackAnomaly(' + a.id + ')" style="background:transparent;border:1px solid var(--border-secondary);color:var(--text-muted);border-radius:4px;padding:2px 6px;font-size:10px;cursor:pointer;">Ack</button>';
      html += '</div>';
      html += '<div style="font-size:11px;color:var(--text-secondary);">';
      html += 'Value: <b>' + valStr + '</b> vs baseline <b>' + baseStr + '</b>';
      if (a.session_key && a.session_key.indexOf('__') !== 0) html += ' &middot; Session: <span style="font-family:monospace;font-size:10px;">' + a.session_key.substring(0, 16) + '</span>';
      html += ' &middot; <span style="color:var(--text-muted);">' + timeStr + '</span>';
      html += '</div></div>';
    });
    listEl.innerHTML = html;
  } catch(e) { /* non-critical */ }
}

async function ackAnomaly(id) {
  try {
    await fetch('/api/anomalies/' + id + '/ack', {method:'POST'});
    loadAnomalyPanel();
    checkAnomalies();
  } catch(e) {}
}

// Load anomaly panel on overview and refresh every 2 minutes
setTimeout(loadAnomalyPanel, 4000);
setInterval(loadAnomalyPanel, 120000);

// === Heartbeat Gap Alerting ===
async function checkHeartbeatStatus() {
  try {
    var data = await fetch('/api/heartbeat-status').then(function(r){return r.json();});
    var banner = document.getElementById('heartbeat-banner');
    if (!banner) return;
    if (data.status === 'warning' || data.status === 'silent') {
      var gap = data.gap_seconds;
      var gapStr = gap >= 3600 ? Math.floor(gap/3600) + 'h ' + Math.floor((gap%3600)/60) + 'm' : Math.floor(gap/60) + ' minutes';
      var intervalMin = Math.floor(data.interval_seconds / 60);
      var msg = data.status === 'silent'
        ? 'Agent heartbeat SILENT for ' + gapStr + ' (expected every ' + intervalMin + 'm). Check if agent is running.'
        : 'Heartbeat delayed: last seen ' + gapStr + ' ago (expected every ' + intervalMin + 'm)';
      document.getElementById('heartbeat-banner-msg').textContent = msg;
      banner.style.background = data.status === 'silent' ? '#7f1d1d' : '#451a03';
      banner.style.color = data.status === 'silent' ? '#fca5a5' : '#fbbf24';
      banner.style.borderColor = data.status === 'silent' ? '#ef4444' : '#f59e0b';
      banner.style.display = 'flex';
    } else {
      banner.style.display = 'none';
    }
  } catch(e) {}
}
setInterval(checkHeartbeatStatus, 30000);
setTimeout(checkHeartbeatStatus, 5000);

function dismissPausedBanner() {
  localStorage.setItem('cm_paused_banner_dismissed', String(Date.now()));
  var banner = document.getElementById('paused-banner');
  if (banner) banner.style.display = 'none';
}

async function refreshPausedBanner() {
  try {
    var status = await fetch('/api/budget/status').then(function(r){return r.json();});
    var banner = document.getElementById('paused-banner');
    if (!banner) return;
    if (!status.paused) {
      banner.style.display = 'none';
      return;
    }
    var dismissedAt = parseInt(localStorage.getItem('cm_paused_banner_dismissed') || '0', 10) || 0;
    var pausedAtMs = Math.floor((status.paused_at || 0) * 1000);
    if (dismissedAt >= pausedAtMs && pausedAtMs > 0) {
      banner.style.display = 'none';
      return;
    }
    var reason = status.paused_reason || 'Auto-pause active';
    document.getElementById('paused-banner-msg').textContent = 'PAUSED: ' + reason;
    banner.style.display = 'flex';
  } catch(e) {}
}
setInterval(refreshPausedBanner, 15000);
setTimeout(refreshPausedBanner, 1500);

// === Telegram Config Functions ===
async function loadTelegramConfig() {
  try {
    var cfg = await fetch('/api/budget/config').then(function(r){return r.json();});
    var tokenEl = document.getElementById('tg-bot-token');
    var chatEl = document.getElementById('tg-chat-id');
    if(cfg.telegram_bot_token) tokenEl.value = cfg.telegram_bot_token;
    if(cfg.telegram_chat_id) chatEl.value = cfg.telegram_chat_id;
    var statusEl = document.getElementById('tg-status');
    if(cfg.telegram_bot_token && cfg.telegram_chat_id) {
      statusEl.innerHTML = '<span style="color:var(--text-success);">Configured</span>';
    } else {
      statusEl.innerHTML = '<span style="color:var(--text-muted);">Not configured</span>';
    }
  } catch(e) {}
}

async function saveTelegramConfig() {
  var token = document.getElementById('tg-bot-token').value.trim();
  var chatId = document.getElementById('tg-chat-id').value.trim();
  await fetch('/api/budget/config', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({telegram_bot_token: token, telegram_chat_id: chatId})
  });
  document.getElementById('tg-status').innerHTML = '<span style="color:var(--text-success);">Saved!</span>';
}

async function testTelegram() {
  var statusEl = document.getElementById('tg-status');
  statusEl.innerHTML = '<span style="color:var(--text-muted);">Sending...</span>';
  try {
    var r = await fetch('/api/budget/test-telegram', {method: 'POST'});
    var data = await r.json();
    if(data.ok) {
      statusEl.innerHTML = '<span style="color:var(--text-success);">Test sent!</span>';
    } else {
      statusEl.innerHTML = '<span style="color:var(--text-error);">' + escHtml(data.error || 'Failed') + '</span>';
    }
  } catch(e) {
    statusEl.innerHTML = '<span style="color:var(--text-error);">Request failed</span>';
  }
}

function switchTab(name) {
  document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
  document.querySelectorAll('.nav-tab').forEach(t => t.classList.remove('active'));
  var page = document.getElementById('page-' + name);
  if (page) page.classList.add('active');
  var tabs = document.querySelectorAll('.nav-tab');
  tabs.forEach(function(t) { if (t.getAttribute('onclick') && t.getAttribute('onclick').indexOf("'" + name + "'") !== -1) t.classList.add('active'); });
  if (!document.querySelector('.nav-tab.active') && typeof event !== 'undefined' && event && event.target) event.target.classList.add('active');
  // Stop cron auto-refresh when leaving crons tab
  if (name !== 'crons' && _cronAutoRefreshTimer) { clearInterval(_cronAutoRefreshTimer); _cronAutoRefreshTimer = null; }
  if (name === 'overview') loadAll();
  if (name === 'overview') { if (typeof _velocityPollTimer !== 'undefined' && _velocityPollTimer) clearInterval(_velocityPollTimer); if (typeof loadTokenVelocity === 'function') _velocityPollTimer = setInterval(loadTokenVelocity, 30000); }
  if (name === 'usage') loadUsage();
  if (name === 'skills') loadSkills();
  if (name === 'crons') loadCrons();
  if (name === 'memory') loadMemory();
  if (name === 'transcripts') loadTranscripts();
  if (name === 'version-impact') loadVersionImpact();
  if (name === 'clusters') loadClusters();
  if (name === 'limits') loadRateLimits();
  if (name === 'flow') initFlow();
  if (name === 'context') loadContextInspector();
  if (name === 'history') loadHistory();
  if (name === 'brain') loadBrainPage();
  if (name === 'selfevolve') loadSelfEvolvePage();
  if (name === 'notifications') { if (typeof loadNotificationsPage === 'function') loadNotificationsPage(); }
  if (name === 'security') { loadSecurityPage(); loadSecurityPosture(); }
  if (name === 'approvals') { if (typeof loadApprovalsTab === 'function') loadApprovalsTab(); }
  if (name === 'alerts') { if (typeof loadAlertsPage === 'function') loadAlertsPage(); }
  if (name === 'actions') loadQAHistory();
  if (name === 'logs') { if (!logStream || logStream.readyState === EventSource.CLOSED) startLogStream(); loadLogs(); }
  if (name === 'models') loadModelAttribution();
  if (name === 'nemoclaw') { loadNemoClaw(); _startNcApprovalsAutoRefresh(); }
  if (name !== 'nemoclaw') _stopNcApprovalsAutoRefresh();
  if (name === 'subagents') { loadSubagents(); if (!_subagentsTimer) _subagentsTimer = setInterval(loadSubagents, 5000); }
  if (name !== 'subagents' && _subagentsTimer) { clearInterval(_subagentsTimer); _subagentsTimer = null; }
}

function exportUsageData() {
  window.location.href = '/api/usage/export';
}

// ── Human-friendly helpers (shared) ──────────────────────────────────────────
function _friendlyDuration(secs) {
  if (secs == null || isNaN(secs)) return '—';
  secs = Math.round(secs);
  if (secs < 60) return secs + ' seconds';
  if (secs < 3600) {
    var m = Math.round(secs / 60);
    return m + (m === 1 ? ' minute' : ' minutes');
  }
  if (secs < 86400) {
    var h = Math.floor(secs / 3600);
    var mm = Math.round((secs % 3600) / 60);
    if (mm === 0) return h + (h === 1 ? ' hour' : ' hours');
    return h + 'h ' + mm + 'm';
  }
  var d = Math.round(secs / 86400);
  return d + (d === 1 ? ' day' : ' days');
}

function _friendlyAgo(seconds) {
  if (seconds == null) return 'never';
  if (seconds < 60) return 'just now';
  if (seconds < 3600) {
    var m = Math.floor(seconds / 60);
    return m + (m === 1 ? ' minute ago' : ' minutes ago');
  }
  if (seconds < 86400) {
    var h = Math.floor(seconds / 3600);
    return h + (h === 1 ? ' hour ago' : ' hours ago');
  }
  var d = Math.floor(seconds / 86400);
  return d + (d === 1 ? ' day ago' : ' days ago');
}

function _friendlyTimestamp(ts) {
  if (!ts) return '—';
  var d = new Date(ts * 1000);
  var now = new Date();
  var sameDay = d.toDateString() === now.toDateString();
  var yesterday = new Date(now); yesterday.setDate(now.getDate() - 1);
  var wasYesterday = d.toDateString() === yesterday.toDateString();
  var time = d.toLocaleTimeString([], {hour:'numeric', minute:'2-digit'});
  if (sameDay) return 'Today at ' + time;
  if (wasYesterday) return 'Yesterday at ' + time;
  var daysAgo = Math.floor((now - d) / 86400000);
  if (daysAgo < 7) return d.toLocaleDateString([], {weekday:'long'}) + ' at ' + time;
  return d.toLocaleDateString([], {month:'short', day:'numeric'}) + ' at ' + time;
}

function _friendlyBytes(n) {
  if (n == null) return '—';
  if (n < 1024) return n + ' bytes';
  if (n < 1024 * 1024) return (n / 1024).toFixed(1) + ' KB';
  return (n / (1024 * 1024)).toFixed(1) + ' MB';
}

// ── Autonomy: how independently your agent runs ──────────────────────────────
async function loadAutonomy() {
  var labelEl = document.getElementById('autonomy-score-label');
  var badgeEl = document.getElementById('autonomy-trend-badge');
  var gapEl   = document.getElementById('autonomy-median-gap');
  var trendEl = document.getElementById('autonomy-trend-pct');
  var svgEl   = document.getElementById('autonomy-sparkline');
  var sampEl  = document.getElementById('autonomy-samples');
  if (!labelEl) return;

  function scoreToLabel(s) {
    if (s >= 0.8) return { text: 'Fully independent', color: '#22c55e' };
    if (s >= 0.5) return { text: 'Mostly independent', color: '#84cc16' };
    if (s >= 0.2) return { text: 'Getting there', color: '#f59e0b' };
    return { text: 'Needs guidance', color: '#94a3b8' };
  }

  try {
    var d = await (typeof fetchJsonWithTimeout === 'function'
      ? fetchJsonWithTimeout('/api/autonomy', 5000)
      : fetch('/api/autonomy').then(function(r){return r.json();}));

    if (d.score == null) {
      labelEl.textContent = 'Just getting started';
      labelEl.style.color = 'var(--text-muted)';
      if (gapEl) gapEl.textContent = 'Use your agent a bit and we\u2019ll show how independent it\u2019s becoming.';
      if (badgeEl) { badgeEl.textContent = ''; badgeEl.style.background = ''; badgeEl.style.border = ''; }
      if (trendEl) trendEl.textContent = '';
      if (sampEl) sampEl.textContent = '';
      return;
    }

    var lbl = scoreToLabel(d.score);
    labelEl.textContent = lbl.text;
    labelEl.style.color = lbl.color;

    if (gapEl && d.median_gap_seconds_7d != null) {
      gapEl.textContent = 'You check in about every ' + _friendlyDuration(d.median_gap_seconds_7d) + '.';
    } else if (gapEl) {
      gapEl.textContent = '';
    }

    if (badgeEl) {
      var dir = d.trend_direction || 'flat';
      var presets = {
        improving:  { text: '\u2191 getting more independent', bg: 'rgba(34,197,94,0.15)', color: '#22c55e', border: 'rgba(34,197,94,0.4)' },
        declining:  { text: '\u2193 needs more guidance',      bg: 'rgba(239,68,68,0.15)', color: '#ef4444', border: 'rgba(239,68,68,0.4)' },
        flat:       { text: 'steady this week',                bg: 'rgba(100,116,139,0.12)', color: 'var(--text-muted)', border: 'var(--border-primary)' },
        no_data:    { text: 'no data yet',                     bg: 'rgba(100,116,139,0.12)', color: 'var(--text-muted)', border: 'var(--border-primary)' }
      };
      var p = presets[dir] || presets.flat;
      badgeEl.textContent = p.text;
      badgeEl.style.background = p.bg;
      badgeEl.style.color = p.color;
      badgeEl.style.border = '1px solid ' + p.border;
    }

    if (trendEl) trendEl.textContent = '';

    if (sampEl && d.samples_7d != null) {
      sampEl.textContent = d.samples_7d + ' check-in' + (d.samples_7d !== 1 ? 's' : '') + ' this week';
    }

    if (svgEl && d.series_daily && d.series_daily.length > 0) {
      var ratios = d.series_daily.map(function(e){ return e.autonomy_ratio; });
      var valid = ratios.filter(function(v){ return v != null; });
      if (valid.length >= 2) {
        var W = 160, H = 48, pad = 4;
        var n = ratios.length;
        var step = (W - pad * 2) / Math.max(n - 1, 1);
        var pts = ratios.map(function(v, i) {
          var x = pad + i * step;
          var y = v == null ? null : H - pad - v * (H - pad * 2);
          return {x: x, y: y};
        });
        var pathD = '';
        pts.forEach(function(p, i) {
          if (p.y == null) return;
          if (!pathD || pts.slice(0, i).every(function(q){ return q.y == null; })) {
            pathD += 'M' + p.x.toFixed(1) + ',' + p.y.toFixed(1);
          } else {
            pathD += ' L' + p.x.toFixed(1) + ',' + p.y.toFixed(1);
          }
        });
        var svgContent = '';
        var firstP = pts.find(function(p){ return p.y != null; });
        var lastP = null; pts.forEach(function(p){ if(p.y != null) lastP = p; });
        if (firstP && lastP && pathD) {
          var fillD = pathD + ' L' + lastP.x.toFixed(1) + ',' + (H - pad) + ' L' + firstP.x.toFixed(1) + ',' + (H - pad) + ' Z';
          svgContent += '<path d="' + fillD + '" fill="rgba(99,102,241,0.15)" stroke="none"/>';
          svgContent += '<path d="' + pathD + '" fill="none" stroke="#6366f1" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>';
        }
        pts.forEach(function(p) {
          if (p.y == null) return;
          svgContent += '<circle cx="' + p.x.toFixed(1) + '" cy="' + p.y.toFixed(1) + '" r="2.5" fill="#6366f1"/>';
        });
        svgEl.innerHTML = svgContent;
      } else {
        svgEl.innerHTML = '<text x="80" y="28" text-anchor="middle" fill="var(--text-muted)" font-size="10">Not enough data yet</text>';
      }
    }
  } catch(e) {
    console.warn('autonomy load failed', e);
    if (labelEl) labelEl.textContent = '—';
    if (gapEl) gapEl.textContent = 'Couldn\u2019t load right now.';
  }
}

// ── Heartbeat: is your agent alive? ──────────────────────────────────────────
async function loadHeartbeat() {
  try {
    var d = await (typeof fetchJsonWithTimeout === 'function'
      ? fetchJsonWithTimeout('/api/heartbeat', 5000)
      : fetch('/api/heartbeat').then(function(r){return r.json();}));
    var dot = document.getElementById('hb-pulse-dot');
    var label = document.getElementById('hb-pulse-label');
    var badge = document.getElementById('hb-status-badge');
    var lastBeat = document.getElementById('hb-last-beat');
    var cadenceEl = document.getElementById('hb-cadence');
    var okRatioLineEl = document.getElementById('hb-ok-ratio-line');
    var sparkEl = document.getElementById('hb-sparkline');
    if (!dot) return;

    var status = d.status || 'never';
    var labels = {
      healthy:  { status: 'Alive and well',   pulse: 'checking in',    badge: 'Healthy' },
      drifting: { status: 'Running a bit late', pulse: 'slow',         badge: 'Late' },
      missed:   { status: 'Something\u2019s wrong', pulse: 'missed',   badge: 'Missed' },
      never:    { status: 'No check-ins yet', pulse: 'waiting...',     badge: 'Waiting' }
    };
    var colors = { healthy: '#22c55e', drifting: '#f59e0b', missed: '#ef4444', never: '#6b7280' };
    var anims = {
      healthy:  'hb-pulse-healthy 2s ease-in-out infinite',
      drifting: 'hb-pulse-drifting 1.5s ease-in-out infinite',
      missed:   'hb-pulse-missed 1.2s ease-in-out infinite',
      never:    'none'
    };
    var badgeColors = {
      healthy:  { bg: 'rgba(34,197,94,0.15)',   color: '#4ade80' },
      drifting: { bg: 'rgba(245,158,11,0.15)',  color: '#fbbf24' },
      missed:   { bg: 'rgba(239,68,68,0.15)',   color: '#f87171' },
      never:    { bg: 'rgba(107,114,128,0.15)', color: '#9ca3af' }
    };
    var L = labels[status] || labels.never;

    dot.style.background = colors[status] || colors.never;
    dot.style.animation = anims[status] || 'none';
    if (label) label.textContent = L.pulse;
    if (badge) {
      var bc = badgeColors[status] || badgeColors.never;
      badge.style.background = bc.bg;
      badge.style.color = bc.color;
      badge.textContent = L.badge;
    }

    if (lastBeat) {
      if (status === 'never') {
        lastBeat.textContent = 'not yet';
        lastBeat.style.color = '#9ca3af';
      } else if (d.last_heartbeat_age_seconds !== null && d.last_heartbeat_age_seconds !== undefined) {
        lastBeat.textContent = _friendlyAgo(d.last_heartbeat_age_seconds);
        lastBeat.style.color = colors[status] || '#9ca3af';
      } else {
        lastBeat.textContent = 'not yet';
        lastBeat.style.color = '#9ca3af';
      }
    }

    if (cadenceEl && d.cadence_24h) {
      var c = d.cadence_24h;
      if (c.expected_beats === 0) {
        cadenceEl.textContent = '';
      } else if (c.actual_beats === 0) {
        cadenceEl.textContent = 'Expected ' + c.expected_beats + ' check-ins today, got none yet';
      } else {
        cadenceEl.textContent = 'Checked in ' + c.actual_beats + ' of ' + c.expected_beats + ' expected today';
      }
    }

    if (okRatioLineEl && d.ok_vs_action_24h) {
      var oa = d.ok_vs_action_24h;
      var total = oa.heartbeat_ok_count + oa.action_taken_count;
      if (total === 0) {
        okRatioLineEl.textContent = '';
      } else {
        var quietPct = Math.round(oa.ok_ratio * 100);
        var actedPct = 100 - quietPct;
        okRatioLineEl.textContent = quietPct + '% quiet check-ins' + (actedPct > 0 ? ' \u00B7 ' + actedPct + '% took action' : '');
      }
    }

    if (sparkEl && d.recent_beats && d.recent_beats.length > 0) {
      sparkEl.innerHTML = d.recent_beats.map(function(b) {
        var cc = b.outcome === 'ok' ? '#22c55e' : '#f59e0b';
        var title = b.outcome === 'ok' ? 'Quiet check-in' : 'Took action';
        return '<span title="' + title + '" style="display:inline-block;width:10px;height:10px;border-radius:50%;background:' + cc + ';"></span>';
      }).join('');
    } else if (sparkEl) {
      sparkEl.innerHTML = '<span style="font-size:11px;color:var(--text-muted);">none yet</span>';
    }
  } catch(e) { console.warn('heartbeat panel load failed', e); }
}

// ── Memory: commit-log + editor ──────────────────────────────────────────────
var _selfconfigCurrentFile = null;
var _selfconfigRevisions = [];
var _selfconfigSelectedTs = null;   // null = "now" (live file)
var _selfconfigMode = 'preview';    // 'preview' | 'edit'
var _selfconfigOriginal = '';       // content loaded into editor (for dirty-check)

// One-line descriptions shown under each filename. Keep filenames as primary —
// users are technical enough to grok .md; descriptions are secondary hints.
var _CONFIG_FILE_META = {
  'USER.md':     { desc: 'What your agent knows about you.' },
  'SOUL.md':     { desc: 'How your agent talks, thinks and treats you.' },
  'AGENTS.md':   { desc: 'The rules your agent uses to make decisions.' },
  'TOOLS.md':    { desc: 'Commands and shortcuts your agent knows.' },
  'IDENTITY.md': { desc: 'Who your agent is \u2014 name, creature, vibe.' },
  'MEMORY.md':   { desc: 'Notes your agent keeps over time.' }
};

function _configMeta(filename) {
  return _CONFIG_FILE_META[filename] || { desc: '' };
}

// Escape HTML for safe injection of raw file content.
function _escapeHtml(s) {
  return (s || '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
                  .replace(/"/g, '&quot;').replace(/'/g, '&#39;');
}

// Render markdown to HTML if marked is available, otherwise escaped <pre>.
function _renderMarkdown(text) {
  if (typeof marked !== 'undefined' && marked.parse) {
    try { return marked.parse(text || ''); } catch (_) {}
  }
  return '<pre style="white-space:pre-wrap;font-family:inherit;margin:0;">' + _escapeHtml(text || '') + '</pre>';
}

// Tracked file metadata (for history + sensitive flag) — populated from
// /api/selfconfig. Keyed by filename (root-level only).
var _selfconfigTrackedMeta = {};

function _isTrackedFile(path) {
  return path && _selfconfigTrackedMeta.hasOwnProperty(path);
}

function _fileSizeStr(size) {
  if (size == null) return '';
  if (size < 1024) return size + ' B';
  if (size < 1024 * 1024) return (size / 1024).toFixed(1) + 'K';
  return (size / (1024 * 1024)).toFixed(1) + 'M';
}

function _fileIconSvg() {
  return '<svg width="13" height="13" viewBox="0 0 16 16" style="flex-shrink:0;margin-right:6px;opacity:0.65;" fill="none" stroke="currentColor" stroke-width="1.3"><path d="M3 1.5h7l3 3V14a.5.5 0 0 1-.5.5h-9A.5.5 0 0 1 3 14V1.5z"/><path d="M10 1.5V4.5h3"/></svg>';
}

function _folderIconSvg() {
  return '<svg width="13" height="13" viewBox="0 0 16 16" style="flex-shrink:0;margin-right:6px;opacity:0.7;" fill="none" stroke="currentColor" stroke-width="1.3"><path d="M1.5 3.5h4l1 1.5h8v8.5a.5.5 0 0 1-.5.5h-12A.5.5 0 0 1 1.5 13.5v-10z"/></svg>';
}

async function loadSelfConfig() {
  var inner = document.getElementById('selfconfig-files-inner');
  if (!inner) return;
  inner.innerHTML = '<span style="color:var(--text-muted);font-size:12px;padding:6px;">Loading\u2026</span>';
  try {
    // Fetch tracked-file metadata (for sensitive/history flags) and the
    // real filesystem listing in parallel.
    var filesReq = fetch('/api/memory-files').then(function(r){return r.json();}).catch(function(){return [];});
    var trackedReq = fetch('/api/selfconfig').then(function(r){return r.json();}).catch(function(){return {files:[]};});
    var results = await Promise.all([filesReq, trackedReq]);
    var realFiles = results[0] || [];
    var tracked = (results[1] && results[1].files) || [];

    _selfconfigTrackedMeta = {};
    tracked.forEach(function(t) { _selfconfigTrackedMeta[t.name] = t; });

    if (!realFiles.length) {
      inner.innerHTML = '<span style="color:var(--text-muted);font-size:12px;padding:6px;">No markdown files yet.</span>';
      return;
    }

    // Group: root files + folders (e.g. memory/2026-04-13.md).
    var roots = [];
    var folders = {};
    realFiles.forEach(function(f) {
      var parts = f.path.split('/');
      if (parts.length <= 1) {
        roots.push(f);
      } else {
        var dir = parts.slice(0, -1).join('/');
        if (!folders[dir]) folders[dir] = [];
        folders[dir].push(f);
      }
    });

    // Sort: tracked identity files first, then alphabetical.
    var trackedOrder = ['USER.md','SOUL.md','IDENTITY.md','AGENTS.md','TOOLS.md','HEARTBEAT.md','MEMORY.md'];
    roots.sort(function(a, b) {
      var ia = trackedOrder.indexOf(a.path);
      var ib = trackedOrder.indexOf(b.path);
      if (ia === -1) ia = 100;
      if (ib === -1) ib = 100;
      if (ia !== ib) return ia - ib;
      return a.path.localeCompare(b.path);
    });

    var html = '';
    roots.forEach(function(f) { html += _selfconfigFileRow(f.path, f.size, 0); });
    Object.keys(folders).sort().forEach(function(dir) {
      html += _selfconfigFolderRow(dir);
      folders[dir].sort(function(a, b) { return b.path.localeCompare(a.path); });  // newest first
      folders[dir].forEach(function(f) {
        var name = f.path.split('/').pop();
        html += _selfconfigFileRow(f.path, f.size, 1, name);
      });
    });
    inner.innerHTML = html;

    // Auto-open the first file if nothing is selected.
    if (!_selfconfigCurrentFile) {
      var first = roots[0] || (Object.values(folders)[0] || [])[0];
      if (first) selfconfigOpenFile(first.path);
    } else {
      selfconfigOpenFile(_selfconfigCurrentFile, _selfconfigSelectedTs);
    }
  } catch(e) {
    inner.innerHTML = '<span style="color:var(--text-muted);font-size:12px;padding:6px;">Couldn\u2019t load right now.</span>';
  }
}

function _selfconfigFileRow(path, size, depth, displayName) {
  var tracked = _selfconfigTrackedMeta[path];
  var sensitive = (tracked && tracked.is_values_file)
    ? ' <span title="Sensitive \u2014 changes here affect how your agent behaves." style="color:#fb923c;font-size:9px;margin-left:4px;vertical-align:middle;">&#9888;</span>'
    : '';
  var recentDot = '';
  var mtime = tracked ? tracked.last_modified_ts : 0;
  if (mtime) {
    var ageMin = (Date.now() / 1000 - mtime) / 60;
    if (ageMin < 1440) {
      recentDot = ' <span title="Changed in the last 24 hours" style="display:inline-block;width:6px;height:6px;border-radius:50%;background:#6366f1;vertical-align:middle;margin-left:5px;"></span>';
    }
  }
  var active = (path === _selfconfigCurrentFile);
  var activeStyle = active
    ? 'background:rgba(99,102,241,0.14);color:var(--text-primary);'
    : 'color:var(--text-secondary);';
  var indent = depth > 0 ? 'padding-left:' + (10 + depth * 14) + 'px;' : '';
  var name = displayName || path;
  return '<div data-filename="' + path + '" data-active="' + (active ? '1' : '') + '" onclick="selfconfigOpenFile(\'' + path + '\')" style="display:flex;align-items:center;cursor:pointer;padding:4px 10px;' + indent + 'margin:0;font-family:\'JetBrains Mono\',\'SF Mono\',monospace;font-size:12px;line-height:1.55;transition:background 0.1s;' + activeStyle + '" onmouseover="if(!this.dataset.active)this.style.background=\'var(--bg-hover)\'" onmouseout="if(!this.dataset.active)this.style.background=\'\'">'
    + _fileIconSvg()
    + '<span style="flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">' + name + '</span>'
    + sensitive
    + recentDot
    + '<span style="margin-left:8px;color:var(--text-muted);font-size:10.5px;flex-shrink:0;">' + _fileSizeStr(size) + '</span>'
    + '</div>';
}

function _selfconfigFolderRow(dir) {
  var name = dir.split('/').pop() || dir;
  return '<div style="display:flex;align-items:center;padding:4px 10px;margin:4px 0 0;font-family:\'JetBrains Mono\',\'SF Mono\',monospace;font-size:11px;line-height:1.55;color:var(--text-muted);text-transform:uppercase;letter-spacing:0.6px;">'
    + _folderIconSvg()
    + '<span>' + name + '</span>'
    + '</div>';
}

// Open a file in the reader. ``ts`` = null → show current live content.
async function selfconfigOpenFile(filename, ts) {
  _selfconfigCurrentFile = filename;
  window._selfconfigCurrentFile = filename;
  _selfconfigSelectedTs = (ts == null) ? null : ts;
  // Highlight the selected file in the list.
  document.querySelectorAll('#selfconfig-files-inner [data-filename]').forEach(function(el) {
    var match = el.getAttribute('data-filename') === filename;
    el.dataset.active = match ? '1' : '';
    el.style.background = match ? 'rgba(99,102,241,0.14)' : '';
  });
  // Only tracked (root-level identity) files get a revision timeline.
  if (_isTrackedFile(filename)) {
    _selfconfigRenderTimeline(filename);
  } else {
    var wrap = document.getElementById('selfconfig-timeline-wrap');
    if (wrap) wrap.style.display = 'none';
  }
  await _selfconfigRenderReader(filename, _selfconfigSelectedTs);
}

function selfconfigBackToNow() {
  if (_selfconfigCurrentFile) selfconfigOpenFile(_selfconfigCurrentFile, null);
}

// Populate the timeline of commits on the left-hand sidebar.
async function _selfconfigRenderTimeline(filename) {
  var wrap = document.getElementById('selfconfig-timeline-wrap');
  var list = document.getElementById('selfconfig-timeline');
  var heading = document.getElementById('selfconfig-timeline-heading');
  if (!wrap || !list) return;
  wrap.style.display = 'block';
  if (heading) heading.textContent = 'History \u00B7 ' + filename;
  list.innerHTML = '<span style="color:var(--text-muted);font-size:12px;padding:6px;">Loading...</span>';
  try {
    var d = await (typeof fetchJsonWithTimeout === 'function'
      ? fetchJsonWithTimeout('/api/selfconfig/' + encodeURIComponent(filename), 5000)
      : fetch('/api/selfconfig/' + encodeURIComponent(filename)).then(function(r){return r.json();}));
    _selfconfigRevisions = d.revisions || [];
    if (!_selfconfigRevisions.length) {
      list.innerHTML = '<div style="color:var(--text-muted);font-size:12px;padding:8px 6px;">No changes yet. When your agent updates this, it\u2019ll show up here.</div>';
      return;
    }
    // Pre-fetch summaries for each adjacent pair in the background (non-blocking).
    _selfconfigRevisions.forEach(function(rev, idx) {
      if (idx < _selfconfigRevisions.length - 1 && !rev._summary) {
        var prevTs = _selfconfigRevisions[idx + 1].ts;
        fetch('/api/selfconfig/' + encodeURIComponent(filename) + '/diff?from=' + prevTs + '&to=' + rev.ts)
          .then(function(r){return r.json();})
          .then(function(dd){
            rev._summary = dd.summary || '';
            rev._addedLines = dd.added_lines || 0;
            rev._removedLines = dd.removed_lines || 0;
            _renderTimelineRows(filename);
          }).catch(function(){});
      }
    });
    _renderTimelineRows(filename);
  } catch(e) {
    list.innerHTML = '<span style="color:var(--text-muted);font-size:12px;padding:6px;">Couldn\u2019t load.</span>';
  }
}

function _renderTimelineRows(filename) {
  var list = document.getElementById('selfconfig-timeline');
  if (!list) return;
  var rows = [];
  // "Now" entry at top.
  var nowActive = _selfconfigSelectedTs == null;
  rows.push(_selfconfigRowHtml(filename, null, {
    label: 'Now',
    sub: 'Current version',
    active: nowActive
  }));
  // One row per revision, newest first.
  _selfconfigRevisions.forEach(function(rev, idx) {
    var isFirst = idx === _selfconfigRevisions.length - 1;
    var when = _friendlyTimestamp(rev.ts);
    var summary;
    if (isFirst) {
      summary = 'Created';
    } else if (rev._summary) {
      summary = rev._summary;
    } else {
      summary = 'Updated';
    }
    var lineDelta = '';
    if (rev._addedLines != null || rev._removedLines != null) {
      var a = rev._addedLines || 0;
      var r = rev._removedLines || 0;
      var parts = [];
      if (a) parts.push('<span style="color:#22c55e;">+' + a + '</span>');
      if (r) parts.push('<span style="color:#ef4444;">\u2212' + r + '</span>');
      if (parts.length) lineDelta = ' &nbsp;\u00B7&nbsp; ' + parts.join(' ');
    }
    rows.push(_selfconfigRowHtml(filename, rev.ts, {
      label: when,
      sub: summary + lineDelta,
      active: _selfconfigSelectedTs === rev.ts
    }));
  });
  list.innerHTML = rows.join('');
}

function _selfconfigRowHtml(filename, ts, opts) {
  var dotColor = ts == null ? '#22c55e' : '#64748b';
  var activeBg = opts.active ? 'background:rgba(99,102,241,0.12);' : '';
  var tsArg = ts == null ? 'null' : ts;
  return '<div onclick="selfconfigOpenFile(\'' + filename + '\',' + tsArg + ')" style="cursor:pointer;position:relative;padding:5px 10px 5px 22px;border-radius:3px;margin:0;transition:background 0.1s;' + activeBg + '" ' + (opts.active ? 'data-active="1"' : '') + ' onmouseover="if(!this.dataset.active)this.style.background=\'var(--bg-hover)\'" onmouseout="if(!this.dataset.active)this.style.background=\'\'">'
    + '<span style="position:absolute;left:8px;top:9px;width:6px;height:6px;border-radius:50%;background:' + dotColor + ';"></span>'
    + '<div style="font-size:11px;font-weight:600;color:var(--text-primary);line-height:1.4;">' + opts.label + '</div>'
    + '<div style="font-size:10.5px;color:var(--text-muted);margin-top:1px;line-height:1.35;">' + opts.sub + '</div>'
    + '</div>';
}

// Populate the reader pane — shows the file content at the requested version.
async function _selfconfigRenderReader(filename, ts) {
  var titleEl = document.getElementById('selfconfig-reader-title');
  var badgeEl = document.getElementById('selfconfig-reader-badge');
  var bodyEl = document.getElementById('selfconfig-reader-body');
  var editorBody = document.getElementById('selfconfig-editor-body');
  var editorToolbar = document.getElementById('selfconfig-editor-toolbar');
  var bannerEl = document.getElementById('selfconfig-reader-banner');
  var bannerText = document.getElementById('selfconfig-reader-banner-text');

  var tracked = _isTrackedFile(filename);
  var meta = tracked ? _selfconfigTrackedMeta[filename] : null;

  if (titleEl) titleEl.textContent = filename;
  if (badgeEl) badgeEl.style.display = (meta && meta.is_values_file) ? 'inline-block' : 'none';
  if (bodyEl) bodyEl.innerHTML = '<div style="color:var(--text-muted);font-size:13px;padding:0;">Loading\u2026</div>';

  // Edit toolbar is available for live files (any, tracked or not). Past
  // versions are only reachable for tracked files — they remain read-only.
  if (editorToolbar) editorToolbar.style.display = (ts == null) ? 'flex' : 'none';

  if (bannerEl) {
    if (ts == null) {
      bannerEl.style.display = 'none';
    } else {
      bannerEl.style.display = 'flex';
      if (bannerText) bannerText.textContent = 'Viewing the version from ' + _friendlyTimestamp(ts);
    }
  }

  _selfconfigMode = 'preview';
  _selfconfigUpdateModeButtons();
  if (bodyEl) bodyEl.style.display = 'block';
  if (editorBody) editorBody.style.display = 'none';

  _selfconfigUpdateStatusBar(filename, ts, null);

  try {
    var url, d;
    if (tracked) {
      url = '/api/selfconfig/' + encodeURIComponent(filename) + '/content' + (ts == null ? '' : '?ts=' + ts);
      d = await fetch(url).then(function(r){return r.json();});
      _selfconfigOriginal = d.content || '';
    } else {
      // Untracked file (e.g. memory/2026-04-13.md) — use /api/file.
      url = '/api/file?path=' + encodeURIComponent(filename);
      d = await fetch(url).then(function(r){return r.json();});
      if (d.error) throw new Error(d.error);
      _selfconfigOriginal = d.content || '';
      d.exists = true;
      d.ts = d.mtime;
    }
    if (bodyEl) {
      if (!d.exists && ts == null) {
        bodyEl.innerHTML = '<div style="color:var(--text-muted);font-size:13px;padding:0;">This file hasn\u2019t been created yet. Click <strong>Edit</strong> above to write the first version.</div>';
      } else if (!d.content || !d.content.trim()) {
        bodyEl.innerHTML = '<div style="color:var(--text-muted);font-size:13px;padding:0;">This file is empty.</div>';
      } else {
        bodyEl.innerHTML = '<div class="mem-prose">' + _renderMarkdown(d.content) + '</div>';
      }
    }
    _selfconfigUpdateStatusBar(filename, ts, d);
  } catch(e) {
    if (bodyEl) bodyEl.innerHTML = '<div style="color:var(--text-muted);font-size:13px;padding:0;">Couldn\u2019t load this version.</div>';
  }
}

function _selfconfigUpdateStatusBar(filename, ts, d) {
  var fileEl = document.getElementById('selfconfig-status-file');
  var modeEl = document.getElementById('selfconfig-status-mode');
  var sizeEl = document.getElementById('selfconfig-status-size');
  var updatedEl = document.getElementById('selfconfig-status-updated');
  if (fileEl) fileEl.textContent = filename || '—';
  if (modeEl) modeEl.textContent = (_selfconfigSelectedTs == null)
    ? (_selfconfigMode === 'edit' ? 'Editing' : 'Preview')
    : 'History';
  if (sizeEl) {
    var src = d && typeof d.content === 'string' ? d.content : (_selfconfigOriginal || '');
    var lines = src ? src.split('\n').length : 0;
    var bytes = src ? new Blob([src]).size : 0;
    sizeEl.textContent = lines + ' line' + (lines === 1 ? '' : 's') + ' \u00B7 ' + _friendlyBytes(bytes);
  }
  if (updatedEl) {
    if (ts != null) updatedEl.textContent = 'Viewing ' + _friendlyTimestamp(ts);
    else if (d && d.ts) updatedEl.textContent = 'Updated ' + _friendlyTimestamp(d.ts);
    else updatedEl.textContent = '';
  }
}

// ── Editor controls ──────────────────────────────────────────────────────────

function _selfconfigUpdateModeButtons() {
  document.querySelectorAll('.sc-mode-btn').forEach(function(btn) {
    var active = btn.getAttribute('data-mode') === _selfconfigMode;
    btn.style.background = active ? 'var(--bg-primary)' : 'transparent';
    btn.style.border = active ? '1px solid var(--border-primary)' : '1px solid transparent';
    btn.style.color = active ? 'var(--text-primary)' : 'var(--text-muted)';
  });
}

function selfconfigSetMode(mode) {
  if (_selfconfigSelectedTs != null && mode === 'edit') return;  // read-only for past versions
  _selfconfigMode = mode;
  _selfconfigUpdateModeButtons();
  var bodyEl = document.getElementById('selfconfig-reader-body');
  var editorBody = document.getElementById('selfconfig-editor-body');
  var textarea = document.getElementById('selfconfig-editor-textarea');
  if (mode === 'edit') {
    if (bodyEl) bodyEl.style.display = 'none';
    if (editorBody) editorBody.style.display = 'flex';
    if (textarea) {
      textarea.value = _selfconfigOriginal || '';
      _selfconfigRenderLineNumbers();
      setTimeout(function(){ textarea.focus(); }, 30);
    }
  } else {
    if (bodyEl) bodyEl.style.display = 'block';
    if (editorBody) editorBody.style.display = 'none';
  }
  _selfconfigUpdateStatusBar(_selfconfigCurrentFile, _selfconfigSelectedTs, null);
}

function _selfconfigRenderLineNumbers() {
  var textarea = document.getElementById('selfconfig-editor-textarea');
  var gutter = document.getElementById('selfconfig-editor-gutter');
  if (!textarea || !gutter) return;
  var count = (textarea.value || '').split('\n').length;
  var nums = new Array(count);
  for (var i = 0; i < count; i++) nums[i] = (i + 1);
  gutter.textContent = nums.join('\n');
  gutter.scrollTop = textarea.scrollTop;
}

function selfconfigOnEditorInput() {
  _selfconfigRenderLineNumbers();
  _selfconfigUpdateStatusBar(_selfconfigCurrentFile, null, null);
}

function selfconfigSyncGutterScroll() {
  var textarea = document.getElementById('selfconfig-editor-textarea');
  var gutter = document.getElementById('selfconfig-editor-gutter');
  if (textarea && gutter) gutter.scrollTop = textarea.scrollTop;
}

function selfconfigDiscardEdit() {
  var textarea = document.getElementById('selfconfig-editor-textarea');
  if (textarea && textarea.value !== _selfconfigOriginal) {
    if (!confirm('Discard unsaved changes?')) return;
  }
  selfconfigSetMode('preview');
}

async function selfconfigSave() {
  var textarea = document.getElementById('selfconfig-editor-textarea');
  var btn = document.getElementById('selfconfig-save-btn');
  if (!textarea || !_selfconfigCurrentFile) return;
  var newContent = textarea.value;
  if (btn) { btn.disabled = true; btn.textContent = 'Saving\u2026'; btn.style.opacity = '0.6'; }
  var tracked = _isTrackedFile(_selfconfigCurrentFile);
  try {
    var r;
    if (tracked) {
      r = await fetch('/api/selfconfig/' + encodeURIComponent(_selfconfigCurrentFile) + '/content', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ content: newContent })
      });
    } else {
      r = await fetch('/api/file', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ path: _selfconfigCurrentFile, content: newContent })
      });
    }
    if (!r.ok) {
      var err = await r.json().catch(function(){ return {}; });
      throw new Error(err.error || ('HTTP ' + r.status));
    }
    _selfconfigOriginal = newContent;
    if (tracked) {
      await _selfconfigRenderTimeline(_selfconfigCurrentFile);
    }
    loadSelfConfig();
    selfconfigSetMode('preview');
  } catch(e) {
    alert('Save failed: ' + (e.message || e));
  } finally {
    if (btn) { btn.disabled = false; btn.textContent = 'Save'; btn.style.opacity = '1'; }
  }
}

async function selfconfigRestoreVersion() {
  if (_selfconfigSelectedTs == null || !_selfconfigCurrentFile) return;
  if (!confirm('Restore this version? The current content will be replaced (but saved as a new version in history).')) return;
  try {
    // Fetch the historical version's content, then save it as the live file.
    var url = '/api/selfconfig/' + encodeURIComponent(_selfconfigCurrentFile) + '/content?ts=' + _selfconfigSelectedTs;
    var d = await fetch(url).then(function(r){return r.json();});
    var content = d.content || '';
    var r = await fetch('/api/selfconfig/' + encodeURIComponent(_selfconfigCurrentFile) + '/content', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ content: content })
    });
    if (!r.ok) throw new Error('Save failed');
    // Return to "now" with the restored content.
    await selfconfigOpenFile(_selfconfigCurrentFile, null);
    loadSelfConfig();
  } catch(e) {
    alert('Couldn\u2019t restore: ' + (e.message || e));
  }
}

// Kept as public shims so older buttons/links still resolve.
async function loadSelfConfigHistory(filename) { return selfconfigOpenFile(filename, null); }
async function loadSelfConfigDiff(filename, fromTs, toTs) { return selfconfigOpenFile(filename, toTs); }
function selfconfigBackToRevisions() { selfconfigBackToNow(); }

// ── Skills: shortcuts your agent can use ─────────────────────────────────────
var _skillsShowDetails = false;

function _skillStatusPill(status) {
  var map = {
    healthy: { label: 'Working',          color: '#22c55e' },
    unused:  { label: 'Never used',       color: '#94a3b8' },
    dead:    { label: 'Safe to remove',   color: '#ef4444' },
    stuck:   { label: 'Not working',      color: '#f59e0b' }
  };
  var s = map[status] || { label: status || '\u2014', color: '#94a3b8' };
  return '<span style="background:' + s.color + '22;color:' + s.color + ';border:1px solid ' + s.color + '44;border-radius:10px;padding:2px 10px;font-size:11px;font-weight:600;">' + s.label + '</span>';
}

async function loadSkills() {
  var summaryEl = document.getElementById('skills-summary-row');
  var listEl = document.getElementById('skills-list');
  if (!summaryEl || !listEl) return;
  listEl.innerHTML = '<div style="color:var(--text-muted);font-size:13px;padding:16px;">Loading...</div>';
  try {
    var data = await fetch('/api/skills').then(function(r) { return r.json(); });
    var skills = data.skills || [];
    var summary = data.summary || {};
    var installed = summary.total_installed || 0;
    var dead = summary.dead_count || 0;
    var stuck = summary.stuck_count || 0;

    function card(title, value, color, sub) {
      return '<div style="background:var(--bg-secondary);border:1px solid var(--border-primary);border-radius:8px;padding:12px 18px;min-width:140px;">'
        + '<div style="font-size:22px;font-weight:700;color:' + (color || 'var(--text-primary)') + ';line-height:1.1;">' + value + '</div>'
        + '<div style="font-size:11px;color:var(--text-muted);margin-top:4px;text-transform:uppercase;letter-spacing:1px;">' + title + '</div>'
        + (sub ? '<div style="font-size:11px;color:var(--text-muted);margin-top:4px;">' + sub + '</div>' : '')
        + '</div>';
    }

    summaryEl.innerHTML =
      card('Installed', installed, 'var(--text-primary)') +
      (dead   > 0 ? card('Safe to remove', dead,  '#ef4444', 'never used') : '') +
      (stuck  > 0 ? card('Not working',    stuck, '#f59e0b', 'broken or misdescribed') : '') +
      (dead === 0 && stuck === 0 && installed > 0
        ? card('All good', '\u2713', '#22c55e', 'every skill is being used')
        : '');

    if (skills.length === 0) {
      listEl.innerHTML = '<div style="color:var(--text-muted);font-size:13px;padding:16px;">Nothing installed yet. Skills let your agent handle specific tasks \u2014 add some to get started.</div>';
      return;
    }

    // Sort: problematic first (dead, stuck), then unused, then healthy.
    // Use `in` not `||` — `order['dead']` is 0 which is falsy, the `||`
    // variant accidentally sent 'dead' to the end of the list.
    var order = { dead: 0, stuck: 1, unused: 2, healthy: 3 };
    skills.sort(function(a, b) {
      var oa = a.status in order ? order[a.status] : 99;
      var ob = b.status in order ? order[b.status] : 99;
      return oa - ob;
    });

    var toggleBtn = '<div style="text-align:right;margin-bottom:8px;">'
      + '<button onclick="_skillsShowDetails=!_skillsShowDetails;loadSkills();" style="background:var(--bg-primary);border:1px solid var(--border-primary);border-radius:6px;padding:4px 10px;font-size:11px;cursor:pointer;color:var(--text-secondary);">'
      + (_skillsShowDetails ? 'Hide details' : 'Show details') + '</button></div>';

    var html = toggleBtn + '<table style="width:100%;border-collapse:collapse;font-size:13px;">' +
      '<thead><tr style="color:var(--text-muted);text-align:left;border-bottom:1px solid var(--border-primary);font-size:11px;text-transform:uppercase;letter-spacing:1px;">' +
        '<th style="padding:10px 10px;">Skill</th>' +
        '<th style="padding:10px 10px;">What it does</th>' +
        '<th style="padding:10px 10px;">Status</th>' +
        '<th style="padding:10px 10px;">Last used</th>' +
        (_skillsShowDetails
          ? '<th style="padding:10px 10px;text-align:right;" title="Tokens always loaded into the agent\'s context">Always loaded</th>'
            + '<th style="padding:10px 10px;text-align:right;" title="Times the agent decided to look at this skill in the last 7 days">Used (7d)</th>'
          : '') +
      '</tr></thead><tbody>';

    skills.forEach(function(sk, idx) {
      var desc = (sk.description || '').length > 80 ? sk.description.slice(0, 77) + '...' : (sk.description || '\u2014');
      var lastUsed = sk.last_used_ts
        ? _friendlyAgo(Math.floor(Date.now() / 1000) - sk.last_used_ts)
        : (sk.status === 'dead' || sk.status === 'unused' ? '\u2014' : 'recently');
      var rowBg = idx % 2 === 0 ? 'var(--bg-primary)' : 'var(--bg-secondary)';
      html += '<tr style="background:' + rowBg + ';border-bottom:1px solid var(--border-primary);">' +
        '<td style="padding:10px 10px;font-weight:600;color:var(--text-primary);"><a href="#" onclick="event.preventDefault();openSkillBrowser(\'' + escHtml(sk.name) + '\')" style="color:var(--text-primary);text-decoration:none;border-bottom:1px dashed var(--border-primary);" title="Browse skill files">' + escHtml(sk.name) + '</a></td>' +
        '<td style="padding:10px 10px;color:var(--text-muted);">' + escHtml(desc) + '</td>' +
        '<td style="padding:10px 10px;">' + _skillStatusPill(sk.status) + '</td>' +
        '<td style="padding:10px 10px;color:var(--text-muted);">' + lastUsed + '</td>' +
        (_skillsShowDetails
          ? '<td style="padding:10px 10px;text-align:right;color:var(--text-muted);">' + (sk.header_tokens || 0).toLocaleString() + ' tokens</td>'
            + '<td style="padding:10px 10px;text-align:right;color:var(--text-muted);">' + ((sk.body_fetch_count_7d || 0) + (sk.linked_file_read_count_7d || 0)) + ' times</td>'
          : '') +
        '</tr>';
    });
    html += '</tbody></table>';
    listEl.innerHTML = html;
  } catch (e) {
    if (listEl) listEl.innerHTML = '<div style="color:var(--text-muted);font-size:13px;padding:16px;">Couldn\u2019t load right now.</div>';
  }
}

// ── Skills Browser ────────────────────────────────────────────────────────
async function openSkillBrowser(skillName) {
  var listEl = document.getElementById('skills-list');
  var browserEl = document.getElementById('skills-browser');
  var treeEl = document.getElementById('skills-browser-tree');
  var contentEl = document.getElementById('skills-browser-content');
  if (!browserEl || !treeEl || !contentEl) return;

  listEl.style.display = 'none';
  browserEl.style.display = '';
  treeEl.innerHTML = '<div style="padding:12px;color:var(--text-muted);">Loading...</div>';
  contentEl.innerHTML = '<div style="color:var(--text-muted);text-align:center;padding:60px;">Loading skill...</div>';

  try {
    var data = await fetch('/api/skills/' + encodeURIComponent(skillName)).then(function(r) { return r.json(); });
    var files = data.files || [];
    var statusCol = {'healthy':'#22c55e','dead':'#ef4444','stuck':'#f59e0b','unused':'#6b7280'};

    // Build tree
    var html = '<div style="padding:8px 12px;border-bottom:1px solid var(--border);margin-bottom:4px;">';
    html += '<div style="font-weight:700;font-size:13px;color:var(--text-primary);">' + escHtml(skillName) + '</div>';
    html += '<div style="font-size:10px;color:' + (statusCol[data.status] || '#888') + ';margin-top:2px;">' + (data.status || '').toUpperCase() + ' &middot; ' + (data.header_tokens || 0) + ' header tokens</div>';
    if (data.description) html += '<div style="font-size:10px;color:var(--text-muted);margin-top:2px;">' + escHtml(data.description) + '</div>';
    html += '</div>';

    files.forEach(function(f) {
      var indent = (f.depth || 0) * 16;
      var isDir = f.path.endsWith('/');
      var icon = f.path.endsWith('.md') ? '📄' : (f.path.endsWith('.py') ? '🐍' : (f.path.endsWith('.sh') ? '📜' : (f.path.endsWith('.js') || f.path.endsWith('.ts') ? '📦' : '📄')));
      var sizeStr = f.size > 1024 ? (f.size / 1024).toFixed(1) + 'K' : f.size + 'B';
      html += '<div onclick="loadSkillFile(\'' + escHtml(skillName) + '\',\'' + escHtml(f.path) + '\')" style="padding:4px 12px 4px ' + (12 + indent) + 'px;cursor:pointer;display:flex;align-items:center;gap:6px;font-size:12px;" onmouseover="this.style.background=\'var(--bg-hover)\'" onmouseout="this.style.background=\'\'">';
      html += '<span>' + icon + '</span>';
      html += '<span style="color:var(--text-primary);flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">' + escHtml(f.path.split('/').pop()) + '</span>';
      html += '<span style="color:var(--text-faint);font-size:10px;">' + sizeStr + '</span>';
      html += '</div>';
    });
    treeEl.innerHTML = html;

    // Auto-load SKILL.md
    loadSkillFile(skillName, 'SKILL.md');
  } catch(e) {
    treeEl.innerHTML = '<div style="padding:12px;color:var(--text-error);">Error: ' + escHtml(String(e)) + '</div>';
  }
}

async function loadSkillFile(skillName, filePath) {
  var contentEl = document.getElementById('skills-browser-content');
  if (!contentEl) return;
  contentEl.innerHTML = '<div style="color:var(--text-muted);padding:20px;">Loading...</div>';

  try {
    var data = await fetch('/api/skills/' + encodeURIComponent(skillName) + '/file?path=' + encodeURIComponent(filePath)).then(function(r) { return r.json(); });
    if (data.error) { contentEl.innerHTML = '<div style="color:var(--text-error);padding:20px;">' + escHtml(data.error) + '</div>'; return; }

    var header = '<div style="display:flex;align-items:center;justify-content:space-between;border-bottom:1px solid var(--border);padding-bottom:8px;margin-bottom:12px;">';
    header += '<div style="font-size:13px;font-weight:600;color:var(--text-primary);">' + escHtml(filePath) + '</div>';
    header += '<div style="font-size:11px;color:var(--text-muted);">' + escHtml(skillName) + ' &middot; ' + (data.language || 'text') + ' &middot; ' + data.size + ' bytes</div>';
    header += '</div>';

    var content = data.content || '';
    if (data.language === 'markdown') {
      // Simple markdown rendering
      content = content.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
      content = content.replace(/^### (.+)$/gm, '<h3 style="margin:16px 0 8px;font-size:14px;color:var(--text-primary);">$1</h3>');
      content = content.replace(/^## (.+)$/gm, '<h2 style="margin:20px 0 8px;font-size:16px;color:var(--text-primary);">$1</h2>');
      content = content.replace(/^# (.+)$/gm, '<h1 style="margin:20px 0 8px;font-size:18px;color:var(--text-primary);">$1</h1>');
      content = content.replace(/`([^`]+)`/g, '<code style="background:var(--bg-secondary);padding:1px 5px;border-radius:3px;font-size:12px;">$1</code>');
      content = content.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
      content = content.replace(/^- (.+)$/gm, '<div style="padding-left:16px;">&bull; $1</div>');
      content = content.replace(/^---$/gm, '<hr style="border:none;border-top:1px solid var(--border);margin:12px 0;">');
      content = '<div style="font-size:13px;line-height:1.7;color:var(--text-secondary);">' + content + '</div>';
    } else {
      content = '<pre style="background:var(--bg-secondary);border:1px solid var(--border);border-radius:6px;padding:12px 16px;font-size:12px;line-height:1.6;overflow-x:auto;color:var(--text-primary);white-space:pre-wrap;">' + escHtml(content) + '</pre>';
    }

    contentEl.innerHTML = header + content;
  } catch(e) {
    contentEl.innerHTML = '<div style="color:var(--text-error);padding:20px;">Error: ' + escHtml(String(e)) + '</div>';
  }
}

var _sunSVG = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="5"/><line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/><line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/></svg>';
var _moonSVG = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>';

function toggleTheme() {
  const body = document.body;
  const toggle = document.getElementById('theme-toggle-btn');
  const isLight = !body.hasAttribute('data-theme') || body.getAttribute('data-theme') !== 'dark';
  
  if (isLight) {
    body.setAttribute('data-theme', 'dark');
    toggle.innerHTML = _sunSVG;
    toggle.title = 'Switch to light theme';
    localStorage.setItem('openclaw-theme', 'dark');
  } else {
    body.removeAttribute('data-theme');
    toggle.innerHTML = _moonSVG;
    toggle.title = 'Switch to dark theme';
    localStorage.setItem('openclaw-theme', 'light');
  }
}

function initTheme() {
  const savedTheme = localStorage.getItem('openclaw-theme') || 'light';
  const body = document.body;
  const toggle = document.getElementById('theme-toggle-btn');
  
  if (savedTheme === 'dark') {
    body.setAttribute('data-theme', 'dark');
    if (toggle) { toggle.innerHTML = _sunSVG; toggle.title = 'Switch to light theme'; }
  } else {
    body.removeAttribute('data-theme');
    if (toggle) { toggle.innerHTML = _moonSVG; toggle.title = 'Switch to dark theme'; }
  }
}

// === Zoom Controls ===
let currentZoom = 1.0;
const MIN_ZOOM = 0.5;
const MAX_ZOOM = 2.0;
const ZOOM_STEP = 0.1;

function initZoom() {
  const savedZoom = localStorage.getItem('openclaw-zoom');
  if (savedZoom) {
    currentZoom = parseFloat(savedZoom);
  }
  applyZoom();
}

function applyZoom() {
  const wrapper = document.getElementById('zoom-wrapper');
  const levelDisplay = document.getElementById('zoom-level');
  
  if (wrapper) {
    wrapper.style.transform = `scale(${currentZoom})`;
  }
  if (levelDisplay) {
    levelDisplay.textContent = Math.round(currentZoom * 100) + '%';
  }
  
  // Save to localStorage
  localStorage.setItem('openclaw-zoom', currentZoom.toString());
}

function zoomIn() {
  if (currentZoom < MAX_ZOOM) {
    currentZoom = Math.min(MAX_ZOOM, currentZoom + ZOOM_STEP);
    applyZoom();
  }
}

function zoomOut() {
  if (currentZoom > MIN_ZOOM) {
    currentZoom = Math.max(MIN_ZOOM, currentZoom - ZOOM_STEP);
    applyZoom();
  }
}

function resetZoom() {
  currentZoom = 1.0;
  applyZoom();
}

// Keyboard shortcuts for zoom
document.addEventListener('keydown', function(e) {
  if ((e.ctrlKey || e.metaKey) && !e.shiftKey && !e.altKey) {
    if (e.key === '=' || e.key === '+') {
      e.preventDefault();
      zoomIn();
    } else if (e.key === '-') {
      e.preventDefault();
      zoomOut();
    } else if (e.key === '0') {
      e.preventDefault();
      resetZoom();
    }
  }
});

function timeAgo(ms) {
  if (!ms) return 'never';
  var diff = Date.now() - ms;
  if (diff < 60000) return Math.floor(diff/1000) + 's ago';
  if (diff < 3600000) return Math.floor(diff/60000) + 'm ago';
  if (diff < 86400000) return Math.floor(diff/3600000) + 'h ago';
  return Math.floor(diff/86400000) + 'd ago';
}

function formatTime(ms) {
  if (!ms) return '--';
  return new Date(ms).toLocaleString('en-GB', {hour:'2-digit',minute:'2-digit',day:'numeric',month:'short'});
}

async function fetchJsonWithTimeout(url, timeoutMs) {
  var ctrl = new AbortController();
  var to = setTimeout(function() { ctrl.abort('timeout'); }, timeoutMs);
  try {
    var r = await fetch(url, {signal: ctrl.signal});
    if (!r.ok) throw new Error('HTTP ' + r.status);
    return await r.json();
  } finally {
    clearTimeout(to);
  }
}

async function resolvePrimaryModelFallback() {
  try {
    var data = await fetchJsonWithTimeout('/api/component/brain?limit=25', 4000);
    var model = (((data || {}).stats || {}).model || '').trim();
    return model || 'unknown';
  } catch (e) {
    return 'unknown';
  }
}

function applyBrainModelToAll(modelName) {
  if (!modelName) return;
  var modelText = fitFlowLabel(modelName, 20);
  document.querySelectorAll('[id$="brain-model-text"]').forEach(function(el) {
    el.textContent = modelText;
  });
  document.querySelectorAll('[id$="brain-model-label"]').forEach(function(label) {
    var short = modelName.split('/').pop().split('-').slice(0, 2).join(' ');
    if (!short) short = 'AI Model';
    label.textContent = fitFlowLabel(short.charAt(0).toUpperCase() + short.slice(1), 14);
  });
}

function fitFlowLabel(text, maxLen) {
  var s = String(text || '').trim();
  if (!s) return '';
  if (s.length <= maxLen) return s;
  return s.substring(0, Math.max(1, maxLen - 1)) + '…';
}

function applyBillingHintToFlow(billingSummary) {
  var hint = 'Auth: ?';
  if (billingSummary === 'likely_api_key') hint = 'Auth: API';
  else if (billingSummary === 'likely_oauth_or_included') hint = 'Auth: OAuth';
  else if (billingSummary === 'mixed') hint = 'Auth: mixed';

  document.querySelectorAll('[id$="brain-billing-text"]').forEach(function(el) {
    el.textContent = fitFlowLabel(hint, 14);
  });
}

function setFlowTextAll(idSuffix, text, maxLen) {
  var fitted = fitFlowLabel(text, maxLen);
  document.querySelectorAll('[id$="' + idSuffix + '"]').forEach(function(el) {
    el.textContent = fitted;
  });
}

async function loadAll() {
  try {
    // Render overview quickly; do not block on heavy usage aggregation.
    var overview = await fetchJsonWithTimeout('/api/overview', 3000);

    // Start secondary panels immediately.
    startActiveTasksRefresh();
    loadActivityStream().catch(function(e){console.warn('activity stream failed',e)});
    loadHealth().catch(function(e){console.warn('health failed',e)});
    loadMCTasks().catch(function(e){console.warn('mctasks failed',e)});
    if (typeof loadReliabilityCard === 'function') loadReliabilityCard().catch(function(e){console.warn('reliability card failed',e)});
    if (typeof loadAnomalyPanel === 'function') loadAnomalyPanel().catch(function(e){console.warn('anomaly panel failed',e)});
    if (typeof loadTokenVelocity === 'function') loadTokenVelocity().catch(function(e){console.warn('velocity check failed',e)});
    if (typeof loadDiagnostics === 'function') loadDiagnostics().catch(function(e){console.warn('diagnostics failed',e)});
    if (typeof loadAutonomy === 'function') loadAutonomy().catch(function(e){console.warn('autonomy failed',e)});
    if (typeof loadHeartbeat === 'function') loadHeartbeat().catch(function(e){console.warn('heartbeat panel failed',e)});
    document.getElementById('refresh-time').textContent = 'Updated ' + new Date().toLocaleTimeString();

    if (overview.infra) {
      var i = overview.infra;
      if (i.runtime) setFlowTextAll('infra-runtime-text', i.runtime, 18);
      if (i.machine) setFlowTextAll('infra-machine-text', i.machine, 18);
      if (i.storage) setFlowTextAll('infra-storage-text', i.storage, 16);
      if (i.network) setFlowTextAll('infra-network-text', 'LAN ' + i.network, 18);
      if (i.userName) setFlowTextAll('flow-human-name', i.userName, 10);
    }

    // If overview cannot determine model yet, use brain endpoint fallback immediately.
    if (!overview.model || overview.model === 'unknown') {
      var fallbackModel = await resolvePrimaryModelFallback();
      if (fallbackModel && fallbackModel !== 'unknown') {
        overview.model = fallbackModel;
      }
    }
    if (overview.model && overview.model !== 'unknown') {
      applyBrainModelToAll(overview.model);
    }

    // Usage may be slow on first run; keep trying in background with timeout.
    try {
      var usage = await fetchJsonWithTimeout('/api/usage', 5000);
      loadMiniWidgets(overview, usage);
    } catch (e) {
      // Keep UI responsive with placeholder values until next refresh.
      loadMiniWidgets(overview, {todayCost:0, weekCost:0, monthCost:0, month:0, today:0});
    }
    return true;
  } catch (e) {
    console.error('Initial load failed', e);
    document.getElementById('refresh-time').textContent = 'Load failed - retrying...';
    return false;
  }
}

async function loadMiniWidgets(overview, usage) {
  // 💰 Cost Ticker 
  function fmtCost(c) { return c >= 0.01 ? '$' + c.toFixed(2) : c > 0 ? '<$0.01' : '$0.00'; }
  document.getElementById('cost-today').textContent = fmtCost(usage.todayCost || 0);
  document.getElementById('cost-week').textContent = fmtCost(usage.weekCost || 0);
  document.getElementById('cost-month').textContent = fmtCost(usage.monthCost || 0);
  
  var trend = '';
  if (usage.trend && usage.trend.trend) {
    var trendIcon = usage.trend.trend === 'increasing' ? '📈' : usage.trend.trend === 'decreasing' ? '📉' : '➡️';
    trend = trendIcon + ' ' + usage.trend.trend;
  }
  var isOauthLikely = (usage.billingSummary === 'likely_oauth_or_included');
  var isMixed = (usage.billingSummary === 'mixed');
  var trendEl = document.getElementById('cost-trend');
  var badgeEl = document.getElementById('cost-billing-badge');
  var infoIcon = document.getElementById('cost-info-icon');

  if (isOauthLikely) {
    if (badgeEl) {
      badgeEl.style.display = '';
      badgeEl.textContent = 'est. equivalent if billed - OAuth likely';
    }
    trendEl.style.display = 'none';
  } else {
    if (badgeEl) {
      badgeEl.style.display = 'none';
      badgeEl.textContent = '';
    }
    trendEl.textContent = trend || 'Today\'s running total';
    trendEl.style.display = trend ? '' : 'none';
  }

  if (infoIcon) {
    if (isOauthLikely || isMixed) {
      infoIcon.style.display = '';
      infoIcon.title = 'Equivalent if billed from token usage. OAuth/included models may be billed $0 at provider level.';
    } else {
      infoIcon.style.display = 'none';
      infoIcon.title = '';
    }
  }

  applyBillingHintToFlow(usage.billingSummary || 'unknown');
  
  // ⚡ Tool Activity (load from logs)
  loadToolActivity();
  
  // 📊 Token Burn Rate
  function fmtTokens(n) { return n >= 1000000 ? (n/1000000).toFixed(1) + 'M' : n >= 1000 ? (n/1000).toFixed(0) + 'K' : String(n); }
  document.getElementById('token-rate').textContent = fmtTokens(usage.month || 0);
  document.getElementById('tokens-today').textContent = fmtTokens(usage.today || 0);
  
  // 🔥 Hot Sessions -- use /api/sessions for consistency with modal
  fetch('/api/sessions').then(function(r){return r.json()}).then(function(sd) {
    var sl = sd.sessions || sd || [];
    if (!Array.isArray(sl)) sl = [];
    document.getElementById('hot-sessions-count').textContent = sl.length;
  }).catch(function() {
    document.getElementById('hot-sessions-count').textContent = overview.sessionCount || 0;
  });
  
  // 📈 Model Mix
  document.getElementById('model-primary').textContent = overview.model || 'unknown';
  var modelLabel = document.getElementById('main-activity-model');
  if (modelLabel && overview.model) {
    var m = overview.model;
    if (m.indexOf('/') !== -1) m = m.split('/').pop();
    m = m.replace(/-/g, ' ').replace(/\b\w/g, function(c){return c.toUpperCase();});
    modelLabel.textContent = m;
  }
  var modelBreakdown = '';
  if (usage.modelBreakdown && usage.modelBreakdown.length > 0) {
    var primary = usage.modelBreakdown[0];
    var others = usage.modelBreakdown.slice(1, 3);
    modelBreakdown = fmtTokens(primary.tokens) + ' tokens';
    if (others.length > 0) {
      modelBreakdown += ' (+' + others.length + ' others)';
    }
  } else {
    modelBreakdown = 'Primary model';
  }
  document.getElementById('model-breakdown').textContent = modelBreakdown;
  
  // 🐝 Worker Bees (Sub-Agents)
  loadSubAgents();
  
}

async function loadSubAgents() {
  try {
    var data = await fetch('/api/subagents').then(r => r.json());
    var counts = data.counts;
    var subagents = data.subagents;
    
    // Update main counter
    document.getElementById('subagents-count').textContent = counts.total;
    
    // Update status text
    var statusText = '';
    if (counts.active > 0) {
      statusText = counts.active + ' active';
      if (counts.idle > 0) statusText += ', ' + counts.idle + ' idle';
      if (counts.stale > 0) statusText += ', ' + counts.stale + ' stale';
    } else if (counts.total === 0) {
      statusText = 'No sub-agents spawned';
    } else {
      statusText = 'All idle/stale';
    }
    document.getElementById('subagents-status').textContent = statusText;
    
    // Update preview with top sub-agents (human-readable)
    var previewHtml = '';
    if (subagents.length === 0) {
      previewHtml = '<div style="font-size:11px;color:#666;">No active tasks</div>';
    } else {
      // Show active ones first
      var activeFirst = subagents.filter(function(a){return a.status==='active';}).concat(subagents.filter(function(a){return a.status!=='active';}));
      var topAgents = activeFirst.slice(0, 3);
      topAgents.forEach(function(agent) {
        var icon = agent.status === 'active' ? '🔄' : agent.status === 'idle' ? '✅' : '⬜';
        var name = cleanTaskName(agent.displayName);
        if (name.length > 40) name = name.substring(0, 37) + '…';
        previewHtml += '<div class="subagent-item">';
        previewHtml += '<span style="font-size:10px;">' + icon + '</span>';
        previewHtml += '<span class="subagent-name" style="overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">' + escHtml(name) + '</span>';
        previewHtml += '<span class="subagent-runtime">' + agent.runtime + '</span>';
        previewHtml += '</div>';
      });
      
      if (subagents.length > 3) {
        previewHtml += '<div style="font-size:9px;color:#555;margin-top:4px;">+' + (subagents.length - 3) + ' more</div>';
      }
    }
    
    document.getElementById('subagents-preview').innerHTML = previewHtml;
    
  } catch(e) {
    document.getElementById('subagents-count').textContent = '?';
    document.getElementById('subagents-status').textContent = 'Error loading sub-agents';
    document.getElementById('subagents-preview').innerHTML = '<div style="color:#e74c3c;font-size:11px;">Failed to load workforce</div>';
  }
}

// === Active Tasks for Overview ===
var _activeTasksTimer = null;
function cleanTaskName(raw) {
  // Strip timestamp prefixes like "[Sun 2026-02-08 18:22 GMT+1] "
  var name = (raw || '').replace(/^\[.*?\]\s*/, '');
  // Truncate to first sentence or 80 chars
  var dot = name.indexOf('. ');
  if (dot > 10 && dot < 80) name = name.substring(0, dot + 1);
  if (name.length > 80) name = name.substring(0, 77) + '…';
  return name || 'Background task';
}

function detectProjectBadge(text) {
  var projects = {
    'mockround': { label: 'MockRound', color: '#7c3aed' },
    'vedicvoice': { label: 'VedicVoice', color: '#d97706' },
    'openclaw': { label: 'OpenClaw', color: '#2563eb' },
    'dashboard': { label: 'Dashboard', color: '#0891b2' },
    'shopify': { label: 'Shopify', color: '#16a34a' },
    'sanskrit': { label: 'Sanskrit', color: '#ea580c' },
    'telegram': { label: 'Telegram', color: '#0088cc' },
    'discord': { label: 'Discord', color: '#5865f2' },
  };
  var lower = (text || '').toLowerCase();
  for (var key in projects) {
    if (lower.includes(key)) return projects[key];
  }
  return null;
}

function humanTime(runtimeMs) {
  if (!runtimeMs || runtimeMs === Infinity) return '';
  var sec = Math.floor(runtimeMs / 1000);
  if (sec < 60) return 'Started ' + sec + 's ago';
  var min = Math.floor(sec / 60);
  if (min < 60) return 'Started ' + min + ' min ago';
  var hr = Math.floor(min / 60);
  if (hr < 24) return 'Started ' + hr + 'h ago';
  return 'Started ' + Math.floor(hr / 24) + 'd ago';
}

function humanTimeDone(runtimeMs) {
  if (!runtimeMs || runtimeMs === Infinity) return '';
  var sec = Math.floor(runtimeMs / 1000);
  if (sec < 60) return 'Finished ' + sec + 's ago';
  var min = Math.floor(sec / 60);
  if (min < 60) return 'Finished ' + min + ' min ago';
  var hr = Math.floor(min / 60);
  if (hr < 24) return 'Finished ' + hr + 'h ago';
  return 'Finished ' + Math.floor(hr / 24) + 'd ago';
}

async function loadActiveTasks() {
  try {
    var grid = document.getElementById('overview-tasks-list') || document.getElementById('active-tasks-grid');
    if (!grid) return;

    // Fetch active sub-agents
    var saData = await fetch('/api/subagents').then(r => r.json()).catch(function() { return {subagents:[]}; });

    // "Active Tasks" should mean ACTIVE. Previously we lingered failed
    // and stale entries here for 24h, which meant a subagent that failed
    // hours ago still appeared as if it were current. Tightened:
    //   - active / idle: always show (subagent still alive)
    //   - failed: only within the last 10 minutes, and only when there's
    //     nothing live — so a just-failed spawn still surfaces briefly.
    //   - stale / older failures: don't show. The subagent detail modal
    //     and the Brain tab are the right surfaces for history.
    var RECENT_MS = 10 * 60 * 1000;
    var now = Date.now();
    var all = (saData.subagents || []);
    var live = all.filter(function(a) { return a.status === 'active' || a.status === 'idle'; });
    var recentFailed = all.filter(function(a) {
      return a.status === 'failed' && (now - (a.updatedAt || 0)) < RECENT_MS;
    });
    var agents = live.length ? live : recentFailed.slice(0, 3);

    if (agents.length === 0) {
      grid.innerHTML = '<div class="card" style="text-align:center;padding:24px;color:var(--text-muted);grid-column:1/-1;">'
        + '<div style="font-size:24px;margin-bottom:8px;">✨</div>'
        + '<div style="font-size:13px;">No active tasks - all quiet</div></div>';
      var badge = document.getElementById('overview-tasks-count-badge');
      if (badge) badge.textContent = '';
      return;
    }

    var html = '';
    var badge = document.getElementById('overview-tasks-count-badge');
    if (badge) {
      var liveCount = agents.filter(function(a) { return a.status === 'active' || a.status === 'idle'; }).length;
      badge.textContent = liveCount > 0 ? (liveCount + ' active') : (agents.length + ' recent');
    }

    // Per-status visual style
    var STATUS_STYLE = {
      active: {cls: 'running',  dot: '#22c55e', label: 'active'},
      idle:   {cls: 'running',  dot: '#f59e0b', label: 'idle'},
      stale:  {cls: '',         dot: '#6b7280', label: 'completed'},
      failed: {cls: '',         dot: '#ef4444', label: 'failed'},
    };

    // Render sub-agents
    agents.forEach(function(agent) {
      var taskName = cleanTaskName(agent.displayName);
      var badge2 = detectProjectBadge(agent.displayName);
      var mins = Math.max(1, Math.floor((agent.runtimeMs || 0) / 60000));
      var st = STATUS_STYLE[agent.status] || STATUS_STYLE.active;

      html += '<div class="task-card ' + st.cls + '" style="cursor:pointer;" onclick="openTaskModal(\'' + escHtml(agent.sessionId).replace(/'/g,"\\'") + '\',\'' + escHtml(taskName).replace(/'/g,"\\'") + '\',\'' + escHtml(agent.key || agent.sessionId).replace(/'/g,"\\'") + '\')">';
      if (agent.status === 'active' || agent.status === 'idle') {
        html += '<div class="task-card-pulse active"></div>';
      }
      html += '<div class="task-card-header">';
      html += '<div class="task-card-name"><span style="display:inline-block;width:8px;height:8px;border-radius:50%;background:' + st.dot + ';margin-right:6px;vertical-align:middle;"></span>' + escHtml(taskName) + '</div>';
      html += '<span class="task-card-badge ' + st.cls + '" style="font-size:10px;">' +
              (agent.status === 'failed' ? '⚠️ ' + st.label :
               agent.status === 'stale'  ? '🤖 ' + st.label :
               '🤖 ' + mins + ' min') +
              '</span>';
      html += '</div>';
      // Task summary line (shown for all statuses if present)
      if (agent.task) {
        var taskPreview = agent.task.length > 90 ? agent.task.substring(0, 87) + '…' : agent.task;
        html += '<div style="font-size:11px;color:var(--text-secondary);margin-top:4px;line-height:1.4;">' + escHtml(taskPreview) + '</div>';
      }
      // The failed badge in the top-right already conveys status; the raw
      // OpenClaw error string ("Validation failed for tool 'subagents':")
      // was redundant on the card and too jargon-y. Full error is still
      // surfaced in the modal when the user clicks through.
      html += '<div style="display:flex;align-items:center;gap:8px;margin-top:4px;">';
      if (badge2) {
        html += '<span style="display:inline-block;padding:1px 8px;border-radius:10px;font-size:10px;font-weight:700;background:' + badge2.color + '22;color:' + badge2.color + ';border:1px solid ' + badge2.color + '44;">' + badge2.label + '</span>';
      }
      html += '<span style="font-size:11px;color:var(--text-muted);">' + escHtml(humanTime(agent.runtimeMs)) + '</span>';
      html += '</div>';
      html += '</div>';
    });

    grid.innerHTML = html;
  } catch(e) {
    // silently fail
  }
}
// Auto-refresh active tasks every 30s
function startActiveTasksRefresh() {
  loadActiveTasks();
  if (_activeTasksTimer) clearInterval(_activeTasksTimer);
  _activeTasksTimer = setInterval(loadActiveTasks, 30000);
}

async function loadToolActivity() {
  try {
    var logs = await fetch('/api/logs?lines=100').then(r => r.json());
    var toolCounts = { exec: 0, browser: 0, search: 0, other: 0 };
    var recentTools = [];
    
    logs.lines.forEach(function(line) {
      var msg = line.toLowerCase();
      if (msg.includes('tool') || msg.includes('invoke')) {
        if (msg.includes('exec') || msg.includes('shell')) { 
          toolCounts.exec++; recentTools.push('exec'); 
        } else if (msg.includes('browser') || msg.includes('screenshot')) { 
          toolCounts.browser++; recentTools.push('browser'); 
        } else if (msg.includes('web_search') || msg.includes('web_fetch')) { 
          toolCounts.search++; recentTools.push('search'); 
        } else {
          toolCounts.other++;
        }
      }
    });
    
    document.getElementById('tools-active').textContent = recentTools.slice(0, 3).join(', ') || 'Idle';
    document.getElementById('tools-recent').textContent = 'Last ' + Math.min(logs.lines.length, 100) + ' log entries';
    
    var sparks = document.querySelectorAll('.tool-spark span');
    sparks[0].textContent = toolCounts.exec;
    sparks[1].textContent = toolCounts.browser;  
    sparks[2].textContent = toolCounts.search;
  } catch(e) {
    document.getElementById('tools-active').textContent = '--';
  }
}

async function loadActivityStream() {
  try {
    var transcripts = await fetchJsonWithTimeout('/api/transcripts', 4000);
    var activities = [];
    
    // Get the most recent transcript to parse for activity
    if (transcripts.transcripts && transcripts.transcripts.length > 0) {
      var recent = transcripts.transcripts[0];
      try {
        var transcript = await fetchJsonWithTimeout('/api/transcript/' + recent.id, 4000);
        var recentMessages = transcript.messages.slice(-10); // Last 10 messages
        
        recentMessages.forEach(function(msg) {
          if (msg.role === 'assistant' && msg.content) {
            var content = msg.content.toLowerCase();
            var activity = '';
            var time = new Date(msg.timestamp || Date.now()).toLocaleTimeString();
            
            if (content.includes('searching') || content.includes('search')) {
              activity = time + ' 🔍 Searching web for information';
            } else if (content.includes('reading') || content.includes('file')) {
              activity = time + ' 📖 Reading files';
            } else if (content.includes('writing') || content.includes('edit')) {
              activity = time + ' ✏️ Editing files'; 
            } else if (content.includes('exec') || content.includes('command')) {
              activity = time + ' ⚡ Running commands';
            } else if (content.includes('browser') || content.includes('screenshot')) {
              activity = time + ' 🌐 Browser automation';
            } else if (msg.content.length > 50) {
              var preview = msg.content.substring(0, 80).replace(/[^\w\s]/g, ' ').trim();
              activity = time + ' 💭 ' + preview + '...';
            }
            
            if (activity) activities.push(activity);
          }
        });
      } catch(e) {}
    }
    
    if (activities.length === 0) {
      activities = [
        new Date().toLocaleTimeString() + ' 🤖 AI agent initialized',
        new Date().toLocaleTimeString() + ' 📡 Monitoring for activity...'
      ];
    }
    
    var html = activities.slice(-8).map(function(a) {
      return '<div style="padding:4px 0; border-bottom:1px solid #1a1a30; color:#ccc;">' + escHtml(a) + '</div>';
    }).join('');
    
    document.getElementById('activity-stream').innerHTML = html;
  } catch(e) {
    document.getElementById('activity-stream').innerHTML = '<div style="color:#666;">Error loading activity stream</div>';
  }
}


// ── Brain tab
// ── Brain tab ─────────────────────────────────────────────────────────
var _brainRefreshTimer = null;
var _brainSourceColors = {};
var _brainColorPalette = ['#2dd4bf','#f97316','#eab308','#ec4899','#3b82f6','#a78bfa','#f43f5e','#10b981'];
var _brainColorIdx = 0;
// Persistent expand state across the 5s auto-refresh re-renders. Without
// this, tapping a brain event "auto-collapses" within ~5s simply because
// the next refresh wipes the .expanded class. Keyed by stable event id.
var _brainExpandedKeys = {};

function _brainEvKey(ev) {
  return (ev.time || '') + '|' + (ev.type || '') + '|' + (ev.source || '');
}

function _toggleBrainEvent(el, key) {
  _brainExpandedKeys[key] = !_brainExpandedKeys[key];
  el.classList.toggle('expanded', !!_brainExpandedKeys[key]);
  var td = el.querySelector('.brain-turn-detail');
  if (td) td.style.display = _brainExpandedKeys[key] ? '' : 'none';
}

function brainSourceColor(source) {
  if (source === 'main') return '#a855f7';
  if (!_brainSourceColors[source]) {
    _brainSourceColors[source] = _brainColorPalette[_brainColorIdx % _brainColorPalette.length];
    _brainColorIdx++;
  }
  return _brainSourceColors[source];
}

function formatBrainTime(isoStr) {
  try {
    var d = new Date(isoStr);
    var now = new Date();
    var sameDay = d.getFullYear()===now.getFullYear() && d.getMonth()===now.getMonth() && d.getDate()===now.getDate();
    var time = d.toLocaleTimeString('en-GB', {hour:'2-digit',minute:'2-digit',second:'2-digit'});
    var prefix = sameDay ? 'Today' : d.toLocaleDateString('en-GB', {day:'numeric',month:'short'});
    return '<span style="opacity:0.45;font-size:10px;margin-right:3px;">' + prefix + '</span>' + time;
  } catch(e) { return isoStr || ''; }
}

function renderBrainDetail(detail) {
  if (!detail) return '';
  var s = detail.trim();
  // Try JSON rendering
  var jsonMatch = s.match(/^```json\s*([\s\S]*?)```$/) || s.match(/^(\{[\s\S]*\}|\[[\s\S]*\])$/);
  if (jsonMatch) {
    try {
      var obj = JSON.parse(jsonMatch[1] || jsonMatch[0]);
      var pretty = JSON.stringify(obj, null, 2);
      return '<pre style="background:var(--bg-tertiary,#1a1a2e);border:1px solid var(--border-primary,#333);border-radius:6px;padding:8px 10px;margin:4px 0 0;font-size:11px;color:var(--text-secondary);overflow-x:auto;white-space:pre-wrap;word-break:break-all;max-height:180px;">' + escHtml(pretty) + '</pre>';
    } catch(e) {}
  }
  // Inline markdown: **bold**, `code`, ```block```
  var html = escHtml(s);
  // Code blocks
  html = html.replace(/```([\s\S]*?)```/g, '<pre style="background:var(--bg-tertiary,#1a1a2e);border:1px solid var(--border-primary,#333);border-radius:6px;padding:6px 10px;margin:4px 0 0;font-size:11px;overflow-x:auto;white-space:pre-wrap;max-height:180px;">$1</pre>');
  // Inline code
  html = html.replace(/`([^`]+)`/g, '<code style="background:var(--bg-tertiary,#1a1a2e);padding:1px 5px;border-radius:3px;font-size:11px;">$1</code>');
  // Bold
  html = html.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
  return '<span style="white-space:pre-wrap;word-break:break-word;">' + html + '</span>';
}

var _brainFilter = 'all';
var _brainTypeFilter = 'all';
var _brainChannelFilter = 'all';
var _brainAllEvents = [];

var _channelIcons = {
  'telegram': '📱', 'whatsapp': '💬', 'discord': '🎮', 'slack': '📢',
  'signal': '📡', 'irc': '💻', 'imessage': '🍎', 'webchat': '🌐',
  'googlechat': '📧', 'cli': '🖥️', 'cron': '⏰'
};
var _channelColors = {
  'telegram': '#2f9ef4', 'whatsapp': '#25d366', 'discord': '#5865F2', 'slack': '#4A154B',
  'signal': '#3a76f0', 'irc': '#6B7280', 'imessage': '#34C759', 'webchat': '#0EA5E9',
  'googlechat': '#1A73E8', 'cli': '#94a3b8', 'cron': '#6B7280'
};

var _brainTypeIcons = {
  'EXEC': '⚙️', 'SHELL': '⚙️', 'READ': '📖', 'WRITE': '✏️',
  'BROWSER': '🌐', 'MSG': '📨', 'SEARCH': '🔍', 'SPAWN': '🚀',
  'DONE': '✅', 'ERROR': '❌', 'TOOL': '🔧',
  'USER': '💬', 'THINK': '🧠', 'AGENT': '🤖'
};


function setBrainTypeFilter(type, btn) {
  _brainTypeFilter = type;
  document.querySelectorAll('.brain-type-chip').forEach(function(b) {
    var isActive = b.dataset.type === type;
    b.style.background = isActive ? 'rgba(168,85,247,0.2)' : 'transparent';
    b.style.fontWeight = isActive ? '600' : '400';
  });
  renderBrainFeed();
}
function setBrainFilter(source, btn) {
  _brainFilter = source;
  document.querySelectorAll('.brain-chip').forEach(function(b) {
    b.classList.remove('active');
    b.style.background = 'transparent';
    b.style.fontWeight = '400';
  });
  btn.classList.add('active');
  var btnColor = btn.style.color || '#a855f7';
  btn.style.background = btn.style.borderColor ? btn.style.borderColor.replace(')', ',0.25)').replace('rgb','rgba') : 'rgba(168,85,247,0.25)';
  btn.style.fontWeight = '700';
  btn.style.boxShadow = '0 0 8px ' + (btn.style.borderColor || '#a855f7');
  renderBrainStream(_brainAllEvents);
}

function scrollBrainToTop() {
  var el = document.getElementById('brain-stream');
  if (el) el.scrollTop = 0;
  var pill = document.getElementById('brain-new-pill');
  if (pill) pill.style.display = 'none';
}

var _brainFilterExpanded = false;
window.toggleBrainFilterExpanded = function() {
  _brainFilterExpanded = !_brainFilterExpanded;
  renderBrainFilterChips(window._brainSourcesCache || []);
};

function _brainChipHtml(s) {
  var isActive = _brainFilter === s.id;
  var icon = s.icon || (s.id === 'main' ? '🧠' : '🤖');
  return '<button class="brain-chip' + (isActive ? ' active' : '') + '" data-source="' +
    escHtml(s.id) + '" title="' + escHtml(s.id) +
    '" onclick="setBrainFilter(this.dataset.source,this)" style="padding:3px 10px;border-radius:12px;border:1px solid ' +
    s.color + ';background:' + (isActive ? 'rgba(100,100,100,0.2)' : 'transparent') +
    ';color:' + s.color + ';font-size:11px;cursor:pointer;font-weight:' +
    (isActive ? '600' : '400') + ';">' + icon + ' ' + escHtml(s.label || s.id) + '</button>';
}

function renderBrainFilterChips(sources) {
  var container = document.getElementById('brain-filter-chips');
  if (!container || !sources) return;
  // Cache for the expand/collapse toggle re-render
  window._brainSourcesCache = sources;

  // "All" chip — always first, always visible
  var allActive = _brainFilter === 'all';
  var html = '<button class="brain-chip' + (allActive ? ' active' : '') +
    '" data-source="all" onclick="setBrainFilter(\'all\',this)" style="padding:3px 10px;border-radius:12px;border:1px solid #a855f7;background:' +
    (allActive ? 'rgba(168,85,247,0.2)' : 'transparent') +
    ';color:#a855f7;font-size:11px;cursor:pointer;font-weight:' +
    (allActive ? '600' : '400') + ';">All</button>';

  // Sort: main first, then by last_ts desc
  var sorted = sources.slice().sort(function(a, b) {
    if ((a.category === 'main') !== (b.category === 'main'))
      return a.category === 'main' ? -1 : 1;
    return (b.last_ts || 0) - (a.last_ts || 0);
  });

  var TOP_N = 5;
  var alwaysShow = [];
  var overflow = [];
  sorted.forEach(function(s) {
    if (alwaysShow.length < TOP_N + 1 && (s.category === 'main' || alwaysShow.length < TOP_N + (sorted[0].category === 'main' ? 1 : 0)))
      alwaysShow.push(s);
    else
      overflow.push(s);
  });
  // Fallback when <= 6 total: just show everything.
  if (sorted.length <= TOP_N + 1) {
    alwaysShow = sorted;
    overflow = [];
  }

  alwaysShow.forEach(function(s) { html += _brainChipHtml(s); });

  if (overflow.length > 0) {
    if (!_brainFilterExpanded) {
      html += '<button class="brain-chip" onclick="toggleBrainFilterExpanded()" style="padding:3px 10px;border-radius:12px;border:1px dashed #888;background:transparent;color:#888;font-size:11px;cursor:pointer;font-weight:400;">+ ' +
        overflow.length + ' more ▾</button>';
    } else {
      // Group overflow by category; render one small label row per group
      var groups = {channel: [], subagent: [], cron: [], other: []};
      overflow.forEach(function(s) {
        var g = groups[s.category] !== undefined ? s.category : 'other';
        groups[g].push(s);
      });
      var groupLabels = {channel: 'Channels', subagent: 'Subagents', cron: 'Crons', other: 'Other'};
      ['channel', 'subagent', 'cron', 'other'].forEach(function(g) {
        if (!groups[g].length) return;
        html += '<span class="brain-chip-group-label">' + groupLabels[g] + '</span>';
        groups[g].forEach(function(s) { html += _brainChipHtml(s); });
      });
      html += '<button class="brain-chip" onclick="toggleBrainFilterExpanded()" style="padding:3px 10px;border-radius:12px;border:1px dashed #888;background:transparent;color:#888;font-size:11px;cursor:pointer;font-weight:400;">− collapse ▴</button>';
    }
  }
  container.innerHTML = html;
}

function renderBrainTypeChips(events) {
  var container = document.getElementById('brain-type-chips');
  if (!container || !events) return;
  var typeColors = {'USER':'#60a5fa','AGENT':'#a855f7','EXEC':'#f59e0b','THINK':'#94a3b8','TOOL':'#f97316','WRITE':'#10b981','SEARCH':'#06b6d4','BROWSER':'#ec4899','SPAWN':'#8b5cf6','MSG':'#22c55e','READ':'#6ee7b7','CONTEXT':'#64748b','RESULT':'#6ee7b7'};
  var typeCounts = {};
  events.forEach(function(ev) { typeCounts[ev.type] = (typeCounts[ev.type]||0) + 1; });
  var types = Object.keys(typeCounts).sort();
  if (types.length < 2) { container.innerHTML = ''; return; }
  var html = '<button class="brain-type-chip" data-type="all" onclick="setBrainTypeFilter(\'all\',this)" style="padding:2px 9px;border-radius:10px;border:1px solid #666;background:' + (_brainTypeFilter === 'all' ? 'rgba(100,100,200,0.15)' : 'transparent') + ';color:#888;font-size:10px;cursor:pointer;font-weight:' + (_brainTypeFilter === 'all' ? '600' : '400') + ';">All types</button>';
  types.forEach(function(t) {
    var col = typeColors[t] || '#888';
    var isActive = _brainTypeFilter === t;
    html += '<button class="brain-type-chip" data-type="' + t + '" onclick="setBrainTypeFilter(\'' + t + '\',this)" style="padding:2px 9px;border-radius:10px;border:1px solid ' + col + ';background:' + (isActive ? col + '22' : 'transparent') + ';color:' + col + ';font-size:10px;cursor:pointer;font-weight:' + (isActive ? '600' : '400') + ';">' + t + ' (' + typeCounts[t] + ')</button>';
  });
  container.innerHTML = html;
}

function renderBrainChannelChips(channels) {
  var container = document.getElementById('brain-channel-chips');
  if (!container) return;
  if (!channels || Object.keys(channels).length < 2) { container.innerHTML = ''; return; }
  var html = '<button class="brain-ch-chip" onclick="setBrainChannelFilter(\'all\',this)" style="padding:2px 9px;border-radius:10px;border:1px solid #666;background:' + (_brainChannelFilter === 'all' ? 'rgba(100,100,200,0.15)' : 'transparent') + ';color:#888;font-size:10px;cursor:pointer;font-weight:' + (_brainChannelFilter === 'all' ? '600' : '400') + ';">All channels</button>';
  Object.keys(channels).sort().forEach(function(ch) {
    var ico = _channelIcons[ch] || '📨';
    var col = _channelColors[ch] || '#888';
    var isActive = _brainChannelFilter === ch;
    html += '<button class="brain-ch-chip" onclick="setBrainChannelFilter(\'' + ch + '\',this)" style="padding:2px 9px;border-radius:10px;border:1px solid ' + col + ';background:' + (isActive ? col + '22' : 'transparent') + ';color:' + col + ';font-size:10px;cursor:pointer;font-weight:' + (isActive ? '600' : '400') + ';">' + ico + ' ' + ch + ' (' + channels[ch] + ')</button>';
  });
  container.innerHTML = html;
}

function setBrainChannelFilter(ch, btn) {
  _brainChannelFilter = ch;
  renderBrainChannelChips(window._brainChannelCounts || {});
  renderBrainStream(_brainAllEvents);
}

function renderBrainStream(events) {
  var el = document.getElementById('brain-stream');
  if (!el) return;
  var filtered = _brainFilter === 'all' ? events : events.filter(function(ev) { return ev.source === _brainFilter; });
  if (_brainTypeFilter !== 'all') {
    filtered = filtered.filter(function(ev) { return ev.type === _brainTypeFilter; });
  }
  if (_brainChannelFilter !== 'all') {
    filtered = filtered.filter(function(ev) { return (ev.channel || '') === _brainChannelFilter; });
  }
  filtered = filtered.slice().sort(function(a,b){
    var ta = a.time ? new Date(a.time).getTime() : 0;
    var tb = b.time ? new Date(b.time).getTime() : 0;
    return tb - ta;
  });
  if (!filtered || filtered.length === 0) {
    el.innerHTML = '<div style="color:var(--text-muted);padding:20px">No activity yet</div>';
    return;
  }
  var html = '';
  filtered.forEach(function(ev) {
    var color = ev.color || brainSourceColor(ev.source || 'main');
    var evType = ev.type || 'TOOL';
    var icon = _brainTypeIcons[evType] || '🔧';
    var fullSrc = ev.sourceLabel || ev.source || 'main';
    var srcParts = fullSrc.split(':');
    var shortSrc = srcParts[srcParts.length - 1] || fullSrc;
    if (shortSrc.length > 12) shortSrc = shortSrc.slice(0, 8) + '\u2026';
    var roleIcon = fullSrc.indexOf('subagent') >= 0 ? '\uD83E\uDD16' : '\uD83E\uDDE0';
    // Channel badge
    var chBadge = '';
    var ch = ev.channel || '';
    if (ch) {
      var chIco = _channelIcons[ch] || '📨';
      var chCol = _channelColors[ch] || '#667';
      var chLabel = ch.charAt(0).toUpperCase() + ch.slice(1);
      if (ev.channelSubject) chLabel += ':' + (ev.channelSubject.length > 14 ? ev.channelSubject.slice(0, 12) + '\u2026' : ev.channelSubject);
      chBadge = '<span class="brain-channel" style="color:' + chCol + ';font-size:10px;flex-shrink:0;opacity:0.8;white-space:nowrap;" title="' + escHtml(ch + (ev.channelSubject ? ': ' + ev.channelSubject : '')) + '">' + chIco + ' ' + escHtml(chLabel) + '</span>';
    }
    // Skill badge — detect from detail path or ev.skill field
    var skillBadge = '';
    var skillName = ev.skill || '';
    if (!skillName) {
      var det = ev.detail || '';
      var skillMatch = det.match(/\/skills\/([^\/\s]+)/);
      if (skillMatch) skillName = skillMatch[1];
      // Also detect cron-invoked skills from [cron:uuid name] pattern
      if (!skillName && det.indexOf('[cron:') === 0) {
        var cronNameMatch = det.match(/\[cron:[0-9a-f-]+ ([^\]]+)\]/);
        if (cronNameMatch) skillName = cronNameMatch[1];
      }
    }
    if (skillName) {
      skillBadge = '<span class="brain-skill" style="color:#f59e0b;font-size:10px;flex-shrink:0;white-space:nowrap;" title="Skill: ' + escHtml(skillName) + '">🎯 ' + escHtml(skillName.length > 16 ? skillName.slice(0, 14) + '\u2026' : skillName) + '</span>';
    }
    // Build turn timeline for USER events (Phase 4: Agent Runtime Timeline)
    var turnTimeline = '';
    if (evType === 'USER') {
      // Find all events in this turn (from this USER to the next USER)
      var evIdx = filtered.indexOf(ev);
      var turnEvents = [];
      for (var ti = evIdx + 1; ti < filtered.length; ti++) {
        if (filtered[ti].type === 'USER') break;
        turnEvents.push(filtered[ti]);
      }
      if (turnEvents.length > 0) {
        var turnStart = ev.time ? new Date(ev.time).getTime() : 0;
        var turnEnd = turnEvents.length > 0 && turnEvents[turnEvents.length-1].time ? new Date(turnEvents[turnEvents.length-1].time).getTime() : turnStart;
        var turnDuration = turnStart && turnEnd ? ((turnStart - turnEnd) / 1000).toFixed(1) : '?';
        var llmCalls = turnEvents.filter(function(e){return e.type==='AGENT'||e.type==='THINK';}).length;
        var toolCalls = turnEvents.filter(function(e){return e.type==='EXEC'||e.type==='READ'||e.type==='WRITE'||e.type==='BROWSER'||e.type==='SEARCH'||e.type==='TOOL';}).length;
        // Detect sub-agent events (different source = sub-agent)
        var parentSource = ev.source || 'main';
        var subagentSources = {};
        turnEvents.forEach(function(te) {
          var teSrc = te.source || 'main';
          if (teSrc !== parentSource && teSrc !== 'main') {
            subagentSources[teSrc] = (subagentSources[teSrc] || 0) + 1;
          }
        });
        var subagentCount = Object.keys(subagentSources).length;

        // Summary badge
        turnTimeline = '<div class="brain-turn-summary" style="display:flex;gap:6px;flex-wrap:wrap;margin-top:2px;font-size:10px;color:var(--text-muted);">';
        turnTimeline += '<span style="background:rgba(139,92,246,0.15);color:#a78bfa;padding:1px 6px;border-radius:3px;">&#9881; ' + turnEvents.length + ' steps</span>';
        if (llmCalls > 0) turnTimeline += '<span style="background:rgba(59,130,246,0.15);color:#60a5fa;padding:1px 6px;border-radius:3px;">&#129302; ' + llmCalls + ' LLM</span>';
        if (toolCalls > 0) turnTimeline += '<span style="background:rgba(245,158,11,0.15);color:#f59e0b;padding:1px 6px;border-radius:3px;">&#128295; ' + toolCalls + ' tools</span>';
        if (subagentCount > 0) turnTimeline += '<span style="background:rgba(236,72,153,0.15);color:#ec4899;padding:1px 6px;border-radius:3px;">&#129302; ' + subagentCount + ' sub-agent' + (subagentCount > 1 ? 's' : '') + '</span>';
        if (turnDuration !== '?' && parseFloat(turnDuration) > 0) turnTimeline += '<span style="background:rgba(16,185,129,0.15);color:#10b981;padding:1px 6px;border-radius:3px;">&#9202; ' + turnDuration + 's</span>';
        turnTimeline += '</div>';
        // Expandable timeline detail. Initial display reflects the persisted
        // expanded state so a 5s auto-refresh re-render preserves the user's
        // tap; otherwise the row would appear to auto-collapse.
        var _isExp = !!_brainExpandedKeys[_brainEvKey(ev)];
        turnTimeline += '<div class="brain-turn-detail" style="display:' + (_isExp ? '' : 'none') + ';margin-top:6px;padding:6px 0 2px 16px;border-left:2px solid rgba(139,92,246,0.3);">';
        var currentSubagent = null;
        turnEvents.forEach(function(te) {
          var teIcon = _brainTypeIcons[te.type] || '&#128295;';
          var teTime = formatBrainTime(te.time);
          var teDetail = (te.detail || '').substring(0, 120);
          var teCol = {'AGENT':'#a855f7','THINK':'#94a3b8','EXEC':'#f59e0b','READ':'#6ee7b7','WRITE':'#10b981','BROWSER':'#ec4899','SEARCH':'#06b6d4','TOOL':'#f97316','RESULT':'#6ee7b7','SPAWN':'#ec4899'}[te.type] || '#888';
          var teSrc = te.source || 'main';
          var isSubagent = teSrc !== parentSource && teSrc !== 'main';

          // Sub-agent group header
          if (isSubagent && currentSubagent !== teSrc) {
            if (currentSubagent) turnTimeline += '</div>'; // close previous
            currentSubagent = teSrc;
            var saLabel = (te.sourceLabel || teSrc).split(':').pop();
            if (saLabel.length > 10) saLabel = saLabel.slice(0, 8);
            var saEvents = subagentSources[teSrc] || 0;
            turnTimeline += '<div style="margin:4px 0 2px 0;padding:4px 8px;background:rgba(236,72,153,0.08);border:1px solid rgba(236,72,153,0.2);border-radius:6px;">';
            turnTimeline += '<div style="font-size:10px;font-weight:600;color:#ec4899;margin-bottom:3px;">&#129302; Sub-agent: ' + escHtml(saLabel) + ' (' + saEvents + ' steps)</div>';
          } else if (!isSubagent && currentSubagent) {
            turnTimeline += '</div>'; // close sub-agent group
            currentSubagent = null;
          }

          var indent = isSubagent ? 'padding-left:12px;' : '';
          turnTimeline += '<div style="display:flex;gap:6px;align-items:flex-start;padding:2px 0;font-size:11px;' + indent + '">';
          turnTimeline += '<span style="color:var(--text-faint);min-width:50px;flex-shrink:0;">' + teTime + '</span>';
          turnTimeline += '<span style="color:' + teCol + ';min-width:55px;font-weight:600;flex-shrink:0;">' + teIcon + ' ' + te.type + '</span>';
          turnTimeline += '<span style="color:var(--text-secondary);overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">' + escHtml(teDetail) + '</span>';
          turnTimeline += '</div>';
        });
        if (currentSubagent) turnTimeline += '</div>'; // close last sub-agent group
        turnTimeline += '</div>';
      }
    }
    var _evKey = _brainEvKey(ev);
    var _evExpCls = _brainExpandedKeys[_evKey] ? ' expanded' : '';
    html += '<div class="brain-event' + _evExpCls + '" data-evkey="' + escHtml(_evKey) + '" onclick="_toggleBrainEvent(this, this.dataset.evkey)">';
    html += '<div class="brain-meta">';
    html += '<span class="brain-time">' + formatBrainTime(ev.time) + '</span>';
    html += '<span class="brain-type" style="background:rgba(100,100,100,0.15);color:' + color + ';padding:1px 6px;border-radius:3px;font-size:10px;font-weight:700;min-width:70px;text-align:center;display:inline-block;white-space:nowrap;">' + icon + ' ' + escHtml(evType) + '</span>';
    html += '<span class="brain-source" style="color:' + color + ';flex-shrink:0;" title="' + escHtml(fullSrc) + '">' + roleIcon + ' ' + escHtml(shortSrc) + '</span>';
    html += chBadge;
    html += skillBadge;
    html += '</div>';
    html += '<span class="brain-detail">' + renderBrainDetail(ev.detail || '') + '</span>';
    html += turnTimeline;
    html += '</div>';
  });
  el.innerHTML = html;
}

function renderBrainChart(events) {
  var canvas = document.getElementById('brain-density-chart');
  if (!canvas || !canvas.getContext) return;
  // Filter events by active pill
  if (_brainFilter !== 'all') {
    events = events.filter(function(ev) { return ev.source === _brainFilter; });
    }
    if (_brainTypeFilter !== 'all') {
    events = events.filter(function(ev) { return ev.type === _brainTypeFilter; });
  }
  var ctx = canvas.getContext('2d');
  var W = canvas.parentElement ? canvas.parentElement.offsetWidth : (canvas.offsetWidth || 800);
  canvas.width = W;
  canvas.height = 80;
  ctx.clearRect(0, 0, W, 80);

  // 60 min / 30s = 120 buckets, stacked by source color
  var now = Date.now();
  var bucketMs = 30000;
  var numBuckets = 120;
  var buckets = {};
  events.forEach(function(ev) {
    try {
      var t = new Date(ev.time).getTime();
      var age = now - t;
      if (age < 0 || age > numBuckets * bucketMs) return;
      var idx = numBuckets - 1 - Math.floor(age / bucketMs);
      if (idx >= 0 && idx < numBuckets) {
        if (!buckets[idx]) buckets[idx] = [];
        buckets[idx].push(ev.color || brainSourceColor(ev.source || 'main'));
      }
    } catch(e) {}
  });

  var maxVal = 1;
  for (var i = 0; i < numBuckets; i++) { if (buckets[i]) maxVal = Math.max(maxVal, buckets[i].length); }
  var barW = W / numBuckets;
  for (var i = 0; i < numBuckets; i++) {
    if (!buckets[i]) continue;
    var colors = buckets[i];
    var segH = Math.max(2, (colors.length / maxVal) * 72) / colors.length;
    colors.forEach(function(col, ci) {
      ctx.fillStyle = col;
      ctx.globalAlpha = 0.82;
      ctx.fillRect(i * barW, 80 - segH * (ci + 1), Math.max(1, barW - 1), segH);
    });
  }
  ctx.globalAlpha = 1;
}

var _brainSSE = null;
var _brainSSEConnected = false;

function _updateBrainLiveIndicator(connected) {
  _brainSSEConnected = connected;
  var el = document.getElementById('brain-live-indicator');
  if (!el) return;
  if (connected) {
    el.innerHTML = '<span style="display:inline-flex;align-items:center;gap:4px;background:rgba(34,197,94,0.15);color:#22c55e;padding:2px 10px;border-radius:10px;font-size:11px;font-weight:700;"><span style="width:7px;height:7px;border-radius:50%;background:#22c55e;animation:livePulse 1.5s ease-in-out infinite;"></span> LIVE</span>';
  } else {
    el.innerHTML = '<span style="display:inline-flex;align-items:center;gap:4px;background:rgba(100,100,100,0.15);color:#888;padding:2px 10px;border-radius:10px;font-size:11px;font-weight:600;">● POLLING</span>';
  }
}

function _startBrainSSE() {
  if (_brainSSE) { try { _brainSSE.close(); } catch(e){} }
  _brainSSE = null;
  _brainSSEConnected = false;

  try {
    var url = '/api/brain-stream';
    var token = localStorage.getItem('gw_token');
    if (token) url += '?token=' + encodeURIComponent(token);
    var es = new EventSource(url);
    _brainSSE = es;

    es.addEventListener('connected', function() {
      _updateBrainLiveIndicator(true);
    });

    es.onmessage = function(e) {
      try {
        var ev = JSON.parse(e.data);
        if (!ev || !ev.time) return;
        // Prepend to events array
        _brainAllEvents.unshift(ev);
        // Cap at 500 events
        if (_brainAllEvents.length > 500) _brainAllEvents = _brainAllEvents.slice(0, 500);
        // Re-render with current filters
        renderBrainStream(_brainAllEvents);
        renderBrainChart(_brainAllEvents);
        if (typeof syncBrainGraph === 'function') syncBrainGraph(_brainAllEvents);
        // Update source chips if new source
        var known = document.querySelector('[data-source="' + ev.source + '"]');
        if (!known && ev.source !== 'all') {
          renderBrainFilterChips(_buildSourcesList(_brainAllEvents));
        }
        renderBrainTypeChips(_brainAllEvents);
        // Flash new-event pill
        var pill = document.getElementById('brain-new-pill');
        var streamEl = document.getElementById('brain-stream');
        if (pill && streamEl && streamEl.scrollTop > 60) {
          pill.style.display = '';
          clearTimeout(pill._hideTimer);
          pill._hideTimer = setTimeout(function(){ pill.style.display = 'none'; }, 5000);
        }
      } catch(err) {}
    };

    es.onerror = function() {
      _updateBrainLiveIndicator(false);
      try { es.close(); } catch(e){}
      _brainSSE = null;
      // Fall back to polling
      if (document.getElementById('page-brain') && document.getElementById('page-brain').classList.contains('active')) {
        _brainRefreshTimer = setTimeout(function() { loadBrainPage(true); }, 5000);
      }
    };

    es.addEventListener('done', function() {
      _updateBrainLiveIndicator(false);
      try { es.close(); } catch(e){}
      _brainSSE = null;
      // Reconnect after a short delay
      if (document.getElementById('page-brain') && document.getElementById('page-brain').classList.contains('active')) {
        setTimeout(_startBrainSSE, 2000);
      }
    });
  } catch(e) {
    _updateBrainLiveIndicator(false);
  }
}

function _stopBrainSSE() {
  if (_brainSSE) { try { _brainSSE.close(); } catch(e){} }
  _brainSSE = null;
  _updateBrainLiveIndicator(false);
}

function _buildSourcesList(events) {
  var seen = {};
  var sources = [];
  events.forEach(function(ev) {
    if (!seen[ev.source]) {
      seen[ev.source] = true;
      sources.push({id: ev.source, label: ev.sourceLabel || ev.source, color: ev.color || '#888'});
    }
  });
  return sources;
}

// ── LLM Context Inspector ─────────────────────────────────────────────────
async function loadContextInspector() {
  try {
    // Fetch overview for model + token info
    var ov = await fetch('/api/overview').then(function(r){return r.json();}).catch(function(){return {};});
    // Fetch brain history for compaction events + turn count
    var brain = await fetch('/api/brain-history').then(function(r){return r.json();}).catch(function(){return {events:[]};});
    // Fetch skills for header token count
    var skills = await fetch('/api/skills').then(function(r){return r.json();}).catch(function(){return {skills:[],summary:{}};});

    var contextWindow = ov.contextWindow || 200000;
    var mainTokens = ov.mainTokens || 0;
    var model = ov.model || 'unknown';
    var events = brain.events || [];

    // Context window usage bar
    var pct = contextWindow > 0 ? Math.min(100, Math.round(mainTokens / contextWindow * 100)) : 0;
    var usageFill = document.getElementById('ctx-usage-fill');
    if (usageFill) usageFill.style.width = pct + '%';
    var usageText = document.getElementById('ctx-usage-text');
    if (usageText) usageText.textContent = _fmtTokens(mainTokens) + ' / ' + _fmtTokens(contextWindow) + ' tokens (' + pct + '%)';
    var windowMax = document.getElementById('ctx-window-max');
    if (windowMax) windowMax.textContent = _fmtTokens(contextWindow);
    var threshold = document.getElementById('ctx-compact-threshold');
    if (threshold) threshold.textContent = 'Compaction at ~' + _fmtTokens(Math.round(contextWindow * 0.8));

    // Stats cards
    var turns = events.filter(function(e){return e.type === 'USER';}).length;
    var compactions = events.filter(function(e){return e.type === 'CONTEXT' && (e.detail||'').indexOf('Compact') >= 0;}).length;
    var el;
    el = document.getElementById('ctx-total-turns'); if (el) el.textContent = turns;
    el = document.getElementById('ctx-compactions'); if (el) el.textContent = compactions;
    el = document.getElementById('ctx-model-name'); if (el) { el.textContent = model.split('/').pop(); el.style.fontSize = model.length > 20 ? '14px' : '20px'; }

    // Context composition breakdown
    var skillHeaderTokens = (skills.summary || {}).total_header_tokens || 0;
    var memoryFiles = ov.memoryCount || 0;
    var memorySize = ov.memorySize || 0;
    var memoryTokens = Math.round(memorySize / 4); // rough estimate

    // Estimate system prompt sections based on known OpenClaw structure
    var sections = [
      {name: '## Tooling', tokens: Math.round(contextWindow * 0.015), color: '#3b82f6', desc: 'Tool list + descriptions'},
      {name: '## Safety', tokens: 120, color: '#ef4444', desc: 'Safety guardrails'},
      {name: '## Skills', tokens: skillHeaderTokens || Math.round(contextWindow * 0.008), color: '#f59e0b', desc: (skills.skills||[]).length + ' skill headers always loaded'},
      {name: '## Memories', tokens: 200, color: '#8b5cf6', desc: 'Memory tool guidance'},
      {name: '## Workspace', tokens: 150, color: '#06b6d4', desc: 'Working directory + docs path'},
      {name: '## Heartbeats', tokens: 80, color: '#10b981', desc: 'Heartbeat prompt'},
      {name: 'Bootstrap: SOUL.md', tokens: memoryTokens > 0 ? Math.min(5000, Math.round(memoryTokens * 0.2)) : 750, color: '#e879f9', desc: 'Agent identity + personality'},
      {name: 'Bootstrap: AGENTS.md', tokens: memoryTokens > 0 ? Math.min(5000, Math.round(memoryTokens * 0.15)) : 500, color: '#c084fc', desc: 'Workspace configuration'},
      {name: 'Bootstrap: TOOLS.md', tokens: memoryTokens > 0 ? Math.min(5000, Math.round(memoryTokens * 0.1)) : 400, color: '#a78bfa', desc: 'Custom tool instructions'},
      {name: 'Bootstrap: MEMORY.md', tokens: memoryTokens > 0 ? Math.min(5000, Math.round(memoryTokens * 0.3)) : 1000, color: '#818cf8', desc: 'Persistent agent memory'},
      {name: 'Tool schemas (JSON)', tokens: Math.round(contextWindow * 0.035), color: '#64748b', desc: 'Hidden but counted in context'},
      {name: 'Conversation history', tokens: Math.max(0, mainTokens - Math.round(contextWindow * 0.08)), color: '#22c55e', desc: 'Recent messages + tool results'},
    ];

    var totalSysPrompt = 0;
    sections.forEach(function(s) { if (s.name.indexOf('Conversation') === -1) totalSysPrompt += s.tokens; });
    var sysTotalEl = document.getElementById('ctx-sysprompt-total');
    if (sysTotalEl) sysTotalEl.textContent = '~' + _fmtTokens(totalSysPrompt) + ' tokens (estimated)';

    // Render composition bars
    var barsEl = document.getElementById('ctx-composition-bars');
    if (barsEl) {
      var maxTokens = Math.max.apply(null, sections.map(function(s){return s.tokens;}));
      var html = '';
      sections.forEach(function(s) {
        var barPct = maxTokens > 0 ? Math.max(1, Math.round(s.tokens / maxTokens * 100)) : 0;
        html += '<div style="display:flex;align-items:center;gap:8px;margin-bottom:6px;">';
        html += '<div style="min-width:160px;font-size:11px;color:var(--text-secondary);white-space:nowrap;">' + escHtml(s.name) + '</div>';
        html += '<div style="flex:1;height:14px;background:var(--bg-primary);border-radius:4px;overflow:hidden;border:1px solid var(--border);">';
        html += '<div style="height:100%;width:' + barPct + '%;background:' + s.color + ';border-radius:4px;transition:width 0.5s;"></div>';
        html += '</div>';
        html += '<div style="min-width:70px;text-align:right;font-size:11px;color:var(--text-muted);font-family:monospace;">' + _fmtTokens(s.tokens) + '</div>';
        html += '</div>';
      });
      barsEl.innerHTML = html;
    }

    // Render system prompt sections (expandable)
    var secEl = document.getElementById('ctx-sysprompt-sections');
    if (secEl) {
      var html = '';
      sections.filter(function(s){return s.name.indexOf('Conversation') === -1;}).forEach(function(s) {
        html += '<div style="display:flex;align-items:center;gap:8px;padding:6px 0;border-bottom:1px solid rgba(255,255,255,0.04);">';
        html += '<span style="width:8px;height:8px;border-radius:50%;background:' + s.color + ';flex-shrink:0;"></span>';
        html += '<span style="font-size:12px;color:var(--text-primary);min-width:160px;">' + escHtml(s.name) + '</span>';
        html += '<span style="font-size:11px;color:var(--text-muted);flex:1;">' + escHtml(s.desc) + '</span>';
        html += '<span style="font-size:11px;color:var(--text-secondary);font-family:monospace;">' + _fmtTokens(s.tokens) + '</span>';
        html += '</div>';
      });
      secEl.innerHTML = html;
    }

    // Compaction log
    var compactionEvents = events.filter(function(e) {
      return e.type === 'CONTEXT' && (e.detail||'').toLowerCase().indexOf('compact') >= 0;
    });
    var logEl = document.getElementById('ctx-compaction-log');
    if (logEl) {
      if (compactionEvents.length === 0) {
        logEl.innerHTML = '<div style="color:var(--text-muted);font-size:12px;padding:8px;">No compactions yet. Context hasn\'t exceeded the ~' + _fmtTokens(Math.round(contextWindow * 0.8)) + ' threshold.</div>';
      } else {
        var html = '';
        compactionEvents.forEach(function(ev) {
          html += '<div style="padding:8px 0;border-bottom:1px solid rgba(255,255,255,0.04);font-size:12px;">';
          html += '<span style="color:var(--text-muted);margin-right:8px;">' + formatBrainTime(ev.time) + '</span>';
          html += '<span style="color:#f59e0b;font-weight:600;">Compaction</span> ';
          html += '<span style="color:var(--text-secondary);">' + escHtml((ev.detail||'').substring(0, 200)) + '</span>';
          html += '</div>';
        });
        logEl.innerHTML = html;
      }
    }
  } catch(e) {
    var barsEl = document.getElementById('ctx-composition-bars');
    if (barsEl) barsEl.innerHTML = '<div style="color:var(--text-error);font-size:12px;">Error loading context data: ' + escHtml(String(e)) + '</div>';
  }
}

function _fmtTokens(n) {
  if (n >= 1000000) return (n / 1000000).toFixed(1) + 'M';
  if (n >= 1000) return (n / 1000).toFixed(1) + 'K';
  return String(n);
}

// ── Advisor: natural-language Q&A over the agent's recent activity ─────────
async function advisorProbe() {
  try {
    var s = await fetchJsonWithTimeout('/api/advisor/status', 3000);
    if (s && s.available) {
      var card = document.getElementById('advisor-card');
      if (card) card.style.display = '';
    }
  } catch (e) { /* keep hidden */ }
}
window.advisorPrefill = function (q) {
  var el = document.getElementById('advisor-q');
  if (el) { el.value = q; el.focus(); }
};
// Minimal markdown renderer — bold, italic, inline code, paragraph breaks.
// Escapes HTML first so LLM output can't inject tags.
function advisorRenderMarkdown(text) {
  var esc = String(text || '')
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  // Inline code `x` — process FIRST so asterisks inside code aren't misread
  esc = esc.replace(/`([^`\n]+)`/g, '<code style="background:rgba(168,85,247,0.18);padding:2px 6px;border-radius:4px;font-family:ui-monospace,Menlo,monospace;font-size:12.5px;color:#ddd6fe;">$1</code>');
  // Bold **x** and __x__
  esc = esc.replace(/\*\*([^\*\n]+)\*\*/g, '<strong style="color:#fff;font-weight:600;">$1</strong>');
  esc = esc.replace(/__([^_\n]+)__/g, '<strong style="color:#fff;font-weight:600;">$1</strong>');
  // Italic *x* and _x_ — require non-space boundary to avoid matching snake_case
  esc = esc.replace(/(^|[\s\(])\*([^\*\n]+)\*/g, '$1<em>$2</em>');
  esc = esc.replace(/(^|[\s\(])_([^_\n]+)_(?=$|[\s\.,\)])/g, '$1<em>$2</em>');
  // Paragraph breaks on blank line; single newlines become <br>
  var paras = esc.split(/\n{2,}/).map(function (p) {
    return '<p style="margin:0 0 10px 0;">' + p.replace(/\n/g, '<br>') + '</p>';
  });
  // Drop trailing empty paragraph
  return paras.join('').replace(/<p[^>]*>\s*<\/p>/g, '');
}

window.advisorAsk = async function () {
  var input = document.getElementById('advisor-q');
  var wrap = document.getElementById('advisor-answer-wrap');
  var qEl = document.getElementById('advisor-answer-q');
  var out = document.getElementById('advisor-answer');
  var metaEl = document.getElementById('advisor-answer-meta');
  var q = (input && input.value || '').trim();
  if (!q || !wrap || !out) return;
  wrap.style.display = '';
  if (qEl) qEl.textContent = '› ' + q;
  out.innerHTML = '<span style="color:#a855f7;">Thinking…</span>';
  if (metaEl) metaEl.textContent = '';
  try {
    var resp = await fetch('/api/advisor/ask', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question: q }),
    });
    var d = await resp.json();
    if (!resp.ok) {
      out.textContent = (d && d.message) || (d && d.detail) || ('Error ' + resp.status);
      return;
    }
    out.innerHTML = advisorRenderMarkdown(d.answer || '(empty answer)');
    if (metaEl) {
      var parts = [];
      if (d.model) parts.push(d.model);
      var totalTokens = (d.input_tokens || 0) + (d.output_tokens || 0);
      if (totalTokens) parts.push(totalTokens + ' tokens');
      if (typeof d.events_in_context === 'number') parts.push(d.events_in_context + ' events in context');
      metaEl.textContent = parts.length ? parts.join(' · ') : '';
    }
  } catch (e) {
    out.textContent = 'Network error: ' + e.message;
  }
};

// ── Self-Evolve: LLM-backed standing review of the agent's trajectory ─────
function selfevolveSeverityColor(sev) {
  if (sev === 'high') return { bg: 'rgba(239,68,68,0.12)', border: '#ef4444', text: '#fca5a5' };
  if (sev === 'low')  return { bg: 'rgba(16,185,129,0.1)', border: '#10b981', text: '#6ee7b7' };
  return { bg: 'rgba(234,179,8,0.12)', border: '#eab308', text: '#fde68a' };
}
function selfevolveCategoryIcon(cat) {
  return ({
    cost: '💰', reliability: '⚠️', latency: '🐢',
    prompt: '📝', model: '🎛️', loop: '🔁',
  })[cat] || '•';
}
function selfevolveRenderFindings(payload) {
  var container = document.getElementById('selfevolve-findings');
  var status = document.getElementById('selfevolve-status');
  if (!container) return;
  container.innerHTML = '';
  var findings = (payload && payload.findings) || [];
  if (payload && payload.insufficient) {
    container.innerHTML = '<div style="padding:10px 12px;color:var(--text-muted);font-size:12px;">' +
      'Not enough data yet — ' + (payload.reason || 'keep the agent running for a while') + '</div>';
  } else if (!findings.length) {
    container.innerHTML = '<div style="padding:10px 12px;color:var(--text-muted);font-size:12px;">' +
      'No findings yet. Click Analyze to review recent activity.</div>';
  } else {
    findings.forEach(function (f) {
      var col = selfevolveSeverityColor(f.severity);
      var card = document.createElement('div');
      card.style.cssText =
        'padding:10px 12px;background:' + col.bg + ';border:1px solid ' + col.border + ';' +
        'border-left-width:3px;border-radius:6px;';
      card.innerHTML =
        '<div style="display:flex;justify-content:space-between;align-items:center;gap:8px;margin-bottom:6px;">' +
          '<div style="font-size:13px;font-weight:600;color:var(--text-primary);">' +
            selfevolveCategoryIcon(f.category) + ' ' + (f.title || '(untitled)') +
          '</div>' +
          '<span style="font-size:10px;font-weight:700;text-transform:uppercase;color:' + col.text +
            ';padding:2px 8px;border-radius:10px;border:1px solid ' + col.border + ';">' +
            (f.severity || 'medium') +
          '</span>' +
        '</div>' +
        (f.evidence ? '<div style="font-size:12px;color:var(--text-muted);margin-bottom:6px;line-height:1.5;">' +
          '<strong style="color:var(--text-secondary);">Evidence:</strong> ' + escapeHtml(f.evidence) + '</div>' : '') +
        (f.suggestion ? '<div style="font-size:12px;color:var(--text-primary);line-height:1.5;">' +
          '<strong style="color:#60a5fa;">Try:</strong> ' + escapeHtml(f.suggestion) + '</div>' : '');
      container.appendChild(card);
    });
  }
  if (status) {
    var meta = [];
    if (payload.generated_at) meta.push('analyzed ' + new Date(payload.generated_at * 1000).toLocaleTimeString());
    if (payload.events_considered) meta.push(payload.events_considered + ' events');
    if (payload.model) meta.push(payload.model);
    status.textContent = meta.join(' · ');
  }
}
// Self-Evolve is intentionally NOT in the top nav (option C: discoverable via
// a contextual link on the Brain tab + deep-link). The probe's job here is
// twofold: (1) reveal the contextual link inside the Advisor card when auth
// is available, and (2) on direct visits to #selfevolve, render the cached
// payload or show the appropriate empty/no-auth state.
async function selfevolveProbe() {
  try {
    var s = await fetchJsonWithTimeout('/api/selfevolve/status', 3000);
    var hint = document.getElementById('advisor-selfevolve-hint');
    var noauth = document.getElementById('selfevolve-noauth');
    var empty = document.getElementById('selfevolve-empty');
    var runBtn = document.getElementById('selfevolve-run-btn');
    if (!s || !s.available) {
      if (hint) hint.style.display = 'none';
      if (noauth) noauth.style.display = '';
      if (runBtn) runBtn.disabled = true;
      return;
    }
    if (hint) hint.style.display = '';
    if (noauth) noauth.style.display = 'none';
    if (s.has_cached) {
      try {
        var cached = await fetchJsonWithTimeout('/api/selfevolve/latest', 3000);
        if (cached && (cached.findings || []).length) {
          selfevolveRenderFindings(cached);
          if (runBtn) runBtn.textContent = 'Re-analyze';
          return;
        }
      } catch (e) { /* fall through to empty state */ }
    }
    if (empty) empty.style.display = '';
  } catch (e) { /* silent */ }
}
async function loadSelfEvolvePage() {
  return selfevolveProbe();
}
window.selfevolveRun = async function () {
  var btn = document.getElementById('selfevolve-run-btn');
  var status = document.getElementById('selfevolve-status');
  var origText = btn ? btn.textContent : '';
  if (btn) { btn.disabled = true; btn.textContent = 'Analyzing…'; btn.style.opacity = '0.6'; }
  if (status) status.textContent = 'Reviewing recent activity — this takes ~15 seconds…';
  try {
    var resp = await fetch('/api/selfevolve/analyze', { method: 'POST' });
    var d = await resp.json();
    if (!resp.ok) {
      if (status) status.textContent = (d && d.message) || (d && d.detail) || ('Error ' + resp.status);
      return;
    }
    selfevolveRenderFindings(d);
  } catch (e) {
    if (status) status.textContent = 'Network error: ' + e.message;
  } finally {
    if (btn) { btn.disabled = false; btn.textContent = '🔄 Re-analyze'; btn.style.opacity = ''; }
  }
};

async function loadBrainPage(silent) {
  if (window.CLOUD_MODE) return;
  if (!silent) { advisorProbe(); selfevolveProbe(); }
  try {
    var data = await fetchJsonWithTimeout('/api/brain-history', 8000);
    var events = (data.events || []).slice().sort(function(a,b){
      var ta = a.time ? new Date(a.time).getTime() : 0;
      var tb = b.time ? new Date(b.time).getTime() : 0;
      return tb - ta;
    });
    _brainAllEvents = events;
    renderBrainFilterChips(data.sources || []);
    renderBrainTypeChips(events);
    // Channel filter chips
    window._brainChannelCounts = data.channels || {};
    if (!Object.keys(window._brainChannelCounts).length) {
      // Build from events if API didn't provide
      events.forEach(function(ev) { if (ev.channel) window._brainChannelCounts[ev.channel] = (window._brainChannelCounts[ev.channel]||0) + 1; });
    }
    renderBrainChannelChips(window._brainChannelCounts);
    renderBrainChart(events);
    if (typeof syncBrainGraph === 'function') syncBrainGraph(events);
    var streamEl = document.getElementById('brain-stream');
    var wasAtTop = !streamEl || streamEl.scrollTop < 40;
    renderBrainStream(events);
  } catch(e) {
    if (!silent) {
      var el = document.getElementById('brain-stream');
      if (el) el.innerHTML = '<div style="color:var(--text-error);padding:20px">Failed to load: ' + escHtml(String(e)) + '</div>';
    }
  }
  // After initial load, start SSE for live updates instead of polling
  if (!_brainSSE && !_brainSSEConnected) {
    _startBrainSSE();
  }
  // Only poll as fallback if SSE is not connected
  if (_brainRefreshTimer) clearTimeout(_brainRefreshTimer);
  if (!_brainSSEConnected && document.getElementById('page-brain') && document.getElementById('page-brain').classList.contains('active')) {
    _brainRefreshTimer = setTimeout(function() { loadBrainPage(true); }, 5000);
  }
}


// ── Security Threat Detection ──────────────────────────────────────────────
var _securityFilter = 'all';
var _securityAllThreats = [];
var _securityRefreshTimer = null;

var _severityColors = {critical:'#ef4444', high:'#f59e0b', medium:'#3b82f6', low:'#64748b', info:'#22c55e'};

function setSecurityFilter(sev, btn) {
  _securityFilter = sev;
  document.querySelectorAll('#security-filter-pills .brain-chip').forEach(function(c){
    c.classList.remove('active');
    c.style.background = 'transparent';
  });
  btn.classList.add('active');
  btn.style.background = 'rgba(' + (sev==='critical'?'239,68,68':sev==='high'?'245,158,11':sev==='medium'?'59,130,246':sev==='low'?'100,116,139':'168,85,247') + ',0.2)';
  renderSecurityThreats(_securityAllThreats);
}

function renderSecurityThreats(threats) {
  var el = document.getElementById('security-threat-list');
  if (!el) return;
  var filtered = _securityFilter === 'all' ? threats : threats.filter(function(t){return t.severity === _securityFilter;});
  var label = document.getElementById('sec-total-label');
  if (label) label.textContent = filtered.length + ' threat' + (filtered.length!==1?'s':'') + ' found';
  if (filtered.length === 0) {
    el.innerHTML = '<div style="color:#22c55e;padding:20px;text-align:center;font-size:13px;">&#9989; No threats detected' + (_securityFilter!=='all'?' at this severity level':'') + '</div>';
    return;
  }
  var html = '';
  filtered.forEach(function(t){
    var sColor = _severityColors[t.severity] || '#888';
    var sevBadge = '<span style="display:inline-block;padding:1px 8px;border-radius:4px;font-size:10px;font-weight:700;color:#fff;background:' + sColor + ';min-width:55px;text-align:center;">' + (t.severity||'?').toUpperCase() + '</span>';
    var time = t.time ? new Date(t.time).toLocaleTimeString() : '';
    html += '<div class="brain-event" style="border-left:3px solid ' + sColor + ';padding-left:10px;margin-bottom:4px;">';
    html += '<span class="brain-time">' + escHtml(time) + '</span>';
    html += sevBadge + ' ';
    html += '<span style="font-weight:600;color:var(--text-primary);min-width:140px;display:inline-block;">' + escHtml(t.rule_id || '') + '</span>';
    html += '<span class="brain-detail" style="white-space:normal;">' + escHtml(t.detail || '') + '</span>';
    if (t.session) html += ' <span style="color:var(--text-muted);font-size:10px;">[' + escHtml(t.session) + ']</span>';
    html += '</div>';
  });
  el.innerHTML = html;
}

function toggleSecCatalog() {
  var el = document.getElementById('sec-catalog');
  var arrow = document.getElementById('sec-catalog-arrow');
  if (!el) return;
  if (el.style.display === 'none') {
    el.style.display = 'block';
    if (arrow) arrow.innerHTML = '&#9660;';
    loadSecCatalog();
  } else {
    el.style.display = 'none';
    if (arrow) arrow.innerHTML = '&#9654;';
  }
}

async function loadSecCatalog() {
  var el = document.getElementById('sec-catalog');
  if (!el) return;
  try {
    var data = await fetchJsonWithTimeout('/api/security/signatures', 5000);
    var sigs = data.signatures || [];
    if (sigs.length === 0) { el.innerHTML = '<div style="color:var(--text-muted);font-size:11px;">No signatures loaded</div>'; return; }
    var html = '<table style="width:100%;font-size:11px;border-collapse:collapse;">';
    html += '<tr style="color:var(--text-muted);border-bottom:1px solid var(--border);"><th style="text-align:left;padding:4px;">ID</th><th style="text-align:left;padding:4px;">Severity</th><th style="text-align:left;padding:4px;">Description</th><th style="text-align:left;padding:4px;">Pattern</th></tr>';
    sigs.forEach(function(s){
      var sColor = _severityColors[s.severity] || '#888';
      html += '<tr style="border-bottom:1px solid var(--border);">';
      html += '<td style="padding:4px;font-family:monospace;color:var(--text-primary);">' + escHtml(s.id) + '</td>';
      html += '<td style="padding:4px;"><span style="color:' + sColor + ';font-weight:600;">' + escHtml((s.severity||'').toUpperCase()) + '</span></td>';
      html += '<td style="padding:4px;color:var(--text-secondary);">' + escHtml(s.description) + '</td>';
      html += '<td style="padding:4px;font-family:monospace;font-size:10px;color:var(--text-muted);">' + escHtml(s.pattern || '') + '</td>';
      html += '</tr>';
    });
    html += '</table>';
    el.innerHTML = html;
  } catch(e) {
    el.innerHTML = '<div style="color:var(--text-error);font-size:11px;">Failed to load: ' + escHtml(String(e)) + '</div>';
  }
}

// ── NemoClaw Governance Tab ───────────────────────────────────────────────────
async function loadNemoClaw() {
  var page = document.getElementById('page-nemoclaw');
  if (!page) return;
  try {
    var data = await fetchJsonWithTimeout('/api/nemoclaw/governance', 8000);
    var tab = document.getElementById('nemoclaw-tab');

    if (!data.installed) {
      if (tab) tab.style.display = 'none';
      page.innerHTML = '<div style="padding:40px 20px;text-align:center;color:var(--text-muted);font-size:14px;">NemoClaw not installed on this host.<br><span style="font-size:12px;">Install via <code style="background:var(--bg-secondary);padding:2px 6px;border-radius:3px;">pip install nemoclaw</code></span></div>';
      return;
    }

    // Show tab
    if (tab) tab.style.display = '';

    // Status dot
    var sandboxes = data.sandboxes || [];
    var anyRunning = sandboxes.some(function(s) { return s.status === 'running' || s.status === 'active'; });
    var dot = document.getElementById('nc-status-dot');
    if (dot) dot.textContent = anyRunning ? '🟢' : '⚪';

    // Sandbox name / count badge
    var nameBadge = document.getElementById('nc-sandbox-name');
    if (nameBadge) nameBadge.textContent = sandboxes.length ? sandboxes.length + ' sandbox' + (sandboxes.length !== 1 ? 'es' : '') : 'no sandboxes';

    // Policy hash badge
    var policyEl = document.getElementById('nc-policy-hash');
    var policy = data.policy || {};
    if (policyEl) policyEl.textContent = policy.hash ? 'sha:' + policy.hash : '';

    // Blueprint version badge
    var bpVer = document.getElementById('nc-blueprint-ver');
    var bpVer2 = document.getElementById('nc-blueprint-ver2');
    var cfg = data.config || {};
    var ver = cfg.version || cfg.blueprintVersion || (policy.lines ? policy.lines + ' lines' : '');
    if (bpVer) bpVer.textContent = ver ? 'v' + ver : '';
    if (bpVer2) bpVer2.textContent = ver || '—';

    // Sandbox status
    var sbStatus = document.getElementById('nc-sandbox-status');
    if (sbStatus) {
      if (sandboxes.length === 0) {
        sbStatus.textContent = 'no sandboxes';
        sbStatus.style.color = 'var(--text-muted)';
      } else {
        var running = sandboxes.filter(function(s) { return s.status === 'running' || s.status === 'active'; }).length;
        sbStatus.textContent = running + '/' + sandboxes.length + ' running';
        sbStatus.style.color = running > 0 ? '#76b900' : 'var(--text-muted)';
      }
    }

    // Inference info from config
    var provEl = document.getElementById('nc-provider');
    var mdlEl = document.getElementById('nc-model');
    var epEl = document.getElementById('nc-endpoint');
    var obEl = document.getElementById('nc-onboarded');
    if (provEl) provEl.textContent = cfg.inferenceProvider || cfg.provider || '—';
    if (mdlEl) mdlEl.textContent = cfg.model || cfg.inferenceModel || '—';
    if (epEl) epEl.textContent = cfg.endpoint || cfg.inferenceEndpoint || '—';
    if (obEl) obEl.textContent = cfg.onboardedAt || cfg.createdAt || '—';

    // Last action / run id
    var laEl = document.getElementById('nc-last-action');
    var riEl = document.getElementById('nc-run-id');
    var state = cfg.state || {};
    if (laEl) laEl.textContent = state.lastAction || cfg.lastAction || '—';
    if (riEl) riEl.textContent = state.runId || cfg.runId || '—';

    // Drift alert
    var driftAlert = document.getElementById('nc-drift-alert');
    var driftDetail = document.getElementById('nc-drift-detail');
    var driftBadge = document.getElementById('nc-drift-badge');
    if (data.drift) {
      if (driftAlert) driftAlert.style.display = '';
      if (driftDetail) driftDetail.textContent = 'Previous: ' + (data.drift.previous_hash || data.drift.old_hash || '?') + ' → Current: ' + (data.drift.current_hash || data.drift.new_hash || '?') + (data.drift.detected_at ? '  (detected ' + data.drift.detected_at.substring(0,19).replace('T',' ') + ' UTC)' : '');
      if (driftBadge) { driftBadge.textContent = '⚠ Policy drift detected'; driftBadge.style.cssText = 'font-size:11px;font-weight:700;color:#ef4444;background:rgba(239,68,68,0.1);border:1px solid rgba(239,68,68,0.3);border-radius:4px;padding:2px 8px;'; }
    } else {
      if (driftAlert) driftAlert.style.display = 'none';
      if (driftBadge) { driftBadge.textContent = '✓ No drift'; driftBadge.style.cssText = 'font-size:11px;font-weight:600;color:#76b900;'; }
    }

    // Network policies table
    var netPol = data.network_policies || [];
    var tbl = document.getElementById('nc-policy-table');
    if (tbl) {
      if (netPol.length === 0 && !policy.hash) {
        tbl.innerHTML = '<div style="color:var(--text-muted);font-size:12px;">No policy file found at ~/.nemoclaw/source/nemoclaw-blueprint/policies/openclaw-sandbox.yaml</div>';
      } else if (netPol.length === 0) {
        tbl.innerHTML = '<div style="color:var(--text-muted);font-size:12px;">Policy loaded (' + (policy.lines || '?') + ' lines) — no network_policies section found.</div>';
      } else {
        var html = '<div style="display:grid;grid-template-columns:1fr 2fr;gap:6px;">';
        netPol.forEach(function(p) {
          html += '<div style="font-weight:600;color:#76b900;padding:4px 0;border-bottom:1px solid var(--border);">' + escHtml(p.name) + '</div>';
          html += '<div style="color:var(--text-secondary);padding:4px 0;border-bottom:1px solid var(--border);word-break:break-all;">' + (p.hosts || []).map(function(h) { return '<span style="background:var(--bg-primary);border:1px solid var(--border);border-radius:3px;padding:1px 5px;margin:1px;display:inline-block;">' + escHtml(h) + '</span>'; }).join(' ') + '</div>';
        });
        html += '</div>';
        tbl.innerHTML = html;
      }
    }

    // Presets
    var presetsEl = document.getElementById('nc-presets');
    if (presetsEl) {
      var presets = data.presets || [];
      if (presets.length === 0) {
        presetsEl.innerHTML = '<span style="color:var(--text-muted);font-size:12px;">None detected</span>';
      } else {
        presetsEl.innerHTML = presets.map(function(p) {
          return '<span style="background:rgba(118,185,0,0.1);border:1px solid rgba(118,185,0,0.25);color:#76b900;border-radius:12px;padding:3px 10px;font-size:12px;font-weight:600;">' + escHtml(p) + '</span>';
        }).join('');
      }
    }

  } catch(e) {
    var tab = document.getElementById('nemoclaw-tab');
    if (tab) tab.style.display = 'none';
    console.warn('NemoClaw governance load failed:', e);
  }
  // Also load approvals
  loadNemoClawApprovals();
}

// Auto-refresh approvals every 15 seconds when NemoClaw tab is active
var _ncApprovalsTimer = null;
function _startNcApprovalsAutoRefresh() {
  if (_ncApprovalsTimer) return;
  loadNemoClawApprovals();
  _ncApprovalsTimer = setInterval(loadNemoClawApprovals, 15000);
}
function _stopNcApprovalsAutoRefresh() {
  if (_ncApprovalsTimer) { clearInterval(_ncApprovalsTimer); _ncApprovalsTimer = null; }
}

async function loadNemoClawApprovals() {
  var listEl = document.getElementById('nc-approvals-list');
  var countEl = document.getElementById('nc-approvals-count');
  if (!listEl) return;
  try {
    var data = await fetchJsonWithTimeout('/api/nemoclaw/pending-approvals', 8000);
    if (!data.installed) {
      listEl.innerHTML = '<div style="color:var(--text-muted);font-size:12px;padding:6px 0;">openshell not available on this host</div>';
      if (countEl) countEl.style.display = 'none';
      return;
    }
    var approvals = data.approvals || [];
    if (countEl) {
      if (approvals.length > 0) {
        countEl.textContent = approvals.length;
        countEl.style.display = '';
      } else {
        countEl.style.display = 'none';
      }
    }
    if (approvals.length === 0) {
      listEl.innerHTML = '<div style="color:var(--text-muted);font-size:12px;padding:8px 0;text-align:center;">✓ No pending requests</div>';
      return;
    }
    var html = '';
    approvals.forEach(function(a) {
      var ruleDisplay = '';
      if (a.host) {
        ruleDisplay = escHtml(a.host);
        if (a.port) ruleDisplay += ':' + escHtml(String(a.port));
        if (a.protocol) ruleDisplay += ' (' + escHtml(a.protocol.toUpperCase()) + ')';
      } else if (a.rule_name) {
        ruleDisplay = escHtml(a.rule_name);
      }
      var timeAgo = '';
      if (a.ts) {
        try {
          var diff = Math.floor((Date.now() - new Date(a.ts).getTime()) / 1000);
          if (diff < 60) timeAgo = diff + 's ago';
          else if (diff < 3600) timeAgo = Math.floor(diff/60) + 'm ago';
          else timeAgo = Math.floor(diff/3600) + 'h ago';
        } catch(e) {}
      }
      html += '<div style="border:1px solid rgba(118,185,0,0.25);border-radius:6px;padding:12px;margin-bottom:8px;background:var(--bg-primary);">';
      html += '<div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:8px;">';
      html += '<div style="font-size:12px;">';
      html += '<span style="color:var(--text-muted);">sandbox: </span><span style="color:#76b900;font-weight:600;font-family:\'JetBrains Mono\',monospace;">' + escHtml(a.sandbox || '') + '</span>';
      if (a.rule_name) html += '<span style="color:var(--text-muted);margin-left:10px;">rule: </span><span style="color:var(--text-secondary);font-family:\'JetBrains Mono\',monospace;font-size:11px;">' + escHtml(a.rule_name) + '</span>';
      html += '</div>';
      if (timeAgo) html += '<span style="font-size:11px;color:var(--text-muted);">' + escHtml(timeAgo) + '</span>';
      html += '</div>';
      if (ruleDisplay) {
        html += '<div style="font-size:13px;font-weight:600;color:var(--text-primary);font-family:\'JetBrains Mono\',monospace;margin-bottom:10px;">' + ruleDisplay + '</div>';
      }
      var chunkId = escHtml(a.chunk_id || '');
      var sandbox = escHtml(a.sandbox || '');
      html += '<div style="display:flex;gap:8px;">';
      html += '<button onclick="ncApprove(\'' + sandbox + '\',\'' + chunkId + '\',this)" style="flex:1;padding:6px 12px;background:rgba(118,185,0,0.15);color:#76b900;border:1px solid rgba(118,185,0,0.4);border-radius:5px;cursor:pointer;font-size:12px;font-weight:600;">&#10003; Approve</button>';
      html += '<button onclick="ncReject(\'' + sandbox + '\',\'' + chunkId + '\',this)" style="flex:1;padding:6px 12px;background:rgba(239,68,68,0.1);color:#ef4444;border:1px solid rgba(239,68,68,0.3);border-radius:5px;cursor:pointer;font-size:12px;font-weight:600;">&#10007; Reject</button>';
      html += '</div>';
      html += '</div>';
    });
    listEl.innerHTML = html;
  } catch(e) {
    listEl.innerHTML = '<div style="color:var(--text-muted);font-size:12px;">Failed to load approvals</div>';
  }
}

async function ncApprove(sandbox, chunkId, btn) {
  if (btn) { btn.disabled = true; btn.textContent = 'Approving...'; }
  try {
    var resp = await fetch('/api/nemoclaw/approve', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({sandbox: sandbox, chunk_id: chunkId})
    });
    var data = await resp.json();
    if (data.ok) {
      setTimeout(loadNemoClawApprovals, 500);
    } else {
      if (btn) { btn.disabled = false; btn.textContent = '✓ Approve'; }
      alert('Approve failed: ' + (data.output || 'unknown error'));
    }
  } catch(e) {
    if (btn) { btn.disabled = false; btn.textContent = '✓ Approve'; }
    console.error('ncApprove error:', e);
  }
}

async function ncReject(sandbox, chunkId, btn) {
  var reason = window.prompt('Reject reason (optional):') || '';
  if (reason === null) return; // cancelled
  if (btn) { btn.disabled = true; btn.textContent = 'Rejecting...'; }
  try {
    var resp = await fetch('/api/nemoclaw/reject', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({sandbox: sandbox, chunk_id: chunkId, reason: reason})
    });
    var data = await resp.json();
    if (data.ok) {
      setTimeout(loadNemoClawApprovals, 500);
    } else {
      if (btn) { btn.disabled = false; btn.textContent = '✗ Reject'; }
      alert('Reject failed: ' + (data.output || 'unknown error'));
    }
  } catch(e) {
    if (btn) { btn.disabled = false; btn.textContent = '✗ Reject'; }
    console.error('ncReject error:', e);
  }
}

async function loadSecurityPosture() {
  // Cloud mode no longer short-circuits this — the daemon now collects
  // posture locally and pushes on its heartbeat, cloud stores it per node,
  // and `/api/security/posture` returns the synced snapshot. The cloud-
  // mode fetch shim auto-injects ?node_id=<current> + &token=<cm_> so the
  // call works against either OSS-local OR cloud-served handler.
  try {
    var data = await fetchJsonWithTimeout('/api/security/posture', 25000);
    var badge = document.getElementById('posture-score-badge');
    var label = document.getElementById('posture-score-label');
    var bar = document.getElementById('posture-score-bar');
    var passedEl = document.getElementById('posture-passed');
    var warnEl = document.getElementById('posture-warnings');
    var failedEl = document.getElementById('posture-failed');
    var listEl = document.getElementById('posture-checks-list');
    if (!badge) return;
    badge.textContent = data.score || '?';
    badge.style.background = data.score_color || '#64748b';
    label.textContent = (data.score_label || 'Unknown') + ' (' + (data.score_pct || 0) + '%)' + (data.config_path ? ' — ' + data.config_path : '');
    bar.style.width = (data.score_pct || 0) + '%';
    bar.style.background = data.score_color || '#64748b';
    passedEl.textContent = data.passed || 0;
    warnEl.textContent = data.warnings || 0;
    failedEl.textContent = data.failed || 0;
    var checks = data.checks || [];
    var html = '';
    var statusIcons = {'pass': '&#9989;', 'warn': '&#9888;&#65039;', 'fail': '&#10060;'};
    var statusColors = {'pass': '#22c55e', 'warn': '#f59e0b', 'fail': '#ef4444'};
    // Show failed first, then warnings, then passed
    checks.sort(function(a,b) {
      var order = {'fail': 0, 'warn': 1, 'pass': 2};
      return (order[a.status] || 2) - (order[b.status] || 2);
    });
    checks.forEach(function(c) {
      var icon = statusIcons[c.status] || '&#10067;';
      var color = statusColors[c.status] || '#64748b';
      html += '<div style="display:flex;align-items:flex-start;gap:8px;padding:8px 10px;background:var(--bg-primary);border:1px solid var(--border);border-radius:6px;border-left:3px solid ' + color + ';">';
      html += '<span style="font-size:14px;flex-shrink:0;">' + icon + '</span>';
      html += '<div style="flex:1;min-width:0;">';
      html += '<div style="font-size:12px;font-weight:600;color:var(--text-primary);">' + escHtml(c.label) + ' <span style="font-size:10px;color:' + color + ';font-weight:700;text-transform:uppercase;">' + escHtml(c.status) + '</span></div>';
      html += '<div style="font-size:11px;color:var(--text-secondary);margin-top:2px;">' + escHtml(c.detail) + '</div>';
      if (c.remediation) {
        html += '<div style="font-size:10px;color:#3b82f6;margin-top:3px;font-family:monospace;background:rgba(59,130,246,0.08);padding:3px 6px;border-radius:3px;">&#128736; ' + escHtml(c.remediation) + '</div>';
      }
      html += '</div></div>';
    });
    listEl.innerHTML = html;
  } catch(e) {
    var panel = document.getElementById('security-posture-panel');
    if (panel) panel.innerHTML = '<div style="color:var(--text-error);padding:10px;font-size:12px;">Posture scan failed: ' + escHtml(String(e)) + '</div>';
  }
}

async function loadSecurityPage(silent) {
  if (window.CLOUD_MODE) return;
  try {
    var data = await fetchJsonWithTimeout('/api/security/threats', 10000);
    var threats = data.threats || [];
    _securityAllThreats = threats;
    var counts = data.counts || {};
    document.getElementById('sec-critical-count').textContent = counts.critical || 0;
    document.getElementById('sec-high-count').textContent = counts.high || 0;
    document.getElementById('sec-medium-count').textContent = counts.medium || 0;
    document.getElementById('sec-clean-count').textContent = counts.clean_sessions || 0;
    var scanTime = document.getElementById('security-scan-time');
    if (scanTime) scanTime.textContent = 'Scanned ' + new Date().toLocaleTimeString();
    renderSecurityThreats(threats);
  } catch(e) {
    if (!silent) {
      var el = document.getElementById('security-threat-list');
      if (el) el.innerHTML = '<div style="color:var(--text-error);padding:20px">Scan failed: ' + escHtml(String(e)) + '</div>';
    }
  }
  if (_securityRefreshTimer) clearTimeout(_securityRefreshTimer);
  if (document.getElementById('page-security') && document.getElementById('page-security').classList.contains('active')) {
    _securityRefreshTimer = setTimeout(function() { loadSecurityPage(true); }, 30000);
  }
}






function openDetailView(type) {
  // Navigate to the appropriate tab with detail view
  if (type === 'cost') {
    openBudgetModal();
    return;
  } else if (type === 'tokens') {
    switchTab('usage');
  } else if (type === 'sessions') {
    showSessionsModal();
  } else if (type === 'tools') {
    switchTab('logs');
  } else {
    // For thinking feed and models, stay on overview but could expand in future
    alert('Detail view for ' + type + ' coming soon!');
  }
}

function showSessionsModal() {
  fetch('/api/sessions').then(r=>r.json()).then(function(d) {
    var sessions = d.sessions || d || [];
    if (!Array.isArray(sessions)) sessions = [];
    var html = '<div style="max-height:60vh;overflow-y:auto;">';
    if (!sessions.length) {
      html += '<div style="text-align:center;padding:32px;color:var(--text-muted);">No active sessions</div>';
    } else {
      html += '<table style="width:100%;border-collapse:collapse;font-size:12px;">';
      html += '<tr style="border-bottom:1px solid var(--border-primary);color:var(--text-muted);text-transform:uppercase;font-size:10px;letter-spacing:0.5px;">';
      html += '<th style="padding:8px;text-align:left;">Session</th><th style="padding:8px;text-align:left;">Kind</th><th style="padding:8px;text-align:right;">Tokens</th><th style="padding:8px;text-align:right;">Age</th></tr>';
      sessions.forEach(function(s) {
        var age = s.lastActivityAge || s.age || '';
        var tokens = s.totalTokens || s.tokens || 0;
        tokens = tokens > 1e6 ? (tokens/1e6).toFixed(1)+'M' : (tokens > 1e3 ? (tokens/1e3).toFixed(0)+'K' : tokens);
        var kind = s.kind || (s.sessionKey && s.sessionKey.includes('subagent') ? 'isolated' : 'main');
        var label = s.label || s.sessionKey || s.name || '--';
        var kindColor = kind === 'main' ? 'var(--text-success)' : kind === 'isolated' ? '#a78bfa' : 'var(--text-muted)';
        html += '<tr style="border-bottom:1px solid var(--border-primary);">';
        html += '<td style="padding:8px;color:var(--text-primary);font-weight:600;max-width:200px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">' + escHtml(label) + '</td>';
        html += '<td style="padding:8px;"><span style="color:'+kindColor+';font-size:10px;font-weight:600;text-transform:uppercase;">'+escHtml(kind)+'</span></td>';
        html += '<td style="padding:8px;text-align:right;color:var(--text-primary);font-family:monospace;">'+tokens+'</td>';
        html += '<td style="padding:8px;text-align:right;color:var(--text-muted);">'+escHtml(age)+'</td>';
        html += '</tr>';
      });
      html += '</table>';
    }
    html += '</div>';
    showGenericModal('💬 Active Sessions (' + sessions.length + ')', html);
  });
}

function showGenericModal(title, bodyHtml) {
  var existing = document.getElementById('generic-modal-overlay');
  if (existing) existing.remove();
  var overlay = document.createElement('div');
  overlay.id = 'generic-modal-overlay';
  overlay.style.cssText = 'position:fixed;inset:0;background:rgba(0,0,0,0.6);display:flex;align-items:center;justify-content:center;z-index:9999;backdrop-filter:blur(4px);';
  overlay.onclick = function(e) { if (e.target === overlay) overlay.remove(); };
  var modal = document.createElement('div');
  modal.style.cssText = 'background:var(--bg-secondary);border:1px solid var(--border-primary);border-radius:12px;padding:0;min-width:400px;max-width:600px;width:90%;box-shadow:0 20px 60px rgba(0,0,0,0.5);';
  modal.innerHTML = '<div style="padding:16px 20px;border-bottom:1px solid var(--border-primary);display:flex;align-items:center;justify-content:space-between;">'
    + '<span style="font-size:15px;font-weight:700;color:var(--text-primary);">'+title+'</span>'
    + '<span onclick="document.getElementById(\'generic-modal-overlay\').remove()" style="cursor:pointer;color:var(--text-muted);font-size:18px;">✕</span>'
    + '</div><div style="padding:16px 20px;">'+bodyHtml+'</div>';
  overlay.appendChild(modal);
  document.body.appendChild(overlay);
}

function renderLogs(elId, lines) {
  var html = '';
  lines.forEach(function(l) {
    var cls = 'msg';
    var display = l;
    try {
      var obj = JSON.parse(l);
      var ts = '';
      if (obj.time || (obj._meta && obj._meta.date)) {
        var d = new Date(obj.time || obj._meta.date);
        ts = d.toLocaleTimeString('en-GB', {hour:'2-digit', minute:'2-digit', second:'2-digit'});
      }
      var level = (obj.logLevelName || obj.level || 'info').toLowerCase();
      if (level === 'error' || level === 'fatal') cls = 'err';
      else if (level === 'warn' || level === 'warning') cls = 'warn';
      else if (level === 'debug') cls = 'msg';
      else cls = 'info';
      var msg = obj.msg || obj.message || obj.name || '';
      var extras = [];
      // Field "0" is usually a JSON string like {"subsystem":"gateway/ws"} - extract subsystem
      var subsystem = '';
      if (obj["0"]) {
        try { var sub = JSON.parse(obj["0"]); subsystem = sub.subsystem || ''; } catch(e) { subsystem = String(obj["0"]); }
      }
      // Field "1" can be a string or object - stringify objects
      function flatVal(v) { return (typeof v === 'object' && v !== null) ? JSON.stringify(v) : String(v); }
      if (obj["1"]) {
        if (typeof obj["1"] === 'object') {
          var parts = [];
          for (var k in obj["1"]) { if (k !== 'cause') parts.push(k + '=' + flatVal(obj["1"][k])); else parts.unshift(flatVal(obj["1"][k])); }
          extras.push(parts.join(' '));
        } else {
          extras.push(String(obj["1"]));
        }
      }
      if (obj["2"]) extras.push(flatVal(obj["2"]));
      // Build display
      var prefix = subsystem ? '[' + subsystem + '] ' : '';
      if (msg && extras.length) display = prefix + msg + ' ' + extras.join(' ');
      else if (extras.length) display = prefix + extras.join(' ');
      else if (msg) display = prefix + msg;
      else display = l.substring(0, 200);
      if (ts) display = '<span class="ts">' + ts + '</span> ' + escHtml(display);
      else display = escHtml(display);
    } catch(e) {
      if (l.includes('Error') || l.includes('failed')) cls = 'err';
      else if (l.includes('WARN')) cls = 'warn';
      display = escHtml(l.substring(0, 300));
    }
    html += '<div class="log-line"><span class="' + cls + '">' + display + '</span></div>';
  });
  document.getElementById(elId).innerHTML = html || '<span style="color:#555">No logs</span>';
  document.getElementById(elId).scrollTop = document.getElementById(elId).scrollHeight;
}

function escHtml(s) { s=String(s||''); return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;'); }

async function viewFile(path) {
  var viewer = document.getElementById('file-viewer');
  var title = document.getElementById('file-viewer-title');
  var content = document.getElementById('file-viewer-content');
  title.textContent = path;
  content.textContent = 'Loading...';
  viewer.style.display = 'block';
  try {
    var data = await fetch('/api/file?path=' + encodeURIComponent(path)).then(r => r.json());
    if (data.error) { content.textContent = 'Error: ' + data.error; return; }
    content.textContent = data.content;
  } catch(e) {
    content.textContent = 'Failed to load: ' + e.message;
  }
  viewer.scrollIntoView({behavior:'smooth'});
}

function closeFileViewer() {
  document.getElementById('file-viewer').style.display = 'none';
}

async function loadSessions() {
  if (window.CLOUD_MODE) {
    // In cloud mode: /api/sessions and /api/subagents already handle CLOUD_MODE server-side
    // fetch interceptor appends node_id+token so these hit the cloud endpoints correctly
  }
  var [sessData, saData, anomalyData, costData, chainData] = await Promise.all([
    fetch('/api/sessions').then(r => r.json()).catch(function() { return {sessions:[]}; }),
    fetch('/api/subagents').then(r => r.json()).catch(function() { return {subagents:[]}; }),
    fetch('/api/usage/anomalies').then(r => r.json()).catch(function() { return {anomalies:[]}; }),
    fetch('/api/sessions/cost-breakdown').then(r => r.json()).catch(function() { return {sessions:[]}; }),
    fetch('/api/delegation-tree').then(r => r.json()).catch(function() { return {chains:[], total_subagents:0, total_chain_cost_usd:0}; })
  ]);
  // Build cost lookup map by session_id suffix
  var costMap = {};
  (costData.sessions || []).forEach(function(c) {
    if (c.session_id) {
      costMap[c.session_id] = c;
      // Also index by last 8 chars for gateway session key matching
      costMap[c.session_id.slice(-16)] = c;
    }
  });
  var anomalySet = {};
  (anomalyData.anomalies || []).forEach(function(a) { if (a && a.session_id) anomalySet[a.session_id] = a; });
  var html = '';
  // Main sessions (non-subagent)
  var mainSessions = sessData.sessions.filter(function(s) { return !(s.sessionId || '').includes('subagent'); });
  var subagents = saData.subagents || [];
  
  mainSessions.forEach(function(s) {
    var anomaly = anomalySet[s.sessionId];
    var sid = s.sessionId || s.id || s.key || '';
    var sparkId = 'session-burn-' + Math.random().toString(36).slice(2);
    html += '<div class="session-item" style="border-left:3px solid var(--bg-accent);padding-left:16px;">';
    html += '<div class="session-name" style="display:flex;justify-content:space-between;align-items:center;gap:8px;">';
    html += '<span>🖥️ ' + escHtml(s.displayName || s.key) + ' <span style="font-size:11px;color:var(--text-muted);font-weight:400;">Main Session</span>';
    if (anomaly) {
      html += '<span class="session-anomaly" title="Cost anomaly: $' + Number(anomaly.cost_usd || 0).toFixed(4) + ' (' + Number(anomaly.ratio || 0).toFixed(2) + 'x rolling avg)">&#9888;&#65039;</span>';
    }
    html += '</span>';
    html += '<button onclick="event.stopPropagation();stopSession(\'' + escHtml(sid).replace(/'/g, "\\\\'") + '\')" style="background:#b91c1c;color:#fff;border:none;border-radius:6px;padding:4px 10px;font-size:11px;font-weight:700;cursor:pointer;">⏹ Emergency Stop</button>';
    html += '</div>';
    var sessCost = costMap[sid] || costMap[(sid||'').slice(-16)] || null;
    html += '<div class="session-meta">';
    html += '<span><span class="badge model">' + (s.model||'default') + '</span></span>';
    if (s.channel !== 'unknown') html += '<span><span class="badge channel">' + s.channel + '</span></span>';
    if (sessCost && sessCost.cost_usd > 0) {
      html += '<span style="font-size:11px;color:var(--text-success);font-weight:600;">💰 $' + Number(sessCost.cost_usd||0).toFixed(4) + ' total</span>';
    }
    html += '<span>Updated ' + timeAgo(s.updatedAt) + '</span>';
    html += '</div>';
    html += '<div style="margin-top:8px;padding:8px;background:var(--bg-secondary);border:1px solid var(--border-primary);border-radius:8px;">';
    html += '<div style="display:flex;justify-content:space-between;align-items:center;gap:8px;flex-wrap:wrap;">';
    html += '<span style="font-size:12px;color:var(--text-secondary);">Burn: <strong style="color:var(--text-primary);">' + Number(s.tokensPerMin || 0).toFixed(1) + ' tok/min</strong></span>';
    html += '<span style="font-size:12px;color:var(--text-secondary);">Projected (1h): <strong style="color:var(--text-primary);">$' + Number(s.projectedCostUsd || 0).toFixed(4) + '</strong></span>';
    if (sessCost && sessCost.tokens > 0) {
      html += '<span style="font-size:12px;color:var(--text-muted);">Total: <strong style="color:var(--text-secondary);">' + (sessCost.tokens >= 1000 ? (sessCost.tokens/1000).toFixed(0)+'K' : sessCost.tokens) + ' tok / $' + Number(sessCost.cost_usd||0).toFixed(4) + '</strong></span>';
    }
    html += '</div>';
    html += '<canvas id="' + sparkId + '" width="220" height="28" style="margin-top:6px;width:100%;height:28px;"></canvas>';
    html += '</div>';
    // Sub-agents nested underneath
    if (subagents.length > 0) {
      html += '<div style="margin-top:8px;margin-left:16px;border-left:2px solid var(--border-primary);padding-left:12px;">';
      subagents.forEach(function(sa) {
        var statusIcon = sa.status === 'active' ? '🟢' : sa.status === 'idle' ? '🟡' : '⬜';
        html += '<details style="margin-bottom:4px;">';
        html += '<summary style="cursor:pointer;font-size:13px;color:var(--text-secondary);padding:4px 0;">';
        html += statusIcon + ' <strong>' + escHtml(sa.displayName) + '</strong>';
        html += ' <span style="color:var(--text-muted);font-size:11px;">' + sa.runtime + '</span>';
        html += '</summary>';
        html += '<div style="padding:6px 0 6px 20px;font-size:12px;color:var(--text-muted);">';
        if (sa.recentTools && sa.recentTools.length > 0) {
          sa.recentTools.slice(-3).forEach(function(t) {
            html += '<div style="font-family:monospace;margin-bottom:2px;">⚡ <span style="color:var(--text-accent);">' + escHtml(t.name) + '</span> ' + escHtml(t.summary.substring(0,80)) + '</div>';
          });
        }
        if (sa.lastText) {
          html += '<div style="font-style:italic;margin-top:4px;">💭 ' + escHtml(sa.lastText.substring(0, 120)) + '</div>';
        }
        html += '</div></details>';
      });
      html += '</div>';
    }
    html += '</div>';
  });
  
  // Show orphan sessions that aren't main
  var subSessions = sessData.sessions.filter(function(s) { return (s.sessionId || '').includes('subagent'); });
  if (subSessions.length > 0 && mainSessions.length === 0) {
    sessData.sessions.forEach(function(s) {
      var anomaly = anomalySet[s.sessionId];
      html += '<div class="session-item">';
      html += '<div class="session-name">' + escHtml(s.displayName || s.key);
      if (anomaly) {
        html += '<span class="session-anomaly" title="Cost anomaly: $' + Number(anomaly.cost_usd || 0).toFixed(4) + ' (' + Number(anomaly.ratio || 0).toFixed(2) + 'x rolling avg)">&#9888;&#65039;</span>';
      }
      html += '</div>';
      html += '<div class="session-meta">';
      html += '<span><span class="badge model">' + (s.model||'default') + '</span></span>';
      html += '<span>Updated ' + timeAgo(s.updatedAt) + '</span>';
      html += '</div></div>';
    });
  }
  
  // Render delegation chains panel (AgentWeave-inspired provenance view)
  var chainHtml = '';
  var chains = (chainData && chainData.chains) || [];
  if (chains.length > 0) {
    var totalCost = chainData.total_chain_cost_usd || 0;
    var totalSA = chainData.total_subagents || 0;
    chainHtml += '<div style="margin-bottom:16px;">';
    chainHtml += '<div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:10px;">';
    chainHtml += '<h4 style="margin:0;font-size:13px;font-weight:700;color:var(--text-primary);">🔗 Delegation Chains <span style="font-size:11px;font-weight:400;color:var(--text-muted);">(' + totalSA + ' sub-agents)</span></h4>';
    chainHtml += '<span style="font-size:11px;color:var(--text-success);font-weight:600;">total chain cost $' + totalCost.toFixed(4) + '</span>';
    chainHtml += '</div>';
    chains.slice(0, 8).forEach(function(chain) {
      var ch = chain.parent_channel || 'unknown';
      var chIcon = ch === 'telegram' ? '✈️' : ch === 'whatsapp' ? '💬' : ch === 'discord' ? '🎮' : ch === 'main' ? '🖥️' : '🌐';
      chainHtml += '<div style="background:var(--bg-secondary);border:1px solid var(--border-primary);border-radius:10px;margin-bottom:8px;overflow:hidden;">';
      chainHtml += '<div style="padding:8px 12px;display:flex;align-items:center;gap:8px;border-bottom:1px solid var(--border-secondary);background:var(--bg-tertiary);">';
      chainHtml += '<span style="font-size:14px;">' + chIcon + '</span>';
      chainHtml += '<span style="font-size:12px;font-weight:600;color:var(--text-primary);flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">' + escHtml(chain.parent_display || chain.parent_key) + '</span>';
      chainHtml += '<span style="font-size:10px;color:var(--text-muted);white-space:nowrap;">' + chain.child_count + ' agents &bull; ';
      chainHtml += (chain.chain_tokens >= 1000 ? (chain.chain_tokens/1000).toFixed(0)+'K' : chain.chain_tokens) + ' tok';
      chainHtml += ' &bull; <span style="color:var(--text-success);">$' + chain.chain_cost_usd.toFixed(4) + '</span></span>';
      chainHtml += '</div>';
      chain.children.slice(0, 5).forEach(function(child, idx) {
        var dot = child.status === 'active' ? '#16a34a' : child.status === 'idle' ? '#d97706' : '#6b7280';
        chainHtml += '<div style="padding:6px 12px 6px 28px;display:flex;align-items:center;gap:8px;border-bottom:1px solid var(--border-secondary);font-size:12px;">';
        chainHtml += '<span style="width:7px;height:7px;border-radius:50%;background:' + dot + ';flex-shrink:0;"></span>';
        if (idx === 0) chainHtml += '<span style="color:var(--text-muted);font-size:10px;margin-right:-4px;">&#x2514;&#x2500;</span>';
        else chainHtml += '<span style="color:var(--text-muted);font-size:10px;margin-right:-4px;">&#x251C;&#x2500;</span>';
        chainHtml += '<span style="color:var(--text-secondary);font-weight:600;flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">' + escHtml(child.label) + '</span>';
        chainHtml += '<span style="background:var(--bg-accent);color:var(--bg-primary);padding:1px 6px;border-radius:8px;font-size:10px;font-weight:600;white-space:nowrap;">' + escHtml(child.model) + '</span>';
        chainHtml += '<span style="color:var(--text-muted);font-size:10px;white-space:nowrap;">';
        chainHtml += (child.total_tokens >= 1000 ? (child.total_tokens/1000).toFixed(0)+'K' : child.total_tokens) + ' tok';
        chainHtml += ' &bull; $' + child.cost_usd.toFixed(4) + '</span>';
        chainHtml += '</div>';
      });
      if (chain.children.length > 5) {
        chainHtml += '<div style="padding:4px 28px;font-size:11px;color:var(--text-muted);">+ ' + (chain.children.length - 5) + ' more sub-agents</div>';
      }
      chainHtml += '</div>';
    });
    if (chains.length > 8) {
      chainHtml += '<div style="font-size:11px;color:var(--text-muted);text-align:center;padding:4px 0;">+ ' + (chains.length - 8) + ' more chains</div>';
    }
    chainHtml += '</div>';
    var chainsEl = document.getElementById('delegation-chains-panel');
    if (chainsEl) chainsEl.innerHTML = chainHtml;
  } else {
    var chainsEl = document.getElementById('delegation-chains-panel');
    if (chainsEl) chainsEl.innerHTML = '';
  }

  document.getElementById('sessions-list').innerHTML = html || '<div style="padding:16px;color:var(--text-muted);">No sessions found</div>';
  mainSessions.forEach(function(s, i) {
    var canvas = document.querySelectorAll('#sessions-list canvas')[i];
    if (!canvas) return;
    var pts = Array.isArray(s.burnSeries) ? s.burnSeries : [];
    drawSessionSparkline(canvas, pts);
  });
}

async function stopSession(sessionId) {
  var sid = String(sessionId || '').trim();
  if (!sid) return;
  if (!confirm('Emergency stop session "' + sid + '"?')) return;
  try {
    var r = await fetch('/api/sessions/' + encodeURIComponent(sid) + '/stop', {method:'POST'});
    var data = await r.json();
    if (!r.ok || !data.ok) throw new Error((data && data.error) || 'Stop failed');
    alert('Emergency stop signal sent for session: ' + sid);
    loadSessions();
  } catch(e) {
    alert('Emergency stop failed: ' + e.message);
  }
}

function drawSessionSparkline(canvas, points) {
  if (!canvas || !canvas.getContext) return;
  var ctx = canvas.getContext('2d');
  var w = canvas.width;
  var h = canvas.height;
  ctx.clearRect(0, 0, w, h);
  var pts = (points || []).slice(-10);
  while (pts.length < 10) pts.unshift(0);
  var maxV = 1;
  pts.forEach(function(v){ if (v > maxV) maxV = v; });
  ctx.strokeStyle = 'rgba(96,255,128,0.95)';
  ctx.lineWidth = 2;
  ctx.beginPath();
  pts.forEach(function(v, i){
    var x = (i / (pts.length - 1)) * (w - 2) + 1;
    var y = h - 2 - ((v / maxV) * (h - 4));
    if (i === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
  });
  ctx.stroke();
}

var _cronJobs = [];
var _cronExpanded = {};
var _cronAutoRefreshTimer = null;
var _cronActionsAvailable = false;
var _cronView = 'active'; // 'active' | 'paused' | 'calendar'

// Cache of recent runs per job, populated lazily when Calendar is opened.
// Keyed by job_id -> [{ts, status}]. Used to render confirmed past-7d
// activity in the Calendar's "Recently ran" section, including failures.
var _cronRecentRunsCache = {};
var _cronRecentRunsLoaded = false;

function setCronView(view) {
  _cronView = view;
  document.querySelectorAll('.cron-view-tab').forEach(function(b) {
    if (b.dataset.view === view) b.classList.add('active'); else b.classList.remove('active');
  });
  if (view === 'calendar' && !_cronRecentRunsLoaded) {
    _loadAllCronRecentRuns();
  } else {
    renderCrons();
  }
}

async function _loadAllCronRecentRuns() {
  // One-shot bulk-load of recent runs for every ACTIVE job so the Calendar's
  // "Recently ran" section can render real, agent-confirmed history (with
  // failure status) rather than "Coming up" only. Skipped if any job has
  // already supplied state.lastRunAtMs (we'd be duplicating).
  _cronRecentRunsLoaded = true;
  try {
    var active = (_cronJobs || []).filter(function(j) { return j.enabled !== false; });
    var sevenDaysAgo = Date.now() - 7 * 86400000;
    var results = await Promise.all(active.map(function(j) {
      return fetch('/api/cron/' + encodeURIComponent(j.id) + '/runs')
        .then(function(r) { return r.ok ? r.json() : {runs:[]}; })
        .catch(function() { return {runs:[]}; });
    }));
    active.forEach(function(j, i) {
      var runs = ((results[i] || {}).runs || [])
        .map(function(r) {
          var ts = r.startedAt ? Date.parse(r.startedAt)
                 : r.timestamp || r.ts || 0;
          return { ts: ts, status: r.status || 'unknown' };
        })
        .filter(function(r) { return r.ts >= sevenDaysAgo && r.ts <= Date.now(); });
      _cronRecentRunsCache[j.id] = runs;
    });
  } catch (e) {
    // non-fatal: Calendar still renders predictions, just no past runs
  }
  renderCrons();
}

function _cronStatus(j) {
  // Honest status. We surface four states:
  //   ok        - last run reported success
  //   error     - last run reported failure
  //   stale     - we have a lastRun but it's older than 6h
  //   scheduled - never ran (or no history) BUT we can compute the next fire
  //               from the schedule, so the cron is wired up and waiting
  //   no-data   - we can't even predict the next fire (no schedule)
  var s = (j.state && j.state.lastStatus) || j.lastStatus || '';
  if (s) return s;
  var lastMs = (j.state && j.state.lastRunAtMs) || (j.lastRun ? Date.parse(j.lastRun) : 0);
  if (lastMs) {
    if (Date.now() - lastMs > 6 * 3600 * 1000) return 'stale';
    return 'ok';
  }
  var nextMs = _cronComputeNextFireMs(j.schedule, Date.now());
  if (nextMs) return 'scheduled';
  return 'no-data';
}

// ── Client-side cron next-fire predictor ────────────────────────────────────
// The agent uploads cron definitions but doesn't always populate the
// `state.nextRunAtMs` field (only after a real run lands). Without this we'd
// show "no data" for every freshly-defined job and an empty Calendar even
// when the schedule clearly fires multiple times a day. We compute a
// best-effort next fire client-side from the schedule shape.
//
// Handles:
//   { kind:'cron', expr:'<5-field cron>' }   - common patterns only
//   { kind:'every', everyMs:N }              - interval since now
//   { kind:'at', atMs:N }                    - one-shot
// Falls back to 0 when the expression is too complex (e.g. ranges/lists in
// multiple fields) - rather than show a wrong time, we omit the prediction.

function _cronParseField(field, min, max) {
  // Returns sorted array of valid values for this single field, or null on
  // anything we don't handle.
  if (field === '*') {
    var out = [];
    for (var i = min; i <= max; i++) out.push(i);
    return out;
  }
  // step: */N  or   M-N/S  or   */N over the whole range
  var stepM = field.match(/^\*\/(\d+)$/);
  if (stepM) {
    var step = parseInt(stepM[1], 10);
    if (!step || step < 1) return null;
    var arr = [];
    for (var v = min; v <= max; v += step) arr.push(v);
    return arr;
  }
  // Comma-separated list of single ints
  if (/^\d+(,\d+)*$/.test(field)) {
    return field.split(',').map(function(x){ return parseInt(x, 10); })
      .filter(function(x){ return x >= min && x <= max; })
      .sort(function(a,b){ return a - b; });
  }
  // Single integer
  if (/^\d+$/.test(field)) {
    var n = parseInt(field, 10);
    if (n < min || n > max) return null;
    return [n];
  }
  // Range  M-N
  var rangeM = field.match(/^(\d+)-(\d+)$/);
  if (rangeM) {
    var lo = parseInt(rangeM[1], 10), hi = parseInt(rangeM[2], 10);
    if (lo > hi || lo < min || hi > max) return null;
    var rng = [];
    for (var k = lo; k <= hi; k++) rng.push(k);
    return rng;
  }
  return null;
}

function _cronComputeNextFireMs(schedule, fromMs) {
  if (!schedule || typeof schedule !== 'object') return 0;
  var now = fromMs || Date.now();

  if (schedule.kind === 'every' && schedule.everyMs > 0) {
    // The agent stores `anchorMs` -- the wall-clock origin from which all
    // fires are scheduled (typically job creation time + optional stagger).
    // With that anchor, the next fire is deterministic:
    //     next = anchor + ceil((now - anchor) / everyMs) * everyMs
    // and the prediction is 100% accurate (matches the agent's scheduler
    // exactly). Without an anchor, fall back to "now + everyMs" which is the
    // worst-case upper bound (true next fire is somewhere in [now, now+N]).
    if (typeof schedule.anchorMs === 'number' && schedule.anchorMs > 0) {
      var elapsed = now - schedule.anchorMs;
      if (elapsed <= 0) return schedule.anchorMs; // agent hasn't started yet
      var n = Math.ceil(elapsed / schedule.everyMs);
      return schedule.anchorMs + n * schedule.everyMs;
    }
    return now + schedule.everyMs;
  }

  if (schedule.kind === 'at' && schedule.atMs > now) {
    return schedule.atMs;
  }

  if (schedule.kind === 'cron' && schedule.expr) {
    var parts = schedule.expr.trim().split(/\s+/);
    if (parts.length < 5) return 0;
    var minSet = _cronParseField(parts[0], 0, 59);
    var hrSet  = _cronParseField(parts[1], 0, 23);
    var domSet = _cronParseField(parts[2], 1, 31);
    var monSet = _cronParseField(parts[3], 1, 12);
    var dowSet = _cronParseField(parts[4], 0, 6);
    if (!minSet || !hrSet || !domSet || !monSet || !dowSet) return 0;

    // Walk forward minute by minute from `now+1min` until we find a match,
    // capped at 366 days so a malformed schedule can't infinite-loop.
    var cap = now + 366 * 86400000;
    var t = new Date(now + 60000);
    t.setSeconds(0, 0);
    while (t.getTime() < cap) {
      var mo = t.getMonth() + 1;
      var dom = t.getDate();
      var dow = t.getDay();
      var hr = t.getHours();
      var mi = t.getMinutes();
      // Cron's day match: if BOTH dom and dow are restricted, OR them.
      // If only one is restricted (other is "*"), AND them.
      var domStar = parts[2] === '*';
      var dowStar = parts[4] === '*';
      var domOk = domSet.indexOf(dom) >= 0;
      var dowOk = dowSet.indexOf(dow) >= 0;
      var dayMatch = (domStar && dowStar) ? true
                   : (domStar) ? dowOk
                   : (dowStar) ? domOk
                   : (domOk || dowOk);
      if (monSet.indexOf(mo) >= 0
          && hrSet.indexOf(hr) >= 0
          && minSet.indexOf(mi) >= 0
          && dayMatch) {
        return t.getTime();
      }
      t = new Date(t.getTime() + 60000);
    }
    return 0;
  }
  return 0;
}

function toggleCronAutoRefresh() {
  var cb = document.getElementById('cron-auto-refresh');
  if (!cb) return;
  if (cb.checked) {
    if (!_cronAutoRefreshTimer) _cronAutoRefreshTimer = setInterval(loadCrons, 30000);
  } else {
    if (_cronAutoRefreshTimer) { clearInterval(_cronAutoRefreshTimer); _cronAutoRefreshTimer = null; }
  }
}

async function loadCrons() {
  var data = await fetch('/api/crons').then(r => r.json());
  _cronJobs = data.jobs || [];
  // Show/hide cron action buttons based on gateway support
  document.querySelectorAll('.cron-action-btn').forEach(function(btn) {
    btn.style.display = _cronActionsAvailable ? '' : 'none';
  });
  renderCrons();
  // Load cron health summary panel
  loadCronHealth();
  // Load multi-node cron status from fleet nodes
  loadCronsMultiNode();
  // Load cron health monitor (GH #302)
  loadCronHealth();
  // Start auto-refresh if checkbox is checked and timer not running
  var cb = document.getElementById('cron-auto-refresh');
  if (cb && cb.checked && !_cronAutoRefreshTimer) {
    _cronAutoRefreshTimer = setInterval(loadCrons, 30000);
  }
}

async function loadCronHealth() {
  var panel = document.getElementById('cron-health-panel');
  if (!panel) return;
  // Clear the health table placeholder when loading completes
  var ht = document.getElementById('cron-health-table');
  if (ht) ht.innerHTML = '';
  try {
    var data = await fetch('/api/cron/health-summary').then(r => r.json());
    var jobs = data.jobs || [];
    var totals = data.totals || {};
    var hasIssues = data.hasErrors || data.hasSilent || data.hasAnomalies;

    // Show/hide emergency stop button
    var killBtn = document.getElementById('cron-kill-all-btn');
    if (killBtn) killBtn.style.display = (_cronActionsAvailable && hasIssues) ? 'inline-flex' : 'none';

    if (jobs.length === 0) { panel.innerHTML = ''; return; }

    var healthColor = {'ok':'#22c55e','warning':'#f59e0b','error':'#ef4444','silent':'#ef4444','disabled':'#6b7280'};
    var healthIcon = {'ok':'&#x2705;','warning':'&#x26A0;&#xFE0F;','error':'&#x274C;','silent':'&#x1F4F5;','disabled':'&#x23F8;'};

    var html = '<div class="card" style="padding:14px;">';
    // Summary row
    html += '<div style="display:flex;align-items:center;gap:16px;flex-wrap:wrap;margin-bottom:12px;">';
    html += '<div style="font-size:13px;font-weight:700;color:var(--text-primary);">&#x1F4CA; Cron Health</div>';
    html += '<span style="font-size:12px;background:#16a34a22;color:#22c55e;border-radius:6px;padding:2px 8px;">'+totals.ok+' healthy</span>';
    if (totals.error) html += '<span style="font-size:12px;background:#ef444422;color:#ef4444;border-radius:6px;padding:2px 8px;">'+totals.error+' errors</span>';
    if (totals.silent) html += '<span style="font-size:12px;background:#ef444422;color:#ef4444;border-radius:6px;padding:2px 8px;">'+totals.silent+' silent</span>';
    if (totals.warning) html += '<span style="font-size:12px;background:#f59e0b22;color:#f59e0b;border-radius:6px;padding:2px 8px;">'+totals.warning+' warnings</span>';
    if (totals.disabled) html += '<span style="font-size:12px;background:#6b728022;color:#6b7280;border-radius:6px;padding:2px 8px;">'+totals.disabled+' disabled</span>';
    html += '</div>';

    // Per-job health rows (only non-ok or all if <=8 jobs)
    var showJobs = jobs.length <= 8 ? jobs : jobs.filter(function(j){return j.health !== 'ok';});
    if (showJobs.length > 0) {
      html += '<div style="display:grid;gap:6px;">';
      showJobs.forEach(function(j) {
        var color = healthColor[j.health] || '#6b7280';
        var icon = healthIcon[j.health] || '';
        var projStr = j.monthlyProjectedCost > 0 ? ' &middot; ~$'+j.monthlyProjectedCost.toFixed(2)+'/mo' : '';
        var anomalyBadges = '';
        if (j.costSpike) anomalyBadges += ' <span title="Cost spike detected" style="font-size:11px;background:#f59e0b22;color:#f59e0b;border-radius:4px;padding:1px 5px;">cost spike</span>';
        if (j.durationSpike) anomalyBadges += ' <span title="Duration spike detected" style="font-size:11px;background:#f59e0b22;color:#f59e0b;border-radius:4px;padding:1px 5px;">slow run</span>';
        if (j.isSilent) anomalyBadges += ' <span title="Job has not run in over 2.5x expected interval" style="font-size:11px;background:#ef444422;color:#ef4444;border-radius:4px;padding:1px 5px;">silent</span>';
        html += '<div style="display:flex;align-items:center;gap:8px;padding:6px 10px;background:var(--bg-secondary);border-radius:8px;border:1px solid var(--border-secondary);">';
        html += '<span style="width:8px;height:8px;border-radius:50%;background:'+color+';flex-shrink:0;"></span>';
        html += '<span style="font-size:12px;font-weight:600;color:var(--text-primary);flex:1;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">'+escHtml(j.name||j.id)+'</span>';
        html += anomalyBadges;
        if (j.consecutiveFailures > 1) html += '<span style="font-size:11px;background:#ef444422;color:#ef4444;border-radius:4px;padding:1px 5px;">'+j.consecutiveFailures+' fails</span>';
        html += '<span style="font-size:11px;color:var(--text-muted);white-space:nowrap;">'+projStr+'</span>';
        if (_cronActionsAvailable) html += '<button onclick="event.stopPropagation();cronPauseJob(\''+escHtml(j.id)+'\')" title="Pause this job" style="font-size:11px;padding:2px 7px;border-radius:5px;border:1px solid var(--border-secondary);background:var(--bg-tertiary);color:var(--text-secondary);cursor:pointer;">&#x23F8; Pause</button>';
        html += '</div>';
      });
      html += '</div>';
    }
    html += '</div>';
    panel.innerHTML = html;
  } catch(e) {
    // Non-fatal: health panel is supplementary
    console.debug('cron health load failed', e);
  }
}

async function cronKillAll() {
  if (!confirm('Emergency stop: disable ALL active cron jobs? This cannot be undone automatically.')) return;
  try {
    var r = await fetch('/api/cron/kill-all', {method:'POST'}).then(res => res.json());
    alert('Disabled ' + (r.disabled||0) + ' cron job(s).' + (r.errors && r.errors.length ? ' Failed: '+r.errors.join(', ') : ''));
    loadCrons();
  } catch(e) {
    alert('Emergency stop failed: ' + e.message);
  }
}

async function cronPauseJob(jobId) {
  try {
    var r = await fetch('/api/cron/toggle', {
      method: 'POST',
      headers: {'Content-Type':'application/json'},
      body: JSON.stringify({jobId: jobId, enabled: false})
    }).then(res => res.json());
    if (r.ok !== false) { loadCrons(); } else { alert('Failed to pause job: ' + (r.error||'unknown error')); }
  } catch(e) {
    alert('Pause failed: ' + e.message);
  }
}

async function loadCronsMultiNode() {
  var panel = document.getElementById('crons-multi-node');
  if (!panel) return;
  try {
    var d = await fetch('/api/nodes').then(function(r){return r.json();});
    var nodes = d.nodes || [];
    if (nodes.length === 0) { panel.style.display = 'none'; return; }
    panel.style.display = 'block';
    var html = '<div class="card" style="padding:14px;">';
    html += '<div style="font-size:13px;font-weight:700;color:var(--text-primary);margin-bottom:10px;">&#x1F310; Multi-Node Cron Status</div>';
    html += '<div style="display:flex;gap:10px;flex-wrap:wrap;">';
    nodes.forEach(function(n) {
      var m = n.latest_metrics || {};
      var cronSummary = (m.crons) || null;
      var statusColor = n.status === 'online' ? '#22c55e' : '#ef4444';
      var errCount = cronSummary ? (cronSummary.error_count || 0) : 0;
      var totalCount = cronSummary ? (cronSummary.total || 0) : 0;
      html += '<div style="background:var(--bg-secondary);border:1px solid var(--border-secondary);border-radius:8px;padding:10px 14px;min-width:180px;">';
      html += '<div style="display:flex;align-items:center;gap:6px;margin-bottom:6px;">';
      html += '<span style="width:8px;height:8px;border-radius:50%;background:'+statusColor+';display:inline-block;"></span>';
      html += '<span style="font-size:13px;font-weight:600;color:var(--text-primary);">'+escHtml(n.name||n.node_id)+'</span>';
      html += '</div>';
      if (cronSummary) {
        html += '<div style="font-size:11px;color:var(--text-muted);">'+totalCount+' jobs';
        if (errCount > 0) html += ' &middot; <span style="color:#ef4444;">'+errCount+' errors</span>';
        html += '</div>';
        if (cronSummary.last_run_at) html += '<div style="font-size:11px;color:var(--text-muted);margin-top:2px;">Last run: '+timeAgo(new Date(cronSummary.last_run_at).getTime())+'</div>';
      } else {
        html += '<div style="font-size:11px;color:var(--text-muted);">No cron data</div>';
      }
      html += '</div>';
    });
    html += '</div></div>';
    panel.innerHTML = html;
  } catch(e) {
    panel.style.display = 'none';
  }
}

function renderCrons() {
  var active = _cronJobs.filter(function(j){ return j.enabled !== false; });
  var paused = _cronJobs.filter(function(j){ return j.enabled === false; });
  var ca = document.getElementById('crons-count-active');
  var cp = document.getElementById('crons-count-paused');
  if (ca) ca.textContent = active.length ? '(' + active.length + ')' : '';
  if (cp) cp.textContent = paused.length ? '(' + paused.length + ')' : '';

  var listEl = document.getElementById('crons-list');
  if (!listEl) return;

  if (_cronView === 'calendar') {
    renderCronCalendar(active);
    return;
  }

  var jobs = _cronView === 'paused' ? paused : active;
  if (jobs.length === 0) {
    var msg = _cronView === 'paused'
      ? 'No paused jobs. Disable any active job to see it here.'
      : 'No active cron jobs yet. Click "+ New Job" to create one.';
    listEl.innerHTML = '<div style="color:var(--text-muted);padding:24px;text-align:center;font-size:13px;">' + msg + '</div>';
    return;
  }

  renderCronList(jobs);
}

function renderCronList(jobs) {
  var html = '';
  jobs.forEach(function(j) {
    var status = _cronStatus(j);
    var isEnabled = j.enabled !== false;
    var disabledClass = isEnabled ? '' : ' cron-disabled';
    var expanded = _cronExpanded[j.id];

    var labelMap = {'no-data':'no data','stale':'stale','ok':'ok','error':'error','pending':'pending','scheduled':'scheduled'};
    var badgeLabel = isEnabled ? (labelMap[status] || status) : 'disabled';
    var badgeClass = isEnabled ? status : 'pending';
    var badgeTitle = '';
    if (status === 'no-data') badgeTitle = 'No run history yet AND no schedule that we can predict. Check the agent side.';
    else if (status === 'stale') badgeTitle = 'Last run was over 6h ago — job may have stopped firing.';
    else if (status === 'scheduled') badgeTitle = 'Job is wired up and waiting for its next fire. Once a real run lands, this will switch to ok / error with run history.';

    html += '<div class="cron-item' + disabledClass + '" onclick="toggleCronExpand(\'' + escHtml(j.id) + '\')">';
    html += '<div style="display:flex;justify-content:space-between;align-items:center;">';
    html += '<div class="cron-name">' + escHtml(j.name || j.id) + '</div>';
    html += '<span class="cron-status ' + badgeClass + '" title="' + escHtml(badgeTitle) + '">' + badgeLabel + '</span>';
    if (status === 'error') {
      var errMsg = (j.state && j.state.lastError) ? escHtml(j.state.lastError) : 'Unknown error';
      var errTime = (j.state && j.state.lastRunAtMs) ? new Date(j.state.lastRunAtMs).toLocaleString() : 'Unknown';
      var consecutiveFails = (j.state && j.state.consecutiveFailures) ? j.state.consecutiveFailures : '';
      html += '<span class="cron-error-actions">';
      html += '<span class="cron-info-icon" title="Error details" onclick="event.stopPropagation();showCronError(this,\'' + errMsg.replace(/'/g,'\\&#39;').replace(/"/g,'&quot;') + '\',\'' + escHtml(errTime) + '\',' + (consecutiveFails||'null') + ')">&#x2139;&#xFE0F;</span>';
      if (_cronActionsAvailable) html += '<button class="cron-fix-btn" onclick="event.stopPropagation();confirmCronFix(\'' + escHtml(j.id) + '\',\'' + escHtml(j.name||j.id).replace(/'/g,'\\&#39;') + '\')">&#x1F527; Fix</button>';
      html += '</span>';
    }
    html += '</div>';
    html += '<div class="cron-schedule">' + formatSchedule(j.schedule) + '</div>';
    html += '<div class="cron-meta">';
    if (j.state && j.state.lastRunAtMs) html += 'Last: ' + timeAgo(j.state.lastRunAtMs);
    // Prefer the agent's reported next-run time; fall back to a client-side
    // prediction from the schedule expression so newly-defined jobs (no run
    // history yet) still surface a useful "Next: ..." line.
    var _nextMs = (j.state && j.state.nextRunAtMs) || _cronComputeNextFireMs(j.schedule, Date.now());
    if (_nextMs) html += ' &middot; Next: ' + formatTime(_nextMs);
    if (j.state && j.state.lastDurationMs) html += ' &middot; Took: ' + (j.state.lastDurationMs/1000).toFixed(1) + 's';
    if (j.lastRunTokens) html += ' &middot; ' + j.lastRunTokens.toLocaleString() + ' tok';
    if (j.lastRunCostUsd) html += ' &middot; $' + j.lastRunCostUsd.toFixed(4);
    if (typeof j.cost_usd === 'number') html += ' &middot; Total: $' + Number(j.cost_usd).toFixed(4);
    if (j.cost_session_count) html += ' (' + j.cost_session_count + ' runs)';
    html += '</div>';
    // Cost badges
    var badges = '';
    if (j.lastRunCostUsd && j.runHistory && j.runHistory.length > 1) {
      var costs = j.runHistory.map(function(r){return r.costUsd||0;}).filter(function(c){return c>0;});
      if (costs.length > 1) {
        var avg = costs.slice(1).reduce(function(a,b){return a+b;},0)/(costs.length-1);
        if (avg > 0 && j.lastRunCostUsd > avg*2) badges += '<span title="Cost spike: '+Math.round(j.lastRunCostUsd/avg)+'x above average" style="margin-left:6px;cursor:help;">&#x26A0;&#xFE0F;</span>';
      }
    }
    if (j.lastRunTokens && j.lastRunTokens > 500 && j.state && j.state.lastStatus === 'ok') {
      if (!j.runHistory || !j.runHistory.length) badges += '<span title="Possible idle spend: tokens used but check if output was produced" style="margin-left:4px;cursor:help;">&#x1F4B8;</span>';
    }
    if (badges) html += '<div style="display:inline;">' + badges + '</div>';

    // Action buttons (hidden unless gateway supports cron invocation)
    if (_cronActionsAvailable) {
    html += '<div class="cron-actions" onclick="event.stopPropagation()">';
    html += '<button class="cron-btn-run" onclick="cronRunNow(\'' + escHtml(j.id) + '\')">&#x25B6; Run Now</button>';
    html += '<button class="cron-btn-toggle" onclick="cronToggle(\'' + escHtml(j.id) + '\',' + !isEnabled + ')">' + (isEnabled ? '&#x23F8; Disable' : '&#x25B6; Enable') + '</button>';
    html += '<button class="cron-btn-edit" onclick="cronEdit(\'' + escHtml(j.id) + '\')">&#x270F; Edit</button>';
    html += '<button class="cron-btn-delete" onclick="cronConfirmDelete(\'' + escHtml(j.id) + '\',\'' + escHtml(j.name||j.id).replace(/'/g,'\\&#39;') + '\')">&#x1F5D1; Delete</button>';
    html += '</div>';
    }

    // Expanded section
    if (expanded) {
      html += '<div class="cron-expand" id="cron-expand-' + escHtml(j.id) + '">';
      if (j.state && j.state.lastError) {
        html += '<div style="color:var(--text-error);margin-bottom:6px;"><strong>Last error:</strong> ' + escHtml(j.state.lastError) + '</div>';
      }
      html += '<div id="cron-runs-' + escHtml(j.id) + '">Loading run history...</div>';
      if (j.payload || j.config) {
        html += '<div class="cron-config-detail">' + escHtml(JSON.stringify(j.payload || j.config || {}, null, 2)) + '</div>';
      }
      html += '</div>';
    }

    html += '</div>';
  });
  document.getElementById('crons-list').innerHTML = html;

  // Load run history for expanded items
  Object.keys(_cronExpanded).forEach(function(id) {
    if (_cronExpanded[id]) loadCronRuns(id);
  });
}

function _cronDayLabel(key) {
  var dayMs = 86400000;
  var today = new Date(); today.setHours(0,0,0,0);
  var d = new Date(key + 'T00:00:00');
  var diff = Math.round((d - today) / dayMs);
  var dayName = d.toLocaleDateString('en-US', {weekday:'long', month:'short', day:'numeric'});
  if (diff === 0) return 'Today &middot; ' + dayName;
  if (diff === 1) return 'Tomorrow &middot; ' + dayName;
  if (diff === -1) return 'Yesterday &middot; ' + dayName;
  if (diff > 0) return 'In ' + diff + ' days &middot; ' + dayName;
  return Math.abs(diff) + ' days ago &middot; ' + dayName;
}
function _cronTimeStr(ts) {
  return new Date(ts).toLocaleTimeString('en-US', {hour:'2-digit',minute:'2-digit',hour12:false});
}
function _cronGroupByDay(items) {
  var groups = {};
  items.forEach(function(it) {
    var key = new Date(it.ts).toISOString().slice(0,10);
    (groups[key] = groups[key] || []).push(it);
  });
  return groups;
}

function renderCronCalendar(jobs) {
  var listEl = document.getElementById('crons-list');
  if (!listEl) return;
  var now = Date.now();
  var dayMs = 86400000;
  var future = now + 7 * dayMs;
  var past = now - 7 * dayMs;

  var upcoming = [];
  var recent = [];
  var predictedCount = 0;
  jobs.forEach(function(j) {
    var nextMs = j.state && j.state.nextRunAtMs;
    var predicted = false;
    if (!nextMs) {
      // No agent-reported next run -- compute it from the schedule so the
      // Calendar populates immediately for jobs that have never landed a
      // run record yet. This is the difference between "Coming up: 0" and
      // showing all 17 actively-scheduled jobs grouped by day.
      var pred = _cronComputeNextFireMs(j.schedule, now);
      if (pred) { nextMs = pred; predicted = true; }
    }
    if (nextMs && nextMs >= now && nextMs <= future) {
      upcoming.push({ts: nextMs, job: j, predicted: predicted});
      if (predicted) predictedCount++;
    }
    var lastMs = j.state && j.state.lastRunAtMs;
    if (lastMs && lastMs >= past && lastMs <= now) {
      recent.push({ts: lastMs, job: j, status: j.state.lastStatus || 'unknown'});
    }
    // Also pull every confirmed run from the per-job /runs cache (loaded
    // lazily when Calendar tab opens). This is how past failures land in
    // "Recently ran" with a red icon, even if state.lastStatus is missing.
    var cached = _cronRecentRunsCache[j.id] || [];
    cached.forEach(function(r) {
      if (r.ts >= past && r.ts <= now && r.ts !== lastMs) {
        recent.push({ts: r.ts, job: j, status: r.status});
      }
    });
  });
  upcoming.sort(function(a,b){return a.ts - b.ts;});
  recent.sort(function(a,b){return b.ts - a.ts;});

  var html = '<div style="padding:12px;">';

  // Summary tiles
  html += '<div style="display:flex;gap:10px;margin-bottom:14px;flex-wrap:wrap;">';
  [
    {label:'Coming up (7d)', val: upcoming.length},
    {label:'Ran (last 7d)',   val: recent.length},
    {label:'Active jobs',     val: jobs.length},
  ].forEach(function(t) {
    html += '<div style="background:var(--bg-secondary);border-radius:8px;padding:10px 16px;flex:1;min-width:130px;">';
    html += '<div style="font-size:10px;color:var(--text-muted);text-transform:uppercase;letter-spacing:0.5px;">' + t.label + '</div>';
    html += '<div style="font-size:22px;font-weight:700;color:var(--text-primary);margin-top:2px;">' + t.val + '</div>';
    html += '</div>';
  });
  html += '</div>';

  if (upcoming.length === 0 && recent.length === 0) {
    html += '<div style="background:var(--bg-secondary);border-radius:8px;padding:24px;text-align:center;color:var(--text-muted);font-size:13px;line-height:1.6;">';
    html += '<div style="font-size:30px;margin-bottom:8px;">&#x1F4C5;</div>';
    html += '<div><strong style="color:var(--text-primary);">No schedule data available yet.</strong></div>';
    html += '<div style="margin-top:6px;max-width:480px;margin-left:auto;margin-right:auto;">ClawMetry shows runs once your agent reports them. If your jobs are scheduled but not running here, check the agent’s gateway connection or wait for the next scheduled fire.</div>';
    html += '</div></div>';
    listEl.innerHTML = html;
    return;
  }

  if (upcoming.length > 0) {
    html += '<div class="cron-cal-section">&#x1F552; Coming up</div>';
    if (predictedCount > 0 && recent.length === 0) {
      // We populated this calendar entirely from client-side predictions
      // because the agent has not reported any run state yet. Be honest:
      // the dots and times below are best-effort, not confirmed acks.
      html += '<div style="background:rgba(96,165,250,0.08);border:1px solid rgba(96,165,250,0.2);'
            + 'border-radius:8px;padding:8px 12px;margin-bottom:8px;font-size:11px;color:var(--text-muted);'
            + 'line-height:1.5;">'
            + '&#x1F4A1; ClawMetry has not received any run state from your agent yet, so these times are '
            + 'computed from each schedule. They will be replaced with confirmed run times once the first '
            + 'real run lands.</div>';
    }
    var upGroups = _cronGroupByDay(upcoming);
    Object.keys(upGroups).sort().forEach(function(k) {
      html += '<div class="cron-cal-day">';
      html += '<div class="cron-cal-daylabel">' + _cronDayLabel(k) + '</div>';
      upGroups[k].forEach(function(it) {
        var icon = it.predicted ? '&#x231B;' : '&#x231B;';
        var iconTitle = it.predicted ? 'Predicted from schedule (not yet confirmed by agent)'
                                     : 'Reported by the agent as the next scheduled run';
        var iconColor = it.predicted ? 'rgba(148,163,184,0.6)' : 'var(--text-muted)';
        html += '<div class="cron-cal-row">';
        html += '<div class="cron-cal-time">' + _cronTimeStr(it.ts) + '</div>';
        html += '<div class="cron-cal-status" style="color:' + iconColor + ';" title="' + iconTitle + '">' + icon + '</div>';
        html += '<div class="cron-cal-name">' + escHtml(it.job.name || it.job.id) + '</div>';
        html += '<div class="cron-cal-sched">' + escHtml(formatSchedule(it.job.schedule)) + '</div>';
        html += '</div>';
      });
      html += '</div>';
    });
  }

  if (recent.length > 0) {
    html += '<div class="cron-cal-section" style="margin-top:18px;">&#x2714;&#xFE0F; Recently ran</div>';
    var pastGroups = _cronGroupByDay(recent);
    Object.keys(pastGroups).sort().reverse().forEach(function(k) {
      html += '<div class="cron-cal-day">';
      html += '<div class="cron-cal-daylabel">' + _cronDayLabel(k) + '</div>';
      pastGroups[k].forEach(function(it) {
        var color = it.status === 'error' ? '#ef4444' : (it.status === 'ok' ? '#22c55e' : '#9ca3af');
        var icon  = it.status === 'error' ? '&#x274C;' : (it.status === 'ok' ? '&#x2705;' : '&#x25CF;');
        html += '<div class="cron-cal-row">';
        html += '<div class="cron-cal-time">' + _cronTimeStr(it.ts) + '</div>';
        html += '<div class="cron-cal-status" style="color:' + color + ';">' + icon + '</div>';
        html += '<div class="cron-cal-name">' + escHtml(it.job.name || it.job.id) + '</div>';
        html += '<div class="cron-cal-sched">' + escHtml(formatSchedule(it.job.schedule)) + '</div>';
        html += '</div>';
      });
      html += '</div>';
    });
  }

  html += '</div>';
  listEl.innerHTML = html;
}

function toggleCronExpand(jobId) {
  _cronExpanded[jobId] = !_cronExpanded[jobId];
  renderCrons();
}

async function loadCronRuns(jobId) {
  try {
    var resp = await fetch('/api/cron/' + encodeURIComponent(jobId) + '/runs');
    if (!resp.ok) throw new Error('HTTP ' + resp.status);
    var data = await resp.json();
    var el = document.getElementById('cron-runs-' + jobId);
    if (!el) return;
    var runs = (data && data.runs) || [];
    if (runs.length === 0) {
      el.innerHTML = '<div style="color:var(--text-muted);">No run history yet — your agent has not reported any runs for this job.</div>';
      return;
    }
    // Build calendar heatmap (last 30 days)
    var now = Date.now();
    var days = 30;
    var dayMap = {};
    runs.forEach(function(r){
      var d = new Date(r.startedAt||r.ts);
      var key = d.toISOString().slice(0,10);
      if(!dayMap[key]) dayMap[key]={status:r.status,cost:r.costUsd||0,count:1};
      else { dayMap[key].count++; dayMap[key].cost+=r.costUsd||0; if(r.status==='error') dayMap[key].status='error'; }
    });
    var cal = '<div style="display:flex;gap:3px;flex-wrap:wrap;margin-bottom:12px;">';
    for(var di=days-1;di>=0;di--){
      var dd=new Date(now-di*86400000);
      var dk=dd.toISOString().slice(0,10);
      var dm=dayMap[dk];
      var col=dm?(dm.status==='error'?'#f87171':(dm.cost>0.05?'#fbbf24':'#4ade80')):'#2a2a2a';
      var tip=dk+(dm?' - '+dm.count+' run(s)'+(dm.cost?' $'+dm.cost.toFixed(4):''):'');
      cal+='<div title="'+tip+'" style="width:14px;height:14px;border-radius:2px;background:'+col+';cursor:default;"></div>';
    }
    cal+='</div>';
    var h = cal + '<div style="font-weight:600;margin-bottom:8px;">Run History (last ' + runs.length + ')</div>';
    runs.forEach(function(r) {
      var statusCls = r.status === 'ok' ? 'run-status-ok' : 'run-status-error';
      var dur = r.durationMs ? ' - ' + (r.durationMs/1000).toFixed(1) + 's' : '';
      var cost = r.costUsd ? ' - $'+r.costUsd.toFixed(4) : '';
      var tok = r.tokens ? ' - '+r.tokens.toLocaleString()+' tok' : '';
      var sid = r.sessionFile ? r.sessionFile.replace('.jsonl','') : '';
      h += '<div class="run-entry">';
      h += '<span>' + new Date(r.startedAt || r.ts).toLocaleString() + dur + tok + cost + '</span>';
      h += '<span class="' + statusCls + '">' + (r.status || 'unknown') + '</span>';
      if(sid) h += '<button data-sid="' + sid.replace(/"/g,'') + '" onclick="loadCronLog(event,this.dataset.sid)" style="margin-left:8px;padding:2px 8px;font-size:11px;border-radius:4px;border:1px solid var(--border-secondary);background:var(--bg-secondary);color:var(--text-muted);cursor:pointer;">View log</button>';
      h += '</div>';
      if (r.status === 'error' && r.error) {
        h += '<div style="color:var(--text-error);font-size:11px;padding:2px 0 4px 8px;border-left:2px solid var(--text-error);margin-left:4px;">' + escHtml(r.error).substring(0,200) + '</div>';
      }
    });
    el.innerHTML = h;
  } catch(e) {
    var el = document.getElementById('cron-runs-' + jobId);
    if (el) el.innerHTML = '<div style="color:var(--text-error);">Could not load run history (' + escHtml(String(e.message||e)) + '). The endpoint may be unreachable or your gateway is offline.</div>';
  }
}

function _closeCronLog() { var m = document.getElementById('cron-log-modal'); if (m) m.remove(); }
async function loadCronLog(evt, sessionId) {
  if(evt) evt.stopPropagation();
  var existing = document.getElementById('cron-log-modal');
  if(existing) existing.remove();
  var modal = document.createElement('div');
  modal.id = 'cron-log-modal';
  modal.setAttribute('style','position:fixed;top:0;left:0;right:0;bottom:0;background:rgba(0,0,0,0.75);z-index:9998;display:flex;align-items:center;justify-content:center;');
  modal.onclick = function(e){ if(e.target===modal) modal.remove(); };
  var inner = document.createElement('div');
  inner.setAttribute('style','background:var(--bg-primary);border-radius:12px;width:85vw;max-height:80vh;display:flex;flex-direction:column;overflow:hidden;padding:0;');
  inner.innerHTML = '<div style="display:flex;justify-content:space-between;align-items:center;padding:16px 20px;border-bottom:1px solid var(--border-secondary);">'
    + '<span style="font-weight:700;font-size:14px;">Session log</span>'
    + '<button onclick="_closeCronLog()" style="background:none;border:none;color:var(--text-muted);font-size:20px;cursor:pointer;line-height:1;">×</button>'
    + '</div>'
    + '<div id="cron-log-content" style="overflow:auto;padding:16px;font-family:SF Mono,Fira Code,monospace;font-size:12px;white-space:pre-wrap;color:var(--text-secondary);flex:1;">Loading...</div>';
  modal.appendChild(inner);
  document.body.appendChild(modal);
  try {
    var data = await fetch('/api/cron-run-log?session_id=' + encodeURIComponent(sessionId)).then(function(r){ return r.json(); });
    var lines = data.events || [];
    var out = lines.map(function(ev) {
      var role = (ev.role || ev.type || '').toUpperCase();
      var text = ev.text || ev.content || ev.summary || ev.tool || '';
      return '[' + (ev.ts || '').substring(11,19) + '] ' + role + ': ' + String(text).substring(0,200);
    }).join('\n');
    document.getElementById('cron-log-content').textContent = out || 'No events found';
  } catch(ex) {
    document.getElementById('cron-log-content').textContent = 'Error: ' + ex.message;
  }
}

async function cronRunNow(jobId) {
  try {
    var res = await fetch('/api/cron/run', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({jobId: jobId})});
    var data = await res.json();
    showCronToast(data.message || 'Job triggered');
    setTimeout(loadCrons, 2000);
  } catch(e) { showCronToast('Error: ' + e.message); }
}

async function cronToggle(jobId, enabled) {
  try {
    var res = await fetch('/api/cron/toggle', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({jobId: jobId, enabled: enabled})});
    var data = await res.json();
    if (data.error) { showCronToast('Error: ' + data.error); return; }
    showCronToast(data.message || (enabled ? 'Job enabled' : 'Job disabled'));
    // Update local state immediately for instant UI feedback
    var job = _cronJobs.find(function(j) { return j.id === jobId; });
    if (job) { job.enabled = enabled; renderCrons(); }
    // Then refresh from server after a short delay
    setTimeout(loadCrons, 1000);
  } catch(e) { showCronToast('Error: ' + e.message); }
}

function cronConfirmDelete(jobId, jobName) {
  var modal = document.createElement('div');
  modal.className = 'cron-confirm-modal';
  modal.innerHTML = '<div class="cron-confirm-box"><p>Delete cron job<br><strong>' + jobName + '</strong>?<br><span style="font-size:12px;color:var(--text-muted);">This cannot be undone.</span></p><button class="confirm-yes" style="background:#ef4444;" onclick="cronDelete(\'' + jobId + '\');this.closest(\'.cron-confirm-modal\').remove()">Delete</button><button class="confirm-no" onclick="this.closest(\'.cron-confirm-modal\').remove()">Cancel</button></div>';
  document.body.appendChild(modal);
  modal.addEventListener('click', function(e) { if (e.target === modal) modal.remove(); });
}

async function cronDelete(jobId) {
  try {
    var res = await fetch('/api/cron/delete', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({jobId: jobId})});
    var data = await res.json();
    showCronToast(data.message || 'Job deleted');
    delete _cronExpanded[jobId];
    loadCrons();
  } catch(e) { showCronToast('Error: ' + e.message); }
}

function cronEdit(jobId) {
  var job = _cronJobs.find(function(j) { return j.id === jobId; });
  if (!job) return;
  document.getElementById('cron-edit-mode').value = 'edit';
  document.getElementById('cron-modal-title').textContent = 'Edit Cron Job';
  document.getElementById('cron-save-btn').textContent = 'Save';
  document.getElementById('cron-edit-id').value = job.id;
  document.getElementById('cron-edit-name').value = job.name || '';
  var sched = job.schedule || {};
  if (sched.kind === 'cron') {
    document.getElementById('cron-edit-schedule').value = sched.expr || '';
    document.getElementById('cron-edit-tz').value = sched.tz || '';
  } else if (sched.kind === 'every') {
    document.getElementById('cron-edit-schedule').value = 'every ' + (sched.everyMs/60000) + 'min';
    document.getElementById('cron-edit-tz').value = '';
  } else {
    document.getElementById('cron-edit-schedule').value = JSON.stringify(sched);
    document.getElementById('cron-edit-tz').value = '';
  }
  document.getElementById('cron-edit-prompt').value = (job.payload && (job.payload.text || job.payload.message || job.payload.prompt)) || (job.config && job.config.prompt) || '';
  document.getElementById('cron-edit-channel').value = (job.payload && job.payload.channel) || (job.config && job.config.channel) || '';
  document.getElementById('cron-edit-model').value = (job.payload && job.payload.model) || (job.config && job.config.model) || '';
  document.getElementById('cron-edit-enabled').checked = job.enabled !== false;
  var modal = document.getElementById('cron-edit-modal');
  modal.style.display = 'flex';
}

function cronCreateNew() {
  document.getElementById('cron-edit-mode').value = 'create';
  document.getElementById('cron-modal-title').textContent = 'Create New Cron Job';
  document.getElementById('cron-save-btn').textContent = 'Create';
  document.getElementById('cron-edit-id').value = '';
  document.getElementById('cron-edit-name').value = '';
  document.getElementById('cron-edit-schedule').value = '';
  document.getElementById('cron-edit-tz').value = '';
  document.getElementById('cron-edit-prompt').value = '';
  document.getElementById('cron-edit-channel').value = '';
  document.getElementById('cron-edit-model').value = '';
  document.getElementById('cron-edit-enabled').checked = true;
  var modal = document.getElementById('cron-edit-modal');
  modal.style.display = 'flex';
}

function closeCronEditModal() {
  document.getElementById('cron-edit-modal').style.display = 'none';
}

async function saveCronEdit() {
  var mode = document.getElementById('cron-edit-mode').value;
  var jobId = document.getElementById('cron-edit-id').value;
  var name = document.getElementById('cron-edit-name').value.trim();
  var schedStr = document.getElementById('cron-edit-schedule').value.trim();
  var tz = document.getElementById('cron-edit-tz').value.trim();
  var prompt = document.getElementById('cron-edit-prompt').value.trim();
  var channel = document.getElementById('cron-edit-channel').value.trim();
  var model = document.getElementById('cron-edit-model').value.trim();
  var enabled = document.getElementById('cron-edit-enabled').checked;

  // Parse schedule
  var schedule = null;
  var everyMatch = schedStr.match(/^every\s+(\d+)\s*min/i);
  if (everyMatch) {
    schedule = { kind: 'every', everyMs: parseInt(everyMatch[1]) * 60000 };
  } else if (schedStr && !schedStr.startsWith('{')) {
    schedule = { kind: 'cron', expr: schedStr };
    if (tz) schedule.tz = tz;
  }

  if (mode === 'create') {
    if (!name) { showCronToast('Name is required'); return; }
    if (!schedule) { showCronToast('Schedule is required'); return; }
    var body = { name: name, schedule: schedule, enabled: enabled };
    if (prompt) body.prompt = prompt;
    if (channel) body.channel = channel;
    if (model) body.model = model;
    try {
      var res = await fetch('/api/cron/create', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(body)});
      var data = await res.json();
      if (data.error) { showCronToast('Error: ' + data.error); return; }
      showCronToast(data.message || 'Job created');
      closeCronEditModal();
      loadCrons();
    } catch(e) { showCronToast('Error: ' + e.message); }
  } else {
    var patch = { enabled: enabled };
    if (name) patch.name = name;
    if (schedule) patch.schedule = schedule;
    if (prompt) patch.prompt = prompt;
    if (channel) patch.channel = channel;
    if (model) patch.model = model;
    try {
      var res = await fetch('/api/cron/update', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({jobId: jobId, patch: patch})});
      var data = await res.json();
      showCronToast(data.message || 'Job updated');
      closeCronEditModal();
      loadCrons();
    } catch(e) { showCronToast('Error: ' + e.message); }
  }
}

function showCronError(el, msg, ts, fails) {
  // Remove any existing popover
  var old = document.querySelector('.cron-error-popover');
  if (old) old.remove();
  var rect = el.getBoundingClientRect();
  var pop = document.createElement('div');
  pop.className = 'cron-error-popover';
  pop.style.top = (rect.bottom + 8) + 'px';
  pop.style.left = Math.min(rect.left, window.innerWidth - 420) + 'px';
  var h = '<span class="ep-close" onclick="this.parentElement.remove()">&times;</span>';
  h += '<div class="ep-label">Error Message</div><div class="ep-value">' + msg + '</div>';
  h += '<div class="ep-label">Failed At</div><div class="ep-value ts">' + ts + '</div>';
  if (fails) h += '<div class="ep-label">Consecutive Failures</div><div class="ep-value">' + fails + '</div>';
  pop.innerHTML = h;
  document.body.appendChild(pop);
  // Close on outside click
  setTimeout(function() {
    document.addEventListener('click', function handler(e) {
      if (!pop.contains(e.target) && e.target !== el) { pop.remove(); document.removeEventListener('click', handler); }
    });
  }, 10);
}

function confirmCronFix(jobId, jobName) {
  var modal = document.createElement('div');
  modal.className = 'cron-confirm-modal';
  modal.innerHTML = '<div class="cron-confirm-box"><p>Ask AI to diagnose and fix<br><strong>' + jobName + '</strong>?</p><button class="confirm-yes" onclick="submitCronFix(\'' + jobId + '\');this.closest(\'.cron-confirm-modal\').remove()">Yes, fix it</button><button class="confirm-no" onclick="this.closest(\'.cron-confirm-modal\').remove()">Cancel</button></div>';
  document.body.appendChild(modal);
  modal.addEventListener('click', function(e) { if (e.target === modal) modal.remove(); });
}

async function submitCronFix(jobId) {
  try {
    var res = await fetch('/api/cron/fix', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({jobId: jobId})});
    var data = await res.json();
    showCronToast(data.message || 'Fix request sent to AI agent');
  } catch(e) {
    showCronToast('Error: ' + e.message);
  }
}

function showCronToast(msg) {
  var t = document.createElement('div');
  t.className = 'cron-toast';
  t.textContent = msg;
  document.body.appendChild(t);
  setTimeout(function() { t.style.opacity = '0'; setTimeout(function() { t.remove(); }, 300); }, 3000);
}

function formatSchedule(s) {
  if (s.kind === 'cron') {
    var expr = s.expr;
    var human = cronToHuman(expr);
    var label = 'cron: ' + expr;
    if (human) label += ' \u2014 ' + human;
    if (s.tz) label += ' (' + s.tz + ')';
    return label;
  }
  if (s.kind === 'every') {
    var mins = s.everyMs / 60000;
    if (mins >= 60) return 'every ' + (mins/60).toFixed(0) + 'h';
    return 'every ' + mins + ' min';
  }
  if (s.kind === 'at') return 'once at ' + formatTime(s.atMs);
  return JSON.stringify(s);
}

function cronToHuman(expr) {
  // Translate common cron expressions to human-readable text
  if (!expr) return '';
  var parts = expr.trim().split(/\s+/);
  if (parts.length < 5) return '';
  var min = parts[0], hr = parts[1], dom = parts[2], mon = parts[3], dow = parts[4];
  var days = ['Sunday','Monday','Tuesday','Wednesday','Thursday','Friday','Saturday'];
  // Every minute
  if (expr === '* * * * *') return 'every minute';
  // Every N minutes
  var evMin = min.match(/^\*\/(\d+)$/);
  if (evMin && hr === '*' && dom === '*' && mon === '*' && dow === '*') return 'every ' + evMin[1] + ' minutes';
  // Every hour at minute X
  if (hr === '*' && dom === '*' && mon === '*' && dow === '*' && /^\d+$/.test(min)) return 'every hour at :' + min.padStart(2,'0');
  // Every N hours
  var evHr = hr.match(/^\*\/(\d+)$/);
  if (evHr && dom === '*' && mon === '*' && dow === '*') {
    if (min === '0') return 'every ' + evHr[1] + ' hours';
    return 'every ' + evHr[1] + ' hours at :' + min.padStart(2,'0');
  }
  // Daily
  if (dom === '*' && mon === '*' && dow === '*' && /^\d+$/.test(hr) && /^\d+$/.test(min)) {
    return 'daily at ' + hr.padStart(2,'0') + ':' + min.padStart(2,'0');
  }
  // Weekdays
  if (dow === '1-5' && /^\d+$/.test(hr) && /^\d+$/.test(min)) return 'weekdays at ' + hr.padStart(2,'0') + ':' + min.padStart(2,'0');
  if (dow === '0,6' && /^\d+$/.test(hr) && /^\d+$/.test(min)) return 'weekends at ' + hr.padStart(2,'0') + ':' + min.padStart(2,'0');
  // Single day of week
  var dowSingle = dow.match(/^(\d)$/);
  if (dowSingle && /^\d+$/.test(hr) && /^\d+$/.test(min)) return (days[parseInt(dowSingle[1])]||'day') + 's at ' + hr.padStart(2,'0') + ':' + min.padStart(2,'0');
  // Weekly (multiple days)
  if (/^[\d,]+$/.test(dow) && /^\d+$/.test(hr)) return 'weekly at ' + hr.padStart(2,'0') + ':' + min.padStart(2,'0');
  return '';
}

async function loadLogs() {
  if (window.CLOUD_MODE) {
    var el = document.getElementById('logs-full');
    if (el) el.innerHTML = '<div style="color:var(--text-secondary);padding:24px;text-align:center;font-size:13px;">Full logs are not available in cloud view. Use the live stream on the Flow tab.</div>';
    return;
  }
  var lines = document.getElementById('log-lines').value;
  var data = await fetch('/api/logs?lines=' + lines).then(r => r.json());
  renderLogs('logs-full', data.lines);
}

async function loadMemoryAnalytics() {
  var panel = document.getElementById('memory-analytics-panel');
  if (!panel || window.CLOUD_MODE) return;
  try {
    var d = await fetch('/api/memory-analytics').then(function(r){return r.json()});
    var statusColor = d.hasBloat ? '#ef4444' : (d.hasWarnings ? '#f59e0b' : '#22c55e');
    var statusLabel = d.hasBloat ? '⚠ Bloat detected' : (d.hasWarnings ? '⚡ Growing' : '✓ Healthy');
    var html = '<div class="card" style="padding:16px;margin-bottom:0">';
    // Stats row
    html += '<div style="display:flex;gap:16px;flex-wrap:wrap;align-items:center;margin-bottom:12px">';
    html += '<div style="font-size:14px;font-weight:700;color:var(--text-primary)">🧠 Memory Analytics</div>';
    html += '<div style="display:inline-flex;align-items:center;gap:6px;padding:3px 10px;border-radius:12px;font-size:11px;font-weight:600;background:' + statusColor + '22;color:' + statusColor + '">';
    html += '<span style="width:6px;height:6px;border-radius:50%;background:' + statusColor + '"></span>' + statusLabel + '</div>';
    html += '<div style="margin-left:auto;display:flex;gap:16px;font-size:12px;color:var(--text-muted)">';
    html += '<span>' + d.fileCount + ' files</span>';
    html += '<span>' + d.totalKB + ' KB total</span>';
    html += '<span>~' + d.estTokens.toLocaleString() + ' tokens</span>';
    html += '</div></div>';
    // Context budget bars
    var budgets = d.contextBudgets || {};
    var budgetNames = {'claude_200k':'Claude 200K','gpt4_128k':'GPT-4 128K','gemini_1m':'Gemini 1M'};
    html += '<div style="display:flex;gap:12px;flex-wrap:wrap;margin-bottom:12px">';
    for (var k in budgetNames) {
      if (!budgets[k]) continue;
      var b = budgets[k];
      var bColor = b.status === 'critical' ? '#ef4444' : (b.status === 'warning' ? '#f59e0b' : '#22c55e');
      html += '<div style="flex:1;min-width:160px;padding:8px 12px;border-radius:8px;background:var(--bg-secondary);border:1px solid var(--border-primary)">';
      html += '<div style="font-size:10px;color:var(--text-muted);margin-bottom:4px">' + budgetNames[k] + ' context used</div>';
      html += '<div style="height:6px;border-radius:3px;background:var(--bg-tertiary,#1e293b);overflow:hidden">';
      html += '<div style="height:100%;width:' + Math.min(b.percentUsed, 100) + '%;background:' + bColor + ';border-radius:3px;transition:width 0.3s"></div></div>';
      html += '<div style="font-size:10px;color:' + bColor + ';margin-top:2px">' + b.percentUsed + '% (' + b.memoryTokens.toLocaleString() + ' / ' + b.limit.toLocaleString() + ')</div>';
      html += '</div>';
    }
    html += '</div>';
    // Top files bar chart
    if (d.topFiles && d.topFiles.length > 0) {
      var maxSize = d.topFiles[0].sizeBytes || 1;
      html += '<div style="margin-bottom:8px">';
      html += '<div style="font-size:11px;font-weight:600;color:var(--text-secondary);margin-bottom:6px">Largest files</div>';
      d.topFiles.forEach(function(tf) {
        var pct = Math.max((tf.sizeBytes / maxSize) * 100, 2);
        var fColor = tf.status === 'critical' ? '#ef4444' : (tf.status === 'warning' ? '#f59e0b' : '#3b82f6');
        html += '<div style="display:flex;align-items:center;gap:8px;margin-bottom:3px">';
        html += '<span style="font-size:11px;color:var(--text-secondary);width:140px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;flex-shrink:0" title="' + tf.path + '">' + tf.path + '</span>';
        html += '<div style="flex:1;height:14px;border-radius:3px;background:var(--bg-tertiary,#1e293b);overflow:hidden">';
        html += '<div style="height:100%;width:' + pct + '%;background:' + fColor + ';border-radius:3px"></div></div>';
        html += '<span style="font-size:10px;color:var(--text-muted);width:50px;text-align:right;flex-shrink:0">' + tf.sizeKB + 'K</span>';
        html += '</div>';
      });
      html += '</div>';
    }
    // Recommendations
    if (d.recommendations && d.recommendations.length > 0) {
      html += '<div style="margin-top:8px;padding:8px 12px;border-radius:6px;background:' + (d.hasBloat ? '#ef444415' : '#f59e0b15') + ';border:1px solid ' + (d.hasBloat ? '#ef444433' : '#f59e0b33') + '">';
      html += '<div style="font-size:11px;font-weight:600;color:' + (d.hasBloat ? '#ef4444' : '#f59e0b') + ';margin-bottom:4px">Recommendations</div>';
      d.recommendations.forEach(function(r) {
        html += '<div style="font-size:11px;color:var(--text-secondary);margin-bottom:2px">• ' + escHtml(r.message) + '</div>';
      });
      html += '</div>';
    }
    // Daily growth sparkline (if data available)
    if (d.dailyGrowth && d.dailyGrowth.length > 1) {
      var maxBytes = Math.max.apply(null, d.dailyGrowth.map(function(g){return g.bytes})) || 1;
      var points = d.dailyGrowth.map(function(g, i) {
        var x = (i / (d.dailyGrowth.length - 1)) * 280;
        var y = 36 - (g.bytes / maxBytes) * 32;
        return x + ',' + y;
      }).join(' ');
      html += '<div style="margin-top:10px">';
      html += '<div style="font-size:11px;font-weight:600;color:var(--text-secondary);margin-bottom:4px">Daily memory files (last 30 days)</div>';
      html += '<svg width="100%" viewBox="0 0 290 40" style="max-width:400px">';
      html += '<polyline points="' + points + '" fill="none" stroke="#3b82f6" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>';
      html += '</svg></div>';
    }
    html += '</div>';
    panel.innerHTML = html;
  } catch(e) { panel.innerHTML = ''; }
}

// Switch between Summary (friendly change-history) and All files (raw explorer).
function memorySwitchView(view) {
  var summary = document.getElementById('memory-summary-view');
  var all = document.getElementById('memory-all-view');
  if (summary) summary.style.display = view === 'summary' ? 'block' : 'none';
  if (all) all.style.display = view === 'all' ? 'block' : 'none';
  document.querySelectorAll('.mem-view-tab').forEach(function(t) {
    var active = t.getAttribute('data-view') === view;
    t.style.background = active ? 'var(--bg-secondary)' : 'transparent';
    t.style.border = active ? '1px solid var(--border-primary)' : '1px solid transparent';
    t.style.color = active ? 'var(--text-primary)' : 'var(--text-muted)';
  });
  if (view === 'summary') {
    if (typeof loadSelfConfig === 'function') loadSelfConfig();
  } else {
    _loadMemoryAllFiles();
  }
}

// Entry point called by nav switchTab + loadAll bootstrap.
async function loadMemory() {
  // Default to Summary (friendly) view.
  if (typeof loadSelfConfig === 'function') loadSelfConfig();
}

// Legacy raw file explorer — runs only when "All files" is selected.
async function _loadMemoryAllFiles() {
  if (window.CLOUD_MODE) {
    var el = document.getElementById('memory-list');
    if (el) el.innerHTML = '<div style="color:var(--text-secondary);padding:24px;text-align:center;font-size:13px;">Memory files are stored locally on the agent machine and are not synced to cloud.</div>';
    return;
  }
  loadMemoryAnalytics();
  var data = await fetch('/api/memory-files').then(r => r.json());
  var el = document.getElementById('memory-list');
  // Add hover CSS once
  if (!document.getElementById('mem-ide-css')) {
    var cs = document.createElement('style');
    cs.id = 'mem-ide-css';
    cs.textContent = '.mem-file:hover,.mem-file.active{background:var(--bg-tertiary,#1e293b)!important}';
    document.head.appendChild(cs);
  }
  // IDE layout: sidebar + content viewer
  el.style.cssText = 'display:flex;height:calc(100vh - 140px);gap:0;padding:0;overflow:hidden;border-radius:8px;border:1px solid var(--border-primary)';
  el.innerHTML = '<div id="mem-sidebar" style="width:260px;min-width:200px;border-right:1px solid var(--border-primary);overflow-y:auto;background:var(--bg-secondary);flex-shrink:0">' +
    '<div style="padding:10px 14px;font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:0.8px;color:var(--text-muted);border-bottom:1px solid var(--border-primary)">Explorer</div>' +
    '<div id="mem-tree" style="padding:4px 0"></div></div>' +
    '<div id="mem-content" style="flex:1;overflow-y:auto;background:var(--bg-primary);padding:0">' +
    '<div style="display:flex;align-items:center;justify-content:center;height:100%;color:var(--text-muted);font-size:13px">' +
    '<div style="text-align:center"><div style="font-size:32px;margin-bottom:8px">📂</div>Select a file to view</div></div></div>';
  // Hide old file-viewer
  var oldViewer = document.getElementById('file-viewer');
  if (oldViewer) oldViewer.style.display = 'none';
  var sidebar = document.getElementById('mem-tree');
  var viewer = document.getElementById('mem-content');
  // Group files: root vs folders
  var roots = [], folders = {};
  data.forEach(function(f) {
    var parts = f.path.split('/');
    var name = f.path;
    if (parts.length <= 1) { roots.push(f); }
    else { var dir = parts.slice(0, -1).join('/'); if (!folders[dir]) folders[dir] = []; folders[dir].push(f); }
  });
  var html = '';
  roots.forEach(function(f) {
    var icon = f.path.endsWith('.md') ? '📝' : '📄';
    var sz = f.size > 1024 ? (f.size/1024).toFixed(1) + 'K' : f.size + 'B';
    html += '<div class="mem-file" data-path="' + escHtml(f.path) + '" style="display:flex;align-items:center;gap:6px;padding:5px 14px;cursor:pointer;font-size:12px;color:var(--text-secondary)">' +
      '<span style="flex-shrink:0">' + icon + '</span>' +
      '<span style="flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">' + escHtml(f.path) + '</span>' +
      '<span style="color:var(--text-muted);font-size:10px;flex-shrink:0">' + sz + '</span></div>';
  });
  Object.keys(folders).sort().forEach(function(dir) {
    html += '<div style="padding:8px 14px 4px;font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:0.5px;color:var(--text-muted);display:flex;align-items:center;gap:4px"><span>📁</span>' + escHtml(dir) + '</div>';
    folders[dir].forEach(function(f) {
      var icon = f.path.endsWith('.md') ? '📝' : '📄';
      var short = f.path.split('/').pop();
      var sz = f.size > 1024 ? (f.size/1024).toFixed(1) + 'K' : f.size + 'B';
      html += '<div class="mem-file" data-path="' + escHtml(f.path) + '" style="display:flex;align-items:center;gap:6px;padding:5px 14px 5px 28px;cursor:pointer;font-size:12px;color:var(--text-secondary)">' +
        '<span style="flex-shrink:0">' + icon + '</span>' +
        '<span style="flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">' + escHtml(short) + '</span>' +
        '<span style="color:var(--text-muted);font-size:10px;flex-shrink:0">' + sz + '</span></div>';
    });
  });
  sidebar.innerHTML = html || '<div style="padding:16px;color:var(--text-muted)">No files</div>';
  // Click to load file content in viewer
  sidebar.querySelectorAll('.mem-file').forEach(function(row) {
    row.onclick = async function() {
      sidebar.querySelectorAll('.mem-file').forEach(function(r) { r.classList.remove('active'); });
      this.classList.add('active');
      var p = this.dataset.path;
      viewer.innerHTML = '<div style="padding:8px 16px;border-bottom:1px solid var(--border-primary);display:flex;align-items:center;gap:8px;background:var(--bg-secondary);position:sticky;top:0;z-index:1">' +
        '<span style="font-size:12px">📝</span><span style="font-size:12px;font-weight:600;color:var(--text-primary)">' + escHtml(p) + '</span>' +
        '<span style="margin-left:auto;font-size:10px;color:var(--text-muted)">Loading...</span></div>' +
        '<pre style="margin:0;padding:16px;font-family:monospace;font-size:12px;line-height:1.6;color:var(--text-secondary);white-space:pre-wrap;word-break:break-word">Loading...</pre>';
      try {
        var d = await fetch('/api/file?path=' + encodeURIComponent(p)).then(function(r) { return r.json(); });
        if (d.error) { viewer.querySelector('pre').textContent = 'Error: ' + d.error; return; }
        var content = d.content || '';
        viewer.innerHTML = '<div style="padding:8px 16px;border-bottom:1px solid var(--border-primary);display:flex;align-items:center;gap:8px;background:var(--bg-secondary);position:sticky;top:0;z-index:1">' +
          '<span style="font-size:12px">📝</span><span style="font-size:12px;font-weight:600;color:var(--text-primary)">' + escHtml(p) + '</span>' +
          '<span style="margin-left:auto;font-size:10px;color:var(--text-muted)">' + content.length + ' chars</span></div>' +
          '<pre style="margin:0;padding:16px;font-family:monospace;font-size:12px;line-height:1.6;color:var(--text-secondary);white-space:pre-wrap;word-break:break-word">' + escHtml(content) + '</pre>';
      } catch(e) { viewer.querySelector('pre').textContent = 'Failed: ' + e.message; }
    };
  });
}

// ===== Mission Control Summary Bar =====
var _mcData = null;
var _mcExpanded = null;
var _mcRefreshTimer = null;

async function loadMCTasks() {
  try {
    var r = await fetch('/api/mc-tasks');
    var data = await r.json();
    var wrapper = document.getElementById('mc-bar-wrapper');
    if (!data.available) { wrapper.style.display='none'; return; }
    wrapper.style.display='';
    var tasks = data.tasks || [];
    var cols = [
      {key:'inbox', label:'Inbox', color:'#3b82f6', bg:'#3b82f620', icon:'📥', tasks:[]},
      {key:'in_progress', label:'In Progress', color:'#16a34a', bg:'#16a34a20', icon:'🔄', tasks:[]},
      {key:'review', label:'Review', color:'#d97706', bg:'#d9770620', icon:'👀', tasks:[]},
      {key:'blocked', label:'Blocked', color:'#dc2626', bg:'#dc262620', icon:'🚫', tasks:[]},
      {key:'done', label:'Done', color:'#6b7280', bg:'#6b728020', icon:'✅', tasks:[]}
    ];
    tasks.forEach(function(t) {
      var col = t.column || 'inbox';
      var c = cols.find(function(x){return x.key===col;});
      if (c) c.tasks.push(t);
    });
    _mcData = cols;
    var bar = document.getElementById('mc-summary-bar');
    var html = '<span style="font-size:12px;font-weight:700;color:var(--text-tertiary);margin-right:4px;">🎯 MC</span>';
    cols.forEach(function(c, i) {
      if (i > 0) html += '<span style="color:var(--text-faint);font-size:12px;margin:0 2px;">│</span>';
      var active = _mcExpanded === c.key ? 'outline:2px solid '+c.color+';outline-offset:-2px;' : '';
      html += '<span data-col-key="'+c.key+'" onclick="toggleMCColumn(this.dataset.colKey)" style="cursor:pointer;display:inline-flex;align-items:center;gap:4px;padding:4px 10px;border-radius:16px;background:'+c.bg+';'+active+'transition:all 0.15s;">';
      html += '<span style="font-size:12px;">'+c.icon+'</span>';
      html += '<span style="font-size:11px;color:var(--text-secondary);">'+c.label+'</span>';
      html += '<span style="font-size:12px;font-weight:700;color:'+c.color+';min-width:16px;text-align:center;">'+c.tasks.length+'</span>';
      html += '</span>';
    });
    var total = tasks.length;
    html += '<span style="margin-left:auto;font-size:10px;color:var(--text-muted);">'+total+' tasks</span>';
    bar.innerHTML = html;
    if (_mcExpanded) renderMCExpanded(_mcExpanded);
  } catch(e) {
    var w = document.getElementById('mc-bar-wrapper');
    if (w) w.style.display='none';
  }
}

function toggleMCColumn(key) {
  if (_mcExpanded === key) { _mcExpanded = null; document.getElementById('mc-expanded-section').style.display='none'; }
  else { _mcExpanded = key; renderMCExpanded(key); }
  // Re-render bar to update active pill
  if (_mcData) {
    var bar = document.getElementById('mc-summary-bar');
    var cols = _mcData;
    var html = '<span style="font-size:12px;font-weight:700;color:var(--text-tertiary);margin-right:4px;">🎯 MC</span>';
    cols.forEach(function(c, i) {
      if (i > 0) html += '<span style="color:var(--text-faint);font-size:12px;margin:0 2px;">│</span>';
      var active = _mcExpanded === c.key ? 'outline:2px solid '+c.color+';outline-offset:-2px;' : '';
      html += '<span data-col-key="'+c.key+'" onclick="toggleMCColumn(this.dataset.colKey)" style="cursor:pointer;display:inline-flex;align-items:center;gap:4px;padding:4px 10px;border-radius:16px;background:'+c.bg+';'+active+'transition:all 0.15s;">';
      html += '<span style="font-size:12px;">'+c.icon+'</span>';
      html += '<span style="font-size:11px;color:var(--text-secondary);">'+c.label+'</span>';
      html += '<span style="font-size:12px;font-weight:700;color:'+c.color+';min-width:16px;text-align:center;">'+c.tasks.length+'</span>';
      html += '</span>';
    });
    var total = cols.reduce(function(s,c){return s+c.tasks.length;},0);
    html += '<span style="margin-left:auto;font-size:10px;color:var(--text-muted);">'+total+' tasks</span>';
    bar.innerHTML = html;
  }
}

function renderMCExpanded(key) {
  var sec = document.getElementById('mc-expanded-section');
  if (!_mcData) { sec.style.display='none'; return; }
  var col = _mcData.find(function(c){return c.key===key;});
  if (!col || col.tasks.length === 0) { sec.style.display='block'; sec.innerHTML='<div style="font-size:12px;color:var(--text-muted);padding:4px;">No tasks in '+col.label+'</div>'; return; }
  sec.style.display='block';
  var html = '<div style="font-size:11px;font-weight:700;color:'+col.color+';margin-bottom:8px;">'+col.icon+' '+col.label+' ('+col.tasks.length+')</div>';
  html += '<div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:6px;">';
  col.tasks.forEach(function(t) {
    var title = t.title || '--';
    var badge = t.companyId ? '<span style="font-size:9px;background:var(--bg-secondary);padding:1px 5px;border-radius:3px;color:var(--text-muted);margin-left:6px;">'+t.companyId+'</span>' : '';
    html += '<div style="font-size:12px;color:var(--text-secondary);padding:4px 8px;background:var(--bg-secondary);border-radius:6px;border-left:3px solid '+col.color+';white-space:nowrap;overflow:hidden;text-overflow:ellipsis;" title="'+(t.title||'').replace(/"/g,'&quot;')+'">'+title+badge+'</div>';
  });
  html += '</div>';
  sec.innerHTML = html;
}

// MC auto-refresh every 30s
if (!_mcRefreshTimer) {
  _mcRefreshTimer = setInterval(function() {
    if (document.querySelector('.nav-tab.active')?.textContent?.trim() === 'Overview') loadMCTasks();
  }, 30000);
}

// ===== Health Checks =====
async function loadHealth() {
  try {
    var data = await fetch('/api/health').then(r => r.json());
    data.checks.forEach(function(c) {
      var dotEl = document.getElementById('health-dot-' + c.id);
      var detailEl = document.getElementById('health-detail-' + c.id);
      var itemEl = document.getElementById('health-' + c.id);
      if (dotEl) { dotEl.className = 'health-dot ' + c.color; }
      if (detailEl) { detailEl.textContent = c.detail; }
      if (itemEl) { itemEl.className = 'health-item ' + c.status; }
    });
  } catch(e) {}
}

// Health SSE auto-refresh
var healthStream = null;
function startHealthStream() {
  if (window.CLOUD_MODE) return;
  if (healthStream) healthStream.close();
  healthStream = new EventSource('/api/health-stream' + (localStorage.getItem('clawmetry-token') ? '?token=' + encodeURIComponent(localStorage.getItem('clawmetry-token')) : ''));
  healthStream.onmessage = function(e) {
    try {
      var data = JSON.parse(e.data);
      data.checks.forEach(function(c) {
        var dotEl = document.getElementById('health-dot-' + c.id);
        var detailEl = document.getElementById('health-detail-' + c.id);
        var itemEl = document.getElementById('health-' + c.id);
        if (dotEl) { dotEl.className = 'health-dot ' + c.color; }
        if (detailEl) { detailEl.textContent = c.detail; }
        if (itemEl) { itemEl.className = 'health-item ' + c.status; }
      });
    } catch(ex) {}
  };
  healthStream.onerror = function() { setTimeout(startHealthStream, 30000); };
}

// ===== System Health Panel =====
async function loadSystemHealth() {
  try {
    var d = await fetchJsonWithTimeout('/api/system-health', 4000);
    var services = Array.isArray(d.services) ? d.services : [];
    var channels = Array.isArray(d.channels) ? d.channels : [];
    var disks = Array.isArray(d.disks) ? d.disks : [];
    var crons = (d.crons && typeof d.crons === 'object') ? d.crons : {enabled: 0, ok24h: 0, failed: []};
    var subagents = (d.subagents && typeof d.subagents === 'object') ? d.subagents : {runs: 0, successPct: 0};

    // Services
    var shtml = '';
    services.forEach(function(s) {
      var dot = s.up ? '🟢' : '🔴';
      shtml += '<div style="display:flex;align-items:center;gap:6px;padding:8px 14px;background:var(--bg-secondary);border-radius:8px;border:1px solid var(--border-secondary);font-size:13px;">'
        + dot + ' <span style="font-weight:600;color:var(--text-primary);">' + s.name + '</span>'
        + '<span style="color:var(--text-muted);font-size:11px;margin-left:auto;">:' + s.port + '</span></div>';
    });
    if (!shtml) {
      shtml = '<div style="padding:8px 10px;background:var(--bg-secondary);border:1px solid var(--border-secondary);border-radius:8px;font-size:12px;color:var(--text-muted);">No service data available</div>';
    }
    document.getElementById('sh-services').innerHTML = shtml;

    // Channels
    var chWrap = document.getElementById('sh-channels-wrap');
    var chEl = document.getElementById('sh-channels');
    if (chEl) {
      if (channels.length === 0) {
        if (chWrap) chWrap.style.display = 'none';
      } else {
        if (chWrap) chWrap.style.display = '';
        var chhtml = '';
        channels.forEach(function(ch) {
          var dotColor = ch.status === 'connected' ? '#16a34a' : (ch.status === 'configured' ? '#d97706' : '#6b7280');
          var dotGlow = ch.status === 'connected' ? 'rgba(22,163,74,0.5)' : (ch.status === 'configured' ? 'rgba(217,119,6,0.35)' : 'transparent');
          var borderColor = ch.status === 'connected' ? 'rgba(22,163,74,0.3)' : 'var(--border-secondary)';
          chhtml += '<div style="display:flex;align-items:center;gap:7px;padding:7px 12px;background:var(--bg-secondary);border-radius:8px;border:1px solid ' + borderColor + ';font-size:12px;" title="' + ch.detail + '">'
            + '<span style="width:9px;height:9px;border-radius:50%;background:' + dotColor + ';box-shadow:0 0 6px ' + dotGlow + ';flex-shrink:0;display:inline-block;"></span>'
            + ch.icon + ' <span style="font-weight:600;color:var(--text-primary);">' + ch.name + '</span>'
            + '<span style="color:var(--text-muted);font-size:10px;margin-left:4px;">' + ch.detail + '</span></div>';
        });
        chEl.innerHTML = chhtml;
      }
    }

    // Disks
    var dhtml = '';
    disks.forEach(function(dk) {
      var barColor = dk.pct > 90 ? '#dc2626' : (dk.pct > 75 ? '#d97706' : '#16a34a');
      dhtml += '<div style="margin-bottom:10px;">'
        + '<div style="display:flex;justify-content:space-between;font-size:12px;margin-bottom:4px;">'
        + '<span style="font-weight:600;color:var(--text-primary);">' + dk.mount + '</span>'
        + '<span style="color:var(--text-muted);">' + dk.used_gb + ' / ' + dk.total_gb + ' GB (' + dk.pct + '%)</span></div>'
        + '<div style="background:var(--bg-secondary);border-radius:6px;height:10px;overflow:hidden;border:1px solid var(--border-secondary);">'
        + '<div style="width:' + dk.pct + '%;height:100%;background:' + barColor + ';border-radius:6px;transition:width 0.5s;"></div>'
        + '</div></div>';
    });
    if (!dhtml) {
      dhtml = '<div style="padding:8px 10px;background:var(--bg-secondary);border:1px solid var(--border-secondary);border-radius:8px;font-size:12px;color:var(--text-muted);">No disk data available</div>';
    }
    document.getElementById('sh-disks').innerHTML = dhtml;

    // Crons
    var c = crons;
    var cFailed = Array.isArray(c.failed) ? c.failed : [];
    var chtml = '<div style="display:flex;gap:12px;flex-wrap:wrap;">'
      + '<div style="flex:1;min-width:100px;padding:12px 16px;background:var(--bg-secondary);border-radius:8px;text-align:center;border:1px solid var(--border-secondary);">'
      + '<div style="font-size:24px;font-weight:700;color:var(--text-primary,#e6edf5);">' + (c.enabled || 0) + '</div>'
      + '<div style="font-size:11px;color:var(--text-muted,#7c8a9d);text-transform:uppercase;letter-spacing:0.5px;">Enabled</div></div>'
      + '<div style="flex:1;min-width:100px;padding:12px 16px;background:var(--bg-secondary,#1a1a2e);border-radius:8px;text-align:center;border:1px solid var(--border-secondary,#333);">'
      + '<div style="font-size:24px;font-weight:700;color:var(--text-success,#22c55e);">' + (c.ok24h || 0) + '</div>'
      + '<div style="font-size:11px;color:var(--text-muted,#7c8a9d);text-transform:uppercase;letter-spacing:0.5px;">OK (24h)</div></div></div>';
    if (cFailed.length > 0) {
      chtml += '<div style="margin-top:8px;padding:10px 14px;background:var(--bg-error);border:1px solid rgba(220,38,38,0.2);border-radius:8px;font-size:12px;color:var(--text-error);">';
      cFailed.forEach(function(f) { chtml += '<div>❌ ' + f + '</div>'; });
      chtml += '</div>';
    }
    document.getElementById('sh-crons').innerHTML = chtml;

    // Sub-agents
    var sa = subagents;
    var pctColor = sa.successPct >= 100 ? 'var(--text-success)' : (sa.successPct > 80 ? 'var(--text-warning)' : 'var(--text-error)');
    var sahtml = '<div style="display:flex;gap:12px;flex-wrap:wrap;">'
      + '<div style="flex:1;min-width:100px;padding:12px 16px;background:var(--bg-secondary);border-radius:8px;text-align:center;border:1px solid var(--border-secondary);">'
      + '<div style="font-size:24px;font-weight:700;color:var(--text-primary,#e6edf5);">' + sa.runs + '</div>'
      + '<div style="font-size:11px;color:var(--text-muted,#7c8a9d);text-transform:uppercase;letter-spacing:0.5px;">Runs</div></div>'
      + '<div style="flex:1;min-width:100px;padding:12px 16px;background:var(--bg-secondary,#1a1a2e);border-radius:8px;text-align:center;border:1px solid var(--border-secondary,#333);">'
      + '<div style="font-size:24px;font-weight:700;color:' + pctColor + ';">' + sa.successPct + '%</div>'
      + '<div style="font-size:11px;color:var(--text-muted,#7c8a9d);text-transform:uppercase;letter-spacing:0.5px;">Success</div></div></div>';
    document.getElementById('sh-subagents').innerHTML = sahtml;

    // Delegation chain panel (AgentWeave-inspired provenance view)
    try {
      var chainData = await fetch('/api/delegation-tree').then(function(r){return r.json();}).catch(function(){return {chains:[]};});
      var chains = (chainData && chainData.chains) || [];
      var chainsEl = document.getElementById('delegation-chains-panel');
      if (chainsEl) {
        if (chains.length === 0) {
          chainsEl.innerHTML = '';
        } else {
          var totalCost = chainData.total_chain_cost_usd || 0;
          var totalSA = chainData.total_subagents || 0;
          var usd_per_tok = 3.0 / 1000000;
          var chtml = '<div style="font-size:11px;text-transform:uppercase;letter-spacing:1.5px;color:var(--text-muted);font-weight:600;margin-bottom:6px;">Delegation Chains</div>';
          chtml += '<div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:8px;">';
          chtml += '<span style="font-size:12px;color:var(--text-muted);">' + totalSA + ' sub-agents across ' + chains.length + ' chains</span>';
          chtml += '<span style="font-size:11px;color:var(--text-success);font-weight:600;">$' + totalCost.toFixed(4) + ' total</span>';
          chtml += '</div>';
          chains.slice(0, 5).forEach(function(chain) {
            var ch = chain.parent_channel || 'unknown';
            var chIcon = ch === 'telegram' ? '✈️' : ch === 'whatsapp' ? '💬' : ch === 'discord' ? '🎮' : ch === 'main' ? '🖥️' : '🌐';
            chtml += '<div style="background:var(--bg-secondary);border:1px solid var(--border-primary);border-radius:8px;margin-bottom:6px;overflow:hidden;">';
            chtml += '<div style="padding:6px 10px;display:flex;align-items:center;gap:6px;background:var(--bg-tertiary);border-bottom:1px solid var(--border-secondary);">';
            chtml += '<span>' + chIcon + '</span>';
            chtml += '<span style="font-size:11px;font-weight:600;color:var(--text-primary);flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">' + escHtml(chain.parent_display || chain.parent_key) + '</span>';
            var chainTokStr = chain.chain_tokens >= 1000 ? (chain.chain_tokens/1000).toFixed(0)+'K' : chain.chain_tokens;
            chtml += '<span style="font-size:10px;color:var(--text-muted);white-space:nowrap;">' + chain.child_count + ' agents &bull; ' + chainTokStr + ' tok &bull; <span style="color:var(--text-success);">$' + chain.chain_cost_usd.toFixed(4) + '</span></span>';
            chtml += '</div>';
            chain.children.slice(0, 4).forEach(function(child) {
              var dot = child.status === 'active' ? '#16a34a' : child.status === 'idle' ? '#d97706' : '#6b7280';
              var tokStr = child.total_tokens >= 1000 ? (child.total_tokens/1000).toFixed(0)+'K' : child.total_tokens;
              chtml += '<div style="padding:4px 10px 4px 20px;display:flex;align-items:center;gap:6px;border-bottom:1px solid var(--border-secondary);font-size:11px;">';
              chtml += '<span style="width:6px;height:6px;border-radius:50%;background:' + dot + ';flex-shrink:0;"></span>';
              chtml += '<span style="color:var(--text-secondary);font-weight:600;flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">' + escHtml(child.label) + '</span>';
              chtml += '<span style="background:var(--bg-accent);color:var(--bg-primary);padding:1px 5px;border-radius:6px;font-size:9px;font-weight:600;white-space:nowrap;">' + escHtml((child.model||'').split('-').slice(0,2).join('-')) + '</span>';
              chtml += '<span style="color:var(--text-muted);font-size:10px;white-space:nowrap;">' + tokStr + 'tok $' + child.cost_usd.toFixed(4) + '</span>';
              chtml += '</div>';
            });
            if (chain.children.length > 4) {
              chtml += '<div style="padding:3px 20px;font-size:10px;color:var(--text-muted);">+ ' + (chain.children.length - 4) + ' more</div>';
            }
            chtml += '</div>';
          });
          if (chains.length > 5) {
            chtml += '<div style="font-size:10px;color:var(--text-muted);text-align:center;padding:2px 0;">+ ' + (chains.length - 5) + ' more chains</div>';
          }
          chainsEl.innerHTML = chtml;
        }
      }
    } catch(e) { /* delegation tree is optional */ }

    // Heartbeat status in system health
    try {
      var hbData = await fetch('/api/heartbeat-status').then(function(r){return r.json();});
      var hbEl = document.getElementById('sh-heartbeat');
      if (hbEl) {
        var hbStatus = hbData.status || 'unknown';
        var hbDot = hbStatus === 'ok' ? '🟢' : (hbStatus === 'warning' ? '🟡' : (hbStatus === 'silent' ? '🔴' : '⚪'));
        var hbLabel = hbStatus === 'ok' ? 'Healthy' : (hbStatus === 'warning' ? 'Delayed' : (hbStatus === 'silent' ? 'SILENT' : 'No data yet'));
        var hbGap = hbData.gap_seconds;
        var hbDetail = '';
        if (hbGap != null) {
          hbDetail = hbGap >= 3600 ? Math.floor(hbGap/3600) + 'h ' + Math.floor((hbGap%3600)/60) + 'm ago' : Math.floor(hbGap/60) + 'm ago';
        }
        var hbInterval = hbData.interval_seconds ? Math.floor(hbData.interval_seconds / 60) : 0;
        var hbColor = hbStatus === 'ok' ? 'var(--text-success)' : (hbStatus === 'warning' ? '#f59e0b' : (hbStatus === 'silent' ? 'var(--text-error)' : 'var(--text-muted)'));
        var hbIntervalStr = hbInterval > 0 ? 'every ' + hbInterval + 'm' : '';
        hbEl.innerHTML = '<div style="display:flex;align-items:center;gap:8px;padding:8px 14px;background:var(--bg-secondary);border-radius:8px;border:1px solid var(--border-secondary);font-size:13px;">'
          + hbDot + ' <span style="font-weight:600;color:' + hbColor + ';">' + hbLabel + '</span>'
          + (hbDetail ? '<span style="color:var(--text-muted);font-size:11px;margin-left:auto;">Last: ' + hbDetail + (hbIntervalStr ? ' (' + hbIntervalStr + ')' : '') + '</span>' : (hbIntervalStr ? '<span style="color:var(--text-muted);font-size:11px;margin-left:auto;">' + hbIntervalStr + '</span>' : ''))
          + '</div>';
      }
    } catch(e) {}

    // Sandbox Status (conditional)
    var sbWrap = document.getElementById('sh-sandbox-wrap');
    var sbEl = document.getElementById('sh-sandbox');
    if (d.sandbox && sbEl) {
      var sb = d.sandbox;
      var sbDot = sb.status === 'running' ? '🟢' : (sb.status === 'error' ? '🔴' : '🟡');
      var sbColor = sb.status === 'running' ? 'var(--text-success,#22c55e)' : (sb.status === 'error' ? 'var(--text-error,#dc2626)' : '#d97706');
      sbEl.innerHTML = '<div style="display:flex;align-items:center;gap:8px;padding:8px 14px;background:var(--bg-secondary);border-radius:8px;border:1px solid var(--border-secondary);font-size:13px;">'
        + sbDot + ' <span style="font-weight:600;color:' + sbColor + ';">' + (sb.name || 'Sandbox') + '</span>'
        + '<span style="color:var(--text-muted);font-size:11px;margin-left:auto;">' + (sb.type || '') + '</span></div>';
      if (sbWrap) sbWrap.style.display = '';
    } else if (sbWrap) { sbWrap.style.display = 'none'; }

    // Inference Provider (conditional)
    var infWrap = document.getElementById('sh-inference-wrap');
    var infEl = document.getElementById('sh-inference');
    if (d.inference && infEl) {
      var inf = d.inference;
      infEl.innerHTML = '<div style="display:flex;align-items:center;gap:8px;padding:8px 14px;background:var(--bg-secondary);border-radius:8px;border:1px solid var(--border-secondary);font-size:13px;">'
        + '🤖 <span style="font-weight:600;color:var(--text-primary);">' + (inf.provider || 'Unknown') + '</span>'
        + (inf.model ? '<span style="color:var(--text-muted);font-size:11px;margin-left:auto;font-family:monospace;">' + inf.model + '</span>' : '')
        + '</div>';
      if (infWrap) infWrap.style.display = '';
    } else if (infWrap) { infWrap.style.display = 'none'; }

    // Security Posture (conditional)
    var secWrap = document.getElementById('sh-security-wrap');
    var secEl = document.getElementById('sh-security');
    if (d.security && secEl) {
      var sec = d.security;
      var badges = '';
      if (sec.sandbox_enabled) badges += '<span style="display:inline-block;padding:2px 8px;border-radius:4px;font-size:11px;font-weight:600;background:rgba(34,197,94,0.15);color:#22c55e;margin-right:4px;">🔒 Sandboxed</span>';
      if (sec.auth_enabled) badges += '<span style="display:inline-block;padding:2px 8px;border-radius:4px;font-size:11px;font-weight:600;background:rgba(34,197,94,0.15);color:#22c55e;margin-right:4px;">🔑 Auth</span>';
      if (sec.localhost_only) badges += '<span style="display:inline-block;padding:2px 8px;border-radius:4px;font-size:11px;font-weight:600;background:rgba(34,197,94,0.15);color:#22c55e;margin-right:4px;">🏠 Localhost</span>';
      else if (sec.bind_address) badges += '<span style="display:inline-block;padding:2px 8px;border-radius:4px;font-size:11px;font-weight:600;background:rgba(220,38,38,0.15);color:#dc2626;margin-right:4px;">⚠️ ' + sec.bind_address + '</span>';
      if (sec.exec_security) badges += '<span style="display:inline-block;padding:2px 8px;border-radius:4px;font-size:11px;font-weight:600;background:rgba(59,130,246,0.15);color:#3b82f6;margin-right:4px;">Exec: ' + sec.exec_security + '</span>';
      if (sec.network_policy) badges += '<span style="display:inline-block;padding:2px 8px;border-radius:4px;font-size:11px;font-weight:600;background:rgba(59,130,246,0.15);color:#3b82f6;margin-right:4px;">Net: ' + sec.network_policy + '</span>';
      if (!badges) badges = '<span style="color:var(--text-muted);font-size:12px;">No security metadata detected</span>';
      secEl.innerHTML = '<div style="display:flex;flex-wrap:wrap;gap:4px;padding:8px 10px;background:var(--bg-secondary);border-radius:8px;border:1px solid var(--border-secondary);">' + badges + '</div>';
      if (secWrap) secWrap.style.display = '';
    } else if (secWrap) { secWrap.style.display = 'none'; }

    // Agent Reliability (async, non-blocking)
    _loadReliabilityWidget();

    return true;
  } catch(e) {
    console.error('System health load failed', e);
    var msg = '<div style="padding:8px 10px;background:var(--bg-secondary);border:1px solid var(--border-secondary);border-radius:8px;font-size:12px;color:var(--text-muted);">Unable to load right now</div>';
    document.getElementById('sh-services').innerHTML = msg;
    document.getElementById('sh-disks').innerHTML = msg;
    document.getElementById('sh-crons').innerHTML = msg;
    document.getElementById('sh-subagents').innerHTML = msg;
    return false;
  }
}
async function _loadReliabilityWidget() {
  var wrap = document.getElementById('sh-reliability-wrap');
  var el = document.getElementById('sh-reliability');
  if (!wrap || !el) return;
  try {
    var r = await fetch('/api/reliability').then(function(r) { return r.json(); });
    if (r.direction === 'insufficient_data' || r.error) {
      wrap.style.display = 'none';
      return;
    }
    wrap.style.display = '';
    var icon = r.direction === 'improving' ? '📈' : r.direction === 'degrading' ? '⚠️' : '✅';
    var color = r.direction === 'improving' ? '#22c55e' : r.direction === 'degrading' ? '#dc2626' : '#3b82f6';
    var label = r.direction.charAt(0).toUpperCase() + r.direction.slice(1);
    var slope = r.slope_per_session > 0 ? '+' + (r.slope_per_session * 100).toFixed(2) + '%' : (r.slope_per_session * 100).toFixed(2) + '%';
    var html = '<div style="padding:10px;background:var(--bg-secondary);border:1px solid var(--border-secondary);border-radius:8px;">';
    html += '<div style="display:flex;align-items:center;gap:8px;margin-bottom:8px;">';
    html += '<span style="font-size:16px;">' + icon + '</span>';
    html += '<span style="font-weight:700;font-size:13px;color:' + color + ';">' + label + '</span>';
    html += '<span style="font-size:11px;color:var(--text-muted);">(' + slope + '/session, ' + r.session_count + ' sessions, ' + r.window_days + 'd)</span>';
    html += '</div>';
    // Sparkline from points
    if (r.points && r.points.length > 2) {
      var pts = r.points;
      var w = 200, h = 30;
      var minD = 0, maxD = 1;
      var stepX = w / Math.max(pts.length - 1, 1);
      var pathD = '';
      for (var i = 0; i < pts.length; i++) {
        var x = Math.round(i * stepX);
        var y = Math.round(h - (pts[i].delivery * h));
        pathD += (i === 0 ? 'M' : 'L') + x + ',' + y;
      }
      var sparkColor = r.direction === 'degrading' ? '#dc2626' : r.direction === 'improving' ? '#22c55e' : '#3b82f6';
      html += '<svg width="' + w + '" height="' + h + '" viewBox="0 0 ' + w + ' ' + h + '" style="display:block;"><path d="' + pathD + '" fill="none" stroke="' + sparkColor + '" stroke-width="1.5"/></svg>';
    }
    if (r.degrading_dimensions && r.degrading_dimensions.length > 0) {
      html += '<div style="margin-top:6px;font-size:11px;color:var(--text-muted);">Degrading: ' + r.degrading_dimensions.join(', ') + '</div>';
    }
    html += '</div>';
    el.innerHTML = html;
  } catch(e) {
    wrap.style.display = 'none';
  }
}
function startSystemHealthRefresh() {
  loadSystemHealth();
  if (window._sysHealthTimer) clearInterval(window._sysHealthTimer);
  window._sysHealthTimer = setInterval(loadSystemHealth, 30000);
}

// ===== Sandbox Status (dedicated endpoint) =====
// Fetches /api/sandbox-status and renders the three cards:
//   • Sandbox card  — hides when sandbox is null
//   • Inference card — hides when inference is null
//   • Security badge — shows "Sandboxed" tag when security.sandbox_enabled is true
// Called on Overview tab load (see bootDashboard).
async function loadSandboxStatus() {
  try {
    var d = await fetch('/api/sandbox-status').then(function(r) {
      if (!r.ok) throw new Error('HTTP ' + r.status);
      return r.json();
    });

    // --- Sandbox card ---
    var sbWrap = document.getElementById('sh-sandbox-wrap');
    var sbEl   = document.getElementById('sh-sandbox');
    if (d.sandbox && sbEl) {
      var sb = d.sandbox;
      var sbDot   = sb.status === 'running' ? '🟢' : (sb.status === 'error' ? '🔴' : '🟡');
      var sbColor = sb.status === 'running'
        ? 'var(--text-success,#22c55e)'
        : (sb.status === 'error' ? 'var(--text-error,#dc2626)' : '#d97706');
      sbEl.innerHTML = '<div style="display:flex;align-items:center;gap:8px;padding:8px 14px;'
        + 'background:var(--bg-secondary);border-radius:8px;border:1px solid var(--border-secondary);font-size:13px;">'
        + sbDot + ' <span style="font-weight:600;color:' + sbColor + ';">' + (sb.name || 'Sandbox') + '</span>'
        + '<span style="color:var(--text-muted);font-size:11px;margin-left:auto;">' + (sb.type || '') + '</span></div>';
      if (sbWrap) sbWrap.style.display = '';
    } else if (sbWrap) {
      sbWrap.style.display = 'none';
    }

    // --- Inference card ---
    var infWrap = document.getElementById('sh-inference-wrap');
    var infEl   = document.getElementById('sh-inference');
    if (d.inference && infEl) {
      var inf = d.inference;
      infEl.innerHTML = '<div style="display:flex;align-items:center;gap:8px;padding:8px 14px;'
        + 'background:var(--bg-secondary);border-radius:8px;border:1px solid var(--border-secondary);font-size:13px;">'
        + '🤖 <span style="font-weight:600;color:var(--text-primary);">' + (inf.provider || 'Unknown') + '</span>'
        + (inf.model ? '<span style="color:var(--text-muted);font-size:11px;margin-left:auto;font-family:monospace;">'
            + inf.model + '</span>' : '')
        + '</div>';
      if (infWrap) infWrap.style.display = '';
    } else if (infWrap) {
      infWrap.style.display = 'none';
    }

    // --- Security badge (Sandboxed) ---
    var secWrap = document.getElementById('sh-security-wrap');
    var secEl   = document.getElementById('sh-security');
    if (d.security && secEl) {
      var sec = d.security;
      var badges = '';
      if (sec.sandbox_enabled) {
        badges += '<span style="display:inline-block;padding:2px 8px;border-radius:4px;font-size:11px;'
          + 'font-weight:600;background:rgba(34,197,94,0.15);color:#22c55e;margin-right:4px;">🔒 Sandboxed</span>';
      }
      if (sec.network_policy) {
        badges += '<span style="display:inline-block;padding:2px 8px;border-radius:4px;font-size:11px;'
          + 'font-weight:600;background:rgba(59,130,246,0.15);color:#3b82f6;margin-right:4px;">'
          + 'Net: ' + sec.network_policy + '</span>';
      }
      if (!badges) badges = '<span style="color:var(--text-muted);font-size:12px;">No security metadata detected</span>';
      secEl.innerHTML = '<div style="display:flex;flex-wrap:wrap;gap:4px;padding:8px 10px;'
        + 'background:var(--bg-secondary);border-radius:8px;border:1px solid var(--border-secondary);">'
        + badges + '</div>';
      if (secWrap) secWrap.style.display = '';
    } else if (secWrap) {
      secWrap.style.display = 'none';
    }
  } catch(e) {
    console.warn('loadSandboxStatus failed', e);
  }
}

// ===== Activity Heatmap =====
var _heatmapDays = 7;
async function loadHeatmap(days) {
  if (days) _heatmapDays = days;
  // Update toggle buttons
  var btn7 = document.getElementById('heatmap-btn-7d');
  var btn30 = document.getElementById('heatmap-btn-30d');
  if (btn7) btn7.className = _heatmapDays === 7 ? 'time-btn active' : 'time-btn';
  if (btn30) btn30.className = _heatmapDays === 30 ? 'time-btn active' : 'time-btn';
  try {
    var data = await fetch('/api/heatmap?days=' + _heatmapDays).then(r => r.json());
    var grid = document.getElementById('heatmap-grid');
    if (!grid) return;
    var maxVal = Math.max(1, data.max);
    var html = '<div class="heatmap-label"></div>';
    for (var h = 0; h < 24; h++) { html += '<div class="heatmap-hour-label">' + (h < 10 ? '0' : '') + h + '</div>'; }
    data.days.forEach(function(day) {
      html += '<div class="heatmap-label">' + day.label + '</div>';
      day.hours.forEach(function(val, hi) {
        var intensity = val / maxVal;
        var color;
        if (val === 0) color = '#12122a';
        else if (intensity < 0.25) color = '#1a3a2a';
        else if (intensity < 0.5) color = '#2a6a3a';
        else if (intensity < 0.75) color = '#4a9a2a';
        else color = '#6adb3a';
        html += '<div class="heatmap-cell" style="background:' + color + ';" title="' + day.label + ' ' + (hi < 10 ? '0' : '') + hi + ':00 — ' + val + ' events"></div>';
      });
    });
    grid.innerHTML = html;
    var legend = document.getElementById('heatmap-legend');
    if (legend) legend.innerHTML = 'Less <div class="heatmap-legend-cell" style="background:#12122a"></div><div class="heatmap-legend-cell" style="background:#1a3a2a"></div><div class="heatmap-legend-cell" style="background:#2a6a3a"></div><div class="heatmap-legend-cell" style="background:#4a9a2a"></div><div class="heatmap-legend-cell" style="background:#6adb3a"></div> More';
  } catch(e) {
    var grid2 = document.getElementById('heatmap-grid');
    if (grid2) grid2.innerHTML = '<span style="color:#555">No activity data</span>';
  }
}

// ===== Usage / Token Tracking =====
async function loadUsage() {
  try {
    var [data, byPlugin] = await Promise.all([
      fetch('/api/usage').then(r => r.json()),
      fetch('/api/usage/by-plugin').then(r => r.json()).catch(function(){ return {plugins: []}; })
    ]);
    function fmtTokens(n) { return n >= 1000000 ? (n/1000000).toFixed(1) + 'M' : n >= 1000 ? (n/1000).toFixed(0) + 'K' : String(n); }
    function fmtCost(c) { return c >= 0.01 ? '$' + c.toFixed(2) : c > 0 ? '<$0.01' : '$0.00'; }
    document.getElementById('usage-today').textContent = fmtTokens(data.today);
    document.getElementById('usage-today-cost').textContent = '≈ ' + fmtCost(data.todayCost);
    document.getElementById('usage-week').textContent = fmtTokens(data.week);
    document.getElementById('usage-week-cost').textContent = '≈ ' + fmtCost(data.weekCost);
    document.getElementById('usage-month').textContent = fmtTokens(data.month);
    document.getElementById('usage-month-cost').textContent = '≈ ' + fmtCost(data.monthCost);

    // Display cost warnings
    displayCostWarnings(data.warnings || []);
    
    // Display trend analysis
    displayTrendAnalysis(data.trend || {}, data);
    // Bar chart
    var maxTokens = Math.max.apply(null, data.days.map(function(d){return d.tokens;})) || 1;
    var chartHtml = '';
    data.days.forEach(function(d) {
      var pct = Math.max(1, (d.tokens / maxTokens) * 100);
      var label = d.date.substring(5);
      var val = d.tokens >= 1000 ? (d.tokens/1000).toFixed(0) + 'K' : d.tokens;
      chartHtml += '<div class="usage-bar-wrap"><div class="usage-bar" style="height:' + pct + '%"><div class="usage-bar-value">' + (d.tokens > 0 ? val : '') + '</div></div><div class="usage-bar-label">' + label + '</div></div>';
    });
    document.getElementById('usage-chart').innerHTML = chartHtml;
    // Cost table
    var usageInfoIcon = document.getElementById('usage-cost-info-icon');
    if (usageInfoIcon) {
      if (data.billingSummary === 'likely_oauth_or_included' || data.billingSummary === 'mixed') {
        usageInfoIcon.style.display = '';
        usageInfoIcon.title = 'Equivalent if billed from token usage. OAuth/included models may be billed $0 at provider level.';
      } else {
        usageInfoIcon.style.display = 'none';
        usageInfoIcon.title = '';
      }
    }

    var costLabel = data.source === 'otlp' ? 'Telemetry Cost' : 'Estimated Cost';
    var tableHtml = '<thead><tr><th>Period</th><th>Tokens</th><th>' + costLabel + '</th></tr></thead><tbody>';
    tableHtml += '<tr><td>Today</td><td>' + fmtTokens(data.today) + '</td><td>' + fmtCost(data.todayCost) + '</td></tr>';
    tableHtml += '<tr><td>This Week</td><td>' + fmtTokens(data.week) + '</td><td>' + fmtCost(data.weekCost) + '</td></tr>';
    tableHtml += '<tr><td>This Month</td><td>' + fmtTokens(data.month) + '</td><td>' + fmtCost(data.monthCost) + '</td></tr>';
    tableHtml += '</tbody>';
    document.getElementById('usage-cost-table').innerHTML = tableHtml;
    // OTLP-specific sections
    var otelExtra = document.getElementById('otel-extra-sections');
    if (data.source === 'otlp') {
      otelExtra.style.display = '';
      var runEl = document.getElementById('usage-avg-run');
      if (runEl) runEl.textContent = data.avgRunMs > 0 ? (data.avgRunMs > 1000 ? (data.avgRunMs/1000).toFixed(1) + 's' : data.avgRunMs.toFixed(0) + 'ms') : '--';
      var msgEl = document.getElementById('usage-msg-count');
      if (msgEl) msgEl.textContent = data.messageCount || '0';
      // Model breakdown table
      if (data.modelBreakdown && data.modelBreakdown.length > 0) {
        var billingMap = {};
        (data.modelBilling || []).forEach(function(b) { billingMap[b.model] = b; });
        var mHtml = '<thead><tr><th>Model</th><th>Tokens</th><th>Billing hint</th></tr></thead><tbody>';
        data.modelBreakdown.forEach(function(m) {
          var b = billingMap[m.model] || {};
          var hint = b.apiKeyConfigured ? 'API key configured' : 'OAuth/included likely';
          mHtml += '<tr><td><span class="badge model">' + escHtml(m.model) + '</span></td><td>' + fmtTokens(m.tokens) + '</td><td>' + escHtml(hint) + '</td></tr>';
        });
        mHtml += '</tbody>';
        document.getElementById('usage-model-table').innerHTML = mHtml;
      }
    } else {
      otelExtra.style.display = 'none';
    }
    renderPluginPieChart(byPlugin.plugins || []);
    // Load session cost breakdown
    fetch('/api/sessions/cost-breakdown').then(r => r.json()).then(function(cbd) {
      window._sessionCostData = cbd.top10 || [];
      renderSessionCostChart();
    }).catch(function() {
      var el = document.getElementById('usage-session-cost-table');
      if (el) el.innerHTML = '<span style="color:var(--text-muted)">No session cost data available</span>';
    });
    // Load trace clusters
    fetch('/api/sessions/clusters').then(r => r.json()).then(function(cd) {
      renderTraceClusters(cd.clusters || [], cd.total_sessions || 0);
    }).catch(function() {
      var el = document.getElementById('trace-clusters-content');
      if (el) el.innerHTML = '<span style="color:var(--text-muted)">No cluster data available</span>';
    });
    // Load cost comparison panel (GH#554)
    loadCostComparison();
    // Load activity heatmap
    loadHeatmap();
  } catch(e) {
    document.getElementById('usage-chart').innerHTML = '<span style="color:#555">No usage data available</span>';
  }
}

function renderProviderCostChart(providers) {
  var el = document.getElementById('provider-cost-chart');
  if (!el) return;
  if (!providers || providers.length === 0) {
    el.innerHTML = '<span style="color:var(--text-muted);">No provider cost data yet — start using models from multiple providers.</span>';
    return;
  }
  var providerColors = {
    'Anthropic': '#f59e0b',
    'OpenAI': '#22c55e',
    'Google/Gemini': '#0ea5e9',
    'Qwen': '#8b5cf6',
    'xAI': '#ef4444',
    'OpenRouter': '#14b8a6',
    'Other': '#94a3b8'
  };
  var totalCost = providers.reduce(function(acc, p) { return acc + (p.cost_usd || 0); }, 0) || 0.0001;
  var html = '<div style="display:flex;flex-direction:column;gap:10px;">';
  providers.forEach(function(p) {
    var color = providerColors[p.provider] || '#94a3b8';
    var pct = Math.round((p.cost_usd / totalCost) * 100);
    var costStr = p.cost_usd >= 0.01 ? '$' + p.cost_usd.toFixed(2) : p.cost_usd > 0 ? '<$0.01' : '$0.00';
    var tokStr = p.tokens >= 1000000 ? (p.tokens/1000000).toFixed(1) + 'M' : p.tokens >= 1000 ? (p.tokens/1000).toFixed(0) + 'K' : String(p.tokens || 0);
    html += '<div style="display:flex;flex-direction:column;gap:4px;">';
    html += '<div style="display:flex;align-items:center;justify-content:space-between;">';
    html += '<div style="display:flex;align-items:center;gap:8px;">';
    html += '<span style="display:inline-block;width:10px;height:10px;border-radius:50%;background:' + color + ';"></span>';
    html += '<span style="font-weight:600;color:var(--text-primary);font-size:13px;">' + escHtml(p.provider) + '</span>';
    html += '</div>';
    html += '<div style="text-align:right;font-size:12px;">';
    html += '<span style="font-weight:700;color:var(--text-primary);">' + costStr + '</span>';
    html += '<span style="color:var(--text-muted);margin-left:8px;">' + tokStr + ' tok · ' + pct + '%</span>';
    html += '</div></div>';
    html += '<div style="background:rgba(255,255,255,0.08);border-radius:4px;height:8px;overflow:hidden;">';
    html += '<div style="background:' + color + ';height:100%;width:' + Math.max(pct, 1) + '%;border-radius:4px;transition:width 0.4s ease;"></div>';
    html += '</div></div>';
  });
  html += '</div>';
  html += '<div style="margin-top:10px;font-size:11px;color:var(--text-muted);">';
  html += 'Total: $' + totalCost.toFixed(4) + ' across ' + providers.length + ' provider' + (providers.length !== 1 ? 's' : '');
  html += '</div>';
  el.innerHTML = html;
}

// ===== Cost Comparison Panel (GH#554) =====
async function loadCostComparison() {
  var card = document.getElementById('cost-comparison-card');
  var el = document.getElementById('cost-comparison-content');
  if (!card || !el) return;
  try {
    var data = await fetch('/api/usage/cost-comparison').then(function(r){return r.json();});
    if (!data || !data.alternatives || data.alternatives.length === 0) return;
    card.style.display = 'block';
    renderCostComparison(data);
  } catch(e) {
    // silently skip if unavailable
  }
}

function renderCostComparison(data) {
  var el = document.getElementById('cost-comparison-content');
  if (!el) return;
  var actual = data.actual || {};
  var alts = data.alternatives || [];
  var actualCost = actual.cost_usd || 0;
  var actualModel = actual.model || 'current model';
  var actualTokens = actual.tokens || 0;
  if (actualTokens === 0) {
    el.innerHTML = '<span style="color:var(--text-muted)">No token data for the last 30 days — usage will appear here once available.</span>';
    return;
  }
  var providerColors = {
    'Google': '#0ea5e9', 'OpenAI': '#22c55e', 'Anthropic': '#f59e0b',
    'Alibaba': '#8b5cf6', 'Meta': '#ef4444', 'Other': '#94a3b8'
  };
  var tokStr = actualTokens >= 1000000 ? (actualTokens/1000000).toFixed(1)+'M' : actualTokens >= 1000 ? Math.round(actualTokens/1000)+'K' : String(Math.round(actualTokens));
  var html = '<div style="margin-bottom:14px;padding:10px 14px;background:rgba(255,255,255,0.05);border-radius:8px;border:1px solid rgba(255,255,255,0.08)">';
  html += '<div style="font-size:12px;color:var(--text-muted);margin-bottom:4px;">Your actual spend (30 days)</div>';
  html += '<div style="display:flex;align-items:baseline;gap:10px;">';
  html += '<span style="font-size:22px;font-weight:700;color:var(--text-primary);">$' + (actualCost >= 0.01 ? actualCost.toFixed(2) : actualCost > 0 ? '<0.01' : '0.00') + '</span>';
  html += '<span style="font-size:12px;color:var(--text-muted);">' + escHtml(actualModel) + ' &middot; ' + tokStr + ' tokens</span>';
  html += '</div></div>';
  html += '<div style="display:flex;flex-direction:column;gap:8px;">';
  alts.forEach(function(alt) {
    var color = providerColors[alt.provider] || '#94a3b8';
    var altCost = alt.estimated_cost || 0;
    var savingsPct = alt.savings_pct || 0;
    var savingsUsd = alt.savings_usd || 0;
    var costStr = altCost >= 0.01 ? '$' + altCost.toFixed(2) : altCost > 0 ? '<$0.01' : '$0.00';
    var isCurrent = actualCost > 0 && Math.abs(altCost - actualCost) / (actualCost || 1) < 0.15;
    var isCheaper = savingsPct > 5;
    var isMoreExpensive = savingsPct < -5;
    var rowStyle = isCurrent ? 'background:rgba(255,255,255,0.08);border:1px solid rgba(255,255,255,0.15);' : 'background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.06);';
    html += '<div style="' + rowStyle + 'border-radius:8px;padding:10px 14px;display:flex;align-items:center;gap:12px;">';
    html += '<span style="display:inline-block;width:8px;height:8px;border-radius:50%;background:' + color + ';flex-shrink:0;"></span>';
    html += '<div style="flex:1;min-width:0;">';
    html += '<div style="font-size:13px;font-weight:600;color:var(--text-primary);">' + escHtml(alt.display_name) + '</div>';
    html += '<div style="font-size:11px;color:var(--text-muted);">' + escHtml(alt.provider) + '</div>';
    html += '</div>';
    html += '<div style="text-align:right;flex-shrink:0;">';
    html += '<div style="font-size:14px;font-weight:700;color:var(--text-primary);">' + costStr + '</div>';
    if (isCurrent) {
      html += '<div style="font-size:11px;color:#94a3b8;">≈ current</div>';
    } else if (isCheaper) {
      html += '<div style="font-size:11px;color:#22c55e;">save $' + Math.abs(savingsUsd).toFixed(2) + ' (' + Math.abs(savingsPct) + '%)</div>';
    } else if (isMoreExpensive) {
      html += '<div style="font-size:11px;color:#ef4444;">+$' + Math.abs(savingsUsd).toFixed(2) + ' (' + Math.abs(savingsPct) + '% more)</div>';
    } else {
      html += '<div style="font-size:11px;color:#94a3b8;">similar cost</div>';
    }
    html += '</div></div>';
  });
  html += '</div>';
  html += '<div style="margin-top:10px;font-size:11px;color:var(--text-muted);line-height:1.5;">Estimates based on 60/40 input/output split for ' + tokStr + ' tokens. Actual costs vary by prompt structure and API tier.</div>';
  el.innerHTML = html;
}

function renderTraceClusters(clusters, totalSessions) {
  var el = document.getElementById('trace-clusters-content');
  if (!el) return;
  if (!clusters || clusters.length === 0) {
    el.innerHTML = '<span style="color:var(--text-muted)">No sessions to cluster yet</span>';
    return;
  }
  var categoryIcons = {
    'code-execution': '⚙️', 'file-ops': '📁', 'web': '🌐',
    'communication': '💬', 'orchestration': '🤖', 'memory': '🧠',
    'no-tools': '💭', 'other-tools': '🔧'
  };
  var costColors = { 'expensive': '#ef4444', 'medium': '#f59e0b', 'cheap': '#22c55e' };
  var html = '<div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:12px;">';
  clusters.forEach(function(c) {
    var icon = categoryIcons[c.tool_category] || '🔧';
    var costColor = costColors[c.cost_tier] || '#888';
    var errBadge = c.has_errors ? '<span style="background:#ef44441a;color:#ef4444;border:1px solid #ef444440;border-radius:4px;padding:1px 6px;font-size:10px;margin-left:6px;">errors</span>' : '';
    var topTools = (c.top_tools || []).slice(0,3).map(function(t){ return '<code style="background:rgba(255,255,255,0.07);padding:1px 5px;border-radius:3px;font-size:10px;">' + escHtml(t.tool) + ' ×' + t.count + '</code>'; }).join(' ');
    html += '<div style="background:var(--bg-card,rgba(255,255,255,0.04));border:1px solid rgba(255,255,255,0.08);border-radius:10px;padding:14px;">';
    html += '<div style="display:flex;align-items:center;gap:8px;margin-bottom:8px;">';
    html += '<span style="font-size:20px;">' + icon + '</span>';
    html += '<div style="flex:1;min-width:0;"><div style="font-size:13px;font-weight:600;color:var(--text-primary,#fff);white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">' + escHtml(c.label) + errBadge + '</div>';
    html += '<div style="font-size:11px;color:var(--text-muted,#888);margin-top:1px;">' + c.session_count + ' session' + (c.session_count !== 1 ? 's' : '') + ' · ' + c.model_family + '</div></div>';
    html += '<div style="text-align:right;"><div style="font-size:14px;font-weight:700;color:' + costColor + ';">$' + c.total_cost_usd.toFixed(3) + '</div><div style="font-size:10px;color:var(--text-muted,#888);">avg $' + c.avg_cost_usd.toFixed(4) + '</div></div>';
    html += '</div>';
    if (topTools) html += '<div style="margin-top:6px;display:flex;flex-wrap:wrap;gap:4px;">' + topTools + '</div>';
    html += '</div>';
  });
  html += '</div>';
  html += '<div style="margin-top:10px;font-size:11px;color:var(--text-muted,#888);">' + totalSessions + ' sessions clustered into ' + clusters.length + ' groups by tool pattern, cost, and model</div>';
  el.innerHTML = html;
}

function renderSessionCostChart() {
  var rows = window._sessionCostData || [];
  var canvas = document.getElementById('usage-session-cost-bar');
  var tableEl = document.getElementById('usage-session-cost-table');
  var threshold = parseFloat((document.getElementById('session-cost-threshold') || {}).value || '0.5') || 0;
  if (!canvas) return;
  var ctx = canvas.getContext('2d');
  var dpr = window.devicePixelRatio || 1;
  var W = canvas.parentElement ? canvas.parentElement.clientWidth || 600 : 600;
  var H = 180;
  canvas.width = W * dpr; canvas.height = H * dpr;
  canvas.style.width = W + 'px'; canvas.style.height = H + 'px';
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  ctx.clearRect(0, 0, W, H);
  if (!rows || rows.length === 0) {
    ctx.fillStyle = 'rgba(255,255,255,0.3)';
    ctx.font = '13px monospace';
    ctx.textAlign = 'center';
    ctx.fillText('No session cost data', W/2, H/2);
    if (tableEl) tableEl.innerHTML = '<span style="color:var(--text-muted)">No sessions found</span>';
    return;
  }
  var maxCost = Math.max.apply(null, rows.map(function(r) { return r.cost_usd || 0; })) || 0.001;
  var pad = { top: 20, bottom: 40, left: 10, right: 10 };
  var barW = Math.floor((W - pad.left - pad.right) / rows.length) - 4;
  rows.forEach(function(r, i) {
    var x = pad.left + i * ((W - pad.left - pad.right) / rows.length);
    var barH = Math.max(2, ((r.cost_usd || 0) / maxCost) * (H - pad.top - pad.bottom));
    var y = H - pad.bottom - barH;
    var overThreshold = threshold > 0 && (r.cost_usd || 0) >= threshold;
    ctx.fillStyle = overThreshold ? '#ef4444' : '#a855f7';
    ctx.fillRect(x + 2, y, barW, barH);
    // Cost label above bar
    ctx.fillStyle = overThreshold ? '#fca5a5' : 'rgba(255,255,255,0.6)';
    ctx.font = '9px monospace';
    ctx.textAlign = 'center';
    if ((r.cost_usd || 0) >= 0.0001) {
      ctx.fillText('$' + (r.cost_usd || 0).toFixed(4), x + 2 + barW/2, y - 3);
    }
    // Session label below
    ctx.fillStyle = 'rgba(255,255,255,0.4)';
    ctx.font = '9px monospace';
    var label = (r.session_id || '').slice(-8);
    ctx.fillText(label, x + 2 + barW/2, H - pad.bottom + 12);
  });
  // Threshold line
  if (threshold > 0 && threshold <= maxCost) {
    var ty = H - pad.bottom - (threshold / maxCost) * (H - pad.top - pad.bottom);
    ctx.strokeStyle = '#f59e0b';
    ctx.setLineDash([4, 3]);
    ctx.lineWidth = 1;
    ctx.beginPath(); ctx.moveTo(pad.left, ty); ctx.lineTo(W - pad.right, ty); ctx.stroke();
    ctx.setLineDash([]);
    ctx.fillStyle = '#f59e0b';
    ctx.font = '9px monospace';
    ctx.textAlign = 'left';
    ctx.fillText('$' + threshold.toFixed(2) + ' threshold', pad.left + 4, ty - 3);
  }
  // Table
  if (tableEl) {
    var aboveThreshold = threshold > 0 ? rows.filter(function(r) { return (r.cost_usd||0) >= threshold; }) : [];
    var tableHtml = '<table style="width:100%;border-collapse:collapse;">';
    tableHtml += '<thead><tr style="color:var(--text-muted);font-size:11px;">';
    tableHtml += '<th style="text-align:left;padding:4px 8px;">Session</th>';
    tableHtml += '<th style="text-align:right;padding:4px 8px;">Tokens</th>';
    tableHtml += '<th style="text-align:right;padding:4px 8px;">Cost</th>';
    tableHtml += '<th style="text-align:left;padding:4px 8px;">Model</th>';
    tableHtml += '<th style="text-align:left;padding:4px 8px;">Date</th>';
    tableHtml += '</tr></thead><tbody>';
    rows.forEach(function(r) {
      var over = threshold > 0 && (r.cost_usd||0) >= threshold;
      var rowStyle = over ? 'background:rgba(239,68,68,0.1);' : '';
      tableHtml += '<tr style="border-top:1px solid var(--border-secondary);' + rowStyle + '">';
      tableHtml += '<td style="padding:4px 8px;font-family:monospace;font-size:11px;color:var(--text-muted);">' + (r.session_id||'').slice(-16) + (over ? ' <span style="color:#ef4444;">⚠</span>' : '') + '</td>';
      tableHtml += '<td style="text-align:right;padding:4px 8px;font-size:12px;">' + ((r.tokens||0) >= 1000 ? ((r.tokens||0)/1000).toFixed(0)+'K' : (r.tokens||0)) + '</td>';
      tableHtml += '<td style="text-align:right;padding:4px 8px;font-size:12px;color:' + (over ? '#ef4444' : 'var(--text-success)') + ';font-weight:600;">$' + (r.cost_usd||0).toFixed(4) + '</td>';
      tableHtml += '<td style="padding:4px 8px;font-size:11px;color:var(--text-muted);">' + escHtml(r.model||'') + '</td>';
      tableHtml += '<td style="padding:4px 8px;font-size:11px;color:var(--text-muted);">' + escHtml(r.day||'') + '</td>';
      tableHtml += '</tr>';
    });
    tableHtml += '</tbody></table>';
    if (aboveThreshold.length > 0) {
      tableHtml = '<div style="margin-bottom:8px;padding:6px 10px;background:rgba(239,68,68,0.1);border:1px solid rgba(239,68,68,0.3);border-radius:6px;font-size:12px;color:#fca5a5;">⚠ ' + aboveThreshold.length + ' session' + (aboveThreshold.length > 1 ? 's' : '') + ' exceeded the $' + threshold.toFixed(2) + ' threshold</div>' + tableHtml;
    }
    tableEl.innerHTML = tableHtml;
  }
}

function renderPluginPieChart(rows) {
  var canvas = document.getElementById('usage-plugin-pie');
  var legend = document.getElementById('usage-plugin-legend');
  if (!canvas || !legend) return;

  var data = (rows || []).filter(function(r){ return (r.total_tokens || 0) > 0; }).slice(0, 8);
  if (!data.length) {
    var ctxEmpty = canvas.getContext('2d');
    ctxEmpty.clearRect(0, 0, canvas.width, canvas.height);
    legend.innerHTML = '<div style="color:var(--text-muted);">No plugin tool-call attribution detected yet.</div>';
    return;
  }

  var palette = ['#0ea5e9','#22c55e','#f59e0b','#ef4444','#8b5cf6','#14b8a6','#f97316','#84cc16'];
  var total = data.reduce(function(acc, r){ return acc + (r.total_tokens || 0); }, 0) || 1;
  var cx = canvas.width / 2;
  var cy = canvas.height / 2;
  var radius = 110;
  var start = -Math.PI / 2;
  var ctx = canvas.getContext('2d');
  ctx.clearRect(0, 0, canvas.width, canvas.height);

  data.forEach(function(r, i) {
    var slice = ((r.total_tokens || 0) / total) * Math.PI * 2;
    ctx.beginPath();
    ctx.moveTo(cx, cy);
    ctx.arc(cx, cy, radius, start, start + slice);
    ctx.closePath();
    ctx.fillStyle = palette[i % palette.length];
    ctx.fill();
    start += slice;
  });

  // Center cutout to create donut.
  ctx.beginPath();
  ctx.arc(cx, cy, 52, 0, Math.PI * 2);
  ctx.fillStyle = getComputedStyle(document.body).getPropertyValue('--bg-secondary') || '#111';
  ctx.fill();
  ctx.fillStyle = getComputedStyle(document.body).getPropertyValue('--text-primary') || '#fff';
  ctx.font = '700 13px Manrope, sans-serif';
  ctx.textAlign = 'center';
  ctx.fillText('Plugins', cx, cy - 2);
  ctx.font = '600 12px Manrope, sans-serif';
  ctx.fillStyle = getComputedStyle(document.body).getPropertyValue('--text-muted') || '#aaa';
  ctx.fillText((total >= 1000 ? (total/1000).toFixed(1) + 'K' : total) + ' tok', cx, cy + 16);

  var lhtml = '';
  data.forEach(function(r, i) {
    lhtml += '<div style="display:flex;align-items:center;justify-content:space-between;gap:10px;padding:6px 0;border-bottom:1px solid var(--border-secondary);">';
    lhtml += '<div style="display:flex;align-items:center;gap:8px;min-width:0;">';
    lhtml += '<span style="display:inline-block;width:10px;height:10px;border-radius:50%;background:' + palette[i % palette.length] + ';"></span>';
    lhtml += '<span style="font-weight:600;color:var(--text-primary);">' + escHtml(r.plugin) + '</span>';
    lhtml += '</div>';
    lhtml += '<div style="text-align:right;">';
    lhtml += '<div style="font-size:12px;">' + (r.pct_of_total || 0).toFixed(1) + '%</div>';
    lhtml += '<div style="font-size:11px;color:var(--text-muted);">' + (r.total_tokens || 0).toLocaleString() + ' tok • $' + Number(r.cost_usd || 0).toFixed(4) + '</div>';
    lhtml += '</div></div>';
  });
  legend.innerHTML = lhtml;
}

function displayCostWarnings(warnings) {
  var container = document.getElementById('cost-warnings');
  if (!warnings || warnings.length === 0) {
    container.style.display = 'none';
    return;
  }
  
  var html = '';
  warnings.forEach(function(w) {
    var icon = w.level === 'error' ? '🚨' : '⚠️';
    html += '<div class="cost-warning ' + w.level + '">';
    html += '<div class="cost-warning-icon">' + icon + '</div>';
    html += '<div class="cost-warning-message">' + escHtml(w.message) + '</div>';
    html += '</div>';
  });
  
  container.innerHTML = html;
  container.style.display = 'block';
}

function displayTrendAnalysis(trend, usageData) {
  var card = document.getElementById('trend-card');
  if (!trend || trend.trend === 'insufficient_data') {
    card.style.display = 'none';
    return;
  }
  
  var directionEl = document.getElementById('trend-direction');
  var predictionEl = document.getElementById('trend-prediction');
  
  var emoji = trend.trend === 'increasing' ? '📈' : trend.trend === 'decreasing' ? '📉' : '➡️';
  directionEl.textContent = emoji + ' ' + trend.trend.charAt(0).toUpperCase() + trend.trend.slice(1);
  
  if (trend.dailyAvg && trend.monthlyPrediction) {
    var dailyAvg = trend.dailyAvg >= 1000 ? (trend.dailyAvg/1000).toFixed(0) + 'K' : trend.dailyAvg;
    var monthlyPred = trend.monthlyPrediction >= 1000000 ? (trend.monthlyPrediction/1000000).toFixed(1) + 'M' : 
                      trend.monthlyPrediction >= 1000 ? (trend.monthlyPrediction/1000).toFixed(0) + 'K' : trend.monthlyPrediction;

    var line = dailyAvg + '/day avg, ~' + monthlyPred + '/month projected';

    // Add projected monthly equivalent cost only when math is meaningful
    if (usageData && usageData.month && usageData.month > 0 && usageData.monthCost && usageData.monthCost > 0) {
      var costPerToken = usageData.monthCost / usageData.month;
      var projectedEquivalent = trend.monthlyPrediction * costPerToken;
      if (projectedEquivalent > 0.01) {
        line += ' - ~$' + projectedEquivalent.toFixed(2) + '/mo equivalent if billed';
        if (usageData.billingSummary === 'likely_oauth_or_included') {
          line += ' (could be $0 with OAuth)';
        }
      }
    }

    predictionEl.textContent = line;
  } else {
    predictionEl.textContent = 'Analyzing usage patterns...';
  }
  
  card.style.display = 'block';
}

function exportUsageData() {
  // Trigger CSV download
  window.open('/api/usage/export', '_blank');
}

// ===== Model Attribution =====
async function loadModelAttribution() {
  try {
    var data = await fetch('/api/model-attribution').then(function(r) { return r.json(); });
    var models = data.models || [];
    var switches = data.switches || [];
    var totalTurns = data.total_turns || 0;
    var primaryModel = data.primary_model || '--';

    // Stat cards — update all instances (duplicate IDs across dashboard variants)
    var cleanModel = primaryModel.replace('anthropic/', '').replace('openai/', '');
    document.querySelectorAll('#model-primary').forEach(function(el) { el.textContent = cleanModel; });
    var primaryPct = totalTurns > 0 && models.length > 0 ? ((models[0].turns / totalTurns) * 100).toFixed(1) : '0';
    document.querySelectorAll('#model-primary-pct').forEach(function(el) { el.textContent = primaryPct + '% of turns'; });
    document.querySelectorAll('#model-count').forEach(function(el) { el.textContent = models.length; });
    document.querySelectorAll('#model-total-turns').forEach(function(el) { el.textContent = totalTurns.toLocaleString(); });
    var fallbackCount = models.filter(function(m) { return m.model !== primaryModel; }).reduce(function(s, m) { return s + m.turns; }, 0);
    var fallbackRate = totalTurns > 0 ? ((fallbackCount / totalTurns) * 100).toFixed(1) : '0';
    document.querySelectorAll('#model-fallback-rate').forEach(function(el) { el.textContent = fallbackRate + '%'; });
    document.querySelectorAll('#model-fallback-detail').forEach(function(el) { el.textContent = fallbackCount + ' turns on non-primary models'; });

    // Model mix bar chart
    var chartHtml = '';
    var colors = ['#4caf50', '#2196f3', '#ff9800', '#e91e63', '#9c27b0', '#00bcd4', '#ff5722', '#607d8b'];
    models.forEach(function(m, i) {
      var pct = totalTurns > 0 ? (m.turns / totalTurns * 100).toFixed(1) : '0';
      var barW = totalTurns > 0 ? Math.max(2, Math.round(m.turns / totalTurns * 100)) : 0;
      var color = colors[i % colors.length];
      chartHtml += '<div style="display:flex;align-items:center;gap:10px;margin:6px 0;">';
      chartHtml += '<div style="min-width:160px;font-size:12px;color:var(--text-secondary);overflow:hidden;text-overflow:ellipsis;white-space:nowrap;" title="' + escHtml(m.model) + '">' + escHtml(m.model.replace('anthropic/', '').replace('openai/', '')) + '</div>';
      chartHtml += '<div style="flex:1;background:var(--bg-secondary);border-radius:4px;height:16px;overflow:hidden;">';
      chartHtml += '<div style="height:100%;width:' + barW + '%;background:' + color + ';border-radius:4px;transition:width 0.4s;"></div></div>';
      chartHtml += '<div style="min-width:60px;text-align:right;font-size:12px;color:var(--text-muted);">' + pct + '%</div>';
      chartHtml += '<div style="min-width:55px;text-align:right;font-size:12px;color:var(--text-secondary);">' + m.turns.toLocaleString() + ' turns</div>';
      chartHtml += '</div>';
    });
    document.getElementById('model-mix-chart').innerHTML = chartHtml || '<div style="color:#666;">No model data found in sessions.</div>';

    // Per-model session table
    var tbodyHtml = '';
    models.forEach(function(m) {
      var pct = totalTurns > 0 ? (m.turns / totalTurns * 100).toFixed(1) : '0';
      tbodyHtml += '<tr>';
      tbodyHtml += '<td style="padding:6px 8px;font-size:13px;" title="' + escHtml(m.model) + '">' + escHtml(m.model.replace('anthropic/', '').replace('openai/', '')) + '</td>';
      tbodyHtml += '<td style="padding:6px 8px;font-size:13px;text-align:right;">' + (m.sessions || 0).toLocaleString() + '</td>';
      tbodyHtml += '<td style="padding:6px 8px;font-size:13px;text-align:right;">' + m.turns.toLocaleString() + '</td>';
      tbodyHtml += '<td style="padding:6px 8px;font-size:13px;text-align:right;">' + pct + '%</td>';
      tbodyHtml += '</tr>';
    });
    var tbl = document.getElementById('model-sessions-table');
    if (tbl) tbl.querySelector('tbody').innerHTML = tbodyHtml || '<tr><td colspan="4" style="color:#666;padding:8px;">No data</td></tr>';

    // Switches section
    if (switches.length > 0) {
      document.getElementById('model-switches-section').style.display = '';
      document.getElementById('model-switches-count').textContent = '(' + switches.length + ' switches)';
      var swHtml = '';
      switches.slice(0, 20).forEach(function(sw) {
        swHtml += '<tr>';
        swHtml += '<td style="padding:6px 8px;font-size:12px;color:var(--text-muted);">' + escHtml(sw.session.substring(0, 8)) + '...</td>';
        swHtml += '<td style="padding:6px 8px;font-size:12px;">' + escHtml(sw.from_model.replace('anthropic/', '').replace('openai/', '')) + '</td>';
        swHtml += '<td style="padding:6px 8px;font-size:12px;color:var(--text-success);">→ ' + escHtml(sw.to_model.replace('anthropic/', '').replace('openai/', '')) + '</td>';
        swHtml += '</tr>';
      });
      var swTbl = document.getElementById('model-switches-table');
      if (swTbl) swTbl.querySelector('tbody').innerHTML = swHtml;
    }
  } catch(e) {
    console.error('loadModelAttribution', e);
  }
}

// ===== Skill Attribution =====
async function loadSkillAttribution() {
  var el = document.getElementById('skill-leaderboard-content');
  if (!el) return;
  try {
    var data = await fetch('/api/skill-attribution').then(function(r) { return r.json(); });
    var top5 = data.top5_week || [];
    var allSkills = data.skills || [];
    var totalCost = data.total_cost || 0;
    function fmtCost(c) { return c >= 0.01 ? '$' + c.toFixed(2) : c > 0 ? '<$0.01' : '$0.00'; }
    if (top5.length === 0) {
      el.innerHTML = '<span style="color:var(--text-muted);font-size:13px;">No skill invocations detected yet. Skills are detected when SKILL.md files are read during sessions.</span>';
      return;
    }
    var html = '<table class="usage-table" style="width:100%;">';
    html += '<thead><tr><th>Skill</th><th style="text-align:right;">Invocations</th><th style="text-align:right;">Avg Cost</th><th style="text-align:right;">Total Cost</th><th></th></tr></thead><tbody>';
    top5.forEach(function(s) {
      html += '<tr>';
      html += '<td style="padding:6px 8px;font-size:13px;font-weight:600;">' + escHtml(s.name) + '</td>';
      html += '<td style="padding:6px 8px;font-size:13px;text-align:right;color:var(--text-muted);">' + s.invocations + '</td>';
      html += '<td style="padding:6px 8px;font-size:13px;text-align:right;">' + fmtCost(s.avg_cost) + '</td>';
      html += '<td style="padding:6px 8px;font-size:13px;text-align:right;font-weight:600;color:var(--text-accent);">' + fmtCost(s.total_cost) + '</td>';
      html += '<td style="padding:6px 8px;font-size:12px;text-align:right;"><a href="' + escHtml(s.clawhub_url) + '" target="_blank" style="color:#4caf50;text-decoration:none;">ClawHub ↗</a></td>';
      html += '</tr>';
    });
    html += '</tbody></table>';
    if (allSkills.length > 5) {
      html += '<div style="margin-top:8px;font-size:12px;color:var(--text-muted);">Showing top 5 of ' + allSkills.length + ' skills this week. <a href="#" onclick="loadAllSkills();return false;" style="color:#4caf50;">View all</a></div>';
    }
    html += '<div style="margin-top:8px;font-size:11px;color:var(--text-muted);">All-time total: ' + fmtCost(totalCost) + ' · ' + escHtml(data.note || '') + '</div>';
    el.innerHTML = html;
  } catch(e) {
    if (el) el.innerHTML = '<span style="color:var(--text-muted)">Skill attribution unavailable</span>';
    console.error('loadSkillAttribution', e);
  }
}

function loadAllSkills() {
  var el = document.getElementById('skill-leaderboard-content');
  if (!el) return;
  fetch('/api/skill-attribution').then(function(r) { return r.json(); }).then(function(data) {
    var allSkills = data.skills || [];
    function fmtCost(c) { return c >= 0.01 ? '$' + c.toFixed(2) : c > 0 ? '<$0.01' : '$0.00'; }
    var html = '<table class="usage-table" style="width:100%;">';
    html += '<thead><tr><th>Skill</th><th style="text-align:right;">Invocations</th><th style="text-align:right;">Avg Cost</th><th style="text-align:right;">Total Cost</th><th></th></tr></thead><tbody>';
    allSkills.forEach(function(s) {
      html += '<tr><td style="padding:6px 8px;font-size:13px;font-weight:600;">' + escHtml(s.name) + '</td>';
      html += '<td style="padding:6px 8px;font-size:13px;text-align:right;color:var(--text-muted);">' + s.invocations + '</td>';
      html += '<td style="padding:6px 8px;font-size:13px;text-align:right;">' + fmtCost(s.avg_cost) + '</td>';
      html += '<td style="padding:6px 8px;font-size:13px;text-align:right;font-weight:600;color:var(--text-accent);">' + fmtCost(s.total_cost) + '</td>';
      html += '<td style="padding:6px 8px;font-size:12px;text-align:right;"><a href="' + escHtml(s.clawhub_url) + '" target="_blank" style="color:#4caf50;text-decoration:none;">ClawHub ↗</a></td>';
      html += '</tr>';
    });
    html += '</tbody></table>';
    html += '<div style="margin-top:8px;font-size:11px;color:var(--text-muted);">All-time total: ' + fmtCost(data.total_cost || 0) + ' · ' + escHtml(data.note || '') + '</div>';
    el.innerHTML = html;
  }).catch(function() {});
}

// ===== Transcripts =====
async function loadTranscripts() {
  try {
    var data = await fetch('/api/transcripts').then(r => r.json());
    var html = '';
    data.transcripts.forEach(function(t) {
      html += '<div class="transcript-item" onclick="viewTranscript(\'' + escHtml(t.id) + '\')">';
      html += '<div><div class="transcript-name">' + escHtml(t.name) + '</div>';
      html += '<div class="transcript-meta-row">';
      html += '<span>' + t.messages + ' messages</span>';
      html += '<span>' + (t.size > 1024 ? (t.size/1024).toFixed(1) + ' KB' : t.size + ' B') + '</span>';
      html += '<span>' + timeAgo(t.modified) + '</span>';
      html += '</div></div>';
      html += '<span style="color:#444;font-size:18px;">▸</span>';
      html += '</div>';
    });
    document.getElementById('transcript-list').innerHTML = html || '<div style="padding:16px;color:#666;">No transcript files found</div>';
    document.getElementById('transcript-list').style.display = '';
    document.getElementById('transcript-viewer').style.display = 'none';
    document.getElementById('transcript-back-btn').style.display = 'none';
  } catch(e) {
    document.getElementById('transcript-list').innerHTML = '<div style="padding:16px;color:#666;">Failed to load transcripts</div>';
  }
}

function showTranscriptList() {
  document.getElementById('transcript-list').style.display = '';
  document.getElementById('transcript-viewer').style.display = 'none';
  document.getElementById('transcript-back-btn').style.display = 'none';
}

// ── Session Replay State ────────────────────────────────────────────────────
window._replayEvents = [];
window._replayIndex = 0;
window._replayFilter = 'all';

function _buildReplayEvent(m, idx) {
  var role = m.role || 'unknown';
  // Determine event type for filtering
  var type = role;
  if (role === 'assistant' && m.content && m.content.indexOf('[tool_use]') !== -1) type = 'tool_use';
  if (role === 'assistant' && m.content && m.content.indexOf('<antml_thinking>') !== -1) type = 'thinking';
  if (role === 'compaction') type = 'compaction';
  // Capture compaction-specific fields
  var extra = {};
  if (role === 'compaction') {
    extra.tokens_before = m.tokens_before;
    extra.first_kept_entry_id = m.first_kept_entry_id;
    extra.from_hook = m.from_hook;
    extra.summary_truncated = m.summary_truncated;
  }
  return { role: role, type: type, content: m.content || '', timestamp: m.timestamp, tokens: m.tokens || null, originalIndex: idx, extra: extra };
}

function _renderReplayEvent(ev, highlighted) {
  var role = ev.role;
  // Handle compaction events specially
  if (role === 'compaction') {
    return _renderCompactionEvent(ev, highlighted);
  }
  var cls = role === 'user' ? 'user' : role === 'assistant' ? 'assistant' : role === 'system' ? 'system' : 'tool';
  var content = ev.content;
  var needsTruncate = content.length > 800;
  var displayContent = needsTruncate ? content.substring(0, 800) : content;
  var highlightStyle = highlighted ? 'box-shadow:0 0 0 2px #6366f1;' : '';
  var html = '<div class="chat-msg ' + cls + '" id="replay-msg-' + ev.originalIndex + '" style="' + highlightStyle + '">';
  html += '<div class="chat-role">' + escHtml(role) + '</div>';
  if (needsTruncate) {
    html += '<div class="chat-content-truncated" id="msg-' + ev.originalIndex + '-short" style="white-space:pre-wrap;word-break:break-word;">' + escHtml(displayContent) + '</div>';
    html += '<div id="msg-' + ev.originalIndex + '-full" style="display:none;white-space:pre-wrap;word-break:break-word;">' + escHtml(content) + '</div>';
    html += '<div class="chat-expand" onclick="toggleMsg(' + ev.originalIndex + ')" style="color:#6366f1;cursor:pointer;font-size:11px;margin-top:4px;">Show more (' + content.length + ' chars)</div>';
  } else {
    html += '<div style="white-space:pre-wrap;word-break:break-word;">' + escHtml(content) + '</div>';
  }
  if (ev.tokens) html += '<div style="font-size:11px;color:var(--text-muted);margin-top:4px;">&#128200; ' + ev.tokens + ' tokens</div>';
  if (ev.timestamp) html += '<div class="chat-ts">' + new Date(ev.timestamp).toLocaleString() + '</div>';
  html += '</div>';
  return html;
}

// ── Compaction Event Renderer ─────────────────────────────────────────────
function _renderCompactionEvent(ev, highlighted) {
  var content = ev.content || '';
  var extra = ev.extra || {};
  var tokensBefore = extra.tokens_before || 0;
  var isTruncated = extra.summary_truncated;
  var highlightStyle = highlighted ? 'box-shadow:0 0 0 2px #eab308;' : '';
  var html = '<div class="chat-msg" id="replay-msg-' + ev.originalIndex + '" style="' + highlightStyle + 'background:linear-gradient(135deg, rgba(234,179,8,0.1) 0%, rgba(234,179,8,0.05) 100%);border-left:3px solid #eab308;">';
  html += '<div class="chat-role" style="color:#eab308;">&#128204; Compaction Summary</div>';
  html += '<div style="font-size:12px;color:var(--text-muted);margin-bottom:6px;">';
  html += '&#128200; ' + (tokensBefore/1000).toFixed(1) + 'K tokens compacted';
  if (extra.from_hook) html += ' (auto)';
  html += ' | Entry ' + (extra.first_kept_entry_id || '...');
  html += '</div>';
  // Summary content with expandable toggle
  if (content) {
    var needsExpand = content.length > 300 || isTruncated;
    var displayContent = needsExpand ? content.substring(0, 300) : content;
    html += '<div id="compaction-' + ev.originalIndex + '-short" style="white-space:pre-wrap;word-break:break-word;font-size:13px;">' + escHtml(displayContent);
    if (needsExpand) html += '...';
    html += '</div>';
    if (needsExpand) {
      html += '<div id="compaction-' + ev.originalIndex + '-full" style="display:none;white-space:pre-wrap;word-break:break-word;font-size:13px;">' + escHtml(content) + '</div>';
      html += '<div style="color:#eab308;cursor:pointer;font-size:11px;margin-top:6px;" onclick="toggleCompaction(' + ev.originalIndex + ')">↓ Expand summary</div>';
    }
  }
  if (ev.timestamp) html += '<div class="chat-ts">' + new Date(ev.timestamp).toLocaleString() + '</div>';
  html += '</div>';
  return html;
}

function toggleCompaction(idx) {
  var short = document.getElementById('compaction-' + idx + '-short');
  var full = document.getElementById('compaction-' + idx + '-full');
  var toggle = short.nextElementSibling.nextElementSibling;
  if (short.style.display === 'none') {
    short.style.display = '';
    full.style.display = 'none';
    if (toggle) toggle.textContent = '\u2193 Expand summary';
  } else {
    short.style.display = 'none';
    full.style.display = '';
    if (toggle) toggle.textContent = '\u2191 Collapse summary';
  }
}

function _replayFilteredEvents() {
  var f = window._replayFilter;
  if (!f || f === 'all') return window._replayEvents;
  return window._replayEvents.filter(function(ev) { return ev.type === f || ev.role === f; });
}

function _replayRenderCurrent() {
  var filtered = _replayFilteredEvents();
  if (!filtered.length) {
    document.getElementById('transcript-messages').innerHTML = '<div style="color:var(--text-muted);padding:16px;">No events match this filter.</div>';
    document.getElementById('replay-pos').textContent = '0/0';
    return;
  }
  var idx = window._replayIndex;
  if (idx < 0) idx = 0;
  if (idx >= filtered.length) idx = filtered.length - 1;
  window._replayIndex = idx;

  // Render all filtered events up to current index (show history)
  var html = '';
  for (var i = 0; i <= idx; i++) {
    html += _renderReplayEvent(filtered[i], i === idx);
  }
  document.getElementById('transcript-messages').innerHTML = html;
  document.getElementById('replay-pos').textContent = (idx + 1) + '/' + filtered.length;
  var scrubber = document.getElementById('replay-scrubber');
  scrubber.max = filtered.length - 1;
  scrubber.value = idx;

  // Scroll highlighted message into view
  var el = document.getElementById('replay-msg-' + filtered[idx].originalIndex);
  if (el) el.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

function replayNext() {
  var filtered = _replayFilteredEvents();
  if (window._replayIndex < filtered.length - 1) {
    window._replayIndex++;
    _replayRenderCurrent();
  }
}

function replayPrev() {
  if (window._replayIndex > 0) {
    window._replayIndex--;
    _replayRenderCurrent();
  }
}

function replayJumpTo(index) {
  window._replayIndex = index;
  _replayRenderCurrent();
}

function replayFilter(type) {
  window._replayFilter = type;
  window._replayIndex = 0;
  // Update pill styles
  document.querySelectorAll('.replay-filter').forEach(function(btn) {
    var isActive = btn.getAttribute('data-type') === type;
    btn.style.background = isActive ? '#6366f1' : 'var(--button-bg)';
    btn.style.color = isActive ? '#fff' : 'var(--text-secondary)';
    btn.style.borderColor = isActive ? '#6366f1' : 'var(--border-secondary)';
  });
  var filtered = _replayFilteredEvents();
  var scrubber = document.getElementById('replay-scrubber');
  scrubber.max = Math.max(0, filtered.length - 1);
  scrubber.value = 0;
  _replayRenderCurrent();
}

async function viewTranscript(sessionId) {
  document.getElementById('transcript-list').style.display = 'none';
  document.getElementById('transcript-viewer').style.display = '';
  document.getElementById('transcript-back-btn').style.display = '';
  document.getElementById('transcript-messages').innerHTML = '<div style="padding:20px;color:#666;">Loading transcript...</div>';
  document.getElementById('replay-controls').style.display = 'none';
  // Reset replay state
  window._replayEvents = [];
  window._replayIndex = 0;
  window._replayFilter = 'all';
  try {
    // Fetch transcript and compaction markers in parallel
    var [data, compactionsData] = await Promise.all([
      fetch('/api/transcript/' + encodeURIComponent(sessionId)).then(r => r.json()),
      fetch('/api/compactions?session_id=' + encodeURIComponent(sessionId) + '&summary_chars=5000').then(r => r.json()).catch(() => ({compactions: []}))
    ]);
    var compactions = compactionsData.compactions || [];
    // Metadata
    var metaHtml = '<div class="stat-row"><span class="stat-label">Session</span><span class="stat-val">' + escHtml(data.name) + '</span></div>';
    metaHtml += '<div class="stat-row"><span class="stat-label">Messages</span><span class="stat-val">' + data.messageCount + '</span></div>';
    if (data.model) metaHtml += '<div class="stat-row"><span class="stat-label">Model</span><span class="stat-val"><span class="badge model">' + escHtml(data.model) + '</span></span></div>';
    if (data.totalTokens) metaHtml += '<div class="stat-row"><span class="stat-label">Tokens</span><span class="stat-val"><span class="badge tokens">' + (data.totalTokens/1000).toFixed(0) + 'K</span></span></div>';
    if (data.duration) metaHtml += '<div class="stat-row"><span class="stat-label">Duration</span><span class="stat-val">' + data.duration + '</span></div>';
    // Add compaction summary if any compactions exist
    if (compactions.length > 0) {
      var totalCompacted = compactions.reduce(function(sum, c) { return sum + (c.tokens_before || 0); }, 0);
      metaHtml += '<div class="stat-row" style="margin-top:8px;padding-top:8px;border-top:1px solid var(--border-secondary);">';
      metaHtml += '<span class="stat-label">💾 Compactions</span><span class="stat-val">' + compactions.length + ' (' + (totalCompacted/1000).toFixed(1) + 'K tokens)</span>';
      metaHtml += '</div>';
    }
    document.getElementById('transcript-meta').innerHTML = metaHtml;
    // Build replay events array - include compaction markers as special events
    var events = [];
    var compactionIdx = 0;
    // Merge compaction markers into the message stream based on timestamp
    var compactionMarkers = compactions.map(function(c) {
      return {
        role: 'compaction',
        type: 'compaction',
        content: c.summary || '',
        timestamp: c.ts_ms,
        tokens_before: c.tokens_before,
        first_kept_entry_id: c.first_kept_entry_id,
        from_hook: c.from_hook,
        summary_truncated: c.summary_truncated
      };
    });
    // Combine messages and compaction markers, then sort by timestamp
    var allMessages = (data.messages || []).concat(compactionMarkers);
    allMessages.sort(function(a, b) {
      var ta = a.timestamp || 0;
      var tb = b.timestamp || 0;
      return ta - tb;
    });
    window._replayEvents = allMessages.map(function(m, idx) {
      return _buildReplayEvent(m, idx);
    });
    if (window._replayEvents.length > 0) {
      // Show replay controls and start at last event (show full conversation by default)
      window._replayIndex = window._replayEvents.length - 1;
      var scrubber = document.getElementById('replay-scrubber');
      scrubber.min = 0;
      scrubber.max = window._replayEvents.length - 1;
      scrubber.value = window._replayIndex;
      document.getElementById('replay-controls').style.display = '';
      // Reset filter pills to "all"
      replayFilter('all');
    } else {
      document.getElementById('transcript-messages').innerHTML = '<div style="color:#555;padding:16px;">No messages in this transcript</div>';
    }
  } catch(e) {
    document.getElementById('transcript-messages').innerHTML = '<div style="color:#e74c3c;padding:16px;">Failed to load transcript</div>';
  }
}

function toggleMsg(idx) {
  var short = document.getElementById('msg-' + idx + '-short');
  var full = document.getElementById('msg-' + idx + '-full');
  if (short.style.display === 'none') {
    short.style.display = '';
    full.style.display = 'none';
    short.nextElementSibling.nextElementSibling.textContent = 'Show more';
  } else {
    short.style.display = 'none';
    full.style.display = '';
    event.target.textContent = 'Show less';
  }
}


// ── Upgrade Banner (on overview page) ──────────────────────────────────────
function dismissUpgradeBanner() {
  document.getElementById('upgrade-banner').style.display = 'none';
  try { localStorage.setItem('cm_upgrade_banner_dismissed', Date.now().toString()); } catch(e){}
}
async function checkUpgradeBanner() {
  try {
    var data = await fetch('/api/version-impact').then(r => r.json());
    if (!data.transitions || data.transitions.length === 0) return;
    var latest = data.transitions[data.transitions.length - 1];
    var upgradedTs = new Date(latest.upgraded_at).getTime();
    // Only show banner for upgrades in the last 7 days
    if (Date.now() - upgradedTs > 7 * 86400000) return;
    // Check if dismissed
    try {
      var dismissed = parseInt(localStorage.getItem('cm_upgrade_banner_dismissed') || '0');
      if (dismissed > upgradedTs) return;
    } catch(e){}
    var costDiff = latest.diff.avg_cost;
    var errorDiff = latest.diff.error_rate;
    var arrows = [];
    if (costDiff && costDiff.pct_change !== null) {
      var c = costDiff.pct_change;
      arrows.push('cost ' + (c > 0 ? '+' : '') + c + '%');
    }
    if (errorDiff && errorDiff.pct_change !== null) {
      var e = errorDiff.pct_change;
      arrows.push('errors ' + (e > 0 ? '+' : '') + e + '%');
    }
    var msg = 'You upgraded from <b>' + escHtml(latest.from_version) + '</b> to <b>' + escHtml(latest.to_version) + '</b>';
    if (arrows.length > 0) msg += ' &mdash; ' + arrows.join(', ');
    var banner = document.getElementById('upgrade-banner');
    document.getElementById('upgrade-banner-msg').innerHTML = msg;
    banner.style.display = 'flex';
  } catch(e){}
}
setTimeout(checkUpgradeBanner, 3000);

// ── Sub-Agent Tree ────────────────────────────────────────────────────────
var _subagentsTimer = null;
var _subagentsExpanded = {};

async function loadSubagents() {
  var el = document.getElementById('subagents-list');
  if (!el) return;
  try {
    var data = await fetch('/api/subagents').then(function(r) { return r.json(); });
    var agents = data.subagents || [];
    var counts = data.counts || {};
    if (agents.length === 0) {
      el.innerHTML = '<div style="color:var(--text-muted);font-size:13px;padding:24px;text-align:center;">No sub-agents found. Sub-agents appear here when spawned by the main session.</div>';
      return;
    }
    var byId = {};
    agents.forEach(function(a) { byId[a.sessionId] = a; });
    var roots = [];
    var childrenOf = {};
    agents.forEach(function(a) {
      var p = a.parent;
      if (p && byId[p]) {
        if (!childrenOf[p]) childrenOf[p] = [];
        childrenOf[p].push(a);
      } else {
        roots.push(a);
      }
    });
    function statusDot(status) {
      var colors = { active: '#16a34a', idle: '#d97706', stale: '#6b7280', failed: '#ef4444' };
      var glow = status === 'active' ? 'box-shadow:0 0 6px rgba(22,163,74,0.6);'
               : status === 'failed' ? 'box-shadow:0 0 6px rgba(239,68,68,0.5);' : '';
      return '<span style="display:inline-block;width:8px;height:8px;border-radius:50%;background:' + (colors[status] || '#6b7280') + ';' + glow + 'flex-shrink:0;margin-right:4px;"></span>';
    }
    function renderAgent(a, depth) {
      var sid = a.sessionId;
      var hasChildren = !!(childrenOf[sid] && childrenOf[sid].length > 0);
      var isExpanded = _subagentsExpanded[sid] !== false;
      var indent = depth > 0 ? 'padding-left:' + (depth * 22 + 12) + 'px;' : 'padding-left:12px;';
      var toggleBtn = hasChildren
        ? '<button onclick="event.stopPropagation();_saToggle(' + JSON.stringify(sid) + ')" style="background:none;border:none;cursor:pointer;font-size:11px;color:var(--text-muted);padding:0 4px 0 0;line-height:1;min-width:16px;">' + (isExpanded ? '▼' : '▶') + '</button>'
        : '<span style="display:inline-block;min-width:16px;"></span>';
      var tokens = a.totalTokens >= 1000 ? (a.totalTokens / 1000).toFixed(1) + 'K' : a.totalTokens;
      var depthBadge = a.depth > 0 ? '<span style="font-size:10px;background:var(--bg-secondary);border:1px solid var(--border-primary);border-radius:4px;padding:1px 5px;color:var(--text-muted);margin-left:6px;">d' + a.depth + '</span>' : '';
      // Click row → subagent detail modal (same call used by Active Tasks cards).
      // Stop-propagation on the toggle button already handles tree expansion.
      var name = (a.displayName || '').replace(/"/g,'&quot;').replace(/'/g,"\\'");
      var sidEsc = (a.sessionId || '').replace(/'/g,"\\'");
      var keyEsc = (a.key || a.sessionId || '').replace(/'/g,"\\'");
      var clickAttr = ' onclick="openTaskModal(\'' + sidEsc + '\',\'' + name + '\',\'' + keyEsc + '\')"';
      var cursor = 'cursor:pointer;';
      var html = '<div' + clickAttr + ' style="display:flex;align-items:center;gap:6px;' + indent + 'padding-top:8px;padding-bottom:8px;padding-right:12px;border-bottom:1px solid var(--border-secondary);' + cursor + 'transition:background 0.1s;" onmouseover="this.style.background=\'var(--bg-hover)\'" onmouseout="this.style.background=\'\'">';
      html += toggleBtn;
      html += statusDot(a.status);
      html += '<span style="font-weight:600;font-size:13px;color:var(--text-primary);flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;" title="' + escHtml(a.displayName) + '">' + escHtml(a.displayName) + '</span>';
      html += depthBadge;
      if (a.status === 'failed') {
        html += '<span style="font-size:10px;background:rgba(239,68,68,0.12);color:#ef4444;border:1px solid rgba(239,68,68,0.4);border-radius:4px;padding:1px 6px;margin-left:6px;font-weight:700;">FAILED</span>';
      }
      html += '<span style="font-size:11px;color:var(--text-muted);white-space:nowrap;margin-left:8px;">' + escHtml(a.model || '') + '</span>';
      html += '<span style="font-size:11px;color:var(--text-muted);white-space:nowrap;margin-left:8px;">' + tokens + ' tok</span>';
      html += '<span style="font-size:11px;color:var(--text-faint);white-space:nowrap;margin-left:8px;">' + escHtml(a.runtime || '') + '</span>';
      html += '</div>';
      if (hasChildren && isExpanded) {
        childrenOf[sid].forEach(function(child) { html += renderAgent(child, depth + 1); });
      }
      return html;
    }
    var summaryHtml = '<div style="display:flex;gap:16px;padding:8px 14px;background:var(--bg-secondary);border-bottom:1px solid var(--border-primary);font-size:12px;flex-wrap:wrap;">';
    summaryHtml += '<span style="color:var(--text-muted);"><strong style="color:var(--text-primary);">' + (counts.total || 0) + '</strong> total</span>';
    if (counts.active) summaryHtml += '<span style="color:#16a34a;"><strong>' + counts.active + '</strong> active</span>';
    if (counts.idle) summaryHtml += '<span style="color:#d97706;"><strong>' + counts.idle + '</strong> idle</span>';
    if (counts.stale) summaryHtml += '<span style="color:var(--text-muted);"><strong>' + counts.stale + '</strong> stale</span>';
    if (counts.failed) summaryHtml += '<span style="color:#ef4444;"><strong>' + counts.failed + '</strong> failed</span>';
    summaryHtml += '</div>';
    var treeHtml = '<div style="border:1px solid var(--border-primary);border-radius:10px;overflow:hidden;">' + summaryHtml;
    roots.forEach(function(a) { treeHtml += renderAgent(a, 0); });
    treeHtml += '</div>';
    el.innerHTML = treeHtml;
  } catch(e) {
    el.innerHTML = '<div style="color:#e74c3c;font-size:13px;padding:16px;">Failed to load sub-agents: ' + escHtml(String(e)) + '</div>';
  }
}

function _saToggle(sid) {
  _subagentsExpanded[sid] = (_subagentsExpanded[sid] === false) ? true : false;
  loadSubagents();
}

// ── Upgrade Impact Panel ───────────────────────────────────────────────────
async function loadVersionImpact() {
  var el = document.getElementById('version-impact-content');
  if (!el) return;
  el.innerHTML = '<div style="color:var(--text-muted);font-size:13px;padding:16px;">Loading version impact data...</div>';
  try {
    var data = await fetch('/api/version-impact').then(r => r.json());
    if (!data.version_detected) {
      el.innerHTML = '<div class="card" style="padding:20px;text-align:center;"><div style="font-size:15px;font-weight:600;color:var(--text-primary);">Version not detected</div><div style="font-size:13px;color:var(--text-muted);margin-top:8px;">Could not detect OpenClaw version from config.</div></div>';
      return;
    }
    var html = '<div style="display:flex;align-items:center;gap:12px;margin-bottom:16px;flex-wrap:wrap;">';
    html += '<div class="card" style="padding:12px 20px;display:inline-flex;align-items:center;gap:10px;">';
    html += '<span style="font-size:12px;color:var(--text-muted);">Current Version</span>';
    html += '<span style="font-size:16px;font-weight:700;color:var(--text-accent);">' + escHtml(data.current_version) + '</span>';
    html += '</div>';
    if (data.version_history && data.version_history.length > 0) {
      html += '<div style="font-size:12px;color:var(--text-muted);">' + data.version_history.length + ' version(s) tracked</div>';
    }
    html += '</div>';
    if (data.version_history && data.version_history.length > 1) {
      html += '<div class="card" style="padding:16px;margin-bottom:16px;">';
      html += '<div style="font-size:13px;font-weight:600;color:var(--text-primary);margin-bottom:10px;">Version Timeline</div>';
      html += '<div style="display:flex;gap:4px;align-items:center;flex-wrap:wrap;">';
      data.version_history.forEach(function(v, i) {
        html += '<div style="display:flex;align-items:center;gap:4px;">';
        html += '<div style="background:var(--text-accent);color:#fff;padding:4px 10px;border-radius:6px;font-size:12px;font-weight:600;">' + escHtml(v.version) + '</div>';
        html += '<div style="font-size:10px;color:var(--text-muted);">' + new Date(v.detected_at).toLocaleDateString() + '</div>';
        if (i < data.version_history.length - 1) html += '<div style="color:var(--text-muted);">&#8594;</div>';
        html += '</div>';
      });
      html += '</div></div>';
    }
    if (!data.transitions || data.transitions.length === 0) {
      html += '<div class="card" style="padding:20px;text-align:center;"><div style="font-size:13px;color:var(--text-muted);">No version transitions yet. Comparison metrics will appear after the next OpenClaw upgrade.</div></div>';
    } else {
      data.transitions.forEach(function(t) {
        html += '<div class="card" style="padding:16px;margin-bottom:12px;">';
        html += '<div style="display:flex;align-items:center;gap:12px;margin-bottom:12px;flex-wrap:wrap;">';
        html += '<span style="font-size:13px;font-weight:600;color:var(--text-muted);">' + escHtml(t.from_version) + '</span>';
        html += '<span style="color:var(--text-accent);font-size:18px;">&#8594;</span>';
        html += '<span style="font-size:15px;font-weight:700;color:var(--text-accent);">' + escHtml(t.to_version) + '</span>';
        html += '<span style="font-size:11px;color:var(--text-muted);">upgraded ' + timeAgo(new Date(t.upgraded_at).getTime() / 1000) + '</span>';
        html += '</div>';
        html += '<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:10px;">';
        var metrics = [
          {key:'avg_cost', label:'Avg Cost/Session', fmtFn: function(v){return '$'+v.toFixed(5);}},
          {key:'avg_tokens', label:'Avg Tokens', fmtFn: function(v){return Math.round(v).toLocaleString();}},
          {key:'avg_tool_calls', label:'Avg Tool Calls', fmtFn: function(v){return v.toFixed(1);}},
          {key:'error_rate', label:'Error Rate', fmtFn: function(v){return (v*100).toFixed(1)+'%';}},
          {key:'avg_duration_ms', label:'Avg Duration', fmtFn: function(v){return v > 60000 ? (v/60000).toFixed(1)+'m' : (v/1000).toFixed(0)+'s';}}
        ];
        metrics.forEach(function(m) {
          var diff = t.diff[m.key];
          if (!diff) return;
          var pct = diff.pct_change;
          var isGoodDown = (m.key === 'avg_cost' || m.key === 'error_rate' || m.key === 'avg_duration_ms');
          var color = pct === null ? 'var(--text-muted)' : (pct === 0 ? 'var(--text-muted)' : (isGoodDown ? (pct < 0 ? '#22c55e' : '#ef4444') : (pct > 0 ? '#22c55e' : '#ef4444')));
          var arrow = pct === null ? '' : (pct > 0 ? '&#8593;' : pct < 0 ? '&#8595;' : '=');
          html += '<div style="background:var(--bg-secondary);border:1px solid var(--border-primary);border-radius:8px;padding:10px;">';
          html += '<div style="font-size:11px;color:var(--text-muted);margin-bottom:4px;">' + m.label + '</div>';
          html += '<div style="display:flex;align-items:baseline;gap:6px;">';
          html += '<span style="font-size:13px;font-weight:600;color:var(--text-primary);">' + m.fmtFn(diff.after) + '</span>';
          if (pct !== null) html += '<span style="font-size:11px;color:' + color + ';font-weight:600;">' + arrow + ' ' + Math.abs(pct) + '%</span>';
          html += '</div>';
          html += '<div style="font-size:10px;color:var(--text-muted);">before: ' + m.fmtFn(diff.before) + '</div>';
          html += '</div>';
        });
        html += '</div>';
        html += '<div style="margin-top:8px;font-size:11px;color:var(--text-muted);">Sessions before: ' + t.before.session_count + ' &bull; after: ' + t.after.session_count + '</div>';
        html += '</div>';
      });
    }
    el.innerHTML = html;
  } catch(e) {
    el.innerHTML = '<div style="padding:16px;color:var(--text-error);">Failed to load version impact data</div>';
  }
}

// ── Session Clusters Panel ─────────────────────────────────────────────────
// ═══════════════════════════════════════════════════════════════════════════
// Rate Limit Monitor — GH#67
// ═══════════════════════════════════════════════════════════════════════════

var _rateLimitTimer = null;

async function loadRateLimits() {
  var container = document.getElementById('rate-limits-content');
  var hourlyEl = document.getElementById('rate-limits-hourly');
  if (!container) return;
  try {
    var data = await fetch('/api/rate-limits').then(function(r) { return r.json(); });
    var providers = data.providers || [];

    if (providers.length === 0) {
      container.innerHTML = '<div class="card" style="padding:24px;text-align:center;color:var(--text-muted);">No API usage data yet. Rate limits will appear once OTLP metrics flow from the OpenClaw gateway.</div>';
      if (hourlyEl) hourlyEl.innerHTML = '';
      return;
    }

    var html = '<div class="grid">';
    providers.forEach(function(p) {
      var statusColor = p.status === 'red' ? '#ef4444' : (p.status === 'amber' ? '#f59e0b' : '#22c55e');
      var statusBg = p.status === 'red' ? 'rgba(239,68,68,0.1)' : (p.status === 'amber' ? 'rgba(245,158,11,0.1)' : 'rgba(34,197,94,0.1)');
      var statusBorder = p.status === 'red' ? 'rgba(239,68,68,0.3)' : (p.status === 'amber' ? 'rgba(245,158,11,0.3)' : 'rgba(34,197,94,0.15)');
      var statusLabel = p.status === 'red' ? '\uD83D\uDD34 HIGH' : (p.status === 'amber' ? '\uD83D\uDFE1 MODERATE' : '\uD83D\uDFE2 OK');
      html += '<div class="card" style="border:1px solid ' + statusBorder + ';background:' + statusBg + ';">';
      html += '<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;">';
      html += '<div class="card-title" style="margin:0;">' + escHtml(p.label) + '</div>';
      html += '<span style="font-size:11px;font-weight:700;color:' + statusColor + ';">' + statusLabel + '</span>';
      html += '</div>';
      html += _rateLimitBar('RPM (1 min)', p.rpm.current, p.rpm.limit, p.rpm.pct);
      html += _rateLimitBar('Input TPM (1 min)', p.tpm_input.current, p.tpm_input.limit, p.tpm_input.pct);
      html += _rateLimitBar('Output TPM (1 min)', p.tpm_output.current, p.tpm_output.limit, p.tpm_output.pct);
      if (p.models && p.models.length > 0) {
        html += '<div style="margin-top:8px;font-size:11px;color:var(--text-muted);">Models: ';
        p.models.forEach(function(m) {
          html += '<span style="display:inline-block;padding:2px 6px;margin:2px;background:var(--bg-secondary);border-radius:4px;font-size:10px;">' + escHtml(m) + '</span>';
        });
        html += '</div>';
      }
      html += '</div>';
    });
    html += '</div>';
    container.innerHTML = html;

    // Hourly summary
    var hourlyHtml = '<div class="section-title">&#128202; Last Hour Summary</div><div class="grid">';
    var totalReqs = 0, totalCost = 0;
    providers.forEach(function(p) { totalReqs += p.hour.requests; totalCost += p.hour.cost_usd; });
    hourlyHtml += '<div class="card"><div class="card-title"><span class="icon">&#128232;</span> Requests (1h)</div><div class="card-value">' + totalReqs.toLocaleString() + '</div></div>';
    hourlyHtml += '<div class="card"><div class="card-title"><span class="icon">&#128176;</span> Cost (1h)</div><div class="card-value">$' + totalCost.toFixed(4) + '</div></div>';
    providers.forEach(function(p) {
      hourlyHtml += '<div class="card"><div class="card-title"><span class="icon">&#128279;</span> ' + escHtml(p.label) + '</div>';
      hourlyHtml += '<div class="card-value">' + p.hour.requests + ' reqs</div>';
      hourlyHtml += '<div class="card-sub">' + p.hour.tokens_in.toLocaleString() + ' in / ' + p.hour.tokens_out.toLocaleString() + ' out &middot; $' + p.hour.cost_usd.toFixed(4) + '</div></div>';
    });
    hourlyHtml += '</div>';
    if (hourlyEl) hourlyEl.innerHTML = hourlyHtml;

    // Auto-refresh every 30s while tab is active
    if (_rateLimitTimer) clearInterval(_rateLimitTimer);
    _rateLimitTimer = setInterval(function() {
      var limitsPage = document.getElementById('page-limits');
      if (limitsPage && limitsPage.classList.contains('active')) loadRateLimits();
      else { clearInterval(_rateLimitTimer); _rateLimitTimer = null; }
    }, 30000);
  } catch(e) {
    if (container) container.innerHTML = '<div class="card" style="padding:16px;color:#ef4444;">Failed to load rate limits: ' + escHtml(String(e)) + '</div>';
  }
}

function _rateLimitBar(label, current, limit, pct) {
  var barColor = pct >= 90 ? '#ef4444' : (pct >= 70 ? '#f59e0b' : '#22c55e');
  var w = Math.min(pct, 100);
  var fmt = typeof current === 'number' ? (current >= 1000 ? (current/1000).toFixed(1) + 'k' : String(current)) : String(current);
  var limFmt = typeof limit === 'number' ? (limit >= 1000 ? (limit/1000).toFixed(0) + 'k' : String(limit)) : String(limit);
  var html = '<div style="margin-bottom:8px;">';
  html += '<div style="display:flex;justify-content:space-between;font-size:11px;color:var(--text-muted);margin-bottom:3px;">';
  html += '<span>' + escHtml(label) + '</span><span style="color:' + barColor + ';font-weight:600;">' + fmt + ' / ' + limFmt + ' (' + pct + '%)</span>';
  html += '</div>';
  html += '<div style="background:var(--bg-secondary);border-radius:4px;height:6px;overflow:hidden;">';
  html += '<div style="width:' + w + '%;height:100%;background:' + barColor + ';border-radius:4px;transition:width 0.4s;"></div>';
  html += '</div></div>';
  return html;
}

// ─────────────────────────────────────────────────────────────────────────────
async function loadClusters() {
  var el = document.getElementById('clusters-content');
  if (!el) return;
  el.innerHTML = '<div style="color:var(--text-muted);font-size:13px;padding:16px;">Analyzing session patterns...</div>';
  try {
    var data = await fetch('/api/clusters').then(r => r.json());
    if (!data.clusters || data.clusters.length === 0) {
      el.innerHTML = '<div class="card" style="padding:20px;text-align:center;"><div style="font-size:13px;color:var(--text-muted);">No sessions found to cluster.</div></div>';
      return;
    }
    var clusterColors = {'browsing-heavy':'#60a5fa','code-heavy':'#34d399','messaging':'#f472b6','doc-analysis':'#a78bfa','mixed-research':'#fbbf24','cron-light':'#94a3b8','expensive-outlier':'#ef4444','general':'#6b7280'};
    var html = '<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:12px;margin-bottom:16px;">';
    data.clusters.forEach(function(cl) {
      var color = clusterColors[cl.label] || '#6b7280';
      var errorPct = (cl.error_rate * 100).toFixed(0);
      html += '<div class="card" style="padding:16px;border-top:3px solid ' + color + ';">';
      html += '<div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:8px;">';
      html += '<div><div style="font-size:14px;font-weight:700;color:var(--text-primary);">' + escHtml(cl.label) + '</div>';
      html += '<div style="font-size:12px;color:var(--text-muted);">' + cl.session_count + ' session' + (cl.session_count !== 1 ? 's' : '') + '</div></div>';
      html += '<div style="background:' + color + '22;color:' + color + ';padding:4px 8px;border-radius:12px;font-size:11px;font-weight:600;">' + cl.session_count + '</div>';
      html += '</div>';
      html += '<div style="display:grid;grid-template-columns:1fr 1fr;gap:6px;margin-bottom:8px;">';
      html += '<div style="font-size:12px;"><span style="color:var(--text-muted);">Avg cost:</span> <span style="font-weight:600;color:var(--text-primary);">$' + cl.avg_cost.toFixed(4) + '</span></div>';
      html += '<div style="font-size:12px;"><span style="color:var(--text-muted);">Avg tokens:</span> <span style="font-weight:600;color:var(--text-primary);">' + (cl.avg_tokens / 1000).toFixed(1) + 'K</span></div>';
      html += '<div style="font-size:12px;"><span style="color:var(--text-muted);">Error rate:</span> <span style="font-weight:600;">' + errorPct + '%</span></div>';
      if (cl.rep_session) {
        html += '<div style="font-size:12px;"><span style="color:var(--text-muted);">Top session:</span> <span style="font-family:monospace;color:var(--text-accent);" title="' + escHtml(cl.rep_session.id) + '">' + escHtml(cl.rep_session.id.substring(0,8)) + '</span></div>';
      }
      html += '</div>';
      if (cl.rep_session && cl.rep_session.tools && cl.rep_session.tools.length > 0) {
        html += '<div style="margin-top:6px;display:flex;gap:4px;flex-wrap:wrap;">';
        cl.rep_session.tools.slice(0,5).forEach(function(t) {
          html += '<span style="background:var(--bg-secondary);border:1px solid var(--border-primary);border-radius:4px;font-size:10px;padding:2px 6px;color:var(--text-muted);">' + escHtml(t) + '</span>';
        });
        html += '</div>';
      }
      html += '</div>';
    });
    html += '</div>';
    var total = data.clusters.reduce(function(s, c) { return s + c.session_count; }, 0);
    html += '<div class="card" style="padding:12px 16px;font-size:12px;color:var(--text-muted);">Total: <strong style="color:var(--text-primary);">' + total + ' sessions</strong> across <strong style="color:var(--text-primary);">' + data.clusters.length + ' clusters</strong></div>';
    el.innerHTML = html;
  } catch(e) {
    el.innerHTML = '<div style="padding:16px;color:var(--text-error);">Failed to load clusters</div>';
  }
}

var _overviewRefreshRunning = false;
function startOverviewRefresh() {
  // Don't fire loadAll() immediately -- bootDashboard already called it
  if (window._overviewTimer) clearInterval(window._overviewTimer);
  window._overviewTimer = setInterval(async function() {
    if (_overviewRefreshRunning) return;
    _overviewRefreshRunning = true;
    try { await loadAll(); } finally { _overviewRefreshRunning = false; }
  }, 10000);
  loadMainActivity();
  if (window._mainActivityTimer) clearInterval(window._mainActivityTimer);
  window._mainActivityTimer = setInterval(loadMainActivity, 5000);
}

// Overview right-panel Brain stream: reuses /api/brain-history (same source as
// the full Brain tab) so users see the identical unified event stream here —
// THINK / AGENT / USER / EXEC / READ / WRITE / SEARCH / SPAWN / CONTEXT / MSG
// instead of the previous "last tool call only" summary.
async function loadMainActivity() {
  try {
    var data = await fetchJsonWithTimeout('/api/brain-history?limit=40', 6000);
    var el = document.getElementById('main-activity-list');
    var dot = document.getElementById('main-activity-dot');
    var label = document.getElementById('main-activity-label');
    var events = (data && data.events) ? data.events.slice() : [];
    // /api/brain-history pins CONTEXT events to the top of the array (Brain
    // tab feature) — for the compact Overview panel we want pure timestamp
    // desc so the most recent conversation sits at the top.
    events.sort(function(a, b) {
      return (b.time || '').localeCompare(a.time || '');
    });

    if (!events.length) {
      el.innerHTML = '<div style="text-align:center;padding:20px;color:var(--text-muted);">No recent activity</div>';
      if (dot) dot.style.background = '#888';
      if (label) { label.textContent = 'No data'; label.style.color = 'var(--text-muted)'; }
      return;
    }

    // Activity = newest event within last 60s → pulse green, else idle amber
    var now = Date.now();
    var latestTs = 0;
    events.forEach(function(ev) {
      var t = Date.parse(ev.time || '');
      if (!isNaN(t) && t > latestTs) latestTs = t;
    });
    var idle = !latestTs || (now - latestTs) > 60000;
    if (dot) {
      dot.style.background = idle ? '#f39c12' : '#2ecc71';
      dot.style.animation = idle ? 'none' : 'pulse-dot 1.5s ease-in-out infinite';
    }
    if (label) {
      label.textContent = idle ? 'Idle' : 'Active';
      label.style.color = idle ? '#f39c12' : '#2ecc71';
    }

    // Per-type colour + icon table matches Brain tab (#page-brain)
    var TYPE_STYLE = {
      USER:     {c:'#9ab4ff', icon:'💬'},
      AGENT:    {c:'#c0a0ff', icon:'🤖'},
      THINK:    {c:'#6ec1e4', icon:'🧠'},
      EXEC:     {c:'#f0c060', icon:'⚡'},
      READ:     {c:'#78dca7', icon:'📖'},
      WRITE:    {c:'#78dca7', icon:'✏️'},
      SEARCH:   {c:'#f28fb0', icon:'🔍'},
      BROWSER:  {c:'#9cd88a', icon:'🌐'},
      MSG:      {c:'#8ec7ff', icon:'💬'},
      SPAWN:    {c:'#d19cf5', icon:'✨'},
      CONTEXT:  {c:'#9aa8bd', icon:'📚'},
      RESULT:   {c:'#78dca7', icon:'✓'},
      TOOL:     {c:'#f0c060', icon:'⚙️'},
    };

    var html = '';
    // Server returns newest-first; render top-down so scroll up = older
    events.forEach(function(ev) {
      var t = ev.time ? new Date(ev.time) : null;
      var ts = '';
      if (t && !isNaN(t.getTime())) {
        ts = t.toLocaleTimeString('en-GB', {hour:'2-digit',minute:'2-digit',second:'2-digit'});
      }
      var type = (ev.type || 'TOOL').toUpperCase();
      var style = TYPE_STYLE[type] || {c:'#c0c0c0', icon:'•'};
      var detail = (ev.detail || '').replace(/</g,'&lt;').replace(/>/g,'&gt;');
      if (detail.length > 80) detail = detail.substring(0, 77) + '…';
      var src = ev.sourceLabel || ev.source || '';
      if (src.length > 12) src = src.substring(0, 10) + '…';
      html += '<div style="display:flex;gap:6px;align-items:center;padding:3px 0;border-bottom:1px solid rgba(255,255,255,0.04);">';
      html += '<span style="color:var(--text-faint);min-width:58px;font-size:10px;font-variant-numeric:tabular-nums;">' + ts + '</span>';
      html += '<span style="font-size:12px;min-width:16px;text-align:center;">' + style.icon + '</span>';
      html += '<span style="color:' + style.c + ';min-width:52px;font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:0.4px;">' + type + '</span>';
      if (src) {
        html += '<span style="color:var(--text-muted);min-width:48px;font-size:9.5px;overflow:hidden;text-overflow:ellipsis;" title="' + src + '">' + src + '</span>';
      }
      html += '<span style="color:#d0d0d0;flex:1;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;" title="' + detail + '">' + detail + '</span>';
      html += '</div>';
    });
    el.innerHTML = html;
  } catch(e) {}
}

// Real-time log stream via SSE
var logStream = null;
var streamBuffer = [];
var MAX_STREAM_LINES = 500;

function startLogStream() {
  if (window.CLOUD_MODE) return;
  if (logStream) logStream.close();
  streamBuffer = [];
  var statusEl = document.getElementById('log-stream-status');
  if (statusEl) statusEl.textContent = '\u25cf Connecting\u2026';
  logStream = new EventSource('/api/logs-stream' + (localStorage.getItem('clawmetry-token') ? '?token=' + encodeURIComponent(localStorage.getItem('clawmetry-token')) : ''));
  logStream.onopen = function() {
    var s = document.getElementById('log-stream-status');
    if (s) { s.textContent = '\u25cf Live'; s.style.color = '#22c55e'; }
  };
  logStream.onmessage = function(e) {
    var data = JSON.parse(e.data);
    streamBuffer.push(data.line);
    if (streamBuffer.length > MAX_STREAM_LINES) streamBuffer.shift();
    appendLogLine('ov-logs', data.line);
    appendLogLine('logs-full', data.line);
    processFlowEvent(data.line);
    document.getElementById('refresh-time').textContent = 'Live \u2022 ' + new Date().toLocaleTimeString();
  };
  logStream.onerror = function() {
    var s = document.getElementById('log-stream-status');
    if (s) { s.textContent = '\u25cf Reconnecting\u2026'; s.style.color = '#f59e0b'; }
    setTimeout(startLogStream, 5000);
  };
}

function parseLogLine(line) {
  try {
    var obj = JSON.parse(line);
    var ts = '';
    if (obj.time || (obj._meta && obj._meta.date)) {
      var d = new Date(obj.time || obj._meta.date);
      ts = d.toLocaleTimeString('en-GB', {hour:'2-digit', minute:'2-digit', second:'2-digit'});
    }
    var level = (obj.logLevelName || obj.level || 'info').toLowerCase();
    var cls = 'info';
    if (level === 'error' || level === 'fatal') cls = 'err';
    else if (level === 'warn' || level === 'warning') cls = 'warn';
    else if (level === 'debug') cls = 'msg';
    var msg = obj.msg || obj.message || obj.name || '';
    var extras = [];
    if (obj["0"]) extras.push(obj["0"]);
    if (obj["1"]) extras.push(obj["1"]);
    var display;
    if (msg && extras.length) display = msg + ' | ' + extras.join(' ');
    else if (extras.length) display = extras.join(' ');
    else if (!msg) display = line.substring(0, 200);
    else display = msg;
    if (ts) display = '<span class="ts">' + ts + '</span> ' + escHtml(display);
    else display = escHtml(display);
    return {cls: cls, html: display};
  } catch(e) {
    var cls = 'msg';
    if (line.includes('Error') || line.includes('failed')) cls = 'err';
    else if (line.includes('WARN')) cls = 'warn';
    else if (line.includes('run start') || line.includes('inbound')) cls = 'info';
    return {cls: cls, html: escHtml(line.substring(0, 300))};
  }
}

function appendLogLine(elId, line) {
  var el = document.getElementById(elId);
  if (!el) return;
  var parsed = parseLogLine(line);
  var div = document.createElement('div');
  div.className = 'log-line';
  div.innerHTML = '<span class="' + parsed.cls + '">' + parsed.html + '</span>';
  el.appendChild(div);
  while (el.children.length > MAX_STREAM_LINES) el.removeChild(el.firstChild);
  // Apply live filter for logs-full
  if (elId === 'logs-full') {
    var span = el.lastElementChild ? el.lastElementChild.querySelector('span') : null;
    var cls = span ? span.className : '';
    var text = el.lastElementChild ? el.lastElementChild.textContent.toLowerCase() : '';
    var query = (document.getElementById('log-filter') ? document.getElementById('log-filter').value : '').toLowerCase();
    var levelOk = _logLevelFilter === 'all'
      || (_logLevelFilter === 'error' && cls === 'err')
      || (_logLevelFilter === 'warn'  && (cls === 'warn' || cls === 'err'))
      || (_logLevelFilter === 'info'  && (cls === 'info' || cls === 'warn' || cls === 'err'));
    if (!levelOk || (query && !text.includes(query))) el.lastElementChild.style.display = 'none';
  }
  var autoScroll = document.getElementById('log-autoscroll');
  if (!autoScroll || autoScroll.checked) {
    if (el.scrollHeight - el.scrollTop - el.clientHeight < 150) {
      el.scrollTop = el.scrollHeight;
    }
  }
}


// ===== Log Tab Helpers =====
var _logLevelFilter = 'all';

function setLogLevel(level, btn) {
  _logLevelFilter = level;
  document.querySelectorAll('#page-logs .time-btn').forEach(function(b) { b.classList.remove('active'); });
  if (btn) btn.classList.add('active');
  filterLogLines();
}

function filterLogLines() {
  var el = document.getElementById('logs-full');
  if (!el) return;
  var query = (document.getElementById('log-filter') ? document.getElementById('log-filter').value : '').toLowerCase();
  Array.from(el.children).forEach(function(div) {
    var span = div.querySelector('span');
    var cls = span ? span.className : '';
    var text = div.textContent.toLowerCase();
    var levelOk = _logLevelFilter === 'all'
      || (_logLevelFilter === 'error' && cls === 'err')
      || (_logLevelFilter === 'warn'  && (cls === 'warn' || cls === 'err'))
      || (_logLevelFilter === 'info'  && (cls === 'info' || cls === 'warn' || cls === 'err'));
    var queryOk = !query || text.includes(query);
    div.style.display = levelOk && queryOk ? '' : 'none';
  });
}

// ===== Flow Visualization Engine =====
var flowStats = { messages: 0, events: 0, activeTools: {}, msgTimestamps: [] };
var flowInitDone = false;

function hideUnconfiguredChannels(svgRoot) {
  // Hide channel nodes and their paths for unconfigured channels
  // All known channels mapped to SVG slot paths
  // Slot assignments: tg=slot1, sig=slot2(middle), wa=slot3
  // Extra channels share slot2 paths and get dynamically repositioned
  var channelMap = {
    'tui':         { node: 'node-tui',         paths: ['path-human-tg',  'path-tg-gw'] },
    'telegram':    { node: 'node-telegram',    paths: ['path-human-tg',  'path-tg-gw'] },
    'signal':      { node: 'node-signal',      paths: ['path-human-sig', 'path-sig-gw'] },
    'whatsapp':    { node: 'node-whatsapp',    paths: ['path-human-wa',  'path-wa-gw'] },
    'imessage':    { node: 'node-imessage',    paths: ['path-human-sig', 'path-sig-gw'] },
    'discord':     { node: 'node-discord',     paths: ['path-human-sig', 'path-sig-gw'] },
    'slack':       { node: 'node-slack',       paths: ['path-human-sig', 'path-sig-gw'] },
    'irc':         { node: 'node-irc',         paths: ['path-human-sig', 'path-sig-gw'] },
    'webchat':     { node: 'node-webchat',     paths: ['path-human-sig', 'path-sig-gw'] },
    'googlechat':  { node: 'node-googlechat',  paths: ['path-human-sig', 'path-sig-gw'] },
    'bluebubbles': { node: 'node-bluebubbles', paths: ['path-human-sig', 'path-sig-gw'] },
    'msteams':     { node: 'node-msteams',     paths: ['path-human-sig', 'path-sig-gw'] },
    'matrix':      { node: 'node-matrix',      paths: ['path-human-sig', 'path-sig-gw'] },
    'mattermost':  { node: 'node-mattermost',  paths: ['path-human-sig', 'path-sig-gw'] },
    'line':        { node: 'node-line',        paths: ['path-human-sig', 'path-sig-gw'] },
    'nostr':       { node: 'node-nostr',       paths: ['path-human-sig', 'path-sig-gw'] },
    'twitch':      { node: 'node-twitch',      paths: ['path-human-sig', 'path-sig-gw'] },
    'feishu':      { node: 'node-feishu',      paths: ['path-human-sig', 'path-sig-gw'] },
    'zalo':        { node: 'node-zalo',        paths: ['path-human-sig', 'path-sig-gw'] }
  };
  // Priority order for slot assignment (up to 3 visible at a time)
  var SLOT_ORDER = ['tui', 'telegram', 'whatsapp', 'imessage', 'signal', 'discord', 'slack',
                    'irc', 'webchat', 'googlechat', 'bluebubbles', 'msteams', 'matrix',
                    'mattermost', 'line', 'nostr', 'twitch', 'feishu', 'zalo'];
  fetch('/api/channels').then(function(r){return r.json();}).then(function(d) {
    var active = d.channels || ['telegram', 'signal', 'whatsapp'];
    // Build display list: up to 3 channels, prioritized by SLOT_ORDER
    var visibleChannels = SLOT_ORDER.filter(function(ch) { return active.indexOf(ch) !== -1; }).slice(0, 3);
    // First: hide ALL known channel nodes
    Object.keys(channelMap).forEach(function(ch) {
      var info = channelMap[ch];
      var node = svgRoot.getElementById ? svgRoot.getElementById(info.node) : svgRoot.querySelector('#' + info.node);
      if (node) node.style.display = 'none';
    });
    // Hide all channel paths too
    ['path-human-tg','path-tg-gw','path-human-sig','path-sig-gw','path-human-wa','path-wa-gw'].forEach(function(pid) {
      var p = svgRoot.getElementById ? svgRoot.getElementById(pid) : svgRoot.querySelector('#' + pid);
      if (p) p.style.display = 'none';
    });
    // Then: show only the active ones and reposition with clean spacing
    var yPositions = [120, 183, 246]; // default 3-channel positions (63px gap)
    if (visibleChannels.length === 1) yPositions = [183];
    else if (visibleChannels.length === 2) yPositions = [145, 225];
    visibleChannels.forEach(function(ch, i) {
      var info = channelMap[ch];
      if (!info) return;
      var node = svgRoot.getElementById ? svgRoot.getElementById(info.node) : svgRoot.querySelector('#' + info.node);
      if (!node) return;
      node.style.display = ''; // show it
      var rect = node.querySelector('rect');
      var text = node.querySelector('text');
      var targetY = yPositions[i];
      if (rect) { rect.setAttribute('y', targetY - 20); }
      if (text) { text.setAttribute('y', targetY + 5); }
      // Show and update paths
      var humanPath = svgRoot.getElementById ? svgRoot.getElementById(info.paths[0]) : svgRoot.querySelector('#' + info.paths[0]);
      if (humanPath) {
        humanPath.style.display = '';
        humanPath.setAttribute('d', 'M 60 56 C 60 ' + (targetY - 30) + ', 65 ' + (targetY - 15) + ', 75 ' + (targetY - 20));
      }
      var gwPath = svgRoot.getElementById ? svgRoot.getElementById(info.paths[1]) : svgRoot.querySelector('#' + info.paths[1]);
      if (gwPath) {
        gwPath.style.display = '';
        gwPath.setAttribute('d', 'M 130 ' + targetY + ' C 150 ' + targetY + ', 160 ' + (183) + ', 180 ' + (183));
      }
    });
  }).catch(function(){});
}

var _flowSse = null;
var _flowSseDebounce = {};
function _startFlowSse() {
  if (window.CLOUD_MODE) return;
  if (_flowSse && _flowSse.readyState !== EventSource.CLOSED) return;
  var _fTok = localStorage.getItem('clawmetry-token') || '';
  _flowSse = new EventSource('/api/flow-events' + (_fTok ? '?token=' + encodeURIComponent(_fTok) : ''));
  _flowSse.onmessage = function(e) {
    try {
      var evt = JSON.parse(e.data);
      var type = evt.type, now = Date.now();
      var dk = type + '_' + (evt.tool || evt.channel || '');
      if (_flowSseDebounce[dk] && (now - _flowSseDebounce[dk]) < 200) return;
      _flowSseDebounce[dk] = now;
      if (type === 'msg_in') {
        triggerInbound(evt.channel || 'tg');
        addFlowFeedItem('📨 Message via ' + (evt.channel || 'telegram'), '#c0a0ff', 'inbound');
        flowStats.msgTimestamps.push(now);
      } else if (type === 'msg_out') {
        triggerOutbound(evt.channel || 'tg');
        addFlowFeedItem('📤 Replied via ' + (evt.channel || 'telegram'), '#50e080', 'reply');
      } else if (type === 'tool_call') {
        var toolName = evt.tool || 'exec';
        triggerToolCall(toolName);
        var toolNames = {exec:'running a command',browser:'browsing the web',search:'searching the web',cron:'scheduling',tts:'generating speech',memory:'accessing memory'};
        addFlowFeedItem('⚡ ' + (toolName || 'tool') + ': ' + (toolNames[toolName] || 'using ' + toolName), '#f0c040', 'tool');
        flowStats.events++;
      } else if (type === 'tool_result') {
        var resultTool = evt.tool || 'tool';
        // Animate the tool→brain path in reverse — the result coming back.
        animateParticle('path-brain-' + resultTool, '#50c070', 600, true);
        highlightNode('node-' + resultTool, 1500);
        setTimeout(function() {
          animateParticle('path-gw-brain', '#50c070', 500, true);
        }, 500);
        var resultSnippet = evt.result ? String(evt.result).substring(0, 80).replace(/\n/g, ' ') : '';
        var resultText = '✓ ' + resultTool + (resultSnippet ? ': ' + resultSnippet : ' done');
        addFlowFeedItem(resultText, '#50c070', 'result');
        flowStats.events++;
      } else if (type === 'heartbeat') {
        addFlowFeedItem('💓 Heartbeat', '#555', 'heartbeat');
      }
    } catch(e2) {}
  };
  _flowSse.onerror = function() { setTimeout(_startFlowSse, 5000); };
}

function initFlow() {
  if (flowInitDone) return;
  flowInitDone = true;
  
  // Performance: Reduce update frequency on mobile
  var updateInterval = window.innerWidth < 768 ? 3000 : 2000;

  // Hide unconfigured channels in the flow SVG
  hideUnconfiguredChannels(document);
  
  fetch('/api/overview').then(function(r){return r.json();}).then(async function(d) {
    if (!d.model || d.model === 'unknown') {
      var fm = await resolvePrimaryModelFallback();
      if (fm && fm !== 'unknown') d.model = fm;
    }
    if (d.model) applyBrainModelToAll(d.model);
    var tok = document.getElementById('flow-tokens');
    if (tok) tok.textContent = (d.mainTokens / 1000).toFixed(0) + 'K';
    
    // Add visual hierarchy hints
    setTimeout(function() {
      enhanceArchitectureClarity();
    }, 1000);
  }).catch(function(){});

  // Populate skills in Flow diagram
  _populateFlowSkills();

  // Connect to the typed flow-events SSE (tails gateway.log + session JSONL)
  _startFlowSse();

  setInterval(updateFlowStats, updateInterval);
}

function _populateFlowSkills() {
  fetch('/api/skills').then(function(r){return r.json();}).then(function(d) {
    var skills = (d.skills || []).filter(function(s) { return s.status !== 'dead'; }).slice(0, 6);
    var container = document.getElementById('flow-skills-list');
    if (!container || !skills.length) return;
    var ns = 'http://www.w3.org/2000/svg';
    var statusColors = {healthy:'#22c55e', stuck:'#f59e0b', unused:'#6b7280', dead:'#ef4444'};
    skills.forEach(function(sk, i) {
      var y = 95 + i * 30;
      var g = document.createElementNS(ns, 'g');
      g.setAttribute('class', 'flow-node');
      var rect = document.createElementNS(ns, 'rect');
      rect.setAttribute('x', '700'); rect.setAttribute('y', String(y));
      rect.setAttribute('width', '120'); rect.setAttribute('height', '24');
      rect.setAttribute('rx', '6'); rect.setAttribute('ry', '6');
      rect.setAttribute('fill', '#7c2d12'); rect.setAttribute('stroke', '#9a3412');
      rect.setAttribute('stroke-width', '1'); rect.setAttribute('filter', 'url(#dropShadowLight)');
      var dot = document.createElementNS(ns, 'circle');
      dot.setAttribute('cx', '712'); dot.setAttribute('cy', String(y + 12));
      dot.setAttribute('r', '3'); dot.setAttribute('fill', statusColors[sk.status] || '#888');
      var text = document.createElementNS(ns, 'text');
      text.setAttribute('x', '720'); text.setAttribute('y', String(y + 16));
      text.setAttribute('style', 'font-size:10px;fill:#fed7aa;font-weight:600;');
      text.textContent = sk.name.length > 14 ? sk.name.slice(0, 12) + '\u2026' : sk.name;
      g.appendChild(rect); g.appendChild(dot); g.appendChild(text);
      container.appendChild(g);
    });
  }).catch(function(){});
}

// Add subtle animation to help users understand the flow
function enhanceArchitectureClarity() {
  // Gentle pulse on key nodes to show importance hierarchy
  var keyNodes = ['node-human', 'node-gateway', 'node-brain'];
  keyNodes.forEach(function(nodeId, index) {
    setTimeout(function() {
      var node = document.getElementById(nodeId);
      if (node) {
        node.style.animation = 'none';
        setTimeout(function() {
          node.style.animation = '';
        }, 100);
      }
    }, index * 800);
  });
  
  // Highlight the main message flow path briefly
  var paths = ['path-human-tg', 'path-tg-gw', 'path-gw-brain'];
  paths.forEach(function(pathId, index) {
    setTimeout(function() {
      var path = document.getElementById(pathId);
      if (path) {
        path.style.opacity = '0.8';
        path.style.strokeWidth = '3';
        path.style.transition = 'all 0.5s ease';
        setTimeout(function() {
          path.style.opacity = '';
          path.style.strokeWidth = '';
        }, 1500);
      }
    }, index * 200);
  });
}

function updateFlowStats() {
  var now = Date.now();
  flowStats.msgTimestamps = flowStats.msgTimestamps.filter(function(t){return now - t < 60000;});
  var el1 = document.getElementById('flow-msg-rate');
  if (el1) el1.textContent = flowStats.msgTimestamps.length;
  var el2 = document.getElementById('flow-event-count');
  if (el2) el2.textContent = flowStats.events;
  var names = Object.keys(flowStats.activeTools).filter(function(k){return flowStats.activeTools[k];});
  var el3 = document.getElementById('flow-active-tools');
  if (el3) el3.textContent = names.length > 0 ? names.join(', ') : '\u2014';
  if (flowStats.events % 15 === 0) {
    fetch('/api/overview').then(function(r){return r.json();}).then(function(d) {
      var tok = document.getElementById('flow-tokens');
      if (tok) tok.textContent = (d.mainTokens / 1000).toFixed(0) + 'K';
    }).catch(function(){});
  }
}

// Enhanced particle animation with performance optimizations and better mobile support
var particlePool = [];
var trailPool = [];
var maxParticles = window.innerWidth < 768 ? 3 : 8; // Limit particles on mobile
var trailInterval = window.innerWidth < 768 ? 8 : 4; // Fewer trails on mobile

function getPooledParticle(isTrail) {
  var pool = isTrail ? trailPool : particlePool;
  if (pool.length > 0) return pool.pop();
  var elem = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
  elem.setAttribute('r', isTrail ? '2' : '5');
  return elem;
}

function returnToPool(elem, isTrail) {
  var pool = isTrail ? trailPool : particlePool;
  elem.style.opacity = '0';
  elem.style.transform = '';
  if (pool.length < 20) pool.push(elem); // Pool size limit
  else if (elem.parentNode) elem.parentNode.removeChild(elem);
}

function animateParticle(pathId, color, duration, reverse) {
  // Animate on main Flow SVG
  _animateParticleOn(pathId, 'flow-svg', color, duration, reverse);
  // Also animate on Overview clone (ov- prefixed IDs)
  _animateParticleOn('ov-' + pathId, 'overview-flow-svg', color, duration, reverse);
}
function _animateParticleOn(pathId, svgId, color, duration, reverse) {
  var path = document.getElementById(pathId);
  if (!path) return;
  var svg = document.getElementById(svgId);
  if (!svg) return;
  
  // Skip if too many particles (performance)
  var activeParticles = svg.querySelectorAll('circle[data-particle]').length;
  if (activeParticles > maxParticles) return;
  
  var len = path.getTotalLength();
  var particle = getPooledParticle(false);
  particle.setAttribute('data-particle', 'true');
  particle.setAttribute('fill', color);
  particle.style.filter = 'drop-shadow(0 0 8px ' + color + ')';
  particle.style.opacity = '1';
  svg.appendChild(particle);
  
  var glowCls = color === '#60a0ff' ? 'glow-blue' : color === '#f0c040' ? 'glow-yellow' : color === '#50e080' ? 'glow-green' : color === '#40a0b0' ? 'glow-cyan' : color === '#c0a0ff' ? 'glow-purple' : 'glow-red';
  path.classList.add(glowCls);
  
  var startT = performance.now();
  var trailN = 0;
  var trailElements = [];
  
  function step(now) {
    var t = Math.min((now - startT) / duration, 1);
    var dist = reverse ? (1 - t) * len : t * len;
    
    try {
      var pt = path.getPointAtLength(dist);
      particle.setAttribute('cx', pt.x);
      particle.setAttribute('cy', pt.y);
    } catch(e) { 
      cleanup();
      return; 
    }
    
    // Create trail less frequently, and only if not too many already
    if (trailN++ % trailInterval === 0 && trailElements.length < 6) {
      var tr = getPooledParticle(true);
      tr.setAttribute('cx', particle.getAttribute('cx'));
      tr.setAttribute('cy', particle.getAttribute('cy'));
      tr.setAttribute('fill', color);
      tr.style.opacity = '0.6';
      tr.style.filter = 'blur(0.5px)';
      svg.insertBefore(tr, particle);
      trailElements.push(tr);
      
      // Fade trail with CSS transition instead of JS animation
      setTimeout(function() {
        tr.style.transition = 'opacity 400ms ease-out, transform 400ms ease-out';
        tr.style.opacity = '0';
        tr.style.transform = 'scale(0.3)';
        setTimeout(function() { 
          if (tr.parentNode) tr.parentNode.removeChild(tr);
          returnToPool(tr, true);
        }, 450);
      }, 50);
    }
    
    if (t < 1) {
      requestAnimationFrame(step);
    } else {
      cleanup();
    }
  }
  
  function cleanup() {
    if (particle.parentNode) particle.parentNode.removeChild(particle);
    returnToPool(particle, false);
    setTimeout(function() { 
      path.classList.remove(glowCls); 
    }, 400);
  }
  
  requestAnimationFrame(step);
}

function highlightNode(nodeId, dur) {
  var node = document.getElementById(nodeId);
  if (!node) return;
  node.classList.add('active');
  setTimeout(function() { node.classList.remove('active'); }, dur || 2000);
  // Also highlight on overview clone
  var ovNode = document.getElementById('ov-' + nodeId);
  if (ovNode) {
    ovNode.classList.add('active');
    setTimeout(function() { ovNode.classList.remove('active'); }, dur || 2000);
  }
}

// Map full OpenClaw channel names → the short key used in SVG path ids
// (path-human-<key>, path-<key>-gw). Channels not in this table fall back
// to the telegram slot path, matching the dynamic Flow channel logic.
var _CH_PATH_KEY = {
  telegram: 'tg',
  signal:   'sig',
  whatsapp: 'wa',
  tui:      'tui',
  webchat:  'webchat',
};
function _chPathKey(ch) {
  if (!ch) return 'tg';
  return _CH_PATH_KEY[ch] || _CH_PATH_KEY[ch.toLowerCase()] || 'sig';
}
function _chNodeId(ch) {
  // Prefer a dedicated node-<channel>; fall back to signal (the shared slot).
  var byName = 'node-' + (ch || 'telegram').toLowerCase();
  return document.getElementById(byName) ? byName : 'node-signal';
}

function triggerInbound(ch) {
  var key = _chPathKey(ch);
  highlightNode(_chNodeId(ch), 3000);
  animateParticle('path-human-' + key, '#c0a0ff', 550, false);
  highlightNode('node-human', 2200);
  setTimeout(function() {
    animateParticle('path-' + key + '-gw', '#60a0ff', 800, false);
    highlightNode('node-gateway', 2000);
  }, 400);
  setTimeout(function() {
    animateParticle('path-gw-brain', '#60a0ff', 600, false);
    highlightNode('node-brain', 2500);
  }, 1050);
  setTimeout(function() { triggerInfraNetwork(); }, 300);
}

function triggerToolCall(toolName) {
  var pathId = 'path-brain-' + toolName;
  animateParticle(pathId, '#f0c040', 700, false);
  highlightNode('node-' + toolName, 2500);
  setTimeout(function() {
    animateParticle(pathId, '#f0c040', 700, true);
  }, 900);
  var ind = document.getElementById('ind-' + toolName);
  if (ind) { ind.classList.add('active'); setTimeout(function() { ind.classList.remove('active'); }, 4000); }
  flowStats.activeTools[toolName] = true;
  setTimeout(function() { delete flowStats.activeTools[toolName]; }, 5000);
  if (toolName === 'exec') {
    setTimeout(function() { triggerInfraMachine(); triggerInfraRuntime(); }, 400);
  } else if (toolName === 'browser' || toolName === 'search') {
    setTimeout(function() { triggerInfraNetwork(); }, 400);
  } else if (toolName === 'memory') {
    setTimeout(function() { triggerInfraStorage(); }, 400);
  }
}

function triggerOutbound(ch) {
  var key = _chPathKey(ch);
  animateParticle('path-gw-brain', '#50e080', 600, true);
  highlightNode('node-gateway', 2000);
  setTimeout(function() {
    animateParticle('path-' + key + '-gw', '#50e080', 800, true);
    highlightNode(_chNodeId(ch), 2200);
  }, 500);
  setTimeout(function() {
    animateParticle('path-human-' + key, '#50e080', 550, true);
    highlightNode('node-human', 1800);
  }, 1200);
  setTimeout(function() { triggerInfraNetwork(); }, 200);
}

function triggerError() {
  var brain = document.getElementById('node-brain');
  if (!brain) return;
  var r = brain.querySelector('rect');
  if (r) { r.style.stroke = '#e04040'; setTimeout(function() { r.style.stroke = '#f0c040'; }, 2500); }
}

function triggerInfraNetwork() {
  animateParticle('path-gw-network', '#40a0b0', 1200, false);
  highlightNode('node-network', 2500);
}
function triggerInfraRuntime() {
  animateParticle('path-brain-runtime', '#40a0b0', 1000, false);
  highlightNode('node-runtime', 2200);
}
function triggerInfraMachine() {
  animateParticle('path-brain-machine', '#40a0b0', 1000, false);
  highlightNode('node-machine', 2200);
}
function triggerInfraStorage() {
  animateParticle('path-memory-storage', '#40a0b0', 700, false);
  highlightNode('node-storage', 2000);
}

// Live feed for Flow tab - shows recent events in plain English
var _flowFeedItems = [];
var _flowFeedMax = 200;
var _toolStreamPaused = false;
var _toolStreamFilter = '';

function toggleToolStreamPause() {
  _toolStreamPaused = !_toolStreamPaused;
  var btn = document.getElementById('tool-stream-pause-btn');
  if (btn) btn.textContent = _toolStreamPaused ? '▶ Resume' : '⏸ Pause';
}

function clearToolStream() {
  _flowFeedItems = [];
  flowStats.events = 0;
  var el = document.getElementById('flow-live-feed');
  if (el) el.innerHTML = '<div style="color:#555;">Stream cleared.</div>';
  var countEl = document.getElementById('flow-feed-count');
  if (countEl) countEl.textContent = '0 events';
}

function applyToolStreamFilter() {
  var inp = document.getElementById('tool-stream-filter');
  _toolStreamFilter = inp ? inp.value.toLowerCase().trim() : '';
  renderToolStream();
}

var _toolCategoryColors = {
  tool: '#f0c040', reply: '#50e080', inbound: '#c0a0ff', system: '#8090b0',
  error: '#e74c3c', heartbeat: '#4a7090', result: '#50c070', ai: '#a080f0'
};

function addFlowFeedItem(text, color, category) {
  if (_toolStreamPaused) return;
  var now = new Date();
  var time = now.toLocaleTimeString('en-GB', {hour:'2-digit',minute:'2-digit',second:'2-digit'});
  var cat = category || 'system';
  _flowFeedItems.push({time: time, text: text, color: color || '#888', cat: cat});
  if (_flowFeedItems.length > _flowFeedMax) _flowFeedItems.shift();
  renderToolStream();
  var countEl = document.getElementById('flow-feed-count');
  if (countEl) countEl.textContent = flowStats.events + ' events';
}

function renderToolStream() {
  var el = document.getElementById('flow-live-feed');
  if (!el) return;
  var filter = _toolStreamFilter;
  var filtered = filter
    ? _flowFeedItems.filter(function(item) { return item.text.toLowerCase().includes(filter) || item.cat.toLowerCase().includes(filter); })
    : _flowFeedItems;
  if (filtered.length === 0) {
    el.innerHTML = filter ? '<div style="color:#555;">No matching events.</div>' : '<div style="color:#555;">Waiting for activity...</div>';
    return;
  }
  var html = '';
  for (var i = filtered.length - 1; i >= Math.max(0, filtered.length - 60); i--) {
    var item = filtered[i];
    var catColor = _toolCategoryColors[item.cat] || '#666';
    html += '<div style="display:flex;gap:6px;align-items:baseline;padding:1px 0;">'
      + '<span style="color:#444;flex-shrink:0;">' + item.time + '</span>'
      + '<span style="color:' + catColor + ';font-size:9px;flex-shrink:0;text-transform:uppercase;letter-spacing:0.5px;min-width:42px;">' + item.cat + '</span>'
      + '<span style="color:' + item.color + ';word-break:break-word;">' + item.text + '</span>'
      + '</div>';
  }
  el.innerHTML = html;
}

var flowThrottles = {};
function processFlowEvent(line) {
  flowStats.events++;
  var now = Date.now();
  var msg = '', level = '';
  try {
    var obj = JSON.parse(line);
    msg = ((obj.msg || '') + ' ' + (obj.message || '') + ' ' + (obj.name || '') + ' ' + (obj['0'] || '') + ' ' + (obj['1'] || '')).toLowerCase();
    level = (obj.logLevelName || obj.level || (obj._meta && obj._meta.logLevelName) || '').toLowerCase();
  } catch(e) { msg = line.toLowerCase(); }

  if (level === 'error' || level === 'fatal') { triggerError(); return; }

  // SSE endpoint handles real events — log stream only catches outbound sends as fallback
  if (msg.includes('sendmessage ok') || msg.includes('send ok') || msg.includes('sent ok')) {
    if (now - (flowThrottles['outbound']||0) < 500) return;
    flowThrottles['outbound'] = now;
    var ch = msg.includes('imessage') ? 'sig' : msg.includes('whatsapp') ? 'wa' : 'tg';
    triggerOutbound(ch); return;
  }

  if (msg.includes('run start') && msg.includes('messagechannel')) {
    if (now - (flowThrottles['inbound']||0) < 500) return;
    flowThrottles['inbound'] = now;
    var ch = 'tg';
    if (msg.includes('signal')) ch = 'sig';
    else if (msg.includes('whatsapp')) ch = 'wa';
    triggerInbound(ch);
    addFlowFeedItem('📨 New message via ' + (ch === 'tg' ? 'Telegram' : ch === 'wa' ? 'WhatsApp' : 'Signal'), '#c0a0ff', 'inbound');
    flowStats.msgTimestamps.push(now);
    return;
  }
  if (msg.includes('inbound') || msg.includes('dispatching') || msg.includes('message received')) {
    triggerInbound('tg');
    addFlowFeedItem('📨 Incoming message received', '#c0a0ff', 'inbound');
    flowStats.msgTimestamps.push(now);
    return;
  }

  if ((msg.includes('tool start') || msg.includes('tool-call') || msg.includes('tool_use')) && !msg.includes('tool end')) {
    var toolName = '';
    var toolMatch = msg.match(/tool=(\w+)/);
    if (toolMatch) toolName = toolMatch[1].toLowerCase();
    var flowTool = 'exec';
    if (toolName === 'exec' || toolName === 'read' || toolName === 'write' || toolName === 'edit' || toolName === 'process') {
      flowTool = 'exec';
    } else if (toolName.includes('browser') || toolName === 'canvas') {
      flowTool = 'browser';
    } else if (toolName === 'web_search' || toolName === 'web_fetch') {
      flowTool = 'search';
    } else if (toolName === 'cron' || toolName === 'sessions_spawn' || toolName === 'sessions_send') {
      flowTool = 'cron';
    } else if (toolName === 'tts') {
      flowTool = 'tts';
    } else if (toolName === 'memory_search' || toolName === 'memory_get') {
      flowTool = 'memory';
    } else if (toolName === 'message') {
      if (now - (flowThrottles['outbound']||0) < 500) return;
      flowThrottles['outbound'] = now;
      triggerOutbound('tg'); return;
    }
    if (now - (flowThrottles['tool-'+flowTool]||0) < 300) return;
    flowThrottles['tool-'+flowTool] = now;
    var toolNames = {exec:'running a command',browser:'browsing the web',search:'searching the web',cron:'scheduling a task',tts:'generating speech',memory:'accessing memory'};
    addFlowFeedItem('⚡ ' + flowTool + ': ' + (toolNames[flowTool] || 'using ' + flowTool), '#f0c040', 'tool');
    triggerToolCall(flowTool); return;
  }

  var toolMap = {
    'exec': ['exec','shell','command'],
    'browser': ['browser','screenshot','snapshot'],
    'search': ['web_search','web_fetch'],
    'cron': ['cron','schedule'],
    'tts': ['tts','speech','voice'],
    'memory': ['memory_search','memory_get']
  };
  if (msg.includes('tool') || msg.includes('invoke') || msg.includes('calling')) {
    for (var t in toolMap) {
      for (var i = 0; i < toolMap[t].length; i++) {
        if (msg.includes(toolMap[t][i])) { triggerToolCall(t); return; }
      }
    }
  }

  if (msg.includes('response sent') || msg.includes('completion') || msg.includes('reply sent') || msg.includes('deliver') || (msg.includes('lane task done') && msg.includes('main'))) {
    var ch = 'tg';
    if (msg.includes('signal')) ch = 'sig';
    else if (msg.includes('whatsapp')) ch = 'wa';
    addFlowFeedItem('✉️ Reply sent via ' + (ch === 'tg' ? 'Telegram' : ch === 'wa' ? 'WhatsApp' : 'Signal'), '#50e080', 'reply');
    triggerOutbound(ch);
    return;
  }

  // Catch embedded run lifecycle events
  if (msg.includes('embedded run start') && !msg.includes('tool') && !msg.includes('prompt') && !msg.includes('agent')) {
    if (now - (flowThrottles['run-start']||0) < 1000) return;
    flowThrottles['run-start'] = now;
    var ch = 'tg';
    if (msg.includes('messagechannel=signal')) ch = 'sig';
    else if (msg.includes('messagechannel=whatsapp')) ch = 'wa';
    else if (msg.includes('messagechannel=heartbeat')) { addFlowFeedItem('💓 Heartbeat run started', '#4a7090', 'heartbeat'); fetch('/api/heartbeat-ping',{method:'POST',headers:{'Authorization':'Bearer '+(localStorage.getItem('clawmetry-token')||'')}}); return; }
    addFlowFeedItem('🧠 AI run started (' + (ch === 'tg' ? 'Telegram' : ch === 'wa' ? 'WhatsApp' : 'Signal') + ')', '#a080f0', 'ai');
    triggerInbound(ch);
    flowStats.msgTimestamps.push(now);
    return;
  }
  if (msg.includes('embedded run agent end') || msg.includes('embedded run prompt end')) {
    if (now - (flowThrottles['run-end']||0) < 1000) return;
    flowThrottles['run-end'] = now;
    addFlowFeedItem('✅ AI processing complete', '#50e080', 'ai');
    return;
  }
  if (msg.includes('session state') && msg.includes('new=processing')) {
    if (now - (flowThrottles['session-active']||0) < 2000) return;
    flowThrottles['session-active'] = now;
    addFlowFeedItem('⚡ Session activated', '#f0c040', 'system');
    return;
  }
  if (msg.includes('lane enqueue') && msg.includes('main')) {
    if (now - (flowThrottles['lane']||0) < 2000) return;
    flowThrottles['lane'] = now;
    addFlowFeedItem('📥 Task queued', '#8090b0', 'system');
    return;
  }
  if (msg.includes('lane dequeue') && msg.includes('main')) {
    if (now - (flowThrottles['lane-dq']||0) < 2000) return;
    flowThrottles['lane-dq'] = now;
    addFlowFeedItem('▶️ Task dequeued', '#607090');
    _diagPush({kind:'lane.dequeue', value:1, ts:now});
    return;
  }
  if (msg.includes('run.attempt') || (msg.includes('run attempt') && msg.includes('retry'))) {
    if (now - (flowThrottles['run-retry']||0) < 1000) return;
    flowThrottles['run-retry'] = now;
    var attemptMatch = msg.match(/attempt[=: ]+(\d+)/i);
    var attempt = attemptMatch ? parseInt(attemptMatch[1]) : 1;
    addFlowFeedItem('🔄 Run retry (attempt ' + attempt + ')', '#e09040');
    _diagPush({kind:'run.attempt', value:attempt, ts:now});
    return;
  }
  if (msg.includes('session.stuck') || (msg.includes('session') && msg.includes('stuck'))) {
    if (now - (flowThrottles['stuck']||0) < 5000) return;
    flowThrottles['stuck'] = now;
    addFlowFeedItem('⚠️ Session stuck detected', '#e04040');
    _diagPush({kind:'session.stuck', value:1, ts:now});
    _showStuckBanner();
    return;
  }
  if (msg.includes('tool end') || msg.includes('tool_end')) {
    if (now - (flowThrottles['tool-end']||0) < 300) return;
    flowThrottles['tool-end'] = now;
    addFlowFeedItem('✔️ Tool completed', '#50c070', 'result');
    return;
  }
}

// === Diagnostic event helpers ===
var _diagBuffer = [];
function _diagPush(event) {
  _diagBuffer.push(event);
  if (_diagBuffer.length > 200) _diagBuffer = _diagBuffer.slice(-200);
}

function _showStuckBanner() {
  var existing = document.getElementById('stuck-session-banner');
  if (existing) return;
  var banner = document.createElement('div');
  banner.id = 'stuck-session-banner';
  banner.style.cssText = 'position:fixed;top:60px;left:50%;transform:translateX(-50%);z-index:9999;background:#e04040;color:#fff;padding:10px 20px;border-radius:8px;font-size:13px;font-weight:600;box-shadow:0 4px 16px rgba(0,0,0,0.4);display:flex;gap:12px;align-items:center;';
  banner.innerHTML = '<span>⚠️ Session stuck detected — agent may be looping</span><button onclick="document.getElementById(\'stuck-session-banner\').remove()" style="background:rgba(255,255,255,0.2);border:none;color:#fff;padding:2px 8px;border-radius:4px;cursor:pointer;font-size:12px;">Dismiss</button>';
  document.body.appendChild(banner);
  setTimeout(function() { var b = document.getElementById('stuck-session-banner'); if (b) b.remove(); }, 30000);
}

// === Overview Split-Screen: Clone flow SVG into overview pane ===
function initOverviewFlow() {
  var srcSvg = document.getElementById('flow-svg');
  var container = document.getElementById('overview-flow-container');
  if (!srcSvg || !container) return;
  // Clone the SVG into the overview pane
  var clone = srcSvg.cloneNode(true);
  clone.id = 'overview-flow-svg';
  clone.style.width = '100%';
  clone.style.height = '100%';
  clone.style.minWidth = '0';
  // Rename defs IDs (filters, patterns, etc.) in clone to avoid duplicate-id conflicts
  var defs = clone.querySelectorAll('filter[id], pattern[id], linearGradient[id], radialGradient[id], clipPath[id], mask[id]');
  defs.forEach(function(f) {
    var oldId = f.id;
    var newId = 'ov-' + oldId;
    f.id = newId;
    // Update all url(#oldId) references in filter, fill, stroke, clip-path, mask attributes
    ['filter','fill','stroke','clip-path','mask'].forEach(function(attr) {
      clone.querySelectorAll('[' + attr + '="url(#' + oldId + ')"]').forEach(function(el) {
        el.setAttribute(attr, 'url(#' + newId + ')');
      });
    });
  });
  // Strip any .active classes captured at clone time so nodes render cleanly
  clone.querySelectorAll('.active').forEach(function(el) { el.classList.remove('active'); });
  // Rename element IDs in clone to avoid getElementById conflicts with original SVG
  clone.querySelectorAll('[id]').forEach(function(el) {
    el.id = 'ov-' + el.id;
  });
  container.innerHTML = '';
  container.appendChild(clone);
  // Hide unconfigured channels in the overview clone too
  // Clone has IDs prefixed with 'ov-', so we use a wrapper approach
  fetch('/api/channels').then(function(r){return r.json();}).then(function(d) {
    var active = d.channels || ['telegram', 'signal', 'whatsapp'];
    var channelMap = {
      'tui':         { node: 'ov-node-tui',         paths: ['ov-path-human-tg',  'ov-path-tg-gw'] },
      'telegram':    { node: 'ov-node-telegram',    paths: ['ov-path-human-tg',  'ov-path-tg-gw'] },
      'signal':      { node: 'ov-node-signal',      paths: ['ov-path-human-sig', 'ov-path-sig-gw'] },
      'whatsapp':    { node: 'ov-node-whatsapp',    paths: ['ov-path-human-wa',  'ov-path-wa-gw'] },
      'imessage':    { node: 'ov-node-imessage',    paths: ['ov-path-human-sig', 'ov-path-sig-gw'] },
      'discord':     { node: 'ov-node-discord',     paths: ['ov-path-human-sig', 'ov-path-sig-gw'] },
      'slack':       { node: 'ov-node-slack',       paths: ['ov-path-human-sig', 'ov-path-sig-gw'] },
      'irc':         { node: 'ov-node-irc',         paths: ['ov-path-human-sig', 'ov-path-sig-gw'] },
      'webchat':     { node: 'ov-node-webchat',     paths: ['ov-path-human-sig', 'ov-path-sig-gw'] },
      'googlechat':  { node: 'ov-node-googlechat',  paths: ['ov-path-human-sig', 'ov-path-sig-gw'] },
      'bluebubbles': { node: 'ov-node-bluebubbles', paths: ['ov-path-human-sig', 'ov-path-sig-gw'] },
      'msteams':     { node: 'ov-node-msteams',     paths: ['ov-path-human-sig', 'ov-path-sig-gw'] },
      'matrix':      { node: 'ov-node-matrix',      paths: ['ov-path-human-sig', 'ov-path-sig-gw'] },
      'mattermost':  { node: 'ov-node-mattermost',  paths: ['ov-path-human-sig', 'ov-path-sig-gw'] },
      'line':        { node: 'ov-node-line',        paths: ['ov-path-human-sig', 'ov-path-sig-gw'] },
      'nostr':       { node: 'ov-node-nostr',       paths: ['ov-path-human-sig', 'ov-path-sig-gw'] },
      'twitch':      { node: 'ov-node-twitch',      paths: ['ov-path-human-sig', 'ov-path-sig-gw'] },
      'feishu':      { node: 'ov-node-feishu',      paths: ['ov-path-human-sig', 'ov-path-sig-gw'] },
      'zalo':        { node: 'ov-node-zalo',        paths: ['ov-path-human-sig', 'ov-path-sig-gw'] }
    };
    var OV_SLOT_ORDER = ['tui', 'telegram', 'whatsapp', 'imessage', 'signal', 'discord', 'slack',
                         'irc', 'webchat', 'googlechat', 'bluebubbles', 'msteams', 'matrix',
                         'mattermost', 'line', 'nostr', 'twitch', 'feishu', 'zalo'];
    var visibleChannels = OV_SLOT_ORDER.filter(function(ch) { return active.indexOf(ch) !== -1; }).slice(0, 3);
    // Use the clone SVG as root for getElementById (it's already in DOM via container)
    function ovEl(id) { return document.getElementById(id); }
    // Hide ALL channel nodes first
    Object.keys(channelMap).forEach(function(ch) {
      var info = channelMap[ch];
      var node = ovEl(info.node);
      if (node) node.style.display = 'none';
    });
    ['ov-path-human-tg','ov-path-tg-gw','ov-path-human-sig','ov-path-sig-gw','ov-path-human-wa','ov-path-wa-gw'].forEach(function(pid) {
      var p = ovEl(pid);
      if (p) p.style.display = 'none';
    });
    // Show and position only active channels
    var yPositions = visibleChannels.length === 1 ? [183] : visibleChannels.length === 2 ? [145, 225] : [120, 183, 246];
    visibleChannels.forEach(function(ch, i) {
      var info = channelMap[ch];
      if (!info) return;
      var node = ovEl(info.node);
      if (!node) return;
      node.style.display = '';
      var rect = node.querySelector('rect');
      var text = node.querySelector('text');
      var targetY = yPositions[i];
      if (rect) rect.setAttribute('y', targetY - 20);
      if (text) text.setAttribute('y', targetY + 5);
      var humanPath = ovEl(info.paths[0]);
      if (humanPath) { humanPath.style.display = ''; humanPath.setAttribute('d', 'M 60 56 C 60 ' + (targetY - 30) + ', 65 ' + (targetY - 15) + ', 75 ' + (targetY - 20)); }
      var gwPath = ovEl(info.paths[1]);
      if (gwPath) { gwPath.style.display = ''; gwPath.setAttribute('d', 'M 130 ' + targetY + ' C 150 ' + targetY + ', 160 183, 180 183'); }
    });
  }).catch(function(){});
}

// === Overview Tasks Panel (right side) ===
var _ovTasksTimer = null;
window._ovExpandedSet = {};  // track which detail panels are open across refreshes

function _ovTimeLabel(agent) {
  var ms = agent.runtimeMs || 0;
  var sec = Math.floor(ms / 1000);
  var min = Math.floor(sec / 60);
  var hr = Math.floor(min / 60);
  if (agent.status === 'active') {
    if (min < 1) return 'Running (' + sec + 's)';
    if (min < 60) return 'Running (' + min + ' min)';
    return 'Running (' + hr + 'h ' + (min % 60) + 'm)';
  }
  if (sec < 60) return 'Finished ' + sec + 's ago';
  if (min < 60) return 'Finished ' + min + ' min ago';
  if (hr < 24) return 'Finished ' + hr + 'h ago';
  return 'Finished ' + Math.floor(hr / 24) + 'd ago';
}

function _ovRenderCard(agent, idx) {
  var isRealFailure = agent.status === 'stale' && agent.abortedLastRun && (agent.outputTokens || 0) === 0;
  var sc = agent.status === 'active' ? 'running' : isRealFailure ? 'failed' : 'complete';
  var taskName = cleanTaskName(agent.displayName);
  var badge = detectProjectBadge(agent.displayName);
  var timeLabel = _ovTimeLabel(agent);
  var detailId = 'ovd2-' + idx;
  var isOpen = !!(window._ovExpandedSet || {})[agent.sessionId];
  var tokTotal = (agent.inputTokens || 0) + (agent.outputTokens || 0);
  var cmdsRun = (agent.recentTools || []).length;

  var h = '';
  // Card with left color bar (via border-left on ov-task-card class)
  h += '<div class="ov-task-card ' + sc + '" style="cursor:pointer;" onclick="openTaskModal(\'' + escHtml(agent.sessionId).replace(/'/g,"\\'") + '\',\'' + escHtml(taskName).replace(/'/g,"\\'") + '\',\'' + escHtml(agent.key).replace(/'/g,"\\'") + '\')">';
  // Row 1: status dot + name + status badge
  h += '<div style="display:flex;align-items:flex-start;gap:8px;margin-bottom:6px;">';
  h += '<span class="status-dot ' + sc + '" style="margin-top:5px;"></span>';
  h += '<div style="flex:1;min-width:0;">';
  h += '<div style="font-weight:700;font-size:14px;color:var(--text-primary);line-height:1.3;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden;">' + escHtml(taskName) + '</div>';
  // Row 2: project pill + time
  h += '<div style="display:flex;align-items:center;gap:8px;margin-top:4px;flex-wrap:wrap;">';
  if (badge) {
    h += '<span style="display:inline-block;padding:1px 8px;border-radius:10px;font-size:10px;font-weight:700;background:' + badge.color + '18;color:' + badge.color + ';border:1px solid ' + badge.color + '33;">' + badge.label + '</span>';
  }
  h += '<span style="font-size:12px;color:var(--text-muted);">' + escHtml(timeLabel) + '</span>';
  h += '</div>';
  h += '</div>';
  // Status badge top-right
  h += '<span class="task-card-badge ' + sc + '" style="flex-shrink:0;">' + (sc === 'running' ? '🔄' : sc === 'failed' ? '❌' : '✅') + '</span>';
  h += '</div>';
  // Row 3: Show details toggle
  h += '<button class="ov-toggle-btn" onclick="event.stopPropagation();var d=document.getElementById(\'' + detailId + '\');var o=d.classList.toggle(\'open\');this.textContent=o?\'▼ Hide details\':\'▶ Show details\';if(o){window._ovExpandedSet=window._ovExpandedSet||{};window._ovExpandedSet[\'' + escHtml(agent.sessionId) + '\']=true;}else{delete window._ovExpandedSet[\'' + escHtml(agent.sessionId) + '\'];}">' + (isOpen ? '▼ Hide details' : '▶ Show details') + '</button>';
  // Collapsible details
  h += '<div class="ov-details' + (isOpen ? ' open' : '') + '" id="' + detailId + '">';
  h += '<div><span style="color:var(--text-muted);">Session:</span> <span style="font-family:monospace;font-size:10px;">' + escHtml(agent.sessionId) + '</span></div>';
  h += '<div><span style="color:var(--text-muted);">Key:</span> <span style="font-family:monospace;font-size:10px;">' + escHtml(agent.key) + '</span></div>';
  h += '<div><span style="color:var(--text-muted);">Model:</span> ' + escHtml(agent.model || 'unknown') + '</div>';
  if (tokTotal > 0) h += '<div><span style="color:var(--text-muted);">Tokens:</span> ' + tokTotal.toLocaleString() + ' (' + (agent.inputTokens||0).toLocaleString() + ' in / ' + (agent.outputTokens||0).toLocaleString() + ' out)</div>';
  if (cmdsRun > 0) h += '<div><span style="color:var(--text-muted);">Commands run:</span> ' + cmdsRun + '</div>';
  if (agent.recentTools && agent.recentTools.length > 0) {
    h += '<div style="margin-top:6px;"><span style="color:var(--text-muted);">Recent tools:</span></div>';
    agent.recentTools.forEach(function(t) {
      h += '<div style="font-size:10px;font-family:monospace;"><span style="color:var(--text-accent);">' + escHtml(t.name) + '</span> ' + escHtml(t.summary) + '</div>';
    });
  }
  h += '<div style="margin-top:6px;"><span style="color:var(--text-muted);">Full prompt:</span></div>';
  h += '<div style="white-space:pre-wrap;word-break:break-word;max-height:120px;overflow-y:auto;padding:6px;background:var(--bg-primary);border-radius:4px;margin-top:2px;font-size:10px;">' + escHtml(agent.displayName) + '</div>';
  h += '</div>';
  h += '</div>';
  return h;
}

async function loadOverviewTasks() {
  try {
    var data = await fetchJsonWithTimeout('/api/subagents', 4000);
    var el = document.getElementById('overview-tasks-list');
    var countBadge = document.getElementById('overview-tasks-count-badge');
    if (!el) return true;
    var agents = data.subagents || [];

    // Also load into hidden active-tasks-grid for compatibility
    loadActiveTasks();

    if (agents.length === 0) {
      if (countBadge) countBadge.textContent = '';
      el.innerHTML = '<div style="text-align:center;padding:40px 20px;color:var(--text-muted);">'
        + '<div style="font-size:32px;margin-bottom:12px;" class="tasks-empty-icon">😴</div>'
        + '<div style="font-size:14px;font-weight:600;color:var(--text-tertiary);margin-bottom:4px;">No active tasks</div>'
        + '<div style="font-size:12px;">The AI is idle.</div></div>';
      return true;
    }

    var running = [], done = [], failed = [];
    agents.forEach(function(a) {
      var isRealFailure = a.status === 'stale' && a.abortedLastRun && (a.outputTokens || 0) === 0;
      if (a.status === 'active') running.push(a);
      else if (isRealFailure) failed.push(a);
      else done.push(a);
    });
    // Filter old completed/failed (2h)
    done = done.filter(function(a) { return a.runtimeMs < 2 * 60 * 60 * 1000; });
    failed = failed.filter(function(a) { return a.runtimeMs < 2 * 60 * 60 * 1000; });

    if (countBadge) countBadge.textContent = running.length > 0 ? '(' + running.length + ' running)' : '(' + (done.length + failed.length) + ' recent)';

    var totalShown = running.length + done.length + failed.length;
    if (totalShown === 0) {
      el.innerHTML = '<div style="text-align:center;padding:40px 20px;color:var(--text-muted);">'
        + '<div style="font-size:32px;margin-bottom:12px;" class="tasks-empty-icon">😴</div>'
        + '<div style="font-size:14px;font-weight:600;color:var(--text-tertiary);margin-bottom:4px;">No active tasks</div>'
        + '<div style="font-size:12px;">The AI is idle.</div></div>';
      return true;
    }

    var html = '';
    var cardIdx = 0;
    if (running.length > 0) {
      html += '<div class="task-group-header">🔄 Running (' + running.length + ')</div>';
      running.forEach(function(a) { html += _ovRenderCard(a, cardIdx++); });
    }
    if (done.length > 0) {
      html += '<div class="task-group-header">✅ Recently Completed (' + done.length + ')</div>';
      done.forEach(function(a) { html += _ovRenderCard(a, cardIdx++); });
    }
    if (failed.length > 0) {
      html += '<div class="task-group-header">❌ Failed (' + failed.length + ')</div>';
      failed.forEach(function(a) { html += _ovRenderCard(a, cardIdx++); });
    }

    // Preserve scroll position for smooth update
    var scrollTop = el.scrollTop;
    el.innerHTML = html;
    el.scrollTop = scrollTop;
    return true;
  } catch(e) {
    return false;
  }
}

function startOverviewTasksRefresh() {
  loadOverviewTasks();
  if (_ovTasksTimer) clearInterval(_ovTasksTimer);
  _ovTasksTimer = setInterval(loadOverviewTasks, 10000);
}

// === Task Detail Modal ===
var _modalSessionId = null;
var _modalTab = 'summary';
var _modalAutoRefresh = true;
var _modalRefreshTimer = null;
var _modalEvents = [];

/* === Component Modal === */
var COMP_MAP = {
  'node-tui':         {type:'channel', name:'TUI',            icon:'⌨️', chKey:'tui'},
  'node-telegram':    {type:'channel', name:'Telegram',       icon:'📱', chKey:'telegram'},
  'node-signal':      {type:'channel', name:'Signal',         icon:'🔒', chKey:'signal'},
  'node-whatsapp':    {type:'channel', name:'WhatsApp',       icon:'📲', chKey:'whatsapp'},
  'node-imessage':    {type:'channel', name:'iMessage',       icon:'💬', chKey:'imessage'},
  'node-discord':     {type:'channel', name:'Discord',        icon:'🎮', chKey:'discord'},
  'node-slack':       {type:'channel', name:'Slack',          icon:'💼', chKey:'slack'},
  'node-irc':         {type:'channel', name:'IRC',            icon:'#️⃣', chKey:'irc'},
  'node-webchat':     {type:'channel', name:'WebChat',        icon:'🌐', chKey:'webchat'},
  'node-googlechat':  {type:'channel', name:'Google Chat',    icon:'💬', chKey:'googlechat'},
  'node-bluebubbles': {type:'channel', name:'BlueBubbles',    icon:'🍎', chKey:'bluebubbles'},
  'node-msteams':     {type:'channel', name:'MS Teams',       icon:'👔', chKey:'msteams'},
  'node-matrix':      {type:'channel', name:'Matrix',         icon:'🔢', chKey:'matrix'},
  'node-mattermost':  {type:'channel', name:'Mattermost',     icon:'⚓', chKey:'mattermost'},
  'node-line':        {type:'channel', name:'LINE',           icon:'💚', chKey:'line'},
  'node-nostr':       {type:'channel', name:'Nostr',          icon:'⚡', chKey:'nostr'},
  'node-twitch':      {type:'channel', name:'Twitch',         icon:'🎮', chKey:'twitch'},
  'node-feishu':      {type:'channel', name:'Feishu',         icon:'🌸', chKey:'feishu'},
  'node-zalo':        {type:'channel', name:'Zalo',           icon:'💬', chKey:'zalo'},
  'node-gateway': {type:'gateway', name:'Gateway', icon:'🌐'},
  'node-brain': {type:'brain', name:'AI Model', icon:'🧠'},
  'node-session': {type:'tool', name:'Sessions', icon:'📋'},
  'node-exec': {type:'tool', name:'Exec', icon:'⚡'},
  'node-browser': {type:'tool', name:'Web', icon:'🌍'},
  'node-search': {type:'tool', name:'Search', icon:'🔍'},
  'node-cron': {type:'tool', name:'Cron', icon:'⏰'},
  'node-tts': {type:'tool', name:'TTS', icon:'🔊'},
  'node-memory': {type:'tool', name:'Memory', icon:'💾'},
  'node-cost-optimizer': {type:'optimizer', name:'Cost Optimizer', icon:'💰'},
  'node-automation-advisor': {type:'advisor', name:'Automation Advisor', icon:'🧠'},
  'node-runtime': {type:'infra', name:'Runtime', icon:'⚙️'},
  'node-machine': {type:'infra', name:'Machine', icon:'🖥️'},
  'node-storage': {type:'infra', name:'Storage', icon:'💿'},
  'node-network': {type:'infra', name:'Network', icon:'🔗'},
  'node-skills': {type:'skills', name:'Skills', icon:'🧬'}
};
function initCompClickHandlers() {
  Object.keys(COMP_MAP).forEach(function(id) {
    // Bind on original flow SVG nodes
    var el = document.getElementById(id);
    if (el) {
      el.classList.add('flow-node-clickable');
      el.addEventListener('click', function(e) {
        e.stopPropagation();
        openCompModal(id);
      });
    }
    // Bind on overview clone nodes (ov- prefixed)
    var ovEl = document.getElementById('ov-' + id);
    if (ovEl) {
      ovEl.classList.add('flow-node-clickable');
      ovEl.addEventListener('click', function(e) {
        e.stopPropagation();
        openCompModal(id);
      });
    }
  });
}

function initOverviewCompClickHandlers() {
  Object.keys(COMP_MAP).forEach(function(id) {
    var ovEl = document.getElementById('ov-' + id);
    if (ovEl) {
      ovEl.classList.add('flow-node-clickable');
      ovEl.addEventListener('click', function(e) {
        e.stopPropagation();
        openCompModal(id);
      });
    }
  });
}
var _tgRefreshTimer = null;
var _imsgRefreshTimer = null;
var _discordRefreshTimer = null;
var _slackRefreshTimer = null;
var _waRefreshTimer = null;
var _sigRefreshTimer = null;
var _gcRefreshTimer = null;
var _mstRefreshTimer = null;
var _mmRefreshTimer = null;
var _tgOffset = 0;
var _tgAllMessages = [];

function isCompModalActive(nodeId) {
  var overlay = document.getElementById('comp-modal-overlay');
  return !!(overlay && overlay.classList.contains('open') && window._currentComponentId === nodeId);
}

function openCompModal(nodeId) {
  var c = COMP_MAP[nodeId];
  if (!c) return;
  
  // Clear ALL existing refresh timers to prevent stale data overwriting new modal
  if (_tgRefreshTimer) { clearInterval(_tgRefreshTimer); _tgRefreshTimer = null; }
  if (_imsgRefreshTimer) { clearInterval(_imsgRefreshTimer); _imsgRefreshTimer = null; }
  if (_waRefreshTimer) { clearInterval(_waRefreshTimer); _waRefreshTimer = null; }
  if (_sigRefreshTimer) { clearInterval(_sigRefreshTimer); _sigRefreshTimer = null; }
  if (_gcRefreshTimer) { clearInterval(_gcRefreshTimer); _gcRefreshTimer = null; }
  if (_mstRefreshTimer) { clearInterval(_mstRefreshTimer); _mstRefreshTimer = null; }
  if (_mmRefreshTimer) { clearInterval(_mmRefreshTimer); _mmRefreshTimer = null; }
  if (_gwRefreshTimer) { clearInterval(_gwRefreshTimer); _gwRefreshTimer = null; }
  if (_brainRefreshTimer) { clearInterval(_brainRefreshTimer); _brainRefreshTimer = null; }
  if (_toolRefreshTimer) { clearInterval(_toolRefreshTimer); _toolRefreshTimer = null; }
  if (_costOptimizerRefreshTimer) { clearInterval(_costOptimizerRefreshTimer); _costOptimizerRefreshTimer = null; }
  if (window._genericChannelTimer) { clearInterval(window._genericChannelTimer); window._genericChannelTimer = null; }
  if (window._tuiRefreshTimer) { clearInterval(window._tuiRefreshTimer); window._tuiRefreshTimer = null; }
  if (_webchatRefreshTimer) { clearInterval(_webchatRefreshTimer); _webchatRefreshTimer = null; }
  if (_ircRefreshTimer) { clearInterval(_ircRefreshTimer); _ircRefreshTimer = null; }
  if (_bbRefreshTimer) { clearInterval(_bbRefreshTimer); _bbRefreshTimer = null; }
  
  // Track current component for time travel
  window._currentComponentId = nodeId;
  
  // Channel modals: surface a status badge in the title so users can tell
  // "configured & quiet" from "never set up" (otherwise both render as 0).
  var titleSuffix = '';
  if (c.type === 'channel' && c.chKey) {
    if (window._cmConfiguredChannels) {
      titleSuffix = window._cmConfiguredChannels.has(c.chKey)
        ? ' <span style="font-size:13px;color:#22c55e;font-weight:500;margin-left:8px;">🟢 Connected</span>'
        : ' <span style="font-size:13px;color:#94a3b8;font-weight:500;margin-left:8px;">⚪ Not configured</span>';
    } else {
      // Fetch + cache, update the title async
      fetch('/api/channels').then(function(r){return r.json();}).then(function(d){
        window._cmConfiguredChannels = new Set(d.channels || []);
        var t2 = document.getElementById('comp-modal-title');
        if (!t2 || window._currentComponentId !== nodeId) return;
        var conn = window._cmConfiguredChannels.has(c.chKey);
        t2.innerHTML = (c.icon || '') + ' ' + escapeHtml(c.name) +
          (conn ? ' <span style="font-size:13px;color:#22c55e;font-weight:500;margin-left:8px;">🟢 Connected</span>'
                : ' <span style="font-size:13px;color:#94a3b8;font-weight:500;margin-left:8px;">⚪ Not configured</span>');
      }).catch(function(){});
    }
  }
  document.getElementById('comp-modal-title').innerHTML = (c.icon || '') + ' ' + escapeHtml(c.name) + titleSuffix;

  // Reset time travel state when opening new component
  _timeTravelMode = false;
  _currentTimeContext = null;
  document.getElementById('time-travel-toggle').classList.remove('active');
  document.getElementById('time-travel-bar').classList.remove('active');

  if (nodeId === 'node-tui') {
    document.getElementById('comp-modal-body').innerHTML = '<div style="text-align:center;padding:40px;"><div class="pulse"></div> Loading TUI messages...</div>';
    document.getElementById('comp-modal-overlay').classList.add('open');
    loadTuiMessages(false);
    window._tuiRefreshTimer = setInterval(function() { loadTuiMessages(true); }, 10000);
    return;
  }

  if (nodeId === 'node-telegram') {
    _tgOffset = 0;
    _tgAllMessages = [];
    document.getElementById('comp-modal-body').innerHTML = '<div style="text-align:center;padding:40px;"><div class="pulse"></div> Loading messages...</div>';
    document.getElementById('comp-modal-overlay').classList.add('open');
    loadTelegramMessages(false);
    _tgRefreshTimer = setInterval(function() { loadTelegramMessages(true); }, 10000);
    return;
  }

  if (nodeId === 'node-imessage') {
    document.getElementById('comp-modal-body').innerHTML = '<div style="text-align:center;padding:40px;"><div class="pulse"></div> Loading iMessages...</div>';
    document.getElementById('comp-modal-overlay').classList.add('open');
    loadIMessageMessages(false);
    _imsgRefreshTimer = setInterval(function() { loadIMessageMessages(true); }, 10000);
    return;
  }

  if (nodeId === 'node-whatsapp') {
    document.getElementById('comp-modal-body').innerHTML = '<div style="text-align:center;padding:40px;"><div class="pulse"></div> Loading WhatsApp messages...</div>';
    document.getElementById('comp-modal-overlay').classList.add('open');
    loadWhatsAppMessages(false);
    _waRefreshTimer = setInterval(function() { loadWhatsAppMessages(true); }, 10000);
    return;
  }

  if (nodeId === 'node-signal') {
    document.getElementById('comp-modal-body').innerHTML = '<div style="text-align:center;padding:40px;"><div class="pulse"></div> Loading Signal messages...</div>';
    document.getElementById('comp-modal-overlay').classList.add('open');
    loadSignalMessages(false);
    _sigRefreshTimer = setInterval(function() { loadSignalMessages(true); }, 10000);
    return;
  }

  if (nodeId === 'node-discord') {
    document.getElementById('comp-modal-body').innerHTML = '<div style="text-align:center;padding:40px;"><div class="pulse"></div> Loading Discord messages...</div>';
    document.getElementById('comp-modal-overlay').classList.add('open');
    loadDiscordMessages(false);
    _discordRefreshTimer = setInterval(function() { loadDiscordMessages(true); }, 10000);
    return;
  }

  if (nodeId === 'node-slack') {
    document.getElementById('comp-modal-body').innerHTML = '<div style="text-align:center;padding:40px;"><div class="pulse"></div> Loading Slack messages...</div>';
    document.getElementById('comp-modal-overlay').classList.add('open');
    loadSlackMessages(false);
    _slackRefreshTimer = setInterval(function() { loadSlackMessages(true); }, 10000);
    return;
  }

  if (nodeId === 'node-googlechat') {
    document.getElementById('comp-modal-body').innerHTML = '<div style="text-align:center;padding:40px;"><div class="pulse"></div> Loading Google Chat messages...</div>';
    document.getElementById('comp-modal-overlay').classList.add('open');
    loadGoogleChatMessages(false);
    _gcRefreshTimer = setInterval(function() { loadGoogleChatMessages(true); }, 10000);
    return;
  }

  if (nodeId === 'node-msteams') {
    document.getElementById('comp-modal-body').innerHTML = '<div style="text-align:center;padding:40px;"><div class="pulse"></div> Loading MS Teams messages...</div>';
    document.getElementById('comp-modal-overlay').classList.add('open');
    loadMSTeamsMessages(false);
    _mstRefreshTimer = setInterval(function() { loadMSTeamsMessages(true); }, 10000);
    return;
  }

  if (nodeId === 'node-mattermost') {
    document.getElementById('comp-modal-body').innerHTML = '<div style="text-align:center;padding:40px;"><div class="pulse"></div> Loading Mattermost messages...</div>';
    document.getElementById('comp-modal-overlay').classList.add('open');
    loadMattermostMessages(false);
    _mmRefreshTimer = setInterval(function() { loadMattermostMessages(true); }, 10000);
    return;
  }

  if (nodeId === 'node-webchat') {
    document.getElementById('comp-modal-body').innerHTML = '<div style="text-align:center;padding:40px;"><div class="pulse"></div> Loading WebChat...</div>';
    document.getElementById('comp-modal-overlay').classList.add('open');
    loadWebchatMessages(false);
    _webchatRefreshTimer = setInterval(function() { loadWebchatMessages(true); }, 12000);
    return;
  }

  if (nodeId === 'node-irc') {
    document.getElementById('comp-modal-body').innerHTML = '<div class="irc-loading">*** Connecting to IRC log... ***</div>';
    document.getElementById('comp-modal-overlay').classList.add('open');
    loadIRCMessages(false);
    _ircRefreshTimer = setInterval(function() { loadIRCMessages(true); }, 15000);
    return;
  }

  if (nodeId === 'node-bluebubbles') {
    document.getElementById('comp-modal-body').innerHTML = '<div style="text-align:center;padding:40px;"><div class="pulse"></div> Loading BlueBubbles...</div>';
    document.getElementById('comp-modal-overlay').classList.add('open');
    loadBlueBubblesMessages(false);
    _bbRefreshTimer = setInterval(function() { loadBlueBubblesMessages(true); }, 12000);
    return;
  }

  // Generic channel handler for all other channel types
  // TUI has a dedicated branch below (below the telegram branch) with a
  // proper chat-bubble renderer + <think>-block stripping.
  var GENERIC_CHANNELS = ['node-googlechat',
    'node-msteams','node-matrix','node-mattermost','node-line',
    'node-nostr','node-twitch','node-feishu','node-zalo'];
  if (GENERIC_CHANNELS.indexOf(nodeId) !== -1 && c.chKey) {
    document.getElementById('comp-modal-body').innerHTML = '<div style="text-align:center;padding:40px;"><div class="pulse"></div> Loading ' + c.name + '...</div>';
    document.getElementById('comp-modal-overlay').classList.add('open');
    loadGenericChannelData(nodeId, c.chKey, c, false);
    window._genericChannelTimer = setInterval(function() { loadGenericChannelData(nodeId, c.chKey, c, true); }, 15000);
    return;
  }

  if (nodeId === 'node-gateway') {
    document.getElementById('comp-modal-body').innerHTML = '<div style="text-align:center;padding:40px;"><div class="pulse"></div> Loading gateway data...</div>';
    document.getElementById('comp-modal-overlay').classList.add('open');
    loadGatewayData(false);
    _gwRefreshTimer = setInterval(function() { loadGatewayData(true); }, 10000);
    return;
  }

  if (nodeId === 'node-brain') {
    document.getElementById('comp-modal-body').innerHTML = '<div style="text-align:center;padding:40px;"><div class="pulse"></div> Loading AI brain data...</div>';
    document.getElementById('comp-modal-overlay').classList.add('open');
    _brainPage = 0;
    loadBrainData(false);
    _brainRefreshTimer = setInterval(function() { loadBrainData(true); }, 10000);
    return;
  }

  if (nodeId === 'node-cost-optimizer') {
    document.getElementById('comp-modal-body').innerHTML = '<div style="text-align:center;padding:40px;"><div class="pulse"></div> Analyzing costs...</div>';
    document.getElementById('comp-modal-overlay').classList.add('open');
    loadCostOptimizerData(false);
    _costOptimizerRefreshTimer = setInterval(function() { loadCostOptimizerData(true); }, 15000);
    return;
  }

  if (c.type === 'tool') {
    var toolKey = nodeId.replace('node-', '');
    // Show cached data instantly if available, otherwise show loading spinner
    if (!_toolDataCache[toolKey]) {
      document.getElementById('comp-modal-body').innerHTML = '<div style="text-align:center;padding:40px;"><div class="pulse"></div> Loading ' + c.name + ' data...</div>';
    }
    document.getElementById('comp-modal-overlay').classList.add('open');
    // If cached, render immediately then refresh in background
    if (_toolDataCache[toolKey]) {
      loadToolData(toolKey, c, false);
    } else {
      loadToolData(toolKey, c, false);
    }
    _toolRefreshTimer = setInterval(function() { loadToolData(toolKey, c, true); }, 10000);
    return;
  }

  // Skills modal — was a legend label only; now a proper clickable node
  // that surfaces per-skill cost/usage attribution from /api/skill-attribution
  // (backend already exists at routes/usage.py:813+).
  if (nodeId === 'node-skills') {
    var sBody = document.getElementById('comp-modal-body');
    sBody.innerHTML = '<div style="text-align:center;padding:40px;"><div class="pulse"></div> Loading skills…</div>';
    document.getElementById('comp-modal-overlay').classList.add('open');
    fetch('/api/skill-attribution').then(function(r){return r.json();}).then(function(data) {
      if (!isCompModalActive('node-skills')) return;
      var skills = data.skills || [];
      var totalCost = data.total_cost || 0;
      var html = '<div style="text-align:center;margin-bottom:16px;font-size:36px;">🧬</div>';
      html += '<div style="display:grid;grid-template-columns:repeat(2,1fr);gap:10px;margin-bottom:16px;">';
      html += '<div style="background:var(--bg-secondary);border-radius:10px;padding:12px;text-align:center;"><div style="font-size:24px;font-weight:700;color:var(--text-primary);">' + skills.length + '</div><div style="font-size:10px;color:var(--text-muted);text-transform:uppercase;">Skills detected</div></div>';
      html += '<div style="background:var(--bg-secondary);border-radius:10px;padding:12px;text-align:center;"><div style="font-size:24px;font-weight:700;color:var(--text-primary);">$' + (typeof totalCost === 'number' ? totalCost.toFixed(2) : totalCost) + '</div><div style="font-size:10px;color:var(--text-muted);text-transform:uppercase;">Total Cost (Month)</div></div>';
      html += '</div>';
      if (skills.length === 0) {
        html += '<div style="text-align:center;padding:30px 20px;color:var(--text-muted);">';
        html += '<div style="font-size:14px;font-weight:600;margin-bottom:8px;">No skills detected yet</div>';
        html += '<div style="font-size:12px;">' + escapeHtml(data.note || 'Skills are detected from /skills/ paths in tool-call details. Once your agent invokes a skill, it will appear here with cost attribution.') + '</div>';
        html += '</div>';
      } else {
        html += '<div style="font-size:12px;font-weight:600;color:var(--text-muted);text-transform:uppercase;letter-spacing:1px;margin-bottom:8px;">Top Skills by Cost</div>';
        html += '<div style="display:flex;flex-direction:column;gap:6px;max-height:55vh;overflow-y:auto;">';
        skills.slice(0, 20).forEach(function(s) {
          html += '<div style="padding:10px 12px;background:var(--bg-secondary);border-radius:8px;border:1px solid var(--border-secondary);">';
          html += '<div style="display:flex;justify-content:space-between;align-items:center;">';
          html += '<span style="font-weight:600;font-size:13px;color:var(--text-primary);">🧬 ' + escapeHtml(s.name) + '</span>';
          html += '<span style="font-size:13px;font-weight:700;color:#22c55e;">$' + (typeof s.total_cost === 'number' ? s.total_cost.toFixed(4) : s.total_cost) + '</span>';
          html += '</div>';
          var meta = [];
          if (s.invocations) meta.push(s.invocations + ' invocation' + (s.invocations === 1 ? '' : 's'));
          if (s.avg_cost) meta.push('avg $' + Number(s.avg_cost).toFixed(4));
          if (s.last_used) {
            try { meta.push('last used ' + _timeAgo(s.last_used)); } catch (e) {}
          }
          if (meta.length) html += '<div style="font-size:11px;color:var(--text-muted);margin-top:4px;">' + escapeHtml(meta.join(' · ')) + '</div>';
          if (s.clawhub_url) {
            html += '<div style="margin-top:6px;"><a href="' + escapeHtml(s.clawhub_url) + '" target="_blank" style="font-size:10px;color:var(--text-link,#60a5fa);text-decoration:none;">🔗 View on ClawHub</a></div>';
          }
          html += '</div>';
        });
        html += '</div>';
      }
      // Only show the trailing note when we DO have skills — empty-state
      // already renders the note inline above. Otherwise we'd show it twice.
      if (data.note && skills.length > 0) {
        html += '<div style="margin-top:12px;font-size:10px;color:var(--text-muted);font-style:italic;text-align:center;">' + escapeHtml(data.note) + '</div>';
      }
      sBody.innerHTML = html;
      document.getElementById('comp-modal-footer').textContent = 'Auto-refreshing - Last updated: ' + new Date().toLocaleTimeString() + ' - ' + skills.length + ' skills';
    }).catch(function(e) {
      if (!isCompModalActive('node-skills')) return;
      sBody.innerHTML = '<div style="padding:20px;color:var(--text-error);">Failed to load skills: ' + escapeHtml(e.message) + '</div>';
    });
    return;
  }

  // Hook the existing Automation Advisor live view (backend already exists at
  // /api/automation-analysis); was falling through to the "Live view coming
  // soon" stub previously.
  if (nodeId === 'node-automation-advisor') {
    document.getElementById('comp-modal-body').innerHTML = '<div style="text-align:center;padding:40px;"><div class="pulse"></div> Analyzing your patterns...</div>';
    document.getElementById('comp-modal-overlay').classList.add('open');
    if (typeof loadAutomationAdvisorDataWithTime === 'function') {
      try { loadAutomationAdvisorDataWithTime(); } catch (e) {
        document.getElementById('comp-modal-body').innerHTML = '<div style="padding:20px;color:var(--text-error);">Failed to load: ' + e.message + '</div>';
      }
    }
    return;
  }

  // Same items-shape modal fits Storage and Network too (both have real
  // backend endpoints now: api_component_storage, api_component_network).
  // Replaces the "Live view coming soon" stub.
  if (nodeId === 'node-runtime' || nodeId === 'node-machine' ||
      nodeId === 'node-storage' || nodeId === 'node-network') {
    document.getElementById('comp-modal-body').innerHTML = '<div style="text-align:center;padding:40px;"><div class="pulse"></div> Loading ' + c.name + ' info...</div>';
    document.getElementById('comp-modal-overlay').classList.add('open');
    fetch('/api/component/' + nodeId.replace('node-', '')).then(function(r){return r.json();}).then(function(data) {
      if (!isCompModalActive(nodeId)) return;
      var body = document.getElementById('comp-modal-body');
      var html = '<div style="text-align:center;margin-bottom:16px;font-size:36px;">' + c.icon + '</div>';
      var items = data.items || [];
      html += '<div style="display:flex;flex-direction:column;gap:1px;">';
      items.forEach(function(item) {
        var valColor = item.status === 'warning' ? 'var(--text-warning)' : item.status === 'critical' ? 'var(--text-error)' : 'var(--text-primary)';
        html += '<div class="stat-row"><span class="stat-label">' + escapeHtml(item.label) + '</span><span class="stat-val" style="color:' + valColor + ';">' + escapeHtml(item.value) + '</span></div>';
      });
      html += '</div>';
      body.innerHTML = html;
      document.getElementById('comp-modal-footer').textContent = 'Last updated: ' + new Date().toLocaleTimeString();
    }).catch(function(e) {
      if (!isCompModalActive(nodeId)) return;
      document.getElementById('comp-modal-body').innerHTML = '<div style="text-align:center;padding:20px;color:var(--text-error);">Failed to load: ' + e.message + '</div>';
    });
    return;
  }

  document.getElementById('comp-modal-body').innerHTML = '<div style="text-align:center;padding:20px;"><div style="font-size:48px;margin-bottom:16px;">' + c.icon + '</div><div style="font-size:16px;font-weight:600;margin-bottom:8px;">' + c.name + '</div><div style="color:var(--text-muted);">Live view coming soon</div><div style="margin-top:8px;font-size:12px;color:var(--text-muted);text-transform:uppercase;">' + c.type + '</div></div>';
  document.getElementById('comp-modal-footer').textContent = 'Last updated: ' + new Date().toLocaleTimeString();
  document.getElementById('comp-modal-overlay').classList.add('open');
}

function loadTelegramMessages(isRefresh) {
  var expectedNodeId = 'node-telegram';
  var url = '/api/channel/telegram?limit=50&offset=0';
  fetch(url).then(function(r) { return r.json(); }).then(function(data) {
    if (!isCompModalActive(expectedNodeId)) return;
    var msgs = data.messages || [];
    var body = document.getElementById('comp-modal-body');
    var html = '<div class="tg-stats"><span class="in">📥 ' + (data.todayIn || 0) + ' incoming</span><span class="out">📤 ' + (data.todayOut || 0) + ' outgoing</span><span style="margin-left:auto;color:var(--text-muted);font-size:11px;">Today</span></div>';
    html += '<div class="tg-chat">';
    if (msgs.length === 0) {
      html += '<div style="text-align:center;padding:20px;color:var(--text-muted);">No messages found</div>';
    }
    msgs.forEach(function(m) {
      var dir = m.direction === 'in' ? 'in' : 'out';
      var ts = m.timestamp ? new Date(m.timestamp).toLocaleTimeString([], {hour:'2-digit',minute:'2-digit'}) : '';
      var date = m.timestamp ? new Date(m.timestamp).toLocaleDateString([], {month:'short',day:'numeric'}) : '';
      var text = m.text || (m.direction === 'in' ? '(message received)' : '(reply sent)');
      html += '<div class="tg-bubble ' + dir + '">';
      html += '<div class="tg-sender">' + escapeHtml(m.sender || (dir === 'in' ? 'User' : 'Clawd')) + '</div>';
      html += '<div class="tg-text md-rendered">' + renderMarkdown(text) + '</div>';
      html += '<div class="tg-time">' + date + ' ' + ts + '</div>';
      html += '</div>';
    });
    if (data.total > msgs.length) {
      html += '<div class="tg-load-more"><button onclick="loadMoreTelegram()">Load more (' + (data.total - msgs.length) + ' remaining)</button></div>';
    }
    html += '</div>';
    body.innerHTML = html;
    document.getElementById('comp-modal-footer').textContent = 'Last updated: ' + new Date().toLocaleTimeString() + ' - ' + data.total + ' total messages';
  }).catch(function(e) {
    if (!isCompModalActive(expectedNodeId)) return;
    if (!isRefresh) {
      document.getElementById('comp-modal-body').innerHTML = '<div style="text-align:center;padding:20px;color:var(--text-error);">Failed to load messages</div>';
    }
  });
}

function loadTuiMessages(isRefresh) {
  var expectedNodeId = 'node-tui';
  fetch('/api/channel/tui?limit=50').then(function(r) { return r.json(); }).then(function(data) {
    if (!isCompModalActive(expectedNodeId)) return;
    var msgs = data.messages || [];
    var body = document.getElementById('comp-modal-body');

    // Scrub OpenClaw-specific junk from the raw transcript text:
    //   `<think>...</think>` reasoning blocks (hidden by default)
    //   `[Wed 2026-04-15 22:49 GMT+2] ` timestamp prefix (duplicates the bubble timestamp)
    //   `[[reply_to_current]]` directive markers
    function cleanTui(text, dir) {
      if (!text) return '';
      text = String(text);
      // Extract and hide thinking blocks; keep final text
      text = text.replace(/<think>[\s\S]*?<\/think>/gi, '').trim();
      // Strip leading channel timestamp `[Wed 2026-04-15 22:49 GMT+2]`
      text = text.replace(/^\[[A-Za-z]{3}\s+\d{4}-\d{2}-\d{2}\s+\d{1,2}:\d{2}\s+[A-Z]{2,5}[+-]?\d*\]\s*/, '');
      // Strip assistant directive tokens
      text = text.replace(/\[\[reply_to_current\]\]\s*/g, '');
      return text.trim();
    }

    var html = '<div class="tg-stats">' +
               '<span class="in">📥 ' + (data.todayIn || 0) + ' incoming</span>' +
               '<span class="out">📤 ' + (data.todayOut || 0) + ' outgoing</span>' +
               '<span style="margin-left:auto;color:var(--text-muted);font-size:11px;">' +
               (data.status === 'connected' ? '⌨️ Connected' : '') + '</span>' +
               '</div>';
    html += '<div class="tg-chat">';
    if (msgs.length === 0) {
      html += '<div style="text-align:center;padding:24px;color:var(--text-muted);">' +
              '<div style="font-size:32px;margin-bottom:8px;">⌨️</div>' +
              '<div>No TUI messages yet.</div>' +
              '<div style="font-size:11px;margin-top:4px;">Type in the OpenClaw terminal to see messages here.</div>' +
              '</div>';
    }
    // Render oldest → newest inside the scroll region (scrolled to bottom after)
    msgs.slice().reverse().forEach(function(m) {
      var dir = m.direction === 'in' ? 'in' : 'out';
      var ts = '', date = '';
      try {
        var d = new Date(m.timestamp);
        if (!isNaN(d.getTime())) {
          ts = d.toLocaleTimeString([], {hour:'2-digit',minute:'2-digit'});
          date = d.toLocaleDateString([], {month:'short',day:'numeric'});
        }
      } catch(e) {}
      var text = cleanTui(m.text, dir) || (dir === 'in' ? '(message received)' : '(reply sent)');
      html += '<div class="tg-bubble ' + dir + '">';
      html += '<div class="tg-sender">' + escapeHtml(m.sender || (dir === 'in' ? 'User' : 'Clawd')) + '</div>';
      html += '<div class="tg-text md-rendered">' + renderMarkdown(text) + '</div>';
      html += '<div class="tg-time">' + (date ? date + ' ' : '') + ts + '</div>';
      html += '</div>';
    });
    html += '</div>';
    body.innerHTML = html;
    var scroll = body.querySelector('.tg-chat');
    if (scroll) scroll.scrollTop = scroll.scrollHeight;
    var f = document.getElementById('comp-modal-footer');
    if (f) f.textContent = 'Last updated: ' + new Date().toLocaleTimeString() +
      ' - ' + (data.total || msgs.length) + ' total TUI messages';
  }).catch(function() {
    if (!isCompModalActive(expectedNodeId)) return;
    if (!isRefresh) {
      document.getElementById('comp-modal-body').innerHTML =
        '<div style="text-align:center;padding:20px;color:var(--text-error);">Failed to load TUI messages</div>';
    }
  });
}

function loadMoreTelegram() {
  // Simple: just increase limit
  fetch('/api/channel/telegram?limit=200&offset=0').then(function(r) { return r.json(); }).then(function(data) {
    if (!isCompModalActive('node-telegram')) return;
    // Re-render with all data
    var msgs = data.messages || [];
    var body = document.getElementById('comp-modal-body');
    var html = '<div class="tg-stats"><span class="in">📥 ' + (data.todayIn || 0) + ' incoming</span><span class="out">📤 ' + (data.todayOut || 0) + ' outgoing</span><span style="margin-left:auto;color:var(--text-muted);font-size:11px;">Today</span></div>';
    html += '<div class="tg-chat">';
    msgs.forEach(function(m) {
      var dir = m.direction === 'in' ? 'in' : 'out';
      var ts = m.timestamp ? new Date(m.timestamp).toLocaleTimeString([], {hour:'2-digit',minute:'2-digit'}) : '';
      var date = m.timestamp ? new Date(m.timestamp).toLocaleDateString([], {month:'short',day:'numeric'}) : '';
      var text = m.text || (m.direction === 'in' ? '(message received)' : '(reply sent)');
      html += '<div class="tg-bubble ' + dir + '">';
      html += '<div class="tg-sender">' + escapeHtml(m.sender || (dir === 'in' ? 'User' : 'Clawd')) + '</div>';
      html += '<div class="tg-text md-rendered">' + renderMarkdown(text) + '</div>';
      html += '<div class="tg-time">' + date + ' ' + ts + '</div>';
      html += '</div>';
    });
    html += '</div>';
    body.innerHTML = html;
    document.getElementById('comp-modal-footer').textContent = 'Last updated: ' + new Date().toLocaleTimeString() + ' - ' + data.total + ' total messages';
  });
}

function loadIMessageMessages(isRefresh) {
  var expectedNodeId = 'node-imessage';
  var url = '/api/channel/imessage?limit=50';
  fetch(url).then(function(r) { return r.json(); }).then(function(data) {
    if (!isCompModalActive(expectedNodeId)) return;
    var msgs = data.messages || [];
    var body = document.getElementById('comp-modal-body');
    var html = '<div class="imsg-stats"><span class="in">📥 ' + (data.todayIn || 0) + ' incoming</span><span class="out">📤 ' + (data.todayOut || 0) + ' outgoing</span><span style="margin-left:auto;color:var(--text-muted);font-size:11px;">Today</span></div>';
    html += '<div class="imsg-chat">';
    if (msgs.length === 0) {
      html += '<div style="text-align:center;padding:20px;color:var(--text-muted);">No messages found</div>';
    }
    msgs.forEach(function(m) {
      var dir = m.direction === 'in' ? 'in' : 'out';
      var ts = m.timestamp ? new Date(m.timestamp).toLocaleTimeString([], {hour:'2-digit',minute:'2-digit'}) : '';
      var date = m.timestamp ? new Date(m.timestamp).toLocaleDateString([], {month:'short',day:'numeric'}) : '';
      var text = m.text || (m.direction === 'in' ? '(message received)' : '(reply sent)');
      html += '<div class="imsg-bubble ' + dir + '">';
      html += '<div class="imsg-sender">' + escapeHtml(m.sender || (dir === 'in' ? 'Contact' : 'Me')) + '</div>';
      html += '<div class="imsg-text md-rendered">' + renderMarkdown(text) + '</div>';
      html += '<div class="imsg-time">' + date + ' ' + ts + '</div>';
      html += '</div>';
    });
    html += '</div>';
    body.innerHTML = html;
    document.getElementById('comp-modal-footer').textContent = 'Last updated: ' + new Date().toLocaleTimeString() + ' - ' + (data.total || msgs.length) + ' total messages';
  }).catch(function(e) {
    if (!isCompModalActive(expectedNodeId)) return;
    if (!isRefresh) {
      document.getElementById('comp-modal-body').innerHTML = '<div style="text-align:center;padding:20px;color:var(--text-error);">Failed to load iMessages: ' + escapeHtml(e.message) + '</div>';
    }
  });
}

function loadWhatsAppMessages(isRefresh) {
  var expectedNodeId = 'node-whatsapp';
  var url = '/api/channel/whatsapp?limit=50';
  fetch(url).then(function(r) { return r.json(); }).then(function(data) {
    if (!isCompModalActive(expectedNodeId)) return;
    var msgs = data.messages || [];
    var body = document.getElementById('comp-modal-body');
    var html = '<div class="wa-stats"><span class="in">📥 ' + (data.todayIn || 0) + ' incoming</span><span class="out">📤 ' + (data.todayOut || 0) + ' outgoing</span><span style="margin-left:auto;color:var(--text-muted);font-size:11px;">Today</span></div>';
    html += '<div class="wa-chat">';
    if (msgs.length === 0) {
      html += '<div style="text-align:center;padding:20px;color:var(--text-muted);">No WhatsApp messages found</div>';
    }
    msgs.forEach(function(m) {
      var dir = m.direction === 'in' ? 'in' : 'out';
      var ts = m.timestamp ? new Date(m.timestamp).toLocaleTimeString([], {hour:'2-digit',minute:'2-digit'}) : '';
      var date = m.timestamp ? new Date(m.timestamp).toLocaleDateString([], {month:'short',day:'numeric'}) : '';
      var text = m.text || (m.direction === 'in' ? '(message received)' : '(reply sent)');
      html += '<div class="wa-bubble ' + dir + '">';
      html += '<div class="wa-sender">' + escapeHtml(m.sender || (dir === 'in' ? 'User' : 'Clawd')) + '</div>';
      html += '<div class="wa-text md-rendered">' + renderMarkdown(text) + '</div>';
      html += '<div class="wa-time">' + date + ' ' + ts + '</div>';
      html += '</div>';
    });
    html += '</div>';
    body.innerHTML = html;
    document.getElementById('comp-modal-footer').textContent = 'Last updated: ' + new Date().toLocaleTimeString() + ' - ' + (data.total || msgs.length) + ' total messages';
  }).catch(function(e) {
    if (!isCompModalActive(expectedNodeId)) return;
    if (!isRefresh) {
      document.getElementById('comp-modal-body').innerHTML = '<div style="text-align:center;padding:20px;color:var(--text-error);">Failed to load WhatsApp messages</div>';
    }
  });
}

function loadSignalMessages(isRefresh) {
  var expectedNodeId = 'node-signal';
  var url = '/api/channel/signal?limit=50';
  fetch(url).then(function(r) { return r.json(); }).then(function(data) {
    if (!isCompModalActive(expectedNodeId)) return;
    var msgs = data.messages || [];
    var body = document.getElementById('comp-modal-body');
    var html = '<div class="sig-stats"><span class="in">📥 ' + (data.todayIn || 0) + ' incoming</span><span class="out">📤 ' + (data.todayOut || 0) + ' outgoing</span><span style="margin-left:auto;color:var(--text-muted);font-size:11px;">Today</span></div>';
    html += '<div class="sig-chat">';
    if (msgs.length === 0) {
      html += '<div style="text-align:center;padding:20px;color:var(--text-muted);">No Signal messages found</div>';
    }
    msgs.forEach(function(m) {
      var dir = m.direction === 'in' ? 'in' : 'out';
      var ts = m.timestamp ? new Date(m.timestamp).toLocaleTimeString([], {hour:'2-digit',minute:'2-digit'}) : '';
      var date = m.timestamp ? new Date(m.timestamp).toLocaleDateString([], {month:'short',day:'numeric'}) : '';
      var text = m.text || (m.direction === 'in' ? '(message received)' : '(reply sent)');
      html += '<div class="sig-bubble ' + dir + '">';
      html += '<div class="sig-sender">' + escapeHtml(m.sender || (dir === 'in' ? 'User' : 'Clawd')) + '</div>';
      html += '<div class="sig-text md-rendered">' + renderMarkdown(text) + '</div>';
      html += '<div class="sig-time">' + date + ' ' + ts + '</div>';
      html += '</div>';
    });
    html += '</div>';
    body.innerHTML = html;
    document.getElementById('comp-modal-footer').textContent = 'Last updated: ' + new Date().toLocaleTimeString() + ' - ' + (data.total || msgs.length) + ' total messages';
  }).catch(function(e) {
    if (!isCompModalActive(expectedNodeId)) return;
    if (!isRefresh) {
      document.getElementById('comp-modal-body').innerHTML = '<div style="text-align:center;padding:20px;color:var(--text-error);">Failed to load Signal messages</div>';
    }
  });
}

function escapeHtml(s) {
  var d = document.createElement('div'); d.textContent = s; return d.innerHTML;
}

function renderMarkdown(text) {
  if (!text) return '';
  var s = escapeHtml(text);
  // Code blocks (``` ... ```)
  s = s.replace(/```(\w*)\n?([\s\S]*?)```/g, '<pre><code>$2</code></pre>');
  // Inline code
  s = s.replace(/`([^`]+)`/g, '<code>$1</code>');
  // Headers
  s = s.replace(/^#### (.+)$/gm, '<h4>$1</h4>');
  s = s.replace(/^### (.+)$/gm, '<h3>$1</h3>');
  s = s.replace(/^## (.+)$/gm, '<h2>$1</h2>');
  s = s.replace(/^# (.+)$/gm, '<h1>$1</h1>');
  // Bold + italic
  s = s.replace(/\*\*\*(.+?)\*\*\*/g, '<strong><em>$1</em></strong>');
  s = s.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
  s = s.replace(/\*(.+?)\*/g, '<em>$1</em>');
  s = s.replace(/_(.+?)_/g, '<em>$1</em>');
  // Links
  s = s.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" rel="noopener">$1</a>');
  // Blockquotes
  s = s.replace(/^&gt; (.+)$/gm, '<blockquote>$1</blockquote>');
  // Unordered lists
  s = s.replace(/^[-*] (.+)$/gm, '<li>$1</li>');
  s = s.replace(/(<li>.*<\/li>\n?)+/g, '<ul>$&</ul>');
  // Line breaks (double newline = paragraph, single = br)
  s = s.replace(/\n\n/g, '</p><p>');
  s = s.replace(/\n/g, '<br>');
  s = '<p>' + s + '</p>';
  // Clean up empty paragraphs
  s = s.replace(/<p><\/p>/g, '');
  s = s.replace(/<p>(<h[1-4]>)/g, '$1');
  s = s.replace(/(<\/h[1-4]>)<\/p>/g, '$1');
  s = s.replace(/<p>(<pre>)/g, '$1');
  s = s.replace(/(<\/pre>)<\/p>/g, '$1');
  s = s.replace(/<p>(<ul>)/g, '$1');
  s = s.replace(/(<\/ul>)<\/p>/g, '$1');
  s = s.replace(/<p>(<blockquote>)/g, '$1');
  s = s.replace(/(<\/blockquote>)<\/p>/g, '$1');
  return s;
}

function loadDiscordMessages(isRefresh) {
  var expectedNodeId = 'node-discord';
  if (!isCompModalActive(expectedNodeId) && isRefresh) return;
  fetch('/api/channel/discord?limit=50').then(function(r) { return r.json(); }).then(function(data) {
    if (!isCompModalActive(expectedNodeId)) return;
    var msgs = data.messages || [];
    var body = document.getElementById('comp-modal-body');
    var html = '<div class="discord-stats"><span class="in">📥 ' + (data.todayIn || 0) + ' incoming</span><span class="out">📤 ' + (data.todayOut || 0) + ' outgoing</span><span style="margin-left:auto;color:var(--text-muted);font-size:11px;">Today</span></div>';
    // Show guild/channel info if available
    var guilds = data.guilds || [];
    var channels = data.channels || [];
    if (guilds.length || channels.length) {
      html += '<div class="discord-server-info">';
      html += '<span style="opacity:0.6;">🏠</span>';
      if (guilds.length) html += '<span class="guild-name">' + escapeHtml(guilds[0]) + '</span>';
      if (channels.length) html += '<span class="ch-name">#' + escapeHtml(channels[0]) + '</span>';
      html += '</div>';
    }
    html += '<div class="discord-chat" style="max-height:60vh;overflow-y:auto;">';
    if (msgs.length === 0) {
      html += '<div style="text-align:center;padding:40px;color:var(--text-muted);">No Discord messages found</div>';
    }
    msgs.slice().reverse().forEach(function(m) {
      var dir = m.direction === 'in' ? 'in' : 'out';
      var sender = escapeHtml(m.sender || (dir === 'in' ? 'User' : 'Bot'));
      var ts = m.timestamp ? new Date(m.timestamp).toLocaleTimeString([], {hour:'2-digit',minute:'2-digit'}) : '';
      var date = m.timestamp ? new Date(m.timestamp).toLocaleDateString([], {month:'short',day:'numeric'}) : '';
      var text = escapeHtml((m.text || '').substring(0, 500));
      html += '<div style="display:flex;flex-direction:column;align-items:' + (dir==='out'?'flex-end':'flex-start') + ';">';
      html += '<div class="discord-bubble ' + dir + '">';
      html += '<div class="discord-sender">' + sender + '</div>';
      html += '<div class="discord-text">' + text + '</div>';
      html += '<div class="discord-time">' + (date ? date + ' - ' : '') + ts + '</div>';
      html += '</div></div>';
    });
    html += '</div>';
    body.innerHTML = html;
    document.getElementById('comp-modal-footer').textContent = 'Last updated: ' + new Date().toLocaleTimeString();
  }).catch(function(e) {
    if (!isCompModalActive(expectedNodeId)) return;
    document.getElementById('comp-modal-body').innerHTML = '<div style="text-align:center;padding:20px;color:var(--text-error);">Failed to load Discord: ' + escapeHtml(e.message) + '</div>';
  });
}

function loadSlackMessages(isRefresh) {
  var expectedNodeId = 'node-slack';
  if (!isCompModalActive(expectedNodeId) && isRefresh) return;
  fetch('/api/channel/slack?limit=50').then(function(r) { return r.json(); }).then(function(data) {
    if (!isCompModalActive(expectedNodeId)) return;
    var msgs = data.messages || [];
    var body = document.getElementById('comp-modal-body');
    var html = '<div class="slack-stats"><span class="in">📥 ' + (data.todayIn || 0) + ' incoming</span><span class="out">📤 ' + (data.todayOut || 0) + ' outgoing</span><span style="margin-left:auto;color:var(--text-muted);font-size:11px;">Today</span></div>';
    var workspaces = data.workspaces || [];
    var channels = data.channels || [];
    if (workspaces.length || channels.length) {
      html += '<div class="slack-workspace-info">';
      html += '<span style="opacity:0.6;">💼</span>';
      if (workspaces.length) html += '<span class="ws-name">' + escapeHtml(workspaces[0]) + '</span>';
      if (channels.length) html += '<span class="ch-name">#' + escapeHtml(channels[0]) + '</span>';
      html += '</div>';
    }
    html += '<div class="slack-chat" style="max-height:60vh;overflow-y:auto;">';
    if (msgs.length === 0) {
      html += '<div style="text-align:center;padding:40px;color:var(--text-muted);">No Slack messages found</div>';
    }
    msgs.slice().reverse().forEach(function(m) {
      var dir = m.direction === 'in' ? 'in' : 'out';
      var sender = escapeHtml(m.sender || (dir === 'in' ? 'User' : 'Bot'));
      var ts = m.timestamp ? new Date(m.timestamp).toLocaleTimeString([], {hour:'2-digit',minute:'2-digit'}) : '';
      var date = m.timestamp ? new Date(m.timestamp).toLocaleDateString([], {month:'short',day:'numeric'}) : '';
      var text = escapeHtml((m.text || '').substring(0, 500));
      html += '<div style="display:flex;flex-direction:column;align-items:' + (dir==='out'?'flex-end':'flex-start') + ';">';
      html += '<div class="slack-bubble ' + dir + '">';
      html += '<div class="slack-sender">' + sender + '</div>';
      html += '<div class="slack-text">' + text + '</div>';
      html += '<div class="slack-time">' + (date ? date + ' - ' : '') + ts + '</div>';
      html += '</div></div>';
    });
    html += '</div>';
    body.innerHTML = html;
    document.getElementById('comp-modal-footer').textContent = 'Last updated: ' + new Date().toLocaleTimeString();
  }).catch(function(e) {
    if (!isCompModalActive(expectedNodeId)) return;
    document.getElementById('comp-modal-body').innerHTML = '<div style="text-align:center;padding:20px;color:var(--text-error);">Failed to load Slack: ' + escapeHtml(e.message) + '</div>';
  });
}

function loadGenericChannelData(nodeId, chKey, comp, isRefresh) {
  if (!isCompModalActive(nodeId) && isRefresh) return;
  var body = document.getElementById('comp-modal-body');
  fetch('/api/channel/' + chKey + '?limit=50&offset=0').then(function(r) { return r.json(); }).then(function(data) {
    if (!isCompModalActive(nodeId)) return;
    var msgs = data.messages || [];
    var todayIn = data.todayIn || 0;
    var todayOut = data.todayOut || 0;
    var status = data.status || 'connected';
    var html = '<div class="tg-stats">'
      + '<span class="in">📥 ' + todayIn + ' incoming</span>'
      + '<span class="out">📤 ' + todayOut + ' outgoing</span>'
      + '<span style="margin-left:auto;color:var(--text-muted);font-size:11px;">' + escapeHtml(status) + ' - Today</span>'
      + '</div>';
    if (msgs.length === 0) {
      html += '<div style="text-align:center;padding:32px;color:var(--text-muted);">'
        + '<div style="font-size:36px;margin-bottom:12px;">' + comp.icon + '</div>'
        + '<div style="font-size:15px;font-weight:600;margin-bottom:6px;">' + escapeHtml(comp.name) + ' connected</div>'
        + '<div style="font-size:13px;">No recent messages found in logs.</div>'
        + '<div style="margin-top:8px;font-size:11px;color:var(--text-muted);">Messages will appear here once detected in session transcripts.</div>'
        + '</div>';
    } else {
      html += '<div class="tg-messages">';
      msgs.forEach(function(m) {
        var dir = m.direction === 'in' ? 'msg-in' : 'msg-out';
        var sender = escapeHtml(m.sender || (m.direction === 'in' ? 'User' : comp.name));
        var text = escapeHtml(m.text || '(no text)');
        var ts = m.timestamp ? new Date(m.timestamp).toLocaleTimeString() : '';
        html += '<div class="tg-msg ' + dir + '">'
          + '<div class="tg-msg-meta"><span class="tg-msg-sender">' + sender + '</span>'
          + (ts ? '<span class="tg-msg-time">' + ts + '</span>' : '') + '</div>'
          + '<div class="tg-msg-text">' + text + '</div>'
          + '</div>';
      });
      html += '</div>';
    }
    body.innerHTML = html;
    document.getElementById('comp-modal-footer').textContent = 'Last updated: ' + new Date().toLocaleTimeString();
  }).catch(function(e) {
    if (!isCompModalActive(nodeId)) return;
    body.innerHTML = '<div style="text-align:center;padding:24px;color:var(--text-muted);">'
      + '<div style="font-size:36px;margin-bottom:12px;">' + comp.icon + '</div>'
      + '<div style="font-weight:600;margin-bottom:6px;">' + escapeHtml(comp.name) + '</div>'
      + '<div style="font-size:13px;">Could not fetch channel data.</div>'
      + '</div>';
  });
}

// ── Webchat themed loader ─────────────────────────────────────────────────
var _webchatRefreshTimer = null;

function loadWebchatMessages(isRefresh) {
  var expectedNodeId = 'node-webchat';
  if (!isCompModalActive(expectedNodeId) && isRefresh) return;
  var body = document.getElementById('comp-modal-body');
  fetch('/api/channel/webchat?limit=50').then(function(r) { return r.json(); }).then(function(data) {
    if (!isCompModalActive(expectedNodeId)) return;
    var msgs = data.messages || [];
    var todayIn = data.todayIn || 0;
    var todayOut = data.todayOut || 0;
    var activeSessions = data.activeSessions || 0;
    var lastActive = data.lastActive ? new Date(data.lastActive).toLocaleTimeString() : '--';
    var html = '<div class="wc-stats">'
      + '<span class="wc-stat-item">🌐 <b>' + activeSessions + '</b> sessions</span>'
      + '<span class="wc-stat-item">📥 <b>' + todayIn + '</b> in</span>'
      + '<span class="wc-stat-item">📤 <b>' + todayOut + '</b> out</span>'
      + '<span style="margin-left:auto;font-size:11px;color:#6b7280;">Last: ' + lastActive + '</span>'
      + '</div>';
    if (msgs.length === 0) {
      html += '<div style="text-align:center;padding:40px;color:#6b7280;">'
        + '<div style="font-size:36px;margin-bottom:12px;">🌐</div>'
        + '<div style="font-size:15px;font-weight:600;margin-bottom:6px;color:#374151;">WebChat connected</div>'
        + '<div style="font-size:13px;">No recent messages found in logs.</div>'
        + '<div style="margin-top:8px;font-size:11px;">Messages appear once sessions are active.</div>'
        + '</div>';
    } else {
      html += '<div class="wc-messages">';
      msgs.forEach(function(m) {
        var dir = m.direction === 'in' ? 'wc-msg-in' : 'wc-msg-out';
        var text = escapeHtml(m.text || '(no text)');
        var ts = m.timestamp ? new Date(m.timestamp).toLocaleTimeString() : '';
        html += '<div class="wc-msg-row ' + (m.direction === 'out' ? 'wc-row-out' : '') + '">'
          + '<div class="wc-bubble ' + dir + '">'
          + '<div class="wc-bubble-text">' + text + '</div>'
          + (ts ? '<div class="wc-bubble-time">' + ts + '</div>' : '')
          + '</div></div>';
      });
      html += '</div>';
    }
    body.innerHTML = html;
    document.getElementById('comp-modal-footer').textContent = 'WebChat - Last updated: ' + new Date().toLocaleTimeString();
  }).catch(function(e) {
    if (!isCompModalActive(expectedNodeId)) return;
    body.innerHTML = '<div style="text-align:center;padding:24px;color:#6b7280;">Could not fetch WebChat data.</div>';
  });
}

// ── IRC themed loader ──────────────────────────────────────────────────────
var _ircRefreshTimer = null;

function loadIRCMessages(isRefresh) {
  var expectedNodeId = 'node-irc';
  if (!isCompModalActive(expectedNodeId) && isRefresh) return;
  var body = document.getElementById('comp-modal-body');
  fetch('/api/channel/irc?limit=50').then(function(r) { return r.json(); }).then(function(data) {
    if (!isCompModalActive(expectedNodeId)) return;
    var msgs = data.messages || [];
    var todayIn = data.todayIn || 0;
    var todayOut = data.todayOut || 0;
    var channels = data.channels || [];
    var nicks = data.nicks || [];
    var html = '<div class="irc-header">'
      + '<span class="irc-stat">📥 ' + todayIn + '</span>'
      + '<span class="irc-stat">📤 ' + todayOut + '</span>';
    if (channels.length > 0) html += '<span class="irc-channels">' + channels.map(function(c){return escapeHtml(c);}).join(' ') + '</span>';
    if (nicks.length > 0) html += '<span class="irc-nick">nick: ' + escapeHtml(nicks[0]) + '</span>';
    html += '</div>';
    if (msgs.length === 0) {
      html += '<div style="text-align:center;padding:32px;color:#9ca3af;font-family:monospace;">'
        + '<div style="font-size:28px;margin-bottom:8px;">#️⃣</div>'
        + '<div>*** No messages found in IRC logs ***</div>'
        + '<div style="margin-top:6px;font-size:11px;color:#6b7280;">Messages appear when IRC channel is active</div>'
        + '</div>';
    } else {
      html += '<div class="irc-log">';
      var sorted = msgs.slice().reverse();
      sorted.forEach(function(m) {
        var ts = m.timestamp ? new Date(m.timestamp).toLocaleTimeString([],{hour:'2-digit',minute:'2-digit',second:'2-digit'}) : '??:??:??';
        var nick = m.direction === 'in' ? (nicks[0] || 'User') : 'Clawd';
        var text = escapeHtml(m.text || '');
        html += '<div class="irc-line">'
          + '<span class="irc-ts">[' + ts + ']</span> '
          + '<span class="irc-nick-tag">&lt;' + escapeHtml(nick) + '&gt;</span> '
          + '<span class="irc-text">' + text + '</span>'
          + '</div>';
      });
      html += '</div>';
    }
    body.innerHTML = html;
    document.getElementById('comp-modal-footer').textContent = 'IRC - ' + (channels.join(', ') || 'no channels') + ' - ' + new Date().toLocaleTimeString();
  }).catch(function(e) {
    if (!isCompModalActive(expectedNodeId)) return;
    body.innerHTML = '<div style="text-align:center;padding:24px;color:#9ca3af;font-family:monospace;">*** Could not fetch IRC data ***</div>';
  });
}

// ── BlueBubbles themed loader ──────────────────────────────────────────────
var _bbRefreshTimer = null;

function loadBlueBubblesMessages(isRefresh) {
  var expectedNodeId = 'node-bluebubbles';
  if (!isCompModalActive(expectedNodeId) && isRefresh) return;
  var body = document.getElementById('comp-modal-body');
  fetch('/api/channel/bluebubbles?limit=50').then(function(r) { return r.json(); }).then(function(data) {
    if (!isCompModalActive(expectedNodeId)) return;
    var msgs = data.messages || [];
    var todayIn = data.todayIn || 0;
    var todayOut = data.todayOut || 0;
    var chatCount = data.chatCount;
    var status = data.status || 'configured';
    var statusColor = status === 'connected' ? '#34C759' : status === 'log-only' ? '#f59e0b' : '#6b7280';
    var html = '<div class="bb-stats">'
      + '<span class="bb-stat-item" style="color:#34C759;">📥 <b>' + todayIn + '</b></span>'
      + '<span class="bb-stat-item" style="color:#34C759;">📤 <b>' + todayOut + '</b></span>'
      + (chatCount !== null && chatCount !== undefined ? '<span class="bb-stat-item">💬 <b>' + chatCount + '</b> chats</span>' : '')
      + '<span style="margin-left:auto;font-size:11px;color:' + statusColor + ';">● ' + escapeHtml(status) + '</span>'
      + '</div>';
    if (msgs.length === 0) {
      html += '<div style="text-align:center;padding:40px;">'
        + '<div style="font-size:36px;margin-bottom:12px;">🍎</div>'
        + '<div style="font-size:15px;font-weight:600;margin-bottom:6px;color:#34C759;">BlueBubbles ' + (status === 'connected' ? 'Connected' : 'Configured') + '</div>'
        + (chatCount !== null && chatCount !== undefined ? '<div style="font-size:13px;color:#6b7280;">' + chatCount + ' chats available via BB server</div>' : '<div style="font-size:13px;color:#6b7280;">No messages found in logs.</div>')
        + '</div>';
    } else {
      html += '<div class="bb-messages">';
      msgs.forEach(function(m) {
        var dir = m.direction === 'in' ? 'bb-msg-in' : 'bb-msg-out';
        var text = escapeHtml(m.text || '(no text)');
        var ts = m.timestamp ? new Date(m.timestamp).toLocaleTimeString() : '';
        html += '<div class="bb-msg-row ' + (m.direction === 'out' ? 'bb-row-out' : '') + '">'
          + '<div class="bb-bubble ' + dir + '">'
          + '<div class="bb-bubble-text">' + text + '</div>'
          + (ts ? '<div class="bb-bubble-time">' + ts + '</div>' : '')
          + '</div></div>';
      });
      html += '</div>';
    }
    body.innerHTML = html;
    document.getElementById('comp-modal-footer').textContent = 'BlueBubbles - ' + escapeHtml(status) + ' - ' + new Date().toLocaleTimeString();
  }).catch(function(e) {
    if (!isCompModalActive(expectedNodeId)) return;
    body.innerHTML = '<div style="text-align:center;padding:24px;color:#6b7280;">Could not fetch BlueBubbles data.</div>';
  });
}

function loadGoogleChatMessages(isRefresh) {
  var nodeId = 'node-googlechat';
  if (!isCompModalActive(nodeId) && isRefresh) return;
  var body = document.getElementById('comp-modal-body');
  fetch('/api/channel/googlechat?limit=50&offset=0').then(function(r) { return r.json(); }).then(function(data) {
    if (!isCompModalActive(nodeId)) return;
    var msgs = data.messages || [];
    var todayIn = data.todayIn || 0;
    var todayOut = data.todayOut || 0;
    var spaces = data.spaces || [];
    var html = '<div class="gc-stats">'
      + '<span class="in">📥 ' + todayIn + ' incoming</span>'
      + '<span class="out">📤 ' + todayOut + ' outgoing</span>'
      + (spaces.length ? '<span style="margin-left:auto;color:#1a73e8;font-size:11px;">🏢 ' + escapeHtml(spaces.join(', ')) + '</span>' : '<span style="margin-left:auto;color:var(--text-muted);font-size:11px;">Today - Google Chat</span>')
      + '</div>';
    if (msgs.length === 0) {
      html += '<div style="text-align:center;padding:32px;color:var(--text-muted);">'
        + '<div style="font-size:40px;margin-bottom:12px;">💬</div>'
        + '<div style="font-size:15px;font-weight:600;margin-bottom:6px;color:#1a73e8;">Google Chat</div>'
        + '<div style="font-size:13px;">No recent messages found in logs.</div>'
        + '<div style="margin-top:8px;font-size:11px;color:var(--text-muted);">Messages will appear here once detected in session transcripts.</div>'
        + '</div>';
    } else {
      html += '<div class="gc-chat">';
      msgs.forEach(function(m) {
        var dir = m.direction === 'in' ? 'in' : 'out';
        var sender = escapeHtml(m.sender || (m.direction === 'in' ? 'User' : 'Clawd'));
        var text = escapeHtml(m.text || '(no text)');
        var ts = m.timestamp ? new Date(m.timestamp).toLocaleTimeString() : '';
        html += '<div class="gc-bubble ' + dir + '">'
          + '<div class="gc-sender">' + sender + '</div>'
          + '<div class="gc-text">' + text + '</div>'
          + (ts ? '<div class="gc-time">' + ts + '</div>' : '')
          + '</div>';
      });
      html += '</div>';
    }
    body.innerHTML = html;
    document.getElementById('comp-modal-footer').textContent = 'Google Chat - Last updated: ' + new Date().toLocaleTimeString();
  }).catch(function() {
    if (!isCompModalActive(nodeId)) return;
    body.innerHTML = '<div style="text-align:center;padding:24px;color:var(--text-muted);"><div style="font-size:36px;margin-bottom:12px;">💬</div><div style="font-weight:600;color:#1a73e8;">Google Chat</div><div style="font-size:13px;margin-top:8px;">Could not fetch channel data.</div></div>';
  });
}

function loadMSTeamsMessages(isRefresh) {
  var nodeId = 'node-msteams';
  if (!isCompModalActive(nodeId) && isRefresh) return;
  var body = document.getElementById('comp-modal-body');
  fetch('/api/channel/msteams?limit=50&offset=0').then(function(r) { return r.json(); }).then(function(data) {
    if (!isCompModalActive(nodeId)) return;
    var msgs = data.messages || [];
    var todayIn = data.todayIn || 0;
    var todayOut = data.todayOut || 0;
    var teams = data.teams || [];
    var html = '<div class="mst-stats">'
      + '<span class="in">📥 ' + todayIn + ' incoming</span>'
      + '<span class="out">📤 ' + todayOut + ' outgoing</span>'
      + (teams.length ? '<span style="margin-left:auto;color:#6264A7;font-size:11px;">👥 ' + escapeHtml(teams.join(', ')) + '</span>' : '<span style="margin-left:auto;color:var(--text-muted);font-size:11px;">Today - MS Teams</span>')
      + '</div>';
    if (msgs.length === 0) {
      html += '<div style="text-align:center;padding:32px;color:var(--text-muted);">'
        + '<div style="font-size:40px;margin-bottom:12px;">👔</div>'
        + '<div style="font-size:15px;font-weight:600;margin-bottom:6px;color:#6264A7;">Microsoft Teams</div>'
        + '<div style="font-size:13px;">No recent messages found in logs.</div>'
        + '<div style="margin-top:8px;font-size:11px;color:var(--text-muted);">Messages will appear here once detected in session transcripts.</div>'
        + '</div>';
    } else {
      html += '<div class="mst-chat">';
      msgs.forEach(function(m) {
        var dir = m.direction === 'in' ? 'in' : 'out';
        var sender = escapeHtml(m.sender || (m.direction === 'in' ? 'User' : 'Clawd'));
        var text = escapeHtml(m.text || '(no text)');
        var ts = m.timestamp ? new Date(m.timestamp).toLocaleTimeString() : '';
        html += '<div class="mst-bubble ' + dir + '">'
          + '<div class="mst-sender">' + sender + '</div>'
          + '<div class="mst-text">' + text + '</div>'
          + (ts ? '<div class="mst-time">' + ts + '</div>' : '')
          + '</div>';
      });
      html += '</div>';
    }
    body.innerHTML = html;
    document.getElementById('comp-modal-footer').textContent = 'Microsoft Teams - Last updated: ' + new Date().toLocaleTimeString();
  }).catch(function() {
    if (!isCompModalActive(nodeId)) return;
    body.innerHTML = '<div style="text-align:center;padding:24px;color:var(--text-muted);"><div style="font-size:36px;margin-bottom:12px;">👔</div><div style="font-weight:600;color:#6264A7;">Microsoft Teams</div><div style="font-size:13px;margin-top:8px;">Could not fetch channel data.</div></div>';
  });
}

function loadMattermostMessages(isRefresh) {
  var nodeId = 'node-mattermost';
  if (!isCompModalActive(nodeId) && isRefresh) return;
  var body = document.getElementById('comp-modal-body');
  fetch('/api/channel/mattermost?limit=50&offset=0').then(function(r) { return r.json(); }).then(function(data) {
    if (!isCompModalActive(nodeId)) return;
    var msgs = data.messages || [];
    var todayIn = data.todayIn || 0;
    var todayOut = data.todayOut || 0;
    var channels = data.channels || [];
    var html = '<div class="mm-stats">'
      + '<span class="in">📥 ' + todayIn + ' incoming</span>'
      + '<span class="out">📤 ' + todayOut + ' outgoing</span>'
      + (channels.length ? '<span style="margin-left:auto;color:#0058CC;font-size:11px;"># ' + escapeHtml(channels.join(', ')) + '</span>' : '<span style="margin-left:auto;color:var(--text-muted);font-size:11px;">Today - Mattermost</span>')
      + '</div>';
    if (msgs.length === 0) {
      html += '<div style="text-align:center;padding:32px;color:var(--text-muted);">'
        + '<div style="font-size:40px;margin-bottom:12px;">⚓</div>'
        + '<div style="font-size:15px;font-weight:600;margin-bottom:6px;color:#0058CC;">Mattermost</div>'
        + '<div style="font-size:13px;">No recent messages found in logs.</div>'
        + '<div style="margin-top:8px;font-size:11px;color:var(--text-muted);">Messages will appear here once detected in session transcripts.</div>'
        + '</div>';
    } else {
      html += '<div class="mm-chat">';
      msgs.forEach(function(m) {
        var dir = m.direction === 'in' ? 'in' : 'out';
        var sender = escapeHtml(m.sender || (m.direction === 'in' ? 'User' : 'Clawd'));
        var text = escapeHtml(m.text || '(no text)');
        var ts = m.timestamp ? new Date(m.timestamp).toLocaleTimeString() : '';
        html += '<div class="mm-bubble ' + dir + '">'
          + '<div class="mm-sender">' + sender + '</div>'
          + '<div class="mm-text">' + text + '</div>'
          + (ts ? '<div class="mm-time">' + ts + '</div>' : '')
          + '</div>';
      });
      html += '</div>';
    }
    body.innerHTML = html;
    document.getElementById('comp-modal-footer').textContent = 'Mattermost - Last updated: ' + new Date().toLocaleTimeString();
  }).catch(function() {
    if (!isCompModalActive(nodeId)) return;
    body.innerHTML = '<div style="text-align:center;padding:24px;color:var(--text-muted);"><div style="font-size:36px;margin-bottom:12px;">⚓</div><div style="font-weight:600;color:#0058CC;">Mattermost</div><div style="font-size:13px;margin-top:8px;">Could not fetch channel data.</div></div>';
  });
}

var _brainRefreshTimer = null;
var _brainPage = 0;

function loadBrainData(isRefresh) {
  var expectedNodeId = 'node-brain';
  var url = '/api/component/brain?limit=50&offset=' + (_brainPage * 50);
  fetchJsonWithTimeout(url, 8000).catch(function(err) {
    if (String((err && err.message) || '').toLowerCase().includes('abort')) {
      return fetchJsonWithTimeout(url, 15000);
    }
    throw err;
  }).then(function(data) {
    if (!isCompModalActive(expectedNodeId)) return;
    var body = document.getElementById('comp-modal-body');
    var s = data.stats || {};
    var tok = s.today_tokens || {};
    var totalTok = (tok.input||0) + (tok.output||0) + (tok.cache_read||0);
    var fmtTok = totalTok >= 1e6 ? (totalTok/1e6).toFixed(1) + 'M' : totalTok >= 1e3 ? (totalTok/1e3).toFixed(1) + 'K' : totalTok;

    var html = '';
    // Model badge
    html += '<div style="text-align:center;margin-bottom:14px;"><span style="background:linear-gradient(135deg,#FFD54F,#FF9800);color:#1a1a2e;padding:4px 14px;border-radius:20px;font-size:12px;font-weight:700;letter-spacing:0.5px;">' + escapeHtml(s.model||'unknown') + '</span></div>';

    // Stats cards 2x2
    // Honest count + per-call avg so users can sanity-check the ratio. A "low"
    // call count with high tokens is normal (cached context + long output);
    // showing tokens-per-call inline avoids the "only 3 calls?" trust panic.
    var avgTokPerCall = (s.today_calls||0) > 0 ? Math.round(totalTok / s.today_calls) : 0;
    var avgTokFmt = avgTokPerCall >= 1e6 ? (avgTokPerCall/1e6).toFixed(1)+'M' : avgTokPerCall >= 1e3 ? (avgTokPerCall/1e3).toFixed(1)+'K' : avgTokPerCall;
    var callsTooltip = 'API round-trips today (one HTTP request to the LLM provider per call). Cached context tokens are reused across calls and counted as cache_read, not as separate calls. Counts only what your agent has uploaded — sessions still open or pending sync may not be reflected yet.';
    html += '<div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-bottom:16px;">';
    html += '<div style="background:var(--bg-secondary);border-radius:10px;padding:12px 14px;text-align:center;cursor:help;" title="' + callsTooltip + '"><div style="font-size:24px;font-weight:700;color:var(--text-primary);">' + (s.today_calls||0) + '</div><div style="font-size:10px;color:var(--text-muted);text-transform:uppercase;margin-top:2px;">API Calls Today</div>' + (avgTokPerCall ? '<div style="font-size:10px;color:var(--text-tertiary);margin-top:2px;">~' + avgTokFmt + ' tok/call avg</div>' : '') + '</div>';
    html += '<div style="background:var(--bg-secondary);border-radius:10px;padding:12px 14px;text-align:center;"><div style="font-size:24px;font-weight:700;color:var(--text-primary);">' + fmtTok + '</div><div style="font-size:10px;color:var(--text-muted);text-transform:uppercase;margin-top:2px;">Tokens</div></div>';
    var costColor = parseFloat((s.today_cost||'$0').replace('$','')) > 50 ? '#f59e0b' : parseFloat((s.today_cost||'$0').replace('$','')) > 100 ? '#ef4444' : '#22c55e';
    html += '<div style="background:var(--bg-secondary);border-radius:10px;padding:12px 14px;text-align:center;"><div style="font-size:24px;font-weight:700;color:' + costColor + ';">' + (s.today_cost||'$0.00') + '</div><div style="font-size:10px;color:var(--text-muted);text-transform:uppercase;margin-top:2px;">Cost</div></div>';
    html += '<div style="background:var(--bg-secondary);border-radius:10px;padding:12px 14px;text-align:center;"><div style="font-size:24px;font-weight:700;color:var(--text-primary);">' + ((s.avg_response_ms||0) >= 1000 ? ((s.avg_response_ms/1000).toFixed(1)+'s') : ((s.avg_response_ms||0)+'ms')) + '</div><div style="font-size:10px;color:var(--text-muted);text-transform:uppercase;margin-top:2px;">Avg Response</div></div>';
    html += '</div>';

    // Thinking & Cache stats row
    var thinkCount = s.thinking_calls || 0;
    var cacheHits = s.cache_hits || 0;
    var cacheRate = s.today_calls > 0 ? Math.round(cacheHits / s.today_calls * 100) : 0;
    html += '<div style="display:flex;gap:8px;margin-bottom:12px;justify-content:center;flex-wrap:wrap;">';
    html += '<span style="background:' + (thinkCount > 0 ? '#7c3aed22' : 'var(--bg-secondary)') + ';color:' + (thinkCount > 0 ? '#7c3aed' : 'var(--text-muted)') + ';padding:3px 10px;border-radius:12px;font-size:11px;font-weight:600;">🧠 Thinking: ' + thinkCount + '/' + (s.today_calls||0) + '</span>';
    html += '<span style="background:' + (cacheRate > 50 ? '#22c55e22' : 'var(--bg-secondary)') + ';color:' + (cacheRate > 50 ? '#22c55e' : 'var(--text-muted)') + ';padding:3px 10px;border-radius:12px;font-size:11px;font-weight:600;">💾 Cache hit: ' + cacheRate + '%</span>';
    var cacheW = tok.cache_write||0;
    html += '<span style="background:var(--bg-secondary);color:var(--text-muted);padding:3px 10px;border-radius:12px;font-size:11px;font-weight:600;">✍️ Cache write: ' + (cacheW>=1e6?(cacheW/1e6).toFixed(1)+'M':cacheW>=1e3?(cacheW/1e3).toFixed(1)+'K':cacheW) + '</span>';
    html += '</div>';

    // Token breakdown bar
    var tIn = tok.input||0, tOut = tok.output||0, tCR = tok.cache_read||0;
    var tTotal = tIn+tOut+tCR || 1;
    html += '<div style="display:flex;height:6px;border-radius:3px;overflow:hidden;margin-bottom:16px;background:var(--bg-secondary);">';
    html += '<div style="width:' + (tIn/tTotal*100) + '%;background:#3b82f6;" title="Input: ' + tIn + '"></div>';
    html += '<div style="width:' + (tOut/tTotal*100) + '%;background:#8b5cf6;" title="Output: ' + tOut + '"></div>';
    html += '<div style="width:' + (tCR/tTotal*100) + '%;background:#22c55e;" title="Cache Read: ' + tCR + '"></div>';
    html += '</div>';
    html += '<div style="display:flex;gap:12px;font-size:10px;color:var(--text-muted);margin-bottom:14px;justify-content:center;">';
    html += '<span>🔵 Input</span><span>🟣 Output</span><span>🟢 Cache Read</span>';
    html += '</div>';

    // Call list
    var calls = data.calls || [];
    if (calls.length === 0) {
      html += '<div style="text-align:center;padding:20px;color:var(--text-muted);">No LLM calls found today</div>';
    } else {
      html += '<div style="display:flex;flex-direction:column;gap:6px;max-height:400px;overflow-y:auto;">';
      var TOOL_ICONS = {read:'📄',write:'✏️',edit:'🔧',exec:'⚡',process:'⚙️',browser:'🌐',web_search:'🔍',web_fetch:'🌍',message:'💬',tts:'🔊',image:'🖼️',canvas:'🎨',nodes:'📱'};
      var TOOL_COLORS = {exec:'#f59e0b',browser:'#3b82f6',web_search:'#8b5cf6',web_fetch:'#06b6d4',message:'#ec4899',read:'#6b7280',write:'#22c55e',edit:'#f97316',tts:'#a855f7',image:'#ef4444',canvas:'#14b8a6',nodes:'#6366f1',process:'#64748b'};
      calls.forEach(function(c) {
        var ts = c.timestamp ? new Date(c.timestamp).toLocaleTimeString([],{hour:'2-digit',minute:'2-digit',second:'2-digit'}) : '';
        var costVal = parseFloat((c.cost||'$0').replace('$',''));
        var cColor = costVal > 0.50 ? '#f59e0b' : costVal > 1.0 ? '#ef4444' : '#22c55e';
        var dur = c.duration_ms > 0 ? (c.duration_ms >= 1000 ? (c.duration_ms/1000).toFixed(1)+'s' : c.duration_ms+'ms') : '--';
        html += '<div style="display:flex;align-items:center;gap:8px;padding:8px 10px;background:var(--bg-secondary);border-radius:8px;border:1px solid var(--border-secondary);font-size:11px;flex-wrap:wrap;">';
        html += '<span style="color:var(--text-tertiary);min-width:58px;">' + ts + '</span>';
        html += '<span style="color:var(--text-muted);font-size:10px;min-width:50px;">' + escapeHtml(c.session||'main') + '</span>';
        html += '<span style="color:#3b82f6;min-width:45px;" title="In">' + (c.tokens_in>=1000?(c.tokens_in/1000).toFixed(1)+'K':c.tokens_in) + '-></span>';
        html += '<span style="color:#8b5cf6;min-width:40px;" title="Out">' + (c.tokens_out>=1000?(c.tokens_out/1000).toFixed(1)+'K':c.tokens_out) + '</span>';
        html += '<span style="color:' + cColor + ';min-width:50px;">' + (c.cost||'$0') + '</span>';
        html += '<span style="color:var(--text-muted);min-width:35px;">' + dur + '</span>';
        if (c.thinking) html += '<span style="background:#7c3aed22;color:#7c3aed;padding:1px 5px;border-radius:4px;font-size:10px;" title="Thinking enabled">🧠</span>';
        if (c.cache_read > 0) html += '<span style="background:#22c55e22;color:#22c55e;padding:1px 5px;border-radius:4px;font-size:10px;" title="Cache hit: ' + c.cache_read + ' tokens">💾' + (c.cache_read>=1000?(c.cache_read/1000).toFixed(0)+'K':c.cache_read) + '</span>';
        // Tool badges
        if (c.tools_used && c.tools_used.length > 0) {
          html += '<span style="display:flex;gap:3px;flex-wrap:wrap;">';
          c.tools_used.forEach(function(t) {
            var icon = TOOL_ICONS[t] || '🔧';
            var bg = TOOL_COLORS[t] || '#6b7280';
            html += '<span style="background:' + bg + '22;color:' + bg + ';padding:1px 5px;border-radius:4px;font-size:10px;" title="' + t + '">' + icon + t + '</span>';
          });
          html += '</span>';
        }
        html += '</div>';
      });
      html += '</div>';
    }

    if (data.total > calls.length) {
      html += '<div style="text-align:center;margin-top:12px;font-size:12px;color:var(--text-muted);">' + calls.length + ' of ' + data.total + ' calls shown</div>';
    }

    body.innerHTML = html;
    document.getElementById('comp-modal-footer').textContent = 'Auto-refreshing - Last updated: ' + new Date().toLocaleTimeString() + ' - ' + (data.total||0) + ' API call' + ((data.total||0) === 1 ? '' : 's') + ' synced today (each = one HTTP round-trip to the LLM provider)';
  }).catch(function(e) {
    if (!isCompModalActive(expectedNodeId)) return;
    var msg = String((e && e.message) || 'Unknown error');
    if (msg.toLowerCase().includes('abort')) {
      msg = 'Request timed out. The brain panel is heavy; please retry in 2-3 seconds.';
    }
    document.getElementById('comp-modal-body').innerHTML = '<div style="text-align:center;padding:20px;color:var(--text-error);">Failed to load brain data: ' + msg + '</div>';
  });
}

function loadCostOptimizerData(isRefresh) {
  var expectedNodeId = 'node-cost-optimizer';
  fetch('/api/cost-optimizer').then(function(r) { return r.json(); }).then(function(data) {
    if (!isCompModalActive(expectedNodeId)) return;
    var body = document.getElementById('comp-modal-body');
    var html = '';

    // ══ SECTION 1: Cost Overview ══════════════════════════════════
    var todayCost = data.todayCost || 0;
    var monthCost = data.projectedMonthlyCost || 0;
    html += '<div class="cost-overview">';
    html += '<div class="cost-overview-header">💰 Cost Overview</div>';
    html += '<div class="cost-overview-row">';
    html += '<div class="cost-overview-item"><span class="cost-overview-label">Today</span><span class="cost-overview-value">$' + todayCost.toFixed(3) + '</span></div>';
    html += '<div class="cost-overview-item"><span class="cost-overview-label">Month Projected</span><span class="cost-overview-value">$' + monthCost.toFixed(2) + '</span></div>';
    html += '</div>';
    if (data.potentialSavings) {
      html += '<div class="savings-highlight">[prod] ' + data.potentialSavings + '</div>';
    }
    html += '</div>';

    // Recent expensive ops
    if (data.expensiveOps && data.expensiveOps.length > 0) {
      html += '<div style="margin-bottom:14px;">';
      data.expensiveOps.slice(0, 3).forEach(function(op) {
        html += '<div style="display:flex;justify-content:space-between;align-items:center;padding:6px 10px;background:var(--bg-hover);border-radius:6px;margin-bottom:4px;border-left:3px solid var(--text-error);">';
        html += '<span style="font-size:12px;color:var(--text-secondary);">' + op.model + ' <span style="color:var(--text-muted);">- ' + op.tokens + ' tokens - ' + op.timeAgo + '</span></span>';
        html += '<span style="font-size:12px;color:var(--text-error);font-weight:700;">$' + op.cost.toFixed(4) + '</span>';
        html += '</div>';
      });
      html += '</div>';
    }

    // ══ SECTION 2: Hardware ═══════════════════════════════════════
    var sys = (data.system) || {};
    // Detect hardware family so we don't paint Apple-only copy (Metal,
    // brew install) on Linux/CUDA users.
    var _bk = String(sys.backend || '').toLowerCase();
    var _isApple = _bk.indexOf('metal') >= 0 || /apple|m[1-4]\b/i.test(sys.cpu || '');
    var _isCuda = _bk.indexOf('cuda') >= 0 || /nvidia|cuda|geforce|rtx|gtx/i.test(sys.gpu || '');
    var _isAmdGpu = _bk.indexOf('rocm') >= 0 || /(amd|radeon)/i.test(sys.gpu || '');
    var _hasGpu = _isApple || _isCuda || _isAmdGpu;
    var _accelLabel = _isApple ? 'Metal' : _isCuda ? 'CUDA' : _isAmdGpu ? 'ROCm' : 'CPU';
    var _ollamaInstall = _isApple ? 'brew install ollama' : 'curl -fsSL https://ollama.com/install.sh | sh';

    html += '<div style="font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:1px;color:var(--text-muted);margin-bottom:6px;">🖥️ Your Hardware</div>';
    html += '<div class="hw-card">';
    if (sys.cpu) html += '<span class="hw-card-chip">' + escapeHtml(sys.cpu) + '</span>';
    if (sys.ram_gb) html += '<span class="hw-card-chip">' + sys.ram_gb + 'GB RAM</span>';
    if (sys.cores) html += '<span class="hw-card-chip">' + sys.cores + ' cores</span>';
    if (sys.backend) html += '<span class="hw-card-chip green">' + escapeHtml(sys.backend) + '</span>';
    html += '</div>';
    // Hardware-aware notice — only show Metal warning to Apple users.
    if (_isApple && !data.llmfitMetalDetected) {
      html += '<div class="hw-metal-notice">⚠️ llmfit doesn\'t detect Apple Metal -- actual performance will be <strong>3-5x faster</strong> with Ollama\'s Metal backend</div>';
    } else if (_isCuda) {
      html += '<div class="hw-metal-notice">ℹ️ Ollama with CUDA on ' + escapeHtml(sys.gpu || 'your GPU') + ' will run these models near-instantly.</div>';
    } else if (!_hasGpu) {
      html += '<div class="hw-metal-notice">ℹ️ No GPU detected — local models will run on CPU. Pick smaller (1B–7B) models for best results.</div>';
    }

    // ══ SECTION 3: Recommended Local Models ══════════════════════
    html += '<div class="co-section">';
    html += '<h3>🤖 Recommended Local Models <span style="font-size:11px;color:var(--text-muted);font-weight:400;">via llmfit - ' + _accelLabel + '-accelerated</span></h3>';

    if (!data.ollamaInstalled) {
      html += '<div class="co-ollama-prompt">';
      html += '<div style="font-size:13px;color:#a78bfa;font-weight:600;">⚠️ Ollama not installed -- install to run models locally (free!)</div>';
      html += '<div class="co-ollama-cmd">' + escapeHtml(_ollamaInstall) + '</div>';
      // JSON.stringify(_ollamaInstall) produces "..." with literal " which
      // collides with the onclick="..." double-quoted attribute and breaks
      // out of the attribute scope (rendering raw JS inside the button).
      // Encode " as &quot; so the HTML parser treats it as a literal quote
      // inside the attribute, then the JS still sees a proper string.
      var _esc1 = JSON.stringify(_ollamaInstall).replace(/"/g, '&quot;');
      html += '<button class="co-action-btn" onclick="navigator.clipboard.writeText(' + _esc1 + ');this.textContent=\'✅ Copied!\';setTimeout(()=>this.textContent=\'📋 Copy Install Command\',2000);">📋 Copy Install Command</button>';
      html += '</div>';
    }

    var models = data.localModels || [];
    if (models.length > 0) {
      models.slice(0, 5).forEach(function(m) {
        var badgeType = (m.useCase || '').toLowerCase().indexOf('cod') !== -1 ? 'coding' : 'chat';
        var _accelMult = _isApple ? 3.5 : _isCuda ? 3.0 : _isAmdGpu ? 2.0 : 1.0;
        var metalTps = m.estimatedTps ? Math.round(m.estimatedTps * _accelMult) + ' tok/s*' : '--';
        var ollamaCmd = 'ollama pull ' + (m.ollamaName || m.name.toLowerCase().replace(/-instruct.*/i,'').replace(/[^a-z0-9.-]/g,'-'));
        html += '<div class="model-card">';
        html += '<div class="model-card-header">';
        html += '<div class="model-card-name">' + m.name + '</div>';
        html += '<span class="model-badge ' + badgeType + '">' + (m.useCase || (badgeType === 'coding' ? 'Coding' : 'Chat')) + '</span>';
        html += '</div>';
        html += '<div class="model-card-stats">';
        html += '<div class="model-card-stat"><span class="model-card-stat-label">Score</span><span class="model-card-stat-value">' + (m.score || '--') + '</span></div>';
        html += '<div class="model-card-stat"><span class="model-card-stat-label">Speed (' + _accelLabel + ')</span><span class="model-card-stat-value">' + metalTps + '</span></div>';
        html += '<div class="model-card-stat"><span class="model-card-stat-label">RAM</span><span class="model-card-stat-value">' + (m.ramRequired || (m.memoryRequiredGb ? m.memoryRequiredGb + 'GB' : '--')) + '</span></div>';
        if (m.savingsEstimate) html += '<div class="model-card-stat"><span class="model-card-stat-label">Savings est.</span><span class="model-card-stat-value" style="color:#4ade80;">' + m.savingsEstimate + '</span></div>';
        html += '</div>';
        html += '<div class="model-install-cmd" onclick="navigator.clipboard.writeText(\'' + ollamaCmd + '\');this.querySelector(\'span.cmd-text\').textContent=\'✅ Copied!\';setTimeout(()=>this.querySelector(\'span.cmd-text\').textContent=\'' + ollamaCmd + '\',2000);">';
        html += '<span class="cmd-text">' + ollamaCmd + '</span>';
        html += '<span style="color:#4ade80;font-size:10px;flex-shrink:0;">📥 Copy</span>';
        html += '</div>';
        if (m.fullName) html += '<a style="display:block;margin-top:5px;font-size:10px;color:#60a5fa;text-decoration:none;" href="https://huggingface.co/' + m.fullName + '" target="_blank">🔗 View on HuggingFace</a>';
        html += '</div>';
      });
      html += '<div style="font-size:10px;color:var(--text-muted);margin-top:4px;">* Speed estimated with Ollama ' + _accelLabel + ' backend</div>';
    } else {
      html += '<div style="color:var(--text-muted);font-size:13px;padding:10px 0;">llmfit not available -- install with: <code>pip install llmfit</code></div>';
    }
    html += '</div>';

    // ══ SECTION 4: Task Recommendations ══════════════════════════
    var taskRecs = data.taskRecommendations || [];
    if (taskRecs.length > 0) {
      html += '<div class="co-section">';
      html += '<h3>📋 Task Recommendations</h3>';
      taskRecs.forEach(function(rec) {
        html += '<div class="task-rec">';
        html += '<div class="task-rec-title">' + rec.task + '</div>';
        if (rec.estimatedSavings) html += '<div class="task-rec-savings">' + rec.estimatedSavings + '</div>';
        html += '<div class="task-rec-arrow">';
        if (rec.currentModel) html += '<span style="color:var(--text-muted);">' + rec.currentModel + '</span>';
        if (rec.suggestedLocal) html += ' -> <span style="color:#4ade80;font-weight:600;">' + rec.suggestedLocal + '</span>';
        else html += ' -> <span style="color:#4ade80;font-weight:600;">keep frontier ✓</span>';
        html += '</div>';
        if (rec.reason) html += '<div class="task-rec-reason">' + rec.reason + '</div>';
        html += '</div>';
      });
      html += '</div>';
    }

    // ══ SECTION 5: Quick Actions ══════════════════════════════════
    html += '<div class="co-section">';
    html += '<h3>⚙️ Quick Actions</h3>';
    html += '<div style="display:flex;gap:8px;flex-wrap:wrap;">';
    var _esc2 = JSON.stringify(_ollamaInstall).replace(/"/g, '&quot;');
    html += '<button class="co-action-btn" style="width:auto;padding:6px 14px;" onclick="navigator.clipboard.writeText(' + _esc2 + ');this.textContent=\'✅ Copied!\';setTimeout(()=>this.textContent=\'📋 Install Ollama\',2000);">📋 Install Ollama</button>';
    html += '<button class="co-action-btn secondary" style="width:auto;padding:6px 14px;" onclick="navigator.clipboard.writeText(\'ollama serve\');this.textContent=\'✅ Copied!\';setTimeout(()=>this.textContent=\'📋 ollama serve\',2000);">📋 ollama serve</button>';
    html += '<a class="co-action-btn secondary" style="width:auto;padding:6px 14px;text-decoration:none;display:inline-block;" href="https://ollama.com/search" target="_blank">🔍 Browse Models</a>';
    html += '</div>';
    html += '</div>';

    body.innerHTML = html;
    document.getElementById('comp-modal-footer').textContent = 'Auto-refreshing - Last updated: ' + new Date().toLocaleTimeString() + ' - ' + (data.llmfitAvailable ? 'llmfit ✓' : 'no llmfit') + ' - ' + _accelLabel + ' backend';
  }).catch(function(e) {
    if (!isCompModalActive(expectedNodeId)) return;
    if (!isRefresh) {
      document.getElementById('comp-modal-body').innerHTML = '<div style="text-align:center;padding:20px;color:var(--text-error);">Failed to load cost optimizer: ' + e.message + '</div>';
    }
  });
}

var _gwRefreshTimer = null;
var _gwPage = 0;

// ═══ TIME TRAVEL ═══════════════════════════════════════════════════
var _timelineData = null;  // {days: [{date, label, events, hasMemory, hours}], today: 'YYYY-MM-DD'}
var _currentTimeContext = null;  // {date: 'YYYY-MM-DD', hour: null} or null for "now"
var _timeTravelMode = false;

function toggleTimeTravelMode() {
  _timeTravelMode = !_timeTravelMode;
  var toggle = document.getElementById('time-travel-toggle');
  var bar = document.getElementById('time-travel-bar');
  
  if (_timeTravelMode) {
    toggle.classList.add('active');
    bar.classList.add('active');
    loadTimelineData();
  } else {
    toggle.classList.remove('active');
    bar.classList.remove('active');
    _currentTimeContext = null;
    // Reload current component data
    reloadCurrentComponent();
  }
}

function loadTimelineData() {
  fetch('/api/timeline').then(function(r) { return r.json(); }).then(function(data) {
    _timelineData = data;
    // Set initial time to "now"
    _currentTimeContext = null;
    updateTimeDisplay();
    updateSliderPosition();
  }).catch(function(e) {
    console.error('Failed to load timeline:', e);
  });
}

function timeTravel(direction) {
  if (!_timelineData || !_timelineData.days) return;
  
  var days = _timelineData.days;
  var currentDate = _currentTimeContext ? _currentTimeContext.date : _timelineData.today;
  var currentIndex = days.findIndex(function(d) { return d.date === currentDate; });
  
  if (direction === 'prev-day' && currentIndex > 0) {
    _currentTimeContext = {date: days[currentIndex - 1].date, hour: null};
  } else if (direction === 'next-day' && currentIndex < days.length - 1) {
    _currentTimeContext = {date: days[currentIndex + 1].date, hour: null};
  } else if (direction === 'now') {
    _currentTimeContext = null;
  }
  
  updateTimeDisplay();
  updateSliderPosition();
  reloadCurrentComponent();
}

function onTimeSliderClick(event) {
  if (!_timelineData || !_timelineData.days) return;
  
  var slider = document.getElementById('time-slider');
  var rect = slider.getBoundingClientRect();
  var percent = (event.clientX - rect.left) / rect.width;
  
  var days = _timelineData.days;
  var index = Math.floor(percent * days.length);
  index = Math.max(0, Math.min(index, days.length - 1));
  
  _currentTimeContext = {date: days[index].date, hour: null};
  updateTimeDisplay();
  updateSliderPosition();
  reloadCurrentComponent();
}

function updateTimeDisplay() {
  var display = document.getElementById('time-display');
  if (!display) return;
  
  if (!_currentTimeContext) {
    display.textContent = 'Live (Now)';
    display.style.color = 'var(--text-accent)';
  } else {
    var day = _timelineData.days.find(function(d) { return d.date === _currentTimeContext.date; });
    if (day) {
      display.textContent = day.label + ' (' + day.events + ' events)';
      display.style.color = 'var(--text-secondary)';
    }
  }
}

function updateSliderPosition() {
  var thumb = document.getElementById('time-slider-thumb');
  if (!thumb || !_timelineData) return;
  
  if (!_currentTimeContext) {
    // "Now" - position at the end
    thumb.style.left = '100%';
  } else {
    var days = _timelineData.days;
    var index = days.findIndex(function(d) { return d.date === _currentTimeContext.date; });
    if (index >= 0) {
      var percent = (index / (days.length - 1)) * 100;
      thumb.style.left = percent + '%';
    }
  }
}

function reloadCurrentComponent() {
  // Re-trigger the current component modal with time context
  var overlay = document.getElementById('comp-modal-overlay');
  if (overlay && overlay.classList.contains('open')) {
    var body = document.getElementById('comp-modal-body');
    body.innerHTML = '<div style="text-align:center;padding:40px;"><div class="pulse"></div> Loading ' + (_currentTimeContext ? 'historical' : 'current') + ' data...</div>';
    
    if (window._currentComponentId) {
      loadComponentWithTimeContext(window._currentComponentId);
    }
  }
}

function loadCostOptimizerDataWithTime() {
  var body = document.getElementById('comp-modal-body');
  var timeContext = _currentTimeContext ? ' (' + _currentTimeContext.date + ')' : '';
  body.innerHTML = '<div style="text-align:center;padding:20px;"><div style="font-size:48px;margin-bottom:16px;">💰</div><div style="font-size:16px;font-weight:600;margin-bottom:8px;">Cost Optimizer' + timeContext + '</div><div style="color:var(--text-muted);">Historical cost analysis coming soon</div><div style="margin-top:8px;font-size:12px;color:var(--text-muted);text-transform:uppercase;">optimizer</div></div>';
  document.getElementById('comp-modal-footer').textContent = 'Time travel: ' + (_currentTimeContext ? _currentTimeContext.date : 'Live');
}

function loadAutomationAdvisorDataWithTime() {
  var body = document.getElementById('comp-modal-body');
  var timeContext = _currentTimeContext ? ' (' + _currentTimeContext.date + ')' : '';
  
  if (_currentTimeContext) {
    body.innerHTML = '<div style="text-align:center;padding:20px;"><div style="font-size:48px;margin-bottom:16px;">🧠</div><div style="font-size:16px;font-weight:600;margin-bottom:8px;">Automation Advisor' + timeContext + '</div><div style="color:var(--text-muted);">Historical pattern analysis coming soon</div><div style="margin-top:8px;font-size:12px;color:var(--text-muted);text-transform:uppercase;">advisor</div></div>';
    document.getElementById('comp-modal-footer').textContent = 'Time travel: ' + _currentTimeContext.date;
    return;
  }
  
  body.innerHTML = '<div style="text-align:center;padding:40px;"><div style="font-size:24px;margin-bottom:20px;">🧠 Loading automation analysis...</div></div>';
  document.getElementById('comp-modal-footer').textContent = 'Live';
  
  fetch('/api/automation-analysis').then(function(r){return r.json();}).then(function(data) {
    var html = '<div style="padding:20px;">';
    html += '<div style="text-align:center;margin-bottom:30px;"><div style="font-size:48px;margin-bottom:12px;">🧠</div><h2 style="margin:0;font-size:20px;">Automation Advisor</h2><p style="color:var(--text-muted);margin:8px 0 0 0;">Analyzing patterns to suggest new automations</p></div>';
    
    if (data.patterns && data.patterns.length > 0) {
      html += '<h3 style="color:var(--text-primary);border-bottom:2px solid var(--border-primary);padding-bottom:8px;margin-bottom:16px;">🔍 Detected Patterns</h3>';
      data.patterns.forEach(function(pattern) {
        var priorityColor = pattern.priority === 'high' ? '#f44336' : pattern.priority === 'medium' ? '#ff9800' : '#4caf50';
        html += '<div style="background:var(--bg-hover);border-radius:8px;padding:16px;margin-bottom:16px;border-left:4px solid ' + priorityColor + ';">';
        html += '<div style="font-weight:600;margin-bottom:8px;">' + pattern.title + '</div>';
        html += '<div style="color:var(--text-muted);margin-bottom:12px;">' + pattern.description + '</div>';
        html += '<div style="font-size:12px;color:var(--text-muted);">Frequency: ' + pattern.frequency + ' • Confidence: ' + pattern.confidence + '%</div>';
        html += '</div>';
      });
    }
    
    if (data.suggestions && data.suggestions.length > 0) {
      html += '<h3 style="color:var(--text-primary);border-bottom:2px solid var(--border-primary);padding-bottom:8px;margin-bottom:16px;">💡 Automation Suggestions</h3>';
      data.suggestions.forEach(function(suggestion) {
        var typeIcon = suggestion.type === 'cron' ? '⏰' : suggestion.type === 'skill' ? '[dev]' : '🔧';
        html += '<div style="background:var(--bg-hover);border-radius:8px;padding:16px;margin-bottom:16px;">';
        html += '<div style="display:flex;align-items:center;margin-bottom:8px;"><span style="font-size:20px;margin-right:8px;">' + typeIcon + '</span>';
        html += '<span style="font-weight:600;">' + suggestion.title + '</span></div>';
        html += '<div style="color:var(--text-muted);margin-bottom:12px;">' + suggestion.description + '</div>';
        if (suggestion.implementation) {
          html += '<div style="background:var(--bg-primary);padding:8px;border-radius:4px;font-family:monospace;font-size:12px;color:var(--text-muted);margin-bottom:8px;">' + suggestion.implementation + '</div>';
        }
        html += '<div style="font-size:12px;color:var(--text-muted);">Impact: ' + suggestion.impact + ' • Effort: ' + suggestion.effort + '</div>';
        html += '</div>';
      });
    }
    
    if (!data.patterns || data.patterns.length === 0) {
      html += '<div style="text-align:center;padding:40px;color:var(--text-muted);">';
      html += '<div style="font-size:48px;margin-bottom:16px;">🌱</div>';
      html += '<h3>No patterns detected yet</h3>';
      html += '<p>Continue using the agent and check back later for automation suggestions.</p>';
      html += '</div>';
    }
    
    html += '</div>';
    body.innerHTML = html;
  }).catch(function(e) {
    body.innerHTML = '<div style="text-align:center;padding:40px;color:var(--text-muted);"><div style="font-size:48px;margin-bottom:16px;">⚠️</div><h3>Analysis Unavailable</h3><p>Unable to load automation analysis: ' + e.message + '</p></div>';
  });
}

function loadComponentWithTimeContext(nodeId) {
  var c = COMP_MAP[nodeId];
  if (!c) return;
  
  // Clear existing refresh timers
  if (_tgRefreshTimer) { clearInterval(_tgRefreshTimer); _tgRefreshTimer = null; }
  if (_imsgRefreshTimer) { clearInterval(_imsgRefreshTimer); _imsgRefreshTimer = null; }
  if (_discordRefreshTimer) { clearInterval(_discordRefreshTimer); _discordRefreshTimer = null; }
  if (_slackRefreshTimer) { clearInterval(_slackRefreshTimer); _slackRefreshTimer = null; }
  if (_gcRefreshTimer) { clearInterval(_gcRefreshTimer); _gcRefreshTimer = null; }
  if (_mstRefreshTimer) { clearInterval(_mstRefreshTimer); _mstRefreshTimer = null; }
  if (_mmRefreshTimer) { clearInterval(_mmRefreshTimer); _mmRefreshTimer = null; }
  if (_gwRefreshTimer) { clearInterval(_gwRefreshTimer); _gwRefreshTimer = null; }
  if (_brainRefreshTimer) { clearInterval(_brainRefreshTimer); _brainRefreshTimer = null; }
  if (_toolRefreshTimer) { clearInterval(_toolRefreshTimer); _toolRefreshTimer = null; }
  if (_costOptimizerRefreshTimer) { clearInterval(_costOptimizerRefreshTimer); _costOptimizerRefreshTimer = null; }
  if (_webchatRefreshTimer) { clearInterval(_webchatRefreshTimer); _webchatRefreshTimer = null; }
  if (_ircRefreshTimer) { clearInterval(_ircRefreshTimer); _ircRefreshTimer = null; }
  if (_bbRefreshTimer) { clearInterval(_bbRefreshTimer); _bbRefreshTimer = null; }
  
  // Load data based on component type
  if (nodeId === 'node-telegram') {
    loadTelegramMessagesWithTime();
  } else if (nodeId === 'node-gateway') {
    loadGatewayDataWithTime();
  } else if (nodeId === 'node-brain') {
    loadBrainDataWithTime();
  } else if (nodeId === 'node-cost-optimizer') {
    loadCostOptimizerDataWithTime();
  } else if (nodeId === 'node-automation-advisor') {
    loadAutomationAdvisorDataWithTime();
  } else if (c.type === 'tool') {
    var toolKey = nodeId.replace('node-', '');
    loadToolDataWithTime(toolKey, c);
  } else {
    // Default component view
    var body = document.getElementById('comp-modal-body');
    var timeContext = _currentTimeContext ? ' (' + _currentTimeContext.date + ')' : '';
    body.innerHTML = '<div style="text-align:center;padding:20px;"><div style="font-size:48px;margin-bottom:16px;">' + c.icon + '</div><div style="font-size:16px;font-weight:600;margin-bottom:8px;">' + c.name + timeContext + '</div><div style="color:var(--text-muted);">Historical view coming soon</div><div style="margin-top:8px;font-size:12px;color:var(--text-muted);text-transform:uppercase;">' + c.type + '</div></div>';
    document.getElementById('comp-modal-footer').textContent = 'Time travel: ' + (_currentTimeContext ? _currentTimeContext.date : 'Live');
  }
}

function loadGatewayData(isRefresh) {
  var expectedNodeId = 'node-gateway';
  fetch('/api/component/gateway?limit=50&offset=' + (_gwPage * 50)).then(function(r) { return r.json(); }).then(function(data) {
    if (!isCompModalActive(expectedNodeId)) return;
    var body = document.getElementById('comp-modal-body');
    var s = data.stats || {};
    var cfg = s.config || {};
    var routes = data.routes || [];

    // Honesty: when everything is zero AND no routing events, the gateway
    // hasn't synced any data yet (cloud user with bridge not running, or
    // freshly installed node). Showing a row of misleading "0"s makes users
    // think the gateway is broken; show a clear awaiting-data state instead.
    var _allZero = !(s.today_messages||0) && !(s.today_heartbeats||0) &&
                   !(s.today_crons||0) && !(s.today_errors||0) &&
                   !(s.active_sessions||0) && routes.length === 0;
    if (_allZero) {
      var html0 = '<div style="text-align:center;padding:32px 24px;">';
      html0 += '<div style="font-size:36px;margin-bottom:10px;opacity:0.6;">🌐</div>';
      html0 += '<div style="font-size:15px;font-weight:600;color:var(--text-primary);margin-bottom:6px;">Gateway not yet synced</div>';
      html0 += '<div style="font-size:12px;color:var(--text-muted);max-width:380px;margin:0 auto;line-height:1.5;">No routing events have been ingested yet. The gateway will appear here once your agent starts handling messages, heartbeats, or cron triggers.</div>';
      if (s.uptime || s.last_seen_at) {
        html0 += '<div style="margin-top:12px;font-size:11px;color:var(--text-muted);">⏱️ Last seen: ' + escapeHtml(s.uptime || s.last_seen_at) + '</div>';
      }
      html0 += '</div>';
      document.getElementById('comp-modal-body').innerHTML = html0;
      document.getElementById('comp-modal-footer').textContent =
        'Auto-refreshing - Last updated: ' + new Date().toLocaleTimeString() + ' - awaiting data';
      return;
    }

    // Top stats row
    var html = '<div style="display:flex;gap:10px;flex-wrap:wrap;margin-bottom:12px;">';
    html += '<div style="flex:1;min-width:70px;background:var(--bg-secondary);border-radius:8px;padding:10px 12px;text-align:center;"><div style="font-size:20px;font-weight:700;color:var(--text-primary);">' + (s.today_messages||0) + '</div><div style="font-size:10px;color:var(--text-muted);text-transform:uppercase;">Messages</div></div>';
    html += '<div style="flex:1;min-width:70px;background:var(--bg-secondary);border-radius:8px;padding:10px 12px;text-align:center;"><div style="font-size:20px;font-weight:700;color:var(--text-primary);">' + (s.today_heartbeats||0) + '</div><div style="font-size:10px;color:var(--text-muted);text-transform:uppercase;">Heartbeats</div></div>';
    html += '<div style="flex:1;min-width:70px;background:var(--bg-secondary);border-radius:8px;padding:10px 12px;text-align:center;"><div style="font-size:20px;font-weight:700;color:var(--text-primary);">' + (s.today_crons||0) + '</div><div style="font-size:10px;color:var(--text-muted);text-transform:uppercase;">Cron</div></div>';
    html += '<div style="flex:1;min-width:70px;background:var(--bg-secondary);border-radius:8px;padding:10px 12px;text-align:center;"><div style="font-size:20px;font-weight:700;color:' + ((s.today_errors||0) > 0 ? 'var(--text-error)' : 'var(--text-primary)') + ';">' + (s.today_errors||0) + '</div><div style="font-size:10px;color:var(--text-muted);text-transform:uppercase;">Errors</div></div>';
    html += '<div style="flex:1;min-width:70px;background:var(--bg-secondary);border-radius:8px;padding:10px 12px;text-align:center;"><div style="font-size:20px;font-weight:700;color:#3b82f6;">' + (s.active_sessions||0) + '</div><div style="font-size:10px;color:var(--text-muted);text-transform:uppercase;">Active Sessions</div></div>';
    html += '</div>';

    // Config summary & uptime
    html += '<div style="display:flex;gap:8px;margin-bottom:14px;flex-wrap:wrap;">';
    if (s.uptime) html += '<span style="background:var(--bg-secondary);padding:3px 10px;border-radius:12px;font-size:11px;color:var(--text-muted);">⏱️ Up since: ' + escapeHtml(s.uptime) + '</span>';
    if (cfg.channels && cfg.channels.length) html += '<span style="background:var(--bg-secondary);padding:3px 10px;border-radius:12px;font-size:11px;color:var(--text-muted);">📡 Channels: ' + cfg.channels.join(', ') + '</span>';
    if (cfg.heartbeat) html += '<span style="background:var(--bg-secondary);padding:3px 10px;border-radius:12px;font-size:11px;color:var(--text-muted);">💓 Heartbeat: ' + cfg.heartbeat + '</span>';
    if (cfg.max_concurrent) html += '<span style="background:var(--bg-secondary);padding:3px 10px;border-radius:12px;font-size:11px;color:var(--text-muted);">⚡ Max concurrent: ' + cfg.max_concurrent + '</span>';
    if (cfg.max_subagents) html += '<span style="background:var(--bg-secondary);padding:3px 10px;border-radius:12px;font-size:11px;color:var(--text-muted);">🐝 Max subagents: ' + cfg.max_subagents + '</span>';
    html += '</div>';

    // Restart history
    var restarts = s.restarts || [];
    if (restarts.length > 0) {
      html += '<div style="margin-bottom:12px;font-size:11px;color:var(--text-muted);"><strong>🔄 Restarts today:</strong> ';
      restarts.forEach(function(r) { if(r) html += '<span style="margin-right:8px;">' + new Date(r).toLocaleTimeString([],{hour:"2-digit",minute:"2-digit"}) + '</span>'; });
      html += '</div>';
    }

    if (routes.length === 0) {
      html += '<div style="text-align:center;padding:20px;color:var(--text-muted);">No routing events found today</div>';
    } else {
      html += '<div style="display:flex;flex-direction:column;gap:6px;">';
      routes.forEach(function(r) {
        var badge = '📨';
        var badgeColor = '#3b82f6';
        if (r.type === 'heartbeat') { badge = '💓'; badgeColor = '#ec4899'; }
        else if (r.type === 'cron') { badge = '⏰'; badgeColor = '#f59e0b'; }
        else if (r.type === 'subagent') { badge = '🐝'; badgeColor = '#8b5cf6'; }
        else if (r.from === 'telegram') { badge = '📱'; badgeColor = '#3b82f6'; }
        else if (r.from === 'whatsapp') { badge = '📲'; badgeColor = '#22c55e'; }

        var status = r.status === 'error' ? '❌' : '✅';
        var ts = r.timestamp ? new Date(r.timestamp).toLocaleTimeString([], {hour:'2-digit',minute:'2-digit',second:'2-digit'}) : '';
        var model = r.to || '';
        if (model.length > 20) model = model.substring(0, 18) + '…';
        var session = r.session || '';
        if (session.length > 20) session = session.substring(0, 18) + '…';

        html += '<div style="display:flex;align-items:center;gap:8px;padding:8px 10px;background:var(--bg-secondary);border-radius:8px;border:1px solid var(--border-secondary);font-size:12px;">';
        html += '<span style="font-size:16px;">' + badge + '</span>';
        html += '<span style="color:var(--text-tertiary);min-width:60px;">' + ts + '</span>';
        html += '<span style="color:var(--text-secondary);font-weight:600;">' + escapeHtml(r.from || '?') + '</span>';
        html += '<span style="color:var(--text-muted);">-></span>';
        html += '<span style="color:var(--text-accent);font-weight:500;flex:1;">' + escapeHtml(model) + '</span>';
        if (session) html += '<span style="color:var(--text-muted);font-size:11px;">' + escapeHtml(session) + '</span>';
        html += '<span>' + status + '</span>';
        html += '</div>';
      });
      html += '</div>';
    }

    if (data.total > routes.length) {
      html += '<div style="text-align:center;margin-top:12px;font-size:12px;color:var(--text-muted);">' + routes.length + ' of ' + data.total + ' events shown</div>';
    }

    body.innerHTML = html;
    document.getElementById('comp-modal-footer').textContent = 'Auto-refreshing - Last updated: ' + new Date().toLocaleTimeString() + ' - ' + (data.total||0) + ' events today';
  }).catch(function(e) {
    if (!isCompModalActive(expectedNodeId)) return;
    if (!isRefresh) {
      document.getElementById('comp-modal-body').innerHTML = '<div style="text-align:center;padding:20px;color:var(--text-error);">Failed to load gateway data</div>';
    }
  });
}

var _toolRefreshTimer = null;
var _costOptimizerRefreshTimer = null;
var TOOL_COLORS = {
  'session': '#1565C0', 'exec': '#E65100', 'browser': '#6A1B9A',
  'search': '#00695C', 'cron': '#546E7A', 'tts': '#F9A825', 'memory': '#283593'
};

function _fmtToolTs(ts) {
  if (!ts) return '';
  var d = new Date(ts);
  if (isNaN(d.getTime())) return '';
  return d.toLocaleTimeString([], {hour:'2-digit',minute:'2-digit',second:'2-digit'});
}
function _fmtToolDate(ts) {
  if (!ts) return '';
  var d = new Date(ts);
  if (isNaN(d.getTime())) return '';
  return d.toLocaleDateString([], {month:'short',day:'numeric'}) + ' ' + d.toLocaleTimeString([], {hour:'2-digit',minute:'2-digit'});
}
function _timeAgo(ts) {
  if (!ts) return '';
  var secs = (Date.now() - new Date(ts).getTime()) / 1000;
  if (secs < 0) secs = 0;
  if (secs < 60) return Math.floor(secs) + 's ago';
  if (secs < 3600) return Math.floor(secs/60) + 'm ago';
  if (secs < 86400) return Math.floor(secs/3600) + 'h ago';
  return Math.floor(secs/86400) + 'd ago';
}

var _toolDataCache = {};
var _toolCacheAge = {};

function loadToolData(toolKey, comp, isRefresh) {
  // If we have cached data and this is first open, skip loading spinner
  // The fetch below will update with fresh data
  var _expectedNodeId = 'node-' + toolKey;
  fetch('/api/component/tool/' + toolKey).then(function(r) { return r.json(); }).then(function(data) {
    // Guard: don't render if user switched to a different modal
    if (!isCompModalActive(_expectedNodeId)) return;
    _toolDataCache[toolKey] = data;
    _toolCacheAge[toolKey] = Date.now();
    var body = document.getElementById('comp-modal-body');
    var s = data.stats || {};
    var events = data.events || [];
    var color = TOOL_COLORS[toolKey] || '#555';
    var html = '';

    // ─── SESSION MODAL ─────────────────────────────────
    if (toolKey === 'session') {
      var agents = data.subagents || [];
      var active = agents.filter(function(a){return a.status==='active';}).length;
      var idle = agents.filter(function(a){return a.status==='idle';}).length;
      var stale = agents.filter(function(a){return a.status==='stale';}).length;

      html += '<div style="display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin-bottom:16px;">';
      html += '<div style="background:var(--bg-secondary);border-radius:10px;padding:12px;text-align:center;"><div style="font-size:24px;font-weight:700;color:#22c55e;">' + active + '</div><div style="font-size:10px;color:var(--text-muted);text-transform:uppercase;">Active</div></div>';
      html += '<div style="background:var(--bg-secondary);border-radius:10px;padding:12px;text-align:center;"><div style="font-size:24px;font-weight:700;color:#f59e0b;">' + idle + '</div><div style="font-size:10px;color:var(--text-muted);text-transform:uppercase;">Idle</div></div>';
      html += '<div style="background:var(--bg-secondary);border-radius:10px;padding:12px;text-align:center;"><div style="font-size:24px;font-weight:700;color:#ef4444;">' + stale + '</div><div style="font-size:10px;color:var(--text-muted);text-transform:uppercase;">Stale</div></div>';
      html += '<div style="background:var(--bg-secondary);border-radius:10px;padding:12px;text-align:center;"><div style="font-size:24px;font-weight:700;color:var(--text-primary);">' + (s.today_calls||0) + '</div><div style="font-size:10px;color:var(--text-muted);text-transform:uppercase;">Calls Today</div></div>';
      html += '</div>';

      if (agents.length > 0) {
        html += '<div style="font-size:12px;font-weight:600;color:var(--text-muted);text-transform:uppercase;letter-spacing:1px;margin-bottom:8px;">Sub-Agents</div>';
        html += '<div style="display:flex;flex-direction:column;gap:6px;max-height:50vh;overflow-y:auto;">';
        agents.forEach(function(a) {
          var dotColor = a.status==='active' ? '#22c55e' : a.status==='idle' ? '#f59e0b' : '#ef4444';
          var dotShadow = a.status==='active' ? 'box-shadow:0 0 6px rgba(34,197,94,0.6);' : '';
          html += '<div style="display:flex;align-items:flex-start;gap:10px;padding:10px 12px;background:var(--bg-secondary);border-radius:10px;border:1px solid var(--border-secondary);">';
          html += '<div style="width:10px;height:10px;border-radius:50%;background:'+dotColor+';margin-top:4px;flex-shrink:0;'+dotShadow+'"></div>';
          html += '<div style="flex:1;min-width:0;">';
          html += '<div style="display:flex;justify-content:space-between;align-items:center;">';
          html += '<span style="font-weight:600;font-size:13px;color:var(--text-primary);">' + escapeHtml(a.displayName || a.id || '?') + '</span>';
          html += '<span style="font-size:10px;color:var(--text-muted);">' + _timeAgo(a.updatedAt) + '</span>';
          html += '</div>';
          if (a.task) html += '<div style="font-size:12px;color:var(--text-secondary);margin-top:2px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">' + escapeHtml(a.task) + '</div>';
          var meta = [];
          if (a.model) meta.push(a.model);
          if (a.tokens) meta.push(a.tokens >= 1000 ? (a.tokens/1000).toFixed(1)+'K tok' : a.tokens+' tok');
          if (a.channel) meta.push(a.channel);
          if (meta.length > 0) html += '<div style="font-size:10px;color:var(--text-muted);margin-top:2px;">' + escapeHtml(meta.join(' - ')) + '</div>';
          if (a.lastMessage) html += '<div style="font-size:11px;color:var(--text-tertiary);margin-top:4px;font-style:italic;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">"' + escapeHtml(a.lastMessage.substring(0,120)) + '"</div>';
          html += '</div></div>';
        });
        html += '</div>';
      } else if (events.length > 0) {
        html += '<div style="font-size:12px;font-weight:600;color:var(--text-muted);text-transform:uppercase;letter-spacing:1px;margin-bottom:8px;">Recent Session Activity</div>';
        html += _renderEventList(events, toolKey, color);
      } else {
        html += '<div style="text-align:center;padding:30px;color:var(--text-muted);">No active sub-agents</div>';
      }

    // ─── EXEC MODAL ────────────────────────────────────
    } else if (toolKey === 'exec') {
      var running = data.running_commands || [];
      html += '<div style="display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin-bottom:16px;">';
      html += '<div style="background:var(--bg-secondary);border-radius:10px;padding:12px;text-align:center;"><div style="font-size:24px;font-weight:700;color:#f59e0b;">' + running.length + '</div><div style="font-size:10px;color:var(--text-muted);text-transform:uppercase;">Running</div></div>';
      html += '<div style="background:var(--bg-secondary);border-radius:10px;padding:12px;text-align:center;"><div style="font-size:24px;font-weight:700;color:var(--text-primary);">' + (s.today_calls||0) + '</div><div style="font-size:10px;color:var(--text-muted);text-transform:uppercase;">Total Today</div></div>';
      html += '<div style="background:var(--bg-secondary);border-radius:10px;padding:12px;text-align:center;"><div style="font-size:24px;font-weight:700;color:'+ ((s.today_errors||0)>0?'#ef4444':'var(--text-primary)') +';">' + (s.today_errors||0) + '</div><div style="font-size:10px;color:var(--text-muted);text-transform:uppercase;">Errors</div></div>';
      html += '</div>';

      if (running.length > 0) {
        html += '<div style="font-size:12px;font-weight:600;color:var(--text-muted);text-transform:uppercase;letter-spacing:1px;margin-bottom:8px;">⚡ Running Now</div>';
        running.forEach(function(cmd) {
          html += '<div style="padding:8px 12px;background:#E6510011;border:1px solid #E6510033;border-radius:8px;margin-bottom:6px;font-family:monospace;font-size:12px;">';
          html += '<div style="display:flex;justify-content:space-between;"><span style="color:var(--text-primary);font-weight:600;">$ ' + escapeHtml((cmd.command||'').substring(0,120)) + '</span>';
          html += '<span class="pulse" style="width:8px;height:8px;"></span></div>';
          if (cmd.pid) html += '<span style="font-size:10px;color:var(--text-muted);">PID: ' + cmd.pid + '</span>';
          html += '</div>';
        });
      }

      if (events.length > 0) {
        html += '<div style="font-size:12px;font-weight:600;color:var(--text-muted);text-transform:uppercase;letter-spacing:1px;margin:12px 0 8px;">Recent Commands</div>';
        html += '<div style="max-height:45vh;overflow-y:auto;display:flex;flex-direction:column;gap:4px;">';
        events.forEach(function(evt) {
          var ts = _fmtToolTs(evt.timestamp);
          var isErr = evt.status === 'error';
          var borderColor = isErr ? '#ef444433' : 'var(--border-secondary)';
          html += '<div style="padding:6px 10px;background:var(--bg-secondary);border:1px solid '+borderColor+';border-radius:6px;">';
          html += '<div style="display:flex;justify-content:space-between;align-items:center;">';
          html += '<code style="font-size:11px;color:var(--text-secondary);word-break:break-all;">$ ' + escapeHtml((evt.detail||'').substring(0,150)) + '</code>';
          html += '<span style="font-size:10px;color:var(--text-muted);white-space:nowrap;margin-left:8px;">' + ts + '</span>';
          html += '</div>';
          var meta = [];
          if (evt.duration_ms) meta.push(evt.duration_ms >= 1000 ? (evt.duration_ms/1000).toFixed(1)+'s' : evt.duration_ms+'ms');
          if (isErr) meta.push('<span style="color:#ef4444;">✗ error</span>');
          if (meta.length) html += '<div style="font-size:10px;color:var(--text-muted);margin-top:2px;">' + meta.join(' - ') + '</div>';
          html += '</div>';
        });
        html += '</div>';
      } else {
        html += '<div style="text-align:center;padding:20px;color:var(--text-muted);">No exec commands today</div>';
      }

    // ─── BROWSER/WEB MODAL ─────────────────────────────
    } else if (toolKey === 'browser') {
      var urls = data.recent_urls || [];
      html += '<div style="display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin-bottom:16px;">';
      html += '<div style="background:var(--bg-secondary);border-radius:10px;padding:12px;text-align:center;"><div style="font-size:24px;font-weight:700;color:var(--text-primary);">' + (s.today_calls||0) + '</div><div style="font-size:10px;color:var(--text-muted);text-transform:uppercase;">Actions Today</div></div>';
      html += '<div style="background:var(--bg-secondary);border-radius:10px;padding:12px;text-align:center;"><div style="font-size:24px;font-weight:700;color:#6A1B9A;">' + urls.length + '</div><div style="font-size:10px;color:var(--text-muted);text-transform:uppercase;">URLs Visited</div></div>';
      html += '<div style="background:var(--bg-secondary);border-radius:10px;padding:12px;text-align:center;"><div style="font-size:24px;font-weight:700;color:'+ ((s.today_errors||0)>0?'#ef4444':'var(--text-primary)') +';">' + (s.today_errors||0) + '</div><div style="font-size:10px;color:var(--text-muted);text-transform:uppercase;">Errors</div></div>';
      html += '</div>';

      if (urls.length > 0) {
        html += '<div style="font-size:12px;font-weight:600;color:var(--text-muted);text-transform:uppercase;letter-spacing:1px;margin-bottom:8px;">🌐 Recent URLs</div>';
        html += '<div style="display:flex;flex-direction:column;gap:4px;margin-bottom:14px;">';
        urls.forEach(function(u) {
          html += '<div style="padding:6px 10px;background:var(--bg-secondary);border-radius:6px;display:flex;align-items:center;gap:8px;">';
          html += '<span style="font-size:14px;">🔗</span>';
          html += '<a href="' + escapeHtml(u.url||'') + '" target="_blank" style="font-size:12px;color:var(--text-link);text-decoration:none;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;flex:1;">' + escapeHtml((u.url||'').substring(0,80)) + '</a>';
          html += '<span style="font-size:10px;color:var(--text-muted);white-space:nowrap;">' + _timeAgo(u.timestamp) + '</span>';
          html += '</div>';
        });
        html += '</div>';
      }

      if (events.length > 0) {
        html += '<div style="font-size:12px;font-weight:600;color:var(--text-muted);text-transform:uppercase;letter-spacing:1px;margin-bottom:8px;">Action Log</div>';
        html += '<div style="max-height:40vh;overflow-y:auto;display:flex;flex-direction:column;gap:4px;">';
        events.forEach(function(evt) {
          var ts = _fmtToolTs(evt.timestamp);
          var actionColors = {snapshot:'#3b82f6',navigate:'#8b5cf6',click:'#f59e0b',type:'#22c55e',screenshot:'#ec4899',open:'#06b6d4',act:'#f97316'};
          var ac = evt.action || 'unknown';
          var acColor = actionColors[ac] || '#6b7280';
          html += '<div style="padding:6px 10px;background:var(--bg-secondary);border-radius:6px;display:flex;align-items:center;gap:8px;font-size:12px;">';
          html += '<span style="background:'+acColor+'22;color:'+acColor+';padding:1px 8px;border-radius:4px;font-size:10px;font-weight:600;min-width:60px;text-align:center;">' + escapeHtml(ac) + '</span>';
          html += '<span style="color:var(--text-secondary);flex:1;white-space:pre-wrap;word-break:break-all;">' + escapeHtml(evt.detail||'') + '</span>';
          html += '<span style="color:var(--text-muted);font-size:10px;white-space:nowrap;">' + ts + '</span>';
          html += '</div>';
        });
        html += '</div>';
      } else {
        html += '<div style="text-align:center;padding:20px;color:var(--text-muted);">No browser actions today</div>';
      }

    // ─── SEARCH MODAL ──────────────────────────────────
    } else if (toolKey === 'search') {
      html += '<div style="display:grid;grid-template-columns:repeat(2,1fr);gap:10px;margin-bottom:16px;">';
      html += '<div style="background:var(--bg-secondary);border-radius:10px;padding:12px;text-align:center;"><div style="font-size:24px;font-weight:700;color:var(--text-primary);">' + (s.today_calls||0) + '</div><div style="font-size:10px;color:var(--text-muted);text-transform:uppercase;">Searches Today</div></div>';
      html += '<div style="background:var(--bg-secondary);border-radius:10px;padding:12px;text-align:center;"><div style="font-size:24px;font-weight:700;color:'+ ((s.today_errors||0)>0?'#ef4444':'var(--text-primary)') +';">' + (s.today_errors||0) + '</div><div style="font-size:10px;color:var(--text-muted);text-transform:uppercase;">Errors</div></div>';
      html += '</div>';

      if (events.length > 0) {
        html += '<div style="font-size:12px;font-weight:600;color:var(--text-muted);text-transform:uppercase;letter-spacing:1px;margin-bottom:8px;">Recent Searches</div>';
        html += '<div style="max-height:55vh;overflow-y:auto;display:flex;flex-direction:column;gap:6px;">';
        events.forEach(function(evt) {
          var ts = _fmtToolTs(evt.timestamp);
          html += '<div style="padding:10px 12px;background:var(--bg-secondary);border-radius:8px;border:1px solid var(--border-secondary);">';
          html += '<div style="display:flex;justify-content:space-between;align-items:flex-start;">';
          html += '<div style="font-size:14px;font-weight:600;color:var(--text-primary);">🔍 ' + escapeHtml(evt.detail || '') + '</div>';
          html += '<span style="font-size:10px;color:var(--text-muted);white-space:nowrap;margin-left:8px;">' + ts + '</span>';
          html += '</div>';
          if (evt.result_count !== undefined) html += '<div style="font-size:11px;color:var(--text-muted);margin-top:4px;">' + evt.result_count + ' results returned</div>';
          if (evt.status === 'error') html += '<div style="font-size:11px;color:#ef4444;margin-top:2px;">✗ Error</div>';
          html += '</div>';
        });
        html += '</div>';
      } else {
        html += '<div style="text-align:center;padding:30px;color:var(--text-muted);">No searches today</div>';
      }

    // ─── CRON MODAL ────────────────────────────────────
    } else if (toolKey === 'cron') {
      var jobs = data.cron_jobs || [];
      html += '<div style="display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin-bottom:16px;">';
      html += '<div style="background:var(--bg-secondary);border-radius:10px;padding:12px;text-align:center;"><div style="font-size:24px;font-weight:700;color:var(--text-primary);">' + jobs.length + '</div><div style="font-size:10px;color:var(--text-muted);text-transform:uppercase;">Cron Jobs</div></div>';
      var cronOk = jobs.filter(function(j){return j.lastStatus!=='error';}).length;
      var cronErr = jobs.filter(function(j){return j.lastStatus==='error';}).length;
      html += '<div style="background:var(--bg-secondary);border-radius:10px;padding:12px;text-align:center;"><div style="font-size:24px;font-weight:700;color:#22c55e;">' + cronOk + '</div><div style="font-size:10px;color:var(--text-muted);text-transform:uppercase;">Healthy</div></div>';
      html += '<div style="background:var(--bg-secondary);border-radius:10px;padding:12px;text-align:center;"><div style="font-size:24px;font-weight:700;color:'+(cronErr>0?'#ef4444':'var(--text-primary)')+';">' + cronErr + '</div><div style="font-size:10px;color:var(--text-muted);text-transform:uppercase;">Errors</div></div>';
      html += '</div>';

      if (jobs.length > 0) {
        html += '<div style="font-size:12px;font-weight:600;color:var(--text-muted);text-transform:uppercase;letter-spacing:1px;margin-bottom:8px;">Scheduled Jobs</div>';
        html += '<div style="display:flex;flex-direction:column;gap:6px;max-height:55vh;overflow-y:auto;">';
        jobs.forEach(function(j) {
          var isErr = j.lastStatus === 'error';
          var borderLeft = isErr ? '3px solid #ef4444' : '3px solid #22c55e';
          html += '<div style="padding:10px 14px;background:var(--bg-secondary);border-radius:8px;border-left:'+borderLeft+';border:1px solid var(--border-secondary);border-left:'+borderLeft+';">';
          html += '<div style="display:flex;justify-content:space-between;align-items:center;">';
          html += '<span style="font-weight:600;font-size:13px;color:var(--text-primary);">' + escapeHtml(j.name || j.task || j.id || '?') + '</span>';
          html += '<span style="padding:2px 8px;border-radius:4px;font-size:10px;font-weight:600;background:' + (isErr ? 'var(--bg-error);color:#ef4444' : 'var(--bg-success);color:#22c55e') + ';">' + (isErr ? 'ERROR' : 'OK') + '</span>';
          html += '</div>';
          var exprStr = typeof j.expr === 'object' ? (j.expr.expr || j.expr.at || ('every ' + Math.round((j.expr.everyMs||0)/60000) + 'm') || JSON.stringify(j.expr)) : (j.expr || j.schedule || '');
          // Show human-readable schedule if we can parse the cron expression,
          // with the raw spec underneath in muted monospace for power users.
          // Non-tech users can't parse "0 */6 * * *" — they need "every 6 hours".
          var human = (typeof cronToHuman === 'function' && /\d/.test(exprStr || '')) ? cronToHuman(exprStr) : '';
          if (human) {
            html += '<div style="font-size:12px;color:var(--text-secondary);margin-top:4px;"><strong>Runs:</strong> ' + escapeHtml(human) + '</div>';
            html += '<div style="font-family:monospace;font-size:10px;color:var(--text-muted);margin-top:2px;opacity:0.7;">' + escapeHtml(exprStr) + '</div>';
          } else {
            html += '<div style="font-family:monospace;font-size:11px;color:var(--text-accent);margin-top:4px;">' + escapeHtml(exprStr) + '</div>';
          }
          var meta = [];
          if (j.lastRun) meta.push('Last: ' + _fmtToolDate(j.lastRun));
          if (j.nextRun) meta.push('Next: ' + _fmtToolDate(j.nextRun));
          if (j.channel) meta.push('-> ' + j.channel);
          if (meta.length) html += '<div style="font-size:10px;color:var(--text-muted);margin-top:4px;">' + escapeHtml(meta.join(' - ')) + '</div>';
          if (isErr && j.lastError) html += '<div style="font-size:11px;color:#ef4444;margin-top:4px;background:#ef444411;padding:4px 8px;border-radius:4px;">' + escapeHtml((j.lastError||'').substring(0,200)) + '</div>';
          html += '</div>';
        });
        html += '</div>';
      } else if (events.length > 0) {
        html += '<div style="font-size:12px;font-weight:600;color:var(--text-muted);text-transform:uppercase;letter-spacing:1px;margin-bottom:8px;">Recent Cron Activity</div>';
        html += _renderEventList(events, toolKey, color);
      } else {
        html += '<div style="text-align:center;padding:30px;color:var(--text-muted);">No cron jobs configured</div>';
      }

    // ─── TTS MODAL ─────────────────────────────────────
    } else if (toolKey === 'tts') {
      html += '<div style="display:grid;grid-template-columns:repeat(2,1fr);gap:10px;margin-bottom:16px;">';
      html += '<div style="background:var(--bg-secondary);border-radius:10px;padding:12px;text-align:center;"><div style="font-size:24px;font-weight:700;color:var(--text-primary);">' + (s.today_calls||0) + '</div><div style="font-size:10px;color:var(--text-muted);text-transform:uppercase;">Generations Today</div></div>';
      html += '<div style="background:var(--bg-secondary);border-radius:10px;padding:12px;text-align:center;"><div style="font-size:24px;font-weight:700;color:'+ ((s.today_errors||0)>0?'#ef4444':'var(--text-primary)') +';">' + (s.today_errors||0) + '</div><div style="font-size:10px;color:var(--text-muted);text-transform:uppercase;">Errors</div></div>';
      html += '</div>';

      if (events.length > 0) {
        html += '<div style="font-size:12px;font-weight:600;color:var(--text-muted);text-transform:uppercase;letter-spacing:1px;margin-bottom:8px;">Recent TTS Generations</div>';
        html += '<div style="max-height:55vh;overflow-y:auto;display:flex;flex-direction:column;gap:6px;">';
        events.forEach(function(evt) {
          var ts = _fmtToolTs(evt.timestamp);
          html += '<div style="padding:10px 12px;background:var(--bg-secondary);border-radius:8px;border-left:3px solid #F9A825;">';
          html += '<div style="display:flex;justify-content:space-between;align-items:center;">';
          html += '<span style="font-size:14px;">🔊</span>';
          html += '<span style="font-size:10px;color:var(--text-muted);">' + ts + '</span>';
          html += '</div>';
          html += '<div style="font-size:13px;color:var(--text-secondary);margin-top:6px;font-style:italic;line-height:1.4;">"' + escapeHtml((evt.detail || '').substring(0, 200)) + '"</div>';
          if (evt.voice) html += '<div style="font-size:10px;color:var(--text-muted);margin-top:4px;">🎤 Voice: ' + escapeHtml(evt.voice) + '</div>';
          if (evt.duration_ms) html += '<span style="font-size:10px;color:var(--text-muted);">' + (evt.duration_ms>=1000?(evt.duration_ms/1000).toFixed(1)+'s':evt.duration_ms+'ms') + '</span>';
          html += '</div>';
        });
        html += '</div>';
      } else {
        html += '<div style="text-align:center;padding:30px;color:var(--text-muted);">No TTS generations today</div>';
      }

    // ─── MEMORY MODAL ──────────────────────────────────
    } else if (toolKey === 'memory') {
      var files = data.memory_files || [];
      var reads = events.filter(function(e){return e.action!=='write';}).length;
      var writes = events.filter(function(e){return e.action==='write';}).length;
      html += '<div style="display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin-bottom:16px;">';
      html += '<div style="background:var(--bg-secondary);border-radius:10px;padding:12px;text-align:center;"><div style="font-size:24px;font-weight:700;color:#3b82f6;">' + reads + '</div><div style="font-size:10px;color:var(--text-muted);text-transform:uppercase;">Reads</div></div>';
      html += '<div style="background:var(--bg-secondary);border-radius:10px;padding:12px;text-align:center;"><div style="font-size:24px;font-weight:700;color:#f59e0b;">' + writes + '</div><div style="font-size:10px;color:var(--text-muted);text-transform:uppercase;">Writes</div></div>';
      html += '<div style="background:var(--bg-secondary);border-radius:10px;padding:12px;text-align:center;"><div style="font-size:24px;font-weight:700;color:var(--text-primary);">' + files.length + '</div><div style="font-size:10px;color:var(--text-muted);text-transform:uppercase;">Files</div></div>';
      html += '</div>';

      if (files.length > 0) {
        html += '<div style="font-size:12px;font-weight:600;color:var(--text-muted);text-transform:uppercase;letter-spacing:1px;margin-bottom:8px;">Workspace Files</div>';
        html += '<div style="display:flex;flex-direction:column;gap:3px;margin-bottom:14px;">';
        files.forEach(function(f) {
          var sizeStr = f.size >= 1024 ? (f.size/1024).toFixed(1)+'KB' : f.size+'B';
          html += '<div style="padding:6px 10px;background:var(--bg-secondary);border-radius:6px;display:flex;align-items:center;gap:8px;font-size:12px;">';
          html += '<span style="font-size:14px;">📄</span>';
          html += '<span style="color:var(--text-link);font-family:monospace;flex:1;">' + escapeHtml(f.path) + '</span>';
          html += '<span style="color:var(--text-muted);font-size:11px;">' + sizeStr + '</span>';
          html += '</div>';
        });
        html += '</div>';
      }

      if (events.length > 0) {
        html += '<div style="font-size:12px;font-weight:600;color:var(--text-muted);text-transform:uppercase;letter-spacing:1px;margin-bottom:8px;">Recent File Operations</div>';
        html += '<div style="max-height:40vh;overflow-y:auto;display:flex;flex-direction:column;gap:4px;">';
        events.forEach(function(evt) {
          var ts = _fmtToolTs(evt.timestamp);
          var isWrite = evt.action === 'write';
          var badge = isWrite ? '<span style="background:#f59e0b33;color:#f59e0b;padding:1px 6px;border-radius:4px;font-size:10px;font-weight:600;">WRITE</span>' : '<span style="background:#3b82f633;color:#3b82f6;padding:1px 6px;border-radius:4px;font-size:10px;font-weight:600;">READ</span>';
          html += '<div style="padding:6px 10px;background:var(--bg-secondary);border-radius:6px;display:flex;align-items:center;gap:8px;font-size:12px;">';
          html += badge;
          html += '<code style="color:var(--text-secondary);flex:1;white-space:pre-wrap;word-break:break-all;">' + escapeHtml(evt.detail || '') + '</code>';
          html += '<span style="color:var(--text-muted);font-size:10px;white-space:nowrap;">' + ts + '</span>';
          html += '</div>';
        });
        html += '</div>';
      } else {
        html += '<div style="text-align:center;padding:20px;color:var(--text-muted);">No file operations today</div>';
      }

    // ─── FALLBACK ──────────────────────────────────────
    } else {
      html += '<div style="display:flex;gap:12px;padding:10px 16px;background:' + color + '22;border-radius:10px;margin-bottom:14px;align-items:center;flex-wrap:wrap;">';
      html += '<span style="font-size:13px;font-weight:600;color:' + color + ';">Today: ' + (s.today_calls||0) + ' calls</span>';
      if (s.today_errors > 0) html += '<span style="font-size:13px;font-weight:600;color:#ef4444;">| ' + s.today_errors + ' errors</span>';
      html += '</div>';
      html += _renderEventList(events, toolKey, color);
    }

    body.innerHTML = html;
    document.getElementById('comp-modal-footer').textContent = 'Auto-refreshing - Last updated: ' + new Date().toLocaleTimeString() + ' - ' + (data.total||0) + ' events today';
  }).catch(function(e) {
    if (!isCompModalActive(_expectedNodeId)) return;
    if (!isRefresh) {
      document.getElementById('comp-modal-body').innerHTML = '<div style="text-align:center;padding:20px;color:var(--text-error);">Failed to load data: ' + e + '</div>';
    }
  });
}

function _renderEventList(events, toolKey, color) {
  if (events.length === 0) return '<div style="text-align:center;padding:30px;color:var(--text-muted);">No events today</div>';
  var html = '<div style="max-height:50vh;overflow-y:auto;display:flex;flex-direction:column;gap:4px;">';
  events.forEach(function(evt) {
    var ts = _fmtToolTs(evt.timestamp);
    var isErr = evt.status === 'error';
    html += '<div style="padding:6px 10px;background:var(--bg-secondary);border-radius:6px;border:1px solid '+(isErr?'#ef444433':'var(--border-secondary)')+';font-size:12px;">';
    html += '<div style="display:flex;justify-content:space-between;"><span style="color:var(--text-secondary);">' + escapeHtml(evt.detail||evt.action||'') + '</span>';
    html += '<span style="color:var(--text-muted);font-size:10px;">' + ts + '</span></div>';
    html += '</div>';
  });
  html += '</div>';
  return html;
}

function closeCompModal() {
  if (_tgRefreshTimer) { clearInterval(_tgRefreshTimer); _tgRefreshTimer = null; }
  if (_imsgRefreshTimer) { clearInterval(_imsgRefreshTimer); _imsgRefreshTimer = null; }
  if (_discordRefreshTimer) { clearInterval(_discordRefreshTimer); _discordRefreshTimer = null; }
  if (_slackRefreshTimer) { clearInterval(_slackRefreshTimer); _slackRefreshTimer = null; }
  if (_waRefreshTimer) { clearInterval(_waRefreshTimer); _waRefreshTimer = null; }
  if (_sigRefreshTimer) { clearInterval(_sigRefreshTimer); _sigRefreshTimer = null; }
  if (_gcRefreshTimer) { clearInterval(_gcRefreshTimer); _gcRefreshTimer = null; }
  if (_mstRefreshTimer) { clearInterval(_mstRefreshTimer); _mstRefreshTimer = null; }
  if (_mmRefreshTimer) { clearInterval(_mmRefreshTimer); _mmRefreshTimer = null; }
  if (_gwRefreshTimer) { clearInterval(_gwRefreshTimer); _gwRefreshTimer = null; }
  if (_brainRefreshTimer) { clearInterval(_brainRefreshTimer); _brainRefreshTimer = null; }
  if (_toolRefreshTimer) { clearInterval(_toolRefreshTimer); _toolRefreshTimer = null; }
  if (_costOptimizerRefreshTimer) { clearInterval(_costOptimizerRefreshTimer); _costOptimizerRefreshTimer = null; }
  if (_webchatRefreshTimer) { clearInterval(_webchatRefreshTimer); _webchatRefreshTimer = null; }
  if (_ircRefreshTimer) { clearInterval(_ircRefreshTimer); _ircRefreshTimer = null; }
  if (_bbRefreshTimer) { clearInterval(_bbRefreshTimer); _bbRefreshTimer = null; }
  if (window._genericChannelTimer) { clearInterval(window._genericChannelTimer); window._genericChannelTimer = null; }
  
  // Reset time travel state
  _timeTravelMode = false;
  _currentTimeContext = null;
  window._currentComponentId = null;
  
  document.getElementById('comp-modal-overlay').classList.remove('open');
}
document.addEventListener('keydown', function(e) { if (e.key === 'Escape') closeCompModal(); });
document.addEventListener('DOMContentLoaded', initCompClickHandlers);

// Pre-fetch tool data so modals open instantly
function _prefetchToolData() {
  var tools = ['session','exec','browser','search','cron','tts','memory','brain','telegram','gateway','runtime','machine'];
  tools.forEach(function(t) {
    fetch('/api/component/tool/' + t).then(function(r){return r.json();}).then(function(data) {
      _toolDataCache[t] = data;
      _toolCacheAge[t] = Date.now();
    }).catch(function(){});
  });
}
document.addEventListener('DOMContentLoaded', function() {
  setTimeout(_prefetchToolData, 2000); // prefetch 2s after load
  setInterval(_prefetchToolData, 30000); // refresh cache every 30s
});

function openTaskModal(sessionId, taskName, sessionKey) {
  _modalSessionId = sessionId || '';
  window._modalSessionKey = sessionKey || '';  // used by the fallback renderer
  document.getElementById('modal-title').textContent = taskName || sessionId || sessionKey;
  document.getElementById('modal-session-key').textContent = sessionKey || sessionId;
  document.getElementById('task-modal-overlay').classList.add('open');
  document.getElementById('modal-content').innerHTML = '<div style="text-align:center;padding:40px;color:var(--text-muted);">Loading transcript...</div>';
  _modalTab = 'summary';
  document.querySelectorAll('.modal-tab').forEach(function(t,i){t.classList.toggle('active',i===0);});
  loadModalTranscript();
  // Auto-refresh only makes sense for LIVE subagents (those with a sessionId
  // whose transcript can update). Failed/stale entries open in fallback mode
  // and their data is immutable — refreshing just causes flicker. The user
  // can re-enable via the checkbox if needed.
  if (_modalAutoRefresh && sessionId) {
    _modalRefreshTimer = setInterval(loadModalTranscript, 4000);
  } else {
    // Reflect the disabled state in the checkbox so the UX matches.
    var cb = document.getElementById('modal-auto-refresh-cb');
    if (cb && !sessionId) cb.checked = false;
  }
  document.addEventListener('keydown', _modalEscHandler);
}

function closeTaskModal() {
  document.getElementById('task-modal-overlay').classList.remove('open');
  _modalSessionId = null;
  if (_modalRefreshTimer) { clearInterval(_modalRefreshTimer); _modalRefreshTimer = null; }
  document.removeEventListener('keydown', _modalEscHandler);
}

function _modalEscHandler(e) { if (e.key === 'Escape') closeTaskModal(); }

function toggleModalAutoRefresh() {
  _modalAutoRefresh = document.getElementById('modal-auto-refresh-cb').checked;
  if (_modalRefreshTimer) { clearInterval(_modalRefreshTimer); _modalRefreshTimer = null; }
  if (_modalAutoRefresh && _modalSessionId) {
    _modalRefreshTimer = setInterval(loadModalTranscript, 4000);
  }
}

function switchModalTab(tab) {
  _modalTab = tab;
  document.querySelectorAll('.modal-tab').forEach(function(t){ t.classList.toggle('active', t.textContent.toLowerCase().indexOf(tab) >= 0 || (tab==='full' && t.textContent==='Full Logs')); });
  renderModalContent();
}

async function loadModalTranscript() {
  // Failed-spawn subagents have sessionId="" (no child was created), so
  // don't bail on empty here — fall straight into the fallback which
  // looks up metadata by key.
  if (!_modalSessionId && !window._modalSessionKey) return;

  // Only hit the transcript endpoint when we actually have a sessionId.
  if (_modalSessionId) {
    try {
      var r = await fetch('/api/transcript-events/' + encodeURIComponent(_modalSessionId));
      var data = await r.json();
      if (!data.error && data.events && data.events.length) {
        _modalEvents = data.events;
        var ec = document.getElementById('modal-event-count');
        if (ec) ec.textContent = '📊 ' + _modalEvents.length + ' events';
        var mc = document.getElementById('modal-msg-count');
        if (mc) mc.textContent = '💬 ' + (data.messageCount || 0) + ' messages';
        // Real transcript available — restore the Summary/Narrative/Full Logs
        // tab strip + footer that the fallback renderer swapped out.
        var tabsEl = document.querySelector('#task-modal-overlay .modal-tabs');
        if (tabsEl) {
          tabsEl.style.display = '';
          if (tabsEl.dataset.fallbackMode && tabsEl.dataset.originalHTML) {
            tabsEl.innerHTML = tabsEl.dataset.originalHTML;
            delete tabsEl.dataset.fallbackMode;
            delete tabsEl.dataset.originalHTML;
          }
        }
        var footer = document.querySelector('#task-modal-overlay .modal-footer');
        if (footer) footer.style.display = '';
        renderModalContent();
        return;
      }
      // data.error or zero events → fall through to the fallback renderer.
    } catch(e) { /* network error — fall through */ }
  }
  // No transcript (empty sessionId, 404, or zero events). Render the
  // spawn metadata we already have from /api/subagents.
  _renderModalSpawnInfo(_modalSessionId || window._modalSessionKey || '', 'No transcript available');
}

// Fallback view when child transcript is gone (OpenClaw TTL) or empty.
// Reads /api/subagents (the list already surfaces task / error / model /
// runtime) and finds the matching entry by sessionId or key. Renders a
// card-style summary with the spawn metadata + any error OpenClaw
// returned. Works for failed spawns AND stale successful ones.
// Which fallback pane is active. Persists across auto-refresh cycles so
// switching to "Brain Events" doesn't snap back to "Overview" every 4s.
window._fallbackTab = window._fallbackTab || 'overview';

function _switchFallbackTab(tab) {
  window._fallbackTab = tab;
  // Toggle tab-strip active state
  document.querySelectorAll('#task-modal-overlay .modal-tab').forEach(function(t) {
    t.classList.toggle('active', (t.dataset.fallbackTab || '') === tab);
  });
  // Toggle pane visibility
  var ov = document.getElementById('fallback-pane-overview');
  var br = document.getElementById('fallback-pane-brain');
  if (ov) ov.style.display = (tab === 'overview') ? '' : 'none';
  if (br) br.style.display = (tab === 'brain')    ? '' : 'none';
}

async function _renderModalSpawnInfo(sessionIdOrKey, reason) {
  var el = document.getElementById('modal-content');
  if (!el) return;
  // Only show the "Loading..." placeholder on the first render. Subsequent
  // re-renders (tab switches, auto-refresh) keep the existing content
  // visible until the fetch resolves, avoiding a flicker that makes the
  // modal hard to read through.
  var alreadyRendered = !!document.getElementById('fallback-pane-overview');
  if (!alreadyRendered) {
    el.innerHTML = '<div style="padding:20px;color:var(--text-muted);">Loading subagent info...</div>';
  }
  try {
    var saData = await fetch('/api/subagents').then(function(r){return r.json();}).catch(function(){return {subagents:[]};});
    var entries = saData.subagents || [];
    var match = entries.find(function(a) {
      return a.sessionId === sessionIdOrKey || a.key === sessionIdOrKey;
    });
    if (!match) {
      if (!alreadyRendered) {
        el.innerHTML = '<div style="padding:20px;color:var(--text-error);">' + escHtml(reason) + '</div>';
      }
      return;
    }
    // Idempotency guard: if the critical fields haven't changed AND the DOM
    // already contains the rendered overview pane (i.e. this isn't the first
    // render), skip rebuilding. We check `fallback-pane-overview` presence
    // so a fresh openTaskModal (which resets modal-content) always re-paints
    // even when the fingerprint coincidentally matches a previous subagent.
    var fingerprint = JSON.stringify([
      match.status, match.task, match.error, match.completionResult,
      match.completionStatus, match.runtimeFormatted, match.tokensIn, match.tokensOut,
    ]);
    if (document.getElementById('fallback-pane-overview')
        && el.dataset.spawnFingerprint === fingerprint) {
      return;
    }
    var startedAt = match.startedAt ? new Date(match.startedAt).toLocaleString() : '';
    var statusColor = { active:'#22c55e', idle:'#f59e0b', stale:'#6b7280', failed:'#ef4444' }[match.status] || '#6b7280';

    // Build Overview pane HTML
    var overviewHtml = '<div style="padding:20px;display:flex;flex-direction:column;gap:16px;">';
    overviewHtml += '<div style="display:flex;align-items:center;gap:10px;">'
                 +  '<span style="display:inline-block;width:12px;height:12px;border-radius:50%;background:' + statusColor + ';"></span>'
                 +  '<strong style="font-size:15px;color:var(--text-primary);">' + escHtml(match.displayName || 'subagent') + '</strong>'
                 +  '<span style="font-size:11px;color:var(--text-muted);text-transform:uppercase;letter-spacing:0.5px;font-weight:700;">' + escHtml(match.status) + '</span>'
                 +  '</div>';
    if (match.task) {
      overviewHtml += '<div><div style="font-size:11px;color:var(--text-muted);text-transform:uppercase;letter-spacing:0.5px;font-weight:700;margin-bottom:6px;">Task</div>'
                   +  '<div style="font-size:13px;color:var(--text-primary);line-height:1.5;white-space:pre-wrap;">' + escHtml(match.task) + '</div></div>';
    }
    var meta = [];
    if (startedAt) meta.push(['Started', startedAt]);
    // Prefer the child's actual runtime (from OpenClaw completion event) over
    // our "time since spawn" calculation — runtimeFormatted is e.g. "1s",
    // match.runtime is e.g. "72h 49m" which is misleading for a 1-second run.
    var rtDisplay = match.runtimeFormatted || match.runtime || '';
    if (rtDisplay) meta.push(['Runtime', rtDisplay]);
    if (match.model && match.model !== 'unknown') meta.push(['Model', match.model]);
    if (match.parent) meta.push(['Parent', match.parent]);
    if (match.runId) meta.push(['Run ID', match.runId]);
    if (match.completionStatus) meta.push(['Outcome', match.completionStatus]);
    if (match.tokensIn || match.tokensOut) {
      meta.push(['Tokens', 'in ' + (match.tokensIn || 0) + ' / out ' + (match.tokensOut || 0)]);
    }
    if (meta.length) {
      overviewHtml += '<div style="display:grid;grid-template-columns:max-content 1fr;gap:4px 14px;font-size:12px;">';
      meta.forEach(function(row) {
        overviewHtml += '<div style="color:var(--text-muted);">' + escHtml(row[0]) + '</div>'
                     +  '<div style="color:var(--text-primary);font-family:monospace;overflow-wrap:anywhere;">' + escHtml(row[1]) + '</div>';
      });
      overviewHtml += '</div>';
    }
    var logParts = [];
    if (match.completionResult && match.completionResult !== '(no output)') {
      logParts.push({ label:'Subagent output', icon:'📤', color:'#22c55e', text: match.completionResult });
    } else if (match.completionStatus) {
      logParts.push({ label:'Subagent output', icon:'📤', color:'#6b7280',
                      text: '(Subagent completed with no output — OpenClaw reported "' + match.completionStatus + '")' });
    }
    if (match.spawnAck && !match.error) {
      logParts.push({ label:'Spawn handshake', icon:'🤝', color:'#3b82f6', text: match.spawnAck });
    }
    if (logParts.length) {
      overviewHtml += '<div><div style="font-size:11px;color:var(--text-muted);text-transform:uppercase;letter-spacing:0.5px;font-weight:700;margin-bottom:8px;">Activity</div>';
      logParts.forEach(function(part) {
        overviewHtml += '<div style="border:1px solid var(--border-primary);border-radius:8px;margin-bottom:10px;overflow:hidden;">'
                     +  '<div style="padding:6px 10px;background:var(--bg-secondary);border-bottom:1px solid var(--border-primary);font-size:11px;color:' + part.color + ';font-weight:600;">'
                     +  part.icon + ' ' + escHtml(part.label) + '</div>'
                     +  '<pre style="margin:0;padding:10px 12px;font-size:12px;color:var(--text-primary);white-space:pre-wrap;word-break:break-word;font-family:ui-monospace,Menlo,monospace;max-height:260px;overflow:auto;">'
                     +  escHtml(part.text) + '</pre></div>';
      });
      overviewHtml += '</div>';
    }
    overviewHtml += '</div>';

    // Brain pane — populated asynchronously by _renderModalBrainEvents.
    var brainHtml = '<div id="modal-brain-events-slot" style="padding:14px 20px;"></div>';

    // Replace the modal-tabs strip with our 2-tab layout for fallback mode
    // (Overview / Brain Events). Restored to Summary/Narrative/Full Logs
    // by loadModalTranscript when a live transcript is found.
    try {
      var tabsStrip = document.querySelector('#task-modal-overlay .modal-tabs');
      if (tabsStrip && !tabsStrip.dataset.fallbackMode) {
        tabsStrip.dataset.fallbackMode = '1';
        tabsStrip.dataset.originalHTML = tabsStrip.innerHTML;
      }
      if (tabsStrip) {
        tabsStrip.style.display = '';
        tabsStrip.innerHTML =
          '<div class="modal-tab' + (window._fallbackTab === 'overview' ? ' active' : '') + '" data-fallback-tab="overview" onclick="_switchFallbackTab(\'overview\')">Overview</div>' +
          '<div class="modal-tab' + (window._fallbackTab === 'brain' ? ' active' : '') + '" data-fallback-tab="brain" onclick="_switchFallbackTab(\'brain\')">Brain Events</div>';
      }
      // Footer isn't meaningful in fallback (no event/message counters).
      var footer = document.querySelector('#task-modal-overlay .modal-footer');
      if (footer) footer.style.display = 'none';
    } catch(e) {}

    // Render both panes, show the active one.
    var showOv = window._fallbackTab !== 'brain';
    el.innerHTML =
      '<div id="fallback-pane-overview" style="display:' + (showOv ? '' : 'none') + ';">' + overviewHtml + '</div>' +
      '<div id="fallback-pane-brain" style="display:'    + (showOv ? 'none' : '') + ';">' + brainHtml + '</div>';
    // Record the fingerprint AFTER the DOM write so concurrent calls don't
    // see a stored fingerprint that matches the state they're about to
    // render and bail out before writing anything.
    el.dataset.spawnFingerprint = fingerprint;

    // Populate Brain events asynchronously (fire-and-forget).
    _renderModalBrainEvents(match).catch(function(){ /* non-fatal */ });
  } catch(e) {
    el.innerHTML = '<div style="padding:20px;color:var(--text-error);">' + escHtml(reason) + '</div>';
  }
}

// Fetch /api/brain-history and render a per-subagent slice into the slot
// the spawn-info renderer left behind. Filter rules:
//   - match by source session UUID (parent OR child)
//   - time window: 30s before startedAt → 10 min after, or until
//     completionTs+1min if we have it
//   - drop CONTEXT entries (they're always present, not actionable here)
async function _renderModalBrainEvents(match) {
  var slot = document.getElementById('modal-brain-events-slot');
  if (!slot) return;
  try {
    var parentUuid = (match.parent || '').split(':').pop() || '';
    var childUuid  = (match.key || '').split(':').pop() || '';
    // Brain events emit `source` as the on-disk session-file UUID, NOT the
    // subagent_id. They differ for sub-agents (sessionId + sessionFile are
    // distinct fields). Without including the file-UUID variant the
    // spawn-detail "Brain Events" tab said "No Brain events found in window"
    // even when the sub-agent was actively running.
    var fileUuid = (match.sessionFile || '').replace(/\.jsonl$/i, '');
    var candidates = [parentUuid, childUuid, match.sessionId, fileUuid].filter(Boolean);
    if (!candidates.length) return;

    var startedMs = match.startedAt || Date.now();
    var endMs;
    if (match.completionTs) {
      var t = Date.parse(match.completionTs);
      if (!isNaN(t)) endMs = t + 60000;  // +1 min buffer after completion
    }
    if (!endMs) endMs = startedMs + 600000;  // default: +10 min
    var winStart = startedMs - 30000;        // -30s lead-up

    var data = await fetchJsonWithTimeout('/api/brain-history?limit=500', 6000);
    var events = (data && data.events) ? data.events : [];
    var filtered = events.filter(function(ev) {
      if ((ev.type || '').toUpperCase() === 'CONTEXT') return false;
      var src = ev.source || '';
      if (candidates.indexOf(src) < 0) return false;
      var ts = Date.parse(ev.time || '');
      if (isNaN(ts)) return true;  // keep undated events
      return ts >= winStart && ts <= endMs;
    });
    // Sort ascending (chronological) for reading top-to-bottom.
    filtered.sort(function(a, b) {
      return (a.time || '').localeCompare(b.time || '');
    });

    if (!filtered.length) {
      slot.innerHTML = '<div><div style="font-size:11px;color:var(--text-muted);text-transform:uppercase;letter-spacing:0.5px;font-weight:700;margin-bottom:8px;">Brain events</div>'
                     + '<div style="padding:10px 12px;background:var(--bg-secondary);border:1px solid var(--border-primary);border-radius:6px;font-size:12px;color:var(--text-muted);">'
                     + 'No Brain events found in the window around this spawn ('
                     + new Date(winStart).toLocaleTimeString() + ' – '
                     + new Date(endMs).toLocaleTimeString() + ').</div></div>';
      return;
    }

    var TYPE_STYLE = {
      USER:{c:'#9ab4ff',icon:'💬'}, AGENT:{c:'#c0a0ff',icon:'🤖'},
      THINK:{c:'#6ec1e4',icon:'🧠'}, EXEC:{c:'#f0c060',icon:'⚡'},
      READ:{c:'#78dca7',icon:'📖'}, WRITE:{c:'#78dca7',icon:'✏️'},
      SEARCH:{c:'#f28fb0',icon:'🔍'}, BROWSER:{c:'#9cd88a',icon:'🌐'},
      MSG:{c:'#8ec7ff',icon:'💬'}, SPAWN:{c:'#d19cf5',icon:'✨'},
      RESULT:{c:'#78dca7',icon:'✓'}, TOOL:{c:'#f0c060',icon:'⚙️'},
    };

    var rows = '';
    filtered.forEach(function(ev) {
      var type = (ev.type || 'TOOL').toUpperCase();
      var style = TYPE_STYLE[type] || {c:'#c0c0c0', icon:'•'};
      var t = ev.time ? new Date(ev.time) : null;
      var ts = t && !isNaN(t.getTime())
        ? t.toLocaleTimeString('en-GB', {hour:'2-digit',minute:'2-digit',second:'2-digit'})
        : '';
      var detail = escHtml(ev.detail || '');
      if (detail.length > 200) detail = detail.substring(0, 197) + '…';
      var src = ev.sourceLabel || ev.source || '';
      if (src.length > 14) src = src.substring(0, 12) + '…';
      rows += '<div style="display:flex;gap:8px;align-items:flex-start;padding:4px 0;border-bottom:1px solid rgba(255,255,255,0.04);">'
           +  '<span style="color:var(--text-faint);min-width:62px;font-size:10.5px;font-variant-numeric:tabular-nums;">' + ts + '</span>'
           +  '<span style="font-size:12px;min-width:16px;text-align:center;">' + style.icon + '</span>'
           +  '<span style="color:' + style.c + ';min-width:54px;font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:0.4px;">' + type + '</span>'
           +  '<span style="color:#d0d0d0;flex:1;white-space:pre-wrap;word-break:break-word;font-size:12px;line-height:1.45;">' + detail + '</span>'
           +  '</div>';
    });
    slot.innerHTML = '<div><div style="font-size:11px;color:var(--text-muted);text-transform:uppercase;letter-spacing:0.5px;font-weight:700;margin-bottom:8px;display:flex;align-items:center;gap:8px;">'
                   + '<span>🧠 Brain events</span>'
                   + '<span style="color:var(--text-faint);font-weight:500;text-transform:none;letter-spacing:0;">'
                   + '(' + filtered.length + ' entries around this spawn)</span></div>'
                   + '<div style="border:1px solid var(--border-primary);border-radius:8px;background:var(--bg-secondary);padding:4px 12px;max-height:360px;overflow:auto;">'
                   + rows + '</div></div>';
  } catch (e) {
    // Silent — modal already has the essentials, Brain-events is a bonus.
  }
}

function renderModalContent() {
  var el = document.getElementById('modal-content');
  // When there's no transcript (failed/GC'd subagent), the fallback
  // renderer took over — don't overwrite it when the user switches tabs.
  if (!_modalEvents || !_modalEvents.length) {
    _renderModalSpawnInfo(_modalSessionId || window._modalSessionKey || '', 'No transcript available');
    return;
  }
  if (_modalTab === 'summary') renderModalSummary(el);
  else if (_modalTab === 'narrative') renderModalNarrative(el);
  else renderModalFull(el);
}

function renderModalSummary(el) {
  var events = _modalEvents;
  // Find first user message as task description
  var desc = '';
  var result = '';
  for (var i = 0; i < events.length; i++) {
    if (events[i].type === 'user' && !desc) {
      desc = events[i].text || '';
      if (desc.length > 500) desc = desc.substring(0, 500) + '...';
    }
  }
  // Find last assistant text as result
  for (var i = events.length - 1; i >= 0; i--) {
    if (events[i].type === 'agent' && events[i].text) {
      result = events[i].text;
      if (result.length > 1000) result = result.substring(0, 1000) + '...';
      break;
    }
  }
  var html = '';
  var renderMd = (typeof marked !== 'undefined' && marked.parse) ? function(s){ return marked.parse(s); } : escHtml;
  html += '<div class="summary-section"><div class="summary-label">Task Description</div>';
  html += '<div class="summary-text md-rendered">' + renderMd(desc || 'No description found') + '</div></div>';
  html += '<div class="summary-section"><div class="summary-label">Final Result / Output</div>';
  html += '<div class="summary-text md-rendered">' + renderMd(result || 'No result yet...') + '</div></div>';
  el.innerHTML = html;
}

function renderModalNarrative(el) {
  var events = _modalEvents;
  var html = '';
  events.forEach(function(evt) {
    var icon = '', text = '';
    if (evt.type === 'user') {
      icon = '👤'; text = 'User sent: <code>' + escHtml((evt.text||'').substring(0, 150)) + '</code>';
    } else if (evt.type === 'agent') {
      icon = '🤖'; text = 'Agent said: <code>' + escHtml((evt.text||'').substring(0, 200)) + '</code>';
    } else if (evt.type === 'thinking') {
      icon = '💭'; text = 'Agent thought about the problem...';
    } else if (evt.type === 'exec') {
      icon = '⚡'; text = 'Ran command: <code>' + escHtml(evt.command||'') + '</code>';
    } else if (evt.type === 'read') {
      icon = '📖'; text = 'Read file: <code>' + escHtml(evt.file||'') + '</code>';
    } else if (evt.type === 'tool') {
      icon = '🔧'; text = 'Called tool: <code>' + escHtml(evt.toolName||'') + '</code>';
    } else if (evt.type === 'result') {
      icon = '✅'; text = 'Got result (' + (evt.text||'').length + ' chars)';
    } else return;
    html += '<div class="narrative-item"><span class="narr-icon">' + icon + '</span>' + text + '</div>';
  });
  el.innerHTML = html || '<div style="padding:20px;color:var(--text-muted);">No events yet</div>';
}

var _expandedEvts = {};
var _expandedGroups = {};

function renderEvtItem(evt, idx) {
  var icon = '📝', typeClass = '', summary = '', body = '';
  var ts = evt.timestamp ? new Date(evt.timestamp).toLocaleTimeString() : '';
  if (evt.type === 'agent') {
    icon = '🤖'; typeClass = 'type-agent';
    summary = '<strong>Agent</strong> - ' + escHtml((evt.text||'').substring(0, 120));
    body = evt.text || '';
  } else if (evt.type === 'thinking') {
    icon = '💭'; typeClass = 'type-thinking';
    var thinkChars = evt.thinking_chars || (evt.text||'').length;
    var thinkBadge = thinkChars > 0 ? ' <span style="background:#374151;color:#9ca3af;font-size:10px;font-weight:600;padding:1px 5px;border-radius:8px;margin-left:4px;" title="~' + Math.round(thinkChars/4) + ' tokens">' + thinkChars + ' chars</span>' : '';
    summary = '<strong>Thinking</strong>' + thinkBadge + ' - ' + escHtml((evt.text||'').substring(0, 100));
    body = evt.text || '';
  } else if (evt.type === 'user') {
    icon = '👤'; typeClass = 'type-user';
    summary = '<strong>User</strong> - ' + escHtml((evt.text||'').substring(0, 120));
    body = evt.text || '';
  } else if (evt.type === 'exec') {
    icon = '⚡'; typeClass = 'type-exec';
    summary = '<strong>EXEC</strong> - <code>' + escHtml(evt.command||'') + '</code>';
    body = evt.command || '';
  } else if (evt.type === 'read') {
    icon = '📖'; typeClass = 'type-read';
    summary = '<strong>READ</strong> - ' + escHtml(evt.file||'');
    body = evt.file || '';
  } else if (evt.type === 'tool') {
    icon = '🔧'; typeClass = 'type-exec';
    summary = '<strong>' + escHtml(evt.toolName||'tool') + '</strong> - ' + escHtml((evt.args||'').substring(0, 100));
    body = evt.args || '';
  } else if (evt.type === 'result') {
    icon = '✅'; typeClass = 'type-result';
    summary = '<strong>Result</strong> - ' + escHtml((evt.text||'').substring(0, 120));
    body = evt.text || '';
  } else {
    summary = '<strong>' + escHtml(evt.type) + '</strong>';
    body = JSON.stringify(evt, null, 2);
  }
  var bodyId = 'evt-body-' + idx;
  var h = '<div class="evt-item ' + typeClass + '">';
  h += '<div class="evt-header" onclick="toggleEvtBody(\'' + bodyId + '\',' + idx + ')">';
  h += '<span class="evt-icon">' + icon + '</span>';
  h += '<span class="evt-summary">' + summary + '</span>';
  h += '<span class="evt-ts">' + escHtml(ts) + '</span>';
  h += '</div>';
  var bodyHtml = (typeof marked !== 'undefined' && marked.parse) ? marked.parse(body) : escHtml(body);
  var isOpen = _expandedEvts[idx] ? ' open' : '';
  h += '<div class="evt-body md-rendered' + isOpen + '" id="' + bodyId + '">' + bodyHtml + '</div>';
  h += '</div>';
  return h;
}

function renderModalFull(el) {
  var events = _modalEvents;
  var html = '';
  var i = 0;
  while (i < events.length) {
    var evt = events[i];
    // Group consecutive thinking blocks
    if (evt.type === 'thinking') {
      var groupStart = i;
      var groupEvts = [];
      while (i < events.length && events[i].type === 'thinking') {
        groupEvts.push({evt: events[i], idx: i});
        i++;
      }
      if (groupEvts.length === 1) {
        // Single thinking block — render normally
        html += renderEvtItem(groupEvts[0].evt, groupEvts[0].idx);
      } else {
        // Multiple consecutive thinking blocks — group them
        var groupId = 'think-group-' + groupStart;
        var firstSnippet = escHtml((groupEvts[0].evt.text||'').substring(0, 80));
        var isGroupOpen = _expandedGroups[groupId] ? ' open' : '';
        html += '<div class="thinking-group">';
        html += '<div class="thinking-group-header" onclick="toggleThinkGroup(\'' + groupId + '\')">';
        html += '<span class="evt-icon">💭</span>';
        html += '<span class="evt-summary"><strong>Thinking</strong> - ' + firstSnippet + '&#8230;</span>';
        html += '<span class="thinking-group-badge">' + groupEvts.length + ' blocks</span>';
        html += '</div>';
        html += '<div class="thinking-group-body' + isGroupOpen + '" id="' + groupId + '">';
        groupEvts.forEach(function(item) {
          html += renderEvtItem(item.evt, item.idx);
        });
        html += '</div>';
        html += '</div>';
      }
    } else {
      html += renderEvtItem(evt, i);
      i++;
    }
  }
  el.innerHTML = html || '<div style="padding:20px;color:var(--text-muted);">No events yet</div>';
}

function toggleEvtBody(bodyId, idx) {
  var b = document.getElementById(bodyId);
  if (!b) return;
  b.classList.toggle('open');
  _expandedEvts[idx] = b.classList.contains('open');
}

function toggleThinkGroup(groupId) {
  var b = document.getElementById(groupId);
  if (!b) return;
  b.classList.toggle('open');
  _expandedGroups[groupId] = b.classList.contains('open');
}

// Initialize theme and zoom on page load
function setBootStep(stepId, state, subtitle) {
  var el = document.getElementById('boot-step-' + stepId);
  if (!el) return;
  el.classList.remove('loading', 'done', 'fail');
  if (state) el.classList.add(state);
  if (subtitle) {
    var textEl = el.querySelector('span:last-child');
    if (textEl) textEl.textContent = subtitle;
  }
}

function finishBootOverlay() {
  var overlay = document.getElementById('boot-overlay');
  document.body.classList.remove('booting');
  document.body.classList.add('app-ready');
  if (overlay) {
    overlay.classList.add('hide');
    setTimeout(function() { if (overlay && overlay.parentNode) overlay.parentNode.removeChild(overlay); }, 350);
  }
}

// Safety net: no matter what happens below, dismiss the boot overlay after
// this cap so users never see "Initializing ClawMetry" forever. Any step that
// finishes later will still update its own slice of the UI when it returns.
var BOOT_HARD_TIMEOUT_MS = 8000;
var _bootFinished = false;
function _safeFinishBoot() {
  if (_bootFinished) return;
  _bootFinished = true;
  finishBootOverlay();
}

function _withTimeout(promise, ms, label) {
  return Promise.race([
    promise,
    new Promise(function(_, reject) {
      setTimeout(function() { reject(new Error((label || 'step') + ' timeout')); }, ms);
    })
  ]);
}

async function bootDashboard() {
  // Hard floor: dismiss overlay after BOOT_HARD_TIMEOUT_MS no matter what.
  // The dashboard stays usable with partial data; individual panels show
  // their own empty / loading states while slower requests land.
  setTimeout(_safeFinishBoot, BOOT_HARD_TIMEOUT_MS);

  // Check auth first -- if not valid, show login and abort boot
  try {
    var stored = localStorage.getItem('clawmetry-token');
    var authRes = await _withTimeout(
      fetch('/api/auth/check' + (stored ? '?token=' + encodeURIComponent(stored) : '')),
      3000,
      'auth'
    );
    var authData = await authRes.json();
    if (authData.needsSetup) {
      document.getElementById('login-overlay').style.display = 'none';
      var gwo = document.getElementById('gw-setup-overlay');
      gwo.dataset.mandatory = 'true';
      document.getElementById('gw-setup-close').style.display = 'none';
      gwo.style.display = 'flex';
      _safeFinishBoot();
      return;
    }
    if (authData.authRequired && !authData.valid) {
      document.getElementById('login-overlay').style.display = 'flex';
      _safeFinishBoot();
      return;
    }
  } catch(e) { /* auth check hung -- boot anyway, safety timeout will fire */ }

  setBootStep('overview', 'loading', 'Loading overview + model context');
  setBootStep('tasks', 'loading', 'Loading active tasks');
  setBootStep('health', 'loading', 'Loading system health');

  // Kick off all three primary steps in parallel. If any hangs we surface
  // "delayed" but the overall boot still completes.
  var results = await Promise.allSettled([
    _withTimeout(Promise.resolve().then(loadAll), 5000, 'overview'),
    _withTimeout(Promise.resolve().then(loadOverviewTasks), 5000, 'tasks'),
    _withTimeout(Promise.resolve().then(loadSystemHealth), 5000, 'health'),
  ]);
  var okOverview = results[0].status === 'fulfilled' && results[0].value !== false;
  var okTasks    = results[1].status === 'fulfilled' && results[1].value !== false;
  var okHealth   = results[2].status === 'fulfilled' && results[2].value !== false;
  setBootStep('overview', okOverview ? 'done' : 'fail', okOverview ? 'Overview ready' : 'Overview delayed');
  setBootStep('tasks',    okTasks    ? 'done' : 'fail', okTasks    ? 'Tasks ready'    : 'Tasks delayed');
  setBootStep('health',   okHealth   ? 'done' : 'fail', okHealth   ? 'System health ready' : 'System health delayed');
  try { loadSandboxStatus(); } catch (e) {}

  // Connect live streams last so they don't eat the waitress thread pool
  // while the initial fetches are still in flight.
  setBootStep('streams', 'loading', 'Connecting live streams');
  try { startLogStream(); } catch (e) {}
  try { startHealthStream(); } catch (e) {}
  setBootStep('streams', 'done', 'Live streams connected');

  // Prefetches and periodic refreshes are background work -- never let them
  // block the overlay.
  (async function backgroundPrefetch() {
    try { await _withTimeout(loadCrons(), 5000, 'crons'); } catch (e) {}
    try { await _withTimeout(loadMemory(), 5000, 'memory'); } catch (e) {}
  })();

  startSystemHealthRefresh();
  startOverviewRefresh();
  startOverviewTasksRefresh();
  startActiveTasksRefresh();

  var sub = document.getElementById('boot-sub');
  if (sub) sub.textContent = 'Dashboard ready';
  setTimeout(_safeFinishBoot, 180);
}

document.addEventListener('DOMContentLoaded', function() {
  initTheme();
  initZoom();
  // Overview is the default tab
  initOverviewFlow();
  initOverviewCompClickHandlers();
  initFlow();
  bootDashboard();
});

// ── History Tab ──────────────────────────────────────────────────────
var _historyRange = 3600; // seconds
var _historyFrom = null;
var _historyTo = null;
var _histTokensChart = null;
var _histCostChart = null;
var _histSessionsChart = null;

function setTimeRange(seconds, btn) {
  _historyRange = seconds;
  _historyFrom = null;
  _historyTo = null;
  document.querySelectorAll('#time-range-picker .time-btn').forEach(b => b.classList.remove('active'));
  if (btn) btn.classList.add('active');
  document.getElementById('custom-range-picker').style.display = 'none';
  loadHistory();
}

function showCustomRange() {
  document.querySelectorAll('#time-range-picker .time-btn').forEach(b => b.classList.remove('active'));
  var cp = document.getElementById('custom-range-picker');
  cp.style.display = 'flex';
  // Default to last 24h
  var now = new Date();
  var ago = new Date(now.getTime() - 86400000);
  document.getElementById('history-to').value = now.toISOString().slice(0,16);
  document.getElementById('history-from').value = ago.toISOString().slice(0,16);
}

function applyCustomRange() {
  var from = document.getElementById('history-from').value;
  var to = document.getElementById('history-to').value;
  if (!from || !to) return;
  _historyFrom = new Date(from).getTime() / 1000;
  _historyTo = new Date(to).getTime() / 1000;
  _historyRange = null;
  loadHistory();
}

function _getHistoryParams() {
  var now = Date.now() / 1000;
  var from_ts, to_ts;
  if (_historyRange) {
    from_ts = now - _historyRange;
    to_ts = now;
  } else {
    from_ts = _historyFrom;
    to_ts = _historyTo;
  }
  var span = to_ts - from_ts;
  var interval = 'minute';
  if (span > 86400) interval = 'hour';
  if (span > 604800) interval = 'day';
  return {from: from_ts, to: to_ts, interval: interval};
}

function _chartOpts(title, yLabel) {
  return {
    responsive: true,
    maintainAspectRatio: false,
    interaction: { mode: 'index', intersect: false },
    plugins: {
      legend: { display: true, position: 'top', labels: { boxWidth: 12, font: { size: 11 }, color: getComputedStyle(document.body).getPropertyValue('--text-secondary') || '#666' } },
      tooltip: { backgroundColor: 'rgba(0,0,0,0.8)', titleFont: { size: 12 }, bodyFont: { size: 11 } }
    },
    scales: {
      x: { type: 'time', time: { tooltipFormat: 'MMM d, HH:mm' }, grid: { display: false }, ticks: { font: { size: 10 }, color: getComputedStyle(document.body).getPropertyValue('--text-muted') || '#999' } },
      y: { beginAtZero: true, grid: { color: 'rgba(128,128,128,0.1)' }, ticks: { font: { size: 10 }, color: getComputedStyle(document.body).getPropertyValue('--text-muted') || '#999' }, title: { display: !!yLabel, text: yLabel || '', font: { size: 11 } } }
    },
    onClick: function(evt, elems) {
      if (elems.length > 0) {
        var idx = elems[0].index;
        var ds = this.data.datasets[elems[0].datasetIndex];
        if (ds && ds.data[idx]) {
          var ts = ds.data[idx].x;
          showSnapshot(ts instanceof Date ? ts.getTime()/1000 : ts/1000);
        }
      }
    }
  };
}

function _destroyChart(chart) {
  if (chart) { try { chart.destroy(); } catch(e){} }
  return null;
}

async function loadHistory() {
  var p = _getHistoryParams();
  var status = document.getElementById('history-status');
  status.textContent = 'Loading...';

  try {
    // Fetch token metrics
    var [tokIn, tokOut, costData, sessData, cronData] = await Promise.all([
      fetch('/api/history/metrics?metric=tokens_in_total&from='+p.from+'&to='+p.to+'&interval='+p.interval).then(r=>r.json()),
      fetch('/api/history/metrics?metric=tokens_out_total&from='+p.from+'&to='+p.to+'&interval='+p.interval).then(r=>r.json()),
      fetch('/api/history/metrics?metric=cost_total&from='+p.from+'&to='+p.to+'&interval='+p.interval).then(r=>r.json()),
      fetch('/api/history/metrics?metric=sessions_active&from='+p.from+'&to='+p.to+'&interval='+p.interval).then(r=>r.json()),
      fetch('/api/history/crons?from='+p.from+'&to='+p.to).then(r=>r.json()),
    ]);

    // Token chart
    _histTokensChart = _destroyChart(_histTokensChart);
    var tokInPts = (tokIn.data||[]).map(function(d){ return {x: new Date((d.bucket_ts||d.timestamp)*1000), y: d.avg_val||d.metric_value||0}; });
    var tokOutPts = (tokOut.data||[]).map(function(d){ return {x: new Date((d.bucket_ts||d.timestamp)*1000), y: d.avg_val||d.metric_value||0}; });
    var ctx1 = document.getElementById('history-tokens-chart').getContext('2d');
    _histTokensChart = new Chart(ctx1, {
      type: 'line',
      data: {
        datasets: [
          { label: 'Input Tokens', data: tokInPts, borderColor: '#6366f1', backgroundColor: 'rgba(99,102,241,0.1)', fill: true, tension: 0.3, pointRadius: 1 },
          { label: 'Output Tokens', data: tokOutPts, borderColor: '#f59e0b', backgroundColor: 'rgba(245,158,11,0.1)', fill: true, tension: 0.3, pointRadius: 1 }
        ]
      },
      options: _chartOpts('Token Usage', 'Tokens')
    });

    // Cost chart
    _histCostChart = _destroyChart(_histCostChart);
    var costPts = (costData.data||[]).map(function(d){ return {x: new Date((d.bucket_ts||d.timestamp)*1000), y: d.avg_val||d.metric_value||0}; });
    var ctx2 = document.getElementById('history-cost-chart').getContext('2d');
    _histCostChart = new Chart(ctx2, {
      type: 'line',
      data: {
        datasets: [
          { label: 'Total Cost ($)', data: costPts, borderColor: '#10b981', backgroundColor: 'rgba(16,185,129,0.1)', fill: true, tension: 0.3, pointRadius: 1 }
        ]
      },
      options: _chartOpts('Cost', 'USD')
    });

    // Sessions chart
    _histSessionsChart = _destroyChart(_histSessionsChart);
    var sessPts = (sessData.data||[]).map(function(d){ return {x: new Date((d.bucket_ts||d.timestamp)*1000), y: d.avg_val||d.metric_value||0}; });
    var ctx3 = document.getElementById('history-sessions-chart').getContext('2d');
    _histSessionsChart = new Chart(ctx3, {
      type: 'line',
      data: {
        datasets: [
          { label: 'Active Sessions', data: sessPts, borderColor: '#8b5cf6', backgroundColor: 'rgba(139,92,246,0.1)', fill: true, tension: 0.3, pointRadius: 2, stepped: 'before' }
        ]
      },
      options: _chartOpts('Sessions', 'Count')
    });

    // Cron runs table
    var runs = cronData.data || [];
    var cronHtml = '';
    if (runs.length === 0) {
      cronHtml = '<div style="color:var(--text-muted);padding:20px;text-align:center;">No cron runs in this time range</div>';
    } else {
      cronHtml = '<table style="width:100%;border-collapse:collapse;"><thead><tr style="border-bottom:1px solid var(--border-primary);"><th style="text-align:left;padding:4px 8px;font-size:11px;color:var(--text-muted);">Time</th><th style="text-align:left;padding:4px 8px;font-size:11px;color:var(--text-muted);">Job</th><th style="text-align:left;padding:4px 8px;font-size:11px;color:var(--text-muted);">Status</th><th style="text-align:right;padding:4px 8px;font-size:11px;color:var(--text-muted);">Duration</th></tr></thead><tbody>';
      runs.slice(-100).reverse().forEach(function(r) {
        var t = new Date(r.timestamp * 1000).toLocaleString();
        var statusColor = r.status === 'success' || r.status === 'completed' ? '#10b981' : (r.status === 'error' || r.status === 'failed' ? '#ef4444' : '#f59e0b');
        var dur = r.duration_ms ? (r.duration_ms/1000).toFixed(1)+'s' : '--';
        cronHtml += '<tr style="border-bottom:1px solid var(--border-secondary);"><td style="padding:4px 8px;font-size:12px;">'+t+'</td><td style="padding:4px 8px;font-size:12px;">'+((r.job_name||r.job_id)||'--')+'</td><td style="padding:4px 8px;font-size:12px;"><span style="color:'+statusColor+';font-weight:600;">&#9679;</span> '+(r.status||'--')+'</td><td style="padding:4px 8px;font-size:12px;text-align:right;">'+dur+'</td></tr>';
      });
      cronHtml += '</tbody></table>';
    }
    document.getElementById('history-cron-table').innerHTML = cronHtml;

    // Update status
    var totalPts = (tokIn.data||[]).length + (costData.data||[]).length;
    status.textContent = totalPts > 0 ? totalPts + ' data points' : 'No data yet -- collector polls every 60s';
  } catch(e) {
    status.textContent = 'Error: ' + e.message;
    console.error('History load error:', e);
  }
}

async function showSnapshot(ts) {
  try {
    var r = await fetch('/api/history/snapshot/' + ts);
    var data = await r.json();
    document.getElementById('snapshot-title').textContent = 'Snapshot @ ' + new Date(ts * 1000).toLocaleString();
    document.getElementById('snapshot-content').textContent = JSON.stringify(data.raw_json || data, null, 2);
    document.getElementById('snapshot-modal').style.display = 'flex';
  } catch(e) {
    console.error('Snapshot error:', e);
  }
}

// ── NemoClaw: duplicate stub removed; see loadNemoClaw() above ────────────────
// (The live implementation lives earlier in this file at the // NemoClaw Governance Tab comment)
/* if (false) { async function loadNemoClaw() { // dead code stub
  try {
    var data = await fetch('/api/nemoclaw/status').then(function(r) { return r.json(); });
    if (!data.installed) {
      document.getElementById('nemoclaw-tab').style.display = 'none';
      return;
    }
    document.getElementById('nemoclaw-tab').style.display = '';

    // Header chips
    var state = data.state || {};
    var cfg = data.config || {};
    var sandboxEl = document.getElementById('nc-sandbox-name');
    if (sandboxEl) sandboxEl.textContent = state.sandboxName || cfg.profile || '';
    var bpVerEl = document.getElementById('nc-blueprint-ver');
    if (bpVerEl) bpVerEl.textContent = state.blueprintVersion || '';

    // Sandbox panel
    var statusEl = document.getElementById('nc-sandbox-status');
    if (statusEl) {
      var statusText = state.lastAction ? state.lastAction : 'unknown';
      statusEl.textContent = statusText;
      statusEl.style.color = (statusText.indexOf('run') !== -1 || statusText.indexOf('start') !== -1) ? '#22c55e' : 'var(--text-primary)';
    }
    var bpVer2 = document.getElementById('nc-blueprint-ver2');
    if (bpVer2) bpVer2.textContent = state.blueprintVersion || '—';
    var lastAction = document.getElementById('nc-last-action');
    if (lastAction) lastAction.textContent = state.lastAction || '—';
    var runId = document.getElementById('nc-run-id');
    if (runId) runId.textContent = state.lastRunId || '—';

    // Inference panel
    var provEl = document.getElementById('nc-provider');
    if (provEl) provEl.textContent = cfg.provider || '—';
    var modelEl = document.getElementById('nc-model');
    if (modelEl) modelEl.textContent = cfg.model || '—';
    var epEl = document.getElementById('nc-endpoint');
    if (epEl) epEl.textContent = cfg.endpoint || '—';
    var onbEl = document.getElementById('nc-onboarded');
    if (onbEl) {
      var ob = cfg.onboardedAt || '';
      if (ob) { try { ob = new Date(ob).toLocaleDateString(); } catch(e) {} }
      onbEl.textContent = ob || '—';
    }

    // Policy
    var hashEl = document.getElementById('nc-policy-hash');
    if (hashEl) hashEl.textContent = data.policy_hash ? 'hash: ' + data.policy_hash : '';

    var driftBadge = document.getElementById('nc-drift-badge');
    var driftAlert = document.getElementById('nc-drift-alert');
    var driftDetail = document.getElementById('nc-drift-detail');
    if (data.policy_drifted) {
      if (driftBadge) { driftBadge.textContent = '⚠️ Policy drift detected'; driftBadge.style.color = '#ef4444'; }
      if (driftAlert) driftAlert.style.display = 'block';
      if (driftDetail && data.drift_info) {
        driftDetail.textContent = 'Old: ' + (data.drift_info.old_hash || '?') + '  →  New: ' + (data.drift_info.new_hash || '?') + '\nDetected: ' + (data.drift_info.detected_at || '');
      }
    } else {
      if (driftBadge) { driftBadge.textContent = '✅ No drift'; driftBadge.style.color = '#22c55e'; }
      if (driftAlert) driftAlert.style.display = 'none';
    }

    // Network policies table
    var policyEl = document.getElementById('nc-policy-table');
    if (policyEl) {
      var policies = data.network_policies || [];
      if (policies.length === 0) {
        policyEl.innerHTML = '<div style="color:var(--text-muted);">No network policies found</div>';
      } else {
        var rows = policies.map(function(p) {
          var hosts = Array.isArray(p.hosts) ? p.hosts.join(', ') : (p.hosts || '');
          return '<tr><td style="color:#76b900;padding:2px 12px 2px 0;white-space:nowrap;">' + _ncEsc(p.name) + '</td>'
               + '<td style="color:var(--text-secondary);">' + _ncEsc(hosts) + '</td></tr>';
        }).join('');
        policyEl.innerHTML = '<table style="width:100%;border-collapse:collapse;">' + rows + '</table>';
      }
    }

    // Presets
    var presetsEl = document.getElementById('nc-presets');
    if (presetsEl) {
      var presets = data.presets || [];
      if (presets.length === 0) {
        presetsEl.innerHTML = '<span style="color:var(--text-muted);font-size:12px;">None detected</span>';
      } else {
        presetsEl.innerHTML = presets.map(function(p) {
          return '<span style="background:rgba(118,185,0,0.12);color:#76b900;border:1px solid rgba(118,185,0,0.25);border-radius:12px;padding:3px 12px;font-size:12px;font-weight:600;">' + _ncEsc(p) + '</span>';
        }).join('');
      }
    }
  } catch(e) {
    console.error('NemoClaw load error:', e);
  }
}

function _ncEsc(s) {
  return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
}

// On page load: check NemoClaw and show tab if installed
(function() {
  try {
    fetch('/api/nemoclaw/status').then(function(r) { return r.json(); }).then(function(d) {
      if (d && d.installed) {
        var t = document.getElementById('nemoclaw-tab');
        if (t) t.style.display = '';
      }
    }).catch(function(){});
  } catch(e) {}
})();
} } // end if(false) stub */
