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

// ── Test anon auth-fail funnel-loss ping helpers (issue #1365) ─────────
// The bootstrap path must fire a ping ONLY when:
//   - localStorage has no prior token (first-load reject, not session timeout)
//   - /api/auth/check returned {authRequired:true, valid:false}
//   - NOT in the needsSetup branch (separate funnel; not our target)
// And the UA bucketer must squash everything into chrome/safari/firefox/other
// without leaking version numbers / OS strings into analytics cardinality.
console.log('anon auth-fail ping helpers (issue #1365)');
{
  const sandbox = { Date: Date };
  vm.createContext(sandbox);
  const code = extractFunction('_uaClass') + '\n' +
               extractFunction('_shouldPingAuthFailFirstLoad') + '\n' +
               'this.api = { _uaClass: _uaClass, _should: _shouldPingAuthFailFirstLoad };';
  vm.runInContext(code, sandbox);
  const api = sandbox.api;

  // _uaClass buckets.
  // Real Chrome UA on Mac:
  eq(api._uaClass(
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 ' +
    '(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'
  ), 'chrome', 'Mac Chrome → chrome');
  // Real Safari UA (no "Chrome" token, has "Safari").
  eq(api._uaClass(
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 ' +
    '(KHTML, like Gecko) Version/17.4 Safari/605.1.15'
  ), 'safari', 'Mac Safari → safari');
  // Real Firefox UA.
  eq(api._uaClass(
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:125.0) Gecko/20100101 Firefox/125.0'
  ), 'firefox', 'Mac Firefox → firefox');
  // Edge embeds Chrome — must bucket as chrome (close enough; we only
  // want browser-engine cardinality, not vendor).
  eq(api._uaClass(
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 ' +
    '(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 Edg/124.0.0.0'
  ), 'chrome', 'Edge (Chromium) → chrome bucket');
  // curl / scripts / unknowns.
  eq(api._uaClass('curl/8.7.1'), 'other', 'curl → other');
  eq(api._uaClass(''), 'other', 'empty UA → other');
  eq(api._uaClass(null), 'other', 'null UA → other');
  eq(api._uaClass(undefined), 'other', 'undefined UA → other');

  // _shouldPingAuthFailFirstLoad gating matrix.
  const FAIL = { authRequired: true, valid: false };
  const OK = { authRequired: true, valid: true };
  const SETUP = { needsSetup: true, authRequired: true, valid: false };

  // True only for: no stored token AND a fresh auth-fail response.
  eq(api._should(null, FAIL), true, 'no token + auth fail → fire ping');
  eq(api._should('', FAIL), true, 'empty token + auth fail → fire ping');

  // Stored token = session-timeout or rotated token, NOT a fresh-install
  // funnel drop. Polluting the signal would defeat the purpose.
  eq(api._should('cm_abc', FAIL), false,
     'stored token + auth fail → suppress (session timeout, not first-load)');

  // Successful auth must never trigger a ping.
  eq(api._should(null, OK), false, 'no token + auth OK → no ping');
  eq(api._should('cm_abc', OK), false, 'stored token + auth OK → no ping');

  // needsSetup is a separate funnel (gateway not running at all). Don't
  // mix it into the "valid token rejected" signal we're trying to surface.
  eq(api._should(null, SETUP), false, 'needsSetup → suppress (separate funnel)');

  // Defensive: malformed authData must never throw.
  eq(api._should(null, null), false, 'null authData → no ping');
  eq(api._should(null, {}), false, 'empty authData → no ping');
  eq(api._should(null, { authRequired: false }), false,
     'authRequired:false → no ping');
}

