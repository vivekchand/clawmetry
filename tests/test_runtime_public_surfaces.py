"""CI guard: every runtime in the catalogue has its public storefront surfaces.

Sibling of ``test_advertised_runtimes_match_catalogue.py`` (pins the *set*)
and ``test_runtime_count_copy_sync.py`` (pins the *number*). This one pins
the *links*: a runtime is not "supported" until the README grid links it to
its own page on clawmetry.com, and that page exists.

Burned 2026-08-17: Exo shipped in the catalogue, the wheel (0.12.726), the
cloud pin, and the README's "Works with 21 agent runtimes" line, but the
README listed it as bare bold text (no link), the homepage grid still had
20 tiles, and /runtimes/exo was a 404. Every other guard was green.

Two layers:

* Offline (always runs): ``RUNTIME_LANDING_PATHS`` covers exactly
  ``ALL_RUNTIMES``, and the README grid carries a link to each path.
* Live (opt-in, ``CLAWMETRY_LIVE_CHECKS=1``): each path serves 200 on
  https://clawmetry.com. Run it as the last step of a new-runtime sprint
  (FLYWHEEL.md section 2a) — it is the "verified live" bar for the
  storefront half of the flywheel.
"""
from __future__ import annotations

import os
import re
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from clawmetry.entitlements import (  # noqa: E402
    ALL_RUNTIMES,
    RUNTIME_LABELS,
    RUNTIME_LANDING_PATHS,
)

LANDING_ORIGIN = "https://clawmetry.com"


def test_every_runtime_has_a_landing_path_and_label():
    missing_path = sorted(ALL_RUNTIMES - set(RUNTIME_LANDING_PATHS))
    extra_path = sorted(set(RUNTIME_LANDING_PATHS) - ALL_RUNTIMES)
    missing_label = sorted(ALL_RUNTIMES - set(RUNTIME_LABELS))
    assert not missing_path, (
        f"runtimes with no RUNTIME_LANDING_PATHS entry: {missing_path}. "
        "Add the /runtimes/<slug> path (and ship the page in clawmetry-landing)."
    )
    assert not extra_path, f"RUNTIME_LANDING_PATHS names unknown runtimes: {extra_path}"
    assert not missing_label, f"runtimes with no RUNTIME_LABELS entry: {missing_label}"
    for rid, path in RUNTIME_LANDING_PATHS.items():
        assert re.fullmatch(r"/[a-z0-9-]+(?:/[a-z0-9-]+)?", path), (rid, path)


def _readme_runtime_grid() -> str:
    text = (REPO / "README.md").read_text(encoding="utf-8")
    m = re.search(r"^## Works with \d+ agent runtimes\s*$(.*?)^## ", text, re.M | re.S)
    assert m, "README.md lost its 'Works with N agent runtimes' section"
    return m.group(1)


def test_readme_grid_links_every_runtime_to_its_page():
    """The grid is the first thing an external-list maintainer clicks through.
    A bold name with no link reads as 'not really supported'."""
    grid = _readme_runtime_grid()
    problems = []
    for rid in sorted(ALL_RUNTIMES):
        url = LANDING_ORIGIN + RUNTIME_LANDING_PATHS[rid]
        if f"]({url})" not in grid:
            problems.append(f"{rid} ({RUNTIME_LABELS[rid]}): no [..]({url}) link in the README grid")
    assert not problems, "\n  ".join(["README runtime grid is out of lockstep:"] + problems)
    # And nothing in the grid is a bare bold runtime name (the Exo failure shape).
    bare = re.findall(r"\*\*(?!\[)([A-Za-z0-9 .+-]{2,40})\*\*", grid)
    bare = [b for b in bare if b.strip().lower() not in {"whole agent fleet"}]
    assert not bare, f"README grid has unlinked runtime names: {bare}"


@pytest.mark.skipif(
    not os.environ.get("CLAWMETRY_LIVE_CHECKS"),
    reason="live storefront check; set CLAWMETRY_LIVE_CHECKS=1 after the landing PR is deployed",
)
def test_every_runtime_page_is_live_on_clawmetry_com():
    import urllib.request

    down = []
    for rid in sorted(ALL_RUNTIMES):
        url = LANDING_ORIGIN + RUNTIME_LANDING_PATHS[rid]
        req = urllib.request.Request(url, method="HEAD", headers={"User-Agent": "clawmetry-ci"})
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                if resp.status != 200:
                    down.append(f"{rid}: {url} -> {resp.status}")
        except Exception as exc:  # noqa: BLE001 - report every failure shape
            down.append(f"{rid}: {url} -> {exc}")
    assert not down, "\n  ".join(["runtime pages not live:"] + down)
