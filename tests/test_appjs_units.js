// Unit tests for pure functions in clawmetry/static/js/app.js.
//
// Covers issue #1127 fixes #2 (formatBrainTime year handling) and #5 (stuck
// banner localStorage dismissal). Runs under `node tests/test_appjs_units.js`
// — no JSDOM, no Playwright, ~50ms. Pulls the target functions out of
// app.js via regex and evaluates them in a sandbox with a stub
// `localStorage`, so we test the actual shipped source rather than a copy.

const fs = require('fs');
const path = require('path');
const vm = require('vm');

const APP_JS = path.join(__dirname, '..', 'clawmetry', 'static', 'js', 'app.js');
const src = fs.readFileSync(APP_JS, 'utf8');

let passed = 0;
let failed = 0;

function eq(actual, expected, label) {
  if (actual === expected) {
    passed++;
    console.log('  ok   ' + label);
  } else {
    failed++;
    console.log('  FAIL ' + label);
    console.log('       expected: ' + JSON.stringify(expected));
    console.log('       actual:   ' + JSON.stringify(actual));
  }
}

function truthy(value, label) {
  if (value) {
    passed++;
    console.log('  ok   ' + label);
  } else {
    failed++;
    console.log('  FAIL ' + label + ' (got falsy)');
  }
}

function extractFunction(name) {
  // Match `function NAME(...) { ... }` with a balanced top-level brace.
  // app.js uses 2-space indent and never nests another top-level
  // `function NAME` so the first `^}` after the opening line is the close.
  const re = new RegExp('^function ' + name + '\\b[\\s\\S]*?^\\}', 'm');
  const m = src.match(re);
  if (!m) throw new Error('could not find function ' + name + ' in app.js');
  return m[0];
}

// ── Test bug #2 — formatBrainTime year handling ────────────────────────
console.log('formatBrainTime (issue #1127 — year missing for cross-year dates)');
{
  const fnSrc = extractFunction('formatBrainTime');
  const sandbox = { Date: Date };
  vm.createContext(sandbox);
  vm.runInContext(fnSrc + '\nthis._formatBrainTime = formatBrainTime;', sandbox);
  const fmt = sandbox._formatBrainTime;

  // Pin "now" to a deterministic moment by stubbing Date's no-arg constructor.
  // We do it via a small wrapper so the function under test always sees the
  // same "now". new Date(isoStr) must still work for real ISO strings.
  function withNow(nowIso, fn) {
    const RealDate = Date;
    sandbox.Date = function(arg) {
      if (arguments.length === 0) return new RealDate(nowIso);
      return new RealDate(arg);
    };
    sandbox.Date.prototype = RealDate.prototype;
    try { return fn(); } finally { sandbox.Date = RealDate; }
  }

  // Same day → "Today"
  withNow('2026-05-13T15:00:00Z', function() {
    const out = fmt('2026-05-13T10:07:28.619Z');
    truthy(out.indexOf('Today') !== -1, 'same day → contains "Today"');
    truthy(out.indexOf('2026') === -1, 'same day → no year');
  });

  // Same year, different day → no year (e.g. "9 May")
  withNow('2026-05-13T15:00:00Z', function() {
    const out = fmt('2026-05-09T10:07:28.619Z');
    truthy(out.indexOf('May') !== -1, 'same year → contains "May"');
    truthy(out.indexOf('2026') === -1, 'same year → year omitted (compact)');
    truthy(out.indexOf('Today') === -1, 'same year → not "Today"');
  });

  // Different year → MUST include year (the bug)
  withNow('2026-05-13T15:00:00Z', function() {
    const out = fmt('2025-05-09T10:07:28.619Z');
    truthy(out.indexOf('May') !== -1, 'cross-year → contains "May"');
    truthy(out.indexOf('2025') !== -1, 'cross-year → year included (bug #1127.2)');
  });

  // Bad input → does not throw (graceful fallback, exact shape not asserted
  // because formatBrainTime's pre-existing behaviour is to let Date(NaN)
  // through; we only require it doesn't crash).
  withNow('2026-05-13T15:00:00Z', function() {
    let threw = false;
    try { fmt(null); } catch(e) { threw = true; }
    eq(threw, false, 'null → no throw');
    try { fmt(''); } catch(e) { threw = true; }
    eq(threw, false, 'empty string → no throw');
  });
}