// ── Test auth-bootstrap.js — zero-click localhost auto-login (issue #1356) ──
//
// The first IIFE in auth-bootstrap.js owns the "first paint" auth flow:
//   1. Read clawmetry-token from localStorage.
//   2. If empty → fetch /api/auth/detected-token; on a token, stash it and
//      call checkAuth(token).
//   3. If present → call checkAuth(storedToken) directly.
//   4. checkAuth calls /api/auth/check?token=…; on valid, hide the overlay;
//      on invalid, wipe localStorage and show the login overlay.
//
// The whole point of #1356 is that step 2 produces a logged-in dashboard
// without the user typing anything. This test exercises the IIFE in a
// sandbox with stubs for fetch / localStorage / document, then asserts:
//   * /api/auth/detected-token is the FIRST fetch on a fresh session.
//   * Its response token gets persisted to localStorage under
//     'clawmetry-token' (the exact key the fetch shim below reads).
//   * checkAuth then calls /api/auth/check?token=… with the just-fetched
//     value (not the empty stored value), and the login overlay is hidden
//     when /api/auth/check returns {valid:true}.
//   * On detected-token 403/404 (non-localhost peer, no token configured),
//     the bootstrap falls through to the overlay path instead of throwing.
//   * No `location.reload()` is ever called (see
//     feedback_no_reload_in_bootstrap_e2e.md — Playwright dies on reload
//     during page-load bootstrap).
console.log('auth-bootstrap.js zero-click auto-login (issue #1356)');
{
  const BOOTSTRAP_JS = path.join(
    __dirname, '..', 'clawmetry', 'static', 'js', 'auth-bootstrap.js'
  );
  const bootSrc = fs.readFileSync(BOOTSTRAP_JS, 'utf8');

  // Extract just the FIRST IIFE — the one that owns the auto-detect +
  // checkAuth flow. The file also defines clawmetryLogin / clawmetryLogout
  // / fetch-shim / version-badge IIFEs after it, none of which are part of
  // this test's scope.
  const iifeMatch = bootSrc.match(/^\(function\(\)\{[\s\S]*?\n\}\)\(\);/m);
  if (!iifeMatch) throw new Error('could not find bootstrap IIFE in auth-bootstrap.js');
  const iifeSrc = iifeMatch[0];

  // Build a sandbox runner. Each scenario re-builds the sandbox so state
  // (localStorage, fetch-call log, overlay style) starts clean.
  function runBootstrap(opts) {
    const calls = []; // every fetch URL, in order
    const lsStore = Object.assign({}, opts.initialLocalStorage || {});
    const ssStore = {};
    const overlayState = { display: '' };
    const gwOverlayState = { display: '', dataset: {} };
    const gwCloseState = { display: '' };
    const logoutBtnState = { display: 'none' };
    let reloadCount = 0;

    const elements = {
      'login-overlay': { style: overlayState },
      'gw-setup-overlay': { style: gwOverlayState, dataset: gwOverlayState.dataset },
      'gw-setup-close': { style: gwCloseState },
      'logout-btn': { style: logoutBtnState },
    };

    const sandbox = {
      localStorage: {
        getItem: function(k) {
          return Object.prototype.hasOwnProperty.call(lsStore, k) ? lsStore[k] : null;
        },
        setItem: function(k, v) { lsStore[k] = String(v); },
        removeItem: function(k) { delete lsStore[k]; },
      },
      sessionStorage: {
        getItem: function(k) {
          return Object.prototype.hasOwnProperty.call(ssStore, k) ? ssStore[k] : null;
        },
        setItem: function(k, v) { ssStore[k] = String(v); },
        removeItem: function(k) { delete ssStore[k]; },
      },
      document: {
        getElementById: function(id) { return elements[id] || null; },
      },
      window: {
        location: {
          // Defensive: any reload attempt during bootstrap is a bug — the
          // Playwright fixture in tests/e2e/zero-click-auth.mjs crashes
          // with "Execution context was destroyed". We assert reloadCount
          // stays 0 in every scenario.
          reload: function() { reloadCount++; },
        },
      },
      fetch: function(url) {
        calls.push(url);
        return Promise.resolve(opts.fetchHandler(url));
      },
      // Bare-bones Promise / setTimeout pulled from this realm; vm context
      // sandboxes don't auto-inherit globals.
      Promise: Promise,
      setTimeout: setTimeout,
    };
    // `encodeURIComponent` is used inside the IIFE.
    sandbox.encodeURIComponent = encodeURIComponent;

    vm.createContext(sandbox);
    vm.runInContext(iifeSrc, sandbox);

    // The IIFE kicks off async work via Promises. Drain the microtask
    // queue by awaiting a setImmediate-equivalent. Two ticks cover the
    // detected-token → checkAuth → /api/auth/check chain.
    return new Promise(function(resolve) {
      setImmediate(function() {
        setImmediate(function() {
          setImmediate(function() {
            resolve({
              calls: calls,
              lsStore: lsStore,
              ssStore: ssStore,
              overlayDisplay: overlayState.display,
              gwOverlayDisplay: gwOverlayState.display,
              logoutDisplay: logoutBtnState.display,
              reloadCount: reloadCount,
            });
          });
        });
      });
    });
  }

  // ── Scenario A: fresh tab, server has token, /api/auth/check says valid ──
  //
  // This is the happy path that #1356 exists to deliver. The bootstrap
  // MUST hit /api/auth/detected-token first, stash the token, then call
  // /api/auth/check?token=…, and hide the overlay.
  (async function scenarioA() {
    const DETECTED_TOKEN = 'deadbeef'.repeat(6); // 48 hex chars — same shape as a real openclaw token
    const result = await runBootstrap({
      initialLocalStorage: {}, // fresh tab
      fetchHandler: function(url) {
        if (url === '/api/auth/detected-token') {
          return { ok: true, json: function() { return Promise.resolve({ token: DETECTED_TOKEN, source: 'openclaw.json' }); } };
        }
        if (url.indexOf('/api/auth/check') === 0) {
          return { ok: true, json: function() { return Promise.resolve({ authRequired: true, valid: true }); } };
        }
        throw new Error('unexpected fetch: ' + url);
      },
    });

    truthy(result.calls.length >= 1, 'A: at least one fetch fires on boot');
    eq(result.calls[0], '/api/auth/detected-token',
       'A: /api/auth/detected-token is the FIRST fetch on a fresh tab');
    eq(result.lsStore['clawmetry-token'], DETECTED_TOKEN,
       'A: detected token persists into localStorage under clawmetry-token');
    truthy(
      result.calls[1] && result.calls[1].indexOf('/api/auth/check?token=' + DETECTED_TOKEN) === 0,
      'A: /api/auth/check is called with the just-fetched token (not empty)'
    );
    eq(result.overlayDisplay, 'none',
       'A: login overlay is hidden after valid auth — zero clicks needed');
    eq(result.logoutDisplay, '',
       'A: logout button is revealed after successful auth');
    eq(result.reloadCount, 0,
       'A: no location.reload() during bootstrap (E2E-fixture-safe)');
  })();

  // ── Scenario B: detected-token returns 403 (non-localhost) ──
  //
  // The bootstrap MUST NOT throw on a 403. It should fall through and
  // call /api/auth/check with no token, surface the overlay (since
  // /api/auth/check then returns {valid:false}).
  (async function scenarioB() {
    const result = await runBootstrap({
      initialLocalStorage: {},
      fetchHandler: function(url) {
        if (url === '/api/auth/detected-token') {
          return { ok: false, status: 403, json: function() { return Promise.resolve({ error: 'localhost only' }); } };
        }
        if (url.indexOf('/api/auth/check') === 0) {
          return { ok: true, json: function() { return Promise.resolve({ authRequired: true, valid: false }); } };
        }
        throw new Error('unexpected fetch: ' + url);
      },
    });

    eq(result.calls[0], '/api/auth/detected-token',
       'B: detected-token is still attempted (no token in localStorage)');
    truthy(!result.lsStore['clawmetry-token'],
       'B: no token persisted when detected-token returns 403');
    truthy(
      result.calls[1] === '/api/auth/check',
      'B: checkAuth falls through with no token (no ?token= query)'
    );
    eq(result.overlayDisplay, 'flex',
       'B: login overlay is shown when no token can be auto-detected');
    eq(result.reloadCount, 0,
       'B: no location.reload() during bootstrap (E2E-fixture-safe)');
  })();

  // ── Scenario C: detected-token returns 404 (server has no GATEWAY_TOKEN) ──
  //
  // Same as B but exercising the "no token detected" branch. Server should
  // surface needsSetup via /api/auth/check, and the bootstrap must promote
  // the gateway-setup overlay (not the login overlay).
  (async function scenarioC() {
    const result = await runBootstrap({
      initialLocalStorage: {},
      fetchHandler: function(url) {
        if (url === '/api/auth/detected-token') {
          return { ok: false, status: 404, json: function() { return Promise.resolve({ error: 'no token detected' }); } };
        }
        if (url.indexOf('/api/auth/check') === 0) {
          return { ok: true, json: function() { return Promise.resolve({ needsSetup: true, authRequired: true, valid: false }); } };
        }
        throw new Error('unexpected fetch: ' + url);
      },
    });

    eq(result.calls[0], '/api/auth/detected-token',
       'C: detected-token attempted even when server has no token');
    eq(result.overlayDisplay, 'none',
       'C: login overlay is hidden (gateway-setup overlay takes over)');
    eq(result.gwOverlayDisplay, 'flex',
       'C: gateway-setup overlay is shown when needsSetup=true');
    eq(result.reloadCount, 0,
       'C: no location.reload() during bootstrap (E2E-fixture-safe)');
  })();

  // ── Scenario D: stored token already in localStorage — skip auto-detect ──
  //
  // If a token was persisted on a prior visit, bootstrap MUST NOT hit
  // /api/auth/detected-token at all — straight to /api/auth/check.
  // Validates the `if(!stored)` guard.
  (async function scenarioD() {
    const STORED = 'cafebabe'.repeat(6);
    const result = await runBootstrap({
      initialLocalStorage: { 'clawmetry-token': STORED },
      fetchHandler: function(url) {
        if (url.indexOf('/api/auth/check') === 0) {
          return { ok: true, json: function() { return Promise.resolve({ authRequired: true, valid: true }); } };
        }
        // detected-token would be a regression — fail loud.
        return { ok: false, status: 500, json: function() { return Promise.resolve({}); } };
      },
    });

    eq(result.calls[0], '/api/auth/check?token=' + STORED,
       'D: stored token short-circuits detected-token fetch entirely');
    truthy(
      result.calls.indexOf('/api/auth/detected-token') === -1,
      'D: /api/auth/detected-token is NEVER called when localStorage has a token'
    );
    eq(result.overlayDisplay, 'none',
       'D: overlay hidden after stored-token auth succeeds');
    eq(result.reloadCount, 0,
       'D: no location.reload() during bootstrap (E2E-fixture-safe)');
  })();

  // ── Scenario E: detected-token fetch rejects (network error) ──
  //
  // catch() branch must run checkAuth(null), not throw. Same end-state
  // as scenario B from the user's perspective (overlay shows).
  (async function scenarioE() {
    const result = await runBootstrap({
      initialLocalStorage: {},
      fetchHandler: function(url) {
        if (url === '/api/auth/detected-token') {
          return Promise.reject(new Error('network down'));
        }
        if (url.indexOf('/api/auth/check') === 0) {
          return { ok: true, json: function() { return Promise.resolve({ authRequired: true, valid: false }); } };
        }
        throw new Error('unexpected fetch: ' + url);
      },
    });

    eq(result.calls[0], '/api/auth/detected-token',
       'E: detected-token attempted even when fetch will reject');
    truthy(!result.lsStore['clawmetry-token'],
       'E: no token persisted on fetch rejection');
    eq(result.overlayDisplay, 'flex',
       'E: overlay shown when network error prevents auto-detect');
    eq(result.reloadCount, 0,
       'E: no location.reload() during bootstrap (E2E-fixture-safe)');
  })();
}

