"""AC-GOV-SBG-001.1/.3: exact grants stay visible and revocable.

Execute the shipped vanilla-JS template with isolated DOM/network stubs.
No browser service, live account or action is used.
"""
import json
from pathlib import Path
import shutil
import subprocess

import pytest


@pytest.mark.parametrize("cloud", [True, False])
def test_exact_and_manual_grants_can_be_seen_and_removed(cloud):
    node = shutil.which("node")
    if not node:
        pytest.skip("node is required for approval management JavaScript behavior")
    template = (Path(__file__).parents[1] / "clawmetry/templates/tabs/approvals.html").read_text()
    source = template.split("<script>", 1)[1].split("</script>", 1)[0]
    script = r"""
      const assert = require('assert');
      const vm = require('vm');
      const cloud = CLOUD_VALUE;
      const binding = 'v1:' + 'a'.repeat(64);
      const exact = {id:'exact/id',name:'Reviewed <action>',tool:'Write',runtime:'claude_code',action:'approve',pattern:'(?!)',action_binding:binding};
      if(!cloud) {
        exact.match={tool:'Write',action_binding:binding,command_regex:'(?!)'};
        delete exact.tool; delete exact.action_binding; delete exact.pattern;
      }
      const manual = {id:'manual-id',name:'Manual command rule',tool:'Bash',pattern:'^safe$',action:'require_approval'};
      let policies = [exact,manual], requests = [], errors = [], rejectDelete = false, rejectLoad = false;
      const elements = new Map();
      for (const id of ['approvals-custom-rules','approvals-pending-list','approvals-history-list','approvals-pending-count','approvals-updated'])
        elements.set(id,{innerHTML:'',textContent:'',style:{}});
      global.window = global;
      global.CLOUD_MODE = cloud;
      global.CLOUD_TOKEN = cloud ? 'cm_test' : '';
      global.localStorage = {getItem:()=>''};
      global.document = {getElementById:id=>elements.get(id)||null,querySelectorAll:()=>[],addEventListener:()=>{}};
      global.setInterval = ()=>{};
      global.confirm = ()=>true;
      global.alert = value=>errors.push(value);
      global.escHtml = value=>String(value).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
      global.fetch = async (url,options={})=>{
        requests.push({url,options});
        if(options.method==='DELETE') {
          if(rejectDelete) return {ok:false,status:503,json:async()=>({error:'isolated unavailable'})};
          policies=policies.filter(p=>url!==('/api/cloud/policies/'+encodeURIComponent(p.id)));
          return {ok:true,json:async()=>({ok:true})};
        }
        if(options.method==='PUT') {
          policies=JSON.parse(options.body).policies;
          return {ok:true,json:async()=>({ok:true})};
        }
        if(url.startsWith('/api/cloud/policies')) {
          if(rejectLoad) throw new Error('isolated list unavailable');
          const capable=(options.headers||{})['X-ClawMetry-Action-Binding']==='v1';
          return {ok:true,json:async()=>({policies:policies.filter(p=>!p.action_binding||capable)})};
        }
        if(url==='/api/approvals/policies') {
          if(rejectLoad) throw new Error('isolated list unavailable');
          return {ok:true,json:async()=>({policies})};
        }
        return {ok:true,json:async()=>({approvals:[],decisions:[],integrations:[]})};
      };
      global.fetchJsonWithTimeout=async url=>(await fetch(url)).json();
      vm.runInThisContext(SOURCE_VALUE);
      (async()=>{
        await loadApprovalsTab();
        let html=elements.get('approvals-custom-rules').innerHTML;
        assert.ok(html.includes('Reviewed &lt;action&gt;'),'exact grant must render safely');
        assert.ok(html.includes('Manual command rule'),'existing manual grant must remain manageable');
        assert.ok(html.includes('Exact action'),'binding must have a useful label');
        assert.ok(!html.includes('(?!)'),'legacy fallback is not an operator-facing pattern');
        if(cloud) {
          const load=requests.find(r=>r.url.startsWith('/api/cloud/policies'));
          assert.equal(load.options.headers['X-ClawMetry-Action-Binding'],'v1');
          assert.equal(load.options.headers.Authorization,'Bearer cm_test');
          rejectDelete=true;
          await removeCustomRule(0);
          assert.equal(policies.length,2,'failed deletion must retain the grant');
          assert.ok(errors.pop().includes('isolated unavailable'));
          rejectDelete=false;
        }
        await removeCustomRule(0);
        await new Promise(setImmediate);
        assert.deepEqual(policies.map(p=>p.id),['manual-id']);
        if(cloud) {
          const removed=requests.find(r=>r.options.method==='DELETE');
          assert.equal(removed.url,'/api/cloud/policies/exact%2Fid');
          assert.equal(removed.options.headers.Authorization,'Bearer cm_test');
        } else {
          assert.ok(requests.some(r=>r.url==='/api/approvals/policies'&&r.options.method==='PUT'));
        }
        await removeCustomRule(0);
        await new Promise(setImmediate);
        assert.equal(policies.length,0,'manual cloud rules remain removable too');
        rejectLoad=true;
        await loadApprovalsTab();
        assert.ok(elements.get('approvals-custom-rules').textContent.includes('Rules unavailable'));
      })().catch(error=>{console.error(error);process.exit(1);});
    """.replace("CLOUD_VALUE", json.dumps(cloud)).replace("SOURCE_VALUE", json.dumps(source))
    result = subprocess.run([node], input=script, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
