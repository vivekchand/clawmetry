"""Guards for clawmetry/runtime_records.py — the table that lets a cost
surface say "not recorded by this runtime" instead of rendering $0.00.

The table is only worth anything if it stays true. These guards are
auto-discovering: they walk the catalogue and the doc rather than an
allowlist, so a NEW runtime fails them until someone decides what it records,
and an EDITED doc row fails them until the verdict is re-derived.

Acceptance criteria proven here (docs/acceptance_criteria.json):

* AC-OBS-CEA-001.2 -- when a cost value cannot be determined the system
  identifies it as unavailable rather than reporting a zero:
  ``test_token_blind_runtime_suppresses_its_zero``,
  ``test_unverified_runtime_claims_nothing``,
  ``test_efficiency_endpoint_says_not_recorded_for_a_token_blind_runtime``,
  ``test_usage_endpoint_attaches_coverage_when_scoped``. The companion guard
  that a runtime which CAN report cost keeps its honest zero is
  ``test_idle_but_capable_runtime_keeps_its_zero`` -- "unavailable" must not
  swallow a real $0.
"""
import re

import pytest

from clawmetry import runtime_records as rr
from clawmetry.entitlements import ALL_RUNTIMES, RUNTIME_COUNT, RUNTIME_LABELS


def _doc(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def _table_row(text, label):
    """The compatibility.md table row whose first cell is exactly ``label``."""
    for line in text.splitlines():
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if cells and cells[0] == label:
            return line
    return None


def test_every_catalogued_runtime_has_a_record():
    """A new runtime cannot ship without someone deciding what it records.

    Without this, a 27th runtime silently inherits the all-UNKNOWN fallback
    and its Cost tab goes back to rendering an unexplained blank.
    """
    missing = sorted(set(ALL_RUNTIMES) - set(rr.RUNTIME_RECORDS))
    assert not missing, f"runtimes with no runtime_records entry: {missing}"


def test_no_records_for_runtimes_that_are_not_catalogued():
    extra = sorted(set(rr.RUNTIME_RECORDS) - set(ALL_RUNTIMES))
    assert not extra, f"runtime_records entries for unknown runtimes: {extra}"


@pytest.mark.parametrize("runtime", sorted(rr.RUNTIME_RECORDS))
def test_states_are_valid(runtime):
    entry = rr.RUNTIME_RECORDS[runtime]
    for signal in rr.SIGNALS:
        assert entry[signal] in rr._STATES, (
            f"{runtime}.{signal} = {entry[signal]!r} is not a known state"
        )


@pytest.mark.parametrize("runtime", sorted(rr.RUNTIME_RECORDS))
def test_derived_cost_requires_tokens_on_disk(runtime):
    """Cost is derived by pricing tokens. Claiming DERIVED cost without
    tokens on disk would mean claiming a number with nothing behind it."""
    entry = rr.RUNTIME_RECORDS[runtime]
    if entry["cost"] == rr.DERIVED:
        assert entry["tokens"] == rr.ON_DISK, (
            f"{runtime} claims derived cost but records no tokens"
        )


@pytest.mark.parametrize("runtime", sorted(rr.RUNTIME_RECORDS))
def test_unavailable_cost_is_not_secretly_derivable(runtime):
    """If tokens are on disk, cost is derivable — so calling cost
    UNAVAILABLE would suppress a number we could honestly show."""
    entry = rr.RUNTIME_RECORDS[runtime]
    if entry["cost"] == rr.UNAVAILABLE:
        assert entry["tokens"] != rr.ON_DISK, (
            f"{runtime} has tokens on disk, so its cost is derivable, not unavailable"
        )


@pytest.mark.parametrize("runtime", sorted(rr.RUNTIME_RECORDS))
def test_verdict_is_grounded_in_the_docs(runtime):
    """Each verdict cites a sentence from that runtime's documented row.

    Edit the doc and this fails, which is the point: the table cannot drift
    away from the compatibility matrix we actually maintain.
    """
    entry = rr.RUNTIME_RECORDS[runtime]
    text = _doc(entry["doc_file"])
    evidence = entry["evidence"]
    assert evidence, f"{runtime} cites no evidence"
    if entry["doc_file"].endswith("compatibility.md"):
        label = entry["doc_label"] or RUNTIME_LABELS[runtime]
        row = _table_row(text, label)
        assert row is not None, (
            f"{runtime}: no row titled {label!r} in docs/compatibility.md"
        )
        assert evidence in row, (
            f"{runtime}: cited evidence {evidence!r} is no longer in its "
            f"docs/compatibility.md row — re-derive the verdict"
        )
    else:
        assert evidence in text, (
            f"{runtime}: cited evidence {evidence!r} is no longer in "
            f"{entry['doc_file']}"
        )


@pytest.mark.parametrize("runtime", sorted(rr.RUNTIME_RECORDS))
def test_every_runtime_explains_itself(runtime):
    """A "not recorded" badge with no reason is barely better than a zero."""
    note = rr.RUNTIME_RECORDS[runtime]["note"]
    assert note and len(note) > 40, f"{runtime} has no operator-facing note"


def test_compatibility_doc_states_the_real_runtime_count():
    text = _doc("docs/compatibility.md")
    m = re.search(r"ClawMetry observes (\d+) AI-agent runtimes", text)
    assert m, "compatibility.md no longer states a runtime count"
    assert int(m.group(1)) == RUNTIME_COUNT, (
        f"compatibility.md says {m.group(1)} runtimes; the catalogue has "
        f"{RUNTIME_COUNT}"
    )


# ── the payload contract every surface depends on ────────────────────────

def test_token_blind_runtime_suppresses_its_zero():
    p = rr.coverage_payload("cursor")
    assert p["status"] == "not_recorded"
    assert p["suppress_zero"] is True
    assert p["headline"] == "Not recorded by Cursor"
    assert p["detail"]
    assert "cost" in p["unrecorded"]


def test_idle_but_capable_runtime_keeps_its_zero():
    """OpenClaw records cost fine. An empty window means zero spend, and a
    zero is the true answer — it must NOT be suppressed."""
    p = rr.coverage_payload("openclaw")
    assert p["status"] == "no_activity"
    assert p["suppress_zero"] is False


def test_data_present_always_wins():
    p = rr.coverage_payload("cursor", has_data=True)
    assert p["status"] == "ok"
    assert p["suppress_zero"] is False


def test_unverified_runtime_claims_nothing():
    p = rr.coverage_payload("devin")
    assert p["status"] == "unverified"
    assert p["suppress_zero"] is True
    assert "Not verified" in p["headline"]


def test_derived_cost_is_labelled_as_an_estimate():
    assert rr.coverage_payload("claude_code", has_data=True)["cost_is_estimate"] is True
    assert rr.coverage_payload("opencode", has_data=True)["cost_is_estimate"] is False


def test_unknown_runtime_does_not_raise():
    p = rr.coverage_payload("no_such_runtime_at_all")
    assert p["status"] == "unverified"
    assert p["records"]["cost"] == rr.UNKNOWN


def test_is_recorded_reads_both_on_disk_and_derived():
    assert rr.is_recorded("opencode", "cost") is True     # runtime's own number
    assert rr.is_recorded("claude_code", "cost") is True   # priced by us
    assert rr.is_recorded("cursor", "cost") is False
    assert rr.is_recorded("devin", "cost") is False


# ── endpoint wiring: the surfaces that used to render the zero ───────────

@pytest.fixture()
def usage_app(monkeypatch):
    """Flask app with routes.usage mounted and its store read stubbed to an
    EMPTY rollup — the exact condition that used to paint $0.00 and "grade
    appears after about a day" for a runtime that will never report cost."""
    from flask import Flask

    import routes.usage as usage_mod

    monkeypatch.setattr(usage_mod, "_ls_call", lambda *a, **k: [])
    app = Flask(__name__)
    app.register_blueprint(usage_mod.bp_usage)
    return app


def test_efficiency_endpoint_says_not_recorded_for_a_token_blind_runtime(usage_app):
    body = usage_app.test_client().get("/api/efficiency?runtime=cursor").get_json()
    assert body["insufficient_data"] is True
    cov = body["coverage"]
    assert cov["status"] == "not_recorded"
    assert cov["suppress_zero"] is True
    assert cov["headline"] == "Not recorded by Cursor"
    assert cov["detail"]


def test_efficiency_endpoint_keeps_the_honest_zero_for_a_capable_runtime(usage_app):
    """OpenClaw records cost. An empty window is a real, reportable $0 and
    must NOT be dressed up as "this runtime does not support it"."""
    body = usage_app.test_client().get("/api/efficiency?runtime=openclaw").get_json()
    cov = body["coverage"]
    assert cov["status"] == "no_activity"
    assert cov["suppress_zero"] is False


def test_efficiency_node_wide_attaches_no_verdict(usage_app):
    """A node mixes runtimes, so there is no single honest verdict."""
    body = usage_app.test_client().get("/api/efficiency").get_json()
    assert body.get("coverage") is None


def test_usage_endpoint_attaches_coverage_when_scoped():
    """/api/usage's fast path carries the same verdict, so the Cost tab and
    the Efficiency card cannot disagree about the same runtime."""
    import routes.usage as usage_mod

    cov = usage_mod._runtime_coverage("cursor", has_data=False)
    assert cov["status"] == "not_recorded"
    assert usage_mod._runtime_coverage("cursor", has_data=True)["status"] == "ok"
    assert usage_mod._runtime_coverage("", has_data=False) is None
    assert usage_mod._runtime_coverage("all", has_data=False) is None