// ── Per-LLM-call Timeline renderer (issue #568) ─────────────────────────
//
// Pure-function check: renderLlmCallTimeline takes the
// /api/llm-call-timeline payload and returns HTML. We extract the function
// + its two phase dictionaries from app.js, run it through node's vm with
// a stub escHtml, and assert structural properties of the output. No DOM,
// no fetch — just shape.
console.log('renderLlmCallTimeline (issue #568 — per-LLM-call lifecycle bar)');
{
  const sandbox = { Date: Date, console: console };
  const lines = src.split('\n');
  const startMarker = 'var _llmTimelinePhaseColors';
  const endMarker = 'function loadLlmCallTimeline(';
  const startIdx = lines.findIndex(function(l) { return l.indexOf(startMarker) === 0; });
  if (startIdx < 0) throw new Error('start marker not found in app.js');
  const endIdx = lines.findIndex(function(l, i) { return i > startIdx && l.indexOf(endMarker) === 0; });
  if (endIdx < 0) throw new Error('end marker not found in app.js');
  // Slice covers _llmTimelinePhaseColors → _llmTimelinePhaseLabels →
  // _formatTimelineMs → renderLlmCallTimeline. Stops before
  // loadLlmCallTimeline (which uses fetch — we don't need it for this test).
  let code = lines.slice(startIdx, endIdx).join('\n') + '\n';
  // Stub escHtml — the real one lives elsewhere in app.js; pull it in.
  code += extractFunction('escHtml') + '\n';
  code += '\nthis.api = {' +
          '  renderLlmCallTimeline: renderLlmCallTimeline,' +
          '  _formatTimelineMs: _formatTimelineMs,' +
          '  _llmTimelinePhaseColors: _llmTimelinePhaseColors,' +
          '  _llmTimelinePhaseLabels: _llmTimelinePhaseLabels,' +
          '};';
  vm.createContext(sandbox);
  vm.runInContext(code, sandbox);
  const api = sandbox.api;

  // (1) _formatTimelineMs covers ms / s / mNNs branches.
  eq(api._formatTimelineMs(0), '0ms', 'format 0 → "0ms"');
  eq(api._formatTimelineMs(150), '150ms', 'format 150 → "150ms"');
  eq(api._formatTimelineMs(4200), '4.2s', 'format 4200 → "4.2s"');
  eq(api._formatTimelineMs(72500), '1m12s', 'format 72500 → "1m12s"');
  eq(api._formatTimelineMs(null), '', 'format null → "" (safe)');

  // (2) 5-phase reasoning payload renders 5 markers + legend.
  const reasoningPayload = {
    event_id: 'ev-1',
    session_id: 'sess-r',
    model: 'claude-opus-4-7',
    reasoning: true,
    phase_count: 5,
    total_ms: 6750,
    phases: [
      { phase: 'prompt_received',     ts: '2026-05-13T12:00:00Z', ms: 0 },
      { phase: 'reasoning_started',   ts: '2026-05-13T12:00:00.150Z', ms: 150 },
      { phase: 'reasoning_completed', ts: '2026-05-13T12:00:04.350Z', ms: 4350 },
      { phase: 'first_output_token',  ts: null, ms: 5550, estimated: true },
      { phase: 'completion',          ts: '2026-05-13T12:00:06.750Z', ms: 6750, tokens: 240 },
    ],
  };
  const html = api.renderLlmCallTimeline(reasoningPayload);
  truthy(html.indexOf('llm-call-timeline') >= 0, 'wrapper class rendered');
  truthy(html.indexOf('llm-call-timeline-bar') >= 0, 'bar rendered');
  // One marker per phase
  const markerCount = (html.match(/llm-call-timeline-marker/g) || []).length;
  eq(markerCount, 5, '5 markers rendered for reasoning payload');
  // Model + reasoning + total span in the header
  truthy(html.indexOf('claude-opus-4-7') >= 0, 'model name in header');
  truthy(html.indexOf('6.8s') >= 0 || html.indexOf('6.7s') >= 0, 'total span in header');
  truthy(html.indexOf('reasoning') >= 0, 'reasoning flag in header');
  // Estimated marker carries the "*" footnote
  truthy(html.indexOf('*') >= 0, 'estimated phase carries footnote marker');
  truthy(html.indexOf('estimated') >= 0, 'footnote line explains "estimated"');

  // (3) 3-phase non-reasoning payload renders 3 markers and "no reasoning".
  const flatPayload = {
    event_id: 'ev-2',
    session_id: 'sess-nr',
    model: 'claude-haiku-3-5',
    reasoning: false,
    phase_count: 3,
    total_ms: 1200,
    phases: [
      { phase: 'prompt_received',    ts: '2026-05-13T12:10:00Z', ms: 0 },
      { phase: 'first_output_token', ts: null, ms: 840, estimated: true },
      { phase: 'completion',         ts: '2026-05-13T12:10:01.200Z', ms: 1200, tokens: 8 },
    ],
  };
  const html2 = api.renderLlmCallTimeline(flatPayload);
  const markerCount2 = (html2.match(/llm-call-timeline-marker/g) || []).length;
  eq(markerCount2, 3, '3 markers rendered for non-reasoning payload');
  truthy(html2.indexOf('no reasoning') >= 0, '"no reasoning" label in header');
  truthy(html2.indexOf('1.2s') >= 0, 'total span 1.2s in header');

  // (4) Empty / malformed payload → graceful fallback (no throw).
  eq(api.renderLlmCallTimeline(null).indexOf('No timeline data') >= 0, true,
     'null payload → "No timeline data."');
  eq(api.renderLlmCallTimeline({phases: []}).indexOf('No timeline data') >= 0, true,
     'empty phases → "No timeline data."');

  // (5) Marker left% values are positioned proportionally to total_ms.
  // Marker 0 (prompt_received, ms=0) → "left:calc(0.00% - 5px)".
  // Marker 4 (completion, ms=6750) → "left:calc(100.00% - 5px)".
  truthy(html.indexOf('left:calc(0.00% - 5px)') >= 0,
         'first marker positioned at 0%');
  truthy(html.indexOf('left:calc(100.00% - 5px)') >= 0,
         'last marker positioned at 100%');
}

