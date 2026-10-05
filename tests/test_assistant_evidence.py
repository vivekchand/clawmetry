"""Real DuckDB regressions for scoped Assistant session evidence.

AC-ASSIST-008.1
AC-ASSIST-008.2
AC-ASSIST-008.3
AC-ASSIST-008.6
"""
from __future__ import annotations

import json
import threading
import time

import duckdb
import pytest

from clawmetry import assistant_evidence as evidence
from clawmetry.assistant_stream import Cancelled
from clawmetry.event_shape import typed_columns
from clawmetry.local_store import LocalStore, _DDL

SID = 'codex:debug-session'
NODE = 'node-é'
TS = '2026-10-04T02:00:00+00:00'


@pytest.fixture
def store(tmp_path):
    obj = LocalStore.__new__(LocalStore)
    obj._write_lock = threading.RLock()
    obj._conn = duckdb.connect(str(tmp_path/'evidence.duckdb'))
    obj._conn.execute('SET threads=2')
    for table in ('events', 'sessions', 'replay_events'):
        ddl = next(d for d in _DDL if d.strip().startswith('CREATE TABLE IF NOT EXISTS '+table+' ('))
        obj._conn.execute(ddl)
    obj._conn.execute("INSERT INTO sessions(agent_type,session_id,node_id,updated_at) VALUES ('openclaw',?,?,1)", [SID, NODE])
    yield obj
    obj._conn.close()


def event(store, eid, kind='message', data=None, *, sid=SID, node=NODE, ts=TS, created=1, blob=None):
    data = data if data is not None else {'role': 'user', 'content': 'visible message '+eid}
    role, block, tool, error = typed_columns(kind, data)
    store._conn.execute('''INSERT INTO events
        (id,node_id,session_id,event_type,ts,data,created_at,role,block_kind,tool_name,is_error)
        VALUES (?,?,?,?,?,?,?,?,?,?,?)''',
        [eid,node,sid,kind,ts,blob if blob is not None else json.dumps(data).encode(),created,role,block,tool,error])


def call(store, eid='call', call_id='call-1', command='python check.py', **kw):
    event(store, eid, 'tool_call', {'role': 'assistant', 'tool_name': 'exec',
          'tool_calls': [{'id':call_id, 'name':'exec', 'arguments':json.dumps({'cmd':command})}],
          'extra': {'callId':call_id}}, **kw)


def result(store, eid='result', call_id='call-1', output='Process exited with code 1\nAssertion failed', **kw):
    event(store, eid, 'tool_result', {'role':'tool', 'tool_name':'exec', 'content':output,
          'extra':{'callId':call_id,'isError':True}, 'exit_code':1}, **kw)


def replay(store, eid, kind, payload, *, sid=SID, runtime='codex', ts=1791079200., created=1):
    store._conn.execute('''INSERT INTO replay_events
        (span_id,session_id,runtime,kind,ts,payload,created_at) VALUES (?,?,?,?,?,?,?)''',
        [eid,sid,runtime,kind,ts,json.dumps(payload).encode(),created])


def read(store, **kwargs):
    return store.query_assistant_session_evidence(**{'session_id':SID,'runtime':'codex','node_id':NODE,**kwargs})


def test_real_codex_error_pairs_by_call_id_across_usage(store):
    """AC-ASSIST-008.1
    AC-ASSIST-008.2
    """
    call(store)
    event(store,'usage','usage',{'extra':{'inputTokens':42}})
    result(store)
    page = read(store)
    assert 'error' not in page
    assert len(page['items']) == 1
    item = page['items'][0]
    assert item['fields']['command'] == 'python check.py'
    assert item['fields']['output'].endswith('Assertion failed')
    assert item['fields']['exit_code'] == '1'
    assert item['call_id'] == 'call-1'
    assert item['pairing']['status'] == 'paired'
    assert item['pairing']['call_event_id'] == 'events:call'
    assert item['pairing']['result_event_id'] == 'events:result'
    assert item['ts'].startswith('2026-10-04T')
    assert page['bytes'] == len(json.dumps(page,ensure_ascii=False,separators=(',',':')).encode())


