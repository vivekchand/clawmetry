"""Contracts for the Blume-inspired Setup and Improve surfaces."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_setup_and_improve_are_reachable_from_the_primary_nav():
    html = (ROOT / "dashboard.py").read_text(encoding="utf-8")
    assert 'data-tab="setup"' in html
    assert 'data-tab="improve"' in html
    assert "tabs/setup.html" in html
    assert "tabs/improve.html" in html
    assert "js/setup.js" in html
    assert "js/improve.js" in html


def test_setup_and_improve_have_live_loaders_and_read_only_copy():
    app = (ROOT / "clawmetry/static/js/app.js").read_text(encoding="utf-8")
    setup = (ROOT / "clawmetry/static/js/setup.js").read_text(encoding="utf-8")
    improve = (ROOT / "clawmetry/static/js/improve.js").read_text(encoding="utf-8")
    assert "name === 'setup'" in app and "loadSetup" in app
    assert "name === 'improve'" in app and "loadImprove" in app
    assert "/api/runtimes/memory-catalog" in setup
    assert "/api/improve/candidates" in improve
    assert "No files change from this view." in (
        ROOT / "clawmetry/templates/tabs/improve.html"
    ).read_text(encoding="utf-8")


def _setup_browser(code):
    """Execute the shipped loader and controls against an encrypted-file adapter."""
    import json
    import subprocess
    source = (ROOT / 'clawmetry/static/js/setup.js').read_text()
    harness = r'''
const assert = require('node:assert/strict');
const nodes = {};
function el(id) {
  return nodes[id] || (nodes[id] = {innerHTML:'', textContent:'', style:{}, children:{},
    querySelector(key){return this.children[key] || (this.children[key]={textContent:''});},
    scrollIntoView(){}, classList:{toggle(){}}, getAttribute(){return null;}});
}
global.document={getElementById:el, querySelectorAll(){return [];}};
global.window=global;
window.CLOUD_MODE=true;
let scope='all', calls=0;
function _cmRuntimeFilter(){return scope;}
function _cmRuntimeLabel(id){return id;}
global.fetch=async()=>{throw Error('cloud must not read local filesystem APIs');};
const groups=[
 {runtime:'claude_code',runtime_label:'Claude Code',category:'memory',scope:'project',root:'/project',exists:true,files:[{path:'CLAUDE.md',content:'<script>bad()</script>',content_available:true}]},
 {runtime:'claude_code',runtime_label:'Claude Code',category:'skills',scope:'global',root:'/skills',exists:true,files:[{path:'a/SKILL.md',content:'Skill',content_available:true}]},
 {runtime:'codex',runtime_label:'Codex',category:'memory',scope:'project',root:'/repo',exists:true,files:[{path:'AGENTS.md',content:'',content_available:false}]}
];
window._cmCloudRuntimeFiles=async()=>{calls++;return {groups};};
'''
    run = subprocess.run(['node', '-e', harness + source + '\n(async()=>{' + code + '\n})().catch(e=>{console.error(e);process.exit(1);});'], capture_output=True, text=True, timeout=15)
    assert run.returncode == 0, run.stderr


def test_hosted_setup_reads_synced_inventory_and_escaped_content():
    """AC-ASSIST-006.1: cloud Setup uses the already encrypted file inventory."""
    _setup_browser(r'''
await loadSetup();
assert.equal(el('setup-summary-files').textContent,'3');
assert.equal(el('setup-summary-runtimes').textContent,'2');
assert.match(el('setup-runtime-grid').innerHTML,/Claude Code/);
assert.match(el('setup-source-note').textContent,/Synced setup files/);
await setupSelectRuntime('claude_code');
await setupOpenFile(0,0);
assert.match(el('setup-file-preview').innerHTML,/&lt;script&gt;/);
assert.equal(calls,1);
setupSetKind('skills');
await setupSelectRuntime('claude_code');
assert.equal(_cmSetupState.selectedGroups.length,1);
assert.equal(_cmSetupState.selectedGroups[0].category,'skills');
assert.equal(calls,1);
''')


def test_setup_runtime_switch_and_missing_content_are_honest():
    """AC-ASSIST-006.3: a new scope cannot retain old files or invent empty content."""
    _setup_browser(r'''
await loadSetup();
await setupSelectRuntime('claude_code');
scope='codex'; await loadSetup();
assert.equal(el('setup-summary-files').textContent,'1');
assert.equal(el('setup-files-panel').style.display,'none');
assert.doesNotMatch(el('setup-runtime-grid').innerHTML,/Claude Code/);
await setupSelectRuntime('codex'); await setupOpenFile(0,0);
assert.match(el('setup-file-preview').textContent,/contents have not been synced/);
setupSetKind('hooks');
assert.match(el('setup-empty').querySelector('span').textContent,/credentials/);
''')


def test_setup_pending_missing_key_and_failure_never_become_zero():
    _setup_browser(r'''
for (const data of [{pending:true,node_online:false},{pending:true,node_online:true},{needkey:true}]) {
 window._cmCloudRuntimeFiles=async()=>data;
 await loadSetup(true);
 assert.equal(el('setup-summary-files').textContent,'Unavailable');
 assert.equal(_cmSetupState.catalog,null);
 assert.equal(el('setup-empty').style.display,'none');
}
window._cmCloudRuntimeFiles=async()=>{throw Error('private internal error');};
await loadSetup(true);
assert.doesNotMatch(el('setup-runtime-grid').textContent,/private internal/);
assert.equal(el('setup-summary-files').textContent,'Unavailable');
''')


def test_setup_discards_a_slow_previous_scope_response():
    _setup_browser(r'''
let release;
window._cmCloudRuntimeFiles=()=>new Promise(r=>{release=r;});
const old=loadSetup();
scope='codex';
window._cmCloudRuntimeFiles=async()=>({groups});
await loadSetup();
release({needkey:true}); await old;
assert.equal(el('setup-summary-files').textContent,'1');
assert.equal(_cmSetupState.catalog.runtimes.length,2);
''')
