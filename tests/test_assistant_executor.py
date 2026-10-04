"""One node executor, final persistence and retries.

Covers AC-ASSIST-007.1, AC-ASSIST-007.2, AC-ASSIST-007.3,
AC-ASSIST-007.4, AC-ASSIST-007.6 and AC-ASSIST-007.8.
"""
import json
import threading
import time
import uuid

import pytest
from flask import Flask

from clawmetry import assistant_executor as execution, assistant_service as service
from clawmetry import assistant_http
from routes.assistant import bp_assistant
from routes.dashboards import bp_dashboards


@pytest.fixture
def stack(tmp_path, monkeypatch):
    from clawmetry import local_store
    monkeypatch.setattr(local_store, 'DB_PATH', tmp_path/'assistant.duckdb')
    store = local_store.LocalStore()
    executor = execution.Executor(store, 'node-test')
    monkeypatch.setattr(execution, '_executor', executor)
    monkeypatch.setattr(service, '_egress_suppressed', lambda: False)
    monkeypatch.setattr(service, '_provider', lambda *a: ('anthropic', 'sk-test-only-credential'))
    monkeypatch.setattr(service, '_planner_system', lambda store: service._PLAN)
    monkeypatch.setattr(service, '_managed_status', lambda window, **kw: {'available': False})
    monkeypatch.setattr(assistant_http, 'rpc', lambda method, **kwargs: getattr(store, method)(**kwargs))
    app=Flask(__name__)
    app.register_blueprint(bp_assistant)
    app.register_blueprint(bp_dashboards)
    yield executor, app.test_client(), store
    for job in executor.jobs.values():
        job.abort()
        if job.worker:
            job.worker.join(3)
    store.stop(flush=False)


def wait(executor, rid):
    deadline=time.monotonic()+4
    while time.monotonic()<deadline:
        data=executor.read(request_id=rid, renew=True)
        if data.get('terminal'):
            return data
        time.sleep(.01)
    pytest.fail('job did not complete')


def generator(monkeypatch, started=None, finish=None):
    calls=[]
    def generate(mode, credential, system, prompt, **kwargs):
        calls.append(system)
        if system.startswith(service._PLAN):
            return json.dumps({'queries':[{'title':'Sessions','sql':'SELECT count(*) AS n FROM sessions','visual':True,'chart_type':'number','y':'n'}]})
        if kwargs.get('on_text'):
            kwargs['on_text']('No sessions ')
        if started:
            started.set()
        if finish:
            assert finish.wait(3)
        if kwargs.get('on_text'):
            kwargs['on_text']('are recorded.')
        return 'No sessions are recorded.'
    monkeypatch.setattr(service.assistant_providers, 'generate', generate)
    return calls


def test_http_json_and_stream_share_persisted_result(stack, monkeypatch):
    executor, client, store=stack
    calls=generator(monkeypatch)
    plain=client.post('/api/assistant/chat',json={'message':'Count'})
    assert plain.status_code==200, plain.get_json()
    data=plain.get_json()
    stored=store.query_assistant_conversation(conversation_id=data['conversation_id'])
    assert stored['messages'][-1]['content']==data['answer']
    response=client.post('/api/assistant/chat',json={'message':'Count','stream':True})
    text=response.get_data(as_text=True)
    assert 'event: delta' in text and 'event: done' in text
    assert len(calls)==4


def test_actual_delta_before_complete_and_no_early_history(stack, monkeypatch):
    executor, client, store=stack
    started, finish=threading.Event(),threading.Event()
    generator(monkeypatch,started,finish)
    rid=uuid.uuid4().hex
    assert executor.start(request_id=rid,operation='chat',payload={'message':'Count','stream':True})['http_status']==202
    assert started.wait(2)
    try:
        deadline=time.monotonic()+1
        while time.monotonic()<deadline:
            data=executor.read(request_id=rid)
            if any(e['event']=='delta' for e in data['events']):break
            time.sleep(.01)
        assert any(e['event']=='delta' for e in data['events'])
        assert not data['terminal']
        assert store.query_assistant_conversation(conversation_id=rid)=={}
    finally:finish.set()
    assert wait(executor,rid)['events'][-1]['event']=='done'


def test_same_request_never_repeats_inference_or_save(stack,monkeypatch):
    executor,client,store=stack
    calls=generator(monkeypatch)
    rid=uuid.uuid4().hex
    payload={'message':'Count','stream':True}
    assert executor.start(request_id=rid,operation='chat',payload=dict(payload))['http_status']==202
    first=wait(executor,rid)
    assert executor.start(request_id=rid,operation='chat',payload=dict(payload))['http_status']==202
    assert executor.read(request_id=rid)==first and len(calls)==2
    assert executor.start(request_id=rid,operation='chat',payload={'message':'Changed'})['http_status']==409
    assert len(store.query_assistant_conversations())==1


