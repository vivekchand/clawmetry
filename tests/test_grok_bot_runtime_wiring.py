"""Grok Bot: every list that must name it, and every honesty claim that must hold.

Adding this runtime was bitten FOUR separate times by the same failure: a
runtime is registered in one list, looks wired, and silently does nothing
because a second list never learned about it. Each omission failed quietly --
an adapter that never loads, a UI with no label, a conformance leg that
dispatches and exits, a catalogue that 404s.

CLAUDE.md states the rule as "BOTH lists". It is more than two, so this test
enumerates them. It also pins the claims that make Grok Bot honest rather than
merely present: no cost, no per-session control, and a catalogue entry that
explains its own emptiness.

Deliberately source-parsed rather than imported where the target is a data
literal, so the guard holds without the paid package installed -- the same
technique the free/paid tier guard uses.
"""
from __future__ import annotations

import ast
import json
import os
import re

import pytest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RT = "grok_bot"


def _src(*parts: str) -> str:
    with open(os.path.join(REPO, *parts), encoding="utf-8") as fh:
        return fh.read()


# ── the lists ───────────────────────────────────────────────────────────────


def test_entitlement_catalogue_names_it():
    from clawmetry import entitlements as ent

    assert RT in ent.PAID_RUNTIMES, "grok_bot must be a paid runtime"
    assert RT in ent.ALL_RUNTIMES
    assert ent.RUNTIME_LABELS.get(RT) == "Grok Bot"


def test_grok_is_relabelled_so_the_two_xai_products_are_distinguishable():
    """Grok Build (CLI, ~/.grok) and Grok Bot (cloud VM) are different products.

    A bare "Grok" label next to "Grok Bot" invites reading one runtime's
    activity under the other's name.
    """
    from clawmetry import entitlements as ent

    assert ent.RUNTIME_LABELS.get("grok") == "Grok Build"
    assert ent.RUNTIME_LABELS["grok"] != ent.RUNTIME_LABELS[RT]


def test_the_daemon_loader_names_it():
    """sync._FAMILY_ADAPTER_SPECS is the ONLY loader; there is no discovery."""
    src = _src("clawmetry", "sync.py")
    assert "clawmetry_pro.adapters.grok_bot" in src
    assert "GrokBotAdapter" in src


def test_it_is_a_paid_import_path_never_an_oss_one():
    """A paid adapter published in the OSS wheel bypasses the licence gate."""
    src = _src("clawmetry", "sync.py")
    assert "clawmetry.adapters.grok_bot" not in src


def test_the_landing_path_is_registered():
    from clawmetry import entitlements as ent

    paths = getattr(ent, "RUNTIME_LANDING_PATHS", None)
    if paths is None:  # map renamed; find it by value shape instead
        assert "/runtimes/grok-bot" in _src("clawmetry", "entitlements.py")
        return
    assert paths.get(RT) == "/runtimes/grok-bot"


def test_the_memory_catalog_has_an_entry_that_explains_its_own_emptiness():
    """ADR-020: no invented roots, and an honest note instead of a bare empty."""
    from clawmetry import runtime_memory

    entry = next((e for e in runtime_memory._catalog() if e.id == RT), None)
    assert entry is not None, "grok_bot missing from the Memory & Skills catalog"
    assert entry.label == "Grok Bot"
    assert entry.note, "an empty-ish catalog entry must carry a note"
    assert "cloud" in entry.note.lower()


def test_the_frontend_knows_it():
    app_js = _src("clawmetry", "static", "js", "app.js")
    assert f"{RT}:" in app_js, "grok_bot absent from app.js maps"
    assert "'Grok Bot'" in app_js


def test_the_logo_manifest_has_a_brand_entry():
    manifest = json.loads(_src("clawmetry", "static", "runtime-logos", "manifest.json"))
    assert RT in manifest
    assert manifest[RT].get("label") == "Grok Bot"


# ── the honesty claims ──────────────────────────────────────────────────────


def test_cost_is_declared_unobservable_everywhere_it_is_declared():
    """No tokens, no model, no dollars exist in Grok Bot's store.

    runtime_records is what the Harness/provenance surfaces read, so an
    optimistic value here becomes a fabricated figure in the UI.
    """
    from clawmetry import runtime_records as rr

    rec = rr.RUNTIME_RECORDS.get(RT)
    assert rec is not None, "grok_bot missing from RUNTIME_RECORDS"
    assert rec["tokens"] == rr.UNAVAILABLE
    assert rec["cost"] == rr.UNAVAILABLE
    assert rec["model"] == rr.UNAVAILABLE


def test_the_frontend_does_not_advertise_a_cost_capability():
    """The capability chip drives what the UI promises the user."""
    app_js = _src("clawmetry", "static", "js", "app.js")
    m = re.search(r"\bgrok_bot:\s*\[([^\]]*)\]", app_js)
    assert m, "grok_bot has no capability list in app.js"
    caps = m.group(1)
    assert "SESSIONS" in caps and "EVENTS" in caps
    assert "COST" not in caps, (
        "grok_bot must not advertise COST: nothing in its store prices a turn"
    )


def test_per_session_control_is_not_offered():
    """One Electron process serves every bot, and the agent runs off-machine.

    Offering a control that cannot reach the agent is the "button that quietly
    does nothing" this project forbids.
    """
    from clawmetry import process_control as pc

    assert RT not in pc.SUPPORTED_RUNTIMES
    assert RT not in getattr(pc, "SPLIT_SUPPORT_RUNTIMES", frozenset())


def test_context_coverage_denylists_it():
    """No compaction entry kind exists, so silence is not evidence of none."""
    from clawmetry import context_coverage

    src = _src("clawmetry", "context_coverage.py")
    assert f'"{RT}"' in src, "grok_bot must be denylisted from compaction claims"


def test_every_runtime_in_the_catalogue_has_a_record_and_a_label():
    """The general invariant this runtime kept violating, pinned for all of them."""
    from clawmetry import entitlements as ent
    from clawmetry import runtime_records as rr

    missing_label = sorted(r for r in ent.ALL_RUNTIMES if not ent.RUNTIME_LABELS.get(r))
    missing_record = sorted(r for r in ent.ALL_RUNTIMES if r not in rr.RUNTIME_RECORDS)
    assert not missing_label, f"runtimes with no display label: {missing_label}"
    assert not missing_record, f"runtimes with no cost record: {missing_record}"


@pytest.mark.parametrize("bad", ["~/.grok/", '"grok"'])
def test_grok_bot_roots_are_not_grok_build_roots(bad):
    """~/.grok is Grok Build. Reading it here would attribute one to the other."""
    from clawmetry import runtime_memory

    entry = next(e for e in runtime_memory._catalog() if e.id == RT)
    for root in entry.roots:
        path = getattr(root, "path", "") or ""
        assert not path.rstrip("/").endswith("/.grok"), (
            f"grok_bot root {path!r} points at Grok Build's directory"
        )