// ── Test bug #5 — stuck-session dismissal persistence ──────────────────
console.log('stuck-session banner dismissal (issue #1127 — resurfaces after reload)');
{
  // Build a minimal sandbox with a stub localStorage.
  const store = {};
  const sandbox = {
    Date: Date,
    localStorage: {
      getItem: function(k) { return Object.prototype.hasOwnProperty.call(store, k) ? store[k] : null; },
      setItem: function(k, v) { store[k] = String(v); },
      removeItem: function(k) { delete store[k]; },
    },
    document: {
      getElementById: function() { return null; },
    },
    _stuckCount: 0,
    _stuckSessions: {},
    _updateStuckBadge: function() {},
    _clearStuckBanner: function() {},
  };

  // Pull in the helpers and the show/dismiss handlers.
  const wanted = [
    '_readStuckDismissals',
    '_writeStuckDismissals',
    '_pruneStuckDismissals',
    '_isStuckDismissed',
    '_markStuckDismissed',
  ];
  const constants = [];
  src.split('\n').forEach(function(line) {
    if (line.indexOf('var _STUCK_DISMISS_KEY') === 0) constants.push(line);
    if (line.indexOf('var _STUCK_DISMISS_TTL_MS') === 0) constants.push(line);
  });
  let code = constants.join('\n') + '\n';
  wanted.forEach(function(name) { code += extractFunction(name) + '\n'; });
  code += '\nthis.api = {\n';
  wanted.forEach(function(name) { code += '  ' + name + ': ' + name + ',\n'; });
  code += '};';

  vm.createContext(sandbox);
  vm.runInContext(code, sandbox);
  const api = sandbox.api;

  // No dismissal yet.
  eq(api._isStuckDismissed('s-1'), false, 'fresh state → not dismissed');

  // Mark dismissed, verify persists.
  api._markStuckDismissed('s-1');
  eq(api._isStuckDismissed('s-1'), true, 'after _markStuckDismissed → dismissed');
  eq(api._isStuckDismissed('s-2'), false, 'different session → independent');

  // Round-trip via store → simulates page reload.
  truthy(store['stuck-session-dismissed'], 'persisted into localStorage');
  // Empty cache, re-read.
  const reload = JSON.parse(store['stuck-session-dismissed']);
  truthy(reload['s-1'] > 0, 'localStorage holds timestamp for s-1');

  // Empty / blank session id → never dismissed.
  eq(api._isStuckDismissed(''), false, 'empty sessionId → not dismissed');
  api._markStuckDismissed(''); // no-op
  eq(Object.keys(JSON.parse(store['stuck-session-dismissed'])).length, 1,
     'empty sessionId is a no-op');

  // TTL prune: backdate s-1 to 25h ago, prune drops it.
  const stale = JSON.parse(store['stuck-session-dismissed']);
  stale['s-1'] = Date.now() - 25 * 60 * 60 * 1000;
  store['stuck-session-dismissed'] = JSON.stringify(stale);
  eq(api._isStuckDismissed('s-1'), false, '> 24h old → no longer dismissed');
  const after = JSON.parse(store['stuck-session-dismissed'] || '{}');
  truthy(!('s-1' in after), '> 24h entry pruned from store');
}

