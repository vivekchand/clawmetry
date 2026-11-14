"""Improve hands a signal to the Assistant instead of to a file browser.

Founder report 2026-10-17, on the hosted Improve tab: "what is this page
supposed to do?? I'm unable to understand ... clicking on Open Setup just
opens setup tab -- i've no idea what to do either -- instead of open setup --
have investigate button to trigger an investigation on that".

"Open Setup" switched tabs and stopped. The reader was left in front of a
memory-file list with no connection to the card they pressed. The action that
does something with a candidate is an investigation, so these tests hold:

1. Investigate reaches the Assistant carrying the evidence the card was built
   from (the excerpt, where it was seen, the runtime), not just a tab switch.
2. A question the Assistant cannot send yet stays in the composer with the
   reason, because a dropped question is the failure we are replacing.
3. Nothing on this path writes a file - the Improve tab stays read-only.

Factory requirement REQ-ASSIST-010 ("Investigate an Improve signal instead of
browsing to Setup", 75d07ea2-7c43-429f-b70e-e91840841006):

* AC-ASSIST-010.1 -- test_investigate_sends_the_evidence_to_the_assistant,
  test_assistant_ask_opens_the_tab_and_sends_the_question
* AC-ASSIST-010.2 -- test_investigate_sends_the_evidence_to_the_assistant
* AC-ASSIST-010.3 -- test_the_review_dialog_investigates_the_signal_it_is_showing,
  test_improve_screen_offers_investigate_and_explains_itself
* AC-ASSIST-010.4 -- test_a_question_that_cannot_be_sent_stays_in_the_composer,
  test_a_missing_assistant_says_so_instead_of_navigating_nowhere
* AC-ASSIST-010.5 -- test_investigating_never_writes_anything
* AC-ASSIST-010.6 -- test_improve_screen_offers_investigate_and_explains_itself
"""

from pathlib import Path
import json

import pytest

ROOT = Path(__file__).parents[1]
IMPROVE_HTML = ROOT / "clawmetry/templates/tabs/improve.html"
IMPROVE_JS = ROOT / "clawmetry/static/js/improve.js"
ASSISTANT_JS = ROOT / "clawmetry/static/js/assistant.js"


# ── the Improve side: a card becomes a question ────────────────────────────

def _run_improve(script):
    from tests.test_improve_frontend import run_node

    run_node(script)


def test_investigate_sends_the_evidence_to_the_assistant():
    _run_improve(r'''
let asked = [];
window.assistantAsk = (question, options) => { asked.push({question, options}); return Promise.resolve(true); };
await loadImprove();
window.improveInvestigate('codex');
assert.equal(asked.length, 1, 'Investigate must reach the Assistant');
const question = asked[0].question;
assert.match(question, /Always keep changes small\./, 'carries what I actually said');
assert.match(question, /Evidence from my conversations/, 'carries the evidence behind the card');
assert.match(question, /codex/, 'names the runtime it came from');
assert.match(question, /2 observed turns/, 'says how often it was seen');
assert.match(question, /which single instruction, skill, agent or hook/, 'asks for one concrete change');
assert.ok(question.length <= 4000, 'stays inside the composer limit');
''')


def test_the_review_dialog_investigates_the_signal_it_is_showing():
    _run_improve(r'''
let asked = [];
window.assistantAsk = question => { asked.push(question); return Promise.resolve(true); };
await loadImprove();
window.improveOpenReview('codex');
assert.equal(nodes['improve-review-modal'].hidden, false);
window.improveInvestigateReviewed();
assert.equal(asked.length, 1, 'the dialog button investigates the open candidate');
assert.match(asked[0], /Always keep changes small\./);
assert.equal(nodes['improve-review-modal'].hidden, true, 'the dialog closes behind the investigation');
window.improveInvestigateReviewed();
assert.equal(asked.length, 1, 'a closed dialog has no candidate to investigate');
''')


