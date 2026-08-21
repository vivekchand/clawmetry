#!/usr/bin/env python3
"""Vendor Google Fonts into the repo so no page load contacts a third party.

Why this exists
---------------
A ``<link href="https://fonts.googleapis.com/...">`` in a served page is three
separate problems for an enterprise deployment:

1. **Air-gap.** A self-hosted install with no egress renders in a fallback
   face, or blocks on the request until it times out.
2. **Privacy.** The request discloses the viewer's IP address and User-Agent
   to a third-party processor on every page load. In the EU this has been
   found to need a legal basis the deployment does not have.
3. **Review.** "Which third parties does your dashboard contact?" is question
   one of every vendor security review. The only good answer is "none".

So we fetch the CSS once, download every ``woff2`` subset, deduplicate them by
content hash (Google serves one variable file per subset, referenced from many
``@font-face`` rules), and emit a stylesheet pointing at local copies. The
``unicode-range`` descriptors are preserved verbatim, so a browser still
downloads only the subsets it actually needs — a Latin-only viewer fetches
roughly 25 KB, not the whole set.

Usage
-----
    python3 scripts/vendor_fonts.py            # regenerate every font set
    python3 scripts/vendor_fonts.py --check    # verify checked-in output is current

``--check`` is what CI runs: it re-derives the stylesheet and fails if the
checked-in one drifted, so a hand-edit or a stale regeneration is caught.
"""
from __future__ import annotations

import argparse
import hashlib
import os
import re
import ssl
import sys
import urllib.request

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATIC = os.path.join(REPO, "clawmetry", "static")

# Pretend to be a modern browser so the css2 API serves woff2 rather than the
# ttf fallback it hands to unrecognised clients.
_UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)

# Each entry: the css2 request, where the woff2 files land, and where the
# generated stylesheet is written. ``rel`` is the path from the stylesheet to
# the font directory, baked into the src: url().
FONT_SETS = [
    {
        "name": "dashboard",
        "url": (
            "https://fonts.googleapis.com/css2"
            "?family=Manrope:wght@400;500;600;700;800"
            "&family=Noto+Sans+Arabic:wght@400;500;700"
            "&family=Noto+Sans+Hebrew:wght@400;500;700"
            "&display=swap"
        ),
        "fonts_dir": os.path.join(STATIC, "fonts"),
        "css_path": os.path.join(STATIC, "css", "fonts.css"),
        "rel": "../fonts",
        "note": "Manrope (UI) + Noto Sans Arabic/Hebrew (RTL locales).",
    },
    {
        "name": "v2",
        "url": (
            "https://fonts.googleapis.com/css2"
            "?family=Instrument+Serif:ital@0;1"
            "&family=JetBrains+Mono:wght@400;500;600"
            "&family=Space+Grotesk:wght@300;400;500;600;700"
            "&display=swap"
        ),
        # Source of truth is frontend/public/: vite.config.ts sets
        # emptyOutDir=true, so anything written straight into dist/ is deleted
        # by the next `npm run build`. Vite copies publicDir verbatim into the
        # bundle root, which is where the Flask catch-all looks for it.
        "fonts_dir": os.path.join(REPO, "frontend", "public", "fonts"),
        "css_path": os.path.join(REPO, "frontend", "public", "fonts.css"),
        "rel": "fonts",
        # The checked-in bundle has to work without a rebuild, so mirror there
        # too. Both copies are byte-identical and both are verified by --check.
        "mirror_dir": os.path.join(STATIC, "v2", "dist"),
        "note": "Instrument Serif + JetBrains Mono + Space Grotesk (v2 preview UI).",
    },
]

_BLOCK_RE = re.compile(r"/\*\s*([a-z-]+)\s*\*/\s*@font-face\s*\{(.*?)\}", re.S)


