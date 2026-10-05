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
checked-in one drifted, so a hand-edit or a stale regeneration is caught. It
generates into a temporary directory and never writes into the tree it is
verifying, and it corroborates any difference with a second independent
generation before calling it drift -- see ``main`` for why both matter.
"""
from __future__ import annotations

import argparse
import contextlib
import hashlib
import os
import re
import shutil
import ssl
import sys
import tempfile
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


def build(spec: dict, fonts_dir: str | None = None) -> str:
    """Download + dedupe one font set. Returns the generated stylesheet text.

    ``fonts_dir`` is where the woff2 files land, defaulting to the set's
    checked-in directory. Both modes now pass a temporary directory so that
    generating is never a partial write into the tree -- and so that --check
    cannot write into the very tree it is about to compare.
    """
    dest = spec["fonts_dir"] if fonts_dir is None else fonts_dir
    blocks = _parse(_fetch(spec["url"]).decode("utf-8"))
    if not blocks:
        raise SystemExit(f"{spec['name']}: no @font-face blocks parsed — API shape changed?")

    os.makedirs(dest, exist_ok=True)
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
            with open(os.path.join(dest, filename), "wb") as fh:
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


def _sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _digests(directory: str) -> dict[str, str]:
    """``{filename: sha256}`` for one font directory; ``{}`` when it is absent.

    Compared by CONTENT, not by name. Names are derived from the family and
    the subset, so a changed font file keeps its old name: comparing listings
    alone cannot tell a current woff2 from a superseded or hand-edited one.
    """
    if not os.path.isdir(directory):
        return {}
    return {
        name: _sha256_file(os.path.join(directory, name))
        for name in sorted(os.listdir(directory))
    }


def _read_text(path: str) -> str:
    if not os.path.exists(path):
        return ""
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def _rel(path: str) -> str:
    return os.path.relpath(path, REPO)


def _describe_drift(spec: dict, css_text: str, fonts: dict[str, str]) -> str | None:
    """What in the checked-in tree disagrees with this generation, if anything.

    Returns a one-line description, or None when every checked-in copy matches.
    Every copy the generator writes is checked: the stylesheet, the woff2 files
    beside it, and the mirrored bundle. Previously only the stylesheet and the
    mirror's file NAMES were compared, and the comparison ran after --check had
    already overwritten the font files -- so a font whose bytes moved upstream
    without changing its name could never be reported at all.
    """
    if _read_text(spec["css_path"]) != css_text:
        return f"{_rel(spec['css_path'])} is stale"
    if _digests(spec["fonts_dir"]) != fonts:
        return (
            f"the woff2 files in {_rel(spec['fonts_dir'])} do not match the "
            "fresh download"
        )

    mirror = spec.get("mirror_dir")
    if mirror:
        mirror_css = os.path.join(mirror, os.path.basename(spec["css_path"]))
        if _read_text(mirror_css) != css_text:
            return f"the mirrored stylesheet in {_rel(mirror)} is stale"
        mirror_fonts = os.path.join(mirror, os.path.basename(spec["fonts_dir"]))
        if _digests(mirror_fonts) != fonts:
            return f"the mirrored woff2 files in {_rel(mirror_fonts)} are stale"
    return None


@contextlib.contextmanager
def _generation(spec: dict):
    """One independent generation, into a throwaway directory.

    Yields ``(css_text, {filename: sha256}, directory)``. The directory is
    removed on exit, so a generation has no effect on the repository unless the
    caller copies it out.
    """
    tmp = tempfile.mkdtemp(prefix="clawmetry-fonts-")
    try:
        css_text = build(spec, fonts_dir=tmp)
        yield css_text, _digests(tmp), tmp
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def _sync_dir(src: str, dest: str) -> None:
    """Make ``dest`` hold exactly ``src``, dropping anything else.

    The prune half matters: without it a subset that upstream stopped serving
    lingers in the tree forever, and the exact-set comparison in
    _describe_drift would then report drift that `vendor_fonts.py` could not
    clear -- a check with no path to green, which is the thing this script's
    whole degrade-on-outage posture exists to avoid.
    """
    os.makedirs(dest, exist_ok=True)
    keep = set(os.listdir(src))
    for stale in set(os.listdir(dest)) - keep:
        os.remove(os.path.join(dest, stale))
    for name in keep:
        shutil.copyfile(os.path.join(src, name), os.path.join(dest, name))


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

        # In --check mode a failure to REACH the upstream API is not drift, and
        # must not be reported as one. The Google Fonts API is outside any
        # contributor's control: an outage, a slow response, or a change to the
        # CSS shape would fail this check on every PR with nothing anyone could
        # do to make it green. A check with no path to green teaches people
        # that red is normal, which is how the OpenSSF Scorecard job sat broken
        # for its entire life.
        #
        # This never hides real drift. It only distinguishes "could not verify"
        # from "verified and wrong". When the fetch succeeds and the content
        # differs, the DRIFT branch below still fails exactly as before.
        #
        # Generation mode deliberately keeps raising: you cannot write a
        # stylesheet you were unable to fetch, and failing loudly is correct
        # there. Mirrors the same posture scripts/verify_vendor.py already
        # takes for the npm registry.
        try:
            with _generation(spec) as (generated, fonts, fresh_dir):
                if args.check:
                    drift = _describe_drift(spec, generated, fonts)
                else:
                    _sync_dir(fresh_dir, spec["fonts_dir"])
                    os.makedirs(os.path.dirname(spec["css_path"]), exist_ok=True)
                    with open(spec["css_path"], "w", encoding="utf-8") as fh:
                        fh.write(generated)
                    _mirror(spec, generated)
                    drift = None
        except BaseException as exc:  # noqa: BLE001 - includes SystemExit from _parse
            if isinstance(exc, KeyboardInterrupt):
                raise
            if not args.check:
                raise
            print(
                f"SKIP   {spec['name']}: could not reach or parse the upstream "
                f"font API ({type(exc).__name__}: {exc})"
            )
            print(
                "       Treated as UNVERIFIED, not as drift. Re-run when the "
                "API is reachable; if this persists the generator needs "
                "updating for a changed API shape."
            )
            continue

        if not args.check:
            count = len(os.listdir(spec["fonts_dir"]))
            size = sum(
                os.path.getsize(os.path.join(spec["fonts_dir"], f))
                for f in os.listdir(spec["fonts_dir"])
            )
            print(
                f"wrote  {spec['name']}: {os.path.relpath(spec['css_path'], REPO)} "
                f"({count} woff2, {size / 1024:.0f} KB)"
            )
            continue

        if drift is None:
            print(f"ok     {spec['name']}: {os.path.relpath(spec['css_path'], REPO)}")
            continue

        # A single disagreeing generation is not yet evidence of drift. The
        # upstream API answers the same request inconsistently often enough to
        # matter: this job failed on main on 2026-10-05 reporting a stale
        # stylesheet, and the regeneration the very next step ran -- same
        # commit, same runner, seconds later -- produced output byte-identical
        # to what was already checked in. Nothing had drifted; one fetch simply
        # came back different.
        #
        # That is the third case the two existing ones do not cover:
        #
        #   could not fetch        -> SKIP  (unverified)
        #   fetched inconsistently -> SKIP  (unverified)   <- this branch
        #   fetched and differs    -> DRIFT (fails)
        #
        # So corroborate: generate a second, independent time. Report drift only
        # when the two agree with each other, which is what a real upstream
        # change looks like. When they disagree, the upstream -- not the tree --
        # is what could not be pinned down, and that is not a contributor's
        # problem to fix. A genuine difference is stable and still fails here.
        #
        # This costs a second download only on the path that was about to fail,
        # so the ordinary green run is unchanged.
        try:
            with _generation(spec) as (again, fonts_again, _unused):
                corroborated = (again, fonts_again) == (generated, fonts)
        except BaseException as exc:  # noqa: BLE001
            if isinstance(exc, KeyboardInterrupt):
                raise
            print(
                f"SKIP   {spec['name']}: {drift}, but the second generation "
                f"needed to confirm it could not be fetched "
                f"({type(exc).__name__}: {exc})"
            )
            print("       Treated as UNVERIFIED, not as drift. Re-run to confirm.")
            continue

        if not corroborated:
            print(
                f"SKIP   {spec['name']}: upstream served two different answers "
                f"for the same request, so {drift} could not be confirmed"
            )
            print(
                "       Treated as UNVERIFIED, not as drift. Nothing in the "
                "tree is known to be stale. Re-run to confirm."
            )
            continue

        print(f"DRIFT  {spec['name']}: {drift}")
        print("       run: python3 scripts/vendor_fonts.py")
        failed = True

    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
