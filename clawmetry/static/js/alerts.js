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
      const txt = new TextDecoder().decode(
        await crypto.subtle.decrypt({ name: 'AES-GCM', iv: raw.slice(0, 12) }, ck, raw.slice(12)));
      const payload = JSON.parse(txt);
      const rules = payload.rules || payload.alerts || [];
      // The daemon stores the full cloud rule body inside ``condition_json``
      // (the top level only has id/name/enabled), so alert_type / threshold /
      // channel_ids live one level down. Flatten it up — otherwise the
      // merge-render's ``find(r.alert_type === ...)`` never matches and the
      // toggle stays OFF even though the rule exists. Top-level id/name/enabled
      // win (they're the authoritative live state).
      return rules.map(r => Object.assign({}, r.condition_json || {}, r));
    } catch (e) {
      return [];
    }
  }

  // Canned example rules shown to OSS-only / no-cloud users. Users can edit
  // these (change threshold, channels, name) before being asked to sign up --
  // investing in configuration first improves conversion.
  const EXAMPLE_RULES = [
    { id: 'example_cost',  alert_type: 'daily_spend',  name: 'Daily spend > $50',
      threshold_value: 50, threshold_unit: 'USD',
      _exampleChannels: '💬 Slack · ✉️ Email' },
    { id: 'example_agent', alert_type: 'node_offline', name: 'Agent offline > 10 min',
      threshold_value: 10, threshold_unit: 'min',
      _exampleChannels: '📟 PagerDuty' },
    { id: 'example_session', alert_type: 'session_cost', name: 'Session cost > $5',
      threshold_value: 5, threshold_unit: 'USD',
      _exampleChannels: '✉️ Email' },
    { id: 'example_velocity', alert_type: 'token_velocity', name: 'Token velocity > 10k/min',
      threshold_value: 10000, threshold_unit: 'tokens/min',
      _exampleChannels: '✈️ Telegram · ✉️ Email' },
    { id: 'example_cron', alert_type: 'cron_failure', name: 'Cron failed 3× in a row',
      threshold_value: 3, threshold_unit: 'fails',
      _exampleChannels: '💬 Slack · ✈️ Telegram' },
    { id: 'example_tool', alert_type: 'error_rate', name: 'Tool failures > 5/hr',
      threshold_value: 5, threshold_unit: '%',
      _exampleChannels: '✉️ Email' },
  ];

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
    // Trial banner removed in PR #791 — paywall fires on action (click
    // + New alert rule / Enable) for Free users instead. Trial/Pro users
    // have full access and see no upgrade prompt unless they hit a cap.

    // For all tiers: try to load rules. If unauthenticated, fall back to
    // canned examples so the user still sees the value.
    if (t.tier === 'none') {
      renderCannedExamples();
      renderHistoryEmpty('Sign up for Cloud to start collecting alert history.');
      return;
    }

    try {
      const data = await fetch('/api/cloud-proxy/api/alerts').then(r => r.json());
      // Cache hit returns an E2E-encrypted ``rules_blob`` ({rules:[...]}) that
      // only the browser can decrypt; cache miss returns plaintext
      // ``{alerts:[]}``. Reading data.alerts alone meant a saved rule (which
      // arrives encrypted) never rendered — the tab stayed on canned examples
      // forever. Decrypt the blob when present.
      let serverRules;
      if (data.rules_blob) {
        serverRules = await alertsDecryptRulesBlob(data.rules_blob);
      } else {
        serverRules = data.alerts || data.rules || [];
      }
      // Preserve optimistic ``pending-`` rules until the cloud cache catches
      // up (the daemon cache_push lags the write by ~2 heartbeats). Without
      // this the toggle visibly flips back OFF on the reconcile reload before
      // the rule appears — looking exactly like "Enable does nothing".
      const pending = (alertsState.rules || []).filter(r =>
        String(r.id).startsWith('pending-') &&
        !serverRules.find(s => s.alert_type === r.alert_type));
      alertsState.rules = serverRules.concat(pending);
    } catch {
      // keep existing (incl. optimistic) rules on a transient fetch error
    }
    renderRules();

    // Bug #1127: Badge counted local OSS fires while page only checked cloud
    // history -> badge "20" with page saying "no alerts fired". Fall back to
    // the same local /api/alerts/history the nav badge uses when cloud has
    // nothing (or errors), so the two stay consistent.
    try {
      const hist = await fetch('/api/cloud-proxy/api/alerts/history?limit=20')
        .then(r => r.json());
      alertsState.history = hist.history || [];
    } catch {
      alertsState.history = [];
    }
    if (!alertsState.history.length) {
      try {
        const local = await fetch('/api/alerts/history?limit=20').then(r => r.json());
        const localFires = (local.alerts || []).map(a => ({
          id: a.id,
          fired_at: a.fired_at,
          resolved_at: a.acknowledged ? a.ack_at : null,
          alert_id: a.rule_id,
          payload: { name: a.type, actual_value: a.message, threshold_unit: '' },
        }));
        alertsState.history = localFires;
      } catch {
        // keep empty
      }
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

  // On/off slider that matches the Approvals protection-rule toggle. Clicking
  // it flips the rule: OFF (example/disabled) -> creates+enables the rule;
  // ON -> disables it. ``alertsToggleRule`` handles create-from-example.
  function toggleSwitch(ruleId, on) {
    return '<div class="alerts-toggle-switch" onclick="event.stopPropagation();alertsToggleRule(\'' + ruleId + '\', ' + (on ? 'false' : 'true') + ')"'
      + ' title="' + (on ? 'Enabled — click to disable' : 'Disabled — click to enable') + '"'
      + ' style="position:relative;width:42px;height:24px;cursor:pointer;flex-shrink:0;">'
      + '<div style="position:absolute;inset:0;background:' + (on ? '#3b82f6' : '#374151') + ';border-radius:12px;transition:background 0.2s;"></div>'
      + '<div style="position:absolute;top:3px;left:' + (on ? '21px' : '3px') + ';width:18px;height:18px;background:#fff;border-radius:50%;transition:left 0.2s;box-shadow:0 1px 3px rgba(0,0,0,0.3);"></div>'
      + '</div>';
  }

  function renderRules() {
    const wrap = document.getElementById('alerts-rules-list');
    // Approvals-style: ALWAYS show the canonical alert types as on/off
    // toggles (default OFF). Each maps to a matching saved rule by
    // alert_type so the toggle reflects its real state; an OFF row uses the
    // example template and creates the rule on toggle-on. This keeps all
    // types visible after you enable one (the old render hid the rest).
    wrap.innerHTML = EXAMPLE_RULES.map(ex => {
      const real = alertsState.rules.find(r => r.alert_type === ex.alert_type);
      const on = !!(real && real.enabled);
      const id = real ? real.id : ex.id;
      const meta = RULE_TYPE_LABELS[ex.alert_type] || { icon: '🔔', verb: ex.alert_type };
      const name = real ? real.name : ex.name;
      const threshold = real ? real.threshold_value : ex.threshold_value;
      const unit = (real ? real.threshold_unit : ex.threshold_unit) || '';
      let metaLine;
      if (real && real.last_triggered_at) {
        metaLine = `Last: ${formatTimeAgo(real.last_triggered_at)} · ${real.trigger_count}× total`;
      } else {
        metaLine = `${meta.verb} ${threshold}${unit ? ' ' + escape(unit) : ''}`
          + (real ? ' · never triggered' : '');
      }
      const channelPills = real
        ? (real.channel_ids || []).map(cid => {
            const ch = alertsState.channels.find(c => c.id === cid);
            return ch ? `<span class="alerts-chan-pill">${chTypeIcon(ch.channel_type)} ${escape(ch.name)}</span>` : '';
          }).join('')
        : `<span class="alerts-chan-pill off">${ex._exampleChannels}</span>`;
      const badge = real ? '' : '<span class="alerts-rule-example-badge">example</span>';
      return `
        <div class="alerts-rule-row${real ? '' : ' alerts-rule-example'}" data-rule-id="${id}">
          <div class="alerts-rule-dot ${on ? 'on' : 'off'}" title="${on ? 'Enabled' : 'Disabled'}"></div>
          <div class="alerts-rule-main">
            <div class="alerts-rule-title">${meta.icon} ${escape(name)} ${badge}</div>
            <div class="alerts-rule-meta">${metaLine}</div>
          </div>
          <div class="alerts-rule-chan">${channelPills || '<span class="alerts-chan-pill off">no channels</span>'}</div>
          ${toggleSwitch(id, on)}
          <button class="alerts-btn-ghost" onclick="alertsHandleEdit('${id}')">Edit</button>
        </div>
      `;
    }).join('');
  }

  function renderCannedExamples() {
    const wrap = document.getElementById('alerts-rules-list');
    wrap.innerHTML = EXAMPLE_RULES.map(ex => {
      const meta = RULE_TYPE_LABELS[ex.alert_type];
      return `
        <div class="alerts-rule-row alerts-rule-example" onclick="alertsHandleEdit('${ex.id}')">
          <div class="alerts-rule-dot off"></div>
          <div class="alerts-rule-main">
            <div class="alerts-rule-title">${meta.icon} ${escape(ex.name)}
              <span class="alerts-rule-example-badge">example</span>
            </div>
            <div class="alerts-rule-meta">Tap to customize — saves require Cloud Pro</div>
          </div>
          <div class="alerts-rule-chan"><span class="alerts-chan-pill off">${ex._exampleChannels}</span></div>
          ${toggleSwitch(ex.id, false)}
          <button class="alerts-btn-ghost" onclick="event.stopPropagation();alertsHandleEdit('${ex.id}')">Edit</button>
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
    // Gate on click (not on Save): the banner that used to explain the trial
    // is gone, so Free / no-cloud users need an explicit prompt that this is
    // a Pro feature before they start filling out a form they can't save.
    // Trial + Pro users skip the paywall and get the editor directly.
    if (alertsState.tier !== 'pro' && alertsState.tier !== 'trial') {
      return openPaywall();
    }
    alertsState.editorRule = null;
    alertsState.editorType = 'node_offline';
    openEditor();
  };

  window.alertsHandleEdit = function (ruleId) {
    // Look up either a real rule (Pro tier) or a canned example (Free/OSS).
    let rule = alertsState.rules.find(r => r.id === ruleId);
    if (!rule) {
      rule = EXAMPLE_RULES.find(r => r.id === ruleId);
    }
    if (!rule) return;
    // Issue #1603: the editor modal DOM is server-side gated to Pro users
    // so Free users get the upsell here instead of a null-deref on
    // ``alerts-editor-modal``. Matches the alertsHandleNewRule gate above.
    if (alertsState.tier !== 'pro' && alertsState.tier !== 'trial') {
      return openPaywall();
    }
    alertsState.editorRule = rule;
    alertsState.editorType = rule.alert_type;
    openEditor();
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
        resp = await fetch('/api/cloud-proxy/api/alerts', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            alert_type: ex.alert_type,
            name: ex.name,
            threshold_value: ex.threshold_value,
            threshold_unit: ex.threshold_unit || '',
            enabled: true,
            channel_ids: [],
            re_alert_policy: 'once',
          }),
        });
      } else {
        resp = await fetch('/api/cloud-proxy/api/alerts/' + ruleId, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ enabled: newEnabled }),
        });
      }
      if (resp.status === 402) {
        // Hit the Free-tier cap server-side
        return openPaywall();
      }
      if (!resp.ok) throw new Error('toggle failed: HTTP ' + resp.status);
      // Optimistic update: the cloud cache warms a few seconds behind the
      // write (daemon heartbeat cache_push), so reflect the new state locally
      // and re-render NOW so the switch flips instantly; the delayed reloads
      // then reconcile against the warmed cache.
      if (ex && newEnabled && !alertsState.rules.find(r => r.alert_type === ex.alert_type)) {
        alertsState.rules.push({
          id: 'pending-' + ruleId, alert_type: ex.alert_type, name: ex.name,
          threshold_value: ex.threshold_value, threshold_unit: ex.threshold_unit || '',
          enabled: true, channel_ids: [],
        });
      } else {
        const r = alertsState.rules.find(x => x.id === ruleId);
        if (r) r.enabled = newEnabled;
      }
      renderRules();
      setTimeout(function () { window.loadAlertsPage(); }, 2500);
      setTimeout(function () { window.loadAlertsPage(); }, 6000);
    } catch (e) {
      console.warn(e);
    }
  };

  // ── Paywall modal ─────────────────────────────────────────────────────────

  // Issue #1717: the alerts modal nodes are templated inside #zoom-wrapper,
  // which gets `transform: scale(currentZoom)` applied unconditionally by
  // app.js applyZoom() at boot — even when currentZoom === 1. Any non-`none`
  // transform creates a containing block for descendants with `position:
  // fixed`, so `inset: 0` no longer means viewport — it means the wrapper.
  // Result: the modal renders pinned to the wrapper's top-left (which
  // scrolls with the page) instead of centered in the viewport. Reparent
  // the modal to <body> on first open to escape the transform.
  function detachModalToBody(modalId) {
    const modal = document.getElementById(modalId);
    if (modal && modal.parentNode !== document.body) {
      document.body.appendChild(modal);
    }
    return modal;
  }

  function openPaywall() {
    const modal = detachModalToBody('alerts-paywall-modal');
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
    // See detachModalToBody() above re: #zoom-wrapper transform / issue #1717.
    const modal = detachModalToBody('alerts-editor-modal');
    if (!modal) return; // editor markup only renders for Pro (is_pro)
    modal.style.display = 'flex';
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
      daily_spend:    { unit: 'USD',         placeholder: 50,    label: 'Daily spend exceeds', name: 'Daily spend cap' },
      session_cost:   { unit: 'USD',         placeholder: 5,     label: 'Single session cost exceeds', name: 'Session cost cap' },
      node_offline:   { unit: 'min',         placeholder: 10,    label: 'Agent has been offline for more than', name: 'Agent offline' },
      token_velocity: { unit: 'tokens/min',  placeholder: 10000, label: 'Token velocity exceeds', name: 'Runaway session' },
      cron_failure:   { unit: 'fails',       placeholder: 3,     label: 'Cron has failed in a row at least', name: 'Cron failure streak' },
      error_rate:     { unit: '%',           placeholder: 20,    label: 'Tool failure rate exceeds', name: 'Tool failures' },
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

    // Editing a canned example or saving on a non-Pro tier: fire the paywall
    // here, AFTER the user has configured the rule. They're more invested by
    // this point -- better conversion than gating on first click.
    const editingExample = alertsState.editorRule
      && String(alertsState.editorRule.id || '').startsWith('example_');
    if (editingExample || (alertsState.tier !== 'pro' && alertsState.tier !== 'trial')) {
      window.alertsCloseEditor();
      return openPaywall();
    }

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
