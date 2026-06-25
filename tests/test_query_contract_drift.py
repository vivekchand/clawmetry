"""Drift CI for the q/1 query contract (issue #2987, Query Spine P1).

Fails when clawmetry/query_contract.py, routes/local_query.py
(_SHAPES + _coerce_args), and docs/QUERY_CONTRACT.md disagree:

* every "live" registry entry maps 1:1 onto _SHAPES (both directions),
* each live entry's arg allowlist matches what _coerce_args actually
  accepts (allowed keys, required-arg enforcement, unknown-arg drop),
* "planned" methods are NOT served (implementing one without flipping
  the registry to live fails),
* the committed docs/QUERY_CONTRACT.md is exactly the generator output,
* trust classes are pinned and no e2e-classed method name appears in
  any *PLAINTEXT* list/set/tuple constant in the source tree (grep
  level guard; hard enforcement lands in Query Spine P4).
"""

from __future__ import annotations

import importlib.util
import pathlib
import re

import pytest

import routes.local_query as lq
from clawmetry import query_contract as qc

ROOT = pathlib.Path(__file__).resolve().parents[1]

LIVE = {n for n, s in qc.QUERY_CONTRACT.items() if s["status"] == qc.STATUS_LIVE}
PLANNED = {n for n, s in qc.QUERY_CONTRACT.items() if s["status"] == qc.STATUS_PLANNED}


# ── registry <-> _SHAPES ──────────────────────────────────────────────

def test_every_live_method_is_a_shape_and_vice_versa():
    assert set(lq._SHAPES) == LIVE, (
        "live registry entries and _SHAPES must match 1:1. "
        f"only_in_shapes={set(lq._SHAPES) - LIVE} "
        f"only_in_registry={LIVE - set(lq._SHAPES)}"
    )


def test_shape_backing_matches_registry():
    for name in LIVE:
        spec = qc.QUERY_CONTRACT[name]
        expect = qc._DISPATCH_OVERRIDES.get(name, spec["backing"])
        assert lq._SHAPES[name] == expect, (
            f"shape {name!r} dispatches {lq._SHAPES[name]!r}, "
            f"registry declares backing {expect!r}"
        )


def test_health_is_the_only_dispatch_special_case():
    assert lq._SHAPES["health"] is None
    assert [n for n, m in lq._SHAPES.items() if m is None] == ["health"]


def test_planned_methods_are_not_served():
    served = PLANNED & set(lq._SHAPES)
    assert not served, (
        f"planned methods {sorted(served)} are served by _SHAPES but the "
        "registry still says planned. Flip their status to live (and add "
        "args/goldens) in the same change."
    )


def test_statuses_and_version():
    assert qc.CONTRACT_VERSION == "q/1"
    for name, spec in qc.QUERY_CONTRACT.items():
        assert spec["status"] in (qc.STATUS_LIVE, qc.STATUS_PLANNED), name
        assert spec["trust"] in (qc.TRUST_PLAINTEXT, qc.TRUST_E2E), name
        assert spec["backing"], name
        assert spec["doc"], name
        assert isinstance(spec["args"], dict), name


# ── registry args <-> _coerce_args ───────────────────────────────────────────

def _required_args(name: str) -> dict:
    return {
        a: "probe-value"
        for a, meta in qc.QUERY_CONTRACT[name]["args"].items()
        if meta.get("required")
    }


def test_live_arg_allowlists_match_coerce_args():
    for name in sorted(LIVE):
        declared = set(qc.QUERY_CONTRACT[name]["args"])
        coerced = lq._coerce_args(name, dict(_required_args(name)))
        assert set(coerced) == declared, (
            f"{name}: registry args {sorted(declared)} != "
            f"_coerce_args output keys {sorted(coerced)}"
        )


def test_live_required_args_are_enforced():
    for name in sorted(LIVE):
        required = _required_args(name)
        if not required:
            continue
        with pytest.raises(ValueError):
            lq._coerce_args(name, {})


def test_unknown_args_are_dropped():
    for name in sorted(LIVE):
        probe = dict(_required_args(name))
        probe["definitely_not_a_real_arg_zz"] = 1
        coerced = lq._coerce_args(name, probe)
        assert "definitely_not_a_real_arg_zz" not in coerced, name


def test_coerce_args_rejects_unknown_shapes():
    with pytest.raises(ValueError):
        lq._coerce_args("not_a_shape_zz", {})


