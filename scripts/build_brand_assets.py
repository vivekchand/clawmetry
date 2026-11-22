#!/usr/bin/env python3
"""Generate every ClawMetry brand asset from one geometric definition.

The mark is a set of concentric open rings (range rings) cut by a horizontal
measurement axis, with a hub and a probe on the 0 degree bearing. It is defined
once here, on a 64-unit grid, and every shipped file is derived from it so the
logo can never drift between surfaces.

Two cuts exist:

* ``full``     - three rings plus both notches. Use at 48px and above.
* ``compact``  - outer ring, one inner ring, probe. Use at 32px and below;
                 the full cut's notches close up and turn to mush at 16px.

Run from the repo root::

    python3 scripts/build_brand_assets.py

Requires ``rsvg-convert`` and ``magick`` (ImageMagick 7) for the raster
outputs; the SVGs are written with no external dependencies at all. ``.icns``
additionally needs macOS ``iconutil`` and is skipped elsewhere.
"""

from __future__ import annotations

import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# --- brand constants ---------------------------------------------------------

BRAND = "#E0462F"  # vermilion; deliberately warmer than OpenClaw's #E94644
INK = "#10151C"  # probe + hub on light grounds
PAPER = "#FFFFFF"  # probe + hub on dark grounds
TILE = "#11161E"  # app-icon tile ground

# --- geometry ----------------------------------------------------------------
# Every arc below is derived from one centre (32,32) and one 0 degree axis.
#   outer ring  r 26   weight 8     aperture +/-42deg
#   mid ring    r 17.5 weight 6     aperture +/-52deg, notched at 90 and 270
#   inner ring  r 9.5  weight 5.5   aperture +/-60deg
#   axis slot   180deg +/-7deg through every ring
#   probe       0deg, hub to x 59
#   hub         r 5.2

_FULL_RINGS = """\
    <path d="M51.32 14.60A26 26 0 0 0 6.14 29.28" stroke-width="8"/>
    <path d="M6.14 34.72A26 26 0 0 0 51.32 49.40" stroke-width="8"/>
    <path d="M42.77 18.21A17.5 17.5 0 0 0 34.13 14.63" stroke-width="6"/>
    <path d="M29.87 14.63A17.5 17.5 0 0 0 14.63 29.87" stroke-width="6"/>
    <path d="M14.63 34.13A17.5 17.5 0 0 0 29.87 49.37" stroke-width="6"/>
    <path d="M34.13 49.37A17.5 17.5 0 0 0 42.77 45.79" stroke-width="6"/>
    <path d="M36.75 23.77A9.5 9.5 0 0 0 22.62 30.51" stroke-width="5.5"/>
    <path d="M22.62 33.49A9.5 9.5 0 0 0 36.75 40.23" stroke-width="5.5"/>"""

_COMPACT_RINGS = """\
    <path d="M51.32 14.60A26 26 0 1 0 51.32 49.40" stroke-width="8.5"/>
    <path d="M38 21.61A12 12 0 1 0 38 42.39" stroke-width="6"/>"""

_CUTS = {
    "full": (_FULL_RINGS, 3.6, 5.2),
    "compact": (_COMPACT_RINGS, 4.0, 5.4),
}


def mark_body(cut: str = "full", brand: str = BRAND, field: str | None = None, indent: str = "  ") -> str:
    """Return the mark's SVG elements on a 0 0 64 64 grid.

    ``field`` is the colour of the hub and probe. Pass ``None`` for a
    single-colour mark, which is the only cut that is safe on an unknown
    background (a favicon sits on whatever the browser's tab bar happens to be).
    """
    rings, probe_w, hub_r = _CUTS[cut]
    field = field or brand
    body = (
        f'<g stroke="{brand}" stroke-linecap="butt">\n{rings}\n  </g>\n'
        f'  <path d="M32 32H59" stroke="{field}" stroke-width="{probe_w}" stroke-linecap="round"/>\n'
        f'  <circle cx="32" cy="32" r="{hub_r}" fill="{field}"/>'
    )
    return "\n".join(indent + line if line.strip() else line for line in body.split("\n"))


def mark_svg(cut: str = "full", brand: str = BRAND, field: str | None = None, size: int = 256) -> str:
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" '
        f'viewBox="0 0 64 64" fill="none" role="img" aria-label="ClawMetry">\n'
        f"{mark_body(cut, brand, field)}\n</svg>\n"
    )


# --- lockups -----------------------------------------------------------------
# The wordmark is already outlined paths in the shipped lockups. We keep those
# glyphs verbatim (same typography as before) and swap only the mark group, so
# this change is a mark swap and not an unannounced typeface change.

LOCKUPS = {
    # name: (viewBox w, h, mark x, mark y, mark size, dark background?)
    "clawmetry-logo-horizontal": (877, 260, 35.0, 35.0, 196.0, False),
    "clawmetry-logo-horizontal-darkbg": (877, 260, 35.0, 35.0, 196.0, True),
    "clawmetry-logo-stacked": (769, 680, 225.0, 54.64, 319.0, False),
    "clawmetry-logo-stacked-darkbg": (769, 680, 225.0, 54.64, 319.0, True),
}

OLD_REDS = ("#E5443A", "#E94644", "#C10A09", "#CD1315")