def test_a_missing_assistant_says_so_instead_of_navigating_nowhere():
    """The old button's failure was silence. Replacing it with a different
    silent navigation would ship the same complaint again."""
    _run_improve(r'''
let switched = [];
window.switchTab = name => switched.push(name);
window.assistantAsk = undefined;
await loadImprove();
window.improveInvestigate('codex');
assert.deepEqual(switched, [], 'never dump the reader on an empty screen');
assert.match(nodes['improve-source-note'].textContent, /Assistant did not load/);
''')


def test_improve_screen_offers_investigate_and_explains_itself():
    html = IMPROVE_HTML.read_text(encoding="utf-8")
    js = IMPROVE_JS.read_text(encoding="utf-8")

    assert "improveInvestigateReviewed()" in html, "the dialog's primary action investigates"
    assert ">Investigate<" in html
    assert "improveInvestigate(" in js, "every card can start one without opening the dialog"
    # Setup is still reachable, but it is no longer the one thing offered.
    primary = [line for line in html.splitlines() if "cm-improve-primary-button" in line]
    assert primary and all("improveOpenSetup" not in line for line in primary), \
        "Open Setup must not be the primary action any more"
    # The screen has to answer "what is this page supposed to do?" on sight.
    assert "Investigate" in html.split("</section>")[0], "the hero names the action"


def test_investigating_never_writes_anything():
    js = IMPROVE_JS.read_text(encoding="utf-8")
    assert "method:" not in js and "POST" not in js, \
        "Improve reads candidates; the investigation happens in the Assistant"


# ── the Assistant side: the question is asked, or the reason is shown ──────

def _assistant_page(replacements=()):
    from tests.test_assistant_frontend import _PAGE_STREAM_JS

    script = _PAGE_STREAM_JS
    for old, new in replacements:
        assert old in script, old
        script = script.replace(old, new, 1)
    # The real composer submits through requestSubmit; the shared DOM stub
    # models events with dispatch(), so give it the browser's entry point.
    return script + r"""
elements.get('cm-assistant-composer').requestSubmit = function () {
  this.dispatch('submit', {preventDefault() {}});
};
const switched = [];
context.switchTab = name => switched.push(name);
"""


def test_assistant_ask_opens_the_tab_and_sends_the_question():
    from tests.test_assistant_frontend import _run_node

    question = 'Investigate this friction.\n\nWhat I said: "fix it"'
    _run_node(_assistant_page() + "const question = " + json.dumps(question) + r""";
streams.push(controlledStream());
const sent = await context.assistantAsk(question);
assert.equal(sent, true, 'a ready assistant sends the question');
assert.deepEqual(switched, ['assistant'], 'the reader is taken to the answer');
assert.equal(chatCalls.length, 1, 'exactly one investigation is started');
assert.equal(chatCalls[0].payload.message, question, 'the evidence reaches the model intact');
assert.match(thread.textContent, /fix it/, 'the question is visible in the thread');
""")


def test_a_question_that_cannot_be_sent_stays_in_the_composer():
    from tests.test_assistant_frontend import _run_node

    offline = _assistant_page([(
        "      available: true, data_available: true, providers: [], managed: {},",
        "      available: false, data_available: false, providers: [], managed: {},\n"
        "      message: 'This computer is not connected.',",
    )])
    _run_node(offline + r"""
const sent = await context.assistantAsk('Investigate this friction.', {waitMs: 0});
assert.equal(sent, false, 'an unreachable computer cannot answer');
assert.equal(chatCalls.length, 0, 'and nothing is sent into the dark');
assert.equal(input.value, 'Investigate this friction.', 'the question survives for the reader');
assert.match(status.textContent, /not connected/, 'and says why it is still sitting there');
""")


def test_assistant_ask_is_exported_for_other_screens():
    source = ASSISTANT_JS.read_text(encoding="utf-8")
    assert "window.assistantAsk = assistantAsk;" in source
    # Same no-raw-HTML contract as the rest of this module.
    assert "innerHTML" not in source
