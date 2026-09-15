/* Price book: the settings screen and the Cost tab's contract-rate card.
 *
 * REQ-OBS-CEA-024 (Software Factory), issue #5936, AC .12 to .16.
 *
 * Screen (tab "price-book"): GET /api/pricing/book shows the validated book,
 * each rejected entry with its reasons as sentences, the deployment aliases
 * and every version with the time it came into effect. An entry is added or
 * edited in a form that is checked on the server (POST /api/pricing/entries,
 * dry_run) with each problem shown beside its field. Saving is a separate,
 * explicit step, and it is refused when the book changed after it was loaded.
 *
 * Card (Cost tab): renders /api/usage's priceBook block. The contract figure
 * carries its financial basis badge (static/js/provenance.js); ambiguous or
 * unpriceable usage is counted as unknown with its reason; restating history
 * is a button, and its result is shown beside the original, never in place
 * of it.
 *
 * Requests: the screen fetches only when opened; the card adds a request
 * only when the user asks for a restatement.
 */
(function () {
  'use strict';

  var state = { book: null, editingId: null, confirming: false, restated: null };

  function esc(s) {
    return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
    });
  }
  function money(v) {
    if (v == null || !isFinite(Number(v))) return 'not available';
    var n = Number(v);
    if (Math.abs(n) >= 0.01) return (n < 0 ? '-$' : '$') + Math.abs(n).toFixed(2);
    return n > 0 ? '<$0.01' : (n < 0 ? '>-$0.01' : '$0.00');
  }
  function calls(n) {
    n = Number(n) || 0;
    return n + (n === 1 ? ' model call' : ' model calls');
  }
  function when(iso) {
    if (!iso) return '';
    var d = new Date(iso);
    return isNaN(d.getTime()) ? String(iso) : d.toLocaleString();
  }
  function dateOnly(iso) {
    if (!iso) return '';
    return /T00:00:00(\.0+)?Z$/.test(iso) ? iso.slice(0, 10) : when(iso);
  }
  function rateText(e) {
    if (e.discount_pct != null) return e.discount_pct + '% off the published rate';
    var r = e.rates || {};
    var parts = ['in ' + r.input_per_1m, 'out ' + r.output_per_1m];
    if (r.cache_read_per_1m != null) parts.push('cache read ' + r.cache_read_per_1m);
    if (r.cache_write_per_1m != null) parts.push('cache write ' + r.cache_write_per_1m);
    return parts.join(' · ') + ' ' + esc(e.currency || 'USD') + ' per 1M tokens';
  }
  function matchText(e) {
    if (e.model != null) return esc(e.model);
    if (e.model_prefix != null) return esc(e.model_prefix) + '<span class="pb-muted"> (prefix)</span>';
    return esc(e.model_regex) + '<span class="pb-muted"> (pattern)</span>';
  }

  // ── Screen ────────────────────────────────────────────────────────────────

  async function loadPriceBookTab() {
    var root = document.getElementById('pb-root');
    if (!root) return;
    var back = document.getElementById('pb-back');
    if (back && !back._pbWired) {
      back._pbWired = true;
      back.addEventListener('click', function () { switchTab('usage'); });
    }
    root.innerHTML = '<div class="card" style="color:var(--text-muted);">Loading...</div>';
    var resp, body = {};
    try {
      resp = await fetch('/api/pricing/book', { cache: 'no-store' });
      body = await resp.json().catch(function () { return {}; });
    } catch (e) {
      root.innerHTML = '<div class="card"><div class="pb-note pb-note-bad">The price book could not be loaded, because this dashboard did not answer. Try Refresh.</div></div>';
      return;
    }
    if (resp.status === 410) {
      root.innerHTML = '<div class="card"><div class="pb-note pb-note-warn">The price book is managed on the computer your agents run on, because negotiated rates stay on that machine. Open ClawMetry there to view or edit it.</div></div>';
      return;
    }
    if (resp.status === 402) {
      root.innerHTML = '<div class="card"><div class="pb-note pb-note-warn">The price book is part of the Pro plan on this install. '
        + '<a href="https://app.clawmetry.com/upgrade?source=price_book" target="_blank" rel="noopener">See plans</a>.</div></div>';
      return;
    }
    if (!resp.ok) {
      root.innerHTML = '<div class="card"><div class="pb-note pb-note-bad">The price book could not be loaded. ' + esc(body.message || '') + '</div></div>';
      return;
    }
    state.book = body;
    state.confirming = false;
    renderBook();
  }

  function renderBook() {
    var b = state.book || {};
    var root = document.getElementById('pb-root');
    var html = '';

    // Status
    html += '<div class="card">';
    if (!b.present) {
      html += '<p style="margin:0 0 6px;font-weight:600;">No price book yet.</p>'
        + '<p class="pb-lede">Every cost on the Cost tab is at published rates until you add an entry.</p>';
    } else if (b.errors && b.errors.length) {
      html += '<div class="pb-note pb-note-bad"><strong>This price book file cannot be used as it is.</strong> '
        + esc(b.errors.join('; ')) + '. No figure uses it until the file is fixed.</div>';
    } else {
      html += '<p style="margin:0;">Current version <span class="pb-code">' + esc(b.version) + '</span></p>';
    }
    html += '<p class="pb-muted" style="margin:8px 0 0;">File: <span class="pb-code">' + esc(b.path || '') + '</span></p>';
    if (!b.engine_available) {
      html += '<div class="pb-note pb-note-warn">Contract amounts need the valuation engine, which this build does not include. '
        + 'You can still keep the book here: the Cost tab shows how much usage it covers.</div>';
    }
    html += '<div class="pb-actions">'
      + (b.errors && b.errors.length ? '' : '<button type="button" class="pb-btn pb-btn-primary" data-pb-act="add">Add an entry</button>')
      + '</div></div>';

    html += '<div id="pb-form-host"></div>';

    // Entries
    var entries = b.entries || [];
    html += '<div class="section-title">Entries <span class="pb-muted" style="font-weight:400;margin-left:6px;">' + entries.length + ' in use</span></div>';
    html += '<div class="card pb-scroll">';
    if (!entries.length) {
      html += '<p class="pb-muted" style="margin:0;">No entries are in use.</p>';
    } else {
      html += '<table class="pb-table"><thead><tr><th>Entry</th><th>Model</th><th>Applies to</th><th>Price</th><th>From</th><th>Until</th><th></th></tr></thead><tbody>';
      entries.forEach(function (e) {
        var scope = [e.channel, e.region, e.provider].filter(Boolean).map(esc).join(' · ') || '<span class="pb-muted">any channel</span>';
        html += '<tr><td class="pb-code">' + esc(e.id) + '</td><td>' + matchText(e) + '</td><td>' + scope + '</td><td>'
          + rateText(e) + '</td><td>' + esc(dateOnly(e.effective_from)) + '</td><td>'
          + (e.effective_to ? esc(dateOnly(e.effective_to)) : '<span class="pb-muted">open</span>') + '</td>'
          + '<td><button type="button" class="pb-btn" data-pb-act="edit" data-pb-id="' + esc(e.id) + '">Edit</button></td></tr>';
      });
      html += '</tbody></table>';
    }
    html += '</div>';

    // Rejected
    var rejected = b.rejected || [];
    html += '<div class="section-title">Rejected entries <span class="pb-muted" style="font-weight:400;margin-left:6px;">' + rejected.length + '</span></div>';
    html += '<div class="card">';
    if (!rejected.length) {
      html += '<p class="pb-muted" style="margin:0;">Nothing in the file was rejected.</p>';
    } else {
      html += '<p class="pb-lede">These are in the file but not used, so no figure is priced from them.</p>';
      rejected.forEach(function (r) {
        var name = r.id ? '<span class="pb-code">' + esc(r.id) + '</span>' : (r.kind === 'alias' ? 'Alias' : 'Entry') + ' number ' + (Number(r.index) + 1);
        var msgs = (r.messages && r.messages.length) ? r.messages.map(function (m) { return m.message; }) : (r.problems || []);
        html += '<div class="pb-note pb-note-bad" style="margin-top:8px;"><strong>' + name + '</strong> (' + esc(r.kind) + ')<ul style="margin:6px 0 0 18px;padding:0;">'
          + msgs.map(function (m) { return '<li>' + esc(m) + '</li>'; }).join('') + '</ul></div>';
      });
    }
    html += '</div>';

    // Aliases
    var aliases = b.aliases || [];
    html += '<div class="section-title">Deployment aliases <span class="pb-muted" style="font-weight:400;margin-left:6px;">Azure OpenAI deployment names and the model behind each</span></div>';
    html += '<div class="card pb-scroll">';
    if (!aliases.length) {
      html += '<p class="pb-muted" style="margin:0;">No aliases. Add them to the file under "aliases" when a deployment name does not say which model it runs.</p>';
    } else {
      html += '<table class="pb-table"><thead><tr><th>Deployment</th><th>Model</th><th>Resource</th><th>From</th><th>Until</th></tr></thead><tbody>';
      aliases.forEach(function (a) {
        html += '<tr><td class="pb-code">' + esc(a.deployment) + '</td><td>' + esc(a.model) + '</td><td>' + (a.resource ? esc(a.resource) : '<span class="pb-muted">any</span>')
          + '</td><td>' + esc(dateOnly(a.effective_from) || 'always') + '</td><td>' + (a.effective_to ? esc(dateOnly(a.effective_to)) : '<span class="pb-muted">open</span>') + '</td></tr>';
      });
      html += '</tbody></table>';
    }
    html += '</div>';

    // Versions
    var tl = (b.timeline || []).slice().reverse();
    html += '<div class="section-title">Versions <span class="pb-muted" style="font-weight:400;margin-left:6px;">each edit is kept, so a figure can always be reproduced</span></div>';
    html += '<div class="card pb-scroll">';
    if (!tl.length) {
      html += '<p class="pb-muted" style="margin:0;">No version has come into effect yet.</p>';
    } else {
      html += '<table class="pb-table"><thead><tr><th>Version</th><th>Applies to usage from</th><th>How</th><th></th></tr></thead><tbody>';
      tl.forEach(function (v, i) {
        html += '<tr><td class="pb-code">' + esc(v.version) + '</td><td>' + esc(when(v.activated_at)) + '</td><td>'
          + (v.source === 'screen' ? 'saved on this screen' : 'file edit, from when the file changed') + '</td><td>'
          + (i === 0 && v.version === b.version ? '<span class="pb-pill">current</span>' : '') + '</td></tr>';
      });
      html += '</tbody></table>';
    }
    html += '</div>';

    root.innerHTML = html;
    root.onclick = function (ev) {
      var btn = ev.target.closest('[data-pb-act]');
      if (!btn) return;
      var act = btn.getAttribute('data-pb-act');
      if (act === 'add') openForm(null);
      if (act === 'edit') openForm(btn.getAttribute('data-pb-id'));
    };
  }

  // ── Form ──────────────────────────────────────────────────────────────────

  var FIELDS = [
    ['id', 'Entry id', 'text', 'for example bedrock-sonnet-2026'],
    ['match_value', 'Model', 'text', 'for example claude-sonnet-4-5'],
    ['channel', 'Channel (optional)', 'text', 'aws-bedrock or azure-openai'],
    ['region', 'Region (optional)', 'text', 'for example us'],
    ['provider', 'Provider (optional)', 'text', 'for example anthropic'],
    ['effective_from', 'Applies from', 'text', 'YYYY-MM-DD'],
    ['effective_to', 'Applies until (optional)', 'text', 'YYYY-MM-DD, the day it stops'],
    ['currency', 'Currency', 'text', 'USD'],
    ['input_per_1m', 'Input rate per 1M tokens', 'text', ''],
    ['output_per_1m', 'Output rate per 1M tokens', 'text', ''],
    ['cache_read_per_1m', 'Cache read rate per 1M (optional)', 'text', ''],
    ['cache_write_per_1m', 'Cache write rate per 1M (optional)', 'text', ''],
    ['discount_pct', 'Discount off the published rate, %', 'text', 'for example 18']
  ];
  // Which form field a server problem belongs next to.
  var ERR_FOR = {
    id: 'id', match: 'match_value', provider: 'provider', channel: 'channel', region: 'region',
    effective_from: 'effective_from', effective_to: 'effective_to', currency: 'currency',
    'rates.input_per_1m': 'input_per_1m', 'rates.output_per_1m': 'output_per_1m',
    'rates.cache_read_per_1m': 'cache_read_per_1m', 'rates.cache_write_per_1m': 'cache_write_per_1m',
    rates: 'input_per_1m', discount_pct: 'discount_pct', pricing: 'pricing_kind'
  };

  function openForm(id) {
    var host = document.getElementById('pb-form-host');
    if (!host) return;
    state.editingId = id;
    state.confirming = false;
    var e = null;
    (state.book.entries || []).forEach(function (x) { if (x.id === id) e = x; });
    var kind = e ? (e.model != null ? 'model' : (e.model_prefix != null ? 'model_prefix' : 'model_regex')) : 'model';
    var vals = e ? {
      id: e.id, match_value: e[kind], channel: e.channel, region: e.region, provider: e.provider,
      effective_from: dateOnly(e.effective_from), effective_to: e.effective_to ? dateOnly(e.effective_to) : '',
      currency: e.currency, discount_pct: e.discount_pct,
      input_per_1m: e.rates ? e.rates.input_per_1m : '', output_per_1m: e.rates ? e.rates.output_per_1m : '',
      cache_read_per_1m: e.rates ? e.rates.cache_read_per_1m : '', cache_write_per_1m: e.rates ? e.rates.cache_write_per_1m : ''
    } : { currency: 'USD' };
    var pricing = e && e.discount_pct != null ? 'discount' : 'rates';
    var html = '<div class="card" id="pb-form-card"><div style="font-weight:600;margin-bottom:10px;">'
      + (id ? 'Edit entry <span class="pb-code">' + esc(id) + '</span>' : 'Add an entry') + '</div>'
      + '<div class="pb-err" id="pb-err-entry" role="alert"></div>'
      + '<div class="pb-form">'
      + '<div class="pb-field"><label for="pb-f-match_kind">The entry names its model</label><select id="pb-f-match_kind">'
      + ['model', 'model_prefix', 'model_regex'].map(function (k) {
          var label = { model: 'exactly (also covers dated snapshots)', model_prefix: 'by prefix', model_regex: 'by pattern' }[k];
          return '<option value="' + k + '"' + (k === kind ? ' selected' : '') + '>' + label + '</option>';
        }).join('') + '</select></div>'
      + '<div class="pb-field"><label for="pb-f-pricing_kind">Price given as</label><select id="pb-f-pricing_kind">'
      + '<option value="rates"' + (pricing === 'rates' ? ' selected' : '') + '>rates per 1M tokens</option>'
      + '<option value="discount"' + (pricing === 'discount' ? ' selected' : '') + '>a discount off the published rate</option>'
      + '</select><div class="pb-err" id="pb-err-pricing_kind"></div></div>';
    FIELDS.forEach(function (f) {
      var v = vals[f[0]];
      html += '<div class="pb-field" data-pb-field="' + f[0] + '"><label for="pb-f-' + f[0] + '">' + esc(f[1]) + '</label>'
        + '<input id="pb-f-' + f[0] + '" type="' + f[2] + '" autocomplete="off" placeholder="' + esc(f[3]) + '" value="' + esc(v == null ? '' : v) + '"'
        + (f[0] === 'id' && id ? ' readonly' : '') + ' aria-describedby="pb-err-' + f[0] + '">'
        + '<div class="pb-err" id="pb-err-' + f[0] + '"></div></div>';
    });
    html += '</div><div class="pb-actions">'
      + '<button type="button" class="pb-btn" id="pb-check">Check</button>'
      + '<button type="button" class="pb-btn pb-btn-primary" id="pb-save">Save…</button>'
      + '<button type="button" class="pb-btn" id="pb-cancel">Cancel</button>'
      + '<span class="pb-muted" id="pb-form-status"></span></div>'
      + '<div id="pb-confirm"></div></div>';
    host.innerHTML = html;
    syncPricingKind();
    document.getElementById('pb-f-pricing_kind').addEventListener('change', syncPricingKind);
    document.getElementById('pb-check').addEventListener('click', function () { check(false); });
    document.getElementById('pb-save').addEventListener('click', function () { check(true); });
    document.getElementById('pb-cancel').addEventListener('click', function () { host.innerHTML = ''; state.editingId = null; });
    host.querySelectorAll('input,select').forEach(function (el) {
      el.addEventListener('input', function () { hideConfirm(); });
    });
    host.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }

  function syncPricingKind() {
    var kind = (document.getElementById('pb-f-pricing_kind') || {}).value;
    ['input_per_1m', 'output_per_1m', 'cache_read_per_1m', 'cache_write_per_1m'].forEach(function (k) {
      var el = document.querySelector('[data-pb-field="' + k + '"]');
      if (el) el.hidden = kind === 'discount';
    });
    var d = document.querySelector('[data-pb-field="discount_pct"]');
    if (d) d.hidden = kind !== 'discount';
    hideConfirm();
  }

  function val(k) {
    var el = document.getElementById('pb-f-' + k);
    return el ? String(el.value || '').trim() : '';
  }
  // A number when it reads as one; otherwise the text as typed, so the server
  // can say what is wrong with it instead of the form silently dropping it.
  function num(k) {
    var v = val(k);
    if (v === '') return undefined;
    var n = Number(v);
    return isFinite(n) ? n : v;
  }

  function buildEntry() {
    var e = { id: val('id') };
    e[val('match_kind') || 'model'] = val('match_value');
    ['channel', 'region', 'provider', 'effective_to'].forEach(function (k) { if (val(k)) e[k] = val(k); });
    e.effective_from = val('effective_from');
    if (val('currency')) e.currency = val('currency');
    if (val('pricing_kind') === 'discount') {
      e.discount_pct = num('discount_pct');
    } else {
      var r = {};
      ['input_per_1m', 'output_per_1m', 'cache_read_per_1m', 'cache_write_per_1m'].forEach(function (k) {
        var n = num(k);
        if (n !== undefined) r[k] = n;
      });
      e.rates = r;
    }
    return e;
  }

  function clearErrors() {
    document.querySelectorAll('#pb-form-card .pb-err').forEach(function (el) { el.textContent = ''; });
    document.querySelectorAll('#pb-form-card input').forEach(function (el) { el.removeAttribute('aria-invalid'); });
  }

  function showProblems(problems) {
    clearErrors();
    (problems || []).forEach(function (p) {
      var target = ERR_FOR[p.field] || 'entry';
      var el = document.getElementById('pb-err-' + target) || document.getElementById('pb-err-entry');
      el.textContent = (el.textContent ? el.textContent + ' ' : '') + p.message;
      var input = document.getElementById('pb-f-' + target);
      if (input) input.setAttribute('aria-invalid', 'true');
    });
  }

  function hideConfirm() {
    state.confirming = false;
    var c = document.getElementById('pb-confirm');
    if (c) c.innerHTML = '';
  }

  function status(text) {
    var s = document.getElementById('pb-form-status');
    if (s) s.textContent = text || '';
  }

  async function post(body) {
    var resp = await fetch('/api/pricing/entries', {
      method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body), cache: 'no-store'
    });
    var out = await resp.json().catch(function () { return {}; });
    return { status: resp.status, body: out };
  }

  async function check(thenConfirm) {
    status('Checking…');
    var r;
    try {
      r = await post({ entry: buildEntry(), replace_id: state.editingId, dry_run: true });
    } catch (e) {
      status('');
      showProblems([{ field: 'entry', message: 'The check did not reach this dashboard, so nothing was saved. Try again.' }]);
      return;
    }
    status('');
    if (r.status !== 200) {
      showProblems([{ field: 'entry', message: r.body.message || 'The entry could not be checked.' }]);
      return;
    }
    showProblems(r.body.problems);
    if (!r.body.ok) { hideConfirm(); return; }
    if (!thenConfirm) { status('No problems found. Nothing is saved until you choose Save.'); return; }
    state.confirming = true;
    document.getElementById('pb-confirm').innerHTML = '<div class="pb-note pb-note-warn">'
      + '<strong>Save this as a new price book version?</strong> It applies to usage from the moment you save. '
      + 'Usage before then keeps the value it has; you can restate it from the Cost tab.'
      + '<div class="pb-actions"><button type="button" class="pb-btn pb-btn-primary" id="pb-confirm-save">Save version</button>'
      + '<button type="button" class="pb-btn" id="pb-confirm-cancel">Not yet</button></div></div>';
    document.getElementById('pb-confirm-cancel').addEventListener('click', hideConfirm);
    document.getElementById('pb-confirm-save').addEventListener('click', save);
  }

  async function save() {
    if (!state.confirming) return;
    var btn = document.getElementById('pb-confirm-save');
    if (btn) btn.disabled = true;
    var r;
    try {
      r = await post({ entry: buildEntry(), replace_id: state.editingId, base_version: state.book.present ? state.book.version : null, confirm: true });
    } catch (e) {
      if (btn) btn.disabled = false;
      document.getElementById('pb-confirm').innerHTML = '<div class="pb-note pb-note-bad">The save did not reach this dashboard, so nothing was saved. Try again.</div>';
      return;
    }
    if (r.status === 200) {
      var msg = r.body.message || 'Saved.';
      await loadPriceBookTab();
      var root = document.getElementById('pb-form-host');
      if (root) root.innerHTML = '<div class="card"><div class="pb-note pb-note-ok">' + esc(msg) + '</div></div>';
      return;
    }
    if (r.status === 422) { showProblems(r.body.problems); hideConfirm(); return; }
    document.getElementById('pb-confirm').innerHTML = '<div class="pb-note pb-note-bad">' + esc(r.body.message || 'Nothing was saved.')
      + (r.status === 409 ? ' <button type="button" class="pb-btn" id="pb-reload">Reload the price book</button>' : '') + '</div>';
    var reload = document.getElementById('pb-reload');
    if (reload) reload.addEventListener('click', loadPriceBookTab);
  }

  // ── Cost tab card ─────────────────────────────────────────────────────────

  function figure(block, key, value, label) {
    if (window.cmProv) return window.cmProv.figure(value, window.cmProv.of(block, key), { label: label });
    return esc(money(value));
  }

  function renderUsagePriceBook(data) {
    var host = document.getElementById('usage-price-book-card');
    var title = document.getElementById('usage-price-book-title');
    if (!host) return;
    var pbk = data && data.priceBook;
    var show = function (on) { host.style.display = on ? '' : 'none'; if (title) title.style.display = on ? '' : 'none'; };
    if (!pbk) { show(false); return; }
    var open = '<button type="button" class="refresh-btn" onclick="openPriceBook()">📒 Price book</button>';
    if (!pbk.present) {
      show(true);
      host.innerHTML = '<div style="display:flex;flex-wrap:wrap;gap:10px;align-items:center;justify-content:space-between;font-size:13px;color:var(--text-secondary);">'
        + '<span>Paying negotiated rates? Record them in the price book, and the usage they cover is also shown at your contract rate.</span>' + open + '</div>';
      return;
    }
    show(true);
    if (!pbk.usable) {
      host.innerHTML = '<div style="font-size:13px;">Your price book file cannot be used as it is: ' + esc((pbk.errors || []).join('; '))
        + '. Costs stay at published rates until it is fixed.</div><div style="margin-top:10px;">' + open + '</div>';
      return;
    }
    var w = pbk.windows || {};
    var rows = [['today', 'Today'], ['week', 'This week'], ['month', 'This month']];
    var html = '<p style="margin:0 0 8px;font-size:13px;color:var(--text-secondary);line-height:1.5;">' + esc(pbk.rule || '') + '</p>';
    if (pbk.message) html += '<div style="margin:0 0 10px;padding:8px 12px;border-radius:8px;background:rgba(245,158,11,0.08);border:1px solid rgba(245,158,11,0.4);font-size:13px;">' + esc(pbk.message) + '</div>';
    html += '<div style="overflow-x:auto;"><table class="usage-table"><thead><tr><th></th><th>At your contract rate</th><th>Same usage at published rates</th><th>Not covered by the book</th><th>Could not be priced</th></tr></thead><tbody>';
    rows.forEach(function (r) {
      var t = w[r[0]] || {};
      if (t.withheld) {
        html += '<tr><td>' + r[1] + '</td><td colspan="4" style="color:var(--text-muted);">Held back on this plan: usage older than 24 hours is not shown here.</td></tr>';
        return;
      }
      html += '<tr><td>' + r[1] + '</td><td>' + figure(pbk, 'windows.' + r[0] + '.contract_usd', t.contract_usd, r[1] + ' at your contract rate')
        + '<div style="font-size:11px;color:var(--text-muted);">' + (t.covered_events || 0) + ' of ' + calls(t.events) + ' covered</div></td>'
        + '<td>' + figure(pbk, 'windows.' + r[0] + '.covered_published_usd', t.covered_published_usd, r[1] + ', covered usage at published rates') + '</td>'
        + '<td>' + figure(pbk, 'windows.' + r[0] + '.published_usd', t.published_usd, r[1] + ', uncovered usage at published rates') + '</td>'
        + '<td>' + (t.unknown_events ? '<strong>' + calls(t.unknown_events) + '</strong>' : '<span style="color:var(--text-muted);">none</span>') + '</td></tr>';
    });
    html += '</tbody></table></div>';
    if (pbk.unknown && pbk.unknown.length) {
      html += '<div style="margin-top:10px;font-size:12px;color:var(--text-secondary);"><strong>Why some usage '
        + (data.capped_at_24h ? 'today' : 'this month') + ' could not be priced:</strong><ul style="margin:4px 0 0 18px;padding:0;">'
        + pbk.unknown.map(function (u) { return '<li>' + esc(u.reason) + ' (' + calls(u.events) + ')</li>'; }).join('') + '</ul></div>';
    }
    if (pbk.truncated) {
      html += '<div style="margin-top:8px;font-size:12px;color:var(--text-muted);">Only the most recent model calls were read, so these figures may be incomplete.</div>';
    }
    html += '<div id="usage-price-book-restatement"></div>';
    html += '<div style="display:flex;flex-wrap:wrap;gap:8px;margin-top:12px;">' + open
      + (pbk.engine ? '<button type="button" class="refresh-btn" id="usage-price-book-restate">Restate history with the current book</button>' : '') + '</div>';
    host.innerHTML = html;
    var btn = document.getElementById('usage-price-book-restate');
    if (btn) btn.addEventListener('click', function () { loadRestatement(btn); });
    if (state.restated && state.restated.book_version === pbk.book_version) renderRestatement(state.restated);
  }

  async function loadRestatement(btn) {
    var rt = (typeof _cmRuntimeFilter === 'function') ? _cmRuntimeFilter() : 'all';
    var q = '?restate=current' + ((rt && rt !== 'all') ? '&runtime=' + encodeURIComponent(rt) : '');
    btn.disabled = true;
    try {
      var body = await (await fetch('/api/usage' + q, { cache: 'no-store' })).json();
      state.restated = body && body.priceBook;
      renderRestatement(state.restated);
    } catch (e) {
      var host = document.getElementById('usage-price-book-restatement');
      if (host) host.innerHTML = '<div style="margin-top:10px;font-size:13px;">The restatement could not be loaded. Nothing changed.</div>';
    }
    btn.disabled = false;
  }

  function renderRestatement(pbk) {
    var host = document.getElementById('usage-price-book-restatement');
    if (!host || !pbk || !pbk.restatement) return;
    var rs = pbk.restatement;
    if (!rs.available) {
      host.innerHTML = '<div style="margin-top:10px;font-size:13px;">There is no recorded book version to restate against.</div>';
      return;
    }
    var html = '<div style="margin-top:12px;padding:10px 12px;border-radius:8px;border:1px dashed rgba(79,70,229,0.5);background:rgba(79,70,229,0.05);">'
      + '<div style="font-weight:600;font-size:13px;">Restatement, not saved</div>'
      + '<div style="font-size:12px;color:var(--text-secondary);margin:2px 0 8px;">Each window valued against version <code>' + esc(rs.against) + '</code> instead of the version in effect at the time. The figures above stay as reported.</div>'
      + '<table class="usage-table"><thead><tr><th></th><th>Restated</th><th>As reported</th><th>Difference</th></tr></thead><tbody>';
    [['today', 'Today'], ['week', 'This week'], ['month', 'This month']].forEach(function (r) {
      var t = (rs.windows || {})[r[0]] || {};
      if (t.withheld) {
        html += '<tr><td>' + r[1] + '</td><td colspan="3" style="color:var(--text-muted);">Held back on this plan.</td></tr>';
        return;
      }
      html += '<tr><td>' + r[1] + '</td><td>' + figure(pbk, 'restatement.windows.' + r[0] + '.restated_usd', t.restated_usd, r[1] + ' restated')
        + '</td><td>' + esc(money(t.original_usd)) + '</td><td>' + esc(t.delta_usd == null ? 'not available' : money(t.delta_usd)) + '</td></tr>';
    });
    html += '</tbody></table><button type="button" class="refresh-btn" style="margin-top:8px;" id="usage-price-book-restate-hide">Hide restatement</button></div>';
    host.innerHTML = html;
    document.getElementById('usage-price-book-restate-hide').addEventListener('click', function () {
      state.restated = null;
      host.innerHTML = '';
    });
  }

  // The Cost tab's way in to the screen (tests/test_every_tab_is_reachable.py).
  function openPriceBook() {
    switchTab('price-book');
  }

  window.loadPriceBookTab = loadPriceBookTab;
  window.renderUsagePriceBook = renderUsagePriceBook;
  window.openPriceBook = openPriceBook;

  // A deep link can open this tab before this deferred bundle has run.
  document.addEventListener('DOMContentLoaded', function () {
    var page = document.getElementById('page-price-book');
    if (page && page.classList.contains('active')) loadPriceBookTab();
  });
})();