// ── Test channel-event renderer (Telegram/Signal/Slack/… provider+sender) ──
//
// Coordinates with the Telegram-ingest agent (PR aca53ec8) on the field
// names: provider, sender, chat_id, direction. Verifies:
//   1. _extractChannelInfo recognises top-level fields (the path the
//      Brain endpoint uses after we enrich channel.* events).
//   2. _extractChannelInfo recognises nested ev.data.{provider,from,…}
//      (the path when the Brain endpoint passes the raw payload through).
//   3. _extractChannelInfo returns null for non-channel events (cli/cron/
//      tool calls) so the legacy render branch keeps owning them.
//   4. renderChannelEventMeta produces HTML containing the provider emoji,
//      the human display name, the sender, and a direction arrow.
//   5. Display-name overrides ("Google Chat", "MS Teams") work.
console.log('channel event renderer (Brain provider/sender labels)');
{
  const sandbox = {
    Date: Date,
    console: console,
  };
  // Pull in the channel maps + helpers + render branch. We grab a slice of
  // app.js by line range so we don't have to single-out 4 helpers and 2
  // dictionaries with separate regexes.
  const lines = src.split('\n');
  const startMarker = 'var _channelIcons = {';
  const endMarker   = '// Render the meta row for a channel event';
  const startIdx = lines.findIndex(function(l) { return l.indexOf(startMarker) >= 0; });
  if (startIdx < 0) throw new Error('start marker not found in app.js');
  const endIdx = lines.findIndex(function(l, i) { return i > startIdx && l.indexOf(endMarker) >= 0; });
  if (endIdx < 0) throw new Error('end marker not found in app.js');
  // Slice covers _channelIcons → _channelDisplayName + _extractChannelInfo.
  let code = lines.slice(startIdx, endIdx).join('\n') + '\n';
  // Add renderChannelEventMeta — single function definition.
  code += extractFunction('renderChannelEventMeta') + '\n';
  // escHtml is a small one-liner; pull it in too.
  code += extractFunction('escHtml') + '\n';
  code += '\nthis.api = {' +
          '  _extractChannelInfo: _extractChannelInfo,' +
          '  renderChannelEventMeta: renderChannelEventMeta,' +
          '  _channelDisplayName: _channelDisplayName,' +
          '  _channelIcons: _channelIcons,' +
          '};';
  vm.createContext(sandbox);
  vm.runInContext(code, sandbox);
  const api = sandbox.api;

  // (1) Top-level fields — the shape our brain.py enrichment emits.
  const inboundTop = {
    type: 'CHANNEL.IN',
    provider: 'telegram',
    sender: 'Vivek Chand',
    chat_id: '1532693273',
    detail: 'hello, how are you doing?',
    time: '2026-05-13T10:00:00Z',
  };
  const info1 = api._extractChannelInfo(inboundTop);
  truthy(info1, 'top-level channel event detected');
  eq(info1.provider, 'telegram', 'provider parsed from top-level field');
  eq(info1.sender, 'Vivek Chand', 'sender parsed from top-level field');
  eq(info1.chatId, '1532693273', 'chat_id parsed from top-level field');
  eq(info1.direction, 'in', 'direction = in for CHANNEL.IN');
  eq(info1.providerLabel, 'Telegram', 'Telegram → Telegram (title-case)');
  eq(info1.providerIcon, '📱', 'Telegram emoji');

  // (2) Nested data — the shape if brain enrichment ever drops fields.
  const inboundNested = {
    type: 'CHANNEL.IN',
    data: {
      provider: 'signal',
      from: { username: 'vivek', id: '+15551234567' },
      chat_id: 'sig-abc',
      text: 'sup',
    },
  };
  const info2 = api._extractChannelInfo(inboundNested);
  truthy(info2, 'nested-data channel event detected');
  eq(info2.provider, 'signal', 'provider parsed from data.provider');
  eq(info2.sender, 'vivek', 'sender parsed from data.from.username');
  eq(info2.providerIcon, '📡', 'Signal emoji');
  eq(info2.providerColor, '#3a76f0', 'Signal color');

  // (3) Outbound (agent reply): role=assistant under data, no top-level fields.
  const outbound = {
    type: 'CHANNEL.OUT',
    data: { provider: 'telegram', role: 'assistant', text: 'doing well!' },
  };
  const info3 = api._extractChannelInfo(outbound);
  truthy(info3, 'outbound channel event detected');
  eq(info3.direction, 'out', 'direction = out for CHANNEL.OUT');

  // (4) Non-channel events fall through (return null).
  eq(api._extractChannelInfo({ type: 'EXEC', detail: 'ls -la' }), null,
     'EXEC (tool) event → null');
  eq(api._extractChannelInfo({ type: 'AGENT', source: 'main', detail: 'thinking' }), null,
     'AGENT main event → null');
  eq(api._extractChannelInfo({ type: 'USER', channel: 'cli' }), null,
     'cli channel → null (legacy branch owns it)');
  eq(api._extractChannelInfo(null), null, 'null event → null');

  // (5) Render branch: assert HTML contains provider emoji+name, sender, arrow.
  const html = api.renderChannelEventMeta(inboundTop, info1);
  truthy(html.indexOf('📱') !== -1, 'rendered HTML contains Telegram emoji');
  truthy(html.indexOf('Telegram') !== -1, 'rendered HTML contains "Telegram"');
  truthy(html.indexOf('Vivek Chand') !== -1, 'rendered HTML contains sender name');
  truthy(html.indexOf('↘') !== -1, 'inbound rendered with ↘ arrow');
  truthy(html.indexOf('brain-channel-pill') !== -1, 'pill class applied');
  truthy(html.indexOf('font-style:italic') !== -1, 'sender italicised');
  // Outbound uses ↗.
  const htmlOut = api.renderChannelEventMeta(outbound, info3);
  truthy(htmlOut.indexOf('↗') !== -1, 'outbound rendered with ↗ arrow');

  // (6) Display-name overrides.
  eq(api._channelDisplayName('googlechat'), 'Google Chat',
     'googlechat → "Google Chat"');
  eq(api._channelDisplayName('msteams'), 'MS Teams', 'msteams → "MS Teams"');
  eq(api._channelDisplayName('imessage'), 'iMessage', 'imessage → "iMessage"');
  eq(api._channelDisplayName('whatsapp'), 'Whatsapp',
     'whatsapp → title-case fallback');

  // (7) Detail text is unchanged — channel renderer only owns the meta row,
  // the existing renderBrainDetail keeps owning the body. This is enforced
  // by the renderBrainStream wiring rather than this helper, so we only
  // assert the helper does NOT touch ev.detail.
  eq(inboundTop.detail, 'hello, how are you doing?',
     'helper did not mutate ev.detail');

  // (8) HTML is escaped — XSS-style sender names don't break out.
  const evil = {
    type: 'CHANNEL.IN', provider: 'telegram',
    sender: '<script>alert(1)</script>', chat_id: '1',
  };
  const evilInfo = api._extractChannelInfo(evil);
  const evilHtml = api.renderChannelEventMeta(evil, evilInfo);
  truthy(evilHtml.indexOf('<script>') === -1, 'sender < escaped');
  truthy(evilHtml.indexOf('&lt;script&gt;') !== -1, 'sender appears escaped');

  // (9) Body-missing affordance for outbound channel events (issue #1201).
  // PR #1198 ingests Telegram outbound ACKs from gateway.log with
  // body=None and a raw_blob.body_capture="ack_only" breadcrumb. Without
  // this affordance the Brain row collapsed to an empty detail span — the
  // user concluded the bot replied with nothing. Verify the renderer:
  //   - flags the event via info.bodyMissing / info.ackOnly,
  //   - emits a "⤴ sent" pill + "(no body captured)" label, NOT empty,
  //   - explains the missing-body via tooltip,
  //   - does NOT trigger for inbound (user) events with empty body,
  //   - does NOT trigger for outbound events that DO have body text.
  const ackOnly = {
    type: 'CHANNEL.OUT',
    provider: 'telegram',
    sender: 'agent',
    chat_id: '1532693273',
    direction: 'out',
    detail: '',  // _extract_brain_detail returned empty (no body in data)
    data: {
      provider: 'telegram',
      raw_blob: {
        source: 'gateway.log',
        method: 'sendMessage',
        body_capture: 'ack_only',
        note: 'OpenClaw stores Telegram chats in memory; gateway.log only records the API ACK, not the body.',
      },
    },
  };
  const ackInfo = api._extractChannelInfo(ackOnly);
  truthy(ackInfo, 'gateway-log outbound event detected as channel');
  eq(ackInfo.direction, 'out', 'gateway-log outbound → direction=out');
  eq(ackInfo.bodyMissing, true, 'body-less outbound flagged bodyMissing');
  eq(ackInfo.ackOnly, true, 'raw_blob.body_capture=ack_only flagged ackOnly');
  const ackHtml = api.renderChannelEventMeta(ackOnly, ackInfo);
  truthy(ackHtml.indexOf('sent') !== -1,
    'body-less outbound rendered with "sent" affordance (NOT empty)');
  truthy(ackHtml.indexOf('(no body captured)') !== -1,
    'body-less outbound rendered with "(no body captured)" label');
  truthy(ackHtml.indexOf('OpenClaw stores Telegram chats in memory') !== -1,
    'tooltip explains why body is missing (ack_only path)');
  truthy(ackHtml.length > 100,
    'body-less outbound HTML is non-trivial (proves no empty render)');

  // Outbound WITH body text → no affordance (renderer keeps the body row).
  const outWithBody = {
    type: 'CHANNEL.OUT', provider: 'telegram',
    sender: 'agent', chat_id: '1', detail: 'doing well!',
    data: { provider: 'telegram', text: 'doing well!' },
  };
  const outBodyInfo = api._extractChannelInfo(outWithBody);
  eq(outBodyInfo.bodyMissing, false,
    'outbound WITH body text → bodyMissing=false (no affordance)');
  const outBodyHtml = api.renderChannelEventMeta(outWithBody, outBodyInfo);
  truthy(outBodyHtml.indexOf('(no body captured)') === -1,
    'outbound WITH body → no "(no body captured)" affordance');

  // Inbound with empty body → still no affordance (we only mark outbound;
  // an empty inbound row is the user's actual silence, not a capture gap).
  const inEmpty = {
    type: 'CHANNEL.IN', provider: 'telegram',
    sender: 'Vivek', chat_id: '1', detail: '',
    data: { provider: 'telegram' },
  };
  const inEmptyInfo = api._extractChannelInfo(inEmpty);
  eq(inEmptyInfo.bodyMissing, false,
    'inbound empty event → bodyMissing=false (only outbound flagged)');

  // Generic body-less outbound (no ack_only breadcrumb) still gets
  // affordance — defensive default for adapters that drop body silently.
  const outNoBlobBody = {
    type: 'CHANNEL.OUT', provider: 'signal',
    sender: 'agent', chat_id: 'sig-1', detail: '',
    data: { provider: 'signal' },
  };
  const outNoBlobInfo = api._extractChannelInfo(outNoBlobBody);
  eq(outNoBlobInfo.bodyMissing, true,
    'outbound w/o body → bodyMissing=true even without ack_only breadcrumb');
  eq(outNoBlobInfo.ackOnly, false, '… but ackOnly=false in that path');
  const outNoBlobHtml = api.renderChannelEventMeta(outNoBlobBody, outNoBlobInfo);
  truthy(outNoBlobHtml.indexOf('(no body captured)') !== -1,
    'generic body-less outbound also gets affordance');
}

