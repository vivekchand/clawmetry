// Alerts tab — Cloud-Pro feature with soft paywall.
//
// Tier states (resolved via /api/cloud-cta/status + /api/cloud-proxy/account):
//   - none:    no cloud token             → "Sign up for Cloud" CTA
//   - free:    cloud, plan=free           → "Upgrade to Pro" CTA
//   - trial:   cloud, plan=trial          → trial banner + full UI
//   - pro:     cloud, plan=cloud_pro/pro  → full UI
//
// All cloud calls go through /api/cloud-proxy/<path> which the OSS Flask
// dashboard forwards to https://app.clawmetry.com with the user's cm_ token
// injected from ~/.openclaw/openclaw.json.

(function () {
  'use strict';

  let alertsState = {
    tier: 'unknown',         // 'none' | 'free' | 'trial' | 'pro' | 'unknown'
    trialDaysLeft: null,
    rules: [],
    channels: [],
    history: [],
    editorRule: null,        // currently-being-edited rule, or null for new
    editorType: 'node_offline',
  };

  // Decrypt the E2E rules_blob the cloud returns on a cache hit. The shared
  // unwrapListAsync() can't do it here: it reads the key as
  // ``cm-enc-key-{node_id}`` and calls window.decryptBlob, but the real key
  // is ``cm-enc-key-{node_id}-{token_prefix}`` and decryptBlob no longer
  // exists — so it silently returned [] and saved rules never rendered. This
  // mirrors the working cm-cloud-* interceptor decrypt (_cmNormKey +
  // crypto.subtle). Returns the rules array, or [] on any failure.
  async function alertsDecryptRulesBlob(blobB64) {
    try {
      const nid = window.CLOUD_NODE_ID || '';
      const tok = window.CLOUD_TOKEN || '';
      const ac = tok.slice(0, 16);
      const kn = nid && ac ? ('cm-enc-key-' + nid + '-' + ac) : null;
      const k = kn ? localStorage.getItem(kn) : '';
      if (!k || typeof window._cmNormKey !== 'function') return [];
      const nk = await window._cmNormKey(k);
      const b64u = (s) => {
        s = s.replace(/-/g, '+').replace(/_/g, '/');
        while (s.length % 4) s += '=';
        const b = atob(s), a = new Uint8Array(b.length);
        for (let i = 0; i < b.length; i++) a[i] = b.charCodeAt(i);
        return a.buffer;
      };
      const ck = await crypto.subtle.importKey('raw', b64u(nk), { name: 'AES-GCM' }, false, ['decrypt']);
      const raw = new Uint8Array(b64u(blobB64));
      const iv = raw.slice(0, 12);
      const ct = raw.slice(12);
      const pt = await crypto.subtle.decrypt({ name: 'AES-GCM', iv }, ck, ct);
      return JSON.parse(new TextDecoder().decode(pt));
    } catch { return []; }
  }

  // ── Paywall helpers ───────────────────────────────────────────────────────

  function openPaywall() {
    var m = document.getElementById('alerts-paywall-modal');
    if (m) m.style.display = 'flex';
  }

  window.alertsClosePaywall = function (e) {
    if (e && e.target !== document.getElementById('alerts-paywall-modal')) return;
    var m = document.getElementById('alerts-paywall-modal');
    if (m) m.style.display = 'none';
  };

  window.alertsCtaClick = function () {
    window.open('https://app.clawmetry.com/?ref=alerts-cta', '_blank');
  };

  // ── Pro editor helpers ────────────────────────────────────────────────────

  function openEditor() {
    var m = document.getElementById('alerts-editor-modal');
    if (m) m.style.display = 'flex';
    alertsRenderTypeForm(alertsState.editorType);
    alertsRenderEditorChannels();
    var title = document.getElementById('alerts-editor-title');
    if (title) title.textContent = alertsState.editorRule && alertsState.editorRule.id ? 'Edit alert rule' : 'New alert rule';
  }

  window.alertsCloseEditor = function (e) {
    if (e && e.target !== document.getElementById('alerts-editor-modal')) return;
    var m = document.getElementById('alerts-editor-modal');
    if (m) m.style.display = 'none';
  };

  // ── Rule type form ────────────────────────────────────────────────────────

  function alertsRenderTypeForm(type) {
    var form = document.getElementById('alerts-editor-form');
    if (!form) return;
    var rule = alertsState.editorRule || {};
    var fields = {
      daily_spend:      [['Threshold ($)', 'number', 'threshold', rule.threshold || 10]],
      node_offline:     [['Offline for (min)', 'number', 'threshold', rule.threshold || 5]],
      session_cost:     [['Session cost ($)', 'number', 'threshold', rule.threshold || 2]],
      session_duration: [['Duration (min)', 'number', 'threshold', rule.threshold || 30]],
      token_velocity:   [['Tokens/min', 'number', 'threshold', rule.threshold || 5000]],
      subagent_depth:   [['Max depth', 'number', 'threshold', rule.threshold || 5]],
      cron_failure:     [],
      error_rate:       [['Error rate (%)', 'number', 'threshold', rule.threshold || 20]],
    };
    var rows = (fields[type] || []).map(function(f) {
      return '<label style="font-size:13px;color:var(--text-secondary);display:flex;gap:8px;align-items:center;">' +
        f[0] + ': <input type="' + f[1] + '" id="ae-' + f[2] + '" value="' + f[3] +
        '" style="width:80px;padding:4px 8px;border:1px solid var(--border-primary);border-radius:6px;background:var(--bg-tertiary);color:var(--text-primary);"></label>';
    }).join('');
    form.innerHTML = rows || '<div style="color:var(--text-muted);font-size:12px;">Triggers on any occurrence.</div>';
  }

  window.alertsPickType = function (type) {
    alertsState.editorType = type;
    document.querySelectorAll('#alerts-type-seg button').forEach(function(b) {
      b.classList.toggle('active', b.dataset.type === type);
    });
    alertsRenderTypeForm(type);
  };

  // ── Channel picker (inside editor) ────────────────────────────────────────

  async function alertsRenderEditorChannels() {
    var el = document.getElementById('alerts-editor-channels');
    if (!el) return;
    // Load channels from cloud proxy
    try {
      var data = await fetch('/api/cloud-proxy/channels').then(function(r) { return r.json(); });
      var channels = Array.isArray(data) ? data : (data.channels || []);
      if (!channels.length) {
        el.innerHTML = '<div style="color:var(--text-muted);font-size:12px;">No channels configured yet. Add one below.</div>';
        return;
      }
      var selectedIds = (alertsState.editorRule && alertsState.editorRule.channel_ids) || [];
      el.innerHTML = channels.map(function(ch) {
        var checked = selectedIds.includes(ch.id) ? ' checked' : '';
        return '<label style="font-size:13px;display:flex;gap:8px;align-items:center;">' +
          '<input type="checkbox" value="' + ch.id + '"' + checked + '> ' + ch.name + '</label>';
      }).join('');
    } catch(e) {
      el.innerHTML = '<div style="color:var(--text-muted);font-size:12px;">Could not load channels.</div>';
    }
  }

  // ── Render helpers ────────────────────────────────────────────────────────

  const EXAMPLE_RULES = [
    { id: 'example_cost',      alert_type: 'daily_spend',  threshold: 10,   enabled: false, name: 'Daily cost spike',      description: 'Alert when daily spend exceeds $10' },
    { id: 'example_agent',     alert_type: 'node_offline', threshold: 5,    enabled: false, name: 'Agent offline',         description: 'Alert when agent is offline for > 5 min' },
    { id: 'example_session',   alert_type: 'session_cost', threshold: 2,    enabled: false, name: 'Session cost',          description: 'Alert when session cost exceeds $2' },
    { id: 'example_velocity',  alert_type: 'token_velocity', threshold: 5000, enabled: false, name: 'Token velocity',      description: 'Alert on token spike > 5000/min' },
    { id: 'example_cron',      alert_type: 'cron_failure', threshold: 1,    enabled: false, name: 'Cron failure',          description: 'Alert on any cron job failure' },
    { id: 'example_error',     alert_type: 'error_rate',   threshold: 20,   enabled: false, name: 'Tool error rate',       description: 'Alert when tool error rate > 20%' },
  ];

  const ALERT_META = {
    daily_spend:      { icon: '💰', verb: 'Daily cost exceeds' },
    session_cost:     { icon: '🧵', verb: 'Session cost exceeds' },
    node_offline:     { icon: '🤖', verb: 'Agent offline >' },
    session_duration: { icon: '⏱',  verb: 'Session duration >' },
    token_velocity:   { icon: '⚡', verb: 'Tokens/min >' },
    subagent_depth:   { icon: '🌳', verb: 'Sub-agent depth >' },
    cron_failure:     { icon: '⏰', verb: 'Cron failed >' },
    error_rate:       { icon: '🛠', verb: 'Tool error rate >' },
  };

  function renderRules() {
    var el = document.getElementById('alerts-rules-list');
    if (!el) return;
    var rules = alertsState.rules;
    var html = '';

    if (!rules.length && (alertsState.tier !== 'pro' && alertsState.tier !== 'trial')) {
      // Show canned example teaser for non-Pro (one rule only)
      var ex = EXAMPLE_RULES[0];
      var meta = ALERT_META[ex.alert_type] || { icon: '🔔', verb: '' };
      html += '<div class="alerts-rule-row" style="opacity:0.6">';
      html += '<div class="alerts-rule-icon">' + meta.icon + '</div>';
      html += '<div class="alerts-rule-body">';
      html += '<div class="alerts-rule-name">' + ex.name + '</div>';
      html += '<div class="alerts-rule-desc">' + ex.description + '</div>';
      html += '</div>';
      html += '<label class="alerts-toggle"><input type="checkbox" onchange="alertsToggleRule(\'' + ex.id + '\', this.checked)" ' + (ex.enabled ? 'checked' : '') + '><span class="alerts-toggle-slider"></span></label>';
      html += '</div>';
      el.innerHTML = html;
      return;
    }

    if (!rules.length) {
      el.innerHTML = '<div class="alerts-empty">No alert rules yet. Click \'+ New alert rule\' to add one.</div>';
      return;
    }

    rules.forEach(function(rule) {
      var meta = ALERT_META[rule.alert_type] || { icon: '🔔', verb: '' };
      html += '<div class="alerts-rule-row">';
      html += '<div class="alerts-rule-icon">' + meta.icon + '</div>';
      html += '<div class="alerts-rule-body">';
      html += '<div class="alerts-rule-name">' + (rule.name || rule.alert_type) + '</div>';
      html += '<div class="alerts-rule-desc">' + meta.verb + ' ' + (rule.threshold || '') + '</div>';
      html += '</div>';
      html += '<div style="display:flex;gap:8px;align-items:center;">';
      html += '<button class="alerts-rule-edit" onclick="alertsHandleEditRule(\'' + rule.id + '\')">✏️</button>';
      html += '<button class="alerts-rule-del" onclick="alertsDeleteRule(\'' + rule.id + '\')">🗑️</button>';
      html += '<label class="alerts-toggle"><input type="checkbox" onchange="alertsToggleRule(\'' + rule.id + '\', this.checked)" ' + (rule.enabled ? 'checked' : '') + '><span class="alerts-toggle-slider"></span></label>';
      html += '</div>';
      html += '</div>';
    });
    el.innerHTML = html;
  }

  function renderHistory() {
    var el = document.getElementById('alerts-history-list');
    if (!el) return;
    var history = alertsState.history;
    if (!history.length) {
      el.innerHTML = '<div class="alerts-empty">No alerts triggered yet.</div>';
      return;
    }
    var html = history.map(function(ev) {
      var d = new Date(ev.triggered_at * 1000);
      var ts = d.toLocaleString();
      return '<div class="alerts-history-row"><span class="alerts-history-ts">' + ts + '</span>' +
        '<span class="alerts-history-msg">' + (ev.message || ev.alert_type || '') + '</span></div>';
    }).join('');
    el.innerHTML = html;
  }

  // ── API calls ─────────────────────────────────────────────────────────────

  async function fetchTier() {
    try {
      // Check OSS status endpoint first
      var oss = await fetch('/api/cloud-cta/status').then(function(r) { return r.json(); });
      if (oss && oss.cloud_connected === false) {
        alertsState.tier = 'none';
        return;
      }
      // Check Pro account
      var acct = await fetch('/api/cloud-proxy/account').then(function(r) { return r.json(); });
      if (acct && (acct.plan === 'cloud_pro' || acct.plan === 'pro')) {
        alertsState.tier = 'pro';
      } else if (acct && acct.plan === 'trial' && acct.trial_days_left > 0) {
        alertsState.tier = 'trial';
        alertsState.trialDaysLeft = acct.trial_days_left;
      } else {
        alertsState.tier = 'free';
      }
    } catch {
      alertsState.tier = 'none';
    }
  }

  async function fetchRules() {
    if (alertsState.tier !== 'pro' && alertsState.tier !== 'trial') return;
    try {
      // Try cloud proxy first (has E2E-encrypted rules_blob on cache hit)
      var data = await fetch('/api/cloud-proxy/alert-rules').then(function(r) { return r.json(); });
      var rules = [];
      if (data && data.rules_blob) {
        rules = await alertsDecryptRulesBlob(data.rules_blob);
      }
      if (!rules.length && data && Array.isArray(data.rules)) {
        rules = data.rules;
      }
      // Fall back to local rules endpoint if proxy returns nothing
      if (!rules.length) {
        var local = await fetch('/api/alerts/rules').then(function(r) { return r.json(); });
        rules = Array.isArray(local) ? local : (local.rules || []);
      }
      alertsState.rules = rules;
    } catch {
      alertsState.rules = [];
    }
  }

  async function fetchHistory() {
    if (alertsState.tier !== 'pro' && alertsState.tier !== 'trial') return;
    try {
      var data = await fetch('/api/alerts/history').then(function(r) { return r.json(); });
      alertsState.history = Array.isArray(data) ? data : (data.history || []);
    } catch {
      alertsState.history = [];
    }
  }

  // ── Init ──────────────────────────────────────────────────────────────────

  async function init() {
    await fetchTier();
    applyTierUI();
    await Promise.all([fetchRules(), fetchHistory()]);
    renderRules();
    renderHistory();
    updateChannelsSummary();
  }

  function applyTierUI() {
    var t = alertsState.tier;
    var paywallTitle = document.getElementById('alerts-paywall-title');
    var paywallBody  = document.getElementById('alerts-paywall-body');
    var paywallCta   = document.getElementById('alerts-paywall-cta');
    if (t === 'none') {
      if (paywallTitle) paywallTitle.textContent = 'Sign up for ClawMetry Cloud';
      if (paywallBody)  paywallBody.textContent  = 'Alerts need the cloud to deliver Slack / PagerDuty / Telegram / Email messages. Sign up — your data stays encrypted, Pro features include a 7-day free trial.';
      if (paywallCta)   paywallCta.textContent   = 'Sign up for Cloud';
    } else if (t === 'free') {
      if (paywallTitle) paywallTitle.textContent = 'Upgrade to Pro';
      if (paywallBody)  paywallBody.textContent  = 'Your free plan includes 1 example rule. Upgrade to Pro to create unlimited rules with Slack, PagerDuty, and email delivery.';
      if (paywallCta)   paywallCta.textContent   = 'Upgrade to Pro';
    }
  }

  async function updateChannelsSummary() {
    var el = document.getElementById('alerts-channels-summary');
    if (!el) return;
    if (alertsState.tier === 'pro' || alertsState.tier === 'trial') {
      try {
        var data = await fetch('/api/cloud-proxy/channels').then(function(r) { return r.json(); });
        var channels = Array.isArray(data) ? data : (data.channels || []);
        el.textContent = channels.length ? channels.map(function(c) { return c.name; }).join(' · ') : 'None configured';
      } catch {
        el.textContent = 'Slack · Email · PagerDuty · Telegram';
      }
    } else {
      el.textContent = 'Slack · Discord · Webhook (direct)';
    }
  }

  // ── Public API ────────────────────────────────────────────────────────────

  window.alertsHandleNewRule = function () {
    if (alertsState.tier !== 'pro' && alertsState.tier !== 'trial') {
      return openPaywall();
    }
    alertsState.editorRule = null;
    alertsState.editorType = 'node_offline';
    openEditor();
  };

  window.alertsHandleEditRule = function (ruleId) {
    if (alertsState.tier !== 'pro' && alertsState.tier !== 'trial') {
      return openPaywall();
    }
    var rule = alertsState.rules.find(function(r) { return r.id === ruleId; });
    if (!rule) return;
    alertsState.editorRule = rule;
    alertsState.editorType = rule.alert_type;
    openEditor();
  };

  window.alertsHandleManageChannels = function () {
    if (alertsState.tier === 'pro' || alertsState.tier === 'trial') {
      // Pro/trial: full cloud channel management (PagerDuty, email, on-call)
      window.open('https://app.clawmetry.com/cloud#channels', '_blank');
    } else {
      // OSS/free: open the Budget & Alerts modal on the "Alert Rules" tab where
      // Slack/Discord direct-webhook config lives. Cloud-routed channels
      // (PagerDuty, email, on-call) remain Pro-only.
      openBudgetModal();
      var alertsTab = document.querySelector('#budget-modal-tabs .modal-tab:nth-child(2)');
      switchBudgetTab('alerts', alertsTab);
    }
  };

  window.alertsHandleUpgrade = function () {
    window.open('https://app.clawmetry.com/pricing', '_blank');
  };

  window.alertsToggleRule = async function (ruleId, newEnabled) {
    if (alertsState.tier !== 'pro' && alertsState.tier !== 'trial') {
      return openPaywall();
    }
    // An optimistic ``pending-`` rule has no server id yet — its real create
    // is still in flight. Just adjust local state (remove on toggle-off) so a
    // double-click doesn't PUT a non-existent id; the reconcile reload syncs.
    if (String(ruleId).startsWith('pending-')) {
      if (!newEnabled) {
        alertsState.rules = alertsState.rules.filter(r => r.id !== ruleId);
        renderRules();
      }
      return;
    }
    try {
      // Enabling a canned EXAMPLE creates a real rule from the template.
      // The old code PUT '/api/alerts/example_cost' which 404s ("unknown
      // example id"), caught + swallowed -> "Enable does nothing". A real
      // (already-saved) rule still goes through the PUT toggle path.
      const ex = EXAMPLE_RULES.find(r => r.id === ruleId);
      const isExample = !!ex && !alertsState.rules.find(r => r.id === ruleId);
      // Dedup: never POST a second rule for a type that already has one
      // (rapid clicks before the cache warms created duplicates).
      if (isExample && newEnabled &&
          alertsState.rules.find(r => r.alert_type === ex.alert_type)) {
        return;
      }
      let resp;
      if (isExample && newEnabled) {
        // POST to /api/alerts/rules to create a real rule from the example template
        const body = {
          name: ex.name,
          alert_type: ex.alert_type,
          threshold: ex.threshold,
          enabled: true,
        };
        resp = await fetch('/api/alerts/rules', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(body),
        });
        if (resp.ok) {
          const created = await resp.json();
          const newRule = {
            id: 'pending-' + Date.now(),
            ...body,
            ...created,
          };
          alertsState.rules = [...alertsState.rules, newRule];
          renderRules();
          // Reload after short delay to get real server id
          setTimeout(function() {
            fetchRules().then(renderRules);
          }, 800);
        }
        return;
      }
      resp = await fetch('/api/alerts/rules/' + ruleId, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ enabled: newEnabled }),
      });
      if (resp.ok) {
        var rule = alertsState.rules.find(function(r) { return r.id === ruleId; });
        if (rule) rule.enabled = newEnabled;
        renderRules();
      }
    } catch(e) {
      console.error('alertsToggleRule error', e);
    }
  };

  window.alertsDeleteRule = async function (ruleId) {
    if (!confirm('Delete this alert rule?')) return;
    try {
      await fetch('/api/alerts/rules/' + ruleId, { method: 'DELETE' });
      alertsState.rules = alertsState.rules.filter(function(r) { return r.id !== ruleId; });
      renderRules();
    } catch(e) {
      console.error('alertsDeleteRule error', e);
    }
  };

  window.alertsSaveRule = async function () {
    if (alertsState.tier !== 'pro' && alertsState.tier !== 'trial') return;
    var type = alertsState.editorType;
    var thresholdEl = document.getElementById('ae-threshold');
    var threshold = thresholdEl ? parseFloat(thresholdEl.value) : null;
    var channelEls = document.querySelectorAll('#alerts-editor-channels input[type="checkbox"]:checked');
    var channelIds = Array.from(channelEls).map(function(el) { return el.value; });
    var rule = alertsState.editorRule;
    var reEl = document.querySelector('input[name="alerts-re"]:checked');
    var reAlert = reEl ? reEl.value : 'once';
    var body = {
      alert_type: type,
      threshold: threshold,
      channel_ids: channelIds,
      re_alert: reAlert,
      enabled: true,
    };
    if (rule && rule.id) body.id = rule.id;
    try {
      var method = (rule && rule.id) ? 'PUT' : 'POST';
      var url = (rule && rule.id) ? ('/api/alerts/rules/' + rule.id) : '/api/alerts/rules';
      var resp = await fetch(url, {
        method: method,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      });
      if (resp.ok) {
        window.alertsCloseEditor();
        await fetchRules();
        renderRules();
      }
    } catch(e) {
      console.error('alertsSaveRule error', e);
    }
  };

  // ── Boot ──────────────────────────────────────────────────────────────────
  // Defer until DOMContentLoaded so the template elements exist.
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }

}());
