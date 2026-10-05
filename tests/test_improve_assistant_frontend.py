"""Exercise the real handoff and stream without any provider calls.

AC-IMPROVE-CHAT-001.1: one-click, one new scoped conversation.
AC-IMPROVE-CHAT-001.3: old collectors and unavailable engines stay actionable.
AC-IMPROVE-CHAT-001.4: navigation, edits and account changes cancel submission.
"""
import pytest

from tests.test_assistant_cloud_states import _cloud_page_script
from tests.test_assistant_frontend import _PAGE_STREAM_JS, _run_node


def page_script(cloud=False, deferred=False, capability=True):
    script = _cloud_page_script() if cloud else _PAGE_STREAM_JS
    if capability:
        script = script.replace('available: true, data_available: true, providers: [], managed: {},',
            'available: true, data_available: true, providers: [], managed: {}, capabilities:{improve_investigation:true},')
    script = script.replace("vm.runInNewContext(fs.readFileSync('clawmetry/static/js/assistant.js', 'utf8'), context);", r'''
context.switchTab = tab => { assert.equal(tab, 'assistant'); context.loadAssistantPage(); };
main.appendChild(add('cm-assistant-improve-context', 'div'));
const reference = {session_id:'codex:incident', runtime:'codex', event_id:'events:anchor'};
vm.runInNewContext(fs.readFileSync('clawmetry/static/js/assistant.js', 'utf8'), context);
''')
    if deferred:
        script = script.replace('context.loadAssistantPage();\nawait flush();', r'''
let finishStatus;
const normalFetch = context.fetch;
context.fetch = (url, options) => url.endsWith('/status')
  ? new Promise((resolve, reject) => {
      finishStatus = resolve;
      if (options.signal) options.signal.addEventListener('abort', () => {
        const error = new Error('Aborted'); error.name='AbortError'; reject(error);
      });
    }) : normalFetch(url, options);
context.loadAssistantPage();
await flush();
''')
    return script


@pytest.mark.parametrize('cloud', [False, True])
def test_handoff_starts_once_streams_and_keeps_followups_in_the_conversation(cloud):
    _run_node(page_script(cloud) + r'''
const first = controlledStream(); streams.push(first);
assert.equal(context.assistantExplainSignal(reference, 'can you start server again ??'), true);
await flush();
assert.equal(chatCalls.length, 1);
assert.deepEqual(chatCalls[0].payload.improve, reference);
assert.ok(!chatCalls[0].payload.conversation_id);
assert.match(chatCalls[0].payload.message, /plain English/);
assert.match(chatCalls[0].payload.message, /prevent a repeat/);
assert.doesNotMatch(chatCalls[0].payload.message, /codex:incident|events:anchor/);
context.loadAssistantPage(); await flush();
assert.equal(chatCalls.length, 1, 'mounting does not replay a submitted request');
first.push(frame('delta', {text:'The agent restarted the wrong service.'})); await flush();
assert.match(thread.textContent, /wrong service/);
first.push(frame('done', {...saved, conversation_id:'incident-chat', answer:'Recovery was not verified.'})); await flush();
const followup = await startChat('How should I verify the proposed fix?');
assert.equal(chatCalls[1].payload.conversation_id, 'incident-chat');
assert.ok(!chatCalls[1].payload.improve, 'follow-up retains saved sources, not a second initial handoff');
followup.push(frame('done', {...saved, conversation_id:'incident-chat'})); await flush();
context.assistantLeave(); assert.equal(timers.size, 0);
''')


@pytest.mark.parametrize('action', ['none', 'edit', 'leave', 'new', 'history', 'scope'])
def test_delayed_readiness_cannot_submit_after_user_or_scope_changes(action):
    _run_node(page_script(cloud=True, deferred=True) + 'const action='+repr(action)+';'+r'''
const stream = controlledStream(); streams.push(stream);
context.assistantExplainSignal(reference, 'start again');
assert.equal(chatCalls.length, 0);
if (action === 'edit') {input.value='My own question';input.dispatch('input');}
if (action === 'leave') context.assistantLeave();
if (action === 'new') elements.get('cm-assistant-new-chat').dispatch('click');
if (action === 'history') elements.get('cm-assistant-history-list').children[0].dispatch('click');
if (action === 'scope') changeScope('other-account-node-key');
finishStatus(jsonResponse({available:true, data_available:true, providers:[], managed:{}, capabilities:{improve_investigation:true}}));
await flush();await flush();
assert.equal(chatCalls.length, action === 'none' ? 1 : 0);
if (action === 'none') {stream.push(frame('done',saved));await flush();}
if (action === 'edit') assert.equal(input.value,'My own question');
context.assistantLeave();await flush();assert.equal(timers.size,0);
''')


def test_old_collector_never_receives_an_ignored_evidence_attachment():
    _run_node(page_script(capability=False) + r'''
context.assistantExplainSignal(reference, 'start again'); await flush();
assert.equal(chatCalls.length,0);
assert.match(status.textContent,/Update ClawMetry/);
assert.match(input.value,/start again/);
submit(); await flush();
assert.equal(chatCalls.length,0);
context.assistantLeave();
''')


def test_leave_and_return_keeps_attachment_for_manual_send_without_autosubmission():
    _run_node(page_script(deferred=True) + r'''
context.assistantExplainSignal(reference, 'start again');
context.assistantLeave();
context.loadAssistantPage(); await flush();
finishStatus(jsonResponse({available:true, data_available:true, providers:[], managed:{}, capabilities:{improve_investigation:true}}));
await flush();await flush();
assert.equal(chatCalls.length,0);
assert.equal(elements.get('cm-assistant-improve-context').hidden,false);
const stream=controlledStream();streams.push(stream);
submit();await flush();
assert.equal(chatCalls.length,1);
assert.deepEqual(chatCalls[0].payload.improve,reference);
stream.push(frame('done',saved));await flush();
context.assistantLeave();assert.equal(timers.size,0);
''')


def test_unavailable_engine_retains_question_for_explicit_send():
    _run_node(page_script(deferred=True) + r'''
context.assistantExplainSignal(reference, 'start again');
finishStatus(jsonResponse({available:false, data_available:true, providers:[], managed:{}, capabilities:{improve_investigation:true}}));
await flush();
assert.equal(chatCalls.length,0);
assert.match(status.textContent,/Connect an available engine/);
assert.match(input.value,/start again/);
assert.equal(elements.get('cm-assistant-improve-context').hidden,false);
context.assistantLeave();
''')