def test_canonical_replay_preferred_for_exact_call_arguments(store):
    result(store)
    call(store,command='legacy preview')
    replay(store,'canonical-call','tool.call',{'call_id':'call-1','tool':'exec','args':{'command':'canonical command'}})
    page=read(store)
    assert page['items'][0]['fields']['command'] == 'canonical command'
    assert page['items'][0]['pairing']['call_event_id'] == 'replay:canonical-call'


@pytest.mark.parametrize('source',['events','replay'])
def test_duplicate_call_ids_are_ambiguous_not_first_match(store,source):
    result(store)
    for i in range(2):
        if source == 'events':call(store,eid='call-'+str(i))
        else:replay(store,'c'+str(i),'tool.call',{'call_id':'call-1','tool':'exec','args':{'cmd':str(i)}})
    item=read(store)['items'][0]
    assert item['pairing']['status'] == 'ambiguous'
    assert 'arguments' not in item['fields']


def test_pair_never_uses_other_session_node_or_adjacent_usage(store):
    call(store,sid='codex:other')
    call(store,eid='foreign-node-call',node='other-node')
    event(store,'nearest','usage',{'content':'not a command'})
    result(store)
    item=read(store)['items'][0]
    assert item['pairing']['status'] == 'unresolved'
    assert 'command' not in item['fields']


def test_pair_scan_exhaustion_does_not_consume_the_primary_error_page(store):
    for i in range(280):call(store,eid='call-'+str(i),call_id='unmatched-'+str(i))
    for i in range(17):result(store,eid='error-'+str(i),call_id='missing-'+str(i),output='recorded failure')
    page=read(store)
    assert len(page['items'])==17
    assert page['coverage']['scanned']<=evidence.MAX_RECORDS
    assert page['coverage']['pair_scan_limited']
    assert all(item['pairing']['status']=='unresolved' for item in page['items'])


def test_large_multifield_unicode_record_still_has_a_continuation(store):
    command='😀'*6000
    call(store,command=command)
    result(store,output='😀'*6000)
    page=read(store)
    assert len(page['items'])==1
    assert page['bytes']<=evidence.MAX_RESPONSE_BYTES
    assert page['items'][0]['field_status']['output']['next_offset'] is not None


def test_embedded_claude_tools_preserve_matching_id_only(store):
    event(store,'claude-call','assistant',{'message':{'role':'assistant','content':[
        {'type':'thinking','thinking':'NEVER_EXPORT_REASONING'},
        {'type':'tool_use','id':'unrelated','name':'Bash','input':{'command':'wrong'}},
        {'type':'tool_use','id':'match','name':'Bash','input':{'command':'right'}}]}})
    event(store,'claude-result','user',{'message':{'role':'user','content':[
        {'type':'tool_result','tool_use_id':'match','is_error':True,'content':'failed assertion'}]}})
    page=read(store)
    item=page['items'][0]
    assert item['fields']['command']=='right'
    assert 'NEVER_EXPORT' not in json.dumps(page)


def test_openclaw_nested_dotted_shapes(store):
    event(store,'oc-call','tool.call',{'data':{'toolUseId':'oc-id','name':'exec','input':{'command':'echo check'}}})
    event(store,'oc-result','tool.result',{'data':{'toolUseId':'oc-id','output':'failure','isError':True}})
    item=read(store)['items'][0]
    assert item['fields']['command']=='echo check'
    assert item['pairing']['status']=='paired'


def test_stable_tied_timestamp_pages_and_late_backfill_cutoff(store):
    """AC-ASSIST-008.3"""
    for i in range(45):event(store,f'e{i:03}')
    first=read(store,mode='recent')
    assert len(first['items'])==20
    event(store,'late-old',ts='2026-10-03T00:00:00Z',created=int(time.time()*1000)+1)
    event(store,'late-tied',created=int(time.time()*1000)+1)
    second=read(store,mode='recent',cursor=first['next_cursor'])
    third=read(store,mode='recent',cursor=second['next_cursor'])
    ids=[x['event_id'] for page in (first,second,third) for x in page['items']]
    assert len(ids)==len(set(ids))==45
    assert not third['next_cursor']
    assert third['coverage']['as_of']==first['coverage']['as_of']
    assert third['coverage']['traversal']=='bounded_live'