// ── Issue #1616 — Alternatives-considered toggle ──────────────────────
//
// Verifies the alternatives renderer + toggle handler:
//   1. real alternatives payload → renders "Chose X over Y, Z" with
//      no em-dashes (memory: feedback_no_em_dashes_in_user_facing_copy).
//   2. empty alternatives → paints the honest "not available" hint with
//      the #1616 tracking link.
//   3. toggleToolAlternatives wires the data-ta attribute through and
//      flips container.dataset.loaded for re-click collapse.
console.log('tool alternatives toggle (issue #1616)');
{
  // Pull both renderers plus escHtml. The toggle handler is window-scoped
  // and uses document.getElementById, so we stub a minimal DOM.
  const sandbox = {
    Date: Date,
    JSON: JSON,
    console: console,
    document: null,
    window: {},
  };
  let code = extractFunction('escHtml') + '\n';
  code += extractFunction('_renderToolAlternativesPanel') + '\n';
  code += extractFunction('_renderToolAlternativesUnavailable') + '\n';
  // Pull the window.toggleToolAlternatives assignment by line range.
  const lines = src.split('\n');
  const startIdx = lines.findIndex(function(l) {
    return l.indexOf('window.toggleToolAlternatives = function') >= 0;
  });
  if (startIdx < 0) throw new Error('toggleToolAlternatives not found in app.js');
  // The function is short — closing "};" is within the next 20 lines.
  let endIdx = startIdx;
  for (let j = startIdx; j < startIdx + 25; j++) {
    if (lines[j] && lines[j].trim() === '};') { endIdx = j; break; }
  }
  code += lines.slice(startIdx, endIdx + 1).join('\n') + '\n';
  code += '\nthis.api = {' +
          '  panel: _renderToolAlternativesPanel,' +
          '  unavailable: _renderToolAlternativesUnavailable,' +
          '  toggle: window.toggleToolAlternatives,' +
          '};';

  // Minimal stub DOM — single container, ids match what the toggle reads.
  const containers = {};
  sandbox.document = {
    getElementById: function(id) {
      if (!containers[id]) {
        containers[id] = {
          dataset: {},
          innerHTML: '',
        };
      }
      return containers[id];
    },
  };
  vm.createContext(sandbox);
  vm.runInContext(code, sandbox);
  const api = sandbox.api;

  // (1) Real alternatives payload renders chosen-over-rejected line.
  const payload = {
    chosen: 'create_event',
    chosen_score: 0.89,
    source: 'logprobs',
    alternatives: [
      { name: 'send_email', score: 0.05 },
      { name: 'ask_clarification', score: 0.06 },
    ],
  };
  const html = api.panel(payload);
  truthy(html.indexOf('create_event') !== -1, 'panel includes chosen tool name');
  truthy(html.indexOf('send_email') !== -1, 'panel includes rejected alternative');
  truthy(html.indexOf('over') !== -1, 'panel uses "over" phrasing (no em-dash)');
  // Memory: no em-dashes in user-facing copy.
  truthy(html.indexOf('—') === -1, 'panel contains NO em-dash');
  truthy(html.indexOf('logprobs') !== -1, 'panel shows source attribution');

  // (2) Empty alternatives → honest unavailable hint with tracking link.
  const empty = api.unavailable();
  truthy(empty.indexOf('not available') !== -1, 'unavailable hint shown');
  truthy(empty.indexOf('1616') !== -1, 'links to tracking issue #1616');
  truthy(empty.indexOf('—') === -1, 'unavailable hint contains NO em-dash');

  // (3) toggleToolAlternatives reads data-ta attribute and flips loaded.
  const fakeBtn = {
    _attrs: { 'data-ta': JSON.stringify(payload) },
    getAttribute: function(k) { return this._attrs[k] || null; },
  };
  api.toggle(fakeBtn, 'ta-test-1');
  const c = containers['ta-test-1'];
  eq(c.dataset.loaded, '1', 'first toggle → loaded=1');
  truthy(c.innerHTML.indexOf('create_event') !== -1,
         'first toggle → container shows chosen tool');
  // Second click collapses (clears innerHTML, dataset.loaded=0).
  api.toggle(fakeBtn, 'ta-test-1');
  eq(c.dataset.loaded, '0', 'second toggle → loaded=0');
  eq(c.innerHTML, '', 'second toggle → container cleared');

  // (4) Toggle with null payload → renders unavailable hint, not crash.
  const nullBtn = {
    _attrs: { 'data-ta': 'null' },
    getAttribute: function(k) { return this._attrs[k] || null; },
  };
  api.toggle(nullBtn, 'ta-test-2');
  const c2 = containers['ta-test-2'];
  truthy(c2.innerHTML.indexOf('not available') !== -1,
         'null payload → unavailable hint rendered');
}

