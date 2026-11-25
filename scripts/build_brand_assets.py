#!/usr/bin/env python3
"""Generate every ClawMetry brand asset from the Little Clawbot vector master.

The owner selected Little Clawbot (option 12): a curious red robot with soft
pincer hands, a tilted visor and one hand waving. It is defined once here on
a 64-unit grid. Every shipped variant derives from this geometry.

Two cuts exist:

* ``full``     - expressive eyes with upward-looking pupils.
* ``compact``  - simple white eyes, for favicon-size rendering.

Run from the repo root::

    python3 scripts/build_brand_assets.py

Requires ``rsvg-convert`` and ``magick`` (ImageMagick 7) for the raster
outputs; the SVGs and PNG-based ICNS container use the Python standard library.
"""

from __future__ import annotations

import re
import shutil
import struct
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# --- brand constants ---------------------------------------------------------

BRAND = "#EB3D36"  # Little Clawbot vermilion
INK = "#191B1E"  # visor, pupils and light-ground feet
PAPER = "#FFFFFF"  # eyes, smile and dark-ground feet
TILE = "#11161E"  # app-icon tile ground

# --- geometry ----------------------------------------------------------------
def mark_body(cut: str = "full", brand: str = BRAND, field: str | None = None, indent: str = "  ") -> str:
    """Return the selected mascot; ``field`` chooses the feet's contrast."""
    if cut not in ("full", "compact"):
        raise ValueError(f"unknown mascot cut: {cut}")
    feet = field or INK
    pupils = '' if cut == "compact" else (
        f'<g fill="{INK}"><circle cx="27.5" cy="27.2" r="2.45"/>'
        '<circle cx="45" cy="27.2" r="2.45"/></g>'
    )
    body = f'''<g data-brand="little-clawbot-v1" transform="rotate(-12 32 33)">
  <g fill="{feet}">
    <rect x="20" y="49" width="8" height="7" rx="3.3"/>
    <rect x="39" y="49" width="8" height="7" rx="3.3"/>
  </g>
  <g fill="{brand}" stroke="{brand}" stroke-linecap="round" stroke-linejoin="round">
    <path d="M17 43Q12 48 8 45" fill="none" stroke-width="4.4"/>
    <path d="M10 44C9 40 7 39 5.5 40C4 41 5 43 6 44C6.5 45 5.5 46 4.5 45L3 44.5C1 44 .5 46 2 48C4 51 9 50 11 47Z" stroke="none"/>
    <path d="M51 35Q61 32 61 23" fill="none" stroke-width="4.5"/>
    <path transform="translate(3 0)" d="M56 25C51 23 51 19 53 16C54 14 57 14 57 17L56 19C56 20 57 20 58 19L59 17C60 15 63 16 63 18C63 22 61 25 58 26Z" stroke="none"/>
    <rect x="14" y="12" width="40" height="41" rx="11.8" stroke="none"/>
  </g>
  <rect x="16" y="21" width="36" height="17" rx="8.5" fill="{INK}"/>
  <g fill="{PAPER}"><ellipse cx="25.5" cy="29.2" rx="5.2" ry="5.5"/>
    <ellipse cx="43" cy="29.2" rx="5.2" ry="5.5"/></g>
  {pupils}
  <path d="M32.3 33.2Q34.5 37 37 33.2" fill="none" stroke="{PAPER}" stroke-width="1.65" stroke-linecap="round"/>
</g>'''
    return "\n".join(indent + line if line.strip() else "" for line in body.split("\n"))


def mark_svg(cut: str = "full", brand: str = BRAND, field: str | None = None, size: int = 256) -> str:
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" '
        f'viewBox="0 0 64 64" fill="none" role="img" aria-label="ClawMetry">\n'
        f"{mark_body(cut, brand, field)}\n</svg>\n"
    )


def monochrome_svg(color: str = INK, size: int = 256) -> str:
    """Use the same geometry as an alpha mask for themed platform icons."""
    mask = mark_body("full", PAPER, PAPER)
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" '
        'viewBox="0 0 64 64" role="img" aria-label="ClawMetry">\n'
        '<defs><mask id="clawbot" maskUnits="userSpaceOnUse" x="0" y="0" width="64" height="64">\n'
        f'{mask}\n</mask></defs>\n'
        f'<rect width="64" height="64" fill="{color}" mask="url(#clawbot)"/>\n</svg>\n'
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

