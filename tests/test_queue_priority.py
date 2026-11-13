"""Execute queue recovery shell with paged GitHub fixtures, never GitHub writes."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
QUEUE = yaml.load((ROOT / '.github/workflows/queue-priority.yml').read_text(), Loader=yaml.BaseLoader)
RECORD = 'PR cites the product record that justified it'


def step(job, index=0):
    return QUEUE['jobs'][job]['steps'][index]['run']


@pytest.fixture
def queue_shell(tmp_path):
    assert shutil.which('jq'), 'Queue workflow requires jq, supplied by its Ubuntu runner'
    gh = tmp_path / 'gh'
    gh.write_text('#!' + sys.executable + '\n' + '''
import json, os, subprocess, sys
args=sys.argv[1:]
path=next(a for a in args if a.startswith('/repos/'))
with open(os.environ['TRACE'], 'a') as out:out.write(json.dumps(args)+'\\n')
data=json.load(open(os.environ['FIXTURE']))
if any(piece in path for piece in data.get('fail', [])):sys.exit(1)
if '-X' in args:sys.exit(0)
if '/pulls?' in path:key='pulls'
elif '/check-runs?' in path:key='checks'
elif 'status=queued' in path:key='queued'
elif 'branch=main' in path:key='main'
else:key='runs'
pages=data[key]
if '--paginate' not in args:pages=pages[:1]
value=pages if '--slurp' in args else pages[0]
query=args[args.index('--jq')+1]
sys.exit(subprocess.run(['jq','-r',query],input=json.dumps(value),text=True).returncode)
''')
    gh.chmod(0o755)
    date = tmp_path / 'date'
    date.write_text('#!/bin/sh\necho 2026-11-01T00:00:00Z\n')
    date.chmod(0o755)

    def run(script, data):
        fixture = tmp_path / 'fixture.json'
        fixture.write_text(json.dumps(data))
        trace = tmp_path / 'trace.jsonl'
        trace.write_text('')
        output = tmp_path / 'output'
        output.write_text('')
        env = dict(os.environ, PATH=str(tmp_path) + os.pathsep + os.environ['PATH'],
                   FIXTURE=str(fixture), TRACE=str(trace), REPO='vivekchand/clawmetry',
                   SELF=QUEUE['name'], GITHUB_OUTPUT=str(output))
        result = subprocess.run(['bash', '-c', script], env=env, text=True, capture_output=True)
        calls = [json.loads(line) for line in trace.read_text().splitlines()]
        return result, calls, output.read_text()
    return run


def mutations(calls, operation):
    return [next(a for a in call if a.startswith('/repos/')) for call in calls
            if '-X' in call and any(a.endswith('/' + operation) for a in call)]


def test_clear_preserves_record_prerequisite_and_release_across_pages(queue_shell):
    data = {'queued': [{'workflow_runs': [
        {'id': 1, 'head_branch': 'feature', 'name': 'CI'},
        {'id': 2, 'head_branch': 'main', 'name': 'CI'},
        {'id': 3, 'head_branch': 'release', 'name': 'Auto-release on [RELEASE] merge'},
    ]}, {'workflow_runs': [
        {'id': 4, 'head_branch': 'feature', 'name': 'Product record (requirements before code)'},
        {'id': 5, 'head_branch': 'feature', 'name': 'renamed record', 'path': '.github/workflows/product-record-gate.yml'},
        {'id': 6, 'head_branch': 'other', 'name': 'CI'},
    ]}]}
    result, calls, _ = queue_shell(step('clear-queue'), data)
    assert result.returncode == 0, result.stderr
    assert [p.rsplit('/', 2)[1] for p in mutations(calls, 'cancel')] == ['1', '6']


def recovery_data(latest='success'):
    def run(id, workflow, conclusion='cancelled', sha='current', created='2026-11-02T10:00:00Z'):
        return dict(id=id, workflow_id=workflow, conclusion=conclusion, head_sha=sha, created_at=created)
    return {
        'pulls': [[{'number': 10, 'head': {'repo': {'full_name': 'outsider/fork'}, 'ref': 'fork', 'sha': 'fork'}}],
                  [{'number': 11, 'head': {'repo': {'full_name': 'vivekchand/clawmetry'}, 'ref': 'feature/a', 'sha': 'current'}}]],
        'checks': [{'check_runs': [{'id': 2, 'name': RECORD, 'conclusion': 'success'}]},
                   {'check_runs': [{'id': 100, 'name': RECORD, 'conclusion': latest}]}],
        'runs': [{'workflow_runs': [run(1, 1), run(2, 2)]}, {'workflow_runs': [
            run(3, 1, 'success', created='2026-11-02T11:00:00Z'),
            run(4, 3, sha='old'), run(5, 4, created='2026-10-30T10:00:00Z'),
        ]}],
    }


def test_recovery_uses_all_pages_latest_checks_and_exact_head(queue_shell):
    result, calls, _ = queue_shell(step('requeue', 1), recovery_data())
    assert result.returncode == 0, result.stderr
    assert mutations(calls, 'rerun') == ['/repos/vivekchand/clawmetry/actions/runs/2/rerun']
    assert any('branch=feature%2Fa' in arg for call in calls for arg in call)
    assert not any('/commits/fork/' in arg for call in calls for arg in call)


@pytest.mark.parametrize('latest', ['failure', None])
def test_newer_nonpassing_record_cannot_reuse_old_success(queue_shell, latest):
    result, calls, _ = queue_shell(step('requeue', 1), recovery_data(latest))
    assert result.returncode == 0, result.stderr
    assert not mutations(calls, 'rerun')


def test_main_busy_check_paginates_and_does_not_ignore_late_running_job(queue_shell):
    data = {'main': [{'workflow_runs': [{'name': QUEUE['name'], 'status': 'in_progress'}]},
                     {'workflow_runs': [{'name': 'final validation', 'status': 'in_progress'}]}]}
    result, _, output = queue_shell(step('requeue'), data)
    assert result.returncode == 0, result.stderr
    assert 'idle=false' in output


@pytest.mark.parametrize('api,job,index', [
    ('status=queued', 'clear-queue', 0), ('branch=main', 'requeue', 0),
    ('/pulls?', 'requeue', 1), ('/check-runs?', 'requeue', 1),
    ('event=pull_request', 'requeue', 1), ('/rerun', 'requeue', 1),
])
def test_api_failures_are_visible_and_never_report_idle_success(queue_shell, api, job, index):
    data = recovery_data()
    data['fail'] = [api]
    result, calls, output = queue_shell(step(job, index), data)
    assert result.returncode != 0
    assert 'idle=true' not in output
    if api != '/rerun':
        assert not mutations(calls, 'rerun')


def test_recovery_wakes_for_final_main_or_record_completion_without_self_loop():
    event = QUEUE['on']['workflow_run']
    assert event['workflows'] == ['*', '!Queue priority (main first)']
    assert event['types'] == ['completed']
    assert 'branches' not in event  # A late PR citation check must also wake recovery.
    condition = QUEUE['jobs']['requeue']['if']
    assert "github.event.workflow_run.head_branch == 'main'" in condition
    assert "github.event.workflow_run.name == 'Product record (requirements before code)'" in condition
    assert 'schedule' not in condition
    assert not any('uses' in s for j in QUEUE['jobs'].values() for s in j['steps'])


def test_edited_body_is_validated_before_reusing_same_sha_success(tmp_path):
    workflow = yaml.load((ROOT / '.github/workflows/e2e-gate.yml').read_text(), Loader=yaml.BaseLoader)
    assert 'edited' in workflow['on']['pull_request']['types']
    steps = workflow['jobs']['e2e-gate']['steps']
    validation = next(s for s in steps if s.get('run') == 'python3 scripts/check_product_record.py')
    polling = next(s for s in steps if s.get('run') == 'python3 scripts/e2e_gate.py')
    assert steps.index(validation) < steps.index(polling)
    assert validation['env']['PR_BODY'] == '${{ github.event.pull_request.body }}'
    assert validation['env']['BASE_SHA'] == '${{ github.event.pull_request.base.sha }}'
    assert validation['env']['HEAD_SHA'] == '${{ github.event.pull_request.head.sha }}'
    assert 'if' not in validation and 'continue-on-error' not in validation
    subprocess.run(['git', 'init', '-q', str(tmp_path)], check=True)
    def git(*args):
        return subprocess.check_output(['git', '-c', 'user.name=Test', '-c', 'user.email=test@example.com', *args], cwd=tmp_path, text=True).strip()
    (tmp_path / 'product.py').write_text('before\n')
    git('add', '.'); git('commit', '-qm', 'base')
    base = git('rev-parse', 'HEAD')
    (tmp_path / 'product.py').write_text('after\n')
    git('commit', '-qam', 'candidate')
    env = dict(os.environ, BASE_SHA=base, HEAD_SHA=git('rev-parse', 'HEAD'))
    # Prior success at this same SHA cannot excuse a body edit that removes its citation.
    for body, expected in [('', 1), ('Product record: https://github.com/vivekchand/clawmetry-cloud/issues/123', 0)]:
        result = subprocess.run([sys.executable, str(ROOT / 'scripts/check_product_record.py')],
                                cwd=tmp_path, env=dict(env, PR_BODY=body), capture_output=True)
        assert result.returncode == expected, result.stderr.decode()
