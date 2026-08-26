// ─────────────────────────────────────────────────────────────────────────
// Provenance: every figure says how it was obtained.
//
// The shared badge that renders beside a dollar amount or a score, plus the
// formatters that put it there. The vocabulary is defined once, in Python
// (clawmetry/provenance.py), and travels beside the figure it describes:
//
//   { "todayCost": 4.12,
//     "provenance": { "todayCost": { "basis": "derived",
//                                    "formula": "...", "source": "...",
//                                    "window": "...", "inputs": {...} } } }
//
// Four bases, in the order a reader trusts them:
//
//   measured   read from a record the agent wrote
//   derived    computed from measured inputs by an exact rule
//   estimated  modelled, with an assumption that can be wrong
//   unknown    nobody knows, so nothing is shown
//
// The last one is the whole point. A failed read once shipped as "$0.00" and
// was read, correctly, as a real result: a zero and a hole are identical once
// they are formatted. Here they never share a shape. `cmMoney` given a null
// paints "not available" in a dimmed, dashed pill; given a real measured zero
// it paints "$0.00" and badges it as measured. Two different facts, two
// different things on screen.
//
// Loaded before app.js so every renderer can reach these; deliberately
// self-contained (its own escaper, no dependency on app.js load order).
// ─────────────────────────────────────────────────────────────────────────
(function () {
  'use strict';

  var MEASURED = 'measured', DERIVED = 'derived',
      ESTIMATED = 'estimated', UNKNOWN = 'unknown';

  // Mirrors clawmetry/provenance.py BASIS_LABEL. The server sends its own
  // `label`, so these are the fallback for a payload from an older daemon.
  var LABEL = {};
  LABEL[MEASURED] = 'measured';
  LABEL[DERIVED] = 'derived';
  LABEL[ESTIMATED] = 'estimated';
  LABEL[UNKNOWN] = 'no basis';

  var HINT = {};
  HINT[MEASURED] = 'Measured: read from a record the agent wrote.';
  HINT[DERIVED] = 'Derived: computed from measured inputs by an exact rule.';
  HINT[ESTIMATED] = 'Estimated: modelled, with an assumption that can be wrong.';
  HINT[UNKNOWN] = 'No basis: this number is not available, so nothing is shown.';

  // One letter for dense tables, where the full word would crowd out the
  // number it is describing.
  var INITIAL = {};
  INITIAL[MEASURED] = 'M';
  INITIAL[DERIVED] = 'D';
  INITIAL[ESTIMATED] = 'E';
  INITIAL[UNKNOWN] = '?';

  // A figure that arrived with no provenance at all: an older daemon, or a
  // surface nobody has labelled yet. It is not the same as "unknown" (we do
  // have a number), and it must not pass silently as if it were labelled,
  // or the rule stops being a rule.
  var UNLABELLED = {
    basis: 'unlabelled',
    label: 'unlabelled',
    hint: 'This figure carries no basis. It comes from a surface that has not '
        + 'been labelled yet, or from a daemon older than provenance labelling.'
  };

  function esc(s) {
    return String(s == null ? '' : s)
      .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }

  function isNum(v) {
    return typeof v === 'number' && isFinite(v);
  }

  // ── Lookup ──────────────────────────────────────────────────────────────
  // Accepts either the whole payload (and a key) or an entry directly, so a
  // caller that has already pulled the entry out of a row does not have to
  // pretend it still has the payload.
  function of(payload, key) {
    if (!payload || typeof payload !== 'object') return null;
    if (payload.basis) return payload;              // already an entry
    var prov = payload.provenance;
    if (!prov || typeof prov !== 'object') return null;
    var got = prov[key];
    return (got && typeof got === 'object') ? got : null;
  }

  function isUnknown(entry) {
    return !!entry && entry.basis === UNKNOWN;
  }

  // ── The tooltip: the formula, and enough to reconstruct the number ──────
  function tip(entry, label) {
    if (!entry) return UNLABELLED.hint;
    var lines = [];
    if (label) lines.push(label);
    lines.push(entry.hint || HINT[entry.basis] || '');
    if (entry.reason) lines.push('Why: ' + entry.reason);
    if (entry.formula) lines.push('How: ' + entry.formula + '.');
    if (entry.window) lines.push('Over: ' + entry.window + '.');
    if (entry.inputs) {
      var bits = [];
      for (var k in entry.inputs) {
        if (Object.prototype.hasOwnProperty.call(entry.inputs, k)) {
          bits.push(k + ' = ' + entry.inputs[k]);
        }
      }
      if (bits.length) lines.push('From: ' + bits.join(', ') + '.');
    }
    if (entry.source) lines.push('Source: ' + entry.source + '.');
    if (entry.note) lines.push('Note: ' + entry.note + '.');
    return lines.filter(Boolean).join('\n');
  }

  // ── The badge ───────────────────────────────────────────────────────────
  // opts.compact  one letter instead of the word (dense tables)
  // opts.label    a name for the figure, shown as the tooltip's first line
  function badge(entry, opts) {
    opts = opts || {};
    var e = entry || UNLABELLED;
    var basis = e.basis || UNKNOWN;
    var text = opts.compact
      ? (INITIAL[basis] || '?')
      : (e.label || LABEL[basis] || basis);
    return '<span class="cm-prov cm-prov-' + esc(basis)
      + (opts.compact ? ' cm-prov-compact' : '')
      + '" title="' + esc(tip(e, opts.label)) + '"'
      + ' aria-label="' + esc((opts.label ? opts.label + ': ' : '') + text)
      + '">' + esc(text) + '</span>';
  }

  // ── Formatting a figure ─────────────────────────────────────────────────
  // Money the way this dashboard has always shown it, kept in ONE place: six
  // copies of this function had drifted across app.js before it moved here.
  function fmtMoney(v) {
    var n = Number(v);
    if (!isFinite(n)) return '';
    if (n >= 0.01 || n <= -0.01) return '$' + n.toFixed(2);
    if (n > 0) return '<$0.01';
    return '$0.00';
  }

  function fmtScore(v, opts) {
    var n = Number(v);
    if (!isFinite(n)) return '';
    var out = n.toFixed((opts && opts.decimals != null) ? opts.decimals : 2);
    return (opts && opts.outOf) ? out + ' / ' + opts.outOf : out;
  }

  // The unknown state. Never a number, never a zero, never blank: a reader
  // has to be able to tell "we could not get this" from "there was none".
  function unknownHtml(entry, opts) {
    opts = opts || {};
    var e = entry || { basis: UNKNOWN, hint: HINT[UNKNOWN] };
    return '<span class="cm-fig cm-fig-unknown" title="'
      + esc(tip(e, opts.label)) + '">'
      + esc(opts.emptyText || 'not available') + '</span>'
      + (opts.noBadge ? '' : badge(e, opts));
  }

  // figure(value, entry, opts) -> html
  //   opts.format    'money' (default) | 'score' | 'raw'
  //   opts.compact   compact badge
  //   opts.noBadge   value only (for a cell whose column header carries it)
  //   opts.label     figure name, shown first in the tooltip
  //   opts.emptyText what to show instead of a number when unknown
  function figure(value, entry, opts) {
    opts = opts || {};
    if (isUnknown(entry) || value == null || (typeof value === 'number' && !isFinite(value))) {
      return unknownHtml(entry, opts);
    }
    var text;
    if (opts.format === 'score') text = fmtScore(value, opts);
    else if (opts.format === 'raw') text = String(value);
    else text = fmtMoney(value);
    if (!isNum(Number(value)) && opts.format !== 'raw') return unknownHtml(entry, opts);
    var e = entry || UNLABELLED;
    return '<span class="cm-fig" data-basis="' + esc(e.basis || 'unlabelled')
      + '" title="' + esc(tip(e, opts.label)) + '">' + esc(text) + '</span>'
      + (opts.noBadge ? '' : badge(e, opts));
  }

  // Shorthands for the two shapes that appear most: a money figure looked up
  // from a payload by key, and a score.
  function money(payload, key, opts) {
    var v = (payload && typeof payload === 'object') ? payload[key] : payload;
    return figure(v, of(payload, key), opts);
  }

  function score(payload, key, opts) {
    opts = opts || {};
    opts.format = 'score';
    var v = (payload && typeof payload === 'object') ? payload[key] : payload;
    return figure(v, of(payload, key), opts);
  }

  // Plain text, for a title attribute or a DOM node with no innerHTML.
  function text(value, entry, opts) {
    opts = opts || {};
    if (isUnknown(entry) || value == null) return opts.emptyText || 'not available';
    if (opts.format === 'score') return fmtScore(value, opts);
    return fmtMoney(value);
  }

  window.cmProv = {
    MEASURED: MEASURED, DERIVED: DERIVED,
    ESTIMATED: ESTIMATED, UNKNOWN: UNKNOWN,
    LABEL: LABEL, HINT: HINT,
    of: of, isUnknown: isUnknown, tip: tip, badge: badge,
    figure: figure, money: money, score: score, text: text,
    fmtMoney: fmtMoney, fmtScore: fmtScore
  };
  // Terse aliases: these get called from inside string-concatenated table
  // rows, where `window.cmProv.figure(...)` would be most of the line.
  window.cmMoney = money;
  window.cmScore = score;
  window.cmFigure = figure;
  window.cmProvBadge = badge;
  window.cmFmtMoney = fmtMoney;
})();
