"""AC-ASSIST-008.1/.2/.5/.6: typed Sources through the real Assistant page.

Factory requirement v5 / blueprint v23 were read before implementation.
Fixtures contain synthetic evidence only; these are not live harness proof.
"""
import copy
import json

import pytest

from tests.test_assistant_frontend import _PAGE_STREAM_JS, _run_node


SESSION = "codex:recorded+session%/世界"
SOURCE = {
    "kind": "session_evidence", "label": "[1] Recorded command failure",
    "rows": 1, "preview_rows": 1,
    "read": {"session_id": SESSION, "runtime": "codex", "mode": "errors", "limit": 20},
    "coverage": {
        "schema_version": 1,
        "scope": {"session_id": SESSION, "runtime": "codex", "node_id": "test-node",
                  "since": "2026-10-04T00:00:00Z", "until": "2026-10-05T00:00:00Z"},
        "next_cursor": "opaque-next-page",
        "coverage": {"scanned": 53, "returned": 1, "scan_limited": True,
                     "decoded_bytes": 1000, "as_of": "2026-10-05T07:00:00Z"},
        "bytes": 1600,
    },
    "preview": [{
        "event_id": "events:result-1", "ts": "2026-10-04T12:00:00Z",
        "kind": "tool_result", "role": "tool", "call_id": "call-1",
        "tool_name": "exec_command", "is_error": True,
        "fields": {"command": "python verify.py --check", "output": "File missing: report.json",
                   "arguments": {"workdir": "/workspace"}, "exit_code": 1},
        "field_status": {
            "command": {"status": "available"}, "arguments": {"status": "available"},
            "output": {"status": "truncated", "offset": 500, "next_offset": 525, "total_chars": 900},
            "exit_code": {"status": "available"}, "error": {"status": "missing"},
        },
        "pairing": {"status": "paired", "basis": "call_id", "call_event_id": "events:call-1",
                    "result_event_id": "events:result-1"},
    }],
}


def _render(source, assertions, setup=""):
    _run_node(_PAGE_STREAM_JS + setup + "\nconst source = " + json.dumps(source) + r"""
const stream = await startChat('What did the recorded command fail on?');
stream.push(frame('done', {answer:'Recorded evidence [1].', conversation_id:'saved', sources:[source]}));
await flush();
const sources = byClass(thread, 'cm-assistant-sources')[0];
assert.ok(sources);
""" + assertions)


def test_typed_evidence_fields_provenance_and_trusted_session_action():
    _render(SOURCE, r"""
assert.match(sources.textContent, /python verify.py --check/);
assert.match(sources.textContent, /File missing: report.json/);
assert.match(sources.textContent, /Characters 501 to 525 of 900/);
assert.match(sources.textContent, /53 records checked/);
assert.match(sources.textContent, /outside the checked records/);
assert.match(sources.textContent, /More records remain to be checked/);
assert.match(sources.textContent, /linked by their recorded call ID/);
assert.match(sources.textContent, /Event: events:result-1/);
assert.match(sources.textContent, /From: 2026-10-04T00:00:00Z/);
assert.match(sources.textContent, /Recorded through: 2026-10-05T07:00:00Z/);
const calls = chatCalls.length, loads = historyLoads;
byClass(sources, 'cm-assistant-evidence-open')[0].dispatch('click');
assert.deepEqual(opened, [source.read.session_id]);
assert.equal(chatCalls.length, calls); assert.equal(historyLoads, loads);
assert.equal(timers.size, 0);
""", "const opened=[]; context.openTrail = sid => opened.push(sid);")


@pytest.mark.parametrize("status,note", [
    ("empty", "Recorded as empty"), ("missing", "Not present in this record"),
    ("withheld", "Withheld from this evidence"), ("unread", "was not read"),
    ("unavailable", "is unavailable"), ("unknown", "Readable content was not supplied"),
])
def test_unreadable_field_never_renders_residual_content(status, note):
    source = copy.deepcopy(SOURCE)
    source["preview"][0]["fields"]["output"] = "DO_NOT_DISPLAY"
    source["preview"][0]["field_status"]["output"] = {"status": status}
    _render(source, "assert.ok(sources.textContent.includes(" + json.dumps(note) + "));"
            "assert.ok(!sources.textContent.includes('DO_NOT_DISPLAY'));")


@pytest.mark.parametrize("status,note", [
    ("unresolved", "No unique command link"), ("ambiguous", "More than one command matched"),
])
def test_pairing_does_not_invent_a_command_match(status, note):
    source = copy.deepcopy(SOURCE)
    source["preview"][0]["pairing"]["status"] = status
    _render(source, "assert.ok(sources.textContent.includes(" + json.dumps(note) + "));"
            "assert.ok(!sources.textContent.includes('Command and result linked'));")


