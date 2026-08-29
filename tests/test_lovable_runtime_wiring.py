"""Lovable: every list that must name it, and every honesty claim that must hold.

Same guard shape as test_grok_bot_runtime_wiring.py: a runtime registered in
one list but not another looks wired and silently does nothing. This pins the
lists, and pins the claims that make Lovable honest rather than merely
present: no cost, no liveness, no per-session control, and a memory-catalog
entry that explains its own emptiness.

Lovable's local surface is a git clone of its GitHub-synced repo (one bot
commit per accepted agent edit); everything else about the runtime lives in
the vendor cloud.
"""
from __future__ import annotations

import json
import os
import re

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RT = "lovable"


def _src(*parts: str) -> str:
    with open(os.path.join(REPO, *parts), encoding="utf-8") as fh:
        return fh.read()


# ── the lists ───────────────────────────────────────────────────────────────


def test_entitlement_catalogue_names_it():
    from clawmetry import entitlements as ent

    assert RT in ent.PAID_RUNTIMES, "lovable must be a paid runtime"
    assert RT in ent.ALL_RUNTIMES
    assert ent.RUNTIME_LABELS.get(RT) == "Lovable"


def test_the_daemon_loader_names_it():
    """sync._FAMILY_ADAPTER_SPECS is the ONLY loader; there is no discovery."""
    src = _src("clawmetry", "sync.py")
    assert "clawmetry_pro.adapters.lovable" in src
    assert "LovableAdapter" in src


def test_it_is_a_paid_import_path_never_an_oss_one():
    """A paid adapter published in the OSS wheel bypasses the licence gate."""
    src = _src("clawmetry", "sync.py")
    assert "clawmetry.adapters.lovable" not in src


def test_the_landing_path_is_registered():
    from clawmetry import entitlements as ent

    paths = getattr(ent, "RUNTIME_LANDING_PATHS", None)
    if paths is None:  # map renamed; find it by value shape instead
        assert "/runtimes/lovable" in _src("clawmetry", "entitlements.py")
        return
    assert paths.get(RT) == "/runtimes/lovable"


def test_the_memory_catalog_has_an_entry_that_explains_its_own_emptiness():
    """ADR-020: no invented roots, and an honest note instead of a bare empty."""
    from clawmetry import runtime_memory

    entry = next((e for e in runtime_memory._catalog() if e.id == RT), None)
    assert entry is not None, "lovable missing from the Memory & Skills catalog"
    assert entry.label == "Lovable"
    assert entry.note, "an empty catalog entry must carry a note"
    assert "cloud" in entry.note.lower()
    # Knowledge/Skills live in Lovable's cloud; a local root would be invented.
    assert entry.roots == ()


def test_the_frontend_knows_it():
    app_js = _src("clawmetry", "static", "js", "app.js")
    assert f"{RT}:" in app_js, "lovable absent from app.js maps"
    assert "'Lovable'" in app_js


def test_the_frontend_prefix_map_buckets_it():
    """qm was once missing from _CM_RT_PREFIXES alone; pin this one."""
    app_js = _src("clawmetry", "static", "js", "app.js")
    m = re.search(r"var _CM_RT_PREFIXES = \{(.*?)\};", app_js, re.DOTALL)
    assert m, "_CM_RT_PREFIXES not found"
    assert f"{RT}: 1" in m.group(1)


def test_the_logo_manifest_has_a_brand_entry():
    manifest = json.loads(_src("clawmetry", "static", "runtime-logos", "manifest.json"))
    assert RT in manifest
    assert manifest[RT].get("label") == "Lovable"


def test_the_runtime_probe_is_env_only_never_a_guess():
    """No install dir exists; the only path evidence a probe could glob would
    be any repo anywhere, which is a false positive. Env override only."""
    from clawmetry import runtime_probe

    probe = next((p for p in runtime_probe.RUNTIME_PROBES if p.id == RT), None)
    assert probe is not None, "lovable missing from runtime_probe.PROBES"
    assert probe.paths == (), "a path glob cannot identify a Lovable repo"
    assert probe.env == "CLAWMETRY_LOVABLE_DIRS"


# ── the honesty claims ──────────────────────────────────────────────────────


def test_cost_is_declared_unobservable_everywhere_it_is_declared():
    """Lovable bills credits in the vendor cloud; the clone records commits.

    runtime_records is what the Harness/provenance surfaces read, so an
    optimistic value here becomes a fabricated figure in the UI.
    """
    from clawmetry import runtime_records as rr

    rec = rr.RUNTIME_RECORDS.get(RT)
    assert rec is not None, "lovable missing from RUNTIME_RECORDS"
    assert rec["tokens"] == rr.UNAVAILABLE
    assert rec["cost"] == rr.UNAVAILABLE
    assert rec["model"] == rr.UNAVAILABLE


def test_the_frontend_does_not_advertise_a_cost_capability():
    """The capability chip drives what the UI promises the user."""
    app_js = _src("clawmetry", "static", "js", "app.js")
    m = re.search(r"\blovable:\s*\[([^\]]*)\]", app_js)
    assert m, "lovable has no capability list in app.js"
    caps = m.group(1)
    assert "SESSIONS" in caps and "EVENTS" in caps
    assert "COST" not in caps, (
        "lovable must not advertise COST: nothing local prices an edit"
    )


def test_per_session_control_is_not_offered():
    """The agent runs in Lovable's cloud; there is no local process to signal.

    Offering a control that cannot reach the agent is the "button that quietly
    does nothing" this project forbids.
    """
    from clawmetry import process_control as pc

    assert RT not in pc.SUPPORTED_RUNTIMES
    assert RT not in getattr(pc, "SPLIT_SUPPORT_RUNTIMES", frozenset())


def test_context_coverage_denylists_it():
    """The clone records commits, not context events; silence proves nothing."""
    src = _src("clawmetry", "context_coverage.py")
    assert f'"{RT}"' in src, "lovable must be denylisted from compaction claims"


def test_every_runtime_in_the_catalogue_has_a_record_and_a_label():
    """The general invariant new runtimes keep violating, re-pinned."""
    from clawmetry import entitlements as ent
    from clawmetry import runtime_records as rr

    missing_label = sorted(r for r in ent.ALL_RUNTIMES if not ent.RUNTIME_LABELS.get(r))
    missing_record = sorted(r for r in ent.ALL_RUNTIMES if r not in rr.RUNTIME_RECORDS)
    assert not missing_label, f"runtimes with no display label: {missing_label}"
    assert not missing_record, f"runtimes with no cost record: {missing_record}"


def test_the_readme_grid_links_it():
    readme = _src("README.md")
    assert "https://clawmetry.com/runtimes/lovable" in readme, (
        "README grid must LINK the runtime, never list it bare"
    )