OLD_REDS = ("#E5443A", "#E94644", "#C10A09", "#CD1315", "#E0462F")


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


def tile_mark_svg(cut: str = "full", size: int = 256) -> str:
    """A known ground keeps the mascot readable in either dashboard theme."""
    body = mark_body(cut, BRAND, PAPER, indent="    ")
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" '
        f'viewBox="0 0 64 64" fill="none" role="img" aria-label="ClawMetry">\n'
        f'  <rect width="64" height="64" rx="14" fill="{TILE}"/>\n'
        f'  <g transform="translate(32,32) scale(0.90) translate(-32,-32)">\n'
        f"{body}\n  </g>\n</svg>\n"
    )


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
        rasterize(src, glyph, max(1, int(size * 0.86)))
        subprocess.run(
            [magick, str(tile), str(glyph), "-gravity", "center",
             "-composite", "-depth", "8", "PNG32:" + str(out)],
            check=True,
        )


def build_icns(out: Path, src: Path) -> bool:
    """Pack modern PNG icon-family frames, including the 1024px Retina frame.

    This also works off macOS. Native iconutil can decode the result; its
    encoder rejects otherwise valid ImageMagick PNG iconsets on macOS 26.
    """
    frames = ((b"icp4", 16), (b"icp5", 32), (b"icp6", 64),
              (b"ic07", 128), (b"ic08", 256), (b"ic09", 512), (b"ic10", 1024))
    chunks = []
    with tempfile.TemporaryDirectory() as td:
        for tag, size in frames:
            png = Path(td) / f"{size}.png"
            app_icon(png, size, src)
            data = png.read_bytes()
            chunks.append(tag + struct.pack(">I", len(data) + 8) + data)
    payload = b"".join(chunks)
    out.write_bytes(b"icns" + struct.pack(">I", len(payload) + 8) + payload)
    return True


def main() -> int:
    print(f"building ClawMetry brand assets in {ROOT}")

    # 1. Canonical mascot and theme-safe in-app variants.
    (ROOT / "clawmetry-logo.svg").write_text(
        mark_svg("full"), encoding="utf-8"
    )
    # The in-app logo and favicon render on a ground we do not control (both
    # dashboard themes, and any browser tab bar), so this one carries the tile.
    (ROOT / "clawmetry" / "static" / "img" / "logo.svg").write_text(
        tile_mark_svg("full", size=64), encoding="utf-8"
    )
    (ROOT / "clawmetry" / "static" / "img" / "favicon.svg").write_text(
        tile_mark_svg("compact", size=64), encoding="utf-8"
    )
    assets = ROOT / "desktop" / "assets"
    (assets / "clawmetry-logo.svg").write_text(
        mark_svg("full"), encoding="utf-8"
    )
    (assets / "clawmetry-mark-compact.svg").write_text(
        mark_svg("compact", field=PAPER), encoding="utf-8"
    )
    # 2. two-tone cuts, for grounds we control
    (assets / "clawmetry-mark-darkbg.svg").write_text(
        mark_svg("full", field=PAPER), encoding="utf-8"
    )
    (assets / "clawmetry-mark-lightbg.svg").write_text(
        mark_svg("full", field=INK), encoding="utf-8"
    )
    (assets / "clawmetry-mark-mono.svg").write_text(monochrome_svg(), encoding="utf-8")
    (assets / "clawmetry-mark-mono-darkbg.svg").write_text(monochrome_svg(PAPER), encoding="utf-8")
    print("  .. 6 mark SVGs")

    # 3. lockups, keeping the existing outlined wordmark
    for name in LOCKUPS:
        path = assets / f"{name}.svg"
        word = wordmark_group(path)
        path.write_text(build_lockup(name, word), encoding="utf-8")
    print("  .. 4 lockups (wordmark glyphs preserved)")

    # The bundled interface uses the same mascot, rather than an inline redraw.
    frontend = ROOT / "frontend" / "src" / "assets"
    (frontend / "little-clawbot.svg").write_text(mark_svg("full"), encoding="utf-8")
    (frontend / "little-clawbot-compact.svg").write_text(mark_svg("compact"), encoding="utf-8")
    rasterize(frontend / "little-clawbot.svg", frontend / "clawbert-logo.png", 512)

    # Shared browser-tab icon for the optional interface.
    (ROOT / "frontend" / "public" / "favicon.svg").write_text(
        tile_mark_svg("compact", size=64), encoding="utf-8"
    )

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
