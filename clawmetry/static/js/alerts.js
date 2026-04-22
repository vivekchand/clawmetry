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

  // ── Tier resolution ───────────────────────────────────────────────────────

  async function resolveTier() {
    try {
      const status = await fetch('/api/cloud-cta/status').then(r => r.json());
      if (!status.connected) return { tier: 'none' };
      const acct = await fetch('/api/cloud-proxy/api/cloud/account').then(r => r.json());
      const plan = (acct.plan || 'free').toLowerCase();
      if (plan === 'cloud_pro' || plan === 'pro') return { tier: 'pro' };
      if (plan === 'trial') {
        const days = parseInt(acct.trial_days_left || 0, 10);
        return { tier: days > 0 ? 'trial' : 'free', trialDaysLeft: days };
      }
      return { tier: 'free' };
    } catch (e) {
      console.warn('[alerts] tier resolution failed', e);
      return { tier: 'none' };
    }
  }

  // ── Page entry point ──────────────────────────────────────────────────────

  window.loadAlertsPage = async function () {
    document.getElementById('alerts-rules-list').innerHTML =
      '<div class="alerts-loading">Loading alerts…</div>';

    const t = await resolveTier();
    alertsState.tier = t.tier;
    alertsState.trialDaysLeft = t.trialDaysLeft || null;

    if (t.tier === 'trial' && t.trialDaysLeft != null) {
      const banner = document.getElementById('alerts-trial-banner');
      banner.style.display = '';
      document.getElementById('alerts-trial-days-left').textContent =
        ' · ' + t.trialDaysLeft + ' day' + (t.trialDaysLeft === 1 ? '' : 's') + ' left';
    } else {
      document.getElementById('alerts-trial-banner').style.display = 'none';
    }

    // For all tiers: try to load rules. If unauthenticated, fall back to
    // canned examples so the user still sees the value.
    if (t.tier === 'none') {
      renderCannedExamples();
      renderHistoryEmpty('Sign up for Cloud to start collecting alert history.');
      return;
    }

    try {
      const data = await fetch('/api/cloud-proxy/api/alerts').then(r => r.json());
      alertsState.rules = data.alerts || [];
    } catch {
      alertsState.rules = [];
    }
    renderRules();

    try {
      const hist = await fetch('/api/cloud-proxy/api/alerts/history?limit=10')
        .then(r => r.json());
      alertsState.history = hist.history || [];
    } catch {
      alertsState.history = [];
    }
    renderHistory();

    try {
      const ch = await fetch('/api/cloud-proxy/api/channels').then(r => r.json());
      alertsState.channels = ch.channels || [];
      renderChannelsSummary();
    } catch {
      alertsState.channels = [];
    }
  };

  // ── Renderers ─────────────────────────────────────────────────────────────

  const RULE_TYPE_LABELS = {
    daily_spend:      { icon: '💰', verb: 'Daily spend exceeds' },
    session_cost:     { icon: '🧵', verb: 'Session cost exceeds' },
    node_offline:     { icon: '🤖', verb: 'Agent offline >' },
    session_duration: { icon: '⏱',  verb: 'Session duration >' },
    token_velocity:   { icon: '⚡', verb: 'Tokens/min >' },
    subagent_depth:   { icon: '🌳', verb: 'Sub-agent depth >' },
    cron_failure:     { icon: '⏰', verb: 'Cron failed >' },
    error_rate:       { icon: '🛠', verb: 'Tool error rate >' },
  };

  function renderRules() {
    const wrap = document.getElementById('alerts-rules-list');
    if (!alertsState.rules.length) {
      renderCannedExamples();
      return;
    }
    wrap.innerHTML = alertsState.rules.map(rule => {
      const meta = RULE_TYPE_LABELS[rule.alert_type] || { icon: '🔔', verb: rule.alert_type };
      const channelPills = (rule.channel_ids || []).map(id => {
        const ch = alertsState.channels.find(c => c.id === id);
        if (!ch) return '';
        return `<span class="alerts-chan-pill">${chTypeIcon(ch.channel_type)} ${escape(ch.name)}</span>`;
      }).join('');
      const dotCls = rule.enabled ? 'on' : 'off';
      const ts = rule.last_triggered_at
        ? `Last: ${formatTimeAgo(rule.last_triggered_at)} · ${rule.trigger_count}× total`
        : `Never triggered`;
      return `
        <div class="alerts-rule-row" data-rule-id="${rule.id}">
          <div class="alerts-rule-dot ${dotCls}" title="${rule.enabled ? 'Enabled' : 'Disabled'}"
               onclick="alertsToggleRule('${rule.id}', ${!rule.enabled})"></div>
          <div class="alerts-rule-main">
            <div class="alerts-rule-title">${meta.icon} ${escape(rule.name)}</div>
            <div class="alerts-rule-meta">${meta.verb} ${rule.threshold_value}${rule.threshold_unit ? ' ' + escape(rule.threshold_unit) : ''} · ${ts}</div>
          </div>
          <div class="alerts-rule-chan">${channelPills || '<span class="alerts-chan-pill off">no channels</span>'}</div>
          <button class="alerts-btn-ghost" onclick="alertsHandleEdit('${rule.id}')">Edit</button>
        </div>
      `;
    }).join('');
  }

  function renderCannedExamples() {
    const examples = [
      { type: 'daily_spend', name: 'Daily spend > $50', threshold: 50, unit: 'USD', channels: '💬 Slack · ✉️ Email' },
      { type: 'node_offline', name: 'Agent offline > 10 min', threshold: 10, unit: 'min', channels: '📟 PagerDuty' },
      { type: 'session_cost', name: 'Session tokens > 1M', threshold: 1000000, unit: 'tokens', channels: '✉️ Email' },
      { type: 'cron_failure', name: 'Cron failed 3× in a row', threshold: 3, unit: 'fails', channels: '💬 Slack · ✈️ Telegram' },
      { type: 'error_rate', name: 'Tool failures > 5/hr', threshold: 5, unit: '/hr', channels: '✉️ Email' },
    ];
    const wrap = document.getElementById('alerts-rules-list');
    wrap.innerHTML = examples.map(ex => {
      const meta = RULE_TYPE_LABELS[ex.type];
      return `
        <div class="alerts-rule-row alerts-rule-example" onclick="alertsHandleNewRule()">
          <div class="alerts-rule-dot off"></div>
          <div class="alerts-rule-main">
            <div class="alerts-rule-title">${meta.icon} ${escape(ex.name)}
              <span class="alerts-rule-example-badge">example</span>
            </div>
            <div class="alerts-rule-meta">Tap to enable — requires Cloud Pro</div>
          </div>
          <div class="alerts-rule-chan"><span class="alerts-chan-pill off">${ex.channels}</span></div>
          <button class="alerts-btn-ghost" onclick="event.stopPropagation();alertsHandleNewRule()">Enable</button>
        </div>
      `;
    }).join('');
  }

  function renderHistory() {
    const wrap = document.getElementById('alerts-history-list');
    if (!alertsState.history.length) {
      return renderHistoryEmpty('No alerts have fired yet.');
    }
    wrap.innerHTML = alertsState.history.map(h => {
      const sev = h.resolved_at ? 'sev-green' : 'sev-red';
      const dot = h.resolved_at ? '●' : '●';
      const payload = h.payload || {};
      return `
        <div class="alerts-hist-row">
          <span class="${sev}">${dot}</span>
          <span class="alerts-hist-time">${formatTimeAgo(h.fired_at)}</span>
          <span class="alerts-hist-text"><b>${escape(payload.name || h.alert_id)}</b>
            → ${escape(String(payload.actual_value ?? ''))} ${escape(payload.threshold_unit || '')}</span>
        </div>
      `;
    }).join('');
  }

  function renderHistoryEmpty(msg) {
    document.getElementById('alerts-history-list').innerHTML =
      `<div class="alerts-loading">${escape(msg)}</div>`;
  }

  function renderChannelsSummary() {
    const wrap = document.getElementById('alerts-channels-summary');
    if (!alertsState.channels.length) {
      wrap.textContent = 'No channels configured yet';
      return;
    }
    const types = [...new Set(alertsState.channels.map(c => chTypeLabel(c.channel_type)))];
    wrap.textContent = types.join(' · ');
  }

  // ── Action handlers (paywall-aware) ───────────────────────────────────────

  window.alertsHandleNewRule = function () {
    if (alertsState.tier === 'pro' || alertsState.tier === 'trial') {
      alertsState.editorRule = null;
      alertsState.editorType = 'node_offline';
      openEditor();
    } else {
      openPaywall();
    }
  };

  window.alertsHandleEdit = function (ruleId) {
    if (alertsState.tier === 'pro' || alertsState.tier === 'trial') {
      const rule = alertsState.rules.find(r => r.id === ruleId);
      if (!rule) return;
      alertsState.editorRule = rule;
      alertsState.editorType = rule.alert_type;
      openEditor();
    } else {
      openPaywall();
    }
  };

  window.alertsHandleManageChannels = function () {
    if (alertsState.tier === 'pro' || alertsState.tier === 'trial') {
      // Channels management is a separate page — for now point to Cloud
      window.open('https://app.clawmetry.com/cloud#channels', '_blank');
    } else {
      openPaywall();
    }
  };

  window.alertsHandleUpgrade = function () {
    window.open('https://app.clawmetry.com/pricing', '_blank');
  };

  window.alertsToggleRule = async function (ruleId, newEnabled) {
    if (alertsState.tier !== 'pro' && alertsState.tier !== 'trial') {
      return openPaywall();
    }
    try {
      const resp = await fetch('/api/cloud-proxy/api/alerts/' + ruleId, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ enabled: newEnabled }),
      });
      if (resp.status === 402) {
        // Hit the Free-tier cap server-side
        return openPaywall();
      }
      if (!resp.ok) throw new Error('toggle failed: HTTP ' + resp.status);
      window.loadAlertsPage();
    } catch (e) {
      console.warn(e);
    }
  };

  // ── Paywall modal ─────────────────────────────────────────────────────────

  function openPaywall() {
    const modal = document.getElementById('alerts-paywall-modal');
    const title = document.getElementById('alerts-paywall-title');
    const body  = document.getElementById('alerts-paywall-body');
    const cta   = document.getElementById('alerts-paywall-cta');
    if (alertsState.tier === 'none') {
      title.textContent = 'Sign up for ClawMetry Cloud';
      body.textContent  = 'Alerts need the cloud to deliver Slack / PagerDuty / Telegram / Email messages. Sign up — your data stays encrypted, Pro features include a 7-day free trial.';
      cta.textContent   = 'Sign up for Cloud';
      cta.dataset.action = 'signup';
    } else {
      title.textContent = 'Upgrade to ClawMetry Pro';
      body.textContent  = 'Free plan allows 1 enabled alert. Upgrade to Pro for unlimited alerts, multi-channel delivery to Slack / PagerDuty / Telegram / Email, and 90-day alert history.';
      cta.textContent   = 'Start 7-day free trial';
      cta.dataset.action = 'upgrade';
    }
    modal.style.display = 'flex';
  }

  window.alertsClosePaywall = function (e) {
    if (e && e.target.id !== 'alerts-paywall-modal') return;
    document.getElementById('alerts-paywall-modal').style.display = 'none';
  };

  window.alertsCtaClick = function () {
    const cta = document.getElementById('alerts-paywall-cta');
    if (cta.dataset.action === 'signup' && typeof openCloudModal === 'function') {
      window.alertsClosePaywall();
      openCloudModal();
    } else {
      window.open('https://app.clawmetry.com/pricing', '_blank');
    }
  };

  // ── Editor modal (Pro tier) ───────────────────────────────────────────────

  function openEditor() {
    document.getElementById('alerts-editor-modal').style.display = 'flex';
    document.getElementById('alerts-editor-title').textContent =
      alertsState.editorRule ? 'Edit alert rule' : 'New alert rule';
    setActiveType(alertsState.editorType);
    renderEditorForm();
    renderEditorChannels();
    setEditorReAlert(alertsState.editorRule?.re_alert_policy || 'once');
  }

  window.alertsCloseEditor = function (e) {
    if (e && e.target.id !== 'alerts-editor-modal') return;
    document.getElementById('alerts-editor-modal').style.display = 'none';
  };

  window.alertsPickType = function (type) {
    alertsState.editorType = type;
    setActiveType(type);
    renderEditorForm();
  };

  function setActiveType(type) {
    document.querySelectorAll('#alerts-type-seg button').forEach(b => {
      b.classList.toggle('active', b.dataset.type === type);
    });
  }

  function renderEditorForm() {
    const t = alertsState.editorType;
    const r = alertsState.editorRule || {};
    const presets = {
      daily_spend:  { unit: 'USD',    placeholder: 50, label: 'Daily spend exceeds', name: 'Daily spend cap' },
      session_cost: { unit: 'USD',    placeholder: 5,  label: 'Single session cost exceeds', name: 'Session cost cap' },
      node_offline: { unit: 'min',    placeholder: 10, label: 'Agent has been offline for more than', name: 'Agent offline' },
      cron_failure: { unit: 'fails',  placeholder: 3,  label: 'Cron has failed in a row at least', name: 'Cron failure streak' },
      error_rate:   { unit: '%',      placeholder: 20, label: 'Tool failure rate exceeds', name: 'Tool failures' },
    };
    const p = presets[t] || { unit: '', placeholder: 0, label: 'Threshold', name: 'Custom alert' };
    const val = r.threshold_value ?? p.placeholder;
    document.getElementById('alerts-editor-form').innerHTML = `
      <div class="alerts-form-row">
        <label>Name</label>
        <input type="text" id="alerts-rule-name" value="${escape(r.name || p.name)}" />
      </div>
      <div class="alerts-form-row">
        <label>${p.label}</label>
        <input type="number" id="alerts-rule-threshold" value="${val}" step="any" style="width:120px;" />
        <span class="alerts-form-unit">${p.unit}</span>
      </div>
    `;
  }

  function renderEditorChannels() {
    const wrap = document.getElementById('alerts-editor-channels');
    if (!alertsState.channels.length) {
      wrap.innerHTML = '<div class="alerts-loading">No channels yet — add one below.</div>';
      return;
    }
    const selected = new Set(alertsState.editorRule?.channel_ids || []);
    wrap.innerHTML = alertsState.channels.map(ch => `
      <label class="alerts-chan-check">
        <input type="checkbox" data-channel-id="${ch.id}" ${selected.has(ch.id) ? 'checked' : ''} />
        <span class="name">${chTypeIcon(ch.channel_type)} ${chTypeLabel(ch.channel_type)}</span>
        <span class="dest">${escape(ch.name)}</span>
      </label>
    `).join('');
  }

  function setEditorReAlert(policy) {
    document.querySelectorAll('input[name="alerts-re"]').forEach(r => {
      r.checked = (r.value === policy);
    });
  }

  window.alertsSaveRule = async function () {
    const name = document.getElementById('alerts-rule-name').value.trim();
    const threshold = parseFloat(document.getElementById('alerts-rule-threshold').value);
    if (!name || isNaN(threshold)) return;
    const channelIds = [...document.querySelectorAll('#alerts-editor-channels input:checked')]
      .map(i => i.dataset.channelId);
    const policy = document.querySelector('input[name="alerts-re"]:checked')?.value || 'once';

    const body = {
      alert_type: alertsState.editorType,
      name,
      threshold_value: threshold,
      enabled: true,
      channel_ids: channelIds,
      re_alert_policy: policy,
    };

    const isEdit = !!alertsState.editorRule;
    const url = isEdit
      ? '/api/cloud-proxy/api/alerts/' + alertsState.editorRule.id
      : '/api/cloud-proxy/api/alerts';
    const method = isEdit ? 'PUT' : 'POST';

    const resp = await fetch(url, {
      method,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
    if (resp.status === 402) {
      window.alertsCloseEditor();
      return openPaywall();
    }
    if (!resp.ok) {
      console.warn('save failed', resp.status, await resp.text());
      return;
    }
    window.alertsCloseEditor();
    window.loadAlertsPage();
  };

  // ── Helpers ───────────────────────────────────────────────────────────────

  function chTypeIcon(type) {
    return ({ slack: '💬', email: '✉️', pagerduty: '📟', telegram: '✈️', phone: '📞' })[type] || '🔔';
  }
  function chTypeLabel(type) {
    return ({ slack: 'Slack', email: 'Email', pagerduty: 'PagerDuty', telegram: 'Telegram', phone: 'Phone' })[type] || type;
  }
  function escape(s) {
    if (s == null) return '';
    return String(s).replace(/[&<>"']/g, c =>
      ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[c]
    );
  }
  function formatTimeAgo(iso) {
    if (!iso) return '';
    try {
      const ts = new Date(iso);
      const sec = Math.floor((Date.now() - ts.getTime()) / 1000);
      if (sec < 60) return 'just now';
      if (sec < 3600) return Math.floor(sec / 60) + 'm ago';
      if (sec < 86400) return Math.floor(sec / 3600) + 'h ago';
      return Math.floor(sec / 86400) + 'd ago';
    } catch {
      return iso;
    }
  }
})();