@pytest.mark.parametrize('change',[{'runtime':'claude_code'},{'node_id':'wrong'},{'session_id':'codex:other'},
    {'since':'2026-10-04T01:00:00Z'},{'mode':'errors'}])
def test_cursor_scope_change_rejected(store,change):
    for i in range(3):event(store,str(i))
    page=read(store,mode='recent',limit=1)
    with pytest.raises(ValueError):read(store,**{'mode':'recent','cursor':page['next_cursor'],**change})


@pytest.mark.parametrize('cursor',['not!base64','e30','W10'])
def test_malformed_cursor_rejected(store,cursor):
    with pytest.raises(ValueError):read(store,cursor=cursor)


def test_long_field_continues_after_redaction_not_raw_offsets(store,monkeypatch):
    monkeypatch.setenv('CLAWMETRY_REDACT','0')
    monkeypatch.setenv('CLAWMETRY_REDACT_PII','0')
    secret='sk-ant-'+('x'*40)
    output='prefix '*582+secret+' suffix'*1100
    result(store,output=output)
    expected,why=evidence.scrub_export_payload(output)
    assert not why and secret not in expected
    chunks=[];offset=0
    while True:
        page=read(store,mode='event',event_id='events:result',field='output',offset=offset)
        item=page['items'][0];chunks.append(item['fields']['output'])
        offset=item['field_status']['output']['next_offset']
        assert secret not in json.dumps(page)
        if offset is None:break
    assert ''.join(chunks)==expected


def test_export_privacy_ignores_ingest_opt_out_and_fails_closed(store,monkeypatch):
    from clawmetry import redaction
    monkeypatch.setenv('CLAWMETRY_REDACT','0')
    event(store,'msg',data={'role':'user','content':'password=superSecretValue bob@example.com'})
    item=read(store,mode='recent')['items'][0]
    assert 'superSecretValue' not in json.dumps(item)
    assert 'bob@example.com' not in json.dumps(item)
    def broken(*_args,**_kwargs):raise RuntimeError('must never leak this exception')
    monkeypatch.setattr(redaction,'_scrub_text',broken)
    page=read(store,mode='recent')
    assert page['items'][0]['fields']=={}
    assert page['items'][0]['field_status']['text']['status']=='withheld'
    assert 'superSecretValue' not in json.dumps(page)


def test_thinking_system_compaction_and_mixed_blocks_never_export(store):
    for kind in ('thinking','compaction','context.compiled'):
        event(store,kind,kind,{'role':'assistant','content':'HIDDEN_'+kind})
    event(store,'mixed','assistant',{'message':{'role':'assistant','content':[
        {'type':'thinking','thinking':'HIDDEN_MIXED'},
        {'type':'text','text':'visible answer'}]}})
    page=read(store,mode='recent')
    assert [x['fields']['text'] for x in page['items']]==['visible answer']
    assert 'HIDDEN' not in json.dumps(page)


def test_empty_is_distinct_from_missing_and_malformed(store):
    result(store,eid='empty',output='')
    result(store,eid='malformed',blob=b'not-json')
    page=read(store)
    byid={x['event_id']:x for x in page['items']}
    assert byid['events:empty']['field_status']['output']['status']=='empty'
    assert byid['events:malformed']['field_status']['output']['status']=='withheld'


def test_oversize_compressed_payload_is_withheld_before_inflation(store,monkeypatch):
    from clawmetry.ccr import compress
    bomb=json.dumps({'role':'user','content':'x'*(evidence.MAX_EVENT_BYTES+1)}).encode()
    event(store,'bomb',blob=compress(bomb,force=True))
    event(store,'large',blob=b'x'*(evidence.MAX_EVENT_BYTES+1))
    page=read(store,mode='recent')
    assert len(page['items'])==2
    assert all(not x['fields'] for x in page['items'])
    assert page['coverage']['decoded_bytes']==evidence.MAX_EVENT_BYTES
    assert page['coverage']['withheld']==2


