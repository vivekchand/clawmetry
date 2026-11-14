'use strict';
const fs = require('fs');
const vm = require('vm');
const assert = require('assert');
const app = fs.readFileSync(require('path').join(__dirname, '../clawmetry/static/js/app.js'), 'utf8');
function source(name) {
  const match = app.match(new RegExp('^function ' + name + '\\([^]*?^}', 'm'));
  assert(match, name + ' is present');
  return match[0];
}
const sandbox = {Date, Number};
vm.createContext(sandbox);
vm.runInContext(source('guardEsc') + '\n' + source('guardAgo') + '\n' + source('guardProtectionEvidence'), sandbox);
// AC-GOV-SBG-004.1 AC-GOV-SBG-004.2 AC-GOV-SBG-004.4:
// Old snapshots must not inherit capabilities from current UI defaults.
let html = sandbox.guardProtectionEvidence({});
assert(html.includes('Protection evidence unavailable'));
assert(html.includes('Update this node'));
// Configuration, a recorded denial and available controls do not establish execution.
html = sandbox.guardProtectionEvidence({protection: {schema_version: 1,
  pre_tool: {configuration: {state: 'configured'}, last_decision: {result: 'denied', observed_at: Date.now(), recent: true}},
  containment: {state: 'available'}, isolation: {state: 'configured'},
  node_inspection: {state: 'backlog', last_pass_ms: Date.now()}}});
assert(html.includes('Configured, not verified'));
assert(html.includes('Denial recorded'));
assert(html.includes('outcome unverified'));
assert(html.includes('isolation unverified'));
assert(html.includes('More activity remains to inspect'));
assert(html.includes('all runtimes'));
assert(html.includes('Initial service failure remains a coverage gap'));
assert(!html.includes('pill-ok'));
// AC-GOV-SBG-004.3: untrusted fields cannot become executable markup or a raw record dump.
html = sandbox.guardProtectionEvidence({protection: {schema_version: 1,
  pre_tool: {configuration: {state: '<img src=x onerror=alert(1)>'},
    last_decision: {result: '<script>alert(1)</script>', observed_at: 'invalid', tool_input: 'SECRET'}},
  node_inspection: {state: 'unavailable', last_pass_ms: 'invalid'}}});
assert(html.includes('Inspection unavailable'));
assert(!html.includes('<img'));
assert(!html.includes('<script'));
assert(!html.includes('SECRET'));
// AC-GOV-SBG-002.1/.3 AC-GOV-SBG-004.1: priority receipt processing does not certify pending history.
html = sandbox.guardProtectionEvidence({protection: {schema_version: 1,
  node_inspection: {state: 'partial', backfill_pending: true, priority_processed: 2}}});
assert(html.includes('Newer records were processed while earlier activity remains pending inspection'));
assert(!html.includes('Some activity has no confirmed scope'));
assert(!html.includes('all clear'));
html = sandbox.guardProtectionEvidence({protection: {schema_version: 1,
  node_inspection: {state: 'partial', backfill_pending: true, priority_processed: 0, history_gap: true}}});
assert(html.includes('Earlier activity remains pending inspection'));
assert(html.includes('Earlier activity is unavailable for inspection'));
assert(!html.includes('Newer records were processed'));
html = sandbox.guardProtectionEvidence({protection: {schema_version: 1,
  node_inspection: {state: 'unavailable', backfill_pending: true, priority_processed: 2}}});
assert(html.includes('Inspection unavailable'));
assert(!html.includes('Newer records were processed'));

console.log('PASS protection evidence rendering');