// ── Runtime filter: _cmRuntimeOf derivation (session-id prefix = runtime) ──
console.log('_cmRuntimeOf (runtime from session-id prefix)');
{
  // Pull the runtime-label map + the deriver. _cmRuntimeOf references the
  // module-level _CM_RT_LABEL, so eval both together.
  const labelSrc = src.match(/var _CM_RT_LABEL = \{[\s\S]*?\};/)[0];
  const fnSrc = extractFunction('_cmRuntimeOf');
  const sandbox = {};
  vm.createContext(sandbox);
  vm.runInContext(labelSrc + '\n' + fnSrc + '\nthis._f = _cmRuntimeOf;', sandbox);
  const rt = sandbox._f;
  eq(rt({ id: 'qwen_code:f9f7f80f-c858' }), 'qwen_code', 'qwen_code: prefix → qwen_code');
  eq(rt({ id: 'claude_code:bfb6be7d' }), 'claude_code', 'claude_code: prefix → claude_code');
  eq(rt({ id: 'codex:019e28c2' }), 'codex', 'codex: prefix → codex');
  eq(rt({ id: 'openclaw:abc' }), 'openclaw', 'openclaw: prefix → openclaw');
  eq(rt({ id: '625c0ad9-71af-4a56' }), 'openclaw', 'bare uuid → openclaw (default)');
  eq(rt({ id: 'clawmetry-selfevolve' }), 'openclaw', 'internal session → openclaw');
  eq(rt({ trace_id: 'qwen_code:x' }), 'openclaw', 'trace_id is NOT read (only id/sessionId/session_id/key)');
  eq(rt({ sessionId: 'goose:20260525_3' }), 'goose', 'sessionId field honoured');
}

