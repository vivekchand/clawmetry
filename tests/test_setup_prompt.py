"""The setup prompt must not teach an agent something untrue.

This is the one artefact in the product whose reader is a coding agent
rather than a person, which changes what "wrong" costs. A person reading
a stale doc notices the header does not work and goes looking. An agent
reading a stale prompt writes the wrong header confidently, reports
success, and the failure surfaces days later as "ClawMetry never showed
my CI runs".

So the prompt is generated from ``clawmetry.ingest_contract`` -- the same
declaration the server validates against -- and these guards check that
it stays that way.
"""
from __future__ import annotations

import importlib

import pytest


@pytest.fixture
def sp():
    import clawmetry.setup_prompt as mod

    importlib.reload(mod)
    return mod


# ── it says what the server accepts ─────────────────────────────────────

def test_prompt_names_the_headers_the_server_actually_reads(sp):
    from clawmetry import ingest_auth, ingest_contract

    text = sp.render("my-engine")
    for header in (ingest_contract.HEADER_KEY,
                   ingest_contract.HEADER_RUNTIME,
                   ingest_contract.HEADER_ENV):
        assert header in text, f"the prompt never mentions {header}"
    # and those are the names the gate looks for, not a parallel set
    assert ingest_auth.HEADER_KEY == ingest_contract.HEADER_KEY


def test_prompt_invents_no_header_of_its_own(sp):
    """The guard that actually catches drift.

    Checking that each declared header APPEARS is too weak: a prompt can
    name the right header in prose and still hand the agent a wrong one
    in the config block. Proven by mutation -- swapping the key header
    for ``x-clawmetry-apikey`` left every other assertion in this file
    green, because the correct name still appeared in the rules section.

    So this reads the other direction: every ``x-clawmetry-*`` token the
    prompt contains must be a header the contract declares.
    """
    import re

    from clawmetry import ingest_contract

    declared = {h["name"].lower() for h in ingest_contract.HEADERS}
    for variant in (sp.render("my-engine"), sp.render("my-engine", key="cmk_a_b")):
        found = set(re.findall(r"x-clawmetry-[a-z-]+", variant.lower()))
        unknown = found - declared
        assert not unknown, (
            f"the prompt tells an agent to send {sorted(unknown)}, which the "
            "server does not read. A header the prompt invents is the exact "
            "failure this generator exists to prevent."
        )
        assert found, "the prompt names no ClawMetry header at all"


def test_renaming_a_header_changes_the_prompt(sp, monkeypatch):
    """The whole point. If the prompt held its own copy of the header
    names, a rename would ship a prompt that teaches the old one."""
    monkeypatch.setattr(sp, "HEADER_KEY", "x-clawmetry-renamed")
    assert "x-clawmetry-renamed" in sp.render("my-engine")


def test_prompt_states_the_real_body_cap(sp):
    from clawmetry.ingest_contract import MAX_BODY_BYTES

    mb = MAX_BODY_BYTES // (1024 * 1024)
    assert f"{mb} MB" in sp.render("my-engine")


def test_endpoints_in_the_prompt_are_declared_surfaces(sp):
    from clawmetry import ingest_contract

    text = sp.render("my-engine")
    declared = {s["path"] for s in ingest_contract.SURFACES}
    assert "/v1/traces" in text and "/v1/traces" in declared


# ── the negative space, which is the useful half ────────────────────────

def _flat(text: str) -> str:
    """Whitespace-collapsed, lower-cased.

    The prompt is hard-wrapped for terminals, so a phrase can straddle a
    newline. Asserting on the raw string tests the line breaks rather
    than the meaning -- and a guard that a reflow can silently satisfy is
    a guard that stops guarding.
    """
    return " ".join(text.split()).lower()


def test_prompt_forbids_the_mistakes_agents_actually_make(sp):
    """Each of these lines exists because an unstated constraint is one
    an agent will violate helpfully."""
    text = _flat(sp.render("my-engine"))
    assert "not in a query" in text, "must forbid the key as a query param"
    assert "bearer" in text, "must forbid Authorization: Bearer"
    assert "does not exist" in text, "must forbid inventing config keys"
    assert "it watches, it does not change" in text, (
        "must state that this is observability -- an agent told to 'set up "
        "monitoring' will otherwise happily edit the agent's own behaviour"
    )


def test_placeholder_is_obviously_not_a_key(sp):
    """An agent that leaves the placeholder in must produce a clean 401,
    not something that looks plausible enough to debug for an hour."""
    text = sp.render("my-engine")
    assert sp.KEY_PLACEHOLDER in text
    assert not sp.KEY_PLACEHOLDER.startswith("cmk_"), (
        "a placeholder shaped like a real key is one an agent will assume "
        "is real"
    )
    flat = _flat(text)
    assert "placeholder, not a key" in flat
    assert "invent a key" in flat


def test_a_real_key_is_substituted_and_the_warning_changes(sp):
    with_key = sp.render("my-engine", key="cmk_1234abcd_secret")
    assert "cmk_1234abcd_secret" in with_key
    assert sp.KEY_PLACEHOLDER not in with_key
    assert "copy it exactly" in _flat(with_key)


# ── verification is part of the task, not an afterthought ───────────────

