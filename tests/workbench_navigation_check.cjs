const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');
const source = fs.readFileSync(path.join(__dirname, '../clawmetry/static/js/app.js'), 'utf8').split('// Optional private-package views.')[1];
function check(cloud) {
  const nodes = new Map();
  const element = () => ({children: [], attrs: {}, appendChild(el) {this.children.push(el); if (el.id) nodes.set(el.id, el);}, insertBefore(el) {this.appendChild(el);}, setAttribute(k, v) {this.attrs[k] = v;}});
  const top = element(), runtime = element(); runtime.parentNode = top; nodes.set('cm-global-runtime-wrap', runtime);
  const context = {CLOUD_MODE: cloud, CLOUD_NODE_ID: 'selected-node', document: {querySelector: () => top, getElementById: id => nodes.get(id), createElement: element, addEventListener() {}}};
  context.window = context; vm.runInNewContext('// Optional private-package views.' + source, context);
  context.cmInstallWorkbenchNavigation([{view_group: 'physical_ai', href: 'https://untrusted.test'}, {view_group: 'physical_ai', href: '//untrusted'}]);
  assert.equal(top.children.length, 0);
  context.cmInstallWorkbenchNavigation([]); assert.equal(top.children.length, 0, 'no paid view without plugin advertisement');
  const entry = {view_group: 'physical_ai', href: cloud ? '/cloud/node/selected-node/robotics' : '/robotics'};
  context.cmInstallWorkbenchNavigation([entry, entry]);
  const group = nodes.get('cm-ai-view-switch'); assert(group); assert.equal(top.children.length, 1, 'deduplicate snapshots');
  assert.equal(group.children[0].textContent, 'Digital AI'); assert.equal(group.children[0].attrs['aria-current'], 'page');
  assert.equal(group.children[0].href, cloud ? '/cloud/node/selected-node' : '/');
  assert.equal(group.children[1].textContent, 'Physical AI'); assert.equal(group.children[1].href, entry.href);
}
check(false); check(true);
console.log('Local and cloud workbench navigation, node scope, entitlement advertisement, and URL validation passed.');
