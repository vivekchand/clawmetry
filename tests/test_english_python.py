"""AC-STE-002.1, AC-STE-002.4: locate CLI prose and retain extraction gaps."""
import pytest

from scripts.english_python import argparse_help


@pytest.fixture(scope="session")
def server():
    yield None


def test_help_fields_are_complete_and_keep_locations():
    source = '''# parser.add_argument('fake', help='Not a message')
example = "parser.add_argument('fake', help='Not a message')"
parser = argparse.ArgumentParser(description='Read the report.')
parser.add_argument('--node', help=('Select a node. '
                                   'Read its events.'), default='localhost')
sub.add_parser('status', help='Show status.', epilog='Open the dashboard.')
'''
    fields = argparse_help(source)
    assert [(field.line, field.text) for field in fields] == [
        (3, 'Read the report.'), (4, 'Select a node. Read its events.'),
        (6, 'Open the dashboard.'), (6, 'Show status.')]
    assert fields[1].key == 'parser.add_argument.--node.help'
    assert all(field.pending is None for field in fields)


def test_dynamic_fields_are_not_evaluated_or_claimed_as_checked():
    source = '''parser.add_argument('--node', help=lookup_secret())
parser.add_argument('--state', help=f'Status: {state}')
parser.add_argument('--count', help='Count: ' + str(count))
parser.add_argument('--title', help=title, default='Some default text')
print('This output is outside parser-help coverage.')'''
    fields = argparse_help(source)
    assert len(fields) == 4
    assert all(field.text is None and field.pending == 'dynamic help field' for field in fields)


def test_hidden_help_is_excluded_and_empty_help_is_reported():
    fields = argparse_help("parser.add_argument('--hidden', help=argparse.SUPPRESS); "
                           "parser.add_argument('--empty', help='')")
    assert len(fields) == 1
    assert fields[0].pending == 'empty help field'


def test_invalid_source_fails_instead_of_reporting_no_prose():
    with pytest.raises(ValueError, match='invalid Python at line 1'):
        argparse_help("parser.add_argument('--node', help='unfinished")
