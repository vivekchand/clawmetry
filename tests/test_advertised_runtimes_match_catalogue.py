"""CI guard against advertised-vs-supported runtime drift.

The homepage hero tooltip + the pricing-page tier bullets advertise a
fixed list of runtimes (OpenClaw, NemoClaw, plus 12 paid). This test
pins the entitlement catalogue to that list and asserts every
advertised runtime has an adapter or catalogue entry, and that no
runtime is in the catalogue without being advertised.

Burned 2026-05-29: NeMo was on the homepage but invisible in
/api/agents because the entitlement catalogue ID drifted vs the
adapter (``name='nemo'`` vs FREE_RUNTIMES ``{'nemoclaw'}``). This guard
catches that class of drift before it ships.
"""
from __future__ import annotations

import importlib

import pytest


# Canonical list per /pricing tier bullets + homepage hero (snapshot
# taken 2026-08-19; update both places + this list in lockstep when
# adding a runtime or moving one between tiers).
#
# goose moved free 2026-08-19, qwen_code 2026-09-20 — see
# entitlements.FREE_RUNTIMES for why.
# Moving a runtime between these two sets is a PUBLIC PRICING CHANGE: the
# /pricing bullets and the homepage hero must ship in the same batch, or
# this guard is lying rather than pinning.
EXPECTED_FREE_RUNTIMES = frozenset({"openclaw", "nemoclaw", "goose", "qwen_code"})
EXPECTED_PAID_RUNTIMES = frozenset({
    "claude_code", "codex", "cursor", "aider",
    "opencode", "hermes", "picoclaw", "nanoclaw",
    "pi", "deepagents", "n8n", "antigravity", "copilot", "grok", "qm",
    "deepseek_harness",
    "exo",
    "kimi",
    "devin",
    "gemini_cli",
    "cline",
    "openhands",
    "openworker",
    "grok_bot",
    "lovable",
    "replit",
    "muse_code",
    "openexecutive",
})
EXPECTED_ALL_RUNTIMES = EXPECTED_FREE_RUNTIMES | EXPECTED_PAID_RUNTIMES


@pytest.fixture(autouse=True)
def fresh_entitlements(monkeypatch, tmp_path):
    """Force a clean entitlements module per test so catalogue lookups
    are deterministic regardless of dev-box state."""
    monkeypatch.delenv("CLAWMETRY_ENFORCE", raising=False)
    monkeypatch.setenv("HOME", str(tmp_path))
    import clawmetry.entitlements as _ent
    importlib.reload(_ent)
    _ent.invalidate()


def test_free_runtimes_matches_marketing():
    """The Free runtimes advertised on /pricing must match FREE_RUNTIMES."""
    from clawmetry.entitlements import FREE_RUNTIMES
    assert FREE_RUNTIMES == EXPECTED_FREE_RUNTIMES, (
        f"FREE_RUNTIMES drift: catalogue={set(FREE_RUNTIMES)} "
        f"vs marketing={set(EXPECTED_FREE_RUNTIMES)}"
    )


def test_paid_runtimes_matches_marketing():
    """The 12 paid runtimes advertised on /pricing must match PAID_RUNTIMES."""
    from clawmetry.entitlements import PAID_RUNTIMES
    assert PAID_RUNTIMES == EXPECTED_PAID_RUNTIMES, (
        f"PAID_RUNTIMES drift: catalogue={set(PAID_RUNTIMES)} "
        f"vs marketing={set(EXPECTED_PAID_RUNTIMES)}"
    )


def test_runtime_labels_cover_every_advertised_runtime():
    """RUNTIME_LABELS must have an entry for every advertised runtime so
    the UI never falls back to a raw id like 'qwen_code' in user-facing copy."""
    from clawmetry.entitlements import RUNTIME_LABELS
    for r in EXPECTED_ALL_RUNTIMES:
        assert r in RUNTIME_LABELS, f"RUNTIME_LABELS missing entry for {r!r}"
        assert RUNTIME_LABELS[r], f"RUNTIME_LABELS[{r!r}] is empty"


def test_api_runtimes_fallback_lists_every_free_runtime():
    """The /api/runtimes hardcoded never-raise fallback in
    routes/entitlement/ must include EVERY free runtime so a busted
    catalogue read still shows the whole free tier.

    ``routes.entitlement`` is a package whose ``__init__`` is a re-export
    shim, so the fallback literal lives in one of the ``_endpoints_*``
    modules. Scanning only the shim (as this did before 2026-09-20) found
    no runtime at all and failed on whichever id the frozenset yielded
    first, which is why it reported goose as missing while goose was in
    the fallback all along.
    """
    import pathlib

    import routes.entitlement as _ep

    pkg = pathlib.Path(_ep.__file__).parent
    body = "\n".join(f.read_text() for f in sorted(pkg.glob("*.py")))
    for r in EXPECTED_FREE_RUNTIMES:
        assert f'"id": "{r}"' in body, (
            f"/api/runtimes fallback in {pkg} missing free runtime {r!r}"
        )


def test_oss_only_ships_free_runtime_adapters():
    """OSS clawmetry/adapters/ must contain adapter files for the Free
    runtimes (openclaw, nemoclaw via the NemoClaw facade in nemo.py,
    goose and qwen_code in files named after the runtime)."""
    import importlib
    # OpenClaw: dedicated file.
    oc = importlib.import_module("clawmetry.adapters.openclaw")
    assert hasattr(oc, "OpenClawAdapter"), "OpenClawAdapter missing"
    # NemoClaw: facade lives in nemo.py (push-mode receiver shares the file).
    nm = importlib.import_module("clawmetry.adapters.nemo")
    assert hasattr(nm, "NemoClawAdapter"), "NemoClawAdapter missing from clawmetry.adapters.nemo"
    # The OSS runtimes that moved free: their reader must ship here, or the
    # "free" claim means "ungated but unusable without the paid wheel".
    for mod_name, cls in (("goose", "GooseAdapter"), ("qwen_code", "QwenCodeAdapter")):
        mod = importlib.import_module(f"clawmetry.adapters.{mod_name}")
        assert hasattr(mod, cls), f"{cls} missing from clawmetry.adapters.{mod_name}"


def test_no_orphan_runtime_in_paid_set():
    """Every entry in PAID_RUNTIMES must be one we can actually advertise
    + sell. Catches the case where someone adds a runtime id to the
    catalogue without updating /pricing."""
    from clawmetry.entitlements import PAID_RUNTIMES
    orphans = set(PAID_RUNTIMES) - EXPECTED_PAID_RUNTIMES
    assert not orphans, (
        f"PAID_RUNTIMES contains runtimes the marketing copy does not "
        f"advertise: {orphans}. Either add them to /pricing or remove "
        f"them from the catalogue."
    )


def test_no_unmodeled_runtime_in_free_set():
    """Symmetric guard: every entry in FREE_RUNTIMES has both an adapter
    and an advertised name."""
    from clawmetry.entitlements import FREE_RUNTIMES
    orphans = set(FREE_RUNTIMES) - EXPECTED_FREE_RUNTIMES
    assert not orphans, (
        f"FREE_RUNTIMES contains runtimes the marketing copy does not "
        f"advertise: {orphans}."
    )
