"""Hosted surfaces must not query the cloud container as if it were a node."""
from pathlib import Path
import shutil
import subprocess

import pytest

ROOT = Path(__file__).parents[1]


def test_hosted_local_surfaces_explain_limit_without_fetching_or_accepting_input():
    if not shutil.which('node'):
        pytest.skip('Node.js is not installed')
    script = r'''
const fs = require('fs'), vm = require('vm'), assert = require('assert');
global.window = global;
window.CLOUD_MODE = true;
const ids = ['page-assistant','cm-assistant-thread','cm-assistant-input',
  'cm-assistant-send','cm-assistant-status-label','cm-assistant-status-message',
  'cm-assistant-setup-title','cm-assistant-setup-description',
  'cm-assistant-data-notice','cm-assistant-history-list','cm-assistant-managed-note',
  'cm-assistant-voice','cm-assistant-new-chat',
  'custom-dashboard-section','custom-dashboard-grid','setup-runtime-grid','improve-list'];
const nodes = Object.fromEntries(ids.map(id => [id, {
  textContent:'', style:{}, childElementCount:1, disabled:false,
  addEventListener(){}, setAttribute(){}, querySelector(){return null},
  classList:{toggle(){}}
}]));
global.document = {readyState:'loading', getElementById:id=>nodes[id]||null,
  addEventListener(){}};
let hits = [];
global.fetch = (url) => {hits.push(url); throw Error('A local endpoint reached the cloud');};
for (const file of ['assistant.js','custom-dashboard.js','setup.js','improve.js'])
  vm.runInThisContext(fs.readFileSync('clawmetry/static/js/'+file,'utf8'));
(async()=>{
  loadAssistantPage();
  await loadCustomDashboardPanels(); await loadSetup(true); await loadImprove();
  assert.deepEqual(hits, []);
  assert.equal(nodes['cm-assistant-send'].disabled,true);
  assert.equal(nodes['cm-assistant-input'].disabled,true);
  assert.equal(nodes['cm-assistant-voice'].disabled,true);
  assert.equal(nodes['cm-assistant-managed-note'].hidden,true);
  for (const id of ['cm-assistant-status-message','cm-assistant-history-list',
    'custom-dashboard-grid','setup-runtime-grid','improve-list']) {
    assert.match(nodes[id].textContent,/computer/);
    assert.doesNotMatch(nodes[id].textContent,/Loading|Scanning|No data/);
  }
})().catch(e=>{console.error(e);process.exitCode=1;});
'''
    result = subprocess.run(['node', '-e', script], cwd=ROOT, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