def test_total_decode_scan_and_response_bounds(store):
    for i in range(150):event(store,str(i),data={'role':'user','content':'z'*20000})
    page=read(store,mode='search',search='not present')
    assert page['items']==[]
    assert page['coverage']['decoded_bytes']<=evidence.MAX_DECODED_BYTES
    assert page['coverage']['scanned']<=evidence.MAX_RECORDS
    assert page['coverage']['scan_limited']
    assert page['next_cursor']
    page=read(store,mode='recent')
    assert page['bytes']<=evidence.MAX_RESPONSE_BYTES
    assert page['next_cursor']


def test_search_literal_after_scrub_and_beyond_default_text_slice(store):
    event(store,'later',data={'role':'user','content':'ordinary '*700+'needle literal%_'})
    page=read(store,mode='search',search='needle literal%_')
    assert len(page['items'])==1
    assert page['items'][0]['event_id']=='events:later'
    assert read(store,mode='search',search='literal___')['items']==[]


def test_scope_and_time_filter_before_candidate_cap(store):
    for i in range(300):event(store,'outside'+str(i),sid='codex:outside')
    event(store,'before',ts='2026-10-03T23:59:00Z')
    event(store,'in')
    page=read(store,mode='recent',since='2026-10-04T00:00:00Z',until='2026-10-04T03:00:00Z')
    assert [x['event_id'] for x in page['items']]==['events:in']
    assert read(store,mode='recent',node_id='other')['coverage']['availability']=='unavailable'


def test_replay_only_session_and_explicit_error_filter(store):
    replay(store,'call','tool.call',{'call_id':'x','tool':'Bash','args':{'command':'check'}})
    replay(store,'result','tool.result',{'call_id':'x','tool':'Bash','is_error':True,'output':'failure'})
    replay(store,'ok','tool.result',{'call_id':'y','tool':'Bash','is_error':False,'output':'okay'})
    page=read(store)
    assert len(page['items'])==1
    assert page['items'][0]['fields']['command']=='check'


@pytest.mark.parametrize('method',['query_assistant_session_evidence','query_assistant_sql'])
def test_deadline_includes_writer_lock_wait(store,method):
    acquired=threading.Event();release=threading.Event()
    def hold():
        with store._write_lock:acquired.set();release.wait(2)
    worker=threading.Thread(target=hold);worker.start();assert acquired.wait(1)
    args={'session_id':SID,'runtime':'codex','node_id':NODE} if 'evidence' in method else {'sql':'SELECT 1'}
    try:
        start=time.monotonic()
        page=getattr(store,method)(**args,timeout_secs=.06)
        assert time.monotonic()-start<.5
        assert 'timed out' in page['error']
    finally:release.set();worker.join()
    assert store._conn.execute('SELECT 1').fetchone()==(1,)


@pytest.mark.parametrize('method',['query_assistant_session_evidence','query_assistant_sql'])
def test_cancellation_waiting_for_writer_releases_resources(store,method):
    """AC-ASSIST-008.6"""
    acquired=threading.Event();release=threading.Event();cancelled=threading.Event()
    def check():
        if cancelled.is_set():raise Cancelled()
    def hold():
        with store._write_lock:acquired.set();release.wait(2)
    worker=threading.Thread(target=hold);worker.start();assert acquired.wait(1)
    timer=threading.Timer(.06,cancelled.set);timer.start()
    args={'session_id':SID,'runtime':'codex','node_id':NODE} if 'evidence' in method else {'sql':'SELECT 1'}
    try:
        with pytest.raises(Cancelled):getattr(store,method)(**args,cancel=check)
    finally:release.set();worker.join();timer.cancel();timer.join()
    assert not any(t.name=='assistant-read-deadline' for t in threading.enumerate())


