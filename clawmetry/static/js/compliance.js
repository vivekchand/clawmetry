/*
 * Compliance tab (REQ-COMP-FWM-004, Factory requirement
 * 2b319261-73a2-4f64-b497-3dd80b99a72e, clawmetry-pro#250).
 *
 * Renders what clawmetry-pro evaluates: per framework and period, every
 * control with its evidence state, the evidence behind it, and its links to
 * the MITRE ATLAS OpenClaw replay scenarios. Rules this file holds:
 *
 *   - a 402 is an upgrade prompt, never a status code or an empty list;
 *   - on the hosted dashboard (window.CLOUD_MODE) nothing is fetched: the
 *     evidence lives in the agent machine's own store, not in the snapshot;
 *   - only states the evaluator can assign are styled; anything else,
 *     `effective` included, is shown as unrecognised and counted apart;
 *   - no percentage, no certification wording.
 *
 * The pure helpers are exported (window.CMCompliance, and module.exports for
 * tests/test_compliance_tab_js.js) so the rules are tested against the
 * shipped source.
 */
(function (root) {
  'use strict';

  var STATES = {
    exercised: { label: 'Exercised', color: '#3b82f6',
      text: 'at least one mapped finding was stored in the period' },
    configured: { label: 'Configured', color: '#d97706',
      text: 'a mapped finding kind exists; none was stored in the period' },
    gap: { label: 'Gap', color: '#dc2626',
      text: 'no ClawMetry capability is mapped to this item' },
    unknown: { label: 'Unknown', color: '#6b7280',
      text: 'the evidence could not be read' },
    operating: { label: 'Operating', color: '#3b82f6',
      text: 'the control mechanism is configured and was active in the period' },
    not_configured: { label: 'Not configured', color: '#dc2626',
      text: 'no evidence source for this control is configured' }
  };
  var GUARD_ORDER = ['exercised', 'configured', 'gap', 'unknown'];
  var MAP_ORDER = ['operating', 'configured', 'not_configured'];
  var LINK_CLASSES = {
    passing: 'Detected',
    partial: 'Partial',
    missed: 'Missed',
    held_before_action: 'Held before action'
  };

  function esc(v) {
    return String(v === null || v === undefined ? '' : v)
      .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;').replace(/'/g, '&#39;');
  }

  function stateOrder(report) {
    var fw = (report && report.framework) || {};
    return fw.evaluation === 'guard_contract' ? GUARD_ORDER : MAP_ORDER;
  }

  // A state is recognised only if the evaluator for THIS framework can assign
  // it. `effective` is in no list: nothing observes that a risk was contained.
  function stateInfo(status, order) {
    var allowed = order || GUARD_ORDER.concat(MAP_ORDER);
    if (allowed.indexOf(status) >= 0 && STATES[status]) {
      return { known: true, key: status, label: STATES[status].label,
        color: STATES[status].color, text: STATES[status].text };
    }
    return { known: false, key: 'unrecognised', color: '#6b7280',
      label: 'Unrecognised state: ' + String(status),
      text: 'not a state ClawMetry assigns; not counted and not shown as met' };
  }

  function summaryCounts(report) {
    var order = stateOrder(report);
    var out = { unrecognised: 0, total: 0 };
    order.forEach(function (s) { out[s] = 0; });
    ((report && report.controls) || []).forEach(function (c) {
      out.total += 1;
      var info = stateInfo(c.status, order);
      if (info.known) out[c.status] += 1; else out.unrecognised += 1;
    });
    return out;
  }

  function pill(info) {
    return '<span class="cm-comp-state cm-comp-state-' + esc(info.key) + '" title="' + esc(info.text) +
      '" style="display:inline-block;padding:1px 8px;border-radius:10px;font-size:11px;font-weight:600;border:1px solid ' +
      info.color + ';color:' + info.color + ';">' + esc(info.label) + '</span>';
  }

  var CARD = 'background:var(--bg-secondary);border:1px solid var(--border-primary);border-radius:10px;padding:14px 16px;margin:10px 0;';

  function lockedHtml() {
    return '<div class="cm-comp-locked" style="max-width:560px;margin:32px auto;' + CARD + 'text-align:center;padding:28px;">' +
      '<div style="font-size:30px;margin-bottom:8px;">🔒</div>' +
      '<h3 style="margin:0 0 8px 0;font-size:17px;color:var(--text-primary);">The Compliance Pack is part of ClawMetry Pro</h3>' +
      '<p style="margin:0 0 18px 0;font-size:13px;line-height:1.55;color:var(--text-secondary);">' +
      'See every NIST AI RMF, SOC 2, OWASP LLM 2026, OWASP Agentic 2026 and MITRE ATLAS control with the evidence your agents produced, ' +
      'which replayed attack stages it caught or missed, and a printable report for your security review.</p>' +
      '<div style="display:flex;gap:10px;justify-content:center;flex-wrap:wrap;">' +
      '<a href="https://app.clawmetry.com/upgrade?source=compliance" target="_blank" rel="noopener" style="background:var(--bg-accent);color:#fff;border-radius:8px;padding:9px 16px;font-size:13px;font-weight:600;text-decoration:none;">Start 7-day free trial</a>' +
      '<a href="https://clawmetry.com/pricing" target="_blank" rel="noopener" style="border:1px solid var(--border-primary);color:var(--text-secondary);border-radius:8px;padding:9px 16px;font-size:13px;font-weight:600;text-decoration:none;">See pricing</a>' +
      '</div></div>';
  }

  function localOnlyHtml() {
    return '<div class="cm-comp-local-only" style="max-width:640px;' + CARD + '">' +
      '<h3 style="margin:0 0 8px 0;font-size:15px;color:var(--text-primary);">Compliance evidence stays on the machine your agents run on</h3>' +
      '<p style="margin:0 0 8px 0;font-size:13px;line-height:1.55;color:var(--text-secondary);">' +
      'Controls are evaluated against the findings, policy decisions and audit records in that machine\'s local store. ' +
      'They are not part of the encrypted snapshot this hosted dashboard receives, so nothing is evaluated here, and an empty report would be wrong.</p>' +
      '<p style="margin:0;font-size:13px;line-height:1.55;color:var(--text-secondary);">' +
      'Open the ClawMetry dashboard on that machine (usually http://localhost:8900) and choose Compliance, or run ' +
      '<code>clawmetry compliance bundle --framework mitre-atlas --from 2026-08-01 --to 2026-08-31</code> there.</p></div>';
  }

  function messageHtml(title, detail, problems) {
    var list = (problems || []).map(function (p) { return '<li>' + esc(p) + '</li>'; }).join('');
    return '<div class="cm-comp-message" style="max-width:720px;' + CARD + '">' +
      '<div style="font-weight:600;color:var(--text-primary);margin-bottom:6px;">' + esc(title) + '</div>' +
      '<div style="font-size:13px;color:var(--text-secondary);line-height:1.5;">' + esc(detail) + '</div>' +
      (list ? '<ul style="font-size:12px;color:var(--text-secondary);margin:8px 0 0 18px;">' + list + '</ul>' : '') +
      '</div>';
  }

  // Maps an error body to words. Never shows an HTTP status or an error code.
  function errorHtml(body) {
    body = body || {};
    if (body.error === 'report_inconsistent') {
      return messageHtml('This report failed its own consistency check, so it is not shown',
        'A report that contradicts its evidence is refused rather than displayed. These checks failed:',
        body.problems);
    }
    if (body.error === 'unknown_framework') {
      return messageHtml('That framework is not available', 'Choose a framework from the list.');
    }
    return messageHtml('The compliance evaluation did not complete',
      'Try again in a moment. If it keeps failing, check that the ClawMetry daemon on this machine is running.');
  }

  function row(label, value) {
    return '<tr><td style="color:var(--text-muted);padding:2px 12px 2px 0;white-space:nowrap;vertical-align:top;">' + esc(label) +
      '</td><td style="padding:2px 0;color:var(--text-primary);">' + esc(value) + '</td></tr>';
  }

  function linkClassLabel(cls) {
    return LINK_CLASSES[cls] || ('Unrecognised result: ' + String(cls));
  }

  function scenariosHtml(sc, variants) {
    if (sc === null || sc === undefined) return '';
    var h = '<div style="margin-top:8px;"><div style="font-size:12px;font-weight:600;color:var(--text-primary);margin-bottom:4px;">MITRE ATLAS replay scenarios</div>';
    if (sc.note) h += '<div style="font-size:12px;color:var(--text-muted);">' + esc(sc.note) + '</div>';
    var links = sc.links || [];
    if (links.length) {
      h += '<div style="overflow-x:auto;"><table style="border-collapse:collapse;font-size:12px;width:100%;"><tr>' +
        ['Case study', 'Stage', 'ATLAS steps', 'Linked by'].concat(variants.map(function (v) { return v.replace(/_/g, ' '); }))
          .map(function (x) { return '<th style="text-align:left;border-bottom:1px solid var(--border-primary);padding:3px 6px;color:var(--text-muted);font-weight:600;">' + esc(x) + '</th>'; }).join('') + '</tr>';
      links.forEach(function (ln) {
        var steps = (ln.steps || []).map(function (s) { return esc(s.step) + ' ' + esc(s.technique) + ' ' + esc(s.technique_name); }).join('<br>');
        h += '<tr><td style="padding:3px 6px;vertical-align:top;">' + esc(ln.case) + '<br><span style="color:var(--text-muted);">' + esc(ln.case_name) + '</span></td>' +
          '<td style="padding:3px 6px;vertical-align:top;">' + esc(ln.stage) + (ln.decisive ? ' (decisive)' : '') + '<br><span style="color:var(--text-muted);">' + esc(ln.title) + '</span></td>' +
          '<td style="padding:3px 6px;vertical-align:top;">' + steps + '</td>' +
          '<td style="padding:3px 6px;vertical-align:top;">' + esc((ln.match || []).join(', ')) + '</td>';
        variants.forEach(function (v) {
          var r = (ln.variants || {})[v] || {};
          h += '<td style="padding:3px 6px;vertical-align:top;"><span class="cm-comp-link cm-comp-link-' + esc(LINK_CLASSES[r['class']] ? r['class'] : 'unrecognised') + '">' +
            esc(linkClassLabel(r['class'])) + '</span><br><span style="color:var(--text-muted);">' + esc(r.outcome) +
            ((r.finding_kinds || []).length ? ': ' + esc(r.finding_kinds.join(', ')) : '') + '</span></td>';
        });
        h += '</tr>';
      });
      h += '</table></div>';
    }
    if ((sc.benign || []).length) {
      h += '<div style="font-size:12px;color:var(--text-secondary);margin-top:4px;">Benign scenarios replayed: ' + esc(sc.benign.length) +
        '; false positives of the mapped kinds: ' + esc((sc.summary || {}).false_positives || 0) + '.</div>';
    }
    (sc.fail_modes || []).forEach(function (fm) {
      h += '<div style="font-size:12px;color:var(--text-secondary);margin-top:4px;">Fail mode ' + esc(fm.id) + ' (' + esc(fm.relates_to) + '): ' +
        esc(fm.title) + '. ' + esc(fm.meaning) + '</div>';
    });
    return h + '</div>';
  }

  function controlHtml(c, report, variants) {
    var order = stateOrder(report);
    var info = stateInfo(c.status, order);
    var guard = order === GUARD_ORDER;
    var h = '<div class="cm-comp-control" data-control="' + esc(c.id) + '" style="' + CARD + '">' +
      '<div style="display:flex;gap:8px;align-items:center;flex-wrap:wrap;margin-bottom:6px;">' +
      '<span style="font-weight:700;color:var(--text-primary);">' + esc(c.id) + '</span>' +
      '<span style="color:var(--text-secondary);">' + esc(c.text) + '</span>' + pill(info) +
      (c.type ? '<span style="font-size:11px;color:var(--text-muted);">' + esc(c.type) + '</span>' : '') + '</div>';
    if (!info.known) {
      h += '<div style="font-size:12px;color:#dc2626;margin-bottom:6px;">ClawMetry does not assign this state. It is not counted in the summary and is not evidence that the control is met.</div>';
    }
    var ev = c.evidence || null;
    if (guard) {
      h += '<table style="font-size:12px;border-collapse:collapse;">' +
        row('Coverage mode', c.coverage_mode || 'none (gap)') +
        row('Pre-action control', 'no: findings are raised after the activity') +
        row('Mapped finding kinds', (c.finding_kinds || []).join(', ') || 'none');
      if (ev) {
        var pd = ev.policy_decisions;
        h += row('Stored findings in period', String(ev.findings) + (ev.findings_capped ? '+' : '')) +
          row('Sessions', ev.sessions) +
          row('Runtimes', (ev.runtimes || []).join(', ') || 'none') +
          row('First evidence', ev.first_evidence_at || 'none') +
          row('Last evidence', ev.last_evidence_at || 'none') +
          row('Policy decisions', pd ? ('configured ' + (pd.configured || 0) + ', exercised ' + (pd.exercised || 0) + ', failed ' + (pd.failed || 0)) : 'not readable');
      }
      h += '</table>';
      if (c.gap_reason) h += '<div style="font-size:12px;color:var(--text-muted);margin-top:4px;">' + esc(c.gap_reason) + '</div>';
      var limits = c.limits || {};
      var lk = Object.keys(limits);
      if (lk.length) {
        h += '<details style="margin-top:6px;font-size:12px;"><summary style="cursor:pointer;color:var(--text-secondary);">Limits</summary><ul style="margin:4px 0 0 18px;">' +
          lk.map(function (k) { return '<li>' + esc(k) + ': ' + esc(limits[k]) + '</li>'; }).join('') + '</ul></details>';
      }
    } else if (ev) {
      h += '<table style="font-size:12px;border-collapse:collapse;"><tr><th style="text-align:left;padding-right:12px;color:var(--text-muted);">Evidence source</th><th style="text-align:left;padding-right:12px;color:var(--text-muted);">Configured</th><th style="text-align:left;padding-right:12px;color:var(--text-muted);">Active in period</th><th style="text-align:left;color:var(--text-muted);">Rows</th></tr>' +
        Object.keys(ev).map(function (k) {
          var e = ev[k] || {};
          return '<tr><td style="padding-right:12px;">' + esc(k) + '</td><td>' + (e.configured ? 'yes' : 'no') + '</td><td>' + (e.active ? 'yes' : 'no') +
            '</td><td>' + esc(String(e.count || 0) + (e.capped ? '+' : '')) + (e.error ? ' (unreadable)' : '') + '</td></tr>';
        }).join('') + '</table>';
      if (c.remediation) h += '<div style="font-size:12px;color:var(--text-secondary);margin-top:4px;">Remediation: ' + esc(c.remediation) + '</div>';
    }
    if ((c.caveats || []).length) {
      h += '<ul style="font-size:12px;color:var(--text-secondary);margin:6px 0 0 18px;">' +
        c.caveats.map(function (x) { return '<li>' + esc(x) + '</li>'; }).join('') + '</ul>';
    }
    if (guard) h += scenariosHtml(c.scenarios, variants);
    return h + '</div>';
  }

  function renderReport(report) {
    report = report || {};
    var fw = report.framework || {};
    var order = stateOrder(report);
    var counts = summaryCounts(report);
    var block = report.scenario_traceability || {};
    var variants = block.available ? (block.variants || []) : [];
    var period = report.period || {};
    var h = '<div class="cm-comp-report">';
    h += '<div style="' + CARD + '"><div style="font-size:15px;font-weight:700;color:var(--text-primary);">' + esc(fw.name) + ' ' + esc(fw.edition || fw.version || '') + '</div>' +
      '<div style="font-size:12px;color:var(--text-muted);margin:2px 0 8px 0;">' + esc(period.from) + ' to ' + esc(period.to) +
      (fw.mapping_version ? ' · mapping version ' + esc(fw.mapping_version) : '') + '</div>' +
      '<div style="display:flex;gap:10px;flex-wrap:wrap;">' +
      order.map(function (s) {
        var info = stateInfo(s, order);
        return '<div class="cm-comp-count" data-state="' + esc(s) + '" title="' + esc(info.text) + '" style="border:1px solid var(--border-primary);border-radius:8px;padding:6px 12px;min-width:90px;">' +
          '<div style="font-size:20px;font-weight:700;color:' + info.color + ';">' + esc(counts[s]) + '</div><div style="font-size:11px;color:var(--text-muted);">' + esc(info.label) + '</div></div>';
      }).join('') +
      (counts.unrecognised ? '<div class="cm-comp-count" data-state="unrecognised" style="border:1px solid #dc2626;border-radius:8px;padding:6px 12px;"><div style="font-size:20px;font-weight:700;color:#dc2626;">' + esc(counts.unrecognised) + '</div><div style="font-size:11px;color:var(--text-muted);">Unrecognised</div></div>' : '') +
      '<div style="border:1px solid var(--border-primary);border-radius:8px;padding:6px 12px;"><div style="font-size:20px;font-weight:700;color:var(--text-primary);">' + esc(counts.total) + '</div><div style="font-size:11px;color:var(--text-muted);">Listed</div></div>' +
      '</div>' +
      '<div style="font-size:12px;color:var(--text-secondary);margin-top:10px;line-height:1.5;">' + esc(report.scope_note) + '</div>';
    if (order === GUARD_ORDER) {
      h += '<div style="font-size:12px;color:var(--text-muted);margin-top:6px;">Effective is never assigned: nothing independently observes that a risk was contained.</div>';
    }
    if ((report.caveats || []).length) {
      h += '<ul style="font-size:12px;color:var(--text-secondary);margin:8px 0 0 18px;">' +
        report.caveats.map(function (x) { return '<li>' + esc(x) + '</li>'; }).join('') + '</ul>';
    }
    h += '</div>';
    h += '<div style="' + CARD + 'font-size:12px;color:var(--text-secondary);line-height:1.5;">';
    if (block.available) {
      var atlas = block.atlas || {};
      h += '<b>Scenario traceability.</b> Linked against the MITRE ATLAS OpenClaw replay suite ' + esc(block.suite_version) +
        ' (ATLAS ' + esc(atlas.edition) + '). Evidence tier: ' + esc(block.tier) + '. ' + esc(block.tier_note);
    } else {
      h += '<b>Scenario traceability.</b> ' + esc(block.reason || 'Not available for this framework.');
    }
    h += '</div>';
    (report.controls || []).forEach(function (c) { h += controlHtml(c, report, variants); });
    return h + '</div>';
  }

  function isoDay(d) {
    return d.getFullYear() + '-' + ('0' + (d.getMonth() + 1)).slice(-2) + '-' + ('0' + d.getDate()).slice(-2);
  }

  function query(fw, from, to) {
    return 'framework=' + encodeURIComponent(fw) + '&from=' + encodeURIComponent(from) +
      '&to=' + encodeURIComponent(to + 'T23:59:59');
  }

  var api = {
    STATES: STATES, GUARD_ORDER: GUARD_ORDER, MAP_ORDER: MAP_ORDER, LINK_CLASSES: LINK_CLASSES,
    esc: esc, stateInfo: stateInfo, summaryCounts: summaryCounts, renderReport: renderReport,
    lockedHtml: lockedHtml, localOnlyHtml: localOnlyHtml, errorHtml: errorHtml, query: query
  };
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  if (!root || !root.document) return;
  root.CMCompliance = api;

  // ── DOM glue ─────────────────────────────────────────────────────────────
  var loaded = false;

  function el(id) { return root.document.getElementById(id); }
  function setBody(html) { var b = el('cm-comp-body'); if (b) b.innerHTML = html; }
  function setStatus(t) { var s = el('cm-comp-status'); if (s) s.textContent = t || ''; }
  function showControls(on) { var c = el('cm-comp-controls'); if (c) c.style.display = on ? 'flex' : 'none'; }

  function params() {
    var f = el('cm-comp-framework'), a = el('cm-comp-from'), b = el('cm-comp-to');
    return { fw: f ? f.value : '', from: a ? a.value : '', to: b ? b.value : '' };
  }

  function readJson(r) {
    return r.json().catch(function () { return {}; });
  }

  function loadComplianceTab() {
    // Hosted dashboard: the evidence is not here. Say so; fetch nothing.
    if (root.CLOUD_MODE) {
      showControls(false);
      setStatus('');
      setBody(localOnlyHtml());
      return;
    }
    if (loaded) return;
    setStatus('');
    fetch('/api/compliance/frameworks').then(function (r) {
      if (r.status === 402) { showControls(false); setBody(lockedHtml()); return null; }
      if (!r.ok) return readJson(r).then(function (b) { setBody(errorHtml(b)); return null; });
      return r.json();
    }).then(function (data) {
      if (!data) return;
      var sel = el('cm-comp-framework');
      var fws = data.frameworks || [];
      if (!fws.length) {
        setBody(messageHtml('No framework maps are installed', 'The installed Compliance Pack lists no framework.'));
        return;
      }
      if (sel) {
        sel.innerHTML = fws.map(function (f) {
          return '<option value="' + esc(f.id) + '">' + esc(f.name) + (f.version ? ' ' + esc(f.version) : '') + '</option>';
        }).join('');
      }
      var now = new Date();
      var start = new Date(now.getTime() - 30 * 86400000);
      if (el('cm-comp-from') && !el('cm-comp-from').value) el('cm-comp-from').value = isoDay(start);
      if (el('cm-comp-to') && !el('cm-comp-to').value) el('cm-comp-to').value = isoDay(now);
      loaded = true;
      showControls(true);
      complianceEvaluate();
    }).catch(function () {
      setBody(errorHtml({}));
    });
  }

  function complianceEvaluate() {
    if (root.CLOUD_MODE) { setBody(localOnlyHtml()); return; }
    var p = params();
    if (!p.fw) return;
    setStatus('Evaluating controls…');
    fetch('/api/compliance/controls?' + query(p.fw, p.from, p.to)).then(function (r) {
      if (r.status === 402) { showControls(false); setBody(lockedHtml()); return null; }
      if (!r.ok) return readJson(r).then(function (b) { setBody(errorHtml(b)); return null; });
      return r.json();
    }).then(function (report) {
      setStatus('');
      if (report) setBody(renderReport(report));
    }).catch(function () {
      setStatus('');
      setBody(errorHtml({}));
    });
  }

  function fetchBlob(url, opts, onBlob) {
    return fetch(url, opts).then(function (r) {
      if (r.status === 402) { showControls(false); setBody(lockedHtml()); return null; }
      if (!r.ok) return readJson(r).then(function (b) { setBody(errorHtml(b)); return null; });
      return r.blob();
    }).then(function (blob) {
      setStatus('');
      if (blob) onBlob(blob);
    }).catch(function () {
      setStatus('');
      setBody(errorHtml({}));
    });
  }

  function complianceOpenReport() {
    if (root.CLOUD_MODE) { setBody(localOnlyHtml()); return; }
    var p = params();
    if (!p.fw) return;
    // Opened synchronously so a popup blocker treats it as the click's window.
    var win = root.open('', '_blank');
    setStatus('Building the printable report…');
    fetchBlob('/api/compliance/report?' + query(p.fw, p.from, p.to), undefined, function (blob) {
      var url = root.URL.createObjectURL(new Blob([blob], { type: 'text/html' }));
      if (win) { win.location.href = url; } else { root.location.assign(url); }
    }).then(function () {
      if (win && win.location && win.location.href === 'about:blank') { try { win.close(); } catch (e) {} }
    });
  }

  function complianceDownloadBundle() {
    if (root.CLOUD_MODE) { setBody(localOnlyHtml()); return; }
    var p = params();
    if (!p.fw) return;
    setStatus('Building the evidence bundle…');
    fetchBlob('/api/compliance/bundle?' + query(p.fw, p.from, p.to), { method: 'POST' }, function (blob) {
      var a = root.document.createElement('a');
      a.href = root.URL.createObjectURL(blob);
      a.download = 'clawmetry-compliance_' + p.fw + '_' + p.from + '_' + p.to + '.zip';
      root.document.body.appendChild(a);
      a.click();
      a.remove();
    });
  }

  root.loadComplianceTab = loadComplianceTab;
  root.complianceEvaluate = complianceEvaluate;
  root.complianceOpenReport = complianceOpenReport;
  root.complianceDownloadBundle = complianceDownloadBundle;
})(typeof window !== 'undefined' ? window : null);
