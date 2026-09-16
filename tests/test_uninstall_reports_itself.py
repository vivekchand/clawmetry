"""`clawmetry uninstall` tells the install registry it is going away.

REQ-OGV-AIH-004 (Factory requirement d30b15cc). The registry counted
arrivals and never departures: production held zero `uninstall` events while
the cloud has accepted that event all along. With the machine's row purged
and no record of why, the account read "never installed" and was sent
install instructions.

Criterion -> tests:

* AC-OGV-AIH-004.1 -- test_uninstall_sends_one_lifecycle_ping,
  test_opting_out_sends_nothing, test_the_uninstall_command_reports_itself
* AC-OGV-AIH-004.2 -- test_a_failing_ping_never_breaks_the_uninstall
"""

import inspect

import pytest

import clawmetry.cli as cli
import clawmetry.telemetry as telemetry


def test_uninstall_sends_one_lifecycle_ping(monkeypatch):
    """One ping, named `uninstall`, carrying a real version."""
    sent = []
    monkeypatch.setattr(
        telemetry, "ping_event",
        lambda event, version="unknown", extra=None: sent.append((event, version)))

    cli._report_uninstall()

    assert [event for event, _v in sent] == ["uninstall"]
    assert sent[0][1] and sent[0][1] != "unknown", (
        "the ping must carry the installed version; `_get_version` does not "
        "exist in cli.py and a NameError here would be swallowed silently"
    )


def test_opting_out_sends_nothing(monkeypatch):
    """Opt-out is total: the shared ping path refuses before any request."""
    posted = []
    monkeypatch.setenv("CLAWMETRY_NO_TELEMETRY", "1")
    monkeypatch.setattr(telemetry, "_post", lambda *a, **k: posted.append(a))

    cli._report_uninstall()

    assert posted == []


def test_a_failing_ping_never_breaks_the_uninstall(monkeypatch):
    """The uninstall is the product; the report is bookkeeping."""
    def _boom(*_a, **_k):
        raise OSError("network unreachable")

    monkeypatch.setattr(telemetry, "ping_event", _boom)
    cli._report_uninstall()  # must not raise


def test_the_uninstall_command_reports_itself():
    """The command actually calls it: a helper nothing invokes reports
    nothing, which is the state this requirement exists to fix."""
    assert "_report_uninstall()" in inspect.getsource(cli._cmd_uninstall)
