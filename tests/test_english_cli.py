"""AC-STE-002.1, AC-STE-001.3: check rendered help and retain option meaning."""
import argparse
import builtins
import sys

import pytest

from clawmetry.english import check_text


@pytest.fixture(scope='session')
def server():
    yield None


@pytest.fixture
def cli_parser(monkeypatch, capsys):
    monkeypatch.delenv('CLAWMETRY_INTERCEPT', raising=False)
    monkeypatch.setenv('CLAWMETRY_NO_STALE_WARN', '1')
    import clawmetry.cli as cli
    import clawmetry.net as net
    monkeypatch.setattr(net, 'configure_outbound_network', lambda **kwargs: None)
    monkeypatch.setattr(sys, 'argv', ['clawmetry', '--help'])
    real_import = builtins.__import__

    def guarded_import(name, *args, **kwargs):
        assert name not in ('dashboard', 'clawmetry.local_store', 'clawmetry.sync'), name
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, '__import__', guarded_import)
    parsers = []
    original_help = argparse.ArgumentParser.print_help

    def capture(parser, *args, **kwargs):
        parsers.append(parser)
        return original_help(parser, *args, **kwargs)

    monkeypatch.setattr(argparse.ArgumentParser, 'print_help', capture)
    with pytest.raises(SystemExit) as stopped:
        cli.main()
    assert stopped.value.code == 0
    assert 'usage: clawmetry' in capsys.readouterr().out
    assert len(parsers) == 1
    return parsers[0]


def subcommands(parser):
    return next(action.choices for action in parser._actions
                if isinstance(action, argparse._SubParsersAction))


def test_all_central_help_screens_render_with_checked_prose(cli_parser):
    pending = [cli_parser]
    checked = 0
    while pending:
        parser = pending.pop()
        assert 'usage: clawmetry' in parser.format_help()
        formatter = parser._get_formatter()
        for action in parser._actions:
            if isinstance(action, argparse._SubParsersAction):
                pending.extend(action.choices.values())
                help_actions = action._choices_actions
            else:
                help_actions = [action]
            for help_action in help_actions:
                if help_action.help is None or help_action.help == argparse.SUPPRESS:
                    continue
                text = formatter._expand_help(help_action)
                assert not check_text(text, 'instruction'), (parser.prog, help_action.dest, text)
                checked += 1
    assert checked >= 182  # Includes argparse's own help actions.


@pytest.mark.parametrize('command, fragments', [
    ('setup', ['--local', '--cloud', 'without creating a cloud account']),
    ('connect', ['--keep-local', '--defer-sync', 'cloud sync disabled', 'cloud sync paused']),
    ('update', ['CLAWMETRY_AUTO_UPDATE', 'CLAWMETRY_AUTOUPDATE_MIN_AGE_HOURS', 'newest release that satisfies']),
    ('uninstall', ['--keep-data', '--unattended', 'code 0 even if some removal steps fail', 'Keep the DuckDB and history databases']),
    ('activate', ['--file', 'CLAW1.', 'shell history', 'Mutually exclusive']),
])
def test_help_keeps_conditions_and_important_options(cli_parser, command, fragments):
    rendered = ' '.join(subcommands(cli_parser)[command].format_help().split())
    for fragment in fragments:
        assert fragment in rendered


def test_top_level_examples_name_the_executable(cli_parser):
    rendered = ' '.join(cli_parser.format_help().split())
    assert 'clawmetry mcp install' in rendered
    assert 'clawmetry instrument --help' in rendered
    assert 'clawmetry hook claude-code --base' in rendered