def test_untrusted_fields_are_text_and_nonpublic_fields_are_not_rendered():
    source = copy.deepcopy(SOURCE)
    item = source["preview"][0]
    item["fields"].update(command='<img src=x onerror="alert(1)">', reasoning="PRIVATE_REASONING")
    item["field_status"]["reasoning"] = {"status": "available"}
    source["url"] = "javascript:alert(1)"
    _render(source, r"""
assert.ok(sources.textContent.includes('<img src=x onerror="alert(1)">'));
assert.ok(!sources.textContent.includes('PRIVATE_REASONING'));
function tags(n) { return [n.tagName, ...n.children.flatMap(tags)]; }
assert.ok(!tags(sources).includes('IMG')); assert.ok(!tags(sources).includes('A'));
""")


@pytest.mark.parametrize("change", ["context.assistantLeave();", "elements.get('cm-assistant-new-chat').dispatch('click');"])
def test_detached_source_button_cannot_navigate_after_leaving_or_new_chat(change):
    _render(SOURCE, "const button=byClass(sources,'cm-assistant-evidence-open')[0];" + change +
            "button.dispatch('click'); assert.deepEqual(opened, []);",
            "const opened=[]; context.openTrail=sid=>opened.push(sid);")


@pytest.mark.parametrize("mismatch", ["session", "node"])
def test_wrong_scope_has_no_session_navigation(mismatch):
    source = copy.deepcopy(SOURCE)
    source["coverage"]["scope"]["session_id" if mismatch == "session" else "node_id"] = "other"
    setup = "context.openTrail=()=>{throw Error('wrong scope')};"
    if mismatch == "node":
        # Turn on cloud mode only at publication; existing request guard gets a
        # stable identity, while the evidence itself refers to another node.
        setup += "context.CLOUD_NODE_ID='test-node';"
        script = _PAGE_STREAM_JS.replace("const context = {", "const context = { CLOUD_MODE:true, _cmAssistantRelay:{version:1,identity:()=> 'test-scope'},")
        script += setup + "const source=" + json.dumps(source) + r""";
const stream=await startChat(); stream.push(frame('done',{answer:'Answer',conversation_id:'saved',sources:[source]})); await flush();
assert.equal(byClass(thread,'cm-assistant-evidence-item').length,1);
assert.equal(byClass(thread,'cm-assistant-evidence-open').length,0);
"""
        _run_node(script)
    else:
        _render(source, "assert.equal(byClass(sources,'cm-assistant-evidence-open').length,0);", setup)


def test_key_change_invalidates_existing_evidence_navigation():
    script = _PAGE_STREAM_JS.replace("const context = {", "let identity='key-A'; const context = { CLOUD_MODE:true, CLOUD_NODE_ID:'test-node', _cmAssistantRelay:{version:1,identity:()=>identity},")
    _run_node(script + "const source=" + json.dumps(SOURCE) + r""";
const opened=[];context.openTrail=sid=>opened.push(sid);
const stream=await startChat();stream.push(frame('done',{answer:'Answer',conversation_id:'saved',sources:[source]}));await flush();
const button=byClass(thread,'cm-assistant-evidence-open')[0];
identity='key-B';button.dispatch('click');assert.deepEqual(opened,[]);
assert.equal(byClass(thread,'cm-assistant-evidence-item').length,0);
""")


def test_sql_coverage_uses_returned_rows_not_preview_rows_and_keeps_query():
    _render({"label": "[1] Recorded errors", "rows": 53, "preview_rows": 20,
             "preview": [{"error_count": n} for n in range(20)],
             "truncated": True, "sql": "SELECT error_count FROM sessions"}, r"""
assert.match(sources.textContent,/preview 20 of 53/);
assert.match(sources.textContent,/Showing 20 of 53 returned rows/);
assert.match(sources.textContent,/query reached its result limit/);
assert.match(sources.textContent,/SELECT error_count FROM sessions/);
""")


def test_empty_or_malformed_typed_evidence_has_honest_empty_state():
    _render({"kind": "session_evidence", "preview": [], "coverage": None}, r"""
assert.match(sources.textContent,/does not establish that nothing was recorded/);
assert.equal(byClass(sources,'cm-assistant-evidence-open').length,0);
""")


def test_renderer_caps_records_and_discloses_the_limit():
    source = copy.deepcopy(SOURCE)
    source["preview"] *= 25
    _render(source, r"""
assert.equal(byClass(sources,'cm-assistant-evidence-item').length,20);
assert.match(sources.textContent,/read reached a limit/);
""")
