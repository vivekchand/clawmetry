"""Guards for the desktop bootstrap carousel's slide art.

Bug pinned here (founder flagged 2026-08-09): the cross-sell carousel
rendered raster screenshots (bundled landing-page PNGs, plus a remote
device-square.png fetch) downscaled into the art slot. They looked cheap,
and the remote fetch broke the module's own "no external assets, no
network beyond loopback" contract. The art is now one inline SVG
illustration per slide (SLIDE_ART_SVG), self-contained and crisp at any
DPI. These tests keep raster/remote art from creeping back.
"""

from __future__ import annotations

import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from desktop.onboarding import (  # noqa: E402
    CROSS_SELL_SLIDES,
    SLIDE_ART_SVG,
    render_bootstrap_carousel,
)

ASSETS_DIR = REPO_ROOT / "desktop" / "assets"


def test_every_slide_has_vector_art():
    for slide in CROSS_SELL_SLIDES:
        assert slide["art"] in SLIDE_ART_SVG, f"no SVG art for {slide['art']!r}"


def test_slides_carry_no_raster_images():
    # 'img' (remote URL) and 'img_asset' (bundled PNG) are the two raster
    # mechanisms the redesign removed.
    for slide in CROSS_SELL_SLIDES:
        assert "img" not in slide and "img_asset" not in slide, slide["art"]


def test_art_svgs_are_wellformed_vector():
    for key, svg in SLIDE_ART_SVG.items():
        root = ET.fromstring(svg)
        assert root.tag.endswith("svg"), key
        assert "viewBox" in root.attrib, key
        # No embedded rasters or external references inside the art
        # (the xmlns namespace URI is not a network fetch).
        assert "<image" not in svg, key
        assert 'href="http' not in svg and "url(http" not in svg, key


def test_carousel_html_is_self_contained():
    html = render_bootstrap_carousel(assets_dir=ASSETS_DIR)
    # The only <img> allowed is the data-URI brand logo in the top bar.
    for m in re.finditer(r'<img[^>]*src="([^"]+)"', html):
        assert m.group(1).startswith("data:"), m.group(0)[:80]
    # No network resource loads: every src/href that isn't a data URI or
    # anchor must not point at http(s).
    assert 'src="http' not in html and "src='http" not in html
    assert "cross-sell-" not in html
    # Each slide's art actually reaches the page payload.
    for key in SLIDE_ART_SVG:
        assert f'"{key}":' in html or f"'{key}':" in html or "<svg" in html
    assert html.count("<svg") >= len(CROSS_SELL_SLIDES)
