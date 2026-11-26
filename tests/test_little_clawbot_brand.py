"""Shipped mascot and icon contracts.

* AC-BRAND-001.1: the selected mascot geometry reaches each owned SVG surface.
* AC-BRAND-001.3: generated icon files have valid platform frames and sizes.
* AC-BRAND-001.4: shared variants are editable vectors with no font dependency.
"""
import struct
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
NS = {'s': 'http://www.w3.org/2000/svg'}


def test_every_owned_brand_svg_contains_editable_clawbot_geometry():
    paths = [ROOT / 'clawmetry-logo.svg']
    paths += list((ROOT / 'desktop/assets').glob('clawmetry-*.svg'))
    paths += list((ROOT / 'clawmetry/static/img').glob('*.svg'))
    paths += list((ROOT / 'frontend/src/assets').glob('little-clawbot*.svg'))
    paths += [ROOT / 'frontend/public/favicon.svg']
    assert len(paths) >= 15
    for path in paths:
        tree = ET.fromstring(path.read_text())
        assert tree.find('.//s:g[@data-brand="little-clawbot-v1"]', NS) is not None, path
        assert not tree.findall('.//s:image', NS), path
        assert not tree.findall('.//s:text', NS), path
        assert tree.get('viewBox'), path


def test_static_and_optional_interface_favicons_match():
    static = ROOT / 'clawmetry/static/img/favicon.svg'
    assert static.read_bytes() == (ROOT / 'frontend/public/favicon.svg').read_bytes()
    tree = ET.fromstring(static.read_text())
    eyes = tree.findall('.//s:ellipse', NS)
    assert len(eyes) == 2
    # The small cut has clear eyes without the full cut's tiny pupil circles.
    assert not tree.findall('.//s:circle', NS)


def test_platform_icon_containers_hold_real_png_frames():
    """Reject stale or malformed platform assets before installer packaging."""
    data = (ROOT / 'desktop/assets/ClawMetry.icns').read_bytes()
    assert data[:4] == b'icns'
    assert struct.unpack('>I', data[4:8])[0] == len(data)
    offset, sizes = 8, set()
    while offset < len(data):
        length = struct.unpack('>I', data[offset + 4:offset + 8])[0]
        png = data[offset + 8:offset + length]
        assert png[:8] == b'\x89PNG\r\n\x1a\n'
        w, h = struct.unpack('>II', png[16:24])
        assert w == h
        sizes.add(w)
        offset += length
    assert offset == len(data)
    assert sizes == {16, 32, 64, 128, 256, 512, 1024}
    ico = (ROOT / 'desktop/assets/ClawMetry.ico').read_bytes()
    assert ico[:4] == b'\x00\x00\x01\x00'
    assert struct.unpack('<H', ico[4:6])[0] >= 6
