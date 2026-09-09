"""CI guard: SUPPORTED_RUNTIMES.txt is the export every other repo reads.

Third sibling of ``test_advertised_runtimes_match_catalogue.py`` (pins the
*set*), ``test_runtime_count_copy_sync.py`` (pins the *number in prose*) and
``test_runtime_public_surfaces.py`` (pins the *links*). This one pins the
*export*: the single generated file that clawmetry-pro, clawmetry-cloud and
clawmetry-landing read instead of keeping their own hand-typed lists.

Burned 2026-09-09: the catalogue had 30 runtimes and every guard in this repo
was green, while the GitHub repository "About" blurb said 26, clawmetry-pro's
FLYWHEEL.md said 22, clawmetry-landing's said 21 and clawmetry-cloud's said
14. None of those surfaces is a file this repo's CI could see, and each had
been edited by hand at a different time. The export plus
``.github/workflows/sync-github-about.yml`` is the fix: one artifact, one
blurb, pushed rather than remembered.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
SCRIPT = REPO / "scripts" / "sync_runtime_count.py"
EXPORT = REPO / "SUPPORTED_RUNTIMES.txt"


@pytest.fixture(scope="module")
def sync():
    spec = importlib.util.spec_from_file_location("sync_runtime_count", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_export_is_not_stale(sync):
    """The committed file matches what the catalogue renders today."""
    stale = sync.check_export()
    assert not stale, (
        f"{stale}\n\nRegenerate with: python3 scripts/sync_runtime_count.py"
    )


def test_export_matches_the_imported_catalogue(sync):
    """The script *parses* entitlements.py; assert that parse against the real
    imported objects, so a reformat of the literals cannot silently produce a
    short catalogue that every downstream repo then trusts."""
    from clawmetry.entitlements import (
        ALL_RUNTIMES,
        FREE_RUNTIMES,
        RUNTIME_LABELS,
        RUNTIME_LANDING_PATHS,
    )

    _, rows = sync.parse_export(EXPORT.read_text(encoding="utf-8"))
    assert {r["id"] for r in rows} == set(ALL_RUNTIMES)
    for r in rows:
        assert r["label"] == RUNTIME_LABELS[r["id"]], r["id"]
        assert r["path"] == RUNTIME_LANDING_PATHS[r["id"]], r["id"]
        want_tier = "free" if r["id"] in FREE_RUNTIMES else "paid"
        assert r["tier"] == want_tier, r["id"]


def test_export_metadata_agrees_with_its_own_rows(sync):
    """COUNT is written out for consumers that only want the number. If it
    could disagree with the rows, a consumer reading COUNT and a consumer
    reading the rows would render two different numbers on the same page."""
    from clawmetry.entitlements import RUNTIME_COUNT

    meta, rows = sync.parse_export(EXPORT.read_text(encoding="utf-8"))
    assert int(meta["COUNT"]) == len(rows) == RUNTIME_COUNT
    assert int(meta["FREE_COUNT"]) == sum(r["tier"] == "free" for r in rows)
    assert int(meta["PAID_COUNT"]) == sum(r["tier"] == "paid" for r in rows)
    assert int(meta["FREE_COUNT"]) + int(meta["PAID_COUNT"]) == int(meta["COUNT"])


def test_blurb_fits_the_github_about_box(sync):
    """GitHub truncates a repository description past 350 characters, with no
    warning — the sentence just stops. The blurb grows every time a marquee
    runtime is added, so this is a real ceiling, not a formality."""
    text = sync.blurb()
    assert len(text) <= sync.GITHUB_ABOUT_LIMIT, (
        f"blurb is {len(text)} chars, over GitHub's {sync.GITHUB_ABOUT_LIMIT} "
        f"limit; shorten it or drop a name from RUNTIME_MARQUEE:\n{text}"
    )
    assert str(sync.catalogue_count()) in text


def test_blurb_arithmetic_is_derived_not_typed(sync):
    """'& N more' must be the total minus the names actually printed. This is
    the exact sum that went wrong: 30 runtimes, 4 named, '& 26 more' in the
    README next to an About blurb that said 26 *total*."""
    from clawmetry.entitlements import RUNTIME_COUNT

    named = sync.marquee()
    assert f"& {RUNTIME_COUNT - len(named)} more" in sync.blurb()


def test_marquee_names_real_runtimes(sync):
    from clawmetry.entitlements import ALL_RUNTIMES, RUNTIME_MARQUEE

    unknown = [r for r in RUNTIME_MARQUEE if r not in ALL_RUNTIMES]
    assert not unknown, f"RUNTIME_MARQUEE names runtimes not in the catalogue: {unknown}"
    assert len(set(RUNTIME_MARQUEE)) == len(RUNTIME_MARQUEE), "duplicate in RUNTIME_MARQUEE"
    assert sync.marquee() == list(RUNTIME_MARQUEE)


def test_export_round_trips_through_the_reference_parser(sync):
    """Other repos copy :func:`parse_export`'s five lines. If the renderer can
    emit something the reference parser mangles, they inherit the bug."""
    text = sync.render_export()
    meta, rows = sync.parse_export(text)
    assert meta["BLURB"] == sync.blurb()
    for r in rows:
        # A TAB or '=' inside a label would break the grammar for everyone.
        assert "\t" not in r["label"] and "\n" not in r["label"], r
        assert r["tier"] in {"free", "paid"}
        assert r["path"].startswith("/")


def test_readme_tagline_names_the_marquee_in_order(sync):
    """The tagline and the blurb are the same sentence in two places. If they
    can name different runtimes, the "& N more" arithmetic silently stops
    matching what the reader just counted."""
    import re

    from clawmetry.entitlements import RUNTIME_LABELS, RUNTIME_MARQUEE

    readme = (REPO / "README.md").read_text(encoding="utf-8")
    m = re.search(r"^Works with \*\*\d+ AI agent runtimes\*\* — (.+?) & \d+ more\.", readme, re.M)
    assert m, "README.md lost its 'Works with N AI agent runtimes — ... & N more.' tagline"

    named = [n.strip() for n in m.group(1).split(",")]
    vendor = {"NemoClaw": "NVIDIA NemoClaw", "Codex": "OpenAI Codex"}
    want = [vendor.get(RUNTIME_LABELS[r], RUNTIME_LABELS[r]) for r in RUNTIME_MARQUEE]
    assert named == want, (
        f"README tagline names {named}; RUNTIME_MARQUEE says {want}. "
        "Reorder the tagline, not the marquee — the marquee is what the "
        "GitHub About blurb and the PyPI summary read."
    )