def test_existing_sql_payload_and_filesystem_guards_unchanged(store):
    for sql in ('SELECT data FROM events',"SELECT * FROM read_json('/tmp/private')",'DELETE FROM events'):
        assert store.query_assistant_sql(sql=sql).get('error')


def test_rpc_allowlist_includes_only_typed_entry_point():
    from routes.local_query import _DAEMON_METHODS
    assert 'query_assistant_session_evidence' in _DAEMON_METHODS


def test_sql_stop_interrupts_running_native_query_without_closing_writer(store):
    store._conn.execute("""INSERT INTO events(id,node_id,event_type,ts,created_at)
        SELECT 'slow-' || CAST(i AS VARCHAR),'local','message','2026-10-04',1 FROM range(1500) r(i)""")
    stopped=threading.Event()
    def check():
        if stopped.is_set():raise Cancelled()
    timer=threading.Timer(.1,stopped.set);timer.start()
    try:
        start=time.monotonic()
        with pytest.raises(Cancelled):
            store.query_assistant_sql(sql='SELECT COUNT(*) FROM events a,events b,events c',cancel=check)
        assert time.monotonic()-start<1
    finally:timer.cancel();timer.join()
    assert store._conn.execute('SELECT COUNT(*) FROM events').fetchone()==(1500,)
    assert not any(t.name=='assistant-read-deadline' for t in threading.enumerate())


def test_cancel_during_projection_never_returns_evidence(store,monkeypatch):
    event(store,'stop-me')
    stopped=threading.Event()
    original=evidence.scrub_export_payload
    def scrub(value):
        stopped.set()
        return original(value)
    def check():
        if stopped.is_set():raise Cancelled()
    monkeypatch.setattr(evidence,'scrub_export_payload',scrub)
    with pytest.raises(Cancelled):read(store,mode='recent',cancel=check)
    assert not any(t.name=='assistant-read-deadline' for t in threading.enumerate())


def test_explicit_thinking_detail_is_withheld_without_fetching_payload(store):
    event(store,'private-thinking','thinking',{'role':'assistant','content':'HIDDEN_REASONING'})
    page=read(store,mode='event',event_id='events:private-thinking')
    assert len(page['items'])==1
    assert page['items'][0]['fields']=={}
    assert page['items'][0]['field_status']['text']['status']=='withheld'
    assert page['coverage']['decoded_bytes']==0


def test_repeated_compression_bombs_spend_the_decode_budget(store):
    from clawmetry.ccr import compress
    bomb=compress(json.dumps({'role':'user','content':'x'*500000}).encode(),force=True)
    for i in range(30):event(store,str(i),blob=bomb)
    page=read(store,mode='recent')
    assert page['coverage']['decoded_bytes']==evidence.MAX_DECODED_BYTES
    assert page['coverage']['scanned']<=8
    assert len(page['items'])<=8 and page['next_cursor']


def test_output_budget_pages_never_skip_records(store):
    for i in range(30):event(store,str(i).zfill(3),data={'role':'user','content':'😀'*5000})
    ids=[];cursor=None
    for _ in range(40):
        page=read(store,mode='recent',cursor=cursor)
        assert page['bytes']<=evidence.MAX_RESPONSE_BYTES
        ids.extend(x['event_id'] for x in page['items'])
        cursor=page['next_cursor']
        if cursor is None:break
    assert len(ids)==len(set(ids))==30


def test_unknown_output_structure_is_missing_not_fabricated_empty(store):
    event(store,'structured','tool.result',{'toolUseId':'x','is_error':True,
        'result':{'stdout':'safe standard output','stderr':'actual recorded error','exit_code':7,
                  'thinking':'HIDDEN_THINKING','arbitrary_blob':'NEVER_INCLUDE'}})
    item=read(store)['items'][0]
    assert item['fields']['exit_code']=='7'
    assert 'safe standard output' in item['fields']['output']
    assert 'actual recorded error' in item['fields']['output']
    assert 'HIDDEN' not in json.dumps(item) and 'NEVER_INCLUDE' not in json.dumps(item)


