"""Source extraction before browser fallback migration.

AC-STE-002.1: literal fallback diagnostics retain the actual source location.
AC-STE-002.4: dynamic expressions remain pending, not claimed as checked.
"""
import pytest

from scripts.english_js import translations


@pytest.fixture(scope="session")
def server():
    yield None


def test_ignores_comments_strings_regex_and_non_translation_methods():
    source = r'''
// t('comment', null, 'fake')
/* t('block', null, 'fake') */
const s = "t('string', null, 'fake')";
const re = /t\('regex', null, 'fake'\)/;
if (condition) /[/'"]/.test(s);
object.t('method', null, 'fake');
t('real', null, 'Read the report.');
'''
    calls = translations(source)
    assert [(c.key, c.fallback) for c in calls] == [('real', 'Read the report.')]
    assert calls[0].line == 8


def test_nested_arguments_escaped_literals_and_division():
    source = r'''const n = ({a: 6}).a / 2;
window.t('key', {count: f(3, /a,b/g), values: [1,2]}, 'The agent\'s session has {count} events.');
t('other', null, "The unit is \u0041.\nRead it.");'''
    calls = translations(source)
    assert calls[0].fallback == "The agent's session has {count} events."
    assert calls[1].fallback == "The unit is A.\nRead it."
    assert source[calls[0].fallback_start:calls[0].fallback_end].startswith("'The agent")


def test_template_expressions_are_code_but_template_text_is_not():
    source = '''const html = `t('fake', null, 'fake') ${t('real', null, `Read the report.`)}`;
t('dynamic', null, `Session ${session.id} has events.`);'''
    calls = translations(source)
    assert [(c.key, c.fallback) for c in calls] == [('real', 'Read the report.'), ('dynamic', None)]
    assert calls[1].pending == 'dynamic fallback'


def test_dynamic_keys_and_computed_fallbacks_are_explicit():
    calls = translations("t('prefix.' + kind, null, 'Data is unavailable.'); t('key', null, message);")
    assert calls[0].key is None and calls[0].fallback == 'Data is unavailable.'
    assert calls[0].pending == 'dynamic key'
    assert calls[1].pending == 'dynamic fallback'


def test_helper_signature_is_explicit_and_definition_is_not_a_call():
    calls = translations("function T(key, fallback, vars) {} T('key', 'The agent stopped.', {n: 1});",
                         aliases={'T': 1})
    assert len(calls) == 1 and calls[0].fallback == 'The agent stopped.'


def test_optional_translation_calls_and_generator_definition():
    source = "function* t(a,b,c) {} window?.t?.('key', null, 'Read the report.');"
    calls = translations(source)
    assert len(calls) == 1 and calls[0].key == 'key'


def test_regex_after_block_and_division_after_expression():
    source = r'''if (ready) { done(); } /t\('fake'\)/.test(s);
const ratio = ({x: 6}).x / 2; t('real', {n: ratio}, 'There are {n} events.');'''
    assert [c.key for c in translations(source)] == ['real']


def test_nested_templates_and_unicode_escapes():
    source = r'''const s = `${`inner ${t('key', {}, '\uD83D\uDD0D Search')}`}`;'''
    calls = translations(source)
    assert len(calls) == 1 and calls[0].fallback == '🔍 Search'


@pytest.mark.parametrize('source', ["t('x', null, 'unfinished", '/* unfinished', 'const t = `unfinished',
                                   "t('x', null, 'text'"])
def test_incomplete_source_fails_explicitly(source):
    with pytest.raises(ValueError):
        translations(source)