def test_live_int_arg_defaults_match():
    """defaults/bounds declared in the registry are what _coerce_args
    actually applies (probe with no value -> default; huge value -> hi)."""
    for name in sorted(LIVE):
        for arg, meta in qc.QUERY_CONTRACT[name]["args"].items():
            if "default" not in meta:
                continue
            coerced = lq._coerce_args(name, dict(_required_args(name)))
            assert coerced[arg] == meta["default"], (name, arg)
            capped = lq._coerce_args(
                name, {**_required_args(name), arg: 10 ** 9}
            )
            assert capped[arg] == meta["hi"], (name, arg)


# ── doc generation ─────────────────────────────────────────────────────────

def test_committed_doc_matches_generator():
    spec = importlib.util.spec_from_file_location(
        "gen_query_contract_doc", ROOT / "scripts" / "gen_query_contract_doc.py"
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    doc = ROOT / "docs" / "QUERY_CONTRACT.md"
    assert doc.exists(), "docs/QUERY_CONTRACT.md missing"
    assert doc.read_text() == mod.render(), (
        "docs/QUERY_CONTRACT.md drifted from the registry. "
        "Regenerate: python3 scripts/gen_query_contract_doc.py"
    )


# ── trust classes ─────────────────────────────────────────────────────────────

# Pinned on purpose: changing a method's trust class is a privacy decision
# and must be made twice (registry + here), never as a drive-by.
EXPECTED_TRUST = {
    "glance": "plaintext",
    "runtimes": "plaintext",
    "models": "plaintext",
    "usage": "plaintext",
    "health": "plaintext",
    "aggregates": "plaintext",
    "approvals": "plaintext",
    "events": "e2e",
    "sessions": "e2e",
    # #2988: rollup_session carries titles -> content class, never plaintext.
    "rollup_sessions": "e2e",
    "session": "e2e",
    "transcript": "e2e",
    "brain": "e2e",
    "spans": "e2e",
    "traces": "e2e",
    "external_calls": "e2e",
    "search": "e2e",
    # #1012 Agent Graph: aggregate node/edge counts only, no content.
    "agent_graph": "plaintext",
}


def test_trust_classes_are_pinned():
    actual = {n: s["trust"] for n, s in qc.QUERY_CONTRACT.items()}
    assert actual == EXPECTED_TRUST


# Grep-level guard (P4 lands hard enforcement): find every
# *PLAINTEXT*-named list/set/tuple constant in the source tree and assert
# no e2e-classed contract method name appears in it as a string literal.
_PLAINTEXT_CONST_RE = re.compile(
    r"^[ \t]*_?[A-Z0-9_]*PLAINTEXT[A-Z0-9_]*\s*(?::[^=\n]+)?=\s*(?:frozenset\s*\()?[\[\{\(]",
    re.M,
)
_BRACKETS = {"[": "]", "{": "}", "(": ")"}


def _literal_blocks(text: str):
    """Yield the bracketed literal following each *PLAINTEXT* assignment."""
    for m in _PLAINTEXT_CONST_RE.finditer(text):
        i = m.end() - 1
        depth = 0
        for j in range(i, min(len(text), i + 20000)):
            c = text[j]
            if c in _BRACKETS:
                depth += 1
            elif c in _BRACKETS.values():
                depth -= 1
                if depth == 0:
                    yield text[i:j + 1]
                    break


def test_no_e2e_method_in_plaintext_push_lists():
    e2e = {n for n, s in qc.QUERY_CONTRACT.items() if s["trust"] == qc.TRUST_E2E}
    offenders = []
    py_files = (
        list((ROOT / "clawmetry").rglob("*.py"))
        + list((ROOT / "routes").glob("*.py"))
        + [ROOT / "dashboard.py"]
    )
    for path in py_files:
        try:
            text = path.read_text()
        except (OSError, UnicodeDecodeError):
            continue
        for block in _literal_blocks(text):
            strings = set(re.findall(r"['\"]([a-z_]+)['\"]", block))
            hit = strings & e2e
            if hit:
                offenders.append((str(path.relative_to(ROOT)), sorted(hit)))
    assert not offenders, (
        "e2e-classed contract methods found in a *PLAINTEXT* push list: "
        f"{offenders}. Content methods must only leave the machine "
        "AES-256-GCM encrypted."
    )
