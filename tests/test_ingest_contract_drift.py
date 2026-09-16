"""The ingest contract, the server and the doc must agree.

Four things describe this surface -- the server, ``docs/INGEST.md``, the
per-runtime setup prompts, and the public reference on the landing site.
Hand-maintaining four descriptions of one contract is four chances to
drift, and the drift is worst in the prompts: a prompt that teaches an
agent a header we do not accept is worse than shipping no prompt, because
the agent writes it confidently and the failure is silent.

So the contract is data, the doc is generated, and these guards fail when
any of them disagrees.

The load-bearing test here is the last one. Declaring "we read
``gen_ai.usage.cache_read.input_tokens``" is only worth printing if
something checks it against the mapper -- and when that check was first
written it found that we did NOT read it (#5685), which had been silently
pricing cached tokens as free.
"""
from __future__ import annotations

import pathlib
import subprocess
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]


# ── the doc is generator output ─────────────────────────────────────────

def test_committed_doc_matches_the_generator():
    out = subprocess.run(
        [sys.executable, "scripts/gen_ingest_doc.py", "--check"],
        cwd=ROOT, capture_output=True, text=True,
    )
    assert out.returncode == 0, (
        "docs/INGEST.md is stale. Run: python3 scripts/gen_ingest_doc.py\n"
        + out.stderr
    )


def test_doc_says_it_is_generated():
    """Someone will open it and start typing otherwise."""
    text = (ROOT / "docs" / "INGEST.md").read_text()
    assert "GENERATED FILE" in text
    assert "clawmetry/ingest_contract.py" in text


# ── the server reads the contract, not its own copy ─────────────────────

def test_ingest_auth_uses_the_declared_constants():
    """If the gate kept private copies of the header names, the doc could
    say one thing and the server enforce another -- which is the whole
    failure this module exists to prevent."""
    from clawmetry import ingest_auth, ingest_contract

    assert ingest_auth.HEADER_KEY is ingest_contract.HEADER_KEY
    assert ingest_auth.HEADER_RUNTIME is ingest_contract.HEADER_RUNTIME
    assert ingest_auth.HEADER_ENV is ingest_contract.HEADER_ENV
    assert ingest_auth.MAX_BODY_BYTES == ingest_contract.MAX_BODY_BYTES


def test_every_declared_surface_is_a_real_route():
    """A path in the reference that 404s is worse than an undocumented
    one: it sends a reader to debug their own request."""
    from clawmetry import ingest_contract

    sources = "\n".join(
        (ROOT / p).read_text()
        for p in ("routes/meta.py", "routes/runtime_ingest.py")
    )
    for surface in ingest_contract.SURFACES:
        path = surface["path"]
        # Route decorators spell the variable part <run_id>; the doc uses
        # <id> for readability. Compare on the stable prefix.
        stem = path.split("<")[0].rstrip("/")
        assert stem in sources, (
            f"{path} is documented but no route in routes/meta.py or "
            f"routes/runtime_ingest.py serves {stem!r}."
        )


def test_declared_response_codes_are_the_ones_we_return():
    from clawmetry import ingest_contract

    declared = {code for code, _ in ingest_contract.RESPONSES}
    for expected in (200, 400, 401, 403, 413):
        assert expected in declared, f"{expected} is returned but undeclared"


# ── the GenAI list is checked against the mapper ────────────────────────

def _mapper_source() -> str:
    return (ROOT / "dashboard.py").read_text()


@pytest.mark.parametrize("attr", [a for a, _ in __import__(
    "clawmetry.ingest_contract", fromlist=["GENAI_READ"]).GENAI_READ])
def test_every_attribute_declared_read_is_named_in_the_mapper(attr):
    """The guard that earns this file.

    Claiming to read an attribute is cheap; the claim is only worth
    printing if something checks it. When this was first written it
    failed on the prompt-cache names -- we were advertising a convention
    we did not implement, and cached tokens were priced as free (#5685).
    """
    assert f'"{attr}"' in _mapper_source(), (
        f"the ingest contract says we read {attr}, but dashboard.py never "
        "names it. Either wire it up, or move it to GENAI_NOT_READ -- "
        "advertising an attribute we ignore is how cached tokens came to "
        "be priced as free."
    )


@pytest.mark.parametrize("attr", [a for a, _ in __import__(
    "clawmetry.ingest_contract", fromlist=["GENAI_NOT_READ"]).GENAI_NOT_READ])
def test_attributes_declared_unread_really_are_unread(attr):
    """The other direction. Someone wiring one of these up should have to
    move it to the read list in the same change, so the published
    reference is never behind the code either."""
    assert f'"{attr}"' not in _mapper_source(), (
        f"{attr} is now read by dashboard.py but the contract still lists "
        "it as unread. Move it to GENAI_READ and regenerate the doc."
    )


def test_read_and_unread_lists_are_disjoint():
    from clawmetry import ingest_contract

    read = {a for a, _ in ingest_contract.GENAI_READ}
    unread = {a for a, _ in ingest_contract.GENAI_NOT_READ}
    assert not (read & unread), f"declared both read and unread: {read & unread}"


# ── the non-goal is stated, because it keeps being asked for ────────────

def test_doc_states_what_we_do_not_accept():
    """Every few months someone asks for syslog ingestion. The reference
    should answer that without a meeting."""
    text = (ROOT / "docs" / "INGEST.md").read_text()
    assert "does not accept" in text.lower()
    for fmt in ("syslog", "CEF"):
        assert fmt in text
