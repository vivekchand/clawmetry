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
    // Eval->monitor loop: fire on production QUALITY, not just cost/errors.
    { id: 'example_quality', alert_type: 'eval_score_below', name: 'Quality score drops below 3',
      threshold_value: 3, threshold_unit: '/ 5',
      _exampleChannels: '✉️ Email · 💬 Slack' },
    { id: 'example_failures', alert_type: 'outcome_failure_rate', name: 'Failure rate exceeds 20%',
      threshold_value: 20, threshold_unit: '%',
      _exampleChannels: '📟 PagerDuty' },
  ];

  // ── Tier resolution ───────────────────────────────────────────────────────

  async function resolveTier() {
    // Self-hosted entitlement FIRST (founder 2026-07-28: alerts must work
    // without a cloud signup). A local Trial/Pro license entitles the tab;
    // rules then live in the LOCAL store and fire via the local evaluator.
    // Only when the local entitlement is free do we consult the cloud
    // account (the original flow).
    try {
      const ent = await fetch('/api/entitlement').then(r => r.json());
      if (ent && ent.is_paid && !ent.expired) {
        alertsState.localMode = true;
        const days = ent.days_until_expiry;
        return { tier: ent.tier === 'trial' ? 'trial' : 'pro',
                 trialDaysLeft: (days === null || days === undefined) ? null : days };
      }
    } catch (e) { /* fall through to the cloud path */ }
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
      const data = await fetch(alertsState.localMode
        ? '/api/alerts/rules' : '/api/cloud-proxy/api/alerts').then(r => r.json());
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
      if (alertsState.localMode) {
        // Local rows speak the local schema (type/threshold/channels);
        // normalise onto the fields the renderer reads.
        serverRules = (serverRules || []).map(function (r) {
          return Object.assign({}, r, {
            alert_type: r.alert_type || r.type,
            name: r.name || r.type,
            threshold_value: (r.threshold_value !== undefined && r.threshold_value !== null)
              ? r.threshold_value : r.threshold,
            channel_ids: r.channel_ids || r.channels || [],
          });
        });
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
      const hist = await fetch(alertsState.localMode
        ? '/api/alerts/history?limit=20'
        : '/api/cloud-proxy/api/alerts/history?limit=20')
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
    renderBuiltinMonitors();

    try {
      const ch = alertsState.localMode
        ? await fetch('/api/alert-channels').then(r => r.json()).then(cfg => ({
            channels: [
              cfg.slack_webhook_url ? { id: 'slack', channel_type: 'slack', name: 'Slack', enabled: true } : null,
              (cfg.telegram_bot_token && cfg.telegram_chat_id) ? { id: 'telegram', channel_type: 'telegram', name: 'Telegram', enabled: true } : null,
              cfg.pagerduty_routing_key ? { id: 'pagerduty', channel_type: 'pagerduty', name: 'PagerDuty', enabled: true } : null,
            ].filter(Boolean),
          }))
        : await fetch('/api/cloud-proxy/api/channels').then(r => r.json());
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
    eval_score_below:     { icon: '⭐', verb: 'Quality score drops below' },
    outcome_failure_rate: { icon: '🚦', verb: 'Failure rate exceeds' },
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
    const activeRt = (typeof _cmRuntimeFilter === 'function') ? _cmRuntimeFilter() : 'all';
    const ruleRt = r => String(r.runtime || 'all').toLowerCase();
    const rtLabel = rt => (typeof _CM_RT_LABEL === 'object' && _CM_RT_LABEL[rt]) || rt;
    wrap.innerHTML = EXAMPLE_RULES.map(ex => {
      // Per-runtime scope: under a runtime filter, that runtime's own rule
      // wins the row; a node-wide rule still shows but is labeled as such.
      const candidates = alertsState.rules.filter(r => r.alert_type === ex.alert_type
        && (activeRt === 'all' || ruleRt(r) === activeRt || ruleRt(r) === 'all'));
      const real = candidates.find(r => activeRt !== 'all' && ruleRt(r) === activeRt)
        || candidates[0];
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
      // Channel pills state what delivery IS, never what it could be.
      // These used to render ex._exampleChannels ("💬 Slack · ✉️ Email") on
      // every OFF row — decorative sample text that looked exactly like
      // configured delivery, so arming a rule appeared to erase it. An OFF
      // row now says nothing about channels; an armed one shows its real
      // channels, or "In-app only", which is what empty channel_ids actually
      // means server-side (routes/alerts.py defaults them to the banner).
      const channelPills = real
        ? ((real.channel_ids || []).map(cid => {
            const ch = alertsState.channels.find(c => c.id === cid);
            return ch ? `<span class="alerts-chan-pill">${chTypeIcon(ch.channel_type)} ${escape(ch.name)}</span>` : '';
          }).join('')
          || '<span class="alerts-chan-pill off" title="Shows in the bell menu and the banner. No external delivery.">In-app only</span>')
        : '';
      const badge = real ? '' : '<span class="alerts-rule-example-badge">example</span>';
      // Evaluator honesty. A rule nothing evaluates must not look identical
      // to one that is armed and simply hasn't tripped — that equivalence is
      // what let two dead rules sit on "never triggered" indefinitely.
      const evaluator = real ? (real.evaluator || '') : '';
      const isDead = evaluator === 'none';
      const deadChip = isDead
        ? '<span class="alerts-chan-pill off" title="'
          + (real && real.needs_recreate
              ? 'Created by an older version that did not record what it should watch. Turn it off and on again to rebuild it.'
              : 'No evaluator runs this type on a self-hosted node yet. It will not fire.')
          + '">not evaluated</span>'
        : '';
      // "never triggered" reads as "armed, all quiet". For a rule nothing
      // evaluates, that is the wrong story — replace it with the real one.
      if (isDead) {
        metaLine = real && real.needs_recreate
          ? 'Turn this off and on again to rebuild it — it can’t fire as saved'
          : 'Nothing on this node evaluates this alert yet';
      }
      const scopeChip = real
        ? (ruleRt(real) === 'all'
            ? '<span class="alerts-chan-pill off" title="Evaluates across all runtimes on this node">node-wide</span>'
            : '<span class="alerts-chan-pill" title="Evaluates only this runtime">' + escape(rtLabel(ruleRt(real))) + '</span>')
        : '';
      return `
        <div class="alerts-rule-row${real ? '' : ' alerts-rule-example'}" data-rule-id="${id}">
          <div class="alerts-rule-dot ${on ? 'on' : 'off'}" title="${on ? 'Enabled' : 'Disabled'}"></div>
          <div class="alerts-rule-main">
            <div class="alerts-rule-title">${meta.icon} ${escape(name)} ${badge} ${scopeChip} ${deadChip}</div>
            <div class="alerts-rule-meta">${metaLine}</div>
          </div>
          <div class="alerts-rule-chan">${channelPills}</div>
          ${toggleSwitch(id, on)}
          <button class="alerts-btn-ghost" onclick="alertsHandleEdit('${id}')">Edit</button>
        </div>
      `;
    }).join('');

    // Orphan rules — saved and often ENABLED, but matching none of the eight
    // canonical rows above, so previously rendered nowhere at all.
    //
    // Found while verifying this fix (2026-08-15): the reporter's own node had
    // two enabled rules that the tab could not display, because matching keys
    // on alert_type and rules written before the alert_type column have none.
    // The tab showed all eight rows as untouched "example" while two live
    // rules sat in the database — invisible, unturn-off-able, and (being
    // "anomaly") unable to fire. Whatever else is true of a rule, if it exists
    // the operator must be able to see it and switch it off.
    const claimed = new Set();
    EXAMPLE_RULES.forEach(ex => {
      const c = alertsState.rules.filter(r => r.alert_type === ex.alert_type);
      const pick = c.find(r => activeRt !== 'all' && ruleRt(r) === activeRt) || c[0];
      if (pick) claimed.add(pick.id);
    });
    const orphans = alertsState.rules.filter(r => !claimed.has(r.id));
    if (orphans.length) {
      wrap.innerHTML += orphans.map(r => {
        const on = !!r.enabled;
        // Never surface the storage vocabulary ("anomaly", "token_spike") as
        // a name — it tells the operator nothing. Note loadAlertsPage's
        // local-schema normaliser fills `name` with the raw `type` when a row
        // has no real name, so an equal-to-type name counts as no name.
        const thr = (r.threshold_value != null ? r.threshold_value : r.threshold);
        const realName = (r.name && r.name !== r.type) ? r.name : '';
        const label = realName || RULE_TYPE_LABELS[r.alert_type]?.verb
          || (thr != null ? `Old rule · threshold ${thr}` : 'Old rule');
        const why = r.needs_recreate
          ? 'Saved by an older version without a record of what it should watch, so nothing can run it.'
          : 'This rule doesn’t match any alert type this version offers.';
        return `
        <div class="alerts-rule-row alerts-rule-orphan" data-rule-id="${escape(r.id)}">
          <div class="alerts-rule-dot ${on ? 'on' : 'off'}" title="${on ? 'Enabled' : 'Disabled'}"></div>
          <div class="alerts-rule-main">
            <div class="alerts-rule-title">🗃️ ${escape(label)}
              <span class="alerts-rule-example-badge">unrecognized</span>
            </div>
            <div class="alerts-rule-meta">${escape(why)} Switch it off to remove it.</div>
          </div>
          <div class="alerts-rule-chan"><span class="alerts-chan-pill off">not evaluated</span></div>
          ${toggleSwitch(r.id, on)}
          <button class="alerts-btn-ghost" onclick="alertsDeleteRule('${escape(r.id)}')">Remove</button>
        </div>`;
      }).join('');
    }
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
          <div class="alerts-rule-chan"><span class="alerts-chan-pill off" title="Delivery to ${escape(ex._exampleChannels.replace(/[^\x20-\x7E ·]/g, '').trim())} comes with Pro">Pro delivery</span></div>
          ${toggleSwitch(ex.id, false)}
          <button class="alerts-btn-ghost" onclick="event.stopPropagation();alertsHandleEdit('${ex.id}')">Edit</button>
        </div>
      `;
    }).join('');
  }

  // #1954: short one-line explanations for each alert type, shown as a hover
  // tooltip on the history row so "what does stuck_session even mean" stops
  // being a user question. Keys match the `type` / `payload.name` strings the
  // evaluator writes.
  const ALERT_TYPE_HINTS = {
    stuck_session:    'A session went silent past the timeout — the agent likely stalled (no new events).',
    token_velocity:   'Runaway-loop guard — tokens/min crossed your threshold (agent burning tokens in a loop).',
    daily_spend:      'Daily spend crossed your budget.',
    session_cost:     'A single session’s cost crossed your threshold.',
    session_duration: 'A session ran longer than your threshold.',
    node_offline:     'An agent node hasn’t pinged in longer than your threshold.',
    cron_failure:     'A cron job failed more times than your threshold.',
    error_rate:       'Tool error rate crossed your threshold.',
    subagent_depth:   'Sub-agent nesting depth crossed your threshold.',
    eval_score_below:     'Average quality score (judged 0-5) of recent sessions dropped below your threshold.',
    outcome_failure_rate: 'Too many recent sessions ended badly (failed or got stuck) as a share of finished sessions.',
  };
  // Hide alerts older than this from the history view. Stops the list from
  // accumulating forever; the user only cares about recent activity.
  const ALERTS_HISTORY_MAX_AGE_MS = 3 * 86400 * 1000;

  function renderHistory() {
    const wrap = document.getElementById('alerts-history-list');
    // #1954: filter ancient entries (>3d) so the list stays useful, then
    // collapse runs of consecutive identical alerts (same type + same message)
    // into a single row with a "× N" counter — kills the "5 identical
    // token_velocity rows" fatigue without losing the signal that it fired.
    const now = Date.now();
    const fresh = (alertsState.history || []).filter(h => {
      const ms = new Date(_alertsTsMs(h.fired_at)).getTime();
      return !isFinite(ms) || (now - ms) <= ALERTS_HISTORY_MAX_AGE_MS;
    });
    if (!fresh.length) {
      return renderHistoryEmpty('No alerts in the last 3 days.');
    }
    const grouped = [];
    for (const h of fresh) {
      const p = h.payload || {};
      const key = (p.name || h.alert_id || '') + '|' + String(p.actual_value ?? '');
      const last = grouped[grouped.length - 1];
      if (last && last._key === key) {
        last._count += 1;
        last._latestFiredAt = h.fired_at;
      } else {
        grouped.push({ ...h, _key: key, _count: 1, _latestFiredAt: h.fired_at });
      }
    }
    wrap.innerHTML = grouped.map(h => {
      const sev = h.resolved_at ? 'sev-green' : 'sev-red';
      const dot = '●';
      const payload = h.payload || {};
      const typeName = payload.name || h.alert_id || '';
      const hint = ALERT_TYPE_HINTS[typeName] || '';
      const countBadge = h._count > 1
        ? ` <span class="alerts-hist-count" title="Fired ${h._count} times in a row">× ${h._count}</span>`
        : '';
      const rowTitle = hint ? ` title="${escape(hint)}"` : '';
      return `
        <div class="alerts-hist-row"${rowTitle}>
          <span class="${sev}">${dot}</span>
          <span class="alerts-hist-time">${formatTimeAgo(h._latestFiredAt)}</span>
          <span class="alerts-hist-text"><b>${escape(typeName)}</b>${countBadge}
            → ${escape(String(payload.actual_value ?? ''))} ${escape(payload.threshold_unit || '')}</span>
        </div>
      `;
    }).join('');
  }

  function renderHistoryEmpty(msg) {
    document.getElementById('alerts-history-list').innerHTML =
      `<div class="alerts-loading">${escape(msg)}</div>`;
  }

  // Always-on monitors — the checks that fire without a rule behind them.
  // Rendered read-only and visibly distinct from the toggleable rules above,
  // so nobody mistakes them for something they forgot to switch off.
  const _BUILTIN_ICONS = {
    heartbeat_silent: '💤', agent_down: '📡', anomaly: '📈',
    token_velocity: '⚡', agent_error_rate: '🛠', error_spike: '🔥',
    security_threat: '🛡', numbat_finding: '🛡', security: '🔐',
    threshold: '💰',
  };

  async function renderBuiltinMonitors() {
    const wrap = document.getElementById('alerts-builtins-list');
    if (!wrap) return;
    let monitors = [];
    try {
      const d = await fetch('/api/alerts/builtins').then(r => r.json());
      monitors = (d && d.monitors) || [];
    } catch {
      wrap.innerHTML = '<div class="alerts-loading">Couldn’t load the always-on monitors.</div>';
      return;
    }
    if (!monitors.length) {
      wrap.innerHTML = '<div class="alerts-loading">No always-on monitors on this build.</div>';
      return;
    }
    wrap.innerHTML = monitors.map(m => `
      <div class="alerts-rule-row alerts-builtin-row">
        <div class="alerts-rule-dot on" title="Always on"></div>
        <div class="alerts-rule-main">
          <div class="alerts-rule-title">${_BUILTIN_ICONS[m.alert_type] || '🔔'} ${escape(m.label)}</div>
          <div class="alerts-rule-meta">${escape(m.watches)}</div>
        </div>
        <div class="alerts-rule-chan">${(m.channels || []).map(c =>
          `<span class="alerts-chan-pill">${escape(c === 'banner' ? 'In-app' : c)}</span>`).join('')}</div>
        <span class="alerts-builtin-tag" title="Built in — fires with no rule of yours behind it">built in</span>
      </div>
    `).join('');
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
      // Pro/trial: full cloud channel management (PagerDuty, email, on-call)
      window.open('https://app.clawmetry.com/cloud#channels', '_blank');
    } else {
      // OSS/free (#1885, closes #590): open the Budget & Alerts modal on the
      // "Alert Rules" tab where Slack/Discord direct-webhook config lives.
      // Cloud-routed channels (PagerDuty, email, on-call) remain Pro-only.
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
      // Ask where it should go BEFORE arming it. Turning an alert on with
      // nowhere to send it is a decision the operator should make knowingly,
      // not discover afterwards from a grey "no channels" pill.
      if (isExample && newEnabled && !alertsState.channels.length
          && !_deliveryChoiceMade) {
        return openDeliveryPrompt(ruleId);
      }
      // With channels configured, "notify me" means the channels the operator
      // already set up — send to all of them rather than silently to none.
      const chosenChannels = alertsState.channels.map(c => c.id);
      let resp;
      if (isExample && newEnabled) {
        resp = await fetch(alertsState.localMode
          ? '/api/alerts/rules' : '/api/cloud-proxy/api/alerts', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            alert_type: ex.alert_type,
            name: ex.name,
            threshold_value: ex.threshold_value,
            threshold_unit: ex.threshold_unit || '',
            enabled: true,
            channel_ids: chosenChannels,
            re_alert_policy: 'once',
          }),
        });
      } else {
        resp = await fetch((alertsState.localMode
          ? '/api/alerts/rules/' : '/api/cloud-proxy/api/alerts/') + ruleId, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ enabled: newEnabled }),
        });
      }
      if (resp.status === 402) {
        // Hit the Free-tier cap server-side
        return openPaywall();
      }
      // 422 = the server has no evaluator for this type on a self-hosted
      // node. Say so instead of leaving a toggle that flips back with no
      // explanation (or worse, one that stays on and never fires).
      if (resp.status === 422) {
        let detail = {};
        try { detail = await resp.json(); } catch {}
        showRuleNotice(ruleId, detail.error
          || 'This alert type has no evaluator on a self-hosted node yet.');
        return;
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
          enabled: true, channel_ids: chosenChannels,
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

  // Delete a rule outright. Only reachable from an orphan row, where toggling
  // off would leave an unusable rule sitting in the database forever.
  window.alertsDeleteRule = async function (ruleId) {
    try {
      const resp = await fetch((alertsState.localMode
        ? '/api/alerts/rules/' : '/api/cloud-proxy/api/alerts/') + ruleId,
        { method: 'DELETE' });
      if (!resp.ok) throw new Error('delete failed: HTTP ' + resp.status);
      alertsState.rules = alertsState.rules.filter(r => r.id !== ruleId);
      renderRules();
      setTimeout(function () { window.loadAlertsPage(); }, 2000);
    } catch (e) {
      console.warn(e);
    }
  };

  // ── Delivery prompt ───────────────────────────────────────────────────────
  //
  // Asked once per visit, before the first alert is armed with nowhere to
  // send it. "Show it in the app" is a real answer, not a dismissal — it sets
  // _deliveryChoiceMade so we don't re-ask on every subsequent toggle.

  let _deliveryChoiceMade = false;
  let _deliveryPendingRuleId = null;

  function openDeliveryPrompt(ruleId) {
    _deliveryPendingRuleId = ruleId;
    const modal = detachModalToBody('alerts-delivery-modal');
    const body = document.getElementById('alerts-delivery-body');
    const ex = EXAMPLE_RULES.find(r => r.id === ruleId);
    if (body && ex) {
      body.textContent = 'You haven’t set up anywhere to send alerts yet. '
        + 'ClawMetry can show “' + ex.name + '” in the app, or deliver '
        + 'it to Slack, Telegram, or PagerDuty.';
    }
    modal.style.display = 'flex';
  }

  window.alertsCloseDelivery = function (e) {
    // Backdrop click / Escape = cancel. The rule stays OFF, which is the
    // truthful outcome: nothing was armed and nothing was configured.
    if (e && e.target && e.target.id !== 'alerts-delivery-modal') return;
    const el = document.getElementById('alerts-delivery-modal');
    if (el) el.style.display = 'none';
    _deliveryPendingRuleId = null;
    renderRules();
  };

  window.alertsDeliverySetUp = function () {
    const el = document.getElementById('alerts-delivery-modal');
    if (el) el.style.display = 'none';
    _deliveryPendingRuleId = null;
    // Straight to Notifications, per the founder's ask: configure first, then
    // come back and arm it. The rule is deliberately NOT created here — an
    // alert that exists but was never confirmed is the ambiguity we're fixing.
    if (typeof switchTab === 'function') switchTab('notifications');
  };

  window.alertsDeliveryInAppOnly = function () {
    const el = document.getElementById('alerts-delivery-modal');
    if (el) el.style.display = 'none';
    _deliveryChoiceMade = true;
    const ruleId = _deliveryPendingRuleId;
    _deliveryPendingRuleId = null;
    if (ruleId) window.alertsToggleRule(ruleId, true);
  };

  // Inline, per-row explanation. Used when the server refuses a rule type
  // (422) — a toggle that springs back with no reason is its own small bug.
  function showRuleNotice(ruleId, message) {
    // Re-render first so the toggle returns to its true (off) position, then
    // attach the reason to that row.
    renderRules();
    const row = document.querySelector('[data-rule-id="' + ruleId + '"]');
    const main = row && row.querySelector('.alerts-rule-main');
    if (!main) return;
    const note = document.createElement('div');
    note.className = 'alerts-rule-notice';
    note.textContent = message;
    main.appendChild(note);
  }

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
      eval_score_below:     { unit: '/ 5',  placeholder: 3,  label: 'Average quality score drops below', name: 'Quality drop' },
      outcome_failure_rate: { unit: '%',    placeholder: 20, label: 'Session failure rate exceeds', name: 'Failure rate' },
    };
    const p = presets[t] || { unit: '', placeholder: 0, label: 'Threshold', name: 'Custom alert' };
    const val = r.threshold_value ?? p.placeholder;
    // Scope: runtime-scoped by default (founder 2026-08-03) — a new rule
    // inherits the active runtime filter; node-wide is the explicit opt-in.
    const activeRt = (typeof _cmRuntimeFilter === 'function') ? _cmRuntimeFilter() : 'all';
    const curScope = String(r.runtime || (activeRt !== 'all' ? activeRt : 'all')).toLowerCase();
    const rtLabel = rt => (typeof _CM_RT_LABEL === 'object' && _CM_RT_LABEL[rt]) || rt;
    const known = (typeof _CM_RT_LABEL === 'object') ? Object.keys(_CM_RT_LABEL) : [];
    const scopeOpts = ['all'].concat(known).map(rt => {
      const label = rt === 'all' ? 'All runtimes (node-wide)' : rtLabel(rt);
      return `<option value="${rt}" ${rt === curScope ? 'selected' : ''}>${escape(label)}</option>`;
    }).join('');
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
      <div class="alerts-form-row">
        <label>Applies to</label>
        <select id="alerts-rule-scope">${scopeOpts}</select>
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

    const scopeSel = document.getElementById('alerts-rule-scope');
    const runtime = scopeSel ? (scopeSel.value || 'all')
      : ((typeof _cmRuntimeFilter === 'function' && _cmRuntimeFilter() !== 'all')
          ? _cmRuntimeFilter() : 'all');
    const body = {
      alert_type: alertsState.editorType,
      name,
      threshold_value: threshold,
      enabled: true,
      channel_ids: channelIds,
      re_alert_policy: policy,
      runtime,
    };

    const isEdit = !!alertsState.editorRule;
    const url = alertsState.localMode
      ? (isEdit ? '/api/alerts/rules/' + alertsState.editorRule.id : '/api/alerts/rules')
      : (isEdit ? '/api/cloud-proxy/api/alerts/' + alertsState.editorRule.id
                : '/api/cloud-proxy/api/alerts');
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
  // #1954: `fired_at` from /api/alerts/history is epoch SECONDS (REAL column
  // written by time.time()), but JS Date() treats a bare number as ms. Without
  // this normalization every row rendered as "20576d ago" (epoch zero → now).
  // Treat numbers below ~year 33658 as seconds and scale to ms. ISO strings
  // and ms-scale numbers pass through unchanged.
  function _alertsTsMs(v) {
    if (typeof v === 'number') return v < 1e12 ? v * 1000 : v;
    if (typeof v === 'string' && /^-?\d+(\.\d+)?$/.test(v)) {
      const n = Number(v);
      return n < 1e12 ? n * 1000 : n;
    }
    return v;
  }
  function formatTimeAgo(iso) {
    if (!iso) return '';
    try {
      const ms = new Date(_alertsTsMs(iso)).getTime();
      if (!isFinite(ms)) return '';
      const sec = Math.floor((Date.now() - ms) / 1000);
      if (sec < 60) return 'just now';
      if (sec < 3600) return Math.floor(sec / 60) + 'm ago';
      if (sec < 86400) return Math.floor(sec / 3600) + 'h ago';
      return Math.floor(sec / 86400) + 'd ago';
    } catch {
      return '';
    }
  }
})();
