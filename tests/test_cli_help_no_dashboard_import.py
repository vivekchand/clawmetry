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