def test_local_and_remote_share_two_slots_until_cancelled_producer_exits(stack,monkeypatch):
    executor,client,store=stack
    entered,finish=threading.Event(),threading.Event()
    def blocked(*a,**kw):
        entered.set();assert finish.wait(3);return json.dumps({'answer':'Late'})
    monkeypatch.setattr(service.assistant_providers,'generate',blocked)
    rid=uuid.uuid4().hex
    executor.start(request_id=rid,operation='chat',payload={'message':'Remote'})
    assert entered.wait(1)
    local=client.post('/api/assistant/chat',json={'message':'Local','stream':True})
    try:
        busy=client.post('/api/assistant/chat',json={'message':'Third'})
        assert busy.status_code==429
        executor.cancel(request_id=rid)
        assert client.post('/api/assistant/chat',json={'message':'Still third'}).status_code==429
        assert not store.query_assistant_conversations()
    finally:
        local.close();finish.set()
    for job in list(executor.jobs.values()):
        if job.worker:job.worker.join(2)


def test_panel_save_is_durable_idempotent_and_query_guarded(stack):
    executor,client,store=stack
    rid=uuid.uuid4().hex
    payload={'name':'Sessions','question':'Count','sql':'SELECT count(*) AS n FROM sessions','chart_spec':{'chart_type':'number','y':'n'}}
    executor.start(request_id=rid,operation='panel_create',payload=dict(payload))
    data=wait(executor,rid)
    assert data['http_status']==201,data
    panel=data['events'][-1]['data']['panel']
    assert panel['panel_id']=='panel-'+rid
    executor.start(request_id=rid,operation='panel_create',payload=dict(payload))
    assert len(store.query_dashboard_panels())==1
    assert client.get('/api/dashboard/panels/'+panel['panel_id']).get_json()['rows']==[{'n':0}]
    bad=client.post('/api/dashboard/panels',json={**payload,'sql':"SELECT * FROM read_csv('/etc/passwd')"})
    assert bad.status_code==400
    assert len(store.query_dashboard_panels())==1


def test_precommit_overflow_never_saves_answer(stack,monkeypatch):
    executor,client,store=stack
    generator(monkeypatch)
    original=executor.service.execute
    def oversized(*args,**kwargs):
        outcome=original(*args,**kwargs)
        outcome.data['answer']='x'*execution.MAX_JOURNAL_BYTES
        return outcome
    monkeypatch.setattr(executor.service,'execute',oversized)
    response=client.post('/api/assistant/chat',json={'message':'Count','stream':True})
    assert 'event: error' in response.get_data(as_text=True)
    assert not store.query_assistant_conversations()


def test_atomic_receipt_write_failure_rolls_back_conversation(stack,monkeypatch):
    executor,client,store=stack
    generator(monkeypatch)
    connection=store._conn
    class FailCommit:
        def execute(self,sql,*args):
            if 'UPDATE assistant_requests SET state=?' in sql:
                raise RuntimeError('fault injection')
            return connection.execute(sql,*args)
        def __getattr__(self,name):return getattr(connection,name)
    monkeypatch.setattr(store,'_conn',FailCommit())
    response=client.post('/api/assistant/chat',json={'message':'Count'})
    assert response.status_code>=400
    assert not store.query_assistant_conversations()


def test_restart_marks_running_receipt_interrupted_without_reexecution(stack):
    executor,client,store=stack
    rid=uuid.uuid4().hex
    payload={'message':'Before restart'}
    digest=execution.hashlib.sha256(execution.encode({'operation':'chat','payload':payload})).hexdigest()
    executor.receipts.claim(rid,executor.epoch,'chat',digest)
    restarted=execution.Executor(store,'node-test')
    assert restarted.start(request_id=rid,operation='chat',payload=payload)['http_status']==202
    data=restarted.read(request_id=rid)
    assert data['terminal'] and data['http_status']==503
    assert not store.query_assistant_conversations()


def test_absent_daemon_never_opens_store_or_provider(stack,monkeypatch):
    executor,client,store=stack
    monkeypatch.setattr(assistant_http,'rpc',lambda *a,**kw:None)
    monkeypatch.setattr(service,'_provider',lambda *a:pytest.fail('provider called without writer'))
    response=client.post('/api/assistant/chat',json={'message':'Count'})
    assert response.status_code==503