// ── Runtime filter: _cmApplyRuntimeScopeNote picks the right scope ─────────
console.log('_cmApplyRuntimeScopeNote (honest note on aggregate / node-wide tabs)');
{
  const maps = src.match(/var _CM_RT_AGGREGATE = \{[\s\S]*?\};/)[0]
    + '\n' + src.match(/var _CM_RT_NODEWIDE = \{[\s\S]*?\};/)[0]
    + '\n' + src.match(/var _CM_RT_LABEL = \{[\s\S]*?\};/)[0];
  const fnSrc = extractFunction('_cmApplyRuntimeScopeNote');
  let filterVal = 'qwen_code';
  function makePage() {
    let kids = [];
    const page = {
      _html: '',
      querySelector: function(sel) { return this._note || null; },
      insertAdjacentHTML: function(pos, html) { this._html = html; this._note = { outerHTML: html, parentNode: this }; },
    };
    return page;
  }
  let thePage = null;
  const sandbox = {
    document: { getElementById: function(id) { return id === 'page-models' || id === 'page-crons' || id === 'page-tracing' ? (thePage = thePage || makePage()) : null; } },
    escHtml: function(s) { return String(s); },
    _cmRuntimeFilter: function() { return filterVal; },
    _cmRuntimeLabel: function(rt) { return ({ qwen_code: 'Qwen Code' })[rt] || rt; },
  };
  vm.createContext(sandbox);
  vm.runInContext(maps + '\n' + fnSrc + '\nthis._note = _cmApplyRuntimeScopeNote;', sandbox);

  // aggregate tab (models) → "all runtimes" note mentioning the runtime
  thePage = null; sandbox.document.getElementById = function(id) { return id === 'page-models' ? (thePage = thePage || makePage()) : null; };
  sandbox._note('models');
  truthy(thePage && thePage._html.indexOf('all runtimes') !== -1, 'aggregate tab → "all runtimes" note');
  truthy(thePage._html.indexOf('Qwen Code') !== -1, 'aggregate note names the selected runtime');

  // node-wide tab (crons) → "node-wide" note
  thePage = null; sandbox.document.getElementById = function(id) { return id === 'page-crons' ? (thePage = thePage || makePage()) : null; };
  sandbox._note('crons');
  truthy(thePage && thePage._html.indexOf('node-wide') !== -1, 'node-wide tab → "node-wide" note');

  // filterable tab (tracing) → NO note (it filters itself)
  thePage = null; sandbox.document.getElementById = function(id) { return id === 'page-tracing' ? (thePage = thePage || makePage()) : null; };
  sandbox._note('tracing');
  truthy(thePage && thePage._html === '', 'filterable tab → no scope note');

  // filter === 'all' → never a note even on aggregate tab
  filterVal = 'all'; thePage = null;
  sandbox.document.getElementById = function(id) { return id === 'page-models' ? (thePage = thePage || makePage()) : null; };
  sandbox._note('models');
  truthy(thePage && thePage._html === '', 'all-runtimes selected → no note');
}

// Auth-bootstrap scenarios above are async — wait for the microtask /
// macrotask queue to drain before printing the summary. (The previous
// synchronous test blocks all completed in-tick, so no wait was needed
// for them; ordering still holds.) Four setImmediate hops cover the
// detected-token → checkAuth → /api/auth/check chain inside each
// scenario's runBootstrap helper plus a buffer tick.
setImmediate(function() {
  setImmediate(function() {
    setImmediate(function() {
      setImmediate(function() {
        console.log('\n' + (failed === 0 ? 'PASS' : 'FAIL') + ' — ' + passed + ' passed, ' + failed + ' failed');
        process.exit(failed === 0 ? 0 : 1);
      });
    });
  });
});
