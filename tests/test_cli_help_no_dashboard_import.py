"""`clawmetry <subcmd> --help` must never import dashboard (#5108, #5309).

dashboard.py calls get_store() at module level when CLAWMETRY_ROLE=dashboard
is set, and on some Python 3.9/Linux runners DuckDB's init SIGSEGVs in that
path. `--version` already short-circuited before the import for exactly this
reason. A subcommand's own `--help`/`-h` (e.g. `clawmetry connect --help`) is
printed entirely by argparse's subparser -h action and never needs dashboard
or the store either -- but main() used to import dashboard unconditionally,
before it even looked at argv[1], so every subcommand's --help paid for (and
in the Conformance Heartbeat, twice crashed on -- #5309) an import it never
needed. `status`/`sync --help` happened to pass in both incidents while
`connect --help` segfaulted, which is consistent with a native init that can
land on any subcommand's dashboard import, not something specific to
`connect`.

Bare `clawmetry --help`/`-h` (no subcommand) was still missing this guard
(#5492): argv[1] is the string "--help" itself, not a member of `_subcmds`,
so the check that catches `<subcmd> --help` never matched it and the process
fell all the way through to the dashboard import just to print help text --
the published-wheel Conformance Heartbeat caught this crashing on
`pypi-install (ubuntu-latest, py3.9)` with `free(): invalid pointer` /
exit 134 on `clawmetry --help`, before the per-subcommand step even ran.
"""
import builtins
import sys

import pytest

import clawmetry.cli as cli


@pytest.mark.parametrize("subcmd", ["status", "sync", "connect", "uninstall"])
def test_subcommand_help_does_not_import_dashboard(subcmd, monkeypatch):
    monkeypatch.setattr(sys, "argv", ["clawmetry", subcmd, "--help"])
    monkeypatch.delitem(sys.modules, "dashboard", raising=False)
    real_import = builtins.__import__
    imported = []

    def _spy(name, *args, **kwargs):
        if name == "dashboard" or name.startswith("dashboard."):
            imported.append(name)
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", _spy)

    with pytest.raises(SystemExit) as exc:
        cli.main()

    assert exc.value.code == 0
    assert not imported, (
        f"`clawmetry {subcmd} --help` imported dashboard ({imported}); "
        "a subcommand's own --help must be printed by argparse alone."
    )


def test_subcommand_help_still_prints_usage(capsys, monkeypatch):
    """The short-circuit must not swallow the actual help text."""
    monkeypatch.setattr(sys, "argv", ["clawmetry", "connect", "--help"])
    with pytest.raises(SystemExit) as exc:
        cli.main()
    assert exc.value.code == 0
    out = capsys.readouterr().out.lower()
    assert "usage: clawmetry connect" in out


@pytest.mark.parametrize("flag", ["--help", "-h"])
def test_bare_help_does_not_import_dashboard(flag, monkeypatch):
    """Bare `clawmetry --help`/`-h` (#5492): argv[1] IS the flag, not a
    subcommand, so it needs its own guard distinct from the one above."""
    monkeypatch.setattr(sys, "argv", ["clawmetry", flag])
    monkeypatch.delitem(sys.modules, "dashboard", raising=False)
    real_import = builtins.__import__
    imported = []

    def _spy(name, *args, **kwargs):
        if name == "dashboard" or name.startswith("dashboard."):
            imported.append(name)
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", _spy)

    with pytest.raises(SystemExit) as exc:
        cli.main()

    assert exc.value.code == 0
    assert not imported, (
        f"`clawmetry {flag}` imported dashboard ({imported}); bare top-level "
        "help must be printed by argparse alone, same as a subcommand's."
    )


def test_bare_help_still_prints_usage(capsys, monkeypatch):
    """The bare-help short-circuit must not swallow the actual help text."""
    monkeypatch.setattr(sys, "argv", ["clawmetry", "--help"])
    with pytest.raises(SystemExit) as exc:
        cli.main()
    assert exc.value.code == 0
    out = capsys.readouterr().out.lower()
    assert "usage: clawmetry" in out
