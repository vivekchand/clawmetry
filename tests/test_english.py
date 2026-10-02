"""Mechanical language checks: AC-STE-001.1/.2/.3 and AC-STE-002.1/.5.

These test the declared subset. They do not certify ASD-STE100 compliance.
"""
import json
from pathlib import Path

import pytest

from clawmetry.english import (INSIGHT_MESSAGES, check_generated_text, check_text,
                              insight_fallback, sentences, terminology, word_count)


@pytest.fixture(scope="session")
def server():
    """These offline unit tests have no live dashboard dependency."""
    yield None


def rules(text, kind="description"):
    return {finding.rule for finding in check_text(text, kind)}


@pytest.mark.parametrize("text", ["It isn't available.", "You’re connected.",
                                  "We’ll try again.", "It's available.", "Let's start."])
def test_contractions(text):
    assert "STE-4.2" in rules(text)


def test_possessives_and_technical_words_are_not_contractions():
    assert not rules("The agent's session has data. The collector is active during the session.")


def test_sentence_limits_depend_on_type():
    text = " ".join(["word"] * 21) + "."
    assert "STE-5.1" in rules(text, "instruction")
    assert "STE-5.1" in rules(text, "unclassified")
    assert not rules(text, "description")
    assert "STE-6.3" in rules(" ".join(["word"] * 26) + ".")


def test_conservative_word_count_supports_protected_forms():
    assert word_count('Select "Show all sessions" (or use the menu).') == 3
    assert word_count("Wait 10 ms for ClawMetry Cloud.") == 4
    assert word_count("Use the read-only view for session_id.") == 6
    assert word_count("Open https://example.com/a.b?x=3.14 for {session_id}.") == 4


def test_decimal_and_identifier_do_not_create_sentences():
    assert len(sentences("The cost is $3.14. Open https://example.com. Try again.")) == 3
    assert len(sentences("Use these items:\n- The first item\n- The second item")) == 3


def test_wrapping_cannot_bypass_sentence_length():
    text = " ".join(["word"] * 13) + "\n" + " ".join(["word"] * 13) + "."
    assert len(sentences(text)) == 1
    assert "STE-6.3" in rules(text)
    assert len(sentences("Select a session.\nRead its events.")) == 2


def test_command_source_is_protected_without_rewriting_it():
    text = 'Run `clawmetry --help`. The result is available at https://example.com/a--b.'
    before = text
    assert not rules(text)
    assert text == before
    assert "CM-DASH" in rules("Data is ready -- open the report.")


def test_punctuation_and_project_terms_are_separate_rules():
    assert "STE-8.1" in rules("The agent stopped; open its session.")
    assert "CM-DASH" in rules("The agent stopped — open its session.")
    assert "CM-TERM" in rules("Utilize the session view.")


@pytest.mark.parametrize("value", [None, "", "  ", 3, [], {}])
def test_invalid_text_is_a_finding(value):
    assert "CM-EMPTY" in rules(value)


@pytest.mark.parametrize("value", ["```We can't start.```", "<b>Data is available.</b>", "Use `secret`."])
def test_generated_prose_cannot_hide_in_markup(value):
    assert "CM-FORMAT" in {f.rule for f in check_generated_text(value)}


def test_generated_summary_contract():
    assert not check_generated_text("The agent used 500 tokens. The estimated cost is $0.02.")
    assert "CM-SUMMARY" in {f.rule for f in check_generated_text("One. Two. Three. Four.")}


def test_project_glossary_has_explicit_meanings_and_roles():
    data = terminology()
    names = [entry["term"] for entry in data["terms"]]
    assert len(names) == len(set(names))
    for entry in data["terms"]:
        assert entry["meaning"] and entry["part_of_speech"]
    assert {"agent", "runtime", "session", "token"} <= set(names)
    assert "Not the ASD dictionary" in data["status"]


def test_fallbacks_pass_after_interpolation():
    for count in (0, 1, 2, 999999):
        for connect in (True, False):
            assert not check_text(insight_fallback(count, connect))
    for value in INSIGHT_MESSAGES.values():
        assert not check_text(value)
    assert "1 row." in insight_fallback(1)
    assert "2 rows." in insight_fallback(2)


def test_catalog_preserves_placeholder_names():
    """The migrated dynamic messages retain their insertion contract."""
    import re
    path = Path(__file__).resolve().parents[1] / "clawmetry/static/locales/en.json"
    catalog = json.loads(path.read_text())
    expected = {"alerts.feed_stopped": {"duration"},
                "overview.hb_banner_silent": {"gap", "interval"},
                "overview.hb_banner_delayed": {"gap", "interval"}}
    for key, names in expected.items():
        assert set(re.findall(r"\{(\w+)\}", catalog[key])) == names
        rendered = catalog[key].format(duration="5 minutes", gap="2 hours", interval=30)
        assert not check_text(rendered)