def _fetch(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": _UA})
    # Some Python builds ship without a usable CA bundle; fall back to certifi
    # when it is importable rather than disabling verification.
    ctx = ssl.create_default_context()
    try:
        import certifi  # noqa: F401

        ctx = ssl.create_default_context(cafile=certifi.where())
    except Exception:
        pass
    with urllib.request.urlopen(req, timeout=30, context=ctx) as resp:
        return resp.read()


def _parse(css: str) -> list[dict]:
    """Pull the fields we care about out of each @font-face block."""
    out = []
    for subset, body in _BLOCK_RE.findall(css):
        def grab(pattern: str, default: str = "") -> str:
            m = re.search(pattern, body)
            return m.group(1).strip() if m else default

        url = grab(r"url\((https://[^)]+\.woff2)\)")
        if not url:
            # Non-woff2 fallback block — we only vendor woff2.
            continue
        out.append(
            {
                "subset": subset,
                "family": grab(r"font-family:\s*'([^']+)'"),
                "weight": grab(r"font-weight:\s*([^;]+)", "400"),
                "style": grab(r"font-style:\s*(\w+)", "normal"),
                "range": grab(r"unicode-range:\s*([^;]+);"),
                "url": url,
            }
        )
    return out


def build(spec: dict) -> str:
    """Download + dedupe one font set. Returns the generated stylesheet text."""
    blocks = _parse(_fetch(spec["url"]).decode("utf-8"))
    if not blocks:
        raise SystemExit(f"{spec['name']}: no @font-face blocks parsed — API shape changed?")

    os.makedirs(spec["fonts_dir"], exist_ok=True)
    by_hash: dict[str, str] = {}
    lines = [
        "/* ClawMetry — self-hosted webfonts. GENERATED, do not hand-edit.",
        f"   {spec['note']}",
        "   Regenerate: python3 scripts/vendor_fonts.py",
        "   Verified in CI: python3 scripts/vendor_fonts.py --check",
        "",
        "   Vendored so that no page load contacts a third party — required for",
        "   air-gapped installs, and so the answer to 'which third parties does",
        "   your dashboard contact?' stays 'none'. */",
        "",
    ]

    for b in blocks:
        slug = b["family"].lower().replace(" ", "-")
        raw = _fetch(b["url"])
        digest = hashlib.sha256(raw).hexdigest()
        if digest not in by_hash:
            filename = f"{slug}-{b['subset']}.woff2"
            n = 1
            while filename in by_hash.values():
                n += 1
                filename = f"{slug}-{b['subset']}-{n}.woff2"
            with open(os.path.join(spec["fonts_dir"], filename), "wb") as fh:
                fh.write(raw)
            by_hash[digest] = filename
        filename = by_hash[digest]
        lines += [
            "@font-face {",
            f"  font-family: '{b['family']}';",
            f"  font-style: {b['style']};",
            f"  font-weight: {b['weight']};",
            "  font-display: swap;",
            f"  src: url('{spec['rel']}/{filename}') format('woff2');",
        ]
        if b["range"]:
            lines.append(f"  unicode-range: {b['range']};")
        lines += ["}", ""]

    return "\n".join(lines)


def _mirror(spec: dict, css_text: str) -> None:
    """Copy a font set into a second location (the checked-in v2 bundle)."""
    dest = spec.get("mirror_dir")
    if not dest:
        return
    dest_fonts = os.path.join(dest, os.path.basename(spec["fonts_dir"]))
    os.makedirs(dest_fonts, exist_ok=True)
    # Drop stale files so a removed subset does not linger in the mirror.
    keep = set(os.listdir(spec["fonts_dir"]))
    for stale in set(os.listdir(dest_fonts)) - keep:
        os.remove(os.path.join(dest_fonts, stale))
    for name in keep:
        with open(os.path.join(spec["fonts_dir"], name), "rb") as src:
            data = src.read()
        with open(os.path.join(dest_fonts, name), "wb") as out:
            out.write(data)
    with open(os.path.join(dest, os.path.basename(spec["css_path"])), "w", encoding="utf-8") as out:
        out.write(css_text)


def _mirror_is_current(spec: dict, css_text: str) -> bool:
    dest = spec.get("mirror_dir")
    if not dest:
        return True
    css_dest = os.path.join(dest, os.path.basename(spec["css_path"]))
    if not os.path.exists(css_dest):
        return False
    with open(css_dest, encoding="utf-8") as fh:
        if fh.read() != css_text:
            return False
    dest_fonts = os.path.join(dest, os.path.basename(spec["fonts_dir"]))
    if not os.path.isdir(dest_fonts):
        return False
    return set(os.listdir(dest_fonts)) == set(os.listdir(spec["fonts_dir"]))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--check",
        action="store_true",
        help="verify the checked-in stylesheets match a fresh generation",
    )
    ap.add_argument("--only", help="limit to one font set by name")
    args = ap.parse_args()

    failed = False
    for spec in FONT_SETS:
        if args.only and spec["name"] != args.only:
            continue
        generated = build(spec)
        path = spec["css_path"]
        if args.check:
            current = ""
            if os.path.exists(path):
                with open(path, encoding="utf-8") as fh:
                    current = fh.read()
            if current != generated:
                print(f"DRIFT  {spec['name']}: {os.path.relpath(path, REPO)} is stale")
                print("       run: python3 scripts/vendor_fonts.py")
                failed = True
            elif not _mirror_is_current(spec, generated):
                print(f"DRIFT  {spec['name']}: mirror in {os.path.relpath(spec['mirror_dir'], REPO)} is stale")
                print("       run: python3 scripts/vendor_fonts.py")
                failed = True
            else:
                print(f"ok     {spec['name']}: {os.path.relpath(path, REPO)}")
        else:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(generated)
            _mirror(spec, generated)
            count = len(os.listdir(spec["fonts_dir"]))
            size = sum(
                os.path.getsize(os.path.join(spec["fonts_dir"], f))
                for f in os.listdir(spec["fonts_dir"])
            )
            print(
                f"wrote  {spec['name']}: {os.path.relpath(path, REPO)} "
                f"({count} woff2, {size / 1024:.0f} KB)"
            )

    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