def test_stale_cancel_wins_over_newer_renew(stack):
    executor,client,store=stack
    job=execution.Job(executor,uuid.uuid4().hex,'chat',30,lambda:None,None)
    job.control(8,'renew',int(time.time()*1000)+29000)
    job.control(7,'cancel',int(time.time()*1000)+29000)
    job.control(9,'renew',int(time.time()*1000)+29000)
    assert job.cancelled.is_set()


def test_reads_remain_available_during_two_inferences_and_do_not_fill_receipts(stack, monkeypatch):
    # AC-ASSIST-007.3/.8: Home/history reads do not consume paid admission or
    # durable replay capacity, including a full Home followed by repeated reloads.
    executor, client, store = stack
    from clawmetry import assistant_receipts
    monkeypatch.setattr(assistant_receipts, 'MAX_RECEIPTS', 1)
    executor.receipts.claim(uuid.uuid4().hex, executor.epoch, 'chat', 'occupied')
    executor.slots.acquire(); executor.slots.acquire()
    try:
        for _ in range(140):
            rid = uuid.uuid4().hex
            assert executor.start(request_id=rid, operation='panels_list', payload={})['http_status'] == 202
            assert wait(executor, rid)['http_status'] == 200
        with store._write_lock:
            assert store._conn.execute('SELECT count(*) FROM assistant_requests').fetchone()[0] == 1
        executor._prune()
        assert len(executor.jobs) <= 64
    finally:
        executor.slots.release(); executor.slots.release()


def test_four_light_workers_bounded_and_active_jobs_survive_prune(stack, monkeypatch):
    executor, client, store = stack
    started = threading.Barrier(5)
    finish = threading.Event()
    original = executor.service.execute
    def blocked(*args):
        started.wait(2)
        assert finish.wait(3)
        return original(*args)
    monkeypatch.setattr(executor.service, 'execute', blocked)
    ids = [uuid.uuid4().hex for _ in range(4)]
    try:
        for rid in ids:
            assert executor.start(request_id=rid, operation='panels_list', payload={})['http_status'] == 202
        started.wait(2)
        busy = executor.start(request_id=uuid.uuid4().hex, operation='panels_list', payload={})
        assert busy['http_status'] == 429
        executor._prune()
        assert set(ids) <= executor.jobs.keys()
        # Cancellation cannot free admission while the producer is blocked.
        executor.cancel(request_id=ids[0])
        assert executor.start(request_id=uuid.uuid4().hex, operation='status', payload={})['http_status'] == 429
    finally:
        finish.set()
    for rid in ids:
        wait(executor, rid)


def test_preparation_cannot_extend_authenticated_lease(stack, monkeypatch):
    executor, client, store = stack
    def slow_prepare(*args):
        time.sleep(.06)
        return None
    monkeypatch.setattr(executor.service, 'prepare_chat', slow_prepare)
    monkeypatch.setattr(service.assistant_providers, 'generate', lambda *a, **kw: pytest.fail('expired request inferred'))
    rid = uuid.uuid4().hex
    result = executor.start(request_id=rid, operation='chat', payload={'message': 'Count'}, lease_seconds=.01)
    assert result['http_status'] == 499
    assert rid not in executor.jobs and not executor.conversations
    assert not store.query_assistant_conversations()


def test_cancel_waiting_for_writer_prevents_atomic_commit(stack, monkeypatch):
    # AC-ASSIST-007.6: cancellation stays observable while finalization waits
    # on the existing writer lock; no successful partial conversation survives.
    executor, client, store = stack
    generator(monkeypatch)
    ready, proceed = threading.Event(), threading.Event()
    original = executor.receipts.finish
    def barrier(*args, **kwargs):
        ready.set()
        assert proceed.wait(3)
        return original(*args, **kwargs)
    monkeypatch.setattr(executor.receipts, 'finish', barrier)
    rid = uuid.uuid4().hex
    executor.start(request_id=rid, operation='chat', payload={'message': 'Count'})
    assert ready.wait(2)
    with store._write_lock:
        proceed.set()
        executor.cancel(request_id=rid)
    final = wait(executor, rid)
    assert final['http_status'] == 499
    assert not store.query_assistant_conversations()


def test_fresh_identity_required_before_read_publication(stack, monkeypatch):
    executor, client, store = stack
    allowed = [True]
    original = executor.service.execute
    def rotate(*args):
        value = original(*args)
        allowed[0] = False
        return value
    monkeypatch.setattr(executor.service, 'execute', rotate)
    rid = uuid.uuid4().hex
    executor.start(request_id=rid, operation='panels_list', payload={}, identity=lambda **kw: allowed[0])
    final = wait(executor, rid)
    assert final['http_status'] == 499 and all(e['event'] != 'done' for e in final['events'])
