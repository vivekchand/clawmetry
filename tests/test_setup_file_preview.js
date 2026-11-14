// Run with node --test tests/test_setup_file_preview.js (no npm dependencies).
const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');

function context() {
  const sandbox = { window: {}, setTimeout, clearTimeout, AbortController,
    document: { querySelectorAll: () => [] } };
  vm.createContext(sandbox);
  vm.runInContext(fs.readFileSync(path.join(__dirname, '../clawmetry/static/js/setup.js'), 'utf8'), sandbox);
  return sandbox;
}

function host() {
  return { innerHTML: '', contains: function() { return true; }, querySelector() {
    return { addEventListener: (name, fn) => { this.onImageError = fn; } };
  } };
}

test('image is an img with original download, never decoded text', () => {
  const c = context(); const h = host();
  c._cmSetupMountPreview(h, {preview_type:'image', data_url:'data:image/png;base64,iVBORw==', content:'garbled', size:4}, 'assets/icon.png');
  assert.match(h.innerHTML, /<img src="data:image\/png;base64,iVBORw=="/);
  assert.match(h.innerHTML, /download="icon.png"/);
  assert.doesNotMatch(h.innerHTML, /garbled|<pre/);
  h.onImageError();
  assert.match(h.innerHTML, /could not be displayed/);
});

test('late image errors cannot overwrite a newly selected preview', () => {
  const c = context(); const h = host();
  c._cmSetupMountPreview(h, {preview_type:'image', data_url:'data:image/png;base64,iVBORw=='}, 'old.png');
  const oldError = h.onImageError;
  c._cmSetupMountPreview(h, {content:'new selection'}, 'new.md');
  h.contains = () => false;
  oldError();
  assert.match(h.innerHTML, /new selection/);
  assert.doesNotMatch(h.innerHTML, /could not be displayed/);
});

test('hosted PNG and SVG show an honest fallback without fetching or injecting bytes', async () => {
  const c = context(); const h = host();
  c.window.CLOUD_MODE = true;
  c._cmSetupState.identity = c._cmSetupIdentity();
  c.document.getElementById = () => h;
  c._cmSetupState.selectedRuntime = 'test';
  c._cmSetupFetch = () => { throw new Error('Hosted files must use the decrypted inventory'); };
  for (const group of [
    {root:'/skills', files:[{path:'icon.png', content_available:false}]},
    {root:'/skills/icon.svg', label:'Logo', files:[{path:'', content:'<svg onload="alert(1)"></svg>'}]},
  ]) {
    c._cmSetupState.selectedGroups = [group];
    await c.setupOpenFile(0, 0);
    assert.match(h.innerHTML, /agent machine/);
    assert.doesNotMatch(h.innerHTML, /<pre|<svg|onload=|<img/);
  }
});

test('binary and older-server image payloads never show replacement text', () => {
  const c = context();
  for (const [name, data] of [
    ['archive.zip', {binary:true, content:'garbled'}],
    ['icon.svg', {content:'<svg onload="alert(1)"></svg>'}],
    ['icon.png', {binary:true, content:'garbled'}],
    ['large.png', {preview_type:'image', truncated:true}],
  ]) {
    const h = host(); c._cmSetupMountPreview(h, data, name);
    assert.doesNotMatch(h.innerHTML, /<pre|garbled|<svg|<img/);
    assert.match(h.innerHTML, /preview|Preview/);
  }
});

test('text is escaped and untrusted image sources are rejected', () => {
  const c = context(); const h = host();
  c._cmSetupMountPreview(h, {content:'<script>alert(1)</script>', truncated:true}, 'README.md');
  assert.match(h.innerHTML, /&lt;script&gt;/);
  assert.match(h.innerHTML, /Showing the beginning/);
  for (const source of ['https://example.com/track.png', 'javascript:alert(1)', 'data:text/html;base64,abcd']) {
    c._cmSetupMountPreview(h, {preview_type:'image', data_url:source}, 'asset.png');
    assert.doesNotMatch(h.innerHTML, /<img|href=/);
  }
});

test('a slow earlier response cannot replace the selected file', async () => {
  const c = context(); const h = host(); let finishFirst;
  c.document.getElementById = () => h;
  c._cmSetupState.selectedRuntime = 'test';
  c._cmSetupState.selectedGroups = [{root:'/skills', files:[{path:'slow.md'}, {path:'fast.md'}]}];
  c._cmSetupFetch = (url) => url.includes('slow.md')
    ? new Promise(resolve => { finishFirst = resolve; })
    : Promise.resolve({ok:true, json:async () => ({content:'new selection'})});
  const first = c.setupOpenFile(0, 0);
  await c.setupOpenFile(0, 1);
  finishFirst({ok:true, json:async () => ({content:'old selection'})});
  await first;
  assert.match(h.innerHTML, /new selection/);
  assert.doesNotMatch(h.innerHTML, /old selection/);
});

test('Memory and Skills use the same image preview', async () => {
  const c = context(); const h = host();
  const app = fs.readFileSync(path.join(__dirname, '../clawmetry/static/js/app.js'), 'utf8');
  const start = app.indexOf('async function cmRuntimeOpenFile(');
  const end = app.indexOf('// Hook into tab switches', start);
  vm.runInContext(app.slice(start, end), c);
  c.cmFileViewerPlaceholder = () => {};
  c.cmFileViewerOpen = () => { throw new Error('Images must not use the text viewer'); };
  c.document.getElementById = () => h;
  c.fetch = async () => ({ok:true, json:async () => ({binary:true, preview_type:'image', data_url:'data:image/png;base64,iVBORw=='})});
  const container = {_cmRuntimePayload:{groups:[{root:'/skills',files:[{path:'icon.png'}]}]}, getAttribute:()=> 'skills', querySelectorAll:()=> []};
  await c.cmRuntimeOpenFile({closest:()=>container, style:{}}, 0, 0);
  assert.match(h.innerHTML, /<img src=/);
});
