"""Agent-facing read CLI — `clawmetry sessions|activity|waste|progress|usage|selfevolve`.

Phase 1 of the Agent CLI (docs/CLI.md): the observability
surface the UI serves, readable from a terminal by humans, CI, and AI agents
closing a self-improve loop ("read my own telemetry, find waste, fix it").

Dispatched from ``clawmetry.cli.main`` on a fast path BEFORE the dashboard
import (~300 ms) so `clawmetry sessions --json` answers in tens of ms and the
process never tags itself CLAWMETRY_ROLE=dashboard — which lets
``local_store.get_store(read_only=True)`` pick the right transport on its own:
daemon HTTP proxy when the sync daemon owns the writer lock, direct read-only
DuckDB in single-process installs.

Grammar (one rule, no exceptions): ``clawmetry NOUN [ID] [read-facet flags]``.
Everything here is read-only; mutations stay in their existing commands.
"""
from __future__ import annotations

# Nouns owned by this package. Checked against sys.argv[1] in cli.main's fast
# path; must never collide with the legacy _subcmds tuple in cli.py.
AGENT_COMMANDS = (
    "sessions",
    "activity",
    "waste",
    "progress",
    "usage",
    "selfevolve",
)


def dispatch(argv: list[str]) -> int:
    """Parse + run one agent-CLI command. Returns the process exit code."""
    from clawmetry.cli_cmds import _common

    try:
        parser = _common.build_parser()
        args = parser.parse_args(argv)
        handler = getattr(args, "_handler", None)
        if handler is None:  # pragma: no cover - argparse enforces a command
            parser.print_help()
            return _common.EXIT_USAGE
        return int(handler(args) or 0)
    except _common.CliError as err:
        return _common.fail(err)
    except KeyboardInterrupt:
        return _common.EXIT_OK
    except BrokenPipeError:
        # `clawmetry activity | head` — downstream closed the pipe; not an error.
        return _common.EXIT_OK
    except SystemExit as exc:  # argparse --help / usage errors
        code = exc.code
        if code is None:
            return _common.EXIT_OK
        return _common.EXIT_USAGE if code == 2 else int(code)
    except Exception as exc:  # never crash on bad input (repo rule)
        return _common.fail(
            _common.CliError("internal", f"unexpected error: {exc}", _common.EXIT_ERROR)
        )