def test_prompt_makes_the_agent_check_its_own_work(sp):
    """An agent that can verify fails loudly instead of silently."""
    text = sp.render("my-engine")
    assert "/api/otel-status" in text
    assert "do not report success" in _flat(text)
    assert "401" in text and "403" in text, (
        "the prompt should name the two auth failures by code, since those "
        "are what the agent will actually see"
    )


# ── the seam: no runtime knowledge in OSS ───────────────────────────────

def test_module_hardcodes_no_runtime_name(sp):
    """Runtime-specific OTel knowledge lives in profiles, which paid
    runtimes register from clawmetry-pro. A vendor name compiled into
    this file would put it on the wrong side of that seam."""
    import pathlib

    src = pathlib.Path(sp.__file__).read_text().lower()
    for vendor in ("claude_code", "codex", "cursor", "openclaw", "copilot"):
        assert vendor not in src, (
            f"{vendor!r} is hardcoded in setup_prompt.py. Runtime-specific "
            "values belong in an OTel profile, not in the OSS generator."
        )


def test_unknown_runtime_still_renders_a_working_prompt(sp):
    """An in-house engine is a supported case and must not get a worse
    prompt than a runtime we ship an adapter for."""
    text = sp.render("totally-unknown-engine")
    assert "/v1/traces" in text
    assert "totally-unknown-engine" in text


def test_no_runtime_at_all_still_renders(sp):
    text = sp.render("")
    assert "/v1/traces" in text
    assert "this agent" in _flat(text)


def test_profile_instrumenter_is_offered_when_one_exists(sp, monkeypatch):
    """A runtime whose native exporter ClawMetry can configure should be
    told to try that first, rather than hand-editing exporter config."""
    class _Prof:
        label = "Example Runtime"
        instrumenter = object()

    monkeypatch.setattr(sp, "_profile", lambda rt: _Prof())
    text = sp.render("example")
    assert "clawmetry instrument example" in text
    assert "Example Runtime" in text


def test_no_instrument_offer_without_a_profile(sp, monkeypatch):
    """Offering a command that does nothing is worse than not offering it."""
    monkeypatch.setattr(sp, "_profile", lambda rt: None)
    assert "clawmetry instrument" not in sp.render("example")


# ── the HTTP surface ────────────────────────────────────────────────────

def test_endpoint_rejects_a_junk_runtime():
    from flask import Flask

    import routes.meta as meta

    app = Flask(__name__)
    app.register_blueprint(meta.bp_otel)
    client = app.test_client()

    bad = client.get("/api/setup-prompt?runtime=../etc/passwd")
    assert bad.status_code == 400
    assert bad.get_json()["error"] == "bad_runtime"

    ok = client.get("/api/setup-prompt?runtime=my-engine")
    assert ok.status_code == 200
    body = ok.get_json()
    assert "/v1/traces" in body["prompt"]
    assert body["runtime"] == "my-engine"


def test_endpoint_never_returns_a_real_key():
    """Secrets are stored only as a SHA-256, so this could not hand one
    back even if it tried -- but an assertion is cheaper than trusting
    that nobody adds a convenience later."""
    from flask import Flask

    import routes.meta as meta

    app = Flask(__name__)
    app.register_blueprint(meta.bp_otel)
    res = app.test_client().get("/api/setup-prompt?runtime=my-engine")
    assert "cmk_" not in res.get_json()["prompt"]


# ── the two-list trap ───────────────────────────────────────────────────

def test_every_registered_subcommand_is_reachable():
    """Registering a parser is not enough to ship a command.

    ``clawmetry/cli.py`` gates dispatch on a hardcoded ``_subcmds``
    tuple: a command with a parser but no entry there falls through to
    the dashboard's argparse and dies with "invalid choice", which reads
    like the command was never written. That is how `setup-prompt`
    behaved when it was first added, and it is the same shape as the
    runtime trap CLAUDE.md warns about -- an adapter is inert until it is
    named in BOTH lists.

    This guard is general on purpose. Asserting only that
    ``setup-prompt`` is present would not have prevented the next one.
    """
    import pathlib
    import re

    src = pathlib.Path(__file__).resolve().parents[1] / "clawmetry" / "cli.py"
    text = src.read_text()

    block = re.search(r"_subcmds = \((.*?)\)\n", text, re.S)
    assert block, "_subcmds is no longer a literal tuple; update this guard"
    allowed = set(re.findall(r'"([a-z0-9-]+)"', block.group(1)))

    # Some commands are dispatched from argv BEFORE argparse runs (hooks,
    # hook, instrument, trace, mcp) so they can skip the ~300ms dashboard
    # import. Those are reachable too -- their parser exists only so
    # `--help` has something to print -- so they count as allowed.
    allowed |= set(re.findall(r'sys\.argv\[1\] == "([a-z0-9-]+)"', text))
    try:
        from clawmetry.cli_cmds import AGENT_COMMANDS
        allowed |= set(AGENT_COMMANDS)
    except Exception:
        pass

    # Top-level parsers only: `sub.add_parser(...)`, not `<x>_sub.add_parser`.
    registered = set(re.findall(r'(?<![\w_])sub\.add_parser\(\s*\n?\s*"([a-z0-9-]+)"', text))

    missing = registered - allowed
    assert not missing, (
        f"these subcommands have a parser but are not in _subcmds, so they "
        f"fall through to the dashboard parser and fail with 'invalid "
        f"choice': {sorted(missing)}"
    )