def test_nonempty_unsupported_output_has_explicit_unread_state(store):
    event(store,'unknown-output','tool.result',{'toolUseId':'x','is_error':True,
        'result':{'error_details':{'code':'FILE_NOT_FOUND','filename':'report.json'}}})
    item=read(store)['items'][0]
    assert 'output' not in item['fields']
    assert item['field_status']['output']['status'] == 'unread'


@pytest.mark.parametrize('kind',['message','tool_result'])
def test_serialized_content_blocks_exclude_reasoning(store,kind):
    blocks=json.dumps([{'type':'thinking','thinking':'PRIVATE_REASONING'},
                       {'type':'input_text','text':'ordinary visible text'},
                       {'type':'output_text','channel':'analysis','text':'PRIVATE_REASONING3'},
                       {'type':'text','phase':'analysis','text':'PRIVATE_REASONING4'},
                       {'type':'reasoning','text':'PRIVATE_REASONING2'}])
    event(store,'serialized',kind,{'role':'user' if kind=='message' else 'tool',
        'content':blocks,'extra':{'isError':kind=='tool_result'}})
    item=read(store,mode='recent')['items'][0]
    field='text' if kind=='message' else 'output'
    assert item['fields'][field]=='ordinary visible text'
    assert 'PRIVATE_REASONING' not in json.dumps(item)


def test_arbitrary_json_stdout_is_preserved_as_text(store):
    text='[{"type":"build_failure","code":"missing_asset"}]'
    result(store,output=text)
    assert read(store)['items'][0]['fields']['output']==text


@pytest.mark.parametrize('kind',['message','tool_result'])
def test_serialized_unknown_blocks_do_not_bypass_hidden_block_guard(store,kind):
    text=json.dumps([{'type':'thinking','thinking':'SYNTHETIC_PRIVATE_THINKING'},
                     {'type':'build_failure','code':'x'}])
    event(store,'mixed-unknown',kind,{'role':'user' if kind=='message' else 'tool','content':text})
    item=read(store,mode='recent')['items'][0]
    assert 'SYNTHETIC_PRIVATE_THINKING' not in json.dumps(item)
    field='text' if kind=='message' else 'output'
    assert item['field_status'][field]['status']=='unread'


def test_error_paging_with_fractional_time_window_and_mixed_key_types(store):
    for i in range(17):
        result(store,eid='codex:session:'+str(i),ts=f'2026-10-04T02:{i:02}:00.123000+00:00',output='x'*9000)
    cursor=None;ids=[]
    for _ in range(8):
        page=read(store,since='2026-10-04T02:00:00Z',until='2026-10-04T03:00:00Z',cursor=cursor)
        assert 'error' not in page
        ids.extend(x['event_id'] for x in page['items'])
        cursor=page['next_cursor']
        if cursor is None:break
    assert len(ids)==len(set(ids))==17


@pytest.mark.parametrize('change',[{'mode':[]},{'mode':'event','event_id':'bad'},
    {'field':{}},{'limit':True},{'offset':-1},{'since':'not a date'},
    {'mode':'search','search':''},{'timeout_secs':float('nan')}])
def test_invalid_typed_arguments_rejected_without_sql(store,change):
    with pytest.raises(ValueError):read(store,**change)


@pytest.mark.parametrize('runtime',['openclaw','claude_code','codex','goose','qwen_code','cursor','gemini_cli','hermes','aider'])
def test_canonical_runtime_scope_over_legacy_agent_labels(store,runtime):
    sid='bare-openclaw-uuid' if runtime=='openclaw' else runtime+':family'
    store._conn.execute("INSERT INTO sessions(agent_type,session_id,node_id,updated_at) VALUES ('openclaw',?,?,1)",[sid,NODE])
    event(store,'family-event',sid=sid)
    page=read(store,session_id=sid,runtime=runtime,mode='recent')
    assert len(page['items'])==1 and page['scope']['runtime']==runtime
