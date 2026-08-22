"""Guards for the acceptance-criteria traceability gate itself.

``scripts/check_ac_coverage.py`` is the thing standing between "we wrote a
requirement" and "we can fail a build when the code stops meeting it". A gate
nobody tests is a gate that quietly stops gating, so this file pins its
behaviour -- especially the declaration rule, which had a real loophole in its
first draft.

This file deliberately declares no acceptance criteria of its own: it tests
the harness, not the product.
"""

from __future__ import annotations

import importlib.util
import json
import os

import pytest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT = os.path.join(REPO_ROOT, "scripts", "check_ac_coverage.py")


def _load_module():
    spec = importlib.util.spec_from_file_location("check_ac_coverage", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def gate():
    return _load_module()


# ── the declaration rule ────────────────────────────────────────────────────

@pytest.mark.parametrize("line", [
    "* AC-OBS-CEA-002.3 -- cache hit rate is surfaced",
    "  * AC-OBS-LADC-001.2 -- tamper is reported as failure",
    "- AC-GOV-ERS-001.1 -- entitled runtime is normalized",
    "AC-OBS-001.1 -- activity is presented",
    "+ AC-RSO-CWD-001.3 -- event rows carry the session cwd",
])
def test_declaration_forms_are_recognised(gate, line):
    assert gate.AC_DECLARATION.findall(line), "should count as a declaration"


@pytest.mark.parametrize("line", [
    # The exact loophole that shipped in the first draft of this gate: a file
    # saying it does NOT cover a criterion marked that criterion covered.
    "Deliberately NOT claimed here: AC-OBS-CEA-001.2 (undeterminable cost).",
    "See AC-OBS-CEA-001.3 for the time-scope rule.",
    "# TODO: someday cover AC-GOV-002.4",
    'assert body["reason"] == "AC-OBS-002.3"',
])
def test_prose_mentions_do_not_count_as_coverage(gate, line):
    assert not gate.AC_DECLARATION.findall(line), (
        "a passing mention must never count as coverage -- that is how a gate "
        "starts reporting a number nobody should trust"
    )


def test_mention_regex_still_sees_prose(gate):
    """Typos must stay catchable even though they don't count as coverage."""
    assert gate.AC_MENTION.findall("see AC-OBS-CEA-001.2 for details") == [
        "AC-OBS-CEA-001.2"
    ]


# ── partition() ─────────────────────────────────────────────────────────────

@pytest.fixture
def tiny_manifest():
    return {
        "in_repo_prefixes": ["AC-OBS-", "AC-GOV-"],
        "external_prefixes": {"AC-CLOUD-": "clawmetry-cloud"},
        "criteria": [
            {"id": "AC-OBS-001.1", "doc": "D", "text": "t"},
            {"id": "AC-OBS-001.2", "doc": "D", "text": "t"},
        ],
    }


def test_partition_splits_covered_and_uncovered(gate, tiny_manifest):
    declared = {"AC-OBS-001.1": {"tests/test_a.py"}}
    covered, uncovered, unknown = gate.partition(tiny_manifest, declared, declared)
    assert covered == ["AC-OBS-001.1"]
    assert uncovered == ["AC-OBS-001.2"]
    assert unknown == []


def test_unknown_in_repo_id_is_flagged(gate, tiny_manifest):
    """A test citing a criterion the manifest lacks proves nothing."""
    mentioned = {"AC-OBS-999.9": {"tests/test_typo.py"}}
    _, _, unknown = gate.partition(tiny_manifest, {}, mentioned)
    assert unknown == ["AC-OBS-999.9"]


def test_external_repo_ids_are_not_flagged_as_typos(gate, tiny_manifest):
    """AC-CLOUD-* lives in clawmetry-cloud; referencing it here is not an error."""
    mentioned = {"AC-CLOUD-001.4": {"tests/test_relay.py"}}
    _, _, unknown = gate.partition(tiny_manifest, {}, mentioned)
    assert unknown == []


# ── the real manifest + baseline ────────────────────────────────────────────

def test_real_manifest_is_wellformed(gate):
    manifest = gate.load_manifest()  # raises on duplicate ids
    assert manifest["criteria"], "manifest must not be empty"
    for crit in manifest["criteria"]:
        assert crit["id"] and crit["doc"] and crit["text"]
        assert crit["id"].startswith(tuple(manifest["in_repo_prefixes"])), (
            "%s is not an in-repo criterion; external families belong under "
            "external_prefixes, not criteria" % crit["id"]
        )


def test_baseline_names_only_real_criteria(gate):
    """A stale baseline entry silently loosens the ratchet."""
    manifest = gate.load_manifest()
    known = {c["id"] for c in manifest["criteria"]}
    with open(gate.BASELINE_PATH, encoding="utf-8") as fh:
        baseline = json.load(fh)
    stale = sorted(set(baseline["uncovered"]) - known)
    assert not stale, "baseline names criteria the manifest no longer has: %s" % stale


def test_gate_passes_on_the_committed_tree(gate):
    """The committed tree must satisfy its own ratchet."""
    manifest = gate.load_manifest()
    declared, mentioned = gate.scan_tests()
    assert gate.cmd_check(manifest, declared, mentioned) == 0
