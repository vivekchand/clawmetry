"""Temporary daemon boundary for Assistant route/provider contract tests."""
import time

import pytest

from clawmetry import assistant_executor as execution, assistant_service as service, assistant_http
from routes.assistant import bp_assistant, assistant_chat


@pytest.fixture
def daemon_adapter(tmp_path, monkeypatch):
    from clawmetry import local_store
    monkeypatch.setattr(local_store, 'DB_PATH', tmp_path/'route-daemon.duckdb')
    store=local_store.LocalStore()
    executor=execution.Executor(store, 'test-node')
    monkeypatch.setattr(execution, '_executor', executor)
    monkeypatch.setattr(service, '_store', lambda method, **kw: getattr(store,method)(**kw), raising=False)
    monkeypatch.setattr(service, '_gate', executor.slots, raising=False)
    monkeypatch.setattr(service, '_conversation_lock', executor.lock, raising=False)
    monkeypatch.setattr(service, '_conversations_in_flight', executor.conversations, raising=False)
    monkeypatch.setattr(service, 'bp_assistant', bp_assistant, raising=False)
    monkeypatch.setattr(service, 'assistant_chat', assistant_chat, raising=False)
    monkeypatch.setattr(service, '_planner_system', lambda store: service._PLAN)
    monkeypatch.setattr(service, '_managed_status', lambda window, **kw: {'available':False})
    monkeypatch.setattr(executor.service,'call', lambda method, **kw: service._store(method,**kw))
    monkeypatch.setattr(assistant_http,'rpc',lambda method,**kw:getattr(store,method)(**kw))
    original=executor.receipts.finish
    def finish(rid,outcome,check, **kwargs):
        if outcome.mutation and outcome.mutation.get('kind')=='conversation':
            m=outcome.mutation
            # Preserve existing store-failure spies at the persistence boundary;
            # actual transactional writes are covered by executor/pipeline tests.
            if not service._store('save_assistant_conversation',conversation_id=m['conversation_id'],title=m['title'],messages=m['messages']):
                raise service._ChatFailure('The answer could not be saved. Please retry.',503)
        return original(rid,outcome,check, **kwargs)
    monkeypatch.setattr(executor.receipts,'finish',finish)
    yield executor
    for job in list(executor.jobs.values()):
        job.abort()
        if job.worker and job.worker.ident is not None:job.worker.join(4)
    deadline=time.monotonic()+2
    while executor.conversations and time.monotonic()<deadline:time.sleep(.01)
    store.stop(flush=False)