def wordmark_group(path: Path) -> str:
    """Pull the wordmark <g> (the last group) out of an existing lockup."""
    svg = path.read_text(encoding="utf-8")
    start = svg.rfind("<g transform=")
    end = svg.rfind("</g>")
    if start == -1 or end == -1 or end < start:
        raise SystemExit(f"could not find the wordmark group in {path}")
    group = svg[start : end + len("</g>")]
    for old in OLD_REDS:
        group = group.replace(old, BRAND).replace(old.lower(), BRAND)
    return group


def build_lockup(name: str, word: str) -> str:
    w, h, mx, my, msize, dark = LOCKUPS[name]
    scale = msize / 64.0
    field = PAPER if dark else INK
    body = mark_body("full", BRAND, field, indent="    ")
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" '
        f'fill="none" role="img" aria-label="ClawMetry">\n'
        f'  <g transform="translate({mx},{my}) scale({scale:.5f})">\n{body}\n  </g>\n'
        f"  {word}\n</svg>\n"
    )


# --- raster ------------------------------------------------------------------


def need(tool: str) -> str:
    path = shutil.which(tool)
    if not path:
        raise SystemExit(f"{tool} is required for the raster assets; install it and re-run")
    return path


def rasterize(svg: Path, out: Path, size: int) -> None:
    subprocess.run(
        [need("rsvg-convert"), "-w", str(size), "-h", str(size), str(svg), "-o", str(out)],
        check=True,
    )


def app_icon(out: Path, size: int, src: Path) -> None:
    """A dark squircle tile with the reversed mark, the way a desktop app icon reads."""
    magick = need("magick")
    radius = int(size * 0.2222)
    with tempfile.TemporaryDirectory() as td:
        td_path = Path(td)
        tile, glyph = td_path / "tile.png", td_path / "glyph.png"
        subprocess.run(
            [magick, "-size", f"{size}x{size}", "xc:none", "-fill", TILE,
             "-draw", f"roundrectangle 0,0 {size - 1},{size - 1} {radius},{radius}", str(tile)],
            check=True,
        )
        rasterize(src, glyph, int(size * 0.62))
        # nudge left: the probe puts the mark's visual mass right of centre
        subprocess.run(
            [magick, str(tile), str(glyph), "-gravity", "center",
             "-geometry", f"-{max(1, size // 64)}+0", "-composite", str(out)],
            check=True,
        )


def build_icns(out: Path, src: Path) -> bool:
    if not shutil.which("iconutil"):
        print("  .. iconutil not found (macOS only) - skipping .icns")
        return False
    with tempfile.TemporaryDirectory() as td:
        iconset = Path(td) / "ClawMetry.iconset"
        iconset.mkdir()
        for base in (16, 32, 128, 256, 512):
            app_icon(iconset / f"icon_{base}x{base}.png", base, src)
            app_icon(iconset / f"icon_{base}x{base}@2x.png", base * 2, src)
        subprocess.run(["iconutil", "-c", "icns", str(iconset), "-o", str(out)], check=True)
    return True


def main() -> int:
    print(f"building ClawMetry brand assets in {ROOT}")

    # 1. the universal single-colour marks (safe on any ground)
    (ROOT / "clawmetry-logo.svg").write_text(mark_svg("full"), encoding="utf-8")
    (ROOT / "clawmetry" / "static" / "img" / "logo.svg").write_text(
        mark_svg("compact", size=64), encoding="utf-8"
    )
    assets = ROOT / "desktop" / "assets"
    (assets / "clawmetry-logo.svg").write_text(mark_svg("full"), encoding="utf-8")
    (assets / "clawmetry-mark-compact.svg").write_text(mark_svg("compact"), encoding="utf-8")
    # 2. two-tone cuts, for grounds we control
    (assets / "clawmetry-mark-darkbg.svg").write_text(
        mark_svg("full", field=PAPER), encoding="utf-8"
    )
    (assets / "clawmetry-mark-lightbg.svg").write_text(
        mark_svg("full", field=INK), encoding="utf-8"
    )
    print("  .. 6 mark SVGs")

    # 3. lockups, keeping the existing outlined wordmark
    for name in LOCKUPS:
        path = assets / f"{name}.svg"
        word = wordmark_group(path)
        path.write_text(build_lockup(name, word), encoding="utf-8")
    print("  .. 4 lockups (wordmark glyphs preserved)")

    # 4. rasters
    reversed_src = assets / "clawmetry-mark-darkbg.svg"
    app_icon(assets / "clawmetry-512.png", 512, reversed_src)
    with tempfile.TemporaryDirectory() as td:
        sizes = [16, 24, 32, 48, 64, 128, 256]
        pngs = []
        for s in sizes:
            p = Path(td) / f"ico_{s}.png"
            rasterize(assets / "clawmetry-mark-compact.svg", p, s)
            pngs.append(str(p))
        subprocess.run([need("magick"), *pngs, str(assets / "ClawMetry.ico")], check=True)
    print("  .. clawmetry-512.png, ClawMetry.ico")
    if build_icns(assets / "ClawMetry.icns", reversed_src):
        print("  .. ClawMetry.icns")

    stale = assets / "clawmetry-lobster.svg"
    if stale.exists():
        stale.unlink()
        print("  .. removed clawmetry-lobster.svg (unreferenced, old identity)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