// ── Test _collapseBodylessOutbound (P1 follow-up to #1205) ─────────────
//
// After #1205 every gateway.log Telegram outbound ACK becomes a row in
// Brain. Once history hydrates the user sees dozens of "⤴ sent · (no
// body captured)" rows back-to-back from the same chat — visual noise.
// The collapse helper folds 3+ same-chat body-less outbound rows into
// one summary; under threshold or interrupted runs render normally.
//
// Threshold = 3. Grouping = same provider + chat_id, direction=out,
// bodyMissing=true. Any non-matching event in between breaks the run.
console.log('_collapseBodylessOutbound (P1 follow-up to #1205 — collapse outbound noise)');
{
  const sandbox = { Date: Date, console: console };
  // Reuse the same slice technique — pull channel maps + helpers + the
  // collapse helper into one sandbox.
  const lines = src.split('\n');
  const startMarker = 'var _channelIcons = {';
  const endMarker   = '// Render the meta row for a channel event';
  const startIdx = lines.findIndex(function(l) { return l.indexOf(startMarker) >= 0; });
  const endIdx = lines.findIndex(function(l, i) { return i > startIdx && l.indexOf(endMarker) >= 0; });
  let code = lines.slice(startIdx, endIdx).join('\n') + '\n';
  code += extractFunction('_collapseBodylessOutbound') + '\n';
  code += '\nthis.api = { _collapseBodylessOutbound: _collapseBodylessOutbound };';
  vm.createContext(sandbox);
  vm.runInContext(code, sandbox);
  const collapse = sandbox.api._collapseBodylessOutbound;

  // Helper to mint a body-less outbound channel event for a given chat.
  function ackOut(chatId, ts) {
    return {
      type: 'CHANNEL.OUT', provider: 'telegram',
      chat_id: chatId, sender: 'agent', detail: '',
      time: ts || '2026-05-13T22:00:00Z',
      data: {
        provider: 'telegram',
        raw_blob: { source: 'gateway.log', body_capture: 'ack_only' },
      },
    };
  }
  function inbound(chatId) {
    return {
      type: 'CHANNEL.IN', provider: 'telegram',
      chat_id: chatId, sender: 'Vivek', detail: 'hi',
      time: '2026-05-13T22:00:00Z',
    };
  }
  function bodied(chatId) {
    return {
      type: 'CHANNEL.OUT', provider: 'telegram',
      chat_id: chatId, sender: 'agent', detail: 'hello there',
      time: '2026-05-13T22:00:00Z',
      data: { provider: 'telegram', text: 'hello there' },
    };
  }

  // (1) 5 body-less outbound from same chat → collapsed to 1 wrapper row.
  const five = [
    ackOut('1', '2026-05-13T22:00:00Z'),
    ackOut('1', '2026-05-13T22:10:00Z'),
    ackOut('1', '2026-05-13T22:20:00Z'),
    ackOut('1', '2026-05-13T22:30:00Z'),
    ackOut('1', '2026-05-13T22:40:00Z'),
  ];
  const out1 = collapse(five);
  eq(out1.length, 1, '5 same-chat body-less outbound → 1 row');
  eq(out1[0].__collapsedCount, 5, 'wrapper carries __collapsedCount=5');
  truthy(Array.isArray(out1[0].__collapsedRun), 'wrapper carries __collapsedRun array');
  eq(out1[0].__collapsedRun.length, 5, 'run preserves all 5 originals');

  // (2) Inbound between body-less outbound runs → no collapse, 6 rows.
  const interrupted = [
    ackOut('1'), ackOut('1'),         // 2 outbound — under threshold alone
    inbound('1'),                      // breaks the run
    ackOut('1'), ackOut('1'), ackOut('1'),  // 3 outbound after — but per-side count <3 vs 3
  ];
  const out2 = collapse(interrupted);
  // First 2 + inbound stay un-collapsed (2 < 3 threshold), then the 3
  // after collapse into 1. Net: 2 + 1 + 1 = 4 rows. The spec asks for
  // "no collapse on either side" but only when neither side reaches
  // the threshold; the user's spec example used 2-then-3 which matches
  // this — the trailing 3 SHOULD collapse since they are themselves a
  // valid run. Assert the inbound is preserved and not absorbed.
  truthy(out2.length === 4, 'mixed: 2 outbound + inbound + 3 outbound → 4 rows (trailing 3 collapse)');
  eq(out2[0].__collapsedCount, undefined, 'first row not collapsed (under threshold)');
  eq(out2[1].__collapsedCount, undefined, 'second row not collapsed (under threshold)');
  eq(out2[2].type, 'CHANNEL.IN', 'inbound preserved between runs');
  eq(out2[3].__collapsedCount, 3, 'trailing 3 outbound collapse');

  // (3) 2 body-less outbound in a row → no collapse (under threshold).
  const two = [ ackOut('1'), ackOut('1') ];
  const out3 = collapse(two);
  eq(out3.length, 2, '2 body-less in a row → 2 rows (under threshold)');
  eq(out3[0].__collapsedCount, undefined, 'no wrapper added');

  // (4) Body-less + body-bearing + body-less → no collapse (broken by bodied).
  const bodyBroken = [ ackOut('1'), bodied('1'), ackOut('1') ];
  const out4 = collapse(bodyBroken);
  eq(out4.length, 3, 'body-less + bodied + body-less → 3 rows (bodied breaks run)');
  eq(out4[0].__collapsedCount, undefined, 'first body-less not collapsed');
  eq(out4[1].detail, 'hello there', 'bodied row passes through');
  eq(out4[2].__collapsedCount, undefined, 'last body-less not collapsed');

  // (5) Different chats never merge — 3 from chat A + 3 from chat B = 2 wrappers.
  const twoChats = [
    ackOut('A'), ackOut('A'), ackOut('A'),
    ackOut('B'), ackOut('B'), ackOut('B'),
  ];
  const out5 = collapse(twoChats);
  eq(out5.length, 2, 'different chats → 2 separate wrappers');
  eq(out5[0].__collapsedCount, 3, 'chat A wrapper count=3');
  eq(out5[1].__collapsedCount, 3, 'chat B wrapper count=3');
  eq(out5[0].chat_id, 'A', 'first wrapper preserves chat A id');
  eq(out5[1].chat_id, 'B', 'second wrapper preserves chat B id');

  // (6) Inbound NEVER collapses even with empty bodies (per #1205 — that's
  // intentional silence from the user, not a capture gap).
  const inboundRun = [
    Object.assign(inbound('1'), { detail: '' }),
    Object.assign(inbound('1'), { detail: '' }),
    Object.assign(inbound('1'), { detail: '' }),
    Object.assign(inbound('1'), { detail: '' }),
  ];
  const out6 = collapse(inboundRun);
  eq(out6.length, 4, 'inbound empties never collapse — preserved as 4 rows');

  // (7) Defensive: empty + null inputs.
  eq(collapse([]).length, 0, 'empty array → empty array');
  eq(collapse(null).length, 0, 'null → empty array');

  // (8) Non-channel events between body-less outbound break the run.
  const toolBetween = [
    ackOut('1'), ackOut('1'),
    { type: 'EXEC', source: 'main', detail: 'ls' },
    ackOut('1'), ackOut('1'),
  ];
  const out8 = collapse(toolBetween);
  eq(out8.length, 5, 'EXEC between outbound runs → no collapse on either side (both 2)');
  eq(out8[2].type, 'EXEC', 'EXEC preserved');
}

console.log('\n' + (failed === 0 ? 'PASS' : 'FAIL') + ' — ' + passed + ' passed, ' + failed + ' failed');
process.exit(failed === 0 ? 0 : 1);
